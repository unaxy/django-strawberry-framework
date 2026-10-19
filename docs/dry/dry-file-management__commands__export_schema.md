# DRY review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenges, plus two
rejections. Zero production edits; zero tracked files changed.

## System trace

Target owns the SDL-export CLI surface: resolve one Strawberry selector to a
`strawberry.Schema` and emit its SDL to stdout or `--path`. FRESH, 62 lines,
7 top-level statements, one `class Command(BaseCommand)`, no other `def`.

Plan's DRY-axis question answered: this command composes the import shim by
name. [export-schema][export-schema]`::Command.handle` calls only
[management-commands-imports][management-commands-imports]`::import_module_symbol_or_command_error`
(full read; no `django.utils.module_loading` / `strawberry.utils.importer`
import in code). The mirror twin [inspect-cmd][inspect-cmd] (read in full,
637 lines) calls that helper for `--schema` plus the dotted-path entry for a
dotted `type`; its remaining ~600 lines (registry bare-name resolution,
relay-pk suppression, relation/scalar/consumer row builders, annotation
renderers) are an introspection contract this file never touches.

Upstream owners read in the live `.venv` (strawberry-graphql 0.324.0, per the
sibling `_imports` item's pinned read): `strawberry.printer::print_schema`
(`def print_schema(schema: BaseSchema) -> str` at
`.venv/lib/python3.14/site-packages/strawberry/printer/printer.py`) renders
the SDL; `strawberry.utils.importer::import_module_symbol` resolves the
selector. The command consumes both by name and owns what neither provides:
the `Schema`-instance gate, the three-branch stdout/file routing with the
byte-identity suppressions, and the `--path`/write failure translation.

Whole-package sweep for a second SDL-export site: `print_schema` occurs in
package source only here (grep over `django_strawberry_framework/` +
`examples/` finds no other render call; `schema.py` and
`config/schema.py` contain none). No inlined copy, so no candidate family on
that axis.

Oracles read: [test-export-schema][test-export-schema] (4 tests pinning the
argparse contracts and the `newline=""` kwarg) and
[test-export-schema-live][test-export-schema-live] (live tier against the real
`config.schema`: stdout/`--path`/`print_schema` byte identity, all eight
`CommandError` shapes, destructive-overwrite success message). Contract
sources: [spec-022][spec-022] Decisions 1–10 (class shape, shared-helper pin,
`print_schema` delegation, byte-identity contract, `CommandError`-only
surface, no-watch/indent/JSON/settings/alias, `__init__` shell,
`call_command`-only tests, joint cut, live-tier placement) plus the
[spec-022-rationale][spec-022-rationale] deliberation companion.
Projections: the [glossary][glossary] export-command entry (restates the
byte-identity contract and all eight shapes), [tree][tree] `commands/` +
test-tree lines (render from the module docstrings), [readme][readme] one-line
command mention, and the module/class/method docstrings themselves.

Excluded with reason: the dispatch-named concurrent dirt (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, IN-FLIGHT `filters/inputs.py` range hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus sibling
untracked `dry-file-*.md` artifacts were left untouched; none names this
rule and none is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The commands are the only CLI surface;
no sibling flavor re-implements SDL export. The twin comparison is the
rejection, not a family (RJskeleton): both files spell
`class Command(BaseCommand)` with `help`/`add_arguments`/`handle` because
Django's discovery + `BaseCommand` hook names own that spelling, and the two
bodies enforce disjoint contracts (selector→SDL→stdout/file vs
type-name→field table). Searched via full reads of both modules, not
surfaced.

**2. Sync/async twins.** No `async def`, no `await`; management commands are
sync by framework. No surface.

**3. Derived rather than repeated knowledge.** `schema_output` is derived
once from `print_schema(schema_symbol)` and both emitting branches consume
that one binding; the selector string passes through `options["schema"]`
unchanged into the shim (no local re-split, no re-derivation). No second
derivation.

**4. Inverse / round-trip pairs.** SDL render is one-way (schema → text);
no parse-back half exists. No surface.

**5. Contracts restated in another medium.** [test-export-schema][test-export-schema]
and [test-export-schema-live][test-export-schema-live] are independent
oracles (they assert bytes, messages, and kwargs through `call_command`;
never read the owner's internals — counted zero). [spec-022][spec-022] +
rationale are contract sources (ship-time pins — counted zero).
[glossary][glossary] entry, [tree][tree] lines, [readme][readme] mention, and
the docstrings are projections (a wording change here re-renders or
redescribes there — counted zero).

**6. Enforcement by omission.** Surface enumerated: positional `schema`
(required, scalar, no `nargs`); `--path` tri-state (omitted → stdout,
empty/whitespace → `CommandError`, value → destructive UTF-8 write);
write-failure translation (`OSError`/`ValueError` → `CommandError`). Every
member enforced: the two argparse shapes pinned in the package tier, every
`handle` branch pinned live (whitespace-only, empty-string, embedded-null,
and missing-parent `--path` rows each exist). The twin's `--schema` flag vs
this command's positional `schema` are distinct grammars at distinct sites,
not an omission. No gap.

### Enumeration

Instrument: `ast.parse` over the working tree, counting `ast.Module.body`
members — **7 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a file-local row or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (states the print-or-write contract) | (none) | F1 |
| 2 | `import pathlib` (F5 write machinery) | `pathlib` | F5 |
| 3 | `from django.core.management.base import BaseCommand, CommandError, CommandParser` | `BaseCommand`, `CommandError`, `CommandParser` | F1 / F5 |
| 4 | `from strawberry import Schema` (F3 gate machinery) | `Schema` | F3 |
| 5 | `from strawberry.printer import print_schema` (upstream render owner) | `print_schema` | F2 |
| 6 | `from ..._imports import import_module_symbol_or_command_error` (shim consumer) | `import_module_symbol_or_command_error` | F1 |
| 7 | `class Command` (all five rules live here) | `Command` | F1–F5 |

Rules: R1 CLI shape + selector delegation (statements 1, 3, 6, 7), R2 SDL
render + three-branch routing (statements 5, 7), R3 non-`Schema` gate
(statements 4, 7), R4 `--path` emptiness gate (statement 7), R5 file-write
branch (statements 2, 3, 7). One indexed row is reused as a *consumer*
relation, not a definition: `management-import-selector-entry` (owned by File
`management/commands/_imports.py`) — statement 6 / F1 calls it by name.
No new family is named (each rule is single-definition, so Worker 0 owes
five file-local index rows, one per finding below).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 add a third flag (e.g. `--indent`) | new argument | **1** (statement 7; Decision 6 forbids it — contract source, listed) | file-local |
| C2 | R1 restore `nargs="?"` on `--path` | bare `--path` silently means stdout again | **1** (statement 7; the bare-`--path` oracle fails — listed) | file-local |
| C3 | R1 change the selector grammar accepted | e.g. a new suffix form | **1** (statement 6 delegates; grammar owned upstream + shim — consumers, counted zero; the local call shape is the only owned site) | file-local |
| C4 | R2 re-add Django's trailing newline on stdout | `ending=""` dropped | **1** (statement 7; the stdout-matches-`print_schema` live twins fail — listed) | file-local |
| C5 | R2 drop `newline=""` on the file write | platform translation returns | **1** (statement 7; the kwargs-pin oracle fails — listed) | file-local |
| C6 | R2 route on truthiness (`if path:`) instead of `is None` | `--path ""` silently means stdout | **1** (statement 7; the empty-`--path` live oracles fail — listed) | file-local |
| C7 | R3 admit a second accepted type (e.g. a subclass gate or duck type) | different gate | **1** (statement 7; the non-schema-symbol live twins fail — listed) | file-local |
| C8 | R4 accept whitespace-only `--path` | `.strip()` dropped | **1** (statement 7; the whitespace-only live twins fail — listed) | file-local |
| C9 | R5 create missing parents instead of failing | `mkdir(parents=True)` | **1** (statement 7; the missing-directory live oracle fails — listed) | file-local |
| C10 | R5 widen the write catch to `Exception` | consumer `Schema(...)` blowup relabelled | **1** (statement 7; the narrow-catch contract source fails — listed) | file-local |
| C11 | one shared `Command(BaseCommand)` skeleton with the twin | common args/handle driver | rejected — RJskeleton (framework-imposed shape, disjoint contracts) | rejection |
| C12 | one `str(e)`/`from e` policy driver with the shim | every `CommandError` shares message/cause policy | already rejected — RJ1 trigger check (stays rejected, see below) | rejection |

No executable proof was run: the target is straight-line delegation plus
branching with no ordering, transactional, or async axis an execution could
distinguish (principle 8); the only instruments used (`ast.parse`,
read-only grep) are non-mutating. All claims below are therefore
`static-reviewed`; there is no `execution-deferred` proof, no shared-tree
pytest was run, and no `docs/dry/temp-tests/` scratch was created.

## Findings

No production edit is owed by a file item; each finding records one rule
with the challenges that proved it has no second site.

### F1 — CLI shape + selector delegation (file-local)

- **Contract + variation.**
  [export-schema][export-schema]`::Command` subclasses `BaseCommand` with
  `help = "Export the GraphQL schema"`, registers positional `schema` and
  optional `--path` (both `type=str`, neither with `nargs`), and resolves
  `options["schema"]` through the shim with `default_symbol_name="schema"`.
  Legitimate variation: the argument inventory, the help strings, the
  delegation call.
- **Sites + roles.** *Definition*: statement 7 (machinery: statements 1, 3,
  6). *Upstream grammar owner consumed by name*:
  `strawberry.utils.importer::import_module_symbol` via the shim's
  `management-import-selector-entry` row (this call is its consumer, counted
  zero). *Oracles*: [test-export-schema][test-export-schema] (missing
  positional, bare `--path`, `--path` help string), the live selector twins
  (colon/default spellings, malformed-selector shapes, unimportable paths).
  *Contract source*: [spec-022][spec-022] Decisions 1–3, 6, 8.
- **Challenges.** C1 → 1 definition; C2 → 1 definition; C3 → 1 definition
  (upstream + shim counted zero as consumer-follows-owner).
- **Owner + lifetime.** This file (Django discovery resolves the command
  through this module path; neither the shim nor any library module may own
  the argument surface). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Exactly two arguments is itself the contract
  (Decision 6 non-goals); `default_symbol_name="schema"` is pinned
  deliberately by the live bare-`"config.schema"` selectors, not depended on
  by accident.
- **Behavioral proof.** `static-reviewed`. Rejects "commands resolve
  selectors directly" (no direct upstream import in code — full read) and
  "a third flag is a free addition" (Decision 6 forbids it).
- **Structural gate.** None owed beyond the existing oracles: they assert
  behavior (parse rejection, help text, resolution outcomes), never the
  owner's internals, and a hand copy of the body at a hypothetical second
  site passes them (the copy is correct) — so a bespoke existence test
  would be economy-violating (principle 9), same bar as the sibling shim
  and inventory items.
- **Coupling.** None.
- **Freshness.**
  `django_strawberry_framework/management/commands/export_schema.py`
  `e27adae94ea38d7c0695e39ecd36bb8d6497695f` (working tree = `HEAD:` —
  target CLEAN). Shim read in full:
  [management-commands-imports][management-commands-imports]
  `05e9de80f388b9edecca9322db23f5cba614b4db` (working tree = `HEAD:`).
  Twin read in full: [inspect-cmd][inspect-cmd]
  `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` (working tree = `HEAD:`).
  Oracles read: [test-export-schema][test-export-schema]
  `5b8fd0b9518ec1a4b24f29d55a568eaad2548365`,
  [test-export-schema-live][test-export-schema-live]
  `9727b17dabb2429269f7d8e49cc919ecff16f1ce`,
  [test-imports][test-imports]
  `2c56e75ed2e5e1a97b82775135f2b972f18a4ac8`.

### F2 — SDL render + three-branch routing (file-local)

- **Contract + variation.**
  [export-schema][export-schema]`::Command.handle` renders once via
  `print_schema(schema_symbol)`, then routes: `path is None` → stdout with
  `ending=""`; empty/whitespace → `CommandError` (F4); otherwise the F5
  write. The `ending=""` + `newline=""` pair is the byte-identity contract:
  stdout bytes = file bytes = `print_schema` return. Legitimate variation:
  the renderer, the routing predicate, either suppression.
- **Sites + roles.** *Definition*: statement 7 (renderer: statement 5,
  consumed by name). *Oracles*: the live byte-identity twins
  (stdout-matches-`print_schema` on both selector spellings,
  `--path`-matches-`print_schema`). *Contract source*: [spec-022][spec-022]
  Decision 4. *Projection*: [glossary][glossary] byte-identity paragraph.
- **Challenges.** C4 → 1 definition; C5 → 1 definition; C6 → 1 definition.
- **Owner + lifetime.** This file (the routing exists only to serve this
  command's two emitters; the renderer stays upstream). No stored
  derivation (`schema_output` is a local binding, recomputed per call).
- **Migration.** None.
- **Distinct behavior.** Routing on `is None`, not truthiness, keeps
  "omitted" and "empty" distinct inputs (C6). `ending=""` governs only the
  emitted string, not shell-redirect translation — the contract is scoped to
  the three emitted byte sequences, per Decision 4.
- **Behavioral proof.** `static-reviewed`. Rejects "the suppressions are
  stylistic" (each names the oracle row contradicting its removal) and "a
  second SDL renderer exists" (package-wide grep: this is the only
  `print_schema` call in package source).
- **Structural gate.** None owed (same economy argument as F1; the
  byte-identity twins fail on bypass).
- **Coupling.** None.
- **Freshness.** Target + renderer + oracles as in F1; [glossary][glossary]
  `bcc99607a5557eeb1602d25676e4fb4e5b877da5` read as projection only
  (export-entry body verified against the three branches).

### F3 — non-`Schema` instance gate (file-local)

- **Contract + variation.**
  [export-schema][export-schema]`::Command.handle` raises
  `CommandError("The `schema` must be an instance of strawberry.Schema")`
  unless the resolved symbol is a `strawberry.Schema` instance (subclass
  admitted — the live tier proves it through `DjangoSchema`).
  Legitimate variation: the accepted population, the verbatim message.
- **Sites + roles.** *Definition*: statement 7 (machinery: statement 4).
  *Oracles*: the live non-schema-symbol twins (DjangoType class, model
  class, settings value — all assert the verbatim message). *Contract
  source*: [spec-022][spec-022] Decision 5 (verbatim wording borrowed from
  strawberry-django).
- **Challenges.** C7 → 1 definition.
- **Owner + lifetime.** This file (the gate exists only on this command's
  resolution path; the twin's `DjangoType`-subclass gate is a disjoint
  population — RJskeleton). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Verbatim message including backticks is pinned;
  the `(ImportError, AttributeError)` catch stays narrow so a consumer
  `Schema(...)` constructor blowup propagates as itself.
- **Behavioral proof.** `static-reviewed`. Rejects "the twin's type gate
  shares this rule" (different accepted population, different message,
  different reasons to change).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### F4 — `--path` emptiness gate (file-local)

- **Contract + variation.**
  [export-schema][export-schema]`::Command.handle` raises
  `CommandError("--path requires a non-empty value")` when `path` is not a
  non-blank string (`not isinstance(path, str) or not path.strip()`).
  Legitimate variation: the blank definition (whitespace counts as empty),
  the verbatim message.
- **Sites + roles.** *Definition*: statement 7. *Oracles*: the live
  whitespace-only / empty-string twins (both assert the verbatim message).
  *Contract source*: [spec-022][spec-022] Decision 5, shape 7.
- **Challenges.** C8 → 1 definition.
- **Owner + lifetime.** This file (reachable only after a real schema
  rendered — the live tier owns the rows a package-tier probe cannot
  reach). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** The `.strip()` is deliberate: `--path "   "` is
  as unusable as `--path ""`. A bare `--path` with no value never reaches
  this gate — argparse rejects it first (C2's oracle).
- **Behavioral proof.** `static-reviewed`. Rejects "truthiness routing
  covers it" (C6: that merge sends `--path ""` silently to stdout).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### F5 — destructive UTF-8 file write + failure translation (file-local)

- **Contract + variation.**
  [export-schema][export-schema]`::Command.handle` writes
  `pathlib.Path(path).write_text(schema_output, encoding="utf-8",
  newline="")` — destructive without prompting, no parent creation —
  catches `(OSError, ValueError)` as `CommandError(str(e)) from e`, then
  reports `self.style.SUCCESS(f"Wrote schema to {path}")`. Legitimate
  variation: encoding, newline policy, destructiveness, caught population,
  message/cause policy, success report.
- **Sites + roles.** *Definition*: statement 7 (machinery: statements 2,
  3). *Oracles*: the live overwrite twin (stale sentinel replaced, success
  message asserted), the missing-directory twin (`OSError`), the
  embedded-null twin (`ValueError`), the package-tier kwargs pin
  (`encoding`/`newline`). *Contract source*: [spec-022][spec-022]
  Decisions 4–5.
- **Challenges.** C9 → 1 definition; C10 → 1 definition.
- **Owner + lifetime.** This file (the write exists only on this command's
  `--path` path; nothing else writes SDL to disk). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Both catches stay narrow: a `ValueError` from the
  consumer's own module body propagates as itself (pinned at the shim tier;
  same policy). The `str(e)`/`from e` spelling shared with the shim's F1
  is the already-rejected RJ1, not a second definition (C12).
- **Behavioral proof.** `static-reviewed`. Rejects "the write should
  create parents" (missing-directory oracle contradicts it) and "the
  catch should be wider" (the non-swallow contract contradicts it).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### RJskeleton — twin `Command` shape shares only the framework spelling (rejected)

Considered: one shared driver for the `class Command(BaseCommand)` /
`help` / `add_arguments` / `handle` skeleton spelled in both
[export-schema][export-schema] and [inspect-cmd][inspect-cmd].
Contract difference: Django owns the class name, the base class, and the
hook names (discovery resolves `management/commands/<name>.py::Command`;
`BaseCommand` calls `add_arguments`/`handle`) — no package rule selects
them, so positing a change to either command's contract (a new export
flag; a new introspection column) never moves the other. What the two
files share beyond the framework spelling — the selector-helper import —
is already composed by name (F1), not inlined. A shared args/handle
abstraction would add a mode flag no real path needs (principle 5).
Trigger to reconsider: a third command whose argument surface genuinely
overlaps one of these two (then extend the `_imports` precedent — shared
bits extract to the shim module when real, per [spec-022][spec-022]
Decision 3 — rather than abstracting the `Command` shell). Durable home:
this clause.

### RJ1 trigger check — file-write `CommandError` spelling (stays rejected)

The sibling `_imports` item rejected a shared `str(e)`/`from e` policy
driver covering its F1 and this file's F5 write branch (disjoint
populations: unimportable-path vs unwritable-path; narrowing either catch
must not move the other). Reconsideration trigger named there: a decision
that every `CommandError` shares one message/cause policy. Checked: no
such decision exists in [spec-022][spec-022], the rationale companion, or
the plan's index — both catches remain deliberately narrow with distinct
populations and distinct oracles. Stays rejected; durable home remains the
sibling clause (no second record opened here).

