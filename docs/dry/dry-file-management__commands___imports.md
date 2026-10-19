# DRY review: `django_strawberry_framework/management/commands/_imports.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenges, plus four
rejections. Zero production edits; zero tracked files changed.

## System trace

Target owns the CLI import-failure translation: bad management-command paths
become `CommandError` at one place instead of at each command. FRESH, 54
lines, 11 top-level statements, four `def`s, no class, no `Command`.

Plan's DRY-axis question answered: both commands compose this shim by name.
[export-schema][export-schema] calls only
`management/commands/_imports.py::import_module_symbol_or_command_error`;
[inspect-cmd][inspect-cmd] calls that helper plus
`management/commands/_imports.py::import_string_or_command_error`. Neither
command imports `django.utils.module_loading` or `strawberry.utils.importer`
directly (full reads of both modules; package-wide grep for
`module_loading|utils.importer|import_module_symbol|import_string` finds no
direct upstream-importer call in either command file). No inlined copy, so no
candidate family on that axis.

Upstream resolution owners read in the live `.venv` (Django 6.1,
strawberry-graphql 0.324.0): `django.utils.module_loading::import_string`
(dotted-path resolution; raises `ImportError` for bad paths) and
`strawberry.utils.importer::import_module_symbol` (`module[:symbol]`
resolution with default; raises `ValueError` on missing symbol,
`ImportError`/`TypeError` on bad modules). The shim consumes both by name and
owns what neither provides: the `(ImportError, AttributeError)`-to-
`CommandError` translation and the pre-import shape validation that catches
the `ValueError`/`TypeError` shapes the narrow catch would miss.

Whole-package sweep for a second translation site: three direct
`import_string` call sites exist, each read and each a distinct contract (see
RJ4): [sets-mixins][sets-mixins]`::LazyRelatedClassMixin.resolve_lazy_class`
(`ImportError` retry with bound-module prefix, else propagate),
[sessions][sessions]`::session_store_class` (broad catch to
`ConfigurationError`), [request-body][request-body]`::_require_boundary_before_csrf`
(no catch; startup chain build). None translates to `CommandError`.

Oracles read: [test-imports][test-imports] (15 tests pinning wrapping,
guards, and `ValueError` passthrough), [test-export-schema][test-export-schema]
and [test-inspect][test-inspect] (command-level twins through `call_command`).
Contract sources: [spec-022][spec-022] Decision 3 (shared-helper pin) and the
[spec-022-rationale][spec-022-rationale] Decision-3 note, plus the
[build-022][build-022] residual note recording the `79e2d117` extraction (so
`inspect_django_type` could share it) and the `61f6726c` pre-validation.
Projections: the [glossary][glossary] export-command entry (names the shared
selector validator), [tree][tree] `commands/` lines (render from the module
docstring), the sibling commands-`__init__` inventory (closest neighbor; this
helper has no `Command` and is discovery-excluded by its underscore prefix).

