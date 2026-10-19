# DRY review: `connection-order-ladder`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

Posited rule (plan row; owner candidate
[plans.py][plans]`::effective_connection_order` +
`ends_in_unique_column` + `deterministic_order`, composing
[querysets.py][querysets]`::applied_order` / `default_order` for the
explicit-else-default tier; consumers [connection.py][connection] and
[nested-planner.py][nested-planner]): the deterministic connection
ordering ladder, from the explicit-else-default tier through the
unique-column-ending order. No prior family artifact exists; this
trace is fresh at current bytes (HEAD `23b5f421` + working tree),
census-first: the 4 indexed files were not assumed complete. The
package-wide sweep finds the rule's mechanism complete inside the
nomination plus lookalikes outside it ([keyset.py][keyset],
[list-field.py][list-field], [lateral-fetch.py][lateral-fetch],
[types-base.py][types-base], [orders-sets.py][orders-sets],
[single-parent-fetch.py][single-parent-fetch]).

The 2026-10-08 rebase split
[queryset-private.py][queryset-private] out of
[querysets.py][querysets]; nomination text predating the split is
stale where it names moved symbols. Verified at current bytes: the
split module owns private `QuerySet` state reads/writes only
(`_db`, `_hints`, `_fields`, prefetch lookups, deferred filter,
`_for_write`, `_query`, `_chain`) and carries no ordering symbol;
`applied_order` / `default_order` still live in
[querysets.py][querysets] (`:333` / `:317` WT).

### Pins and attribution

HEAD `23b5f421` (detached, intended).
`ITEM_BASELINE=83a1c0c8901bc229239e82bae203b6a01d5ce13c` (stash
commit on `23b5f421`; `before` copy in slot-1). The item-scoped diff
vs `ITEM_BASELINE` over package/tests/examples is empty (this item
has made no edits; fingerprints below prove it).

| File | WT | HEAD | BASE | Dirt attribution (by diff content vs `git show HEAD:`) |
|---|---|---|---|---|
| `optimizer/plans.py` | `218be6d2` | `6f2d0c70` | `218be6d2` | 3 hunt hunks (truth import, `truth.name` in `resolver_key`, `truth.static_attr` `_meta` read in `ends_in_unique_column`); ladder bodies otherwise HEAD-clean |
| `connection.py` | `d537ab99` | `b984ca99` | `d537ab99` | heavy hunt dirt incl. `_finalize_queryset` guard-removal hunk + `_keyset_order_ref` guard-removal hunk; ladder call lines themselves unchanged |
| `optimizer/nested_planner.py` | `a9875bbb` | `73d03184` | `a9875bbb` | 2 hunt hunks (truth import, `truth.name` log line) + f56's ledgered `target_definition=` pass-through (buildable); ladder step (d) clean |
| `utils/querysets.py` | `e6660894` | `4d8a3d39` | `e6660894` | heavy hunt dirt throughout the seal; `default_order` / `applied_order` bodies (`:317-339` WT) clean (nearest hunks end at WT `:309`, resume at WT `:403`) |
| `utils/_queryset_private.py` | `a26a8d43` | `ff8b2b46` | `a26a8d43` | concurrent; no ordering symbol at either state |
| `keyset.py` | `a1890813` | `ec694bc8` | `a1890813` | concurrent dirt outside the cursor-field validation read here |
| `list_field.py` | `b5cfe957` | `c84cefb2` | `b5cfe957` | concurrent dirt outside the `_selected_ordering` read here |
| `optimizer/lateral_fetch.py` | `995f1aa2` | `995f1aa2` | `995f1aa2` | clean |
| `types/base.py` | `f42bcee3` | `a63b7edf` | `f42bcee3` | concurrent dirt outside the `_validate_cursor_field` read here |
| `orders/sets.py` | `fd453bec` | `2d35adfa` | `fd453bec` | concurrent dirt outside the `_apply_orderings` read here |
| `optimizer/single_parent_fetch.py` | `bd6beb1c` | `bd6beb1c` | `bd6beb1c` | clean |
| `utils/connections.py` | `2313fce5` | `2313fce5` | `2313fce5` | clean; no order derivation (sidecar-kwarg plumbing only) |

All BASE blobs equal WT (nothing moved since the baseline). Dispatch
pins match: plans WT `218be6d2` / HEAD `6f2d0c70`, connection
`d537ab99` / `b984ca99`, nested_planner `a9875bbb` / `73d03184`,
querysets `e6660894` / `4d8a3d39`.

Nothing in this item touches hunt-dirtied lines: the verdict is
zero-edit, so no consolidation is blocked-on-hunt (there is nothing
to block).

### The ladder as traced

Four rungs, each one definition, each consumer composing by name
(AST census over all 121 package `.py` files: each `def` below
occurs exactly once):

