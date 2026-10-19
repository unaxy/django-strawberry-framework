# DRY review: `orm-lookup-path-resolution`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

Rule: resolving a multi-segment ORM lookup path (`author__books__title`)
into a classification or plan — the strict classifier with its lenient
fallback ladder. Provisional owner [relations.py][relations]
`::classify_path`; confirmed below (ownership reasoning under Findings F1).

Prior records entered only as triggers: field_meta R3 (single pk-name read
vs multi-segment classification; trigger: elision needs a multi-segment
path) and list_field J5 (four walkers with distinct contracts; trigger: a
caller needing another walker's answer). Both framings re-derived fresh
below; neither inherited.

What the target owns: [relations.py][relations] holds the strict,
immutable path classification (`ClassifiedPath`: ordered `hops` with
`relation_kind` + `PathInfo.m2m` cardinality, a terminal that is never
`None`, `first_many_index`, `relation_chain`), the lenient to-many walk
kept verbatim as a fail-open fallback, the one-body ladder composing them
(`_traverses_to_many`), the cached hot path (`path_traverses_to_many`),
and the lookup-expression tail validator (`validate_lookup_expr`,
a deliberately separate contract — see F3).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The `_meta`-walk mechanism
(split a `__` path, `get_field` per segment, follow the relation) was
swept package-wide, not neighbour-only. Six bodies share it (Enumeration);
two lookalikes excluded with reasons (`utils/permissions.py` matches
segments against DECLARED `RelatedFilter`/`RelatedOrder` attributes and
never touches `_meta.get_field`; [filters-base.py][filters-base]
`::_target_definition_for` walks the REGISTRY graph via
`related_target_for`, never `get_field`). Filter/order generation are
CONSUMERS of the owner by name ([filter-sets.py][filter-sets]
`::candidate_filter_metadata` direct-raise vs expanded-fail-closed;
`::filter_for_lookup` `distinct` stamp via `path_traverses_to_many`;
[order-sets.py][order-sets] declaration + apply validation raising
`ConfigurationError`, aggregate-vs-direct via `path_traverses_to_many`).
2. **Sync/async twins.** The rule is pure sync metadata reads; no colored
pair exists. `path_traverses_to_many` serves both pipelines from one
cached body. Inapplicable beyond that sentence.
3. **Derived rather than repeated knowledge.** `pk`-alias handling is
re-derived per contract (`_meta.pk` vs `_meta.pk.name` vs unresolved),
not shared; the separator is spelled `LOOKUP_SEP` in three bodies and
literal `"__"` in two ([connection.py][connection],
[plans.py][plans]) for the identical constant — spelling, not a rule
(considered unification declined under F1: zero change obligation).
`flatten_lookup_path` ([strings.py][strings]) is spelling production
(`__` -> `_`), never resolution: examined, not a member.
4. **Inverse / round-trip pairs.** None: classification has no inverse.
`validate_lookup_expr` is the AFTER-terminal contract (transforms + final
lookup from the terminal's own `get_transform`/`get_lookup`), not the
path contract's mirror. Stays separate (F3).
5. **Contracts restated in another medium.** Oracles spell expectations
independently and would fail, not follow, a classifier change:
[test-relations.py][test-relations] strict pins (hop/kind/terminal/error
arms), the 32-path legacy-parity matrix for the ladder (incl.
`genres__nonexistent` -> `True` many-then-garbage fallback and the one
deliberate divergence, unique reverse FK -> `False`), keyset order-path
arms ([test-keyset-connection.py][test-keyset-connection]
`::test_resolve_order_path_field_arms`), prefetch-target arms
(`tests/utils/test_querysets.py`, Category-shaped only — the gap behind
Defect D1), deterministic-order classifier pins
([test-list-field.py][test-list-field] + live sync/async suites).
Projections (per-walker docstrings) state each contract; no projection
owns.
6. **Enforcement by omission.** No member lacks a guard its contract
requires. The strict classifier raises where the prefetch sealer must
fail open and vice versa — that asymmetry IS the two contracts (F1),
not a missing guard. No defect of this axis found.

### Enumeration

Instrument: `split(LOOKUP_SEP)` + `split("__")` census over
`django_strawberry_framework/**/*.py` (14 hits), every hit read at its
body; every `get_field`-per-segment walk adjudicated.

| Body | Separator | `pk` | Failure | Terminal | Verdict |
|---|---|---|---|---|---|
| [relations.py][relations] `::classify_path` | `LOOKUP_SEP` | `-> _meta.pk` | raises `PathResolutionError` | field or relation descriptor (+ hops) | owner |
| [relations.py][relations] `::_lenient_traverses_to_many` | `LOOKUP_SEP` | unresolved | `False` | bool (many reached?) | owned internals: one ladder body |
| [connection.py][connection] `::_resolve_order_path_field` | literal `"__"` | `-> pk.name` | `None` (-> keyset contract error) | concrete non-relation column | rejection F1 |
| [plans.py][plans] `::_select_path_traversable` | literal `"__"` | unresolved | `False` (-> path dropped) | bool under a consumer projection | rejection F1 |
| [querysets.py][querysets] `::_prefetch_relation_target_or_none` (+ accessor helper) | `LOOKUP_SEP` | unresolved | `None` (fail-open pass-through) | terminal MODEL | rejection F1 |
| [list-field.py][list-field] `::_resolve_order_field_path` | `LOOKUP_SEP` | `-> opts.pk.name` | `None` (-> certification refused) | `(field, related opts)` | rejection F1 |

`list_field.py` carries five `split` hits but ONE walker: the other four
are call-site uses inside the same classifier cluster (terminal-piece
check, annotation heads, predicate longest-prefix loop), owned by the
`list_field.py` file item (R7), not new members. The walker's own
`_walk_selections` descends GraphQL selection trees via field maps, not
`__` paths: examined, different mechanism, not a member.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Behaviors below are
`execution-verified` by the workspace probe unless marked
`static-reviewed` (import/shape/absences).

- **C1 — new lookup form in path position** (a transform segment, e.g.
`title__length`): 0 shared definitions move. Each body answers per its
own contract — strict raises, ladder `False`, connection `None`,
plans `False`, prefetch `None`, list_field `None` (probe P4, all six
`execution-verified`). Supporting transforms in path position would be
one independent edit per contract that wants it, never one shared edit.
- **C2 — new failure mode for unresolvable mid-path** (raise? `None`?
skip?): 0 shared, 5 independent by construction. Probe P3 matrix on
`shelf__nonexistent` / `title__nonsense` / `genres__nonexistent`:
raise / (`False`,`False`,`True`) / `None` / `False` / fail-open-`None`
/ `None` — `execution-verified`. Three walkers spell `None` with three
meanings (keyset contract error vs prune-drop vs refuse-certification
vs pass-through); textual agreement is not a shared rule.
- **C3 — path with 5+ segments** (recursion vs loop): all six bodies
loop over the split (`for` over segments; no self-call —
`static-reviewed` at each body); no depth cap exists. Probe P2:
8-segment self-chain classifies to 7 hops + scalar terminal, 4-segment
FK chain to 3 hops, both to-many probes `False` —
`execution-verified`. A depth change touches nothing.
- **C4 — lifetime (principle 4).** Resolved paths are cached in exactly
one place: the `path_traverses_to_many` two-layer `lru_cache(2048)`.
Owner [relations.py][relations]; validity key `(model, field_path)`
definition-time-stable metadata; published at import; mutated by no
package caller (only tests clear); invalidated via the
`cache_clear`/`cache_info` handles. `classify_path` itself stays
`not cached` by stated contract (unhashable test doubles). No satellite
caches. Anti-duplication mandates no new shared state: none added.
- **C5 — owner (principle 7).** State the contract + consumers: the
strict hop-plan + lenient ladder serves filter generation, order
validation/generation, and the `distinct`/aggregate stamps — all
already composing `classify_path` / `path_traverses_to_many` by name.
The narrowest cohesive owner every consumer can depend on without
reversing a dependency is [relations.py][relations] (a leaf utils
module; satellites in `connection.py`, `plans.py`, `querysets.py`,
`list_field.py` can all import it, and the set-members already do).
F1 records the decision.

Experiments: workspace probe
`orm-lookup-path-resolution-probe.py` (`execution-verified`, 30 checks:
28 pass, 2 fail documenting Defect D1); shared-tree anchor
`tests/utils/test_relations.py::test_path_traverses_to_many_matches_legacy`
(31 passed, `execution-verified`, `--no-cov -n0`).

## Findings

### F1 — five walkers, four contracts: REJECTED (no consolidation)

One mechanism (split a `__` path, `get_field` per segment, follow the
relation), four contracts (the lenient walk is already composed INTO the
owner by name via `_traverses_to_many` — that consolidation stands and
is not re-litigated):

- `::classify_path` answers the immutable hop plan and RAISES, because
a filter/order path that does not resolve is a schema-author error the
package must name (consumers: direct-leaf propagate, expanded-leaf
fail-closed, order validation `ConfigurationError`).
- `::_resolve_order_path_field` answers the terminal concrete column or
`None`, because a value cursor can only anchor a non-nullable column;
`None` becomes the keyset contract error at its one caller.
- `::_select_path_traversable` answers traversability under a consumer
projection (`(names, defer_mode)` extra inputs no sibling takes),
because a dropped path surrenders resolver keys it can never satisfy.
- `::_prefetch_relation_target_or_none` answers the terminal MODEL or
`None` FAIL-OPEN, because it must additionally accept the default
`<model>_set` accessor spelling Django's own prefetch traversal reaches
by attribute access, and must never fail-close a path Django supports.
- `::_resolve_order_field_path` answers `(field, related opts)` or
`None`, because ordering-term certification refuses whatever it cannot
read (transforms/lookups included).

A change to one terminal rule (the keyset nullability guard, the
accessor fallback, the projection inputs, the expansion rule) moves
exactly one body (C1/C2 counts: 0 shared). One shared walker would need
terminal-rule + failure-mode + input flags — a principle-5 mode-flag
violation — to reproduce behaviors the loop text does not share.
Difference is load-bearing in both directions: merging makes the
prefetch guard reject legal Django paths or the classifier silently
accept unresolvable ones.

Migration: none (no body moves). Reconsideration triggers: **T1** a
caller needing another walker's answer; **T2** `classify_path` gaining
an accessor-name fallback or a non-raising mode (adopts the querysets
I-R1 trigger); **T3** a separator-spelling unification (`"__"` ->
`LOOKUP_SEP`) re-opens the C-count on that axis only. Durable home:
the new clause on [relations.py][relations] `::classify_path` (this
change, projection only) + this artifact. The sibling clause owed at
[querysets.py][querysets] `::_prefetch_relation_target_or_none`
(querysets I-R1 home) is recorded here as pending text — that file is
fenced read-only for this cycle, so the edit belongs to its owning
item, not this diff: *"Fail-open sibling of
`utils/relations.py::classify_path`: unresolvable paths return `None`
(including the default `<model>_set` accessor spelling) so the seal
never fail-closes a prefetch Django supports."*

### F2 — field_meta R3 trigger: UNFIRED

Elision walks no multi-segment path. The eligibility conjunction
(`FieldMeta.fk_id_elision_eligible`) is stamped per single relation
hop; `_target_pk_name` reads one model's `_meta.pk.name`;
`walker.py::_plan_select_relation` consumes one hop's stamp; the
id-only check (`_selected_scalar_names`) scans one level of child
scalar selections and returns `None` on any relation child
(`static-reviewed` at each body). R3's framing (single pk-name read vs
multi-segment classification) verified, trigger not fired, no compose
owed. Home: this artifact; the field_meta R3 record stands.

### F3 — `validate_lookup_expr` separation: CONFIRMED (no shared body)

The lookup-expression tail (transforms + final lookup from the
terminal's own `get_transform`/`get_lookup`, incl. the
trailing-transform-implies-`exact` rule) is a contract SEPARATE from
path classification — stated in its own docstring, verified against its
body. It has zero in-package callers (definition + tests only) and is
kept as the public tail contract in-flight specs (spec-058, spec-060)
already name; that is API surface, not dead code (principle 11:
removal would strand named consumers). A new registered transform
needs zero definition edits (structural validation, no allow-list).
No consolidation, no edit. Home: its own docstring (already present).

## Defects

### D1 — `_reverse_relation_by_accessor_or_none` raises `AttributeError` on forward M2M (UNFIXED, fenced file)

Owner: [querysets.py][querysets]
`::_reverse_relation_by_accessor_or_none` (via
`::_prefetch_relation_target_or_none`).

The accessor scan screens candidates with
`getattr(candidate, "concrete", True)` to keep only reverse relations
before calling `candidate.get_accessor_name()`. On Django 6.0/6.1 a
forward `ManyToManyField` reports `concrete=False` (the version split
[field-meta.py][field-meta] `::from_django_field` already documents for
`attname`/`concrete`), passes the screen, and has no
`get_accessor_name` — the call raises `AttributeError`, uncaught (the
caller's `except` wraps only `get_field`). This breaks the function's
own contract ("a miss returns `None` ... must never fail-close").

Wire: `_prefetch_relation_target_or_none(Book, "shelf__nonexistent")`
and `(Book, "shelf__pk")` raise instead of returning `None`
(`execution-verified`, probe P3/P5 FAIL rows); the crash needs a miss
at a model carrying a forward M2M (`Shelf.alt_branches`,
`Book.genres` — both `concrete=False`, no accessor,
`execution-verified` field census). Reachable through the seal:
`_sealed_prefetch_related_lookups` calls the walker unwrapped, so a
consumer `Prefetch` with an unresolvable tail through such a model
raises `AttributeError` out of the seal instead of the typed
`(None, (code, detail))` discipline. Floor Django 5.2 reports forward
M2M `concrete=True` (screen holds — latent there); ceiling 6.0/6.1
crashes. Both trees in this cycle run 6.1.

Oracle gap: existing prefetch-target tests (`tests/utils/test_querysets.py`)
probe `Category` (no M2M field) and accessor models without a forward
M2M on the miss path — the crashing shape has zero coverage. Not fixed
here: the file is fenced read-only this cycle and DRY routes
non-duplication bugs unfixed. Homing owed by Worker 0 (suggested: the
`utils/querysets.py` owning item; repair and regression test land
together there, same change).

## Pending execution

None. Every proof this item relies on already ran: workspace probe
(`execution-verified`, 28/30 with 2 fails pinning D1) and the
shared-tree anchor (31 passed). No `execution-deferred` item exists.
Gate business (full `uv run pytest`) is Worker 0's final gate, not this
item — deferred with that reason, per AGENTS.md (no pytest after edits
beyond the one authorized focused test).

## Judgment

Four contracts, not one rule with four spellings: consolidation
REJECTED with per-walker differences (F1), both prior triggers checked
(F2 unfired; J5's T1 adopted as F1-T1), homes recorded (owner clause
this change; querysets-clause text pending at its fenced owner). One
defect routed unfixed (D1). Zero behavior change: one projection-only
docstring clause + this artifact.

## Implementation (Worker 1)

Tracked change (the ONLY production-tree edit):

- `django_strawberry_framework/utils/relations.py` —
`::classify_path` docstring: strict-vs-fail-open sibling clause
(projection; body untouched; AST-identical behavior).

Item-scoped diff state: `git diff c5b999cb -- <touched>` shows the
relations.py hunk only (new, mine); `docs/dry/` artifact is new
(`git diff --no-index /dev/null` shape for review). Querysets,
plans untouched — `querysets.py` fingerprint unchanged from HEAD
(read-only confirm below). `connection.py` NOT touched: its worktree
blob `3c4d5dcb` equals ITEM_BASELINE and differs from HEAD
`93e998f2` by the pre-existing cursor-guard hunk (external concurrent
content, verified via `git show HEAD:` — attribution stop not
triggered: no edit there).

Freshness fingerprints (worktree blobs): relations.py
`7662b0bb` == HEAD == baseline (pre-edit); plans.py `cce98531` ==
HEAD == baseline; querysets.py `96618fba` == HEAD == baseline
(read-only, never edited); connection.py worktree `3c4d5dcb` ==
baseline, HEAD `93e998f2` (divergence = cursor-guard, concurrent).
Tests read: test_relations.py `37db9b64`, test_list_field.py
`2f77f77d`, test_keyset_connection.py `7490409a`,
tests/utils/test_querysets.py `8b39c9f8`; sources read:
list_field.py `d6af6164`, field_meta.py `7215c887`, walker.py
`9b111ed9`, filters/sets.py `4a40e51b`, orders/sets.py `6044ab1a`,
filters/base.py `ba52351c`, permissions.py `9889d6fe`.
Searched population: all `split(LOOKUP_SEP)` / `split("__")` hits
package-wide (14, enumerated); excluded on body evidence:
permissions-hops, registry-graph walk, selection-tree descent,
order-entry parsers, spelling manglers. Any fingerprint change reopens.

Proofs: disposable workspace
`.../dry-ws/orm-lookup-path-resolution` (`__file__` printed from the
copy; DB `NAME` = the copy's `examples/fakeshop/db.sqlite3`; read-only
probe, no source mutation, no DB writes); shared-tree focused test
`tests/utils/test_relations.py::test_path_traverses_to_many_matches_legacy`
(`-n0 --no-cov`, 31 passed). Scratch paths: workspace dir +
`.../dry-ws/orm-lookup-path-resolution-probe.py` (outside both trees;
Worker 0 removes by explicit path after verification).

## Independent verification (Worker 2)

Recorded BEFORE reading `## Findings` / `## Implementation (Worker 1)` /
`## Defects` bodies (only section headers, lines 1-60, and the tail link
block opened for anchoring). HEAD `bfaee91d`; ITEM_BASELINE
`c5b999cb6ce7c791ffc5008c101bc95aa57e596f`; current `27661be8debeadac05fc2c5890930c192de69021`.
Provisional owner `utils/relations.py::classify_path` read with the other
walkers; `utils/querysets.py` touched by read only (worktree blob
`96618fba`, never edited).

### Walker census (my own sweep)

Instrument: every `.split(` call in `django_strawberry_framework/` (26 hits),
then every `get_field` / `get_accessor_name` / `LOOKUP_SEP` site for walks
that do not split. Each candidate below carries subject, failure mode,
return — the contract triple the five-walker rejection stands or falls on.

IN (five `_meta` path walkers, one owner + four rejected):

- W0 owner `utils/relations.py::classify_path`. Subject: `(model,
  field_path)`. Failure: raises `PathResolutionError` naming model, path,
  segment (missing / non-traversable incl. forward `GenericForeignKey` /
  empty-`path_infos` / non-relation-mid-path / non-str input). Return: frozen
  `ClassifiedPath` (ordered `hops` with `relation_kind` + `PathInfo.m2m`
  cardinality, terminal NEVER `None`, `first_many_index`,
  `relation_chain`). Owned ladder internals, single-bodied: the legacy
  lenient walk `::_lenient_traverses_to_many` (fail-open bool shim, early
  `True` on many-side, `False` on any failure) runs ONLY as the
  `PathResolutionError` arm inside the one ladder body
  `::_traverses_to_many`, served through `::_classify_path_cached` /
  `::_path_traverses_to_many_cached` to the public
  `::path_traverses_to_many`. One definition for the strict plan, one
  documented compatibility arm, one composition body — not three owners.
- W1 `connection.py::_resolve_order_path_field`. Subject: `(model, path)`.
  Failure: `None`. Return: terminal concrete non-relation column or `None`.
  Extra contract mid-path: intermediate must be non-nullable
  `forward_single` (nullable / reverse / multi-valued yields `None` even
  when resolvable) — cursor anchoring cannot tolerate NULLs or fan-out.
- W2 `optimizer/plans.py::_select_path_traversable`. Subject: `(path,
  names, defer_mode, model)`. Failure: `False`. Return: bool. Contract is
  traversability UNDER A CONSUMER PROJECTION (Django deferred-loading rule
  mirrored per level, `defer()` vs `.only()` arms, attname aliases,
  dotted-entry scoping) for prune decisions. Unresolvable segment answers
  `False` (drop path, pay a fallback query, never `FieldError`).
- W3 `utils/querysets.py::_prefetch_relation_target_or_none`. Subject:
  `(parent_model, path)`. Failure: `None` (fail-open). Return: terminal
  MODEL or `None`. Extra contract: on a field-map miss it scans the
  reverse-ACCESSOR map (`_reverse_relation_by_accessor_or_none`), so the
  default `<model>_set` spelling resolves; non-relation / unknown /
  generic-FK / lazy-string segments answer `None` and Django keeps
  fetch-time ownership.
- W4 `list_field.py::_resolve_order_field_path`. Subject: `(opts, path)`.
  Failure: `None`. Return: `(field, related opts)` or `None`. Contract is
  ordering-term CERTIFICATION refusal: a piece that is not a field of the
  model in hand is a transform/lookup this package does not read, and an
  unresolved path is never certified. Relation-terminal paths RESOLVE here
  (unlike W1 which refuses relation terminals) because the caller expands
  them into the related model's `Meta.ordering`.

OUT (excluded on body, each opened):

- `utils/permissions.py` hops split (source_path + declared field_name
  splits): walks permission DECLARATIONS (`RelatedFilter`/`RelatedOrder`
  `field_name` prefix match, longest-declaration-wins, fires branch gates).
  Subject is the declaration graph, never `_meta.get_field`. Different
  rule, not a sixth walker.
- `filters/base.py::resolve_globalid_target_definition`: walks the TYPE
  REGISTRY graph via `related_target_for` (own-PK branch, `None` on miss).
  Never `get_field` per hop. Different mechanism, not a sixth walker.
- `optimizer/walker.py::_walk_selections` descent (+ `nested_planner.py`
  index-term `meta.get_field` singletons, `plans.py` single-shot
  `meta.get_field(ref)` uniqueness probe, `types/definition.py`
  `related_target_for` single-hop): GraphQL-selection descent or
  one-field reads, no `__`-split multi-segment `_meta` walk. Consumers of
  the family, not members.
- `list_field.py` order parsers (`_is_deterministic_order_*` chain,
  annotation-head splits, `pieces` loop): CALLERS of W4 plus
  annotation/`extra` name parsing. One certification reader, not a second
  definition — the `pieces` loop re-invokes W4 per prefix.
- `filters/inputs.py` `top_name.split("__", 1)[0]` hide-flat check:
  first-segment grouping predicate, no resolution at all.
- `utils/strings.py::flatten_lookup_path`: mangler (`__` -> `_`), produces
  identifiers, resolves nothing. Spelling production, inverse direction.
- `optimizer/plans.py::_flatten_select_related` (+ `_lookup_path`):
  builds paths from a dict / reads an attribute; construction, not
  resolution.
- `strings.py`/`relay.py`/`_imports.py`/`errors.py`/`testing/client.py`/
  `middleware`/`filters/sets.py` splits: non-ORM vocabularies (words,
  type names, selectors, versions). No `_meta` walk.

No fifth walker missed: the sweep's only other `_meta`-walking bodies are
the singletons and registry walks above, each excluded for a body-level
reason. Definition count: 5 walker definitions (1 owned + 4 rejected),
each moved by zero of my posited changes below except its own.

### My change challenges (re-derived, not inherited)

- X1 new segment kind (e.g. a traversable generic shape): moves W0 (+ its
  single ladder body) only. W1/W2/W3/W4 each keep their terminal contract
  (cursor column / projection prune / prefetch target / certification);
  none follows W0. Count 1.
- X2 mid-path failure semantics (raise vs `None` vs `False`): five
  genuinely different outcomes — W0 raises typed error, W1 `None`
  (unanchorable cursor), W2 `False` (prune to fallback query), W3 `None`
  (Django keeps traversal), W4 `None` (refuse certification). Changing any
  one breaks its caller's contract and moves no other. 0 shared /
  5 independent.
- X3 paths of 5+ segments: all five loop per segment; no unrolled body
  anywhere. Touches nothing.
- X4 lifetime: exactly one stored derivation — the bounded `lru_cache`
  pair at the owner for definition-time-stable `(model, field_path)` pairs
  (with the paired `cache_clear` that empties both layers). W1–W4 cache
  nothing (request-scoped inputs). No shared state to consolidate.
- X5 owner: `classify_path` by responsibility (DRY.md principle 7). It is
  the strictest contract (raises, richest return: hops + terminal +
  cardinality + chain), lives in the leaf `utils/relations.py` every
  legitimate consumer can import without reversing a dependency
  (connection/plans/list_field/querysets are all heavier or sibling
  flavors), and already owns the adjacent relation taxonomy
  (`relation_kind`, `instance_accessor`) its hops record. Dependency
  direction + existing responsibility beat narrowness of any single
  consumer module. The four others stay as named adapters at their call
  sites; sharing only the split-and-`get_field` mechanism would couple
  independent failure policies.

### `validate_lookup_expr` fate (dead-or-API)

Zero production callers in the package (def in `utils/relations.py`,
contract prose in `exceptions.py`, readers only in
`tests/utils/test_relations.py` plus forward SPEC prose). It is NOT a
sixth `_meta` path walker: subject is `(terminal, lookup_expr)` where the
terminal is already classified, mechanism is `get_transform`/`get_lookup`
cursor walking (never `_meta.get_field`), failure is
`LookupValidationError`, return is the final lookup CLASS. Exported in
`__all__` — a staged public-API helper whose consumers land with the
search-fields surface, not dead code to delete. Correctly excluded from
the family; no deletion owed here.

### D1 adjudication (my own reproduction)

- Installed Django: `6.1` (`uv run python -c "import django;
  print(django.__version__)"`, read-only).
- Defect body: `utils/querysets.py::_reverse_relation_by_accessor_or_none`
  skips only `concrete`-truthy candidates, then calls the unguarded
  `candidate.get_accessor_name()`. On Django 6.0/6.1 a forward
  `ManyToManyField` reports `concrete=False` (verified live: Book `genres`
  field `concrete=False`, `is_relation=True`, `hasattr(get_accessor_name)
  == False`), so it is NOT skipped and the call raises `AttributeError`.
  On 5.2 the same field reports `concrete=True` and is skipped — latent
  there, live here.
- Execution proof (read-only, shared tree, fakeshop settings): scratch
  script `check_m2m.py` (explicit path under `/var/.../T/opencode/`,
  outside both trees for the verdict record; DATABASE untouched, no
  source mutated) printed `concrete= False`, `AttributeError
  'ManyToManyField' object has no attribute 'get_accessor_name'`, and —
  load-bearing — `_reverse_relation_by_accessor_or_none(Book, "nope__x")`
  RAISED `AttributeError` instead of returning `None`, and
  `_prefetch_relation_target_or_none(Book, "nope__x")` propagated it (the
  `_reverse...` call sits inside the `except` arm of the `get_field`
  miss, outside any guard).
- Contract source: BOTH docstrings state fail-open-`None` —
  `_prefetch_relation_target_or_none` ("returns `None`, and the caller
  keeps the status-quo behavior ... never fail-close a prefetch path
  Django supports") and `_reverse_relation_by_accessor_or_none` ("A miss
  returns `None` and the caller keeps the fail-open contract"). Docstring
  + body disagree = defect, not a robustness row.
- Wire reachability: the seal path `_seal_or_defect` ->
  `_sealed_prefetch_related_lookups` -> `_prefetch_relation_target_or_none`
  runs on EVERY sealed queryset evaluation carrying a queryset-bearing
  `Prefetch` (no `try` around the call; the `AttributeError` escapes the
  seal rather than becoming an `untrusted` defect). Feasible project
  shape under supported public API: any consumer type over a model with a
  forward M2M (e.g. library `Book.genres`, glossary/kanban M2M models)
  whose `get_queryset` (or any queryset the framework seals) carries
  `Prefetch` with an unresolvable `prefetch_through` — a typo segment, a
  plain-column segment, a generic-FK alias — a shape Django itself
  supports at fetch time and the seal contract explicitly leaves to
  Django. Wire input: any live GraphQL operation resolving that type,
  e.g. the library `books` list/connection query selecting scalar leaves,
  with fixture rows from the library seed (`Book` + `Genre` rows exist in
  the example project). The scan iterates ALL fields of the parent model,
  so the forward M2M poisons even unrelated bogus segments.
- Severity: request failure (unhandled `AttributeError` escapes the seal
  => 500-class GraphQL error for the field/operation), NOT wrong data
  (no rows leak; nothing is mis-targeted) and NOT masked (no defect tuple
  is produced). Availability break on a fail-open path: the exact
  inversion of the stated contract.
- Card class: behavior defect owned by `utils/querysets.py` (the
  `_reverse...` guard), homed at closeout on a NAMED querysets card. The
  oracle gap (existing fail-open tests pin `Category`/`Item`, both
  M2M-free per `apps/products/models.py` — FKs only) rides the SAME fix
  card as its regression arm (`Book` + bogus/column/generic segments =>
  `None`, plus a seal-level `Prefetch("bogus", queryset=...)` over `Book`
  => seal holds, Django keeps traversal). No second card: the oracle
  exists, its population is just M2M-blind.
- Correctly UNFIXED here: both halves hold. (a) Owner file fenced: this
  item's edit scope is `utils/relations.py` (+ ledger rows it lands);
  `utils/querysets.py` is explicitly READ-ONLY for this item (another
  item disputes its artifact; worktree blob `96618fba` untouched —
  re-hashed below). (b) DRY.md defects rule: findings-route defects are
  "never fixed inside the item; never dropped". A docstring-only item
  that touched the fenced file to fix D1 would violate both. Concur with
  UNFIXED; do not re-file (see `## Defects`).

### Owner-edit judgment (ran myself)

- Prose: the +14 docstring clause names all four rejected walkers with
  per-walker contract triples (terminal-column-or-`None` cursor anchor /
  projection traversability / terminal-model-or-`None` + accessor seal /
  `(field, opts)`-or-`None` certification) plus the reopen trigger ("a
  caller needing another walker's answer, or this classifier gaining an
  accessor-name fallback or a non-raising mode"). Citations are
  `path::Symbol` form, no line numbers. AGENTS.md-clean.
- AST-identity: `classify_path` body minus docstring identical ITEM vs
  worktree (ast dump compare => True); module function/class count 23 ==
  23; `git diff` ITEM..worktree for the file is exactly the +14
  docstring hunk, nothing else.
- Ruff + layout: `uv run ruff check` clean, `uv run ruff format --check`
  clean, `scripts/check_trailing_commas.py` fixed 0. No code layout
  touched (docstring only), so the trailing-comma/layout gates are
  vacuously satisfied.

### Freshness (re-hashed by me)

Worktree `git hash-object`: relations `1cf81e58`,
connection `3c4d5dcb`, plans `cce98531`, querysets `96618fba`,
list_field `d6af6164`. ITEM..current diff: relations +14 docstring hunk
only; connection/plans/querysets/list_field empty. The dirt on
`connection.py` etc. in `git status` is concurrent work outside this
item's scope (no ledger row, no item hunk) — preserved, unattributed,
untouched. Querysets read-only honored (no edit attempted; blob matches
the fenced value).

### Gate / pending-execution (judged after reading below)

No `proof:`-type execution is owed by a docstring-only rejection item
beyond the read-only probes already run (Django version print, M2M
attribute probe, AST-identity, ruff pair, hash-object set). Any
`## Pending execution` entries in the artifact are judged on read:
`gate:` witnesses stay as gates, and no `proof:` entry may remain
unlisted. Verdict and per-point reconciliation follow under Reconciliation.

### Reconciliation (Worker 2) — agree-or-differ per point, after reading Findings

- Owner `classify_path` (strict hop-plan, raises) + owned ladder
  internals (single-bodied): AGREE. My W0 triple matches F1 bullet 1;
  the lenient walk as fail-open arm inside the one `_traverses_to_many`
  body matches "already composed INTO the owner ... not re-litigated".
- Four rejections with contract triples (terminal-column-or-`None`
  keyset error / traversability-under-projection / terminal-model-or-`None`
  fail-open+accessor / field-opts-or-`None` certification refusal): AGREE
  on all four — each body opened, triples in my census match F1 bullets
  2-5. Closest pair W1/W4 (both order-side, both `None`-on-failure) still
  differ in subject (`model` vs `opts`), return (field vs `(field,
  opts)`), and terminal rule (W1 refuses relation terminals +
  nullable/reverse/multi; W4 resolves them for `Meta.ordering`
  expansion). Genuinely different, not two spellings.
- Exclusions (permissions-hops, filters registry walk, walker descent,
  order parsers, flatten mangler, `validate_lookup_expr` zero-callers):
  AGREE on every one; my OUT list gives a body-level reason per site and
  F3's verdict (zero in-package callers, public tail contract of
  in-flight specs, principle 11 keeps it) is identical to my dead-or-API
  judgment: API surface, correctly excluded, nothing to delete.
- C1 transform → 0 shared: AGREE (my X1, same count).
- C2 mid-path failure → 0 shared / independent: AGREE in substance.
  Counting note only: the probe lists six arms (lenient arm spelled out
  with its many-then-garbage `True`); I fold the lenient arm into the
  owner (five definitions). Same 0-shared verdict, same three-`None`s
  with three meanings (keyset error / refuse-certification /
  pass-through; W2 answers `False`, W0 raises).
- C3 5+ segments → touches nothing (loops): AGREE (my X3; same
  six-vs-five folding note, same verdict).
- C4 lifetime → one `lru` cache at owner: AGREE (my X4 matches the
  two-layer cache, `(model, field_path)` key, import publish,
  `cache_clear`/`cache_info` invalidation, `classify_path` contractually
  uncached). No new shared state added — correct.
- C5 owner confirmed: AGREE (my X5: strictest contract + leaf-module
  dependency direction, matching C5's "narrowest cohesive owner ...
  without reversing a dependency").
- F2 field_meta R3 trigger UNFIRED (elision single-hop): AGREE —
  verified at the bodies myself (`fk_id_elision_eligible` is a per-hop
  conjunction, `_target_pk_name` reads one model's pk,
  `_plan_select_relation` consumes one hop's stamp,
  `_selected_scalar_names` scans one child level). No compose owed.
- Triggers T1/T2/T3 + homes (owner clause written; querysets-clause text
  pending — fenced): AGREE. The +14 clause is in the diff (verified
  above); the querysets sibling clause is quoted as pending text and
  correctly NOT applied — that file is fenced read-only this cycle and
  the edit belongs to its owning item.
- DEFECT D1 UNFIXED: CONCUR — do not re-file. Every sub-point
  re-derived in my trace: Django 6.1 installed; unguarded
  `get_accessor_name()` after a `concrete`-only screen; live
  `AttributeError` on `(Book, "nope__x")` at both helper levels;
  fail-open-`None` contract stated in both docstrings; unwrapped seal
  call so the error escapes instead of becoming `(None, (code,
  detail))`; 500-class severity (availability break, no wrong data, no
  masking); `utils/querysets.py` card class with the M2M-blind oracle
  gap riding the same fix card as its regression arm; UNFIXED here
  correct on both halves (owner file fenced + defects never fixed
  in-item).
- No pending execution (probe 28/30 with 2 fails pinning D1; anchor 31
  passed): AGREE — `## Pending execution: None` is correct; both proofs
  ran, nothing is `execution-deferred`, and the full suite is Worker 0's
  final gate (AGENTS.md authorizes no pytest here beyond the focused
  anchor already run).
- relations.py +14 docstring, rest empty: AGREE — re-ran the item diff
  (`--stat`: 1 file, 14 insertions) and the per-file diffs for
  connection/plans/querysets/list_field (empty).
- Querysets read-only honored (`96618fba`): AGREE — re-hashed identical
  in the worktree; never edited.
- Enumeration (14-hit census, list_field five-hits-one-walker, walker
  descent different mechanism): AGREE. My wider 26-hit `.split(`
  instrument is a superset ending at the same verdict: no fifth walker.
- Matrix six axes: AGREE on all six discharge reasons (package-wide
  sweep, pure-sync inapplicability, pk/separator re-derivation with T3
  covering the spelling axis, no round-trip pair, independent oracles
  with the D1 gap named, omission-asymmetry IS the contracts).
- No-gate reasoning: AGREE under the sibling standard — a REJECTED
  finding owes triggers + a durable home (owner docstring clause,
  present), not a structural gate; same bar as the verified
  single-owned/rejected siblings.
- AGENTS.md prose on the diff: AGREE — `path::Symbol` citations, no
  line numbers, no process provenance; projection-only rejection owes
  no new tests, and the behaviors stay pinned by the existing oracles.
- Freshness: all eleven source + four test blob ids re-hashed
  identical to the artifact's record EXCEPT relations.py, which moved
  `7662b0bb` → `1cf81e58` by exactly this item's +14 hunk (expected).
  Connection worktree `3c4d5dcb` vs HEAD divergence is the concurrent
  cursor-guard hunk — correctly unattributed, no edit there, no stop
  triggered.

Differences: presentation only (six probe arms vs five definitions —
substantive agreement, since F1 itself folds the lenient walk into the
owner). One legibility nit observed, not filed as a defect: the
Enumeration sentence "The walker's own `_walk_selections` ..." sits in
the list_field paragraph while naming the optimizer walker; harmless.

### Verdict (Worker 2)

`Status: verified`. Rejection stands with per-walker contract
differences, triggers T1/T2/T3 with the owner home landed and the
fenced sibling home pending at its owner, D1 concurred UNFIXED and left
for its owning card, zero behavior change. No `revision-needed` item;
no new defect filed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-058]: ../SPECS/spec-058-graph_substrate-0_1_1.md
[spec-060]: ../SPECS/spec-060-search_fields-0_1_2.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[list-field]: ../../django_strawberry_framework/list_field.py
[order-sets]: ../../django_strawberry_framework/orders/sets.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[relations]: ../../django_strawberry_framework/utils/relations.py
[strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-keyset-connection]: ../../tests/test_keyset_connection.py
[test-list-field]: ../../tests/test_list_field.py
[test-relations]: ../../tests/utils/test_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
