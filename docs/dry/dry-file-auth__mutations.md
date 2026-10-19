# DRY review: `django_strawberry_framework/auth/mutations.py`

Status: verified
Run: 0.0.15 2026-09-30-8

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in a family row (reused indexed name or one new family named for
Worker 0 to add) or a file-local row with its proving challenge, plus nested
rejections carrying contract difference + trigger. Zero production edits; zero
tracked files changed.

## System trace

FRESH target (1396 lines): the opt-in session-auth mutation factories
(`login_mutation` / `logout_mutation` / `register_mutation`) plus the phase-2.5
auth bind (`bind_auth_mutations`), over spec-040 Decisions 5/6/8/9. The module
is deliberately a thin layer: declaration-ledger mechanics ride the
[mutations/sets.py][mutations-sets] driver (`make_declaration_registry`,
`_validate_permission_classes`), payload/input construction rides
[mutations/inputs.py][mutations-inputs] (`build_payload_type`,
`payload_object_slot`, `materialize_mutation_input_class`,
`mutation_input_shape`, `build_mutation_input`,
`mutation_input_field_specs`, `editable_input_fields`), authorization +
envelope leaf ctors ride [mutations/resolvers.py][mutations-resolvers]
(`authorize_or_raise`, `payload_cls_for`, `build_payload`, `field_error`,
`run_write_pipeline_sync`, `_model_decode_step`, `_model_write_step`),
request resolution rides
[utils/permissions.py][utils-permissions]`::request_from_info`, the async
boundary rides [utils/querysets.py][utils-querysets]`::run_in_one_sync_boundary`,
and transport classification/capability rides
[auth/sessions.py][auth-sessions]. The genuinely new machinery is the
declaration-cache-conflict path, the permission-holder synthesis (+ its seal
twins), the anonymity definition, the login/logout prologue pairs, the
transport critical sections, the register decode/write step pair + rider, and
the surface-keyed bind. `current_user` lives in
[auth/queries.py][auth-queries] and reuses this module's declaration path,
field helper, bridge, and anonymity definition BY CALL.

Connected code read for judgment, outside the item:
[auth/__init__.py][auth-init], [auth/queries.py][auth-queries] (full),
[auth/sessions.py][auth-sessions] (full),
[utils/sessions.py][utils-sessions] (full: lease + engine expression),
[mutations/sets.py][mutations-sets] (registry driver, permission validation,
`DjangoMutation.check_permission`, both seal halves, `_resolve_primary_type`),
[mutations/resolvers.py][mutations-resolvers] (pipeline skeleton, auth gate,
payload/error ctors), [mutations/inputs.py][mutations-inputs] (payload/input
builders), [mutations/fields.py][mutations-fields] (`_lazy_ref`,
`build_lazy_field_signature`), [mutations/permissions.py][mutations-perms]
(`DjangoModelPermission` home),
[utils/permissions.py][utils-permissions] (`request_from_info`),
[utils/querysets.py][utils-querysets] (boundary, disposal, recourse,
`model_for`), [utils/directives.py][utils-directives],
[utils/execution_mode.py][utils-execution],
[utils/write_values.py][utils-write-values] (`unencodable_text_error`),
[utils/errors.py][utils-errors] (`field_error`, `"__all__"` sentinel),
[registry.py][registry] (subsystem-clear bus),
[types/finalizer.py][finalizer] (phase-2.5 slot),
[consumers.py][consumers] (lease checkpoints),
[forms/resolvers.py][forms-resolvers] + [rest/resolvers.py][rest-resolvers]
(write-flavor mirroring), [exceptions.py][exceptions], oracles
[test-auth-mutations][test-auth-mutations],
[test-auth-queries][test-auth-queries],
[test-auth-sessions][test-auth-sessions], [auth-helpers][auth-helpers],
[auth-conftest][auth-conftest], consumer
[accounts-schema][accounts-schema], contract source [spec-040][spec-040].

