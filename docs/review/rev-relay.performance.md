# Review · Performance: `django_strawberry_framework/relay.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=04fd0769352ba604a1db2942738f8dab9f630b18

## Trace

Read the whole live target (634 lines) plus every caller and callee the hot
paths touch: the read resolvers (`DjangoNodeField` / `DjangoNodesField`
`_resolve`), the write primitive
(`django_strawberry_framework/relay.py::decode_model_global_id` and its
`_resolve_real_pk` lookup), the batch caller
(`django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids`
loop over
`django_strawberry_framework/utils/write_values.py::type_check_relation_id`),
the decode/coerce/stamp primitives
(`django_strawberry_framework/types/relay.py::decode_global_id`,
`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`,
`django_strawberry_framework/utils/querysets.py::model_for`,
`django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`,
`django_strawberry_framework/utils/lazy.py::unwrap_lazy_object`,
`django_strawberry_framework/utils/truth.py::name`),
the per-request guards
(`django_strawberry_framework/resource_policy.py::check_deadline`,
`django_strawberry_framework/utils/execution_mode.py::async_execution`),
the stamped id-attr default
(`django_strawberry_framework/types/relay.py::_resolve_id_attr_default`),
the package-root eager import, the own test module
(`tests/test_relay_node_field.py`, whole, for the NodeID fixtures and the
contract rows), and the fakeshop NodeID-non-pk shape (`PublisherType` /
`Publisher`). Orientation via `review_inspect.py` (its per-row `await` lead is
per-TYPE sequential gathering, discharged in R1).

Target fingerprint as read: `e75e2b66a9b406f60d55e952a001d640392331c1`.
`git diff ITEM_BASELINE -- django_strawberry_framework/relay.py` is empty: the
concurrent dirt predates the item baseline, and the file has not moved since.
Sibling axis records did not exist at review time (only the skeleton
`rev-relay.md`); the plan's Routed lead for this item (connection.py Comments,
observed: `test_relay_connection.py` temporal wordings plus bare
`(Decision 5)` pointer quality) is pure prose quality with zero Performance
content - judged out-of-axis, left for the owning Comments pass.

Cells: default only. Sharded and pg are inapplicable by construction: F1's
claim is a query COUNT on backend-agnostic ORM calls (`filter()` /
`values_list().first()`), reaching no alias or dialect decision; the
`using`-pin such a test passes through is orthogonal to the count. The
verifier judges; the gate re-runs any package-tier pin in all three suites
for free.

Probe evidence (all at `review/relay.py/performance`, package digest
`sha256:ecded019e560d47d15a90b09ad8e21899e087da4bbf0bf385f2cdef5855d7152`):

- `review-20260929T080627-f02d75`: query shape + CPU medians (4 passed).
- `review-20260929T080840-3e678a`: stamp breakdown (1 passed).
- `review-20260929T080849-c9b269`: importtime, 5 rounds.

Fingerprints of everything inspected (a finding's Freshness lists only files
beyond these): `django_strawberry_framework/relay.py` e75e2b66,
`django_strawberry_framework/types/relay.py` 4b2a9df5,
`django_strawberry_framework/utils/querysets.py` 8fc556d5,
`django_strawberry_framework/utils/truth.py` d5c96bc8,
`django_strawberry_framework/utils/lazy.py` 770f36ae,
`django_strawberry_framework/utils/write_values.py` 72f132f0,
`django_strawberry_framework/utils/execution_mode.py` 9805cdaf,
`django_strawberry_framework/resource_policy.py` cc3f9d80,
`django_strawberry_framework/mutations/resolvers.py` c9cff059,
`django_strawberry_framework/__init__.py` 0ef72601,
`tests/test_relay_node_field.py` af4866a1, `tests/conftest.py` fabb7d3c,
`examples/fakeshop/apps/library/schema.py` 9682db07,
`examples/fakeshop/apps/library/models.py` b980e82c,
`scripts/_bench_common.py` 253a3953, `docs/review/review-0_0_15.md` 46017cde,
`docs/review/rev-relay.md` 046befd1 (all `git hash-object`, abbreviated).

