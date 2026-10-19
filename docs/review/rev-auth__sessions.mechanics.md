# Review · Mechanics: `django_strawberry_framework/auth/sessions.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5bdea138317eca79e8727c89022df017e3e73d46

## Trace

Read the whole live target (279 lines: `Transport`, `require_channels`,
`classify_transport`, `require_session`, `_require_mutable_scope`,
`scope_session_lock`, `uses_signed_cookie_sessions`, `login_supported`,
`logout_supported`) plus the full call graph in both directions: the sole
runtime importer `django_strawberry_framework/auth/mutations.py`
(`from . import sessions`; `_transport_prologue`, `_login_authenticate`,
`_channels_http_login_establish`, `_login_resolve_body`,
`_login_resolve_body_async`, `_logout_prologue`, `_channels_logout`,
`_logout_resolve_body`, `_logout_resolve_body_async`); the shared-primitive
owner `django_strawberry_framework/utils/sessions.py` whole
(`scope_key`, `ScopeSingletonMessages`, `scope_singleton`,
`session_store_class`, the actor lease); `ChannelsRequestAdapter`,
`request_from_info`, `_is_request` in
`django_strawberry_framework/utils/permissions.py`;
`django_strawberry_framework/utils/imports.py::require_optional_module`;
`unwrap_lazy_object`; the `truth` helpers used (`is_instance`,
`is_subclass`, `kind`, `render`); `django_strawberry_framework/auth/__init__.py`;
`django_strawberry_framework/auth/queries.py` whole (sibling flavor);
`django_strawberry_framework/routers.py::require_channels` + hint block
(twin); the `session_store_class` call site in
`django_strawberry_framework/consumers.py`; exception bases in
`django_strawberry_framework/exceptions.py`; `tests/auth/test_sessions.py`
whole (every branch pinned); the contract sources (README session-auth
support matrix + production error policy + security-profile identity rule;
glossary `auth-mutations` + `channels-request-adapter` + router anchors);
and the `review_inspect.py` overview (leads only, no finding taken from it).

Importer inventory (grep over package + tests + example): the only
production runtime importer is `auth/mutations.py`. Every other production
mention (`consumers.py`, `utils/sessions.py`, `utils/permissions.py`,
`routers.py`, `rest_framework/__init__.py`, `views.py`, `utils/imports.py`)
is a prose citation. Test importers: `tests/auth/test_sessions.py` (whole),
`tests/auth/test_mutations.py` (`_SCOPE_LOCK_KEY`), `tests/test_routers.py`
(opt-in boundary proof). No symbol is moved or renamed by this record, so
no `--cited-by` sweep is owed; no defect (no HUNT fields) and no
duplication (no DRY fields).

Cells: default, sharded and pg are all inapplicable by construction. The
target reaches no database, alias or dialect decision: classification is a
pure real-class + `scope["type"]` read, the lock is an in-memory
per-scope `asyncio.Lock`, and the only settings touch
(`uses_signed_cookie_sessions` via `session_store_class`) resolves a class
object without opening a connection. No workspace probe was needed: every
behavior is pinned by the existing package-tier tests read statically, and
no uncertain behavior required runtime proof. No run ids.

The target was dirty with concurrent work at read time (`M
django_strawberry_framework/auth/sessions.py`); the fingerprints below are
the live text actually reviewed. `tests/auth/test_sessions.py` is likewise
dirty. The neighbor blobs still match the plan's `## Owned changes`
(`auth/mutations.py` 98ae63f1, `tests/auth/test_mutations.py` 4cb49982,
`routers.py` 299da0f5, `tests/test_routers.py` f513d869), so no concurrent
drift entered through them.

Fingerprints (`git hash-object`):

