# DRY review: `utils/sessions.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits, zero plan edits.

## System trace

Target [utils-sessions][utils-sessions] at HEAD blob
`f0d9297c942a4915ca08ac0714cee73f6042af34` (408 lines). The worktree blob is
`21041723250de58876d95eaec14e1078a6f16a4f` (392 lines, 7 hunks, 31+/47-).
No `## Owned changes` row names this file, so the dirt entered as
concurrent-external until content attribution proved otherwise — and it did:

| Hunk (HEAD lines) | Content | Attribution |
|---|---|---|
| `ScopeSingletonMessages` docstring | four-failures prose → one-failure prose | external: rewrites the record contract the dirt below narrows |
| `ScopeSingletonMessages` fields | drops `unreadable`/`unstorable`/`uninspectable` | external: triple-field deletion no ledger row owns |
| `scope_singleton` body | removes all three `BaseException` containments; naked `scope.get`/`scope[key]=`; `truth.is_instance`/`truth.kind` | external: imports `utils/truth.py`, untracked at HEAD |
| `session_store_class` docstring+imports | reword; `describe_value` → `truth` | external: same untracked import |
| `session_store_class` checks | `isinstance`→`truth.is_instance`, `describe_value`→`truth.describe`, `type(exc).__name__`→`truth.name`, `str.__str__`→`truth.text` (moved pre-emptiness) | external: same untracked import |
| `session_store_class` import tail | `type(exc).__name__`→`truth.name` | external: same untracked import |
| `_ACTOR_STATE_MESSAGES` | drops three fields | external: follows the record narrowing |

Every hunk migrates toward `django_strawberry_framework/utils/truth.py`,
which does not exist in the HEAD tree (`git ls-tree HEAD` has no such entry;
worktree status `??`, alongside untracked `utils/lazy.py`,
`tests/utils/test_truth.py`, `tests/utils/test_lazy.py`). Nothing in the
seven hunks is ledger-owned, and nothing is mine — I made no edits. This
artifact therefore traces HEAD bytes exclusively, read via
`git show HEAD:django_strawberry_framework/utils/sessions.py`; worktree bytes
were used only to fingerprint the dirt above. Nothing tracked was touched.

What the target owns: two subjects sharing one module for one reason — each
is state or an expression the transport layer ([consumers.py][consumers]) and
the auth layer ([auth-sessions][auth-sessions] / [auth-mutations][auth-mutations])
must agree on exactly while neither may import the other:

- the `SESSION_ENGINE` → `SessionStore` resolver ([utils-sessions][utils-sessions]`::session_store_class`),
  with two callers on opposite sides of the opt-in boundary (capability read
  in auth, instantiation in consumers);
- the per-scope machinery ([utils-sessions][utils-sessions]`::scope_key`,
  `::ScopeSingletonMessages`, `::scope_singleton`) plus the connection actor
  lease ([utils-sessions][utils-sessions]`::ConnectionActorState`,
  `::connection_actor_state`, `::note_authenticated_actor`,
  `::connection_was_authenticated`, `::actor_lease`, `::actor_transition`).

Connected behavior examined (all at HEAD, fingerprints under Findings):
[auth-sessions][auth-sessions] (key/messages/lock/capability consumers),
[auth-mutations][auth-mutations]`::_channels_logout` (the one site holding
both locks; login path for the no-lease justification),
[consumers.py][consumers] (key consumer, three lease holders, engine
instantiation), [exceptions.py][exceptions] (`::_safe_type_name`,
`::describe_value` bodies, both composed by call),
[operation-lease][operation-lease] (full read, for the standing
`operation-lease-vs-actor-lease` rejection),
[operation-state][operation-state] (lifetime contrast for R12),
[utils-policies][utils-policies] F3 (the open `hostile-mapping-hardening`
contract for R2), [connection.py][connection] + [forms-inputs][forms-inputs]
(exception-tail spellings for R6), [utils-init][utils-init] (projection
line), HEAD `tests/utils/test_sessions.py` (345 lines, oracle census) and
HEAD `tests/auth/test_sessions.py` (831 lines, hostile-row + key-pin census).
Prior file artifacts for `auth/sessions.py`, `consumers.py`,
`utils/policies.py`, `utils/operation_lease.py`, and `utils/errors.py` were
used only as rejected-candidate triggers to check, per [DRY.md][dry].

## Verification

### Matrix

Each axis discharged against the target's real surface (searches named;
populations are `git grep` at HEAD unless noted).

1. **Cross-flavor policy mirroring.** The target IS the cross-flavor seam:
transport vs auth. Census: exactly four production import sites —
[auth-sessions][auth-sessions] (key, messages, singleton, resolver),
[auth-mutations][auth-mutations] (transition only),
[consumers.py][consumers] (key, lease, latch read/write, resolver), plus the
internal `actor_transition` → `actor_lease` composition. Every shared
algorithm is one body composed by call; what differs per surface is DATA
(the two `ScopeSingletonMessages` records, three key names), never a
mirrored body. The one prose mirror (lock-order stated here and at
`_channels_logout`) is two projections of one code nesting (FL9).
Discharged: no mirrored policy body.

2. **Sync/async twins.** `scope_singleton` / `connection_actor_state` are
sync by contract (await-free atomicity IS the guarantee; an async twin
would void it). `actor_transition` has no sync twin: the only sync caller
bridges the whole async logout once
([auth-mutations][auth-mutations]:949 `async_to_sync(_channels_logout)`),
so bridge-at-boundary replaces per-primitive twinning (R11). `actor_lease`
is a sync accessor returning the lock (no `await` in the lookup path).
Discharged: one body per primitive, no twin owed.

3. **Derived rather than repeated knowledge.** `SESSION_ENGINE` is read at
exactly one code site (`:223`; every other package hit is docstring/prose/
message text). The key grammar `__django_strawberry_framework_{name}__` is
spelled at exactly one code site (`:128`); all three key constants compose
by call. Provenance is written at one site (`:339`) and read at one site
(`:344`); `type(exc).__name__` tails (R6) and `str.__str__` flattening (R7)
were each censused package-wide and rejected with triggers. Discharged:
single derivation per fact, consumers by name.

4. **Inverse / round-trip pairs.** `scope_key` builds and never parses (no
split/strip surface anywhere; grep for the prefix finds only the builder
plus one literal test oracle). Latch write (`note_authenticated_actor`)
and read (`connection_was_authenticated`) are two halves of one record in
one module; `actor_transition` latches through `note_authenticated_actor`
by name rather than re-spelling the store. Discharged: pairs co-sited,
never split across modules.

