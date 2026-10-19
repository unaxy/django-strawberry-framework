# DRY review: `django_strawberry_framework/consumers.py`

Status: verified
Run: 0.0.15 2026-09-19-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one REUSED plan family (re-challenged fresh on the
consumer side), one NEWLY NAMED family for Worker 0 to index (no production
edit here; the family item owns the sweep and the decision), a file-local
record with its proving challenge, or a recorded rejection with difference +
trigger + home. Zero production edits; zero tracked files changed.

## System trace

Mid-size target (2087 lines, 46 top-level statements, working == HEAD). The
package's WebSocket-transport module, owning two independent things: the
handshake-time Host boundary (`consumers.py::DjangoWebSocketHostValidator`,
its projection `consumers.py::_host_validation_request`) and the revalidating
consumer factory (`consumers.py::build_revalidating_consumer_class`) with its
two actor-revalidation checkpoints (admission
`consumers.py::revalidate_operation_actor`, outbound
`consumers.py::send_revalidated_operation_frame`), the one shared actor
decision (`consumers.py::_actor_is_current`), the one revocation entry
(`consumers.py::_revoke_connection`), the five-state close machine
(`consumers.py::_ConnectionRevocation`), the stop-aware result seam
(`consumers.py::_stop_aware_results`, `consumers.py::_StopAwareSchema`,
`consumers.py::_install_stop_aware_schema`), the loop containment
(`consumers.py::_contain_message_loop_failure`), the actor refresh
(`consumers.py::_refreshed_actor`), and the window validation
(`consumers.py::resolved_revalidation_window`). It CONSUMES by name every
other rule it touches: the connection actor lease + provenance + store
resolver (`utils/sessions.py`), the per-event masking API
(`extensions/error_policy.py`), the tail renderer (`exceptions.py`),
`channels.auth.get_user`, Django's `HttpRequest.get_host`, and upstream's
close codes / handler attributes / result-source names.

Connected code read for judgment, outside the item:
`django_strawberry_framework/routers.py` (import block,
`routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`,
`routers.py::_ROUTER_CLASS` cache, the `_build_router_class` window +
consumer-class arms, the Host/Origin/Auth composition);
`django_strawberry_framework/utils/sessions.py` (whole module, 408 lines:
`utils/sessions.py::scope_key`, `utils/sessions.py::scope_singleton`,
`utils/sessions.py::session_store_class`,
`utils/sessions.py::ConnectionActorState`,
`utils/sessions.py::connection_actor_state`,
`utils/sessions.py::note_authenticated_actor`,
`utils/sessions.py::connection_was_authenticated`,
`utils/sessions.py::actor_lease`, `utils/sessions.py::actor_transition`);
`django_strawberry_framework/extensions/error_policy.py` (module head +
`extensions/error_policy.py::masking_is_active`,
`extensions/error_policy.py::is_maskable_result`,
`extensions/error_policy.py::schema_error_policy`,
`extensions/error_policy.py::mask_execution_result` def lines);
`django_strawberry_framework/views.py::resolved_max_request_body_bytes`
(full body + docstring, the shaped-after source);
`django_strawberry_framework/exceptions.py::describe_value` (full body +
scope docstring) and `exceptions.py::ConfigurationError` (def line);
`django_strawberry_framework/auth/mutations.py::_channels_logout` (full
body: the transition side of the shared lease) and
`auth/mutations.py::_channels_http_login_establish` (def line, the
function-local-import precedent);
`django_strawberry_framework/auth/sessions.py` (def census:
`auth/sessions.py::scope_session_lock`,
`auth/sessions.py::logout_supported`, and the opt-in-eager-import shape);
`tests/test_consumers.py` (full `def test` census, 90+ rows; bodies read
for the window-OverflowError row, one cancellation row, the hostile-scope
rows' titles) plus `tests/test_routers.py` (the no-auth-import eviction
row body, the stop-aware partition row body, window/host/revocation row
titles); installed upstream `.venv` `strawberry 0.324.0`
(`subscriptions/protocols/graphql_transport_ws/handlers.py`:
`schema.stream`, 4403/Forbidden connect refusal, incremental-frame
rejection, `aclosing`, `handle`/`handle_message`;
`graphql_ws/handlers.py`: `schema.subscribe`, 1011 arm;
`schema/schema.py`: `subscribe`/`stream`/`execute` defs;
`channels/auth.py`: `get_user` + `database_sync_to_async`;
`channels/security/websocket.py`: `OriginValidator`,
`AllowedHostsOriginValidator`, `WebsocketDenier`).

