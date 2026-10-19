# DRY review: `django_strawberry_framework/filters/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an open
family holding item, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Small target (114 lines, FRESH — no prior cycle record names it beyond a
passing blob mention in the auth artifact's orientation reads): the filtering
subsystem's leaf manifest plus its Decision-11 consumer-helper ledger. It
DEFINES one behavior (the `filter_input_type` thin wrapper over an already
single-sited driver) and one piece of state (the helper-reference ledger +
its clear callback + bus registration); everything else is by-name
composition: 13 re-export bindings from `base.py`, 2 from `sets.py`, 2
body-private imports from `inputs.py`, and the 16-member `__all__` mirror.
No branching, no queryset, no transport, no sync/async machinery, no
`__getattr__`, no deprecation shim: runtime effects are import-time binding,
one set object, one bus registration, and one pure function body that
delegates.

Connected code read for judgment, outside the item:
[filters-base][filters-base] (head + `Filter` import line + `validate_range`
definition site), [filters-sets][filters-sets] (head),
[filters-inputs][filters-inputs] (head: alias table,
`INPUTS_MODULE_PATH`, `_input_type_name_for`),
[orders-init][orders-init] (full: the Decision-11 twin leaf),
[orders-inputs][orders-inputs] (helper-ledger clear passage),
[utils-inputs][utils-inputs]`::build_lazy_input_annotation` (full driver
body + docstring), [registry][registry]`::register_subsystem_clear`
(contract), [finalizer][finalizer] phase-2.5 subpass-3 passage (orphan-check
consumer), [sets-mixins][sets-mixins]`::LazyRelatedClassMixin` (definition
site), the package root [pkg-root][pkg-root] (full; confirms no filter
import and the Decision-2-shaped omission), [connection][connection]
sidecar-signature builder (function-local consumer import + ledger prose),
sibling leaf manifests [auth-init][auth-init] (head) and
[extensions-init][extensions-init] (shape precedent), the contract source
[spec-027][spec-027] Decision 2 passage (subpackage import path, read),
oracles [test-filter-inputs][test-filter-inputs] (Decision-11 block, read)
and [test-filter-finalizer][test-filter-finalizer] (import block + orphan
block via grep), consumer imports across `tests/` + `examples/` + `docs/`
(grep population), and prose projections [docs-readme][docs-readme] +
[glossary][glossary] (usage blocks via grep).

Excluded with reason: every other indexed family whose files-covered list
was scanned for this path — only `subsystem-clear-lifecycle` and
`lazy-related-class-resolution` list `filters/__init__.py`, and both are
routed below (F1 consumer row, F2 family row; C9, C11 end with 0
definitions here). `set-type-naming`, `sync-boundary-recourse-wording`,
`one-sync-boundary`, `drf-soft-export-guard` were judged on their mechanisms
against this target's REAL surface and found to have none here (Matrix axes
1-3, C9-C10). The concurrent dirt (`connection.py` hunk — working blob
`3c4d5dcb…` vs HEAD; `tests/test_connection.py`; staged
`tests/utils/test_querysets.py` +31; `docs/bug_hunt/bug_hunt-0_0_15.md`;
`docs/dry/dry-0_0_15.md`) was left untouched; the only concurrent-dirty file
read was [connection][connection] lines 1935-1989, a region outside the
cursor-guard hunk. None of the dirt is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE flavor
(filters) from three home modules. Sibling leaves each aggregate only their
own flavor (auth/orders/forms/mutations/types/extensions); the package root
is the sole cross-flavor aggregator and deliberately carries no filter
symbol (full read of [pkg-root][pkg-root]: zero filter imports — the
spec-027 Decision 2 posture). The shared eager-re-export + `__all__` shape
across leaves is intentional separation per contract (subpackage grain vs
default recipe), not duplication — the same verdict the auth and extensions
artifacts record for their leaves, re-derived fresh here with this leaf's
own difference. Considered family `package-root-public-surface`: rejected,
see F1. The orders twin ([orders-init][orders-init]`::order_input_type`)
is the same SHAPE with per-family parameters (different base, label,
ledger, module path) — C7/C8 prove opposite change responses, so it is a
parameterized sibling, not a second definition (F3).

**2. Sync/async twins.** Target defines no colored pair: no `async def`,
no `await`, no `sync_to_async` (full 114-line read). The apply pair
(`FilterSet.apply_sync` / `apply_async`) is owned at
[filters-sets][filters-sets]. Considered families `one-sync-boundary`
(files-covered names `filters/sets.py`, not this leaf) and
`subsystem-clear-lifecycle` (files-covered names this leaf — routed, F2):
checked, no twin surface here. No boundary call lives in this file.

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the
13 + 2 re-export bindings in the SAME file (one edit region, not two
definitions). `INPUTS_MODULE_PATH` + `_input_type_name_for` are imported
for body use only — absent from `__all__`, and every test addresses them
through the `filters.inputs` submodule path, never the leaf — so no second
public surface exists. The input-type NAME derivation is not re-derived
here: the leaf passes `_input_type_name_for` through to the driver, which
delegates to `set_input_type_name` → `ClassBasedTypeNameMixin.type_name_for`.
Considered family `set-type-naming`: checked, no surface — this file holds
no naming rule (C9 ends here with 0 definitions; do not inherit).
Considered family `sync-boundary-recourse-wording`: checked, no surface —
no recourse string, no permission hook lives here (`sync_pipeline_recourse`
is a write-pipeline wording at `utils/querysets.py`, naming flavors, never
filters; C10 ends here with 0 definitions; do not inherit).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack,
build/parse halves. Import binding → `__all__` membership → `import *`
binding is one direction with a single author (this file), not two halves
that can drift apart. No deprecation shim exists (no `warnings`, no
`deprecated` token in the full read). No surface.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (bindings + manifest + ledger + wrapper);
authoritative contract sources (spec-027 Decision 2 for the export grain;
the driver/finalizer docstrings for the helper + orphan mechanics);
independent oracles (the four `filter_input_type` behavior tests spelling
`ForwardRef`/`TypeError`/ledger/idempotency without reading the owner, the
orphan-raise tests, explicit-name consumer imports resolving through this
file without reading `__all__`); projections (leaf docstring, README +
GLOSSARY usage blocks, spec code blocks). A new primitive moves its home
definition once; this file's rows follow by name (C1-C3).

