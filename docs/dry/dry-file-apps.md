# DRY review: `django_strawberry_framework/apps.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, rejection
re-checked fresh against its trigger) or a file-local record. Zero production
edits; zero tracked files changed.

## System trace

Small target (47 lines, 3 top-level statements): the package's Django
`AppConfig` — `apps.py::DjangoStrawberryFrameworkConfig`. It DEFINES two
things: the app-loader identity (`name`, `verbose_name`) and the process-wide
upstream-patch dispatch (`ready()` driving the four `apply()` calls). It
ENFORCES nothing itself: every gate lives inside the patch modules'
`apply()`, every patch body lives in its own module. The file is a consumer
of the install lifecycle, not a second definition of it.

Connected code read for judgment, outside the item: `conf.py`
`::upstream_patches_enabled` + `UPSTREAM_PATCH_DEPENDENCIES` (full bodies
read); `tests/test_apps.py` (full read, 8 test functions / 14 collected
rows); `docs/SPECS/spec-021-apps-0_0_7.md` Slice 1 + Problem statement +
Current state + Goals + Non-goals (contract source for the identity,
negative-shape, non-export, and no-extra-hook rules);
`examples/fakeshop/config/settings.py` `INSTALLED_APPS` entry (consumer);
`examples/fakeshop/apps/kanban/apps.py` (the only other `def ready` in the
example tree — neighbor examined, different contract);
`django_strawberry_framework/__init__.py` (verified patch- and
config-free); the four sibling file artifacts
(`dry-file-_django_patches.md`, `dry-file-_strawberry_patches.md`,
`dry-file-_cross_web_patches.md`, `dry-file-_graphql_core_patches.md` —
their F1 sections re-check this target's dispatch from the owned side);
`views.py::_RawBodyRequestAdapter` + `testing/_wrap.py` (existence + import
shape only, to place the dispatch's consumers).

Excluded with reason: the four patch-module bodies (owned by their verified
artifacts; re-read only at the `apply` signature/gate/docstring level plus
probe-verified call-shape sweeps); `connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` (concurrent
dirt, left untouched; none is in this item's paths); filter / order /
mutation / form / rest_framework flavors (no patch or dispatch vocabulary —
the gate-call, owner-attr, and config-class sweeps below cover all 117
package files); PyPI-latest re-checks (retirement signals live in the
patch modules' own oracles, not here).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** All three sibling patch modules'
contracts compared via their verified artifacts' F1 sections (each read in
full) plus fresh probe-verified shape sweeps here: the owner-attr literal
occurs in exactly the four patch modules; `if not
upstream_patches_enabled("…")` call sites are exactly the four `apply()`
gates; `from .conf import upstream_patches_enabled` occurs in exactly the
four patch modules — never in `apps.py`. Same skeleton (gate, validate,
installed-check, install), different contracts per sibling artifact; the
shared skeleton stays rejected under the existing family (F1 — trigger
re-checked, see Findings). The only other `def ready` in the example tree
(`examples/fakeshop/apps/kanban/apps.py::KanbanConfig.ready`, importing
`.signals`) is a different app with a different contract (example
out of population; no patch vocabulary). No type / filter / order /
mutation / form / rest surface carries dispatch vocabulary.

**2. Sync/async twins.** Target has no async surface (AST: zero
`AsyncFunctionDef`, zero `Await`). `ready()` is sync by Django contract;
each `apply()` is sync; the Strawberry multipart twins and the graphql-core
nested helper are their modules' business, not this file's. Axis discharged
by absence, stated reason above.

**3. Derived rather than repeated knowledge.** The `name` literal is spelled
once in production (`apps.py::DjangoStrawberryFrameworkConfig.name`,
probe-verified single site for `verbose_name`; the `name` string's other
spellings are the consumer's `INSTALLED_APPS` entry and prose/doc references
— consumers and projections, listed never counted). The gate name is
composed by absence: `ready()` passes no dependency string anywhere (probe:
no `upstream_patches_enabled` / `APPLY_UPSTREAM_PATCHES` outside the
docstring), so there is no second spelling of the gate vocabulary to drift.
The four `apply as apply_<dep>` aliases are call-local bindings consumed two
lines below, never restated. No reconstructed copies found.

**4. Inverse / round-trip pairs.** No uninstall API exists anywhere in the
lifecycle (tests revert by `__dict__` identity restore; oracles, not a
second definition — recorded in every sibling artifact). Capture-at-import /
validate-at-apply is one per-module pipeline; `ready()` touches neither end
(it calls `apply()`, which owns both). The re-fire safety
(`config.ready()` twice) is the dispatch-level echo of each `apply()`'s
idempotence, pinned by the dispatch oracle — a consumer assertion, not a
second lifecycle.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target + the four `apply()` gates + `conf.py`
gate vocabulary); oracles that compose by name — `tests/test_apps.py` (8
functions / 14 rows: importability, subclass, name + verbose-name pin,
registry pickup, the 3-key negative-shape test, `ready` presence, the
revert-all-four dispatch + re-fire test, the double-reload reinstall test),
the four `tests/test_*_patches.py` lifecycle rows, `tests/base/test_conf.py`
gate-shape rows, the live transport rows for the request-hardening half;
projections (the module + class + `ready()` docstrings, the GLOSSARY
`AppConfig` entry, CHANGELOG entries, spec-021, TREE.md entries). Every
oracle restatement imports the module by name and pins behavior; none
respells the rule. The spec-021 "three appliers" wording is a
release-boundary historical record (0.0.7 carried one, 0.0.11 three, 0.0.15
four), not a live contradiction — the GLOSSARY entry names all four.

**6. Enforcement by omission.** Four deliberate omissions, each with a
contract source and a pinning oracle: (a) no gate in `ready()` — the gate
lives inside each `apply()` (both docstrings record this; per-module gate
rows + opt-out transport rows pin it); adding one would double-gate (C10,
refused). (b) no `label` / `default_auto_field` / `default` — spec-021
Decisions 2, 5, 8; pinned by the negative-shape test (which deliberately
excludes `ready` and `__doc__`). (c) no checks, signals, `DjangoType`
imports, or `finalize_django_types` call — spec-021 Goals 3–4 + Non-goals;
GLOSSARY prose-records the full "registers no … connects no … imports no …
does not call" list. (d) async / non-Django adapters need no dispatch entry
— the cross_web artifact scopes the patch to the Django sync adapter with
its own pinning oracle. No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **3 top-level statements** — plus, better than the minimum, every
`ClassDef` body member (4) and every `ready()` body statement (9). Every
member lands below; every challenge in `### Challenges` ends in a family row
or a file-local record.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (AppConfig purpose, one line) | (none) | projection, R6 |
| 2 | `from django.apps import AppConfig` (sole module-level import) | `AppConfig` | machinery for R2 |
| 3 | `class DjangoStrawberryFrameworkConfig(AppConfig)` | class + `__dict__` shape | R1–R5 |
| 3.1 | class docstring (one line) | (none) | projection, R6 (ruff D101) |
| 3.2 | `name = "django_strawberry_framework"` | app-label source | R2, file-local |
| 3.3 | `verbose_name = "Django Strawberry Framework"` | display name | R2, file-local |
| 3.4 | `def ready(self) -> None` (+ docstring, no-inventory discipline) | dispatch | R1, F1 |
| 3.4.1–4 | four function-local `from … import apply as apply_<dep>` | call-local aliases | R1/R5, F1 + file-local |
| 3.4.5–8 | four `apply_<dep>()` calls (django, strawberry, cross_web, graphql_core) | dispatch order | R1, F1 |

Rules: R1 upstream-patch dispatch (four imports + four calls, order,
function-locality, gatelessness, no inventory repetition — the consumer side
of the install lifecycle); R2 app-loader identity (`name` + `verbose_name` +
single-AppConfig discovery); R3 negative shape (the three forbidden keys);
R4 non-export posture (absence from the root surface); R5 deferred-import
discipline (module import pulls no patch module); R6 dispatcher-docstring
projection discipline. The plan's `## Responsibility index` already carries
`upstream-patch-install-lifecycle` (rejected) covering R1 and this target —
reused, not renamed. No other existing family owns a definition here (the
`package-root-public-surface` family owns the root manifest R4 only adjoins;
see the file-local record). No new family is named: R1 counts through F1,
R2–R5 each count 1 or 0 with no second site (challenges below).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 retirement | upstream fixes one patch (e.g. cross_web stops decoding) | **1** (that patch module deletes outright; `ready()` drops its two lines as consumer follow, listed not counted) | independent |
| C2 | R1 gate rename | `APPLY_UPSTREAM_PATCHES` key renamed | **1** (`conf.py` owns the key; each `apply` passes only its dependency name; `ready()` names no key) | independent |
| C3 | R1 fifth module | a fifth patch module arrives | **1** new lifecycle + `ready()` gains two lines as consumer (the recorded trigger's arrival shape, not a count owed today) | independent (see F1) |
| C4 | R1 order change | reorder the four calls | **1** maintenance point (four adjacent call lines, one function, one edit; patch modules untouched — no order dependence exists between them) | file-local |
| C5 | R2 identity rename | rename `name` (or `verbose_name`) | **1** (class attribute; the `INSTALLED_APPS` entry + registry oracle follow as consumer/oracle) | independent |
| C6 | R3 shape lift | set `label` (or another forbidden key) | **1** (class body; the negative-shape oracle moves, not a definition) | independent |
| C7 | R4 export | re-export the config from the package root | **0** definitions here (surface-manifest change at the root: one import + one `__all__` entry; the exact-tuple pin oracle moves as consumer) | file-local |
| C8 | R5 import hoist | move the four imports module-top | **1** (this file alone; the GLOSSARY function-locality sentence moves as projection) | independent |
| C9 | R1/R5 twin | an async `ready` twin | **0** moves — refused (Django calls sync `ready()`; no twin exists or is plannable) | refused |
| C10 | R1 gate-in-ready | add a gate around the dispatch in `ready()` | **0** moves — refused (gate lives in each `apply()` by recorded contract; double-gating couples the dispatcher to the vocabulary it deliberately does not spell) | refused |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
setup, no shared-tree pytest — the workspace recipe is for mutating proofs,
of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-apps/probe_w1.py
```

Output (`ALL OK`, 30 sections): 3-member module AST with kinds
(`Expr, ImportFrom, ClassDef`); sole module-level import is `AppConfig`; no
async surface; class bases; 4-member class body; both literals; the three
forbidden keys absent; `ready(self)` with a 9-statement body (docstring + 4
imports + 4 calls); import modules exactly the four patch modules; call
order django → strawberry → cross_web → graphql_core; no gate vocabulary in
the `ready()` code; population 117; gate call sites exactly the four
`apply()` gates with gate imports exactly the four patch modules; owner-attr
literal in exactly the four patch modules; the config class defined once
(the five other `…Config.ready` hits are `:meth:` docstring projections in
the patch modules); `__init__.py` mentions neither `apps` nor the config
class; `complete_list_value` single-sited to `_graphql_core_patches.py`;
`verbose_name` single-sited here; target blob `8ae1a3a3…`; item-baseline
diff empty. Two first-draft checks failed on probe precision (the `conf.py`
`def` + error-string self-mentions counted as gate "callsites"; docstring
`:meth:` references counted as class "sites") and were corrected to count
`if not upstream_patches_enabled("…")` lines and `class …` definitions —
both re-verified green, substance unaffected. Status:
`execution-verified` for every identity/count/shape/absence claim below.
Rejects the wrong results "a second dispatch site exists", "the gate is
spelled twice", "the config is defined twice", "the order differs",
"an async twin exists".

## Findings

No production edit is owed by a file item; the one family below is REUSED
from the plan (rejection re-checked fresh), the rest are file-local records.

### F1 — upstream-patch install lifecycle (existing family `upstream-patch-install-lifecycle`, status stays `rejected`)

- **Contract + variation.** The per-dependency install shape — gate by
dependency name, fail loud on drift, install idempotently, self-heal a
third-party revert, retain the replaced callable across reloads — repeated
as a skeleton in four modules with per-module validation depth and install
arity. This target holds the consumer side: one dispatcher calling four
`apply()` bodies by name, spelling no gate and no patch inventory.
Legitimate variation axes: which appliers dispatch, in which call order,
with what import locality.
- **Sites + roles.** *Definitions*: the four `_validate_upstream_shape`,
`_patch_is_installed`, `apply`, capture, and `_PATCH_OWNER*` triples — one
set per patch module (owned by the sibling artifacts). *Consumer* (this
target): `apps.py::DjangoStrawberryFrameworkConfig.ready` — four
function-local imports + four calls, deliberately repeating no patch
inventory (the dispatcher docstring says so; GLOSSARY repeats it as
projection). *Gate vocabulary, single-owned*:
`conf.py::upstream_patches_enabled` + `UPSTREAM_PATCH_DEPENDENCIES`.
*Oracles*: each module's `tests/test_*_patches.py` lifecycle rows,
`tests/test_apps.py` dispatch + double-reload rows (the revert-all-four
test owns the dispatch contract deterministically),
`tests/base/test_conf.py` gate-shape rows, plus the live transport rows.
*Projections*: each module's docstring (own bug inventory; django +
strawberry prose-record the delegator/reimplementer depth split), the
`ready()` docstring (pointer-only inventory), GLOSSARY dispatch/kill-switch
entries.
- **Challenges.** C1, C2 → 1 each; C3 → the trigger's arrival shape; C4 →
1 maintenance point in the consumer; C10 → refused.
- **Trigger re-checked fresh (not inherited).** The recorded trigger is "a
sequence-level change needed in two or more patch modules, or a fifth patch
module arriving with an identical install shape". Measured today: package
still 117 `.py` files (probe); `apps.py` still dispatches exactly 4
appliers in the same order (full read + probe); all four `apply()` bodies
re-read at gate level — still gate→validate→check→install with no logging,
locking, or ordering additions; capture strictness still differs per module
(exact ×3 vs prefix-match in graphql-core — the sibling artifacts' C8/C9
evidence, not re-litigated here). No fifth module, no sequence change:
the rejection stands on fresh evidence.
- **REJECTED shared form (unchanged):** one driver owning the
gate→validate→check→install sequence and the owner-mark machinery, plus —
considered and refused here — folding the dispatch into it (a dispatcher
that also owns validation depth would couple four disjoint retirement dates
to one call site; C1 deletes one module while the dispatcher drops two
lines by construction). Contract differences, this member's share: (a) the
dispatcher WRAPS nothing and REIMPLEMENTS nothing — validation depth is
per-upstream-contract in the modules (C2/C8 move one side without touching
the other); (b) per-dependency gates with independent outright deletion per
module (this dispatcher deletes lines; modules delete files); (c) the gate
key itself is already single-owned in `conf.py` (C2), so the only truly
shared token already has one owner. Reconsideration trigger unchanged.
Durable home: plan's rejected index row + the four sibling artifacts' F1
sections + this finding.
- **Owner + lifetime.** No new owner (rejected — each module keeps its
lifecycle; the dispatcher keeps its two-lines-per-module shape). No stored
derivation in this target (the four aliases are call-local, "not cached"
by construction); principle-4 fields for the modules' captures live in the
sibling artifacts.
- **Migration.** None (zero-edit item; rejection, not consolidation).
- **Distinct behavior.** The four lifecycles agree on skeleton, not on
contract: C1 retires one member without moving the others or the dispatch
order.
- **Behavioral proof.** `execution-verified` for dispatcher population +
call order + import locality + gatelessness (probe). `static-reviewed`
for per-module depth differences (four gate bodies read; full bodies in
the sibling artifacts) and oracle bodies (not run; no shared-tree pytest
per item rules). Rejects "a fifth dispatch site exists".
- **Structural gate.** The existing dispatch oracle
(`tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely`
— reverts all four to captured originals, drives `ready()`, asserts all
installed, re-fires) plus the double-reload reinstall rows. Negative
control (by construction, stated honestly): dropping any one dispatch line
fails the all-installed assertion deterministically; a shared driver would
pass every current behavioral oracle, so the rejection rests on
lifecycle/retirement contracts with the trigger above as the change
obligation, not on a behavioral gate.
- **Coupling.** None.
- **Freshness.**
`django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f`,
`django_strawberry_framework/conf.py`
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`,
`django_strawberry_framework/_django_patches.py`
`ba98f5859ec32971c3aa566c221bdc4db392e137`,
`django_strawberry_framework/_strawberry_patches.py`
`f77df3499eb96051d70055266a677ca3cde5b219`,
`django_strawberry_framework/_cross_web_patches.py`
`6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`,
`django_strawberry_framework/_graphql_core_patches.py`
`1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`,
`tests/test_apps.py`
`5ca8b62c53185343ebfec95315f59ec6104fc851`,
`tests/test_django_patches.py`
`e26a26099c12efb2e2cab1e324b73226eab5dd76`,
`tests/test_strawberry_patches.py`
`b431de7728769d24828b90ea59591fa7fb08af6c`,
`tests/test_cross_web_patches.py`
`70c16389aa5d2a14746dba1612c909263bffd822`,
`tests/test_graphql_core_patches.py`
`53dca51737e6163c09549d015713ebf9dfcdec88`.

### File-local records (no second site after the matrix)

- **R2 — app-loader identity.** `name` + `verbose_name` literals (C5 → 1;
the `INSTALLED_APPS` string in `examples/fakeshop/config/settings.py` is
the consumer typing the same string per spec-021 Decision 7, which forbids
changing it to the dotted config path; test spellings are oracles). The
`KanbanConfig` name/verbose_name pair is a different app's identity, not a
second spelling of this rule. The logger-name string
(`__init__.py::logger`) is a different rule with its own owner. Trigger: a
second consumer-facing spelling the package itself must keep in sync (e.g.
a dotted-path `INSTALLED_APPS` entry the package rewrites) would make it a
family. Freshness: target +
`examples/fakeshop/config/settings.py`
`e2ba51142ef2921163a7d3b8a880ed109df4e3a8` + `tests/test_apps.py` as in F1.
- **R3 — negative AppConfig shape.** The absence of `label`,
`default_auto_field`, and `default` from the class `__dict__` (C6 → 1;
C9 documents the refused twin). Contract sources: spec-021 Decisions 2, 5,
8; oracle: the consolidated negative-shape test (which deliberately
excludes `ready` and `__doc__`). `KanbanConfig.default_auto_field` is a
models-carrying example app's required setting, not a second site.
Trigger: a second AppConfig in-package would reopen the row, still
single-owned per app.
- **R4 — non-export posture.** The class is importable at
`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` and
absent from the package root (C7 → 0 definitions here; probe-verified both
halves). Contract source: spec-021 Decision 3 + Goal 5; oracle: the
exact-`__all__` pin in `tests/base/test_init.py` (adjoins the open
`package-root-public-surface` family, which owns the root manifest — this
row records the apps-side absence, not a membership claim). Trigger: a
second surface the config must stay out of would join this record.
Freshness: target + `django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`.
- **R5 — deferred-import discipline.** The four patch imports are
function-local, so importing `django_strawberry_framework.apps` outside
Django pulls in no patch module (C8 → 1; probe: sole module-level import
is `AppConfig`). The `conf.py` import-time signal wiring is the adjacent
opposite decision (import time, not `ready()` — spec-021 Current state
records why), not a second site of this rule. Trigger: a second deferred
import with the same "no Django needed" contract would make it a family.
Freshness: target (+ GLOSSARY projection sentence, prose).
- **R6 — dispatcher-docstring projection discipline.** The module, class,
and `ready()` docstrings name the four dependency owners but repeat no
patch inventory, pointing at each module's docstring as the single source
of truth instead. Projections with no second definition; the falsifiable
halves (four modules, four gates, default-on, idempotent re-fire) verified
against the bodies above. The three `:meth:` docstring references in the
patch modules are inbound projections of R1, not definitions. Trigger: a
second inventory spelling (rather than a pointer) would make it a family.

## Defects

None. Every claim checked while tracing held: the dispatch order matches
the GLOSSARY entry; all four captures are the live unmarked upstream
methods (sibling probes); each gate reads its own dependency name;
`__init__.py` mentions neither the patch modules nor the config class; the
`INSTALLED_APPS` entry is the bare package path per spec-021 Decision 7;
the spec-021 "three appliers" checklist wording is a 0.0.7-bound historical
record, superseded in-tree by the 0.0.11/0.0.14/0.0.15 applier arrivals the
CHANGELOG carries — not a live contradiction. Nothing routed to any owner.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
117-file sweeps, command in `### Challenges`) already ran green against the
shared tree; they mutate no source and open no database, so no workspace
copy was owed. No pytest was run in the shared tree, per item rules; oracle
bodies are `static-reviewed`. No `execution-deferred` items.

## Judgment

Backstop discharged: 3/3 `ast.Module.body` members enumerated plus all 4
class-body and all 9 `ready()`-body members, 10 challenges run, every rule
terminating in the one existing rejected family it belongs to
(`upstream-patch-install-lifecycle`, trigger re-checked fresh — still
rejected, no new row owed) or a file-local record (R2–R6) — no
consolidation owed, no defect found, no new family named. Zero-edit result
is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: the only family
this target touches is already indexed.

## Independent verification (Worker 2)

Trace provenance (expectation-first). Read in order before opening
`## Findings`: `AGENTS.md`, `docs/dry/DRY.md`, `docs/dry/worker-2.md`,
the plan item (`File apps.py`, `Run 0.0.15 2026-09-18-1`), the complete
target `django_strawberry_framework/apps.py` (47 lines, full read), the
item-scoped diff (`git diff 77f665224799521c6a35d1d7221c9928d4408053 --
django_strawberry_framework/apps.py` = empty, 0 bytes) plus
`git status --short` (target clean; concurrent dirt listed below left
alone), then connected sites: `django_strawberry_framework/conf.py`
(full read of `Settings` + `upstream_patches_enabled` + dependency set),
`tests/test_apps.py` (full read, 8 functions), the four patch modules at
gate level (`def apply`, `upstream_patches_enabled` call sites, gate
imports, ready docrefs) plus the `graphql_core` module head,
`django_strawberry_framework/__init__.py` (patch- and config-free),
`examples/fakeshop/config/settings.py` (`INSTALLED_APPS` consumer entry),
the GLOSSARY `AppConfig` entry (four-applier dispatch prose), the
`__all__` pin in `tests/base/test_init.py`, and the Worker 1 read-only
probe `docs/dry/temp-tests/dry-file-apps/probe_w1.py`. The section below
was drafted from that trace before `## Findings` was opened; the
reconciliation at its end names every difference found.

Own enumeration (independent `ast.parse` count). `ast.Module.body` = 3
(`Expr` module docstring, `ImportFrom` AppConfig, `ClassDef`
`DjangoStrawberryFrameworkConfig`). Class body = 4 (class docstring,
`name` assign, `verbose_name` assign, `FunctionDef ready`). `ready()` body
= 9 (docstring + 4 `ImportFrom` + 4 `Expr` calls). Matches the artifact
`### Enumeration` member-for-member; every member lands where the artifact
puts it (docstrings to R6, module import to R5 machinery, class shape to
R1-R5, literals to R2, `ready` + imports + calls to R1/F1). No member
unassigned, no hidden member.

Own sweeps (all 117 package files). `if not upstream_patches_enabled("`
= 4 callsites in exactly the four patch modules; corresponding gate
imports = 4; owner-attr literal in exactly the four patch modules; the
config class defined once (this target); `verbose_name` single-sited
here; `complete_list_value` single-sited to the graphql-core patch
module; root `__init__` mentions neither `apps`, `AppConfig`, nor the
config class. Population = 117. One wording note: the ready docref sweep
is 5 hits in 3 files (strawberry x2, cross_web x1, django x2;
graphql-core cites no ready ref). The probe text counts hits (5) while R6
says "three references" (files). Files-vs-hits phrasing only; both agree
all such refs are inbound projections, not definitions, and the missing
graphql-core inbound pointer is not a contract breach (no rule requires
every patch module to cite the dispatcher; the dispatcher docstring
already names all four). Substance holds.

Own sites, roles, counts, and owner choice. Definitions: each patch
module's install triple (validate, installed-check, `apply`, capture,
owner mark) owned per module; gate vocabulary
(`APPLY_UPSTREAM_PATCHES` key + dependency set + read rule) owned by
`conf.py::upstream_patches_enabled`. Consumer: this target's `ready()`
(four function-local imports + four calls, no gate, no inventory).
Oracles (independent, none reads from the owner it checks):
`tests/test_apps.py` pins literals directly, drives `ready()` through the
registry after revert-all-four and asserts the installed tuple, and
reinstalls after double reload; per-module lifecycle suites, gate-shape
rows, and live transport rows cover the dispatched behavior. Projections:
module/class/`ready()` docstrings, GLOSSARY dispatch entry (verified: names
all four appliers in order, function-locality, self-gating, no-inventory
rule, and the registers-no/connects-no/imports-no/does-not-call list),
CHANGELOG/spec/TREE entries. Counts per posited change, authoritative
definitions only: C1 retirement 1 (module deletes; dispatcher drops two
lines as consumer follow); C2 gate rename 1 (conf owns the key; `ready`
names none); C3 fifth module is the recorded trigger's arrival shape, no
count owed today; C4 order change 1 maintenance point in the single
consumer function; C5 identity rename 1 (INSTALLED_APPS entry is the
consumer); C6 shape lift 1 (negative-shape oracle moves, not a
definition); C7 root re-export 0 here (root manifest owns); C8 import
hoist 1 (this file alone); C9 async twin refused (Django calls sync
`ready()`); C10 gate-in-ready refused (would double-gate against the
recorded contract). Owner choice matches the artifact: no new owner, no
consolidation. `ready()` keeps loader identity plus dispatch; the gate
vocabulary stays in conf; install bodies stay per module. The existing
rejected family `upstream-patch-install-lifecycle` is the correct home
for R1 (re-checked fresh, trigger not met: still 117 files, 4 appliers in
order, no sequence-level change across modules, no fifth module); R2
identity, R3 negative shape, R4 non-export posture, R5 deferred imports,
R6 docstring discipline stay file-local with triggers as recorded. A file
item owes no production edit and none is demanded.

Matrix judgment against the real surface. Axis 1 discharged (sibling
contracts compared via artifacts plus fresh shape sweeps; the only other
example-tree `ready` is a different app/contract; no flavor surface
carries dispatch vocabulary). Axis 2 discharged by stated absence (zero
async nodes; sync `ready()` is Django's contract). Axis 3 discharged (name
spelled once in production; gate composed by absence; aliases call-local).
Axis 4 discharged (no uninstall API; revert-by-identity is oracle
machinery; re-fire safety is a consumer assertion). Axis 5 discharged
(oracles compose by name; the spec's older applier count is a
release-boundary record, GLOSSARY names all four). Axis 6 discharged (four
omissions each with contract source and pinning oracle; no member lacks a
required guard). No unsearched axis, no found consolidation excusing one.

Freshness re-hash (all match, no staleness): target `8ae1a3a3…`, conf
`c6ad46aa…`, django patches `ba98f585…`, strawberry `f77df349…`,
cross_web `6b3a7c35…`, graphql-core `1cd579fb…`, `test_apps`
`5ca8b62c…`, django-patches tests `e26a2609…`, strawberry tests
`b431de77…`, cross-web tests `70c16389…`, graphql-core tests
`53dca517…`, fakeshop settings `e2ba5114…`, root `__init__`
`0ef72601…`. Item-baseline diff for the target re-measured empty (0
bytes); working blob equals baseline, cycle member, and `HEAD`.

Negative control. The dispatch oracle reverts all four patches to
captured originals, asserts the all-`False` tuple, drives `ready()`, and
asserts all-`True` plus re-fire. Dropping any one dispatch line fails the
all-installed assertion deterministically; inspection of the oracle body
suffices and no shared-tree or workspace mutation was owed for this
existing gate. The rejection itself rests on lifecycle/retirement
contracts with the recorded trigger, honestly stated, not on a
behavioral gate a shared driver would also pass.

Pending execution: none owed, none listed; agreed. The probe already ran
green (read-only, no source mutation, no database); oracle bodies are
`static-reviewed` per item rules; no `execution-deferred` proof exists.
Coupling: none; agreed. `AGENTS.md` prose check: no process provenance,
symbol-path citations only, existing oracles at the mandated tiers
(package tests for loader/dispatch identity, live transport rows for
request-hardening effects), no changelog/pragma/review-tree/bulk-delete
issues. Concurrent dirt preserved untouched: `connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`. No tracked
`.py` edits, so no ruff run owed. No Worker 2 scratch files created (no
mutating proof owed); no shared-tree pytest run.

Reconciliation. Per-family agreement: F1 reuse-as-rejected (agree),
R2/R3/R4/R5/R6 file-local (agree each with trigger). Differences: only
the files-vs-hits phrasing in the ready-docref count (5 hits, 3 files),
substance identical. Zero defects found, zero pending execution.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
77f665224799521c6a35d1d7221c9928d4408053 --
django_strawberry_framework/apps.py docs/dry/dry-file-apps.md` is empty (0
bytes, re-measured after the probe runs); the working blob
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f` equals the item baseline, the
cycle baseline member, and `HEAD:` — the target is clean, so no hunk
attribution was owed. Before touching any path, the item-scoped paths were
verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt (`connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied. Dirt elsewhere left alone, not a stop. No
commit. Untracked scratch created (not tracked changes): this artifact
`docs/dry/dry-file-apps.md` and the read-only probe
`docs/dry/temp-tests/dry-file-apps/probe_w1.py` (`ALL OK`, 30 sections; no
source mutation, no DB, no shared-tree pytest). No ruff run owed (no tracked
`.py` edits; artifact is `.md` only).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
