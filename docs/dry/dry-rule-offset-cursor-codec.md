# DRY review: `offset-cursor-codec`

Status: verified
Run: 0.0.15 2026-10-11-19

## System trace

Target cluster in [connections.py][connections]: `decode_offset_cursor` +
`_OFFSET_CURSOR_MAX_DIGITS` + `validate_offset_pagination` +
`assert_relay_pagination_bound` + `page_arguments` (file CLEAN, verified via
`git diff`). Whole-package mechanism sweep: one offset decoder, one bound
check, one check order, one page-argument rewrite; every other cursor site
composes by name or owns a distinct vocabulary. Consumers: offset fork
(`derive_connection_window_bounds`, [connection.py][connection]
`::_consume_fallback`) runs `page_arguments` then `validate_offset_pagination`
then the engine; keyset fork (`derive_keyset_window_bounds`,
`::_resolve_keyset_connection`) runs `page_arguments` + `assert_…` directly
plus [keyset.py][keyset] `::decode_keyset_cursor`. Upstream owns the engine
(`SliceMetadata.from_arguments`), the wrap (`Edge.resolve_edge`,
`CURSOR_PREFIX`), and the `start+i` mint integer.

## Verification

### Matrix

1. Cross-flavor: GlobalID decoders are node-identity vocabulary, not page
   cursors — different subject. Keyset codec is a vocabulary fork (Finding F2).
2. Sync/async twins: all five members are pure sync — no await boundary;
   inapplicable by construction.
3. Derived-twice: prefix read by name (`relay.Edge.CURSOR_PREFIX`, 1 code
   site); `arrayconnection` literal only in prose (3 sites); bound texts
   spelled once each. No twin.
4. Round-trip: offset encode owned upstream; decode + window integer mapping
   are the one read half each (Finding F3). Keyset encode/decode co-sited.
5. Media: oracles spell literals (20 focused tests green, see Findings);
   docstrings project; no definition in another medium.
6. Omission: both offset slice entries validate; the window consumer takes
   ints, not cursors; keyset entries call `assert_…` + keyset decode. No gap.

### Challenges

- C1 cursor grammar (admit padding, move the `sys.maxsize` ceiling): moves
  `decode_offset_cursor` only — count 1. Keyset/engine untouched.
- C2 bound posture (reword, clamp instead of refuse): moves
  `assert_relay_pagination_bound` only — count 1.
- C3 check order (first-before-after): moves `validate_offset_pagination`
  only — count 1.
- C4 mint arithmetic: a wire-wrap change moves 0 package defs (both mints
  call `resolve_edge` by name); a window-integer change moves
  `::_resolve_from_window` only — count 1.
- C5 `last: 0` / default-cap rule: moves `page_arguments` only — count 1;
  its 3 call sites compose unchanged.

## Findings

- F1 `offset-cursor-codec` + `offset-page-validation` +
  `relay-pagination-bound-check` + `connection-page-arguments` — CONSOLIDATED
  (already single-owned, zero-edit). Owner: [connections.py][connections].
  Proof: `tests/utils/test_connections.py` decode/assert/validate/derive
  rows, 20/20 green via `heavy uv run pytest -n0 --no-cov` (run exec-85).
  Keyset `last: 0`/cap rows in `test_keyset_api.py` pin the fork statically.
- F2 keyset-halves merge — REJECTED, vocabulary fork (prior connections R3
  trigger re-checked, unfired). Contract differences: `dstcursor` vs
  `arrayconnection` prefix; encrypted JSON vs canonical decimal; uniform
  `GraphQLError` (oracle-hiding) vs `PaginationArgumentError` (engine
  wording); fingerprint binding; forward-only bounds. Trigger: one shared
  cursor grammar across both vocabularies.
