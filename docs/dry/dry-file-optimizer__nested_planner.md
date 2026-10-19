# DRY review: `optimizer/nested_planner.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Target `django_strawberry_framework/optimizer/nested_planner.py` is the
transactional planner for nested Relay connection selections: the walker
normalizes selections and metadata, then delegates one recognized nested
connection here. The target owns six rules — plan orchestration
(`plan_connection_relation` + result + per-key window pass + fallback
log + identity filter + node unwrap + raw-field resolve),
plan-time window-slice resolution (offset + keyset adapters + int
coercion), the composite-index advisory (tri-state coverage inventory
+ bounded dedup + DEBUG-gated log), the relation-connection
`to_attr` grammar (canonical + two delegates), scalar-only window
projection, and keyset cursor-column projection — and consumes
twelve neighboring owners by name without re-deriving any of them.

Trace subject is HEAD bytes only (blob
`b4dfd4a6f61044c6b5dca6ed9fa07d74f52d846d`, 1453 lines, HEAD
`5ee86193` confirmed before the first read and after the last).
The worktree file (`225011b691c956a0a6a9dc4a28c40a598b94870a`)
carries a concurrent session's uncommitted edits (+9: M2M-window
advisory silence arm in `_advise_composite_index`) that are NOT
traced, NOT edited, NOT reverted, and NOT worked around; both
fingerprints are recorded under Freshness in every finding.
Hunt-dirtied neighbors and the three hunt-dirtied oracle suites
were read at HEAD bytes only, via a disposable `git archive HEAD`
tree; clean neighbors were read in place. The main checkout was
never touched. No probe scope was created: every claim below is
decided statically against HEAD bytes, so no pytest ran.

Sites and roles, HEAD bytes:

- Definition `optimizer/nested_planner.py::plan_connection_relation`
  (+ `NestedConnectionPlanResult`, `_divergent_key_windows`,
  `_log_connection_fallback`, `_identities_for_response_keys`,
  `_connection_node_selections`, `_raw_relation_field`): the
  orchestration. Sole production caller is the walker delegation
  (`optimizer/walker.py::_plan_connection_relation`, pure delegate:
  twelve injected callables + one `merge_from`); no second planning
  body exists (census over `plan_connection_relation`,
  `NestedConnectionRequest(`, `merge_from`, `merge_metadata_from`).
- Definition `optimizer/nested_planner.py::_connection_window_slice_from_arguments`
  (+ `_keyset_window_slice_from_arguments`, `_coerce_pagination_int`):
  the plan-time slice adapters. Consumers: `_divergent_key_windows`
  (both adapters), `optimizer/walker.py::_normalized_alias_payload`
  (coercion, for divergence/conflict comparison), and the keyset +
  plans suites directly.
- Definition `optimizer/nested_planner.py::_advise_composite_index`
  (+ the tri-state tokens, coverage chain, order/index readers,
  B-tree type set, backend-ordering probe, bounded dedup, render):
  the advisory. Sole production caller is the strategy loop's
  first-accepted-window latch; oracles are the 66-test advisory
  suite (autouse dedup reset per test).
- Definition `optimizer/nested_planner.py::relation_connection_to_attr`
  (+ `_relation_connection_to_attr`,
  `_relation_connection_to_attr_for_key`): the `to_attr` grammar.
  Plan side builds via the canonical (request `to_attr`);
  resolve side probes via the delegates
  (`connection.py`, per-key first then shared);
  `types/resolvers.py::_check_n1` threads the probed attr as a
  parameter (never rebuilds it); the walker carries aliases for
  historical test pins. Package-wide `_dst_` census: no second
  spelling of this grammar (the `_dst_row_number` /
  `_dst_total_count` annotation names are plans-owned per verified
  `nested-fetch-strategy-seam`; the `_dst_synthesized_relation_connection`
  marker is a finalizer re-entrancy token — R10).
- Definition `optimizer/nested_planner.py::_project_scalar_only_window`
  (+ `_concrete_order_columns`, `_order_entry_field_name`): the
  scalar-only column set. Sole production caller is the
  scalar-only branch; sole test reader is `test_walker.py`.
- Definition `optimizer/nested_planner.py::_extend_only_projection`:
  the cursor-column union. Three production call sites: the
  planner keyset branch plus two in `connection.py::_keyset_order_state`
  (declared-order fast path + `orderBy:` path).
- Consumers of indexed families, each composing by name:
  `_select_nested_strategy` (`nested-connection-strategy-selection`),
  `_connector_only_field` (`window-partition-resolution`; zero
  production callers, one pin — re-verified), the SKIP gate
  (`optimizer-hint-skip-predicate`), the hint strategy read
  (`optimizer-hint-shape`), the raw-leg classify + `windowable`
  gate (`window-partition-resolution`), the scalar attach read
  (`prefetch-attach-column-projection`), the request build
  (`nested-fetch-strategy-seam`; sole `NestedConnectionRequest(`
  site — re-verified), the base-queryset gate
  (`unwindowable-child-queryset-classification`).
- Consumers of verified-artifact families (names live in those
  artifacts; rows not yet indexed — cited, never re-litigated):
  entry parsing + explicit-nulls reads (`order-entry-vocabulary`,
  plans F-L), the deterministic order
  (`connection-order-ladder`, plans F-K; the two call sites are
  this planner + `connection.py`, the cursor-parity pair),
  the edges/node unwrap (`edges-node-unwrap`, selections F-L),
  the count observers (`count-observer-walks`, selections F-M),
  the connection vocabulary (`connection-vocabulary-resolution`,
  selections F-K), response keys (`response-key-grammar`,
  selections F-G), plan construction + merges
  (`optimization-plan-record`, plans F-G), the deferred-loading
  unpack (`deferred_loading_of`, plans-owned; four consumers),
  the lookup accessor (`relation-instance-accessor`), the keyset
  cursor state + codec (keyset-owned), the fallback error type
  (`UnwindowableConnection`, utils/connections-owned).
- Held for undispatched items (consumer links recorded here,
  rules adjudicated there): bounds derivation, range plan, fetch
  mode, sidecar core, relay cap (all utils/connections-owned —
  File `utils/connections.py`); the soft-import primitive
  (utils/imports-owned — File `utils/imports.py`).
- Oracles (all spell expectations independently; none reads an
  owner table): the advisory suite (66 tests), `test_walker.py`
  (orchestration + alias-namespace pins), `test_keyset_connection.py`
  (keyset adapter + cursor projection), `test_plans.py`
  (offset adapter + per-key attrs + divergent windows),
  `test_nested_fetch.py` (result record + request floor),
  `test_relay_connection.py` (shared + per-key `to_attr`
  literals, fast-path probes), `test_join_taxonomy.py`
  (planner interplay rows), plus live suites pinning behavior
  over HTTP (auto windows, single-parent fast path, keyset,
  library shapes, hints observability).
- Projections: the target module/class/helper docstrings, the
  delegation + fast-path + strictness consumer docstrings
  (walker, connection, `_check_n1`, finalizer field-name
  comment), the GLOSSARY connection-aware-planning + strictness
  anchors, the README strategy-override paragraph and indexing
  paragraph (the latter is D1's contradicted contract row),
  TREE module lines, spec-033 Decisions 4/5/6/8/11 + spec-035
  Decisions 4/5 + the BACKLOG enforced-matching-order contract.

Converge / diverge on fresh evidence (run-5 rows naming this file
as interplay context): CONVERGE on planner re-resolution
(standing hints-R7 / nested_fetch-R1; trigger re-checked fresh,
not met), on `nested-fetch-strategy-seam` (sole-builder census
re-derived fresh), on `unwindowable-child-queryset-classification`
(three-gate census re-derived fresh), on
`prefetch-attach-column-projection` (sibling-consumer boundary
re-derived fresh), and on `window-partition-resolution` (five
call-site census re-derived fresh). DIVERGE on the M2M advisory
near-miss (join_taxonomy-D1(b)): fresh evidence — the README M2M
indexing row, the violated equality-constancy premise, and a
recommended shape matching neither README M2M shape — makes it
defect-shaped; recorded as D1 observed-not-homed because the
concurrent session owns those lines. The walker artifact is
REOPENED prior evidence only: every walker-side claim above
(delegation, aliases, coercion read, absorb seam, identity
derivation, merge scheme) was re-derived fresh against HEAD
bodies, never inherited.

## Verification

### Matrix

Mechanism censuses ran over a disposable `git archive HEAD` tree
of the package plus tests, examples, and docs; every count below
is HEAD-true.

1. Cross-flavor policy mirroring — SEARCHED. No sibling flavor
   (mutations, forms, rest_framework, filters, orders) owns a
   fetch-strategy or window-planning surface. The three
   cross-flavor touchpoints are all composition, verified at
   HEAD bodies: root/per-parent keyset resolution
   (`connection.py::_keyset_order_state`) consumes
   `_extend_only_projection` (F6) and the entry vocabulary
   through its own `_keyset_order_ref` adapter (which composes
   `order_entry_name_and_direction` + the explicit-nulls
   predicate by name — no second parser); the synthesized
   resolver probes `to_attr` through the delegates (F4);
   strictness threads the probed attr (F4). The exact-type
   B-tree gate and the fail-soft `except` are per-domain
   instances of the rejected shared populations (R8/R9,
   triggers checked). No mirrored second definition.
2. Sync/async twins — NO SUCH SURFACE. The target holds zero
   `async def`, zero `await` (grep-verified; the two `async`
   tokens are docstring rationale about `SynchronousOnlyOperation`
   avoidance). Plan-time sync orchestration plus in-memory
   derivation; no colored twin exists to drift. The async-facing
   rules the target touches (cursor-column loading, morph
   predicate alias-lateness) are single-sited with stated
   async rationale, not twins.
3. Derived rather than repeated knowledge — SEARCHED. Every
   derivation composes its owner by name: entry parsing (F5),
   explicit-nulls (F3/F5 consumers), connection order (F1),
   bounds + range + fetch mode (F1/F2), sidecar core (F1;
   already one body — R17), keyset codec + cursor state
   (F1/F2), deferred-loading unpack (F6), attach columns (F5),
   partition/connector (F1/E1), lookup accessor (F1), relay cap
   (F2), soft import (F3), merges (F1; R12), resolver keys
   (F1; R11). Reconstructed-fact candidates investigated:
   the order name/attname index (R6, rejected), the identity
   filter vs derivation (R11, rejected), the `_check_n1`
   probe (threaded, F4), per-key vs shared probe order (F4).
   No fact has two derivations.
4. Inverse / round-trip pairs — SEARCHED. Four pairs, each
   single-owned with a composed half: request build (planner)
   vs window read (`connection.py::_resolve_from_window`,
   incl. the physical-shape fetch-mode read-back and R14's
   defensive tail); `to_attr` build (F4) vs resolve probe
   (delegates; never parsed back — the `$` escape has zero
   unescape sites, correctly one-way); keyset seek encode
   (mint, keyset-owned) vs decode (composed codec); advisory
   key (single site). `resolve_strategy` has no inverse
   (verified in `nested-connection-strategy-selection`).
   No pair has two owners.
5. Contracts restated in another medium — SEARCHED. Every
   medium a change moves is classified in System trace:
   oracles (7 package suites + 5 live suites, all independent
   spellings incl. literal `to_attr` pins and the 66-row
   advisory matrix) and projections (target docstrings,
   4 consumer-side contract docstrings, 2 GLOSSARY anchors,
   2 README paragraphs, TREE lines, spec Decisions). The D1
   README row is a projection contradicting the body, filed
   as a defect rather than counted. No restated definition.
6. Enforcement by omission — SEARCHED. Families enumerated,
   each member checked: all eight refusal arms fire on their
   shapes (conflict, SKIP, unresolvable target, missing model,
   malformed, unwindowable join, unwindowable base, strategy
   refusal); the keyset path shares `_divergent_key_windows`
   so no gate is offset-only; divergent aliases route per key
   while the shared scheme keeps the legacy attr; the
   scalar-only branch carries cursor columns for keyset
   targets through the shared effective order (no gap
   between the scalar and keyset branches); every accepted
   window of every strategy passes the advisory latch;
   both `to_attr` schemes probe resolve-side in per-key-first
   order. No member lacks its guard; no gap found. (D1 is a
   wrong firing, not a missing guard.)

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`b4dfd4a6`, 1453 lines), read via `git show HEAD:` plus an AST
dump. Count: 63 nodes (1 module docstring + 23 imports + 39
named members). Every named member lands below; nothing is
unassigned. Split homes cite both; existing-family homes name
the indexed row (no new row owed — both already list this
file).

| # | Member | Home |
|---|---|---|
| 1 | Module docstring (transactional-planner contract prose) | Projection at the owner; supports F1 (prose, not a definition) |
| 2-14, 16-24 | Plain imports (future, stdlib, Django, graphql-core, keyset, utils.connections, utils.imports, utils.relations, logger, hints, join_taxonomy, nested_fetch, plans, selections) | Mechanics L1; each a consumer link to its owner, all consumed |
| 15 | `relay_max_results_from_info as _relay_max_results_from_info` re-export | L1 (historical private name for the walker alias + test pins; dig owned in utils/connections) |
| 25 | `_PostgresBTreeIndex` | F3 (`composite-index-advisory`) |
| 26 | `_BTREE_INDEX_TYPES` | F3 |
| 27 | `_every_backend_supports_index_column_ordering` | F3 |
| 28 | `NestedConnectionPlanResult` (+ `accepted`) | F1 (`nested-connection-plan-orchestration`) |
| 29 | `_connector_only_field` | E1 (consumer of EXISTING `window-partition-resolution`) |
| 30 | `_order_entry_field_name` | F5 (`scalar-only-window-projection`) |
| 31 | `_concrete_order_columns` | F5 |
| 32 | `_select_nested_strategy` | E2 (consumer of EXISTING `nested-connection-strategy-selection`) |
| 33 | `_concrete_order_terms` | F3 |
| 34 | `_index_leading_terms` | F3 |
| 35-37 | `_INDEX_COVERED`, `_INDEX_ABSENT`, `_INDEX_UNKNOWN` | F3 (tri-state tokens) |
| 38 | `_terms_serve_order` | F3 |
| 39 | `_index_serves_window` | F3 |
| 40 | `_plain_field_terms` | F3 |
| 41 | `_model_index_shapes` | F3 |
| 42 | `_index_coverage` | F3 |
| 43 | `_describe_index_columns` | F3 |
| 44-46 | `_MAX_INDEX_ADVISORY_KEYS`, `_IndexAdvisoryKey`, `_index_advisory_seen` | F3 (bounded dedup) |
| 47 | `clear_index_advisory_dedup` | F3 (test-isolation seam; zero production callers) |
| 48 | `_index_advisory_already_emitted` | F3 |
| 49 | `_advise_composite_index` | F3 |
| 50 | `_project_scalar_only_window` | F5 |
| 51 | `_extend_only_projection` | F6 (`keyset-cursor-column-projection`) |
| 52 | `relation_connection_to_attr` | F4 (`relation-connection-to-attr-grammar`) |
| 53 | `_relation_connection_to_attr` | F4 (compatibility delegate) |
| 54 | `_relation_connection_to_attr_for_key` | F4 (compatibility delegate) |
| 55 | `_connection_node_selections` | F1 (adapter over the selections-owned unwrap) |
| 56 | `_coerce_pagination_int` | F2 (`plan-time-window-slice-resolution`) |
| 57 | `_connection_window_slice_from_arguments` | F2 |
| 58 | `_keyset_window_slice_from_arguments` | F2 |
| 59 | `_divergent_key_windows` | F1 |
| 60 | `_log_connection_fallback` | F1 |
| 61 | `_identities_for_response_keys` | F1 |
| 62 | `_raw_relation_field` | F1 |
| 63 | `plan_connection_relation` | F1 |

Homes tally: F1 7, F2 3, F3 20, F4 3, F5 3, F6 1,
existing-family consumers 2, L1 mechanics (docstring + imports).

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed,
never counted):

- Orchestration: posit a ninth refusal arm — 1 definition
  (`plan_connection_relation` gains the arm; the walker
  delegation passes through). Posit a third window scheme —
  1 definition (the scheme selector + `_divergent_key_windows`
  payload map). Posit a new strategy-dispatch input — 1
  request-build site (sole `NestedConnectionRequest(` census).
  No second planning body exists (walker delegates; root
  connection path never plans nested).
- Per-key window pass: posit a new per-payload gate — 1
  definition (`_divergent_key_windows`); both schemes inherit
  it. Posit a new fallback reason — 1 log site shape
  (`_log_connection_fallback` + reason strings; R15 keeps the
  other media separate).
