# DRY review: `django_strawberry_framework/rest_framework/__init__.py`

Status: verified
Run: 0.0.15 2026-09-22-6

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to a family
holding item, or is a rejection carrying its contract difference + trigger.
Zero production edits; zero tracked files changed. HEAD at dispatch `5ee86193`
confirmed unmoved at finish (see `## Implementation (Worker 1)`).

## System trace

Small target (62 lines): the DRF soft-dependency guard leaf. It DEFINES one
constant (the install-hint string), one thin wrapper (the guard), and one
import-time call (the guard posture); everything else is by-name composition
of the shared raising primitive. It defines no mutation, input-generation,
converter, resolver, or hook-context logic of its own; it carries no `__all__`,
no re-exports, and no `__getattr__`. Runtime effects are the import-time guard
call plus two module bindings.

Posture, established by a package-wide `require_drf(` census at HEAD (exactly
2 production call sites: the root `__getattr__` + this file's own line 62;
every other hit is prose): this leaf is a CONSUMER of
[utils-imports][utils-imports]`::require_optional_module` (the raising
primitive) and the guard the root `__getattr__` routes through — not a second
definition of either. The four DRF-importing siblings (`sets.py`, `inputs.py`,
`serializer_converter.py`, `resolvers.py`) do NOT call it: each imports
`rest_framework` directly at module top and relies on the parent-package
`__init__` executing first, so the line-62 call fires before any submodule
body runs. `hook_context.py` imports no DRF symbol at all yet sits behind the
same guard — intended per the spec table ("or any submodule").

Connected code read for judgment, outside the item:
[pkg-root][pkg-root] (full: `_DRF_SOFT_EXPORTS` + `__getattr__` + `__all__`
polarity), [utils-imports][utils-imports] (full: the primitive + both floors +
the three best-effort siblings), [routers][routers] (HEAD bytes: module
docstring guard prose, `__all__`, `_CHANNELS_INSTALL_HINT`,
`::require_channels`, `_ROUTER_CLASS` memo, `::__getattr__`),
[debug-toolbar][debug-toolbar] (HEAD bytes: hint + `::require_debug_toolbar` +
import-time call), [auth-sessions][auth-sessions] (HEAD bytes:
`::require_channels` lazy-call twin), [keyset][keyset] (HEAD bytes:
`::_cursor_crypto_types` direct primitive calls),
[types-converters][types-converters] (HEAD bytes: the return-`None`
soft-import precedent block), [rf-sets][rf-sets] + [rf-converter][rf-converter]
+ [rf-resolvers][rf-resolvers] (HEAD bytes: docstring guard prose + DRF import
lines only), [rf-inputs][rf-inputs] + [rf-hook-context][rf-hook-context]
(full worktree reads, both clean), the sibling-leaf manifests
[filters-init][filters-init] + [forms-init][forms-init] (full) and the
`__all__`-polarity census over every other leaf `__init__`, the contract
source [spec-039][spec-039] Decision 12 (full section read), the oracles
[test-soft-dep][test-soft-dep] (full) + [test-imports][test-imports] (head +
guard-shape prose) + [test-soft-helper][test-soft-helper] (shape read), the
floor's other two places (`pyproject.toml` dev-group row + the Decision
itself), prose projections [glossary][glossary] (both soft-dependency entries
via grep), and the verified artifacts [dry-root][dry-root] (F4/F5/R2/R3/R4 +
W2 Phase-A C9/D-W2-2), [dry-routers][dry-routers] (F3 family proposal),
[dry-toolbar][dry-toolbar] (F1 twin check), and
[dry-orders-init][dry-orders-init] (leaf-manifest shape + observation
precedent) — all as trigger inputs re-derived fresh below, never inherited.

Dirt note (all read via `git show HEAD:<path>`, never touched): the worktree
copies of [rf-sets][rf-sets] (`70a1e1b1…`), [rf-converter][rf-converter]
(`95568390…`), [rf-resolvers][rf-resolvers] (`c0b54039…`), [routers][routers]
(`bc30430e…`), and [types-converters][types-converters] (`679c9448…`) are
hunt-dirtied. Every judgment below is against HEAD bytes; in each file the
relied lines were verified intact against its hunk list (the `require_drf` /
`from rest_framework` / gate-prose lines in the three siblings; the
`__all__` / hint / `require_channels` / `_ROUTER_CLASS` / `__getattr__`
regions in routers; the soft-import assignment block in converters — zero
hunks touch any of them). The target itself is CLEAN: worktree
`45cf7b63a2b768421b80b99ee78ec048a03641e1` equals
`HEAD:django_strawberry_framework/rest_framework/__init__.py`.

Excluded with reason: every other indexed family whose files-covered list was
scanned for this path — none lists `rest_framework/__init__.py` (the
`related-object-visibility-recheck` and `sync-boundary-recourse-wording` rows
name `rest_framework/resolvers.py`, a sibling with its own item; both were
judged on their mechanisms against this target's REAL surface and found to
have none here — Matrix axes 1-3, C12). No index row named
`soft-dependency-require-guard` exists in the current plan despite the
verified routers artifact proposing it; this artifact names it fresh for
Worker 0 (F2), converging with — not inheriting — that proposal, the toolbar
twin check, and the root W2 wrapper analysis.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The sibling leaves each own a distinct
surface contract, none a mirror of this guard leaf (full reads of
[filters-init][filters-init] and [forms-init][forms-init]; `__all__`-polarity
census over the rest: 10 carry one, `middleware/` + `management/` +
`management/commands/` + this leaf carry none — each absence for its own
reason, see F3). The guard wrappers across flavors (`require_drf` here,
`require_channels` in [routers][routers] + [auth-sessions][auth-sessions],
`require_debug_toolbar` in [debug-toolbar][debug-toolbar]) are per-feature
name+hint declarations over the one primitive — F2 proves opposite change
responses for wrapper-local vs primitive changes, so they are parameterized
members, not copies. The root hook consumes this guard by name (one call);
unifying the call into the root would couple the DRF boundary to the surface
file. No mirrored policy needs consolidation.

**2. Sync/async twins.** Target defines no colored pair: no `async def`, no
`await`, no `sync_to_async` (full 62-line read). The sync/async resolver pair
(`resolve_serializer_sync` / `resolve_serializer_async`) is owned at
[rf-resolvers][rf-resolvers]. Considered families
`related-object-visibility-recheck` and `sync-boundary-recourse-wording`
(both name the sibling resolver module, not this leaf): checked, no twin
surface here (C12). No boundary call lives in this file.

**3. Derived rather than repeated knowledge.** The `3.17.0` floor is spelled
once in code (the hint); the `pyproject.toml` dev-group row is config, the
spec Decision is the contract source, and the test `_HINT_SUBSTRING` is the
oracle — an intentional contract change moves all four together, which per DRY
vocabulary is not duplication (C2). The channels-floor interpolation shape
(`CHANNELS_FLOOR` + f-string hints) is NOT mirrored here for a stated reason:
that constant exists because the channels hint is written at four sites,
while the DRF hint is single-sited — interpolation would be machinery (R6).
The guarded module-name string (`"rest_framework"`) is spelled once, at the
wrapper call. `__all__` is absent, not derived: there is no binding here a
manifest could publish without breaking the guard posture (F3).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. Import → guard-raise-or-module is one direction with a single author
(this file over the primitive), not two halves that can drift apart. The
target carries no `__getattr__` at all (verified: the token is absent from
the full read; the package-wide module-hook census is exactly 2 — root +
routers), so there is no miss arm here and nothing round-trips. No surface.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (hint + wrapper + import-time call); the
authoritative contract source (spec-039 Decision 12: the import-behavior
table, the single-hint rule, the three-places-that-must-agree, the
non-memoization clause); independent oracles (the per-entry-point hint-match
tests spelling the floor substring without reading the hint; the
fresh-subprocess root-import test; the star-hygiene test; the per-name
non-memoization test; the generic primitive tests in
[test-imports][test-imports]); projections (both module docstrings here, the
root table comment + hook docstring citing this guard, the sibling `sets.py`
docstring gate line, the glossary soft-dependency entries, the spec code
blocks). A floor bump moves its home definition once; every other medium
follows by role (C2).

