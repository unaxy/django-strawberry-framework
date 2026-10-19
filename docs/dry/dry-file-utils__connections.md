# DRY review: `utils/connections.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Target `django_strawberry_framework/utils/connections.py` is the cycle-safe
shared-contracts module between the optimizer planner
(`optimizer/nested_planner.py`, reached via `optimizer/walker.py` delegation)
and the Relay resolver (`connection.py`). It owns the slice-window bounds
derivation (offset engine plus keyset fork), the window-range-to-fetch
derivation (range plan, marker rows, n+1 probe, fetch mode, sentinel split),
the sidecar kwarg family with its presence predicates, the Relay cap ladder,
and the connection supplied-ness spelling. It imports from neither consumer,
so both import it without a cycle.

Attribution. HEAD is `0c0537e2`. Target HEAD blob `f549389e` (797 lines);
worktree blob `efcf749a` (802 lines). `git diff HEAD` shows exactly one hunk
(7+/2-) inside `derive_connection_window_bounds`: cursor presence
`is_supplied(before/after)` becomes `bool(before/after)` with a five-line
comment stating the engine-truthiness reason. ITEM_BASELINE `b1484a8c`
resolves and holds the worktree blob for this path, so the hunk predates
dispatch. No `## Owned changes` ledger row names this file (the ledger covers
the walker D1 fix, six adopted rule hunks in unrelated modules, and six test
gates). The hunk is therefore concurrent-external: traced, never judged,
nothing reverted, nothing built on it. Every verdict below is at HEAD bytes
`f549389e`; the hunk itself is recorded as O2 (observed-not-homed).

Sites found. Every consumer composes by name; the census below was read at
worktree bytes and each cited site verified present at its HEAD blob:

- `connection.py` (HEAD `4894f90f`, worktree `1fca6266` dirty): imports 14
  names. Resolve-time half: `_consume_window` derive dispatch (offset/keyset
  fork on `Meta.cursor_field`), `_resolve_from_window` (range-plan reads,
  `split_window_rows`, `constant_false_shape`), `_resolve_keyset_connection`
  slicer (cap, bound check, quirk compositions), sidecar extraction at three
  pipeline sites, kwarg constants at the field factory, `NEXT_PAGE_PROBE_ROWS`
  at the keyset overfetch.
- `optimizer/nested_planner.py` (HEAD `b4dfd4a6`, worktree dirty): imports 8
  names. Plan-time half: `_connection_window_slice_from_arguments` and
  `_keyset_window_slice_from_arguments` adapters, the per-key sidecar gate,
  the `fetch_mode` to `(with_total_count, next_page_probe)` mapping, and
  `window_range_plan` at range build. Re-exports the cap dig under its
  historical private name for the walker alias and walker tests.
- `optimizer/plans.py` (HEAD `cce98531`, worktree dirty): ORM window renderer;
  `window_range_plan` plus `assert_window_fetch_mode` at
  `apply_window_pagination`.
- `optimizer/lateral_fetch.py` (`db1ea315`, clean): raw-SQL renderer;
  `window_range_plan` plus `assert_window_fetch_mode_for` at
  `LateralWindowSpec.__post_init__`.
- `optimizer/nested_fetch.py` (HEAD `4d8d37a7`, worktree dirty):
  `assert_window_fetch_mode_for` at `NestedConnectionRequest.__post_init__`.
- `optimizer/single_parent_fetch.py` (`e995270a`, clean): `window_range_plan`
  at `single_parent_spec`; counted and reversed shapes refused, input request
  pre-guarded.
- `optimizer/walker.py` (HEAD `75f9c6b6`, worktree dirty): aliases
  `_relay_max_results_from_info` off the planner; delegates planning, no
  direct import.
- Prose projections only: `optimizer/selections.py` (`FetchMode` /
  `fetch_mode`), `exceptions.py` (fetch-mode and bounds contract),
  `keyset.py` (`orderBy:` vocabulary), consumer docstrings.
- Composed owners (this file is the consumer, never a second definition):
  `utils/input_values.py::is_inactive_value`,
  `utils/typing.py::schema_config_from_info`,
  `resource_policy.py::policy_from_info` and `::effective_bound`.
- Engine oracle: strawberry-graphql 0.324.0
  `strawberry/relay/utils.py::SliceMetadata.from_arguments` and
  `StrawberryConfig.relay_max_results = 100`, verified byte-level (`if
  before:` / `if after:` truthiness, `isinstance` gates, exact error texts).
- Test oracles: `tests/utils/test_connections.py` (`65d54027`, clean, 39
  tests over 14 names), `tests/test_keyset.py` (`e5655de7`),
  `tests/test_keyset_connection.py` (`70db0483`),
  `tests/test_relay_connection.py` (worktree `fe2b2d24` dirty),
  `tests/optimizer/test_plans.py` (`1e09d6d8`),
  `tests/optimizer/test_walker.py` (`587cb9f4`), plus the live pagination
  suites the unit module docstring names. `is_supplied`,
  `is_backward_shape`, `is_ambiguous_empty_window`, and
  `NEXT_PAGE_PROBE_ROWS` carry no direct name reference in any test file;
  each is covered transitively through its callers.
- Contract sources: spec-032 Decision 6 (sidecar refusal symmetry), spec-033
  Decisions 4/5 (cursor-parity invariant, per-parent fallback discipline),
  spec-047 Decision 7 (policy ceiling over the Relay cap).

## Verification

### Matrix

1. Cross-flavor policy mirroring: read the sibling flavors before calling any
   concern unique. `list_field.py` owns ordered-offset bounding plus a
   wire-name map for error rendering (different pagination contract, R9; the
   wire map is a different rule over a shared token pair, R6). Filters and
   orders bind `unset_sentinel=UNSET` at their own sites as consumers of the
   one input-values rule (R5). Mutations, forms, and `rest_framework` carry
   no window logic. No second window derivation exists in any flavor.
2. Sync/async twins: the module is pure and uncolored (16 `def`, 0 `async
   def`, no await boundary). Both resolver colors compose the same bodies:
   the sync and async `_resolve` twins both call
   `connection_sidecar_inputs_from_kwargs`, and the uncolored
   `_consume_window` runs the shared derive for both pipelines. No twin pair
   exists to drift.
3. Derived rather than repeated knowledge: the cap ladder
   (explicit/config/engine-default, then policy ceiling) is derived once in
   `resolve_relay_max_results`; the sentinel count is single-sourced in
   `NEXT_PAGE_PROBE_ROWS`; Relay's `sys.maxsize` unbounded sentinel is
   normalized once in `window_range_plan`; `list_field.py` reads the
   published wire name from the executable schema rather than re-deriving it
   here. One site per derivation.
4. Inverse/round-trip pairs: the plan/consume pairs (`window_range_plan`
   with `split_window_rows`, derive with consume) are same-helper by
   construction and colocated in this module. Offset versus keyset is a
   cursor-vocabulary fork with genuinely different algorithms, not a grammar
   with two halves (R3). No separated halves.
5. Contracts restated in another medium: specs are contract sources,
   module and consumer docstrings are projections, tests are independent
   oracles (literal `ConnectionWindowBounds(...)` expectations, never read
   from the owner), and the installed engine source is the external oracle
   for every parity text. Per finding, consumers, oracles, and projections
   are listed, never counted as definitions.
6. Enforcement by omission: enumerated the fetch-mode guard family —
   `NestedConnectionRequest` and `LateralWindowSpec` (both in
   `__post_init__`), `apply_window_pagination` (direct), single-parent
   (pre-guarded input plus counted/reversed refusal, inapplicable by
   construction). Keyset-versus-offset coverage: backward keyset shapes are
   refused via `UnwindowableConnection` while the keyset slicer serves them;
   no member lacks an applicable guard. The `last_zero_quirk` composition
   appears twice inside `connection.py` (O1, routed to open File
   `connection.py`); it is not an omission in this file. No defect.

### Enumeration

Instrument: every name in `ast.Module.body` over HEAD bytes (`git show
HEAD:django_strawberry_framework/utils/connections.py`, 797 lines; the
worktree hunk touches no top-level statement, so the census is identical in
both states). 38 statements: 1 module docstring, 12 imports, 5 assigns, 4
classes, 16 functions — 25 named symbols plus mechanics. `WindowRangePlan`'s
6 members, `FetchMode`'s 4 values, and `ConnectionWindowBounds`' 3 fields
are homed with their records.