- Identity recording: posit a new identity vocabulary — 1
  definition (walker's `_resolver_identities_for`); the
  planner filter (R11) follows by construction.
- Slice adapters: posit a new pagination argument — 1
  coercion (shared `_coerce_pagination_int`, incl. the
  walker normalization consumer) + the two shared
  derivations (listed, utils/connections-owned). Posit a
  new malformed class — 1 mapping per twin (the caught
  sets differ legitimately: GraphQLError exists only on
  the keyset path). Posit moving coercion into the shared
  helper — rejected (R2).
- Advisory inventory: posit a newly representable index
  shape — 1 definition (`_model_index_shapes` arm).
  Posit a new equality-prefix column (second morph half) —
  1 prefix site (`_advise_composite_index`) + the coverage
  rule (unchanged: permutation + direction-agnostic
  prefix). Posit a new uninspectable order-term kind — 1
  definition (`_concrete_order_terms` None arm). Posit a
  new B-tree-backed index type — 1 set
  (`_BTREE_INDEX_TYPES` + soft import).
- Advisory emission: posit a new dedup dimension — 1 key
  (`_IndexAdvisoryKey`); strategy stays excluded by the
  stated field-static contract. Posit rewording the
  recommendation — 1 renderer (`_describe_index_columns`)
  + 1 log call. The M2M firing is D1.
- `to_attr` grammar: posit a third scheme (beyond shared /
  per-key) — 1 definition (`relation_connection_to_attr`);
  plan build + both resolve probes + strictness follow by
  construction. Posit a response-key alphabet change — 1
  escape (`_` to `$`; zero unescape sites, correctly
  one-way). No second spelling exists (census).
- Scalar projection: posit a new scalar column class — 1
  definition (`_project_scalar_only_window`); attach facts
  stay taxonomy-owned, order facts stay in F5. Posit the
  projection consuming the advisory's terms walk — rejected
  (R1: skip-vs-None contracts).
- Cursor projection: posit a third mask mode — 1 definition
  (`_extend_only_projection`); all three production call
  sites follow. Posit moving the union into the shared
  unpack — rejected (R13: unpack reads, this rewrites).
- Connector shim: posit a new connector rule — 1 definition
  (the taxonomy classifier); the shim follows (E1).
- Strategy read: posit a new builtin name — 1 definition
  (the `nested_fetch.py` registry); the planner read follows
  (E2). Posit the planner branching on resolve failure —
  the standing trigger (R3), not met.

No read-only probe was needed: every claim above is decided
statically against HEAD bytes (AST census, package-wide
HEAD-true reader censuses, body reads, provenance-chain
reads), so no `docs/dry/temp-tests/dry-file-optimizer__nested_planner/`
scope was created and no pytest ran.

## Findings

### F1 — Nested-connection plan orchestration (NEW family `nested-connection-plan-orchestration`, open)

Contract: the transactional planning of one recognized nested
connection — eight ordered refusal arms (response-key conflict,
divergent-scheme select, hint SKIP, target resolution,
missing related model, per-payload windows, unwindowable join,
unwindowable base queryset), each leaving the selection
unplanned with strictness-visible bookkeeping (malformed keys
record identities so the field's own error preempts the
strictness flag); edges/node unwrap with the once-resolved
connection vocabulary; one child-queryset build through the
shared seam under the prefetch-child seal; the deterministic
order through the plans-owned ladder; scalar-only vs keyset
projection branches; split count observers feeding one shared
fetch-mode value; one fully-resolved request per window to
the field-static strategy with merge-only-on-True into an
isolated plan; the field-static advisory latch on the first
accepted window; metadata absorb plus identity recording on
the success path only. Varies over refusal arms, window
schemes, projection branches, and absorb/identity bookkeeping.

Sites and roles: definitions `optimizer/nested_planner.py`
(`plan_connection_relation`, `NestedConnectionPlanResult`,
`_divergent_key_windows`, `_log_connection_fallback`,
`_identities_for_response_keys`, `_connection_node_selections`,
`_raw_relation_field`; HEAD `b4dfd4a6`). Sole production
caller is the walker delegation (pure: twelve injected
callables + one `merge_from` — re-verified fresh, never
inherited from the reopened artifact). Consumers composing
by name from twelve owners: scheme predicates + identity
derivation + child builders (walker-injected), SKIP (hints),
target model + cursor state (definition/keyset),
windows (F2), join + windowability (join_taxonomy), base
safety (nested_fetch classifier), order (plans ladder),
unwrap + observers + vocabulary + response keys
(selections), request + strategy (nested_fetch seam),
merges + appenders (plans record), lookup (relations).
Oracles: `test_walker.py` orchestration rows (incl. the
per-key `to_attr` set pin and divergent-window rows),
`test_plans.py` window rows, `test_nested_fetch.py`
result-record rows, `test_relay_connection.py`
fast-path + alias-routing rows, and the live auto /
fastpath / shapes / keyset suites. Projections: target
docstrings, the delegation + fast-path + strictness
consumer docstrings, GLOSSARY anchors, TREE lines, the
spec-033/035 Decisions.

Challenges: all orchestration rows count 1 definition; no
second planning body, window pass, fallback log, identity
filter, unwrap adapter, or raw-field resolve exists
(package-wide censuses). Owner by responsibility:
`plan_connection_relation` — the narrowest module the
walker already delegates to with no reversal. The family
item audits the rule whole (arm order, scheme selection,
projection branches, absorb/identity discipline, every
composed read) and decides the structural gate; this file
item makes no edit. Family-item note (below the defect
bar): the resolve side reads the fetch mode back off the
window's physical shape rather than re-deriving it — the
round-trip's read half, already single-owned, needs no
gate beyond the mode-exclusivity the seam enforces.

Freshness: target HEAD
`b4dfd4a6f61044c6b5dca6ed9fa07d74f52d846d` (worktree
`225011b691c956a0a6a9dc4a28c40a598b94870a`, concurrent
M2M silence arm in `_advise_composite_index` — NOT traced);
`optimizer/walker.py` HEAD
`e8d800052cc87ca77070290c4c2f396061259b81`,
`optimizer/nested_fetch.py` HEAD
`4d8d37a7f52cf94d2916f17db3a8a21393e28d57` (worktree
`29ce5201` hunt dirt — NOT traced),
`optimizer/join_taxonomy.py` HEAD
`9b355a5090ce471e373849dd0a61da8f808e78b9` (worktree
`e1cbb3e3` hunt dirt — NOT traced), `optimizer/hints.py`
HEAD `da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74`
(worktree `8064af14` hunt dirt — NOT traced),
`optimizer/plans.py` `cce98531`, `optimizer/selections.py`
`a48f6172`, `optimizer/extension.py` `49667a93`,
`connection.py` HEAD
`4894f90f74f30db0a2b0b8b0e2e5f5bfcb0a449` (worktree
hunt dirt — read at HEAD only), `utils/connections.py`
HEAD `f549389e82ca87df57c298a6ae5b8c740d0a20b`,
`keyset.py` HEAD
`df4b5e2ff0f3a6b2d77198a1fd3b0ef5f29ae38b`,
`utils/relations.py` HEAD `7662b0bb` (worktree
`1cf81e58` hunt dirt — NOT traced),
`types/resolvers.py` `f3341e6a`,
`tests/optimizer/test_walker.py` `78c0f7a4`,
`tests/optimizer/test_plans.py` `1e09d6d8`,
`tests/optimizer/test_nested_fetch.py` HEAD `7fbd957b`
(worktree `f58c265c` hunt dirt — NOT traced),
`tests/test_relay_connection.py` `b6bd90d9`,
`test_optimizer_auto_api.py` `ca9fea06`,
`test_single_parent_fastpath_api.py` `492fac73`,
`test_library_shapes_api.py` `8e2678b2`, GLOSSARY
`d3ef357c`, TREE `25423989`.

### F2 — Plan-time window-slice resolution (NEW family `plan-time-window-slice-resolution`, open)

Contract: the plan-time-only pagination-to-window derivation —
int coercion for inline-literal token strings (pass-through
for `None` and non-castables so the shared `isinstance`
gate keeps its shipped malformed behavior), composition of
the shared bounds owners (offset engine / keyset fork),
`max_results` threading from the schema config, the
malformed-to-`None` mapping (`ValueError`/`TypeError`, plus
the codec's `GraphQLError` on the keyset path only),
`UnwindowableConnection` propagation for valid-but-unplannable
shapes, and keyset cursor pre-validation before backward
classification (so strictness cannot mask malformed input
as an unplanned N+1). The offset twin never catches
`GraphQLError` because its shared helper never raises it
(body-verified); the keyset twin's extra catch covers the
codec alone, whose every failure path was verified to
raise the uniform `GraphQLError`. Varies over pagination
vocabulary, error mapping, and cursor validation.

Sites and roles: definitions `optimizer/nested_planner.py`
(`_connection_window_slice_from_arguments`,
`_keyset_window_slice_from_arguments`,
`_coerce_pagination_int`; HEAD `b4dfd4a6`). Consumers:
`_divergent_key_windows` (sole caller of both adapters),
`optimizer/walker.py::_normalized_alias_payload`
(coercion for divergence/conflict comparison — the
documented identical coercion), `test_keyset_connection.py`
(keyset adapter rows, attribute access — D2's witness),
`test_plans.py` (offset adapter rows). Shared owners
composed (held for File `utils/connections.py`):
`derive_connection_window_bounds`,
`derive_keyset_window_bounds`, `relay_max_results_from_info`.
Oracles spell bounds literally and assert attribute reads.
Projections: adapter docstrings (incl. the record-over-tuple
note the keyset annotation contradicts — D2).

Challenges: all slice rows count 1; no second coercion,
offset adapter, or keyset adapter exists. Owner:
the adapters beside the coercion — the narrowest module
both the planner pass and the walker normalization
already import. The family item audits the twins whole
(coercion, caught sets, cursor validation, the shared
derivations' error contracts) and decides the gate;
this file item makes no edit.

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
concurrent dirt — NOT traced); `optimizer/walker.py`
`e8d80005`, `utils/connections.py` `f549389e`,
`keyset.py` `df4b5e2f`,
`tests/test_keyset_connection.py` `6dc6b59e`,
`tests/optimizer/test_plans.py` `1e09d6d8`,
`tests/optimizer/test_walker.py` `78c0f7a4`.

### F3 — Composite-index advisory (NEW family `composite-index-advisory`, open)

Contract: the dev-mode one-time-per-shape composite-index
advisory — a B-tree-only coverage inventory over every
represented physical shape (unconditional field-based
`Meta.indexes`, unconditional field-based unique constraints
and `unique_together`, single-column pk/unique/db_index;
non-B-tree / expression / partial / opclass / lagged shapes
count UNINSPECTABLE, never covering, never absent), a
direction-carrying order-terms walk that returns `None`
(UNKNOWN, silence) on any non-local-concrete term or
explicit NULLS placement, an equality-prefix coverage rule
(any permutation, direction-agnostic) plus exact-or-fully-
reversed order service, a morph-first equality prefix, an
effective-order strip of partition-constant columns, a
backend-neutral descending-term probe (fail-soft, every
alias must support column ordering), a strategy-independent
bounded-LRU dedup keyed on (model label, equality, order),
a `DESC`-annotated renderer, and a WARNING-under-DEBUG /
debug-otherwise single log call. Silence unless absence is
proven from fully-inspectable metadata. Varies over
represented shapes, the equality model, order-term kinds,
the B-tree set, and emission policy.

Sites and roles: definitions `optimizer/nested_planner.py`
(all 20 advisory members; HEAD `b4dfd4a6`) in one linear
in-file call chain (single callers throughout — census).
Sole production caller is the F1 first-accepted-window
latch. Consumers composing by name: the taxonomy
connector + morph facts, the entry parser + explicit-nulls
predicate (plans F-L), the soft-import primitive
(utils/imports — held), the package logger. Oracles: the
66-test advisory suite (inventory matrix, tri-state rows,
dedup rows incl. eviction, backend-probe rows, log-level
rows; autouse per-test dedup reset — the stated explicit
contract, no clear-bus wiring owed). Projections: member
docstrings, the README indexing paragraph (D1's
contradicted row), the nested_fetch module indexing prose.

Challenges: all advisory rows count 1; no second
inventory, coverage rule, order walk, dedup, renderer, or
emission site exists. Owner: `_advise_composite_index`
beside the chain — the narrowest module with the planner
latch as its sole caller. The family item audits the rule
whole (inventory arms, tri-state, equality model, dedup,
emission) and decides the gate; this file item makes no
edit. Family-item notes: (a) D1's M2M firing is the one
wrong output (observed-not-homed — D1); (b) the explicit-
nulls-to-None discipline also appears in
`connection.py::_keyset_order_ref` with a raise outcome
(cursor anchorability, not coverage silence) — same
composed predicate, different contract, for the
connection.py re-trace to note, not adjudicated here.

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
concurrent M2M dirt on the advised lines — NOT traced;
D1's lines); `optimizer/join_taxonomy.py` HEAD `9b355a50`
(worktree `e1cbb3e3` dirt — NOT traced),
`optimizer/plans.py` `cce98531`, `utils/imports.py`
`291ecedd`, `optimizer/extension.py` `49667a93` (LRU
contrast — R7), `optimizer/nested_fetch.py` HEAD
`4d8d37a7` (worktree `29ce5201` dirt — NOT traced),
`tests/optimizer/test_nested_index_advisory.py` HEAD
`beee6b7d` (worktree `103a19da` hunt dirt — NOT traced),
`docs/README.md` `c32da236`, GLOSSARY `d3ef357c`.

### F4 — Relation-connection `to_attr` grammar (NEW family `relation-connection-to-attr-grammar`, open)

Contract: the package-reserved window `to_attr` grammar —
`_dst_<field>_connection` default plus
`_dst_<field>$<key>_connection` per-key with `_`-to-`$`
escape; one-way (zero unescape sites — correctly absent,
attrs are read with `getattr`, never parsed); plan builds
via the canonical while resolve probes via the delegates
(per-key first from `info.path.key`, shared fallback,
tracking which attr held rows so strictness probes the
same location). Varies over schemes, escape, and probe
order.

Sites and roles: definitions `optimizer/nested_planner.py`
(`relation_connection_to_attr` + both delegates; HEAD
`b4dfd4a6`). Builder: the F1 request loop (canonical).
Readers composing by name: `connection.py` (both
delegates), `types/resolvers.py::_check_n1` (threaded
`to_attr` parameter — verified no rebuild), the walker
aliases (historical test pins). Oracles spell both
schemes literally (`_dst_books_connection`,
`_dst_books$x_connection`, divergent set pins). The
`_dst_row_number` / `_dst_total_count` annotation names
are plans-owned (verified `nested-fetch-strategy-seam`
boundary — converged, not re-litigated). Projections:
grammar docstring, fast-path + strictness + finalizer
consumer prose, GLOSSARY window paragraph.

Challenges: both grammar rows count 1; no second
spelling, escape, or probe exists (package-wide `_dst_`
census). Owner: `relation_connection_to_attr` — the
narrowest module both plan and resolve sides already
import. The family item audits the grammar whole (both
schemes, escape, probe order, strictness threading) and
decides the gate (a literal-spelling producer is the
plausible divergence); this file item makes no edit.

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
dirt — NOT traced, outside F4 lines); `connection.py`
HEAD `4894f90f` (worktree dirt — read at HEAD only),
`types/resolvers.py` `f3341e6a`, `types/finalizer.py`
`77fd9a2d`, `optimizer/walker.py` `e8d80005`,
`optimizer/nested_fetch.py` HEAD `4d8d37a7` (worktree
`29ce5201` dirt — NOT traced),
`tests/test_relay_connection.py` `b6bd90d9`,
`tests/optimizer/test_walker.py` `78c0f7a4`,
`tests/optimizer/test_plans.py` `1e09d6d8`,
`tests/optimizer/test_nested_fetch.py` HEAD `7fbd957b`
(worktree `f58c265c` dirt — NOT traced),
`tests/optimizer/test_lateral_fetch.py` `67431054`,
GLOSSARY `d3ef357c`.

### F5 — Scalar-only window projection (NEW family `scalar-only-window-projection`, open)

Contract: a scalar-only (pageInfo/totalCount) window loads
exactly pk + the attach-complete connector set + the
concrete order columns via a direct `.only()`, gated on
the threaded operation flag; order entries resolve
through the shared entry parser with a skip policy for
related spans and unresolvables (forgoing an unread
column is harmless — projection completeness, never a
claim). Varies over column classes and the skip policy.

Sites and roles: definitions `optimizer/nested_planner.py`
(`_project_scalar_only_window`, `_concrete_order_columns`,
`_order_entry_field_name`; HEAD `b4dfd4a6`). Sole
production caller is the F1 scalar branch. Consumers
composing by name: attach columns
(`prefetch-attach-column-projection` — CONVERGE with
join_taxonomy F3: the sibling-consumer boundary
re-derived fresh; both readers feed FieldMeta legs per
that item's D1 dual contract), entry parsing
(`order-entry-vocabulary`, plans F-L — the shim body
re-verified delegating), the operation flag (walker G2
gate). Oracles: `test_walker.py` projection rows (incl.
the walker-namespace `_concrete_order_columns` pin).
Projections: writer docstrings stating the shared owner.

Challenges: both projection rows count 1; no second
scalar column set, order walk, or entry shim exists.
Owner: `_project_scalar_only_window` beside its walks —
the narrowest module with the scalar branch as its sole
caller. The family item audits the projection whole and
decides the gate; this file item makes no edit.

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
dirt — NOT traced, outside F5 lines);
`optimizer/join_taxonomy.py` HEAD `9b355a50` (worktree
`e1cbb3e3` dirt — NOT traced), `optimizer/plans.py`
`cce98531`, `optimizer/walker.py` `e8d80005`,
`tests/optimizer/test_walker.py` `78c0f7a4`.

### F6 — Keyset cursor-column projection (NEW family `keyset-cursor-column-projection`, open)

Contract: cursor columns survive an existing `.only()` /
`.defer()` mask — `.only()` re-applies the union read
through the shared deferred-loading unpack (chaining
replaces, so the union is reload-bearing); `.defer()`
clears then re-applies every deferred field except the
cursor columns; no mask or full coverage returns the
queryset unchanged. Otherwise cursor minting lazy-loads
per edge in sync execution and raises in async. Varies
over mask modes; the column source is threaded
(keyset-owned), never derived here.

Sites and roles: definition
`optimizer/nested_planner.py::_extend_only_projection`
(HEAD `b4dfd4a6`). Three production call sites: the F1
keyset branch plus two in
`connection.py::_keyset_order_state` (declared-order fast
path + `orderBy:` path — read fresh at HEAD). Single
unpack owner composed (`deferred_loading_of`;
fourth consumer beside two plans-internal readers and
the lateral projection read). Oracles:
`test_keyset_connection.py` projection rows. Projection:
helper docstring (mask-mode rationale).

Challenges: both rows count 1; no second cursor-column
union exists (the lateral/consumer readers read the
mask — R13). Owner: `_extend_only_projection` — the
narrowest module all three call sites already import.
The family item audits the union whole and decides the
gate; this file item makes no edit.

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
dirt — NOT traced, outside F6 lines);
`connection.py` HEAD `4894f90f` (worktree dirt — read
at HEAD only), `optimizer/plans.py` `cce98531`,
`optimizer/lateral_fetch.py` `db1ea315`,
`tests/test_keyset_connection.py` `6dc6b59e`.

### E1 — Connector shim (consumer of EXISTING family `window-partition-resolution`, open)

`optimizer/nested_planner.py::_connector_only_field` is the
`parent_join_column` projection shim over the single
join-condition classifier. Body re-verified delegating at
HEAD (one call, `None`-lenient return, historical-name
docstring intact). Production-caller census re-derived
fresh: ZERO (the planner's live paths use the raw-leg
classify in F1 and the attach read in F5); one oracle
pin (`test_walker.py`, imported from this module
directly). CONVERGE with join_taxonomy F1: the connector
rule, the shim's consumer role, and family question (b)
(the shim's existence — unhomed, for the family item)
all stand as recorded there; nothing here reopens them.
No index row owed (the existing row already lists this
file).

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
dirt — NOT traced, outside E1 lines);
`optimizer/join_taxonomy.py` HEAD `9b355a50` (worktree
`e1cbb3e3` dirt — NOT traced), `optimizer/plans.py`
`cce98531` (sibling shim), `optimizer/walker.py`
`e8d80005`, `tests/optimizer/test_walker.py` `78c0f7a4`.

### E2 — Strategy selection read (consumer of EXISTING family `nested-connection-strategy-selection`, open)

`optimizer/nested_planner.py::_select_nested_strategy`
reads the per-field hint (`getattr` with `None` default),
re-resolves a set name through the single `resolve_strategy`,
else answers the active extension default. Body re-verified
at HEAD: unguarded call (the standing R3 trigger — not
met), field-static (never enters the plan-cache key, per
the docstring). Sole caller is the F1 strategy loop;
`active_strategy`'s sole production caller is this read
(census). CONVERGE with the run-5 selection family: this
file is pure consumer, the registry + resolver + alias
stay the single definition. No index row owed (the
existing row already lists this file).

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
dirt — NOT traced, outside E2 lines);
`optimizer/nested_fetch.py` HEAD `4d8d37a7` (worktree
`29ce5201` dirt — NOT traced), `optimizer/hints.py`
HEAD `da46ef89` (worktree `8064af14` dirt — NOT traced),
`optimizer/extension.py` `49667a93`.

