# Review · Mechanics: `django_strawberry_framework/schema.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5ef09ed4565b774a3f9cda2f473514732bf12064

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target and no Routed lead on this item),
`docs/review/rev-schema.md` (skeleton: `Status: reviewing`, blank
Path class). Sibling axis records: `rev-schema.performance.md` read
whole, incl. its Handoff (no-findings; eleven rejections; open
thread on the pipeline atomic elision answered in my Handoff; no
`## Cross-axis (for Mechanics)` section, so no foreign Proof owed);
`rev-schema.comments.md` did not exist at close. `rev-schema.md`
carries no Worker-2 sections yet.

Target read whole, all 1408 lines, as it stands: blob
`84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1` (same bytes the
Performance record fingerprinted). Dirty vs HEAD (`+17/-19`,
concurrent truthful-reads migration) — reviewed as it stands per
the dispatch, no hunk attributed here.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/schema/mechanics/inspect/` (json
`docs/review/temp-tests/schema/mechanics/schema.json`): 50 symbols,
0 Django/ORM markers, 3 hot entry points (all three the refusal
hooks — exceptional path), 6 import-time calls. Leads only.

Contracts traced by hand: `docs/README.md` (mutation-transaction
envelope, production error policy, enforcement ownership, refusal
shape), `docs/GLOSSARY.md` (per-operation extension isolation,
`DjangoResourcePolicyExtension` bullet vs body, `ErrorPolicy`
frozenness — the last already in the plan's `## Decisions`, not
re-raised), `GOAL.md` "Trust boundary", spec-047 plus its
rationale companion (the `_subscribe`/`_stream` seam move), the
owner modules (`extensions/operation_state.py`,
`extensions/resource_policy.py`,
`extensions/error_policy.py`, `mutations/fields.py`,
`utils/write_transaction.py`, `consumers.py`, `views.py`), the
upstream bodies at both ends of the supported range (wheel audit,
table below), and the pinning tests (`tests/test_schema.py`,
`tests/extensions/test_operation_state.py`,
`tests/mutations/test_write_transaction.py`,
`tests/test_error_policy.py`).

Upstream wheel audit (wheels under
`docs/review/temp-tests/schema/mechanics/upstream/`):

| Wheel | Errors shape | Stream seam |
|---|---|---|
| graphql-core 3.2.8 (installed) | `errors` list | n/a |
| graphql-core 3.2.9 | `errors` list; no `collected_errors` | n/a |
| graphql-core 3.2.10 | `CollectedErrors`; `collected_errors` only | n/a |
| strawberry-graphql 0.316.0 (floor) | n/a | `subscribe` -> `_subscribe`; no `stream`/`_stream` |
| strawberry-graphql 0.319.0 | n/a | `subscribe`/`stream` -> `_stream`; no `_subscribe` |
| strawberry-graphql 0.324.0 (installed) | n/a | `subscribe` -> `stream` -> `_stream`; no `_subscribe` |

0.317/0.318 unaudited (named in F1 for the fix to close).
`get_extensions(sync=...)` resolution
(`ext if isinstance(ext, SchemaExtension) else ext()`),
`create_extensions_runner(execution_context, extensions)`, the
`sync=True`-only-from-`execute_sync` call sites, the
`strawberry-definition` backref, `base_resolver.wrapped_func`, and
every `ExecutionContext` attribute `_refuse_operation_document`
touches (`allowed_operations`, `graphql_document`,
`validation_rules`, `pre_execution_errors`,
`_provided_operation_name` + the `operation_name` fallback) are
verified identical on floor 0.316.0 and ceiling 0.324.0. asgiref
seams (`AsyncToSync.executors`,
`SyncToAsync.thread_sensitive_context`,
`SyncToAsync.context_to_thread_executor`, caller-first selection
order) verified present in installed asgiref 3.11.1.

Probes, address `review/schema.py/mechanics`, default cell:

- `review-20260929T122511-ac2414` (exit 0): control — the two
  subscribe-driven isolation nodes pass unmodified, 2 passed.
- `review-20260929T122646-e1ade1` (exit 1): resume binding
  neutralized (`resumed_stream` -> identity) — both fail on the
  pinned assertions (`assert 7 is None` at
  `tests/extensions/test_operation_state.py:1227`, `assert 3 is
  None` at `:1255`), 2 failed.
- `review-20260929T122559-3bb63b` (exit 0): finalized probe
  (`pytest.raises(AssertionError)` around each) — 2 passed.
  Superseded exploratory `review-20260929T122519-1ac79a` (exit 1,
  same breakage, nothing cited from it).

A floor-band pytest is not runnable through `workspace.py` (every
run re-syncs the copy venv to the ceiling lockfile via
`uv run --frozen`), so the floor leg is proven by equivalence, not
by a floor interpreter: neutralizing resume binding at the ceiling
reproduces the floor's binding shape exactly for every read the
two pinned tests make (resolver reads during frame production see
the leaked `operation()` scope in both; between-frame task reads
see the leaked budget var in both — the ceiling's extra
`on_stream_result` rebinds and resets around result handling only,
which neither test reads inside of). The static half (the floor
never invokes resume binding: no `_stream` in 0.316.0;
`django_strawberry_framework/schema.py::DjangoSchema._stream` the
sole production caller of
`django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner.resumed_stream`)
closes the loop.

