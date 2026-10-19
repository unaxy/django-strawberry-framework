# Review · Performance: `django_strawberry_framework/schema.py`

Status: no-findings
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5ef09ed4565b774a3f9cda2f473514732bf12064

Path class: hot — the chain build runs once per operation
(`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`),
the return seam once per non-streamed operation
(`django_strawberry_framework/schema.py::DjangoSchema._masked_return`
via `execute` / `execute_sync`), the runner construction once per
operation
(`django_strawberry_framework/schema.py::DjangoSchema.create_extensions_runner`),
the marker check once per executed field
(`django_strawberry_framework/schema.py::DjangoMutationExecutionContext.execute_field`),
each generated-mutation window once per top-level mutation field
(sync and async twins), and the resume gate once per streamed
operation
(`django_strawberry_framework/schema.py::DjangoSchema._stream`).
Cold: construction (`__init__`, the `extensions` setter, the
`_consumer_extension_entries` split), import (the refusal documents),
and refusal (exceptional: a broken deployment's every operation).

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target and no Routed lead on this item),
`docs/review/rev-schema.md` (skeleton: `Status: reviewing`, blank
Path class). Sibling axis records
(`rev-schema.{performance,mechanics,comments}.md`) did not exist when
read, and still do not at close; no Handoff or Cross-axis text was
available.