5. **Contracts restated in another medium.** Media: production (target);
oracles (HEAD `tests/utils/test_sessions.py`: 11 resolver rows incl.
hostile-`str`-engine pair, 4 state rows, 1 latch row, 1 lease row, 4
transition rows; HEAD `tests/auth/test_sessions.py`: hostile-get/setitem/
isinstance/acquire rows exercising `scope_singleton` through the auth
lock); projections (module/class/function docstrings,
[utils-init][utils-init] line, glossary auth entries). Oracles are
independent: the key pin spells raw bytes literally (`"..._auth_session_lock__"`,
with a comment forbidding the constant), and every `match=` pins a
literal substring, never a record field. The grammar needs exactly one
literal pin (all keys are builder outputs, so a constant rename cannot
change bytes). Docstring load-bearing claims verified against bodies:
cycle-neutrality (top-level imports are `asyncio`/`contextlib`/
`dataclasses`/`collections.abc`/`typing` only; Django + exceptions imports
are function-local; zero `auth`/`consumers`/`routers`/`channels` imports),
opt-in rationale, lock order, hot-path cost, 3.10+ eager-`Lock`
justification. Discharged: one definition per rule across media; oracles
contradict rather than follow.

6. **Enforcement by omission.** Four member enumerations, each closed:
(a) `scope_singleton` call sites: 2/2 pass messages, mechanically (required
dataclass fields — a third site cannot forget a wording); (b) scope-key
sites: 3/3 via the builder (grammar spelled once); (c) lease holders: 4/4
hold across their critical section — transport checkpoints
([consumers.py][consumers]:869, :984, per the verified File `consumers.py`
artifact C2/C3), the control-frame revocation read (:1808, read under the
lease), and `_channels_logout` (:918, nested inside the session lock at
:916, nesting read at HEAD); (d) engine readers: 1/1 via the resolver.
Login takes the session lock ([auth-mutations][auth-mutations]:699) but no
lease — justified, not missing: `login_supported` refuses every WebSocket
([auth-sessions][auth-sessions]), and the Channels login arm is per-request
(`_channels_http_login_establish`), so login never runs on a multiplexed
scope. Discharged: no omission gap; every absence carries its contract
source.

### Enumeration

Instrument: `ast.Module.body` over the 408-line HEAD bytes — 20 statements
(module docstring, 6 imports, `__all__`, 12 name-bearing members). Nested
members: `ScopeSingletonMessages` (4 fields), `ConnectionActorState`
(`__slots__` + `__init__`). Every member homed; no sampling.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (opt-in rationale, lease contract, lock order, cost, atomicity) | projection (pointers owned at the bodies; claims verified in axis 5) |
| 1–6 | 6 imports (`__future__`, `asyncio`, `contextlib`, `dataclasses`, `AsyncIterator`/`MutableMapping`, `Any`) | mechanics (cycle-neutrality evidence; no rule) |
| 7 | `__all__` (10 names) | FL0 (leaf manifest; every name defined here) |
| 8 | `scope_key` | FL1 (grammar owner) |
| 9 | `ScopeSingletonMessages` | FL2 (record-shape owner) |
| 10 | `scope_singleton` | FL3 (singleton-body owner) |
| 11 | `session_store_class` | FL4 (resolver owner) |
| 12 | `_ACTOR_STATE_SCOPE_KEY` | FL1 (declaration by call) |
| 13 | `_ACTOR_STATE_MESSAGES` | FL2 (per-surface data) |
| 14 | `ConnectionActorState` | FL5 (record owner) |
| 15 | `connection_actor_state` | FL5 (get-or-create by call) |
| 16 | `note_authenticated_actor` | FL6 (latch write) |
| 17 | `connection_was_authenticated` | FL6 (latch read) |
| 18 | `actor_lease` | FL7 (transport-side accessor) |
| 19 | `actor_transition` | FL8 (auth-side context manager); its order half is FL9 |

Ten file-local rows (FL0–FL9); zero new families; zero adoptions; twelve
rejections (R1–R12) with contract difference + trigger + home.

### Challenges

Each rule, changes posited on its variation axes; the count is authoritative
definitions only (consumers, oracles, projections listed, never counted).
Every row ends in its home.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | FL1 grammar | rename the `__django_strawberry_framework_` prefix | **1** (`scope_key` body; 3 constants + 1 literal oracle follow) | file-local |
| C2 | FL1 population | add a fourth scope key | **0** existing (new declaration by call) | file-local |
| C3 | FL2 record | add a fifth failure mode | **1** shape (record; both data sites must answer — mechanical) | file-local |
| C4 | FL3 containment | drop or reword one arm | **1** body (+ record shape + 2 data sites as the coupled triple) | file-local |
| C5 | FL4 resolver | new engine scheme or validation | **1** (resolver; read + instantiate callers follow) | file-local |
| C6 | FL4 timing | cache the engine at import | **1** (breaks the call-time oracles that pin `override_settings`) | file-local |
| C7 | FL5 record | add a third state field | **1** (record + accessors; `__slots__` keeps it fixed) | file-local |
| C8 | FL6 latch | make provenance clearable | **1** (write half; read half + carve-out oracles follow as consumers) | file-local |
| C9 | FL7 access | wrap the lease in a context manager | **1** (accessor; 4 holders follow; hot-path cost stated) | file-local |
| C10 | FL8 timing | latch after the body instead of before | **1** (CM; fail-closed oracles reject) | file-local |
| C11 | FL9 order | swap outer/inner | **1** code site (`_channels_logout` nesting; 2 prose projections follow) | file-local |
| C12 | R8 locks | merge the two locks into one | refused (deadlock: non-reentrant, one site holds both; sections disjoint) | rejected |
| C13 | R6 tails | hostile metaclass reaches a caught exception | unfired at HEAD (would force 3 sites: here ×2 + auth ×1 — the trigger) | rejected |
| C14 | indexed families | `one-sync-boundary`, `sealed-execution-queryset`, `awaitable-refusal-and-disposal`, `subsystem-clear-lifecycle`, `soft-dependency-require-guard` | **0** here each (zero `sync_to_async`/queryset/awaitable/clear-bus/soft-guard surface; grep-verified) | no surface — do not inherit |

No read-only probe was needed: every count above is decided statically
against HEAD bytes (definition counts, import census, key/reader/holder
censuses, oracle-text reads), so no `docs/dry/temp-tests/` experiment was
run. A probe against the live tree would execute worktree (migrated) bytes,
not the HEAD bytes this item traces, and prove nothing about them. All
behavioral proof below is therefore `static-reviewed`.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved its home. `Migration: none` throughout
(zero-edit item) — stated once here, not per row. `Coupling: none`
throughout (file item consolidates nothing) — likewise stated once, except
the C4 coupled triple which is noted inside FL3.

### FL0 — leaf manifest (file-local)

- **Contract + variation.** `__all__` names the 10 public symbols, every
one defined in this module. Varies per symbol only.
- **Sites + roles.** *Definition*: `__all__` (:104–115). *Oracles*: none
(a manifest omission is review-visible, not behavior).
- **Challenges.** C2-shape: a new public helper gains one row here.
- **Owner + lifetime.** This module. No stored derivation.
- **Behavioral proof.** `static-reviewed` (10/10 names resolve to module
definitions; no re-export).
- **Freshness.** Target as header.

