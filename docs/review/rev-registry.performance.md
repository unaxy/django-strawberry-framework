# Review · Performance: `django_strawberry_framework/registry.py`

Status: no-findings
Run: 0.0.15 2026-09-28-3
Path class: hot — `TypeRegistry.model_for_type`, `TypeRegistry.get` and
`TypeRegistry.get_definition` run per resolver, plan edge and filter
application on live requests, and
`TypeRegistry.definition_for_graphql_name` runs per type-name GlobalID
decode; the mutators (`register`, `unregister`, `clear`,
`discard_pending`) are import/finalize/test cold.

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=da5c1882de6a2330b1ce41878b78c073ef5a36b4

## Trace

Read the whole live target (`django_strawberry_framework/registry.py`,
lines 1-641, `git hash-object` 492654d219d1061fef33f186d962dc5369b71ebe).
The target is dirty with concurrent work: HEAD blob 81bd561c, live diff
54 insertions / 23 deletions. Every figure below measures the live bytes.

Callers traced in and out (hot readers first):

- `django_strawberry_framework/optimizer/extension.py:832` —
  `model_for_type` per resolver per request (origin-to-model trace);
  `:1629` — `model_for_type` per connection field per request.
- `django_strawberry_framework/optimizer/walker.py:465-466,506-509,1459`
  — `get` + `get_definition` per relation edge per plan build.
- `django_strawberry_framework/types/resolvers.py:367,400-403` —
  `get_definition` / `get` per relation-resolver invocation.
- `django_strawberry_framework/filters/sets.py:2126,2896` and
  `django_strawberry_framework/utils/querysets.py:4181` — `get` per filter
  application per request.
- `django_strawberry_framework/types/relay.py:836` — the single production
  caller of `definition_for_graphql_name`, on the type-name branch of
  `decode_global_id`, reached per wire GlobalID via
  `django_strawberry_framework/relay.py:119` (node/nodes fields, per
  element) and `:320` (mutation typed-id decodes).
- Cold readers: `types/finalizer.py` (finalize loops over `iter_types`,
  `iter_definitions`, `iter_pending_relations`, `models_with_multiple_types`),
  `management/commands/inspect_django_type.py:180-191` (management command),
  `auth/mutations.py:1293-1297` + `mutations/sets.py:1340-1343`
  (`types_for` on the error path only, after `get` returns `None`).

Storage cost read at
`django_strawberry_framework/utils/truth.py::IdentityMap`: `get`,
`__getitem__`, `__setitem__`, `pop`, `setdefault`, `__contains__` are one
`id()` dict probe each; only `items` / `keys` snapshot (used by finalize-,
audit- and test-time iterators, never by a hot reader).

Orientation: `review_inspect.py` (no per-row DB leads, no in-module hot
entry points, import-time work = the sentinel + the singleton) under
`docs/review/temp-tests/registry/performance/inspect/`.

Routed lead on the plan item (from connection.py Comments:
`tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule`
docstring vs the `clear()` callback replay; order/relay twin staleness):
judged out of axis. It grades prose truth about `clear()`, a test-only
cold path, with zero performance content. Returned to Worker-0 for the
Comments pass; nothing recorded here beyond this paragraph.

Database cells: default, sharded and pg are all inapplicable by
construction. The target reaches no database, alias or dialect decision:
pure in-memory identity maps, zero ORM imports and zero ORM calls (sweep
for `filter` / `exists` / `count` / `objects.` / `_meta` / `bulk_` /
`settings` / `re.compile` / locks finds only `_meta` inside the
`model_for_type` docstring). The instruments below bootstrap the
workspace copy's in-memory SQLite database per `scripts/_bench_common.py`
and prove nothing about another cell; there is nothing cell-specific to
prove.

Looks-for discharge (each entry: finding, none+reason, or rejection):

- N+1 / per-row queries: none. Zero queries issued; the only per-wire-value
  scan is the CPU-only name scan (see R1).
- `len(qs)` / `bool(qs)`: none. No querysets in the file.
- `only()` / `defer()`: none. No querysets in the file.
- Unbatched writes: none. No database writes in the file.
- `blog.id` vs `blog_id`: none. No FK traversal in the file.
- Repeated `_meta` walks: none. No `_meta` access in code.
- Repeated settings reads: none. No settings access in the file.
- Repeated regex compilation: none. No regex in the file (the
  `fullmatch` inside the definition name property belongs to
  `types/definition.py` and is read, not compiled, per scan row).
- Repeated schema/type lookups per request: hot readers are O(1)
  (`get` 0.19 us, `model_for_type` 0.11 us, `get_definition` 0.11 us,
  medians, run `review-20260929T072704-edcccf`); the O(N) decode scan is
  R1 (rejected) and its reorder variant is R2 (rejected, measured worse).