Excluded with reason: the concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, sibling
`dry-file-*.md` artifacts) was left untouched; none is in this item's paths.
Every other indexed family whose files-covered list touches `auth/` was judged
on its mechanism against this target's REAL surface (Matrix + Challenges C2,
C3, C6, C7); `connection.py`-owned families were not re-derived beyond the
attribution check.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The three write flavors (model / form /
serializer) share ONE skeleton
([mutations/resolvers.py][mutations-resolvers]`::run_write_pipeline_sync`) with
per-flavor decode/write STEP pairs; the register rider is a fourth step pair,
not a fourth kit (`_run_register_pipeline_sync` delegates unchanged;
`_register_decode_step` rides `_model_decode_step`;
`_register_write_step` delegates its tail to `_model_write_step`). The async
entries share one boundary
([mutations/resolvers.py][mutations-resolvers]`::run_pipeline_async` over
`run_in_one_sync_boundary`); the register rider's `resolve_async` calls the
boundary directly with its sync body — same contract, one hop. Sibling
`resolve_sync`/`resolve_async` pairs in
[forms/resolvers.py][forms-resolvers] and [rest/resolvers.py][rest-resolvers]
were read: same skeleton-by-call shape, no second skeleton. The auth fixed
fields do NOT ride the write skeleton (no model write, no transaction — a
deliberate non-mirror, Decision 5), but reuse its gate (`authorize_or_raise`),
payload ctors (`payload_cls_for`, `build_payload`, `field_error`), and input
builders by call. Considered families: `one-sync-boundary` (F2, consumer),
`sync-boundary-recourse-wording` (C6: no surface — this file mints no recourse
string; the discipline arrives via the shared machinery),
`queryset-seed-and-model-read` (C7: no surface — no `model_for` call; the rider
reads the validated snapshot's `.model`, the owned source).

**2. Sync/async twins.** Four native pairs, each a principle-5 two-colored-body
separation with the contrast recorded in both docstrings: login establish
(`_django_http_login_establish` / `_channels_http_login_establish`), login
bodies (`_login_resolve_body` / `_login_resolve_body_async`), logout teardown
(`_django_http_logout` / `_channels_logout`), logout bodies
(`_logout_resolve_body` / `_logout_resolve_body_async`); plus the interim
`_sync_bridged_async_body` seam (real coroutine fn, one shared worker) that
`current_user` rides. Django-HTTP arms stay in one boundary; Channels arms run
the all-sync prologue in one boundary then await native `channels.auth`
teardown/establishment — never a nested `async_to_sync` except the one
permitted sync->async hop for a directly-invoked sync consumer. Compared by
behavior, not shape (see F15, F16; probes P1 + oracle dispatch-spy tests).
Considered family `one-sync-boundary`: reused (F2) — checked, consumer-only,
do not inherit.

**3. Derived rather than repeated knowledge.** Every shared derivation is
consumed by call, never re-spelled: permission normalization
(`_validate_permission_classes`), request resolution (`request_from_info` under
the single `_AUTH_FAMILY_LABEL`), directives (`validated_field_directives`),
lazy refs + signatures (`_lazy_ref`, `build_lazy_field_signature`), payload
slot/name (`payload_object_slot`, `build_payload_type`), primary lookup
(`registry.get` + `types_for` split — F5), failure envelope (`field_error("")`
→ `"__all__"` sentinel owned by [utils/errors.py][utils-errors]),
storability preflight (`unencodable_text_error` — login collapses to the
undifferentiated envelope, register to the field-keyed error: same primitive,
justified different mapping).

**4. Inverse / round-trip pairs.** No encode/decode halves here: the register
`EXCLUDED`-password capture (`mutation_input_field_specs(excluded_attrs=...)`
→ `_model_decode_step` extended tuple → `_register_write_step`) is a
producer/consumer pair across the bind/resolver boundary with ONE writer
(`build_input` stashes the kind) and one reader (the shared decode) — the seam
is owned at [mutations/inputs.py][mutations-inputs], this file only passes the
set. The `Register`→`RegisterPayload` name derive rides the unchanged
machinery; only `RegisterInput` is pinned (F9).

**5. Contracts restated in another medium.** Production (this file) +
authoritative contract ([spec-040][spec-040] Decisions 3/5/6/8/9/11 + D-N1/D-N3)
+ independent oracles ([test-auth-mutations][test-auth-mutations] (2701 lines),
[test-auth-queries][test-auth-queries], [test-auth-sessions][test-auth-sessions])
+ projections (module docstring, README usage blocks) + consumer
([accounts-schema][accounts-schema]). Oracles never read the owner: the
enumeration guard asserts the literal `("__all__", ["Incorrect
username/password"])` tuple; the seal/conflict/dispatch/bind oracles assert
behavior (raises, identity, call counts, payload presence). Counts below count
definitions only; oracles/projections are listed per finding.

**6. Enforcement by omission.** Three deliberate omissions, each with a
contract source: no relation-visibility helper on the rider (D-N3, in-file
`Meta` comment + F18 — the shared decode's own handling is inherited, so no
second auth-local rule exists); `validate_password` errors keyed to
`password` directly, NOT via `validation_error_to_field_errors` (D-N2, F18
nested rejection); logout-only schemas bind with no user type (Decision 8,
F19 — the surface-keyed bind never resolves one). Axis-6 sweep over the four
factories + rider finds no member lacking a guard its contract requires (the
permission gate runs on all four surfaces incl. `current_user`; the capability
check runs on login/logout; `require_session` runs on both).

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **72 top-level statements** (1 docstring + 21 imports + 9
module-level constant/ledger bindings + 1 clear-registration + 2 classes + 32
functions + 6 ledger-alias/registration statements grouped above). The audit
dossier counts **39 rule-bearing definitions** (2 classes + 5 methods + 32
functions). Every one lands below; every challenge in `### Challenges` ends
in a family row, a file-local row, or a rejection.

| # | Member | Home |
|---|---|---|
| 1 | `_AUTH_FAMILY_LABEL` | F7 |
| 2 | `_INCORRECT_CREDENTIALS_MESSAGE` | F8 |
| 3 | `_WEBSOCKET_LOGIN_UNSUPPORTED` | F8 |
| 4 | `_WEBSOCKET_LOGOUT_UNSUPPORTED` | F8 |
| 5 | `_REGISTER_INPUT_NAME` | F9 |
| 6 | `_REGISTER_EXCLUDED_INPUT_FIELDS` | F9 |
| 7 | `_REGISTER_PROTECTED_FIELDS` | F9 |
| 8 | `_SURFACE_FACTORY_NAMES` | F9 |
| 9 | `_auth_declaration_registry` + `register/clear/iter_/store` aliases + `register_subsystem_clear` row | F4 + F10 |
| 10 | `_AuthMutationMetaSnapshot` + `__init__`/`__setattr__`/`__delattr__` | F6 (new family, slot sub-rule) |
| 11 | `_SealedAuthHolderMeta` + `__setattr__`/`__delattr__` | F6 (new family, head sub-rule) |
| 12 | `_make_permission_holder` | F10 |
| 13 | `_declared_auth_surface` | F10 |
| 14 | `_reject_conflicting_permission_classes` | F10 |
| 15 | `_declare_auth_surface` | F10 |
| 16 | `_declare_fixed_auth_surface` | F10 (consumed by [auth/queries.py][auth-queries] by call) |
| 17 | `_sync_bridged_async_body` | F11 (consumed by [auth/queries.py][auth-queries] by call) + F2 consumer |
| 18 | `_make_auth_field` | F11 (+ nested rejection vs `make_resolver_entries`) |
| 19 | `_authenticated_actor_or_none` | F12 + F1 member sites |
| 20 | `_failed_login_payload` | F14 |
| 21 | `_transport_prologue` | F13 |
| 22 | `_login_result_payload` | F14 |
| 23 | `_login_authenticate` | F13 |
| 24 | `_django_http_login_establish` | F15 |
| 25 | `_channels_http_login_establish` | F15 + F2 consumer |
| 26 | `_login_resolve_body` | F16 |
| 27 | `_login_resolve_body_async` | F16 + F2 consumer |
| 28 | `_logout_prologue` | F13 |
| 29 | `_logout_observation` | F14 |
| 30 | `_django_http_logout` | F15 |
| 31 | `_channels_logout` | F15 + F3 member |
| 32 | `_logout_resolve_body` | F16 |
| 33 | `_logout_resolve_body_async` | F16 + F2 consumer |
| 34 | `login_mutation` | F17 |
| 35 | `logout_mutation` | F17 |
| 36 | `derive_register_fields` | F18 |
| 37 | `_register_decode_step` | F18 |
| 38 | `_register_write_step` | F18 (+ nested D-N2 rejection) |
| 39 | `_run_register_pipeline_sync` | F18 |
| 40 | `_synthesize_register_rider` (+ inner `Register`/`Meta`/`input_type_name`/`build_input`/`resolve_sync`/`resolve_async`) | F18 (+ D-N3 omission note) + F2 consumer (`resolve_async`) |
| 41 | `register_mutation` | F17 |
| 42 | `_resolve_user_primary_or_raise` | F5 (family row) |
| 43 | `bind_auth_mutations` | F19 (called by [finalizer.py][finalizer] by name) |

Seven indexed families considered: five reused as rows (F1–F5), two checked
with no surface (`sync-boundary-recourse-wording`, `queryset-seed-and-model-read`,
C6–C7 — do not inherit). One new family named (F6, two sub-rules for Worker 0
to add). Thirteen file-local rows (F7–F19 minus the six family rows).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 disposal protocol | route refused awaitables through a new protocol (e.g. cancel futures too) | **3 sites, 2 owners** (the two inline copies + [utils/querysets.py][utils-querysets]`::_dispose_sync_awaitable`); within-file count alone is **2** (both copies move together) | family row (open family decides) |
| C2 | F2 boundary shape | change the worker (e.g. thread-sensitivity) | **1** (utils owner; all auth call sites follow by call) | consumer — do not inherit |
| C3 | F3 lease semantics/order | change lease acquisition or the outer/inner order | **1** (utils owner for the lease; this file is the ONE site holding both, order prose is projection at both ends) | consumer/enforcement — verified, not inherited |
| C4 | F4 clear phases | add a clear phase / change bus semantics | **1** (registry bus; the `auth.declarations` row re-declares its flag) | consumer — verified, not inherited |
| C5 | F5 primary-resolution split | change the `get`→`types_for` two-case split | **2** (`_resolve_primary_type` + `_resolve_user_primary_or_raise`) | family row (Decision-8 wording stays separate) |
| C6 | `sync-boundary-recourse-wording` | change any recourse sentence | **0 here** (no recourse string minted; discipline via shared machinery) | no surface — do not inherit |
| C7 | `queryset-seed-and-model-read` | change the model source | **0 here** (no `model_for` call; snapshot `.model` is the owned source) | no surface — do not inherit |
| C8 | F6 seal behavior | change the seal (exception type, re-seal rule) | **4 sites, 2 shapes** (slot pair + head pair) | NEW family `sealed-authorization-source` |
| C9 | F7 family label | rename the auth request family | **1** (the constant; all call sites pass it by reference) | file-local |
| C10 | F8 failure message | reword the undifferentiated message | **1** (the constant; oracle lists the literal) | file-local |
| C11 | F8 ws rejections | reword either transport rejection | **1** each (free wording, top-level errors) | file-local |
| C12 | F9 register names | rename `RegisterInput` / change payload derive | **1** (constant + unchanged machinery) | file-local |
| C13 | F10 conflict key | admit a presentation kwarg into the key | **1** (auth-local rule; spec pins the key to `permission_classes`) | file-local (probe P2) |
| C14 | F11 dispatch seam | change sync/async dispatch (new executor mode) | **1** (the seam; `make_resolver_entries` doesn't move — different contract) | file-local + nested rejection |
| C15 | F12 anonymity shapes | admit a 6th hostile shape | **1** (the function; `logout` + `current_user` follow by call) | file-local (probe P1) |
| C16 | F14 login envelope | change the failed-login shape | **1** (the ctor; both bodies follow by call; oracle lists) | file-local |
| C17 | F13 prologue order | insert a login/logout prologue step | **1** per prologue (sync + async bodies follow by call) | file-local |
| C18 | F15 compensation | change compensation (e.g. log instead of chain) | **2** per transport pair (Django + Channels twins move together) | file-local, principle-5 twins |
| C19 | F18 password steps | change hashing/validation (new validator call) | **1** (the write step; skeleton follows) | file-local |
| C20 | F19 bind order/keying | move the phase-2.5 slot / add a 5th surface | **1** (finalizer owns the slot; the bind owns keying) | file-local |
| C21 | F18 D-N2 non-reuse | key `validate_password` errors via the generic mapper | **0 saved** (would mis-key to `"__all__"`; deliberate) | nested rejection |
| C22 | F18 D-N3 omission | give the rider its own visibility helper | **0 existing** (inherits the shared decode's; no second rule exists) | justified omission, not a defect |

Executable proofs: P1 (13 checks, execution-verified) discharges C15 + the
F1 outcome half (coroutine closed, no warning under `-W error`; future-left-pending
delta documented for the family); P2 (7 checks, execution-verified) discharges
C13 (cache/conflict/drain). Both ran as read-only scripts in the shared tree
(no source mutation, no DB writes, process-local registry use only):
`uv run python docs/dry/temp-tests/dry-file-auth__mutations/probe_anonymity.py`,
`uv run python docs/dry/temp-tests/dry-file-auth__mutations/probe_ledger.py`.
`uv run python docs/dry/temp-tests/dry-file-auth__mutations/probe_ledger.py`.
All other claims are `static-reviewed` (import moves, bodies composed by name,
single spanning reads).

## Findings

No production edit is owed by a file item; each finding records the rule with
the challenge that proved its home. `Migration: none` throughout (zero-edit
item) — stated once here, not per row. `Coupling: none` throughout (file item
consolidates nothing) — likewise stated once.

### F1 — `awaitable-refusal-and-disposal` (family row, open)

- **Contract + variation.** Release a refused awaitable without awaiting it.
  Legitimate variation: which awaitable kinds get closed/cancelled/ignored.
- **Sites + roles.** *Definition (owner)*:
  [utils/querysets.py][utils-querysets]`::_dispose_sync_awaitable` (close
  coroutine / cancel future / ignore the rest). *Second-definition candidates*:
  this file's two inline detect-then-dispose copies
  ([auth/mutations.py][auth-mutations]`::_authenticated_actor_or_none` —
  `inspect.isawaitable` → `suppress(BaseException)`-wrapped `.close()` →
  anonymous — twice: legacy-call result and raw value; re-derived fresh from
  this side, not inherited). *Consumers*: `logout` ok-capture +
  `current_user` return (by call of the containing function). *Oracles*:
  hostile-awaitable tests + probe P1.
- **Challenges.** C1 → 3 sites / 2 owners (within-file count 2).
- **Owner + lifetime.** Indexed family owns the decision; no stored
  derivation here. Documented delta for the family item (probe P1): a `Future`
  value is left pending by the inline copies (`.close` absent → suppressed)
  where the owner would cancel it; outcome (anonymous) is identical and
  fail-closed, coroutine hygiene verified (`CORO_CLOSED`, no warning under
  `-W error`). No contract row requires cancellation at this site, so this is
  consolidation input, not a defect.
- **Distinct behavior.** Refusal (collapse to anonymous) vs the sync-pipeline
  refusal (raise `SyncMisuseError`) — different contracts sharing only the
  disposal half.
- **Behavioral proof.** `execution-verified` (P1: 13/13). Rejects "an
  awaitable `is_authenticated` escapes or warns" (collapses to `None`,
  coroutine closed).
- **Structural gate.** Hostile-awaitable collapse tests in
  [test-auth-mutations][test-auth-mutations] (pre-existing); negative control
  = P1's `non-listed-shape-propagates` + `coroutine-closed-after-refusal`
  checks.
- **Freshness.** Target `dbe64995b87240b87a1d5119f46cc42c7cab646f`,
  [utils/querysets.py][utils-querysets] `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`,
  [test-auth-mutations][test-auth-mutations] `6390492979efe8ee6f9268a355b1f75404bbdbc6`.

### F2 — `one-sync-boundary` (family row, consumer)

- **Contract + variation.** Every async surface needing sync ORM work runs it
  in ONE `sync_to_async(thread_sensitive=True)` worker. No local variation.
- **Sites + roles.** *Definition*:
  [utils/querysets.py][utils-querysets]`::run_in_one_sync_boundary`.
  *Consumer sites here (by call, one per index — verified against the whole
  file)*: `_sync_bridged_async_body`, `_login_resolve_body_async` (both arms),
  `_logout_resolve_body_async` (both arms), rider `resolve_async`. *Oracles*:
  the `_sync_boundary_spy` dispatch tests
  (`test_sync_login_dispatch_never_enters_the_async_boundary`,
  `test_async_login_dispatch_awaits_the_native_async_body_exactly_once`,
  logout twins) + `test_bridged_async_body_is_a_real_coroutine_function`.
- **Challenges.** C2 → 1.
- **Owner + lifetime.** Indexed owner; no stored derivation. Checked —
  consumer only, do not inherit.
- **Behavioral proof.** `static-reviewed` (call sites name the owner; oracles
  pin call counts). **Structural gate.** The spy tests above (pre-existing).
- **Freshness.** Target as F1; utils-querysets as F1;
  [auth-conftest][auth-conftest] `74c62311315801dd946e3e017d587ded828a6f5e`.

### F3 — `ws-connection-actor-state` (family row, enforcement verified)

- **Contract + variation.** The connection actor lease serializes WebSocket
  revalidation checkpoints against package-owned actor transitions; scope
  session lock OUTER, actor lease INNER at the one site holding both.
- **Sites + roles.** *Definition*: [utils/sessions.py][utils-sessions]`::actor_lease`
  (+ `actor_transition`). *Enforcement site here*:
  [auth/mutations.py][auth-mutations]`::_channels_logout` (holds
  `scope_session_lock` OUTER, `actor_transition` INNER; `was_authenticated`
  latched from the under-lock `ok` observation). *Companion evidence*:
  [utils/sessions.py][utils-sessions] module docstring (names exactly this site
  + order — verified verbatim) and this function's docstring (records the
  order + the head-of-line consequence pointer). *Negative sites* (verified
  holding NO lock, as documented): `_django_http_login_establish`,
  `_django_http_logout` — Channels-scope-only by construction.
- **Challenges.** C3 → 1 (lease owned in utils; the order has exactly one
  holding site, order prose is projection at both ends).
- **Owner + lifetime.** Indexed owner; the lease is per-scope runtime state,
  not a stored derivation owed lifetime fields here.
- **Behavioral proof.** `static-reviewed` (lock-order prose verified verbatim
  against both docstrings; `actor_transition` reached by call).
  **Structural gate.** WebSocket revalidation + logout-interaction tests in the
  consumers/auth suites (pre-existing; this file adds no new gate).
- **Freshness.** Target as F1; [utils/sessions.py][utils-sessions]
  `f0d9297c942a4915ca08ac0714cee73f6042af34`; [consumers.py][consumers]
  `18f3ea161b6081a91445796902a9635cb7e2e3bc`.

### F4 — `subsystem-clear-lifecycle` (family row, consumer verified)

- **Contract + variation.** Every subsystem registers teardown on the
  [registry.py][registry] bus with a stable owner + phase flag; full clears
  drain everything, pre-bind resets drain only `before_bind` rows.
- **Sites + roles.** *Definition*: [registry.py][registry]`::register_subsystem_clear`
  / `::iter_subsystem_clears` / `::_subsystem_clears`. *Row here*:
  `register_subsystem_clear(clear_auth_mutation_registry,
  owner="auth.declarations")` — full-clear-ONLY (no `before_bind`, verified
  off the call), so declarations survive the pre-bind reset for the phase-2.5
  re-read, and draining the ledger drains the same-args cache (fresh-holder
  proof in P2). *Sister rows* (surveyed, untouched): relay/filters/orders/
  mutations/forms/rest/connection/queries-alias rows. *Consumer of the bus*:
  [finalizer.py][finalizer] pre-bind reset + `TypeRegistry.clear()`.
- **Challenges.** C4 → 1.
- **Owner + lifetime.** Indexed owner (bus); the flag choice is this row's
  declaration, justified by the Decision-9 lifecycle in the module docstring.
- **Behavioral proof.** `execution-verified` (P2 drain/re-mint) +
  `static-reviewed` (flag read off the call). **Structural gate.**
  `test_declarations_survive_the_pre_bind_reset`,
  `test_registry_clear_drains_ledger_and_resets_conflict_state` (pre-existing).
- **Freshness.** Target as F1; [registry.py][registry]
  `9cc8bb553fd417fc465809a541769a8383469cda`;
  [finalizer.py][finalizer] `77fd9a2dd229eb9de5f29188c5058035d3606323`.

### F5 — `type-registry-model-type-map` (family row, candidate member)

- **Contract + variation.** "What counts as the registered primary" + the
  two-case finalize error split (no-type vs ambiguous). Wording varies per
  flavor by necessity (Decision 8: the auth message must name the consumer's
  factories and pre-empt the generic mutation message).
- **Sites + roles.** *Existing definition*:
  [mutations/sets.py][mutations-sets]`::_resolve_primary_type` (generic
  mutation wording). *Candidate second definition*:
  [auth/mutations.py][auth-mutations]`::_resolve_user_primary_or_raise`
  (same `registry.get` → `types_for` split, auth-factory wording, fired from
  the phase-2.5 slot BEFORE `bind_mutations()` so the generic message can
  never pre-empt it — ordering verified in [finalizer.py][finalizer]).
  *Owner of the read*: the registry getter itself.
- **Challenges.** C5 → 2 for the split mechanism; 1 per wording (each message
  moves alone). The auth-first ordering is a distinct, intentionally separate
  rule owned by the finalizer.
- **Owner + lifetime.** Indexed family decides: shared split helper vs the
  current mirror. No stored derivation.
- **Behavioral proof.** `static-reviewed` (both bodies read; split steps
  match). **Structural gate.**
  `test_login_only_schema_without_user_type_raises_the_login_arm_error`,
  `test_register_only_schema_without_user_type_raises_the_register_arm_error`,
  `test_ambiguous_user_primary_raises_the_set_meta_primary_message`
  (pre-existing; pin the auth wordings independently of the generic one).
- **Freshness.** Target as F1; [mutations/sets.py][mutations-sets]
  `cffa29e52002e1cfef94a032366524fb69c9d258`.

### F6 — `sealed-authorization-source` (NEW family, two sub-rules)

- **Contract + variation.** A per-request authorization source captured at
  declaration time is immutable afterwards: creation-time write honored once;
  later writes/deletes raise `ConfigurationError` (0.0.15 hardening vs a
  `has_permission` hook rebinding the source for later requests — the
  persistent cross-request bypass class). Varies only in carrier shape.
- **Sites + roles.** *Sub-rule (a) slot seal — existing definition*:
  [mutations/sets.py][mutations-sets]`::_ValidatedMutationMeta` (full Meta
  record, 15 slots). *Sub-rule (a) second shape*:
  [auth/mutations.py][auth-mutations]`::_AuthMutationMetaSnapshot`
  (duck-typed `operation` + `permission_classes`, 3 slots — deliberately NOT
  a `_ValidatedMutationMeta`, which requires model kwargs a model-less field
  lacks; the docstring states the mirror). *Sub-rule (b) head seal — existing
  definition*: [mutations/sets.py][mutations-sets]`::make_meta_validating_metaclass`
  (generic factory; creation write honored once). *Sub-rule (b) second shape*:
  [auth/mutations.py][auth-mutations]`::_SealedAuthHolderMeta`
  (single-purpose metaclass; the holder path has no `Meta` and must not enter
  the mutation ledger, so the factory's `__new__` doesn't fit — only the seal
  halves match). Cross-mentions are one-directional (auth cites sets; sets
  never cites auth). *Oracles*:
  `test_auth_permission_holder_snapshot_is_sealed`,
  `test_auth_permission_holder_head_is_sealed`.
- **Challenges.** C8 → 4 sites / 2 shapes for a seal-behavior change; 1 per
  shape for a slot/carrier change. The carrier-shape difference is real
  (model-backed record vs model-less duck type), so the family item must
  decide shared-mixin vs documented mirror.
- **Owner + lifetime.** Proposed: narrowest cohesive owner every consumer can
  depend on without reversing a dependency (principle 7) — likely a small
  seal helper near the existing owners; the family item decides. Lifetime:
  process-lifetime immutability, stated in both docstrings.
- **Behavioral proof.** `static-reviewed` (both seal bodies read; threat
  models match verbatim). **Structural gate.** The two seal tests above
  (pre-existing; each pins one shape independently).
- **Freshness.** Target as F1; mutations-sets as F5.
- **Worker-0 rows owed:** one `## Families` item
  (`Family sealed-authorization-source`) and index rows for its two sub-rules
  (slot seal: `_ValidatedMutationMeta` + `_AuthMutationMetaSnapshot`; head
  seal: `make_meta_validating_metaclass` + `_SealedAuthHolderMeta`), holding
  item `Family sealed-authorization-source`, status `open`.

### F7 — auth request family label (file-local)

- **Contract + variation.** Every auth surface resolves its request under one
  module-level constant (`"AuthMutation"`), never a per-field literal — the
  spec-040 D1 wording-drift guard. Varies only in spelling.
- **Sites + roles.** *Definition*: `_AUTH_FAMILY_LABEL`. *Consumer sites*:
  `_transport_prologue`, both async bodies' `request_from_info` calls,
  [auth/queries.py][auth-queries] resolve body (by import). *Owner of the
  resolution*: [utils/permissions.py][utils-permissions]`::request_from_info`.
- **Challenges.** C9 → 1.
- **Owner + lifetime.** This module (narrowest owner its consumers already
  import). No stored derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Any drift
  fails loudly at the `family_label` attribution in resolution errors; no
  bespoke gate owed (principle-9 economy).
- **Freshness.** Target as F1; [utils/permissions.py][utils-permissions]
  `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`.

### F8 — failure + transport-capability wordings (file-local)

- **Contract + variation.** `_INCORRECT_CREDENTIALS_MESSAGE`: the single
  undifferentiated login-failure message, byte-identical for unknown-user /
  wrong-password / inactive / unstorable (anti-enumeration, Decision 5 — NOT
  split, ever). `_WEBSOCKET_*_UNSUPPORTED`: actionable transport-capability
  rejections — top-level `ConfigurationError`s, explicitly NOT part of the
  byte-compatible envelope, so wording is free.
- **Sites + roles.** *Definitions*: the three constants. *Consumers*: failed
  envelope ctor (F14); capability checks in `_transport_prologue` (F13).
  *Oracle (independent)*: the enumeration-guard assertion
  `("__all__", ["Incorrect username/password"])` in
  `test_async_channels_http_wrong_password_is_failed_login_envelope_session_untouched`
  (pins the literal without reading the constant) + the byte-identical
  wrong-password/unknown-user coverage around it.
- **Challenges.** C10, C11 → 1 each.
- **Owner + lifetime.** This module (the messages are auth-surface-specific;
  no narrower owner exists). No stored derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** The
  enumeration-guard oracle above (pre-existing); the WS rejections need no
  wording pin (free by contract) — their *firing order* (before auth/session
  mutation) is pinned by `test_websocket_login_is_rejected_before_authenticate_is_called`.
- **Freshness.** Target as F1.

### F9 — register naming / exclusion / protection / surface-name tables (file-local)

- **Contract + variation.** `_REGISTER_INPUT_NAME` (`"RegisterInput"`): the
  pinned public input name (the model-derived default would be the shape name;
  the PAYLOAD name has no seam — `Register`→`RegisterPayload` derives through
  the unchanged machinery). `_REGISTER_EXCLUDED_INPUT_FIELDS` (`{password}`):
  captured out of model construction with the provided-marker preserved (D6
  seam). `_REGISTER_PROTECTED_FIELDS`: account-control fields that must never
  become registration input even if a custom model lists them in
  `USERNAME_FIELD`/`REQUIRED_FIELDS`. `_SURFACE_FACTORY_NAMES`: surface key →
  consumer-facing factory name for Decision-8 bind errors.
- **Sites + roles.** *Definitions*: the four constants. *Consumers*:
  `build_input` pinning, `mutation_input_field_specs(excluded_attrs=...)`,
  `derive_register_fields`, `_resolve_user_primary_or_raise` messages.
  *Oracles*: `test_derive_register_fields_*` (incl. protected-field and
  unknown-name rejection), input-name SDL assertions, bind-error message
  tests.
- **Challenges.** C12 → 1 (name pin vs derive are one rule: the input name is
  pinned BECAUSE the shape default is deterministic — a single contract with
  two spellings owned here).
- **Owner + lifetime.** This module. No stored derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** The derive +
  exclusion-seam + bind-message tests above (pre-existing).
- **Freshness.** Target as F1; [mutations/inputs.py][mutations-inputs]
  `fc4420475f404297822d7d94bee7bdd275700803`.

### F10 — declaration-cache-conflict machine (file-local)

- **Contract + variation.** One declaration per surface per process over the
  disjoint auth ledger: same normalised `permission_classes` → cached holder
  (every-call re-record is identity-deduped, so reloads re-append without
  duplicating); different → loud `ConfigurationError`; draining the ledger
  drains the cache (post-`clear()` re-declaration mints fresh). The conflict
  key is the schema-affecting args ONLY (`permission_classes`;
  `description`/`deprecation_reason`/`directives` never enter it — pinned by
  `test_presentation_kwargs_never_enter_the_conflict_key`). The fixed path
  records on the auth ledger only; `register_mutation` records on BOTH
  ledgers (mutation ledger for `bind_mutations()`, auth ledger for the
  Decision-8 register-arm validation).
- **Sites + roles.** *Driver (owner)*:
  [mutations/sets.py][mutations-sets]`::make_declaration_registry` (shared
  mechanics, disjoint stores — principle 1). *Auth-local rule here*:
  `_make_permission_holder` (the ONE synthesis site: duck-typed snapshot +
  `DjangoMutation.check_permission` bound directly, so iteration/denial/
  async-guard are reused by call), `_declared_auth_surface`,
  `_reject_conflicting_permission_classes`, `_declare_auth_surface`,
  `_declare_fixed_auth_surface`. *Cross-module consumer by call*:
  [auth/queries.py][auth-queries]`::current_user` (fourth surface through the
  same path). *Oracles*: `test_same_args_factory_calls_dedupe_to_one_cached_holder`,
  `test_conflicting_permission_classes_second_call_raises`,
  `test_registry_clear_drains_ledger_and_resets_conflict_state`,
  `test_factory_after_finalize_raises_the_standing_configuration_error`,
  `test_register_factory_recache_and_reregister_on_every_call`.
- **Challenges.** C13 → 1 (key rule lives here; the dedup/reject/clear
  mechanics live in the driver).
- **Owner + lifetime.** Driver owns mechanics; this module owns the key +
  synthesis. Ledger lifetime = process (full-clear-only, F4).
- **Behavioral proof.** `execution-verified` (P2: 7/7 — cache identity,
  conflict raise, `()`-vs-`[DjangoModelPermission]` distinctness, drain,
  fresh re-mint with new classes). Rejects "a drained ledger trips a stale
  conflict" and "re-record duplicates".
- **Structural gate.** The five oracles above (pre-existing); negative
  control = P2's distinct-keys-conflict + post-clear-fresh-mint checks.
- **Freshness.** Target as F1; mutations-sets as F5; auth-queries
  `5c59ba75023d21998efc6a8b1b714bdfab273ad7`.

### F11 — field construction + interim async bridge (file-local + nested rejection)

- **Contract + variation.** `_make_auth_field`: the ONE fixed-field ctor —
  sync/async dispatch per call via
  [utils/execution_mode.py][utils-execution]`::async_execution`, injected
  `__signature__`/`__annotations__` over `_lazy_ref` refs, directives through
  the shared validator. `_sync_bridged_async_body`: the interim seam — a real
  coroutine fn bridging through the one shared worker so native per-transport
  async work can replace it per surface later (login/logout already carry
  native async bodies; `current_user` rides the bridge).
- **Sites + roles.** *Definition*: the two helpers. *Shared by call* (never
  re-spelled): `_lazy_ref`, `build_lazy_field_signature`
  ([mutations/fields.py][mutations-fields]), `validated_field_directives`
  ([utils/directives.py][utils-directives]), `async_execution`, the boundary
  (F2). *Consumers*: the three factories here + `current_user` in
  [auth/queries.py][auth-queries]. *Oracles*: `test_bridged_async_body_is_a_real_coroutine_function`,
  `test_auth_field_dispatch_splits_sync_and_async_resolver_bodies`, the four
  dispatch-spy tests.
- **Challenges.** C14 → 1.
- **Owner + lifetime.** This module (auth-fixed-field shape). No stored
  derivation.
- **Behavioral proof.** `static-reviewed` (seams named by the owner; oracles
  pin dispatch counts + coroutine reality). **Structural gate.** The oracles
  above (pre-existing).
- **Rejection (nested).** Considered: fold the dispatch seam into
  [mutations/resolvers.py][mutations-resolvers]`::make_resolver_entries`.
  Contract difference: the write entries wrap ONE sync body in the shared
  boundary (sync-only ORM pipeline); the auth seam dispatches between a sync
  body and a NATIVE async body carrying per-transport awaits (Channels
  login/logout must await `channels.auth` + session persistence natively —
  a single sync body cannot express that). Posit a new executor mode → only
  the auth seam moves. Trigger: unifying the write pipeline onto native
  per-transport async bodies would make the seams one rule. Durable home:
  `_make_auth_field` docstring (already states the seam/specialization split).
- **Freshness.** Target as F1; [mutations/fields.py][mutations-fields]
  `cf518361d7884b8b71550cb6b73bff0c1a64549e`;
  [utils/directives.py][utils-directives]
  `380786cf7b3213603a592717cc65386892d7bf50`;
  [utils/execution_mode.py][utils-execution]
  `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9`.

### F12 — the anonymity definition (file-local)

- **Contract + variation.** `_authenticated_actor_or_none`: the ONE
  anonymous-vs-authenticated classifier shared by `logout`'s `ok` and
  `current_user`'s nullable return (no-`user`-attr and unauthenticated both
  anonymous; exactly five hostile shapes collapse to anonymous; anything else
  — e.g. a store `DatabaseError` — propagates so outages are never hidden).