**6. Enforcement by omission.** Three deliberate omissions, each with a
contract source: the whole filter surface stays out of the package root
(spec-027 Decision 2, read at [spec-027][spec-027]) — F1;
`FilterArgumentsFactory` stays out of the leaf (spec-027 contents bullet
lists `__init__.py` without it; the orders twin documents the same
convention) — F1; `INPUTS_MODULE_PATH` / `_input_type_name_for` stay out
of `__all__` (leading-underscore body-use; every consumer uses the
submodule path) — F1. Every member the contract requires is present: all
16 re-exported names bound, `__all__` names exactly those 16, nothing else
bound at module scope except the private ledger pair and imported
machinery. No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **12 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (subsystem paragraph + `Filter`-identity clause + orphan-check prose + usage shape) | (none) | prose projection, F1/F2/F3 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from ..registry import register_subsystem_clear` | 1 name (machinery) | F2 consumer row |
| 4 | `from ..utils.inputs import build_lazy_input_annotation` | 1 name (machinery) | F3 consumer row |
| 5 | `from .base import (...)` | 13 names | R1, F1 |
| 6 | `from .inputs import INPUTS_MODULE_PATH, _input_type_name_for` | 2 names, body-private | R1-absent-by-design, F1/F3 |
| 7 | `from .sets import FilterSet, FilterSetMetaclass` | 2 names | R1, F1 |
| 8 | `_helper_referenced_filtersets: set[...] = set()` | ledger state | R2, F2 |
| 9 | `def _clear_helper_referenced_filtersets` | 1 name | R2, F2 |
| 10 | `register_subsystem_clear(...)` call | bus row, owner `filters.helper_references` | R2, F2 |
| 11 | `def filter_input_type` | 1 name | R3, F3 |
| 12 | `__all__ = (...)` | 16-member tuple | R1, F1 |

Rules: R1 filters leaf manifest (statements 5-7 + 12 + usage prose; 16 =
13 base + 2 sets + the helper); R2 helper-reference ledger lifecycle
(statements 3, 8-10 + ledger prose); R3 Decision-11 leaf wrapper
(statements 4, 6, 11; statement 6's pair is R3's private parameter feed).
Six indexed families considered (`package-root-public-surface`,
`subsystem-clear-lifecycle`, `lazy-related-class-resolution`,
`set-type-naming`, `sync-boundary-recourse-wording`, `one-sync-boundary`):
one rejected with contract difference + trigger (F1), one routed as the
holding family (F2), four checked with no surface (Matrix axes 1-3, C9-C11).
Two new file-local index rows are named for Worker 0 (`F1`, `F3`); F2 needs
no new row (its holding family row already covers this file).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new primitive | expose a 14th base primitive (e.g. a new filter class) | **1** (the definition at `base.py`; this file's import line + `__all__` entry are consumer rows that follow by name; README blocks are projections) | independent |
| C2 | R1 rename | rename `FilterSet` → `DjangoFilterSet` | **1** (`sets.py`; import line + tuple entry + helper annotation here follow) | independent |
| C3 | R1 home move | move `FilterSet` from `sets.py` to `base.py` | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R1 omission lift | lift Decision 2 (root-export filter symbols) | **0 here** (root gains import lines; this file does not move) | independent — proves separation |
| C5 | R2 bus-contract change | change the `register_subsystem_clear` contract (e.g. require `before_bind`) | **1** ([registry][registry] bus; this file's row-10 call follows only as a consumer of the signature) | independent |
| C6 | R2 ledger rename | rename `_helper_referenced_filtersets` → `_helper_filtersets` | **1** (the declaration at statement 8; the driver write + finalizer read + test imports follow by name — listed as Coupling, not counted) | independent |
| C7 | R3 form change | change the ForwardRef form (e.g. drop `strawberry.lazy`) | **1** ([utils-inputs][utils-inputs]`::build_lazy_input_annotation`; both leaves unchanged) | independent — proves single ownership, 0 here |
| C8 | R3 wording change | change the filter family label (`"a FilterSet"` → other) | **1 here** (leaf parameters; the orders twin + driver untouched) | independent — proves per-family parameters |
| C9 | `set-type-naming` check | change the `Foo` → `FooFilterInputType` derivation | **0 here** (owned at `sets_mixins.py::ClassBasedTypeNameMixin` via `set_input_type_name`; this file passes the function through) | no surface — do not inherit |
| C10 | `sync-boundary-recourse-wording` check | change the sync-misuse recourse sentence | **0 here** (owned at `utils/querysets.py::sync_pipeline_recourse`; no recourse token lives here) | no surface — do not inherit |
| C11 | `lazy-related-class-resolution` check | change lazy-target resolution semantics | **0 here** (mixin defined at `sets_mixins.py::LazyRelatedClassMixin`; this file's statement-5 row is a by-name consumer) | consumer only — route, do not inherit |
| C12 | R1 upstream rename | upstream renames `django_filters.Filter` | **1** (`base.py` import line; this file's row + docstring clause follow) | independent |

No executable proof was run: the target has no runtime semantics beyond
import-time binding plus a pure delegating wrapper whose body is owned
elsewhere (no branches, no awaits, no queryset/transport code), so there is
no behavior an execution could distinguish that the cited oracles do not
already pin. The read-only `ast.parse` enumeration above ran in the shared
tree (non-mutating; the workspace recipe authorizes mutating proofs, of
which this item has none). Every binding is exercised by consumer imports
on every suite run (`tests/filters/*`, `connection.py`'s call-time import,
fakeshop app modules). All claims below are therefore `static-reviewed`;
there is no `execution-deferred` proof and no `docs/dry/temp-tests/`
scratch was created — inspection suffices, and a probe could distinguish
nothing.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — filters leaf manifest (file-local)

- **Contract + variation.** The filters subpackage's public surface is
  exactly 16 names, each composed by name from its home module (13 from
  `base.py`, 2 from `sets.py`, `filter_input_type` defined here), with
  `__all__` mirroring the re-export bindings in-file. Legitimate
  variation: set membership only (a 14th primitive adds one import line +
  one tuple entry in this file).
- **Sites + roles.** *Definitions*: [filters-base][filters-base] (13
  names incl. `Filter`, `validate_range`, and the `LazyRelatedClassMixin`
  re-export of [sets-mixins][sets-mixins]`::LazyRelatedClassMixin`);
  [filters-sets][filters-sets]`::FilterSet`,
  `::FilterSetMetaclass`. *Consumer rows*: this file's statements 5, 7,
  12. *Consumers-as-oracles*: explicit-name imports (`tests/filters/*`,
  fakeshop `filters.py`/`schema.py` modules, [connection][connection]'s
  call-time import) — independent (they resolve the homes through this
  file without reading the manifest). *Projections*: statement-1 usage
  shape, Decision 2 code block, README + GLOSSARY usage blocks.
  *Consumer of a second family*: the `LazyRelatedClassMixin` row is a
  by-name consumer of open family `lazy-related-class-resolution`
  (definition at [sets-mixins][sets-mixins]; C11 → 0 here).
- **Challenges.** C1, C2, C3, C12 → 1 definition each (the home module);
  C4 → 0 here.
- **Owner + lifetime.** Per-symbol home modules (existing owners, chosen
  by responsibility: each class's declaration, validation, and runtime
  machinery all live there; no narrower owner this file's consumers could
  depend on exists). This file is a consumer (principle 6: compose by
  name). No stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owners stand; a new
  primitive adds its definition plus one consumer row here.
- **Distinct behavior.** The manifest intentionally covers only the 16 —
  `FilterArgumentsFactory` excluded (spec-027 contents bullet lists this
  file without it; the orders twin states the same convention),
  `INPUTS_MODULE_PATH` / `_input_type_name_for` imported-but-not-exported
  (statement 6 feeds R3's body; every test addresses them via
  `filters.inputs`), root excluded (Decision 2). The `Filter`-identity
  clause ("IS `django_filters.Filter` itself… deliberately shadows") is
  verified prose: [filters-base][filters-base] binds `Filter` by plain
  upstream import, so the shadowing is a namespace placement, not a fork.
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows
  its owner" (bindings are by-name imports; `filters.FilterSet is
  filters.sets.FilterSet` by construction of the import system) and "star
  binding leaks a 17th name" (`__all__` names exactly the 16 bound
  re-export names; grep finds no other public binding in this file).
- **Structural gate.** No exact-`__all__` oracle exists for this leaf
  (grep over `tests/filters/`: every `__all__` hit is the unrelated
  `Meta.fields = "__all__"` token) — the same standing as the auth and
  extensions leaves, whose artifacts record the identical observation.
  Standing in: every consumer imports names explicitly, so a dropped
  binding fails loudly (`ImportError`) at use sites on every suite run.
  Noted as an observation, not a defect: no contract row requires a
  manifest pin, and a bespoke existence test per leaf manifest would
  violate the gate-only economy (principle 9).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/filters/__init__.py`
  `86b258186638c96995e31919346f44d7951c65ea` (matches the blob the auth
  artifact recorded — target untouched since that pass),
  `django_strawberry_framework/filters/base.py`
  `ba52351c284425336262ae6c2b82b262f6586fc0`,
  `django_strawberry_framework/filters/sets.py`
  `4ab65a26b0ccf56f7f40f4938282bba9690673d1`,
  `django_strawberry_framework/sets_mixins.py`
  `ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3`,
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `django_strawberry_framework/auth/__init__.py`
  `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
  `django_strawberry_framework/extensions/__init__.py`
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `docs/SPECS/spec-027-filters-0_0_8.md`
  `ca463bdda7426f833949a9428f58bf0b7f4117b9`.
  Searched population for a second manifest of the 16-name set: whole
  package + `tests/` + `examples/` + `docs/` (grep `from
  django_strawberry_framework.filters import` / `from ..filters import`:
  only home-submodule paths, this file, consumer imports, and prose
  mentions). Excluded on strength of body:
  `filters/inputs.py::FieldSpec` et al. (submodule-internal aliases, not
  the leaf surface) and `mutations/sets.py` machinery (different
  subsystem).
- **Rejection (nested).** Considered: consolidate the leaf manifest into
  indexed family `package-root-public-surface` (same eager-re-export +
  `__all__` shape — the auth and extensions items rejected the same
  family for their leaves with difference + trigger; this leaf is the
  same SHAPE but not the same difference, compared fresh). Contract
  difference here: the root manifest is the default recipe every consumer
  pays for at package import, while this leaf is the
  family-grain opt-in whose membership rule is per-primitive inclusion
  with the factory and input-namespace internals deliberately held out —
  and Decision 2 forbids the root from ever carrying these names because
  it would widen the surface for consumers who never filter. Posit
  root-exporting `FilterSet` → the root moves and this file does not
  (C4); posit adding a 14th primitive → this file moves and the root
  does not (C1); posit un-rooting an enforcement pair → the root moves
  and neither leaf does. Different responsibility, different population,
  opposite reasons to change: same shape, not the same rule. Trigger to
  reconsider: a decision to root-export the filter surface, or to drive
  every subpackage manifest from one shared driver/validator, would make
  the sites one rule. Durable home: spec-027 Decision 2 (already states
  the grain) + this file's docstring paragraph 1.

### F2 — helper-reference ledger lifecycle (family row: `subsystem-clear-lifecycle`)

- **Contract + variation.** The `_helper_referenced_filtersets` set
  records every `FilterSet` passed to `filter_input_type`; the
  `_clear_helper_referenced_filtersets` callback empties it; the
  `register_subsystem_clear(..., owner="filters.helper_references")` row
  replays that callback under `registry.clear()`. Legitimate variation:
  per-family ledger identity only (the orders twin owns a disjoint set +
  owner string; neither may share the other's).
- **Sites + roles.** *Declaration*: this file's statements 8-9 (ledger +
  clear fn). *Lifecycle owner*: [registry][registry]`::register_subsystem_clear`
  bus (owns replay, validation, `before_bind` posture). *Writer*:
  [utils-inputs][utils-inputs]`::build_lazy_input_annotation` (`ledger.add`
  through the passed reference). *Reader*: [finalizer][finalizer] phase-2.5
  subpass 3 (compares against `Meta.filterset_class`-wired sets, raises
  `ConfigurationError` for orphans). *Oracles*: ledger-membership tests
  (`test_filter_input_type_records_filterset_into_helper_referenced_set`,
  idempotency test) + orphan-raise tests in
  [test-filter-finalizer][test-filter-finalizer] — independent (they drive
  the helper + finalizer, never read the bus). *Projection*: statement-1
  ledger paragraph + finalizer subpass-3 docstring.
- **Challenges.** C5 → 1 (the bus); C6 → 1 (the declaration here; writer +
  reader rows follow by name).
- **Owner + lifetime.** Split by responsibility (principle 7): the bus
  owns replay; this leaf owns the ledger object + owner string (the
  narrowest site every legitimate consumer — driver, finalizer — can
  depend on without importing a sibling flavor). Lifetime: process-global
  mutable set; validity key = registry generation (every `registry.clear()`
  replays the row); published at import time; mutated by the driver on
  each helper call and by the callback on clear; invalidated (emptied) on
  clear — never removed. Parked-globals posture inherited from the shared
  namespace lifecycle (materialized input classes stay parked; only
  ledgers reset).
- **Migration.** None (zero-edit file item): this row already composes
  the bus by name. Consolidation, if any, lives in the holding family
  item, not here.
- **Distinct behavior.** The ledger is per-family: the orders twin's set
  + `orders.helper_references` row is a sibling member of the same bus
  family, not a duplicate — posit orphaning an `OrderSet` → the orders
  ledger + finalizer order pass move, this file does not.
- **Behavioral proof.** `static-reviewed` (import-time registration only;
  replay ordering owned by the bus). Rejects "two ledgers drift" (they
  are intentionally disjoint populations under distinct owners).
- **Structural gate.** The orphan-raise oracles above (pre-existing, not
  new gates — no failability run owed by this zero-edit item); the
  `registry.clear()` co-clear is pinned by the finalizer clear tests.
- **Coupling.** C6 couples to the driver write + finalizer read by
  import-name; a ledger rename moves those two import rows in the same
  change. Named here so the coupling is visible.
- **Freshness.** Target `86b258186638c96995e31919346f44d7951c65ea`,
  `django_strawberry_framework/registry.py`
  `9cc8bb553fd417fc465809a541769a8383469cda`,
  `django_strawberry_framework/utils/inputs.py`
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`,
  `django_strawberry_framework/types/finalizer.py`
  `77fd9a2dd229eb9de5f29188c5058035d3606323`,
  `django_strawberry_framework/orders/__init__.py`
  `ed546f9c70d56d73e0d84a029e9e04f27da3934b`,
  `django_strawberry_framework/orders/inputs.py`
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516`,
  `tests/filters/test_inputs.py`
  `77d637c52044a5688b3fca51ebd3b5f46e02b473`,
  `tests/filters/test_finalizer.py`
  `8365a1323b4bd6c81339754f3b2cf24f556db293`.
- **Routing.** Member site of open family `subsystem-clear-lifecycle`
  (its files-covered list already names this file): holding item is that
  family. No new index row owed.

### F3 — Decision-11 leaf parameters (file-local)

- **Contract + variation.** `filter_input_type` validates its argument is
  a `FilterSet` subclass (`TypeError` naming the value), records it in
  the family ledger, and returns the ForwardRef-wrapped
  `Annotated[<runtime str>, strawberry.lazy(<module>)]` form the
  `ForwardRef` test pins. Legitimate variation: per-family parameters
  only (`expected_base`, `family_name`, `expected_label`, `ledger`,
  `input_type_name_for`, `module_path`).
- **Sites + roles.** *Body definition*:
  [utils-inputs][utils-inputs]`::build_lazy_input_annotation` (owns
  validation + ledger write + annotation construction; shared with the
  orders twin). *Parameter declaration*: this file's statement 11.
  *Private feeds*: statement 6 (`_input_type_name_for`,
  `INPUTS_MODULE_PATH` — body-use imports, deliberately outside
  `__all__`). *Sibling parameter declaration*:
  [orders-init][orders-init]`::order_input_type` (different base, label,
  ledger, module path, element-vs-single wrapping prose). *Oracles*: the
  four helper tests in [test-filter-inputs][test-filter-inputs]
  (`ForwardRef` shape, lazy module path, ledger record, idempotency,
  triple `TypeError`) — independent (they assert literals like
  `"MyFilterInputType"` and the module-path constant from the submodule,
  never read the driver). *Consumers*: hand-written resolvers (README +
  fakeshop schemas) + [connection][connection]'s synthesized signature
  (function-local import, preserving the lazy-subpackage contract).
- **Challenges.** C7 → 1 (the driver; 0 here); C8 → 1 here (orders twin
  untouched). The pair moves opposite files under opposite changes:
  shared body, independent parameters.
- **Owner + lifetime.** The driver owns the body (existing owner by
  responsibility: the mechanics it single-sites for both set families);
  this leaf owns its six parameter bindings. No stored derivation; no
  lifetime fields owed.
- **Migration.** None (zero-edit item): the consolidation this shape
  invites has already landed (the driver); the leaves are declarations,
  not copies.
- **Distinct behavior.** Element-type parity with a documented divergence:
  the filter helper's return is used bare (`filter:` is a single object)
  while the orders twin's return is wrapped (`list[...]` per spec-028
  Decision 5) — the divergence lives at resolver-annotation sites, never
  in the helpers.
- **Behavioral proof.** `static-reviewed`. Rejects "the twins duplicate
  the body" (both bodies are one call each to the named driver; the
  ForwardRef form is constructed in exactly one place) and "inlining the
  driver call duplicates the rule" (C7 proves a form change touches one
  definition).
- **Structural gate.** The `ForwardRef`-in-`__args__` oracle pins the
  load-bearing form (pre-existing, not a new gate — no failability run
  owed); the `TypeError` oracle pins eager validation.
- **Coupling.** None beyond F2's ledger row (the `ledger=` argument
  names F2's set; a ledger rename moves that keyword in the same change
  as C6).
- **Freshness.** Target `86b258186638c96995e31919346f44d7951c65ea`,
  `django_strawberry_framework/utils/inputs.py`
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`,
  `django_strawberry_framework/filters/inputs.py`
  `82b52d97b8f8b26d2846df24dabcabb793507c87`,
  `django_strawberry_framework/orders/__init__.py`
  `ed546f9c70d56d73e0d84a029e9e04f27da3934b`,
  `django_strawberry_framework/connection.py` working
  `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` (concurrent cursor-guard
  dirt; the read region sits outside its hunk and is used as consumer
  evidence only),
  `tests/filters/test_inputs.py`
  `77d637c52044a5688b3fca51ebd3b5f46e02b473`,
  `docs/README.md`
  `6b8cfbe81ef38e4a390994ae96ea995937523ac4`,
  `docs/GLOSSARY.md`
  `bcc99607a5557eeb1602d25676e4fb4e5b877da5`.

## Defects

None. Every docstring claim checked held: the `Filter`-identity clause
(`base.py` binds `Filter` by plain upstream import — placement, not a
fork); the finalizer phase-2.5 prose (matches the finalizer's subpass-3
docstring: compare-then-raise-`ConfigurationError`); the ForwardRef idiom
(pinned by oracle); the `__all__` membership (16/16 bound, verified
against the three import statements). The axis-6 sweep finds no missing
guard: all 16 required members present, all three omissions carry contract
sources.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding plus a pure delegating wrapper whose body is
owned elsewhere, all bindings resolve through consumer imports on every
suite run, the pinned oracles already execute the wrapper's contract, and
the only instrument used (`ast.parse`) is non-mutating.

## Judgment

Zero-edit file item. Three rules traced: two file-local with proving
challenges (F1 manifest, C1-C4/C12; F3 leaf parameters, C7-C8), one
routed to its open holding family (F2 ledger lifecycle →
`subsystem-clear-lifecycle`). Six indexed families considered — one
rejected with this leaf's own contract difference + trigger
(`package-root-public-surface`, F1 nested rejection, compared fresh
against the auth/extensions leaf rejections rather than inherited), one
routed (F2), four checked with no surface (`lazy-related-class-resolution`
consumer-only via C11, `set-type-naming` via C9,
`sync-boundary-recourse-wording` via C10, `one-sync-boundary` by surface
absence). Enumeration covers 12/12 statements. No defects, no pending
execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (design-equivalent zero-edit result submitted for
verification). Item-scoped diff vs
`5e8d2f16b3dd5bdaf235a6288f22c2f5aaa9f302`:
`git diff <baseline> -- django_strawberry_framework/filters/__init__.py`
empty (exit 0); working blob
`86b258186638c96995e31919346f44d7951c65ea` equals
`HEAD:django_strawberry_framework/filters/__init__.py` and HEAD `9031cb3d`
— target CLEAN, so no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-filters____init__.md`) is a new untracked file, the
item's only output. No `uv run ruff format .` / `ruff check` run (no edits
to format; `.md` is outside ruff format scope). No shared-tree pytest run.
No `docs/dry/temp-tests/` scratch created (inspection suffices — see
`### Challenges` note). Concurrent dirt listed in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) plus the other untracked `dry-file-*.md`
artifacts were left untouched; the `## Owned changes` ledger (walker D1
fix + 2 live test files) gains no row from this item. Worker-0
instructions: (a) tick the plan item
`File filters/__init__.py — dry-file-filters____init__.md` as verified
under Run `0.0.15 2026-09-18-1` once Worker 2 agrees; (b) add these two
`## Responsibility index` rows (both `file-local`, holding item
`File filters/__init__.py`):

| `filters-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/filters/__init__.py`) | `django_strawberry_framework/filters/__init__.py` (+2 owner modules) | File `filters/__init__.py` | file-local |
| `filters-decision-11-leaf-parameters` | `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation` (body; leaf owns its six parameter bindings) | `django_strawberry_framework/filters/__init__.py` | File `filters/__init__.py` | file-local |

(F2 needs no new row: open family `subsystem-clear-lifecycle` already
covers this file; this artifact records the row-10 contribution.) No
commit.

## Independent verification (Worker 2)

Own trace recorded BEFORE opening `## Findings` above; reconciliation follows it.
Target read in full (114 lines): leaf docstring, `__future__` boilerplate,
four `from`-imports, ledger state + clear fn + bus row, one `def`
(`filter_input_type`), one `__all__` tuple. No branch, no `async def`, no
`await`, no `sync_to_async`, no `__getattr__`, no `warnings`, no queryset /
transport code. Runtime effects are import-time binding, one set object, one
bus registration, one pure delegating call.

### Own trace: rules, sites, counts, owners

Three rules re-derived from the target's real surface:

- **R1 (16-name leaf manifest).** Contract: the filters subpackage surface is
  exactly 16 names composed by name from their homes (13 from `base.py`, 2
  from `sets.py`, `filter_input_type` defined here), with `__all__` mirroring
  the re-export bindings in-file. Sites: definitions at
  `django_strawberry_framework/filters/base.py` (13 names incl. `Filter`,
  `validate_range`, and the `LazyRelatedClassMixin` re-export of
  `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin`) and
  `django_strawberry_framework/filters/sets.py::FilterSet`,
  `::FilterSetMetaclass`; consumer rows = this file's import lines + tuple;
  oracles = explicit-name consumer imports (`tests/filters/*`,
  fakeshop `filters.py` / `schema.py`, `django_strawberry_framework/connection.py`
  call-time import at `::_sidecar_signature` region); projections = usage
  blocks (leaf docstring, spec-027 Decision 2 code block, README + GLOSSARY).
  Counts: 14th primitive → 1 (home module; import line + tuple entry follow);
  rename `FilterSet` → 1 (home); home move `sets.py` → `base.py` → 1 (the
  move; one import line follows); lift Decision 2 (root-export filters) → 0
  here (root moves, this file does not); upstream `django_filters.Filter`
  rename → 1 (`base.py` line). Owner I would choose: per-symbol home modules
  (declaration, validation, runtime machinery all live there); this file
  composes by name (principle 6). No stored derivation.
- **R2 (helper-reference ledger lifecycle).** Contract: the
  `_helper_referenced_filtersets` set records every `FilterSet` passed to
  `filter_input_type`; `_clear_helper_referenced_filtersets` empties it; the
  `register_subsystem_clear(..., owner="filters.helper_references")` row
  replays it under `registry.clear()`. Sites: declaration = this file
  statements 8-9; lifecycle owner =
  `django_strawberry_framework/registry.py::register_subsystem_clear` bus;
  writer = `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`
  (`ledger.add` through the passed reference); reader =
  `django_strawberry_framework/types/finalizer.py` phase-2.5 subpass 3
  (compare vs `Meta.filterset_class`-wired sets, raise `ConfigurationError`
  for orphans); oracles = ledger-membership + idempotency tests and
  orphan-raise tests in `tests/filters/test_inputs.py` +
  `tests/filters/test_finalizer.py`; projection = ledger paragraph + subpass-3
  docstring. Counts: bus-contract change → 1 (the bus; row-10 call follows);
  ledger rename → 1 (declaration here; driver write + finalizer read follow by
  name). Owner I would choose: split by responsibility (principle 7) — bus
  owns replay, this leaf owns the ledger object + owner string (narrowest site
  driver + finalizer can depend on without importing a sibling flavor).
  Lifetime: process-global mutable set; validity key = registry generation;
  published at import; mutated by driver per call and by callback on clear;
  invalidated (emptied) on clear, never removed.
- **R3 (Decision-11 leaf parameters).** Contract: `filter_input_type`
  validates `FilterSet` subclass (`TypeError` naming the value), records in
  the family ledger, returns ForwardRef-wrapped
  `Annotated[<runtime str>, strawberry.lazy(<module>)]`. Sites: body
  definition = `utils/inputs.py::build_lazy_input_annotation` (shared with
  `django_strawberry_framework/orders/__init__.py::order_input_type`);
  parameter declaration = this file's statement 11 (six bindings:
  `expected_base`, `family_name`, `expected_label`, `ledger`,
  `input_type_name_for`, `module_path`); private feeds = statement 6
  (`_input_type_name_for`, `INPUTS_MODULE_PATH`, body-use, outside `__all__`);
  sibling declaration = orders twin (different base, label, ledger, module
  path); oracles = four helper tests in `tests/filters/test_inputs.py`
  (ForwardRef shape, lazy module path, ledger record, idempotency, triple
  `TypeError`); consumers = hand-written resolvers + connection sidecar
  function-local import. Counts: ForwardRef form change → 1 (the driver; 0
  here); family-label change → 1 here (orders twin untouched). Owner I would
  choose: driver owns the body, this leaf owns its six parameter bindings. No
  stored derivation.

Reconciliation vs W1: identical on all three rules, all sites and roles, all
twelve counts (C1-C12 re-derived with the same numbers: C1/C2/C3/C6/C8/C12 →
1 each at the stated owner; C4/C9/C10/C11 → 0 here; C5 → 1 bus; C7 → 1
driver), and all owners (per-symbol homes; split bus/leaf for R2; driver body
+ leaf params for R3). No difference to reconcile on substance.

### Enumeration check (member-by-member, own instrument)

Own `ast.parse` count of `ast.Module.body`: **12**, matching W1. Member
mapping agrees: (1) docstring Expr → prose projection (F1/F2/F3); (2)
`from __future__` → boilerplate; (3) `from ..registry import` (1 machinery
name) → F2 consumer row; (4) `from ..utils.inputs import` (1 machinery name)
→ F3 consumer row; (5) `from .base import` (13 names, verified by own count:
`ArrayFilter`, `ArrayFilterMethod`, `Filter`, `GlobalIDFilter`,
`GlobalIDMultipleChoiceFilter`, `LazyRelatedClassMixin`, `ListFilter`,
`ListFilterMethod`, `RangeField`, `RangeFilter`, `RelatedFilter`,
`TypedFilter`, `validate_range`) → R1/F1; (6) `from .inputs import` (2 names,
body-private) → R3 feeds + F1 omission row; (7) `from .sets import` (2 names)
→ R1/F1; (8) `_helper_referenced_filtersets` AnnAssign → R2/F2; (9)
`def _clear_helper_referenced_filtersets` → R2/F2; (10)
`register_subsystem_clear(...)` Expr → R2/F2 bus row
(`filters.helper_references` verified as the sole owner string under
`django_strawberry_framework/` outside prose); (11) `def filter_input_type`
→ R3/F3; (12) `__all__` AnnAssign (16-tuple, verified by own literal eval:
13 + 2 + helper = 16) → R1/F1. Nothing unassigned. Every challenge C1-C12
ends in a family row, a file-local row, or a no-surface routing, as claimed.

### Matrix judgment (each claimed inapplicability judged on its reason)

1. Cross-flavor: AGREE. Verified each sibling leaf aggregates only its own
   flavor and the root carries zero filter imports (grep over
   `django_strawberry_framework/__init__.py`: no `Filter` hit; root imports
   only connection / error-policy / extensions-error+resource / forms /
   list-field / mutations / optimizer / permissions / relay / resource-policy
   / scalars / schema / types). The shared eager-re-export + `__all__` shape
   is intentional separation per contract (subpackage grain vs default
   recipe), not duplication — the same verdict the auth and extensions
   artifacts record for their leaves, here re-derived with this leaf's own
   Decision-2 difference (see Rejections), not inherited.
2. Sync/async twins: AGREE. Target holds no `async def` / `await` /
   `sync_to_async` (full 114-line read). The apply pair
   (`FilterSet.apply_sync` / `apply_async`) is owned at `filters/sets.py`;
   `one-sync-boundary` (files-covered names `filters/sets.py`, not this leaf)
   and `subsystem-clear-lifecycle` (names this leaf — routed F2) correctly
   handled. No boundary call lives here.
3. Derived knowledge: AGREE. `__all__` mirrors the bindings in one edit
   region — one definition, not two. `INPUTS_MODULE_PATH` +
   `_input_type_name_for` are body-use only (absent from `__all__`; every
   consumer addresses them via `filters.inputs`), so no second public surface.
   Name derivation is passed through (`_input_type_name_for` →
   `set_input_type_name` → `ClassBasedTypeNameMixin.type_name_for`), not
   re-derived. `set-type-naming` (C9 → 0 here) and
   `sync-boundary-recourse-wording` (C10 → 0 here; no recourse token in file)
   correctly no-surface with reasons checked against the file's real verbs.
4. Round-trip: AGREE. Binding → `__all__` membership → `import *` binding is
   one author, one direction; no encode/decode halves, no deprecation shim
   (`warnings` / `deprecated` absent from full read).
5. Other media: AGREE. Four media inventoried (production; contract sources
   spec-027 Decision 2 + driver/finalizer docstrings; independent oracles;
   projections). Variation counted once at the home definition (C1-C3).
6. Omission: AGREE. Three omissions each carry a contract source verified
   in-tree: root exclusion (spec-027 Decision 2, read at
   `docs/SPECS/spec-027-filters-0_0_8.md`); `FilterArgumentsFactory` held out
   (spec contents bullet + orders-twin convention prose); private feeds held
   out of `__all__` (leading-underscore + submodule-path consumers). All 16
   required members present (16/16 bound, verified by literal eval), nothing
   else bound at module scope except the private ledger pair + imported
   machinery. No member lacks a required guard.

### Counts, roles, oracles

All definition counts confirmed (C1-C3, C5, C6, C8, C12 → 1 each at the
stated owner; C4, C7-here, C9, C10, C11 → 0 here; C7-driver → 1). Roles
confirmed: homes = definitions; this file = consumer (principle 6); bus =
lifecycle owner; driver = body owner; finalizer = reader; the four
`filter_input_type` tests + orphan tests = independent oracles (they spell
literals — `"MyFilterInputType"`, module-path constant from the SUBMODULE,
`ForwardRef` shape, `TypeError` on `42` / non-class / `None` — and drive the
helper + finalizer, never read the driver body or the manifest); consumer
explicit-name imports = oracles resolving through the file without reading
`__all__`; docstrings / README / GLOSSARY / spec blocks = projections. No
oracle rewritten — zero production edits and zero test edits; the diff below
is empty.

### Equivalence, zero-edit, routing

Item-scoped diff confirmed empty by fresh run:
`git diff 5e8d2f16b3dd5bdaf235a6288f22c2f5aaa9f302 -- django_strawberry_framework/filters/__init__.py`
prints nothing (exit 0); working blob `86b258186638c96995e31919346f44d7951c65ea`
equals `HEAD:django_strawberry_framework/filters/__init__.py` and HEAD is
`9031cb3d`; `wc -l` = 114. No behavior changed, so principle-8 equivalence
holds vacuously; inspection-only proof is ADEQUATE here — the target's only
runtime effects are import-time binding plus a pure delegating wrapper whose
body is owned elsewhere (no short-circuit order, no exception-shape choice
beyond the driver's `TypeError`, no query/transaction/cancellation axis
exists by construction), the shape DRY.md expressly clears for inspection
("import moves, body composed by name"), every binding resolves through
consumer imports on each suite run, and the pinned oracles already execute
the wrapper's contract. No scratch probe created; for this leaf a probe could
distinguish nothing. The read-only `ast.parse` enumeration ran in the shared
tree (non-mutating; the workspace recipe authorizes mutating proofs, of which
this item has none). Coverage + assignment validated (12/12 statements home;
C1-C12 each end in a file-local row, the F1 rejection, the F2 family routing,
or a no-surface check). DB / sharded / Postgres cells are inapplicable by
construction: the target reaches no database, alias, or dialect decision.
Routings judged: `package-root-public-surface` → rejection ENDORSED (own
difference + trigger, compared fresh vs auth/extensions — see below);
`subsystem-clear-lifecycle` → family routing ENDORSED (its files-covered list
already names this file; row-10 is the member site); `lazy-related-class-resolution`
→ consumer-only ENDORSED (C11 → 0 here, statement-5 row is by-name use);
`set-type-naming`, `sync-boundary-recourse-wording`, `one-sync-boundary` →
no-surface ENDORSED (each reason checked against the file's real verbs, none
present; nothing inherited). Two new file-local index rows (F1, F3) ENDORSED;
F2 needs no new row — correctly noted.

### Rejections, fingerprints, gates, pending, coupling

F1 nested rejection carries its contract difference (root = default recipe
every consumer pays at package import; this leaf = family-grain opt-in with
per-primitive inclusion and factory + input-namespace internals held out; and
Decision 2 forbids the root from ever carrying these names — opposite change
responses C1 vs C4 proved) + trigger (root-export the filter surface, or
drive every manifest from one shared driver/validator) + durable home
(spec-027 Decision 2 + leaf docstring para 1). Compared fresh vs the
auth-leaf difference (Decision-3 structural `django.contrib.auth` import
avoidance) and the extensions-leaf difference (per-extension recipe status:
debug out, error/resource in) — same SHAPE, three different differences, none
inherited. ENDORSED. Fingerprints re-hashed against the working tree, 18/18
match: target `86b25818`, `filters/base.py` `ba52351c`, `filters/sets.py`
`4ab65a26`, `sets_mixins.py` `ad8987ea`, package root `0ef72601`, `auth/__init__.py`
`6bc3c4a5`, `extensions/__init__.py` `dc3ebdc2`, spec-027 `ca463bdd`,
`registry.py` `9cc8bb55`, `utils/inputs.py` `ee31d360`, `types/finalizer.py`
`77fd9a2d`, `orders/__init__.py` `ed546f9c`, `orders/inputs.py` `6f6ec946`,
`filters/inputs.py` `82b52d97`, `tests/filters/test_inputs.py` `77d637c5`,
`tests/filters/test_finalizer.py` `8365a132`, `docs/README.md` `6b8cfbe8`,
`docs/GLOSSARY.md` `bcc99607`. The connection working blob `3c4d5dcb` is
concurrent dirt outside this item's paths; the read region (sidecar-signature
builder) sits outside its hunk and is used as consumer evidence only.
Nothing stale. Gates: F1 gate-absence ENDORSED — no exact-`__all__` oracle
exists for this leaf (grep over `tests/filters/`: only `Meta.fields =
"__all__"` tokens), same standing as the auth/extensions leaves; standing in
is every explicit-name consumer import failing loudly as `ImportError` on
every run, so no bespoke manifest pin is owed (principle-9 gate-only
economy); F2 orphan-raise + ledger-membership oracles ENDORSED as
pre-existing pins (not new gates, so no failability run owed by this
zero-edit item); F3 ForwardRef-in-`__args__` + `TypeError` oracles ENDORSED as
pre-existing pins of the load-bearing form and eager validation. Each gate's
negative control holds: drop a binding → `ImportError` at use sites; bypass
the bus → orphan/clear tests diverge; hand-copy the driver body →
behavioral oracles still pass (proving they check behavior, not identity),
while a form change at the copy alone changes nothing (proving single
ownership). `## Pending execution` absent: CORRECT, no `execution-deferred`
proof exists. Coupling: C6 + F3 `ledger=` keyword coupling to driver write +
finalizer read named in both findings — marked so neither half lands alone.
CORRECT.

### AGENTS.md prose check

Item diff empty → no format/lint surface (no `ruff format` / `ruff check`
owed; `.md` outside ruff scope); no pytest run owed (zero-edit, and AGENTS.md
bars runs unless asked); no commit, no CHANGELOG, no version touch.
Artifact: reference-style links with the 10-group link-definitions block present; `path::Symbol` citations throughout (raw `path:NN`
occurrences, if any, are permitted: `docs/dry/dry-*.md` are per-cycle
scratchpad artifacts that close with their cycle); statement-# table is an
enumeration instrument, not a source ref; no process provenance beyond the
required item-scoped diff record; no test-tier obligation (no behavior added,
no fixture needed — existing oracles sit at the mandated `tests/filters/`
tier); concurrent dirt (`django_strawberry_framework/connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, sibling
`dry-file-*.md` artifacts) untouched and outside this item's paths.

### Defects (Worker 2)

None. Docstring claims re-checked: `Filter`-identity clause holds (`base.py`
binds `Filter` by plain upstream import — placement, not a fork); finalizer
phase-2.5 prose matches the subpass-3 docstring (compare-then-raise
`ConfigurationError`); ForwardRef idiom pinned by oracle; `__all__` 16/16
bound verified by literal eval. Axis-6 sweep finds no missing guard.

### Judgment (Worker 2)

`Status: verified`, no pending execution. Three rules traced: two file-local
with proving challenges (F1 manifest C1-C4/C12; F3 leaf parameters C7-C8),
one routed to its open holding family (F2 ledger lifecycle →
`subsystem-clear-lifecycle`). Six indexed families considered — one rejected
with this leaf's own difference + trigger, one routed, four checked with no
surface. Enumeration 12/12. No defects, no pending, zero edits. Worker-0
instructions: (a) tick the plan item
`File filters/__init__.py — dry-file-filters____init__.md` as verified under
Run `0.0.15 2026-09-18-1`; (b) add these two `## Responsibility index` rows
(both `file-local`, holding item `File filters/__init__.py`):

| `filters-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/filters/__init__.py`) | `django_strawberry_framework/filters/__init__.py` (+2 owner modules) | File `filters/__init__.py` | file-local |
| `filters-decision-11-leaf-parameters` | `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation` (body; leaf owns its six parameter bindings) | `django_strawberry_framework/filters/__init__.py` | File `filters/__init__.py` | file-local |

(F2 needs no new row: open family `subsystem-clear-lifecycle` already covers
this file.) No commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[connection]: ../../django_strawberry_framework/connection.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-filter-finalizer]: ../../tests/filters/test_finalizer.py
[test-filter-inputs]: ../../tests/filters/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
