# DRY review: `django_strawberry_framework/__init__.py`

Status: verified
Run: 0.0.15 2026-09-21-2

File item. No production edits owed; the trace below proves single ownership for
every rule the target defines or enforces, so this is a zero-edit result. No new
families are named (no holding Family item is owed); seven file-local rows and four
rejections are carried in `## Index rows for Worker 0` for the plan's
`## Responsibility index`. Worker 0 never needs to edit the plan on my behalf beyond
adding those rows.

## System trace

The target is the package's public surface file: 38 eager re-exported names admitted
by 16 subpackage import blocks plus strawberry's `auto`, published through a
39-entry `__all__` (the 39th member, `__version__`, is defined in-target); the
single-sourced release literal; the canonical package logger; and a 7-name DRF
lazy-export table resolved by a PEP 562 `__getattr__` through the shared
`rest_framework.require_drf()` guard. It defines no resolver, execution, async, or
serialization logic of its own: every re-exported name is owned by its subpackage,
and the root's rules are membership (what is public), the version string, the logger
identity, the lazy-export routing, and three import-hygiene absences enforced by
omission.

Sites found, by role:

- Definitions in-target: `__all__` + 16 import blocks + `auto` import (surface
  membership); `__version__`; `logger`; `_DRF_SOFT_EXPORTS` + `__getattr__`;
  the debug-exclusion and logger-first comments (enforced by position/omission).
- Consumer (re-export chain, not definitions): `SyncMisuseError` reaches the root
  via `types/__init__.py` <- `types/relay.py` (redundant-alias form) <-
  `utils/querysets.py` (the single `class` definition); `permissions.py` carries a
  second redundant-alias re-export for its own dotted path. The querysets item's
  file-local row for the marker stands; the root adds no definition.
- Consumers of the surface: every `from django_strawberry_framework import ...`
  site (the `tests/` tree broadly; every fakeshop schema, e.g.
  `examples/fakeshop/config/schema.py`, the library/products/kanban/scalars/accounts
  schemas; `TODAY.md` examples). Submodule-fallback imports (`conf`,
  `_strawberry_patches`, `_django_patches`, `_cross_web_patches`) resolve through
  the import system, not through any root attribute, and are unaffected by `__all__`.
- Consumers of `logger` (9 production import sites, all by the name `logger`, never
  the string): `optimizer/__init__.py` (re-export; fanned out to `extension.py`,
  `walker.py`, `nested_planner.py`, `single_parent_fetch.py` via `from . import
  logger`), `types/finalizer.py`, `types/resolvers.py` (as `_resolver_logger`),
  `consumers.py`, `extensions/error_policy.py`, `extensions/debug.py`,
  `_request_body.py`, `schema.py`. Tests derive the name from the object
  (`caplog.set_level("DEBUG", logger=logger.name)`); only the oracle spells it.
- Consumers of `__version__`: hatchling (`[tool.hatch.version]` path pointer),
  `docs/dry/export_dry_review.py` (`VERSION_PATTERN`, double-quote spelling) and
  `scripts/bug_hunt.py` (`_INIT_VERSION_PATTERN`, either quote) — both read the one
  literal; format coupling, not second definitions.
- Oracles: `tests/base/test_init.py` (version pin, logger-name pin, optimizer
  re-export identity, exact `__all__` pin, 3 + 13 re-export identity pins,
  lazy-resolution, non-memoization, miss-AttributeError, star hygiene, orders
  absence); `tests/rest_framework/test_soft_dependency.py` (fresh-process DRF-absent
  import, per-name hint, package/sets import hints, star DRF-free, miss
  AttributeError, per-name non-memoization, `-> Any` annotation pin);
  `tests/middleware/test_debug_toolbar.py` (star binds no toolbar name).
- Projections: CHANGELOG surface bullets, per-spec surface lists, the KANBAN
  rule-31 dissolution note, the GLOSSARY `Current package version` line and
  soft-dependency entries, `uv.lock`'s root entry, module docstrings restating
  promotion/omission rationale.

Connected behavior examined: all 14 sibling `__init__.py` files (every export,
omission, and `__all__` polarity in the package); `routers.py`'s PEP 562 hook (the
only twin); `utils/imports.py::require_optional_module` (the guard primitive);
`rest_framework/__init__.py::require_drf` (the guard the root routes through);
`types/relay.py` + `permissions.py` redundant-alias re-exports; `scalars.py::Upload`
and `filters::Filter` (upstream pass-through twins); `apps.py::name` (the only other
in-code spelling of the package-name string); the eager-import census (P1: 67
modules; orders/filters/auth/testing/rest_framework absent; `extensions.debug`
present via the `extensions` package init); prior-cycle trigger check (the
querysets artifact's four rejections touch no root definition; its SyncMisuseError
file-local row is consistent with the chain traced here; the earlier
`docs/dry/temp-tests/dry-file-__init__/` scope is empty — no trigger inputs exist).

No scratch directory was created: every probe was a read-only inline command (no
file-based experiment was needed), each recorded below with its status. No
source-mutating proof was run. Tree state at probe time: HEAD `bfaee91d` with 110
dirty concurrent paths (26 under the package); the target and all oracle files are
clean, and every cited line inside a dirty file was verified intact against its
hunk list before being relied on (dirty inputs are fingerprinted by working-tree
hash with a `WORK` tag below).

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. Read all 14 sibling `__init__.py`
   files end to end. Each owns a distinct surface contract, not a mirror of the
   root's: filters/orders add Decision-11 helpers + helper-reference ledgers;
   types is a dotted-path convenience re-export; utils pins 7 of many names;
   testing keeps relay helpers dotted-path-only for import weight; auth is a
   structural opt-in (spec-040 Decision 3); middleware/management carry no
   `__all__` at all; extensions documents the root-exclusion rationale from the
   other side. Container shape differs cosmetically (tuple vs list) with no
   behavioral rule attached — change challenge (retuple one `__all__`) moves one
   file, so no family. The sharpest non-mirror: `routers.py::__all__` INCLUDES
   its lazy name (star import opts into the channels guard) while the root
   EXCLUDES its 7 (star stays DRF-free) — opposite polarity by opposite contract
   (R2). No mirrored policy needs consolidation.
2. Sync/async twins — INAPPLICABLE, with the reason stated. The target defines no
   async surface, no await boundary, and no execution code; its one function is a
   synchronous import hook. The `apply_cascade_permissions` /
   `aapply_cascade_permissions` pair is re-exported as two names but twinned in
   `permissions.py`, not here — the root holds no twin logic to drift.
3. Derived rather than repeated knowledge — SEARCHED, two candidates considered.
   (a) The logger-name literal vs `__name__`: rejected (F3) — the LOGGING key is
   a consumer-visible contract that must be spelled somewhere (config keys are
   strings), while `__name__` equality is incidental; deriving would couple a
   wire-visible key to module identity. (b) `__all__` (39 strings) vs the import
   blocks: the tuple IS the membership definition, not a derivation — P3 proves
   mechanically that every import is a member and the only non-imported member
   is the in-target `__version__`. The test's 39-tuple is an oracle and must
   spell the strings to catch drift. No duplicated fact found.
4. Inverse / round-trip pairs — INAPPLICABLE in the encode/decode sense: the
   target has no serialization, pack/unpack, or build/parse pair. The nearest
   shape, import-vs-star-binding, is pinned in both directions by
   `test_star_import_preserves_namespace_hygiene` (every `__all__` member binds;
   soft names, `_DRF_SOFT_EXPORTS`, and `__getattr__` do not), and the
   `__getattr__` miss arm has no inverse by construction (a miss raises; nothing
   round-trips).
5. Contracts restated in another medium — SEARCHED. Every restatement is
   classified in the findings: oracles (the three test modules above),
   projections (CHANGELOG, specs, KANBAN note, GLOSSARY lines, `uv.lock` root
   entry, docstrings), consumers (hatchling pointer, planner/bug-hunt readers,
   example/test import sites). No second authoritative definition exists in any
   medium: nothing besides the target constructs the surface, the version, the
   logger, or the lazy table (the `scripts/` + package `__all__` census finds no
   surface-constructing reader; `_DRF_SOFT_EXPORTS` readers are the hook itself
   plus tests that derive from it by `tuple(...)`).
6. Enforcement by omission — SEARCHED by census. P1 plus contract-source review
   over every omitted member: `DjangoDebugExtension` (established: root comment
   + `extensions/__init__.py` rationale — F6); `orders` absence (established:
   oracle pin, added by spec-050 against the list_field `orderBy` leak — F7);
   `rest_framework` absence (established: fresh-subprocess oracle — F7); `auth`
   absence (established: owner prose citing spec-040 Decision 3 — F7);
   `filters`/`testing`/`middleware`/`management` absence (incidental: no spec
   decision, no pin; the `filters/sets.py` "does NOT import" line is a
   descriptive premise, not a normative contract — therefore not rules, no
   rows). `logger` and the 7 lazy names are importable-but-not-in-`__all__` by
   stated contract (F3/F4). No guard-missing member with a contract source was
   found, so no axis-6 defect is owed.

### Enumeration

Instrument: every statement in `ast.Module.body` of
`django_strawberry_framework/__init__.py` at HEAD blob
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`, indices 0-24. Count: 25.

| # | Statement | Disposition |
|---|---|---|
| 0 | Module docstring | Projection of F1 (folds into the surface row) |
| 1 | `import logging` | Support import for F3 (folds into the logger row) |
| 2 | `from typing import Any` | Support import for F5/R3 (folds into the hook rows) |
| 3 | `logger = logging.getLogger(...)` + comment | F3 file-local |
| 4 | `from strawberry import auto` + comment | R1 rejection (auto vs Filter vs Upload) |
| 5-20 | 16 re-export `ImportFrom` blocks | F1 file-local (one rule: eager surface admission) |
| 21 | `__version__ = "0.0.15"` + comment | F2 file-local |
| 22 | `_DRF_SOFT_EXPORTS` table + comment | F4 file-local |
| 23 | `def __getattr__` + docstring | F5 file-local (routing/non-memoization/miss) + R2/R3/R4 rejections (hook twin, `-> Any` idiom, miss message) |
| 24 | `__all__ = (...)` (39 entries) | F1 file-local (membership publication) |
| — | Debug-exclusion comment (60-61) | F6 file-local (omission enforced by absence) |
| — | Import-hygiene absences (orders/rest_framework/auth, enforced by the graph of 5-20) | F7 file-local |
| — | `# noqa: E402` markers (16x) | Import mechanics, not a rule: ruff requires one per line; no abstraction exists |

Every member lands in a file-local row (F1-F7) or a rejection (R1-R4). Zero
members need a holding family.

### Challenges

Each rule's real variation axes, with the authoritative-definition count per
posited change (consumers/oracles/projections listed in the findings, never
counted). Sharded/PG cells are inapplicable by construction for every row: the
target's code path reaches no database, alias, or dialect decision (Worker 2
judges).

| Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|
| F1 surface | Add a public name | 1 (import block + `__all__`, one edit) | single-owned |
| F1 surface | Remove / rename a public name | 1 (target only; oracle fails until updated as oracle) | single-owned |
| F1 surface | Reorder `__all__` | 1 (no second order definition; pin is the oracle) | single-owned |
| F2 version | Bump the value | 1 (`__version__`; test pin = oracle, GLOSSARY/lock = projections) | single-owned |
| F2 version | Reformat (quotes/spacing) | 1 (planner needs `"`; bug_hunt tolerates both; both read the one literal) | single-owned |
| F2 version | Add a new version reader | 0 (readers compose; nothing defined moves) | single-owned |
| F3 logger | Rename the LOGGING key | 1 (line 14; all consumers bind the name `logger`) | single-owned |
| F3 logger | Derive from `__name__` | — (rejected: wire key vs module identity are different contracts) | independent |
| F3 logger | Move below the subpackage imports | 1 (breaks `from . import logger` consumers; the fix is here alone) | single-owned |
| F4 lazy table | Add / retire / retarget a lazy name | 1 each (the table; oracles derive via `tuple(...)`) | single-owned |
| F5 hook | Memoize resolutions into globals | 1 (root only; breaks the eviction discipline by design) | single-owned |
| F5 hook | Change the miss error shape | 1 (root only; routers unaffected) | single-owned |
| F5 hook | Route through a different guard | 1 (root lines 121-123; the guard's own text lives in `rest_framework/__init__.py`) | consumer, not second def |
| F6 debug omission | Promote `DjangoDebugExtension` to root | 1 (root import + `__all__`; single axis — membership is binary) | single-owned |
| F7 hygiene | Eagerly import orders / rest_framework / auth | 1 each (the edge lands in one site; oracles/Decision 3 fail until then) | single-owned |
| R1 pass-through | Change auto's / Filter's / Upload's source | 1 each, never the same 1 | independent |
| R2 hooks | Customize root's miss message | 1 (routers unaffected) | independent |
| R2 hooks | Add a second lazy name to routers | 1 (routers only; root table unaffected) | independent |
| R2 hooks | Unify dispatch in one shared table | — (rejected: opposite memoization + `__all__` polarity; see trigger) | independent |
| R3 `-> Any` | Narrow root's hook to `-> type` | 1 (breaks the root oracle; routers unaffected; no third axis exists) | independent |
| R3 `-> Any` | Narrow routers' hook | 1 (root unaffected) | independent |
| R4 miss message | Customize either hook's message | 1 each (each mirrors the interpreter today) | independent |

Probes (all read-only, replayable; tree state as noted in System trace):

- P0 AST enumeration: `uv run python - <<'PY'` (`ast.parse`, dump
  `ast.Module.body`) → 25 statements, indices 0-24. `execution-verified`.
- P1 eager-import census: `uv run python -c "import sys,
  django_strawberry_framework as p; ..."` → 67 modules; orders/filters/auth/
  testing/rest_framework absent; `extensions.debug` present (via the
  `extensions` package init, which the root's `extensions.*` imports execute).
  `execution-verified`.
- P2 surface probe: `uv run python -c` → `len(__all__) == 39`; tuple is not
  plain-`sorted()` (constants, then classes, then lowercase, alphabetical
  within — convention, order pinned by the oracle); all 7 lazy names resolve
  (`SerializerMutation`, `SerializerFieldConversion`, `NestedSerializerConfig`,
  `SerializerHookContext`, `UploadMetadata` are classes; the two converters are
  functions); logger inherits the root level (no handler/level set).
  `execution-verified`.
- P3 bindings-vs-pin check: `uv run python - <<'PY'` (AST on target +
  `tests/base/test_init.py`) → 38 imported names, every one in `__all__`; the
  only non-imported `__all__` member is `__version__`; the pinned 39-tuple
  equals the target tuple as a sequence. `execution-verified`.
- S1 `getLogger` census (package): exactly 1 call site (target line 14).
  `static-reviewed`.
- S2 module-`__getattr__` census (package): exactly 2 (target line 98,
  `routers.py` line 565); the `conf.py` / `consumers.py` / `utils/permissions.py`
  hooks are class-level (different mechanism). `static-reviewed`.
- S3 `"django_strawberry_framework"` string census (package): in-code
  occurrences are the logger call and `apps.py::name` only (rest are comments).
  `static-reviewed`.
- S4 `import logger` census: 9 production import sites, all by name; optimizer
  re-export fans out to 4 siblings. `static-reviewed`.
- S5 `_DRF_SOFT_EXPORTS` readers: the hook + tests deriving via `tuple(...)` +
  spec prose. No mutation site. `static-reviewed`.
- S6 `__all__` census over `scripts/` + package: no surface-constructing reader
  (only `review_inspect.py`'s AST-strip docstring mention). `static-reviewed`.

## Findings

Seven file-local confirmations (F1-F7) and four rejections (R1-R4). No finding
consolidates anything: each records a single owner that stands, or a separation
that holds. Fingerprint prefixes below are 12 hex chars; `HEAD` = `git rev-parse
HEAD:<path>`, `WORK` = `git hash-object <path>` for the 110-path concurrent dirt
(the cited lines in every `WORK` file were verified intact against its hunk list).

### F1 — Package-root eager export surface (file-local)

- Contract + variation: the root admits exactly 38 eager public names (37 from
  16 subpackage import blocks + strawberry's `auto`) and publishes them through
  `__all__` (39 entries with `__version__`); the surface widens only via a spec.
  Varies on membership, spelling, and order.
- Sites + roles: definition = target lines 16-58 (imports) + 129-169 (`__all__`).
  Consumers = every `from django_strawberry_framework import ...` site (tests/
  broadly; fakeshop schemas; `TODAY.md`). Oracles =
  `tests/base/test_init.py::test_public_api_surface_is_pinned` (exact tuple),
  `::test_reexported_types_resolve_to_canonical_subpackage_definitions` (13
  identities), `::test_file_upload_exports_resolve_to_their_source_definitions`
  (3 identities), `::test_star_import_preserves_namespace_hygiene`;
  `tests/middleware/test_debug_toolbar.py` (star binds no toolbar name).
  Projections = CHANGELOG surface bullets, per-spec surface lists, the KANBAN
  rule-31 note, subpackage docstrings restating promotion ("backs the public
  re-exports").
- Challenges: add / remove-or-rename / reorder — each forces exactly 1
  definition (the target; the pin moves as oracle). Second-site candidates
  disproved: the sibling `__all__`s (10 of the 14 subpackage inits carry one;
  middleware/management/commands/rest_framework carry none) each define a
  different membership
  contract (sharpest: `routers.py` includes its lazy name while the root
  excludes its 7 — opposite polarity, opposite reasons); no script or package
  module constructs the surface (S6); the test tuple is an oracle by role.
- Owner + lifetime: target `__all__` + import block. Published at import as an
  immutable tuple; valid for the process lifetime; no append/extend site exists
  in the package or scripts census. Consumers compose by name.
- Migration: none — single owner stands.
- Distinct behavior: submodule dotted-path surfaces stay separate (each keeps its
  own `__all__`-or-nothing contract); star import binds exactly `__all__`.
- Behavioral proof: P0 (16 ImportFrom + auto + 39-tuple) `execution-verified`;
  P2 (count 39) `execution-verified`; P3 (bindings-vs-`__all__` vs pin,
  sequence-equal) `execution-verified`. Oracle green-ness itself was not
  re-executed (no suite run needed for a structural verdict; CI owns it).
- Structural gate + negative control: the exact-tuple pin — equality rejects any
  addition, removal, rename, or reorder. Negative control is analytic: the
  bypass it guards (a second surface-constructing site) does not exist per S6,
  so there is no hand-copy control to construct; any drift fails `==`.
  `static-reviewed`.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `tests/base/test_init.py` `HEAD
  4cc121057689`; `tests/middleware/test_debug_toolbar.py` `HEAD dd6df61673fb`;
  all 14 sibling `__init__.py` files `HEAD` (rest_framework `45cf7b63a2b7`,
  optimizer `d400569adf8b`, extensions `dc3ebdc24b48`, utils `1a4c2ec8bfd3`,
  testing `48b45d1b4332`, types `24e8ec204a78`, filters `86b258186638`,
  orders `ed546f9c70d5`, forms `a76a4f797414`, mutations `9a5683e91457`, auth
  `6bc3c4a5eb96`, middleware `6e1b64ca7b93`, management `beb4e0ee66a2`,
  commands `31cb58b85817`); `routers.py` `WORK d5c4350911f6` (cited lines
  intact); `mutations/permissions.py` `HEAD 54f770ae5aa1` (widens-only-via-spec
  contract); `examples/fakeshop/config/schema.py` `HEAD 303ea2da9df1`;
  `TODAY.md` `HEAD 9c6786222a74`; CHANGELOG `HEAD d4e1035554f1`; searched
  populations S6 + the `from django_strawberry_framework import` census.

### F2 — Single-sourced release literal (file-local)

- Contract + variation: `__version__ = "0.0.15"` is the one release literal;
  hatchling derives packaging metadata from it (`dynamic = ["version"]`, no
  `[project].version`). Varies on value only (format is coupled to readers).
- Sites + roles: definition = target line 66. Consumers = hatchling
  (`[tool.hatch.version]` path pointer in `pyproject.toml`),
  `export_dry_review.py::VERSION_PATTERN` (requires `"`), `scripts/bug_hunt.py`
  (`_INIT_VERSION_PATTERN`, either quote) — all read the one literal. Oracle =
  `test_version` (spells the literal, as an oracle must). Projections = GLOSSARY
  `Current package version` line, `uv.lock` root entry, CHANGELOG release notes.
  A version bump moves production + oracle + projections together, which per
  DRY vocabulary is an intentional contract change, not duplication.
- Challenges: bump value → 1; reformat quotes/spacing → 1 (readers tolerate or
  fail loud on the one spelling — no second spelling to sync); add a reader → 0
  (readers compose). No second version literal exists anywhere in the repo.
- Owner + lifetime: target line 66. Import-time constant; never mutated (no
  write site in any census); validity = the release.
- Migration: none.
- Distinct behavior: the KANBAN rule-31 note already dissolves the gate
  question — no parity gate is owed because no second literal exists.
- Behavioral proof: P0 (Assign `__version__`) `execution-verified`; reader
  bodies read (`VERSION_PATTERN`, `_INIT_VERSION_PATTERN`, hatch table) and
  confirmed single-source consumers. `static-reviewed`.
- Structural gate + negative control: `test_version` equality pin — any literal
  drift fails it. No bypass site exists (S6 + the no-second-literal census).
  `static-reviewed`.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `pyproject.toml` `HEAD 9be864937662`;
  `uv.lock` `HEAD 6e8552ad5074`; `tests/base/test_init.py` `HEAD 4cc121057689`;
  `docs/dry/export_dry_review.py` `HEAD 83e969d9c8e5`; `scripts/bug_hunt.py`
  `HEAD 14e39585a2f6`; `docs/GLOSSARY.md` `HEAD bc51debc54cf`; CHANGELOG `HEAD
  d4e1035554f1`.

### F3 — Canonical package logger (file-local)

- Contract + variation: `logger = logging.getLogger("django_strawberry_framework")`
  is the one framework-wide logger; the name is the consumer-visible LOGGING key
  (public surface though absent from `__all__`); the binding precedes all
  subpackage imports. Varies on the key string only.
- Sites + roles: definition = target line 14 (+ first-position order). Consumers
  = the 9 production import sites (S4), all binding the name `logger`; the
  optimizer re-export fans out to 4 siblings. Oracles =
  `test_logger_name_is_django_strawberry_framework` (spells the key),
  `test_optimizer_subpackage_reexports_top_level_logger` (identity). No consumer
  spells the string: tests derive `logger.name`; no in-tree LOGGING dict exists.
- Challenges: rename the key → 1 (line 14; every consumer binds by name).
  Derive from `__name__` → rejected, not counted: a wire-visible config key and
  module identity are different contracts (a rename must be able to move one
  without the other). Move below the imports → the breakage is loud
  (`from . import logger` at consumer import time) and the fix is 1 site (here).
  Second-token candidate disproved: `apps.py::name` spells the same characters
  but is Django's required dotted app path — posit a LOGGING-key rename and it
  does not move (count 1 → independence, even with identical text).
- Owner + lifetime: target line 14. Published at import before any subpackage
  import; plain `Logger` (P2: inherits root level, no handler); never mutated
  by the package.
- Migration: none.
- Distinct behavior: the `not in __all__` status is contractual (star import
  must not bind the logger); the optimizer re-export is the sanctioned
  intra-subpackage handle per its docstring.
- Behavioral proof: P2 (level inheritance) `execution-verified`; S1 (exactly 1
  `getLogger` call package-wide) + S3 (only other in-code spelling is
  `apps.py::name`) + S4 (9 by-name import sites) `static-reviewed`.
- Structural gate + negative control: the name pin + the identity pin — a rename
  fails the first, a second `getLogger` call fails the second. Bypass (a second
  call) does not exist per S1. `static-reviewed`.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `tests/base/test_init.py` `HEAD
  4cc121057689`; `tests/optimizer/test_walker.py` `HEAD 5bbd7a567f04`;
  `django_strawberry_framework/apps.py` `HEAD 8ae1a3a3b12f`; consumers:
  `optimizer/__init__.py` `HEAD d400569adf8b`, `optimizer/extension.py` `HEAD
  49667a9370ce`, `optimizer/walker.py` `HEAD 9b111ed93895`,
  `optimizer/nested_planner.py` `WORK e69dbf5f30aa4` (line 48 intact),
  `optimizer/single_parent_fetch.py` `HEAD e995270af9b2`, `types/finalizer.py`
  `WORK 35ff5286683b` (line 63 intact), `types/resolvers.py` `HEAD f3341e6a9f52`,
  `consumers.py` `HEAD 936210e2993d`, `extensions/error_policy.py` `HEAD
  16f475471a8b`, `extensions/debug.py` `HEAD bf25c1461113`, `schema.py` `HEAD
  c2e1b748c26c`, `_request_body.py` `HEAD a70571ff5b38`; censuses S1/S3/S4.

### F4 — DRF lazy-export name table (file-local)

- Contract + variation: `_DRF_SOFT_EXPORTS` maps 7 public names to
  `(submodule, attr)` targets; all 7 stay out of `__all__` so star import stays
  DRF-free (spec-039 Decision 12). Varies on membership and per-name target.
- Sites + roles: definition = target lines 78-95. Its only production reader is
  the hook (F5). Oracles derive from it by `tuple(...)` (composition by name,
  never restated): the per-name hint/non-memoize parametrizations and the
  star-DRF-free assertions; plus `test_dynamic_drf_soft_exports_via_getattr`
  (resolution) in `tests/base/test_init.py`. Projections = spec-039 prose,
  CHANGELOG's lazy-export bullet.
- Challenges: add / retire / retarget a lazy name → 1 each (the table row; the
  hook body is unchanged — it is table-driven). No second enumeration of the 7
  exists (S5).
- Owner + lifetime: target lines 78-95. Import-time constant table; read by the
  hook and the oracles; no mutation site in any census.
- Migration: none.
- Distinct behavior: the table holds names, not objects — resolution (guard +
  import) is the hook's job (F5), so the table never imports DRF itself.
- Behavioral proof: P2 (all 7 resolve to the tabled kinds: 5 classes, 2
  functions) `execution-verified`; S5 (readers = hook + deriving tests; no
  mutation) `static-reviewed`.
- Structural gate + negative control: the `tuple(_DRF_SOFT_EXPORTS)`-derived
  parametrizations — adding a name auto-extends the hint and non-memoization
  coverage, so a table edit cannot silently escape the oracles; retargeting to
  a wrong attr fails resolution. `static-reviewed`.
- Coupling: none (F5 consumes this table by name; no shared edit needed).
- Freshness: target `HEAD 0ef72601ecac`;
  `tests/rest_framework/test_soft_dependency.py` `HEAD ac2b38ae04f0`;
  `tests/base/test_init.py` `HEAD 4cc121057689`; `tests/_soft_dependency.py`
  `HEAD 7b28c07853d1`; spec-039 `HEAD cf78af93437b`; census S5.

### F5 — DRF lazy-export hook behavior (file-local)

- Contract + variation: `__getattr__` resolves tabled names through
  `require_drf()` (install-hint `ImportError` when DRF is absent), never
  memoizes into globals (each access re-fires the guard for eviction tests),
  and raises the normal `AttributeError` for anything else (spec-039 Decision
  12). Varies on guard routing, memoization, and miss behavior.
- Sites + roles: definition = target lines 98-126. The guard itself is defined
  in `rest_framework/__init__.py::require_drf` (thin wrapper over
  `utils/imports.py::require_optional_module`); the root is its consumer (one
  call), not a second guard definition. Oracles = the soft-dependency suite
  (per-name hint, non-memoization, miss-AttributeError, fresh-subprocess
  import) + the base init's `__getattr__` tests. The twin hook in `routers.py`
  is a different contract — see R2 (rejection), not a second site of this rule.
- Challenges: memoize into globals → 1 (root only; breaks the eviction
  discipline by design). Change the miss error shape → 1 (root only; routers
  unaffected). Route through a different guard → 1 (root lines 121-123); the
  guard's own text moves only in `rest_framework/__init__.py`.
- Owner + lifetime: target lines 98-126. Stateless function; no stored
  derivation (non-memoization is the point — principle 4 "not cached", stated
  in the docstring).
- Migration: none.
- Distinct behavior: guard ownership stays in `rest_framework/__init__.py`
  (its file item owns any guard-consolidation question); the root owns routing
  only. Miss passthrough preserves normal Python semantics for typos.
- Behavioral proof: P2 (7 resolutions + 2 function kinds, feeding the `-> Any`
  pin) `execution-verified`; hook body + guard delegation read end to end.
  `static-reviewed`.
- Structural gate + negative control: per-name hint + non-memoization +
  miss-AttributeError oracles — memoizing fails the `vars()` assertion, a wrong
  guard fails the hint match, swallowing misses fails the `AttributeError`
  assertions. `static-reviewed`.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`;
  `rest_framework/__init__.py` `HEAD 45cf7b63a2b7`; `utils/imports.py` `HEAD
  291ecedd30c7`; `tests/rest_framework/test_soft_dependency.py` `HEAD
  ac2b38ae04f0`; `tests/base/test_init.py` `HEAD 4cc121057689`; spec-039 `HEAD
  cf78af93437b`.

### F6 — Debug-extension root exclusion (file-local)

- Contract + variation: `DjangoDebugExtension` is deliberately NOT root-exported;
  its public opt-in remains `django_strawberry_framework.extensions`. Binary
  membership — no further axes.
- Sites + roles: enforcement = the root's omission (comment lines 60-61 names
  the decision at the site). The `extensions/__init__.py` rationale (always-on
  recipe vs opt-in) is the describing projection; absence from `__all__` is
  pinned by the exact-tuple oracle. Note the exclusion is namespace hygiene,
  not import cost: P1 shows `extensions.debug` IS eagerly imported (the root's
  `extensions.*` imports execute the `extensions` package init) — only the root
  NAME is withheld.
- Challenges: promote to root → 1 site (root import + `__all__`; the extensions
  side already exports it). No other change moves this rule.
- Owner + lifetime: the root import block (by omission), documented at target
  lines 60-61. No stored state.
- Migration: none.
- Distinct behavior: the two always-on extensions (`DjangoErrorPolicyExtension`,
  `DjangoResourcePolicyExtension`) ARE root-exported because `DjangoSchema`
  installs them on every schema — the opposite case, recorded in the same
  extensions docstring, stays as is.
- Behavioral proof: P1 (`extensions.debug` imported, name absent from root
  namespace — the star-hygiene oracle asserts the `__all__` half)
  `execution-verified`; both rationale texts read. `static-reviewed`.
- Structural gate + negative control: the exact-tuple pin rejects any
  promotion-sans-spec. `static-reviewed`.
- Coupling: none. (The in-flight spec-052 debug-extraction card may move the
  debug surface; this finding records the rule as it stands at the
  fingerprints below — any 052 edit reopens it by freshness, not by verdict.)
- Freshness: target `HEAD 0ef72601ecac`; `extensions/__init__.py` `HEAD
  dc3ebdc24b48`; `extensions/debug.py` `HEAD bf25c1461113`;
  `tests/base/test_init.py` `HEAD 4cc121057689`.

### F7 — Root import-hygiene absences (file-local)

- Contract + variation: `import django_strawberry_framework` pulls neither
  `orders` (oracle-pinned; spec-050 guards the list_field `orderBy` leak),
  nor `rest_framework` (fresh-subprocess oracle; DRF stays soft), nor `auth`
  (owner prose citing spec-040 Decision 3: opt-in is structural so non-auth
  consumers never pay the `django.contrib.auth` import). Each absence varies
  only on its own edge — three binary rules, one row.
- Sites + roles: enforcement = the import graph of the 16 blocks (absence of
  any edge). Oracles = `test_orders_submodule_not_imported_at_package_root`
  (subprocess) and the fresh-process DRF-absent test; `auth` rests on owner
  prose + Decision 3 (established, unpinned — the absence of a pin is not a
  defect). `filters`/`testing`/`middleware`/`management` absences are
  incidental (no decision, no pin) and therefore not rules — no rows.
- Challenges: land an eager edge to any of the three → 1 site (wherever the
  edge lands); the oracle/Decision fails until the edge is removed. Each
  absence moves independently of the others.
- Owner + lifetime: the root import graph (target lines 16-58). Import-time
  property; no stored state.
- Migration: none.
- Distinct behavior: incidental absences (filters/testing/...) stay incidental —
  a future edge there breaks no contract and owes no row until a decision or
  pin establishes one.
- Behavioral proof: P1 (all three absent from `sys.modules` after root import
  on the working tree) `execution-verified`. `auth/__init__.py` docstring read.
  `static-reviewed`.
- Structural gate + negative control: the two subprocess oracles — either edge
  fails its `not in sys.modules` assertion in a fresh interpreter (re-import
  in-process cannot detect the leak, hence the subprocess shape).
  `static-reviewed`.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `tests/base/test_init.py` `HEAD
  4cc121057689`; `tests/rest_framework/test_soft_dependency.py` `HEAD
  ac2b38ae04f0`; `auth/__init__.py` `HEAD 6bc3c4a5eb96`; census P1.

### R1 — Upstream-symbol pass-through (rejected)

- Contract + variation (candidate, disproved): "re-export an upstream symbol so
  consumers import one name from us" — root `auto` (target line 16),
  `filters::Filter` (`filters/base.py` line 31 → `filters/__init__.py`), and
  `scalars.py::Upload` (line 25 → root line 46). Posited as one rule; the
  challenges prove three.
- Sites + roles: three independent definitions, each with its own upstream,
  consumer contract, and reason to change: `auto` is a typing marker for
  declare-but-infer fields (consumers: scalars example via the root import,
  `tests/types/test_definition_order.py`; production consumes `StrawberryAuto`
  directly for `isinstance`); `Filter` is a base class for subclassing that
  deliberately shadows the upstream name; `Upload` is a `NewType` scalar whose
  registry Strawberry owns. The root's `Upload` line is a consumer of
  `scalars.py`, not a fourth definition.
- Challenges: change `auto`'s source → 1 (root); change `Filter`'s source → 1
  (filters); change `Upload`'s source → 1 (scalars; root follows as consumer).
  Never the same 1. Contract differences: marker vs subclassing base vs
  registry-owned scalar; different upstreams (`strawberry`, `django_filters`,
  `strawberry.file_uploads.scalars`); different consumer instructions.
- Owner + lifetime: each site keeps its own import line (no shared owner —
  that is the verdict). No stored state beyond the bindings.
- Migration: none — sites stay separate.
- Distinct behavior: all of it — nothing is shared except the Python import
  mechanism.
- Behavioral proof: import lines + consumer sites read; P2 confirms root `auto`
  resolves; the scalars schema consumes it at line 39. `static-reviewed`
  (identity `auto is strawberry.auto` follows from import mechanics; no
  execution needed to disprove shared ownership).
- Structural gate + negative control: the per-site oracles (auto-marker tests,
  filter tests, upload tests) each pin their own site; a shared gate would fail
  open on the other two sites' contracts, so none is owed.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `filters/base.py` `WORK 91c41b1f7da5`
  (line 31 intact); `filters/__init__.py` `HEAD 86b258186638`; `scalars.py`
  `HEAD 5e354042d405`; `types/base.py` `WORK 1fe9e5ad6b17` (StrawberryAuto import
  + `_is_auto_annotation` intact);
  `examples/fakeshop/apps/scalars/schema.py` `HEAD 90b37673bdff`;
  `tests/types/test_definition_order.py` `WORK 202f835c832f1` (line 24 intact).
- Reconsideration trigger: if the package ever wraps upstream symbols uniformly
  (a deprecation/compat shim layer with one policy), the three become one rule
  and this rejection reopens.

### R2 — PEP 562 lazy-export hook, root vs routers (rejected)

- Contract + variation (candidate, disproved): "resolve a soft-dependency name
  lazily behind a guard" — target `__getattr__` (lines 98-126) vs
  `routers.py::__getattr__` (line 565). Same mechanism (PEP 562, the only two
  module-level hooks package-wide per S2), deliberately different contracts.
- Sites + roles: two independent definitions. Root: 7-name table dispatch,
  `require_drf()` guard, MUST NOT memoize (eviction tests re-hit), names
  ABSENT from `__all__` (star stays DRF-free). Routers: single-`if` dispatch,
  `require_channels()` inside `_build_router_class`, MEMOIZES into
  `_ROUTER_CLASS`, name PRESENT in `__all__` (star opts into the guard).
- Challenges: customize root's miss message → 1 (routers unaffected); add a
  second lazy name to routers → 1 (routers only); unify dispatch in one shared
  table → rejected as a consolidation (it would need a polarity flag over
  memoization + `__all__` membership, coupling two independent soft-dependency
  boundaries against principle 5). Contract differences are load-bearing and
  oracle-pinned on both sides (non-memoization assertions vs router memo + F822
  lazy-`__all__` comment).
- Owner + lifetime: each hook keeps its own body; guards stay at
  `rest_framework/__init__.py` / `routers.py` over the shared
  `require_optional_module` primitive (already single-owned — no work here).
- Migration: none.
- Distinct behavior: everything except the `def __getattr__(name: str)` shape
  and the interpreter-mirroring miss line (see R3/R4 for those tokens).
- Behavioral proof: both hook bodies + both `__all__` decisions + both guard
  wirings read end to end; S2 proves no third module hook exists.
  `static-reviewed`.
- Structural gate + negative control: each side's own oracles (hint +
  non-memoize vs router build + memo); no shared gate is owed for severed
  contracts.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `routers.py` `WORK d5c4350911f6`
  (lines 62-77, 565-569 intact); `rest_framework/__init__.py` `HEAD
  45cf7b63a2b7`; `utils/imports.py` `HEAD 291ecedd30c7`;
  `tests/rest_framework/test_soft_dependency.py` `HEAD ac2b38ae04f0`;
  `tests/test_routers.py` `WORK 4dc9443386ee0` (no hook-annotation pin —
  absence stands); census S2.
- Reconsideration trigger: if both hooks are ever required to share memoization
  polarity, `__all__` polarity, and guard shape at once, they become one rule.

### R3 — Module-hook `-> Any` return idiom (rejected)

- Contract + variation (candidate, disproved): "module `__getattr__` hooks
  return `-> Any`" — target line 98 vs `routers.py` line 565. Shared token,
  independent justification.
- Sites + roles: root's annotation is oracle-pinned with a runtime reason (two
  of the seven lazy targets are plain functions; the package ships `py.typed`,
  so `-> type` would hand type-checking consumers a false type —
  `test_getattr_return_annotation_admits_function_valued_exports` asserts the
  annotation AND the callable/not-type runtime facts). Routers' annotation is
  unpinned permissiveness over a single class return (no `get_type_hints` pin
  in `tests/test_routers.py` at the fingerprinted revision).
- Challenges: narrow root's to `-> type` → 1 (breaks the root oracle; routers
  unaffected); narrow routers' → 1 (root unaffected). No third axis exists for
  a bare annotation.
- Owner + lifetime: each hook keeps its own annotation. No stored state.
- Migration: none.
- Distinct behavior: the root's `Any` is load-bearing (function-valued
  exports); the routers' is merely permissive.
- Behavioral proof: P2 (the two function-valued exports) `execution-verified`;
  both annotations + the root pin read. `static-reviewed`.
- Structural gate + negative control: the root pin is the gate for the root
  annotation; routers' unpinned annotation needs no gate (nothing varies on
  it). A shared-alias gate would couple an enforced contract to an unenforced
  style choice.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `routers.py` `WORK d5c4350911f6`
  (line 565 intact); `tests/rest_framework/test_soft_dependency.py` `HEAD
  ac2b38ae04f0`; `tests/test_routers.py` `WORK 4dc9443386ee0`.
- Reconsideration trigger: if the package ever types module hooks jointly
  (e.g. a shared lazy-export protocol with one annotation), the two become one
  rule.

### R4 — AttributeError miss-message wording (rejected)

- Contract + variation (candidate, disproved): the identical
  `raise AttributeError(f"module {__name__!r} has no attribute {name!r}")`
  line in the target (line 126) and `routers.py` (line 569). Shared token, no
  shared rule: each mirrors the interpreter's own miss message so unrelated
  typos behave as usual.
- Sites + roles: two independent spellings of CPython's message format. The
  oracles (`...has no attribute 'unregistered_symbol_xyz'`,
  `match="DefinitelyNotAName"`) pin the behavior (an `AttributeError` naming
  the miss), not a package-owned wording.
- Challenges: customize root's message → 1; customize routers' → 1. An upstream
  CPython wording change would move both, but that is not a package rule change
  and counts for neither side.
- Owner + lifetime: each hook keeps its line. No stored state.
- Migration: none.
- Distinct behavior: none today (identical text) — independence rests on
  justification (each follows the interpreter), not on spelling difference.
- Behavioral proof: both lines + both miss oracles read. `static-reviewed`.
- Structural gate + negative control: none owed — no package rule exists to
  bypass; the interpreter owns the wording.
- Coupling: none.
- Freshness: target `HEAD 0ef72601ecac`; `routers.py` `WORK d5c4350911f6`
  (line 569 intact); `tests/base/test_init.py` `HEAD 4cc121057689`;
  `tests/rest_framework/test_soft_dependency.py` `HEAD ac2b38ae04f0`.
- Reconsideration trigger: if either hook ever needs a package-specific miss
  message (e.g. did-you-mean suggestions), the shared wording becomes a package
  rule and this rejection reopens.

## Defects

None. Three candidates were examined and are NOT defects (recorded so Worker 2
can see they were considered, not missed):

- (Not a defect) `types/base.py::_is_auto_annotation` recognizes the instance,
  `"auto"`, and `"strawberry.auto"` spellings only — a PEP 563 consumer writing
  the dotted-root `django_strawberry_framework.auto` spelling would not match.
  No contract row is broken: the docstring enumerates exactly three spellings,
  and consumers are instructed `from django_strawberry_framework import auto`
  (CHANGELOG). At most a robustness note for the `types/base.py` file item;
  no owner, no routing.
- (Not a defect) `export_dry_review.py::VERSION_PATTERN` requires `"` while
  `scripts/bug_hunt.py::_INIT_VERSION_PATTERN` accepts either quote. Both
  accept the current spelling; divergent tolerance with no failure is not a bug.
- (Not a defect) `filters`/`testing`/`middleware`/`management` absences from the
  root import are unpinned. They are incidental (no spec decision, no pin —
  the `filters/sets.py` "does NOT import" line is a descriptive premise, not a
  normative contract), hence not rules and not missing guards.

- (Worker 2) D-W2-2 (minor, test-side): no independent oracle pins the exact
  `_DRF_SOFT_EXPORTS` key set from above. The per-name guard/non-memoization
  tests parametrize their population FROM the table
  (`tests/rest_framework/test_soft_dependency.py` lines 97, 131) and
  `tests/base/test_init.py::test_dynamic_drf_soft_exports_via_getattr` spells 7
  names (lower bound only), so adding an 8th lazy entry with a valid target
  breaks zero committed tests — unlike the eager surface, where any widening
  fails the exact-tuple pin whose stated rationale ("silent surface widening
  shows up at test time") applies equally here. This narrows W1's F4 gate
  sentence without contradicting it: the `tuple(...)`-derived parametrizations
  do auto-extend per-name BEHAVIOR coverage (hint fires, no memoize) for
  whatever the table holds; what is unpinned is MEMBERSHIP itself. Fix shape
  (for the owning card, not this item): one exact-set pin; do not rewrite the
  parametrized behavior tests. Owner: `tests/rest_framework/test_soft_dependency.py`.
  (Worker 2's Phase-A candidates D-W2-1/D-W2-3 were downgraded to observations
  in reconciliation — no contract row broken — and are not defects.)

## Pending execution

No entries: every behavioral proof above is `execution-verified` (read-only
probes P0-P3, commands recorded) or `static-reviewed` (censuses S1-S6 and body
reads). No `proof:` or `gate:` command is owed. Sharded and Postgres cells are
inapplicable by construction (stated per finding in `### Challenges`).

## Index rows for Worker 0

No new families are named — no Family holding item is owed. Worker 0 is asked to
add the following eleven rows to the plan's `## Responsibility index` (statuses
`file-local` / `rejected` only):

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| Package-root eager export surface: 38 names admitted by import + `__all__` | `django_strawberry_framework/__init__.py::__all__` | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| Single-sourced release literal `__version__` | `django_strawberry_framework/__init__.py::__version__` | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| Canonical package logger + logger-before-subimports order | `django_strawberry_framework/__init__.py::logger` | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| DRF lazy-export name table `_DRF_SOFT_EXPORTS` | `django_strawberry_framework/__init__.py::_DRF_SOFT_EXPORTS` | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| DRF lazy-export hook: guard routing + non-memoization + miss passthrough | `django_strawberry_framework/__init__.py::__getattr__` | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| Debug-extension root exclusion by omission | `django_strawberry_framework/__init__.py` (import block, by omission) | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| Root import-hygiene absences (orders / rest_framework / auth) | `django_strawberry_framework/__init__.py` (import graph, by omission) | `django_strawberry_framework/__init__.py` | File `__init__.py` | file-local |
| Upstream-symbol pass-through (auto / Filter / Upload) | `django_strawberry_framework/__init__.py` (root side; rejection recorded here) | `django_strawberry_framework/__init__.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/__init__.py`, `django_strawberry_framework/scalars.py`, `django_strawberry_framework/types/base.py` | File `__init__.py` | rejected |
| PEP 562 lazy-export hook (root vs routers) | `django_strawberry_framework/__init__.py::__getattr__` (rejection recorded here) | `django_strawberry_framework/__init__.py`, `django_strawberry_framework/routers.py`, `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/utils/imports.py` | File `__init__.py` | rejected |
| Module-hook `-> Any` return idiom | `django_strawberry_framework/__init__.py::__getattr__` (rejection recorded here) | `django_strawberry_framework/__init__.py`, `django_strawberry_framework/routers.py` | File `__init__.py` | rejected |
| AttributeError miss-message wording | `django_strawberry_framework/__init__.py::__getattr__` (rejection recorded here) | `django_strawberry_framework/__init__.py`, `django_strawberry_framework/routers.py` | File `__init__.py` | rejected |

## Judgment

The target is a pure surface file whose every rule is already single-owned:
membership is defined once (`__all__` + imports), the version once, the logger
once (proved by census), the lazy table once, the hook routing once, and the
four omissions each in exactly one place. The package-wide mechanism sweeps
found the plausible twins (sibling `__all__`s, the routers hook, upstream
pass-throughs, the `apps.py` name token, the interpreter's miss message) and
each challenge counted 1 — shared tokens, independent rules. Zero production
edits, zero new families, zero defects. Ready for verification.

## Independent verification (Worker 2) — expectations (Phase A)

Worker 2, File `__init__.py`, run `0.0.15 2026-09-21-2`. Recorded BEFORE
reading `## Findings` (Worker 1's diagnosis withheld until Phase B).
`ITEM_BASELINE=6198956b4270a5d86848c787db02697350e2042c` (resolves).
HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e` at start AND end (unmoved).
Target `django_strawberry_framework/__init__.py` blob `0ef72601ecac300ac87ff993af1b04a4f1bc335a`
at start and end (clean, unmoved). Working tree carried 111 dirty paths at
start and end (count unchanged); every package file censused below was read at
HEAD bytes. The artifact `docs/dry/dry-file-__init__.md` was stat-checked only
(47966 bytes, mtime unchanged start→end) and never opened; no worker-memory
directory was read. No pytest was run (not authorized); all probes are
read-only `python` runs, re-run by me, kept in
`docs/dry/temp-tests/dry-file-__init__-r2-w2/` (`census.py`, `probe2_sources.py`,
`probe3_live.py`, `probe4_subprocess.py`). `FAKESHOP_SHARDED=1`/Postgres not
authorized — nothing below needs them (no database, alias, or dialect decision
is reachable from the target; inapplicable by construction).

### Enumeration (my instrument + count)

Instrument: every name bound at module level per `ast.Module.body` over HEAD
bytes (`census.py`), plus the module docstring. 25 top-level statements; **45
module-level bindings**: 1 plain import (`logging`), 39 from-imports (`Any` +
38 public eager re-exports: 1 third-party `auto` + 37 first-party), 5
defined-here (`logger`, `__version__`, `_DRF_SOFT_EXPORTS`, `__getattr__`,
`__all__`). Derived counts: `__all__` 39 entries (unique; grouped
4 SCREAMING + 29 CamelCase + 6 tail, each group ASCII-sorted — verified
mechanically, stated in no prose); `_DRF_SOFT_EXPORTS` 7 entries, every key ==
its attr (name-identity holds). `__all__ − imports = {__version__}`;
`imports − __all__ = {Any}`.

Per-binding home (every member lands; `S`=surface row, `L`=logger row,
`V`=version row, `D`=lazy-DRF row, `H`=pull/hygiene row — rows proposed
under Assignment; the routers-twin rejection covers one line inside
`__getattr__`):

- `logging` → L (construction machinery for `logger`).
- `Any` → D (return annotation of `__getattr__` only; `-> Any` pinned by
  `tests/rest_framework/test_soft_dependency.py::test_getattr_return_annotation_admits_function_valued_exports`
  because two soft exports are plain functions).
- `auto` → S (third-party re-export; single site per `git grep 'import auto'`).
- 37 first-party eager aliases → S. `probe2_sources.py` at HEAD: 26 DEFINED in
  the stated source module, 11 re-exported THROUGH it (`forms/__init__` 2,
  `mutations/__init__` 4, `optimizer/__init__` 1, `types/__init__` 3,
  `scalars.py` 1 — Strawberry's `Upload`), 0 missing. Deepest chains spot-read:
  `types/relay.py` re-exports `SyncMisuseError` via
  `from ..utils.querysets import SyncMisuseError as SyncMisuseError` (single
  class def at `utils/querysets.py:119`, already rowed file-local by the
  querysets item — this file is a pass-through consumer, no new assignment).
- `logger` → L. `__version__` → V. `_DRF_SOFT_EXPORTS`, `__getattr__` → D
  (all 7 lazy targets DEFINED in their stated submodules at HEAD, `probe2`).
- `__all__` → S. Module docstring + all rationale comments → projections on
  their rule's row (R10: no rule of their own; the auto rationale, logger-first
  E402 note, version single-source note, DebugExtension non-export note, and
  DRF-table role sentences describe R1–R8 mechanics).

Rules I enumerate for assignment: R1 attribute surface (38 eager + 7 lazy
resolvable), R2 star surface (`__all__` membership/order/exclusions), R3
canonical logger + logger-first ordering, R4 release literal, R5 lazy-target
table, R6 lazy-resolution behavior, R7 eager-import hygiene, R8 deliberate
non-exports, R9 re-export identity, R10 prose (projection-only).

### Matrix (all six axes discharged against the real surface)

1. Cross-flavor policy mirroring — SEARCHED. Ten subpackage `__init__` surfaces
   read at HEAD (`filters`, `forms`, `mutations`, `types`, `utils`, `testing`,
   `auth`, `middleware` (deliberately empty), `orders`, `rest_framework`): each
   owns its own membership; no twin of the root's 39-member selection exists
   (adding a root name moves no sibling). Soft-guard flavors
   (`require_drf` / routers `require_channels` / `require_debug_toolbar` over
   `utils/imports.py::require_optional_module`): the root only CONSUMES
   `require_drf`; each wrapper is a one-line name+hint declaration over an
   existing driver (already the principle-1 shape — posit a hint change: count
   1; posit a primitive change: count 1 at `utils/imports.py`). No candidate.
2. Sync/async twins — INAPPLICABLE with reason: the module defines no
   coroutine, `await`, or async construct (census: one `def`, sync); the
   `aapply/apply_cascade_permissions` pair is re-exported, and its twin
   contract is owned by `permissions.py`, not this file.
3. Derived rather than repeated knowledge — SEARCHED, four sub-cases:
   (a) `__all__` vs import list: INTENTIONAL SEPARATION, not duplication. The
   star facet carries independent selection info the bindings lack — `logger`
   is bound but unstarred (LOGGING-key rationale in the comment), 7 lazy names
   resolve but are unstarred (Decision 12), `logging`/`Any` are machinery.
   Precedent shape: DRY.md's `FilterSet.get_fields` two-`__all__` case.
   (b) Submodule strings in the table: single spelling; the filesystem is
   reality, not a second definition. (c) Package anchor: `__getattr__` derives
   via `__name__` twice (`import_module(submodule, __name__)`, miss message) —
   no second package-name literal. (d) Logger literal: single `getLogger` call
   in the package (HEAD grep); `apps.py::name` shares the spelling but is the
   Django app-registry identity — rename-logger challenge (C3) does not move
   it. No consolidation.
4. Inverse / round-trip pairs — INAPPLICABLE with reason: the table is a
   one-way name→target map; `_DRF_SOFT_EXPORTS` uses at HEAD are exactly
   definition + `__getattr__`'s `.get(name)` + test reads — no inverse lookup
   exists anywhere. No encode/decode, pack/unpack, build/parse in the module.
5. Contracts restated in another medium — SEARCHED and classified (oracles,
   consumers, projections listed, never counted):
   - Oracles: `tests/base/test_init.py` (9 tests: exact `__version__` literal,
     logger type+name strings, optimizer `is` identity, exact 39-tuple `__all__`
     pin incl. order, 3 file/upload identities, 7 lazy names spelled
     explicitly, 1-name non-memoization, miss message, star hygiene, 13
     re-export identities, orders-absence subprocess) and
     `tests/rest_framework/test_soft_dependency.py` (fresh-process DRF-absent
     import+star, per-name guard raises, package/sets import raises, star
     DRF-free, miss-type, per-name non-memoization, `-> Any` pin). NOTE: the
     per-name guard/non-memoization tests parametrize their population FROM
     `_DRF_SOFT_EXPORTS` (owner-read population) — drops are still caught by
     test_init's explicit 7, but additions are caught NOWHERE (defect D-W2-2).
   - Consumers: hatchling `path = "django_strawberry_framework/__init__.py"`
     reads the version (0 edits on bump); 14 `import logger` sites incl. the
     optimizer re-export bind the one object (0 edits on rename);
     `from .rest_framework import require_drf` + the explicit `require_drf()`
     call cover the full-eviction and partial-eviction shapes respectively.
   - Projections: glossary PEP-562 entry (BOTH lazy instances + their opposite
     `__all__` decisions + shared miss behavior), 5× "Exported from the
     package root" per-symbol lines, auth/DebugExtension/views non-export
     notes, TREE.md "package root owns the public exports" ownership line,
     `extensions`/`auth`/`middleware`/`utils` docstring paragraphs,
     `routers.py:204` + `utils/imports.py:132` guard-contract citations,
     `types/base.py:593` `auto` mention. A surface change moves projections
     with the facets by design (production+oracle+projection ≠ 3 definitions).
6. Enforcement by omission — SEARCHED by enumeration. Star-membership over all
   45 bindings: 39 in, 5 out (`logging`, `Any` machinery; `logger` deliberate
   per comment; `_DRF_SOFT_EXPORTS` + `__getattr__` machinery, absence pinned
   by the star test) — every absence justified, none a gap. Eager-pull family
   (`probe4` Q1, module set HEAD-valid per the import-edge diff check): ~65
   modules in; absences with contract sources — `orders` (test-pinned),
   `rest_framework` (DRF-free contract), `auth` (spec-040 Decision 3,
   structural opt-in), `routers` (channels-free root import); name-level
   deliberate omissions with contract sources — `DjangoDebugExtension`
   (extensions home, default-recipe rationale in `extensions/__init__.py`),
   views (leaf imports, glossary), middleware/debug_toolbar (leaf opt-in,
   spec-042). `extensions.debug` IS pulled while its name stays unexported —
   intended (name-level opt-in; eager-subpackage shape documented). No member
   lacks an enforcement a contract source requires → no defect from this axis.

### Challenges (authoritative-definition counts; rest listed)

- C1 add an eager public name → attribute facet 1 (import line) + star facet 1
  (`__all__` entry; a DISTINCT decision — logger precedent proves independent
  variation). Oracles moving: `__all__` pin (+identity test by convention).
  Projections: glossary line. No second meaning-site.
- C2 rename a re-exported symbol → defining module (elsewhere) + root import
  alias + `__all__` string; root-side 2 coordinated facet edits, each
  single-owned. Same verdict as C1.
- C3 rename the logger string → 1 (`getLogger` literal). `apps.py::name`
  untouched (different contract). 14 consumers move by binding (0 edits).
  Oracle: logger-name test. Count 1, file-local.
- C4 bump `0.0.15` → next → 1 (`__version__` literal). Hatchling reads by path
  (0 edits). Oracle `test_version` moves by design. Remaining `0.0.15` strings
  are historical hunt references in docstrings, untouched. Count 1, file-local.
- C5 add an 8th lazy DRF name → 1 (table row). Guard 0, `__getattr__` body 0
  (table-driven), `__all__` 0 (excluded by Decision 12). PROVES D-W2-2: zero
  committed tests fail on lazy widening today (reading-established, not
  execution-verified — no mutation run authorized). Count 1, file-local.
- C6 reword the miss fallback → root line 1; `routers.py` twin untouched (each
  module mimics the interpreter for its OWN `__name__`; wording owned
  externally by CPython convention). The twin mechanisms differ in contract:
  table + DRF-guard + EXCLUDED-from-`__all__` (spec-039 Decision 12) vs single
  name + channels-guard + LISTED-in-`__all__` (spec-041) — the opposite
  `__all__` decisions are source-stated in both modules and the glossary.
  REJECTION (below), not a family; extracting the one shared line would be
  principle-11 machinery.
- C7 root-export `DjangoDebugExtension` → import + `__all__` (facets, 1 each);
  root comment deleted + extensions-docstring paragraph + glossary line are
  projections moving with it. No second meaning definition.
- C8 a new subpackage re-exports `logger` (optimizer docstring's "future
  subpackages" invitation) → 0 root edits (pure consumer). Proves the
  consumer/definition split for R3.
- C9 change the DRF floor `3.17.0` → 0 root edits (root never spells the floor;
  name-based resolution). The three-places-that-must-agree live at the guard +
  pyproject + spec — OBSERVED and left for the `rest_framework/__init__.py`
  file item to enumerate; no family named from here (no definition site in
  this file).
- C10 flip the lazy `__all__` policy to the routers shape → 1 (`__all__`
  facet); table comment + `__getattr__` docstring + glossary + soft-dep tests
  are projections/oracles of the Decision-12 rule. Count 1, file-local.

### Assignment proposals (every rule lands)

Existing families checked: all 13 plan-index families are
querysets/relations-centered (`awaitable-refusal-and-disposal` … `orm-lookup-path-resolution`,
incl. the two rejected rows) — none genuinely owns a root-surface rule, so
none is taken. New families proposed: NONE (no count>1 found; C9's triple is
another file's to enumerate).

File-local rows proposed (5 rows covering R1–R9; R10 projection-only, no row):

1. `root-public-surface` — owner `django_strawberry_framework/__init__.py`
   (import block + `__all__`; R1+R2+R9). Proving challenges C1/C2/C5/C10:
   no sibling owns root membership; identity holds by construction for all
   38+7 (`probe2` 0 missing, `probe3` P3b 7/7 `is`). Consumers: every
   `from django_strawberry_framework import …` site. Oracles: `__all__` pin,
   identity tests, star-hygiene tests.
2. `root-canonical-logger` — owner `__init__.py::logger` (R3). Proving
   challenges C3/C8: one `getLogger` call package-wide; optimizer re-export is
   `from .. import logger` (same object, `probe3` P3e `is`); ordering is
   load-bearing (9 top-level `from . import logger` / `from .. import logger`
   sites read at HEAD, incl. eagerly-imported `schema.py`, `optimizer/*`,
   `types/*`). Oracles: logger-name + optimizer-identity tests.
3. `release-literal` — owner `__init__.py::__version__` (R4). Proving
   challenge C4: one declaration; hatchling consumer by path. Oracle:
   `test_version`.
4. `root-lazy-drf-exports` — owner `__init__.py::_DRF_SOFT_EXPORTS` +
   `__getattr__` (R5+R6). Proving challenges C5/C6/C10: table-driven,
   name-identity key==attr all 7, guard-first both eviction shapes,
   non-memoizing (`probe3` P3c 7/7), interpreter-shaped miss (`probe3` P3d
   exact). Oracles: soft-dependency suite + lazy tests in test_init.
5. `root-import-hygiene` — owner `__init__.py` import block by omission
   (R7+R8). Proving evidence: Q1 eager set + six absences with contract
   sources (matrix axis 6); DebugExtension/auth/views/middleware omissions each
   contract-sourced. Oracles: orders-absence + fresh-process DRF-absent tests.

Rejection proposed (1):

- R-R1 `module-__getattr__-fallback-wording` (root `__getattr__` miss line vs
  `routers.py::__getattr__` miss line): REJECTED. Contract difference: the
  shared text mimics the interpreter per-module (`__name__` differs), and the
  enclosing mechanisms are opposite by design (table+DRF-guard+excluded vs
  single+channels-guard+listed — spec-039 Decision 12 vs spec-041, glossary
  PEP-562 entry states both). Shared form considered (one fallback helper):
  would own one line and couple two soft-dependency flavors — principle-11
  machinery. Trigger: both modules adopt one shared lazy-export driver (none
  exists; PEP 562 is language mechanism, not package rule). Durable home if
  accepted: a docstring clause at the root `__getattr__` (owner of this side).

### Defects (Worker 2; minor, none verdict-affecting, none a release blocker)

- D-W2-1 (prose gap) — owner `django_strawberry_framework/__init__.py` (table
  comment): role sentences cover 6 of 7 `_DRF_SOFT_EXPORTS` entries;
  `describe_serializer_input` (input-shape diagnostic, role documented only at
  `rest_framework/inputs.py::describe_serializer_input`, HEAD blob
  `9b17d95229b3` lines ~924-934) has none. Table (authoritative) + tests
  (all 7 resolve) are correct; prose lags by one entry.
- D-W2-2 (test-side pin gap) — owner
  `tests/rest_framework/test_soft_dependency.py`: no independent oracle pins
  the exact lazy key set from above — the per-name tests parametrize FROM the
  table (lines 97, 131) and test_init spells 7 names (lower bound only), so an
  8th lazy entry breaks zero tests (C5; reading-established —
  execution-verification would need a source-mutating run, not authorized).
  Unlike `__all__`'s exact pin, silent lazy widening is uncaught.
- D-W2-3 (ambiguous layering claim) — owner
  `django_strawberry_framework/utils/__init__.py` (docstring): "The package
  root re-exports a small, PINNED set of names" is true for the utils-root
  reading (7 == len(utils `__all__`)) but false for the
  `django_strawberry_framework`-root reading (root re-exports ZERO utils
  names) — and "package root" repo-wide means the latter (TREE.md). One
  available reading contradicts the root imports.

### Probe outcomes (all re-run by me; all green)

- `census.py` (HEAD bytes): 25 stmts, 45 bindings, `__all__` 39
  (unique/grouped-sorted), table 7 (key==attr 7/7). OK.
- `probe2_sources.py` (HEAD bytes each): 38/38 eager aliases resolve (26
  defined + 11 re-exported-through, 0 missing); 7/7 lazy targets DEFINED. OK.
- `probe3_live.py` (in-process, dirty tree): package `__file__` under the
  checkout; version `0.0.15`; star keys == `set(__all__)` (39); 12 hygiene
  absences; lazy `is` identity 7/7; non-memoization 7/7; miss wording exactly
  the interpreter shape; optimizer `is` root logger. OK — every claim executes
  clean files only (target + `optimizer/__init__`), except lazy identity which
  additionally binds two dirty-but-importable modules (`rest_framework/sets`,
  `serializer_converter`); HEAD-definedness of those targets comes from
  `probe2`, not this run.
- `probe4_subprocess.py` (fresh interpreters): Q1 eager set enumerated
  (~65 modules; `orders`/`auth`/`rest_framework`/`filters`/`routers`/`views`
  absent); Q2 DRF-absent matrix all-OK (root+star succeed, subpackage
  unimported, per-name hint `djangorestframework>=3.17.0`, miss stays
  `AttributeError`). OK. HEAD-validity of Q1's absences: the dirty→HEAD diff
  adds no first-party module edge (only `..exceptions` widenings,
  one `strawberry.relay.utils` widening, stdlib `keyword`) and removes none —
  module-level import graph identical, so the set holds at HEAD.
- HEAD greps (populations stated): `getLogger(` 1 site; `def __getattr__`
  module-level 2 sites (root + routers; class-level 3 excluded by mechanism);
  `_DRF_SOFT_EXPORTS` uses = def + `.get` + test reads; `import auto` 1 site;
  `class SyncMisuseError` 1 site; `DjangoDebugExtension` root comment +
  extensions home; `0.0.15` declaration 1 site (+historical prose).
  `TREE.md` read at HEAD (dirty in tree); every other input file verified
  byte-identical tree==HEAD or read at HEAD bytes.

### Freshness fingerprints (HEAD blobs inspected; `git rev-parse HEAD:<path>`)

Target `0ef72601ecac`; `connection` `93e998f2c7ea`; `error_policy`
`fa94fcd9e952`; `extensions/error_policy` `16f475471a8b`;
`extensions/resource_policy` `52084078ac16`; `extensions/__init__`
`dc3ebdc24b48`; `forms/__init__` `a76a4f797414`; `list_field` `ce682d5f7951`;
`mutations/__init__` `9a5683e91457`; `optimizer/__init__` `d400569adf8b`;
`optimizer/hints` `da46ef891ccd`; `permissions` `757dce34cecd`; `relay`
`c3c5aea52768`; `resource_policy` `647133d23785`; `scalars` `5e354042d405`;
`schema` `c2e1b748c26c`; `types/__init__` `24e8ec204a78`; `types/converters`
`9ceb34afec59`; `types/relay` `524398622354`; `rest_framework/__init__`
`45cf7b63a2b7`; `rest_framework/sets` `2c7117d6410e`;
`rest_framework/serializer_converter` `32904418a169`;
`rest_framework/inputs` `9b17d95229b3`; `rest_framework/hook_context`
`f4910159df29`; `utils/imports` `291ecedd30c7`; `utils/querysets`
`96618fba4eaf`; `utils/__init__` `1a4c2ec8bfd3`; `routers` `a18c5001471d`;
`apps` `8ae1a3a3b12f`; `auth/__init__` `6bc3c4a5eb96`;
`middleware/__init__` `6e1b64ca7b93`; `filters/__init__` `86b258186638`;
`orders/__init__` `ed546f9c70d5`; `tests/base/test_init.py` `4cc121057689`;
`tests/rest_framework/test_soft_dependency.py` `ac2b38ae04f0`; `pyproject.toml`
`9be864937662`; `docs/GLOSSARY.md` `bc51debc54cf`; `docs/TREE.md`
`cd075cbb6726`. Excluded on body inspection (not family members): `apps.py`
(app identity ≠ logger name); `conf.py`/`consumers.py`/`utils/permissions.py`
`__getattr__` (instance-level, different mechanism); every non-root `__all__`
(own surface each); guard-wrapper trio (declarations over existing driver).
Pre-finish gate: no hunk in any path this item touches beyond my own scratch —
HEAD, target blob, artifact size/mtime, and dirt count (111) all identical
start→end. No verdict set (Phase A).

## Independent verification (Worker 2) — reconciliation (Phase B)

Read W1's record (lines 1–721) only after the blind append (byte-verified
`TAIL_MATCH`). No `dry-file-__init__-r2-w1` scratch scope exists — W1 ran
inline probes only, as stated. Re-ran every load-bearing check as V1–V19
(HEAD bytes throughout; live parts read-only, no pytest): V1 routers
memoization shape, V2 WORK↔HEAD line mapping, V3 filters pass-through, V4
auto spellings, V5 permissions re-export, V6 toolbar oracle body, V7 version
readers, V8 projection existence, V9 logger-import recount, V10 lazy kinds +
logger level, V11 `__all__`-vs-pin sequence equality, V12 scripts `__all__`
sweep, V13 test-side string spellings, V14 table-mutation sweep, V15
filters-premise reading, V16 full fingerprint re-hash (29 HEAD + 7 WORK),
V17 management inits, V18 `get_type_hints` absence, V19 spec-039 path.
Outcome: adopt W1's 7 file-local rows + 4 rejections (11 index rows) in full;
details per difference below. HEAD `bfaee91d` / target `0ef72601ecac` /
dirt 111 identical at Phase-A start, Phase-B start, and now.

### Enumeration — agree (finer instrument, same base)

Both count 25 statements (W1 P0; my census). My 45-binding instrument is a
strict refinement: every W1 statement disposition maps onto my per-binding
homes without conflict (#0→projection, #1→logger row, #2→hook rows, #3→F3,
#4→R1 — endorsed below, #5–20+#24→F1, #21→F2, #22→F4, #23→F5+R2/R3/R4,
debug comment→F6, hygiene absences→F7, noqa markers→mechanics). Inversely, my
10 rules map onto W1's rows: R1+R2+R9→F1, R3→F3, R4→F2, R5→F4, R6→F5,
R7+R8→F6+F7 (narrowed — see Matrix 6), R10→projections. No member is homeless
on either side; no holding family is owed by either side.

### Matrix — agree on all six, with supplements both ways

1. Cross-flavor: agree (searched, no candidate). W1 read all 14 sibling inits;
   I read 12 — gap closed by V17 (both management inits docstring-only, no
   `__all__`, exactly as W1 states). W1's container-shape challenge
   (retuple moves one file) endorsed as searched-and-clear; my guard-wrapper
   analysis (declarations over the existing driver, count 1 per posit) stands
   uncontradicted.
2. Sync/async: agree (inapplicable, same reason — one sync hook; twin owned
   by `permissions.py`).
3. Derived knowledge: agree (no consolidation). Framing delta reconciled: W1's
   challenge table counts "add a public name" as 1 ("import block + `__all__`,
   one edit"); my Phase A counted attribute-facet 1 + star-facet 1. Both agree
   the single owner is the target, no second site exists, and the logger
   (bound-but-unstarred) proves the star facet varies independently — W1's
   "one edit" is loose wording for "one owner", verdict-unaffecting, no action.
   W1's logger-vs-`__name__` rejection (wire key vs module identity) is
   stronger than my Phase-A note and is adopted.
4. Round-trip: agree (inapplicable). W1's star-binding-both-directions
   observation endorsed as supplement; my no-inverse-use grep (V14 extends it
   to no-mutation) stands.
5. Other media: agree (classified, none counted). Union of oracle lists: W1's
   third oracle module (V6 toolbar star test — verified body + hash
   `dd6df61673fb`) and version-reader consumers (V7 — `VERSION_PATTERN`
   requires `"`, `_INIT_VERSION_PATTERN` either quote, both clean) are
   supplements I missed and now endorse; my glossary PEP-562 entry +
   per-symbol lines + TREE.md ownership line are supplements W1 has only
   generically ("soft-dependency entries") and stand. The owner-read
   `tuple(...)` populations are where D-W2-2 (held, see Defects) bites.
6. Omission: agree on established (Debug/orders/rest_framework/auth) and
   incidental (filters/testing/middleware/management — V15 confirms the
   filters line is a descriptive premise). CORRECTION (mine, conceded): my
   Phase A listed `routers`/`views` module absences as contract-sourced; they
   are incidental — `routers.py` is channels-free to import, so the
   channels-free root property never required its absence, and no decision or
   pin covers `views`. My H row narrows to W1's F6+F7 scope exactly.

### Challenges — counts agree on every shared posit

F1 add/remove/reorder (1 each), F2 bump/reformat/add-reader (1/1/0 — reformat
verified via V7), F3 rename/derive-rejected/move-below (1/—/1), F4
add/retire/retarget (1 each), F5 memoize/miss-shape/guard-route (1/1/1), F6
promote (1), F7 land-edge (1 each) — all endorsed; my C1–C10 are the same
posits at coarser grouping, plus C8 (0-edit consumer extension) and C9 (0
root edits on floor change, left for the rest_framework item), which stand
uncontradicted. R1/R2/R3/R4 challenge sets endorsed with the verifications
below. Sharded/PG inapplicable-by-construction: independently agreed.

### Site roles — agree, four W1 supplements endorsed, two count/wording corrections

- `permissions.py:134` redundant-alias `SyncMisuseError` re-export (V5):
  verified consumer with rationale comment; querysets row stands. Endorsed.
- Toolbar star oracle (V6), version readers (V7), projection/consumer
  listings (V8 — CHANGELOG/KANBAN-rule-31/uv.lock/TODAY/schema all verified
  existentially): endorsed.
- CORRECTION (both): production `import logger` statements are **12**, not
  W1's "9" nor my Phase-A "14" (V9 recount excluding 3 comment/docstring
  lines; test-side: 8 statements — my Phase-A grep was `head`-truncated).
  Both workers' SETS agree exactly; only the headlines were wrong.
  Verdict-unaffecting (all bind by name; S1's single `getLogger` stands).
- CORRECTION (W1 sentence, verdict-unaffecting): S4/F3's "only the oracle
  spells it" is false for tests — V13 finds the literal in
  `tests/extensions/test_debug.py` (~13 `caplog` sites),
  `tests/optimizer/test_extension.py`, and others. Harmless: those are
  additional oracle pinnings of the wire-visible key, not definitions; the
  production half (S3: logger call + `apps.py::name` only) re-verified true.
- R1 upstream pass-through (V3+V4): `filters/base.py:31` import,
  `filters/__init__.py` shadows-upstream docstring, `types/base.py:51`
  `StrawberryAuto` import + 3-spelling `_is_auto_annotation` contract all
  verified at HEAD. A candidate class my Phase A never swept; correctly
  reasoned and rejected (marker vs base vs scalar, distinct upstreams).
  Endorsed with its trigger (uniform upstream-wrap layer).
- R2 hook twin (V1+V2): double-checked-locking memoization into
  `_ROUTER_CLASS` (HEAD 172–173/333–340/529–530) and guard-first uncached
  builder (HEAD 356) verified; WORK 565–569 == HEAD 533–537 byte-identical
  (numbering delta = dirt shift, reconciled). Opposite memoization +
  opposite `__all__` polarity + distinct guards = load-bearing contract
  difference. Endorsed with its trigger. (My Phase-A combined rejection
  retires in favor of W1's R2+R4 split.)
- R3 `-> Any` idiom (V18): routers side unpinned at HEAD and in WORK diff;
  root side pinned with runtime reason. Independent justification for a
  shared token. Endorsed with its trigger.
- R4 miss wording: agreed — interpreter-owned, each side mirrors for its own
  `__name__`; CPython drift counts for neither. Endorsed with its trigger.

### Assignments — adopt W1's 11 rows

My 5 file-local rows + 1 combined rejection retire in favor of W1's 7 + 4
(finer, verified, same owners): F1 surface, F2 version, F3 logger, F4 table,
F5 hook, F6 debug exclusion, F7 hygiene, R1 pass-through, R2 hooks, R3 `-> Any`,
R4 wording. No existing plan family taken (agreed — all 13 are
querysets/relations-centered); no new family named (agreed — no count>1; C9's
floor triple stays with the rest_framework item). Worker 0 is asked to add
W1's `## Index rows for Worker 0` table (11 rows) verbatim.

### Defects — one held, two downgraded, three endorsed

- D-W2-2 HELD (appended under `## Defects`, marked Worker 2): lazy-membership
  upper bound unpinned; exact-set pin owed on a future card. Narrowed
  precisely against W1's F4 gate sentence (behavior coverage auto-extends;
  membership does not). Minor, test-side, routes to the maintainer via Worker 0.
- D-W2-1 (table-comment role sentence) + D-W2-3 (utils "package root"
  ambiguity) DOWNGRADED to observations: neither names a broken contract row
  (comment lacks a gloss but contradicts nothing; the utils sentence carries
  its true reading via "the seven" + "(`__all__` below)"). Recorded here, not
  defects. (No Worker 0 action.)
- W1's three not-defects endorsed: (a) verified — docstring enumerates
  exactly three spellings and explicitly rejects other dotted prefixes (V4);
  (b) verified — divergent quote tolerance, both accept current spelling
  (V7); (c) verified — incidental absences incl. my conceded routers/views
  (V15 + Matrix 6).

### Probes — W1's P0–P3/S1–S6 all endorsed (two with corrected numbers)

P0 25 statements (match), P1 67 modules — CORRECTION of my Phase-A "~65":
a careful count of my own Q1 output is exactly 67; absence sets compatible
(mine fuller, stands as supplement); P2 39-tuple + grouped order + 5/2 kinds
+ logger level inheritance — all re-verified (V10: per-name kind table,
handlers `[]`, level `NOTSET`); P3 bindings-vs-`__all__`-vs-pin — re-verified
as sequences 39/39 (V11; W1's "38 imported" excludes support import `Any`,
consistent with my `imports−__all__={Any}`); S1/S3/S5/S6 re-verified
(V14/V12: no mutation site, only the `review_inspect.py` docstring mention);
S2 twin census agreed modulo the WORK↔HEAD numbering delta (V2); S4 set
agreed with the 9→12 count correction + test-spelling sentence correction
above. No `proof:`/`gate:` entries owed — `## Pending execution` stays empty
(agreed); sharded/PG inapplicable by construction (agreed, judged).

### Freshness — every fingerprint re-hashed, all match

Phase-A shared set re-confirmed (target `0ef72601ecac`, both test files,
16 sibling/related modules, pyproject, GLOSSARY, TREE.md). V16a: all 22
W1-only HEAD prefixes match byte-identical (testing `48b45d1b4332`,
management `beb4e0ee66a2`, commands `31cb58b85817`, mutations/permissions
`54f770ae5aa1`, opt/extension `49667a9370ce`, opt/walker `9b111ed93895`,
single_parent `e995270af9b2`, types/resolvers `f3341e6a9f52`, consumers
`936210e2993d`, ext/debug `bf25c1461113`, schema `c2e1b748c26c`,
_request_body `a70571ff5b38`, fakeshop schema `303ea2da9df1`, TODAY
`9c6786222a74`, CHANGELOG `d4e1035554f1`, uv.lock `6e8552ad5074`,
export_dry_review `83e969d9c8e5`, bug_hunt `14e39585a2f6`, toolbar oracle
`dd6df61673fb`, test_walker `5bbd7a567f04`, _soft_dependency `7b28c07853d1`,
scalars schema `90b37673bdff`); spec-039 = `docs/SPECS/spec-039-…md`
`cf78af93437b` (path resolved, match). V16b: all 7 WORK hashes match W1's —
concurrent dirt unshifted under every intact-line claim. Nothing stale.

### Item diff + gate

Diff scope = the artifact only (untracked): W1 pass-1 content (47966 B) + my
Phase-A append (20303 B, byte-verified) + this reconciliation + the D-W2-2
entry + the Status flip — all item-authored, no third-party hunk (110→111
dirt delta is the artifact file itself). Target untouched (`0ef72601ecac`).
Zero production edits (file item owes none). `uv run ruff check` /
`ruff format --check` on the artifact: both exit 0 (vacuous for `.md`;
per-cycle scratch exempt from style cleanup; line-number citations allowed).
W1's "110 dirty at probe time" vs my "111": the artifact did not exist yet
at W1's probe time — reconciled, no drift. No test-tier issue (no tests
added); no process provenance in the diff beyond the DRY-mandated worker
sections. The six immaterial deltas above (two counts, one sentence, one
gloss, two downgrades) follow the querysets precedent: reconciled here,
not revision drivers. One minor test-side defect held for carding (D-W2-2).

Status: verified.

## Iterations

### Adjudication-1 (Worker 1) — stale-input re-review, `docs/TREE.md`

Scope: plan `docs/dry/dry-0_0_15.md`, `## Run 0.0.15 2026-09-21-2`,
`### Freshness reconciliation 2` row for this item. HEAD moved
`bfaee91d`→`69a25369` (three test/docs commits, zero package files —
re-verified: `git diff --name-only bfaee91d..69a25369` names no path under
`django_strawberry_framework/`). `ITEM_BASELINE=5830473eaa6cd813c741a4b25b70de8c4b7e7bc5`
(resolves). HEAD `69a253690002fdd413704a7879528c3ded363020` at start and end
(unmoved). Target blob still `0ef72601ecac300ac87ff993af1b04a4f1bc335a` at
HEAD. No production edits (file-item adjudication owes none); no probes were
needed — every question below is static-decidable from committed bytes, so no
scratch scope was created, no pytest run, no ruff scope (no `.py` added).

Re-hash (every recorded fingerprint, HEAD bytes via `git rev-parse HEAD:<path>`
prefix match over the 60-row inventory re-derived from all W1 Freshness rows +
W2 Phase-A fingerprints + V16): 59 match, stale set exactly `docs/TREE.md`
(recorded `cd075cbb6726`, HEAD `c0b0b909f0cb8332bef26a9e5cc035497b2f2173` —
the plan's landed blob, confirmed). The 7 W1 WORK rows: 6 paths have
HEAD-identical bytes across the range (routers, nested_planner, finalizer,
filters/base, types/base, tests/test_routers — W2's V2 intact-line mappings
preserved); the 7th, `tests/types/test_definition_order.py`, landed with bytes
byte-identical to the recorded WORK hash (`202f835c832f1`, full 13-char prefix
match on HEAD blob `202f835c832f19c7…`) — the concurrent dirt W1 verified
landed verbatim, so R1's "line 24 intact" claim is now HEAD-verified, not
stale. No other mismatch: no finding's scope reopens.

Causing range for `docs/TREE.md` (`git diff bfaee91d..69a25369 -- docs/TREE.md`):
5 hunks, 6+/7-, all at TREE.md lines 576+ (two duplicated generated-tree
sections): test_definition_order.py + test_resolvers.py description rewords
(x2), test_write_values.py description reword (x2), one deleted kanban
test_mutations.py row. Hunk-by-hunk against every recorded claim citing
TREE.md (artifact lines 856, 986, 1016, 1039-1040, 1102, 1206):

- Line 856 (Phase-A matrix 5, projection list) + line 1102 (reconciliation
  matrix 5, supplement): the cited ownership sentence —
  "including the package root's, which owns the public exports" — sits at
  TREE.md line 190 in BOTH revisions, byte-identical (`cmp` clean), outside
  every hunk. The "5x per-symbol lines" grouped with it live in GLOSSARY.md
  (5 hits), not TREE.md (0 hits); the GLOSSARY fingerprint matched, so they
  are untouched. CONFIRM both; no definition count, oracle role, or projection
  citation moves.
- Line 986 (D-W2-3 "(TREE.md)" authority for the "package root" reading):
  the line-190 sentence still establishes it, byte-identical; and the defect
  was already downgraded to an observation in reconciliation for reasons
  independent of TREE.md. CONFIRM (observation stands, no action).
- Line 1016 (probe outcomes, "read at HEAD") + lines 1039-1040 (freshness row)
  + line 1206 (reconciliation freshness set): the read is superseded by the
  re-read above with the same verdict. CONFIRM with refreshed fingerprint:
  `docs/TREE.md` HEAD `c0b0b909f0cb8332bef26a9e5cc035497b2f2173` (this
  paragraph is the refreshed pin; history above untouched).

Landed-basename sweep (all 48 range files vs the artifact): the only other
touches are (a) R1's `tests/types/test_definition_order.py` consumer site —
promoted to HEAD-verified above (line 24 is the root-`auto` import; body uses
throughout); (b) V13's existential "finds the literal in
`tests/optimizer/test_extension.py`" — 100 occurrences at HEAD (was 101),
claim survives; (c) kanban/KANBAN prose (consumer-schema list, rule-31 note)
— the kanban schema file and KANBAN.md are both unlanded, and the deleted
TREE.md row names only the kanban test file. No further claim affected.

`## Pending execution`: confirmed empty (no `proof:`/`gate:` owed; sharded/PG
inapplicable by construction, judged twice already) — nothing to run.
D-W2-2 (test-side exact-set pin, homed for closeout): both premise blobs
unchanged (`tests/rest_framework/test_soft_dependency.py` `ac2b38ae04f0`,
`tests/base/test_init.py` `4cc121057689` MATCH) — unaffected, still owed at
closeout in its recorded shape.

Family index: no definition count moved anywhere (zero package files in range;
the TREE.md delta is projection-only test-description prose). All 11 rows
(7 file-local + 4 rejected, no open families) stand — NO index-row change owed
to Worker 0.

Item diff: this artifact only (untracked) — the `Status:` line swap plus this
one EOF append; all prior bytes untouched (pre-edit sha256
`ceaa0f354afd41f85f53293f5afdca668574ac864f5af27d14e9307db394cf40`, 81352 B).
Dirt elsewhere is concurrent work, left alone. No stop condition met.

## Independent verification (Worker 2) — adjudication

Worker 2, File `__init__.py` adjudication-1, run `0.0.15 2026-09-21-2`.
Two-phase per clarification 1: Phase A below was written to
`docs/dry/temp-tests/dry-adjud-init-w2/phase_a_expectations.md` BEFORE opening
`## Iterations` (artifact read only lines 1–1237 in Phase A; scope verified
absent before creation), and is embedded here as recorded. Reconciliation
follows, then the verification job and verdict.

### Phase A (as recorded pre-read)

Worker 2, File `__init__.py` adjudication, run `0.0.15 2026-09-21-2`.
Recorded BEFORE opening Worker 1's adjudication record (`## Iterations` at
artifact lines 1238–1315 — NOT read; artifact read only lines 1–1237).
Scope `docs/dry/temp-tests/dry-adjud-init-w2/` verified absent before creation.

Tripwire: HEAD `69a253690002fdd413704a7879528c3ded363020` at start.
`ITEM_BASELINE=5830473eaa6cd813c741a4b25b70de8c4b7e7bc5` resolves (commit).
Range anchor `bfaee91dcd332a5f86250fff90ab21b377bc674e` resolves (commit).
Artifact `docs/dry/dry-file-__init__.md` untracked, 86281 bytes.

A1. Fingerprint re-hash at current HEAD (all recorded rows, both workers).
Method: `git rev-parse HEAD:<path>` prefix-compared against every recorded
`HEAD`/`WORK` prefix in artifact lines 1–1237, plus
`bfaee91d:<path>`-vs-`HEAD:<path>` movement check per path. HEAD-tagged rows:
60 checked → 59 MATCH (all unmoved across `bfaee91d..69a25369`), 1 STALE
(the "58/57" in the scope file's first draft was my summary-arithmetic slip;
the 60 per-line results underneath agree with W1 — see R-1):

- STALE: `docs/TREE.md` recorded `cd075cbb6726` → HEAD `c0b0b909f0cb`
  (moved in range; old prefix matches the diff `index cd075cbb..c0b0b909`).
  Expected refresh pin: `c0b0b909f0cb`.
- MATCH (59, all `unmoved-across-range`): target `0ef72601ecac`;
  `tests/base/test_init.py` `4cc121057689`;
  `tests/middleware/test_debug_toolbar.py` `dd6df61673fb`; all 14 sibling
  inits; `mutations/permissions.py` `54f770ae5aa1`; fakeshop `config/schema.py`
  `303ea2da9df1`; `TODAY.md` `9c6786222a74`; CHANGELOG `d4e1035554f1`;
  `pyproject.toml` `9be864937662`; `uv.lock` `6e8552ad5074`;
  `export_dry_review.py` `83e969d9c8e5`; `bug_hunt.py` `14e39585a2f6`;
  `GLOSSARY.md` `bc51debc54cf`; `test_walker.py` `5bbd7a567f04`; `apps.py`
  `8ae1a3a3b12f`; `optimizer/extension.py` `49667a9370ce`;
  `optimizer/walker.py` `9b111ed93895`; `single_parent_fetch.py` `e995270af9b2`;
  `types/resolvers.py` `f3341e6a9f52`; `consumers.py` `936210e2993d`;
  `extensions/error_policy.py` `16f475471a8b`; `extensions/debug.py`
  `bf25c1461113`; `schema.py` `c2e1b748c26c`; `_request_body.py` `a70571ff5b38`;
  `test_soft_dependency.py` `ac2b38ae04f0`; `tests/_soft_dependency.py`
  `7b28c07853d1`; spec-039 `cf78af93437b`; `utils/imports.py` `291ecedd30c7`;
  `scalars.py` `5e354042d405`; scalars example schema `90b37673bdff`; W2-only
  `connection`, `error_policy`, `extensions/resource_policy`, `list_field`,
  `optimizer/hints`, `permissions`, `relay`, `resource_policy`,
  `types/converters`, `types/relay`, `rest_framework/sets`,
  `rest_framework/serializer_converter`, `rest_framework/inputs`,
  `rest_framework/hook_context`, `utils/querysets`, `routers.py` (HEAD tag
  `a18c5001471d`). Full prefixes in the scope file.

WORK-tagged rows (7): recorded hashes are probe-time working-tree bytes, so the
adjudication check is HEAD-blob movement across the range. 6 package files
UNMOVED (routers, nested_planner, finalizer, filters/base, types/base, plus
`tests/test_routers.py`): every intact-line / absence claim stands on
identical HEAD bytes — expect CONFIRM. 1 LANDED:
`tests/types/test_definition_order.py` `7dd04d67ed4d` → `202f835c832f` — and
the landed blob EQUALS the recorded WORK hash `202f835c832f1` (the landed
commit incorporated exactly the dirty bytes W1 fingerprinted). R1's claims
verified at new HEAD bytes: line 24 byte-identical (the root-`auto` import);
`auto` consumption intact (6 remaining `field: auto` tests; only the
end-to-end finalization test was re-tiered away). Expect CONFIRM; a WORK→HEAD
tag refresh would be identical-bytes churn — acceptable either way, never a
revision driver.

Zero package blobs moved across the range (landed set contains no
`django_strawberry_framework/` path): no definition, consumer, or
enforcement-site claim is directly affected. Expect CONFIRM.

A2. `docs/TREE.md` diff, hunk by hunk (5 hunks, all prose). Recorded TREE.md
claims: exactly one cited line — the ownership line paraphrased as "package
root owns the public exports" (Phase-A matrix axis 5 + reconciliation),
located at TREE.md line 190 at HEAD ("...the package root's, which owns the
public exports..."). The "5x per-symbol supplement lines" live in GLOSSARY.md
(5 hits there, 0 in TREE.md; GLOSSARY MATCH) — not TREE.md claims at all.
H1 (`@@ -576`, copy 1): 2 comment rewords — no cited claim, expect CONFIRM.
H2 (`@@ -607`): 1 reword — expect CONFIRM. H3 (`@@ -624`): kanban
`test_mutations.py` row deletion, artifact never mentions that file — expect
CONFIRM. H4/H5 (copy 2): same rewords — expect CONFIRM. `grep public.export`
over the TREE.md diff: zero hunk lines touch the cited region. Expect:
findings CONFIRMed, TREE.md pin refreshed to `c0b0b909f0cb`. Note (plan
erratum, immaterial): the plan says "47 landed files"; the range holds 48
paths (stat + name-only agree).

A3. Landed-file sweep vs artifact mentions (all 48 basenames):
`tests/types/test_definition_order.py` (R1 claim + WORK row — holds verbatim,
expect CONFIRM); `tests/optimizer/test_extension.py` (prose V13 observation
only, never fingerprinted — still spells the literal 100x at HEAD, was 101;
the single touched line is a deleted import — observation stands, expect
CONFIRM, no action); other 45 landed files (incl. the `docs/feedback2.md`
deletion): zero mentions in lines 1–1237, no effect.

A4. Expected adjudication shape + verdict: W1 re-hashes all rows (59 MATCH +
TREE.md stale, refresh to `c0b0b909f0cb`); diffs TREE.md hunk-by-hunk against
the line-190 citation; CONFIRMs all 7 file-local rows + 4 rejections; notes
test_definition_order.py landed-with-identical-bytes (or misses it — the
plan's sweep did — in which case a supplement, still CONFIRM); leaves
`## Pending execution` empty; leaves D-W2-2 (closeout-homed; premises
unmoved) unaffected. Verdict expectation: `verified`, provided W1's record
reconciles (any delta gets an explicit R-item in Phase B).

### Reconciliation (every difference explicitly)

- R-1 (CORRECTION, mine, conceded): my scope-file draft summarized "58 HEAD
  checks (57 match + 1 stale)". The true count is 60 checks → 59 MATCH + 1
  STALE: my 60 per-line results agree with W1's "60-row inventory, 59 match"
  on every row — only my summary arithmetic was wrong. W1's count endorsed;
  the embedded Phase A above carries the corrected summary with this note.
- R-2 (agree): HEAD tripwire `69a25369` start→end, unmoved (both workers);
  `ITEM_BASELINE=5830473e` resolves (both); target blob `0ef72601ecac`
  (both).
- R-3 (agree): zero package files in range — verified independently by both
  (`--name-only` shows no `django_strawberry_framework/` path); range is 3
  commits (W1 stated, I verified `rev-list --count` = 3); 48 landed files
  (both caught; plan's "47" is an erratum, immaterial).
- R-4 (agree): TREE.md 5 hunks, 6+/7-, all at lines 576+ in the two duplicated
  generated-tree sections (my H1–H5 = W1's hunk list exactly); cited artifact
  line set identical (856, 986, 1016, 1039–1040, 1102, 1206).
- R-5 (agree, strengthened): line-190 ownership sentence byte-identical in
  both revisions — W1 via `cmp`, re-verified by me via `cmp` on
  `git show {bfaee91d,HEAD}:docs/TREE.md` line 190. Per-symbol lines:
  GLOSSARY 5 / TREE.md 0 (both, exact). D-W2-3's line-986 "(TREE.md)"
  authority stands on the intact line 190, and the downgrade rationale is
  TREE.md-independent (W1 explicit; my sweep consistent).
- R-6 (agree): refreshed pin `c0b0b909f0cb8332bef26a9e5cc035497b2f2173` —
  my full-blob `git rev-parse` matches W1's pin character-for-character.
- R-7 (agree): WORK rows — 6 unmoved paths identical on both lists (routers,
  nested_planner, finalizer, filters/base, types/base, tests/test_routers);
  `tests/types/test_definition_order.py` landed byte-identical to WORK
  `202f835c832f1` (both; I verified the full HEAD blob
  `202f835c832f19c79beda2508b3c0cf6fa5b913a`). R1 promoted to HEAD-verified.
  W1 did NOT miss it (my A4 hedge is moot — the plan's sweep did, W1 didn't).
- R-8 (agree): `tests/optimizer/test_extension.py` 101 → 100 literal
  spellings, V13 existential observation survives (both, exact; the one
  touched line is a deleted import). Kanban/KANBAN prose: schema + KANBAN.md
  unlanded (W1; consistent with my zero-mention sweep for the deleted row).
- R-9 (agree): `## Pending execution` stays empty (both); D-W2-2 unaffected
  with both premise blobs MATCH (`ac2b38ae04f0`, `4cc121057689` — in my
  re-hash too); no index-row change owed to Worker 0 (W1 explicit;
  consistent with my confirm-everything expectation).
- R-10 (agree): AGENTS.md prose rules on W1's hunks — the `## Iterations`
  append is DRY-mandated worker content, not process provenance; citations
  are paths + blob ids with per-cycle scratchpad line refs (allowed in
  `docs/dry/dry-*.md`); no tests added (none owed); no `.py` added, so no
  ruff scope (my scope likewise holds only `.md` — no ruff owed).

### Verification job

- Fingerprint agreement: 60/60 HEAD rows + 7/7 WORK dispositions agree
  between my blind re-hash and W1's record (R-1, R-6, R-7); every MATCH
  re-derived from `git rev-parse`, never copied.
- Artifact untouched except W1's hunks: PROVED. Reconstructing pre-edit bytes
  as (current lines 1–1236 with line 3 restored to `Status: verified`)
  yields exactly 81352 B and sha256
  `ceaa0f354afd41f85f53293f5afdca668574ac864f5af27d14e9307db394cf40` —
  W1's recorded pre-edit hash. So the Status-line swap + the blank-line +
  `## Iterations` append (current lines 1237–1315) are the ONLY changes; the
  hash match simultaneously confirms the pre-edit header was `Status:
  verified`. (First attempt at a 1237-line boundary missed by the junction
  blank line — 81353 B — which is itself consistent: the append owns its
  leading blank line.) Internal cross-checks agree: W1's cited artifact lines
  match my Phase-A reads; the "lines 1–721" run-2 citation reconciles with
  the 16-line D-W2-2 insert (738 − 16 = 722, off-by-one blank-line
  accounting, no mid-file edit).
- HEAD tripwire: `69a253690002fdd413704a7879528c3ded363020` at my start, at
  W1's start/end (per record), and at my finish — unmoved throughout.
- Pending execution (empty) and defect D-W2-2 (closeout-homed) unaffected
  (R-9). No new defect found by me. No pytest needed: every adjudication
  question was static-decidable from committed bytes (no scratch `.py`, no
  live probes, no ruff scope).

### Verdict

All findings CONFIRMed, all fingerprints agree, the artifact is byte-proved
untouched outside W1's two hunks, and nothing is owed to Worker 0 (no index
change, no new family, no new defect, no pending command).

Status: verified.

### Adjudication-2 (Worker 1) — scoped re-review, 11 stale inputs + WORK check

Scope: plan `docs/dry/dry-0_0_15.md`, `## Run 0.0.15 2026-09-21-3`,
`### Freshness reconciliation 3` row for this item + the
`### Adjudication-2 dispatch, File __init__.py` brief. HEAD moved
`69a25369`→`24e6b4d3` (11 commits, 4 touching this item's inputs:
`9350eb8d` policy canonicalization, `44712901` sliced-child refusal,
`fee87ac4` OrderSet seal move, `c87f4f98` FilterSet seal).
`ITEM_BASELINE=ce32f10fd6cfcbda604cc3d1acca10c4f96bbb2c` (resolves).
HEAD `24e6b4d3e74b104779225cd6bbff713880bc48e3` at start and end
(unmoved). Target blob still
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` at HEAD. No production
edits (file-item adjudication owes none). Main checkout off limits;
every fact below comes from `git show HEAD:` / `git grep HEAD` (the
worktree carries concurrent dirt) or from HEAD-pristine bytes extracted
under the probe scope. No pytest, no settings, no database; the
inspect command was never imported.

Probes (all read-only, re-derived under the fresh scope
`docs/dry/temp-tests/dry-adjud2-init-w1/` — the run-2
`dry-adjud-init-*` scopes did not survive the worktree move, so nothing
is replayed; `uv run ruff check` + `uv run ruff format --check` both
pass on the scope):

- `rehash.py` → 49/60 MATCH, exactly the 11 tabled STALE, zero
  unexpected; 7 WORK dispositions (6 unmoved, nested_planner MOVED as
  tabled). `ALL OK (60 rows + 7 WORK dispositions as expected)`.
- `census_head.py` → S1 single `getLogger`, S4 12 by-name statements,
  optimizer re-export + 4-sibling fan-out, per-file logger lines, S3
  code-hit set, test_walker +73 shift, GLOSSARY cites. `26/26 checks
  pass`.
- `import_graph.py` → AST import-module sets old-vs-new for all 10
  moved package files. `10/10 identical`.
- `eager_head.py` → HEAD-pristine `git archive` tree + one fresh root
  import (package `__file__` under the scope's `head-tree/`,
  first-party set 67 modules): orders/rest_framework/auth absent,
  `extensions.debug` present, optimizer `is` root logger. `ALL OK`.

Re-hash detail (blind containment): every recorded prefix re-derived
from `git rev-parse HEAD:<path>`, including TREE.md at its
adjudication-1 refresh (`c0b0b909f0cb`, MATCH). The 11 STALE are
exactly the plan's tabled set — no extra mismatch to report, so no
finding's scope widens silently. WORK rows: routers, finalizer,
filters/base, types/base, tests/test_routers all HEAD-unmoved across
the range (`a18c5001471d`, `77fd9a2dd229`, `ba52351c2844`,
`91c587477ff8`, `17842b601bca` at both ends); test_definition_order
HEAD `202f835c832f` at both ends (the landed-verbatim bytes);
nested_planner HEAD `0ad8ff5d0ee1`→`b4dfd4a6f610` (the tabled WORK
check — re-verified below, line 48 intact).

F2 (GLOSSARY `bc51debc→d3ef357c`) — CONFIRM. All 5 hunks examined:
`9350eb8d` H1 (`:24`, DEFAULT_* + DjangoErrorPolicyExtension
description rewords), H2 (`:838`, exact-type sentence), H3 (`:1124`,
masker built-FIRST), H4 (`:1571`, production-error-policy built-first);
`44712901` H5 (`:1555`, prefetch sliced-policy body re-render). The
cited version line sits at GLOSSARY.md:20, byte-identical at both
heads (it is the unchanged context line of H1); the 5 `Exported from
the package root` per-symbol supplements (lines 618/686/696/708/724)
are byte-identical; the PEP-562 entry (both lazy instances + opposite
`__all__` decisions + shared miss behavior) is byte-identical; the
re-export list keeps all 46 link targets (descriptions only reworded).
No hunk adds, removes, or renames a root-exported name, and the
changed prose (policy-template separation, exact-type close, slice
licence) touches no version/surface/logger claim. Pin refreshed to
`d3ef357c26ede6a5bd21d4290b394ade4eb987b4`.

F3 (logger rule) — CONFIRM, with two line re-pins. Hunks per file:

- test_walker (`5bbd7a56→1cbc2559`, `44712901`, 2 hunks, +73/−0): H1
  (`:19`) adds 3 import names (one new `nested_fetch` import line + 2
  walker names — test-only edges); H2 (`:1298`) appends 2 slice-policy
  tests. The file's 5 `import logger` lines (the by-name pattern F3
  rests on: `caplog.set_level("DEBUG", logger=logger.name)`) shift
  uniformly +73 (`1755/3491/3608/3752/4218` →
  `1828/3564/3681/3825/4291`); zero `getLogger`, zero package-name
  string spelling at either head. Nothing added or removed from any
  census. Pin refreshed to
  `1cbc25599e1cd2b4cc0c222b3edd7d9e8d87c1f2`.
- walker (`9b111ed9→e8d80005`, `44712901`, 6 hunks): H1 (`:14`) adds 2
  names to the existing `..utils.querysets` import (same module, no
  new edge); H2–H5 (`:417`–`:494`) add the `policy` parameter, the
  `_build_connection_child_queryset` seam, and comments;
  H6 (`:1616`) rewires one planner call to the seam. The logger line
  moves `:24`→`:26` (re-pinned; the +2 is H1's import-block growth),
  still `from . import logger`. No `getLogger` added. Pin refreshed
  to `e8d800052cc87ca77070290c4c2f396061259b81`.
- nested_planner WORK check (HEAD `0ad8ff5d→b4dfd4a6`, `44712901`, 1
  hunk at `:1073`, docstring-only): line 48 is `from . import logger`
  at both heads, byte-identical context. The W1 WORK row's "line 48
  intact" claim is now HEAD-verified.
- ext/error_policy (`16f47547→7ee4e9dd`, `9350eb8d`, 4 hunks at `:79`,
  `:206`, `:285`, `:452`): 1-for-1 `DEFAULT_ERROR_POLICY` →
  `_PACKAGE_ERROR_POLICY` renames (same module) + one comment reword.
  Line 81 `from .. import logger` intact (all hunks net-zero above
  and below it). Pin refreshed to
  `7ee4e9dda5b0d5b1a84effdf98d2175ae0dd11d6`.
- schema (`c2e1b748→19f90bf5`, `9350eb8d`, 4 hunks at `:60`, `:72`,
  `:463`, `:1075`): same-module policy renames only. Line 62
  `from . import logger` intact. Pin refreshed to
  `19f90bf55289d1ab31d5dc09236335e67037adc2`.

Re-derived censuses at HEAD bytes: S1 exactly 1 `getLogger` call
(target line 14); S4 exactly the reconciled 12 production `import
logger` statements (`_request_body:128`, `consumers:392`,
`extensions/debug:105`, `extensions/error_policy:81`,
`optimizer/__init__:26`, `optimizer/extension:72`,
`nested_planner:48`, `single_parent_fetch:49`, `walker:26`,
`schema:62`, `finalizer:63`, `resolvers:40` — the 3 remaining grep
hits are the target comment + optimizer docstring lines), all binding
the name `logger`; optimizer re-export (`from .. import logger` +
`__all__` member, module MATCH) fans out to the same 4 siblings;
S3 in-code string occurrences are exactly the logger call
(target:14) plus `apps.py::name` (apps.py:9; file MATCH, unmoved in
range — the disproof stands; zero single-quote spellings
package-wide; rest are comments/docstrings). No hunk in range
adds, removes, or renames a root-`logger` consumer or a `getLogger`
call, and no hunk touches the `apps.py::name` disproof.

W2 Phase-A census inputs (import-graph / logger-consumer /
import-hygiene claims) — CONFIRM each (ext/error_policy and schema
per above; the rest here):

- connection (`93e998f2→4894f90f`, `fee87ac4` + `c87f4f98`, 7 combined
  hunks at `:114`, `:1769`, `:1777`, `:1813`, `:1823`, `:1849`,
  `:1860`): `fee87ac4` introduced `_sidecar_steps` + the OrderSet
  seal wiring; `c87f4f98` added the filter kind,
  `_sidecar_visibility_policy`, and the FilterSet seal. The `:114`
  import hunk adds 7 names from the already-imported
  `.utils.querysets` module (same edge). No logger line touched
  (connection.py is and stays a non-consumer), no `getLogger`. Pin
  refreshed to `4894f90fb2963a44d25b0eabc649c67d04afa587`.
- error_policy (`fa94fcd9→1a19cd7d`, `9350eb8d`, 4 hunks at `:34`,
  `:45`, `:91`, `:130`): module-docstring template paragraph, one
  added name (`canonical_policy`) on the existing `.utils.policies`
  import, exact-type `__post_init__`, `_PACKAGE_ERROR_POLICY`
  constant + `resolve_error_policy` default swap. Non-consumer
  before and after; no `getLogger`. Pin refreshed to
  `1a19cd7d9c15964847ae21122b3032d27f60d546`.
- ext/resource_policy (`52084078→38801833`, `9350eb8d`, 2 hunks at
  `:103`, `:1271`): 1-for-1 `DEFAULT_RESOURCE_POLICY` →
  `_PACKAGE_RESOURCE_POLICY` renames (same module). Non-consumer
  before and after. Pin refreshed to
  `388018335b94c5765bf6d7f92b2a22f41b6a9b40`.
- list_field (`ce682d5f→21380eb7`, `fee87ac4`, 7 hunks at `:74`,
  `:93`, `:462`, `:1339`, `:1481`, `:1527`, `:1580`): dropped
  same-module names, `_require_orderset_class` /
  `_apply_orderset_{sync,async}` moved to querysets as
  `require_orderset_class` / `apply_orderset_{sync,async}`
  (imported from the already-imported `.utils.querysets`), 2
  docstring re-pointings, 2 call-site renames. Non-consumer before
  and after; no `getLogger`. Pin refreshed to
  `21380eb72364caef0da05ca3ee3f26c0134e3904`.
- resource_policy (`647133d2→4b69e974`, `9350eb8d`, 5 hunks at `:52`,
  `:433`, `:462`, `:861`, `:875`): docstring reword,
  `_PACKAGE_RESOURCE_POLICY` constant (via the already-imported
  `canonical_policy` — import edge pre-existing at old `:79`),
  `resolve_resource_policy` default swap, `policy_from_info` miss
  path + docstring. Non-consumer before and after. Pin refreshed
  to `4b69e974decbd45916bd55f444f4b5f86724a07a`.
- querysets (`96618fba→b68be0e3`, `fee87ac4` + `44712901` +
  `c87f4f98`, 10 hunks at `:2404`, `:2525`, `:2742`, `:2796`,
  `:2979`, `:2997`, `:3041`, `:3136`, `:3898`, `:4152`): the diff
  contains zero added/removed import lines and zero
  `getLogger`/`import logger` lines (mechanical grep over the
  diff). Non-consumer before and after. Pin refreshed to
  `b68be0e337d178fc703ca1ac2ff4144c1fd766a5`.

Import-hygiene absences (orders / rest_framework / auth) — CONFIRM.
Three independent legs: (a) AST import-module sets are identical
old-vs-new for all 10 moved package files (zero added/removed
module edges anywhere in range); (b) no added `import` line in the
whole range diff names orders/rest_framework/auth; (c) the live
HEAD-pristine eager census (67 first-party modules — the same count
as W1's P1) shows all three absent plus filters/testing/routers/
views absent and `extensions.debug` present, with the optimizer
logger identical to the root logger. The range moves no eager edge
the F7 row answers to.

MATCH-only findings — CONFIRM without re-review (plan rule): F1
(all 21 inputs MATCH: target, both oracles, 14 sibling inits,
mutations/permissions, fakeshop schema, TODAY, CHANGELOG); F4/F5
(target, both soft-dependency oracles, `_soft_dependency`,
spec-039, rest_framework init, utils/imports — all MATCH); F6
(target, extensions init, extensions/debug, test_init — all MATCH);
F7's prose leg (`auth/__init__.py` Decision-3 docstring — MATCH;
the P1 leg re-derived live above); R1 (target, filters init,
scalars, scalars schema MATCH; filters/base, types/base,
test_definition_order HEAD-unmoved); R2/R3/R4 (target,
rest_framework init, utils/imports, both oracles, routers HEAD
`a18c5001471d` MATCH; routers + test_routers HEAD-unmoved). No
definition count, oracle role, projection citation, or exclusion
hold moves in any of them.

D-W2-2 (test-side `_DRF_SOFT_EXPORTS` oracle gap) — CONFIRM
untouched, still closeout-homed: both premise blobs MATCH
(`test_soft_dependency.py` `ac2b38ae04f0`, `test_init.py`
`4cc121057689`; zero diff lines in either across the range), the
target + guard + table inputs MATCH, and the string
`_DRF_SOFT_EXPORTS` occurs zero times in the entire range diff. The
defect's recorded shape (one exact-set pin on the owning card)
stands as written.

`## Pending execution`: confirmed still empty (no `proof:`/`gate:`
owed; sharded/PG inapplicable by construction, judged twice
already) — nothing to run. Family index: no definition count moved
anywhere (the range adds no root-`logger` consumer, no `getLogger`,
no eager edge, no surface member; the GLOSSARY delta is
projection-only policy/prefetch prose). All 11 rows (7 file-local +
4 rejected, no open families) stand — NO index-row change owed to
Worker 0. Scratch custody: scope `dry-adjud2-init-w1/` (4 probes +
`head-tree/` extraction) retained for Worker 2.

Item diff: this artifact only (untracked) — the `Status:` line swap
plus this one EOF append; all prior bytes untouched (pre-edit
sha256 `54d7cb404364243496583fa4d10e04cc822ac700418e4da4315776db69051bb9`,
97529 B). Dirt elsewhere is concurrent work, left alone. No stop
condition met.

## Independent verification (Worker 2) — adjudication-2

Worker 2, File `__init__.py` adjudication-2, run `0.0.15 2026-09-21-3`.
Two-phase per clarification 1: Phase A below was written to
`docs/dry/temp-tests/dry-adjud2-init-w2/phase_a_expectations.md` BEFORE opening
W1's adjudication-2 record (artifact read only lines 1–1499 in Phase A;
`docs/dry/temp-tests/dry-adjud2-init-w1/` unopened — existence noted for
custody only), and is embedded here as recorded. Reconciliation follows, then
the verification job and verdict.

### Phase A (as recorded pre-read)

Worker 2, File `__init__.py` adjudication-2. Recorded BEFORE opening Worker 1's
adjudication-2 diagnosis. Scope `docs/dry/temp-tests/dry-adjud2-init-w2/`
verified absent before creation (`ls docs/dry/temp-tests/` first; no
collision). Tripwire: HEAD `24e6b4d3` at start; `ITEM_BASELINE=ce32f10f`
resolves; range `69a25369..24e6b4d3` = 11 commits; target
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` clean. Run-2 scope
`dry-adjud-init-w2/` EXISTS (name listing only, contents unopened) — confirms
the W2-brief correction of the W1-brief erratum; immaterial either way. Method:
`git rev-parse HEAD:` / `git show HEAD:` / `git grep HEAD` only (worktree dirt
ignored); no pytest, no settings, no database, no package import. Probes:
`rehash.py` (full 60+7), `census.py` (C1–C4).

A1. Blind full-table re-hash: **49 MATCH, 11 STALE** — every recorded prefix
equals the old-head blob in all 60 rows (prior pins exact). STALE set derived
independently: GLOSSARY `bc51debc54cf→d3ef357c26ed`, test_walker
`5bbd7a567f04→1cbc25599e1c`, walker `9b111ed93895→e8d800052cc8`,
ext/error_policy `16f475471a8b→7ee4e9dda5b0`, schema `c2e1b748c26c→19f90bf55289`,
connection `93e998f2c7ea→4894f90fb296`, error_policy `fa94fcd9e952→1a19cd7d9c15`,
ext/resource_policy `52084078ac16→388018335b94`, list_field
`ce682d5f7951→21380eb72364`, resource_policy `647133d23785→4b69e974decb`,
querysets `96618fba4eaf→b68be0e337d1`. WORK: 6 UNMOVED (routers `a18c5001471d`,
finalizer `77fd9a2dd229`, filters/base `ba52351c2844`, types/base `91c587477ff8`,
test_routers `17842b601bca`, test_definition_order `202f835c832f`) +
nested_planner MOVED `0ad8ff5d0ee1→b4dfd4a6f610` (the WORK check). Refreshed
full blobs: `d3ef357c26ede6a5bd21d4290b394ade4eb987b4`,
`1cbc25599e1cd2b4cc0c222b3edd7d9e8d87c1f2`,
`e8d800052cc87ca77070290c4c2f396061259b81`,
`7ee4e9dda5b0d5b1a84effdf98d2175ae0dd11d6`,
`19f90bf55289d1ab31d5dc09236335e67037adc2`,
`4894f90fb2963a44d25b0eabc649c67d04afa587`,
`1a19cd7d9c15964847ae21122b3032d27f60d546`,
`388018335b94c5765bf6d7f92b2a22f41b6a9b40`,
`21380eb72364caef0da05ca3ee3f26c0134e3904`,
`4b69e974decbd45916bd55f444f4b5f86724a07a`,
`b68be0e337d178fc703ca1ac2ff4144c1fd766a5`; nested_planner
`b4dfd4a6f61044c6b5dca6ed9fa07d74f52d846d`.

A2. Causing-range hunks per file (re-derived `@@` headers): GLOSSARY 5
(`-24/-838/-1124/-1555/-1571`; version line 20 byte-identical both heads,
outside every hunk); test_walker 2 (`-19` imports, `-1295` two new tests);
walker 6 (`-14` imports, `-415/-446/-457/-473` policy seam, `-1568`
call-site); ext/error_policy 4 (`-79/-206/-285/-452`, DEFAULT→_PACKAGE
swaps); schema 4 (`-60/-72/-463/-1075`, same swaps); connection 7
(`-114/-1769/-1777/-1813/-1823/-1849/-1860`); error_policy 4
(`-34/-45/-91/-130`); ext/resource_policy 2 (`-103/-1271`); list_field 7
(`-74/-93/-462/-1339/-1481/-1527/-1580`); resource_policy 5
(`-52/-433/-462/-861/-875`); querysets 10
(`-2404/-2525/-2742/-2796/-2979/-2997/-3041/-3136/-3898/-4152`);
nested_planner 1 (`-1073`, docstring-only). Logger lines: walker 24→26 same
text, ext/error_policy:81 intact, schema:62 intact, **nested_planner:48
`from . import logger` intact at BOTH heads**. Range-wide sweep: zero new
module edges (only name swaps/additions on pre-existing edges); zero new
edges to orders/rest_framework/auth. `class SyncMisuseError` still single at
querysets:119 both heads. All 15 root-re-exported names in the 8 stale
sources still defined at HEAD (checked each).

A3. Per-finding expectations: F1 CONFIRM (zero stale inputs, no re-pin); F2
CONFIRM + GLOSSARY re-pin; F3 CONFIRM + 4 re-pins, WORK row stands
re-verified; F4/F5/F6/F7 CONFIRM (all MATCH); R1/R2/R3/R4 CONFIRM (WORK rows
unmoved: routers `__getattr__` def at HEAD 533, filters/base:31 + finalizer:63
+ test_definition_order:24 re-read intact); census inputs CONFIRM + 8
re-pins; D-W2-2 unaffected (both premises MATCH), stays closeout-homed;
pending stays empty. Expected verdict: `verified` (plain).

A4. Census re-derivation (`census.py`, ALL OK): C1 exactly 1 `getLogger`
(`__init__.py:14`); C2 AST sweep over 117 package files, docstrings excluded
→ exactly 2 in-code literals (`__init__.py:14` + `apps.py:9`); C3 exactly 12
production `import logger` statements, all by name (walker:26, rest as
reconciled); C4 no eager root edge to orders/rest_framework/auth + WORK
intact lines green.

A5. Blindness: HEAD `24e6b4d3` at Phase-A start and end; lines 1500+
unread; W1 scope unopened; run-2 scope name-listed only; no worker-memory
read; no pytest/settings/database.

### Reconciliation (every difference explicitly)

- R-1 (agree): blind stale set identical — same 11 files, same recorded
  prefixes, all 11 refreshed full blobs character-identical, old pins exact
  in all 60 rows both sides (49 MATCH). WORK dispositions identical: 6
  unmoved with identical both-ends blobs + nested_planner
  `0ad8ff5d0ee1→b4dfd4a6f610`. TREE.md adjud1 refresh `c0b0b909f0cb` MATCH
  both sides.
- R-2 (agree): hunk coverage identical — per-file `@@` headers match on all
  12 files (5/2/6/4/4/7/4/2/7/5/10/1), logger-line outcomes match (walker
  24→26 re-pin, :81/:62/:48 intact), nested_planner hunk docstring-only.
  W1's per-commit attribution (4 commits touching this item's inputs;
  per-file mapping incl. connection `fee87ac4`+`c87f4f98`, querysets all
  three, GLOSSARY two) verified independently via per-file `git log` —
  exact.
- R-3 (agree): dispositions CONFIRM everywhere both sides, with identical
  re-pin sets (F2 1, F3 4, census 8 with ext/error_policy + schema shared).
  F1's 21-input MATCH count verified (target + 2 oracles + 14 siblings +
  permissions + fakeshop schema + TODAY + CHANGELOG). MATCH-only rule
  applied correctly to F1/F4/F5/F6/F7-prose/R1–R4.
- R-4 (agree): censuses. W1's three static probes re-run read-only with
  identical outputs (`rehash.py` ALL OK 60+7; `census_head.py` 26/26 incl.
  test_walker 5-line +73 shift `1755/3491/3608/3752/4218→1828/3564/3681/
  3825/4291`, GLOSSARY 5 supplements byte-identical at :618/:686/:696/:708/
  :724, PEP-562 7 lines identical, 46 re-export targets; `import_graph.py`
  10/10 SAME). My C1–C4 agree (1 call site; 2 AST literals; the same 12
  file:line statements; no eager edges). The live eager leg I re-derived in
  my own scope (`eager_w2.py`, pristine `head-tree-w2/`): 67 first-party
  modules, orders/rest_framework/auth absent, `extensions.debug` present,
  optimizer `is` root logger — identical to W1's `eager_head.py` claims.
- R-5 (W1 erratum, immaterial): W1's record repeats the W1-brief erratum
  ("run-2 `dry-adjud-init-*` scopes did not survive the worktree move") —
  `dry-adjud-init-w2/` DOES exist here (Phase-A record only, contents
  unopened by me). Immaterial per the brief: W1's fresh scope stands, nothing
  was replayed either way, no verdict impact.
- R-6 (scope note, immaterial): W1's `import_graph.py` covers 10 moved
  package files, omitting the 11th (`utils/policies.py`, not a fingerprinted
  input). Its range diff carries zero import-line changes (verified: 2
  hunks, body/docstring only), so the zero-drift conclusion extends to
  11/11. No revision driver.
- R-7 (agree): D-W2-2 closeout-homed intact — both premises MATCH, target +
  guard + table inputs MATCH, and `_DRF_SOFT_EXPORTS` occurs 0 times in the
  entire range diff (re-verified). Recorded shape stands.
- R-8 (agree): `## Pending execution` stays empty; sharded/PG inapplicable by
  construction (judged twice already); no index-row change owed (all 11
  rows stand, no open families).
- R-9 (agree): AGENTS.md prose rules on W1's hunks — the `plan`/`Worker`
  hits are DRY-mandated structural references (scope line, section heading,
  custody sentence), the same kind adjudication-1 passed; no
  audit/sweep/restored/hardening/previously/grader/feedback. Citations are
  `path::Symbol` + blob ids + per-cycle scratchpad line refs (allowed in
  `docs/dry/dry-*.md`). No tests added (none owed); no production/test file
  touched.
- R-10 (agree): ruff — `uv run ruff check` + `uv run ruff format --check`
  pass on W1's scope (verified read-only; 121 files formatted incl. the
  pristine extraction) and on my scope + the artifact (my 3 probes cleaned
  to green, re-run with identical outputs).

### Verification job

- Fingerprint agreement: 60/60 HEAD rows + 7/7 WORK dispositions agree
  between my blind re-hash and W1's record (R-1); every MATCH re-derived
  from `git rev-parse`, never copied.
- Artifact untouched except W1's hunks: PROVED. Reconstructing pre-edit
  bytes as (current lines 1–1498 with line 3 restored to `Status: verified`)
  yields exactly 97529 B and sha256
  `54d7cb404364243496583fa4d10e04cc822ac700418e4da4315776db69051bb9` —
  W1's recorded pre-edit size/hash. So the Status-line swap + the junction
  blank line + the `### Adjudication-2 (Worker 1)` append (lines 1499–1716)
  are the ONLY changes; the hash match simultaneously confirms the pre-edit
  header was `Status: verified`.
- HEAD tripwire: `24e6b4d3e74b104779225cd6bbff713880bc48e3` at my Phase-A
  start, Phase-A end, W1's start/end (per record), and my finish — unmoved
  throughout. Target blob `0ef72601ecac` unmoved.
- Item diff: this artifact only (untracked) — Status flip + two appends, all
  item-authored. Baseline-window other paths (`utils/strings.py`,
  `tests/utils/test_strings.py`, bug_hunt, plan) are hunt/Worker-0 bytes,
  out of item scope, untouched. No stop condition met.
- Pending execution (empty) and defect D-W2-2 (closeout-homed) unaffected
  (R-7, R-8). No new defect found by me. No pytest needed: the adjudication
  questions were static-decidable from committed bytes plus read-only
  fresh-interpreter censuses against pristine extractions (no settings, no
  database; the inspect command never imported).

### Verdict

All findings CONFIRMed, all fingerprints agree, the artifact is byte-proved
untouched outside W1's two hunks, both deltas (R-5, R-6) are immaterial, and
nothing is owed to Worker 0 (no index change, no new family, no new defect,
no pending command). Scratch custody: `dry-adjud2-init-w1/` (W1: 4 probes +
`head-tree/`) and `dry-adjud2-init-w2/` (W2: 3 probes + Phase-A record +
`head-tree-w2/`) retained; run-2 scope untouched.

Status: verified.