**6. Enforcement by omission.** Every guarded member is covered: all five
submodule import paths execute the line-62 call via parent-package order
(Python semantics — no submodule import can skip the parent `__init__`); all
7 lazy root names run `require_drf()` before the submodule import (root lines
121-123, guard-first). `hook_context.py` is guarded despite being DRF-free —
intended, with a contract source (the Decision 12 table's "or any submodule"
row; the root table routes its two names through the guard like the rest).
The `require_drf(` production census (exactly: root call + line-62 call)
proves no sibling hand-rolls a second guard and none needs to. No member
lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **7 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (soft-dep posture + three-places + `types/converters.py` precedent prose) | (none) | prose projection, F1/F2/F3 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from typing import Any` | 1 name (annotation machinery) | F2 support row + R3 |
| 4 | `from ..utils.imports import require_optional_module` | 1 name (primitive) | F2 consumer row |
| 5 | `_DRF_INSTALL_HINT: str = (...)` | hint string | F1 |
| 6 | `def require_drf` | 1 name | F2 |
| 7 | `require_drf()` module-level call | guard posture (by execution) | F3 |

Rules: R1 install-hint single source (statement 5 + floor prose); R2
thin-wrapper guard (statements 3, 4, 6 + guard prose); R3 import-time guard
posture (statement 7 + the manifested absences: no `__all__`, no re-exports,
no `__getattr__`). One family named for Worker 0 (F2 →
`soft-dependency-require-guard`, no such row in the current plan); two new
file-local rows (F1, F3); six rejections (R1..R6 below, named `J1`..`J6` to
avoid collision with the F-labels).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted. All bodies judged at HEAD bytes (see Dirt note: every relied line
verified intact against its file's hunk list).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 hint wording | reword the hint keeping the floor | **1** (statement 5; oracles match the floor substring, unaffected) | independent |
| C2 | R1 floor value | bump `3.17.0` → next floor | **1** in code (statement 5; `pyproject.toml` row = config, spec Decision = contract source, test literal = oracle — intentional contract change, not duplication) | independent |
| C3 | R2 primitive shape | change `require_optional_module` (new signal beside the hint; new parameter) | **1** ([utils-imports][utils-imports]; this wrapper + all four twins follow by call — 0 here) | independent — proves consumer |
| C4 | R2 new dep | a sixth optional dep needs a guard | **1** (the new wrapper, wherever it lives; 0 here) | independent — proves per-feature declarations |
| C5 | R2 per-module calls | add `require_drf()` calls to each sibling module | — (rejected J1: 5 copies over a mechanism parent-init order already covers) | independent |
| C6 | R2 memoization | memoize the guard result | **1 here** (breaks the eviction discipline by design; primitive + twins untouched) | independent |
| C7 | R3 manifest | give the leaf an `__all__` + re-exports | — (rejected J4: any eager binding breaks the Decision 12 posture) | independent — proves separation |
| C8 | R3 hook | add a leaf `__getattr__` | — (rejected J5: a second lazy-export site; laziness lives at the root table) | independent |
| C9 | R1 floor const | hoist the floor to a `utils/imports.py` const + interpolate | — (rejected J6: single-sited hint needs no interpolation; the channels const exists for four sites) | independent |
| C10 | R2 annotation | narrow `-> Any` to `-> ModuleType` | **1 here** (twins unaffected; bare annotation, no third axis — J3) | independent |
| C11 | R3 hook-context reach | make `hook_context` importable without DRF | spec Decision + root table + statement 7 move together (the "or any submodule" row forbids it today) | independent — proves the guard-all posture |
| C12 | resolver families | change the visibility-recheck / recourse wording | **0 here** (owned at `utils/querysets.py`; no token of either lives here) | no surface — do not inherit |

No executable proof was run: the target has no runtime semantics beyond an
import-time guard call plus a one-line delegating wrapper whose body is owned
elsewhere (no branches, no awaits, no queryset/transport code), so there is
no behavior an execution could distinguish that the cited oracles do not
already pin. The read-only `ast.parse` enumeration above ran in the shared
tree (non-mutating; the workspace recipe authorizes mutating proofs, of which
this item has none). Every binding is exercised on every suite run (the guard
call at any `rest_framework` import; the wrapper at every lazy root access).
All claims below are therefore `static-reviewed`; there is no
`execution-deferred` proof and no `docs/dry/temp-tests/` scratch was created
— inspection suffices, and a probe could distinguish nothing.

## Findings

No production edit is owed by a file item; each finding records the rule with
the challenge that proved it has no second site. Fingerprints are full
hashes; HEAD `5ee86193` throughout.

### F1 — DRF install-hint single source (file-local)

- **Contract + variation.** The one DRF-absent string lives in exactly one
  source location (`_DRF_INSTALL_HINT`) and names the verified
  `djangorestframework>=3.17.0` floor; every DRF-absent raise routes through
  `require_drf()`. The floor is one of three places that must agree (hint,
  `[dependency-groups].dev` row, spec-039 Decision). Legitimate variation:
  hint wording, floor value — here.
- **Sites + roles.** *Definition*: statement 5. No second hint string in code
  (package-wide `_DRF_INSTALL_HINT` census: definition + the one wrapper
  call + prose mentions). *Oracles*: the hint-match rows in
  [test-soft-dep][test-soft-dep] (independent: the re-typed `_HINT_SUBSTRING`
  literal + chained-cause assertions) + the fresh-subprocess
  floor-substring assertion. *Projections*: statement-1 floor paragraph, the
  wrapper docstring's hint sentence, the Decision, the glossary entries.
- **Challenges.** C1 → 1 here (oracles unaffected); C2 → 1 in code (config +
  contract source + oracle move by role).
- **Owner + lifetime.** This file's statement 5 (existing owner by
  responsibility: the feature owner single-sites its hint per the primitive's
  own docstring rule). Import-time constant; never mutated (no write site in
  any census); validity = the verified floor.
- **Migration.** None (zero-edit item): single owner stands.
- **Distinct behavior.** The test literal MUST spell the floor (an oracle
  reading the hint would pass whatever it says); the `pyproject.toml` row is
  the installable pin, not a second definition.
- **Behavioral proof.** `static-reviewed`. Rejects "the hint lives twice in
  code" (census: one definition) and "a floor bump is a four-definition
  change" (C2 proves one definition + three role-followers).
- **Structural gate.** The per-entry-point `match=_HINT_SUBSTRING` rows: any
  hint edit dropping the floor fails all three raising-entry tests (plus the
  subprocess row). Pre-existing, not a new gate — no failability run owed.
- **Coupling.** None.
- **Freshness.** Target `45cf7b63a2b768421b80b99ee78ec048a03641e1`
  (worktree == HEAD; target CLEAN),
  [test-soft-dep][test-soft-dep]
  `ac2b38ae04f0dc9731b31c590d5bc433d019e719` (clean),
  `pyproject.toml` `9be864937662d3932c1ba754c9b40877e4da2103` (clean; line
  55 the `djangorestframework>=3.17.0` row), [spec-039][spec-039]
  `cf78af93437bd9995adc473c45a876740181f127` (clean; Decision 12),
  [glossary][glossary] `d3ef357c26ede6a5bd21d4290b394ade4eb987b4` (clean).
  Searched population for a second DRF hint: whole package + `tests/` +
  `examples/` (grep `_DRF_INSTALL_HINT|djangorestframework>=`: the definition,
  the wrapper call, oracle literals, config rows, prose). Excluded on strength
  of body: the `_HINT_SUBSTRING` test literal (oracle by role) and the
  `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR` consts (other features' floors).

### F2 — thin-wrapper guard (family row: `soft-dependency-require-guard`)

- **Contract + variation.** Absence of an optional dependency raises one
  actionable install-hint `ImportError` (original chained) at the first
  moment the integration is reached for; presence returns the module
  unchanged; no memoization, so eviction-simulated absence re-fires in one
  process. Legitimate variation: the guarded module name + the feature-keyed
  hint text, each single-sited at its feature owner.
- **Sites + roles.** *Definition*:
  [utils-imports][utils-imports]`::require_optional_module` (whole body read;
  its docstring already names this wrapper's shape). *Thin-wrapper members*
  (all bodies read at HEAD, all delegate by name with no hand-rolled
  pattern): this file's `::require_drf` (own hint, import-time call),
  [routers][routers]`::require_channels` (own hint, lazy builder call),
  [auth-sessions][auth-sessions]`::require_channels` (own hint, lazy call
  after Channels-shape recognition),
  [debug-toolbar][debug-toolbar]`::require_debug_toolbar` (own hint,
  import-time call). *Direct consumers*: [keyset][keyset]`::_cursor_crypto_types`
  (two primitive calls, same hint — composes by name, no wrapper). *Wrapper
  consumers*: this file's statement 7 + the root `__getattr__` guard call.
  *Oracles*: the absence/eviction rows in [test-soft-dep][test-soft-dep] +
  the generic primitive tests in [test-imports][test-imports] (independent:
  re-typed literals + chained-cause + raw-propagation assertions).
  *Projections*: each wrapper's docstring naming the shared primitive
  (verified all four directions) + Decision 12 + spec-041 Decision 5.
- **Challenges.** C3 → 1 at the primitive (0 here); C4 → 1 new wrapper (0
  here); C6 → 1 here (memoization is per-wrapper posture). The triple moves
  opposite sites under opposite changes: shared body, independent
  declarations.
- **Owner + lifetime.** [utils-imports][utils-imports]`::require_optional_module`
  (existing owner by responsibility: the one raising primitive every guard
  delegates to). No stored derivation anywhere on this path (each call
  re-runs the import — the docstrings state the non-memoization as the
  eviction-test property); no lifetime fields owed.
- **Migration.** None (zero-edit file item): this member already composes by
  name. Consolidation, if any, lives in the holding family item, not here —
  expected to be keep-the-wrappers (the hint-per-feature split is the
  documented single-siting rule).
- **Distinct behavior.** Guard timing differs per feature and stays per site:
  this leaf + the toolbar guard at leaf import, the router lazily at first
  symbol access, auth after transport classification — unifying the call
  moment would move each feature's import contract. Top-level-only guarding
  (a present-but-broken submodule propagates its own raw `ImportError`) is
  the shared contract, stated at each wrapper.
- **Behavioral proof.** `static-reviewed` (primitive + all four wrappers +
  both floor consts + keyset calls read). Rejects "this file hand-rolls an
  import pattern" (the body is one delegation call) and "a fifth wrapper
  would copy the raise" (C4 proves it would name the primitive).
- **Structural gate.** The absence rows (a hand-rolled `import rest_framework`
  passes every present-path oracle and fails exactly the hint-match rows) —
  pre-existing, not a new gate.
- **Coupling.** None.
- **Freshness.** Target `45cf7b63a2b768421b80b99ee78ec048a03641e1`,
  [utils-imports][utils-imports]
  `291ecedd30c7d8af9c007758112e867c09d031eb` (clean, whole module),
  [routers][routers] HEAD `a18c5001471d4a937bb81d2ff41a2e442e7d2dad`
  (worktree `bc30430e79a5d9fa4c37f6f6c13e2fb098888e21` hunt dirt in
  `_factory_application` + `_websocket_application` only — every relied
  region verified intact), [auth-sessions][auth-sessions]
  `fad7feb883a3675710a55d71642b309e55f64104` (clean),
  [debug-toolbar][debug-toolbar]
  `5360149bfa207e707c98985e9a1d79672220b210` (clean),
  [keyset][keyset] `df4b5e2f105c2b9fa956eac7cea25ba8a0a8de80` (clean),
  [test-soft-dep][test-soft-dep] `ac2b38ae04f0dc9731b31c590d5bc433d019e719`,
  [test-imports][test-imports]
  `6c8efcfb1d53f12912920b25ffae4455d6c39631` (clean).
  Searched population: whole package for
  `require_optional_module|require_drf|require_channels|require_debug_toolbar`
  (every hit a wrapper, a wrapper call, a direct consumer, or prose).
- **Routing.** Member site of family `soft-dependency-require-guard` —
  NAMED for Worker 0 (no such row in the current plan; the verified routers
  artifact proposed the same name and the toolbar + root-W2 artifacts
  recorded the same membership — converged fresh here, not inherited:
  every wrapper body + the primitive re-read at HEAD, C3/C4/C6 re-derived
  with this member's own counts). Holding item is that family.

### F3 — import-time guard posture: no manifest, no hook (file-local)

- **Contract + variation.** Importing this package — or any of its five
  submodules — runs `require_drf()` first, so a DRF-absent build raises the
  guarded `ImportError` before any submodule body executes. The leaf
  publishes no `__all__`, no re-exports, and no `__getattr__`: laziness
  lives at the root `_DRF_SOFT_EXPORTS` table, which addresses submodule
  dotted paths directly and never reads a leaf attribute. Binary posture —
  no further axes.
- **Sites + roles.** *Definition*: statement 7 (the call) + the manifested
  absences (verified by the full 62-line read + the module-hook census:
  exactly 2 package-wide, root + routers). *Enforcement mechanism*:
  parent-package `__init__` execution order (Python semantics — no submodule
  import can skip it). *Consumers of the posture*: the four DRF-importing
  siblings (rely on the order; verified none calls the guard) + the root
  `__getattr__` (calls it explicitly, then imports by tabled submodule
  string). *Oracles*: the package-import + sets-import hint tests in
  [test-soft-dep][test-soft-dep] (independent: they drive real imports under
  eviction and match the floor substring).
- **Challenges.** C7/C8 → rejected (J4/J5: a manifest or hook here would be a
  second surface site breaking Decision 12); C11 → the guard-all posture is
  load-bearing (the spec table forbids carving `hook_context` out).
- **Owner + lifetime.** This file's statement 7 + its absences. Import-time
  property; no stored state.
- **Migration.** None.
- **Distinct behavior.** The no-`__all__` absence is contractual (any eager
  binding either imports DRF — breaking the soft dep — or is dead weight
  the root table never reads), unlike the incidental no-`__all__` leaves
  (`middleware/` is a docstring-only namespace, `management/` + `commands/`
  are single-line markers — different reasons, no shared rule). The eager
  sibling leaves (filters/orders/forms) publish manifests because their
  imports are always safe; this leaf must raise instead — opposite polarity
  by opposite contract.
- **Behavioral proof.** `static-reviewed`. Rejects "a submodule import can
  dodge the guard" (parent-init order is unconditional) and "the root table
  needs a leaf attribute" (it imports submodule dotted paths directly).
- **Structural gate.** The two import-path hint tests (package + sets) —
  deleting statement 7 fails both (the sets import would raise a bare
  `ModuleNotFoundError` instead). Pre-existing, not a new gate.
- **Coupling.** None.
- **Freshness.** Target `45cf7b63a2b768421b80b99ee78ec048a03641e1`,
  [pkg-root][pkg-root] `0ef72601ecac300ac87ff993af1b04a4f1bc335a` (clean),
  [rf-sets][rf-sets] HEAD `2c7117d6410ecab315abde0d56f861938ba6ab1b`
  (worktree `70a1e1b1610e797620dbd705066c422857325b7f`; relied docstring
  line + DRF import line verified intact),
  [rf-converter][rf-converter] HEAD `32904418a169941c2afa1c9cd6866c55debc64f3`
  (worktree `95568390a70e6a40acad9639c24dfe2bde263ffa`; relied DRF import
  line verified intact), [rf-resolvers][rf-resolvers] HEAD
  `8024703ec0fb09758daeec0585e0065de1c61fc3` (worktree
  `c0b5403979692f695d89d998121027e3b6afaf62`; relied DRF import lines
  verified intact — the line-133 hunk touches the adjacent signals import
  only), [rf-inputs][rf-inputs]
  `9b17d95229b312f23deb5778468e3abacf730ec2` (clean),
  [rf-hook-context][rf-hook-context]
  `f4910159df293d21ad8bf038d36514da5e7ed0e3` (clean),
  [filters-init][filters-init]
  `86b258186638c96995e31919346f44d7951c65ea` (clean),
  [forms-init][forms-init] `a76a4f797414e90b102eaca2598314ed6ba4b47c`
  (clean), [orders-init][orders-init]
  `ed546f9c70d56d73e0d84a029e9e04f27da3934b` (clean),
  [test-soft-dep][test-soft-dep] `ac2b38ae04f0dc9731b31c590d5bc433d019e719`.

### J1 — per-module `require_drf()` calls in the siblings (rejected)

Considered: each of the five `rest_framework/` modules calls `require_drf()`
before its DRF import (the shape the wrapper docstring's "every
serializer-mutation module ... call this" sentence suggests on a flat
reading). Contract difference: the enforcement mechanism is not a call but
parent-package execution order — importing any submodule unconditionally
executes this `__init__` first, so the single line-62 call already covers
all five; per-module calls would be five copies of one routing with no new
behavior (C5). The production `require_drf(` census proves the copies were
never written (exactly 2 call sites: root + self). Trigger to reconsider: a
submodule reachable without executing the parent `__init__` (no such import
shape exists in Python) would make per-module calls one rule. Durable home:
the statement-1 guard paragraph (already states the package-level posture).

### J2 — one shared guard function for all wrappers (rejected)

Considered: consolidate the four thin wrappers into one shared function.
Contract difference: each wrapper IS a one-line name+hint declaration over
the already-shared primitive — the consolidation this shape invites has
already landed (commit `d5c3c635` migrated this wrapper onto
`require_optional_module`). A further merge would need a module-name + hint
dispatch table coupling four independent soft-dependency boundaries against
principle 5; C3/C4 prove opposite change responses (primitive change → 1 at
the primitive; new dep → 1 new wrapper). CONVERGE with the verified routers
F3 expectation ("keep-the-wrappers"), the toolbar F1 twin check, and the root
W2 wrapper analysis — re-derived fresh (all four bodies + the primitive
re-read at HEAD). Trigger: a second behavior shared by every wrapper beyond
name+hint (none exists; memoization polarity already differs by contract).
Durable home: [utils-imports][utils-imports]`::require_optional_module`
docstring (already states the no-`feature_label`, hint-at-owner rule).

### J3 — module-guard `-> Any` return idiom (rejected)

Considered: the `-> Any` on `require_drf` vs `require_channels` (both
modules) vs `require_debug_toolbar` as one typing rule. Shared token,
independent justification: each wrapper returns an imported module object
(untypable as anything narrower without lying), while the root/routers hooks'
`-> Any` admits function-valued lazy exports (root, oracle-pinned) or a
single class permissively (routers, unpinned). C10 moves one annotation;
no third axis exists for a bare annotation. CONVERGE with verified root R3
(fresh evidence: all three wrapper annotations re-read at HEAD; the
`require_drf` annotation is on a guard returning a module, not on a hook).
Trigger: a shared lazy-export/guard protocol with one annotation would make
the sites one rule. Durable home: each wrapper keeps its own annotation.

### J4 — leaf manifest like the sibling leaves (rejected)

Considered: publish an `__all__` + re-exports here in the filters/orders/forms
shape. Contract difference (this leaf's own, the inverse of the orders
F1-nested rejection): those leaves publish manifests because their imports
are always safe; this leaf must RAISE at import when DRF is absent
(Decision 12 table row 3). Any eager binding either imports a DRF-backed
name (breaking the soft dep for every consumer) or binds a DRF-free name the
root table never reads (it imports submodule dotted paths directly) — C7
moves nothing legitimate. The no-`__all__` leaves (`middleware/`,
`management/`, `commands/`) share the absence token for unrelated reasons
(namespace/marker files), not this contract. Trigger: DRF becoming a hard
dependency (the Decision names the flip: `SerializerMutation` joins
`__all__` then) would make a manifest one rule with the siblings. Durable
home: spec-039 Decision 12 + the statement-1 soft-dep paragraph.

### J5 — leaf `__getattr__` / lazy-export hook (rejected)

Considered: a PEP 562 hook here beside the root and routers hooks. No such
hook exists (verified: the token is absent from the full 62-line read; the
fresh package-wide census is exactly 2 module-level `__getattr__` defs —
root line 98, routers line 533, both at HEAD). Contract difference: laziness
for the DRF surface lives at the root table (7 names, guard-first routing,
non-memoizing, star-excluded); a leaf hook would be a second lazy-export
site with no names to own (C8). CONVERGE with verified root R2 (opposite
memoization + `__all__` polarity keep root vs routers severed; a leaf hook
would share neither side's contract). Trigger: the leaf gaining lazily-owned
names of its own (none exist; every DRF name resolves through the root
table). Durable home: root `__getattr__` docstring (already owns the routing
contract).

### J6 — DRF floor as an interpolated `utils/imports.py` const (rejected)

Considered: hoist `3.17.0` to a `DRF_FLOOR` const beside `CHANNELS_FLOOR` /
`STRAWBERRY_FLOOR` and interpolate it into the hint. Contract difference:
those consts exist because their hints are written at MORE than one site
(the `CHANNELS_FLOOR` comment states it: the router's three hints + the auth
session boundary's one); the DRF hint is single-sited (F1 census), so a
const + import would be principle-11 machinery serving one interpolation —
C9 moves one write either way, and the const adds an import edge from the
guard leaf to the primitive module it already imports for the call. Fresh
pair, no prior verdict (no earlier artifact compared these floors).
Trigger: a second DRF-hint site appearing anywhere in code would make the
const one rule. Durable home: the `CHANNELS_FLOOR` comment (already states
the multi-site reason) + statement 5 here.

## Defects

None. Three candidates were examined and are NOT defects (recorded so
Worker 2 can see they were considered, not missed):

- (Not a defect) The `require_drf` docstring sentence "every
  serializer-mutation module + the root `__getattr__` call this before
  importing a DRF class" over-states the mechanism: the siblings never call
  it (production census: exactly 2 call sites, root + self) — the guard
  fires via parent-package execution order. The MECHANICS hold (the guard
  runs before every submodule body; the Decision 12 table states exactly
  this), and the sentence mirrors the spec's own "route the guard through"
  phrasing narrowed to one verb — it breaks no contract row. Same
  observation-not-defect precedent as the verified orders-leaf "leading-`_`"
  looseness. No owner, no routing.
- (Not a defect) The [glossary][glossary] `require_optional_module` entry
  still says "migrating `require_drf()` onto the same primitive is a
  deliberate follow-on non-goal" although commit `d5c3c635` (spec-042,
  shipped) already migrated it. Stale projection: the behavior is correct
  (statement 6 delegates), only the rendered description lags, and
  projections never own the rule. At most a glossary-DB refresh note for
  the owning card queue; no contract row breaks. No owner, no routing.
- (Not a defect) No mechanical comparator pins the DRF hint floor against
  the `pyproject.toml` dev-group row (the toolbar flavor has
  `test_install_hint_floor_matches_the_pyproject_dev_group_row`; the DRF
  suite matches `_HINT_SUBSTRING` only). Investigated per axis 6, verdict
  negative: no contract source requires a comparator (Decision 12 states
  the three-place agreement, not a test shape), and sibling behavior
  justifies the investigation, never the verdict. Robustness note, not a
  missing guard. No owner, no routing.

The standing root-artifact test-side pin gap (D-W2-2: no exact-set oracle
for the `_DRF_SOFT_EXPORTS` key set) was trigger-checked: it is owned by
[test-soft-dep][test-soft-dep], untouched by this item, and still open —
left for closeout homing, not re-filed.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond an import-time guard call plus a one-line delegating wrapper whose
body is owned elsewhere, all bindings resolve through consumer imports on
every suite run, the pinned oracles already execute the guard's contract,
and the only instrument used (`ast.parse`) is non-mutating. Sharded /
Postgres cells are inapplicable by construction: the target reaches no
database, alias, or dialect decision.

## Judgment

Zero-edit file item. Three rules traced: two file-local with proving
challenges (F1 hint single-source, C1-C2; F3 guard posture, C7/C8/C11),
one routed to its holding family (F2 thin-wrapper guard →
`soft-dependency-require-guard`, named for Worker 0 — no such row in the
current plan). Two indexed families considered with no surface (C12). Six
rejections, each with its contract difference + trigger + durable home
(J1 per-module calls, J2 shared-guard consolidation, J3 `-> Any` idiom, J4
leaf manifest, J5 leaf hook, J6 floor-const interpolation — J2/J3/J5
converge with verified prior verdicts on fresh evidence, J1/J4/J6 fresh).
Enumeration covers 7/7 statements. No defects, no pending execution, no
production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `ITEM_BASELINE=62870bfac8f0becf63cb7025ce58dd4098edc2a4`:
`git diff <baseline> -- django_strawberry_framework/rest_framework/__init__.py`
empty (target untouched since the baseline; working blob
`45cf7b63a2b768421b80b99ee78ec048a03641e1` equals
`HEAD:django_strawberry_framework/rest_framework/__init__.py` and HEAD is
still `5ee86193` — target CLEAN, so no hunk attribution was owed). The
artifact itself (`docs/dry/dry-file-rest_framework____init__.md`) is a new
untracked file, the item's only output. No `uv run ruff format .` / `ruff
check` run (no edits to format; `.md` is outside ruff format scope; no `.py`
scratch created). No shared-tree pytest run (inspection suffices — see
`### Challenges` note; the entry command authorizes a focused `--no-cov` run
only where it could settle a judgment, and here it could settle nothing).
No `docs/dry/temp-tests/` scratch created. Concurrent dirt (hunt edits
across `django_strawberry_framework/` incl. the three `rest_framework/`
siblings + `routers.py` + `types/converters.py`, plus plan/artifact/test
dirt) left untouched; the `## Owned changes` ledger gains no row from this
item. Worker-0 instructions: (a) tick the plan item `File
rest_framework/__init__.py — dry-file-rest_framework____init__.md` as
verified under Run `0.0.15 2026-09-22-6` once Worker 2 agrees; (b) add these
nine `## Responsibility index` rows plus one `## Families` item (holding
item `File rest_framework/__init__.py` except the family row):