### FL1 — `utils-sessions-scope-key-grammar` (file-local)

- **Contract + variation.** Every package scope key is namespaced
`__django_strawberry_framework_{name}__`, built by `scope_key`, never
hand-spelled. Varies in the `name` argument only.
- **Sites + roles.** *Definition*: `scope_key` (:118–128; the grammar is
spelled at exactly one code site — package-wide prefix grep returns only
this line). *Declarations by call*: `_ACTOR_STATE_SCOPE_KEY` (:270),
[auth-sessions][auth-sessions]`::_SCOPE_LOCK_KEY`,
[consumers.py][consumers]`::_REVALIDATED_AT_SCOPE_KEY`. *Oracle*: the one
raw-literal pin (auth lock bytes), which transitively pins the builder's
prefix for all keys.
- **Challenges.** C1 → 1; C2 → 0 existing.
- **Owner + lifetime.** This module (grammar owner). Keys live as long as
the scope dict entries under them; the package never clears them.
- **Behavioral proof.** `static-reviewed` (single spelling + three
by-call declarations + one literal oracle). Rejects "a fourth key with a
novel prefix" and "a hand-spelled key drifting from the builder".
- **Freshness.** Target as header; [auth-sessions][auth-sessions]
`fad7feb8`; [consumers.py][consumers] `936210e2`.

### FL2 — `utils-sessions-singleton-messages` (file-local)

- **Contract + variation.** The four consumer-facing `scope_singleton`
failures travel as a frozen `ScopeSingletonMessages` record, one per call
site; the record's required fields mechanically force every site to answer
every failure mode. `corrupted` is a format template receiving `actual`.
Varies in wording per surface only — never in shape per site.
- **Sites + roles.** *Definition (shape)*: `ScopeSingletonMessages`
(:131–149). *Data*: `_ACTOR_STATE_MESSAGES` (:272–280),
[auth-sessions][auth-sessions]`::_SCOPE_LOCK_MESSAGES`. Both `corrupted`
wordings verified to carry `{actual}` (2/2, read not assumed).
- **Challenges.** C3 → 1 shape (+ 2 data co-movers, mechanical).
- **Owner + lifetime.** This module (record shape); wordings owned by
their surfaces. No stored derivation.
- **Behavioral proof.** `static-reviewed` (dataclass-required-fields
mechanics + both wordings read). Rejects "a new failure mode answered at
one site and forgotten at the other".
- **Freshness.** Target as header; [auth-sessions][auth-sessions]
`fad7feb8`.

### FL3 — `utils-sessions-scope-singleton` (file-local)

- **Contract + variation.** The one per-scope lazy get-or-create: no
`await` between read and store (atomic on the event loop — two
multiplexed operations cannot mint two objects), and a corrupted slot is
a typed `ConfigurationError`, never a silent replacement. Read, store,
and type test are each contained because the scope is a mapping other
software also writes to. Varies in `factory`/`expect`/messages per site
only — never in algorithm per site.
- **Sites + roles.** *Definition*: `scope_singleton` (:152–199).
*Composed by call*: `::_safe_type_name` for the `corrupted` tail (R5).
*Call sites*: `connection_actor_state` (:324–330),
[auth-sessions][auth-sessions]`::scope_session_lock` (:319–325).
*Oracles*: lazy-create/reuse, serialization, and the hostile
get/setitem/isinstance/acquire rows (exercised through the auth lock).
`factory()` raising propagates raw — correct, because both real
factories are package-owned constructors that cannot raise (a guard no
real path reaches is the wrong guard). Explicit `None` is absent by
design (keys are package-namespaced; no second meaning exists).
- **Challenges.** C4 → 1 body; the body + record shape + 2 data sites
move as a documented triple on any failure-mode change (Coupling noted,
not fixed — file item).
- **Owner + lifetime.** This module (singleton body). Stored derivation:
the scope-dict slot, owned by the scope, created on first use, never
cleared by the package.
- **Behavioral proof.** `static-reviewed` (one body, two by-call sites,
hostile-row oracles). Rejects "two operations mint two locks" and "a
corrupted slot is silently overwritten".
- **Freshness.** Target as header; [auth-sessions][auth-sessions]
`fad7feb8`; [exceptions.py][exceptions] `e06b0b7f`.

### FL4 — `utils-sessions-engine-resolver` (file-local)

- **Contract + variation.** The ONE `settings.SESSION_ENGINE` →
`SessionStore` expression for both callers: settings read at CALL time
(`override_settings` honored), non-string/empty/unresolvable engines
rejected as typed `ConfigurationError`, a hostile `str`-subclass engine
flattened through the base `str` slot before the emptiness check and both
interpolations, resolution through Django's own `import_string` so
consumer subclasses resolve identically to shipped engines. Varies in
validation only.
- **Sites + roles.** *Definition*: `session_store_class` (:202–263; the
only code read of `settings.SESSION_ENGINE` package-wide).
*Composed by call*: `::describe_value` for the non-string tail (R5).
*Callers*: [auth-sessions][auth-sessions]`::uses_signed_cookie_sessions`
(reads — capability question), [consumers.py][consumers]`::_refreshed_actor`
(instantiates — revalidation reload). *Oracles*: the 11 resolver rows
incl. the hostile-`__format__`/`__repr__` engine pair.
- **Challenges.** C5 → 1; C6 → 1.
- **Owner + lifetime.** This module (cycle-neutral host: both Django
imports function-local, so the transport reaches the engine without
importing opt-in `auth`). No stored derivation (call-time read).
- **Behavioral proof.** `static-reviewed` (single expression, two
follow-by-call callers, hostile-engine oracles). Rejects "a raising
`__format__` replaces the typed error" and "a cached engine ignores
`override_settings`".
- **Freshness.** Target as header; [auth-sessions][auth-sessions]
`fad7feb8`; [consumers.py][consumers] `936210e2`;
[exceptions.py][exceptions] `e06b0b7f`.

### FL5 — `utils-sessions-actor-state-record` (file-local)

- **Contract + variation.** One connection's lease + provenance arrive
together in ONE record under ONE scope key, so a caller can never hold a
lease from one slot while reading provenance from another. `__slots__`
keeps the shape fixed (a typo is `AttributeError`, not a silent orphan).
The `asyncio.Lock` is constructed eagerly — safe because it binds its
loop on first contention (3.10+ floor), which is what keeps the
get-or-create await-free and atomic. Varies in fields only.
- **Sites + roles.** *Definition*: `ConnectionActorState` (:283–312) +
`connection_actor_state` get-or-create (:315–330, via FL3 by call).
Zero direct constructions package-wide (the class travels only as
`factory=`/`expect=`). *Oracles*: init/slots/reuse/isolation rows.
- **Challenges.** C7 → 1.
- **Owner + lifetime.** This module. Stored derivation: the scope-dict
slot under `_ACTOR_STATE_SCOPE_KEY`, scope-lifetime (GC'd with the
connection; never revoked — R12 for why no lease wraps it).
- **Behavioral proof.** `static-reviewed` (one record, one accessor,
zero bypass constructions). Rejects "lease and provenance created
independently" and "a second state object per scope".
- **Freshness.** Target as header.

