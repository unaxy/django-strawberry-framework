# DRY review: `keyset-order-state-halves`

Status: verified
Run: 0.0.15 2026-10-12-22

## System trace

One definition-keyed vocabulary plus one query-time resolver, each with
by-name consumers; no second derivation in the package. Declared side:
`keyset.py:297` `declared_cursor_state_for_definition`, 1 definition, 2
production calls (`connection.py:1485`, `nested_planner.py:1230`); every
consumer threads the SAME object (`_keyset_connection_context` ->
slicer `:817-824` + window `:748-749`; planner `keyset_context.columns`
/ `.fingerprint` -> `_keyset_window_slice_from_arguments`
`nested_planner.py:1037-1042`). Resolver side: `_keyset_order_state`
(`connection.py:910`) — fast path RETURNS `state.columns` /
`state.fingerprint` (`:937-946`, reuse not restatement), orderBy branch
derives per-order columns (`:947-1001`, one `order_fingerprint` call);
one call feeds BOTH halves: decode x2 (`:1090`, `:1099`) + encode
(`:1161`). Census: `order_fingerprint` 1+2, `CursorColumn` 1 record + 2
constructors, `KeysetSeek` 1+3, `keyset_contract_error` 1+6,
`_dst_cursor_value_` 1 site, `_extend_only_projection` 1+3. No
`KeysetState` symbol exists; the axis-3/4 question was re-derived from
zero. Zero production edits; the `keyset.py` contract-error docstring
present-tense reword is uncommitted unledgered foreign dirt (HEAD text
is past-tense history) left untouched.

## Verification

### Matrix

1. Cross-flavor: keyset is connection-only; no second derivation in
filters/orders/forms/rest. 2. Sync/async: pure reads, no I/O; both
pipelines share resolver + codec, no twin. 3. Derived twice: declared
once per definition, effective once per resolve, nested threads, fast
path reuses; pk inline converges (R6). 4. Round-trip: one
`(columns, fingerprint)` per resolve feeds encode + decode; payload +
fingerprint single-owned. 5. Other media: spec corpus + BACKLOG
describe, oracles pin both halves incl. live tier — projections. 6.
Omission: missing terminal-unique check / nested orderBy derivation are
by contract (ladder guarantees; sidecar gates refuse). No guard gap.

### Challenges

- C1 (fingerprint grammar change): 1 definition; 2 call sites follow.
Count 1. - C2 (new orderBy shape): 1 definition (`_keyset_order_state`
+ `_keyset_order_ref`); declared path untouched. Count 1. - C3
(nullable policy): declared (ConfigurationError) and query-time
(GraphQLError) move independently; each counts 1. Two contracts. - C4
(`CursorColumn` gains a field): 2 constructors, distinct contracts
(merging is R5, rejected). Record shape counts 1.

### Proofs

- `execution-verified`: `heavy uv run pytest
tests/test_keyset_connection.py tests/test_keyset.py --no-cov -q -n0`
-> 81 passed (default-reuse, 6 guard rejections, order-ref/path arms,
window-slice arms, codec round-trips).
- `static-reviewed`: live `test_keyset_api.py:437` + `:491` (single-run
authorization spent on the focused package scope; CI owns live).

## Findings

### R1: query-time guards x declared validation — two contracts

Finalization (`validate_cursor_field_columns`, ConfigurationError,
local-only declared strings) vs query time (`_keyset_order_state` arms,
GraphQLError, effective entries incl. related paths). Trigger: one error
vocabulary + one timing for both populations.

### R2: `_keyset_order_ref` x `split_order_ref` — two contracts

None-vocabulary parser over effective entries (strings + OrderBy/F,
explicit-nulls refusal) vs raising parser over declared strings
(local-only). C2 moves only the former. Trigger: declared entries admit
expressions, or effective entries go strings-only.

### R3: nested context x top-level state — one derivation

Same producer, different definition inputs (child vs root); nested never
derives orderBy columns. Trigger: nested deriving columns from anything
but `declared_cursor_state_for_definition`.

### R4: windowed mint x slicer mint — one vocabulary

`_resolve_from_window` mints from `keyset_state` direct because windows
are provably sidecar-free (plan gate `nested_planner.py:1031` + resolve
gate `connection.py:2324-2330`); slicer fast path returns the identical
objects. Trigger: a windowed resolve carrying orderBy.

