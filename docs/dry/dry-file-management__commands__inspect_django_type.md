# DRY review: `django_strawberry_framework/management/commands/inspect_django_type.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenges, three indexed
family names are reused as consumer relations, one new family is named for
Worker 0, plus three rejections. Zero production edits; zero tracked files
changed.

## System trace

Target owns the type-introspection CLI surface: resolve one DjangoType (by
dotted path or bare registry name) and print its per-field GraphQL
resolution table (Django field name, Django field type, resolved GraphQL
type, nullability, which converter row fired). FRESH, 637 lines, **41
top-level statements**, one `class Command(BaseCommand)` with four methods,
nine module-level `def`s, seven module constants.

Plan's DRY-axis questions answered. Both import entries are used, each once:
[inspect-cmd][inspect-cmd]`::Command.handle` calls
[management-commands-imports][management-commands-imports]`::import_module_symbol_or_command_error`
for `--schema` (first, so types register and finalize before resolution),
and [inspect-cmd][inspect-cmd]`::Command._resolve_type` calls
[management-commands-imports][management-commands-imports]`::import_string_or_command_error`
for a dotted `type` (dispatched on `"." in arg`; bare names take the
registry path, so the dotted entry never sniffs). Neither command file
imports `django.utils.module_loading` or `strawberry.utils.importer`
directly (full reads of both modules; the `inspect` docstring's two prose
mentions are projections). No inlined copy, so no candidate family on that
axis — the indexed `management-import-selector-entry` and
`management-import-dotted-path-entry` rows are reused as consumer relations.

Introspection reads the existing surface rather than re-deriving types.
Every definition attribute the target touches was read at its owner:
`registry::iter_definitions` + `registry::model_for_type` (consumer of the
indexed `type-registry-model-type-map` family, whose plan row already lists
this file); `definition.origin/model/selected_fields/field_map`,
the four-corner `consumer_*` sets, `relation_connections`,
`graphql_type_name`, `finalized`, `interfaces` (owners:
[types-definition][types-definition], [types-base][types-base]);
`SCALAR_MAP` + `_field_output_type_for` (owner:
[types-converters][types-converters]); `_PACKAGE_SCALAR_MAP` (owner:
[scalars][scalars] — whose item already records this file as the consumer
that derives the `BigInt` SDL name with no second literal);
`_is_relay_shaped` (owner: [types-base][types-base]); `snake_case`
(owner: [utils-strings][utils-strings]); `NameConverter.from_type` +
`config.scalar_map` (upstream schema config). The two `origin.__annotations__[`
index sites are the only such spellings in package source (package-wide
grep); no second introspection-table renderer exists.

Mirror twin [export-schema][export-schema] read in full (62 lines): shared
skeleton is framework spelling over disjoint contracts (rejection
RJskeleton below); the only shared rule beyond it — the selector-helper
import — is already composed by name.