1. **Keyset-default rung** —
   [plans.py][plans]`::effective_connection_order` (`:959`): a
   keyset target's declared `cursor_field` IS the connection order
   when no explicit `order_by` won (`:985-986`); otherwise rung 3
   over rung 2 (`deterministic_order(applied_order(query, model),
   model)`, `:987`). Precedence composer, not a reader: it names
   the tier helpers. Contract source:
   [spec-030][spec-030] ("`effective_connection_order`,
   `deterministic_order`, and `ends_in_unique_column`, the ordering
   rule plan time and resolve time share") + spec-033 Decision 4
   (cursor-parity invariant) / Decision 11 (the hoist).
2. **Explicit-else-default tier** —
   [querysets.py][querysets]`::applied_order` (`:333`,
   `tuple(query.order_by) or default_order(query, model)`) over
   `::default_order` (`:317`, `()` unless `query.default_ordering`,
   else `tuple(model._meta.ordering or ())`). `model._meta.ordering`
   is read at exactly one package site (`:330`, inside
   `default_order`); `model` is the caller's model, never
   `query.get_meta()`, so plan-time and resolve-time derive from one
   model read.
3. **Total-order rung** —
   [plans.py][plans]`::deterministic_order` (`:990`): the effective
   ordering with the pk appended as terminal tiebreaker unless it
   already ends unique. The tiebreak append (`(*effective,
   model._meta.pk.attname)`, `:1006`) is the only order-derivation
   `pk.attname` site; the other five `pk.attname` reads answer
   different questions (relay id-attr, scalar-projection seed, join
   parent column, walker elision, lateral pk-alias resolution).
4. **Unique-terminal predicate** —
   [plans.py][plans]`::ends_in_unique_column` (`:906`): string refs
   (`pk` / name / attname honored, `__` traversals refused),
   `OrderBy` / `F` via the shared parser, unnameable terminals
   refused; a nullable unique column is NOT total (SQL UNIQUE
   permits multiple NULLs). Single call site (`:1004`, inside
   `deterministic_order`) plus the [connection.py][connection]`:184`
   alias re-export (`_ends_in_unique_column is
   ends_in_unique_column`, pinned by identity test).

Supporting vocabulary, each one definition:

- Entry parser
  [plans.py][plans]`::order_entry_name_and_direction` (`:854`):
  one dash rule, one expression unwrap. Five composing call sites,
  all by name: `:928` (inside `ends_in_unique_column`),
  [nested-planner.py][nested-planner]`:180` (name-only shim) and
  `:268` (advisory terms), [lateral-fetch.py][lateral-fetch]`:1197`
  (column render), [connection.py][connection]`:871` (keyset ref
  parse).
- NULLS gate
  [plans.py][plans]`::order_entry_has_explicit_nulls` (`:887`):
  two composing call sites ([connection.py][connection]`:869`,
  [nested-planner.py][nested-planner]`:266`).
- Reversal [plans.py][plans]`::_reverse_order_by` (`:1262`):
  one call site (`:1175`, the backward window); mirrors Django's
  `queryset.reverse()` (string toggle, `OrderBy.reverse_ordering`
  clone, bare-expression `.desc()`), `OptimizerError` on an
  unreversible entry.
- Keyset validation pair: [types-base.py][types-base]
  `::_validate_cursor_field` (class-creation shape + Relay gate)
  and [keyset.py][keyset]`::validate_cursor_field_columns`
  (finalization column contract incl. the unique-terminal
  requirement) over the single syntax owner
  [keyset.py][keyset]`::split_order_ref` /
  `::validate_cursor_field_references`. This is what lets the
  keyset-default rung return the declared tuple unverified: the
  tiebreak is DECLARED, not appended (BACKLOG contract).

Consumers (all compose by name; none restates a rung):

| Consumer | Call | Role |
|---|---|---|
| [connection.py][connection]`::_finalize_queryset` (`:1794-1797`) | `applied_order` + `effective_connection_order`, `order_by(*ordered)` iff `ordered != applied` | resolve-time pipeline tail (steps 5-6), shared by both colors |
| [nested-planner.py][nested-planner] step (d) (`:1399`) | `effective_connection_order` | plan-time window order |
| [connection.py][connection]`::_keyset_order_state` (`:937`) | reads post-finalize `query.order_by` | keyset cursor-column resolution (the order finalize already applied) |
| [plans.py][plans]`::apply_window_pagination` (`:1142`) | applies received `order_by` | window mechanism, receives ladder output |
| [lateral-fetch.py][lateral-fetch]`::_order_columns` | parser + column render | lateral SQL render of the planned order |
| [nested-planner.py][nested-planner] projection/advisory (`_concrete_order_columns`, `_concrete_order_terms`) | parser + NULLS gate | scalar projection / index advisory readings |
| [list-field.py][list-field]`::_selected_ordering` (`:1150`) | `default_order` for the model tier | list offset-guard classification (different ladder, see R2) |
| [single-parent-fetch.py][single-parent-fetch]`:249`, [lateral-fetch.py][lateral-fetch]`:645` | order-equality vs captured spec | fetch-time plan recognition, not derivation |

Producers (write `query.order_by`; excluded, see R10): OrderSet
[orders-sets.py][orders-sets]`::_apply_orderings` (`:1013`),
consumer resolvers, the seal's pk-membership rewrite
([querysets.py][querysets]`:3621-3624`, carries combinator terms, a
different rule, see R4).

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — searched. The list field
   carries its own ordering ladder
   ([list-field.py][list-field]`::_selected_ordering`: extra >
   explicit > model-default > nothing) plus the
   `_is_deterministic_order_*` per-term classifier family. Same
   token ("deterministic order"), different contract: the list
   ladder classifies what Django will compile (extra included) to
   REFUSE an unguarded offset, while the connection ladder DERIVES
   the total order to apply (extra excluded by stated contract).
   The list ladder composes `default_order` for its model tier
   rather than re-reading `Meta.ordering`. Rejection R2 records
   the contract difference + trigger. OrderSet is the
   explicit-order producer, not a second derivation (R10).
2. **Sync/async twins** — discharged: no twin surface. Every
   ladder function is pure over a lazy `Query` / tuple (no I/O,
   no await point); both pipeline colors share the one
   color-agnostic tail
   [connection.py][connection]`::_finalize_queryset`. Compared by
   behavior: sync and async resolve-time orders are the same call.
3. **Derived rather than repeated knowledge** — searched.
   `model._meta.ordering`: exactly one code read (AST census,
   [querysets.py][querysets]`:330`). Tiebreak append: exactly one
   derivation site ([plans.py][plans]`:1006`). Direct
   `query.order_by` reads enumerated package-wide (rg census, 8
   code sites): the two ladder composers
   ([querysets.py][querysets]`:339`,
   [plans.py][plans]`:985`), the post-finalize keyset read
   ([connection.py][connection]`:937`), the list selection
   ([list-field.py][list-field]`:1148-1149`), the seal rewrite
   pair ([querysets.py][querysets]`:3550`, `:3621-3623`), the two
   fetch-recognition guards
   ([lateral-fetch.py][lateral-fetch]`:645`,
   [single-parent-fetch.py][single-parent-fetch]`:249`).
   Each answers a different question (derive / recognize /
   carry / classify); none derives a connection effective order
   except through the ladder (R7 examines the closest call).
   `default_ordering` reads: `default_order`
   ([querysets.py][querysets]`:328`), the list
   guard's exact-`True` gate
   ([list-field.py][list-field]`:1185`, a different verdict; the
   remaining `default_ordering` mention is the seal's audit
   comment). No second derivation by other means.
4. **Inverse / round-trip pairs** — searched. Entry parse
   (`order_entry_name_and_direction`) vs canonical-ref render
   ([connection.py][connection]`::_keyset_order_ref` builds
   `-name` from the parsed half — composes the parser, does not
   re-parse). Forward vs reversed window order:
   `_reverse_order_by` is the single tuple transform; the
   resolve-time keyset path uses Django's own
   `queryset.reverse()` ([connection.py][connection]`:1119`) —
   mirror-by-construction across a mechanism boundary (tuple
   transform vs queryset method), documented at the owner (R6).
   Fingerprint join (`order_fingerprint`) has one producer.
5. **Contracts restated in another medium** — classified.
   Production: the ladder. Oracles (independent, spell
   expectations literally): [test-plans.py][test-plans]
   `TestOrderEntryHasExplicitNulls` /
   `TestDeterministicOrderHoistParity` /
   `TestEffectiveConnectionOrder` / `TestReverseOrderBy` (22
   tests), [test-connection.py][test-connection] default-ordering
   trio + `ends_in_unique_column` pair (5 tests),
   [test-keyset.py][test-keyset] (55 tests, validation halves),
   [test-list-field.py][test-list-field] classifier pins (25
   tests), the live cleared-default-ordering row
   ([test-library-shapes-api.py][test-library-shapes-api]). All
   re-executed green at WT bytes (see Implementation). Contract
   source: [spec-030][spec-030] + spec-033 Decisions 4/11.
   Projections: the cursor-parity docstrings at each consumer
   (describe; never own). A contract change legitimately moves
   production + oracles together.
6. **Enforcement by omission** — enumerated, no gap. Every
   package site deriving or applying a connection order: the two
   ladder composers (finalize, planner step d), the window
   applier (`:1142`, receives ladder output), the single-parent
   re-application (`:288`, re-applies spec order), the keyset
   defensive empty-order arm (`:942`, examined in R7 — defensive
   consumer, no precedence of its own), the seal rewrite
   (carries combinator terms, R4). No member derives a
   connection effective order outside the ladder; adding a guard
   nowhere is owed, so no behavior defect is filed.

### Challenges

Each change posited on the rule's variation axes; counts are
authoritative definitions (consumers / oracles / projections
listed, not counted).

- **C1 — the tiebreaker changes** (append `pk` F-expression
  instead of the attname string, or a different tiebreak
  column): moves [plans.py][plans]`::deterministic_order`
  (`:1006`) only. Count **1**. (The five other `pk.attname`
  reads answer different questions; listed under F-ladder.)
- **C2 — the unique-terminal rule changes** (e.g. nullable
  unique columns become total): moves
  `::ends_in_unique_column` only. Count **1**. The keyset
  terminal check ([keyset.py][keyset]`:367-375`) does not move:
  its per-entry loop already rejected nullable columns, so its
  `primary_key or unique` check keeps meaning the same verdict
  (R1). The list per-term classifiers do not move: they judge
  per-term resolvability, not terminal uniqueness (R2).
- **C3 — the explicit-else-default tier changes** (e.g. honor
  `extra(order_by=)` in connections): moves
  [querysets.py][querysets]`::applied_order` only. Count
  **1**. The list `_selected_ordering` does not move: it
  already reads extra under its own contract (R2). The
  `Meta.ordering = None` / cleared-`default_ordering` arms
  move inside `default_order` only (C3b, count **1**).
- **C4 — the keyset-default rung changes** (e.g. the declared
  tuple gains a precondition beyond "no explicit order won"):
  moves `::effective_connection_order` (`:985-986`) only.
  Count **1**. The keyset empty-order arm
  ([connection.py][connection]`:938-942`) does not move: it
  encodes no precedence of its own (R7). The keyset
  validation pair does not move: it validates the declared
  vocabulary, not when it wins (R1).
- **C5 — the entry vocabulary changes** (e.g. a new
  parseable expression shape): moves
  `::order_entry_name_and_direction` only; all five call
  sites follow by construction. Count **1**. The keyset
  `split_order_ref` twin does not move: loud-config vs
  fallback-signal postures (R3). The seal carried-term pair
  does not move: exact-type genuineness gates (R4). The
  advisory index dash-strip does not move: config-name
  vocabulary (R5).
- **C6 — the NULLS-explicit verdict changes** (e.g. a third
  positioning flag): moves
  `::order_entry_has_explicit_nulls` only; both call sites
  follow. Count **1**.
- **C7 — backward-window reversal changes** (e.g. a new
  entry shape needing reversal): moves `::_reverse_order_by`
  only. Count **1**. The resolve-time `.reverse()` does not
  move: it is Django's own method (R6).
- **C8 — the declared-vocabulary syntax changes** (e.g. allow
  relation traversal in `cursor_field`): moves
  [keyset.py][keyset]`::split_order_ref` /
  `::validate_cursor_field_references` only; both validation
  stages follow. Count **1**.

Every challenge counts 1. No experiment beyond the census
and the re-executed oracles was needed: the mechanism is
pure derivation with named composition at every site, and
the counts are structural (single `def` + by-name calls),
not behavioral.

## Findings

### F-ladder — the connection-order ladder (CONFIRM, single-owned, zero-edit)

- **Contract + variation.** A connection paginates under a
  deterministic TOTAL order: the keyset target's declared
  `cursor_field` when no explicit order won, else the
  explicit `orderBy:` or model `Meta.ordering` (while default
  ordering stands), with the pk appended as terminal
  tiebreaker unless the order already ends in a unique
  column. Varies on: declared vocabulary (config), explicit
  input, model ordering, terminal uniqueness, NULLS
  positioning (reversal/advisory readings).
- **Sites + roles.** Definitions (each exactly one, AST
  census over 121 files): `effective_connection_order`,
  `deterministic_order`, `ends_in_unique_column`,
  `order_entry_name_and_direction`,
  `order_entry_has_explicit_nulls`, `_reverse_order_by` (all
  [plans.py][plans]); `applied_order`, `default_order` (both
  [querysets.py][querysets]). Consumers: resolve-time
  `_finalize_queryset`, plan-time planner step (d), keyset
  cursor resolution, window application, lateral render,
  projection/advisory readings, list model-tier read (table
  in System trace). Oracles: the 22 + 5 + 55 + 25 + 1 tests
  above. Projections: cursor-parity docstrings, spec-030 /
  spec-033 text. Excluded with contract differences: R1-R11.
- **Challenges.** C1-C8, every count 1.
- **Owner + lifetime.** [plans.py][plans] owns the ladder
  (precedence + totality + vocabulary + reversal); the
  explicit-else-default tier lives in
  [querysets.py][querysets] beside the other `Query`-state
  reads it generalizes (`default_order` is also the list
  field's model-tier reader — the narrowest owner every
  legitimate consumer can import). Pure derivation, not
  cached: no lifetime fields. Ownership reasoning: the
  cursor-parity invariant (plan-time window order and
  resolve-time pipeline order must agree) forces one
  precedence body shared by the planner and the pipeline;
  spec-033 Decision 11 sites the hoist at plans.py, and the
  nomination's candidacy is confirmed on the dependency
  direction (both consumers already import plans.py; the
  tier helpers sit one layer down where the list field can
  also reach them without importing the optimizer).
- **Migration.** None: every consumer already composes by
  name. Zero-edit.
- **Distinct behavior.** The keyset validation pair keeps
  its loud-config terminal check (R1); the list ladder
  keeps its extra-aware classify-and-refuse posture (R2);
  the seal keeps its exact-type carried-term gates (R4);
  resolve-time reversal stays Django's `.reverse()` (R6).
- **Behavioral proof.** `execution-verified`: the 22-test
  ladder subset, the 5-test connection pins, the 55-test
  keyset file, the 25-test list classifier pins, and the 1
  live cleared-default-ordering row all re-executed green
  at WT bytes in the item copy (run ids + results in
  Implementation). Each oracle rejects a diverged order
  (wrong tiebreak, dropped `Meta.ordering`, mis-parsed
  entry, unreversed window) — they pin the composition,
  not just the bodies.
- **Structural gate.** None added, deliberately: the bypass
  population ("a site deriving a connection effective
  order") is semantic, not syntactic. Every syntactic proxy
  has many legitimate members with distinct contracts
  (`query.order_by` reads: 8 sites / 6 contracts;
  `order_by(*` applications: 6 sites / 5 contracts;
  `pk.attname` reads: 6 sites / 6 contracts), so a census
  gate would need a brittle cross-owner allowlist, and a
  per-helper existence test is forbidden. The behavioral
  oracles pin every rung at package + live tiers, and the
  `is`-identity test pins the alias. A future inline
  derivation with a DIVERGENT order fails the oracles; a
  byte-correct hand copy is the residual DRY.md accepts
  when no justified gate exists.
- **Coupling.** None: zero-edit, no dependency introduced.
- **Freshness.** Package fingerprints in System trace (all
  BASE == WT). Oracles: [test-plans.py][test-plans]
  `fe606e15` (clean), [test-connection.py][test-connection]
  WT/BASE `da8ac393` vs HEAD `60a2088e` (concurrent dirt
  outside the pinned tests), [test-keyset.py][test-keyset]
  `b1624f47` (clean), [test-list-field.py][test-list-field]
  WT/BASE `499bae42` vs HEAD `5401e7e8`, live row file
  `bad9ef33` (clean). Contract source [spec-030][spec-030]
  `295f9cfb` (clean). Searched populations: 121 package
  files (AST census), `query.order_by` / `order_by(` /
  `default_ordering` / `Meta.ordering` / `cursor_field` /
  `reverse` rg sweeps. Excluded modules on body strength:
  [queryset-private.py][queryset-private] (no ordering
  symbol), [utils-connections.py][utils-connections] (no
  order derivation), [orders-sets.py][orders-sets]
  (producer), [types-base.py][types-base] except
  `_validate_cursor_field`, [single-parent-fetch.py][single-parent-fetch]
  (recognition only).

### R1 — keyset terminal validation stays at finalization (REJECT merge)

[keyset.py][keyset]`::validate_cursor_field_columns` (`:324-375`)
checks the declared terminal is `primary_key or unique` — beside
`ends_in_unique_column`'s fuller verdict (nullable-unique refused,
`__` refused, unnameable refused). Contract difference: the
keyset check is CONFIGURATION validation (loud
`ConfigurationError` naming the entry + remediation, at
finalization, over entries its own loop already proved local
concrete non-nullable — so `unique` already means
unique-and-non-null there), while the ladder predicate is a
RUNTIME fallback signal (boolean, over arbitrary effective
orders). Composing the predicate would trade an exact local
check for a general one with five dead arms and couple the
leaf keyset module to the optimizer (dependency direction).
Durable home: the keyset docstrings already state the v1
column contract; no new prose owed. Trigger: the v1 column
contract dropping a per-entry precondition (e.g. nullable
columns admitted) — then the terminal check must re-derive
nullability and the merge question reopens.

### R2 — the list-field ladder is a different rule (REJECT merge)

[list-field.py][list-field]`::_selected_ordering` (extra >
explicit > model-default > nothing) plus the
`_is_deterministic_order_*` per-term classifiers share the
"deterministic order" token only. Contract differences: (a)
the list ladder classifies what Django will compile
INCLUDING `extra(order_by=)` to refuse an unguarded offset;
the connection ladder derives the order to apply EXCLUDING
extra by stated contract (both docstrings state the split);
(b) the list field never appends a tiebreaker — it raises;
(c) the classifiers judge per-term resolvability (relation
defaults, annotation refs, transform chains, cycle refusal),
not terminal uniqueness. The shared sub-rule (model-tier
read) already composes `default_order` by name. Trigger: a
consumer needing one "effective order of a queryset"
definition for both refuse-posture and apply-posture — then
the extra-inclusion split is the design question.

### R3 — `split_order_ref` is a documented intentional twin (REJECT merge)

[keyset.py][keyset]`::split_order_ref` re-spells the parser's
string branch with loud `ConfigurationError`s. The twin is
load-bearing: a malformed declared entry is a configuration
error, never a fallback signal, and the syntax owner serves
both validation stages identically. Merging would force one
posture on two contracts. Trigger: the declared vocabulary
admitting a shape the runtime parser rejects (or vice
versa) — then the two syntaxes genuinely differ and the
twin is two rules, not one.

### R4 — the seal carried-term pair keeps its genuineness gates (REJECT merge)

[querysets.py][querysets]`::_is_carried_order_term` /
`::_rewrite_order_term` re-spell dash handling and F/OrderBy
unwrap with EXACT-type gates (`type(entry) is OrderBy`) and
a "can the single-table rewrite carry this term" verdict
plus attname re-spelling (a combinator orders `"shelf"` by
the column; a plain queryset would expand `Meta.ordering`).
Contract difference: the seal pair proves rewritability
under the sealed-execution posture; the ladder parser
resolves names and lets each caller decide. Trigger: the
rewrite admitting a term class the parser cannot name —
then the vocabularies diverge further, never merge.

### R5 — the advisory index dash-strip is config vocabulary (REJECT merge)

[nested-planner.py][nested-planner]`::_index_leading_terms`
(`:360-363`) strips `-` over `Meta.indexes` field-name
strings under an exact-B-tree gate. Different vocabulary
(config names, never annotations/expressions/`pk`), different
failure posture (`FieldDoesNotExist` → UNKNOWN, fail-soft).
Sharing the runtime parser would couple index inspection to
the order-entry vocabulary. Trigger: `Meta.indexes` entries
admitting expression shapes — then the parser question
reopens (expressions already route to UNKNOWN today).

### R6 — resolve-time reversal stays Django's `.reverse()` (REJECT merge)

`_reverse_order_by` (tuple → tuple, plan-time) mirrors
Django's `queryset.reverse()` (queryset → queryset,
resolve-time keyset path). Mirror-by-construction across a
mechanism boundary: the window needs the reversed ORDER as
data (to render `_dst_row_number_reversed`), while the
resolve-time path needs a reversed queryset. One body
cannot serve both shapes. Documented at the owner.
Trigger: Django changing reversal semantics for an entry
shape — then the mirror must be re-pinned (an upstream
migration, legitimately multi-site).

