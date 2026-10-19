# DRY review: `utils/strings.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits, zero plan edits.

## System trace

Target [utils-strings][utils-strings] at HEAD blob
`991f7dad20b3c6857d19c4daef5e76f0f9b2373e` (267 lines). The worktree blob is
`5a4f481132f87cc83abeb2a4a4a679990fa5b9bc` (269 lines, 2 hunks, 5+/3-).
No `## Owned changes` row names this file, so the dirt entered as
concurrent-external until content attribution proved otherwise — and it did:

| Hunk (HEAD lines) | Content | Attribution |
|---|---|---|
| import block (`:22`) | `ConfigurationError, _safe_type_name` → `ConfigurationError` + `from . import truth` | external: imports `utils/truth.py`, untracked at HEAD |
| `_plain_text` body (`:43-45`) | `isinstance` → `truth.is_instance`, `_safe_type_name(value)` → `truth.kind(value)` | external: same migration, same untracked import |

Both hunks are the hunt's truthful-reads migration: `utils/truth.py` does
not exist in the HEAD tree (`git ls-tree HEAD` has no such entry; worktree
status `??`, alongside untracked `utils/lazy.py`,
`tests/utils/test_truth.py`, `tests/utils/test_lazy.py`). Nothing in either
hunk is ledger-owned, and nothing is mine — I made no edits. Mechanics
agree: `ITEM_BASELINE=f481b18e…` already carries target blob `5a4f4811`,
so the dirt predates the item. This artifact therefore traces HEAD bytes
exclusively, read via `git show HEAD:…`; worktree bytes were used only to
fingerprint the dirt above. Nothing tracked was touched.

What the target owns: every name transform the package applies at the
GraphQL/Django boundary — one normalizer (`_plain_text`), one injective
forward caser (`graphql_camel_name`), its exact inverse (`snake_case` over
the memoized `_snake_case_cached`), one lossy stem builder (`pascal_case`)
plus its emptiness guard (`pascal_case_or_raise`), and one lookup-path
collapser (`flatten_lookup_path`). Production callers at HEAD, all composing
by name: `graphql_camel_name` from 5 files over 12 call sites (plus 2
alias-only leaves and 1 compat re-export); `snake_case` from
[walker][walker] over 3 sites; `pascal_case` from 2 stem sites;
`pascal_case_or_raise` from 2 guard sites; `flatten_lookup_path` from 3
mangle sites (census under Matrix).

Connected behavior examined (all at HEAD, fingerprints in Findings):
[utils-inputs][utils-inputs] `ee31d360` (triple emitter, `pascalize_token`,
re-export shim), [filters-inputs][filters-inputs] `82b52d97`
(`LOOKUP_NAME_MAP`, `_pascal_case`, alias), [filters-sets][filters-sets]
`993e887a` (reverse map), [orders-inputs][orders-inputs] `6f6ec946`
(alias), [orders-sets][orders-sets] `6044ab1a` (aggregate alias),
[forms-inputs][forms-inputs] `6418753d` (triples),
[mutations-inputs][mutations-inputs] `fc442047` (audit + triples),
[rest-inputs][rest-inputs] `2410f380` (nested spec),
[rest-converter][rest-converter] `6652d092` (naming + enum stem),
[sets-mixins][sets-mixins] `ad8987ea` (`type_name_for`),
[types-converters][types-converters] `058f1081` (enum stem),
[types-definition][types-definition] `fa6c4d33` (`_normalize_pk_name`),
[types-finalizer][types-finalizer] `de34ae2a` (surface audit),
[walker][walker] `75f9c6b6` (reversal + forward maps),
[utils-imports][utils-imports] `291ecedd` (`_plain_text` twin),
[utils-input-values][utils-input-values] `f2566609` (`_field_name`),
[utils-permissions][utils-permissions] `9889d6fe` (`_check_method_name`),
[utils-relations][utils-relations] `8dbc3fe6` (cache-control twin),
[utils-init][utils-init] `1a4c2ec8` (pinned re-export),
[exceptions][exceptions] `e06b0b7f` (`_safe_type_name` body), HEAD
[test-strings][test-strings] `3dad1a9d` (207 lines, 12 tests, oracle
census) and HEAD [test-filters-inputs][test-filters-inputs] `f31757d2`
(alias oracle). Prior file artifacts for `utils/inputs.py`,
`utils/imports.py`, `utils/input_values.py`, `utils/permissions.py`,
`utils/relations.py`, `utils/sessions.py`, `types/definition.py`, and
`rest_framework/serializer_converter.py` were used only as
rejected-candidate triggers to check, per [DRY.md][dry]; the concurrent
`docs/review/rev-utils__strings*.md` scratch was trigger-scanned the same
way (one consumer-call observation, no second definition).

## Verification

### Matrix

Each axis discharged against the target's real surface (`git grep` at HEAD
unless noted; line numbers are HEAD).

