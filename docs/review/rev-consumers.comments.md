# Review · Comments: `django_strawberry_framework/consumers.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=cf28b509ad848b9219ef23444c4e99cbd19c1fb8

## Trace

Read the whole live target (`django_strawberry_framework/consumers.py`,
1715 lines: module docstring, 30 symbol docstrings, 25 `#`/`#:` comment
blocks per the `review_inspect.py` census) and the whole own test module
(`tests/test_consumers.py`, 171 lines: module docstring, 2 class
docstrings, 10 function docstrings, 3 banner comments). No sibling axis
records existed at dispatch (only `rev-consumers.md`, `Status:
reviewing`); required reading was AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan, and `rev-consumers.md`. The target and both test
files are dirty versus HEAD but byte-identical to ITEM_BASELINE
(`git diff ITEM_BASELINE -- <paths>` is empty); every grade below is
against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/consumers/comments/inspect/` plus
`consumers.json`. `build_tree_md.py --list-docstrings` passes on the
target and on `tests/test_consumers.py` (1 module, 0 breaking, each).
`check_citations.py --paths <file> --substrings --json` reports 20
citations, 0 violations in the target and 0 citations in the test
module. Provenance sweep (REVIEW.md pattern, regex mode) on the target
hits only kept spec-Decision pointers plus `now` (6), `previously`
(1), `no longer` (2), `legacy` (19, all the protocol's own name),
`used to` (1), each discharged in Findings/Rejected. Voice scan over
both files: one `your` in the target module docstring (F5), two quoted
`your` hypotheticals (R5), none in the own test module; no `Tests
that`/`Ensures` (10/10 clean); no `.py:NN`.

Contract trace, each prose claim checked against its body and one real
caller or authority. Installed upstream strawberry-graphql 0.324.0:
`AsyncBaseHTTPView.run` adapter instantiation by name, `view=` /
`schema=` handler keywords, `connection_acknowledged` set/flip/check,
`send_next` / `send_data_message` / `send_message` funnel into
`send_json`, `run_operation` / `handle_async_results` result loops,
`aclosing`, legacy `cleanup_operation` (unconditional task index +
await), `handle_invalid_message` 4400, `ConnectionRejectionError`
4403/`Forbidden` via `on_ws_connect`, neighbouring 4400/4401/4408/4409
/4429, `NonText`/`NonJsonMessageReceived` translation (plus legacy
`ignore_parsing_errors=True`, which F2 turns on),
`_reject_incremental_delivery` on non-`ExecutionResult`,
subscription-limit `error` from the message-loop task, `complete`
after each result loop, subscripted-generic handler aliases,
`connection_init_wait_timeout` / `keep_alive` knobs, `get_context`
once per connection, `ChannelsWebSocketAdapter.close` ->
`consumer.close`, `ws_consumer` identity, `decode_json` in
`iter_json`. Floor and boundary wheels fetched from PyPI and audited
(0.316.0: transport reads `subscribe` + `execute`, parses
`payload["query"]` in `handle_subscribe` catching only
`GraphQLSyntaxError`; 0.318.1 same; 0.319.0 reads `stream`; no
`isinstance`/`type` test on the schema at any of them; no `aclosing`
at floor): every range sentence in the module docstring, the
`_StopAwareSchema` docstrings, and the `handle_subscribe` containment
comment holds exactly. Channels: `OriginValidator` reads only
`Origin`, `AllowedHostsOriginValidator` is a factory, `get_user` is
`@database_sync_to_async` reading `scope["session"]` with the
allow-list / `get_user` / constant-time hash / flush-on-mismatch /
`AnonymousUser` shape the `_refreshed_actor` docstring states,
`login`/`logout` replace `scope["user"]`, session middleware
consults the live store at send. Django 6.1: ASGI adapter `.upper()`,
comma-join, Latin-1, `unknown`/`0` (the `#"join(value) for name"`
pinpoint resolves), `_get_raw_host` / `get_host` /
`split_domain_port`, `HTTP_X_FORWARDED_PORT` +
`SECURE_PROXY_SSL_HEADER` verdict-neutrality. Package: router
composition order, `_build_router_class` / `_ROUTER_CLASS` /
soft-channels guard, `websocket_consumer_class=` /
`websocket_revalidation_window=` (default imported from this module),
both hint spellings, `__all__` silence, `_channels_logout`
(flush + `AnonymousUser` under scope lock + `actor_transition`),
`_authenticated_actor_or_none` (F9 turns on its 08-26 widening),
`_channels_http_login_establish` function-local import precedent,
`auth/__init__` eager imports, the `sys.modules`-eviction
no-auth-import test, `utils/sessions.py` lease section + helpers +
`scope_key` namespacing (F1 turns on its `dataclasses` import),
`scope_session_lock`, `logout_supported` signed-cookie refusal,
`resolve_auth_aliases` / `ChannelsRequestAdapter.user` /
`request_from_info`, `views.py::_resolved_max_request_body_bytes`
shape parity, `views.py` importing nothing from this module,
`_strawberry_patches.py` assigning `BaseView.parse_json`,
`mask_execution_result` copy semantics + `is_maskable_result` /
`masking_is_active` / `schema_error_policy`,
`DjangoSchema._masked_return`, `truth.describe` huge-int rendering,
`math.isfinite` `OverflowError`, `_monotonic` monkeypatching,
`graphql-core` `TypeError` on non-string input. Own-test-module
claims: no `config/asgi.py`, no WS mount, README gap row naming both
test modules, window domain + handshake verdicts + checkpoints driven
in `tests/test_routers.py` via `WebsocketCommunicator`, lease
lifecycle in `tests/utils/test_sessions.py`, HTTP sibling
`test_transport_api.py` — all true. Other-module prose census: 90
`tests/test_routers.py` docstrings mention a target subject; every
first line states behavior, the full bodies of the six
claim-densest were read, the rest were voice/provenance-flag
scanned; live-tier `consumers` hits are generic package-user
wording, none about this module's symbols.