## Findings

### High

None.

### Medium

#### F1: one extra query per relation id for NodeID-over-non-pk-column types

- Observation: `django_strawberry_framework/relay.py::_resolve_real_pk`
  issues one `filter().values_list("pk").first()` query per
  `django_strawberry_framework/relay.py::decode_model_global_id` call
  whenever the decoded type's id slot is a concrete non-pk column (a
  consumer `relay.NodeID[...]` annotation). The batched set decoder
  `django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids`
  calls it once per member, so an M2M GlobalID set of K ids targeting
  such a type issues K extra queries before its one visibility query -
  N+1-shaped. The default `"pk"` shape issues zero (proven below).
- Evidence: probe `test_probe_decode_query_shape` at
  `review/relay.py/performance`, run `review-20260929T080627-f02d75`
  (`CaptureQueriesContext` over K direct `decode_model_global_id`
  calls, `Category` pk type vs `Category.name` NodeID type):
  pk shape K=1/2/4 -> 0/0/0 queries; nodeid shape -> 1/2/4 queries.
  The loop is `django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids`
  (`for value in provided_values` over
  `django_strawberry_framework/utils/write_values.py::type_check_relation_id`
  into `decode_model_global_id`). Reachable project shape: any M2M to a
  model whose primary Relay type carries a non-pk NodeID (fakeshop's
  `PublisherType.house_code` proves the shape; no live M2M targets it,
  so the pin lands at the package tier).
- Impact: every mutation attaching K GlobalIDs to such an M2M pays K
  small indexed SELECTs that one `id_attr__in` query could answer.
  Client-controlled K, per request on the write path.
- Severity: Medium. N+1-shaped, but gated on the rare NodeID-over-non-pk
  escape-hatch shape on the write path; the common pk shape is
  query-free. High is reserved for common-path N+1.
- Recommendation: batch the NodeID-to-pk mapping at
  `django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids`
  (the owner outside the target): decode + coerce each member without
  the per-id lookup, then resolve each distinct non-pk `(type,
  id_attr)` group's values with one `__in` query. Keep the
  single-id primitive as the single source of the status contract -
  add the batched mapping beside it in `relay.py` (or expose the
  pure decode/coerce half for the caller to compose), not a second
  decoder.
- Must not change: the `GlobalIDDecode` status contract per member
  (WRONG_MODEL / UNCOERCIBLE_PK incl. the no-row-maps-to-UNCOERCIBLE_PK
  rule), downstream visibility enforcement, the no-existence-leak
  property, and the `using` / active-pipeline alias pinning of the
  mapping query.
- Proof: `uv run python scripts/workspace.py run
  review/relay.py/verify-performance-<n> -- pytest
  tests/utils/test_write_values.py -k
  test_custom_node_id_relation_set_batches_real_pk_lookup --no-cov
  -n0` reports `1 passed`. The test is new (planned name in plain
  text; Worker-2 keeps it or reports the landed name): it decodes a
  same-type non-pk-NodeID set at K=1/2/4 and asserts constant total
  query counts plus the stated absolute. Fails on revert to per-id
  lookups.
- Freshness: none beyond Trace.
- Path class: hot - runs per input id of every mutation relation
  decode on the write path (per request per resolver).
- Instrument: `CaptureQueriesContext` probe (above); permanent
  package-tier query-count test.
- Before: 1 query per `decode_model_global_id` call on the non-pk
  shape (K=1/2/4 -> 1/2/4), 0 on the pk shape.
- After: constant queries across K for the non-pk shape (Worker-2
  measures; direction only: flat, absolute stated in the test).
- Delta: K-1 mapping queries removed per K-member set.

### Low

#### F2: eager `truth.name()` per node(s) request for an error-only argument