Excluded with reason: the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) - never touched, not in this finding's sites;
in-flight spec bodies behind the Decision pointers (spec-040/046/048
cited as pointers, defaults pinned by oracles instead);
`docs/GLOSSARY.md` entries (projections, not relied upon);
`optimizer/*`, `connection.py`, `list_field.py`, `middleware/*`,
`conf.py` bodies beyond the cited seams (other families' surface);
other files' `except BaseException` bodies (the package-wide mechanism
sweep belongs to a family item; this item counts only this file's 38
sites); the floor wheel `strawberry-graphql==0.316.0` (version-range
claims below verified against installed 0.324.0 source + the partition
test, not against the floor wheel - stated per finding, no verdict
depends on it); concurrent dirt (`connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) - read
where needed as oracles, never edited.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** No sibling flavor revalidates a
socket actor: HTTP re-authenticates per request through middleware,
mutations/forms/DRF have no connection to revoke. The one genuine twin
shape is the numeric-setting validator (`resolved_revalidation_window`
vs `views.py::_resolved_max_request_body_bytes`) - recorded as rejection
J1, not a family. The tail renderer both call is the new family F4. The
eviction oracle (`test_routers.py` no-auth-import row, body read) proves
the `utils/sessions.py` placement is load-bearing, not taste.

**2. Sync/async twins.** None in target, by construction: Channels
consumers are async-only, and every checkpoint, the revocation machine,
the result seam, and the containment are single-colored. The sync HTTP
twin (`views.py`) shares no checkpoint with this module - checked, not
assumed: no `sync_to_async`/`async_to_sync` bridge exists here, and the
one sync-boundary rule this file touches
(`utils/querysets.py::run_in_one_sync_boundary`) is obeyed negatively
(F1). No behavioral pair to compare.

**3. Derived rather than repeated knowledge.** Five facts this file could
have respelled are composed by name: the revocation close is upstream's
own 4403/Forbidden connect-refusal shape (R1, verified in installed
source); the invalid-message close is the transport-ws handler's own
4400 shape (R5); Host matching is Django's `get_host` (R14); the scope
key is built by `utils/sessions.py::scope_key` (R7); the router's window
default IS this module's constant by import, never a second literal
(R6, probe `router-window-default`). The `_HOST_META_KEYS_BY_HEADER`
projection reproduces the ASGI adapter's treatment key-for-key (pinned
by the routers key-for-key oracle). No reconstructed copy found.

**4. Inverse / round-trip pairs.** No encode/decode grammar lives here.
Checked and ruled out one by one: code+reason travel as one literal
pair per close (never split); decide/close/settle are one machine's
phases, not a pair; the window timestamp is write-once-read-many under
the same lease (no inverse); the Host projection is one-directional
(scope into `META`, verdict discarded string). No second half anywhere.

**5. Contracts restated in another medium.** Three media carry this
file's contracts: production code (target); oracles that spell
expectations independently - `tests/test_consumers.py` (hostile rows
fail closed, cancellation rows re-raise, the `10**10000` OverflowError
chaining row, host-projection rows) and `tests/test_routers.py` (the
eviction import-boundary row, the upstream-read partition row, window
+ host + live revocation rows), each verified to fail rather than
follow a production change (bodies read for the cited rows, titles
censused for the rest); projections (the module/class/function
docstrings - long, and load-bearing claims verified against bodies and
installed upstream source); upstream source itself as the external
oracle for every seam name the docstrings assert. Fakeshop mounts no
WebSocket endpoint, so the package tier (communicator-based) is the
strongest existing tier for these rows - correctly placed per
`AGENTS.md`, not a live-tier gap.

**6. Enforcement by omission.** Three member-by-member checks. (a) Both
protocols get both halves: each generated handler installs admission
(`handle_subscribe` / `handle_start`) + stop-aware schema (both
`__init__`s) + loop containment (both `handle`s); the adapter seam is
protocol-neutral by construction - enumerated, all present. (b) The
non-string-query floor guard exists only on the transport-ws handler:
deliberate (floor parses `payload["query"]` in `handle_subscribe`;
legacy parses inside its task), recorded in R13; the
floor-legacy pairing rests on the code comment + installed-source read,
not on a floor-wheel fetch (stated limit, no verdict depends on it).
(c) Ungated frames (`complete`, `ack`, `ping`/`pong`, `ka`) are
deliberate (R4/R8 docstrings), still serialized under the lease past
DECIDED, and still end at disconnect settlement. No member lacks a
guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the working-tree blob, counting
`ast.Module.body` - **46 top-level statements** (working == HEAD; the
item-baseline diff is empty, probe `item-diff-empty`) - plus the
"or better" nested census: 4 factory-nested classes with 9 methods,
`_ConnectionRevocation` 6 members, `_StopAwareSchema` 5 members,
`DjangoWebSocketHostValidator` 2 members. Every member lands below;
every challenge in `### Challenges` ends in a family row, a file-local
record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (transport contract + Host section) | (none) | projection |
| 1-7 | imports: future, asyncio, contextlib, math, time, collections.abc, typing | machinery names | machinery |
| 8-9 | django imports: DisallowedHost, HttpRequest | Host decision | consumer (R14) |
| 10 | `from . import logger` | log sink | consumer (all log sites, F5) |
| 11 | `from .exceptions import ConfigurationError, describe_value` | typed rejection | consumer (R6, F4) |
| 12 | `from .utils.sessions import (4 names)` | lease + provenance + key | consumer (F2) |
| 13 | `_DEFAULT_REVALIDATION_WINDOW = 0.0` | window default | R6 (routers default follows) |
| 14-15 | `_REVOCATION_CLOSE_CODE/_REASON` | 4403/Forbidden | R1 |
| 16 | `_MAX_REVOCATION_CLOSE_ATTEMPTS = 2` | close bound | R2 |
| 17-21 | five `_REVOCATION_*` states | machine vocabulary | R3 |
| 22 | `_INFORMATION_BEARING_FRAME_TYPES` | gated set | R4 |
| 23-26 | invalid-message + internal-error code/reason pairs | containment closes | R5 |
| 27 | `_CLIENT_FRAME_SHAPE_ESCAPES` | escape classifier | R5 |
| 28 | `_REVALIDATED_AT_SCOPE_KEY` | window cache slot | R7 |
| 29 | `def _monotonic` | clock seam | R7 |
| 30 | `def _unusable_window_error` | one rejection builder | R6 (+ F4 consumer) |
| 31 | `def resolved_revalidation_window` | window validation | R6 (+ F4 consumer; J1) |
| 32 | `class _ConnectionRevocation` (+ 6 members) | close state machine | R3 |
| 33 | `async def revalidate_operation_actor` | admission checkpoint | R8 |
| 34 | `async def send_revalidated_operation_frame` | outbound checkpoint | R8 |
| 35 | `async def _actor_is_current` | shared decision | R8 |
| 36 | `async def _revoke_connection` | revocation entry | R8 |
| 37 | `async def _stop_aware_results` | stop + per-event mask | F3 consumer + R9 |
| 38 | `class _StopAwareSchema` (+ 5 members) | result-source wrapper | R10 |
| 39 | `def _install_stop_aware_schema` | per-handler install | R10 |
| 40 | `async def _contain_message_loop_failure` | loop refusal | R11 (J2) |
| 41 | `async def _refreshed_actor` | session reload | R12 (F1 consumer) |
| 42 | `def build_revalidating_consumer_class` (+ 4 nested classes, 9 methods) | factory | R13 |
| 43 | `_HOST_META_KEYS_BY_HEADER` | projection table | R14 |
| 44 | `def _host_validation_request` | projection | R14 |
| 45 | `class DjangoWebSocketHostValidator` (+ 2 members) | Host boundary | R14 |

Cross-cutting: F5 (38 `except BaseException` containment sites inside
statements 33-36, 40, 42-nested) and F2 (lease reads inside 33-36).
Rules F1-F2 reuse is one existing plan name (F1) plus four NEW names
(F2-F5) proposed below for Worker 0 to index; R1-R14 are file-local;
J1-J3 are recorded rejections.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 one boundary | `get_user` gains a second sync hop | **1** at channels auth (this file's refusal-to-wrap follows) | consumer |
| C2 | F2 lease | a second primitive joins the transport/auth ordering | **1** (`utils/sessions.py::actor_lease`; both sides follow) | consumer |
| C3 | F2 provenance | provenance must survive a new transition kind | **1** (the latch; both checkpoints follow) | consumer |
| C4 | F2 store | engine resolution learns a new scheme | **1** (`session_store_class`; both callers follow) | consumer |
| C5 | F3 masking | policy learns a new maskable shape | **1** (`is_maskable_result` + builder; both application sites follow) | consumer |
| C6 | F4 tail | placeholder grammar changes | **1** (`exceptions.py::describe_value`; all routed sites follow) | consumer |
| C7 | F5 containment trio | a fourth process-level exception joins the re-raise set | **38** (every site spells the trio) | family-open |
| C8 | F5 message | the shared log sentence is reworded | **34** (every revalidation site spells it) | family-open |
| C9 | R1 close identity | upstream renames the connect refusal | **1** (the pair; oracles move) | file-local |
| C10 | R2 bound | first-plus-two-retries becomes first-plus-N | **1** | file-local |
| C11 | R3 machine | a sixth state (e.g. close-acknowledged) ships | **1** (states + transitions move together) | file-local |
| C12 | R4 frame set | a new information-bearing frame type ships | **1** | file-local |
| C13 | R5 split | a fourth escape class needs the invalid-message close | **1** (tuple; both `handle`s follow) | file-local |
| C14 | R6 default | default window becomes positive | **1** (routers default follows by import) | file-local |
| C15 | R6 domain | window admits `None` (disabled revalidation) | **1** | file-local |
| C16 | R7 clock | window measured on a loop clock instead | **1** (`_monotonic`; tests re-point the seam) | file-local |
| C17 | R8 checkpoints | a third checkpoint (e.g. per-message admission) ships | **1 owner shape** (decision + entry shared; new caller joins) | file-local |
| C18 | R9 stop | inner sources must be abandoned, not closed | **1** (the `finally` arm) | file-local |
| C19 | R10 wrap | upstream adds a fourth schema read | **1** (wrapper + audited set; the partition test fails first) | file-local |
| C20 | R11 containment | a third protocol needs loop containment | **1 owner shape** (classifier + closer shared) | file-local |
| C21 | R12 refresh | backend allow-list moves out of `get_user` | **0 here** (upstream owns; this file follows) | consumer |
| C22 | R13 factory | upstream renames a seam attribute | **1** (attribute reads; no module import to move) | file-local |
| C23 | R14 projection | Django reads a third META key for Host | **1** (table; verdict still Django's) | file-local |
| C24 | J1-J3 | the three refused shared forms | **0 moves - refused**, differences + triggers in findings | refused |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
setup, no shared-tree pytest - the workspace recipe is for mutating
proofs, of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-consumers/probe_w1.py
```

Output (`46 checks, 0 failed`): 46-member AST with the full def-name
list; nested census (4 factory classes, 6+5+2 members); 38
`except BaseException` + 34/4 log-literal counts; 15 single-site
claims; 12-module-level-import hygiene (channels-free,
strawberry-free, three function-local imports present); router
4-import + once-call + default + composition census; owner-docstring
cross-citations both directions (`session_store_class`,
`_stop_aware_results`, `describe_value` scope, `run_in_one_sync_boundary`,
transition side, shaped-after line); item-baseline diff empty;
upstream spot checks at installed 0.324.0 (stream/subscribe reads,
4403 refusal, incremental rejection). One first-draft check failed on
probe precision (the revoke-close literal is 4 sites, not 3 - the
attempt body plus three entry arms) and was corrected, substance
unaffected. Status: `execution-verified` for every identity/count/
shape/absence/import claim below. Rejects the wrong results "a second
definition lives here", "the target drifted from its baseline", "the
router respells the default", "masking is re-stated at the seam".

## Findings

No production edit is owed by a file item; F1 reuses the plan's
existing family, F2-F5 are NEW names proposed for the index, the rest
are file-local records and three recorded rejections.

### F1 - one sync boundary (existing family `one-sync-boundary`, stays `open`)

- **Contract + variation.** A logical read crosses exactly one sync
  boundary; `database_sync_to_async`'s `close_old_connections` is part
  of the contract, not decoration.
- **Sites + roles.** *Definition*:
  `utils/querysets.py::run_in_one_sync_boundary` (owner side; family
  item's surface). *Negative consumer here*:
  `consumers.py::_refreshed_actor` - obeys by refusing a second wrap
  around `channels.auth.get_user` (already decorated), with the store
  constructed outside the boundary (IO-free: `load()` defers to first
  access inside `get_user`). The docstring names the owner as the
  reason. *Oracles*: the family gate. *Projections*: the `_refreshed_actor`
  docstring paragraph.
- **Challenges.** C1 - 1 at channels auth, 0 here; the obedience needs
  no move whatever the owner does short of a hop-count change.
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation here.
- **Migration.** None (zero-edit item; consumer role only).
- **Distinct behavior.** Nothing here wraps any boundary; the single
  hop is upstream's decorator, reused verbatim.
- **Behavioral proof.** `static-reviewed` (body + decorator read in
  installed `channels/auth.py`); `execution-verified` for the census.
  Rejects "this file crosses its own sync boundary".
- **Structural gate.** The live revalidation rows (an authenticated
  socket that executes proves the hop happened exactly once - twice
  would discard the close semantics); negative control: wrapping the
  call in the shared runner passes happy-path rows and breaks
  connection cleanup under load (stated statically; the family item
  owns the executed gate).
- **Coupling.** None.
- **Freshness.** `consumers.py` `18f3ea16…` + `utils/querysets.py`
  `5907a1f7…` (owner def line, from the querysets artifact - not
  re-read here, stated honestly) + installed `channels/auth.py`
  `9da53b03…`.

### F2 - WebSocket connection actor state (NEW family `ws-connection-actor-state`, proposed `open`)

- **Contract + variation.** Transport revalidation and auth
  transitions share one lease, one provenance latch, and one
  engine-to-store expression across the opt-in boundary, with total
  lock order (session lock OUTER, actor lease INNER). Variation:
  transition kinds (login/logout/register) on the auth side;
  checkpoint kinds (admission/outbound) on the transport side.
- **Sites + roles.** *Definitions* (all in `utils/sessions.py`):
  `utils/sessions.py::actor_lease`, `utils/sessions.py::actor_transition`,
  `utils/sessions.py::connection_was_authenticated` /
  `utils/sessions.py::note_authenticated_actor`,
  `utils/sessions.py::session_store_class`,
  `utils/sessions.py::scope_key`. *Consumers here*:
  `consumers.py::revalidate_operation_actor`,
  `consumers.py::send_revalidated_operation_frame` (whole critical
  sections under the lease),
  `consumers.py::_RevocationGatedWebSocketAdapter.send_json`'s
  delegated arm (same lease), `consumers.py::_actor_is_current`
  (provenance read/latch + window cache under the lease),
  `consumers.py::_refreshed_actor` (store instantiation),
  `consumers.py::_REVALIDATED_AT_SCOPE_KEY` (key built by the shared
  builder). *Second-side consumer*:
  `auth/mutations.py::_channels_logout` (the one site holding both
  locks, in the stated order - body read). *Oracles*: the eviction
  import-boundary row (placement), the same-connection logout rows,
  the provenance hostile rows in `tests/test_consumers.py`.
  *Projections*: both module docstrings (each names the other side).
- **Challenges.** C2, C3, C4 - 1 each at the sessions owner; zero
  definitions here.
- **Owner + lifetime.** `utils/sessions.py` (unchanged). Lifetime per
  principle 4: lease + provenance live on the ASGI scope under one
  namespace-built key, published at first use (await-free get-or-create),
  mutable only through the named helpers, never invalidated before
  disconnect (provenance is write-once).
- **Migration.** None (file item; the family item owns the decision).
- **Distinct behavior.** `auth/sessions.py::scope_session_lock`
  (mutation-vs-mutation) stays a different primitive - sharing it
  would serialize checkpoints against session writes they must not
  wait for; the docstrings record the split on both sides.
- **Behavioral proof.** `static-reviewed` (sessions module read whole;
  both checkpoint bodies + logout body read); `execution-verified`
  for the census. The race-freedom itself is proved by the existing
  logout-during-send oracles, `static-reviewed` here, executed at the
  final gate.
- **Structural gate.** The eviction row + same-connection logout rows.
  Negative control: a lease private to `consumers.py` passes every
  single-checkpoint oracle and fails exactly the logout-during-send
  rows.
- **Coupling.** None.
- **Freshness.** Target `18f3ea16…` + `utils/sessions.py`
  `f0d9297c…` + `auth/mutations.py` `dbe64995…` (transition hunk only)
  + `auth/sessions.py` `fad7feb8…` (def lines only) +
  `tests/test_routers.py` `9e8ef0d5…` (eviction row body read).

### F3 - subscription per-event error masking (NEW family `subscription-per-event-error-masking`, proposed `open`)

- **Contract + variation.** One classifier, one replacement builder,
  two application sites: query teardown (extension) and per-event
  transport seam. Variation: policies (`ErrorPolicy` values) and
  result shapes (maskable vs incremental frames).
- **Sites + roles.** *Definitions* (all in
  `extensions/error_policy.py`): `mask_execution_result`,
  `is_maskable_result`, `masking_is_active`, `schema_error_policy`.
  *Consumers*: the extension teardown (owner side) and
  `consumers.py::_stop_aware_results` here (masks each yielded value
  through the shared classifier + builder, returns the copy, resolves
  the policy once per subscription, reads the DEBUG gate per event).
  The shape gate is what lets an unmaskable incremental frame reach
  upstream's own refusal instead of being degraded. *Oracles*: the
  error-policy suite + subscription masking rows (titles censused;
  bodies belong to the family item). *Projections*: both docstrings
  (each names the other seam - verified both directions).
- **Challenges.** C5 - 1 at the error-policy owner; zero definitions
  here (the import is function-local precisely to avoid a second
  ownership edge - verified).
- **Owner + lifetime.** `extensions/error_policy.py` (unchanged). No
  stored derivation here beyond the per-subscription policy local
  (lifetime: one generator; validity: the executing schema object).
- **Migration.** None (file item).
- **Distinct behavior.** The stop mechanics in the same generator
  (R9) stay this file's own - masking composed by name, stopping
  owned locally; neither may be "simplified" into the other.
- **Behavioral proof.** `static-reviewed` (seam body + four def lines
  + both docstring halves read); `execution-verified` for the census.
- **Structural gate.** The per-event masking rows + the incremental
  passthrough row. Negative control: inlining a local classifier
  passes every happy-path oracle and fails exactly the new-shape rows
  the owner adds (family item's gate to prove).
- **Coupling.** None.
- **Freshness.** Target `18f3ea16…` +
  `extensions/error_policy.py` `baea073f…` (head + 4 defs).

### F4 - typed rejection value tail (NEW family `typed-rejection-value-tail`, proposed `open`)

- **Contract + variation.** Every typed rejection whose value came
  from outside the package renders its `got` tail through
  `exceptions.py::describe_value`, so the message cannot raise while
  being formatted. Variation: per-domain prose; the renderer is fixed.
- **Sites + roles.** *Definition*:
  `exceptions.py::describe_value` (its scope docstring already claims
  exactly this population: body cap, revalidation window, router
  rejections, schema-policy rejections). *Consumers verified here*:
  `consumers.py::_unusable_window_error` (via
  `consumers.py::resolved_revalidation_window`). *Consumers cited by
  the owner, for the family item to classify*:
  `views.py::_resolved_max_request_body_bytes` (body read - confirmed
  consumer), `routers.py`'s three rejections, `error_policy.py`,
  `resource_policy.py`, `extensions/debug.py` (titles only, stated
  honestly). *Oracles*: the `10**10000` OverflowError-chaining row
  (body read - pins the hostile-tail contract directly).
- **Challenges.** C6 - 1 at the renderer; zero definitions here.
- **Owner + lifetime.** `exceptions.py` (unchanged). Pure derivation,
  never cached (principle 4: "not cached" stated by use).
- **Migration.** None (file item).
- **Distinct behavior.** Per-domain prose stays per site - only the
  tail is shared; unifying messages would couple unrelated settings'
  docs.
- **Behavioral proof.** `static-reviewed` (renderer body + scope
  paragraph + window rejection read); `execution-verified` for the
  census. Rejects "this file interpolates the value itself".
- **Structural gate.** The huge-int row (a direct interpolation
  raises `ValueError`/`OverflowError` instead of `ConfigurationError`).
  Negative control: `f"{value!r}"` in `_unusable_window_error`
  passes every small-value oracle and fails exactly that row.
- **Coupling.** None.
- **Freshness.** Target `18f3ea16…` + `exceptions.py` `e06b0b7f…`
  + `views.py` `9f85b0df…` (resolver body read) +
  `tests/test_consumers.py` `17842b60…` (chaining row body read).

### F5 - checkpoint fail-closed containment (NEW family `ws-checkpoint-fail-closed-containment`, proposed `open`)

- **Contract + variation.** At every suspension-bearing checkpoint:
  the process-level trio (`CancelledError`, `KeyboardInterrupt`,
  `SystemExit`) propagates; any other escape is logged and answered
  with the site's fail-closed value. Variation axis: the fail-closed
  continuation per site (`False`, `revoked=True`, fall-through to DB,
  suppress-and-return).
- **Sites + roles.** *Definitions*: 38 `except BaseException` sites,
  all in this file (probe count; package-wide `except BaseException`
  bodies elsewhere are a different population - listed as excluded,
  the mechanism sweep is the family item's). The 34 revalidation-failed
  log literals + 4 revoke-close-failed literals are the shared
  wordings. No single definition exists today - that absence is what
  keeps this family open rather than closed.
- **Challenges.** C7 (38 sites), C8 (34 sites) - the counts that keep
  this family open.
- **Owner + lifetime.** TBD by the family item. Candidate: this
  module (every site is here; no consumer could fail to import it).
  Caution recorded now so the family item does not consolidate blind:
  per-site continuations are each site's own security contract
  (denial vs latch-vs-fall-through), and a helper with a mode flag
  per continuation would be principle-5 machinery - parameterize by
  the fail-closed value or reject.
- **Migration.** None (file item).
- **Distinct behavior.** The `handle()` overrides' `except Exception`
  (R11) is NOT a member: ordinary-only containment with a different
  trio rationale (bypass by inheritance) - stays separate whatever
  the family item decides.
- **Behavioral proof.** `static-reviewed` (all checkpoint bodies
  read); `execution-verified` for the counts. The per-site values are
  proved by the hostile + cancellation oracle rows (titles censused,
  two bodies read), `static-reviewed` here.
- **Structural gate.** The hostile/cancellation rows per site; the
  family item owes the executed gate plus its negative control (a
  hand-deleted containment arm fails exactly its site's rows).
- **Coupling.** None.
- **Freshness.** Target `18f3ea16…` + `tests/test_consumers.py`
  `17842b60…` (titles censused, cancellation + chaining bodies read).

### File-local records (no second definition after the matrix)

- **R1 - revocation close identity.** The 4403/`"Forbidden"` pair (C9
  - 1). Reused verbatim from upstream's own connect-time refusal
  (verified in installed transport-ws source: the
  `ConnectionRejectionError` arm), which is the non-disclosure
  property by construction. Trigger: upstream renames its refusal.
  Freshness: target + installed handler `1c5da7ef…`.
- **R2 - close-attempt bound.** First attempt plus exactly one retry
  (C10 - 1). The amplification + non-transient-raise rationale is
  recorded at the constant. Trigger: a new transient raise class.
  Freshness: target only.
- **R3 - five-state revocation machine.** States, `decide` before any
  await, connection-owned shielded attempt, terminal `settle`
  (C11 - 1). The decided-vs-committed split and the abandon-vs-retry
  arms are the load. Trigger: a consumer needing close acknowledgement.
  Freshness: target only.
- **R4 - information-bearing frame set.** `next`/`data`/operation
  `error` (C12 - 1). Control frames deliberately ungated but still
  lease-serialized past DECIDED (matrix axis 6c). Trigger: a new
  protocol frame carrying operation payload. Freshness: target +
  `tests/test_routers.py` `9e8ef0d5…` (only-information-bearing row).
- **R5 - loop-containment close split.** 4400/`"Failed to parse
  message"` for the three client-shape escapes, 1011/`"Internal
  error"` otherwise, traceback server-side only (C13 - 1). The 4400
  shape is upstream's own invalid-message refusal, spent on legacy
  too. Trigger: a fourth client-shape escape class. Freshness: target
  + installed handlers (`1c5da7ef…`, `58c0ca4b…`).
- **R6 - window validation.** Default, single rejection builder,
  exact-type gate (never `bool`), guarded float conversion before any
  predicate, finite/non-negative domain, no upper bound (C14, C15 -
  1 each; routers default + construction call are consumers by
  import). Trigger: a second WS numeric setting would extend this
  record, not J1's refusal. Freshness: target + `routers.py`
  `a18c5001…` + chaining oracle.
- **R7 - window cache mechanics.** `_monotonic` seam + namespaced
  scope key + lease-held compare-and-write (C16 - 1). The clock is the
  documented test seam (replaces sleeping under `-n auto`).
  Trigger: none owed beyond the seam's own tests. Freshness: target.
- **R8 - checkpoint cluster.** Admission + outbound + shared decision
  + single revoke entry (C17 - 1 owner shape). The no-error-frame
  symmetry, the never-downgrade rule, and the lease-through-send are
  each single-sited. Trigger: a third checkpoint joins the decision
  and the entry rather than copying them. Freshness: target +
  `tests/test_consumers.py` `17842b60…` + live revocation rows in
  `tests/test_routers.py`.
- **R9 - stop mechanics.** Lease-free latch read, bounded pulls,
  masked copy, `aclose`-when-present `finally` (C18 - 1). Masking
  itself is F3's; what stays here is stopping. Trigger: upstream
  guaranteeing source closure on all paths would shrink the
  `finally`, not move it. Freshness: target + partition-test half.
- **R10 - stop-aware wrapper.** Both result-source names wrapped
  unconditionally + `__getattr__` transparency + per-handler install
  (C19 - 1). The read set is re-derived from installed handler source
  by the partition test rather than trusted. Trigger: a fourth
  upstream read (the test fails first - that is the gate).
  Freshness: target + installed handlers + schema `c3d8de12…` +
  `tests/test_routers.py` partition row (body read).
- **R11 - loop-containment fan-out.** Two `handle()` overrides + the
  shared classifier/closer, `Exception`-not-`BaseException` by
  inheritance (C20 - 1 owner shape). Override point is `handle`, not
  `handle_message` (the `RecursionError`-in-`iter_json` unwind -
  verified in installed `ws_handler.py`). Trigger: a third protocol
  handler. Freshness: target + installed handlers.
- **R12 - actor refresh.** `get_user` reused verbatim + synthetic
  one-key mapping + store outside the boundary (C21 - 0 here,
  upstream owns the backend coverage). The mapping exists so a
  hash-mismatch flush cannot land on the live store. Trigger: a
  second actor-resolution need on this path joins this function.
  Freshness: target + installed `channels/auth.py` `9da53b03…`.
- **R13 - consumer factory.** Three bases read off the handed class
  (never imported), per-instance revocation + initkwarg window,
  function-local classes (import-unreachable, not merely unexported),
  router-side cache lifetime (C22 - 1). The floor non-string-query
  guard rides on the transport handler only (matrix axis 6b; the
  floor-legacy pairing is comment-sourced - stated limit).
  Trigger: a fourth upstream seam attribute. Freshness: target +
  `routers.py` `a18c5001…`.
- **R14 - Host boundary.** Projection table + minimal-request builder
  + `DisallowedHost`-only denial via Channels' own denier, composed
  outermost by the router (C23 - 1). Matching stays Django's; the two
  deliberately unprojected META keys are verdict-neutral by the
  recorded argument. Trigger: Django reading a third key for Host.
  Freshness: target + `routers.py` `a18c5001…` + host oracle rows
  (titles) + installed `websocket.py` `15bc4fa9…`.

### J1 - window validator vs body-cap validator (rejection, not a family)

`consumers.py::resolved_revalidation_window` vs
`views.py::_resolved_max_request_body_bytes`. Considered shared form:
one numeric-setting validator. Contract difference: float window
`>= 0.0` with int-coercion and no `None` vs int byte-count `> 0` with
two-rung `None` coalescing (constructor > setting > default) and a
disable spelling; different prose, different overflow arms
(`OverflowError` on float conversion vs digit-limit on comparison).
One shape, two domains - unifying couples WS revocation-delay policy
to HTTP body-cap evolution. Reconsideration trigger: a third
numeric-setting validator with this shape, or a shared-spelling change
(e.g. admitting a new numeric type) that must land on both. Durable
home: both resolvers' docstrings (each already names the other) + this
finding.

### J2 - loop containment vs strawberry-patch translation (rejection, not a family)

`consumers.py::_contain_message_loop_failure` vs
`_strawberry_patches.py`'s `RecursionError` translation. Considered
shared form: one RecursionError rule. Contract difference: in-flight
exception classification on the WS `decode_json` path (which never
enters `parse_json`) vs raise-site translation on the HTTP
`parse_json` path; different inputs, different outputs (close code vs
translated raise). Reconsideration trigger: the WS path ever entering
`parse_json`. Durable home: the containment docstring's "why not the
patch's job" paragraph + this finding.

### J3 - tolerant `aclose` vs required async-generator (rejection, not a family)

`consumers.py::_stop_aware_results`' `getattr(source, "aclose", None)`
tolerance vs requiring the typed async generator upstream declares.
Considered shared form: assume `aclose` always present. Contract
difference: the legacy upstream path accepts any async iterator, so
the tolerance is a compatibility floor (`>=0.316.0`), not defensiveness.
Reconsideration trigger: the floor rising past every release that
accepts a bare async iterator. Durable home: the generator docstring's
`finally` paragraph + this finding.

## Defects

None. Every claim checked while tracing held: the four router imports
all consumed; the default flows by import, never respelled; all four
masking names composed at one call site; the lease spans validation
through send at both checkpoints with the delegated arm included; the
provenance latch precedes the anonymous carve-out on every path; the
4403/4400/1011 identities match installed upstream's own spends; both
handler generations install both halves; the partition test derives
rather than asserts; the eviction test pins the `utils` placement. No
guard any contract requires is missing beyond what is recorded and
deliberate above; the X-row pattern does not apply (no concurrent hunk
exists in this file - item-baseline diff is empty).

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
whole-tree byte sweeps, command in `### Challenges`) already ran green
against the shared tree; they mutate no source and open no database, so
no workspace copy was owed and no `__file__`/DB `NAME` record applies.
No pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed` (two bodies read per cited row class at minimum, full
title census otherwise) and the final gate executes them. No
`FAKESHOP_SHARDED` or Postgres cell is owed: this artifact's
execution-verified claims (statement counts, import census,
absence/single-site facts, baseline diff, installed-source spot
checks) touch no database, alias, or dialect decision
(`inapplicable by construction` - the target's DB-reaching paths are
exercised by the oracles cited, not by this probe).

## Independent verification (Worker 2)

Recorded before reading `## Findings` below (reconciliation follows the
trace). Own instrument: `ast.parse` over the working tree, package-wide
literal sweeps, `git hash-object` re-hashes of every cited blob, and
oracle-home greps; read-only probe
`docs/dry/temp-tests/dry-file-consumers-w2/probe_w2.py` (`64 checks, 0
failed`); `probe_w1.py` re-run green under my invocation (`46 checks, 0
failed`). No source mutation, no Django setup, no DB, no shared-tree
pytest, so no workspace copy was owed and no `__file__`/DB `NAME` record
applies.

**Own trace.** The WebSocket-transport module owning the handshake Host
boundary (`consumers.py::DjangoWebSocketHostValidator` +
`consumers.py::_host_validation_request`) and the revalidating-consumer
factory (`consumers.py::build_revalidating_consumer_class`) with two
actor checkpoints (`consumers.py::revalidate_operation_actor`,
`consumers.py::send_revalidated_operation_frame`), one shared decision
(`consumers.py::_actor_is_current`), one revoke entry
(`consumers.py::_revoke_connection`), the five-state close machine
(`consumers.py::_ConnectionRevocation`), the stop-and-mask seam
(`consumers.py::_stop_aware_results`,
`consumers.py::_StopAwareSchema`,
`consumers.py::_install_stop_aware_schema`), the loop refusal
(`consumers.py::_contain_message_loop_failure`), the actor reload
(`consumers.py::_refreshed_actor`), and the window validation
(`consumers.py::resolved_revalidation_window` +
`consumers.py::_unusable_window_error` +
`consumers.py::_DEFAULT_REVALIDATION_WINDOW` +
`consumers.py::_monotonic` + `consumers.py::_REVALIDATED_AT_SCOPE_KEY`).
Consumers by name of: the actor lease/provenance/store/key cluster in
`utils/sessions.py`; the classifier/builder/policy quadruple in
`extensions/error_policy.py`; the tail renderer in `exceptions.py`;
`channels.auth.get_user`; Django's `HttpRequest.get_host`; upstream's
close codes, handler attributes, and result-source names.

**Counts per posited change (mine, authoritative definitions only).**
Sync-hop gain: 1 at channels auth, 0 here (negative consumer). Second
lease primitive / new transition kind / new store scheme: 1 each at
`utils/sessions.py`, 0 here. New maskable shape: 1 at
`extensions/error_policy.py` (classifier + builder move together), 0
here. Tail grammar change: 1 at `exceptions.py::describe_value`, 0
here. Fourth process-level exception: 38 (every `except BaseException`
site spells the trio - family stays open). Shared log sentence reword:
34 (family stays open). R-series (close identity, attempt bound,
machine, frame set, escape tuple, default, domain x2, clock,
checkpoint cluster, stop, wrapper, containment fan-out, refresh,
factory, projection): 1 each, except refresh (0 here - upstream owns
the backend coverage). J1/J2/J3: refused, 0 moves.

**Owners I would choose.** `utils/querysets.py::run_in_one_sync_boundary`
(F1, existing family, unchanged); `utils/sessions.py`
lease/provenance/store cluster (F2, new); `extensions/error_policy.py`
masking cluster (F3, new); `exceptions.py::describe_value` (F4, new);
TBD by the family item for containment (F5, new; candidate this module
with the mode-flag caution below); file-local R1-R14; J1-J3 rejected.
Identical to the artifact in every row.

**Enumeration (member by member, own count).** `ast.Module.body` = 46:
0 docstring; 1-7 stdlib/typing imports; 8-9 Django imports; 10 logger;
11 exceptions; 12 sessions; 13 window default; 14-15 revocation close
pair; 16 attempt bound; 17-21 five states; 22 frame set; 23-26
containment closes; 27 escape tuple; 28 scope key; 29-31 clock/error
builder/validator; 32 revocation class (6 members); 33-37 five async
checkpoints/seam entries; 38 stop-aware schema (5 members); 39
installer; 40 containment; 41 refresh; 42 factory (4 nested classes,
9 methods); 43 host table; 44 host projection; 45 Host validator (2
members). Every member lands in the artifact's rows 0-45 with the same
homing; the nested census matches (4 factory classes including
`GraphQLWebSocketConsumer`; 6 + 5 + 2 members). No member unassigned;
every challenge ends in a family row, a file-local record, or a
rejection.

**Matrix (judged on the real surface).** 1: discharged - no sibling
flavor revalidates a socket actor (HTTP is per-request; mutations/forms
/DRF own no connection); the numeric-validator twin is refused as J1
on domain difference, the shared tail named as F4. 2: discharged - no
sync twin exists in target (async-only by construction, no
`sync_to_async` bridge); the one touched sync-boundary rule is obeyed
negatively (F1). 3: discharged - all five respellable facts composed by
name (verified: upstream 4403 shape in installed source, transport-ws
4400 shape, Django `get_host`, `utils/sessions.py::scope_key`, router
default by import). 4: discharged - no round-trip grammar lives here
(close pairs travel as one literal; decide/close/settle are one
machine's phases; Host projection is one-directional). 5: discharged -
oracles spell expectations independently (titles censused: 92 test defs
in `tests/test_consumers.py`, 117 in `tests/test_routers.py`; hostile/
cancel rows fail closed by literal text; the `10**10000` chaining row
pins `ConfigurationError`; the partition test derives the read set;
the eviction row pins the `utils` placement); projections verified
against bodies and installed upstream. 6: discharged - both protocols
get both halves (admission + stop-aware install + containment in both
`__init__`s/`handle`s; adapter seam protocol-neutral); the
transport-only floor guard is deliberate with the stated legacy reason;
ungated frames deliberate, still lease-serialized past DECIDED. No axis
unsearched, no claimed inapplicability without reason.

**Roles, counts, oracles.** Single definitions verified by
package-wide sweep: 4403/4400/1011 literals once each in production
(router cites 4403 only in prose); window default, attempt bound,
frame set, escape tuple, scope key, both resolvers, and the classifier/
closer once each. All F1-F4 consumer roles confirmed (refusal-to-wrap
with the store built outside the boundary; whole critical sections
under the shared lease; per-event masking through the shared
classifier + builder; hostile tail through the shared renderer). No
oracle reads from the owner it checks (the window tests drive the
documented `_monotonic` seam; masking rows assert masked copies
against independently spelled policies).

**Equivalence (principle 8).** Zero-edit item: no behavior changed, so
no equivalence proof is owed. Recorded for the family item: an F5
consolidation would have to prove per-site continuations (`False` vs
revoked-latch vs fall-through-to-DB vs suppress-and-return), exception
order, log points, and lease scope observably unchanged - which is why
the artifact correctly leaves F5 open rather than consolidating.

**Zero-edit accepted.** Item-scoped diff empty by my own check (`git
diff d56415fb4b23dc86fab1c06edda70e8333fb63e7 --
django_strawberry_framework/consumers.py`, probe `w2-item-diff-empty`);
working == HEAD == baseline blob `18f3ea16…`. Coverage complete (46/46
+ nested); every candidate homed (F1 reused; F2-F5 newly named with
owners; R1-R14 file-local with proving challenges; J1-J3 rejected with
difference + trigger + home). A file item owes no production edit and
none is demanded; candidates route to their holding families.

**Rejections.** J1 carries the domain difference (int `> 0` with
two-rung `None` coalescing and digit-limit arm vs float `>= 0.0` with
no `None` and float-conversion `OverflowError` arm - both bodies read)
plus trigger. J2 carries the path difference (WS in-flight
classification on the `decode_json` loop vs HTTP raise-site
translation at `BaseView.parse_json` - both names verified present)
plus trigger. J3 carries the compatibility difference (legacy
iteration accepts a bare async iterator; unconditional `aclose` lives
only in `cleanup_operation` - installed source read) plus trigger. One
nit, not verdict-changing: J1's home says both resolvers' docstrings
each name the other, but only the consumers side names views (verified
present); `views.py` carries no back-pointer (verified absent). The
finding itself remains the durable home; a file item lands no edit, so
no correction is demanded.

**Freshness: re-hashed all, with errata.** These match: target
`18f3ea16…`, `utils/sessions.py` `f0d9297c…`,
`extensions/error_policy.py` `baea073f…`, `exceptions.py`
`e06b0b7f…`, `views.py` `9f85b0df…`, `auth/mutations.py`
`dbe64995…`, `auth/sessions.py` `fad7feb8…`, `routers.py`
`a18c5001…`, `utils/querysets.py` `5907a1f7…` (owner line, as honestly
scoped), installed handlers/schema/auth/websocket `1c5da7ef…` /
`58c0ca4b…` / `c3d8de12…` / `9da53b03…` / `15bc4fa9…` (via
`git hash-object`, probes `w2-hash-*` / `w2-venv-*`). Errata
(transcription-only: the cited paths are correct, the two test-file
prefixes are swapped; mapping verified stable across item baseline,
HEAD, and worktree - `tests/test_consumers.py` = `9e8ef0d5…`,
`tests/test_routers.py` = `17842b60…`): F2 must read
``tests/test_routers.py`` `17842b60…` (eviction row body read); F4 must
read ``tests/test_consumers.py`` `9e8ef0d5…` (chaining row body read);
F5 must read ``tests/test_consumers.py`` `9e8ef0d5…` (titles censused,
cancellation + chaining bodies read); R4 must read
``tests/test_routers.py`` `17842b60…` (only-information-bearing row);
R8 must read ``tests/test_consumers.py`` `9e8ef0d5…` (+ live
revocation rows in `tests/test_routers.py`, unhashed). Worker 0's
Outcomes (the binding record) must carry these corrected values. Not
filed under Defects: not a package bug, routes to no card.

**Gates.** Every finding names its gate plus negative control as
static reasoning over pre-existing oracles whose homes I verified
exist: eviction rows (`tests/test_routers.py` strict-eviction block),
logout-during-send row (`tests/test_routers.py::test_a_same_socket_logout_cannot_complete_across_a_parked_protected_send`),
huge-int row (`tests/test_consumers.py::test_resolved_window_huge_int_overflow_is_configuration_error`),
only-information-bearing row (1678), partition row (5410), hostile +
cancellation rows (85+/40+ titles in `tests/test_consumers.py`, two
bodies per cited class confirmed present by census). Acceptable for a
zero-edit file item introducing no new gate: no consolidation depends
on an executed gate; the final gate executes the suite; family items
own the executed failability proofs.

**Pending execution.** Correctly absent. Both probes are read-only
(AST + byte sweeps + `git diff --exit-code`); no DB, alias, or dialect
surface is touched, so `inapplicable by construction` is judged sound
(the target's DB-reaching paths are exercised by the cited oracles at
the gate, not by the probe). No shared-tree pytest run by either
worker. Fakeshop mounts no WebSocket endpoint (package-wide sweep for
`websocket|ProtocolTypeRouter|channels` under `examples/fakeshop`
finds nothing), so the communicator-based package tier is the
strongest existing tier - correctly placed per `AGENTS.md`, not a
live-tier gap.

**Coupling.** Correctly none: five findings over five disjoint owners
(querysets, sessions, error_policy, exceptions, TBD-in-file); no shared
import move, no generated-slot collision, no landing order constraint.

**AGENTS.md prose.** 68 `path::Symbol` citations, zero raw `path:NN`
(swept); no process provenance (commands shown with summarized counts
only); tests at the mandated tier (justified above); artifact + both
probes are untracked-only, no tracked `.py` changed, so no ruff run is
owed. Concurrent dirt preserved untouched (`django_strawberry_framework/connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` - confirmed
via `git status --short`; plan/test files read as oracles and ledger
only).

**Reconciliation.** Differences from `## Findings`: (a) the five-line
freshness errata corrected above - paths, counts, roles, owners, and
homing all agreed; (b) the J1 one-directional-pointer nit - rejection
stands. Agreement everywhere else: F1 reuse as consumer (count 1 at
channels auth); F2/F3/F4 as consumers (counts 1 each at their owners);
F5 open at 38/34 with the mode-flag caution, which I endorse verbatim -
the per-site continuations are distinct security contracts and a helper
parameterized by anything coarser than the fail-closed value would be
principle-5 machinery (parameterize by value or reject); R1-R14
file-local at count 1 (R12 at 0 here); J1-J3 refused with difference +
trigger + home. Verdict: verified.

## Defects (Worker 2)

None. No package defect found while tracing: all four router imports
consumed; the default flows by import, never respelled; all four
masking names composed at the one call site; the lease spans validation
through send at both checkpoints including the delegated arm; the
provenance latch precedes the anonymous carve-out on every path; the
4403/4400/1011 identities match installed upstream's own spends; both
handler generations install both halves; the partition test derives
rather than asserts; the eviction test pins the `utils` placement. The
freshness errata in `## Independent verification (Worker 2)` is an
artifact transcription error, not a package defect - recorded in place
with exact corrections, routes to no card.

## Judgment

Backstop discharged: 46/46 `ast.Module.body` members enumerated plus
the nested census (4 factory classes / 9 methods, 6 + 5 + 2 members),
24 challenges run, every rule terminating in the one reused plan family
(F1, confirmed consumer role), a newly named family for Worker 0 to
index (F2 lease/provenance/store, F3 per-event masking, F4 tail
renderer, F5 containment - F2/F3/F4 confirmed consumer roles with count
1 at their owners, F5 open at counts 38/34), a file-local record with
its proving challenge (R1-R14), or a recorded rejection with difference + trigger
+ home (J1-J3) - no consolidation owed, no defect found, no new
production surface. Zero-edit result is legitimate.

Four `## Responsibility index` rows proposed for Worker 0 (names +
owners + holding items): `ws-connection-actor-state` /
`utils/sessions.py` / family item; `subscription-per-event-error-masking`
/ `extensions/error_policy.py` / family item; `typed-rejection-value-tail`
/ `exceptions.py::describe_value` / family item;
`ws-checkpoint-fail-closed-containment` / TBD (candidate:
`django_strawberry_framework/consumers.py`) / family item. The three
refusals live at their owner docstrings plus these findings.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
d56415fb4b23dc86fab1c06edda70e8333fb63e7 --
django_strawberry_framework/consumers.py` is empty (0 bytes, asserted
by the probe `item-diff-empty` check after all reads) - the target's
working blob (`18f3ea161b6081a91445796902a9635cb7e2e3bc`) equals its
`HEAD` blob, predates the item baseline untouched, and stays
untouched: this file item makes zero production edits. The `## Owned
changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never
touched; concurrent dirt (`connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied (test and plan files read as oracles and
ledger only). `docs/dry/dry-file-consumers.md` (this artifact) is a
new untracked file - Worker 0 ticks the plan box. No commit. No ruff
run owed (no tracked `.py` edits; artifact is `.md` only; the probe is
untracked scratch under
`docs/dry/temp-tests/dry-file-consumers/`). No `__file__`/DB record
(no workspace copy - no mutating proof exists). Scratch created (not
tracked changes): this artifact and the read-only probe
`docs/dry/temp-tests/dry-file-consumers/probe_w1.py` (`46 checks, 0
failed`; no source mutation, no DB, no shared-tree pytest).

## Re-pass at 9031cb3d (Worker 1)

Bounded re-pass only: the target is byte-identical across the
fast-forward, so this section re-derives solely the findings touching
the five changed package files, re-hashes every prior fingerprint
old-to-new, and spot-confirms the rest. Prior reasoning above is
untouched; nothing below revises it except where stated.

Scope of the range-diff (f8a75753 to 9031cb3d, package files only):
`utils/querysets.py` (seal wording, negate exact-bool gate,
`_SealPolicy.carry_result_cache`, deferred-state wording, result-cache
carry arms), `permissions.py` (three prose wordings only),
`resource_policy.py` (`_windowed_rows`/`bounded_rows` docstrings only),
`schema.py` (enforcement-subclass docstring only),
`types/resolvers.py` (one comment only). No test, router, view,
session, error-policy, exception, auth, or installed-upstream file in
this artifact's populations changed.

Per-finding verdicts (one line each):

- F1 one-sync-boundary: CONFIRMED unchanged (negative consumer; owner
  def still exactly 1; range-diff holds zero `run_in_one_sync_boundary`
  lines; sync token counts 2/4/0/4/0/1 identical across the revs).
- F2 ws-connection-actor-state: CONFIRMED unchanged (all three owner
  blobs identical; no owner file in the range-diff).
- F3 subscription-per-event-error-masking: CONFIRMED unchanged (owner
  blob identical; no owner file in the range-diff).
- F4 typed-rejection-value-tail: CONFIRMED unchanged (renderer blob
  identical; `describe_value` counts 4/7/0/0/1/3/7/0/2/4 identical
  across the revs; range-diff holds zero `describe_value` lines in
  `permissions.py`, `resource_policy.py`, `schema.py`,
  `types/resolvers.py`; the `resource_policy.py` hunk is docstring-only
  and touches no cited consumer site).
- F5 ws-checkpoint-fail-closed-containment: CONFIRMED unchanged
  (target-identical, so the 38/34 counts stand; re-run probes below
  re-assert the census).
- R1-R14 file-local: CONFIRMED unchanged (target-identical; the only
  artifact-adjacent hunks are prose/comment-only and touch no cited
  site; package `schema.py` is cited nowhere in this artifact, and the
  `schema/schema.py` citation is upstream Strawberry, whose blob is
  identical).
- J1-J3 rejections: CONFIRMED unchanged (both J1 bodies identical by
  blob; J2/J3 upstream seams identical by blob; triggers unmet).

Fingerprint table (f8a75753 old to 9031cb3d new; working tree equals
HEAD for every row except where noted):

- `consumers.py`: 18f3ea16 to 18f3ea16 (target CLEAN, unchanged).
- `utils/querysets.py`: 5907a1f7 to 1539b66c (STALE then re-derived;
  F1 unaffected per the zero-line diff above).
- `utils/sessions.py`: f0d9297c to f0d9297c.
- `extensions/error_policy.py`: baea073f to baea073f.
- `exceptions.py`: e06b0b7f to e06b0b7f.
- `views.py`: 9f85b0df to 9f85b0df.
- `routers.py`: a18c5001 to a18c5001.
- `auth/mutations.py`: dbe64995 to dbe64995.
- `auth/sessions.py`: fad7feb8 to fad7feb8.
- `tests/test_consumers.py`: 9e8ef0d5 to 9e8ef0d5 (Worker 2 errata
  mapping stands: this file holds the chaining/cancellation rows).
- `tests/test_routers.py`: 17842b60 to 17842b60 (eviction,
  only-information-bearing, partition rows).
- `permissions.py`: 9e0236b3 to 757dce34 (context only; no finding
  cites its body).
- `resource_policy.py`: 9205124f to 647133d2 (context only for F4;
  consumer sites untouched per the zero-line diff).
- `schema.py` (package): eb767f01 to 2f727321 (context only; cited
  nowhere in this artifact).
- `types/resolvers.py`: fc077f38 to f3341e6a (context only; cited
  nowhere in this artifact).
- Installed `channels/auth.py`: 9da53b03 to 9da53b03.
- Installed transport-ws handler: 1c5da7ef to 1c5da7ef.
- Installed graphql-ws handler: 58c0ca4b to 58c0ca4b.
- Installed `strawberry/schema.py`: c3d8de12 to c3d8de12.
- Installed `channels/security/websocket.py`: 15bc4fa9 to 15bc4fa9.

Proof status: read-only probes, no source mutation, no Django setup,
no database, no shared-tree pytest, so no workspace copy was owed and
no `__file__`/DB `NAME` record applies. `probe_w1.py` re-run green
(`46 checks, 0 failed`); `probe_w2.py` re-run green (`64 checks, 0
failed`); new `probe_repass_9031cb3d.py` green (`39 checks, 0
failed`: target stability, old/new blob pairs, F1 def count,
cross-revision token counts, zero-line diffs, owner/oracle hashes,
item-baseline emptiness). Commands:

```shell
uv run python docs/dry/temp-tests/dry-file-consumers/probe_w1.py
uv run python docs/dry/temp-tests/dry-file-consumers-w2/probe_w2.py
uv run python docs/dry/temp-tests/dry-file-consumers/probe_repass_9031cb3d.py
```

Gate re-checks: every finding's gate plus negative control stands as
recorded (no consolidation depends on an executed gate; zero-edit file
item). Prior Worker 2 freshness errata (test-file prefix swap) and the
J1 one-directional-pointer nit are carried forward unaltered. No new
gate is owed: the re-pass introduces no definition, moves no site, and
touches no oracle.

Defects: none new. The range-diff introduces no guard any contract
requires beyond what R1-R14 already record as deliberate.

Pending execution: none. All three probes are read-only (AST plus byte
sweeps plus `git diff`); no DB, alias, or dialect surface is touched,
so `inapplicable by construction` is judged sound (the target's
DB-reaching paths are exercised by the cited oracles at the final
gate, not by these probes). No shared-tree pytest run. No
`FAKESHOP_SHARDED` or Postgres cell is owed.

Item-scoped diff state: `git diff
b6f6c3c9c22f447c04787aa9b72578e2e8b49a54 --
django_strawberry_framework/consumers.py` is empty (asserted by the new
probe). Zero production edits. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) are clean and were never touched. Concurrent dirt
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was never edited, reverted, or tidied. New
untracked scratch only: this section and
`docs/dry/temp-tests/dry-file-consumers/probe_repass_9031cb3d.py`. No
commit. No ruff run owed (no tracked `.py` edits; artifact is `.md`
only; the probe is untracked scratch).

## Independent verification (Worker 2) — re-pass at 9031cb3d

Recorded before re-reading `## Re-pass at 9031cb3d (Worker 1)` findings;
reconciliation follows the trace. Own instrument: `ast.parse` over the
working tree, package-wide token counts at both revs, `git diff`
zero-line checks, `git hash-object` / `git rev-parse` re-hashes, and
oracle-home greps; read-only probe
`docs/dry/temp-tests/dry-file-consumers-w2/probe_w2_repass_9031cb3d.py`
(`43 checks, 0 failed`); `probe_w1.py` re-run green (`46 checks, 0
failed`); `probe_w2.py` re-run green (`64 checks, 0 failed`);
`probe_repass_9031cb3d.py` re-run green (`39 checks, 0 failed`). No
source mutation, no Django setup, no DB, no shared-tree pytest, so no
workspace copy was owed and no `__file__`/DB `NAME` record applies.

**F1 re-derived at the new tree.** `run_in_one_sync_boundary` has
exactly one definition package-wide
(`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`,
`ast` def count 1) and zero in the target (`ast` def count 0, 46
`ast.Module.body` members unchanged). Sync-count census working vs
`f8a75753` is identical at `2/4/0/4/0/1` (`utils/querysets.py`,
`permissions.py`, `resource_policy.py`, `schema.py`,
`types/resolvers.py`, `consumers.py`). Range-diff `f8a75753..9031cb3d`
holds zero `run_in_one_sync_boundary` lines in `utils/querysets.py`.
The target's only sync hop remains upstream's `database_sync_to_async`
via `channels.auth.get_user` in `consumers.py::_refreshed_actor`, with
the store built outside the boundary; no `from .utils.querysets import`
and no `sync_to_async` bridge in post-docstring code. Negative-consumer
role confirmed; owner unchanged.

**Sweep of the 5 changed files against artifact site lists.** The
range-diff touches only `utils/querysets.py` (seal wording, negate
exact-`bool` gate, `_SealPolicy.carry_result_cache`, deferred-state
wording, result-cache carry arms), `permissions.py` (three prose
wordings), `resource_policy.py` (`_windowed_rows`/`bounded_rows`
docstrings), `schema.py` (enforcement-subclass docstring),
`types/resolvers.py` (one comment). None touches a cited site:
`consumers.py` cites package `schema.py` nowhere (the only
`schema/schema.py` citation is upstream Strawberry, blob-identical) and
cites `types/resolvers.py` and `permissions.py` bodies nowhere; the
`resource_policy.py` hunk is docstring-only with zero `describe_value`
lines and touches no F4 consumer site; F4 tail census is identical
across revs at `4/7/0/0/1/3/7/0/2/4` (`resource_policy.py`,
`schema.py`, `types/resolvers.py`, `permissions.py`,
`exceptions.py`, `views.py`, `routers.py`,
`extensions/error_policy.py`, `extensions/debug.py`, `consumers.py`).
F2/F3 owners (`utils/sessions.py`, `extensions/error_policy.py`) have
no file in the range-diff. F5 is target-local (38/34 counts stand,
target-identical). R1-R14 and J1-J3 likewise unaffected (J1 both bodies
blob-identical; J2/J3 upstream seams blob-identical; triggers unmet).

**Fingerprint deltas re-hashed (spot-check, working tree).** Target
`consumers.py` `18f3ea16…` stable old-to-new and working == HEAD.
`utils/querysets.py` `5907a1f7…` to `1539b66c…` (stale-then-re-derived;
F1 unaffected per the zero-line diff). Unchanged owners confirmed:
`utils/sessions.py` `f0d9297c…`, `extensions/error_policy.py`
`baea073f…`, `exceptions.py` `e06b0b7f…`, `views.py` `9f85b0df…`,
`routers.py` `a18c5001…`, `auth/mutations.py` `dbe64995…`,
`auth/sessions.py` `fad7feb8…`, `tests/test_consumers.py`
`9e8ef0d5…` (chaining/cancellation rows), `tests/test_routers.py`
`17842b60…` (eviction, only-information-bearing, partition rows) with
the prior Worker 2 errata mapping carried forward. Context-only changes
confirmed old-to-new: `permissions.py` `9e0236b3…` to `757dce34…`,
`resource_policy.py` `9205124f…` to `647133d2…`, package `schema.py`
`eb767f01…` to `2f727321…`, `types/resolvers.py` `fc077f38…` to
`f3341e6a…`. Installed upstreams identical (`channels/auth.py`
`9da53b03…`, transport-ws `1c5da7ef…`, graphql-ws `58c0ca4b…`,
`strawberry/schema.py` `c3d8de12…`,
`channels/security/websocket.py` `15bc4fa9…`). Full agreement with the
Worker 1 old-to-new table in every row.

**Gates / negative controls for affected rows; no oracle rewritten.**
F1: live revalidation rows (authenticated-socket execution proves the
single hop; the family item owns the executed gate). F4: huge-int row
`tests/test_consumers.py::test_resolved_window_huge_int_overflow_is_configuration_error`
present; body calls `consumers.py::resolved_revalidation_window`,
expects `ConfigurationError` with `OverflowError` cause, and contains
zero `describe_value` references — oracle independent, negative control
(direct interpolation passes small-value oracles, fails exactly this
row) stands as static reasoning. F2: eviction block and
`tests/test_routers.py::test_a_same_socket_logout_cannot_complete_across_a_parked_protected_send`
present. F3: per-event masking + incremental-passthrough rows stand
(family item owns the executed failability proof). R4/R10: row 1678 and
`tests/test_routers.py::test_the_stop_aware_schema_passes_every_upstream_schema_read_through`
present. Acceptable for a zero-edit file item: no consolidation depends
on an executed gate; the final gate executes the suite.

**Zero-edit confirmed myself.** `git diff
b6f6c3c9c22f447c04787aa9b72578e2e8b49a54 --
django_strawberry_framework/consumers.py` is empty; working == HEAD ==
`18f3ea16…`; `git status --short` shows only the pre-existing concurrent
dirt plus untracked DRY artifacts/probes, none touched.

**Pending: correctly none.** All four probes are read-only (`ast` plus
byte sweeps plus `git diff --exit-code`); no DB, alias, or dialect
surface is touched, so `inapplicable by construction` is judged sound
(the target's DB-reaching paths are exercised by the cited oracles at
the final gate, not by the probes). No shared-tree pytest run by either
worker. No `FAKESHOP_SHARDED` or Postgres cell is owed.

**AGENTS.md prose check (re-pass scope).** Zero raw `path:NN` in the
re-pass section (swept); no process provenance (commands shown with
summarized counts only); `path::Symbol` usage unchanged from the
verified base (68 citations, zero raw); tests at the mandated tier
(Fakeshop mounts no WebSocket endpoint — package-wide sweep finds no
`websocket|ProtocolTypeRouter|channels` under `examples/fakeshop` — so
the communicator-based package tier is the strongest existing tier,
correctly placed, not a live-tier gap); artifact + all four probes are
untracked-only, no tracked `.py` changed, so no ruff run is owed.
Concurrent dirt preserved untouched.

**Reconciliation vs Worker 1 re-pass.** Agreement in every row: F1
confirmed unchanged (1 def, zero-line diff, `2/4/0/4/0/1` census); F2
confirmed unchanged (owner blobs identical, no owner file in the
range-diff); F3 confirmed unchanged (owner blob identical); F4 confirmed
unchanged (renderer blob identical, `4/7/0/0/1/3/7/0/2/4` census,
zero-line diffs, docstring-only hunk); F5 confirmed unchanged (38/34
stand); R1-R14 file-local confirmed unchanged; J1-J3 refused confirmed
unchanged. Fingerprint table agrees row-for-row. No new gate owed, no
new defect, pending-absent judged sound. The carried-forward errata
(test-file prefix swap) and J1 one-directional-pointer nit remain as
recorded and do not affect the verdict.

**Defects (Worker 2) — re-pass.** None. The range-diff introduces no
guard any contract requires beyond what R1-R14 already record as
deliberate. The prior `## Defects (Worker 2)` entry (no package defect;
freshness errata is transcription-only, routes to no card) stands.

**Verdict: verified.** Zero production edits, no pending execution.
The F2–F5 families were named pre-ff but never indexed (the tick was
never applied); Worker 0 should index them now with the exact rows
below, verified against the artifact findings.

## Defects (Worker 2) — re-pass at 9031cb3d

None. See the re-pass verification section above.

## Re-trace at bfaee91d (Worker 1)

Prior reasoning above untouched; nothing below revises it except D1. This
section re-traces the whole file fresh at the new target (not a bounded
re-pass: the plan reopened the item), reconciles against the prior
enumeration, and traces the 3+/3-.

Scope. `ITEM_BASELINE=4cb165e0813aa19ca48abc9b76b62acd504b5572`;
`HEAD=bfaee91d`; target `18f3ea16…` (at `9031cb3d`) → `936210e2…` (at
`bfaee91d`); working == HEAD == `936210e2…` (the dispatch's "clean"
confirmed by `git hash-object`); item-scoped diff
(`git diff 4cb165e0… -- django_strawberry_framework/consumers.py`) empty.
`## Owned changes` ledger check: ledger paths are `optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py` — nothing on
this path, confirmed. Concurrent dirt (`auth/mutations.py`,
`connection.py`, `extensions/resource_policy.py`, `filters/inputs.py`,
`filters/sets.py`, `forms/inputs.py`, `forms/sets.py`,
`mutations/fields.py`, `mutations/resolvers.py`, `mutations/sets.py`,
`optimizer/hints.py` + test companions) never edited, reverted, or tidied.

The 3+/3- (the whole `9031cb3d..bfaee91d` diff on this file; module
docstring, masking paragraph, prose-only): (a) "`schema.execute` needs
nothing, because that call runs the extension teardown before returning"
→ "needs nothing here, because that call masks both what its teardown
found and what it returns (`schema.py::DjangoSchema._masked_return`)";
(b) "so the two seams cannot drift on the question" → "so the seams
cannot drift on the question". Effect: the paragraph now NAMES the third
live masking site while `_stop_aware_results`' own docstring still claims
"two application sites" — that contradiction is D1 below. No code token,
no count, no gate moves on this file.

### Matrix (fresh, at bfaee91d)

1. Cross-flavor mirroring: unchanged — no sibling flavor revalidates a
socket actor; J1 still refused (both bodies blob-identical:
`views.py 9f85b0df…`, window validator untouched). 2. Sync/async twins:
none in target — Channels consumers are async-only, no `sync_to_async(` /
`async_to_sync(` bridge (probe; the one `database_sync_to_async`
substring is prose naming upstream's decorator inside `get_user`).
Principle 5 judgment: `connection.py`'s two-colored-bodies contrast does
not extend here — there is no twin pair in this file to color, only the
F1 negative-consumer obedience; the 3-line delta is prose and touches no
execution color, so the twin contract is untouched. The new
`schema.py::execute` / `execute_sync` twin is out-of-file (schema's
rule, not this file's). 3. Derived knowledge: unchanged — all five
compositions by name re-verified (upstream 4403/4400 shapes at identical
blobs, Django `get_host`, `scope_key`, router default by import).
4. Round-trip pairs: none lives here (unchanged). 5. Other media: oracles
stable — `tests/test_consumers.py 9e8ef0d5…` and
`tests/test_routers.py 17842b60…` range-clean; cited gates present
(huge-int row, partition row, same-socket-logout row, per-event masking
rows, incremental-passthrough row — names verified present, bodies as
previously read); `tests/test_error_policy.py` +65 / `tests/test_schema.py`
+38 in range add family-oracle rows (incl. two return-seam rows) without
moving any row this artifact cites. 6. Omission: unchanged — both
protocols still get both halves; floor-only guard and ungated frames
deliberate as recorded (R13/R4, bodies identical).

### Enumeration (fresh, reconciled)

Instrument: `ast.parse` over the working blob — **46 `ast.Module.body`
statements** (delta 0: the change is docstring prose, no statement added
or removed), nested census 4 factory classes / 9 methods, 6 + 5 + 2
method members. Reconciliation vs the prior #0–#45 table: every member
lands in the same home (F1 consumer; F2/F3/F4 consumers; F5 open; R1–R14
file-local; J1–J3 rejected; docstring/imports as projection/machinery).
No member unassigned, no new rule, no rule lost.

### Challenges (fresh counts, authoritative definitions only)

C1 (second sync hop): 1 at channels auth, 0 here (negative consumer;
`run_in_one_sync_boundary` def still exactly 1 package-wide, range-diff
holds zero such lines). C2/C3/C4 (lease primitive / transition kind /
store scheme): 1 each at `utils/sessions.py`, 0 here (owner blob
`f0d9297c…` identical; logout two-lock order re-read intact at working
`auth/mutations.py` lines 916/918 — range-clean, concurrent dirt
elsewhere). C5 (new maskable shape): 1 at `extensions/error_policy.py`
(classifier + builder move together; the range's `degraded_result`
extraction is a behavior-preserving 1-line swap ×3, same construction).
C5b (new masking APPLICATION site — the range's own change): 0 here; the
new site is `schema.py::_masked_return`, a consumer by name of the same
four helpers (single `mask_execution_result(` call each at
`error_policy.py:410`, `consumers.py:1385`, `schema.py:1083` — AST-counted).
C6 (tail grammar): 1 at `exceptions.py::describe_value`, 0 here.
C7/C8 (fourth process exception / log-sentence reword): 38 / 34, family
stays open (probe re-asserted). C9–C23 (R-series): 1 each (R12: 0 here),
bodies identical. Considered, no membership: `awaitable-refusal-and-
disposal` (no sync-awaitable crosses here; J3's `aclose` tolerance is
upstream-iterator compatibility, 0 definitions) and
`operation-bound-extension-mechanism` (this file neither defines nor
enforces operation binding; the LIFO-ordering mention is a projection
reference, 0 definitions). J1–J3: refused, triggers unmet (J-bodies and
upstream seams blob-identical).

Proof: read-only probe
`docs/dry/temp-tests/dry-file-consumers/probe_w1_retrace_bfaee91d.py`
(**59 checks, 0 failed**: enumeration, nested census, 38/34/4 counts,
delta lines old-absent/new-present, D1 phrase present, 3 call sites,
owner single-defs, stability + range-cleanliness of 7 witnesses, 3 cited
oracle names present, channels-free/twin-free/module-shape asserts,
2087-line no-truncation assert). Two first-draft checks failed on probe
precision only (docstring/`__slots__` counted as class members;
`database_sync_to_async` substring matched a bridge sweep) and were
corrected to method-def / call-syntax checks — substance unaffected.
Command: `uv run python
docs/dry/temp-tests/dry-file-consumers/probe_w1_retrace_bfaee91d.py`.
No source mutation, no Django setup, no DB, no shared-tree pytest: no
workspace copy owed, no `__file__`/DB record. `grep -c truncated` == 0:
every input read whole (target in full, both diffs in full, all cited
regions).

## Findings (re-trace verdicts, one line each)

- F1 `one-sync-boundary` (reuse): CONFIRMED consumer, count 1 at channels
auth / 0 here; querysets range hunks touch no cited site.
- F2 `ws-connection-actor-state` (reuse): CONFIRMED consumer, counts 1
each at sessions owner; lease/provenance/store roles re-read intact.
- F3 `subscription-per-event-error-masking` (reuse): CONFIRMED consumer,
count 1 at error-policy owner; owner extraction behavior-preserving; THIS
file's consumer role unchanged — but its projection now contradicts the
site count (D1).
- F4 `typed-rejection-value-tail` (reuse): CONFIRMED consumer, count 1 at
renderer; hostile tail still composed by name.
- F5 `ws-checkpoint-fail-closed-containment` (reuse, open): CONFIRMED at
38/34; mode-flag caution stands; delta touches no site.
- R1–R14 file-local: CONFIRMED, one definition each (R12 zero here);
only the module docstring moved and it is projection, not rule.
- J1–J3 rejections: CONFIRMED refused with difference + trigger + home;
J1 one-directional-pointer nit carried forward as recorded.
- `awaitable-refusal-and-disposal` / `operation-bound-extension-mechanism`:
considered fresh, no rule of this file belongs to either (0 definitions).

## Defects

- **D1 (owned-by-this-file prose drift, UNFIXED — DO NOT FIX in this
cycle).** `consumers.py::_stop_aware_results` docstring: "one classifier,
one replacement builder, two application sites". Counted live from this
side (AST `mask_execution_result(` call sites, one each): (1)
`extensions/error_policy.py::_process_result` (line 410, teardown);
(2) `consumers.py::_stop_aware_results` (line 1385, per-event); (3)
`schema.py::DjangoSchema._masked_return` (line 1083, returned result —
new in this range). Three live vs prose "two". Prose-only, no wire
impact (`degraded_result` is the shared floor all three call; masking
twice is a no-op by construction). The fix belongs to a card, not this
cycle: home on a NAMED owning card via this re-trace / Family
`subscription-per-event-error-masking`. Confirms the `extensions/
error_policy.py` re-trace's D1 from this side, verbatim.
- No other defects. Every other claim checked while tracing held; no
guard any contract requires is missing beyond the deliberate R1–R14
record; the range introduces none.

## Pending execution

None. The probe is read-only (AST + byte sweeps + git plumbing); no DB,
alias, or dialect surface touched — `inapplicable by construction` (the
target's DB-reaching paths are exercised by the cited oracles at the
final gate, not by this probe). No shared-tree pytest run. No
`FAKESHOP_SHARDED` or Postgres cell owed.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
4cb165e0813aa19ca48abc9b76b62acd504b5572 --
django_strawberry_framework/consumers.py` empty; working == HEAD ==
`936210e2…`. Ledger paths and concurrent dirt untouched (content
attributed before reading the one dirty cited file). New untracked
scratch only: this section + `docs/dry/temp-tests/dry-file-consumers/
probe_w1_retrace_bfaee91d.py`. No commit. No ruff run owed (no tracked
`.py` edits; artifact + probe are `.md`/untracked-scratch only).

Freshness (bfaee91d): target `936210e2…`; stable witnesses
`sessions f0d9297c…`, `exceptions e06b0b7f…`, `views 9f85b0df…`,
`routers a18c5001…`, `auth/sessions fad7feb8…`,
`test_consumers 9e8ef0d5…`, `test_routers 17842b60…`, upstream
`9da53b03… / 1c5da7ef… / 58c0ca4b… / c3d8de12… / 15bc4fa9…`; moved owners
`error_policy baea073f…→16f47547…`, `schema 2f727321…→c2e1b748…`,
`querysets 1539b66c…→96618fba…` (each range-diff read in full, findings
re-derived above); `auth/mutations.py` range-clean (working hunk
elsewhere, cited lines re-read).

## Judgment

Backstop discharged fresh at bfaee91d: 46/46 members enumerated plus the
nested census, challenges re-run with counts, every rule homed (2 reused
plan families as consumer in the narrow sense — F1 `one-sync-boundary`,
F4 `typed-rejection-value-tail` — plus F2/F3/F5 newly-named rows
re-confirmed for the index, R1–R14 file-local, J1–J3 rejected, two
families considered with no membership). The 3+/3- moves no finding's
count; it creates exactly one owned-by-this-file prose defect (D1),
carried UNFIXED for card homing. Zero-edit result is legitimate.

## Independent verification (Worker 2) — re-trace at bfaee91d

Recorded before re-reading `## Re-trace at bfaee91d (Worker 1)` findings;
reconciliation follows the trace. Own instrument: `ast.parse` over the
working tree, package-wide literal sweeps via the content-search tool,
`git hash-object` / `git show` / `git diff` plumbing, and oracle-home
greps; read-only re-run of
`docs/dry/temp-tests/dry-file-consumers/probe_w1_retrace_bfaee91d.py`
(`59 checks, 0 failed` under my invocation). No source mutation, no
Django setup, no DB, no shared-tree pytest, so no workspace copy was
owed and no `__file__`/DB `NAME` record applies.

**Own trace.** The WebSocket-transport module owning the handshake Host
boundary (`consumers.py::DjangoWebSocketHostValidator` +
`consumers.py::_host_validation_request`) and the revalidating-consumer
factory (`consumers.py::build_revalidating_consumer_class`) with two
actor checkpoints (`consumers.py::revalidate_operation_actor`,
`consumers.py::send_revalidated_operation_frame`), one shared decision
(`consumers.py::_actor_is_current`), one revoke entry
(`consumers.py::_revoke_connection`), the five-state close machine
(`consumers.py::_ConnectionRevocation`), the stop-and-mask seam
(`consumers.py::_stop_aware_results`,
`consumers.py::_StopAwareSchema`,
`consumers.py::_install_stop_aware_schema`), the loop refusal
(`consumers.py::_contain_message_loop_failure`), the actor reload
(`consumers.py::_refreshed_actor`), and the window validation
(`consumers.py::resolved_revalidation_window` +
`consumers.py::_unusable_window_error` +
`consumers.py::_DEFAULT_REVALIDATION_WINDOW` +
`consumers.py::_monotonic` + `consumers.py::_REVALIDATED_AT_SCOPE_KEY`).
Consumers by name of: the actor lease/provenance/store/key cluster in
`utils/sessions.py`; the classifier/builder/policy quadruple in
`extensions/error_policy.py`; the tail renderer in `exceptions.py`;
`channels.auth.get_user`; Django's `HttpRequest.get_host`; upstream's
close codes, handler attributes, and result-source names.

**Enumeration (member by member, own count).** `ast.Module.body` = 46,
delta 0 — my count matches the artifact's #0–#45 table with the same
homing (docstring as projection; stdlib/typing imports as machinery;
Django imports + logger + exceptions + sessions imports as consumers;
window default / close pair / attempt bound / five states / frame set /
containment closes / escape tuple / scope key as R-rows; clock/error
builder/validator as R6–R7; revocation class / five async
checkpoints-seam entries / stop-aware schema / installer / containment /
refresh / factory / host table / host projection / Host validator as
R3/R8/R10/R11/R12/R13/R14). Nested census matches: 4 factory-nested
classes with 9 methods (3+3+1+2), `consumers.py::_ConnectionRevocation`
6 methods, `consumers.py::_StopAwareSchema` 5 methods,
`consumers.py::DjangoWebSocketHostValidator` 2 methods (raw body lengths
8/7/3 include docstring/`__slots__`; method-def counts are 6/5/2).
No member unassigned; every challenge ends in a family row, a
file-local record, or a rejection.

**Masking-site census from THIS side.** Package-wide sweep for
`mask_execution_result(` finds exactly 4 matches: 1 definition
(`extensions/error_policy.py::mask_execution_result`) + exactly 3 live
calls — `extensions/error_policy.py::_process_result` (line 410,
teardown), `consumers.py::_stop_aware_results` (line 1385, per-event),
`django_strawberry_framework/schema.py::DjangoSchema._masked_return`
(line 1083, returned result, new in this range). No fourth production
call: `views.py` holds zero; `tests/test_error_policy.py` holds many
direct calls but those are oracles spelling expectations independently,
not application sites. The W1 "exactly three" claim is CONFIRMED by my
own census.

**Delta is prose-only (diffed myself).** `git show
9031cb3d:consumers.py` vs `git show bfaee91d:consumers.py` is the 3+/3-
module-docstring hunk only: `schema.execute` "needs nothing, because
that call runs the extension teardown before returning" becomes "needs
nothing here, because that call masks both what its teardown found and
what it returns (`schema.py::DjangoSchema._masked_return`)"; "so the
two seams cannot drift" becomes "so the seams cannot drift". Six
changed lines, zero code tokens, zero statements added/removed (46/46
stable), zero gates moved. Item-scoped diff `git diff
4cb165e0813aa19ca48abc9b76b62acd504b5572 --
django_strawberry_framework/consumers.py` is empty by my own check;
working == HEAD == `936210e2…` (the dispatch's "clean" CONFIRMED by
`git hash-object`); old target blob `18f3ea16…` confirmed.

**Family roles re-judged.** C1: 1 at channels auth, 0 here (negative
consumer — `consumers.py::_refreshed_actor` reuses `get_user` verbatim,
store built outside the boundary, docstring names the owner; sound).
C2/C3/C4: 1 each at `utils/sessions.py`, 0 here (whole critical
sections under the shared lease; two-lock order
`scope_session_lock`-OUTER / `actor_transition`-INNER re-read intact in
working `auth/mutations.py`; sound). C5: 1 at
`extensions/error_policy.py` (classifier + builder move together), 0
here (per-event masking through the shared names; the range's
`degraded_result` extraction is a behavior-preserving swap; sound).
C5b (new application site): 0 here — the new site is
`schema.py::_masked_return`, a consumer by name of the same helpers
(my 3-call census above); it moves no count in this file. C6: 1 at
`exceptions.py::describe_value`, 0 here (hostile tail composed by
name; sound). C7/C8: 38 `except BaseException` sites / 34 + 4 log
literals re-asserted (probe green + my own 38-count and 34-count;
the 4-count is the narrow `the revoked connection's close could not be`
literal). `ws-checkpoint-fail-closed-containment` "open" means exactly
this: the family item is undispatched, no owner decision exists yet
(plan holds it `open` with TBD candidate this module), and the 38/34
counts are what keep it open rather than closed. The consumer-role
question does not arise for F5 — it is 38 local definitions awaiting
the family decision, not a consumer of an existing owner — so judging
it "open, TBD, mode-flag caution stands" without a family decision is
sound; a file item must name the family and stop, which is what the
artifact does. `awaitable-refusal-and-disposal` + 
`operation-bound-extension-mechanism` considered with 0 definitions is
sound: no sync-awaitable crosses here (J3's `aclose` tolerance is
upstream-iterator compatibility, verified distinct), and this file
neither defines nor enforces operation binding (the sole LIFO mention
is a projection reference to teardown ordering). R1–R14 file-local at
count 1 each (R12 at 0 here — upstream owns the backend coverage)
CONFIRMED; J1–J3 refused with difference + trigger + home CONFIRMED
(bodies blob-identical, triggers unmet; the J1 one-directional-pointer
nit is carried forward as recorded and verdict-neutral).

**Twin judgment.** Async-only CONFIRMED: no `sync_to_async(` /
`async_to_sync(` call syntax anywhere in the target (swept; the sole
`database_sync_to_async` substring is prose naming upstream's
decorator inside `get_user` plus the `_refreshed_actor` docstring/body
reference). No sync twin, no bridge. The channels-auth boundary role
is sound (exactly-one-boundary obedience, F1 negative consumer). The
principle-5 `connection.py` two-colored-bodies contrast does not
extend here — there is no twin pair in this file to color. The new
`schema.py::execute` / `execute_sync` twin is schema's rule, out of
file. The 3-line prose delta touches no execution color.

**D1 confirmation + card class.** Counts CONFIRMED by my own census
(three live calls above vs `consumers.py::_stop_aware_results`
docstring "two application sites" still present at line 1321, while
the module docstring now names `_masked_return`). Prose-only defect:
no wire impact (`degraded_result` is the shared floor all three call;
masking twice is a no-op by construction), no contract row broken, no
wire or configuration input reaches a different behavior — so NOT a
release blocker under `GOAL.md` "Trust boundary". Owned-by-this-file
drift, correctly left UNFIXED in this cycle. Homing CONFIRMED: plan
`docs/dry/dry-0_0_15.md` already records "D1
(`consumers.py::_stop_aware_results` two-application-sites prose with
three live, from File `extensions/error_policy.py` re-trace) —
prose-only, not a blocker; home on a NAMED owning card via the
`consumers.py` re-trace / Family
`subscription-per-event-error-masking`" — the family named here is
that same family, so the two D1 records home together.

**Freshness re-hashed at bfaee91d (working tree).** Target
`936210e2…`; stable witnesses `utils/sessions.py` `f0d9297c…`,
`exceptions.py` `e06b0b7f…`, `views.py` `9f85b0df…`, `routers.py`
`a18c5001…`, `auth/sessions.py` `fad7feb8…`,
`tests/test_consumers.py` `9e8ef0d5…`, `tests/test_routers.py`
`17842b60…`; moved owners `extensions/error_policy.py`
`baea073f…→16f47547…`, package `schema.py`
`2f727321…→c2e1b748…`, `utils/querysets.py`
`1539b66c…→96618fba…`; installed upstreams
`channels/auth.py` `9da53b03…`, transport-ws `1c5da7ef…`, graphql-ws
`58c0ca4b…`, `channels/security/websocket.py` `15bc4fa9…`
(`strawberry/schema.py` `c3d8de12…` as previously recorded, not
re-hashed this pass — no finding depends on a fresh value).
`auth/mutations.py` working `200805d2…` vs HEAD `dbe64995…` is
concurrent dirt (the file is `M` in `git status --short`); the cited
two-lock lines were re-read intact in the working tree, so no finding
goes stale on it. Full agreement with the W1 freshness table in every
row I re-hashed.

**Pending execution: correctly empty.** The delta is docstring prose
with zero executable tokens, so static review (full target read, both
diffs read whole, all cited regions re-read) plus the read-only probe
(AST + byte sweeps + `git diff --exit-code`, no DB/alias/dialect
surface) is adequate: there is no ordering, transactional, async, or
cancellation behavior a workspace execution could additionally prove
about this hunk. The target's DB-reaching paths are exercised by the
cited oracles at the final gate, not by the probe
(`inapplicable by construction`, judged sound). No shared-tree pytest
by either worker per item rules; no `FAKESHOP_SHARDED` or Postgres
cell owed. Fakeshop mounts no WebSocket endpoint, so the
communicator-based package tier remains the strongest existing tier,
correctly placed per `AGENTS.md`.

**AGENTS.md prose on the empty diff.** Item-scoped diff empty (my own
check above); no process provenance in the re-trace section (commands
shown with summarized counts only); citations are `path::Symbol`
throughout with line numbers only for the D1 census inside this
per-cycle `dry-*.md` scratchpad (permitted class); tests at the
mandated tier (package communicator tier justified above, not a
live-tier gap); artifact + probes are untracked-only, zero tracked
`.py` changed, so no ruff run is owed (a `--fix` pass would touch the
concurrent dirt listed below). Concurrent dirt preserved untouched
(`auth/mutations.py`, `connection.py`,
`extensions/resource_policy.py`, `filters/inputs.py`,
`filters/sets.py`, `forms/inputs.py`, `forms/sets.py`,
`mutations/fields.py`, `mutations/resolvers.py`, `mutations/sets.py`,
`optimizer/hints.py` + test companions + plan/bug-hunt dirt —
confirmed via `git status --short`; the one dirty cited file was
content-attributed before reading, per the W1 note).

**Reconciliation vs Worker 1 re-trace.** Agreement in every row:
enumeration 46 delta 0 + nested 4/9 (6+5+2); 3+/3- prose-only naming
`schema.py::_masked_return` ("two seams"→"the seams"), moves no
count; F1 1-at-channels-auth/0-here; F2 1-each-at-sessions; F3
1-at-error-policy; F4 1-at-renderer; F5 open at 38/34 with the
mode-flag caution endorsed verbatim; R1–R14 file-local (R12 zero
here); J1–J3 refused; the two considered families at 0 definitions;
async-only twin judgment; D1 three-live-vs-"two" with NAMED-card
homing; pending-absent; zero production edits; probe 59/59 green
(re-run green under my invocation). Terminology note (not a
difference): the re-trace calls F2/F3/F5 "reuse" where the base
artifact called them "newly named" — at bfaee91d all five families
exist in the plan index as `open` (verified in
`docs/dry/dry-0_0_15.md`), so "re-confirmed for the index" and
"reuse" describe the same state. No counts moved, no finding
re-homed.

**Verdict: verified.** Zero production edits, no pending execution.
Worker 0 should tick File `consumers.py` on this verification and
carry D1 (owned-by-this-file prose drift, UNFIXED) to its NAMED
owning card via Family `subscription-per-event-error-masking`
together with the `extensions/error_policy.py` re-trace's D1, as the
plan already records.

## Defects (Worker 2) — re-trace at bfaee91d

None. No new package defect found while tracing: the single live
defect in scope (D1, three masking sites vs "two application sites"
prose) is already owned by Worker 1 above with exact census and card
homing, so it is not re-filed here. The prior `## Defects (Worker 2)`
(no package defect; freshness errata transcription-only) and the J1
one-directional-pointer nit stand as recorded and verdict-neutral.