Oracles read: [test-inspect][test-inspect] (package tier, 17 tests: argparse
help, schema-naming config, converter-SDL-name resolution + title,
no-Meta / unfinalized branches, MRO-ancestor key naming, inherited
Strawberry-definition fallback, multi-member union rendering, UNRESOLVED
forward-ref refusal, direct `relay.Node` inheritance, OneToOne + MTI
relation pks, renamed-relation / consumer-enum SDL names, `Meta.name` /
`__name__` collision, custom-scalar / union / definitionless
`_scalar_name` rows) and [test-inspect-live][test-inspect-live] (project
tier, 20 tests: Meta-name + class-name bare lookup, dotted path, cold-path
`--schema` in both selector forms, choice row, forward/M2M/reverse
relation rows, consumer `strawberry.field` relation, four-corner scalar
override matrix, cold-path BigInt fallback, Relay pk row,
override-baked nullability, connection-only shape, file/image output
converters, every malformed-path / malformed-selector / unregistered /
non-DjangoType failure). Contract source: [spec-029][spec-029] Slice 2 /
Decision 4 (SHIPPED `0.0.9`; command shape, shape-dispatched `type`
argument, `--schema`-first finalization, the seven `CommandError`
populations, happy-path + failure-mode tiers). Projections: the
[glossary][glossary] introspection-command entry (restates the
read-don't-rederive contract per field origin), [tree][tree] `commands/` +
test-tree lines (render from the module docstrings), [readme][readme]
one-line mention, and the module/class/method docstrings themselves.

Excluded with reason: the dispatch-named concurrent dirt
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, IN-FLIGHT `filters/inputs.py` range hunk
+ `tests/filters/test_inputs.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) plus the grown working-tree dirt outside this
item's paths (`extensions/resource_policy.py`, `filters/sets.py`,
`forms/inputs.py`, sibling untracked `dry-file-*.md` artifacts) were left
untouched; none names this rule and none is in this item's paths. The plan
row `type-registry-model-type-map` already lists this file as covered, so
reusing that name creates no new index obligation beyond the one new
family named below.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The commands are the only CLI
surface; no sibling flavor re-implements type introspection. The twin
comparison is the rejection, not a family (RJskeleton): both files spell
`class Command(BaseCommand)` with `help`/`add_arguments`/`handle`
because Django's discovery + `BaseCommand` hook names own that spelling,
and the two bodies enforce disjoint contracts (selector-to-SDL vs
type-name-to-field-table). The `inspect` body is ~10x the twin's with no
overlapping rule beyond the shim import. Searched via full reads of both
modules.

**2. Sync/async twins.** No `async def`, no `await` in the target
(grep over the file: zero hits); management commands are sync by
framework. No surface — same verdict as the twin, with reason.

**3. Derived rather than repeated knowledge.** `scalar_namer` is derived
once (`partial(_scalar_name, ...)` over the schema config, defaulting to
the cold-path table) and every row builder consumes that one binding;
the SDL name is derived once per site via `_sdl_type_name` (converter
applied, `graphql_type_name` fallback only for the unfinalized path —
distinct states, not a second derivation); the selector string passes
through `options["schema"]` unchanged into the shim (no local re-split).
The `SCALAR_MAP` MRO walk in `_matched_scalar_key` re-spells the
iteration shape `scalar_for_field` owns to NAME the fired row — recorded
as RJkeywalk, not a second derivation of the scalar itself (nullability
is never re-derived; the annotation is read). Otherwise searched, no
second derivation.

**4. Inverse / round-trip pairs.** Table render is one-way
(definition → text); the annotation renderers (`_render_annotation`,
`_render_strawberry_type`) have no parse-back half. No surface.

**5. Contracts restated in another medium.** [test-inspect][test-inspect]
and [test-inspect-live][test-inspect-live] are independent oracles (they
assert rendered rows, titles, verbatim messages, and converter labels
through `call_command`; never read the owner's internals — counted
zero). [spec-029][spec-029] Decision 4 is the contract source (ship-time
pin — counted zero). [glossary][glossary] entry, [tree][tree] lines,
[readme][readme] mention, and the docstrings are projections (a wording
change here re-renders or redescribes there — counted zero).

**6. Enforcement by omission.** Field-kind family enumerated:
auto-synthesized scalar, auto-synthesized relation, suppressed Relay pk,
relation pk (OneToOne / MTI parent link), consumer-authored scalar
(annotation / assigned / overlap), consumer-authored relation, file/image
output-object column, choice-enum column, connection-only shape. Every
member reaches a row builder (`_resolve_row` most-specific-first) and
every member is pinned at the tier [AGENTS.md][agents] mandates (live
where a fakeshop shape exists; package where the shape would change the
shipped SDL or needs a throwaway type). `CommandError` family
enumerated: malformed dotted path, malformed selector (3 shapes),
unimportable dotted path, unimportable selector, unregistered bare name,
ambiguous bare name, non-DjangoType symbol, no-definition base,
unfinalized type, UNRESOLVED forward ref — every member pinned. No gap.

### Enumeration

Instrument: `ast.parse` over the working tree, counting
`ast.Module.body` members — **41 top-level statements**. Every member
lands below; every challenge in `### Challenges` ends in a file-local
row, a reused family row, the new family, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (read-don't-rederive contract per field origin) | (none) | F1–F12 (prose at definition site) |
| 1–5 | `import datetime/decimal/types/typing/uuid` (render machinery) | `datetime`, `decimal`, `pytypes`, `typing`, `uuid` | F12 |
| 6 | `from collections.abc import Callable, Mapping` | `Callable`, `Mapping` | F11 (`_ScalarNamer`, `scalar_map` type) |
| 7 | `from functools import partial` | `partial` | F1 (one `scalar_namer` derivation) |
| 8 | `import strawberry` | `strawberry` | F11 (cold-path `JSON` name) |
| 9 | `from django.core.management.base import ...` | `BaseCommand`, `CommandError`, `CommandParser` | F1 / F3 |
| 10 | `from django.db import models` | `models` | F5 (row signatures) |
| 11 | `from strawberry.schema.name_converter import NameConverter` | `NameConverter` | F10 |
| 12 | `from strawberry.types.base import StrawberryList, StrawberryOptional` | wrappers | F12 |
| 13–17 | upstream definition imports (`StrawberryEnumDefinition`, `UNRESOLVED`, `StrawberryObjectDefinition`, `ScalarDefinition`, `StrawberryUnion`) | render/UNRESOLVED machinery | F8 / F12 |
| 18 | `from ..._imports import ...` (shim consumer) | both entry helpers | F1 (consumer of both indexed rows) |
| 19 | `from ...registry import registry` | `registry` | F2 (consumer of `type-registry-model-type-map`) |
| 20 | `from ...scalars import _PACKAGE_SCALAR_MAP` | map | F11 (consumer, per scalars item R4) |
| 21 | `from ...types.base import DjangoType, _is_relay_shaped` | gate + shape predicate | F3 / F4 (consumed by name) |
| 22 | `from ...types.converters import SCALAR_MAP, _field_output_type_for` | map + shared walk | F7 (consumed by name) |
| 23 | `from ...utils.strings import snake_case` | `snake_case` | F5 (consumed by name) |
| 24 | `_GLOBAL_ID_GRAPHQL_TYPE = "GlobalID!"` | constant | F4 |
| 25 | `_RELAY_PK_CONVERTER = "relay.Node id"` | constant | F4 |
| 26 | `_DEFAULT_NAME_CONVERTER = NameConverter()` | default | F1 / F10 |
| 27 | `_ScalarNamer = Callable[...]` | alias | F11 |
| 28 | `_RELATION_KIND_LABELS` (5 keys = the 5 `RelationKind` literals) | label map | F6 |
| 29 | `_UNFINALIZED_HINT` | message | F3 |
| 30 | `_GRAPHQL_SCALAR_NAMES` (built-ins + derived `BigInt`) | fallback table | F11 |
| 31 | `class Command` (F1–F5 live here) | `Command` | F1–F5 |
| 32 | `def _yes_no` | token | F5–F8 (shared leaf) |
| 33 | `def _annotation_is_optional` | predicate | F7 |
| 34 | `def _matched_scalar_key` | key naming | F7 |
| 35 | `def _render_strawberry_type` | renderer | F12 |
| 36 | `def _consumer_nullable` | token | F6 / F8 (shared leaf) |
| 37 | `def _consumer_converter_label` | label | F8 |
| 38 | `def _sdl_type_name` | SDL name | F2 / F9 / F10 |
| 39 | `def _scalar_name` | name resolution | F6–F8 / F11 / F12 (shared leaf) |
| 40 | `def _render_annotation` | renderer | F6 / F7 / F12 |

Rules: R1 CLI shape + `--schema`-first handle + type dispatch
(statements 7, 9, 18, 26, 31); R2 bare-name registry resolution
(statements 19, 31, 38); R3 type gates (statements 9, 21, 29, 31);
R4 suppressed-Relay-pk row (statements 21, 24, 25, 31); R5 row dispatch
(statements 10, 23, 31, 32); R6 relation rows + labels (statements 28,
31, 36, 39, 40); R7 scalar rows + key naming (statements 22, 31, 33,
34, 39, 40); R8 consumer-authored rows + labels (statements 13–17, 31,
36, 37, 39); R9 table render + title (statements 31, 38); R10 SDL-name
resolution (statements 11, 26, 38); R11 scalar-name fallback table
(statements 6, 8, 20, 27, 30, 39); R12 annotation renderers + tokens
(statements 1–5, 12–17, 32, 35, 36, 39, 40). Three indexed rows are
reused as *consumer* relations, not definitions:
`management-import-selector-entry` + `management-import-dotted-path-entry`
(owned by File `management/commands/_imports.py` — statement 18 / R1
calls each by name) and `type-registry-model-type-map` (owned by
`registry.py::TypeRegistry` — statement 19 / R2 reads it by name). One
new family is named (N1). Worker 0 owes twelve file-local index rows
(one per finding F1–F12) plus the N1 family item.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 add a third flag (e.g. `--format`) | new argument | **1** (statement 31) | file-local |
| C2 | R1 import `--schema` lazily (after bare-name resolution) | cold-path bare names stop finalizing | **1** (statement 31; the cold-path live twins fail — listed) | file-local |
| C3 | R1 change the selector grammar accepted | new suffix form | **1** here is zero — grammar owned upstream + shim (consumers, counted zero); the local call shape is the only owned site | file-local |
| C4 | R1 resolve dotted paths via the registry instead of `import_string` | dotted/registry fallback merge | **1** (statement 31; Decision 4 forbids the retry — contract source, listed; the malformed-dotted live oracle fails) | file-local |
| C5 | R2 match bare names on `__name__` only (drop the SDL surface) | `Meta.name` / converter names stop resolving | **1** (statement 31; the `PublicPatron` + `ApiItemRefType` twins fail — listed) | file-local |
| C6 | R2 change the SDL-name rule (e.g. converter renames) | new emitted name | **0** here (owner: upstream `NameConverter` + `graphql_type_name`; this site follows via `from_type`, counted zero) | file-local |
| C7 | R2 change ambiguity from error to first-match | silent wrong-type tables | **1** (statement 31; the two ambiguity twins fail — listed) | file-local |
| C8 | R3 admit non-`DjangoType` symbols | different gate population | **1** (statement 31; the non-DjangoType live oracle fails — listed) | file-local |
| C9 | R3 merge the no-definition and unfinalized branches | one message | **1** (statement 31; Decision 4 pins them distinct — contract source; the two package oracles fail — listed) | file-local |
| C10 | R4 stop suppressing the Relay pk (schema keeps `id: GlobalID!` via interface) | scalar pk row instead of GlobalID row | **1** here for the row (statement 31) — plus the owner half, see N1 | new family N1 |
| C11 | R4 suppress relation pks too (owner flips `_build_annotations` order) | command must flip its `is_relation`-first check or crash | **2** (owner branch + statement 31; the O2O/MTI package twins fail — listed) | new family N1 |
| C12 | R5 reorder dispatch (scalar branch before consumer check) | overridden fields report the auto converter | **1** (statement 31; the four-corner live matrix fails — listed) | file-local |
| C13 | R6 add a sixth `RelationKind` literal | new cardinality token | **0** here for the vocabulary (owner: `utils/relations.py::RelationKind`, counted zero); **1** for the display row (statement 28 gains a label; fallback covers it meanwhile) | file-local |
| C14 | R6 change the connection-only detection (e.g. rename `relation_connections`) | sibling lookup breaks | **0** here (owner: finalizer synthesizer, counted zero); **1** for the read site (statement 31; the `PeriodicalType` live twins fail — listed) | file-local |
| C15 | R7 change first-MRO-match to longest-match in `scalar_for_field` | key walk must follow | overlap noted — see RJkeywalk | rejection |
| C16 | R7 re-derive nullability via `convert_scalar` instead of reading the annotation | override-baked nullability inverts | **1** (statement 31; the `NullabilityOverrideBookType` live oracle distinguishes exactly this — listed) | file-local |
| C17 | R8 print the `StrawberryAnnotation` repr for assigned overrides | repr leaks into the type column | **1** (statement 31; the `BranchType` live oracle asserts its absence — listed) | file-local |
| C18 | R8 swallow UNRESOLVED as a printed type | bogus type column | **1** (statement 31; the forward-ref package oracle fails — listed) | file-local |
| C19 | R9 title with `__name__` instead of the SDL name | title diverges from schema | **1** (statement 31; the `PublicPatron` title twins fail — listed) | file-local |
| C20 | R11 hardcode a second `"BigInt"` literal instead of deriving it | literals drift | **1** (statement 30; the scalars-item consumer record + the `ScalarSpecimenType` live twin fail — listed) | file-local |
| C21 | R12 merge `_render_annotation` + `_render_strawberry_type` into one dispatcher | per-node branch | rejected — RJrender (distinct object models, shared leaf; prior trigger) | rejection |
| C22 | one shared `Command(BaseCommand)` skeleton with the twin | common args/handle driver | rejected — RJskeleton (framework-imposed shape, disjoint contracts) | rejection |

No executable proof was run: the target is straight-line delegation plus
branching over already-finalized records with no ordering,
transactional, or async axis an execution could distinguish (principle
8); the only instruments used (`ast.parse`, read-only grep) are
non-mutating. All claims below are therefore `static-reviewed`; there
is no `execution-deferred` proof, no shared-tree pytest was run, and no
`docs/dry/temp-tests/` scratch was created.

## Findings

No production edit is owed by a file item; each finding records one rule
with the challenges that proved it has no second site (or names the
family where the count exceeded one).

### F1 — CLI shape + `--schema`-first handle + type dispatch (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command` subclasses `BaseCommand` with
  `help = "Inspect a DjangoType's resolved per-field GraphQL types"`,
  registers positional `type` plus optional `--schema` (both `type=str`,
  neither with `nargs`), imports `--schema` FIRST via the selector entry
  (register + finalize + supply scalar map and name converter), builds
  the one `scalar_namer` partial, then dispatches `type` by shape
  (`"." in arg` → dotted entry; else registry). Legitimate variation:
  the argument inventory, the help strings, the import-first order, the
  dispatch predicate.
- **Sites + roles.** *Definition*: statement 31 (machinery: statements
  7, 9, 18, 26). *Upstream grammar owners consumed by name*:
  `strawberry.utils.importer::import_module_symbol` and
  `django.utils.module_loading::import_string` via the two reused indexed
  rows (both calls are their consumers, counted zero). *Oracles*: the
  `--schema` help package test, the cold-path live twins (both selector
  forms), the malformed-selector / malformed-dotted live rows, the
  schema-naming-config package twins. *Contract source*:
  [spec-029][spec-029] Decision 4 (shape dispatch is NOT a catch-all
  fallback; `--schema` mirrors `export_schema`).
- **Challenges.** C1 → 1; C2 → 1; C3 → 0 here (owner + shim counted
  zero); C4 → 1.
- **Owner + lifetime.** This file (Django discovery resolves the command
  through this module path; neither the shim nor any library module may
  own the argument surface). No stored derivation (`scalar_namer` is a
  per-call partial).
- **Migration.** None.
- **Distinct behavior.** Import-first order is load-bearing (required
  for bare names in a cold process); shape dispatch (not fallback) is
  pinned by Decision 4 and the malformed-dotted oracle.
- **Behavioral proof.** `static-reviewed`. Rejects "dotted paths fall
  back to the registry" (Decision 4 forbids it) and "the selector entry
  is inlined" (no direct upstream import in code — full read).
- **Structural gate.** None owed beyond the existing oracles: they
  assert behavior (cold finalize, help text, verbatim messages), never
  the owner's internals, and a hand copy of the body at a hypothetical
  second site passes them (the copy is correct) — so a bespoke
  existence test would be economy-violating (principle 9), same bar as
  the sibling shim and twin items.
- **Coupling.** None.
- **Freshness.** Target
  `django_strawberry_framework/management/commands/inspect_django_type.py`
  `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` (working tree = `HEAD:` —
  target CLEAN; also clean vs `ITEM_BASELINE`). Shim read in full:
  [management-commands-imports][management-commands-imports]
  `05e9de80f388b9edecca9322db23f5cba614b4db` (working tree = `HEAD:`).
  Twin read in full: [export-schema][export-schema]
  `e27adae94ea38d7c0695e39ecd36bb8d6497695f` (working tree = `HEAD:`).
  Oracles read: [test-inspect][test-inspect]
  `6bad5092b3a2c09c5fcd2e0c37031334b97e764b`,
  [test-inspect-live][test-inspect-live]
  `76765d66ffdcef4e3760eccdeffe6f473cdb9b92` (both working tree =
  `HEAD:`).

### F2 — bare-name registry resolution (consumer of `type-registry-model-type-map`)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._resolve_bare_name` matches a
  bare name against both resolution surfaces — the converter-applied SDL
  name (`_sdl_type_name`: honors a custom schema `NameConverter` AND
  `Meta.name`) and `type_cls.__name__` — over
  `registry.iter_definitions()` (each type visited once, so one type
  matching on several surfaces appends once); zero matches → hint-carrying
  `CommandError`; ≥2 distinct types → ambiguity `CommandError` listing
  copyable dotted paths with models (via `registry.model_for_type`) in
  sorted order. Legitimate variation: the matched surfaces, the error
  populations and wording, the candidate rendering.
- **Sites + roles.** *Definition of the map*: `registry.py::TypeRegistry`
  (indexed family `type-registry-model-type-map` — this site is its
  consumer, counted zero; the plan row already lists this file).
  *Definition of the SDL-name rule*: upstream `NameConverter` +
  `graphql_type_name` (consumed via F10, counted zero). *Owned here*:
  the two-surface match, the dedupe-by-iteration, the ambiguity listing
  (statements 19, 31, 38). *Oracles*: the ambiguity package test
  (copyable paths re-importable), the `Meta.name` live test (both
  spellings title the SDL name), the converter-SDL package twins, the
  collision package test, the unregistered-name live test. *Contract
  source*: [spec-029][spec-029] Decision 4.
- **Challenges.** C5 → 1; C6 → 0 here (name rule owned upstream);
  C7 → 1.
- **Owner + lifetime.** This file for the match + listing (exists only
  on this command's bare-name path; the registry owns the map, the
  converter owns the name). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** `iter_definitions` visits each type once, so
  the multi-surface match cannot double-append one type; the ambiguity
  message carries models so the operator can pick a dotted path.
- **Behavioral proof.** `static-reviewed`. Rejects "`__name__`-only
  matching suffices" (the `PublicPatron` / `ApiItemRefType` twins
  contradict it) and "the registry owns the listing" (the registry
  exposes iteration; formatting candidates as CLI hints is this
  command's job).
- **Structural gate.** None owed (same economy argument as F1; the
  ambiguity twins fail on bypass).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1; [registry][registry]
  `9cc8bb553fd417fc465809a541769a8383469cda` read (working tree =
  `HEAD:`).

### F3 — DjangoType-subclass / no-definition / unfinalized gates (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command.handle` raises `CommandError`
  for: a resolved symbol that is not a `DjangoType` subclass; a
  `DjangoType` with no `__django_strawberry_definition__` (abstract /
  no-`Meta` base); a definition with `finalized is False`
  (`_UNFINALIZED_HINT`). The latter two are distinct branches per
  Decision 4. Legitimate variation: the accepted population, the three
  verbatim messages.
- **Sites + roles.** *Definition*: statement 31 (machinery: statements
  9, 21, 29). *Oracles*: the non-DjangoType live test, the no-Meta
  package test, the unfinalized package test. *Contract source*:
  [spec-029][spec-029] Decision 4.
- **Challenges.** C8 → 1; C9 → 1.
- **Owner + lifetime.** This file (gates exist only on this command's
  resolution path; the twin's `Schema`-instance gate is a disjoint
  population — RJskeleton). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** `finalized is False` (identity, not
  truthiness) matches the finalizer's flag contract; the no-definition
  message names the abstract/no-Meta cause.
- **Behavioral proof.** `static-reviewed`. Rejects "one gate covers
  both definition states" (Decision 4 pins them distinct; two oracles).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### F4 — suppressed-Relay-pk row (mirrors the owner; see N1)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._is_suppressed_relay_pk` returns
  the Relay-Node-suppressed primary key: `field.is_relation` short-circuits
  first (a relation pk is never suppressed), then the shared
  `_is_relay_shaped(origin, interfaces)` gate, then identity with
  `model._meta.pk.name`. The row prints `GlobalID!` / `no` /
  `relay.Node id` (statements 24–25) and never indexes the absent
  annotation. Legitimate variation: the three conjuncts, the row
  literals.
- **Sites + roles.** *Owner of the suppression rule*:
  [types-base][types-base] `_build_annotations` (performs the drop;
  relation branch at its line 1942 precedes the pk-suppression check at
  1983 — verified by body read). *Shared predicate composed by name*:
  `types/base.py::_is_relay_shaped` (statement 21 import; counted zero).
  *Owned here*: the `is_relation`-first mirror of the owner's branch
  order + the row literals (statement 31). *Oracles*: the direct-inheritance
  package test (consumes the `cls`-arm, not just `Meta.interfaces`),
  the Relay-pk live tests (`BookType`, `GenreType`), the O2O/MTI
  relation-pk package twins (prove the first check is load-bearing —
  without it the command would print GlobalID for a relation the schema
  exposes as a relation type).
- **Challenges.** C10 → 1 here + owner (N1); C11 → 2 (N1).
- **Owner + lifetime.** The suppression rule stays with
  `_build_annotations`; this file owns only its row. No stored
  derivation. Whether the `is_relation`-first mirror must stay a second
  maintained predicate or can derive from post-state is N1's question —
  NOT decided here (a file item consolidates nothing).
- **Migration.** None.
- **Distinct behavior.** Checking `field.is_relation` first mirrors the
  owner's branch order, so the command reports the relation row the
  schema actually builds; the `CustomNode(relay.Node)` and direct
  `class Foo(DjangoType, relay.Node)` spellings stay in lockstep via the
  shared predicate (the direct-inheritance oracle pins the arm a
  Meta-only check would miss).
- **Behavioral proof.** `static-reviewed`. Rejects "the pk row can index
  the annotation" (absent by construction — `KeyError`) and "shape can
  be a Meta-membership check" (the direct-inheritance oracle
  contradicts it).
- **Structural gate.** The O2O/MTI twins + the direct-inheritance test
  fail the two weakenings (drop the first check → GlobalID on a
  relation; Meta-only check → scalar row on direct inheritance). No
  bespoke gate owed.
- **Coupling.** N1 (`relay-pk-suppression-read-mirror`): if the family
  item reshapes the mirror, F4's first branch and docstring move with
  it.
- **Freshness.** Target + oracles as in F1; [types-base][types-base]
  `91c587477ff8257e80dbb9a9c79859f34c5b4c7e` read (working tree =
  `HEAD:`).

### F5 — most-specific-first row dispatch (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._resolve_row` indexes
  `field_map[snake_case(field.name)]` once, then dispatches:
  suppressed Relay pk → consumer-authored → relation → scalar. The
  consumer check precedes the relation/scalar branches because
  `_build_annotations` skips auto-synthesis for those names (neither the
  auto-converter nor a `SCALAR_MAP` row produced them). Legitimate
  variation: the branch order, the single `field_map` index.
- **Sites + roles.** *Definition*: statement 31 (machinery: statements
  10, 23 — `snake_case` consumed by name from its owner, counted zero).
  *Oracles*: the four-corner live matrix (each corner proves its
  branch fires and the auto label does not), the `note: auto` inverse
  row (proves the consumer check does not swallow declare-but-infer).
- **Challenges.** C12 → 1.
- **Owner + lifetime.** This file (dispatch exists only to serve this
  table). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Order is the contract: swapping the consumer
  check below the relation branch re-labels every override with the
  auto converter the owner skipped.
- **Behavioral proof.** `static-reviewed`. Rejects "dispatch order is
  stylistic" (the matrix names the oracle contradicting each swap).
- **Structural gate.** None owed (the matrix fails each reorder).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1; [utils-strings][utils-strings]
  `3ec3b262ea8666d4ba36cf83807ca377fee5a680` read (working tree =
  `HEAD:`).

### F6 — relation rows + cardinality labels + connection-only shape (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._relation_row` renders the
  resolved type from `origin.__annotations__[field.name]`, labels the
  converter `relation: <friendly>` via `_RELATION_KIND_LABELS` (5 keys =
  the 5 `RelationKind` literals in [utils-relations][utils-relations];
  unmapped kinds fall back to the raw token), and reports `no (list)` on
  the many side else the `FieldMeta.nullable` yes/no token. The
  `"connection"`-shaped exception (`_suppressed_connection_name` +
  `_connection_only_relation_row`) detects the popped list annotation
  (absent from `__annotations__`, present in `selected_fields`) via the
  synthesizer's own `relation_connections` record and renders the
  synthesized `<rel>_connection` sibling from the finalized Strawberry
  field metadata, suffixed `(connection-only)`. Legitimate variation:
  the label map, the nullability tokens, the sibling-detection rule.
- **Sites + roles.** *Definition*: statement 31 (machinery: statements
  28, 36, 39, 40). *Owners consumed by name, counted zero*:
  `RelationKind` vocabulary ([utils-relations][utils-relations]),
  `relation_connections` record + `_suppress_relation_list_form`
  (finalizer synthesizer — existence verified, 3 sites), Strawberry
  field metadata (upstream). *Oracles*: the forward-FK / M2M /
  reverse-FK live rows, the `PeriodicalType.issues` connection-only live
  twins (both selector forms; assert the sibling type AND the absence of
  the list form), the renamed-relation package test (SDL name, not
  `__name__`).
- **Challenges.** C13 → 0 here for vocabulary + 1 for the label row;
  C14 → 0 here for the record + 1 for the read site.
- **Owner + lifetime.** This file for labels, tokens, and the sibling
  detection (exists only to serve this table; the cardinality grammar
  and the synthesis record stay with their owners). No stored
  derivation.
- **Migration.** None.
- **Distinct behavior.** The map is exhaustive today with a raw-token
  fallback, so a sixth literal degrades to a truthful label rather than
  a crash; the connection-only path never indexes the deleted
  annotation (the `KeyError` it avoids is the branch's reason).
- **Behavioral proof.** `static-reviewed`. Rejects "the converter column
  can name the auto-converter for overrides" (F5's matrix contradicts
  it) and "the sibling type can be re-derived by concatenation" (it is
  read from the synthesizer's record — inverted lookup, never string
  building).
- **Structural gate.** None owed (the relation + connection-only rows
  fail each weakening).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1; [types-finalizer][types-finalizer]
  `77fd9a2dd229eb9de5f29188c5058035d3606323` read (working tree =
  `HEAD:`); [utils-relations][utils-relations]
  `7662b0bb669c4dfba4a437f3b8f309357f718dca` read (working tree =
  `HEAD:`).

### F7 — scalar rows + converter-row naming (file-local; MRO overlap rejected)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._scalar_row` reads nullability
  from the resolved annotation (`_annotation_is_optional`: `T | None`
  union — statements 33, 40), then names the converter that fired:
  file/image columns via the shared `_field_output_type_for` walk
  (`convert_field_output -> <OutputType>`), choice columns as `choice
  enum`, otherwise `SCALAR_MAP[<MRO-ancestor>]` via `_matched_scalar_key`
  (Decision 4: the matched ancestor, so a consumer subclass reports e.g.
  `TextField`). Legitimate variation: the read-don't-rederive rule, the
  three converter spellings, the ancestor (not concrete) naming.
- **Sites + roles.** *Definition*: statement 31 (machinery: statements
  22, 33, 34, 39, 40). *Owners consumed by name, counted zero*:
  `SCALAR_MAP` + `_field_output_type_for` ([types-converters][types-converters]).
  *Oracles*: the `NullabilityOverrideBookType` live test (distinguishes
  annotation-read from `convert_scalar` re-run — a re-run reproduces
  `field.null` and reports the OPPOSITE), the file/image live twins
  (output-map naming, `SCALAR_MAP` absence, `ImageField` ≠ `FileField`
  fallthrough), the choice live rows, the `SCALAR_MAP[TextField]` live
  row, the MRO-ancestor package test. *Contract source*: Decision 4 +
  the glossary read-don't-rederive paragraph.
- **Challenges.** C15 → RJkeywalk (rejection); C16 → 1.
- **Owner + lifetime.** This file for the row + naming (the maps and
  walks stay with the converter module). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** File/image columns MUST NOT name the
  `SCALAR_MAP` row (`SCALAR_MAP` keeps file rows as `str` for the
  filter-input path); the `_matched_scalar_key` fallback (concrete
  class name) is unreachable for finalized auto-scalar inputs because
  dispatch routes every consumer-authored field away first.
- **Behavioral proof.** `static-reviewed`. Rejects "nullability can be
  recomputed from the column" (the override oracle contradicts it) and
  "the concrete class names the row" (the ancestor oracle contradicts
  it).
- **Structural gate.** None owed (the override + file + ancestor rows
  fail each weakening).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1; [types-converters][types-converters]
  `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75` read (working tree =
  `HEAD:`).

### F8 — consumer-authored rows + override labels (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._consumer_authored_row` reads the
  resolved type from the finalized Strawberry field metadata
  (`origin.__strawberry_definition__` — authoritative for BOTH override
  kinds, forward refs resolved), refusing Strawberry's `UNRESOLVED`
  sentinel with a recovery-hint `CommandError` instead of printing a
  bogus type; `_consumer_converter_label` names the firing row from the
  four-corner override sets (`annotation` / `strawberry.field` /
  `annotation + strawberry.field` overlap idiom × `scalar` / `relation`
  kind); `_consumer_nullable` maps the wrapper (`StrawberryOptional` →
  `yes`, bare `StrawberryList` → `no (list)`, leaf → `no`).
  Legitimate variation: the metadata source, the UNRESOLVED refusal, the
  label grammar, the three tokens.
- **Sites + roles.** *Definition*: statement 31 (machinery: statements
  13–17, 36, 37, 39). *Owners consumed by name, counted zero*: the
  four-corner sets ([types-base][types-base]), the `UNRESOLVED` sentinel
  (upstream Strawberry — finalize alone does not force resolution;
  schema build does). *Oracles*: the four-corner live matrix (all four
  spellings incl. the overlap idiom + the `note: auto` inverse), the
  `BranchType.shelves` live test (`StrawberryAnnotation` absence +
  auto-label absence), the UNRESOLVED package test, the consumer-enum
  package test (finalized metadata reports the SDL name).
- **Challenges.** C17 → 1; C18 → 1.
- **Owner + lifetime.** This file (labels + refusal exist only to serve
  this table; the override sets and the sentinel stay with their
  owners). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** The overlap idiom is labelled, not hidden
  (annotation fixes the type, `strawberry.field` supplies the resolver);
  the UNRESOLVED hint names both recoveries (build the schema / fix the
  module scope).
- **Behavioral proof.** `static-reviewed`. Rejects "the annotation entry
  is renderable" (it holds a `StrawberryAnnotation` or an unresolved
  forward-ref string — neither renderable) and "the sentinel can print"
  (Strawberry itself raises on it at schema-build time).