### FL6 — `utils-sessions-auth-provenance-latch` (file-local)

- **Contract + variation.** Whether a connection has EVER carried an
authenticated actor: write-once in meaning (only ever set, never
cleared), which is what makes it provenance instead of a second copy of
`scope["user"]` — a package-owned logout replaces the live actor with
`AnonymousUser`, so the live value cannot answer the ever-question, and
reading it would let the anonymous carve-out skip revalidation of frames
an admitted operation still wants to send. The latch keeps the carve-out
(zero session reads for a genuinely anonymous socket) while denying it
to an identity change, and makes the post-transition refusal read-free.
- **Sites + roles.** *Definition*: `note_authenticated_actor` (sole
writer, :333–339) + `connection_was_authenticated` (sole reader,
:342–344); attribute touched at exactly those two code sites plus
`__init__` default. *Writers by call*: `actor_transition` (latch-inside-
lease) and the transport's observed-authenticated site. *Readers by call*:
both revalidation checkpoints ([consumers.py][consumers]:1112, :1124).
- **Challenges.** C8 → 1.
- **Owner + lifetime.** This module (latch halves); the bit lives in the
FL5 record. No separate stored derivation.
- **Behavioral proof.** `static-reviewed` (single writer/reader,
attribute census closed). Rejects "a logged-out socket revalidates as
always-anonymous" and "provenance cleared by a later read".
- **Freshness.** Target as header; [consumers.py][consumers] `936210e2`.

### FL7 — `utils-sessions-actor-lease-access` (file-local)

- **Contract + variation.** The transport side of the shared primitive:
returns the bare `asyncio.Lock` to be held with `async with` across the
ENTIRE validate/commit/send sequence — holding it through the
asynchronous ASGI send is the load-bearing part, since releasing after
validation would let a same-connection logout complete underneath an
already-authorized frame. Deliberately NOT wrapped in an
`asynccontextmanager` (a wrap would build a generator + manager per
acquisition on the outbound hot path) and deliberately NOT re-entrant (a
nested checkpoint would be a control-flow bug; deadlock beats silent
authorization).
- **Sites + roles.** *Definition*: `actor_lease` (:347–378). *Holders*:
[consumers.py][consumers]:869, :984 (checkpoints), :1808 (control-frame
revocation read), and `actor_transition` internally (:405).
- **Challenges.** C9 → 1.
- **Owner + lifetime.** This module (accessor); the lock lives in the
FL5 record. No stored derivation.
- **Behavioral proof.** `static-reviewed` (one accessor, four holders,
hot-path rationale stated). Rejects "a second lock object per scope" and
"validation released before send".
- **Freshness.** Target as header; [consumers.py][consumers] `936210e2`.

### FL8 — `utils-sessions-actor-transition` (file-local)

- **Contract + variation.** The auth side of the same primitive, named
for what it means there: owns the lease across the native teardown /
establishment itself (the interval where durable session and scope actor
disagree), so no checkpoint may authorize anything — by read or from the
positive-window cache — anywhere inside it. `was_authenticated` (read
before the body replaces it) latches INSIDE the lease and BEFORE the body
runs, unconditionally — so the first post-block checkpoint sees an
authenticated-ever connection even when the teardown failed part way
(fail-closed direction). Exclusion runs both ways: entering blocks until
any protected frame already being written has left.
- **Sites + roles.** *Definition*: `actor_transition` (:381–408).
*Latches by call* through FL6 (`note_authenticated_actor`, never a
re-spelled store). *Sole holder*:
[auth-mutations][auth-mutations]`::_channels_logout` (:918).
- **Challenges.** C10 → 1.
- **Owner + lifetime.** This module. No stored derivation.
- **Behavioral proof.** `static-reviewed` (one CM, one holder, latch
timing read). Rejects "a checkpoint authorizing mid-teardown" and "a
failed teardown leaving the socket anonymous-ever".
- **Freshness.** Target as header; [auth-mutations][auth-mutations]
`d1a59c44`.

### FL9 — `utils-sessions-lease-order` (file-local)

- **Contract + variation.** The scope session lock is OUTER, the actor
lease INNER. Exactly one site holds both
([auth-mutations][auth-mutations]`::_channels_logout`: lock at :916,
lease at :918); nothing holding the lease ever asks for the session lock
(checkpoints are pure transport, never enter auth), so the order is
total and acyclic with one rule to remember.
- **Sites + roles.** *Definition (code)*: the `_channels_logout`
nesting (enforced once). *Projections*: this module's docstring order
clause + the `_channels_logout` docstring clause (prose restating one
nesting, never owning — DRY vocabulary). Positing a second primitive
joins it to this order rather than duplicating the rule.
- **Challenges.** C11 → 1 code site (+ 2 prose co-movers).
- **Owner + lifetime.** Stated here, enforced at `_channels_logout`. No
stored derivation.
- **Behavioral proof.** `static-reviewed` (nesting read at HEAD;
holder censuses closed on both primitives). Rejects "a second dual-hold
site with the reverse order".
- **Freshness.** Target as header; [auth-mutations][auth-mutations]
`d1a59c44`.

### R1 — `utils-sessions-vs-operation-lease` (rejected, CONVERGE)

[operation-lease][operation-lease]`::OperationLease` is a revocable handle
answering payload-or-`None` after its scope ends — no acquire/release,
never spans an await. `actor_lease` is an `asyncio.Lock` held with
`async with` across validate/commit/send and teardown. Same word, disjoint
verbs: the actor lease serializes actors in time; the operation lease
revokes readability at scope end. CONVERGE with verified
`operation-lease-vs-actor-lease` on fresh HEAD-byte evidence (both bodies
re-read; [operation-lease][operation-lease] `10c164b7`). Trigger re-checked
unfired: neither side gained the other's verb. Durable home: the
operation-lease artifact R-LOCK + owner docstrings.

### R2 — `utils-sessions-vs-hostile-mapping` (rejected, fresh)

Considered: `scope_singleton`'s read/store/inspect containment as a member
of open `hostile-mapping-hardening`. Contract difference: that family's
triple is materialize-once into a plain dict + string key-guard +
unknown-vocabulary rejection over a deployment-supplied mapping
([utils-policies][utils-policies] F3, verified run 5). Here live-scope
mutation IS the point (a materialized copy could not publish the created
singleton back to the scope), the key is package-built (no key guard or
vocabulary exists to check), and each arm reports a per-surface typed
message rather than the triple's rejections. Same `try/except` token,
different rule. Trigger: the family item scoping read-containment as a
member shape, or a scope read needing materialize semantics. Durable
home: this row + the family's open item. Freshness:
[utils-policies][utils-policies] `8c881c0a`; family population
([conf.py][conf] `c6ad46aa`, [types-base][types-base] `dda91365`) cited via
the verified policies F3.

