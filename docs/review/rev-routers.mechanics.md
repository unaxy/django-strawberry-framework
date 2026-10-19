# Review · Mechanics: `django_strawberry_framework/routers.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=eb71162ba7be2797bf4dbdb4e7d24da989e96eed

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-routers.md` (skeleton: `Status: reviewing`, blank Path
class), sibling axis records, then the whole live target. Sibling
`rev-routers.performance.md` read whole (Status: no-findings, Path
class cold, six rejections R1-R6, no `## Cross-axis` section at all;
its Handoff flags R1's double compile and R5's unmemoized module hook
as the revisitable judgments — both read here as contract-load-bearing
and cold, no Mechanics content — and judges the plan's Routed lead
out-of-axis). Sibling `rev-routers.comments.md` did not exist at write
time; no Handoff or Cross-axis text was available from it.

The plan's Routed lead on this item (consumers.py Comments wordings in
`tests/test_routers.py`: `_ws_communicator` "now that the HTTP branch
no longer carries one" / "the branch now carries two independent
handshake checks"; `test_the_websocket_pattern_is_keyword_only_...`
"no longer" Decision-4 quotation; `test_a_factory_that_raises_from_its_body_...`
"your factory") was read and judged in-axis-scope: all three wordings
describe structure this record verifies as true (the HTTP value is the
bare Django application with no session middleware; the WebSocket
branch carries the Host check outside the Origin check; the convention
is normalized while the factory body is not), so they carry no
mechanics defect, misplaced rule, or contract divergence. They are
wording, tense, and voice — Comments scope — and are routed onward to
this item's Comments pass, which grades that module whole. Recorded
under `## Cross-axis (for Comments)` as a routing note, not a finding.