- **Structural gate.** None owed (the matrix + sentinel oracles fail
  each weakening).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### F9 — table render + SDL title (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::Command._print_table` titles with the
  converter-applied SDL name (`_sdl_type_name`, not `__name__`) plus the
  model path, prints the fixed header + rule, then one row per
  `selected_fields` in selection order with fixed column widths
  (`field` / Django field type name / GraphQL type / nullable /
  converter). Legitimate variation: the title source, the column
  inventory and widths, the iteration order.
- **Sites + roles.** *Definition*: statement 31 (machinery: statement
  38). *Oracles*: the `PublicPatron` title twins (SDL name titles, class
  name resolves but never titles), the `ApiItemRefType` converter-title
  package test, every `_field_row` live test (per-row isolation so
  `String` cannot false-green against `String!`).
- **Challenges.** C19 → 1.
- **Owner + lifetime.** This file (render exists only to serve this
  command). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Title names the schema surface the operator
  inspects; row order follows `selected_fields` (the Meta-filtered
  selection), not the annotation dict.
- **Behavioral proof.** `static-reviewed`. Rejects "`__name__` titles"
  (the title twins contradict it).
- **Structural gate.** None owed (same economy argument as F1).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### F10 — SDL type-name resolution (file-local)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::_sdl_type_name` runs
  `name_converter.from_type` over the finalized Strawberry object
  definition — the same metadata-driven rendering `_scalar_name` uses —
  so custom-converter renames are honored, not just `Meta.name`; a
  registered-but-unfinalized type (no class-owned
  `__strawberry_definition__` — inheritance of a parent's definition
  does NOT count) falls back to the converter-independent
  `graphql_type_name` so bare-name resolution still reaches the clean
  unfinalized diagnostic. Legitimate variation: the converter-first
  rule, the class-owned (`__dict__.get`, not `getattr`) fallback gate.
