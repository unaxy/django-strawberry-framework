# DRY review: `django_strawberry_framework/_django_patches.py`

Status: verified
Run: 0.0.15 2026-09-21-2

## System trace

Target: `django_strawberry_framework/_django_patches.py` (423 lines at HEAD,
blob `ba98f5859ec32971c3aa566c221bdc4db392e137`; clean in the working tree;
item-baseline diff empty — see Freshness). The module is one of the package's
four one-per-dependency upstream-patch modules. It replaces Django's
`SimpleTestCase._remove_databases_failures` classmethod with a reimplementation
that adds an `isinstance(method, _DatabaseFailure)` guard before the
`setattr(connection, name, method.wrapped)` step, so any code path that replaced
a connection method between `setUpClass` and `tearDownClass` no longer crashes
teardown with `AttributeError: 'function' object has no attribute 'wrapped'`
(Django Trac #37064, closed upstream as `wontfix`).

HEAD moved once during this item (`bfaee91d` -> `69a25369`, three concurrent
test-tier/docs commits). The target blob is identical at both; of the inputs
this item fingerprints only `docs/TREE.md` and `tests/test_strawberry_patches.py`
changed, and neither moves a conclusion: the four cited TREE lines are
byte-identical (the diff touches only unrelated test-module one-liners plus a
deleted kanban row), and the strawberry suite was named as an F1 oracle by role
only, never inspected. All fingerprints below are new-HEAD blobs.

What the target owns, by role:

- Definitions in-target: the import-time upstream capture
  (`_captured_upstream_descriptor`, `_original_remove_databases_failures`), the
  three-tier shape validation (`_validate_upstream_shape`), the replacement
  (`_patched_remove_databases_failures` + its two stamp `setattr`s), the install
  probe (`_patch_is_installed`), the gated idempotent applier (`apply`), the
  stamp constants, the `ImportError -> None` import sentinel, the Trac-37064
  guard behavior (the isinstance-gated unwrap delta), the shared
  `_is_database_failure` predicate, the two-body audited source set plus the
  validated-source teardown discriminator and its reload-preserved state, the
  classmethod-kind spellings, and the module docstring (Trac record, ecosystem
  precedent, defense-in-depth framing).
- Consumer edges (compose by name, not definitions): `apply()` gates on
  `conf.py::upstream_patches_enabled("django")`; `apps.py::ready()` calls
  `apply()` first of four; `testing/_wrap.py::safe_wrap_connection_method`
  calls the target's `_is_database_failure` predicate (the single wrap-half
  consumer).
- Upstream contract oracles: installed Django 6.1 `test/testcases.py`
  (`_remove_databases_failures` body, `_add_databases_failures` wrap side,
  `_DatabaseFailure` protocol), installed `db/backends/base/features.py`
  (`disallowed_simple_test_case_connection_methods`, four pairs), installed
  `debug_toolbar/panels/sql/tracking.py::wrap_cursor` (the wrap-time isinstance
  precedent the docstring cites).
- Oracles: `tests/test_django_patches.py` (25 rows: lifecycle, inheritance onto
  `TransactionTestCase`/`TestCase`, unwrap/skip/retirement-detector, the audited
  SET plus drift refusals, both gate spellings, reload preservation);
  `tests/testing/test_wrap.py` (9 rows incl. the degrade-vs-abort asymmetry row
  and the two-halves composition row); `tests/test_apps.py` (four-patch dispatch
  + double-reload capture retention, parametrized over all four modules);
  `tests/base/test_conf.py` (gate vocabulary, surveyed by test names). No live
  tier exists: GraphQL execution never runs Django's test-case cleanup loop
  (stated in both suite docstrings; verified by reading — no `test_query` row
  names this target).
- Projections: the target docstring itself; `docs/GLOSSARY.md` ("Django Trac
  #37064 hardening", "defensive upstream patches", `safe_wrap_connection_method`
  entries); `docs/TREE.md` module/test one-liners (generated); spec-024
  (durable contract record, archived); KANBAN `DONE-024-0.0.7` history lines;
  `CHANGELOG.md` 0.0.7 entry (history).

Sites found outside the target, by mechanism sweep (populations printed):

- Patch-stamp mechanism (`_PATCH_OWNER`): exactly the four patch modules. No
  fifth site.
- Install/validate/capture vocabulary (`_patch_is_installed`,
  `_validate_upstream_shape`, `_captured_upstream*`): the same four modules
  (definitions) plus test consumers. No other production site.
- `isinstance(.*_DatabaseFailure)`: exactly one production definition — the
  target's `_is_database_failure` (node 17). Sole production consumer:
  `testing/_wrap.py` (calls the predicate by name). External mirror (not
  package population): debug-toolbar's `wrap_cursor`, verified present at the
  installed 7.1.1. Tests construct `_DatabaseFailure` but never reimplement the
  predicate.
- `method.wrapped` reads in production: the target's live replacement (node 19)
  plus the two pinned upstream-text constants (data, not definitions). No other
  production read (`schema.py`/`finalizer.py` `.wrapped_func`/`.wrapped_cls`
  are Strawberry attributes, unrelated).
- `__func__` unwrap: the target (capture + validate + probe) plus disjoint
  mechanisms excluded on body strength — `filters/sets.py` hook-override
  identity checks, `types/definition.py` resolver unwrap, `mutations/*`
  docstring-only mentions.
- `inspect.signature` arity pins: the four patch modules (upstream-shape
  validation) plus two consumer-config validators excluded on body strength —
  `routers.py::_require_factory_calling_convention` (binds `schema=schema`,
  fail-open on un-introspectable) and `types/base.py::_validate_globalid_callable`
  (binds encoder params + syncness check). Different contracts (consumer config
  vs upstream shape), different error types, different fail-open stances.
- `globals().get` reload-state carry: exactly one site in the package — the
  target's `_validated_remove_databases_failures_source` init. No sibling keeps
  validated state across reload.
- Audited-upstream vocabulary (`_AUDITED*`): the target's body-source SET plus
  `filters/sets.py::_AUDITED_DJANGO_FILTER_RANGE` (a version-tuple range) —
  the R1 considered-and-rejected pair.
- Importers of the target (production): `apps.py` (`apply`), `testing/_wrap.py`
  (`_is_database_failure`). Nothing else reads `_disallowed_connection_methods`
  or `_validated_remove_databases_failures_source` outside the target and its
  suite.

Prior cycle records checked as triggers only: `docs/dry/dry-0_0_11.md` line 26
(the "four functions, wrap half correctly separate" verdict — stale as a census:
the file has since grown the audited SET, the validated-source discriminator,
and the reload-preserved state; the separation claim itself re-proved fresh
below as L2); `docs/dry/dry-file-_cross_web_patches.md` F1/F2 (the two open
families — assigned to, not re-named); `docs/bug_hunt/bug_hunt-0_0_15.md`
(the `globals().get` reload fix — landed, permanent oracle
`test_reload_preserves_the_installed_patch_teardown` exists; no open trigger).
Fresh trace below; nothing imported.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED, hit. The four patch modules are
   the mirror: each spells the safe-replacement lifecycle (import sentinel,
   stamp, capture, validation, install probe, gated applier) in local
   vocabulary. Django's aspects assign to the two open families (F1-assign,
   F2-assign). The wrap-time half (`testing/_wrap.py`) shares the target's
   predicate by name — one definition, not a mirror. The filters
   version-range near-miss yields R1 (rejection). Non-patch flavors
   (`rest_framework`, `forms`, `orders`, `routers`, `types`) share no rule
   with this target (arity-pin and `__func__` sweeps excluded above).
2. Sync/async twins — SEARCHED, ruled inapplicable with reason. The target is
   synchronous Django test-teardown code: Django's `_add/_remove_databases_failures`
   are sync classmethods with no async twin (verified in installed 6.1 source),
   the target defines no `async def`, and no test-case cleanup path awaits.
   The patch family's only async twin (strawberry's sync/async multipart
   delegates) is strawberry-internal and shares no member with this target.
   No behavior pair in-target can drift.
3. Derived rather than repeated knowledge — SEARCHED, hit inside F1-assign,
   L2, L4. The install-state question is answered once (`_patch_is_installed`,
   identity compare); the capture-vs-live split (validate pins the import-time
   capture, the probe reads the live descriptor) is deliberate and pinned by
   `test_apply_reinstalls_when_class_attribute_reverted` and the double-reload
   rows. The `(name, operation)` pairs are never re-spelled: both audited
   shapes read through the same list upstream wrote, discriminated by the
   single `_validated_...` global (L4). The gate is composed by name
   (`upstream_patches_enabled("django")`), never recomputed. The per-module
   tests re-derive installed-state by direct identity compare as independent
   oracles (oracles never read from the owner they check) — listed, not
   counted.
4. Inverse / round-trip pairs — SEARCHED, discharged both halves. Lifecycle:
   install-once process-global; revert exists only as test scaffolding
   (restore saved descriptors by identity), not a product round-trip, and no
   contract requires an uninstall half — inapplicable with reason (same as the
   cross_web item). Upstream pair: `_add_databases_failures` (upstream-owned,
   unpatched) wraps unconditionally — `setattr(connection, name,
   _DatabaseFailure(method, message))` cannot `AttributeError` (verified in
   installed source) — so only the remove half's unconditional `.wrapped` read
   crashes; one-sided hardening is complete, not a missing half. The
   capture-read/install-write kind agreement (classmethod descriptor <->
   `classmethod(...)`) is recorded inside L5 as a kind-parameterized pair.
5. Contracts restated in another medium — SEARCHED, classified. Gate
   semantics: owned by `conf.py::upstream_patches_enabled`, projected by this
   docstring, composed by name in `apply()` (no restatement in code). Dispatch
   order: owned by `apps.py::ready`, projected by GLOSSARY. One-module-per-
   dependency organizing rule: owned by spec-024 Decision 1, instantiated here
   (File `apps.py`/`conf.py` items enumerate it). Trac record + defense
   framing: spec-024 durable, target docstring rationale projection, GLOSSARY/
   TREE/CHANGELOG/KANBAN projections or history. Retirement signal: the
   permanent oracle `test_unpatched_..._crashes_on_non_wrapper` reverts to the
   captured genuine upstream and fails if Django ever fixes the bug (a detector,
   not prose). Test `match=` substrings pin F2 message fragments as oracles
   (listed, not counted). The wrap/unwrap two-halves framing prose appears in
   three docstrings (target, `_wrap.py`, `testing/__init__.py`) — projections
   of one behavioral contract (spec-024 Decision 8), zero additional
   definitions.
