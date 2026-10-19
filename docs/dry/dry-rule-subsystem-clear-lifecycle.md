# DRY review: `subsystem-clear-lifecycle`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `subsystem-clear-lifecycle`. Provisional owner the registry bus
(`django_strawberry_framework/registry.py::TypeRegistry` F6 aspects live here as
module-level bus, not methods). Known member files per the plan item (20):
[registry][registry], [finalizer][finalizer], [connection][connection],
[relay][relay], [filters-init][filters-init], [filter-inputs][filter-inputs],
[orders-init][orders-init], [order-inputs][order-inputs],
[mutation-inputs][mutation-inputs], [mutation-sets][mutation-sets],
[form-inputs][form-inputs], [form-sets][form-sets], [auth-mut][auth-mut],
[auth-q][auth-q], [serializer-inputs][serializer-inputs],
[serializer-converter][serializer-converter], [sets-mixins][sets-mixins],
[filter-sets][filter-sets], [order-sets][order-sets], [utils-inputs][utils-inputs].
Prior records used only as triggers, never verdicts: the registry file item's
F6 bus aspects (`docs/dry/dry-file-registry.md`, verified) and the six verified
registry siblings — both named claims re-derived against the tree at `HEAD
bfaee91d`: the teardown item's "`clear()` replays the F6 bus" cell holds
([registry][registry]`::TypeRegistry.clear` replays `iter_subsystem_clears()`
after dropping its own maps), and the enum-cache item's "`_enums.clear()` is
F6 bus replay, consumer not definition" holds (the reset line consumes F4
state; the key/collision contract lives in `register_enum` / `get_enum`). Never
read any `worker-memory/`.

Attribution before edit (item fences edits, never reading): the bus core
carries only ledgered clauses — `git diff HEAD --
django_strawberry_framework/registry.py` shows one hunk, the Family
`relay-node-name-decode` docstring trigger clause from `## Owned changes`, by
content. Every other member file's working dirt was diffed vs `git show HEAD:`
hunk-by-hunk: all 20 bus-line sweeps (`register_subsystem_clear` /
`iter_subsystem_clears` / `_subsystem_clears` / `before_bind` / `clear_*`) are
empty, and the added lines are pure logic/prose (connection cursor guards,
filter range-shape fail-loud arms, hostile-name wording, trigger clauses) with
zero new module-level mutable state. The item-scoped diff vs `ITEM_BASELINE
0d6a3427` is empty on all 20 package paths; the only new path is this artifact
(untracked, owned by this item). No stop triggered; nothing else on the bus
paths. Dirt elsewhere is concurrent work, left alone.

## System trace

Rule: each subsystem registers its teardown callback once, at its own import
time, under a stable logical owner; `TypeRegistry.clear()` replays every
registered callback (full reset, test-only) and the finalizer replays the
`before_bind` subset pre-bind (per-pass emit reset, production build path).
New subsystem with caches = one declaration (a `register_subsystem_clear`
line), never a new reset mechanism.

Bus contract, body-read:

- Registration: [registry][registry]`::register_subsystem_clear` validates
  (zero-arg callable, non-empty owner) and stores
  `_subsystem_clears[owner] = (clear, before_bind)`. Re-registering an owner
  replaces (reload-safe, no duplicates). `owner` is a logical identity, not an
  import path, so factory-generated callbacks do not collide.
- Replay: [registry][registry]`::iter_subsystem_clears` returns an immutable
  `tuple` snapshot in registration (dict-insertion = import) order;
  `before_bind=True` selects only flagged rows. `TypeRegistry.clear()` replays
  the full tuple after dropping its own maps; [finalizer][finalizer] replays the
  narrow tuple pre-bind, then binds declarations. No other production caller of
  `iter_subsystem_clears` exists in the package (tests only).
- Exceptions: neither replay loop guards — the first raising callback aborts
  the tail and propagates (P8 pins this). Every standing callback is
  practically infallible (`dict`/`list`/`set` `.clear()`, `delattr` guarded by
  `in subclass.__dict__`, `_safe_import` best-effort lookups); see `## Defects`
  (a).
- Double-clear: safe by construction — `.clear()` on an empty container is a
  no-op and every `delattr` arm is presence-guarded (P3).
- Lifetime: `_subsystem_clears` itself is never dropped by either mutator
  (P4); entries live owner-import to process end. `clear()` resets the state
  the callbacks point at, never the registration.

All 17 registration sites (static census 17/17; live minimal-process census 8
— laziness holds: only an imported owner can register):

