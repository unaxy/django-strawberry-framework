# DRY review: `utils/input_values.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/utils/input_values.py` is the neutral
set-input traversal substrate: the dict-vs-dataclass walk
(`iter_input_items` / `input_field_value`), the one active-input rule
(`is_inactive_value`), the family traversal config and record shapes
(`SetInputTraversal` / `ActiveField` / `LOGIC` / `RELATED` / `LEAF`), the
shared traversal-depth budget (`DEFAULT_SET_INPUT_TRAVERSAL_DEPTH` +
resolve / raise / assert trio), the shared related-declaration front half
(`related_declaration_mapping` + `RelatedDeclarationError`), the neutral
walker (`iter_active_fields`), and the typed traversal-error constructors
(`_field_name` / `_walk_error`).

Dirt attribution (all 11 hunks, by content — no ledger row names this
file; the [plan][plan] `## Owned changes` ledger was read whole and
covers other paths only): hunks `@@ -37` (import swap
`_safe_type_name` → `truth`), `@@ -59` (`_field_name` /
`_walk_error`), `@@ -87` (`iter_input_items`), `@@ -126`
(`input_field_value`), `@@ -208` (`set_traversal_depth_cap`), `@@ -227`
(`raise_set_traversal_depth_exceeded`), `@@ -271`
(`RelatedDeclarationError`), `@@ -291` + `@@ -299`
(`related_declaration_mapping`), `@@ -344` + `@@ -368`
(`iter_active_fields`) uniformly replace `isinstance` → `truth.is_instance`,
`getattr` → `truth.static_attr`, `_safe_type_name` → `truth.kind`,
`str.__str__` → `truth.text`, `__qualname__` → `truth.qualname`, and delete
every `try/except BaseException` containment plus the `"unreadable"`
signal arm. That is the concurrent truthful-reads migration (untracked
`utils/truth.py`, `scripts/check_truthful_reads.py`), pre-baseline: the
item baseline already carries the worktree bytes
(`456329c0:path` = `18992b79` = worktree; `git diff ITEM_BASELINE --
<target>` is empty), so the item-scoped diff holds zero hunks I did not
make and every HEAD-vs-worktree hunk is concurrent-external. Per dispatch
all bytes traced below are HEAD bytes (`f2566609`, 421 lines); the
worktree state (`18992b79`, 349 lines) is fingerprinted, never traced.
Nothing tracked was touched. HEAD is `0c0537e2`, unmoved since dispatch.

Production consumer census at HEAD bytes (every import statement read):

- `filters/sets.py` drives `iter_active_fields` (`_normalize_input`),
  composes `is_inactive_value` (10 call sites), `iter_input_items`
  (thin delegate), and `raise_set_traversal_depth_exceeded` (via
  `_raise_logic_depth_exceeded`); reads `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH`
  as its `_MAX_LOGIC_DEPTH` default.
- `orders/inputs.py` drives `iter_active_fields` (`normalize_input_value`
  + `_ensure_field_specs` warm-up gate) and filters on `RELATED`.
- `orders/sets.py` binds `UNSET` into its `SetInputTraversal` config.
- `sets_mixins.py` derives each family's canonical config
  (`_input_traversal` reads `_permission.traversal`) and composes
  `is_inactive_value` in the shared permission wrapper.
- `utils/permissions.py` re-exports `iter_input_items` (in `__all__`),
  drives `iter_active_fields`, composes `related_declaration_mapping`
  (translating both signal kinds), `assert_set_traversal_depth`,
  `input_field_value` + `is_inactive_value` (`extract_branch_value`).
- `utils/connections.py::is_supplied` composes `is_inactive_value`,
  binding `strawberry.UNSET`; `connection.py` consumes `is_supplied`.
- `filters/inputs.py` composes `is_inactive_value` (leaf + range patch).

Oracles: `tests/utils/test_input_values.py` (HEAD `2c6de200`, 620 lines,
29 tests; independent literals — `== [("a", 1)]`, `is True`, hostile
subclass pins). Live wire rows live in
`examples/fakeshop/test_query/test_library_api.py` (projection). The
worktree oracle (`69f7b2c0`, 18+/215-) is the concurrent truth rewrite,
NOT traced (see O2).

## Verification

### Matrix

