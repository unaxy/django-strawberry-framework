# DRY review: `sealed-execution-queryset`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Rule: the sealed-execution queryset. Querysets are sealed against consumer
evaluation so visibility and permission decisions execute inside the boundary.
Provisional owner [querysets.py][querysets] `::_seal_or_defect`, confirmed
below. GOAL.md trust-boundary mechanism: consumer Python is trusted but its
RESULTS are validated ([GOAL.md][goal] #"Application Python - resolvers").

What "sealed" means operationally:

- Every read of candidate state comes from the instance `__dict__` via
  `object.__getattribute__`, never through attribute access, so a custom
  `__getattribute__`, an instance-shadowed callable, or a redefined
  `query` / `_query` descriptor cannot run code or return a lie.
- The extracted state is validated (concrete table, base-table alias map,
  exact-`sql.Query` type, exact-builtin containers, identity-proved genuine
  Django AST nodes, Django row-iterable membership, deferred-filter shape,
  recursive prefetch-child seal, policy axes), then rebuilt as a fresh
  framework-owned plain `models.QuerySet`. The seal NEVER returns the
  consumer object.
- Violation inside `_seal_or_defect` returns `(None, (code, detail))`; every
  surface raises `ConfigurationError` (source seals via
  `_prepared_visibility_source`, hook-result seals via
  `_normalized_visibility_result` / `_visibility_result_error`, post-OrderSet
  seals via `_validate_post_orderset_result`, raw-list seals via
  `normalized_row_source` / `_raw_list_source_message`). No surface returns a
  defect object to a caller.
- Codes run `type` -> `table` -> `untrusted` -> `routing` -> `evaluated` ->
  `sliced` -> `combined` -> `projection` -> `alias`: one canonical ordering
  every site shares; each message site renders only the subset it can reach,
  and `_defect_message` fails loud on an unrendered code.
- There is no unseal. Downstream framework transforms compose onto the sealed
  object; the consumer original never re-enters. No identity fast path exists
  (`result is queryset` is re-sealed: a hook may mutate and return the same
  object). `_result_cache` is dropped by every policy except
  `_RAW_LIST_SOURCE_POLICY`, which carries an exact-`list` forward.

Seal sites (all compose `_seal_or_defect` by name; six `_SealPolicy`
constants declare the per-surface variation):

- [querysets.py][querysets] `::_seal_or_defect` — definition. `::_SealPolicy`
  plus `_DEFAULT` / `_CASCADE` / `_PREFETCH_CHILD` / `_LIST_ARGUMENT` /
  `_ORDERSET_RESULT` / `_RAW_LIST_SOURCE` policies — variation declarations.
  `_prepared_visibility_source`, `_normalized_visibility_result`,
  `_validate_post_orderset_result`, `_snapshot_routing_intent`,
  `normalized_row_source`, `materialized_rows`, `prepared_resolver_source`,
  `post_process_queryset_result_sync/async`, `apply_type_visibility_sync/async`
  — composing consumers inside the owner module.
- [permissions.py][permissions] — consumer: root source prep plus per-edge
  hook-result seal under `_CASCADE_SEAL_POLICY` with bespoke path renderers.
- [list-field.py][list-field] — consumer: no-argument and
  `_LIST_ARGUMENT_VISIBILITY_POLICY` seals both colors, plus
  snapshot/validate around consumer `OrderSet.apply_*`.
- [walker.py][walker] — consumer: `_build_child_queryset` seals the planned
  prefetch child under `_PREFETCH_CHILD_POLICY` (ledgered D1 fix `fd39cac6`).
- [connection.py][connection] — consumer: both pipelines seal via
  `apply_type_visibility_*` off the `prepared_resolver_source` head; plus its
  own pre-boundary `_guard_source_not_pre_sliced` (Finding R-guard).
- [resolvers.py][type-resolvers] — consumer: related-object recheck seals,
  prefetch-cache reads via `normalized_row_source` / `materialized_rows`,
  windowing via `bounded_rows`.
- [resource-policy.py][resource-policy] — consumer: `bounded_rows` /
  `_windowed_rows` seal subclasses via `normalized_row_source` before slicing.
- Sweep-found consumers beyond the plan list: [relay.py][types-relay] (node
  defaults, four seals), [filter-sets.py][filter-sets] (related-visibility
  child seals, both colors), [mutation-resolvers.py][mutation-resolvers]
  (write-pipeline locate seal). Worker 0: extend the index row's files.
- Excluded: [resource-policy-ext.py][resource-policy-ext] carries no seal
  mechanism (document-budget `ResourcePolicy`; different "policy" word).

Dirty-file verification (read freely, edited nothing):

- `connection.py` + `extensions/resource_policy.py` external dirt confirmed
  vs `git show HEAD:`: cursor-guard feature (`_offset_cursor_prefix`,
  `_reject_negative_offset_cursor`, fallback branch) and `charge_document`
  budget arms (`_charge_directive_values`) — neither touches a seal site.
- [list-field.py][list-field] dirt is the ledgered
  `relay-node-target-guard` docstring clause, not seal code.
- Core (`querysets.py`, `permissions.py`, `walker.py`,
  `types/resolvers.py`, root `resource_policy.py`) clean at HEAD; D1 fix
  `fd39cac6` present in `walker.py` (`_PREFETCH_CHILD_POLICY` import + seal
  call). Nothing else on this family's core paths since `ITEM_BASELINE`
  (item diff names only `docs/bug_hunt/bug_hunt-0_0_15.md`).
- `querysets.py` read-only confirmed: `git diff HEAD --name-only` names no
  `utils/querysets.py`; no consolidation below edits it.

Prior records used as triggers only: the `utils/querysets.py` file item's two
traces are both stale at `bfaee91d` — F3/C12 (defect-code count), F4/C14
(pre-sliced count), D5, D-W2-a, D-W2-b checked as triggers, never verdicts;
START.md standing rule honored (no blacklist shape anywhere in this family).

## Verification

### Matrix

1. Cross-flavor mirroring: sync/async `apply_type_visibility` twins share
   both seals by construction (docstring pins the drift rule); cascade,
   walker-child, list-argument, orderset-result, raw-list surfaces differ by
   declared policy only. No second seal body found package-wide.
2. Sync/async twins: `post_process_*`, list pipelines, connection pipelines,
   `bounded_rows*` compared by behavior — same seals, color differs only in
   await handling. No drift.
3. Derived knowledge: `_captured_model` reads the definition once per call
   and threads it through both seals; alias resolution order
   (pipeline > explicit > none) lives in `_prepared_visibility_source` alone.
4. Round-trip pairs: prove side (`_seal_or_defect` + genuineness walks) and
   rebuild side (`_reconstructed_value`) share `_PLAIN_CONTAINER_TYPES`;
   `tests/utils/test_querysets.py` pins the rebuild side to every member.
5. Other media: production (owner module), oracles
   (`tests/utils/test_querysets.py` seal matrix, live visibility / multi-db
   suites), projections (module + seal + policy docstrings,
   [spec-045][spec-045]). Listed, not counted.
6. Enforcement by omission: every framework-owned `get_queryset` invocation
   routes through the two runners — `type_cls.get_queryset(` has exactly two
   package call sites, both in [querysets.py][querysets] (sync + async
   runners). `filters/base.py` super-call is consumer-side DRF surface, out
   of population. No unsealed hook invocation exists.

### Enumeration

Instruments: `grep` populations over `django_strawberry_framework`
(`get_queryset(` invocations: 2; `_seal_or_defect(` call sites: source,
result, orderset, raw-list, recursive-prefetch = 5 shapes, one body;
`_SealPolicy(` constructions: 6, one declaration site;
`apply_type_visibility_*` call sites: all consumer files above, zero
duplicated seal bodies) + full read of the owner and every consumer call
site. Every member lands in F-seal (single-owned), R-wording, R-guard, or
the consumer list above; `_UNRECOMPOSED_CHILD_POLICY` has zero source hits
(retired, see below).

### Challenges

- C1 — add a seal defect code: `_seal_or_defect` (1 definition) + one arm at
  each message site that can reach it (consumers, listed not counted).
  Count: 1.
- C2 — add a seal-policy axis (new surface needing e.g. unevaluated results
  or a sliced licence): `_SealPolicy` field + its check in the seal
  (1 definition). Count: 1. Connection's pre-slice guard evaluated as a
  candidate second definition — rejected (R-guard).
- C3 — new queryset method that evaluates (hostile `.first()` override,
  shadowed `__aiter__`, replaced `Query.chain`): 0 definitions move —
  neutralized without rejection; the seal never dispatches the consumer
  object. Probe rows 1–2 prove it. Count: 0.
- C4 — new consumer of rows: composes `apply_type_visibility_*` /
  `normalized_row_source` by name (1 call site, no definition moves).
  Inside the boundary iff it consumes the sealed return; reading the raw
  consumer object past the seal is a bypass hole. Count: 1 (new call site).
- Probe (execution-verified, WS copy): `PYTHONPATH=<WS>/examples/fakeshop
  uv run --directory <WS> python probe_seal.py` — hostile subclass seals to
  a fresh exact-`QuerySet` with predicate kept and 0 SQL; sliced /
  wrong-table / projection defects; both raise paths. Recorded
  `__file__` inside `<WS>` and DB `NAME` inside `<WS>` (see Finding F-seal).

## Findings

### F-seal — CONFIRMED single-owned, no edit (zero-edit consolidation)

Contract + variation: the sealed-execution queryset; varies on model rows,
slice/combinator tolerance, alias pinning, evaluated tolerance, result-cache
carriage — all declared as `_SealPolicy` fields.
Sites + roles: definition `_seal_or_defect` (+ `_SealPolicy` declarations);
consumers enumerated above; oracles (seal matrix + live suites); projections
(docstrings, [spec-045][spec-045]).
Challenges: C1=1, C2=1, C3=0, C4=1(call site).
Owner + lifetime (principle 7/4): owner stays `_seal_or_defect` — the
narrowest cohesive owner every consumer already imports without reversing a
dependency. Lifetime: per-call / per-queryset; nothing cached (pure
derivation, fresh object per seal); publish point = return to the sealing
surface; who may mutate = downstream framework transforms on the sealed
object only; no unseal exists and none is owed.
Migration: none — already single; D1 fix already moved the last divergent
caller (walker) onto the shared policy.
Distinct behavior kept: exact-`QuerySet` fast path + counted path in
`normalized_row_source` (perf, same owner); cascade `require_model_rows`
off; child/orderset/raw-list axes; `_result_cache` carriage by reference
(documented cost choice).
Behavioral proof: execution-verified — WS probe, all assertions passed
(package `<WS>/django_strawberry_framework/__init__.py`, DB
`<WS>/examples/fakeshop/db.sqlite3`, seal executed 0 SQL; hostile `.all()` /
`.filter()` / shadowed `.first()` never dispatched; `('sliced',
'rows 0:3')`, `table`, `projection` defects; both `ConfigurationError`
wordings). Rejects: a consumer override erasing the predicate post-seal;
a violation returning anything but a typed raise. Existing oracles cited
(`tests/utils/test_querysets.py`, live visibility + multi-db suites) without
re-running; the one authorized shared-tree test is unspent.
Structural gate: DEFERRED with reason — bypass means not calling the seal,
whose population (future surfaces) cannot be enumerated today; a
name-existence pin on today's call sites would pass a hand copy (copy is
correct) and rot on the next legitimate surface. Gate design belongs with
the `seal-defect-code-wording` family's message-site population work, which
owns the only enumerable bypass-adjacent set. No `proof:`/`gate:` command
owed by this finding beyond the executed probe, listed under Pending.
Freshness: [querysets.py][querysets] `96618fba`, [permissions.py][permissions]
`757dce34`, [walker.py][walker] `9b111ed9`, [resolvers.py][type-resolvers]
`f3341e6a`, [resource-policy.py][resource-policy] `647133d2`,
[list-field.py][list-field] worktree `d6af6164` (HEAD `ce682d5f`; ledgered
docstring dirt), [connection.py][connection] worktree `3c4d5dcb` (HEAD
`93e998f2`; external cursor-guard dirt), [relay.py][types-relay] worktree
`c333c785` (HEAD `52439862`; ledgered docstring dirt),
[filter-sets.py][filter-sets] worktree `4a40e51b` (HEAD `4ab65a26`;
concurrent hunk, untouched), [mutation-resolvers.py][mutation-resolvers]
worktree `a322d17a` (HEAD `3fd1e571`; concurrent dirt, untouched),
[resource-policy-ext.py][resource-policy-ext] worktree `583bf460` (HEAD
`52084078`; external dirt; excluded), [GOAL.md][goal] `7dfbef5c`,
[spec-045][spec-045] `97561f2d`. HEAD `bfaee91d`,
ITEM_BASELINE `9b79d85102190980afc375ff15b315c2a684d339`.

