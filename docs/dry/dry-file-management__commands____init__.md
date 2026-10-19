# DRY review: `django_strawberry_framework/management/commands/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; the single
rule below is recorded file-local with its proving challenge. Zero production
edits; zero tracked files changed.

## System trace

Trivial target (1 line, FRESH): a one-line module docstring naming the two
shipped commands (`export_schema`, `inspect_django_type`) and nothing else —
no imports, no names bound, no `__all__`, no logic. Its only candidate role
is the durable home for the "which commands exist" inventory statement.

Connected code read for judgment, outside the item:
[management-init][management-init] (full; the parent namespace marker — a
distinct fact, see F1), [apps.py][apps] (full; patch dispatcher only, no
management mention — no second inventory there), [commands-imports][commands-imports]
(full; shared import-translation helpers, no `Command` subclass — not a
command), [export-schema][export-schema] (full; ships `Command`, positional
`schema` + `--path`), [inspect-cmd][inspect-cmd] (full; ships `Command`,
positional `type` + `--schema`), Django's [find-commands][find-commands]
(`django/core/management/__init__.py::find_commands`: names starting with
`"_"` are excluded from discovery — `_imports.py` can never be a command),
[spec-022][spec-022] Decision 1 + Slice 1 checklist (contract source: both
`__init__.py` markers ship as one-line-docstring modules; the inventory
wording was a suggestion, not a pin), the [spec-022-rationale][spec-022-rationale]
Decision-1 note (the docstring grew from one command to two when
`inspect_django_type` landed under `DONE-029-0_0_9`), and the
[tree-render][tree-render] generator (`scripts/build_tree_md.py::python_docstring` /
`::first_python_docstring_sentence`: TREE.md folder lines render FROM module
docstrings — projection, not definition).

Excluded with reason: the concurrent dirt named in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, IN-FLIGHT `filters/inputs.py` range hunk
+ `tests/filters/test_inputs.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was left untouched; none of it is in this item's
paths and none of it names this inventory.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** No flavor policy lives here: the file
binds no names for any surface. Sibling markers each name only their own
subtree. No surface.

**2. Sync/async twins.** No `def`, no `await`, no resolver body. No surface.

**3. Derived rather than repeated knowledge.** The inventory fact is stated
once, here. [apps.py][apps] states no management fact (full read). The
[parent marker][management-init] states the namespace role (changes only if
the subtree is repurposed); this file states the implementation inventory
(changes with every command added — it already grew once). No surface.

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. No surface.

**5. Contracts restated in another medium.** Three media carry command
names: the [spec-022][spec-022] prose (contract source at ship time; the
inventory wording explicitly a suggestion, per the
[rationale][spec-022-rationale]), the [TREE.md][tree] folder lines (rendered
FROM this docstring by the [tree-render][tree-render] generator — projection,
a wording change here re-renders there, counted zero), and the
[README][readme] / [GLOSSARY][glossary] command entries (per-command
descriptions, not the inventory list — projections, counted zero). No second
maintained inventory.

**6. Enforcement by omission.** No guard family, no per-member enforcement:
the file enforces nothing on the commands beneath it. Command discovery is
upstream Django behavior ([find-commands][find-commands]), stated nowhere
in-package. Absence here is not a gap: no contract source requires this
marker to do more than exist plus name its implementations.

### Enumeration

Instrument: `ast.parse` over the working tree, counting `ast.Module.body`
members — **1 top-level statement**. Every member lands below; the single
challenge in `### Challenges` ends in a file-local row.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (`"""Implementations of the framework's ..."""`) | (none) | F1 |

Rules: R1 command inventory statement (statement 1). No indexed family names
this rule (no family in the plan's `## Responsibility index` covers a command
inventory); no new family is named (the single row is file-local, so Worker 0
owes one index row: `management-commands-inventory-marker`, file-local,
holding item `File management/commands/__init__.py`).