### R5: twin `CursorColumn` constructors — one record, two producers

`cursor_columns_for` (validated entries, attname sources) vs
`_keyset_order_state` (effective entries, annotation sources). Merging
couples finalization errors to per-resolve GraphQL errors. Trigger: the
vocabularies unify.

### R6: pk-name inline — converge on run-21 item-D rejection

`connection.py:891` is item-D's field-answer pair; T1-T5 re-checked at
current bytes, all unfired (census still 4, owner still FIELD+raise,
spelling undrifted).

### R7: projection call sites — converge on consolidated owner

3 calls consume `_extend_only_projection` (sibling run-9 counted 4; HEAD
and WT agree on 3 — committed drift). Sibling R9 trigger unfired.

### R8: keyset window-slice twin — converge on f19

Owned keyset fork of the offset adapter (bounds via
`derive_keyset_window_bounds`, decode via canonical codec); bodies fork
at the cursor vocabulary by design.

### Freshness

HEAD `c37a08a0`, ITEM_BASELINE `c3bc1484`; blobs connection `29252be7`,
keyset `b3f1b48a`, nested_planner `9f99edfe`, relations `b0cc6c33`,
predicates `9e7d80d1`, plans `c5e7c5f6`, utils/connections `2313fce5`,
tests `0bca5629` / `180c76e3`, live `5bd9347a`. Population: whole
package (mechanism patterns + `== "pk"` census). Contract sources:
owner docstrings,
run-21 item-C1/D1 verdicts, sibling f19 + projection verdicts.

## Defects

None.

## Pending execution

None.

## Judgment

One derivation with consumers (declared vocabulary: 1 producer, 2 call
sites, threaded objects) beside one query-time resolver for a second
contract (effective order, GraphQLError, per-resolve); encode and decode
share one `(columns, fingerprint)` per resolve by construction.
Zero-edit: no plausible change moves 2 definitions carrying real logic.

## What shrinks

Net package change over ITEM_BASELINE: zero lines (rejection of all
eight candidate compositions). What was counted and where it stays:

- Declared vocabulary: `declared_cursor_state_for_definition`
(`keyset.py:297-322`) derives `columns` via `cursor_columns_for` +
`fingerprint` via `order_fingerprint` once per definition; 2 production
calls (`connection.py:1485`, `nested_planner.py:1230`); consumers
`_keyset_connection_context`, `_keyset_order_state`,
`_resolve_keyset_connection`, `_consume_window`, `_resolve_from_window`,
`_divergent_key_windows`, `_keyset_window_slice_from_arguments` — all
thread, none re-derive.
- Effective-order state: `_keyset_order_state` (`connection.py:910-1001`):
fast path returns declared objects (`:937-946`); orderBy branch parses
(`_keyset_order_ref`, composing `order_entry_name_and_direction` +
`order_entry_has_explicit_nulls` by name), resolves
(`_resolve_order_path_field`), guards (visible-path / nullable / JSON /
column — 4 `keyset_contract_error` arms), annotates related values
(`_dst_cursor_value_{index}`, 1 site), extends the only-projection
(projection-family owner), fingerprints once. Feeds decode x2 + encode.
- No terminal-unique arm at query time is load-bearing omission, not a
gap: `effective_connection_order` (`plans.py:1118`) returns the declared
field (finalization-validated unique terminal) or `deterministic_order`
(pk tiebreaker unless `ends_in_unique_column`); `_finalize_queryset`
(`connection.py:1759`) applies it before the slicer runs. The
`connection.py:183` compat alias keeps serving live
`tests/test_connection.py:81` + `tests/optimizer/test_plans.py:1152`
pins — not dead, not touched.
- `keyset_contract_error` arms: 6 production calls (encode NULL
`keyset.py:539`; order-state x4; slicer non-queryset
`connection.py:1077`) across two modules. HEAD docstring past-tense
history ("was re-typed at five") stands as written; the present-tense
"Five sites share" reword is uncommitted unledgered worktree dirt,
outside this item's fence, left untouched.
- Guard twin table: nullable (finalization ConfigurationError vs query
GraphQLError vs encode NULL arm — three enforcement points, one policy
each, distinct timing); JSON (`_is_supported_cursor_field` single
predicate, 2 calls: `keyset.py:361`, `connection.py:976`); visible
(`visible_value_path` single owner `predicates.py:446`, 1 consumer);
related (`_resolve_order_path_field`, pk inline converges on item-D);
aggregate/expression/explicit-nulls (`_keyset_order_ref`
None-vocabulary, 1 consumer).
- Oracle inventory (all pre-existing, zero added, zero rewritten):
`tests/test_keyset_connection.py` (23 nodes: context x3, vocabulary x2,
window fallback x2, default-reuse, 6 guard rejections, order-ref parse,
path-field arms + MTI, window-slice arms, projection arms);
`tests/test_keyset.py` codec/seek round-trips (58 nodes); live
`test_keyset_api.py:437` (order-fingerprinted mint under orderBy) +
`:491` (non-disclosure). The `fingerprint == order_fingerprint(...)`
unit assertions pin half-sharing (wiring), not spelling — composing the
owner is correct there; a grammar change is behavior-preserving by
design, and mismatch-rejection is pinned behaviorally live.
- Index row for Worker-0: `keyset-order-state-halves`, owners
`keyset.py::declared_cursor_state_for_definition` +
`connection.py::_keyset_order_state` (two-contract family),
files connection/keyset/nested_planner + relations/predicates/plans +
utils/connections consumers, `rejected` (R1-R8 with triggers above).