### L1 — Module mechanics (file-local)

Module docstring (transactional-planner rationale —
projection of F1, never a definition), the 23 imports
(each consumed: every imported name has at least one
code read — census), and the `_relay_max_results_from_info`
re-export (historical private name: the walker aliases
it off this module and `test_walker.py` pins it through
there; the dig itself is single-owned in
utils/connections and shared with the resolve-time cap).
Single definition each, single module, no second site.
Challenge: posit a second planner docstring, a second
import-direction rule, or a second relay-cap alias —
none exists (package-wide censuses).

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
dirt — NOT traced); `utils/connections.py` `f549389e`,
`optimizer/walker.py` `e8d80005`,
`tests/optimizer/test_walker.py` `78c0f7a4`.

### R1 — `_concrete_order_columns` vs `_concrete_order_terms` (rejected)

The projection walk skips related spans and unresolvables
(forgoing an unread column is harmless); the advisory
walk returns `None` on the first of them (a coverage
claim from a partial order is a false positive) and
additionally rejects explicit NULLS placement and
dedupes direction-carrying terms. Same entry vocabulary,
opposite unknown-policies — and the difference is
load-bearing in both directions (stated at both bodies).
Contract difference: projection completeness vs coverage
claim. Reconsideration trigger: either walk's unknown
policy converges on the other's — then the walks merge
and the shared index (R6) follows.

### R2 — Plan-time coercion vs the shared derivation (rejected)

`_coerce_pagination_int` lives in the planner (plus the
walker normalization consumer) and is deliberately NOT
folded into the shared bounds helpers: plan-time inputs
are raw literal token strings while the resolver caller
already receives engine-coerced ints (stated at the
adapter). Folding it would make the shared helper own
an input shape only one of its two callers produces.
Contract difference: plan-time literal vocabulary vs
resolve-time coerced vocabulary. Reconsideration
trigger: the resolver starts receiving raw strings —
then the coercion belongs to the shared derivation.

### R3 — Planner re-resolution vs validation (rejected, standing)

Run-5 hints R7 / nested_fetch R1, both verified: one
owner composed twice, not two definitions. Trigger
re-checked fresh against HEAD: `_select_nested_strategy`
still calls `resolve_strategy` unguarded (no catch, no
branch on failure). Not met; the standing rejection and
its trigger stand.

### R4 — Connector shim vs `_record_relation_access` (rejected, standing)

Run-5 join_taxonomy R5, verified: source-row local column
vs child-side attach column. Trigger re-checked fresh
against HEAD: the walker still appends `attname` (the
forward FK id, `None` for reverse shapes) while the shim
projects the child-side connector; no call site needs
both. Not met; stands.

### R5 — Attach order vs advisory order (rejected, standing)

Run-5 join_taxonomy R16, verified at the owner:
connector-first attach-key order vs morph-first
index-prefix order. Trigger re-checked fresh: the
advisory still prefixes morph-first and the property
still orders connector-first, with the contrast stated
at the property. Not met; stands.

### R6 — The order-walk name/attname index (rejected)

`{field.name: field.attname}` over `concrete_fields`
plus its value set is spelled identically in both order
walks — and only there (census; the lateral reversed
map, linear name-or-attname scan, and plans
`get_field` reads each carry their own failure policy
and return). The shared lines are a per-site loop index
feeding divergent unknown-policies (R1): a new field
kind moves the policies, not the map, so extracting the
two lines relieves no change obligation while coupling
two families' interiors. Contract difference: per-site
`_meta` spelling idiom vs a resolution rule.
Reconsideration trigger: a change that must move the
index content identically at both sites without touching
either policy (e.g. the iteration itself gains a filter
both walks need verbatim).

### R7 — Advisory dedup LRU vs the extension LRUs (rejected)

Three hand-rolled `OrderedDict` LRUs with three
contracts: the advisory dedup is a module-level
emission SET (values `None`, hit suppresses, evict-one
past cap); the document-key cache is a module-level
deterministic-value MEMO (hit returns the value,
no-source bypass, evict-one); the plan cache is an
INSTANCE plan store (cacheability-gated insert,
quarter-sweep eviction, hit/miss counters, exec-memo
interplay). Unifying them needs mode flags for
dedup-vs-memo, eviction quantum, bypass predicates, and
lifetime — machinery coupling three independent domains.
The advisory docstring's "exactly like the extension's
cross-request LRUs" is correctly scoped to race
consequence only (a dropped record changes re-warning,
never correctness — the same neutrality both extension
caches state). Contract difference: emission-dedup set
vs deterministic-value memo vs instance plan store.
Reconsideration trigger: two sites converging on
identical insert/promote/evict/race semantics with no
per-site bypass.

### R8 — Exact-type B-tree gate (rejected, standing)

File `_request_body.py` J2 (verified) already rejects one
shared exact-type gate: per-domain gates, different
reasons. This file's `type(index) not in
_BTREE_INDEX_TYPES` (an uninspected `Index` subclass may
change the access method) is one more instance — and the
adjacent `isinstance(constraint, models.UniqueConstraint)`
is its deliberate counter-shape (a constraint subclass is
safe because condition/expressions/opclasses/fields are
all inspected). Trigger checked against HEAD, not met:
no new foreign-object protocol needing exclusion.
Stands.

### R9 — Fail-soft backend probe guard (rejected, standing)

File `_request_body.py` J1 (verified) already rejects one
shared `except` guard. This file's `except Exception:
return False` (unproven ordering support degrades to
UNKNOWN, never to a coverage claim) is one more
per-domain instance. Trigger checked against HEAD, not
met. Stands.

### R10 — Synthesized marker vs the window grammar (rejected)

`_SYNTHESIZED_RELATION_CONNECTION_MARKER` shares only the
`_dst_` prefix with F4: it is a finalizer re-entrancy
token stamped on field OBJECTS so a partial-finalize
rerun recognizes its own attachment, while the window
grammar names instance LIST attrs the prefetch attach
lands. No reader confuses the namespaces (census).
Contract difference: finalize idempotence marker vs
fetch landing grammar. Reconsideration trigger: a
reader matching both namespaces with one predicate.

### R11 — Identity filter vs identity derivation (rejected)

`_identities_for_response_keys` filters the parallel
(runtime paths, identities) tuples by response key; the
walker builds those tuples as a cartesian product over
prefixes and response keys. Filter-over-parallel-tuples
vs cartesian construction — the filter's docstring states
"never a re-derivation", and the runtime paths always
end in a response key (cartesian proof), so the `[-1]`
read is safe by construction. Contract difference:
per-key selection vs key construction. Reconsideration
trigger: a caller needing filtered identities without
the walker's derivation — then the filter owns a second
derivation.

### R12 — Planner merge vs the walker absorb seam (rejected)

The planner calls `plan.merge_metadata_from(sub_plan)`
directly while the walker routes its absorb through
`_absorb_child_plan` — but the seam adds nothing over
the plans-owned body (rationale-only wrapper), and the
planner cannot compose the seam without reversing the
walker-imports-planner dependency. One owner composed
at two sites under an import-direction constraint.
Contract difference: named absorb seam with rationale
vs direct owner composition. Reconsideration trigger:
the absorb discipline gaining a step outside
`merge_metadata_from` — then the direct call diverges
from the seam.

### R13 — Cursor union vs consumer projection (rejected)

`_extend_only_projection` REWRITES the queryset's mask
(only-union / defer-invert); plans `_consumer_projection`
READS the mask into `(names, defer_mode)` for prune
decisions. Same unpack owner, opposite directions —
and the lateral backend's projection read is a third
reader, not a second writer. Contract difference: mask
rewrite vs mask read. Reconsideration trigger: a caller
needing read-then-rewrite in one pass under one
contract.

### R14 — Planner `last: 0` refusal vs the resolver tail (rejected)

The planner refuses to plan a reversed `last: 0` window
(per-key fallback, strictness-visible); the resolver
keeps its own `reverse and limit == 0` guard returning
`None` so the fallback factory reproduces upstream's
serve-all quirk. Different inputs (plan-time bounds vs
resolve-time rows + bounds), different callers (nested
planner vs every window consumer incl. root connections
and direct callers), stated at the planner arm as "the
defensive tail for direct callers". Contract difference:
plan-time refusal vs resolve-time defensive tail.
Reconsideration trigger: a planned reversed-`last: 0`
window reaching the resolver — then the planner arm
failed and one guard is redundant.

### R15 — Fallback wordings across three media (rejected)

The planner's debug log ("falls back to per-parent
resolution" + reason slot), the partition shim's raised
`OptimizerError` (test-only callers), and the
resolve-time strictness reasons ("not window-planned…",
user-visible under raise/warn) share vocabulary but
serve three audiences in three media with different
slots. Contract difference: plan-time debug trace vs
shim refusal error vs resolve-time strictness reason.
Reconsideration trigger: an oracle asserting cross-media
byte parity, or the shim gaining production callers
(its wording would turn user-visible).

### R16 — Full-flip match vs order reversal rendering (rejected)

`_terms_serve_order` admits a fully-reversed index scan
as a coverage PREDICATE (direction comparison, no SQL);
plans `_reverse_order_by` RENDERS reversed SQL (direction
flip + NULLS swap + loud rejection of unreversibles).
A match verdict vs a rendering — the plans R-1
reversal-split precedent, same shape (lateral
`order_sql` is the third, direction-only member).
Contract difference: coverage predicate vs SQL
rendering. Reconsideration trigger: the advisory
consuming the renderer (or the renderer the matcher's
verdict).

### R17 — Sidecar kwargs-arity vs input-arity (rejected, already one body)

`has_connection_sidecar_kwargs` (the planner's
per-payload gate) delegates to
`has_connection_sidecar_input` (the resolver's gate)
after one extraction — a single rule with two arities
in one module, whose docstring states the sharing.
Like join_taxonomy R3: two call shapes, one read body,
already shared. No consolidation to propose; held for
File `utils/connections.py` to record at the owner.

## Defects

### D1 — HEAD M2M advisory recommends a child-table composite that cannot serve the through-partitioned page (observed; concurrent session owns these lines — NOT homed)

At HEAD bytes, `optimizer/nested_planner.py::_advise_composite_index`
builds its equality prefix from `join.parent_join_column` —
the related model's pk attname for an M2M — and, when no
represented child-table index covers `(child_pk, order...)`,
recommends that child-table composite. Three fresh facts
make this defect-shaped (DIVERGE from the join_taxonomy
near-miss-(b) "advisory-only prose, not filed" on this
evidence):

- The README indexing paragraph (HEAD `c32da236`, the
  package's own indexing contract) states an M2M "cannot
  take that single shape" and needs TWO indexes — the
  through table's `(parent_id, child_id)` pair and the
  related model's `(order columns..., pk)`, pk TERMINAL.
  The advisory names `(child_pk, order...)`: pk LEADING,
  matching neither shape.
- The advisory's own equality model ("each equality column
  is CONSTANT within a partition") fails for M2M: every
  child row in a parent partition carries a DISTINCT pk,
  so the leading equality column is never constant.
- The partition key itself lives in the through table
  (verified `THROUGH_TABLE` / through-parent-FK mechanics
  at HEAD), outside the inspected child metadata — the
  exact gap the concurrent arm's paragraph names.

Contract row broken: the README M2M indexing row + the
advisory's serving claim ("lets the database serve each
partition's page from the index"). Feasible project
shape: any schema with an M2M nested connection under
the optimizer (M2M is windowable; supported public API).
Wire input reaching it: any GraphQL query planning an
M2M windowed connection (WARNING under DEBUG, debug
otherwise). A maintainer following the recommendation
creates a useless index — the advisory's sole output is
the recommendation, so a wrong recommendation IS its
behavior (cf. the filed join_taxonomy D1 prose defect).

The worktree already carries the concurrent session's
fix on these exact lines (the +9 M2M silence arm +
docstring paragraph recorded under Freshness).
Worker 0: home on a card ONLY if the concurrent session
does not land its arm; if it lands, close as
fixed-concurrent. Owner if homed:
`optimizer/nested_planner.py::_advise_composite_index`
(this file). Untouched per protocol — recorded, never
edited, never worked around.

Freshness: target HEAD `b4dfd4a6` (worktree `225011b6`
concurrent dirt on D1's lines — read for attribution
only); `optimizer/join_taxonomy.py` HEAD `9b355a50`
(worktree `e1cbb3e3` dirt — NOT traced),
`optimizer/nested_fetch.py` HEAD `4d8d37a7` (worktree
`29ce5201` dirt — NOT traced), `docs/README.md`
`c32da236`.

### D2 — HEAD keyset adapter annotation claims a tuple the body never returns (HEAD defect — home normally)

`optimizer/nested_planner.py::_keyset_window_slice_from_arguments`
annotates its bounds half `tuple[int, int | None, bool]`
while the body returns the shared `ConnectionWindowBounds`
record from `derive_keyset_window_bounds` (a frozen
dataclass, verified not a tuple). Every consumer uses
attribute access (the divergent pass, the strategy loop,
and the keyset adapter oracles asserting `window.offset`
/ `window.limit` / `window.reverse`), so runtime behavior
is correct — but the annotation contradicts the body and
contradicts the sibling offset adapter's documented
record-over-tuple decision. No type gate runs in CI, so
the blast radius is static readers and external
type-checkers: minor, but defect-shaped (stated contract
vs body).

Contract row broken: the function's own return
annotation. Feasible project shape: any consumer
type-checking against the planner (supported import
surface for tests and downstream tooling). Owner:
`optimizer/nested_planner.py::_keyset_window_slice_from_arguments`
(this file; HEAD-clean lines, NOT externally owned —
normal homing, no closeout condition). Worker 0: home on
a NAMED card at closeout. Never fixed inside this item.

Freshness: target HEAD `b4dfd4a6` (D2's lines are the
HEAD-clean annotation); `utils/connections.py`
`f549389e`, `tests/test_keyset_connection.py` `6dc6b59e`.

Near-misses considered against HEAD bytes and NOT filed:
(a) `_identities_for_response_keys` indexing
`runtime_path[-1]` — safe by construction (cartesian
proof: every path ends in a response key; R11). (b) The
direct `sel._optimizer_response_key_arguments` read —
guarded by the diverge premise (the attr exists and is
truthy exactly when divergent is true; walker's
docstring + body). (c) The twins' different caught sets
— principled (the offset helper never raises
`GraphQLError`; the codec raises only it — both
body-verified). (d) The keyset-never-reverses arm
(`window.reverse and window.limit == 0` dead on the
keyset path) — a shared gate, harmless, stated. (e) The
connector shim's zero production callers — join_taxonomy
F1's family question (b), not broken behavior. (f)
`through_model` with zero production readers — F2's
principle-11 question in join_taxonomy, not this file.

## Pending execution

None. All conclusions are static against HEAD bytes; no
probe, no pytest, no scratch scope. PG and sharded cells
need no execution for these claims: the item is zero-edit
(no behavior changed anywhere), and the one
alias-touching body (`_every_backend_supports_index_column_ordering`)
is reasoned from its fail-soft contract, never executed
(its oracles live in the advisory suite, which the final
gate runs).

## Judgment

Zero-edit file item: the target single-owns nested-connection
orchestration, plan-time slice resolution, the composite-index
advisory, the window `to_attr` grammar, and both window
projections, consuming twelve neighboring owners by name
everywhere it must hold, with six new families named for
Worker 0 (`Index rows` below), two existing-family consumer
verifications needing no new rows, one file-local row, and
seventeen rejections (five standing rejections
trigger-checked, the rest fresh or at-owner). Converged
with every run-5 interplay row except the M2M advisory
near-miss, where fresh evidence (README row + violated
premise + mismatched shape) diverges to an
observed-not-homed defect on concurrent-owned lines;
one HEAD-clean annotation defect filed for normal homing.
No pending execution, no production edit, no test edit.
HEAD stayed `5ee86193` throughout; the item touched
nothing tracked.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.)

- Family `nested-connection-plan-orchestration` | Owner
  `optimizer/nested_planner.py::plan_connection_relation`
  (with `NestedConnectionPlanResult`,
  `_divergent_key_windows`, `_log_connection_fallback`,
  `_identities_for_response_keys`,
  `_connection_node_selections`, `_raw_relation_field`) |
  Files `optimizer/nested_planner.py`, `optimizer/walker.py`,
  `optimizer/nested_fetch.py`, `optimizer/join_taxonomy.py`,
  `optimizer/hints.py`, `optimizer/plans.py`,
  `optimizer/selections.py`, `optimizer/extension.py`,
  `connection.py`, `utils/connections.py`, `keyset.py`,
  `utils/relations.py`, `types/resolvers.py` | Holding item
  Family `nested-connection-plan-orchestration` | open
- Family `plan-time-window-slice-resolution` | Owner
  `optimizer/nested_planner.py::_connection_window_slice_from_arguments`
  (with `_keyset_window_slice_from_arguments`,
  `_coerce_pagination_int`) | Files
  `optimizer/nested_planner.py`, `optimizer/walker.py`,
  `utils/connections.py`, `keyset.py` | Holding item Family
  `plan-time-window-slice-resolution` | open
- Family `composite-index-advisory` | Owner
  `optimizer/nested_planner.py::_advise_composite_index`
  (with the tri-state tokens, coverage chain, order/index
  readers, B-tree set, backend probe, bounded dedup,
  renderer) | Files `optimizer/nested_planner.py`,
  `optimizer/join_taxonomy.py`, `optimizer/plans.py`,
  `utils/imports.py`, `optimizer/extension.py`,
  `optimizer/nested_fetch.py` | Holding item Family
  `composite-index-advisory` | open
- Family `relation-connection-to-attr-grammar` | Owner
  `optimizer/nested_planner.py::relation_connection_to_attr`
  (with `_relation_connection_to_attr`,
  `_relation_connection_to_attr_for_key`) | Files
  `optimizer/nested_planner.py`, `connection.py`,
  `types/resolvers.py`, `types/finalizer.py`,
  `optimizer/walker.py`, `optimizer/nested_fetch.py` |
  Holding item Family `relation-connection-to-attr-grammar`
  | open
- Family `scalar-only-window-projection` | Owner
  `optimizer/nested_planner.py::_project_scalar_only_window`
  (with `_concrete_order_columns`,
  `_order_entry_field_name`) | Files
  `optimizer/nested_planner.py`, `optimizer/join_taxonomy.py`,
  `optimizer/plans.py`, `optimizer/walker.py` | Holding item
  Family `scalar-only-window-projection` | open
- Family `keyset-cursor-column-projection` | Owner
  `optimizer/nested_planner.py::_extend_only_projection` |
  Files `optimizer/nested_planner.py`, `connection.py`,
  `optimizer/plans.py`, `optimizer/lateral_fetch.py` |
  Holding item Family `keyset-cursor-column-projection`
  | open
- Module mechanics (docstring, 23 imports, relay-cap
  re-export) | `optimizer/nested_planner.py` |
  `optimizer/nested_planner.py` | File
  `optimizer/nested_planner.py` | file-local
- Projection walk vs advisory walk (skip-vs-None) |
  `optimizer/nested_planner.py::_concrete_order_columns`
  (rejection recorded here) |
  `optimizer/nested_planner.py` | File
  `optimizer/nested_planner.py` | rejected
- Plan-time coercion vs the shared derivation |
  `optimizer/nested_planner.py::_coerce_pagination_int`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/walker.py`, `utils/connections.py` | File
  `optimizer/nested_planner.py` | rejected
