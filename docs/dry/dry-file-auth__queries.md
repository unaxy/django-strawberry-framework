# DRY review: `django_strawberry_framework/auth/queries.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in a family row (reused indexed name), a file-local row with its
proving challenge, or a rejection carrying contract difference + trigger +
durable home. Zero production edits; zero tracked files changed.

## System trace

FRESH target (121 lines): the read-side member of the opt-in session-auth
surface — the `current_user()` query-field factory plus its
bind-materialized `CurrentUserAlias` return-alias namespace, over spec-040
Decision 7 (nullable session actor, no queryset work) and the D12/D13 reuse
directives. The module defines almost nothing: declaration rides
[auth/mutations.py][auth-mutations]`::_declare_fixed_auth_surface`,
field construction rides `_make_auth_field`, the async path rides
`_sync_bridged_async_body`, anonymity rides `_authenticated_actor_or_none`,
request resolution rides
[utils/permissions.py][utils-permissions]`::request_from_info`, the gate rides
[mutations/resolvers.py][mutations-resolvers]`::authorize_or_raise`, the lazy
return ref rides [mutations/fields.py][mutations-fields]`::_lazy_ref`, the
alias namespace rides
[utils/inputs.py][utils-inputs]`::make_input_namespace`, and teardown rides
the [registry.py][registry] bus. The genuinely local rules are the resolve
contract (classify -> gate-first with `instance=actor` -> return actor), the
factory wiring (fourth surface through the shared fixed path, nullable alias
ref, no envelope), and the alias-identity constants. `bind_auth_mutations`
(in [auth/mutations.py][auth-mutations]) is the namespace's materialize
consumer; [types/finalizer.py][finalizer] owns the phase-2.5 slot that makes
the materialize reachable.

Connected code read for judgment, outside the item:
[auth/mutations.py][auth-mutations] (sibling artifact
`dry-file-auth__mutations.md` used as rejected-candidate triggers only —
compared by behavior/contract throughout, nothing inherited on authority;
full declaration path, bridge seam, anonymity definition, and `bind_auth_mutations`
re-read off the working tree), [auth/__init__.py][auth-init],
[auth/sessions.py][auth-sessions] (transport prologue ownership — confirms
`me` deliberately has none), [utils/inputs.py][utils-inputs]`::make_input_namespace`
(trio shape + parked-global lifecycle paragraph),
[mutations/fields.py][mutations-fields]`::_lazy_ref` +
`::build_lazy_field_signature`, [utils/permissions.py][utils-permissions]`::request_from_info`,
[mutations/resolvers.py][mutations-resolvers]`::authorize_or_raise`,
[registry.py][registry]`::register_subsystem_clear`, the phase-2.5 window in
[finalizer.py][finalizer], oracles
[test-auth-queries][test-auth-queries] (619 lines) +
[test-auth-mutations][test-auth-mutations], consumer
[accounts-schema][accounts-schema], contract source [spec-040][spec-040]
(Decision 7, Decisions 9/10, D1/D4/D12/D13/D15/D17, D-N1).

Excluded with reason: the concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, sibling
`dry-file-*.md` artifacts incl. the mutations artifact's probe pair) was left
untouched; none is in this item's paths. Every other indexed family whose
files-covered list touches `auth/` was judged on its mechanism against this
target's REAL surface (Matrix + Challenges C7–C13); `connection.py`-owned
families were not re-derived beyond the attribution check.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The read/mutation envelope split is the
file's central deliberate non-mirror: mutations resolve to the frozen
`{node/errors}` / `{ok/errors}` envelope, `me` returns the user type directly
(`null` for anonymous) with no `ok`/`errors` slot — Decision 7 pins the
nullable-by-contract read posture, so unifying onto the envelope (J5) is a
rejected consolidation, not a mirror to build. The shared machinery IS shared
by call, never re-spelled: declaration-cache-conflict path
(`_declare_fixed_auth_surface`), field dispatch seam (`_make_auth_field`,
incl. the interim `_sync_bridged_async_body`), anonymity definition
(`_authenticated_actor_or_none`), gate (`authorize_or_raise`), lazy ref
(`_lazy_ref`), request label (the `_AUTH_FAMILY_LABEL` constant imported from
[auth/mutations.py][auth-mutations]). Compared against the sibling artifact's
F10/F11/F12/F13/F14/F16/F18 row by row by behavior: queries consumes F10, F11
(dispatch + bridge), F12, and the F2 boundary through the bridge; it has no
counterpart to F13 prologues (no transport capability to enforce — spec edge
table: "`register` / `me` are unaffected — the actor is simply anonymous"),
F14 envelopes (no envelope by contract), F15 critical sections (no session
mutation), or F18 rider steps (no model write) — each absence carries a
Decision-7/edge-table contract source, so none is an enforcement gap.
Considered family `one-sync-boundary`: reused as consumer (F2).

**2. Sync/async twins.** One sync body only
(`_current_user_resolve_body`); the async path is the shared interim bridge
(`_sync_bridged_async_body(sync_body)` — a real coroutine fn through the one
shared worker), NOT a native per-transport async body like login/logout carry.
There is no twin to drift: a contract change to the resolve behavior moves the
single sync body; the bridge moves only for a dispatch-shape change (owned at
F11 in [auth/mutations.py][auth-mutations]). The Decision-10 count invariant
(one resolution enters the thread-sensitive boundary exactly once) holds via
the bridge and is pinned by the dispatch-spy oracles. Giving `me` a native
async body (J2) is rejected: reads perform no per-transport awaits.