| # | Owner | Flag | State cleared | Clear shape |
|---|---|---|---|---|
| 1 | `relay.node_fields` | full | `_node_fields_declared` list (finalize-time no-Node check ledger) | one-liner `.clear()` |
| 2 | `connection.type_cache` | full | `_connection_type_cache` dict (provenance-checked entries) | one-liner `.clear()` |
| 3 | `filters.helper_references` | full | `_helper_referenced_filtersets` set (orphan-audit ledger) | one-liner `.clear()` |
| 4 | `orders.helper_references` | full | `_helper_referenced_ordersets` set (orphan-audit ledger) | one-liner `.clear()` |
| 5 | `filters.input_namespace` | narrow | filter ledger + `_field_specs` + factory caches + `FilterSet` binding attrs | heavy `clear_generated_input_namespace` |
| 6 | `orders.input_namespace` | narrow | order ledger + `_field_specs` + factory caches + `OrderSet` binding attrs | heavy `clear_generated_input_namespace` |
| 7 | `mutations.input_namespace` | narrow | `_materialized_names` ledger | light `make_input_namespace` clear |
| 8 | `forms.input_namespace` | narrow | `_materialized_names` ledger | light clear |
| 9 | `rest_framework.input_namespace` | narrow | `_materialized_names` ledger + `_SERIALIZER_SHAPE_REGISTRY` | light clear + one extra dict |
| 10 | `auth.current_user_alias` | narrow | `CurrentUserAlias` ledger | light clear |
| 11 | `mutations.shape_cache` | full | per-shape build cache dict | `make_shape_build_cache` pair |
| 12 | `forms.shape_cache` | full | per-shape build cache dict | `make_shape_build_cache` pair |
| 13 | `rest_framework.shape_cache` | narrow | per-shape build cache dict (primed pre-finalize, so pre-bind) | `make_shape_build_cache` pair |
| 14 | `mutations.declarations` | full | `DjangoMutation` declaration list | `make_declaration_registry` |
| 15 | `forms.declarations` | full | `DjangoFormMutation` declaration list (disjoint) | `make_declaration_registry` |
| 16 | `auth.declarations` | full | auth surface declaration list (disjoint) | `make_declaration_registry` |
| 17 | `rest_framework.choice_enums` | full | `_SERIALIZER_CHOICE_ENUMS` name-keyed dict | one-liner `.clear()` |

Non-registering members and why (body-read, not gaps): [sets-mixins][sets-mixins]
declares the reset population (`SetLifecycleAttrs` / `binding_attrs` — the
DRY.md worked-example descriptor); [filter-sets][filter-sets] /
[order-sets][order-sets] declare their ONE `_lifecycle` instance each;
[utils-inputs][utils-inputs] owns the three clear bodies
(`clear_generated_input_namespace`, `make_shape_build_cache::clear_fn`,
light `clear_fn`) plus the parked-globals lifecycle paragraph every site
cross-references. Their state reaches `clear()` through the consuming
subsystem's row (heavy clears resolve factory/set modules via `_safe_import`,
so partial-load build states still clear whatever is reachable).

Intentional variation inside the table: row 13 is narrow while rows 11–12 are
full-only because the serializer shape cache can be primed before finalization
by `input_type_name()` — the comment at the registration site states it — so a
pre-bind reset must drain it or nested hits suppress re-materialization. Row 9
clears two dicts because the shape-debug registry shares the input build
lifecycle (docstring-stated). Neither is a defect; both are recorded here.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** All 17 sites enumerated by body (above).
   The three declaration ledgers share mechanics through
   [mutation-sets][mutation-sets]`::make_declaration_registry` with disjoint
   stores (already consolidated); the three shape caches share
   [utils-inputs][utils-inputs]`::make_shape_build_cache` with disjoint dicts
   (already consolidated); the two heavy namespace clears share
   `make_set_input_namespace` + `clear_generated_input_namespace` (already
   consolidated); the four light namespace clears share `make_input_namespace`
   (already consolidated). What remains per site is one adapter line over its
   own state (principle 5). No flavor keeps a second bus.
2. **Sync/async twins.** Zero `AsyncFunctionDef` on the bus path and in every
   callback (all are `dict`/`list`/`set` clears plus guarded `delattr`; no ORM
   I/O, no awaits, no threads). Reads are colorless; registration is
   import-time-only. Trigger: a teardown callback touching the DB or awaiting.
3. **Derived rather than repeated knowledge.** `iter_subsystem_clears()`
   derives the replay population per call from the one dict; no site
   re-derives the owner list; each owner string is declared once, at its
   registration. The parked-globals paragraph is stated once
   (`make_input_namespace`) and cross-referenced, never restated.
4. **Inverse / round-trip pairs.** register/iter/replay; light
   materialize/clear; heavy materialize/clear; declaration
   register/clear/iter; shape get-or-store/clear. Each pair pinned by the
   oracles below.
5. **Contracts restated in another medium.** Production (bus + 17 adapters);
   oracles ([test-registry][test-registry] bus rows, per-subsystem namespace /
   declaration / shape-cache rows at their mandated tiers); projections
   (bus + adapter docstrings, verified against bodies; specs 027/028/031/032/
   036/038/039/040 as contract sources; glossary clear entries). No consumer
   restates the lifecycle.
