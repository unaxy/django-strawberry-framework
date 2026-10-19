# DRY review: `django_strawberry_framework/extensions/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, or is a rejection
carrying its contract difference + trigger. Zero production edits; zero
tracked files changed.

## System trace

Tiny target (35 lines, FRESH — no prior cycle record names it): the extensions
leaf manifest. It DEFINES nothing behavioral — three re-export bindings
composing one `SchemaExtension` class name each by name from their home
modules, plus the 3-member `__all__` mirror and a docstring stating two
policies: the debug-extension opt-in (submodule-only at root) and the
error/resource root-export rationale (`DjangoSchema` installs both, so they
are default recipe). No logic, no branching, no guard, no `__getattr__`, no
soft-dependency machinery: the only runtime effect is import-time binding,
and every import below is a hard dependency by construction (grep: no
`require_optional_module` anywhere under `extensions/`).

Connected code read for judgment, outside the item:
[extensions-debug][extensions-debug] (class definition + fail-closed gate,
read in full), [extensions-error-policy][extensions-error-policy] (masking
implementation + two-seam account, read in full),
[extensions-resource-policy][extensions-resource-policy] (three-pass account,
head + install-position passages),
[extensions-operation-state][extensions-operation-state] (`__all__` +
`_OperationBoundExtension` contract, read),
the package root [pkg-root][pkg-root] (full; confirms exactly the two
root-exported names and the debug omission),
[schema.py][schema] (admitted + refused chains install both enforcement
extensions; declaration-folding passages),
[consumers.py][consumers] (per-event masking seam imports the helpers from
the submodule path, never the leaf), sibling leaf manifests
[mutations-init][mutations-init] (`__all__` shape),
[utils-init][utils-init] (pinned-set precedent cited by the target docstring),
[testing-init][testing-init] (eager shape precedent),
[middleware-debug-toolbar][middleware-debug-toolbar]
(`require_debug_toolbar` — the soft-guard twin that does NOT live here),
[utils-imports][utils-imports] (`require_optional_module` primitive), oracles
[test-init][test-init] (identity rows) and
[test-operation-state][test-operation-state] (leaf imports),
plus consumer imports in `examples/fakeshop/test_query/` and `tests/`.