### R3 — `utils-sessions-vs-shared-except-guard` (rejected, CONVERGE)

Considered: one shared `except BaseException → ConfigurationError` driver
for the three `scope_singleton` arms (plus the two `session_store_class`
`except` tuples). Standing J1 trigger-check (`_request_body.py` J1,
re-checked at join_taxonomy, nested_fetch, nested_planner — all rejected):
each arm carries a distinct failure meaning (unreadable vs unstorable vs
uninspectable vs corrupted) with per-surface wordings that a driver would
need passed in anyway — which is exactly the FL2 record already here. The
`BaseException` breadth (notably swallowing even `KeyboardInterrupt`-shaped
raisers) is justified per arm by await-freedom: no genuine cancellation
can surface where no `await` exists, so every caught raiser is the hostile
scope by elimination. Trigger: two arms converging on one message +
meaning. Durable home: the standing J1 line.

### R4 — `utils-sessions-vs-exact-type-gate` (rejected, trigger-check)

Considered: the `isinstance(value, expect)` corrupted-slot test as a
member of the shared exact-type population (standing J2). Contract
difference: this test is polymorphic BY DESIGN — a lock/str subclass that
still honors the protocol still serializes / still reads — while the
exact-type gate exists precisely to refuse subclasses. An exact-type gate
here would corrupt-slot-reject a working lock subclass. Trigger: a
corrupted-slot escape via a subclass honoring the test but breaking the
protocol. Durable home: this row.

### R5 — `utils-sessions-safe-render-composition` (rejected, CONVERGE)

Considered: the `corrupted` tail (`::_safe_type_name`) and the non-string
tail (`::describe_value`) as renderers defined here. They are composed BY
CALL from [exceptions.py][exceptions] — no second renderer is defined, no
label grammar re-spelled. CONVERGE with verified File `exceptions.py` C1
(kind-name policy, `::_safe_type_name`) + C3/F1 (fragment spelling,
`::describe_value`) compose-by-name on fresh HEAD-byte evidence
([exceptions.py][exceptions] `e06b0b7f`, both bodies re-read).
Same-direction precedent only: `errors-safe-renderer-composition` (the
`_unprintable`/`_safe_text` pair's converge — a different composition
pair, not this one). Trigger: an inline kind-label or `got`-tail rendering
appearing here. Durable home: the exceptions owner + this row.

### R6 — `utils-sessions-exception-tail-spelling` (rejected, fresh)