6. **Enforcement by omission.** Swept all 20 member files for module-level
   mutable state with no bus row: none found. Factory caches with no direct
   row clear through their consumer's heavy row via `_safe_import`; the
   `SetLifecycleAttrs` population declares rather than stores; in-flight
   dirty hunks add no new module-level state (verified per-file above). No
   member lacks a guard its contract requires: no defect.

### Enumeration

Instrument: `rg register_subsystem_clear\( over the 117-file package
population (`git ls-files django_strawberry_framework | grep -c` = 117,
re-counted) + `ast` def census of the bus + body reads of all 17 adapters.
Every bus member assigned; every challenge ends in the family row or a
recorded rejection; no file-local row (each rule has its 17 adapters or its
rejection).

- `register_subsystem_clear` / `iter_subsystem_clears`: 1 def each; production
  call sites of the former: exactly the 17 adapters; of the latter: exactly 2
  (`TypeRegistry.clear`, finalizer pre-bind).
- `_subsystem_clears`: 1 storage dict; written only by `register_subsystem_clear`
  (incl. test save/restore harness); read only by `iter_subsystem_clears`.
- `TypeRegistry.clear` replay tail: 1 site (the `for clear in
  iter_subsystem_clears(): clear()` loop). Finalizer narrow replay: 1 site.
- Adapters: 17 defs/bound-methods over 14 modules (table above); 5 share
  groups already factored (declaration ×3, shape ×3, heavy ×2, light ×4);
  5 one-liners + connection + choice-enums stay as named adapters.

### Challenges

Counts are authoritative definitions only; consumers, oracles, projections
listed, never counted. Workspace probes P1–P8 map onto C1–C5 (19/19
`execution-verified`); negative control N1 proved by source mutation in the
copy.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New subsystem with caches (e.g. a second connection-class cache) | **1** (one `register_subsystem_clear` line + its callback; the bus needs no change). Contrast, 0 moved for the bus itself. P6 proves the shape: unregistered state survives `clear()` silently, and no census oracle names the newcomer — the subsystem's own clear test must pin its row (each standing row is owned by its subsystem's tier, not by a central list). |
| C2 | Third lifecycle phase beyond the `before_bind` bool | **1** (the register filter + iter filter in [registry][registry]); the 2 replay sites are consumers. P2 pins the current two-phase shape. N1 proves the flag is load-bearing (flag dropped → narrow set loses the owner). |
| C3 | Collapse all 17 callbacks into one shared clearable-record (generic "register this dict/set/list, the bus clears it") | **Rejected**: adapters clear genuinely different state with different lifetime reasons and different phase flags (helper-ledger orphan audits, provenance-checked connection entries, parked-global input ledgers, per-pass shape caches, pre-bind-surviving declarations, disjoint key spaces). A generic record re-declares every owner/flag/object triple while coupling independent subsystems and obscuring the stated reasons (parked-globals, orphan audits, primed-pre-finalize, first-wins naming). Removes no change obligation. |
| C4 | Replay-order change (sorted / reversed / parallel replay) | **0** definitions depend on order: all 17 ledgers are disjoint; both pre-bind rows (namespace + shape) drain before any rebuild; declarations are full-only. P5 pins current (registration) order; no consumer reads it. Contrast: type-teardown LIFO is order-load-bearing and oracle-pinned; the bus is order-free by disjointness. |
| C5 | Exception isolation (a raising callback skips instead of aborting the tail) | **1** (the `clear()` replay loop; the finalizer loop twins it). Current abort-and-propagate pinned by P8. Not proposed; trigger below. |

**Experiment (executed, disposable workspace).** Copy per [dry][dry] "Tests"
(`rsync`, docs excluded); every command via `uv run --directory "$WS"` with
`$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/subsystem-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_bus.py
```

Proof (`CHECKS_PASSED=19/19`): entry shape + reload-replace + both rejections
(P1), phase filter + tuple snapshot (P2), full replay + double-clear safety
(P3), bus survives `clear()` (P4), registration-order replay (P5),
unregistered-state leak (P6), adapter distinctness + live-owner subset (P7),
raise-aborts-tail + propagates (P8). Minimal-process live census: 8 owners vs
17 static sites (laziness re-proved). Status: `execution-verified`. Copy
`__file__`: `.../dry-ws/subsystem-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/subsystem-w1/examples/fakeshop/db.sqlite3` (copy's own tree and
database; never the shared tree; the probes open no DB at all). No source
mutation in the proof. Searched population inside the copy: 117 `.py`
(matches the shared tree). `grep -c truncated` == 0.

**Negative control N1 (executed, disposable workspace).** Dropped only
`before_bind=True` from the copy's `filters.input_namespace` row, re-ran a
narrow-membership assertion: fails exactly at
`filters.input_namespace missing from before_bind set` (exit 1). Restored
byte-identical (md5 `196a1800…` before and after), re-ran: passes, and the
full 19/19 re-passes. Status: `execution-verified`. Proves the instrument
fails the divergence it guards.

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "subsystem or
before_bind or clear_runs_owner or clear_tolerates or clear_drops_all_state"`
→ 9 passed (every bus oracle row this finding relies on, green post-trace with
zero edits in flight, so no run is invalidated).