Target read whole (1408 lines, blob `84f2d5aa`). The target is dirty
vs HEAD (`+17/-19` per `git diff --stat` — concurrent work, reviewed
as it stands per the dispatch; no hunk attributed here). The dirty
content is the truthful-reads migration and nothing else:
`describe_value` to `truth.describe` on raise/refusal paths,
double-`getattr` to `truth.static_attr` on the marked-mutation path,
`issubclass(type(...))` to `truth.is_instance` / `truth.is_type` /
`truth.is_subclass` on the per-member, per-stream and construction
checks. Two hunks touch hot paths (the marked-mutation meta read at
:256-:257 and the per-member `_is_extension` at :1243); both are
measured below (R7, R3). `tests/test_schema.py` is dirty beside it
(`+11/-91`, concurrent test work, body not read). A re-review is owed
if concurrent work lands a new hot-path reader or a new per-operation
statement.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/schema/performance/inspect/` (json
`docs/review/temp-tests/schema/performance/schema.json`): 50 symbols,
0 Django/ORM markers, 1 per-row lead (the `close` cancel-surviving
loop — discharged below, it awaits one transition future, never rows),
3 hot entry points, all three the `_RefusedConfiguration` hooks
(exceptional path; the real hot paths are mapped by hand below), 6
import-time calls (R10).

Hot-path map (callers traced by hand over the package plus first-hand
reads of the installed upstream at strawberry-graphql 0.324.0):

- Per field: graphql-core calls
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext.execute_field`
  for every executed field; unmarked fields return after
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._marked_mutation_class`
  (125 ns query parent, 333 ns full mutation-field walk).
- Per operation: upstream `execute` / `execute_sync` / `subscribe`
  call `self.get_extensions()` and `self.create_extensions_runner()`
  (verified at upstream `schema.py:747`, `:821`, `:1158`; the `sync`
  flag is the `_operation_mode` fact). The admitted chain costs 4.0
  us in the real factory shape, 2.8 us empty.
- Per non-streamed operation: the overrides add one frame plus
  `django_strawberry_framework/schema.py::DjangoSchema._masked_return`
  (375 ns inactive, 458 ns active-clean).
- Per generated mutation field: the sync twin holds one outer
  `transaction.atomic` (10.1 us enter/exit CPU, of which 9.7 us is
  Django's own; it substitutes for the pipeline's own outer atomic)
  and nests the pipeline's atomic, which adds exactly the
  SAVEPOINT/RELEASE pair (probe B statement list). The async twin
  adds the private-thread machinery (139 us, R1) around the same
  nesting. No per-row work exists on either twin: the window is one
  atomic for the whole field, and completion inside it runs no target
  code per row.
- Per streamed operation: one `truth.is_instance` gate (~333 ns, same
  predicate as row `is_extension_check`).
- Per operation, through the private record: one authority recall
  plus two membership recalls in `get_extensions` (167 + 167/250 ns
  each, R4), one authority recall in `_masked_return`, and one
  `copy_policy` per policy read by the arming/teardown hooks (250 ns
  each, R5).
- Cold: `__init__` (two policy resolutions + the entries split),
  the `extensions` setter (per-entry resolvability check), the
  refusal chain (only when the accepted configuration is unreadable),
  import (R10). `create_extensions_runner` is one constructor call;
  the constructor body is
  `extensions/operation_state.py::DjangoExtensionsRunner`, whose own
  item measures it.

Measurements, address `review/schema.py/performance`, package digest
`sha256:b4b25dfd...f3df0d3c` on every run (tree as it stands, not the
plan's bench-baseline digest; every figure is self-referenced and no
before/after exists — no findings). No bench-baseline figure moves:
nothing is proposed, and the per-operation overheads measured here
are constants present identically in baseline and gate.
`_bench_common.py` blob `253a3953` matches the baseline on every run;
`importtime_report.py` blob `15f679c9` equals gate-2's and differs
from the cycle baseline's `bfce84b9`, so the importtime row compares
nothing there. Provenance on every run: python 3.14.2, django 6.1,
strawberry-graphql 0.324.0, in-memory SQLite
(`file:dsf-bench-default?mode=memory&cache=shared`), macOS arm64.

- `review-20260929T122140-bd2290`: `probe_hot_costs.py` (probe blob
  `c419c6da`), minimal `DjangoSchema` objects, medians as printed
  per row: marked lookup 125.0 ns (query parent) / 333.0 ns (full
  mutation-field walk), `get_extensions` 2791.0 ns (empty) /
  4167.0 ns (one class entry), recalls 167.0 / 167.0 / 250.0 ns
  (authority / membership empty / membership one),
  `is_extension` 333.0 ns, `claimed_authority` 750.0 ns,
  `masked_return` 375.0 ns (inactive) / 458.0 ns (active, clean
  result), `copy_policy` 250.0 ns, window enter/exit 10125.0 ns vs
  bare atomic 9667.0 ns, error-list length 125.0 ns, clean rollback
  check 166.0 ns, `closed_in_transaction` read 834.0 ns,
  `resolve_write_alias` 83.0 ns (None) / 167.0 ns (model),
  `async_execution` 250.0 / 291.0 / 125.0 ns (unbound / bound sync /
  bound async), one refusal parse 17042.0 ns, full async window
  139354.0 ns (n=60) vs executor construction alone 1375.0 ns.
- `review-20260929T122213-c01c46`: `probe_mutation_window.py` (probe
  blob `f383af5c`), the real aggregated fakeshop schema (build
  1.35 s, cold): real `register` marked lookup 375.0 ns, meta read
  83.0 ns (old double-`getattr`) vs 500.0 ns (new `static_attr`),
  `resolve_write_alias` on the real model 167.0 ns, real
  factory-entry `get_extensions` 4000.0 ns (5 members: error,
  optimizer, resource, guard, marker). One real `register` mutation
  through `execute_sync`: 7 statements absolute — BEGIN, SAVEPOINT,
  the username uniqueness SELECT, the INSERT, the re-fetch SELECT,
  RELEASE, COMMIT — of which exactly the SAVEPOINT/RELEASE pair is
  window-attributable (the pipeline's nested atomic; without the
  window its atomic would be outer). Cardinalities do not apply: a
  single top-level mutation field has no parent scaling.
- `review-20260929T122226-d7e102`: `importtime_report.py --rounds 5`
  (`docs/review/temp-tests/schema/performance/importtime.json`):
  69 modules, package cumulative 242624 us, self 29311 us;
  `django_strawberry_framework.schema` self 774 us, cumulative 774
  us — every dependency already paid by earlier package imports, so
  the module adds zero marginal child cost; the 774 us is its own
  body (50 symbols plus the three refusal parses at ~17 us each).
- `review-20260929T122118-db99dd` (exit 1): first `probe_hot_costs`
  revision, probe-side stub bug (`_rollback_for_new_errors` needs a
  bound `_execution_errors`), fixed before any figure was taken;
  superseded, no figure cited from it.

Cells: default measured (both probes bootstrap in-memory SQLite;
every instrument does so by construction). Sharded and pg are
`inapplicable by construction`: every rejection is pure CPU cost
with no alias-selected shape (the one router read,
`utils/write_transaction.py::resolve_write_alias`, costs the same
whichever alias it answers — 167 ns) and no dialect branch (the
SAVEPOINT pair is Django's cross-backend nesting machinery, present
on SQLite and Postgres alike; the absolute list above is the
statement shape, not a per-cell count). The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):

- `django_strawberry_framework/schema.py`
  `84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1` (live, whole, dirty)
- `django_strawberry_framework/utils/truth.py`
  `d5c96bc8d191d3fce0a20140d8e91063bb466ec9` (`is_instance`,
  `is_type`, `is_subclass`, `static_attr`, `describe`, `text`,
  `name` bodies)
- `django_strawberry_framework/utils/private_state.py`
  `b3c45503c3e2f648640b95ecad4d71a8315abb51` (whole)
- `django_strawberry_framework/utils/write_transaction.py`
  `4a83f43dfd8970ade29f4c89a021ae7adf88645b` (module docstring;
  `resolve_write_alias`, `managed_write_transaction`,
  `require_managed_write`, `write_pipeline`, `open_write_pipeline`
  bodies)
- `django_strawberry_framework/utils/policies.py`
  `0a2b7dbad96594b5d668774218809c6a94d136be` (whole)
- `django_strawberry_framework/utils/execution_mode.py`
  `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9` (whole)
- `django_strawberry_framework/extensions/error_policy.py`
  `a1defd394d8eda9b698964030a09efe6914278db` (module head;
  `masking_is_active`, `is_maskable_result`, `schema_error_policy`,
  `mask_execution_result` bodies; extension docstring)
- `django_strawberry_framework/extensions/resource_policy.py`
  `0134d83a9aa2db580b7b8180ded27a3d31b115c7`
  (`DjangoResourcePolicyExtension.__init__`, `_policy`,
  `_resolved_policy`, `on_operation`; `_AdmissionGuard`)
- `django_strawberry_framework/extensions/operation_state.py`
  `d9ed9cc67fea892afa2dd22a33236a52fc061fb1`
  (`_OperationModeMarker` and `DjangoExtensionsRunner` `__init__`;
  `_OperationBoundExtension.__init__`)
- `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a` (schema import lines)
- `django_strawberry_framework/mutations/fields.py`
  `0e4d5ed1c7efbcbb4e70db9162f2ffc85460a699` (marker definition and
  stamp site only)
- `django_strawberry_framework/auth/mutations.py`
  `84183c893fdbf258e112ccf6d1cc66fbc50c513`
  (`register_mutation` factory return only)
- `django_strawberry_framework/resource_policy.py`
  `5b4a80f0e03674b3ae105a03bb21774b602bfa38`
  (`policy_from_info`, `check_deadline` heads only)
- `examples/fakeshop/config/schema.py`
  `303ea2da9df1f8611c02926fd28c59e5ccf9ecac` (whole)
- `examples/fakeshop/apps/accounts/schema.py`
  `dd2e81b3474e7d0ce8c42eb573642addd579af1b` (whole)
- `examples/fakeshop/apps/products/schema.py`
  `04a5afe3dddff9279660ae1370924e03857d57e7` (`CreateCategory` and
  the `Mutation` field table only)
- `examples/fakeshop/apps/products/models.py`
  `02d3ea18e94fc70461decd57c081706f326d9b1b` (`Category` head only)
- `examples/fakeshop/test_query/test_auth_api.py`
  `17fc9ddb7c31c5ae936795fe524f233b3a1e4304` (module docstring, the
  `register` wire shape and variable shapes only)
- `examples/fakeshop/test_query/test_products_api.py`
  `fe78cf9d4862123442611444d44bf81b5187ec6d` (the `createCategory`
  wire shape only)
- `tests/auth/_helpers.py`
  `996762b0db5d527da12f636342a5ba45d86c99ed`
  (`tests/auth/_helpers.py::_session_request` body only)
- `scripts/_bench_common.py`
  `253a39533f35b94f6afb7a1167c2c38489bbbbef` (instrument)
- `scripts/importtime_report.py`
  `15f679c9ad736b71215d8ead0733116f56083cef` (instrument)
- Upstream `strawberry/schema/schema.py` at installed
  strawberry-graphql 0.324.0 (the `get_extensions`,
  `create_extensions_runner`, `execute`, `execute_sync`, `_stream`
  seams; venv content, no git hash)

## Findings

### High

None.

### Medium

None.

### Low

None.

Proof lines: none exist — zero findings, and no sibling record
exists to carry a `## Cross-axis (for Performance)` section.