- **Sites + roles.** *Definition*: statement 38 (machinery: statements
  11, 26). *Owners consumed by name, counted zero*: `NameConverter`
  (upstream), `graphql_type_name` ([types-definition][types-definition]).
  *Oracles*: the `ApiItemRefType` resolve + title package test, the
  partially-finalized-child package test (inherited definition ignored,
  pending alias used), the `Meta.name` live tests. *Consumers*: F2
  (both match surfaces) and F9 (title).
- **Challenges.** C6 → 0 here (name rule owned upstream); the
  `__dict__`-vs-`getattr` distinction → 1 (statement 38; the
  inherited-definition oracle fails `getattr` — listed).
- **Owner + lifetime.** This file (the converter-application point for
  this command's two SDL-name uses). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** `__dict__.get` is deliberate: a partially
  finalized subclass inheriting its parent's Strawberry definition must
  NOT render under the parent's name.
- **Behavioral proof.** `static-reviewed`. Rejects "`getattr` suffices"
  (the inheritance oracle contradicts it) and "`graphql_type_name`
  suffices" (it ignores custom converters — the prefixing oracle
  contradicts it).
- **Structural gate.** None owed (the two oracles fail each weakening).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1; [types-definition][types-definition]
  `fa6c4d330e72d7dceb5f2af7f56e460c6cf72383` read (working tree =
  `HEAD:`).

### F11 — GraphQL scalar-name fallback table (file-local; `BigInt` derived)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::_GRAPHQL_SCALAR_NAMES` maps Python /
  Strawberry scalars to the SDL names Strawberry prints (true built-ins
  as fixed spec constants) while package-defined scalars (today just
  `BigInt`) are merged from `scalars._PACKAGE_SCALAR_MAP` — never a
  second hardcoded literal; [inspect-cmd][inspect-cmd]`::_scalar_name`
  resolves in precedence order: schema `scalar_map` entry (via the
  schema-supplied converter) → built-in/derived table → Strawberry
  definition metadata (`__strawberry_definition__` / `_scalar_definition`
  / definition-or-union instance, rendered via the active converter) →
  `__name__` fallback. Legitimate variation: the precedence, the
  no-second-literal rule, the fallback.
- **Sites + roles.** *Definition*: statements 30, 39 (machinery:
  statements 6, 8, 20, 27). *Owners consumed by name, counted zero*:
  `_PACKAGE_SCALAR_MAP` ([scalars][scalars] — whose item R4 already
  records this table as its consumer), the schema `scalar_map` +
  converter (upstream config). *Oracles*: the schema-config package test
  (`ApiCategoryType!` + `OpaqueToken!` match the live SDL), the cold-path
  BigInt live test (fallback pinned end-to-end against the real model —
  drift breaks a column), the custom-scalar / named-union /
  definitionless package tests. *Consumers*: F6–F8, F12 row rendering.
- **Challenges.** C20 → 1.
- **Owner + lifetime.** This file (cold-path fallback exists only for
  this command's no-`--schema` runs; the map and the live config stay
  with their owners). No stored derivation (the merge is module-level
  data over an owner map, recomputed never — the comment states the
  drift rationale; the scalars item owns the no-drift proof).
- **Migration.** None.
- **Distinct behavior.** Precedence is the contract: a supplied schema
  map wins (so `--schema` names match that schema's SDL exactly);
  without one the table is the best available cold answer.
- **Behavioral proof.** `static-reviewed`. Rejects "a hardcoded
  `"BigInt"` suffices" (the no-second-literal comment + the live twin
  contradict it) and "the table can ignore the schema map" (the
  `OpaqueToken` row contradicts it).
- **Structural gate.** None owed (the config + BigInt + leaf rows fail
  each weakening).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1; [scalars][scalars]
  `5e354042d405040f6137cebd39abe9c042ffece8` read (working tree =
  `HEAD:`).

### F12 — annotation renderers + nullability tokens (file-local; twins rejected)

- **Contract + variation.**
  [inspect-cmd][inspect-cmd]`::_render_annotation` renders resolved
  Python typing annotations (`Name!` leaf, `T | None` → `Name`,
  multi-member union → `A | B`, `list[T]` → `[Inner!]!`);
  [inspect-cmd][inspect-cmd]`::_render_strawberry_type` renders finalized
  Strawberry wrappers (`StrawberryOptional` strips one `!`,
  `StrawberryList` wraps `[Inner!]!`, leaf via `_scalar_name` + `!`);
  both share the `_scalar_name` leaf; `_yes_no` / `_consumer_nullable`
  map booleans/wrappers to the column tokens. Legitimate variation: the
  SDL-mirroring shapes, the shared leaf, the token spellings.
- **Sites + roles.** *Definition*: statements 35, 40 (+ leaves 32, 36,
  39; machinery: statements 1–5, 12–17). *Consumers*: F6 (relation +
  connection-only rows), F7 (scalar rows). *Oracles*: the multi-member
  union package test, the `genres`/`loans`/`shelves` list-shape live
  rows, the `quantity: Float` nullable-annotation live row.
- **Challenges.** C21 → RJrender (rejection).
- **Owner + lifetime.** This file (renderers exist only to serve this
  table). Pure functions; nothing stored.
- **Migration.** None.
- **Distinct behavior.** Two renderers walk different object models
  (`typing.get_origin`/`get_args` vs `StrawberryOptional`/`StrawberryList`
  isinstance) and share only the leaf — the shape the prior
  `dry-0_0_11` trigger records as deliberate.
- **Behavioral proof.** `static-reviewed`. Rejects "one dispatcher
  covers both" (RJrender: a forced merge reintroduces a type-dispatch
  branch on every node).
- **Structural gate.** None owed (the union + list-shape rows fail a
  merge that drops either half).
- **Coupling.** None.
- **Freshness.** Target + oracles as in F1.

### N1 — `relay-pk-suppression-read-mirror` (NEW FAMILY, open)

- **Contract + variation.** "Which fields lose their synthesized
  annotation on a Relay-shaped type": [types-base][types-base]
  `_build_annotations` performs the drop (relation branch before the
  pk-suppression check, verified by body read at its lines 1942/1983);
  [inspect-cmd][inspect-cmd]`::Command._is_suppressed_relay_pk`
  re-evaluates the same predicate from the same inputs (shared
  `_is_relay_shaped` token for the shape half, restated
  `is_relation`-first order for the ordering half) to predict which row
  to print instead of deriving it from post-state. Varies on the
  suppressed population (today: non-relation pks only).
- **Sites + roles.** *Performer*: `_build_annotations` (owner —
  owns the branch order). *Predictor*: `_is_suppressed_relay_pk` +
  F4's row (this file — must move with the owner; an owner flip to
  suppressing relation pks turns this file's relation rows into
  `KeyError`s, and an owner flip the other way turns its GlobalID rows
  into lies). *Shared token, counted zero*: `_is_relay_shaped`.
- **Challenges.** C10 → 2 (owner branch + predictor row); C11 → 2
  (owner order + predictor first-check; O2O/MTI twins fail).
- **Owner + lifetime.** For the family item to decide (performer-side
  candidates: a stored suppressed flag on the definition, or
  derive-from-absence — the file already detects absence for the
  connection-only shape — vs keeping the predictor behind a gate).
  No stored derivation today on either side (the drop leaves no record;
  the predictor re-runs per field).
- **Migration.** None proposed here (a file item consolidates nothing).
- **Distinct behavior.** The predictor is load-bearing, not stylistic:
  removing its first check mis-reports every relation pk; the shared
  predicate keeps the shape half in lockstep (direct-inheritance oracle).
- **Behavioral proof.** `static-reviewed` (branch-order claim verified
  by body read of the owner, not by vocabulary).
- **Structural gate.** The O2O/MTI twins + direct-inheritance test are
  the existing negative controls for the predictor's two conjuncts.
- **Coupling.** F4 moves with whatever the family item decides.
- **Freshness.** Target + [types-base][types-base] as in F4.
- **Trigger if the family item rejects:** a stored post-state record of
  suppression on the definition (then the predictor becomes a pure
  consumer and this family closes).

### RJskeleton — twin `Command` shape shares only the framework spelling (rejected)

Considered: one shared driver for the `class Command(BaseCommand)` /
`help` / `add_arguments` / `handle` skeleton spelled in both
[export-schema][export-schema] and [inspect-cmd][inspect-cmd].
Contract difference: Django owns the class name, the base class, and
the hook names (discovery resolves `management/commands/<name>.py::Command`;
`BaseCommand` calls `add_arguments`/`handle`) — no package rule selects
them, so positing a change to either command's contract (a new export
flag; a new introspection column) never moves the other. What the two
files share beyond the framework spelling — the selector-helper import —
is already composed by name (F1), not inlined. A shared args/handle
abstraction would add a mode flag no real path reaches (principle 5).
Trigger to reconsider: a third command whose argument surface genuinely
overlaps one of these two (then extend the `_imports` precedent — shared
bits extract to the shim module when real, per [spec-022][spec-022]
Decision 3 — rather than abstracting the `Command` shell). Durable home:
this clause (mirrors the twin artifact's RJskeleton; either copy
reopens both).

### RJrender — annotation / Strawberry renderers stay siblings (rejected)

Considered: one dispatcher merging `_render_annotation` (typing
annotations) and `_render_strawberry_type` (Strawberry wrappers).
Contract difference: different object models (`typing.get_origin` /
`get_args` vs `StrawberryOptional` / `StrawberryList` isinstance) over
disjoint inputs (post-finalize `__annotations__` values vs finalized
field-metadata `.type`s); they already share the `_scalar_name` leaf,
so the only thing a merge shares is the call site at the cost of a
per-node type-dispatch branch. Prior `dry-0_0_11` trigger records the
same verdict on the same pair — re-checked against the current bodies,
still holds. Trigger to reconsider: a third caller needing both input
shapes through one entry (then the leaf stays shared and only the
dispatch is new). Durable home: this clause.

### RJkeywalk — `SCALAR_MAP` MRO iteration shape overlap (rejected)

Considered: folding [inspect-cmd][inspect-cmd]`::_matched_scalar_key`'s
`for klass in type(field).__mro__: if klass in SCALAR_MAP` walk into
[types-converters][types-converters]`::scalar_for_field`'s identical
iteration. Contract difference: resolve-for-conversion (returns the
scalar; raises `ConfigurationError` on no match; serves `convert_scalar`
+ filter inputs) vs name-for-display (returns the ancestor's class name;
falls back to the concrete name; serves only this table's converter
column — and only ever sees auto-scalar inputs whose match necessarily
resolved at construction). Posit changing first-match to longest-match
→ both move, but no such variation axis exists on the owner (its
docstring pins first-match as the single lookup); posit adding a
`SCALAR_MAP` entry → neither walk moves (data, not code). Shared
iteration shape, not a shared rule. Trigger to reconsider: a
`key_for_field`-style naming entry point landing beside
`scalar_for_field` (then this call site composes it by name).
Durable home: [types-converters][types-converters]`::scalar_for_field`
clause (for a future family item to record; this file item writes no
production prose).

## Defects

None. Module docstring matches its body (per-origin read sources named
and verified: `origin.__annotations__` for auto fields incl. the
`SCALAR_MAP`-naming-only walk, `origin.__strawberry_definition__` for
both consumer-override kinds, `UNRESOLVED` refusal, shape-dispatched
`type` argument, `--schema`-first finalization + scalar map + name
converter); every `CommandError` population the docstring promises
exists in code with its oracle; the axis-6 sweep finds no field kind
without a row builder and no import path bypassing the shim; all 23
imports are used (verified by full read — incl. `StrawberryEnumDefinition`
/ `ScalarDefinition` / `StrawberryUnion` in the `_scalar_name`
isinstance, `CommandParser` in the `add_arguments` annotation).

## Pending execution