1. **Cross-flavor mirroring** — searched. Both set families drive the one
   walker through per-family `SetInputTraversal` configs; leaf semantics
   stay at the three call sites exactly as the module docstring claims
   (filter operator-bag + range patch, order `Ordering` + recursion,
   permission dedup + double dispatch — each body re-read). No mirrored
   rule; the module exists to de-mirror the four original copies.
2. **Sync/async twins** — inapplicable with reason: the target is pure
   in-memory traversal (no `await`, no ORM, no executor read);
   `apply_sync` / `apply_async` on both families drive the same walker.
3. **Derived rather than repeated** — searched. The budget resolves once
   (`set_traversal_depth_cap`); kinds classify once; specs are looked up
   in the passed map, never re-derived from `_meta`; type labels compose
   `exceptions._safe_type_name` by name. The only twice-spelled dispatch
   is the dict-vs-dataclass premise inside `iter_input_items` vs
   `input_field_value` — split by contract (R5), not drift.
4. **Inverse / round-trip pairs** — searched, none. `iter_input_items`
   (partial walk) vs `input_field_value` (total point read) are siblings,
   not inverses (R5). Cap-resolve → raise → assert compose one direction.
   No kind-string parser inverts the `LOGIC` / `RELATED` / `LEAF` grammar.
5. **Contracts in another medium** — searched. Oracles (above) spell every
   verdict independently; the module docstrings, the `FilterSet` /
   `OrderSet` glossary null/omission prose, and the live wire rows are
   projections. A contract change moves 1 definition + its oracles; the
   latter are listed in each finding, never counted.
6. **Enforcement by omission** — searched, family enumerated. Depth cap:
   filter logical ×5, filter related ×2, shared permission walk via
   `assert_...`, order normalize transitively via permission-first apply
   ordering (order `apply_sync` docstring steps 2→3 + body; filter
   `run_permissions=True` default; connection sidecars via
   `apply_*_sync`) — no gap, no defect. Active rule: every traversal
   surface composes by name; the one unhomed spelling
   (`list_field.py:466-468`) is routed, not homed (O1). Related front
   half: both related-branch traversals compose it (walker + permission
   walker); no third spelling exists (census, `### Challenges` C9).

### Enumeration

Instrument: `ast.Module.body` over HEAD bytes (`git show
HEAD:django_strawberry_framework/utils/input_values.py`), 23 members: 1
docstring + 5 imports + 4 assigns + 10 functions + 3 classes. All 17
named definitions homed:

| # | Symbol | Home |
|---|---|---|
| 1 | `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH` | FL4 (budget value) |
| 2 | `LOGIC` / `RELATED` / `LEAF` | FL3 (kind grammar) |
| 3 | `_field_name` | FL7 + R1 + R2 + R3 (boundary) |
| 4 | `_walk_error` | FL7 |
| 5 | `iter_input_items` | FL1 + FA `:91` arm (converge) |
| 6 | `input_field_value` | FL1 + FA `:130` arm (adopt) |
| 7 | `is_inactive_value` | FL2 + CONFIRM `unset-bindings` row |
| 8 | `SetInputTraversal` | FL3 |
| 9 | `ActiveField` | FL3 |
| 10 | `set_traversal_depth_cap` | FL4 |
| 11 | `raise_set_traversal_depth_exceeded` | FL4 |
| 12 | `assert_set_traversal_depth` | FL4 + F-NEW (guard shape) |
| 13 | `RelatedDeclarationError` | FL5 |
| 14 | `related_declaration_mapping` | FL5 |
| 15 | `iter_active_fields` | FL6 + FA `:355` arm (converge) |
| 16 | Module mechanics (docstring, imports, no `__all__`) | FL8 |

### Challenges

- C1 (budget value): default 8→10 moves 1 definition (the constant;
  `FilterSet._MAX_LOGIC_DEPTH` references it; all 6 enforcement paths
  follow). FL4.
- C2 (boundary semantics): `>`→`>=` moves 6 spellings (`assert_...` +
  5 filter inline checks). → F-NEW `traversal-depth-cap-check`.