6. Enforcement by omission — SEARCHED, no gap. Population, each with its
   contract source: (a) method pairs — read from the same list upstream wrote
   per validated shape, so omission is impossible by construction; a third
   shape raises rather than guesses (oracle
   `test_disallowed_methods_rejects_an_unvalidated_upstream_shape`);
   (b) test-case hierarchy — patched at the defining class `SimpleTestCase`,
   inherited by `TransactionTestCase`/`TestCase` (3 inheritance oracles) and
   verified for direct `SimpleTestCase` subclasses whose MRO excludes
   `TransactionTestCase` (dedicated oracle); (c) aliases — the loop visits
   every alias and skips `cls.databases`, identical to upstream (upstream
   normalizes `"__all__"` to a frozenset on the add side before teardown runs);
   (d) the add half needs no guard (axis 4); (e) wrap-half coverage is
   method-name-generic (arbitrary-names oracle). No member lacks a guard its
   contract (spec-024) requires.

### Enumeration

Instrument: every statement in `ast.Module.body` of the target at HEAD
(24 nodes; verified by executing `ast.parse` — probe P1, 22/22 PASS).
Rule-bearing members each land below in an assignment (F1-assign/F2-assign),
a file-local row (L1–L6), or the rejection (R1); the 5 plain imports carry no
rule.

| # | `ast` node | Name / content | Home |
|---|---|---|---|
| 0 | Expr (docstring) | Trac record, gate/audience narrative, ecosystem precedent, defense framing, visibility | L6 (+ projections noted) |
| 1 | Import | `inspect` | — (no rule) |
| 2 | Import | `textwrap` | — (no rule) |
| 3 | ImportFrom | `django.db::connections` | — (no rule) |
| 4 | ImportFrom | `SimpleTestCase` | — (no rule) |
| 5 | ImportFrom | `.conf::upstream_patches_enabled` | — (consumer edge; rule owned by File `conf.py`) |
| 6 | Try | `from ... import _DatabaseFailure` / `except ImportError -> None` | F1-assign (import sentinel) |
| 7 | Assign | `_PATCH_OWNER_ATTRIBUTE` literal | F1-assign (stamp identity) |
| 8 | Assign | `_PATCH_ORIGINAL_ATTRIBUTE` literal | F1-assign (stamp identity) |
| 9 | Assign | `_PATCH_OWNER` per-module value | F1-assign (stamp identity) |
| 10 | FunctionDef | `_captured_upstream_descriptor` | F1-assign (recovery) + L5 (classmethod-kind spelling) |
| 11 | Assign | `_original_remove_databases_failures` import-time capture | F1-assign (capture) |
| 12 | Assign | `_CLASS_ATTRIBUTE_..._SOURCE` pinned body | L3 (audit data) + R1 (range-pin contrast) |
| 13 | Assign | `_CONNECTION_FEATURE_..._SOURCE` pinned body | L3 (audit data) |
| 14 | AnnAssign | `_AUDITED_..._SOURCES` 2-tuple | L3 (the SET) |
| 15 | AnnAssign | `_validated_..._source` reload-preserved state | L4 (discriminator state) |
| 16 | FunctionDef | `_validate_upstream_shape` | F1-assign (validation step) + F2-assign (3 messages) |
| 17 | FunctionDef | `_is_database_failure` | L2 (shared predicate + asymmetry) |
| 18 | FunctionDef | `_disallowed_connection_methods` | L4 (discriminator; 4th raise is an internal invariant, not F2) |
| 19 | FunctionDef | `_patched_remove_databases_failures` | L1 (guard behavior) |
| 20 | Expr | `setattr` owner stamp | F1-assign (marking) |
| 21 | Expr | `setattr` original stamp | F1-assign (marking) |
| 22 | FunctionDef | `_patch_is_installed` | F1-assign (install check) + L5 (`__func__`-read kind) |
| 23 | FunctionDef | `apply` | F1-assign (4-step order) + gate consumer edge + L5 (`classmethod(...)` install kind) |

Count check: 24 nodes enumerated, 19 rule-bearing nodes assigned (4 of them
split across two rows by aspect: 10, 16, 22, 23), 5 imports correctly
rule-free. Nothing unassigned.

### Challenges

Change challenges per rule (consumers/oracles/projections listed, never
counted). LC/W challenges confirm the cross_web item's counts from this
module's side; G/P/A/D/K/R challenges prove single ownership.

- LC-C1 (stamp rename): rename the `_PATCH_OWNER_ATTRIBUTE` value. Forced
  moves: the literal + capture read + two marking writes in each of the 4
  patch modules. Count: **4 authoritative definitions**. (Django touches: nodes
  7, 10, 20, 21.)
- LC-C2 (apply order): check installed-before-validate. Forced moves: all 4
  `apply()` bodies (all spell gate -> validate -> installed-check -> install).
  Count: **4**.
- LC-C3 (sentinel convention): replace the `None` missing-shape sentinel with
  a dedicated marker. Forced moves: the `None` reads in all 4 modules'
  captures, probes, and validators (django: nodes 6, 16-tier-1, 17).
  Count: **4**.
- LC-C4 (capture tolerance): a capture must additionally tolerate an unstamped
  third-party wrapper by wrapping it instead of replacing it. Forced moves:
  all 4 capture functions (each spells replace-semantics today). Count: **4**.
- W-C1 (hint reword): reword the shared `Disable this patch with
  APPLY_UPSTREAM_PATCHES = {"<dep>": False} ... or use a supported ...`
  grammar. Forced moves: 11 raise sites across the 4 modules (django
  contributes node 16's 3 raises; node 18's raise has no hint and does not
  move). Count: **11 sites / 4 module wordings**.
- G-C1 (guard widening): skip unwrap for any method lacking a `wrapped`
  attribute, not just non-`_DatabaseFailure` instances. Forced moves: the
  target's predicate (node 17) — the replacement (node 19) and the wrap-half
  consumer follow by construction. Count: **1 definition**.
- P-C1 (degrade reversal): the wrap half must abort (not install) when the
  private symbol is missing. Forced moves: the target's predicate — the only
  `None`-branch; `_wrap.py` follows by construction. Count: **1**.