| `drf-install-hint-single-source` | `django_strawberry_framework/rest_framework/__init__.py::_DRF_INSTALL_HINT` | `django_strawberry_framework/rest_framework/__init__.py` | File `rest_framework/__init__.py` | file-local |
| `soft-dependency-require-guard` | `django_strawberry_framework/utils/imports.py::require_optional_module` | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/routers.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/middleware/debug_toolbar.py`, `django_strawberry_framework/keyset.py` | Family `soft-dependency-require-guard` | open |
| `rest-framework-leaf-guard-posture` | `django_strawberry_framework/rest_framework/__init__.py` (import-time call, by omission of manifest/hook) | `django_strawberry_framework/rest_framework/__init__.py` | File `rest_framework/__init__.py` | file-local |
| `rest-framework-per-module-guard-calls` | `django_strawberry_framework/rest_framework/__init__.py::require_drf` (rejection recorded here; durable home the leaf module docstring) | `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/rest_framework/hook_context.py` | File `rest_framework/__init__.py` | rejected |
| `rest-framework-shared-guard-consolidation` | `django_strawberry_framework/utils/imports.py::require_optional_module` (rejection recorded here; CONVERGE with verified routers F3 + toolbar F1 + root W2 on fresh evidence) | `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/routers.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/middleware/debug_toolbar.py`, `django_strawberry_framework/utils/imports.py` | File `rest_framework/__init__.py` | rejected |
| `rest-framework-guard-return-idiom` | `django_strawberry_framework/rest_framework/__init__.py::require_drf` (rejection recorded here; CONVERGE with verified root R3 on fresh evidence) | `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/routers.py`, `django_strawberry_framework/middleware/debug_toolbar.py`, `django_strawberry_framework/auth/sessions.py` | File `rest_framework/__init__.py` | rejected |
| `rest-framework-leaf-vs-sibling-manifest` | `django_strawberry_framework/rest_framework/__init__.py` (rejection recorded here; durable home spec-039 Decision 12 + leaf docstring) | `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/filters/__init__.py`, `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/forms/__init__.py` | File `rest_framework/__init__.py` | rejected |
| `rest-framework-leaf-hook` | `django_strawberry_framework/rest_framework/__init__.py` (rejection recorded here; CONVERGE with verified root R2 on fresh evidence — no third module hook) | `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/routers.py` | File `rest_framework/__init__.py` | rejected |
| `rest-framework-floor-const-interpolation` | `django_strawberry_framework/rest_framework/__init__.py::_DRF_INSTALL_HINT` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/utils/imports.py` | File `rest_framework/__init__.py` | rejected |