Looks-for discharge (REVIEW.md "Performance"), each a finding, `none`
with the reason, or a rejection:

- N+1 and per-row queries: none. The target issues no query of its
  own: the window's outer atomic substitutes for the pipeline's own
  outer atomic (BEGIN/COMMIT replace, not add), and the one real
  mutation captured carries exactly 7 statements, of which only the
  SAVEPOINT/RELEASE nesting pair is window-attributable (R2). No
  related-object read in a loop, no `await` per row (every `await`
  is one window hop, the completion value, or the single-transition
  close loop, which iterates only on repeated cancellation), no
  `.filter()` on a prefetched relation (the module builds no
  queryset; 0 inspect ORM markers).
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none — the
  only `len` reads are over the in-memory execution error list
  (125 ns); no queryset exists to count.
- `only()` / `defer()`: none — no projection exists to narrow.
- Unbatched writes: none — the module issues no writes (one
  transaction boundary per mutation field, R2).
- `blog.id` vs `blog_id`: none — no model attribute reads (the one
  model read is the mutation Meta's class-level `model`, R7).
- Repeated `_meta` walks, settings reads, regex compilation,
  schema/type lookups: no `_meta` (the one hit is the local
  `mutation_meta` variable), no `re` import, no schema or type
  registry lookup per request. Settings reads: `DEBUG` per operation
  inside `extensions/error_policy.py::masking_is_active` (R8); the
  `DJANGO_STRAWBERRY_FRAMEWORK` dict at construction only; the
  router list per mutation through the cached Django router (R9).
  Per-field work is two attribute reads plus identity comparisons
  (R6); per-member truth checks (R3).
- `lru_cache` on methods (`B019`): none — no `functools` import, no
  decorator in the module.
- Locks, cache reads, re-parses, extra round trips on a per-request
  path: no locks, no cache backend, no re-parse (the refusal
  documents are parsed once at import precisely so a refused
  operation never lexes request input, R10). Round trips: the
  SAVEPOINT/RELEASE pair per generated mutation (R2) and the two
  executor hops per async mutation (R1); nothing else.
- Import-time cost: none with numbers — 774 us self, cumulative
  equal to self (zero marginal child cost), no settings read at
  import (R10).
- Allocation in the hot loop: no hot loop exists. Per-operation
  allocation is the chain list plus 4 extension objects (R3); the
  per-field unmarked path allocates nothing; the per-member kind
  tuple and the one `{}` on the mutation-field arm are below any
  budget (R11).

## Rejected

- **R1: the async window's private thread per mutation (139.4 us
  machinery, vs 1.4 us executor construction).** The isolation
  mechanism, not an accident: the module docstring's contract (one
  thread nothing outside the window shares, so the atomic's enter,
  the pipeline, and the exit share one connection no other
  operation, socket, or hygiene pass can reach) is what the
  `ThreadPoolExecutor(max_workers=1)` plus fresh
  `ThreadSensitiveContext` key plus cancel-surviving close buys.
  Reopens on a pooled design that preserves per-window exclusivity,
  per-return connection hygiene, the cancel-to-completion close,
  and a nested-window deadlock analysis.