## Defects

None. The module docstring matches its body (print-or-write, one schema
symbol); the `handle` docstring enumerates all three output branches plus
the argparse-rejected bare `--path`; the `help` strings match the pinned
test assertions; the axis-6 sweep finds no member lacking a required guard
and no SDL path bypassing `print_schema`.

## Pending execution

None. No `execution-deferred` proof: the target is straight-line
delegation plus branching already pinned by oracles at two tiers asserting
exact bytes, messages, and kwargs; there is no ordering, transactional, or
async axis an execution could distinguish (principle 8), and the only
instruments used (`ast.parse`, read-only grep) never mutate.

## Judgment

Zero-edit file item. 7/7 members assigned (F1–F5, all file-local with
proving challenges C1–C10 → 1 definition each); two rejections carry
contract differences + triggers (C11 → RJskeleton, C12 → RJ1 trigger
check). The indexed `management-import-selector-entry` row is reused as
the consumer relation for F1's delegation; no new family is named. The
plan's DRY-axis question is discharged: this command composes the shim by
name (consumer role), nothing is inlined, and the package holds no second
SDL-export site.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `b5f589f820b32a4f3783c3a683a9ef24678be9e6`:
`git diff <baseline> --stat -- django_strawberry_framework/management/
docs/dry/dry-file-management__commands__export_schema.md` empty (exit 0,
no output); `git status --short` shows no entry under
`django_strawberry_framework/management/`, `tests/management/`, or
`examples/fakeshop/tests/` — target CLEAN
(`e27adae94ea38d7c0695e39ecd36bb8d6497695f` matches both
`HEAD:django_strawberry_framework/management/commands/export_schema.py`
and the working tree). The artifact itself
(`docs/dry/dry-file-management__commands__export_schema.md`) is a new
untracked file, the item's only output. No `uv run ruff format .` /
`ruff check` run (no edits to format). The `## Owned changes` ledger
(walker D1 fix + 2 live test files) gains no row from this item. All
concurrent dirt (dispatch-named plus sibling untracked `dry-file-*.md`
artifacts) was left untouched. No scratch paths created
(`docs/dry/temp-tests/`, workspace copies: none).