- Planner re-resolution vs validation |
  `optimizer/nested_fetch.py::resolve_strategy` (standing
  hints-R7 / nested_fetch-R1 trigger-checked here) |
  `optimizer/nested_fetch.py`, `optimizer/nested_planner.py`,
  `optimizer/hints.py` | File `optimizer/nested_planner.py`
  | rejected
- Connector shim vs relation-access record | `optimizer/walker.py::_record_relation_access`
  (standing join_taxonomy-R5 trigger-checked here) |
  `optimizer/walker.py`, `optimizer/nested_planner.py`,
  `optimizer/join_taxonomy.py` | File
  `optimizer/nested_planner.py` | rejected
- Attach order vs advisory order |
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
  (standing join_taxonomy-R16 trigger-checked here) |
  `optimizer/join_taxonomy.py`, `optimizer/nested_planner.py`
  | File `optimizer/nested_planner.py` | rejected
- Order-walk name/attname index |
  `optimizer/nested_planner.py::_concrete_order_columns`
  (rejection recorded here) |
  `optimizer/nested_planner.py`, `optimizer/lateral_fetch.py`,
  `optimizer/plans.py` | File `optimizer/nested_planner.py`
  | rejected
- Advisory dedup LRU vs the extension LRUs |
  `optimizer/nested_planner.py::_index_advisory_already_emitted`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/extension.py` | File
  `optimizer/nested_planner.py` | rejected
- Exact-type B-tree gate vs the shared exact-type
  population |
  `optimizer/nested_planner.py::_index_leading_terms`
  (standing J2 trigger-checked here) |
  `optimizer/nested_planner.py`,
  `django_strawberry_framework/_request_body.py` | File
  `optimizer/nested_planner.py` | rejected
- Fail-soft backend probe guard vs the shared except
  population |
  `optimizer/nested_planner.py::_every_backend_supports_index_column_ordering`
  (standing J1 trigger-checked here) |
  `optimizer/nested_planner.py`,
  `django_strawberry_framework/_request_body.py` | File
  `optimizer/nested_planner.py` | rejected
- Synthesized marker vs the window grammar |
  `optimizer/nested_planner.py::relation_connection_to_attr`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `types/finalizer.py` | File `optimizer/nested_planner.py`
  | rejected
- Identity filter vs identity derivation |
  `optimizer/nested_planner.py::_identities_for_response_keys`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/walker.py` | File `optimizer/nested_planner.py`
  | rejected
- Planner merge vs the walker absorb seam |
  `optimizer/nested_planner.py::plan_connection_relation`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/walker.py`, `optimizer/plans.py` | File
  `optimizer/nested_planner.py` | rejected
- Cursor union vs consumer projection |
  `optimizer/nested_planner.py::_extend_only_projection`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/plans.py`, `optimizer/lateral_fetch.py` | File
  `optimizer/nested_planner.py` | rejected
- Planner last-zero refusal vs the resolver tail |
  `optimizer/nested_planner.py::_divergent_key_windows`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `connection.py` | File `optimizer/nested_planner.py`
  | rejected
- Fallback wordings across three media |
  `optimizer/nested_planner.py::_log_connection_fallback`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/plans.py`, `connection.py` | File
  `optimizer/nested_planner.py` | rejected
- Full-flip match vs order reversal rendering |
  `optimizer/nested_planner.py::_terms_serve_order`
  (rejection recorded here) | `optimizer/nested_planner.py`,
  `optimizer/plans.py`, `optimizer/lateral_fetch.py` | File
  `optimizer/nested_planner.py` | rejected
- Sidecar kwargs-arity vs input-arity |
  `utils/connections.py::has_connection_sidecar_kwargs`
  (already one body; held for File `utils/connections.py`)
  | `utils/connections.py`, `optimizer/nested_planner.py`,
  `connection.py` | File `optimizer/nested_planner.py`
  | rejected

## Independent verification (Worker 2)

### W2 trace (recorded BEFORE opening `## Findings`)

Only the `##`/`###` heading list, `Status:`/`Run:` lines, and the file
tail (append anchor) were seen before this trace was written. Family
names below are my own; any resemblance to the artifact's headings is
convergent vocabulary for the same code, not adoption.

#### Subject, fingerprints, and window attribution

- `git rev-parse --short HEAD` = `5ee86193` at W2 start; HEAD unmoved
  throughout the trace.
- Target HEAD bytes:
  `git rev-parse HEAD:django_strawberry_framework/optimizer/nested_planner.py`
  = `b4dfd4a6f61044c6b5dca6ed9fa07d74f52d846d` (1453 lines) — governs.
- Worktree `git hash-object` =
  `225011b691c956a0a6a9dc4a28c40a598b94870a` (+9 vs HEAD: M2M-window
  advisory silence arm in `_advise_composite_index` + docstring
  paragraph). Concurrent-external, never traced; HEAD blob governs.
- Window `git diff --name-only ITEM_BASELINE -- django_strawberry_framework
  tests examples` names exactly `filters/sets.py`, `orders/base.py`,
  `orders/inputs.py`, `tests/filters/test_sets.py`,
  `tests/orders/test_base.py`, `tests/orders/test_inputs.py`. Content
  re-verified hunk by hunk: dunder-consistency hardening
  (`not (meta_fields == "__all__")` + `# noqa: SIM201`), `__class__`-guarded
  `isinstance` arms, `_safe_class_name` adoption, and hostile-declaration
  oracles (`_NeRefusingAllStr`, refusing-`__ne__` collections). All six
  paths are out of this item's scope and all hunks match the concurrent
  hunt's hardening shape; none is Worker 1's. Zero production edits by
  Worker 1 confirmed; the item-scoped diff is the new untracked artifact
  alone. No scope violation.

#### Enumeration (my own instrument and count)

`ast.parse` over the HEAD bytes: 63 `ast.Module.body` nodes = 1 module
docstring + 23 `ImportFrom` + 39 named members. The 39, in order:

1. `_PostgresBTreeIndex` (AnnAssign), 2. `_BTREE_INDEX_TYPES`
   (AnnAssign), 3. `_every_backend_supports_index_column_ordering`,
2. `NestedConnectionPlanResult` (the one ClassDef),
3. `_connector_only_field`, 6. `_order_entry_field_name`,
4. `_concrete_order_columns`, 8. `_select_nested_strategy`,
5. `_concrete_order_terms`, 10. `_index_leading_terms`,
6. `_INDEX_COVERED`, 12. `_INDEX_ABSENT`, 13. `_INDEX_UNKNOWN`,
7. `_terms_serve_order`, 15. `_index_serves_window`,
8. `_plain_field_terms`, 17. `_model_index_shapes`, 18. `_index_coverage`,
9. `_describe_index_columns`, 20. `_MAX_INDEX_ADVISORY_KEYS`,
10. `_IndexAdvisoryKey`, 22. `_index_advisory_seen`,
11. `clear_index_advisory_dedup`, 24. `_index_advisory_already_emitted`,
12. `_advise_composite_index`, 26. `_project_scalar_only_window`,
13. `_extend_only_projection`, 28. `relation_connection_to_attr`,
14. `_relation_connection_to_attr`, 30. `_relation_connection_to_attr_for_key`,
15. `_connection_node_selections`, 32. `_coerce_pagination_int`,
16. `_connection_window_slice_from_arguments`,
17. `_keyset_window_slice_from_arguments`, 35. `_divergent_key_windows`,
18. `_log_connection_fallback`, 37. `_identities_for_response_keys`,
19. `_raw_relation_field`, 39. `plan_connection_relation`.

#### Sites, roles, and definition counts per posited change

Counts below are authoritative definitions forced by the posited change;
consumers / oracles / projections move alongside and are listed, never
counted. All site censuses are package-wide unless noted.

- P1 composite-index advisory (coverage inventory + emission + dedup).
  Posit "admit opclass-aware coverage" and posit "warn per request
  instead of per shape": 1 definition (the planner cluster: items 1-3,
  9-10, 11-13, 14-15, 16-19, 20-25). No second advisory site exists
  (package census for "composite index" / "Advisory only": the planner
  body, `nested_fetch.py` module prose, `plans.py` UNKNOWN-contract
  prose, `docs/README.md` advisory paragraph — all projections /
  consumers). Oracles: `tests/optimizer/test_nested_index_advisory.py`
  (imports `_INDEX_*`, `_advise_composite_index`,
  `_concrete_order_terms`, `_index_coverage`, `_index_leading_terms`,
  `clear_index_advisory_dedup`; pokes `_MAX_INDEX_ADVISORY_KEYS` /
  `_index_advisory_already_emitted` /
  `_every_backend_supports_index_column_ordering` through the module).
  Projection: `docs/README.md` advisory paragraph (incl. the M2M
  two-index sentence — see P34). Owner I would choose: the planner
  (sole writer; narrowest module the one caller already lives in).
- P2 `to_attr` connection-attribute grammar. Posit "add a namespace
  segment": 1 definition (`relation_connection_to_attr`; the two
  underscore delegates are pass-through compat, not definitions).
  Consumers composing by name: `plan_connection_relation` (writer),
  `connection.py` resolve-time readers (via direct
  `optimizer.nested_planner` imports), `walker.py` aliases (kept, no
  reader through the walker). No second grammar spelled anywhere
  (package `_dst_` census: window-annotation constants owned by
  `plans.py`, lateral/single-parent spec attrs, predicate/order alias
  grammars in their own owners — different namespaces, different
  readers). Owner: the planner (writer side; both readers already
  import it; moving the grammar to `connection.py` would reverse the
  plan->resolve dependency).
- P3 window-slice posture (offset adapter vs keyset adapter). Posit
  "treat over-max `first` as fallback instead of malformed": 2 bodies
  move in the same direction (`_connection_window_slice_from_arguments`,
  `_keyset_window_slice_from_arguments`). I count 2 spellings of one
  posture convention and still REJECT consolidation: the shared
  mechanical part (int coercion) is already one body
  (`_coerce_pagination_int`); the remainder is per-vocabulary
  derivation with per-vocabulary error sets, and the keyset half's
  cursor-validation preamble (both cursors validated before bounds so
  strictness cannot mask a malformed `before:` as N+1) is genuinely
  different work with no offset counterpart — a shared driver would
  parameterize preamble + error tuple + derive callable, i.e. the
  adapters with extra steps (principle 5). Reconsideration trigger: a
  third window vocabulary needs the same translate — then the posture
  becomes a driver. Owner of each adapter: the planner (plan-time-only
  thin layers over the shared `utils/connections.py` derive owners;
  the resolver consumes the shared owners directly).
- P4 pagination-int coercion. Posit "accept float-like strings": 1
  definition (`_coerce_pagination_int`). Consumers: both slice adapters
  + `walker.py` divergence normalization (same rule: literal-vs-variable
  window sameness). Owner: the planner (sole definition; the walker
  already imports the planner). Fold vs split: the walker's use serves
  window comparison, so the coercion rides inside my window-slice
  family rather than standing alone.
- P5 strategy selection. Posit "a new strategy kind": 1 definition
  (`nested_fetch.py::resolve_strategy` + registry). The planner's
  `_select_nested_strategy` composes it (re-resolution) and
  `active_strategy` (default). Standing hints-R7 / nested_fetch-R1
  trigger re-checked against HEAD bytes: the call is still unguarded
  (no catch, no branch on failure) — not met; the rejection stands.
  Consumer note on existing family
  `nested-connection-strategy-selection`.
- P6 SKIP gate. Posit "a new skip spelling": 1 definition
  (`hints.py::hint_is_skip`). Consumers: planner (`plan_connection_relation`
  refusal), `walker.py` prefetch-hint acceptance, `extension.py` field
  gate. Consumer note on existing family
  `optimizer-hint-skip-predicate`.