- 865d6e704d2df50bcad465ad3005eccb39e8c545 `django_strawberry_framework/auth/sessions.py`
- 98ae63f1965a08d28332ae6e24aa24ea39d9d511 `django_strawberry_framework/auth/mutations.py`
- b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9 `django_strawberry_framework/auth/queries.py`
- 2e480818424d4b130e613e3e2da027aaad7144ad `django_strawberry_framework/auth/__init__.py`
- 21041723250de58876d95eaec14e1078a6f16a4f `django_strawberry_framework/utils/sessions.py`
- 1c9cfd398e6096e03bda82ba93dfd66a6d2fb890 `django_strawberry_framework/utils/permissions.py`
- 291ecedd30c7d8af9c007758112e867c09d031eb `django_strawberry_framework/utils/imports.py`
- 770f36ae9cc9eec1201e5daece196ed038d758d1 `django_strawberry_framework/utils/lazy.py`
- d5c96bc8d191d3fce0a20140d8e91063bb466ec9 `django_strawberry_framework/utils/truth.py`
- 299da0f541f184ec833e01a4d9c83cc0d7880d15 `django_strawberry_framework/routers.py`
- 0791c04a6c7b2619562f33dc707b002cde718c6b `django_strawberry_framework/consumers.py`
- 93401220b5e2c528a421481721f0e2ac460aa0bd `django_strawberry_framework/exceptions.py`
- b71c84ecd4dc90b9af37518d186716f1d64d9a96 `tests/auth/test_sessions.py`
- 4cb499820cbed5163777099e9c9804cf7a523b50 `tests/auth/test_mutations.py`
- f513d869c78247d103a2e52d32b053d98ddc1f0d `tests/test_routers.py`
- 30978c34f63a833ffcc0fa11c80b773d241921be `docs/README.md`
- 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd `docs/GLOSSARY.md`

Looks-for discharge (each entry: none + reason, or rejection + trigger):

1. Rule enforced at a caller instead of its owner: none. The
   classify -> capability -> `require_session` order lives in the shared
   `_transport_prologue` at the state-machine owner (login and logout reuse
   one body); the scope-lock-OUTER / actor-lease-INNER order has a single
   call site and is documented at the lease owner. The sync-bridge
   per-request-scope rule is asserted in docstrings and fails loud via
   asyncio (R4).
2. Policy in an adapter, mechanism in a policy layer: none. The adapter
   returns `None` for an absent session and raises nothing; the boundary
   converts absence to the actionable error, and the capability predicates
   live in the module whose charter owns them.
3. Contract source deciding differently from the body: none. README matrix
   rows (WebSocket login rejected pre-authentication; signed-cookie
   WebSocket logout rejected pre-mutation; missing middleware rejected on
   both surfaces), the subclass-only signed-cookie test including its
   custom-engine caveat direction, and the glossary transport / lock /
   fail-closed paragraphs all match the body and the prologue ordering.
4. Branch no real path reaches: none. Every branch is pinned by
   `tests/auth/test_sessions.py` (unknown object, missing/unknown scope
   type, lazy proxy, `__class__` stand-in, channels-absent, both
   missing-session shapes, immutable scope, corrupted slot, subclassed
   engine, all six capability answers, cancellation and cross-scope
   lifecycle); the two guards unreachable via a real communicator are
   fail-closed and tested, not dead.
5. Mode flag standing in for a named adapter: none. `Transport` is a
   classifier output; the per-mode native paths live in the state machines,
   and no behavior hides behind the enum in this module.
6. State owned in two places: none. The engine expression is single-sited
   in `utils/sessions.py` (the opt-in split the boundary test pins); the
   lock lives only in the scope dict (no-global-registry test); the actor
   lease is a separate documented key; `CHANNELS_FLOOR` is single-sited.
7. Dependency pointing the wrong way: none. The target imports only
   `utils.*` + `exceptions` (no `auth`, `consumers`, `routers`,
   `channels`); no `TYPE_CHECKING`; `consumers.py` reaches the engine
   through `utils/sessions.py` (function-local import).
8. `django.conf.settings` read at import: none. Settings are read at call
   time inside `session_store_class` (`override_settings` honored, pinned
   by tests); module level builds only a key string and a messages record.
9. `__all__` disagreeing with the public surface: none. No `__all__`,
   matching both auth siblings; the module is private by charter (named in
   neither `auth.__all__` nor the package root) and the channels-free
   import is pinned by a subprocess test.
10. Two sites implementing one rule: rejected (R2, R3). The lock/lease
    key + messages pairs are per-surface DATA by the `ScopeSingletonMessages`
    design, already sharing `scope_key` / `scope_singleton`.
11. Sync/async twins that drifted: none. The target holds no twins; the
    single `scope_session_lock` helper serves both callers, and the
    callers' twin bodies live in the closed `auth/mutations.py` item,
    outside this fence.
12. Guard one flavor has and a sibling lacks: rejected (R1, R7). The
    `isinstance(scope, MutableMapping)` check is deliberately the builtin:
    ABC capability (virtual subclasses legitimate), gate-clean (TR101 is
    report-only and targets `type` only), and a `__class__` spoof fails
    loud at the subsequent real attribute use. `getattr(request,
    "session", None)` matches the sibling resolver convention and is
    gate-clean (TR104 targets dunder/`Meta`/`_meta` only).

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