- F3 two-mints merge — REJECTED, distinct integer contracts, one wrap owner.
  `start+i` is upstream slice arithmetic; `row-1` is the window's positional
  mapping; both wrap via `Edge.resolve_edge` by name. Wire parity pinned by
  `test_fast_path_wire_parity_with_pipeline` /
  `test_fast_path_wire_parity_last_only` (static-reviewed). Trigger: a
  package-owned cursor-position type both integers derive from.
- F4 engine-halves merge (`SliceMetadata.from_arguments`) — REJECTED,
  upstream-owned; fed validated args, never rejects them. Not consolidatable.
- F5 `_coerce_pagination_int` fold-in — REJECTED, plan-time-only coercion,
  recorded separation at both owners. Trigger: resolver args arriving raw.

## Defects

None. Axis-6 enumeration found every slice entry guarded; no second site
anywhere implies no missing-guard defect to home.
(Worker-2) No defects: independent whole-package sweep found no second
decoder, bound check, mint rule, check order, or page rewrite, and every
slice entry guards — nothing to home.

## Pending execution

None. The one authorized focused run discharged F1; F2–F5 rest on
inspection + standing oracles (no `proof:` owed for a rejection).

## Judgment

One owner already: the offset-cursor codec + page validation live once in
[connections.py][connections], composed by name on both forks. Zero edits.

## What shrinks

Nothing — zero-edit confirmation. Net package lines over
`ITEM_BASELINE=afff18de`: +0/-0. No machinery added, none removed.

## Index rows for Worker-0 (members carry none)

- `offset-cursor-codec` | `utils/connections.py::decode_offset_cursor` |
  `utils/connections.py` | holding item | consolidated.
- `offset-page-validation` |
  `utils/connections.py::validate_offset_pagination` |
  `utils/connections.py` | holding item | consolidated.
- `relay-pagination-bound-check` |
  `utils/connections.py::assert_relay_pagination_bound` |
  `utils/connections.py`, `connection.py` | holding item | consolidated.
- `connection-page-arguments` | `utils/connections.py::page_arguments` |
  `utils/connections.py`, `connection.py` | holding item | consolidated.
- `window-offset-cursor-mint` | `connection.py::_resolve_from_window` |
  `connection.py` | holding item | file-local (F3 upstream merge rejected).
- `keyset-cursor-codec` | `keyset.py::decode_keyset_cursor` | `keyset.py`,
  `connection.py`, `optimizer/nested_planner.py` | holding item | rejected
  (F2 vocabulary fork vs the offset codec).

## Freshness

HEAD `c37a08a0`. Blobs: connections `2313fce5`, connection.py `3e111147`
(WT-dirty, concurrent), keyset `a1890813` (WT-dirty, concurrent),
nested_planner `dc0c401c`, test_connections `37afb2dd`, relay_connection
`6f8e5c33`, keyset_api `5bd9347a`. Searched population: all of
`django_strawberry_framework/` + upstream strawberry relay sources.

## Independent verification (Worker-2)

Own trace, recorded before reading `## Findings`. Read in full:
[connections.py][connections] (whole module), [keyset.py][keyset] (codec halves),
[connection.py][connection] `::_resolve_from_window` / `::_consume_window` /
`::_consume_fallback` / `::_resolve_keyset_connection`, upstream
`SliceMetadata.from_arguments` + `Edge.resolve_edge` + `ListConnection`
slicing, `optimizer/nested_planner.py::_coerce_pagination_int` + both
slice adapters, `optimizer/walker.py` re-exports, and the
`git diff afff18de -- django_strawberry_framework tests examples` (empty).

