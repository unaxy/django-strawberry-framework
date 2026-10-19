# DRY review: `logger-single-sourcing`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `logger-single-sourcing`. Provisional owner
`django_strawberry_framework/__init__.py::logger`. Seed sites
`django_strawberry_framework/__init__.py`,
`django_strawberry_framework/optimizer/__init__.py`; re-derived below,
not trusted. Prior records used only as rejected-candidate triggers:
[dry-file-__init__.md][dry-file-init] F1 (sole `getLogger`, identity test
as gate) and [dry-file-optimizer-__init__.md][dry-file-opt-init] F1/F2
(fourth intra-subpackage consumer, gate execution deferred here).

## System trace

Rule: the package logger object and its consumer-facing name. The name
is the key clients use in Django's `LOGGING` config dict, so the string
is public surface even though the object stays out of `__all__`.

Whole-package mechanism sweep (117 `.py` files under
`django_strawberry_framework/`, every file opened by the search):

- `logging.getLogger`: exactly 1 site,
  `django_strawberry_framework/__init__.py::logger` (the
  `logging.getLogger("django_strawberry_framework")` binding).
- `import logging` / `from logging import`: exactly 1 site (same file).
- `logger =` / `_resolver_logger =` module-level assignment: exactly 1
  site (same binding; the `_resolver_logger` name is an import alias,
  not an assignment).
