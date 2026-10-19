# DRY review: `django_strawberry_framework/middleware/request_body.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in a plan-indexed family (reused where the same rule appears
elsewhere, re-derived never inherited) or in a file-local row with its proving
challenge. Zero production edits; zero tracked files changed.

## System trace

Mid-size target (374 lines, 18 top-level statements): the publish/consumer
side of the request-body boundary's ordering protocol. It DEFINES no protocol
name and no policy: the five protocol names, the publish channel, the
exemption predicate and its singleton all live in
`django_strawberry_framework/_boundary_ordering.py`, and the boundary itself
(the cap, the wire refusals, the measurement) lives in
`django_strawberry_framework/views.py` and
`django_strawberry_framework/_request_body.py`. What this module OWNS is the
chain position: the `MIDDLEWARE` entry that runs the views' boundary from
`process_view` ahead of the CSRF middleware, publishes the handling request
on the channel so the exemption can answer per request, recognizes exactly
the callbacks it may run a boundary for, and refuses a misordered chain at
startup. It CONSUMES, by name, the ordering protocol (four marks plus the
method name plus the channel), the `ConfigurationError` it raises, and
`HttpResponse` for the refusal shape. It ENFORCES nothing belonging to
another module: the limit, the refusal statuses, the wire reasons, and the
body measurement stay the views' and the measurement leaf's.