(c) add the `## Families` item `- [ ] Family
`soft-dependency-require-guard` —
[dry-rule-soft-dependency-require-guard.md](dry-rule-soft-dependency-require-guard.md)
— no artifact on disk; undispatched`. No commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-orders-init]: dry-file-orders____init__.md
[dry-root]: dry-file-__init__.md
[dry-routers]: dry-file-routers.md
[dry-toolbar]: dry-file-middleware__debug_toolbar.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[keyset]: ../../django_strawberry_framework/keyset.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[routers]: ../../django_strawberry_framework/routers.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-imports]: ../../tests/utils/test_imports.py
[test-soft-dep]: ../../tests/rest_framework/test_soft_dependency.py
[test-soft-helper]: ../../tests/_soft_dependency.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Recorded BEFORE opening `## Findings` (expectation-first). All HEAD-blob
citations below are my own hashes; dirty files judged against HEAD bytes.

### W2 trace: target, window, fingerprints

- Target `django_strawberry_framework/rest_framework/__init__.py`: worktree ==
  HEAD blob `45cf7b63`, 62 lines. HEAD `5ee86193` at my read, unmoved from
  dispatch. Window diff vs `ITEM_BASELINE=62870bfac8f0becf63cb7025ce58dd4098edc2a4`
  names ONLY `docs/dry/dry-0_0_15.md`, and that hunk is the Worker-0 dispatch
  paragraph for this item (accounting, lines appended under run 6). No other
  hunk; nothing to attribute, nothing stops the item.