Fingerprints (`git hash-object` of every tracked file whose body
was read; findings list no further files):

- `django_strawberry_framework/schema.py`
  `84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1` (live, whole, dirty)
- `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a` (schema import +
  `__all__` lines)
- `django_strawberry_framework/extensions/operation_state.py`
  `d9ed9cc67fea892afa2dd22a33236a52fc061fb1` (runner, resume,
  registrar, `_binds_operation_state` deferred import)
- `django_strawberry_framework/extensions/resource_policy.py`
  `0134d83a9aa2db580b7b8180ded27a3d31b115c7`
  (`DjangoResourcePolicyExtension.__init__`, `_policy`,
  `_resolved_policy`, budget arming + `rebind_on_resume` call)
- `django_strawberry_framework/extensions/error_policy.py`
  `a1defd394d8eda9b698964030a09efe6914278db` (no policy-carrying
  `__init__`; `_process_result` in-place adoption;
  `on_operation` streamed caveat)
- `django_strawberry_framework/mutations/fields.py`
  `0e4d5ed1c7efbcbb4e70db9162f2ffc85460a699` (marker definition,
  stamp site, import direction)
- `django_strawberry_framework/utils/write_transaction.py`
  `4a83f43dfd8970ade29f4c89a021ae7adf88645b` (alias + managed
  transaction ownership; import direction)
- `django_strawberry_framework/utils/policies.py`
  `0a2b7dbad96594b5d668774218809c6a94d136be`
- `django_strawberry_framework/utils/private_state.py`
  `b3c45503c3e2f648640b95ecad4d71a8315abb51`
- `django_strawberry_framework/utils/execution_mode.py`
  `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9`
- `django_strawberry_framework/utils/truth.py`
  `d5c96bc8d191d3fce0a20140d8e91063bb466ec9`
- `django_strawberry_framework/error_policy.py`
  `57a0bed1ba730f8e4c879d852274eac39f12b` (resolution ownership)
- `django_strawberry_framework/resource_policy.py`
  `5b4a80f0e03674b3ae105a03bb21774b602bfa38` (resolution ownership)
- `django_strawberry_framework/consumers.py`
  `0791c04a6c7b2619562f33dc707b002cde718c6b` (two-public-names
  posture, per-event masking seam, `subscribe`/`stream` reads)
- `django_strawberry_framework/views.py`
  `48ee582ecdba41d49beb2434f2a9e0af992d39d4` (no streamed seam)
- `tests/test_schema.py`
  `3676f7e8a9370966c3159264825857a599cdf085`
- `tests/extensions/test_operation_state.py`
  `7509c1ccaa1c56c50be2ca3bc4337b75bcca90ce`
- `tests/mutations/test_write_transaction.py`
  `689e31f47ae0dc010e67386e4a076b782afac5ff`
- `tests/test_error_policy.py`
  `9a72cdb83d4739be4018a3c58d0bf2736b63f569` (`_masked_return`
  rows only)
- `tests/test_registry.py`
  `8bd9a8693a48c489d3b7029b2a0e4a86b86502e7` (untouched
  sibling, read for the `_clear_helper` census only)
- `docs/README.md`
  `30978c34f63a833ffcc0fa11c80b773d241921be`
- `docs/GLOSSARY.md`
  `3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`
- `docs/SPECS/spec-047-resource_policy-0_0_14.md`
  `844eab5321d9107837a63c01998779d920be6d1e`
- `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`
  `7f321ce6c677f4fb580cc028d19f11d085aa1e6b`
- `GOAL.md` `7dfbef5c784519d5f95311aaeb8c6766ee966b02`
  ("Trust boundary" only)
- `docs/review/review-0_0_15.md`
  `648170305d979962d8d43217a27d85b5a582e6c7`
- `docs/review/rev-schema.md`
  `088e6c8e390de80b667542286e4f9189637e6801`
- `docs/review/rev-schema.performance.md`
  `6db9758c68fe50e705fa6a58c4171148d8150c22` (whole, incl.
  Handoff; no Cross-axis section present)
- Upstream (scratch downloads, sha256 of the audited file):
  `gc329/graphql/execution/execute.py`
  `17f901b3d2d0b8baabf593d2771d2001e14bd26fe453e9bf9e82d680fd6bd22b`,
  `gc3210/graphql/execution/execute.py`
  `209f1f912133d659795f2348e6752a786f4152dfffeed008d999528fdff2481f`,
  `sb316/strawberry/schema/schema.py`
  `9263a5ae869a15814589ca931eb4b29b7ccc5f136cb6ed0f7bbe9dfe893d4714`,
  `sb319/strawberry/schema/schema.py`
  `b251729cc71bae3e9c7fa74d066f886994dd67d6d1650b51755a593d3bdbcc85`

No `check_citations.py --cited-by` run: the recommendation adds a
method and renames nothing.

## Findings

### High

#### F1: streamed operations on the strawberry floor band run with no resume binding