- Observation: both sync branches pass
  `owner=truth.name(resolved...)` into
  `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`
  (`django_strawberry_framework/relay.py::DjangoNodeField._resolve`
  per request; `django_strawberry_framework/relay.py::DjangoNodesField._resolve`
  per distinct type per request), but the guard uses `owner` only on
  the raise path - the success path returns the value unchanged. Every
  sync node refetch pays an MRO-walking name build it never reads.
- Evidence: probe median `truth.name(type)` 375.0 ns over 3000
  repeats, run `review-20260929T080627-f02d75`; guard body read (raise
  path alone formats `owner`).
- Impact: 375 ns of pure overhead on every sync `node(id:)` request
  (per distinct type on `nodes(ids:)`), removable without touching
  behavior.
- Severity: Low - bounded sub-microsecond saving on a hot path.
- Recommendation: guard the call with `inspect.isawaitable(result)`
  at both sites (the module already imports `inspect` and uses the
  same check one line down in the single resolver):
  awaitable -> call the guard as today; otherwise skip it. No
  signature change to the shared helper, no new seam.
- Must not change: `SyncMisuseError` raised with the identical
  message for coroutine/awaitable returns in sync context (incl.
  native-coroutine disposal); non-awaitable values returned
  unchanged.
- Proof: `uv run python scripts/workspace.py run
  review/relay.py/verify-performance-<n> -- pytest
  tests/test_relay_node_field.py -k test_sync_node_path_builds_no_owner_name
  --no-cov -n0` reports `1 passed`. The test is new (planned name in
  plain text; Worker-2 keeps it or reports the landed name): it
  counts `truth.name` calls over a sync single + batch refetch and
  asserts zero. Existing `SyncMisuseError` rows still pass
  unmodified.
- Freshness: none beyond Trace.
- Path class: hot - per request (single) / per distinct decoded
  type per request (batch) on the read path.
- Instrument: `timeit` median probe (above); permanent call-count
  pin test.
- Before: 1 `truth.name` call (375 ns median) per sync node
  request.
- After: 0 calls on the success path (Worker-2 measures).
- Delta: -375 ns per request, -1 MRO walk.

#### F3: `_node_id_slot` recomputed per id for one type

- Observation:
  `django_strawberry_framework/relay.py::_node_id_slot` (resolve the
  id attr + model + `_meta` field triple) is a per-TYPE constant, but
  it is recomputed per ID: N times per distinct type in the
  `django_strawberry_framework/relay.py::DjangoNodesField._resolve`
  coerce loop (via
  `django_strawberry_framework/relay.py::_coerce_pk_or_none`), and
  twice per
  `django_strawberry_framework/relay.py::decode_model_global_id` call
  (once in `_coerce_pk_or_none`, once in
  `django_strawberry_framework/relay.py::_resolve_real_pk`).
- Evidence: probe medians over 3000 repeats, run
  `review-20260929T080627-f02d75`: `_node_id_slot` 459.0 ns (pk
  shape) / 541.0 ns (non-pk `get_field` shape); call sites read.
- Impact: ~0.5 us of repeated `_meta`/registry/attr reads per
  redundant call - ~45 us on a 100-id same-type batch, ~0.5 us on
  every write-side decode - for a value that cannot change
  mid-request.
- Severity: Low - bounded sub-microsecond-per-id saving on hot
  paths.
- Recommendation: compute once per type per call path and thread it
  through the private helpers (a per-request memo dict in the batch
  loop; pass the slot from `decode_model_global_id` into the coerce
  and real-pk halves): all three `_coerce_pk_or_none` call sites are
  in-target and private, so no lifecycle state is needed. A
  co-cleared per-type module cache (the file's existing
  `register_subsystem_clear` precedent) is the alternative if
  Worker-2 finds the threading less plain; either shape must keep
  the unstamped-type live-scan fallback working.
