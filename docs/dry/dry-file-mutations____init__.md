# DRY review: `django_strawberry_framework/mutations/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an open
family holding item, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Small target (36 lines, FRESH — no prior cycle record names it beyond passing
blob mentions in the auth/forms/filters leaf artifacts): the write-side leaf
manifest. It DEFINES nothing behavioral — four re-export bindings composing
one public name each by name from four home modules, plus the 4-member
typed `__all__` mirror and a docstring stating the six-module map (spec-036
Decision 4: the `inputs` / `sets` / `resolvers` / `fields` quartet plus
`permissions.py` for Decision-15 write-auth and `operations.py` for canonical
operation descriptors) plus the public-surface path (four-symbol surface;
eager re-export + typed `__all__` matching the
[forms-`__init__`][forms-init] package-marker shape). No logic, no branching,
no guard, no `__getattr__`, no ledger, no queryset, no transport, no
sync/async machinery: the only runtime effect is import-time binding.

Connected code read for judgment, outside the item:
[mutations-operations][mutations-operations] (full docstring + `OPERATION_CREATE`
/ `OPERATION_UPDATE` / `OPERATION_DELETE` / `OPERATION_FORM` descriptors +
`get_operation_descriptor` / `operation_takes_id` / `operation_takes_data`
predicates, verified by grep), [mutations-inputs][mutations-inputs]
(docstring + `FieldError` / `materialize_mutation_input_class` /
`build_payload_type`, verified by grep),
[mutations-sets][mutations-sets] (docstring + `DjangoMutation` /
`make_meta_validating_metaclass` / `_ValidatedMutationMeta` /
`bind_mutations`, verified by grep),
[mutations-permissions][mutations-permissions] (docstring +
`DjangoModelPermission`, verified by grep),
[mutations-resolvers][mutations-resolvers] (docstring +
`run_write_pipeline_sync` / `make_resolver_entries`, verified by grep),
[mutations-fields][mutations-fields] (`DjangoMutationField` factory
definition, verified by grep), the package root [pkg-root][pkg-root] (full;
confirms the `from .mutations import` 4-name block + the four `__all__`
entries + the debug-omission lines), the shape-match twin
[forms-`__init__`][forms-init] (full 30-line read: eager re-export + typed
`__all__`, no helper), the seal consumer
[auth-mutations][auth-mutations] (import block: `from ..mutations.sets import`
`DjangoMutation` / `_validate_permission_classes` /
`make_declaration_registry` / `register_mutation as
record_mutation_declaration` — submodule path, never the leaf; the
`make_meta_validating_metaclass` mirror clause, read), the contract source
[spec-036][spec-036] Decisions 4, 5, 15 (read), oracles
[test-init][test-init] (four-symbol surface comment + root exact-tuple pin +
leaf-vs-root `is` identity rows, read), and `tests/mutations/*` consumer
imports (grep population).

Excluded with reason: every other indexed family whose files-covered list
touches `mutations/` was judged on its mechanism against this target's REAL
surface and found to have none here (see Matrix axes 1-3 and Challenges
C6-C10); the concurrent dirt was left untouched; none of it is in this
item's paths. The `mutations/fields.py` working hunk (+60/-17 vs HEAD, work
`8c60a5c6…` vs HEAD `cf518361…`) is external concurrent work outside the
item: the leaf's `fields.py` bullet was verified against the factory
definition, which the working tree still carries (`def DjangoMutationField(`
at working line 301), and the bullet claims the factory's ownership, not its
body.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE flavor
(mutations) from four home modules. Sibling leaves each aggregate only their
own flavor; the package root is the sole cross-flavor aggregator, so there
is no second cross-flavor export table to drift. Considered family
`package-root-public-surface`: rejected, see F1.