Cells: no workspace run was needed — every instrument above is
static (source reads, AST census, citation resolution,
spec/upstream/wheel comparison). Sharded and pg are inapplicable by
construction to this Comments pass (no database-reaching probe; all
Proofs are static counts plus grade judgments; Worker-2's prose
edits owe `--code-digest` identity, not cell runs). Cells
unverified: none. Run ids: none (no `workspace.py` runs).

Fingerprints (`git hash-object`):
target `67887b5be1bc80cfc4f051de54d38fde00396ff3`;
`tests/test_consumers.py`
`7dee4bedeb95c06d8eaf2a8c216c682c3d61541b`;
`tests/test_routers.py`
`36c962b1a3c8ba8c879e7d89c44bfe17b4a31c71`;
`routers.py` `e18772f7`, `utils/sessions.py` `21041723`,
`auth/mutations.py` `84183c89`, `auth/sessions.py` `865d6e70`,
`utils/permissions.py` `1c9cfd39`, `views.py` `48ee582e`,
`schema.py` `84f2d5aa`, `extensions/error_policy.py` `a1defd39`,
`utils/truth.py` `d5c96bc8`, `utils/querysets.py` `8fc556d5`,
`_strawberry_patches.py` `90f711fb`. Upstream wheels by version
(strawberry-graphql 0.316.0 / 0.318.1 / 0.319.0 / installed
0.324.0; Django 6.1; graphql-core `TypeError` reproduced live). A
finding's Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

- Observation: the module docstring's import-graph paragraph says the
  connection-actor-lease helpers come from `utils/sessions.py`, "a
  module whose own imports are `__future__`, `asyncio`, `contextlib`
  and typing names". That module now also does `import dataclasses`
  (plus `collections.abc`, whose two names are typing names and stay
  covered). The load-bearing property — stdlib-only, channels-free —
  still holds; the enumeration itself is false.
- Evidence: `git show 05a08e31:.../consumers.py` carries the sentence
  verbatim while `git show a8f31a2d^:.../utils/sessions.py` has no
  `dataclasses` import; `a8f31a2d` (2026-09-03) added it after the
  sentence (2026-07-31). Live `utils/sessions.py` import block
  read in full.
- Impact: a reader auditing the transport import graph from this
  paragraph undercounts the module's imports; the next stdlib-or-not
  question starts from a false inventory.
- Severity: Medium (stale module-docstring enumeration on internal
  code; property it evidences still holds).
- Recommendation: name `dataclasses` in the enumeration; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'dataclasses'
  django_strawberry_framework/consumers.py` prints `1` (0 today);
  the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py` (module
  docstring, "Importing this module" paragraph).
