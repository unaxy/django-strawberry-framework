# DRY review: `django_strawberry_framework/auth/sessions.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in a family row (reused indexed name) or a file-local row with
its proving challenge, plus rejections carrying contract difference +
trigger + durable home. Zero production edits; zero tracked files changed.

## System trace

FRESH target (397 lines): the transport-owned auth session boundary —
transport classification + capability answers + the per-scope session lock
the login / logout state machines build on. The module defines the explicit
[Transport][auth-sessions] modes, the channels soft-dependency entry
(`require_channels`), the `isinstance`-first classifier
(`classify_transport`), the missing-session pre-check (`require_session` +
`_safe_transport_label`), the scope-mutability gate
(`_require_mutable_scope`) and the single acquisition helper
(`scope_session_lock`), and the capability answers
(`uses_signed_cookie_sessions`, `login_supported`, `logout_supported`).
It composes everything else by call, never re-spells: the engine expression
rides [utils/sessions.py][utils-sessions]`::session_store_class`, the
scope key + singleton mechanics ride `::scope_key` / `::scope_singleton`,
the guard primitive rides
[utils/imports.py][utils-imports]`::require_optional_module`, request
resolution rides
[utils/permissions.py][utils-permissions]`::request_from_info` (upstream),
and the hostile renderers ride [exceptions.py][exceptions]`::_safe_type_name`
/ `::_safe_arg_repr`. Its consumers are the login/logout prologues and
critical sections in [auth/mutations.py][auth-mutations] (by call) and, by
omission, `current_user` in [auth/queries.py][auth-queries] (no prologue by
spec edge-table contract). The module holds NO actor lease and never
imports it: the lease's lessee is
[auth/mutations.py][auth-mutations]`::_channels_logout`, which enters
[utils/sessions.py][utils-sessions]`::actor_transition` INNER while
already holding this module's lock OUTER.

Connected code read for judgment, outside the item:
[auth/__init__.py][auth-init] (leaf manifest + Decision-3 opt-in, full),
[auth/mutations.py][auth-mutations] (prologue, capability predicates,
both critical sections, the lease holding site at `_channels_logout`,
full read of the cited regions), [auth/queries.py][auth-queries]
(sibling artifact `dry-file-auth__queries.md` used as rejected-candidate
triggers only — compared by behavior/contract, nothing inherited),
[utils/sessions.py][utils-sessions] (full: engine resolver, singleton,
lease, provenance, lock-order prose), [utils/imports.py][utils-imports]
(full), [routers.py][routers]`::require_channels` + hint block,
[utils/permissions.py][utils-permissions]`::ChannelsRequestAdapter` +
`::request_from_info` (adapter shape, `__getattr__` delegation, scope
reads), [exceptions.py][exceptions] (safe-renderer ladder),
[consumers.py][consumers] (engine reach-through at `_refreshed_actor`),
[keyset.py][keyset] + [rest-init][rest-init] + [debug-toolbar][debug-toolbar]
(same-primitive different-dep guards, guard lines only), oracles
[test-auth-sessions][test-auth-sessions] (824 lines, full),
[test-routers][test-routers] (hint-substring row),
[test-governance][test-governance] (floor-drift rows), live
[test-auth-api][test-auth-api] (sessionless rows, spot-read), consumer
[accounts-schema][accounts-schema] (full), contract source
[spec-040][spec-040] (auth session-lifecycle + capability rows, cited
regions re-read off the tree).

Excluded with reason: the concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, sibling
`dry-file-*.md` artifacts) was left untouched; none is in this item's
paths. `connection.py`-owned families were not re-derived beyond the
attribution check. Every other indexed family was judged on its mechanism
against this target's REAL surface (Matrix + Challenges C12–C18).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Auth is one flavor; no sibling flavor
mirrors transport classification — filters/orders/mutations never classify
a Channels scope, so there is no second classifier to drift. The four auth
surfaces share the prologue by call (`_transport_prologue` composes
`classify_transport` / capability predicate / `require_session`; the
`me` surface deliberately omits it per the spec edge table — sibling
queries J4, a contract source, not a gap). The three write flavors'
`resolve_async` boundary sharing is owned at `one-sync-boundary`; this
file spells no `sync_to_async` (zero code hits) and owns no resolver body.
Considered families: `one-sync-boundary` (checked, no surface — C12),
`sealed-authorization-source` (no seal here — C18),
`subsystem-clear-lifecycle` (no bus row here — C15).

**2. Sync/async twins.** One async member only
(`scope_session_lock`, an `asynccontextmanager` around an
`asyncio.Lock.acquire` that must await); no sync twin exists and none is
owed (J5): per-request bridge scopes live on one private loop each while
multiplexed WebSocket scopes never enter the bridge — the contrast is
recorded in the helper's own docstring, and the sync-bridge arm owes no
second body. `classify_transport` / `require_session` / the capability
answers are sync-pure (no ORM, no await points). Compared by behavior, not
shape; the serialization/cancellation behavior is pinned by the lock
oracles, not by a twin.