- My fingerprints (short): target `45cf7b63`; root `__init__.py` `0ef72601`
  (clean); `utils/imports.py` `291ecedd` (clean); `routers.py` HEAD `a18c5001`
  vs work `bc30430e` (hunt hostile-value hardening in
  `_factory_application` / `_websocket_application`, guard region
  lines 199-208 byte-identical at HEAD); `middleware/debug_toolbar.py`
  `5360149b` (clean); `auth/sessions.py` `fad7feb8` (clean); `keyset.py`
  `df4b5e2f` (clean); siblings HEAD `resolvers.py` `8024703e`,
  `serializer_converter.py` `32904418`, `sets.py` `2c7117d6` (all hunt-dirty,
  judged at HEAD), `inputs.py` `9b17d952` (clean), `hook_context.py`
  `f4910159` (clean); `types/converters.py` HEAD `9ceb34af` (dirty, judged at
  HEAD); `tests/rest_framework/test_soft_dependency.py` `ac2b38ae` (clean);
  `docs/GLOSSARY.md` `d3ef357c` (clean); `pyproject.toml` `9be86493` (clean).

### W2 enumeration (instrument: `ast.Module.body`, my count: 7)

1. Module docstring (lines 1-19) — projection: soft-dep posture, three-places
   rule, spec-039 + converters-precedent cites. Defines no rule itself.