Excluded with reason: the dispatch-named concurrent dirt (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
IN-FLIGHT `filters/inputs.py` range hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus sibling
untracked `dry-file-*.md` artifacts were left untouched; none names this
rule and none is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The commands are the only CLI surface;
no sibling flavor re-implements import translation. Both command modules
compose the shim by name (full reads); the three direct `import_string`
sites carry non-CLI contracts (RJ4). Searched, not surfaced.

**2. Sync/async twins.** No `async def`, no `await`; the helpers are pure
import wrappers. No surface.

**3. Derived rather than repeated knowledge.** Each grammar's module path is
extracted once per entry (`split(":", 1)[0]` for selectors,
`rpartition(".")` for dotted paths) and the ORIGINAL string is passed to
validation and upstream. The selector split mirrors upstream's own split, but
only to feed the validator: posit an upstream grammar change and the local
extraction follows its owner (consumer, counted zero — see C5). The
`str(e)`/`from e` spelling shared with [export-schema][export-schema]`::Command.handle`
is addressed in RJ1. Otherwise searched, no second derivation.

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. No surface.

**5. Contracts restated in another medium.** [test-imports][test-imports] and
the two command-level twins are independent oracles (they assert messages,
`__cause__` identity, and `ValueError` passthrough; never read the owner's
internals — counted zero). [spec-022][spec-022] + rationale + [build-022][build-022]
are contract sources (ship-time pins and extraction history — counted zero).
[glossary][glossary] export entry, [tree][tree] lines, and module docstrings
are projections (a wording change here re-renders or redescribes there —
counted zero).

**6. Enforcement by omission.** Family enumerated: two commands by helper
need. `export_schema` needs the selector helper only and calls it; `inspect`
needs both helpers and calls both (selector for `--schema`, dotted-path for
`type`, dispatched on `"." in arg`). Every import failure on those paths
routes through the shim; the remaining inline `CommandError`s in both
commands are per-command diagnostics (not-a-`Schema`, empty `--path`,
ambiguity, unfinalized, `UNRESOLVED`), each a distinct rule enforced at its
own site. Upstream's non-`CommandError` shapes (`ValueError`/`TypeError`)
are covered by the pre-validation — that coverage is why the validator
exists. No gap.

### Enumeration

Instrument: `ast.parse` over the working tree, counting `ast.Module.body`
members — **11 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a file-local row or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (states the translation contract) | (none) | F1 |
| 2 | `from collections.abc import Callable` (R1 signature machinery) | `Callable` | F1 |
| 3 | `from typing import TypeVar` (R1 generic machinery) | `TypeVar` | F1 |
| 4 | `from django.core.management.base import CommandError` | `CommandError` | F1 |
| 5 | `from django.utils.module_loading import import_string` (upstream owner) | `import_string` | F4 |
| 6 | `from strawberry.utils.importer import import_module_symbol` | `import_module_symbol` | F3 |
| 7 | `T = TypeVar("T")` (R1 return-passthrough machinery) | `T` | F1 |
| 8 | `def import_or_command_error` | R1 | F1 |
| 9 | `def _validate_absolute_module_path` | R2 | F2 |
| 10 | `def import_module_symbol_or_command_error` | R3 | F3 |
| 11 | `def import_string_or_command_error` | R4 | F4 |

Rules: R1 translation core (statements 1–4, 7–8), R2 shape validation
(statement 9), R3 selector entry (statements 6, 10), R4 dotted-path entry
(statements 5, 11). No indexed family name applies (the plan's
`## Responsibility index` holds no import-translation row; the nearest rows
cover unrelated rules, e.g. `soft-dependency-require-guard` owns
`utils/imports.py` only); no new family is named (each rule is
single-definition, so Worker 0 owes four file-local index rows, one per
finding below).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 widen the catch to `ValueError` | consumer `ValueError` must become `CommandError` | **1** (statement 8; the four passthrough oracles fail — listed, not counted) | file-local |
| C2 | R1 drop the `from e` chaining | cause no longer preserved | **1** (statement 8; `__cause__`-identity oracles fail — listed) | file-local |
| C3 | R2 add a whitespace-only-module rejection | third malformed shape | **1** (statement 9; both entries follow as consumers) | file-local |
| C4 | R2 reword the empty-path message | different wording | **1** (statement 9; message-matching oracles fail — listed) | file-local |
| C5 | R3 change the colon-split grammar | e.g. accept a new selector suffix | **1** (statement 10; upstream's split owns resolution — the local split exists only to feed validation, consumer-follows-owner, counted zero) | file-local |
| C6 | R3 change the `"schema selector"` label | different label | **1** (statement 10) | file-local |
| C7 | R4 change the `rpartition(".")` grammar | e.g. require two dots | **1** (statement 11) | file-local |
| C8 | R4 drop the missing-module guard | `"schema"` with no dot reaches `import_string` | **1** (statement 11; the requires-module-path oracle fails — listed) | file-local |
| C9 | shared translate-any-exception spelling with [export-schema][export-schema]`::Command.handle` file-write branch | one `str(e)`/`from e` policy driver | rejected — RJ1 (disjoint populations) | rejection |
| C10 | one resolve-anything entry merging R3+R4 | callers stop dispatching by shape | rejected — RJ3 (disjoint grammars, upstream-distinct owners) | rejection |
| C11 | fold the three direct `import_string` sites into the shim | every `import_string` call translates to `CommandError` | rejected — RJ4 (non-CLI contracts) | rejection |
| C12 | merge with [utils-imports][utils-imports] soft-import helpers | one import-handling owner | rejected — RJ2 (library vs CLI error contracts) | rejection |

No executable proof was run: the target is pure string predicates plus
import delegation with no ordering, transactional, or async axis an
execution could distinguish (principle 8); the only instrument used
(`ast.parse`, read-only greps) is non-mutating. All claims below are
therefore `static-reviewed`; there is no `execution-deferred` proof, no
shared-tree pytest was run, and no `docs/dry/temp-tests/` scratch was
created.

## Findings

No production edit is owed by a file item; each finding records one rule
with the challenges that proved it has no second site.

### F1 — import-failure to `CommandError` translation (file-local)

- **Contract + variation.**
  `management/commands/_imports.py::import_or_command_error` runs a
  zero-arg importer, returns its value unchanged, and re-raises
  `(ImportError, AttributeError)` as `CommandError(str(e)) from e`.
  Legitimate variation: the caught population, the message/cause policy,
  the return contract.
- **Sites + roles.** *Definition*: statement 8 (machinery: statements 1–4,
  7). *Upstream failures consumed*: `django.utils.module_loading::import_string`
  (`ImportError`), `strawberry.utils.importer::import_module_symbol`
  (`ImportError`/`AttributeError`). *Consumers*: statements 10–11 (same
  file), both command modules by name. *Oracles*: [test-imports][test-imports]
  (passthrough, both wrappings with `__cause__` identity, non-swallow of
  `ValueError`), the command-level twins (behavior through the shim).
  *Contract source*: [spec-022][spec-022] Decision 3 + rationale.
- **Challenges.** C1 → 1 definition; C2 → 1 definition.
- **Owner + lifetime.** This file (narrowest cohesive owner every CLI
  consumer can depend on without reversing a dependency; library code
  cannot import it — hence RJ2/RJ4 stay separate). No stored derivation;
  no lifetime fields owed (each call re-runs the importer; module caching
  is upstream's lifetime, not this rule's).
- **Migration.** None (zero-edit item): the single owner stands.
- **Distinct behavior.** The narrow catch is intentional: a consumer
  module's own `ValueError` propagates unchanged (pinned oracles), and the
  pre-validation (F2) exists exactly to cover the `ValueError`/`TypeError`
  shapes the catch deliberately misses.
- **Behavioral proof.** `static-reviewed`. Rejects "a second translation
  site exists" (package-wide grep: the only same-population spelling is
  the file-write branch — RJ1) and "the catch should be wider" (the
  passthrough oracles contradict it).
- **Structural gate.** None owed beyond the existing oracles: they assert
  behavior (messages, cause identity, passthrough), never the owner's
  internals, and a hand copy of the body at a call site passes them (the
  copy is correct) — so a bespoke existence test per helper would be
  economy-violating (principle 9), same bar as the sibling inventory item.
- **Coupling.** None.
- **Freshness.**
  `django_strawberry_framework/management/commands/_imports.py`
  `05e9de80f388b9edecca9322db23f5cba614b4db` (working tree = `HEAD:` —
  target CLEAN). Consumers read in full: [export-schema][export-schema]
  `e27adae94ea38d7c0695e39ecd36bb8d6497695f`,
  [inspect-cmd][inspect-cmd]
  `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` (both working tree = `HEAD:`).
  Oracles read: [test-imports][test-imports] `2c56e75ed2e5e1a97b82775135f2b972f18a4ac8`,
  [test-export-schema][test-export-schema] `9727b17dabb2429269f7d8e49cc919ecff16f1ce`,
  [test-inspect][test-inspect] `76765d66ffdcef4e3760eccdeffe6f473cdb9b92`.

### F2 — absolute-module-path shape validation (file-local)

- **Contract + variation.**
  `management/commands/_imports.py::_validate_absolute_module_path`
  rejects an empty module path and a leading-`.` relative path before any
  import is attempted, each naming the offending value and the
  caller-supplied label. Legitimate variation: the rejected shapes, the
  wording, the label threading.
- **Sites + roles.** *Definition*: statement 9. *Consumers*: statements
  10–11 (labels `"schema selector"` / `"dotted object path"`).
  *Oracles*: [test-imports][test-imports] (both shapes on both entries),
  the command-level malformed-selector twins. *Projection*:
  [glossary][glossary] export entry (names the shared validator).
- **Challenges.** C3 → 1 definition (both entries follow as consumers);
  C4 → 1 definition.
- **Owner + lifetime.** This file (the validation exists only to serve
  the translation: upstream reports these shapes as unrelated
  `ValueError`/`TypeError`, so the rule cannot live upstream and neither
  command may own it without duplicating it — the exact duplication the
  `79e2d117` extraction removed). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Shape validation only; resolution stays with the
  upstream owners (F3/F4 delegation).
- **Behavioral proof.** `static-reviewed`. Rejects "each entry validates
  its own shapes" (both call this one body — full read) and "validation
  belongs at the commands" (that is the pre-extraction shape the build
  history records as removed).
