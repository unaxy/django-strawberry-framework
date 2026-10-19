# DRY review: `django_strawberry_framework/_graphql_core_patches.py`

Status: verified
Run: 0.0.15 2026-09-21-2

## System trace

Target: `django_strawberry_framework/_graphql_core_patches.py` (127 lines at HEAD,
blob `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`; clean in the working tree;
item-baseline diff empty — see `## Implementation (Worker 1)`). The module is one
of the package's four one-per-dependency upstream-patch modules. It wraps
graphql-core's `ExecutionContext.complete_list_value` with a delegating wrapper
that awaits the residual completion awaitable an async-iterable list leaves
behind when its children are awaitable, and otherwise preserves upstream
behavior.

What the target owns, by role:

- Definitions in-target: the import-time upstream capture
  (`_captured_upstream_method`, `_original_complete_list_value`), the shape
  validation (`_validate_upstream_shape`), the delegating wrapper
  (`_patched_complete_list_value` + nested `_await_residual` + its two stamp
  `setattr`s), the install probe (`_patch_is_installed`), the gated idempotent
  applier (`apply`), the stamp constants (`_PATCH_OWNER_ATTRIBUTE`,
  `_PATCH_ORIGINAL_ATTRIBUTE`, `_PATCH_OWNER`), the `ImportError -> None`
  import sentinel, and the module docstring (bug record, independent gate key,
  retirement condition).
- Consumer edges (compose by name, not definitions): `apply()` gates on
  `conf.py::upstream_patches_enabled("graphql_core")`; `apps.py::ready()` calls
  `apply()` last of four; the guard composes upstream's own
  `graphql.pyutils.is_iterable` and the executor's own `is_awaitable`.
- Upstream contract oracle: installed graphql-core 3.2.8
  `execution/execute.py::ExecutionContext.complete_list_value`, whose
  `async_iterable_to_list` holds a bare `return self.complete_list_value(...)`
  with no `await` (probe S3).
- Oracles: `tests/test_graphql_core_patches.py` (8 test functions, 10 collected
  rows: lifecycle, idempotence, self-heal, residual sentinel, signature drift,
  three missing-symbol refusals, independent `graphql_core`-vs-`strawberry`
  gate, global disable, None-owner capture);
  `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_iterable_with_awaitable_children_completes_over_http`
  (the wire delta: async-iterable + awaitable children completes to data; its
  docstring states a sync-children request would pass without the patch, so the
  row discriminates — and it never names the patch module, a pure wire oracle);
  `tests/test_apps.py` (four-patch dispatch + double-reload capture retention,
  parametrized over all four modules); `tests/base/test_conf.py` (gate
  vocabulary rows).