1. **Cross-flavor policy mirroring.** The target IS the cross-flavor seam:
filter, order, form, serializer, and model-mutation inputs plus the
optimizer and the type system. Census per helper (production only):
`graphql_camel_name` — 12 call sites in 5 files ([forms-inputs][forms-inputs]
`:537/:606`, [mutations-inputs][mutations-inputs] `:462/:542/:629`,
[rest-inputs][rest-inputs] `:1528`, [rest-converter][rest-converter]
`:599/:604/:605/:1044`, [utils-inputs][utils-inputs] `:200/:1338`), plus 2
call-free Decision-9 aliases ([filters-inputs][filters-inputs] `:68`,
[orders-inputs][orders-inputs] `:55`, read only by tests) and the
[utils-inputs][utils-inputs] `:52` compat re-export (zero in-repo readers —
comment only, homed in that file's verified `module-mechanics`);
`snake_case` — 3 sites in [walker][walker] (`:410/:768/:1420`);
`pascal_case` — [types-converters][types-converters] `:775`,
[rest-converter][rest-converter] `:885`; `pascal_case_or_raise` —
[filters-inputs][filters-inputs] `:260`, [sets-mixins][sets-mixins] `:114`;
`flatten_lookup_path` — [utils-inputs][utils-inputs] `:199`,
[utils-permissions][utils-permissions] `:76`, [orders-sets][orders-sets]
`:729`. Every site composes by call; what differs per flavor is the
surrounding triple/spec/alias shape, never the caser body. Discharged: no
mirrored policy body.

2. **Sync/async twins.** Five pure string functions over exact `str`; no
`await`, no I/O, no executor color. The `lru_cache` memo is thread-safe and
color-free. No twin owed by construction. Discharged.

3. **Derived rather than repeated knowledge.** Each neighboring derivation
was censused and either composes or is rejected with a trigger:
`LOOKUP_NAME_MAP` pins only the irregulars derivation cannot produce
(`icontains`→`iContains` has no underscore; `in` is a keyword) — R2;
Strawberry `to_camel_case` at 8 sites in 3 files predicts the
schema-published vocabulary and deliberately disagrees with the package
caser (`field_2`/`field2` collapse) — R1; reverse maps are recorded at
build (`InputFieldSpec`, `GeneratedInputFieldSpec`) or derived by name
(`_FORM_KEY_BY_PYTHON_ATTR`), never re-spelled — R3; `replace("__", "_")`
has exactly one site (`:266`); `.capitalize()` has exactly the two
in-grammar sites (`:192-193`, `:248`); the `__x` marker has exactly one
encoder (`:247`) and one decoder (`:57-73`); the edge-split twin (R7) and
the digit-boundary sub-rule (R8) are same-file intentional separations.
Discharged: one derivation per fact, consumers by name.

4. **Inverse / round-trip pairs.** `graphql_camel_name` ↔ `snake_case` are
one grammar in two halves, co-sited in this module, pinned by a 22-literal
round-trip oracle. `pascal_case` is one-way by contract (case-folding and
interior-collapse are documented losses); `flatten_lookup_path` is one-way
(collapse). The table reverse (`_FORM_KEY_BY_PYTHON_ATTR`) derives from
`LOOKUP_NAME_MAP` by comprehension, first-match-wins preserved. Discharged:
pairs co-sited, never split across modules.

5. **Contracts restated in another medium.** Production: the target.
Oracles (all literal, none reading an owner table): HEAD
[test-strings][test-strings] — 12 tests pinning every rule (round-trip 22,
acronym/digit/edge 6, pascal stems, empty edges, flatten incl.
idempotence, hostile-subclass across 4 entries, `__x` escape + literal
discrimination, guard delegation + raise, non-str rejection ×4, cache
controls incl. `__wrapped__`); HEAD [test-filters-inputs][test-filters-inputs]
pins the alias (`""`, `"_"`, `"galaxy_name"`); live pins per the oracle
module docstring in [live-composition][live-composition] (introspection)
and [live-library][live-library] (34 camel-name hits). The worktree oracle
dirt (2+/1-, exact-message pin) is concurrent-unattributed and was not
relied on. Projections: module + per-function docstrings, the
[utils-init][utils-init] bullet, the TREE.md line, and owner-citing
consumer comments (triple emitter, `_pascal_case`, `type_name_for`,
`_check_method_name`, audit). No glossary or README projection (`git grep`
empty). Discharged: media classified, oracles independent.

6. **Enforcement by omission.** `_plain_text` guards all 5 public entries
(4 direct, `pascal_case_or_raise` via delegation);
`_snake_case_cached` is reachable only through `snake_case` plus its 3
control assigns (whole-package census); the `LOOKUP_NAME_MAP.get`
fallthrough is that table's contract (owned in verified
[filters-inputs][filters-inputs]), not a gap here; the snake memo is
correctly off the subsystem-clear bus (pure `str`→`str`, nothing to
invalidate — and the [utils-relations][utils-relations] precedent is also
test-cleared, not bus-registered). The exact-`str` fast path exists exactly
where the hot path calls (this normalizer). Discharged: no gap.

### Enumeration

Instrument: `ast.Module.body` over HEAD bytes — 15 statements: module
docstring, 3 imports, `__all__`, 7 function defs, 3 cache-control assigns.
Every member is homed below; the `__x` halves home with their functions
(FL2 decoder, FL5 encoder), the twin pairs with their rejections.

| # | Member | Home |
|---|---|---|
| 0 | module docstring | FL0 (rule-map projection) |
| 1 | `import functools` | FL0 (cache + wraps machinery) |
| 2 | `from collections.abc import Callable` | FL0 (annotation-only) |
| 3 | `from …exceptions import ConfigurationError, _safe_type_name` | FL0 (both composed by call in FL1) |
| 4 | `__all__` (exact 5) | FL0 |
| 5 | `_plain_text` | FL1 |
| 6 | `_snake_case_cached` | FL2 |
| 7 | `snake_case` | FL2 |
| 8 | `snake_case.cache_clear` | FL2 (lifetime; R5 refused the shared helper) |
| 9 | `snake_case.cache_info` | FL2 (lifetime; R5 refused the shared helper) |
| 10 | `snake_case.cache_parameters` | FL2 (lifetime; R5 refused the shared helper) |
| 11 | `pascal_case` | FL3 (edge half of R7, digit half of R8) |
| 12 | `pascal_case_or_raise` | FL4 |
| 13 | `graphql_camel_name` | FL5 (edge half of R7, digit half of R8) |
| 14 | `flatten_lookup_path` | FL6 |

15/15 homed. No member routes to a family: the two cross-file sameness
sights on this surface are already held — the enum-stem template by open
`generated-choice-enum-name-template`, the normalizer twins by verified
rows (X1–X4, X6).

### Challenges

Counts are authoritative definitions forced per posited change; consumers,
oracles, and projections that also move are listed, never counted.