## Findings

### F1 — subsystem-clear lifecycle (REJECTED consolidation: single-owned bus + factored adapters, no further merge)

- **Contract + variation.** Owner-registered zero-arg teardowns keyed by
  stable logical owner; `before_bind=True` marks per-pass emit-state resets
  the finalizer also runs pre-bind. Varies on phase membership only (C2);
  order-free (C4); abort-on-raise (C5).
- **Sites + roles.** *Definitions*: `_subsystem_clears`,
  `register_subsystem_clear`, `iter_subsystem_clears`, the `clear()` replay
  tail (one each, all [registry][registry]). *Replay consumer*:
  [finalizer][finalizer] pre-bind sweep (narrow only). *Adapters*: the 17
  callbacks (table above; 5 groups already factored through
  `make_declaration_registry` / `make_shape_build_cache` /
  `make_set_input_namespace`+`clear_generated_input_namespace` /
  `make_input_namespace`). *Population declarants* (not state):
  `SetLifecycleAttrs` + the two `_lifecycle` instances. *Oracles*:
  `test_clear_runs_owner_registered_subsystem_callback`,
  `test_before_bind_iteration_excludes_full_clear_only_callbacks`,
  `test_register_subsystem_clear_rejects_string_references`,
  `test_register_subsystem_clear_rejects_empty_owner`, the four
  poisoned-`sys.modules` tolerance rows, `test_clear_drops_all_state`,
  plus each subsystem's own namespace/declaration/shape rows at its tier.
  *Projections*: bus + adapter docstrings, the parked-globals paragraph,
  glossary clear entries, specs 027/028/036/038/039/040.
- **Challenges.** C1 → 1 (+0 bus); C2 → 1; C3 → rejected; C4 → 0; C5 → 1
  (not proposed). Count > 1 nowhere in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).** [registry][registry] bus stands:
  narrowest cohesive owner every subsystem can import without cycles or
  reversing a dependency (all 14 adapter modules already import it at module
  top; the reverse would cycle). Stored-registration lifetime: validity key =
  owner-import → process end; publish point = owner import (executable
  callback, so renames fail at the owner instead of drifting); who may mutate
  = `register_subsystem_clear` (import-time) + test-harness save/restore;
  reads = `iter_subsystem_clears` snapshots; explicitly NOT invalidated by
  `clear()` or the pre-bind sweep (P4). Callback-state lifetimes: emit rows
  (validity = one bind pass; invalidated by pre-bind sweep + full clear);
  declaration rows (validity = collection → full clear; survive retry by
  contract); cache rows (validity = one pass or one clear per their flag).
- **Migration.** None (zero-edit rejection: no behavior hunk, no test hunk;
  every durable home below already exists).
- **Distinct behavior (stays separate).** Declaration survival across
  recover-in-place retry vs emit reset per pass; parked input classes
  (ledgers drain, `__dict__` never stripped — LazyType holders survive
  autouse reload); connection provenance (a surviving entry serves only its
  own definition); helper-ledger orphan audits (emptiness is load-bearing);
  serializer shape primed pre-finalize (narrow cache vs full-only twins);
  disjoint enum key spaces (registry tuple vs serializer name — owned by the
  enum-cache finding, linked not re-litigated).
- **Behavioral proof.** `execution-verified` for entry shape, replace
  semantics, both rejections, phase filter, full replay, double-clear,
  bus survival, order, the leak-without-registration shape, adapter
  distinctness, and abort-on-raise (workspace 19/19 + N1 + the authorized
  9-passed focused run). `static-reviewed` for the zero-`async` census, the
  17/17 static census, oracle-body independence (synthetic owners +
  literals; none reads the bus dict except the documented harness
  save/restore), and docstring-vs-body prose.
- **Structural gate.** Deferred with reason: a behavior-preserving hand copy
  of any adapter (identical clear over the same object) passes every standing
  oracle by construction, so no behavioral gate can pin unity; only a source
  census could ("every cache has a bus row"), and that is a bespoke existence
  test per helper, which [dry][dry] forbids for gate-only findings — the same
  bar as all six verified registry siblings and the teardown finding. Unity
  rests on the one-way import edges plus the triggers below. Coverage that
  stays: the bus-mechanism rows (each fails a real break — N1 demonstrates
  the shape) plus each subsystem's own clear rows at its tier.