- Must not change: the slot rule itself (`"pk"` -> `_meta.pk`,
  else `get_field`, `FieldDoesNotExist` -> `None`), the
  coerce-against-the-resolution-field contract (incl. the `"007"`
  non-pk case), and the pass-through for non-concrete NodeID attrs.
- Proof: `uv run python scripts/workspace.py run
  review/relay.py/verify-performance-<n> -- pytest
  tests/test_relay_node_field.py -k
  test_batch_coercion_computes_id_slot_once_per_type --no-cov -n0`
  reports `1 passed`. The test is new (planned name in plain text;
  Worker-2 keeps it or reports the landed name): it spies the slot
  computation over a 4-id same-type batch plus one write decode and
  asserts once per distinct type (batch) / once (write decode).
  Existing coercion rows still pass unmodified.
- Freshness: none beyond Trace.
- Path class: hot - per id per batch request; twice per write-side
  decode per request.
- Instrument: `timeit` median probe (above); permanent
  compute-count pin test.
- Before: N computations per N-id same-type batch; 2 per write
  decode (459/541 ns each).
- After: 1 per distinct type per batch; 1 per write decode
  (Worker-2 measures).
- Delta: -(N-1) x ~0.5 us per batch; -1 x ~0.5 us per write decode.

## Rejected

Looks-for map (every entry discharged): N+1/per-row queries -> F1,
R1; `len`/`bool` -> R8; `only`/`defer` -> R8; unbatched writes ->
R8; `blog.id`/`blog_id` -> R8; repeated `_meta`/settings/regex/
schema-type lookups -> F3, R3, R4; `lru_cache` on methods -> R8;
locks/cache/re-parse/round trips -> F1, R4, R7; import-time cost ->
R6; walk allocation -> F2, R9, R11. R2, R5, R10 are read-path
micro-rejections with numbers.

- R1: READ-path query shape is already batched. `node(id:)` issues
  one `resolve_node` query per request; `nodes(ids:)` groups by
  decoded type and issues one `resolve_nodes` call per distinct type
  (Decision 4, read at both branches plus the async gather).
  `review_inspect.py`'s per-row `await` lead is per-TYPE sequential
  gathering, required by the documented Django async-ORM connection
  rule and the "single gathering coroutine" spec promise - not a
  per-row await. Trigger: a batch test showing queries scaling with
  row count within one decoded type.
- R2: `django_strawberry_framework/relay.py::_stamp_node_type`
  costs 4417 ns/row, but `copy.copy` alone is 2667 ns (60%, run
  `review-20260929T080840-3e678a`) and the copy is the documented
  cross-request isolation requirement, not overhead; the remainder
  (`unwrap_lazy_object` 375 ns + one `static_attr` + two truth
  type checks + one `setattr`) is the truthful minimum for a
  routing stamp on hostile consumer returns. Hoisting the per-type
  reads would save a fraction of a dominated cost. Trigger: a node
  profile attributing over 10 percent of per-row time to the
  stamp's type reads excluding the copy.
- R3: `django_strawberry_framework/types/relay.py::decode_global_id`
  costs 3292 ns/id (run `review-20260929T080627-f02d75`) for one
  base64 parse plus one registry lookup per step - single-pass,
  no repeated sub-work, and the single source three call paths
  share. The steady-state `resolve_id_attr` is one `__dict__` read
  (`django_strawberry_framework/types/relay.py::_resolve_id_attr_default`;
  the finalize stamp exists precisely to kill the per-row rescan).
  Trigger: a second registry/`_meta` lookup per decode appearing,
  or a future batch-decode API making per-id decode the bottleneck.
- R4: `django_strawberry_framework/resource_policy.py::check_deadline`
  runs once per node(s) request; the unarmed path is one
  `ContextVar.get()` (`_armed_budget`, read) plus O(1) compares -
  no settings read, no regex, no lock, no cache, no query.
  Trigger: the armed-budget path appearing in a request profile.