- **C1 — marker grammar.** `__x` becomes another escape: encoder (`:247`)
plus decoder (`:57-73`) move together — 1 file. Consumers 0; round-trip +
escape oracles move.
- **C2 — digit boundary dropped.** `pascal_case` `:191-194` plus
`graphql_camel_name` `:244-246` — 2 spellings, 1 file, different
encodings/conditions; extraction refused (R8). Consumers 0; stem + wire
oracles move.
- **C3 — edge rule dropped.** `pascal_case` `:195-196` plus
`graphql_camel_name` `:238-239` — 2 byte-identical spellings, 1 file;
extraction refused (R7). Consumers 0; edge oracles move.
- **C4 — normalizer accepts a new kind.** `_plain_text` alone — count 1;
the twins keep their postures per X1–X3. Consumers 0; rejection oracles
move.
- **C5 — error type changes.** The FL1 message site — count 1; twin
messages are separately owned (X1–X3). Consumers 0; message oracles move.
- **C6 — acronym rule changes.** `_snake_case_cached` — count 1; the
walker composes (its forward maps cover the miss). Consumers 0; acronym
oracles move.
- **C7 — memo policy changes.** The `:50` decorator — count 1; the
[utils-relations][utils-relations] and [utils-permissions][utils-permissions]
memos have disjoint keys/lifetimes (R5). Consumers 0; cache-control
oracles move.
- **C8 — collapse rule changes.** `flatten_lookup_path` — count 1; the
3 mangle sites compose; the Prefetch `$` grammar is a different rule
(R4). Consumers 0; flatten oracles move.
- **C9 — emptiness guard moves into `pascal_case`.** `pascal_case_or_raise`
plus 2 `make_error` arms — the guard rule has 1 owner; the call shape is
unchanged so consumers adapt 0. Guard oracles move.
- **C10 — irregular lookup added.** `LOOKUP_NAME_MAP` only — count 1, and
0 in this file: proves the table is not a restatement of the derivation
(R2). Filter oracles move.
- **C11 — Strawberry changes `to_camel_case`.** 0 here: the 8 prediction
sites shift with upstream while `graphql_camel_name` stands — proves
separate contracts (R1). Audit oracles move.
- **C12 — sixth helper added.** `__all__` here — count 1; the
[utils-init][utils-init] pinned set is a separate decision (it carries 2
of 5 today). Consumers 0.

## Findings

### FL0 — `strings-module-mechanics` (file-local)

- **Contract + variation.** The leaf's mechanics: a 4-bullet rule-map
docstring, `functools` (cache + wraps), annotation-only `Callable`, the
[exceptions][exceptions] pair (`ConfigurationError` raised, `_safe_type_name`
composed by call — the one safe renderer, no second spelling here), and an
exact-5 `__all__` with zero star-importers (whole-package census).
- **Sites + roles.** Definition: the target (`:0-30`). Consumers: every
importer reads the submodule by name; [utils-init][utils-init] re-exports 2
of 5 (verified file-local there); [utils-inputs][utils-inputs] `:52`
re-exports 1 (verified file-local there, zero in-repo readers). Oracles:
`__all__` membership is pinned transitively by the import lines of every
oracle. Projections: the docstring bullets, the TREE.md line.
- **Challenges.** C12 count 1.
- **Owner + lifetime.** The target (principle 7 — every consumer already
depends on `utils`). No stored derivation.
- **Freshness.** Target as header; [utils-init][utils-init] `1a4c2ec8`,
[utils-inputs][utils-inputs] `ee31d360`, [exceptions][exceptions] `e06b0b7f`.

### FL1 — `strings-plain-text-guard` (file-local)