- **Coupling.** None.
- **Freshness.** Working-tree blob ids (`git hash-object`; HEAD id in
  parentheses where dirty): [registry][registry] `612bea87…` (`HEAD`
  `9cc8bb55…`; delta is the ledgered name-decode trigger clause only),
  [finalizer][finalizer] `f4266a15…` (`HEAD` `77fd9a2d…`; ledgered snapshot
  trigger only), [connection][connection] `3c4d5dcb…` (`HEAD` `93e998f2…`;
  concurrent cursor-guard feature, outside every cited cache line),
  [relay][relay] `69085e7a…` (`HEAD` `c3c5aea5…`; ledgered decode trigger
  only), [filter-inputs][filter-inputs] `06797dc7…` (`HEAD` `82b52d97…`;
  concurrent range-shape hunk, outside every cited namespace line),
  [filter-sets][filter-sets] `4a40e51b…` (`HEAD` `4ab65a26…`; predicate-key
  wording, outside lifecycle lines), [form-inputs][form-inputs]
  `436fcf42…` (`HEAD` `55614839…`; hostile-value guards, outside namespace
  lines), [form-sets][form-sets] `98ef150d…` (`HEAD` `36ce80b4…`; safe-name
  wording, outside declaration/shape lines), [mutation-sets][mutation-sets]
  `936f5ae7…` (`HEAD` `cffa29e5…`; safe-name wording, outside shape/
  declaration lines), [auth-mut][auth-mut] `200805d2…` (`HEAD`
  `dbe64995…`; safe-name wording, outside declaration lines),
  [filters-init][filters-init] `86b25818…`, [orders-init][orders-init]
  `ed546f9c…`, [order-inputs][order-inputs] `6f6ec946…`,
  [mutation-inputs][mutation-inputs] `fc442047…`, [auth-q][auth-q]
  `5c59ba75…`, [serializer-inputs][serializer-inputs] `9b17d952…`,
  [serializer-converter][serializer-converter] `32904418…`,
  [sets-mixins][sets-mixins] `ad8987ea…`, [order-sets][order-sets]
  `6044ab1a…`, [utils-inputs][utils-inputs] `ee31d360…` (all clean vs HEAD),
  [test-registry][test-registry] `e330cfb8…`,
  `docs/dry/dry-file-registry.md` `4350662b…`,
  `docs/dry/dry-rule-type-teardown-lifecycle.md` `18652d82…`,
  `docs/dry/dry-rule-type-registry-enum-cache.md` `8afa1681…`. Searched
  population: whole package (117 `.py`, both trees); excluded on strength of
  body: all modules without bus vocabulary. Installed Strawberry / Django
  read as behavior anchors only, not fingerprinted inputs. Any fingerprint
  change reopens the finding.
- **Reconsideration triggers (recorded at the owners).** The lifecycle stays
  single-owned until one fires: T-phase fires if a subsystem needs a reset
  moment neither full-clear nor pre-bind names (C2 — extend the flag, never a
  second bus); T-record fires if two adapters converge on one object, one
  flag, and one lifetime reason with no residual difference (C3); T-isolate
  fires if a fallible teardown (network / thread / file handle) registers and
  needs tail protection (C5). Durable homes: the `register_subsystem_clear`
  docstring (phase vocabulary + `before_bind` meaning), the `clear()` replay
  comment (soft-dependency laziness + rename-fails-at-owner), the finalizer
  pre-bind comment (emit-vs-declaration split), this finding.

## Defects

None meeting the [agents][agents] bar (contract row + feasible shape +
wire/config input). Three observations kept out for cause: (a) a raising
callback skips the tail (P8) — every standing callback is infallible
(`.clear()` / guarded `delattr` / `_safe_import`), and no contract row
requires isolation, so this is a stated semantic, not a bug; T-isolate covers
the day a fallible teardown registers. (b) `rest_framework.shape_cache` is
narrow while its mutation/form twins are full-only — intentional
(primed-pre-finalize, site-commented), not drift. (c) No census oracle names
all 17 owners, so a future subsystem that caches without registering leaks
silently until its own clear test runs (P6 demonstrates the shape) — an
absence, not a second definition, and no contract source extends the rule to
an unnamed future subsystem (axis 6 needs established applicability); no card
owed until a concrete unregistered cache appears. None fixed inside this item.

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable workspace
(19/19 + N1, copy `__file__` + copy DB `NAME` recorded, no source mutation
except the copy-only N1 with byte-identical restore); the one authorized
shared-tree focused test ran green post-trace (9 passed) with zero edits in
flight, so no run is invalidated. No `execution-deferred` items.
`FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by construction`: every
executed claim is in-memory `dict`/`list`/`set` work plus pure function
registration on fresh instances; the probes open no DB (recorded `NAME` is
the copy's own file, never touched). Full-suite gate business is deferred to
the final-gate item with reason: the entry command authorizes workspace runs
plus one focused `--no-cov` test, and a green unmutated suite would discharge
no failability proof for a rejection that proposes no gate.

## Judgment

The bus is a lifecycle fan-out, single-owned at [registry][registry], with
all sharing already factored (`make_declaration_registry`,
`make_shape_build_cache`, `make_set_input_namespace` +
`clear_generated_input_namespace`, `make_input_namespace`) and the remainder
as 5 named one-liner adapters over genuinely different state. The same
"clear my dict" spelling 5 times is 5 adapters, not 5 definitions (principle
5); a shared clearable-record would re-declare every triple while hiding the
reasons (principle 11). Consolidation rejected; zero edits.

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`0d6a34270ac271136debb706681a7b77010e2592`) is empty on all 20 member paths
(and vs `HEAD` `bfaee91d` likewise, except the content-attributed concurrent
hunks listed under Freshness); the only new path is this artifact (untracked,
owned by this item). No test file touched, so no test-tier obligation arises
beyond the consumed focused run. No `CHANGELOG.md` touch. No commit per
standing rule.