## Independent verification (Worker 2)

Own trace recorded BEFORE reading `## Findings` (target + mirror twin +
shim + both oracle tiers + contract sources read in full; W1 artifact read
last). Re-derived rules with posited changes and definition counts:

- R1 CLI shape + selector delegation. Sites:
  [export-schema][export-schema]`::Command.add_arguments` /
  `::Command.handle` (definition — owns the two-argument surface and the
  delegation call); upstream grammar
  `strawberry.utils.importer::import_module_symbol` consumed by name through
  the shim's `management-import-selector-entry` row (consumer, counted zero).
  Changes: add `--indent` flag / restore bare-`--path` tolerance / accept a
  new selector suffix form. Each forces exactly 1 definition (this file's
  `Command`; upstream + shim follow as owner/consumer, counted zero). Owner
  chosen: this file (Django discovery resolves the command through this
  module path; no library module may own the argument surface).
- R2 SDL render + three-branch routing + byte-identity. Sites:
  [export-schema][export-schema]`::Command.handle` (definition — single
  `print_schema` call plus `path is None` / blank / value routing with
  `ending=""`); `strawberry.printer::print_schema` (upstream renderer,
  consumed by name, counted zero). Changes: drop `ending=""` / drop
  `newline=""` / route on truthiness. Each forces 1 definition. Owner
  chosen: this file (routing exists only to serve its two emitters;
  renderer stays upstream). `schema_output` is a per-call local binding, no
  stored derivation.