- Grade: stale.
- Text-before:
  `connection-actor-lease helpers from ``utils/sessions.py`` - a module whose own imports are ``__future__``, ``asyncio``, ``contextlib`` and typing names, so it adds nothing to the import graph.`
- Text-after:
  `connection-actor-lease helpers from ``utils/sessions.py`` - a module whose own imports are ``__future__``, ``asyncio``, ``contextlib``, ``dataclasses`` and typing names, so it adds nothing to the import graph.`

### Low

- Observation: the `_contain_message_loop_failure` docstring's
  translation paragraph says both upstream exceptions never reach
  the containment "because both handlers translate them internally",
  with the parenthetical "a binary or malformed-JSON frame already
  gets upstream's controlled close". On legacy, a malformed-JSON
  frame gets no close at all: the loop iterates
  `iter_json(ignore_parsing_errors=True)`, so `NonJsonMessageReceived`
  is never raised there and the frame is silently dropped. The
  paragraph's outcome (neither exception reaches the containment)
  holds; its mechanism is wrong for one of the four combinations,
  at floor and installed alike.
- Evidence: installed + 0.316.0 legacy `handle()` source
  (`ignore_parsing_errors=True`, `except NonTextMessageReceived`
  only, 1002 close) versus transport-ws (both exceptions to
  `handle_invalid_message`).
- Impact: a reader believes every malformed frame ends in a
  controlled close; on legacy it ends in silence, which matters
  when reasoning about what the containment can still see.
- Severity: Low (bounded prose precision; outcome claim true).
- Recommendation: state the per-protocol disposition; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'ignore_parsing_errors'
  django_strawberry_framework/consumers.py` prints `1` (0 today);
  the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py::_contain_message_loop_failure`.
- Grade: stale (false across the supported range, not by a body
  change since).
- Text-before:
  `Two upstream exceptions do NOT reach here because both handlers translate them internally: ``NonTextMessageReceived`` / ``NonJsonMessageReceived`` (a binary or malformed-JSON frame already gets upstream's controlled close).`
- Text-after:
  `Two upstream exceptions do NOT reach here because neither handler lets them escape: transport-ws closes ``4400`` on a ``NonTextMessageReceived`` / ``NonJsonMessageReceived``, while legacy closes ``1002`` on the former and never raises the latter (``ignore_parsing_errors=True`` drops a malformed-JSON frame outright).`

- Observation: the `_actor_is_current` anonymous-carve-out comment
  says "the authenticated predicate itself is the one
  `auth/mutations.py::_authenticated_actor_or_none` applies,
  deliberately spelled rather than imported". Since 08-26 that
  helper applies more than the spelled copy: the legacy-callable
  and awaitable arms (`6873dac6`) have no counterpart in the two
  spelled tests. The why-spelled rationale (private helper,
  whole-`auth`-package import cost) and the third-site promotion
  pointer stay true; the identity claim overclaims by omission
  and leaves a future auth-predicate extension with no pointer
  back to this copy.
- Evidence: `git show 0fa6501d:.../auth/mutations.py` has neither
  arm while the same commit's consumers copy already claims
  identity; live helper body read (None / `is_authenticated` /
  callable / awaitable arms) against the two spelled tests.
- Impact: a reader extending the auth predicate will not know this
  copy exists to keep in step; whether the code should adopt the
  arms is a Mechanics question, but the prose must not claim an
  identity the bodies no longer have.
- Severity: Low (bounded prose precision on internal code).
- Recommendation: scope the claim to the plain-attribute core and
  name the elided arms; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'plain-attribute core'
  django_strawberry_framework/consumers.py` prints `1` (0 today);
  the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py::_actor_is_current`
  (anonymous-carve-out comment).
- Grade: stale.
- Text-before:
  `The authenticated predicate itself is the one ``auth/mutations.py::_authenticated_actor_or_none`` applies, deliberately spelled rather than imported`
- Text-after:
  `The authenticated predicate's plain-attribute core is the one ``auth/mutations.py::_authenticated_actor_or_none`` applies - the None actor and the ``is_authenticated`` flag, without that helper's legacy-callable and awaitable arms, which no scope actor takes - deliberately spelled rather than imported`