None. No `execution-deferred` proof: the target is delegation plus
branching over already-finalized records pinned by oracles at two tiers
asserting exact rows, titles, messages, and labels; there is no
ordering, transactional, or async axis an execution could distinguish
(principle 8), and the only instruments used (`ast.parse`, read-only
grep) never mutate.

## Judgment

Zero-edit file item. 41/41 members assigned (F1–F12, all file-local with
proving challenges C1–C22 → 0/1 each as recorded); three indexed names
reused as consumer relations (`management-import-selector-entry`,
`management-import-dotted-path-entry`, `type-registry-model-type-map` —
each verified used: both shim entries called, registry read twice);
one new family named (N1 `relay-pk-suppression-read-mirror`, count 2,
holding item owed); three rejections carry contract differences +
triggers (C21 → RJrender, C22 → RJskeleton, C15 → RJkeywalk). The
plan's DRY-axis questions are discharged: both import entries composed
by name (verified both used), the registry map read by name (not
inherited), and the package holds no second introspection-table site.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `aaafe579f4b901e157be9b8d538b3eed03320d0f`:
`git diff <baseline> -- django_strawberry_framework/management/commands/inspect_django_type.py`
empty (exit 0, no output); the artifact path is new and untracked so it
contributes no diff hunks; `git status --short` shows no entry under
`django_strawberry_framework/management/`, `tests/management/`, or
`examples/fakeshop/tests/` — target CLEAN
(`46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` matches both
`HEAD:django_strawberry_framework/management/commands/inspect_django_type.py`
and the working tree, and is clean vs `ITEM_BASELINE` too). The artifact
itself (`docs/dry/dry-file-management__commands__inspect_django_type.md`)
is a new untracked file, the item's only output. No `uv run ruff format .` /
`ruff check` run (no edits to format). The `## Owned changes` ledger
(walker D1 fix + 2 live test files) gains no row from this item. All
concurrent dirt (dispatch-named: `connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`, the
IN-FLIGHT `filters/inputs.py` range hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` — plus grown
dirt outside this item's paths) was left untouched. No scratch paths
created (`docs/dry/temp-tests/`, workspace copies: none — probes were
read-only inline instruments).

## Independent verification (Worker 2)

Own trace recorded from the target + its neighbours (twin FIRST), before
reconciling with `## Findings` below. Read order honoured:
[AGENTS.md][agents], [DRY.md][dry], `worker-2.md`, the plan item
(`management/commands/inspect_django_type.py`, 637 lines,
`docs/dry/dry-0_0_15.md`, Run `0.0.15 2026-09-18-1`), the complete target in
full, the item-scoped diff, the mirror twin
[export-schema][export-schema] (62 lines, read in full FIRST),
[shim][management-commands-imports] in full, both oracle tiers in full,
[registry][registry], [types-base][types-base] (`_build_annotations` branch
order + `_is_relay_shaped`), [types-converters][types-converters],
[types-definition][types-definition], [types-finalizer][types-finalizer],
[scalars][scalars], [utils-strings][utils-strings],
[utils-relations][utils-relations], [spec-029][spec-029] Decision 4; the W1
artifact read last. No `worker-memory/` read. No probe run (read-only
`ast.parse` + `grep`; static-only — adequacy judged below).

Re-derived rules (my names; counts are authoritative definitions only):

- R1 CLI shape + `--schema`-first handle + type dispatch. Sites:
  [inspect-cmd][inspect-cmd]`::Command.add_arguments` /
  `::Command.handle` / `::Command._resolve_type` (definition — owns the
  two-argument surface, the import-first order, the `"." in arg` predicate,
  the one `scalar_namer` partial); upstream grammars
  `django.utils.module_loading::import_string` +
  `strawberry.utils.importer::import_module_symbol` consumed by name through
  the two shim entries (consumers, counted zero). Changes posited: add a
  third flag / import `--schema` lazily / accept a new selector suffix /
  resolve dotted paths via the registry. Each forces 1 here (this file's
  `Command`; C3 forces 0 here — grammar owned upstream + shim). Owner I
  choose: this file (Django discovery resolves the command through this
  module path). Matches W1 F1.
- R2 bare-name match + ambiguity listing. Sites:
  [inspect-cmd][inspect-cmd]`::Command._resolve_bare_name` +
  `::_sdl_type_name` (owns the two-surface match, dedupe-by-iteration, the
  hint/ambiguity wordings); the map owned by
  `registry.py::TypeRegistry` (indexed `type-registry-model-type-map`,
  consumer, counted zero); the SDL-name rule owned by upstream
  `NameConverter` + `graphql_type_name` (consumed via R10, counted zero).
  Changes: `__name__`-only matching / converter-rename rule change /
  first-match instead of error. Counts: 1 / 0 here / 1. Owner I choose:
  this file for the match + listing; registry for the map; converter for
  the name. Matches W1 F2 (consumer-of-indexed-row reading — agree the
  plan row already listing this file means no new index obligation).
- R3 type gates (non-`DjangoType` / no-definition / unfinalized). Sites:
  [inspect-cmd][inspect-cmd]`::Command.handle` (definition). Changes:
  admit non-`DjangoType` symbols / merge the two definition-state
  branches. Each forces 1. Owner I choose: this file (gates exist only on
  this path; the twin's `Schema`-instance gate is a disjoint population).
  Matches W1 F3.
- R4 Relay-pk row. Sites: performer `_build_annotations` in
  [types-base][types-base] (owns the drop; relation branch precedes the
  pk-suppression check — verified by body read); predictor
  [inspect-cmd][inspect-cmd]`::Command._is_suppressed_relay_pk` + row
  literals (owns the `is_relation`-first mirror + `GlobalID!` / `no` /
  `relay.Node id` literals); shared token `_is_relay_shaped` composed by
  name (counted zero). Changes: stop suppressing / suppress relation pks
  too. Counts: 1 here + owner (C10), 2 (C11). Owner I choose: suppression
  rule stays with `_build_annotations`; this file owns only its row; the
  mirror question belongs to a family item. Matches W1 F4 + N1 (coupling
  endorsed — see ruling below).
- R5 row dispatch (suppressed-pk → consumer → relation → scalar + the
  single `field_map[snake_case]` index). Sites:
  [inspect-cmd][inspect-cmd]`::Command._resolve_row` (definition;
  `snake_case` consumed by name, counted zero). Change: reorder the
  consumer check below the relation/scalar branches. Forces 1. Owner I
  choose: this file. Matches W1 F5.
- R6 relation rows + labels + connection-only shape. Sites:
  [inspect-cmd][inspect-cmd]`::Command._relation_row` /
  `::_suppressed_connection_name` / `::_connection_only_relation_row` +
  `_RELATION_KIND_LABELS` (definition — owns labels, tokens, sibling
  detection); `RelationKind` vocabulary + `relation_connections` record +
  `_suppress_relation_list_form` + Strawberry field metadata consumed by
  name (counted zero). Changes: sixth literal (0 here for vocabulary + 1
  for the label row; fallback covers meanwhile) / rename
  `relation_connections` (0 here for the record + 1 for the read site).
  Owner I choose: this file for labels/tokens/detection; vocabulary and
  synthesis record stay with their owners. Matches W1 F6.
- R7 scalar rows + nullability + key naming. Sites:
  [inspect-cmd][inspect-cmd]`::Command._scalar_row` / `::_yes_no` /
  `::_annotation_is_optional` / `::_matched_scalar_key` (definition);
  `SCALAR_MAP` + `_field_output_type_for` consumed by name (counted
  zero). Changes: longest-match in `scalar_for_field` (rejection — see
  RJkeywalk) / re-derive nullability via `convert_scalar` (forces 1; the
  override oracle distinguishes exactly this). Owner I choose: this file
  for the row + naming; maps/walks stay with the converter module.
  Matches W1 F7.
- R8 consumer-authored rows + labels + UNRESOLVED refusal. Sites:
  [inspect-cmd][inspect-cmd]`::Command._consumer_authored_row` /
  `::_consumer_converter_label` / `::_consumer_nullable` (definition);
  four-corner sets + `UNRESOLVED` sentinel consumed by name (counted
  zero). Changes: print the `StrawberryAnnotation` repr / swallow
  UNRESOLVED. Each forces 1. Owner I choose: this file (labels + refusal
  exist only for this table). Matches W1 F8.
- R9 table render + SDL title. Sites:
  [inspect-cmd][inspect-cmd]`::Command._print_table` (definition;
  machinery `_sdl_type_name`). Change: title with `__name__`. Forces 1.
  Owner I choose: this file. Matches W1 F9.
- R10 SDL-name resolution. Sites:
  [inspect-cmd][inspect-cmd]`::_sdl_type_name` (definition; machinery
  `NameConverter`, default converter; `graphql_type_name` fallback).
  Change: the converter rule itself (0 here — owned upstream) /
  `__dict__.get`-vs-`getattr` (forces 1; the inherited-definition oracle
  fails `getattr`). Owner I choose: this file for the
  converter-application point. Matches W1 F10.
- R11 scalar-name fallback table + precedence. Sites:
  [inspect-cmd][inspect-cmd]`::_GRAPHQL_SCALAR_NAMES` /
  `::_scalar_name` (definition — owns the cold-path table + precedence:
  schema `scalar_map` → built-in/derived table → definition metadata →
  `__name__`); `_PACKAGE_SCALAR_MAP` + schema `scalar_map`/converter
  consumed by name (counted zero). Change: second hardcoded `"BigInt"`
  literal (forces 1). Owner I choose: this file for the fallback;
  map/live config stay with owners. Matches W1 F11 (no-second-literal
  rule + precedence endorsed).
- R12 annotation renderers + tokens. Sites:
  [inspect-cmd][inspect-cmd]`::_render_annotation` /
  `::_render_strawberry_type` + shared `_scalar_name` leaf + `_yes_no` /
  `::_consumer_nullable` (definition). Change: merge into one dispatcher
  (rejection — see RJrender). Owner I choose: this file. Matches W1 F12.

Reconciliation vs W1: agree on all twelve rules, all counts (C1–C22 map
1:1 to my posited changes incl. the three 0-here readings C3/C6/C13-vocab/
C14-record and the two N1 2-counts C10/C11), all owners, all three
consumer-reuse readings, and the N1 + three-rejection disposition.
Differences (non-load-bearing, no count changes): (a) oracle-population
prose counts — W1 says "17 tests" package / "20 tests" live; `grep -c
"def test"` gives 18 defs package and 19 defs live (live expands to 24
cases via four parametrize groups: `--schema` ×2, connection-only ×2,
file/image ×2, malformed-selector ×3). The enumerated oracle *lists* in
W1 name all 18 package behaviours, so coverage is complete — the head
numbers are off by one, not the assignment. Worker 0 should correct the
numbers at closeout, not reopen. (b) Enumeration-table shorthand
"`class Command` (F1–F5 live here)" understates: F6–F8 helpers are also
`Command` methods (`_relation_row`, `_scalar_row`,
`_consumer_authored_row` et al. are class-indented); the per-rule
statement lists (R6–R8 all include statement 31) state this correctly,
so the shorthand is imprecise, not wrong. (c) Freshness lists no blob
for [utils-relations][utils-relations] although F6 verifies "5 keys =
the 5 `RelationKind` literals" against it. I re-read the owner and
confirm the equality holds today (both exactly `many`,
`reverse_many_to_one`, `reverse_one_to_one`, `forward_single`,
`generic`); the fallback (`_RELATION_KIND_LABELS.get(kind, kind)`)
makes a sixth literal degrade to a truthful label rather than a crash,
so the missing hash is a closeout nicety (Worker 0: record
`7662b0bb669c4dfba4a437f3b8f309357f718dca`), not a reopen — every
load-bearing input (target, shim, twin, both oracle tiers, registry,
types-base, converters, definition, finalizer, scalars, strings) is
fingerprinted and re-hashed matching below.

### Enumeration (member-by-member vs own count)

Instrument re-run independently: `ast.parse` over the working tree,
`len(ast.Module.body)` = **41**, matching W1. Member mapping verified:

- 0 module docstring → F1–F12 prose at definition site (projection).
  Agree.
- 1–5 `datetime`/`decimal`/`pytypes`/`typing`/`uuid` → F12 render
  machinery (`datetime`/`decimal`/`uuid` in `_GRAPHQL_SCALAR_NAMES`;
  `typing`/`pytypes` in `_annotation_is_optional`/`_render_annotation`).
  Agree.
- 6 `Callable`/`Mapping` → F11 (`_ScalarNamer`, `scalar_map` type).
  Agree.
- 7 `partial` → F1 (one `scalar_namer` derivation). Agree.
- 8 `strawberry` → F11 (cold-path `JSON` name). Agree.
- 9 `BaseCommand`/`CommandError`/`CommandParser` → F1/F3. Agree.
- 10 `models` → F5 row signatures (`models.Field`). Agree.
- 11 `NameConverter` → F10. Agree.
- 12 `StrawberryList`/`StrawberryOptional` → F12 wrappers. Agree.
- 13–17 `StrawberryEnumDefinition`/`UNRESOLVED`/
  `StrawberryObjectDefinition`/`ScalarDefinition`/`StrawberryUnion` →
  F8/F12 (`UNRESOLVED` in the consumer refusal; the other four in the
  `_scalar_name` isinstance). Agree.
- 18 shim import (both entries) → F1 consumer of both indexed rows
  (each called once: selector entry in `handle`, dotted entry in
  `_resolve_type`). Agree — verified by full shim read; no direct
  `django.utils.module_loading` / `strawberry.utils.importer` import in
  either command file.
- 19 `registry` → F2 consumer of `type-registry-model-type-map`
  (`iter_definitions` + `model_for_type`). Agree.
- 20 `_PACKAGE_SCALAR_MAP` → F11 consumer (derived `BigInt`, no second
  literal). Agree.
- 21 `DjangoType`/`_is_relay_shaped` → F3/F4 by name. Agree.
- 22 `SCALAR_MAP`/`_field_output_type_for` → F7 by name. Agree.
- 23 `snake_case` → F5 by name. Agree.
- 24 `_GLOBAL_ID_GRAPHQL_TYPE` / 25 `_RELAY_PK_CONVERTER` → F4. Agree.
- 26 `_DEFAULT_NAME_CONVERTER` → F1/F10. Agree.
- 27 `_ScalarNamer` alias → F11. Agree.
- 28 `_RELATION_KIND_LABELS` (5 keys) → F6. Agree (key set verified
  equal to the 5 `RelationKind` literals).
- 29 `_UNFINALIZED_HINT` → F3. Agree.
- 30 `_GRAPHQL_SCALAR_NAMES` (built-ins + derived `BigInt`) → F11.
  Agree.
- 31 `class Command` (12 methods: `add_arguments`, `handle`,
  `_resolve_type`, `_resolve_bare_name`, `_print_table`, `_resolve_row`,
  `_is_suppressed_relay_pk`, `_relation_row`,
  `_suppressed_connection_name`, `_connection_only_relation_row`,
  `_scalar_row`, `_consumer_authored_row`) → hosts F1–F9 rows (see (b)
  above). Agree with the per-rule lists.
- 32 `_yes_no` → F6/F7 leaf (relation `nullable` + scalar optional
  tokens). Agree (W1 "F5–F8" overstates the direct-use span by including
  the dispatcher; harmless).
- 33 `_annotation_is_optional` → F7. Agree.
- 34 `_matched_scalar_key` → F7. Agree.
- 35 `_render_strawberry_type` → F12 (consumed by F6/F8). Agree.
- 36 `_consumer_nullable` → F6/F8. Agree.
- 37 `_consumer_converter_label` → F8. Agree.
- 38 `_sdl_type_name` → F2/F9/F10. Agree.
- 39 `_scalar_name` → F6–F8/F11/F12 shared leaf. Agree.
- 40 `_render_annotation` → F6/F7/F12. Agree.

41/41 assigned; every `### Challenges` row ends in a file-local row, a
reused consumer row, N1, or a rejection. No orphan member.

### Matrix (against the target's real surface; twin FIRST)

Twin [export-schema][export-schema] read first and in full: shared
skeleton is Django framework spelling (`class Command(BaseCommand)` +
`help`/`add_arguments`/`handle`) over disjoint contracts
(selector-to-SDL vs type-name-to-field-table); the only shared rule
beyond it (selector-helper import) is already composed by name (F1).
RJskeleton endorsed.

1. Cross-flavor mirroring: commands are the only CLI surface; no sibling
   re-implements introspection. Twin comparison is the rejection, not a
   family (searched by full reads of both modules). Discharged. Agree.
2. Sync/async twins: `grep -c "async def|await"` = 0; management
   commands are sync by framework. "No surface, with reason" judged
   correct. Agree.
3. Derived knowledge: `scalar_namer` derived once via
   `partial(_scalar_name, …)` and consumed by every row builder; SDL
   name derived once per site via `_sdl_type_name` (the unfinalized
   `graphql_type_name` fallback is a distinct state, not a second
   derivation); selector string passes through unchanged; the
   `SCALAR_MAP` MRO walk in `_matched_scalar_key` names the fired row
   (RJkeywalk, not a second scalar derivation); nullability is read from
   the annotation, never re-derived. Discharged. Agree.
4. Inverse/round-trip: table render is one-way; neither renderer has a
   parse-back half. No surface. Agree.
5. Contracts in another medium: both oracle tiers are independent
   (assert rendered rows/titles/verbatim messages/converter labels
   through `call_command`; the one `__strawberry_definition__`
   absence assertion pins the fallback without reading the owner to
   compute an expectation — never rewritten to read from the owner,
   counted zero); [spec-029][spec-029] Decision 4 is the contract source
   (counted zero); glossary/tree/readme entries + docstrings are
   projections (counted zero). Discharged. Agree.
6. Enforcement by omission: field-kind family (auto scalar, auto
   relation, suppressed Relay pk, O2O/MTI relation pks,
   annotation/assigned/overlap consumer scalars + relations,
   file/image output columns, choice-enum columns, connection-only
   shape) every member reaches a row builder via most-specific-first
   dispatch, each pinned at the mandated tier (live where a fakeshop
   shape exists, package where the shape would change the shipped SDL
   or needs a throwaway type); the ten `CommandError` populations every
   member pinned. No gap. Agree.

### Counts + roles; equivalence; zero-edit

Counts confirmed per row (C1–C22: 0/1 as recorded; C10/C11 → 2 via N1;
C15/C21/C22 → rejections). Roles confirmed: one authoritative
definition per file-local rule (this file); upstream/owner sites
consumed by name and counted zero (shim ×2, registry map, relay
predicate + branch order, `RelationKind` + synthesis record, converter
maps/walks, four-corner sets, sentinel, `NameConverter` +
`graphql_type_name`, scalar map/converter); oracles/projections counted
zero; no oracle rewritten. Observable equivalence (principle 8):
straight-line delegation plus branching over already-finalized records
with no ordering, transactional, or async axis an execution could
distinguish — `static-reviewed` is the correct proof level for every
finding; no `execution-deferred` proof owed.

Zero-edit confirmed by fresh run: `git diff
aaafe579f4b901e157be9b8d538b3eed03320d0f --
django_strawberry_framework/management/commands/inspect_django_type.py`
empty (exit 0); `git status --short` shows no entry under
`django_strawberry_framework/management/`, `tests/management/`, or
`examples/fakeshop/tests/`; target blob
`46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d` matches both `HEAD:` and the
working tree. No production edit owed by a file item; none made.

Coverage + assignment validated: every rule the file defines/enforces
lands in F1–F12 (all file-local with proving challenges), three indexed
names reused strictly as consumer relations (both shim entries called;
registry read twice via `iter_definitions` + `model_for_type`), one new
family named, three rejections. A file item never owes a production
edit — no candidate routed elsewhere was missed (package-wide grep
confirms the two `origin.__annotations__[` index sites are the only
such spellings; no second introspection-table renderer exists).

NEW family `relay-pk-suppression-read-mirror` (F4/N1) — RULED JUSTIFIED,
coupling CORRECT. The suppressed population is one rule with one
variation axis; performer (`_build_annotations` branch order) + predictor
(`_is_suppressed_relay_pk` `is_relation`-first check) must move together
(C11 → 2; C10 → owner + row). Folding alternatives fail: into F4 alone
would hide the owner half a file item may not consolidate; into an
existing indexed family would couple unrelated vocabularies (the
`type-registry-model-type-map` row already lists this file but owns a
different rule; the shared `_is_relay_shaped` token is already composed
by name and counted zero — the ordering half is what remains); two rows
(one for suppression, one for ordering) would split one population
change into two findings that must still land together. One family is
the narrowest correct shape. Coupling marked both directions (F4
"Coupling: N1" + N1 "Coupling: F4 moves with whatever the family item
decides" + plan holding-item owed) — neither finding can be accepted
alone. Endorsed.

### Rejections; fingerprints; gates; Pending; AGENTS.md prose

- RJskeleton (shared `Command` shell): difference (Django owns the
  class/base/hook names; a change to either contract never moves the
  other; the only shared rule beyond framework spelling is already
  composed by name) + trigger (a third command with genuinely
  overlapping argument surface — then extend the `_imports` precedent
  per spec-022 Decision 3, not the shell) + durable home (this clause,
  mirroring the twin). Endorsed.
- RJrender (merged annotation/Strawberry dispatcher): difference
  (disjoint object models — `typing.get_origin`/`get_args` vs
  `StrawberryOptional`/`StrawberryList` isinstance — over disjoint
  inputs; only the `_scalar_name` leaf is shared, so a merge buys a
  per-node dispatch branch) + trigger (a third caller needing both
  shapes) + prior `dry-0_0_11` trigger re-checked against current
  bodies. Endorsed.
- RJkeywalk (MRO walk into `scalar_for_field`): difference
  (resolve-for-conversion — returns the scalar, raises on no match —
  vs name-for-display — returns the ancestor name, falls back to the
  concrete name, only ever sees auto-scalar inputs whose match already
  resolved; owner docstring pins first-match, so the posited
  longest-match axis does not exist; new `SCALAR_MAP` entries are data,
  move neither walk) + trigger (`key_for_field`-style naming entry
  point beside `scalar_for_field` — then compose by name) + durable
  home (`scalar_for_field` clause). Endorsed.

Fingerprints re-hashed (working tree; all match W1 and `HEAD:`):
target `46dffb3db…`, shim `05e9de80…`, twin `e27adae9…`, package oracle
`6bad5092…`, live oracle `76765d66…`, registry `9cc8bb55…`, types-base
`91c58747…`, converters `9ceb34af…`, definition `fa6c4d330…`, finalizer
`77fd9a2d…`, scalars `5e354042…`, strings `3ec3b262…`. (Plus owner
re-read without a listed blob: utils-relations
`7662b0bb669c4dfba4a437f3b8f309357f718dca` — equality confirmed above;
  Worker 0: append to F6 freshness at closeout.)

Gates / negative controls (inline, static — each weakening names the
oracle that fails it): drop the `is_relation`-first check → O2O/MTI
package twins print `GlobalID!` for a relation the schema exposes as a
relation type (fail); Meta-only shape check → direct-inheritance
package test reports a scalar row instead of the suppressed row (fail);
`getattr` for `__dict__.get` → partially-finalized-child package test
renders under the parent's name (fail); consumer-check reorder →
four-corner live matrix re-labels overrides with auto converters
(fail); `convert_scalar` re-run for annotation-read →
`NullabilityOverrideBookType` live oracle inverts (fail);
`StrawberryAnnotation`-repr print → `BranchType.shelves` live test
shows the repr leak (fail); UNRESOLVED print → forward-ref package
oracle prints a bogus type Strawberry itself raises on (fail);
`__name__` title → `PublicPatron`/converter title twins diverge from
the SDL (fail); hardcoded `BigInt` → cold-path live twin + scalars-item
consumer record drift (fail); `__name__`-only bare match →
`PublicPatron`/`ApiItemRefType` twins stop resolving (fail);
first-match→silent ambiguity → both ambiguity twins go silent-wrong
(fail). No bespoke existence gate owed beyond these behaviour oracles
(principle 9 economy — a hand copy at a hypothetical second site passes
them because the copy is correct; agreed).

Pending absent — JUDGED ADEQUATE for this 637-line file. The target is
delegation plus branching over already-finalized records pinned by
oracles at two tiers asserting exact rows, titles, messages, and
labels; no ordering, transactional, async, or DB-alias axis exists for
an execution to distinguish (principle 8). The only instruments used
(`ast.parse`, read-only `grep`) never mutate; no `docs/dry/temp-tests/`
scratch, no workspace copy, no shared-tree pytest was needed, and none
was run. No `execution-deferred` proof; `## Pending execution` stays
absent. Inapplicable cells (`FAKESHOP_SHARDED=1`, Postgres): the
command's code path reaches no database, alias, or dialect decision —
inapplicable by construction.

AGENTS.md prose check: no process provenance in the artifact body
(baselines/dirt named only under `## Implementation (Worker 1)` as
prior verified items do); citations use `path::Symbol` (raw
`path:NN`-style line mentions at F4/N1 sit inside this per-cycle
`docs/dry/dry-*.md` artifact, which the source-ref rule expressly
permits); tests at the mandated tiers (live where a fakeshop shape
exists, package where the shape would change the shipped SDL or needs a
throwaway type); no bulk operations under `docs/review/` or
`docs/shadow/`; concurrent dirt (dispatch-named in-flight
`filters/inputs.py` hunk + grown worktree dirt incl.
`extensions/resource_policy.py`, `filters/sets.py`, `forms/inputs.py`)
left untouched. Pass.

## Defects (Worker 2)

None. Docstring-to-body check repeated: per-origin read sources named
and present (`origin.__annotations__` for auto fields incl. the
naming-only `SCALAR_MAP` walk, `origin.__strawberry_definition__` for
both override kinds, `UNRESOLVED` refusal, shape-dispatched `type`
argument, `--schema`-first finalization + scalar map + name converter);
every `CommandError` population promised exists with its oracle; axis-6
sweep finds no field kind without a row builder and no import path
bypassing the shim; all imports used (spot-verified incl.
`CommandParser` in the `add_arguments` annotation and the three
`isinstance` leaves in `_scalar_name`). The two head-count imprecisions
and the missing relations blob noted above are artifact niceties for
Worker 0's closeout, not production defects — no `## Defects` entry
owed and no revision demanded on their account.

## Judgment (Worker 2)

Zero-edit file item verified. 41/41 members assigned; matrix discharged
against the real surface (twin read FIRST); counts + roles confirmed
with no oracle rewritten; equivalence is `static-reviewed` throughout
with no deferred proof; item-scoped diff empty; new family
`relay-pk-suppression-read-mirror` justified with correct F4↔N1
coupling; three rejections carry differences + triggers; fingerprints
match; gates fail their negative controls; Pending absent judged
adequate; AGENTS.md prose passes. `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[management-commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[registry]: ../../django_strawberry_framework/registry.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-inspect]: ../../tests/management/test_inspect_django_type.py

<!-- examples/ -->
[test-inspect-live]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Iterations

### Scoped re-trace (run 7, `0.0.15 2026-09-28-7`, pass stale7-1)

Scope: the drift `git diff 5ee86193..0c0537e2 --
django_strawberry_framework/management/commands/inspect_django_type.py`
(1+/2-) carries exactly one code hunk plus its import drop, traced at
HEAD bytes (blob `2807d0fc`; worktree `bb63204c` is HUNT `truth.*`
dirt, 30+/24-, attributed by diff content against `git show HEAD:`,
untouched — it rewrites `__name__`/`getattr`/`isinstance` reads plus
one docstring cite and one `_model_name` helper, and no hunk lands
inside the drift sites). Prior sections stay as verified evidence
about `5ee86193` bytes; nothing above is rewritten. Findings no drift
hunk touches STAND without re-review, per the dispatch. Zero tracked
edits; no production edit is owed by a file item. Blocked-on-hunt
respected: the inline predictor and every hunt-dirtied line untouched
(read-only against HEAD bytes plus this append).

Hunk map (both read off `git show HEAD:`, never the worktree file):

- H1 (`e1ba094e`): `Command._resolve_row` —
  `definition.field_map[snake_case(field.name)]` becomes
  `definition.field_map[field.name]`. One consumer call deleted, zero
  added.
- H2 (`e1ba094e`): the now-unused `from
  ...utils.strings import snake_case` statement dropped.

Owner-side confirmation (adjudication input, not a target hunk):
`types/base.py` at HEAD constructs `field_map = {f.name: ...}` — the
direct read matches the owner grammar — and `_build_annotations` no
longer takes or indexes `field_map` at all (`2bcd50bd` removed the
dead parameter). The target's revised read is the grammar-conformant
consumer, not a second derivation.

REVISE (drift touches the recorded reasoning; fingerprints refreshed
to HEAD blobs in the table below):

- Enumeration (41→40). Instrument re-run on HEAD bytes (`ast.parse`,
  `len(ast.Module.body)`): **40**. Delta is exactly minus old member
  23 (the `snake_case` import statement), zero additions. Old members
  0–22 keep their numbers; old 24–40 shift down one (new 23–39).
  Every HEAD member keeps its recorded home under the shift:
  0 docstring → F1–F12 prose; 1–5 render imports → F12; 6
  `Callable`/`Mapping` → F11; 7 `partial` → F1; 8 `strawberry` →
  F11; 9 `BaseCommand`/`CommandError`/`CommandParser` → F1/F3; 10
  `models` → F5; 11 `NameConverter` → F10; 12 wrappers → F12; 13–17
  upstream definition imports → F8/F12; 18 shim import → F1; 19
  `registry` → F2; 20 `_PACKAGE_SCALAR_MAP` → F11; 21
  `DjangoType`/`_is_relay_shaped` → F3/F4; 22
  `SCALAR_MAP`/`_field_output_type_for` → F7; 23 (old 24)
  `_GLOBAL_ID_GRAPHQL_TYPE` → F4; 24 (old 25) `_RELAY_PK_CONVERTER`
  → F4; 25 (old 26) `_DEFAULT_NAME_CONVERTER` → F1/F10; 26 (old 27)
  `_ScalarNamer` → F11; 27 (old 28) `_RELATION_KIND_LABELS` → F6; 28
  (old 29) `_UNFINALIZED_HINT` → F3; 29 (old 30)
  `_GRAPHQL_SCALAR_NAMES` → F11; 30 (old 31) `class Command` → hosts
  F1–F9 rows; 31 (old 32) `_yes_no` → F6/F7 leaf; 32 (old 33)
  `_annotation_is_optional` → F7; 33 (old 34) `_matched_scalar_key`
  → F7; 34 (old 35) `_render_strawberry_type` → F12; 35 (old 36)
  `_consumer_nullable` → F6/F8; 36 (old 37)
  `_consumer_converter_label` → F8; 37 (old 38) `_sdl_type_name` →
  F2/F9/F10; 38 (old 39) `_scalar_name` → shared leaf; 39 (old 40)
  `_render_annotation` → F6/F7/F12. Per-rule statement lists re-keyed:
  R1 → (7, 9, 18, 25, 30); R2 → (19, 30, 37); R3 → (9, 21, 28,
  30); R4 → (21, 23, 24, 30); R5 → (10, 30, 31); R6 → (27, 30,
  35, 38, 39); R7 → (22, 30, 32, 33, 38, 39); R8 → (13–17, 30, 35,
  36, 38); R9 → (30, 37); R10 → (11, 25, 37); R11 → (6, 8, 20, 26,
  29, 38); R12 → (1–5, 12–17, 31, 34, 35, 38, 39). All `###
  Challenges` counts (0/1/2) unchanged — every `statement 31` cite
  reads `statement 30 (old 31)` at HEAD (`statement 28` → 27 in C13,
  `statement 30` → 29 in C20). W2-text notes (history stands; HEAD
  readings): W2 `- 23 snake_case → F5` names the deleted member; the
  `41/41` verdicts read `40/40` at HEAD with identical homes.
- F5 (row dispatch). REVISED contract clause: `_resolve_row` indexes
  `field_map[field.name]` once — the `snake_case` application is gone
  with the owner's rekey; the consumer no longer translates. Machinery
  cites re-keyed to statements 10, 30, 31 (old 10, 23, 31, 32 minus
  deleted 23). `snake_case` is NO LONGER consumed by this file: the
  recorded `consumed by name, counted zero` relation is deleted, not
  recomposed. Definition count unchanged (consumers counted zero
  before and after); C12 still forces 1 (statement 30). The
  `## System trace` `snake_case (owner: utils-strings)` cite retires
  with it. W2's R5 trace (`the single field_map[snake_case] index`)
  is superseded in spelling only; W2's count (1) and owner (this
  file) are confirmed.
- Defects (import census). REVISED head-count: `all 23 imports are
  used` reads `all 22 imports are used` at HEAD. Re-verified two
  ways: the hunk removes exactly one use (the `snake_case` call)
  with its import statement, and an AST `Name`-load census over HEAD
  bytes shows all 29 bound names referenced, zero unused. Verdict
  (no defect) stands.

CONFIRM (hunks examined; nothing else invalidates):

- F4 + N1 (`relay-pk-suppression-read-mirror` predictor). The target
  hunk lands nowhere near the predictor (untouched lines) or the row
  literals. Owner-side drift examined: `e1ba094e` (import drop,
  `field_map` rekey, `_validate_relation_shape_targets` read,
  `_build_annotations` `field_meta`-read drop) plus `2bcd50bd` (dead
  `field_map` parameter and `relation_kind`/`nullable` snapshot-arg
  removal). Order claim re-verified at HEAD bytes: the `if
  field.is_relation:` relation branch still precedes the
  pk-suppression `continue` in the scalar `else:` arm — the recorded
  `relation branch precedes the pk-suppression check` holds (the
  recorded `1942`/`1983` line pointers are stale; the order is what
  the finding rests on). The shared `_is_relay_shaped` composition is
  untouched (no hunk in its body). C10/C11 counts (owner + row / 2)
  unchanged. Predictor still inline; the owner
  `types/base.py::_is_suppressed_relay_pk` still absent
  package-wide; UNAPPLIED / blocked-on-hunt status unchanged.

STAND (no hunk touches their reasoning; STALE-input drifts shown
irrelevant in the fingerprint table): F1 (shim MATCH, twin MATCH;
oracle drifts keep every cited behavior — 18 same-named package
tests, live assertions only strengthened); F2 (registry drift is the
`2bcd50bd` `discard_pending` docstring reword;
`iter_definitions`/`model_for_type` untouched); F3, F8, F9, F12
(target/oracle inputs only; cited behaviors intact); F6 (finalizer
drift is `e1ba094e` import drop plus 2 direct reads;
`relation_connections` / `_suppress_relation_list_form` untouched;
`RelationKind` re-read at HEAD — still exactly the 5 literals;
utils-relations drift is `4667db4f` `instance_accessor` docstring
prose); F7 + RJkeywalk (converters drift is the `e6a33c46`
module-docstring first line; `SCALAR_MAP` /
`_field_output_type_for` / the `scalar_for_field` first-match pin
untouched); F10 (`types/definition.py` MATCH); F11 (`scalars.py`
MATCH); RJskeleton; RJrender; matrix axes 1–6; the W2 remainder;
the `## Implementation` / `## Independent verification` blobs
(records of their own passes, not re-hashed).

Fingerprint table (recorded pin → `5ee86193` → HEAD `0c0537e2`):

| # | Input | Recorded | `5ee86193` | HEAD | Verdict | Cause |
|---|---|---|---|---|---|---|
| 1 | target `inspect_django_type.py` | `46dffb3d` | MATCH | `2807d0fc` | STALE | window: `e1ba094e` H1 + H2 |
| 2 | shim `_imports.py` | `05e9de80` | MATCH | `05e9de80` | MATCH | — |
| 3 | twin `export_schema.py` | `e27adae9` | MATCH | `e27adae9` | MATCH | — |
| 4 | package oracle `tests/management/test_inspect_django_type.py` | `6bad5092` | MATCH | `9b1360d0` | STALE | window: `4667db4f` fixture swap (4 test-local models → real library models); same 18 test names, cited behaviors intact |
| 5 | live oracle `examples/fakeshop/tests/test_inspect_django_type.py` | `76765d66` | `925a394d` | `925a394d` | STALE | PRE-WINDOW: 2 file/image assertions strengthened (recorded → `5ee86193`); unchanged in window; 19 defs, cited behaviors intact |
| 6 | `registry.py` | `9cc8bb55` | MATCH | `81bd561c` | STALE | window: `2bcd50bd` `discard_pending` docstring reword (prose-only) |
| 7 | `types/base.py` | `91c58747` | MATCH | `dda91365` | STALE | window: `e1ba094e` (import drop, `field_map` rekey = owner grammar, `_validate_relation_shape_targets` read, `_build_annotations` `field_meta`-read drop) + `2bcd50bd` (dead `field_map` param + snapshot-arg removal); order claim re-verified at HEAD |
| 8 | `types/converters.py` | `9ceb34af` | MATCH | `058f1081` | STALE | window: `e6a33c46` module-docstring first line (prose-only) |
| 9 | `types/definition.py` | `fa6c4d330` | MATCH | `fa6c4d330` | MATCH | — |
| 10 | `types/finalizer.py` | `77fd9a2d` | MATCH | `de34ae2a` | STALE | window: `e1ba094e` (import drop + 2 direct reads) |
| 11 | `scalars.py` | `5e354042` | MATCH | `5e354042` | MATCH | — |
| 12 | `utils/strings.py` | `3ec3b262` | MATCH | `991f7dad` | STALE (retired) | window: `e1ba094e` 159-line (exact-`str` check + docstrings); target no longer consumes `snake_case` → input retired, no replacement |
| 13 | `utils/relations.py` (W2 re-read) | `7662b0bb` | MATCH | `8dbc3fe6` | STALE | window: `4667db4f` `instance_accessor` docstring reword (prose-only); `RelationKind` 5 literals intact at HEAD |

4 MATCH / 9 STALE (8 window + 1 pre-window), every STALE with its
cause above. All STALE causes examined against the claims that cite
them; none moves a count, an owner, or a verdict.

Holding-family consequences: NONE. No definition count moves
anywhere (all 0/1/2 counts confirmed; the deleted `snake_case` call
was a counted-zero consumer). No family assignment moves (F5 stays
file-local; enumeration homes preserved under the shift). No
holding-family census names this call site: the artifact contains no
`snake_case`-consumer or `field_map`-reader census (grep for
`census` over the artifact: zero hits), the plan contains no
`snake_case` row (grep over `docs/dry/dry-0_0_15.md`: zero hits),
and `e1ba094e`'s `five readers` is commit-message prose, not an
artifact census. The open `relay-pk-suppression-read-mirror` family
(plan `## Families`, UNAPPLIED / blocked-on-hunt): predictor
untouched, owner order holds — no consequence, status unchanged.
Observation for Worker-0 (not a consequence): no `##
Responsibility index` row is homed at this file — the original
pass's twelve file-local rows were never transcribed (only N1's
family item exists). Transcription-time note: use the HEAD
re-keyed statement lists above, not the pre-shift numbers.

Index-row texts: none. Enumeration delta is zero-or-negative with
zero additions (41→40, one deletion) — a deleted consumer call owes
no row.

Item-scoped diff holds this artifact (untracked) and nothing else.
Zero `.py` touched → no ruff owed. No workspace runs (read-only
instruments: `git show`, `ast.parse`, grep). HEAD unmoved at
`0c0537e2`.

## Independent verification (Worker-2) — stale7 re-trace

Run `0.0.15 2026-09-28-7`, pass verify-1, address
`dry/dry-file-management__commands__inspect_django_type-stale7/verify-1`.
Fresh context. This section's part (a) was derived BEFORE opening W1's
`## Iterations` (target at HEAD bytes, `5ee86193` bytes, owner, plan);
part (b) reconciles after reading it. Trace target: HEAD blob
`2807d0fc`; worktree `bb63204c` is hunt dirt, traced but never edited.

### (a) Independent derivation (pre-read)

Drift hunk re-derived (`git diff 5ee86193..0c0537e2 -- <target>`):
1+/2- exactly — the `from ...utils.strings import snake_case` line
deleted, `field_meta = definition.field_map[snake_case(field.name)]`
→ `field_meta = definition.field_map[field.name]` (`e1ba094e` key
grammar). Nothing else in the target moves across the window.

Enumeration re-derived (`ast.parse`, `len(ast.Module.body)`): `5ee86193`
bytes → 41; HEAD bytes → 40. Deleted member is exactly old #23 (the
`snake_case` import); HEAD #0–22 are byte-identical statements to old
#0–22; HEAD #23–39 are old #24–40 shifted by one. Zero additions. All
homes preserved under the shift (only F5's machinery list loses the
deleted member; `class Command` keeps its 12 methods with the one index
line changed).

