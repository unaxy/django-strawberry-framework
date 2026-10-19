# Review: `django_strawberry_framework/connection.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - the resolve path runs per connection field per request and per parent row for nested connections; the factory/cache path is cold

## Implementation (Worker-2)

Pass 1. Implemented in axis order Performance -> Mechanics -> Comments.

Attribution (before the first edit): `git diff HEAD` on
`django_strawberry_framework/connection.py` shows the concurrent
truth-helper migration plus the negative-cursor guard (+67/-99), which
predates ITEM_BASELINE and is named on the run-3 Drift line covering this
file; `git diff <ITEM_BASELINE>` was empty on every path touched below
(`connection.py`, `tests/test_relay_connection.py`,
`examples/fakeshop/test_query/test_keyset_api.py`), and all three
`git hash-object` values equalled the records' Trace fingerprints, so the
tree reviewed is the tree edited and no stop was owed. All concurrent
hunks are preserved byte-for-byte. One mid-pass touch of the `before`
copy (a fail-check that copied the new live test into it) was restored
from `git show <ITEM_BASELINE>:...` and re-hashes to the baseline blob
`305b972f`; the copy's package code was never edited.

### Performance - 3/3 implemented

- F1 (Medium, `_window_edge_class` memo) - implemented as recommended: a
  module-level `truth.IdentityMap` keyed by connection class plus
  `clear_window_edge_class_cache()` registered with
  `register_subsystem_clear` beside `clear_connection_type_cache`
  (owner `connection.edge_class`), so schema reloads drop stale entries.
  The derivation itself is byte-identical. Before
  `review-20260929T010858-0e9326`: 30.0 calls/request at 54625.0 ns
  median. After `review-20260929T011234-da324d`: 30.0 calls/request at
  542.0 ns median (Proof threshold below 5000.0). Delta about -54 us per
  page; enclosing `_consume_window` fell 78021.0 to 18687.5 ns. Behaviour
  pinned by the 7 nodes below (8 passed with the F2 test); no timing test,
  per the record. No deterministic memo-identity test was added: the
  suggested `is` pin passes with and without the memo (both derivations
  resolve to the same Edge class object), so the probe rerun plus the
  bench delta carry the number.
- F2 (Medium, lazy fallback source) - implemented as recommended:
  `_build_windowed_fallback` now takes a zero-arg source factory run only
  when the fallback runs, the resolver passes
  `lambda: getattr(root, accessor_name).all()` on the windowed path, and
  the non-window path builds `source` after the window check but still
  before `_check_n1`, preserving error precedence there. Before
  `review-20260929T010911-bdc762`: `related_manager_all_calls=30`. After
  `review-20260929T011248-398d37`: `related_manager_all_calls=0`. The
  missing-accessor timing note stands as analyzed (a served window never
  touches the manager). Permanent test
  `tests/test_relay_connection.py::test_windowed_fast_path_constructs_no_fallback_queryset`
  (new, deterministic package test: 4 windowed parents construct zero
  related `.all()`); failability `review-20260929T012552-b54e30` exit 0,
  exactly the new row fails under the reintroduced prebuild.
- F3 (Medium, guard reorder) - implemented verbatim: the inner conjunction
  is now `not range_plan.next_page_probe and not constant_false and
  _has_next_page_requested(info)`. Before `review-20260929T010858-0e9326`:
  30.0 calls/request. After `review-20260929T011234-da324d`: 0.0 calls.
  Behaviour pinned by the same 7 nodes; no new test.

The 7 behaviour-pin nodes (F1/F2/F3 shared Proof) plus the new F2 test
report `8 passed` in the shared tree (`--no-cov -n0`).

Bench delta for the plan's `## Bench baseline` (`bench_nested_fetch.py`,
`--cell pg`, 200 parents x 30 children, page `first: 2`): before
`review-20260929T010927-049ab0`, after `review-20260929T011305-20cfca`;
instrument blob `d7f8c39e` identical both sides. Windowed median ms:
count-free 50.53 -> 33.04 (-34.6%), totalCount 44.92 -> 34.23 (-23.8%);
lateral count-free 52.11 -> 27.62, totalCount 43.70 -> 32.60; query counts
identical (2/2/101 and 2/2/201). Per-parent also moved (count-free 334.19
-> 278.84, totalCount 351.49 -> 193.78) on a path this change cannot touch,
so part of every delta is machine/buffer drift between the back-to-back
runs; direction is down as predicted and the probe medians above are the
attributable numbers. No other bench row moves (plan cache, walk,
importtime untouched).