- Projections: the target docstring itself; `conf.py::UPSTREAM_PATCH_DEPENDENCIES`
  comment (the `graphql_core` independence clause); `apps.py::ready` docstring
  (four-module dispatch, no inventory); spec-050 rationale Decision 13
  (dependency-owned lifecycle; durable home of R3); `docs/GLOSSARY.md`
  ("Upstream patches" entry, incl. "either workaround can be disabled or
  retired without changing the other"); `docs/TREE.md` module one-liners
  (generated); `CHANGELOG.md` 0.0.15 executor-patch entry (history).

Sites found outside the target, by mechanism sweep (HEAD `69a25369`,
populations printed with each sweep; every verdict-relevant sweep re-run at
HEAD bytes via `git grep`, identical to the worktree probe):

- Patch-stamp mechanism (`_PATCH_OWNER_ATTRIBUTE` literal): exactly the four
  patch modules. No fifth site.
- Install/validate/capture vocabulary (`_patch_is_installed`,
  `_validate_upstream_shape`, `_captured_upstream*`): the same four modules
  (definitions) plus test consumers. `def apply(` exists in 6 production files:
  the four patch appliers plus `filters/sets.py::FilterSet.apply` (classmethod,
  filter application) and `optimizer/plans.py` `apply(self, queryset)` (plan
  application) — disjoint contracts, excluded on body strength.
- `complete_list_value` in production: this module only. `is_iterable` /
  `_await_residual`: this module only. `def _captured_upstream_method(`: exactly
  two modules (this one + `_strawberry_patches.py`, the same-name near-twin).
  The `startswith("django_strawberry_framework.")` capture arm: this module only.
- `upstream_patches_enabled("graphql_core")` (gate call) and
  `{"graphql_core": False}` (hint): this module only (hint on 2 adjacent lines).
  Production gate call sites overall: exactly the four `apply()` gates.
- `AsyncIterable` in production: 6 files — this module (executor-branch mirror),
  `utils/querysets.py` (the `is_async_only_iterable` predicate + refusal, R1),
  `connection.py` (Relay pagination async-shape dispatch + source guard, bodies
  read), `list_field.py` (predicate call sites — consumers, sweep-classified),
  `types/resolvers.py` + `resource_policy.py` + `utils/execution_mode.py` (prose
  mentions, no definition).
- `raise RuntimeError(` across the four patch modules: 12 sites, of which 11
  carry the `Cannot apply django-strawberry-framework's ...` refusal grammar
  (3 + 3 + 2 + 3); the 12th is django's hint-less teardown invariant.
- Root `__init__.py` never mentions the patch modules (private by contract);
  `apps.py` dispatches exactly 4 appliers in listed order.

Prior cycle records checked as triggers only: the overwritten
`Run: 0.0.15 2026-09-18-1` artifact on this same path (its C4/C5/C6 triggers
re-traced fresh below as R1/R2/R3; its capture-strictness observation re-derived
as an F1-assign divergence; every count re-derived by the fresh probe — nothing
imported); the run-2 verified siblings `dry-file-_cross_web_patches.md` (F1/F2)
and `dry-file-_django_patches.md` (F1-assign/F2-assign) — assigned to, not
re-named, with their counts confirmed and divergences noted from this side
under F1-assign/F2-assign. Fresh trace below.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED, hit. The four patch modules are
   the mirror: each spells the full safe-replacement lifecycle (import sentinel,
   stamp, capture, validation, install probe, gated applier) in local
   vocabulary. All three siblings read in full and compared by
   behavior/contract, not shape: django REIMPLEMENTS a teardown loop (pins a
   SET of two audited upstream bodies + stores the validated source for
   teardown-time reads); strawberry WRAPS three methods by delegation but
   REIMPLEMENTS `parse_query_params` (pins that one body; installs four members
   atomically); cross_web REPLACES one property with the async contract and
   never calls the captured getter; this module WRAPS one executor method by
   pure delegation (pins call shape only — upstream body changes flow through
   the delegated call). Yields F1-assign (mechanism) + F2-assign (wording).
   Non-patch flavors share no rule with this target (`complete_list_value`,
   `is_iterable`, `_await_residual` each single-filed here; the `AsyncIterable`
   neighbors classify as predicate/refusal, dispatch, consumers, or prose —
   see System trace).
2. Sync/async twins — SEARCHED, no twin defined here. The target defines zero
   top-level `async def` (probe S1); the single `async def _await_residual` is
   nested inside the sync wrapper — one in-module helper, not a twin pair. One
   install covers both executors by construction: `complete_list_value` is the
   single seam the sync and async executors flow through (the wrapper is sync
   and returns either a plain value or a coroutine). The patch family's only
   async twin (strawberry's sync/async multipart delegates) is
   strawberry-internal and shares no member with this target. No behavior pair
   in-target can drift.
3. Derived rather than repeated knowledge — SEARCHED, hit inside F1-assign and
   L1. The install-state question is answered once (`_patch_is_installed`,
   identity compare); the capture-vs-live split (validate pins the import-time
   capture, the probe reads the live attribute) is deliberate and pinned by
   `test_apply_reinstalls_a_reverted_executor_method` and the double-reload
   rows. The six-parameter signature is derived once via `inspect` at validate
   time, never restated. The guard's `not is_iterable(result)` half composes
   upstream's own imported predicate by name. The gate name is consumed by
   passing the string to single-owned `conf.py::upstream_patches_enabled`;
   the canonical set is single-owned at `conf.py::UPSTREAM_PATCH_DEPENDENCIES`.
   The per-module test re-derives installed-state by direct `__dict__` identity
   compare as an independent oracle (oracles never read from the owner they
   check) — listed, not counted.
4. Inverse / round-trip pairs — SEARCHED, discharged both halves. Lifecycle:
   install-once process-global; revert exists only as test scaffolding (restore
   saved attributes by identity), not a product round-trip, and no contract
   requires an uninstall half — inapplicable with reason (same as both sibling
   items). Retirement-signal pair: the sentinel oracle
   (`test_captured_upstream_still_returns_a_residual_awaitable`, which drives
   the CAPTURED upstream method, not a hardcoded copy) flips exactly when
   upstream no longer leaves a residual. The capture-read/install-write kind
   agreement (plain attribute <-> plain assign) is recorded inside L2 as a
   kind-parameterized pair.
5. Contracts restated in another medium — SEARCHED, classified. Gate semantics:
   owned by `conf.py::upstream_patches_enabled`, projected by this docstring,
   composed by name in `apply()` (no restatement in code). Dispatch order:
   owned by `apps.py::ready`. One-module-per-dependency organizing rule: owned
   by spec-024 Decision 1, instantiated for this member by spec-050 Decision 13
   (File `apps.py`/`conf.py` items enumerate it). Bug narrative + retirement
   condition: this docstring is the sole definition (L3); the sentinel oracle
   is its standing re-check. GLOSSARY/TREE.md/CHANGELOG lines are projections
   or history. Test `match=` substrings pin F2 message fragments as oracles
   (listed, not counted).
6. Enforcement by omission — SEARCHED, no gap. Input family partitioned three
   ways against the guard `not is_iterable(result) and isinstance(result,
   AsyncIterable) and self.is_awaitable(res)`, probe-executed against the REAL
   bodies (S4a/b/c): (a) sync-iterable input takes upstream's inline branch —
   patch passes the value through unwrapped; (b) async-iterable input with
   all-synchronous completion — the wrap is entered (the outer coroutine is
   awaitable) but observably neutral (await yields data, not awaitable);
   (c) async-iterable input with awaitable children — the residual, the wrap
   required (unpatched leaves an awaitable after one await that resolves to
   the genuine completion; patched resolves to data). The guard mirrors
   upstream's branch so the patch touches only the path known to exhibit the
   defect — minimal blast radius, not a second policy. Executor coverage needs
   no per-executor guard (one seam, axis 2). No member lacks a guard its
   contract requires.

### Enumeration

Instrument: every statement in `ast.Module.body` of the target at HEAD
(17 nodes; verified by executing `ast.parse` over the file — probe S1).
Rule-bearing members (13) each land below in an assignment (F1-assign/F2-assign),
a file-local row (L1/L2/L3), or a rejection (R1/R2/R3); node 4 is a consumer edge;
the 3 plain imports carry no rule.

| # | `ast` node | Name / content | Home |
|---|---|---|---|
| 0 | Expr (docstring) | bug record, gate key, retirement condition | L3 (+ F1/F2 projections noted) |
| 1 | Import | `inspect` | — (machinery for F1-assign validation) |
| 2 | ImportFrom | `AsyncIterable` | — (machinery for the L1 guard) |
| 3 | ImportFrom | `typing.Any` | — (machinery, annotations) |
| 4 | ImportFrom | `.conf::upstream_patches_enabled` | — (consumer edge; rule owned by File `conf.py`) |
| 5 | Try | `ExecutionContext` + `is_iterable` import / `except ImportError -> None` | F1-assign (import sentinel) |
| 6 | Assign | `_PATCH_OWNER_ATTRIBUTE` literal | F1-assign (stamp identity) |
| 7 | Assign | `_PATCH_ORIGINAL_ATTRIBUTE` literal | F1-assign (stamp identity) |
| 8 | Assign | `_PATCH_OWNER` per-module value | F1-assign (stamp identity) |
| 9 | FunctionDef | `_captured_upstream_method` (prefix arm, no docstring) | F1-assign (recovery) + L2 (plain-method spelling) |
| 10 | Assign | `_original_complete_list_value` import-time capture | F1-assign (capture + stored derivation) |
| 11 | FunctionDef | `_validate_upstream_shape` (presence + 6-param sig; no body pin — delegator) | F1-assign (validation step) + F2-assign (2 messages) |
| 12 | FunctionDef | `_patched_complete_list_value` (+ nested `_await_residual`) | L1 (residual-await rule) |
| 13 | Expr | `setattr` owner stamp | F1-assign (marking) |
| 14 | Expr | `setattr` original stamp | F1-assign (marking) |
| 15 | FunctionDef | `_patch_is_installed` | F1-assign (install check) + L2 (identity-read kind) |
| 16 | FunctionDef | `apply` | F1-assign (4-step order) + gate consumer edge |

Count check: 17 nodes enumerated, 13 rule-bearing nodes assigned (3 of them
split across two rows by aspect: 9, 11, 15), 1 consumer-edge import, 3 imports
correctly rule-free. Nothing unassigned.

### Challenges

Change challenges per rule (consumers/oracles/projections listed, never
counted). LC/W challenges confirm the sibling items' counts from this module's
side; R/K/G/P challenges prove single ownership or refuse with a contract
difference.

- LC-C1 (stamp rename): rename the `_PATCH_OWNER_ATTRIBUTE` value. Forced moves:
  the literal + capture read + two marking writes in each of the 4 patch
  modules. Count: **4 authoritative definitions**. (This module touches: nodes
  6, 9, 13, 14.)
- LC-C2 (apply order): check installed-before-validate (skip validation when
  already installed). Forced moves: all 4 `apply()` bodies (all spell gate ->
  validate -> installed-check -> install; django stores its validated source
  between validate and check). Count: **4**.
- LC-C3 (sentinel convention): replace the `None` missing-shape sentinel with
  a dedicated marker. Forced moves: the `None` reads in all 4 modules'
  captures, probes, and validators (here: node 5 write, node 9/11/15 reads).
  Count: **4**.
- LC-C4 (capture tolerance): a capture must additionally tolerate an unstamped
  third-party wrapper by wrapping it instead of replacing it. Forced moves:
  all 4 capture functions (each spells replace-semantics today — here an
  unmarked method is returned as genuine). Count: **4**.
- W-C1 (hint reword): reword the shared `Disable this patch with
  APPLY_UPSTREAM_PATCHES = {"<dep>": False} ... or use a supported ...`
  grammar. Forced moves: 11 raise sites across the 4 modules (this module
  contributes node 11's 2 raises). Count: **11 sites / 4 module wordings**.
- R-C1 (retirement): upstream awaits the recursive completion internally (or
  restructures the branch). Forced moves: this module deletes outright; the
  other three patch modules untouched; the sentinel oracle flips to the
  retirement signal; the wrap is observably neutral post-fix (S4b shape), so
  retirement is hygiene, not repair. Count: **1**.
- R-C2 (await depth): the residual needs deeper/different awaiting. Forced moves:
  `_await_residual` + guard co-move in-module. Count: **1**.
- R-C3 (seam change): upstream renames `complete_list_value` or changes arity.
  Forced moves: capture name + sig check co-move; anything else fails loud at
  `apply()`. Count: **1**.
- R-C4 (unify detection with `is_async_only_iterable`): **0** moves — refused
  (upstream-branch mirror vs resolver-source classification; R1).
- R-C5 (one residual policy with `awaitable-refusal-and-disposal`): **0** moves
  — refused (executor-internal completion vs consumer-boundary refusal; R2).
- R-C6 (fold the wrapper into `_strawberry_patches.py`): **0** moves — refused
  (dependency-owned lifecycle; durable home spec-050 Decision 13; R3).
- K-C1 (kind reshape): upstream makes the member a property. Forced moves: only
  this module's plain-method kind spellings (nodes 9/15/16) — siblings patch
  disjoint kinds (property x1, classmethod x1, plain x1 twin as F1's parameter).
  Count: **1**.
- G-C1 (gate rename): the `graphql_core` key is renamed. Forced moves: `conf.py`
  owns the key; this `apply()` passes only its dependency name as consumer
  (hint spellings follow as F2 projections). Count: **1** (in `conf.py`).
- P-C1 (status-prose change, e.g. upstream fixes the bug): only this docstring
  moves (GLOSSARY follows as projection, never counted). Count: **1**.

Experiment: one read-only probe, `execution-verified` (ALL OK, 9 sections),
replayable at
`docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/probe_graphql_core_patches.py`:

```shell
uv run python docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/probe_graphql_core_patches.py
```

Output: target `__file__` printed as the shared-tree copy (read-only probe, no
workspace owed, no DB opened); S1 17-member AST count with kind list (5
FunctionDef, 0 top-level AsyncFunctionDef, 1 nested `_await_residual`); S2
capture is the live unmarked upstream method with the 6-param
all-`POSITIONAL_OR_KEYWORD` shape; S3 upstream source holds the bare
`return self.complete_list_value(` with no `await` (graphql-core 3.2.8); S4a/b/c
three-way partition executed against the REAL captured and patched callables
(sync passthrough; neutral wrap; defect-then-fix with the residual proven to be
the genuine pending completion); S5 gated install idempotent + self-healing
under minimal settings; S6 package population 117 `.py` files with the
owner-attr literal in exactly the four patch modules, the
`upstream_patches_enabled("graphql_core")` gate call and the
`{"graphql_core": False}` hint each single-sited here, `complete_list_value` /
`is_iterable` / `_await_residual` single-sited here,
`def _captured_upstream_method(` in exactly two modules, the prefix arm unique
here, 11 refusal literals / 12 `raise RuntimeError(` across the four patch
modules, exactly 4 production gate call sites, `__init__.py` patch-free,
`apps.py` dispatching exactly 4 appliers. Rejects the wrong results "upstream
already awaits the recursion", "the capture wrapped a previous package
install", "a second production site spells the gate, hint, predicate, or
install", "the patch wraps the sync path", "a top-level async twin exists",
"the residual is not the genuine completion".

## Findings

No production edit is owed by a file item; the two assignments below reuse the
already-open families (no new family named), the rest are file-local records
and rejections.

### F1-assign — Upstream-patch safe-replacement lifecycle (assign to open family `upstream-patch-lifecycle`)

- Contract + variation: as named by the cross_web item (F1 there): how a patch
  module safely replaces one upstream member process-wide (import sentinel,
  genuine capture, owner/original stamps, presence + call-shape validation,
  idempotent self-healing install, per-dependency gate). This module's aspects:
  `None`-sentinel import (node 5), stamp literals (nodes 6-8), reload-tolerant
  recovery (node 9, concept), import-time capture (node 10), two-tier validation
  presence/signature (node 11, mechanism), two marking writes (nodes 13-14),
  identity install check (node 15, concept), gate -> validate -> installed-check
  -> install order (node 16). Legitimate variation (this module's parameters):
  dependency key `"graphql_core"`, plain-method descriptor kind, delegator depth
  (shape-only pin, no body pin).
- Sites + roles (definitions): this module's nodes above, jointly with the three
  sibling aspects the cross_web and django artifacts inventoried (property kind,
  classmethod kind + 2-body set, 4-method conjunction). Consumers:
  `apps.py::ready` (this module dispatched last of four);
  `tests/test_apps.py::_PATCHED_SLOTS` + `_all_patches_installed`. Oracles: the
  10-row per-module suite (lifecycle, drift refusals, both gate spellings,
  sentinel, None-owner capture), the `test_apps.py` dispatch + double-reload
  rows, the live completion row for the behavior half. Projections: this docstring's
  lifecycle sentences, `conf.py::UPSTREAM_PATCH_DEPENDENCIES` comment, GLOSSARY
  entries.
- Challenges: LC-C1 count 4; LC-C2 count 4; LC-C3 count 4; LC-C4 count 4 (see
  `### Challenges`). The sibling items' LC counts are confirmed from this
  module's side with zero conflicts.
- Owner + lifetime: TBD by the family item (unchanged by this assignment).
  Lifetime: process-global from `AppConfig.ready()`; reload-safe by stamp
  recovery (principle 4 for this module's stored derivation
  `_original_complete_list_value`: owner — the module import; validity key —
  the installed graphql-core release, any drift failing loud at `apply()`;
  publish point — import time, before `apply()` can replace; who may mutate —
  nobody, rebound only by reload which re-captures through the owner mark;
  invalidation — never within a process).
- Migration: for the family item to decide (driver with kind adapters vs
  recorded per-module ownership). This module's kind adapter, if extracted, is
  L2; its behavior rule L1 stays here regardless.
- Distinct behavior (stays separate whatever the family decides): the
  plain-method kind spellings (L2); the delegator's shape-only pin (this module
  and cross_web pin call shape; the reimplementers pin body source); the
  single-identity probe (vs strawberry's 4-member conjunction); no validated
  state carried across reload (vs django's L4). In-family divergences for the
  family item (observed from this side, not decided here): (a) this module's
  capture accepts any `django_strawberry_framework.*` owner prefix where the
  other three require exact `_PATCH_OWNER` equality — CONFIRMED (here lines
  39-41 vs strawberry:414, cross_web:230, django:149; unreachable today,
  disjoint members, no contract source requires exactness); (b) this module's
  `_captured_upstream_method` carries no docstring where its strawberry same-name
  twin does — CONFIRMED; (c) this module's `pragma: no cover` comment reads
  "exercised through patched imports in tests." where the other three read
  "exercised via monkeypatch in tests" — CONFIRMED by sweep; (d) this module's
  docstring carries no Surface-visibility section where the other three do —
  CONFIRMED by sweep (prose gap; no contract requires the section).
- Behavioral proof: definition counts `static-reviewed` (mechanism sweeps with
  populations, re-verified at HEAD bytes). Lifecycle liveness
  `execution-verified`: S2 (capture IS the live unmarked upstream method in a
  bare process), S5 (gated install idempotent + self-healing under minimal
  settings). Permanent oracles (dispatch, double-reload, idempotence, self-heal
  rows) `static-reviewed` — exist at HEAD, run at the gate. Rejects "a fifth
  install site exists" and "the capture wrapped a prior package install".
  Replay: `uv run python
  docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/probe_graphql_core_patches.py`.
- Structural gate + negative control: owed by the family item (named by the
  cross_web item; e.g. a population-enumerated check over the four modules'
  lifecycle members). Negative-control shape: a hand copy of the lifecycle with
  one step reordered or one stamp renamed must fail the gate while every
  behavioral oracle stays green. No gate proposed here beyond the requirement.
- Coupling: F2-assign (wording lives inside the same `apply()`/`validate`
  bodies — land together or sequence explicitly); L2 (the kind adapter this
  validation's capture/probe/install spellings parameterize); sibling File items
  (`conf.py`, `apps.py`, `_strawberry_patches.py`) trace the same sites from
  their side; Worker 0 dedups identical namings.
- Freshness: target `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`;
  `_cross_web_patches.py` `6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`;
  `_django_patches.py` `ba98f5859ec32971c3aa566c221bdc4db392e137`;
  `_strawberry_patches.py` `f77df3499eb96051d70055266a677ca3cde5b219`;
  `conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`;
  `apps.py` `8ae1a3a3b12f0c9792094959c573ea6fab5d804f`;
  `tests/test_graphql_core_patches.py`
  `53dca51737e6163c09549d015713ebf9dfcdec88`;
  `tests/test_apps.py` `5ca8b62c53185343ebfec95315f59ec6104fc851`;
  `tests/base/test_conf.py` `f35c70742354d0ab123b163a92c6a8a503c6ea29`;
  `docs/GLOSSARY.md` `bc51debc54cf3ed142b45fa9feda1b99bce60c79`;
  installed graphql-core 3.2.8 `execution/execute.py` blob
  `869f59f3f5662fc55e3dbb48023e6879dab40a8a` (`git hash-object` of the installed
  file). All tracked inputs above CLEAN (worktree == HEAD `69a25369`).
  Searched populations: `_PATCH_OWNER_ATTRIBUTE` literal -> 4 production files;
  `_patch_is_installed|_validate_upstream_shape|_captured_upstream` -> 4
  production + test consumers; `upstream_patches_enabled("` production call
  sites -> exactly the 4 `apply()` gates;
  `def _captured_upstream_method(` -> 2 modules;
  `startswith("django_strawberry_framework.")` -> 1 module;
  `def apply(` -> 6 files (4 patch appliers + 2 disjoint contracts).
  Excluded on body strength: `filters/sets.py` (HEAD
  `4ab65a26b0ccf56f7f40f4938282bba9690673d1`, worktree DIRTY hunt-concurrent
  `4a40e51b288cad04cce3124697874c399d33f0fc` — `FilterSet.apply` classmethod is
  filter application, no gate/validate/install vocabulary; hunt diff touches no
  `def apply(` line) and `optimizer/plans.py` (`cce985319c8833f3660653327d3003f1f03655a5`,
  CLEAN — `apply(self, queryset)` is plan application).

### F2-assign — Upstream-patch refusal wording (assign to open family `upstream-patch-refusal-wording`)

- Contract + variation: as named by the cross_web item (F2 there): the
  `RuntimeError` grammar every patch `apply()` raises on unsupported upstream
  shape (`Cannot apply django-strawberry-framework's <patch> patch:
  <expected-shape> ... Disable this patch with APPLY_UPSTREAM_PATCHES =
  {"<dep>": False} or use a supported <version-noun>.`). This module's aspects:
  node 11's 2 raises (presence tier naming
  `ExecutionContext.complete_list_value` + `graphql.pyutils.is_iterable`, and
  the 6-param signature tier) — both carrying the `{"graphql_core": False}`
  hint, the `graphql-core patch` name, and the `graphql-core version` noun.
- Sites + roles (definitions): this module's 2 raises, jointly with the 9
  sibling raises the cross_web and django artifacts inventoried (3 + 3 + 3).
  Oracles (listed): per-module `match=` fragments (`complete_list_value no
  longer`, `ExecutionContext.complete_list_value`, `graphql.pyutils.is_iterable`
  here). Projections: module-docstring opt-out spellings, `conf.py` gate
  docstring, GLOSSARY "kill switch" entry.
- Challenges: W-C1 count 11 sites / 4 module wordings (this module: 2) —
  confirmed from this side (HEAD `git grep -c`: 3 + 3 + 2 + 3; 12th
  `raise RuntimeError(` is django's hint-less teardown invariant, not a member).
- Owner + lifetime: TBD by the family item (unchanged by this assignment;
  natural candidates recorded by the cross_web item).
- Migration: the family item's decision (one message builder vs recorded
  deliberate per-module wording). The `match=` oracles move as oracles, never
  rewritten to read from a builder.
- Distinct behavior: the per-site expected-shape clauses stay per-module (they
  name disjoint upstream members); only the shared opt-out/two-exit framing is
  the family's.
- Behavioral proof: `static-reviewed` (literal sweeps at HEAD + worktree;
  wording has no runtime behavior beyond the raised text, which the `match=`
  oracles pin). The hint's end-to-end truth (gate precedes validation, so the
  named escape silences the abort) is pinned by permanent oracle
  `test_apply_uses_independent_dependency_gate` (`static-reviewed` — exists at
  HEAD, runs at the gate). Rejects "a 12th refusal site exists" and "a refusal
  lacks the hint".
- Structural gate + negative control: owed by the family item (named by the
  cross_web item: pin the hint spelling against `UPSTREAM_PATCH_DEPENDENCIES`
  keys + the gate's accepted shapes; negative control: a message with a renamed
  key passes behavior oracles but fails the gate).
- Coupling: F1-assign (same bodies; sequence together). Sibling File items as
  in F1-assign.
- Freshness: production fingerprints as in F1-assign; oracles
  `tests/test_graphql_core_patches.py`, `tests/base/test_conf.py` as above.

### L1 — Residual-awaitable list completion (file-local)

- Contract + variation: the delegating wrapper plus its double-await helper:
  delegate every call to the captured upstream method, but when the input took
  upstream's async-iterable branch (`not is_iterable(result)` and an
  `AsyncIterable`) and the delegated call returned an awaitable, await that
  residual — twice if the first await yields a second awaitable — instead of
  letting an unawaited coroutine escape to the executor. Varies only with this
  upstream defect's shape (await depth, branch predicate, seam name). The three
  guard conjuncts co-move in-module by design (axis 6: they scope the wrap to
  the defective path).
- Sites + roles: sole definition — node 12 (wrapper + nested `_await_residual`).
  Invoked process-wide by the executor once installed (no production caller).
  Oracles: the sentinel row (drives the CAPTURED body — retirement detector),
  the sig-drift/missing-symbol rows (the seam contract), the live HTTP row
  (wire delta, discriminating docstring). Projections: the docstring's bug
  sentences (L3), GLOSSARY/CHANGELOG lines.
- Challenges: R-C1 count 1 (one deletion on retirement, observably neutral even
  before it); R-C2 count 1 (depth moves helper + guard together); R-C3 count 1
  (seam moves capture + sig check, else fail loud). R-C4/R-C5/R-C6 refuse the
  considered unifications (R1/R2/R3).
- Owner + lifetime: the target module; dies with the module at retirement
  (upstream fix -> sentinel flips -> deliberate outright deletion, per the
  docstring's "retired independently").
- Migration / Distinct behavior / Coupling: none pending; coupled to F1-assign
  by residence only (the lifecycle installs it; the rule is independent of the
  lifecycle's shape).
- Behavioral proof: `execution-verified` — S3 (installed 3.2.8 body holds the
  un-awaited recursion) + S4a/b/c (sync passthrough unwrapped; sync-children
  wrap neutral; unpatched leaves the genuine residual, patched resolves to
  data). The permanent oracles above are `static-reviewed` (exist at HEAD, run
  at the gate). Rejects "upstream already awaits the recursion", "the patch
  wraps the sync path", "the residual is not the genuine completion". Same
  replay command as F1-assign.
- Structural gate + negative control: none owed (single site; the live row
  fails if the rule is silently removed — a residual escaping to the executor
  surfaces as `errors`, which the row asserts absent — and the sentinel row
  fails if the defect it diagnoses ever disappears).
- Freshness: target + `tests/test_graphql_core_patches.py` +
  `examples/fakeshop/test_query/test_list_field_async_api.py`
  (`49e423ea593b8883c4c07593accd822390e82468`, CLEAN) + installed upstream blob
  as in F1-assign.

### L2 — Plain-method capture/install/probe spelling (file-local kind adapter)

- Contract + variation: the descriptor-kind parameter of F1-assign as spelled
  for a plain-method target: `owner.__dict__.get(name)` + exact-or-prefixed
  owner recovery in the capture, plain-identity read in the probe, plain
  attribute install. Varies only with this upstream member's descriptor kind.
- Sites + roles: sole definitions — the kind-specific lines of nodes 9/15/16.
  Siblings patch disjoint kinds (property x1, classmethod x1) or share the
  plain kind as F1's parameter (strawberry's same-name twin, exact-match where
  this one is prefix-tolerant — the strictness divergence is F1-assign's,
  reconciled by the family item, not a second site of THIS spelling).
  Descriptor-kind sweep: property x1 (cross_web), classmethod x1 (django),
  plain x2 (strawberry + here). Oracles: double-reload
  capture-retention rows, the None-owner row, the self-heal row.
- Challenges: K-C1 count 1 (a kind reshape moves only this module). G-C1
  confirms the gate key is not owned here.
- Owner + lifetime: the target module (kind adapter of the F1-assign machine,
  wherever F1 lands — the family item may relocate this spelling as F1's plain
  adapter; until then it lives here).
- Migration / Distinct behavior: none pending; if F1 extracts a driver, this row
  becomes that driver's plain adapter (with the strictness parameter settled
  there).
- Behavioral proof: `static-reviewed` (kind sweep + the oracles above). Kind
  facts `execution-verified`: S2 (live member is a plain unmarked function;
  capture recovers it by identity), S5 (install + self-heal through the plain
  spelling). Same replay command.
- Structural gate + negative control: none owed (single site).
- Coupling: F1-assign (kind adapter of that machine).
- Freshness: target + three sibling fingerprints as in F1-assign +
  `tests/test_apps.py` as above.

### L3 — Module status prose: bug, gate key, retirement (file-local)

- Contract + variation: the module docstring's graphql-core-specific record —
  bug mechanics (async-iterable materialization + un-awaited residual),
  the independent `APPLY_UPSTREAM_PATCHES` key `"graphql_core"`, and the
  retirement condition (captured implementation no longer exhibits the bug
  pinned by `tests/test_graphql_core_patches.py`). Varies only with this
  upstream's history.
- Sites + roles: sole definition — node 0 (the graphql-core-specific sentences;
  the lifecycle/gate sentences project F1-assign/`conf.py` rules). The sentinel
  oracle named in the retirement sentence is the standing re-check; the
  GLOSSARY/TREE.md/CHANGELOG lines are projections.
- Challenges: P-C1 count 1 (only this docstring moves; GLOSSARY follows as
  projection, never counted).
- Owner + lifetime: the target module; dies with the module at retirement.
- Migration / Distinct behavior / Coupling: none (file-local prose).
- Behavioral proof: the falsifiable halves `execution-verified` — S3 (defect
  present in the installed tree as described), S5 (install runs under the
  default gate; opt-out rows pin the key), S2 (capture is the implementation
  the retirement sentence names). The retirement-test name resolves
  (`tests/test_graphql_core_patches.py` exists with the sentinel row —
  `static-reviewed`). Rejects "the prose describes a fixed bug" and "the named
  retirement test does not exist".
- Structural gate + negative control: none owed (unique prose; no bypass
  population).
- Freshness: target + `tests/test_graphql_core_patches.py` + `docs/GLOSSARY.md`
  + `docs/TREE.md` (`c0b0b909f0cb8332bef26a9e5cc035497b2f2173`, CLEAN) +
  `CHANGELOG.md` (`d4e1035554f14ccd6563f67198c4ef59cd705aa1`, CLEAN).

### R1 — Guard predicate vs `is_async_only_iterable` (rejected)

- Contract + variation: two async-iterable spellings that look like one rule
  and are two. This module's guard half (`not is_iterable(result) and
  isinstance(result, AsyncIterable)`) mirrors upstream's own branch predicate
  using upstream's own imported `is_iterable`: it must move if and only if
  graphql-core's branch moves. `utils/querysets.py::is_async_only_iterable`
  (`isinstance(value, AsyncIterable) and not isinstance(value, Iterable)`)
  classifies resolver SOURCES for the package's sync-misuse refusal, with the
  QuerySet both-protocols carve-out ("a Django QuerySet is both sync and async
  iterable and must never classify as async-only"). Concrete contract
  difference: the mirror's first half must track upstream's branch exactly
  (built on upstream's own `is_iterable`), while the classifier's
  `not Iterable` half exists for the package's QuerySet carve-out — different
  primitives answering different questions. A mapping carrying `__aiter__`
  separates them: upstream's `is_iterable` rejects mappings, so upstream takes
  its async branch and the mirror must wrap, while the package predicate sees
  `__iter__` and classifies it not-async-only, so a unified guard would skip
  the wrap and let the residual escape. Conversely an upstream
  branch-predicate change must move the mirror without moving package refusal.
  A shared-form consolidation (one async-iterable predicate) would own the
  English phrase and destroy the change-direction split both docstrings exist
  to protect. Reconsideration trigger: if graphql-core's branch predicate and
  the package's source classification ever needed to move on one change (e.g.
  upstream adopting the package predicate as its branch), the two become one
  rule — consolidate then.
- Sites + roles: two independent definitions (rejected pair). Target node 12
  guard; `utils/querysets.py::is_async_only_iterable` (+ its consumers
  `reject_async_iterable_in_sync_context`, `list_field.py`, `connection.py`,
  `resource_policy.py` — listed, not counted).
- Challenges: R-C4 count 0 per direction (neither direction's change may move
  the other). A shared form would own 0 executable lines that both sides could
  keep.
- Owner + lifetime: unchanged — each side keeps its owner.
- Migration: none (rejection).
- Distinct behavior: preserved exactly — upstream-mirror vs
  source-classification ARE the observable distinction (the carve-out fires on
  one side only).
- Behavioral proof: `static-reviewed` — rests on reading both predicates (the
  mirror's upstream-`is_iterable` composition vs the classifier's QuerySet
  carve-out). The guard's runtime behavior is `execution-verified` (S4a/b/c).
  Rejects "the guard respells the package predicate".
- Structural gate + negative control: none owed (rejection, no owner to bypass).
- Coupling: L1 (the guard side of the pair).
- Freshness: target as above; `utils/querysets.py`
  `96618fba4eafb6a87e73414770014e3aee5b41ef` (CLEAN); `connection.py` HEAD
  `93e998f2c7ea1d7f18607a6e37e394466ac75ad` / worktree
  `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` (DIRTY hunt-concurrent: +55-line
  insertion at ~703; the three cited bodies byte-identical at HEAD lines 1050 /
  1095 / 1575, hunt diff holds zero `AsyncIterable` lines — exclusion stands on
  both byte sets); `list_field.py` HEAD
  `ce682d5f79518919ff3676f2fc8bbe2bd33995a4` / worktree
  `d6af61646784deac2f3053bb4096b8599deae2f5` (DIRTY hunt-concurrent;
  sweep-classified consumer, no body claim); `resource_policy.py`
  `647133d23785d325856b2d1d495d18c5741dd23c` (CLEAN);
  `types/resolvers.py` HEAD `f3341e6a9f52659925762bce097033bac67e3b51` /
  worktree `5f4cce2b1bb37b75af4239f264ed0049a9faa5c9` (DIRTY hunt-concurrent;
  prose mention only, no body claim); `utils/execution_mode.py`
  `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9` (CLEAN; prose mention only).
  Excluded on body strength: `connection.py` (Relay pagination async-shape
  dispatch + source-shape guard — pagination contracts, not executor
  completion), `utils/querysets.py` (predicate + refusal, this rejection's
  other side), `schema.py` (`c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`, CLEAN —
  write-transaction field-result completion await, a transaction contract).

### R2 — Residual completion vs awaitable-refusal-and-disposal (rejected)

- Contract + variation: two residual-awaitable policies that look like one rule
  and are two. This module COMPLETES an executor-internal residual (await it,
  twice if needed — L1): the value is upstream's own pending completion and
  awaiting it is the only correct handling. The open family
  `awaitable-refusal-and-disposal` (owner
  `utils/querysets.py::_dispose_sync_awaitable`) REFUSES a consumer-returned
  residual at a sync/async boundary: fail closed with `SyncMisuseError` and
  dispose without awaiting (close coroutines, cancel futures — "those must not
  recursively await an unbounded chain, so disposal is the only safe handling
  there too"). Concrete contract difference: opposite actions (await vs
  close/cancel) at different layers (executor seam vs consumer boundary) with
  different reasons to change (upstream defect shape vs caller-context
  discipline). A shared-form consolidation (one residual policy) would own the
  English word "residual" while each remainder kept its entire mechanism.
  Reconsideration trigger: if one residual policy ever governed both the
  executor seam and the consumer boundaries (e.g. executor-internal residuals
  needing refusal, or consumer residuals needing completion) — consolidate then.
- Sites + roles: two independent definitions (rejected pair). Target node 12
  (+ helper); `utils/querysets.py::_dispose_sync_awaitable` + the family index
  row's enforcement sites (listed, not counted; the undispatched family item
  re-sweeps regardless).
- Challenges: R-C5 count 0 per direction (completing a consumer residual hides
  a caller bug; refusing the executor residual breaks every async-iterable
  list).
- Owner + lifetime: unchanged — each side keeps its owner.
- Migration: none (rejection).
- Distinct behavior: preserved exactly — await-to-data vs fail-closed-plus-
  dispose ARE the observable distinction.
- Behavioral proof: `static-reviewed` — rests on reading both mechanisms (the
  double-await helper vs close/cancel disposal). The completion half is
  `execution-verified` (S4c-fix). Rejects "the wrapper is a second disposal
  site".
- Structural gate + negative control: none owed (rejection, no owner to bypass).
- Coupling: L1 (the completion side of the pair).
- Freshness: target + `utils/querysets.py` as in R1.

### R3 — Executor-wrapper home vs `_strawberry_patches.py` (rejected)

- Contract + variation: one module-placement question, answered by dependency
  ownership, not dependency topology. The wrapper COULD live in
  `_strawberry_patches.py` (graphql-core is a transitive Strawberry
  dependency), but the patched callable, upstream release cadence, retirement
  signal, and consumer opt-out all belong to graphql-core, while the HTTP-view
  patch has a different owner and a different retirement condition. Concrete
  contract difference: separate gates and separate end dates — folding them
  couples unrelated escape hatches and lets an HTTP-view opt-out
  (`{"strawberry": False}`) silently restore an executor bug. The independent
  gate is pinned by oracle (`{"strawberry": False}` leaves this patch
  installing) and projected by GLOSSARY ("either workaround can be disabled or
  retired without changing the other"). Reconsideration trigger: if the
  graphql-core workaround ever shared strawberry's retirement/opt-out lifecycle
  (one gate, one end date) — consolidate then. Durable home: spec-050
  rationale Decision 13 already records this rejection at the owner ("Rejected:
  Keeping the executor wrapper in `_strawberry_patches.py`..."); this artifact
  re-checks it, it does not move it.
- Sites + roles: two independent definitions (rejected pair). Target module;
  `django_strawberry_framework/_strawberry_patches.py` (whose docstring's
  three-lifecycles record names only HTTP-view concerns).
- Challenges: R-C6 count 0 (no placement change is owed; the durable home
  already answers it).
- Owner + lifetime: unchanged — each module keeps its lifecycle.
- Migration: none (rejection).
- Distinct behavior: preserved exactly — per-dependency gates that move
  independently.
- Behavioral proof: `static-reviewed` — rests on reading Decision 13, the
  independent-gate oracle, and the GLOSSARY projection. The gate half is
  `execution-verified` (S5 installs under the default gate; the opt-out matrix
  is oracle-pinned). Rejects "topology decides module home".
- Structural gate + negative control: none owed (rejection, no owner to bypass).
- Coupling: L1 (the wrapper whose home is decided).
- Freshness: target + `_strawberry_patches.py` as in F1-assign +
  `docs/spec-050-list_field_arguments-0_0_15-rationale.md`
  (`8b88dc9d7ed268b1f77ccc54ee37c24b2466434f`, CLEAN) + `docs/GLOSSARY.md` as
  above.

## Defects

None found. Near-misses examined and ruled out (each checked against its
permanent oracle or live upstream bytes, not assumed):

- This module's prefix-match capture vs the other three modules' exact-match:
  an in-family contract divergence, recorded under F1-assign for the family
  item — not a defect (members are disjoint so no behavior differs; no contract
  source requires exactness; same ruling as both sibling items).
- This module's capture lacking the docstring its strawberry twin carries, the
  `pragma: no cover` comment wording divergence, and the missing
  Surface-visibility docstring section: prose gaps, not behavior (no contract
  source requires any of them).
- Guard conjunct order (`not is_iterable` first): mirrors upstream's branch
  order and short-circuits before touching the executor — the three-way
  partition is probe-executed, not assumed.
- Double-await depth: exactly upstream's nesting (outer coroutine, then at most
  the inner `get_completed_results` coroutine, which resolves to data) —
  S4c-fix proves resolution; a deeper escape cannot arise from the pinned
  6-param body shape, and any upstream restructure fails loud at `apply()`.
- Reload hazards (stale capture, pre/post-reload identity operands),
  `None`-sentinel mishandling, live-vs-capture confusion in validate-vs-probe,
  gate bypass: each traced to a passing permanent oracle (double-reload rows,
  missing-symbol refusal rows, both gate spellings, self-heal row). No guard
  any contract requires is missing (axis 6: full input partition, no gap).
- The upstream defect is still present at installed graphql-core 3.2.8 (S3 + S4c:
  bare un-awaited recursion; unpatched body leaves the genuine residual), so no
  retirement question arises this cycle.

## Pending execution

None. No `proof:` entry is owed: every conclusion resting on a probe is
`execution-verified` above (replay command recorded), and every other
conclusion rests on permanent oracles that the cycle gate runs.
`FAKESHOP_SHARDED=1` and Postgres cells are inapplicable by construction for
the probe-backed conclusions (pure import/source/shape facts plus in-memory
coroutine mechanics; the probe opens no connection and reads no database) —
stated here for Worker 2's judgment. The one database-touching oracle (the live
row, `django_db(transaction=True)`) is `static-reviewed` and runs at the gate
in default mode.

## Index rows for Worker 0

No new families: the lifecycle aspects assign to the already-open
`upstream-patch-lifecycle` row and the 2 refusal messages to the already-open
`upstream-patch-refusal-wording` row (no index edits owed for those). New rows:

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| Residual-awaitable list completion | `django_strawberry_framework/_graphql_core_patches.py::_patched_complete_list_value` | `django_strawberry_framework/_graphql_core_patches.py` | File `_graphql_core_patches.py` | file-local |
| Plain-method capture/install/probe spelling | `django_strawberry_framework/_graphql_core_patches.py::_captured_upstream_method` | `django_strawberry_framework/_graphql_core_patches.py` | File `_graphql_core_patches.py` | file-local |
| Module status prose: bug, gate key, retirement | `django_strawberry_framework/_graphql_core_patches.py` (module docstring) | `django_strawberry_framework/_graphql_core_patches.py` | File `_graphql_core_patches.py` | file-local |
| Executor-branch guard predicate vs `is_async_only_iterable` | `django_strawberry_framework/_graphql_core_patches.py` (rejection recorded in File artifact) | `django_strawberry_framework/_graphql_core_patches.py`, `django_strawberry_framework/utils/querysets.py` | File `_graphql_core_patches.py` | rejected |
| Executor-residual completion vs awaitable-refusal-and-disposal | `django_strawberry_framework/_graphql_core_patches.py` (rejection recorded in File artifact) | `django_strawberry_framework/_graphql_core_patches.py`, `django_strawberry_framework/utils/querysets.py` | File `_graphql_core_patches.py` | rejected |
| Executor-wrapper home vs `_strawberry_patches.py` | spec-050 rationale Decision 13 (rejection already recorded at the owner) | `django_strawberry_framework/_graphql_core_patches.py`, `django_strawberry_framework/_strawberry_patches.py` | File `_graphql_core_patches.py` | rejected |

## Judgment

Zero-edit result, proved: the target is a single-responsibility patch module
whose every rule-bearing member is assigned — lifecycle aspects and 2 refusal
messages to the two already-open families (`upstream-patch-lifecycle`,
`upstream-patch-refusal-wording`; counts LC 4 / W 11-over-4 confirmed from this
module's side with zero conflicts, four in-family divergences noted without
re-deciding them), three file-local rows with their single-ownership
challenges, three rejections with contract differences and triggers. No new
family named. No production edit owed, none made; no defects; no pending
execution. The upstream defect is still present at installed graphql-core 3.2.8,
so retirement is not in question this cycle.

## Implementation (Worker 1)

Zero tracked changes. HEAD at start `69a253690002fdd413704a7879528c3ded363020`
(= HEAD at finish; tripwire clean — recorded after the artifact write).
`ITEM_BASELINE=568c37809f473bab46a9dd475504846c7ccbf8dc` verified present
(`git cat-file -t` = `commit`). Item-scoped diff: `git diff <ITEM_BASELINE> --
docs/dry/dry-file-_graphql_core_patches.md
django_strawberry_framework/_graphql_core_patches.py` is empty (the target is
untouched — working blob `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5` equals HEAD
and the item baseline); this artifact itself is an untracked new file in this
worktree (new-file rule), overwriting the prior-cycle file of the same path;
the read-only probe scope
`docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/` (fresh,
non-colliding; the old `dry-file-_graphql_core_patches/` scope is earlier-cycle
and was only read) is gitignored scratch, not tracked changes. The 15
DRY-adopted ledger paths + all hunt dirt were never touched (condition b);
`management/commands/inspect_django_type` never imported (condition c). No
pytest run (read-only probe only, per authorization); no sharded/Postgres cells
(those stay `unverified`-as-inapplicable per `## Pending execution`). `uv run
ruff check` + `ruff format --check` both pass scoped to the probe scope. No
CHANGELOG, no commit, no plan edits.

## Independent verification (Worker 2)

Scope: `docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w2/` (fresh,
verified absent before use; holds `phase_a_expectations.md`,
`enumerate.py`, `probe_branch_fidelity.py`, plus a byte copy of this
artifact as Worker 1 left it, `w1_artifact_baseline.md`, sha256
`a5208e63...ac73`). Worker 1's scope
`docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/` was read and
re-run read-only, never written. HEAD at Worker 2 start
`69a253690002fdd413704a7879528c3ded363020`; HEAD at finish (recorded after
this append): `69a253690002fdd413704a7879528c3ded363020` — tripwire clean.
`ITEM_BASELINE=568c37809f473bab46a9dd475504846c7ccbf8dc` resolves
(`git cat-file -t` = `commit`). Target untouched: worktree blob
`1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5` equals HEAD equals the item
baseline; the only item-authored bytes are this untracked artifact and the
two gitignored probe scopes.

### Phase A (as recorded pre-read, verbatim)

The full text below is the blind record written to
`docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w2/phase_a_expectations.md`
BEFORE opening this artifact and before opening Worker 1's scope. Inputs:
the complete target, the three sibling patch modules, `conf.py`, `apps.py`,
`tests/test_graphql_core_patches.py`, `tests/test_apps.py`, the live oracle
`test_list_field_async_api.py::test_async_iterable_with_awaitable_children_completes_over_http`,
spec-050 Decision 13, GLOSSARY/TREE projections, installed graphql-core
3.2.8, and the two run-2 verified sibling artifacts (family shapes only).

--- begin verbatim Phase A ---

Run: 0.0.15 2026-09-21-2. HEAD at Phase A: `69a25369`.
Target blob: `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5` (clean in tree).
Instrument: `enumerate.py` in this scope — every statement in `ast.Module.body`.

Recorded BEFORE opening `docs/dry/dry-file-_graphql_core_patches.md` and before
opening Worker 1's scope `docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/`.

## Enumeration (my instrument: 17 nodes, 0–16)

| # | node | content | my home |
|---|---|---|---|
| 0 | Expr docstring | bug narrative, `"graphql_core"` key, retirement pointer at `tests/test_graphql_core_patches.py` | file-local prose (L-prose) |
| 1 | Import | `inspect` | — (no rule) |
| 2 | ImportFrom | `collections.abc::AsyncIterable` | — (no rule; used by the guard in node 12) |
| 3 | ImportFrom | `typing::Any` | — (no rule) |
| 4 | ImportFrom | `.conf::upstream_patches_enabled` | — (consumer edge; rule owned by File `conf.py`) |
| 5 | Try | `ExecutionContext` + `is_iterable` import / `ImportError -> None` ×2 | lifecycle family (import sentinel; 2-name shape = legitimate variation) |
| 6 | Assign | `_PATCH_OWNER_ATTRIBUTE` literal | lifecycle family (stamp identity) |
| 7 | Assign | `_PATCH_ORIGINAL_ATTRIBUTE` literal | lifecycle family (stamp identity) |
| 8 | Assign | `_PATCH_OWNER` per-module value | lifecycle family (stamp identity) |
| 9 | FunctionDef | `_captured_upstream_method(owner, name)` (incl. `None`-owner guard + `django_strawberry_framework.*` prefix tolerance) | lifecycle family (capture concept); prefix clause recorded as in-family divergence (already named by cross_web F1), not a new row |
| 10 | Assign | `_original_complete_list_value` import-time capture call | lifecycle family (capture) |
| 11 | FunctionDef | `_validate_upstream_shape` (presence tier + 6-arity tier, 2 raises) | lifecycle family (validation mechanism) + wording family (2 messages) |
| 12 | FunctionDef | `_patched_complete_list_value` (delegate + guard + nested `_await_residual` double-await) | file-local residual-await behavior (L-resid); delegation depth is a lifecycle parameter |
| 13 | Expr | `setattr` owner stamp | lifecycle family (marking) |
| 14 | Expr | `setattr` original stamp | lifecycle family (marking) |
| 15 | FunctionDef | `_patch_is_installed` (None-guard + single-identity probe) | lifecycle family (install-check concept) + file-local plain-kind spelling |
| 16 | FunctionDef | `apply` (gate -> validate -> installed-check -> install) | lifecycle family (4-step order) + gate consumer edge + file-local plain-kind install spelling |

Count check: 17 nodes, 13 rule-bearing (11, 15, 16 split by aspect), 4
rule-free imports (1–4). Nothing unassigned.

## Sites + roles (my trace)

- Definitions in-target: nodes 5–16 per the table above.
- Consumer edges: `apply()` gates on
  `conf.py::upstream_patches_enabled("graphql_core")`; `apps.py::ready()`
  calls `apply()` fourth of four; the wrapper composes upstream's
  `self.is_awaitable` predicate and upstream's `is_iterable` by name
  (upstream-owned, not package definitions).
- Consumers (package): `apps.py::ready` (dispatch);
  `tests/test_apps.py::_PATCHED_SLOTS` + `_all_patches_installed` (7-slot
  table incl. the `(ExecutionContext, "complete_list_value")` slot).
- Oracles: `tests/test_graphql_core_patches.py` (8 test functions: install
  at load + idempotence, self-heal, retirement sentinel, drift refusal,
  3-param missing-symbol refusal, independent gate, global disable,
  None-owner capture); `tests/test_apps.py` (dispatch + double-reload
  rows, parametrized over all four modules);
  `tests/base/test_conf.py` (gate vocabulary incl. `"graphql_core"`);
  live `test_async_iterable_with_awaitable_children_completes_over_http`
  (wire-observable residual completion; selects an async child on purpose).
- Upstream oracles: installed graphql-core 3.2.8
  `ExecutionContext.complete_list_value` (branch + signature),
  `graphql.pyutils.is_iterable` (excludes str/mapping — probe-verified).
- Projections: target docstring; spec-050 Decision 13 (durable contract:
  dependency-owned lifecycle, independent gate key, retirement sentinel);
  GLOSSARY ("defensive upstream patches", "kill switch", async-adapter
  entry naming the `graphql_core` key); TREE.md one-liner (generated);
  `conf.py::UPSTREAM_PATCH_DEPENDENCIES` comment ("independently owns
  async-iterable list completion"); `apps.py::ready` docstring (dispatch
  order); kanban `constants.py` path strings (generated inventory, no rule).

## Definition counts per posited change (my challenges)

- LC-C1 (stamp rename): the literal + capture read + two marking writes in
  each of the 4 patch modules. Count: **4**.
- LC-C2 (apply order, check-installed-before-validate): all 4 `apply()`
  bodies spell gate -> validate -> installed-check -> install. Count: **4**.
- LC-C3 (sentinel convention, `None` -> dedicated marker): the `None` reads
  in all 4 modules' captures/probes/validators (here: node 5 except arms,
  node 9 owner guard, node 11 presence tier, node 15 None-guard). Count: **4**.
- LC-C4 (capture tolerance change): all 4 capture functions spell
  replace-semantics today (here node 9 incl. the prefix clause). Count: **4**.
- W-C1 (hint reword): 11 raise sites / 4 module wordings (this module
  contributes node 11's 2 raises: presence + signature). Count: **11/4**.
- RES-C1 (residual depth): upstream nests a third awaitable level, or the
  residual shape changes. Forced move: node 12 only (nested
  `_await_residual` + guard). Siblings patch disjoint upstreams. Count: **1**.
- RES-C2 (guard widening/narrowing): the AsyncIterable branch condition
  changes. Forced move: node 12's first two conjuncts only — they must stay
  branch-faithful to upstream, so the package `is_async_only_iterable`
  spelling cannot substitute (see R1). Count: **1**.
- KIND-C1 (descriptor-kind reshape): graphql-core makes the member a
  property/classmethod. Forced move: only this module's plain-kind
  spellings (nodes 9/15/16). Siblings follow their own upstreams' kinds.
  Count: **1**.
- PROSE-C1 (retirement pointer reword): node 0 only. Count: **1**
  (projection, listed for completeness).

## Family assignments I would choose

- Lifecycle aspects (nodes 5–11, 13–16 mechanism/concept/order) → assign to
  already-open `upstream-patch-lifecycle`. No new family.
- Wording aspects (node 11's 2 raises) → assign to already-open
  `upstream-patch-refusal-wording`. No new family. Expected family totals
  after assignment: lifecycle 4 modules; wording 11 sites / 4 wordings
  (3+3+3+2), unchanged from the cross_web census.
- Residual-await delegation behavior (node 12: delegate, guard triple,
  `_await_residual` double-await) → file-local (count 1 per RES-C1/RES-C2).
- Plain-method capture/install/probe spelling (nodes 9/15/16 kind forms) →
  file-local kind adapter (count 1 per KIND-C1). Shared plain-kind text
  with strawberry is kind-parameter coincidence, not a shared rule: each
  follows its own upstream's kind.
- Capture prefix-tolerance clause → stays INSIDE the lifecycle capture
  assignment (one branch of the recovery condition, inseparable); the
  prefix-vs-exact divergence is recorded as in-family input for the family
  item, already named by cross_web F1. No separate row owed; a W1 file-local
  row for the clause would be a granularity delta, not an error.
- Docstring bug/retirement prose (node 0) → file-local prose (projection of
  Decision 13 + the sentinel oracle). The missing Surface-visibility section
  (present in the other three modules) is a prose gap with no behavioral
  contract behind it — not a defect (django item already noted it).

## Expected rejections with triggers

- R1 — Wrapper guard conjuncts vs package `is_async_only_iterable`
  (`utils/querysets.py::is_async_only_iterable`, "the one spelling").
  Shared form considered: one async-only predicate. Contract difference:
  the wrapper's `not is_iterable(result) and isinstance(result,
  AsyncIterable)` must stay branch-faithful to upstream's branch using
  upstream's own predicate (graphql's `is_iterable` excludes str/mapping;
  `collections.abc.Iterable` includes them — probe-verified, and the
  async-str shape takes the upstream branch while failing the package
  predicate, so substitution would drop residuals). Remainder: the
  `self.is_awaitable(res)` third conjunct has no package counterpart at
  all. Trigger: upstream re-spells its branch on a single importable
  predicate the package can compose by name, or the package stops
  mirroring the branch.
- R2 — `inspect.signature` arity pin (node 11) vs consumer-config
  validators (`routers.py::_require_factory_calling_convention`,
  `types/base.py::_validate_globalid_callable`). Already excluded on body
  strength by the django item; confirm from this side. Contract
  difference: upstream-shape pin (RuntimeError, fail-closed) vs consumer
  config validation (ConfigurationError paths, fail-open/bind stances).
  Trigger: a single package introspection policy covering both.
- Considered and NOT rejections (sweep exclusions, not rows):
  - `self.is_awaitable` shared token with `schema.py::DjangoMutationExecutionContext._execute_mutation_field_async`
    and every `inspect.isawaitable` site: all compose an upstream/std-lib
    predicate by name; none defines awaitability. Different
    responsibilities (transaction hold-open / refusal checks / residual
    repair). No shared rule, so no rejection row owed.
  - Nested `_await_residual` vs upstream's nested `await_completed` /
    `async_iterable_to_list`: upstream population, out of scope.
  - Two-`setattr` marking vs strawberry's `_mark_patch_replacement`
    helper: same lifecycle marking concept, spelling divergence for the
    family item — not a contract difference.
  - `try/except ImportError` 2-name shape vs siblings' 1/1/5-name shapes:
    legitimate lifecycle variation (per-module symbol set), not a second rule.
  - `resource_policy.py::bounded_rows_async` docstring async-iteration
    prose: row-bounding contract, disjoint from residual completion.

## Matrix discharge (my own)

1. Cross-flavor policy mirroring — SEARCHED, hit. The four patch modules
   are the mirror (lifecycle + wording assign to the two open families).
   `_PATCH_OWNER` census: exactly the 4 patch modules. Gate call sites:
   exactly the 4 `apply()` gates (+ the `conf.py` owner). Non-patch
   flavors share no rule (R1/R2 + exclusions above).
2. Sync/async twins — SEARCHED, no twin. Target defines no module-level
   `async def`; the single nested `_await_residual` has no package twin
   (upstream's nested closings are out of population; strawberry's
   multipart twins harden HTTP parsing, disjoint). The wrapper's
   sync-def/conditional-coroutine shape mirrors upstream's
   `AwaitableOrValue` contract — one site, no pair to drift.
3. Derived rather than repeated knowledge — SEARCHED, hit inside
   assignments. Install state answered once (node 15, identity compare);
   capture-vs-live split deliberate (validate pins the import-time
   capture; probe reads the live descriptor; probe-verified
   not-installed pre-apply in a bare process). Gate composed by name.
   Upstream branch re-derived with upstream's own predicate (R1: cannot
   use the package spelling). Test oracles re-derive install state by
   direct identity compare (oracles, listed not counted).
4. Inverse / round-trip pairs — SEARCHED, discharged. Lifecycle:
   install-once process-global; revert exists only as test scaffolding
   (restore saved descriptor by identity), no product uninstall half —
   inapplicable with reason (same as the cross_web/django items).
   Capture-read/install-write kind agreement (plain `__dict__.get` <->
   plain attribute install) recorded in the file-local kind row. No
   encode/decode or pack/unpack surface in-target.
5. Contracts restated in another medium — SEARCHED, classified. Gate
   semantics owned by `conf.py`, projected by this docstring, composed by
   name in `apply()`. Dependency-owned lifecycle + retirement sentinel
   owned by spec-050 Decision 13; docstring projects, sentinel oracle
   pins. Dispatch order owned by `apps.py::ready`, projected by GLOSSARY.
   One-module-per-dependency rule owned by spec-024 Decision 1 (File
   `apps.py`/`conf.py` items enumerate). Bug narrative projected in
   docstring + live-oracle docstring; behavior owned by node 12. Test
   `match=` substrings pin F2 fragments as oracles (listed, not counted).
6. Enforcement by omission — SEARCHED, no gap. Population with contract
   sources: (a) result shapes — sync Iterable (pass-through; upstream
   correct there; guard + upstream branch), AsyncIterable + non-awaitable
   res (pass-through; third conjunct), AsyncIterable + awaitable res
   (patched; docstring + Decision 13 + live oracle), non-iterable
   non-async (upstream GraphQLError, untouched); the guard is exhaustive
   over the branch by construction. (b) Execution colors — the guard keys
   on result shape, not transport, so sync and async paths share the one
   class-level install (no per-color member to omit). (c) Await depth —
   exactly 2 levels, matching upstream's `AwaitableOrValue` contract
   (single residual level); deeper nesting is not a value upstream can
   produce here. (d) Dispatch — all four appliers dispatched, this one
   fourth; `"graphql_core"` in `UPSTREAM_PATCH_DEPENDENCIES` (pinned by
   `tests/base/test_conf.py` oracles).

## Probes (mine, in this scope)

- `enumerate.py` → 17 nodes (0–16). Replay: `uv run python
  docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w2/enumerate.py`.
- `probe_branch_fidelity.py` → 10/10 PASS (capture identity + unstamped +
  not-installed pre-apply; 6-arity pinned names; `is_iterable` vs
  `Iterable` disagreement on str/mapping; 5-shape branch matrix incl. the
  async-str distinguisher). Replay: `uv run python
  docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w2/probe_branch_fidelity.py`.
- No pytest run (read-only probes only; permanent oracles run at the gate).

## Phase-B checklist (what I will verify against W1)

Enumeration member-by-member; LC/W counts from this side; wording census
(11 sites / 4 wordings, this module 2); R1/R2 presence-or-equivalent;
prefix-clause disposition; kind-spelling home; prose home; freshness
fingerprints re-hashed at HEAD; `## Pending execution` typing;
AGENTS.md prose rules on the artifact diff; Status decision.

--- end verbatim Phase A ---

### Reconciliation (every difference between Phase A and Worker 1)

Agreements first (explicitly reconciled, all hold): 17-node enumeration
with identical node boundaries; all rule-bearing homes (F1-assign,
F2-assign, three file-local rows); all definition counts (LC-C1..C4 = 4,
W-C1 = 11 sites / 4 wordings with this module contributing 2, every
file-local challenge count 1); both family assignments with no new family;
the R1 rejection (blind agreement — same pair, same contract difference,
same trigger shape); the prefix-clause disposition (inside the capture
assignment as in-family divergence, already named by cross_web F1); the
plain-kind home (file-local adapter, strawberry's twin as F1's parameter);
the prose home (file-local, missing Surface-visibility section not a
defect); all six matrix axes (searched/hit/discharged identically); zero
defects; empty `## Pending execution` with sharded/Postgres inapplicable by
construction. Deltas below; none moves a count, an assignment, a rejection
contract/trigger, or a gate.

- D1 — Enumeration row 16 (immaterial labeling; substance agreed). Worker 1's
  table homes node 16 as "F1-assign (4-step order) + gate consumer edge"
  while L2's Sites+roles claims "the kind-specific lines of nodes 9/15/16"
  and K-C1 counts nodes 9/15/16. My Phase A split row 16 three ways (the
  django item's row-23 precedent). The kind-install line
  (`ExecutionContext.complete_list_value = ...`) is assigned (L2 claims it,
  K-C1 counts it); only the table cell is terse. Adopted as-is; no action.
- D2 — My expected R2 (arity pin vs routers/types validators) has no Worker 1
  row (yielded; correctly omitted). The exclusion is family-boundary
  evidence already recorded by the verified django F1-assign and re-swept by
  the undispatched family item — Worker 1 uses exactly this reasoning for
  the R2 family side. A file item owes coverage + assignment of its own
  target's rules, not a re-derivation of every sibling-recorded exclusion.
  No action.
- D3 — Worker 1's R2 (residual completion vs awaitable-refusal-and-disposal):
  adopted (I had noted the near-miss without requiring a row). Verified
  against the owner: `utils/querysets.py::_dispose_sync_awaitable` closes
  coroutines / cancels futures and never awaits; the quoted rationale
  ("those must not recursively await an unbounded chain, so disposal is the
  only safe handling there too") is verbatim at `querysets.py:223-224`;
  refusal raises `SyncMisuseError` at the callers. Opposite actions (await
  vs close/cancel) at different layers (executor seam vs consumer
  boundary) — the rejection is well-formed with a trigger. Adopted.
- D4 — Worker 1's R3 (executor-wrapper home vs `_strawberry_patches.py`):
  adopted (not in my Phase A). Verified: spec-050 rationale Decision 13
  records *Decision* + *Why* + *Rejected: Keeping the executor wrapper in
  `_strawberry_patches.py`...* at the owner; the independent-gate oracle
  (`{"strawberry": False}` leaves this patch installing,
  `test_apply_uses_independent_dependency_gate`) and the GLOSSARY
  projection ("either workaround can be disabled or retired without
  changing the other") both confirmed by reading. Contract difference
  (separate gates/end dates; folding couples escape hatches) + trigger
  (shared lifecycle) are well-formed. Adopted.
- D5 — Evidence correction (immaterial; corrected record here, conclusion
  stands): the `## Defects` near-miss "any upstream restructure fails loud
  at `apply()`" overclaims. This module is a delegator (shape-only pin —
  Worker 1's own matrix axis 1 states it): presence/signature drift fails
  loud at `apply()`; a signature-preserving body restructure flows through
  and surfaces via the sentinel oracle (fix direction: the sentinel asserts
  a residual exists) or the live row (regression direction: an escaping
  residual becomes `errors`). Both oracles run at the gate. The depth
  analysis itself is verified: I read the installed tail —
  `get_completed_results` exists, the sync branch returns data or exactly
  one gathering coroutine that resolves to data, so depth ≤ 2 from this
  body; S4c re-ran green. The no-defect conclusion stands on S4c plus the
  oracle coverage; only the attribution clause is corrected, here.
- D6 — Evidence correction (immaterial; corrected record here): R1's
  Sites+roles consumer census lists `connection.py` alongside the
  `is_async_only_iterable` consumers, while R1's own Freshness correctly
  excludes `connection.py` on body strength. My package grep shows
  `connection.py` never calls the predicate; the true consumer set is
  `reject_async_iterable_in_sync_context` (`querysets.py:458`),
  `list_field.py` (3 call sites), and `resource_policy.py:1216` — matching
  the predicate owner's docstring. `connection.py` is excluded-on-body-strength
  only (Relay pagination async-shape dispatch + source guard at HEAD
  `connection.py:1050/1095/1575`, read at HEAD bytes — pagination
  contracts, not executor completion; the hunt diff holds zero
  `AsyncIterable` lines, so the exclusion stands on both byte sets). The
  rejection is unaffected (consumers listed, not counted).
- D7 — Evidence correction (immaterial; corrected record here): the
  "`AsyncIterable` in production: 6 files" sentence lists 7 names. The
  count is right — my census confirms exactly 6 literal holders (this
  module, `querysets.py`, `connection.py`, `types/resolvers.py`,
  `resource_policy.py`, `execution_mode.py`); `list_field.py` carries no
  literal (predicate consumer via import). Read as "6 literal holders plus
  `list_field.py` consumers". Census stands.
- D8 — Evidence correction (immaterial; corrected record here): the
  Challenges Experiment prose claims S6 asserts `is_iterable` /
  `_await_residual` single-sited, but the probe code asserts neither (read
  the probe). The underlying facts are true — my own greps confirm both
  single-sited here. Corrected record here; census stands.
- D9 — Worker 1-only additions, all adopted: divergence (c) (pragma-comment
  wording — confirmed from my own reads of all four modules: 3× "exercised
  via monkeypatch in tests", here "exercised through patched imports in
  tests."); the `def apply(` 6-file sweep with `filters/sets.py` +
  `optimizer/plans.py` body-strength exclusions (re-verified below at
  current bytes); the axis-4 retirement-signal pair; G-C1 (gate key owned
  by `conf.py` — consistent with my consumer-edge treatment).
- D10 — Matrix complement (no gap): my axis-6 color/depth/dispatch partition
  points are covered by Worker 1's axis 2 (one seam), `## Defects` + S4c
  (depth), and F1-assign consumers + `test_apps.py` oracles (dispatch).
  Worker 1's S4a/b/c partition re-ran green against the real callables.
  Both records kept; they are complementary, not conflicting.
- D11 — Freshness: all 24 recorded HEAD blobs re-hashed MATCH (table
  below). Worktree states: 23/24 unchanged; `filters/sets.py` worktree
  moved under the running hunt (`4a40e51b...` → `61e1b2c9...`; HEAD
  `4ab65a26...` unchanged). Re-verified at current bytes: the current
  diff touches no `def` line (two hunks at 1459/2357, both inside class
  bodies) and S6's `def apply(` 6-file census re-ran green — the
  exclusion stands; new worktree blob recorded here. No finding stale:
  every claim rests on HEAD bytes or on worktree bytes re-verified here.

| Input | Worker 1 recorded | Worker 2 re-hash | State |
|---|---|---|---|
| target | `1cd579fb…` CLEAN | same | MATCH |
| `_cross_web_patches.py` | `6b3a7c35…` CLEAN | same | MATCH |
| `_django_patches.py` | `ba98f585…` CLEAN | same | MATCH |
| `_strawberry_patches.py` | `f77df349…` CLEAN | same | MATCH |
| `conf.py` | `c6ad46aa…` CLEAN | same | MATCH |
| `apps.py` | `8ae1a3a3b…` CLEAN | same | MATCH |
| `tests/test_graphql_core_patches.py` | `53dca517…` CLEAN | same | MATCH |
| `tests/test_apps.py` | `5ca8b62c…` CLEAN | same | MATCH |
| `tests/base/test_conf.py` | `f35c7074…` CLEAN | same | MATCH |
| `docs/GLOSSARY.md` | `bc51debc…` CLEAN | same | MATCH |
| installed graphql-core `execute.py` | `869f59f3…` | same | MATCH |
| `filters/sets.py` | HEAD `4ab65a26…` / work `4a40e51b…` | HEAD same / work `61e1b2c9…` | HEAD MATCH, work re-verified |
| `optimizer/plans.py` | `cce98531…` CLEAN | same | MATCH |
| `test_list_field_async_api.py` | `49e423ea…` CLEAN | same | MATCH |
| `docs/TREE.md` | `c0b0b909…` CLEAN | same | MATCH |
| `CHANGELOG.md` | `d4e10355…` CLEAN | same | MATCH |
| `utils/querysets.py` | `96618fba…` CLEAN | same | MATCH |
| `connection.py` | HEAD `93e998f2…` / work `3c4d5dcb…` | same / same | MATCH |
| `list_field.py` | HEAD `ce682d5f…` / work `d6af6164…` | same / same | MATCH |
| `resource_policy.py` | `647133d2…` CLEAN | same | MATCH |
| `types/resolvers.py` | HEAD `f3341e6a…` / work `5f4cce2b…` | same / same | MATCH |
| `utils/execution_mode.py` | `9805cdaf…` CLEAN | same | MATCH |
| `schema.py` | `c2e1b748…` CLEAN | same | MATCH |
| spec-050 rationale | `8b88dc9d…` CLEAN | same | MATCH |

### Checks Worker 2 ran for this verdict

- Enumeration member-by-member: my own instrument agrees 17/17 with
  identical node boundaries; every rule-bearing home agreed (D1 notes the
  one terse cell).
- Worker 1's probe re-run read-only at current bytes: ALL OK (S1 17
  members; S2 capture identity + 6-param shape; S3 bare recursion; S4a/b/c
  three-way partition against the real captured/patched callables with a
  stub executor self — the defect-bearing bodies are the real ones, the
  stub stands in only for the sibling `self` methods, which is the
  unavoidable unit seam; S5 idempotent install + self-heal; S6 117-file
  census, 4 patch modules, 11 refusals / 12 raises).
- My own probes (re-derivation, not trust): `enumerate.py` 17 nodes;
  `probe_branch_fidelity.py` 10/10 PASS (capture/arity/predicate facts +
  5-shape branch matrix with the async-str distinguisher that
  execution-verifies R1's separation where Worker 1's R1 proof is
  static-reviewed).
- Upstream bytes read directly: async branch + `get_completed_results`
  tail (depth ≤ 2 verified); `is_iterable` excludes str/mapping
  (verified behaviorally); installed release graphql-core 3.2.8.
- Rejections verified against owners: R1 predicate + QuerySet carve-out
  read, distinguisher executed; R2 owner body + verbatim rationale read;
  R3 durable home + gate oracle + GLOSSARY projection read.
- `## Pending execution` typing: empty, correctly — every probe-backed
  conclusion is `execution-verified` with replay commands; sharded/PG
  inapplicable-by-construction judged SOUND (executor-completion path
  reaches no database, alias, or dialect decision; probes open no
  connection; the one DB-touching oracle runs at the gate in default
  mode).
- AGENTS.md prose rules on the item diff: no process provenance (no
  first-person narrative; "Worker 1" only in the mandated section
  header); `path::Symbol` citations throughout; zero inline markdown
  links (no LINK DEFINITIONS block owed); raw line refs permitted in
  `dry-*` scratchpads; zero-edit so no test-tier question arises.
- Lint: `uv run ruff check` + `uv run ruff format --check` both pass
  scoped to my scope dir (two `.py` probes); the item adds no tracked
  `.py` (both probe scopes gitignored).
- Item-scoped diff: `git diff 568c3780 -- <target>` empty; artifact is
  untracked-new (this append + the `Status:` swap are the only Worker 2
  bytes — verified by diff against `w1_artifact_baseline.md` in my
  scope); no ledger, hunt-owned, or plan path touched;
  `management/commands/inspect_django_type` never imported; no pytest
  run (read-only probes only, per authorization).
- Defects: none found by Worker 1; none found by Worker 2. All nine
  near-miss rulings re-checked (prefix divergence, prose gaps, conjunct
  order, depth, reload/sentinel/gate oracle coverage, upstream still
  broken at 3.2.8 via re-run S3+S4c). No `(Worker 2)` entries appended
  — there is nothing to home.

### Verdict + handoff to Worker 0

`Status: verified` (plain — no `proof:` entry, no pending execution). Zero
production edits, zero `## Owned changes` rows. No `## Families` item owed
(both assignments reuse already-open families). Transcribe the six index
rows exactly as Worker 1 proposed (3 file-local: residual-awaitable list
completion; plain-method capture/install/probe spelling; module status
prose — 3 rejected: guard predicate vs `is_async_only_iterable`;
residual completion vs awaitable-refusal-and-disposal; wrapper home vs
`_strawberry_patches.py`). Scratch custody: retain both
`dry-file-_graphql_core_patches-r2-*` scopes (Worker 1's probe re-ran
green; Worker 2's scope carries the re-derived evidence + the blind
Phase-A record + the pre-append baseline copy).

## Iterations

### Adjudication-1 (Worker 1, run 0.0.15 2026-09-22-4) — scoped re-review over 9 stale inputs

No production edits: a file-item adjudication owes none, like the file item
itself. Scope only: 7 old-range inputs (`69a25369..24e6b4d3`: GLOSSARY,
querysets, connection, list_field, resource_policy, schema, spec-050
rationale) + 2 new-range inputs (`24e6b4d3..5ee86193`: filters/sets, TREE).
Every other fingerprinted input is byte-identical at the new HEAD and stands
by input identity (table below).

Provenance: HEAD at start `5ee8619330e7e236b61060a1ec9cb9e62b7061aa`
(= dispatch HEAD; tripwire re-checked after this append).
`ITEM_BASELINE=22fb25e0585a31e6e898335a96319836e432cb42` resolves
(`git cat-file -t` = `commit`). The artifact is UNTRACKED: pre-edit
`79641 B / sha256 01f557d4627c7273be4ed663395983a11b3d0590f8503fe95aaf4290df7b9416`
(recorded before the Status swap and re-verified immediately before this
append; Worker 2 reconstructs by truncating to that size and hashing).
This section plus the Status swap are the only bytes. Fresh scratch scope
`docs/dry/temp-tests/dry-adjud1-graphqlcore-w1/` (verified absent before
use; holds `census.py` + byte-comparison spans). No pytest run (no test
authorization conveyed); `management/commands/inspect_django_type` never
imported; hunt-owned paths untouched.

#### Full-table blind re-hash (24/24, independent `git rev-parse HEAD:<path>`)

Old pins exact in all 24 rows (recorded prefix == `69a25369` blob in every
row, installed file included): no containment finding. 15 MATCH + exactly
the 9 tabled STALE (7 old + 2 new), zero unexpected.

| Input | Recorded | HEAD now | State |
|---|---|---|---|
| target | `1cd579fb…` | same | MATCH, clean |
| `_cross_web_patches.py` | `6b3a7c35…` | same | MATCH |
| `_django_patches.py` | `ba98f585…` | same | MATCH |
| `_strawberry_patches.py` | `f77df349…` | same | MATCH |
| `conf.py` | `c6ad46aa…` | same | MATCH |
| `apps.py` | `8ae1a3a3…` | same | MATCH |
| `tests/test_graphql_core_patches.py` | `53dca517…` | same | MATCH |
| `tests/test_apps.py` | `5ca8b62c…` | same | MATCH |
| `tests/base/test_conf.py` | `f35c7074…` | same | MATCH |
| `docs/GLOSSARY.md` | `bc51debc…` | `d3ef357c26ede6a5bd21d4290b394ade4eb987b4` | STALE (old) |
| installed graphql-core `execute.py` | `869f59f3…` | same (3.2.8) | MATCH |
| `filters/sets.py` | HEAD `4ab65a26…` | `722e0c773dcb1fb806d1fde4837bff4d6c988fba` / work `d56c21f0…` | STALE (new) + DIRTY |
| `optimizer/plans.py` | `cce98531…` | same | MATCH |
| `test_list_field_async_api.py` | `49e423ea…` | same | MATCH |
| `docs/TREE.md` | `c0b0b909…` | `254239899d23abf0fb87d5a67806089465e14efc` | STALE (new) |
| `CHANGELOG.md` | `d4e10355…` | same | MATCH |
| `utils/querysets.py` | `96618fba…` | `b68be0e337d178fc703ca1ac2ff4144c1fd766a5` / work `799139be…` | STALE (old) + DIRTY |
| `connection.py` | HEAD `93e998f2…` | `4894f90fb2963a44d25b0eabc649c67d04afa587` / work `9c5b8724…` | STALE (old) + DIRTY |
| `list_field.py` | HEAD `ce682d5f…` | `21380eb72364caef0da05ca3ee3f26c0134e3904` / work `616ca7f6…` | STALE (old) + DIRTY |
| `resource_policy.py` | `647133d2…` | `4b69e974decbd45916bd55f444f4b5f86724a07a` | STALE (old), clean |
| `types/resolvers.py` | HEAD `f3341e6a…` | same / work `5f4cce2b…` | MATCH + DIRTY (work blob == run-2 record) |
| `utils/execution_mode.py` | `9805cdaf…` | same | MATCH |
| `schema.py` | `c2e1b748…` | `19f90bf55289d1ab31d5dc09236335e67037adc2` | STALE (old), clean |
| spec-050 rationale | `8b88dc9d…` | `15806f31c47f38a1567f7c551674ec37e9a52ab9` | STALE (old) |

All verdict claims rest on HEAD bytes. Five inputs are dirty in the
worktree (four briefed + querysets, whose 2-line `__name__` →
`_safe_class_name` sidecar hardening is the same concurrent bytes the
querysets adjudication-3 outcome already recorded as out-of-scope);
every worktree-dependent claim is re-verified at current bytes below.

#### Causing commits (mechanical attribution, both ranges)

Old range (`69a25369..24e6b4d3`): exactly 5 of the 11 commits touch the 7
inputs — `9350eb8d` (resource_policy 5 hunks, schema 3 hunks, GLOSSARY 4
hunks), `fee87ac4` (connection + list_field + querysets seal move),
`44712901` (querysets slice-policy hunks, GLOSSARY prefetch-seal hunk),
`ec0d21de` (rationale Decision 20 rewrite part 1 + link def),
`c87f4f98` (connection + querysets FilterSet seal, rationale rename +
Decision 20 part 2). The other 6 (`357e5487`, `1f68871a`, `fa6d48f8`,
`9fb725c8`, `3c53842f`, `24e6b4d3`) touch none of the 7 (empty
per-commit stat, verified). New range (`24e6b4d3..5ee86193`):
`29ddc0a8` owns the filters/sets 2-line swap alone; `174a109c` owns the
two TREE conftest rows; `3ad0dfd6` owns the TREE shapes row; `5ee86193`
touches neither.

#### F1-assign — CONFIRM (hashes refreshed, divergences re-swept)

GLOSSARY stale: the 5 hunks (numstat 7+/7-, all 1-for-1 swaps, file stays
2230 lines) reword the DEFAULT-policy exports, the ErrorPolicy exact-type
sentence, the masker build, the production-policy entry (`9350eb8d`) and
the prefetch-seal entry (`44712901`). Every patch-related span is
byte-identical with no re-pin: entry `2089-2102` (md5 `fc764053…` both),
lines `313` / `542` / `2093` / `2097` (md5-identical each). The lifecycle
projections F1 cites are untouched. filters/sets stale: exactly the 2
docstring lines (`29ddc0a8`), inside `_apply_common_finalize` (`:3360`)
and `apply_sync` (`:~3399`) docstrings — zero executable change, `def`
lines `:3384/:3437/:3506` unshifted, gate/install vocabulary still 0
hits, `FilterSet.apply` still a thin filter dispatcher (re-read
`:3506-3532` at HEAD). optimizer/plans MATCH: `apply(self, queryset)`
`:288` re-read (only/select/prefetch application); the `def
apply_window_pagination(` sibling at `:947` never matched the `def apply(`
needle. Divergences re-swept at HEAD: (a) prefix arm still unique here
(P6); (b) strawberry twin still docstringed (`:403`) vs here bare —
CONFIRMED; (c) pragma wording still 3× monkeypatch + 1× patched-imports;
(d) `Surface visibility` section still in 3/4, absent here. Refreshed:
GLOSSARY `d3ef357c…`, filters/sets `722e0c77…`.

#### F2-assign — CONFIRM (hashes refreshed)

Same production inputs as F1 (all MATCH except the two above). The
`match=` oracles MATCH; the kill-switch projection (GLOSSARY `:2097`)
byte-identical per F1. Wording census re-derived at HEAD: 11 refusal
lines over the 4 modules (`3+3+2+3`, this module 2) / 12 raises —
identical. The hint's end-to-end truth still oracle-pinned (oracle file
MATCH). Refreshed: same two hashes as F1.

#### L1 — CONFIRM (no stale input; behavior re-executed this pass)

Freshness is target + oracle + live row + installed upstream: all four
MATCH. Additionally the S4a/b/c partition + S3 were re-executed against
the real callables in this pass (W1 probe replay, ALL OK below), so the
`execution-verified` half does not rest on carried evidence.

#### L2 — CONFIRM (no stale input; kind census re-derived)

Freshness is target + three siblings + `test_apps.py`: all MATCH.
Capture-def kind census re-derived at HEAD: `body_getter` ×1 (cross_web,
property) / `descriptor` ×1 (django, classmethod) / `method` ×2
(strawberry + here, plain) — identical, K-C1 count 1 stands.

#### L3 — CONFIRM (hashes refreshed, TREE rows re-pinned)

GLOSSARY projections byte-identical per F1 (no re-pin). TREE stale: the
only new-range change is 3 added rows (conftest ×2 at `~543/~789`,
shapes at `~680`); TREE was unchanged in the old range (empty diff).
Module one-liners `:199/:329` byte-identical and unshifted (md5
`34b8cd31…`); test rows content-identical (`:482` unshifted,
`:721→:723` shifted +2 by the insertions above — the artifact carried no
TREE line pin, so this is a recorded re-pin, not a correction).
CHANGELOG MATCH. Refreshed: GLOSSARY `d3ef357c…`, TREE `25423989…`.

#### R1 — CONFIRM (hashes refreshed, all bodies re-read, consumers re-pinned)

Predicate body `is_async_only_iterable` (`:375-390`) byte-identical:
`isinstance(value, AsyncIterable) and not isinstance(value, Iterable)`
with the QuerySet carve-out and the 3-consumer census intact in the
docstring (same lines, no re-pin). `reject_async_iterable_in_sync_context`
(`:431-465`, incl. the `:458` call) byte-identical. All 10 querysets
hunks sit at lines ≥2404 (7 prose/comment, 1 constants incl. new
`_LIST_RELATION_CHILD_POLICY` + `_ORDERSET→_SIDECAR` rename with
identical constructor args, 1 one-line constant swap, 1 new-functions
hunk); single definitions hold (`def is_async_only_iterable` ×1,
whole-file `AsyncIterable` count 6 both heads, zero predicate lines in
the new-code span). The mapping distinguisher (`__aiter__` + `__iter__`
separating upstream-`is_iterable` from the package predicate) is
unaffected: neither primitive moved. Consumers re-pinned from HEAD
bytes: list_field `:103→:100` import, calls `:1333/:1337/:1829` →
`:1332/:1336/:1751` (same `if is_async_only_iterable(source):` spelling;
bodies re-read — rejection-cleanup guards + the sync-wrapper refusal,
pure consumers; the `fee87ac4` −78 deletion spans old `:1339-1422` and
contains no predicate call); resource_policy `:1216→:1240` inside
`_windowed_rows_async` (`:1193→:1217`, +24 from the two additive hunks),
body re-read (`if not is_async_only_iterable(result): return
_windowed_rows(…)`); the 5 `9350eb8d` hunks are all above `:900` and
policy-template-only. connection still never calls the predicate (0 hits
both heads); the 3 exclusion bodies byte-identical
(`:1050/:1095/:1575` → `:1057/:1102/:1582`, +7 from the import hunk —
Relay count-only async closure, full async resolve closure,
`_guard_non_queryset_iterable`; pagination contracts, re-read); the 5
connection hunks (seal imports, `_sidecar_steps` 3-tuples, new
`_sidecar_visibility_policy`, both pipeline bodies) are disjoint from
all three. schema await body `:318-365` byte-identical (async mutation
transaction hold-open, `self.is_awaitable` composed by name); the 3
rename hunks are 1-for-1 swaps elsewhere. types/resolvers prose-only
(`:422`, zero predicate hits, both byte sets — worktree blob
`5f4cce2b…` equals the run-2 record, dirt unmoved);
utils/execution_mode prose-only (`:5`). Refreshed: querysets
`b68be0e3…`, connection `4894f90f…`, list_field `21380eb7…`,
resource_policy `4b69e974…`, schema `19f90bf5…`.

#### R2 — CONFIRM (hash refreshed, disposal body re-read)

`_dispose_sync_awaitable` (`:217-232`) byte-identical: close coroutines /
cancel futures, never await, with the verbatim rationale at `:223-224`
intact (same lines, no re-pin). `SyncMisuseError` `:119` unmoved. Single
`def _dispose_sync_awaitable` ×1 at HEAD. The new `_apply_sidecar_*`
functions are new *consumers* of the owner (call
`_dispose_sync_awaitable` by name before raising at a sync boundary) —
consistent with the family's direction, not a second definition; the
rejection's contract difference (executor-internal completion vs
consumer-boundary refusal, opposite actions) is untouched. Refreshed:
querysets `b68be0e3…`.

#### R3 — CONFIRM (hash refreshed, Decision 13 byte-identity proven)

Decision 13 span (`:445-460`, heading map identical both heads through
Decision 20) byte-identical, md5 `297b6c54…` both:

> `*Decision:* Put the ExecutionContext.complete_list_value delegator in
> its own _graphql_core_patches.py module and gate it with the canonical
> graphql_core dependency key. … *Rejected:* Keeping the executor wrapper
> in _strawberry_patches.py because graphql-core is a transitive
> Strawberry dependency. …`

The 3 rationale hunks are all outside the span: Decision 8 probe rename
(`:366`, `c87f4f98`), the Decision 20 sidecar-seam rewrite (`:621`,
`ec0d21de` OrderSet-half + `c87f4f98` FilterSet-discharge — the rewritten
Decision 20 the brief names), and the link-def addition (`:736`,
`ec0d21de`). Gate oracle (MATCH) + GLOSSARY `either workaround` projection
(`:2097`, byte-identical per F1) re-checked. Refreshed: rationale
`15806f31…`, GLOSSARY `d3ef357c…`.

#### Defects — none (stand)

No defects were recorded. Near-miss rulings re-checked: upstream still
broken at installed 3.2.8 (S3 + S4c-defect re-ran green this pass);
reload/sentinel/gate oracle coverage rests on MATCH inputs; the D5
attribution correction (delegator shape-only pin) is unaffected — target
MATCH.

#### Census re-derivation (all sweeps, HEAD bytes, populations printed)

New probe (fresh scope, read-only, HEAD bytes via git plumbing +
worktree cross-checks):

```shell
uv run python docs/dry/temp-tests/dry-adjud1-graphqlcore-w1/census.py
```

Output `ALL OK`: production set re-derived 117 files (P0); owner-attr 4
(P1); gate call + hint + `complete_list_value` + `is_iterable` +
`_await_residual` single-sited here (P2/P3/P4/P13); capture-method defs 2
(P5); prefix arm unique (P6); refusals 11 over 4 files `3+3+2+3` / raises
12 (P7/P8); gate call sites exactly 4 (P9); root patch-free + apps 4
appliers (P10/P11); `def apply(` exactly the 6 files (P12);
AsyncIterable exactly the 6 holders + list_field literal-free (P14);
predicate def single / connection zero / list_field 3 / resource_policy
1 / resolvers prose-only (P15); capture kinds 1/1/2 (P16); pragma 3+1 +
Surface visibility 3-present-here-absent (P17); lifecycle vocab 4
production + 7 test consumers (P18/T2: `test_transport_api`,
`test_apps`, 4 patch suites, `test_views`). Test-tree population (300
`.py` at HEAD incl. both new files): `def apply(` 0 holders (T3),
AsyncIterable 6 holders, all oracle/consumer files (T4) — neither new
file holds lifecycle vocab (T2). Worktree cross-checks agree: `def
apply(` 6, AsyncIterable 6, connection zero, single predicate/disposal
defs (W1a–e). Rewritten suites (`test_walker`,
`test_relay_id_projection`, `test_connection_pagination_api`,
`test_kanban_api`) are cited 0 times in this artifact — no carried pin
falls in them.

#### W1 probe replay (read-only, current bytes)

```shell
uv run python docs/dry/temp-tests/dry-file-_graphql_core_patches-r2-w1/probe_graphql_core_patches.py
```

Output `ALL OK`: S1 17 members; S2 capture identity + 6-param shape; S3
bare recursion at graphql-core 3.2.8; S4a/b/c partition against the real
callables; S5 idempotent install + self-heal; S6 117 files / 4 patch
modules / 11 refusals / 12 raises / single-sited gate+hint. (This probe
carries no HEAD pin — its pinned counts/blobs all re-verified green at
`5ee86193`; the dispatch's tripwire warning does not materialize here.
S6 reads worktree bytes; the P-series above re-derives the same
populations at HEAD bytes.)

#### Mention-checks (corrections verified, not scope)

Rationale unchanged in the new range: `git diff 24e6b4d3..5ee86193`
empty, `15806f31…` both heads. The non-rationale spec-050 doc,
build-050 DONE record, fakeshop README, and test_query README are cited
in 0 Freshness rows (8 Freshness bullets swept; `rationale` cites are
the R3 input only).

#### Worktree states (all hunt-concurrent, never this item's)

connection `9c5b8724…` (64+/1-, 0 AsyncIterable lines), list_field
`616ca7f6…` (+8, 0 predicate lines; calls at `:1340/:1344/:1759`),
types/resolvers `5f4cce2b…` (== run-2 record, prose `:422` intact),
filters/sets `d56c21f0…` (+31/−2, 0 def-line touches, 0 gate lines;
`def apply(` at `:3535`), querysets `799139be…` (2-line safe-class-name
hardening at `:3114/:3149`, 0 R1/R2 lines). Target, schema,
resource_policy, and all other fingerprinted inputs clean. Exclusions
and censuses stand on both byte sets per the re-verifications above.

#### Judgment

All eight findings CONFIRM with refreshed hashes; no REVISE owed — every
stale input's landed diff is disjoint from the cited spans (byte-identical
bodies/prose, content-identical TREE rows, re-pinned consumer lines), and
every sweep re-derives the run-2 populations exactly. No new family, no
defect, no pending execution. Ready for Worker 2 two-phase verification
(Phase A withholds this section and `dry-adjud1-graphqlcore-w1/`).

### Worker-2 verdict (run 7) — fresh verification at HEAD `0c0537e2`

Fresh Worker 2 (both run-3/run-4 W2 passes never returned; nothing
inherited). Verified the run-4 submission fresh at HEAD bytes. HEAD at
start `0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62` (= HEAD at finish;
tripwire clean). Target HEAD blob
`1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5` == the submission's pinned
blob: the submission stands on current target bytes. Worktree target
blob `90ac4f3c` (129 lines; 5 hunks, 6+/4-) attributed hunk-by-hunk
below — all concurrent/external; `## Owned changes` carries zero rows
naming this file. Read-only probes only; scratch `/tmp/w2r7/`
(`probe_head.py`, `head/` extraction tree). No pytest run (read-only
probes only, per dispatch); no plan edits; no other tracked file
touched.

#### Independent trace (re-derived, not trusted)

- Enumeration: own `ast` instrument over HEAD target bytes → 17 nodes
  with kind list `Expr, Import, ImportFrom x3, Try, Assign x3,
  FunctionDef, Assign, FunctionDef x2, Expr x2, FunctionDef x2` —
  identical boundaries to the submission. Homes agree: nodes 5–16
  rule-bearing (nodes 9/11/15 split by aspect; node 16's kind-install
  line claimed by L2 per K-C1 — the run-2 D1 terse-cell point, substance
  agreed), node 4 a consumer edge into `conf.py`, nodes 1–3 rule-free.
  Zero top-level `async def`; one nested `_await_residual`.
- Consumer edges: `apply()` gates on
  `conf.py::upstream_patches_enabled("graphql_core")`;
  `apps.py::ready` dispatches this `apply()` last of four;
  the guard composes upstream `graphql.pyutils.is_iterable` and the
  executor's own `is_awaitable` by name.
- Upstream contract: installed graphql-core 3.2.8,
  `execution/execute.py` blob
  `869f59f3f5662fc55e3dbb48023e6879dab40a8a` (== run-4 pin). The
  `async_iterable_to_list` body holds the bare
  `return self.complete_list_value(` with no `await`; upstream checks
  `not is_iterable` before `isinstance(result, AsyncIterable)` (same
  order as the HEAD guard). `is_iterable` is pure `isinstance` checks.
- Mechanism sweeps re-derived at HEAD via `git grep` (production
  population 117 files): owner-attr literal exactly the 4 patch
  modules; gate call sites exactly the 4 `apply()` gates; the
  `{"graphql_core": False}` hint on 2 adjacent lines here only;
  `complete_list_value` / `is_iterable` / `_await_residual`
  single-sited here; `def _captured_upstream_method(` in exactly 2
  modules; the `startswith("django_strawberry_framework.")` arm unique
  here; refusal grammar 3+3+2+3 = 11 over the 4 modules / 12 raises
  (django's hint-less teardown invariant is the 12th); `def apply(`
  in exactly 6 files (4 appliers + `filters/sets.py::FilterSet.apply`
  + `optimizer/plans.py::apply`, both re-read — disjoint contracts);
  `AsyncIterable` in exactly 6 production files
  (`_graphql_core_patches`, `querysets`, `connection`,
  `types/resolvers`, `resource_policy`, `execution_mode`;
  `list_field.py` literal-free consumer); `is_async_only_iterable`
  callers `list_field.py` x3 (`:1332/:1336/:1751`) +
  `resource_policy.py` x1 (`:1240`) + the `querysets.py` self-use
  (`:460`); `connection.py` zero calls; root `__init__.py`
  patch-free; `apps.py` dispatches exactly 4 appliers in listed order.
- Matrix re-derived: axis 1 SEARCHED hit (4-module mirror → F1/F2
  assigns); axis 2 SEARCHED no twin; axis 3 SEARCHED hit inside
  assigns; axis 4 SEARCHED discharged (install-once, no product
  uninstall half; sentinel pair intact); axis 5 SEARCHED classified
  (gate owned by `conf.py`, dispatch by `apps.py`, lifecycle by
  spec-050 Decision 13, bug narrative file-local); axis 6 SEARCHED no
  gap (three-way partition probe-executed, T4a/b/c).
- Challenges re-derived: LC-C1..C4 = 4/4/4/4; W-C1 = 11 sites / 4
  wordings (this module 2); R-C1/C2/C3, K-C1, G-C1 (owner `conf.py`),
  P-C1 = 1; R-C4/C5/C6 = 0, refused with contract differences + triggers.
- Behavior executed (`uv run python /tmp/w2r7/probe_head.py`, ALL OK,
  29 checks, HEAD module loaded pristine under a stub gate): capture
  IS the live unmarked method with the exact 6-param
  all-`POSITIONAL_OR_KEYWORD` shape; sync input passes through
  unwrapped and value-identical; sync-children wrap entered and
  neutral; unpatched async-iterable + awaitable children leaves the
  genuine `get_completed_results` residual after one await, patched
  resolves to data; gate-off no-op, install, idempotence, probe
  false-after-revert, self-heal, restore; guard-order equivalence
  over a 12-shape battery (T6); the R1 mapping distinguisher executed
  (mirror wraps, package predicate declines — T7).
- Rejections verified against owners: R1 bodies read (QuerySet
  carve-out + 3-consumer census intact in the predicate docstring) and
  the separation executed (T7); R2 disposal body re-read at HEAD
  (`:219-232`, close/cancel, never await, rationale verbatim at
  `:223-224`) with `SyncMisuseError` at the callers; R3 Decision 13
  span intact at HEAD (`:452-467`, Decision + Why + Rejected
  verbatim) with the independent-gate oracle and the GLOSSARY
  "either workaround" projection re-checked.
- Oracles re-checked: `tests/test_graphql_core_patches.py` (8 test
  functions, 1 parametrized x3 → 10 rows; sentinel drives the
  CAPTURED method); live HTTP row (discriminating docstring intact,
  never names the patch module); `tests/test_apps.py`
  (`_PATCHED_SLOTS` incl. the `complete_list_value` slot, dispatch +
  double-reload rows); `tests/base/test_conf.py` (gate vocabulary).
- Defects: none found. Near-miss rulings re-checked (prefix
  divergence unreachable — members disjoint; prose gaps contract-free;
  depth ≤ 2 from the pinned body; reload/sentinel/gate oracle
  coverage intact; upstream still broken at 3.2.8). The run-2 D5
  attribution correction (delegator shape-only pin; body restructures
  surface via sentinel/live oracles, not `apply()`) is adopted and
  unaffected — target MATCH. No `(Worker-2)` entries: nothing to home.

#### Worktree hunk attribution (all 5, by content; concurrent work)

1. `from .utils import truth` import — truth-migration wave (sibling
   patch modules carry the identical import in their worktree diffs;
   `utils/truth.py` is UNTRACKED, absent from HEAD). External.
2. `_captured_upstream_method`: `owner.__dict__.get` →
   `truth.class_dict(owner).get` — same wave. Equivalent on the whole
   reachable population: capture's only call site passes the
   module-global `ExecutionContext`-or-`None`; executed
   `class_dict(ExecutionContext).get(...) is
   ExecutionContext.__dict__[...]` → True, and `class_dict(None)` is
   the empty mapping (None is pre-guarded anyway). Diverges only for
   a non-class truthy owner, which no caller passes.
3. `_patch_is_installed`: `ExecutionContext.__dict__.get` →
   `truth.class_dict(ExecutionContext).get` (+ line wrap) — same wave,
   same equivalence (operand is `ExecutionContext`-or-`None`).
4. Pragma comment reword ("exercised through patched imports in
   tests." → "exercised via monkeypatch in tests") — aligns this
   module with the other three (3× monkeypatch at HEAD); prose only,
   resolves F1-assign divergence (c) in the worktree.
5. Guard reorder (`not is_iterable` first → `isinstance` first) —
   behavior-preserving: both conjuncts are pure total predicates
   (`is_iterable` is `isinstance`-only per installed source;
   `isinstance` never raises), so short-circuit order is
   unobservable (DRY principle 8); executed equivalent over a
   12-shape battery incl. str/bytes/mapping/set/async-gen/dual-protocol
   shapes (T6). Cosmetic note: the worktree order no longer mirrors
   upstream's branch order (`not is_iterable` first); the conjunction
   is order-insensitive so no defect. External concurrent edit.

No hunk is owed to this item; the submission stands on HEAD bytes
regardless of their landing.

#### Freshness re-pinned at HEAD `0c0537e2` (24/24, zero inheritance)

MATCH (17): target `1cd579fb` (dirty, HEAD pin stands);
`_cross_web_patches` `6b3a7c35`, `_django_patches` `ba98f585`,
`_strawberry_patches` `f77df349`, `conf.py` `c6ad46aa`,
`apps.py` `8ae1a3a3`, `tests/test_graphql_core_patches.py`
`53dca517`, `tests/test_apps.py` `5ca8b62c`,
`tests/base/test_conf.py` `f35c7074`, installed upstream
`869f59f3` (3.2.8), `optimizer/plans.py` `cce98531`, live row
`49e423ea`, `CHANGELOG.md` `d4e10355`,
`utils/execution_mode.py` `9805cdaf`, `connection.py` `4894f90f`,
`list_field.py` `21380eb7`, `resource_policy.py` `4b69e974`
(all three == run-4 pins; bodies/callers re-pinned above).
RE-PINNED (7): `utils/querysets.py` `3616927d` (range diff holds
zero R1/R2-symbol lines; predicate `:377-390`, disposal `:219-232`,
reject `:433-465` re-read — contract text intact, +2 line shift);
`types/resolvers.py` `72d62dc4` (prefetch-origin lines only,
prose-only stands); `schema.py` `e6b52335` (exclusion body re-read
at `:466` — async-mutation window transaction hold-open, disjoint);
`filters/sets.py` `993e887a` (1 comment line, `def apply` `:3506`
unmoved); `docs/GLOSSARY.md` `3413edc3` (entry md5 `fc764053…`
identical, -2 shift to `:2087-2100`; `:313/:542` identical;
kill-switch line `:2097→:2095` content-identical); `docs/TREE.md`
`5d562733` (one-liners + test rows present); spec-050 rationale
`49157062` (range hunks at `:13/:52/:382`, all outside the D13 span
`:452-467`). Every stale input's landed diff is disjoint from the
cited spans; every sweep re-derives the run-4 populations exactly.

#### Exact plan rows (all stand verbatim — no corrections)

- `upstream-patch-lifecycle` (shared): CONFIRM — aspects assign,
  counts LC 4/4/4/4 re-derived, 4 in-family divergences re-swept
  (prefix arm unique; strawberry twin docstringed vs here bare;
  pragma 3+1; Surface-visibility 3/4 absent here).
- `upstream-patch-refusal-wording` (shared): CONFIRM — 2 raises
  assign, census 11/`3+3+2+3` re-derived, hint end-to-end truth
  still oracle-pinned.
- Residual-awaitable list completion (file-local): CONFIRM.
- Plain-method capture/install/probe spelling (file-local): CONFIRM.
- Module status prose: bug, gate key, retirement (file-local): CONFIRM.
- Executor-branch guard predicate vs `is_async_only_iterable`
  (rejected): CONFIRM — contract difference executed (T7).
- Executor-residual completion vs awaitable-refusal-and-disposal
  (rejected): CONFIRM — bodies re-read at HEAD.
- Executor-wrapper home vs `_strawberry_patches.py` (rejected):
  CONFIRM — Decision 13 span intact at HEAD.

#### Checks

- `## Pending execution` empty, correctly: every probe-backed
  conclusion is `execution-verified` with a replay command;
  sharded/Postgres inapplicable-by-construction judged SOUND (no
  database, alias, or dialect decision in the path; the probe opens
  no connection; the one DB-touching oracle runs at the gate).
- AGENTS.md prose rules: no process provenance; `path::Symbol`
  citations; zero-edit so no test-tier question; raw line refs
  permitted in `dry-*` scratchpads. Ruff N/A: the item touches no
  tracked `.py` (artifact `.md` only; both probe scopes gitignored,
  `/tmp` scratch outside the tree).
- Item-scoped diff: target untouched by this item (worktree hunks
  attributed concurrent above); this section + the `Status:` swap
  are the only Worker-2 bytes; plan, ledger, and hunt-owned paths
  untouched.

#### Verdict + handoff to Worker-0

`Status: verified` (plain — no `proof:` entry, no pending
execution). Zero production edits, zero `## Owned changes` rows. No
`## Families` item owed (both assignments reuse already-open
families). Transcribe the six index rows exactly as proposed (3
file-local + 3 rejected per the exact-rows section above; the 2
shared family rows already carried). Scratch custody: `/tmp/w2r7`
holds the re-derived evidence (probe + HEAD extraction); prior
`dry-file-_graphql_core_patches-r2-*` and `dry-adjud1-graphqlcore-*`
scopes were read never, written never — retain per prior custody.