- **Observation:** `django_strawberry_framework/schema.py::DjangoSchema._stream`
  overrides a private upstream method that exists only at
  strawberry-graphql >= 0.319. On the supported floor band
  (0.316–0.318) subscriptions run through upstream `_subscribe`,
  which nothing wraps, so no `_ResumedStream` binding covers any
  frame: whole-operation state armed during frame one (the
  resource budget, via
  `django_strawberry_framework/extensions/operation_state.py::OperationState.rebind_on_resume`)
  is never rebound per drive, and the driving task keeps the
  operation's bindings between frames.
- **Defect:** the package's stated per-operation isolation fails
  on a supported configuration. The glossary isolation anchor
  promises every resumption bound and the driving task answering
  between frames "from its enclosing operation, or from nothing",
  with no version qualifier — but on the floor band two streams
  interleaved in one task confuse budgets and a paused stream
  leaves its ceiling in the driving task.
- **Evidence:** (1) Wheel audit: 0.316.0 routes
  `subscribe` -> `_subscribe` and has no `stream`/`_stream`;
  0.319.0 and 0.324.0 route through `_stream` and have no
  `_subscribe`; `DjangoSchema._stream` at `schema.py:1215` is the
  sole production caller of `resumed_stream` (verified by
  whole-tree grep: the only other references are the definition
  and tests). The floor therefore never invokes resume binding.
  (2) Behavioral probe at the ceiling, neutralizing
  `resumed_stream` to the identity — the exact floor binding
  shape for every read the pinned tests make (see Trace for the
  equivalence argument): control 2 passed
  (`review-20260929T122511-ac2414`); neutralized 2 failed on the
  pinned assertions, `assert 7 is None` at
  `tests/extensions/test_operation_state.py:1227` and
  `assert 3 is None` at `:1255`
  (`review-20260929T122646-e1ade1`, exit 1); finalized
  `pytest.raises(AssertionError)` form 2 passed
  (`review-20260929T122559-3bb63b`). Reach assertion: the two
  failing nodes drive public `schema.subscribe` only (no
  `Schema.stream` use), so the identical breakage is reachable on
  the floor band through supported public API. Positive control:
  the unmodified nodes pass in the same copy.
- **Impact:** cross-operation budget/state confusion
  (over/under-enforcement across operations sharing a driving
  task) plus driving-task hygiene violation, on strawberry
  0.316–0.318. Narrowed: single-stream-per-task drives deliver
  correctly (the leaked `operation()` scope carries the
  operation's own state; the probe's first-frame assertions pass
  pre-breakage), so the common transport shape is unaffected to
  the extent transports drive one stream per task — package
  router tasking is unverified (open thread in Handoff). The
  trigger needs multi-stream driving, cross-task drives, or
  between-frame state reads by a direct `schema.subscribe`
  consumer — feasible project code under supported public API
  (GOAL.md "Trust boundary"), and exactly the shapes the pinned
  tests exist to cover.
- **Severity:** High. Consequence class is data isolation /
  public-contract failure (an operation answered by another
  operation's budget). Factors narrowing urgency, not class: the
  floor band only (0.316–0.318; 0.317/0.318 seam presence
  unaudited, presumed `_subscribe`); single-stream drives
  unaffected; the ceiling (all currently pinned rows) correct.
- **Recommendation:** bind the floor seam the same way.
  Override `_subscribe` beside `_stream`, mirroring its body
  (wrap `super()._subscribe(...)` in `resumed_stream` when the
  runner is a `DjangoExtensionsRunner`, else pass through):
  each override fires where its upstream exists and is dead
  where absent, which is the `consumers.py` two-public-names
  posture applied to the private seam pair. Owner:
  `django_strawberry_framework/schema.py::DjangoSchema`
  (the override site). Worker-2 also: (a) audits the 0.317 and
  0.318 wheels for `_stream` vs `_subscribe` presence and
  records the version map in `## Implementation (Worker-2)`;
  (b) un-skips the subscribe-only isolation rows (at least the
  two Proof nodes; every further `_SKIP_WITHOUT_STREAM` row
  whose body uses no `stream`) so the CI floor cell pins the
  fix; rows genuinely needing `Schema.stream` stay skipped.
  The alternative (version-qualifying the glossary isolation
  anchor to >= 0.319 instead of fixing) is a maintainer
  decision, not a Worker-2 call — the contract as written
  covers the floor.
- **Must not change:** ceiling behavior (every existing
  resume/stream test passes unmodified); public API (no new
  public names — `_subscribe` stays private like `_stream`);
  chain shapes; the skip on rows that genuinely need
  `Schema.stream`.
- **Proof:** at `review/schema.py/verify-mechanics-<n>`:
  (1) new direct-call test
  `test_a_subscribe_whose_runner_is_not_the_packages_is_handed_back_untouched`
  in tests/test_schema.py (calls the `_subscribe` override
  directly with a package runner and a foreign runner;
  asserts `_ResumedStream` for the first, identity for the
  second — mirroring the `_stream` half-row) — plain-text
  name, Worker-2 creates it: run that node with
  `uv run python scripts/workspace.py run review/schema.py/verify-mechanics-<n> -- pytest`
  plus `--no-cov -n0`; must report `1 passed`. Mandatory
  anyway: the override body is uncovered at the ceiling
  otherwise, and the coverage gate is 100. (2) ceiling
  regression, same address:
  `uv run python scripts/workspace.py run review/schema.py/verify-mechanics-<n> -- pytest tests/extensions/test_operation_state.py::test_two_streams_interleaved_in_one_task_each_keep_their_own_budget tests/extensions/test_operation_state.py::test_a_paused_stream_leaves_no_binding_in_the_task_that_drove_it --no-cov -n0`
  must report `2 passed`. (3) static, shared tree:
  `grep -c "def _subscribe" django_strawberry_framework/schema.py`
  prints `1`. Failability: reverting the `_subscribe`
  override fails exactly command (1)'s row (prove manifest
  names that node; any further failing row must be justified
  as the override's own coverage).
- **Freshness:** Trace fingerprints cover every file read; no
  further files.
- **Owner + contract source:** owner is
  `django_strawberry_framework/schema.py::DjangoSchema`
  (it owns the streamed-operation seam); contract sources are
  the glossary per-operation-extension-isolation anchor
  (unqualified: every resumption bound, driving task clean
  between frames) and the two pinned subscribe-driven tests
  named above.

### Medium

None.

### Low

None.

Proof lines: F1's three lines above (two workspace pytest
invocations at the verify address plus one shared-tree static
grep). No sibling `## Cross-axis (for Mechanics)` section exists
(the Performance record places none; the Comments record does not
exist), so no foreign Proof is owed.

