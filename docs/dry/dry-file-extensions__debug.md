# DRY review: `django_strawberry_framework/extensions/debug.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in a named family row (indexed names reused where the same rule
appears) or is recorded file-local with its proving challenge, and every
rejection carries its contract difference + trigger + home. Zero production
edits; zero tracked files changed.

## System trace

FRESH target, 862 lines: `DjangoDebugExtension`, the development-only
in-response debug surface. It DEFINES the per-operation capture of Django
query-log SQL plus execution exceptions into `extensions["debug"]`, and
ENFORCES the fail-closed production gate (`settings.DEBUG` / explicit
`allow_unsafe_production` acknowledgement) with bounded, deterministically
truncated payloads. Three Strawberry hook overrides (`on_operation`,
`on_execute`, `get_results`) over one shared stash writer; one
overlap-safe cursor coordinator; one acknowledgement authority; one
operation state subclass. No queryset execution, no resolver body, no
`sync_to_async`, no soft dependency (every import is a hard dep), no
`register_subsystem_clear`.

Connected code read for judgment, outside the item:
[extensions-init][extensions-init] (leaf manifest + debug-opt-in prose, full),
[extensions-operation-state][extensions-operation-state] (base contract +
`_reconstruction_refusal` extension point + compatibility branch, full),
[extensions-error-policy][extensions-error-policy] (masking read of
`original_error` + admitted-chain order, code passages),
[error-policy][error-policy] (`ErrorPolicy.__post_init__` bool gate, full),
[middleware-debug-toolbar][middleware-debug-toolbar] (server-side counterpart
+ `require_debug_toolbar` guard, full),
[utils-private-state][utils-private-state] (`PrivateAuthority` contract,
full), [exceptions][exceptions] (`describe_value` scope paragraph naming
this file + safe-renderer family, passages),
[utils-typing][utils-typing] (`MAX_TYPE_WRAPPER_DEPTH` raise-policy peel,
passages), [utils-imports][utils-imports] (`require_optional_module`
primitive, passages), [schema][schema] (admitted-chain order comment naming
this file), [consumers][consumers] (per-event masking seam prose),
[pkg-root][pkg-root] (debug omission), oracles
[test-debug][test-debug] (module docstring contract map, full head +
spot passages) and [test-debug-api][test-debug-api] (live-tier split,
full head), upstream graphene-django `debug/sql/tracking.py` +
`debug/exception/formating.py` (wire oracle: `duration > 10`,
`sql.lower().strip().startswith("select")`, `wrap_exception` triple),
Django's `CaptureQueriesContext` source (save/restore + length-snapshot
oracle), Strawberry's `SchemaExtension` hook list (`on_operation`,
`on_execute`, `get_results` — exactly the three overridden here; no
`on_parse`/`on_validate`, which is the no-`debug`-key contract).