### R7 — the keyset empty-order arm is a defensive consumer (REJECT definition)

[connection.py][connection]`::_keyset_order_state` (`:937-947`)
reads post-finalize `query.order_by` and, when empty,
applies the declared `state.cursor_field`. Closest call to
a second definition of the keyset-default rung — examined
and excluded: (a) every in-package path passes finalize
first (`fallback()` re-runs `_pipeline_sync`), so the arm
fires only for direct external calls or the
applied==ordered==cursor_field degenerate case, and in
both cases the applied order EQUALS the ladder's answer;
(b) the arm encodes no precedence of its own — it reuses
the declared tuple as the cursor VOCABULARY (columns +
fingerprint must be the declared ones for mint/decode
parity), while the WHEN (no explicit order won) lives
once in `effective_connection_order`. Coherent changes
(precedence condition, declared tuple) move one site;
the "change what the default IS while keeping the
vocabulary" change is incoherent (breaks byte-parity).
Trigger: the arm gaining its own precedence condition —
then it becomes a second definition.

### R8 — `pk`-alias spellings answer different questions (REJECT merge)

The `pk` alias is honored in four shapes: uniqueness
verdict ([plans.py][plans]`:937`), attname resolution
([lateral-fetch.py][lateral-fetch]`:1203-1204`, field
object in [keyset.py][keyset]`:248-249` and
[connection.py][connection]`:892`), and projection skip
([nested-planner.py][nested-planner]`::_concrete_order_columns`,
which skips `pk` — harmless: the scalar projection always
seeds the pk attname first, `:744`). Same token, four
questions; no one plausible change moves two (C1/C2 move
one each). Trigger: a fifth client needing the same
(pk-alias → attname) answer as the lateral renderer —
then that pair shares a helper.