- **Structural gate.** None owed (same economy argument as F1; the
  malformed-selector oracles at both tiers fail on bypass).
- **Coupling.** None.
- **Freshness.** Target + consumers + oracles as in F1; [glossary][glossary]
  `bcc99607a5557eeb1602d25676e4fb4e5b877da5` read as projection only.

### F3 — Strawberry selector resolution entry (file-local)

- **Contract + variation.**
  `management/commands/_imports.py::import_module_symbol_or_command_error`
  splits the module name off `selector` on `":"`, validates it (F2,
  `"schema selector"`), and delegates the full selector to upstream
  `import_module_symbol` with `default_symbol_name`, translated via F1.
  Legitimate variation: the grammar split, the label, the delegation.
- **Sites + roles.** *Definition*: statement 10. *Upstream grammar
  owner*: `strawberry.utils.importer::import_module_symbol` (resolution;
  consumed by name). *Consumers by name*:
  [export-schema][export-schema]`::Command.handle` (positional `schema`),
  [inspect-cmd][inspect-cmd]`::Command.handle` (`--schema`, first so types
  register/finalize before resolution). *Oracles*: resolve/default/wrap/
  no-mask rows in [test-imports][test-imports] plus the `--schema`
  selector twins in [test-inspect][test-inspect].
- **Challenges.** C5 → 1 definition (local split feeds validation only);
  C6 → 1 definition.