- **Contract + variation.** One normalizer for the boundary: exact-`str`
fast path first (the walker's every call), `ConfigurationError` naming the
safe kind for a non-string, `str.__str__` copy for a subclass so hostile
`__hash__`/`split`/`replace`/`__str__` never run in the helpers or the
cache. Varies on accepted kinds and the message; the twins vary
independently (X1–X3).
- **Sites + roles.** Definition: `_plain_text` (`:33-47`). Consumers (5,
all in-file): the 4 direct normalizations (`:130`, `:187`, `:234`, `:264`)
plus `pascal_case_or_raise` via delegation. Oracles: hostile-subclass pins
across 4 entries, non-str rejection ×4 (all literal).
- **Challenges.** C4 + C5 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header.

### FL2 — `strings-snake-reversal-and-memo` (file-local)

- **Contract + variation.** The exact inverse of FL5 over lowercase
snake-case identifiers: `__x` consumption between two uppercase characters
only (`:57-73`), acronym-run cohesion with title-case split, digit
attachment, lossy Strawberry boundaries documented with the caller's
recourse (forward-name match at
[walker][walker]`::_field_by_graphql_name`). The `wraps` keeps the
function's own name and docstring (pinned) while exposing `__wrapped__`;
the 3 control assigns publish the memo's controls. Varies on acronym,
digit, and marker rules (C1, C6); the memo policy (C7).
- **Sites + roles.** Definition: `_snake_case_cached` + `snake_case` +
3 assigns (`:50-135`). Consumers: [walker][walker] `:410/:768/:1420`.
Oracles: reversal pins, 22-literal round-trip, `__x` discrimination,
cache-control (hit/miss/name/`__wrapped__`). Projections: the docstring's
inverse claim + Strawberry-loss table.
- **Challenges.** C1 count 1 file, C6 + C7 count 1.
- **Owner + lifetime.** The target. Stored derivation: process-global
`lru_cache(2048)` keyed by exact `str`; pure values, nothing to
invalidate — correctly off the subsystem-clear bus (Matrix axis 6); tests
clear directly.
- **Freshness.** Target as header; [walker][walker] `75f9c6b6`.

### FL3 — `strings-pascal-stem-grammar` (file-local)

- **Contract + variation.** Lossy `PascalCase` stems: edges preserved
verbatim, interior runs collapsed (so `LOOKUP_SEP` paths stem per
segment), digit-leading separators retained (injectivity over
`field_2`/`field2`), per-segment `capitalize` (acronyms folded —
injective over lowercase input only), token-less input → `""`. Varies on
edge (R7), digit (R8), and folding rules.
- **Sites + roles.** Definition: `pascal_case` (`:138-197`). Consumers:
[types-converters][types-converters] `:775`,
[rest-converter][rest-converter] `:885` (both enum stems; their shared
template is held by open `generated-choice-enum-name-template`, not here),
plus FL4 by delegation. Oracles: stem pins incl. the `price`/`price_`/
`_price` regression note and the silent-empty pin.
- **Challenges.** C2 + C3 (shared halves, 1 file).
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [types-converters][types-converters]
`058f1081`, [rest-converter][rest-converter] `6652d092`.

### FL4 — `strings-pascal-emptiness-guard` (file-local)

- **Contract + variation.** The no-token check both stem consumers wrap:
`""` from FL3 becomes `make_error(name)`, keeping each consumer's error
type and message while the emptiness rule stays single-sited. Varies on
the emptiness definition and the injection shape (C9).
- **Sites + roles.** Definition: `pascal_case_or_raise` (`:200-214`).
Consumers (2, both by call with own errors):
[filters-inputs][filters-inputs]`::_pascal_case` (`:260`, RangeFilter
message), [sets-mixins][sets-mixins]`::type_name_for` (`:114`, per-field
message); each docstring names the sharing. Oracles: delegation + raise
pins with an injected `ValueError`.
- **Challenges.** C9 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [filters-inputs][filters-inputs]
`82b52d97`, [sets-mixins][sets-mixins] `ad8987ea`.

### FL5 — `strings-camel-forward-grammar` (file-local)

- **Contract + variation.** Injective `camelCase` over normalized
snake-case identifiers: head kept, later segments capitalized, edges
preserved, empty tokens literal, digit-leading separators retained,
adjacent-uppercase separators escaped as `__x` (`:247`). Varies on every
injectivity axis (C1–C3); the Strawberry disagreement is contractual (R1).
- **Sites + roles.** Definition: `graphql_camel_name` (`:217-249`).
Consumers: 12 call sites in 5 files (Matrix axis 1) — every generated
input's wire name. Oracles: 22-literal round-trip, `a_a_a`→`aA__xA`,
alias pins in [test-filters-inputs][test-filters-inputs], live SDL pins.
- **Challenges.** C1 count 1 file; C2 + C3 (shared halves, 1 file).
- **Owner + lifetime.** The target (principle 7 — [utils-inputs][utils-inputs]
`:47` records the ownership). Pure derivation, never stored.
- **Freshness.** Target as header; [utils-inputs][utils-inputs] `ee31d360`,
[forms-inputs][forms-inputs] `6418753d`, [mutations-inputs][mutations-inputs]
`fc442047`, [orders-inputs][orders-inputs] `6f6ec946`,
[rest-inputs][rest-inputs] `2410f380`, [rest-converter][rest-converter]
`6652d092`.

### FL6 — `strings-lookup-flatten-mangle` (file-local)

- **Contract + variation.** Every run of 2+ underscores becomes one, so
`LOOKUP_SEP` never survives into a generated identifier. Terminates
(collapse is strictly shortening); inputs are declared field paths.
Varies on the collapse shape (C8).
- **Sites + roles.** Definition: `flatten_lookup_path` (`:252-267`).
Consumers (3, all by call with one-owner comments):
[utils-inputs][utils-inputs] `:199` (python-attr derivation),
[utils-permissions][utils-permissions] `:76` (`check_*_permission`
mangle, behind a memoized wrapper), [orders-sets][orders-sets] `:729`
(aggregate alias). Oracles: flatten pins incl. idempotence.
- **Challenges.** C8 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [utils-inputs][utils-inputs] `ee31d360`,
[utils-permissions][utils-permissions] `9889d6fe`, [orders-sets][orders-sets]
`6044ab1a`.

### R1 — `strings-camel-vs-strawberry-prediction` (rejected, fresh)

Strawberry `to_camel_case` at 8 production sites in 3 files
([mutations-inputs][mutations-inputs] `:189`,
[walker][walker] `:258/:313/:322`,
[types-finalizer][types-finalizer] `:260/:265/:271/:749`) predicts the
name the SCHEMA publishes under the default `NameConverter`; FL5 mints
the name generated inputs pin. The two disagree by contract (`field_2`
vs `field2` collapse to one under upstream), and substituting the
package caser into any predictor lets a collision through — the
[mutations-inputs][mutations-inputs] audit docstring states exactly
that failure. C11 moves 0 here. Durable homes: that docstring,
[utils-inputs][utils-inputs] `:1266`, the FL5 docstring. Trigger: an
upstream converter change making the vocabularies agree, or generated
inputs abandoning injectivity. Freshness: target as header;
`fc442047`, `75f9c6b6`, `de34ae2a`.

### R2 — `strings-camel-vs-lookup-table` (rejected, fresh)

`LOOKUP_NAME_MAP` ([filters-inputs][filters-inputs] `:101`) pins the
irregular vocabulary derivation cannot produce: `icontains`→`iContains`
has no underscore to split on, and `in` cannot be a dataclass field —
the table's own comment states both. Its reverse derives by name
([filters-sets][filters-sets] `:138`, first-match-wins preserved).
C10 moves 0 here. Durable home: the table comment. Trigger: the lookup
vocabulary becoming derivable (underscored Django names for every
irregular). Freshness: target as header; `82b52d97`, `993e887a`.

### R3 — `strings-reverse-vs-recorded-maps` (rejected, fresh)

Wire→python at read time reverses with FL2; wire→python at build time is
recorded (`InputFieldSpec`, `GeneratedInputFieldSpec`) because generated
inputs pin explicit names the reversal need not recover. The walker is
the one site that must derive (selections carry wire names only), and
even it forward-matches on a miss. Recording and deriving answer
different questions; unifying them means either dropping recorded specs
(then every resolver reverses, lossy) or pre-recording selections
(impossible — they arrive per request). Note: the worktree carries the
ledger-owned `mutation-input-reverse-map` owner
(`relation_input_python_attr`), absent at HEAD by design; this finding
is at HEAD bytes and moves nothing there. Trigger: generated inputs
dropping recorded specs. Freshness: target as header; `ee31d360`,
`fc442047`, `75f9c6b6`.

### R4 — `strings-flatten-vs-dunder-grammars` (rejected, fresh)

Whole-package dunder census, population = sites that read LOOKUP_SEP
path structure: FL6 is the single collapse-to-identifier site (`:266`);
the rest are traversal splits (`connection.py:800`,
`filters/base.py:660`, `plans.py:679`, `plans.py:700` — the defer
head-segment split), refusal/branch guards (9 sites), and the Prefetch
`to_attr` `$` escape grammar — collapse, split, refuse, and escape are
four rules, not one. Four `startswith("__")` screens sit outside the
population: a leading `__` is a reserved-prefix token (GraphQL spec /
Python dunder), not LOOKUP_SEP — `conf.py:343` (dunder-attr
`AttributeError`), `types/base.py:1295` + `types/definition.py:257`
(GraphQL-name gates, held by open `graphql-name-gate`),
`types/converters.py:621` (sanitize-posture sibling). Merging collapse
into any other arm changes what Django splits on. Durable home: this
row. Trigger: a second collapse-to-identifier need. Freshness: target
as header; `ee31d360`, `9889d6fe`, `6044ab1a`, `c6ad46aa` (out),
`dda91365` (out), `058f1081` (out), `fa6c4d33` (out), `cce98531`
(4th split).

### R5 — `strings-memo-vs-shared-wrapper` (rejected, fresh)

Three memo wirings, three lifetimes: FL2's pure-`str`→`str` memo with 3
published controls; [utils-relations][utils-relations]' model-keyed twin
memos with a custom two-cache clear (test-cleared, not bus-registered);
[utils-permissions][utils-permissions]' inline `@lru_cache` on the
mangle wrapper. A shared wrapper would need knobs for key shape,
control surface, and clear fan-out — machinery hiding three one-paragraph
lifetimes. Durable home: this row. Trigger: a fourth memo needing FL2's
exact control trio over pure values. Freshness: target as header;
`8dbc3fe6`, `9889d6fe`.

### R6 — `strings-exact-gate-vs-shared` (rejected, trigger-check)

Standing-J2 trigger check: `type(…) is str` appears in exactly 3 files
([utils-imports][utils-imports], [utils-strings][utils-strings],
`utils/querysets.py` ×5). FL1's gate is a hot-path fast lane (the
walker's every call) fused with its validity check, not a shareable
verdict — same direction as verified J2. Trigger unfired (no two
gates, one message). Durable home: the standing J2 row. Freshness:
target as header; `291ecedd`.

### R7 — `strings-edge-split-twin` (rejected, fresh, same-file)

`pascal_case` `:195-196` and `graphql_camel_name` `:238-239` compute
leading/trailing runs with byte-identical expressions (`diff` of the two
ranges is empty; `:197` has no twin). One rule
("edges are identity"), two spellings, one file — and each grammar's docstring
states its edge rule as part of its contract (principle 10), so a
`_split_edges` helper would move the statement away from both owners to
save a two-spot edit in one file. C3 count: 2 spellings, 1 file.
Durable home: this row. Trigger: a third edge-splitting site, in or out
of this file. Freshness: target as header.

### R8 — `strings-digit-sub-rule-twin` (rejected, fresh, same-file)

Both grammars retain the separator before a digit-leading segment
("capitalization cannot encode that boundary"), but the encodings and
conditions differ: FL3 filters empties then join-capitalizes, FL5 keeps
empty tokens literal and threads `__x` state. A shared helper needs
mode flags for exactly the parts that differ. C2 count: 2 spellings, 1
file. Durable home: this row. Trigger: the encodings converging, or a
third consumer. Freshness: target as header.

### X1 — imports `_plain_text` twin (CONVERGE, row stands)

Verified `imports-plain-text-vs-strings-twin` re-checked at HEAD:
[utils-imports][utils-imports] `:54` still passes non-strings through
(and still imports no `ConfigurationError` — stdlib-only layering
holds), FL1 still fails closed with the typed error. Bodies re-read,
trigger unfired. No new row; the standing row stands. Freshness:
`291ecedd`.

### X2 — input-values `_field_name` twin (CONVERGE, row stands)

Verified `input-values-field-name-vs-strings-twin` re-checked at HEAD:
[utils-input-values][utils-input-values] `:60` still carries its own
per-subject message ("Set input field names must be strings…",
input-type attributed) vs FL1's boundary message — the verified
`policies` R3 direction. Trigger (generalized message or third
normalizer) unfired. No new row. Freshness: `f2566609`.

### X3 — pk-name normalizer (CONVERGE, row stands)

Verified `types-definition-pk-normalize-vs-boundary-normalize`
re-checked at HEAD: [types-definition][types-definition]
`_normalize_pk_name` still returns `None` for malformed input where FL1
raises — posture difference unchanged. Trigger (unify-needs-verdict
flag) unfired. No new row. Freshness: `fa6c4d33`.

### X4 — token encoder (CONVERGE, row stands)

Verified `token-encoder-vs-pascal-case` re-checked at HEAD:
[utils-inputs][utils-inputs]`::pascalize_token` is still the injective
escape grammar (`_u`/`_c`/`_x`/`X_h`/`X_l`/`X_d`/`X_z`) vs FL3's lossy
fold — owner-recorded separation both sides, bodies re-read. Trigger
unfired. No new row. Freshness: `ee31d360`.

### X5 — str-slot idiom (CONVERGE, row stands)

Verified `utils-sessions-str-slot-flatten` re-checked at HEAD: 34
`str.__str__` hits in 14 files — the base-slot call is the shared form,
and FL1's line is this boundary's content-normalization use of it.
Trigger (primitive failure or second content read) unfired. No new row.
Freshness: `e06b0b7f` for the sibling renderer bodies.

### X6 — relations non-walk mechanisms (CONVERGE, row stands)

Verified `utils-relations-non-walk-mechanisms` re-checked at HEAD: FL6
re-read, still a spelling mangle rather than any of the four path
walkers — declaration hops, spelling mangler, registry-graph, and
selection descent stay distinct. Trigger unfired. No new row.
Freshness: `8dbc3fe6`.

## Defects

None. The examinations that could have produced one all closed clean at
HEAD bytes: every index in the reversal loop is length-guarded, the
`part[0]` reads sit behind non-empty filters, `camel[-1]` behind a
non-empty guard, the collapse loop is strictly shortening over declared
(not wire) inputs, hostile-subclass closure before the cache is pinned
by oracle, and the worktree oracle dirt pins the exact HEAD message
rather than contradicting it.

## Judgment

The boundary-naming surface is already one owner per rule: five
transforms each defined once in this module and composed by name from
every flavor, with the neighboring derivations (lookup table, upstream
predictor, recorded maps, token encoder, twin normalizers) each carrying
a contract difference and a trigger. Zero-edit stands.

## Index rows for Worker-0

| `strings-module-mechanics` | `django_strawberry_framework/utils/strings.py` (docstring + 3 imports + exact-5 `__all__`, zero star-importers) | `django_strawberry_framework/utils/strings.py` | File `utils/strings.py` | file-local |
| `strings-plain-text-guard` | `django_strawberry_framework/utils/strings.py::_plain_text` (exact-str fast path + ConfigurationError + subclass copy; 5 in-file consumers) | `django_strawberry_framework/utils/strings.py` | File `utils/strings.py` | file-local |
| `strings-snake-reversal-and-memo` | `django_strawberry_framework/utils/strings.py::snake_case` (+ `_snake_case_cached` + 3 control assigns; `__x` decoder, pure 2048-memo, off the clear bus) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/optimizer/walker.py` | File `utils/strings.py` | file-local |
| `strings-pascal-stem-grammar` | `django_strawberry_framework/utils/strings.py::pascal_case` (edges verbatim, interior collapse, digit retention, lowercase-only injectivity, `""` on token-less) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | File `utils/strings.py` | file-local |
| `strings-pascal-emptiness-guard` | `django_strawberry_framework/utils/strings.py::pascal_case_or_raise` (no-token check + injected `make_error`; 2 consumers by call) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/sets_mixins.py` | File `utils/strings.py` | file-local |
| `strings-camel-forward-grammar` | `django_strawberry_framework/utils/strings.py::graphql_camel_name` (injective camelCase + `__x` encoder; 12 call sites in 5 files) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/filters/inputs.py` | File `utils/strings.py` | file-local |
| `strings-lookup-flatten-mangle` | `django_strawberry_framework/utils/strings.py::flatten_lookup_path` (run-collapse to one; 3 mangle sites by call) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/orders/sets.py` | File `utils/strings.py` | file-local |
| `strings-camel-vs-strawberry-prediction` | `django_strawberry_framework/utils/strings.py::graphql_camel_name` (rejection recorded here; fresh — minted injectivity vs schema-published prediction, disagree by contract; trigger: upstream converter change or injectivity abandoned) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/finalizer.py` | File `utils/strings.py` | rejected |
| `strings-camel-vs-lookup-table` | `django_strawberry_framework/utils/strings.py::graphql_camel_name` (rejection recorded here; fresh — derivation vs irregular vocabulary, owner-stated; trigger: lookups becoming derivable) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py` | File `utils/strings.py` | rejected |
| `strings-reverse-vs-recorded-maps` | `django_strawberry_framework/utils/strings.py::snake_case` (rejection recorded here; fresh — read-time reversal vs build-time records; walker is the one must-derive site; trigger: recorded specs dropped) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/optimizer/walker.py` | File `utils/strings.py` | rejected |
| `strings-flatten-vs-dunder-grammars` | `django_strawberry_framework/utils/strings.py::flatten_lookup_path` (rejection recorded here; fresh — single collapse site vs splits/guards/`$`-escape; trigger: second collapse need) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/orders/sets.py` | File `utils/strings.py` | rejected |
| `strings-memo-vs-shared-wrapper` | `django_strawberry_framework/utils/strings.py::snake_case` (rejection recorded here; fresh — three memos, three lifetimes, shared wrapper needs knobs; trigger: fourth memo needing this exact trio) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/utils/permissions.py` | File `utils/strings.py` | rejected |
| `strings-exact-gate-vs-shared` | `django_strawberry_framework/utils/strings.py::_plain_text` (rejection recorded here; standing-J2 trigger-check — hot-path fast lane, 3-file census; trigger: two gates, one message) | `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/imports.py` | File `utils/strings.py` | rejected |
| `strings-edge-split-twin` | `django_strawberry_framework/utils/strings.py::pascal_case` (rejection recorded here; fresh same-file — byte-identical pair, grammar prose owns each half; trigger: third edge-splitting site) | `django_strawberry_framework/utils/strings.py` | File `utils/strings.py` | rejected |
| `strings-digit-sub-rule-twin` | `django_strawberry_framework/utils/strings.py::pascal_case` (rejection recorded here; fresh same-file — differing encodings, shared helper needs mode flags; trigger: encodings converge or third consumer) | `django_strawberry_framework/utils/strings.py` | File `utils/strings.py` | rejected |

## Families

None new. Zero adoptions. Six convergences onto standing rows
(`imports-plain-text-vs-strings-twin`, `input-values-field-name-vs-strings-twin`,
`types-definition-pk-normalize-vs-boundary-normalize`,
`token-encoder-vs-pascal-case`, `utils-sessions-str-slot-flatten`,
`utils-relations-non-walk-mechanisms` — triggers re-checked in X1–X6,
their rows stand). Eight fresh rejections (R1–R8). The enum-stem
template sameness stays held by open `generated-choice-enum-name-template`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[rest-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rest-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py
[utils-input-values]: ../../django_strawberry_framework/utils/input_values.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-filters-inputs]: ../../tests/filters/test_inputs.py
[test-strings]: ../../tests/utils/test_strings.py

<!-- examples/ -->
[live-composition]: ../../examples/fakeshop/test_query/test_schema_composition_api.py
[live-library]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Traced expectation-first: required reading, full HEAD target read
(`991f7dad`, 267 lines), AST enumeration over HEAD bytes,
HEAD-vs-worktree diff (2 hunks, 5+/3-), item-scoped diff vs
`ITEM_BASELINE=f481b18e` (empty on the target — the baseline tree
already carries `5a4f4811`, so the dirt predates the item by
mechanics; content attribution below is independent of that fact),
whole-package consumer greps at HEAD, and the connected sites plus
both oracle files opened — all before this artifact's `## Findings`.
HEAD `0c0537e2` unmoved at start; worktree blob `5a4f4811`
(269 lines); path `M`.

My trace. Enumeration instrument: `ast.Module.body` over HEAD bytes —
15 statements: module docstring, 3 imports (`functools`,
`collections.abc`, `exceptions`), `__all__`, 7 defs (`_plain_text`,
`_snake_case_cached`, `snake_case`, `pascal_case`,
`pascal_case_or_raise`, `graphql_camel_name`,
`flatten_lookup_path`), 3 cache-control assigns. Six rules, all owned
here:

1. Boundary normalizer (`_plain_text`, definition). Consumers: the 4
   in-file normalizations + `pascal_case_or_raise` by delegation.
   Oracles: hostile-subclass and non-str pins (literals). Posited
   change (new accepted kind / message): count 1.
2. Snake reversal + memo (`_snake_case_cached` + `snake_case` + 3
   assigns, definition). Consumers: walker ×3 by call. Oracles:
   round-trip, `__x` discrimination, cache controls. Change
   (marker/acronym/memo): count 1 file.
3. Pascal stems (`pascal_case`, definition). Consumers: 2 enum stems
   + FL4 by delegation. Change (edge/digit/fold): count 1 file.
4. Emptiness guard (`pascal_case_or_raise`, definition). Consumers:
   2 by call with own errors. Change (emptiness definition): 1.
5. Camel forward (`graphql_camel_name`, definition). Consumers: 12
   call sites in 5 files + aliases. Change (any injectivity axis):
   1 file.
6. Lookup flatten (`flatten_lookup_path`, definition). Consumers: 3
   mangle sites. Change (collapse shape): 1.

Matrix expectations: axis 1 — the target is the seam, flavors share
by call; axis 2 — pure functions, no twin owed; axis 3 — one
derivation per fact (`LOOKUP_NAME_MAP` irregulars, upstream
predictor, recorded maps, `pascalize_token` escapes stay separate);
axis 4 — camel/snake one grammar in two halves, co-sited; axis 5 —
test literals are oracles, docstrings/TREE are projections; axis 6 —
`_plain_text` covers all 5 entries, memo off the clear bus by
purity. Hunk expectation (content): both hunks are the truthful-reads
migration (`truth.is_instance`/`truth.kind`, `_safe_type_name`
import dropped) — external, matching the hunt's untracked
`utils/truth.py` and the same one-line pattern across the dirty
sibling files; no `## Owned changes` row names this file.

AGREE, each independently reproduced at HEAD bytes:

- Enumeration 15/15 member-by-member: every row matches my census
  above (order, kinds, homes). The 7-def / 3-assign / 3-import
  split is exact.
- Hunk attribution: both hunks re-diffed; `truth.py` absent from
  `git ls-tree HEAD utils/`, worktree status `??` (with `lazy.py`
  and both truth/lazy test files); ledger has no strings row;
  `exceptions.py` lost `_safe_type_name` in the worktree, so the
  hunks track the migration, not an invention. Concurrent-external
  stands.
- R1: 8 call sites re-grepped line-by-line (`mutations-inputs`
  `:189`, walker `:258/:313/:322`, finalizer `:260/:265/:271/:749`);
  the audit docstring states the substitution failure verbatim.
  Contract difference + trigger stand.
- R2: table `:101` with the owner-stated irregular comment,
  first-match-wins reverse `:138`. Stands.
- R3: `relation_input_python_attr` confirmed absent at HEAD;
  ledger adoption row confirmed present; walker is the one
  must-derive site. Stands.
- R5: relations twin memos + custom two-cache clear (`:521/:551`
  + `:599-611`), permissions inline memo (`:66`); `lru_cache`
  appears in exactly these 3 utils files. Stands.
- R6: `type(…) is str` re-grepped: exactly 3 files
  (imports ×1, strings ×1, querysets ×5). Trigger unfired. Stands.
- R7 substance: the leading/trailing pair is byte-identical;
  package-wide `lstrip/rstrip("_")` census finds no third site —
  trigger unfired. (Citation blemish below; substance stands.)
- R8: both bodies re-read, encodings/conditions differ as stated;
  `isdigit` census finds no third digit-boundary consumer —
  trigger unfired. Stands.
- X1–X6: all six standing rows exist in the plan with matching
  triggers; all six bodies re-read at HEAD (`imports.py:54`
  pass-through, no `ConfigurationError` import; `input_values.py:60`
  per-subject message; `_normalize_pk_name` None-posture;
  `pascalize_token` `_u`/`_c`/`_x`/`X_h`/`X_l`/`X_d`/`X_z`
  escapes; 34 `str.__str__` occurrences in 14 files; relations
  walkers vs mangle). Every trigger unfired; every row stands.
- Consumer census: 12 camel call sites in 5 files + 2 aliases +
  1 zero-reader re-export, 3 snake sites, 2 pascal sites, 2 guard
  sites, 3 mangle sites — every cited line re-grepped exact.
- Oracles: HEAD test file 207 lines / 12 tests; 22-literal
  round-trip, 6 acronym pairs, 4-entry hostile pin, 4-helper
  rejection pin, cache controls incl. `__wrapped__`; alias pins
  (`""`, `"_"`, `"galaxy_name"`) in `f31757d2`; worktree oracle
  dirt (2+/1- exact-message pin) correctly not relied on.
- All 22 freshness fingerprints re-hashed exact; no second
  definition of any transform (`def` census is strings-only);
  `__x` has one encoder/one decoder; `_snake_case_cached` has no
  out-of-file readers; zero star-importers; `__all__` exact-5;
  `utils/__init__` carries 2 of 5; `utils/inputs.py:47` ownership
  record confirmed; `$` escape grammar real; challenges C1–C12
  counts all reproduce; `## Pending execution` correctly absent
  (all `static-reviewed`; executing would run migrated bytes);
  scaffold intact (10/10 group headers); ruff gates vacuous-pass
  (`.md`-only change); AGENTS.md prose clean.
- Zero-defect call: every guard re-read at HEAD — reversal
  indices length-guarded (`i + 3 < len`, guarded
  previous/following), both `part[0]` reads behind non-empty
  filters, `camel[-1]` behind the non-empty guard, collapse loop
  strictly shortening over declared paths, hostile-subclass
  closure before the cache pinned by oracle. No new Worker-2
  defects.

DIFFER on record accuracy only — 2 blemishes, neither
verdict-moving, each reproducible below. Per the cycle's
record-accuracy bar (File `utils/sessions.py` W2:
`revision-needed` for verdict-neutral blemishes), this is
`revision-needed`, not `verified`: resubmission to the SAME W1
context (no re-trace; every judgment stands; fix the prose, keep
the verdicts).

1. R7 range over-includes by one line. R7 (repeated in C3) cites
   "`pascal_case` `:195-197`" against "`graphql_camel_name`
   `:238-239`" as "byte-identical expressions" — but `:197` is
   `return f"{leading}{stem}{trailing}"`, which has no twin in
   the camel range (camel reattaches at `:240` with `{camel}`).
   The byte-identical pair is `:195-196` vs `:238-239`
   (mechanical: extract both ranges, `diff` — 2 lines vs 2
   lines, empty diff). Fix both citations to `:195-196`.
   Substance (refused extraction, 1-file count, third-site
   trigger) stands verbatim.
2. R4 census undercounts its own population. "Whole-package
   `"__"` census … refusal/branch guards (9 sites)" with the
   exhaustive "the rest are" framing reproduces as the nine
   `"__" in` guard sites (`connection.py:884`,
   `filters/inputs.py:870/:885/:928`, `keyset.py:202`,
   `lateral_fetch.py:1140`, `nested_planner.py:192/:264`,
   `plans.py:843`) — but omits five same-population code sites:
   the `startswith("__")` refusal guards at `conf.py:343`
   (raises `AttributeError`), `types/base.py:1295`,
   `types/converters.py:621`, `types/definition.py:257` (all
   three raise `ConfigurationError`), and the `"__"`-branching
   defer-coverage check at `plans.py:698/700`. Dispose all five
   on one stated basis: fold them into the guard count with a
   corrected number, or rule them out-of-population with a
   reason (e.g. GraphQL reserved-prefix / settings-dunder rule
   ≠ `LOOKUP_SEP` rule). Rejection (single collapse site,
   four rules not one) and trigger stand; corrected numbers
   strengthen them.

HEAD movement check: `0c0537e2` at dispatch, at every W2 check,
and at verdict; target worktree blob `5a4f4811` stable; no new
ledger row names this file; plan untouched by W2 per dispatch.
Verdict: `revision-needed` on record accuracy (SAME W1 context,
prose-only fixes 1–2 above); all judgments stand pending them.

## Iterations

### Pass 2 (record-accuracy revision, same W1 context)

W2 verdict `revision-needed` on 2 prose blemishes; every judgment
stood. No re-trace, no verdict change, no production or plan edit.
(1) R7/C3 range `:195-197` → `:195-196` vs `:238-239`, both
citations (pair re-proven byte-identical by empty `diff` this pass;
`:197` has no twin). (2) R4 census completed on the stated
population basis (sites that read LOOKUP_SEP path structure):
`plans.py:700` folded in as the 4th traversal split; the 4
`startswith("__")` screens ruled out-of-population (reserved-prefix /
dunder-attr rule ≠ LOOKUP_SEP rule), all five fingerprinted.
HEAD `0c0537e2` unmoved; target blobs unchanged (`991f7dad` /
`5a4f4811`); resubmitted as `ready-for-verification/2`.

## Independent re-verification (Worker-2) — pass 2, verdict `verified`

Re-pass on resubmission `ready-for-verification/2` (same W2
context). Gates: HEAD `0c0537e2` unmoved, target blobs
`991f7dad`/`5a4f4811` stable, item diff vs `ITEM_BASELINE`
still empty — pass-1 HEAD evidence stands without re-trace. Both
record fixes reproduce mechanically: (1) R7 + C3 cite `:195-196`
vs `:238-239`, extract-and-`diff` empty, `:197` confirmed twinless
(stem return vs camel `:240` parts line); (2) R4 disposal basis
stated (LOOKUP_SEP-path-structure population), `plans.py:700`
confirmed the head-segment split line, all 4 `startswith`
screens ruled out with the reserved-prefix reason, all 5 new
fingerprints re-hashed exact (`c6ad46aa`, `dda91365`, `058f1081`,
`fa6c4d33`, `cce98531`), and the `graphql-name-gate` open-family
hold confirmed in the plan. Nothing else moved (delta vs pass 1
is Status + the two fixed rows + `## Iterations`). All pass-1
judgments stand; record now reproduces. Verdict: `verified`.