### R9 — `capture_applied_order_normalization` is a token collision (REJECT)

[orders-sets.py][orders-sets]`::capture_applied_order_normalization`
is the OrderSet input-normalization recording ledger
(test-observation scope), not a queryset ORDER BY
derivation. Same words, disjoint rule. No trigger: the
names collide by language, never by contract.

### R10 — producers and appliers are not derivations (REJECT)

OrderSet `_apply_orderings`
([orders-sets.py][orders-sets]`:1013`), the window applier
([plans.py][plans]`:1142`), the single-parent re-application
([single-parent-fetch.py][single-parent-fetch]`:288`), and
the fetch-recognition equality guards (System trace table)
write or compare orders; none derives an effective order.
A change to what the effective order IS moves the ladder;
these sites follow their inputs. No trigger short of one
of them growing its own derivation.

### R11 — the Django dash contract is upstream-shared (REJECT shared helper)

"One leading `-` = descending" is Django's `order_by`
contract, restated per site in per-site vocabulary with
load-bearing per-site postures (None-signal, UNKNOWN,
loud-config, exact-type). A shared strip helper would
couple the seal, the advisory, keyset config, and the
ladder across independent failure postures — machinery,
not consolidation. Trigger: Django changing its dash
contract — an upstream migration, legitimately multi-site.