- **Owner + lifetime.** This file (the entry is the composition point the
  [spec-022][spec-022] Decision-3 pin names; neither command may own it
  without the other inlining a copy). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Selector grammar only; the dotted-path grammar is
  F4's, not a mode of this entry (RJ3).
- **Behavioral proof.** `static-reviewed`. Rejects "commands resolve
  selectors directly" (grep + full reads: no direct upstream call in
  either command).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + consumers + oracles as in F1.

### F4 — Django dotted-path resolution entry (file-local)

- **Contract + variation.**
  `management/commands/_imports.py::import_string_or_command_error`
  `rpartition(".")`s the module off `dotted_path`, rejects a missing
  module (`"a module path is required"` — a shape upstream reports as
  `ImportError`, but with a message that does not name the CLI contract),
  validates it (F2, `"dotted object path"`), and delegates to upstream
  `import_string`, translated via F1. Legitimate variation: the partition
  grammar, the missing-module guard, the label, the delegation.
- **Sites + roles.** *Definition*: statement 11. *Upstream grammar
  owner*: `django.utils.module_loading::import_string` (consumed by
  name). *Consumer by name*: [inspect-cmd][inspect-cmd]`::Command._resolve_type`
  (dotted `type` only; bare names take the registry path — the caller
  dispatches by shape before calling, so this entry never sniffs).
  *Oracles*: resolve/require/malformed/wrap/no-mask rows in
  [test-imports][test-imports] plus the dotted-path twins in
  [test-inspect][test-inspect].
- **Challenges.** C7 → 1 definition; C8 → 1 definition.
- **Owner + lifetime.** This file (same composition-point reasoning as
  F3). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Dotted-path grammar only (RJ3); the
  missing-module guard is this entry's own (no second site — C8).
- **Behavioral proof.** `static-reviewed`. Rejects "the guard duplicates
  upstream" (upstream's `ImportError` text names no CLI contract; the
  guard fires before any import).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + consumer + oracles as in F1.

### RJ1 — file-write `CommandError` shares only the spelling (rejected)