- `Logger(` direct construction, `basicConfig`, `dictConfig`,
  `setLevel`, `addHandler`, `propagate` as code: 0 sites (remaining hits
  for `logging`/`propagate` are prose: "logging out", "error
  propagates", docstrings).
- `from ... import ... logger` code imports: 12 sites (census below).
  No subpackage `__init__` besides `optimizer/__init__.py` re-exports
  `logger`; no module builds the logger name by concatenation.

Roles:

- **Definition (1):**
  `django_strawberry_framework/__init__.py::logger`.
- **Re-export / consumer (1):**
  `django_strawberry_framework/optimizer/__init__.py` (`from .. import
  logger` + `__all__` entry; projection: its docstring paragraphs 1
  and 3).
- **Intra-subpackage consumers through the leaf, `from . import logger`
  (4):** `optimizer/extension.py` (`logger.debug`), `optimizer/walker.py`
  (`logger.debug` x2), `optimizer/nested_planner.py`
  (`logger.warning`/`logger.debug` advisory switch on `settings.DEBUG`),
  `optimizer/single_parent_fetch.py` (`logger.debug`).
- **Cross-subpackage consumers through the leaf path,
  `from ..optimizer import logger` (2):** `types/resolvers.py` (aliased
  `_resolver_logger`, the N+1-warning surfacing site; projection: its
  comment block stating the alias keeps the cross-subpackage origin
  explicit), `types/finalizer.py` (`logger.warning`).
- **Direct-root consumers, `from . import logger` / `from .. import
  logger` (5):** `schema.py`, `consumers.py`, `_request_body.py`,
  `extensions/debug.py`, `extensions/error_policy.py`.
- **Oracles (independent: they spell the contract without reading the
  definition):**
  `tests/base/test_init.py::test_logger_name_is_django_strawberry_framework`
  (spells the string), `::test_optimizer_subpackage_reexports_top_level_logger`
  (asserts `is` identity),
  `::test_package_defines_exactly_one_getlogger_call` (new in this
  change; see Findings), plus ~100 `caplog` behavior tests across
  `tests/` and `examples/fakeshop/test_query/` that pin the destination
  name `"django_strawberry_framework"` per emitted event (they follow
  `.name` where they configure capture, so they pin events, not the
  spelling; the spelling pin is the name test above).
- **Projections:** the root in-file comment ("exactly one source
  location"), the optimizer leaf docstring, the `types/resolvers.py`
  alias comment, the `types/__init__.py` dependency-direction prose
  (types consumes optimizer, one-way), spec-048 (log destination pinned:
  package logger at `ERROR`), spec-052 Decision 3 (a *future, different
  package* takes the name `"django_strawberry_debug"`; a new name for a
  new package, not a second definition here).

Connected sources read for judgment: every site file above (import
blocks plus one emission site each), `types/__init__.py` layering
prose, `tests/base/test_init.py` + `tests/base/__init__.py` in full,
`tests/rest_framework/test_dry_import_ratchet.py` (structural-gate
precedent: identity over grep), `scripts/prove_failability.py` (gate
instrument), `pyproject.toml` (ruff tier rules), spec-052 Decision 3
region. Upstream: none; the rule is package-internal.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Swept every subpackage `__init__`
   for logger re-export vocabulary: only `optimizer/__init__.py`
   re-exports it. All other subpackages consume the root directly or
   not at all. One rule, one leaf re-export, no second surface.
2. **Sync/async twins.** Logger acquisition has no colored pair.
   Emission calls live in both sync and async paths (notably
   `consumers.py`) but share the one handle. No twin definition.
3. **Derived rather than repeated knowledge.** The name string is passed
   once as a `getLogger` argument; every other spelling is a consumer
   (LOGGING configs, `caplog` destinations), an oracle (the name test),
   or a projection (comments, `apps.py` name, spec prose). Nothing
   derives or concatenates the name.
4. **Inverse / round-trip pairs.** None; no encode/decode of the logger.
5. **Contracts restated in another medium.** Media: code (1 definition +
   12 import sites + emission calls), oracles (name / identity /
   cardinality pins + event-level `caplog` suites live and package
   tier), projections (listed above), specs (048 destination, 052 future
   name). A change moves once at the owner; the rest follow by name.
   Counts taken at the definition only, every finding.
6. **Enforcement by omission.** Deliberate and contract-sourced:
   `logger` absent from root `__all__` (star hygiene; pinned by the
   exact-tuple oracle; owned by family `package-root-public-surface`,
   not this one); no second logger for any subpackage (one package, one
   logger; trigger below). No member lacks a guard its contract
   requires.

### Enumeration

Instrument: three vocabulary sweeps over the full 117-file package
population (`getLogger`, `import logging`/`from logging`,
module-level `logger =`/`_resolver_logger =`), plus a `from ... import
... logger` import census and a `Logger(`/`setLevel`/`addHandler`/
`basicConfig`/`dictConfig` absence sweep. Every hit is assigned above:
1 definition, 12 import sites (1 re-export + 11 consumers incl. the
alias), 0 second definitions, 0 derived spellings. The only
`getLogger(` in the package is the root binding.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Rename the logger string (e.g. `"djsf"`) | **1** (root binding). Leaf re-export + 11 consumer imports follow by construction (they bind the object, never the string). The name-test oracle moves deliberately as the spelling pin; `.name`-following `caplog` suites do not move. |
| C2 | Default handling at the definition (set a level, attach a handler) | **1** (root; nothing is set today: stdlib default `NOTSET`, propagate). Per-call-site emission levels (`debug`/`warning`/`error`/`exception`) are per-site behavior decisions, not this rule; e.g. retuning the N+1 advisory moves `types/resolvers.py` only. |
| C3 | Add a second named logger (e.g. an optimizer-only name) | **0 existing moved; 1 new decision point.** No second `getLogger` exists to move; a new name is a NEW rule with its own reason (spec-052's `"django_strawberry_debug"` for a different package is the precedent shape), not a move of this one. This count-0/1 split is what proves today's count is 1. |

## Findings

### F1 — logger single-sourcing (single-owned; gate-only cardinality addition)

- **Contract + variation.** The string `"django_strawberry_framework"`
  lives in exactly one source location; every in-package handle to the
  canonical logger composes it by name. Consumer-facing (the
  `LOGGING`-dict key), so the spelling is pinned, not just the object.
  No legitimate variation: one package, one logger.
- **Sites + roles.** As inventoried above: 1 definition
  (`django_strawberry_framework/__init__.py::logger`); 1 re-export
  (`optimizer/__init__.py`); 11 consumers (4 intra-subpackage, 2
  cross-subpackage incl. the `_resolver_logger` alias, 5 direct-root);
  oracles and projections as listed.
- **Challenges.** C1, C2 -> 1 definition; C3 -> 0 existing + 1 new
  decision point (proof of current count 1, not duplication).
- **Owner + lifetime (principle 7).** The package root stands: every
  legitimate consumer in any subpackage can import it without reversing
  a dependency or importing a sibling flavor for its machinery.
  Dependency direction wins over narrowness: the root already imports
  `DjangoOptimizerExtension` from the leaf, and `types/__init__.py`
  documents the optimizer/types one-way rule, so leaf-owning the logger
  would drag the optimizer subpackage into every importer's closure
  for a one-line binding. Host-module size is not a criterion.
  Principle 4: the only stored derivation is the module binding itself
  (`getLogger(name)` evaluated once at import, published as the module
  attribute, never mutated, never invalidated; validity = process
  lifetime; the registry singleton is stdlib's, not ours). No owner-held
  cache, no invalidation protocol owed. Anti-duplication mandates no
  new shared state, and none is added.
- **Migration.** Production: none (already single; zero production
  hunks). Tests: one structural gate added (below). No oracle rewritten
  (the two standing oracles are untouched; the new test scans source,
  it does not import the owner it checks).
- **Distinct behavior (stays separate, where recorded).** Emission-site
  levels stay per call site (C2). The `_resolver_logger` alias stays a
  consumer-side naming choice recorded at
  `django_strawberry_framework/types/resolvers.py` (cross-subpackage
  origin explicitness). `logger` stays out of root `__all__` while
  present in leaf `__all__` (star hygiene; owned by
  `package-root-public-surface`). A future second logger *name* for a
  distinct responsibility (spec-052 shape) is a new rule, not a member
  of this family.
- **Rejection carried by this finding.** The "second definition"
  candidate is rejected: the leaf re-export shares *identity* (`is`),
  not just spelling, with the root binding, so it is a consumer, not a
  second authoritative definition. Concrete contract difference: a
  second `getLogger("django_strawberry_framework")` call would be a
  second maintained spelling of the name with zero runtime divergence
  (singleton), while the re-export is one spelling composed by name.
  Reconsideration trigger: a second `getLogger` call appearing anywhere
  under the package (the new cardinality gate below fails on exactly
  that), or a subpackage adopting a distinct logger name with its own
  level/handling contract (that name becomes its own family row).
  Durable home: the root in-file comment plus the optimizer leaf
  docstring paragraph 3 (both already state the single-location rule;
  no prose edit owed).
- **Behavioral proof (`execution-verified`).** Disposable workspace copy
  of the live tree per [DRY.md][dry] "Tests" (docs/ excluded):
  `WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/logger-single-sourcing`.
  From inside `WS`, `import django_strawberry_framework` resolves to
  `.../dry-ws/logger-single-sourcing/django_strawberry_framework/__init__.py`
  and settings `DATABASES.default.NAME` resolves to
  `.../dry-ws/logger-single-sourcing/examples/fakeshop/db.sqlite3`
  (copy's own tree and database; never the shared tree). Baseline
  `tests/base/test_init.py` in `WS`: 12 passed, 0 pre-existing
  failures. Rename mutant (root string -> `"djsf"`): exactly
  `test_logger_name_is_django_strawberry_framework` fails. Duplicate
  mutant (behavior-preserving same-name `getLogger` hand copy pasted
  into the leaf): exactly
  `test_package_defines_exactly_one_getlogger_call` fails while all 11
  other rows pass, confirming the standing oracles are blind to the
  duplication (singleton) and the new gate is not. Both restores proved
  by `filecmp.cmp(shallow=False)` plus SHA-256 comparison. Rejects the
  wrong results "the re-export is a second logger", "a second
  same-name call diverges at runtime", "the identity test gates
  cardinality".
- **Structural gate.** Three oracles, each with its failing mutant:
  (1) spelling pin (fails rename; entry 1 above); (2) composition pin
  `optimizer_logger is logger` (fails retarget/deletion by reasoning;
  *passes* the same-name hand copy by construction, which is why (3)
  exists); (3) NEW cardinality pin
  `tests/base/test_init.py::test_package_defines_exactly_one_getlogger_call`
  (fails the hand copy; entry 2 above). The new gate's population is
  independently enumerated (`Path(package.__file__).parent.rglob("*.py")`,
  117 files, no hardcoded list); per-region identity (the one hit must
  be root `__init__.py`) + cardinality (exactly one); rejected parse
  failures (`unparseable` must be empty); AST-based so comments,
  docstrings, and import-style changes (`logging.getLogger` vs bare
  `getLogger`) neither satisfy nor break it. Negative controls run via
  [`scripts/prove_failability.py`][prove-script] in `WS` with
  `--scratch-root` outside both trees (manifest at
  `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/logger-manifest.json`;
  full report pasted in `## Implementation (Worker 1)`). Note on the
  runner's verdict labels: both entries report `**WEAKLY PINNED**`
  because each fails exactly 1 row. That label is a builder floor for
  boundaries owed many rows; here each boundary is one literal owed one
  row (a spelling; a count), and each mutant fails exactly its owning
  row with 0 errors and a green baseline, which is the exact pin, not
  a weak one. Recorded as judgment, not as a second run.
- **Coupling.** None. Production untouched; the one test addition reads
  source text and reaches no database, alias, or dialect decision
  (sharded/PG cells inapplicable by construction). No dependency on any
  other family or on the ledgered walker/D1 work.
- **Freshness.** Working-tree blob ids (`git hash-object`): root
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`, optimizer leaf
  `d400569adf8ba801ff2293b6abddfd414fa18858`, extension
  `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`, walker
  `9b111ed938951a073a9226ccbcfacabc3af981e8`, nested_planner
  `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04`, single_parent_fetch
  `e995270af9b213b7f931c03d7dc8f7c084819e1b`, types/resolvers
  `f3341e6a9f52659925762bce097033bac67e3b51`, types/finalizer
  `77fd9a2dd229eb9de5f29188c5058035d3606323`, types leaf
  `24e8ec204a781e2014565523cdcd97b840104cac`, schema
  `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`, consumers
  `936210e2993ddca4b77ffebf65e728f59d17079c`, _request_body
  `a70571ff5b3849afd01b6ae44e38416acdb27dd0`, extensions/debug
  `bf25c146111337ee0af590e7496b34c010c2f7be`, extensions/error_policy
  `16f475471a8b8295117640f7b14d949603d7bbc0`, tests/base/test_init.py
  `c65cf892ed2d2c01e2a1a0d98c5c8ade98d33fdf` (post-edit; pre-edit
  `4cc121057689409213beb5ec31772130cdacb975`), tests/base/__init__.py
  `713a215586ce97e5e3c1a5da4c4676f3b73aecf1`, pyproject
  `9be864937662d3932c1ba754c9b40877e4da2103`, spec-052
  `2cd287080d16f278901c780730a60b4046796ff9`. Excluded modules: all
  remaining 100 package files excluded on the strength of the three
  vocabulary sweeps (population 117 enumerated; hit lists above in
  full). Searched populations: package `getLogger`/`import
  logging`/`logger =`/`Logger(`/handler-config sweeps; tests/ +
  test_query/ logger-destination census (102 + 9 hits); standing-docs
  logger prose (GLOSSARY/README 1 hit each; TREE/KANBAN/TODAY/GOAL 0).
  Any fingerprint change reopens the finding.

No sub-rule decomposed: emission levels are per-site decisions and the
alias is consumer naming; neither is a shared rule, so Worker 0 owes no
new index row from this family.

## Defects

None. Every docstring/comment claim re-checked held: root "exactly one
source location" (one `getLogger` hit package-wide), leaf "sole
definition at root" + re-export contract, resolver alias rationale,
types-leaf one-way dependency prose, spec-048 destination pin. The leaf
docstring naming three intra-subpackage consumers while the sweep finds
four (`single_parent_fetch.py` same shape) was already ruled not-a-defect
by both prior items (no exhaustiveness claimed; consequent holds a
fortiori); re-checked, still holds, not re-filed. No guard missing on any
member: every consumer binds through an import that fails loudly if the
owner goes away. Nothing routed; consolidation depends on no repair.

## Pending execution

None for this item. Every executed proof is recorded above with its
workspace command and outcome (`execution-verified`); the one authorized
shared-tree focused run
(`uv run pytest tests/base/test_init.py::test_package_defines_exactly_one_getlogger_call --no-cov -n0 -q`)
passed (1 passed, 0.28s). Full-suite green and sharded/PG cells belong
to the final gate item, not this family: the production diff here is
empty and the new test reaches no database.

## Judgment

Single-owned rule, no duplication to consolidate: 1 authoritative
definition across the three change axes (C1, C2: 1; C3: 0 existing + 1
new decision point). The re-export is composition by name, rejected as a
second definition with its contract difference and trigger. The standing
gates covered spelling and composition but not cardinality (proven: the
hand copy passes both, singleton), so the item lands a gate-only
addition: one population-level cardinality pin with its negative
control executed. Zero production edits; one test added at the mandated
tier. Standard set as dispatched: proof where consolidation was claimed
(none owed), trigger where singularity is claimed (reconsideration
trigger + failing gate above).

## Implementation (Worker 1)

Tracked changes (item-scoped diff vs `ITEM_BASELINE`
`cbd7e705b395a6453ee562c8c08145e0d7e2e7a7`; `HEAD` is `bfaee91d`):

- `tests/base/test_init.py` (+33, no deletions):
  `test_package_defines_exactly_one_getlogger_call` plus its two
  stdlib imports (`ast`, `pathlib.Path`). Pre-edit target confirmed
  clean (`git diff HEAD -- <path>` empty; path absent from `git status`
  and from the plan's `## Owned changes` ledger, whose rows are the
  walker D1 fix + 2 live test files on untouched paths). Production
  targets confirmed clean the same way (empty diff vs `HEAD` for both
  `django_strawberry_framework/__init__.py` and
  `django_strawberry_framework/optimizer/__init__.py`).
- New untracked artifact: this file
  (`docs/dry/dry-rule-logger-single-sourcing.md`).

After the edit: `uv run ruff check --fix tests/base/test_init.py`
(3 fixed: branch merge into one `or` condition) then `uv run ruff
format tests/base/test_init.py` until `ruff format --check` and `ruff
check` both pass on the touched path. No `CHANGELOG.md` touch. No
commit. Concurrent dirt (10 package files, 8 test files, bug-hunt and
plan artifacts, untracked sibling `dry-file-*.md`) never edited,
reverted, or tidied; attributed by content as external where named.

Workspace failability report (run in `WS` via
`uv run --directory "$WS" python scripts/prove_failability.py
<manifest> --scratch-root <outside-both-trees>`; package `__file__`
and DB `NAME` verified as the copy's own before any verdict):

```text
[1/2] django_strawberry_framework/__init__.py::logger (name gate)
    -> **WEAKLY PINNED - revision-needed** (1 row)
[2/2] django_strawberry_framework/optimizer/__init__.py::logger
      (cardinality negative control)
    -> **WEAKLY PINNED - revision-needed** (1 row)
| 1 | name gate | mutation: root string -> "djsf" | **1** | 0 |
  scope: test_logger_name_is_django_strawberry_framework -n0 |
  restore: filecmp True; sha256 proved |
  failing: test_logger_name_is_django_strawberry_framework
  (baseline 1 passed, 0 pre-existing) |
| 2 | cardinality negative control | mutation: hand-copy getLogger
  into leaf | **1** | 0 | scope: tests/base/test_init.py -n0 |
  restore: filecmp True; sha256 proved |
  failing: test_package_defines_exactly_one_getlogger_call
  (baseline 12 passed, 0 pre-existing; other 11 pass on the mutant) |
```

Reading of the two `WEAKLY PINNED` labels: see Findings (one literal
owed one row each; exact pins, judged by hand as the runner requires).

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/logger-single-sourcing`
(includes its own `.venv`, created by the authorized run),
manifest
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/logger-manifest.json`,
scratch-root
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/logger-failability-scratch`.

Worker 0 rows: tick Family `logger-single-sourcing` (this artifact);
no new responsibility-index row (no sub-rule decomposed); append to
`## Owned changes`: `tests/base/test_init.py` — Family
`logger-single-sourcing` — `test_package_defines_exactly_one_getlogger_call`
(gate-only cardinality pin; production untouched).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[dry-file-init]: dry-file-__init__.md
[dry-file-opt-init]: dry-file-optimizer____init__.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[prove-script]: ../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-file-init]: dry-file-__init__.md
[dry-file-opt-init]: dry-file-optimizer____init__.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Run: 0.0.15 2026-10-01-9. HEAD `5c3496e0` (detached, intended).
ITEM_BASELINE `f05c9d5172500c32bc341a892dc3fcd4084e6e7b`.
Address `dry/loggersrc-w2/verify` (slot-2). This section was written from a
fresh trace at current bytes BEFORE reading `## Findings` below (see the
pre-exposure note at the end); reconciliation follows it.

### Own trace

Population: every `.py` under `django_strawberry_framework/`. Instruments:
literal `getLogger` sweep, regex sweeps for `Logger\(`, `get_logger`,
`import logger` / `logger as`, `logger.<level>` call sites, the
`"django_strawberry_framework"` literal, and `print(`/`logging.<level>(`
bypasses; import-execution in the shared venv; source mutation only in the
workspace copy.

Authoritative-definition census (mechanical, current bytes):

- `getLogger` CALLS package-wide: exactly 1:
  `django_strawberry_framework/__init__.py:14`
  (`logger: logging.Logger = logging.getLogger("django_strawberry_framework")`).
- No `Logger(` construction anywhere (the sole `Logger\(` hit is the
  annotation on that same line). No `get_logger`. No
  `from logging import getLogger` (no bare-Name call exists to find; the
  gate's predicate covers the shape anyway).
- Count of independently maintained logger-name definitions: 1.

Owner I would choose: `django_strawberry_framework/__init__.py::logger`.
Responsibility reasoning: the logger name is the consumer-visible key in
Django `LOGGING` config (public surface though absent from `__all__`), and
the binding order (logger before subpackage imports) is owned there too.
It is the narrowest module every legitimate consumer can import without a
cycle or a sibling-flavor import. Matches the responsibility-index row
`Canonical package logger + logger-before-subimports order` (file-local,
File `__init__.py`).

Re-export (rejection re-derived, not inherited):
`django_strawberry_framework/optimizer/__init__.py:26`
(`from .. import logger`, re-exported via `__all__`) is composition by
name, not a second definition. Contract difference: it declares no name
string, binds no new object (identity holds: the composition test asserts
`optimizer_logger is logger`), and carries no change axis of its own --
renaming the logger is one edit at the root; deleting the re-export breaks
consumers but changes no rule. Trigger that would make it a second
definition: it binding its own `getLogger`/`Logger` object or a divergent
name.

Consumers (every importer verified to call through the handle; all compose
by name):

- Direct from root: `_request_body.py:128`, `schema.py:83`,
  `consumers.py:375` (`from . import logger`); `extensions/error_policy.py:86`,
  `extensions/debug.py:109` (`from .. import logger`).
- Via the optimizer re-export: `optimizer/extension.py:73`,
  `optimizer/walker.py:30`, `optimizer/nested_planner.py:49`,
  `optimizer/single_parent_fetch.py:50` (`from . import logger`);
  `types/finalizer.py:63`, `types/resolvers.py:41` (as `_resolver_logger`)
  via `from ..optimizer import logger`.
- 11 production importing modules + the re-export itself. Each has >= 1
  `logger.<level>` / `_resolver_logger.<level>` call site (e.g.
  `single_parent_fetch.py:299`, `resolvers.py:385`, `finalizer.py:470`,
  `nested_planner.py:688`, `consumers.py:838`).
- Test consumers: `tests/base/test_init.py` (spelling + composition +
  cardinality pins); `tests/optimizer/test_extension.py`,
  `test_nested_index_advisory.py`, `test_walker.py` (caplog via
  `.name`, i.e. derived from the owner; the 3 literal spellings at
  `test_extension.py:2296,2439,2620` are independent oracles).

Challenges (definition counts per posited change):

- C1 rename the logger string: 1 definition (root line 14).
  `apps.py:15` (`name = "django_strawberry_framework"`) shares the token,
  not the contract (Django app-registry identity; a logger rename does not
  move it) -- excluded with reason. Prose mentions move as projections.
- C2 add a new logging consumer module: 0 new definitions (import by name).
- C3 change the level/message policy at a call site: 0 definitions
  (per-call-site decision; levels stay per site).
- C4 (adversarial) add a second `getLogger` with the same name: the rule
  stays one object (stdlib singleton) but the literal gains a second source
  location -- exactly what the cardinality pin guards. Executed mutant:
  pin fails with 2 hits (see Execution record).

Matrix discharge against the target's real surface:

1. Cross-flavor mirroring: no per-flavor logger exists; one package-wide
   handle. Clean.
2. Sync/async twins: logging calls are sync stdlib invoked from both
   colors; no twin of the RULE. Clean.
3. Derived knowledge: the literal occurs at the root definition, at
   `apps.py:15` (different contract, excluded above), and in prose
   (projections). No concatenation-derived second spelling. Clean.
4. Round-trip pairs: no encode/decode surface. Inapplicable with reason.
5. Other media: tests pin spelling (oracle), wiring (identity), and
   cardinality (source scan); docstrings project the rule. Oracle
   independence holds: the spelling test spells the literal itself, the
   composition test asserts identity, the cardinality test scans source.
   Clean.
6. Enforcement by omission: enumerated every `logger.` call-site module --
   all import the canonical handle. No `logging.<level>(` module-level
   bypass; the 4 `print(` hits are docstring probe recipes in
   `_strawberry_patches.py` / `_cross_web_patches.py`, not executed
   logging. Clean.

Leaf-docstring consumer note (re-judged fresh): the
`optimizer/__init__.py` docstring names 3 intra-subpackage consumers
(`extension.py`, `walker.py`, `nested_planner.py`); current bytes show 4
(plus `single_parent_fetch.py:50`, logging at `:299`). The docstring
states no exact count -- each named module does consume through the
re-export -- and its load-bearing claim (removing the re-export breaks
production siblings, not just tests) is STRENGTHENED by the 4th.
True-but-incomplete is not contradiction: still not-a-defect, no
`## Defects` entry.

Gate assessment: the standing gates pin value
(`test_logger_name_is_django_strawberry_framework`) and wiring
(`test_optimizer_subpackage_reexports_top_level_logger`) but not source
cardinality -- proven by the hand-copy mutant, which passes both by
construction (fresh private name; stdlib singleton) while the pin fails.
The cardinality pin is the right and only addition: population = every
package `*.py` (`rglob`, sorted), unparseable files reject loudly, exact
hit-list assert. No production edit owed: the owner was already single.

Pending execution: none owed -- every proof below executed. Cells:
default executed; sharded/pg inapplicable by construction (the gate scans
source text and asserts on strings; it reaches no database, alias, or
dialect decision).

Index row: NOT owed. The responsibility index already carries this rule
as file-local under File `__init__.py`
(`Canonical package logger + logger-before-subimports order`, owner
`__init__.py::logger`). A family row would duplicate it, and the Sept-19
siblings carry none. Endorsement: "none owed" (no text for Worker-0 to act
on). Revisited after reading `## Findings` in case W1 named sub-rules.

### Dirt attribution (`tests/base/test_init.py` vs HEAD)

- HEAD `4cc12105` -> WT `239648ed`. Diff = 2 hunks, +116/-0, matching the
  plan's `## Owned changes` adopted-orphan row
  (`logger-single-sourcing` + `version-single-sourcing`, 116+/0-) exactly.
- Hunk 1 (imports `ast`, `os`, `re`, `Path`): adopted -- the logger gate
  needs `ast` + `Path`, the version gate needs `os` + `re` + `Path` + `ast`.
- Hunk 2 (two test functions): adopted -- `test_package_defines_exactly_one_getlogger_call`
  (this item) + `test_package_defines_exactly_one_version_declaration`
  (sibling, ticked).
- Embedded in hunk 2: the scratch-name pin (`"shadow"`, `"temp-tests"`,
  `"worker-memory"` in the version gate's `skipped_dirs`): an OPEN
  maintainer decision, never resolved here. This item's verdict is
  INDEPENDENT of it (the logger gate scans `package_root` only, no
  `skipped_dirs`). Positions: keep = the version gate keeps skipping cycle
  scratch (else false hits / red gate); remove/re-home = closeout's call.
  Either way the logger verdict stands.
- (iii) unattributed: NONE. No STOP.
- Item-scoped diff vs ITEM_BASELINE on the three indexed paths: EMPTY
  (`git diff ITEM_BASELINE -- <paths>` prints nothing; the only name in
  the unscoped diff is the plan file's own dispatch record). No new edits
  since dispatch. Indexed production files clean at HEAD blobs `8b165672`
  (`__init__.py`) and `d400569a` (`optimizer/__init__.py`), confirmed by
  `git hash-object` vs `git rev-parse HEAD:`.

### Checks re-run by W2

- `uv run mypy`: clean, 119 source files.
- `uv run basedpyright`: 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_any.py`: 130 allowed `Any` uses at 90 sites.
- `uv run ruff format --check` + `uv run ruff check` on touched tracked
  paths: VACUOUS -- this item lands no tracked edits (artifact is
  untracked per-cycle scratch; raw `path:NN` allowed, no style cleanup
  owed).
- Banned provenance words (`plan`, `audit`, `sweep`, `restored`,
  `hardening`, `previously`, `worker`, `grader`, `feedback`) in the
  adopted logger gate (lines 49-77): NONE (whole-word grep clean). The
  whole file's single hit, `"worker-memory"` at line 102, sits in the
  sibling version gate's `skipped_dirs` -- the known scratch-name pin,
  already a closeout defect + open maintainer decision, not a new finding.

### Execution record

- Shared venv (`uv run`, worktree `.venv`, Python 3.14.2):
  `pytest tests/base/test_init.py --no-cov` -> 13 passed (includes the
  adopted logger gate, both standing gates, and the sibling version gate).
- Workspace `dry/loggersrc-w2/verify` (slot-2 copy; stdlib-only drivers,
  no package import): real gate body extracted from the copy's
  `tests/base/test_init.py` and exec'd with `__file__` stubbed to the
  copy -- pristine copy PASSES (`GATE-BODY PASS`, run
  `dry-20261001T062029-adf170`, copy fresh); after appending a
  behavior-preserving hand copy
  (`_w2_probe_logging.getLogger("django_strawberry_framework")` in
  `keyset.py`, run `dry-20261001T062033-4a7c15`) the same body FAILS with
  `hits == ['__init__.py', 'keyset.py']` (run
  `dry-20261001T062035-003ee8`, copy modified: 1, shared unmoved).
  Drivers: `/tmp/loggersrc-w2/gate_body.py`, `/tmp/loggersrc-w2/mutate.py`.
- Old-gates-pass half: executed stdlib probe (system `python3`, no repo
  interaction) -- `logging.getLogger(same-name)` returns the identical
  object, so the spelling and composition gates (which read unmodified
  modules; the mutant binds a fresh private name) necessarily pass.
- Substitution note: the full-pytest mutant leg inside the copy is
  impossible -- slots 1-3 venvs fail imports (`typing_extensions`
  missing in slot-2, observed) and `workspace.py` scrubs `VIRTUAL_ENV`,
  so the copy venv cannot be swapped for a healthy one and slot-4 cannot
  be selected (lowest-free allocation; this address is bound to slot-2).
  Substituted with real-gate-body exec + singleton probe per the
  run-9 childalias precedent; the unmutated leg ran green as real pytest
  in the shared venv. Shared-tree `keyset.py` re-verified mutant-free
  after the runs.
- Cells: default only; sharded/pg need no run (inapplicable by
  construction, stated above).

Pre-exposure note: before writing this section, a repo-wide
`_resolver_logger` grep surfaced 7 artifact line fragments (alias
mechanism mentions). Every count, pin, and verdict above was
mechanically re-derived at current bytes (commands + runs recorded
here), so the trace stands as independent evidence regardless.

### Reconciliation (W2 vs W1 `## Findings` -- every difference explicit)

- R1 F1 single-ownership + census: ENDORSED. W1: 1 `getLogger` at the
  root; 12 import sites (1 re-export + 11 consumers: 4 intra-subpackage
  incl. `single_parent_fetch`, 2 cross-subpackage incl. the alias, 5
  direct-root). Mine: identical counts at current bytes. Zero census
  drift (`single_parent_fetch` was already the 4th in Sept). Survives.
- R2 Owner + lifetime: ENDORSED. Same owner
  (`__init__.py::logger`); W1's principle-4 lifetime record adopted
  (module binding evaluated once at import, never mutated or
  invalidated, process lifetime; the registry singleton is stdlib's).
- R3 Challenges: ENDORSED (different but compatible sets; count 1 under
  both). W1 C1/C2 -> 1, C3 -> 0 existing + 1 new decision point. Mine
  C1 -> 1, C2/C3 -> 0, C4 adversarial -> pin. C2's premise re-swept
  fresh at current bytes: `setLevel`/`addHandler`/`basicConfig`/
  `dictConfig` 0 hits, `propagate` hits all prose, `import logging`
  still exactly 1 site (the root). Holds.
- R4 Re-export rejection: ENDORSED. Contract difference + trigger exact
  and still current (identity holds -- composition test green in the
  13-pass run; no second `getLogger`; no divergent name). W1's trigger
  text kept (gate-as-tripwire + distinct-name-becomes-own-row).
- R5 Matrix: ENDORSED all six axes. My axis-6 sweep adds the
  print/`logging.<level>` bypass census (4 docstring-recipe hits, not
  executed logging). W1's `__all__`-omission point concurs (verified:
  root `__all__` lacks `logger`, leaf `__all__` carries it; owned by
  family `package-root-public-surface`, not this one).
- R6 Gate-only addition: ENDORSED. Right tier (`tests/base/test_init.py`;
  unreachable from any GraphQL field, so `tests/` per AGENTS.md), right
  shape (rglob population, exact hit list, unparseable rejection), zero
  production edits (both indexed production files clean at HEAD blobs).
- R7 Structural gates + negative controls: ENDORSED with fresh
  re-execution. Cardinality mutant re-proven in substituted form (real
  gate-body exec pristine-PASS -> mutated-FAIL with 2 hits, runs
  recorded; singleton probe + by-construction argument for the
  non-logger rows: the mutant adds no `__version__` binding, no export,
  no observable state). Rename leg accepted by inspection at current
  bytes (test spells the literal, root binds the literal, suite green)
  -- discharged, not trusted from Sept. No `proof:` owed.
- R8 Leaf-docstring 3-vs-4 note: ENDORSED not-a-defect (independently
  re-judged; true-but-incomplete, load-bearing claim strengthened).
- R9 Defects none: ENDORSED. No `(Worker-2)` entries.
- R10 Pending execution none -> plain `verified`: ENDORSED. No `proof:`
  correctly remains; cells default-executed, sharded/pg inapplicable by
  construction (W1's cell reasoning judged sound).
- R11 No index row: ENDORSED ("none owed"; W1's "no sub-rule decomposed"
  concurs; the rule is already file-local under File `__init__.py`).
- R12 Freshness: Sept pins superseded by mine where they differ (root
  blob `0ef72601` -> `8b165672` by typing drift; population 117 -> 119
  by two untracked hunt files, verdict-neutral since the gate enumerates
  by rglob). Corroborations: leaf blob `d400569a` UNCHANGED since Sept;
  W1's test_init pre-edit pin `4cc12105` == current HEAD (adopted-dirt
  lineage confirmed). Differing pins are never staleness by themselves;
  every verdict above was re-derived at current bytes.

Non-disagreements (expected Sept-to-now deltas): run ids, baselines
(`cbd7e705` -> `f05c9d51`), blob pins, file counts, workspace
paths/instruments (Sept opencode dry-ws + `prove_failability.py` ->
slot-2 copy + gate-body exec; substitution forced by slots 1-3 venv
damage, recorded above). None touches a verdict.

W2 verdict: `verified` (plain). No revision candidates. Not blocked --
the scratch-name open decision is independent of this item (positions
recorded under Dirt attribution).