**3. Derived rather than repeated knowledge.** Every shared derivation is
consumed by call or by imported constant, never re-spelled: the alias name
(`CURRENT_USER_ALIAS_NAME`, one literal, consumed here twice and imported by
the bind), the module path (`AUTH_QUERIES_MODULE_PATH`, one literal,
consumed by the trio call and the lazy-ref call), request resolution,
permission normalization, gate, lazy ref, boundary worker. The one
queries-local derivation is the `| None` nullable wrap on the return ref —
the me-only contract (non-null payload refs elsewhere are unaffected), not a
second spelling of an existing rule.

**4. Inverse / round-trip pairs.** The materialize/clear pair for the alias
namespace is trio-owned ([utils/inputs.py][utils-inputs]`::make_input_namespace`):
`bind_auth_mutations` calls the materialize arm, this module's pre-bind bus
row calls the clear arm, parked globals stay parked (no `setattr`/`delattr`
in code — verified by grep; the words appear only in the docstring's reuse
pointer). No second lifecycle, no hand-rolled pair.

**5. Contracts restated in another medium.** Production (this file) +
authoritative contract ([spec-040][spec-040] Decision 7 + D1/D4/D12/D13/D15/D17
+ D-N1 + edge table) + independent oracles
([test-auth-queries][test-auth-queries], live `me` rows in the fakeshop auth
API suite) + projections (module + factory + resolve-body docstrings,
consumer [accounts-schema][accounts-schema]). Oracles never read the owner:
the alias-identity test asserts `auth_queries.CurrentUserAlias is user_type`
(behavior, not the constant); the gated-`me` test pins the exact denial
string; the dispatch spies pin boundary counts; the SDL/live tests pin
`me: UserType` and the anonymous-`null` / visibility-skip behavior. Counts
below count definitions only; oracles/projections are listed per finding.