### R-wording — REJECTED consolidation of per-site refusal prose

Difference: each site names its own subject and contract — source wording
(`_prepared_visibility_source`), hook-result wording
(`_visibility_result_error`), single-sentence shape wording
(`_validate_post_orderset_result`), raw-list ceiling wording
(`_raw_list_source_message`), cascade path renderers, connection
`GraphQLError` client wording. Shared = dispatch + exhaustiveness
(`_defect_message`), never the sentences. Merging them would attribute a
rejection to the wrong call.
Trigger: two sites rendering the same (code, subject) pair, or a new site
quoting another site's subject.
Home: already at the owner — `_defect_message` docstring ("Each site owns
its own prose ... what is shared is the dispatch and the exhaustiveness").
No edit owed. C1 count stands at 1 definition.

### R-guard — REJECTED consolidation of the connection pre-slice guard

Difference: `_guard_source_not_pre_sliced` reads the CONSUMER object through
normal attribute access (`source.query.is_sliced`) BEFORE the boundary and
raises client-facing `GraphQLError` on every request regardless of sidecar
input; the seal's `sliced` defect proves dispatch-free state INSIDE the
boundary and raises author-facing `ConfigurationError`. Different stage,
different error contract, different read discipline — the F4/C14 trigger's
"two definitions" reading is not sustained.
Trigger: the guard migrates to `__dict__` reads + typed errors, or the seal
gains a pre-visibility client-facing arm.
Home: clause owed at `connection.py::_guard_source_not_pre_sliced`
docstring — recorded here, owner edit deferred (file externally dirty;
[querysets.py][querysets] read-only under another item's dispute). Not
edited silently.

### Old D5 / D-W2-a — GONE, verified from the tree, not re-filed

- D5 (dead defect-code arms): `_raw_list_source_message` now carries exactly
  `type`/`table`/`untrusted`; `_prepared_visibility_source`
  `type`/`table`/`untrusted`/`sliced`/`combined`/`projection`;
  `_visibility_result_error` adds only the reachable `alias`; the false
  docstring now enumerates `evaluated`, `sliced`, `combined`, `projection`
  as switched off. Landed by `5741eaa6`. Gone.
- D-W2-a (`_UNRECOMPOSED_CHILD_POLICY` residue): zero source hits
  (one stale `__pycache__` bytes match only); both visibility runners and
  the walker name `_PREFETCH_CHILD_POLICY`. Landed by `4d9f1c3d`. Gone.
- D-W2-b (slice-licence premise scope) untouched by the ff; lives in the
  contested file-item artifact — observed, not duplicated here.

## Defects

None new. Tracing found no non-duplication bug: the pre-boundary attribute
read in R-guard is deliberate triage with a fail-closed unreadable arm, and
the by-reference cache carriage is a documented cost choice at its site.

## Pending execution

- `proof:` `PYTHONPATH=<WS>/examples/fakeshop uv run --directory <WS>
  python probe_seal.py` (`<WS>=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/sealed-execution-queryset`)
  — execution-verified (all assertions passed; copy `__file__` + DB `NAME`
  recorded in F-seal). WS left on disk for Worker 2; remove by explicit path
  after verification.
- Shared-tree authorization unspent: no edit landed, no new oracle added, so
  no focused `--no-cov` run was spent and no `gate:` command is owed.

## Judgment

The seal is one function plus one policy record; every surface composes it
by name and every refusal wording differs by contract. Consolidation is
already complete (walker D1 included); both candidate merges are rejected
with difference, trigger, and home. Zero production edits;
`utils/querysets.py` untouched. Old D5/D-W2-a confirmed gone, not re-filed.
Gate deferred with reason; probe execution-verified in the disposable copy.

Item-scoped diff state: no tracked edits; one new untracked artifact (this
file). `git diff 9b79d851 -- django_strawberry_framework` empty;
`utils/querysets.py` clean vs HEAD and vs ITEM_BASELINE. Scratch:
`<WS>/probe_seal.py` (WS-only, never in the shared tree).

## Independent verification (Worker 2)

Recorded BEFORE opening `## Findings` (header `Status:`/`Run:` + section
list + tail `## Defects`/`## Pending execution`/`## Judgment` seen only to
place this section; no finding body read). All site/role/count/owner claims
below are re-derived from the tree at HEAD `bfaee91d`.

### What "sealed" means operationally (Worker 2 re-derivation)

- Candidate query STATE is read exclusively from the instance `__dict__`
  via `object.__getattribute__`
  (`django_strawberry_framework/utils/querysets.py::_seal_or_defect` + helpers);
  no attribute access, so custom `__getattribute__`, instance-shadowed
  callables, redefined `query`/`_query` descriptors cannot run code or lie.
- Extracted state is validated (concrete-table match incl. proxy siblings,
  exact `django.db.models.sql.Query` type, exact-builtin containers,
  identity-proved genuine Django AST nodes over compiler-reachable slots,
  Django row-iterable membership, exact-shape deferred-filter state,
  recursive `Prefetch`-child seal, routing/alias/evaluated/sliced/combined/
  projection checks per policy), then rebuilt as a FRESH framework-owned
  plain `models.QuerySet`. The seal NEVER returns the consumer object.
- Zero SQL at seal time (lazy state composition only); per-call/per-queryset
  lifetime, nothing cached (`result is queryset` is ALWAYS re-sealed; a hook
  may mutate and return the same object). `_result_cache` is dropped by every
  policy EXCEPT `_RAW_LIST_SOURCE_POLICY`, which carries an exact-`list`
  forward (subclass `__getitem__`/non-list cache fail closed).
- No unseal exists anywhere in the package (grep `unseal|Unseal|UNSEAL`:
  only prose adjectives `unsealable`/`unsealed` at `resource_policy.py`,
  `utils/querysets.py`, `permissions.py`; no function, no reverse path).
  Downstream framework transforms compose onto the sealed object; the
  consumer original never re-enters.

### Every seal site + consumer (Worker 2 sweep)

Definition (counted as ONE per the change challenge: a new defect code takes
one fixed position in the canonical ordering + one arm per reachable message
site; a new policy axis is one field + its check — never a threaded keyword):

- `django_strawberry_framework/utils/querysets.py::_seal_or_defect` — the
  single sealing primitive. `::_SealPolicy` + 6 frozen policy constants are
  variation DECLARATIONS (principle 1), not definitions:
  `_DEFAULT_SEAL_POLICY`, `_CASCADE_SEAL_POLICY`
  (`require_model_rows=False, reject_combined=True`),
  `_PREFETCH_CHILD_POLICY`
  (`reject_sliced=False, require_shared_alias=True`),
  `_LIST_ARGUMENT_VISIBILITY_POLICY` (`reject_combined=True`),
  `_ORDERSET_RESULT_POLICY`
  (`reject_combined=True, require_unevaluated=True`),
  `_RAW_LIST_SOURCE_POLICY`
  (`require_model_rows=False, reject_sliced=False, carry_result_cache=True`).
- In-owner composing consumers (same module, all by name):
  `_prepared_visibility_source` (source seal), `_normalized_visibility_result`
  (hook-result seal), `apply_type_visibility_sync/async` (both seals, both
  colors), `_validate_post_orderset_result` (post-`OrderSet` seal under
  `_ORDERSET_RESULT_POLICY` + `_snapshot_routing_intent` baseline),
  `normalized_row_source` (raw-list subclass rebuild under
  `_RAW_LIST_SOURCE_POLICY`), `materialized_rows`/`_readable_queryset_state`
  (exact-type row reads), `prepared_resolver_source`
  (async-refusal-first head shared by list/connection),
  `post_process_queryset_result_sync/async`, `_sealed_prefetch_related_lookups`
  (recursive child seal), `_defect_message` (exhaustive dispatch shared by all
  message sites).

External consumers (each composes by name; none restates the predicate):

- `django_strawberry_framework/permissions.py` — root source prep + per-edge
  hook-result seals, both under `_CASCADE_SEAL_POLICY`, with bespoke
  path-rich renderers (root + cascade). Sync walk + async twin off it.
- `django_strawberry_framework/list_field.py` — no-argument seals (default
  policy, both colors) + `_LIST_ARGUMENT_VISIBILITY_POLICY` seals (both
  colors) + `_snapshot_routing_intent`/`_validate_post_orderset_result`
  around consumer `OrderSet.apply_sync/apply_async` (both colors).
- `django_strawberry_framework/optimizer/walker.py::_build_child_queryset` —
  planned `Prefetch`-child seal under `_PREFETCH_CHILD_POLICY` (D1 fix
  present: imports `_PREFETCH_CHILD_POLICY`, seals with captured
  `target_model`; docstring records `reject_sliced=False` degrade-to-unplanned
  + `require_shared_alias=True` single-connection rationale).
- `django_strawberry_framework/connection.py` — color-agnostic
  `_prepare_pipeline_source` head off `prepared_resolver_source` (both
  pipelines: sync `reject_awaitable_sync_source`, async
  `reject_residual_async_source`) + per-branch guards
  (`non_queryset_guard`, `queryset_guard=_guard_source_not_pre_sliced`) +
  colored `apply_type_visibility_sync/async` seals downstream.
- `django_strawberry_framework/types/resolvers.py` — recheck
  (`apply_type_visibility_sync/async`) + prefetch-cache short-circuit +
  `bounded_rows`/`bounded_rows_async` row bounding (relation + root paths).
- `django_strawberry_framework/resource_policy.py` — `bounded_rows` /
  `bounded_rows_async` / `_windowed_rows` / `normalized_row_source` (row-source
  seal-then-slice seam; the only thing between a raw list and the whole table).
- Sweep-found, same rule, same owner (index extension owed — plan index row
  names only the seven files above):
  `django_strawberry_framework/types/relay.py` (node `get_object`/`get_objects`
  seals via `apply_type_visibility_*` over `initial_queryset`),
  `django_strawberry_framework/filters/sets.py`
  (`_derive_related_visibility_querysets_sync/async` via
  `apply_type_visibility_*`), `django_strawberry_framework/mutations/resolvers.py`
  (visibility-scoped row locate via `apply_type_visibility_sync` over
  `initial_queryset`; relation decode via the shared related-visibility
  compose).
- Excluded: `django_strawberry_framework/extensions/resource_policy.py` —
  no `seal_or_defect`/`SealPolicy`/`prepared_resolver`/`bounded_rows` import
  or call (grep empty); its "policy" is `ResourcePolicy` (row ceilings,
  `charge_document` budget arms — concurrent +169 dirt, read freely, never
  edited). Different word, different contract, correctly out of family.

### Violations handling (Worker 2)

- `_seal_or_defect` returns `(None, (code, detail))`; NO surface returns a
  defect object to a caller. Every surface raises `ConfigurationError`:
  source seals via `_prepared_visibility_source`, hook results via
  `_normalized_visibility_result`/`_visibility_result_error`, post-OrderSet
  via `_validate_post_orderset_result` shape-map + `routing` arm,
  raw-list via `normalized_row_source`/`_raw_list_source_message`.
- Codes canonical order `type` -> `table` -> `untrusted` -> `routing` ->
  `evaluated` -> `sliced` -> `combined` -> `projection` -> `alias`; each
  message site renders only the subset it can reach; `_defect_message`
  fails loud (`framework defect: ... added without an arm`) on unrendered
  codes. Message ladders checked exact (no `_UNRECOMPOSED_CHILD_POLICY`;
  see old-defects below).

### Definition counts (Worker 2 change challenges)

- C1 new defect code (e.g. a new `readonly` shape): 1 (`_seal_or_defect`
  ordering + per-site arms are consumers of the code, not definitions).
- C2 new axis (e.g. connection pre-slice guard as candidate second
  definition): evaluated below — provisional 1, pending seam analysis.
- C3 new evaluating method (e.g. another `QuerySet` method override):
  0 — neutralized by construction (state-walk replaces method inventory;
  probe-proved per record). No new definition.
- C4 new consumer (e.g. a new surface sealing a queryset): 1 call site
  inside-iff-sealed-return (compose by name, declare policy only if a
  genuinely new axis varies).

### Owner Worker 2 would choose

`django_strawberry_framework/utils/querysets.py::_seal_or_defect` (+
`_SealPolicy` declarations at the same home). Narrowest cohesive owner every
legitimate consumer can import without reversing a dependency (owner depends
only on `django`/`asgiref`/`strawberry`-probe/`exceptions`/write-txn helpers;
never back into filters/orders/mutations/permissions) — dependency direction
wins per principle 7. Lifetime per-call/per-queryset; nothing cached.

### Freshness re-hashed (Worker 2, worktree vs HEAD)

- `utils/querysets.py` `96618fba…` == HEAD (clean, READ-ONLY honored — never
  edited). `permissions.py` `757dce34…` clean. `optimizer/walker.py`
  `9b111ed9…` clean. `types/resolvers.py` `f3341e6a…` clean.
  `resource_policy.py` `647133d2…` clean.
- Dirty (concurrent, content-attributed, left alone):
  `list_field.py` worktree `d6af6164…` vs HEAD `ce682d5f…`;
  `connection.py` `3c4d5dcb…` vs `93e998f2…` (cursor-guard feature, seal sites
  untouched per §C2 read); `types/relay.py` `c333c785…` vs `52439862…`;
  `filters/sets.py` `4a40e51b…` vs `4ab65a26…`; `mutations/resolvers.py`
  `a322d17a…` vs `3fd1e571…`; `extensions/resource_policy.py` `583bf460…`
  vs `52084078…`. None touched by this zero-edit item; seal-site hunks
  verified by content grep (seal call sites identical in worktree and HEAD
  for the lines cited).
- Item-scoped diff: `git diff 9b79d851 -- django_strawberry_framework`
  EMPTY on family paths (only `docs/bug_hunt/bug_hunt-0_0_15.md` moved since
  ITEM baseline — other cycle's artifact, concurrent); `git diff 334a2bb25`
  empty (current stash == worktree). Zero tracked edits by this item; one new
  untracked artifact (this file). AGENTS.md prose: dirty-at-start/concurrent
  paths are out-of-scope unless the item touches them — this item touches
  none, so the six dirty family files stay unread-for-edit, read-only for
  trace. `querysets.py` fenced READ-ONLY (collision note) honored.

### Old defects (Worker 2, independently)

- `grep -rn _UNRECOMPOSED_CHILD_POLICY django_strawberry_framework/`:
  ZERO hits (Worker 2). Old D-W2-a gone from the tree.
- D5 wording (seal wording no policy can reach, dropped in `5741eaa6`):
  no orphan arm remains; every message ladder renders exactly its reachable
  subset with a loud default for unrendered codes. Closeout owes the landing
  note; not re-filed here.

### Adjudications to reconcile after opening Findings

- C2 (connection `_guard_source_not_pre_sliced` as candidate second
  definition): open — seam analysis owed (pre-slice triage vs seal proof).
- R-guard deferral (owner-home clause in-artifact, edit deferred for
  dirt + read-only): deferral judged CORRECT provisionally; landing date
  owed (clause lands when `querysets.py` fence lifts AND `connection.py`
  dirt settles, not before).
- `proof:` pending: WS probe reported execution-verified (not re-runnable by
  the gate) — provisional: record-of-executed-proof, NOT a gate-runnable
  `proof:`; item `verified` (not `verified, pending execution`) if no other
  `proof:` remains. Decided finally below after reading `## Findings` +
  `## Pending execution`.
- No-gate (bypass population = future surfaces): hand-copy standard
  provisionally applied — a hand copy of the owner body passes every behavior
  oracle, so no bespoke existence test is owed; deferral legitimate, not an
  unowed gate. Confirmed/falsified below.

### Reconciliation + verdict (Worker 2, after opening `## Findings`)

Agreement/difference per reconciliation point (all re-derived above, then
compared):

1. 1 definition (`_seal_or_defect` + 6 policy constants as variation
   declarations) — AGREE. Verified: 5 call-shape sites / 1 body
   (recursive-prefetch, orderset, raw-list, source, result), 6
   `_SealPolicy(` constructions / 1 declaration site, zero seal bodies
   elsewhere package-wide.
2. Consumers compose by name (permissions root+cascade, list_field both
   colors + OrderSet snapshot/validate, walker `_build_child_queryset` with
   D1 fix present in tree, connection both pipelines off the
   `prepared_resolver_source` head, types/resolvers
   recheck+prefetch+`bounded_rows`, root resource_policy rows, +
   types/relay + filters/sets + mutations/resolvers) — AGREE on every site;
   omission-difference only: the plan responsibility-index row names just the
   first seven files, so an INDEX EXTENSION is owed for the three sweep-found
   files (exact rows below).
3. `extensions/resource_policy.py` excluded (different "policy" word) —
   AGREE (zero seal imports/calls verified; `ResourcePolicy` row ceilings +
   concurrent `charge_document` dirt are another contract).
4. No unseal — AGREE (only prose adjectives in tree, no reverse path).
5. Violations raise `ConfigurationError` — AGREE (all five message paths
   verified; no defect object ever returned to a caller).
6. C1=1, C2=1 (candidate rejected), C3=0 (neutralized, probe-proved), C4=1
   call site inside-iff-sealed-return — AGREE on all four counts.
7. Owner confirmed (narrowest, all import) — AGREE: chosen independently
   before opening Findings; dependency direction wins per principle 7.
8. Lifetime per-call/per-queryset, nothing cached, `result is queryset`
   re-sealed — AGREE (verified at both runners' no-fast-path comments).
9. Already-single, no merge — AGREE (walker D1 fix `fd39cac6` in history,
   code + docstring present in tree).
10. R-wording rejected (per-site prose, home at `_defect_message` docstring)
    — AGREE (home clause verified present in tree; six subjects confirmed
    distinct; trigger well-formed; no edit owed).
11. R-guard rejected (triage vs proof; owner-home clause in-artifact, edit
    deferred) — AGREE on the rejection; deferral judged CORRECT, see below.
12. Old D5/D-W2-a GONE — AGREE and independently confirmed: zero
    `_UNRECOMPOSED_CHILD_POLICY` source hits (Worker 2 grep); all four
    message ladders carry exactly their reachable keys with a loud default;
    landings in history (`5741eaa6` drops the unreachable wording,
    `4d9f1c3d` retires the residue policy). Closeout owes the landing note;
    not re-filed.
13. D-W2-b left in the contested file-item artifact — AGREE (observed here,
    not duplicated; that artifact untouched).
14. No new defects — AGREE (pre-boundary dispatch read is deliberate triage
    with a fail-closed unreadable arm; by-reference cache carriage is a
    documented cost choice at its site). No `(Worker 2)` entries under
    `## Defects`.

### C2 judgment (challenged candidate, opened as ordered)

`connection.py::_guard_source_not_pre_sliced` vs the seal's `sliced`
defect: ADJACENT WITH OVERLAP, not the same rule. Overlap is exactly one
input shape (a sliced queryset arriving as the connection resolver return).
Difference is fourfold, all read from the tree: (a) stage — guard is
pre-boundary triage on the consumer object (runs inside
`_prepare_pipeline_source` BEFORE `apply_type_visibility_*`), seal is
inside-boundary proof on extracted state; (b) read discipline — guard
dispatches (`source.query.is_sliced`, fail-closed unreadable arm), seal
never dispatches; (c) error contract — guard raises client-facing
`GraphQLError` on EVERY request regardless of sidecar input (the connection
always reorders via `_finalize_queryset` then slices, both illegal on a
sliced query), seal raises author-facing `ConfigurationError` under
`policy.reject_sliced`; (d) coverage — guard covers only the resolver-return
source, seal covers source AND hook result AND orderset/raw-list/prefetch
shapes under policy. Change-coupling: softening sliced-rejection for one
connection shape moves the guard alone; adding a seal code moves the seal
alone — count stays 1 definition. Rejection SUSTAINED. The seam (triage
before, proof inside; triage may dispatch because it fail-closes unreadable,
proof may not) is recorded in-artifact at R-guard; its durable home is the
guard's docstring (edit deferred — see R-guard judgment). Reconsideration
trigger as stated (guard goes `__dict__` + typed, or seal gains a
pre-visibility client arm) is well-formed.

### R-guard deferral judgment

Deferral CORRECT, with one narrowed reason. The `querysets.py` read-only
fence does NOT block this clause (wrong file — the home is
`connection.py::_guard_source_not_pre_sliced`); the blocker is the
`connection.py` external dirt alone (worktree `3c4d5dcb…` vs HEAD
`93e998f2…` cursor-guard feature): editing now would violate the
concurrent-work attribution rule. The clause is projection (prose),
behavior-neutral, preserved verbatim in-artifact — nothing enforceable is
lost. It does NOT belong in the artifact only: the artifact copy is the
pending record, the guard docstring is the durable home. LANDING: the first
change that legitimately edits the guard after the external dirt settles
(lands or reverts); if none arrives before closeout, as a prose-only delta
at closeout (Worker 0 schedules; no new card needed — R-guard Home is the
record). Blocks nothing.

### `proof:`-pending adjudication

`verified`, NOT `verified, pending execution`. The sole `proof:`-prefixed
line records an ALREADY-EXECUTED probe (assertions passed; copy `__file__`
+ DB `NAME` recorded inside `<WS>` in F-seal, proving the disposable copy —
not the shared tree — was exercised; hostile subclass → fresh exact
`QuerySet`, predicate kept, 0 SQL, sliced/table/projection defects, both
`ConfigurationError` wordings). By kind it is `execution-verified` evidence,
not `execution-deferred` work: the command embeds the `<WS>` placeholder and
the WS is removed by explicit path after verification, so the final gate
cannot run it "as listed". No gate-runnable `proof:` remains; no `gate:`
owed (zero edits, no new oracle). Worker 0: tick WITHOUT the pending
marker; do NOT run the line at the gate; W1's text left intact, this
adjudication is the authority (re-type the prefix at closeout if desired).

### Gate judgment

No structural gate owed NOW — legitimate deferral, not an unowed gate.
Bypass = not calling the seal; its population (future surfaces) is
unenumerable today, and the hand-copy standard is correctly applied: a
behavior-preserving hand copy passes every behavior oracle (the copy is
correct), so no behavior gate can catch bypass, while a name/existence pin
would pass the copy AND rot on the next legitimate surface — exactly the
bespoke existence test DRY.md forbids. Parking gate design with the
`seal-defect-code-wording` family's enumerable message-site population is
sound coupling.

### Freshness re-hash (Worker 2; all match the artifact)

`utils/querysets.py` `96618fba…` == HEAD (read-only honored);
`permissions.py` `757dce34…`; `optimizer/walker.py` `9b111ed9…`;
`types/resolvers.py` `f3341e6a…`; `resource_policy.py` `647133d2…`;
`list_field.py` worktree `d6af6164…`/HEAD `ce682d5f…`;
`connection.py` worktree `3c4d5dcb…`/HEAD `93e998f2…`;
`types/relay.py` worktree `c333c785…`/HEAD `52439862…`;
`filters/sets.py` worktree `4a40e51b…`/HEAD `4ab65a26…`;
`mutations/resolvers.py` worktree `a322d17a…`/HEAD `3fd1e571…`;
`extensions/resource_policy.py` worktree `583bf460…`/HEAD `52084078…`
(excluded). HEAD `bfaee91d`; ITEM_BASELINE
`9b79d85102190980afc375ff15b315c2a684d339`. Item-scoped diff EMPTY on
family paths (`git diff 9b79d851 -- django_strawberry_framework` names only
the other cycle's `docs/bug_hunt/bug_hunt-0_0_15.md`; `git diff 334a2bb25`
empty). AGENTS.md prose on empty diff: the six dirty family files are
concurrent work, content-attributed and untouched — out of scope, correctly
left alone. Artifact citations use `path::Symbol` (no line numbers); no
process provenance; oracles cited at the mandated tiers
(`tests/utils/test_querysets.py` + live visibility/multi-db suites); ruff
on touched paths trivially passes (no `.py` touched; `ruff check`/`format
--check` clean). No pytest run (none authorized, none owed for zero edits).

### Exact plan rows owed (Worker 0 applies)

- Tick: `- [ ] Family \`sealed-execution-queryset\` —
  [dry-rule-sealed-execution-queryset.md](dry-rule-sealed-execution-queryset.md)`
  → `- [x] Family \`sealed-execution-queryset\` —
  [dry-rule-sealed-execution-queryset.md](dry-rule-sealed-execution-queryset.md)
  — verified (Run 0.0.15 2026-09-19-1; CONFIRMED single-owned, already-single,
  no gate; zero edits; no pending execution)`.
- Index extension + status: `| \`sealed-execution-queryset\` |
  \`utils/querysets.py::_seal_or_defect\` | \`utils/querysets.py\`,
  \`permissions.py\`, \`list_field.py\`, \`optimizer/walker.py\`,
  \`connection.py\`, \`types/resolvers.py\`, \`resource_policy.py\` | Family
  \`sealed-execution-queryset\` | open |` → Files covered adds
  \`types/relay.py\`, \`filters/sets.py\`, \`mutations/resolvers.py\`;
  Status `open` → `consolidated` (already-single; walker D1 consolidation
  ledgered under File `utils/querysets.py`).
- Landing note (closeout `## Outcomes`): old D5 landed `5741eaa6`, old
  D-W2-a landed `4d9f1c3d` (both in HEAD range, verified gone); R-guard
  owner-home clause deferred to the guard docstring per above; D-W2-b stays
  homed in the contested file-item artifact.
- Scratch paths (remove by explicit path after tick):
  `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/sealed-execution-queryset`
  (WS-only `probe_seal.py`; never in the shared tree; no
  `docs/dry/temp-tests/` dir from this item).

Verdict: `Status: verified`. No `(Worker 2)` defects. Concurrent dirt and
the contested `dry-file-utils__querysets.md` sections preserved; nothing
committed.

## Run-8 scoped re-trace (Worker 1, REOPENED item s17)

Run: 0.0.15 2026-09-30-8. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh: it scopes the
drift delta across all seven member files plus the three sweep-found
consumers and the excluded file, CONFIRMs or REVISEs every prior family
finding (F-seal, R-wording, R-guard, old D5/D-W2-a), re-derives the seal
rule with the member/consumer census at HEAD, and tests the carried run-8
evidence from the family side (s16 rewrite helpers + F3 population, s11
seal-side exclusion, s12 walker consumer shape). Zero production edits;
zero tracked files changed except this artifact.

Method: probes `/tmp/s17/*.py` + `/tmp/s17/*.sh` (`sealhunks.py`
diff-hunk classifier, `census*.sh` / `dump*.sh` greps + `git show` reads,
`dirt*.py` worktree attribution), cited by content. All execution via
`workspace.py run dry/sealed-exec-retrace-s17/consolidate` (copy slot-2,
synced 2026-09-30T20:19:14Z, fresh at every run; the copy carries no
`.git`, so all git reads are `git -C <shared>` through the same runner).
The target is never imported: pure `git show` bytes plus `git grep` with
directory pathspecs. No pytest; read-only probes only.

### Scope and fingerprints

Drift base `0c0537e2`, HEAD `83998e08` (unmoved at close).
`ITEM_BASELINE=4fa16e78b8bddd4ba766617141d1c5de22cc1c0c` (resolves;
before-copy pinned slot-1).

| File | Base | HEAD | Worktree |
|---|---|---|---|
| `utils/querysets.py` | `3616927d` | `392e50d0` | `cfc773ba` |
| `permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` |
| `list_field.py` | `21380eb7` | `77ddb86c` | `1dcb0c43` |
| `optimizer/walker.py` | `75f9c6b6` | `bdd9c2f1` | `9130aceb` |
| `connection.py` | `4894f90f` | `3d6dd424` | `64b85d0e` |
| `types/resolvers.py` | `72d62dc4` | `574e9768` | `7a953c53` |
| `resource_policy.py` | `4b69e974` | `47befb3f` | `927b89a2` |
| `types/relay.py` | `52439862` | `968fb95a` | `6c2e8c20` |
| `filters/sets.py` | `993e887a` | `3d307402` | `ec278851` |
| `mutations/resolvers.py` | `043a2d0b` | `7a25afea` | `dd00ec6e` |
| `extensions/resource_policy.py` | `19e2309d` | `5cc373ec` | `8944e79e` |

Base blobs match the run-7 stamps; all 11 HEAD blobs re-hashed identical
at write time. Committed delta `0c0537e2..HEAD` on these files is exactly
15 commits: 7 behavior-bearing + 7 typing-only + 1 pragma-only.

- Seal rewrite (read end to end): `5c5e32c5` — combined
  `get_queryset` served as its pk set. Owner: `reject_combined` ->
  `rewrite_combined` (default on), `_LIST_ARGUMENT_VISIBILITY_POLICY`
  deleted, cascade/sidecar/raw-list constructions recomposed, new
  `_is_model_column` / `_combined_lost_property` /
  `_pk_membership_query_or_defect` / `_COMBINED_WHAT`, combined arm moved
  after projection, three message sites recomposed. Members: connection
  `_sidecar_visibility_policy` deleted (single default policy both
  pipelines), list field `policy=` kwargs deleted (single default policy
  both colors), walker `_hint_prefetch_over_pk_set` new (composes the
  rewrite + `_COMBINED_WHAT` by name), permissions cascade renderers
  compose `_COMBINED_WHAT` + `reject` -> `rewrite` prose.
- Relay re-seal: `2935e0e4` — `_resolve_nodes_default/_async`
  `node_ids=None` path returns a fresh `apply_type_visibility_*` seal
  instead of the already-sealed `qs` (+2 composing call sites, same rows).
- Seal-neutral behavior (each full diff read + zero seal-content lines):
  `10d2b9cd` (order-ladder tier via `default_order`/`applied_order`;
  s11's row), `dbf0a870` + `193f9946` (connection pagination),
  `b63df99d` (relay id-filter split downstream of the seals),
  `bbe54687` (filters relation-identity classes).
- Typing-only on family paths (every seal-function hunk classified by
  content): `999a1aab` (15 hunks: casts, annotations, `type: ignore`
  comments, one annotation narrowing, one local rename with cast-back),
  `b20277fe` (60 hunks: annotations, casts, `@overload` stubs, one local
  rename with consistent follow-through), `fef11e64` (3 hunks:
  annotations + reformat), `dd3a10b1` / `5f440a93` / `849f67bc` /
  `dfbea72b` (zero seal-function hunks), `e37448e5` (pragma comment).
- `## Owned changes` names no pending family-file edit (only the walker
  D1-fix row, landed `fd39cac6`): all worktree dirt below is concurrent,
  zero owned.

### Drift delta — per-file freshness (11 STALE, 0 MATCH)

Every input drifted; each re-derived at HEAD bytes. HEAD blob + causes +
judgment:

- `utils/querysets.py` `392e50d0` (`5c5e32c5 999a1aab b20277fe
  10d2b9cd dfbea72b fef11e64`): the seal rewrite + order tier + typing.
  Every finding re-derived below.
- `permissions.py` `d77c5050` (`5c5e32c5` + 3 typing): cascade renderers
  compose `_COMBINED_WHAT`; `reject` -> `rewrite` prose; typing
  annotation-only. Seal shapes intact.
- `list_field.py` `77ddb86c` (`5c5e32c5 10d2b9cd` + 6 typing): single
  default policy; order read via `default_order`. Seal shapes intact.
- `optimizer/walker.py` `bdd9c2f1` (`5c5e32c5` + 3 typing): new
  `_hint_prefetch_over_pk_set` consumer; D1 child seals intact.
- `connection.py` `3d6dd424` (`5c5e32c5 10d2b9cd dbf0a870 193f9946` + 6
  typing): sidecar policy deleted; guard intact (annotation only).
- `types/resolvers.py` `574e9768` (3 typing): annotation-only; all seal
  sites identical modulo annotations.
- `resource_policy.py` `47befb3f` (4 typing): annotation-only; seam
  identical modulo annotations.
- `types/relay.py` `968fb95a` (`2935e0e4 b63df99d` + 4 typing): 4 -> 6
  seal sites; rest seal-neutral.
- `filters/sets.py` `3d307402` (`bbe54687 e37448e5` + 5 typing):
  seal-neutral; child seals intact.
- `mutations/resolvers.py` `7a25afea` (3 typing): annotation-only;
  locate seal intact.
- `extensions/resource_policy.py` `5cc373ec` (4 typing): still zero seal
  imports/calls (HEAD and worktree); exclusion stands.

### F-seal — REVISE (single-owned, rule stands; record updated)

The sealed-execution queryset at HEAD: everything the prior record says,
with the combined arm recomposed — a servable combinator is SERVED as
the set of primary keys it selects (`<model>.filter(pk__in=<combined>
.values("pk"))` with the outer ordering re-applied), and only a shape
the rewrite would change fails closed as `combined`. Codes now run
`type` -> `table` -> `untrusted` -> `routing` -> `evaluated` -> `sliced`
-> `projection` -> `combined` -> `alias`
(`utils/querysets.py:3475`; projection moved before combined so a
`.values()` combinator a model-row surface refuses is never turned into
model rows). The seal still never returns the consumer object (fresh
`models.QuerySet` at `:3792`, clone-writes at `:3803`-`:3810`), still
executes zero SQL, still drops `_result_cache` except under the raw-list
policy (exact-`list` check `:3741`, carriage `:3811`), still has no
identity fast path (comments `:4436`-`:4440` + `:4715`-`:4718`), still
has no unseal (package `unseal` grep: prose adjectives +
`_UNSEALABLE_STATE_CAUSES` only).

Definition census (directory pathspec, HEAD bytes): `def
_seal_or_defect` exactly once package-wide (`utils/querysets.py:3462`,
spans `:3462`-`:3928`); 6 `_SealPolicy` constructions at the one
declaration site (`:2880` default, `:2887` cascade
`(require_model_rows=False)`, `:2896` prefetch-child
`(reject_sliced=False, require_shared_alias=True)`, `:2909`
list-relation-child `(require_shared_alias=True)`, `:2915`
sidecar-result `(require_unevaluated=True)`, `:2926` raw-list-source
(`require_model_rows=False, reject_sliced=False,
rewrite_combined=False, carry_result_cache=True)`); 6 fields
(`:2869`-`:2874`, `rewrite_combined` default on); 5 call shapes in-owner
(`:2608` recursive prefetch under `_PREFETCH_CHILD_POLICY`, `:3104`
orderset under `_SIDECAR_RESULT_POLICY` + the one `expected_routing`,
`:3897` raw-list, `:4234` source, `:4340` result); `reject_combined`,
`_LIST_ARGUMENT_VISIBILITY_POLICY`, `_sidecar_visibility_policy` zero
hits package-wide. The rewrite helpers live inside the one seal body:
`_is_model_column` `:3341` (sole caller `:3393`),
`_combined_lost_property` `:3367` (callers `:3408` self-recursive +
`:3447`), `_pk_membership_query_or_defect` `:3432` (callers: seal
`:3770` + walker `:1419` by name).

Consumer census (all compose by name; zero duplicated seal bodies):
in-owner `visibility_scoped_related_queryset` (`:4451`, composes
`:4467`) alongside the listed `_prepared_visibility_source` /
`_normalized_visibility_result` (sole callers: runners `:4441` /
`:4719`) / `_validate_post_orderset_result` + `_snapshot_routing_intent`
(`:3201` `:3209` `:3234` `:3248`, inside `_apply_sidecar_sync/async`)
/ `normalized_row_source` / `materialized_rows` /
`prepared_resolver_source` (callers `:4832` `:4858` in the
`post_process_queryset_result` runners) / shared sidecar appliers;
permissions root (`:631`, `policy=` `:635`) + edge (`:711`, `policy=`
`:717`); list field `:1463` `:1509` (default policy, no `policy=`
anywhere in file) + `apply_orderset` `:1474` `:1520` +
`prepared_resolver_source` `:1732` `:1782`; walker
`_build_child_queryset` `:549` (default `:556`, seal `:629`,
pass-through `:635`) + `_build_connection_child_queryset` `:640`
(`:663`) + call `:1188`, and `_apply_hint` `:1240` ->
`_hint_prefetch_over_pk_set` `:1316` / `:1398` (rewrite `:1419`,
`_COMBINED_WHAT` `:1424`, the one outside-owner `models.QuerySet(`
`:1426`, strict-forward `:1432`); connection prepared head `:1812`
(guards `:1810` `:1817`) + seals `:1900` `:1947` + shared sidecar
appliers; types/resolvers recheck `:424` `:428` / `:447` `:452` +
prefetch-cache `:602`-`:603` + `bounded_rows*` `:605` `:620` `:624`;
resource_policy `_windowed_rows` `:1012` / `:1235` + normalized `:1069`
+ `bounded_rows` `:1082` / `:1315`; relay 6 sites (`:984` `:1009`
`:1051` `:1053` `:1076` `:1078`, the `:1051` / `:1076` `node_ids=None`
re-seals new); filters/sets child seals `:2760` `:2795`;
mutations/resolvers locate seal `:713`. `sql.Query(` zero outside the
owner. External `policy=` passers: exactly permissions x2 + walker x2;
in-owner threading x4 (`:4426` `:4447` `:4704` `:4725`). `M6` holds:
`type_cls.get_queryset(` exactly `:4428` + `:4706`.

Message-site arms (all six ladders render exactly their reachable keys;
`_defect_message` `:4070` fails loud (`:4088`-`:4093`): orderset 8 keys
(`:3137`-`:3152`: 6-shape map + own `combined` + own `routing`; `alias`
subsumed by comment), prepared-source 6
(`:4243` `:4248` `:4253` `:4258` `:4266` `:4270`), result-error 7
(`:4121` `:4127` `:4133` `:4138` `:4145` `:4149` `:4155`), raw-list 3
(`:3992` `:3996` `:4001`), cascade root 5 (`:364` `:370` `:374` `:380`
`:385`), cascade edge 6 (`:425` `:430` `:438` `:445` `:452` `:457`).
Zero dead arms (combined unreachable only under the raw-list policy;
`evaluated` / `routing` only at the orderset site;
`require_unevaluated=True` solely at `:2915`).

Challenges re-derived: C1=1 (new code takes one ordering position;
per-site arms are consumers). C2=1 (new axis is one field + its check;
`rewrite_combined` is the worked example — field `:2871`, check
`:3769`, declarations only elsewhere; the connection pre-slice guard
stays rejected, R-guard). C3=0 (state-walk replaces method inventory;
the seal-side rewrite runs on the proven-genuine `rebuilt_query`; the
walker path reads trusted schema configuration — author `OptimizerHint`
input, not consumer hook results — per the `:3367` docstring). C4=1
(the drift added three composing call sites — walker `:1419`, relay
`:1051` `:1076` — by name, no definition moves). Owner stays
`utils/querysets.py::_seal_or_defect` (narrowest cohesive, dependency
direction unchanged); lifetime per-call, nothing cached.

Record corrections (verdict-neutral): (1) `_ORDERSET_RESULT_POLICY`
never existed (zero hits at base and HEAD) — the policy is
`_SIDECAR_RESULT_POLICY`. (2) Base carried 7 constructions (prior
omitted `_LIST_RELATION_CHILD_POLICY`); HEAD carries 6
(`_LIST_ARGUMENT_VISIBILITY_POLICY` deleted). (3) list_field/connection
compose the shared sidecar appliers in-owner (pre-base move; prior text
described direct snapshot/validate composition). (4) Previously
unlisted in-owner consumers: `visibility_scoped_related_queryset`,
`_apply_sidecar_sync/async`, the shared appliers.

### R-wording — REVISE (rejection stands; one shared sentence noted)

Per-site refusal prose stays per-site: all six ladders re-read at HEAD
(root, edge, source, result-defaults, orderset, raw-list) still name
their own subject and contract; only the `combined` arms changed, and
they changed identically in shape — own subject prefix + the shared
what-phrase. `_COMBINED_WHAT` re-derived from the family side: 1
definition (`utils/querysets.py:3973`) + 6 code composers (`:3149`
orderset, `:4147` result-error, `:4268` prepared-source,
`permissions.py:387` root, `permissions.py:455` edge,
`optimizer/walker.py:1424`) + 2 prose cites (`:3117`,
`permissions.py:409`) — the s16 F3 population pin-for-pin. Difference
from the prior home clause: `_defect_message` (`:4082`-`:4084`) still
says "what is shared is the dispatch and the exhaustiveness, never the
wording" — now doubly stale (cause list + combined text; s16 O1). The
merger rejection stands (merging subjects would still misattribute);
the home clause update belongs to s18 (`seal-defect-code-wording` owns
gate-plus-declaration). Trigger stands. No edit owed by this family.

### R-guard — CONFIRM (rejection stands; landing still pending)

`connection.py::_guard_source_not_pre_sliced` re-read at HEAD: def
`:1648` (drift is the `models.QuerySet[models.Model, object]`
annotation only), dispatch read `source.query.is_sliced` `:1665`,
fail-closed unreadable arm raising client-facing `GraphQLError`,
fires regardless of sidecar input; call sites `:1030` (direct) +
`:1817` (passed as `queryset_guard`). The fourfold difference from the
seal's `sliced` proof (stage, read discipline, error contract,
coverage) re-verified unchanged. Landing still pending: the guard
docstring carries no seal-vs-triage seam clause — record-only carry to
closeout (Worker 0 schedules with the 09-19 R-guard Home record; no new
card, blocks nothing). Zero-edit item makes no prose edit.

### Old D5 / D-W2-a — GONE, re-confirmed from the tree

- D5: all six message ladders carry exactly their reachable keys (8 / 6
  / 7 / 3 / 5 / 6 per the F-seal census) with the shared loud default;
  zero dead arms re-derived. Gone.
- D-W2-a: `_UNRECOMPOSED_CHILD_POLICY` zero hits package-wide at HEAD.
  Gone. Not re-filed.

### Carried run-8 evidence tested from the family side

- s16: rewrite helpers inside the one seal body CONFIRMED
  (sole-definition census above; the only external composition is the
  walker's by-name call). s16 F3 `_COMBINED_WHAT` 1+6+2 CONFIRMED
  pin-for-pin (R-wording). s16 I-R4 runner set CONFIRMED (external
  `policy=` exactly permissions x2 + walker x2; default everywhere
  else; `require_unevaluated=True` solely `:2915`).
- s11: seal-side `:3733` (snapshot-key `state.get` into
  `_sealed_prefetch_related_lookups`) + `:3806` (clone-write onto the
  sealed object) both inside `_seal_or_defect` (`:3462`-`:3928`;
  exclusion under seal contracts CONFIRMED. Package-wide
  `_prefetch_related_lookups` census re-derived: exactly the s11
  population (`optimizer/plans.py:572` lenient + `walker.py:1432`
  strict-forward live reads; rest def-name / prose / the two
  seal-contract lines) — rename-count-2 re-proved.
- s12: walker `:1426` constructs around the seal's own rewrite composed
  at `:1419`, with `:1432` the strict-forward composed read; the helper
  extracts no state, proves nothing, delegates the rewrite and fails
  closed — consumer shape CONFIRMED, not a second sealing body.

### Worktree dirt attribution (by content; all concurrent, zero owned)

`-U0` hunks, worktree vs HEAD (`truth.+` = hunt introspection
migration; seal-site census re-run in the worktree matches HEAD in
shape on all 11 files — same call sites, same 6 policy constructions,
same `policy=` passers, excluded file still zero):

| File | + / - | Hunks (content) |
|---|---|---|
| `utils/querysets.py` | +222 / -283 | 115 truth + 23 other (roots, `_safe_class_name` deletion, except-narrowing, reformat, docstring) — the s16 table, same bytes (`cfc773ba`) |
| `permissions.py` | +42 / -36 | 24 truth + 15 other (truth import, spec-034 prose, `name`/`edge` re-derivation, `_walk` conditions batch, twin docstring) |
| `list_field.py` | +85 / -143 | 19 truth + 26 other (validator rework, trigger prose, wire-name reads) — 0 seal-function hunks |
| `optimizer/walker.py` | +9 / -10 | 8 truth + 2 other (header + import root) |
| `connection.py` | +130 / -126 | 7 truth + 37 other (window/fallback rework, imports, prose) — 0 seal-content lines |
| `types/resolvers.py` | +45 / -21 | 2 truth + 20 other (deadline, boundary worker, stub reads) — 0 seal-function hunks |
| `resource_policy.py` | +32 / -39 | 5 truth + 11 other — 0 seal-function hunks |
| `types/relay.py` | +129 / -75 | 29 truth + 17 other (lazy-unwrap, slot param, trigger prose) — 0 seal-function hunks |
| `filters/sets.py` | +153 / -63 | 32 truth + 13 other (registry reads, form-key rework) — 0 seal-function hunks |
| `mutations/resolvers.py` | +56 / -21 | 6 truth + 12 other (wire-name map) — 0 seal-function hunks |
| `extensions/resource_policy.py` | +7 / -23 | 0 truth + 4 other (`_ValueBudget` rework) — excluded, still zero seal imports |

Seal-call/policy content lines in the dirt: exactly 8, all
introspection-expression swaps inside unchanged composing calls
(`_safe_type_name(value)` -> `truth.kind(value)` at the raw-list raise;
`.__name__` -> `truth.name(...)` in the 3 `_COMBINED_WHAT.format`
model args). Composition shape, policies, and census unaffected. The
trace reads HEAD bytes throughout.

### Defects

None new. The walker's attribute reads (`inner.query`, `inner._db`,
`inner._hints`) are documented trusted-configuration input, not a
seal-contract bypass (different trust level by design). The R-guard
owner-home clause pends as record-only closeout prose, not a defect.

### Pending execution

None owed. Zero edits, no new oracle (the drift's oracles exist at the
mandated tiers: live `test_combined_visibility_api.py` (+1266) +
`tests/utils/test_querysets.py` seal-matrix updates (+266) + walker /
permissions / connection / list live-suite updates in `5c5e32c5`,
cited by content, not run). Probes cited by content under `/tmp/s17`.
WS slot-2 left on disk for Worker 2; remove by explicit path after
verification. Shared-tree authorization unspent.

### Judgment

The seal is still one function plus one policy record; the drift
recomposed its combined arm (serve-as-pk-set under `rewrite_combined`)
and every surface followed by composition, not by restatement: one
default policy on the read surfaces, one shared what-phrase, one new
by-name consumer in the walker, two re-seal sites in relay. Both
candidate merges stay rejected with difference, trigger, and home;
both old defects stay gone. Zero production edits.

Item-scoped diff state: this item wrote only this artifact (header
swap + this section) — verified at write: all 11 family `.py` files
are byte-identical between the pre-work sync copy and the worktree,
and the runner reports shared moved by exactly 1 file (this artifact)
since sync. Every `.py` hunk in the worktree is concurrent dirt
content-attributed above, untouched by this item.

### Exact plan rows owed (Worker 0 applies)

- Repeat of the 09-19 owed extension (never applied — the index row
  still names 7 files): Files covered adds `types/relay.py`,
  `filters/sets.py`, `mutations/resolvers.py`; Status `open` ->
  `consolidated` (already-single; this re-trace). Tick text when
  verified: REOPENED run 8, re-trace verified s17 (1 CONFIRM + 2
  REVISE + GONE re-confirmed, zero-edit).
- No NEW rows: the combined-what row is already rowed run 8 under
  `seal-defect-code-wording`; rewrite helpers live inside the seal
  body; `walker.py:1426` is a consumer; the e1-style flags belong to
  their own items.

## Run-8 verification (Worker 2)

Run: 0.0.15 2026-09-30-8. The W1 section above is the CLAIM
under test; every count below is re-derived expectation-first at
HEAD bytes. All execution via `workspace.py run
dry/sealed-exec-retrace-s17/verify` (slot-3, synced
2026-09-30T20:38:37Z; the copy carries no `.git`, so all git
reads are `git -C <shared>` through the runner). Package-wide
greps use the directory pathspec `django_strawberry_framework/`
(the `**/*.py` form misses top-level files). The target is never
imported: pure `git show` bytes plus `git grep`. No pytest;
read-only probes only.

### Scope and fingerprints (Worker 2, all three states)

Drift base `0c0537e2`, HEAD `83998e08` (both `rev-parse`
confirmed; HEAD unmoved at close).
`ITEM_BASELINE=4fa16e78b8bddd4ba766617141d1c5de22cc1c0c`
resolves (`cat-file -t` = commit). Base/HEAD blobs via
`rev-parse --short=8 <commit>:<path>`, worktree via
`hash-object | cut -c1-8`, all through the runner:

| File | Base | HEAD | Worktree |
|---|---|---|---|
| `utils/querysets.py` | `3616927d` | `392e50d0` | `cfc773ba` |
| `permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` |
| `list_field.py` | `21380eb7` | `77ddb86c` | `1dcb0c43` |
| `optimizer/walker.py` | `75f9c6b6` | `bdd9c2f1` | `9130aceb` |
| `connection.py` | `4894f90f` | `3d6dd424` | `64b85d0e` |
| `types/resolvers.py` | `72d62dc4` | `574e9768` | `7a953c53` |
| `resource_policy.py` | `4b69e974` | `47befb3f` | `927b89a2` |
| `types/relay.py` | `52439862` | `968fb95a` | `6c2e8c20` |
| `filters/sets.py` | `993e887a` | `3d307402` | `ec278851` |
| `mutations/resolvers.py` | `043a2d0b` | `7a25afea` | `dd00ec6e` |
| `extensions/resource_policy.py` | `19e2309d` | `5cc373ec` | `8944e79e` |

All 33 match W1. Per-file commit sets re-derived independently;
all match W1 except `list_field.py` (see record corrections:
7 typing commits, not 6).

### Delta (Worker 2, 15 commits, 7+7+1)

`git log --oneline --no-merges 0c0537e2..83998e08` on the 11
files names exactly 15 commits: behavior `5c5e32c5`
`2935e0e4` `10d2b9cd` `dbf0a870` `193f9946` `b63df99d`
`bbe54687` (7); typing `999a1aab` `b20277fe` `dd3a10b1`
`5f440a93` `849f67bc` `dfbea72b` `fef11e64` (7); pragma
`e37448e5` (1). Classification re-derived by content:

- `5c5e32c5` (seal rewrite, read end to end): owner
  `reject_combined` -> `rewrite_combined` (default on),
  `_LIST_ARGUMENT_VISIBILITY_POLICY` deleted,
  cascade/sidecar/raw-list recomposed, new `_is_model_column` /
  `_combined_lost_property` /
  `_pk_membership_query_or_defect` / `_COMBINED_WHAT`, combined
  arm after projection, three message sites recomposed;
  connection `_sidecar_visibility_policy` deleted, list field
  `policy=` kwargs deleted, walker `_hint_prefetch_over_pk_set`
  new, permissions renderers compose `_COMBINED_WHAT`.
  Seal-bearing, as claimed.
- `2935e0e4` (relay re-seal): `_resolve_nodes_default/_async`
  `node_ids=None` returns a fresh `apply_type_visibility_*`
  seal (+2 composing call sites). Confirmed.
- Seal-neutral behavior (full diff read + zero seal-token
  lines in `+/-`): `10d2b9cd` (order tier: new
  `default_order`/`applied_order` + `_finalize_queryset` /
  `_selected_ordering` reads), `dbf0a870` + `193f9946`
  (connection pagination window/keyset/fallback),
  `b63df99d` (`_apply_node_filter` split; seal lines are
  context only), `bbe54687` (filters relation-identity;
  zero `apply_type_visibility` touches). All five verdicts
  SUSTAINED.
- Typing-only (seal-function hunks sampled by content; all
  casts, annotations, `type: ignore` comments, `@overload` /
  `@override`, one local rename with cast-back in
  `999a1aab`, cast-wrapped same-expression appends in
  `b20277fe`, cast removals where stubs turned true in
  `fef11e64`): `999a1aab`, `b20277fe`, `fef11e64` carry
  seal-function hunks, all typing-only;
  `dd3a10b1`/`5f440a93`/`849f67bc`/`dfbea72b` carry zero
  seal-function hunks on family paths (hunk headers:
  signatures, `ListArgumentError`, `@override` imports,
  keyset/pagination comments); `e37448e5` is one pragma
  line. Classifications SUSTAINED (hunk counts differ by
  seal-function definition; see record corrections).

### F-seal REVISE — survives

Re-derived at HEAD bytes (directory pathspec):

- `def _seal_or_defect` exactly once package-wide
  ([querysets.py][querysets] `:3462`, spans `:3462`-`:3928`).
- 6 `_SealPolicy` constructions at the one declaration site
  (`:2880` default, `:2887` cascade
  `(require_model_rows=False)`, `:2896` prefetch-child,
  `:2909` list-relation-child, `:2915` sidecar-result,
  `:2926` raw-list-source); 6 fields with
  `rewrite_combined: bool = True` (`:2871`).
- 5 call shapes in-owner (`:2608` recursive prefetch under
  `_PREFETCH_CHILD_POLICY`, `:3104` orderset under
  `_SIDECAR_RESULT_POLICY` with the one
  `expected_routing`, `:3897` raw-list, `:4234` source,
  `:4340` result). `reject_combined`,
  `_LIST_ARGUMENT_VISIBILITY_POLICY`,
  `_sidecar_visibility_policy` zero hits package-wide.
- Rewrite helpers inside the one seal body:
  `_is_model_column` `:3341` (sole caller `:3393`),
  `_combined_lost_property` `:3367` (callers `:3408`
  self-recursive + `:3447`), `_pk_membership_query_or_defect`
  `:3432` (callers `:3770` seal + [walker.py][walker]
  `:1419` by name).
- Codes `type` -> `table` -> `untrusted` -> `routing` ->
  `evaluated` -> `sliced` -> `projection` -> `combined` ->
  `alias` (docstring `:3474`-`:3475`; implementation
  routing `:3640`, evaluated `:3753`, sliced `:3755`,
  projection `:3757`, combined `:3769`, alias
  `:3777`/:3783). Fresh `models.QuerySet` at `:3792`,
  clone-writes `:3803`-`:3810`, exact-`list` check
  `:3741`, carriage `:3811`, no fast path
  (`:4436`-`:4440` + `:4715`-`:4718`), no unseal
  (package `unseal` grep: prose adjectives +
  `_UNSEALABLE_STATE_CAUSES` only).
- Consumers compose by name; zero duplicated seal bodies.
  In-owner: `visibility_scoped_related_queryset`
  (`:4451`), `_apply_sidecar_sync/async` (`:3175` /
  `:3218`), shared appliers, `prepared_resolver_source`
  (`:4777`, callers `:4832` `:4858`).
  [permissions.py][permissions] root `:631` (`policy=`
  `:635`) + edge `:711` (`policy=` `:717`).
  [list-field.py][list-field] `:1463` `:1509` (no
  `policy=` anywhere in file) + `apply_orderset`
  `:1474` `:1520` + `prepared_resolver_source`
  `:1732` `:1782`. Walker `:549` (default `:556`,
  seal `:629`, pass-through `:635`) + `:640`
  (`:663`) + call `:1188`, `_apply_hint` `:1240` ->
  `:1316` / `:1398` (rewrite `:1419`,
  `_COMBINED_WHAT` `:1424`, `models.QuerySet(`
  `:1426`, strict-forward `:1432`).
  [connection.py][connection] head `:1812` (guards
  `:1810` `:1817`) + seals `:1900` `:1947`.
  [resolvers.py][type-resolvers] `:424` `:428` /
  `:447` `:452` + `:602`-`:603` + `:605` `:620`
  `:624`. [resource-policy.py][resource-policy]
  `:1012` / `:1235` + `:1069` + `:1082` / `:1315`.
  [relay.py][types-relay] 6 sites (`:984` `:1009`
  `:1051` `:1053` `:1076` `:1078`; `:1051` / `:1076`
  new). [filter-sets.py][filter-sets] `:2760`
  `:2795`. [mutation-resolvers.py][mutation-resolvers]
  `:713`. `sql.Query` zero outside the owner (stronger
  than claimed). External `policy=` exactly
  permissions x2 + walker x2; in-owner threading x4
  (`:4426` `:4447` `:4704` `:4725`).
  `type_cls.get_queryset(` exactly `:4428` + `:4706`.
- Message ladders render exactly their reachable keys:
  orderset 8 (6-shape map `:3137`-`:3147` + own
  `combined` `:3148` + own `routing` `:3151`; `alias`
  subsumed per comment `:3122`-`:3128`),
  prepared-source 6, result-error 7, raw-list 3, cascade
  root 5, cascade edge 6; `_defect_message` `:4070`
  fails loud (`:4088`-`:4093`). Zero dead arms
  (combined unreachable only under raw-list;
  `require_unevaluated=True` solely `:2915`). Key
  line numbers corrected for two ladders (see below);
  counts and sets confirmed.
- Challenges: C1=1 (one ordering position; arms are
  consumers). C2=1 (one field + its check;
  `rewrite_combined` field `:2871`, check `:3769`,
  declarations only elsewhere; guard stays rejected).
  C3=0 (state-walk; seal rewrite on proven-genuine
  `rebuilt_query`; walker reads trusted `OptimizerHint`
  per `:3384`-`:3387`). C4=1 (drift added three
  composing call sites — walker `:1419`, relay
  `:1051` `:1076` — by name, no definition moves).
  Owner stays [querysets.py][querysets]
  `::_seal_or_defect`; lifetime per-call, nothing
  cached.
- Record corrections verified: (1)
  `_ORDERSET_RESULT_POLICY` zero hits at base and HEAD
  (policy is `_SIDECAR_RESULT_POLICY`); (2) base
  carried 7 constructions (incl.
  `_LIST_RELATION_CHILD_POLICY`), HEAD 6
  (`_LIST_ARGUMENT_VISIBILITY_POLICY` deleted);
  (3) list/connection compose shared sidecar appliers
  at base and HEAD (zero direct
  snapshot/validate imports in either file);
  (4) `visibility_scoped_related_queryset`,
  `_apply_sidecar_sync/async`, shared appliers
  confirmed in-owner.

REVISE stands.

### R-wording REVISE — survives

All six ladders re-read: own subject and contract at each
site; only the `combined` arms changed (own subject prefix
+ shared what-phrase). `_COMBINED_WHAT` re-derived: 1
definition (`:3973`) + 6 code composers (`:3149`
orderset, `:4147` result-error, `:4268`
prepared-source, [permissions.py][permissions] `:387`
root + `:455` edge, [walker.py][walker] `:1424`) + 2
prose cites (`:3117`, [permissions.py][permissions]
`:409`) + 2 imports — the s16 F3 population pin-for-pin.
`_defect_message` (`:4082`-`:4084`) still says "what is
shared is the dispatch and the exhaustiveness, never the
wording" — stale (cause list + combined text shared;
s16 O1). Merger rejection stands; home-clause update
belongs to s18 (`seal-defect-code-wording` owns
gate-plus-declaration; its tick line already records O1
doubly false). Trigger stands. No edit owed by this
family.

### R-guard CONFIRM — survives

[connection.py][connection]
`::_guard_source_not_pre_sliced` re-read: def `:1648`
(drift is the `models.QuerySet[models.Model, object]`
annotation only, confirmed by
`0c0537e2..83998e08` diff), dispatch read
`source.query.is_sliced` `:1665`, fail-closed unreadable
arm raising client-facing `GraphQLError`, fires
regardless of sidecar input (docstring `:1658`-`:1659`);
call sites `:1030` (direct) + `:1817` (passed as
`queryset_guard`). Fourfold difference from the seal's
`sliced` proof (stage, read discipline, error contract,
coverage) re-verified unchanged. Landing still pending:
the guard docstring (`:1649`-`:1662`) carries no
seal-vs-triage seam clause. Record-only carry to closeout
(Worker 0 schedules with the 09-19 R-guard Home record;
no new card, blocks nothing). Zero-edit item makes no
prose edit.

### Old D5 / D-W2-a GONE — re-confirmed

- D5: all six ladders carry exactly their reachable keys
  (8 / 6 / 7 / 3 / 5 / 6) with the shared loud default;
  zero dead arms re-derived. Gone.
- D-W2-a: `_UNRECOMPOSED_CHILD_POLICY` zero hits
  package-wide at HEAD. Gone. Not re-filed.

### Carried run-8 evidence (family side, fresh derivation)

- s16: rewrite helpers inside the one seal body
  CONFIRMED (sole-definition census above; only external
  composition is the walker's by-name call). F3 1+6+2
  CONFIRMED pin-for-pin. I-R4 runner set CONFIRMED
  (external `policy=` exactly permissions x2 + walker
  x2; default everywhere else;
  `require_unevaluated=True` solely `:2915`).
- s11: seal-side `:3733` (`state.get` into
  `_sealed_prefetch_related_lookups`) + `:3806`
  (clone-write) both inside `:3462`-`:3928`;
  exclusion under seal contracts CONFIRMED.
  Package-wide `_prefetch_related_lookups` census:
  exactly the s11 population
  (`optimizer/plans.py:572` lenient +
  `walker.py:1432` strict-forward live reads; rest
  def-name / prose / the two seal-contract lines).
- s12: walker `:1426` constructs around the seal's own
  rewrite composed at `:1419`, with `:1432` the
  strict-forward composed read; the helper extracts no
  `__dict__` state, proves nothing, delegates the
  rewrite and fails closed — consumer shape CONFIRMED,
  not a second sealing body.

### Worktree dirt (by content; concurrent, zero owned)

`--numstat HEAD` splits re-derived: querysets
+222/-283, permissions +42/-36, list_field +85/-143,
walker +9/-10, connection +130/-126, types/resolvers
+45/-21, resource_policy +32/-39, relay +129/-75,
filters/sets +153/-63, mutations +56/-21,
extensions/resource_policy +7/-23 — all 11 match W1.
Seal census re-run in the worktree (copy = shared, fresh
at every run): same 1 def, same 6 policy constructions,
same 5 call shapes, same 4 external `policy=` passers,
same 1+6+2 `_COMBINED_WHAT` population (3 model args
swapped `.__name__` -> `truth.name(...)`), excluded
file still zero in HEAD and worktree. Composition
shape, policies, and census unaffected; the trace reads
HEAD bytes throughout. Owned-changes note: the ledger
names adopted orphans in family files beyond D1, but
those bytes are in neither HEAD nor this worktree
(`run_in_one_sync_boundary`, `type-stamp`,
`relay-node-target-guard` prose all zero in both), so
the current dirt is concurrent, zero owned, as claimed
for this worktree.

### Zero-edit vs ITEM_BASELINE

`git diff 4fa16e78 --name-only --
django_strawberry_framework/` is EMPTY (zero `.py`
files). The artifact is untracked (`??`); the sole
tracked change since the baseline is
`docs/dry/dry-0_0_15.md` (plan). This item wrote only
this artifact. Shared-tree authorization unspent. No
pytest run (none authorized, none owed for zero edits).

### Index-row / home-clause instructions — correct as exact text

- Plan index row at HEAD still names 7 files, status
  `open`; tick box still `[ ]` (worktree line 1300
  shows REOPENED s17 queued). The owed extension
  (Files covered adds `types/relay.py`,
  `filters/sets.py`, `mutations/resolvers.py`; Status
  `open` -> `consolidated`; tick text REOPENED run 8,
  1 CONFIRM + 2 REVISE + GONE, zero-edit) is the
  correct replacement.
- No NEW rows: `_COMBINED_WHAT` is already rowed run 8
  under `seal-defect-code-wording` (worktree line
  1288: identical 1+6+2); rewrite helpers live inside
  the seal body; `walker.py:1426` is a consumer (this
  verification); e1-style flags belong to their own
  items. The s18 home-clause handoff (wording-clause
  update owned by `seal-defect-code-wording`) matches
  that family's tick line (O1 doubly false).

### Record corrections (verdict-neutral, Worker 2)

1. `list_field.py` per-file freshness: 7 typing commits
   (`999a1aab` `b20277fe` `dd3a10b1` `5f440a93`
   `849f67bc` `dfbea72b` `fef11e64`), not 6. Seal
   shapes intact either way.
2. Typing seal-hunk counts by Worker 2's seal-function
   list: `999a1aab` 16 (W1: 15), `b20277fe` 67 (W1:
   60), `fef11e64` 3 (match). All sampled hunks are
   typing-only; the classification stands, counts
   differ by function-list definition.
3. Prepared-source key lines at HEAD are `:4244`
   `:4249` `:4254` `:4259` `:4266` `:4270` (W1 cites
   `:4243` `:4248` `:4253` `:4258` for the first
   four — off by one; sets and count correct).
4. Raw-list key lines at HEAD are `:3994` `:3998`
   `:4003` (W1 cites `:3992` `:3996` `:4001`; sets
   and count correct).
5. `## Owned changes` names adopted orphans in family
   files beyond the D1 row; those bytes are absent
   from this worktree, so the zero-owned attribution
   for the current dirt stands.

No `(Worker 2)` entries under `## Defects` (prior
sections preserved intact). No new defects: the
walker's attribute reads are documented
trusted-configuration input, and the R-guard clause
pends as record-only closeout prose.

Verdict: `Status: verified`. Zero production edits.
Concurrent dirt and the contested file-item sections
preserved; nothing committed. WS slot-3 left on disk
for Worker 0; remove by explicit path after tick
(`/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-3`).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutation-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[permissions]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[resource-policy-ext]: ../../django_strawberry_framework/extensions/resource_policy.py
[type-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