After the (zero) edits: `uv run ruff check` + `uv run ruff format --check`
have no touched `.py` paths to run against (vacuously satisfied; `.md`
artifacts are excluded from format). The artifact itself uses reference-style
links with the bottom `LINK DEFINITIONS` block and `path::Symbol` citations.

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
`WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/subsystem-w1`
(includes its own `.venv`, created by the authorized runs, plus `probe_bus.py`
holding the 19 executed checks + `probe_n1.py` holding N1). No manifest (no
`prove_failability.py` run — no gate added, none owed).

Worker 0 rows: tick Family `subsystem-clear-lifecycle` (this artifact); no
`## Responsibility index` change (provisional owner + all 20 member files
already covered, status stays `open` until Worker 2); no `## Owned changes`
append (zero tracked edits); no defect homing (none found).

## Independent verification (Worker 2)

Own trace, recorded before reading `## Findings` above (bodies read at HEAD
`bfaee91d`; worktree hashes re-checked below; no `worker-memory/` opened).

Bus contract, re-derived from [registry][registry] bodies. Registration:
[registry][registry]`::register_subsystem_clear` validates zero-arg callable +
non-empty owner, stores `_subsystem_clears[owner] = (clear, before_bind)`;
re-register replaces (reload-safe, no duplicates); owner is a logical
identity, not an import path. Replay: [registry][registry]`::iter_subsystem_clears`
returns an immutable tuple snapshot in dict-insertion (import) order;
`before_bind=True` selects flagged rows only. [registry][registry]`::TypeRegistry.clear`
replays the full tuple after dropping its own maps; [finalizer][finalizer]
replays the narrow tuple pre-bind, then binds declarations; no other
production caller of `iter_subsystem_clears` exists (tests only). Order:
registration order, and order-free by disjointness (every callback clears a
distinct object; both pre-bind rows drain before any rebuild; declarations
are full-only; contrast type-teardown LIFO which is order-load-bearing).
Exceptions: neither replay loop guards — first raise aborts the tail and
propagates. Double-clear: safe — `.clear()` on empty is a no-op, every
`delattr` arm is `in subclass.__dict__`-guarded, `_safe_import` lookups are
best-effort. Lifetime: `_subsystem_clears` is never dropped by either
mutator (no `_subsystem_clears.clear()` in the package); entries live
owner-import to process end; `clear()` resets pointed-at state, never the
registration.

Registrants, static census 17/17 over 14 modules (each with cleared state,
body-read). Full-clear rows: `relay.node_fields` (list
`_node_fields_declared`), `connection.type_cache` (dict
`_connection_type_cache`, provenance-checked), `filters.helper_references`
(set `_helper_referenced_filtersets`), `orders.helper_references` (set
`_helper_referenced_ordersets`), `mutations.shape_cache` /
`forms.shape_cache` (per-shape dicts via `make_shape_build_cache`),
`mutations.declarations` / `forms.declarations` / `auth.declarations`
(disjoint lists via `make_declaration_registry`),
`rest_framework.choice_enums` (dict `_SERIALIZER_CHOICE_ENUMS`). Narrow
(pre-bind + full) rows: `filters.input_namespace` / `orders.input_namespace`
(heavy: ledger + `_field_specs` + factory caches + `_lifecycle` binding
attrs via `clear_generated_input_namespace`), `mutations.input_namespace` /
`forms.input_namespace` / `auth.current_user_alias` (light: single ledger
via `make_input_namespace`), `rest_framework.input_namespace` (light ledger
plus `_SERIALIZER_SHAPE_REGISTRY` debug drain, docstring-stated),
`rest_framework.shape_cache` (narrow per-shape dict, primed pre-finalize so
pre-bind, site-commented). Non-registering members: [sets-mixins][sets-mixins]
`::SetLifecycleAttrs` + `::binding_attrs` derivation (population
descriptor); [filter-sets][filter-sets] / [order-sets][order-sets] one
`_lifecycle` instance each; [utils-inputs][utils-inputs] owns the three
clear bodies (`::clear_generated_input_namespace`,
`::make_shape_build_cache` pair, `::make_input_namespace` trio) plus the
parked-globals paragraph. No second bus: only [registry][registry] defines
a subsystem-clear dict; `_type_teardowns` is the separate rejected
teardown family; prose mentions in inputs/finalizer are consumers, not
stores.