- R1 (bound `scope.get("type")` vs the unbound-`Mapping.get` discipline):
  `classify_transport` reads the scope type through the scope's own bound
  `.get`, while the adapter's `_scope_value` and the context resolver
  deliberately read through unbound `Mapping.get` so no override runs. Not
  a finding: no contract source establishes the unbound rule for this read
  (the cited docstrings govern the adapter's scope-value reads and context
  reads), and no trust boundary is crossed — a lying scope mapping is the
  deployment lying to itself over server-side ASGI data, and every real
  scope is a plain dict. Trigger: `scope["type"]` ever read from
  client-influenced data, or the mapping-read disciplinedocstring extended
  to classification reads.
- R2 (`require_channels` twin in `routers.py`): the two guards share the
  owner (`require_optional_module`) and the floor (`CHANNELS_FLOOR`) and
  differ only in their feature-keyed hint strings, which
  `utils/imports.py` requires to stay single-sited at the feature owner;
  both sites document the twin. DRY change challenge: a hint rewording
  touches exactly one site by design. Trigger: a third behavioral fork
  between the guards, or the hint-ownership rule withdrawn. (The
  `require_drf` count wording is already routed to the `rest_framework/`
  integration item.)
- R3 (`_is_request` vs `classify_transport` accepted-set overlap): both
  unwrap a lazy proxy and real-class-check against `HttpRequest` /
  `ChannelsRequestAdapter`, but they answer different contracted questions
  (read-path resolvability vs auth transport mode) and the sets may
  legitimately diverge; the overlap is pinned by agreement tests (lazy
  request resolves-and-classifies; `__class__` stand-in refused by both).
  Trigger: a third request class landing in one predicate but not the
  other.
- R4 (sync-bridge loop caveat for a multiplexed scope): the sync logout
  body bridges even a WebSocket scope "for completeness", while the lock
  docstring requires the bridge to see only per-request scopes; a reused
  multiplexed scope could see a cross-loop `RuntimeError` instead of
  serializing. Not a finding: no production path reaches it (the router's
  WebSocket consumer is async and both async bodies await Channels scopes
  natively; sync consumers build per-request scopes), and a violation
  fails loud, never silently unserialized. Trigger: a multiplexed scope
  reaching repeated sync bridges.
- R5 (hand-built adapter with a non-`Mapping` scope): `request_from_info`
  returns a bare adapter as-is without validating its scope, so a
  directly-constructed adapter holding a non-mapping scope reaches
  `candidate.scope.get("type")` as `AttributeError`, not the documented
  actionable `ConfigurationError`. Not a finding: outside the typed
  contract (`scope: Mapping`), and every resolver-built adapter is
  `isinstance`-checked at construction. Trigger: `request_from_info`
  validating or coercing scope shape itself.
- R6 (`Transport` exhaustiveness): `login_supported` / `logout_supported`
  default-allow any member that is not `CHANNELS_WEBSOCKET`, so a fourth
  member would ship allowed until someone edits the predicates. Not a
  finding: speculative with no reachable input today; the enum is closed at
  three members and all six capability answers are pinned. Trigger: a
  fourth `Transport` member landing without capability answers.
- R7 (`current_user` has no classification or capability gate): correct by
  contract — the read path mutates no session, and the glossary read-path
  paragraph requires it to work over the router (WebSocket). Trigger: a
  session-mutating step added to the read path.

Handoff: The module is small, fully pinned, and its contracts check out in
both directions (README matrix, glossary anchors, owner docstrings, the
opt-in boundary test, the truthful-reads gate tiers). The two threads I
considered most seriously both end in documented, fail-loud behavior: the
bound `.get` on `scope["type"]` (R1) and the sync-bridge loop caveat (R4).
For Performance awareness (not a cross-axis finding; their
repeated-settings-reads entry owns it): `logout_supported` re-resolves the
engine (`settings` + `import_string` + `issubclass`) on every WebSocket
logout call — unmeasured, and logout is once-per-session, so I left it
alone. No sibling records existed at review time; nothing here depends on
their verdicts. Scratch kept under
`docs/review/temp-tests/auth-sessions/mechanics/` (`inspect/` overview +
stripped source, `sessions.json`).

## Verify mechanics

Pass 1 implements Comments F1-F9, prose-only in the target. Mechanics held
no findings; this pass confirms no-findings stands and the change disturbs
nothing the Mechanics verdicts rest on. Fully static; no workspace copy
bound, no run ids.