- **R2: the sync window nests the pipeline's atomic, adding the
  SAVEPOINT/RELEASE pair per generated mutation (7 statements
  absolute on the real `register` run) plus the second atomic
  level's ~10 us CPU.** The window must be the OUTER transaction to
  span completion — that is the file's reason to exist — and
  nesting is how Django layers atomics. Eliding the pipeline's nest
  when a managed window is already open would need proof the
  pipeline never rolls back to its own savepoint and never catches
  a database error and keeps issuing queries; that contract
  question belongs to the Mechanics axis (see Handoff), and without
  its answer the pair stays. Reopens on that proof.
- **R3: the per-operation admitted chain (4.0 us factory shape, 2.8
  us empty: 4 constructions, 2 private-state settles, 2 ContextVars,
  3 truth checks per member).** Per-operation state isolation: a
  shared instance would share charge counters and operation state
  between concurrent requests (stated on `_admitted_chain`), and
  the checks are the admission boundary for consumer factories.
  Reopens on a per-operation budget breach with chain-build
  attribution.
- **R4: two membership recalls per operation (the refusal gate plus
  upstream's resolution through the `extensions` property).** The
  gate must run before factories do, and upstream re-reads the
  property internally; distinguishing "accepted empty" from "lost"
  without the second recall would couple this file to upstream's
  directives append. ~0.2–0.3 us each. Reopens if upstream exposes
  resolution input/output separately.
- **R5: copy-per-read policy overhead per operation (~250 ns per
  copy plus its recall: the resource arming and the error teardown
  each read their schema property).** The authority boundary the
  property docstrings state (a resolver-reachable object must be a
  duplicate). `_masked_return` already reads the record directly
  rather than through the property. Reopens only on an authority
  boundary redesign (a maintainer decision).
- **R6: the marker check per executed field (125 ns query parent;
  333–375 ns full walk for a top-level mutation field, identical on
  synthetic and real `register` nodes).** The cheapest correct
  shape: identity comparisons first, the dict lookup and `getattr`
  chain only for top-level mutation fields. A 100-field query pays
  ~13 us against millisecond resolver work. Reopens on a per-field
  budget breach with dispatch attribution.
- **R7: `truth.static_attr` meta read at +417 ns per marked
  mutation vs the double-`getattr` it replaces (83 ns vs 500 ns on
  the real `Register` class; concurrent truthful-reads migration).**
  The read must not run consumer code, and the delta is per
  mutation field, not per row. Reopens if `truth.static_attr` gains
  a fast path for exact-type classes (the delta then shrinks with no
  site change).
- **R8: `settings.DEBUG` read per operation inside the masking gate
  (333 ns inactive / 458 ns active-clean).** Override-honoring by
  contract (the consumers-item precedent): caching DEBUG would pin
  stale answers across setting overrides. Reopens if DEBUG becomes
  immutable at startup, or on a per-operation budget breach with
  gate attribution.
- **R9: `resolve_write_alias` per mutation (83 ns model-less, 167
  ns with a model; Django caches the router list).** Per mutation
  field, sub-micosecond; memoizing per model would need
  settings-change invalidation for nothing a profile could see.
  Reopens on a profile attributing mutation latency to alias
  resolution.
- **R10: 774 us module self time at import (69-module census;
  cumulative equals self, so zero marginal child cost; the three
  refusal parses are ~51 us of it).** Once per process on the
  eager package-root import; the pre-parsed refusal documents are
  deliberate (a refused operation must never lex request input).
  No settings read at import. Reopens if this module leaves the
  package-root import graph.
- **R11: the `{}` on the mutation-field lookup arm and the
  per-call kind tuple in
  `django_strawberry_framework/schema.py::_claimed_authority`.**
  ~50–100 ns each, the loop's natural spelling; hoisting either
  buys nothing a profile could see. Reopens with R6's trigger.

Handoff: Performance review is closed with no findings and eleven
rejections. The judgment calls a verifier could revisit are R1's
139 us per async mutation (read as the isolation mechanism's price;
the pooled alternative needs the deadlock analysis the trigger
names), R2's SAVEPOINT pair (read as inherent nesting; the elision
proof is a Mechanics-owned contract question — whether
`utils/write_transaction.py::open_write_pipeline`'s nested atomic
is ever rolled back to or caught past — flagged here as an open
thread for that axis, not a finding), and R7's +417 ns
(concurrent-work delta on a security read). Everything else was
discharged by absence (no ORM, no regex, no functools, no hot loop,
no per-row window work) or by sub-microsecond measurement against
millisecond-dominated paths. The target was dirty (+17/-19, the
truthful-reads migration) and `tests/test_schema.py` beside it
(+11/-91) — a re-review is owed if concurrent work lands a new
hot-path reader or a new per-operation statement. No defects; no
Routed leads; no cross-axis text placed or owed (sibling records
never appeared). No bench figure moves. Cells unverified: none
beyond the stated inapplicable-by-construction judgments for
sharded/pg. Runs: `review-20260929T122140-bd2290` (hot costs),
`review-20260929T122213-c01c46` (real mutation),
`review-20260929T122226-d7e102` (importtime); superseded
`review-20260929T122118-db99dd` (exit 1, probe-side bug, nothing
cited). Scratch:
`docs/review/temp-tests/schema/performance/probe_hot_costs.py`
(blob `c419c6da`), `.../probe_mutation_window.py` (blob `f383af5c`),
`.../importtime.json`, `.../schema.json`, `.../inspect/`.
Fingerprints: every `git hash-object` in `## Trace`; target live
blob `84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1`.