Definition counts. One change obligation for the bus mechanism
(`_subsystem_clears` + register + iter + `clear()` replay tail, all in
[registry][registry]); the finalizer narrow sweep is a consumer (1 site);
production callers of register: exactly 17; of iter: exactly 2. Adapters:
17 callbacks over 14 modules; 12 already factored through
`make_declaration_registry` (x3), `make_shape_build_cache` (x3),
`make_set_input_namespace` + `clear_generated_input_namespace` (x2),
`make_input_namespace` (x4 incl. auth alias); remainder 5 one-liner
adapters (relay, connection, 2x helper-ledger, choice-enums) + the 2 stated
intentional variations (narrow serializer cache, shape-debug drain). Owner
I would choose: [registry][registry] bus (principle 7) — narrowest
cohesive owner every adapter module already imports at top without cycles;
the reverse would cycle; dependency direction wins over size.

C3 challenge, applied myself. New subsystem with TWO caches. With the bus:
one callback clearing both (or two one-liners) + one register line per
owner row — ~3 lines, state + lifetime + flag stated at the owner. With a
declarative clearable-record (principle 1): two declarations (owner/flag/
object triples) + the record type + driver + validation — saves ~1 line
per cache while adding ~30 lines of machinery and coupling independent
subsystems. Not worth it. Residual-candidate check: no adapter pair shares
more than the bus call. Shape caches, declaration ledgers, light/heavy
namespaces already share their factories (the 5 factored groups); the 5
one-liners share only the language primitive `.clear()` over disjoint
objects with different flags and lifetime reasons (orphan audits,
provenance, parked-globals, name-keyed enums); the rest pair
(ledger + debug drain) occurs once. Verdict: irreducible remainder.
Concur REJECT. Holding family: none owed.

Unregistered-cache sweep (axis 6 + no-census-oracle). Module-level
mutables without a bus row, each body-justified: dynamic set caches
(model-identity keys, stale entry cannot wrong-hit, comment-stated no
hook); `_lookups_for_field_class_cache` (Django field-class keys, never
recreated by `clear()`); `_SERIALIZER_FIELD_CONVERTERS` (consumer
extension registry, process-persistent by design, mirrors `SCALAR_MAP`);
`_ASYNC_MUTATION_LOCKS` (process-wide mutex, not test state); derived
maps (`_FORM_KEY_BY_PYTHON_ATTR`, lookup tables) are pure derivations
(principle 4, not cached across a validity boundary). No subsystem today
caches across `clear()` unregistered in a way that leaks stale state into
the next build. So: not a D1-class defect (no contract row + reaching
wire sequence names an unnamed future subsystem); accepted risk with
trigger. Trigger judged recorded: C1/P6 (subsystem's own clear test must
pin its row) plus observation (c) plus T-record. Adequate; no card owed
until a concrete unregistered cache appears.

Lifetime/boundedness. Registrations never dropped by `clear()` is
contract, not leak. Boundedness pinned by: fixed owner vocabulary (17
stable strings), owner-keyed replace (reload accumulates nothing), laziness
(only imported owners register; minimal-process census 8 vs static 17
re-proves it), test-harness save/restore around synthetic owners. Across
tests the dict size is constant; state dicts drain while the registration
persists. Concur with P4 + lifetime fields.