2. `from __future__ import annotations` — mechanics, no rule.
3. `from typing import Any` — mechanics serving stmt 6's annotation.
4. `from ..utils.imports import require_optional_module` — composition by name
   (the consumer link for stmt 6).
5. `_DRF_INSTALL_HINT` AnnAssign + comment (lines 27-33) — one production
   definition of the hint text. MY CALL: file-local (F1 shape).
6. `def require_drf` (lines 36-55) — thin wrapper: binds ("rest_framework",
   hint) and delegates. MY CALL: consumer/declaration of the raising rule
   single-owned at `utils/imports.py::require_optional_module`, NOT a second
   definition. Family membership, if named, must record count 1 on the rule.
7. `require_drf()` call + comment (lines 58-62) — import-time enforcement
   posture. MY CALL: file-local (F3 shape); the toolbar-twin shape
   (`debug_toolbar.py` line 117) is the same spelling under a different
   contract (MIDDLEWARE dotted-path opt-in vs serializer-submodule gate).

### W2 matrix (against the target's real surface)

1. Cross-flavor: SEARCHED. Read all five soft-dep flavors at HEAD bytes:
   DRF wrapper (target), `routers.py::require_channels` (HEAD 199-208),
   `auth/sessions.py::require_channels` (117-126, own feature-keyed hint),
   `middleware/debug_toolbar.py::require_debug_toolbar` (100-114, own hint +
   import-time call), `keyset.py::_cursor_crypto_types` (direct primitive
   calls, no wrapper, memoized derivation). Raising rule owned once.
2. Sync/async: INAPPLICABLE by construction — the target's runtime surface is
   a module import + a string constant + a raising call; no await boundary,
   no twin exists.
3. Derived/repeated: SEARCHED. Floor `3.17.0` re-typed across media (hint,
   pyproject row, spec-039, test literals, glossary, target docstring); ONE
   production definition (the hint). Bump-the-floor moves 1 definition;
   pyproject/test/spec/glossary move as constraint/oracle/projection.
4. Round-trip: INAPPLICABLE by construction — guard raises or returns a
   module; no encode/decode pair exists.
5. Other media: SEARCHED. Oracle `test_soft_dependency.py`: hint literal
   re-typed (independent, good) but export-set assertions parametrize over
   `_DRF_SOFT_EXPORTS` itself (dependent — the standing D-W2-2 gap, which my
   grep confirms still open: no literal key-set pin anywhere in tests/).
   Primitive oracle `tests/utils/test_imports.py` uses its own `_HINT`
   (independent). Projections: spec-039 Decision 12 (normative verb is
   "route through", NOT "call"), glossary entries (two stale words found by
   me: `require_optional_module` body says "planned"/"non-goal" for what
   shipped; `Soft dependency` body says channels "planned 0.0.14").
6. Omission: SEARCHED. Package-wide census: exactly 4 production modules
   import `rest_framework` (sets/inputs/serializer_converter/resolvers at
   HEAD), ALL under the guarded parent, none calling `require_drf` (HEAD-exact
   grep: zero sibling calls; only prose at sets.py:38). `hook_context.py`
   imports no DRF yet sits behind the guard — intended per the spec-039
   table ("or any submodule") + its two names ride the root lazy table. No
   omission gap; no second guard definition (the only other
   `raise ImportError` sites are routers' present-but-broken split hints, a
   different rule).

`require_drf()` production call sites (my census): exactly 2 — root
`__getattr__` line 123 + target line 62. `require_optional_module(`
production call sites: exactly 5 code sites — 4 wrappers + keyset's direct
pair inside one function. `import_module(` sites: root lazy-submodule import
(different rule) + the 3 importing helpers in `utils/imports.py`. No
hand-rolled absence guard anywhere.

### W2 challenges + definition counts

- C1 reword the DRF hint: 1 definition (target hint). Count 1.
- C2 change raise semantics (chain/memoize/exception): 1 definition (the
  primitive); all wrappers + keyset inherit. Count 1.
- C3 add a fifth soft dependency: 1 new declaration (wrapper + hint); no
  existing definition moves. Count 1.
- C4 add a cross-cutting guard behavior (logging): 1 natural home (the
  primitive); wrappers inherit. Count 1. The 4 wrappers are enforcement
  sites (DRY.md vocabulary: five flavors each opening their own call = five
  enforcement sites, not five copies), not 4 definitions.
- C5 change no-memoization: primitive body owns call-level re-execution;
  root non-binding is a SEPARATE root-owned rule (verified file-local at the
  root item), not a second definition of this target's rule.

### W2 owner/family calls

- F1 (hint single-source): file-local at the target. Owner stands.
- F2 (thin-wrapper guard): I would name the rule `soft-dependency-require-guard`
  ONLY as an already-single-owned rule: owner
  `utils/imports.py::require_optional_module`, members the 4 wrappers +
  keyset's direct-call function as consumers, the raising/no-memoization
  contract counted 1. The wrapper is a consumer (feature binding), and any
  holding family item's honest verdict is verify-single-owned (possibly
  gate-only), never a consolidation — a wrapper-merging driver would
  contradict the owner's recorded no-`feature_label` decision and DRY
  principle 1 (new soft dep = declaration). Coherence test I apply: the rule
  must be "absence raises route through the primitive with a feature hint"
  (all 5 call sites comply); keyset's wrapper-less shape is a justified
  consumer variance (no external caller needs a boundary name there), not a
  second rule. The root `__getattr__` is a downstream consumer of the
  WRAPPER (2 hops from the primitive), not a family member.
- F3 (import-time posture): file-local at the target; the toolbar import-time
  call is same-shape/different-contract, not a second site of this rule.
- `-> Any` on `require_drf`: forced by returning `import_module()`'s
  unknowable module type; the `__getattr__` hooks' `-> Any` is forced by
  heterogenous lazy names. Same spelling, independent reasons — no shared
  rule; rejection-shaped (convergence onto a prior Any-idiom rejection only
  if that rejection's stated principle covers per-site annotation
  independence, which I verify against the cited row, not the title).
- No `__all__` in the leaf: nothing public to manifest (`require_drf` is
  imported by name; the hint is private). Rejection-shaped with a trigger.
- No `__getattr__` in the leaf: the leaf exports nothing lazily; the lazy
  hook lives at the root (verified there). Rejection-shaped.