**2. Sync/async twins.** Target defines no colored pair: no `def`, no
`await`, no `sync_to_async` (full 36-line read; the single `async` token is
docstring prose in the `resolvers.py` bullet). The write sync/async
twinship (`run_write_pipeline_sync` + single-`sync_to_async` async path via
`make_resolver_entries`) is owned at
[mutations-resolvers][mutations-resolvers]. Considered families
`one-sync-boundary`, `shared-write-skeleton` (+ `shared-write-entry-factory`),
`related-object-visibility-recheck`, `sync-boundary-recourse-wording`:
checked, no surface — this file holds no boundary call, no decoder, no
recourse string (C8 ends here with 0 definitions; do not inherit).
`subsystem-clear-lifecycle` (files-covered names `mutations/inputs.py` +
`mutations/sets.py`, not this leaf): checked, no surface — this file
registers no clear callback and holds no ledger (C7 ends here with 0
definitions).

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the
four import bindings in the SAME file (one edit region, not two
definitions). The input-type NAME derivation is not re-derived here: no
naming rule lives in this file. Considered families `set-type-naming`,
`converter-table-per-surface-ownership`: checked, no surface — this file
holds no naming rule and no converter table (C9 ends here with 0
definitions; do not inherit). Considered family `drf-soft-export-guard`:
checked, no surface — no lazy `__getattr__`, no soft-dependency table, no
hint string lives here (C10 ends here with 0 definitions).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. Import binding → `__all__` membership → `import *` binding is one
direction with a single author (this file), not two halves. No surface.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (bindings + manifest); authoritative contract
sources ([spec-036][spec-036] Decisions 4-5-15); projections (in-file
docstring, [tree][tree] mutations rows, [glossary][glossary] anchors);
independent oracles (the root exact-tuple pin + the four leaf-vs-root `is`
identity rows in [test-init][test-init], explicit-name consumer imports in
`tests/mutations/*`). A new public symbol moves its home definition once;
this file plus the root follow by name (C1). Counted once, at the home
module.