- C3 (resolution): non-int declared knob must raise instead of defaulting
  moves 1 (the helper gate; inline sites are incidentally loud
  `TypeError` — disclosed as F-NEW's migration decision point).
- C4 (refusal sentence): wording change moves 1 (the raiser; all 6
  enforcement paths compose it). FL4.
- C5 (active rule): a third inactive spelling moves 1
  (`is_inactive_value`; 20+ consumers follow) + 1 unhomed observation
  (`list_field.py:466-468`, O1). FL2.
- C6 (active identity): falsy-means-inactive moves 1 (oracle pins
  falsy-active). FL2.
- C7 (walk shape): accept non-dict `Mapping` inputs moves 2 dispatch arms
  (`iter_input_items`, `input_field_value`) — the dispatch is a premise,
  not a rule: sharing it would move the helper PLUS both branchers (3),
  so consolidation relieves no change obligation. R5.
- C8 (error detail): a new hostile operation moves 0 definitions (caller
  passes a detail word to the shared `_walk_error`). FL7.
- C9 (related rule): "declarations must be `dict`" moves 1 proof
  (`related_declaration_mapping`) + 2 adapting consumers (listed, not
  counted). Census: exactly 2 callers. FL5.
- C10 (new consumer family): a third set family moves 0 definitions
  (declares a config, drives the walker — principle 1). FL3/FL6.
- C11 (fourth kind): moves 1 classifier + per-consumer kind filters
  (listed). FL3/FL6.
- C12 (FA sixth container): moves `base_container_values` + FB gates;
  the `:91` / `:130` / `:355` arms do NOT move (fixed-shape reads, not
  member-set spellings) — evidence the arms share FA's threat model,
  not its member set. F-FA.
- C13 (FA snapshot): reads-must-snapshot moves the streaming `:355` arm
  only (FA's known open question, owned by the family item). F-FA.
- C14 (lookup key threat): `dict.get` must ALSO defeat lying key `__eq__`
  moves 1 (`:130`; iteration arms unaffected — the lookup/iteration axis
  inside F-FA, owned by the family item).

## Findings

### F-FA — Base-slot container reads (CONVERGE + ADOPT into open family `base-slot-container-reads`)

Fresh evidence confirms the two named arms are members: `:91`
`dict.items(input_value)` and `:355` `list.__iter__(input_value)` read
consumer containers through unbound slots so a subclass override cannot
decide what the walk sees — FA's contract verbatim — with oracles pinning
both (`test_dict_subclass_overrides_cannot_replace_the_shared_walk`,
`test_hostile_list_iteration_cannot_escape_the_order_walk`). The eager /
lazy axis FA flagged is real (`:355` streams; the owner candidate
snapshots) and stays the family item's question (C13).

Adopted on fresh evidence: `:130` `dict.get(input_value, field_name)` —
the only unbound point-lookup on a consumer container package-wide (the
`inputs.py:688-689` twins read framework-owned `safe_meta`, already
excluded by FA). Same threat model, same fix shape; iteration-vs-lookup
is a shape axis like eager-vs-lazy (C12, C14). The owner candidate serves
iteration only, so the family item owns whether the contract widens or
this arm splits back out.

Boundary evidence for the family item (held, not homed here): the
permission walker's conditional read (`permissions.py:672`,
`dict.items(related) if isinstance(related, dict) else related.items()`)
covers non-dict mappings with an instance fallback FA's contract does
not cover (holding: File `utils/permissions.py`); two further unbound
reads at `inputs.py:753` / `:1322` whose container provenance was not
traced here (holding: File `utils/inputs.py`); the instance-side reads
inside this file are distinguished at R4.

Freshness: target HEAD `f2566609`; `canonical.py` HEAD `b9ded33b`;
`inputs.py` HEAD `ee31d360`; `permissions.py` HEAD `9889d6fe`
(worktrees dirty, NOT traced).

### F-NEW — Traversal depth-cap guard (NEW family `traversal-depth-cap-check`, open)

Contract: a set-input walk fails closed when its depth counter passes
the set's budget. Sites: `assert_set_traversal_depth` (`:255-270`,
resolve + `>` + shared raiser) and five filter-inline spellings
(`filters/sets.py:2747`, `:2807`, `:3125`, `:3415`, `:3476` — each `if
_depth > cls._MAX_LOGIC_DEPTH: cls._raise_logic_depth_exceeded()`).
These are restatements, not enforcement sites: enforcement sites compose
the definition (the `pipeline_write_phase` precedent), while the five
inline the `>` comparison instead of calling `assert_...` (identical
errors: `_raise_logic_depth_exceeded` passes exactly the three words
`assert_...` takes). Challenges: C2 counts 6; C1/C4 count 1 (value +
sentence already single-owned, FL4). Owner candidate:
`assert_set_traversal_depth` (already owns the shape; five one-line
compositions). Migration decision point (disclosed, not resolved): the
helper is lenient on a non-int declared knob (falls back to the default)
while the inline sites are incidentally loud (`TypeError`) — the family
item decides whether strict-vs-lenient sourcing splits the rule (C3).