## Verify performance

Pass 1, address `review/schema.py/verify-performance-1`. No-findings
stands. The pass diff read whole (6 files); the live tree equals its
post-image on all six (fingerprints below match the diff's `index`
post-images, so no concurrent drift sits under this verdict).

Ceiling-inert (judged, not taken on trust). Two static proofs plus
the runs. (1) The installed ceiling, strawberry-graphql 0.324.0,
contains zero occurrences of `_subscribe` in
`strawberry/schema/schema.py` (grep exit 1); a whole-package sweep
matches only the unrelated transport name `handle_subscribe`.
`subscribe` routes through `stream` into `_stream`, so the ceiling
never calls the new override. (2) No production caller names it:
the only `_subscribe` references in the package are the override
itself, its docstrings, and the `super()._subscribe(...)` line
inside its own body, which runs only if something calls the
override; the sole caller anywhere is the new direct-call pin,
which stubs the upstream seam with `create=True`. The override body
mirrors `_stream` (one `truth.is_instance` gate plus the
`resumed_stream` wrap), so even on the floor band where it fires it
replicates the ~333 ns gate the review already discharged, and the
review's re-review trigger ("a new hot-path reader or a new
per-operation statement") is answered here: the new statement is
this item's own, measured by equivalence to the existing gate.