Considered: one `str(e)`/`from e` policy driver covering F1 and
[export-schema][export-schema]`::Command.handle` #"write_text" branch
(`(OSError, ValueError)` → `CommandError(str(e)) from e`). Contract
difference: import-failure population (operator named an unimportable
path) vs file-write-failure population (operator named an unwritable
path). Posit narrowing F1's catch → the write branch must not move;
posit rewording write failures with the path → import failures must not
move. Different reasons to change: same spelling, not the same rule.
Trigger to reconsider: a decision that every `CommandError` raising
shares one message/cause policy. Durable home: this clause.

### RJ2 — merge with `utils/imports.py` soft-import helpers (rejected)

Considered: one import-handling owner for
[management-commands-imports][management-commands-imports] and
[utils-imports][utils-imports]`::import_attr_if_importable` /
`::loaded_attr` / `::import_attr` / `::require_optional_module`.
Contract difference: library soft-lookup (returns `None` on
`ImportError`, or raises hint-carrying `ImportError`; `CommandError`
unavailable and meaningless outside a command) vs CLI failure (raises
`CommandError`, cause-chained, for an operator-facing path). Body read
of [utils-imports][utils-imports] confirms no `CommandError` and no
shape validation anywhere in it. Trigger to reconsider: a single
error-translation policy covering library and CLI surfaces. Durable
home: this clause.

### RJ3 — one resolve-anything entry merging R3+R4 (rejected)

Considered: a single helper taking either grammar. Contract difference:
Strawberry `module[:symbol]` (upstream owner `import_module_symbol`,
default-symbol contract) vs Django dotted path (upstream owner
`import_string`, missing-module contract) — disjoint grammars with
distinct upstream owners and distinct guards (F4's missing-module guard
has no selector analogue). Callers already dispatch by shape before
calling (`inspect` on `"." in arg`; `export` always a selector), so a
merged entry would add shape-sniffing — a mode flag no real path needs
(principle 5). Trigger to reconsider: callers stop dispatching by shape
and one grammar's guards become the other's. Durable home: this clause.

### RJ4 — fold the three direct `import_string` sites into the shim (rejected)

Considered: routing [sets-mixins][sets-mixins]`::LazyRelatedClassMixin.resolve_lazy_class`,
[sessions][sessions]`::session_store_class`, and
[request-body][request-body]`::_require_boundary_before_csrf` through F1/F4.
Contract differences, each read on strength of body: lazy-related
resolution retries with a bound-module prefix and otherwise propagates
`ImportError` (consumer-declared class reference, not an operator path);
session-engine resolution raises deployment-facing `ConfigurationError`
after `str`-flattening a hostile setting; middleware-chain comparison
lets `ImportError` propagate raw at startup. None can raise
`CommandError` (no command context) and none pre-validates shapes.
Posit changing the CLI wording → none of the three moves; posit
changing the `ConfigurationError` text → the shim does not move. Shared
upstream token, not a shared rule. Trigger to reconsider: a CLI surface
that resolves consumer-declared class references through a command.
Durable home: this clause.

## Defects

None. The module docstring matches its body (translation + both
grammars, no `Command`, correctly discovery-excluded); every upstream
non-`CommandError` shape is covered by F2; the narrow catch is
intentional and pinned; the axis-6 sweep finds no member lacking a
required guard and no import path bypassing the shim.