## Defects

None found. Two examined-and-cleared notes (not defects,
recorded so no cycle re-litigates):

- [nested-planner.py][nested-planner]`::_concrete_order_columns`
  skips a literal `"pk"` term (matches name/attname only).
  Harmless by construction: the scalar-only projection
  always seeds `related_model._meta.pk.attname` first
  (`:744`), so no window under-projects. No behavior gap,
  no card owed.
- The WT `truth.static_attr(model, "_meta")` read inside
  `ends_in_unique_column` ([plans.py][plans]`:932-935`) and
  the `_finalize_queryset` / `_keyset_order_ref` guard
  removals ([connection.py][connection] hunks at `:852` /
  `:1781` HEAD) are concurrent hunt work on ladder-adjacent
  lines. Untouched per the concurrent-work rule; a future
  consolidation touching those lines must re-attribute
  first. Not defects in the ladder's contract.

## Pending execution

Empty: every behavioral proof above is `execution-verified`
at WT bytes (run ids in Implementation). No `proof:`
entries remain. No `gate:` entries: the sharded and pg
cells are inapplicable by construction — every ladder
function is pure derivation over a lazy `Query` / tuple
(no database hit, no alias read, no dialect decision;
`meta.get_field` / `_meta` reads touch model metadata
only), so no cell-specific behavior exists to verify.
Worker-2 judges the claim.