### Mechanics - 1 High + 1 cross-axis Low implemented

- H1 (High defect, offset `last: 0` bypasses the relay cap) - fixed at the
  owner `django_strawberry_framework/connection.py::_consume_fallback`:
  the offset tail detects the quirk (`is_backward_shape(first, last) and
  last == 0 and not is_supplied(before)`, mirroring the keyset definition)
  and bounds the served page at the already-resolved `max_results` via the
  new `_cap_offset_last_zero_page` helper (at most `cap` edges, kept
  `hasPreviousPage` False, `hasNextPage` True when the trim drops rows,
  cursors re-anchored), covering queryset and non-queryset sources and the
  async awaitable arm. Under-cap pages are byte-identical (no trim, flags
  as upstream set them). Permanent test
  `examples/fakeshop/test_query/test_keyset_api.py::test_offset_last_zero_stays_bounded_by_relay_cap`
  (new live test, first line `seed_data(30)`; `last: 0` and `last: 0` +
  `after:` each serve exactly 100 with `hasPreviousPage` False +
  `hasNextPage` True): `1 passed` in the shared tree. Compatibility:
  under-cap serve-all pins `2 passed`, keyset path `4 passed` (all 6 in
  the shared tree). The new test fails on the unfixed `before` copy
  (`review-20260929T011822-5d6f84`, exit 1). Failability
  `review-20260929T012807-41a301` exit 0: disabling the trim fails exactly
  the new live row. Recorded under `## Defects` below.
- C1 (Low, `FieldDoesNotExist` hoist, Comments verifier grades it) -
  implemented once with the Comments F4/cross-axis hoist: the import lives
  at top level in the Django group, the in-function import and its false
  idiom comment are gone. `grep -c "^from django.core.exceptions import
  FieldDoesNotExist"` prints `1`, nested prints `0`; behaviour
  `tests/test_keyset_connection.py::test_resolve_order_path_field_arms` +
  `::test_resolve_order_path_field_accepts_mti_parent_link` report
  `2 passed`.

### Comments - 5 Medium + 5 Low implemented, 6 Low deferred, 1 cross-axis implemented

- F1 (Medium, phantom second resolve path) - implemented verbatim at both
  sites (offset/keyset window branches; wrapper/non-wrapper sources).
  Proof prints `0`.
- F2 (Medium, future-keyset framing) - implemented with one wording change
  from the text-after, recorded here: the reviewer's after retains the
  substring the Proof keys on (`keyset-cursor backend`), which would leave
  the Proof at `1` instead of the governed `0`. Landed `the keyset backend
  rides` (dropping `cursor`), present tense and true as the body proves;
  the Proof now prints `0`.
- F3 (Medium, coroutine dispatch) - implemented as the text-after proposes
  (async-iterable queryset + execution color). Proof prints `0`.
- F4 (Medium, false import idiom) - implemented by the C1 hoist above (the
  comment line is deleted). Proof prints `0`.
- F5 (Medium, spent until-033 posture) - implemented as the text-after
  proposes (version anchor dropped, glossary landing clause). Both Proofs
  print `0`.
- L1 (Low, card id), L2 (Low, legacy label), L3 (Low, spec-revision
  history), L4 (Low, spec-algorithm), L5 (Low, bare spec-047 tags) -
  implemented verbatim; all Proofs print `0`. All five ride on
  `connection.py`, which higher findings change.
- L6-L9 (Low, `tests/test_connection.py` pointers/grammar) - deferred: no
  higher finding touches that file (Severity ride rule).
- L10-L11 (Low, `test_library_api.py` provenance/ambiguity) - deferred: no
  higher finding touches that file (Severity ride rule).
- Cross-axis (Low, import hoist) - implemented once with C1 above; both
  Proofs govern and both pass (`grep -c` prints `1` at top level;
  `build_tree_md.py --list-docstrings` on the target prints ok).

Inverse proof (prose-only identity on `connection.py`, whose code other
axes changed): live file vs reconstruction
(`docs/review/temp-tests/connection/implement/reconstruction-connection.py`,
ITEM_BASELINE prose plus only the Performance/Mechanics code hunks, built
by `build_reconstruction.py` reverting all 12 prose hunks):
`review_inspect.py --code-digest` prints `sha256:de3bdc08...` on both
sides, exit 0. No code moved by the Comments edits.

Files changed and why:

- `django_strawberry_framework/connection.py` - F1 memo + cache/clear,
  F2 factory + resolver laziness, F3 reorder, H1 cap helper + quirk trim,
  C1 hoist, all Comments prose above. The only package file.