Looks-for discharge (REVIEW.md "Mechanics"), each a finding,
`none` with the reason, or a rejection with its trigger (reasons
here; full triggers under `## Rejected`):

- Rule enforced at a caller instead of its owner: none. The
  mutation marker is owned by `mutations/fields.py` (schema only
  reads it); the write alias and managed transaction by
  `utils/write_transaction.py`; both policies by their modules
  (schema resolves once at construction, the documented seam);
  masking by `extensions/error_policy.py` (the return seam
  composes its four gates/helpers by name, never restating —
  independently corroborated by concurrent DRY rule
  `subscription-per-event-error-masking`, Status: verified).
- Policy in an adapter, mechanism in a policy layer: none.
  Schema.py implements no policy logic: bounds live in
  `resource_policy.py`, masking in `extensions/error_policy.py`,
  the wire codes and chain order at the refusing/composing
  layer that owns them.
- Decision vs contract sources: F1 (floor gap vs the
  unqualified isolation contract) plus two prose-side items
  (C1 under Cross-axis; the glossary "as a CLASS" lead routed
  in my report — body correct, index bullet stale, fix is a
  glossary-DB edit plus render outside the item fence).
  Verified matches, no finding: the README mutation envelope
  (completion-spanning window, private-thread async window,
  closed-connection refusal, plain-`strawberry.Schema` refusal
  owned by the pipeline, serial independence,
  `execution_context_class=` escape); the README error-policy
  section (first-in-chain, hook-escape seam on the schema,
  per-event router coverage); the refusal code/chain/document
  rules (raw-text pre-parse scan is what makes the
  `RESOURCE_LIMIT_EXCEEDED`-before-parse claim true under
  document substitution); `_operation_mode`'s
  sync-flag claim (call sites verified identical on floor and
  ceiling); the extension-entry resolution mirror (verified
  identical on floor and ceiling bodies).
- Branch no real path reaches: none. Every defensive branch is
  pinned by a named real-path or hostile-seam test:
  closed-window refusal (sync + async nodes),
  blocked-caller nesting, repeated + mid-enter cancellation,
  hostile error containers (sync + async, rollback witnessed by
  probe-row absence), the refusal hooks, the one-shot policy
  snapshot, the `_stream` foreign-runner passthrough,
  `_masked_return` pass-through identity + degrade arms,
  `_marked_mutation_class` early-Nones,
  double-declaration/double-settle refusals. The two
  judgment calls are R5 (pinned `[]` fallback) and R7
  (deliberate fail-safe).
- Mode flag standing in for a named adapter: none. `sync: bool`
  is upstream's `get_extensions` signature, converted to the
  `OperationMode` adapter at the boundary by
  `django_strawberry_framework/schema.py::_operation_mode`;
  no other mode flag in the module.
- State owned in two places: none. The enforcement record vs
  accepted-entries split is by lifetime (policies point at
  nothing; entries point back at the schema), each direction
  documented where it is held.
- Dependency pointing the wrong way / `TYPE_CHECKING` hiding a
  cycle: none. All runtime imports point down or sideways
  (policies, extensions, utils, the mutations marker); no
  `TYPE_CHECKING` block exists; the one upward edge
  (`extensions/operation_state.py::_binds_operation_state`'s
  function-local schema import) is documented at the site as
  the deferred direction (R14).
- `django.conf.settings` read at import: none. No settings
  import; the one "settings" hit is a docstring mention of
  `settings.DEBUG`; import-time work is the two private-state
  holders, the fallback record, and three small parses.
