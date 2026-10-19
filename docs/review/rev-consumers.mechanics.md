# Review · Mechanics: `django_strawberry_framework/consumers.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=cf28b509ad848b9219ef23444c4e99cbd19c1fb8

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-consumers.md` (skeleton: `Status: reviewing`, blank Path
class), sibling axis records, then the whole live target. Sibling
`rev-consumers.performance.md` read whole (Status: no-findings, Path
class hot, eight rejections R1-R8, no `## Cross-axis (for Mechanics)`;
its Handoff agrees with this record's R-lot on the local-import shape
from the cost angle and notes a board-owned Host-denial logging item it
does not re-raise — no Mechanics content for this axis). Sibling
`rev-consumers.comments.md` did not exist at write time; no Handoff or
Cross-axis text was available from it.

Target read whole (1715 lines, blob `67887b5b`, same bytes the
Performance record fingerprinted). The target is dirty vs HEAD
(concurrent work; reviewed as it stands per the dispatch, no hunk
attributed here). Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/consumers/mechanics/inspect/` (json
`docs/review/temp-tests/consumers/mechanics/consumers.json`).

Callers and neighbours traced by first-hand reads (fingerprints below):
the only production importer is
`django_strawberry_framework/routers.py` (import block, the guarded
factory call, window validation, outermost Host composition);
`django_strawberry_framework/views.py::_resolved_max_request_body_bytes`
(the twin validator the window docstring names);
`django_strawberry_framework/utils/sessions.py` (lease, provenance,
resolver — the shared side of every ordering claim);
`django_strawberry_framework/extensions/error_policy.py` (the four
masking helpers the result source delegates to);
`django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`
(the spelled-not-imported predicate);
`django_strawberry_framework/__init__.py` (re-exports no consumers
name); `tests/test_consumers.py` (whole); `tests/test_routers.py`
(revocation, containment, read-set, non-string-query, and Host rows);
`docs/GLOSSARY.md` anchors connection-scoped revocation, WebSocket
revalidation window, WebSocket Host boundary, WebSocket
consumer-injection seam, auth mutations, production error policy,
`DjangoErrorPolicyExtension`, single-upstream parity; `docs/README.md`
transport, auth, and production-profile rows. No production module
outside `routers.py` imports this target; nothing in `utils/`, `auth/`,
or `extensions/` imports it back.

Upstream read first-hand at both ends of the supported range
(`strawberry-graphql>=0.316.0`, installed 0.324.0, channels 4.3.2,
Django 6.1): installed `subscriptions/protocols/graphql_transport_ws/handlers.py`
(`handle_subscribe` creates the operation task, parses nothing),
`subscriptions/protocols/graphql_ws/handlers.py` (`handle_start`
likewise; `handle_async_results` catches only `CancelledError`),
`channels/handlers/ws_handler.py` (adapter `send_json`/`close`,
`GraphQLWSConsumer.__init__`/`connect`/`disconnect`, `max_subscriptions_per_connection`
default 100), `schema/schema.py` (`_prepare_operation_async` converts
every parse failure, including the lexer `TypeError`, to
`PreExecutionError`); floor 0.316.0 fetched from upstream git
(`graphql_transport_ws/handlers.py` parses `payload["query"]` in
`handle_subscribe` catching only `GraphQLSyntaxError`;
`graphql_ws/handlers.py` `handle_start` is the same no-parse shape as
installed; `_parse_and_validate_async` carries the same broad
parse-to-`PreExecutionError` conversion as installed).

Probe `docs/review/temp-tests/consumers/mechanics/probe_legacy_nonstring.py`
(copied to `tests/test_mech_probe_legacy.py` in the copy only; drives
the two generated handler classes directly against a scripted transport
with an anonymous never-authenticated scope, so admission takes the
read-free carve-out and no database is touched): default cell
`review-20260929T024209-44b9ef` 2 passed; sharded cell
`review-20260929T024216-e72e86` 2 passed. Three earlier reds were
superseded probe revisions (setup bug, then two wrong expectations the
probe itself corrected — the record's R1 tells that story):
`review-20260929T023828-0152d3`, `review-20260929T023901-3c1ac7`,
`review-20260929T024128-85e050`, plus one uncaptured diagnostic rerun of
the single node. pg is inapplicable by construction for this evidence:
the probe performs zero database I/O and asserts only in-memory
handler/dispatch facts while upstream dispatch is dialect-free; the
static upstream facts are cell-independent. The verifier judges.

`check_citations.py --cited-by` was not run: this record proposes no
move or rename of any symbol. `workspace.py audit` on this record is
owed by Worker-0 per the checks table.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/consumers.py`
`67887b5be1bc80cfc4f051de54d38fde00396ff3` (live, whole, dirty);
`django_strawberry_framework/routers.py`
`e18772f76beed8f42cc5bba0d7b9a4e4f7f77bd2`;
`django_strawberry_framework/views.py`
`48ee582ecdba41d49beb2434f2a9e0af992d39d4` (validator + cap only);
`django_strawberry_framework/utils/sessions.py`
`21041723250de58876d95eaec14e1078a6f16a4f`;
`django_strawberry_framework/extensions/error_policy.py`
`a1defd394d8eda9b698964030a09efe6914278db`;
`django_strawberry_framework/auth/mutations.py`
`84183c893fdbf258e112ccf6d1cc66f6bc50c513` (predicate + login/logout
shape only); `django_strawberry_framework/auth/sessions.py`
`865d6e704d2df50bcad465ad3005eccb39e8c545` (lock + support rows only);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (exports);
`tests/test_consumers.py`
`7dee4bedeb95c06d8eaf2a8c216c682c3d61541b` (whole);
`tests/test_routers.py`
`36c962b1a3c8ba8c879e7d89c44bfe17b4a31c71` (revocation, containment,
read-set, non-string-query, Host rows);
`tests/utils/test_sessions.py`
`8b75454900a05e5aeb319820c6ca19709bbb54bf` (resolver rows only);
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be`;
installed upstream `graphql_transport_ws/handlers.py`
`1c5da7ef500ea4b8967923e0f66bb02d74083f59`,
`graphql_ws/handlers.py`
`58c0ca4bc364455536583abee0cee5c2be5f7123`,
`channels/handlers/ws_handler.py`
`de158159f84155c9276f9201542ff580f0c7f812`.

## Findings

### High

None.

### Medium

None.

### Low

None.

Looks-for discharge (REVIEW.md "Mechanics"), each a finding, `none`
with the reason, or a rejection (full text under `## Rejected`):