- `tests/test_relay_connection.py` - F2 deterministic counter test (the
  package tier the record prescribes; a live tier cannot count
  related-manager constructions).
- `examples/fakeshop/test_query/test_keyset_api.py` - H1 live test beside
  the keyset `last: 0` cap twins (the strongest reachable tier: a real
  over-cap query) plus its `seed_data` import.

No module first line changed, so no TREE.md render owed.

Formatter result (explicit touched paths, gate order, all green):
`ruff check --fix` (All checks passed), `check_trailing_commas.py`
(0 violations), `ruff format` (1 file reformatted, then stable); verify
pass `ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all pass, and `check_citations.py
--check` passes on the whole tree (1297 citations resolve).

Scratch paths and run ids (all under
`docs/review/temp-tests/connection/implement/` unless noted):

- `nested_fetch_before.json` / `nested_fetch_after.json` - bench JSONs.
- `probe_seed_count.py` - seed-size probe (copied into the implement copy
  as `test_zz_probe_seed_count.py` for its run, then removed from the
  copy; the shared-tree original stays).
- `failability-f2.json` / `failability-h1.json` - prove manifests.
- `reconstruction-connection.py` / `build_reconstruction.py` -
  Comments inverse-proof reconstruction and its builder.
- `review-20260929T010858-0e9326` before hotpath (F1 54625.0 ns, F3 30.0
  calls); `review-20260929T010911-bdc762` before all-calls (30);
  `review-20260929T010927-049ab0` before bench; all at
  `review/connection.py/before`.
- `review-20260929T011234-da324d` after hotpath (F1 542.0 ns, F3 0.0
  calls); `review-20260929T011248-398d37` after all-calls (0);
  `review-20260929T011305-20cfca` after bench; all at
  `review/connection.py/implement --fresh`.
- `review-20260929T011427-498a24` seed probe, superseded (queried
  `totalCount` on `ItemTypeConnection`, which carries none);
  `review-20260929T011520-55e8ea` seed probe green (`seed_data(20)` and
  `(30)` both serve first:100 with `hasNextPage` True; landed `(30)` for
  margin).
- `review-20260929T011822-5d6f84` new H1 test against the unfixed `before`
  copy (exit 1, fails as required; copy restored after).
- `review-20260929T012552-b54e30` F2 prove (exit 0, exactly the new row
  fails); `review-20260929T012807-41a301` H1 prove (exit 0, exactly the
  new live row fails); both `workspace.py prove ... --fresh`.
- Shared-tree focused runs (all `--no-cov -n0`): F2 + 7 pins `8 passed`;
  H1 live `1 passed`; H1 compat `6 passed`; C1 `2 passed`; final combined
  `16 passed`.

Fingerprints (`git hash-object`; before values equal the records' Trace):

- Touched, before -> after:
  `django_strawberry_framework/connection.py`
  68d1ea2c325eb8a3c34d34df7bc6125ad736ec16 ->
  c8b9670109d05f9a09f2f8a113e491baa7511317;
  `tests/test_relay_connection.py`
  a4769a3dfb4aadc1e6bedf0677eb9c0f51fc22b0 ->
  fe2b2d24ab6e71e6238183690b02821abb239497;
  `examples/fakeshop/test_query/test_keyset_api.py`
  305b972f228cb1326e783ccb05f2e3eee3c429e0 ->
  88a432b0858c54afc91a79cedbf8938983ab2c23.
- Read unchanged (equal to the records'):
  `utils/truth.py` d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
  `utils/typing.py` a672cd6b4f5cf6c207bd4f65eb080acd971a6b98;
  `utils/connections.py` efcf749a26dc7d3fa9b3cc142789a11de2647070;
  `apps/products/services.py` ece9da7a1d5a1ad88f09f42a980c4436972a68a0;
  `apps/products/schema.py` 04a5afe3dddff9279660ae1370924e03857d57e7;
  `tests/test_keyset_connection.py`
  70db0483f461a4ef7befb11bc4acaf1302bb76d3;
  `tests/test_connection.py` 8e08b23fbf7eee84a94ab406d8713855056087a1;
  `test_query/test_library_api.py`
  2cd1b6dd1a2f3f9a5261ff9a4509611633fa3f20;
  `registry.py` 492654d219d1061fef33f186d962dc5369b71ebe;
  `keyset.py` 279ad7b089de282e52b8210ad9c61101c8b3e401;
  `list_field.py` 450e87cde13edc1bfc3c4d4a161c5540d1ac5277.
  Upstream read via interpreter introspection, not files:
  strawberry-graphql 0.324.0 `relay/types.py` + `relay/utils.py`.
- Also read, no fingerprint owed (review inputs, not change inputs): the
  plan, the three axis records, this artifact's skeleton, the Performance
  and Mechanics scratch probes.

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/connection.py` | connection.py | Performance, Mechanics, Comments | `_window_edge_class` (memo) + `_window_edge_class_cache`, `clear_window_edge_class_cache` (new); `_build_windowed_fallback` (factory) + `_build_relation_connection_resolver._resolve` (lazy source); `_resolve_from_window` (guard reorder; docstring F1/F2/L3); `_consume_window` docstring (F1); `_cap_offset_last_zero_page` (new) + `_consume_fallback` (quirk trim); `_resolve_order_path_field` (import hoist); `_KeysetPage` docstring (L4); `_resolve_keyset_connection` docstring (F3); `DjangoConnection.resolve_connection` comments (L5); `_build_relation_connection_resolver` docstring (L1/L2/F5) |
| `tests/test_relay_connection.py` | connection.py | Performance | `test_windowed_fast_path_constructs_no_fallback_queryset` (new) |
| `examples/fakeshop/test_query/test_keyset_api.py` | connection.py | Mechanics | `test_offset_last_zero_stays_bounded_by_relay_cap` (new); `seed_data` import |