| # | Member (HEAD line) | Home |
|---|---|---|
| 1 | `CONNECTION_FILTER_KWARG` (61) | L-sidecar |
| 2 | `CONNECTION_ORDER_KWARG` (62) | L-sidecar |
| 3 | `CONNECTION_ORDER_KWARG_GRAPHQL` (63) | L-sidecar (R6 interplay) |
| 4 | `NEXT_PAGE_PROBE_ROWS` (72) | F-new `window-range-fetch-derivation` |
| 5 | `UnwindowableConnection` (75) | C1 `plan-time-window-slice-resolution` (R7 interplay) |
| 6 | `connection_sidecar_inputs_from_kwargs` (96) | L-sidecar |
| 7 | `is_supplied` (116) | L-supplied (R5 interplay) |
| 8 | `is_backward_shape` (132) | C1 `plan-time-window-slice-resolution` |
| 9 | `has_connection_sidecar_input` (146) | L-sidecar |
| 10 | `has_connection_sidecar_kwargs` (151) | L-sidecar (R1 held confirmation) |
| 11 | `FetchMode` (161) | F-new `window-range-fetch-derivation` |
| 12 | `_is_probe_shape` (201) | F-new `window-range-fetch-derivation` |
| 13 | `is_ambiguous_empty_window` (219) | F-new `window-range-fetch-derivation` |
| 14 | `WindowRangePlan` + 6 members (243) | F-new `window-range-fetch-derivation` |
| 15 | `window_range_plan` (402) | F-new `window-range-fetch-derivation` |
| 16 | `assert_window_fetch_mode` (476) | F-new `window-range-fetch-derivation` (C2 interplay) |
| 17 | `assert_window_fetch_mode_for` (510) | F-new `window-range-fetch-derivation` (C2 interplay, R2) |
| 18 | `split_window_rows` (531) | F-new `window-range-fetch-derivation` |
| 19 | `ConnectionWindowBounds` (595) | C1 `plan-time-window-slice-resolution` |
| 20 | `derive_connection_window_bounds` (608) | C1 `plan-time-window-slice-resolution` |
| 21 | `_RELAY_MAX_RESULTS_DEFAULT` (693) | C1 `plan-time-window-slice-resolution` (R8 interplay) |
| 22 | `assert_relay_pagination_bound` (701) | C1 `plan-time-window-slice-resolution` (R8 interplay) |
| 23 | `relay_max_results_from_info` (721) | C1 `plan-time-window-slice-resolution` (R4 interplay) |
| 24 | `resolve_relay_max_results` (739) | C1 `plan-time-window-slice-resolution` (C3 interplay) |
| 25 | `derive_keyset_window_bounds` (761) | C1 `plan-time-window-slice-resolution` (R3 interplay) |
| L0 | Module docstring + 12-import block | File-local mechanics |

Homes tally: C1 9, F-new 9, L 7 plus mechanics, C2/C3 interplay with 0
homed. 25/25 homed, 0 unassigned.

### Challenges

Each rule, changes posited on its variation axes, authoritative definitions
counted (consumers, oracles, projections listed, never counted):

- Slice-window bounds (C1). New offset pagination shape (a further
  `SliceMetadata` classification arm): 1 definition
  (`derive_connection_window_bounds`; the two plan-time adapters and the
  resolve-time dispatch are consumers). Keyset backward planning in v2: 1
  definition (the refusal arm in `derive_keyset_window_bounds`; the slicer
  already serves the shape). Cap-precedence change: 1 definition
  (`resolve_relay_max_results`; policy ladder and config dig are composed
  owners). Bound-text change: 1 definition per text
  (`assert_relay_pagination_bound` for `first`/`last`, the adjacent
  `TypeError` pair for forged-negative cursors; engine is the external
  oracle). Core shape change (`last`-int rule): 1 definition
  (`is_backward_shape`; quirk compositions stay at their call sites).