**3. Derived rather than repeated knowledge.** Every shared derivation is
consumed by call or by import, never re-spelled: the engine class via
`session_store_class()`, the scope key via `scope_key(...)`, the singleton
via `scope_singleton(...)`, the floor via the `CHANNELS_FLOOR` import
(zero bare `4.3` literals in this file or the router — probe P1), the
request object itself (resolved upstream by `request_from_info`). The one
local derivation is `_SCOPE_LOCK_KEY` (one literal via the shared builder,
consumed five times in-file) and the four lock-failure wordings (one
`ScopeSingletonMessages` record, the per-surface data the shared algorithm
requires). The `Transport` enum is the single spelling of the three modes;
`is_http`/`is_websocket` are `==` probes against `scope["type"]`, not a
second spelling.

**4. Inverse / round-trip pairs.** No encode/decode halves. The lock's
acquire/release pairing is one context manager, not two halves that can
drift; the singleton get-or-create is one body owned in
[utils/sessions.py][utils-sessions]; the capability predicate pair
(`login_supported` / `logout_supported`) answers two different questions
(any-WebSocket vs signed-cookie-WebSocket) over different inputs, not two
halves of one grammar.

**5. Contracts restated in another medium.** Production (this file) +
authoritative contract ([spec-040][spec-040] classify → capability →
session steps + WebSocket-login refusal rationale) + independent oracles
([test-auth-sessions][test-auth-sessions] classification table,
missing-session rows, lock lifecycle rows, capability truth tables,
hostile-containment rows; [test-auth-api][test-auth-api] sessionless
login/logout rows; [test-routers][test-routers] hint-substring pin;
[test-governance][test-governance] floor-drift pins) + projections (module
docstring incl. the non-re-export clause; consumer
[accounts-schema][accounts-schema] via the mutations layer). Oracles never
read the owner: the lock test spells the raw key bytes literally (fails on
a rename), the capability tests assert bare booleans, the hint tests match
`channels>=4.3.2` without importing the constant, the failure tests match
message substrings (`"session"`, `"mutable Channels scope"`). Counts below
count definitions only; oracles/projections are listed per finding.

**6. Enforcement by omission.** Sweep over all ten rule-bearing members:
every path that needs a guard has one (classification rejects unknown
transports; capability predicates gate before session work at the caller;
`require_session` pre-checks both middleware absences; the lock rejects
immutable scopes and corrupted slots loudly; hostile dunders are contained
at every read). Deliberate omissions, each with a contract source: no
actor lease here (J1 — separate session surface, lessee is
`_channels_logout`); no `describe_value` tail (J3 — inline safe-renderer
composition, different contract); no clear-bus row (C15 — nothing here has
ledger lifecycle); no sync lock twin (J5). No member lacks a guard its
contract requires — no defect.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **25 top-level statements** (1 docstring + 11 imports + 3
module-level bindings + 1 class + 9 functions, of which 1 async). The
audit counts **13 rule-bearing definitions** (1 enum + 9 functions + 3
constants). Every member lands below; every challenge in `### Challenges`
ends in a family row, a file-local row, or a rejection.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (opt-in + classification + privacy clause) | projection (F2/F3/F6 pointers; owned at spec + bodies) |
| 1–11 | 11 imports (`__future__`, `asyncio`, `contextlib`, `enum`, `AsyncIterator`/`MutableMapping`, `Any`, `HttpRequest`, exceptions trio, imports pair, `ChannelsRequestAdapter`, sessions quartet) | consumers by import (no rule) |
| 12 | `_CHANNELS_INSTALL_HINT` | F1 |
| 13 | `_SCOPE_LOCK_KEY` | F3 |
| 14 | `_SCOPE_LOCK_MESSAGES` | F3 |
| 15 | `Transport` | F2 |
| 16 | `require_channels` | F1 |
| 17 | `classify_transport` | F2 |
| 18 | `_safe_transport_label` | F4 (+ nested rejection vs `_safe_class_name`) |
| 19 | `require_session` | F4 |
| 20 | `_require_mutable_scope` | F3 |
| 21 | `scope_session_lock` | F3 |
| 22 | `uses_signed_cookie_sessions` | F5 |
| 23 | `login_supported` | F5 |
| 24 | `logout_supported` | F5 |