Excluded with reason: every other indexed family whose files-covered list
touches `extensions/` was judged on its mechanism against this target's
REAL surface (Matrix axes 1-3, C12-C14); the concurrent dirt
(`django_strawberry_framework/connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target owns ONE flavor's diagnostic
(the debug response surface). Sibling extensions own theirs: masking at
[extensions-error-policy][extensions-error-policy]`::mask_execution_result`,
resource enforcement at `extensions/resource_policy.py`. The three share
only the `_OperationBoundExtension` base (an owned extension point, F6)
and the `PrivateAuthority` primitive (single owner, composed by name —
F5). The `allow_unsafe_production` bool-strictness mirrors
[error-policy][error-policy]`::ErrorPolicy.__post_init__` by CITATION
(the docstring names it), not by shared code: separate classes,
separate messages, separate reasons to change — rejected, see F5 nested
rejection. Considered families `subscription-per-event-error-masking`
and `typed-rejection-value-tail`: the first rejected with difference
(capture publishes originals; masking strips them — R4), the second
confirmed consumer-only (F7).

**2. Sync/async twins.** No colored pair: one synchronous generator
`on_operation` serves both colors (the engine enters sync generator
hooks on the async path too — stated in the docstring), plus one
`on_execute` teardown and one pure `get_results` read. No
`run_in_one_sync_boundary` call, no `sync_to_async`, no ORM execution
(flag writes + `queries_log` reads only). The async bound (executor-thread
queries escape the event-loop-thread bracket) is a DOCUMENTED limitation,
not a second body. Considered families `one-sync-boundary` (0 calls —
R2, do not inherit) and the `connection.py` two-colored-body contrast
(DRY.md principle 5's opposite answer: debug shares the one pure path
and documents the color bound instead).

**3. Derived rather than repeated knowledge.** Wire keys are deliberate
literals (`isSlow`/`isSelect`/`excType`/… spelled at the serialize
sites; the docstring forbids deriving them through a casing helper), and
`isSlow`/`isSelect` derive at exactly one site
(`_serialize_sql_row`). `vendor`/`alias` are read off the connection
object, never reconstructed. The hop ceiling `64` re-spells
[utils-typing][utils-typing]`::MAX_TYPE_WRAPPER_DEPTH`'s NUMBER with the
opposite failure policy (stop-and-keep vs raise) — deliberately NOT
imported, stated in-file; rejected, see F3 nested rejection. The install
hint / floor strings live at their own owners; this file holds none.
Considered family `soft-dependency-require-guard`: 0 `require_*` calls,
0 optional imports — R1, do not inherit.

**4. Inverse / round-trip pairs.** No encode/decode halves. The acquire /
release bracket is one coordinator's two seams (F1), not two owners that
can drift; the snapshot (flag + log length) / restore pair is taken and
discharged by the same `on_operation` body. No surface.

**5. Contracts restated in another medium.** Three media: production code
(the definitions); independent oracles (both test tiers re-spell wire
keys and the 10s threshold as literals, never importing the serializers
— stated in [test-debug][test-debug]'s own rules; upstream graphene
shapes corroborate the wire, not the code); projections (module + class
+ method docstrings, the leaf usage line, `schema.py` order comment).
A wire change moves the production serializer once; oracles and prose
follow as listed-never-counted (C2, C3).

**6. Enforcement by omission.** Three deliberate absences, each with a
contract source: no `on_parse`/`on_validate` overrides (parse/validation
failures carry no `debug` key — the engine reads results before this
hook's teardown on those paths; module docstring); no soft-dependency
guard (no optional import exists to guard — R1); `get_results` returns
`{}` when no stash exists (pure idempotent read; class docstring). Every
guard the contract requires is present: bool-strict construction (F5),
per-operation DEBUG read (F5), `ExecutionResult`-only stash gate (F3),
per-row + per-list + budget caps (F4). The `getattr(error,
"original_error", None)` vs error-policy's deliberate DIRECT access is a
checked separation, not a gap: this read runs inside the diagnostic
degrade (a hostile attribute costs at most its own list), while the
masking read enforces a production contract — different responsibilities,
and no contract source extends the direct-access rule to this site.
Ambiguous-or-newly-proposed would route to the maintainer; this one is resolved by
the differing failure policies, so no defect and no card.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **49 top-level statements (0–48)**. Every member lands below;
every challenge in `### Challenges` ends in a family row, a file-local
row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (counterpart relation, fail-closed + caps postures, opt-in shape, wire contract, capture boundaries) | (none) | prose projection; R5 home; F5 home |
| 1–3 | `import math/threading/traceback` | stdlib names | consumer bindings (F2/F3 use) |
| 4–7 | `collections.abc.Mapping`, `contextlib.ExitStack`, `dataclasses.dataclass`, `typing.*` imports | stdlib names | consumer bindings (F1/F4/state use) |
| 8–9 | `django.conf.settings`, `django.db.connections` | hard-dep names | consumer bindings (F1/F5 use) |
| 10–11 | `graphql.ExecutionResult`, `graphql.GraphQLError` | hard-dep names | consumer bindings (F3 use) |
| 12 | `from .. import logger` | hard-dep name | consumer binding (F4 degrade logs) |
| 13 | `from ..exceptions import ConfigurationError, describe_value` | hard-dep names | F7 consumer site; R-bool-strictness token |
| 14 | `from ..utils.private_state import PrivateAuthority` | hard-dep name | F5 consumer (single owner composed by name) |
| 15 | `from .operation_state import OperationState, _OperationBoundExtension` | hard-dep names | F6 consumer (owned extension point) |
| 16 | `if TYPE_CHECKING` (`BaseDatabaseWrapper` import) | type-only name | annotation projection |
| 17 | `__all__ = ["DjangoDebugExtension"]` | 1-member manifest | file-local (F5 scope note) |
| 18 | `_SLOW_QUERY_SECONDS = 10` | slow threshold | F2 |
| 19 | `_MAX_ORIGINAL_ERROR_HOPS = 64` | chain-walk ceiling | F3 (+ nested rejection) |
| 20–25 | six payload-cap constants (row counts, per-row chars, text budget) | caps | F4 |
| 26 | `_TRUNCATION_MARKER` | cut marker | F4 |
| 27–29 | `_DebugSQLRow`, `_DebugExceptionRow`, `_DebugPayload` TypedDicts | wire shapes | F2 |
| 30 | `_CaptureToken` | bracket token | F1 |
| 31 | `_ConnectionSnapshot` | per-connection snapshot | F1 |
| 32 | `_ActiveCapture` | immutable coordinator record | F1 |
| 33 | `_CursorCaptureCoordinator` + `__init__`/`acquire`/`release` | flag ownership | F1 |
| 34 | `_coordinator` singleton | module coordinator | F1 |
| 35 | `_serialize_sql_row` | SQL wire row | F2 |
| 36 | `_serialize_exception` | exception wire row | F2 |
| 37 | `_terminal_original_error` | chain walk | F3 |
| 38 | `_collect_exceptions` | result-error filter | F3 |
| 39 | `_query_log_entries_since` | log slice | F1 |
| 40 | `_truncate` | one truncation primitive | F4 |
| 41 | `_row_cost` | string-cost meter | F4 |
| 42 | `_apply_payload_caps` | three-pass cap applier | F4 |
| 43 | `_serialized_sql_row_or_dropped` | per-row degrade | F4 |
| 44 | `_build_payload` | payload assembly + dual degrade | F3/F4 |
| 45 | `_DebugOperationState` + `__init__` | per-operation capture state | F6 |
| 46 | `_AcceptedDisclosure` | acknowledgement record | F5 |
| 47 | `_ACKNOWLEDGEMENT` authority | settled-gate store | F5 |
| 48 | `DjangoDebugExtension` + 9 methods (`__init__`, `_new_operation_state`, `allow_unsafe_production`, `_acknowledged`, `_disclosure_permitted`, `on_operation`, `on_execute`, `_stash_payload_if_executed`, `get_results`) + `_reconstruction_refusal` | extension lifecycle | F5 (gate + hooks), F6 (refusal override) |

Rules: R-coord (30–34, 39: overlap-safe flag ownership + snapshot slice);
R-wire (18, 27–29, 35–36: six-key/triple serializers + threshold);
R-chain (19, 37–38, 44-stash half: terminal-error walk + collection
guards + stash gate); R-caps (20–26, 40–43, 44-cap half: truncation +
row counts + budget + degrades); R-gate (46–48, 13–14: acknowledgement
+ fail-closed lifecycle); R-state (15, 45, 48-refusal: operation-bound
state + reconstruction refusal). Eight indexed families considered
(`typed-rejection-value-tail`, `soft-dependency-require-guard`,
`one-sync-boundary`, `subscription-per-event-error-masking`,
`sealed-authorization-source`, `ws-connection-actor-state`,
`drf-soft-export-guard`, `subsystem-clear-lifecycle`): one confirmed
consumer-only (F7), three rejected with difference + trigger (R1, R2,
R4), four checked with no surface (C12–C14 + Matrix axes 1–2). No new
family is named (all definition rows are file-local, so Worker 0 owes
six `## Responsibility index` file-local rows + the F7 consumer
confirmation against the existing `typed-rejection-value-tail` row).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-coord bracketing | bracket a third per-connection flag alongside `force_debug_cursor` | **1** (`acquire`/`release` pair inside the coordinator; snapshots follow) | independent |
| C2 | R-coord keying | key the active map by alias instead of wrapper object | **1** (the coordinator; the docstring's per-thread rationale is projection) | independent |
| C3 | R-wire threshold | slow cut 10s → 5s | **1** (`_SLOW_QUERY_SECONDS`; test literal + graphene shape are oracles, listed) | independent |
| C4 | R-wire key | rename `isSlow` → snake-case wire key | **1** (`_serialize_sql_row` + its TypedDict; tests follow as oracles) | independent |
| C5 | R-chain ceiling | hop ceiling 64 → 32 | **1** (local constant; [utils-typing][utils-typing] untouched — proves separation) | independent |
| C6 | R-chain terminal | retain the OUTERMOST instead of terminal `GraphQLError` | **1** (`_terminal_original_error`; collection order follows) | independent |
| C7 | R-chain gate | accept a new executed-result subtype for stashing | **1** (`_stash_payload_if_executed` `isinstance` gate; `isinstance` already covers subclasses — likely 0 moves, still 1 owner) | independent |
| C8 | R-caps marker | change the truncation marker text | **1** (`_TRUNCATION_MARKER`; both row families follow by name) | independent |
| C9 | R-caps order | admit SQL rows before exception rows under the budget | **1** (`_apply_payload_caps` pass 3; constants untouched) | independent |
| C10 | R-gate default | default `allow_unsafe_production=True` | **1** (`__init__` default + gate reading; property follows; [error-policy][error-policy] untouched — proves separation) | independent |
| C11 | R-gate setting | cache `settings.DEBUG` at construction instead of per-operation read | **1** (`_disclosure_permitted`; docstring test-context rationale is projection) | independent |
| C12 | `soft-dependency-require-guard` check | give this file a `require_debug_toolbar`-style guard | **0 exist** (no `require_*`, no optional import — grep empty) | no surface — do not inherit |
| C13 | `one-sync-boundary` check | route the capture through `run_in_one_sync_boundary` | **0 calls** (flag writes + log reads only; async bound documented) | no surface — do not inherit |
| C14 | operation-lease check | bind capture state through `OperationLease` | **0 uses** (lifetime owned by the runner via the state object) | no surface — no family named |
| C15 | R-gate bool-strictness | accept truthy strings for the acknowledgement | **1 here** (`__init__`); [error-policy][error-policy]`::ErrorPolicy.__post_init__` does NOT move (different decision) | independent — proves separation |
| C16 | mask/capture order | invert to mask-before-capture | **0 package definitions** (order owned by upstream LIFO teardown semantics; both docstrings are projections; tests are oracles) | shared upstream owner — R4 |

Read-only probes run (non-mutating, shared tree — the workspace recipe
authorizes mutating proofs, of which this item has none): `ast.parse`
enumeration above; Django `CaptureQueriesContext` source read (confirms
the save/enable/snapshot-length/restore shape this file's docstring
claims to mirror); Strawberry `SchemaExtension` hook list (confirms the
three overridden hooks and the absent `on_parse`/`on_validate`);
graphene `tracking.py`/`formating.py` reads (confirm the wire oracle
values); whole-package greps per population (`force_debug_cursor` /
`queries_log` / `isSlow|isSelect` single-sited here; `original_error`
code-reads only at the masking owner + this file; `describe_value`
consumer site fresh at 2 occurrences). No behavior an execution could
distinguish beyond what these reads show: every finding below is
`static-reviewed`, there is no `execution-deferred` proof, and no
`docs/dry/temp-tests/` scratch was created.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — overlap-safe cursor capture + log slice (file-local)

- **Contract + variation.** Every configured connection's
  `force_debug_cursor` is enabled for exactly the operation's bracket,
  overlap-safe via a lock-protected, reference-counted, immutable-record
  coordinator keyed by wrapper object (never alias); the saved value —
  not `False` — is restored by the final release; each connection's
  `queries_log` is sliced from its acquisition length with rollover
  clamping. Legitimate variation: which flags are bracketed, key
  granularity — both inside the coordinator.
- **Sites + roles.** *Definitions*: statements 30–34, 39 (token,
  snapshot, immutable record, coordinator + singleton, slice). No second
  site in the package (grep: `force_debug_cursor` / `queries_log`
  single-sited here). *Oracles*: Django's `CaptureQueriesContext`
  (save/enable/length-snapshot/restore — upstream owner of the shape;
  this file's overlap-safety + saved-value-restore are the deliberate
  superset, stated in-file); coordinator restore/unwind tests in
  [test-debug][test-debug] (independent: exercise the two seams, never
  read the map). *Consumers*: `on_operation` acquire/release call sites
  (same file). *Projections*: module docstring capture-boundaries
  passage.
- **Challenges.** C1, C2 → 1 definition (the coordinator).
- **Owner + lifetime.** `_CursorCaptureCoordinator` (existing owner by
  responsibility: the only code touching the map, saved values, and flag
  writes — its docstring says so). Stored derivation: `_ActiveCapture`
  (owner: coordinator; validity key: wrapper-object identity;
  publish point: `acquire`; mutators: `acquire`/`release` under the
  lock; invalidated: final `release` deletes the entry). Snapshots live
  on `_DebugOperationState` for one operation (F6).
- **Migration.** None (zero-edit item).
- **Distinct behavior.** Restoration safety is this rule; row
  ATTRIBUTION across nested operations is intentionally shared (outer
  payload includes inner rows — stated, tested).
- **Behavioral proof.** `static-reviewed`. Rejects "alias-keyed map
  suffices" (per-thread wrappers behind one alias — stated + Django
  connection semantics) and "second slice site exists" (grep: none).
- **Structural gate.** Pre-existing coordinator tests (restore contract,
  partial-acquisition unwind, async shared-wrapper overlap) carry their
  own failability in their owning suites; no new gate owed by this
  zero-edit item.
- **Coupling.** None.
- **Freshness.** Target
  `bf25c146111337ee0af590e7496b34c010c2f7be`,
  [extensions-operation-state][extensions-operation-state]
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9`. Searched population:
  whole package for `force_debug_cursor|queries_log` (1 file);
  `tests/` + `examples/` + `docs/` for prose consumers. Excluded on
  strength of body: Django's `CaptureQueriesContext` (upstream oracle,
  not a package definition).

### F2 — wire serializers + threshold (file-local)

- **Contract + variation.** One Django log entry → the six-key graphene
  wire row (`vendor`/`alias`/`sql`/`duration`/`isSlow`/`isSelect`;
  `isSlow` ≡ `duration > 10`; `isSelect` ≡ leading-`select` test;
  `executemany` keeps Django's raw form and is never a select); one
  exception → the `wrap_exception`-shaped triple with explicit
  `format_exception(type, exc, __traceback__)` args. Non-finite durations
  refused per row. Legitimate variation: key spellings, threshold —
  all at the two serializers.
- **Sites + roles.** *Definitions*: statements 18, 27–29, 35–36. No
  second serializer in the package (grep: `isSlow|isSelect` single-sited;
  `last_executed_query` mentioned only in this file's prose).
  *Oracles*: graphene `tracking.py` (`duration > 10`, same select test)
  + `formating.py::wrap_exception` (independent: upstream shapes the
  wire predates this port); both test tiers re-spell keys/threshold as
  literals (independent by their own stated rule). *Projections*:
  TypedDicts (same file = same edit region, not second definitions).
- **Challenges.** C3, C4 → 1 definition each.
- **Owner + lifetime.** The two serializer functions (existing owners by
  responsibility: the one place spelling the wire). No stored
  derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** Verbatim preservation (`execute()` interpolated
  vs `executemany` raw) is this rule's documented fidelity half.
- **Behavioral proof.** `static-reviewed`. Rejects "a second wire
  spelling exists" (grep: none) and "threshold shared with graphene by
  import" (literal `10`, cited as kept-verbatim — C3 moves one site).
- **Structural gate.** Pre-existing serializer tests (independent
  literals; slow cut, executemany form, interpolated SELECT) — no new
  gate owed.
- **Coupling.** None.
- **Freshness.** Target `bf25c146…` (above),
  [test-debug][test-debug]
  `eda81e523094d604eb0d2d5c62deffdc805c1ae2`,
  [test-debug-api][test-debug-api]
  `8417985a690906b8b49d4a002cc9515322c5a57e`.

### F3 — chain walk + collection guards + stash gate (file-local)

- **Contract + variation.** Nested `GraphQLError.original_error` links
  walked to the terminal exception, doubly bounded (identity set +
  `_MAX_ORIGINAL_ERROR_HOPS`), deterministic stop (last unique
  candidate); result errors filtered (`None` result / `None` errors /
  `original_error is None` skipped, order preserved, no dedup); payload
  stashed only for a graphql-core `ExecutionResult`. Legitimate
  variation: bound size, stop policy, accepted result shapes — all here.
- **Sites + roles.** *Definitions*: statements 19, 37–38, 44 (build
  half) + 48-`_stash_payload_if_executed` (shared stash writer).
  *Consumers*: the two teardowns (`on_operation` rebuild,
  `on_execute` streaming stash) call the one writer by name.
  *Oracles*: chain/cycle/ceiling tests in [test-debug][test-debug];
  no-`debug`-key tests for parse/validation shapes (both tiers).
  *Projections*: method + class docstrings (dual-teardown rationale).
- **Challenges.** C5, C6, C7 → 1 definition each.
- **Owner + lifetime.** `_terminal_original_error` /
  `_collect_exceptions` / `_stash_payload_if_executed` (existing
  owners by responsibility: the only readers of the chain/result
  shapes for diagnosis). No stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** Capture (publish originals) vs masking (strip
  them) is a separate contract — R4. The masking-order list position is
  upstream-LIFO-owned (C16).
- **Behavioral proof.** `static-reviewed`. Rejects "walk shared with
  typing peel" (nested rejection below) and "stash gate duplicated in
  the two teardowns" (both call the one writer — grep: single `def
  _stash_payload_if_executed`).
- **Structural gate.** Pre-existing chain + no-key + double-`get_results`
  tests — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `bf25c146…`,
  [extensions-error-policy][extensions-error-policy]
  `baea073f5615aaddc82c1f463071998bee7a6b62` (masking side read for
  the R4 difference).
- **Rejection (nested).** Considered: extract the hop ceiling with
  [utils-typing][utils-typing]`::MAX_TYPE_WRAPPER_DEPTH` (same number
  `64`). Contract difference: the typing peel turns over-ceiling into a
  loud `RuntimeError` (a corrupt chain must hang nothing); this walk
  turns over-ceiling/cycle into best-effort capture (a malformed
  consumer chain must fail no response). One shared constant would own
  two opposite failure policies. Trigger to reconsider: the in-file
  comment names it — a FOURTH chain-peel motivating a shared extraction
  (three peels was judged not enough). Durable home: the
  `_MAX_ORIGINAL_ERROR_HOPS` comment (already states policy difference
  + trigger).

### F4 — caps + truncation + degrades (file-local)

- **Contract + variation.** One truncation primitive + one marker for
  both row families; row-count caps keep the EARLIEST rows; one shared
  character budget (string values only) admits exception rows first,
  then SQL rows, stopping (never skipping) at the first over-budget
  row; both lists always present. SQL collection degrades per ROW
  (named function, order-preserving); log-drain failure degrades to
  rows-so-far; exception collection degrades to `[]`; every degrade
  logs server-side and never touches `data`/`errors`. Legitimate
  variation: limits, orderings, degrade granularity — all here.
- **Sites + roles.** *Definitions*: statements 20–26, 40–44. No second
  truncation primitive or cap table for this payload in the package
  (other `truncat*` hits — `resource_policy.py`, `utils/querysets.py`,
  `utils/connections.py`, `utils/errors.py`, `_request_body.py`,
  form/serializer/scalar sites — each bound a different value under a
  different contract; read: none shapes a `debug` payload).
  *Oracles*: `_apply_payload_caps` arithmetic tests + live caps wiring
  test (both tiers). *Projections*: `_apply_payload_caps` docstring
  (three passes + both orderings contractual).
- **Challenges.** C8, C9 → 1 definition each.
- **Owner + lifetime.** `_truncate` / `_row_cost` /
  `_apply_payload_caps` / `_serialized_sql_row_or_dropped` /
  `_build_payload` (existing owners by responsibility: the one place
  spelling the payload shape — `_build_payload`'s docstring claims
  exactly that). No stored derivation spanning calls (budget is a local
  counter per build); no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The per-row guarantee's scope is stated:
  per-row limits cap what an OPERATION can inflate; `vendor`/`alias`
  are deployment-fixed connection facts, not operation input (checked:
  the "far below the whole budget" claim holds within that scope —
  max row text ≈ 4–16k chars vs 262144 budget).
- **Behavioral proof.** `static-reviewed`. Rejects "whole-loop guard
  suffices" (in-file rationale: generator abandonment drops trailing
  rows — the named function exists for exactly this) and "a second cap
  table governs" (grep over cap-constant names: single-sited).
- **Structural gate.** Pre-existing caps-arithmetic + degrade tests —
  no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `bf25c146…`,
  [resource-policy][resource-policy]
  `647133d23785d325856b2d1d495d18c5741dd23c` (nearest `truncat*`
  neighbour read and excluded: different value, different contract).

### F5 — acknowledgement gate + fail-closed lifecycle (file-local)

- **Contract + variation.** Construction settles one bool behind a
  `PrivateAuthority` (never an attribute — resolvers reach the
  extension via `info.schema.extensions`); non-bool refused as
  `ConfigurationError` (truthy strings would arm the disclosure);
  `settings.DEBUG` read per operation (`getattr` with default —
  deleted/malformed fails closed; only exact `True` opens); withheld
  operations acquire nothing, snapshot nothing, publish `{}` (with one
  misconfiguration warning), and the operation itself runs normally.
  Class-entry (fresh per operation) vs acknowledgement-factory spellings
  documented; shared-instance-on-raw-schema outside the guarantee.
  Legitimate variation: acknowledgement shape, gate predicate — here.
- **Sites + roles.** *Definitions*: statements 13 (tokens), 14, 46–48
  (record, authority, lifecycle). *Single owners composed by name*:
  [utils-private-state][utils-private-state]`::PrivateAuthority`,
  [exceptions][exceptions]`::describe_value` + `ConfigurationError`
  (F7). *Oracles*: fail-closed both-directions tests, deleted-`DEBUG`
  test, non-bool construction test, per-operation freshness tests (both
  tiers). *Projections*: module/class/`__init__`/property docstrings.
- **Challenges.** C10, C11, C15 → 1 definition here each
  (`ErrorPolicy` untouched throughout — proves separation).
- **Owner + lifetime.** `DjangoDebugExtension` + `_ACKNOWLEDGEMENT`
  (existing owners by responsibility: the gate deciding what a
  production response discloses). Stored derivation lifetime
  (principle 4): owner `_ACKNOWLEDGEMENT`; validity key: extension
  identity (verified live on every recall); publish point:
  `__init__` settle; mutators: none (settle-only; reconstruction
  refused); invalidated: owner collection drops the entry.
- **Migration.** None.
- **Distinct behavior.** The read-only `allow_unsafe_production`
  property is a deployment self-check, never the gate's read (stated;
  `__dict__`-injection answered past by the descriptor).
- **Behavioral proof.** `static-reviewed`. Rejects "attribute storage
  suffices" (in-file resolver-write rationale) and "gate shared with
  error policy" (nested rejection below).
- **Structural gate.** Pre-existing gate tests (withhold + warn,
  acknowledgement publishes, malformed stays closed) — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `bf25c146…`,
  [utils-private-state][utils-private-state]
  `08088b820ac20579e471915644a931953362fca8`,
  [exceptions][exceptions]
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`,
  [error-policy][error-policy]
  `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`,
  [utils-imports][utils-imports]
  `291ecedd30c7d8af9c007758112e867c09d031eb` (R1 primitive read).
- **Rejection (nested).** Considered: unify the bool-strictness with
  [error-policy][error-policy]`::ErrorPolicy.__post_init__`'s `enabled`
  check (same `isinstance` + `ConfigurationError` + `describe_value`
  shape, cited in-file as "the same rule and the same failure shape").
  Contract difference: the policy flag decides production masking for a
  whole schema at construction; this acknowledgement decides per-class-entry
  debug disclosure per operation — posit per-operation acknowledgement
  override → only this file moves; posit policy message/key validation
  changes → only `error_policy.py` moves (C10/C15 move one side).
  Shared tokens (`describe_value`, `ConfigurationError`) are already
  single-owned and composed by name — sharing the CALL is the DRY
  answer, not sharing the two `isinstance` lines. Trigger to
  reconsider: a decision to validate every construction-time security
  bool through one named validator with one failure shape. Durable
  home: the `__init__` docstring (already records the twin).

### F6 — operation-bound state + refusal override (file-local)

- **Contract + variation.** Snapshots + payload live on
  `_DebugOperationState` (one operation's capture), never on the
  extension — so a parse failure publishes no payload rather than the
  last operation's; `_reconstruction_refusal` overrides the base's
  message with the acknowledgement-specific wording. Legitimate
  variation: per-operation scratch shape — the subclass.
- **Sites + roles.** *Definitions*: statements 15 (base import), 45,
  48-refusal + 48-`_new_operation_state`. *Owner of the mechanism*:
  [extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`
  (carrier, compatibility branch, refusal extension point — its
  docstring INVITES this override). *Oracles*: nested-operation
  attribution + concurrent-instance isolation tests (both tiers).
  *Projections*: state + class docstrings (shared-stash disclosure
  rationale).
- **Challenges.** Posit a third per-operation scratch slot → **1**
  (the subclass gains its identity; runner binding discovers it);
  posit rewording the base refusal → **0 here** (base moves; this
  override stands — proves the override is not a copy).
- **Owner + lifetime.** Operation-state subclass (existing pattern by
  responsibility: runner owns lifetime; state dies with the runner).
  `__slots__` discipline inherited from the base contract.
- **Migration.** None.
- **Distinct behavior.** Raw-schema compatibility branch lives at the
  base; this subclass adds no branch.
- **Behavioral proof.** `static-reviewed` (override is a string +
  factory method; binding behavior exercised by isolation tests on
  every suite run).
- **Structural gate.** Pre-existing isolation tests — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `bf25c146…`,
  [extensions-operation-state][extensions-operation-state]
  `b2674a22…` (above),
  [extensions-init][extensions-init]
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc` (leaf binds this class).

### F7 — `typed-rejection-value-tail` (indexed family: consumer-only)

- **Contract + variation.** Per the family owner
  ([exceptions][exceptions]`::describe_value`): a typed rejection's
  `got <this>` tail must render without ever raising. This file is the
  family's FRESHEST consumer site (verified: the owner's scope
  paragraph names `extensions/debug.py` among the deployment-supplied
  rejections, and this file carries exactly 2 `describe_value`
  occurrences — import at statement 13 + the `__init__` tail).
- **Sites + roles.** *Definition*: `exceptions.py::describe_value`
  (unchanged by this item). *Consumer*: statement 48-`__init__` raise.
  *Oracle*: non-bool construction test (independent: passes a hostile
  value, expects `ConfigurationError` — would go red if the tail
  raised). *Projection*: `__init__` docstring truthy-string passage.
- **Challenges.** Posit a new tail grammar → **1** (the owner;
  this call site follows by name); posit refusing without a tail →
  **0 here** (owner + this message move only as consumer).
- **Owner + lifetime.** `exceptions.py::describe_value` (existing
  owner; no change proposed). No stored derivation.
- **Migration.** None — consumer already composes by name; nothing to
  consolidate.
- **Behavioral proof.** `static-reviewed` (import + call read; owner
  semantics exercised by the construction test).
- **Structural gate.** The family's own (owned elsewhere); this site
  adds no gate.
- **Coupling.** None.
- **Freshness.** Target `bf25c146…`, owner
  `e06b0b7f…` (above). No index change owed: the plan's
  `typed-rejection-value-tail` row already covers `extensions/debug.py`.

### R1 — `soft-dependency-require-guard` (indexed family: rejected)

Considered: a `require_debug_toolbar`-style guard twin here (the plan
item names it). No surface: 0 `require_*` calls, 0 optional imports —
every import in statements 1–15 resolves to stdlib, hard Django /
graphql-core / Strawberry deps, or first-party modules (grep:
`require_optional_module` absent from this file AND from all of
`extensions/`; the sibling leaf artifact records the same). Contract
difference: [middleware-debug-toolbar][middleware-debug-toolbar]'s guard
defends a leaf-module import-time boundary for an OPTIONAL package
(`debug_toolbar`); this file HAS no optional package to defend, so a
guard would defend nothing. Trigger to reconsider: this extension
gaining an optional dependency (a soft client library, an alternative
cursor backend) would open a genuine guard rule owned here.
Durable home: this artifact (nothing in the target states a guard
because there is none to state; the eager-shape note lives at the leaf).

### R2 — `one-sync-boundary` (indexed family: rejected)

Considered: routing the capture through
`utils/querysets.py::run_in_one_sync_boundary`. No surface: 0 calls; the
target performs no ORM execution inside the bracket (flag writes +
`queries_log` reads only — nothing `sync_to_async` must wrap), and the
hook is one sync generator body serving both colors rather than a
sync/async twin pair. Contract difference: the family owns "ORM work
must not interleave with awaits inside a transaction"; this file's rule
is "observe the debug cursor for exactly the operation" with a
DOCUMENTED async bound (executor-thread queries escape — module
docstring). Posit moving the slice into an async hook → the hook, not
the family, moves. Trigger to reconsider: the capture gaining queryset
execution (it has none) would make the boundary rule reach it. Durable
home: the module docstring's async-execution bullet (already states the
bound).

### R3 — operation-lease use (no indexed family: checked, not named)

Considered (plan item names `operation_lease` with a question mark): 0
uses of `OperationLease` in this file. State lifetime here is owned by
the runner through the state object (F6); leases belong to scopes that
outlive the task binding them (stream resumes, whole-operation budgets
— none of which this extension arms). Check, don't inherit: no second
site, no family named, no index row owed.

### R4 — `subscription-per-event-error-masking` (indexed family: rejected)

Considered: one shared `original_error` reader with the masking side.
Contract difference: this file reads `original_error` chains to PUBLISH
unmasked originals for diagnosis (fail-closed gate, bounded payload);
the family reads them to STRIP them for production (masking last in
teardown). Same GraphQL object, opposite responsibilities — and the
only shared rule between them (debug listed AFTER masking so its
teardown runs FIRST) is owned by upstream LIFO teardown semantics, not
by either file (C16 → 0 package definitions; both docstrings are
projections; the order test is the oracle). Code-read grep: only the
masking owner + this file read `original_error` in code; `consumers.py` /
`schema.py` / `exceptions.py` hits are prose. Trigger to reconsider: a
single pipeline owning both capture and masking (one reader, two
downstream maps) would make the sites one rule. Durable home: this
file's class docstring list-order passage + the `schema.py`
admitted-chain comment (both already state it).

### R5 — debug-toolbar middleware counterpart (rejected)

Considered: one "debug surface" rule spanning this file and
[middleware-debug-toolbar][middleware-debug-toolbar]. Contract
difference: this file publishes a per-operation diagnostic INSIDE the
GraphQL response extensions map (engine seam, fail-closed under
`DEBUG`, bounded text); the middleware injects a `debugToolbar`
payload into tagged HTTP responses + HTML (server-side seam, toolbar
opt-in boundary at leaf import, panels/history store). Different
transports, different keys (`debug` vs `debugToolbar`), opposite gating
postures — unifying them would couple the response contract to the
toolbar's presence. Trigger to reconsider: a decision to drive both
surfaces from one switch (contradicts both fail-closed postures today).
Durable home: the module docstring paragraph 1 (already names the
middleware as the in-response counterpart it ports graphene's
capability alongside of — relation stated, not shared).

## Defects

None. Checked claims, all held: the `strawberry-graphql>=0.316.0`
floor (pinned at `pyproject.toml` line 40); the upstream wire shapes
(`duration > 10`, same select test, `wrap_exception` triple — read in
the installed graphene tree); the per-row guarantee's stated scope
(per-row limits cap operation-inflatable text; `vendor`/`alias` are
deployment-fixed — the docstring already scopes it so); the
`getattr`-vs-direct `original_error` difference from the masking read
(distinct failure policies, Matrix axis 6 — resolved, not routed). The
axis-6 sweep finds no member lacking a guard its contract requires.

## Pending execution

None. No `execution-deferred` proof: all findings are
`static-reviewed` on read-only probes, and every behavior is exercised
by the two existing tiers on every suite run.

## Judgment

Zero-edit file item. Six definition rules traced, all file-local with
proving challenges (C1–C11, C15); one indexed family confirmed
consumer-only (`typed-rejection-value-tail`, F7 — files-covered already
names this file, no index change owed); three indexed families rejected
with contract difference + trigger + home (`soft-dependency-require-guard`
R1, `one-sync-boundary` R2, `subscription-per-event-error-masking` R4);
`operation_lease` checked with no surface and no family named (R3);
toolbar-counterpart, hop-ceiling, and bool-strictness separations
rejected with homes in standing prose (R5, F3/F5 nested). No defects,
no pending execution, no production edits. Worker 0 owes six
`## Responsibility index` file-local rows (F1–F6); F7 confirms the
existing family row; R1/R2/R4 carry the cycle's triggers.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `cb8743a8050bdf51b129700261aa5a4e487f2c63`:
`git diff <baseline> -- django_strawberry_framework/extensions/debug.py`
empty; working blob `bf25c146111337ee0af590e7496b34c010c2f7be` matches
`HEAD:django_strawberry_framework/extensions/debug.py` — target CLEAN,
so no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-extensions__debug.md`) is a new untracked file, the
item's only output. No `uv run ruff format .` / `ruff check` run (no
edits to format). No shared-tree pytest run. No `docs/dry/temp-tests/`
scratch created (read-only probes only — see `### Challenges` note; a
probe could distinguish nothing a mutating run would change). Concurrent
dirt listed in the dispatch (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus the
other untracked `dry-file-*.md` artifacts were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no
row from this item. No commit.

## Independent verification (Worker 2)

Own trace first, recorded BEFORE reading `## Findings` (reconciliation follows).
Target re-read in full (862 lines confirmed). Connected surfaces re-read, not
taken on trust: [middleware-debug-toolbar][middleware-debug-toolbar] (full),
[extensions-operation-state][extensions-operation-state] (carrier + refusal
extension point + runner binding, full), `extensions/error_policy.py`
`original_error` reads (direct access + degrade paths), `error_policy.py`
bool gate, `utils/typing.py` peel policy, `describe_value` occurrences, and
`tests/extensions/test_debug.py` heads + serializer/gate bodies.

Own rules, with the owners I would choose and definition counts per posited
change (consumers / oracles / projections listed, never counted):

- **T1 cursor capture + log slice** (token, snapshot, immutable record,
  coordinator + singleton, slice). Change: bracket a third flag / re-key by
  alias → **1** definition. Owner: `extensions/debug.py::_CursorCaptureCoordinator`.
- **T2 wire serializers** (slow threshold, 3 TypedDicts, 2 serializers).
  Change: 10s → 5s / rename `isSlow` → **1** each. Owner: the two serializer
  functions.
- **T3 chain walk + guards + stash gate** (hop ceiling, walk, collector,
  one stash writer, two teardowns calling it). Change: ceiling 64 → 32 /
  outermost-instead-of-terminal / new result subtype → **1** each. Owner:
  `_terminal_original_error` / `_collect_exceptions` /
  `DjangoDebugExtension._stash_payload_if_executed`.
- **T4 caps + truncation + degrades** (6 cap constants, marker, `_truncate`,
  `_row_cost`, `_apply_payload_caps`, per-row drop, `_build_payload`).
  Change: marker text / SQL-before-exceptions budget order → **1** each.
  Owner: `_truncate` / `_apply_payload_caps` / `_build_payload`.
- **T5 acknowledgement gate + lifecycle** (record, authority, extension + 9
  methods). Change: default-True / cache-DEBUG-at-construction /
  accept-truthy-strings → **1 here** each (`ErrorPolicy` untouched throughout).
  Owner: `DjangoDebugExtension` + `_ACKNOWLEDGEMENT`.
- **T6 operation-bound state + refusal** (subclass + slots + refusal
  override + factory). The mechanism is owned by
  [extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`
  (its docstring INVITES the refusal override); the subclass/refusal is one
  local declaration, not a second definition. Owner of the local half:
  `_DebugOperationState`.
- **T7 tail call** (`describe_value` import + 1 call site = exactly 2
  occurrences). Consumer of `exceptions.py::describe_value`; **0**
  definitions here.

Reconciliation vs W1 (T1–T7 map onto F1–F7 with the same owners and the same
counts on every challenge C1–C11, C15): full agreement on verdicts, with one
prose qualification. W1's Matrix-5/Challenges prose says the test tiers
re-spell wire expectations "never importing the serializers"; the test module
in fact imports `_serialize_exception`, `_serialize_sql_row`,
`_collect_exceptions`, `_terminal_original_error`, `_apply_payload_caps`,
`_build_payload` (own module head) and calls them. Oracle independence still
holds in substance — expectations are independent literals (`set(row) ==
{...}`, boundary values `10.0 → False` / `10.5 → True`, literal cap
constants), so a key rename or threshold move fails; calling the unit under
test is not reading the oracle from the owner, and no oracle was rewritten.
Not a defect (untracked cycle-closing prose, no contract row broken); noted
for precision only.

Enumeration (member-by-member vs own `ast.parse` count): **49 statements
(0–48)**, mapping matches W1 row-for-row — 0 docstring; 1–3 stdlib imports;
4–7 stdlib-from imports; 8–9 Django; 10–11 graphql-core; 12 logger; 13
exceptions tokens; 14 `PrivateAuthority`; 15 operation-state base; 16
`TYPE_CHECKING`; 17 `__all__`; 18 threshold; 19 hop ceiling; 20–25 six caps;
26 marker; 27–29 TypedDicts; 30–32 token/snapshot/record; 33 coordinator;
34 singleton; 35–44 ten functions; 45 state; 46 record; 47 authority; 48
extension + 9 methods + refusal. Every member lands in W1's homes; nothing
unassigned; no second site for any definition row (population greps
re-run: `force_debug_cursor` / `queries_log` / `isSlow|isSelect` single-sited
here; `original_error` code-reads only at the masking owner + this file;
`require_*` / `run_in_one_sync_boundary` / `OperationLease` absent here).

Findings judged: F1–F6 file-local — endorsed (each carries contract +
variation, roles, challenges with count 1, owner, static proof, coupling
none). F3/F5 nested rejections — endorsed (typing peel raises where this
walk keeps best-effort; `ErrorPolicy.enabled` vs per-operation
acknowledgement move independently per C10/C15; shared tokens already
single-owned and composed by name; durable homes in standing in-file
comments). F7 consumer-only — endorsed (plan's `typed-rejection-value-tail`
row already covers `extensions/debug.py`; no index change). R1/R2/R4
rejected with difference + trigger + home — endorsed (0 `require_*` / 0
boundary calls / publish-originals vs strip-them; triggers ride the existing
family items). R3 checked-no-surface — endorsed (no `operation_lease` family
row exists in the plan, only a file item; no row owed). R5 toolbar
counterpart — endorsed and verified against the real surface (HTTP
middleware injecting `debugToolbar` + HTML bridge vs in-response `debug`
map; import-time soft-dep guard vs fail-closed `DEBUG` gate; relation
already stated in the module docstring, not shared).

Fingerprints re-hashed (working tree; all cited files clean vs `HEAD`, so
working blob = `HEAD` blob): target `bf25c146…` match; operation-state
`b2674a22…` match; ext-error-policy `baea073f…` match; private-state
`08088b82…` match; exceptions `e06b0b7f…` match; error-policy `fa94fcd9…`
match; utils-imports `291ecedd…` match; ext-init `dc3ebdc2…` match;
resource-policy `647133d2…` match; test-debug `eda81e52…` match;
test-debug-api `8417985a…` match. Two supplemental blobs for inputs W1 read
but did not fingerprint (recorded here so the rejections are staleness-bound):
middleware-debug-toolbar `5360149b…`, utils-typing `de6309f6…`.

Negative controls / gates: zero-edit item proposes no consolidation, so no
new gate is owed; the cited pre-existing suites (serializer key sets,
threshold boundaries, chain/cycle/ceiling, caps arithmetic, fail-closed both
directions, non-bool refusal, coordinator restore/unwind/overlap, isolation)
are supporting evidence, not structural gates in the DRY.md sense. The final
gate executes them. `## Pending execution` absent — adequate for this file:
every rule's variation axes are pure-function or construction-time decisions
fully determined by the read bodies; the ordering/async behaviors (LIFO
mask-order, executor-thread bound) are already executed by the two existing
tiers on every suite run, and no W1 edit created behavior needing fresh
proof. No probe was run per dispatch; none is owed.

AGENTS.md prose check: item-scoped diff
`git diff cb8743a8050bdf51b129700261aa5a4e487f2c63 --
django_strawberry_framework/extensions/debug.py` is EMPTY (confirmed
directly); working blob `bf25c146…` == `HEAD` blob — no code rules
triggered, no ruff run owed. Artifact: `path::Symbol` citations,
reference-style links with the 10-group block intact, no process
provenance, no commit. Concurrent dirt (working `connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, untracked
`dry-file-*.md` artifacts) left untouched; none is in this item's paths.

Defects (Worker 2): none. Axis-6 sweep agrees — no member lacks a guard its
contract requires; the `getattr`-vs-direct `original_error` separation is
resolved by differing failure policies, not routed.

Verdict: `Status: verified`, no pending execution. Worker 0 owes six
`## Responsibility index` file-local rows (exact lines below); F7 confirms
the existing `typed-rejection-value-tail` row unchanged; R1/R2/R4 triggers
ride their existing family items; R3/R5 and the nested F3/F5 rejections need
no rows (homes in standing prose / in-file comments).

```text
| Overlap-safe cursor capture + log slice | `django_strawberry_framework/extensions/debug.py::_CursorCaptureCoordinator` | `django_strawberry_framework/extensions/debug.py` | File `extensions/debug.py` | file-local |
| Wire serializers + threshold | `django_strawberry_framework/extensions/debug.py::_serialize_sql_row` (+ `::_serialize_exception`) | `django_strawberry_framework/extensions/debug.py` | File `extensions/debug.py` | file-local |
| Chain walk + collection guards + stash gate | `django_strawberry_framework/extensions/debug.py::_terminal_original_error` (+ `::_collect_exceptions`, `::DjangoDebugExtension._stash_payload_if_executed`) | `django_strawberry_framework/extensions/debug.py` | File `extensions/debug.py` | file-local |
| Caps + truncation + degrades | `django_strawberry_framework/extensions/debug.py::_apply_payload_caps` (+ `::_truncate`, `::_build_payload`) | `django_strawberry_framework/extensions/debug.py` | File `extensions/debug.py` | file-local |
| Acknowledgement gate + fail-closed lifecycle | `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension` (+ `::_ACKNOWLEDGEMENT`) | `django_strawberry_framework/extensions/debug.py` | File `extensions/debug.py` | file-local |
| Operation-bound state + refusal override | `django_strawberry_framework/extensions/debug.py::_DebugOperationState` (mechanism at `extensions/operation_state.py::_OperationBoundExtension`) | `django_strawberry_framework/extensions/debug.py` | File `extensions/debug.py` | file-local |
```

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[consumers]: ../../django_strawberry_framework/consumers.py
[error-policy]: ../../django_strawberry_framework/error_policy.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-private-state]: ../../django_strawberry_framework/utils/private_state.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-debug]: ../../tests/extensions/test_debug.py
[test-debug-api]: ../../examples/fakeshop/test_query/test_debug_extension_api.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
## Bounded re-review at bfaee91d (Worker 2, Q9)

Phase 1 trace only. No status set. No verdict on prior findings proposed.
Target bytes are HEAD bytes. Zero edits made.

### Scope and clean confirmation

- Target: `django_strawberry_framework/extensions/debug.py`, whole file, current HEAD bytes.
- Clean: yes for the target. Worktree `git hash-object` equals `HEAD:` blob, and
  `git status --short` names no debug path. HEAD is `bfaee91d`.
- Delta established by the worker itself from
  `git diff 9031cb3d..bfaee91d -- django_strawberry_framework/extensions/error_policy.py`:
  (a) shared floor addition: new `extensions/error_policy.py::degraded_result`
  plus one `__all__` entry; (b) three floor-line swaps from the inline
  `StrawberryExecutionResult(data=None, errors=[_degraded(policy)])` spelling to
  `degraded_result(policy)` in `extensions/error_policy.py::mask_execution_result`,
  `extensions/error_policy.py::DjangoErrorPolicyExtension._process_result`, and
  `extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation`;
  (c) docstring update: module docstring two seams to three seams (hook-escape
  result built after teardowns, seam at `schema.py::DjangoSchema._masked_return`,
  idempotence by construction, plain-`strawberry.Schema` caveat, one impl three
  sites), plus `on_operation` docstring update for the same third seam.
- Worktree dirt note (preserved, out of scope): `extensions/error_policy.py`
  worktree differs from HEAD by one docstring sentence about the three sites
  becoming one only under a future single engine hook. It is concurrent work,
  not part of the `9031cb3d..bfaee91d` delta, and this trace reads HEAD bytes
  for the delta. All other dirty paths were ignored as concurrent work.
- Contracts applied: DRY.md principle 5 (shared lifecycle plus adapters) and
  principle 7 (choose the owner by responsibility). Tests read as oracles only.

### (1) Debug observation surface, with roles

All definitions below live in `django_strawberry_framework/extensions/debug.py`.
Tests are independent oracles. Docstrings are projections.

Hooks (each a definition in `debug.py`):

- `extensions/debug.py::DjangoDebugExtension.on_operation`: one sync generator
  serving both execution colors. Pre-yield: fail-closed gate first
  (`_disclosure_permitted`), then `ExitStack` acquires one
  `extensions/debug.py::_CursorCaptureCoordinator.acquire` token plus one
  `extensions/debug.py::_ConnectionSnapshot` per configured connection.
  Post-yield in `finally`: calls
  `extensions/debug.py::DjangoDebugExtension._stash_payload_if_executed`.
  Definition; consumers: the engine operation lifecycle.
- `extensions/debug.py::DjangoDebugExtension.on_execute`: teardown stashes the
  moment graphql-core returned, covering the streaming seam where the engine
  reads extension results inside the still-open operation context. Calls the
  same one stash writer. Inert when state or snapshots is `None`. Definition.
- `extensions/debug.py::DjangoDebugExtension._stash_payload_if_executed`: the
  one stash writer shared by the two teardowns. Publishes only when
  `execution_context.result` is graphql-core `ExecutionResult`
  (`GraphQLExecutionResult`); sync parse/validation `None` and async
  strawberry `PreExecutionError` stash nothing. Definition; consumers: the two
  teardowns above.
- `extensions/debug.py::DjangoDebugExtension.get_results`: pure idempotent read
  of the stashed payload (`{"debug": payload}` once published, else `{}`).
  Never mutate-or-pop, never writes `execution_context` or a result map.
  Definition.
- State: `extensions/debug.py::_DebugOperationState` (subclass of
  `extensions/operation_state.py::OperationState`) with `snapshots` and
  `payload`; `None` means never bracketed (inert fail-closed path, hook
  entered outside an operation). Built by
  `extensions/debug.py::DjangoDebugExtension._new_operation_state`.
  Definition; the per-operation adapter under principle 5.

Payloads recorded (each a definition in `debug.py`):

- SQL rows: `extensions/debug.py::_query_log_entries_since` slices each
  snapshot log, `extensions/debug.py::_serialized_sql_row_or_dropped`
  serializes per row (drop-one-row degrade, log order preserved),
  `extensions/debug.py::_serialize_sql_row` builds the six-key wire row
  (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`; `isSlow` from
  `extensions/debug.py::_SLOW_QUERY_SECONDS`; verbatim interpolated statement;
  non-finite duration refused). Whole-log-drain failure degrades to rows so
  far in `extensions/debug.py::_build_payload`. Definitions.
- Exception rows: `extensions/debug.py::_collect_exceptions` owns the
  `result is None` / `errors is None` guards and the `original_error is None`
  filter (graphql-core parse/validation marker); preserves result-error order,
  never deduplicates. `extensions/debug.py::_terminal_original_error` walks
  nested `GraphQLError.original_error` doubly bounded (identity set plus
  `extensions/debug.py::_MAX_ORIGINAL_ERROR_HOPS`); malformed chains degrade
  to best-effort terminal, terminal `GraphQLError` retained.
  `extensions/debug.py::_serialize_exception` builds `excType` / `message` /
  `stack` from explicit `format_exception` args. Whole-collection failure
  degrades to `[]` in `_build_payload`. Definitions.
- Caps: `extensions/debug.py::_apply_payload_caps` (three fixed-order passes:
  per-row truncation, earliest-row count caps, one shared text budget with
  exceptions admitted before SQL, stop-at-first-over-budget), with
  `extensions/debug.py::_truncate`,
  `extensions/debug.py::_TRUNCATION_MARKER`,
  `extensions/debug.py::_row_cost` (string values only), and limits
  `_MAX_SQL_ROWS`, `_MAX_EXCEPTION_ROWS`, `_MAX_SQL_TEXT_CHARS`,
  `_MAX_EXCEPTION_MESSAGE_CHARS`, `_MAX_EXCEPTION_STACK_CHARS`,
  `_MAX_PAYLOAD_TEXT_CHARS`. Both lists always present. Definitions.
- Coordinator: `extensions/debug.py::_CursorCaptureCoordinator` (sole toucher
  of the active map, saved flags, and `force_debug_cursor`; keyed by concrete
  wrapper, first bracket saves and enables, last release restores saved value,
  lock covers transition plus write), `extensions/debug.py::_ActiveCapture`,
  `extensions/debug.py::_CaptureToken`, `extensions/debug.py::_ConnectionSnapshot`.
  Definitions.
- Disclosure gate: `extensions/debug.py::DjangoDebugExtension._acknowledged`
  (via `extensions/debug.py::_ACKNOWLEDGEMENT` private authority),
  `extensions/debug.py::DjangoDebugExtension._disclosure_permitted`
  (acknowledged OR `settings.DEBUG is True` exact bool, read per operation),
  `extensions/debug.py::DjangoDebugExtension.__init__` bool validation
  (non-bool is `ConfigurationError`), read-only
  `extensions/debug.py::DjangoDebugExtension.allow_unsafe_production`.
  Definitions.

Oracles read (not definitions, not edited): `tests/extensions/test_debug.py`
(serializers, chain handling, coordinator restore, slicing, `get_results`
no-stash/idempotence and raising-teardown recovery, masking ordering both
directions, merge precedence, async overlap, nesting, concurrency isolation,
caps arithmetic), `examples/fakeshop/test_query/test_debug_extension_api.py`
(live wire keys, duration, parse/validation no-`debug`-key, malformed `DEBUG`,
mutation intervals), `tests/test_error_policy.py` copy-contract section,
`examples/fakeshop/test_query/test_error_policy_api.py` hook-failure rows
(one entry plus one log record, idempotent teardown plus return seam).

### (2) Masking references in debug.py, with roles

Exhaustive over current HEAD bytes. No import, no call, no shared floor, no
shared lifecycle body with the masking implementation. Shared lifecycle only
via the operation-state owner (principle 5).

- Imports: `debug.py` imports stdlib, Django settings/connections, graphql
  `ExecutionResult`/`GraphQLError`, `logger`, `ConfigurationError` /
  `describe_value`, `PrivateAuthority`, and
  `extensions/operation_state.py::OperationState` plus
  `extensions/operation_state.py::_OperationBoundExtension`. It does NOT import
  `mask_execution_result`, `masking_is_active`, `is_maskable_result`,
  `degraded_result`, `_degraded`, `DjangoErrorPolicyExtension`, or
  `schema.py::DjangoSchema._masked_return`. Role: no consumer site.
- Calls: zero calls to any of the above masking symbols anywhere in `debug.py`.
  Verified by import-block read plus whole-file search (only prose hits).
  Role: no consumer site.
- Floors: `debug.py` never calls `degraded_result` and never spells the
  whole-response floor (`data=None` plus single policy message). Its floors
  are local and different in kind: per-row drop, per-list empty degrade, and
  deterministic bounding. Different contract (diagnostic completeness) from
  the masking floor (disclosure prevention). Role: intentional separation,
  not a second definition of the same rule.
- Prose references only (projections, never definitions or consumers):
  module docstring unmasked-disclosure warning plus LIFO ordering rule naming
  `MaskErrors` stripping `original_error` (list debug after masking or
  `exceptions` reads `[]`); class docstring list-after-masking rule, streaming
  pre-masking payload note, transport-masks-frames note, rebuild-pass comment
  pinning the masking-order behavior; `__init__` docstring analogy to
  `error_policy.py::ErrorPolicy.__post_init__` bool rule (same shape, separate
  owner); `_MAX_ORIGINAL_ERROR_HOPS` comment deliberately NOT importing the
  typing ceiling (failure policy differs; stays local until a fourth peel
  motivates extraction).
- Shared lifecycle (principle 5): both debug and error-policy extensions
  derive from `extensions/operation_state.py::_OperationBoundExtension` and
  are bound by `extensions/operation_state.py::DjangoExtensionsRunner`. That
  shared body is owned in `operation_state.py`. Debug contributes only its
  adapter (`_DebugOperationState`, bracket plus stash); error policy
  contributes only its adapter (classify plus mask plus adopt). Ordering
  between them is engine LIFO, not a shared-body call. Role: fellow adapters
  under one lifecycle owner, not co-owners of either rule.
- Reverse direction (recorded for completeness, not debug sites):
  `extensions/error_policy.py` prose names
  `extensions/debug.py::DjangoDebugExtension` for the copy-preserving mask
  contract and front-insert position; `schema.py` prose names it as a consumer
  extension example; `extensions/operation_state.py` prose names the debug
  payload and the mask as ordering examples. All projections.

### (3) Definition counts

Change challenge counts. Consumers, oracles, and projections that also move
are listed, never counted.

- C1, whole-response floor content (message, `data=None`, no location, no
  correlation id): definitions forced = 1,
  `extensions/error_policy.py::degraded_result` (wrapping
  `extensions/error_policy.py::_degraded`). Consumers, not definitions: the
  three swapped teardown call sites plus `schema.py::DjangoSchema._masked_return`
  plus oracles (`tests/test_error_policy.py` return-seam rows, live hook rows).
  Debug contributes 0 and calls 0; its per-row/empty-list degrades do not move
  under this change. Before the delta the same rule was spelled 3 times
  inline; after, 1 definition with 4 consumers. No second definition in
  `debug.py`.
- C2, new observed surface for debug (new result shape admitted as executed,
  e.g. treat strawberry `PreExecutionError` as executed, or a new engine
  result subclass): definitions forced = 1,
  `extensions/debug.py::DjangoDebugExtension._stash_payload_if_executed`
  `isinstance` gate. `extensions/error_policy.py::is_maskable_result` does not
  move with it: it admits both graphql-core and strawberry shapes for masking,
  a different rule with different reasons to change (maskability vs
  executed-ness). Count stays 1, even with identical-looking `isinstance`
  text. Same for a new capturable field or row key: 1 definition in the owning
  serializer or cap helper.
- C3, new hook (engine adds a lifecycle hook, or a new masking seam is added
  beside the three): debug stash-writer definitions forced = 1
  (`_stash_payload_if_executed`); a new debug teardown would be a third
  consumer, not a second definition. Masking-implementation definitions forced
  = 1 each (`mask_execution_result`, `is_maskable_result`,
  `masking_is_active`); a new seam would be a fourth/fifth consumer calling
  them by name, as `_masked_return` already does. The delta itself is this
  shape: 1 new floor definition, 0 new hook definitions in `debug.py`.

### (4) Owners the worker would choose (principle 7)

- Whole-response masking floor: `extensions/error_policy.py::degraded_result`
  (as the delta chose). Responsibility: fail-closed disclosure prevention with
  real consumers on every seam (operation teardown, per-event mask path,
  schema return). Narrowest cohesive owner every legitimate consumer can
  depend on without reversing a dependency or importing a sibling flavor
  (`schema.py` and `consumers.py` already depend on the error-policy module;
  `debug.py` must not). Debug must neither own nor mirror it.
- Masking implementation and gates (`mask_execution_result`,
  `is_maskable_result`, `masking_is_active`, `_degraded`, `_masked`,
  `_replacement_for`, `_is_unexpected`): `extensions/error_policy.py` (as is).
  `schema.py::DjangoSchema._masked_return` and
  `consumers.py::_stop_aware_results` stay consumers.
- Debug observation lifecycle, payload shape, serializers, caps, coordinator,
  disclosure gate: `extensions/debug.py` (as is). Considered and rejected:
  sharing truncation/budget with masking (different contracts, would couple
  independent domains); sharing bool validation with `ErrorPolicy`
  construction (same shape, separate reasons to change; analogy prose is
  correct as projection); extracting the `original_error` walk until the
  stated fourth-peel trigger (per the owner comment).
- Shared operation lifecycle: `extensions/operation_state.py`
  (`_OperationBoundExtension`, `OperationState`, `DjangoExtensionsRunner`)
  (as is). Both extensions stay adapters. Engine LIFO itself is upstream and
  unowned here; the package list-order contract stays recorded as projections
  at both adapters plus the chain builder, which is the principle 5
  record-the-contrast shape, not a new shared owner.

### (5) Whether the delta breaks anything derived

No. The delta changes no behavior the trace above depends on, and no contract
row is broken. No defect is recorded (a defect would need the breached
contract row plus the feasible project shape plus the wire or configuration
input reaching it; none exists).

- Floor extraction plus three swaps: behavior-preserving by construction
  (identical expression behind one name, same policy argument, same
  `_degraded` body, same logging). Observable behavior on every axis of
  principle 8 is unchanged: same type returned, same `data=None`, same single
  error, same short-circuit order, same exceptions raised (none new), same
  query effects (none).
- Interaction with debug: `debug.py` gates only on graphql-core
  `ExecutionResult`, while the floor builds a strawberry `ExecutionResult`;
  that relation is identical before and after, so the no-`debug`-key contract
  on non-executed results (oracles: raising-teardown recovery rows,
  parse/validation rows, async `PreExecutionError` row) is untouched. The
  degraded errors carry `original_error=None`, which both the masking
  classifier (deliberate, leave alone; idempotent teardown plus return) and
  `debug.py::_collect_exceptions` (skip) already read the same way; the
  spelling move does not change what either reads.
- Copy-preserving masking (`mask_execution_result` shallow copy leaving the
  engine-assigned `execution_context.result` originals for LIFO-ordered debug
  teardown) and the `_masked_return`-on-the-returned-value separation are
  untouched by the delta; masking-order oracles (debug-after-masking sees one
  original row, debug-before-masking sees `[]`) and hook-failure oracles (one
  masked entry plus one log record across `HOOK_ROWS`; DEBUG pass-through and
  opt-out twins) still describe the same code paths.
- Docstring update: projection only. It documents the pre-existing third seam
  the oracles already pin; it adds no hook, no import, and no `debug.py` edit.

### (6) Freshness fingerprints

Method: `git hash-object <path>` on worktree bytes; `git show HEAD:<path> |
git hash-object --stdin` where HEAD comparison matters; `git rev-parse` for
commits. Target clean means worktree blob equals HEAD blob plus no status
entry for the path.

- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e`.
- Delta base: `9031cb3dde0b2a3bee49992994a370738e106b15`.
- Delta command: `git diff 9031cb3d..bfaee91d --
  django_strawberry_framework/extensions/error_policy.py`.
- `django_strawberry_framework/extensions/debug.py`: worktree
  `bf25c146111337ee0af590e7496b34c010c2f7be`, `HEAD:` same
  `bf25c146111337ee0af590e7496b34c010c2f7be`; status clean for this path.
- `django_strawberry_framework/extensions/error_policy.py`: base blob
  `baea073f5615aaddc82c1f463071998bee7a6b62`, HEAD blob
  `16f475471a8b8295117640f7b14d949603d7bbc0`, worktree blob
  `bd763bcc428ce0f495448e6d228061dd0bc08688` (one extra docstring sentence vs
  HEAD; concurrent dirt, excluded; delta trace uses HEAD bytes).
- `django_strawberry_framework/extensions/operation_state.py`:
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9` (worktree equals `HEAD:`).
- `django_strawberry_framework/schema.py`:
  `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5` (worktree equals `HEAD:`).
- `django_strawberry_framework/consumers.py`:
  `936210e2993ddca4b77ffebf65e728f59d17079c`.
- `docs/dry/DRY.md`: `e8151123ff7e129fe9881ec342231e9e1795148e`.
- `docs/dry/worker-2.md`: `4f089ea4a58d73295638e83abf8c612bf31487f8`.
- `AGENTS.md`: `e42247fa310bf7a85914d7efa7f177ee5307b860`.
- Oracles read: `tests/extensions/test_debug.py`
  `eda81e523094d604eb0d2d5c62deffdc805c1ae2`;
  `tests/test_error_policy.py`
  `9ff5328eaed329a5fd69ac2e7002cf0052452241`;
  `examples/fakeshop/test_query/test_error_policy_api.py`
  `9a425677bb9763cb05776e0521afa06ad4197307`;
  `examples/fakeshop/test_query/test_debug_extension_api.py`
  `8417985a690906b8b49d4a002cc9515322c5a57e`.
- Searched population: `django_strawberry_framework/extensions/` (debug,
  error_policy, operation_state, `__init__`), `schema.py` masked-return seam,
  `consumers.py` result-source seam, plus the oracle files above. Excluded on
  body strength: remaining package modules import or call none of the
  masking/degraded symbols (whole-package grep for `mask_execution_result`,
  `degraded_result`, `is_maskable_result`, `DjangoDebugExtension` reviewed;
  only the named sites reference them). Any fingerprint change reopens this
  trace.

PHASE-1-TRACE-RECORDED docs/dry/dry-file-extensions__debug.md