- P7 child-side connector column. Posit "M2M connector becomes the
  through-FK pair": 1 definition
  (`join_taxonomy.py::_parent_join_column`). Consumers: the descriptor
  slot, `prefetch_attach_columns`, the planner shim
  (`_connector_only_field`), the planner advisory read. Standing
  join_tax-R5 trigger re-checked at HEAD (`walker.py::_record_relation_access`
  read end to end): it appends the SOURCE-row local attname to the
  parent plan while connector consumers append CHILD-side columns to
  child projections — no one call site needs both; not met. Standing
  join_tax-R8 trigger re-checked at HEAD: the scalar window's
  unconditional pk (Relay edge identity) is still an adjacent but
  separate `append_unique` from the attach-column append — no two
  reasons collapse; not met. Both rejections stand.
- P8 advisory equality order vs attach order. Standing join_tax-R16
  trigger re-checked at HEAD: `prefetch_attach_columns` still
  connector-first, the advisory still morph-first — neither order's
  owner changed its rule; not met; stands.
- P9 partition key vs lookup path. Standing join_tax-R7 trigger
  re-checked at HEAD: the planner still builds the prefetch lookup via
  `instance_accessor` while `join.partition_expr` carries the query
  name — Django has not unified the vocabularies; not met; stands.
- P10 `.only()`/`.defer()` union extension. Posit "support `.values()`
  masks": 1 definition (`_extend_only_projection`, consuming the shared
  `plans.py::deferred_loading_of` unpack). Consumers: the planner's
  keyset branch + two resolve-time keyset paths in `connection.py` —
  every production consumer loads keyset cursor columns, so the family
  is the keyset cursor-column loader, not a generic projection
  mechanism. Oracles: `tests/test_keyset_connection.py` (direct
  import). Owner: the planner (narrowest module both plan and resolve
  sides already import).
- P11 scalar-only window projection. Posit "add a morph column": 1
  definition (`_project_scalar_only_window`, consuming
  `prefetch_attach_columns` + `_concrete_order_columns`). In-file sole
  caller (`plan_connection_relation`); the walker alias has no reader
  through the walker (documented extraction-compat). The G2-gate
  question in its docstring ("must consult the gate itself") resolves
  clean: `enable_only` IS the threaded G2 verdict
  (`walker.py::_enable_only_for_operation`), so the body consults the
  gate through its parameter — no defect. Owner: the planner.
- P12 advisory dedup LRU vs the extension LRUs. Posit "quarter-sweep
  eviction everywhere": each cache keeps its own policy (advisory:
  single-item `popitem(last=False)` past 512, process-wide shape keys;
  extension doc-key cache: same mechanism, different keys/lifetime;
  extension plan cache: instance-level, quarter-sweep). I REJECT a
  shared LRU driver: different eviction policies, key domains, and
  lifetimes; one driver would need policy flags (principle 5). The
  reset seam matches optimizer convention (extension caches are poked
  directly by `tests/optimizer/test_extension.py`; only declaration
  caches register `register_subsystem_clear`) — no omission.
  Reconsideration trigger: two caches adopt the same
  policy+key-domain+lifetime.
- P13 order-term readers (three contracts). Posit per-reader changes:
  lateral `_order_columns` (renders `field.column` SQL, `None` ->
  downgrade to windowed), `_concrete_order_terms` (coverage
  `(attname, direction)`, `None` -> UNKNOWN silence),
  `_concrete_order_columns` (projection attnames, skip
  unrepresentable) — 1 definition each, no shared body. I REJECT
  cross-consolidation: rendered-SQL-column vs coverage-attname vs
  projected-attname domains, with skip vs fail-None vs
  downgrade postures. The 2-line `by_name`/`attnames` index build
  shared by the two planner siblings counts 2 spellings on a
  "repopulate the index" posit; REJECTED as incidental (each
  contract pins "local concrete" for its own reader; extraction
  would name a thing no third site needs). Trigger: a third
  concrete-index builder appears.
- P14 orchestration. Posit "a new refusal arm": 1 definition
  (`plan_connection_relation` + `NestedConnectionPlanResult` +
  in-file helpers `_divergent_key_windows`,
  `_connection_window_slice_from_arguments`,
  `_keyset_window_slice_from_arguments`, `_log_connection_fallback`,
  `_identities_for_response_keys`, `_raw_relation_field`,
  `_connection_node_selections`). Single production caller (the walker
  adapter, via 8 injected callables); oracles per helper
  (`_divergent_key_windows`, keyset arms in `tests/test_keyset_connection.py`,
  `_select_nested_strategy` + result record in
  `tests/optimizer/test_nested_fetch.py`). Split from window-slice: the
  pure argument->bounds derivation (with its own oracles) earns
  separation from the side-effecting plan assembly — different reasons
  to change (pagination vocabulary vs planning policy). Owner: the
  planner.
- P15 fallback logging. Posit "a new reason vocabulary": 1 definition
  (`_log_connection_fallback` + the in-file reason strings). The
  `plans.py` "falls back to per-parent" exception wordings share WORDS,
  not a rule (observability log vs refusal error — a wording change to
  one need not move the other). REJECTED as cross-media restatement.
  Trigger: a reader parses the log text (then the wording becomes a
  grammar with two halves).
- P16 B-tree exact-type gate. Posit "admit `GinIndex`": 1 definition
  (`_index_leading_terms` + `_BTREE_INDEX_TYPES`, consuming the shared
  `utils/imports.py::import_attr_if_importable` soft-import owner).
  Standing exact-type-gate posture (`_request_body.py` J2, verified):
  per-domain exclusion rules — trigger re-checked (no new foreign
  shape needs exclusion here); not met.
- P17 backend capability probe. Posit "per-alias fetch-time probing": 1
  definition (`_every_backend_supports_index_column_ordering`;
  fail-soft `False`). Oracles pin the all-aliases rule. No second
  backend-capability read package-wide (census).
- P18 index rendering. Posit "render opclasses": 1 definition
  (`_describe_index_columns`). In-file sole caller.
- P19 result record. Posit "carry per-window metadata": 1 definition
  (`NestedConnectionPlanResult`; `accepted` derives from
  `accepted_response_keys`). Request/response separation from
  `nested_fetch.py::NestedConnectionRequest` is by direction (fetch
  input vs plan output), not duplication.
- P20 identity filter. Posit "match on full paths": 1 definition
  (`_identities_for_response_keys`; filters the walker's
  `_resolver_identities_for` derivation, never re-derives).
- P21 raw relation field. Posit "resolve via the field map": 1
  definition (`_raw_relation_field`; `_meta` read for the partition
  derivation's `remote_field` need).
- P22 node-selections adapter. Posit "unwrap change": 1 owner
  (`selections.py::connection_node_children`); the planner adapter
  composes it. Consumer, not a definition.
- P23 order-entry parse. Posit "a new entry spelling": 1 owner
  (`plans.py::order_entry_name_and_direction`); the planner shim
  (`_order_entry_field_name`) + `ends_in_unique_column` + lateral
  `_order_columns` consume. The shim keeps its historical name for its
  caller and test pins — a boundary pin, not a second parse.
- P24 window-bounds derivation. Posit "a new bound rule": 1 owner per
  fork (`utils/connections.py::derive_connection_window_bounds` /
  `derive_keyset_window_bounds`); planner adapters + `connection.py`
  consume. Consumers, not definitions.
- P25 effective order. Posit "a precedence change": 1 owner
  (`plans.py::effective_connection_order`); planner + `connection.py`
  consume (cursor-parity invariant).
- P26 fetch mode. Posit "a new mode": 1 owner
  (`utils/connections.py::FetchMode` + `WindowRangePlan`); planner +
  strategies consume by derivation, never by re-spelling.
- P27 selection observers / field names / response keys. Posit "a
  vocabulary change": 1 owner each (`selections.py`); planner +
  `connection.py` + `extension.py` consume. The planner's
  `_response_keys` import is an alias, not a definition.
- P28 keyset codec. Posit "a cursor version bump": 1 owner
  (`keyset.py` encode + decode halves); the planner decodes only,
  `connection.py` mints/decodes. Round-trip halves co-owned at the
  codec; the planner holds no half.
- P29 child-queryset gate. Posit "a new unwindowable shape": 1 owner
  (`nested_fetch.py::unwindowable_child_queryset_reason`); planner +
  lateral + single-parent strategies consume. Consumer note territory
  on existing family `unwindowable-child-queryset-classification`.
- P30 strategy seam / request record. Posit "a new request field": 1
  owner (`nested_fetch.py::NestedConnectionRequest`); the planner is
  the sole producer, strategies consume. Consumer note territory on
  existing family `nested-fetch-strategy-seam`.
- P31 max-results read. Posit "a new config source": 1 owner
  (`utils/connections.py::relay_max_results_from_info`); the planner
  re-exports the historical private name for the walker alias + test
  pins. Re-export, not a definition.
- P32 soft import. Posit "a new import policy": 1 owner
  (`utils/imports.py::import_attr_if_importable`); planner
  (`BTreeIndex`) + `types/converters.py` + `registry.py` consume.
  Consumer, not a definition.
- P33 instance accessor. Posit "a new accessor rule": 1 owner
  (`utils/relations.py::instance_accessor`); planner lookup +
  walker + finalizer + resolvers + field_meta consume. Consumer.
- P34 M2M advisory shape at HEAD (defect territory, own finding). At
  HEAD bytes `_advise_composite_index` has no relation-kind arm: for
  an M2M join (`through_model` set, connector = related pk attname)
  it recommends a single child-table `(pk, order...)` composite. The
  contract projection (`docs/README.md` advisory paragraph) states an
  M2M "cannot take that single shape" and "needs two indexes".
  Contract row + feasible shape (any M2M nested connection under a
  windowed plan with DEBUG on) + wire input (a Relay M2M connection
  query) all present: a HEAD defect by the GOAL.md trust-boundary
  test. The defective function is concurrently dirtied (+9 silence
  arm), so the defect is observed-not-homed. Separately, the keyset
  adapter's return annotation claims
  `tuple[tuple[int, int | None, bool], KeysetSeek | None] | None`
  while the body returns `(bounds, seek)` with `bounds` a
  `ConnectionWindowBounds` (HEAD-verified:
  `utils/connections.py::derive_keyset_window_bounds` annotates and
  returns `ConnectionWindowBounds`; the caller reads
  `window.reverse`/`window.limit` attributes) — an annotation/body
  mismatch on clean lines, homeable normally.
- P35 module mechanics. The `_relay_max_results_from_info` re-export,
  the `_INDEX_*` tri-state tokens beside their classifier, and the
  `_MAX_INDEX_ADVISORY_KEYS`/`_IndexAdvisoryKey`/`_index_advisory_seen`
  dedup store beside their recorder are not rules of their own; they
  home with the advisory family (tokens/store) or stand as file-local
  mechanics (re-export).

#### Matrix discharge (my own)

1. Cross-flavor policy mirroring: searched `mutations/`, `forms/`,
   `rest_framework/` for `Prefetch(` / planning mirrors — none; those
   flavors own input/output shaping while fetch planning is
   optimizer-owned. `connection.py` / `list_field.py` are the resolve
   side and consume the same shared owners by name (P24-P27), not
   mirrors. Inapplicable with reason.
2. Sync/async twins: `async def` census at HEAD over the target +
   `nested_fetch.py` + `lateral_fetch.py` + `single_parent_fetch.py` =
   0 in all four. Planning is sync-only; async execution reads planner
   outputs off physical window shape by documented invariant, never by
   re-derivation. Inapplicable with HEAD-verified reason.
3. Derived knowledge: `to_attr` single grammar (P2); order-term triple
   (P13, rejected); `pk.attname` readers (P7, standing trigger checked);
   `by_name`/`attnames` index build (P13, rejected as incidental).
   Discharged by census + challenges.
4. Inverse / round-trip pairs: keyset encode/decode co-owned by
   `keyset.py` (P28); offset cursors positional in `connection.py`;
   the planner mints nothing and holds no half. Consumer-only with
   reason.
5. Contracts in another medium: oracles listed per posit above
   (`test_nested_index_advisory.py`, `test_walker.py`,
   `test_keyset_connection.py`, `test_nested_fetch.py`,
   `test_imports.py` prose, `test_plans.py` prose); projections are
   module/test docstrings, the README advisory paragraph, and
   spec-033/035 Decision cites (no GLOSSARY rule prose — censused).
   No contract restated as a second definition; the README-vs-body M2M
   mismatch is filed as a defect (P34), not a consolidation.
6. Enforcement by omission: enumerated the advisory latch (first
   accepted window only — documented, all strategies share the attach
   path), the M2M/GenericRelation/partial-order arms (P34 defect on
   M2M; morph prefix present; UNKNOWN silence present), keyset column
   loading on both scalar-only and edges branches (both present),
   the G2 gate threading (verified, P11), and cache-reset registration
   (optimizer convention uniformly direct — no omission). The seven
   unread-through-walker planner aliases are documented
   extraction-compat kept in `walker.py`; removal is the REOPENED
   walker item's decision, not a defect of this target.

#### My family map (before reconciliation)

Six planner-owned rules (advisory; `to_attr` grammar; window-slice
resolution incl. coercion; scalar-only projection; keyset
cursor-column loader; orchestration), each owned in the planner;
consumptions of existing families (`nested-connection-strategy-selection`,
`optimizer-hint-skip-predicate`, plus the partition / attach-column /
unwindowable / strategy-seam touchpoints) as consumer notes or absorbed
memberships; module mechanics file-local; P3/P12/P13/P15 plus the five
standing triggers as rejections with triggers.

### Findings reconciliation (every difference explicit)

Read order honored: the trace above was complete before `## Findings`
was opened. Converge / diverge per area:

- Family splits (F1-F6): CONVERGE on all six. My map reached the same
  six rules independently: orchestration (P14) vs window-slice (P3/P4)
  earns separation as side-effecting plan assembly vs pure
  pagination-to-bounds derivation (different variation axes, separate
  oracle populations); coercion folds into F2 (its only production
  consumers serve window comparison/derivation — no independent reason
  to change apart); the advisory stays whole (P1 — inventory + emission
  + dedup move as one change unit under a sole-caller latch; splitting
  coverage from emission would strand single-module families);
  `to_attr` (P2) is cross-boundary grammar, not assembly; scalar-only
  (P11) vs keyset loader (P10) split on construction-vs-rewrite
  direction with R1/R13 guarding the boundary, and F6 is correctly
  named by its real consumer population (all three production call
  sites load keyset cursor columns). Six is a lot; each holds >=1
  member under a distinct contract with distinct reasons to change.
  No merge proposed; splits APPROVED.
- E1 (connector shim -> existing `window-partition-resolution`):
  CONVERGE. The shim is 100% consumption of the classifier's
  `parent_join_column` rule; zero production callers re-verified at
  HEAD; join_taxonomy F1's family question (b) on the shim's existence
  verified present (that artifact's "Family-item questions carried"
  lines); no new family owed, no index row owed (plan row already
  lists this file — re-verified).
- E2 (strategy read -> existing
  `nested-connection-strategy-selection`): CONVERGE. Pure consumer
  (re-resolution + default); the standing unguarded-call trigger
  re-checked fresh at HEAD (not met); `active_strategy` sole-caller
  census re-verified at HEAD (this read only); no row owed (plan row
  already lists this file — re-verified).
- My P6/P22/P24-P30 consumptions (SKIP gate, unwrap adapter, bounds,
  order, fetch mode, observers, codec, queryset gate, seam, cap,
  soft-import, accessor): W1 absorbs each as a listed consumption
  inside the homed member (F1/F5 consumer lists + System-trace
  consumer census) rather than filing E-notes. CONVERGE with that
  treatment: E-notes exist only where a whole separate member IS the
  consumption (E1/E2); call-sites inside homed members are correctly
  listed, not separately rowed. My trace's "consumer note territory"
  phrasing was loose; W1's handling is the tighter one.
- My P23 (`_order_entry_field_name`): W1 homes the shim in F5 (its
  only caller's family) while citing plans F-L `order-entry-vocabulary`
  as the composed owner. CONVERGE — homing a single-caller shim with
  its caller is correct; the citation is verified real (that
  artifact's enumeration even names this shim as a consumer).
- R1/R6 (order walks + shared index): CONVERGE. My P13 reached the
  same reject on both; W1's R6 trigger (a change moving the index
  content identically at both sites without touching either policy)
  is tighter than mine — adopted.
- R2 (coercion vs shared derivation): CONVERGE. I had not separately
  posited it; W1's contract difference (plan-time literal vocabulary
  vs resolve-time coerced vocabulary) is verified stated at the
  adapter body, with a real trigger.
- R3/R4/R5 (standing re-resolution / attname-vs-connector /
  attach-vs-advisory): CONVERGE. Each shows the fresh HEAD check, not
  a citation; my independent re-checks agree (all not met).
- R7 (LRU contrast): CONVERGE. My P12 reached the same reject;
  W1's three-contract analysis (emission set vs deterministic memo vs
  instance store) plus the correctly-scoped "exactly like" sentence
  is stronger than my trace.
- R8/R9 (standing exact-type / except-guard): CONVERGE on both
  rejections; R9's trigger sentence is thinner than R8's (recorded
  as observation O2 below, not a gap in the decision).
- R10 (synthesized marker): CONVERGE. I censused the marker but filed
  nothing; W1's rejection is correct and complete (finalizer
  re-entrancy token vs fetch landing grammar, census-verified).