Module-existence check behind the inventory: the directory holds exactly four
`.py` files. Both named commands exist as modules ([export-schema][export-schema],
[inspect-cmd][inspect-cmd], each shipping its own `Command`). The third file,
[commands-imports][commands-imports], is an underscore-prefixed helper with no
`Command` subclass, excluded from Django discovery by construction
([find-commands][find-commands]). No third command module exists unlisted —
the docstring names every loadable command, neither more nor fewer.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 add a third command | add `management/commands/ping.py` shipping a `Command` | **1** (this file's statement 1 gains the third name; [TREE.md][tree] folder lines re-render as projection; [spec-022][spec-022] prose is a historical suggestion, not a live definition; the new module is new content, not a moved definition; no test reads the wording) | file-local — proves no second site |

No executable proof was run: the target has no runtime semantics beyond the
wording (no branches, no awaits, no queryset/transport code), so there is no
behavior an execution could distinguish. The read-only `ast.parse`
enumeration above ran in the shared tree (non-mutating; the workspace recipe
authorizes mutating proofs, of which this item has none). Command loading
itself is exercised on every suite run by the command tests
(`tests/management/*` resolve through `management.commands.*`). The claim
below is therefore `static-reviewed`; there is no `execution-deferred` proof,
no shared-tree pytest was run, and no `docs/dry/temp-tests/` scratch was
created.

## Findings

No production edit is owed by a file item; the finding records the rule
with the challenge that proved it has no second site.

### F1 — command inventory statement (file-local)

- **Contract + variation.** `management/commands/__init__.py` carries the
  single maintained statement of which `manage.py` commands the framework
  ships (today: `export_schema`, `inspect_django_type`). Legitimate
  variation: the command-name list only.
- **Sites + roles.** *Definition*: `django_strawberry_framework/management/commands/__init__.py`
  statement 1 (module path cited: the file binds no symbol to cite).
  *Contract source*: [spec-022][spec-022] Slice 1 checklist + Decision 1
  (both `__init__.py` markers ship as one-line-docstring modules; inventory
  wording a suggestion, confirmed by the [rationale][spec-022-rationale]
  Decision-1 note). *Ground truth mirrored, not stated*: the directory
  listing itself (both named modules exist; no third command module exists;
  `_imports.py` is discovery-excluded by its underscore prefix).
  *Projection*: [TREE.md][tree] `commands/` folder lines, rendered from
  this docstring by the [tree-render][tree-render] generator; the
  [README][readme] / [GLOSSARY][glossary] per-command entries.
  *Consumers*: none — nothing imports the bare `commands` package; tests
  import the `management.commands.*` submodules directly. *Intentional
  separation*: the [parent marker][management-init] docstring states the
  namespace role (repurposing the subtree moves it; adding a command does
  not) — recorded here so no cycle re-litigates the two markers as copies
  (checks the sibling's nested rejection trigger from this side: confirmed,
  opposite change responses).
- **Challenges.** C1 → 1 definition (this file).
- **Owner + lifetime.** This file (narrowest cohesive owner by
  responsibility: the inventory of a package can only live at its own
  path — [apps.py][apps] cannot own it without stating management facts it
  deliberately omits per [spec-022][spec-022]; `docs/` cannot own it without
  reversing the render direction). No stored derivation; no lifetime fields
  owed.
- **Migration.** None (zero-edit item): the single owner stands.
- **Distinct behavior.** The inventory covers naming only; command behavior
  lives in the command modules, the import-error translation in
  `management/commands/_imports.py::import_or_command_error`.
- **Behavioral proof.** `static-reviewed`. Rejects "a second site states
  the inventory" ([apps.py][apps] full read: no management mention;
  package + `docs/` reads find only this statement plus generated,
  historical, and per-command prose) and "the TREE.md lines are a second
  definition" (the [tree-render][tree-render] generator reads this
  docstring — derivation, not authorship).