Freshness: target HEAD `f2566609`; `filters/sets.py` HEAD `993e887a`.

### FL1 — Dict-vs-dataclass walk + point read (file-local)

`iter_input_items` (partial walk: `None` for non-walkable) and
`input_field_value` (total point read: `None` when absent, never fails
on shape) are the single-sited traversal primitives; the
`__dataclass_fields__` census is this file only (plus docstring
mentions). The shared dispatch premise is split by contract at R5.

### FL2 — Active-input rule definition (file-local)

`is_inactive_value` (`None`-or-sentinel, identity-based) is the one
definition: 19 call sites across 6 files compose it by name, zero
hand-spelled twins (C5, C6). The cross-file verdict is CONFIRMED on the
existing verified `unset-bindings-across-families` row (no new row).

### FL3 — Traversal config and record shapes (file-local)

`SetInputTraversal` (5 axes: specs, related attr, logic keys, sentinel,
top-level-list), `ActiveField`, and the `LOGIC` / `RELATED` / `LEAF`
grammar. One declaration per family (`_permission.traversal`), read —
never re-spelled — by `_input_traversal` (C10, C11).

### FL4 — Depth budget value, resolution, refusal sentence (file-local)

`DEFAULT_SET_INPUT_TRAVERSAL_DEPTH` (8), `set_traversal_depth_cap`
(declared-or-default), `raise_set_traversal_depth_exceeded` (shared
sentence + defensive label read). All 6 enforcement paths compose the
value and the sentence (C1, C4). The guard SHAPE is F-NEW.

### FL5 — Related-declaration front half (file-local)

`related_declaration_mapping` (absent/`None` → `{}`, non-`Mapping` →
signal) + `RelatedDeclarationError` (internal, caller-translated). Census:
exactly 2 callers (this walker's `:370`, the permission walker's
`:657`), both translating per-caller prose (C9).

### FL6 — Neutral walker (file-local)

`iter_active_fields`: inactive skip → optional top-level-list flatten →
spec lookup → leaf/related/logic classification, one level, no child
recursion. Three consumers drive it (filter normalizer, order
normalizer, permission walkers); recursion and leaf shape stay
per-consumer by design.

### FL7 — Traversal-error construction (file-local)

`_field_name` (fail-closed key gate + base-slot `str` render) and
`_walk_error` (shared constructor, per-operation detail). The 11
`except BaseException` guards already compose the constructor; only the
detail words vary (C8, R6).

### FL8 — Module mechanics (file-local)

Charter docstring (accurate against all bodies read), 5 imports (no
family package — the cycle-free contract holds), no `__all__`
(full-path importers only; the one re-export lives in
`permissions.py::__all__`).

### R1 — `_field_name` vs `strings._plain_text` (rejected)

Same fail-closed shape (non-str → `ConfigurationError`, subclass →
`str.__str__`), but the error grammars are per-subject (traversal-type
label vs value-type label) — CONVERGE with verified `policies.py` R3
(per-subject rejection grammars). No cohesive shared owner (a raising
normalizer fits neither `strings.py` nor this leaf), and the exact-`str`
fast path is a hot-path-only optimization. Trigger: either side
generalizes its message, or a third fail-closed str normalizer appears.

### R2 — `_field_name` vs `imports._plain_text` (rejected)

Fail-closed gate vs tolerant pass-through (non-str returns as-is) —
CONVERGE with verified `imports` R1 direction. Trigger: either side
changes its non-str posture.

### R3 — Atom base-slot read vs FA container reads (rejected)

`:67` `str.__str__(value)` is per-value CONTENT RENDERING, not member
ENUMERATION — CONVERGE with verified canonical R4 (which drew exactly
this line for the write-transaction atom reads). Trigger: R4's trigger.

### R4 — Instance-side reads vs FA (rejected)

