# Review · Comments: `django_strawberry_framework/auth/sessions.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5bdea138317eca79e8727c89022df017e3e73d46

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row
naming this target and no Routed lead on this item),
`docs/review/rev-auth__sessions.md` (skeleton: `Status: reviewing`,
blank Path class), all three axis records with every `Handoff:`
and `## Cross-axis` section, then the WHOLE live target. Sibling
`rev-auth__sessions.performance.md` read whole (Status:
no-findings, Path class hot with the per-auth-mutation reason,
13/13 probe bounds `ok`, R1-R7, no `## Cross-axis` section; its
Handoff asks only that a body-touching finding re-run
`probe_hotpath_costs.py` - this record's findings are prose-only,
so the probes stand). Sibling
`rev-auth__sessions.mechanics.md` read whole (Status:
no-findings, 12-entry discharge, R1-R7, no `## Cross-axis`
section; its Handoff flags nothing for Comments). No conflict
with either sibling: Mechanics R4 (sync-bridge loop caveat)
reaches the same verdict this record's prose grade does (the
"never the bridge" sentence states the production invariant,
which holds), and Mechanics R5 (hand-built adapters reach
`classify_transport`) corroborates finding F3's arrival-path
evidence. This record creates
`docs/review/rev-auth__sessions.comments.md`.

Target read whole (279 lines, blob `865d6e70`). Dirty vs HEAD
(concurrent work) and byte-identical to ITEM_BASELINE (`git diff
5bdea138 --` over the target and the own test module is empty),
so the fingerprints below are both what was reviewed and the
baseline. Own test module `tests/auth/test_sessions.py` read
whole (526 lines, blob `b71c84ec`; dirty vs HEAD, identical to
ITEM_BASELINE). `tests/auth/conftest.py` (36 lines, blob
`a5c413ba`) and `tests/auth/_helpers.py` (39 lines, blob
`996762b0`) read whole: no prose about the target's symbols
(the `_sync_boundary_spy` docstring is dispatch-seam prose
the closed mutations item already landed as M6).

Instruments (all static; no workspace run was needed):
`review_inspect.py` census for the target under
`docs/review/temp-tests/auth-sessions/comments/inspect/` (JSON
`docs/review/temp-tests/auth-sessions/comments/sessions.json`);
`build_tree_md.py --list-docstrings` on the target and the own
test module (1 module, 0 breaking, each);
`check_citations.py --paths <file> --substrings --json` (target
11 citations, 0 violations, 11/11 resolved) and `--cited-by` for
every target symbol; the REVIEW.md provenance pattern plus
`used to` / `Tests that` / `Ensures` / voice-pronoun scans over
both files (the only provenance-pattern hits are two kept-class
spec Decision pointers and one pytest-xdist "worker", all
graded true below). Every grade below is against the live text
at the fingerprints in this section, each claim checked against
its body and one real caller or authority: installed channels
4.3.2 (`channels/auth.py` login/logout session branches read),
installed Django 6.1 (`contrib/auth` login/logout),
`docs/SPECS/spec-040-auth_mutations-0_0_13.md` (byte-compatible
envelope wording), `git log -S` / `git grep` dating for the
dangling-pointer claim, and the live-tier twin prose in
`examples/fakeshop/test_query/test_auth_api.py`.

Other-test-module prose about the target's symbols (all read,
all graded): `tests/auth/test_mutations.py::_finalize_schema`
(`auth/sessions.py::require_session` cite, true),
`::_channels_router` third paragraph (CHANNELS_HTTP arm, true -
landed L2 of the closed mutations item, agreed, not re-filed;
paragraphs 1-2 are router-subject, ruled by the closed routers
item's G-finding, not re-litigated),
`test_websocket_signed_cookie_logout_rejected_before_any_mutation`
(prologue ordering, true);
`tests/test_routers.py::test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package`
(import-boundary subject, ruled Low/deferred by the closed
routers item, behavioral claims true, not re-filed),
`::test_a_same_socket_logout_cannot_complete_across_a_parked_protected_send`
(scope-lock exclusion prose, true);
`examples/fakeshop/test_query/test_auth_api.py` sessionless
login/logout docstrings (true - and more precise than the
target on the downstream failure shape; corroborates F2);
`tests/utils/test_imports.py:4` (two-wrapper naming, already
Routed on the plan to the `utils/imports` item, not
re-litigated). No other test module holds prose about the
target's symbols (package-wide symbol census; `tests/auth/`
support files clean; `examples/` hits are only the kanban
constants row and a README note, neither a test module).