Per-finding expectations from the hunk: REVISE F5 (contract now
`field_map[field.name]`, no composed call; C12 still 1 — dispatch order
unchanged); REVISE the defects import census 23→22 (import statements
#1–23 → #1–22; every remaining bound name re-verified used at HEAD
bytes, each ≥2 line hits; `snake_case` 0 hits at HEAD); CONFIRM F4+N1
(predictor still inline at HEAD bytes — `is_relation`-first, composes
`_is_relay_shaped`, identity with `model._meta.pk.name` — and the owner
`_build_annotations` still routes the relation branch with `continue`
before the `suppress_pk_annotation` check, so UNAPPLIED/blocked-on-hunt
unchanged); STAND everything else (F1–F3, F6–F12, RJskeleton, RJrender,
RJkeywalk, all matrix axes — no drift hunk touches their sites).

Deleted-call judgment: the deleted call was a plain consumer (counted
zero in F5); its removal moves no definition count, no family
assignment, and no census. Independently verified no plan census names
the call site: no `## Responsibility index` row names this file or
`snake_case` at all (the original pass's twelve file-local rows were
never transcribed), and the `type-registry-model-type-map` family row
carries no files-covered census. Owner grammar verified at HEAD:
`types/base.py` line 637 builds `field_map = {f.name: ...}`, and the
`e1ba094e` message records the five readers re-indexed directly.