`python_attr in related`, `related[python_attr]`,
`config.field_specs.get`, `config.logic_keys` membership use instance
reads because no base slot exists (arbitrary `Mapping`, framework-owned
config) — the HEAD docstring's recorded "different contracts, not a
missed merge", confirmed against both bodies. Trigger: related
declarations constrained to `dict`.

### R5 — Walk-all vs read-one same-file split (rejected)

`iter_input_items` (partial: `None` for non-walkable) vs
`input_field_value` (total: `None` for absent-or-unwalkable) share only
the dispatch premise; C7 proves sharing it relieves no change obligation
(helper + 2 branchers = 3 moves vs 2). O(1) point read vs O(n) walk is
load-bearing. Same-file intentional separation (precedent:
`types-resolvers-attach-twin-split`). Trigger: `input_field_value`
needing walk errors.

### R6 — Standing guard triggers re-checked (rejected)

J1 (shared `except` driver): all 11 `BaseException` guards translate via
the already-shared `_walk_error` constructor with per-operation detail —
CONVERGE with `_request_body` J1 (no second driver). J2 (exact-type
gate): unfired — this file uses `isinstance` only. Trigger: a guard with
no per-site detail, or an exact-type gate appearing here.

CONFIRMED by reference (no rows): `unset-bindings-across-families`
(verified; definition here, consumers compose — C5/C6) and
`orders-normalize-vs-filter-normalize` (verified same-name-pair split;
this file defines neither side).

## Defects

None. Two routed observations and one held prose note, none meeting the
defect bar (no contract row broken):

- O1 — `list_field.py:466-468` hand-spells `is not None and is not
  strawberry.UNSET` ×3 (exactly `is_supplied`, uncomposed). Never homed
  (outside the verified `unset-bindings` census). Holding: File
  `list_field.py` re-trace (already queued REOPENED). Freshness:
  `list_field.py` HEAD `21380eb7`.
- O2 — the worktree oracle (`tests/utils/test_input_values.py`
  `69f7b2c0`, 18+/215- vs HEAD `2c6de200`) is the concurrent truth
  rewrite; all oracle citations above are HEAD bytes.
- O3 — this file's `:301-303` says the permission walker "materializes
  through the UNBOUND `dict.items`"; the body
  (`permissions.py:672`) does so only for `dict`, falling back to
  instance `.items()` for other mappings. Realistic declarations are
  dicts, so nothing breaks; holding File `utils/permissions.py` judges
  whether the sentence needs narrowing when it homes the conditional.

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no workspace runs. Sharded and Postgres cells are inapplicable by
construction: the target is pure in-memory traversal reaching no
database, alias, or dialect decision.

## Judgment

Zero-edit file item. All 17 named definitions homed: 8 file-local (one
dual-homed to the new family, three arms dual-homed to FA), 1
converge-plus-adopt into open `base-slot-container-reads`, 1 confirm of
the verified `unset-bindings` row, 1 new family
(`traversal-depth-cap-check`), 6 rejections (4 converging with verified
verdicts). No consolidation inside this file item; no production edits;
no defects.

## Index rows for Worker-0