Runs, all at the verify address, default cell, package digest
`sha256:04570f7b...` on every run:

- `review-20260929T130413-373563`: the two resume-binding pins
  (`test_two_streams_interleaved_in_one_task_each_keep_their_own_budget`,
  `test_a_paused_stream_leaves_no_binding_in_the_task_that_drove_it`)
  unmodified — 2 passed.
- `review-20260929T130418-9c2cac`: full
  `tests/extensions/test_operation_state.py` — 55 passed, including
  the 11 un-skipped subscribe-only rows.
- `review-20260929T130424-e53a0b`: `tests/test_schema.py -k "stream
  or subscribe"` — 10 passed, including the existing `_stream`
  foreign-runner row and the new `_subscribe` pin.

No bench row moves; no re-measurement run, per the mech Handoff's
ceiling-inert note, which this pass obeys: code the ceiling never
calls moves no warm/cold figure, and the one-def import delta sits
inside noise under R10's trigger (module still on the package-root
import graph). R1-R11 stand, each judged against the diff rather
than carried: no window, chain, recall, copy, marker, alias,
settings, or refusal line changed — the only executable production
hunk is the uncalled override, everything else is docstring and
comment prose, and the test/live hunks are un-skips, one new pin,
and prose.

Disturbance check (prose vs Performance claims): C2's restated
`_stream` sentence keeps the review's path-class row true (the
resume gate still fires once per streamed operation at the
ceiling; the floor band now has its twin). M2's flag recount is
about `_SchemaEnforcement` fields, not the "2 private-state
settles" R3 counts. M3's refusal-enumeration fix touches no cost
figure (refusal stays cold/exceptional). M1/M4-M8/L1-L5 are
version boundaries, counts, censuses, agency, and mood — none
cited by any Performance number. The `Schema._subscribe` mention
in `tests/test_routers.py:475` is pre-existing prose in a file
this pass never touches: out of scope, no disturbance.

Cells: default run (all three runs above). Sharded and pg are
`inapplicable by construction`, judged afresh: the override wraps
a stream source and reaches no database, alias, or dialect
decision — the same reason the review record states, still true
of the changed code.

Fingerprints (`git hash-object`, live, equal to the pass-1
post-image): `django_strawberry_framework/schema.py`
`f4e807e9e64c1a38e03942705299f5636ba2dd35`;
`tests/test_schema.py`
`83877a6a2b1ecd3ac71be77393f952b6f150edea`;
`tests/extensions/test_operation_state.py`
`6ce414b6d74b8988aeb3b1d74e7cb49913e52585`;
`tests/mutations/test_write_transaction.py`
`96416deb48a6dfccb5e5895817bf602d5bc0ce61`;
`examples/fakeshop/test_query/test_extension_isolation_api.py`
`61d57babbdd9c0c7304d39d464b2c1f7d7d1f545`;
`examples/fakeshop/test_query/test_mutation_atomicity.py`
`69d7cc4d2fccd6761fde2ed80d78a6f99188b136`.

Handoff: Performance verify is closed. Nothing was edited beyond
this section and the scratch dir below; no production or test
file touched. No new defects, no routed leads, no open threads.
Scratch: `docs/review/temp-tests/schema/verify-performance-1/`
(housing only; the evidence lives in the three workspace run
logs). The new-floor-gate cost equivalence argued above is mine;
a future floor-band bench could pin it, but no finding turns on
it.

Status: verified