- R11/R13/R15: CONVERGE on all three (filter-vs-derivation with the
  cartesian `[-1]` proof re-verified at HEAD; mask-rewrite-vs-read
  with the 4-consumer unpack census re-verified at HEAD; three-media
  wordings with the test-only-callers claim verified).
- R12 (planner merge vs walker absorb seam): CONVERGE. I had not
  posited it; verified at HEAD (`_absorb_child_plan` is docstring +
  one `merge_metadata_from` call; composing it from the planner would
  reverse the walker-imports-planner edge). Correct rejection.
- R14 (last:0 refusal vs resolver tail): CONVERGE. I had not posited
  it; the resolver tail (`if reverse and limit == 0`, HEAD-verified)
  and the planner arm's "defensive tail for direct callers" statement
  confirm the plan-time-vs-resolve-time contract split.
- R16 (full-flip match vs reversal rendering): CONVERGE. I had not
  posited it; `_reverse_order_by`, lateral `order_sql`, and the plans
  R-1 reversal-split precedent all verified present; predicate-vs-
  rendering is the right contract difference.
- R17 (sidecar arity): CONVERGE. I had not posited it; the
  extract-then-delegate single body verified at HEAD; holding it for
  File `utils/connections.py` matches the join_taxonomy-R3 precedent.
- D1 (M2M advisory): CONVERGE. My P34 reached the same defect
  independently (README row + violated equality-constancy premise).
  W1 adds the pk-leading-vs-terminal mismatch detail. The README quote
  verified verbatim at HEAD; M2M windowability verified (`"many"` in
  `WINDOWABLE_RELATION_KINDS`); the join_taxonomy near-miss-(b) text
  verified present, making the fresh-evidence DIVERGE legitimate (the
  "prose (no behavior)" framing is rebutted: the recommendation IS the
  advisory's behavior). Observed-not-homed is the correct filing: the
  +9 concurrent dirt sits on D1's exact lines, and the closeout
  condition (home only if the concurrent arm does not land, else
  fixed-concurrent) matches the hints/nested_fetch D1 precedent.
  Owner named (this file). No W2 defect filed here — W1's record
  stands as written.
- D2 (keyset annotation): CONVERGE. My P34 reached the same mismatch
  independently. Verified: `@dataclass(frozen=True)` record vs the
  tuple claim; every consumer attribute-accesses (HEAD-verified test
  asserts + planner reads); the sibling's record-over-tuple docstring
  contradicts the stale annotation. Lines HEAD-clean -> normal homing
  on a NAMED card at closeout is correct; minor blast radius (no type
  gate in CI) correctly stated; consistent with the join_taxonomy-D1
  prose-defect precedent. No W2 defect filed — W1's record stands.
- Near-misses (a)-(f): all six re-verified (cartesian safety;
  diverge-guarded attr read with `if not per_key: return False`;
  principled caught sets; dead-on-keyset shared gate via
  forward-only `(0, limit, False)` bounds; shim zero-callers as F1
  family business; `through_model` zero-readers as join_taxonomy F2
  business per that artifact's near-miss (a)). Correctly not filed.
- Standing triggers with no explicit re-check row (join_taxonomy R7
  partition-vs-lookup; join_taxonomy R8 six `pk.attname` readers):
  W1 re-derived both planner-side roles fresh (lookup construction in
  the F1 consumer list; the scalar pk as a separate F5 column class)
  but carries no "trigger checked" sentence for either. I checked both
  fresh at HEAD myself: the planner still builds the lookup via
  `instance_accessor` while `partition_expr` carries the query name
  (R7 not met); the scalar pk is still an adjacent-but-separate
  `append_unique` from the attach append (R8 not met). Both standing
  rejections stand. Recorded here so the cycle record is complete;
  not a coverage gap (both roles are homed) and not verdict leverage.

### Enumeration check (member-by-member, 39/39)

My instrument (`ast.parse` over HEAD bytes) agrees exactly: 63 nodes =
1 docstring + 23 imports + 39 named members. Every member cross-checked
against the artifact's table: F1 7/7 (result, node-selections,
divergent pass, fallback log, identity filter, raw field,
orchestrator), F2 3/3 (coercion + both adapters), F3 20/20 (B-tree
pair, backend probe, terms walk, leading-terms walk, 3 tri-state
tokens, serve-order, serves-window, plain terms, shapes inventory,
coverage, renderer, 3 dedup store members, clear seam, recorder,
emitter), F4 3/3 (canonical + 2 delegates), F5 3/3 (entry shim, order
columns, scalar projector), F6 1/1 (union extender), E1/E2 2/2 (shims
to existing families), L1 (docstring + 23 imports + re-export).
Zero unassigned. The L1 "every imported name has a code read" census
re-verified mechanically over HEAD bytes: 48 imported names, all with
>=1 `ast.Name` load except the `__future__` flag (not a runtime name).

### Matrix judgment (per axis, against the real surface)

1. Cross-flavor: DISCHARGED. Flavor-surface search plus three
   touchpoints verified at HEAD bodies; the `connection.py`
   keyset-adapter composition claim re-verified (both shared predicates
   composed by name); R8/R9 per-domain instances trigger-checked.
   No mirrored second definition — agreed.
2. Sync/async: DISCHARGED with one count correction (C6 below). Zero
   `async def` / zero `await` re-verified at HEAD across the target and
   all three strategy modules; planning is sync-only and async
   execution reads planner outputs off physical shape by invariant.
   "No such surface" is the right call with the stated reason.
3. Derived knowledge: DISCHARGED. Owner-per-derivation mapping matches
   my P22-P33 censuses; R6/R11/R2 carry the investigated candidates
   with triggers. No fact has two derivations — agreed.
4. Round-trip: DISCHARGED. All four pairs verified (request build vs
   `_resolve_from_window` read-back; one-way `$` escape with zero
   unescape sites package-wide, re-verified; keyset mint-vs-decode at
   the codec; single advisory-key site). No pair has two owners.
5. Other media: DISCHARGED with two precision notes (C4/C5/C8 below).
   Oracle population (7 package + 5 live suites) verified present;
   GLOSSARY anchors verified (connection-aware-planning prose incl.
   the window/`to_attr` paragraph; strictness anchor); README rows
   verified; the D1 README row correctly filed as a defect rather
   than counted. No restated definition — agreed.
6. Omission: DISCHARGED with one enumeration correction (C2 below).
   The eight-arm claim re-derived: eight return-arms plus malformed
   bookkeeping plus per-key/per-window fallbacks, every shape firing
   on inspection. No missing guard — agreed; D1 is a wrong firing,
   correctly separated from the omission question.

### Rejection/freshness/pending checks

- All 17 rejections carry a contract difference + reconsideration
  trigger; the 5 standing re-checks (R3/R4/R5/R8/R9) show the actual
  HEAD check except R9's thinner sentence (observation O2).
- Freshness: 26/26 cited blobs re-verified byte-exact via
  `git rev-parse HEAD:<path>` (target, walker, nested_fetch,
  join_taxonomy, hints, plans, selections, extension, lateral,
  connection, utils/connections, keyset, utils/relations,
  utils/imports, resolvers, finalizer, all 7 package suites, 3 live
  suites, README, GLOSSARY, TREE) plus both worktree dirt fingerprints
  where claimed. One cited oracle lacks its blob (correction C8).
- Pending execution: none, with the zero-edit + statically-reasoned
  construction case for the PG/sharded cells. ACCEPTED: no behavior
  changed anywhere, so no cell can distinguish this item; the final
  gate runs the oracles.
- AGENTS.md prose: no process narration (only cycle-standard "Worker 0:"
  homing addresses + CONVERGE/DIVERGE verdict vocabulary, precedented);
  `path::Symbol` citations throughout; no tests added/edited in this
  file item (tier N/A); no `pragma`, no TODO. Ruff: `uv run ruff
  format --check` exit 0 ("1 file already formatted"),
  `uv run ruff check` exit 0 ("No Python files found") on the artifact
  path — the .md artifact is ruff-excluded in effect, recorded.
  `check_trailing_commas.py --check` on the artifact: excluded, exit 0;
  no LINK DEFINITIONS block owed (link-free, matching all three prior
  run-5 file artifacts).
- Probes: none by W1 (all static) and none needed by W2 — every claim
  above was decided by HEAD-bytes reads, AST/package censuses, and
  `git rev-parse` fingerprints. No `temp-tests` scope created, no
  pytest ran, no workspace copy needed (no mutating proof).

### W2 corrections on record (all non-structural; nothing reopens)

- C1 — "Twelve injected callables" (System trace, F1 sites) is wrong:
  the delegation threads exactly EIGHT
  (`resolve_optimizer_hints`, `resolve_relation_target`,
  `response_key_arguments_conflict`, `aliased_arguments_diverge`,
  `target_has_custom_get_queryset`, `resolver_identities_for`,
  `build_child_queryset`,
  `build_prefetch_child_queryset_from_base` — counted from the HEAD
  signature and the walker call site). Read "eight" in both places.
- C2 — Refusal-arm enumeration: the F1 contract's eight-list names
  "divergent-scheme select" (a scheme selector, not a refusal arm) and
  omits the all-windows strategy refusal, while the Matrix axis-6
  eight-list differs (it names malformed + strategy refusal instead).
  Corrected census: eight return-arms (unresolvable target,
  response-key conflict, hint SKIP, missing related model, empty
  per-payload windows, unwindowable join, unwindowable base,
  all-windows strategy refusal) + malformed-keys identity bookkeeping
  (records-and-continues) + per-key/per-window fallbacks
  (sidecar/unwindowable/last:0/strategy-refusal, logged,
  strictness-visible). The axis-6 conclusion (every shape fires) is
  unaffected; the family item audits from this corrected census.
- C3 — "Twelve neighboring owners" (System trace, Judgment) is
  reachable only counting the definition parameter as an owner
  alongside the 10 import-source modules + walker-injected callables.
  Under the strict module convention the count is ELEVEN. The
  underlying consumer lists are complete and verified; only the
  headline number is soft.
- C4 — F2 oracle listing: `tests/optimizer/test_plans.py` never
  imports the planner — its sole adapter mention is a docstring
  (line 1028) on a plans-owned `apply_window_pagination` row. No test
  calls `_connection_window_slice_from_arguments` directly
  (verified). Read the F2 oracles as: keyset adapter direct rows
  (`test_keyset_connection.py`) + offset adapter through
  `_divergent_key_windows`/orchestration rows (`test_walker.py`).
  "Sole caller of both adapters" for the divergent pass still holds.
- C5 — "All spell expectations independently" (System trace) overstates:
  the tri-state advisory rows import `_INDEX_*` tokens from the owner
  and assert coverage results against them (HEAD-verified). Pre-existing
  oracle shape, no rewrite in this zero-edit item, behavior rows stay
  independent — the family item may strengthen those rows.
- C6 — Axis 2 "two `async` tokens" is three at HEAD (comment +
  docstring + comment rationale; lines verified). Zero `async def` /
  zero `await` confirmed; the no-such-surface conclusion stands.
- C7 — "The walker carries aliases for historical test pins" (F4):
  no test or production site imports the `to_attr` delegates via the
  walker (verified); `connection.py` imports them from
  `optimizer.nested_planner` directly. Read "historical aliases, no
  reader through the walker" (documented extraction-compat; removal is
  the REOPENED walker item's decision, not this target's defect).
- C8 — Freshness completion: the cited live keyset oracle
  `examples/fakeshop/test_query/test_keyset_api.py` (verified to
  exercise nested connections over HTTP) is HEAD `305b972f` — owed
  alongside the other three live-suite blobs.
- O1 — See the R7/R8 paragraph under reconciliation: both standing
  triggers independently checked by W2 (not met); recorded for cycle
  completeness.
- O2 — R9's trigger sentence ("Trigger checked against HEAD, not met")
  does not name the checked condition (the J1 condition: a new guard
  needing the same position-state classification). The decision is
  correct (the probe guard is per-domain fail-soft); the sentence is
  just thinner than R8's.

### Defects (Worker 2)

None. W1's D1/D2 are both correctly filed and correctly homed (D1
observed-not-homed with the concurrent-landing closeout condition; D2
for normal closeout homing); my independent trace found no third
production defect. The seven unread-through-walker aliases are
documented extraction-compat in `walker.py` whose removal belongs to
that REOPENED item, not a defect of this target.

### Verdict

`verified` (zero-edit). Coverage complete (39/39 members homed, matrix
discharged on all six axes against the real surface), assignment
correct (six new families each earning separation, two existing-family
convergences correct, one file-local, seventeen rejections each with
contract difference + trigger), both defect filings correct on their
contract rows, no pending execution, nothing tracked touched. Ten
on-record corrections/observations above (C1-C8, O1-O2), none
structural, none reopening. HEAD `5ee86193` unmoved at verdict.

## Run 8 re-trace (Worker-1, scoped re-trace s10)

Prior sections are run-5 evidence only; nothing above is edited.
Every verdict below is decided fresh against HEAD bytes
(`3637dc3a`, 1502 lines, HEAD `83998e08` confirmed before the
first read and after the last — unmoved throughout). No probe
scope was created, no pytest ran, no workspace copy was needed:
every claim is static (AST census, `git show HEAD:` /
`git grep HEAD` reads, `git rev-parse` fingerprints), so no
source-mutating proof exists to route through `workspace.py`.

### Subject, drift, and dirt attribution

- Target `django_strawberry_framework/optimizer/nested_planner.py`:
  HEAD blob `3637dc3afc084c241f22983ff58fa88c3cb33335` (1502
  lines); worktree `e5daffc5eb9602c8f082fa6304ca0e7e89bc228b`
  (1512 lines, 11+/1-); pre-merge bytes
  `d32d1b7bd872b7424d1857ac8c235dac4e765347` at `9aaaad5d`
  (1463 lines; `9aaaad5d` = "dry-0015 pre-ff snapshot", not an
  ancestor of HEAD — read-only evidence, never applied).
- `## Owned changes` names no hunk on this file, so all three
  worktree hunks are concurrent, attributed by diff content vs
  `git show HEAD:`: (1) `from ..utils import truth` plus the
  `truth.name(type(strategy))` fallback rendering — the
  truthful-reads gate work (`utils/truth.py` is untracked
  concurrent work); (2) the M2M silence arm plus docstring
  paragraph in `_advise_composite_index` — D1's fix shape on
  D1's lines, the concurrent session's. The `9aaaad5d` bytes
  carry these same concurrent hunks atop pre-drift code (the
  `last: 0` arm, the `tuple(order_by)` pre-read, the tuple
  annotation, the old re-export comment all present there);
  worktree dirt = HEAD + the same hunks. Nothing traced
  outside HEAD bytes.
- Drift `0c0537e2..HEAD` on this target is five commits. Two
  bear behavior: `dbf0a870` removes the planner's `last: 0`
  fallback arm plus its docstring paragraph (the
  `page_arguments` rewrite windows `last: 0` like `first: 0`
  before anything slices); `10d2b9cd` re-signs the order read
  (`effective_connection_order` takes `child_queryset.query`
  instead of `tuple(child_queryset.query.order_by)`). Three
  are typing-only (`999a1aab`, `b20277fe`, `fef11e64`:
  annotations, casts, `TYPE_CHECKING` imports; `fef11e64`
  nets casts back out) and move no rule ownership — except
  `999a1aab` also fixes D2's annotation (recorded under D2)
  and `b20277fe` rewords the L1 re-export comment (recorded
  under L1).
- Neighbors and oracles were read at HEAD bytes only: the
  worktree dirties `connection.py`, `keyset.py`,
  `list_field.py`, `extension.py`, `hints.py`,
  `join_taxonomy.py`, `nested_fetch.py`, `plans.py`,
  `selections.py`, `walker.py`, `definition.py`,
  `finalizer.py`, `resolvers.py`, `querysets.py`, and
  `relations.py` concurrently, so every body below cites its
  HEAD blob (see Freshness), never the worktree.

### Enumeration (fresh)

Instrument: `ast.Module.body` over the HEAD bytes via
`git show HEAD:` plus an AST dump. Count: 65 nodes =
1 module docstring + 23 `ImportFrom` + 1 `If`
(`TYPE_CHECKING`) + 40 named members (30 `FunctionDef` +
1 `ClassDef` + 6 `Assign` + 3 `AnnAssign`). Every named
member lands below; nothing is unassigned. Delta vs run 5
(63 nodes, 39 members): +1 `If` block holding 13
type-checking-only imports +1 member (`_M`); all 39 prior
names present with identical spelling.