- A-C1 (audit widening): Django 6.2 renames the feature flag; the SET gains a
  third body. Forced moves: the target's constants + discriminator read
  (nodes 12–15, 18) — strawberry's shield pin and every delegator validate
  unchanged (disjoint upstreams). Count: **1** (the pin *mechanism* stays
  F1's; the *data* is file-local).
- D-C1 (discriminator removal): drop validated-state carry (stateless
  teardown). Forced moves: only the target — no sibling keeps validated
  state (`globals().get` sweep: 1 site). Count: **1**.
- K-C1 (kind reshape): upstream makes the method a plain function. Forced
  moves: only this module's classmethod-kind spellings (nodes 10/22/23) —
  siblings patch disjoint kinds (property ×1, plain ×2). Count: **1**.
- R-C1 (range widening): django-filter 28 ships; the optimizer range may
  widen. Forced moves: `filters/sets.py` only — the body SET cannot move on
  a version event (it keys on source text, and reformats fail it even within
  one version). Count: **1**, and symmetrically a body reformat moves only
  the SET. Two rules sharing a word, not a rule.

Experiments: one read-only probe, `execution-verified` (22/22 PASS),
command + per-claim mapping under Behavioral proof; replay in
`docs/dry/temp-tests/dry-file-_django_patches-r2-w1/probe_upstream_shape.py`.
No pytest run (permanent oracles run at the gate; the working tree is dirty
elsewhere so a shared-tree run would not measure HEAD).

## Findings

### F1-assign — Upstream-patch safe-replacement lifecycle (assign to open family `upstream-patch-lifecycle`)

- Contract + variation: as named by the cross_web item (F1 there): how a patch
  module safely replaces one upstream member process-wide (import sentinel,
  genuine capture, owner/original stamps, presence + call-shape validation,
  idempotent self-healing install, per-dependency gate). This module's aspects:
  `None`-sentinel import (node 6), stamp literals (nodes 7–9), reload-tolerant
  recovery (node 10, concept), import-time capture (node 11), three-tier
  validation presence/signature/body steps (node 16, mechanism), two marking
  writes (nodes 20–21), identity install check (node 22, concept), gate ->
  validate -> installed-check -> install order (node 23). Legitimate
  variation (django's parameters): dependency key `"django"`, classmethod
  descriptor kind, reimplementer depth with a 2-body audited set.
- Sites + roles (definitions): this module's nodes above, jointly with the
  three sibling aspects the cross_web artifact inventoried (property kind,
  4-method conjunction, single-identity probe). Consumers: `apps.py::ready`
  (django dispatched first of four); `tests/test_apps.py::_PATCHED_SLOTS` +
  `_all_patches_installed`. Oracles: the 25-row per-module suite (lifecycle,
  drift refusals, both gate spellings, reload preservation), the `test_apps.py`
  dispatch + double-reload rows. Projections: this docstring's lifecycle prose,
  `conf.py::UPSTREAM_PATCH_DEPENDENCIES` comment, GLOSSARY entries.
- Challenges: LC-C1 count 4; LC-C2 count 4; LC-C3 count 4; LC-C4 count 4
  (see ### Challenges). No new family named: every count above moves the
  already-open family.
- Owner + lifetime: TBD by the family item (unchanged by this assignment).
  Lifetime: process-global from `AppConfig.ready()`; reload-safe by stamp
  recovery; invalidation = none (install-once).
- Migration: for the family item to decide (driver with kind adapters vs
  recorded per-module ownership). This module's kind adapter, if extracted,
  is L5; its reimplementer data is L3; its validated-state carry is L4.
- Distinct behavior (stays separate whatever the family decides): the
  classmethod-kind spellings (L5), the 2-body SET + teardown discriminator +
  reload-preserved state (L3/L4), the guard behavior itself (L1/L2).
  In-family divergences for the family item (observed, not decided here):
  graphql_core's capture accepts any `django_strawberry_framework.*` owner
  prefix where the other three require exact equality (already recorded by
  the cross_web item); graphql_core's docstring carries no Surface-visibility
  section where the other three do (prose gap, no behavioral contract
  requires it — not a defect).
- Behavioral proof: definition counts `static-reviewed` (mechanism sweeps
  with populations). Lifecycle liveness `execution-verified`: P2 (capture IS
  the live upstream descriptor in a bare process, unstamped, uninstalled
  there), P3 (installed Django 6.1 body validates live and returns the
  feature-flag source), P6 (probe `is False` pre-install documents the
  capture-vs-install split). Permanent oracles (idempotence, self-heal,
  double-reload) `static-reviewed` — exist at HEAD, run at the gate.
  Replay: `uv run python
  docs/dry/temp-tests/dry-file-_django_patches-r2-w1/probe_upstream_shape.py`.
- Structural gate + negative control: owed by the family item (named by the
  cross_web item; e.g. a population-enumerated check over the four modules'
  lifecycle members). Negative-control shape: a hand copy of the lifecycle
  with one step reordered or one stamp renamed must fail the gate while every
  behavioral oracle stays green. No gate proposed here beyond the requirement.
- Coupling: F2-assign (wording lives inside the same `apply()`/`validate`
  bodies — land together or sequence explicitly); L3/L4 (the discriminator
  reads the validated source this validation produces — the family item must
  keep them consistent); sibling File items (`conf.py`, `apps.py`,
  `_strawberry_patches.py`, `_graphql_core_patches.py`) trace the same sites
  from their side; Worker 0 dedups identical namings.
- Freshness: target `ba98f5859ec32971c3aa566c221bdc4db392e137`;
  `_cross_web_patches.py` `6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`;
  `_strawberry_patches.py` `f77df3499eb96051d70055266a677ca3cde5b219`;
  `_graphql_core_patches.py` `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`;
  `conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`;
  `apps.py` `8ae1a3a3b12f0c9792094959c573ea6fab5d804f`;
  `tests/test_django_patches.py` `e26a26099c12efb2e2cab1e324b73226eab5dd76`;
  `tests/test_apps.py` `5ca8b62c53185343ebfec95315f59ec6104fc851`;
  `tests/base/test_conf.py` `f35c70742354d0ab123b163a92c6a8a503c6ea29`;
  `docs/GLOSSARY.md` `bc51debc54cf3ed142b45fa9feda1b99bce60c79`;
  installed Django 6.1 `test/testcases.py` blob
  `f866a33963d0842f989f2589ed93a9d51938dc03` (`git hash-object`).
  Searched populations: `_PATCH_OWNER` -> 4 production files;
  `_patch_is_installed|_validate_upstream_shape|_captured_upstream` -> 4
  production + test consumers; `upstream_patches_enabled` production call
  sites -> exactly the 4 `apply()` gates; `inspect.signature` -> 4 patch
  modules + 2 consumer-config validators excluded on body strength
  (`routers.py` `a18c5001471d4a937bb81d2ff41a2e442e7d2dad`,
  `types/base.py` `91c587477ff8257e80dbb9a9c79859f34c5b4c7e`).

### F2-assign — Upstream-patch refusal wording (assign to open family `upstream-patch-refusal-wording`)

- Contract + variation: as named by the cross_web item (F2 there): the
  `RuntimeError` grammar every patch `apply()` raises on unsupported upstream
  shape (`Cannot apply django-strawberry-framework's <patch> patch:
  <expected-shape> ... Disable this patch with APPLY_UPSTREAM_PATCHES =
  {"<dep>": False} or use a supported <version-noun>.`). This module's
  aspects: node 16's 3 raises (symbol/descriptor tier, `(cls)` signature
  tier, audited-body tier — all carrying the `{"django": False}` hint and
  the `Django version` noun). Node 18's raise is explicitly NOT a member:
  it fires at teardown (never from `apply()`), carries no opt-out hint, and
  phrases an internal invariant ("ran without a validated upstream body") —
  a different contract (L4), proven by W-C1 (a hint reword does not move it).
- Sites + roles (definitions): this module's 3 raises, jointly with the 8
  sibling raises the cross_web artifact inventoried (3 + 3 + 2). Oracles
  (listed): per-module `match=` fragments (`_DatabaseFailure`,
  `expected (cls) signature`, `upstream body`, `{"django": False}`).
  Projections: module-docstring opt-out spellings, `conf.py` gate docstring,
  GLOSSARY entries.
- Challenges: W-C1 count 11 sites / 4 module wordings (django: 3).
- Owner + lifetime: TBD by the family item (unchanged by this assignment;
  natural candidates recorded by the cross_web item).
- Migration: the family item's decision (one message builder vs recorded
  deliberate per-module wording). The `match=` oracles move as oracles, never
  rewritten to read from a builder.
- Distinct behavior: the per-site expected-shape clauses stay per-module
  (they name disjoint upstream members); only the shared opt-out/two-exit
  framing is the family's. Node 18's invariant raise stays with L4.
- Behavioral proof: `static-reviewed` (literal sweeps; wording has no runtime
  behavior beyond the raised text, which the `match=` oracles pin). The
  hint's end-to-end truth (gate precedes validation, so the named escape
  silences the abort) is pinned by permanent oracle
  `test_django_dependency_opt_out_silences_drifted_pin_abort`
  (`static-reviewed` — exists at HEAD, runs at the gate).
- Structural gate + negative control: owed by the family item (named by the
  cross_web item: pin the hint spelling against `UPSTREAM_PATCH_DEPENDENCIES`
  keys + the gate's accepted shapes; negative control: a message with a
  renamed key passes behavior oracles but fails the gate).
- Coupling: F1-assign (same bodies; sequence together). Sibling File items
  as in F1-assign.
- Freshness: production fingerprints as in F1-assign; oracles
  `tests/test_django_patches.py`, `tests/base/test_conf.py` as above.

### L1 — Trac #37064 unwrap-time guard behavior (file-local)