Target read whole (543 lines, blob `e18772f7`, same bytes the
Performance record fingerprinted). The target is dirty vs HEAD
(`+24/-18`, concurrent work; reviewed as it stands per the dispatch,
no hunk attributed here): the whole dirty content is the
truthful-reads migration (`describe_value` to `truth.describe`,
`isinstance`/`issubclass`/`inspect.iscoroutine` to `truth` readers,
`except BaseException` / `except Exception` narrowed to the documented
tuples) on construction and raise paths only. Live bytes still equal
ITEM_BASELINE (`git diff eb71162b -- <target>` empty at write time).
Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/routers/mechanics/inspect/` (json
`docs/review/temp-tests/routers/mechanics/routers.json`).

Callers and neighbours traced by first-hand reads (fingerprints below):
no package module imports this target — the only in-repo importers are
`tests/test_routers.py` and one row in
`tests/mutations/test_write_transaction.py` (a socket harness
constructing the router with a never-reached `_no_http_application`);
the package root re-exports no routers name (read whole);
`django_strawberry_framework/consumers.py` (window default, validator,
consumer factory, Host validator prose — the deliberate private-default
import lands here); `django_strawberry_framework/utils/imports.py`
(whole — the single optional-import owner); `django_strawberry_framework/utils/truth.py`
(the `is_type` / `is_instance` / `is_subclass` readers this module
leans on); `django_strawberry_framework/auth/sessions.py` (the second
`require_channels` wrapper and its feature-keyed hint);
`django_strawberry_framework/rest_framework/__init__.py` (whole — the
`require_drf` twin and its guard census);
`django_strawberry_framework/middleware/debug_toolbar.py`
(`require_debug_toolbar` — the fourth wrapper);
`django_strawberry_framework/types/base.py::_validate_globalid_callable`
(the signature-bind pre-check twin);
`django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable`
(the coroutine-disposal twin); `django_strawberry_framework/views.py`
(module docstring — the URLconf-independence half of the transport
contract); `tests/test_routers.py` (construction, seam, window,
concurrency, absence, and handshake-independence rows);
`tests/test_ci_governance.py` (both floor pins);
`tests/mutations/test_write_transaction.py` (the second importer);
`docs/GLOSSARY.md` anchors `DjangoGraphQLProtocolRouter`,
`require_optional_module`, PEP 562 lazy export, soft dependency,
WebSocket consumer-injection seam, WebSocket revalidation window,
WebSocket Host boundary; `docs/README.md` transport rows (the Channels
router section and the 0.0.14 migration table). Fakeshop carries no
`config/asgi.py` (WSGI-only, confirmed by listing), so no live request
reaches this target. `consumers.py`, `views.py`, and `utils/` mention
routers in prose only; nothing imports it back.

Probe `docs/review/temp-tests/routers/mechanics/probe_re_arms.py`
(copied to `tests/test_mech_probe_re_arms.py` in the copy only; pure
stdlib plus construction-time validation, zero database I/O, zero
socket): default cell `review-20260929T103932-036c84` 3 passed; sharded
cell `review-20260929T104141-a17e04` 3 passed. Witness identification
`review-20260929T103942-b58273`: `"(" * 500 + ")" * 500` raises
`RecursionError` at depth 500 (depth 200 compiles);
`"a{99999999999999999999999}"` raises `OverflowError` ("the repetition
number is too large"; the 32-bit-count candidate compiles);
`dict.update` and `iter` raise `ValueError` ("no signature found for
builtin"). pg is inapplicable by construction for this evidence: the
probe asserts interpreter behavior (`re`, `inspect`) plus the typed
conversion at the construction boundary, with no database, alias, or
dialect in reach; the static facts are cell-independent. The verifier
judges.

`check_citations.py --cited-by` was not run: this record proposes no
move or rename of any symbol. `workspace.py audit` on this record is
owed by Worker-0 per the checks table.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/routers.py`
`e18772f76beed8f42cc5bba0d7b9a4e7c7f77bd2` (live, whole, dirty);
`django_strawberry_framework/consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (window, factory, validator
regions); `django_strawberry_framework/utils/imports.py`
`291ecedd30c7d8af9c007758112e867c09d031eb` (whole);
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9` (identity readers);
`django_strawberry_framework/auth/sessions.py`
`865d6e704d2df50bcad465ad3005eccb39e8c545` (guard + classifier);
`django_strawberry_framework/rest_framework/__init__.py`
`45cf7b63a2b768421b80b99ee78ec048a03641e1` (whole);
`django_strawberry_framework/types/base.py`
`dc67f084cbc969d64b7b1f1ef18c388095d394f7` (GlobalID validator);
`django_strawberry_framework/utils/querysets.py`
`8fc556d582b313e4aed7cddaa15f9a8480d88a46` (awaitable disposal);
`django_strawberry_framework/views.py`
`48ee582ecdba41d49beb2434f2a9e0af992d39d4` (module docstring);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (whole);
`django_strawberry_framework/middleware/debug_toolbar.py`
`ffda621eaf1bf9114a3144ca42586af8639c91ff` (guard);
`tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (construction, seam,
window, concurrency, absence, handshake rows);
`tests/test_ci_governance.py`
`cfc66f6e028b3dabdabfdfd13bebd1ada656e3e0` (floor pins);
`tests/mutations/test_write_transaction.py`
`689e31f47ae0dc010e67386e4a076b782afac5ff` (second importer);
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be` (transport rows);
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd` (transport anchors);
`docs/review/rev-routers.performance.md`
`1023ed524d3c0aa6fac881bfc55175017906df95` (whole);
`docs/review/rev-consumers.mechanics.md`
`499497af14b60bb57d2710fb8182afccdab6ca0a` (whole — shape reference
plus its R3/R6 rulings this record builds on).

## Findings

### High

None.

### Medium

None.

### Low

None.

Proof lines: none exist — zero findings, and the Performance record
carries no `## Cross-axis (for Mechanics)` section.

Looks-for discharge (REVIEW.md "Mechanics"), each a finding, `none`
with the reason, or a rejection (full text under `## Rejected`):