- `__all__` disagreeing with the public surface: R10 (absent,
  consistent with six siblings; root `__all__` covers all
  three public names).
- Two sites implementing one rule: R1, R2, R3, R4, R8 — each
  challenged, each kept separate for a stated reason.
- Sync/async twins drifted: R9 (shared `_masked_return` /
  `_exit_window`; asymmetries justified) and R16 (symmetric
  exception-path rule).
- Guard one flavor has and a sibling lacks: F1 for version
  flavors (floor vs ceiling streaming). Masking flavors
  discharged with no finding: `execute`/`execute_sync` mask at
  return, transports mask per frame at the result source, the
  teardown adopts in place at close onto the same object
  upstream returns (`context.result = result` verified), and
  direct in-process pre-close reads are inside the trust
  boundary (R11). Error-container flavors discharged: both
  graphql-core shapes pinned (C1 is the version number in
  prose only; probe order is safe — no audited release
  carries both attributes).

## Rejected

- **R1: the enforcement-kind tuples in
  `django_strawberry_framework/schema.py::_declared_authority`
  and
  `django_strawberry_framework/schema.py::_claimed_authority`.**
  Change challenge ("add a third authority kind" / "rename a
  kind string") counts 2. Kept: construction-time
  classification (exact type, subclass refused loudly, factory
  opaque) and operation-time classification (resolved member,
  subclass refused by failing the operation closed) are
  different contracts over different inputs; a shared constant
  would couple a loud construction error to a fail-closed
  operation refusal. Trigger: a third authority kind, or a
  rename landing in one message and missed in the other.
- **R2: authority order in
  `django_strawberry_framework/schema.py::_refused_chain` and
  `django_strawberry_framework/schema.py::_admitted_chain`.**
  Both place error-policy first and resource-policy late, but
  the member sets differ (no consumers, no guard on the
  refused chain) and each order carries its own documented
  contract (refusal last-word vs spec-048 Decision 10).
  Trigger: a third chain shape, or an order change correct in
  one chain and wrong in the other.
- **R3: the triple refusal restatement (`on_parse` setup +
  post-yield, `on_validate` setup).** Each statement is
  load-bearing at its own seam (pre-parse publish,
  post-parse restate, pre-validate restate); a helper would
  still need three calls at the same three sites. Trigger: a
  fourth seam needing the same statement — then extract it.
- **R4:
  `django_strawberry_framework/schema.py::_is_extension` as a
  one-line wrapper over `truth.is_instance`.** Delegates,
  does not duplicate: the rule has one owner (`utils/truth.py`)
  and the wrapper carries only the local why. Trigger: logic
  added to the wrapper beyond delegation.
- **R5:
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execution_errors`
  returning `[]` for a shape-less container.** Deliberate and
  pinned (`tests/test_schema.py`
  `test_execution_errors_fallback`); every real path carries
  one audited shape (3.2.8/3.2.9 `errors`, 3.2.10
  `collected_errors.errors`), and the fail-closed docstring
  scopes itself precisely to *raising* access, which does
  mark rollback and re-raise (both twins pinned with
  probe-row rollback witnesses). Trigger: a supported
  graphql-core whose context carries neither attribute —
  then the default must become a raise.
- **R6: `handle.close()` outside the `DatabaseError`
  suppress in
  `django_strawberry_framework/schema.py::_close_thread_connections`.**
  The docstring's `DatabaseError` sentence matches the
  suppress exactly (`connection.close()` is the Django-level
  close that raises it; a raw DBAPI handle raises non-Django
  errors, a different class), and no supported backend
  raises on handle close (sqlite/postgres closes are
  infallible in practice; the handle dance itself is the
  in-memory-sqlite path where Django skips its own close).
  Broadening suppression would hide lifecycle bugs.
  Trigger: a supported backend whose handle close raises
  during teardown.
- **R7: the `_FALLBACK_ENFORCEMENT` arm of
  `django_strawberry_framework/schema.py::_enforcement`.**
  Deliberate fail-safe for pathological construction
  (subclass skipping `super().__init__`, object whose
  construction raised before settling); cost is one ternary,
  and removal would convert a package-defaults degradation
  into a crash. Trigger: evidence the arm fires on any real
  construction path — then it needs a pinning test, not
  removal.
- **R8: masking composed at three seams (teardown,
  per-event, return).** One rule, single owner
  (`extensions/error_policy.py::mask_execution_result`),
  three composing sites, none restating the classifier —
  the DRY change challenge counts one authoritative
  definition. Trigger: a fourth masking site, or a site
  restating the classifier.
- **R9: the `execute`/`execute_sync` and sync/async-window
  twins.** Both pairs share their rule (`_masked_return`;
  `_exit_window` with the rollback + closed-connection
  rules); the asymmetries (async `entered` flag,
  caller-thread adoption, cancel-surviving close) are the
  execution model's, each pinned (mid-enter cancellation,
  blocked-caller nesting, twice-cancelled window).
  Trigger: a failure-rule change landing in one twin only.
- **R10: no module `__all__` in schema.py.** Consistent with
  six siblings (`connection`, `consumers`, `keyset`,
  `permissions`, `registry`, `conf` carry none); the package
  root's `__all__` covers all three public names
  (`DjangoSchema`, `DjangoMutationExecutionContext`,
  `SCHEMA_CONFIGURATION_ERROR_CODE`). Trigger: a public
  name exported from schema.py but absent from the root
  `__all__`.
- **R11: direct `schema.stream` frames readable unmasked
  between yield and close.** Every wire flavor masks
  pre-render (views via `_masked_return`; the ASGI router
  via the per-frame result source); the teardown adopts the
  masked fields in place onto the same object upstream
  returns, so post-close reads are masked; pre-close direct
  reads are in-process trusted readers under GOAL.md "Trust
  boundary". Trigger: a wire transport rendering streamed
  frames before close without the result-source wrapper.
- **R12: exact error-policy entries silently dropped by
  `django_strawberry_framework/schema.py::_consumer_extension_entries`.**
  Nothing is dropped:
  `extensions/error_policy.py::DjangoErrorPolicyExtension`
  takes no policy (no `__init__` policy parameter; its
  `_policy()` reads the schema), so an exact entry declares
  nothing — unlike a resource entry, which is folded.
  Trigger: a policy parameter added to the error extension.
- **R13:
  `django_strawberry_framework/schema.py::_entry_resource_policy`
  reading `entry._policy` across modules.** The owning
  module documents that property as DjangoSchema's read
  seam ("this property is how it reads it"), served from
  its private record as a copy. Trigger: that property's
  contract changing.
- **R14: the deferred `from ..schema import DjangoSchema`
  in `extensions/operation_state.py::_binds_operation_state`.**
  Documented direction (schema builds on operation_state),
  function-local, no cycle; the module has no
  `TYPE_CHECKING` block. Trigger: a second deferred edge or
  a `TYPE_CHECKING`-hidden cycle.
- **R15:
  `django_strawberry_framework/schema.py::_is_resolvable_extension_entry`
  mirroring upstream's resolution expression.** Verified
  identical on the floor (0.316.0) and ceiling (0.324.0)
  upstream bodies, and quoted verbatim at the site; drift
  fails loud (construction accepts what the first operation
  rejects deep in the engine — the setter exists to pull
  exactly that failure to startup). Trigger: an upstream
  release changing the resolution expression.
- **R16: the exception paths of both mutation-window twins
  skipping the closed-connection rule.** An exception
  through `atomic.__exit__` already forces rollback, so the
  committed-without-write hazard that rule guards cannot
  arise there; symmetric in both twins. Trigger: an
  exception path that can commit.

## Cross-axis (for Comments)

### C1: the graphql-core version that moved the error list is 3.2.10, not 3.2.9

- **Observation:** the docstring of
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execution_errors`
  ("graphql-core < 3.2.9 ... 3.2.9 replaced that attribute")
  and the docstring of
  `test_execution_errors_reads_both_graphql_core_error_shapes`
  in `tests/mutations/test_write_transaction.py` ("graphql-core
  3.2.9 errors relocation ... 3.2.9 moved it") both name the
  wrong release.
- **Evidence:** wheel audit — 3.2.9's `ExecutionContext`
  carries only the plain `errors` list with `self.errors.append`
  (no `collected_errors` attribute anywhere in the module);
  3.2.10 introduces `CollectedErrors` with `collected_errors`
  only (sha256 fingerprints in Trace). Corroborated by
  newrelic-python-agent 13.2.0 release notes ("graphql-core
  v3.2.10 renamed the `errors` attribute to `collected_errors`")
  and the v3.2.9...v3.2.10 upstream compare. The in-repo error
  originates in commit `bec431d` ("graphql-core 3.2.9 moved
  ..."), found via web search, not via repo history mining.
- **Impact:** a wrong version in a load-bearing audit claim:
  a maintainer checking "which shape does my 3.2.9 have"
  finds the old shape and must distrust the docstring. Body
  unaffected — probe order is safe on every audited release
  (none carries both attributes), and `CollectedErrors.errors`
  is a live-list property whose length never shrinks, so the
  before/after rollback comparison stays valid on 3.2.10
  (a first error at a non-nulled position always grows it;
  ignored positions are duplicates under an already-collected
  ancestor).
- **Severity:** Low (proposed; Comments judges). Factual error
  in a private-method docstring plus a test docstring; no wire
  or behavior impact.
- **Recommendation:** restate both docstrings as 3.2.10 (owner:
  the Comments pass; the two docstring sites only — no code).
- **Must not change:** n/a (prose only).
- **Proof:** static, shared tree:
  `grep -n "3\.2\.9" django_strawberry_framework/schema.py tests/mutations/test_write_transaction.py`
  exits 1 (no matches; those files name the number nowhere
  else). Grade requirement: both docstrings read 3.2.10 and
  grade true against the audited wheels.
- **Freshness:** Trace fingerprints cover both files.

### C2: the `_stream` coverage claim after the F1 disposition

- **Observation:** the docstring of
  `django_strawberry_framework/schema.py::DjangoSchema._stream`
  claims "one override covers every streamed operation on
  every transport". True at the ceiling; false on the floor
  band, where `subscribe` routes through `_subscribe` past
  this override (F1).
- **Evidence:** F1's wheel audit (0.316.0 has no `_stream`;
  0.319.0+ has no `_subscribe`).
- **Impact:** the docstring misstates the override set a
  reader must hold to reason about streamed binding on the
  supported range.
- **Severity:** Low (proposed; Comments judges). Private-method
  docstring; rewritten as part of the F1 fix in any case.
- **Recommendation:** after Worker-2 lands F1, restate as the
  shipped override set (two overrides, each firing where its
  upstream exists) — or, if the maintainer takes the qualify
  alternative, as the version-gated truth. Owner: the Comments
  pass, conditioned on the F1 disposition.
- **Must not change:** n/a (prose only).
- **Proof:** static, shared tree:
  `grep -n "one override covers every streamed operation" django_strawberry_framework/schema.py`
  exits 1. Grade requirement: the coverage sentence grades
  true against the shipped override set on every supported
  band — the Comments verifier judges against the F1
  disposition recorded in `## Implementation (Worker-2)`.
- **Freshness:** Trace fingerprints cover the file.

Handoff: Mechanics review is closed with one High defect (F1,
floor streaming bypasses resume binding — contract row,
feasible shape, and reaching input all named), sixteen
rejections, and two Comments cross-axis items (C1 version
number with wheel proof; C2 conditioned on the F1
disposition). Beyond the record's trace I also read the
concurrent DRY rule `subscription-per-event-error-masking`
(Status: verified, untracked) to corroborate R8 — my verdict
is from my own trace; the DRY record only confirms it — and
the Performance record's Handoff thread on the pipeline
atomic elision (whether
`utils/write_transaction.py::open_write_pipeline`'s nested
atomic is ever rolled back to or caught past): seen, and left
for its owner — the nested atomic belongs to
write_transaction.py, outside this item's fence, and no
schema.py action follows from it; Worker-0 may home it on a
write_transaction/utils item if wanted. Open threads for the
next passes: (1) package router tasking is unverified —
whether any bundled transport multiplexes streams onto one
task bounds F1's wire exposure (my Impact scopes to what I
proved: single-stream-per-task delivers correctly); (2)
strawberry 0.317/0.318 seam presence is unaudited (F1
prescribes the audit in-implementation); (3) the F1 fix is
ceiling-inert by construction (an override of a method the
ceiling upstream never calls), so the Performance verifier
owes no re-measurement beyond the existing resume tests
passing — noted here, not placed as a cross-axis finding,
since it is a no-impact statement. The target was dirty
(+17/-19, same blob the Performance record read); a
re-review is owed if concurrent work lands a new enforcement
seam or a new streamed path. No bench figure moves (no
Performance finding to move one). Cells: sharded/pg
inapplicable by construction for F1's evidence (the seam
opens no database; all three probes carry no `django_db`
marker and ran in the default cell) — the verifier judges;
C1/C2 are static prose, no cells.

## Verify mechanics

Pass 1, address `review/schema.py/verify-mechanics-1`
(copy slot-4; package digest
`sha256:04570f7beca8ade0e4c6aee841d76d8693634e5c402a0f2cd952806360778364`
on every run; python 3.14.2, django 6.1, strawberry-graphql
0.324.0, default cell). Live fingerprints:
`schema.py` f4e807e9, `tests/test_schema.py` 83877a6a,
`tests/extensions/test_operation_state.py` 6ce414b6,
`tests/mutations/test_write_transaction.py` 96416deb,
`test_extension_isolation_api.py` 61d57bab,
`test_mutation_atomicity.py` 69d7cc4d — each matches the
pass-1 diff's `+++` blob, so the live tree carries the
implementation unclobbered.

1. Proof (1) new direct-call pin — pass.
   `review-20260929T130458-bd5a90`:
   `tests/test_schema.py::test_a_subscribe_whose_runner_is_not_the_packages_is_handed_back_untouched`
   `1 passed`. The node asserts `_ResumedStream` for the
   package runner and identity for the foreign runner,
   mirroring the `_stream` half-row as prescribed.
2. Proof (2) ceiling isolation regression — pass.
   `review-20260929T130506-02a481`: the two Proof nodes
   `2 passed`.
3. Proof (3) static — pass.
   `review-20260929T130512-3e6cff`:
   `grep -c "def _subscribe"
   django_strawberry_framework/schema.py` prints `1` in
   the copy; shared tree also prints `1`.
4. Failability — pass. `_subscribe` removed in the copy
   only (script under scratch; shared tree still prints
   `1`): `review-20260929T130729-ba40c5` reports `1
   failed, 187 passed` over `tests/test_schema.py` +
   `tests/extensions/test_operation_state.py`, the single
   failure exactly the new pin (the stubbed base returns
   the bare sentinel, so the `isinstance(...,
   _ResumedStream)` assertion fails). Reproduces the
   Implementation section's 187/188 claim exactly.
5. Wheel audit 0.317/0.318 — pass, re-derived. Both
   extracted trees carry `subscribe` (904) routed to
   `self._subscribe` (926) with `async def _subscribe`
   (821) and no `stream`/`_stream` definition; both
   `schema.py` files sha256
   `beef81019948755883d55d454854014ab6b371b0747f7120fd833a76fccdd72d`,
   identical to each other as claimed. The floor
   `(execution_context, extensions_runner,
   middleware_manager, execution_context_class=None,
   operation_extensions=None)` signature is accepted by
   the override's `(execution_context,
   extensions_runner, *args, **kwargs)` and passed
   through untouched. Corroborated, not trusted: sb316
   same shape, sb319 `subscribe` -> `stream` ->
   `_stream` with no `_subscribe`, installed ceiling
   `subscribe` a thin wrapper over `stream` with no
   `_subscribe` — so the override fires exactly on
   0.316–0.318 and is dead at the ceiling.
6. 11 un-skipped rows — pass.
   `review-20260929T130520-7fb74f`: `14 passed` (10
   subscribe-only singles + the forged-assignment row's 4
   params + the mode row). Every un-skipped body calls
   `schema.subscribe` only, or `execute_sync` only in the
   forged row; none references `schema.stream`.
7. 4 staying-skipped — pass, genuinely need
   `Schema.stream`. Each body streams a query, which
   `subscribe` cannot serve: closed-stream (385),
   cancelled-stream (413), the setter test's `_run_stream`
   leg (633), task-outliving (889). Still decorated (4
   `@_SKIP_WITHOUT_STREAM` in the file), and green at the
   ceiling: `review-20260929T130528-262ca7`, `6 passed`
   (incl. the setter row's 3 legs), 0 skipped. The 4
   `tests/test_schema.py` skips likewise all call
   `schema.stream` and ride the full-suite green below.
8. Ceiling behavior identical — pass.
   `review-20260929T130550-446bff`: full
   `tests/test_schema.py` +
   `tests/extensions/test_operation_state.py`, `188
   passed`, 0 failed, 0 skipped — every pre-existing
   resume/stream test unmodified-green.
   `review-20260929T130601-934dd1`:
   `tests/mutations/test_write_transaction.py`, `70
   passed, 1 skipped` (the skip is pre-existing and the
   file's hunk is prose-only).
9. No new public names — pass. The added method is
   private; package-wide `_subscribe` hits are the
   definition, its two docstring mentions, the `super()`
   call, and the unrelated pre-existing
   `consumers.py::handle_subscribe`; root `__init__.py`
   diff vs ITEM_BASELINE is empty. The diff's only new
   `def`s are `_subscribe`, the new pin, and its local
   `_frames`.
10. Chain shapes intact — pass. No `_admitted_chain` /
    `_refused_chain` / `get_extensions` /
    `create_extensions_runner` hunk; every removed
    `schema.py` line is docstring/comment prose.
11. R1–R16 stand — pass. Zero R-site symbols appear in
    any added/removed diff line, so every trigger site is
    byte-untouched; R10 holds (`__all__` still absent, 0
    hits); R5 holds (the `_execution_errors` hunk is the
    docstring's version number only, the `[]` fallback
    untouched). The new `_stream`/`_subscribe` twin is
    accepted under the R9 twin rationale (shared wrapper
    rule, asymmetries are the upstream's).
12. C1/C2 landed as prescribed — pass (presence only).
    Both docstrings read 3.2.10 and the `_stream`
    coverage sentence reads as the shipped two-override
    set; prose-truth grading belongs to the Comments
    verifier. The L5 one-liner wrap and M7 Proof-pattern
    notes in `## Implementation (Worker-2)` are likewise
    that verifier's business.