| # | Member | Home |
|---|---|---|
| 1 | Module docstring (transactional-planner contract prose) | L1 (projection; supports F1) |
| 2-14, 16-24 | Plain imports (future, stdlib, Django, graphql-core, keyset, utils.connections, utils.imports, utils.relations, logger, hints, join_taxonomy, nested_fetch, plans, selections) | L1; each consumed |
| 15 | `relay_max_results_from_info as _relay_max_results_from_info` | L1 (REVISED: private internal alias for two reads, no longer a re-export — the walker binds its own) |
| TC | `if TYPE_CHECKING:` block (13 nested imports: MutableSequence, QuerySet, Options, GraphQLResolveInfo, Arguments, CursorColumn, DjangoTypeDefinition, ConcreteField, ModelField, FieldMeta, OptimizerHint, NestedConnectionStrategy, OrderEntry, FieldSelection) | L1 (typing-only mechanics) |
| 25 | `_M = TypeVar(...)` | L1 (typing-only mechanics) |
| 26 | `_PostgresBTreeIndex` | F3 |
| 27 | `_BTREE_INDEX_TYPES` | F3 |
| 28 | `_every_backend_supports_index_column_ordering` | F3 |
| 29 | `NestedConnectionPlanResult` (+ `accepted`) | F1 |
| 30 | `_connector_only_field` | E1 (existing `window-partition-resolution`) |
| 31 | `_order_entry_field_name` | F5 |
| 32 | `_concrete_order_columns` | F5 |
| 33 | `_select_nested_strategy` | E2 (existing `nested-connection-strategy-selection`) |
| 34 | `_concrete_order_terms` | F3 |
| 35 | `_index_leading_terms` | F3 |
| 36-38 | `_INDEX_COVERED`, `_INDEX_ABSENT`, `_INDEX_UNKNOWN` | F3 |
| 39 | `_terms_serve_order` | F3 |
| 40 | `_index_serves_window` | F3 |
| 41 | `_plain_field_terms` | F3 |
| 42 | `_model_index_shapes` | F3 |
| 43 | `_index_coverage` | F3 |
| 44 | `_describe_index_columns` | F3 |
| 45-47 | `_MAX_INDEX_ADVISORY_KEYS`, `_IndexAdvisoryKey`, `_index_advisory_seen` | F3 |
| 48 | `clear_index_advisory_dedup` | F3 (zero production callers, re-verified) |
| 49 | `_index_advisory_already_emitted` | F3 |
| 50 | `_advise_composite_index` | F3 |
| 51 | `_project_scalar_only_window` | F5 |
| 52 | `_extend_only_projection` | F6 |
| 53 | `relation_connection_to_attr` | F4 |
| 54 | `_relation_connection_to_attr` | F4 |
| 55 | `_relation_connection_to_attr_for_key` | F4 |
| 56 | `_connection_node_selections` | F1 |
| 57 | `_coerce_pagination_int` | F2 |
| 58 | `_connection_window_slice_from_arguments` | F2 |
| 59 | `_keyset_window_slice_from_arguments` | F2 |
| 60 | `_divergent_key_windows` | F1 |
| 61 | `_log_connection_fallback` | F1 |
| 62 | `_identities_for_response_keys` | F1 |
| 63 | `_raw_relation_field` | F1 |
| 64 | `plan_connection_relation` | F1 |
| 65 | (node 65 = the `If`; counted above as TC) | L1 |

Homes tally: F1 7, F2 3, F3 20, F4 3, F5 3, F6 1,
existing-family consumers 2, L1 (docstring + 23 imports +
TYPE_CHECKING block + `_M` + relay-cap alias). Tally
identical to run 5 modulo the two typing-only additions.

### Matrix (fresh, HEAD surface)

1. Cross-flavor policy mirroring — SEARCHED, holds. No
   sibling flavor owns fetch-strategy or window-planning.
   The order read now composes one rung deeper: the planner
   passes `child_queryset.query` into
   `plans.py::effective_connection_order`, which composes
   `utils/querysets.py::applied_order` over
   `utils/querysets.py::default_order`; the resolve-time
   tail (`connection.py::_finalize_queryset`) and the list
   offset guard (`list_field.py::_selected_ordering`)
   compose the same owners — composition, not mirroring
   (package-wide `model._meta.ordering` census: exactly one
   read, `querysets.py::default_order`; held for s16, and
   the ladder re-signing for s11). `connection.py:893`'s
   `tuple(queryset.query.order_by)` reads a finalized
   queryset's order for keyset-state comparison, a
   different contract from the Django-compiled default
   read. `_keyset_order_ref` still composes the shared
   entry predicates by name. No mirrored second definition.
2. Sync/async twins — NO SUCH SURFACE, holds. Zero
   `async def`, zero `await` (AST-verified); the three
   `async` tokens are the same prose rationale W2 counted
   (C6), shifted lines only.
3. Derived rather than repeated knowledge — SEARCHED,
   holds with the revised order chain (axis 1). Every other
   derivation still composes its owner by name; the
   investigated candidates (R1/R2/R6/R11) re-verify as
   rejected below. No fact has two derivations.
4. Inverse / round-trip pairs — SEARCHED, three hold, one
   retired. Request build vs `_resolve_from_window`
   read-back, one-way `$` escape (zero unescape sites
   package-wide, re-verified), and keyset mint-vs-decode
   hold. The `last: 0` pair is gone on BOTH sides
   (`dbf0a870` removed the planner arm and the resolver's
   reversed zero-limit branch; `last_zero_quirk` has zero
   package hits): `utils/connections.py::page_arguments`
   single-owns the `last: 0` → `first: 0` rewrite, held
   for File `utils/connections.py` (s15). No pair has two
   owners.