- Observation: the `DjangoWebSocketHostValidator` class docstring
  opens with an imperative, "Deny a WebSocket handshake whose
  `Host` Django's own boundary refuses." A class first line is a
  description; ruff leaves mood unchecked so this review is the
  gate.
- Evidence: first-line read; every other class first line in the
  target is descriptive.
- Impact: minor mood inconsistency on the module's one
  public-spelled class.
- Severity: Low.
- Recommendation: recast as a description; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Deny a WebSocket handshake'
  django_strawberry_framework/consumers.py` prints `0` (1 today);
  the rewritten first line earns grade true (description mood,
  same contract).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py::DjangoWebSocketHostValidator`.
- Grade: duplicates the code (mood defect; imperative first line on
  a class, which the class-first-line rule requires as a
  description).
- Text-before:
  `Deny a WebSocket handshake whose ``Host`` Django's own boundary refuses.`
- Text-after:
  `The handshake's ``Host`` check: an ASGI middleware denying the handshakes Django's own boundary refuses.`

- Observation: the `revalidate_operation_actor` docstring opens
  with a question, "Admission checkpoint: may a NEW operation
  start on this connection?" A function first line is imperative.
- Evidence: first-line read against the axis mood rule.
- Impact: minor mood inconsistency on a public checkpoint
  function.
- Severity: Low.
- Recommendation: keep the label, make the verb imperative; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'may a NEW operation start'
  django_strawberry_framework/consumers.py` prints `0` (1 today);
  the rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py::revalidate_operation_actor`.
- Grade: duplicates the code (mood defect; interrogative first
  line on a function, which the rule requires as imperative).
- Text-before:
  `Admission checkpoint: may a NEW operation start on this connection?`
- Text-after:
  `Admission checkpoint: decide whether a NEW operation may start on this connection.`

- Observation: the legacy `handle` override's docstring opens with
  a noun phrase, "The legacy handler's identical loop
  containment." A method first line is imperative.
- Evidence: first-line read; the transport-ws twin opens with the
  imperative "Contain ...".
- Impact: minor mood inconsistency between twin overrides.
- Severity: Low.
- Recommendation: state the behavior imperatively; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'identical loop containment'
  django_strawberry_framework/consumers.py` prints `0` (1 today);
  the rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py::build_revalidating_consumer_class._RevalidatingGraphQLWSHandler.handle`.
- Grade: duplicates the code (mood defect; nominal first line on a
  method, which the rule requires as imperative).
- Text-before:
  `The legacy handler's identical loop containment.`
- Text-after:
  `Contain the legacy loop's escapes exactly like the transport-ws override.`

- Observation: the module docstring's export paragraph addresses
  the reader: "an injected consumer of your own". Second person.
- Evidence: voice scan (the file's only reader-addressing `your`;
  the two `your session ...` hits are quoted wire hypotheticals,
  R5).
- Impact: trivial voice inconsistency.
- Severity: Low.
- Recommendation: drop the filler phrase; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'of your own'
  django_strawberry_framework/consumers.py` prints `0` (1 today);
  the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/consumers.py` (module
  docstring, export paragraph).
- Grade: voice defect (`your` addressing the reader; the axis
  bans second person).
- Text-before:
  `The supported choices are the package default or an injected consumer of your own, passed as`
- Text-after:
  `The supported choices are the package default or an injected consumer, passed as`

- Observation: the `test_a_subscribe_before_connection_init_...`
  docstring in `tests/test_routers.py` — prose about this
  module's admission checkpoint — opens "An unacknowledged
  connection is upstream's 4401, not our rejection" ("our") and
  continues "identical to the un-patched package". The package
  never patches these handlers; the factory derives subclasses
  ("never a per-instance patch"), and "patch" is load-bearing
  vocabulary owned by `_strawberry_patches.py`. The behavior
  claims (4401, read skipped) are true and tested.
- Evidence: first-line + body read against the factory docstring
  ("never a per-instance patch") and the passing 4401 assertion.
- Impact: a reader looking for the "patch" finds subclass seams;
  first-person voice in a contract sentence.
- Severity: Low.
- Recommendation: de-pronominalize and name the mechanism; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'our rejection\|un-patched package'
  tests/test_routers.py` prints `0` (2 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_subscribe_before_connection_init_is_closed_by_upstream_without_revalidating`.