F-FA converges and adopts into the already-open family (existing plan
row stands, holding item unchanged). FL2 confirms the verified
`unset-bindings-across-families` row (no new row). All other rows below
are new for the [plan][plan] `## Responsibility index`.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `traversal-depth-cap-check` | `django_strawberry_framework/utils/input_values.py::assert_set_traversal_depth` (owner candidate; 5 filter-inline restatements) | `django_strawberry_framework/utils/input_values.py`, `django_strawberry_framework/filters/sets.py` | Family `traversal-depth-cap-check` | open (F-NEW; C2 counts 6; migration decision: strict-vs-lenient knob sourcing, C3) |
| `input-values-dict-dataclass-walk` | `django_strawberry_framework/utils/input_values.py::iter_input_items` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL1; covers `input_field_value`; `:91`/`:130` arms in FA; R5 split) |
| `input-values-active-rule` | `django_strawberry_framework/utils/input_values.py::is_inactive_value` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL2; C5 + C6 count 1; confirms `unset-bindings` row) |
| `input-values-traversal-shapes` | `django_strawberry_framework/utils/input_values.py::SetInputTraversal` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL3; covers `ActiveField`, `LOGIC`/`RELATED`/`LEAF`; C10 + C11) |
| `input-values-depth-budget` | `django_strawberry_framework/utils/input_values.py::set_traversal_depth_cap` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL4; covers `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH`, `raise_set_traversal_depth_exceeded`; C1 + C4 count 1; guard shape in F-NEW) |
| `input-values-related-front-half` | `django_strawberry_framework/utils/input_values.py::related_declaration_mapping` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL5; covers `RelatedDeclarationError`; 2 callers; C9) |
| `input-values-neutral-walker` | `django_strawberry_framework/utils/input_values.py::iter_active_fields` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL6; `:355` arm in FA) |
| `input-values-traversal-errors` | `django_strawberry_framework/utils/input_values.py::_walk_error` | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL7; covers `_field_name`; 11 guards compose; C8) |
| `input-values-module-mechanics` | `django_strawberry_framework/utils/input_values.py` (docstring + imports, no `__all__`) | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | file-local (FL8) |
| `input-values-field-name-vs-strings-twin` | `django_strawberry_framework/utils/input_values.py::_field_name` (rejection recorded here) | `django_strawberry_framework/utils/input_values.py`, `django_strawberry_framework/utils/strings.py` | File `utils/input_values.py` | rejected (R1; CONVERGE with verified `policies` R3 per-subject grammars; trigger: generalized message or third normalizer) |
| `input-values-field-name-vs-imports-twin` | `django_strawberry_framework/utils/input_values.py::_field_name` (rejection recorded here) | `django_strawberry_framework/utils/input_values.py`, `django_strawberry_framework/utils/imports.py` | File `utils/input_values.py` | rejected (R2; CONVERGE with verified `imports` R1 pass-through-vs-fail-closed; trigger: either side changes non-str posture) |
| `input-values-atom-read-vs-container-reads` | `django_strawberry_framework/utils/input_values.py::_field_name` (rejection recorded here) | `django_strawberry_framework/utils/input_values.py`, `django_strawberry_framework/utils/canonical.py` | File `utils/input_values.py` | rejected (R3; CONVERGE with verified canonical R4 rendering-vs-enumeration; trigger: R4's trigger) |
| `input-values-instance-reads-vs-base-slot` | `django_strawberry_framework/utils/input_values.py::iter_active_fields` (rejection recorded here) | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | rejected (R4; no base slot for arbitrary Mapping / framework config; trigger: related declarations constrained to `dict`) |
| `input-values-walk-vs-point-read` | `django_strawberry_framework/utils/input_values.py::iter_input_items` (rejection recorded here) | `django_strawberry_framework/utils/input_values.py` | File `utils/input_values.py` | rejected (R5; same-file total-vs-partial + O(1) split, C7; trigger: point read needing walk errors) |
| `input-values-standing-guard-triggers` | `django_strawberry_framework/utils/input_values.py::_walk_error` (rejection recorded here) | `django_strawberry_framework/utils/input_values.py`, `django_strawberry_framework/_request_body.py` | File `utils/input_values.py` | rejected (R6; CONVERGE with J1, J2 unfired; trigger: detail-less guard or new exact-type gate) |

Convergences by reference (no rows): open `base-slot-container-reads`
(F-FA: `:91` + `:355` converge, `:130` adopts), verified
`unset-bindings-across-families` (FL2 confirms the definition site),
verified `orders-normalize-vs-filter-normalize` (consumer-only).

## Independent verification (Worker-2)

Own trace over HEAD bytes (`f2566609`, 421 lines; worktree `18992b79`
fingerprinted, never traced; `git diff ITEM_BASELINE -- <target>` empty;
HEAD `0c0537e2` unmoved at close). `ast.Module.body`: 23 members = 1
docstring + 5 imports + 4 assigns + 10 functions + 3 classes; 17 named
definitions. No `__all__`; imports touch no family package. Zero `await`
(axis 2 inapplicable); `isinstance` only, no exact-type gate (J2
unfired); 11 `except BaseException` guards (R6 population).

Definition counts per posited change (mine): budget value 1 (constant;
`FilterSet._MAX_LOGIC_DEPTH` references it — `filters/sets.py:1220`);
guard shape 6 (helper + 5 inline `if _depth > cls._MAX_LOGIC_DEPTH`
at `filters/sets.py:2747`, `:2807`, `:3125`, `:3415`, `:3476`, each
paired with `cls._raise_logic_depth_exceeded()`); refusal sentence 1
(the raiser, which the filter-side `_raise_logic_depth_exceeded`
composes with exactly branch/input_noun/subject); active rule 1
(`is_inactive_value`, 19 occurrences across 6 non-defining files; my
independent `UNSET`-comparison sweep finds zero hand-spelled twins
besides `list_field.py:466-468`); related front half 1 (exactly 2
callers: this walker's `:370`, the permission walker's `:657`).
Owner choices agree throughout: depth-guard shape to
`assert_set_traversal_depth` (already owns it); FA arms to the open
family item; everything else file-local.

Reconciliation — every W1 claim re-derived, two record slips corrected
(neither moves a verdict, a material count, or an index row):

- Enumeration 23/17: agree exactly (member-by-member AST recount).
- 11 hunks concurrent-external: agree by content. Every `+/-` line is
  in the truth-migration vocabulary (`truth.is_instance` /
  `truth.static_attr` / `truth.kind` / `truth.text` / `truth.qualname`,
  `BaseException`-containment deletion, `"unreadable"`-arm removal) or
  its mechanical consequence (try/except collapse, docstring reword).
  No ledger row names this file (`## Owned changes` ends at plan
  `:1219`; zero hits).
- F-FA: agree. `:91` `dict.items`, `:130` `dict.get`, `:355`
  `list.__iter__` verified at the cited HEAD lines; both pinning tests
  exist in oracle HEAD `2c6de200`; `:130` is the only `dict.get(` on a
  consumer container package-wide (`inputs.py:688-689` read
  framework-owned `safe_meta`). Correction: the held pointer "two
  further unbound reads at `inputs.py:753` / `:1322`" is incomplete —
  `:523` (`dict.items(v)` over consumer Meta cache-key values) and
  `:632` (`dict.items(fields)` over consumer `Meta.fields`) are further
  consumer-container unbound reads File `utils/inputs.py` must home in
  its own trace. (`:710` reads framework `safe_meta`, covered by the
  stated exclusion.)
- Unset-bindings confirm: agree. Row present in the verified
  `utils/connections.py` artifact; `is_supplied` binds `UNSET` and
  composes by name.
- F-NEW `traversal-depth-cap-check`: ENDORSED as open. The five inline
  sites are verbatim restatements of the helper's guard shape (value +
  sentence already composed; only the `>` is inlined), so C2 counts 6
  and the strict-vs-lenient knob sourcing is correctly disclosed as the
  family item's migration decision. Correction: matrix axis 6 "filter
  logical x5, filter related x2" overcounts — the 5 inline sites split
  logic x3 (`:2747`, `:2807`, `:3125`) + related x2 (`:3415`, `:3476`);
  5 inline + `assert_...` = the 6 paths C1/C2/C4 already count. No gap
  either way; order-side transitivity via permission-first apply steps
  confirmed at `orders/sets.py:786`.