- **Sites + roles.** *Definition*: the function (incl. the F1 inline disposal
  copies, routed separately). *Consumers by call*: `_logout_observation` +
  [auth/queries.py][auth-queries] resolve body. *Oracles*: hostile-truthiness
  ×5 tests, lazy/modeless-actor tests, live hostile-logout test (fail-closed
  teardown), probe P1.
- **Challenges.** C15 → 1 (a 6th shape moves the function; both consumers
  follow).
- **Owner + lifetime.** This module. No stored derivation.
- **Behavioral proof.** `execution-verified` (P1: 13/13 — all four hostile
  surfaces + positive/negative actors + propagation asymmetry). Rejects
  "logout-`ok` and `me` can disagree" (both derive from this result) and
  "a hostile value escapes as a top-level error" (for the five shapes).
- **Structural gate.** The hostile-shape tests above (pre-existing);
  negative control = P1's `non-listed-shape-propagates` check.
- **Freshness.** Target as F1.

### F13 — transport + login/logout prologues (file-local)

- **Contract + variation.** Fixed step order, no session mutation:
  `_transport_prologue` (resolve → classify → capability-reject → require
  session; parameterised by per-surface predicate+message); `_login_authenticate`
  (prologue → gate with username-only `data` (NEVER the password) → storability
  preflight → exactly ONE `authenticate()` call, no local user-model query —
  the actor-not-lookup rule D-N1); `_logout_prologue` (prologue → gate →
  payload class; model-less denial reads the holder name for the pinned
  `"Not authorized to logout Session."` string).