- R3 non-`Schema` instance gate. Sites:
  [export-schema][export-schema]`::Command.handle` (definition; machinery
  `strawberry::Schema`). Change: admit a second accepted type. Forces 1
  definition. Owner chosen: this file (gate exists only on this resolution
  path; the twin's `DjangoType`-subclass gate is a disjoint population).
- R4 `--path` emptiness gate. Sites:
  [export-schema][export-schema]`::Command.handle` (definition). Change:
  accept whitespace-only `--path`. Forces 1 definition. Owner chosen: this
  file (reachable only after a real schema rendered).
- R5 destructive UTF-8 write + failure translation + report. Sites:
  [export-schema][export-schema]`::Command.handle` (definition; machinery
  `pathlib::Path.write_text`, `django.core.management.base::CommandError`).
  Changes: auto-create parents / widen catch to `Exception`. Each forces 1
  definition. Owner chosen: this file (only SDL-to-disk writer).

Reconciliation vs W1: full agreement on all five rules, all counts (each
change forces 1), all owners, and the consumer relation (statement 6 calls
the shim's `management-import-selector-entry` by name, counted zero). No
difference to reconcile. W1's F1–F5 split matches this trace exactly.

### Enumeration (Worker 2, member-by-member)

Instrument re-run independently: `ast.parse` over the working tree,
`len(ast.Module.body)` = **7**, matching W1. Every member:

| # | Statement | Worker 2 home | Agree? |
|---|---|---|---|
| 1 | module docstring (print-or-write contract) | F1 (contract prose at definition site) | agree |
| 2 | `import pathlib` (F5 write machinery) | F5 | agree |
| 3 | `from django.core.management.base import ...` | F1 / F5 machinery | agree |
| 4 | `from strawberry import Schema` (F3 gate machinery) | F3 | agree |
| 5 | `from strawberry.printer import print_schema` (upstream renderer) | F2 (consumed by name) | agree |
| 6 | `from ..._imports import import_module_symbol_or_command_error` | F1 consumer of `management-import-selector-entry` | agree |
| 7 | `class Command` (all five rules live here) | F1–F5 | agree |

7/7 assigned; no member unassigned; no `__all__`, no second `def`/`class`.
No sampling — every member checked.

### Matrix (Worker 2, judged on the real surface; mirror twin FIRST)

Twin [inspect-cmd][inspect-cmd] read in full (637 lines) before judging:
both files spell `class Command(BaseCommand)` with `help` /
`add_arguments` / `handle` because Django's discovery + `BaseCommand` hook
names own that spelling; bodies enforce disjoint contracts
(selector-to-SDL-to-stdout/file vs type-name-to-field-table with registry
resolution, relay-pk suppression, row builders, annotation renderers). The
only shared rule beyond the framework spelling — the selector-helper import
— is already composed by name (F1). Shared skeleton rejected as framework
spelling, not a family — agree with W1's RJskeleton. No consolidation
excuses any axis; each axis discharged:

1. Cross-flavor mirroring — searched via full reads of both commands;
   rejection carries contract difference + trigger. Adequate.
2. Sync/async twins — no `async def` / `await` in target; management
   commands are sync by framework. Inapplicable with reason. Adequate.
3. Derived knowledge — `schema_output` derived once from
   `print_schema(schema_symbol)`; both emitters consume that binding;
   selector passes through `options["schema"]` unchanged (no local
   re-split). No second derivation. Adequate.
4. Inverse / round-trip — SDL render is one-way schema-to-text; no
   parse-back half exists. Inapplicable with reason. Adequate.
5. Contracts in another medium — [test-export-schema][test-export-schema]
   + [test-export-schema-live][test-export-schema-live] are independent
   oracles (assert bytes, messages, kwargs through `call_command`; never
   read owner internals — counted zero); [spec-022][spec-022] + rationale
   are contract sources (ship-time pins — counted zero);
   [glossary][glossary] entry, [tree][tree] lines, [readme][readme] mention,
   module/class/method docstrings are projections (counted zero). Adequate.
6. Enforcement by omission — surface enumerated (positional `schema`;
   `--path` tri-state omitted/blank/value; write-failure translation) and
   every member pinned (two argparse shapes at package tier; every `handle`
   branch live: whitespace-only, empty-string, embedded-null,
   missing-parent, overwrite, byte-identity twins). Twin's `--schema` vs
   this positional `schema` are distinct grammars, not an omission.
   Adequate; no gap.

### Counts + roles; oracle integrity

C1–C10 each force exactly 1 authoritative definition (statement 7;
C3's upstream + shim correctly counted zero as owner/consumer). Consumers,
oracles, projections listed, never counted. Roles confirmed: definitions
(statement 7 + machinery imports), one consumer relation
(`management-import-selector-entry`, owned by File
`management/commands/_imports.py`, reused not redefined), oracles at both
tiers, projections as above. No oracle rewritten to read from its owner:
package tier asserts parse rejection / help text / kwargs through
`call_command` + `create_parser`; live tier asserts SDL bytes, verbatim
messages, overwrite behavior against the real `config.schema`. The
`create_parser` help assertion exercises emitted behavior, not internals.

### Equivalence (principle 8) + zero-edit + routing

`static-reviewed`, no execution — adequate for this 62-line delegating
command. No ordering, transactional, cancellation, or async axis exists for
an execution to distinguish beyond what the live oracles already pin
(stdout/file/`print_schema` byte identity, verbatim `CommandError`
messages, destructive-overwrite bytes, `OSError`/`ValueError` translation,
kwargs pin). Existing oracles at two tiers assert the exact observable
behavior each challenge would perturb. No `docs/dry/temp-tests/` scratch
needed; no shared-tree pytest run by W1 or W2 (per AGENTS.md, no pytest
after edits — and there were no edits). Item-scoped diff confirmed empty
by W2: `git diff b5f589f820b32a4f3783c3a683a9ef24678be9e6 --
django_strawberry_framework/management/commands/export_schema.py` prints
nothing; `git status --short` shows no entry under
`django_strawberry_framework/management/`, `tests/management/`, or
`examples/fakeshop/tests/` (only this artifact as a new untracked file).
Coverage + assignment validated (7/7 above); no production edit owed by a
file item. Routing judged correct: `management-import-selector-entry`
reused as consumer (plan index confirms the row exists as file-local owned
by `_imports.py`); skeleton-twin rejected (framework spelling + disjoint
contracts + principle-5 mode-flag bar); RJ1 stays rejected (disjoint
populations, narrow catches, trigger checked against
[spec-022][spec-022], rationale, and plan index — durable home stays the
sibling clause, no second record opened here).

### Rejections, fingerprints, gates, Pending, coupling

- RJskeleton: contract difference (Django owns class/base/hook names; new
  export flag never moves introspection and vice versa) + trigger (third
  command with genuinely overlapping args surface, then extend the `_imports`
  precedent per [spec-022][spec-022] Decision 3). Adequate.
- RJ1 trigger check: difference (unimportable-path vs unwritable-path
  populations; narrowing either catch must not move the other) + trigger
  (a decision that every `CommandError` shares one message/cause policy;
  checked, absent). Stays rejected. Adequate.
- Freshness re-hashed by W2 (working tree = `HEAD:` throughout, all clean):
  target `e27adae94ea38d7c0695e39ecd36bb8d6497695f` (match);
  shim `05e9de80f388b9edecca9322db23f5cba614b4db` (match);
  twin `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` (match);
  package oracle `5b8fd0b9518ec1a4b24f29d55a568eaad2548365` (match, clean);
  live oracle `9727b17dabb2429269f7d8e49cc919ecff16f1ce` (match, clean);
  [test-imports][test-imports]
  `2c56e75ed2e5e1a97b82775135f2b972f18a4ac8` (match, clean);
  [glossary][glossary] `bcc99607a5557eeb1602d25676e4fb4e5b877da5`
  (match). Observation (not a defect): W1 cites [spec-022][spec-022] +
  rationale as contract sources without listing their blobs; W2 records
  spec `7d0cb08afb389db882cea97bf54a8d907222d43e` (working tree = `HEAD:`)
  here so the closeout Outcomes can bind it. No fingerprint changed; no
  finding reopens.
- Structural gates: none owed beyond existing oracles — adequate. Each
  posited bypass names the failing oracle row (C2 bare-`--path`, C4/C5
  byte-identity twins, C6 empty-path, C7 non-schema twins, C8
  whitespace-only, C9 missing-directory, C10 narrow-catch contract). A hand
  copy of the owner body at a hypothetical second site passes those oracles
  because the copy is correct, so a bespoke existence test would be
  economy-violating under principle 9 — same bar as the sibling shim and
  inventory items. Negative controls are the listed oracle rows failing on
  removal, not a new gate to run.
- `## Pending execution`: absent — adequate. No `execution-deferred` proof
  exists because no ordering/transactional/async axis needs one; the only
  instruments used (`ast.parse`, read-only scans) never mutate.
- Coupling: none marked — correct; zero edits, no cross-file dependency.

### AGENTS.md prose check (Worker 2)

Item-scoped diff touches no production/test paths (artifact only); no
process provenance in prose; citations use `path::Symbol` form with
reference-style link definitions (10 canonical group headers present, no
raw `path:NN` found by scan); tests referenced at their mandated tiers
(package argparse/kwargs pin vs live `config.schema` behavior); no
`feedback.md` mention, no CHANGELOG edit, no bulk-delete under
`docs/review/`, no commit, no branch operation; concurrent dirt untouched.
No `ruff format` / `ruff check` owed (no `.py` edits). Pass.

### Defects (Worker 2)

None. Module/class/`handle` docstrings match the three-branch body plus the
argparse-rejected bare `--path`; `help` strings match pinned assertions;
axis-6 sweep finds no missing guard and package-wide scan confirms this is
the sole `print_schema` call in package source (no SDL bypass). The spec-blob
observation above is artifact completeness, not a production defect, and is
cured by recording the hash here.

Judgment: zero-edit file item verified. 7/7 members assigned to F1–F5
(file-local, each proved by challenges forcing exactly 1 definition);
RJskeleton + RJ1 carry differences + triggers; consumer reuse correct; no
new family. Worker 0 owes five file-local index rows (exact lines below)
and may tick this item `verified` with no pending execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[management-commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py

<!-- tests/ -->
[test-export-schema]: ../../tests/management/test_export_schema.py
[test-imports]: ../../tests/management/test_imports.py

<!-- examples/ -->
[test-export-schema-live]: ../../examples/fakeshop/tests/test_export_schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
