# DRY review: `django_strawberry_framework/orders/__init__.py`

Status: verified
Run: 0.0.15 2026-09-22-5

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an open
family holding item, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Small target (101 lines): the ordering subsystem's leaf manifest plus its
Decision-11 consumer-helper ledger. It DEFINES one behavior (the
`order_input_type` thin wrapper over an already single-sited driver) and one
piece of state (the helper-reference ledger + its clear callback + bus
registration); everything else is by-name composition: 1 re-export binding
from `base.py`, 1 public + 2 body-private names from `inputs.py`, 2 from
`sets.py`, and the 5-member `__all__` mirror. No branching, no queryset, no
transport, no sync/async machinery, no `__getattr__`, no deprecation shim:
runtime effects are import-time binding, one set object, one bus registration,
and one pure function body that delegates.

Connected code read for judgment, outside the item:
[orders-base][orders-base] (HEAD bytes: head + `RelatedOrder` definition
site), [orders-sets][orders-sets] (HEAD bytes: head + `OrderSetMetaclass` /
`OrderSet` definition sites), [orders-inputs][orders-inputs] (HEAD bytes:
head: alias table, `INPUTS_MODULE_PATH`, `Ordering`),
[orders-factories][orders-factories] (`OrderArgumentsFactory` definition
site), [filters-init][filters-init] (full: the Decision-11 twin leaf),
[utils-inputs][utils-inputs]`::build_lazy_input_annotation` (HEAD bytes: full
driver body + docstring) and `::set_input_type_name` (HEAD bytes: naming
delegate), [registry][registry]`::register_subsystem_clear` (HEAD bytes:
contract), [finalizer][finalizer] phase-2.5 orders passage (HEAD bytes:
subpass-3 orphan prose + reader), [pkg-root][pkg-root] (full grep: confirms
zero orders imports, the Decision-2-shaped omission), [connection][connection]
sidecar-signature builder (HEAD bytes: function-local consumer import +
ledger prose), [list-field][list-field] sidecar builder (HEAD bytes:
function-local consumer import), the contract source [spec-028][spec-028]
Decision 2 + Decision 11 passages (read), oracles
[test-order-inputs][test-order-inputs] (HEAD bytes: Decision-11 block +
clear block, read) and [test-order-finalizer][test-order-finalizer] (import
block + orphan block, read), consumer imports across `tests/` + `examples/` +
`docs/` (grep population), prose projections [docs-readme][docs-readme] +
[glossary][glossary] (usage blocks via grep), and the verified holding family
[dry-clear-lifecycle][dry-clear-lifecycle] (member table: row 4 names this
file's bus row).

Dirt note (all read via `git show HEAD:<path>`, never touched): the worktree
copies of [orders-base][orders-base] (`afd55efd…`), [orders-inputs][orders-inputs]
(`889b5971…`), [orders-sets][orders-sets] (`f09d9983…`),
[utils-inputs][utils-inputs] (`47b2af21…`, including a `__class__`-guard +
`_safe_arg_repr` hunk inside `build_lazy_input_annotation` itself),
[registry][registry] (`612bea87…`, `TypeRegistry`-body hunk, outside the bus
contract), [finalizer][finalizer] (`35ff5286…`, `_field_surface_names` hunk,
outside the orphan passage), [connection][connection] (`9c5b8724…`, import +
`_consume_window` / `_consume_fallback` hunks, outside the sidecar region),
[list-field][list-field] (`f979f0d6…`, `_validate_*` hunks, outside the
consumer region), and [test-order-inputs][test-order-inputs] (`a0300a00…`,
two appended hostile-`__qualname__` tests outside the Decision-11 block) are
hunt-dirtied. Every judgment below is against HEAD bytes; the dirt changes no
count (details per finding). The target itself is CLEAN: worktree
`ed546f9c70d56d73e0d84a029e9e04f27da3934b` equals
`HEAD:django_strawberry_framework/orders/__init__.py`.

Excluded with reason: every other indexed family whose files-covered list was
scanned for this path — only `subsystem-clear-lifecycle` lists
`orders/__init__.py`, and it is routed below (F2 family row; C5, C6 end with 1
definition at the stated owner, never here). `sync-boundary-recourse-wording`
(open; owns a write-pipeline wording at `utils/querysets.py`) and
`one-sync-boundary` (files-covered names `orders/sets.py`, not this leaf) were
judged on their mechanisms against this target's REAL surface and found to
have none here (Matrix axes 1-3, C10-C11). No index row named
`package-root-public-surface`, `lazy-related-class-resolution`, or
`set-type-naming` exists in the current plan; the filters-twin artifact's
treatment of those names was orientation only (prior rejections are triggers
to check), and each mechanism is re-derived fresh below with this leaf's own
difference (F1 nested rejection, C9, C11).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE flavor (orders)
from three home modules. The sibling filter leaf aggregates only its own
flavor (full read of [filters-init][filters-init]); the package root is the
sole cross-flavor aggregator and deliberately carries zero orders imports
(full grep of [pkg-root][pkg-root]: no `orders` / `Order` hit — the spec-028
Decision 2 posture). The shared eager-re-export + `__all__` shape across
leaves is intentional separation per contract (subpackage grain vs default
recipe), not duplication — re-derived fresh here with this leaf's own
Decision-2 difference (see F1). The filters twin
([filters-init][filters-init]`::filter_input_type`) is the same SHAPE with
per-family parameters (different base, label, ledger, module path) — C7/C8
prove opposite change responses, so it is a parameterized sibling, not a
second definition (F3).

**2. Sync/async twins.** Target defines no colored pair: no `async def`, no
`await`, no `sync_to_async` (full 101-line read). The apply pair
(`OrderSet.apply_sync` / `apply_async`) is owned at
[orders-sets][orders-sets]. Considered families `one-sync-boundary`
(files-covered names `orders/sets.py`, not this leaf) and
`subsystem-clear-lifecycle` (files-covered names this leaf — routed, F2):
checked, no twin surface here. No boundary call lives in this file.

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the 1 +
1 + 2 re-export bindings in the SAME file (one edit region, not two
definitions). `INPUTS_MODULE_PATH` + `_input_type_name_for` are imported for
body use only — absent from `__all__`, and every in-tree consumer addresses
them through the `orders.inputs` submodule path, never the leaf — so no second
public surface exists. The input-type NAME derivation is not re-derived here:
the leaf passes `_input_type_name_for` through to the driver; at HEAD bytes it
is the alias `set_input_type_name`, whose body is one delegate call to
`set_class.type_name_for()` ([utils-inputs][utils-inputs]`::set_input_type_name`,
HEAD), and `OrderSet` inherits that mixin method
([orders-sets][orders-sets]`::OrderSet`, HEAD). The set-naming check ends here
with 0 definitions (C9; do not inherit). The sync-recourse wording check ends
here with 0 definitions (C10; no recourse token lives here).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. Import binding → `__all__` membership → `import *` binding is one
direction with a single author (this file), not two halves that can drift
apart. No deprecation shim exists (no `warnings`, no `deprecated` token in the
full read). No surface.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (bindings + manifest + ledger + wrapper);
authoritative contract sources (spec-028 Decision 2 for the export grain,
Decision 11 for the helper + ledger + orphan mechanics; the driver/finalizer
docstrings for the shared body and the read side); independent oracles (the
four `order_input_type` behavior tests spelling `ForwardRef` / `TypeError` /
ledger / idempotency without reading the owner, the orphan-raise tests, the
`registry.clear()` co-clear test, explicit-name consumer imports resolving
through this file without reading `__all__`); projections (leaf docstring,
README + GLOSSARY usage blocks, spec code blocks). A new primitive moves its
home definition once; this file's rows follow by name (C1-C3).

**6. Enforcement by omission.** Three deliberate omissions, each with a
contract source: the whole orders surface stays out of the package root
(spec-028 Decision 2, read at [spec-028][spec-028]) — F1;
`OrderArgumentsFactory` stays out of the leaf (Decision 2 advanced tier:
reached via `orders.factories` directly; the filter twin documents the same
convention; verified absent from the full read) — F1; `INPUTS_MODULE_PATH` /
`_input_type_name_for` stay out of `__all__` (body-use imports; every consumer
uses the submodule path) — F1. Every member the contract requires is present:
all 5 re-exported names bound, `__all__` names exactly those 5 (the 4 public
tier + `OrderSetMetaclass` on the Decision-2 advanced tier), nothing else
bound at module scope except the private ledger pair and imported machinery.
No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **12 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (subsystem paragraph + export-tier prose + orphan-check prose + usage shape) | (none) | prose projection, F1/F2/F3 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from ..registry import register_subsystem_clear` | 1 name (machinery) | F2 consumer row |
| 4 | `from ..utils.inputs import build_lazy_input_annotation` | 1 name (machinery) | F3 consumer row |
| 5 | `from .base import RelatedOrder` | 1 name | R1, F1 |
| 6 | `from .inputs import INPUTS_MODULE_PATH, Ordering, _input_type_name_for` | 3 names: `Ordering` public, pair body-private | R1 + R1-absent-by-design, F1/F3 |
| 7 | `from .sets import OrderSet, OrderSetMetaclass` | 2 names | R1, F1 |
| 8 | `_helper_referenced_ordersets: set[...] = set()` | ledger state | R2, F2 |
| 9 | `def _clear_helper_referenced_ordersets` | 1 name | R2, F2 |
| 10 | `register_subsystem_clear(...)` call | bus row, owner `orders.helper_references` | R2, F2 |
| 11 | `def order_input_type` | 1 name | R3, F3 |
| 12 | `__all__ = (...)` | 5-member tuple | R1, F1 |

Rules: R1 orders leaf manifest (statements 5-7 + 12 + tier prose; 5 = 1 base
+ 1 inputs-public + 2 sets + the helper); R2 helper-reference ledger lifecycle
(statements 3, 8-10 + ledger prose); R3 Decision-11 leaf wrapper (statements
4, 6, 11; statement 6's private pair is R3's parameter feed). Three indexed
families considered (`subsystem-clear-lifecycle`, `sync-boundary-recourse-wording`,
`one-sync-boundary`): one routed as the holding family (F2), two checked with
no surface (Matrix axes 1-3, C10-C11). Two new file-local index rows are named
for Worker 0 (`F1`, `F3`) plus one rejected row (F1 nested rejection); F2 needs
no new row (its holding family row already covers this file — member 4 of the
verified family census).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted. All bodies judged at HEAD bytes (see Dirt note: the worktree dirt
sits outside every read region except the driver's guard hunk, which changes
no count — the leaf still passes the same six parameters).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new primitive | expose a 2nd base primitive (e.g. a sibling order class) | **1** (the definition at `base.py`; this file's import line + `__all__` entry are consumer rows that follow by name; README blocks are projections) | independent |
| C2 | R1 rename | rename `OrderSet` → `DjangoOrderSet` | **1** (`sets.py`; import line + tuple entry + helper annotation here follow) | independent |
| C3 | R1 home move | move `OrderSet` from `sets.py` to `base.py` | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R1 omission lift | lift Decision 2 (root-export orders symbols) | **0 here** (root gains import lines; this file does not move) | independent — proves separation |
| C5 | R2 bus-contract change | change the `register_subsystem_clear` contract (e.g. require `before_bind`) | **1** ([registry][registry] bus; this file's row-10 call follows only as a consumer of the signature) | independent |
| C6 | R2 ledger rename | rename `_helper_referenced_ordersets` → `_helper_ordersets` | **1** (the declaration at statement 8; the driver write + finalizer read + test imports follow by name — listed as Coupling, not counted) | independent |
| C7 | R3 form change | change the ForwardRef form (e.g. drop `strawberry.lazy`) | **1** ([utils-inputs][utils-inputs]`::build_lazy_input_annotation`; both leaves unchanged) | independent — proves single ownership, 0 here |
| C8 | R3 wording change | change the orders family label (`"an OrderSet"` → other) | **1 here** (leaf parameters; the filters twin + driver untouched) | independent — proves per-family parameters |
| C9 | set-naming check | change the `Foo` → `FooOrderInputType` derivation | **0 here** (owned at `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` via `set_input_type_name`; this file passes the function through) | no surface — do not inherit |
| C10 | `sync-boundary-recourse-wording` check | change the sync-misuse recourse sentence | **0 here** (owned at `utils/querysets.py::sync_pipeline_recourse`; no recourse token lives here) | no surface — do not inherit |
| C11 | lazy-target-resolution check | change lazy-target resolution semantics | **0 here** (mixin family defined at `sets_mixins.py`; this file binds only `RelatedOrder` — neither defines nor re-exports the mixin, so not even a consumer row) | no surface — do not inherit |
| C12 | R1 upstream shape change | upstream grows a 7th `Ordering` member | **1** (`inputs.py` enum; this file's row + docstring clause follow) | independent |

No executable proof was run: the target has no runtime semantics beyond
import-time binding plus a pure delegating wrapper whose body is owned
elsewhere (no branches, no awaits, no queryset/transport code), so there is
no behavior an execution could distinguish that the cited oracles do not
already pin. The read-only `ast.parse` enumeration above ran in the shared
tree (non-mutating; the workspace recipe authorizes mutating proofs, of which
this item has none). Every binding is exercised by consumer imports on every
suite run (`tests/orders/*`, `connection.py`'s and `list_field.py`'s call-time
imports, fakeshop app modules). All claims below are therefore
`static-reviewed`; there is no `execution-deferred` proof and no
`docs/dry/temp-tests/` scratch was created — inspection suffices, and a probe
could distinguish nothing.

## Findings

No production edit is owed by a file item; each finding records the rule with
the challenge that proved it has no second site.

### F1 — orders leaf manifest (file-local)

- **Contract + variation.** The orders subpackage's public surface is exactly
  5 names, each composed by name from its home module (1 from `base.py`, 1
  public from `inputs.py`, 2 from `sets.py`, `order_input_type` defined here),
  with `__all__` mirroring the re-export bindings in-file. Legitimate
  variation: set membership only (a 2nd primitive adds one import line + one
  tuple entry in this file).
- **Sites + roles.** *Definitions*: [orders-base][orders-base]`::RelatedOrder`;
  [orders-inputs][orders-inputs]`::Ordering`;
  [orders-sets][orders-sets]`::OrderSet`, `::OrderSetMetaclass`. *Consumer
  rows*: this file's statements 5, 6 (`Ordering` arm), 7, 12.
  *Consumers-as-oracles*: explicit-name imports (`tests/orders/*`,
  `tests/test_list_field.py`, `tests/test_connection.py`, fakeshop
  `orders.py` / `schema.py` modules, [connection][connection]'s and
  [list-field][list-field]'s call-time imports) — independent (they resolve
  the homes through this file without reading the manifest). *Projections*:
  statement-1 tier prose, Decision 2 three-tier passage, README + GLOSSARY
  usage blocks.
- **Challenges.** C1, C2, C3, C12 → 1 definition each (the home module); C4 →
  0 here.
- **Owner + lifetime.** Per-symbol home modules (existing owners, chosen by
  responsibility: each class's declaration, validation, and runtime machinery
  all live there; no narrower owner this file's consumers could depend on
  exists). This file is a consumer (principle 6: compose by name). No stored
  derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owners stand; a new primitive
  adds its definition plus one consumer row here.
- **Distinct behavior.** The manifest intentionally covers only the 5 —
  `OrderArgumentsFactory` excluded (Decision 2 advanced tier: reached via
  `orders.factories` directly; verified absent from the full read),
  `INPUTS_MODULE_PATH` / `_input_type_name_for` imported-but-not-exported
  (statement 6 feeds R3's body; every in-tree consumer addresses them via
  `orders.inputs`), root excluded (Decision 2). `OrderSetMetaclass` rides the
  Decision-2 advanced tier on filter-twin parity (verified:
  [filters-init][filters-init]`__all__` carries `FilterSetMetaclass`), even
  though in-tree consumers import it from `orders.sets` — the `__all__`
  membership is the contract, the submodule path a compatible alias.
  Observation (not a defect): statement-1's "the leading `_` flags them
  private" over-generalizes — `INPUTS_MODULE_PATH` has no leading underscore;
  the MECHANICS hold (both excluded from `__all__`, verified), and the phrasing
  mirrors spec-028 Decision 2's own parenthetical, so no contract row breaks.
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows its
  owner" (bindings are by-name imports; `orders.OrderSet is orders.sets.OrderSet`
  by construction of the import system) and "star binding leaks a 6th name"
  (`__all__` names exactly the 5 bound re-export names; grep finds no other
  public binding in this file).
- **Structural gate.** No exact-`__all__` oracle exists for this leaf (grep
  over `tests/orders/`: every `__all__` hit is the unrelated
  `Meta.fields = "__all__"` token) — the same standing as the filters, auth,
  and extensions leaves. Standing in: every consumer imports names explicitly,
  so a dropped binding fails loudly (`ImportError`) at use sites on every
  suite run. Noted as an observation, not a defect: no contract row requires a
  manifest pin, and a bespoke existence test per leaf manifest would violate
  the gate-only economy (principle 9).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/orders/__init__.py`
  `ed546f9c70d56d73e0d84a029e9e04f27da3934b` (worktree == HEAD; target CLEAN),
  `django_strawberry_framework/orders/base.py` HEAD
  `4736fda0228ee723aada11bfe374f81036ac4c30` (worktree `afd55efd…` hunt dirt
  inside the `RelatedOrder` body — the definition site judged is the HEAD
  class),
  `django_strawberry_framework/orders/inputs.py` HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (worktree `889b5971…` hunt dirt
  at the import block + `normalize_input_value` — outside the enum/alias
  region),
  `django_strawberry_framework/orders/sets.py` HEAD
  `6044ab1a11c77a42b715f0d0722fe7c9695064bc` (worktree `f09d9983…` hunt dirt
  in imports + `OrderSet` body — the two class definition sites judged are
  the HEAD classes),
  `django_strawberry_framework/orders/factories.py`
  `4f35b66b06fe67e800ac43dabe8a1733b221168d` (clean; exclusion witness),
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a` (clean; zero orders imports),
  `django_strawberry_framework/filters/__init__.py`
  `86b258186638c96995e31919346f44d7951c65ea` (clean; parity witness),
  `docs/SPECS/spec-028-orders-0_0_8.md`
  `94a3141c02b92265779d8f3f7a2eefc019f765d8` (clean; Decision 2).
  Searched population for a second manifest of the 5-name set: whole package
  + `tests/` + `examples/` + `docs/` (grep `from
  django_strawberry_framework.orders import` / `from ..orders import` /
  `from .orders import`: only the finalizer ledger read, two call-time helper
  imports, consumer imports, and prose mentions). Excluded on strength of body:
  `orders/inputs.py` aliases (`FieldSpec`, `build_input_class` — submodule
  surface, not the leaf) and `mutations/sets.py` machinery (different
  subsystem).
- **Rejection (nested).** Considered: consolidate the leaf manifest with the
  package-root manifest into one shared manifest rule (same eager-re-export +
  `__all__` shape — the filters twin's artifact rejected the same shape for
  its leaf; compared fresh here, not inherited). Contract difference here: the
  root manifest is the default recipe every consumer pays for at package
  import, while this leaf is the family-grain opt-in whose membership rule is
  the Decision-2 three-tier split (public 4 + advanced metaclass + held-out
  factory and input-namespace internals) — and Decision 2 forbids the root
  from ever carrying these names because it would widen the surface for
  consumers who never order. Posit root-exporting `OrderSet` → the root moves
  and this file does not (C4); posit adding a 2nd primitive → this file moves
  and the root does not (C1). Different responsibility, different population,
  opposite reasons to change: same shape, not the same rule. Trigger to
  reconsider: a decision to root-export the orders surface, or to drive every
  subpackage manifest from one shared driver/validator, would make the sites
  one rule. Durable home: spec-028 Decision 2 (already states the grain) +
  this file's docstring paragraph 1. Named for Worker 0 as rejected index row
  `orders-leaf-vs-root-manifest` (no such row exists in the current plan).

### F2 — helper-reference ledger lifecycle (family row: `subsystem-clear-lifecycle`)

- **Contract + variation.** The `_helper_referenced_ordersets` set records
  every `OrderSet` passed to `order_input_type`; the
  `_clear_helper_referenced_ordersets` callback empties it; the
  `register_subsystem_clear(..., owner="orders.helper_references")` row
  replays that callback under `registry.clear()`. Legitimate variation:
  per-family ledger identity only (the filters twin owns a disjoint set +
  owner string; neither may share the other's).
- **Sites + roles.** *Declaration*: this file's statements 8-9 (ledger +
  clear fn). *Lifecycle owner*: [registry][registry]`::register_subsystem_clear`
  bus (owns replay, validation, `before_bind` posture). *Writer*:
  [utils-inputs][utils-inputs]`::build_lazy_input_annotation` (`ledger.add`
  through the passed reference). *Reader*: [finalizer][finalizer] orders
  phase-2.5 subpass 3 (compares against `Meta.orderset_class`-wired sets,
  raises `ConfigurationError` for orphans). *Oracles*: ledger-membership tests
  (`test_order_input_type_records_orderset_into_helper_referenced_set`,
  idempotency test) + orphan-raise tests in
  [test-order-finalizer][test-order-finalizer] + the co-clear test
  (`test_registry_clear_clears_helper_referenced_ordersets`) — independent
  (they drive the helper + finalizer + `registry.clear()`, never read the
  bus). *Projection*: statement-1 ledger paragraph + finalizer subpass-3
  docstring.
- **Challenges.** C5 → 1 (the bus); C6 → 1 (the declaration here; writer +
  reader rows follow by name).
- **Owner + lifetime.** Split by responsibility (principle 7): the bus owns
  replay; this leaf owns the ledger object + owner string (the narrowest site
  every legitimate consumer — driver, finalizer — can depend on without
  importing a sibling flavor). Lifetime: process-global mutable set; validity
  key = registry generation (every `registry.clear()` replays the row);
  published at import time; mutated by the driver on each helper call and by
  the callback on clear; invalidated (emptied) on clear — never removed.
  Parked-globals posture inherited from the shared namespace lifecycle
  (materialized input classes stay parked; only ledgers reset).
- **Migration.** None (zero-edit file item): this row already composes the bus
  by name. Consolidation, if any, lives in the holding family item, not here.
- **Distinct behavior.** The ledger is per-family: the filters twin's set +
  `filters.helper_references` row is a sibling member of the same bus family,
  not a duplicate — posit orphaning a `FilterSet` → the filters ledger +
  finalizer filter pass move, this file does not.
- **Behavioral proof.** `static-reviewed` (import-time registration only;
  replay ordering owned by the bus). Rejects "two ledgers drift" (they are
  intentionally disjoint populations under distinct owners).
- **Structural gate.** The orphan-raise oracles above (pre-existing, not new
  gates — no failability run owed by this zero-edit item); the
  `registry.clear()` co-clear is pinned by the clear test.
- **Coupling.** C6 couples to the driver write + finalizer read by import-name;
  a ledger rename moves those two import rows in the same change. Named here so
  the coupling is visible.
- **Freshness.** Target `ed546f9c70d56d73e0d84a029e9e04f27da3934b`,
  `django_strawberry_framework/registry.py` HEAD
  `9cc8bb553fd417fc465809a541769a8383469cda` (worktree `612bea87…` hunt dirt
  in the `TypeRegistry` body — outside the bus contract),
  `django_strawberry_framework/utils/inputs.py` HEAD
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` (worktree `47b2af21…` hunt dirt
  including the driver's guard hunk — the judged body is the HEAD
  validate/record/build triple),
  `django_strawberry_framework/types/finalizer.py` HEAD
  `77fd9a2dd229eb9de5f29188c5058035d3606323` (worktree `35ff5286…` hunt dirt
  in `_field_surface_names` — outside the orphan passage),
  `django_strawberry_framework/filters/__init__.py`
  `86b258186638c96995e31919346f44d7951c65ea`,
  `tests/orders/test_inputs.py` HEAD
  `baf23440b8c1701b70b4c828e29c8eaf87626488` (worktree `a0300a00…` hunt dirt:
  two appended hostile-`__qualname__` tests outside the Decision-11 block —
  the judged oracles are the HEAD block),
  `tests/orders/test_finalizer.py`
  `44a00e8f6a30f9364bd1ff0a983928a19c1e34cf` (clean).
- **Routing.** Member site of verified family `subsystem-clear-lifecycle`
  (member 4 of its census: `orders.helper_references` / this set / one-liner
  `.clear()`): holding item is that family. No new index row owed.

### F3 — Decision-11 leaf parameters (file-local)

- **Contract + variation.** `order_input_type` validates its argument is an
  `OrderSet` subclass (`TypeError` naming the value), records it in the family
  ledger, and returns the ForwardRef-wrapped
  `Annotated[<runtime str>, strawberry.lazy(<module>)]` form the `ForwardRef`
  test pins. Legitimate variation: per-family parameters only (`expected_base`,
  `family_name`, `expected_label`, `ledger`, `input_type_name_for`,
  `module_path`).
- **Sites + roles.** *Body definition*:
  [utils-inputs][utils-inputs]`::build_lazy_input_annotation` (owns validation
  + ledger write + annotation construction; shared with the filters twin).
  *Parameter declaration*: this file's statement 11. *Private feeds*:
  statement 6 (`_input_type_name_for`, `INPUTS_MODULE_PATH` — body-use imports,
  deliberately outside `__all__`). *Sibling parameter declaration*:
  [filters-init][filters-init]`::filter_input_type` (different base, label,
  ledger, module path; same element-type shape). *Oracles*: the four helper
  tests in [test-order-inputs][test-order-inputs] (`ForwardRef` shape,
  `TypeError`, ledger record, idempotency) — independent (they assert literals
  like `"HelperOrderAInputType"` and drive the helper, never read the driver).
  *Consumers*: hand-written resolvers (README + fakeshop `schema.py` modules,
  wrapping as `list[...] | None` per Decision 5) + [connection][connection]'s
  and [list-field][list-field]'s synthesized signatures (function-local
  imports, preserving the lazy-subpackage contract).
- **Challenges.** C7 → 1 (the driver; 0 here); C8 → 1 here (filters twin
  untouched). The pair moves opposite files under opposite changes: shared
  body, independent parameters.
- **Owner + lifetime.** The driver owns the body (existing owner by
  responsibility: the mechanics it single-sites for both set families); this
  leaf owns its six parameter bindings. No stored derivation; no lifetime
  fields owed.
- **Migration.** None (zero-edit item): the consolidation this shape invites
  has already landed (the driver); the leaves are declarations, not copies.
- **Distinct behavior.** Element-type parity with a documented divergence: both
  helpers return the element type; the DIVERGENCE lives at resolver-annotation
  sites (order wraps as `list[...]` per spec-028 Decision 5, filter uses it
  bare because `filter:` is a single object) — never in the helpers.
- **Behavioral proof.** `static-reviewed`. Rejects "the twins duplicate the
  body" (both bodies are one call each to the named driver; the ForwardRef form
  is constructed in exactly one place) and "inlining the driver call duplicates
  the rule" (C7 proves a form change touches one definition).
- **Structural gate.** The `ForwardRef`-in-`__args__` oracle pins the
  load-bearing form (pre-existing, not a new gate — no failability run owed);
  the `TypeError` oracle pins eager validation.
- **Coupling.** None beyond F2's ledger row (the `ledger=` argument names F2's
  set; a ledger rename moves that keyword in the same change as C6).
- **Freshness.** Target `ed546f9c70d56d73e0d84a029e9e04f27da3934b`,
  `django_strawberry_framework/utils/inputs.py` HEAD
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` (dirt as F2),
  `django_strawberry_framework/orders/inputs.py` HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (dirt as F1),
  `django_strawberry_framework/filters/__init__.py`
  `86b258186638c96995e31919346f44d7951c65ea`,
  `django_strawberry_framework/connection.py` HEAD
  `4894f90fb2963a44d25b0eabc649c67d04afa587` (worktree `9c5b8724…` hunt dirt
  at the import block + `_consume_window` / `_consume_fallback` — outside the
  sidecar region, used as consumer evidence only),
  `django_strawberry_framework/list_field.py` HEAD
  `21380eb72364caef0da05ca3ee3f26c0134e3904` (worktree `f979f0d6…` hunt dirt
  in `_validate_*` — outside the consumer region, used as consumer evidence
  only),
  `tests/orders/test_inputs.py` HEAD
  `baf23440b8c1701b70b4c828e29c8eaf87626488` (dirt as F2),
  `docs/README.md` `c32da2366faadee08f40d6a90237cdcdc74e8bc1` (clean),
  `docs/GLOSSARY.md` `d3ef357c26ede6a5bd21d4290b394ade4eb987b4` (clean).

## Defects

None. Every docstring claim checked held: the three-tier export prose (5/5
bound, factory absent, private pair outside `__all__` — all verified against
the import statements + spec-028 Decision 2); the filter-parity clauses
(factory exclusion and metaclass inclusion both verified against the twin's
real surface); the finalizer phase-2.5 prose (matches the subpass-3 docstring:
compare-then-raise-`ConfigurationError`); the element-type + list-wrap idiom
(pinned by oracle + Decision 11); the eager-`TypeError` clause (driver body at
HEAD bytes); the `__all__` membership (5/5 bound, verified against the three
import statements). The axis-6 sweep finds no missing guard: all 5 required
members present, all three omissions carry contract sources. The F1
"leading-`_` flags them private" observation is prose looseness shared with
the spec's own parenthetical, with the mechanics verified — it breaks no
contract row and is therefore not a defect.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding plus a pure delegating wrapper whose body is owned
elsewhere, all bindings resolve through consumer imports on every suite run,
the pinned oracles already execute the wrapper's contract, and the only
instrument used (`ast.parse`) is non-mutating. Sharded / Postgres cells are
inapplicable by construction: the target reaches no database, alias, or
dialect decision.

## Judgment

Zero-edit file item. Three rules traced: two file-local with proving
challenges (F1 manifest, C1-C4/C12; F3 leaf parameters, C7-C8), one routed to
its verified holding family (F2 ledger lifecycle → `subsystem-clear-lifecycle`,
member 4). Three indexed families considered — one routed (F2), two checked
with no surface (`sync-boundary-recourse-wording` via C10, `one-sync-boundary`
by surface absence); three further mechanisms checked fresh with no surface
(C9 set-naming pass-through, C11 lazy-target mixin neither defined nor
re-exported here, F1 nested root-manifest rejection with this leaf's own
contract difference + trigger). Enumeration covers 12/12 statements. No
defects, no pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `ITEM_BASELINE=acfb865e6534aa4265bcbee15a0219672594e256`:
`git diff <baseline> -- django_strawberry_framework/orders/__init__.py` empty
(exit 0); working blob `ed546f9c70d56d73e0d84a029e9e04f27da3934b` equals
`HEAD:django_strawberry_framework/orders/__init__.py` and HEAD `5ee86193` —
target CLEAN, so no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-orders____init__.md`) is a new untracked file, the item's
only output. No `uv run ruff format .` / `ruff check` run (no edits to format;
`.md` is outside ruff format scope; no `.py` scratch created). No shared-tree
pytest run (inspection suffices — see `### Challenges` note; the entry command
authorizes a focused `--no-cov` run only where it could settle a judgment, and
here it could settle nothing). No `docs/dry/temp-tests/` scratch created.
Concurrent dirt (hunt edits across `django_strawberry_framework/`,
`tests/orders/test_inputs.py`, `docs/dry/dry-0_0_15.md`) left untouched; the
`## Owned changes` ledger gains no row from this item. Worker-0 instructions:
(a) tick the plan item `File orders/__init__.py — dry-file-orders____init__.md`
as verified under Run `0.0.15 2026-09-22-5` once Worker 2 agrees; (b) add these
three `## Responsibility index` rows (holding item `File orders/__init__.py`):

| `orders-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/orders/__init__.py`) | `django_strawberry_framework/orders/__init__.py` (+3 owner modules) | File `orders/__init__.py` | file-local |
| `orders-decision-11-leaf-parameters` | `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation` (body; leaf owns its six parameter bindings) | `django_strawberry_framework/orders/__init__.py` | File `orders/__init__.py` | file-local |
| `orders-leaf-vs-root-manifest` | `django_strawberry_framework/orders/__init__.py` (rejection recorded here; durable home spec-028 Decision 2 + leaf docstring) | `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/__init__.py` | File `orders/__init__.py` | rejected |

(F2 needs no new row: verified family `subsystem-clear-lifecycle` already
covers this file as member 4; this artifact records the row-10 contribution.)
No commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md
[dry-clear-lifecycle]: dry-rule-subsystem-clear-lifecycle.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[list-field]: ../../django_strawberry_framework/list_field.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-order-finalizer]: ../../tests/orders/test_finalizer.py
[test-order-inputs]: ../../tests/orders/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Own trace recorded BEFORE opening `## Findings` above; reconciliation follows it.
HEAD confirmed `5ee86193` (`git rev-parse --short HEAD`) before starting — pin holds.
Target read in full (101 lines): leaf docstring, `__future__` boilerplate, five
`from`-imports, ledger state + clear fn + bus row, one `def` (`order_input_type`),
one `__all__` tuple. No branch, no `async def`, no `await`, no `sync_to_async`, no
`__getattr__`, no `warnings`, no `deprecated`, no queryset / transport code (token
sweep empty). Runtime effects are import-time binding, one set object, one bus
registration, one pure delegating call.

Fingerprints re-derived myself (worktree vs `HEAD:`, `5ee86193`): target
`django_strawberry_framework/orders/__init__.py` `ed546f9c` both (CLEAN, 101 lines);
`filters/__init__.py` `86b25818` both; `orders/factories.py` `4f35b66b` both;
package root `0ef72601` both; spec-028 `94a3141c` both;
`tests/orders/test_finalizer.py` `44a00e8f` both; `tests/test_registry.py`
`e330cfb8` both. Hunt-dirtied, traced at HEAD bytes only, never touched:
`orders/base.py` HEAD `4736fda0`, `orders/inputs.py` HEAD `6f6ec946`, `orders/sets.py`
HEAD `6044ab1a`, `registry.py` HEAD `9cc8bb55`, `utils/inputs.py` HEAD `ee31d360`,
`types/finalizer.py` HEAD `77fd9a2d`, `connection.py` HEAD `4894f90f`,
`list_field.py` HEAD `21380eb7`, `filters/inputs.py` HEAD `82b52d97`,
`tests/orders/test_inputs.py` HEAD `baf23440`. Every HEAD pin matches the blob the
verified filters-leaf and `subsystem-clear-lifecycle` artifacts recorded — no drift
on any input this trace relies on.

### Own trace: rules, sites, counts, owners

Three rules re-derived from the target's real surface:

- **R1 (5-name leaf manifest).** Contract: the orders subpackage surface is exactly
  5 names composed by name from their homes (1 from `base.py`, 1 public from
  `inputs.py`, 2 from `sets.py`, `order_input_type` defined here), with `__all__`
  mirroring the re-export bindings in-file; three tiers per spec-028 Decision 2
  (public 4 + advanced-in-`__all__` metaclass + held-out factory). Sites:
  definitions at `django_strawberry_framework/orders/base.py::RelatedOrder`,
  `django_strawberry_framework/orders/inputs.py::Ordering`,
  `django_strawberry_framework/orders/sets.py::OrderSet`,
  `::OrderSetMetaclass`; consumer rows = this file's import lines + tuple;
  oracles = explicit-name consumer imports (`tests/orders/*`, fakeshop
  `orders.py` / `schema.py`, `connection.py` + `list_field.py` call-time imports)
  resolving through this file without reading `__all__`; projections = tier
  prose (leaf docstring, Decision 2, GLOSSARY/usage blocks). Counts: 6th
  primitive → 1 (home module; import line + tuple entry follow); rename
  `OrderSet` → 1 (home); home move (`RelatedOrder` base→sets) → 1 (the move; one
  import line follows); lift Decision 2 (root-export orders symbols) → 0 here
  (root moves, this file does not) — proves separation. Owner I would choose:
  per-symbol home modules (declaration, validation, runtime machinery all live
  there); this file composes by name (principle 6). No stored derivation.
- **R2 (helper-reference ledger lifecycle).** Contract: the
  `_helper_referenced_ordersets` set records every `OrderSet` passed to
  `order_input_type`; `_clear_helper_referenced_ordersets` empties it; the
  `register_subsystem_clear(..., owner="orders.helper_references")` row replays
  it under `registry.clear()`. Sites: declaration = this file statements 8-9
  (ledger + clear fn; bus row = statement 10); lifecycle owner =
  `django_strawberry_framework/registry.py::register_subsystem_clear` bus (owns
  replay, validation, `before_bind` posture); writer =
  `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`
  (`ledger.add` through the passed reference); reader =
  `django_strawberry_framework/types/finalizer.py` phase-2.5 `_bind_ordersets`
  subpass 3 (local import as `helper_ledger`, compare vs
  `Meta.orderset_class`-wired sets, raise `ConfigurationError` for orphans);
  oracles = ledger-membership + idempotency + clear-empties tests in
  `tests/orders/test_inputs.py`, the three orphan-raise tests in
  `tests/orders/test_finalizer.py`, the poisoned-`sys.modules` tolerance row in
  `tests/test_registry.py` — independent (they drive the helper + finalizer +
  registry and spell literals, never read the bus or the driver); projection =
  ledger paragraph + subpass-3 docstring. Counts: bus-contract change → 1 (the
  bus; the register call follows as consumer); ledger rename → 1 (the
  declaration here; driver write + finalizer read + test imports follow by
  name). Owner I would choose: split by responsibility (principle 7) — bus owns
  replay, this leaf owns the ledger object + owner string (narrowest site driver
  + finalizer can depend on without importing a sibling flavor; matches the
  Decision 2 co-location rationale). Lifetime: process-global mutable set;
  validity key = registry generation; published at import; mutated by driver per
  call and by callback on clear; invalidated (emptied) on clear, never removed.
  Routing I would choose: member site of VERIFIED family
  `subsystem-clear-lifecycle` (its census already lists this file among 20
  members and row 4 `orders.helper_references` among 17 adapters) — a
  convergence note, no new index row, no verdict change.
- **R3 (Decision-11 leaf parameters).** Contract: `order_input_type` validates
  its argument is an `OrderSet` subclass (eager `TypeError` naming the value),
  records it in the family ledger (idempotent set write), returns the
  ForwardRef-wrapped `Annotated[<runtime str>, strawberry.lazy(<module>)]`
  element-type form the ForwardRef oracle pins. Sites: body definition =
  `utils/inputs.py::build_lazy_input_annotation` (owns validation + ledger write
  + annotation construction; shared with
  `django_strawberry_framework/filters/__init__.py::filter_input_type`);
  parameter declaration = this file's statement 11 (six bindings:
  `expected_base`, `family_name`, `expected_label`, `ledger`,
  `input_type_name_for`, `module_path`); private feeds = statement 6's
  `INPUTS_MODULE_PATH` + `_input_type_name_for` (body-use, deliberately outside
  `__all__`; every test addresses them via `orders.inputs`); sibling parameter
  declaration = filters twin (different base, label, ledger, module path;
  element-vs-list divergence lives at resolver-annotation sites per Decision 11,
  never in the helpers); oracles = the four helper tests in
  `tests/orders/test_inputs.py` (ForwardRef shape, `TypeError`, ledger record,
  idempotency); consumers = hand-written resolvers (fakeshop schemas) +
  `connection.py` / `list_field.py` function-local imports (lazy-subpackage
  contract). Counts: ForwardRef form change → 1 (the driver; 0 here) — proves
  single ownership; family-label change → 1 here (filters twin untouched) —
  proves per-family parameters. Owner I would choose: driver owns the body, this
  leaf owns its six parameter bindings. No stored derivation.

Matrix discharged myself against the export surface: (1) cross-flavor — target
aggregates ONE flavor from three home modules; every sibling leaf aggregates only
its own flavor (auth/forms/mutations/types/extensions/rest_framework import sweeps)
and the root carries zero orders tokens (grep empty) per Decision 2 grain; the
shared eager-re-export + `__all__` shape is intentional separation, not
duplication; filters twin is a parameterized sibling (opposite change responses).
(2) sync/async — inapplicable with reason: no colored surface (full read + token
sweep); the apply pair lives at `orders/sets.py`; `one-sync-boundary` names that
module, not this leaf; no boundary call here. (3) derived knowledge —
`__all__` mirrors the bindings in one edit region (one definition, not two);
private feeds are body-use only; the input-type NAME is passed through
(`_input_type_name_for` = `set_input_type_name` alias → `type_name_for`), never
re-derived here → `set-type-naming` 0 here. (4) round-trip — no surface: one
author, one direction, no shim. (5) other media — production; contract sources
(spec-028 Decisions 2/5/9/11 + driver/finalizer docstrings); independent oracles
above; projections (docstrings, README/GLOSSARY, spec blocks). (6) omission —
three deliberate omissions each with a Decision 2 source (root exclusion; factory
held out; private feeds out of `__all__`); all 5 required members present, 5/5
bound; no member lacks a required guard. Rejection I would record: consolidating
this manifest into `package-root-public-surface` — contract difference: root =
default recipe every consumer pays at package import, this leaf = family-grain
opt-in with per-primitive inclusion and factory + input-namespace internals held
out, and Decision 2 forbids the root from ever carrying these names (opposite
change responses: C1 moves here only, C4 moves root only); trigger: a decision to
root-export the orders surface or drive every manifest from one shared
driver/validator; durable home: Decision 2 + leaf docstring paragraph 1.

Window-diff attribution (own, hunk-by-hunk): the
`ITEM_BASELINE..worktree` window over package/test/example paths names exactly
`optimizer/nested_fetch.py`, `rest_framework/sets.py`, `routers.py` — all three
hunks are comment rewording plus `try/except BaseException` guard
removal/refinement around `__class__`-consulting interrogations
(`issubclass(type(value), str)`, `isidentifier`/`iskeyword` on exact-`str` keys,
`callable()`), on paths outside this item's scope, in the concurrent hunt's guard
vocabulary, absent from the ledger and cycle baseline. Zero hunks touch
`orders/__init__.py`, `orders/*`, or any oracle this item relies on. Attribution:
all concurrent-external. No scope violation. Item-scoped diff for this item is the
new untracked artifact only; target still clean (no status line, fingerprints
match).

### Reconciliation vs W1 (read after the trace above)

Identical on all three rules, all sites and roles, all shared counts
(C1-C8 re-derived with the same numbers: C1/C2/C3/C5/C6/C8 → 1 each at the
stated owner; C4/C9/C10 → 0 here; C7 → 1 driver / 0 here), and all owners
(per-symbol homes; split bus/leaf for R2; driver body + leaf params for R3).
Four deltas, none structural:

- **C11 wording.** I read the statement-5 `RelatedOrder` row as an arguable
  by-name consumer of the lazy-target-resolution mechanism; W1 records 0 here
  with "neither defines nor re-exports the mixin, so not even a consumer row".
  Count agrees (0); no row owed either way. W1's stricter reading is ENDORSED:
  the leaf names no mixin-family symbol, so no consumer row exists — the
  `RelatedOrder` binding is an R1 row owned at `base.py`.
- **C12.** W1 posits a 7th `Ordering` member → 1 at `inputs.py`, an axis I did
  not posit. Legitimate variation-axis exercise of the enum member of the
  manifest; count verified correct (home moves, leaf row follows). ADOPTED.
- **Oracle-list delta.** I additionally cite the poisoned-`sys.modules`
  tolerance row in `tests/test_registry.py` as F2 evidence; W1's four cited
  oracles (ledger-membership, idempotency, orphan-raise ×3, co-clear) suffice
  for every leaf claim. No gap; the tolerance row stands as supporting evidence.
- **Boilerplate adjective (W2 correction C1, on-record).** The Item-kind block
  says "routed to an open family holding item", but F2's holding family is
  VERIFIED. Stale word (true of the filters twin's run, not this one); the
  operative F2 Routing line already says "verified family", so no finding is
  affected. Corrected here; no W1 edit owed.

### Enumeration check (member-by-member, own instrument)

Own `ast.parse` count of `ast.Module.body`: **12**, matching W1. All 12 map
identically: (1) docstring → prose projection F1/F2/F3; (2) `__future__` →
boilerplate; (3) registry import (1 machinery name) → F2 consumer row; (4)
utils.inputs import (1 machinery name) → F3 consumer row; (5) base import (1
name, verified `RelatedOrder`) → R1/F1; (6) inputs import (3 names, verified
`Ordering` public + `INPUTS_MODULE_PATH` / `_input_type_name_for` body-private)
→ R1 feeds + F1 omission row + F3 feeds; (7) sets import (2 names, verified
`OrderSet` + `OrderSetMetaclass`) → R1/F1; (8) ledger AnnAssign → R2/F2; (9)
clear def → R2/F2; (10) bus row (`orders.helper_references` verified the sole
registration at HEAD — exactly 1 code site + prose mentions) → R2/F2; (11)
`order_input_type` def → R3/F3; (12) `__all__` (5-tuple, verified 1 + 1 + 2 +
helper = 5) → R1/F1. Nothing unassigned; every challenge C1-C12 ends in a
family row, a file-local row, a rejection, or a no-surface routing, as claimed.

### Matrix judgment (each claimed inapplicability judged on its reason)

1. Cross-flavor: AGREE. Replicated the root grep (zero `orders`/`Order` hits)
   and swept every sibling leaf's imports (each aggregates only its own
   flavor); the shared manifest shape is intentional separation per Decision 2
   grain, re-derived with this leaf's own difference, not inherited.
2. Sync/async twins: AGREE. No colored surface (full 101-line read + token
   sweep); apply pair at `orders/sets.py`; `one-sync-boundary` correctly
   no-surface here; no boundary call lives in this file.
3. Derived knowledge: AGREE. `__all__` mirrors the bindings in one edit region;
   private feeds are body-use only (verified: tests import them from
   `orders.inputs`; no in-tree import takes them from the leaf); naming passes
   through the `set_input_type_name` alias to `type_name_for` (W1's HEAD body
   read confirmed), never re-derived; C9/C10 → 0 here with reasons checked.
4. Round-trip: AGREE. One author, one direction; no shim (`warnings` /
   `deprecated` absent).
5. Other media: AGREE. Four media inventoried with the right contract sources
   (Decisions 2/11 + driver/finalizer docstrings; Decisions 5/9 cited where
   their judgments need them), independent oracles, and projections; variation
   counted once at each home (C1-C3).
6. Omission: AGREE. Three omissions each carry the verified Decision 2 source
   (root exclusion; factory held out, absence verified; private feeds out of
   `__all__`); 5/5 required members bound; no member lacks a required guard.

### Counts, roles, oracles, gates, coupling

All definition counts confirmed (C1-C3, C5, C6, C8, C12 → 1 each at the stated
owner; C4, C7-here, C9, C10, C11 → 0 here; C7-driver → 1). Roles confirmed:
homes = definitions; this file = consumer (principle 6); bus = lifecycle owner;
driver = body owner; finalizer = reader; helper/clear/orphan tests = independent
oracles (they spell literals — `"HelperOrderAInputType"`, `TypeError` on `int`,
ledger membership, orphan names — and drive the helper + finalizer + registry,
never read the driver body or the manifest); explicit-name consumer imports =
oracles resolving through the file without reading `__all__`; docstrings / spec
/ README / GLOSSARY = projections. No oracle rewritten — zero edits anywhere.
Gates: F1 gate-absence ENDORSED (replicated the `tests/orders/` grep: only
`Meta.fields = "__all__"` tokens; standing in is every explicit-name import
failing loudly as `ImportError`; no bespoke manifest pin owed per principle 9);
F2 orphan-raise + co-clear oracles ENDORSED as pre-existing pins; F3
ForwardRef-in-`__args__` + `TypeError` oracles ENDORSED as pre-existing pins of
the load-bearing form and eager validation. Coupling: C6 + F3 `ledger=` keyword
coupling named in both findings — marked so neither half lands alone. CORRECT.

### Rejections, fingerprints, dirt, pending

F1 nested rejection carries its contract difference (default recipe vs
Decision-2 three-tier family-grain opt-in; opposite change responses C1 vs C4
proved) + trigger (root-export the orders surface, or one shared
driver/validator) + durable home (Decision 2 + docstring paragraph 1), compared
fresh vs the filters twin. ENDORSED. Fingerprints re-hashed against the tree,
18/18 full-hash match (target `ed546f9c` both; HEAD pins `4736fda0` /
`6f6ec946` / `6044ab1a` / `9cc8bb55` / `ee31d360` / `77fd9a2d` / `4894f90f` /
`21380eb7` / `baf23440`; clean `4f35b66b` / `0ef72601` / `86b25818` / `94a3141c`
/ `44a00e8f` / `e330cfb8` / `c32da236` / `d3ef357c`; all 9 short dirt hashes
match). Nothing stale. Dirt spot-checks confirm W1's load-bearing
characterizations: the driver's worktree hunk sits inside
`build_lazy_input_annotation` (`{set_class!r}` → `{_safe_arg_repr(set_class)}`
+ guard arms) and changes no count (the clean leaf passes the same six
parameters by keyword); the test dirt is two appended hostile-input tests at
line 979+, outside the judged Decision-11 block. `## Pending execution` = None:
CORRECT — all proofs `static-reviewed`, no `execution-deferred` entry;
sharded/Postgres inapplicable-by-construction ENDORSED (the target reaches no
database, alias, or dialect decision). No `pending execution` flag on the tick.

### Artifact-shape judgment (form vs DRY.md contract)

The shape satisfies the contract; ZERO corrections owed. The DRY.md artifact
contract requires title, `Status:`, `Run:`, System trace, Verification
(Matrix/Enumeration/Challenges), Findings, Defects, Pending execution, Judgment —
all present. F1/F2/F3 labels: DRY.md mandates no label scheme, and the verified
filters twin uses F1/F2/F3 identically — convention, not deviation. The finding
record fields (contract, sites+roles, challenges, owner+lifetime, migration,
distinct behavior, proof, gate, coupling, freshness; rejection difference +
trigger + durable home) are complete in all three findings. `## Implementation
(Worker 1)` on a zero-edit item carrying the diff record + index rows: identical
to the verified filters-twin and subsystem-family artifacts (the required
Worker-0 transcription rows must live somewhere, and no `## Index rows`
section exists in the DRY.md contract). The link block is the standard scaffold
(all 10 canonical headers present), not nonstandard HTML. The single stale
adjective ("open family" boilerplate) is corrected on-record above (C1).

### F2 convergence-vs-amendment judgment

LAWFUL CONVERGENCE NOTE, not an amendment. The verified family already lists
this file among its 20 members and row 4 `orders.helper_references` among its
17 adapters; W1 re-litigates nothing (family C3/C4/C5, census, triggers, and
verdict untouched), proposes no consolidation, and claims only that this file's
statement-10 bus row is that census's member 4 — exactly the routing the
filters twin recorded when the family was open. A file item may converge onto
an existing family; this one does so without altering the verified verdict.
Worker 0 transcribes NOTHING for F2: no new index row (the family row already
covers this file); the file-item tick is the only plan change F2 implies.

### AGENTS.md prose check

Reference-style links with the 10-group block present; `path::Symbol` citations
throughout (zero raw `path:NN`; statement-# table is the enumeration
instrument, permitted); no process provenance beyond the required diff record;
no banned tokens (feedback/author/provenance sweep empty); no test-tier
obligation (file item, no behavior added — existing oracles sit at the mandated
`tests/orders/` + `tests/test_registry.py` tiers); concurrent dirt untouched
(sibling `orders/*.py`, all hunt-dirtied inputs, and `tests/orders/*` never
edited — HEAD bytes only). Ruff: W1 touched no `.py` (artifact is `.md`,
excluded — `ruff format --check` on it is a no-op pass); my own scratch
`docs/dry/temp-tests/dry-file-orders____init__-w2/census.py` (4 KB, read-only
AST census) passes `ruff format --check` + `ruff check` green after the scoped
fix pass. No pytest run (zero-edit; AGENTS.md bars runs unless asked). No
commit, no CHANGELOG, no version touch. No mutating proof was needed, so no
`$TMPDIR/dry-ws` workspace was created (no `__file__`/DB record owed).

### Defects (Worker 2)

None. Docstring claims re-checked: three-tier export prose (5/5 bound, factory
absent, private pair outside `__all__`); filter-parity clauses (factory
exclusion + metaclass inclusion both verified against the twin's real surface;
in-tree metaclass consumers use the `orders.sets` submodule path — verified by
HEAD census); finalizer phase-2.5 prose (matches subpass-3: local import,
compare, raise); element-type + list-wrap idiom (oracle + Decision 11); eager
`TypeError` (driver body at HEAD). The "leading-`_` flags them private"
looseness (`INPUTS_MODULE_PATH` has no underscore) breaks no contract row —
mechanics verified, phrasing shared with the spec's own parenthetical — so
W1's observation-not-defect stands. Axis-6 sweep finds no missing guard.

### Judgment (Worker 2)

`Status: verified`, no pending execution. Three rules traced: two file-local
with proving challenges (F1 manifest C1-C4/C12; F3 leaf parameters C7-C8), one
lawfully converged onto its verified holding family (F2 ledger lifecycle →
`subsystem-clear-lifecycle`, member 4). Three indexed families considered — one
routed, two checked with no surface; three further mechanisms checked fresh
(C9, C11, F1 nested root-manifest rejection with this leaf's own difference +
trigger). Enumeration 12/12. One on-record prose correction (C1), nothing
structural. No defects, no pending, zero edits. Worker-0 instructions: (a) tick
the plan item `File orders/__init__.py — dry-file-orders____init__.md` as
verified under Run `0.0.15 2026-09-22-5`; (b) add these three
`## Responsibility index` rows verbatim (holding item
`File orders/__init__.py`):

| `orders-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/orders/__init__.py`) | `django_strawberry_framework/orders/__init__.py` (+3 owner modules) | File `orders/__init__.py` | file-local |
| `orders-decision-11-leaf-parameters` | `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation` (body; leaf owns its six parameter bindings) | `django_strawberry_framework/orders/__init__.py` | File `orders/__init__.py` | file-local |
| `orders-leaf-vs-root-manifest` | `django_strawberry_framework/orders/__init__.py` (rejection recorded here; durable home spec-028 Decision 2 + leaf docstring) | `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/__init__.py` | File `orders/__init__.py` | rejected |

(F2 needs no new row: verified family `subsystem-clear-lifecycle` already
covers this file as member 4.) After ticking, remove by explicit path:
`docs/dry/temp-tests/dry-file-orders____init__-w2/` (4 KB, one read-only census).
No commit.
