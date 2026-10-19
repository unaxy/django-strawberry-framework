# DRY review: `django_strawberry_framework/_boundary_ordering.py`

Status: verified
Run: 0.0.15 2026-09-21-2

Item baseline: `ITEM_BASELINE=3bccf53c3127f104b2f57fc87c791a3b04b1d976`, HEAD
`bfaee91d` at dispatch. Target clean at HEAD blob
`197eea8e01cb405f38b21022689ed54970efcb97` (re-confirmed at start; item diff
empty at finish — see Judgment). 111 dirty concurrent paths left untouched;
every fact below about a dirty path (`routers.py`, `test_transport_api.py`)
was read via `git show HEAD:` / `git grep HEAD`.

## System trace

The target is the ordering-protocol module between the two owners of the
request-body boundary: `django_strawberry_framework/views.py` owns the boundary
itself (spec-046 Decisions 7 + 9), `middleware/request_body.py` owns where in
the lifecycle it runs (Decision 18). Neither imports the other; both import
only the constants from here, and this module imports nothing but the standard
library at runtime (verified by execution — probe P1 below).

What the target owns: four attribute-name constants (`_BOUNDARY_MARKER`,
`_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`), one
method-name constant (`_BOUNDARY_METHOD`), one chain-published request
`ContextVar` (`_boundary_middleware_request`), and the withdrawable
`csrf_exempt` value (`_CsrfOrderingExemption` + shared `_CSRF_ORDERING_EXEMPTION`).

Sites found, all at HEAD:

- Writer/reader census per mark (definition = target; every other site consumes
  by name — full table in Challenges):
  - `_BOUNDARY_MARKER`: stamped `views.py:580`, read `request_body.py:330`.
  - `_BOUNDARY_ENFORCED`: stamped `request_body.py:243`; read
    `request_body.py:216` (idempotency), `views.py:621` (skip), target `:147`
    (exemption predicate).
  - `_BOUNDARY_MOUNT`: stamped `views.py:581` (per-mount `object()` token,
    `views.py:552`), read `request_body.py:238` (guarded: a raising read costs
    the handoff, never the response).
  - `_BOUNDARY_PREPARED_VIEW`: stamped `request_body.py:242` as
    `(mount, view)`; consumed once `views.py:555-559` (exact
    `type is tuple` + len 2 + token-identity check, then `delattr`).
  - `_BOUNDARY_METHOD`: defined `views.py:584` (`_enforce_request_boundary`);
    probed `request_body.py:336` (callable, on the class, pre-construction)
    and invoked `request_body.py:230` — both through the constant.
- `_boundary_middleware_request`: set/reset around the downstream call in both
  `request_body.py:163/167` (`__call__`) and `:176/180` (`__acall__`); read
  only by the exemption predicate (target `:146`).
- `_CSRF_ORDERING_EXEMPTION`: bound once, `views.py:579`, on the shared mixin
  `as_view` both transports inherit.
- No other importer of the target exists in the package: `git grep
  _boundary_ordering HEAD -- django_strawberry_framework/` names only
  `views.py` and `middleware/request_body.py` (plus the target's own
  docstring self-references). `routers.py:406` mounts via `as_view` — a
  consumer of an already-stamped callback, not a protocol party.
- Oracle tier: `tests/test_views.py` imports all five constants (`:81-87`) and
  never spells a literal (stated in-test at `:2914-2915`, `:3696-3697`; the
  one literal fixture, `:3223`, is an independent spelling oracle — see F4);
  live tier `test_transport_api.py` pins the shipped chain, the real mount's
  marker, recognition, and the configured-CSRF-class witness.
- Contract sources: spec-046 Decision 18 (three-state switch, recognition ends
  at the boundary, one-complete-CSRF-check guarantee), glossary anchors
  `GraphQLRequestBodyBoundaryMiddleware` / `DjangoGraphQLView` /
  `Request-body cap`, upstream `getattr(callback, "csrf_exempt", False)` at
  `django/middleware/csrf.py:420` (installed Django 6.1).
- Prior cycle: `dry-0_0_14.md` ticks this file with no boundary family named
  and no outcomes text — no rejected-candidate trigger to check. Per-cycle
  artifacts from 0.0.14 were closed out and are absent from HEAD.

## Verification

### Enumeration

Instrument: `ast.Module.body` over the target at HEAD (13 nodes) + a
runtime-name census. Count: 13 top-level nodes; 8 module-level runtime names
(+ 1 method). Every member lands below; nothing is unassigned.

| # | Node | Name / content | Lands in |
|---|---|---|---|
| 1 | Expr | module docstring (protocol statement) | F1–F6 (projection of each) |
| 2 | ImportFrom | `__future__.annotations` | idiom, no rule |
| 3 | ImportFrom | `contextvars.ContextVar` | F5 (mechanism import) |
| 4 | ImportFrom | `typing.TYPE_CHECKING` | F8 (type-only seam) |
| 5 | If | `TYPE_CHECKING` → `django.http.HttpRequest` | F8 (no runtime import) |
| 6 | Assign | `_BOUNDARY_MARKER` | F1 |
| 7 | Assign | `_BOUNDARY_ENFORCED` | F2 |
| 8 | Assign | `_BOUNDARY_MOUNT` | F3 |
| 9 | Assign | `_BOUNDARY_PREPARED_VIEW` | F3 |
| 10 | Assign | `_BOUNDARY_METHOD` | F4 |
| 11 | AnnAssign | `_boundary_middleware_request` | F5 |
| 12 | ClassDef | `_CsrfOrderingExemption` + `__bool__` | F6 |
| 13 | Assign | `_CSRF_ORDERING_EXEMPTION` | F7 |

Nodes 2–5 carry no rule (import idiom + the F8 type-only seam, which exists so
the runtime closure stays stdlib-only). All eight rules F1–F8 assign to the
one named family `request-body-boundary-ordering` (consolidated — see Index
rows). Cross-site candidates considered and declined: R1–R3.

### Matrix

Discharged against the target's real surface (a name/protocol module: no ORM,
no I/O, no async body of its own).

1. Cross-flavor policy mirroring — searched. Sibling callback-attribute
   recognition exists in exactly one place: `middleware/debug_toolbar.py:233`
   (`view_class` read for Strawberry-view tagging). Different question,
   different answer use → R1 (rejected, contract difference + trigger). Sibling
   request-attribute stamps: toolbar's `request._is_graphiql` (bool tag for
   response postprocessing) and Django's own (`_stream`, `_read_started`,
   `user`, `session`, `consumer`, `scope`) — all distinct contracts, none a
   package boundary mark. The WebSocket branch (`consumers.py`, `routers.py`)
   carries no boundary marks at all: no middleware-chain CSRF ordering question
   exists there, so there is no mirrored policy to unify — a justified
   absence, not a gap. `csrf_exempt` is assigned at exactly one package site
   (`views.py:579`); the only other `csrf_exempt` mentions are docstrings and
   the oracle asserting its ABSENCE on the inner continuations
   (`tests/test_views.py:2578`).
2. Sync/async twins — ruled inapplicable with reason. The target defines no
   suspendable work: constants, one `ContextVar`, one synchronous predicate.
   The predicate is read by Django's `process_view` path on both transports;
   the variable is published symmetrically by the middleware's `__call__` /
   `__acall__` twins (both set/reset in `finally`; the async twin exists
   because the reset must follow the `await` — stated at
   `request_body.py:169-175`). The twin structure itself is the middleware's
   rule, owned by the middleware file item, not this one. Observation (not a
   defect): the dedicated reset pin is async-only
   (`test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`);
   the sync arm's reset has no dedicated row — behavior is symmetric by
   construction, only the pin is single-sided. Flagged for the middleware
   item's attention in F5; no behavior gap, no oracle owed by this item.
3. Derived rather than repeated knowledge — searched, none found. "Is a
   package view" is derived nowhere else: no `isinstance` / `issubclass`
   check against the package views exists in the package census (toolbar
   checks against Strawberry's `BaseView` — R1). The boundary name is built by
   concatenation nowhere; the mount token is created per-mount (`views.py:552`),
   never re-derived. The one deliberate derivation — the middleware building a
   view instance from `view_class` + `view_initkwargs` bookkeeping — is the
   middleware's rule (Django's `as_view` contract), not a restatement of any
   target name.
4. Inverse / round-trip pairs — searched; three pairs, each one grammar with
   two halves, none duplicated. ENFORCED stamp (write `request_body.py:243` /
   three read consequences); PREPARED_VIEW 2-tuple (write `:242` / consume
   `views.py:555-559`); METHOD name (define `views.py:584` / probe `:336` +
   invoke `:230` through the constant). Literal census: the four
   `graphql_request_body_boundary*` spellings occur ONLY at target `:70,76,80,85`
   (`git grep graphql_request_body_boundary HEAD` — 4 hits, all the
   definitions); the ContextVar name occurs only at target `:104`; the method
   name string occurs only at target `:95` plus the one independent literal
   oracle (tests `:3223`, fails closed — see F4). No second grammar exists.
5. Contracts restated in another medium — classified, each under its role.
   Definition: the eight target sites. Consumers: `views.py`, `request_body.py`
   (by name). Oracles: `tests/test_views.py` (constant-importing rows + the
   identity pin `:3678` + the literal-spelling row `:3223-3245`), live
   `test_transport_api.py` (chain/marker/recognition/configured-class rows).
   Projections (never counted): spec-046 Decision 18 + rationale companion,
   glossary anchors, module docstrings on all three sides, KANBAN card 053
   prose, `docs/TREE.md` lines, kanban tracked-path constants, the DONE
   build-046 record, bug-hunt battery prose. A contract change moves
   production + oracles + projections together by design; the definition count
   stays 1 (2 for F4, irreducible — see Challenges).
6. Enforcement by omission — enumerated, no gap. Family = package view
   callbacks: both transports resolve `as_view` to the shared mixin
   (`tests/test_views.py:2545` pins
   `view_class.as_view.__func__ is _RequestBodyBoundaryMixin.as_view.__func__`
   for both), so both get marker + mount + exemption from the single site
   `views.py:579-581`, and the bookkeeping (`view_class`/`view_initkwargs`)
   survives via `functools.wraps` (pinned `:2546-2548`). No second stamping
   site, no unstamped mount, no flavor lacking a guard the contract requires.
   The declined-callback fallback (exemption stays true, view-local CSRF
   re-entry) is itself the contract for unrecognized callbacks (Decision 18,
   third state), pinned both tiers — omission of the stamp there is the
   specified behavior, not a missing guard.

### Challenges

Posited changes with authoritative-definition counts (consumers, oracles,
projections listed, never counted). Searched population for every count:
`git grep -n <symbol> HEAD` over the full tree excluding the generated
single-line `KANBAN.html` (a projection whose echoes add no site), plus
`git show HEAD:` reads of every hit file.

| Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|
| F1 marker | rename the mark value | 1 (target `:70`) | single-owned |
| F1 marker | change what recognition accepts | 0 in target (middleware's rule, `:329-343`) | separation holds |
| F1 marker | add a third stamping site | 0 new (writer set is 1 by census) | single-owned |
| F2 stamp | rename the stamp value | 1 (target `:76`) | single-owned |
| F2 stamp | add a second stamper | 0 new (single-writer invariant, target `:48-54`) | single-owned |
| F2 stamp | add a fourth read consequence | 0 in target (new consumer reads the constant) | single-owned |
| F3 handoff | rename either attribute | 1 each (target `:80` / `:85`) | single-owned |
| F3 handoff | reshape the tuple | 1 grammar, 2 halves (write `:242` / consume `views.py:555-559`) | single grammar |
| F3 handoff | relax the token check | reader side only (`views.py:556`); writer untouched | halves separable |
| F3 handoff | per-mount token to module singleton | breaks decorator-copied-callback exactness | rejected merge |
| F4 name | rename the boundary method | 2: name (target `:95`) + method (`views.py:584`), IRREDUCIBLE | 2, pinned junction |
| F4 name | probe accepts but invoke calls another name | impossible (both read the constant, `:230` + `:336`) | unity holds |
| F4 name | middleware imports views for the name | reverses the dependency the module prevents | rejected shape |
| F5 var | rename/re-identify the variable | 1 (target `:103-106`) | single-owned |
| F5 var | change publish scope | 0 in target (middleware's rule) | separation holds |
| F5 var | merge with a sibling ContextVar | declined per sibling contract (R2) | rejected merge |
| F6 predicate | flip any one of the three answers | 1 (target `:146-147`) | single-owned |
| F6 predicate | collapse to single `getattr` with default | already rejected at the owner (`:137-145` docstring) | rejected shape |
| F6 predicate | read a second fact | 1 (sole `__bool__` in package) | single-owned |
| F7 singleton | per-view instances | 0 observable (stateless) | single-owned |
| F8 layering | add a django/first-party runtime import | breaks cycle-avoidance; probe P1 fails | enforced |

## Findings

All eight rules assign to the one named family `request-body-boundary-ordering`
(consolidated at the target; see Index rows). No consolidation is owed: every
rule already has exactly one authoritative definition that every other site
composes by name — the module was created as that owner by the spec-046 slice
(`docs/builder/DONE/build-046-transport_security-0_0_15.md:979-980`) and this
item verified the single ownership still holds at HEAD.

### F1 — Callback recognition mark `_BOUNDARY_MARKER` (family)

- Contract + variation: the one attribute whose presence makes a resolved view
  "a package view whose boundary a chain entry can run". Varies on value
  spelling only; meaning and writer set are fixed (writer = mixin `as_view`,
  reader = middleware recognition).
- Sites + roles: definition = target `:70`. Consumers = `views.py:580`
  (stamp), `request_body.py:330` (recognition read). Oracles =
  `tests/test_views.py:2544` (both transports stamped), `:2941-2948` (marked
  fixtures), `:3166` + `:3238` (marker-routed rows); live
  `test_transport_api.py` `:3065` (real mount marked). Projections = target
  `:16-20`, middleware docstring, Decision 18, glossary.
- Challenges: rename → 1; recognition-meaning change → middleware's rule (0
  in target); third writer → contract change composing the same constant (0
  new).
- Owner + lifetime: target `:70`. Process-lived string; valid from import;
  never mutated (no second assignment in census).
- Migration: none — writer and reader already compose by name.
- Distinct behavior: the mark alone never authorizes running a boundary —
  recognition continues to bookkeeping + callable-boundary probe
  (`request_body.py:332-337`); a marked callback without those is declined,
  keeping the view-local arrangement. Recorded at the middleware owner.
- Behavioral proof: probe P1 step 1 + census `execution-verified` (no second
  spelling exists to diverge); recognition rows `static-reviewed` (permanent
  oracles pin both verdicts — accept in `:2544`/live `:3065`, decline across
  `:2941-2969` fixtures). No suite run needed for the single-ownership
  verdict; CI owns green-ness.
- Structural gate + negative control: the literal census
  (`git grep graphql_request_body_boundary HEAD` → exactly the 4 definitions)
  is the gate a second spelling fails; negative control is the declined-mark
  fixtures (marked-but-unbuildable callbacks behave as view-local — the
  fallback the mark's absence-or-insufficiency must produce).
  `static-reviewed`.
- Coupling: none.
- Freshness: target `HEAD 197eea8e01cb`; `views.py` `HEAD 9f85b0df26a1`;
  `middleware/request_body.py` `HEAD e6e32e785ec8`; `tests/test_views.py`
  `HEAD 4dc9a2572350`; `test_transport_api.py` `HEAD 17320f1ff335`
  (dirty in tree — facts via `git show HEAD:`); spec-046 `HEAD 8d8adaf2f2f0`;
  GLOSSARY `HEAD bc51debc54cf`; census population = full tree minus
  `KANBAN.html`.

### F2 — Per-request completion stamp `_BOUNDARY_ENFORCED` (family)

- Contract + variation: stamped once a chain participant has run the
  boundary, so the view never re-measures and the exemption withdraws for
  exactly those requests. Varies on value spelling; single-writer invariant
  (target `:48-54`: one writer licenses keying the exemption off the stamp).
- Sites + roles: definition = target `:76`. Consumer/writer =
  `request_body.py:243` (sole in-package stamper — census-verified).
  Consumers/reads = `request_body.py:216`, `views.py:621`, target `:147`.
  Oracles = `:3191/3207` (stamp-then-believe, one measurement),
  `:3245-3246` (stamp without handoff), `:3276/3295` (no stamp on failure
  paths), `:3721`, async predicate rows `:3412-3414`; live
  `test_transport_api.py` configured-class row (withdrawal witness).
- Challenges: rename → 1; second stamper → violates the stated invariant (0
  new — the invariant exists to forbid it); fourth read → new consumer (0 in
  target).
- Owner + lifetime: target `:76` owns the name; each stamp lives on one
  request object for that request's chain traversal. Never deleted (unlike
  F3's handoff — completion is forever within the request).
- Migration: none — all three reads already compose by name.
- Distinct behavior: the three reads enforce different consequences
  (idempotency / skip / withdrawal) — three consumers of one stamp, not three
  definitions. The stamp is never a permission: it records a completed
  measurement, nothing more.
- Behavioral proof: one-measurement row + failure-path unstamped rows
  `static-reviewed` (existing oracles pin stamp-present, stamp-absent, and
  stamp-without-handoff); writer census `execution-verified` via P1-adjacent
  grep (sole stamper). No suite run needed.
- Structural gate + negative control: `test_duplicate_boundary_entries...`
  (`:3724-3761`) fails a lost idempotency read; the failure-path rows fail a
  stamp written too early. Negative control = second boundary entry leaving
  the first result intact (pinned), and raising-setup paths leaving the
  request unstamped (pinned `:3276`). `static-reviewed`.
- Coupling: none.
- Freshness: same five HEAD blobs as F1 (target `197eea8e01cb`, views
  `9f85b0df26a1`, middleware `e6e32e785ec8`, tests `4dc9a2572350`,
  live `17320f1ff335` via HEAD).

### F3 — Mount-token-bound prepared-view handoff (family)

- Contract + variation: `(mount token, prepared view instance)` under
  `_BOUNDARY_PREPARED_VIEW`, consumed exactly once by the callback whose own
  token it carries — the view whose boundary ran is the view whose dispatch
  continues. Varies on attribute spellings and tuple shape; the exactness
  (token identity + single consumption) is fixed.
- Sites + roles: definitions = target `:80` + `:85` (names); token minted
  per-mount `views.py:552` (`object()`). Writer = `request_body.py:242`
  (after setup + boundary, only when mount readable). Consumer =
  `views.py:554-559` (`prepared_view`: exact shape check + `delattr`). Oracle
  = `tests/test_views.py:294-305` (constructs the tuple FROM the constants,
  drives the callback, asserts dispatch-on-prepared + consumption).
  Projection = target `:28-35` + `views.py:529-538`.
- Challenges: rename → 1 each; reshape → 1 grammar / 2 halves (round-trip
  pair — one body impossible across modules and request phases); relax check
  → reader only; singleton token → breaks decorator-copied-callback
  exactness (rejected: `views.py:532-535` states the divergence it prevents).
- Owner + lifetime: target owns the names; each handoff lives from
  `process_view` to the callback's first read, then deleted. Publish point =
  post-boundary; invalidated by consumption. Pure agreement — no cache.
- Migration: none — writer and consumer already compose the constants.
- Distinct behavior: the mount-token read is guarded (`:238-240`: raising →
  `None`, boundary still stamped) while the prepared-view consumption is
  strict (malformed → fall back to a fresh instance, never dispatch a
  stranger's). Optimization vs trust: the handoff saves a construction; it
  never authorizes one. Recorded at both owners' docstrings.
- Behavioral proof: prepared/fresh dispatch pair `static-reviewed` (oracle
  pins prepared-dispatched, stamp-consumed, and fresh-fallback);
  unreadable-mount row (`:3210-3246`) pins stamp-without-handoff.
  `static-reviewed`. No suite run needed.
- Structural gate + negative control: the oracle builds the tuple from the
  constants, so a writer/reader shape drift fails the row; negative control =
  a malformed handoff dispatches fresh (the `None` arm), which the same test's
  fresh half pins. `static-reviewed`.
- Coupling: none.
- Freshness: same five HEAD blobs as F1.

### F4 — Boundary method name `_BOUNDARY_METHOD` (family)

- Contract + variation: the single name that (a) the middleware probes on a
  marked callback's `view_class` pre-construction, (b) the middleware invokes
  on the built instance, and (c) the mixin defines. Varies on spelling; the
  probe/invoke unity is the load-bearing property (target `:36-46`).
- Sites + roles: definition of the NAME = target `:95`; definition of the
  METHOD = `views.py:584`. Consumers = `request_body.py:336` (probe) + `:230`
  (invoke), both through the constant. Oracles =
  `test_the_probed_boundary_method_is_the_one_the_package_views_define`
  (`:3664-3680`: identity
  `getattr(mixin, _BOUNDARY_METHOD) is mixin._enforce_request_boundary` +
  both-transport callability) and
  `test_the_middleware_runs_the_boundary_it_probed_the_class_for`
  (`:3683-3721`: minimal class installed via `setattr` from the constant,
  never spelled); independent literal oracle = `:3222-3245` (fixture defines
  the method under its literal name — a rename of either side fails the
  stamp assertion). Projections = target `:36-46`, middleware `:204-210`.
- Challenges: rename → 2 (name + method). IRREDUCIBLE without violating a
  stronger principle: deriving the name from the method requires the
  middleware to import views — the exact dependency this module exists to
  prevent (principle 7: dependency direction wins); defining the method under
  the constant (`setattr` instead of `def`) obscures the method for subclass
  overrides. The junction is instead pinned by the identity oracle, which
  fails closed in both rename directions. Probe/invoke split → impossible by
  construction (single constant, two reads). This is the "one owned
  translation" shape (principle 2): the name table produces it, both sides
  read it.
- Owner + lifetime: target `:95` owns the name; `views.py:584` owns the
  method. Process-lived; the junction is valid at import and checked by the
  oracle.
- Migration: none — both middleware uses already read the constant (verified
  by reading `:230` and `:336`: no literal attribute access).
- Distinct behavior: the probe requires a CALLABLE on the CLASS (not mere
  presence, not on the instance — avoids running a foreign `__init__`);
  running an accepted boundary that raises non-`HTTPException` is deliberately
  unguarded (Decision 18: a guard would sit across the cap's own errors; card
  053's second open question keeps the decision open — no oracle may pin
  today's outcome).
- Behavioral proof: the three oracle rows `static-reviewed` (identity pin +
  probe/invoke unity + literal-spelling sensitivity); "no literal at either
  call site" verified by reading, `static-reviewed`. No suite run needed.
- Structural gate + negative control: the identity assertion is the gate — a
  method renamed without the constant (or vice versa) fails it; the minimal
  class row fails a call site that stops reading the constant
  (recognition-accepts-but-invocation-misses → `AttributeError`, not a
  stamp). Negative control = forged classes carrying a non-callable or
  raising attribute under the name are declined (pinned `:3640-3661`).
  `static-reviewed`. No bespoke existence test per helper is proposed: the
  census (no second spelling of the string in-package) is the replayable
  population check.
- Coupling: none (the card-053 open question constrains what oracles may pin,
  not this finding's verdict).
- Freshness: same five HEAD blobs as F1.

### F5 — Chain-published request variable (family)

- Contract + variation: the request the boundary middleware is currently
  handling, or `None` outside any such request — the one per-request fact the
  exemption needs that a process-wide callback attribute cannot carry.
  `ContextVar` (not thread-local) so the async chain sees it; set/reset
  around the downstream call so it cannot leak. Varies on identity only.
- Sites + roles: definition = target `:103-106`. Publishers =
  `request_body.py:163/167` + `:176/180` (both transports, both in
  `finally`). Sole reader = target `:146`. Oracles = async reset row
  (`:3391-3423`: True handled-unstamped / False handled-stamped / True after
  raise) + every full-chain row that withdraws the exemption (sync and async
  live rows). Projection = target `:97-102`.
- Challenges: re-identify → 1; re-scope publish → middleware's rule (0 in
  target — downstream-spanning is required because the reader is a later
  chain entry); merge with a sibling ContextVar → R2 (declined per sibling).
- Owner + lifetime: target owns the variable. Per-request binding: published
  at chain entry, reset in `finally` on the way out (both transports);
  default `None` outside. No lease (unlike the optimizer frame — R2 states
  why: a copied context holding a stale REQUEST still answers the predicate
  correctly, because the stamp it consults lives on that same request
  object; there is no cross-request retention of plans or budgets to revoke).
- Migration: none — publishers and reader already compose the variable.
- Distinct behavior: the variable answers "which request is being handled",
  never "was the boundary run" — the stamp answers that, on the published
  object. Two facts, two carriers, one predicate joining them.
- Behavioral proof: probe P1 steps 2–5 `execution-verified` (None → True,
  handled-unstamped → True, handled-stamped → False, reset → True);
  async reset row `static-reviewed`. No suite run needed.
- Structural gate + negative control: the async row fails a lost reset
  (True-again-after-raise) and a lost publish (withdrawal never happens);
  negative control = raising downstream still resets (pinned `:3415-3423`).
  Observation for the middleware file item (not a defect): no sync-twin row
  pins `__call__`'s reset explicitly — behavior symmetric by construction,
  pin single-sided. `static-reviewed`.
- Coupling: none.
- Freshness: same five HEAD blobs as F1; sibling ContextVar bodies excluded
  per R2 (`orders/sets.py` `HEAD 6044ab1a11c7`, `optimizer/_context.py` `HEAD
  3d8dcfdfba5b`, `extensions/operation_state.py` `HEAD b2674a22d2df`,
  `permissions.py` `HEAD 757dce34cecd`, `utils/operation_lease.py` `HEAD
  10c164b731b3`).

### F6 — Withdrawable exemption predicate (family)

- Contract + variation: the package view callback's `csrf_exempt` value —
  true unless a chain entry has actually run the boundary for THIS request.
  Three states, two clauses: no middleware handling → True; handled but
  unstamped → True; handled and stamped → False. Varies on the answers; the
  two-clause shape is fixed (target `:137-145` rejects the fold).
- Sites + roles: definition = target `:137-147` (sole `__bool__` in the
  package — census-verified). Upstream reader = Django's
  `CsrfViewMiddleware.process_view`
  (`getattr(callback, "csrf_exempt", False)`, installed Django 6.1
  `django/middleware/csrf.py:420`). Oracles = async reset row (all three
  answers through the object itself, `:3411-3423`), no-middleware rows
  (`:3427-3455`, unconditionally true), declined-callback rows (`:3458-3518`,
  true + complete check), live configured-class row (false → class runs).
  Projections = target `:109-135`, Decision 18 three-state list, glossary.
- Challenges: flip any answer → 1; collapse clauses → already rejected at the
  owner (same answers today, unreadable at three cases); read a second fact
  → 1 (no second predicate exists).
- Owner + lifetime: target `:137-147`. Stateless pure predicate over
  (ContextVar, request stamp); valid wherever both carriers are.
- Migration: none — single predicate stands.
- Distinct behavior: "absent middleware" and "handled but unstamped" want the
  same answer for different reasons — kept as two clauses so a third case
  stays readable. It is never a bypass in either state: exactly one complete
  CSRF check runs past the boundary (Decision 18 guarantee; Django's
  `csrf_processing_done` makes the double-arrangement one check).
- Behavioral proof: probe P1 steps 2–5 `execution-verified` (full truth
  table through the real singleton); upstream read shape verified in the
  installed Django (`csrf.py:420`), `execution-verified` (grep, not a run —
  structural fact about upstream source); oracle rows `static-reviewed`. No
  suite run needed.
- Structural gate + negative control: the async row pins BOTH clauses plus
  the withdrawal through the object Django consults; negative controls =
  declined-callback complete-check rows (true must still protect) and the
  configured-class call log (false must really hand over — "Nothing else
  here can fail if that stops happening", live row docstring).
  `static-reviewed`.
- Coupling: none.
- Freshness: same five HEAD blobs as F1; upstream Django 6.1
  `django/middleware/csrf.py:420` (installed `.venv`, untracked — version
  recorded, not a blob).

### F7 — Shared exemption singleton (family)

- Contract + variation: one instance shared by every package view callback —
  it carries no per-view state; its answer is a property of the request, not
  the mount. No variation: stateless by construction.
- Sites + roles: definition = target `:152`. Consumer = `views.py:579`
  (bound on every `as_view` callback, both transports). Oracles: behavior
  rows (`:2543` both callbacks truthy-true) — no identity oracle pins
  `is`-sharing, and none is owed (see Behavioral proof).
- Challenges: per-view instances → 0 observable difference (stateless
  instances answer identically); per-request instances → same. The sharing
  is provable only structurally (single assignment site, one binding
  statement executed per mount).
- Owner + lifetime: target `:152`. Process-lived; immutable (no attributes).
- Migration: none — single site stands.
- Distinct behavior: none — sharing vs re-instantiation is deliberately
  unobservable. No gate is proposed for the sharing: an identity pin would
  relieve no change obligation (replacing the singleton with per-call
  instantiation changes nothing observable), and a bespoke existence test
  per helper is what DRY forbids.
- Behavioral proof: P1 asserts `type(ex) is _CsrfOrderingExemption`
  `execution-verified`; mount behavior rows `static-reviewed`. The
  unobservability claim rests on reading the class body (no `__init__`, no
  attributes, pure `__bool__`) — `static-reviewed`.
- Structural gate + negative control: none owed (see above); the behavior
  rows fail any stateful replacement that answers differently.
- Coupling: none.
- Freshness: same five HEAD blobs as F1.

### F8 — Stdlib-only layering (family)

- Contract + variation: the target imports nothing but the standard library
  at runtime (`contextvars`, `typing`), so both protocol parties can depend
  on it without a cycle and neither party imports the other. Django appears
  only under `TYPE_CHECKING`. No legitimate variation — any runtime
  first-party/django import breaks the design (target `:10-11`).
- Sites + roles: definition = target `:57-64` (imports). Structural
  consumers = the two `from ... _boundary_ordering import` blocks
  (`views.py:95-101`, `request_body.py:89-96`) — constants only. Negative
  census: no `views` import in `request_body.py`, no `request_body` import in
  `views.py` (verified by reading both import blocks).
- Challenges: add a runtime import → breaks the stated design; probe P1 step
  1 fails. Move a constant into either party → the other party must import
  across, reintroducing the coupling.
- Owner + lifetime: target `:57-64`. Valid at import, forever.
- Migration: none — closure already minimal.
- Distinct behavior: the `TYPE_CHECKING` import of `HttpRequest` is the one
  deliberate seam — typing without runtime cost.
- Behavioral proof: probe P1 step 1 `execution-verified`: the file executes
  standalone via `importlib.spec_from_file_location` with zero `django*`
  modules in `sys.modules`. Replay: `uv run python
  docs/dry/temp-tests/dry-file-_boundary_ordering-r2-w1/probe_exemption.py`.
  (First probe revision failed on a probe bug — importing through the package
  root pulls Django via `__init__`; fixed by loading the file directly.
  The failure and fix are both in the probe's history, not the target's.)
- Structural gate + negative control: P1 is the gate (fails on any added
  runtime import); negative control = the probe asserts `django` absent from
  `sys.modules` BEFORE loading, so a pre-polluted interpreter fails loudly
  instead of passing vacuously. A permanent import-linter gate is card 053's
  own Slice work ("import-linter leaf wording") — this item proposes none,
  to avoid front-running the owning card. `execution-verified` (probe) /
  `static-reviewed` (negative census).
- Coupling: none (card 053 owns the future permanent gate; no dependency —
  this finding's verdict does not need it).
- Freshness: target `HEAD 197eea8e01cb`; both parties' import blocks at
  their F1 blobs; probe file untracked (scratch scope, retained for Worker 2).

### R1 — Boundary recognition vs toolbar `view_class` read (rejected)

- Considered: unifying "recognize a callback by `view_class`" across
  `request_body.py::_package_view_instance` and
  `middleware/debug_toolbar.py:233`.
- Contract difference: the boundary asks "can a chain entry RUN this
  callback's boundary here?" (marker + class + mapping + callable boundary +
  buildable — five clauses ending at the boundary, every failure a decline
  that keeps the view-local arrangement); the toolbar asks "is this ANY
  Strawberry Django view?" (`isinstance`/`issubclass` against `BaseView` for
  response tagging). Different questions, different answer uses (run a
  security boundary vs tag a response), different failure costs (decline vs
  skip-tagging). A shared recognizer would couple a security gate to a
  developer-only overlay.
- Trigger: a second middleware needing runnable-boundary recognition (a
  second RUNNER, not a second reader of `view_class`).
- Freshness: toolbar `HEAD 5360149bfa20`; middleware `HEAD e6e32e785ec8`.
  Rejection recorded here (file item); durable prose already lives at both
  owners' docstrings (boundary: `:256-270`; toolbar: `:221-232`).

### R2 — Boundary ContextVar vs sibling ContextVars (rejected)

- Considered: one shared "current request / current scope" variable across
  `_boundary_middleware_request`, `_ORDER_NORMALIZATION_CAPTURE`
  (`orders/sets.py:197`), `_execution_frames` (`optimizer/_context.py:204`),
  `_RUNNER_SCOPES` / `_RESUME_REGISTRARS`
  (`extensions/operation_state.py:272/286`), `_cascade_state`
  (`permissions.py:172`).
- Contract difference per sibling: orders capture is a GraphQL-resolution
  ledger with close-under-lock semantics (a descendant may still publish);
  the optimizer frame sits behind an `OperationLease` because token reset
  cannot revoke copied contexts holding plans/budgets; runner scopes answer
  "innermost runner" for operation nesting; cascade state is traversal-local.
  The boundary variable is uniquely published by a MIDDLEWARE around the
  downstream call and uniquely read by DJANGO ITSELF (via the exemption
  object in `process_view`) — no sibling crosses the Django-core boundary,
  and no sibling shares the chain-entry lifetime. Merging any two would
  couple a middleware-chain fact to a GraphQL-execution fact with different
  publishers, readers, and end-of-scope semantics (reset vs lease-close vs
  close+reset).
- Trigger: a second chain-published fact read by Django core itself (same
  publisher, same reader, same lifetime).
- Freshness: the five sibling blobs listed in F5 + target `HEAD
  197eea8e01cb`. Rejection recorded here; durable prose at the owner
  (target `:97-102`: why a ContextVar, why set/reset around downstream).

### R3 — Attribute marks vs `PrivateAuthority` (rejected)

- Considered: filing the boundary marks behind `utils/private_state.py`'s
  tamper-proof storage instead of plain attributes.
- Contract difference: `PrivateAuthority` defends configuration against
  consumer tampering (resolver-writable carriers, process-lived owners);
  the boundary marks are COOPERATIVE signals that MUST be readable and
  writable by all parties — including deployment decorators that copy them
  via `functools.wraps` (the handoff's exactness depends on the copy,
  `views.py:532-538`) and Django's own resolver-held callback. Hiding them
  would break the cooperation they exist for. Opposite threat models:
  authority-vs-tamper vs agreement-vs-divergence.
- Trigger: a mark whose readers must be protected from consumer writes
  (i.e. a mark that becomes a policy).
- Freshness: `utils/private_state.py` `HEAD 08088b820ac2`; target `HEAD
  197eea8e01cb`. Rejection recorded here; durable prose at the owner
  (target `:16-20`: attribute rather than class check, so recognition needs
  no import).

## Defects

### D1 — Card-053 open-question premises went stale at HEAD (adjacent prose; self-homed, not a release blocker)

- What: the first bullet under card TODO-ALPHA-053-0.0.15's "Open question"
  (`KANBAN.md`, "Two safe-direction costs in the middleware-ordering audit")
  states two premises that HEAD contradicts. (a) "a chain spelled
  `[boundary, csrf, boundary]` is refused at startup, because the audit keeps
  the *last* boundary index" — the audit at
  `middleware/request_body.py:363-374` keeps the FIRST boundary index
  (`boundary_index is None` guard; docstring `:355-357`; oracle
  `test_the_first_boundary_entry_is_the_one_the_ordering_is_measured_against`),
  so that chain is ACCEPTED at HEAD. (b) "two adjacent boundary entries
  measure the body twice" — `process_view` early-returns on the stamp
  (`:216`), and `test_duplicate_boundary_entries...` (`:3724-3761`) pins
  one measurement. The bullet's framing ("deliberately left unpinned by any
  test") is likewise stale: both behaviors are pinned now.
- Owner: card TODO-ALPHA-053-0.0.15 itself (rendered card prose; fix = card
  edit + rerender). Already homed — closeout ticks, no homing search owed.
- Status: UNFIXED (recorded, not repaired — a file item does not edit the
  board, and the prose is the card's own to reword).
- Explicitly NOT a release blocker per AGENTS.md rule 35: no contract row is
  broken by any wire or configuration input — the CODE is correct and pinned;
  only the card's description of it predates the fix. Robustness/prose row.
- The bullet's sibling (forged callable boundary raising out of
  `process_view`) is still live and correctly unpinned — untouched by this
  defect; F4 records its constraint.
- Freshness: `KANBAN.md` `HEAD bd1f3f451ee5` (clean); middleware `HEAD
  e6e32e785ec8`; tests `HEAD 4dc9a2572350`.

No other defects. In particular: no guard-missing member (axis 6 enumerated
clean), no docstring contradicting its body (every cited docstring claim was
checked against its body — including the "first entry" audit prose and the
two-clause predicate rationale), no layering violation (F8).

### D-W2-1 (Worker 2; minor, prose) — middleware docstring "two marks" vs four at HEAD

- What: `middleware/request_body.py` module docstring says the exemption
  "lives in `_boundary_ordering.py` ... together with the two marks"
  (`:45-46`). At HEAD the module holds FOUR marks (`_BOUNDARY_MARKER`,
  `_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`;
  `_BOUNDARY_METHOD` is explicitly "not a mark" per the target's own
  docstring, then and now). History: exact when it landed in `dc2b73d2`
  (module held exactly MARKER + ENFORCED + METHOD); `18550f5d` added MOUNT
  + PREPARED_VIEW (3 -> 5 `_BOUNDARY*` assignments) without updating it —
  stale-by-growth, not wrong-on-its-date. This qualifies the "no docstring
  contradicting its body" sentence above (that sentence stands as Worker
  1's pass-1 record; this entry is the correction).
- Owner: File `middleware/request_body.py` (the sentence lives there; fix =
  "together with the marks", count-free). NOT fixed inside this item.
- Status: UNFIXED (recorded for Worker 0 homing at closeout).
- Explicitly NOT a release blocker per AGENTS.md rule 35: no behavioral
  contract breaks; no wire/config input reaches it. Prose row.
- Freshness: middleware `HEAD e6e32e785ec8`; target `HEAD 197eea8e01cb`.

## Pending execution

None. No `proof:` entry: every conclusion resting on a probe is
`execution-verified` by P1 (replay: `uv run python
docs/dry/temp-tests/dry-file-_boundary_ordering-r2-w1/probe_exemption.py` —
settings-free, read-only, no DB); all other verdicts are structural
(single-ownership censuses + existing permanent oracles, `static-reviewed`).
No `gate:` entry: no production edit was made, so no regression witness is
owed by this item. Sharded and Postgres cells: inapplicable by construction —
the target reaches no database, alias, or dialect decision (its runtime
closure is the standard library; the probe runs without Django settings),
stated here for Worker 2's judgment.

Probe custody: `docs/dry/temp-tests/dry-file-_boundary_ordering-r2-w1/`
(untracked; sole file `probe_exemption.py`) is this item's only scratch
scope — retained for Worker 2, for Worker 0 to remove by explicit path after
`verified`. No other scope touched.

## Index rows for Worker 0

One consolidated family row (no family item owed — nothing to merge) plus
three rejection rows. Suggested exact rows for the plan's
`## Responsibility index`:

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `request-body-boundary-ordering` | `_boundary_ordering.py` (name/protocol owner; method defined `views.py:584`) | `_boundary_ordering.py`, `views.py`, `middleware/request_body.py` | File `_boundary_ordering.py` | consolidated |
| Boundary recognition vs toolbar `view_class` read | `middleware/request_body.py::_package_view_instance` (rejection recorded here) | `middleware/request_body.py`, `middleware/debug_toolbar.py` | File `_boundary_ordering.py` | rejected |
| Boundary ContextVar vs sibling ContextVars | `_boundary_ordering.py::_boundary_middleware_request` (rejection recorded here) | `_boundary_ordering.py`, `orders/sets.py`, `optimizer/_context.py`, `extensions/operation_state.py`, `permissions.py`, `utils/operation_lease.py` | File `_boundary_ordering.py` | rejected |
| Attribute marks vs `PrivateAuthority` | `_boundary_ordering.py` (rejection recorded here) | `_boundary_ordering.py`, `utils/private_state.py` | File `_boundary_ordering.py` | rejected |
| `prepared-view-handoff-shape` | TBD by family item (candidates: `_boundary_ordering.py` via pack/validate helpers, or `views.py`) | `_boundary_ordering.py`, `views.py`, `middleware/request_body.py` | Family `prepared-view-handoff-shape` | open |

Revision-2 pointer (run 2): the `open` row above is the Difference-1 horn-(a) routing — see `## Iterations` Rev-2-1 for the reshaped-challenge count, sites, and carve-out of the `consolidated` row (which now covers F3's names/token/policy only).

Status rationale for `consolidated` (for Worker 0 to confirm or re-home):
the eight rules already have exactly one authoritative definition each (F4
has two only at the irreducible name/method junction, pinned by an identity
oracle), verified at HEAD by this item. Dispatching a family item would have
nothing to merge; the spec-046 slice did the consolidating, this item proved
it held. If Worker 0 prefers `open` + a verification-only family pass, the
artifact supports that reading too — but no edit would come out of it.

## Judgment

Proved zero-edit result. The target is a single-owner protocol module in the
strongest sense this cycle measures: eight rules, eight definitions, every
consumer composing by name, every variation axis challenged, the one
two-definition junction (F4) irreducible and oracle-pinned, three cross-site
candidates declined with contract differences and triggers, the matrix
discharged against the real surface, and the one probe `execution-verified`
with its negative control. The single defect is adjacent card prose, already
self-homed, explicitly not a release blocker. Nothing in the target, its
consumers, or its oracles needs to move. `Status: ready-for-verification/1`.

## Independent verification (Worker 2) — expectations (Phase A)

Run 0.0.15 2026-09-21-2, File `_boundary_ordering.py`. Worker 1's artifact and
scratch were not opened in any form; everything below is derived independently.
HEAD at start `bfaee91dcd332a5f86250fff90ab21b377bc674e`, at end the same
(recorded again at the foot). Target clean at HEAD blob
`197eea8e01cb405f38b21022689ed54970efcb97` (matches dispatch; working tree
equals HEAD bytes). Both protocol parties clean:
`views.py` and `middleware/request_body.py` show no `git status` entry, so
working-tree reads of those two files are HEAD reads. Every package-wide
census below ran as `git grep -n <symbol> HEAD` (HEAD-pinned; immune to the
concurrent dirt). ITEM_BASELINE=`3bccf53c3127f104b2f57fc87c791a3b04b1d976`
noted, not needed: Phase A touches only the scope dir
`docs/dry/temp-tests/dry-file-_boundary_ordering-r2-w2/` (created by this
pass; no collision with retained scopes).

### Enumeration

Instrument: `ast.Module.body` walk of the target (docstring + imports +
guard listed, every binding recorded). Count: **8 defined names** (5 stamp /
name constants, 1 ContextVar, 1 class with 1 method, 1 singleton instance)
plus the module-docstring protocol statement (row R9).

1. `_BOUNDARY_MARKER` (L70) — callback mark literal.
2. `_BOUNDARY_ENFORCED` (L76) — request stamp literal.
3. `_BOUNDARY_MOUNT` (L80) — per-mount token mark literal.
4. `_BOUNDARY_PREPARED_VIEW` (L85) — prepared-view handoff stamp literal.
5. `_BOUNDARY_METHOD` (L95) — boundary method-name literal.
6. `_boundary_middleware_request` (L103) — ContextVar.
7. `_CsrfOrderingExemption` (L109, method `__bool__` L137).
8. `_CSRF_ORDERING_EXEMPTION` (L152) — singleton instance.

### Rules, sites, challenges, owners, assignments

Role tags: D = authoritative definition, C = consumer / enforcement site,
O = independent oracle, P = explanation / projection. Counts below count D
only; C/O/P are listed, never counted.

**R1 — Request-body boundary callback mark (`_BOUNDARY_MARKER`).**
D: target L70 (literal spelled exactly once package-wide; literal sweep for
`graphql_request_body_boundary` returns only the four constant assignments).
C: `views.py::_RequestBodyBoundaryMixin.as_view` writes `True` (L580);
`middleware/request_body.py::_package_view_instance` reads by truthiness
(L330). O: `tests/test_views.py` (marker asserts, forged marked callbacks)
and live `test_transport_api.py` (real-mount marker + recognition). P:
target docstring, middleware/views docstrings, spec-046 Decision 18.
Challenges: (a) rename the literal (e.g. versioned suffix) -> D moves: 1
(the constant); both C sites compose by name and follow. (b) change the
value grammar (True -> version token) -> D moves: 1; the truthiness read is
a C-side contract that tolerates any truthy. Owner I would choose: the
target (it holds the literal today; both parties already import it).
Assignment: **file-local**. Index row: family `Request-body boundary
callback mark`, owner `_boundary_ordering.py::_BOUNDARY_MARKER`, files
target + `views.py` + `middleware/request_body.py`, holding File
`_boundary_ordering.py`, status `file-local`.

**R2 — Boundary-completed request stamp + single-writer invariant
(`_BOUNDARY_ENFORCED`).** D: target L76 (name) + the single writer
`middleware/request_body.py::process_view` L243 (`setattr(request, ..., True)`;
package-wide sweep shows no other writer; the literal is spelled nowhere
else). C (three reads, three distinct questions): target L147 (part of "view
still owns ordering?", with the ContextVar clause),
`middleware/request_body.py` L216 (re-entrancy: an earlier chain entry
already ran), `views.py::_enforce_request_boundary_once` L621 (skip
redundant measure). O: `tests/test_views.py` stamp asserts (present /
absent / falsy), live CSRF-class-behind-boundary row. P: target docstring
"one writer" paragraph, Decision 18 three-states prose. Challenges: (a)
rename the literal -> D: 1. (b) change the value grammar preserving
truthiness (e.g. True -> timestamp) -> D: 1 (writer); the three C reads
follow without edits, which is what proves they are consumers, not
definitions. (c) posit a second writer -> package-wide `setattr(request,`
sweep finds only L242/L243 (the handoff tuple + this stamp): none exists.
The three identical `getattr(request, _BOUNDARY_ENFORCED, False)` spellings
are the language-level optional-attribute idiom (same shape as Django's own
`user` / `session` / `_body` reads), not a rule with three owners. Owner:
target for name + meaning; writer stays in the middleware (only a chain
participant that ran the boundary may write). Assignment: **file-local**.

**R3 — Per-mount opaque token (`_BOUNDARY_MOUNT`).** D: target L80 (name);
single producer `views.py::as_view` L552+L581 (`mount = object()`,
stamped on the callback). C: middleware L238 reads opaquely (threads into
the handoff tuple; None means "stamped, no handoff"); `views.py`
`prepared_view` L556 compares by identity (`is not mount`). O:
`tests/test_views.py` mount-token handoff rows. Challenges: (a) token
representation change (`object()` -> uuid string) -> D: 1 (producer); C
sites thread/compare opaquely and follow. (b) mount-absent semantics change
-> producer + handoff-skip branch, one rule, one producer. Owner: target
for the name; producer stays in `as_view` (the mount is born there).
Assignment: **file-local**.

**R4 — Prepared-view handoff mark name (`_BOUNDARY_PREPARED_VIEW`).**
D: target L85 (name, literal spelled once). C: middleware L242 packs
`(mount, view)`; `views.py::prepared_view` L555-L559 validates
(exact-tuple, len 2, token identity), consumes once (`delattr`), returns
`[1]`. Exactly one reader package-wide, so consume-once has exactly one
consumer. O: `tests/test_views.py` handoff rows (prepared instance
dispatched, stamp consumed, second callback cannot inherit). Assignment
for the NAME: **file-local**. The handoff TUPLE SHAPE, however, is a
second rule riding on this mark: see the routed family below (F-new-1).

**R5 — Boundary method name (`_BOUNDARY_METHOD`).** D: target L95 (literal
`"_enforce_request_boundary"`, spelled once; the method itself is defined
once at `views.py` L584). C: middleware L336 probes
`callable(getattr(view_class, _BOUNDARY_METHOD, None))` and L230 invokes
`getattr(view, _BOUNDARY_METHOD)(request)` — both read the constant, the
documented one-fact shape. O (the contrast case that proves the mechanism):
`test_the_probed_boundary_method_is_the_one_the_package_views_define` pins
constant-against-definition with a literal attribute spelling
(`getattr(mixin, _BOUNDARY_METHOD) is mixin._enforce_request_boundary`),
and `test_the_middleware_runs_the_boundary_it_probed_the_class_for` pins
constant-against-call-site without spelling the name. Challenges: (a)
rename the method -> D: 1 (constant) + the definition it names move as one
fact; both C sites follow by reference; both O tests fail until moved.
(b) method moves to another module -> constant untouched; probe still
resolves by name. Owner: target (it holds the name today). Assignment:
**file-local**.

**R6 — Boundary-middleware request publication (`_boundary_middleware_request`).**
D: target L103 (sole ContextVar binding; ContextVar-name literal spelled
once). C: middleware `__call__` L163/L167 and `__acall__` L176/L180
(set/reset around downstream in `finally`); target L146 (exemption read).
No other publisher package-wide (every other ContextVar owns a different
rule: operation state, execution frames, cascade state, budget, write
pipeline). O: behavioral — exemption truth-table rows and the
publish/reset-through-raise tests exercise it without naming it (naming it
would couple the oracle to the mechanism; the value it publishes is
observable only through the exemption). Challenges: (a) scope change
(publish `(request, chain-id)`) -> D: 1 + its C sites listed. (b) posit a
second publisher -> none found. Owner: target. Assignment: **file-local**.

**R7 — Withdrawable CSRF ordering exemption predicate
(`_CsrfOrderingExemption.__bool__`).** D: target L137-L147 (two-clause
predicate; the ONLY implementation of "view still owns ordering" —
package-wide `csrf_exempt` assignment sweep finds exactly one site,
`views.py` L579, and no `csrf_exempt` decorator use). C: Django's
`CsrfViewMiddleware.process_view` reads the value's truthiness (framework
consumer, outside the package). O: `tests/test_views.py` three-state rows
(true outside any chain / true handled-but-unstamped / false stamped) plus
the live row proving the configured CSRF class runs behind the boundary.
P: class docstring "never a bypass" paragraph, Decision 18. Challenges:
(a) add a fourth state (e.g. stamped-by-foreign) -> D: 1. (b) fold the two
clauses into one `getattr` -> D: 1; the two-clause split is the documented
readability contract. Owner: target (it defines the predicate today; the
single `csrf_exempt` assignment in `views.py` is its C site). Assignment:
**file-local**.

**R8 — Shared exemption singleton (`_CSRF_ORDERING_EXEMPTION`).**
D: target L152 (one instance). C: `views.py` L579 assigns it as every
package callback's `csrf_exempt`. O: `bool(...) is True/False` asserts read
through the shared object. Challenge: posit per-view instances -> no
per-view state exists (answer is a property of the request, proven by the
predicate reading only the ContextVar + stamp); one instance is forced, not
incidental. Owner: target. Assignment: **file-local**.

**R9 — Ordering-protocol placement (marks live here; parties import inward
only).** D: target module docstring (views owns the boundary per Decisions
7/9; middleware owns lifecycle placement per Decision 18; the marks live
here because neither party imports the other and this module imports
nothing but stdlib). Mechanically verified, not trusted: AST probe shows
the target's runtime imports are `__future__` + `contextvars` + `typing`
(all stdlib/compiler) with `django.http` under `TYPE_CHECKING` only, and
the module executes standalone via `spec_from_file_location` with no
package import; `views.py` package imports are `_boundary_ordering`,
`_request_body`, `conf`, `exceptions` (no `middleware.*` — the probe's one
`request_body` hit is the `_request_body` measurement module, not the
middleware); `middleware/request_body.py` package imports are
`_boundary_ordering` + `exceptions` (no `views`). P: middleware/views
docstrings restating the split, GLOSSARY middleware anchor, TREE.md
one-liners (projections). Challenge: posit the middleware importing
`views.py` (or vice versa) -> the barrier is load-bearing (import cycle /
leaf-import posture per Decision 18); the target's stdlib-only shape is
what makes the inward-only graph possible. Owner: target (the statement
lives in its docstring). Assignment: **file-local**.

**F-new-1 — Prepared-view handoff tuple shape (ROUTED, new family).**
The grammar "`(mount token, prepared view instance)`, token first" is
encoded at two code sites with no coded single definition: the pack
(`middleware/request_body.py` L242) and the unpack
(`views.py::prepared_view` L555-L559: exact-type + len-2 + `[0]`-identity +
`[1]`-extraction). The target's `#:` comment states the shape in prose —
a projection, not a composable definition; neither code site invokes a
shared constructor/accessor. Challenge: posit a shape change (carry a
third element, e.g. a cap snapshot) -> authoritative encodings that must
move: 2 (pack + unpack validation/extraction). Consumers/oracles listed,
not counted: the mark constant (unchanged by a shape move), the
mount-absent skip branch, the handoff oracle rows. This is DRY.md axis 4
(pack/unpack) without one coded grammar, and the exact-type check couples
even representation experiments pack-side to the unpack-side pin. The
family item decides the landing: candidate owner `_boundary_ordering.py`
via pack/validate helpers (import-feasible — both parties already import
it), or rejection with the producer-construction vs defensive-validation
contract difference (the unpack guards exist because the request attribute
namespace is shared with foreign writers). Proposed index row: family
`prepared-view-handoff-shape`, owner TBD by family item, files target +
`views.py` + `middleware/request_body.py`, holding Family
`prepared-view-handoff-shape`, status `open`.

**Rejection R-A — `view_class` recognition: toolbar hierarchy check vs
boundary marker+method probe.** Considered shared form: "recognize a
callback by reading `view_class`". Contract difference: `debug_toolbar.py`
L233-L234 asks hierarchy membership (`isinstance(view, type) and
issubclass(view, BaseView)`, importing upstream's BaseView) to tag traffic
for toolbar injection (spec-042); `_package_view_instance` asks
boundary-runnability (marker + `view_class`/`view_initkwargs` bookkeeping
+ callable boundary method, no view import) to decide whether a boundary
can run safely (spec-046 Decision 18). Posit a change to either
recognition (e.g. toolbar tags non-Strawberry views; boundary requires a
second method) -> the other does not move. Trigger: a recognition change
both must follow (e.g. a shared forged-callback guard policy). Recorded
here; no family.

**Rejection R-B — Request-attribute stamping: `_is_graphiql` vs the
boundary stamps.** Considered shared form: "stamp the request object".
Contract difference: `debug_toolbar` writes a literal-attribute view tag
for response post-processing; the boundary stamps carry completion (R2)
and a prepared-instance handoff (R4) with single-writer / consume-once
lifecycles. No shared mechanism beyond `setattr` itself (language-level);
a shared stamping helper would couple unrelated lifecycles. Trigger: a
second toolbar stamp or a shared stamp-namespace policy. Recorded here; no
family.

Existing-family fit: none of the 13 querysets families (seal, awaitable
disposal, coercion, recourse wording, alias inheritance, row adapter,
post-set validation, sync boundary, seed/model read, lookup-path
resolution, wording, plus the two file-local/rejected rows) nor the 11
`__init__.py` rows (export surface, version, logger, DRF lazy hook,
exclusions, hygiene, pass-through, getattr hook, idiom, miss wording)
names a mechanism on this surface. No rule above belongs to any of them;
no existing family is proposed.

### Matrix discharge (against the target's real surface)

1. **Cross-flavor policy mirroring.** Searched: the transport boundary has
   no per-surface flavors (one mixin, one middleware); sibling flavors with
   adjacent mechanisms are `debug_toolbar` recognition (rejection R-A) and
   the `_is_graphiql` stamp (rejection R-B). No second flavor of any target
   rule exists.
2. **Sync/async twins.** The target has no async surface (no coroutine, no
   await). Its consumers twin correctly around the shared objects: both
   `as_view` arms call the shared `prepared_view` helper; both `run`
   overrides call `_enforce_request_boundary_once` first; middleware
   `__call__`/`__acall__` share the one ContextVar with a documented
   why-separate (`finally`-after-`await`). No twin of a target rule.
3. **Derived rather than repeated knowledge.** Searched by literal sweep:
   all four mark literals + the ContextVar name spelled exactly once each;
   both `_BOUNDARY_METHOD` uses read the constant (probe L336 + invoke
   L230); the mount token has one producer and is threaded opaquely. The
   one grammar derived twice is the handoff tuple shape -> routed as
   F-new-1.
4. **Inverse / round-trip pairs.** Pack/unpack handoff tuple -> F-new-1.
   ContextVar set/reset: two balanced twins, each `finally`-guarded,
   sharing one object (no pair to unify). Stamp write/read: one writer,
   three named-constant readers (consumers). Mark stamp/read: one writer,
   one reader. Exemption predicate: single implementation, framework
   consumer.
5. **Contracts restated in another medium.** Contract sources: spec-046
   Decisions 7/9/18 (read at HEAD; Decision 18's three-states and
   recognition-ends-at-the-boundary match the code). Oracles:
   `tests/test_views.py` (package tier; forges callbacks, pins the method
   name against the definition with a literal spelling, asserts the
   exemption truth table through the shared object) and live
   `test_transport_api.py` (real mount recognized through a real decorator;
   configured CSRF class runs behind the boundary). Oracle-independence
   note: tests import the mark *constants* (correct — the literal strings
   carry no wire contract; writer/reader agreement is guaranteed by
   construction), while the one value that IS load-bearing (the method
   name) is pinned against a literal spelling. Projections (listed, never
   counted): target/middleware/views docstrings, GLOSSARY middleware
   anchor, TREE.md one-liners, build-046 DONE plan, bug_hunt-0_0_15
   battery note, kanban tracked-path constant.
6. **Enforcement by omission.** Family enumerated: exactly two package
   views (`DjangoGraphQLView`, `AsyncDjangoGraphQLView`), both inheriting
   the mixin; the single `as_view` override stamps both marks + exemption
   on both (one test asserts both transports share the mixin's
   `__func__`); both `run` overrides call `_enforce_request_boundary_once`
   first; `routers.py` mounts via `as_view` and inherits the marks. No
   third view, no undecorated transport, no omitted member. The prepared
   view has exactly one consumer (consume-once safe). No gap.

### Defects

**D-W2-1 (Worker 2; minor, prose).**
`middleware/request_body.py` module docstring says the exemption "lives in
`_boundary_ordering.py` ... together with the two marks". At HEAD the
module holds four marks (`_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`,
`_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`; `_BOUNDARY_METHOD` is
explicitly "not a mark" per the target's own docstring, then and now).
History: the sentence was exact when it landed in `dc2b73d2` (module held
exactly MARKER + ENFORCED + METHOD); `18550f5d` added MOUNT +
PREPARED_VIEW (3 -> 5 `_BOUNDARY*` assignments) without updating it —
stale-by-growth, not wrong-on-its-date. No behavioral contract breaks; no
wire/config input reaches it. Owner: File `middleware/request_body.py`.
Fix shape: "together with the marks" (count-free, cannot rot again).

Non-defect observation (recorded so Phase B can compare, not routed): the
target's `_BOUNDARY_ENFORCED` comment names two readers
(`_enforce_request_boundary_once`, the exemption) but not the middleware's
own L216 re-entrancy read. Incomplete enumeration, not a contradiction —
no contract row breaks. Not a defect.

### Probes

- `probe_exemption.py` (this scope dir; execution-verified): loads the
  target standalone via `spec_from_file_location` (no package import —
  proves the stdlib-only claim by construction), asserts the exemption
  truth table True (outside chain) / True (handled, unstamped) / False
  (stamped) / True (falsy stamp) / True (after reset), singleton shape,
  ContextVar default None. Passes.
- AST import-separation probe (inline, re-runnable): target runtime
  imports stdlib-only; `views.py` imports no `middleware.*`;
  `middleware/request_body.py` imports no `views`. Passes (the probe's one
  `request_body` hit on `views.py` is the `_request_body` measurement
  module, verified by full dotted path).
- Census probes (all `git grep -n ... HEAD`, listed above): 8 names, 4
  literals, ContextVar name, `csrf_exempt` sites (1 assignment),
  `setattr(request|view` sites (4, all protocol), `view_class` readers
  (2 mechanisms, rejected), `getattr(request` readers, `process_view`
  definers (2), `as_view`/`BaseView` view family (2 views, 1 override),
  `_boundary_ordering` importers (2 package + 1 oracle + 1 generated
  path constant).

Phase-A HEAD tripwire: HEAD at end `bfaee91dcd332a5f86250fff90ab21b377bc674e`
— unmoved; every claim rests on that HEAD. Pre-finish gate: target still
blob `197eea8e01cb405f38b21022689ed54970efcb97` (no hunk by anyone);
artifact `docs/dry/dry-file-_boundary_ordering.md` never opened or
touched by this pass; scope dir contains only this section + the probe.
No verdict set (Phase B work).

## Independent verification (Worker 2) — reconciliation (Phase B)

HEAD `bfaee91d` unmoved across both phases; target + both parties still
clean (`git status` empty on all three). Phase-A section appended
mechanically (`cat >>` + 1 newline separator; tail `cmp`-identical over
20151 bytes) before this read. Worker 1's scratch (`probe_exemption.py`,
sole file) read and replayed green. Every `git grep` / `git show` below
is HEAD-pinned. Reconciliation is per-difference; agreements verified (not
sampled) are listed once and endorsed.

### Verified agreements (endorsed, no action)

- Enumeration: 13 nodes / 8 runtime names + 1 method — identical both
  passes (W1's table rows 1-13 match my AST walk member for member).
- F1, F2, F5, F6, F7, F8: sites, roles, counts, owners — agree. F5's
  lease-vs-reset distinction and F8's negative census verified
  independently (sibling set/get sites all inside GraphQL-execution
  modules; none middleware-published, none Django-read).
- F4: agree on substance (junction identified, irreducibility reasoned via
  dependency direction, identity oracle pinned). W1's count-2 framing of
  the name/method junction is the more careful statement; my Phase-A
  count-1 (constant-as-owner) is the terser view of the same junction.
  No action — the finding both of us defend is identical.
- R1, R2, R3: agree. R2's per-sibling differences and R3's opposite
  threat models (verified against `utils/private_state.py`'s own
  authority-vs-lifetime docstring) exceed my Phase-A trace; both carry
  contract differences + triggers and are sound.
- Matrix axes 1, 2, 5, 6: agree. Axis-2 single-sided pin confirmed (the
  async reset row `:3391` exists; no sync-twin reset row exists at HEAD);
  correctly an observation for the middleware item, not a defect.
- D1: verified verbatim (`KANBAN.md:370` under card
  TODO-ALPHA-053-0.0.15), both premises stale exactly as stated
  (first-index audit + `:3371` oracle; stamp early-return + `:3724`
  oracle), homing correct, non-blocker call correct. Endorsed.
- Freshness: all 15 recorded blobs re-hashed independently — 15/15 match
  (target `197eea8e01cb`, views `9f85b0df26a1`, middleware
  `e6e32e785ec8`, tests `4dc9a2572350`, live `17320f1ff335` via HEAD,
  five R2 siblings, private_state, toolbar, KANBAN, spec-046, GLOSSARY).
- Upstream fact: installed Django is 6.1 and `csrf.py:420` reads
  `getattr(callback, "csrf_exempt", False)` — exact.
- Oracle cites spot-checked at HEAD (`:2578` absence assert, `:3371`,
  `:3391`, `:3640-3661` forged rows, `:3724-3761` duplicate test) — all
  exact. P1 replays green (6/6); my Phase-A probe (complementary:
  falsy-stamp case) also green. Pending-execution empty + sharded/PG
  inapplicability reasoning endorsed (stdlib-only closure, settings-free
  probe, no DB/alias/dialect surface).
- Assignment shape: the single `consolidated` family row is accepted
  (Worker 0 confirms); file-local-vs-mega-family is presentational once
  every rule is homed — with the one exception below, which must land as
  an open family row or a fourth rejection row either way.
- Item diff: artifact + two scratch scopes only (both untracked, both
  retained for Worker 0); zero production edits. AGENTS.md prose rules
  hold (raw `path:NN` allowed in per-cycle artifacts; no feedback-file
  mention; no suite run — probes only, settings-free).

### Difference 1 (substantive): F3's two halves — revision required

W1's F3 reshape row counts "1 grammar, 2 halves" and files the handoff
tuple shape as consolidated on the ground that "one body is impossible
across modules and request phases". My Phase-A F-new-1 counts 2
authoritative encodings (pack `request_body.py:242`, unpack
`views.py:555-559`) with no coded single definition and routes an open
family. Phase-A was written blind; the disagreement is real and I hold
my position:

- The pack site constructs `(mount, view)`; the unpack site re-encodes
  the shape (exact-`tuple` + len-2 + `[0]`-identity + `[1]`-extraction).
  Neither invokes or derives from a shared shape definition — the
  target's `#:` comment is prose, a projection. A specific plausible
  change (carry a third element) moves both code sites: count 2.
- "One body impossible" conflates call sites with definitions. Two call
  sites must remain (different request phases), but the grammar need not
  be defined twice: both parties already import the target, so
  pack/validate helpers there are import-feasible with zero dependency
  change. The impossibility premise is unproven, so the consolidated
  filing does not follow.
- Per DRY.md, a row naming a second site is a family or a rejection with
  contract difference + trigger — F3 as written is neither (no trigger,
  no owner prose for the duality).

Reproducible feedback for Worker 1's revision pass (either horn is
acceptable): (a) route Family `prepared-view-handoff-shape`, status
`open`, files target + `views.py` + `middleware/request_body.py`, with
the reshape challenge (count 2), both halves as sites, and owner
candidates (`_boundary_ordering.py` via pack/validate helpers, or
`views.py`); or (b) record rejection R4 with the contract difference
(total construction from owned locals vs defensive validation of a
shared-namespace value + closure-bound token check + consume-once) and
the trigger (a third shape element or a second producer/consumer pair),
with one durable prose clause at the owner. Add the corresponding index
row (open family or fourth rejection). W1's F3 sub-rows ("halves
separable", "singleton token rejected") stand untouched — both verified.

### Difference 2 (trivial): two evidence-precision corrections, same pass

- Matrix axis 4 says the method-name string "occurs only at target `:95`
  plus the one independent literal oracle (tests `:3223`)". It is also
  spelled at tests `:2487` (`view._enforce_request_boundary(...)`) and
  `:3678` (`mixin._enforce_request_boundary`). Correct the census
  sentence. Verdict-neutral: all three are oracle-side; production has
  no literal (verified).
- System trace says both parties "import only the constants from here".
  The middleware also imports the ContextVar and the views import the
  singleton. Reword (e.g. "only names from here", or list precisely).

### Difference 3 (Worker 2 yields): _is_graphiql needs no formal row

My Phase-A R-B proposed a formal rejection row for the `_is_graphiql`
stamp; W1 judges it inline in matrix axis 1 ("distinct contracts"). Same
sites, same verdict — and W1's treatment is adequate: the shared form
("stamp the request") is language-level `setattr` with no framable
change challenge, which is matrix discharge, not a rejected candidate.
I withdraw the row requirement; no action.

### Difference 4 (defects): symmetric blind finds, both real

W1's D1 (card prose) and my D-W2-1 ("two marks" stale count, appended
above marked Worker 2) were each found blind by one pass and missed by
the other; both verified real. D-W2-1 qualifies W1's "no docstring
contradicting its body" sentence (history-proven stale-by-growth, not
wrong-on-its-date). Neither is a release blocker; D1 is self-homed,
D-W2-1 homes to File `middleware/request_body.py` at closeout. No
revision action for either beyond acknowledgment.

### Verdict

`Status: revision-needed` — one substantive item (Difference 1, either
horn) plus two one-line corrections (Difference 2). Resubmission returns
to this Worker 2 per DRY.md (fresh only if this context is gone).

## Iterations

### Revision 2 (Worker 1 re-pass) — horn (a) routed; Difference 2 corrected

Scope: Difference 1 (F3 shape, horn (a)), Difference 2 (two corrections +
one parallel-site twin), Differences 3–4 acknowledgment. Everything else in
the artifact stands as verified. Append-only: prior lines are untouched; each
item below supersedes by pointer. All line numbers re-derived against HEAD
bytes by probe P-R2 (see Rev-2-4), not copied from either pass.

#### Rev-2-1 (Difference 1, substantive): Family `prepared-view-handoff-shape` routed OPEN

Disposition: horn (a). The layout (arity 2, token first, positional) is one
rule with two coded encodings and no coded owner: the pack site constructs
it positionally (middleware/request_body.py:242 `setattr(request,
_BOUNDARY_PREPARED_VIEW, (mount, view))`, AST-verified Tuple of [mount,
view]); the unpack site re-encodes it (views.py:555-559: exact-tuple +
len-2 + [0]-identity against the closure-bound per-mount token from :552 +
[1]-extraction, then consume-once). The target states the shape in prose
(:82-84 `(mount token, prepared view instance)`) and defines no helper or
record type (AST defs == {_CsrfOrderingExemption, __bool__}) — a projection,
not a composable definition. Import-feasibility confirmed: both parties
import from _boundary_ordering (views.py:95-101, request_body.py:89-96) and
neither imports the other (AST imports only, so docstring citations cannot
pollute the answer).

Why route rather than reject: the shape-knowledge count is honestly 2 and
reducible. Carrying a third element moves pack + unpack-len-check today; with
a target-owned layout (record + keyword construction / named access) the
unpack needs no edit — the pack's remaining edit supplies DATA (the new
element's value, which only pack-side locals hold), and supplying an argument
is construction, not a shape definition. Reorder (token second) moves 2
today, 1 (the layout) with sharing. The construction-vs-validation difference
is real but scopes WHAT is shared (layout only), not whether: token mint,
closure-bound check, guarded mount read, consume-once, and fresh-fallback all
stay at their current owners under any landing. Unlike F4's junction, no
structural principle bars the sharing — dependency direction is satisfied,
since both parties already import the target. The family item decides the
landing (record vs helpers vs rejection-after-sweep); this routing carries no
consolidation verdict.

Routed family:

- Family: `prepared-view-handoff-shape`. Status: open. Holding item: Family
  `prepared-view-handoff-shape` (a file item never consolidates — no
  production edit here; the family item will).
- Files: `_boundary_ordering.py`, `views.py`,
  `middleware/request_body.py`.
- Contract + variation: the handoff VALUE's layout — arity 2, token first,
  positional — vs the names (stay F3), the token mint (stays views.py:552),
  and the validation policy (stays the unpack site). Varies on arity/order;
  the exactness requirement rides with the layout.
- Sites + roles: pack (middleware/request_body.py:242) = shape encoding;
  unpack (views.py:555-559) = shape encoding; target :82-84 = projection;
  oracle = tests/test_views.py:294-305 (builds the tuple FROM the constants,
  pins prepared-dispatched + consumed) + full-chain prepared-dispatch rows.
- Challenges: third element -> 2 (pack + unpack len-check); reorder -> 2
  (pack construction + unpack [0]/[1] use); validation strictness -> unpack
  only (out of family scope, stays F3 per the standing sub-row).
- Owner candidates: `_boundary_ordering.py` via pack/validate helpers (a
  layout record is the sub-variant — keyword construction / named access is
  what frees the unpack), or `views.py`. Family item decides.
- Stays separate under any landing: per-mount token mint, closure-bound
  identity check, guarded mount read (:238-240), consume-once delattr,
  fresh-instance fallback, mount-absent skip. Recorded so the family item
  does not re-litigate F3's standing rows.

Supersessions (originals untouched above):

- S1: the Challenges-table row `F3 handoff | reshape the tuple | ... |
  single grammar` is SUPERSEDED for the LAYOUT: reshape -> count 2, routed
  to Family `prepared-view-handoff-shape` (open). The row's site cites (:242,
  views.py:555-559) stand confirmed.
- S2: the F3 finding's reshape clause (`reshape -> 1 grammar / 2 halves
  (round-trip pair — one body impossible across modules and request
  phases)`) is SUPERSEDED: the "one body impossible" premise is withdrawn
  (import-feasible, probe-verified). Two CALL sites must remain (different
  request phases — undisputed), but the layout need not be DEFINED twice.
  The rename, relax-check, and singleton-token clauses stand untouched, as do
  the F3 sub-rows ("halves separable", "singleton token rejected") W2
  verified.
- S3: the `request-body-boundary-ordering` consolidated index row now covers
  F3's names/token/policy only; the layout sub-rule is held by the open
  family row added under `## Index rows for Worker 0`. F1, F2, F4–F8 and
  R1–R3 rows unchanged.

#### Rev-2-2 (Difference 2, trivial): census + import sentences corrected

2a. Matrix axis 4 — original: "the method name string occurs only at target
`:95` plus the one independent literal oracle (tests `:3223`, fails closed —
see F4)." SUPERSEDED BY: "the method name occurs in production only as the
name (target :95, a string literal) and the method it names (views.py:584,
F4's junction — :623 is that method's own internal call, and target :24/:91
plus views.py:397/:628 are docstring cites, all projections); the oracle side
spells it as code at tests :2487 (direct call), :3223 (fixture definition),
and :3678 (identity pin) — :3223 and :3678 fail closed in both rename
directions per F4, while :2487's spelling fails on a method rename only (a
direct attribute call that never reads the constant) — with exactly one
prose mention (:2342 docstring)." Census instrument:
tokenize NAME-exact classification over HEAD bytes (P-R2): tests code ==
{2487, 3223, 3678} with one prose hit covering :2342; middleware code == {}
(both uses read the constant, :230 + :336); views code == {584, 623}; target
code == {} with string hits covering :24/:91/:95. Verdict-neutral per W2:
all three test spellings are oracle-side; production has no protocol-use
literal. "No second grammar exists" stands.

2b. System trace — original: "Neither imports the other; both import only the
constants from here, and this module imports nothing but the standard library
at runtime (verified by execution — probe P1 below)." SUPERSEDED BY:
"Neither imports the other; both import only names from here — the middleware
takes the five constants plus the ContextVar (request_body.py:89-96), the
views take four constants plus the singleton (views.py:95-101) — and this
module imports nothing but the standard library at runtime (verified by
execution — probe P1 below)." Verified against both import blocks at HEAD
(P-R2): views does not take _BOUNDARY_METHOD (it defines the method) or the
ContextVar; middleware does not take the singleton.

2b-parallel. F8 finding — original: "Structural consumers = the two `from ...
_boundary_ordering import` blocks (views.py:95-101, request_body.py:89-96) —
constants only." The trailing "constants only" is the same loose claim as the
System-trace sentence (flagged transparently as the parallel site of
Difference 2, not a new difference): SUPERSEDED BY "— names only (constants +
ContextVar + singleton per the blocks above)." F8's sites/roles/counts/owner
verdict stands verified; only the two-word characterization is corrected.

#### Rev-2-3: Differences 3–4 acknowledged, no action

Difference 3: W2 yielded — `_is_graphiql` stays matrix-axis-1 discharge, no
formal row. Nothing to do. Difference 4: D-W2-1 ("two marks" stale count)
acknowledged as real, prose-only, non-blocking; it homes to File
`middleware/request_body.py` at closeout — Worker 0's job, not this item's.
D1 stands self-homed. The pass-1 "no docstring contradicting its body"
sentence stands as Worker 1's pass-1 record, qualified by D-W2-1 as W2 wrote.

#### Rev-2-4: probes, fingerprints, gate

Probe P-R2:
docs/dry/temp-tests/dry-file-_boundary_ordering-r2-w1rev2/probe_handoff_shape.py
(sole file in this revision's only scratch scope; sibling scopes untouched).
Replay: `uv run python` on that path from the repo root — settings-free,
read-only (git show HEAD: + AST + tokenize), no DB. Result: 20/20 PASS at
HEAD bfaee91d. Two probe bugs found and fixed during the pass, both in the
probe: a naive substring def/record check tripped by `__bool__`/`package`,
and line-granularity string classification tripped by a code+literal line —
fixed via AST defs and NAME-exact token classification; the target never
implicated. Earlier scopes retained for Worker 0: r2-w1 (pass-1 probe), r2-w2
(W2 probe). Pending execution stays empty: P-R2 is execution-verified,
nothing deferred.

Fingerprints (re-hashed this pass; unchanged rows keep HEAD blobs): target
197eea8e01cb405f38b21022689ed54970efcb97, views.py
9f85b0df26a17e800ec392aa13f6848e07633895, middleware/request_body.py
e6e32e785ec84360c63c9ff529a58f8d63bc8898, tests/test_views.py
4dc9a25723501cd1f84161423a1aefbf00ff7eb9 — all equal HEAD, all match the
pass-1 record. This revision touches no source bytes: the F3 reshape filing
change is a routing verdict, not a source change, and the re-hashed blobs
are the evidence it was reasoned against. New claims cite HEAD line numbers
verified by P-R2, listed above.

Pre-finish gate: HEAD bfaee91d at start, bfaee91d at finish — unmoved. Target
clean (worktree == HEAD blob). Artifact is untracked item scratch (created by
this item's pass-1 + W2; content = run-2 pass-1 + Phase A/B, no foreign
hunk). Item-scoped paths show only item-worker content. test_transport_api.py
is dirty from concurrent work — untouched and unrelied-upon this revision (no
live-tier cite added). Ruff check + format pass on the rev-2 scratch scope
only; the artifact is per-cycle scratch (raw path:NN, no style sweep, no
auto-fix outside the scope). No suite run. Sharded/Postgres: still
inapplicable by construction (unchanged from pass-1, endorsed by W2).

Status: ready-for-verification/2. Resubmission returns to the SAME Worker 2.

### Re-pass verification (Worker 2) — `verified`

HEAD `bfaee91d` unmoved; target + parties + tests clean (4/4 blobs
re-hashed: `197eea8e01cb`, `9f85b0df26a1`, `e6e32e785ec8`,
`4dc9a2572350` — all match pass 1). Verified against my own Difference
1/2 requirements, re-derived from HEAD bytes (worktree == HEAD on all
four files), not taken from P-R2:

- Difference 1: horn (a) complete — family name, `open` status, holding
  item, exact three files, contract/variation scoped to layout-only,
  both halves as sites with roles (pack/unpack = shape encodings,
  target = projection, oracle = `:294-305` + full-chain rows), reshape
  challenges with count 2 (third element, reorder) plus the
  unpack-only strictness carve-out, owner candidates with reasoning,
  stays-separate list, and exact index-row text with pointer. My own AST
  run confirms the dispositive facts: single setattr-tuple pack at
  `:242` positional `[mount, view]`; `prepared_view` `:554-559` with all
  five checks; target defs exactly `{_CsrfOrderingExemption, __bool__}`;
  exact import-name sets both blocks; neither party imports the other.
  S1/S2/S3 supersessions honest (pass-1 originals byte-present as
  quoted); F3's rename/relax/singleton sub-rows untouched. The "needs no
  edit with sharing" rationale is correctly framed as routing rationale,
  carrying no consolidation verdict — the family item decides.
- Difference 2: 2a census matches my independent NAME-exact tokenize run
  line for line (tests `{2487, 3223, 3678}` + prose `:2342`; middleware
  `{}`; views `{584, 623}`; target strings `:24/:91/:95`); fail-closed
  division sound (`:2487` method-rename-only, `:3223`+`:3678` jointly
  both directions); "no second grammar" stands. 2b import wording
  matches my AST sets exactly (middleware 5+Var, views 4+singleton).
  2b-parallel: F8 `:509` original confirmed, supersession honest.
- Differences 3-4: acknowledgments correct, no action owed. My Phase-A
  bytes, D-W2-1, and Phase-B reconciliation all byte-intact (W1 touched
  none). P-R2 replayed 20/20 green; ruff check + format clean on the
  rev-2 scope. Pending execution stays empty; sharded/PG
  inapplicability unchanged and still endorsed.

`Status: verified`. For Worker 0: transcribe the five index rows (1
consolidated, 1 open family + `## Families` item
`prepared-view-handoff-shape`, 3 rejected); D1 self-homed, D-W2-1 homes
to File `middleware/request_body.py` at closeout.

### Adjudication-1 (Worker 1) — stale live-tier input landed; CONFIRM throughout, re-pin `:3065`→`:3080`

Scope: HEAD moved `bfaee91d`→`69a25369` (three commits: `1dd7d147`
kanban, `a01a2ab8` test re-tiering, `69a25369` docs; zero package
files — `git diff --name-only` shows 0 paths under
`django_strawberry_framework/`). HEAD `69a25369` at dispatch and at
finish. `ITEM_BASELINE=f5a05fa88e37c2412d17aea3210cd461e567b2b1`
resolves (read-only). Append-only: every prior line untouched; this
section supersedes by pointer. All bytes below read via `git show
<rev>:` / `git rev-parse <rev>:<path>` (HEAD-pinned; working-tree dirt
never read).

#### Adj-1: fingerprints — 14/15 MATCH, exactly the one expected STALE

Re-hashed every recorded fingerprint at HEAD `69a25369` (full table;
recorded prefixes from F1/F5/R1/R3/D1/D-W2-1 + W2 reconciliation):

| Input | Recorded | HEAD now | State |
|---|---|---|---|
| target `_boundary_ordering.py` | `197eea8e01cb` | `197eea8e01cb…` | MATCH |
| `views.py` | `9f85b0df26a1` | `9f85b0df26a1…` | MATCH |
| `middleware/request_body.py` | `e6e32e785ec8` | `e6e32e785ec8…` | MATCH |
| `tests/test_views.py` | `4dc9a2572350` | `4dc9a2572350…` | MATCH |
| `test_transport_api.py` | `17320f1ff335` | `818b639b538d…` | STALE (expected) |
| spec-046 (`docs/SPECS/spec-046-transport_security-0_0_14.md`) | `8d8adaf2f2f0` | `8d8adaf2f2f0…` | MATCH |
| `docs/GLOSSARY.md` | `bc51debc54cf` | `bc51debc54cf…` | MATCH |
| `orders/sets.py` | `6044ab1a11c7` | `6044ab1a11c7…` | MATCH |
| `optimizer/_context.py` | `3d8dcfdfba5b` | `3d8dcfdfba5b…` | MATCH |
| `extensions/operation_state.py` | `b2674a22d2df` | `b2674a22d2df…` | MATCH |
| `permissions.py` (package) | `757dce34cecd` | `757dce34cecd…` | MATCH |
| `utils/operation_lease.py` | `10c164b731b3` | `10c164b731b3…` | MATCH |
| `middleware/debug_toolbar.py` | `5360149bfa20` | `5360149bfa20…` | MATCH |
| `utils/private_state.py` | `08088b820ac2` | `08088b820ac2…` | MATCH |
| `KANBAN.md` | `bd1f3f451ee5` | `bd1f3f451ee5…` | MATCH |

Cross-check by landed set: the 47 landed basenames intersect the
fingerprinted paths in exactly `test_transport_api.py`
(`tests/test_views.py` not landed; landed `tests/test_permissions.py`
+ `tests/utils/test_permissions.py` are distinct paths from fingerprinted
package `permissions.py`, whose blob MATCHes). No other mismatch, so no
finding's scope reopens. `routers.py` carries no recorded fingerprint
(mention only, L53-54); its HEAD blob is identical at both ends
(`a18c5001…`), so that claim's basis is unchanged.

Refreshed blob (full): `test_transport_api.py` HEAD =
`818b639b538df98dd4c9d4571ebfc694bedc221a`.

#### Adj-2: causing range — one commit, two hunks, both disjoint from every cite

Only `a01a2ab8` touches the file in range (16+/1-, net +15 lines;
3248 → 3263 lines):

- H1 (import, L88): `from graphql_client import ...` gains
  `post_graphql_raw`. No artifact claim cites the live file's import
  block (F4/F8 import cites are production blocks). No effect.
- H2 (new test after old L1419, new `:1423-1436`):
  `test_post_not_json_body_is_upstreams_malformed_json_400` (upstream
  parse-400 pinned byte for byte via the new raw-envelope helper).
  Purely additive; shifts every later line by +15. It names no boundary
  mark, chain entry, or CSRF class, and no artifact claim counts or
  censuses live-file tests. No effect beyond the line shift.

The unified range diff contains exactly these two hunks, so every
pre-existing line outside them is byte-identical by construction; the
two cited bodies below were additionally diffed explicitly.

#### Adj-3: per-claim dispositions (every `test_transport_api.py` cite + implicit live cites)

- L10-11 (dirty-path read method): CONFIRM. Pass-1 method record, true
  as history; the file has since landed clean — noted here, original
  untouched.
- L58-59 (System trace: live tier pins shipped chain, real mount's
  marker, recognition, configured-class witness): CONFIRM. Shipped-chain
  test body old `:3033-3088` = new `:3048-3103`, `diff`-clean.
- L152-153 (matrix axis 5 oracle list): CONFIRM, same evidence.
- L224 (F1 oracle `:3065`, real mount marked): CONFIRM with re-pin.
  Old `:3065` is the marker-assert line itself (`assert
  getattr(callback, _BOUNDARY_MARKER, False), (`); new `:3080` is the
  same bytes (verified by `grep` + the `diff`-clean body window).
  Superseding pin: `:3080`.
- L238 (F1 proof "accept in `:2544`/live `:3065`"): CONFIRM with the
  same re-pin `:3080`. (A second `:3065` pin the dispatch listed once;
  both move together with the body.)
- L250/L289-291 (F1/F2 freshness `live 17320f1ff335`): CONFIRM, blob
  refreshed to `818b639b…` (full above). F3/F4 "same five HEAD blobs"
  freshness lines refresh identically.
- L267 (F2 configured-class withdrawal witness): CONFIRM.
  Configured-class test old `:3162-3208` = new `:3177-3223`,
  `diff`-clean.
- F3 carved row (L293-329 + Rev-2-1 routed family): CONFIRM,
  unaffected. F3 cites no live oracle (oracle =
  `tests/test_views.py:294-305`, MATCH). Rev-2-1's "+ full-chain
  prepared-dispatch rows" is unaffected under either reading:
  `test_views.py` is MATCH, and every pre-existing live line is
  byte-identical per the 2-hunk range diff.
- F6 L442 (live configured-class row) + L463-464 (docstring quote
  "Nothing else here can fail if that stops happening"): CONFIRM. Quote
  byte-identical (old `:3171` → new `:3186`).
- L756 (W2 R1), L777 (W2 R2), L850 (W2 R7), L972-973 (W2 matrix axis
  5): CONFIRM. Line-free role cites; the bodies they name are the two
  `diff`-clean tests above.
- L1074-1077 (W2 15/15 freshness): CONFIRM, live blob refreshed (15/15
  hold at the new HEAD after refresh).
- L1332 (Rev-2-4 "dirty … unrelied-upon"): CONFIRM as pass-2 history.
  This adjudication relies on the live file only for static byte
  comparison, now against clean HEAD bytes.

No definition count, oracle role, or projection citation moves: the
stale input is an oracle throughout (never a definition, consumer, or
enforcement site), all cited rows are byte-identical, and the only
citation change is the mechanical `:3065`→`:3080` re-pin plus the blob
refresh — both recorded here, originals untouched (run-1-history
precedent, as in the querysets adjudications).

#### Adj-4: pending execution + defects — unaffected

- `## Pending execution` still empty: CONFIRM. No `proof:`/`gate:`
  entries owed; P1's probe-backed conclusions are untouched by this
  pass (target blob MATCH; nothing re-derived, nothing trusted from a
  lost scope — the relocation note's re-derivation rule fires only on
  conclusions touched, and none is). Static-decidable throughout: no
  fresh scope created, no `.py` added (no ruff owed), no pytest run.
  Sharded/Postgres inapplicability (stdlib-only closure, no DB surface)
  stands unchanged.
- D1 (card-053 prose): CONFIRM unaffected — all three cited blobs MATCH
  (`KANBAN.md` `bd1f3f45`, middleware `e6e32e78`, tests `4dc9a257`),
  cites no live file. Still self-homed to TODO-ALPHA-053-0.0.15.
- D-W2-1 (middleware "two marks" prose): CONFIRM unaffected — both
  cited blobs MATCH. Still homes to File `middleware/request_body.py`
  at closeout.

#### Adj-5: index rows — stand, no change owed to Worker 0

Five transcribed rows (1 consolidated `request-body-boundary-ordering`
covering F3's names/token/policy, 3 rejected, 1 open
`prepared-view-handoff-shape`): all STAND. This re-review moves no
definition count — the F3 carve-out and the routed family cite no live
oracle, and the live re-tiering is additive-only. No row change is owed
to Worker 0.

Pre-finish gate: HEAD `69a25369` at start and finish — unmoved. Target
clean at HEAD blob (MATCH above). Artifact is untracked item scratch;
this pass's item-scoped change is exactly the `Status:` line swap + this
one EOF append — no other path touched, concurrent dirt left alone.

Status: ready-for-verification/adjudication-1.

## Independent verification (Worker 2) — adjudication

HEAD at Phase-B open: `69a253690002fdd413704a7879528c3ded363020` (unmoved
from Phase-A start). Phase-A scope file:
`docs/dry/temp-tests/dry-adjud-boundary-w2/phase_a_expectations.md`.

### Phase A as recorded pre-read

Verbatim from the scope file (written before opening artifact lines 1382+;
the 6-line overshoot is disclosed inside):

# Phase A expectations (Worker 2, blind) — `_boundary_ordering` adjudication

Run 0.0.15 2026-09-21-2. Item: File `django_strawberry_framework/_boundary_ordering.py`.
Scope: `docs/dry/temp-tests/dry-adjud-boundary-w2/` (created this pass; confirmed
absent before creation). No `.py` in this scope; static-decidable.

## Blindness and boundary

Pre-existing artifact = `docs/dry/dry-file-_boundary_ordering.md` lines 1–1381
(everything before `### Adjudication-1 (Worker 1)` at line 1382), plus the tree
at HEAD. The `## Iterations` section at line 1170 contains pre-existing
Revision-2 + re-pass records (needed for the F3 carved row), so the blind
boundary is line 1382, not line 1170.

Disclosure: the read that established the 1381/1382 boundary overshot by 6
lines (1382–1387: the adjudication heading naming CONFIRM + `:3065`→`:3080`
and the first scope sentence). Nothing further was read. The `:3080` value
below is re-derived independently from the `+15` shift proof, not taken from
that heading; Phase B will reconcile any wording overlap explicitly.

HEAD at Phase-A start: `69a253690002fdd413704a7879528c3ded363020`.
ITEM_BASELINE=`f5a05fa88e37c2412d17aea3210cd461e567b2b1` resolves (verified via
`git rev-parse`). Adjudication range: `bfaee91d..69a25369` (three commits, all
the maintainer's test/docs push; zero package files).

## Fingerprint re-hash (all 15, at current HEAD)

Recorded prefixes are from F1–F8/R1–R3/D1/D-W2-1 Freshness rows and the
Rev-2-4 full blobs. Method: `git rev-parse HEAD:<path>` for HEAD blobs,
`git rev-parse bfaee91d:<path>` for range-stability, `git hash-object` for the
worktree where relevant. All 15 paths are clean in `git status` (no entry),
so worktree reads are HEAD reads.

| # | Input | Recorded | HEAD now | bfaee91d→HEAD | State |
|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/_boundary_ordering.py` | `197eea8e01cb` | `197eea8e01cb405f38b21022689ed54970efcb97` | SAME | MATCH |
| 2 | `django_strawberry_framework/views.py` | `9f85b0df26a1` | `9f85b0df26a17e800ec392aa13f6848e07633895` | SAME | MATCH |
| 3 | `django_strawberry_framework/middleware/request_body.py` | `e6e32e785ec8` | `e6e32e785ec84360c63c9ff529a58f8d63bc8898` | SAME | MATCH |
| 4 | `tests/test_views.py` | `4dc9a2572350` | `4dc9a25723501cd1f84161423a1aefbf00ff7eb9` | SAME | MATCH |
| 5 | `examples/fakeshop/test_query/test_transport_api.py` | `17320f1ff335` | `818b639b538df98dd4c9d4571ebfc694bedc221a` | DIFF | STALE (the one) |
| 6 | `django_strawberry_framework/orders/sets.py` | `6044ab1a11c7` | `6044ab1a11c77a42b715f0d0722fe7c9695064bc` | SAME | MATCH |
| 7 | `django_strawberry_framework/optimizer/_context.py` | `3d8dcfdfba5b` | `3d8dcfdfba5ba644b4759f80e95d57ba0fa1a98b` | SAME | MATCH |
| 8 | `django_strawberry_framework/extensions/operation_state.py` | `b2674a22d2df` | `b2674a22d2dfd58ff97c51a02e16068bb22032e9` | SAME | MATCH |
| 9 | `django_strawberry_framework/permissions.py` | `757dce34cecd` | `757dce34cecd7a249b2634947a771d4608808bfe` | SAME | MATCH |
| 10 | `django_strawberry_framework/utils/operation_lease.py` | `10c164b731b3` | `10c164b731b381d2b62adb5e2c5ce6b694a53fd0` | SAME | MATCH |
| 11 | `django_strawberry_framework/utils/private_state.py` | `08088b820ac2` | `08088b820ac20579e471915644a931953362fca8` | SAME | MATCH |
| 12 | `django_strawberry_framework/middleware/debug_toolbar.py` | `5360149bfa20` | `5360149bfa207e707c98985e9a1d79672220b210` | SAME | MATCH |
| 13 | `KANBAN.md` | `bd1f3f451ee5` | `bd1f3f451ee79e9552e3ec6d74e0a5eb348c5ecf` | SAME | MATCH |
| 14 | `docs/SPECS/spec-046-transport_security-0_0_14.md` | `8d8adaf2f2f0` | `8d8adaf2f2f07cbc6cd3d434a029b2419b7d4704` | SAME | MATCH |
| 15 | `docs/GLOSSARY.md` | `bc51debc54cf` | `bc51debc54cf3ed142b45fa9feda1b99bce60c79` | SAME | MATCH |

Notes:

- Old live blob at `bfaee91d` is `17320f1ff335a868d5ed324a49f1d7c4ee899cfc`
  — the recorded prefix was exact, so the STALE is the predicted landing, not
  a mis-record.
- Worktree hash of the live file is `818b639b…`, equal to the HEAD blob: the
  file landed clean, no residual dirt.
- Spec-046 identity: the recorded `8d8adaf2f2f0` prefix resolves to
  `docs/SPECS/spec-046-transport_security-0_0_14.md` (full blob above); no
  other spec-046 file was fingerprinted.
- Landed-set intersection: `git diff --name-only bfaee91d..69a25369` names 45
  files, zero under `django_strawberry_framework/`. The only fingerprinted
  path in that set is the live file. (`tests/test_permissions.py` and
  `tests/utils/test_permissions.py` landed but are NOT fingerprinted here —
  the fingerprinted permissions input is the package module, row 9, SAME.)
- Upstream Django `csrf.py:420` is version-recorded (6.1), not a blob; no
  re-hash owed. Per conditions, `management/commands/inspect_django_type`
  was never imported.

Expectation: exactly one STALE (row 5), fourteen MATCH. Any adjudication
record claiming otherwise must be reconciled as a real difference.

## The diff, hunk by hunk

Single causing commit for this file: `a01a2ab8` ("test: move the
request-observable rows live and pin the cost each one claims"). Stat: 16
insertions, 1 deletion (net +15 lines; 3248 → 3263 lines).

### Hunk 1 — import line 88 (1 del + 1 ins, no shift)

```diff
-from graphql_client import assert_graphql_data, post_graphql
+from graphql_client import assert_graphql_data, post_graphql, post_graphql_raw
```

Adds one imported name; removes nothing. Line count unchanged by this hunk
alone. The live file's `_BOUNDARY_MARKER` import stays at line 96 in both
versions (verified by `grep -n` on both blobs).

Claims it could touch: none by content. It is above every cited live row
(all cited rows are at old lines ≥3033), adds no boundary symbol, and
changes no assertion. The only theoretical touch is line-number identity
for a pin at line 88 itself — no recorded pin cites line 88 (the sole live
line pin is `:3065`; see below).

Expected disposition: CONFIRM, immaterial. Reason: pure-additive import
growth serving hunk 2's new test; no oracle body, role, or pin moves.

### Hunk 2 — new test after old line 1419 (15 ins, +15 shift below)

New `test_post_not_json_body_is_upstreams_malformed_json_400` at new lines
1422–1434 (plus 2 blank separator lines: new 1420–1421), asserting POST
`{not json` to `/graphql/` returns upstream's byte-exact 400
(`b"Unable to parse request body as JSON"`).

Content check: the 15 inserted lines cite no boundary symbol (grep for
`_BOUNDARY|_Csrf|_CSRF|_package_view|csrf_exempt|marker` over new 1420–1434
returns nothing). It exercises the raw-envelope helper and upstream parse
wording — a wire-meaning pin for a path the boundary module never names.

Structural effect: every old line ≥1420 shifts by exactly +15. Proved by
segment diffs on HEAD-pinned bytes:

- Old 1–1419 vs new 1–1419: differ ONLY at line 88 (hunk 1).
- Old 1420–3248 vs new 1435–3263 (1829 lines): byte-identical.
- Therefore the hunk is a pure insertion; nothing below it was edited.

Claims it could touch, one by one:

1. **Live-tier oracle roles** (System trace L58-59: shipped chain, real
   mount's marker, recognition, configured-CSRF-class witness; Matrix axis 5
   L153: chain/marker/recognition/configured-class rows; F5 "sync and async
   live rows"; Phase-A R1/L756 and matrix L973-974): all these rows live in
   the byte-identical post-insert segment (old ≥3033). Their bodies, roles,
   and verdicts cannot have moved — only their line numbers shift by +15.
   Expected: CONFIRM, roles unchanged. The new test adds a fifth live
   behavior (upstream parse wording) that no boundary finding cites; it does
   not re-tier, rename, or split any cited row.
2. **The `:3065` real-mount line pin** (F1 L224): old 3065 is
   `assert getattr(callback, _BOUNDARY_MARKER, False), (` inside
   `test_the_shipped_chain_supplies_the_ordering_for_fakeshops_real_mount`
   (old def 3033). New 3080 is the identical line (context old 3064–3071 vs
   new 3079–3086 byte-identical; enclosing def new 3048 = 3033+15).
   Expected: REVISE the pin (`:3065`→`:3080`) + refresh the row-5 hash to
   `818b639b…`. This is a line-pin + hash refresh only; the claim the pin
   supports (real mount marked, recognition accepts) is CONFIRMed by
   identical bodies. No other live line pin exists in the pre-existing
   artifact (census of `test_transport` mentions: L10, L58, L153, L224,
   L250, L267, L756, L973, L1332 — only L224 carries a line number).
3. **Withdrawal witness** (F2 L267 configured-class row; F6 L460-464 call-log
   + "Nothing else here can fail" docstring): the witness test
   `test_the_configured_csrf_class_checks_fakeshops_real_mount_behind_the_boundary`
   moves old 3162 → new 3177 (+15); the 87-line tail old 3162–3248 vs new
   3177–3263 is byte-identical, including the "Nothing else here can fail"
   sentence (old 3171 → new 3186) and the call-log assert. No line number
   for this row is recorded, so no re-pin is owed — only the shared row-5
   hash refresh.
   Expected: CONFIRM, body-identical.
4. **F3 carved row** (F3 L293-330; Rev-2-1 carve-out L1180-1255): F3's oracle
   is `tests/test_views.py:294-305` (row-4 blob, MATCH) plus, in Rev-2-1,
   "full-chain prepared-dispatch rows" with no live-file cite. Census shows
   zero `test_transport` mentions in F3 or Rev-2-1 ranges. The carved family
   `prepared-view-handoff-shape` (open, held by the family item) cites the
   same package-tier oracle.
   Expected: CONFIRM, untouched — no live-tier dependence exists to go
   stale, and the carve-out needs no edit.

## Pending execution and defects (expected: unaffected)

- `## Pending execution` is empty (probe-backed P1 `execution-verified`
  with replay command; sharded/PG inapplicable by construction). The stale
  input is a live-tier test file; P1 is settings-free and reads only the
  target's bytes (row 1, MATCH). The lost run-2 probe files (worktree-entry
  scratch custody) do not affect this: P1's conclusion rests on the target
  blob, which is SAME across the range. Expected: still empty, no `proof:`
  or `gate:` owed.
- D1 (card-053 prose, self-homed to TODO-ALPHA-053-0.0.15): cites KANBAN
  (row 13, MATCH), middleware (row 3, MATCH), tests (row 4, MATCH). No live
  cite. Expected: unaffected, still closeout-homed.
- D-W2-1 (middleware "two marks" prose): cites middleware (row 3, MATCH)
  and target (row 1, MATCH). No live cite. Expected: unaffected, still
  closeout-homed to File `middleware/request_body.py`.

## What Phase B must check

Fingerprint agreement (15/15 as above, or reconcile); artifact append-only
(Status swap + adjudication append, pre-existing bytes intact — via W1's
recorded pre-edit hash if given, else targeted re-reads); HEAD tripwire
(start `69a25369`, re-checked at finish); AGENTS.md prose rules on the
adjudication diff (symbol citations, no feedback-file mention, no suite
run); pending-execution still empty; D1 and D-W2-1 still homed as recorded.

Phase-A HEAD tripwire: HEAD at end of Phase A is recorded at Phase-B open
(one `git rev-parse HEAD` call then); no tree mutation was made in Phase A
(scope dir + this file only).

(End of Phase-A verbatim.)

### Reconciliation (Phase B) — every difference, explicitly

W1's record: `### Adjudication-1` (artifact lines 1382–1527) + the header
`Status:` swap. Dispositions agree throughout (CONFIRM + re-pin `:3065`→
`:3080` + hash refresh); the differences below are enumeration depth and
window framing, all resolved in W1's favor or as immaterial.

- R-1 (fingerprints): AGREE 15/15. W1's table lists the same 15 inputs
  (different row order), same 14 MATCH + 1 STALE split, same recorded
  prefixes, and the same refreshed live full blob
  `818b639b538df98dd4c9d4571ebfc694bedc221a` (character-identical to my
  independent `git rev-parse`). W1's landed-set cross-check (47 basenames;
  `tests/test_views.py` not landed; landed `test_permissions` files are
  distinct paths from fingerprinted package `permissions.py`) matches mine
  (45 paths via `git diff --name-only`; the 47/45 count difference is
  basenames-vs-paths counting over the same range, immaterial — the
  intersection result is identical: only `test_transport_api.py`). No gap.
- R-2 (hunks): AGREE. Same causing commit (`a01a2ab8`), same stat (16+/1-,
  net +15, 3248→3263), same H1 (import line 88, no shift) and H2 (new
  upstream-parse-400 test after old 1419, pure insertion, no boundary
  symbol). New-test window framing differs (mine: new 1420–1434 anchored
  on leading blanks; W1: new 1423–1436 anchored on the def through
  trailing blanks) — immaterial: both windows cover the same test, both
  prove pure insertion, and the +15 shift below holds under either
  anchoring (separator blanks are identical bytes). My 1829-line
  post-insert proof and W1's "two hunks, everything else byte-identical by
  construction" are the same fact at different granularities. No gap.
- R-3 (missed second `:3065` pin — Phase-A gap, W1 correct): Phase A
  claimed L224 was the sole live line pin. W1 correctly found the second
  pin at L238 ("accept in `:2544`/live `:3065`"), which my filename-grep
  census missed (that line says "live" without the filename). Verified
  byte-present at L236–240. Same disposition both pins (`:3080`); W1's
  record moves both together. Endorsed; no revision action (W1 already
  carries the complete re-pin).
- R-4 (under-enumerated W2 live cites — Phase-A gap, W1 correct): Phase A
  named the W2 live cites at L756 and L973; W1 additionally names L777
  (R2 "live CSRF-class-behind-boundary row") and L850 (R7 "live row
  proving the configured CSRF class runs behind the boundary"), both
  verified byte-present, both line-free role cites over the same two
  diff-clean bodies. Same disposition (CONFIRM). Endorsed; no action.
- R-5 (cited-body windows): W1's shipped-chain window (old 3033–3088 =
  new 3048–3103, 56 lines) and witness-test window (old 3162–3208 = new
  3177–3223, 47 lines) both re-diffed independently in Phase B:
  diff-clean. These sit inside my coarser proofs (1829-line post-insert
  segment; 87-line tail) — consistent, and W1's tighter windows are the
  better citation. Endorsed.
- R-6 (withdrawal witness + docstring quote): AGREE. Same test (old 3162
  → new 3177), same quote shift (old 3171 → new 3186), same
  body-identical verdict. No line pin recorded, none owed beyond the
  shared hash refresh. No gap.
- R-7 (F3 carved row): AGREE, W1 stronger. Both find zero `test_transport`
  mentions in F3/Rev-2-1 and the same package-tier oracle
  (`tests/test_views.py:294-305`, MATCH). W1 additionally disposes
  Rev-2-1's ambiguous "+ full-chain prepared-dispatch rows" under either
  reading (package-tier MATCH + every pre-existing live line identical),
  which closes the ambiguity my Phase A left open. Endorsed.
- R-8 (routers.py mention-only): Phase A did not check it; W1 records
  both-ends blob `a18c5001…` identical. Independently verified in Phase B
  (`git rev-parse` at both ends equal; worktree differs only by concurrent
  hunt dirt, which W1 correctly did not read). Endorsed.
- R-9 (pending + defects + index rows): AGREE on all. Pending still empty
  (no `proof:`/`gate:`; P1 untouched — rests on the MATCH target blob, so
  the relocation re-derivation rule does not fire); D1 still self-homed
  to TODO-ALPHA-053-0.0.15; D-W2-1 still homes to File
  `middleware/request_body.py` at closeout; all five index rows STAND
  (Phase A did not name the index-row consequence; W1's "no row change
  owed to Worker 0" is correct — no definition count moves). No gap.
- R-10 (6-line overshoot): the heading glimpse named CONFIRM + `:3080`.
  My `:3080` was derived from the shift proof (old 3065 + 15, context
  diffed) before Phase A was written, and every other number above
  (blobs, windows, line counts) was re-derived from HEAD-pinned bytes;
  the glimpse contributed no evidence Phase B relies on. The two
  enumeration gaps (R-3, R-4) cut against the glimpse mattering: had I
  absorbed W1's record, I would not have under-enumerated it. Recorded
  for Worker 0; verdict-neutral.

### Verification job

- Fingerprint agreement: 15/15, including the refreshed live full blob
  character-identical. Done (R-1).
- Artifact append-only: W1 recorded no pre-edit hash, so targeted
  re-reads. Verified byte-present as quoted: L3 header swap, L224 pin,
  L236–240 second pin, L248–253 freshness, L267 witness, L460–464 quote,
  L777/L850 W2 cites, `## Pending execution` body (still empty),
  D1/D-W2-1 headers, Rev-2/Re-pass sections untouched (line numbers
  1170–1381 stable), W1 append exactly lines 1382–1527 + header swap, no
  other path touched (no W1 scope dir exists; `git status` shows no new
  tracked path attributable to this pass). Pre-existing bytes intact.
- HEAD tripwire: `69a253690002fdd413704a7879528c3ded363020` at Phase-A
  start, Phase-B open, and finish — unmoved throughout.
- AGENTS.md prose rules on the adjudication diff: raw `path:NN` allowed
  (per-cycle artifact); no feedback-file mention (grep-clean over
  1382–1527); no suite run (static-decidable, none claimed); no
  CHANGELOG/commit/plan edits (plan untouched by this pass); no
  `management/commands/inspect_django_type` import. Clean.
- Pending-execution still empty; D1 and D-W2-1 homing unchanged (R-9).
- This pass added no `.py` (scope holds the Phase-A `.md` only), so no
  ruff gate is owed; ran no pytest (read-only `git show`/`grep`/`diff`
  probes only), created no disposable workspace (nothing source-mutating
  to prove). Sharded/Postgres stay as typed (inapplicable by
  construction, target MATCH).

### Verdict

`Status: verified`. W1's adjudication is complete: every stale-input cite
re-derived against HEAD bytes, both `:3065` pins re-pinned, the blob
refreshed, pending/defects/index rows correctly untouched. The item keeps
plain `verified` (pending-execution empty). Nothing is owed to Worker 0
beyond transcription of this outcome; no defect, no family, no ledger row
arises from this pass.

### Adjudication-2 (Worker 1) — two doc inputs landed; CONFIRM throughout, re-pin `:370`→`:371`

Scope: HEAD moved `69a25369`→`24e6b4d3` (eleven the maintainer commits; zero touches
to the target, either protocol party, or either oracle tier). HEAD
`24e6b4d3` at dispatch and at finish. `ITEM_BASELINE=f303097a60d87251cc14037fb18b40c063e77475`
resolves (read-only). Append-only: every prior line untouched; this section
supersedes by pointer. All bytes below read via `git show <rev>:` /
`git rev-parse <rev>:<path>` (HEAD-pinned; worktree dirt never read).
Pre-edit artifact: 111844 B, sha256
`b4d6ab4c1f2075bc0bd2ae8c30df26130465fd8e1afa7575fd2a583d9ff58732`
— W2 reconstructs by restoring the `Status:` line to `verified` and
truncating this append (self-checked this pass: that procedure
reproduces the hash exactly).

#### Adj2-1: fingerprints — 13/15 MATCH, exactly the two expected STALE

Re-hashed every recorded fingerprint at HEAD `24e6b4d3` (full table;
recorded prefixes from F1/F5/R1/R3/D1/D-W2-1 + the adj-1 live refresh):

| Input | Recorded | HEAD now | State |
|---|---|---|---|
| target `_boundary_ordering.py` | `197eea8e01cb` | `197eea8e01cb…` | MATCH |
| `views.py` | `9f85b0df26a1` | `9f85b0df26a1…` | MATCH |
| `middleware/request_body.py` | `e6e32e785ec8` | `e6e32e785ec8…` | MATCH |
| `tests/test_views.py` | `4dc9a2572350` | `4dc9a2572350…` | MATCH |
| `test_transport_api.py` | `818b639b538d` | `818b639b538d…` | MATCH (adj-1 pin holds) |
| `orders/sets.py` | `6044ab1a11c7` | `6044ab1a11c7…` | MATCH |
| `optimizer/_context.py` | `3d8dcfdfba5b` | `3d8dcfdfba5b…` | MATCH |
| `extensions/operation_state.py` | `b2674a22d2df` | `b2674a22d2df…` | MATCH |
| `permissions.py` (package) | `757dce34cecd` | `757dce34cecd…` | MATCH |
| `utils/operation_lease.py` | `10c164b731b3` | `10c164b731b3…` | MATCH |
| `utils/private_state.py` | `08088b820ac2` | `08088b820ac2…` | MATCH |
| `middleware/debug_toolbar.py` | `5360149bfa20` | `5360149bfa20…` | MATCH |
| `KANBAN.md` | `bd1f3f451ee5` | `dae7e7979fa2…` | STALE (expected) |
| spec-046 (`docs/SPECS/spec-046-transport_security-0_0_14.md`) | `8d8adaf2f2f0` | `8d8adaf2f2f0…` | MATCH |
| `docs/GLOSSARY.md` | `bc51debc54cf` | `d3ef357c26ed…` | STALE (expected) |

Old-pin exactness: both recorded prefixes equal the `69a25369` blobs
(`git rev-parse` verified), so the two STALEs are the predicted landings,
not mis-records. Blind containment: the FULL table was re-hashed and no
third mismatch surfaced, so no finding's scope reopens beyond F1/D1.

Refreshed full blobs: GLOSSARY HEAD =
`d3ef357c26ede6a5bd21d4290b394ade4eb987b4`; KANBAN.md HEAD =
`dae7e7979fa2e9842cb3a257882322740a1a6d03`.

#### Adj2-2: F1 — GLOSSARY CONFIRM, no re-pin owed

Only two commits in range touch the file (`git log 69a25369..HEAD --
docs/GLOSSARY.md`); range diff is 7+/7-, net 0 lines:

- `9350eb8d` H1 (`:24-34`): `DEFAULT_ERROR_POLICY` /
  `DEFAULT_RESOURCE_POLICY` summaries → "inspectable value template"
  wording, plus the `DjangoErrorPolicyExtension` summary → "built first
  in chain" wording. H2 (`:841`): `ErrorPolicy` `__post_init__`
  exact-type-test sentence. H3 (`:1127`): masking-ordering
  masker-position sentence. H4 (`:1574`): production-error-policy install
  sentence. All four are policy/extension prose in entries F1 never
  cites. No effect.
- `44712901` H1 (`:1558`): "Prefetch alias threading" sentence re-render
  ("because nothing refilters it" → the sliced-policy paragraph). One
  entry, one line, disjoint from every cited anchor. No effect.

Every cited entry diffed window-by-window, old vs new HEAD bytes:

- `## DjangoGraphQLView` `:636-646` — IDENTICAL at the same lines.
- `## GraphQLRequestBodyBoundaryMiddleware` `:1040-1056` — IDENTICAL at
  the same lines.
- `## Request-body cap` `:1724-1734` — IDENTICAL at the same lines.
- Anchor-table rows (`:126` / `:151` / `:203`) and the `:257` family
  line sit at identical lines at both heads (grep census).

F1's GLOSSARY role is projection-only (System trace L61-63 anchors; F1
projections L225; the same anchors underlie F6 L443 and W2's R9, which
carry no separate GLOSSARY fingerprint — F1 L252 is the item's sole
one). All five landed hunks are single-line swaps in uncited entries,
so no line shifts and no anchor text moves. Disposition: CONFIRM; blob
refreshed; no line re-pin owed. F6's glossary cite rides the same
byte-identical middleware anchor — CONFIRM by the same evidence.

#### Adj2-3: D1 — KANBAN CONFIRM, re-pin `:370`→`:371`

Only two commits in range touch the file; range diff is net +1 line:

- `357e5487` H1 (KANBAN `:331-334`): inserts the FilterSet-seal row
  after the `clear_resource_context` bullet, before `#### Definition of
  done`. It touches card 053's bullets — but NOT the Open-question
  bullet, which sits 36 lines below.
- `c87f4f98` H1 (same window): rewrites that FilterSet row in place
  (shared helper pair, `_SIDECAR_RESULT_POLICY`, both halves
  discharged). Same window, net 0.

D1 bullet: old `:370` vs new `:371`, single-line `diff` — BYTE-IDENTICAL
(the "last boundary index" / "measure the body twice" / "deliberately
left unpinned" text is verbatim). Card homing intact: card heading `:246`
(`### [TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY
squeeze]`) unchanged; `#### Open question` `:368`→`:369`; the bullet is
still the FIRST bullet under it; the sibling forged-callable bullet is
still live at `:372`, untouched. the maintainer's card-053 edits neither fixed nor
reworded the bullet — both hunks sit at `:331-334` (the FilterSet row),
disjoint from the Open-question section. D1 survives whole: CONFIRM,
still UNFIXED, still self-homed to card TODO-ALPHA-053-0.0.15, still
explicitly not a release blocker (AGENTS.md rule 35: the code is correct
and pinned; only the card's description of it predates the fix).

Both premises re-verified against HEAD code (middleware + tests blobs
MATCH, so the contradict-side is byte-stable; re-read anyway):

- (a) "refused at startup … keeps the *last* boundary index": the audit
  at `middleware/request_body.py:363-374` keeps the FIRST
  (`boundary_index is None` guard, `:369`; docstring `:355-357` states
  first/first); oracle
  `test_the_first_boundary_entry_is_the_one_the_ordering_is_measured_against`
  at `tests/test_views.py:3371`. The bullet still says "last" — stale
  exactly as recorded.
- (b) "measure the body twice": `process_view` early-returns on the
  stamp (`:216-217`); oracle
  `test_duplicate_boundary_entries_do_not_run_the_request_boundary_twice`
  at `:3724`. The bullet still says twice — stale exactly as recorded.
- The "deliberately left unpinned by any test" framing is still stale
  (both behaviors pinned); the sibling stays live and correctly unpinned
  (F4's constraint untouched).

D1 freshness: KANBAN refreshed to `dae7e797…`; middleware `e6e32e785ec8`
MATCH; tests `4dc9a2572350` MATCH.

#### Adj2-4: pending execution + D-W2-1 + index rows — unaffected

- `## Pending execution` still empty: CONFIRM. No `proof:`/`gate:`
  entries owed; P1/P-R2 conclusions rest on the MATCH target blob.
  Static-decidable throughout: no fresh scope created
  (`docs/dry/temp-tests/` listed; the run-2 scope
  `dry-adjud-boundary-w2/` left untouched), no `.py` added (no ruff
  owed), no pytest run. Sharded/Postgres inapplicability (stdlib-only
  closure, no DB surface) stands unchanged.
- D-W2-1 (middleware "two marks" prose): CONFIRM unaffected — both cited
  blobs MATCH; `git log 69a25369..HEAD --
  django_strawberry_framework/middleware/request_body.py` is empty (no
  commit in range touches the file); the sentence still reads "together
  with the two marks" at `:45-46`. Still homes to File
  `middleware/request_body.py` at closeout.
- Five index rows STAND (1 consolidated `request-body-boundary-ordering`
  covering F3's names/token/policy, 3 rejected, 1 open
  `prepared-view-handoff-shape`): no definition count moves — both stale
  inputs are projections/prose throughout (GLOSSARY a projection, KANBAN
  adjacent prose), never definitions, consumers, or enforcement sites.
  No row change is owed to Worker 0.

Pre-finish gate: HEAD `24e6b4d3` at start and finish — unmoved. Target
clean at HEAD blob (MATCH above). Artifact is untracked item scratch;
this pass's item-scoped change is exactly the `Status:` line swap + this
one EOF append — no other path touched, concurrent dirt left alone.

Status: ready-for-verification/adjudication-2.

## Independent verification (Worker 2) — adjudication-2

Run 0.0.15 2026-09-21-3. HEAD `24e6b4d3` at Phase-A start, Phase-B open,
and finish — unmoved throughout. Phase-A scope file (blind record, written
before opening artifact lines 1840+):
`docs/dry/temp-tests/dry-adjud2-boundary-w2/phase_a_expectations.md`.
No `.py` in that scope; static-decidable throughout, no pytest, no
workspace. Every byte below read via `git rev-parse <rev>:` /
`git show <rev>:` (HEAD-pinned; worktree dirt never read).

### Phase-A record (as sealed pre-read)

Blind stale set, derived independently from HEAD bytes: exactly 2 of 15
STALE — `docs/GLOSSARY.md` (`bc51debc…`→`d3ef357c26ede6a5…`) and `KANBAN.md`
(`bd1f3f45…`→`dae7e7979fa2e984…`); the other 13 MATCH, each verified SAME by
direct old-vs-new blob comparison. Full 15-table with both-end blobs is in
the scope file. Causing range `69a25369..24e6b4d3` re-derived as: KANBAN
net +1 (3900→3901) via `357e5487` (+1 FilterSet-seal bullet, hunk
`@@ -331,6 +331,7`) plus `c87f4f98` (1-/1+ in-place reword of that
bullet, final form at new `KANBAN.md:334`); GLOSSARY net 0 lines
(2230→2230) via `9350eb8d` (4 hunks `@@ -24/-838/-1124/-1571`, 6+/6-,
error-policy prose) plus `44712901` (1 hunk `@@ -1555`, 1+/1-,
Prefetch-child prose). Expectations sealed: F1 CONFIRM + hash refresh (no
re-pin — zero GLOSSARY line pins exist in lines 1–1839; the three cited
anchors resolve at identical lines with md5-identical entry windows);
D1 CONFIRM + re-pin `:370`→`:371` + hash refresh (bullet md5-identical
`b1766ae4…`, card homing intact under TODO-ALPHA-053-0.0.15, premises'
code cites in MATCH files); D-W2-1 unaffected; pending execution still
empty; all five index rows STAND. Phase A additionally records a
pre-existing recorded-pin erratum: the artifact's 12-char KANBAN pin
`bd1f3f451ee5` is inexact at digit 12 (the blob at `bfaee91d`,
`69a25369`, and HEAD-check is `bd1f3f451ee79e…`, digit 12 = `7`) —
exact at 11 chars, same blob, plan's 8-char pin exact; immaterial.

### Reconciliation (Phase B) — every difference, explicitly

W1's record: `### Adjudication-2` (artifact lines 1840–1993) + the header
`Status:` swap. Dispositions agree throughout (CONFIRM + `:370`→`:371`
re-pin + two hash refreshes).

- R-1 (fingerprints): AGREE 15/15. Same 15 inputs, same 13 MATCH + 2
  STALE split, same recorded prefixes, same refreshed full blobs
  character-identical to my independent `git rev-parse` (GLOSSARY
  `d3ef357c26ede6a5bd21d4290b394ade4eb987b4`, KANBAN
  `dae7e7979fa2e9842cb3a257882322740a1a6d03`). One correction to W1's
  line 1877 "old-pin exactness" sentence: it overstates for KANBAN at
  the 12th digit (see the Phase-A erratum above — visible verbatim at
  artifact line 1587 since adjudication-1). Immaterial, no revision
  action: the MATCH/STALE judgments are correct, the refresh
  supersedes the recorded string, and history lines are append-only.
  My record carries the correction.
- R-2 (GLOSSARY hunks): AGREE. Same 2 commits / 5 hunks / 7+/7-.
  `-U0` changed lines (`:27,:28,:31,:841,:1127,:1558,:1574`) match
  W1's cites (`:24-34,:841,:1127,:1574,:1558`) exactly — framing
  differs only (W1 cites changed lines, Phase A cited hunk headers).
  Entry windows agree (mine wider, W1's nested inside, all IDENTICAL);
  anchor rows `:126/:151/:203` + `:257` line-stable both passes.
  F1 CONFIRM + refresh with no re-pin; F6 rides the same evidence.
- R-3 (KANBAN/D1): AGREE. Same two-commit story, net +1, same window,
  same content-disjointness verdict. Bullet `:370`→`:371`
  byte-identical under dual proof (W1's single-line diff, my md5
  `b1766ae4…` over the full line). Homing intact, each re-verified in
  Phase B: card heading `:246` unchanged, `#### Open question`
  `:368`→`:369`, bullet still FIRST under it (`:371`, blank `:370`),
  sibling forged-callable bullet `:371`→`:372` md5-identical
  (`1e4c2fc3…`) and still live, card still `In progress` (index `:48`).
  W1's line-36 arithmetic (insertion end `:334`, bullet old `:370`)
  checks. Premises re-verified against HEAD bytes: audit
  `:363-374` first-index + oracle def `:3371` exact, stamp
  early-return `:216-217` + oracle def `:3724` exact, "deliberately
  left unpinned" framing still stale exactly as recorded. D1 CONFIRM:
  still UNFIXED, still self-homed to card TODO-ALPHA-053-0.0.15,
  still explicitly not a release blocker.
- R-4 (pending + D-W2-1 + index): AGREE on all. Pending still empty
  (P1/P-R2 rest on the MATCH target blob; sharded/PG inapplicability
  unchanged). D-W2-1 unaffected — Phase B verified the sentence
  still reads "together with the two marks" at middleware `:45-46`
  and the range log for that file is empty; still closeout-homed to
  File `middleware/request_body.py`. All five index rows STAND (both
  stale inputs are projections/prose throughout, never definitions).
- R-5 (10-line overshoot): the boundary-establishing read saw lines
  1840–1849 (heading + pre-edit hash). Independence stands: every
  number above was re-derived from HEAD-pinned bytes, and the
  digit-12 erratum cuts against absorption — had this pass absorbed
  W1's record it would have repeated "old-pin exactness" instead of
  disproving it. Verdict-neutral. Recorded for Worker 0.
- R-6 (Phase-A boundary erratum, mine): pre-existing bytes are lines
  1–1838, not 1–1839 — line 1839 is W1's blank separator, part of
  the append (proved by the reconstruction below). Content boundary
  unaffected.

### Verification job

- Hash agreement: 15/15 rows plus both refreshed full blobs
  character-identical (R-1). Hunk coverage: all 5 GLOSSARY changed
  lines and both KANBAN hunks matched commit-by-commit (R-2, R-3).
- Artifact append-only: PROVED by sha256 reconstruction. Procedure:
  restore the `Status:` line to `verified`, truncate W1's append
  (lines 1839–1993, separator included) → `111844 B / sha256
  b4d6ab4c1f2075bc0bd2ae8c30df26130465fd8e1afa7575fd2a583d9ff58732`
  — exact match to W1's recorded pre-edit size/hash. (Naive
  truncation at 1839 yields 111845 B and fails; the separator
  belongs to the append.) Artifact is `??` untracked; no W1 scope
  exists (`dry-adjud2-boundary-*` holds only this pass's scope);
  no other path touched.
- HEAD tripwire: `24e6b4d3` at Phase-A start, Phase-B open, and
  finish — unmoved.
- AGENTS.md prose rules on W1's hunks: four banned-word hits, all
  clean on inspection — `Worker` ×2 (role labels "Worker 1" /
  "Worker 0", standard artifact vocabulary), `audit` ×1 (the D1
  defect's domain subject, quoted from the card bullet), `hardening`
  ×1 (card proper noun "Boundary hardening …"). No `plan`, `sweep`,
  `restored`, `previously`, `grader`, or `feedback`-file mention.
  Raw `path:NN` citations are allowed in per-cycle artifacts;
  `path::Symbol` forms used where the rule needs them. No suite
  run, no CHANGELOG/commit/plan edits, no
  `management/commands/inspect_django_type` import.
- Ruff: not owed — neither pass added a `.py` (W1: artifact only, no
  scope; this pass: one `.md` scope file). No repo-wide `--fix`
  pass over concurrent hunt dirt.
- Pending-execution still empty; D1 and D-W2-1 homing unchanged
  (R-3, R-4). No defects found by this pass; no `## Defects` entry.

### Verdict

`Status: verified` (plain — pending-execution empty). W1's
adjudication-2 is complete: every stale-input cite re-derived against
HEAD bytes, the `:370` pin re-pinned, both blobs refreshed,
pending/defects/index rows correctly untouched. The item returns to
`verified` on this verdict. Nothing is owed to Worker 0 beyond
transcription of this outcome; no defect, no family, no ledger row
arises from this pass.