- Contract + variation: the replacement's one behavioral delta over upstream:
  unwrap only what Django wrapped (`_is_database_failure` gate before
  `setattr(..., method.wrapped)`), leaving any foreign replacement untouched.
  Strictly defensive in both directions (still-wrapped -> unwrapped exactly as
  upstream; replaced -> left alone). Varies only with this upstream bug's fix
  shape. Contract sources: spec-024 Decision 3 ("exactly one behavioural
  addition"), the module docstring's defensive-framing section, Trac #37064.
- Sites + roles: sole definition — node 19. Consumers: none in production
  (invoked by Django's `addClassCleanup` machinery at `tearDownClass`).
  Oracles: `test_patched_..._unwraps_a_real_wrapper` (happy path),
  `test_patched_..._skips_non_wrapper_methods` (the fix proper),
  `test_patched_..._covers_direct_simple_test_case_subclass` (MRO premise),
  `test_unpatched_..._crashes_on_non_wrapper` (retirement detector: fails if
  installed Django ever fixes the bug), the two-halves composition row in
  `test_wrap.py`. Projections: GLOSSARY "Django Trac #37064 hardening" entry,
  CHANGELOG 0.0.7 entry.
- Challenges: G-C1 count 1 (predicate moves; replacement and wrap-half follow
  by construction). A-C1 confirms the guard is independent of the audit data
  (a third body moves L3/L4, not the guard's two arms).
- Owner + lifetime: the target module; dies with the module at retirement
  (upstream fix -> detector fails -> deliberate removal).
- Migration / Distinct behavior / Coupling: none pending; coupled to L2
  (consumes the predicate) and L4 (reads the method list through the
  discriminator) by name, not by copy.
- Behavioral proof: guard arms `static-reviewed` against the named permanent
  oracles (exist at HEAD, run at the gate). Retirement-detector premise
  `execution-verified`: P2 (the capture the detector reverts to IS genuine
  upstream) + P3 (installed 6.1 body is the pinned feature shape, whose
  `setattr(..., method.wrapped)` line the detector's crash needs — P3's
  shared-unwrap-line check). Same replay command as F1-assign.
- Structural gate + negative control: none owed (single site; the detector
  oracle already fails if the guard is silently removed — removing the
  `isinstance` check turns the skip oracle red).
- Freshness: target + `tests/test_django_patches.py` + `tests/testing/test_wrap.py`
  (`4d3c1351254377197994ee577e4f77844c7c309b`) + spec-024
  (`46335d7e98ea569cd85c3ec256b7276b04fb7dc1`) + installed `testcases.py` blob
  as in F1-assign. Excluded on body strength: upstream's own loop (external
  text the replacement mirrors, not a package definition).

### L2 — The `_DatabaseFailure` predicate + degrade-vs-abort asymmetry (file-local)

- Contract + variation: what counts as Django's wrapper (`_DatabaseFailure is
  not None and isinstance(method, _DatabaseFailure)`), shared by both halves
  of the defense-in-depth; when the private symbol is absent the wrap half
  degrades ("no wrapper visible, slot free" -> install) while the unwrap half
  aborts at validation (tier 1 raises before anything installs). Contract
  source: spec-024 Decision 8 (pins the asymmetry and its reason: a public
  import dying on a private-symbol move is worse than a wrap that proceeds;
  the degraded path is reachable only with the Django patch opted out since
  otherwise `ready()` refused to boot). Varies only with Django's private
  symbol.
- Sites + roles: sole definition — node 17 (one `isinstance` spelling in
  production; sweep population: every `isinstance(.*_DatabaseFailure)` hit is
  this line, docstrings, tests constructing the class, or history). Two
  enforcement sites, both composing by name: node 19 (unwrap gate) and
  `testing/_wrap.py::safe_wrap_connection_method` (wrap decline) — the
  healthy shape (principle 6), not duplication. The abort arm lives in node
  16 tier 1 (same module). Oracles: wrap-half asymmetry row
  (`..._installs_when_database_failure_symbol_missing`), decline/install rows,
  unwrap-half `..._fails_loudly_when_database_failure_symbol_missing`,
  composition row. External mirror (not package population): debug-toolbar's
  `wrap_cursor` isinstance check — `execution-verified` present at installed
  7.1.1 (P5).
- Challenges: G-C1 count 1; P-C1 count 1 (either change moves the predicate
  alone; both enforcement sites follow by construction — that is the proof no
  second definition exists). The prior-cycle (0_0_11) "correctly separate
  halves" verdict re-checked as a trigger: the halves are still separate
  lifecycle sites, now sharing one predicate — confirmed and strengthened.
- Owner + lifetime: the target module — the package's owner of Django-private-
  symbol knowledge; both consumers are Django-test-teardown-domain, and the
  patch module is import-safe by construction (try/except sentinel), so the
  public `testing` package importing a private name degrades exactly as
  Decision 8 specifies. Lifetime: import/process-global, same as F1-assign.
- Migration / Distinct behavior: none pending (already consolidated by name).
  Distinct: the wrap half's `TypeError`-on-non-callable and restoration
  semantics stay in `_wrap.py` (not this file's rules; File `testing/_wrap.py`
  enumerates them).
- Behavioral proof: predicate truth table `execution-verified` (P6: True for
  a live `_DatabaseFailure`, False for a plain function). Asymmetry arms
  `static-reviewed` against the named permanent oracles. Same replay command.
- Structural gate + negative control: none owed (single definition; a second
  spelling would be caught by the `isinstance(.*_DatabaseFailure)` sweep
  population recorded here, not by a bespoke gate).
- Coupling: `_wrap.py` consumer (File `testing/_wrap.py` item traces the
  consumer side); L1/L4 consume the predicate by name.
- Freshness: target + `testing/_wrap.py`
  (`0df97813659bea9ed2002f64e6885896c5cabd6f`) + `testing/__init__.py`
  (`48b45d1b433283c40bf8d602d71a26d261a833b2`) + both suites + spec-024 as
  above + installed `tracking.py` blob
  (`046b254a52f7849f4edf8178a6b860b9d0c66e0f`).

### L3 — Two-body audited upstream source set (file-local declarations)

- Contract + variation: the closed SET of upstream bodies the reimplementation
  supersedes (class-attribute shape for Django 5.2.16–6.0.x, feature-flag
  shape for 6.1), plus the widening rule: a new body joins only after its read
  path is reimplemented in L4 and the crash shape re-confirmed (the
  "WIDENING THIS SET IS AN AUDIT" comment). Varies only with Django's
  teardown-loop text. The pin *mechanism* (membership test before supersede)
  is F1-assign's; this row is the django *data* it operates on (principle 1:
  declarations, not a second driver).
- Sites + roles: sole definitions — nodes 12–14. Consumed by name: node 16
  tier 3 (membership test), node 18 (discriminator key), node 15 (carries the
  validated member). Oracles: `test_audited_..._are_exactly_the_two_known_shapes`
  (closed-SET pin), per-shape acceptance rows (nested classes whose dedented
  source must equal the constants — written to match byte-for-byte, not read
  from the constants), unaudited-shape refusal, sourceless-distribution
  refusal. The strawberry shield's single-source pin is F1-assign's distinct
  behavior, not a second site of THIS set (disjoint upstream, disjoint text).
- Challenges: A-C1 count 1 (a third Django body moves only these nodes +
  L4's read; every other pin in the package is text-disjoint and cannot
  move). R-C1 proves the version-range pin is a different rule (R1).
- Owner + lifetime: the target module (audit data lives with the
  reimplementation it authorizes); dies with the module at retirement.
- Migration: none pending. If F1-assign extracts a driver, these nodes become
  that driver's django declaration record (shape noted for the family item;
  no design here).
- Behavioral proof: `execution-verified` — P3 (installed 6.1 source equals
  the feature constant and differs from the class constant; live
  `_validate_upstream_shape()` returns the feature source; the SET is exactly
  the two constants; both pinned bodies share the `method.wrapped` unwrap
  line the guard needs). Same replay command.
- Structural gate + negative control: none owed beyond the existing closed-SET
  oracle (a third body added without its L4 read path is caught by review of
  that oracle's failure mode, and the WIDENING comment states the rule at the
  owner per principle 10).
- Coupling: F1-assign (mechanism) + L4 (discriminator reads the validated
  member) + R1 (range-pin contrast).
- Freshness: target + `tests/test_django_patches.py` + installed
  `testcases.py` blob as above.

### L4 — Validated-source teardown read + reload-preserved state (file-local)

- Contract + variation: at teardown, read the `(name, operation)` pairs from
  wherever the VALIDATED body says they live (class attribute for the 5.2–6.0
  shape, connection feature flag for 6.1 — never by probing `cls` for a
  legacy attribute, since 6.1's add side ignores such an attribute and removal
  must stay symmetric); an unrecognized validated value raises an internal
  invariant instead of guessing; the validated value survives an in-process
  reload via `globals().get` so the still-installed previous generation's
  teardown stays valid until the next `apply()` revalidates. Varies only with
  Django's method-list storage. The `globals().get` carry is safe by
  construction (only `apply()` stores, only after validating this process's
  own Django; a carried value can authorize no new install).
- Sites + roles: sole definitions — nodes 15, 18. Uniqueness: `globals().get`
  sweep = 1 site package-wide; no sibling keeps validated state (all are
  stateless after install). Consumers: node 19 (teardown loop). Oracles:
  per-shape read rows incl. the legacy-attribute-ignored row (6.1 symmetry),
  unvalidated-shape invariant row, reload-preservation row (pins the exact
  failure the naive `= None` reset caused, per the bug-hunt record).
- Challenges: D-C1 count 1 (no sibling moves — nothing else keeps validated
  state). A-C1 moves L3+L4 together (one rule's data + read — the SET without
  its read is unaudited by the WIDENING rule, so they are one row).
- Owner + lifetime: the target module. Lifetime (principle 4): owner = this
  module's dict; validity key = membership in the audited SET; publish point
  = `apply()` post-validation store; who may mutate = `apply()` only;
  invalidation = reload preserves (deliberately), next `apply()` revalidates.
- Migration / Distinct behavior: none pending. Distinct: node 18's invariant
  raise is NOT an F2-assign member (no hint, teardown-time, internal) — W-C1
  proves it.
- Behavioral proof: `static-reviewed` against the named permanent oracles
  (reload row pins the pre-fix `RuntimeError` shape; symmetry row pins the
  legacy-attribute ignore). Supporting live facts `execution-verified`: P4
  (class attribute gone at installed 6.1, so the discriminator is load-bearing
  there, not vestigial; feature flag carries exactly the four documented
  pairs). Same replay command.
- Structural gate + negative control: none owed (single site; the reload and
  invariant oracles fail if the carry or the raise is removed).
- Coupling: F1-assign (validation produces the value this reads — the family
  item must keep them consistent) + L3 (data) + L1 (consumer).
- Freshness: target + `tests/test_django_patches.py` + installed
  `testcases.py` + installed `features.py` blobs (`testcases` as above,
  `features.py` `9f00dcfc3537168cf725d97dd8475a66caf7f522`).

### L5 — Classmethod-descriptor capture/install/probe spelling (file-local kind adapter)

- Contract + variation: the descriptor-kind parameter of F1-assign as spelled
  for a classmethod target: `__dict__.get` + `__func__` unwrap + exact-owner
  recovery in the capture, `isinstance(descriptor, classmethod)` + arity pin
  in validation, `__func__`-identity read in the probe (with the
  attribute-absent -> `False` branch), `classmethod(...)` install. Varies
  only with this upstream member's descriptor kind.
- Sites + roles: sole definitions — the kind-specific lines of nodes 10/16/
  22/23. Siblings patch disjoint kinds (property ×1, plain ×2) — parameters
  of F1-assign, not second classmethod sites (descriptor-kind sweep:
  classmethod ×1, property ×1, plain ×2 — no second classmethod site anywhere
  in the package). Oracles: double-reload capture-retention rows, the
  attribute-absent probe row, self-heal row.
- Challenges: K-C1 count 1 (a kind reshape moves only this module).
- Owner + lifetime: the target module (kind adapter of the F1-assign machine,
  wherever F1 lands — the family item may relocate this spelling as F1's
  classmethod adapter; until then it lives here).
- Migration / Distinct behavior: none pending; if F1 extracts a driver, this
  row becomes that driver's classmethod adapter.
- Behavioral proof: `static-reviewed` (kind sweep + the oracles above). Kind
  facts `execution-verified`: P2 (live descriptor is a classmethod whose
  `__func__` is unstamped upstream), P4 (defined on `SimpleTestCase`, not
  redefined below). Same replay command.
- Structural gate + negative control: none owed (single site).
- Coupling: F1-assign (kind adapter of that machine).
- Freshness: target + three sibling fingerprints as in F1-assign +
  `tests/test_apps.py` as above.

### L6 — Trac record + ecosystem-precedent + defense-in-depth framing prose (file-local)

- Contract + variation: the module docstring's django-specific record — Trac
  #37064 mechanics and `wontfix` link, the debug-toolbar wrap-time precedent
  vs cache-panel sentinel analysis, the wrap-time/unwrap-time defense framing,
  the Surface-visibility rule (private module, public `apply` for tests).
  Varies only with this upstream's history.
- Sites + roles: sole definition — node 0 (the django-specific sections; the
  lifecycle/gate sentences project F1-assign/`conf.py` rules). Retirement
  signal: the permanent unpatched-crash oracle (detector, not prose).
  Projections of this prose: GLOSSARY/TREE.md lines, KANBAN history.
- Challenges: posit a Trac-status change (upstream fixes #37064): only this
  docstring moves (GLOSSARY follows as projection, never counted) — plus the
  deliberate retirement the detector forces. Count: **1**.
- Owner + lifetime: the target module; dies with the module at retirement.
- Migration / Distinct behavior / Coupling: none (file-local prose).
- Behavioral proof: every checkable prose claim `execution-verified` — P3
  (installed body matches the pinned shape the record describes), P4
  (defined-on-SimpleTestCase + hierarchy claims; four-pairs claim), P5
  (toolbar precedent line present verbatim). The `wontfix` status and ticket
  link are upstream facts cited, not package behavior. Same replay command.
- Structural gate + negative control: none owed (unique prose; no bypass
  population).
- Freshness: target + installed blobs (`testcases.py`, `features.py`,
  `tracking.py`) + `docs/GLOSSARY.md` as above.

### R1 — Audited-body SET vs audited-version RANGE (rejected)

- Contract + variation: two spellings of "audited" that look like one rule
  and are two. The target's `_AUDITED_..._SOURCES` pins exact source TEXT a
  reimplementation supersedes: any text change — including a reformat within
  one version — fails closed, and the validated member doubles as the
  teardown-read discriminator. `filters/sets.py::_AUDITED_DJANGO_FILTER_RANGE`
  pins a version-tuple RANGE for optimizer capability gating: any release
  inside the range passes without re-audit, and no text is ever read.
  Concrete contract difference: a Django body reformat with zero behavior
  change moves the SET (must re-audit) and cannot move the RANGE (no release
  involved); a django-filter 28.0 release moves the RANGE's upper bound and
  cannot move the SET (different upstream, text-keyed). A shared-form
  consolidation (one "audited upstream" record) would own the English word
  and the fail-closed stance — nothing executable — while each remainder kept
  its entire mechanism (text-membership vs range-compare) and its own trigger
  vocabulary. Reconsideration trigger: if the teardown discriminator ever
  keyed off `django.VERSION` instead of validated source text, the two pins
  would share a range-comparison shape; consolidate then. Durable home: this
  artifact (file item cannot edit); the F1-assign family item records the
  outcome at the pin-mechanism owner.
- Sites + roles: two independent definitions (rejected pair). Target nodes
  12–14 (+ L3/L4 machinery); `filters/sets.py` range + `_release_is_audited`
  + `_DJANGO_FILTER_OPTIMIZER_AUDITED` (inspected: version-tuple compare at
  import, capability flag consumed at generation time).
- Challenges: R-C1 count 1 per direction (each change moves exactly one
  side). A shared form would own 0 executable lines.
- Owner + lifetime: unchanged — each side keeps its owner.
- Migration: none (rejection).
- Distinct behavior: preserved exactly — text-identity vs range-membership
  ARE the observable distinction (reformat-without-release and release-
  without-text-change move opposite sides).
- Behavioral proof: `static-reviewed` — rests on reading both mechanisms
  (the SET's membership test + discriminator vs the RANGE's tuple compare +
  capability flag). No execution claimed or needed (no shared runtime
  behavior asserted).
- Structural gate + negative control: none owed (rejection, no owner to
  bypass).
- Coupling: L3 (the SET side of the pair).
- Freshness: target as above; `filters/sets.py`
  `4ab65a26b0ccf56f7f40f4938282bba9690673d1`.

## Defects

None found. Near-misses examined and ruled out (each checked against its
permanent oracle or live upstream bytes, not assumed):

- graphql_core's prefix-match capture vs the other three modules' exact-match:
  an in-family contract divergence, recorded under F1-assign for the family
  item — not a defect (members are disjoint so no behavior differs; no
  contract source requires exactness).
- graphql_core's docstring lacking the Surface-visibility section: prose gap,
  not behavior (no contract source requires the section).
- Node 18's hint-less raise: an internal teardown invariant by design (L4),
  not an F2-assign wording gap — proven by W-C1.
- The add half (`_add_databases_failures`) unpatched: safe by construction
  (unconditional wrap cannot `AttributeError` — verified in installed source),
  not an axis-6 omission.
- `cls.databases` as `"__all__"`: normalized to a frozenset by the add side
  before teardown runs (verified in installed source) — the patched loop's
  `in` test matches upstream exactly.
- A bare-function (non-classmethod) foreign assignment to the class attribute:
  the probe's `is` identity reports `False` and the next `apply()` self-heals
  — correct by construction across all non-identical shapes, not a missing
  branch.
- Reload hazards (stale capture, validated-state reset, pre/post-reload
  identity operands), `None`-sentinel mishandling, live-vs-capture confusion,
  gate bypass: each traced to a passing permanent oracle (double-reload rows,
  reload-preservation row, missing-symbol refusal row, both gate spellings,
  self-heal row). No guard any contract requires is missing (axis 6: full
  population enumeration, no gap).
- The upstream defect is still present at installed Django 6.1 (P3: the pinned
  feature body still reads `method.wrapped` unconditionally), so no retirement
  question arises this cycle.

## Pending execution

None. No `proof:` entry is owed: every conclusion resting on a probe is
`execution-verified` above (22/22 PASS, replay command recorded), and every
other conclusion rests on permanent oracles that the cycle gate runs.
`FAKESHOP_SHARDED=1` and Postgres cells are inapplicable by construction for
the probe-backed conclusions (pure import/source/shape facts; the probe opens
no connection and reads no database): the one sharded-sensitive permanent
oracle (`test_disallowed_methods_read_falls_back_...`, which installs the flag
on every alias) already handles both modes by construction and runs at the
gate — stated here for Worker 2's judgment.

## Index rows for Worker 0

No new families: the lifecycle aspects assign to the already-open
`upstream-patch-lifecycle` row and the 3 refusal messages to the already-open
`upstream-patch-refusal-wording` row (no index edits owed for those). New rows:

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| Trac #37064 unwrap-time teardown guard | `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures` | `django_strawberry_framework/_django_patches.py` | File `_django_patches.py` | file-local |
| The `_DatabaseFailure` isinstance predicate + wrap-degrades/unwrap-aborts asymmetry | `django_strawberry_framework/_django_patches.py::_is_database_failure` | `django_strawberry_framework/_django_patches.py` | File `_django_patches.py` | file-local |
| Two-body audited upstream source set for the reimplemented teardown | `django_strawberry_framework/_django_patches.py::_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` | `django_strawberry_framework/_django_patches.py` | File `_django_patches.py` | file-local |
| Validated-source teardown read + reload-preserved validation state | `django_strawberry_framework/_django_patches.py::_disallowed_connection_methods` | `django_strawberry_framework/_django_patches.py` | File `_django_patches.py` | file-local |
| Classmethod-descriptor capture/install/probe spelling | `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor` | `django_strawberry_framework/_django_patches.py` | File `_django_patches.py` | file-local |
| Trac record + ecosystem-precedent + defense-in-depth framing prose | `django_strawberry_framework/_django_patches.py` (module docstring) | `django_strawberry_framework/_django_patches.py` | File `_django_patches.py` | file-local |
| Audited-body SET vs audited-version RANGE | `django_strawberry_framework/_django_patches.py` (rejection recorded in File artifact; F1-assign family item records at the pin-mechanism owner) | `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/filters/sets.py` | File `_django_patches.py` | rejected |

## Judgment

Zero-edit result, proved: the target is a single-responsibility patch module
whose every rule-bearing member is assigned — lifecycle aspects and 3 refusal
messages to the two already-open families (`upstream-patch-lifecycle`,
`upstream-patch-refusal-wording`; counts LC 4 / W 11-over-4 confirmed from
this module's side), six file-local rows with their single-ownership
challenges, one rejection with its contract difference and trigger. No new
family named. No production edit owed, none made; no defects; no pending
execution. The upstream defect is still present at installed Django 6.1, so
retirement is not in question this cycle. HEAD moved `bfaee91d` -> `69a25369`
during the item; the target blob is unchanged and every cited line re-verified
against the new HEAD.

## Independent verification (Worker 2)

### Phase A (as recorded pre-read, verbatim)

Written to `docs/dry/temp-tests/dry-file-_django_patches-r2-w2/phase_a_expectations.md`
BEFORE opening this artifact (HEAD `69a25369` throughout). Reproduced exactly:

> Instrument: every node in `ast.Module.body` of the target (docstring + imports +
> `Try` + assignments + defs + module-level `Expr` stamps). Count: **24 top-level
> nodes**: 1 module docstring, 5 imports (inspect, textwrap, connections,
> SimpleTestCase, upstream_patches_enabled), 1 `Try` (`_DatabaseFailure` import
> with `None` fallback), 3 stamp constants, 7 `FunctionDef`, 0 `AsyncFunctionDef`,
> 0 `ClassDef`, 5 data assignments (1 `Assign` capture + 2 `Assign` pinned sources
> + 2 `AnnAssign` audited-tuple / validated-source), 2 module-level `setattr`
> stamp `Expr`.
>
> 15 named members to home: `_PATCH_OWNER_ATTRIBUTE`, `_PATCH_ORIGINAL_ATTRIBUTE`,
> `_PATCH_OWNER`, `_captured_upstream_descriptor`,
> `_original_remove_databases_failures`,
> `_CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE`,
> `_CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE`,
> `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`,
> `_validated_remove_databases_failures_source`, `_validate_upstream_shape`,
> `_is_database_failure`, `_disallowed_connection_methods`,
> `_patched_remove_databases_failures`, `_patch_is_installed`, `apply`.
>
> Sites + roles (my trace): Definition (this file): the Trac #37064 unwrap guard,
> the dual-shape method-list read, the 3-tier validate, the classmethod-aware
> install check, the gated `apply`, the stamp constants + capture. Consumers:
> `testing/_wrap.py::safe_wrap_connection_method`, `apps.py::ready`, 4x `apply` ->
> `conf.py::upstream_patches_enabled`. Oracles: `tests/test_django_patches.py`
> (25 tests + 1 helper), `tests/testing/test_wrap.py` (9 tests),
> `tests/test_apps.py` dispatch + reload rows; all spell expectations literally,
> none reads the owner. Projections: module docstring, the strawberry precedent
> citation, spec-024 + GLOSSARY + TREE rows.
>
> Challenges: C1 stamp rename -> 4 (route `upstream-patch-lifecycle`); C2 wording
> change -> 11 sites / 4 wordings (route `upstream-patch-refusal-wording`); C3
> install-check change -> 4 defs but kind-specific bodies (route lifecycle with
> kind note); C4 predicate change -> 1 definition + 2 by-name consumers
> (file-local); C5 third body shape -> 1 definition (file-local); C6 gate change
> -> 1 definition in conf (independence).
>
> Assignment: lifecycle aspects + 3 refusal raises to the two open families;
> guard rule, dual-shape read, teardown-without-validation raise file-local;
> expected rejections: (a) filters audited-range vs body-source pin, trigger a
> shared "audited upstream artifact" record type; (b) wrap vs unwrap halves (one
> predicate, two sites), trigger a predicate fork.
>
> Censuses: stamps 4/4 identical literals, owners per-module; install/validate
> vocabulary 4/4 each (django validate returns `str`); 12 `raise RuntimeError`
> (3+4+2+3), 11 "Cannot apply" + 1 teardown invariant; isinstance sweep exactly
> 1 code site (`_is_database_failure`); `method.wrapped` 1 live + 2 pinned-text +
> prose; audited-word target 14 lines, filters range separate; gate callers
> exactly the 4 canonical names; installed Django 6.1, no legacy class attr,
> installed body is the feature shape.
>
> Matrix: (1) cross-flavor searched, 2 open families routed, no new candidate;
> (2) sync/async inapplicable (0 async defs, sync-only teardown); (3) derived
> once, no second site, discriminator deliberate; (4) add/remove Django-owned,
> remove-side hardening only; (5) oracles + projections classified, no
> restatement; (6) 4 keys x 4 gates, loop-level guard, no gap.
>
> Sharded/Postgres: expect inapplicable-by-construction (no DB/alias/dialect
> decision); judge W1's reason in Phase B.
>
> Expected verdict: `verified` PROVIDED full 24-node/15-member enumeration, real
> matrix discharge, C1-C6-style challenges, the two family routings, rejections
> with triggers, and HEAD-`69a25369` fingerprints (target `ba98f585...` plus the
> sibling/conf/apps/wrap/suite blobs, all CLEAN).

### Reconciliation (every difference)

- R-1 Enumeration: NO difference. W1's 24 nodes numbered 0-23 in source order
  match my 24 node-for-node (docstring, 5 imports, Try, 3 consts, capture def,
  capture assign, 2 pinned sources, 2 AnnAssigns, 4 defs, 2 setattr Exprs, 2
  defs). 19 rule-bearing + 5 rule-free; the 4 aspect-split homes (nodes 10, 16,
  22, 23) are exactly the splits my C3/F1-vs-F2 notes anticipated. Checked
  member-by-member against `ast.parse` output: every member homed, nothing
  unassigned.
- R-2 Challenges: NO conflict. W1's LC-C1/W-C1/G-C1/P-C1/A-C1/D-C1/K-C1/R-C1
  reproduce my C1-C6 counts (4 / 11-over-4 / 1 / 1 / 1 / 1 / 1 / 1-per-direction)
  and add LC-C2 (apply order, 4), LC-C3 (sentinel convention, 4), LC-C4 (capture
  tolerance, 4) — all routing to the already-open lifecycle family. I re-derived
  the cross-module premises: apply order gate -> validate -> probe -> install in
  all 4 `apply()` bodies (source-ordered AST walk), None-sentinel write + probe
  + validator reads in all 4 modules, 12 raises / 11 "Cannot apply" refusal
  sites. One nuance: django's capture fn (node 10) holds no `is None` itself
  (getattr-defaults style); W1's LC-C3 django accounting is nodes 6/16-tier-1/17,
  which is exact — the loose "captures" word in LC-C3's one-line summary does
  not move the count-4 conclusion. LC-C4's "replace-semantics" is spelled
  jointly by capture (recovery) + `apply()` (install); count stays 4 at module
  granularity either way.
- R-3 R1 trigger: W1's trigger ("discriminator keyed off `django.VERSION`")
  SUPERSEDES my vaguer "shared audited record type" — it names the concrete
  change that would unify the shapes. Adopted.
- R-4 Expected rejection (b) WITHDRAWN by me: W1 correctly treats wrap/unwrap as
  L2 (one predicate definition + two enforcement sites composing by name, the
  principle-6 healthy shape), not a rejected pair. No trigger is owed for a pair
  of definitions that does not exist. W1's treatment is the better analysis.
- R-5 Sweep-coverage gaps (immaterial, cured below): W1's `__func__` exclusion
  list omits `types/relay.py` (override/closure classification),
  `utils/typing.py:109` (staticmethod peel for async detection),
  `filters/sets.py:1044` (unbound hook call), and the `wrapped_func` exclusion
  omits `extensions/resource_policy.py:292` (same Strawberry-attr mechanism as
  the named schema/finalizer sites). I read each body: all disjoint contracts
  (relay emitter classification, callable introspection, filter rebuild,
  Strawberry resolver unwrap) — none is a second capture/install/probe site.
  The verdict-relevant claim stands; the enumeration was incomplete, not the
  conclusion. I supply the missing HEAD blobs under Freshness so a later move
  can still reopen mechanically.
- R-6 Missing excluded-module fingerprints (immaterial, cured below): W1
  fingerprinted routers/types-base/filters-sets but not types/definition,
  mutations/*, schema, finalizer (named exclusions) nor the R-5 sites. I
  re-verified every exclusion at HEAD bytes AND confirmed working-tree dirt
  touches none of the sweep-vocabulary lines in any of them, so each exclusion
  holds on both byte sets. HEAD blobs supplied below; the family item re-sweeps
  regardless. Not revision-worthy: no conclusion depends on an unverified byte.
- R-7 Lost probe (CONDITION 2 — re-derived, not downgraded): W1's replay path
  (`...-r2-w1/probe_upstream_shape.py`, 22/22) does not exist; no
  execution-verified claim is accepted on W1's word. I re-derived every
  probe-backed claim with two fresh probes under my scope (81 checks total,
  all PASS): `probe_w2_census.py` (47/47, configured Django: enumeration,
  stamp/install/validate censuses, 12/11 raise census, isinstance sweep,
  wrapped reads, installed-body match, live `_validate_upstream_shape()`
  return, installed-after-setup, predicate truth table, gate behavior,
  unvalidated-discriminator raise, oracle counts 25/9) and
  `probe_w2_upstream.py` (34/34, bare process without `django.setup()`:
  capture IS the live unstamped upstream descriptor, uninstalled pre-setup,
  body equals feature constant and differs from class constant, both pinned
  bodies carry the unwrap line, add-side unconditional wrap + `__all__` ->
  frozenset normalization + `addClassCleanup` teardown path, defined-on-
  SimpleTestCase-only, feature flag exactly the four documented pairs, toolbar
  7.1.1 precedent line verbatim, apply order x4, None-sentinel census x4).
  W1's P1-P6 map onto these 1:1 (P1 enumeration, P2 bare capture, P3 live
  validation + SET + unwrap line, P4 shape/hierarchy/pairs, P5 toolbar, P6
  predicate + pre-install split). The artifact's replay command is SUPERSEDED
  by these two probes; `execution-verified` is ENDORSED as re-derived-by-W2.
  `## Pending execution: None` stands — nothing is deferred.
- R-8 TREE.md "four cited lines": W1 does not quote which four; I verified
  `git diff bfaee91d..69a25369 -- docs/TREE.md` touches NO patch-related line,
  so any cited patch line is trivially byte-identical. Claim holds; citation
  precision immaterial (projection, cannot move a count).
- R-9 `tests/test_strawberry_patches.py` "named by role only": the file is named
  nowhere else in the artifact and never inspected; its HEAD-move diff removes
  one row on an unrelated surface. Immaterial either way.
- R-10 Sharded/Postgres: W1's "inapplicable by construction" reason (probe facts
  are pure import/source/shape; no connection opened; the flag-installing oracle
  loops all aliases so both modes construct identically) is SOUND — my probes
  likewise open no connection, and the oracle's alias loop is mode-generic by
  construction. Endorsed; no `proof:`/`gate:` entry owed.
- R-11 Defects: W1 records none with 9 ruled-out near-misses; I independently
  examined two further candidates and rule both out: (a) the
  `except ImportError -> None` pragma comment ("exercised via monkeypatch")
  reads as the tested-None-state rationale shared verbatim by all 4 patch
  modules — accurate on that reading, family-owned prose if anything, and no
  contract row + feasible shape + wire input exists per the trust-boundary
  rule; (b) the docstring's "5.2.16-6.0.x" range matches pyproject's
  `Django>=5.2.16` floor + 5.2/6.0/6.1 classifiers exactly. NO `## Defects`
  entries appended by Worker 2.
- R-12 Structural gates: W1 correctly owes lifecycle/wording gates (with
  negative-control shapes) to the family item and correctly owes none for the
  single-site L-rows, each with its fail-if-removed reasoning (L1 skip oracle,
  L3 closed-SET oracle, L4 reload/invariant oracles). The `isinstance(...)`
  sweep population recorded in L2 is the stated tripwire for a second spelling.
  Agreed in full.
- R-13 Matrix axes 2/4 inapplicability reasons: axis 2 (no `async def`, sync
  Django teardown verified in installed 6.1 source — I re-verified: both
  methods are sync classmethods) and axis 4 (install-once, revert is test
  scaffolding only; add side cannot AttributeError — I re-verified in
  installed source) are judged SOUND on their stated reasons. Axis 6 population
  (pairs/hierarchy/aliases/add-half/method-generality) matches my independent
  omission census with contract sources. No unsearched axis; the found
  routings excuse nothing (each axis searched independently).
- R-14 Index rows: 6 file-local + 1 rejected + 2 assignments to already-open
  rows, no new family — matches my Phase-A assignment exactly. Endorsed for
  Worker 0 transcription (Worker 0 edits the plan, not I).
- R-15 AGENTS.md prose on the diff: PASS. Citations use `path::Symbol`
  (`conf.py::upstream_patches_enabled`, `apps.py::ready`,
  `testing/_wrap.py::safe_wrap_connection_method`, installed
  `tracking.py::wrap_cursor`); the single `dry-0_0_11.md line 26` reference
  sits inside a `docs/dry/dry-*.md` artifact where raw lines are permitted;
  no process provenance (probe commands + HEAD-move paragraph are evidence /
  required freshness context, not provenance); no links emitted so the
  reference-style convention is vacuous; zero-edit so no test-tier, CHANGELOG,
  or commit questions arise.

### Freshness (re-hashed by Worker 2 at HEAD `69a25369`)

All 20 recorded fingerprints MATCH (`git rev-parse HEAD:<path>` for tracked,
`git hash-object` for installed): target `ba98f585...`, cross_web `6b3a7c35...`,
strawberry `f77df349...`, graphql_core `1cd579fb...`, conf `c6ad46aa...`, apps
`8ae1a3a3...`, test_django `e26a2609...`, test_apps `5ca8b62c...`, test_conf
`f35c7074...`, GLOSSARY `bc51debc...`, installed `testcases.py` `f866a339...`,
routers `a18c5001...`, types/base `91c58747...`, test_wrap `4d3c1351...`,
spec-024 `46335d7e...`, _wrap `0df97813...`, testing/__init__ `48b45d1b...`,
installed `tracking.py` `046b254a...`, installed `features.py` `9f00dcfc...`,
filters/sets `4ab65a26...` (full ids in the artifact body; each re-checked
byte-for-byte, zero mismatches). HEAD-move diligence confirmed: target blob
identical at `bfaee91d` and `69a25369`; TREE.md + strawberry-suite diffs move
no relied-upon byte (R-8/R-9).

Worker-2-supplied HEAD blobs for sweep-excluded modules (R-5/R-6; exclusions
re-verified at HEAD, dirt confirmed clear of all sweep lines):
`types/definition.py` `fa6c4d33...`, `types/relay.py` `52439862...`,
`utils/typing.py` `de6309f6...`, `types/finalizer.py` `77fd9a2d...`,
`schema.py` `c2e1b748...`, `extensions/resource_policy.py` `52084078...`,
`mutations/fields.py` `cf518361...`, `mutations/inputs.py` `fc442047...`,
`mutations/operations.py` `16223c6b...`, `mutations/permissions.py`
`54f770ae...`, `mutations/resolvers.py` `3fd1e571...`, `mutations/sets.py`
`cffa29e5...`.

### Scope, lint, tripwire

Item-scoped diff by content attribution (no ITEM_BASELINE recorded): the new
untracked artifact is the item's only product; the target is clean at HEAD;
no tracked hunk is item-authored (all other dirt is plan-ledgered DRY-adopted
or hunt-concurrent — left alone). My writes: this section + `Status:` below,
and ignored scratch under
`docs/dry/temp-tests/dry-file-_django_patches-r2-w2/` (3 files:
`phase_a_expectations.md`, `probe_w2_census.py`, `probe_w2_upstream.py`;
`ruff check` + `ruff format --check` both pass scoped to that dir). The broken
`inspect_django_type` module was never imported (condition 3). No pytest run:
every execution-backed claim is re-derived by the 81 probe checks; permanent
oracles are correctly typed `static-reviewed` (exist at HEAD, run at the gate)
and suite greenness is gate business, not item proof. HEAD never moved during
verification (`69a25369` at start and finish); no fingerprint went stale.

### Verdict

`verified`. Zero-edit file item: 24/24 members homed (lifecycle + wording
aspects to the two already-open families, six file-local rows, one rejection
with contract difference + trigger), all challenges confirmed at count
(LC x4, W 11-over-4, G/P/A/D/K/R x1), matrix discharged against the real
surface, no defects, no pending execution.

## Iterations

### Adjudication-1 (run 0.0.15 2026-09-21-3) — Worker 1 scoped re-review

Scope: 1 stale input of 20 (`docs/GLOSSARY.md`) + 2 moved W2-supplied
sweep-exclusion blobs (`schema.py`, `extensions/resource_policy.py`). No
production edits — a file-item adjudication owes none.

Baselines: `ITEM_BASELINE=706c7eed0163474e2e3b6dfc7db4fcca02b22184`
(resolves). HEAD `24e6b4d3e74b104779225cd6bbff713880bc48e3` at start and
finish (no move during this pass). Causing range `69a25369..24e6b4d3`;
per-path causing commits exactly `9350eb8d` + `44712901` (the other 9
range commits touch none of this item's inputs).

Append-only self-proof (artifact untracked): pre-edit `64733 B / sha256
8f2be39f5747db33ac5223b5ea3754dc4da32008ac1593f443b1540506323b47`; this
section appended at line 989; the sole other change is the `Status:` line
(`Status: verified` → `Status: ready-for-verification/adjudication-1`,
+31 bytes). W2 reconstructs via `sed '3s/.*/Status: verified/'
docs/dry/dry-file-_django_patches.md | head -c 64733 | shasum -a 256`
(must print the pre-edit sha256 above; self-verified by W1).

Full 20-table blind re-hash at HEAD bytes (`git rev-parse HEAD:<path>`;
`git hash-object` for installed): 19 MATCH, exactly the 1 tabled STALE,
zero unexpected. MATCH: target `ba98f585…`, cross_web `6b3a7c35…`,
strawberry `f77df349…`, graphql_core `1cd579fb…`, conf `c6ad46aa…`, apps
`8ae1a3a3…`, test_django `e26a2609…`, test_apps `5ca8b62c…`, test_conf
`f35c7074…`, installed testcases `f866a339…`, routers `a18c5001…`,
types/base `91c58747…`, test_wrap `4d3c1351…`, spec-024 `46335d7e…`,
_wrap `0df97813…`, testing/__init__ `48b45d1b…`, tracking `046b254a…`,
features `9f00dcfc…`, filters/sets `4ab65a26…`. STALE: GLOSSARY
`bc51debc→d3ef357c` (as tabled). W2-supplied exclusion re-hash (12): 10
MATCH (`types/definition.py` `fa6c4d33…`, `types/relay.py` `52439862…`,
`utils/typing.py` `de6309f6…`, `types/finalizer.py` `77fd9a2d…`, all six
`mutations/*.py` pins exact), exactly the 2 tabled STALE
(`schema.py` `c2e1b748→19f90bf5`, `ext/resource_policy.py`
`52084078→38801833`), zero unexpected. Installed Django 6.1 confirmed in
the worktree venv; all three installed blobs match.

Hunks examined (all pure substitution; line counts equal old/new: GLOSSARY
2230, schema.py 1319, ext/resource_policy.py 1435 — no line shifted, no
re-pin owed anywhere):

- GLOSSARY (`bc51debc→d3ef357c`, 5 hunks): `9350eb8d` ×4 — root-export
  policy bullets (`:24–35`), ErrorPolicy exact-type sentence (`:841`),
  masker-first-in-chain reorder (`:1127`), production-error-policy install
  wording (`:1574`); `44712901` ×1 — prefetch-alias-threading re-render
  (`:1558`). Zero changed lines carry patch vocabulary
  (`37064|_django_patches|upstream.patch|APPLY_UPSTREAM|safe_wrap|
  DatabaseFailure|TestCase|teardown`: 0 hits over `^[+-]` lines).
- schema.py (`c2e1b748→19f90bf5`, 3 hunks): pure
  `DEFAULT_*_POLICY`→`_PACKAGE_*_POLICY` renames (`:60`, `:72`, `:463`,
  `:1075`). No new read, no new line.
- ext/resource_policy.py (`52084078→38801833`, 2 hunks): the same rename
  (`:103`, `:1271`). No new read, no new line.

Per-finding verdicts (all CONFIRM):

- F1-assign: CONFIRM. Cited GLOSSARY projections (lifecycle/dispatch prose)
  are byte-identical: AppConfig entry `:538–545` md5 `2ead0d34…`,
  Upstream-patches entry `:2089–2102` md5 `fc764053…`, TOC/table/family
  rows `:77`/`:209`/`:228`/`:258` md5-identical. All 5 hunks sit in
  policy/prefetch entries disjoint from every cited span; projections
  cannot move the count-4 challenges either way.
- F2-assign: CONFIRM. Same projection basis (opt-out spellings); same
  identical spans as F1; node-18 invariant still hint-less inside the
  MATCH-blob target.
- L1: CONFIRM. "Django Trac #37064 hardening" entry `:2065–2078`
  md5-identical (`a77349b1…`); every L1-fingerprinted input MATCHes
  (GLOSSARY is a named projection there, pinned under F1/L6).
- L2/L3/L4/L5: CONFIRM by input identity — every fingerprinted input
  MATCHes; no finding cites a moved byte.
- L6: CONFIRM. Target docstring (MATCH blob) + GLOSSARY spans `:2065–2078`
  / `:2089–2102` / `:1786–1806` (safe_wrap entry md5 `7f2c8674…`) all
  byte-identical; line numbers unchanged.
- R1: CONFIRM by input identity (`filters/sets.py` MATCH).
- R-5/R-6 exclusions: CONFIRM. schema.py `wrapped_func` read
  (`_marked_mutation_class`, `:240`; docstring prose `:213`) inside span
  `:190–260` md5-identical (`9132553d…`); ext/resource_policy.py
  `_mutation_input_specs` (`:265`) `wrapped_func` read at `:288` inside
  span `:270–310` md5-identical (`ffdc6afb…`). Sweep census identical at
  both heads (schema `:213`+`:240`; ext `:288` only; zero
  `wrapped_cls`/`method.wrapped`/`_DatabaseFailure`/patch-vocab/`__func__`
  hits in either file at either head). Same Strawberry-attr mechanism,
  disjoint contracts (mutation-class/spec mapping vs patch
  capture/install/probe) — both exclusions hold as recorded. Citation
  precision note: W2's `:292` is the `return None` tail of the same
  `_mutation_input_specs` body at BOTH heads (the `wrapped_func` read
  itself is `:288` at both); nothing shifted, so no re-pin is owed — the
  precise pin `:288` is recorded here for the family item.
- Matrix axis 5 dispatch-order projection (`:542–544`) md5-identical
  (`0d1a3427…`).

Refreshed fingerprints (HEAD blobs): GLOSSARY
`d3ef357c26ede6a5bd21d4290b394ade4eb987b4` (F1/F2/L6); schema.py
`19f90bf55289d1ab31d5dc09236335e67037adc2`; ext/resource_policy.py
`388018335b94c5765bf6d7f92b2a22f41b6a9b40`.

Static-decidable, no scope: every cited projection span and every
exclusion body is byte-identical at HEAD, so any re-derived census
returns identical values by construction; W2's probes read no GLOSSARY
byte (0 hits in both probe files — read-only grep; prior scopes
`dry-file-_django_patches[-w1,-w2,-r2-w2]` untouched) and pin no moved
blob or line; the code diffs are pure identifier renames. No execution
could strengthen a byte-identity claim. No `docs/dry/temp-tests/` scope
created.

No defects found; `## Pending execution` still none. `Status:`
set to `ready-for-verification/adjudication-1` for fresh Worker-2
two-phase verification.

## Independent verification (Worker 2) — adjudication-1

### Phase A (blind record, pre-read)

Written to
`docs/dry/temp-tests/dry-adjud1-django-w2/phase_a_expectations.md`
BEFORE opening `## Iterations` (lines 990+). HEAD `24e6b4d3`
throughout. Every fact from `git show HEAD:` /
`git show 69a25369:` / `git rev-parse` / `git hash-object` (one
flagged worktree read, only to explain a line-number cite).
Condensed here; the scope file is the full record:

- Blind 20-table re-hash: 19 MATCH + 1 STALE ({GLOSSARY}
  `bc51debc…→d3ef357c…`); old pins exact in all 17 tracked rows;
  3 installed blobs (`testcases.py` `f866a339…`, `features.py`
  `9f00dcfc…`, `tracking.py` `046b254a…`, Django 6.1) all MATCH.
- Blind 12-blob exclusion re-hash: 10 MATCH + 2 STALE
  (`schema.py` `c2e1b748…→19f90bf5…`,
  `extensions/resource_policy.py` `52084078…→38801833…`); old
  8-char prefixes exact in all 12 rows.
- Causing-range hunks re-derived: GLOSSARY 5 hunks / 7 lines
  (`9350eb8d` x4 policy prose, `44712901` x1 prefetch prose);
  `schema.py` 4 hunks / 5 lines, all 1-for-1
  `DEFAULT_*→_PACKAGE_*` swaps; `ext/resource_policy.py` 2
  hunks / 2 lines, same swap. All pure substitution, zero line
  shift (GLOSSARY 2230 lines both heads).
- GLOSSARY expectation: CONFIRM + hash refresh, no re-pin —
  cited entries byte-identical at identical numbers
  (`:2065-2077` md5 `ff0812aa…`, `:1786-1805` md5 `449ea5d6…`,
  Upstream entry md5 `1c3c678f…`, all both-heads-equal).
- Exclusion expectation: CONFIRM holds + hash refresh —
  `schema.py:240` body `:236-241` and `ext/resource_policy.py`
  `:285-293` diff-identical old-vs-new; Strawberry
  `base_resolver.wrapped_func` mechanism, disjoint contracts;
  sweep vocabulary zero hits in both files at both heads;
  `wrapped_cls` zero hits package-wide. Line note recorded
  blind: the `:292` cite is the dirty-worktree number (HEAD
  bytes read `:288` at both heads; `:292` = `return None`
  tail) — expected W1 to repeat `:292` (erratum) or pin
  `:288` (HEAD-true).
- Static-decidable, no probes: byte comparison + body reads
  decide every claim; no behavior/ordering/async/database
  question in scope.
- Expected verdict: `verified` (plain), provided W1 shows the
  same 1+2 stale set, CONFIRM + refresh throughout, no missed
  mover, proved append-only, clean prose.

### Reconciliation (every difference)

- R-A1 Stale set: AGREE. My blind 1+2 (zero unexpected) is
  exactly W1's 19/1 + 10/2. No third mover on either side.
- R-A2 Hunk coverage: AGREE with two immaterial errata, both
  W1-side miscounts with complete coverage. (a) `schema.py`:
  W1 writes "3 hunks" but names all 4 sites
  (`:60`/`:72`/`:463`/`:1075`); mechanical count is 4
  (`grep -c "^@@"` = 4). Corrected to 4 here; no site
  unexamined. (b) GLOSSARY H1 span `:24-35` overshoots the
  mechanical hunk (`@@ -24,11` = lines 24-34) by one line;
  all 3 changed lines contained. Per-commit attribution
  (`9350eb8d` + `44712901`) agrees; ext/rp 2 hunks and
  GLOSSARY 5 hunks agree; W1's changed-line pins
  (`:841`/`:1127`/`:1558`/`:1574`) each land on the new-side
  changed line of the hunk I derived. Line counts 2230 /
  1319 / 1435 both heads re-verified.
- R-A3 F1/F2/L6 + matrix axis 5: AGREE (CONFIRM). Window
  boundaries differ by choice (W1 includes trailing blank
  lines: `:2065-2078` vs my `:2065-2077`, `:2089-2102`,
  `:1786-1806`), and every W1 window re-hashes
  both-heads-identical with a matching prefix
  (`2ead0d34…` `:538-545`, `fc764053…` `:2089-2102`,
  `a77349b1…` `:2065-2078`, `7f2c8674…` `:1786-1806`,
  `0d1a3427…` `:542-544`). TOC rows `:77`/`:209`/`:228`/`:258`
  md5-identical, re-verified. No re-pin owed — agree.
- R-A4 L1: AGREE (CONFIRM). Same entry, nested windows, both
  verified byte-identical.
- R-A5 L2/L3/L4/L5/R1: AGREE (CONFIRM by input identity).
  Every cited input MATCHes per my independent re-hash.
- R-A6 R-5/R-6 exclusions: AGREE (CONFIRM), including the
  citation-precision note — W1 independently derived the
  exact finding I predicted blind (`:292` is the
  `return None` tail at both heads; the read is `:288` at
  both; precise pin `:288` recorded, no shift so no re-pin
  owed). Bodies diff-identical; W1's spans `:190-260`
  (`9132553d…`) and `:270-310` (`ffdc6afb…`) re-verified
  both-heads-identical; sweep census agrees (schema
  `:213`+`:240`; ext `:288` only; zero `wrapped_cls` /
  `method.wrapped` / `_DatabaseFailure` / `__func__` hits
  in either file at either head — re-run). Same mechanism,
  disjoint contracts; both exclusions hold as recorded.
- R-A7 Hash agreement: all 3 refreshed full blobs
  character-identical — GLOSSARY
  `d3ef357c26ede6a5bd21d4290b394ade4eb987b4`, schema.py
  `19f90bf55289d1ab31d5dc09236335e67037adc2`,
  ext/resource_policy.py
  `388018335b94c5765bf6d7f92b2a22f41b6a9b40`.
- R-A8 Static-decidable + no W1 scope: AGREE. W1's probe-grep
  claim corroborated read-only (0 `GLOSSARY` hits and 0
  new-prefix hits in both run-2 probe files); prior-scope
  mtimes predate this pass (Sep 21 16:47-16:57); the only
  `temp-tests/` delta since Phase-A start is my own
  `dry-adjud1-django-w2/` scope. No execution could
  strengthen a byte-identity claim.
- R-A9 Append-only: PROVED. `sed '3s/.*/Status: verified/'` +
  `head -c 64733` reproduces W1's recorded
  `8f2be39f5747db33ac5223b5ea3754dc4da32008ac1593f443b1540506323b47`
  exactly. Item diff vs `ITEM_BASELINE=706c7eed` (resolves)
  is the untracked artifact only: W1's append + the +31-byte
  `Status:` swap, zero other bytes.
- R-A10 Prose rules on W1's hunks: PASS. Zero hits for
  `plan` / `audit` / `restored` / `previously` / `grader` /
  `feedback`; the 5 remaining hits are role labels
  (`Worker 1`, `Worker-2`), the item's own mechanism
  vocabulary (`sweep-exclusion`, `Sweep census`), and the
  GLOSSARY entry title (`Django Trac #37064 hardening`) —
  the same vocabulary the verified base uses throughout,
  not process narrative. Raw `:NN` cites sit inside a
  `docs/dry/dry-*.md` artifact where they are permitted.
  No `.py` touched by W1 or by this verification (artifact
  `.md` + one `.md` record file), so no `ruff` run is owed.
- R-A11 Defects / pending execution: AGREE — none found,
  still none. No `(Worker 2)` defect entries.

Deltas D1 (hunk numeral 3→4) and D2 (H1 span tail 35→34) are
record errata only: coverage was complete in both cases, no
conclusion depends on either numeral, and both are corrected in
this section. No `revision-needed` trigger exists: the stale set
is exact, every verdict is CONFIRM on byte-identical evidence,
hashes agree character-for-character, append-only is proved, and
prose is clean.

### Scope, tripwire, verdict

My writes: this section + the `Status:` line below, and the
ignored scratch record
`docs/dry/temp-tests/dry-adjud1-django-w2/phase_a_expectations.md`
(blindness record only; existing django scopes untouched).
HEAD `24e6b4d3` at Phase-A start and at finish — tripwire
holds. `ITEM_BASELINE=706c7eed` resolves; baseline-window other
paths (bug_hunt, plan) are Worker-0/hunt bytes outside item
scope. No production/test file touched; the broken
`inspect_django_type` module was never imported; no pytest run
(static-decidable pass).

`verified`. Adjudication-1 closes: GLOSSARY projections CONFIRM
+ re-pinned to `d3ef357c…` with zero line movement, R-5/R-6
exclusions CONFIRM + re-pinned to `19f90bf5…` / `38801833…`
with diff-identical bodies, all other inputs MATCH. No index,
ledger, or family change owed.