- Grade: process provenance ("our") + stale mechanism name
  ("un-patched").
- Text-before:
  `An unacknowledged connection is upstream's 4401, not our rejection.`
  and
  `so what the client sees is upstream's own ``4401 Unauthorized`` close - identical to the un-patched package.`
- Text-after:
  `An unacknowledged connection is upstream's 4401, not a revocation.`
  and
  `so what the client sees is upstream's own ``4401 Unauthorized`` close - identical to upstream without the revalidating subclass.`

- Observation: the
  `test_the_legacy_graphql_ws_protocol_is_revalidated_at_handle_start`
  docstring — prose about this module's admission close — narrates
  process: "The response is now the same connection-level close
  ... which removed the one asymmetry the two call sites used to
  carry." "Now" + "used to carry" describe how the code came to
  be, not the present rule. The behavior claims (legacy live on
  the mount via upstream's both-protocols default, verified;
  connection-scoped close, verified) are true.
- Evidence: body read; `subscription_protocols` default carries
  both protocols at installed and floor.
- Impact: process-provenance residue in a contract sentence; the
  next reader must factor out history to find the rule.
- Severity: Low.
- Recommendation: rewrite as the present-tense rule; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'used to carry' tests/test_routers.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_the_legacy_graphql_ws_protocol_is_revalidated_at_handle_start`.
- Grade: process provenance.
- Text-before:
  `The response is now the same connection-level close ``graphql-transport-ws`` gets: with revocation connection-scoped there is no per-protocol rejection payload left to differ, which removed the one asymmetry the two call sites used to carry.`
- Text-after:
  `The response is the same connection-level close ``graphql-transport-ws`` gets: revocation is connection-scoped, so no per-protocol rejection payload differs between the two call sites.`

## Rejected

- Bare `(Decision 12)` (module docstring; `resolved_revalidation_window`
  docstring) and `(Decision 19's ...)` (`_host_validation_request`
  docstring): repo-wide convention, not a defect — spec-046 is
  anchored repeatedly on the reader's path through the module
  docstring, and each use sits inside that spec's narrative.
  Trigger: a second spec gaining Decision-numbered prose in this
  module.
- `legacy` throughout (19 hits): the `graphql-ws` protocol's own
  name (upstream `GRAPHQL_WS_PROTOCOL`, handler package
  `graphql_ws`), never a code-age judgment. Trigger: none.
- "that escape used to kill the message loop" (floor containment
  comment): upstream-range vocabulary, corroborated by the 0.316.0
  wheel (in-method `parse`, only `GraphQLSyntaxError` caught);
  states the guarded failure mode. Trigger: the floor rising past
  the in-task parse move.