- R5: `django_strawberry_framework/relay.py::_check_nodes_result`
  runs `truth.own_attr(type(result), "__len__")` once per distinct
  type per batch (sub-microsecond MRO walk on the exact result
  type), the truthful sized-vs-iterator discriminator the
  positional contract needs. Trigger: relocation to per-row, or a
  measured cost over 1 us per type.
- R6: import-time cost is negligible. `relay.py` self time 301 us,
  cumulative == self (pulls in nothing new at its position - every
  import is already in the package closure), 0.13 percent of the
  236 ms package import; module-level work is one
  `register_subsystem_clear` plus Enum/NamedTuple defs; no settings
  read at import (run `review-20260929T080849-c9b269`, 5 rounds,
  instrument `15f679c9`, package digest as in Trace). The package
  root imports it eagerly, so this figure is the full story.
  Trigger: a new third-party/heavy module import at relay top, or
  self time over 1 ms.
- R7: the lazy `current_write_pipeline` import inside
  `django_strawberry_framework/relay.py::_resolve_real_pk` is a
  `sys.modules` hit (sub-100 ns class) on the non-pk write path
  only, directly before the query it serves, and a documented
  import-cycle dodge. Trigger: F1's batching landing (hoist the
  import with the batched query) or relocation onto a query-free
  hot path.
- R8: absent shapes. No `len(qs)`/`bool(qs)` (the five `len()`
  calls are over materialized lists), no `only()`/`defer()`, no
  writes (nothing for `bulk_*` to batch), no FK dereference
  (`blog_id` has no site), no `lru_cache` on methods, no locks,
  cache reads, or re-parses on any request path. Trigger:
  introduction of any such shape.
- R9: the three-pass id loop (decode-all, typed-check-all,
  coerce-and-group) costs ~2 extra list iterations (~100 ns/id
  class) against the phase structure Decision 5 documents
  (decode-everything-before-any-query). Fusing would tangle three
  contracts in one loop to save noise. Trigger: batch sizes where
  3N iteration shows in a request profile.
- R10: `django_strawberry_framework/relay.py::_check_typed_match`
  is an identity comparison with `__django_strawberry_definition__`
  reads on the raise path only; the success path allocates
  nothing. Trigger: success-path attribute reads added.
- R11: assembly and cold code. `django_strawberry_framework/relay.py::_interleave`,
  `django_strawberry_framework/relay.py::_await_and_stamp`, and
  `django_strawberry_framework/relay.py::_decode_or_graphql_error`
  are result assembly with no repeated work; both factories'
  bodies, `django_strawberry_framework/relay.py::_validate_node_target`,
  `validated_field_directives`, and the `GlobalIDDecode` /
  `DecodeResult` defs run at construction/import only. Trigger:
  per-row relocation of any factory-time work.

No bench-baseline figure moves: F1 is pinned by a query-count test
(counts, not bench timings), F2/F3 are sub-microsecond CPU micros
pinned by call-count tests plus the `timeit` medians above - all
below bench spread by construction.

## Cross-axis (for Comments)

### C1: `type_check_relation_id` promises no DB fetch; the GlobalID branch fetches