Fingerprint expectations (method: `git rev-parse HEAD:<path>` vs the
recorded pins, `git hash-object <path>` for worktree dirt, `git
rev-parse 5ee86193:<path>` to split window vs pre-window causes):
MATCH — shim `05e9de80`, twin `e27adae9`, definition `fa6c4d33`,
scalars `5e354042` (4 MATCH); STALE — target (window: the hunk),
package oracle `6bad5092`→`9b1360d0` (window), live oracle (pre-window:
recorded `76765d66` already ≠ `5ee86193` bytes `925a394d`, which equal
HEAD bytes — unchanged across the window), registry, types-base,
converters, finalizer, strings, utils-relations (all window: `5ee86193`
bytes equal the recorded pins, HEAD differs) — 9 STALE (8 window + 1
pre-window). 13 rows total.

Index rows owed: none — a deletion with zero additions owes no row.
The 12-untranscribed-rows gap is an original-pass bookkeeping gap under
the 2026-09-22 ruling, not a re-trace debt; no back-transcription
demanded.

### (b) Reconciliation (post-read) — all AGREE, no differences

Read W1's `### Scoped re-trace` after part (a). Per-finding verdicts:

- Enumeration 41→40: AGREE. Deleted member exactly old #23, old 0–22
  fixed, old 24–40 → new 23–39, zero additions; all twelve re-keyed
  per-rule lists re-checked sound (R5 correctly drops the deleted
  member → (10, 30, 31)); `class Command` → new 30 with 12 methods.