Handoff: Pass 1 implements everything the ride rule reaches: Performance
3/3, Mechanics H1 + C1, Comments 5 Mediums + 5 riding Lows + the shared
hoist, with 6 Lows deferred to files no higher finding touches. Three
judgment calls, each recorded above: no F1 `is` pin (vacuous without the
memo), F2 wording is the Recommendation's factory shape with error
precedence preserved before `_check_n1`, and F2-Comments (the keyset
prose) drops `cursor` so its Proof prints the governed `0`. The bench
delta is directional only (per-parent drift); the probe medians are the
attributable numbers. Open threads for verifiers: the F2-Comments wording
deviation (grade true + Proof 0, as recorded), the six deferred Lows (in
`## Outcomes` scope, not this diff), and the async over-cap trim line
(covered by line, exercised over-cap only via sync - the async under-cap
oracle covers the wrapper). No disputed finding, no missing fixture, no
stop beyond the restored `before`-copy touch.

## Defects

H1 (Mechanics High): offset `last: 0` served the whole table past the
`relay_max_results` / `max_page_size` page cap. Fixed at
`django_strawberry_framework/connection.py::_consume_fallback` by bounding
the served quirk page at the resolved cap (helper
`_cap_offset_last_zero_page`), mirroring the keyset quirk shape, for
queryset and non-queryset sources, sync and async. Permanent test
`examples/fakeshop/test_query/test_keyset_api.py::test_offset_last_zero_stays_bounded_by_relay_cap`
(live, over-cap); fails without the fix
(`review-20260929T011822-5d6f84`) and under prove
(`review-20260929T012807-41a301`); under-cap and keyset pins unaffected.
No pre-existing failure was met.

V1 (Mechanics verify 1, High, introduced by pass 1): the H1 async trim
wrapper closed over `conn` and then rebound `conn` to the wrapper
itself, so `await conn` awaited the running coroutine
(`ValueError: coroutine already executing`) on every async offset
`last: 0` page. Fixed at
`django_strawberry_framework/connection.py::_consume_fallback` by
binding the untrimmed awaitable to `untrimmed` before defining the
wrapper (pass 2; sync trim bytes and helper contract unchanged).
Proved by the two pre-existing async oracles below, which fail with
the bug present and pass with the fix.

## Iterations

### Implement pass 2

Answers the Mechanics `revision-needed` gap V1 only. Pass 1 stands
(Performance verified, Comments verified, H1 sync fix + tests +
failability verified); nothing below relitigates it.

Attribution (before the first edit): `git diff <ITEM_BASELINE> --` the
three pass-1 paths hashes
`ef54683033035551709fa8a005924e2440c1232d72705e96eb8049db53a837eb`
(429 lines), equal to the pass-1 record both verifiers bound, and all
three `git hash-object` values equalled the pass-1 after-values, so
the tree held still. `git diff HEAD e6b022ba -- connection.py` is the
concurrent 67+/99- truth-migration + negative-cursor guard named on
the run-3 Drift line covering this file, and
`git show HEAD:connection.py` contains zero pass-1 symbols, so every
HEAD-vs-live hunk is either that Drift-line concurrent work or this
item's pass 1. No stop owed; all concurrent hunks preserved.