- **Structural gate.** None owed: each command's own tests resolve its
  module directly, so a missing command breaks loudly at collection; a
  stale inventory line is prose drift the TREE.md render propagates
  visibly, and a bespoke docstring↔directory equality test would be a
  per-helper existence test without a plausible silent-breakage bypass
  (principle-9 economy).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/management/commands/__init__.py`
  `31cb58b858170a8b7f11a806d2993d8c40ef92c8` (working tree =
  `HEAD:` — target CLEAN). Searched population for a second statement of
  the inventory: whole package + `tests/management/` + `docs/` (reads find
  only this statement, the distinct parent-marker fact, and
  generated/historical/per-command prose); bodies of [apps.py][apps],
  [management-init][management-init], [commands-imports][commands-imports],
  [export-schema][export-schema], [inspect-cmd][inspect-cmd], and
  `django/core/management/__init__.py::find_commands` read in full and
  excluded on strength of body (distinct contracts recorded above).
- **Rejection (nested).** Considered: fold the two `management/`
  one-line markers into one shared "marker wording" rule. Contract
  difference: the parent states the namespace role (changes only if the
  subtree is repurposed); this file states the implementation inventory
  (changes with every command added — it already grew once with
  `inspect_django_type`). Posit repurposing the subtree without adding a
  command → the parent moves, this file does not; posit adding a third
  command → this file moves, the parent does not. Different reasons to
  change: same shape, not the same rule. Trigger to reconsider: a decision
  to generate both wordings from one driver would make the sites one rule.
  Durable home: this clause.

## Defects

None. The docstring matches its body (two names, both loadable, no third
module unlisted); the [spec-022][spec-022] pin is satisfied (one line,
nothing else); the axis-6 sweep finds no member lacking a required guard.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond its wording, all command imports resolve through the namespace on
every suite run, and the only instrument used (`ast.parse`) is
non-mutating. Inspection alone suffices — there is no ordering,
transactional, or async axis an execution could distinguish (principle 8).

## Judgment

Zero-edit file item. One rule traced, file-local with its proving challenge
(C1 → 1 definition); the "which commands exist" inventory is stated nowhere
else ([apps.py][apps], command modules, `docs/` all checked), and the
directory confirms the docstring is exact (both named modules loadable, no
third command, helper discovery-excluded). No families named or reused, no
defects, no pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `c79d0bd3cf135036cef1bd0112232ee785948700`:
`git diff <baseline> -- django_strawberry_framework/management/commands/__init__.py`
empty; `git status --short` clean for the target and the artifact path;
target blob `31cb58b858170a8b7f11a806d2993d8c40ef92c8` matches both
`HEAD:django_strawberry_framework/management/commands/__init__.py` and the
working tree — target CLEAN. The artifact itself
(`docs/dry/dry-file-management__commands____init__.md`) is a new untracked
file, the item's only output. No `uv run ruff format .` / `ruff check` run
(no edits to format). The `## Owned changes` ledger (walker D1 fix + 2 live
test files) gains no row from this item. Concurrent dirt named in the
dispatch (`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, IN-FLIGHT `filters/inputs.py` range
hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus sibling
untracked `dry-file-*.md` artifacts were left untouched. No scratch paths
created (`docs/dry/temp-tests/`, workspace copies: none).

## Independent verification (Worker 2)

Own trace recorded BEFORE reading `## Findings` (read order: target,
siblings, consumers, generator, Django discovery source, then findings for
reconciliation).

