# DRY review: `django_strawberry_framework/auth/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, or is a rejection
carrying its contract difference + trigger. Zero production edits; zero
tracked files changed.

## System trace

Tiny target (20 lines, FRESH — no prior cycle record names it): the opt-in
session-auth leaf manifest. It DEFINES nothing behavioral — two re-export
bindings composing four factory names by name from their home modules, plus
the 4-member `__all__` mirror and a docstring stating the structural opt-in
(spec-040 Decision 3). No logic, no branching, no queryset, no transport,
no sync/async machinery: the only runtime effect is import-time binding.

Connected code read for judgment, outside the item:
[auth/mutations.py][auth-mutations] (the three factory definitions
`login_mutation` / `logout_mutation` / `register_mutation`, read in full),
[auth/queries.py][auth-queries] (`current_user` definition + alias-namespace
lifecycle, read in full), [auth/sessions.py][auth-sessions] (module
docstring non-re-export clause + `Transport` / capability surface, read),
the package root [__init__.py][pkg-root] (full; confirms no auth import and
the Decision-3-shaped omission), sibling leaf manifests
[filters/__init__.py][filters-init] (head),
[mutations/__init__.py][mutations-init] (`__all__` shape),
[extensions/__init__.py][extensions-init] (eager shape precedent),
[utils/__init__.py][utils-init] (pinned-set precedent), the contract source
[spec-040][spec-040] Decision 3 (lines 839-861), oracles
[test_mutations.py][test-auth-mutations] (imports + the two auth-free
subprocess tests) and [test_queries.py][test-auth-queries] (imports),
consumer [accounts/schema.py][accounts-schema], and prose projections
[docs/README.md][docs-readme] (auth usage blocks) +
`examples/fakeshop/README.md` (auth usage block).