- Window-range fetch (F-new). A new ambiguous shape: 1 definition
  (`is_ambiguous_empty_window`; renderers and the resolver consume the
  marker flag). A fifth fetch mode: 1 definition (the `FetchMode` value plus
  its `fetch_mode` arm; the planner's boolean mapping is a consumer). Probe
  eligibility change: 1 definition (`_is_probe_shape`; plan builder,
  record predicate, and observer mapping all read it). Sentinel count 1 to
  2: 1 definition (`NEXT_PAGE_PROBE_ROWS`; both domains' flag derivations
  read the constant or the rows). Sentinel-exclusion change: 1 definition
  (`split_window_rows`; sole consumer is the resolver). Probe/count
  exclusion change: 1 definition (`assert_window_fetch_mode`; the `_for`
  arity delegates through the shared plan builder).
- Sidecar family (L-sidecar). A third sidecar (e.g. `search`): the named-pair
  signature plus both predicates move as 1 rule cluster, surfacing
  deliberately at each destructuring consumer (docstring-stated). Kwarg
  rename: 1 cluster (constants plus extraction). Camelization default flip:
  already recognized (twin constant plus fallback read, no second spelling
  anywhere; census: `CONNECTION_ORDER_KWARG_GRAPHQL` has no reader outside
  this module and its unit oracle).
- Supplied-ness (L-supplied). A third inactive spelling for connection
  surfaces: 1 definition (`is_supplied`; census: zero raw `UNSET`
  comparisons remain in `connection.py` or `nested_planner.py`).
- Arity pairs (R1, R2). Input-shape change for either pair: 1 body (each
  `_for`/`kwargs` arity delegates to its input arity after one mechanical
  step).
- Offset/keyset fork (R3). Cursor-vocabulary-neutral slice engine: the only
  change that would merge the twins; no such engine exists, and every
  shareable part (cap, bound check, shape test, record, signal) is already
  shared.
- Dig versus resolve (R4). Planner no longer needing `None`
  distinguishable: the only change merging the pair; the `None` contract is
  load-bearing today (engine-default passthrough versus terminal default).
- UNSET bindings (R5). A change moving every binding together: none exists;
  each family binds the shared rule for its own subject (filters
  load-bearing at many sites, orders defensive-inert via traversal config,
  connections via the single `is_supplied`).
- Wire-name twin (R6). A shared wire-name grammar owner: none exists; the
  recognition constant and the error-rendering fallback map change for
  different reasons.
- Fallback signal (R7). Walker unifying fallback with malformed paths: the
  only change merging the signal into the error taxonomy; the catch
  separation is load-bearing for strictness visibility.
- Engine-text mirrors (R8). Engine rewording a text: this file re-decides
  parity per text as a consumer; the triggers differ (prefix mismatch in the
  engine, forged-negative index here), so the shared wording is not a shared
  rule.
- Ordered-offset bounding (R9). Unifying cursor and offset pagination into
  one contract: no such contract exists; `list_field.py` bounding (ordered
  offset, no cursors, no tiebreaker) and Relay window derivation vary
  independently.

## Findings

### C1 — Converge onto open `plan-time-window-slice-resolution`

Contract: the shared pagination-arguments-to-window derivation both the
plan-time adapters and the resolve-time pipeline compose — the offset engine
run (`derive_connection_window_bounds`), the keyset fork
(`derive_keyset_window_bounds`), the `(offset, limit, reverse)` record
(`ConnectionWindowBounds`), the valid-but-unplannable signal
(`UnwindowableConnection`), the backward-shape core (`is_backward_shape`),
the keyset bound-check wording (`assert_relay_pagination_bound`), and the
cap ladder (`relay_max_results_from_info`, `resolve_relay_max_results`,
`_RELAY_MAX_RESULTS_DEFAULT`). Varies over pagination vocabulary, cursor
kind, error mapping, and cap precedence.

Sites and roles: definitions here (9 symbols, HEAD `f549389e`); plan-time
adapter consumers in `optimizer/nested_planner.py`
(`_connection_window_slice_from_arguments`,
`_keyset_window_slice_from_arguments`, the per-key gate); resolve-time
consumers in `connection.py` (`_consume_window`, `_resolve_from_window`,
`_resolve_keyset_connection`); the walker delegates without importing.
Oracles: unit bounds/wording/cap tests plus the live pagination suites.
Projections: spec-033 Decisions 4/5, spec-047 Decision 7, consumer
docstrings. The family row already lists this file; this item homes the 9
symbols into it and proposes no boundary change. Owner stays
`optimizer/nested_planner.py::_connection_window_slice_from_arguments` with
the `_keyset_` twin and `_coerce_pagination_int`; the family item decides
whether the shared derivation keeps its cycle-safe home (recommended: the
import cycle forces it) with a gate, or moves.

### C2 — Converge (interplay only) onto open `nested-fetch-strategy-seam`

The seam's guard and parameter vocabulary are enforced and threaded here but
defined by the window-range-fetch rule (F-new): `assert_window_fetch_mode`
at `apply_window_pagination`, `assert_window_fetch_mode_for` at both seam
record constructors, `window_range_plan` at the planner and all three
backends. No symbol is homed into the seam; the family row already lists
this file as interplay. The family item reads the enforcement sites, owns
nothing here.

### C3 — Converge (interplay only) onto open `policy-authority-isolation`

`resolve_relay_max_results` reads `policy_from_info(info).max_page_size`
(a per-operation copy) as a ceiling through `effective_bound`: a pure
consumer read, no policy defined, no authority held. The policies artifact
already classifies this file as indirect at exactly this HEAD. No symbol is
homed into the family; no boundary change proposed.

### F-new — `window-range-fetch-derivation` (name for Worker-0)

Contract: the pure slice-to-fetch derivation shared by the planner, both
renderers, the single-parent fast path, and the resolver — range bounds and
`sys.maxsize` normalization (`window_range_plan`), the range record and its
fetch/mode predicates (`WindowRangePlan` plus `_probe_increment`,
`fetch_upper_bound`, `fetch_limit`, `probe_shape`, `constant_false_shape`,
`fetch_mode`), the probe-shape predicate (`_is_probe_shape`), the ambiguous
marker predicate (`is_ambiguous_empty_window`), the count/probe policy
(`FetchMode`), the probe/count exclusion boundary
(`assert_window_fetch_mode` plus the raw-args `_for` arity), the sentinel
exclusion (`split_window_rows`), and the single-sourced sentinel count
(`NEXT_PAGE_PROBE_ROWS`). Varies over window shape, selection observers,
renderer dialect, and pagination domain (offset window versus keyset value
page). Sub-rule candidates for the family item to decompose: range
normalization, marker policy, probe policy, fetch-mode policy, sentinel
split, exclusion boundary.

Sites and roles: definitions here (9 symbols, HEAD `f549389e`);
`WindowRangePlan(` constructed once, `window_range_plan` consumed at 4
plan/render sites; `split_window_rows` consumed once (resolver); the
sentinel constant consumed twice (window `_probe_increment`, keyset
overfetch). Consumers: planner mapping, ORM renderer, lateral renderer,
single-parent spec, resolver split and flag derivation. Oracles: probe,
marker, mode, and split unit tests plus live pagination suites.
Projections: the record and enum docstrings, renderer comments.

Challenges: see `### Challenges` (window-range fetch): every posited change
counts 1 definition. The family item's sharpest question is the gate: owner
already single, so the finding is gate-or-reject — the plausible bypass is
a renderer re-deriving `offset + limit` inline instead of reading the plan
(the lateral dialect already carries the warning comment), and the gate
must be shown green before it is adopted. Owner candidate:
`utils/connections.py::window_range_plan` with the record (the narrowest
cohesive home every consumer already imports). No stored derivation, so no
principle-4 lifetime fields.

### L-sidecar — Connection sidecar kwarg family (file-local)

The kwarg names in both vocabularies (3 constants), the single extraction
(`connection_sidecar_inputs_from_kwargs`, both order spellings), and both
presence predicates (`has_connection_sidecar_input`,
`has_connection_sidecar_kwargs`). One rule cluster: the refusal symmetry
between the walker's plan-time gate and the resolver's consume-time gate
(spec-032 Decision 6). Challenge: a third sidecar moves the cluster as one
and surfaces deliberately at each destructuring consumer; no second spelling
exists (census above). The kwargs/input arity split is the held R1
confirmation, not a second definition.

### L-supplied — Connection supplied-ness spelling (file-local)

`is_supplied` is the connection surfaces' single spelling of the
package-active-input rule with the `UNSET` sentinel bound here (the rule
itself stays in `utils/input_values.py`, which deliberately imports no
strawberry). Challenge: the formerly 15 hand-written inverse sites across
the two connection modules now route through this one body — census finds
zero raw `UNSET` comparisons in either. Sibling-family bindings are R5, not
second definitions of this subject.

### L0 — Module mechanics (file-local)

Module docstring (the two-contract statement plus the coercion non-ownership
clause) and the 12-import block (7 stdlib/typing, engine `SliceMetadata`,
4 package edges, all consumed). No re-export, no `__all__`, no lazy cycle
break.

### R1 — Sidecar kwargs-arity versus input-arity (rejected, held confirmation)

`has_connection_sidecar_kwargs` delegates to `has_connection_sidecar_input`
after one extraction (HEAD lines 151-158, body-verified): two call shapes,
one read body, already shared. Confirms the held rejection recorded under
File `optimizer/nested_planner.py` (R17). No consolidation to propose;
reconsideration trigger: a kwargs-shaped caller needing different
presence semantics than the input-shaped gate.

### R2 — Fetch-mode assert arity (rejected, already one body)

`assert_window_fetch_mode_for` resolves the shared plan and delegates to
`assert_window_fetch_mode`: same arity-pair shape as R1 over a different
rule. The effective-state exclusion is spelled once. Trigger: a raw-args
carrier needing different normalization than `window_range_plan`.

### R3 — Offset/keyset derive twins (rejected, vocabulary fork)

The bounds derivation forks before the offset engine because a keyset cursor
is not an offset: genuinely different algorithms (slice metadata versus
forward-only arithmetic with backward refusal), with every shareable part
already shared (cap ladder, bound check, shape core, record, signal).
Trigger: a cursor-vocabulary-neutral slice engine both forks could run
through.

### R4 — Cap dig versus cap resolve (rejected, distinct contracts)

`relay_max_results_from_info` preserves `None` (planner needs "no cap
configured" distinguishable for engine-default passthrough);
`resolve_relay_max_results` lands on a terminal number (resolver must bound
a page). The difference is the whole contract, docstring-stated. Trigger:
the planner no longer needing the `None` leg.

### R5 — UNSET bindings across families (rejected, consumers of one rule)

Filters bind `UNSET` at many sites (load-bearing), orders via traversal
config (defensive-inert), connections once via `is_supplied`: three
consumers of the one `is_inactive_value` rule, each varying with its own
subject's input shaping. No change moves all bindings together. Trigger: a
fourth inactive spelling or a binding migration that must touch every family
at once (the open File `utils/input_values.py` sweep re-checks this).

### R6 — GraphQL order twin versus list-field wire map (rejected)

`CONNECTION_ORDER_KWARG_GRAPHQL` recognizes the sidecar in raw selection
arguments; `list_field.py::_DEFAULT_WIRE_NAMES` renders a fallback wire
name for list-field errors (the primary read is the published schema map).
Shared token pair, different rules and reasons to change. Trigger: a shared
wire-name grammar owner both seams are migrated onto.

### R7 — Fallback signal versus error taxonomy (rejected)

`UnwindowableConnection` is a control-flow signal for valid-but-unplannable
shapes, deliberately outside `ValueError`/`TypeError` (malformed, caught to
leave-unplanned-but-accounted) and outside `OptimizerError`/`GraphQLError`
(planner bug / consumer-visible error). The walker catch separation keeps
the fallback strictness-visible; merging the types would collapse that
distinction. Trigger: the walker unifying the fallback and malformed paths.

### R8 — Engine-parity mirrors (rejected, consumer relationship)

`_RELAY_MAX_RESULTS_DEFAULT = 100` mirrors `StrawberryConfig`'s default and
the forged-negative-cursor `TypeError` texts mirror the engine's
malformed-cursor wording (both verified byte-identical against
strawberry-graphql 0.324.0). Each is single-spelled here with the engine as
external oracle; the triggers differ (prefix mismatch in the engine versus
forged-negative index here), so the shared wording is parity, not a shared
rule. Trigger per text: the engine rewording it, which re-opens the parity
decision rather than a consolidation.

### R9 — Ordered-offset bounding versus Relay window derivation (rejected)

`list_field.py` bounding (ordered offset, no cursors, no pk tiebreaker, no
`DISTINCT`, policy-bounded skip) and this module's cursor-window derivation
are different pagination contracts that vary independently (a tiebreaker or
cursor rule moves one, never the other). Trigger: a unified pagination
contract both surfaces are migrated onto.

### O1 — `last_zero_quirk` pair in `connection.py` (observed, routed)

The composition `is_backward_shape(first, last) and last == 0 and not
<before-absent>` is spelled at two `connection.py` sites (the per-parent
offset tail and the keyset slicer) with before-absence spelled inline at
one and via a local at the other — semantically identical. Both sites live
in open File `connection.py` (REOPENED, undispatched), which owns the pair;
this file provides only the shared core. No verdict from this item, no
defect filed, no family named (a within-one-file pair is that file item's
to home).

### O2 — Worktree cursor-presence hunk (observed-not-homed, concurrent)

The 7+/2- worktree hunk re-spells offset-twin cursor presence from
`is_supplied` to engine-truthiness `bool()`, explicitly diverging the
offset twin from the keyset twin (which keeps `is_supplied`) at worktree
bytes. It is concurrent-external (see System trace): all verdicts above are
at HEAD bytes, where both twins share the `is_supplied` reading. The hunk's
author owns the split and its tests. No defect filed — homing it here would
double-home in-flight work.

Freshness. Target verdict basis HEAD `f549389e`; worktree `efcf749a`;
ITEM_BASELINE `b1484a8c`; HEAD `0c0537e2` (re-verified after the trace, no
movement). Connected files inspected at worktree bytes, each cited site
verified present at its HEAD blob: `connection.py` HEAD `4894f90f` /
worktree `1fca6266`, `optimizer/nested_planner.py` `b4dfd4a6` / dirty,
`optimizer/plans.py` `cce98531` / dirty, `optimizer/lateral_fetch.py`
`db1ea315` clean, `optimizer/nested_fetch.py` `4d8d37a7` / dirty,
`optimizer/single_parent_fetch.py` `e995270a` clean, `optimizer/walker.py`
`75f9c6b6` / dirty, `optimizer/selections.py` `a48f6172` / dirty,
`keyset.py` `df4b5e2f` / dirty, `utils/input_values.py` `f2566609` /
dirty, `utils/typing.py` `de6309f6` / dirty, `resource_policy.py`
`4b69e974` / dirty, `exceptions.py` `e06b0b7f` / dirty, `list_field.py`
`21380eb7` / dirty. Oracles: `tests/utils/test_connections.py` `65d54027`
clean, `tests/test_keyset.py` `e5655de7` clean,
`tests/test_keyset_connection.py` `70db0483` clean,
`tests/test_relay_connection.py` worktree `fe2b2d24` dirty,
`tests/optimizer/test_plans.py` `1e09d6d8` clean,
`tests/optimizer/test_walker.py` `587cb9f4` clean. Engine:
strawberry-graphql 0.324.0. Excluded on body strength after full reads:
`keyset.py` (codec/seek/fingerprint, no bounds derivation),
`utils/typing.py` and `utils/input_values.py` (composed owners, consumed by
name), `list_field.py` (ordered-offset contract, R9).

## Defects

None. O1 is routed to its owning open item and O2 is concurrent work in
flight; neither is a defect of this target.

## Judgment

Zero-edit file item: 25/25 symbols homed (9 converged onto open
`plan-time-window-slice-resolution`, 9 named into new
`window-range-fetch-derivation`, 7 plus mechanics file-local), 9 rejections
(one held confirmation), 2 routed observations, no defects, no consolidation
(the item fences it), no production or test edits, no plan edits. The target
is already the single owner of every rule it defines; every open family
naming it converges without a boundary change.

## Index rows for Worker-0

New family (for `## Families` plus its `## Responsibility index` row):

- Family `window-range-fetch-derivation` | Owner candidate
  `django_strawberry_framework/utils/connections.py::window_range_plan`
  (with `WindowRangePlan`) | Files
  `django_strawberry_framework/utils/connections.py`,
  `django_strawberry_framework/connection.py`,
  `django_strawberry_framework/optimizer/nested_planner.py`,
  `django_strawberry_framework/optimizer/plans.py`,
  `django_strawberry_framework/optimizer/lateral_fetch.py`,
  `django_strawberry_framework/optimizer/nested_fetch.py`,
  `django_strawberry_framework/optimizer/single_parent_fetch.py` | Holding
  item Family `window-range-fetch-derivation` | open (named by File
  `utils/connections.py` F-new; gate-or-reject: owner already single,
  plausible bypass is a renderer re-deriving bounds inline)

Convergences onto open families (no new rows; files-covered already list
this file — recorded here so Worker-0 can confirm the homing):

- `plan-time-window-slice-resolution`: homes 9 definitions from this file
  (`derive_connection_window_bounds`, `derive_keyset_window_bounds`,
  `ConnectionWindowBounds`, `UnwindowableConnection`, `is_backward_shape`,
  `assert_relay_pagination_bound`, `relay_max_results_from_info`,
  `resolve_relay_max_results`, `_RELAY_MAX_RESULTS_DEFAULT`); no boundary
  change proposed.
- `nested-fetch-strategy-seam`: interplay only (guard enforced and plan
  threaded at the seam; definitions stay in `window-range-fetch-derivation`).
- `policy-authority-isolation`: interplay only (indirect consumer via
  `policy_from_info` copies, as the policies artifact already records).

File-local rows:

- `connection-sidecar-kwarg-family` |
  `django_strawberry_framework/utils/connections.py::connection_sidecar_inputs_from_kwargs`
  (with the 3 kwarg constants and both presence predicates) |
  `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | file-local
- `connection-supplied-ness-spelling` |
  `django_strawberry_framework/utils/connections.py::is_supplied` |
  `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | file-local
- `connections-module-mechanics` |
  `django_strawberry_framework/utils/connections.py` (docstring + import
  block) | `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | file-local

Rejection rows:

- `sidecar-kwargs-arity-vs-input-arity` |
  `django_strawberry_framework/utils/connections.py::has_connection_sidecar_kwargs`
  (already one body; confirms the held File `optimizer/nested_planner.py`
  R17) | `django_strawberry_framework/utils/connections.py`,
  `django_strawberry_framework/optimizer/nested_planner.py`,
  `django_strawberry_framework/connection.py` | File `utils/connections.py`
  | rejected
- `fetch-mode-assert-arity` |
  `django_strawberry_framework/utils/connections.py::assert_window_fetch_mode_for`
  (already one body via the shared plan builder) |
  `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | rejected
- `offset-keyset-derive-fork` |
  `django_strawberry_framework/utils/connections.py::derive_keyset_window_bounds`
  (cursor-vocabulary fork; shared parts already shared) |
  `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | rejected
- `cap-dig-vs-cap-resolve` |
  `django_strawberry_framework/utils/connections.py::relay_max_results_from_info`
  (`None`-preserving dig versus terminal-default resolve, distinct
  contracts) | `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | rejected
- `unset-bindings-across-families` |
  `django_strawberry_framework/utils/connections.py::is_supplied`
  (consumers of the one input-values rule, not definitions) |
  `django_strawberry_framework/utils/connections.py`,
  `django_strawberry_framework/filters/inputs.py`,
  `django_strawberry_framework/filters/sets.py`,
  `django_strawberry_framework/orders/sets.py`,
  `django_strawberry_framework/utils/input_values.py` | File
  `utils/connections.py` | rejected
- `graphql-order-twin-vs-list-wire-map` |
  `django_strawberry_framework/utils/connections.py::CONNECTION_ORDER_KWARG_GRAPHQL`
  (recognition constant versus error-rendering fallback map) |
  `django_strawberry_framework/utils/connections.py`,
  `django_strawberry_framework/list_field.py` | File `utils/connections.py`
  | rejected
- `unwindowable-signal-vs-error-taxonomy` |
  `django_strawberry_framework/utils/connections.py::UnwindowableConnection`
  (control-flow signal; walker catch separation load-bearing) |
  `django_strawberry_framework/utils/connections.py`,
  `django_strawberry_framework/optimizer/nested_planner.py`,
  `django_strawberry_framework/optimizer/walker.py` | File
  `utils/connections.py` | rejected
- `relay-parity-text-mirrors` |
  `django_strawberry_framework/utils/connections.py::_RELAY_MAX_RESULTS_DEFAULT`
  (engine-parity mirrors with differing triggers; engine is the external
  oracle) | `django_strawberry_framework/utils/connections.py` | File
  `utils/connections.py` | rejected
- `ordered-offset-vs-relay-window` |
  `django_strawberry_framework/utils/connections.py::window_range_plan`
  (different pagination contracts) |
  `django_strawberry_framework/utils/connections.py`,
  `django_strawberry_framework/list_field.py` | File `utils/connections.py`
  | rejected

## Independent verification (Worker-2)

Expectation-first trace (recorded before reading Findings; reconciled
after). From the target at HEAD bytes plus consumer reads I expected:
(a) 38 top-level statements / 25 named symbols; (b) a sidecar cluster
(3 constants + extraction + 2 predicates) with the kwargs/input arity
pair already one body per the held nested_planner R17; (c) a
slice-derivation cluster converging onto open
`plan-time-window-slice-resolution`; (d) a window-range/fetch cluster
(FetchMode, range plan + builder, marker/probe predicates, exclusion
asserts, split, sentinel count) with consumers in connection.py, the
planner, both renderers, the seam records, and single-parent; (e) the
worktree hunk as pre-baseline concurrent dirt (ITEM_BASELINE holds the
worktree blob); (f) `is_supplied` as the single UNSET-binding for
connection surfaces. Every expectation reconciled with no difference
except the record corrections C-W1..C-W4 below, none structural.

(1) Enumeration: STANDS. Own AST over `git show HEAD:...` gives 38
statements (1 docstring + 12 imports + 5 assigns + 4 classes +
16 functions, 0 async) = 25 named symbols; all 25 homes verified
member by member (C1 9, F-new 9, L-sidecar 6, L-supplied 1, L0
mechanics). Record counts (6/4/3 members, 14 connection.py
imports, 8 planner imports, 39 tests, 20/20 freshness blobs) all
re-verified exact.

(2) Hunk attribution: STANDS. ITEM_BASELINE `b1484a8c` is a WIP stash
commit whose tree holds worktree blob `efcf749a` for this path;
worktree-vs-baseline diff is empty; HEAD holds `f549389e`. The 7+/2-
`is_supplied` -> `bool()` hunk predates dispatch; no `## Owned
changes` row (ledger = plan lines 1058-1122) names this file. Hence
concurrent-external, correctly traced-not-judged. Corroborated
independently: the hunt record verifies the same hunk (`bool()` only
at the offset twin, keyset keeps `is_supplied`).

(3) F-new `window-range-fetch-derivation`: ENDORSED. 9/9 definitions
confirmed single-owned here with 1-definition change counts
re-derived; 7-file consumer census confirmed exact (code reads in
exactly the 7 named files; `selections.py`/`exceptions.py` prose-only,
`keyset.py` zero reads). No colliding family row exists in the plan
index. Owner candidate `window_range_plan` + record is the narrowest
cohesive home every consumer already imports. Gate-or-reject framing
adopted; the plausible bypass (renderer re-deriving `offset + limit`
inline) is real — the lateral dialect carries the warning comment.

(4) C1/C2/C3: STAND. C1's 9 symbols are exactly the slice-derivation
cluster; family row + owner match the plan; no boundary change owed.
C2 interplay-only (guard enforced + plan threaded at the seam,
definitions stay in F-new) verified at all 4 enforcement sites. C3
verified: one ceiling read through `effective_bound`, and the policies
artifact classifies this file indirect at exactly HEAD `f549389e`.

(5) Rejections: all 9 STAND on independent probes. R1 confirms the
held nested_planner R17 verbatim ("held for File
`utils/connections.py`", already one body, HEAD 151-158
body-verified). R2 same shape via the shared plan builder. R3: keyset
fork never touches SliceMetadata; all five shareable parts already
shared. R4: planner passes the raw None-able dig
(nested_planner.py:861/923); None leg load-bearing. R5: filters bind
at 12+ sites, orders once via traversal config
(orders/sets.py:399) — consumers, not definitions. R6: wire map
identical at HEAD list_field.py:340 with schema-map-primary read.
R7: `except (ValueError, TypeError) -> None -> malformed` vs `except
UnwindowableConnection -> fallback` separation verified; type merge
would collapse strictness visibility. R8: engine oracle re-verified
byte-level against installed strawberry-graphql 0.324.0 (`if
before:`/`if after:`, isinstance gates, both error texts,
relay_max_results 100). R9: list_field.py carries zero
SliceMetadata/cursor references; contracts vary independently.

(6) Routings: both ENDORSED. O1: the quirk composition spelled at
exactly connection.py:823 and :1105 (semantically identical;
:1001/:1022/:1179 thread the value, not a third spelling); both sites
in open File `connection.py`, which owns the pair — correct routing,
no family to name from here. O2: concurrent-external hunk correctly
observed-not-homed; homing it would double-home the hunt flow's
in-flight fix (which owns the split and its tests).

(7) Zero-defect call: STANDS. No production defect found in the
target at HEAD bytes. The one known prose candidate (the
"future keyset-cursor backend" clause in `split_window_rows`) is
already routed to the review flow's pending utils/connections.py
item — review-owned, not DRY's to home. Axis-6 guard census
re-verified (both seam `__post_init__`s, `apply_window_pagination`
direct, single-parent pre-guarded + counted/reversed refusal).

On-record corrections (none structural, none reopening):
C-W1: 4 enumeration HEAD-line pins read worktree-shifted (+5):
`assert_relay_pagination_bound` 701->696,
`relay_max_results_from_info` 721->716, `resolve_relay_max_results`
739->734, `derive_keyset_window_bounds` 761->756 (693 pin correct).
Bodies identical in both states; no verdict depends on a pin.
C-W2: test oracle census "14 names" miscounts: 15 top-level names
(17 unique incl. function-level imports); 39-test count exact.
C-W3: completeness note — `window_range_plan` has a 5th production
call site, the resolver inference at connection.py:417 inside
`_resolve_from_window`; the "4 plan/render sites" count is true as
qualified and the resolver consumption is named in the consumer list.
C-W4: removed the stray duplicate trailing `Status:` line (siblings
carry exactly one, at line 3); verdict surface now canonical.

Freshness re-verified after all reads: target HEAD `f549389e` /
worktree `efcf749a`; all 20 connected-file/oracle blobs match W1's
pins exactly (states unchanged); engine 0.324.0. Window diff vs
ITEM_BASELINE names 4 tracked paths (plan, review-0_0_15.md,
list_field.py truth-migration, test_library_api.py docstring touch)
plus this untracked artifact — all concurrent, none W1's; the
list_field.py dirt leaves the R6/R9-cited sites byte-identical. No
`dry-file-utils__connections*` scratch exists. Artifact excluded
from source-layout rules (0 files checked). HEAD `0c0537e2` unmoved
at verdict.

Verdict: VERIFIED. Zero-edit file item; 25/25 enumeration, hunk
externally attributed, F-new endorsed, C1/C2/C3 stand, 9/9 rejections
stand, O1/O2 correctly routed, zero defects, 16/16 index rows
transcribable, no pending execution, nothing tracked touched.

## Run 8 re-trace (Worker-1, scoped re-trace s15)

Prior sections are run-7 evidence only; nothing above is edited.
Every verdict below is decided fresh against HEAD bytes (blob
`735aa454`, 855 lines, HEAD `83998e08` confirmed before the
first read and after the last — unmoved throughout). No pytest
ran (dispatch: read-only probes only), no probe scope was
created, zero production edits. Method: the AST census ran in
the disposable copy (`workspace.py run
dry/connections-retrace-s15/consolidate`, run
dry-20260930T184846-2b974a, exit 0); the copy carries no git
repo and its venv cannot import strawberry, so `git show HEAD:`
/ `git grep HEAD` / `git rev-parse` fingerprints ran read-only
in the shared tree and the engine oracle was verified by direct
text read of the installed source. Nothing tracked was touched
except this artifact.

### Subject, drift, and dirt attribution

- Target `django_strawberry_framework/utils/connections.py`:
  HEAD blob `735aa454b8f8d449ed776687767ff0b3aa716b54`
  (855 lines) == worktree blob — CLEAN, no dirt to
  attribute. `9aaaad5d` ("dry-0015 pre-ff snapshot", not an
  ancestor — read-only evidence, never applied) holds
  `efcf749a26dc7d3fa9b3cc142789a11de2647070` (802 lines),
  byte-identical to run 7's worktree state (drift-base code
  plus the then-uncommitted cursor-truthiness hunk).
  ITEM_BASELINE `b37fec92ae0ebb70c2f845896b6fac5414685332`
  (WIP stash on `83998e08`) holds `735aa454` for this
  path: the clean worktree trivially predates dispatch.
- Drift `0c0537e2..HEAD` on this target is four commits.
  Two bear behavior: `193f9946` (new page-argument rewrite,
  first as `offset_page_first`, called by the offset derive;
  cursor presence moves from `is_supplied` to engine
  truthiness `bool()` with a six-line comment — the
  run-7 O2 hunk, landed in substance (identical `bool()`
  lines; the worktree's five-line comment reworded)) and
  `dbf0a870` (the
  rewrite generalizes to `page_arguments` with the `last:
  0` → `first: 0` arm, called by both derives; the
  `is_backward_shape` docstring drops from four reading
  sites to three; the keyset derive reorders to
  rewrite-first and returns `first` directly). Two are
  typing-only (`999a1aab`, `b20277fe`: annotations,
  TypeVars, the `_RawWindowArguments` Protocol, the
  `TYPE_CHECKING` block, one `cast`, `Mapping` for
  `Sequence`); `999a1aab` additionally inlines the
  `bounded` local in `window_range_plan`, verified
  behavior-identical by body read (`bounded` was `limit is
  not None` and both use sites substitute it exactly).
  `offset_page_first` has zero hits anywhere at HEAD
  (package, tests, examples): the rename left no remnant.
- Neighbors and oracles were read at HEAD bytes only via
  `git show HEAD:` / `git grep HEAD`; the worktree
  concurrently dirties every connected neighbor except
  `lateral_fetch.py` and `single_parent_fetch.py`, plus
  `test_relay_connection.py` among the oracles (see
  Freshness), so every body below cites its HEAD blob,
  never the worktree.

### Enumeration (fresh)

Instrument: every name in `ast.Module.body` over HEAD bytes
(workspace run dry-20260930T184846-2b974a). Count: 44
statements = 1 module docstring + 12 imports + 1 `If`
(`TYPE_CHECKING`) + 8 assigns (3 TypeVars + 3 sidecar
constants + sentinel count + Relay default) + 5 classes +
17 functions (0 async). Delta vs run 7 (38 statements, 25
named symbols): +1 `If`, +3 TypeVar assigns, +1 class
(`_RawWindowArguments`), +1 function (`page_arguments`) =
30 named symbols, every one homed below, 0 unassigned.
`WindowRangePlan`'s 8 fields + 6 members, `FetchMode`'s 4
values, `ConnectionWindowBounds`' 3 fields, and the
Protocol's 5 properties are homed with their records.

| # | Member (HEAD line) | Home |
|---|---|---|
| 1 | `CONNECTION_FILTER_KWARG` (70) | L-sidecar |
| 2 | `CONNECTION_ORDER_KWARG` (71) | L-sidecar |
| 3 | `CONNECTION_ORDER_KWARG_GRAPHQL` (72) | L-sidecar (R6 interplay) |
| 4 | `NEXT_PAGE_PROBE_ROWS` (81) | F-new `window-range-fetch-derivation` |
| 5 | `UnwindowableConnection` (84) | C1 `plan-time-window-slice-resolution` (R7 interplay) |
| 6 | `connection_sidecar_inputs_from_kwargs` (105) | L-sidecar |
| 7 | `is_supplied` (127) | L-supplied (R5 interplay) |
| 8 | `is_backward_shape` (143) | C1 `plan-time-window-slice-resolution` |
| 9 | `page_arguments` (156) | C1 `plan-time-window-slice-resolution` (new; s10-R14 hold) |
| 10 | `has_connection_sidecar_input` (176) | L-sidecar |
| 11 | `has_connection_sidecar_kwargs` (181) | L-sidecar (R1 held confirmation) |
| 12 | `FetchMode` (191) | F-new `window-range-fetch-derivation` |
| 13 | `_is_probe_shape` (231) | F-new `window-range-fetch-derivation` |
| 14 | `is_ambiguous_empty_window` (249) | F-new `window-range-fetch-derivation` |
| 15 | `WindowRangePlan` + 8 fields + 6 members (273) | F-new `window-range-fetch-derivation` |
| 16 | `window_range_plan` (432) | F-new `window-range-fetch-derivation` |
| 17 | `assert_window_fetch_mode` (505) | F-new `window-range-fetch-derivation` (C2 interplay) |
| 18 | `assert_window_fetch_mode_for` (554) | F-new `window-range-fetch-derivation` (C2 interplay, R2) |
| 19 | `split_window_rows` (575) | F-new `window-range-fetch-derivation` |
| 20 | `ConnectionWindowBounds` (639) | C1 `plan-time-window-slice-resolution` |
| 21 | `derive_connection_window_bounds` (652) | C1 `plan-time-window-slice-resolution` |
| 22 | `_RELAY_MAX_RESULTS_DEFAULT` (750) | C1 `plan-time-window-slice-resolution` (R8 interplay) |
| 23 | `assert_relay_pagination_bound` (753) | C1 `plan-time-window-slice-resolution` (R8 interplay) |
| 24 | `relay_max_results_from_info` (773) | C1 `plan-time-window-slice-resolution` (R4 interplay) |
| 25 | `resolve_relay_max_results` (791) | C1 `plan-time-window-slice-resolution` (C3 interplay) |
| 26 | `derive_keyset_window_bounds` (813) | C1 `plan-time-window-slice-resolution` (R3 interplay) |
| L0 | Module docstring + 12-import block + `if TYPE_CHECKING:` (50) + `_FirstT`/`_LastT`/`_RowT` (55-57) + `_RawWindowArguments` Protocol (539) | File-local mechanics |

Homes tally: C1 10, F-new 9, L-sidecar 6, L-supplied 1,
L0 mechanics. 30/30 homed, 0 unassigned.

### Matrix (fresh, HEAD surface)

1. Cross-flavor policy mirroring — SEARCHED, holds.
   `list_field.py` still owns ordered-offset bounding with
   zero `SliceMetadata`/cursor/window references (fresh
   grep, R9); filters bind `unset_sentinel` at 14 sites
   and orders at 1, both consuming the one input-values
   rule (re-counted, R5); mutations, forms, and
   `rest_framework` carry zero window references (fresh
   package-pathspec grep). No second window derivation
   exists in any flavor. `page_arguments` is read by
   exactly three code sites (both derives plus
   `connection.py::_consume_fallback`), all composing the
   one body.
2. Sync/async twins — HOLDS. 17 `def`, 0 `async def`,
   no await boundary. Both resolver colors compose the
   same bodies: `_consume_fallback` runs `page_arguments`
   once upstream of the keyset/offset dispatch, and the
   uncolored `_consume_window` runs the shared derive.
   No twin pair exists to drift.
3. Derived rather than repeated knowledge — HOLDS. Cap
   ladder once (`resolve_relay_max_results`), sentinel
   count once (`NEXT_PAGE_PROBE_ROWS`), `sys.maxsize`
   normalization once (`window_range_plan`), published
   wire name from the schema map (R6). The page-argument
   rewrite (`last: 0` arm plus cap-default arm) lives in
   the one `page_arguments` body; no slicer re-derives
   either arm (the keyset slicer's former `else cap` arms
   are deleted, verified by body read).
4. Inverse/round-trip pairs — HOLDS. Plan/consume pairs
   stay same-helper and colocated. Offset versus keyset
   is still a cursor-vocabulary fork with different
   algorithms sharing one more pre-step (`page_arguments`)
   than in run 7 (R3). No separated halves.
5. Contracts restated in another medium — HOLDS. The
   drift commits moved the contract sources with the
   code (spec-033 Decisions 5/6, spec-047 Decision 7,
   GLOSSARY planning entry — projections, read not
   counted); the unit oracle is byte-unchanged
   (`65d54027`, 39 tests, no `page_arguments` reference
   — the rewrite is covered transitively through its
   three readers, as `is_supplied` et al. already were);
   the drift's live rows (root, nested, keyset `last: 0`;
   `before`-past-cap; `sys.maxsize` cursor) are the
   independent oracles for the new arms; the engine
   source is re-verified byte-level at 0.324.0 (R8).
6. Enforcement by omission — SEARCHED, no defect. Guard
   census re-derived: `NestedConnectionRequest` and
   `LateralWindowSpec` `__post_init__`s, direct
   `apply_window_pagination`, single-parent pre-guard
   (keyset/count/reverse refused) plus the
   `plain_first_page` gate. Backward keyset shapes still
   refused via `UnwindowableConnection` while the
   slicer serves them. The O1 quirk pair is deleted, not
   omitted (zero `last_zero_quirk` hits package-wide);
   the O2 split is committed fork-local behavior, not a
   missing guard (see R3).

### Challenges (fresh, definition counts)

- Slice-window bounds (C1). New offset shape: 1
  definition (the offset derive; adapters and dispatch
  consume). `last: 0`-rule change: 1 definition
  (`page_arguments`; the single `last == 0` site
  package-wide, three composing readers). No-page-arg
  default change: 1 definition (the cap arm in the same
  body). Keyset backward planning in v2: 1 definition
  (the refusal arm). Cap precedence: 1 definition
  (`resolve_relay_max_results`). Bound text: 1
  definition per text. Shape core: 1 definition
  (`is_backward_shape`; exactly one extra term at one
  call site now, `not before_supplied` in the offset
  derive — the keyset resolver's `not last_zero_quirk`
  term is deleted with the flag).
- Window-range fetch (F-new). All seven run-7 counts
  re-derive at 1 definition each; the `bounded` inline
  moves no ownership.
- Sidecar family (L-sidecar). Third-sidecar and rename
  challenges unchanged: 1 rule cluster; twin census
  re-verified (no reader outside this module and the
  unit oracle).
- Supplied-ness (L-supplied). Third-spelling challenge:
  1 definition; zero raw `UNSET` comparisons in either
  connection module re-verified. The offset derive no
  longer reads `is_supplied` for cursors — that question
  moved to engine truthiness by fork contract (R3), not
  to a second `UNSET` spelling.
- Arity pairs (R1, R2). Either input-shape change: 1
  body each (both delegations body-verified intact).
- Fork, dig, bindings, twin, signal, mirrors, bounding
  (R3–R9). Each trigger re-checked unfired; counts stand
  (see verdicts).

### Per-finding verdicts

CONFIRM = holds at HEAD modulo line shifts and
typing-only annotation drift. REVISE = holds with a
recorded content change. All 25 prior names present
with identical spelling; 5 new names (all drift-attributed)
homed above.

- C1 converge onto open
  `plan-time-window-slice-resolution` — REVISE (homing
  +1). The 9 prior symbols hold with identical
  contracts; `page_arguments` joins as the 10th homed
  definition (the page-argument rewrite both derives
  run through, plus the fallback slicer). Consumers
  re-censused: `connection.py` now imports 15 names
  (+`page_arguments`), the planner 8 (7 + the retained
  private cap alias); `window_range_plan` still 4
  plan/render sites + the resolver inference
  (`connection.py:450`) + the internal `_for` delegate;
  `split_window_rows` 1 consumer; sentinel constant 2
  code consumers. Owner stays the planner adapter per
  the plan row; no boundary change proposed. The
  s10-R14 hold is confirmed at the owner (next
  section).
- C2 interplay onto open `nested-fetch-strategy-seam`
  — CONFIRM. All 4 enforcement sites re-verified
  (`plans.py:1135`, `nested_fetch.py:272`,
  `lateral_fetch.py:245`, planner range build); 0
  symbols homed, as before.
- C3 interplay onto open `policy-authority-isolation`
  — CONFIRM. The single ceiling read through
  `effective_bound` is intact
  (`resolve_relay_max_results:810`); 0 symbols homed.
- F-new `window-range-fetch-derivation` — CONFIRM. 9/9
  definitions intact with 1-definition counts
  re-derived; the 7-file consumer census is exact;
  gate-or-reject framing stands (the lateral warning
  comment is untouched). No plan-row change.
- L-sidecar — CONFIRM. Cluster intact
  (annotation-only drift); the kwargs/input arity
  split is still the held R1 confirmation; refusal
  symmetry holds (planner predicate +
  `connection.py:1800/:2267` gates).
- L-supplied — CONFIRM. `is_supplied` still the
  single connection-surfaces binding; zero raw
  `UNSET` comparisons in either connection module
  re-verified. Note: the offset derive's cursors now
  read engine truthiness — a fork-contract move
  recorded under R3, not a second binding.
- L0 mechanics — REVISE (typing-only). Docstring and
  12-import block hold (all consumed; `Mapping`
  replaces `Sequence`, `typing` widens). Joined by the
  `TYPE_CHECKING` block, the 3 TypeVars, and the
  `_RawWindowArguments` Protocol (annotation-only
  scaffold for the R2 arity; zero runtime behavior).
  Plan-row edit named below.
- R1 sidecar arity — CONFIRM (extract-then-delegate
  single body intact, :181-188; still the held
  nested_planner-R17 confirmation).
- R2 assert arity — CONFIRM (delegates through the
  shared plan builder, :554-572; Protocol parameter
  is annotation-only; trigger unfired).
- R3 derive fork — CONFIRM (fork intact; one more
  shared pre-step than run 7; trigger unfired).
  Recorded fork-local difference (committed, no
  longer O2 dirt): offset cursor presence reads
  engine truthiness `bool()` (it must match the
  slice `SliceMetadata` builds — `if before:` /
  `if after:`, re-verified), while the keyset fork
  never parses cursors at bounds time and keeps
  `is_supplied(before)` for its refusal. Different
  correct answers per fork, each docstring-stated;
  live rows cover the `""` shapes. The five
  shareable parts stay shared, plus `page_arguments`.
- R4 dig vs resolve — CONFIRM (`None`-preserving
  dig vs terminal resolve; planner passes the raw
  dig at `:882/:944`; walker binds directly;
  trigger unfired).
- R5 UNSET bindings — CONFIRM (filters 14, orders
  1, connections via `is_supplied`; rule owned in
  `input_values.py`; trigger unfired).
- R6 order twin vs wire map — CONFIRM (twin unread
  outside module + unit oracle; list-field map at
  `:350` with schema-map-primary read intact;
  trigger unfired).
- R7 fallback signal — CONFIRM (planner `:884`
  `except (ValueError, TypeError) -> None ->
  malformed` vs `:1015` `except
  UnwindowableConnection -> fallbacks` separation
  intact; trigger unfired).
- R8 parity mirrors — CONFIRM (engine 0.324.0
  bytes re-verified: `if before:`/`:145`, `if
  after:`/`:139`, both isinstance gates, both
  error texts, default 100; per-text parity
  re-decided, triggers unfired).
- R9 ordered-offset vs Relay window — CONFIRM
  (list_field zero window references; contracts
  vary independently; trigger unfired).
- O1 quirk pair — REVISE: pair
  deleted-committed by `dbf0a870`
  (`_KeysetPage.last_zero_quirk`, the slicer
  composition, the window consumer's reversed
  zero-limit branch, and the planner's
  `window.reverse and window.limit == 0` arm all
  removed; zero `last_zero_quirk` / extra
  `last == 0` hits package-wide). The routing to
  File `connection.py` is spent — no pair remains
  to home. The underlying rule survives once in
  `page_arguments` (next section). No defect.
- O2 worktree hunk — REVISE: landed-committed by
  `193f9946` (HEAD bytes carry the identical `bool()`
  lines with the comment reworded five lines to six;
  target CLEAN, no observation remains). The
  fork-local cursor-presence difference is folded
  into R3's record above. No defect.
- W2 corrections C-W1..C-W4: pins refresh (all
  members shifted by the insertions; fresh pins in
  the table above); import census 14→15 top-level
  names at `connection.py` (+`page_arguments`);
  the 5th `window_range_plan` site stands as the
  resolver inference (`connection.py:450`).

Tally: 14 CONFIRM (C2, C3, F-new, L-sidecar,
L-supplied, R1–R9), 4 REVISE (C1 homing +1, L0
typing mechanics, O1 pair deleted, O2 landed), 0
new families, 0 defects.

### s10-R14 hold (owner-side record, held for s15)

CONFIRMED from this file's side with fresh evidence.
The `last: 0` → `first: 0` rule lives in exactly one
body, `utils/connections.py::page_arguments`
(`:169`, `if last == 0 and not isinstance(first,
int): return 0, None`): package-wide census finds no
other `last == 0` site and no `last_zero_quirk`
remnant. All three slicing paths compose it by name
— `derive_connection_window_bounds:710`,
`derive_keyset_window_bounds:851`, and
`connection.py::_consume_fallback:775` (which hands
the already-clamped cap, so the planned window and
the served page are the same bounded page). The
`is_backward_shape` docstring's "three sites read
it" is exact at HEAD (offset derive, keyset derive,
keyset slicer — the slicer adding no extra term).
Oracles: the drift's `first: 0` page rows (root,
nested, keyset, live + package) plus the unchanged
39-test unit module. No second definition, no
competing spelling, nothing left to home.