**Sites + roles (mine).** *Definition*:
`django_strawberry_framework/management/commands/__init__.py` statement 1
(module docstring; binds nothing). *Contract source*:
[spec-022][spec-022] Slice 1 checklist + Decision 1 (both `__init__.py`
markers ship as one-line-docstring modules; inventory wording a suggestion,
confirmed by the [rationale][spec-022-rationale] Decision-1 note that the
docstring grew from one command to two when `inspect_django_type` landed).
*Ground truth mirrored, not stated*: the directory listing itself.
*Projection*: [TREE.md][tree] `commands/` folder lines, rendered FROM this
docstring by the [tree-render][tree-render] generator
(`::python_docstring` / `::first_python_docstring_sentence` bodies read:
`ast.parse` + `ast.get_docstring`, first-sentence extraction); the
[README][readme] / [GLOSSARY][glossary] per-command entries (per-command
descriptions, not the inventory list). *Consumers*: none of the bare
`commands` package — package-wide grep finds no
`from django_strawberry_framework.management.commands import`; tests import
the `management.commands.*` submodules directly
(`test_export_schema.py`, `test_inspect_django_type.py`,
`test_imports.py` read). *Command discovery itself* is upstream Django
behavior ([find-commands][find-commands] body read in the live `.venv`:
`pkgutil.iter_modules` minus `is_pkg` minus `name.startswith("_")`),
stated nowhere in-package.

**First-hand directory + load checks (mine).**
`django_strawberry_framework/management/commands/` holds exactly four
`.py` files plus `__pycache__`: `__init__.py`, `_imports.py`,
`export_schema.py`, `inspect_django_type.py`. Both named modules import
and each ships `Command` (`ast.parse` class scan + live import:
`export_schema.Command` True, `inspect_django_type.Command` True;
discoverable set via `pkgutil.iter_modules` =
`['export_schema', 'inspect_django_type']` — exactly the docstring list,
neither more nor fewer). `_imports.py` ships no `Command` class and is
discovery-excluded twice over: underscore prefix (the `find_commands`
predicate) plus no command body (shared import-translation helpers only).
No third command module exists unlisted.

**Single-sited? Yes.** Joint-inventory grep over `*.py` under
`django_strawberry_framework/` finds only this file (the one line naming
both commands together). [apps.py][apps] full read: patch dispatcher only,
no management mention. The [parent marker][management-init] states a
distinct fact (the namespace role — moves only if the subtree is
repurposed). The command modules state per-command behavior, never the
inventory. Owner I would choose: this file (narrowest cohesive owner by
responsibility — the inventory of a package can only live at its own path;
[apps.py][apps] cannot own it without stating management facts it
deliberately omits; `docs/` cannot own it without reversing the render
direction). Matches W1.

**Reconciliation vs W1.** Agree on every row: one definition (C1 → 1, my
own add-a-third-command challenge moves only this file; TREE.md re-renders
as projection; spec prose is a historical suggestion; the new module is new
content, not a moved definition; no test reads the wording); roles
(definition / contract source / ground-truth listing / projection /
no consumers / intentional separation from the parent marker with opposite
change responses); owner + no-lifetime reasoning; gate economy (below).
No differences to reconcile.

**Enumeration.** Independent `ast.parse` count over the working tree: 1
top-level statement (`Expr`, module docstring) → lands in F1. Matches
W1's instrument, count, and assignment. No unassigned member. Rules: R1
command inventory statement only; no indexed family covers it.

**Matrix vs real surface.** Minimal is correct here: no `def`/no `await`
(axes 2, 4 vacuous — the file binds nothing, so no twin or round-trip
half can hide); no flavor policy, binds nothing for any surface (axis 1
— sibling markers each name only their own subtree, verified by full read
of all three one-liners); inventory stated once here, parent marker
states the namespace role with opposite change responses and
[apps.py][apps] states no management fact (axis 3 — full read confirms no
second statement); spec pin (historical suggestion) + TREE render
(generator body read, not assumed) + per-command README/GLOSSARY entries
correctly classified as contract source / projection / projection
(axis 5); no guard family and absence here is not a gap — no contract
source asks this marker to enforce anything on the commands beneath it,
and discovery is upstream Django behavior stated nowhere in-package
(axis 6). No unsearched axis hides a consolidation.