Gate judgment. No behavioral gate can pin unity (hand copy over the same
object passes every oracle by construction); only a source census could,
and a bespoke existence test per helper is forbidden for gate-only
findings. Same bar as the six verified registry siblings and the teardown
finding. Standing coverage (bus-mechanism rows, each failing a real break
per N1 shape, plus each subsystem's own clear rows at its tier) is the
correct remainder. Concur: no gate owed, triggers carry the remainder.

Agreement/difference per point. Bus definitions (list + clear-replay tail)
— agree. Replay consumer = finalizer pre-bind narrow sweep — agree. 17
adapters with the stated breakdown — agree (recounted 17/17, 14 modules).
`SetLifecycleAttrs` + two `_lifecycle` declarants with bodies in
[utils-inputs][utils-inputs] — agree. No second bus — agree. C1 new
subsystem 1 — agree. C2 third phase 1 — agree. C3 shared-record REJECTED
(5 groups factored, 5 one-liners stay) — agree, with the irreducibility
proof above. C4 replay-order 0 (disjoint, order-free; contrast teardown
LIFO) — agree. C5 exception isolation 1 (abort-and-propagate pinned) —
agree. Owner registry bus (principle 7) — agree. Lifetime
(import-to-process-end, never dropped; emit/declaration/cache rows per
flag) — agree. REJECT consolidation (5 named adapters, not definitions) —
agree. No defects with 3 cause-kept observations — agree (each judged
above; none meets the agents defect bar). No pending execution (19/19 +
N1 executed; 1 focused run 9 passed; sharded/PG inapplicable) — agree
(see below). Zero edits — agree.

Freshness re-hashed (`git hash-object` worktree vs HEAD). Match the
artifact in all 21 rows: [registry][registry] `612bea87` vs HEAD
`9cc8bb55` (ledgered name-decode clause only); [finalizer][finalizer]
`f4266a15` vs `77fd9a2d` (ledgered snapshot trigger only);
[connection][connection] `3c4d5dcb` vs `93e998f2` (concurrent cursor
guards, outside cache lines); [relay][relay] `69085e7a` vs `c3c5aea5`
(ledgered decode trigger only); [filter-inputs][filter-inputs] `06797dc7`
vs `82b52d97` (concurrent range-shape hunk, outside namespace lines);
[filter-sets][filter-sets] `4a40e51b` vs `4ab65a26`;
[form-inputs][form-inputs] `436fcf42` vs `55614839`;
[form-sets][form-sets] `98ef150d` vs `36ce80b4`;
[mutation-sets][mutation-sets] `936f5ae7` vs `cffa29e5`;
[auth-mut][auth-mut] `200805d2` vs `dbe64995` (all outside cited lines;
bus-token grep over the worktree diff is empty save `+++`/`---`
headers); clean matches: [filters-init][filters-init] `86b25818`,
[orders-init][orders-init] `ed546f9c`, [order-inputs][order-inputs]
`6f6ec946`, [mutation-inputs][mutation-inputs] `fc442047`,
[auth-q][auth-q] `5c59ba75`, [serializer-inputs][serializer-inputs]
`9b17d952`, [serializer-converter][serializer-converter] `32904418`,
[sets-mixins][sets-mixins] `ad8987ea`, [order-sets][order-sets] `6044ab1a`,
[utils-inputs][utils-inputs] `ee31d360`, [test-registry][test-registry]
`e330cfb8`. Nothing stale; no reopen.

`## Pending execution` judged. Workspace 19/19 + N1 claim accepted on
its recorded evidence (copy `__file__` + copy DB `NAME`, no source
mutation except copy-only N1 with byte-identical restore); no
`execution-deferred` remains so no re-run is owed by this item. Focused
run (9 passed, bus oracle rows, post-trace, zero edits in flight) needs
no invalidation. Sharded/PG `inapplicable by construction` accepted:
every executed claim is in-memory `dict`/`list`/`set` work plus pure
registration; probes open no DB. Full-suite gate correctly deferred to
the final-gate item (a green unmutated suite discharges no failability
proof for a rejection proposing no gate). `Status: verified` with no
`pending execution` flag is correct.

AGENTS.md prose on empty diff judged. Item-scoped diff vs `ITEM_BASELINE
0d6a3427` is empty on all 20 package paths; vs HEAD the only bus-path
hunk is the ledgered sibling clause (name-decode trigger, 4 lines,
content-attributed to `## Owned changes`); all other bus-token sweeps
over the worktree diff are empty and added lines carry zero new
module-level mutable state. Zero tracked edits is legitimate (matrix
discharged, challenges counted, rejections carry triggers, backstop
assigned). No process provenance beyond the required scratch paths; all
citations are `path::Symbol` via the reference-style link block (10
canonical headers intact); no test tier owed beyond the consumed focused
run at the mandated package tier. `ruff` vacuous (no touched `.py`;
artifacts excluded from format). Concurrent dirt preserved, untouched.

Defects (Worker 2): none. The three observations stay cause-kept; the
sweep above found no concrete unregistered cache, so no new defect is
filed.

Verdict: `verified`, no pending execution. Worker 0 rows owed: tick
Family `subsystem-clear-lifecycle`; `## Responsibility index` status
`open` to `rejected` (single-owned bus + factored adapters, no merge);
no `## Owned changes` append; no defect homing; remove by explicit path
after tick: `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/subsystem-w1`
(Worker 1 scratch only; this pass created no scratch).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mut]: ../../django_strawberry_framework/auth/mutations.py
[auth-q]: ../../django_strawberry_framework/auth/queries.py
[connection]: ../../django_strawberry_framework/connection.py
[filter-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[form-inputs]: ../../django_strawberry_framework/forms/inputs.py
[form-sets]: ../../django_strawberry_framework/forms/sets.py
[mutation-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutation-sets]: ../../django_strawberry_framework/mutations/sets.py
[order-inputs]: ../../django_strawberry_framework/orders/inputs.py
[order-sets]: ../../django_strawberry_framework/orders/sets.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/relay.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[serializer-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