- R1/R2/R3: agree, converges grounded — both `_plain_text` bodies
  re-read (fail-closed vs pass-through; per-subject grammars), `:67`
  `str.__str__` verified, and the cited verified verdicts (policies
  R3, imports R1, canonical R4) read in their artifacts.
- R4: agree — the "different contracts, not a missed merge" sentence is
  in the HEAD docstring verbatim and both bodies confirm it.
- R5: agree — partial-vs-total + O(1)-vs-O(n) is a real contract
  split; C7's arithmetic is sound.
- R6: agree — 11 guards counted, all translating via the shared
  constructor; J1 converge grounded in the verified `_request_body`
  artifact.
- O1: agree, correctly routed — the x3 spelling verified verbatim at
  `list_field.py:466-468`, holding item already REOPENED. O3: agree,
  correctly held — the conditional read verified verbatim at
  `permissions.py:672`; File `utils/permissions.py` is open.
- Freshness: all cited HEAD blobs re-pinned intact (`canonical.py`
  `b9ded33b`, `inputs.py` `ee31d360`, `permissions.py` `9889d6fe`,
  `filters/sets.py` `993e887a`, `list_field.py` `21380eb7`, oracle
  `2c6de200`, worktree oracle `69f7b2c0`).
- Zero-defect call: agree — my trace broke no contract row. The two
  corrections above are per-cycle prose slips, not product defects; no
  `## Defects` entry owed. Sharded/PG inapplicability by construction
  accepted (pure in-memory traversal).

No production edits; artifact-only change (this section + `Status:`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[plan]: dry-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