1. The shared tree still carries the sent change: `git diff
   5bdea138317eca79e8727c89022df017e3e73d46 --
   django_strawberry_framework/auth/sessions.py` is byte-identical to
   `docs/review/temp-tests/auth-sessions/diff/pass-1.diff` (cmp IDENTICAL,
   7045 bytes each). `tests/auth/test_sessions.py` diff vs ITEM_BASELINE is
   0 bytes: the pass touches the target only.
2. Prose-only identity: `uv run python scripts/review_inspect.py
   --code-digest
   5bdea138317eca79e8727c89022df017e3e73d46:django_strawberry_framework/auth/sessions.py
   django_strawberry_framework/auth/sessions.py` exits 0 with both sides
   `sha256:d54bef3769a6d4d6004c11cc7dabe61df6b793c3f25947d39e113e6d012faf85`.
   No executable line moved, so no Mechanics defect is introducible; every
   pinned behavior and every Performance probe bound stands.
3. Whole-diff reading through the Mechanics axis: 7 hunks, each inside the
   module docstring, a function docstring, or a `#` comment (F1 capability
   paragraph, F2 module bullet + `require_session`, F3 hint comment, F5
   lock-messages comment, F6 `classify_transport` docstring, F7-F9 first
   lines + F4 deletions). Zero executable lines touched.
4. No symbol moved: top-level symbol keys identical baseline-vs-live (12/12:
   3 Assigns, `Transport`, 7 Functions, 1 AsyncFunction; line numbers shift
   by prose only). `Transport` members identical (3, same values). No
   `__all__` before or after; imports untouched (covered by the digest
   identity). No `--cited-by` sweep owed.
5. Rejections R1-R7 stand undisturbed: all 10 executable R-site patterns are
   byte-identical baseline-vs-live - `candidate.scope.get("type")` (R1),
   `require_optional_module("channels", ...)` (R2),
   `unwrap_lazy_object(request)` + real-class checks (R3),
   `factory=asyncio.Lock` (R4), the `getattr(request, "session", None)` /
   `MutableMapping` shapes (R5, R12-discharge), `transport is [not]
   Transport.CHANNELS_WEBSOCKET` + `not uses_signed_cookie_sessions()` with
   the enum closed at 3 (R6), and the read path untouched via byte-identical
   `auth/queries.py` (R7). Every trigger still false: no fourth member, no
   third guard fork, no mapping-discipline extension, no multiplexed-scope
   bridge path (`auth/mutations.py` byte-identical, 98ae63f1).
6. Neighbors byte-stable: all 14 record fingerprints reproduce exactly
   (mutations 98ae63f1, queries b036bdac, auth `__init__` 2e480818,
   utils/sessions 21041723, utils/permissions 1c9cfd39, utils/imports
   291ecedd, utils/lazy 770f36ae, utils/truth d5c96bc8, routers 299da0f5,
   consumers 0791c04a, exceptions 93401220, test_sessions b71c84ec,
   test_mutations 4cb49982, test_routers f513d869), so no concurrent drift
   entered through any file the verdicts rest on.
7. Lint gates: `ruff check` pass, `ruff format --check` pass,
   `check_trailing_commas.py --check` 0 violations, `check_citations.py
   --check` 1302 resolve, all exit 0.

No new findings, no disputes, no attacks applicable beyond the disturbance
sweep (a prose-only diff has no second cardinality, flavor, or cell).
Scratch: `docs/review/temp-tests/auth-sessions/verify-mechanics-1/`
(`live-item-diff.diff`, `symbols.txt`, `enum-members.txt`,
`neighbor-fingerprints.txt`, `rsites-base.txt`, `rsites-live.txt`,
`lint-ruff-check.txt`, `lint-ruff-format.txt`, `lint-commas.txt`,
`lint-citations.txt`).
Fingerprints: live target
`e50011e6cae837a7b1322d704a7f8adbb69bcec3` (== pass-diff `+` side),
baseline `865d6e704d2df50bcad465ad3005eccb39e8c545`, code digest
`sha256:d54bef3769a6d4d6004c11cc7dabe61df6b793c3f25947d39e113e6d012faf85`.

Handoff: Mechanics verification closes with no findings standing and zero
disturbance. The one judgment call worth stating: the Comments rewordings
touch prose the Mechanics record quotes as corroboration (the
`require_session` downstream shape, the hint comment's arrival path), but
they make that prose MORE consistent with the Mechanics verdicts (R4/R5),
never less; no re-grade owed. Nothing here depends on the Performance or
Comments verifiers' verdicts. Open threads: none.

Status: verified