## Independent verification (Worker-2)

Pass 1, `dry/keyset-order-state-halves/verify-1`, detached HEAD
`c37a08a0`, ITEM_BASELINE `c3bc1484`. Pre-read trace below was
recorded after reading System trace + Verification but BEFORE
opening `## Findings`; every count re-derived with own greps at WT
bytes. Zero-edit concurred pre-read: item-path diff vs baseline is
empty (the only baseline diff is item-2's 3 ported files); `tests/`
+ `examples/` untouched.

Own sites + roles. Declared vocabulary, definition-keyed:
`keyset.py::declared_cursor_state_for_definition` 1 def + 2
production calls (`connection.py::_generate_connection_class`
namespace write, `nested_planner.py::plan_connection_relation`
`keyset_context`); every consumer threads the SAME object (class
slot -> slicer + window mint; planner columns/fingerprint ->
keyset window adapter). `keyset.py::order_fingerprint` 1 def + 2
calls (`:321` declared, `connection.py:1001` orderBy branch).
`keyset.py::CursorColumn` 1 record + 2 constructors (`:270`
declared local-only attname, `connection.py:990` effective incl.
`__` annotation aliases). `keyset.py::KeysetSeek` 1 carrier + 3
constructors (slicer after `:1096`, before/flip `:1105`, window
adapter `:962`); all renderers compose `.q()` / `.plan()`.
`keyset.py::keyset_contract_error` 1 def + 6 details (connection
x5 `:955/:964/:971/:977/:1077`, keyset `:539`); stem shared, detail
per site. `_dst_cursor_value_` 1 site (`:983-984` annotate).
`nested_planner.py::_extend_only_projection` 1 def + 3 calls
(connection `:942` fast path, `:1000` orderBy, planner `:1417`
keyset). No `KeysetState` symbol (grep x0). No second
comma-join fingerprint, no second per-index cursor annotation, no
second only/defer unpack derivation found (`deferred_loading_of`
1 def + 3 readers: `merged_projection`, `_extend_only_projection`,
lateral adapter).

Own challenges. C1 fingerprint-grammar change: 1 def moves, 2
callers pass tuples through. Count 1. C2 new orderBy shape: the
`_keyset_order_ref` + `_resolve_order_path_field` + guard cluster
moves; declared path untouched. Count 1. C3 nullable policy:
declared `ConfigurationError` (finalization, static local
columns) vs query-time `GraphQLError` (per-request, live entries
incl. expressions + `visible_value` Case) — different stages,
inputs, error vocabularies; a policy change moves both but each
carries its own logic and no shared helper can span a
finalization gate and a wire guard without a mode flag. Two
contracts, count 1 each. C4 record gains a field: 2 constructor
literals move, but each is a single expression beside
non-shared guard logic; merging them re-spells the literal with
zero shrinkage. Below bar. Terminal-unique has no query-time
check because `effective_connection_order` (shared plan/resolve
ladder) already totalizes the order the slicer reads — ladder
guarantee, not a gap. R4 sidecar-free legs re-derived: planner
refuses sidecar windows (`_divergent_key_windows` gate), the
ladder returns declared `cursor_field` when no orderBy wins, and
the window mint consumes declared columns only; the orderBy
derivation exists solely on the slicer path. Owner choice: no
consolidation; existing owners stand (keyset vocabulary/codec/
carrier, connection effective-order resolver, planner threading
+ projection, plans ladder + window render, utils/connections
bounds fork).

Reconciliation (post-read). R1 agree (my C3 split identically;
stage/input/vocabulary + trigger). R2 agree (my C2 named the same
cluster; None-vs-raising + durable prose at `split_order_ref`).
R3 agree (1+2, child-vs-root inputs). R4 agree — sidecar-free
proof airtight: plan gate `:1031-1033` refuses sidecar windows,
resolve gate `:2323-2332` refuses sidecar resolves (both read at
WT bytes), ladder answers declared `cursor_field` whenever no
orderBy wins (Meta.ordering case checked both halves). R5 agree
(contract split sound: validated-attname vs effective-annotation
producers; merge = zero shrinkage + coupled error postures; my
C4). R6 agree: T1-T5 re-checked — 4 segment spellings verbatim,
`== "pk"` 14/10 = item-D 15/11 minus the C1-consolidated twin,
owner blob `b0cc6c33` identical to item-D pin (T3 stays ruled),
owner FIELD+raise no NAME variant (T2), Django 6.1.2 via clean
uv.lock + CPython 3.14 (T4). R7 agree with nit N1 (below). R8
agree: f19 scope covers the twin + forks + kernel; WT pins
re-derived (`SliceMetadata.from_arguments` 1 call, 2
`ConnectionWindowBounds` one per fork, `derive_keyset_window_bounds`
1+2, shared sub-decisions shared). Matrix: all six discharged on
the real surface; axis-5 oracles pre-exist, none rewritten
(`tests/` + `examples/` diff empty); the `order_fingerprint`
assertions pin half-sharing wiring, mismatch pinned behaviorally
live (`:437` + `:491` verified present). Freshness: all 10 blobs
identical. Foreign dirt: docstring reword confirmed foreign vs
HEAD + unledgered, untouched. Pending execution None: concur —
proof execution-verified, no deferred entry owed.

Own consolidation hunt (zero-edit acceptance): guard twins (a
shared nullable guard needs a mode flag across
ConfigurationError/GraphQLError stages; JSON already shares its
predicate), twin constructors (shared helper = the literal),
windowed/slicer mint (already one codec; inputs differ by path
legitimacy), second fingerprint/annotation/projection derivation
(`",".join` x2 package-wide: owner + unrelated consumers header;
`_dst_cursor_value_` x1; `deferred_loading_of` 1+3). No
candidate. Bar unmet everywhere; no P11 deletion (every helper
carries readers + a named contract).

Record nits (verdict-neutral, no `## Defects` entry): N1 R7
parenthetical attaches ambiguously — the sibling's literal
"exactly 4" is the `deferred_loading_of`-caller census (HEAD
collapsed plans x2 -> 1, committed; WT confirms 3), while its
`_extend_only_projection` count was "3 calls + walker alias"
(alias removal = run-21 item-A ledgered-uncommitted deletion;
alias still at HEAD). Convergence unaffected. N2 WT
`keyset_contract_error` docstring present-tense "Five sites"
miscounts (6 call sites at HEAD and WT); HEAD past-tense reads
as true consolidation history — fix rides with the foreign
hunk's owner.

Proof re-run: `workspace.py run dry/keyset-order-state-halves/verify-1
-- pytest tests/test_keyset_connection.py tests/test_keyset.py
--no-cov -q -n0` -> 81 passed, exit 0, fresh slot-6 copy
(`dry-20261012T071500-685c41`). Ruff: zero production paths
touched — no run owed (stated, not run); trailing-comma script
excludes this file (exit 0).

Verdict: verified. No defects.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