Executed proof commands (evidence, not pending):

- `uv run python scripts/workspace.py run
  dry/connorder-f58/consolidate -- pytest
  tests/optimizer/test_plans.py -n0 --no-cov -q -k
  "TestOrderEntryHasExplicitNulls or
  TestDeterministicOrderHoistParity or
  TestEffectiveConnectionOrder or TestReverseOrderBy"`
  → 22 passed (`dry-20261009T190239-0bee7e`)
- `... -- pytest tests/test_connection.py -n0 --no-cov -q
  -k "test_default_ordering_applied_when_unordered or
  test_default_ordering_preserves_supplied_orderby or
  test_default_ordering_preserves_meta_ordering or
  test_ends_in_unique_column"` → 5 passed
  (`dry-20261009T190245-0e2093`)
- `... -- pytest tests/test_keyset.py -n0 --no-cov -q` →
  55 passed (`dry-20261009T190300-24b860`)
- `... -- pytest tests/test_list_field.py -n0 --no-cov -q
  -k "order_term_classifier or order_reference_classifier
  or order_predicate_classifier or
  is_model_default_ordering_active or has_deterministic"`
  → 23 passed (`dry-20261009T190335-8abca3`; plus an
  earlier 2-test name-matched subset green,
  `dry-20261009T190315-bb2e0e`)
- `... -- pytest
  examples/fakeshop/test_query/test_library_shapes_api.py::test_reading_lists_connection_honors_a_cleared_default_ordering
  -n0 --no-cov -q` → 1 passed
  (`dry-20261009T190347-a62027`)

## Judgment

CONFIRM. The connection-order ladder is one rule with one
owner per rung and every consumer composing by name: the
precedence composer (`effective_connection_order`), the
explicit-else-default tier (`applied_order` /
`default_order`), the total-order rung
(`deterministic_order`), the unique-terminal predicate
(`ends_in_unique_column`), the entry vocabulary (parser +
NULLS gate), and the reversal (`_reverse_order_by`) each
have exactly one definition (AST census, 121 files), and
all eight change challenges count 1. The lookalikes
(keyset validation, list ladder, seal rewrite, advisory
reads, fetch guards, producers) are distinct contracts
with recorded differences + triggers (R1-R11). Zero-edit:
no consolidation exists to implement, and no structural
gate is justified (the bypass population is semantic; a
syntactic census would couple unrelated owners).

## Implementation (Worker-1)

No tracked changes made: the item-scoped diff vs
`ITEM_BASELINE=83a1c0c8901bc229239e82bae203b6a01d5ce13c`
over package/tests/examples is empty (verified after the
last proof run; all fingerprints in System trace still
read BASE == WT). No production edit, no test edit, no
orphan sweep owed, no ruff run owed (no `.py` touched).
`check_public_types.py` not required (no public symbol
touched). Single new file: this artifact (untracked,
per-cycle scratch).

Type gates, all in the item copy
(`dry/connorder-f58/consolidate`, slot-2, fresh, shared
tree unmoved at every run), all through `heavy`:

- `... -- basedpyright` → 0 errors, 0 warnings, 0 notes
  (`dry-20261009T190407-b5a5a2`)
- `... -- basedpyright -p pyrightconfig.floor.json` → 0
  errors, 0 warnings, 0 notes
  (`dry-20261009T190519-da2cd7`)
- `... -- python scripts/check_truthful_reads.py --check`
  → 120 files, 0 errors (`dry-20261009T190632-811029`)

`check_any.py` / `ALLOWED_ANY` neither run nor cited
(gone). No cast, widening, or suppression added. Machine:
`pressure` GREEN at start (10.1 GiB free); every pytest /
basedpyright / workspace run through `heavy`; focused
`-n0` single files only; scratch confined to the
workspace copy; `TMPDIR` / `DSF_WS_ROOT` untouched.

## Independent verification (Worker-2)

Own trace frozen BEFORE reading `## Findings` (full text at
`~/dry/tmp/w2-f58-independent-trace-prefindings.md`,
written 2026-10-09T19:14Z; artifact first opened afterwards).

### My trace (pre-findings)

One owner per rung, every consumer composing by name: `default_order`
/ `applied_order` (`utils/querysets.py`, the explicit-else-default
tier); `ends_in_unique_column` / `deterministic_order` /
`effective_connection_order` (`optimizer/plans.py`, terminal
predicate / tiebreak / precedence); `order_entry_name_and_direction`
/ `order_entry_has_explicit_nulls` (entry vocabulary);
`_reverse_order_by` (tuple reversal mirroring Django's
`queryset.reverse()` upstream oracle). Consumers: `_finalize_queryset`
(resolve-time, both colors), planner step (d) (plan-time),
`_keyset_order_ref` / `_keyset_order_state`, `_order_entry_field_name`
/ `_concrete_order_columns` / `_concrete_order_terms`,
lateral `_order_columns`, `_selected_ordering` (model tier),
`spec.order_by` appliers. Aliases (not definitions): connection
`_ends_in_unique_column`, walker re-exports. Producer (not a
competing derivation): OrderSet `apply_*`.

My eight challenges, every count 1: tier-default semantics
(`default_order`), effective-terms meaning (`applied_order`),
terminal uniqueness (`ends_in_unique_column`; keyset terminal check
excluded — non-null pre-guaranteed), tiebreak column
(`deterministic_order`), keyset-vs-explicit precedence
(`effective_connection_order`), dash vocabulary
(`order_entry_name_and_direction`; loud twin + flip/re-spell/index
readers different ops/domains), NULLS verdict
(`order_entry_has_explicit_nulls`), reversal (`_reverse_order_by`;
Django `.reverse()` the upstream oracle). Owner I would choose:
keep every rung where it is (query tier lowest in
`utils/querysets.py`, ladder in `optimizer/plans.py`, loud config
vocabulary in `keyset.py`, determinism classification in
`list_field.py`). Zero-edit CONFIRM, pending reconciliation.

### Reconciliation (every difference)

- Grouping: my R-c (determinism classifiers) + R-d
  (`_selected_ordering` source check) = W1 R2 folded. Same
  sites, same contract differences. No divergence.
- My R-k (projection/advisory sibling split,
  `_concrete_order_columns` vs `_concrete_order_terms`): W1
  lists the pair as consumers with no R. Concur on
  reflection — the split is within one consumer, no ladder
  rung is duplicated, both already compose the shared
  parser; no R owed. Treatment differs, verdict identical.
- W1 R7 (keyset empty-order arm) exceeds my trace (I had it
  as consumer/state-check). Endorsed: verified the fallback
  closure re-runs `_pipeline_sync` (`connection.py:324`)
  which ends in `_finalize_queryset`, and the arm's output
  equals the ladder's answer in every case (including the
  applied==ordered==cursor_field degenerate case). The
  trigger (arm gaining its own precedence) is the right
  tripwire.
- W1 R8 (pk-alias shapes) exceeds my trace. Endorsed, with
  a census completion (Correction 3b — inside R2/R4
  families, trigger unaffected).
- W1 R11 (dash-contract umbrella) matches my C6 analysis.
  Endorsed.
- Remaining map: my R-a = R3, R-b = R1, R-e = R4 (verified
  the exact-type gates at `querysets.py:3478-3481`), R-f =
  R5, R-h = R9, R-i = matrix axis 4 discharge, R-j =
  freshness exclusion, R-l = R6 + contract sources. No
  unmatched candidate on either side: every lookalike I
  found independently appears in W1's record, and every
  W1-cited site exists at the cited bytes with the cited
  contract.

### Confirmations (re-derived)

- Zero-edit: item diff vs `83a1c0c89...` empty over the 4
  indexed paths and over package/tests/examples alike;
  only `docs/dry/dry-0_0_15.md` (W0-owned plan) differs;
  no new `.py` (untracked `.py` = attributed concurrent
  work). All dispatch WT/HEAD pins match; BASE == WT.
- 121 package `.py` files; each ladder/keyset `def`
  occurs exactly once (9/9). Parser: exactly 5 code call
  sites (`plans.py:928`, `nested_planner.py:180` + `:268`,
  `lateral_fetch.py:1197`, `connection.py:871`). NULLS
  gate: exactly 2 (`nested_planner.py:266`,
  `connection.py:869`). `_reverse_order_by`: one call site
  (`plans.py:1175`).
- `query.order_by` reads: exactly the 8 W1 enumerates
  (each verified: derive / recognize / carry / classify —
  no second effective-order derivation).
  `order_by(*` applications: 6 (all write/compare, none
  derive). `*.pk.attname`: 6 (`plans.py:1006` + the five
  W1 names, roles match). `default_ordering`: 2 code reads
  (`querysets.py:328`, `list_field.py:1185`, different
  verdicts).