Sites + roles. Definitions (all in [connections.py][connections]): `decode_offset_cursor`
(offset grammar + decode), `_OFFSET_CURSOR_MAX_DIGITS` (digit ceiling),
`validate_offset_pagination` (engine-mirror check order), `assert_relay_pagination_bound`
(bound wording/check), `page_arguments` (`last: 0` rewrite + default cap).
Consumers by name: `derive_connection_window_bounds`, `derive_keyset_window_bounds`,
`::_consume_fallback`, `::_resolve_keyset_connection`, both planner slice
adapters, `::_consume_window`. Upstream (not ours to consolidate): the engine,
the wrap (`CURSOR_PREFIX` + `resolve_edge`), the `start+i` mint integer.
Keyset codec: 1 encode def + 2 call sites, 1 decode def + 4 call sites, all by
name. Oracles spell literals (`tests/utils/test_connections.py`, live
`test_connection_pagination_api.py`); docstrings project.

Counts per posited change. Grammar (padding, ceiling, `""`): `decode_offset_cursor`
only — 1 (no second offset `int()` decode; engine `int()` is upstream; keyset
grammar is a different vocabulary). Bound wording/posture: `assert_…` only — 1
(each literal spelled once package-wide). Check order: `validate_…` only — 1
for the engine-mirror rule; the keyset decode-then-bound sequences (slicer +
window adapter) are local statement order over different decoders, error types,
and `""` handling (`is_supplied("")` is active, engine truthiness is not), with
no contract source establishing cross-vocabulary precedence parity as one rule;
sharing sequencing would need a driver (barred machinery), so the count-3
reading rejects alike. Mint: wire-wrap change — 0 package defs (both offset
mints call `resolve_edge` by name); window-integer change — `::_resolve_from_window`
only — 1; `start+i` is upstream. `last: 0`/cap: `page_arguments` only — 1
(single `last == 0` site; 3 call sites compose). Keyset fork: distinct
contracts (AES-SIV value codec vs base64 int; uniform invalid-cursor error vs
engine wordings; fingerprint binding; seek vs offset positioning) — separate
rules. Coercion: plan-time-only, owned by the planner, walker imports by name,
separation recorded at both owners — stays out.

Owner I would choose: [connections.py][connections] for the offset cluster
(cycle-safe home both planner and resolver import; already the owner — no
move); codec halves stay in [keyset.py][keyset]. No consolidation, no move.

Matrix (own discharge). Axis 1: GlobalID `to_base64` is node identity, not a
page cursor — different subject. Axis 2: the five members are pure sync;
inapplicable by construction (the keyset slicer's sync/async arms already share
`_build`/`_page`). Axis 3: prefix read by name (1 code site); `arrayconnection`
prose-only; bound texts once each. Axis 4: offset encode upstream, one decode
def, one window-integer site; keyset halves co-sited. Axis 5: oracles spell own
literals (samples verified). Axis 6: every wire-cursor slice entry guards
(both `derive_*`, both planner adapters, `::_consume_fallback`, `::_resolve_keyset_connection`);
`::_resolve_from_window` takes ints, not cursors — no gap.

Reconciliation (after reading `## Findings`). Concur on F1–F5 in full:
same sites, roles, counts, and owner; all four triggers sound
(engine-mirror wording, keyset fork, mint fork, upstream engine, coercion
separation). Two verdict-neutral record corrections carried: (a) axis-3
`arrayconnection` prose count is 5 (`connection.py` x2, `keyset.py` x3),
not 3 — zero code sites, so "no twin" stands; (b) the F1 "20/20"
selection expression is unrecorded (the file holds 43 test functions /
67 collected items), so the exact 20 is not reproducible — superseded by
my focused run `heavy uv run pytest -n0 --no-cov
tests/utils/test_connections.py` + 2 parity tests + 3 keyset zero-page
tests: 75/75 green, discharging F1 and upgrading the F3 parity pins from
static-reviewed to execution-verified. All 7 freshness blobs re-derived —
match. All 6 index rows accurate (owners, files, statuses). Pending
execution None is correct (rejections owe no `proof:`). Zero-edit holds
(item diff vs baseline empty); no touched `.py` paths, so no ruff run is
owed; no line-number citations. Verdict: verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[connections]: ../../django_strawberry_framework/utils/connections.py
[keyset]: ../../django_strawberry_framework/keyset.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