Excluded with reason: every other indexed family whose files-covered list
touches `extensions/` was judged on its mechanism against this target's REAL
surface and found to have none here (see Matrix axes 1-3 and Challenges
C6-C7, C10); the concurrent dirt (`django_strawberry_framework/connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE subsystem
(extensions) from three home modules. Sibling leaves each aggregate only
their own flavor (auth/filters/forms/mutations/types/utils/testing); the
package root is the sole cross-flavor aggregator, so there is no second
cross-flavor export table to drift. The shared eager-re-export + `__all__`
shape across leaves is intentional separation per contract (opt-in vs
default recipe, stated in this file's own docstring), not duplication —
the same verdict the root artifact records for this exact file and the
auth artifact records for its leaf. Considered family
`package-root-public-surface`: rejected, see F1.

**2. Sync/async twins.** Target defines no colored pair: no `def`, no
`await`, no `sync_to_async`, no resolver body. The error-policy sync/async
unity (one synchronous generator teardown serving both colors) and the
debug capture color bounds are owned and documented at
[extensions-error-policy][extensions-error-policy] and
[extensions-debug][extensions-debug]. Considered families
`subscription-per-event-error-masking` (files-covered names
`extensions/error_policy.py`) and `one-sync-boundary`: checked, no
surface — this file holds no masking call and no boundary call (C6 ends
here with 0 definitions). `subsystem-clear-lifecycle`: checked, no
surface — grep finds no `register_subsystem_clear` anywhere under
`extensions/`.

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the
three import bindings in the SAME file (one edit region, not two
definitions). The only other spellings of the 3-name set are consumers
(`tests/extensions/*`, `tests/base/test_init.py`, fakeshop suites import
the leaf by name; `schema.py` and `consumers.py` import from the
SUBMODULE paths, never the leaf), oracles (identity assertions, not
manifest reads), and projections (docstring usage block) — listed, never
counted. Considered families `soft-dependency-require-guard` and
`drf-soft-export-guard`: checked, no surface — no `__getattr__`, no
soft-export table, no hint string, no `require_optional_module` lives
here or anywhere under `extensions/` (C7, C10 end here with 0
definitions).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack,
build/parse halves. Import binding → `__all__` membership → `import *`
binding is one direction with a single author (this file), not two halves
that can drift apart. No surface.

**5. Contracts restated in another medium.** Three media carry this file's
contracts: production code (the bindings + manifest); the mechanism owners
(`schema.py::DjangoSchema` install chains, the root manifest, each home
module's class); projections (in-file docstring paragraphs 2-4, root
comments). A new extension moves this file plus prose as projection —
counted once, at the home-module definition (C1).

**6. Enforcement by omission.** Three deliberate omissions, each with a
contract source: the debug class stays out of the package root (this
file's docstring paragraph 2 + root lines 60-61) — F2; the masking
helpers (`is_maskable_result`, `mask_execution_result`,
`masking_is_active`, `schema_error_policy`) stay submodule-private
(`consumers.py` and `tests/extensions/*` import them from
`.extensions.error_policy`, never the leaf) — F5; the operation-state
machinery (`OperationState`, `DjangoExtensionsRunner`,
`_OperationBoundExtension`) stays submodule-private (same submodule-path
imports) — F5. Every member the contract requires is present: all three
extension classes exported, nothing else bound. No member lacks a guard
its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **5 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (home paragraph + debug-opt-in + root-export rationale + eager-shape note + usage block) | (none) | prose projection, F1/F2/F3/F4 |
| 2 | `from ...extensions.debug import DjangoDebugExtension` | 1 name | R1, F1 |
| 3 | `from ...extensions.error_policy import DjangoErrorPolicyExtension` | 1 name | R1, F1 |
| 4 | `from ...extensions.resource_policy import DjangoResourcePolicyExtension` | 1 name | R1, F1 |
| 5 | `__all__ = [...]` | 3-member list | R1, F1 |

Rules: R1 extensions leaf manifest (statements 2-5 + usage block); R2
debug opt-in / no-root-re-export for debug (docstring paragraph 2 + root
absence); R3 error/resource root-export rationale (docstring paragraph 3);
R4 eager shape with no soft boundary (docstring paragraph 4); R5
helper + operation-state privacy omission (absence in statements 2-5).
Seven indexed families considered (`package-root-public-surface`,
`subscription-per-event-error-masking`, `one-sync-boundary`,
`soft-dependency-require-guard`, `drf-soft-export-guard`,
`typed-rejection-value-tail`, `subsystem-clear-lifecycle`): one rejected
with contract difference + trigger (F1), six checked with no surface
(Matrix axes 1-3, C6-C7, C10). No existing family name is reused for a
finding; no new family is named (all five rows are file-local, so Worker
0 owes five `## Responsibility index` rows).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new extension | expose a 4th `SchemaExtension` (e.g. a metrics extension) | **1** (the definition at its home module; this file's import line + `__all__` entry are consumer rows that follow by name; docstring rationale is projection) | independent |
| C2 | R1 rename | rename `DjangoDebugExtension` → `DjangoDevExtension` | **1** (home definition; import line + tuple entry + docstring mentions here follow) | independent |
| C3 | R1 home move | move `DjangoErrorPolicyExtension` to a top-level-adjacent module | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R2 omission lift | root-export the debug extension | **0 here** (root gains import lines; `DjangoSchema` opt-in posture moves; this file's docstring paragraph 2 becomes false prose, a projection, not a definition) | independent — proves separation |
| C5 | R3 rationale lift | root STOPS exporting error/resource extensions | **0 here** (root + `DjangoSchema` install chains move; this file's docstring paragraph 3 becomes false prose) | independent — proves separation |
| C6 | `subscription-per-event-error-masking` check | change per-event masking semantics | **0 here** (`extensions/error_policy.py::mask_execution_result` + `consumers.py` seam move; this file holds no masking call) | no surface — do not inherit |
| C7 | `soft-dependency-require-guard` check | give the debug extension a `require_debug_toolbar`-style guard | **0 here** (the guard would live at `debug.py` or `middleware/debug_toolbar.py`; this file holds no guard — grep: zero `require_optional_module` under `extensions/`) | no surface — do not inherit |
| C8 | R5 helper promotion | promote `mask_execution_result` to the leaf surface | **1** (`extensions/error_policy.py` definition; this file's row follows) | independent |
| C9 | R5 state promotion | promote `OperationState` to the leaf surface | **1** (`extensions/operation_state.py` definition; this file's row follows) | independent |
| C10 | R4 laziness conversion | convert the leaf to a lazy `__getattr__` table | **0 exist** (no table, no `__getattr__` anywhere under `extensions/`); the conversion would be a NEW rule owned here | independent — proves no second site |

No executable proof was run: the target has no runtime semantics beyond
import-time binding (no branches, no awaits, no guard, no queryset or
transport code), so there is no behavior an execution could distinguish.
The read-only `ast.parse` enumeration above ran in the shared tree
(non-mutating; the workspace recipe authorizes mutating proofs, of which
this item has none). Every binding is exercised by consumer imports on
every suite run (`tests/extensions/*`, `tests/base/test_init.py`,
fakeshop suites). All claims below are therefore `static-reviewed`;
there is no `execution-deferred` proof and no `docs/dry/temp-tests/`
scratch was created — inspection suffices, and a probe could distinguish
nothing.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — extensions leaf manifest (file-local)

- **Contract + variation.** The extensions subpackage's public surface is
  exactly three `SchemaExtension` class names, each composed by name from
  its home module, with `__all__` mirroring the bindings in-file.
  Legitimate variation: set membership only (a 4th extension adds one
  import line + one list entry in this file).
- **Sites + roles.** *Definitions*:
  [extensions-debug][extensions-debug]`::DjangoDebugExtension`;
  [extensions-error-policy][extensions-error-policy]`::DjangoErrorPolicyExtension`;
  [extensions-resource-policy][extensions-resource-policy]`::DjangoResourcePolicyExtension`.
  *Consumer rows*: this file's statements 2-5. *Oracles*: explicit-name
  consumer imports (`tests/extensions/test_operation_state.py`,
  `tests/base/test_init.py`, fakeshop suites) — independent (they resolve
  the homes through this file without reading the manifest); notably even
  the package's own heaviest consumers (`schema.py`, `consumers.py`)
  import from the SUBMODULE paths, so the leaf is a consumer-facing
  convenience, never a load-bearing hub. *Projections*: statement-1 usage
  block.
- **Challenges.** C1, C2, C3 → 1 definition each (the home module); C4 →
  0 here.
- **Owner + lifetime.** Per-symbol home modules (existing owners, chosen
  by responsibility: each class's declaration, hooks, and state machinery
  all live there; no narrower owner this file's consumers could depend on
  exists). This file is a consumer (principle 6: compose by name). No
  stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owners stand; a new
  extension adds its definition plus one consumer row here.
- **Distinct behavior.** The manifest intentionally covers only the three
  extension classes — masking helpers and operation-state machinery
  excluded (F5), root membership governed by F2/F3.
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows
  its owner" (bindings are by-name imports; `extensions.DjangoDebugExtension
  is extensions.debug.DjangoDebugExtension` by construction of the import
  system) and "star binding leaks a 4th name" (`__all__` names exactly
  the three; grep finds no other binding in this file).
- **Structural gate.** No exact-`__all__` oracle exists for this leaf
  (grep: no `import *` on `extensions`, no `__all__` assertion in
  `tests/extensions/`) — unlike the root, whose exact-tuple oracle pins
  its manifest. Standing in: every consumer imports the three names
  explicitly, so a dropped binding fails loudly (`ImportError`) at use
  sites on every suite run, and the root identity rows
  (`test_init.py`, leaf-vs-home `is` assertions for the two root-exported
  names) pin two of the three bindings by identity. Noted as an
  observation, not a defect: no contract row requires a manifest pin, and
  adding a bespoke existence test per leaf manifest would violate the
  gate-only economy (DRY.md principle 9: never a bespoke existence test
  per helper without a justified population and a plausible bypass).
- **Coupling.** None.
- **Freshness.**
  `django_strawberry_framework/extensions/__init__.py`
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`
  (matches the fingerprint both the root and auth artifacts recorded —
  target untouched since those passes),
  `django_strawberry_framework/extensions/debug.py`
  `bf25c146111337ee0af590e7496b34c010c2f7be`,
  `django_strawberry_framework/extensions/error_policy.py`
  `baea073f5615aaddc82c1f463071998bee7a6b62`,
  `django_strawberry_framework/extensions/resource_policy.py`
  `52084078ac166d8116b9e4bb2522e8ce193251ea`,
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `django_strawberry_framework/schema.py`
  `2f72732123ca1156c4eb122ce7b53de6269de95e`,
  `django_strawberry_framework/consumers.py`
  `18f3ea161b6081a91445796902a9635cb7e2e3bc`,
  `tests/base/test_init.py`
  `4cc121057689409213beb5ec31772130cdacb975`,
  `django_strawberry_framework/mutations/__init__.py`
  `9a5683e91457b1a47e795de8b5fbd9db48ca1039`,
  `django_strawberry_framework/utils/__init__.py`
  `1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee`,
  `django_strawberry_framework/testing/__init__.py`
  `48b45d1b433283c40bf8d602d71a26d261a833b2`.
  Searched population for a second manifest of the 3-name set: whole
  package + `tests/` + `examples/` + `docs/` (grep over
  `DjangoDebugExtension|DjangoErrorPolicyExtension|DjangoResourcePolicyExtension`:
  only homes, this file, the root's two-name subset, `schema.py`
  submodule imports, prose mentions). Excluded on strength of body:
  `extensions/error_policy.py::mask_execution_result` et al. (helpers,
  not the class — different contract, F5) and
  `extensions/operation_state.py::OperationState` (state, not surface —
  F5).
- **Rejection (nested).** Considered: consolidate the leaf manifest into
  indexed family `package-root-public-surface` (same eager-re-export +
  `__all__` shape — the auth item rejected the same family for its leaf
  with difference + trigger; this leaf is the same SHAPE but not the same
  difference). Contract difference here: the root manifest is the
  default recipe every consumer pays for at package import (eager import
  of 38 bindings), while this leaf is the opt-in import path whose
  membership rule is per-extension recipe status — debug is deliberately
  NOT default recipe (F2), error/resource ARE (F3). Posit root-exporting
  debug → the root moves and this file does not (C4); posit adding a 4th
  opt-in extension → this file moves and the root does not (C1); posit
  un-rooting the enforcement pair → the root moves and this file does
  not (C5). Different responsibility, different population, opposite
  reasons to change: same shape, not the same rule. Trigger to
  reconsider: a decision to drive every subpackage manifest from one
  shared driver/validator, or to root-export the whole leaf wholesale by
  construction, would make the sites one rule. Durable home: this file's
  docstring paragraphs 2-3 (already state both policies).

### F2 — debug opt-in / no-root-re-export for debug (file-local)

- **Contract + variation.** The package root never imports
  `DjangoDebugExtension`; consumers opt in with
  `from django_strawberry_framework.extensions import
  DjangoDebugExtension`. No legitimate variation while the default-recipe
  split stands.
- **Sites + roles.** *Contract source*: this file's docstring paragraph 2
  (default recipe vs opt-in) + the root's lines 60-61 ("Do not import or
  root-export DjangoDebugExtension here"). *Mechanism*: nothing —
  absence of an import line, enforced by the root's exact-tuple pin
  oracle (any addition fails it). *Projection*: this file's usage block.
  *Oracles*: the root exact-`__all__` pin (independent: spells the tuple
  without reading this file) + every debug consumer importing from the
  submodule path.
- **Challenges.** C4 → 0 definitions here — proves the rule is enforced
  away from this file; this file could not drift it even if edited
  carelessly.
- **Owner + lifetime.** The package root owns the omission (its manifest
  is the surface that must stay clean); this file carries prose only. No
  stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The opt-in covers the submodule path only; the
  helper/state privacy (F5) is a separate, narrower rule, and the
  error/resource root-export (F3) is the opposite case with its own
  rationale.
- **Behavioral proof.** `static-reviewed` (grep: no `DjangoDebugExtension`
  in the package root; the pin oracle guards the tuple).
- **Structural gate.** The root exact-tuple pin; negative control is the
  root artifact's (a root binding of the debug class passes every
  behavioral test and fails only the pin + identity rows).
- **Coupling.** None.
- **Freshness.** Target `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  package root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`.

### F3 — error/resource root-export rationale (file-local)

- **Contract + variation.** `DjangoErrorPolicyExtension` and
  `DjangoResourcePolicyExtension` ARE root-exported because
  `DjangoSchema` installs both on every schema it builds (default
  recipe); the explicit leaf imports exist only for a consumer assembling
  a plain `strawberry.Schema`. No legitimate variation while the
  install-everywhere posture stands.
- **Sites + roles.** *Mechanism definitions*:
  [schema.py][schema]`::DjangoSchema` admitted + refused chains (both
  install the pair; declaration-folding reads consumer entries as policy
  declarations). *Projection*: this file's docstring paragraph 3.
  *Oracles*: root identity rows (leaf-vs-home `is` assertions for both
  names in `tests/base/test_init.py`).
- **Challenges.** C5 → 0 definitions here — proves the rationale is
  enforced away from this file.
- **Owner + lifetime.** [schema.py][schema]`::DjangoSchema` (existing
  owner by responsibility: schema construction owns what every schema
  installs). This file carries prose only. No stored derivation; no
  lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The rationale covers exactly the enforcement
  pair; the debug opt-in (F2) is the opposite case recorded beside it.
- **Behavioral proof.** `static-reviewed` (admitted chain
  `DjangoErrorPolicyExtension()` + `DjangoResourcePolicyExtension()`;
  refused chain mirrors; root binds exactly the two names the paragraph
  names).
- **Structural gate.** The root identity oracles above (pre-existing, not
  new gates — no failability run owed by this zero-edit item).
- **Coupling.** None.
- **Freshness.** Target `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `django_strawberry_framework/schema.py`
  `2f72732123ca1156c4eb122ce7b53de6269de95e`,
  package root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`.

### F4 — eager shape with no soft boundary (file-local)

- **Contract + variation.** Every import in this file is a hard
  dependency; there is no soft-dependency boundary to defend and no lazy
  machinery. No legitimate variation: the shape follows from the
  dependency facts, and any future soft extension would open a new rule
  (C10), not move this one.
- **Sites + roles.** *Definition*: this file's statements 2-4 (eager
  imports) + docstring paragraph 4 (states the
  `utils/__init__.py` / `testing/__init__.py` shape + the hard-dep
  claim). *Negative evidence*: grep finds no `require_optional_module`,
  no `__getattr__`, no install-hint string anywhere under `extensions/`
  — the `require_debug_toolbar` twin lives at
  [middleware-debug-toolbar][middleware-debug-toolbar], a different
  subsystem with its own opt-in boundary (leaf-module import time).
- **Challenges.** C7, C10 → 0 definitions here.
- **Owner + lifetime.** This file (existing owner: the shape is local to
  the manifest). No stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** Eagerness is per-file: the root's DRF
  soft-exports (`drf-soft-export-guard`) and the toolbar middleware guard
  keep their own owners and hint strings; nothing here duplicates them.
- **Behavioral proof.** `static-reviewed` (full read of all four
  `extensions/` modules' import blocks; the cited precedent files use the
  same eager + `__all__` shape, verified by read).
- **Structural gate.** None owed: any softening arrives as a new import
  guard + `__getattr__` in this file — visible in review, not silently
  absorbable.
- **Coupling.** None.
- **Freshness.** Target `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `django_strawberry_framework/utils/imports.py`
  `291ecedd30c7d8af9c007758112e867c09d031eb`,
  `django_strawberry_framework/middleware/debug_toolbar.py`
  `5360149bfa207e707c98985e9a1d79672220b210`.

### F5 — helper + operation-state privacy omission (file-local)

- **Contract + variation.** The masking helpers
  (`is_maskable_result`, `mask_execution_result`, `masking_is_active`,
  `schema_error_policy`) and the operation-state machinery
  (`OperationState`, `DjangoExtensionsRunner`, `_OperationBoundExtension`)
  stay submodule-private: neither this leaf's `__all__` nor the package
  root names them. Rationale: the helpers are seam functions shared
  between the extension teardown and the transport's result source, and
  the state machinery is per-operation binding infrastructure — both are
  read through their owning modules' paths, never through a surface
  manifest.
- **Sites + roles.** *Definitions*:
  [extensions-error-policy][extensions-error-policy] (helper functions +
  `__all__`), [extensions-operation-state][extensions-operation-state]
  (`__all__` + `_OperationBoundExtension`). *Enforcement site*: this
  file's statements 2-5 (the omission). *Oracles*: `consumers.py`
  imports the four helpers from `.extensions.error_policy`;
  `tests/extensions/test_operation_state.py` imports state machinery
  from `.extensions.operation_state` — both resolve through submodule
  paths without reading the manifest.
- **Challenges.** C8, C9 → 1 definition each (the owning module); this
  file's row follows.
- **Owner + lifetime.** The owning modules (existing owners by
  responsibility). No stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** Privacy is per-symbol: a future public helper
  would gain one row here without moving the three classes.
- **Behavioral proof.** `static-reviewed` (grep: no helper/state name
  bound in this file; no leaf-path import of them anywhere — every hit
  uses the submodule path).
- **Structural gate.** None owed: the omission is enforced by absence,
  and any public-use addition arrives as a new import line in this file.
- **Coupling.** None.
- **Freshness.** Target `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `django_strawberry_framework/extensions/error_policy.py`
  `baea073f5615aaddc82c1f463071998bee7a6b62`,
  `django_strawberry_framework/extensions/operation_state.py`
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9`,
  `django_strawberry_framework/consumers.py`
  `18f3ea161b6081a91445796902a9635cb7e2e3bc`.

## Defects

None. Every docstring claim checked held: the usage block names a bound
symbol (`DjangoDebugExtension` in `__all__` order position 1); the
"every import below is a hard dependency" claim (grep: zero
`require_optional_module` under `extensions/`); the
`utils/__init__.py` / `testing/__init__.py` shape citation (both use
eager re-export + `__all__`, verified by read); the root-export split
(root binds exactly the two names paragraph 3 names, omits exactly the
one paragraph 2 names); the `DjangoSchema`-installs-both rationale
(admitted + refused chains). The axis-6 sweep finds no missing guard.

(Worker 2): traced independently; no additional defects found.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding, all bindings resolve through consumer imports
on every suite run, and the only instrument used (`ast.parse`) is
non-mutating.

## Judgment

Zero-edit file item. Five rules traced, all file-local with proving
challenges (C1-C5, C8-C10); seven indexed families considered — one
rejected with contract difference + trigger (`package-root-public-surface`,
F1 nested rejection, same shape as the auth item's but with this leaf's
own difference: opt-in membership rule vs default-recipe rule), six
checked with no surface (`subscription-per-event-error-masking`,
`one-sync-boundary` via C6, `soft-dependency-require-guard` via C7,
`drf-soft-export-guard` via C10, `typed-rejection-value-tail` and
`subsystem-clear-lifecycle` via Matrix axes 1-2). No defects, no pending
execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (design-equivalent zero-edit result submitted for
verification). Item-scoped diff vs `2e063233f5926db3011a211ff0bed3fb118b3ef0`:
`git diff <baseline> -- django_strawberry_framework/extensions/__init__.py`
empty; working blob `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc` matches
both `HEAD:django_strawberry_framework/extensions/__init__.py` and HEAD —
target CLEAN, so no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-extensions____init__.md`) is a new untracked file, the
item's only output. No `uv run ruff format .` / `ruff check` run (no edits
to format). No shared-tree pytest run. No `docs/dry/temp-tests/` scratch
created (inspection suffices — see `### Challenges` note). Concurrent dirt
listed in the dispatch (`connection.py` hunk, `tests/test_connection.py`,
staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus the other
untracked `dry-file-*.md` artifacts were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no row
from this item. No commit.

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Worked expectation-first: read AGENTS.md,
DRY.md, worker-2.md, the plan item, the 35-line target, the item-scoped
diff (`git diff 2e063233f5926db3011a211ff0bed3fb118b3ef0 -- <target>`,
empty, exit 0), every connected site below, then the artifact findings.
Worker 1's worker-memory never opened.

### Own trace

Re-derived before opening `## Findings`. The target defines no behavior:
three by-name re-export bindings plus a 3-member `__all__` mirror plus a
docstring stating two placement policies and the eager-shape note.

| Rule | Owner I would choose | Change test | Count |
|---|---|---|---|
| R1 leaf manifest | per-symbol home modules; leaf is consumer (principle 6) | 4th extension / rename / home move | 1 / 1 / 1 at home |
| R2 debug opt-in | package root (surface that must stay clean); leaf prose only | root-export debug | 0 here |
| R3 root-export rationale | `schema.py::DjangoSchema` (installs both) | un-root the pair | 0 here |
| R4 eager shape | this file (local shape) | add guard / lazy table | 0 exist |
| R5 helper/state privacy | `error_policy.py` + `operation_state.py` | promote helper / state | 1 each at owner |

Connected sites read: `extensions/debug.py` (full class + gate),
`extensions/error_policy.py` (masking + two-seam account),
`extensions/resource_policy.py` (three-pass account, install passages),
`extensions/operation_state.py` (`__all__` + base contract),
package root (full; exactly the two root-exported names, debug omitted
with lines-60-61 comment), `schema.py` admitted chain (both installed)
plus refused-chain mirror, `consumers.py` per-event seam (imports helpers
from the submodule path), `tests/base/test_init.py` (leaf imports +
`is` identity rows for both root-exported names),
`tests/extensions/test_operation_state.py` (submodule-path imports),
sibling leaves (`mutations`, `utils`, `testing` inits: eager + `__all__`).

### Reconciliation vs Worker 1

Agree on all five rows: same owners, same counts (C1-C3 = 1 at home;
C4/C5 = 0 here, proving separation; C6/C7/C10 = 0, no surface;
C8/C9 = 1 at the owning module). No difference to reconcile.

### Enumeration check

Own instrument: `ast.parse`, `len(ast.Module.body)` = 5, node kinds
`Expr, ImportFrom x3, Assign`. Member-by-member vs W1's table: docstring
(projection, F1/F2/F3/F4), three imports (R1/F1 consumer rows), `__all__`
(R1/F1) — 5/5 land, none unassigned. Count matches.

### Matrix judgment

Axis 1: agree — one-subsystem aggregate; root is the sole cross-flavor
aggregator; shared eager shape is intentional separation per stated
contract, and `package-root-public-surface` is rejected with this leaf's
own difference (below), not inherited. Axis 2: agree — no `def`/`await`
in target; masking unity and debug color bounds live at their owners;
C6 ends here with 0; `register_subsystem_clear` grep under `extensions/`
empty (verified). Axis 3: agree — `__all__` mirrors bindings in one edit
region, not two definitions; `schema.py`/`consumers.py` use submodule
paths (verified); no `__getattr__`/`require_optional_module` under
`extensions/` (verified). Axis 4: agree — one direction, single author.
Axis 5: agree — new extension moves home definition + consumer row here +
prose projection, counted once at home. Axis 6: agree — three omissions
each with a contract source; every required member present.

### Counts, roles, oracles

Counts confirmed as above. Roles confirmed: homes = definitions; leaf
statements 2-5 = consumer rows; `test_init.py` identity assertions =
independent oracles (spell names literally, never read the manifest);
docstring blocks = projections. No oracle rewritten to read its owner.

### Equivalence (principle 8) + Pending

`static-reviewed`, and inspection-only is adequate here: import-time
binding only — no branch, await, guard, queryset, or transport code — so
no execution could distinguish anything a read cannot. Bindings resolve
through consumer imports on every suite run. `## Pending execution`
absent: correct, nothing deferred.

### Zero-edit confirmation

Item-scoped diff confirmed empty by my own command (no output, exit 0);
working blob `dc3ebdc2...` equals `HEAD:<target>`. Coverage validated
(5/5 members assigned; 7 families considered). No production edit owed
by a file item; none demanded.

### Rejections, fingerprints, gates, coupling

F1 nested rejection carries its own contract difference (default-recipe
root rule vs opt-in per-extension membership rule; C4/C1/C5 move opposite
files) + trigger (shared driver/validator or wholesale root-export) +
durable home (docstring paragraphs 2-3). The six no-surface checks each
judged sound (C6/C7/C10 greps re-run; `typed-rejection-value-tail` and
`subsystem-clear-lifecycle` have no body here). All 14 freshness blobs
re-hashed — every one matches, including the target blob both the root
artifact and the auth artifact recorded (`dc3ebdc2...`), so the target is
untouched since those passes. No new gate created; the referenced
pre-existing gates (root exact-tuple pin, root identity rows) carry their
negative controls in their owning artifacts, and the gate-only economy
call (no bespoke per-leaf manifest test) is correct. Coupling: none.

### AGENTS.md prose check

No production diff, so no provenance, citation, tier, changelog, or
commit rule is reachable. Artifact uses `path::Symbol` citations and the
reference-style link block; concurrent dirt (connection.py hunk,
test files, staged querysets test, bug-hunt/dry plan edits, sibling
untracked artifacts) untouched.

### Verdict

`Status: verified`. Five file-local rows owed; Worker 0 index lines in
the return. No defects, no pending execution, no edits.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[consumers.py]: ../../django_strawberry_framework/consumers.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[schema.py]: ../../django_strawberry_framework/schema.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py
[test-operation-state]: ../../tests/extensions/test_operation_state.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review at bfaee91d (Worker 2, Q8)

Phase 1 trace only. No status set, no verdict on prior findings proposed.
Zero production edits. Prior artifact sections not read in this phase.

Scope: `django_strawberry_framework/extensions/__init__.py` whole target at
current HEAD bytes, plus the delta established from
`git diff 9031cb3d..bfaee91d -- django_strawberry_framework/extensions/error_policy.py`
(shared floor addition + floor-line changes + docstring update).
Applicable contracts: DRY.md principles 1 (declare variation, share meaning)
and 7 (choose the owner by responsibility). Tests read as oracles only.

### (1) Export / wiring map with roles

`django_strawberry_framework/extensions/__init__.py` at HEAD is 5
`ast.Module.body` members: module docstring + 3 `ImportFrom` + 1 `__all__`
assignment. It defines no class, no function, no policy object.

Re-exported (each a consumer-by-name re-export at this module; the
authoritative definition lives in the named submodule):

- `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension`
  re-exported as `DjangoDebugExtension`. Role here: consumer / projection of
  the debug surface. Wiring note carried by this module's own docstring:
  deliberately NOT re-exported from the package root; the subpackage import
  path signals opt-in rather than default recipe.
- `django_strawberry_framework/extensions/error_policy.py::DjangoErrorPolicyExtension`
  re-exported as `DjangoErrorPolicyExtension`. Role here: consumer /
  projection of the error-policy authority. Docstring states it IS
  root-exported because `django_strawberry_framework/schema.py::DjangoSchema`
  installs it on every schema it builds.
- `django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension`
  re-exported as `DjangoResourcePolicyExtension`. Role here: consumer /
  projection of the resource-policy authority. Same root-export rationale as
  the error-policy extension.

`__all__` carries exactly those 3 names, matching the 3 imports one to one.

NOT exported / rewired through this module (verified by AST + text search;
no `ImportFrom`/`Import` names them, no attribute assignment exposes them):

- `django_strawberry_framework/extensions/operation_state.py::OperationState`
- `django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner`
- `django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
- `django_strawberry_framework/extensions/operation_state.py::_OperationModeMarker`
- every masking helper in
  `django_strawberry_framework/extensions/error_policy.py`
  (`mask_execution_result`, `is_maskable_result`, `masking_is_active`,
  `schema_error_policy`, `degraded_result`, `_degraded`, `_is_unexpected`,
  `_masked`, `_replacement_for`).

Installing wiring (traced as the consumer of the two authorities, not as
definitions in the target):

- `django_strawberry_framework/schema.py::DjangoSchema.get_extensions`
  resolves the per-operation chain; the admitted chain is built by
  `django_strawberry_framework/schema.py::_admitted_chain` as
  error-policy instance first, consumer entries middle, resource-policy
  instance last (plus guard + mode marker). Refused configuration uses
  `django_strawberry_framework/schema.py::_refused_chain` with the same two
  authorities. Both authorities are constructed fresh per operation and read
  configuration from the schema record, never from a shared entry.

### (2) Masking references with roles

Every occurrence of masking behavior touching the target module or its
immediate subject:

- In `django_strawberry_framework/extensions/__init__.py` itself: zero direct
  references. No import of `mask_execution_result` or kin, no re-export, no
  call, no shape gate, no docstring mention of masking internals. The only
  masking-adjacent reference is indirect: re-exporting
  `extensions/error_policy.py::DjangoErrorPolicyExtension`, whose own module
  owns masking. Role: none at this module; the module neither defines nor
  forwards the masking rule.
- In `django_strawberry_framework/extensions/error_policy.py` (delta subject):
  definitions `extensions/error_policy.py::mask_execution_result`,
  `extensions/error_policy.py::is_maskable_result`,
  `extensions/error_policy.py::masking_is_active`,
  `extensions/error_policy.py::schema_error_policy`,
  `extensions/error_policy.py::degraded_result` (new in delta),
  `extensions/error_policy.py::DjangoErrorPolicyExtension._process_result`
  and `extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation`
  apply them. Module docstring (updated in delta) names all three seams and
  cites `consumers.py::_stop_aware_results` and
  `schema.py::DjangoSchema._masked_return` as the other two application
  sites sharing the one implementation.
- External consumers of the masking rule (each imports by name from the
  owning module, never via the `extensions/__init__.py` surface):
  `django_strawberry_framework/schema.py::DjangoSchema._masked_return`
  (imports `degraded_result`, `is_maskable_result`, `mask_execution_result`,
  `masking_is_active` at module top; applies them to the returned result;
  fails closed to `degraded_result`); `django_strawberry_framework/consumers.py::_stop_aware_results`
  (function-local import of `is_maskable_result`, `mask_execution_result`,
  `masking_is_active`, `schema_error_policy`; masks each yielded
  per-event result). Roles: consumers / enforcement sites.
- Debug ordering reference (context, not masking definition):
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension`
  reads `original_error` and documents LIFO teardown ordering after any
  masking extension. No masking code shared.

### (3) Definition counts

New function `extensions/error_policy.py::degraded_result`:

- Authoritative definitions: 1 (`def degraded_result` in
  `django_strawberry_framework/extensions/error_policy.py`). No second
  `def` of that name anywhere in `django_strawberry_framework/`, tests, or
  examples (searched).
- Export declarations of it: 1 (one added `"degraded_result"` element in that
  same module's `__all__`). It is NOT added to
  `django_strawberry_framework/extensions/__init__.py::__all__` and NOT
  imported there: new-export count at the target module = 0.
- Former inline floors replaced by calls to it in the delta: 3
  (`extensions/error_policy.py::mask_execution_result` fail-closed tail,
  `extensions/error_policy.py::DjangoErrorPolicyExtension._process_result`
  adopt-failure branch,
  `extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation`
  teardown-failure branch). Each changed from an inline
  `StrawberryExecutionResult(data=None, errors=[_degraded(policy)])`
  construction to `degraded_result(policy)`. Consumers of the floor, not
  definitions of it.
- Private entry floor `extensions/error_policy.py::_degraded` (one
  `GraphQLError`): still defined once, still called by `degraded_result`;
  unchanged by the delta except as the callee. Not counted as new.
- New extension class in this delta: none. `DjangoErrorPolicyExtension`
  definition count unchanged at 1. New export at the target
  (`extensions/__init__.py`): none; its 3 imports / 3 `__all__` entries are
  identical before and after.
- Challenge posits recorded: (a) change the whole-response floor shape
  (e.g. add an extensions map entry beside the policy message) -- exactly 1
  definition must move (`degraded_result`); the 3 call sites plus the 2
  cross-module fail-closed builders
  (`schema.py::DjangoSchema._masked_return`,
  `consumers.py::_stop_aware_results` is a caller of `mask_execution_result`
  not of the floor, while `schema.py::_masked_return` calls the floor)
  follow by name. (b) change per-entry degrade (`_degraded`) -- exactly 1
  definition (`_degraded`); `degraded_result` and `_replacement_for` consume
  it. (c) change what counts as maskable (`is_maskable_result`) -- exactly 1
  definition; teardown, schema return, and transport source consume it.
  All counts = 1 definition; remainder are consumers/oracles/projections.

### (4) Owners I would choose (principles 1/7)

- Masking meaning + lifecycle owner:
  `django_strawberry_framework/extensions/error_policy.py`. It already owns
  the classifier (`_is_unexpected`), the replacement (`_masked`), the
  per-entry degrade (`_degraded`), the whole-response floor
  (`degraded_result`), the gates (`masking_is_active`, `is_maskable_result`,
  `schema_error_policy`), the one copy-returning application
  (`mask_execution_result`), and the teardown applier
  (`DjangoErrorPolicyExtension`). Every legitimate consumer can depend on
  that module without reversing a dependency or importing a sibling flavor
  for its machinery; narrowest cohesive owner with enforcement authority.
  The delta strengthens this ownership (one floor instead of three inline
  spellings).
- Extension-class public-surface owner:
  `django_strawberry_framework/extensions/__init__.py` owns only the
  re-export record (which 3 extension classes constitute the subpackage
  surface + the docstring stating why debug stays off the root while the two
  installed-by-default authorities are root-exported). It must not own
  masking behavior, the floor, or the operation-state base: importing those
  here would widen the surface every consumer pays for and reverse the
  dependency direction (helpers depend on nothing here; this module depends
  on the three extension modules). Variation axis legitimately declared
  here: membership of the surface (add/remove an extension class), not
  behavior of any member.
- Operation-state base owner:
  `django_strawberry_framework/extensions/operation_state.py`
  (`_OperationBoundExtension`, `OperationState`, `DjangoExtensionsRunner`).
  Correctly NOT surfaced through the target; each extension module imports
  the base directly. Moving it through the target would add an owner without
  relieving any change obligation.
- Application-site roles stay consumers: `schema.py::DjangoSchema._masked_return`
  and `consumers.py::_stop_aware_results` call the owned functions by name
  and restate no classification, replacement, gate, or floor. Their local
  fail-closed `degraded_result(policy)` uses are the declared variation of
  one rule (which seam failed), sharing the meaning (what fail-closed
  publishes).

### (5) Whether the delta breaks anything derived

No break derived in this scope. No defect raised (no contract row + reaching
input named, so no release blocker; per AGENTS.md review-finding rule this
section records a non-finding, not a robustness row).

- The target module is byte-identical across the delta window (same blob at
  both commits; clean at HEAD), so its export contract (3 classes, no
  helpers, no base) is undisturbed by construction.
- The delta's shared floor is internal consolidation at its owner: one new
  `def` + one `__all__` element in the owning module, 3 former inline
  spellings converted to calls. No second definition remains in the module;
  behavior on the posited floor-shape change moves in exactly 1 place.
- The delta's docstring update (two seams to three, plus the plain-schema
  hole and the idempotence-by-construction note) is a projection describing
  the already-owned rule; it adds no code path and changes no import.
- The new `degraded_result` export living in
  `extensions/error_policy.py::__all__` but NOT in
  `extensions/__init__.py::__all__` is the correct surface, not an omission:
  `schema.py` and `consumers.py` import it from the owning module by name,
  and the target's surface contract is extension classes only. No caller
  imports the floor via the target, so no wiring input reaches a missing
  name. Reaching-input check: any `from
  django_strawberry_framework.extensions import degraded_result` input would
  fail, but that spelling is not a supported public API (no feeder, doc, or
  test uses it; oracles import from `extensions.error_policy`), so it is not
  a feasible project shape under the supported API.
- Idempotence claim relied upon by the third seam (masked errors carry
  `original_error is None`, classifier reads them as deliberate) is stated
  in both the module docstring and `schema.py::DjangoSchema._masked_return`
  docstring; the delta changes no classifier line, so nothing derived here
  contradicts it.

### (6) Freshness fingerprints of everything inspected

HEAD is `bfaee91d`. Prior commit of delta window is `9031cb3d`.
`git status --short -- django_strawberry_framework/extensions/__init__.py`
is empty (clean, confirmed). `git diff 9031cb3d..bfaee91d --
django_strawberry_framework/extensions/__init__.py` is empty (no change;
same blob at both commits).

Blobs (`git rev-parse HEAD:<path>` unless noted; worktree `git hash-object`
matches HEAD except where concurrent dirt is noted):

- `django_strawberry_framework/extensions/__init__.py` HEAD + worktree:
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`; at `9031cb3d`: same
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`.
- `django_strawberry_framework/extensions/error_policy.py` at `9031cb3d`:
  `baea073f5615aaddc82c1f463071998bee7a6b62`; at HEAD:
  `16f475471a8b8295117640f7b14d949603d7bbc0`. Worktree hash differs
  (`bd763bcc428ce0f495448e6d228061dd0bc08688`; worktree `git diff HEAD`
  is a 4-insertion/1-deletion docstring sentence, concurrent dirt outside
  this phase's window; phase-1 claims above are on HEAD bytes, verified via
  `git show HEAD:<path>` AST).
- `django_strawberry_framework/extensions/debug.py` HEAD + worktree:
  `bf25c146111337ee0af590e7496b34c010c2f7be` (clean).
- `django_strawberry_framework/extensions/resource_policy.py` HEAD:
  `52084078ac166d8116b9e4bb2522e8ce193251ea`; worktree
  `583bf460b07b24c57dbcb16aee6272c1ee4983fd` (dirty in worktree,
  concurrent work; not relied upon beyond its `__all__` + class name, read
  at worktree bytes identical in those respects).
- `django_strawberry_framework/extensions/operation_state.py` HEAD +
  worktree: `b2674a22d2dfd58ff97c51a02e16068bb22032e9` (clean).
- `django_strawberry_framework/schema.py` HEAD + worktree:
  `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5` (clean).
- `django_strawberry_framework/consumers.py` HEAD + worktree:
  `936210e2993ddca4b77ffebf65e728f59d17079c` (clean).
- Oracles read (not executed): `tests/test_error_policy.py` HEAD + worktree
  `9ff5328eaed329a5fd69ac2e7002cf0052452241` (module docstring tiers +
  `mask_execution_result` copy-contract + fail-closed rows; imports
  `DjangoErrorPolicyExtension`, `_degraded`, `mask_execution_result`,
  `masking_is_active`, `schema_error_policy` from the owning module, never
  `degraded_result`, never via the target `__init__`);
  `examples/fakeshop/test_query/test_error_policy_api.py` HEAD + worktree
  `9a425677bb9763cb05776e0521afa06ad4197307` (live wire rows: completion
  surfacing, hook-failure masking via schema return seam, id-once logging,
  DEBUG/opt-out/nested/overlap rows). `degraded_result` has zero direct
  name references in `tests/` or `examples/` (searched); it is covered
  through the floor behavior, not by name, which is consistent with
  oracle-not-reading-owner.
- Required role reading: `AGENTS.md` (worktree), `docs/dry/DRY.md`
  (canonical), `docs/dry/worker-2.md` (role delta) read before tracing.
- Population searched for second definitions / alternative importers:
  every `mask_execution_result` / `degraded_result` / `is_maskable_result` /
  `masking_is_active` / `schema_error_policy` / `_masked_return` /
  `_stop_aware_results` reference under `django_strawberry_framework/`
  enumerated above; `from django_strawberry_framework.extensions import`
  has exactly 1 hit (the docstring example line inside the target itself).
  Excluded on strength of body: `debug.py` helpers (diagnostic payload, not
  masking), `resource_policy.py` budget walk (request-side charge, not
  response-side mask), `operation_state.py` machinery (binding, not policy).

PHASE-1-TRACE-RECORDED -- artifact: docs/dry/dry-file-extensions____init__.md