Excluded with reason: every other indexed family whose files-covered list
touches `auth/` was judged on its mechanism against this target's REAL
surface and found to have none here (see Matrix axes 1-2 and Challenges
C6-C7); the concurrent dirt (`django_strawberry_framework/connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE flavor (auth)
from two home modules. Sibling leaves each aggregate only their own flavor
(filters/forms/mutations/types/extensions); the package root is the sole
cross-flavor aggregator, so there is no second cross-flavor export table to
drift. The shared eager-re-export + `__all__` shape across leaves is
intentional separation per contract (Decision 3: opt-in, no root re-export),
not duplication — same verdict the root artifact records for
`extensions/__init__.py`. Considered family `package-root-public-surface`:
rejected, see F1.

**2. Sync/async twins.** Target defines no colored pair: no `def`, no
`await`, no `sync_to_async`, no resolver body. The auth sync/async twinship
(`_login_resolve_body` / `_login_resolve_body_async`,
`_logout_resolve_body` / `_logout_resolve_body_async`, `_make_auth_field`
dispatch via `async_execution()`) is owned and documented at
[auth/mutations.py][auth-mutations]. Considered families `one-sync-boundary`
(files-covered names `auth/mutations.py`) and `ws-connection-actor-state`
(files-covered names `auth/mutations.py`): checked, no surface — this file
holds no boundary call and no actor/lease state (C6, C7 end here with 0
definitions). `subsystem-clear-lifecycle` (files-covered names
`auth/mutations.py` + `auth/queries.py`): checked, no surface — this file
registers no clear callback and drains no ledger.

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the
four import bindings in the SAME file (one edit region, not two
definitions). The only other spellings of the 4-name set are consumers
(`accounts/schema.py`, `tests/auth/*` explicit imports), oracles (the
auth-free subprocess assertions name module paths, not the manifest), and
projections (docstring usage block, Decision 3 code block, README blocks) —
listed, never counted. Considered family `drf-soft-export-guard`: checked,
no surface — no lazy `__getattr__`, no soft-dependency table, no hint
string lives here.

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack,
build/parse halves. Import binding → `__all__` membership → `import *`
binding is one direction with a single author (this file), not two halves
that can drift apart. No surface.

**5. Contracts restated in another medium.** Three media carry this file's
contracts: production code (the bindings + manifest); the authoritative
contract source [spec-040][spec-040] Decision 3 (exactly-four-symbols,
submodule-only, no root re-export); projections (in-file docstring,
`docs/README.md` + fakeshop README usage blocks); consumers/oracles
(`accounts/schema.py`, `tests/auth/*`). A new factory moves this file plus
Decision 3 prose plus README blocks as projection — counted once, at the
home-module definition (C1).

**6. Enforcement by omission.** Two deliberate omissions, each with a
contract source: the `sessions` internals stay submodule-private
([auth/sessions.py][auth-sessions] module docstring: "deliberately NOT
re-exported: neither `auth.__all__` nor the package root names it") — F3;
the whole auth surface stays out of the package root (Decision 3) — F2.
Every member the contract requires is present: all four factories exported,
nothing else bound. No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **4 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (opt-in paragraph + usage block) | (none) | prose projection, F1/F2 |
| 2 | `from .mutations import login_mutation, logout_mutation, register_mutation` | 3 names | R1, F1 |
| 3 | `from .queries import current_user` | 1 name | R1, F1 |
| 4 | `__all__ = (...)` | 4-member tuple | R1, F1 |

Rules: R1 auth leaf manifest (statements 2-4 + usage block); R2 structural
opt-in / no-root-re-export (docstring paragraph + root absence); R3
sessions-privacy omission (absence in statements 2-4). Four indexed
families considered (`package-root-public-surface`,
`ws-connection-actor-state`, `one-sync-boundary`, `drf-soft-export-guard`):
one rejected with contract difference + trigger (F1), three checked with no
surface (Matrix axes 1-3, C6-C7). No existing family name is reused for a
finding; no new family is named (all three rows are file-local, so Worker 0
owes no index rows).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new factory | expose a 5th auth factory (e.g. `refresh_mutation`) | **1** (the definition at its home module; this file's import line + `__all__` entry are consumer rows that follow by name; Decision 3 prose + README blocks are projections) | independent |
| C2 | R1 rename | rename `current_user` → `me` | **1** (home definition; two lines here + consumer imports follow) | independent |
| C3 | R1 home move | move `current_user` from `queries.py` to `mutations.py` | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R2 omission lift | lift Decision 3 (root-export auth) | **0 here** (root gains import lines; the finalizer `loaded_attr` guard moves; this file does not) | independent — proves separation |
| C5 | R3 privacy lift | promote a sessions helper (e.g. `classify_transport`) to the public surface | **1** ([auth/sessions.py][auth-sessions] definition; this file's row follows) | independent |
| C6 | `ws-connection-actor-state` check | change actor-lease semantics | **0 here** (`utils/sessions.py::actor_lease` + `auth/mutations.py` teardown move; this file holds no actor state) | no surface — do not inherit |
| C7 | `one-sync-boundary` check | change the sync-boundary worker | **0 here** (resolver bodies in `auth/mutations.py` move; this file holds no boundary call) | no surface — do not inherit |
| C8 | R2 root-side violation | root adds `from .auth import ...` | **0 here** (root + finalizer guard move; this file's docstring paragraph becomes false prose, a projection, not a definition) | independent — proves separation |

No executable proof was run: the target has no runtime semantics beyond
import-time binding (no branches, no awaits, no queryset/transport code),
so there is no behavior an execution could distinguish. The read-only
`ast.parse` enumeration above ran in the shared tree (non-mutating; the
workspace recipe authorizes mutating proofs, of which this item has none).
Every binding is exercised by consumer imports on every suite run
(`tests/auth/*`, `accounts/schema.py`). All claims below are therefore
`static-reviewed`; there is no `execution-deferred` proof and no
`docs/dry/temp-tests/` scratch was created.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — auth leaf manifest (file-local)

- **Contract + variation.** The auth subpackage's public surface is exactly
  four field-factory names, each composed by name from its home module, with
  `__all__` mirroring the bindings in-file. Legitimate variation: set
  membership only (a 5th factory adds one import line + one tuple entry in
  this file).
- **Sites + roles.** *Definitions*: [auth/mutations.py][auth-mutations]
  `::login_mutation`, `::logout_mutation`, `::register_mutation`;
  [auth/queries.py][auth-queries] `::current_user`. *Consumer rows*: this
  file's statements 2-4. *Oracles*: explicit-name consumer imports
  (`tests/auth/test_mutations.py`, `tests/auth/test_queries.py`,
  `accounts/schema.py`) — independent (they resolve the homes through this
  file without reading the manifest). *Projections*: statement-1 usage
  block, Decision 3 code block, README usage blocks.
- **Challenges.** C1, C2, C3 → 1 definition each (the home module); C4 → 0
  here.
- **Owner + lifetime.** Per-symbol home modules (existing owners, chosen by
  responsibility: the factories' declaration, bind, and resolver machinery
  all live there; no narrower owner this file's consumers could depend on
  exists). This file is a consumer (principle 6: compose by name). No stored
  derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owners stand; a new factory
  adds its definition plus one consumer row here.
- **Distinct behavior.** The manifest intentionally covers only the four
  factories — `sessions` internals excluded (F3), root excluded (F2).
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows its
  owner" (bindings are by-name imports; `auth.login_mutation is
  auth.mutations.login_mutation` by construction of the import system) and
  "star binding leaks a 5th name" (`__all__` names exactly the four; grep
  finds no other binding in this file).
- **Structural gate.** No exact-`__all__` oracle exists for this leaf (grep:
  no `import *` on `auth`, no `__all__` assertion in `tests/auth/`) —
  unlike the root, whose exact-tuple oracle pins its manifest. Standing in:
  every consumer imports the four names explicitly, so a dropped binding
  fails loudly (`ImportError`) at use sites on every suite run. Noted as an
  observation, not a defect: no contract row requires a manifest pin, and
  adding a bespoke existence test per leaf manifest would violate the
  gate-only economy (DRY.md principle 9: never a bespoke existence test per
  helper without a justified population and a plausible bypass).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/auth/__init__.py`
  `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
  `django_strawberry_framework/auth/mutations.py`
  `dbe64995b87240b87a1d5119f46cc42c7cab646f`,
  `django_strawberry_framework/auth/queries.py`
  `5c59ba75023d21998efc6a8b1b714bdfab273ad7`,
  `django_strawberry_framework/mutations/__init__.py`
  `9a5683e91457b1a47e795de8b5fbd9db48ca1039`,
  `django_strawberry_framework/extensions/__init__.py`
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `examples/fakeshop/apps/accounts/schema.py`
  `c0fdc23be03f7ea0c621492b96a1a4857ef60a74`,
  `tests/auth/test_mutations.py`
  `6390492979efe8ee6f9268a355b1f75404bbdbc6`,
  `tests/auth/test_queries.py`
  `7d7cfcedb74bfb36e233d5ad71d50326f02eab1d`,
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md`
  `4c9c585c3a1d372ae7413823d3afe20b9f17bdc4`.
  Searched population for a second manifest of the 4-name set: whole
  package + `tests/` + `examples/` + `docs/` (grep `login_mutation|
  logout_mutation|register_mutation|current_user` over
  `django_strawberry_framework/`: only homes, this file, and prose
  mentions). Excluded on strength of body: `mutations/sets.py`
  `::register_mutation` (different symbol — the declaration-registry
  recorder aliased at `auth/mutations.py` line 67, not the rider factory).
- **Rejection (nested).** Considered: consolidate the leaf manifest into
  indexed family `package-root-public-surface` (same eager-re-export +
  `__all__` shape). Contract difference: Decision 3 makes the opt-in
  STRUCTURAL — the root must never import auth so an auth-free consumer
  never pays the `django.contrib.auth` import — while the root manifest is
  the default recipe every consumer pays for. Posit lifting Decision 3 →
  the root moves and this file does not (C4); posit adding a 5th auth
  factory → this file moves and the root does not (C1). Different
  responsibility, different population, opposite reasons to change: same
  shape, not the same rule. Trigger to reconsider: a decision to
  root-export auth, or to drive every subpackage manifest from one shared
  driver/validator, would make the sites one rule. Durable home: this
  file's docstring paragraph (already states Decision 3).

### F2 — structural opt-in / no-root-re-export (file-local)

- **Contract + variation.** The package root never imports `auth`;
  consumers opt in with `from django_strawberry_framework.auth import ...`
  (Decision 3). No legitimate variation while Decision 3 stands.
- **Sites + roles.** *Contract source*: [spec-040][spec-040] Decision 3.
  *Mechanism definitions*: the finalizer's `loaded_attr` lookup
  (`types/finalizer.py`, phase-2.5 auth bind) + the registry's
  self-registration callbacks (no callback exists before its owner module
  imports). *Projection*: this file's statement-1 paragraph 2 (states the
  root absence + the consumer idiom). *Oracles* (independent, fresh
  subprocesses):
  `tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem`
  and `::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem`.
  *Consumers*: `accounts/schema.py`, `tests/auth/*`, README blocks.
- **Challenges.** C4 → 0 definitions here; C8 → 0 here. Both prove the rule
  is enforced away from this file — this file could not drift it even if
  edited carelessly.
- **Owner + lifetime.** Decision 3 owns the contract; the finalizer +
  registry own the mechanism. This file carries prose only. No stored
  derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The opt-in covers the submodule path only; the
  `sessions` privacy (F3) is a separate, narrower rule with its own owner
  prose.
- **Behavioral proof.** `static-reviewed` (grep: no `auth` import in the
  package root; the two subprocess oracles pin the mechanism
  independently).
- **Structural gate.** The two auth-free-subprocess oracles above; negative
  control is structural (a plain function-local import in the finalizer
  would load the subsystem under either driver — stated in the oracle's own
  docstring).
- **Coupling.** None.
- **Freshness.** Target `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
  package root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `tests/auth/test_mutations.py`
  `6390492979efe8ee6f9268a355b1f75404bbdbc6`, spec file
  `4c9c585c3a1d372ae7413823d3afe20b9f17bdc4`.

### F3 — sessions-privacy omission (file-local)

- **Contract + variation.** Transport/session internals (`Transport`,
  `classify_transport`, `require_session`, scope lock, capability answers)
  stay submodule-private: neither `auth.__all__` nor the package root names
  them. Rationale recorded at the owner: `auth/__init__.py` eagerly imports
  `.mutations` / `.queries`, so an `auth`-hosted resolver would register the
  whole opt-in subsystem on the first authenticated WebSocket operation
  just to read `SESSION_ENGINE`.
- **Sites + roles.** *Definition*: [auth/sessions.py][auth-sessions] module
  docstring (the "deliberately NOT re-exported" clause) + the private API
  itself. *Enforcement site*: this file's statements 2-4 (the omission).
  *Oracles*: `tests/auth/test_sessions.py` imports from the full submodule
  path; `consumers.py::_refreshed_actor` reaches the engine through
  `utils/sessions.py::session_store_class`, never through `auth`.
- **Challenges.** C5 → 1 definition (sessions module); this file's row
  follows.
- **Owner + lifetime.** [auth/sessions.py][auth-sessions] (existing owner by
  responsibility: transport classification + capability). No stored
  derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** Privacy is per-symbol: a future public sessions
  helper would gain one row here without moving the four factories.
- **Behavioral proof.** `static-reviewed` (grep: no `sessions` name bound
  in this file; no `auth.sessions` re-export anywhere).
- **Structural gate.** None owed: the omission is enforced by absence, and
  any public-use addition would arrive as a new import line in this file —
  visible in review, not silently absorbable.
- **Coupling.** None.
- **Freshness.** Target `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
  `django_strawberry_framework/auth/sessions.py`
  `fad7feb883a3675710a55d71642b309e55f64104`.

## Defects

None. The docstring usage block names exactly the four exported symbols in
`__all__` order modulo `current_user`-first (presentation, not contract);
the Decision 3 citation matches the spec's heading; no guard any member
requires is missing (Matrix axis 6).

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding, all bindings resolve through consumer imports
on every suite run, and the only instrument used (`ast.parse`) is
non-mutating.

## Judgment

Zero-edit file item. Three rules traced, all file-local with proving
challenges (C1-C5, C8); four indexed families considered — one rejected
with contract difference + trigger (`package-root-public-surface`, F1),
three checked with no surface (`ws-connection-actor-state`,
`one-sync-boundary` via C6-C7, `drf-soft-export-guard` via Matrix axis 3).
No defects, no pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (design-equivalent zero-edit result submitted for
verification). Item-scoped diff vs `5020c98e25257658ec6412552511f50ad67aed16`:
`git diff <baseline> -- django_strawberry_framework/auth/__init__.py` empty;
target blob `6bc3c4a5eb965988d91fef5c87240826e5163e6c` matches both
`HEAD:django_strawberry_framework/auth/__init__.py` and HEAD `9031cb3d` —
target CLEAN. The artifact itself
(`docs/dry/dry-file-auth____init__.md`) is a new untracked file, the item's
only output. No `uv run ruff format .` / `ruff check` run (no edits to
format). Concurrent dirt listed in the dispatch (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus the other
untracked `dry-file-*.md` artifacts were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no row
from this item.

## Independent verification (Worker 2)

Own trace recorded BEFORE opening `## Findings` above; reconciliation follows it.
Target read in full (20 lines): a docstring, two `from`-imports, one `__all__`
tuple. No `def`, no `await`, no decorator, no branch, no `__getattr__`.

### Own trace: rules, sites, counts, owners

Three rules re-derived from the target's real surface:

- **R1 (leaf manifest).** Contract: the auth subpackage surface is exactly four
  field-factory names composed by name from their homes, with `__all__`
  mirroring the bindings in-file. Sites: definitions at
  `django_strawberry_framework/auth/mutations.py::login_mutation`,
  `::logout_mutation`, `::register_mutation` (rider factory) and
  `django_strawberry_framework/auth/queries.py::current_user`; consumer rows =
  this file's statements 2-4; oracles = explicit-name imports in
  `tests/auth/test_mutations.py`, `tests/auth/test_queries.py`,
  `examples/fakeshop/apps/accounts/schema.py`; projections = usage blocks
  (docstring, spec-040 Decision 3, READMEs). Counts: add-a-5th-factory → 1
  (home module; import line + tuple entry follow); rename → 1 (home);
  move `current_user` across home modules → 1 (the move; one import line
  follows). Owner I would choose: per-symbol home modules (declaration, bind,
  and resolver machinery all live there); this file composes by name
  (principle 6). No stored derivation.
- **R2 (structural opt-in).** Contract: the package root never imports auth
  (spec-040 Decision 3, verified at `docs/SPECS/spec-040-auth_mutations-0_0_13.md`
  Decision 3: "importable ONLY from the submodule", "never imported by the
  package root"). Mechanism: finalizer's `loaded_attr` guarded bind
  (`django_strawberry_framework/types/finalizer.py` phase-2.5 slot) + registry
  self-registration (callback exists only once the owner imports); projection =
  this file's docstring paragraph 2. Counts: lift Decision 3 → 0 here (root +
  finalizer guard move); root-side violation (`from .auth import ...`) → 0
  here (root + guard move; docstring becomes false prose). Owner: Decision 3
  for the contract, finalizer + registry for the mechanism.
- **R3 (sessions privacy).** Contract: transport/session internals stay
  submodule-private (owner prose at
  `django_strawberry_framework/auth/sessions.py` module docstring: "deliberately
  NOT re-exported", verified in-tree; rationale cites the eager
  `.mutations`/`.queries` import registering the whole opt-in subsystem).
  Enforcement site = this file's omission in statements 2-4. Count: promote a
  sessions helper → 1 (sessions module; one row here follows). Owner:
  `django_strawberry_framework/auth/sessions.py`.

Reconciliation vs W1: identical on all three rules, all sites and roles, all
eight counts (C1-C8 re-derived with the same numbers), and all three owners.
No difference to reconcile on substance. Two prose corrections, neither
verdict-blocking (see Worker-0 instructions): (a) the Enumeration summary's
parenthetical "Worker 0 owes no index rows" is wrong — file-local rows DO take
`## Responsibility index` rows (precedent: the nine `_request_body.py` and
eleven `views.py` file-local rows standing in the plan); (b) the "four indexed
families" summary undercounts — Matrix axis 2 additionally checks
`subsystem-clear-lifecycle` (check recorded on disk, just missing from the
tally), so five families were touched: one rejected, four no-surface.

### Enumeration check (member-by-member, own instrument)

Own `ast.parse` count of `ast.Module.body`: **4**, matching W1. Member mapping
agrees: (1) docstring Expr → prose projection (R2 paragraph + R1 usage block);
(2) `from .mutations import` binding 3 names → R1 consumer row; (3)
`from .queries import` binding 1 name → R1 consumer row; (4) `__all__` 4-tuple
→ R1 consumer row, with the R3 omission read off statements 2-4. Nothing
unassigned. The `mutations/sets.py::register_mutation` exclusion is correct:
it is the generic declaration recorder (aliased as
`record_mutation_declaration` at `auth/mutations.py` line 67), a different
contract from the rider factory — shared token, not shared rule.

### Matrix judgment (each claimed inapplicability judged on its reason)

1. Cross-flavor: AGREE. Verified each sibling leaf aggregates only its own
   flavor (`mutations/__init__.py` 4-symbol surface,
   `extensions/__init__.py` eager shape) and the root carries no auth import
   (grep over `django_strawberry_framework/__init__.py`: zero hits). The
   Decision-3 structural reason for the shared eager shape is real, and the
   verified root artifact records the same intentional-separation verdict for
   `extensions/__init__.py`.
2. Sync/async twins: AGREE. Target holds no `def`/`await`/`sync_to_async`
   (full read). The twinship (`_login_resolve_body` /
   `_login_resolve_body_async`, `_make_auth_field` dispatch via
   `async_execution()`) is owned and documented at `auth/mutations.py`.
   `one-sync-boundary`, `ws-connection-actor-state`
   (`utils/sessions.py::actor_lease` + `auth/mutations.py` teardown), and
   `subsystem-clear-lifecycle` (callbacks registered by `auth/mutations.py` +
   `auth/queries.py`, none here) correctly routed as no-surface: zero of the
   mechanisms' verbs appear in this file.
3. Derived knowledge: AGREE. `__all__` mirrors the bindings in one edit
   region — one definition, not two. `drf-soft-export-guard` correctly
   no-surface: no `__getattr__`, no soft-export table, no hint string here.
4. Round-trip: AGREE. Binding → manifest → star-binding is one author, one
   direction; no second half exists.
5. Other media: AGREE. Three media inventoried; variation counted once at the
   home definition (C1). Oracles below are independent of the manifest.
6. Omission: AGREE. Both omissions carry contract sources (sessions-module
   clause; Decision 3); all four required members present, nothing else bound
   (full read). No member lacks a required guard.

### Counts, roles, oracles

All definition counts confirmed (C1-C3, C5 → 1; C4, C6-C8 → 0). Roles
confirmed: homes = definitions, this file = consumer, Decision 3/sessions
docstrings = contract sources/projections, subprocess tests = independent
oracles (assert on `sys.modules` in a fresh process, never read the owner or
the manifest), explicit-name consumer imports = oracles that resolve through
the file without reading `__all__`. No oracle rewritten — zero production
edits, zero test edits.

### Equivalence, zero-edit, routing

Item-scoped diff confirmed empty by fresh run:
`git diff 5020c98e25257658ec6412552511f50ad67aed16 --
django_strawberry_framework/auth/__init__.py` prints nothing; working blob
`6bc3c4a5` equals `HEAD:django_strawberry_framework/auth/__init__.py` and HEAD
is `9031cb3d`. No behavior changed, so principle-8 equivalence holds
vacuously; inspection-only proof is ADEQUATE here — the target's only runtime
effect is import-time binding (no ordering, transaction, await, or
cancellation axis exists by construction), the shape DRY.md expressly clears
for inspection ("import moves, body composed by name"), and every binding is
exercised by consumer imports on each suite run. No scratch probe created;
for this leaf a probe could distinguish nothing. Coverage + assignment
validated (4/4 statements home; C1-C8 each end in a file-local row, the F1
rejection, or a no-surface routing). Routings judged: `package-root-public-surface`
→ rejection ENDORSED (difference + trigger both concrete; C4/C1 opposition
proves separate responsibilities); `ws-connection-actor-state`,
`one-sync-boundary`, `drf-soft-export-guard`, `subsystem-clear-lifecycle` →
no-surface ENDORSED (each reason checked against the file's real verbs, none
present; nothing inherited).

### Rejections, fingerprints, gates, pending, coupling

F1 nested rejection carries its contract difference (structural opt-in vs
default recipe; opposite change responses) + trigger (root-export decision or
a shared manifest driver) + durable home (docstring paragraph, already
stating Decision 3). Fingerprints re-hashed against the working tree, 11/11
match: target `6bc3c4a5`, `auth/mutations.py` `dbe64995`, `auth/queries.py`
`5c59ba75`, `auth/sessions.py` `fad7feb8`, package root `0ef72601`,
`mutations/__init__.py` `9a5683e9`, `extensions/__init__.py` `dc3ebdc2`,
`accounts/schema.py` `c0fdc23b`, `tests/auth/test_mutations.py` `63904929`,
`tests/auth/test_queries.py` `7d7cfced`, spec-040 `4c9c585c`. Nothing stale.
Supplemental bindings for orientation-level reads W1 left unfingerprinted
(recorded here so the finding is bound): `filters/__init__.py` `86b25818`,
`utils/__init__.py` `1a4c2ec8`, `docs/README.md` `6b8cfbe8`,
`examples/fakeshop/README.md` `b97f15d5`, `tests/auth/test_sessions.py`
`ef7d7c78`, `consumers.py` `18f3ea16`, `utils/sessions.py` `f0d9297c`.
Gates: F1 gate-absence ENDORSED — a dropped binding fails loudly as
`ImportError` at the explicit-name use sites on every run, so no bespoke
manifest pin is owed (principle-9 economy); F2's two subprocess oracles
ENDORSED — negative control verified verbatim in the oracle's own docstring
("A plain function-local import in the finalizer would load the subsystem
under either one"); both are pre-existing oracles, not new gates, so no
failability run is owed by this zero-edit item; F3 gate-absence ENDORSED
(omission by absence; any addition arrives as a visible import line).
`## Pending execution` absent: CORRECT, no `execution-deferred` proof exists.
Coupling: none marked, CORRECT.

### AGENTS.md prose check

Item diff empty → no formatting/lint surface. Artifact: reference-style links
with the full 10-group `<!-- LINK DEFINITIONS -->` block present;
`path::Symbol` citations throughout (raw `path:NN` occurrences are permitted:
`docs/dry/dry-*.md` are per-cycle scratchpad artifacts that close with their
cycle); no process provenance; no test-tier obligation (no behavior added,
no fixture needed); concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`bug_hunt-0_0_15.md`, plan, sibling `dry-file-*.md` artifacts) untouched and
outside this item's paths.

### Defects (Worker 2)

None. Docstring usage block matches the four exported symbols; Decision 3
citation matches the spec heading verbatim; sessions non-re-export clause
single-owned at its module; axis-6 sweep finds no missing guard.

### Judgment (Worker 2)

`Status: verified`, no pending execution. Three rules traced, all file-local
with proving challenges; one rejection with difference + trigger; four
families checked with no surface; zero edits, zero defects. Worker-0
instructions: (a) tick the plan item
`File auth/__init__.py — dry-file-auth____init__.md` as verified under Run
`0.0.15 2026-09-18-1`; (b) add these three `## Responsibility index` rows
(all `file-local`, holding item `File auth/__init__.py`):

| `auth-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/auth/__init__.py`) | `django_strawberry_framework/auth/__init__.py` (+2 owner modules) | File `auth/__init__.py` | file-local |
| `auth-structural-opt-in` | spec-040 Decision 3 (mechanism: finalizer `loaded_attr` guard + registry self-registration) | `django_strawberry_framework/auth/__init__.py` | File `auth/__init__.py` | file-local |
| `auth-sessions-privacy-omission` | `django_strawberry_framework/auth/sessions.py` (non-re-export clause) | `django_strawberry_framework/auth/__init__.py` | File `auth/__init__.py` | file-local |

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-auth-queries]: ../../tests/auth/test_queries.py

<!-- examples/ -->
[accounts-schema]: ../../examples/fakeshop/apps/accounts/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