Dispositions:

- V1 (High, async trim self-await) - implemented as recommended: the
  `_consume_fallback` async arm binds `untrimmed = conn` before
  defining `_trim_async`, and the wrapper awaits `untrimmed` instead
  of `conn`. No signature or helper change; the sync trim line is
  byte-identical.

Files changed and why:

- `django_strawberry_framework/connection.py` - the V1 closure bind
  (2 added lines, 1 changed line inside `_consume_fallback`; the
  only package file). No test file changed: both V1 Proof nodes are
  pre-existing oracles.

Before/after numbers with run ids: none owed beyond the V1 Proof
nodes - state so. V1 is a correctness fix on an error path (raise
vs serve); no instrument, bench row, or query count moves.

Permanent tests with focused results: none new - state so. The V1
Proof pins two pre-existing oracles (shared tree, `--no-cov -n0`):

- `tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`
  (V1 Proof): `1 passed` post-fix (in the 2-node run below).
- `tests/test_relay_connection.py::test_consume_window_unservable_window_runs_the_async_fallback`
  (Performance verifier's second node): `1 passed` post-fix.
- H1 Proof rows re-run post-fix: (1) live
  `test_offset_last_zero_stays_bounded_by_relay_cap` `1 passed`;
  (2) under-cap serve-all pins `2 passed`; (3) keyset path pins
  `4 passed`.
- Full async scope `pytest tests/test_relay_connection.py -k async`:
  `2 passed, 67 deselected` (the selection is exactly the two
  Proof nodes).

Failability proofs (V1's gate: the async oracle fails with the bug
present): the pre-fix run of the two async nodes on the unedited
tree reports `2 failed, 2 errors`, both failing inside
`_trim_async` with `ValueError: coroutine already executing` at
`connection.py:839` (`resolved = await conn`); the post-fix run of
the same two nodes reports `2 passed`. The gate fails with the bug
present and passes with the fix; no `prove_failability.py` manifest
is owed (no new gate, the oracles pre-exist).

Formatter result (explicit touched path, gate order, all green):
`ruff check --fix` (All checks passed), `check_trailing_commas.py`
(0 violations), `ruff format` (1 file left unchanged); verify pass
`ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all pass, and
`check_citations.py --check` passes on the whole tree (1297
citations resolve). No module first line changed, so no TREE.md
render owed.

Scratch paths and run ids: no scratch file created and no
workspace run id - state so. Every proof ran as a focused
`uv run pytest <node> --no-cov -n0` in the shared tree (the
dispatch's authorized form): pre-fix 2-node fail run; post-fix
2-node pass run; H1 (1) `1 passed`, H1 (2) `2 passed`, H1 (3)
`4 passed`; `-k async` `2 passed, 67 deselected`. The re-pass
verifier's Proofs run at `verify-mechanics-2`.

Fingerprints (`git hash-object`):

- Touched, before -> after:
  `django_strawberry_framework/connection.py`
  c8b9670109d05f9a09f2f8a113e491baa7511317 ->
  1fca6266cd5f748915875badf1881680b599de37.
  (This artifact is untracked and item-owned; no self-hash owed.)
- Read unchanged (equal to the pass-1 after-values):
  `tests/test_relay_connection.py`
  fe2b2d24ab6e71e6238183690b02821abb239497;
  `examples/fakeshop/test_query/test_keyset_api.py`
  88a432b0858c54afc91a79cedbf8938983ab2c23.
- Also read, no fingerprint owed (review inputs, not change inputs):
  AGENTS.md, START.md, REVIEW.md, worker-2.md, the plan, the three
  axis records with every Handoff, Cross-axis, Verification and V1
  section, this artifact's pass-1 section.

Proposed owned changes (delta rows only; amends the pass-1
`connection.py` row - no new path):

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/connection.py` | connection.py | Mechanics | `_consume_fallback` async arm (`untrimmed` bind for the V1 closure fix; sync trim + `_cap_offset_last_zero_page` unchanged) |

No bench delta for the plan's `## Bench baseline` (no figure moves),
no missing fixture for `## Decisions`, nothing disputed, blocked or
stopped.

Handoff: Pass 2 is the one-hunk V1 closure fix plus re-runs: both
async oracles green, H1 rows 1+2+4 green, `-k async` green, lint
gates green, zero new files. The re-pass verifier needs only the
V1 Proof node, the second async node, and the H1 rows at
`verify-mechanics-2`; Performance and Comments need no
re-verification (no number, prose, or sync byte moves - both
records say so explicitly).