Every package module's prose about the target's symbols was
read: `auth/mutations.py` prologue/establish/teardown docstrings
(true - order, lock, capability twins all match the bodies),
`consumers.py` module docstring + `_SCOPE_LOCK_KEY` twin comment
+ revalidation docstring (true, incl. the "re-export" wording:
the attribute import demonstrably worked), `utils/sessions.py`
module docstring + four `scope_session_lock` cites (true),
`utils/permissions.py::_is_request` (true),
`routers.py` hint comment (true), `utils/imports.py:39`
census ("the router's three, the auth session boundary's one",
verified true: three `CHANNELS_FLOOR` interpolations in
`routers.py`, one here), `utils/imports.py:122` guard example
(true, illustrative). No stale package-module prose: no
`Routed:` leads from this pass. (The plan's existing
`require_drf` "three guards" lead enumerates this module's
`require_channels` but concerns `rest_framework` prose, owned
by that integration item.)

No module first line is touched by any finding, so no TREE.md
render is owed.

Cells: default, sharded, and pg are all `inapplicable by
construction` for this Comments pass (no database-reaching
probe; every Proof is a static count plus a grade judgment;
Worker-2's prose edits owe `--code-digest` identity, not cell
runs). Cells unverified: none. Run ids: none (no
`workspace.py` runs).

Fingerprints (`git hash-object` of every file whose body was
read): `django_strawberry_framework/auth/sessions.py`
`865d6e704d2df50bcad465ad3005eccb39e8c545` (live, whole, dirty,
== ITEM_BASELINE); `tests/auth/test_sessions.py`
`b71c84ecd4dc90b9af37518d186716f1d64d9a96` (live, whole, dirty,
== ITEM_BASELINE); `tests/auth/conftest.py`
`a5c413ba57dfc3f97e4f3743f04851977de777de` (live, whole);
`tests/auth/_helpers.py`
`996762b0db5d527da12f636342a5ba45d86c99ed` (live, whole);
`tests/auth/test_mutations.py`
`4cb499820cbed5163777099e9c9804cf7a523b50` (cite + router-harness
+ ordering regions); `tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (import-boundary +
parked-send regions, module-import census);
`tests/utils/test_imports.py`
`e39ac485ca7253ebd1ec2f07b26d164a480ac3d7` (line 4);
`examples/fakeshop/test_query/test_auth_api.py`
`17fc9ddb7c31c5ae936795fe524f233b3a1e4304` (module docstring +
sessionless regions);
`django_strawberry_framework/auth/mutations.py`
`98ae63f1965a08d28332ae6e24aa24ea39d9d511` (prologue, establish,
teardown, bridge regions);
`django_strawberry_framework/auth/__init__.py`
`2e480818424d4b130e613e3e2da027aaad7144ad` (whole);
`django_strawberry_framework/consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (prose regions);
`django_strawberry_framework/utils/sessions.py`
`21041723250de58876d95eaec14e1078a6f16a4f` (module docstring,
`scope_key`, cites); `django_strawberry_framework/utils/permissions.py`
`1c9cfd398e6096e03bda82ba93dfd66a6d2fb890` (adapter, resolver,
`_is_request`); `django_strawberry_framework/utils/imports.py`
`291ecedd30c7d8af9c007758112e867c09d031eb` (floor comment,
guard); `django_strawberry_framework/utils/lazy.py`
`770f36ae9cc9eec1201e5daece196ed038d758d1` (cited seam);
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9` (cited seams);
`django_strawberry_framework/routers.py`
`299da0f541f184ec833e01a4d9c83cc0d7880d15` (hint block);
`docs/review/review-0_0_15.md`
`4cdb69bdad191fcb3fda7c99fb0b0cecbed76128` (plan + ledger);
`docs/review/rev-auth__sessions.md`
`df7948c97badf5354fbebf7dbc1063444aa74825` (skeleton);
`docs/review/rev-auth__sessions.performance.md`
`7467401fb32760ca65e2748d5cb9f1aa921a7dec` (whole);
`docs/review/rev-auth__sessions.mechanics.md`
`aaed2391526c2b8081c44992164e6feb42e77646` (whole);
`docs/review/rev-auth__mutations.comments.md`
`46dd3080dbf6e2e8552d98ae4b2992f7363c13da` (shape + L2 + R1/R2
regions); `docs/review/rev-routers.comments.md`
`8f0c06da85119d2e988e8b9e699f4f8700a65038` (import-boundary +
G-finding regions). A finding's Freshness lists only files
beyond these: none.

## Findings

### High

None.

### Medium

#### F1: module docstring says the engine expression is "single-sited OUTSIDE this package"

- Observation: the capability paragraph of the module
  docstring says the engine expression "is single-sited OUTSIDE
  this package". Under the repository's standing reading of
  "package" (the distribution: "package root", "package-tier",
  and this same docstring's own "neither ``auth.__all__`` nor
  the package root names it"), that is false:
  `django_strawberry_framework/utils/sessions.py::session_store_class`
  lives INSIDE the distribution. The paragraph means "outside
  the ``auth`` subpackage" (its next two sentences say "must not
  import ``auth`` at all" and "an ``auth``-hosted resolver",
  and the `utils/sessions.py` twin paragraph writes "The
  ``auth`` package is structurally opt-in" explicitly), but as
  written the sentence contradicts its own paragraph.
- Evidence: docstring read against the import below it
  (`from ..utils.sessions import ... session_store_class`)
  and the twin paragraph in
  `django_strawberry_framework/utils/sessions.py`
  (module docstring, "Why it lives here" section).
- Impact: a reader auditing the opt-in boundary goes looking
  for an engine resolver outside the distribution that does
  not exist, instead of the `utils` owner one import away.
- Severity: Medium. Misleading module-docstring sentence on
  internal code.
- Recommendation: reword to "OUTSIDE the ``auth``
  subpackage"; see text-after.
- Must not change: n/a.
- Proof: `grep -c "OUTSIDE this package" django_strawberry_framework/auth/sessions.py` prints `0` (1 today); the rewritten sentence earns grade true. Run at `review/auth/sessions.py/verify-comments-1`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py` module docstring (capability paragraph).
- Grade: stale.
- Text-before:
  `They are built on ``utils/sessions.py::session_store_class``, imported below: the engine expression stays single-sited, but it is single-sited OUTSIDE this package, because its other caller ...`