5. Contracts restated in another medium — SEARCHED, holds.
   All 12 cited oracle files exist at HEAD (fingerprints
   below); the advisory suite still counts 66 tests; the
   GLOSSARY planning anchor describes the `first: 0` page
   consistently with the code (projection updated by the
   same commit, no contradiction); the README M2M row is
   verbatim (D1's contract row intact). No restated
   definition.
6. Enforcement by omission — SEARCHED, holds. The eight
   return-arms re-derive exactly per the C2 corrected
   census (unresolvable target, response-key conflict,
   hint SKIP, missing related model, empty per-payload
   windows, unwindowable join, unwindowable base,
   all-windows strategy refusal) plus malformed bookkeeping
   and per-key/per-window fallbacks. Fallback-reason
   census (re-derived — a reason is gone): the divergent
   pass carries exactly two reasons (`sidecar arguments`,
   `unsupported pagination window`) plus the malformed
   channel; the four `_log_connection_fallback` call sites
   carry `conflicting arguments for one response key`,
   the per-key reason passthrough, `malformed pagination`,
   and the strategy-refusal f-string — five strings total,
   `last: 0` gone. The keyset path still shares the pass
   (no offset-only gate); the advisory latch still fires on
   the first accepted window of every strategy; probes
   still run per-key-first with `probe_attr` threading;
   the scalar branch still funnels keyset targets through
   the shared effective order. No member lacks its guard.

### Challenges (fresh, definition counts)

Consumers, oracles, projections listed, never counted. All
counts are authoritative definitions forced by the posited
change, at HEAD bytes.

- Orchestration: ninth refusal arm — 1
  (`plan_connection_relation`); third window scheme — 1
  (selector + `_divergent_key_windows`); new
  strategy-dispatch input — 1 (sole
  `NestedConnectionRequest(` site, re-verified). No second
  planning body (walker delegates; eight injected
  callables, re-verified).
- Per-key window pass: new per-payload gate — 1
  (`_divergent_key_windows`, both schemes inherit); new
  fallback reason — 1 (`_log_connection_fallback` shape;
  vocabulary now five strings, re-derived above).
- Identity recording: new identity vocabulary — 1
  (walker's `_resolver_identities_for`); the planner
  filter follows (R11).
- Slice adapters: new pagination argument — 1 (shared
  `_coerce_pagination_int`, both adapters + the walker
  normalization consumer inherit); new malformed class —
  1 mapping per twin (caught sets unchanged:
  `ValueError`/`TypeError` offset,
  `GraphQLError`/`ValueError`/`TypeError` keyset).
- Advisory inventory/emission: new index shape — 1
  (`_model_index_shapes` arm); new equality-prefix column
  — 1 prefix site + unchanged coverage rule; new
  uninspectable term kind — 1 (`_concrete_order_terms`
  None arm); new B-tree type — 1 (`_BTREE_INDEX_TYPES`);
  new dedup dimension — 1 (`_IndexAdvisoryKey`);
  reworded recommendation — 1 renderer + 1 log call.
- `to_attr` grammar: third scheme — 1
  (`relation_connection_to_attr`; sole builders of both
  `_dst_..._connection` spellings, re-verified);
  alphabet change — 1 escape (zero unescape sites).
- Scalar projection: new column class — 1
  (`_project_scalar_only_window`); advisory-walk
  consumption still rejected (R1).
- Cursor projection: third mask mode — 1
  (`_extend_only_projection`; all three call sites
  re-verified: planner keyset branch + two in
  `_keyset_order_state`); union-into-unpack still rejected
  (R13).
- Connector shim / strategy read: new connector rule — 1
  (taxonomy classifier, E1 follows); new builtin name — 1
  (nested_fetch registry, E2 follows); planner branching
  on resolve failure — standing trigger, not met (R3).
- Last-zero handling: new `last: 0` semantic — 0
  definitions in this file (R14 SUPERSEDED: the rule lives
  once in `page_arguments`, held for s15).
- Default-order read: new Django ordering semantic — 0
  definitions in this file (the planner passes the query
  through; the read lives once in
  `utils/querysets.py::default_order`/`applied_order`,
  held for s16).

### Per-finding verdicts (28/28)

CONFIRM = holds at HEAD modulo line shifts and typing-only
annotation drift. REVISE = holds with a recorded content
change. Citations re-derived at HEAD; `path::Symbol` form.

- F1 `nested-connection-plan-orchestration` — REVISE
  (citation only). Orchestration, eight arms (C2 census
  re-derived verbatim), sole walker caller, merge scheme,
  latch, absorb/identity discipline all hold. Revised:
  the order read now cites
  `optimizer/plans.py::effective_connection_order`
  taking `(cursor_field, query, model)` and composing
  `utils/querysets.py::applied_order` over
  `utils/querysets.py::default_order`; the cursor-parity
  pair (planner + `connection.py::_finalize_queryset`)
  holds with both sites passing the query. Fallback
  vocabulary is five strings (`last: 0` gone). No new
  row: the querysets owners are held for s16, the ladder
  re-signing for s11.
- F2 `plan-time-window-slice-resolution` — REVISE
  (D2 cross-reference struck). Twins, coercion, caught
  sets, cursor pre-validation, `UnwindowableConnection`
  propagation all hold. Revised: the keyset adapter now
  annotates `tuple[ConnectionWindowBounds, KeysetSeek |
  None] | None`, matching the sibling's record-over-tuple
  decision — the "annotation contradicts" parenthetical is
  spent (see D2 CLOSED).
- F3 `composite-index-advisory` — CONFIRM. All 20 members
  intact; chain, tri-state, coverage rule, morph-first
  prefix, dedup, renderer, emission, and the 66-test
  oracle suite hold. D1's lines at HEAD still recommend
  the child-table composite (no `through_model` read).
- F4 `relation-connection-to-attr-grammar` — CONFIRM.
  Sole builders (two f-strings), one-way escape, resolve
  probes per-key-first with `probe_attr` threading, and
  `_check_n1` threading all re-verified.
- F5 `scalar-only-window-projection` — CONFIRM. Column
  set, skip policy, sole caller, attach/entry
  composition, and the G2 threading all hold; its order
  input arrives via the revised ladder (F1 note).
- F6 `keyset-cursor-column-projection` — CONFIRM. Union
  semantics and all three production call sites
  re-verified (planner keyset branch + declared-order
  fast path + `orderBy:` path).
- E1 connector shim — CONFIRM. Body still delegating
  (annotation-only drift); zero production callers and
  the single `test_walker.py` pin re-verified.
- E2 strategy read — CONFIRM. Unguarded re-resolution
  (standing trigger not met) and sole
  `active_strategy()` caller re-verified.
- L1 module mechanics — REVISE. Docstring, 23 imports
  (all consumed), and single-module mechanics hold.
  Revised: (a) the `TYPE_CHECKING` block (13 nested
  imports) and `_M` join L1 as typing-only mechanics;
  (b) the relay-cap import is no longer a re-export —
  `optimizer/walker.py` binds
  `_relay_max_results_from_info` directly from
  `utils/connections.py` and `test_walker.py` imports it
  from the walker, while the planner keeps the historical
  private spelling for its own two internal
  `max_results=` reads. Plan-row edit named below.
- R1 order-walk policies — CONFIRM (skip-vs-None
  contracts intact, both bodies re-read).
- R2 coercion placement — CONFIRM (plan-time literal vs
  resolve-time coerced vocabularies; adapter statement
  intact).
- R3 re-resolution vs validation — CONFIRM (standing;
  unguarded call re-verified, trigger not met).
- R4 shim vs access record — CONFIRM (standing; walker
  still appends source-row `attname`, trigger not met).
- R5 attach vs advisory order — CONFIRM (standing;
  connector-first vs morph-first with the stated
  contrast, trigger not met).
- R6 shared name/attname index — CONFIRM (identical
  two-line index at both walks, policies still
  divergent, trigger intact).
- R7 advisory vs extension LRUs — CONFIRM (three
  contracts intact; race-consequence scoping intact).
- R8 exact-type B-tree gate — CONFIRM (standing; gate
  plus the deliberate `UniqueConstraint` counter-shape
  intact, trigger not met).
- R9 fail-soft probe guard — CONFIRM (standing;
  `except Exception: return False` intact, trigger not
  met).
- R10 synthesized marker — CONFIRM (still
  finalizer-owned re-entrancy token; no namespace
  confusion).
- R11 identity filter vs derivation — CONFIRM (filter
  with "never a re-derivation" + `[-1]`; walker
  cartesian intact).
- R12 planner merge vs absorb seam — CONFIRM (seam still
  rationale + one `merge_metadata_from` call; planner
  direct call intact; trigger not met).
- R13 cursor union vs consumer projection — CONFIRM
  (rewrite-vs-read direction split intact).
- R14 last-zero refusal vs resolver tail — REVISE:
  SUPERSEDED. Both halves are gone at HEAD (planner arm
  + resolver reversed zero-limit branch removed by
  `dbf0a870`; `last_zero_quirk` zero hits): no two
  guards remain to contrast. The rule lives once in
  `utils/connections.py::page_arguments`, oracled by
  the `first: 0` page rows (root, nested, keyset, live
  + package). Held for File `utils/connections.py`
  (s15) to record at the owner. Plan-row edit named
  below.
- R15 fallback wordings — CONFIRM (three-media split
  intact; planner medium now five reasons — noted, not
  a new split).
- R16 full-flip match vs reversal rendering — CONFIRM
  (predicate vs rendering; all three members present).
- R17 sidecar arity — CONFIRM (extract-then-delegate
  single body intact; held for s15 as before).
- D1 M2M advisory — CONFIRM, still OPEN and still
  observed-not-homed. HEAD bytes still lack any
  `through_model` read; README row verbatim at
  `docs/README.md:352`; the worktree still carries the
  concurrent arm on D1's exact lines. Same closeout
  condition: home on a card only if the concurrent arm
  does not land, else fixed-concurrent. Owner unchanged
  (this file).
- D2 keyset annotation — REVISE: CLOSED,
  fixed-committed by `999a1aab`. HEAD annotates the
  `ConnectionWindowBounds` record; every consumer
  attribute-accesses (unchanged). No closeout homing
  owed. Closeout note named below.
- Near-misses: (a) cartesian `[-1]`, (b)
  diverge-guarded attr read, (c) principled caught sets
  — CONFIRM still-not-filed; (d) keyset-never-reverses
  shared gate — MOOT (the arm is removed; the rewrite
  windows `last: 0` like `first: 0`, no dead gate
  remains); (e) shim zero-callers, (f) `through_model`
  zero-readers — CONFIRM still family business
  elsewhere.
- W2 corrections: C1 (eight callables) CONFIRM exact;
  C2 census CONFIRM intact (per-window fallback list
  now sidecar/unsupported-window/strategy-refusal);
  C3 headline count stays soft, underlying lists
  verified (querysets joins as transitive order owner);
  C4 CONFIRM (docstring-only mention, shifted one
  line); C5 CONFIRM (token imports + assertions
  intact); C6 CONFIRM (same three prose tokens); C7
  CONFIRM and extended (no reader through the walker
  for the delegates; the relay-cap alias likewise no
  longer routes via this module); C8 refreshed (live
  keyset oracle now `315c0372`); O1/O2 stand as
  recorded.

Tally: 23 CONFIRM, 5 REVISE (F1 citation, F2 D2-reference,
L1 mechanics, R14 superseded, D2 closed), 0 new families,
0 defects beyond D1.

### Defects (run 8)

D1 persists exactly as filed (observed-not-homed, closeout
condition unchanged). D2 is closed fixed-committed — not a
defect anymore. No new defect found: the typing drift adds
no behavior, the `last: 0` retirement is fully oracled,
and the order re-signing narrows reads onto fewer owners.

### Pending execution

None. All verdicts are static against HEAD bytes; no probe
ran, no pytest ran, no workspace copy was needed. PG and
sharded cells need no execution: the item is zero-edit (no
behavior changed anywhere) and the one alias-touching body
keeps its fail-soft contract unexecuted, as in run 5.

### Freshness (run 8)

HEAD `83998e08` unmoved throughout. Target: HEAD
`3637dc3afc084c241f22983ff58fa88c3cb33335`,
worktree
`e5daffc5eb9602c8f082fa6304ca0e7e89bc228b`,
`9aaaad5d`
`d32d1b7bd872b7424d1857ac8c235dac4e765347`
(pre-ff snapshot = pre-drift code + the same concurrent
hunks; worktree = HEAD + those hunks). Every input below
read via `git show HEAD:` / `git grep HEAD` (worktree
concurrently dirty unless noted clean):

- Neighbors (HEAD short): `walker.py` `bdd9c2f1`,
  `nested_fetch.py` `304e2f3e`, `join_taxonomy.py`
  `6274d9a0`, `hints.py` `f6776564`, `plans.py`
  `fdc4b1b0`, `selections.py` `4127d08a`,
  `extension.py` `6a6465f2`, `lateral_fetch.py`
  `583f6d7b`, `connection.py` `3d6dd424`,
  `utils/connections.py` `735aa454` (clean),
  `utils/querysets.py` `392e50d0`, `utils/imports.py`
  `28d51ced` (clean), `utils/relations.py` `72e7ff08`,
  `keyset.py` `8da76569`, `types/resolvers.py`
  `574e9768`, `types/finalizer.py` `cb2dde6b`,
  `types/definition.py` `5bf257c3`, `list_field.py`
  `77ddb86c`.
- Oracles (HEAD short): `test_nested_index_advisory.py`
  `a6d59a76`, `test_walker.py` `3f5e19a5`,
  `test_keyset_connection.py` `70db0483`,
  `test_plans.py` `df714065`, `test_nested_fetch.py`
  `7fbd957b`, `test_relay_connection.py` `29a2be59`,
  `test_join_taxonomy.py` `481294c3`,
  `test_lateral_fetch.py` `c5aab598`,
  `test_optimizer_auto_api.py` `47e2b003`,
  `test_single_parent_fastpath_api.py` `492fac73`,
  `test_library_shapes_api.py` `fbd38b2a`,
  `test_keyset_api.py` `315c0372`.
- Projections (HEAD short): `docs/README.md` `a3deca98`
  (M2M row verbatim), `docs/GLOSSARY.md` `431ca7ba`
  (planning anchor carries the `first: 0` page prose),
  `docs/TREE.md` `163e364b`.

### Judgment (run 8)

Zero-edit re-trace: the target still single-owns its six
rules with the same member homes (modulo two typing-only
additions), the drift retires one fallback reason and one
rejection (R14) while fixing one defect (D2), and every
other prior verdict re-verifies at HEAD bytes. D1 stays
observed-not-homed on concurrent-owned lines. No
production edit, no test edit, nothing tracked touched
except this artifact.

### Index rows for Worker 0 (run 8; edits only, no new families)

(Worker 0 alone edits the plan; record actions named here.)

- REVISE the R14 plan row (`Planner last-zero refusal vs
  the resolver tail`, File `optimizer/nested_planner.py`,
  rejected) → superseded: both guards removed by
  `dbf0a870`; the `last: 0` → `first: 0` rule lives once
  in `utils/connections.py::page_arguments`, held for
  File `utils/connections.py` (s15).
- CLOSE D2 (`_keyset_window_slice_from_arguments`
  annotation): fixed-committed by `999a1aab`; drop its
  closeout homing.
- EDIT the L1 plan row (`Module mechanics (docstring, 23
  imports, relay-cap re-export)`) → mechanics now
  (docstring, 23 imports, `TYPE_CHECKING` block, `_M`,
  relay-cap internal alias): the walker binds
  `_relay_max_results_from_info` from
  `utils/connections.py` directly; the planner keeps the
  private spelling for two internal reads.
- NOTE on the F1 plan row
  (`nested-connection-plan-orchestration`): the order
  read cites `utils/querysets.py::default_order` /
  `applied_order` transitively via
  `plans.py::effective_connection_order(query)`; owners
  held for s16 (querysets) and s11 (plans). No row split.

## Run-8 verification (Worker 2)

Run: 0.0.15 2026-09-30-8. Required reading included the run-8
author section; nothing in it was adopted — every decisive claim
below was re-derived from `git show` + AST + grep at HEAD bytes
under my own invocation, with my own counts, before judging each
CONFIRM/REVISE. My probe `/tmp/w2_nested_planner_run8_verify.py`
(97 checks, ALL OK) plus end-to-end body reads carry the verdicts;
four first-pass probe mismatches were each investigated to a
byte-level resolution (three were my probe's wrong variable, pin,
and mention assumptions, one is a genuine record catch in
D-W2-R8-1). Zero production edits; this section + the `Status:`
line are the only tracked changes.

### Expectation-first trace

- HEAD `83998e08` unmoved; target HEAD blob `3637dc3a` (1502
  lines), worktree `e5daffc5` (1512 lines), 3 hunks, 11+/1-.
  Pre-merge `9aaaad5d` blob `d32d1b7b` (1463 lines, read-only via
  `git show`, never applied).
- `ast.Module.body` over HEAD bytes: 65 nodes = 1 docstring + 23
  `ImportFrom` + 1 `If` (`TYPE_CHECKING`, node 25) + 40 named
  members (30 `FunctionDef` + 1 `ClassDef` + 6 `Assign` + 3
  `AnnAssign`; `_M` node 26, members 27-65). All 39 run-5 names
  present verbatim + `_M`; the TC block holds 13 statements / 14
  names.
- `0c0537e2..HEAD` touches this target in exactly 5 commits: 2
  behavior-bearing (`dbf0a870`: the divergent-pass `last: 0` arm
  + docstring paragraph removed; `10d2b9cd`: one line,
  `tuple(child_queryset.query.order_by)` →
  `child_queryset.query`) + 3 typing-only (`999a1aab`: TC block,
  casts, the D2 annotation fix; `b20277fe`: signatures, casts,
  `_M`, the L1 comment reword; `fef11e64`: casts netted back
  out). A statement-keyword diff over the three typing commits
  shows only `cast(...)`-wrapped returns otherwise identical —
  no rule moves except the two recorded content changes.
- Dropped shapes: `last: 0` / `last_zero` / `limit == 0` score 0
  in the target at HEAD; `last_zero_quirk` scores 0 files
  package-wide plus tests/examples at HEAD (10 hits at
  `9aaaad5d`, the control); the resolver's
  `reverse and limit == 0` branch scores 0 in `connection.py` at
  HEAD (present at `dbf0a870^`, the control). The `== 0` hits
  surviving in `connection.py` (3) are marker-row serving prose,
  not guards.
- New owners, each confirmed at HEAD with its cited contract:
  `utils/connections.py::page_arguments` (1 def; `last == 0`
  without int `first` → `(0, None)`; neither-int → `(cap,
  last)`; called from both window-bound derivations +
  `connection.py::_consume_fallback` = 3 call sites);
  `utils/querysets.py::default_order` (sole
  `model._meta.ordering` read package-wide, 1 hit) /
  `::applied_order` (explicit else default);
  `optimizer/plans.py::effective_connection_order`
  (`cursor_field, query, model`;
  `deterministic_order(applied_order(query, model), model)`;
  docstring names the shared ladder + cursor-parity invariant).
- The target reads neither querysets owner directly (0 hits) —
  transitive only through the ladder call. The
  `connection.py:893` `tuple(queryset.query.order_by)` reads a
  finalized queryset's explicit order for the keyset fast-path
  comparison — a different contract, re-read in context.

### Per-judgment results (28 rows, my counts)

1. F1 REVISE (citation): ENDORSED. 9 orchestrator returns = the
   8 C2 arms re-derived guard-by-guard
   (1133/1151/1158/1175/1238/1249/1283/1476) + the success
   return; sole caller threads 8 callables + `merge_from`; the
   order call passes `(cursor-or-None, child_queryset.query,
   related_model)` while the resolve tail passes
   `(cursor_field, qs.query, target_model)` (cursor-parity pair
   holds); fallback vocabulary 5 strings with `last: 0` gone.
   Citation-only: the querysets owners and the ladder re-signing
   are correctly held out.
2. F2 REVISE (D2-reference): ENDORSED. Twins, coercion (4 reads
   + the walker consumer), caught sets
   (`ValueError`/`TypeError` vs +`GraphQLError`), cursor
   pre-validation, `UnwindowableConnection` propagation all
   re-read intact; the annotation now matches the sibling's
   record decision (D2).
3. F3 CONFIRM. 20/20 members; inventory, coverage, morph
   prefix, dedup, renderer, emission, and probe bodies re-read;
   66-test suite intact; 0 `through_model` at HEAD.
4. F4 CONFIRM. Sole builders (2 f-strings); one-way escape (0
   unescape sites); resolve probes per-key-first with
   `probe_attr`; `_check_n1` threads the `to_attr` parameter.
5. F5 CONFIRM. `enable_only` gate; pk + attach-complete
   connector set + concrete order columns; skip policy
   re-read; sole caller; order input via the shared ladder.
6. F6 CONFIRM. Union semantics re-read; 3 production call sites
   (`nested_planner.py:1367` + `connection.py:899`/`949`).
7. E1 CONFIRM. Delegating one-call body; 0 production callers;
   single pin (1 test: def + docstring + call, plus the module
   import = 4 exact-symbol lines; the other 14 substring hits
   are the unrelated `_ensure_connector_only_fields`).
8. E2 CONFIRM. Unguarded re-resolution (no try/except);
   `active_strategy()` sole production caller (1); field-static
   docstring intact.
9. L1 REVISE: ENDORSED. 23 imports = 51 names, all with `Name`
   loads; TC block + `_M` typing-only; relay-cap: the walker
   binds from `utils/connections.py` directly (import +
   assignment, 0 reads via this module), `test_walker.py`
   imports it from the walker (3330), the target keeps the
   private spelling for its 2 `max_results=` reads (882/944; 5
   mention lines total incl. import + comment + docstring);
   the comment reword verified in the `b20277fe` diff.
10. R1 CONFIRM (skip-vs-None contracts re-read in both bodies;
    the shared index lines feed divergent policies).
11. R2 CONFIRM (adapter literal-vs-coerced statement intact).
12. R3 CONFIRM (unguarded call re-verified; trigger not met).
13. R4 CONFIRM (walker appends the source-row `attname`,
    re-read; trigger not met).
14. R5 CONFIRM (morph-first vs connector-first re-read on both
    sides; trigger not met).
15. R6 CONFIRM (identical two-line index at both walks;
    policies still divergent; trigger intact).
16. R7 CONFIRM (emission set vs deterministic memo vs instance
    store; `OrderedDict` 2 here + 3 in `extension.py`;
    race-consequence scoping intact).
17. R8 CONFIRM (gate plus the deliberate `UniqueConstraint`
    counter-shape re-read; trigger not met).
18. R9 CONFIRM (`except Exception: return False` re-read;
    trigger not met).
19. R10 CONFIRM (finalizer token, 3 hits; namespaces distinct,
    no confused reader).
20. R11 CONFIRM (filter plus `[-1]` plus the walker's cartesian
    construction re-read).
21. R12 CONFIRM (seam = docstring + one `merge_metadata_from`
    at walker:1479; direct call intact; trigger not met).
22. R13 CONFIRM (mask-rewrite vs `(names, defer_mode)` read
    re-read on both sides).
23. R14 REVISE SUPERSEDED: ENDORSED. Both halves score 0 at
    HEAD (target arm + resolver branch removed by `dbf0a870`;
    quirk 0 files with the `9aaaad5d` control at 10). The rule
    lives once in `page_arguments` (1 def, 3 call sites),
    oracled by `first: 0` rows across root, nested, and keyset
    shapes in live (`test_keyset_api.py`, `test_library_api.py`)
    and package (`test_walker.py:3805`,
    `test_relay_connection.py:1653`/`1689`,
    `test_lateral_pg_parity.py:410`) suites. SUPERSEDED is the
    right disposition over REVISED: no two guards survive to
    contrast, and the trigger (a reversed `last: 0` window
    reaching the resolver) is now impossible by construction —
    the rewrite runs inside both derivations and the fallback
    before anything slices. Held for s15.
24. R15 CONFIRM (three media re-read: target debug log with 5
    reasons; `connection.py` strictness ×2; `plans.py`
    `OptimizerError` wording).
25. R16 CONFIRM (match predicate vs SQL rendering; all three
    members present).
26. R17 CONFIRM (extract-then-delegate single body re-read;
    held for s15 as before).
27. D1 CONFIRM, still OPEN and still observed-not-homed. HEAD
    carries 0 `through_model` reads; the README M2M row is
    verbatim at `docs/README.md:352`; the worktree carries the
    concurrent M2M silence arm on D1's exact lines. Same
    closeout condition (home only if the concurrent arm does
    not land, else fixed-concurrent); owner unchanged.
28. D2 REVISE CLOSED: ENDORSED. HEAD annotates
    `tuple[ConnectionWindowBounds, KeysetSeek | None] | None`
    exactly as D2 demanded; the `999a1aab` diff carries the
    tuple→record change; every consumer attribute-accesses
    (`bounds.offset/limit/reverse` ×2 each at the request-build
    sites, `window.*` in oracles, no `bounds[`/`window[`
    subscript — the `keyed[0]/[1]` subscripts hit the outer
    pair, correctly). Dropping closeout homing is safe: the
    fix is committed at HEAD, nothing remains to home.
- Near-misses: (a)/(b)/(c) CONFIRM still-not-filed (cartesian
  construction, divergent-ternary guard, caught sets — each
  re-read); (d) MOOT endorsed (0 `limit == 0` / `last: 0` in
  the target; the surviving `== 0` hits elsewhere are
  marker-serving prose); (e)/(f) CONFIRM family business
  elsewhere (0 callers / 0 readers re-verified).
- Run-5 corrections: C1 exact (8 callables + `merge_from`); C2
  intact (8 arms re-derived; per-window fallback list now
  sidecar/unsupported-window/strategy-refusal + conflict/
  malformed at the orchestrator); C3 soft headline noted,
  underlying lists verified (+ querysets as transitive order
  owner); C4 (docstring-only at 1027, one line from the run-5
  cite); C5 (token imports + assertions intact); C6 (same 3
  prose tokens); C7 extended (the seven walker aliases have 0
  readers via the walker across package + tests + examples,
  verified over every `from ...walker import` line;
  `test_walker.py:3308` reads `_coerce_pagination_int`
  through the walker's production import, not an alias-block
  name, so the alias comment holds within its stated
  population); C8 refreshed blob verified; O1/O2 stand as
  recorded.

### Hunk attribution (mine, all 3 read end to end)

Net 3 at 11+/1- confirmed. The item-scoped diff is 0 bytes so
every hunk predates the item; no `## Owned changes` row names
this file and zero hunks were authored here — all 3
concurrent-external, conclusively. Content: (1) the
`from ..utils import truth` import (truth-gate work;
`utils/truth.py` untracked `??`); (2) the M2M silence arm + 6
docstring lines in `_advise_composite_index` (D1's lines;
`through_model` ×1 also at `9aaaad5d`, so it predates the
merge); (3) the `truth.name(type(strategy))` fallback
rendering. `9aaaad5d` = pre-drift code (arm + `tuple(order_by)`
pre-read + tuple annotation + old re-export comment, all
verified present) + the same concurrent shapes; worktree =
HEAD + those shapes.

### Record defects (W2, run 8)

One imprecise artifact record; it moves no verdict, index row,
or downstream decision, so no resubmission is owed — the
correction stands here, following the run-7 precedent:

- D-W2-R8-1 (enumeration `#` column order): the table numbers
  `_M` 25 / members 26-64 / the `If` 65. True AST order is the
  `If` at node 25, `_M` at 26, members at 27-65 (verified
  mechanically). Tally (65), member set (40), homes, and TC
  content (13 statements / 14 names) are all correct — the
  index column alone misplaces the `If` last.

### Gate state

- Item-scoped diff 0 bytes (own run). All 33 cited HEAD blobs
  re-hashed identical. Matrix re-discharged per axis against
  the target's real surface: (1) cross-flavor — the order
  chain composes shared owners, 1 `_meta.ordering` read,
  `connection.py:893` a different contract, entry predicates
  composed; (2) sync/async — no such surface (0/0,
  AST-verified, + 3 prose tokens); (3) derived knowledge —
  owner-per-derivation re-derived, R1/R2/R6/R11 carry the
  candidates; (4) round-trip — 3 hold + the `last: 0` pair
  retired on both sides, 0 unescape sites; (5) other media —
  12 oracle files + 66 advisory rows + GLOSSARY `first: 0`
  prose + verbatim README row verified, D1 filed not counted;
  (6) omission — 8 arms + bookkeeping + fallbacks re-derived,
  latch/probes/scalar branch re-read. Every cited oracle
  confirmed present at HEAD with independently spelled
  expectations (the C5 token-import shape stands as recorded
  for the family item). Pending correctly none (static
  verdicts; zero-edit; the alias-touching probe keeps its
  fail-soft contract unexecuted — the same construction case
  as run 5, judged sound).
- Target defects: none. The one item above is a record
  correction, not target behavior. D1 persists as filed; D2
  stays closed; no new family owed; no consolidation missed —
  the behavior drift intersects only the REVISEd rows
  (fallback vocabulary + order citation), everything else is
  annotation/comment.
- Index actions for `docs/dry/dry-0_0_15.md` (4 proposed, all
  judged — I do not edit that file): R14 supersede ENDORSED
  (row 23); D2 close ENDORSED (row 28); L1 edit ENDORSED (row
  9); F1 order-read note ENDORSED (row 1; note, not split —
  the target holds 0 direct querysets reads).
- Family impact: none beyond the four endorsed record actions
  plus evidence carried to s15 (the `page_arguments` rule),
  s16 (the querysets order owners), s11 (the ladder
  re-signing), and s12 (the walker alias prose) — no new
  rows, zero owned changes.
- Verdict: `verified`, zero-edit. HEAD `83998e08` unmoved at
  close. No ruff/mypy owed (artifact `.md` only; probe
  `/tmp`-only).