- F5 REVISE: AGREE. Contract `field_map[field.name]`, machinery (10,
  30, 31), C12 still 1, `consumed by name` relation deleted (not
  recomposed), `## System trace` cite retired with it.
- Defects census 23→22 all-used: AGREE. Import statements #1–23 →
  #1–22; bound-name count 29 re-derived identical; `snake_case` 0 hits
  at HEAD; verdict (no defect) stands.
- F4+N1 CONFIRM: AGREE. Predictor inline at HEAD bytes, owner order
  (relation branch + `continue` before the `suppress_pk_annotation`
  check) re-verified, `_is_relay_shaped` body untouched,
  `types/base.py::_is_suppressed_relay_pk` 0 hits package-wide at
  HEAD, UNAPPLIED/blocked-on-hunt unchanged. The `_build_annotations`
  dead-`field_map`-param note (`2bcd50bd`) corroborated in the HEAD
  signature.
- STAND set: AGREE on stated reasons, each re-derived: F1 (package
  oracle drift is exactly `4667db4f`, same 18 test names; live file
  byte-identical across window); F2 (registry drift is the prose-only
  `discard_pending` reword); F6 (finalizer drift is exactly the import
  drop + 2 direct reads; `RelationKind` still exactly the 5 literals
  at HEAD; relations drift is the prose-only `instance_accessor`
  reword); F7+RJkeywalk (converters drift is the 1-line docstring
  first line); F10/F11 (MATCH inputs); F3/F8/F9/F12, RJskeleton,
  RJrender, all matrix axes, W2 remainder (no hunk touches their
  sites).
- Fingerprints: 13/13 digit-for-digit AGREE with part (a) (`git
  rev-parse HEAD:<path>` for HEAD blobs, `git hash-object` for
  worktree, `git rev-parse 5ee86193:<path>` for cause splits — never
  one against the other): 4 MATCH (shim, twin, definition, scalars),
  9 STALE — 8 window with the cited commits/hunks confirmed
  (target `e1ba094e`; package oracle `4667db4f`; registry/finalizer/
  converters/strings/relations as tabled; strings 87+/72- = 159
  lines) + 1 pre-window (live oracle: recorded `76765d66` resolves
  and blob-diffs to `925a394d` as exactly the file/image
  assertion-strengthening, unchanged across the window). Row 12
  correctly marked STALE (retired) — the target no longer consumes
  the input.
- Owner grammar: AGREE — `field_map` keyed by Django name at HEAD
  (`types/base.py` construction + `e1ba094e` message + the five
  re-indexed readers, this target among them).
- No-holding-family-consequence: AGREE. Deleted call was counted-zero;
  no definition count, family assignment, or census moves. The
  `relay-pk-suppression-read-mirror` family: predictor untouched,
  owner order holds, status unchanged.
- No literal index rows owed: AGREE — a deletion with zero additions
  owes no row. The 12-untranscribed-rows observation is endorsed as
  an original-pass bookkeeping gap (confirmed: zero index rows name
  this file); no back-transcription demanded; W1's use-HEAD-re-keyed-
  lists note is correct.

Immaterial note N1 (non-blocking, no revision): W1's parenthetical
"grep over `docs/dry/dry-0_0_15.md`: zero hits" reads as a bare
`snake_case` grep, which returns 5 prose hits (file row, staleness,
dispatch ×3) — none an index row or census. The substance (no
`snake_case` row/census in the plan) is TRUE and independently
re-verified (index-range grep + family-row inspection); the
artifact-half parenthetical holds exactly (0 `census` hits in
pre-W1 bytes). Record-accuracy nit only; W1's text left untouched.

Nothing-else-changed: W1's edit is append-only — lines 1–1362
reconstruct to 80990 B = cited 80966 + the required 24-byte Status
swap (`verified` → `ready-for-verification/stale7-1`); `## Iterations`
is pure append. My edit is this section appended at EOF plus the
Status swap below. No production edit, no plan edit, no tracked file
touched by either worker (zero `.py` → no ruff owed, confirmed
instead of run). AGENTS.md prose: W1's append carries run metadata
only in `## Iterations` (the convention `## Implementation`
sections follow), symbol-path citations, line pointers only inside
this per-cycle artifact (permitted); no `docs/review/` or
`docs/shadow/` operations. No workspace runs by either worker
(read-only `git show` / `ast.parse` / grep); HEAD unmoved at
`0c0537e2`.

Window attribution vs `ITEM_BASELINE=1f6a231b`: the plan (Worker-0's
dispatch records) plus this untracked artifact are the item's window;
`docs/review/review-0_0_15.md` drifted mid-task by concurrent work
(out of scope, untouched, not re-attributed). Nothing in the window
belongs to W1 beyond this artifact.

Verdict: `Status: verified` (scoped re-trace at HEAD blob `2807d0fc`;
REVISE enumeration/F5/import-census + CONFIRM F4+N1 + STAND rest, all
re-derived; 4 MATCH / 9 STALE; no defects; no pending execution).