### Defects (run 8)

None. The drift retires dead arms (O1), lands the
observed split with its stated reason (O2/R3), and
adds one shared rewrite (C1) — all oracled, no
behavior left unowned. The `cast`, the Protocol,
and the `bounded` inline are verified behavior-free.

### Pending execution

None. All verdicts are static against HEAD bytes; no
probe ran, no pytest ran (dispatch), no workspace
mutation was needed. PG and sharded cells need no
execution: the item is zero-edit and the target is
uncolored pure code reaching no database, alias, or
dialect decision.

### Freshness (run 8)

HEAD `83998e08` unmoved throughout. Target: HEAD
`735aa454b8f8d449ed776687767ff0b3aa716b54` ==
worktree (CLEAN); `9aaaad5d`
`efcf749a26dc7d3fa9b3cc142789a11de2647070`
(802 lines = run-7 worktree bytes); ITEM_BASELINE
`b37fec92` holds `735aa454`. Every input below read
via `git show HEAD:` / `git grep HEAD` (worktree
concurrently dirty unless noted clean):

- Neighbors (HEAD short): `connection.py`
  `3d6dd424`, `nested_planner.py` `3637dc3a`,
  `plans.py` `fdc4b1b0`, `lateral_fetch.py`
  `583f6d7b` (clean), `nested_fetch.py` `304e2f3e`,
  `single_parent_fetch.py` `3a4bb89b` (clean),
  `walker.py` `bdd9c2f1`, `selections.py`
  `4127d08a`, `keyset.py` `8da76569`,
  `input_values.py` `3c17224f`, `typing.py`
  `1ce032f1`, `resource_policy.py` `47befb3f`,
  `exceptions.py` `f27e1f91`, `list_field.py`
  `77ddb86c`.