- **Sites + roles.** *Definitions*: the three functions. *Shared by call*:
  `classify_transport` / `login_supported` / `logout_supported` /
  `require_session` ([auth/sessions.py][auth-sessions]), `authorize_or_raise`
  + `payload_cls_for` ([mutations/resolvers.py][mutations-resolvers]),
  `unencodable_text_error` ([utils/write_values.py][utils-write-values]).
  Each prologue is consumed by BOTH its sync body and its async arm (async
  runs it inside the one boundary). *Oracles*: gate-string tests
  (`test_gated_login_denies_with_the_exact_pinned_string_before_authenticate`,
  `test_gated_logout_denies_with_the_session_holder_string`,
  `test_login_gate_sees_the_attempted_username_and_never_the_password`),
  capability-order tests, preflight tests.
- **Challenges.** C17 → 1 per prologue.
- **Owner + lifetime.** This module (auth state-machine order). No stored
  derivation.
- **Behavioral proof.** `static-reviewed` (order read off the bodies; no-arg
  / username-only gate data verified). **Structural gate.** The oracles above
  (pre-existing; the password-never-in-`data` test is the negative control
  for the rate-limit-keying claim).
- **Freshness.** Target as F1; [auth/sessions.py][auth-sessions]
  `fad7feb883a3675710a55d71642b309e55f64104`;
  [mutations/resolvers.py][mutations-resolvers]
  `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`;
  [utils/write_values.py][utils-write-values]
  `d28587c7c8d9f0d25e0a01bf289a63d9c3291728`.

### F14 — payload construction observations (file-local)

- **Contract + variation.** `_failed_login_payload`: the ONE undifferentiated
  envelope (`node`/`result` `None` + single non-field-keyed entry via
  `field_error("", …)` — the D8 reuse; no error code, deliberately).
  `_login_result_payload`: failed→envelope / success→object payload, built
  BEFORE session mutation so a construction failure creates no orphan session
  (pinned by
  `test_login_payload_construction_failure_is_execution_error_session_untouched`).
  `_logout_observation`: pre-teardown `ok` capture + payload-before-mutation
  (shared anonymity definition, F12).
- **Sites + roles.** *Definitions*: the three ctors. *Shared by call*:
  `field_error`, `build_payload` ([mutations/resolvers.py][mutations-resolvers]
  + [utils/errors.py][utils-errors] for the `""`→`"__all__"` rule). Each ctor
  is consumed by both its sync and async bodies.
- **Challenges.** C16 → 1 per ctor.
- **Owner + lifetime.** This module (auth envelope policy). No stored
  derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** The
  enumeration-guard + construction-failure + live hostile-`ok` tests
  (pre-existing).
- **Freshness.** Target as F1; resolvers + errors as F13/F6-chain:
  [utils/errors.py][utils-errors] `3e25e93bf2265209f79b03d4b17670814f25d676`.

### F15 — transport critical sections (file-local, principle-5 twins)

- **Contract + variation.** Mutate + durably persist, compensating
  fail-closed (local actor anonymized, partial durable row flushed, original
  error re-raised with cleanup chained via `__context__`, never a false
  success): Django-HTTP arms run Django's native `login`/`logout` + explicit
  save/flush with NO asyncio lock; Channels arms await `channels.auth` +
  explicit `asave()` (login) / native durable flush (logout, no double-flush)
  under the per-scope lock ONCE (non-reentrant — compensation runs inside the
  held lock); `_channels_logout` additionally holds the actor lease INNER
  (F3). Success payloads hold the user OBJECT (signal-updated `last_login`
  visible to nested fields).
- **Sites + roles.** *Definitions*: `_django_http_login_establish`,
  `_channels_http_login_establish`, `_django_http_logout`, `_channels_logout`.
  Twin pairs share one contract with different await points — the principle-5
  shape, contrast recorded in each docstring.
- **Challenges.** C18 → 2 per pair (twins move together on a compensation
  change; justified separation on await points — no consolidation owed).
- **Owner + lifetime.** This module. No stored derivation.
- **Behavioral proof.** `static-reviewed` (compensation paths read;
  lock/lease placement verified against F3). **Structural gate.** The
  login-compensation suite (`test_login_backend_selection_failure_compensates`,
  `test_login_session_cycle_failure_*`, `test_login_explicit_save_failure_compensates`,
  `test_login_cleanup_*`, cancellation twins, Channels round-trip tests)
  + live hostile-logout teardown test (pre-existing).
- **Freshness.** Target as F1.

### F16 — resolve bodies (file-local, principle-5 twins)

- **Contract + variation.** Login bodies: prologue → payload-before-mutation
  → transport critical section (sync bridges Channels-HTTP through the ONE
  permitted `async_to_sync` hop; async bridges Django-HTTP through the one
  boundary and awaits Channels natively). Logout bodies: prologue → critical
  section; `ok` keeps the shipped meaning (true only for a pre-teardown
  authenticated actor; anonymous logout still flushes residue → `{ok: false,
  errors: []}`). Transport classification runs on the event loop (pure, no
  ORM — never `SynchronousOnlyOperation`).
- **Sites + roles.** *Definitions*: `_login_resolve_body`,
  `_login_resolve_body_async`, `_logout_resolve_body`,
  `_logout_resolve_body_async`. Consumers of F2/F11/F13/F15 by call/composition.
- **Challenges.** Sync/async pair per surface = principle-5 twins (different
  await points, same observable contract incl. `ok` semantics) — no count
  above 1 per surface for a contract change.
- **Owner + lifetime.** This module. No stored derivation.
- **Behavioral proof.** `static-reviewed` + the F2 dispatch oracles.
  **Structural gate.** The `_sync_boundary_spy` dispatch tests + native-async
  Channels tests (`test_async_channels_http_wrong_password_*`,
  round-trip/cycle/flush tests) (pre-existing).
- **Freshness.** Target as F1.

### F17 — the three factories (file-local thin wrappers)

- **Contract + variation.** `login_mutation(username:, password:)` → bind-made
  `LoginPayload` (object slot typed as the consumer primary; username maps
  onto `USERNAME_FIELD` inside `ModelBackend`, AllowAny default = explicit
  `()`); `logout_mutation()` → model-less `{ok, errors}` (logout-only
  schemas need no user type — Decision-8 structural exemption);
  `register_mutation(data: RegisterInput!)` → rider through
  `DjangoMutationField`, re-recording on BOTH ledgers every call (F10).
  Vary only in surface + presentation kwargs.
- **Sites + roles.** *Definitions*: the three factories (declaration +
  wiring only; all behavior in F10/F11/F18/F19). *Consumers*:
  [accounts-schema][accounts-schema]. *Oracles*: surface-keyed bind tests
  (orphan-payload trio), reload-idempotence, recache/reregister tests.
- **Challenges.** A new surface reuses the whole path (declaration + field +
  bind arms) — 1 new declaration + bind-arm rows, never a new ledger.
- **Owner + lifetime.** This module (consumer-surface shape). No stored
  derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** The bind +
  reload oracles (pre-existing).
- **Freshness.** Target as F1; [accounts-schema][accounts-schema]
  `c0fdc23be03f7ea0c621492b96a1a4857ef60a74`.

### F18 — register derivation + step pair + rider (file-local + nested items)