**Counts + roles + oracles.** C1 → 1 authoritative definition (this
file). Consumers/oracles/projections that also move: zero counted (TREE.md
re-render is a projection; spec prose is historical; the new module is new
content). No oracle was rewritten to read from the owner it checks —
command tests resolve their modules directly and assert behavior, never
the inventory wording.

**Equivalence / proof status.** `static-reviewed`. The target has no
runtime semantics beyond its wording (no branches, no awaits, no
queryset/transport code), so no execution could distinguish a behavior
(principle 8). No `docs/dry/temp-tests/` scratch created, no workspace
copy (the recipe authorizes mutating proofs, of which this item has
none); the only instrument used (`ast.parse`, `pkgutil.iter_modules`,
live imports) is non-mutating. Command loading itself is exercised on
every suite run by the command tests. No shared-tree pytest was run
(correctly — no production edit to verify).

**Zero-edit + diff (confirmed myself).**
`git diff c79d0bd3cf135036cef1bd0112232ee785948700 -- django_strawberry_framework/management/commands/__init__.py`
is empty (ran myself, exit 0, no output); `git status --short` shows no
touch to the target (only concurrent dirt elsewhere plus untracked
`sibling dry-file-*.md` artifacts including this one). Target blob
`31cb58b858170a8b7f11a806d2993d8c40ef92c8` matches both
`HEAD:django_strawberry_framework/management/commands/__init__.py` and
the working tree — target CLEAN, nothing stale.

**Rejections / fingerprints / Pending / coupling.** Nested rejection
carries concrete contract difference (namespace role vs implementation
inventory) + opposite change responses (repurpose-subtree moves parent
only; add-third-command moves this file only — the latter already
observed once with `inspect_django_type`) + reconsideration trigger (a
decision to generate both wordings from one driver) + durable home (this
clause). Fingerprints re-hashed myself: target `31cb58b8…` match;
`_imports.py` `05e9de80…`, `export_schema.py` `e27adae9…`,
`inspect_django_type.py` `46dffb3d…`, [apps.py][apps] body read,
[management-init][management-init] `beb4e0ee…`, `find_commands` body read
in the live `.venv` — W1's exclusion claims confirmed on strength of
body. Pending absent — adequate for a 1-line inventory docstring: no
ordering/transactional/async axis exists for an execution to distinguish,
every suite run resolves the commands through the namespace, and the only
instrument is non-mutating (principle 8); inspection-only is the correct
call, not a gap. Coupling: none — correct (no former definition to
migrate, no generated slot to collide).

**AGENTS.md prose check.** No process provenance; citations are link-ref
`path::Symbol` / module paths (no raw `path:NN`); no tests owed or added
(file binds no behavior; command tests at the mandated package tier
already import through the submodules); `<!-- LINK DEFINITIONS -->` block
carries all ten canonical group headers (reuses W1's block, no new refs
needed); no TODO anchors, no `ruff`/pytest obligations (zero edits — no
`ruff format` run, correctly, so concurrent dirt is untouched), no
feedback-file mention, no commit. Clean.

**Defects (Worker 2).** None — docstring matches body (two names, both
loadable, no third module unlisted, helper discovery-excluded);
[spec-022][spec-022] pin satisfied (one line, nothing else); axis-6 sweep
finds no member lacking a required guard; no layering contradiction.

**Verdict.** `verified`, no pending execution. File-local row owed: Worker 0
writes one index row — `management-commands-inventory-marker`, file-local,
holding item `File management/commands/__init__.py`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[apps]: ../../django_strawberry_framework/apps.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[management-init]: ../../django_strawberry_framework/management/__init__.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[tree-render]: ../../scripts/build_tree_md.py

<!-- .venv/ -->
[find-commands]: ../../.venv/lib/python3.14/site-packages/django/core/management/__init__.py

<!-- External -->
[glossary]: ../GLOSSARY.md