- Oracles (HEAD short): `test_connections.py`
  `65d54027` (clean, 39 tests, no `page_arguments`
  reference — transitive coverage, as run 7),
  `test_keyset.py` `e5655de7` (clean),
  `test_keyset_connection.py` `70db0483` (clean),
  `test_relay_connection.py` `29a2be59`,
  `test_plans.py` `df714065` (clean),
  `test_walker.py` `3f5e19a5` (clean).
- Projections (HEAD): spec-033 Decisions 5/6 +
  rationale, spec-047 Decision 7, GLOSSARY planning
  entry (all moved with the drift commits).
- Engine: strawberry-graphql 0.324.0 (installed
  dist-info), `SliceMetadata.from_arguments` and
  `relay_max_results = 100` bytes re-verified.

### Judgment (run 8)

Zero-edit re-trace: the target still single-owns
every rule it defines, with one new shared rewrite
(`page_arguments`, homed into C1) absorbing two
retired arms and one landed observation. 30/30
symbols homed (C1 10, F-new 9, L 7 plus mechanics),
14 CONFIRM + 4 REVISE, the s10-R14 hold confirmed
at the owner, zero defects, no consolidation (the
item fences it), no production or test edits, no
plan edits. Every open family naming this file
converges without a boundary change.

### Index rows for Worker 0 (run 8; edits only, no new families)