- **Contract + variation.** `derive_register_fields`: USERNAME_FIELD first,
  then distinct REQUIRED_FIELDS in order, then `password` once (deduped);
  takes the model as an argument (custom-USERNAME_FIELD testable without an
  `AUTH_USER_MODEL` swap); protected/account-control fields raise; unknown /
  non-editable / reverse names rejected by DELEGATING to `editable_input_fields`
  (never a re-check). `_register_decode_step`: shared model decode + password
  capture (EXCLUDED kind keeps the provided-marker; unset → `None` password;
  list-passthrough on decode failure). `_register_write_step`: null/non-str/
  unstorable-password guards → `validate_password(raw, user)` with the
  constructed instance (UserAttributeSimilarity sees the submitted identity —
  deliberate improvement over upstream's user-less call) → `set_password`
  BEFORE `full_clean` → shared `_model_write_step` tail (the ONLY
  auth-specific steps are validate+hash). `_run_register_pipeline_sync`:
  unchanged skeleton (atomicity, authorize-before-decode, rollback
  short-circuits, by-pk-without-visibility `refetch_optimized` — the 036
  own-write exception). `_synthesize_register_rider`: lazy `Register`
  `DjangoMutation` (import must not materialize a phantom input/payload;
  pinned `__name__` for `RegisterPayload`; `input_type_name`/`build_input`
  seams; create-only `resolve_sync`/`resolve_async` discarding `id`).
- **Sites + roles.** *Definitions*: the five functions + rider (inner
  `Meta`/`input_type_name`/`build_input`/`resolve_sync`/`resolve_async`).
  *Shared by call*: `editable_input_fields`, `mutation_input_shape`,
  `build_mutation_input`, `materialize_mutation_input_class`,
  `mutation_input_field_specs`, `_model_decode_step`, `_model_write_step`,
  `run_write_pipeline_sync`, the boundary (F2). *Oracles*: derive trio +
  protected/unknown rejection tests, exclusion-seam tests (incl.
  three-tuple-no-exclusion guard), write-step quartet (null/non-str/
  surrogate/`validate_password`-keyed), gate tests (exact create-string,
  model-less-introspection raise), live register tests.
- **Challenges.** C19 → 1 per step; C21 → nested rejection; C22 → justified
  omission.
- **Owner + lifetime.** This module (registration policy); skeleton/ledger
  owners unchanged. No stored derivation.
- **Behavioral proof.** `static-reviewed` (step order + delegation read;
  `set_password`-before-`full_clean` verified). **Structural gate.** The
  oracles above (pre-existing; the non-str/surrogate guards are
  defense-in-depth with direct tests).
- **Rejection (nested, D-N2).** Considered: route `validate_password`
  failures through the generic `validation_error_to_field_errors` mapper.
  Contract difference: the mapper keys list-style `ValidationError`s (no
  `error_dict`) to the `"__all__"` sentinel; the register contract keys them
  to `password` directly (codes preserved per-leaf). Sharing the mapper would
  mis-key every password failure. Trigger: a mapper variant keyed by an
  explicit caller-supplied path would make the sites one rule. Durable home:
  `_register_write_step` docstring (already states the non-reuse).
- **Omission note (D-N3, axis 6).** The rider wires NO relation-visibility
  helper: the narrowed stock-user `Meta.fields` carries no relation input,
  and a custom-model forward-FK `REQUIRED_FIELDS` entry rides the shared
  decode's own `<field>_id` relation handling — inheriting whatever the
  shared path does. No second rule exists to consolidate; no guard is
  missing (enumerated: the rider is the only member; contract source =
  Decision 6 + in-file `Meta` comment). Not a defect.
- **Freshness.** Target as F1; inputs
  `fc4420475f404297822d7d94bee7bdd275700803`; resolvers
  `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`; write-values
  `d28587c7c8d9f0d25e0a01bf289a63d9c3291728`.

### F19 — surface-keyed phase-2.5 bind (file-local)

- **Contract + variation.** `bind_auth_mutations()`: no declared surfaces →
  no-op; else resolve the user primary at most once and ONLY for user-typed
  surfaces (login/register/current_user) via F5 (logout-only binds with no
  user type and emits no orphan payloads); materialize `LoginPayload`/
  `LogoutPayload` on the existing `mutations.inputs` row;
  `current_user` alias via the [auth/queries.py][auth-queries] namespace trio
  (function-local import — queries imports this module); register needs no
  auth-side emit (the rider is an ordinary `DjangoMutation` bound next by
  `bind_mutations()` in the pinned order). Runs AFTER the pre-bind emit reset
  and BEFORE `bind_mutations()` (Decision 9/8 ordering owned by
  [finalizer.py][finalizer], reached via the opt-in `loaded_attr` guard so
  auth-free processes never import this module).
- **Sites + roles.** *Definition*: the bind. *Called by name* from the
  finalizer; *consumers of* F5 + `build_payload_type` +
  `materialize_mutation_input_class` + `materialize_current_user_alias` by
  call. *Oracles*: orphan-payload trio, reload-cycle tests
  (`test_reload_idempotence_cycle_rebuilds_the_full_auth_surface`,
  `test_register_arm_error_survives_a_reload_cycle`), auth-free-subprocess
  tests, `test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads`.
- **Challenges.** C20 → 1 (slot owned by finalizer; keying owned here).
- **Owner + lifetime.** This module (auth bind keying); finalizer owns the
  slot. Emit artifacts ride others' ledgers (no new lifecycle).
- **Behavioral proof.** `static-reviewed` (keying + order read; guard
  verified in the finalizer). **Structural gate.** The oracles above
  (pre-existing).
- **Freshness.** Target as F1; finalizer
  `77fd9a2dd229eb9de5f29188c5058035d3606323`; auth-queries
  `5c59ba75023d21998efc6a8b1b714bdfab273ad7`.

## Defects

None meeting the bar (a defect names the contract row it breaks, a feasible
project shape under supported public API, and the wire/configuration input
that reaches it). Two observations were driven to a verdict and are NOT
defects:

1. **Future left pending by the inline disposal copies (F1 delta).** A
   `Future` as an `is_authenticated` VALUE is not cancelled (probe P1
   `future-left-pending-not-cancelled`). Outcome contract holds (fail-closed
   anonymous, no warning for the realistic coroutine shape); no contract row
   (spec-040, oracle, owner prose) requires cancellation at this site. Routed
   to Family `awaitable-refusal-and-disposal` as consolidation input, not
   fixed here.
2. **Per-login `FieldError` allocation in the unstorable preflight.**
   `_login_authenticate` builds two `FieldError`s to test for `None` and
   discards them. Same-observable-behavior allocation nit on an
   already-DB-bound path; no contract row covers allocation. Noted, not routed.

A pre-existing-failure check is owed and done: no test was run for this item
(per the dispatch: NO shared-tree pytest), so no failure predates or blocks
it; the two probes passed 20/20.

## Pending execution

None. Both executable proofs already ran to green as listed (P1: 13 checks;
P2: 7 checks); every other proof is `static-reviewed` by kind (import moves,
bodies composed by name). No `execution-deferred` proof exists. The final
suite gate belongs to the plan's gate item, not this file item.

## Judgment

Zero-edit file item. 72 top-level statements / 39 rule-bearing definitions
enumerated, all homed: five reused indexed families (F1 `awaitable-refusal-and-disposal`
as the open consolidation candidate incl. the within-file count-2 + future
delta; F2 `one-sync-boundary`, F3 `ws-connection-actor-state`, F4
`subsystem-clear-lifecycle` as verified consumers; F5
`type-registry-model-type-map` as candidate member), two indexed families
checked with no surface and not inherited
(`sync-boundary-recourse-wording`, `queryset-seed-and-model-read`), one NEW
family named with two sub-rules (F6 `sealed-authorization-source`), thirteen
file-local rows (F7–F19 minus the six family rows) each with its proving
challenge, three nested rejections/omission notes with triggers and durable
homes (F11 dispatch seam, F18 D-N2, F18 D-N3). No defects, no pending
execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `0bb0512a328773a9c695fc4b22cf8cff0b6bf0cf`: `git diff
<baseline> --stat` empty — target CLEAN. Target blob
`dbe64995b87240b87a1d5119f46cc42c7cab646f` matches both the working tree and
`HEAD:django_strawberry_framework/auth/mutations.py` (HEAD `9031cb3d`). The
artifact itself (`docs/dry/dry-file-auth__mutations.md`) is a new untracked
file, the item's only output, plus the untracked read-only probe pair under
`docs/dry/temp-tests/dry-file-auth__mutations/` (`probe_anonymity.py`,
`probe_ledger.py`; 20/20 green, process-local only). No `uv run ruff format .`
/ `ruff check` run (no edits to format). Concurrent dirt listed in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) plus sibling untracked `dry-file-*.md` artifacts were
left untouched; the `## Owned changes` ledger (walker D1 fix + 2 live test
files) gains no row from this item.

## Independent verification (Worker 2)

Own trace, recorded BEFORE reading `## Findings` (reconciliation follows per
row). Instrument: `ast.parse` over the working-tree target (blob
`dbe64995b87240b87a1d5119f46cc42c7cab646f`, 1396 lines): **72 top-level
statements, 39 rule-bearing definitions (2 classes + 32 functions + 5
methods)** — identical to W1's count, member-by-member confirmed (32 function
names in file order end at `bind_auth_mutations`; class methods 3 + 2).

Rules re-derived with owners I would choose, per posited change:

- Awaitable refusal/disposal: 2 inline `inspect.isawaitable` → `.close()` copies
  in `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`
  (legacy-call result + raw value) plus
  `django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable` = 3
  sites / 2 owners. Family row, open family decides. Agree with F1 (incl. the
  Future delta: re-ran probe P1 — future left pending, outcome anonymous,
  coroutine closed, no warning under `-W error`; consolidation input, not a
  defect since no contract row requires cancellation here).
- Sync boundary: 5 consumer call sites, all by call of
  `django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`
  (bridge seam, login-async both arms, logout-async both arms, rider
  `resolve_async`); no local worker. Consumer only. Agree with F2.
- Lease/order: one holding site
  `django_strawberry_framework/auth/mutations.py::_channels_logout` (scope lock
  OUTER, `actor_transition` INNER); negative sites `_django_http_login_establish`
  / `_django_http_logout` hold no lock as documented; order prose verified
  verbatim at both ends (`utils/sessions.py` names exactly this site).
  Enforcement site, not inherited. Agree with F3.
- Clear lifecycle: one row, full-clear-only (no `before_bind` flag on the call),
  ledger drain = cache drain (probe P2 re-run 7/7 green). Consumer. Agree F4.
- Primary-resolution split: `registry.get` → `types_for` two-case split exists
  twice (`_resolve_primary_type` generic wording +
  `_resolve_user_primary_or_raise` auth wording); wording differs deliberately
  per Decision 8 and the auth arm fires first (finalizer runs `bind_auth()`
  BEFORE `bind_mutations()`, verified in
  `django_strawberry_framework/types/finalizer.py`). Candidate member of the
  already-open family. Agree with F5; no index change owed (family row already
  lists this file).
- Seal behavior: 4 sites / 2 shapes (snapshot slot pair + holder-head pair),
  mirroring the sets.py halves with a real carrier difference (15-slot
  model-backed record vs 3-slot model-less duck type; generic Meta factory vs
  single-purpose holder metaclass). Cross-mentions one-directional (auth cites
  sets; 24 `auth` substrings in sets.py all generic `authorization` prose, zero
  module citations — grepped). Ruling below. Agree with F6.
- Label/wordings/tables/cache+conflict/field+bridge/anonymity/prologues/
  envelopes/critical sections/resolve bodies/factories/register steps/bind
  keying: each re-derived at 1 definition per posited change (twins move
  together per transport pair, which is principle-5 separation, not
  duplication). Owners: this module throughout; drivers own their mechanics
  (ledger, boundary, gate, payload, slot). Agree with F7–F19 file-local
  assignments.

Reconciliation vs W1: full agreement on every row F1–F19, both checked-no-surface
families, all three nested items, both non-defect observations, and Pending
(none). No oracle rewritten (enumeration guard asserts the literal
`("__all__", ["Incorrect username/password"])`; zero reads of the constant in
tests). Differences: none substantive. One cosmetic nit (not a defect, no
revision owed): the `### Challenges` prose lists the ledger-probe command twice.

Ruling — F6 `sealed-authorization-source` (NEW family): JUSTIFIED, and the
one-family/two-sub-rule shape is correct. Not one flat row (a seal-behavior
change moves 4 sites across 2 shapes — that shared count is the family's
reason to exist); not two separate families (splitting would lose exactly
that count); not a fold into `sealed-execution-queryset` (different contract:
queryset-execution sealing guards recomposition of validated query state with
defect codes, while auth-source sealing guards post-declaration rebinding of
authorization config against a hook-held class — posit a new queryset defect
code: only the queryset seal moves; posit a seal-exception change: only the
auth seals move; separate reasons to change). Worker 0 rows owed as W1 stated.

Ruling — F5 candidacy: VERIFIED. Same split mechanism, deliberately different
wording owned by Decision 8, distinct finalizer-owned ordering. Correctly
routed as candidate member, not a file-local row (names a second site) and not
a consolidation (file item consolidates nothing).

Enumeration: every member lands — 8 constants in F7/F8/F9 (rows 1–8), ledger
group in F4+F10 (row 9), 2 classes + 5 methods in F6 (rows 10–11), 32 functions
across F10–F19 + F5 (rows 12–43, with dual-homed bridge/resolve twins noted).
No member unassigned; no challenge homeless.