- `lru_cache` on methods: none. No cache decorator in the file.
- Locks / cache reads / re-parses / round trips on a per-request path:
  none. No locks; the in-function `types.relay` import is a `sys.modules`
  hit the import cycle requires (R3).
- Import-time cost: none. Module self time 162 us (minimum over 5 rounds,
  run `review-20260929T073109-318dc7`), 0.5% of the 29.6 ms package self
  total; top imports are stdlib + `django.db.models` + three light locals
  (`exceptions`, `utils.truth`, `utils.imports`, itself 68 us self), with
  the heavy `types.relay` edge kept in-function and the definition types
  under `TYPE_CHECKING`.
- Allocation in the walk: none chargeable here. `types_for` tuples on the
  error path only (cold); `iter_subsystem_clears` tuple per test-only
  `clear()`; `discard_pending` set+list per finalize drain (R4);
  `iter_definitions` snapshot per decode scan (~1-2 us of the R1 figure,
  left in place).

Fingerprints (`git hash-object`) of every file inspected: registry.py
492654d2, types/relay.py 4b2a9df5, relay.py e75e2b66,
optimizer/extension.py 39a8739c, optimizer/walker.py d5759ef8,
types/resolvers.py 640905c6, filters/sets.py e47c6758,
utils/querysets.py 8fc556d5, mutations/sets.py 21c15c0b,
auth/mutations.py 84183c89, types/definition.py 1c59a3fe,
utils/truth.py d5c96bc8, utils/imports.py 291ecedd,
types/finalizer.py b9d8acb2, inspect_django_type.py bb63204c,
testing/relay.py f807bf92 (each the 8-char prefix of the full object id
reported to Worker-0).

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

### R1: index over the decode-time name scan

The scan in
`django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name`
(`implements_relay_node` + `graphql_type_name` equality over all 82
finalized fakeshop definitions, 16 of them Relay-Node, full list built
with no early exit so the ambiguity error names every collider) costs
65.8 us per type-name decode (timeit median, 7 repeats x 2000 iterations,
run `review-20260929T072704-edcccf`, package digest
`sha256:04203a6a...`, `_bench_common.py` blob 253a3953): 82
`implements_relay_node` probes per call and 94% of the 69.8 us type-name
`decode_global_id` measured in the same run. It is linear in definition
count (~0.8 us per definition), runs per wire GlobalID on the type-name
branch (node/nodes per element, mutation typed-id decodes), and runs
before the strategy gate, so strategy-doomed and attacker-crafted
type-name payloads pay it too. A lazily built name-to-definitions index,
reset by `register_definition` / `unregister` / `clear`, would cut it to
sub-microsecond.

Rejected: the saving cannot stay as plain as the scan. The index needs
lifecycle resets across three mutators plus byte-identical miss and
ambiguity messages (the ambiguity message joins every collider, which is
why the scan builds the full list), all to save ~65 us on the minority
decode branch — the default `model` strategy decodes via O(1)
`apps.get_model` + `TypeRegistry.get`, and every successful decode is
followed by at least one database round trip an order of magnitude
costlier. The method docstring already reserves the single-inverse
decision to its own trigger.

Trigger: re-run `probe_decode.py` at
`review/registry.py/performance` and the scan median exceeds 250 us
(definition growth toward ~300, or a second production caller beside
`types/relay.py:836`), or a measured request profile shows type-name
decodes dominating — then index the Relay-Node definitions grouped by
name, preserving the exact miss/ambiguity texts.

### R2: name-first conjunct reorder in the scan

Same scan as R1. Reading the name equality before
`implements_relay_node` looks cheaper (skip the `issubclass` for the 66
non-matching definitions) but measures worse: 65.4 us shipped order vs
131.9 us name-first (interleaved timeit medians, 9 x 2000, identical
single-match result asserted, run `review-20260929T072949-aeeff7`). The
`graphql_type_name` property re-validates on every read (type check, copy
and regex `fullmatch`), so it costs ~1.6 us a row — more than the
`issubclass` it would skip. The shipped order is already the cheap
predicate first.

Rejected: measured anti-saving, plus a behavior edge (the property raises
on invalid names, which the reorder would read for non-Node definitions
the shipped order never touches).

Trigger: the definition name becomes a stored attribute (validate once);
re-measure both orders before touching the conjuncts.

### R3: hoisting the in-function `types.relay` import