**6. Enforcement by omission.** One deliberate omission set with a contract
source: only the four Decision-5 (+Rev3 fourth-symbol) names are
re-exported — operation descriptors (`OPERATION_CREATE` et al.),
input/payload generators (`build_mutation_input`, `build_payload_type`),
the declaration registry + `bind_mutations`, the permission walk
(`run_permission_classes`), and the resolver entries stay on their
submodule paths (Decision 5 names exactly the four-symbol surface;
[test-init][test-init] calls it "complete"). Every member the contract
requires is present: all four symbols bound, `__all__` names exactly those
four. No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the working file, counting `ast.Module.body`
members — **7 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (subsystem paragraph + six module-role bullets + public-surface paragraph) | (none) | prose projection, F1/F2 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from .fields import DjangoMutationField` | 1 name | R1, F1 |
| 4 | `from .inputs import FieldError` | 1 name | R1, F1 |
| 5 | `from .permissions import DjangoModelPermission` | 1 name | R1, F1 |
| 6 | `from .sets import DjangoMutation` | 1 name | R1, F1 |
| 7 | `__all__: tuple[str, ...] = (...)` | 4-member tuple | R1, F1 |

Rules: R1 mutations leaf manifest (statements 3-7 + public-surface prose);
R2 six-module map prose (statement 1 paragraphs 1-2, Decision-4 mirror
shape). Eleven indexed families considered
(`package-root-public-surface`, `sealed-authorization-source`,
`subsystem-clear-lifecycle`, `shared-write-skeleton` (+ entry factory),
`one-sync-boundary`, `related-object-visibility-recheck`,
`sync-boundary-recourse-wording`, `set-type-naming`,
`converter-table-per-surface-ownership`, `drf-soft-export-guard`): one
rejected with contract difference + trigger (F1), one routed as checked
member-adjacent with no surface here (seals, C6), the rest checked with no
surface (Matrix axes 1-3, C7-C10). No existing family name is reused for a
finding; two new file-local index rows are named for Worker 0 (`F1`, `F2`).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new symbol | expose a 5th leaf name (e.g. surface `bind_mutations` or an operation descriptor) | **1** (the definition at its home module; this file's import line + `__all__` entry plus the root's import line + `__all__` entry + oracle rows are consumer rows that follow by name) | independent |
| C2 | R1 rename | rename `DjangoMutation` → `DjangoModelMutation` | **1** (home definition; two lines here + root lines + consumer imports follow) | independent |
| C3 | R1 home move | move `DjangoModelPermission` out of `permissions.py` | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R1 un-root | root stops exporting the four (leaf stays) | **0 here** (root import + `__all__` + pin/identity oracles move; this file does not) | independent — proves separation |
| C5 | R2 module-role change | change what `operations.py` owns (e.g. new descriptor kind) | **0 here** (that module moves; this file's bullet becomes stale prose, a projection, not a definition) | independent — proves projection |
| C6 | seal check | change the slot/head seal contract (`_ValidatedMutationMeta` / `make_meta_validating_metaclass`) | **0 here** (owned at [mutations-sets][mutations-sets]; [auth-mutations][auth-mutations] consumes via the `..mutations.sets` submodule path and mirrors — never the leaf) | no surface — route to holding family |
| C7 | `subsystem-clear-lifecycle` check | change the clear-bus contract | **0 here** (bus at `registry.py`; rows live in `mutations/inputs.py` + `mutations/sets.py`, none here — full read: zero `register_subsystem_clear` in this file) | no surface — do not inherit |
| C8 | pipeline/visibility/recourse check | change the write-pipeline boundary worker, relation visibility, or the sync-misuse recourse sentence | **0 here** (skeleton at [mutations-resolvers][mutations-resolvers]; decoders there; recourse at `utils/querysets.py::sync_pipeline_recourse`; no pipeline/decoder/recourse token lives here) | no surface — do not inherit |
| C9 | naming/converter check | change the input-type naming derivation or the scalar table | **0 here** (naming via `sets_mixins.py::ClassBasedTypeNameMixin`; table at `types/converters.py`; this file holds neither) | no surface — do not inherit |
| C10 | laziness conversion | convert the leaf to a lazy `__getattr__` table | **0 exist** (no table, no `__getattr__` in this file); the conversion would be a NEW rule owned here | independent — proves no second site |

No executable proof was run: the target has no runtime semantics beyond
import-time binding (no branches, no awaits, no queryset/transport code), so
there is no behavior an execution could distinguish. The read-only
`ast.parse` enumeration above ran in the shared tree (non-mutating; the
workspace recipe authorizes mutating proofs, of which this item has none).
Every binding is exercised by consumer imports on every suite run
(`tests/mutations/*`, `tests/base/test_init.py`, fakeshop suites). All
claims below are therefore `static-reviewed`; there is no
`execution-deferred` proof and no `docs/dry/temp-tests/` scratch was
created — inspection suffices, and a probe could distinguish nothing. No
shared-tree pytest run.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — mutations leaf manifest (file-local)

- **Contract + variation.** The mutations subpackage's public surface is
  exactly four names, each composed by name from its home module
  (`DjangoMutationField` from [mutations-fields][mutations-fields],
  `FieldError` from [mutations-inputs][mutations-inputs],
  `DjangoModelPermission` from
  [mutations-permissions][mutations-permissions], `DjangoMutation` from
  [mutations-sets][mutations-sets]), with `__all__` mirroring the bindings
  in-file. Legitimate variation: set membership only (a 5th name adds one
  import line + one tuple entry in this file, plus consumer rows at the
  root).
- **Sites + roles.** *Definitions*: [mutations-sets][mutations-sets]
  `::DjangoMutation`, [mutations-inputs][mutations-inputs] `::FieldError`,
  [mutations-permissions][mutations-permissions] `::DjangoModelPermission`,
  [mutations-fields][mutations-fields] `::DjangoMutationField` (factory
  function, PascalCase per the `DjangoConnectionField` /
  `DjangoNodeField` parity note). *Consumer rows*: this file's statements
  3-7; the package root [pkg-root][pkg-root] `from .mutations import`
  block + four `__all__` entries (second-layer consumer, pinned by the
  root's exact-tuple oracle). *Oracles*:
  [test-init][test-init] exact-tuple pin (spells the tuple without reading
  this file) + four leaf-vs-root `is` identity rows (resolve through this
  file without reading the manifest) — independent, never rewritten to
  read the owner they check. *Projections*: statement-1 public-surface
  paragraph, Decision 5 code block, [tree][tree] + [glossary][glossary]
  blocks.
- **Challenges.** C1, C2, C3 → 1 definition each (the home module); C4 →
  0 here.
- **Owner + lifetime.** Per-symbol home modules (existing owners, chosen
  by responsibility: each class's/factory's declaration, `Meta`
  validation, and machinery all live there; no narrower owner this file's
  consumers could depend on exists). This file is a consumer (principle 6:
  compose by name). No stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owners stand; a new symbol
  adds its definition plus one consumer row here (plus the root's consumer
  row).
- **Distinct behavior.** The manifest intentionally covers only the four —
  descriptors, generators, registry + bind, permission walk, and resolver
  entries stay on submodule paths (Decision 5 four-symbol surface, Matrix
  axis 6).
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows
  its owner" (bindings are by-name imports; `mutations.DjangoMutation is
  mutations.sets.DjangoMutation` by construction of the import system)
  and "star binding leaks a 5th name" (`__all__` names exactly the four;
  full read finds no other binding in this file).
- **Structural gate.** No exact-`__all__` oracle exists for this leaf
  (grep over `tests/mutations/`: imports are explicit-name or submodule
  paths; no `__all__` assertion, no `import *`) — the same standing as
  the auth/extensions/filters/forms leaves. Standing in: every consumer
  imports the four names explicitly, so a dropped binding fails loudly
  (`ImportError`) at use sites on every suite run; the root's exact-tuple
  pin + four identity rows additionally pin all four names one layer up.
  Noted as an observation, not a defect: no contract row requires a
  manifest pin, and a bespoke existence test per leaf manifest would
  violate the gate-only economy (principle 9).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/mutations/__init__.py`
  `9a5683e91457b1a47e795de8b5fbd9db48ca1039` (work == HEAD),
  `django_strawberry_framework/mutations/operations.py`
  `16223c6b8a477bec61da690d08f1c1a01125d8ec`,
  `django_strawberry_framework/mutations/inputs.py`
  `fc4420475f404297822d7d94bee7bdd275700803`,
  `django_strawberry_framework/mutations/sets.py`
  `cffa29e52002e1cfef94a032366524fb69c9d258`,
  `django_strawberry_framework/mutations/permissions.py`
  `54f770ae5aa1238327246cd2dcb141e8aac14965`,
  `django_strawberry_framework/mutations/resolvers.py`
  `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`,
  `django_strawberry_framework/mutations/fields.py` HEAD
  `cf518361d7884b8b71550cb6b73bff0c1a64549e` (work
  `8c60a5c6deb43bf45c49ec31292195262b5a5ff2` is external concurrent dirt,
  outside this item's paths; the factory definition the bullet claims
  still stands in the working tree),
  `django_strawberry_framework/forms/__init__.py`
  `a76a4f797414e90b102eaca2598314ed6ba4b47c`,
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `django_strawberry_framework/auth/mutations.py`
  `dbe64995b87240b87a1d5119f46cc42c7cab646f` (work == HEAD),
  `tests/base/test_init.py`
  `4cc121057689409213beb5ec31772130cdacb975`,
  `docs/SPECS/spec-036-mutations-0_0_11.md`
  `5d79ac8b7297b175f4316c40ddb2e49d857fdcc9`.
  Searched population for a second manifest of the 4-name set: whole
  package + `tests/` + `examples/` + `docs/` (grep `DjangoMutationField`:
  only the home factory, this file, the root consumer, and prose
  mentions). Excluded on strength of body: `mutations/sets.py`
  `::register_mutation` (the declaration-registry recorder, a different
  contract from the rider factory — shared token, not shared rule) and
  `auth/mutations.py::register_mutation` (the rider factory, different
  subsystem).
- **Rejection (nested).** Considered: consolidate the leaf manifest into
  indexed family `package-root-public-surface` (same eager-re-export +
  `__all__` shape — the auth, extensions, filters, and forms items
  rejected the same family for their leaves, each with its OWN difference
  + trigger; this leaf is the same SHAPE but not the same difference,
  compared fresh, nothing inherited). Contract difference here: the root
  manifest is the cross-flavor default recipe every consumer pays for at
  package import (39-entry `__all__`, exact-tuple pin + identity oracles),
  while this leaf is the single-flavor 4-name manifest aggregating FOUR
  homes (unlike the forms leaf's single home) that IS root-exported per
  Decision 5 + Rev3 — so a new symbol moves BOTH files as layered
  consumers (C1) while un-rooting the four moves ONLY the root (C4), and
  root-side changes to unrelated symbols move ONLY the root. Different
  responsibility (flavor grain vs cross-flavor recipe), different
  population (4 vs 39), different gates: same shape, not the same rule.
  Trigger to reconsider: a decision to drive every subpackage manifest
  from one shared driver/validator, or to root-export the whole leaf
  wholesale by construction (e.g. `from .mutations import *`), would make
  the sites one rule. Durable home: [spec-036][spec-036] Decision 5
  (already states the root export) + this file's public-surface paragraph.

### F2 — six-module map prose (file-local)

- **Contract + variation.** The docstring maps the six sibling modules to
  their responsibilities in the spirit of `filters/` / `orders/` per
  Decision 4 (operations / inputs / sets / permissions / resolvers /
  fields), and states the public-surface path (four-symbol surface; eager
  re-export + typed `__all__` matching the [forms-`__init__`][forms-init]
  shape; filters / orders add Decision-11 helpers this file does not
  need). No legitimate variation while Decisions 4-5-15 stand; a module
  rename or role change revises prose, not behavior.
- **Sites + roles.** *Contract sources*: [spec-036][spec-036] Decisions 4
  (module split + operations vocabulary), 5 (four-symbol surface), 15
  (write-auth class). *Mechanism definitions*:
  [mutations-operations][mutations-operations] (descriptors +
  `get_operation_descriptor` / `operation_takes_id` /
  `operation_takes_data`), [mutations-inputs][mutations-inputs]
  (generators + `FieldError` + `build_payload_type`),
  [mutations-sets][mutations-sets] (base + metaclass + `Meta` validation +
  `bind_mutations`), [mutations-permissions][mutations-permissions]
  (`DjangoModelPermission` + `run_permission_classes`),
  [mutations-resolvers][mutations-resolvers] (sync + async pipeline),
  [mutations-fields][mutations-fields] (factory). *Projection*: this
  file's statement 1. *Shape precedent*:
  [forms-`__init__`][forms-init] (eager + typed `__all__`, verified by
  full read; no helper, matching the "does not need" clause).
- **Challenges.** C5 → 0 definitions here — proves the prose is enforced
  away from this file; this file could not drift any module's contract
  even if edited carelessly.
- **Owner + lifetime.** Each sibling module owns its contract (existing
  owners by responsibility); Decisions 4-5-15 own the layout. This file
  carries prose only. No stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The map covers exactly the six modules; the
  `forms/` four-module quartet is the named shape-match precedent, not a
  twin (spec-038 Decision 4 text: converter / inputs / sets / resolvers +
  reuse of `DjangoMutationField` + `FieldError`).
- **Behavioral proof.** `static-reviewed` (each bullet's named symbol
  verified at its owner: `OPERATION_CREATE`, `FieldError`,
  `materialize_mutation_input_class`, `build_payload_type`,
  `DjangoMutation`, `make_meta_validating_metaclass`,
  `_ValidatedMutationMeta`, `bind_mutations`, `DjangoModelPermission`,
  `run_write_pipeline_sync`, `make_resolver_entries`,
  `DjangoMutationField`; Decision 4-5-15 text matches the spec headings
  verbatim).
- **Structural gate.** None owed: stale prose is visible in review, not
  silently absorbable, and no gate pins docstring wording.
- **Coupling.** None.
- **Freshness.** Target `9a5683e91457b1a47e795de8b5fbd9db48ca1039`,
  six modules + [forms-`__init__`][forms-init] + [spec-036][spec-036] as
  in F1.

## Defects

None. Every docstring claim checked held first-hand: the six-module map
(descriptors + predicates in `operations.py`; `FieldError` + input/payload
generation in `inputs.py`; base + metaclass `Meta` validation + phase-2.5
bind in `sets.py`; `DjangoModelPermission` default write-auth in
`permissions.py`; sync + async pipeline in `resolvers.py`;
`DjangoMutationField` factory in `fields.py`); the Decision-4 quartet +
permissions + operations framing (spec-036 Decision 4 text verified);
the Decision-15 write-auth attribution (Decision 15 text verified); the
`forms/__init__.py` shape-match clause (eager re-export + typed `__all__`
verified by full read; no helper in either file); the four-symbol surface
clause (Decision 5 + Rev3 fourth symbol + the "complete" oracle comment in
[test-init][test-init]). The axis-6 sweep finds no missing guard: all four
required members present, the omission set carries Decision 5. The
working-tree `mutations/fields.py` hunk is concurrent dirt outside this
item's paths, attributed by content as external (not in the dispatch list,
not in the `## Owned changes` ledger) and left untouched.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding, all bindings resolve through consumer imports on
every suite run, and the only instrument used (`ast.parse`) is non-mutating.

## Judgment

Zero-edit file item. Two rules traced, both file-local with proving
challenges (F1 manifest, C1-C4; F2 map prose, C5); eleven indexed families
considered — one rejected with this leaf's own contract difference +
trigger (`package-root-public-surface`, F1 nested rejection, compared fresh
against the auth/extensions/filters/forms leaf rejections rather than
inherited), one routed as checked member-adjacent
(`sealed-authorization-source` via C6: seals owned at
[mutations-sets][mutations-sets], consumed via the submodule path and
mirrored — the leaf re-exports only `DjangoMutation`), nine checked with
no surface (`subsystem-clear-lifecycle` via C7, `shared-write-skeleton` (+
entry factory) / `one-sync-boundary` / `related-object-visibility-recheck`
/ `sync-boundary-recourse-wording` via C8, `set-type-naming` /
`converter-table-per-surface-ownership` via C9, `drf-soft-export-guard` via
C10). Enumeration covers 7/7 statements. No defects, no pending execution,
no production edits.

## Implementation (Worker 1)

No tracked changes made (design-equivalent zero-edit result submitted for
verification). Item-scoped diff vs
`406c7c90d283642839508a6309a3b215db545520`:
`git diff <baseline> -- django_strawberry_framework/mutations/__init__.py`
empty (0 bytes); working blob
`9a5683e91457b1a47e795de8b5fbd9db48ca1039` equals
`HEAD:django_strawberry_framework/mutations/__init__.py` — target CLEAN, so
no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-mutations____init__.md`) is a new untracked file, the
item's only output. No `uv run ruff format .` / `ruff check` run (no edits
to format; `.md` is outside ruff format scope). No shared-tree pytest run.
No `docs/dry/temp-tests/` scratch created (inspection suffices — see
`### Challenges` note). Concurrent dirt (the dispatch list: `connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, in-flight `filters/inputs.py` range hunk +
`tests/filters/test_inputs.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`; plus further concurrent work observed in-tree and
likewise left alone: `mutations/fields.py` hunk,
`extensions/resource_policy.py`, `filters/sets.py`, `forms/inputs.py`,
`tests/*`, sibling untracked `dry-file-*.md` artifacts) was left untouched;
the `## Owned changes` ledger (walker D1 fix + 2 live test files) gains no
row from this item. Worker-0 instructions: (a) tick the plan item
`File mutations/__init__.py — dry-file-mutations____init__.md` as verified
under Run `0.0.15 2026-09-18-1` once Worker 2 agrees; (b) add these two
`## Responsibility index` rows (both `file-local`, holding item
`File mutations/__init__.py`):

| `mutations-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/mutations/__init__.py`) | `django_strawberry_framework/mutations/__init__.py` (+4 owner modules) | File `mutations/__init__.py` | file-local |
| `mutations-module-map-prose` | spec-036 Decisions 4-5-15 (mechanism: sibling modules + registry/finalizer bind) | `django_strawberry_framework/mutations/__init__.py` | File `mutations/__init__.py` | file-local |

No commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[pkg-root]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Required reading done in order: `AGENTS.md`,
`docs/dry/DRY.md`, `docs/dry/worker-2.md`, the plan item
(`File mutations/__init__.py`, plan `docs/dry/dry-0_0_15.md`, Run
`0.0.15 2026-09-18-1`), the complete target (36-line full read), the
item-scoped diff (empty — verified first-hand below), consumers/tests of
touched sites (package root import block + `__all__`, `tests/base/test_init.py`
full read, `tests/mutations/*` import grep, `forms/__init__.py` full 30-line
read, `auth/mutations.py` import block + mirror clause, spec-036 Decisions
4/5/15), and the six sibling modules at their claimed symbols (grep +
docstring reads). Never read `worker-memory/`. No probe run — inspection-only
(see adequacy ruling below). No production edits; concurrent dirt untouched.

### Own trace (recorded before opening `## Findings`)

- **R1 — 4-name leaf manifest.** Four `from .<home> import <Name>`
  bindings + one 4-member typed `__all__` mirror, all in one 36-line file.
  Homes I would choose (by responsibility — each declaration, `Meta`
  validation, and machinery lives there; no narrower owner the leaf's
  consumers could depend on): `mutations/sets.py::DjangoMutation`,
  `mutations/inputs.py::FieldError`, `mutations/permissions.py::DjangoModelPermission`,
  `mutations/fields.py::DjangoMutationField` (factory function, `def` at
  working line 301 with the `N802` PascalCase parity note). The leaf and the
  package root are consumers (principle 6, compose by name). My challenges:
  5th name / rename / home-move each force exactly **1** definition (the
  home); un-rooting forces **0** here (root + oracles move) — independence
  proved in both directions. Owner choice matches W1.
- **R2 — six-module map prose + Decision-4/15 + forms shape-match.** The
  docstring maps `operations` / `inputs` / `sets` / `permissions` /
  `resolvers` / `fields` to their responsibilities. First-hand symbol
  checks at each owner: `operations.py` descriptors `OPERATION_CREATE` /
  `OPERATION_UPDATE` / `OPERATION_DELETE` / `OPERATION_FORM` +
  `get_operation_descriptor` / `operation_takes_id` / `operation_takes_data`;
  `inputs.py` `FieldError` + `materialize_mutation_input_class` +
  `build_payload_type`; `sets.py` `DjangoMutation` +
  `make_meta_validating_metaclass` + `_ValidatedMutationMeta` +
  `bind_mutations`; `permissions.py` `DjangoModelPermission` +
  `run_permission_classes`; `resolvers.py` `run_write_pipeline_sync` +
  `make_resolver_entries` (+ `run_pipeline_async` single-`sync_to_async`
  path); `fields.py` `DjangoMutationField` factory. Decision 4 text
  (module split + operations vocabulary), Decision 5 text (four-symbol
  surface: base + factory + `FieldError` + write-auth class), and the
  forms shape-match clause (eager re-export + typed `__all__`, no helper —
  full 30-line read of `forms/__init__.py` confirms 2-name manifest, no
  helper in either file) all hold. A module-role change forces **0**
  definitions here (stale prose = projection). Matches W1's F2.
- **Counts.** `ast.parse` over the working file: **7** top-level
  statements (docstring, `__future__` import, four `from` imports,
  `__all__` AnnAssign). Matches W1's instrument + count.

### Reconciliation vs W1

Per-row agreement/difference:

- **F1 manifest (file-local): AGREE.** Same 4-name set, same four homes,
  same consumer/oracle/projection roles, same C1–C4 counts (1/1/1/0).
  Owner choice identical (per-symbol homes; leaf = consumer).
- **F2 map prose (file-local): AGREE.** Same six-module contract split,
  same Decision-4/5/15 anchoring, same forms precedent, same C5 = 0.
- **F1 nested rejection (`package-root-public-surface`): AGREE with own
  difference confirmed fresh.** W1's difference (root = cross-flavor
  39-entry default recipe with exact-tuple pin + identity oracles; leaf =
  single-flavor 4-name manifest over FOUR homes, IS root-exported per
  Decision 5 + Rev3; C1 moves both as layered consumers, C4 moves only
  the root) is distinct from all four prior leaf rejections, which I
  re-read first-hand: auth (structural opt-in — root must never import
  auth), extensions (opt-in recipe — debug deliberately not default),
  filters (family-grain opt-in — Decision 2 forbids the root carrying
  filter names), forms (single-flavor 2-name over a SINGLE home). Same
  shape, four different differences + this fifth; nothing inherited.
  Trigger (shared manifest driver/validator, or wholesale `import *`
  root-export) and durable home (spec-036 Decision 5 + file's
  public-surface paragraph) adequate.
- **Sealed-auth adjacency (C6 → `sealed-authorization-source`): AGREE.**
  Seals owned at `mutations/sets.py`; `auth/mutations.py` consumes via
  the `..mutations.sets` submodule path (import block read first-hand)
  and mirrors `make_meta_validating_metaclass` — never the leaf. Route
  to the holding family; do not inherit. Correct.
- **Nine no-surface checks (C7–C10): AGREE each.** `subsystem-clear-lifecycle`
  (zero `register_subsystem_clear` in the leaf — grep-confirmed; rows live
  in `mutations/inputs.py` + `mutations/sets.py`); `shared-write-skeleton`
  (+ entry factory) / `one-sync-boundary` /
  `related-object-visibility-recheck` / `sync-boundary-recourse-wording`
  (no pipeline/decoder/recourse token in the leaf); `set-type-naming` /
  `converter-table-per-surface-ownership` (no naming rule, no table);
  `drf-soft-export-guard` (no `__getattr__`, no soft table, no hint).
  Each judged on this target's real surface, not inherited.

### Ruling on the `fields.py`-hunk independence claim (observed worktree blob)

W1's claim **CONFIRMED robust**, against the working tree first-hand.
Observed blobs: HEAD `cf518361d7884b8b71550cb6b73bff0c1a64549e`, work
`8c60a5c6deb43bf45c49ec31292195262b5a5ff2` (+60/-17 vs HEAD, matches W1's
record). Hunk content (full `git diff HEAD` read): hardens
`_validate_mutation_target` (guarded `isinstance` / own-`__dict__` /
identity-scan ledger seams, `_safe_class_name` labels),
`_has_mutation_protocol` (raising-attribute → `False` probe), and
`_is_registered_mutation_target` (`any(... is ...)` identity scan) —
plus import of `_safe_class_name`. It does **not** remove, rename, or
re-target `DjangoMutationField` (`def DjangoMutationField(` still at
working line 301 with the parity note), does not alter the leaf's import
binding (`from .fields import DjangoMutationField` still resolves), and
does not touch what F1 claims (the bullet claims the factory's ownership,
not its body). Six-module-map bullets re-verified against working content:
all six owners' claimed symbols present (see own trace). The hunk is
concurrent dirt outside this item's paths — left untouched, as is the
in-flight `filters/inputs.py` hunk (no finding here touches filter bytes).

### Enumeration check (member-by-member vs own count 7)

W1 table rows 1–7 cover 7/7 `ast.Module.body` members with no remainder:
docstring → F1/F2 prose; `__future__` boilerplate → none; four imports →
R1/F1; `__all__` → R1/F1. My independent parse yields the same 7 members
in the same order. **Complete; no unassigned member.**

### Fingerprint re-hashes (working tree)

Target `9a5683e91457b1a47e795de8b5fbd9db48ca1039` (== HEAD, clean);
`operations.py` `16223c6b…`; `inputs.py` `fc442047…`; `sets.py`
`cffa29e5…`; `permissions.py` `54f770ae…`; `resolvers.py` `3fd1e571…`;
`fields.py` HEAD `cf518361…` / work `8c60a5c6…` (dual-recorded correctly);
`forms/__init__.py` `a76a4f797…`; package root `0ef72601…`;
`auth/mutations.py` `dbe64995…` (== HEAD); `tests/base/test_init.py`
`4cc12105…`; spec-036 `5d79ac8b…`. **12/12 match W1's record; nothing stale.**

### Negative controls + Pending + coupling

- **Gate adequacy: ACCEPT.** No exact-`__all__` oracle exists for this leaf
  (grep over `tests/mutations/`: explicit-name or submodule-path imports
  only; the two `__all__` hits are the unrelated sentinel pin and the root
  `FieldError` membership check) — the same standing as the
  auth/extensions/filters/forms leaves. Standing cover is mechanical, not
  bespoke: a dropped binding fails loudly (`ImportError`) at explicit
  consumer imports on every suite run, and the root's exact-tuple pin +
  four leaf-vs-root `is` identity rows pin all four names one layer up.
  No bespoke per-leaf existence test owed (principle 9 gate-only economy;
  no contract row requires a manifest pin). W1's "observation, not a
  defect" ruling is correct.
- **Oracles independent:** `test_init.py` exact-tuple pin spells the tuple
  literally (never reads the leaf manifest); the four `is` identity rows
  resolve through the leaf without reading it. Never rewritten to read the
  owner. Confirmed by full read.
- **Pending absent: ADEQUATE (no probe owed).** The target has no runtime
  semantics beyond import-time binding (no `def`, no `await`, no
  `sync_to_async`, no queryset/transport code — full-read confirmed; the
  lone `async` token is docstring prose). `inapplicable by construction`
  with stated reason; no behavior an execution could distinguish. No
  `docs/dry/temp-tests/` scratch owed; no shared-tree pytest run owed.
- **Coupling: none. AGREE.**

### Equivalence (principle 8)

Zero-edit item: no observable behavior exists to change (import-time
bindings only; identity `mutations.X is mutations.<home>.X` holds by
construction of the import system; `__all__` names exactly the four with
no other binding in the file). Nothing to prove equivalent beyond the
static review recorded.

### Zero-edit + AGENTS.md prose check

Item-scoped diff vs `406c7c90d283642839508a6309a3b215db545520`:
`git diff <baseline> -- django_strawberry_framework/mutations/__init__.py`
**empty (exit 0, 0 bytes)** — confirmed myself. Coverage 7/7, assignment
complete (R1/R2 file-local rows below; C6 routed to its holding family;
C7–C10 checked no-surface). A file item owes no production edit; none
demanded. Artifact citations use `path::Symbol` + reference-style links
with the canonical group headers; no process provenance; no test-tier
violation (no new tests owed — bindings exercised by existing consumer
imports); no CHANGELOG edit; no commit. No ruff run owed (no `.py`
touched; `.md` outside ruff scope). All concurrent dirt preserved
(`mutations/fields.py` hunk, `filters/inputs.py` + `filters/sets.py` +
`forms/inputs.py` + `extensions/resource_policy.py` + `connection.py`
hunks, staged `tests/utils/test_querysets.py`, sibling untracked
artifacts, `docs/dry/dry-0_0_15.md` in-flight edits).

## Defects (Worker 2)

None. Every docstring claim re-checked first-hand and held (six-module
map, Decision-4 quartet + permissions + operations framing, Decision-15
write-auth attribution, forms shape-match, four-symbol surface per
Decision 5 + Rev3 + the "complete" oracle comment). Axis-6 sweep: all four
required members present; omission set carries Decision 5. No missing
guard, no layering contradiction, no stale prose. (No `(Worker 2)` entries
— nothing to home.)

## Judgment (Worker 2)

`Status: verified`. Zero-edit file item: two file-local rules with proving
challenges, eleven indexed families considered (one rejected with this
leaf's own fresh difference + trigger, one routed member-adjacent, nine
checked no-surface), 7/7 enumeration, 12/12 fingerprints fresh, gate
adequate, no pending execution, no defects. Worker 0 may tick the plan item
and add the two index rows endorsed below (identical to W1's proposal).