Note (already homed, not a new defect): the [kanban][kanban] DONE-029
residual observes the [glossary][glossary] introspection-command entry
owes the three rejections this file enforces on the `inspect` paths
(two shared shapes plus F4's missing-module guard). That entry is a
`GlossaryTerm` row with DB-backed remediation already described on the
board — owned there, so no `## Defects` entry is opened here.

## Pending execution

None. No `execution-deferred` proof: the target is pure string
predicates plus delegation to upstream importers, all branching already
pinned by oracles at two tiers asserting exact messages, cause identity,
and passthrough; there is no ordering, transactional, or async axis an
execution could distinguish (principle 8), and the only instruments used
(`ast.parse`, read-only grep) never mutate.

## Judgment

Zero-edit file item. 11/11 members assigned (F1–F4, all file-local with
proving challenges C1–C8 → 1 definition each); four rejections carry
contract differences + triggers (C9–C12 → RJ1–RJ4). No indexed family
name covers this rule and none is newly named. The plan's DRY-axis
question is discharged: both commands compose the shim by name
(consumer roles), nothing is inlined, and the three remaining direct
`import_string` sites are distinct non-CLI contracts, not second owners.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `78b3818852378e89dbf54a0965c6589b81f83a95`:
`git diff <baseline> --stat -- django_strawberry_framework/management/`
empty (exit 0, no output); `git status --short --
django_strawberry_framework/management/` empty — target CLEAN
(`05e9de80f388b9edecca9322db23f5cba614b4db` matches both
`HEAD:django_strawberry_framework/management/commands/_imports.py` and
the working tree). The artifact itself
(`docs/dry/dry-file-management__commands___imports.md`) is a new
untracked file, the item's only output. No `uv run ruff format .` /
`ruff check` run (no edits to format). The `## Owned changes` ledger
(walker D1 fix + 2 live test files) gains no row from this item. All
concurrent dirt (dispatch-named plus sibling untracked `dry-file-*.md`
artifacts) was left untouched. No scratch paths created
(`docs/dry/temp-tests/`, workspace copies: none).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Item baseline `78b3818852378e89dbf54a0965c6589b81f83a95`
(per dispatch); HEAD at verification `9031cb3d`. Reading order honored:
AGENTS.md, DRY.md, worker-2.md, the plan item, the target in full, both
consumers in full (`export_schema.py`, 62 lines; `inspect_django_type.py`,
call paths plus module docstring), `utils/imports.py` in full,
`tests/management/test_imports.py` in full, and the three rival
`import_string` bodies (`sets_mixins.py::resolve_lazy_class`,
`sessions.py::session_store_class`,
`request_body.py::_require_boundary_before_csrf`) — all before reconciling
against `## Findings` below. Worker 1's `worker-memory/` never opened.

### Own trace

The target owns one job: translate operator-facing import failures on
management-command paths to `CommandError` at a single composition point. I
decompose it, independently of W1's labels, into four rules:

- **T1 translation core** —
  `django_strawberry_framework/management/commands/_imports.py::import_or_command_error`
  runs a zero-arg importer, returns its value unchanged, and catches exactly
  `(ImportError, AttributeError)` as `CommandError(str(e)) from e`. Changes:
  widen the catch to `ValueError` → **1** definition (this body; the
  `ValueError`-passthrough oracles fail — listed, not counted); drop
  `from e` → **1** definition (cause-identity oracles fail). Owner I would
  choose: this file — the narrowest module both commands can import without
  reversing a dependency (library code cannot import a
  `management.commands` helper).
- **T2 shape validation** —
  `django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path`
  rejects an empty module path and a leading-`.` relative path with a
  value+label message, before any import. Changes: add a whitespace-only
  rejection → **1** definition (both entries follow as consumers); reword the
  empty-path message → **1** definition. Owner: this file — upstream reports
  these shapes as `ValueError`/`TypeError` the narrow catch misses, and
  neither command may own the check without duplicating it.
- **T3 selector entry** —
  `django_strawberry_framework/management/commands/_imports.py::import_module_symbol_or_command_error`
  takes `split(":", 1)[0]`, validates it (label `"schema selector"`), and
  delegates the full selector to Strawberry's `import_module_symbol` with
  `default_symbol_name`, via T1. Changes: grammar-split change → **1**
  definition (the local split feeds validation only; resolution is owned
  upstream — consumer, counted zero); label change → **1**. Owner: this
  file — the composition point neither command may own.
- **T4 dotted-path entry** —
  `django_strawberry_framework/management/commands/_imports.py::import_string_or_command_error`
  takes `rpartition(".")`, enforces the missing-module guard (`"a module path
  is required"`), validates (label `"dotted object path"`), and delegates to
  Django's `import_string` via T1. Changes: partition-grammar change → **1**;
  drop the missing-module guard → **1** (the requires-module-path oracle
  fails). The guard is T4's own: upstream reports that shape as `ImportError`
  without CLI contract, and the guard fires pre-import — no second site.
  Owner: this file.

Composition by name (verified by full reads + grep, not by W1's word):
[export-schema] imports only `import_module_symbol_or_command_error` and
calls it once (its `handle`); [inspect-cmd] imports both helpers and calls
the selector helper for `--schema` and the dotted helper for a dotted `type`,
dispatching dotted-vs-bare on `"." in arg` before calling (so T4 never
sniffs). Neither command file imports `django.utils.module_loading` or
`strawberry.utils.importer` in code (the `inspect` docstring's two prose
mentions are projections). No inlined copy anywhere. The three remaining
direct `import_string` sites each carry a non-CLI contract read on strength
of body (see RJ4). Reconciliation: T1–T4 coincide exactly with W1's R1–R4,
including counts and owners. No difference.

### Enumeration (member-by-member)

Own instrument: `ast.parse` over the working tree, `len(ast.Module.body)` =
**11** — matches W1. Walked each: (1) module docstring → F1 machinery
(agree); (2) `Callable` import → F1 (agree); (3) `TypeVar` import → F1
(agree); (4) `CommandError` import → W1 books to F1: strictly this import
serves all four `def`s (F2 and the T4 guard raise `CommandError` directly,
the entries via F1/F2) — observation only, outcome unchanged (see below);
(5) `import_string` import → F4 (agree); (6) `import_module_symbol` import →
F3 (agree); (7) `T = TypeVar("T")` → F1 (agree); (8–11) the four `def`s → F1,
F2, F3, F4 respectively (agree). 11/11 assigned, none by sample; the (4)
bookkeeping note changes no family/index outcome because every rule is
file-local to the same file with no second site. Coverage + assignment
valid.

### Counts, roles, oracles

Challenge counts C1–C8 each = 1 authoritative definition — re-derived above
(T1–T4) and agreeing in every row, including C5's consumer-follows-owner
zero-count for the local colon split. Roles: definitions = statements 8–11
(+ machinery); consumers = statements 10–11 internally + both command
modules by name; oracles = [test-imports] (15 tests: passthrough, both
wrappings with `__cause__` identity, `ValueError` non-swallow twice, both
guards on both entries, resolve/default/require rows) plus the command-level
twins in [test-export-schema] and [test-inspect]; contract sources = spec-022
Decision 3 + rationale + build-022 extraction notes; projections = the
[glossary] export entry, [tree] `commands/` lines, module docstrings, and
the sibling commands-`__init__` inventory note. Oracle independence verified
by reading the test bodies: they assert messages, cause identity, and
passthrough through the public helpers and never read owner internals. No
oracle rewritten. Agree.

### Equivalence (principle 8) and zero-edit

No production edit owed or made: I reproduced the item-scoped check myself —
`git diff 78b3818852378e89dbf54a0965c6589b81f83a95 --
django_strawberry_framework/management/commands/_imports.py` empty (exit 0,
no output) and `git status --short` shows no entry under
`django_strawberry_framework/` for this item (only the untracked artifact
itself). Target blob `05e9de80…` equals both W1's record and
`git show HEAD:<target>`. Observable behavior is therefore identical by
construction; no ordering, transactional, or async axis exists in a pure
string-predicate + delegation shim (no `async def`/`await`), and every
branch is pinned by oracles at two tiers asserting exact messages, cause
identity, and passthrough. No executable probe owed: W1's "NO probe — inline
analysis" is adequate for this 54-line surface, and as a file item I route
candidates rather than demand edits — there are none, every rule being
single-definition and the only same-population spellings considered being
the four rejections below.

### Rejections

- **RJ1** (file-write `CommandError` shares only the spelling): endorse.
  Contract difference is real — `(ImportError, AttributeError)`
  operator-path population vs `(OSError, ValueError)` file-write
  population; narrowing T1's catch must not move the write branch and
  rewording write failures must not move import failures. The trigger (a
  decision that every `CommandError` shares one message/cause policy) is the
  correct reconsideration condition. Durable home "this clause" accepted for
  a zero-edit file item: a docstring-clause edit would itself be a
  production edit the item does not owe; Worker 0 carries the trigger in
  Outcomes.
- **RJ2** (merge with [utils-imports]): endorse. Read
  [utils-imports] in full: soft-lookup / best-effort / loaded-only / strict
  plus hint-carrying `ImportError`; no `CommandError` and no shape
  validation anywhere in it. Library-vs-CLI error contracts are disjoint
  (`CommandError` is meaningless outside a command). Trigger adequate.
- **RJ3** (one resolve-anything entry): endorse. Disjoint grammars with
  distinct upstream owners and distinct guards (F4's missing-module guard
  has no selector analogue); callers already dispatch by shape, so a merged
  entry adds shape-sniffing — a mode flag no real path needs (principle 5).
  Trigger adequate.
- **RJ4** (fold the three direct `import_string` sites): endorse — each body
  verified myself: `resolve_lazy_class` retries with a bound-module prefix
  else propagates `ImportError` (consumer-declared class reference);
  `session_store_class` broad-catches to deployment-facing
  `ConfigurationError` after hostile-setting flattening; startup chain-build
  lets `ImportError` propagate raw. None can raise `CommandError`; a CLI
  wording change moves none of them. Shared upstream token, not a shared
  rule. Trigger adequate.

W1 names no new families; correct — each rule is single-definition and each
rejection keeps its sites separate.

### Fingerprints (re-hashed by me)

- Target `05e9de80f388b9edecca9322db23f5cba614b4db` — matches W1; equals the
  `HEAD:` blob (target CLEAN).
- [export-schema] `e27adae94ea38d7c0695e39ecd36bb8d6497695f` — matches.
- [inspect-cmd] `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` — matches.
- [test-imports] `2c56e75ed2e5e1a97b82775135f2b972f18a4ac8` — matches.
- [test-export-schema] `9727b17dabb2429269f7d8e49cc919ecff16f1ce` — matches.
- [test-inspect] `76765d66ffdcef4e3760eccdeffe6f473cdb9b92` — matches.
- [glossary] `bcc99607a5557eeb1602d25676e4fb4e5b877da5` — matches
  (projection).
All matched; no fingerprint changed, nothing reopens. Observation, not a
defect: per the sibling-file-item bar, hashing the load-bearing
target/consumers/oracles suffices; the RJ4 bodies and contract sources are
named with body-strength reasons while their rules are owned elsewhere, so
their future changes cannot reopen these file-local rows.

### Gates, Pending, coupling

Structural gates: none owed beyond the existing behavior oracles — endorsed
under principle 9's economy rule (a hand copy of the owner body at a call
site passes the behavior oracles because the copy is correct, so a bespoke
per-helper existence test would be machinery, same bar as the sibling
commands-`__init__` inventory item). Failability is shown statically and
tightly: each challenge names the oracle row contradicting the divergence
(C1 → passthrough rows, C2 → cause-identity rows, C4/C8 → message rows). No
new gate → no `prove_failability` run owed; `## Pending execution` absent —
correct, with zero `execution-deferred` proofs and only read-only
instruments used (`ast.parse`, greps; no shared-tree pytest, no temp-tests).
Coupling: none — endorsed (four `def`s in one file, no cross-finding landing
dependency).

### AGENTS.md prose check

The item-scoped diff is empty, so: no process provenance added, no test-tier
obligation (zero-edit; the existing oracles already sit at the mandated
tiers — `tests/` package tests plus `examples/fakeshop/tests/` per-app
non-live), no format run owed (no edits; ruff untouched, correctly).
Artifact citations use `path::Symbol` form with a `LINK DEFINITIONS` block
carrying the canonical group headers; no raw `path:NN` line refs. No
violation — no revision trigger.

### Defects (Worker 2)

None. (Worker 2) No docstring/body mismatch, no missing guard, no import
path bypassing the shim, no layering contradiction found. The DONE-029
glossary note is already board-homed per W1; I independently confirm it is
board-owned and open no entry here.

### Verdict (Worker 2)

**Status: verified.** Zero-edit file item: 11/11 members assigned to F1–F4
(file-local; C1–C8 all count 1), RJ1–RJ4 carry contract differences +
triggers, fingerprints re-hash clean, no pending execution, no coupling, no
defects.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md

<!-- docs/builder/ -->
[build-022]: DONE/build-022-export_schema-0_0_7.md

<!-- django_strawberry_framework/ -->
[export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[management-commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[request-body]: ../../django_strawberry_framework/middleware/request_body.py
[sessions]: ../../django_strawberry_framework/utils/sessions.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-imports]: ../../tests/management/test_imports.py

<!-- examples/ -->
[test-export-schema]: ../../examples/fakeshop/tests/test_export_schema.py
[test-inspect]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