`definition_for_graphql_name` imports `implements_relay_node` per call.
A `sys.modules`-hit import costs ~0.1 us against the 65.8 us scan, and
the module top cannot take the edge: `types/relay.py` imports back toward
the registry at decode time, and the in-function shape is the documented
cycle dodge on both sides.

Trigger: the import cycle is removed at the owner; the hoist then rides
that change.

### R4: batching `discard_pending` across the finalize drain

`django_strawberry_framework/registry.py::TypeRegistry.discard_pending`
rebuilds the pending list (id-set + comprehension) per call from the
per-entry finalize loop — quadratic in pending count. Finalize runs once
per schema build (cold), the shape keeps the module independent of
`PendingRelation` equality by documented contract, and no bench figure
moves with it.

Trigger: a measured finalize-time profile names this drain; batch at the
finalizer (the owner of the per-entry loop), not here.

## Cross-axis

None. No out-of-axis findings; the plan's Routed lead is prose for the
Comments pass (see Trace) and is returned, not re-recorded.

Handoff: read the whole live target plus every caller above; the one hot
cost worth measuring (the decode scan) is rejected with numbers, and the
tempting reorder is measured worse, so neither should be re-raised
without the stated triggers. Open threads: none on this axis. The sibling
axes run concurrently and their records did not exist when this record
closed; the Comments pass owns the Routed `test_registry.py` docstring
staleness. `Path class: hot` is set in this record's header for the plan
item. Scratch under `docs/review/temp-tests/registry/performance/`
(probes, import-time JSON, inspect output); workspace runs
`review-20260929T072704-edcccf`, `review-20260929T072949-aeeff7`,
`review-20260929T073109-318dc7` (plus two superseded exit-1 probe runs
whose figures the exit-0 reruns replace).

## Verify performance

No-findings stands. Pass-1 moves no number: the whole
`docs/review/temp-tests/registry/diff/pass-1.diff` is prose plus
test-only pins. `django_strawberry_framework/registry.py` carries
exactly three docstring hunks (F4 `iter_types` real-consumer
sentence, F7 `register_with_definition` imperative first line, F8
`_detach_type_from_model` helper-bound clause) and the inverse
proof holds: `review_inspect.py --code-digest
da5c1882de6a2330b1ce41878b78c073ef5a36b4:django_strawberry_framework/registry.py
django_strawberry_framework/registry.py` exits 0 with two equal
digests (`sha256:3949c414...`), so production code is
byte-identical modulo docstrings. The remaining three files are
`tests/test_registry.py` (F1/F2/F3/F5/F9 prose, F10 one-line
rename, L1 two new `pytest.raises` rows asserting already-true
guard behavior), `tests/orders/test_composition.py` (F6 one-line
mechanism wording), and `docs/SPECS/spec-018-meta_primary-0_0_6.md`
(F10 test-name sweep). F11 deferred and untouched, as recorded.

Disturbance check: live `git hash-object` prefixes match the
diff's post-images exactly (registry.py `27358cbc`,
test_registry.py `8bd9a869`, test_composition.py `9414d257`,
spec-018 `9f7c3784`) and the diff's pre-images match the review
fingerprints (`492654d2`, `48af782f`, `d0cc8722`), so live is
pass-1 applied on ITEM_BASELINE with no concurrent drift in any
touched file. Every review figure (hot readers 0.19 / 0.11 /
0.11 us, decode scan 65.8 us, import-time self 162 us) still
measures the same executable bytes: no bench row moves, and no
bench rerun is owed by a prose-only change. Rejection triggers
re-checked: R1 (no definition growth, no second production caller
of the scan), R2 (conjunct order untouched), R3 (import cycle and
in-function edge untouched), R4 (finalize drain untouched) — all
four stand.

Cells judged: concur `inapplicable by construction` for default,
sharded and pg. Own sweep of the live target for
`.filter(`/`.exists`/`.count`/`objects.`/`_meta`/`bulk_`/`settings`/`re.compile`/`using=`/`connections[`
finds exactly one hit, `_meta` inside the `model_for_type`
docstring (prose, line 376); the module is pure in-memory maps
with typing-only `django.db.models` and zero queries. No
cell-specific proof owed.

Smoke: `review-20260929T075012-5c751d` (address
`review/registry.py/implement`, cell default, fresh copy;
`pytest tests/test_registry.py --no-cov -p no:cacheprovider -q`),
80 passed, exit 0. The copy provably carries pass-1 bytes
(F10/F4/L1 markers present, copy `md5` of `tests/test_registry.py`
equals live). Provenance header under
`docs/review/temp-tests/registry/verify-performance-1/smoke-stderr.txt`.

Handoff: nothing beyond this section was read or written. Open
threads: none on this axis.

Status: verified