- Rule enforced at a caller instead of its owner: none. The window
  domain is validated by its owner
  (`django_strawberry_framework/consumers.py::resolved_revalidation_window`,
  called once at construction); the default is spelled once at the
  owner and imported (the deliberate private import the consumers
  record's R6 upholds); the Host decision is Django's own
  `get_host()` behind the consumers-owned validator; the Origin and
  session layers are upstream's, composed — never restated. The
  value-then-combination order (a bad window is a bad window
  whatever else was passed) keeps each rule at its own site.
- Policy in an adapter, mechanism in a policy layer: none. The module
  composes wrappers and owns only its seam contracts: the
  window-with-injected-consumer combination (seam-owned — pushing it
  into the window validator would teach consumers about the seam, the
  worse direction), the factory calling convention, and the
  mountability floor. Revalidation policy, Host projection, and
  masking all live with their owners.
- Decision the contract sources make differently from the body: none.
  Checked row by row against the glossary
  `DjangoGraphQLProtocolRouter` anchor, the `require_optional_module`
  and PEP 562 anchors, and the README router section plus migration
  table: `"http"` is the supplied application verbatim; the default
  pattern is exact at both ends; omitting `django_application` is
  Python's `TypeError` while `None`/non-callable is the migration-naming
  `ConfigurationError` (R7); `url_pattern` is renamed with no alias
  and the keywords are keyword-only; the schema passes through
  untouched; Host runs outside Origin as two separate checks; the
  soft-dependency matrix (package and submodule import channels-free,
  symbol access raises the install hint) holds — the module-level
  import chain reaches stdlib plus already-imported Django and
  package names only; the present-but-broken errors split by half
  with the original chained; the guard is the documented thin
  wrapper. The migration table's three rows each land where the
  table says.
- Branch no real path reaches: none. Every suspicious arm is
  reachable: `OverflowError` / `RecursionError` in the pattern
  validator (probed witnesses above, converted with `__cause__`
  intact); the `ValueError` member of the signature pass-through
  (`dict.update`, `iter` — the `TypeError` member is pinned by
  `test_a_factory_whose_signature_cannot_be_read_is_judged_by_the_call`);
  both `_ROUTER_CLASS` cache hits (the outer by repeat access, the
  inner under the build lock by construction — the concurrency test
  forces the second thread onto the lock path and pins the one-class
  property); the non-consumer-class fall-through, the non-callable
  fall-through, the coroutine addendum, and the plain-scalar arm
  (each pinned by its parametrized row); both `ImportError` halves
  (the degraded-install test); the `__getattr__` miss (the plain
  `AttributeError` row). The `__signature__`-descriptor propagation
  past `(TypeError, ValueError)` is the pinned consumer-behaviour
  rule, not a hole.
- Mode flag standing in for a named adapter: none. `None` / subclass
  / factory is a discriminated injection seam with per-shape
  construction, not a mode selector; the window is a numeric bound
  whose `> 0.0` reads are cache/combination predicates, not behaviour
  switches.
- State owned in two places: none. `_ROUTER_CLASS` is the single
  build cache and the package consumer class is built inside the
  same guarded builder precisely so no second cache in consumers.py
  can outlive an eviction (`build_revalidating_consumer_class` is a
  pure factory, no cache of its own). The window is validated to a
  local and threaded as an argument; no scope or global carries it.
- Dependency pointing the wrong way: none. Module level reaches
  stdlib, `ConfigurationError`, truthful readers, the optional-import
  owner, and consumers (the transport below the composition root).
  No package module imports routers back (only prose citations), and
  the `TYPE_CHECKING` block holds annotation-only Django/strawberry
  names under `from __future__ import annotations` — no runtime
  cycle, real or hidden. The `re_path` import stays function-local
  inside the guarded builder with the rest of the soft composition.
- `django.conf.settings` read at import: none — the module imports
  no settings object at all (no `django.conf` import outside prose;
  the one `DJANGO_SETTINGS_MODULE` hit is the docstring's `asgi.py`
  example). Module level binds hint strings, the cache slot, and one
  lock.
- `__all__` disagreeing with the public surface: none. The star
  surface is pinned by contract to the one lazy export (spec-041
  Decision 3, the test's `__all__` assertion, the glossary PEP 562
  anchor: star import must fire the guard). `require_channels` is a
  named leaf import with one production caller, deliberately not
  star surface; the package root re-exports no routers name. Absence
  from `__all__` blocks nothing by name, and nothing by name needs
  blocking.
- Two sites implementing one rule: run the change challenge on all
  five candidate pairs; each is rejected with its count and trigger:
  the four `require_*` wrappers incl. the twin-named
  `require_channels` pair (R1), the signature-bind pre-check vs the
  GlobalID encoder check (R2), the coroutine close vs the shared
  awaitable disposer (R3), the floor literals vs their pyproject rows
  (R4). The remaining lookalike — module build lock vs the instance
  `threading.Lock`s in `extensions/debug.py` and `orders/sets.py` —
  guards different state with different lifetimes (one process-wide
  class fill vs per-object mutation); posit a locking-policy change
  and exactly one site moves. Trigger: a second process-wide lazy
  builder hand-rolling the double-checked shape instead of sharing it.
- Sync/async twins that drifted: none — no sync twin exists. Router
  construction is synchronous by contract ("Router construction is
  synchronous and cannot await anything", the reason the coroutine
  arm closes rather than awaits); the async surface is the composed
  ASGI application itself. The HTTP tier's sync/async split lives in
  views.py, which does not import this module.
- Guard one flavor has and a sibling lacks: three asymmetries, each
  correct. The factory RESULT is callable-checked while the
  class-branch `as_asgi(...)` results are mounted unchecked (R5).
  The WebSocket branch carries Host, Origin, and session checks the
  HTTP branch lacks — the contract-owned transport split (spec-046:
  Django's middleware owns those questions on HTTP), pinned
  structurally and live. The coroutine refusal closes while a
  returned future is refused without disposal (R3).

## Rejected

- **R1: the four `require_*` soft-dependency wrappers (incl. two
  functions both named `require_channels`) should be one.**
  The shared mechanics already are one: every wrapper is a
  two-line delegation to `utils/imports.py::require_optional_module`,
  so a guard-semantics change has exactly one site. What differs —
  the hint string — is feature-keyed by contract ("hint strings stay
  single-sited at the feature owner"): the router's hint names the
  router, the auth boundary's names the auth boundary, and routing
  the auth path through the router's guard would misdirect the
  consumer it is trying to help. The twin name follows the
  `require_<dependency>` convention under different module paths;
  all four call sites qualify it. Challenge count: posit a hint-text
  change — one wrapper moves; posit a mechanics change — the
  primitive moves. Trigger: a fifth wrapper hand-rolling the
  try/except instead of delegating, or two hints converging to
  identical text.
- **R2: `_require_factory_calling_convention` duplicates the
  signature-bind pre-check in
  `types/base.py::_validate_globalid_callable`.** Same primitive
  (`inspect.signature(...).bind(...)` into `ConfigurationError`),
  opposite policies on purpose: the seam lets an un-introspectable
  factory through to be judged by the call (a C callable is a
  legitimate factory), while the GlobalID gate rejects an
  indescribable encoder at validation time (spec-031 Decision 6
  demands a statically known sync triple). A lying `__signature__`
  is trusted by both — as it is by every introspecting caller —
  and a descriptor raising outside `(TypeError, ValueError)`
  propagates as consumer behaviour here (pinned). Posit a policy
  change on either side and only that seam moves. Trigger: a third
  bind-precheck site, or the two policies converging.
- **R3: the coroutine close should route through
  `utils/querysets.py::_dispose_sync_awaitable`, and a returned
  future should be disposed too.** Different rules. The shared
  disposer detects with `inspect.iscoroutine` (an `isinstance`
  read — a `__class__`-spoofing factory return would then dispatch
  `.close()` into consumer code), while this boundary classifies a
  hostile factory return truthfully and closes only a genuine,
  never-started coroutine (no bytecode runs). Importing the
  queryset machinery for the one call would also drag a heavy
  module into the soft-dependency import chain for no gain. A
  returned future is refused without disposal deliberately: the
  addendum names the one-keyword-away coroutine mistake, a bare
  pending future makes no GC noise, and construction cannot await.
  Trigger: the disposer gaining a truthful mode this boundary could
  share, or a contract demanding future disposal at a sync seam.
- **R4: the floor literals are written twice (constants plus
  pyproject rows).** Install metadata vs runtime message —
  different reasons to change — and both pairs are pinned equal by
  `tests/test_ci_governance.py`
  (`test_channels_floor_constant_matches_the_pyproject_dependency_row`,
  `test_strawberry_floor_constant_matches_the_pyproject_dependency_row`),
  so a one-sided bump fails loudly. The four `pip install`
  hints all interpolate the constants, so the hints cannot drift
  from each other. Trigger: a third written copy, or a pin going red.
- **R5: the class branch mounts `as_asgi(...)` results unchecked
  while the factory branch callable-checks.** The factory check
  exists because a factory is arbitrary consumer code whose garbage
  would otherwise fail deep inside Channels' routing. The class
  branch calls upstream's `as_asgi` mounting convention on a
  verified `GraphQLWSConsumer` subclass (None branch: the package's
  own consumer) — overriding `as_asgi` to return garbage is outside
  the documented seam contract ("mounted through its own
  `as_asgi(schema=schema)`"), and no contract source promises a
  construction-time rejection for it. Checking would also be a
  behavior promise about upstream's return this module has no
  standing to make. Trigger: a contract extending the mountability
  floor to the class branch, or a reachable override shape the
  handshake misattributes.
- **R6: `_validated_websocket_url_pattern` rejects `str`
  subclasses it could accept.** Exact-type strictness at a
  construction boundary is the documented choice ("the router's
  public annotation is a string"), matching the package's other
  config gates; a subclass would work today, but no contract
  promises duck-typed admission and strictness keeps the rejected
  set describable (`None`, numbers, bytes, arbitrary objects,
  malformed patterns — all pinned). The `utils/imports.py`
  `_plain_text` normalizer accepting subclasses is the opposite
  rule for the opposite reason (import machinery needs exact
  `str`). Trigger: a consumer contract requiring subclass
  admission.
- **R7: omitting `django_application` raises a bare `TypeError`
  with no migration hint, while `None` names the migration.**
  Unfixable by construction — the `TypeError` comes from Python's
  own signature binding before any package code runs — and the
  split is the documented contract (glossary anchor, README
  migration table, and the "deliberately" comment at the guard).
  Teaching the omission the hint would need `*args` introspection,
  which would trade a standard missing-argument error for a
  hand-rolled one. Trigger: the parameter going optional again.

## Cross-axis (for Comments)

Routing note, not a finding — the plan's Routed lead on this item
(the `_ws_communicator`, keyword-only-pattern, and factory-body
wordings in `tests/test_routers.py`, quoted in the Trace) was judged
to carry no mechanics content: every structure the wordings assert is
true of the body (bare-Django HTTP value; Host-outside-Origin
WebSocket checks; convention normalized, body never). Owning Comments
pass grades that module whole, including tense, voice, and quotation
quality. No severity, no Proof owed from this axis.

Handoff: Mechanics review is closed with no findings, seven
rejections, and one routing note for this item's Comments phase. The
judgments a verifier could revisit are R5 (the class-branch
no-check — the trigger names the exact shape that would reopen it)
and the inner-lock-cache-hit reachability claim (timing-dependent by
nature; the one-class property it protects is what the test pins).
Everything else was discharged by first-hand reads (every contract
row checked against the body, both directions of every import edge),
by the oracles named in the Trace, or by the workspace probe, whose
three nodes rerun verbatim in any copy. One belief worth keeping:
the `except` tuples I first read as possibly defensive
(`OverflowError`, `RecursionError`, `ValueError`) are all reachable
through the router path on the installed interpreter, with the
witnesses above. Routed lead OUT of this item (for Worker-0, not a
finding here): `django_strawberry_framework/rest_framework/__init__.py::require_drf`
says "the three soft-dependency guards" while four thin wrappers over
`require_optional_module` exist (`routers.require_channels`,
`auth.sessions.require_channels`, `require_drf`,
`middleware.debug_toolbar.require_debug_toolbar`) — pre-existing at
HEAD, prose in another module, for that (pending) item's Comments
pass to judge whether the count means names or sites. No defects, no
production or test edits. Cells: default and sharded green on the
probe; pg inapplicable by construction with the reason stated above,
for the verifier to judge.

## Verify mechanics

Precondition: the live tree carries exactly the change under grade.
`git hash-object` gives `routers.py` 299da0f5 (the end-state blob of
`docs/review/temp-tests/routers/diff/pass-1.diff`, whose index line
reads `e18772f7..299da0f5`), `tests/test_routers.py` f513d869 and
`tests/auth/test_mutations.py` ff8a261d, both equal to their
ITEM_BASELINE blobs; the live item diff is byte-identical to
pass-1.diff (`diff` IDENTICAL, 1 file, +23/-17). All checks below are
static in the shared tree; no workspace copy was bound, no run id
exists.

(a) Prose-only, digest-proven. `review_inspect.py --code-digest
eb71162b:django_strawberry_framework/routers.py
django_strawberry_framework/routers.py` exits 0 with two equal
digests (`sha256:38c32db5...28c65c` both sides). The stripped AST is
identical, so no executable line, branch, guard, literal, or import
moved: no Mechanics defect can have been introduced, and every
looks-for discharge grounded in "the body does X" still reads the
same body. The def/class census is identical in names and order (7
module functions, the nested `DjangoGraphQLProtocolRouter`, module
`__getattr__`; line numbers shift only from comment reflow), so no
symbol moved or was renamed.

(b) Rejections R1-R7 stand undisturbed; the rewords agree with them.

- R1 (four `require_*` wrappers stay separate; hints single-sited at
  the feature owner): the T1 reword AGREES. "This module's single
  channels-ABSENT install hint", "The auth transport carries its own
  feature-keyed twin (`auth/sessions.py`)", "passing this module's
  `_CHANNELS_INSTALL_HINT` string", and "every true-absence path of
  this builder routes through its single install hint" state exactly
  R1's rationale (feature-keyed hints; twin name under different
  module paths) where the old unscoped "the single" (now 0 hits)
  contradicted the census R1 defends. Challenge counts unchanged:
  code identical, primitive still the one mechanics site.
- R2 (factory seam pass-through vs GlobalID gate): code identical;
  the `_factory_application` reword corrects only the rejected
  alternative's mechanism (`bind` accepts `*args`/partial shapes) and
  keeps the conclusion (floor-not-proof, un-introspectable pass
  through). The policy split R2 defends is untouched.
- R3 (coroutine close stays local; futures refused undisposed): code
  identical; no new import (the import block is covered by digest
  identity). The reword adds no disposal promise.
- R4 (floor literals in two places, pinned equal): literals untouched
  (digest identity); the T2 bound `through 6.0` -> `through 6.1` is a
  prose ceiling update matching the advertised classifiers, not a
  floor change, and all four hints still interpolate the constants.
- R5 (class branch mounts `as_asgi` results unchecked): code
  identical; no reword promises a class-branch check.
- R6 (exact-`str` strictness): the `_validated_websocket_url_pattern`
  reword sharpens the mechanism (stringified-match instead of
  never-match) while still justifying the same rejection; it adds no
  subclass-admission promise.
- R7 (omission `TypeError` vs `None` `ConfigurationError`): code
  identical; the "deliberately" comment is intact and the dropped
  clause ("migration is no longer one line") was pure temporal, not
  part of the documented contract.

Routing note: the plan's Routed lead was captured in the Comments
record as F2/F3/F5, all test-file Lows, all correctly DEFERRED per
the ride rule (no higher finding touches either test file; both
files byte-identical to ITEM_BASELINE). Deferral is the prescribed
disposition, not a disturbance. The out-of-item route
(`require_drf` "three guards" count) still belongs to the pending
`rest_framework` item; untouched here.

(c) Test files untouched, citers intact. `git diff ITEM_BASELINE --
tests/test_routers.py tests/auth/test_mutations.py` is 0 bytes; both
hashes equal the Trace fingerprints. `check_citations.py --paths
<target> --substrings`: 7 citations resolve, 0 violations (same
count the Comments Trace baselined). `check_trailing_commas.py
--check <target>`: 0 violations. Cells: the inapplicable-by
construction call for all three cells stands (a prose-only diff
reaches no database, alias, or dialect at runtime).

Verdict: `verified`. No new finding, no routed gap, no
`revision-needed` item. The pass-1 change is prose-only,
digest-proven, lint-green, and mechanics-neutral; every R1-R7
rejection and every looks-for discharge in this record stands on
unchanged code.

Fingerprints: `django_strawberry_framework/routers.py`
`299da0f541f184ec833e01a4d9c83cc0d7880d15` (live, post pass 1);
`tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (== ITEM_BASELINE);
`tests/auth/test_mutations.py`
`ff8a261d09ca63a0f606673bf11b9262f2bb1f35` (== ITEM_BASELINE);
code digest `sha256:38c32db58e89f01bad17c719bdea9fac43bf9f1e986406e590eef031bd28c65c`
both sides, exit 0. Run ids: none (fully static; no copy bound).
Scratch: `docs/review/temp-tests/routers/verify-mechanics-1/`
(`code-digest.txt`, `fingerprints.txt`, `greps.txt`,
`live-item.diff`, `symbols-base.txt`, `symbols-live.txt`,
`lint-commas-check.txt`, `lint-citations-check.txt`).

Handoff: Mechanics verification of pass 1 is closed. The only
judgment a later pass could revisit is the T1-agrees-with-R1 reading
(contract-load-bearing scoping vs mere tense cleanup): it was judged
agreement because the new sentences name the twin and the
feature-keying R1's trigger defends. If a later pass touches code in
this target, the R5 trigger (a reachable override shape the
handshake misattributes) and the inner-lock-cache-hit reachability
claim rerun as the regression probes. Nothing is blocked; nothing
routes elsewhere.

Status: verified. Open threads: none.