- Rule enforced at a caller instead of its owner: none. The window
  default and its validator live with the knob's consumer
  (`django_strawberry_framework/consumers.py::resolved_revalidation_window`,
  called once by the router at construction); the Host decision is
  Django's own `get_host()` with only the projection package-owned;
  masking is the extension module's classifier/replacement/shape gate,
  never restated; lease, provenance, and the engine expression are
  `django_strawberry_framework/utils/sessions.py`'s, shared with the
  auth layer so neither side drags the other in.
- Policy in an adapter, mechanism in a policy layer: none. The
  generated adapter stays a two-line delegation into
  `django_strawberry_framework/consumers.py::send_revalidated_operation_frame`,
  which owns the whole critical section; the delegated-control arm is
  the same ruling's cut-off half (nothing after DECIDED), not a second
  policy, with the invariant stated on the adapter.
- Decision the contract sources make differently from the body: none.
  Gated set (`next`/`data`/operation `error`), delegated control
  frames, `4403`/`Forbidden` reuse, `4400` invalid-message vs `1011`
  internal-error split, window semantics at both checkpoints,
  Host-before-Origin with no new setting, per-event masking with the
  incremental frame passing through to upstream's own refusal, and the
  same-connection logout consequences (teardown completes durably, the
  reply frame is gated like any post-revocation frame, the close is
  the answer) all match the glossary anchors, README rows, owner
  docstrings, and the oracles named in the Trace. The containment
  closes and the floor-compat operation message are module-owned;
  no outer contract constrains them (single-upstream parity governs
  card claims, not wire text).