Equivalence (principle 8): zero-edit item — no observable behavior to prove
equivalent beyond preservation, which the empty item-scoped diff establishes
(`git diff 0bb0512a328773a9c695fc4b22cf8cff0b6bf0cf --
django_strawberry_framework/auth/mutations.py` empty, re-run by Worker 2;
working blob = HEAD blob = `dbe64995…`). Executable behavior claims re-verified
by re-running both read-only probes green (13 + 7); all other proofs are
`static-reviewed` by kind (call sites name owners; prose verified verbatim).
Structural gates are pre-existing and each pins its shape independently (2 seal
tests, enumeration guard, 4 dispatch spies + bridge-coroutine test, conflict
trio, bind/orphan/reload suites); negative controls live in the probes
(non-listed-shape propagates, coroutine-closed, distinct-keys-conflict,
post-clear-fresh-mint). Freshness: re-hashed 19 blobs — all match W1
(querysets `1539b66c…`, sets `cffa29e5…`, resolvers `3fd1e571…`, inputs
`fc442047…`, auth-queries `5c59ba75…`, auth-sessions `fad7feb8…`,
utils-sessions `f0d9297c…`, registry `9cc8bb55…`, finalizer `77fd9a2d…`,
consumers `18f3ea16…`, utils-permissions `9889d6fe…`, write-values
`d28587c7…`, errors `3e25e93b…`, fields `cf518361…`, directives `380786cf…`,
execution-mode `9805cdaf…`, test-mutations `63904929…`, auth-conftest
`74c62311…`, accounts-schema `c0fdc23b…`).

Rejections: F11 nested (fold into `make_resolver_entries`) — verified against
the body: entries wrap ONE sync body through the shared boundary, auth seam
dispatches sync vs NATIVE async bodies with per-transport awaits; trigger
correct. F18 D-N2 — verified against
`django_strawberry_framework/utils/errors.py::validation_error_to_field_errors`:
non-dict errors fall back to the sentinel, so sharing the mapper would mis-key
every password failure to `"__all__"`; trigger (caller-keyed mapper variant)
correct; durable home in the write-step docstring present. F18 D-N3 —
justified omission (in-file Meta comment present; stock narrowed fields carry
no relation input; custom FK rides the shared decode); only member enumerated.
Recourse/seed no-surface — verified by grep (no recourse string minted, no
`model_for` call). All carry difference + trigger + durable home.

AGENTS.md prose check: item-scoped diff empty, so no production prose risk;
artifact carries the `LINK DEFINITIONS` bottom block with the 10 canonical
group headers, `path::Symbol` citations, fingerprints as blob ids (required),
no process provenance; probes are untracked read-only temp scripts (no DB
writes, registry re-drained). No ruff run owed (markdown-only artifact append;
no `.py` edits — same basis as W1). Concurrent dirt untouched (verified via
`git status --short`: only pre-existing entries plus sibling untracked
artifacts; this item adds no tracked hunks and no `## Owned changes` row).

Defects (Worker 2): none. The two W1 observations stay non-defects (no
contract row: Future cancellation unrequired; preflight allocation nit).
No new defects found while tracing.

Verdict: `Status: verified`. Exact plan rows Worker 0 should write:

- Families line: `- [ ] Family `sealed-authorization-source` —
  [dry-rule-sealed-authorization-source.md](dry-rule-sealed-authorization-source.md)`
- Index row (slot seal): ``| `sealed-authorization-source (slot seal)` |
  `django_strawberry_framework/mutations/sets.py::_ValidatedMutationMeta` |
  `django_strawberry_framework/mutations/sets.py`,
  `django_strawberry_framework/auth/mutations.py` | Family
  `sealed-authorization-source` | open |``
- Index row (head seal): ``| `sealed-authorization-source (head seal)` |
  `django_strawberry_framework/mutations/sets.py::make_meta_validating_metaclass`
  | `django_strawberry_framework/mutations/sets.py`,
  `django_strawberry_framework/auth/mutations.py` | Family
  `sealed-authorization-source` | open |``

(F5 needs no index edit: `type-registry-model-type-map` already lists this
file; F1–F4 likewise already cover it.)

## Run 0.0.15 2026-09-30-8 re-trace (Worker-1, scoped; HEAD bytes)

Scope: FILE re-trace of `django_strawberry_framework/auth/mutations.py` at
HEAD bytes (`83998e08`, blob `72595bb188afd8dcc321638d97393fbd396a51b5`,
1535 lines). The run-7 record above is prior evidence only; every row below
re-verifies against current HEAD bytes with fresh evidence. Zero production
edits; zero tracked files changed.
`ITEM_BASELINE=b65886084f7b8474b0cf29c9728057ba35df8c39`.

Drift since the prior stamp (`9031cb3d`, blob
`dbe64995b87240b87a1d5119f46cc42c7cab646f`, 1396 lines): six commits,
`241+/102-`: `e6a33c46` (module-docstring first line, prose-only),
`999a1aab` + `b20277fe` (annotations/casts/comments; two runtime-identity
moves verified: `resolvers.field_error` → the same-object
`django_strawberry_framework/utils/errors.py::field_error`, `.model` reads
→ identity `django_strawberry_framework/mutations/sets.py::backing_model_of`),
`2915250d` (two inline disposal sites → local `_close_unawaited`, proven
equivalent), `849f67bc` (`@override` markers, runtime no-ops), `dc0ae008`
(BEHAVIOR-BEARING: the non-string `USERNAME_FIELD` refusal arm + annotated
registry bindings + `_safe_arg_repr` import; 27-line production hunk +
26-line oracle).

### Attribution (run-8)

By diff content vs `git show HEAD:<path>` (worktree `120+/187-`,
`d3853af47d03d399dced4becc14be8999b42f539`, 1468 lines):

- Owned (ledger Run-7 Family `awaitable-refusal-and-disposal`, e1): the
  `_disposed_awaitable` import, the `if _disposed_awaitable(...)` call, and
  the disposal docstring clause inside
  `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`.
  ABSENT at HEAD bytes (HEAD carries the `2915250d` local `_close_unawaited`
  shape); present in the worktree and in the `9aaaad5d` snapshot
  (`31c4e643eb44e4c5d4457c751b9c65f6b8edeaa5`, 1345 lines, read-only
  evidence, never applied). Recorded, not judged.