- Observation: `django_strawberry_framework/utils/write_values.py::type_check_relation_id`
  is documented "Type-check + coerce ONE relation id to a pk WITHOUT
  a DB fetch" with "Neither branch touches the DB - visibility is
  confirmed separately by the caller." But its GlobalID branch calls
  `django_strawberry_framework/relay.py::decode_model_global_id`,
  whose `_resolve_real_pk` step issues a query for every
  NodeID-over-non-pk-column id (F1's probe: 1 query per call) - and
  the shape is live in fakeshop (`PublisherType.house_code`). The
  promise holds only for the pk shape. (F1's batching does not cure
  this: a batched mapping still queries, so the docstring needs the
  reword regardless.)
- Evidence: docstring first line + "Neither branch touches the DB"
  sentence read at fingerprint 72f132f0; F1's 1/2/4-query probe.
- Impact: a reader composing write-decode query budgets (or
  auditing the no-hidden-query property the sentence advertises)
  undercounts by one query per non-pk-NodeID id.
- Severity: Medium (stale contract sentence on a shared helper;
  the Comments verifier grades the landed text).
- Recommendation: reword to the true contract at the owner
  (`django_strawberry_framework/utils/write_values.py::type_check_relation_id`):
  the pk branch touches no DB; the GlobalID branch resolves a
  non-pk NodeID value to its real pk with a query (batched per
  set after F1), visibility still confirmed separately. NOTE for
  Worker-0: the sentence lives in the `utils/write_values.py`
  item's file - re-route there if F1's implementation does not
  touch that file; recorded here because F1's orbit owns the
  triggering fact.
- Must not change: n/a (prose finding).
- Proof: `rg -n "Neither branch touches the DB" django_strawberry_framework/utils/write_values.py`
  prints 0 lines, and the landed docstring first line no longer
  claims WITHOUT-a-DB-fetch unconditionally (Comments verifier
  grades the whole docstring true).
- Freshness: none beyond Trace.

Handoff: read the whole target, all three hot paths (read single,
read batch sync+async, write decode single+set), and the own test
module whole; no sibling records existed to cross-read. Findings:
one Medium (F1, per-id mapping query, owner outside the target at
`decode_visible_relation_ids`), two riding Lows (F2 eager owner
name, F3 repeated slot computation), one Comments cross-axis (C1,
conditionally re-routable to the write_values item). Everything
else on the looks-for list is rejected with a trigger; the two
review_inspect leads (per-row await, import-time call) both
discharged as non-issues. The incoming Routed lead is prose-only
and stays with the Comments pass. Open threads for the verifier:
F1's Proof node id is proposed (Worker-2 lands the name; the
property - constant counts across K=1/2/4 plus a stated absolute -
governs); F3's fix shape is Worker-2's choice (threading vs
co-cleared cache) with the compute-count property governing. No
bench figure moves; no sensitivity concerns; cells beyond default
stated inapplicable with reasons for the verifier to judge.

## Verify performance

Precondition: the live tree carries exactly the change under
grade. `git hash-object` on the four touched paths gives
`relay.py` f5760b45, `utils/write_values.py` 13548c76,
`tests/test_relay_node_field.py` d4ce0c7d,
`tests/utils/test_write_values.py` 9f459e2f - the end-state blob
ids of `docs/review/temp-tests/relay/diff/pass-1.diff`.
`git diff ITEM_BASELINE --stat` names no other source or test
file (only concurrent `docs/dry/dry-0_0_15.md` growth and plan
lines). All four landed test names equal the record's planned
names, so every Proof below ran in its recorded form.

All runs at `review/relay.py/verify-performance-1` (slot-3,
package digest `sha256:d677641c...`, copy `fresh` on every run).
Worker-2 chose F3's threading shape (per-request memo dict plus
`slot=` kwargs); no co-cleared cache exists, so no lifecycle
state was added.

### F1: batched mapping - pass

- Count pin `test_custom_node_id_relation_set_batches_real_pk_lookup`:
  `review-20260929T092136-12f47a`, `1 passed`. The test asserts
  exactly 2 queries (one `__in` mapping plus one visibility) at
  each of K=1/2/4 - constant across K with the absolute stated -
  and exactly 1 query (mapping alone, no visibility) for the
  no-row member. The property governs and it holds.
- Failability: `review-20260929T092316-931612` (`prove`, manifest
  `failability-verify.json`, pre-images byte-identical to
  ITEM_BASELINE): reverting `write_values.py` to the per-id
  loop fails exactly the count pin (`pinned`); the alias pin
  below passes on both sides (`behaviour preserved`), as a
  preserved-behavior pin must.