Two indexed families reused as rows (F1, F6); six indexed families
checked with no surface and not inherited (C12–C18, J1–J4); four
file-local rows (F2–F5); five rejections with difference + trigger + home
(J1–J5, J5 file-local-adjacent).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 hint wording | reword the auth install hint | **1** (own hint; router's unaffected; floor import untouched) | family row (member site) |
| C2 | F1 floor | bump the verified Channels floor | **1** in source (`CHANNELS_FLOOR`; both hints follow by reference; `pyproject.toml` row + governance pin listed as the packaging co-mover) | family row (member site) |
| C3 | F2 transport set | admit a 4th scope type (e.g. `"sse"`) | **1** (enum + classifier move together; callers follow; reject-unknown oracle lists `"sse"` as rejected) | file-local |
| C4 | F2 classification order | sniff `scope["type"]` before `isinstance` | **1** (first branch; adapter `__getattr__` rationale in docstring; hostile-adapter oracles pin the order) | file-local |
| C5 | F3 lock lifecycle | make the lock reentrant / process-global | **1** (helper + messages; invariant-12 oracle forbids the registry) | file-local |
| C6 | F3 key bytes | rename the scope key | **1** (constant; oracle spells the raw bytes literally) | file-local |
| C7 | F4 pre-check wording | reword the missing-session error | **1** (the function; oracle pins the `"session"` substring as the constraint) | file-local |
| C8 | F4 hostile label | change the transport-label fallback | **1** (helper; `_safe_class_name` doesn't move — different input contract) | file-local + nested rejection |
| C9 | F5 engine axis | recognize a new engine kind | **1** (`uses_signed_cookie_sessions`; default/signed/subclass oracles pin the `issubclass` shape) | file-local |
| C10 | F5 capability axis | allow WebSocket login | **1** (`login_supported`; oracle pins `False`; logout row unaffected) | file-local |
| C11 | F6 privacy | promote a sessions helper to the public surface | **1** (sessions definition; manifest row follows) | indexed file-local row (definition site) |
| C12 | `one-sync-boundary` check | change the worker (e.g. thread-sensitivity) | **0 here** (zero `sync_to_async`/boundary code hits; owner in utils) | no surface — do not inherit |
| C13 | lease semantics/order | change lease acquisition or the outer/inner order | **0 here** (lease owned in utils; the one holding site is `auth/mutations.py::_channels_logout`) | no surface — do not inherit (J1) |
| C14 | rejection-tail wording | change the `got {type} {value!r}` fragment | **0 here** (`describe_value` never used; safe renderers composed by call) | no surface — do not inherit (J3) |
| C15 | clear-bus semantics | add a clear phase | **0 here** (no bus row; no ledger lifecycle) | no surface — do not inherit (J4) |
| C16 | refusal/disposal protocol | route refused awaitables through a new protocol | **0 here** (no awaitable handling; owner in utils) | no surface — do not inherit |
| C17 | seal behavior | change the authorization seal | **0 here** (no seal halves; owners in mutations sets/auth) | no surface — do not inherit |
| C18 | registry/relay/globalid | change model-type mapping or node decode | **0 here** (no registry/relay surface) | no surface — do not inherit |

Executable proofs: P1 (23 checks), P2 (18 checks), P3 (31 checks) —
72/72 `execution-verified`, all as read-only scripts in the shared tree
(no source mutation, no DB writes, in-memory scopes/requests only,
`override_settings` + stub engine module restored/removed on exit):
`uv run python docs/dry/temp-tests/dry-file-auth__sessions/probe_softdep.py`,
`.../probe_privacy.py`, `.../probe_transport.py`.
All other claims are `static-reviewed` (single spanning reads, bodies
composed by name, grep-verified absences over the 397-line target).
NO shared-tree pytest ran (per the dispatch).

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved its home. `Migration: none` throughout
(zero-edit item) — stated once here, not per row. `Coupling: none`
throughout (file item consolidates nothing) — likewise stated once.

### F1 — `soft-dependency-require-guard` (family row, member site)

- **Contract + variation.** Every soft dependency is reached through one
raising primitive with a per-feature install hint naming the verified
floor. Varies only in dependency + hint wording.
- **Sites + roles.** *Definition (owner)*:
[utils/imports.py][utils-imports]`::require_optional_module` (+
`::CHANNELS_FLOOR`, the single floor literal). *Member site here*:
[auth/sessions.py][auth-sessions]`::require_channels` (docstring + single
`return require_optional_module("channels",
install_hint=_CHANNELS_INSTALL_HINT)`) over this module's own
`_CHANNELS_INSTALL_HINT`. *Twin member*:
[routers.py][routers]`::require_channels` (same shape, router-keyed
wording). *Same-primitive different-dep sites* (surveyed, untouched):
[rest-init][rest-init]`::require_drf`,
[debug-toolbar][debug-toolbar]`::require_debug_toolbar`,
[keyset.py][keyset] crypto loads. *Oracles*:
`test_classify_channels_scope_without_channels_raises_the_install_hint`
+ `test_auth_submodule_import_stays_channels_free` (subprocess),
[test-routers][test-routers] hint-substring pin,
[test-governance][test-governance] floor-vs-pyproject drift pins.
- **Challenges.** C1 → 1; C2 → 1 in source (packaging row listed).
- **Owner + lifetime.** Indexed owner; no stored derivation. This site is
a member, not a second definition: posit a hint reword → only this hint
moves; posit a primitive change → only the owner moves.
- **Behavioral proof.** `execution-verified` (P1: 23/23 — twin bodies,
own-hint wiring, `CHANNELS_FLOOR` interpolation, zero re-typed literals,
single-sited owner). Rejects "the auth guard hand-rolls its import" and
"the floor is re-typed at a guard site".
- **Structural gate.** The oracles above (pre-existing); negative control
= P1's distinct-wordings + absent-literal checks.
- **Freshness.** Target as header; [utils/imports.py][utils-imports]
`291ecedd30c7d8af9c007758112e867c09d031eb`;
[routers.py][routers]
`a18c5001471d4a937bb81d2ff41a2e442e7d2dad`;
[test-auth-sessions][test-auth-sessions]
`ef7d7c78011a67d20edc9fa7a28623c66abd9978`;
[test-governance][test-governance]
`2074291d2858acb76f83ca6c4d6c332efdc02d69`;
`pyproject.toml` `9be864937662d3932c1ba754c9b40877e4da2103`.

### F2 — transport classification (file-local)

- **Contract + variation.** The `request_from_info` result resolves to ONE
explicit [Transport][auth-sessions] mode: `isinstance` against
`ChannelsRequestAdapter` first (attribute sniffing is unreliable under its
`__getattr__` delegation), then `scope["type"]` splitting Channels HTTP
from WebSocket; `HttpRequest` takes the native path; everything else is a
typed `ConfigurationError`. Varies in the mode set + the read order.
- **Sites + roles.** *Definitions*: `Transport` + `classify_transport`.
*Upstream owner of the shaped object*:
[utils/permissions.py][utils-permissions]`::ChannelsRequestAdapter`
(+ `::request_from_info`). *Consumers by call*:
[auth/mutations.py][auth-mutations]`::_transport_prologue` (both
login/logout arms, sync + async). *Contract source*:
[spec-040][spec-040] classify step. *Oracles*: classification table,
unknown/missing/foreign rejections, hostile-scope/eq/repr/class
containment rows.
- **Challenges.** C3 → 1; C4 → 1.
- **Owner + lifetime.** This module (narrowest owner every consumer
already imports). No stored derivation.
- **Behavioral proof.** `execution-verified` (P3 classify block: 7/7 incl.
hostile-repr containment). Rejects "a lifespan scope takes a native path"
and "a hostile `__eq__` escapes as a raw error".
- **Structural gate.** The oracles above (pre-existing); negative control
= P3's missing/lifespan/foreign + hostile checks.
- **Distinct behavior.** The channels-absent `ImportError` (F1) fires
between recognition and scope read — a soft-dep refusal, not a
classification answer; ordering verified (guard before `scope["type"]`).
- **Freshness.** Target as header;
[utils/permissions.py][utils-permissions]
`9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`;
[auth/mutations.py][auth-mutations]
`dbe64995b87240b87a1d5119f46cc42c7cab646f`.

### F3 — per-scope session lock (file-local)

- **Contract + variation.** Same-scope session mutations serialize under
ONE scope-owned `asyncio.Lock`, lazily created with no `await` between
read and store (atomic on the single loop), acquired through the single
helper; scope-ownership (never process-global — invariant 12),
mutability, and corruption are all loud `ConfigurationError`s. Varies in
key bytes, message wordings, and the acquire/release discipline.
- **Sites + roles.** *Definitions*: `_SCOPE_LOCK_KEY`
(`scope_key("auth_session_lock")`), `_SCOPE_LOCK_MESSAGES`
(`ScopeSingletonMessages` record), `_require_mutable_scope`,
`scope_session_lock`. *Shared by call*:
[utils/sessions.py][utils-sessions]`::scope_key` / `::scope_singleton`
(the get-or-create body, incl. its no-`await` atomicity + corrupted-slot
prose). *Consumer by call*:
[auth/mutations.py][auth-mutations] login/logout critical sections (the
OUTER half of the lease order). *Oracles*: lazy-create/reuse,
serialization-with-waiter-queue, immutable-scope, corrupted-slot,
cancellation-pair, cross-scope-independence, no-global-registry rows.
- **Challenges.** C5 → 1; C6 → 1.
- **Owner + lifetime.** This module (auth-boundary lock ownership).
Lifetime: scope-dict entry under the namespaced key, created on first use,
never cleared by the package (no bus row — C15).
- **Behavioral proof.** `execution-verified` (P3 lock block: 9/9 —
held-inside, key bytes, reuse, independence, no orphan, immutable loud,
corrupted loud, no-global-registry). Rejects "two operations mint two
locks" and "a second scope blocks on the first".
- **Structural gate.** The oracles above (pre-existing); negative control
= P3's immutable/corrupted + independence checks.
- **Distinct behavior.** Async-only by construction (J5); the loop caveat
is stated in the helper docstring, not enforced in code — enforcement
lives at the call sites (per-request bridge scopes vs multiplexed
WebSocket scopes), read and confirmed.
- **Freshness.** Target as header;
[utils/sessions.py][utils-sessions]
`f0d9297c942a4915ca08ac0714cee73f6042af34`.

### F4 — missing-session pre-check + hostile transport label (file-local)

- **Contract + variation.** `require_session` collapses both middleware
absences (Django request without `SessionMiddleware`;
Channels scope with `None` session) to `getattr(request, "session",
None) is None` and raises the transport-specific configuration error
(keeping the `"session"` substring) instead of a downstream
`None.cycle_key()` `AttributeError`. `_safe_transport_label` renders the
label without trusting `transport.value` / `__repr__` / str-subclass
dunders, falling back to `_safe_type_name`; the success path never
touches the label at all. Varies in wording + label discipline.
- **Sites + roles.** *Definitions*: `require_session`,
`_safe_transport_label`. *Composed by call*:
[exceptions.py][exceptions]`::_safe_type_name` / `::_safe_arg_repr`.
*Consumers by call*: both prologues in
[auth/mutations.py][auth-mutations]. *Oracles*: present-session
pass-through (both transports), `None`-session raise, hostile
descriptor/getattr/value/repr/str rows, success-does-not-touch row,
live [test-auth-api][test-auth-api] sessionless rows.
- **Challenges.** C7 → 1; C8 → 1.
- **Owner + lifetime.** This module (auth-boundary error contract). No
stored derivation.
- **Behavioral proof.** `execution-verified` (P3 pre-check block: 5/5).
Rejects "a sessionless login crashes in `cycle_key`" and "an evil
`transport.value` replaces the typed error".
- **Structural gate.** The oracles above (pre-existing); negative control
= P3's hostile-value + success-path checks.
- **Rejection (nested).** Considered: fold `_safe_transport_label` into
[exceptions.py][exceptions]`::_safe_class_name`. Contract difference: the
class renderer reads `__name__`/`__qualname__` off a class object; this
helper reads `.value` off a `Transport` carrier with a str-slot fast path
for the enum's own string values. Posit a class-label fallback change →
only the basement moves; posit a transport-wording change → only this
helper moves. Trigger: a shared "render an enum carrier for an error"
shape with a second caller. Durable home: the helper docstring (already
states the carrier contract).
- **Freshness.** Target as header;
[exceptions.py][exceptions]
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`;
live [test-auth-api][test-auth-api]
`b4fec8cd415cf53a7597a2aa1d27e1540e31b1be`.

### F5 — session-engine capability answers (file-local)

- **Contract + variation.** `uses_signed_cookie_sessions` answers the
engine question from settings (not adapter metadata) through the shared
resolver with an `issubclass` test so subclasses share the
no-server-side-record limit. `login_supported` refuses ANY WebSocket
(no replacement cookie can be sent over an established socket).
`logout_supported` refuses only the signed-cookie WebSocket (server-side
engines revoke by record deletion; a signed-cookie socket has no record
and no cookie path). Varies on the engine axis + the transport axis
independently.
- **Sites + roles.** *Definitions*: the three functions. *Shared by call*:
[utils/sessions.py][utils-sessions]`::session_store_class` (the ONE
engine expression; its other caller is
[consumers.py][consumers]`::_refreshed_actor`, which instantiates it —
read vs instantiate, same resolver). *Consumers by call*: the prologue
predicates in [auth/mutations.py][auth-mutations]. *Contract source*:
[spec-040][spec-040] capability step + root-cause-3 rationale.
*Oracles*: default/signed-cookie/subclass detection trio, login table,
logout table + signed-cookie-WebSocket row.
- **Challenges.** C9 → 1; C10 → 1 (per axis; `logout_supported` follows
the engine answer by call, never re-spells it).
- **Owner + lifetime.** This module (transport capability). Settings read
at call time (honors `override_settings`); no stored derivation.
- **Behavioral proof.** `execution-verified` (P3 capability block: 10/10).
Rejects "a subclassed engine is treated as revokable" and "a WebSocket
login is admitted".
- **Structural gate.** The oracles above (pre-existing); negative control
= P3's subclass + signed-cookie-WebSocket checks.
- **Freshness.** Target as header; utils-sessions as F3;
[consumers.py][consumers]
`18f3ea161b6081a91445796902a9635cb7e2e3bc`.

### F6 — `auth-sessions-privacy-omission` (indexed file-local row, definition site)

- **Contract + variation.** Transport/session internals (`Transport`,
`classify_transport`, `require_session`, scope lock, capability answers)
stay submodule-private: neither `auth.__all__` nor the package root names
them. Varies per symbol only (a future public helper gains one row).
- **Sites + roles.** *Definition*: this module (the private API itself +
the "deliberately NOT re-exported" clause in its docstring, verified
verbatim). *Enforcement site*:
[auth/__init__.py][auth-init] statements 2–4 (the omission; index row
stays `file-local` there per the plan — no change). *Rationale at the
owner*: `auth/__init__.py` eagerly imports `.mutations` / `.queries`, so
an `auth`-hosted resolver would register the whole opt-in subsystem on
the first authenticated WebSocket operation just to read
`SESSION_ENGINE` — hence the resolver lives in
[utils/sessions.py][utils-sessions], which both sides already depend on
(cycle-neutrality verified: no top-level auth/consumers/routers/channels/
Django imports; both Django imports function-local). *Oracles*:
[test-auth-sessions][test-auth-sessions] imports from the full submodule
path; [consumers.py][consumers] reaches the engine through
`session_store_class`, never through `auth`.
- **Challenges.** C11 → 1 (sessions definition; manifest row follows).
- **Owner + lifetime.** This module (transport classification +
capability). No stored derivation.
- **Behavioral proof.** `execution-verified` (P2: 18/18 — clause present,
manifest exactly-four with no sessions names, no `__all__` here, root
imports no auth, utils cycle-neutrality, consumers engine path).
Rejects "the engine is reachable through `auth`" and "a fifth name leaks
through the manifest".
- **Structural gate.** Omission by absence: any public-use addition
arrives as a visible import line in the manifest (review-visible, not
silently absorbable); the auth-free subprocess oracles pin the opt-in
from the other side.
- **Freshness.** Target as header; [auth/__init__.py][auth-init]
`6bc3c4a5eb965988d91fef5c87240826e5163e6c`; package root verified
auth-free by AST (no fingerprint owed beyond the read — root blob
unchanged by this item; see Implementation).

### J1 — `ws-connection-actor-state` (rejected for this file; separate session surface)

Considered: this file as a member/lessee of the actor-lease family.
Contract difference: the family serializes WebSocket revalidation
checkpoints against package-owned actor transitions via the
connection-scoped lease ([utils/sessions.py][utils-sessions]`::actor_lease`
/ `::actor_transition`, held across validate/commit/send and across
native teardown respectively). This file owns the OTHER primitive — the
per-scope session-mutation lock — and never touches the lease (zero
`actor_lease`/`actor_transition` hits; `actor_lease` population is
[utils/sessions.py][utils-sessions] alone — P2). The ONE site holding
both is [auth/mutations.py][auth-mutations]`::_channels_logout` (scope
lock OUTER at line 916, lease INNER at line 918, order prose verified
verbatim at both ends). Posit a lease-semantics change → utils +
consumers + mutations move; this file does not (C13 → 0 here). The shared
`scope_singleton`/`scope_key` reuse is composition by call inside F3, not
lease membership. Trigger: this module acquiring or ordering against the
lease would make it a member. Durable home:
[utils/sessions.py][utils-sessions] module docstring (names the holding
site + order) + `_channels_logout` docstring.

### J2 — `one-sync-boundary` (checked, no surface)

The file spells no `sync_to_async` / `database_sync_to_async` and calls
no boundary worker (zero code hits for all three spellings). The async
helper awaits only a lock acquisition — no ORM, no thread-affinity
question. Posit a worker change → 0 here (C12). Do not inherit.

### J3 — `typed-rejection-value-tail` (checked, no surface)

`describe_value` never appears in the target (zero hits); the file
composes the lower-level `_safe_type_name` / `_safe_arg_repr` by call for
inline tails, not the `got {type} {value!r}` fragment the family owns.
Posit a fragment change → 0 here (C14). The safe-renderer use is recorded
inside F4, not as family membership. Do not inherit.

### J4 — `subsystem-clear-lifecycle` (checked, no surface)

No `register_subsystem_clear` row here and no ledger lifecycle (the
scope lock lives and dies with its scope dict; F3 lifetime). Posit a bus
change → 0 here (C15). Do not inherit.

### J5 — sync twin for `scope_session_lock` (rejected)

Considered: a sync acquisition twin for sync-bridge callers. Contract
difference: the lock serializes multiplexed operations sharing one event
loop; the bridge only ever sees per-request scopes whose lock is created
and awaited on that request's own loop, while long-lived WebSocket scopes
only reach the native async body — a sync twin would serialize nothing
(the bridge has no shared loop to serialize on) and would need its own
blocking primitive with different cancellation semantics. One async
helper is the complete surface. Trigger: a multiplexed scope reaching a
sync path. Durable home: `scope_session_lock` docstring (already carries
the loop paragraph).

## Defects

None meeting the bar (a defect names the contract row it breaks, a
feasible project shape under supported public API, and the wire or
configuration input that reaches it). Three observations were driven to a
verdict and are NOT defects:

1. **`login_supported` answers `True` for a non-`Transport` argument**
(`is not` never raises). Callers always pass the classifier's output;
a garbage carrier is a programming error, not wire input, and no
contract row requires validation there (`require_session` is the
hostile-carrier path and it contains — F4). Not routed.
2. **`BaseException` containment wraps `KeyboardInterrupt`/`SystemExit`
at the diagnostic reads** (e.g. `classify_transport`'s `isinstance`
guard). Package-wide fail-closed diagnostics discipline (same shape in
[utils/permissions.py][utils-permissions], [exceptions.py][exceptions]);
the lock-acquire path deliberately re-raises cancellation/quit signals,
so the async teardown contract is preserved where it matters. Changing
the read guards is a cross-cutting decision for a family item, not this
file's defect. Not routed.
3. **The sync-bridge loop caveat is prose, not a runtime check.**
Enforcement lives at the call sites by construction (per-request scopes
vs multiplexed scopes); a runtime loop-identity assertion would add a
check to a path whose single-loop property comes from the caller shape.
Not routed.

A pre-existing-failure check is owed and done: no test was run for this
item (per the dispatch: NO shared-tree pytest), so no failure predates or
blocks it; every probe created passes (72/72).

## Pending execution

None. No `execution-deferred` proof exists. Every finding's claim is
discharged by one of three executed or static kinds: (a) the three
read-only probes above (72 checks, `execution-verified`, commands
recorded in `### Challenges`; rerun verbatim to reproduce); (b) a single
spanning read of one literal/flag/call-arg tuple; (c) grep-verified
absence over the 397-line target (no boundary spelling, no lease, no
`describe_value`, no bus row, no second classifier). Ordering and async
behavior beyond (a)–(c) is pinned by the pre-existing oracles named as
structural gates, which this zero-edit item neither weakens nor needs to
re-run. The final suite gate belongs to the plan's gate item, not this
file item. No workspace copy was needed (nothing mutates); no `prove_failability.py`
run was owed (zero-edit file item; gates are pre-existing oracles, and
the dispatch barred shared-tree pytest).

## Judgment

Zero-edit file item. 25 top-level statements / 13 rule-bearing
definitions enumerated, all homed: two reused indexed families (F1
`soft-dependency-require-guard` as the channels twin member site incl.
the floor single-siting proof; F6 `auth-sessions-privacy-omission` as
the definition site confirming the `auth/__init__.py` file-local row),
six indexed families checked with no surface and not inherited
(C12–C18), four file-local rows (F2 classification, F3 scope lock, F4
pre-check + label with a nested `_safe_class_name` rejection, F5
capability answers) each with its proving challenges, five rejections
with difference + trigger + durable home (J1–J5). This file's relation
to `ws-connection-actor-state` is settled: separate session surface
(outer-lock owner), not a lessee — the lessee is
[auth/mutations.py][auth-mutations]`::_channels_logout`. No defects, no
pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `2783292f78c5504fed976cfcfd44807e59937ab1`:
`git diff <baseline> -- django_strawberry_framework/auth/sessions.py
docs/dry/dry-file-auth__sessions.md` empty — target CLEAN. Target blob
`fad7feb883a3675710a55d71642b309e55f64104` matches the working tree,
`HEAD:django_strawberry_framework/auth/sessions.py`, and HEAD `9031cb3d`.
The artifact itself (`docs/dry/dry-file-auth__sessions.md`) is a new
untracked file, the item's only output. Probe scratch lives at
`docs/dry/temp-tests/dry-file-auth__sessions/` (`probe_softdep.py`
23 checks, `probe_privacy.py` 18 checks, `probe_transport.py` 31 checks;
all `execution-verified`, 72/72). `uv run ruff format` /
`uv run ruff check --fix` run scoped to that scratch dir only (probes
re-run green afterwards); no package file formatted. Concurrent dirt
listed in the dispatch (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus
sibling untracked `dry-file-*.md` artifacts and sibling
`temp-tests/dry-file-auth__mutations/` probes were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no
row from this item.

## Independent verification (Worker 2)

Own trace, derived before reconciling with `## Findings` (AST + text over the
pinned blob `fad7feb883a3675710a55d71642b309e55f64104`, plus first-hand reads
of the lessee, twin, owner, consumer, and oracle sites named below). Scratch:
`docs/dry/temp-tests/dry-file-auth__sessions-w2/w2_rederive.py` (42/42 green,
read-only, static — no Django import, no DB, no source mutation); W1's three
probes re-run verbatim in the shared tree (read-only scripts, not pytest):
23/23 + 18/18 + 31/31 = 72/72 green.

### Own rule derivation (counts are authoritative definitions only)

- **R1 soft-dep guard (member site).** `require_channels` + `_CHANNELS_INSTALL_HINT`.
  Hint reword forces 1 (own hint; router's unaffected); floor bump forces 1 in
  source (`CHANNELS_FLOOR`; packaging row co-moves). Owner:
  [utils/imports.py][utils-imports]`::require_optional_module` (indexed).
  Twin member confirmed first-hand:
  [routers.py][routers]`::require_channels` is the same single-`return`
  delegate with a router-keyed wording; the two wordings differ; zero bare
  `4.3` literals in either file. Agree with F1.
- **R2 transport classification (file-local).** `Transport` + `classify_transport`.
  4th scope type forces 1 (enum + classifier move together); sniff-before-`isinstance`
  forces 1 (adapter `__getattr__` rationale in docstring). Owner: this module
  (narrowest owner every consumer already imports). Consumers by call:
  [auth/mutations.py][auth-mutations] prologues + both critical-section arms.
  Agree with F2.
- **R3 per-scope session lock (file-local).** `_SCOPE_LOCK_KEY` +
  `_SCOPE_LOCK_MESSAGES` + `_require_mutable_scope` + `scope_session_lock`.
  Reentrant/process-global rework forces 1 (helper + messages; invariant-12
  oracle forbids the registry); key rename forces 1. Owner: this module
  (auth-boundary lock ownership; scope-dict lifetime, no bus row). Agree with F3.
- **R4 missing-session pre-check + hostile label (file-local).** `require_session` +
  `_safe_transport_label`. Reword forces 1; label-fallback change forces 1
  (nested rejection vs `::_safe_class_name` holds: class renderer reads
  `__name__`/`__qualname__` off a class; this helper reads `.value` off a
  `Transport` carrier with a str fast path — different input contracts).
  Owner: this module. Agree with F4 + nested rejection.
- **R5 engine capability answers (file-local).** `uses_signed_cookie_sessions` +
  `login_supported` + `logout_supported`. New engine kind forces 1
  (`issubclass` shape); allow-WebSocket-login forces 1 (`login_supported`
  only). Engine expression owned outside:
  [utils/sessions.py][utils-sessions]`::session_store_class` (other caller
  [consumers.py][consumers]`::_refreshed_actor` instantiates it — read vs
  instantiate, same resolver; verified in both bodies). Owner of the answers:
  this module. Agree with F5.
- **R6 privacy omission (indexed file-local row, definition site).** Clause lives
  in this module's docstring (verified verbatim: NOT re-exported, both
  manifests named); enforced at [auth-init][auth-init] (exactly four factories,
  no sessions names, verified by AST); this module defines no `__all__`;
  package root imports no auth; `utils/sessions.py` top-level imports stay
  cycle-neutral (Django imports function-local). Challenge C11 forces 1
  (sessions definition; manifest row follows). Agree with F6; index row at
  `auth/__init__.py` needs no change.

### Relation to `ws-connection-actor-state` (verified first-hand)

Separate surface, not a member: the target carries zero `actor_lease` /
`actor_transition` hits (grep-verified). The lease owner is
[utils/sessions.py][utils-sessions]`::actor_lease`; the ONE dual-holding site
is [auth/mutations.py][auth-mutations]`::_channels_logout` (scope lock OUTER,
lease INNER — read at both `async with` lines, order prose verified verbatim
at the lessee docstring and the lease-owner module docstring). C13 forces 0
here. W1 J1 is correct; no file-local row may inherit the lease.

### Relation to `soft-dependency-require-guard` (twin member — yes)

Confirmed above (R1): this module is the channels twin member site alongside
the router, same primitive, own hint. W1 F1 membership is correct.

### Enumeration (member-by-member vs own AST count)

Own `ast.Module.body` count: **25** (1 docstring + 11 imports + 3 assigns + 1
class + 9 functions of which 1 async) — matches W1. Rule-bearing: **13**
(1 enum + 9 functions + 3 constants) — matches. Rows 0–24 homed as claimed:
0 projection (docstring), 1–11 consumers-by-import, 12 F1, 13–14 F3, 15–17 F2
(+16 also F1 call), 18–19 F4, 20–21 F3, 22–24 F5. No member unassigned; no
second classifier, lease, tail, bus row, or boundary worker in the target
(all zero-hit, re-verified). Agree.

### Roles, counts, oracles

Definition/consumer/oracle/projection tags re-checked per finding — agree on
all six. Oracles never read the owner (lock test spells raw key bytes;
capability tests assert bare booleans; hint tests match the floor string
without importing it; failure tests match substrings). No oracle rewritten.
`tests/auth/test_sessions.py` (824 lines, 50 tests) + live sessionless rows +
router hint pin + governance floor pins are the pre-existing structural gates
at their correct tiers (package tier for hostile/containment rows unreachable
from the wire; live tier for sessionless login/logout). Agree.

### Equivalence (principle 8) + zero-edit

Observable behavior preserved trivially: item-scoped diff vs
`2783292f78c5504fed976cfcfd44807e59937ab1` for the target is empty (exit 0;
baseline blob = HEAD blob = worktree blob = `fad7f...4104`), confirmed
first-hand. No consolidation inside a file item; nothing to prove equivalent
beyond the untouched tree. W1's probe blocks (classification outcomes,
hostile containment, pre-check pass/raise, success-path purity, key bytes,
reuse, independence, immutability/corruption loudness, no-global-registry,
capability truth tables incl. subclass engine) pin the behavior the oracles
guard. Agree.

### Rejections J1–J5

Each carries contract difference + trigger + durable home: J1 (lease vs
session lock; trigger = acquiring/ordering against the lease; home = lease
docstring + lessee docstring); J2–J4 (checked, no surface — zero-hit
mechanisms with C12/C14/C15 zero-counts and do-not-inherit; trigger implicit
in a future surface addition, the established file-item shape); J5 (sync twin
rejected — different cancellation/loop contract; trigger = multiplexed scope
reaching a sync path; home = helper docstring). Fingerprints: all 13 W1-cited
blobs re-hashed, all match (target, utils-imports, routers, test-sessions,
governance, pyproject, utils-permissions, auth-mutations, utils-sessions,
exceptions, consumers, auth-init, test-auth-api). Negative controls: probe
assertions fail on bypass (distinct-wordings, absent-literal, missing/
lifespan/foreign/hostile, immutable/corrupted/independence, subclass/
signed-WS); no `prove_failability.py` workspace run — owed nothing here
because no new gate is introduced (gates pre-exist and stay green; the
dispatch barred shared-tree pytest; the suite proof belongs to the plan gate
item). `## Pending execution` correctly absent: every claim is discharged by
an executed read-only probe, a spanning read, or a re-verified absence; no
`execution-deferred` proof exists; sharded/Postgres cells inapplicable (no DB
in the target path; probes DB-free). Coupling: none, stated once — correct
for a zero-edit file item. Agree.

### AGENTS.md prose check

Zero production edits: formatting/lint/test-tier rules have no package-code
trigger; scratch is untracked `temp-tests/` (W2 dir only). Artifact: 10-group
`LINK DEFINITIONS` block present, reference-style links, `path::Symbol`
citations; the two numeric refs (`statements 2–4`, lessee `async with` lines)
sit inside a `docs/dry/dry-*.md` scratchpad artifact where raw numbers are
permitted. No `feedback.md` mention, no `pragma: no cover`, no CHANGELOG
touch, no process provenance in code. No violation.

### Defects (Worker 2)

None. W1's three driven-to-verdict observations concurred: (1) non-`Transport`
arg to `login_supported` is a programming error, hostile-carrier path covered
by F4; (2) `BaseException` read-guards are package-wide fail-closed
discipline with cancellation preserved at `acquire`; (3) loop-caveat
enforcement-by-construction at call sites. `auth/queries.py` omission shape
re-checked (zero sessions/classify/Transport references; nullable-actor
return) — consistent with the cited contract, no gap. No `(Worker 2)` entries
added to `## Defects`.

### Judgment (Worker 2)

`Status: verified`, no pending execution. Zero-edit file item: 25/13
enumerated and homed, six axes discharged, C1–C18 counts confirmed, J1–J5
rejections adequate, fingerprints all match, diff empty, no defects.

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
[consumers]: ../../django_strawberry_framework/consumers.py
[debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[keyset]: ../../django_strawberry_framework/keyset.py
[rest-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[routers]: ../../django_strawberry_framework/routers.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py

<!-- tests/ -->
[test-auth-sessions]: ../../tests/auth/test_sessions.py
[test-governance]: ../../tests/test_ci_governance.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->
[accounts-schema]: ../../examples/fakeshop/apps/accounts/schema.py
[test-auth-api]: ../../examples/fakeshop/test_query/test_auth_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