- Concurrent-external (every other worktree-vs-HEAD hunk, never judged):
  the containment removal (HEAD's four contained reads → bare reads + a
  "propagates" docstring), the holder-metaclass rewrite
  (`_SealedAuthHolderMeta` → `DjangoMutationMetaclass` + `truth.*`, 15
  `truth.` sites vs the snapshot's 11), the compensation
  `except BaseException` → `except Exception` narrowing, the wire-name-map
  threading through `_register_write_step`, and docstring rewordings. The
  worktree's `_authenticated_actor_or_none` fuses owned disposal lines with
  the concurrent bare-reads rewrite on the same lines; the re-trace judges
  HEAD bytes only.

### Enumeration (run-8)

Instrument: `ast.parse` over `git show HEAD:<path>`, counting
`ast.Module.body` members — **78 top-level statements** (1 docstring + 24
imports + 8 constants + 5 ledger assigns + 1 clear-registration `Expr` + 2
classes + 2 `TYPE_CHECKING` `If`s + 2 alias binds + 33 functions). The audit
counts **40 rule-bearing definitions** (2 classes + 5 methods + 33
functions). Delta vs prior 72/39: +1 import statement
(`typing_extensions.override`), +2 `TYPE_CHECKING` blocks (checker-only),
+2 alias binds (`_AuthDeclaration`, `_AuthDeclarationT`, annotation-only),
+1 function (`_close_unawaited` → F1). Function order is identical to prior
with `_close_unawaited` inserted between `_make_auth_field` and
`_authenticated_actor_or_none`. (Record note: prior prose said "21
imports"; the instrument reads 23 at the prior blob and 24 at HEAD — the
72/78 totals are exact either way.)

| # | Member | Home |
|---|---|---|
| 1–8 | the 8 constants (byte-identical set) | F7/F8/F9 as prior |
| 9 | ledger group (registry + 3 annotated aliases + store + `register_subsystem_clear` row; annotations are runtime no-ops) | F4 + F10 |
| 10 | `if TYPE_CHECKING:` imports block (incl. `_RegisterDecoded`, `_OkPayload`, `_OkPayloadClass`, `_AuthLedgerEntry`) | type-only projection, no rule (checker view of F18/F14/F19 shapes; changes follow the runtime owners) |
| 11 | `_AuthMutationMetaSnapshot` + `__init__`/`__setattr__`/`__delattr__` (`@override` markers only) | F6 slot sub-rule |
| 12 | `if TYPE_CHECKING:` `_AuthHolderAttributes` + `else: _AuthHolderAttributes = type` (runtime base still `type`) | type-only projection, no rule (checker view of the F10 holder shape) |
| 13 | `_SealedAuthHolderMeta` + `__setattr__`/`__delattr__` (`@override` markers only) | F6 head sub-rule |
| 14 | `_AuthDeclaration`, `_AuthDeclarationT` (annotation-only; `from __future__ import annotations` keeps them unevaluated) | type-only projection, no rule (names for the F10 declaration rule) |
| 15–47 | the 33 functions in file order (`_make_permission_holder` … `bind_auth_mutations`, incl. new `_close_unawaited`) | `_close_unawaited` → F1 family row; all others keep their prior homes (rows 12–43 above) |

Every member lands; every challenge below ends in a family row, a
file-local row, a type-only projection, or a rejection.

### Matrix (run-8, HEAD bytes)

**1. Cross-flavor policy mirroring.** CONFIRM. The register rider is still
a fourth step pair, not a fourth kit: `_run_register_pipeline_sync`
delegates unchanged (skeleton casts/rename-only, verified hunk by hunk;
`coerce_lookup_id`'s `ed004ebd` change is update/delete-only and the rider
is create-only), `_register_decode_step` rides `_model_decode_step` (body
SAME), `_register_write_step` delegates its tail to `_model_write_step`
(body SAME). Siblings still ride by call at HEAD
(`forms/resolvers.py` + `rest_framework/resolvers.py` name
`run_write_pipeline_sync`). Fixed fields still reuse gate/ctors/builders
by call (`authorize_or_raise`, `payload_cls_for` cast-only, `build_payload`,
`field_error` — now imported direct from the same
`django_strawberry_framework/utils/errors.py` object). C6 re-verified: 0
`recourse` strings minted in the target. C7 re-verified: 0 `model_for`
calls; the rider reads via identity `backing_model_of` (the owned source).

**2. Sync/async twins.** CONFIRM. Four native pairs + the bridge seam, all
present at HEAD bytes with the principle-5 contrast in both docstrings
(verified by full read): login establish, login bodies, logout teardown,
logout bodies. The bridge is still a real `async def` (`_async_body`
awaiting the one boundary). `_close_unawaited` needs no twin: both call
sites are sync. Dispatch-spy oracles all present (4/4 names).

**3. Derived knowledge.** CONFIRM. Every shared derivation still consumed
by call; two composition renames are proven identity (same-object
`field_error`, identity `backing_model_of`). The `AuthMutation` literal is
still single-sited (1 hit package-wide); all four `family_label=`
consumers pass the constant by reference. The login/register storability
mapping difference stands (envelope vs field-keyed, same primitive).

**4. Inverse / round-trip pairs.** CONFIRM. The `EXCLUDED`-password
producer/consumer is unchanged (`mutation_input_field_specs` SAME);
`Register`→`RegisterPayload` still derives, `RegisterInput` still pinned
(read at HEAD).

**5. Contracts in another medium.** CONFIRM. Production + [spec-040][spec-040]
(frozen: zero commits since the prior stamp) + oracles (test-name sets:
`test_mutations` 81→83 with +2/−0; `test_queries` −1 strictness row
(re-homed live); live auth +2 `_over_http` strictness rows (one re-homed,
one additional) with all other names unchanged; `test_sessions` +1; the
enumeration-guard literal byte-identical
with zero constant reads in tests/examples) + projections
(module-docstring first line reworded, consumer schema docstring-only) +
consumer (all four factories called).

**6. Enforcement by omission.** CONFIRM. The three deliberate omissions
stand (D-N3 `Meta` comment read; D-N2 direct `password` keying read;
logout-only bind exemption read). Four-surface guard sweep re-run at HEAD:
permission gate on all four incl. `current_user` (exact-string denial
oracles present), capability check on login/logout, `require_session` on
both. Two new boundaries ruled NOT omissions (no contract row; `dc0ae008`
is type-only and Django requires both fields): a missing `USERNAME_FIELD`
attribute raises `AttributeError` from the `getattr`, and a non-iterable
`REQUIRED_FIELDS` raises `TypeError` at the unpack — see Defects (run-8).

### Challenges (run-8, HEAD bytes)

Counts are authoritative definitions only; consumers, oracles, projections
are listed in the findings.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 disposal protocol | route refused awaitables through a new protocol | **2 sites / 2 owners** (`_close_unawaited` + `utils/querysets.py::_dispose_sync_awaitable`); within-file **1** (was 2) | REVISE counts, family row stands open |
| C2 | F2 boundary shape | change the worker | **1** (owner; 6 calls — bridge 1, login-async 2, logout-async 2, rider 1 — follow by call; record corrects prior "5") | REVISE census, consumer stands |
| C3 | F3 lease order | change lease/order | **1** | CONFIRM |
| C4 | F4 clear phases | add a phase | **1** | CONFIRM |
| C5 | F5 primary split | change the split | **2** mechanism / 1 per wording | CONFIRM |
| C6/C7 | recourse/seed | — | **0 here** (0 grep hits each) | CONFIRM no surface |
| C8 | F6 seal behavior | change the seal | **4 sites / 2 shapes** | CONFIRM new family stands |
| C9–C12 | F7/F8/F9 label/wordings/tables | rename/reword | **1** each | CONFIRM |
| C13 | F10 conflict key | admit a presentation kwarg | **1** | CONFIRM |
| C14 | F11 dispatch seam | new executor mode | **1** (+ nested rejection stands) | CONFIRM |
| C15 | F12 anonymity | admit a 6th hostile shape | **1** | CONFIRM |
| C16/C17 | F14/F13 envelopes/prologues | change shape/order | **1** per ctor/prologue | CONFIRM |
| C18 | F15 compensation | change compensation | **2** per transport pair (principle-5 twins) | CONFIRM |
| C19/C20 | F18 steps / F19 bind | change hashing / slot | **1** per step; slot finalizer-owned | CONFIRM |
| C21/C22 | F18 D-N2/D-N3 | share mapper / add helper | **0 saved** / **0 existing** | CONFIRM rejection + omission |
| C23 | F18 new arm: non-string `USERNAME_FIELD` refusal | reword the refusal / widen the check | **1** (`derive_register_fields`; the render composes `_safe_arg_repr` by name) | NEW — file-local sub-row `register-username-field-type-refusal` nested under F18 |

### Per-finding verdicts (run-8, HEAD bytes)

- F1 `awaitable-refusal-and-disposal` — **REVISE** (counts only). The two
  inline copies are now one local `_close_unawaited` + 2 `isawaitable`
  detects (equivalence proven: a non-callable `close` skipped ≡ the old
  suppressed `TypeError`; read/call failures suppressed ≡ old; a coroutine
  still closed). Owner bodies SAME. New delta for the family (same class as
  the Future delta, consolidation input, not a defect): a non-coroutine
  non-future awaitable WITH a callable `close` is closed by the local
  helper but ignored by the owner; outcome (anonymous, no warning) is
  identical either way and no contract row pins the treatment. Gate tests
  pin coroutine-closed + anonymous independently. Family row stays open.
- F2 `one-sync-boundary` — **REVISE** (census only: 6 calls, not 5 —
  bridge 1, login-async 2, logout-async 2, rider 1 — identical at both
  blobs; prior "5" was a miscount). Consumer-only stands; C2 count 1.
- F3 `ws-connection-actor-state` — **CONFIRM**. Lease bodies SAME, order
  prose byte-identical, holding site + negative sites verified by read.
- F4 `subsystem-clear-lifecycle` — **CONFIRM**. Bus SAME; row still
  full-clear-only (no `before_bind` on the call); finalizer pre-bind reset
  + phase-2.5 slot read intact.
- F5 `type-registry-model-type-map` — **CONFIRM**. `_resolve_primary_type`
  SAME; auth arm annotation-only; Decision-8 wording + finalizer-owned
  ordering unchanged. Candidate member stands.
- F6 `sealed-authorization-source` — **CONFIRM**. Seal bodies
  annotation/cast/`@override`-only; carrier differences unchanged;
  cross-mentions one-directional (0 `auth/` cites in `sets.py`; 22/22
  `auth` occurrences stable). New family + two sub-rules stand.
- F7–F17, F19 — **CONFIRM** (evidence per row in Matrix/Challenges:
  constants byte-identical; conflict key read; seam + bridge read;
  containment byte-identical — the old→HEAD diff of
  `_authenticated_actor_or_none` minus comments is exactly the two disposal
  call swaps + one identity `cast`; gate data username-only/`None` read;
  compensation blocks read; factories + consumer read; bind + slot read).
- F18 register rule — **REVISE** (contract extension only). Everything
  prior stands (steps/skeleton SAME-or-identity; D-N2 rejection stands
  against the SAME mapper; D-N3 omission stands on the same `Meta`
  comment); the contract gains the `dc0ae008` first refusal arm, examined
  as C23 below. Model reads now via identity `backing_model_of` (landed
  `b20277fe`); counts unchanged.
- No-surface families (`sync-boundary-recourse-wording`,
  `queryset-seed-and-model-read`) — **CONFIRM** (0 hits each; do not
  inherit).
- Nested rejections (F11 dispatch seam, F18 D-N2) + D-N3 omission note —
  **CONFIRM** (contract differences re-verified against SAME bodies;
  triggers + durable homes unchanged).

Prior P1 (13 checks) transfers to HEAD bytes: containment byte-identical,
disposal proven equivalent, both deltas recorded. Prior P2 (7 checks)
transfers: ledger mechanics SAME, registry-alias annotations runtime
no-ops. Re-trace proofs are `static-reviewed`; no execution was run (a
shared-tree run would execute concurrent-external bytes, and the workspace
copy mirrors the same dirt — neither can evidence HEAD).

### The new refusal arm (C23; family decision)

`derive_register_fields` first reads `USERNAME_FIELD` as `object` and
refuses a non-string with a `ConfigurationError` naming model + rendered
value, before any name is validated. Single-sited: the only
`USERNAME_FIELD` value read package-wide (11 hits, 1 value read + prose);
single production caller (`_synthesize_register_rider`); the render
composes `django_strawberry_framework/exceptions.py::_safe_arg_repr` by
name (shared, never-raising renderer). Independent oracle
`test_derive_register_fields_rejects_a_non_string_username_field` pins the
literal (`...USERNAME_FIELD to be a field name string; got 7.`) at the
package tier, with the tier justified in its docstring (no fakeshop model
can declare the shape). Owning family: neither `mutation-error-envelope`
(resolve-time `FieldError` leaves vs this declaration-time
`ConfigurationError` — different contracts) nor
`already-registered-error-wording` (no registration collision involved).
It extends the SAME file-local register-derivation rule (F18), beside the
sibling protected-fields refusal: named sub-row
`register-username-field-type-refusal` for Worker-0 to fold into the F18
row (no new family; no plan edit here). Boundary (not defects): a MISSING
`USERNAME_FIELD` raises `AttributeError`, a non-iterable `REQUIRED_FIELDS`
raises `TypeError` — both are Django-broken models outside the type-only
contract, with no contract row demanding a refusal.

### e1 owned-region status (run-8)

The ledger's e1 composition (`_disposed_awaitable` import + call +
docstring) is ABSENT at HEAD bytes — HEAD carries the pre-consolidation
local `_close_unawaited` shape — and present in the worktree + the
`9aaaad5d` snapshot (fused there with the concurrent bare-reads rewrite).
Fingerprints: HEAD `72595bb1…`, worktree `d3853af4…`, snapshot
`31c4e643…` (full ids in Freshness). The F1 family row stays open on HEAD
bytes; e1's merge is the family's business, not this file item's.

### Defects (run-8)

None meeting the bar. The two prior observations stay non-defects (the
Future delta persists at HEAD as consolidation input; the preflight
allocation nit keeps the same shape). The two new boundaries above
(missing attribute, `REQUIRED_FIELDS` shape) were driven to a verdict and
are NOT defects: no contract row, Django-broken inputs, `dc0ae008`
type-only.

### Pending execution (run-8)

None. No `execution-deferred` proof exists; no workspace or shared-tree
test run was performed or is owed (the one behavior-bearing drift ships
its own oracle; all other drift is proven identity statically). The final
suite gate belongs to the plan's gate item.

### Judgment (run-8)

Zero-edit file re-trace at HEAD bytes. 78 top-level statements / 40
rule-bearing definitions enumerated, all homed (one new member → F1; four
type-only members → projections). Verdicts: 16 finding-CONFIRMs (F3–F17,
F19) + 2 no-surface + 3 nested CONFIRMs, 3 REVISEs (F1 counts, F2 census,
F18 contract extension + named sub-row), 0 new families, 0 defects, 0
pending execution. e1's owned composition is recorded absent at HEAD
(present worktree + snapshot only).

### Freshness (run-8)

`MATCH` = byte-identical to the prior stamp; `STALE` = changed at HEAD
(re-verified above); dispositions say what the change means for the citing
finding. All hashes are `git rev-parse HEAD:<path>` full blob ids.

| Input | Prior | HEAD now | State | Disposition |
|---|---|---|---|---|
| target `auth/mutations.py` | `dbe64995…` | `72595bb188afd8dcc321638d97393fbd396a51b5` | STALE (6 commits) | retraced (this section) |
| worktree target (uncommitted) | — | `d3853af47d03d399dced4becc14be8999b42f539` | — | attributed only (e1 + concurrent) |
| `9aaaad5d` snapshot bytes | — | `31c4e643eb44e4c5d4457c751b9c65f6b8edeaa5` | — | read-only evidence (e1 present, guard absent) |
| drift-base `0c0537e2` bytes | — | `d1a59c44e1476ba13d07bb38c6af194dcf80634f` | — | reference (prior + doc line) |
| `utils/querysets.py` | `1539b66c…` | `392e50d085c5b5a15c850a9a69b0f1b50e8529a4` | STALE | owner bodies SAME (F1/F2 stand) |
| `mutations/sets.py` | `cffa29e5…` | `f8c645006f028aeddc031970e6b07163725b798a` | STALE | consumed bodies SAME/cast-only (F4/F5/F6/F10 stand) |
| `mutations/resolvers.py` | `3fd1e571…` | `7a25afeaed1d74bd91a142197fea712bac46993b` | STALE | skeleton cast/rename-only; `ed004ebd` off the rider path (F13/F14/F18 stand) |
| `mutations/inputs.py` | `fc442047…` | `fd463fff72862429cdb122eb3a50cdc635352f5e` | STALE | consumed bodies SAME/cast-only (F9/F18/F19 stand) |
| `auth/queries.py` | `5c59ba75…` | `837ce75fe1da1c299a974a3fc2e32534309d4e5f` | STALE | 4 consumers by call intact (F10/F11/F12/F19 stand) |
| `auth/sessions.py` | `fad7feb8…` | `2fa0f1690b84a0ea91223ea7f08efba8b052ac9f` | STALE | bodies SAME/cast-only (F13/F15/F16 stand) |
| `utils/sessions.py` | `f0d9297c…` | `e4008fa7cdccbcf302ba1338021f6768a88b9665` | STALE | lease SAME, order prose byte-identical (F3 stands) |
| `registry.py` | `9cc8bb55…` | `9d2021ebd34dd57e9dbb245be3c44af25685325f` | STALE | bus SAME; sentinel change off-bus (F4 stands) |
| `types/finalizer.py` | `77fd9a2d…` | `cb2dde6b296d4a481a9b8bbab7bdaec86e1d0ce7` | STALE | slot/order/guard read intact (F4/F5/F19 stand) |
| `consumers.py` | `18f3ea16…` | `5436cf355de38c54a109763de67f7d7265c8245f` | STALE | revocation prose identical (F3/F15 stand) |
| `utils/permissions.py` | `9889d6fe…` | `e2b46fd7d9712de1293c867708b1299f0e85e521` | STALE | `request_from_info` SAME (F7/F13 stand) |
| `utils/write_values.py` | `d28587c7…` | `01a3318cf6ba21e57516897a9d29e27c4f7aa853` | STALE | preflight SAME (F13/F18 stand) |
| `utils/errors.py` | `3e25e93b…` | `793855e0cf653cc7171281ca8ebb437050a43054` | STALE | `field_error` + mapper SAME (F14/D-N2 stand) |
| `mutations/fields.py` | `cf518361…` | `8d3ce7e20eef050ca544f295da51e7847deff23c` | STALE | lazy machinery SAME (F11 stands) |
| `utils/directives.py` | `380786cf…` | `0368ff5190627a220ff0f3c37462a667405ba1b6` | STALE | validator SAME (F11 stands) |
| `utils/execution_mode.py` | `9805cdaf…` | `b86a08cdce3d7111c3be26b717c798e196ad73f9` | STALE | dispatch SAME (F11 stands) |
| `tests/auth/test_mutations.py` | `63904929…` | `59d13bdae97568f7517dbcbdf561bcfbeb46508f` | STALE | 81→83 (+2/−0); guard literal identical (gates stand) |
| `tests/auth/conftest.py` | `74c62311…` | `74c62311315801dd946e3e017d587ded828a6f5e` | MATCH | — |
| `accounts/schema.py` | `c0fdc23b…` | `dd2e81b3474e7d0ce8c42eb573642addc579af1b` | STALE | docstring line only (F17 stands) |
| `exceptions.py` (new input) | — | `f27e1f91d4021a6a1f8310f9a20d59b1e03f83a8` | — | `_safe_arg_repr` never-raising owner (C23) |
| `tests/auth/test_queries.py` | — | `211599d2527debdb83ace344c37879452fde2e6d` | — | awaitable-closed gates present (F1/F12) |
| `test_query/test_auth_api.py` | — | (names diffed, +2 strictness rows) | — | live names otherwise unchanged (F12/F14/F16) |
| [spec-040][spec-040] | — | (0 commits since prior) | MATCH | contract source frozen |

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[consumers]: ../../django_strawberry_framework/consumers.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-perms]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-directives]: ../../django_strawberry_framework/utils/directives.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-execution]: ../../django_strawberry_framework/utils/execution_mode.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[auth-conftest]: ../../tests/auth/conftest.py
[auth-helpers]: ../../tests/auth/_helpers.py
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-auth-queries]: ../../tests/auth/test_queries.py
[test-auth-sessions]: ../../tests/auth/test_sessions.py