- Branch no real path reaches: none. The one suspicious arm —
  `django_strawberry_framework/consumers.py::_ConnectionRevocation.close`
  observing a done-and-cancelled attempt while CLOSING — is reachable
  by prestart cancellation (a `cancel()` delivered before the attempt
  coroutine's first step runs none of its recording body) and is
  pinned by
  `tests/test_routers.py::test_close_observes_an_already_cancelled_attempt_as_abandoned`:
  R4. `stream` never being called below 0.319.0 is the documented
  version-dependent seam, not a dead branch.
- Mode flag standing in for a named adapter: none. The window is a
  numeric bound with uniform expiry semantics at both checkpoints,
  not a mode selector; the `window > 0.0` gates are cache
  read/write, not behaviour switches.
- State owned in two places: none. Revocation lives on the consumer
  instance (private to this module — no reader outside it), while
  lease, provenance, and the revalidation timestamp live on the scope;
  that split is the shared-vs-private line (the auth layer reaches
  the lease, never the revocation), every access holds the lease, and
  the timestamp stays out of `ConnectionActorState` because the
  window knob is consumers-owned while the state record is shared:
  R10.
- Dependency pointing the wrong way: none. Module level reaches only
  stdlib, hard Django (`HttpRequest`, `DisallowedHost`), the package
  logger, `ConfigurationError`, truthful readers, and
  `django_strawberry_framework/utils/sessions.py`. The three
  function-local imports are each justified where used (soft
  `channels`, `strawberry`-above-the-guard, and the late-bound
  resolver: R5). No `TYPE_CHECKING` block exists to hide a cycle,
  and no lower layer imports this module back.
- `django.conf.settings` read at import: none — the module imports
  no settings object at all (`settings.ALLOWED_HOSTS` appears once,
  in prose about upstream). `SESSION_ENGINE` and `DEBUG` are read
  per miss / per event at runtime by their owners.
- `__all__` disagreeing with the public surface: none, with the
  prose it assumes routed to Comments (C1). The module defines no
  `__all__`, matching six sibling top-level modules (`connection`,
  `conf`, `schema`, `keyset`, `registry`, `apps` carry none either);
  no star-import consumer exists, the package root re-exports no
  consumers name, and the router imports by name: R6.
- Two sites implementing one rule: run the change challenge on all
  four candidate pairs; each is rejected with its count and trigger:
  the window/body-cap validators (R3), the two `handle()` overrides
  (shared `_contain_message_loop_failure`, protocol name
  legitimately differs), admission vs outbound (shared
  `_actor_is_current` + `_revoke_connection`, responses legitimately
  differ), and the authenticated predicates (R2).
- Sync/async twins that drifted: none — no sync twin exists. The
  transport is ASGI-WebSocket-only (Channels), and the HTTP tier's
  sync/async split lives in `views.py`, which does not import this
  module.
- Guard one flavor has and a sibling lacks: the transport-ws
  non-string-query arm has no legacy twin, and the asymmetry is
  correct — legacy never parses in `handle_start` on any supported
  release (floor and installed sources read), and upstream's own
  broad parse catch answers with an operation error on both, so the
  arm's loop-survival job never arises there. Probed end to end
  (transport arm sends the package message and creates no operation;
  legacy answers with upstream's own masked operation error and the
  task completes normally): R1. The unhashable-id combination and
  the newer-release rewording were traced and carry their own
  triggers: R8, R9. The containment guard itself is symmetric (both
  `handle()` overrides, both pinned live and scripted).

## Rejected

- **R1: legacy has no twin of the transport-ws non-string-query arm
  (`handle_start` vs `handle_subscribe`).** The arm's job is
  loop survival where upstream parses in the admission method, and
  that is transport-ws-on-floor only: floor `handle_subscribe`
  parses `payload["query"]` catching only `GraphQLSyntaxError`
  (a non-string escapes as `TypeError` and kills the loop), while
  floor and installed `handle_start` alike only forward the query
  to the operation task. Where the task receives it, upstream's own
  broad parse catch (installed `_prepare_operation_async`, floor
  `_parse_and_validate_async`) converts the lexer `TypeError` to a
  `PreExecutionError` that each loop renders as an operation error,
  so no whole-protocol unwrapping and no dropped operation occur on
  any supported release. Probed live: the transport arm sends
  `{"id", "error", [{"message": "Query must be a string."}]}` and
  creates no operation, while legacy answers with upstream's own
  operation error (masked to the policy message at this tier) and
  its task completes with no exception. An earlier probe revision
  expected a dead legacy task; the probe corrected the reviewer,
  not the code. Trigger: a contract requiring operation-error
  containment (rather than loop survival) on legacy, or a reachable
  input where the legacy task path loop-kills or discloses.
- **R2: the authenticated predicate is spelled twice in
  `_actor_is_current` (scope actor, refreshed actor) and a third
  time in substance by
  `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`.**
  The module records its own tolerance ("a THIRD site promotes to
  `utils/permissions.py`"), and the split is structural: importing
  the auth helper would register the whole GraphQL auth subsystem
  on first authenticated operation, which a test forbids. The
  divergence (legacy-callable and awaitable handling) cannot
  mis-authorize here: under the `Django>=5.2` floor no Django user
  carries those shapes, and the attribute only routes
  anonymous-carve-out vs session-reload, both fail-closed — a weird
  scope actor is still judged by the reloaded session user.
  Challenge count: posit a predicate-semantics change — two
  in-module spellings plus the auth surface move together, which is
  the recorded trigger firing, not drift. Trigger: a third site, or
  a scope-actor shape whose routing changes a verdict.
- **R3: `resolved_revalidation_window` duplicates the shape of
  `views.py::_resolved_max_request_body_bytes` (exact-type gate,
  `truth.describe` tail, typed `ConfigurationError`).** Same
  pattern, different rules: int+float domain with float coercion,
  NaN/inf/negative rejection, and Overflow chaining vs int-only
  with a None-means-unset ladder. The shared tail renderer is
  single-owned by `utils/truth.py::describe`, so a rendering change
  has one site; a domain change has exactly its own. Trigger: a
  third exact-type-plus-tail validator (then factor the shape) or
  the two domains converging.
- **R4: `close()` observing a done-and-cancelled attempt while
  CLOSING is a branch no production transition reaches.**
  Refuted by construction and by test: a `cancel()` landing before
  the attempt coroutine's first step runs none of its recording
  body, leaving CLOSING with a cancelled attempt (the disconnect
  `settle()` racing a just-created attempt is the producer), and
  `test_close_observes_an_already_cancelled_attempt_as_abandoned`
  drives exactly that interleaving and asserts ABANDONED with no
  second attempt. It enforces the documented never-rest-in-CLOSING
  invariant at the read site. Trigger: removal of the
  prestart-cancellation producer.
- **R5: hoist the function-local `session_store_class` import in
  `_refreshed_actor` to the module top (the module already imports
  four names from `utils/sessions.py`).** The locality is
  load-bearing late binding, not leftover caution: the resolver
  failure rows patch `utils.sessions.session_store_class`
  (`tests/test_routers.py` fail-closed row), which a top-level
  `from`-binding would freeze out. Cost is one dict lookup on the
  miss path. Trigger: the patch point moving into this module's
  namespace.
- **R6: add an `__all__` spelling the supported surface.**
  No consumer needs one: no star-import of this module exists, the
  package root re-exports none of its names, the router imports by
  name (including the deliberate private default import), and six
  sibling top-level modules likewise define none. Direct-import
  "support" is a documentation contract either way — `__all__`
  never blocked `from M import name` — and the only import-time
  barrier claimed (the function-local consumer class) is real.
  Trigger: a star-import consumer or a root re-export of a
  consumers name. The docstring sentences that presuppose the list
  are C1.
- **R7: the scope/refreshed actor checks lack the auth helper's
  legacy-callable and awaitable arms.** Same facts as R2, read as a
  guard gap: no contract extends the session-auth anonymity
  definition (whose docstring scopes it to the session-auth
  surfaces) to the transport scope actor, and the routing-only use
  keeps every shape fail-closed. Trigger: a documented Channels
  auth-middleware shape with a non-boolean `is_authenticated`
  whose routing changes a verdict.
- **R8: unhashable operation id combined with a non-string query
  takes the transport arm (operation error, open connection)
  instead of the unhashable-id 4400.** Safe, not silent: the arm
  copies `message["id"]` into the reply without hashing or
  indexing it, so the dispatcher crash the 4400 answers never
  occurs on that path; no operation is registered and the gated
  error send revalidates normally. No contract demands uniform
  refusal for unhashable ids across payload shapes. Trigger: such
  a contract.
- **R9: on newer releases the transport arm rewords upstream's own
  non-string-query error ("Query must be a string." instead of
  upstream's text).** No wire-text parity contract exists
  (single-upstream parity governs Alpha card claims, not channel
  wire text); the package message is fixed and discloses nothing,
  and making the arm floor-only would need the version test the
  module rejects as the wrong shape (undetectable renames). The
  arm's load-bearing job is floor loop survival; the rewording is
  its harmless shadow on newer releases. Trigger: a wire-parity
  contract for operation errors.
- **R10: revalidation state is split across the consumer instance
  (`_revocation`), the shared scope record (lease + provenance),
  and a second scope key (the window timestamp).** The instance
  half is private to this module (verified: no `_revocation`
  reader outside it, auth layer included) while the scope half is
  the auth-shared contract; merging the timestamp into
  `ConnectionActorState` would couple the shared record to the
  consumers-owned window knob. Every read and write of all three
  holds the actor lease, so no torn observation exists. Trigger: a
  reader outside the lease, or a third scope key for the same
  state.

## Cross-axis (for Comments)

### Medium

- **C2 — Observation.** The non-string-query test docstring states
  which layer answers, and is wrong on one protocol:
  `tests/test_routers.py::test_a_non_string_query_delivered_over_a_socket_does_not_break_the_loop`
  says "The hostile payload's own failure is the operation task's
  business - whichever error frame it answers with is upstream's to
  send." On graphql-transport-ws no operation task exists for that
  input — the package arm in the generated `handle_subscribe`
  answers before `super()` runs — so both clauses misdirect a
  future editor to the wrong layer. On legacy both clauses hold.
  Symbol: `tests/test_routers.py::test_a_non_string_query_delivered_over_a_socket_does_not_break_the_loop`.
  Grade: stale.
- **Evidence.** The arm at
  `django_strawberry_framework/consumers.py::build_revalidating_consumer_class`
  (`handle_subscribe`, non-string `payload["query"]`) sends the
  error via `send_message` and returns without delegating; the
  Mechanics probe `review-20260929T024209-44b9ef` shows the sent
  frame is the package's `{"message": "Query must be a string."}`
  with `"1" not in handler.operations`, while the legacy twin
  sends upstream's own masked operation error from its task.
- **Impact.** A maintainer chasing the transport-ws error text
  starts in upstream's operation task, where it is not produced;
  the row's true pin (loop survival on both protocols) is
  unaffected.
- **Severity.** Medium — a false behavior statement in a committed
  test docstring about internal code, the ladder's Medium row. No
  wire or runtime consequence either way.
- **Recommendation.** Reword to name the answering layer per
  protocol. Text before: "The hostile payload's own failure is the
  operation task's business - whichever error frame it answers with
  is upstream's to send." Text after (proposal; the verifier grades
  what lands): "The hostile payload's own failure is the answering
  layer's business - the transport-ws admission arm for that
  protocol, the operation task everywhere else - and whichever
  error frame answers it is that layer's to send."
- **Must not change.** n/a (prose only).
- **Proof.**
  `grep -n "upstream's to send" tests/test_routers.py` prints
  nothing (exit 1); the reworded docstring states the answering
  layer per protocol and grades true.
- **Freshness.** None beyond the Trace.

### Low

- **C1 — Observation.** Three module-docstring sentences reason
  about an `__all__` the module does not define. The name
  `__all__` occurs in
  `django_strawberry_framework/consumers.py` only in prose (3
  sites, verified by grep; no assignment exists): "unreachable by
  import rather than merely absent from ``__all__``", "Not exported
  (no ``__all__`` entry here, ...)", and "an ``__all__`` and
  documentation contract, not an import-time one". With no list,
  there are no entries to be absent from and no list half of a
  privacy contract; the actual mechanism is
  documentation-convention-only (plus genuine function-locality for
  the consumer class). Symbol:
  `django_strawberry_framework/consumers.py::DjangoWebSocketHostValidator`
  (primary site) and the module docstring. Grade: stale.
- **Evidence.** `grep -c "__all__"
  django_strawberry_framework/consumers.py` prints 3, all prose;
  `grep -n "^__all__" django_strawberry_framework/consumers.py`
  prints nothing; the Mechanics verdict (R6) is that no list is
  wanted, so the prose must stop presupposing one.
- **Impact.** Bounded clarity: a reader auditing the "unsupported
  to import" claim against the module finds no mechanism where one
  is described. No behavior turns on it.
- **Severity.** Low — misleading mechanism description in a
  private module's docstring, no wire or runtime consequence.
- **Recommendation.** Reword all three sites to
  documentation-contract language with no `__all__` presupposition
  (e.g. "merely private by convention", "Not exported (neither
  documented as public nor named by ...)", "a documentation
  contract, not an import-time one"). Text after is the proposal
  shape; the verifier grades what lands.
- **Must not change.** n/a (prose only).
- **Proof.**
  `grep -n "merely absent from" django_strawberry_framework/consumers.py`
  prints nothing (exit 1);
  `grep -n "no \`\`__all__\`\` entry here" django_strawberry_framework/consumers.py`
  prints nothing (exit 1);
  `grep -n "an \`\`__all__\`\` and documentation contract" django_strawberry_framework/consumers.py`
  prints nothing (exit 1); the reworded sentences grade true.
- **Freshness.** None beyond the Trace.

Handoff: Mechanics review is closed with no Mechanics findings, ten
rejections, and two cross-axis prose leads for this item's Comments
phase. The judgments a verifier could revisit are R1 (the one-sided
arm — the probe reruns verbatim in any copy, and the floor sources
are the two upstream URLs in the Trace) and the C2 Medium (a false
"which layer answers" sentence; Low would also be defensible, the
ladder's letter says Medium). Everything else was discharged by
absence (no settings import, no `TYPE_CHECKING`, no sync twin, no
mode flag, no star-import consumer, no lower-layer importer, no
`_revocation` reader outside the module) or by first-hand upstream
reads at both ends of the range. Two probe-corrected beliefs are
worth keeping: the legacy "dropped op" theory died on upstream's
broad parse catch (both releases), and the close-machine arm I first
read as dead is reachable by prestart cancellation and test-pinned.
The Comments sibling never appeared, so C1/C2 may duplicate its own
leads — Worker-2 discharges by finding, not by reporter. No defects,
no Routed leads out of this item, no production or test edits. Cells:
default and sharded green on the probe; pg inapplicable by
construction with the reason stated above, for the verifier to judge.

## Verification (Mechanics)

Pass 1, address `review/consumers.py/verify-mechanics-1`, scratch
`docs/review/temp-tests/consumers/verify-mechanics-1/`.

Step 1 (tree still carries the sent change): `git diff
cf28b509ad848b9219ef23444c4e99cbd19c1fb8 --
django_strawberry_framework/consumers.py tests/test_routers.py`
is byte-identical to
`docs/review/temp-tests/consumers/diff/pass-1.diff`
(sha256 `8f9551da...44273` both sides, `diff` empty,
HASH_EQUAL). Grading proceeds.

Proof runs (verbatim, expectation-first): none exist in-axis.
This record's `## Findings` are High/Medium/Low all `None`, so
it carries zero in-axis Proof lines; its two Proof lines (C2,
C1) sit under `## Cross-axis (for Comments)` and are graded by
the Comments verifier, not here. Other records' `## Cross-axis
(for Mechanics)`: none — the Performance record states it
carries none, and the Comments record carries no `## Cross-axis`
section at all. No address run was owed and none was made: every
check below is static (grep, git, `--code-digest`, lint
`--check`), which run in the shared tree. (Method note: the
artifact's Implementation header was glanced before this
vacuous-proof determination; with zero in-axis proofs there was
no expectation to bias, and the remainder was read after.)
Numbers to reproduce for this axis: none claimed — Worker-2
reports a prose-only pass with no measurements and no workspace
runs, and no bench figure is bound to this item's change.

Whole item-scoped diff read through this axis: 12 `@@` hunks,
44 insertions / 37 deletions, 2 files, every hunk prose. The 9
`consumers.py` hunks reword the module docstring (import-graph
enumeration, `__all__` site 1, `your own` voice), three
docstring first lines (`revalidate_operation_actor`, the legacy
`handle`, `DjangoWebSocketHostValidator`), the
`_actor_is_current` carve-out comment, the
`_contain_message_loop_failure` paragraph, and the validator's
`__all__` sites 2-3; the 3 `test_routers.py` hunks reword two
docstrings and the C2 comment. `grep -E "^[+-].*(def |class
|import |__all__ *=)"` over the diff matches only the prose
phrase "the class statement is FUNCTION-LOCAL" — no definition,
import, or `__all__` assignment moved. Mechanics verdict per
hunk: no placement, contract, dependency, state, or
duplication impact; no symbol moved or renamed (so no
`--cited-by` sweep is owed, ungated `docs/` citers included);
no consolidation (no DRY gate owed); no guard added or removed.

Behavior preservation: `--code-digest` identity, exit 0 both
sides, digests equal to Worker-2's prefixes —
`consumers.py` `sha256:cf167fe8...48afe`,
`test_routers.py` `sha256:a7be3a89...439` (outputs kept under
this pass's scratch). A revert proof is vacuous with no
production hunk: there is no pre-fix behavior to show worse,
and code-digest identity is the complete preservation proof.
`test_consumers.py` is untouched (empty diff vs ITEM_BASELINE,
`7dee4bed` matches the Trace).

Attacks on this axis (all passing, recorded, nothing owed):

- A1 (C1 kept-half truth): `routers.py:69` still defines
  `__all__ = ("DjangoGraphQLProtocolRouter",)`, and
  `consumers.py` now mentions `__all__` exactly once (:1673,
  the true cross-module reference). The local-list
  presupposition is gone; the kept half is true.
- A2 (R1 one-sided arm intact): `"Query must be a string."`
  still sits only in the `handle_subscribe` path (:1358 under
  :1339); `handle_start` (:1400) still carries no twin, and
  both `handle()` overrides (:1364, :1405) survive. The
  asymmetry verdict stands on unchanged code.
- A3 (dependency direction): module-level imports are still
  stdlib + hard Django (`DisallowedHost`, `HttpRequest`) +
  logger + `ConfigurationError` + truth + `utils/sessions`
  (:380-:395); the three function-local imports survive
  (:1063 error-policy helpers, :1301 `get_user`, :1303
  `session_store_class`); no settings import, no
  `TYPE_CHECKING` block. R5/R6 stand.
- A4 (state privacy, R10): no `_revocation` reader outside
  `consumers.py` (package-wide grep, zero hits elsewhere).
- A5 (import-by-name, R6): the router still imports the four
  names by name (`routers.py:50-55`, deliberate private
  default included); no star import, no root re-export.
- A6 (neighbour consistency): `utils/sessions.py:100` does
  `import dataclasses`, and the auth helper's
  legacy-callable/awaitable arms live at
  `auth/mutations.py:474-477` — the reworded prose now
  matches bodies the code never changed. (Truth grades
  belong to the Comments verifier; noted here only as
  no-behavior-change corroboration.)
- A7 (cells): sharded and pg inapplicable by construction —
  a prose-only diff with code-digest identity touches no
  query, alias, or dialect decision. Verifier concurs with
  the records; cells unverified: none.

Disputes: none recorded — the Implementation states "zero
disputed" and carries no `disputed:` entry. Nothing to judge.

Permanent tests and failability: none added, none owed. A
prose-only change owes no permanent test and no failability
proof (REVIEW.md "Comments"); the test-tier check and
`workspace.py prove` are vacuous, and no `## Pending
execution` command names this axis.

Lint gates (`--check` forms only, all green): `ruff check
<both paths>` — All checks passed; `ruff format --check
<both paths>` — 2 files already formatted;
`check_trailing_commas.py --check <both paths>` — 0
violations; `check_citations.py --check` tree-wide — OK,
1297 citations resolve (1105 in 477 .py files, 192 in
KANBAN.md), the same count Worker-2 baselined pre-edit, so
no rename rotted a citer. Outputs kept under this pass's
scratch.

Verdict: `verified`. No new finding, no routed gap, no
`revision-needed` item. The pass-1 change is prose-only,
digest-proven, lint-green, and mechanics-neutral; every
R1-R10 rejection and every looks-for discharge in this
record stands on unchanged code.

Fingerprints: `consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (pre
`67887b5b`, equals the Trace), `test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (pre
`36c962b1`, equals the Trace), `test_consumers.py`
`7dee4bed...` unchanged. Run ids: none (no workspace
runs; all checks static). Scratch:
`docs/review/temp-tests/consumers/verify-mechanics-1/`
(`code-digest-consumers.txt`,
`code-digest-test_routers.txt`, `lint-ruff-check.txt`,
`lint-ruff-format-check.txt`, `lint-commas-check.txt`,
`lint-citations-check.txt`).

Handoff: Mechanics verification of pass 1 is closed. The
only judgments a later pass could revisit are the
inapplicable-by-construction cell call (prose-only, so
near-mechanical) and the A6 neighbour reads (done as
consistency corroboration, not grading). If a later pass
touches code in this target, the R1 arm check (A2) and the
revocation-privacy grep (A4) rerun verbatim as regression
probes. Nothing is blocked; nothing routes elsewhere.