- Dirt attribution verified by content: plans exactly 3
  hunt hunks; connection guard-removal hunks (HEAD `:852`,
  `:1781`) leave ladder call lines verbatim; querysets
  `:317-339` clean (changed-line accounting `:309`/`:403`
  confirmed); nested step (d) clean.
- Oracles: literal expectations throughout (HoistParity /
  Effective / Nulls / Reverse classes + connection pins
  read in full); package-wide circular-oracle scan (owner
  on both sides of `==`) empty; the `is`-identity test
  pins the alias beside literal behavioral pins. Nothing
  rewritten at all, so no oracle was rewritten to read
  from its owner.
- Matrix: all six axes discharged against the real
  surface (axis 2: both colors share `_finalize_queryset`
  at `:1953`/`:2016`; axis 6: every applier enumerated,
  R7 arm examined, no gap, no defect owed). No structural
  gate justified — concur (semantic bypass population,
  measured syntactic proxies, behavioral oracles at
  package + live tiers pin every rung).
- Pending execution: empty, confirmed — every proof
  below re-executed green in MY copy; no `proof:`/`gate:`
  entry owed.

### Proof + gate re-runs (Worker-2 copy)

All at `dry/connorder-f58/verify-1` (slot-3, fresh, shared
tree unmoved at every run), through `heavy`, `-n0`:

- ladder 22: 22 passed (`dry-20261009T191907-3f5dd5`)
- connection 5: 5 passed (`dry-20261009T191917-fcc2ee`)
- keyset file: 55 passed
  (`dry-20261009T191933-741875`; confirms 52 defs → 55
  cases via parametrize)
- list classifier pins: 23 passed
  (`dry-20261009T191945-1aa1a0`; see Correction 1)
- live cleared-ordering row: 1 passed
  (`dry-20261009T192138-bb6f22`)
- `basedpyright`: 0 errors, 0 warnings, 0 notes
  (`dry-20261009T192155-780a98`)
- `basedpyright -p pyrightconfig.floor.json`: 0/0/0
  (`dry-20261009T192308-6ddb8d`)
- `check_truthful_reads.py --check`: 120 files,
  0 errors (`dry-20261009T192422-b778eb`)

`check_any.py` neither run nor cited (gone). `pressure`
GREEN at start; no heavy job contended.

### Sharded/pg judgment: inapplicable-by-construction SUSTAINED

Every ladder + lookalike body is pure derivation over a
lazy `Query`, an order tuple, or model `_meta`: no
`.db`/`using`/router read, no dialect branch, no DB I/O
(verified per body, including the WT hunt-touched `_meta`
read — metadata only). NULLS placement varies by backend
at execution, but the ladder only detects explicitness (a
backend-independent AST property) and appends pk. The one
backend-sensitive neighbor (the advisory's backend gate)
is advisory-only, fail-soft, and not a ladder rung. The
SQLite-run oracles fully determine ladder behavior.

### Corrections (Worker-2; verdict-neutral)

No finding, definition count, trigger, or gate changes.
Recorded so Outcomes carries true figures:

1. List-pin oracle count is 23 distinct, not 25. W1's
   "23 + 2" double-counts: the earlier run's `-k`
   (`deterministic_order or default_ordering`,
   `dry-20261009T190315-bb2e0e`) selected exactly
   `tests/test_list_field.py:1887` + `:2013` (zero defs
   contain `deterministic_order`, no class matches, and
   selection was exactly 2), and both defs contain
   `is_model_default_ordering_active`, so both are inside
   the main 23. Both runs green; every
   classifier-exercising test (all 10 classifier defs +
   both ordering-active defs) lies within the 23 — no pin
   missing, only the sum wrong. Carry 23 in: matrix axis
   5, F-ladder sites ("22 + 5 + 55 + 23 + 1"), F-ladder
   proof. Worker-0: Outcomes records 23.
2. Matrix axis 3's "(the remaining `default_ordering`
   mention is the seal's audit comment)" is phantom — no
   such mention exists package-wide (census: 2 code reads
   + docstrings + def name + one call). Census substance
   correct; pointer only.
3. Two census completions, both inside already-rejected
   families: (a) the `_meta.ordering` census misses the
   two `related_opts.ordering` reads (`list_field.py:773`,
   `:785`) — R2 members reading a different (related)
   model for a different verdict, correctly unmerged;
   (b) R8's "four pk-alias shapes" misses
   `list_field.py:775` (`path == "pk"` expansion guard,
   R2) and `querysets.py:3458` (`_is_model_column` "pk"
   arm, R4). Neither can merge with the ladder
   (different rules, triggers already recorded).

### Prose + touched-path gates

Item diff empty → no code/prose rule engaged. Ruff
`format --check` + `check` touched-path set: EMPTY (no
`.py` touched; a repo-wide run would measure concurrent
dirt, not this item). Artifact `.md` excluded from
source-layout rules by policy (checker: 0 violations).
No package defect found; no `## Defects` entry owed.

Verdict: verified (plain — no `proof:` entry remains).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[keyset]: ../../django_strawberry_framework/keyset.py
[lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[list-field]: ../../django_strawberry_framework/list_field.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[queryset-private]: ../../django_strawberry_framework/utils/_queryset_private.py
[single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[types-base]: ../../django_strawberry_framework/types/base.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py

<!-- tests/ -->
[test-connection]: ../../tests/test_connection.py
[test-keyset]: ../../tests/test_keyset.py
[test-list-field]: ../../tests/test_list_field.py
[test-plans]: ../../tests/optimizer/test_plans.py

<!-- examples/ -->
[test-library-shapes-api]: ../../examples/fakeshop/test_query/test_library_shapes_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