- `now` / `previously` / `no longer` in the target ("carries one
  now", "previously authorized", "no longer be overtaken", "now
  that nothing is cancelled", "valid now", "no longer
  recognizes", "now this generator"): each describes runtime
  sequence or connection state, not code history. Trigger: none.
- Quoted `your session was revoked / flushed` (`_REVOCATION_CLOSE`
  comment): quoted wire hypotheticals illustrating the
  non-disclosure property, not reader address. Trigger: none.
- `handle_subscribe` / `handle_start` / `__init__` overrides
  without docstrings: function-local private classes; the
  interface contract lives in the factory and module docstrings,
  and the classes are unreachable by import. Trigger: if any of
  them becomes importable.
- "a bespoke code was considered and rejected" (close-code
  comment): design-rationale record naming the reason, no
  round/worker/review attribution. Trigger: none.
- Channels session middleware "re-reads at send time"
  (`_refreshed_actor` docstring): loose verb for reads-flags-plus-
  saves (verified in `channels/sessions.py`), but the operative
  claim — a flush handed the live store would land where the
  send-time middleware acts — is true and reader-actionable.
  Trigger: none.
- `test_consumers.py::test_resolved_window_rejection_message_names_the_value`
  "The rejection's honest message, byte for byte": states the
  exact-equality assertion it performs; "honest" characterizes the
  value-naming contract, not provenance. Trigger: none.
- `tests/test_routers.py` "moved from `subscribe` + `execute` to
  `stream`" (stop-aware test): upstream history load-bearing to
  the partition assertion, corroborated by the 0.318.1/0.319.0
  wheels. Trigger: none.
- `tests/test_routers.py` "no longer matches" (password rotation),
  "previously authorized" (sibling race), "no longer exists"
  (generation ordering): state-transition mechanics phrased as
  present-tense rules. Trigger: none.
- `pre-hook` jargon (one comment, two docstrings in
  `tests/test_routers.py`): descriptive "hook running before
  handling", not a symbol claim; no `::` citation to rot.
  Trigger: none.
- Routed (owner: routers item; observed, not graded — that pass
  grades `tests/test_routers.py` whole): `_ws_communicator`
  "now that the HTTP branch no longer carries one" /
  "the branch now carries two independent handshake checks";
  `test_the_websocket_pattern_is_keyword_only_...` "no longer"
  Decision-4 quotation; `test_a_factory_that_raises_from_its_body_...`
  "your factory". None is about this module's symbols except the
  Host-half sentence, whose behavior claim (two independent
  handshake checks, spec-046 Decision 19) is true.
- No stale prose about this module's symbols was found in any
  other package module: the router hints and composition
  docstrings naming `DjangoWebSocketHostValidator` match its
  contract, and no other package module describes consumer
  behavior.

Handoff: beyond the record's trace I read the live bodies of
`routers.py` (composition, cache, hints, kwargs),
`auth/mutations.py` (logout twins, predicate, import precedent),
`auth/sessions.py` (locks, `logout_supported`),
`utils/sessions.py` (lease section, helpers),
`utils/permissions.py` (adapter, aliases),
`extensions/error_policy.py` (mask/copy/shape gates), the
`DjangoSchema` masking seams, `truth.describe`, and the
`_strawberry_patches.py` `parse_json` assignment — all to check
prose, all true except F1/F9. Floor/boundary wheels
(strawberry-graphql 0.316.0/0.318.1/0.319.0) were fetched from
PyPI into `/tmp/sg0316` and audited, not kept as evidence; the
record cites versions, URLs are re-derivable. Open thread for the
Mechanics axis (not a Comments finding): F9's prose fix scopes
the claim, but whether `_actor_is_current`'s spelled copy should
also adopt the legacy-callable/awaitable arms is a behavior
question for the sibling pass — reachable only with a
method-style `is_authenticated` consumer user model, which no
test constructs. No `## Cross-axis` section: nothing else I saw
belongs to another axis.

## Verification (Comments)

Pass 1, address `review/consumers.py/verify-comments-1`, scratch
`docs/review/temp-tests/consumers/verify-comments-1/`, item diff
`docs/review/temp-tests/consumers/diff/pass-1.diff`.

Step 1 (tree still carries the sent change): `git diff
cf28b509ad848b9219ef23444c4e99cbd19c1fb8 --
django_strawberry_framework/consumers.py tests/test_routers.py`
hashes `79ab14c2...4ce67`, equal to the hash of `pass-1.diff`
(`diff` empty, IDENTICAL). Grading proceeds.

Proof runs (verbatim, expectation-first, before reading
`## Implementation (Worker-2)`; static greps, so in the shared tree
per REVIEW.md; full output in scratch `proofs.txt`). All 13 hold:

- Comments Medium: `dataclasses` prints 1. Lows:
  `ignore_parsing_errors` 1, `plain-attribute core` 1,
  `Deny a WebSocket handshake` 0, `may a NEW operation start` 0,
  `identical loop containment` 0, `of your own` 0,
  `our rejection|un-patched package` in `test_routers.py` 0,
  `used to carry` in `test_routers.py` 0.
- Mechanics C2: `grep -n "upstream's to send"` prints nothing
  (exit 1). C1: `merely absent from`,
  `no __all__ entry here`, `an __all__ and documentation contract`
  all print nothing (exit 1 each).

Grades — every docstring/comment Worker-2 wrote or moved, each as
the whole docstring it sits in (all landed texts read whole in the
live files; pre-existing prose elsewhere not graded):

- Module docstring (3 edits): the `dataclasses` enumeration is
  exactly the live `utils/sessions.py` import block
  (`__future__`/`asyncio`/`contextlib`/`dataclasses` plus
  `collections.abc` AsyncIterator/MutableMapping and `typing.Any`
  as "typing names"); "merely private by convention" names the
  true contrast the sentence's own mechanism clause states
  (function-locality vs convention); the voice fix drops only the
  filler. True.
- `revalidate_operation_actor` first line: imperative, label kept,
  same contract; body coherent. True.
- `_actor_is_current` carve-out comment: the spelled code below is
  exactly "the None actor and the `is_authenticated` flag", and
  the elided arms live in `_authenticated_actor_or_none`
  (`auth/mutations.py:474-477`, callable + awaitable); "which no
  scope actor takes" is the Mechanics R2/R7 floor fact. True.
- `_contain_message_loop_failure` paragraph: per-protocol
  disposition corroborated at installed upstream
  (`handle_invalid_message` closes 4400; legacy `handle()` runs
  `iter_json(ignore_parsing_errors=True)` with only a NonText arm
  closing 1002). True.
- Legacy `handle` first line: imperative, matches the body and the
  transport-ws twin. True.
- `DjangoWebSocketHostValidator` docstring (first line + C1 sites
  2-3): the landed first line is description mood with the same
  contract (judgment call upheld — the proposed sentence measures
  exactly 111 columns, past the 110 grace; the landed line is 79);
  site 2's kept `routers.py::__all__` half is true
  (`routers.py:69` defines the tuple without this name, the
  package root re-exports no consumers name), and the file's sole
  remaining `__all__` mention is that true reference (:1673);
  site 3 is consistent documentation-contract language. True.
- Legacy test docstring: present-tense rule, behavior first line.
  True.
- Subscribe-before-init test docstring: de-pronominalized,
  mechanism named ("the revalidating subclass", matching the
  module docstring's "never a per-instance patch"). True.
- C2 comment (judgment call upheld): the Proof string lived in the
  inline comment, so the reword correctly landed there, naming the
  answering layer per protocol per the Mechanics probe evidence;
  the untouched docstring above makes no layer claim, so nothing
  contradicts. True.

Instruments: `build_tree_md.py --list-docstrings` on both files —
2 modules, 0 breaking. `check_citations.py --paths <both>
--substrings` — 30 citations, 0 violations, 0 warnings.
`review_inspect.py --code-digest <ITEM_BASELINE>:<path> <path>` —
equal both files (`consumers.py` `cf167fe8...48afe`,
`test_routers.py` `a7be3a89...439`, matching Worker-2's
prefixes); direct baseline comparison, no reconstruction (no
other axis changed code in these files). The REVIEW.md prose-diff
view marks zero hunks `[code changed too]`.

Diff hygiene: added lines carry no process provenance (scan hits
discharged: 3x `legacy` = the protocol's own name,
`legacy-callable` = the arm name from the proposal, `round-trips`
= the preserved operation sentence), no line-number citation, no
`we`/`you`/`I` (the only `your` hits left are the two kept quoted
hypotheticals). Both module first lines are byte-identical to
ITEM_BASELINE, so no TREE.md row is owed. No added line exceeds
99 columns.

Whole-diff reading: 12 `@@` hunks, 44+/37-, every hunk one of the
11 findings; no touched symbol has other prose the change made
false. Sibling verifiers' sections read: Performance verification
reports no routed gaps, Mechanics verification reports no routed
gap (its A6 neighbour reads were re-derived independently above,
not taken on trust). Disputes: none recorded, nothing to judge.
No permanent test owed (prose-only). Cells: sharded and pg
inapplicable by construction (static proofs + digest identity);
cells unverified: none.

Fingerprints: `consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b`,
`test_routers.py` `f513d869c78247d103a2e52d32b053d98ddc1f0d`
(both equal Worker-2's post-edit values), `test_consumers.py`
`7dee4bed...` unchanged. Run ids: none (no workspace runs; all
checks static). Scratch: `proofs.txt`, `citations.json`, `diff/`
under the verify dir.

Verdict: verified. 11/11 prose findings landed, 13/13 Proofs
hold, every landed text grades true.

Handoff: Comments verification of pass 1 is closed with no new
finding, no dispute, and nothing routed onward. The three
judgment calls (C2 comment location, shortened Host first line,
C1 kept routers half) were each verified against an independent
fact — Proof-string location, a column count of 111 vs 79, and
the live `routers.py:69` tuple — not taken from Worker-2's notes.
The `routers.py` Routed leads this record placed stay with that
item. If a later pass touches code here, the `--code-digest`
pair above reruns verbatim as the prose/code regression probe.