- Status contract: the decode/model-check/coerce lines moved
  verbatim into `_decode_and_coerce` (same `WRONG_MODEL` /
  `UNCOERCIBLE_PK` arms, same no-row-maps-to-`UNCOERCIBLE_PK`
  rule now via the batched `None`); every non-`OK` status takes
  the same uniform-error line it took before. The no-row leg is
  pinned by the count pin itself; the existing wrong-model /
  malformed legs (`test_decode_visible_relation_ids_accepts_global_id_members_with_one_query`)
  are green in the full-module run below, and the live
  WRONG_MODEL / UNCOERCIBLE_PK rows over HTTP (4 wrong-type +
  2 uncoercible across model and form flavors) pass in
  `review-20260929T093109-20fde8`, `6 passed`.
- Equivalence notes (read, not just run): input order is
  preserved positionally; `.first()` semantics survive as
  first-match-wins over the unordered pair list; the Python-side
  `attr == wanted` match agrees with SQL `=` on every supported
  backend (SQLite/Postgres `=` is case-sensitive; both sides pass
  through the same `to_python`/`from_db` normalization); every
  `pending` member carries a memoized slot, so the `slots[...]`
  read cannot miss; the decode-before-any-query phase structure
  (Decision 5) is intact - mapping still precedes visibility.
- Alias pinning: `test_custom_node_id_relation_set_mapping_uses_pipeline_alias`,
  `review-20260929T092144-229c6e`, `1 passed`. The pin isolates
  the mapping query: the visibility path in this flow calls
  `manager.all()`, never `manager.using(...)` (read at
  `utils/querysets.py::base_queryset` / `related_visibility_queryset_or_default`),
  so `using.assert_any_call("default")` can only be satisfied by
  `_resolve_real_pks_batched`. Targeted mutant (recovery block
  neutered, anchor-matched exactly once):
  `review-20260929T092820-179cb8`, `pinned` - the pin fails
  exactly when mapping recovery goes missing.
- No-existence-leak: the mapping still runs on the default
  manager with visibility enforced downstream, and no-row /
  hidden / missing all collapse to the same uniform error; the
  hidden/missing rows are green in the full-module run.

### F2: isawaitable guards - pass