(Worker 0 alone edits the plan; record actions named
here.)

- NOTE on the C1 plan row
  (`plan-time-window-slice-resolution`): homing from
  this file gains `page_arguments` (10th definition;
  the page-argument rewrite both derives and the
  fallback slicer compose). No boundary change.
- DISCHARGE the s10-R14 hold on the
  `optimizer/nested_planner.py` R14 plan row
  (superseded, held for s15): confirmed at the owner
  — the `last: 0` → `first: 0` rule lives once in
  `utils/connections.py::page_arguments` (single
  `last == 0` site, three composing readers).
- NOTE on the O1 routing (File `connection.py`):
  spent — the quirk pair is deleted-committed by
  `dbf0a870`; no homing owed.
- EDIT the L0 plan row
  (`connections-module-mechanics`) → mechanics now
  (docstring + 12-import block + `TYPE_CHECKING`
  block + 3 TypeVars + `_RawWindowArguments`
  Protocol): typing-only scaffold, zero runtime
  behavior.

## Run-8 verification (Worker 2)

Expectation-first re-trace at HEAD bytes; every
count below is my own instrument, never a quote
of W1. Method: AST/file probes ran in the
disposable copy (`workspace.py run
dry/connections-retrace-s15/verify`, runs
dry-20260930T185639 through dry-20260930T185712,
all exit 0, copy fresh, shared tree unmoved
since sync); the copy carries no git repo and
its venv cannot import strawberry, so `git
show HEAD:` / `git grep HEAD` / `git rev-parse`
fingerprints ran read-only in the shared tree
(W1's precedent) and the engine oracle by
direct text read of the installed source. All
body cites are HEAD bytes — the worktree
concurrently dirties every connected neighbor
except `lateral_fetch.py` and
`single_parent_fetch.py`, plus
`test_relay_connection.py` among the oracles.
No pytest ran (dispatch: read-only probes
only); nothing tracked touched except this
artifact. Package-wide censuses used the
directory pathspec (`-- django_strawberry_framework/`).

Expectations recorded before opening W1's
verdicts: (a) 44 top-level statements / 30
named symbols with `page_arguments` the new
function; (b) exactly the four drift commits
with two behavior-bearing; (c) zero
`last_zero_quirk` and a single `last == 0`
site; (d) 15/8 consumer imports; (e) all R1-R9
triggers unfired. Every expectation reconciled
with no difference except precision notes
P-W1/P-W2 below, neither structural.

(1) Enumeration: STANDS. Own AST over the
copy (target blob == HEAD, so copy bytes are
HEAD bytes): 44 statements = 1 docstring + 12
imports + 1 `If` (`TYPE_CHECKING`, :50) + 8
assigns (TypeVars :55-57, sidecar constants
:70-72, sentinel :81, Relay default :750) + 5
classes + 17 functions, 0 async. All 26 table
pins re-verified exact (defs :105-:813,
classes :84/:191/:273/:539/:639); member
detail matches (FetchMode docstring + 4,
WindowRangePlan docstring + 8 AnnAssign + 6
methods, Protocol docstring + 5 properties,
ConnectionWindowBounds docstring + 3).
17 + 5 + 8 = 30 named symbols; all 30 homes
verified member by member (C1 10, F-new 9,
L-sidecar 6, L-supplied 1, L0 mechanics),
0 unassigned.

(2) Drift re-scope: STANDS. `git log
0c0537e2..HEAD` on the target names exactly
four commits. `193f9946` (new
`offset_page_first` + `bool()` cursor
presence) and `dbf0a870` (generalization to
`page_arguments` with the `last: 0` arm, both
derives rewired, docstring four sites to
three, keyset reorder rewrite-first returning
`first` directly) bear behavior — both diffs
read in full. `999a1aab` on this target is
ONLY the `bounded` inline (one hunk), verified
behavior-identical by body read (`bounded`
was `limit is not None`; both use sites
substitute it exactly, `limit` unchanged
between). `b20277fe` (77 changed lines, all
read) is annotations + imports + TypeVars +
Protocol + one identity `cast` + one comment:
zero runtime behavior. `offset_page_first`
has zero hits at HEAD across package, tests,
and examples.

(3) C1 REVISE (homing +1): STANDS. The 9
prior symbols hold; `page_arguments` (:156)
is the 10th homed definition. Consumers
re-censused: `connection.py` imports 15
names (counted, +`page_arguments` vs run 7);
planner 7 + retained private cap alias = 8;
`window_range_plan` code calls at exactly 4
plan/render sites (planner :1421, ORM
:1128, lateral :391, single-parent :146) +
resolver inference (:450) + internal `_for`
delegate (:565); `split_window_rows` 1 code
consumer (:482); sentinel 2 code consumers
(`_probe_increment` :340, keyset overfetch
:1079).

(4) C2/C3/F-new/L-sidecar/L-supplied:
STAND. C2: all 4 enforcement sites
re-verified (`plans.py:1135`,
`nested_fetch.py:272`,
`lateral_fetch.py:245`, planner range
build :1421); 0 homed. C3: the single
ceiling read `effective_bound(
policy_from_info(info).max_page_size, cap)`
intact at :810; 0 homed. F-new: 9/9
definitions intact with 1-definition counts
re-derived; the 7-file consumer census is
exact (no 8th reader found); the lateral
warning comment is present and text-identical
to the drift base. L-sidecar: cluster
intact, refusal symmetry holds (planner
predicate + gates at :1800/:2267 regions).
L-supplied: single binding; zero raw `UNSET`
comparisons in either connection module
re-verified with a four-spelling ERE.

(5) L0 REVISE (typing scaffold): STANDS.
Docstring + 12-import block intact (all
consumed; `Mapping` replaces `Sequence`,
`typing` widens); the `TYPE_CHECKING`
block, 3 TypeVars, and the Protocol are
annotation-only (the one `cast` is runtime
identity). Zero runtime behavior confirmed.

(6) Rejections: all 9 STAND on independent
probes. R1: extract-then-delegate intact
(:181-188). R2: delegates through the shared
plan builder (:554-572); Protocol parameter
annotation-only. R3: fork intact with one
more shared pre-step; fork-local difference
verified committed and docstring-stated
(offset `bool()` :727-728, keyset keeps
`is_supplied(before)` :852); five shareable
parts shared, plus `page_arguments`. R4:
both adapters pass the raw None-able dig
(:882/:944 windows); walker binds directly
(:115). R5: filters 14, orders 1 code site
(+ 1 prose mention), connections via
`is_supplied`. R6: twin unread outside
module + unit oracle; map at :350 with
schema-map-primary read intact. R7: `except
(ValueError, TypeError) -> None -> malformed`
vs `except UnwindowableConnection ->
fallbacks` separation intact (:884/:1015
regions). R8: engine bytes re-verified
(`if after:` :139, `if before:` :145,
isinstance gates :151/:161, all four error
texts byte-identical, default 100).
R9: zero `SliceMetadata`, zero `cursor`,
zero Relay-derivation references in
`list_field.py` (see P-W1).

(7) O1 REVISE (spent): STANDS. Zero
`last_zero_quirk` hits package-wide
(censused). Removals verified in the
`dbf0a870` diff and at HEAD bytes: the flag
(`_KeysetPage` carries 5 fields, no quirk;
`has_previous_page` has no exception), the
slicer composition (`page_size` rewritten,
`else cap` gone), the consumer branch (`if
reverse and limit == 0: return None`
deleted), the planner arm (no
`window.reverse and window.limit` conjunction
at HEAD). Remaining `limit == 0` hits are
the `first: 0` marker machinery, a different
rule. The routing is spent; the rule
survives once in `page_arguments`.

(8) O2 REVISE (landed): STANDS, including
the comment-reword catch. Byte comparison
of `9aaaad5d` blob vs HEAD: the `bool()`
lines identical; the comment reworded, five
lines (backtick voice, :670-674) to six
(double-backtick voice, :721-726). Target
CLEAN (worktree == HEAD `735aa454`).

(9) s10-R14 hold: CONFIRMED at the owner.
Single `last == 0` site package-wide
(`page_arguments:169`; `last==0` / `0 ==
last` / `last is 0` / `last != 0` variants
all censused, zero elsewhere). Exactly
three code readers (:710, :851, :775;
zero test/example references — transitive
coverage, as run 7). The clamped-cap chain
verified end to end (entry :1312 resolves,
`_consume_window` :1330 threads,
`_consume_fallback` :734/:742 receives,
:775 rewrites). `is_backward_shape`
docstring exact: three readers (:729 with
`not before_supplied`, :852 and :1070 with
no extra term — :1070 body-read). No
slicer re-derives either arm
(`isinstance(first/last` code sites only
:153/:169/:171 plus one planner prose
comment).

(10) Oracles: STAND. Unit module HEAD
`65d54027` == worktree (clean), 39 tests
counted, 15 top-level imported names, no
`page_arguments` reference. Engine:
strawberry-graphql 0.324.0 (dist-info),
bytes as in (6). Live rows present at
HEAD: root `last: 0` (:5299), nested
`last: 0` (:6742, :11504), `before`-past-cap
+ `sys.maxsize` (:5230-5248), keyset rows
(`test_keyset_api.py`, `test_relay_connection.py`
via the `dbf0a870` stat). Drift moved the
contract sources (both commits touch
spec-033 + spec-047; `dbf0a870` also
GLOSSARY + rationale; checklist and
planning entries state the `first: 0`
page).

(11) Zero-edit + freshness: STANDS.
ITEM_BASELINE `b37fec92` holds `735aa454`
for this path; worktree holds `735aa454` —
zero-edit confirmed. `9aaaad5d` holds
`efcf749a` (802 lines). All 20
neighbor/oracle HEAD pins re-fingerprinted
exact with matching clean/dirty states
(14 neighbors: `3d6dd424` dirty,
`3637dc3a` dirty, `fdc4b1b0` dirty,
`583f6d7b` clean, `304e2f3e` dirty,
`3a4bb89b` clean, `bdd9c2f1` dirty,
`4127d08a` dirty, `8da76569` dirty,
`3c17224f` dirty, `1ce032f1` dirty,
`47befb3f` dirty, `f27e1f91` dirty,
`77ddb86c` dirty; 6 oracles: `65d54027`
clean, `e5655de7` clean, `70db0483`
clean, `29a2be59` dirty, `df714065`
clean, `3f5e19a5` clean). HEAD
`83998e08` unmoved at verdict (checked
before the first read and after the last).

Precision notes (neither structural, neither
reopening):
P-W1: the "zero window references"
shorthand (matrix-1, twice) overclaims
textually: `list_field.py` carries
`_windowed_rows` + "offset window" prose
(its own ordered-offset contract, R9's
other side), and forms/mutations/
rest_framework carry lifecycle-phase prose
("bind/validation/write window"). The
verdict substance — zero Relay/pagination-
window *logic* outside the owner — is
verified true; "references" should read
"derivation references".
P-W2: `connection.py` bare `else:` control
flow (8 sites) is unrelated residue, not
`else cap` remnants — no `else cap` line
remains; noted so no future grep confuses
the two.

Verdict: VERIFIED. Zero-edit re-trace;
30/30 enumeration, drift re-scoped
(2 behavior + 2 typing-only), 14 CONFIRM
+ 4 REVISE all survive on independent
evidence, s10-R14 hold confirmed at the
owner, zero defects, no pending execution,
nothing tracked touched except this
artifact.