- Text-after:
  `They are built on ``utils/sessions.py::session_store_class``, imported below: the engine expression stays single-sited, but it is single-sited OUTSIDE the ``auth`` subpackage, because its other caller ...`

#### F2: two sites name the downstream failure "None.cycle_key() AttributeError"

- Observation: the module-docstring pre-check bullet and the
  `django_strawberry_framework/auth/sessions.py::require_session`
  docstring both say the absence would otherwise surface as a
  raw "``None.cycle_key()`` ``AttributeError``". That shape is
  wrong on every natural path. Django: a request whose
  `SessionMiddleware` never ran has NO `session` attribute, so
  the native call fails as a missing-attribute `AttributeError`
  - the live tier pins the exact shape as
  "`'WSGIRequest' object has no attribute 'session'`"
  (`examples/fakeshop/test_query/test_auth_api.py::test_sessionless_login_refuses_with_the_error_naming_both_middleware_stacks`).
  Channels: a scope with no session key never reaches a
  session call - installed `channels/auth.py` raises
  `ValueError` ("Cannot find session in scope" /
  "Login cannot find session in scope") first. Logout: the
  native call is `flush()`, never `cycle_key()`, on both
  engines. The true content (actionable configuration error
  instead of a raw downstream failure) stands; only the named
  shape is false.
- Evidence: installed channels 4.3.2 `channels/auth.py`
  login/logout bodies read (session-key guard before any
  session call; `cycle_key` on the login leg only, `flush`
  on logout); installed Django `contrib/auth` login/logout
  read (`request.session` attribute access first); live-tier
  sessionless docstrings read (true, more precise twin).
- Impact: a reader tracing the pre-check's purpose learns a
  downstream shape that matches none of the four
  login/logout x Django/Channels paths, and the project's own
  live-tier prose contradicts the target.
- Severity: Medium. False stated downstream shape in two
  docstrings on internal code.
- Recommendation: name the real per-path shapes; see
  text-after (both sites).
