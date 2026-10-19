# Review · Mechanics: `django_strawberry_framework/extensions/debug.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=2dae90d03c0749ebc2f4a512dd7668b1706b51bc

## Trace

Read the whole live target (863 lines: `DjangoDebugExtension` + 9 methods,
`_CursorCaptureCoordinator`, `_DebugOperationState`, the SQL/exception
serializers, `_terminal_original_error`, `_collect_exceptions`,
`_query_log_entries_since`, `_truncate`, `_row_cost`, `_apply_payload_caps`,
`_serialized_sql_row_or_dropped`, `_build_payload`, `_stash_payload_if_executed`)
plus the full call graph in both directions: the base
`django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
and `OperationState` (slots, carrier, compatibility branch, managed marking);
the sibling gate
`django_strawberry_framework/extensions/error_policy.py::masking_is_active`
(docstring + body), `is_maskable_result`, `_is_unexpected`, `_masked`,
`DjangoErrorPolicyExtension.on_operation`; the re-export
`django_strawberry_framework/extensions/__init__.py`; the acknowledgement
owner `django_strawberry_framework/utils/private_state.py::PrivateAuthority`
(whole); the deliberate-non-import
`MAX_TYPE_WRAPPER_DEPTH` ceiling and its raise-policy peels in
`django_strawberry_framework/utils/typing.py`; the toolbar counterpart
`django_strawberry_framework/middleware/debug_toolbar.py` (grep: no capture /
threshold / truncation overlap); the installed engine (strawberry-graphql
0.324.0 `Schema.execute`, `execute_sync`, `stream`, `_handle_execution_result`,
`_prepare_operation_sync`, `_prepare_operation_async`, `ExecutionResult`,
`PreExecutionError`, `ExecutionContext`) and the installed Django (6.1
`BaseDatabaseWrapper` equality, `queries_log`, `force_debug_cursor`,
`LazySettings.__getattr__`); graphene-django's `debug/` subsystem (`sql/types`,
`sql/tracking`, `exception/types`, `exception/formating`, middleware) for
wire-value parity; `tests/extensions/test_debug.py` (streaming seam rows,
Scenario 23 hostile shapes, gate rows, imports) and the sibling gate oracles
in `tests/test_error_policy.py` (deleted/unreadable-DEBUG rows,
`_SneakyError`); the contract sources (README response-debug-extension
section + fail-closed paragraph; glossary `DjangoDebugExtension`,
debug-fail-closed-gate, debug-payload-caps, debug-payload-availability,
masking-extension-ordering, response-extensions-debug-middleware,
django-debug-cursor-capture, async-sql-capture-boundary,
bounded-query-log-rollover anchors); and the `review_inspect.py` overview
(leads only, no finding taken from it).

Importer inventory (grep over package + tests + example): the only
production importer is `extensions/__init__.py` (the class re-export); every
other production mention (`extensions/error_policy.py`, `schema.py`,
package-root `__init__.py`) is a prose citation. Test importers:
`tests/extensions/test_debug.py` (whole, incl. private-helper imports via the
module), `tests/extensions/test_operation_state.py` (the class),
`tests/test_error_policy.py` (acknowledged instance as a fixture),
`examples/fakeshop/test_query/test_debug_extension_api.py` (live tier),
`examples/fakeshop/test_query/test_multi_db.py` (acknowledged factory).
No lower layer (`utils/*`, `types/*`, `error_policy.py`, `exceptions.py`)
imports the target. No symbol is moved or renamed by this record, so no
`--cited-by` sweep is owed; one defect (HUNT fields on F1), no duplication
(change challenges in R1 + the discharge list).

Cells: the F1 probe ran in the default cell (its process has no databases at
all — sharded and pg are inapplicable by construction: the gate runs before
any alias is touched, and an unconfigured process has no dialect to decide;
the verifier judges). The subscription probe ran in the default cell with
minimal configured settings (no alias/dialect decision involved). No other
workspace run was needed: every remaining behavior is pinned by existing
tests read statically or by installed-source reads that import nothing.

The target was dirty with concurrent work at read time (`M
django_strawberry_framework/extensions/debug.py`); the fingerprints below are
the live text actually reviewed. `git diff ITEM_BASELINE --
django_strawberry_framework/extensions/debug.py` is empty (live == item
baseline); the cycle diff touches only the `__init__` exact-bool check and
the `truth.describe` import, neither on the F1 path, so F1 ships at HEAD and
at the cycle baseline too (hunk inspection). No sibling axis records existed
at review time.

Fingerprints (`git hash-object`):

- 054e04df5915ed12c49ef63e4710feebca7388aa `django_strawberry_framework/extensions/debug.py`
- d9ed9cc67fea892afa2dd22a33236a52fc061fb1 `django_strawberry_framework/extensions/operation_state.py`
- a1defd394d8eda9b698964030a09efe6914278db `django_strawberry_framework/extensions/error_policy.py`
- dc3ebdc24b4817a64ea360d92bbbed340ad30bcc `django_strawberry_framework/extensions/__init__.py`
- b3c45503c3e2f648640b95ecad4d71a8315abb51 `django_strawberry_framework/utils/private_state.py`
- a672cd6b4f5cf6c207bd4f65eb080acd971a6b98 `django_strawberry_framework/utils/typing.py`
- ffda621eaf1bf9114a3144ca42586af8639c91ff `django_strawberry_framework/middleware/debug_toolbar.py`
- 93843bd3deae18c0dce234990ce14d3594a85000 `tests/extensions/test_debug.py`
- 9a72cdb83d4739be4018a3c58d0bf2736b63f569 `tests/test_error_policy.py`
- 8417985a690906b8b49d4a002cc9515322c5a57e `examples/fakeshop/test_query/test_debug_extension_api.py`
- 30978c34f63a833ffcc0fa11c80b773d241921be `docs/README.md`
- 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd `docs/GLOSSARY.md`

Upstream (not git-tracked; read from the shared `.venv`):
strawberry-graphql 0.324.0 (`schema/schema.py`, `types/execution.py`),
Django 6.1 (`db/backends/base/base.py`, `conf/__init__.py`), graphene-django
`debug/` (`sql/types.py`, `sql/tracking.py`, `exception/types.py`,
`exception/formating.py`, `middleware.py`).

Looks-for discharge (each entry: finding, none + reason, or rejection +
trigger):

1. Rule enforced at a caller instead of its owner: none, except F1 (the gate
   owns both settings-failure shapes but survives only one). Otherwise:
   `isSlow`/`isSelect` derive in
   `django_strawberry_framework/extensions/debug.py::_serialize_sql_row`,
   never at a call site; the stash gate lives in the one writer
   `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._stash_payload_if_executed`
   shared by both teardowns; the result/None guards live in
   `django_strawberry_framework/extensions/debug.py::_collect_exceptions`;
   caps live in
   `django_strawberry_framework/extensions/debug.py::_apply_payload_caps`
   behind the one assembler
   `django_strawberry_framework/extensions/debug.py::_build_payload`.
2. Policy in an adapter, mechanism in a policy layer: none. The fail-closed
   gate and the payload caps are the extension's own policy (spec-048
   Decisions 5/6 as the docstrings cite); the cursor bracket is Django's
   mechanism ridden, not re-owned (no package cursor wrapper); per-operation
   isolation rides `operation_state.py` rather than re-implementing it.
3. Contract source deciding differently from the body: one defect (F1: the
   gate's own "not a request that dies inside the gate" promise + the
   sibling `masking_is_active` two-exception rule vs the one-exception
   body) and one cross-axis stale-mechanism lead (C1: the sync-None
   sentences vs the installed engine; the gate outcome still holds).
   Otherwise the body matches every source checked: glossary cap numbers
   (100/25/4096/4096/16384/262144, exceptions-first, stop-not-skip),
   availability (both lists after execution, no key on parse/validation
   failure — verified against the installed engine's result assignments on
   all four colors), masking order (LIFO + `original_error` read position,
   rebuild-before-read on non-streaming, pre-masking stash on streaming),
   README bracketing/aggregation/fail-closed paragraphs, and graphene
   wire values (`duration > 10`, `sql.lower().strip().startswith("select")`
   verbatim incl. order, interpolated statement, `str(type)`/`str()`/
   three-arg `format_exception` triple).
4. Branch no real path reaches: rejected (R5: `state.snapshots or []`;
   the `None` side is unreachable and unobservable). Every other branch is
   reached by a real path and pinned: both stash-gate outcomes (executed
   vs parse/validation, all colors incl. streaming), both `get_results`
   outcomes, the coordinator first/overlap/final-release transitions, the
   hop-ceiling + cycle stops, the per-row vs drain degrades, the exact-bool
   refusal, the deleted/malformed-DEBUG inerts.
5. Mode flag standing in for a named adapter: none.
   `allow_unsafe_production` is a security acknowledgement (exact-bool,
   construction-only, authority-held), not a behavior mode; no enum hides
   branches. The F1 recommendation deliberately does NOT introduce a shared
   DEBUG-read helper: the two gates fail to opposite values, so sharing
   needs a default parameter (the smell this entry names).
6. State owned in two places: none. Snapshots + payload live only on
   `_DebugOperationState` (the shared-instance republication the class
   docstring describes is why); the acknowledgement lives only in
   `_ACKNOWLEDGEMENT` (the property is a read view, and the gate reads the
   authority, not the view); saved-vs-live flag values are distinct roles
   in one immutable record; the two teardowns share one conditional writer
   (the rebuild preserves the streaming stash by refusing non-graphql
   shapes rather than clearing).
7. Dependency pointing the wrong way: none. The target imports only the
   package root (`logger`), `exceptions`, `utils/*`, and the sibling
   `operation_state` seam; the `TYPE_CHECKING` Django import is
   annotation-only over a module that cannot import back; nothing lower
   imports the target; the `schema.py` back-edge stays function-local in
   `operation_state.py`.
8. `django.conf.settings` read at import: none. Module level binds only
   the lazy `settings`/`connections` proxies; the one `DEBUG` read is per
   operation inside
   `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._disclosure_permitted`
   (per-test override honored, pinned). Touching `queries_log`/
   `force_debug_cursor` opens no connection (plain attributes; verified in
   installed Django).
9. `__all__` disagreeing with the public surface: none.
   `__all__ = ["DjangoDebugExtension"]` matches the subpackage re-export,
   the TREE/docs rosters, and the never-root-exported rule; test imports
   of privates via the module need no export.
10. Two sites implementing one rule: rejected (R1: the hop ceiling;
    examined-and-single: truncation, row cost, stash gate, coordinator,
    wire literals, warning, bool-validation wording — each change-challenged
    to count 1). No consolidation owed.
11. Sync/async twins that drifted: none. One sync generator serves both
    colors per hook (the engine enters sync hooks on the async path too);
    the two teardowns share the one stash writer, so they cannot drift on
    the gate. Subscription frames are not a twin (R4).
12. Guard one flavor has and a sibling lacks: one defect (F1: the sibling
    masking gate catches `ImproperlyConfigured`, this gate does not; the
    sibling docstring establishes the shape as in-scope). Rejected: R2
    (defaulted `getattr` vs direct `original_error` read — withhold-safe,
    no hostile-capture contract), R3 (whole-list vs per-row degrade —
    contracted asymmetry), R6 (foreign error objects), R8 (acknowledged +
    unconfigured fails loud at acquisition — correct).

## Findings

### High

None.

### Medium

#### F1: the fail-closed gate dies with `ImproperlyConfigured` when Django settings are unconfigured

- **Observation (Defect)** —
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._disclosure_permitted`
  reads the gate through `getattr(settings, "DEBUG", None)`, which survives
  `AttributeError` (a deleted setting) but lets `ImproperlyConfigured` (a
  genuinely unconfigured settings proxy) escape the gate. The escape happens
  pre-yield in
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.on_operation`,
  outside any `try`, so the engine coerces it into a synthetic error: the
  operation returns `data: None` plus the `ImproperlyConfigured` text
  instead of its data. The gate's own comment promises "not a request that
  dies inside the gate", and the sibling gate
  `django_strawberry_framework/extensions/error_policy.py::masking_is_active`
  catches both exceptions for the same question.
- **Evidence** — HUNT evidence record. Workspace run
  `review-20260929T171651-1c41a9` (address
  `review/extensions/debug.py/mechanics`, cell default, copy slot-3 fresh,
  package digest `sha256:c071c3db...`, exit 0), command `uv run python
  scripts/workspace.py run review/extensions/debug.py/mechanics -- python
  /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/extensions-debug/mechanics/probe_unconfigured.py`.
  Reach: genuine real path, no mocks — child processes with
  `DJANGO_SETTINGS_MODULE`/`FAKESHOP_*` scrubbed and no
  `settings.configure()`, executing `{ ok }` through a plain
  `strawberry.Schema` carrying the bare class (the documented opt-in) with
  a pure-Python resolver. Positive control: the identical process shape
  without the extension (package still imported, proving the import works
  unconfigured) returns `DATA: {'ok': 'ok'}`, `ERRORS: []`. Figures: with
  the extension, `DATA: None`, `ERRORS: ['Requested setting DEBUG, but
  settings are not configured. ...']`, `EXTENSIONS: {}`; stderr shows the
  raise from Django's `_setup` via the gate's read. Upstream static root:
  Django 6.1 `LazySettings.__getattr__` raises `ImproperlyConfigured` when
  unconfigured, and a defaulted `getattr` suppresses `AttributeError` only.
  The HEAD..live and cycle-baseline..live deltas do not touch this path
  (hunk inspection), so the defect ships at HEAD and at the cycle baseline
  too.
- **Impact** — Any operation through a schema carrying the extension in a
  process without configured Django settings (a settings-free test
  process, a script exercising pure-Python resolvers) answers a synthetic
  error instead of its data — exactly backwards from the gate's purpose
  (leave the operation untouched). No disclosure: the fail direction is an
  error, not a leak. Narrow shape, loud failure, dev-only surface.
- **Severity** — Medium: correctness failure (error instead of data) on a
  documented spelling. Aggravating: trivially reachable once the shape
  holds, and the error text names settings rather than the gate, so the
  misattribution costs debugging time. Mitigating: narrow shape
  (unconfigured process + debug extension), loud rather than silent,
  dev-only surface, three-line fix.
- **Recommendation** — Owner:
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._disclosure_permitted`
  (the gate owns both settings-failure shapes). Mirror the sibling: read
  `settings.DEBUG` inside `try`/`except (AttributeError,
  ImproperlyConfigured)`, defaulting to the inert answer, keeping the exact
  `is True` check and the acknowledgement short-circuit; reword the gate
  comment, which currently describes the getattr-with-default mechanism.
  Considered and rejected: a shared DEBUG-read helper for the two gates —
  they fail to opposite values (inert vs masking), so sharing needs a
  default parameter, which is the mode-flag smell entry 5 names. Same
  structure, separate sites.
- **Must not change** — Deleted-`DEBUG` behavior (inert + exactly one
  fail-closed warning, pinned by
  `tests/extensions/test_debug.py::test_deleted_debug_setting_is_an_inert_refusal`);
  malformed-`DEBUG` values still inert; `DEBUG=True` still discloses; the
  acknowledgement still opens regardless of the setting; warning text and
  level; operation result bytes on every configured-settings path.
- **Proof** — At `review/extensions/debug.py/verify-mechanics-<n>`: (1)
  new package-tier test `test_unconfigured_settings_is_an_inert_refusal`
  in tests/extensions/test_debug.py (beside the Scenario 23 gate rows;
  simulates the unconfigured proxy by replacing the wrapped holder with
  one raising `ImproperlyConfigured` — the sibling `_UnreadableSettings`
  shape with the second documented exception — executes a pure query
  through a schema carrying the bare class; asserts data intact, no
  `debug` key, exactly one fail-closed warning, coordinator empty) —
  plain-text name, Worker-2 creates it at the package tier (settings
  manipulation is unreachable over live HTTP, mirroring the sibling gate
  tests): run that node with `uv run python scripts/workspace.py run
  review/extensions/debug.py/verify-mechanics-<n> -- pytest` plus
  `--no-cov`; must report `1 passed`. (2) deleted-`DEBUG` compat
  unaffected: `uv run python scripts/workspace.py run
  review/extensions/debug.py/verify-mechanics-<n> -- pytest
  tests/extensions/test_debug.py::test_deleted_debug_setting_is_an_inert_refusal
  --no-cov` must report `1 passed`. Failability: reverting the production
  hunk must fail exactly command (1)'s row; command (2) passes before and
  after.
- **Freshness** — Trace fingerprints cover every cited file.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._disclosure_permitted`.
  Contract sources: the gate's own comment ("must get the same inert
  refusal ... not a request that dies inside the gate"); the sibling
  `django_strawberry_framework/extensions/error_policy.py::masking_is_active`
  docstring + body ("answering a schema outside a configured Django
  process ... letting that escape would answer a masking question by
  exception", catching both exceptions); Django's `LazySettings`
  unconfigured-read behavior (upstream root cause); the existing oracle
  `tests/extensions/test_debug.py::test_deleted_debug_setting_is_an_inert_refusal`
  (pins the deleted half of the same promise).

### Low

None.

## Rejected

- R1 (hop ceiling 64 re-spelled instead of importing
  `MAX_TYPE_WRAPPER_DEPTH`): deliberate per the comment, and the comment
  is right: the walks differ in failure policy (stop-and-keep the
  best-effort terminal vs raise), so they differ in reason to change.
  Change challenge: "raise the error-chain ceiling" touches this site
  only; "raise the type-peel ceiling" touches `utils/typing.py` only.
  Count 1 each. Trigger: a fourth chain-peel motivating the shared
  extraction (the comment's own trigger).
- R2 (defaulted `getattr(error, "original_error", None)` in
  `django_strawberry_framework/extensions/debug.py::_collect_exceptions`
  vs the sibling's direct read): not a defect. A hostile read (an
  `original_error` property that raises `AttributeError`) is absorbed as
  absence and the row skipped; a non-`AttributeError` escape degrades the
  whole exceptions list via
  `django_strawberry_framework/extensions/debug.py::_build_payload`. Both
  fail directions withhold diagnostic rows — safe for a disclosure
  surface — and no contract promises hostile-error capture (hostile
  objects need a consumer extension inserting foreign entries). The
  sibling's direct-read rule transfers only where "absent" is the
  dangerous answer (masking); here it is the safe one. Trigger: a
  contract promising hostile capture, or a real path losing rows to one
  hostile entry.
- R3 (exception collection degrades to an empty list while SQL degrades
  per row): contracted asymmetry, not drift. The `_build_payload`
  docstring promises exactly this (no partial list to adopt), the fail
  direction withholds, and the only mid-loop raise on a non-hostile path
  is a raising exception `__str__` — still a consumer bug, still withheld
  safely. Per-row exception capture would be a design change, not a fix.
  Trigger: a contract promising partial exception capture.
- R4 (subscription frames carry no `debug` key — new-card candidate):
  verified, not a defect. Probe run `review-20260929T171727-726f79`
  (same address/cell/copy as F1, package digest `sha256:c071c3db...`,
  exit 0): a 2-frame subscription over `Schema.stream` with an
  acknowledged extension yields `extensions={}` on both frames, while
  queries publish. No contract promises per-frame or subscription debug:
  the availability anchor enumerates query/mutation/introspection
  outcomes and omits subscriptions, and per-frame capture needs a new
  seam design (slicing cadence, budget scope per frame vs per stream) no
  contract answers — a maintainer decision, hence a card, not a fix
  (same standing as the earlier skipped-finalize diagnosis lead).
  Worker-0: please carry to `## Decisions`. Trigger: a contract promising
  subscription/per-frame debug rows.
- R5 (`state.snapshots or []` in the stash writer): the `None` side is
  unreachable — both stash callers guarantee a list (`on_operation`
  assigns before its `try`/`finally`; `on_execute` guards `is None`) —
  and unobservable either way (both spellings yield `[]` for the empty
  case). Harmless defensive default; removing it changes nothing.
  Trigger: a third stash caller.
- R6 (foreign objects in `errors` reaching the terminal-error walk):
  the collector admits only entries with a non-`None` `original_error`,
  which stock results always type as `GraphQLError`; a foreign admitted
  object still terminates (the `isinstance` return + the hop bound).
  Trigger: a real path putting foreign objects in `errors`.
- R7 (`vendor` reads the Django wrapper while graphene reads the raw
  handle): deliberate improvement, verified against graphene's
  `sql/tracking.py` (`getattr(conn, "vendor", "unknown")` on the DBAPI
  handle, which carries no `vendor` — nearly always `"unknown"`). The
  contract promises graphene's wire NAMES, not its bug; the wrapper
  value is the documented semantic. Trigger: a migrant tool depending on
  `"unknown"`.
- R8 (acknowledged + unconfigured dies at acquisition): correct. The
  acknowledgement explicitly requests capture, capture needs databases,
  and none exist — fail-loud is the honest answer (observed as the
  `DATABASES` raise in run `review-20260929T171703-89a27a` while shaping
  the R4 probe). The inert promise covers the unacknowledged gate only.
  Trigger: a contract promising inert-when-impossible even when
  acknowledged.

## Cross-axis (for Comments)

### C1: three prose sites say sync early-returns "leave `result` as `None`"; the installed engine assigns a strawberry shape

- **Observation** — The class `Lifecycle` paragraph, the `on_operation`
  teardown comment, and the `_stash_payload_if_executed` docstring in
  `django_strawberry_framework/extensions/debug.py` each say sync
  parse/validation early-returns "leave `result` as `None`". On the
  installed engine (strawberry-graphql 0.324.0) `execute_sync` assigns
  the strawberry pre-execution `ExecutionResult` to
  `execution_context.result` before the operation context unwinds (the
  `pre_execution_result` branch; `_prepare_operation_sync` returns the
  strawberry shape, built with extension results read inside the still-open
  context). The outcome the sentences protect still holds — the
  `isinstance(result, GraphQLExecutionResult)` gate excludes the
  strawberry shape, so no stash and no key — but the mechanism sentence is
  false on the installed engine. (The async half of the same sentences —
  "may assign a strawberry `PreExecutionError` before teardown" — is
  accurate on 0.324.0 and must survive the reword.)
- **Evidence** — Installed-source read (no behavior at issue; the no-key
  outcome is pinned by existing tests on all colors): 0.324.0
  `Schema.execute_sync` early-return branch +
  `Schema._prepare_operation_sync` return type vs the three sentences.
  Whether the 0.316.0 floor also assigned (born-stale) or left `None`
  (version drift) is untested and does not matter to the grade: the prose
  must hold across the supported range, and it does not hold on latest.
- **Impact** — A reader reasoning about teardown state — or a future gate
  change relaxing `isinstance` toward `is not None` — builds on a false
  premise that looks load-bearing. Three sites state it, so the false
  premise has three citers.
- **Severity** — Medium: stale mechanism in a public class docstring plus
  two internal sites. Not the High "wrong contract" shape: the contract
  outcome (no key without execution) is stated correctly everywhere.
- **Recommendation** — Reword the three sites to cover both shapes
  ("leave `result` as `None` or a strawberry pre-execution shape (sync;
  version-dependent), or a strawberry `PreExecutionError` (async)"),
  keeping the gate sentence that already handles both. Comments owns the
  exact text; the async half stays as written.
- **Must not change** — n/a (Comments finding).
- **Proof** — Static, in the shared tree: `rg -n "leave .*result.* as
  None" django_strawberry_framework/extensions/debug.py` must print no
  line still claiming the `None`-only sync shape, and each reworded
  sentence must grade true against strawberry 0.324.0's
  `execute_sync`/`_prepare_operation_sync` while covering the 0.316.0
  floor either way it behaves.
- **Freshness** — Trace fingerprints cover every cited file.
- **Owner + contract source** — Owner: the three prose sites (Comments
  axis implements with Comments). Contract source: the installed engine
  behavior above + the module's own stash gate, which already admits only
  the graphql-core shape — the code handles both, the prose lags it.

Handoff: The module is in strong shape — the isolation, degradation, cap,
and ordering machinery all match their contracts, and the graphene parity
check passed value-by-value (the one deviation, R7's `vendor`, favors this
package). Beyond the record's trace I also read the `test_debug_extension_api.py`
live-tier module list (grep-level; the availability/cap contracts it pins
agree with the body) and the `error_policy.py` package-level policy (only
to confirm the sibling-gate relationship F1 cites). Two threads worth
naming that the record does not otherwise state: `get_results` returns the
stashed payload object itself (fresh outer dict, shared innards) — safe
because nothing in the merge path mutates it, and copying would cost per
operation, so no finding; and the `__init__` order (carrier refusal before
bool validation) yields the more accurate error on a hostile re-`__init__`,
so no finding. Open threads for Worker-0: (1) R4 asks for a `## Decisions`
entry (subscription/per-frame debug as a new card; probe run on file);
(2) the F1 fix touches the gate comment, so the Comments verifier should
expect that hunk inside the Mechanics change. No sibling records existed at
review time; nothing here depends on their verdicts. Scratch kept under
`docs/review/temp-tests/extensions-debug/mechanics/` (`inspect/` overview +
stripped source, `debug.json`, `probe_unconfigured.py`, `probe_subscription.py`).
Runs: `review-20260929T171651-1c41a9` (F1 proof), `review-20260929T171727-726f79`
(R4 behavior), `review-20260929T171703-89a27a` (R8 shaping failure, exit 1,
shaping only), `review-20260929T171618-ed21dd` (path mistake, exit 2, no
evidence). Fingerprints: target `054e04df` at read; see Trace for the rest.

## Verification (Mechanics)

Address `review/extensions/debug.py/verify-mechanics-1` (slot-2, package
digest `sha256:d0ab2d72...`, cell default); before copy
`review/extensions/debug.py/before` pinned at ITEM_BASELINE (the old
`getattr` spelling is baseline line 740). The shared tree carries every
axis's implements; this pass grades the F1 hunks only. Verdict: F1 pass;
C1 not graded (Comments owns it; the gate-comment hunk at the F1 site is
F1's own reword, confirmed below). No new finding on this axis; one
routed gap for Worker-0 (step 6).

Step 1 — Proofs first (the main artifact carries no Worker-2 sections,
so there was nothing to defer). `git diff ITEM_BASELINE` over the two
item paths hashes to `824f4330f0749dda205ad8364dcb9586e4506f1d`; it holds
the dispatched F1 production hunk (the `ImproperlyConfigured` import,
the gate `try`/`except`, the reworded gate comment) and the new gate
test beside the Scenario 23 rows, plus sibling-axis hunks this axis does
not grade (Perf F1/F2 code, Comments F1-F15 and C1 prose). No
`pass-<n>.diff` was dispatched; the graded bytes are fingerprinted
below. Other records hold no `Cross-axis (for Mechanics)` (Performance:
none; Comments: no section), and this is pass 1, so the two Proof lines
below are the whole step-1 set, run verbatim at the address:

- Proof (1): `uv run python scripts/workspace.py run
  review/extensions/debug.py/verify-mechanics-1 -- pytest
  tests/extensions/test_debug.py::test_unconfigured_settings_is_an_inert_refusal
  --no-cov` reports `1 passed` (run `review-20260929T175834-84c9d8`).
- Proof (2): `uv run python scripts/workspace.py run
  review/extensions/debug.py/verify-mechanics-1 -- pytest
  tests/extensions/test_debug.py::test_deleted_debug_setting_is_an_inert_refusal
  --no-cov` reports `1 passed` (run `review-20260929T175844-336fea`).

Step 2 — numbers: none claimed for this axis (Mechanics carries no bench
figure), so nothing to reproduce.

Step 3 — whole-diff read through this axis, then attacks. The F1
production hunk matches the recommendation line by line:
`settings.DEBUG` inside `try`/`except (AttributeError,
ImproperlyConfigured)` defaulting inert, exact `is True` kept, the
acknowledgement short-circuit first (semantically identical to the old
`or` ordering), and the gate comment reworded off the getattr
mechanism. The new test sits beside the Scenario 23 rows at the package
tier, simulates the unconfigured proxy via a raising `_wrapped` holder,
and asserts data intact, no `debug` key, exactly one fail-closed
warning, and an empty coordinator. Sibling hunks do not touch the gate
path: Perf F1/F2 sit inside `_build_payload`, which the gate precedes
(the inert path never reaches it, pinned by the no-bracket row below);
`_build_payload` is the only production caller of either reshaped
helper and the new `budget` default preserves the old call shape
(existing slicing rows pass unmodified). C1's three reword sites are
prose in the class Lifecycle paragraph, the `on_operation` teardown
comment, and the stash-writer docstring — not graded here. Attacks, all
passing (each a bounded pytest scope at the address, `--no-cov`):

- Gate rows, both tiers (DEBUG=True discloses via
  `test_execute_sync_restores_the_prior_flag_value`; ack opens regardless
  via the package acknowledged-factory row and the live ack row;
  malformed-DEBUG inert via the 3-param live malformed row; warning
  text/level via the live withhold-and-warn row; ack construction and
  read-path rows): `18 passed` (run `review-20260929T180102-91abad`).
- Full `tests/extensions/test_debug.py` module (configured-path bytes):
  `75 passed` (run `review-20260929T180116-34951b`).
- A settings module raising a third exception type on import would still
  escape the gate — same as the sibling gate and same as before; the
  accepted contract is exactly the two documented exceptions, so no
  finding. Acknowledged-plus-unconfigured still fails loud at
  acquisition (R8), unchanged by the short-circuit reorder.

Step 4 — disputes: none recorded; nothing to judge.

Step 5 — failability, tier, symbols, lint. `workspace.py prove` with
manifest
`docs/review/temp-tests/extensions-debug/verify-mechanics-1/gate-failability.json`
(anchor/replacement revert of the gate body to the getattr spelling;
scope both Proof rows; `expect_failing` exactly row (1)): baseline `2
passed`; mutant fails exactly
`test_unconfigured_settings_is_an_inert_refusal` with the F1 signature
(`assert [GraphQLError('Requested setting DEBUG, but settings are not
configured.')] is None`) while the deleted-DEBUG row passes; restore
byte-proved (`da22bf47` before and after) (run
`review-20260929T180209-e14ec5`). Row (2) also passes at the `before`
address (run `review-20260929T180344-5e2652`), so it passes before and
after. Tier: package tier is correct — settings-holder manipulation is
unreachable over live HTTP, mirroring the sibling gate tests. No symbol
moved or renamed, so no `--cited-by` sweep is owed. Lint gates (shared
tree, `--check` forms): `ruff check` all passed; `ruff format --check`
2 files already formatted; `check_trailing_commas.py --check`
violations 0; `check_citations.py --check` OK, 1306 resolve.

Step 6 — no new problem on this axis. Routed gap for Worker-0
(Comments): the F1 code change made two test-prose sites stale — the
Scenario 23 banner (`tests/extensions/test_debug.py`, "the gate reads
it with a defaulted getattr") and the
`test_deleted_debug_setting_is_an_inert_refusal` docstring ("with a
default, not attribute access"). Outcomes hold; only the mechanism
clause is false. Runnable: `rg -n "defaulted .*getattr|with a default,
not attribute access" tests/extensions/test_debug.py`.

Cells: sharded and pg inapplicable by construction — judged, not
assumed. The gate reads only the acknowledgement authority and
`settings.DEBUG` before any bracket exists, touching no alias, dialect,
or backend behavior; the new test executes a pure-Python `{ ok }` with
no database; and `test_inert_operation_acquires_no_bracket_and_takes_no_snapshot`
(replacing the connections handler with a raising double) proves the
refusal path reaches no connection. Default cell only.

Fingerprints (`git hash-object`, graded bytes):
`django_strawberry_framework/extensions/debug.py` `da22bf47...`;
`tests/extensions/test_debug.py` `445e4ac3...`;
`examples/fakeshop/test_query/test_debug_extension_api.py` `8417985a...`
(unchanged since review). Item diff `824f4330...` (above).

Handoff: This pass read AGENTS.md, START.md, REVIEW.md (Worker-1
verifies, Worker-2 implements, Workspace), the plan item (implementing;
F1 + gate test in scope), all three axis records whole (Performance F1
read for gate-path interaction only; Comments F1-F17 + C1 sites located
in the diff, none graded), the whole live target gate region plus the
full item-scoped diff hunk inventory (18 production + 9 test hunks),
and the gate rows in both test tiers. Conclusions the checks do not
state: the live tier needs no new row (malformed/ack/warning pins
already cover the must-not-change list; the unconfigured shape is
package-tier-only by construction), and the prove mutant's failure text
replays the review-pass F1 evidence signature exactly. Open thread: the
step-6 routed gap belongs to the Comments verifier of this item
(`verify-comments-1` scratch exists; if that pass already closed,
Worker-0 routes instead). Scratch: the prove manifest above; no probe
scripts. Runs: `review-20260929T175834-84c9d8` (Proof 1),
`review-20260929T175844-336fea` (Proof 2),
`review-20260929T180102-91abad` (gate rows),
`review-20260929T180116-34951b` (full module),
`review-20260929T180209-e14ec5` (prove),
`review-20260929T180344-5e2652` (before compat).