**6. Enforcement by omission.** Sweep over both members: the resolve body runs
the permission gate on its only path (gate-first, before the nullable
return); the factory routes `permission_classes` through the shared
fixed-surface declaration (conflict key excludes presentation kwargs — owned
at the sibling's F10). Deliberate omissions, each with a contract source: no
transport prologue (spec edge table — missing session leaves `me` anonymous,
never an error; J4), no `get_queryset` re-run and no re-fetch (D-N1,
actor-not-lookup), no envelope (Decision 7), no `require_session`. No member
lacks a guard its contract requires — no defect.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **15 top-level statements** (1 docstring + 8 imports + 2 constants
+ 1 trio unpack + 1 clear registration + 2 functions). The audit counts **6
rule-bearing definitions** (2 functions + 2 constants + 1 trio + 1 bus row).
Every member lands below; every challenge in `### Challenges` ends in a
family row, a file-local row, or a rejection.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring | projection (Decision 7 + D13 + D-N1 pointers; owned at spec + bodies) |
| 1–8 | 8 imports (`__future__`, `functools`, `typing.Any`, `_lazy_ref`, `register_subsystem_clear`, `make_input_namespace`, `request_from_info`, `.mutations` 5-name block) | consumers by import (no rule) |
| 9 | `AUTH_QUERIES_MODULE_PATH` | R3 |
| 10 | `CURRENT_USER_ALIAS_NAME` | R3 |
| 11 | Trio unpack (`_current_user_alias_names`, `materialize_current_user_alias`, `clear_current_user_alias_namespace`) | R3 (ledger home) + F1 (clear arm) |
| 12 | `register_subsystem_clear(...)` call | F1 |
| 13 | `_current_user_resolve_body` | R1 |
| 14 | `current_user` | R2 |

Three indexed families reused (F1–F3); seven indexed families checked with no
surface and not inherited (C7–C13); three file-local rows (R1–R3); five
rejections with difference + trigger + home (J1–J5).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R3 alias spelling | rename `CurrentUserAlias` | **1** (the constant; bind imports it; SDL oracle lists the resolved shape) | file-local |
| C2 | R3 module path | move the queries module | **1** (the constant; trio + lazy ref share it) | file-local |
| C3 | Trio mechanics | change ledger/materialize/clear shape | **1** (`make_input_namespace` owner; this module only wires) | consumer — do not inherit |
| C4 | F1 clear phase | add a clear phase / change bus semantics | **1** (registry bus; this row declares `before_bind=True` per D15) | consumer — verified, not inherited |
| C5 | R1 gate payload/order | change gate args or gate-vs-null order | **1** (resolve body; spec pins `data=None`, `instance=actor`, gate-first) | file-local |
| C6 | R2 nullable shape | envelope-ize `me` / change nullability | **1** (factory call site; payload refs elsewhere unaffected) | file-local (+ J5 rejection) |
| C7 | Anonymity classification | admit a 6th hostile shape | **0 here** (owned by `_authenticated_actor_or_none`; this body + logout follow by call) | no surface — do not inherit |
| C8 | Declaration key/conflict | admit a kwarg into the conflict key | **0 here** (sibling F10 owns the key; fourth surface rides it) | no surface — do not inherit |
| C9 | Dispatch seam | change sync/async dispatch | **0 here** (`_make_auth_field` owner; this factory passes bodies) | no surface — do not inherit |
| C10 | Boundary worker | change the worker (e.g. thread-sensitivity) | **0 here** (`run_in_one_sync_boundary` owner, reached via the bridge) | consumer — do not inherit |
| C11 | Request-resolution wording/label | rename family / change resolution | **0 here** (`request_from_info` owner; label owned at sibling F7) | no surface — do not inherit |
| C12 | Lazy-ref shape | change the forward-ref spelling | **0 here** (`_lazy_ref` owner) | no surface — do not inherit |
| C13 | Holder synthesis/seal | change holder shape or seal | **0 here** (sibling F6/F10 owners; only the `"CurrentUser"` name string is passed) | no surface — do not inherit |

No executable probe was created: every claim above is composition-by-call or
a single spanning read (import edges, one constant shared by two call sites,
flag read off the registration call, absence verified by grep), and every
behavioral surface is already pinned by the pre-existing oracles named as
gates. See `## Pending execution` for the full inspection-sufficiency case.
NO shared-tree pytest ran (per the dispatch).

## Findings

No production edit is owed by a file item; each finding records the rule with
the challenge that proved its home. `Migration: none` throughout (zero-edit
item) — stated once here, not per row. `Coupling: none` throughout (file item
consolidates nothing) — likewise stated once.

### F1 — `subsystem-clear-lifecycle` (family row, consumer verified)

- **Contract + variation.** Every subsystem registers teardown on the
  [registry.py][registry] bus with a stable owner + phase flag; full clears
  drain everything, pre-bind resets drain only `before_bind` rows.
- **Sites + roles.** *Definition*: [registry.py][registry]`::register_subsystem_clear`
  / `::iter_subsystem_clears` / `::_subsystem_clears`. *Row here*:
  `register_subsystem_clear(clear_current_user_alias_namespace,
  owner="auth.current_user_alias", before_bind=True)` — the PRE-BIND emit
  row (D15): the alias ledger drains before each re-materialize so a reload's
  different `UserType` class object never trips the distinct-class collision
  guard, while the auth declaration ledger row stays full-clear-only for the
  phase-2.5 re-read. *Consumer of the bus*: [finalizer.py][finalizer] pre-bind
  reset + `TypeRegistry.clear()`. *Oracles*:
  `test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row`,
  `test_current_user_only_bind_emits_no_login_logout_payloads`.
- **Challenges.** C4 → 1.
- **Owner + lifetime.** Indexed owner (bus); the flag choice is this row's
  declaration, justified by Decision 9/D15 in the module docstring. No stored
  derivation beyond the ledger (trio-owned, parked-global lifetime).
- **Behavioral proof.** `static-reviewed` (flag + owner read off the call;
  trio halves verified against
  [utils/inputs.py][utils-inputs]`::make_input_namespace` body). Rejects "the
  alias ledger survives a pre-bind reset" and "declarations drain pre-bind".
- **Structural gate.** The oracles above (pre-existing).
- **Freshness.** Target `5c59ba75023d21998efc6a8b1b714bdfab273ad7`,
  [registry.py][registry] `9cc8bb553fd417fc465809a541769a8383469cda`,
  [utils/inputs.py][utils-inputs] `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`,
  [finalizer.py][finalizer] `77fd9a2dd229eb9de5f29188c5058035d3606323`,
  [test-auth-queries][test-auth-queries] `7d7cfcedb74bfb36e233d5ad71d50326f02eab1d`.

### F2 — `one-sync-boundary` (family row, consumer)

- **Contract + variation.** Every async surface needing sync ORM work runs it
  in ONE `sync_to_async(thread_sensitive=True)` worker. No local variation.
- **Sites + roles.** *Definition*:
  [utils/querysets.py][utils-querysets]`::run_in_one_sync_boundary` (D17: no
  auth module spells `sync_to_async` itself — verified by grep: zero code
  hits in this file). *Consumer site here (indirect, by call)*: the factory's
  `async_body=_sync_bridged_async_body(sync_body)` — the bridge's worker is
  the boundary; the resolve body's lazy-user forcing runs inside it
  (Decision 10). *Oracles*: `test_sync_me_dispatch_never_enters_the_async_boundary`,
  `test_async_me_dispatch_awaits_the_native_async_body_exactly_once`,
  `test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary`.
- **Challenges.** C10 → 0 here (1 at the utils owner).
- **Owner + lifetime.** Indexed owner; no stored derivation. Checked —
  consumer only, do not inherit.
- **Index-coverage note for Worker 0 (not a finding):** the
  `one-sync-boundary` files-covered list names `auth/mutations.py` but not
  `auth/queries.py`; this file reaches the boundary through the bridge defined
  there. The family item may add `auth/queries.py` as a consumer site — no
  plan edit is owed by this file item.
- **Behavioral proof.** `static-reviewed` (bridge reached by call; oracles pin
  the count). **Structural gate.** The spy tests above (pre-existing).
- **Freshness.** Target as F1; [utils/querysets.py][utils-querysets]
  `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`;
  [auth/mutations.py][auth-mutations] `dbe64995b87240b87a1d5119f46cc42c7cab646f`.

### F3 — `auth-leaf-manifest` (indexed row, definition site)

- **Contract + variation.** The opt-in surface re-exports exactly the four
  factories; each symbol is defined once in its home module. Varies only in
  membership.
- **Sites + roles.** *Definition of this symbol*:
  [auth/queries.py][auth-queries]`::current_user`. *Manifest owner*:
  [auth/__init__.py][auth-init] (`from .queries import current_user`,
  `__all__` entry — verified). *Sole factory consumer*:
  [accounts-schema][accounts-schema] (`me = current_user()`). Manifest row
  itself stays file-local at `auth/__init__.py` per the index — no change.
- **Challenges.** A fifth surface adds one import + one `__all__` entry at the
  manifest; this symbol's definition does not move — 1 per side, never a
  shared count.
- **Owner + lifetime.** Manifest owned at [auth/__init__.py][auth-init]; no
  stored derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Any dropped
  re-export breaks the consumer schema import (live suite imports through the
  package surface).
- **Freshness.** Target as F1; [auth/__init__.py][auth-init]
  `6bc3c4a5eb965988d91fef5c87240826e5163e6c`;
  [accounts-schema][accounts-schema] `c0fdc23be03f7ea0c621492b96a1a4857ef60a74`.

### R1 — me resolve contract (file-local)

- **Contract + variation.** Classify the request actor through the ONE shared
  anonymity definition, run the permission gate FIRST with `data=None` and
  `instance=<actor>`, then apply the nullable-return rule (authenticated ->
  actor, anonymous -> `null`, never an error). Denial is a top-level
  `GraphQLError` (authorization axis); `null` is the anonymous axis. No
  `get_queryset` re-run, no re-fetch (D-N1 actor-not-lookup).
- **Sites + roles.** *Definition*:
  [auth/queries.py][auth-queries]`::_current_user_resolve_body`. *Shared by
  call*: `request_from_info` (D1 label import), `_authenticated_actor_or_none`
  (C7 owner), `authorize_or_raise` (D4). *Oracles*:
  `test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string`
  (pins `"Not authorized to current_user <UserType>."` without reading the
  machinery), `test_me_is_null_not_a_crash_when_the_request_user_is_absent`,
  the hostile-shape collapse tests, live `test_anonymous_me_is_null_not_an_error`,
  `test_me_without_authentication_middleware_is_null_not_a_crash`,
  `test_login_and_me_skip_user_type_visibility`.
- **Challenges.** C5 → 1 (gate args/order live here); C7 → 0 here (anonymity
  owned in [auth/mutations.py][auth-mutations]).
- **Owner + lifetime.** This module (read-side resolve order). No stored
  derivation.
- **Behavioral proof.** `static-reviewed` (order + args read off the body;
  no-queryset-work verified by grep — zero `get_queryset`/`model_for` code
  hits). **Structural gate.** The oracles above (pre-existing).
- **Distinct behavior.** `instance=actor` (vs login/logout `instance=None`)
  is the Decision-7 contract, not drift: the gate must see the actor so an
  `IsAuthenticated`-style class can deny the anonymous caller.
- **Freshness.** Target as F1; resolvers `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`;
  [utils/permissions.py][utils-permissions] `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`.

### R2 — factory construction (file-local)

- **Contract + variation.** Fourth surface through the shared fixed path:
  `_declare_fixed_auth_surface("current_user", "CurrentUser", ...)` (ledger +
  conflict key owned at the sibling's F10), sync body + bridged async body
  through `_make_auth_field` (F11 seam), return annotation
  `_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) | None`
  (nullable-by-contract; no envelope). Varies only in surface + presentation
  kwargs (`permission_classes`/`description`/`deprecation_reason`/`directives`
  pass through untouched).
- **Sites + roles.** *Definition*:
  [auth/queries.py][auth-queries]`::current_user`. *Shared by call*: the
  declaration path, the field seam + bridge, `_lazy_ref`. *Oracles*: the
  dispatch-spy pair, `test_hostile_directives_raise_configuration_error`
  (directives ride the shared validator), `test_conflicting_current_user_gates_raise_the_one_declaration_error`,
  live `me: UserType` SDL + round-trip tests.
- **Challenges.** C6 → 1; C8/C9/C12 → 0 here (owners elsewhere).
- **Owner + lifetime.** This module (query-surface shape). No stored
  derivation.
- **Behavioral proof.** `static-reviewed`. **Structural gate.** The oracles
  above (pre-existing).
- **Freshness.** Target as F1; [mutations/fields.py][mutations-fields]
  `cf518361d7884b8b71550cb6b73bff0c1a64549e`.

### R3 — alias-identity constants + namespace wiring (file-local)

- **Contract + variation.** The bind-materialized return-alias identity:
  `CURRENT_USER_ALIAS_NAME = "CurrentUserAlias"` pinned once and imported by
  the bind (never re-spelled there); `AUTH_QUERIES_MODULE_PATH` pinned once
  and shared by the trio call and the lazy-ref call; the trio unpack homes
  the ledger (`_current_user_alias_names`), the materialize arm (consumed by
  `bind_auth_mutations`), and the clear arm (F1's bus row) in this module.
- **Sites + roles.** *Definitions*: the two constants + the unpack.
  *Consumers by import*: the bind's `materialize_current_user_alias(...)`
  call (D13). *Oracle*: `test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row`
  + `CurrentUserAlias is user_type` identity assertion.
- **Challenges.** C1, C2 → 1 each; C3 → 0 here (trio mechanics owned in
  [utils/inputs.py][utils-inputs]).
- **Owner + lifetime.** This module (narrowest owner both consumers already
  import). Ledger lifetime = process-emit (pre-bind reset, parked globals).
- **Behavioral proof.** `static-reviewed` (unpack order verified against the
  trio's `return ledger, materialize_fn, clear_fn`; single spelling verified
  by grep — one literal each, zero re-spellings elsewhere in package source).
- **Freshness.** Target as F1; trio owner as F1.

### J1 — nullable wrap vs shared payload-ref helper (rejected)

Considered: fold the `| None` into a shared "nullable lazy ref" helper.
Contract difference: every other `_lazy_ref` consumer is a non-null envelope
ref; nullability is the me-only Decision-7 contract, and the wrap is one
operator at one call site — a helper would own a one-caller shape.
Trigger: a second nullable lazy return appears. Durable home:
[auth/queries.py][auth-queries]`::current_user` docstring (already states
nullable-by-contract).

### J2 — native async body for `me` (rejected)

Considered: mirror login/logout's native sync/async body pair. Contract
difference: reads perform no per-transport awaits (no session mutation, no
durable flush), so the interim bridge is the complete async path; the native
pairs exist for Channels `login`/`logout` awaits that have no read-side
counterpart (Decision 10). Trigger: read-side per-transport async work
appears. Durable home: the bridge docstring in
[auth/mutations.py][auth-mutations]`::_sync_bridged_async_body` + Decision 10.

### J3 — alias namespace folded into the `mutations.inputs` emit ledger (rejected)

Considered: one emit ledger for payloads + alias. Contract difference: the
payload ledger is full-clear-only emit while the alias ledger is a pre-bind
EMIT reset (D15) — different lifecycle phases on the same bus; sharing a
ledger would drain payloads pre-bind or keep a stale alias across reloads
(the distinct-class collision the row exists to prevent). Trigger: the bus
gains per-row phase granularity finer than the boolean flag. Durable home:
module docstring pre-bind paragraph + Decision 9/D15.

### J4 — transport prologue for `me` (rejected)

Considered: open the resolve body with `_transport_prologue` like login/logout.
Contract difference: the spec edge table exempts `me` — a missing session
leaves the actor anonymous (`null`), never a top-level error; capability
refusals protect session *mutation*, of which reads perform none. Adding the
prologue would turn anonymous reads into configuration errors. Trigger: a
read surface whose truthfulness needs session durability. Durable home: spec
edge-table row + the resolve-body comment naming the shared anonymity owner.

### J5 — envelope for `me` (rejected)

Considered: return `{user, errors}` like the mutation surfaces. Contract
difference: Decision 7's direct nullable return — an anonymous session is an
expected state, not an error, and there is no failing operation to key
errors to. Trigger: clients needing uniform read errors. Durable home:
[spec-040][spec-040] Decision 7.

## Defects

None meeting the bar (a defect names the contract row it breaks, a feasible
project shape under supported public API, and the wire/configuration input
that reaches it). Three observations were driven to a verdict and are NOT
defects:

1. **Runtime `| None` union on the return annotation.** The factory applies
   `_lazy_ref(...) | None` at runtime (not under `from __future__ import
   annotations` semantics). Floor is Python 3.10 (`requires-python =
   ">=3.10,<4.0"` in `pyproject.toml` `9be864937662d3932c1ba754c9b40877e4da2103`),
   so `UnionType` syntax is valid on every supported interpreter. Not routed.
2. **Actor computed before the gate.** The resolve body forces the lazy
   `SimpleLazyObject` while computing the gate's `instance` argument on the
   sync path too. Sync context makes this well-defined, and the async path
   runs the whole body inside the one boundary via the bridge (Decision 10's
   stated reason). Matches the spec body text verbatim. Not routed.
3. **No `require_session` / capability check.** Deliberate per the spec edge
   table (J4); the axis-6 sweep confirms no contract requires it. Not a
   missing guard, not routed.

A pre-existing-failure check is owed and done: no test was run for this item
(per the dispatch: NO shared-tree pytest), so no failure predates or blocks
it; no probe was created to pass or fail.

## Pending execution

None. No `execution-deferred` proof exists. Inspection suffices because every
finding's claim is one of three static kinds, each discharged above: (a)
composition-by-call off an import edge whose owner body was read
(C7–C13, F2, R1/R2 shared halves); (b) a single spanning read of one literal,
flag, or call-arg tuple (C1/C2/C4/C5/C6, F1/F3, R3); (c) absence verified by
grep over the 121-line target (no `sync_to_async`, no `setattr`/`delattr`, no
`get_queryset`/`model_for` in code). Ordering, transactional, and async
behavior beyond (a)–(c) is pinned by the pre-existing oracles named as
structural gates (dispatch spies, denial-string pin, alias-identity, live
`me` rows), which this zero-edit item neither weakens nor needs to re-run.
The final suite gate belongs to the plan's gate item, not this file item. No
workspace copy was needed; no read-only probe was created.

## Judgment

Zero-edit file item. 15 top-level statements / 6 rule-bearing definitions
enumerated, all homed: three reused indexed families (F1
`subsystem-clear-lifecycle` as verified pre-bind row incl. the D15 contrast
with the declarations row; F2 `one-sync-boundary` as indirect consumer via
the bridge with an index-coverage note for Worker 0; F3 `auth-leaf-manifest`
as the symbol's definition site), seven indexed families checked with no
surface and not inherited (C7–C13), three file-local rows (R1 resolve
contract, R2 factory wiring, R3 alias identity) each with its proving
challenge, five rejections with difference + trigger + durable home
(J1–J5). Compared against the sibling `dry-file-auth__mutations.md` by
behavior/contract: queries consumes F10/F11/F12/boundary by call and omits
F13/F14/F15/F16/F18 counterparts by Decision-7/edge-table contract, never by
accident. No defects, no pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `3320e3a77063c572f0e0e14e94a667ca35a6db59`: `git diff
<baseline> -- django_strawberry_framework/auth/queries.py
docs/dry/dry-file-auth__queries.md` empty — target CLEAN. Target blob
`5c59ba75023d21998efc6a8b1b714bdfab273ad7` matches the working tree,
`HEAD:django_strawberry_framework/auth/queries.py`, and the sibling
artifact's freshness line (HEAD `9031cb3d`). The artifact itself
(`docs/dry/dry-file-auth__queries.md`) is a new untracked file, the item's
only output; no probe directory was created under `docs/dry/temp-tests/`
(nothing executed). No `uv run ruff format .` / `ruff check` run (no `.py`
edits to format). Concurrent dirt listed in the dispatch (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus
sibling untracked `dry-file-*.md` artifacts and the sibling's
`temp-tests/dry-file-auth__mutations/` probes were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no row
from this item.

## Independent verification (Worker 2)

Own trace first (recorded before reading `## Findings`; reconciled after).
Target re-read off the working tree (121 lines) plus the connected bodies
listed below. Item-scoped diff confirmed empty myself (see `Zero-edit`).

### Own trace

- **Pre-bind clear row.** One `register_subsystem_clear` call with
  `owner="auth.current_user_alias"`, `before_bind=True`, over the trio's
  clear arm. Definitions on a bus-semantics change: 1, at
  [registry.py][registry]`::register_subsystem_clear`. Owner I would choose:
  the bus. The flag value is this row's declaration. Agree vs W1 F1.
- **Sync-bridge consumer.** Factory passes
  `async_body=_sync_bridged_async_body(sync_body)`; the bridge
  (`auth/mutations.py::_sync_bridged_async_body`) is a real coroutine
  awaiting `run_in_one_sync_boundary`. No `sync_to_async` spelled here
  (code hits: zero; the one `sync_to_async` mention is docstring prose).
  Definitions on a worker change: 0 here, 1 at
  [utils/querysets.py][utils-querysets]`::run_in_one_sync_boundary`.
  Owner: the utils helper. Agree vs W1 F2 (consumer, indirect by call).
- **Manifest definition site.** `current_user` defined here; re-exported by
  [auth/__init__.py][auth-init] (`from .queries import current_user` +
  `__all__` entry, verified); sole factory consumer is
  [accounts-schema][accounts-schema] (`me = current_user()`).
  Manifest owned at `auth/__init__.py`. Agree vs W1 F3.
- **Resolve contract.** [auth/queries.py][auth-queries]`::_current_user_resolve_body`:
  `request_from_info` -> `_authenticated_actor_or_none` ->
  `authorize_or_raise(holder, info, "current_user", None, instance=actor)` ->
  `return actor`, gate-first. Gate-args/order change: 1 definition here.
  Anonymity change: 0 here (owned at
  [auth/mutations.py][auth-mutations]`::_authenticated_actor_or_none`).
  Owner: this module. Agree vs W1 R1, incl. the `instance=actor` vs
  login/logout `instance=None` distinction as Decision-7 contract.
- **Factory wiring.** [auth/queries.py][auth-queries]`::current_user`:
  fourth surface through `_declare_fixed_auth_surface("current_user",
  "CurrentUser", ...)`, sync + bridged-async bodies through `_make_auth_field`,
  return `_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) |
  None`. Nullable/envelope change: 1 here. Declaration-key, dispatch-seam,
  lazy-ref-shape changes: 0 here. Owner: this module. Agree vs W1 R2.
- **Alias identity.** `CURRENT_USER_ALIAS_NAME = "CurrentUserAlias"` (one
  literal; used at the lazy-ref call site and imported by the bind) and
  `AUTH_QUERIES_MODULE_PATH` (one literal; shared by the trio call and the
  lazy-ref call); trio unpack homes ledger + materialize arm (consumed by
  `bind_auth_mutations`) + clear arm (F1 row). Spelling changes: 1 each
  here. Trio-mechanics change: 0 here (owned at
  [utils/inputs.py][utils-inputs]`::make_input_namespace`). Owner: this
  module (narrowest both consumers import). Agree vs W1 R3.

Connected bodies re-read: [auth/mutations.py][auth-mutations] declaration
path, bridge seam, anonymity definition, `bind_auth_mutations` alias call;
[utils/inputs.py][utils-inputs]`::make_input_namespace` trio shape +
parked-global paragraph; [mutations/fields.py][mutations-fields]`::_lazy_ref`
+ `::build_lazy_field_signature`;
[utils/permissions.py][utils-permissions]`::request_from_info`;
[mutations/resolvers.py][mutations-resolvers]`::authorize_or_raise`;
[registry.py][registry]`::register_subsystem_clear`;
[utils/querysets.py][utils-querysets]`::run_in_one_sync_boundary`;
[finalizer.py][finalizer] phase-2.5 window; oracles
[test-auth-queries][test-auth-queries] (spot-read alias, dispatch-spy,
denial-string, lazy-forcing, hostile-shape rows) + consumer
[accounts-schema][accounts-schema]; spec Decision 7 / D-N1 / edge table
(`register` / `me` unaffected; anonymous `me` is `null`, never an error).

### Enumeration (member-by-member vs own count)

Instrument re-run myself: `ast.parse`, `len(ast.Module.body)` = **15**.
Members: 0 module docstring; 1-8 eight imports (`__future__`,
`functools`, `typing.Any`, `_lazy_ref`, `register_subsystem_clear`,
`make_input_namespace`, `request_from_info`, `.mutations` 5-name block);
9 `AUTH_QUERIES_MODULE_PATH`; 10 `CURRENT_USER_ALIAS_NAME`; 11 trio unpack;
12 `register_subsystem_clear(...)` call; 13 `_current_user_resolve_body`;
14 `current_user`. Matches W1's table exactly. Rule-bearing definitions:
**6** (2 functions + 2 constants + 1 trio + 1 bus row). Every member homed:
docstring projection; imports consumers-by-import; 9-10 R3; 11 R3 + F1;
12 F1; 13 R1; 14 R2. No unassigned member. Agree.

### Matrix (against the real surface)

1. **Cross-flavor.** Agree: `me` returns the user type directly (`null`
   for anonymous), no envelope, by Decision 7; shared declaration / seam /
   bridge / anonymity / gate / lazy-ref / label all consumed by call or
   imported constant, never re-spelled. Absences (no F13 prologue, no F14
   envelope, no F15 critical section, no F18 rider) each carry a
   Decision-7/edge-table source. Not gaps.
2. **Sync/async.** Agree: one sync body; async path is the shared interim
   bridge, not a native per-transport body like login/logout carry. No twin
   to drift; bridge-shape change owned at sibling F11. J2 rejected correctly.
3. **Derived knowledge.** Agree: alias name + module path single-spelled
   and shared; request/permission/gate/lazy/boundary all by call; `| None`
   is the me-only contract at one call site (J1).
4. **Round-trip.** Agree: materialize/clear trio-owned; bind calls the
   materialize arm, this module's pre-bind row calls the clear arm; no
   `setattr`/`delattr` in code (both words appear only in the docstring's
   reuse pointer — re-verified by read). No second lifecycle.
5. **Other media.** Agree in substance with one prose correction (below):
   production + spec Decision 7/D1/D4/D12/D13/D15/D17/D-N1/edge table +
   oracles + docstring projections. No oracle was rewritten by this
   zero-edit item. Correction: the alias-ledger assertions do read owner
   objects (`CURRENT_USER_ALIAS_NAME`, `_current_user_alias_names`,
   `clear_current_user_alias_namespace`), so "oracles never read the owner"
   overstates it. The independent pins remain: `auth_queries.CurrentUserAlias
   is user_type` reads the parked global by literal attribute name (fails on
   a rename), the denial string is spelled literally, the dispatch spies pin
   boundary counts, SDL/live rows pin `me: UserType` and anonymous-`null`.
   Ledger-equality lines are auxiliary, not the independence carrier.
6. **Omission.** Agree: gate runs on the only path, gate-first;
   `permission_classes` rides the shared fixed path; deliberate omissions
   (no prologue, no `get_queryset`/re-fetch, no envelope, no
   `require_session`) each carry a contract source (edge table, D-N1,
   Decision 7). No member lacks a required guard. No defect.

### Counts + roles; equivalence

Challenges C1-C13 re-derived: C1/C2 1 each here; C3 trio mechanics 1 at the
owner (0 here); C4 bus semantics 1 at the owner (0 new here; flag choice is
this row's declaration); C5 gate args/order 1 here; C6 nullable shape 1 here;
C7-C13 0 here (anonymity, declaration key, dispatch seam, boundary worker,
request wording/label, lazy-ref shape, holder synthesis/seal — owners
elsewhere). Consumers/oracles/projections listed, never counted. Agree.
Roles confirmed: definitions at the bus / utils helper / trio owner /
sibling owners vs consumers-by-call here; oracles pre-existing at
`tests/auth/test_queries.py` + live fakeshop auth API rows; projections in
module/factory/body docstrings + consumer schema. No oracle rewritten (zero
production edits, zero test edits).
Principle 8: no consolidation, so no observable-behavior migration to prove.
W1's `static-reviewed` proofs each name the rejected wrong result (stale
alias across reloads, declarations draining pre-bind, extra/missing boundary
entry, gate-vs-null reorder, envelope-ized `me`) discharged by the named
pre-existing spies/identity/denial/SDL rows. Adequate for a zero-edit file
item; the final suite gate re-runs them.

### Zero-edit

`git diff 3320e3a77063c572f0e0e14e94a667ca35a6db59 --
django_strawberry_framework/auth/queries.py` re-run myself: empty (exit 0).
`git status --short` re-run: target clean; only concurrent dirt plus the
untracked `docs/dry/dry-file-auth__queries.md` artifact. Coverage validated
(`### Enumeration` accounts for all 15; every challenge ends in F1-F3, R1-R3,
C7-C13 no-surface, or J1-J5). Assignment validated (family rows reuse indexed
names; file-local rows carry proving challenges; rejections carry homes). No
candidate owes a holding family beyond the reused ones; a file item owes no
production edit. `## Owned changes` correctly gains no row.

### Rejections, fingerprints, gates, pending, coupling

J1-J5 each carry a concrete contract difference, the reconsideration trigger
(second nullable lazy return; read-side async work; finer-than-boolean bus
phase; read surface needing durability; uniform read errors), and a durable
home (factory docstring; bridge docstring + Decision 10; module pre-bind
paragraph + Decision 9/D15; spec edge row + body comment; Decision 7).
Difference + trigger judged correct in all five; none is a shared-responsibility
split.
Freshness re-hashed myself via `git hash-object` (working tree): target
`5c59ba75023d21998efc6a8b1b714bdfab273ad7`,
[registry.py][registry] `9cc8bb553fd417fc465809a541769a8383469cda`,
[utils/inputs.py][utils-inputs] `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`,
[finalizer.py][finalizer] `77fd9a2dd229eb9de5f29188c5058035d3606323`,
[test-auth-queries][test-auth-queries] `7d7cfcedb74bfb36e233d5ad71d50326f02eab1d`,
[utils/querysets.py][utils-querysets]
`1539b66c9ce9a659e1dc5f6bf1029b15d6868587`,
[auth/mutations.py][auth-mutations] `dbe64995b87240b87a1d5119f46cc42c7cab646f`,
[auth/__init__.py][auth-init] `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
[accounts-schema][accounts-schema] `c0fdc23be03f7ea0c621492b96a1a4857ef60a74`,
[mutations/fields.py][mutations-fields]
`cf518361d7884b8b71550cb6b73bff0c1a64549e`,
[utils/permissions.py][utils-permissions]
`9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`, resolvers
`3fd1e57199b6366a8bc0b1661518e8bc8949ece4`. All match W1. Target blob also
equals `HEAD:django_strawberry_framework/auth/queries.py`; HEAD is `9031cb3d`.
Negative controls: each relied-on oracle would fail its bypass — missing
pre-bind row leaves a stale alias across reloads (collision guard fires);
inlined/duplicated boundary changes the dispatch-spy counts; gate reorder or
`instance` change moves the pinned denial string / recording-gate `seen`
tuple; dropped re-export breaks the consumer-schema import; envelope-izing
`me` breaks SDL + anonymous-`null` rows. No `prove_failability.py` run was
owed: zero-edit file item, dispatch barred shared-tree pytest, and the
plan's gate item re-runs the suite.
`## Pending execution`: absent. Endorsed as adequate — every finding's claim
is composition-by-call off a read owner body, a single spanning read of one
literal/flag/arg tuple, or grep-verified absence over 121 lines, with
ordering/async pinned by the named pre-existing spies. No probe under
`docs/dry/temp-tests/` was needed; none created. Coupling: `none`
throughout + `Migration: none` stated once — correct, the item consolidates
nothing.

### One-sync-boundary files-covered note (ruling)

W1's note verified and endorsed. Claim: the `one-sync-boundary`
files-covered list names `auth/mutations.py` but not `auth/queries.py`,
while this file reaches the boundary through the bridge defined there.
Verified: plan row lists `auth/mutations.py` without `auth/queries.py`;
`auth/queries.py` line 115 calls `_sync_bridged_async_body(sync_body)` and
that helper (`auth/mutations.py` line 392-393) awaits
`run_in_one_sync_boundary`; the resolve body's lazy-user forcing therefore
runs inside the one boundary (Decision 10), pinned by
`test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary`.
`auth/queries.py` is a genuine (indirect) consumer site and belongs on the
family's files-covered list. Exact corrected row Worker 0 should write:

`| `one-sync-boundary` | `utils/querysets.py::run_in_one_sync_boundary` |
`utils/querysets.py`, `schema.py`, `permissions.py`, `orders/sets.py`,
`filters/sets.py`, `mutations/resolvers.py`, `auth/mutations.py`,
`auth/queries.py`, `types/resolvers.py`, `testing/client.py` | Family
`one-sync-boundary` | open |`

(single change: insert `auth/queries.py` after `auth/mutations.py`; no other
token moves; status stays `open` for the family item).

### AGENTS.md prose check

Item-scoped content is the untracked artifact only (no `.py` edits, so no
`ruff format` / `ruff check` run owed). Citations use `path::Symbol` form
through reference-style links with the 10 canonical group headers intact; no
`path:NN` citations found; no process provenance or author-attribution
footer; tests stay at the mandated tiers (`tests/auth/`, live fakeshop auth
API rows) with no new example model; `__version__` untouched. Pass.

## Defects (Worker 2)

None. The three W1 non-defect verdicts re-checked: runtime `| None`
valid under `requires-python = ">=3.10,<4.0"` (re-read from
`pyproject.toml`); actor-computed-before-gate matches the spec body and runs
in-boundary on the async path via the bridge; no `require_session` is the
spec-edge-table exemption (J4), not a missing guard. No new defect found.

## Judgment (Worker 2)

`Status: verified`. Zero-edit file item: 15 statements / 6 rule-bearing
definitions, all homed; matrix discharged against the real surface; counts,
roles, and rejections confirmed; fingerprints re-hashed and matching;
inspection-only (no probe, no pending execution) adequate for this 121-line
read-path file; concurrent dirt preserved; no commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[registry]: ../../django_strawberry_framework/registry.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-auth-queries]: ../../tests/auth/test_queries.py

<!-- examples/ -->
[accounts-schema]: ../../examples/fakeshop/apps/accounts/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