<!-- examples/ -->
[accounts-schema]: ../../examples/fakeshop/apps/accounts/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
All other claims are `static-reviewed` (import moves, bodies composed by name,
single spanning reads).

## Independent verification (Worker-2) — run-8 re-trace

Basis: detached HEAD `83998e08`; target HEAD blob
`72595bb188afd8dcc321638d97393fbd396a51b5` (1535 lines), worktree blob
`d3853af47d03d399dced4becc14be8999b42f539` (1468 lines),
`9aaaad5d` snapshot blob `31c4e643eb44e4c5d4457c751b9c65f6b8edeaa5`
(1345 lines), drift-base `0c0537e2` blob
`d1a59c44e1476ba13d07bb38c6af194dcf80634f` — all four re-hashed by
W2, all match. `ITEM_BASELINE=b65886084f7b8474b0cf29c9728057ba35df8c39`:
item-scoped diff 0 bytes (re-run by W2). Zero-edit holds.

### Independent trace (W2 instruments, HEAD bytes)

Enumeration: `ast.parse` over `git show HEAD:<path>`, counting
`ast.Module.body` — **78 statements** (1 docstring `Expr` + 20
`ImportFrom` + 4 `Import` + 11 `Assign` + 4 `AnnAssign` + 1
clear-registration `Expr` + 2 `ClassDef` + 2 `TYPE_CHECKING` `If` + 29
`FunctionDef` + 4 `AsyncFunctionDef`), **40 rule-bearing definitions**
(2 classes + 5 methods + 33 functions). Member-by-member against the
run-8 table: the 8 constants byte-identical in value; ledger group +
3 annotated aliases; 2 `TYPE_CHECKING` projections; 2 seal classes;
2 alias binds (`_AuthDeclaration` used in annotations only, lines
353/369/399/400/422, under `from __future__ import annotations`);
33 functions in identical order to the prior record with
`_close_unawaited` inserted 8th. Base blob reads 72 / 32 by the same
instrument (imports 19+4=23 there, 20+4=24 at HEAD — the run-8
record note correcting "21 imports" is itself correct).

Drift scope: `9031cb3d..HEAD` on the target = exactly the 6 commits
named (e6a33c46 prose-only + 4 typing-only + dc0ae008), 241+/102-
(240+/101- vs `0c0537e2`, the +1/-1 being the docstring line).
W2 typing-erased proof (annotations, docstrings, `TYPE_CHECKING`
branches, `cast`, `@override` stripped; per-statement normalized
AST diff base-vs-HEAD): every delta is one of — new
`_close_unawaited`; 2 alias binds; holder base via the runtime-`type`
alias (identical); the 2 disposal call swaps; `resolvers.field_error`
→ same-object direct import (`mutations/resolvers.py` line 94 reads
it from `utils/errors.py`); 4 `.model` reads → identity
`backing_model_of` (`cast` over a plain slot read; the rider's
triple read → one hoisted read is unobservable); the dc0ae008 arm.
No other behavioral delta exists, which independently bounds every
CONFIRM below.

F1: W2 probe (`/tmp/w2_f1_probe.py`, exact HEAD sources exec'd, 20/21
green — the 1 "FAIL" is the finding itself recorded):
inline-copy → helper equivalent on all 6 shapes (coroutine closed;
future pending both ways; non-callable `close` skipped ≡ suppressed
`TypeError`; raising close suppressed both ways; descriptor-read
parity); the divergence is REAL (custom awaitable with callable
`close`: closed locally, ignored by the owner — generator-based
coroutines included since `inspect.iscoroutine` is `False` for
them); outcome identical at the site on every shape (anonymous, no
escape, and no warning — an ignored generator-based coroutine warns
nothing on GC, verified with `warnings.record`). Contract-row
absence verified three ways: spec-040 silent on disposal (0
awaitable-disposal rows); the 2 oracles pin native-coroutine
closure only (both shapes close those); owner prose explicitly
unpins the rest ("no standard cleanup protocol").

F2: 6 `run_in_one_sync_boundary` calls at HEAD (471 bridge,
867+874 login-async, 1069+1070 logout-async, 1400 rider
`resolve_async` — each attributed to its enclosing def by AST),
identical 6 at base. The prior "5" was a miscount. No direct
`sync_to_async` code call; only the 2 permitted `async_to_sync`
bridges (841, 1049) plus prose.

C23: dc0ae008 hunk read (27 production + 26 oracle lines):
`USERNAME_FIELD` 11 hits / exactly 1 value read (line 1160);
single production caller (rider line 1315); `_safe_arg_repr`
shared (6 use sites) and never-raising (`except BaseException`);
oracle pins the literal via `match=` with the package-tier reason
in its docstring. Family-membership rejections checked against the
0_0_15 record: `mutation-error-envelope` owns resolve-time
`FieldError` leaves (consolidated), `already-registered-error-wording`
owns the registry-collision wording — a declaration-time
`ConfigurationError` with no collision belongs to neither; count 1
each way.

e1: absent at HEAD (0 `_disposed_awaitable` hits); present
worktree + snapshot with the 3 owned lines byte-identical
(import / docstring clause / call — each `diff`-clean). Adjacent
signature narrowing + `cast` + relocated comment are the recorded
typing-only / concurrent-adjacent deltas, not owned bytes.

Attribution: worktree-vs-HEAD = 38 hunks, 120+/187- as dispatched.
Owned content sits in exactly 2 hunks (import line + function
fusion); the other 36 carry no owned token (`truth.` 15 worktree /
11 snapshot, both counts match). No concurrent hunk alters an owned
byte.

Spot evidence re-derived: `"AuthMutation"` literal 1 occurrence
package-wide; `family_label=` 4/4 pass the constant; `recourse` 0,
`model_for` 0; dispatch spies 4/4 + bridge test present;
test_mutations 81→83 +2/-0 vs the prior stamp (W2's first 82→83
used the drift base instead — resolved in W1's favor);
enumeration-guard literal byte-identical with 0 constant reads in
tests/examples; consumer calls all four factories; all 21
Freshness blobs re-hashed byte-identical; spec-040 0 commits;
rider `operation = "create"` with ed004ebd confined to
`coerce_lookup_id`; D-N3 comment, D-N2 direct keying + durable
home, F4 flagless call, F5 `bind_auth()`-before-`bind_mutations()`
order, lease OUTER/INNER prose at both ends, 22 `auth` hits / 0
module cites in sets.py — all read at HEAD bytes.

### Per-row judgments

- C1/F1 REVISE (counts-only + consolidation-input delta): CONFIRM.
  2 sites / 2 owners, within-file 1; equivalence proven; the
  divergence real, outcome-identical, unpinned — consolidation
  input, not a defect. Record correction R1 (below) on the status
  phrase only.
- C2/F2 REVISE (census 6-not-5): CONFIRM. Count 1; consumer-only
  stands.
- C3–C5, C8–C22 / F3–F17, F19 (16 finding-CONFIRMs): CONFIRM, each
  bounded by the typing-erased proof plus the reads above.
- C6/C7 no-surface: CONFIRM (0/0).
- Nested F11 / D-N2 / D-N3: CONFIRM (differences re-verified,
  triggers + durable homes present).
- C23/F18 REVISE (contract extension): CONFIRM the revise;
  ENDORSE the `register-username-field-type-refusal` sub-row
  nested under F18 (single site, same function/owner/phase as the
  sibling protected-fields refusal; no new family; W2 edits no
  record).
- e1 status: CONFIRM as recorded (absent HEAD / present worktree +
  snapshot / byte-identical owned lines).
- Defects: CONFIRM none. The two new boundaries (missing
  attribute → `AttributeError`, non-iterable `REQUIRED_FIELDS` →
  `TypeError`) are Django-broken inputs with no contract row —
  correctly non-defects under the bar.
- Pending execution: CONFIRM none (W2's probes are read-only
  `/tmp` instruments evidencing HEAD bytes, not deferred proofs).

### Adversarial focus — answers

1. F1 equivalence + divergence: proven as stated above; the
   "not a defect" classification holds (spec-040 silent, oracles
   native-coroutine-only where both shapes agree, owner prose
   explicitly unpinned; the close-then-later-await direction is
   pre-existing base behavior, and e1's direction removes rather
   than adds closure for that shape).
2. "Family row stays open" is a MISSTATEMENT of record state:
   the 0_0_15 record holds Family `awaitable-refusal-and-disposal`
   at `consolidated` (index) / verified via run-7 e1 (Families).
   R1 corrects the 3 occurrences to `consolidated`; the F1 home
   assignment is untouched. Nothing here moves e1's verified
   verdict: e1 was rendered on post-consolidation bytes; the
   HEAD-bytes deltas describe its pre-image; the oracles hold
   under the owner and the custom-shape change is unpinned and
   outcome-identical. R1 moves no verdict, index row, or
   decision — metadata precision, no resubmission (run-8 s1/s4
   precedent).
3. F2 census: 6, recounted above at both blobs with enclosing
   defs. Prior "5" a miscount. Confirmed.
4. F18 sub-row: ENDORSED as judged above.
5. e1 fingerprints: HEAD `72595bb1…`, worktree `d3853af4…`,
   snapshot `31c4e643…` (full ids under Basis) — all match.

### Judgment

Zero-edit re-trace verified at HEAD bytes. Every W1 verdict
survives on W2's independent evidence: enumeration 78/40 exact,
16 finding-CONFIRMs + 2 no-surface + 3 nested CONFIRMs stand, 3
REVISEs confirmed (F1 counts + recorded delta, F2 census, F18
extension with endorsed sub-row), 0 defects, 0 pending execution,
item-scoped diff empty, owned lines byte-identical, all other
hunks concurrent-external. One record correction (R1, family-row
status wording) with no verdict/index/decision move.

Verdict: `Status: verified`.