- Pin `test_sync_node_path_builds_no_owner_name`:
  `review-20260929T092154-caa36a`, `1 passed`: zero `truth.name`
  calls over a sync single plus a sync batch refetch (spy scoped
  to this module's own `truth` reference).
- Failability: same `prove` run as F1 (`review-20260929T092316-931612`):
  reverting `relay.py` to the unconditional guard calls fails
  exactly this pin (`pinned`).
- Raise path unchanged: the three `SyncMisuseError` rows
  (`test_node_sync_with_async_consumer_resolve_node_raises_sync_misuse`,
  `test_nodes_sync_with_async_consumer_resolve_nodes_raises_sync_misuse`,
  `test_node_sync_async_get_queryset_raises_sync_misuse`) pass
  unmodified - awaitables still reach the identical guard call
  (message, disposal, recourse untouched); only non-awaitables
  skip it.

### F3: slot threading - pass

- Pin `test_batch_coercion_computes_id_slot_once_per_type`:
  `review-20260929T092202-55ab5a`, `1 passed`: one `_node_id_slot`
  computation for a 4-id same-type batch and one for a single
  write decode - the once-per-type / once-per-decode property.
- Failability: same `prove` run (`review-20260929T092316-931612`):
  reverting `relay.py` to per-call resolution fails exactly this
  pin (`pinned`).
- Slot rule intact: the rule body is untouched (only call sites
  thread the value); the coerce-against-the-resolution-field
  contract rows (`test_node_custom_node_id_attr_resolves`,
  `test_node_custom_node_id_attr_uncoercible_returns_null`,
  `test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id`,
  the three `decode_model_global_id` rows) pass unmodified.

### Regression sweep

Both touched modules whole, default cell:
`review-20260929T092217-85090e`, `60 passed` (30 + 30, zero
failures) - every pre-existing row in the item's orbit,
including all `SyncMisuseError`, coercion, visibility-count and
single-decode rows, is green beside the four new pins.

### Cells

I judged the reviewer's inapplicable-by-construction claim
sound (the F1 claim is a query COUNT over backend-agnostic ORM
calls with no dialect branch; F2/F3 count Python calls, not
queries; the one alias decision is covered by a
backend-independent mock pin) - and then ran every cell anyway:
sharded (`review-20260929T092446-581d68` F2+F3, `2 passed`;
`review-20260929T092508-04c053` F1, `2 passed`) and pg
(`review-20260929T092835-ebf773` F1, `2 passed`;
`review-20260929T092928-59d137` F2+F3, `2 passed`). No
`unverified` cell remains; the gate re-runs these pins in all
three suites for free.

### Bench rows

No bench row moves. None of the four bench instruments executes
the changed paths (write decode, node-resolver sync guards);
the claims are pinned by query-count and call-count tests plus
the record's `timeit` medians, all below bench spread by
construction. The one row the L1 hoist could touch is
importtime: `review-20260929T092737-f71c23` (5 rounds,
instrument `15f679c9`, same id as the reviewer's R6 probe)
gives `relay.py` self 299 us, cumulative == self (the hoisted
import pulls in nothing new - already in the root closure),
far under R6's 1 ms trigger. Module count 69 vs the reviewer's
67 is the concurrent `lazy.py` + `truth.py`, predating
ITEM_BASELINE, not this item.

### Rejections R1-R11

All stand; no trigger tripped. Read-path batching (R1), stamp
cost (R2), decode shape (R3), deadline (R4), length-check (R5),
absent shapes (R8 - the new code's `len()` is over a
materialized list, no `only`/`defer`/`lru_cache`/locks added),
three-pass phase structure (R9), typed-match (R10),
assembly/cold code (R11) are all untouched or preserved.
R6 holds by the importtime run above. R7's trigger (hoist the
import with F1's batching) is exactly what landed via Mech L1;
its premise sentence ("documented import-cycle dodge") is
corrected by the Mechanics Handoff (no comment names a cycle,
hoist proven green, site absent from the spec-053 whitelist) -
noted, not blocking, and L1's landing moots it.

### Prose

The item's prose edits disturb no Performance claim. Every
sentence with performance content grades true against the pins:
`_decode_and_coerce` "query-free half" (no ORM call in the
body); `_resolve_real_pks_batched` "one query per `(type,
id_attr)`" + `.first()` semantics (the count pin); the slot
"once per type / once per decode" paragraphs (F3 pin);
`type_check_relation_id` "raw-pk branch touches no DB;
GlobalID branch resolves ... (batched per set)" (Perf C1, the
true contract); `decode_visible_relation_ids` "(i)
type-checked query-free first ... one `__in` query per group"
(the count pin). The remaining prose (Mech C1 consumer census,
Mech C2 sub-cases, Comments F1-F6 pointers/ordinals, deadline
comments) carries no performance content. (Grading the landed
text is the Comments verifier's; this axis confirms nothing
here contradicts its numbers.)

Scratch: `docs/review/temp-tests/relay/verify-performance-1/`
(`failability-verify.json`, `failability-alias.json`,
`importtime-after.json`).

Status: verified

Handoff: F1/F2/F3 all pass with failability shown two ways for
the load-bearing F1 (whole-file revert fails the count pin
only; targeted recovery-neutering fails the alias pin only).
Landed names equal planned names, so the record's Proof lines
ran verbatim. Judgment calls for a later reader: (1) the
`==`-vs-`=` equivalence argument rests on the supported
SQLite/Postgres matrix (case-sensitive `=`) - a future
case-insensitive-collation backend would reopen it; (2) the
alias pin's isolation rests on the visibility path never
calling `manager.using` in this flow (read, plus the mutant);
(3) pg/sharded runs were belt-and-braces beyond the
inapplicable-by-construction claim, all green. No open threads
on the Performance axis; no new defects.