13. Lint gates — pass (read-only): `ruff check`, `ruff
    format --check`, and `check_trailing_commas.py
    --check` over all 6 touched paths, 0 violations.
14. Cells — default verified (every run above ran
    there); sharded + pg inapplicable by construction,
    judged: the seam opens no database, the new pin
    carries no `django_db` marker, and
    `test_operation_state.py` carries zero file-wide with
    no ORM reach — no alias or dialect decision exists to
    vary by cell.

No disputed findings exist; none judged. No new defects;
no failing attack. Scratch:
`docs/review/temp-tests/schema/verify-mechanics-1/`
(`revert_subscribe.py`).

Open threads: (1) package router tasking is still
unverified (the record's own thread 1) — it bounds F1's
wire exposure only, not the fix, and no re-pass is owed;
(2) my verify copy (slot-4) now carries the failability
revert by design; Worker-0 releases it at cleanup, and no
run after `review-20260929T130729-ba40c5` depends on it.

Status: verified

Handoff: Beyond the record I read the Performance and
Comments records whole, the pass-1 diff whole, the live
override + new pin + skip regions, and the 0.317/0.318
extracted wheels plus the sb316/sb319 corroborating
wheels and the installed ceiling source. The judgment
calls are the cells verdict (14 above, concur with the
record) and accepting the `_stream`/`_subscribe` twin
under R9. The failability failure mode is worth one
line: with the override reverted the pin fails on the
`isinstance` assertion rather than `AttributeError`,
because `patch.object(..., create=True)` installs
`_subscribe` on the base class which the subclass then
inherits — the test still fails iff the wrapper is
absent, which is exactly the property owed. Nothing else
is left for a later pass.