- DRF floor const: single production site; a const cannot span
  pyproject/spec/test/glossary media, so interpolation relieves no change
  obligation. Rejection-shaped. SEPARATE from the missing pyproject-vs-hint
  comparator (toolbar has
  `test_install_hint_floor_matches_the_pyproject_dev_group_row`; DRF has no
  pyproject-reading test — my grep) — that absence is a robustness gap with
  nothing false today (all three places agree: hint = pyproject = spec =
  `3.17.0`), correctly NOT a defect.
- Sharded/PG cells: inapplicable by construction — the target reaches no
  database, alias, or dialect decision (import guard + string constant only).

### W2 not-a-defect calls (my own, pre-reading)

- (a) `require_drf` docstring "every serializer-mutation module ... call
  this": strictly false under the modules-as-callers reading (HEAD-exact
  census: ZERO sibling calls; the spec's normative verb is "route through",
  satisfied via parent-init ordering), true under the operational reading
  (the guard runs before any sibling DRF import). It does NOT contradict
  `require_drf`'s OWN body (all body claims verify: delegates exactly as
  routers/toolbar do, returns module, raises chained hint, no memoization),
  breaks no contract row (behavior correct + oracle-covered: the
  package-import test pins the line-62 call, so acting on the misreading
  fails the suite, not the release). MY CALL: rule-out defensible; I judge
  W1's stated reason, not just its outcome.
- (b) Stale glossary `require_optional_module` entry ("planned",
  "non-goal" migration that LANDED — the target line 55 delegates): the
  observation is TRUE, and the glossary's own shipped-table says
  `0.0.14`, so the body is internally inconsistent too. I also found the
  sibling staleness the brief does not list (`Soft dependency` body: channels
  "planned 0.0.14" vs present-tense router entry + shipped tree). MY CALL:
  genuine stale-projection class; whether it is a homed defect or a ruled-out
  robustness note turns on this cycle's prose-defect precedent, which I
  calibrate against the querysets D2 record before reconciling.
- (c) Missing DRF floor comparator: TRUE absence, nothing false today.
  MY CALL: correctly not-a-defect (robustness gap at most).
- D-W2-2 pin gap: my grep confirms still open (every test reference derives
  from `_DRF_SOFT_EXPORTS`; `test_init.py:285` only asserts star-import
  absence). Correctly not re-filed by W1.

(End of pre-Findings trace.)

### W2 reconciliation (after reading Findings + cited rows on fresh evidence)

Verdict inputs, each re-derived by me rather than trusted:

- Enumeration 7/7 CONFIRMED member-by-member against my own `ast.Module.body`
  count (docstring / `__future__` / `Any` import / primitive import /
  hint / wrapper / call). Homes agree on all 7, with one notation
  correction (W2-C3 below).
- Matrix CONFIRMED on the target's real surface. Axis 1 searched (I re-read
  all five soft-dep flavors at HEAD + verified W1's `__all__`-polarity
  census myself: exactly 10 leaves carry one, exactly the 4 named carry
  none). Axes 2/4 inapplicability-by-construction ACCEPTED (no async
  surface; no inverse pair — reasons match my own). Axis 3 searched (floor
  repetition census matches mine; 1 production definition). Axis 5 searched
  (oracle roles agree; my one evidence correction is W2-C1). Axis 6 searched
  (my HEAD-exact censuses agree: 4 DRF-importing modules, all gated, zero
  sibling `require_drf` calls; exactly 2 production call sites; hook_context
  over-gating intended per the Decision 12 table I read myself).
- F1 (file-local) ENDORSED. Count C1/C2 = 1/1 re-derived. All five
  freshness hashes re-hashed MATCH. Correction W2-C1 only.