Connected code read for judgment, outside the item (whole bodies, not
samples): `_boundary_ordering.py` (full: five names, channel, exemption
predicate and singleton), `views.py` (full: mixin, `as_view` stamp,
`_enforce_request_boundary` behavior `def`,
`_enforce_request_boundary_once` stamp read, both `run` twins, both CSRF
continuations), `_request_body.py` (contract half, bodies: single-siting
claim checked), `middleware/__init__.py` (full: no-re-export posture),
`middleware/debug_toolbar.py` (full: sibling recognizer for the axis-1
sweep), `exceptions.py::ConfigurationError` (owner of the audit raise),
`examples/fakeshop/config/settings.py` `MIDDLEWARE` block (the shipped
chain: boundary entry immediately before `CsrfViewMiddleware`),
`tests/test_views.py` (import block plus all 17 middleware/boundary titles;
six bodies fully read: mount-handoff guard, non-callable-setup parity,
setup-super invariant, misordered-chain refusal, probe/invoke pins,
duplicate-entry idempotence), `test_transport_api.py` (chain/CSRF titles
censused; shipped-chain rows' roles read),
`docs/GLOSSARY.md` middleware anchor (projection),
`docs/README.md` chain snippet (projection), archived spec-046 (historical
only, never relied upon), installed Django 6.1
`django/middleware/csrf.py::CsrfViewMiddleware.process_view` (the
`csrf_exempt` truthiness read, verified by execution). Excluded with reason:
filter/order/mutation/form/rest_framework/auth/testing/type/optimizer
surfaces (package-wide token sweeps confirm no boundary-mark, measurement,
or decode vocabulary there); the four upstream-patch modules (workaround
lifecycle; the target never imports them and names none of their tokens,
probe-verified); `consumers.py`/`routers.py` (different transports, no
`process_view` — exactly two `def process_view` exist package-wide: this
file's and the toolbar's). The concurrent dirt named in the plan item
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, in-flight `filters/inputs.py` range hunk +
`tests/filters/test_inputs.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was never read for verdicts, never touched; the
further concurrent dirt (`extensions/resource_policy.py`,
`filters/sets.py`, `forms/inputs.py`, `mutations/fields.py` and their test
companions) likewise left alone.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The only sibling recognizer is
`middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view`, which
tags ANY Strawberry view by class (`isinstance(view, type) and
issubclass(view, BaseView)`, over all global traffic, for diagnostics) —
a different contract from this file's marker + `view_class` /
`view_initkwargs` bookkeeping + callable-boundary class probe, which must
identify one exact mount without importing `views.py` and then run that
mount's boundary through a prepared instance. Different inputs, outputs,
and failure modes; the separation is already indexed under F1 at the
owner (with the KANBAN trigger) and re-derived below, not re-litigated.
No filter/order/mutation/form/rest surface carries a boundary mark or a
`process_view`. Search performed (117 files, probe sections 10–11),
one intentional separation confirmed.

**2. Sync/async twins.** One colored pair, compared by behavior:
`__call__` / `__acall__` publish the same request on the same channel
around the same downstream call and reset it in `finally`; the `await`
is the whole difference, and the split is mechanism-forced — returning
the coroutine from a synchronous `finally` would reset the mark before
the CSRF middleware ever read it (stated at the `__acall__` body,
probe-verified structurally). `process_view` itself has NO transport
split: one sync body serves both, because the boundary it runs is
synchronous on both transports. Both `views.py::run` twins compose the
stamp this hook writes. Twinship recorded file-local (L1), nothing to
consolidate.

**3. Derived rather than repeated knowledge.** No reconstructed copies
found. The five protocol names are imported by name and never respelled
(probe: zero mark/method literals in the target, each literal exactly
once package-wide in the owner). The boundary is invoked through the
constant, never a literal attribute. The mount token is identity
(`object()` in `views.py`), never derived. The refusal is rendered from
the caught exception's own `reason` / `status_code` — composed, never
restated. The audit resolves `settings.MIDDLEWARE` entries to classes
and compares by class, never by dotted-path string, and reads the chain
live at instantiation. `settings.MIDDLEWARE` is the only setting read,
and only at chain-build time.

**4. Inverse / round-trip pairs.** Four stamp/read round trips, each
single-owned at `_boundary_ordering.py` with halves in different modules
by construction; this file holds the publish/write halves of three
(ENFORCED write in `process_view`, PREPARED_VIEW write in
`process_view`, channel set/reset in `__call__` / `__acall__`) and the
read halves of one (MARKER/MOUNT reads in `_package_view_instance` /
`process_view`). The views hold the mirror halves. Each half composes
by name; none restates. The fifth apparent pair — refusal in
`process_view` vs refusal in upstream `dispatch` — is one rendering
rule read twice (L6), not two definitions.

**5. Contracts restated in another medium.** Production (target + owner
+ views); oracles that compose by name (`tests/test_views.py` imports
the middleware class, `_package_view_instance`, and the protocol
constants rather than respelling values; the live tier imports
`_package_view_instance` and names the dotted chain path); the shipped
fakeshop chain (boundary entry immediately before CSRF, with the
ordering rationale in comments); projections (this module's docstring,
the mirror paragraphs in `views.py`, the GLOSSARY middleware anchor,
the README chain snippet, the CHANGELOG line). The archived spec-046
is historical corroboration only. No medium restates the rule as a
second definition.

**6. Enforcement by omission.** Family enumerated: {package callback,
foreign callback} x {sync chain, async chain} x {no-CSRF chain,
misordered chain, duplicate entries}. A declined callback is left
entirely alone — no boundary run, no stamp — which keeps the view-local
arrangement rather than losing the ordering (pinned by the
declined-callback CSRF oracles; the omission is the contract, not a
gap). Both transports share the one `process_view`; the async
difference lives only in the publish twins. A misordered chain is
refused at startup; a chain with no CSRF entry passes the audit (no
read to run behind). Duplicate entries are idempotent via the
ENFORCED early return. No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **18 top-level statements**. Class methods counted with their
owner (4 methods). Every member lands below; every challenge in
`### Challenges` ends in a family row, a file-local row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (ordering rationale + non-goals) | (none) | projection, F1/F2/F3/L2 |
| 2 | `from __future__ import annotations` | (none) | machinery |
| 3 | `from typing import ...` | names | machinery (annotation guard) |
| 4 | `from asgiref.sync import ...` | twin helpers | machinery for L1 |
| 5 | `from cross_web import HTTPException` | refusal type | machinery for L6 |
| 6 | `from django.conf import settings` | chain read | machinery for L4 (live read) |
| 7 | `from django.http import HttpResponse` | refusal render | machinery for L6 |
| 8 | `from django.middleware.csrf import CsrfViewMiddleware` | audit referent | machinery for L4 |
| 9 | `from django.utils.module_loading import import_string` | chain resolve | machinery for L4 |
| 10 | `from _boundary_ordering import ...` | 6 names | consumer import, F1/F2/F3 |
| 11 | `from exceptions import ConfigurationError` | audit raise | consumer import, L4 |
| 12 | `if TYPE_CHECKING:` + 3 imports | (annotations) | machinery (zero runtime import) |
| 13 | `__all__` | 1 class name | L7 |
| 14 | `_MISORDERED_MIDDLEWARE_MESSAGE` | audit text | L4 |
| 15 | `_NO_SETUP` | sentinel | L5 |
| 16 | `class GraphQLRequestBodyBoundaryMiddleware` + `__init__` + `__call__` + `__acall__` + `process_view` | chain entry | L1 (`__init__`/`__call__`/`__acall__`) + L2/L5/L6 (`process_view`) |
| 17 | `def _package_view_instance` | recognition | L3 (+F1/F2 consumer) |
| 18 | `def _require_boundary_before_csrf` | audit | L4 |

Rules: F1 `request-body-boundary-protocol-marks` (publish/write halves
here), F2 `boundary-method-name-single-sourcing` (probe + invoke here,
behavior in views), F3 `csrf-ordering-exemption` (publish twins here),
L1 publish twin, L2 boundary-run hook, L3 recognition, L4 ordering
audit, L5 setup fidelity, L6 refusal render, L7 leaf manifest.
Checked-not-member: `sync-adapter-raw-body-source`,
`decode-failure-400-translation`, `request-body-json-parse-reason`, the
nine `_request_body.py` measurement rules (zero code-token traffic,
probe-verified).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. Execution claims below are `execution-verified` by
`docs/dry/temp-tests/dry-file-middleware__request_body/probe_request_body_middleware.py`
(96 sections green, shared tree, no settings, no DB, no pytest); oracle
bodies named are `static-reviewed` except where the probe re-proves the
property.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 publish | rename one mark string | **1** (owner constant; this file's write/read follow) | independent here |
| C2 | F1 publish | sixth per-request fact | **1** (new constant at owner; publish site here follows) | independent here |
| C3 | F2 probe/invoke | probe one method, invoke another | **1** new name definition at owner (one-name constant cannot express two) | independent here |
| C4 | F2 probe/invoke | rename the boundary method | **1** name definition + **1** behavior referent in views; this file **0** | independent here |
| C5 | F3 publish | publish `(request, stamp-snapshot)` instead of the request | **1** (channel at owner; both twins here follow as consumers) | independent here |
| C6 | F3 publish | mid-flight "boundary running now" state | **1** (`__bool__` at owner; this file **0**) | independent here |
| C7 | L1 twin | publish only around `process_view` | refused by mechanism (the CSRF middleware reads mid-chain, after the hook returns) | refused |
| C8 | L1 twin | one shared body for `__call__`/`__acall__` | refused by mechanism (sync `finally` resets before the downstream await resolves) | intentional separation |
| C9 | L2 hook | run the boundary without `setup` | **1** body here; refused by contract (request-local boundary state) | independent |
| C10 | L2 hook | skip the ENFORCED stamp on success | **1** body here (view re-measures; duplicate-entry oracle fails) | independent |
| C11 | L3 recognition | stop at bookkeeping shape, skip the boundary probe | **1** body here; refused by contract (foreign class → uncontrolled 500) | independent |
| C12 | L3 recognition | probe the built instance, not the class | **1** body here; refused (runs a foreign `__init__` to answer) | independent |
| C13 | L3 recognition | broaden the `TypeError` arm to `Exception` | **1** body here; refused (guard sits across the body cap's own errors) | independent |
| C14 | L4 audit | compare dotted paths, not classes | **1** body here; refused (subclass evasion on either side) | independent |
| C15 | L4 audit | judge every entry, not the first of each kind | **1** body here; refused (the first entry is what runs / parses) | independent |
| C16 | L5 setup | call `setup` unconditionally | **1** body here; refused (foreign minimal callbacks carry none) | independent |
| C17 | L6 render | render the refusal as a JSON envelope | **1** body here; refused (attributable wire shape) | independent |
| C18 | L7 manifest | add a second public name | **1** (the tuple extends in one place) | independent |

## Findings

### F1 — request-body-boundary protocol marks (existing family `request-body-boundary-protocol-marks`, stays `open`; publish/write record from this side)

- **Contract + variation.** The four ordering-protocol names live once in
`_boundary_ordering.py`; this file publishes two of them per request and
reads two off the callback. Variation: one row per mark, same reason to
change (the ordering protocol).
- **Sites + roles.** *Definitions*: the four constants (owner elsewhere;
probe-verified sole spellings, zero literals here). *Publish/write
sites (this file)*:
`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
(writes ENFORCED + PREPARED_VIEW, reads MOUNT),
`::_package_view_instance` (reads MARKER). *Mirror halves*:
`views.py::as_view` (stamps MARKER/MOUNT, consumes PREPARED_VIEW),
`views.py::_enforce_request_boundary_once` (reads ENFORCED).
*Oracles*: the 17 middleware/boundary titles in `tests/test_views.py`
(import the constants by name) plus the live shipped-chain rows in
`test_transport_api.py`. *Projections*: this module's docstring, the
GLOSSARY anchor.
- **Challenges.** C1, C2 → 1 owner definition each; this file follows.
- **Owner + lifetime.** Unchanged: `_boundary_ordering.py`
(dependency direction — neither side may import the other; this file
imports the protocol module, never `views.py`, probe-verified). The
per-request stamp lifetime (written after the boundary runs, read by
the view and the exemption, never cleared — the request owns it) is
the owner's; this file only writes within `process_view`.
- **Migration.** None (zero-edit file item).
- **Distinct behavior.** The guarded MOUNT read (`except Exception`
→ `None`: an optional handoff cannot turn a completed boundary into a
500, pinned by its oracle) is this file's consumer hygiene, not a
second mark definition: posit deleting the guard → a raising
decorator 500s a checked request — 1 body here, protocol untouched.
- **Behavioral proof.** `execution-verified` (probe: by-name imports,
zero literals, write/read halves at the stated bodies, guarded-handoff
shape). Rejects "a call site restates a protocol string".
- **Structural gate.** The by-name import discipline + the literal-count
search (each string once package-wide) + the handoff-guard oracle.
Negative control (static): hand-spelling any literal at a stamp/read
site passes every behavioral oracle and fails only the count search —
the family item owes that search (already recorded at the owner).
- **Coupling.** None.
- **Freshness.**
`django_strawberry_framework/middleware/request_body.py`
`e6e32e785ec84360c63c9ff529a58f8d63bc8898`,
`django_strawberry_framework/_boundary_ordering.py`
`197eea8e01cb405f38b21022689ed54970efcb97`,
`django_strawberry_framework/views.py`
`9f85b0df26a17e800ec392aa13f6848e07633895`,
`tests/test_views.py`
`fa97efdf3309c2944431390a36e7da464c3de327`,
`examples/fakeshop/test_query/test_transport_api.py`
`17320f1ff335a868d5ed324a49f1d7c4ee899cfc`.
Population: 117 package `.py` files.

### F2 — boundary-method-name single-sourcing (existing family `boundary-method-name-single-sourcing`, stays `open`; probe/invoke record from this side)

- **Contract + variation.** The name the recognition accepts a class
for IS the name the hook runs: the probe
(`callable(getattr(view_class, _BOUNDARY_METHOD, None))`) and the
invoke (`getattr(view, _BOUNDARY_METHOD)(request)`) both read the one
constant. Variation axis is the method identity itself.
- **Sites + roles.** *Definition*: `_BOUNDARY_METHOD` (owner elsewhere;
sole spelling, probe-verified). *Behavior referent*:
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary` (the
`def`; never spells the string). *Consumers (this file)*: the probe
and the invoke above. *Oracles*: the def-vs-constant identity row and
the probe-vs-invoke row (both `static-reviewed` here, verified at the
owner item; neither spells the name). *Projection*: both consumers'
docstrings ("not spelled again here").
- **Challenges.** C3 → 1 new owner definition; C4 → 1 name definition
+ 1 referent in views, **0** here.
- **Owner + lifetime.** Unchanged: NAME with `_boundary_ordering.py`,
BEHAVIOR with `views.py`. No stored derivation.
- **Migration.** None.
- **Distinct behavior.** None in this file beyond the two reads being
two reads of one constant: posit a literal at the invoke site → the
drift the probe exists to remove (the probe-vs-invoke oracle's
subject).
- **Behavioral proof.** `execution-verified` for no-second-spelling +
two-read structure (probe). Rejects "the middleware spells the method
name".
- **Structural gate.** The def-vs-constant + probe-vs-invoke oracles
(owner item) + the prospective string-count search. Negative control
(static): an invoke-site literal passes both behavior oracles and
fails only the count search — owed by the family item.
- **Coupling.** None.
- **Freshness.** Same five hashes as F1.

### F3 — CSRF-ordering exemption (existing family `csrf-ordering-exemption`, stays `open`; publish record from this side)

- **Contract + variation.** The exemption answers per request; this
file publishes the fact it answers from: the handling request, for the
span of the downstream call. Variation axes from this side: the
published fact (the request, not a flag) and the twin bodies carrying
it.
- **Sites + roles.** *Definitions*: channel + predicate + instance
(owner elsewhere). *Publish sites (this file)*: `__call__` /
`__acall__` (set around the downstream call, reset in `finally`).
*Assign site*: `views.py::as_view` (singleton identity, no plain
`True`). *Upstream reader*: Django's `CsrfViewMiddleware.process_view`
(`if getattr(callback, "csrf_exempt", False):`, verified by execution
at installed Django 6.1). *Oracles*: the async-reset row (both
predicate clauses plus both resets), the both-transports callback-mark
row, the duplicate-entry row, the declined-callback and no-CSRF-entry
matrix rows, the live shipped-chain rows (titles censused; bodies
under the owner item).
- **Challenges.** C5 → 1 owner definition with twin follow-through
here as consumers; C6 → 1 owner body, **0** here.
- **Owner + lifetime.** Unchanged: `_boundary_ordering.py`. This file
owns the publish discipline: set at middleware entry, reset in
`finally` (sync: after the response exists; async: after the await —
which is why `__acall__` is a second body, L1). The stamp READ is a
pure per-`__bool__`-call derivation ("not cached": no memoization on
the path; probe asserts singleton statelessness at the owner).
- **Migration.** None.
- **Distinct behavior.** Publishing the request rather than a flag is
the load-bearing half from this side: "installed" is chain property,
"ordered" is request property (stated at the `__call__` body).
- **Behavioral proof.** `execution-verified` (probe: twin set/reset
shape, four-state exemption table plus reset and foreign-stamp
isolation executed without settings or DB). Rejects "the exemption
leaks across requests". Oracle bodies `static-reviewed`.
- **Structural gate.** The async-reset oracle (both clauses + both
resets, raise path included). Negative control (static): `return
True` fails its stamped assertion; `return False` fails the unstamped
ones.
- **Coupling.** None.
- **Freshness.** Same five hashes as F1 plus installed
`django/middleware/csrf.py` `3c709f2f4b276fdf837377e93e7f104c46b53dc4`
(Django 6.1 in this worktree's `.venv`; the read-shape line verified
identical by execution; floor-version axis stays with CI via the
CSRF-matrix oracles).

### L1 — middleware publish twin (file-local, intentional separation)

`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.__call__`
+ `::__acall__` (+ the `__init__` coroutine marking + the
`sync_capable` / `async_capable` pair). One rule (publish the handling
request for the downstream-call span, reset in `finally` so a raising
view cannot leak the mark) in two mechanism-forced colors: the reset
must happen after the downstream response exists, and on async that
means after the await (C7 refused, C8 two-bodies — principle-5
record). `__init__` binds `get_response`, runs the ordering audit
(L4), and marks the instance a coroutine function exactly when the
downstream chain is one (probe-verified shape). Gate: the async-reset
oracle (both resets incl. the raise path) + the probe's twin-shape
sections. Negative control (static): a single shared body passes every
sync oracle and fails the async post-await reset row. Freshness:
target `e6e32e78…`, `tests/test_views.py` `fa97efdf…`.

### L2 — boundary-run hook (file-local)

`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`.
One order: ENFORCED early return (duplicate-entry idempotence) →
recognition (L3) → `setup` (L5) → invoke-by-name (F2) →
`HTTPException` refusal (L6) → guarded optional handoff (F1 hygiene)
→ PREPARED_VIEW write → ENFORCED stamp. Challenges C9/C10 move 1 body
here (C9 refused by the request-local-state contract). The handoff is
written only after the boundary passed, and the stamp only after the
handoff attempt, so a later entry (or the view) never sees a partial
result. Gate: the minimal-boundary run row (run recorded + stamp set)
+ the duplicate-entry row. Negative control (static): dropping the
stamp passes the run row and fails the idempotence row. Freshness:
target `e6e32e78…`, `tests/test_views.py` `fa97efdf…`.

### L3 — package-view recognition (file-local)

`middleware/request_body.py::_package_view_instance`. One decision
ending at the boundary: MARKER read → `view_class` / `view_initkwargs`
bookkeeping shape (Django's own `as_view` bookkeeping, `isinstance`
gates so a non-class is never called) → callable probe of
`_BOUNDARY_METHOD` on the class (never the instance: C12 refused —
answering costs a foreign `__init__`) → construction from the named
kwargs. Every attribute read guarded to `None` (a read that cannot be
completed recognized nothing: C11 refused — stopping at the
bookkeeping shape turns a foreign callback into a 500); only the
construction's `TypeError` is caught narrowly, because a guard there
would sit across the body cap's own errors (C13 refused). No `or {}`
default: absent means "not ours" (probe-verified code shape). Gate:
the never-constructed-foreign-class row + the three raising-read
decline rows + the minimal-boundary run row. Negative control
(static): probing the instance passes the decline rows and fails the
unrecorded-construction assertion. Freshness: target `e6e32e78…`,
`tests/test_views.py` `fa97efdf…`.

### L4 — ordering audit (file-local)

`middleware/request_body.py::_require_boundary_before_csrf` +
`::_MISORDERED_MIDDLEWARE_MESSAGE` (raised as
`exceptions.py::ConfigurationError`, composed by name — the audit
owns no error vocabulary). Read off `settings.MIDDLEWARE` live at
chain-build time (startup failure, not first-request failure);
entries resolved via `import_string` and compared by class, so a
subclass on either side is recognized as what it is (C14 refused);
function entries skipped, never probed; the FIRST entry of each kind
decides (the first boundary entry measures first, the first CSRF
entry parses first — C15 refused); a chain with no CSRF entry passes
(no read to run behind; the view's own continuation still protects).
Gate: the misordered-refusal row + the subclass row + the two
first-entry rows + the three accepting chains. Negative control
(static): dotted-path comparison passes the base-class row and fails
the subclass row. Freshness: target `e6e32e78…`,
`django_strawberry_framework/exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`,
`tests/test_views.py` `fa97efdf…`.

### L5 — setup lifecycle fidelity (file-local)

`_NO_SETUP` + the `setup` block in `process_view`. The sentinel
separates "no Django setup lifecycle" (boundary-only recognition
stands) from "shadows `setup` with a non-callable" (must fail exactly
as `View.as_view` would when it calls it — C16 refused). `setup`
runs before the boundary (C9's contract: a consumer subclass may
derive request-local boundary state there); a missing `request`
attribute afterwards raises the `AttributeError` Django's own message
shape, before any stamp (both parity oracles pin middleware-vs-direct
equality and the unstamped request). Gate: the non-callable-setup
row + the setup-super-invariant row. Negative control (static):
calling the attribute unconditionally passes package-mount rows and
500s the minimal foreign callbacks. Freshness: target `e6e32e78…`,
`tests/test_views.py` `fa97efdf…`.

### L6 — refusal render (file-local)

The `except HTTPException` arm in `process_view`: `HttpResponse`
with the exception's own `reason` / `status_code` as `text/plain` —
the same shape upstream's `dispatch` produces, so a client cannot
tell which side of the CSRF check refused it (stated at the body;
both `dispatch` translations verified at the views item). Composed,
never restated: no status, reason, or content-type literal of its own
beyond the `text/plain` the wire shape requires. C17 → 1 body here,
refused by the non-attributability contract. Gate: the live
indistinguishability rows + the package-tier refusal-shape rows
(titles censused). Negative control (static): a JSON envelope passes
status assertions and fails the content-type rows. Freshness: target
`e6e32e78…`, `tests/test_views.py` `fa97efdf…`,
`test_transport_api.py` `17320f1f…`.

### L7 — leaf manifest (file-local)

`middleware/request_body.py::__all__` (exactly the middleware class).
Reached by dotted settings path, never re-exported: package root
never imports it (verified: zero `request_body`/`middleware`/
`Boundary` hits in `django_strawberry_framework/__init__.py`) and
`middleware/__init__.py` deliberately re-exports nothing (read at its
body) — importing the leaf module is the opt-in, the same posture the
`middleware/__init__.py` item records. No production importer exists:
deployments reach the class through the `MIDDLEWARE` string
(fakeshop's shipped chain); only the two oracle files import it by
name. C18 → 1 (the tuple). Gate: the by-name oracle imports (a
rename without a manifest update fails at import). No bespoke gate
owed beyond it. Freshness: target `e6e32e78…`,
`django_strawberry_framework/middleware/__init__.py`
`6e1b64ca7b937bb71e9cadeadd92e82236d9e1f8`.

### Checked-not-member rejections (no index rows; durable homes cited)

- **J1 — measurement rules.** The nine `_request_body.py` file-local
rules (attribute centralization, ladder, probe, capability halves,
restore, bounded read, chunk ceiling, signals, manifest) carry zero
code-token traffic here (AST code-token sweep, probe section 10:
no `_body` / `_stream` / `_read_started` / `body_exceeds_limit`).
This module invokes the boundary by method name and translates its
refusal; it never measures. Trigger: a chain-position measurement
(e.g. a middleware-phase handshake needing its own size probe).
Durable home: the target module docstring's "holds no policy of its
own" clause + spec-046 Decision 7.
- **J2 — `sync-adapter-raw-body-source`.** Zero traffic (no adapter
token in code). Contract difference (re-derived from this side):
process-scope workaround vs mount-scope permanent body source — both
upstream of any chain position; a middleware entry cannot choose a
view's adapter. Trigger: unchanged (upstream fixing the eager
decode). Durable home: the indexed rejection + the views-side
record.
- **J3 — `decode-failure-400-translation`.** Zero traffic (no
`parse_json` / decode token in code). The `except HTTPException` here
translates the boundary's own refusal (L6), not a foreign decode
raise — different exception, different direction. Trigger:
unchanged. Durable home: the indexed rejection.
- **J4 — `request-body-json-parse-reason`.** Zero traffic (no reason
literal in code). Trigger: unchanged. Durable home: the indexed
rejection.

## Defects

None. Every docstring/comment claim checked while tracing held: no
import of `views.py` in either direction involving this module
(probe-verified; `views.py` imports the protocol module, never the
middleware); twin set/reset shape with `finally` on both; statement
order in `process_view` (guard → recognition → setup → run → refuse
→ handoff → stamp, probe-verified by position); audit semantics
(class comparison, first-entry-wins, function skip, no-CSRF pass);
`_NO_SETUP` identity check; no `or {}` default in code; root and
`middleware/__init__.py` never import the leaf; installed Django
reads `csrf_exempt` for truthiness at request time. Nothing routed to
any owner.

## Pending execution

None. The single execution proof (read-only probe, command in
`### Challenges` head) already ran green (96/96) against the shared
tree; it mutates nothing, opens no database, touches no settings,
and runs no pytest. No `execution-deferred` items. No shared-tree
pytest was run (item rules). The sharded/Postgres cells are
`inapplicable by construction`: the target performs no query,
connection, alias, or dialect decision.

## Judgment

Backstop discharged: 18/18 `ast.Module.body` members enumerated, 18
challenges run, every rule terminating in a reused indexed family
(F1–F3, all `open`, publish/consumer records from this side), a
file-local row with its proving challenge (L1–L7, twins as an
intentional separation), or a checked-not-member rejection with
difference, trigger, and durable home (J1–J4). No existing family is
renamed; no new family is named (every cross-file rule here already
has a holding family; the twin pair is a mechanism-forced intra-file
separation). Zero-edit result is legitimate.

Proposed `## Responsibility index` rows for Worker 0 to add (all
file-local, holding item File `middleware/request_body.py`):

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `middleware-publish-twin` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.__call__` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `boundary-run-hook` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `package-view-recognition` | `django_strawberry_framework/middleware/request_body.py::_package_view_instance` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `ordering-audit` | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `setup-lifecycle-fidelity` | `django_strawberry_framework/middleware/request_body.py::_NO_SETUP` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `refusal-render` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `middleware-leaf-manifest` | `django_strawberry_framework/middleware/request_body.py::__all__` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
db5c5b791de72d7ebab4675c0643320b5d5bbacf --
django_strawberry_framework/middleware/request_body.py` is empty (0
bytes); the working blob
`e6e32e785ec84360c63c9ff529a58f8d63bc8898` equals both the item
baseline and `HEAD:` — the target is clean against both, so no hunk
attribution was owed. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched. Concurrent dirt named in the
plan item (`django_strawberry_framework/connection.py`,
`tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, in-flight
`django_strawberry_framework/filters/inputs.py` +
`tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus the
further concurrent dirt (`extensions/resource_policy.py`,
`filters/sets.py`, `forms/inputs.py`, `mutations/fields.py` and
companions) was never edited, reverted, or tidied. Untracked scratch
created (not tracked changes): this artifact
`docs/dry/dry-file-middleware__request_body.md` and the read-only
probe
`docs/dry/temp-tests/dry-file-middleware__request_body/probe_request_body_middleware.py`
(96/96 green after `uv run ruff format` + `uv run ruff check --fix`
scoped to that path only; remaining ANN/D/E402 nits live in
untracked scratch, not shipped). Freshness fingerprints
(`git hash-object` working tree): `middleware/request_body.py`
`e6e32e78…`, `_boundary_ordering.py` `197eea8e…`, `views.py`
`9f85b0df…`, `_request_body.py` `a70571ff…`,
`middleware/__init__.py` `6e1b64ca…`, `exceptions.py` `e06b0b7f…`,
`middleware/debug_toolbar.py` `5360149b…`, `tests/test_views.py`
`fa97efdf…`, `test_transport_api.py` `17320f1f…`,
`config/settings.py` `e2ba5114…`, `docs/GLOSSARY.md` `bcc99607…`,
`docs/README.md` `6b8cfbe8…`,
`spec-046-transport_security-0_0_14.md` `8d8adaf2…`; installed Django
6.1 `middleware/csrf.py` `41e503dc…` (read-shape line verified
identical by execution); searched population 117 package `.py`
files. No commit.

## Independent verification (Worker 2)

Own trace re-derived from the target, the views enforcement half
read FIRST, then the protocol owner, oracles, and a fresh re-run of
the read-only probe. Every difference vs W1 is reconciled per row
below. Procedural note: the artifact's `## Findings` was opened
before the consumer trace finished (required-order deviation);
substance is still expectation-first — every count below was
recomputed from source (`ast.parse` listing, package-wide greps,
probe re-run), not copied.

### Own rule derivation (counts + owners I would choose)

- **Protocol marks (4 names + channel + method name = 6 bindings).**
Target imports all six by name from `_boundary_ordering.py`,
spells zero literals (no `graphql_request_body_boundary`,
no `_enforce_request_boundary` in source — grep-verified). Writes
ENFORCED + PREPARED_VIEW, reads MOUNT + MARKER. Owner:
`_boundary_ordering.py`. Agree F1 (publish/write record).
- **Method name (probe + invoke, 2 reads of 1 constant).** Probe
`callable(getattr(view_class, _BOUNDARY_METHOD, None))` on the
class; invoke `getattr(view, _BOUNDARY_METHOD)(request)` on the
built instance. Behavior referent is the `def` at
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary`;
neither file spells the string. Owner: NAME elsewhere, BEHAVIOR
at views. Agree F2.
- **Exemption (publish twin).** `__call__` / `__acall__` set the
channel around the downstream call, reset in `finally`; assign
site is `views.py::as_view` (`csrf_exempt = _CSRF_ORDERING_EXEMPTION` by identity — read at its body, line
579); upstream reader is Django's
`CsrfViewMiddleware.process_view` truthiness read (re-verified by
execution at installed Django: line 6 of the method source is
`if getattr(callback, "csrf_exempt", False):`). Owner:
`_boundary_ordering.py`. Agree F3.
- **Publish twin (2 bodies, 1 rule).** Split is
mechanism-forced: a shared sync body would reset the mark in
`finally` before the downstream coroutine ever runs. `__init__`
binds `get_response`, runs the audit, marks the coroutine case.
Owner here. Agree L1 (intentional separation, principle 5).
- **Boundary-run hook (1 order).** ENFORCED early return →
recognition → setup → invoke-by-name → HTTPException refusal →
guarded optional handoff → PREPARED_VIEW write → ENFORCED stamp
(position-verified by probe re-run). Stamp-after-handoff means
no partial result is ever visible. Owner here. Agree L2.
- **Recognition (1 decision ending at the boundary).** MARKER →
`view_class` / `view_initkwargs` shape with `isinstance` gates →
callable class-level probe → construction; reads guarded
broadly, construction narrowed to `TypeError`; no `or {}`
default. Owner here. Agree L3.
- **Ordering audit (1 check).** Live `settings.MIDDLEWARE` read
at chain-build, `import_string` resolve, class comparison,
function skip, first-entry-wins, no-CSRF pass. Raises the
composed `ConfigurationError`. Owner here. Agree L4.
- **Setup fidelity (1 sentinel + 1 block).** `_NO_SETUP`
separates no-lifecycle from non-callable-shadow (which must fail
as `View.as_view` would); `setup` runs before the boundary;
missing `request` raises before any stamp. Owner here. Agree L5.
- **Refusal render (1 arm).** `HttpResponse` from the caught
exception's own `reason` / `status_code` as `text/plain` —
composed, matching upstream `dispatch` shape (translations
verified at the views item). Owner here. Agree L6.
- **Manifest (1 tuple, 1 name).** Leaf reached by dotted
`MIDDLEWARE` path; root and `middleware/__init__.py` never
import it (grep-verified: zero hits). Owner here. Agree L7.

### Reconciliation vs W1, per row

F1/F2/F3: agree on all three (publish/consumer records, owners
unchanged, all `open`). L1–L7: agree on all seven (single
owners here; twin pair mechanism-forced). J1–J4: agree as
checked-not-member rejections (zero code-token traffic
re-proved by probe section 10, re-run green; differences +
unfired triggers + durable homes all hold). No new family is
owed: every cross-file rule already has a holding family, and
the twin pair is an intra-file separation. One verdict-neutral
observation (not a defect): C13's rationale ("guard sits across
the body cap's own errors") is misplaced — the construction
site cannot raise body-cap errors, which surface later at the
invoke; the operative reason for narrowness is the docstring's
own "determined answer vs no answer" distinction. Count (1 body
here) and refused status stand either way; no change owed.

### Enumeration check (member by member vs own count)

Own `ast.parse` count: **18** top-level statements (matches
W1). Cross-foot from my own listing: 1 `Expr` + 10
`ImportFrom` + 1 `If` + 3 `Assign` (`__all__`,
`_MISORDERED_MIDDLEWARE_MESSAGE`, `_NO_SETUP`) + 1 `ClassDef`
+ 2 `FunctionDef` = 18. Bound defs: the class plus
`_package_view_instance` plus `_require_boundary_before_csrf`.
Class methods with owner: `__init__`, `__call__`, `__acall__`
(async, verified), `process_view`. W1's rows 1–18 home every
member (projection / machinery / consumer imports / L7 / L4 /
L5 / L1+L2+L5+L6 / L3+F1+F2 / L4); no member unassigned. Agree.

### Matrix vs real surface (halves FIRST)

Middleware-vs-view halves verified at both bodies: MARKER
stamped at views 580 / read at target 330; MOUNT stamped 581 /
read 238; PREPARED_VIEW written 242 / consumed once with token
check + `delattr` at views 554–559; ENFORCED written 243 / read
at views 621 and exemption 147; METHOD defined at views 584 /
probed 336 + invoked 230; channel set/reset at target 163–180 /
read at exemption 146; exemption assigned at views 579;
shipped chain lists boundary 103 immediately before CSRF 104.
Sync/async twins compared by behavior (same publish span,
`await` the whole difference; `process_view` one sync body on
both transports — boundary is synchronous). Exactly two `def
process_view` exist package-wide (this file + toolbar's):
sibling recognizer confirmed a different contract (any
Strawberry view by class, diagnostics) vs exact-mount
recognition + boundary run. No reconstructed knowledge (names
by import, mount token by identity, refusal from the exception,
chain by live class comparison). Omission sweep over
{package, foreign} x {sync, async} x {no-CSRF, misordered,
duplicate} all covered; the decline omission is the contract
(pinned by oracles), not a gap. Discharged. Agree.

### Counts + roles; oracles

C1–C18 definition counts re-derived: agree (C4 is 1 name + 1
referent with 0 here; C7/C8 refused by mechanism; C9–C17 each
1 body here with contract refusals; C18 is 1 tuple).
Consumers, oracles, projections listed, never counted —
confirmed. No oracle rewritten: zero production edits, test
files untouched, and oracles import owner symbols by name
(`tests/test_views.py` import block read: middleware class,
`_package_view_instance`, all five protocol names). Oracle
census re-measured: 17 middleware/boundary titles in
`tests/test_views.py` (matches W1; 72 sync + 10 async = 82
total, matching the views item's 82), live shipped-chain rows
in `test_transport_api.py` import `_package_view_instance` and
derive from real `MIDDLEWARE`. Agree.

### Equivalence (principle 8)

Zero-edit item: no behavior to preserve across a change.
Observable claims are census/identity/absence/order facts, all
`execution-verified` by the re-run probe (96/96 green, `uv run
python
docs/dry/temp-tests/dry-file-middleware__request_body/probe_request_body_middleware.py`,
shared tree, read-only, no settings, no DB). Oracle bodies stay
`static-reviewed`; the final gate executes them.
Sharded/Postgres `inapplicable by construction` (no query,
connection, alias, or dialect decision in the target) — agree.

### Zero-edit + coverage/assignment

Item-scoped diff confirmed empty by Worker 2 (`git diff
db5c5b791de72d7ebab4675c0643320b5d5bbacf --
django_strawberry_framework/middleware/request_body.py` = 0
bytes; target absent from `git status --short`). Working blob
`e6e32e78…` equals item baseline and `HEAD:` (canonical
`9031cb3d`). All 18 members homed; no consolidation owed by a
file item; F1–F3 route to existing `open` families; L1–L7
carry proving challenges with index rows proposed below;
J1–J4 carry differences + triggers + homes. Validated.

### Freshness re-hashes (Worker 2)

Target `e6e32e78…` match; `_boundary_ordering.py`
`197eea8e…` match; `views.py` `9f85b0df…` match;
`tests/test_views.py` `fa97efdf…` match;
`test_transport_api.py` `17320f1f…` match;
`_request_body.py` `a70571ff…` match;
`middleware/__init__.py` `6e1b64ca…` match; `exceptions.py`
`e06b0b7f…` match; `debug_toolbar.py` `5360149b…` match;
`config/settings.py` `e2ba5114…` match; `docs/GLOSSARY.md`
`bcc99607…` match; `docs/README.md` `6b8cfbe8…` match. One
correction owed (verdict-neutral, amend in place): installed
`django/middleware/csrf.py` hashes `3c709f2f…` here, not the
recorded `41e503dc…` — the read-shape line it fingerprints was
re-verified identical by execution above, and the sibling views
item records `3c709f2f…` at the same canonical HEAD, so the
venv file moved under W1, not the finding. No finding reopens.
Population re-measured at 117 package `.py` files (probe
re-run). No fingerprint stale.

### Structural gates (negative controls judged plausible)

F1 literal-count search, F2 probe-vs-invoke + def-vs-constant
rows, F3 async-reset row (both clauses + both resets incl.
raise path), L1 twin-shape rows, L2 minimal-run + duplicate
rows, L3 never-constructed + raising-read rows, L4
misordered + subclass + first-entry rows, L5 non-callable +
super-invariant rows, L6 indistinguishability + content-type
rows: each fails exactly its guarding row under the stated
hand-copy (static judgment). Execution of these controls
belongs to the holding family items; a file item owes none.
`## Pending execution` correctly absent (probe already ran
green; no `execution-deferred` proof). Coupling `None`
throughout: correct.

### AGENTS.md prose check

Item diff empty, so no production/test prose to check.
Artifact: no process provenance, no `feedback` mention, 25
`path::Symbol` citation sites, zero raw `path:NN` lines (none
owed — citations are symbolic throughout). Test tier stated
with live-tier shipped-chain rows plus package-tier
recognizer/audit shapes, matching the verified views-item
split. Docs-only edit: no `ruff` run (`ruff format` /
`check --fix` operate on Python; nothing here can violate
them). Concurrent dirt untouched (verified via `git status
--short` before and after; this edit touches only the item's
own untracked artifact, preserving the in-flight filters hunk
and every other hunk).

### Defects (Worker 2)

None. Every docstring/comment claim spot-checked while
tracing held (no `views.py` import in either direction
involving this module; twin set/reset with `finally` on both;
`process_view` statement order; audit class-comparison,
first-entry-wins, function-skip, no-CSRF pass; `_NO_SETUP`
identity check; no `or {}` default; root and
`middleware/__init__.py` never import the leaf; installed
Django reads `csrf_exempt` for truthiness at request time).
Two verdict-neutral observations for Worker 0 (not defects):
(a) amend the F3 freshness Django hash `41e503dc…` →
`3c709f2f…` in place (line above); (b) C13 rationale note
under Reconciliation — no change owed.

### Judgment (Worker 2)

Verified. Publish-side boundary module; shared rules consumed
by name (F1–F3, all `open`); rejections re-derived with
unfired triggers and homes (J1–J4); seven file-local rules
with proving challenges (L1–L7, twin pair an intentional
separation); zero edits, zero pending execution, zero defects.
Worker 0 owes one in-place amendment (F3 Django hash), which
reopens nothing.

Worker-0 instructions. Add these `## Responsibility index`
rows (W1's seven as proposed, endorsed verbatim), all
file-local, holding item File `middleware/request_body.py`:

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `middleware-publish-twin` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.__call__` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `boundary-run-hook` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `package-view-recognition` | `django_strawberry_framework/middleware/request_body.py::_package_view_instance` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `ordering-audit` | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `setup-lifecycle-fidelity` | `django_strawberry_framework/middleware/request_body.py::_NO_SETUP` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `refusal-render` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
| `middleware-leaf-manifest` | `django_strawberry_framework/middleware/request_body.py::__all__` | `django_strawberry_framework/middleware/request_body.py` | File `middleware/request_body.py` | file-local |