The two `type(exc).__name__` tails (:233, :262) spell caught-exception
labeling raw, while 14 sites in 6 files route the same position through
`_safe_type_name` ([connection.py][connection] ×5, [forms-inputs][forms-inputs]
×2, serializer_converter ×1, types/base ×1, types/finalizer ×4, directives
×1). Package census: 9 raw sites in 6 files vs 14 safe sites in 6 files —
and [forms-inputs][forms-inputs] mixes BOTH spellings in one file (:347 raw,
:459/:474 safe), which is what interchangeability looks like, not a felt
rule. Census basis: only sites rendering the caught exception's CLASS NAME
as a rejection tail count — `permissions.py:662` (`_safe_type_name` of
`exc.value`, a carried attribute's type) and `schema.py:1078`
(`describe_value(exc)`, the instance rendered as a rejected value) are
different positions and excluded on that basis. Contract difference:
untrusted-VALUE rendering (hostile `__name__`
in scope per the `_safe_type_name` docstring; `describe_value`'s stated
scope is values, explicitly not exceptions) vs caught-EXCEPTION labeling
(raw half of a mixed idiom; no contract source establishes hostile
exception metaclasses as in scope for these members). Positing the merge
anyway would be a threat-model ruling, not a consolidation — and per
[DRY.md][dry] axis 6, an unestablished rule is a rejection with a trigger,
never a finding. Trigger: a hostile metaclass reaching any caught-
exception tail, or the maintainer ruling metaclass hostility in scope — then converge
all tails here (×2) plus [auth-sessions][auth-sessions]:371 onto the safe
renderer. Durable home: this row. Freshness: [connection.py][connection]
`4894f90f`; [forms-inputs][forms-inputs] `6418753d`.

### R7 — `utils-sessions-str-slot-flatten` (rejected, fresh)

Considered: one shared hostile-`str` flattening helper over the 20+-site
`str.__str__` population ([exceptions.py][exceptions] ×9,
[types-base][types-base]/relay/definition, scalars, auth, here). Contract
difference: this site is a CONTENT-preserving normalization (the exact
deployment string must survive into the emptiness check, the import path,
and the `{engine!r}` tail), while the population majority renders LABELS;
and every site keeps its own failure contract (straight-line here,
nested-fallback in `_safe_type_name`, try/except in
`_safe_transport_label`). A helper would own the one-line primitive while
relieving no change obligation — the primitive is a language fact, and a
change to any site's contract still moves that site alone. Trigger: a
second content-preserving settings-boundary read appearing, or the
primitive proving insufficient somewhere (all sites move together — then
it is a family). Durable home: this row.

### R8 — `utils-sessions-lock-vs-scope-lock` (rejected, fresh)

Considered: the actor lease and the per-scope session lock as one lock.
Contract difference, threefold: (a) disjoint critical sections —
revalidation validate/commit/send + actor transitions vs session
read-mutate-persist + compensation; (b) disjoint owners — transport vs
auth, structurally forbidden from importing each other, which is WHY the
shared primitive lives in cycle-neutral `utils`; (c) MERGING THEM
DEADLOCKS: both are non-reentrant and `_channels_logout` holds both
(FL9), so one lock turns the ordered nesting into self-deadlock. The
module docstring states the positive case too: two independent locks give
no ordering between the two state machines, and the lease exists because
the session lock cannot cover revalidation. C12 refused on the deadlock
alone. Trigger: the two critical sections collapsing into one state
machine. Durable home: the module docstring (already states it) + this row.

### R9 — `utils-sessions-transition-vs-bare-lock` (rejected, fresh)

Considered: one access shape for the lease — either wrap `actor_lease` in
a context manager or drop `actor_transition` to bare-lock use. Contract
difference: the auth side needs latch+teardown BUNDLING (latch-inside-
lease-before-body, unconditionally — the fail-closed timing), while the
transport side needs the RAW lock on the outbound hot path (a CM wrap
builds a generator + manager per acquisition, per protected frame).
Same lock, different access contracts; each shape is load-bearing where
it sits. Trigger: transport needing bundled latch semantics, or auth
needing bare-lock access. Durable home: the `actor_lease` docstring
(already states the cost) + this row.

### R10 — `utils-sessions-engine-vs-capability` (rejected, CONVERGE)

Considered: answering the signed-cookie capability inside
`session_store_class` (resolve + answer in one). Contract difference: the
resolver is an EXPRESSION (which `SessionStore` class), the capability is
a QUESTION (does this engine keep a server-side record) — and the second
caller proves the split load-bearing: [consumers.py][consumers] must
INSTANTIATE the class, which no boolean answer permits. The capability
composes the resolver by call and adds the `issubclass` test auth owns.
CONVERGE with the accepted File `auth/sessions.py` F5 (read-vs-
instantiate, same resolver) on fresh HEAD-byte evidence. Trigger: a third
caller needing both halves atomically. Durable home: the F5 row + this row.

### R11 — `utils-sessions-no-sync-transition-twin` (rejected, fresh)

Considered: a sync twin of `actor_transition`. Contract difference: the
transition body contains async teardown (`channels.auth.logout` is
`database_sync_to_async`), and the only sync caller bridges the WHOLE
async logout once ([auth-mutations][auth-mutations]:949) — bridge-at-
boundary, the same shape as the write pipeline's one sync body. A sync
twin would need its own bridge inside the lease hold: a second bridge
discipline for zero new callers. Trigger: a sync caller needing the
transition without the logout body. Durable home: this row.

### R12 — `utils-sessions-state-vs-operation-state` (rejected, fresh)

Considered: `ConnectionActorState` as a member of the per-operation state
machinery ([operation-state][operation-state]). Contract difference:
connection lifetime vs operation lifetime, in storage and threat alike —
the actor state lives in a scope-dict slot, GC'd with the connection,
never revoked, because its readers hold the scope itself; operation state
rides a `ContextVar`-bound lease precisely so a background task outliving
its request stops reading (and stops retaining) the completed operation.
A lease around the actor state would add revocation no reader needs.
Trigger: a scope outliving its safe-use with readers still holding it.
Durable home: this row. Freshness: [operation-state][operation-state]
`b2674a22`.

## Defects

None. The one near-miss — raw `type(exc).__name__` tails vs the safe
renderer — is R6, a rejection rather than a defect: no contract source
establishes hostile exception metaclasses as in scope for these members
(`describe_value`'s stated scope is values, explicitly not exceptions;
the spellings are a mixed idiom — 9 raw sites vs 14 safe, 6 files each —
with same-file auth on the raw side),
so the AGENTS.md defect bar (contract row + feasible shape + wire input)
is not met. Its trigger names exactly the observation that would promote
it.

## Judgment

Hub module, fully single-owned per rule: the scope-key grammar, the
singleton body + message record, the engine resolver, and the actor
lease/provenance/order cluster each count 1 on every variation axis, with
transport and auth composing strictly by call across the opt-in boundary
they must not cross by import. Ten rules stand file-local; twelve
rejections carry contract differences + triggers (five converging with
verified prior verdicts on fresh HEAD-byte evidence, seven fresh). Zero
defects, zero edits.

## Implementation (Worker-1)

No tracked changes. No production edits (file item consolidates nothing),
no test edits, no plan edits. The worktree dirt on the target (7 hunks,
`f0d9297c` → `21041723`) is concurrent-external by content attribution
(see System trace) and was left untouched. The only write is this artifact
itself (new file, untracked at write time).

## Index rows for Worker-0

| `utils-sessions-leaf-manifest` | `django_strawberry_framework/utils/sessions.py` (`__all__`, 10 names, all module-defined) | `django_strawberry_framework/utils/sessions.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-scope-key-grammar` | `django_strawberry_framework/utils/sessions.py::scope_key` (namespaced grammar, spelled once; 3 declarations by call) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/consumers.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-singleton-messages` | `django_strawberry_framework/utils/sessions.py::ScopeSingletonMessages` (4-field required record shape; 2 per-surface data sites) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/sessions.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-scope-singleton` | `django_strawberry_framework/utils/sessions.py::scope_singleton` (await-free atomic get-or-create + 4-arm containment; 2 call sites) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/sessions.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-engine-resolver` | `django_strawberry_framework/utils/sessions.py::session_store_class` (ONE engine expression; call-time read; read + instantiate callers) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/consumers.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-actor-state-record` | `django_strawberry_framework/utils/sessions.py::ConnectionActorState` (+ `::connection_actor_state`; slotted, zero bypass constructions) | `django_strawberry_framework/utils/sessions.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-auth-provenance-latch` | `django_strawberry_framework/utils/sessions.py::note_authenticated_actor` (+ `::connection_was_authenticated`; write-once latch, single writer/reader) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/consumers.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-actor-lease-access` | `django_strawberry_framework/utils/sessions.py::actor_lease` (bare-lock transport accessor; 4 holders; hot-path non-wrap) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/consumers.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-actor-transition` | `django_strawberry_framework/utils/sessions.py::actor_transition` (latch-inside-lease-before-body CM; sole holder `_channels_logout`) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/mutations.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-lease-order` | `django_strawberry_framework/auth/mutations.py::_channels_logout` nesting (session lock OUTER, lease INNER; stated at `django_strawberry_framework/utils/sessions.py` module docstring as projection) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/mutations.py` | File `utils/sessions.py` | file-local |
| `utils-sessions-vs-operation-lease` | `django_strawberry_framework/utils/sessions.py::actor_lease` (rejection recorded here; CONVERGE with verified `operation-lease-vs-actor-lease` on fresh evidence — exclusion vs revocation; trigger re-checked unfired) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/utils/operation_lease.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-vs-hostile-mapping` | `django_strawberry_framework/utils/sessions.py::scope_singleton` (rejection recorded here; fresh — live-scope mutation vs the materialize/key-guard/vocabulary triple; trigger: family scoping read-containment) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/utils/policies.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-vs-shared-except-guard` | `django_strawberry_framework/utils/sessions.py::scope_singleton` (rejection recorded here; CONVERGE with standing J1 on fresh evidence — per-arm meanings + await-freedom breadth; trigger: two arms, one message) | `django_strawberry_framework/utils/sessions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-vs-exact-type-gate` | `django_strawberry_framework/utils/sessions.py::scope_singleton` (rejection recorded here; standing-J2 trigger-check — polymorphic acceptance by design; trigger: subclass escape) | `django_strawberry_framework/utils/sessions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-safe-render-composition` | `django_strawberry_framework/utils/sessions.py::scope_singleton` (rejection recorded here; CONVERGE with verified exceptions C1 + C3/F1 compose-by-name on fresh evidence — no second renderer; trigger: inline rendering here) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/exceptions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-exception-tail-spelling` | `django_strawberry_framework/utils/sessions.py::session_store_class` (rejection recorded here; fresh — caught-exception labeling vs untrusted-value rendering, 9-raw/14-safe census; trigger: hostile metaclass or the maintainer threat-model ruling) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/auth/sessions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-str-slot-flatten` | `django_strawberry_framework/utils/sessions.py::session_store_class` (rejection recorded here; fresh — content normalization vs label rendering over the 20+-site idiom population; trigger: second content read or primitive failure) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/exceptions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-lock-vs-scope-lock` | `django_strawberry_framework/utils/sessions.py::actor_lease` (rejection recorded here; fresh — disjoint sections/owners + merge-deadlocks proof; trigger: sections collapse) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/sessions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-transition-vs-bare-lock` | `django_strawberry_framework/utils/sessions.py::actor_transition` (rejection recorded here; fresh — latch-bundling vs hot-path raw access; trigger: either side needing the other's shape) | `django_strawberry_framework/utils/sessions.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-engine-vs-capability` | `django_strawberry_framework/utils/sessions.py::session_store_class` (rejection recorded here; CONVERGE with accepted auth F5 on fresh evidence — expression vs question, instantiate-caller proof; trigger: third caller needing both) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/consumers.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-no-sync-transition-twin` | `django_strawberry_framework/utils/sessions.py::actor_transition` (rejection recorded here; fresh — bridge-at-boundary vs per-primitive twins; trigger: sync caller needing the transition alone) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/auth/mutations.py` | File `utils/sessions.py` | rejected |
| `utils-sessions-state-vs-operation-state` | `django_strawberry_framework/utils/sessions.py::ConnectionActorState` (rejection recorded here; fresh — connection lifetime vs operation lifetime; trigger: scope outliving safe-use) | `django_strawberry_framework/utils/sessions.py`, `django_strawberry_framework/extensions/operation_state.py` | File `utils/sessions.py` | rejected |

## Families

None new. Zero adoptions. Five convergences onto verified/accepted prior
verdicts (`operation-lease-vs-actor-lease`, standing J1, exceptions C1 +
C3/F1, auth F5, standing-J2 direction — their rows stand; triggers
re-checked in R1/R3/R4/R5/R10). Seven fresh rejections
(R2/R6/R7/R8/R9/R11/R12).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[consumers]: ../../django_strawberry_framework/consumers.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[operation-lease]: ../../django_strawberry_framework/utils/operation_lease.py
[operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[types-base]: ../../django_strawberry_framework/types/base.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py
[utils-policies]: ../../django_strawberry_framework/utils/policies.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Traced expectation-first: required reading, full HEAD target read
(`f0d9297c`, 408 lines), AST enumeration, worktree-vs-HEAD 7-hunk diff,
whole-package consumer grep, and the connected sites below opened before
this artifact's `## Findings`. HEAD `0c0537e2` unmoved at start; target
worktree blob `21041723` (392 lines); `git status` shows the path `M`;
item-scoped diff vs `ITEM_BASELINE=ce45eedf` on the target is empty (the
baseline stash commit already carries `21041723`), so the 7 hunks predate
the item by mechanics — content attribution below is independent of that
fact.

My trace. Enumeration instrument: `ast.Module.body` over HEAD bytes —
20 statements: module docstring, 6 imports (`__future__`, `asyncio`,
`contextlib`, `dataclasses`, `collections.abc`, `typing`), `__all__`,
`scope_key`, `ScopeSingletonMessages`, `scope_singleton`,
`session_store_class`, `_ACTOR_STATE_SCOPE_KEY`, `_ACTOR_STATE_MESSAGES`,
`ConnectionActorState`, `connection_actor_state`,
`note_authenticated_actor`, `connection_was_authenticated`,
`actor_lease`, `actor_transition`. Four rules, all owned here:

1. `SESSION_ENGINE` expression (`session_store_class`, definition).
   Consumers (2, both composing by name): `auth/sessions.py` capability
   read, `consumers.py` instantiation (function-local import). Oracles:
   `tests/utils/test_sessions.py` malformed-engine rows (independently
   spelled literals, never reading the resolver). Projections: module
   docstring, glossary auth-mutations anchor. Posited change (engine
   grammar / new failure arm): count 1.
2. Per-scope lazy singleton (`scope_singleton` +
   `ScopeSingletonMessages`, definition). Consumers (2, data not bodies):
   `auth/sessions.py::scope_session_lock` (`asyncio.Lock`),
   `connection_actor_state` (`ConnectionActorState`). Posited change
   (atomicity shape, corruption verdict): count 1 — the messages record
   is per-site data the one body reads.
3. Scope-key grammar (`scope_key`, definition). Consumers (3, all by
   name): this file's `_ACTOR_STATE_SCOPE_KEY`, auth's
   `_SCOPE_LOCK_KEY`, consumers' `_REVALIDATED_AT_SCOPE_KEY`. Posited
   change (prefix grammar): count 1.
4. Actor lease + provenance (`ConnectionActorState`, `actor_lease`,
   `actor_transition`, latch/read pair; definition). Consumers:
   `consumers.py` (3 lease sites + latch/read), `auth/mutations.py`
   (the one dual-holder). Owner I would choose: the target
   (principle 7 — transport and auth both already depend on `utils`;
   nothing here imports `auth`/`consumers`/`channels`, both Django
   imports function-local).

Matrix expectations: axis 1 — auth/transport share by design, no
mirrored policy; axis 2 — `actor_lease` (sync handle) vs
`actor_transition` (async CM) are two verbs on one lock, not twins;
axis 3 — all three scope keys derive through the builder; axis 4 — no
round-trip pair on this surface; axis 5 — docstrings/glossary are
projections, tests are oracles; axis 6 — the revalidated-at key is a
plain timestamp read/write (default `-inf`, no factory, no type gate),
so `scope_singleton` covering only 2 of 3 scope keys is a contract
difference, not an enforcement gap.

Hunk expectation (content, HEAD-vs-worktree): all 7 hunks are the
truthful-reads migration — `truth.is_instance`/`truth.kind`/
`truth.name`/`truth.describe`/`truth.text`, the
unreadable/unstorable/uninspectable arms and fields dropped,
`_safe_type_name`/`describe_value` imports replaced — and
`utils/truth.py` is absent at HEAD. Concurrent-external; a file item
traces HEAD bytes and leaves them untouched.

Reconciliation against `## Findings` (every check re-derived fresh
at HEAD bytes; agreements first, differences last):

AGREE, and independently verified: enumeration 20/20 member-by-member
exact (my AST list is identical: docstring, 6 imports, `__all__`, 12
name-bearing), every member homed, FL0–FL9 homes fit (FL9's two-file
file-local stands: ONE definition — the `_channels_logout` nesting —
plus two projections; the file-local test is definition count, and the
index row honestly carries both files); hunk attribution 7/7 (my
content map matches the System-trace table hunk for hunk;
truth-migration, `utils/truth.py` absent at HEAD, item diff vs
`ITEM_BASELINE` empty — zero-edit confirmed mechanically, not
claimed); all 11 freshness fingerprints byte-exact
(`fad7feb8`/`d1a59c44`/`936210e2`/`e06b0b7f`/`10c164b7`/`b2674a22`/
`8c881c0a`/`c6ad46aa`/`dda91365`/`4894f90f`/`6418753d`); test sizes
345/831 and the oracle census 11/4/1/1/4 re-derived exact; every cited
HEAD line re-read exact (lease holders :869/:984/:1808, latch readers
:1112/:1124, nesting :916/:918, bridge :949, login lock :699 inside
`_channels_http_login_establish`, auth singleton call :319–325,
`{actual}` 2/2, `issubclass` capability test, auth:371 trigger site);
holder/reader/writer censuses closed (lease 4, session lock 2,
transition sole caller :918, provenance write :339/read :344/init
default, zero bypass constructions, one code `SESSION_ENGINE` read
:223, one prefix spelling :128 + one literal oracle); converges R1
(bodies re-read, exclusion vs revocation), R3 (J1 text re-read:
per-arm meanings + FL2 record + await-freedom breadth; trigger
unfired), R4 (J2 text re-read: polymorphic acceptance by design —
an exact gate would corrupt-slot-reject a working lock subclass),
R10 (F5 re-read: expression vs question + instantiate-caller proof);
fresh R2 (policies-F3 triple re-read: live mutation vs
materialize/key-guard/vocabulary), R7 (33-hit `str.__str__`
population; content normalization vs label rendering), R8
(disjoint sections/owners + merge-deadlocks proof), R9
(latch-bundling vs hot-path raw access), R11 (async
`database_sync_to_async` teardown + bridge-at-boundary, only sync
caller :949), R12 (ContextVar+lease operation scope vs GC'd
connection slot); R5/R6 SUBSTANCE (below); matrix discharge on all
six axes; zero-defect call (below); no pending execution owed (all
`static-reviewed`; a live-tree probe would execute migrated bytes,
correctly refused); scaffold intact (10/10 group headers); ruff
gates vacuous-pass (`.md`-only change); AGENTS.md prose clean.

DIFFER on record accuracy only — 3 blemishes, none verdict-moving,
each reproducible below. Per the cycle's record-accuracy bar (File
`utils/errors.py` W2: `revision-needed` for verdict-neutral
blemishes), this is `revision-needed`, not `verified`: resubmission
to the SAME W1 context (no re-trace; every judgment stands; fix the
prose, keep the verdicts).

1. R5 converge pointers name the wrong bodies. `scope_singleton`
   composes `exceptions.py::_safe_type_name` (= File `exceptions.py`
   C1/R1 kind-name policy) and `session_store_class` composes
   `::describe_value` (= C3/F1 fragment spelling) — both bodies
   re-read at HEAD `e06b0b7f`, compose-by-call confirmed, count 1
   at the owner. But R5 converges with "verified File
   `exceptions.py` C2/C5" (which own `_unprintable`/`_safe_text` —
   the errors.py pair, correctly cited at errors R8) and with
   `errors-safe-renderer-composition` (a different composition
   pair). Repoint the converge to C1 + C3/F1; drop or recast the
   errors-row pointer as same-direction precedent at most. The
   index row repeats the C2/C5 citation — fix there too. Substance
   (no second renderer defined here) and trigger (inline rendering
   appearing here) stand verbatim.
2. R6 safe census undercounts: "10 safe sites in 5 files" omits
   `types/finalizer.py` ×4 (`:129/:145/:936/:957`, all
   `f"{_safe_type_name(exc)}."` caught-exception tails —
   same position, contexts re-read). True same-spelling
   `_safe_type_name(exc)` census at HEAD:
   `git grep -n '_safe_type_name(exc)' HEAD --
   django_strawberry_framework/` → 14 sites in 6 files
   (connection ×5, forms/inputs ×2, serializer_converter ×1,
   types/base ×1, finalizer ×4, directives ×1). The raw side
   (9 in 6; `operation_state.py:378` is `type(extension)`,
   correctly excluded) is verified exact. Dispose the two
   boundary cases on one stated basis: `permissions.py:662`
   (`exc.value`) and `schema.py:1078` (`describe_value(exc)`).
   The index row repeats "9-raw/10-safe" — fix there too.
   Rejection (threat-model ruling ≠ consolidation; mixed-file
   evidence at forms-inputs :347/:459/:474) and trigger stand;
   corrected numbers strengthen them.
3. `## Defects` "package-majority idiom" gloss is false under
   every basis (9 < 14 by sites; 6 = 6 by files). Restate as the
   mixed idiom it is. The bar analysis itself stands and I
   re-derive it independently: no contract source routes
   caught-exception tails (`describe_value`'s stated scope is
   got-tails on rejected values; `_safe_type_name`'s hostile-
   `__name__` scope is acknowledged, not denied); the types
   reaching THESE tails are minted by Django machinery or the
   trusted deployment (settings read + engine-path import), so no
   wire input reaches them — the AGENTS.md bar (contract row +
   feasible shape + wire input) is not met. C13's trigger names
   exactly the observation that would promote it. Zero defects
   stands.

HEAD movement check: `0c0537e2` at dispatch and at every W2 check
(first to last); target worktree blob `21041723` stable; no new
ledger row names this file; plan untouched by W2 per dispatch. No
new Worker-2 defects. Verdict: `revision-needed` on record
accuracy (SAME W1 context, prose-only fixes 1–3 above); all
judgments stand pending them.

## Independent re-verification (Worker-2) — pass 2, verdict `verified`

Re-pass on resubmission `ready-for-verification/2` (same W2 context).
Gates: HEAD `0c0537e2` unmoved, target blob `21041723` stable, item
diff vs `ITEM_BASELINE` still empty — pass-1 HEAD evidence stands
without re-trace. All 3 record fixes reproduce mechanically: (1) R5
repoints to C1 (`_safe_type_name`) + C3/F1 (`describe_value`) with
bodies named, errors-row recast as same-direction precedent with the
different-pair disclaimer, index row fixed (re-read); substance,
trigger, and freshness untouched; (2) R6 cites 14 safe in 6 with the
exact per-file breakdown (5/2/1/1/4/1 — re-grepped byte-exact) and a
stated class-name-tail basis disposing `permissions.py:662`
(`exc.value`) and `schema.py:1078` (`describe_value(exc)`), index row
fixed (re-read); raw side, trigger, and freshness untouched; (3)
`## Defects` gloss restated as the mixed idiom with exact numbers
(9 vs 14, 6 files each); bar analysis untouched. Nothing else moved:
W1 verdict prose stable (FL0–FL9, R1–R12, Judgment counts),
pass-1 W2 section byte-intact (single instance; residual
`C2/C5`/`majority`/`10 safe` hits are its historical quotes plus
R7's legitimate `str`-population majority), no new sections. No new
defects. Verdict: `verified`.