- F2 (family `soft-dependency-require-guard`, named for Worker 0) ENDORSED
  as already-single-owned: owner `utils/imports.py::require_optional_module`,
  members the 4 thin wrappers as enforcement-site declarations + keyset's
  direct-call function as consumer + stmt-7/root-call as wrapper consumers.
  Counts C3/C4/C6 = 1/1/1 re-derived; my hostile C4 (cross-cutting behavior
  has 1 natural home, the primitive) agrees. Coherence holds: the rule is
  "absence raises route through the primitive with a feature hint" and all 5
  call sites comply; keyset's wrapper-less shape is justified consumer
  variance (no external caller needs a boundary name); the root hook is a
  downstream wrapper-consumer, correctly NOT in the member list (nor in the
  index row W1 drafted). The holding family item's honest verdict is
  verify-single-owned (possibly gate-only), which W1 states outright
  ("expected to be keep-the-wrappers"). The family NAME converges with the
  routers artifact's proposal, but W1 traced fresh: it did NOT inherit
  routers-F3's interpolation overgeneralization (false for DRF/toolbar/keyset
  literal floors) nor toolbar-F1's "routers import-time call" error (routers
  calls lazily — HEAD line 356), used current line numbers (routers hook 533
  vs root-R2's stale 565), and completed root-W2's wrapper trio to a quartet
  (+auth/sessions). Independence evidence, recorded.
- F3 (file-local) ENDORSED. Hook census re-derived fresh: exactly 2
  module-level `__getattr__` at HEAD (root:98, routers:533). The stmt-7
  deletion gate claim verified true (both import tests fail without it).
  Marker-leaf characterizations verified file-by-file. Correction W2-C4 only.
- J1 ENDORSED (fresh). Mechanism (parent-init order) + census + trigger
  ("no such import shape exists in Python") all verified; durable home real.
  Consistent with the Defects-(a) ruling (see below).
- J2 ENDORSED (converge). Consolidation-already-landed verified via commit
  `d5c3c635` ("align require_drf with require_channels/require_debug_toolbar").
  All three converge legs re-read fresh: routers-F3 "keep-the-wrappers"
  verbatim; toolbar-F1 twin-check bodies match HEAD; root-W2 wrapper analysis
  ("one-line name+hint declaration over an existing driver... already the
  principle-1 shape... No candidate") — which also shows W1's "principle 5"
  cite should read principle 1 (W2-C6).
- J3 ENDORSED (converge). Root-R3 re-read: "shared token, independent
  justification" + "no third axis for a bare annotation" + joint-protocol
  trigger. W1 applies the principle to a FRESH pair R3 never considered
  (guard-module-return vs hook annotations, all 3 twin annotations re-read at
  HEAD by W1, 4th being this file's) with a coherently extended trigger.
  Corrections W2-C7 (overstated parenthetical) + W2-O1 (weak durable home).
- J4 ENDORSED (fresh). Contract difference verified against the Decision 12
  table row 3 I read + the root table's dotted-path imports; trigger names
  the spec's own hard-dep flip. The orders-shape contrast cites a real
  nested rejection (orders artifact line 891).
- J5 ENDORSED (converge). Root-R2 re-read: severance on opposite memoization
  + `__all__` polarity verbatim as W1 glosses it; W1 adds the fresh census
  (still exactly 2) + the no-names-to-own argument. Trigger + durable home
  (root hook docstring, which does own the routing contract) verified real.
- J6 ENDORSED (fresh). Multi-site reason verified at the `CHANNELS_FLOOR`
  comment ("the router's three, the auth session boundary's one" = 4 sites,
  all interpolating — HEAD-verified); DRF single-sited (F1 census); trigger
  crisp (a second DRF-hint site in code).
- Defects-(a) (docstring "call this" overstatement) RULE-OUT ENDORSED. W1
  admits the overstatement honestly (zero sibling calls at HEAD — my census
  agrees) and rules out on: mechanics hold (Decision 12 table states the true
  mechanism), mirrors spec phrasing, breaks no contract row, oracle-covered
  (F3's stmt-7 gate fails the suite if acted on). The cited orders-leaf
  "leading-`_`" precedent is REAL and W2-endorsed on all four analogous
  points (orders artifact lines 879-882). No body contradiction exists (every
  body claim in the docstring verifies). Correctly not filed.
- Defects-(b) (stale glossary entry) RULE-OUT ENDORSED. The observation is
  true (I verified: "planned"/"landing"/"non-goal" vs shipped tree + the
  glossary's own shipped-table). Rule-out calibrated: the entry's signature
  + semantics are correct (only status words lag), no contract row breaks,
  no feasible consumer-harm path (one grep self-corrects; behavior tested).
  Distinguished from querysets-D2 (filed) on fresh read: D2 documented a
  NON-EXISTENT keyword (consumer writes broken code + a spec "Verified
  dependency to protect" clause pinned the shape) — a contract row with a
  wire input, which (b) lacks. W1 even names the right refresh routing
  (glossary-DB queue, per D2's own repair note). My two unlisted siblings
  (W2-O2) fall under the same class principle. Correctly not filed.
- Defects-(c) (missing DRF floor comparator) RULE-OUT ENDORSED. Absence
  verified true (no pyproject-reading DRF test; toolbar has one). W1's reason
  applies the axis-6 rule exactly (Decision 12 states agreement, not a test
  shape; sibling behavior justifies investigation, never verdict) and nothing
  is false today (hint = pyproject = spec = `3.17.0`, all re-verified).
  Robustness note at most. Correctly not filed.
- D-W2-2 trigger-check ENDORSED: my grep confirms still open (no literal
  key-set pin; all references derive from the table; `test_init.py:285`
  asserts star-absence only). Matches the recorded shape (root artifact lines
  685-698). Correctly not re-filed.
- Pending execution: none claimed, none owed. Static-only proofs ACCEPTED:
  the item is exactly DRY.md's inspection-suffices shape (import posture +
  body composed by name), every binding executes on every suite run, and the
  ordering claim (parent-init-first) is both language semantics and
  oracle-pinned (package + sets import tests). Sharded/PG inapplicable by
  construction ACCEPTED (import guard + string constant; no DB/alias/dialect
  surface — matches my reason).
- Window: at W1 finish, only the plan (Worker-0 accounting) — CONFIRMED via
  the baseline diff at my read start. At MY finish one more tracked file
  appears (`docs/bug_hunt/bug_hunt-0_0_15.md`): attributed BY CONTENT to
  concurrent hunt Worker-0 accounting (querysets stale re-pass Iteration 7 +
  verification + ledger row + scenario-authz dispatch — zero overlap with
  this item's paths). Per scope rule ("dirt elsewhere is concurrent work to
  leave alone, not a stop") the item is NOT stopped. The hunt's touched files
  (`utils/querysets.py` + its test) are relied on by neither my trace nor
  W1's. HEAD unmoved throughout (`5ee86193`); target still clean (`45cf7b63`).
- Gates: `uv run ruff check` + `uv run ruff format --check` on the touched
  path (the `.md` artifact) both pass (exit 0; check: no Python files, all
  passed). `check_trailing_commas.py --check` on the artifact: excluded from
  the rules, exit 0. Prose scan: `path::Symbol` citations throughout, no
  process-provenance or banned words (sole `429` hit is hex inside a git
  hash). No oracle rewritten (zero test edits). AGENTS.md prose rules hold.
- W1's Worker-0 instructions (9 index rows + 1 family item) verified
  consistent with the findings (2 file-local + 1 open family with the 6
  member files, root correctly excluded + 6 rejected with CONVERGE/fresh
  marks matching J-texts). Endorsed verbatim.

### W2 corrections (evidence-precision, none structural, none verdict-affecting)

- W2-C1: F1's oracle parenthetical claims "chained-cause assertions" for
  [test-soft-dep] — FALSE. That file contains no `__cause__`/`from exc`
  assertion (verified by grep); the chained-cause pin lives in
  [test-imports] (correctly cited by F2). The DRF oracle's independence
  rests on the re-typed literal alone, which is true — verdict unaffected.
  (Genesis: mirrors toolbar-F1's oracle phrasing, where the suite does carry
  all three.)
- W2-C2: C3's "this wrapper + all four twins" is ambiguous (reads 1+4=5;
  exact census is 4 thin wrappers total — this + 3 — plus keyset's direct
  pair). Recommend "all three twin wrappers + the keyset direct consumer"
  (J3's "all three" already counts it right). Count (1 at the primitive)
  unaffected.
- W2-C3: Enumeration stmt-3 home "R3" collides with rule-R3 (posture); it
  means rejection-R3 = J3 (the `Any` idiom stmt 3 serves). Recommend "J3".
  The member is covered either way (F2 support + J3).
- W2-C4: F3's freshness note says the resolvers line-133 hunk "touches the
  adjacent signals import only" — the changed line is the `..exceptions`
  import (adds `_safe_arg_repr, _safe_class_name`); signals is context. The
  relied DRF lines ARE intact (both context) — verdict unaffected.
- W2-C5: F2's "top-level-only guarding ... stated at each wrapper" overstates:
  the BEHAVIOR holds at all 4 wrappers (each guards a top-level name), but it
  is STATED only at the toolbar (+ routers via its split-hint design);
  require_drf/sessions imply it via the call arg. (Phrase shared with
  toolbar-F1.) Recommend "holds at each, stated at two."
- W2-C6: J2's "against principle 5" should read principle 1 (+6/7): wrappers
  are variation declarations over a shared meaning, not adapters called by a
  shared body — exactly the root-W2 analysis J2 converges with, which cites
  P1 itself. Reasoning sound; number wrong.
- W2-C7: J3's "untypable as anything narrower without lying" overstates:
  `-> ModuleType` would be SOUND (runtime values are always modules; Any
  flows into it). Sites keep `Any` to match the delegated primitive's
  declared type, each independently — which is all the rejection needs
  (hooks still cannot take ModuleType, so no change moves together).

### W2 observations

- W2-O1: J3's durable home ("each wrapper keeps its own annotation") restates
  the verdict rather than naming a doc site. Acceptable for a bare
  annotation; note the root half already has a de-facto home (the
  annotation-pin's test docstring stating the hook idiom).
- W2-O2: Two stale glossary words NOT listed in Defects-(b) fall under its
  ruled-out class principle (status prose, correct surrounding contracts, no
  contract row): the `require_optional_module` body's own "planned"/"landing"
  words + the `Soft dependency` body's channels "planned 0.0.14" (vs the
  present-tense router entry + shipped tree). Covered by (b); no separate
  filing.
- W2-O3 (positive, recorded above): W1 demonstrably traced fresh rather than
  inheriting — declined routers-F3's interpolation overgeneralization,
  corrected toolbar-F1's routers-timing error, refreshed stale line numbers,
  completed the wrapper trio. Convergence verdicts are earned, not copied.

### W2 judgment

`Status: verified`, no pending execution. Three rules traced: two file-local
with proving challenges (F1 hint C1-C2; F3 posture C7/C8/C11), one routed to
its holding family (F2 → `soft-dependency-require-guard`, named for Worker 0 —
no such row in the current plan; expected holding verdict keep-the-wrappers /
verify-single-owned). Six rejections, each with contract difference + trigger
+ durable home (J2/J3/J5 converge with verified prior verdicts on fresh
evidence, all three legs re-read; J1/J4/J6 fresh). Enumeration 7/7 confirmed
member-by-member. No defects (three rule-outs endorsed + D-W2-2 confirmed
still open, not re-filed), no W2 defects filed, no pending, zero edits.
Worker-0 instructions: (a) tick the plan item
`File rest_framework/__init__.py — dry-file-rest_framework____init__.md` as
verified under Run `0.0.15 2026-09-22-6`; (b) add the nine
`## Responsibility index` rows + one `## Families` item from W1's
`## Implementation` section verbatim; (c) nothing to remove (no
`docs/dry/temp-tests/` scratch was created by either worker; all W2 probes
were read-only greps / `git show` / `git hash-object`). No commit.