- Must not change: n/a.
- Proof: `grep -c "None.cycle_key" django_strawberry_framework/auth/sessions.py` prints `0` (2 today); both rewritten sites earn grade true. Run at `review/auth/sessions.py/verify-comments-2`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py` module docstring (pre-check bullet) + `django_strawberry_framework/auth/sessions.py::require_session` docstring.
- Grade: stale.
- Text-before (module bullet):
  `becomes an actionable, transport-specific configuration error instead of a downstream ``None.cycle_key()`` ``AttributeError```
- Text-after (module bullet):
  `becomes an actionable, transport-specific configuration error instead of a raw downstream failure (a missing ``session`` attribute on Django, ``channels.auth``'s ``ValueError`` when the scope has no ``session`` key)`
- Text-before (`require_session` sentence):
  `Without this pre-check the absence surfaces downstream as a raw ``None.cycle_key()`` ``AttributeError`` during the native login/logout; the pre-check converts it into a transport-specific configuration error.`
- Text-after (`require_session` sentence):
  `Without this pre-check the absence surfaces downstream as a raw failure during the native login/logout (a missing ``session`` attribute on Django, ``channels.auth``'s ``ValueError`` when the scope has no ``session`` key); the pre-check converts it into a transport-specific configuration error.`

#### F3: the install-hint comment misstates the arrival path, the adapter's type discipline, and the later failure

- Observation: the `_CHANNELS_INSTALL_HINT` comment's second
  sentence - "A Channels-shaped context can only reach this
  module through ``request_from_info``'s duck-typed adapter, so
  if it arrives without the optional dependency the
  classification raises this rather than swallowing the failure
  into a later ``AttributeError``" - is wrong three ways.
  (a) "only through ``request_from_info``": a directly
  constructed `ChannelsRequestAdapter` reaches
  `django_strawberry_framework/auth/sessions.py::classify_transport`
  fine - every Channels row of the own test module does
  exactly that, and the sibling Mechanics record's R5
  reasons about hand-built adapters reaching it. (b)
  "duck-typed adapter": the adapter is classified by REAL
  class precisely because attribute sniffing (duck typing)
  is unreliable under its `__getattr__` delegation - the
  module docstring's central doctrine sentence says so. (c)
  "a later ``AttributeError``": without the guard,
  classification succeeds (it needs no channels import) and
  the failure surfaces later as a hint-less `ImportError`
  at the unguarded `from channels.auth import ...` in the
  establish/teardown helpers, never an `AttributeError`.
  The comment's first sentence (single hint, mirrors the
  router's, single-sited per `utils/imports.py`) is true
  and stays.
- Evidence: comment read against
  `django_strawberry_framework/auth/sessions.py::classify_transport`
  (takes any object; tests pass hand-built adapters),
  `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter.__getattr__`,
  and `django_strawberry_framework/auth/mutations.py::_channels_http_login_establish`
  / `::_channels_logout` (unguarded channels imports).
- Impact: a reader learns a false exclusivity (blocking a
  legitimate direct-construction call shape in their mental
  model), a type-discipline label that inverts the module's
  own doctrine, and a downstream shape that cannot occur.
- Severity: Medium. Triply false comment sentence on
  internal code.
- Recommendation: rewrite the second sentence as the
  present-tense rule; see text-after.
- Must not change: n/a.
- Proof: `grep -cE "duck-typed|can only reach this module|into a later" django_strawberry_framework/auth/sessions.py` prints `0` (2 today); the rewritten comment earns grade true. Run at `review/auth/sessions.py/verify-comments-3`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::_CHANNELS_INSTALL_HINT` comment.
- Grade: stale.
- Text-before:
  `A Channels-shaped context can only reach this module through ``request_from_info``'s duck-typed adapter, so if it arrives without the optional dependency the classification raises this rather than swallowing the failure into a later ``AttributeError``.`
- Text-after:
  `A Channels-shaped context reaches this boundary as a real-class ``ChannelsRequestAdapter`` (built by ``request_from_info`` or directly), so if it arrives without the optional dependency the classification raises this actionable error at the boundary rather than letting the failure surface later as a hint-less ``ImportError`` at the ``channels.auth`` import.`

#### F4: "(auth plan root cause 3)" points at a document that never existed

- Observation: the
  `django_strawberry_framework/auth/sessions.py::login_supported`
  and `::logout_supported` docstrings both close with the
  parenthetical "(auth plan root cause 3)". No "auth plan"
  exists on the reader's path: the phrase occurs nowhere in
  the package, tests, specs, README, GLOSSARY, or KANBAN
  outside these two docstrings, and `git grep "auth plan"`
  at the introducing commit (`c8346750`, July 2026) already
  returns only this file - the pointer was dangling at
  birth. The causal sentences it trails already state the
  rule in present tense (no replacement cookie over an
  established socket), so the parenthetical adds only a
  hunt for a nonexistent plan.
- Evidence: repo-wide `auth plan` / `root cause 3` census
  (two hits, both here); `git log -S` dating (introduced
  `c8346750`, never defined); both docstrings read whole
  (causal sentences true, consistent with the
  `_WEBSOCKET_LOGIN_UNSUPPORTED` /
  `_WEBSOCKET_LOGOUT_UNSUPPORTED` comments in
  `django_strawberry_framework/auth/mutations.py`).
- Impact: a reader following the pointer searches the tree
  for a root-cause analysis that is not there, instead of
  trusting the true sentence beside it.
- Severity: Medium. Dangling process pointer in two
  docstrings on internal code.
- Recommendation: delete the parenthetical at both sites;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c "auth plan root" django_strawberry_framework/auth/sessions.py` prints `0` (2 today - the logout site wraps "root/cause" across lines); both docstrings earn grade true. Run at `review/auth/sessions.py/verify-comments-4`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::login_supported` docstring + `django_strawberry_framework/auth/sessions.py::logout_supported` docstring.
- Grade: process provenance.
- Text-before (login):
  `... so it could only authenticate the in-memory scope while silently failing to establish a reusable browser session (auth plan root cause 3).`
- Text-after (login):
  `... so it could only authenticate the in-memory scope while silently failing to establish a reusable browser session.`
- Text-before (logout):
  `... but a signed-cookie WebSocket has no server-side record to revoke and cannot delete or replace the browser cookie over an established socket (auth plan root cause 3).`
- Text-after (logout):
  `... but a signed-cookie WebSocket has no server-side record to revoke and cannot delete or replace the browser cookie over an established socket.`

### Low

#### F5: "which had the same body" narrates the sharing in past tense

- Observation: the `_SCOPE_LOCK_MESSAGES` comment says the
  helper is "shared with the WebSocket revalidation state,
  which had the same read / create-with-no-await /
  validate-or-fail-closed body". Both callers share
  `django_strawberry_framework/utils/sessions.py::scope_singleton`
  NOW - the revalidation state still has that body through
  the helper. "had" reads as change history (each side had
  its own copy before the sharing); present tense states
  the rule.
- Evidence: comment read against
  `django_strawberry_framework/utils/sessions.py::scope_singleton`
  (shared helper, both call sites live) and the
  `connection_actor_state` caller.
- Impact: one-word temporal wart in an otherwise
  present-tense sharing rationale.
- Severity: Low. Past-tense provenance flavor; the sharing
  claim itself is true.
- Recommendation: "had" to "shares"; see text-after.
- Must not change: n/a.
- Proof: `grep -c "which had the same" django_strawberry_framework/auth/sessions.py` prints `0` (1 today); the rewritten comment earns grade true. Run at `review/auth/sessions.py/verify-comments-5`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::_SCOPE_LOCK_MESSAGES` comment.
- Grade: process provenance.
- Text-before:
  `(shared with the WebSocket revalidation state, which had the same read / create-with-no-await / validate-or-fail-closed body)`
- Text-after:
  `(shared with the WebSocket revalidation state, which shares the same read / create-with-no-await / validate-or-fail-closed body)`

#### F6: classify docstring names `request` as the checked object; the body checks the unwrapped candidate

- Observation: the
  `django_strawberry_framework/auth/sessions.py::classify_transport`
  docstring opens "Begins with ``truth.is_instance(request,
  ChannelsRequestAdapter)``", but the body first runs
  `candidate = unwrap_lazy_object(request)` and checks the
  CANDIDATE. For a lazy proxy the two differ observably (a
  `SimpleLazyObject` is not an adapter by real class, yet
  the body classifies what it wraps - the next sentence's
  whole subject). The module docstring states the operand
  correctly ("a real-class check ..., on the object a Django
  lazy proxy wraps"), so the function docstring disagrees
  with its own module docstring on the spelling that
  matters exactly for the lazy case.
- Evidence: docstring read against the body (unwrap line
  precedes both `truth.is_instance` calls) and the module
  docstring's classification paragraph; lazy-proxy test
  (`test_a_django_lazy_request_resolves_and_classifies_as_the_request_it_wraps`
  in `tests/auth/test_sessions.py`) pins the behavior.
- Impact: a reader copying the spelled check tests the
  proxy instead of the wrapped object - the one shape the
  sentence exists to rule on.
- Severity: Low. The docstring as a whole still guides
  correctly (sentence two states the lazy semantics), so
  this is operand-spelling drift, not a misleading rule.
- Recommendation: name the candidate; see text-after.
- Must not change: n/a.
- Proof: `grep -c "truth.is_instance(request, ChannelsRequestAdapter)" django_strawberry_framework/auth/sessions.py` prints `0` (1 today); the rewritten docstring earns grade true. Run at `review/auth/sessions.py/verify-comments-6`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::classify_transport` docstring.
- Grade: stale.
- Text-before:
  `Begins with ``truth.is_instance(request, ChannelsRequestAdapter)`` (attribute-presence sniffing is unreliable under the adapter's ``__getattr__`` delegation).`
- Text-after:
  `Begins with ``truth.is_instance`` against ``ChannelsRequestAdapter``, applied to the ``unwrap_lazy_object`` candidate (attribute-presence sniffing is unreliable under the adapter's ``__getattr__`` delegation).`

#### F7: `uses_signed_cookie_sessions` first line is descriptive, not imperative

- Observation: "True when the configured session engine is
  Django's signed-cookie engine." Function first lines are
  imperative; ruff leaves mood unchecked, so the reviewer is
  the gate (run precedent: the queries L1 imperative fix).
- Evidence: docstring first line read; body is a predicate
  function.
- Impact: mood consistency across the module's eight
  function docstrings.
- Severity: Low. Clarity only.
- Recommendation: imperative opener; see text-after.
- Must not change: n/a.
- Proof: `grep -c '"""True when the configured session engine' django_strawberry_framework/auth/sessions.py` prints `0` (1 today); the rewritten docstring earns grade true. Run at `review/auth/sessions.py/verify-comments-7`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::uses_signed_cookie_sessions` docstring.
- Grade: duplicates the code.
- Text-before:
  `True when the configured session engine is Django's signed-cookie engine.`
- Text-after:
  `Return True when the configured session engine is Django's signed-cookie engine.`

#### F8: `login_supported` first line is descriptive, not imperative

- Observation: "Whether ``login`` can truthfully establish
  a durable session on ``transport``." Same mood rule as F7.
- Evidence: docstring first line read; body is a predicate
  function.
- Impact: mood consistency across the module's eight
  function docstrings.
- Severity: Low. Clarity only.
- Recommendation: imperative opener; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Whether ``login`` can' django_strawberry_framework/auth/sessions.py` prints `0` (1 today); the rewritten docstring earns grade true. Run at `review/auth/sessions.py/verify-comments-8`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::login_supported` docstring.
- Grade: duplicates the code.
- Text-before:
  `Whether ``login`` can truthfully establish a durable session on ``transport``.`
- Text-after:
  `Return whether ``login`` can truthfully establish a durable session on ``transport``.`

#### F9: `logout_supported` first line is descriptive, not imperative

- Observation: "Whether ``logout`` can truthfully
  invalidate the session on ``transport``." Same mood rule
  as F7.
- Evidence: docstring first line read; body is a predicate
  function.
- Impact: mood consistency across the module's eight
  function docstrings.
- Severity: Low. Clarity only.
- Recommendation: imperative opener; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Whether ``logout`` can' django_strawberry_framework/auth/sessions.py` prints `0` (1 today); the rewritten docstring earns grade true. Run at `review/auth/sessions.py/verify-comments-9`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/sessions.py::logout_supported` docstring.
- Grade: duplicates the code.
- Text-before:
  `Whether ``logout`` can truthfully invalidate the session on ``transport``.`
- Text-after:
  `Return whether ``logout`` can truthfully invalidate the session on ``transport``.`

## Looks-for discharge

Every Comments list entry, each a finding, `none` + reason,
or rejection + trigger:

- Every docstring and comment in the target: graded. F1-F9
  filed; everything else true. True roll: module first line
  (TREE.md row, `--list-docstrings` clean) and the
  classification doctrine, lock, and opt-in paragraphs (all
  verified against the bodies, `auth/__init__.py`, and the
  `utils/sessions.py` twin); `Transport` class docstring
  (descriptive, correct per-mode paths);
  `require_channels` docstring (sole call site verified,
  channels-free import pinned by the subprocess test);
  `classify_transport` docstring save F6 (order, adapter
  forcing, both rejections match the body);
  `require_session` docstring save F2 (collapse shape, kept
  `"session"` substring pinned by tests, envelope-scope
  parenthetical consistent with spec-040);
  `_require_mutable_scope` docstring (read-only `Mapping`
  typing verified, fail-loud reason sound);
  `scope_session_lock` docstring (single-helper claim
  verified - sole acquisition site pair in
  `auth/mutations.py`; invariant-12 content stated at the
  owner per the closed mutations pass; atomicity sentence
  matches the await-free helper; loop caveat states the
  production invariant, which holds - see Rejected);
  `uses_signed_cookie_sessions` body paragraphs (capability
  rationale + subclass recognition, pinned by tests);
  login/logout capability paragraphs save F4 and mood
  (consistent with the mutations rejection comments);
  `_SCOPE_LOCK_KEY` comment (matches the `scope_key`
  builder and the consumers twin).
- Every docstring and comment in the own test module
  (`tests/auth/test_sessions.py`, graded whole): all true.
  Module docstring (live-tier sessionless pointer verified
  present, soft-dependency discipline named correctly,
  subprocess proof described accurately; "the running
  worker" is the pytest-xdist worker, legitimate);
  `_adapter` docstring (imperative, true); section banners
  (accurate); all twelve behavior docstrings (each states
  the expected behavior, none opens "Tests that"/"Ensures",
  each verified against its body - incl. the waiter-queue
  barrier, the `-W error` teardown rationale, the
  subclass-`issubclass` mechanism, and the no-global-registry
  namespace census); inline comments (raw-literal pin
  verified byte-equal to the `scope_key` output, waiter
  facts, pragma reasons). No `we`/`you`/`I`, no line
  cites, no dead names.
- Prose other test modules hold about the target's symbols:
  graded true throughout (census in Trace); the two
  history-flavored sites (routers import-boundary docstring,
  `_channels_router` paragraphs 1-2) were ruled by their
  closed owning items and are not re-litigated.
- Stale prose in another package module: none found (full
  census in Trace, incl. the verified-true
  `utils/imports.py` install-hint census). No `Routed:`
  leads.
- Module first line (one line, one sentence, terminal `.`,
  no `e.g.`/`i.e.`): true, both graded files
  (`--list-docstrings` 0 breaking each).
- Function/method/class first-line mood: F7/F8/F9 filed;
  the other five function first lines imperative, the
  `Transport` class first line descriptive - all true.
- Public symbol without a docstring: none (every public
  name documented; constants carry `#` comments).
- Docstring restating the signature or hints: none (each
  docstring adds raising behavior, ordering, or contract
  beyond the signature).
- "we"/"you"/"I": none (grep over both files, zero hits).
- Test docstring mood ("Tests that"/"Ensures"): none.
- Source reference by line number or dead name: F4 filed
  (dead "auth plan" name); no line-number cites anywhere;
  all 11 `path::Symbol` cites in the target resolve.
- Stated reason contradicted by the body: F2, F3, F6
  filed; all other reasons verified.
- Unrecorded intentional separation / rejected
  consolidation: none (the lock/lease split and the
  engine-in-`utils` split are both recorded at their
  owners with matching twins).

## Rejected

- The `scope_session_lock` loop-caveat closing claim
  ("Long-lived multiplexed scopes (WebSocket) only ever
  reach the native async body, never the bridge").
  Rejected: states the production invariant, which holds -
  the router's WebSocket consumer is async and both async
  bodies await Channels scopes natively, so no production
  path reaches the sync bridge with a multiplexed scope;
  the sync body's "for completeness" arm is dead in
  production by that routing, exactly as the sibling
  Mechanics R4 rules. Trigger: a multiplexed scope
  reaching repeated sync bridges.
- "a directly-invoked ``SyncGraphQLHTTPConsumer`` builds a
  new scope per request" (agency: the server builds the
  scope). Rejected: the load-bearing content (one fresh
  scope per request; the lock never crosses loops) is true
  and no code cites the consumer as a scope factory; the
  verb is style-level. Trigger: none.
- "tests it with ``issubclass``" (subclass-engine test
  docstring; the body calls `truth.is_subclass`). Rejected:
  behavioral description, true for every input the check
  can see (`session_store_class` returns a class or raises;
  the real-MRO/non-class nuance is load-bearing nowhere
  here). Trigger: a non-class reaching the check.
- "the running worker" (subprocess-test docstring).
  Rejected: the pytest-xdist worker, a real runtime entity,
  not review attribution. Trigger: none.
- "recognises" spelling (lazy-proxy test docstring).
  Rejected: standing package vocabulary per the closed
  mutations pass. Trigger: none.
- The bare `# pragma: no cover` on the corrupted-slot test
  body. Rejected: legitimate (the `__aenter__` raise never
  reaches the body); the missing reason beside two
  reasoned pragmas is style. Trigger: none.
- "public scope-key bytes" (raw-literal comment; the
  constant is private). Rejected: the bytes ARE
  externally visible on the consumer's scope, and the pin
  works exactly as described. Trigger: none.
- `consumers.py` "``auth/sessions.py``'s re-export of it".
  Rejected: referentially true - the attribute import
  demonstrably worked (it is the old import the boundary
  test names). Trigger: none.
- "supportable" vs "supported" wobble in the
  `logout_supported` docstring. Rejected: same meaning in
  context. Trigger: none.
- `tests/test_routers.py` import-boundary history
  sentences. Not re-litigated: ruled Low/deferred by the
  closed routers item (owning pass). Trigger: that item
  reopens.
- `tests/auth/test_mutations.py::_channels_router`
  paragraphs 1-2 ("Through 0.0.14" / "no longer").
  Not re-litigated: router-subject, ruled by the closed
  routers item's G-finding. Trigger: that item reopens.
- `tests/utils/test_imports.py:4` two-wrapper naming.
  Not duplicated: already Routed on the plan to the
  `utils/imports` item. Trigger: none.
- The plan's `require_drf` "three guards" lead (enumerates
  this module's `require_channels`). Owned by the
  `rest_framework` integration item; this record's
  `require_channels` docstring needs no count. Trigger:
  none.

Handoff: Comments review closes findings-recorded with 4
Medium and 5 Low, all prose-only in the target (no test
edits proposed; the own test module grades true throughout).
The load-bearing corrections are F2 (downstream shape the
live tier contradicts), F3 (arrival path + type discipline +
later failure), and F4 (dangling plan pointer); F1, F5, F6
are single-sentence precision fixes and F7-F9 mood. No
defects, no `Routed:` leads (every neighboring prose site
verified true or already owned elsewhere), no `## Cross-axis`
section (nothing out-of-axis found), no TREE.md render owed
(no first-line change). If Worker-2's rewording moves any
cited symbol it must re-run `--cited-by`, but none is
proposed. Open threads: none. Scratch kept under
`docs/review/temp-tests/auth-sessions/comments/` (`inspect/`
overview + stripped source, `sessions.json`).

## Verify comments

Pass 1 (implement: Comments F1-F9 prose-only in the target).
Fully static; no workspace copy bound. Required reading done in
order (AGENTS.md, START.md, REVIEW.md, worker-2.md, the plan
incl. `## Owned changes`, all four records with every Handoff,
`docs/review/temp-tests/auth-sessions/diff/pass-1.diff` whole,
then the live target). HEAD at verify time
0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62; target
e50011e6cae837a7b1322d704a7f8adbb69bcec3.

Per-finding verdicts (Proof = the record's grep; grade = the
whole landed docstring/comment against its body and one
authority):

- F1: pass. Proof `grep -c "OUTSIDE this package"` prints `0`
  (was 1); landed `OUTSIDE the ``auth`` subpackage` x1
  (line 37). Grade true: the owner
  `utils/sessions.py::session_store_class`
  (`utils/sessions.py:191`) lives inside the distribution but
  outside the `auth` subpackage, matching the paragraph's own
  "must not import ``auth``" sentences and the
  `utils/sessions.py` twin ("The ``auth`` package is
  structurally opt-in").
- F2: pass. Proof `grep -c "None.cycle_key"` prints `0`
  (was 2); landed per-path shapes at both sites (module
  bullet lines 28-30; `require_session` lines 173-176; the
  `channels.auth`/`ValueError` pair split across lines
  174-175, occurrences 2/2). Grade true against installed
  channels 4.3.2 + Django 6.1: `channels/auth.py::login`
  raises `ValueError` ("Cannot find session in scope") and
  `::logout` raises `ValueError` ("Login cannot find session
  in scope") before any session call; `cycle_key()` sits on
  the login leg only, `flush()` on logout; Django's
  `contrib.auth.login` touches `request.session`
  first (line 177), so a sessionless request fails as a
  missing-attribute `AttributeError`, pinned live at
  `examples/fakeshop/test_query/test_auth_api.py:727`
  ("'WSGIRequest' object has no attribute 'session'").
- F3: pass. Proof `grep -cE "duck-typed|can only reach this
  module|into a later"` prints `0` (was 2); landed comment
  lines 71-75. All three corrections grade true: (a) arrival
  path - `tests/auth/test_sessions.py:58` `_adapter`
  directly constructs `ChannelsRequestAdapter(object(),
  scope)`, every Channels row; (b) type discipline -
  "real-class" matches the module doctrine (line 13) and the
  body `truth.is_instance` checks (lines 143/157);
  (c) later failure - the unguarded `from channels.auth
  import ...` sites at `auth/mutations.py:626,844` raise a
  hint-less `ImportError`, and classification itself needs no
  channels import, so it cannot fail as `AttributeError`.
- F4: pass. Proof `grep -c "auth plan root"` prints `0`
  (was 2); both parentheticals deleted, the causal sentences
  intact and terminal-`.` (login lines 266-269, logout lines
  277-280). Repo-wide `.py` retirement sweep for all six
  retired phrases: 0 hits (the only remaining matches are the
  stale `__pycache__/sessions.cpython-314.pyc` bytecode, not
  source; other-file "duck-typed" hits are legitimate
  vocabulary about genuinely duck-typed contracts, outside
  this item's fence).
- F5: pass. Proof `grep -c "which had the same"` prints `0`
  (was 1); landed `which shares the same` x1 (line 88).
  Grade true: `scope_singleton` has exactly two live call
  sites - `auth/sessions.py:234` (the lock) and
  `utils/sessions.py:308` (inside `connection_actor_state`,
  the WebSocket revalidation state) - so the sharing is
  present tense.
- F6: pass. Proof `grep -c "truth.is_instance(request,
  ChannelsRequestAdapter)"` prints `0` (was 1); landed
  `unwrap_lazy_object` candidate spelling (lines 128-130).
  Grade true against the body: `candidate =
  unwrap_lazy_object(request)` (line 142) precedes both
  `truth.is_instance` calls, and the sentence now agrees with
  the module docstring's classification paragraph.
- F7: pass. Proof `grep -c '"""True when the configured
  session engine'` prints `0` (was 1); landed `Return True
  when ...` x1 (line 246). Imperative; body paragraphs
  unchanged.
- F8: pass. Proof `grep -c 'Whether ``login`` can'` prints
  `0` (was 1); landed `Return whether ``login`` can ...` x1
  (line 264). Imperative.
- F9: pass. Proof `grep -c 'Whether ``logout`` can'` prints
  `0` (was 1); landed `Return whether ``logout`` can ...` x1
  (line 275). Imperative.

Cross-checks:

- `check_citations.py --paths <target> --substrings --json`:
  checked 11, violations 0, warnings 0, 11/11 resolved (same
  count as review time).
- Provenance sweep over every added line (REVIEW.md pattern
  plus `used to` / `Tests that` / `Ensures` / `we`/`you`/`I`):
  0 hits.
- `--code-digest ITEM_BASELINE:<target> <target>`: exit 0,
  `sha256:d54bef37...` both sides - prose-only proven.
- Prose-diff tool output under `verify-comments-1/diff/`:
  5 prose hunks, 0 `[code changed too]` markers.
- `pass-1.diff` is byte-identical to `git diff ITEM_BASELINE
  -- <target>`; `git diff ITEM_BASELINE --stat` over
  package + tests + examples names the target only
  (+23/-18); the own test module is byte-identical to the
  baseline (`b71c84ec`); no TREE.md render owed (no
  first-line change) and none touched.
- Whole-docstring re-grade: every changed site's full
  docstring/comment read true (module docstring, hint
  comment, lock comment, `classify_transport`,
  `require_session`, `uses_signed_cookie_sessions`,
  `login_supported`, `logout_supported`).

New defects: none. The sibling Handoffs asked only for a
probe re-run if a body-touching finding landed; none did
(code-digest identity), so the Performance 13/13 bounds and
the Mechanics no-findings verdicts stand untouched.

Scratch: `docs/review/temp-tests/auth-sessions/verify-comments-1/`
(`notes.md` command log, `live-target.diff`, `diff/` prose diff).

Status: verified
