# DRY review: `django_strawberry_framework/middleware/debug_toolbar.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in the one indexed family it belongs to (membership confirmed
against the owner's body, not inherited) or is recorded file-local with its
proving challenge, and every rejection carries its contract difference +
trigger + home. Zero production edits; zero tracked files changed.

## System trace

FRESH target, 301 lines: `DebugToolbarMiddleware`, the server-side
HTTP+HTML toolbar surface for Strawberry Django GraphQL views. It DEFINES the
view-tagging predicate (`process_view` against the engine-owned `BaseView`),
the `debugToolbar` JSON payload builder (`_get_payload`), and the two-shape
response mutation (`_postprocess`: GraphiQL bridge-template append on tagged
200 HTML; `debugToolbar` injection on tagged `application/json` operation
responses minus `IntrospectionQuery`), and it ENFORCES two wiring gates at
leaf import (the soft-dependency install hint via `require_debug_toolbar()`;
the `INSTALLED_APPS` `ImproperlyConfigured`). Everything else — panels,
request tracking, history storage, handle rendering, show-toolbar gating —
stays the stock toolbar's own (spec-042 Decision 6). No queryset execution,
no resolver body, no `sync_to_async`, no `describe_value` tail, no
`OperationState`, no `register_subsystem_clear`, no `__all__`.

Connected code read for judgment, outside the item:
[utils-imports][utils-imports] (raising primitive + floor constants, full),
[middleware-init][middleware-init] (import-clean + no-re-export prose, full),
[request-body][request-body] (sibling leaf: full head + `process_view` +
`__call__`/`__acall__` twin, passages),
[extensions-debug][extensions-debug] (in-response counterpart + R5 relation,
full via its verified artifact),
[extensions-operation-state][extensions-operation-state] (carrier + refusal
point, passages), [routers][routers]`::require_channels` (twin wrapper,
passages), [rf-init][rf-init]`::require_drf` (twin wrapper, full),
[auth-sessions][auth-sessions]`::require_channels` (lazy-call twin,
passages), [keyset][keyset] (direct primitive consumers, passages),
[exceptions][exceptions] (`describe_value` owner scope, passages),
[spec-042][spec-042] Decisions 3/4/5 (lines 1009-1129 read), 6/7/8 (lines
1131-1296 read), 9 (head read), oracles
[test-debug-toolbar][test-debug-toolbar] (absence/broken/guard/floor rows +
coverage-only units + template contract, full) and
[test-debug-toolbar-api][test-debug-toolbar-api] (live-tier split, head +
payload/HTML/introspection/encoding rows), the template asset
[debug-toolbar-html][debug-toolbar-html] (scrub + guard family, head),
`pyproject.toml` dev-group row (floor pin, read), upstream
`strawberry_django/middlewares/debug_toolbar.py` (borrow source, full),
stock `debug_toolbar/middleware.py` (owner of `__call__`/`__acall__` +
`_postprocess` + `show_toolbar`, full), Strawberry core
`strawberry/django/views.py` (`BaseView` + subclass coverage, passages).

Excluded with reason: the concurrent dirt named in the dispatch
(`django_strawberry_framework/connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
IN-FLIGHT `filters/inputs.py` range hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths and none of it names this
namespace. Sibling index rows are precedents only
(`middleware-no-reexport-opt-in-surface` lives file-local at the marker;
`typed-rejection-value-tail`, `operation-bound-extension-mechanism`,
`one-sync-boundary` are indexed elsewhere) — this artifact re-derives
rather than inherits them.

## Verification

### Matrix

**1. Cross-flavor policy mirroring — toolbar HTTP+HTML vs debug-extension
in-response FIRST, by behavior + contract.** Target owns ONE integration's
HTTP surface: while the toolbar is enabled, EVERY JSON response from a
Strawberry Django view gets the `debugToolbar` key (minus
`IntrospectionQuery`), whether from GraphiQL or a programmatic client, plus
the bridge template on tagged 200 HTML. [extensions-debug][extensions-debug]`::DjangoDebugExtension`
owns the opposite surface: a per-operation diagnostic INSIDE the GraphQL
response extensions map under the `debug` key, fail-closed under
`settings.DEBUG` / explicit `allow_unsafe_production` acknowledgement, with
bounded text. Different transports (middleware chain vs engine extension
seam), different keys (`debugToolbar` vs `debug`), different gating
(import-time soft-dep opt-in + toolbar `show_toolbar` vs per-operation
`DEBUG` read), different payloads (panel titles/subtitles + `requestId` vs
SQL rows + exception triples). Unifying them would couple the response
contract to the toolbar's presence — rejected, see R1. Sibling
[request-body][request-body] owns a different boundary (body cap + CSRF
ordering) behind its own `process_view` — same hook name, opposite contract
(rejected, see R5). Considered families `soft-dependency-require-guard`
(member — F1), `typed-rejection-value-tail` (0 tails — R2, do not inherit),
`operation-bound-extension-mechanism` (0 uses — R3, do not inherit).

**2. Sync/async twins.** No colored pair: 0 `async def`, 0 `await` in the
target (grep-verified over the pinned blob). The two overrides are
synchronous by construction — `process_view` is Django's sync hook;
`_postprocess` is the stock toolbar's private sync method, called
synchronously from BOTH stock colors (`__call__` line 160 and `__acall__`
line 188 both `return self._postprocess(...)` without awaiting). Async
support is inherited, not doubled: stock `__init__` sniffs
`iscoroutinefunction(get_response)` and marks the instance; this subclass
adds no `__call__`/`__acall__`, no `sync_capable`/`async_capable`, no ORM
execution. The request-body sibling's `__call__`/`__acall__` twin is the
contrast that proves the point — that twin exists because its reset must
happen after the downstream response exists; nothing here awaits, so no
twin is owed. Considered family `one-sync-boundary`: 0 calls (flag reads +
body decode only) — R4, do not inherit.

**3. Derived rather than repeated knowledge.** Wire keys are deliberate
literals (`debugToolbar`/`requestId`/`panels`/`title`/`subtitle` spelled at
the build sites; the docstring states the bridge key by name). The
`7.0.0` floor lives in exactly one source string
(`_DEBUG_TOOLBAR_INSTALL_HINT`); the re-typed test literal and the
`pyproject.toml` dev-group row are GATED comparators, not second
definitions (the floor test compares all three — F2). The app hint lives
in exactly one source string. `content_type.split(";")[0]` derives the
media type once per `_postprocess` call and both branches read the local,
never re-split. No casing helper, no reconstructed default, no second
spelling of either hint in code (whole-package grep: each `_HINT`
single-sited).

**4. Inverse / round-trip pairs.** One payload shape, two seams in the
same file: `_get_payload` decodes the response body and builds the
`debugToolbar` object; `_postprocess` re-encodes it with
`DjangoJSONEncoder`. Both halves live under one owner (F6/F7), change
together, and have no second owner that can drift. No encode/decode split
across modules. No surface.

**5. Contracts restated in another medium.** Four media: production code
(the definitions); authoritative contract source [spec-042][spec-042]
(Decisions 3–9 + borrowing posture — the only place that can move the
rule); independent oracles (package tier pins absence/broken/guard/floor +
unreachable bails with literals and a fake toolbar, never importing the
hint for expectations; live tier pins HTML marker, named panel payloads,
`TemplatesPanel` absence, `has_content`-false `null`, callable
title/subtitle, introspection skip, `Content-Length` refresh,
`Content-Encoding` early-out through real `/graphql/` HTTP); projections
(module + class + method docstrings, leaf usage line, `middleware/`
marker prose, `TREE.md` folder lines, `GLOSSARY.md` debug-toolbar entry).
A wire change moves the production builder once; oracles and prose follow
as listed-never-counted (every Challenge below). Upstream borrow +
stock behavior are corroborating oracles, not package definitions (R6).

**6. Enforcement by omission.** Every guard the contract requires is
present: import-time soft-dep guard (F1/F4), `INSTALLED_APPS` gate (F3),
`isinstance(view, type)` short-circuit (F5), all four `_get_payload`
bails + non-object refusal (F6), streaming + `Content-Encoding` early-outs
+ tag/media/status gates + introspection skip + `Content-Length`-only
refresh (F7). Four deliberate absences, each resolved: no
`describe_value` tail (no typed rejection is raised here — R2); no
`OperationState` (no per-operation capture state exists — R3); no sync
boundary (no ORM execution exists — R4); no re-export at the marker or
root (the dotted-path surface contract — F8, mechanism half here,
omission halves elsewhere). No member lacks a guard its contract
requires; ambiguous-or-newly-proposed would route to the maintainer, and there is
none.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **25 top-level statements (0–24)**. Every member lands below;
every challenge in `### Challenges` ends in a family row, a file-local
row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (borrow posture, two overrides, soft-dep opt-in, wiring trio, three divergences, template guard family) | (none) | prose projection; F1–F8 + R1/R6 homes |
| 1 | `from __future__ import annotations` | annotation gate | binding (F1/F5/F7 signatures use) |
| 2 | `import collections` | stdlib name | F6 consumer (`OrderedDict` payload) |
| 3 | `import json` | stdlib name | F6/F7 consumer (decode, `operationName`, re-encode) |
| 4 | `from collections.abc import Callable` | typing name | F5/F7 consumer (`view_func` signature) |
| 5 | `from typing import Any` | typing name | F1 consumer (guard return annotation) |
| 6 | `from django.apps import apps` | hard-dep name | F3 consumer (`is_installed` gate) |
| 7 | `from django.core.exceptions import ImproperlyConfigured` | hard-dep name | F3 consumer (gate raise) |
| 8 | `from django_strawberry_framework.utils.imports import require_optional_module` | primitive name | F1 consumer (single owner composed by name) |
| 9 | `_DEBUG_TOOLBAR_INSTALL_HINT: str = ...` | install-hint string (`django-debug-toolbar>=7.0.0`) | F1 + F2 |
| 10 | `_DEBUG_TOOLBAR_APP_HINT: str = ...` | app-hint string | F3 |
| 11 | `def require_debug_toolbar` | guard wrapper | F1 (indexed member) |
| 12 | `require_debug_toolbar()` bare call | import-time guard execution | F4 |
| 13 | `if not apps.is_installed("debug_toolbar"): raise ...` | second wiring gate | F3 |
| 14 | `from debug_toolbar.middleware import _DebugToolbarMiddleware` | optional base | F4 (order) + F7 consumer (super chain) |
| 15 | `from debug_toolbar.toolbar import DebugToolbar` | optional type | F6/F7 consumer (annotations) |
| 16 | `from django.core.serializers.json import DjangoJSONEncoder` | hard-dep name | F7 consumer (re-encode) |
| 17 | `from django.http.request import HttpRequest` | hard-dep name | F5/F6/F7 consumer (annotations) |
| 18 | `from django.http.response import HttpResponse` | hard-dep name | F5/F6/F7 consumer (annotations) |
| 19 | `from django.template.loader import render_to_string` | hard-dep name | F7 consumer (bridge append) |
| 20 | `from django.utils.encoding import force_str` | hard-dep name | F6 consumer (charset decode) |
| 21 | `from strawberry.django.views import BaseView` | engine name | F5 consumer (detection target) |
| 22 | `_HTML_TYPES = {"text/html", "application/xhtml+xml"}` | sniff set | F7 |
| 23 | `def _get_payload` | payload builder | F6 |
| 24 | `class DebugToolbarMiddleware` + `process_view` + `_postprocess` | middleware + 2 overrides | F5 (tag) + F7 (mutation) + F8 (identity) |

Rules: R-guard (8–9, 11: thin wrapper over the raising primitive); R-hint
(9: single install-hint + floor gate); R-appgate (6–7, 10, 13: second
wiring gate); R-order (12–21: import-time execution + sub-guard imports);
R-tag (21, 24-`process_view`: engine-owned view detection + non-class
guard); R-payload (2–3, 15, 17–18, 20, 23: shape bails + panel mapping);
R-mutate (3, 14, 16–19, 22, 24-`_postprocess`: stock-first chain +
streaming/encoding bails + HTML/JSON branches + introspection skip +
length refresh); R-identity (24-class: same-name dotted-path surface, no
re-export). One indexed family confirmed member (`soft-dependency-require-guard`,
F1 — files-covered already names this file, no index change owed); three
indexed families checked with no surface (R2–R4, do not inherit); two
cross-file resemblances rejected with difference (R1 toolbar counterpart,
R5 request-body hook); one external resemblance classified as borrow, not
duplication (R6).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-hint text | reword the install hint (new pip spelling) | **1** (`_DEBUG_TOOLBAR_INSTALL_HINT`; test literal + pyproject row follow as gated comparators) | independent |
| C2 | R-hint floor | floor `7.0.0` → `8.0.0` | **1** (same hint string; test literal + dev-group row follow as gated sites — proves the gate, not a second definition) | independent |
| C3 | R-appgate text | reword the `INSTALLED_APPS` hint | **1** (same app-hint string; gate call follows) | independent |
| C4 | R-order timing | move the guard from import time into each method | **1** (the bare call + sub-guard import block reorder together; primitive untouched) | independent |
| C5 | R-tag target | narrow detection to `GraphQLView` only (drop async coverage) | **1** (`process_view` line; engine base untouched — proves the target is spelled once here) | independent |
| C6 | R-tag guard | drop the `isinstance(view, type)` short-circuit | **1** (`process_view` line; stock + upstream untouched) | independent |
| C7 | R-payload bail | add a fifth shape bail (e.g. empty-body refusal) | **1** (`_get_payload` guard chain) | independent |
| C8 | R-payload key | rename the `debugToolbar` wire key | **1** (`_get_payload` builder; `_postprocess` re-encodes opaquely via `json.dumps` — no second spelling) | independent |
| C9 | R-payload panel | stop skipping `TemplatesPanel` | **1** (`_get_payload` loop guard) | independent |
| C10 | R-payload title | change the `has_content`-false / callable policy | **1** (same loop body) | independent |
| C11 | R-mutate skip | rename the skipped `operationName` | **1** (`_postprocess` branch; builder untouched) | independent |
| C12 | R-mutate encoding | lift the `Content-Encoding` early-out | **1** (same guard; stock untouched — proves separation) | independent |
| C13 | R-mutate bridge | change the bridge template path | **1** (`_postprocess` `render_to_string` arg; asset + template-contract rows follow as oracle/asset) | independent |
| C14 | R-mutate length | always set `Content-Length` (even when absent) | **1** (the two `if "Content-Length" in response` sites move together — one rule, two call sites) | independent |
| C15 | `soft-dependency-require-guard` membership | add a second optional dep to this leaf | **1 here** (a new wrapper + hint here; primitive + sibling wrappers untouched — proves member-not-copy) | member |
| C16 | `typed-rejection-value-tail` check | give a raise here a `got <this>` tail | **0 exist** (no `describe_value`, no typed rejection raised — grep empty) | no surface — do not inherit |
| C17 | `operation-bound-extension-mechanism` check | bind payload state through `_OperationBoundExtension` | **0 uses** (no extension, no state subclass — grep empty) | no surface — do not inherit |
| C18 | `one-sync-boundary` check | route body decode through `run_in_one_sync_boundary` | **0 calls** (charset decode + `json.loads` only; async bound inherited from stock) | no surface — do not inherit |
| C19 | R-identity | rename the class (keep the dotted path) | **1 here** (the class statement; `MIDDLEWARE` strings + marker/root omissions follow as consumers/projections) | independent |

Read-only probes run (non-mutating, shared tree — the workspace recipe
authorizes mutating proofs, of which this item has none): `ast.parse`
enumeration above; whole-package greps per population (`_get_payload` /
`_HTML_TYPES` / `_is_graphiql` / `debugToolbar` / both `_HINT`s /
`TemplatesPanel` / `IntrospectionQuery` single-sited here;
`require_debug_toolbar` defined once here + one prose mention in
[rf-init][rf-init]; `process_view` in 4 files with three distinct
contracts read; `_postprocess` single-sited; `describe_value` /
`OperationLease` / `run_in_one_sync_boundary` /
`_OperationBoundExtension` absent here against 12/5/8/5-file populations);
stock `__call__`/`__acall__` bodies read (both call sync `_postprocess`);
`BaseView` subclass coverage read; upstream borrow diff-read line by line
(three divergences named); template scrub read; floor trio compared
(hint ≡ literal ≡ dev-group row). No behavior an execution could
distinguish beyond what these reads show: every finding below is
`static-reviewed`, there is no `execution-deferred` proof, and no
`docs/dry/temp-tests/` scratch was created.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — `soft-dependency-require-guard` (indexed family: member)

- **Contract + variation.** Every soft dependency exposes one thin
  wrapper over [utils-imports][utils-imports]`::require_optional_module`
  passing its own module name + single install-hint string; present, the
  module is returned; absent, `ImportError` carrying the hint is raised
  with the original chained. No memoization (eviction-simulated absence
  re-hits the guard in one process). Only the top-level package is
  guarded — a present-but-broken submodule propagates its own raw
  `ImportError` naming the real missing module. Legitimate variation:
  module name, hint text/floor — per wrapper.
- **Body/hint/floor verification (the twin check).** Bodies identical:
  `return require_optional_module("debug_toolbar",
  install_hint=_DEBUG_TOOLBAR_INSTALL_HINT)` here vs `return
  require_optional_module("rest_framework",
  install_hint=_DRF_INSTALL_HINT)` at
  [rf-init][rf-init]`::require_drf` vs `return
  require_optional_module("channels", install_hint=_CHANNELS_INSTALL_HINT)`
  at [routers][routers]`::require_channels` (and the lazy-call twin at
  [auth-sessions][auth-sessions]`::require_channels`). Hints distinct:
  `django-debug-toolbar>=7.0.0` vs `djangorestframework>=3.17.0` vs
  `channels[daphne]>=4.3.2`. Floors distinct per dependency. Same shape,
  different guarded module — member, not copy.
- **Sites + roles.** *Definition*: the raising primitive
  [utils-imports][utils-imports]`::require_optional_module` (unchanged by
  this item). *Members*: this file's
  `middleware/debug_toolbar.py::require_debug_toolbar` (import-time call),
  `rest_framework/__init__.py::require_drf` (import-time call),
  `routers.py::require_channels` (import-time call),
  `auth/sessions.py::require_channels` (lazy call after Channels-shape
  recognition), `keyset.py::_cursor_crypto_types` (two direct primitive
  calls — composes by name, no wrapper). *Consumers*: the bare
  `require_debug_toolbar()` call + sub-guard imports (same file).
  *Oracles*: absence/broken-install/guard-unit/floor-gate tests in
  [test-debug-toolbar][test-debug-toolbar] (independent: re-typed literal
  + chained-cause + raw-propagation assertions). *Projections*: wrapper +
  module docstrings, [spec-042][spec-042] Decision 5.
- **Challenges.** C15 → 1 here for a new leaf dep (primitive + siblings
  untouched); posit a primitive signature change → **1** (the owner;
  all wrappers follow by call). C1/C2 → 1 definition for hint/floor
  moves (gated comparators listed, never counted).
- **Owner + lifetime.** [utils-imports][utils-imports]`::require_optional_module`
  (existing owner by responsibility: the one raising primitive every
  guard delegates to). No stored derivation; no lifetime fields owed.
- **Migration.** None — already composes by name; nothing to consolidate.
- **Distinct behavior.** Import-time (this leaf, DRF leaf, router root)
  vs lazy-call (auth sessions) timing is per-site opt-in shape, not a
  second rule; top-level-only vs submodule-raw is the shared contract,
  stated at each wrapper.
- **Behavioral proof.** `static-reviewed`. Rejects "fourth hand-rolled
  import pattern" (grep: every wrapper delegates; no inline
  `import_module`-with-hint elsewhere) and "hint lives twice in code"
  (grep: each `_HINT` single-sited; test literal + TOML row are the
  named gated comparators).
- **Structural gate.** Pre-existing absence/broken/floor suites (fail
  loud on bypass: evict the module and the leaf raises; break the
  submodule and the raw name propagates; drift any of the three floor
  sites and the gate row fails) — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`,
  [utils-imports][utils-imports] `291ecedd…`,
  [rf-init][rf-init] `45cf7b63…`, [routers][routers] `a18c5001…`,
  [auth-sessions][auth-sessions] `fad7feb8…`, [keyset][keyset]
  `df4b5e2f…`, [test-debug-toolbar][test-debug-toolbar] `692f1ef9…`,
  `pyproject.toml` `9be86493…`. Searched population: whole package
  (117 `.py`) for `require_optional_module|require_debug_toolbar|
  require_channels|require_drf`. Excluded on strength of body:
  [rf-init][rf-init]'s prose mention of this guard (docstring citation,
  not a definition).

### F2 — install-hint single-sourcing + floor gate (file-local)

- **Contract + variation.** The one toolbar-absent string lives in
  exactly one source location (`_DEBUG_TOOLBAR_INSTALL_HINT`) and names
  the verified `django-debug-toolbar>=7.0.0` floor; every toolbar-absent
  raise routes through `require_debug_toolbar()`. The floor is GATED in
  exactly three places that must agree (hint, re-typed `_HINT_SUBSTRING`
  test literal, `[dependency-groups].dev` row — the test compares all
  three); anything else restating the floor, docs included, is gated by
  nothing, so a bump sweeps the tree for the package NAME and reads each
  hit. Legitimate variation: hint wording, floor value — here.
- **Sites + roles.** *Definitions*: statements 9, 11 (string + wrapper).
  No second hint string in code (grep single-sited). *Oracles*: the
  hint-matching rows + `test_install_hint_floor_matches_the_pyproject_dev_group_row`
  (independent by the re-typed-literal discipline). *Projections*: the
  in-file gate paragraph (states the trio + the sweep rule).
- **Challenges.** C1, C2 → 1 definition each.
- **Owner + lifetime.** `_DEBUG_TOOLBAR_INSTALL_HINT` (existing owner by
  responsibility: the one string every raise carries). No stored
  derivation.
- **Migration.** None.
- **Distinct behavior.** The gate's narrow-needle warning (sweep for the
  NAME, not the `>=` specifier — a backtick/space restatement does not
  match) is this rule's stated instrument clause.
- **Behavioral proof.** `static-reviewed`. Rejects "floor shared with
  upstream's `>=6.0.0`" (deliberately above: first release with the
  Django 6.0 classifier — [spec-042][spec-042] Decision 5) and "second
  hint site exists" (grep: none).
- **Structural gate.** Pre-existing floor-gate row — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`, `pyproject.toml` `9be86493…`,
  [test-debug-toolbar][test-debug-toolbar] `692f1ef9…`.

### F3 — app-gate second wiring gate (file-local)

- **Contract + variation.** Importing the leaf without `"debug_toolbar"`
  in `INSTALLED_APPS` raises one actionable `ImproperlyConfigured`
  carrying the single `_DEBUG_TOOLBAR_APP_HINT`, instead of Django's
  cryptic `HistoryEntry` app-label `RuntimeError` (the sub-guard
  `debug_toolbar.middleware` import defines that model). The registry is
  ready by `MIDDLEWARE`-resolution import time, so the pre-check is
  valid. Legitimate variation: hint wording — here.
- **Sites + roles.** *Definitions*: statements 6–7, 10, 13. No second
  app gate in the package (grep: `_DEBUG_TOOLBAR_APP_HINT` + the
  `is_installed("debug_toolbar")` call single-sited). *Oracles*:
  `test_leaf_import_requires_debug_toolbar_in_installed_apps`
  (independent: removes the app, evicts only the leaf, expects the
  actionable raise). *Projections*: module docstring wiring paragraph +
  in-file gate comment (spec-042 Error shapes).
- **Challenges.** C3 → 1 definition; posit firing the gate at call time
  instead of import → **1** (the `if` block; leaf import would then
  succeed app-less and fail cryptically downstream — same owner).
- **Owner + lifetime.** The `if not apps.is_installed(...)` block
  (existing owner by responsibility: the only reader of the app
  registration for this leaf). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Settings error (`ImproperlyConfigured`, Django's
  idiom) vs missing-package error (`ImportError` hint) is the deliberate
  two-gate split — different failures, different raises, one leaf.
- **Behavioral proof.** `static-reviewed`. Rejects "gate shared with the
  install hint" (C3 moves one string; different exception type) and "a
  second app gate exists" (grep: none).
- **Structural gate.** Pre-existing app-gate test — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`.

### F4 — import-time guard ordering (file-local)

- **Contract + variation.** The leaf body order is the opt-in: bare
  `require_debug_toolbar()` runs FIRST, then the app gate, then every
  statement import that needs the optional dependency (plus engine/Django
  names that ride beneath the guard by Decision-5 placement). The parent
  [middleware-init][middleware-init] imports nothing optional, so package
  walkers traverse cleanly; only the leaf pays. `E402` is the deliberate
  price, silenced per import. Legitimate variation: which imports ride
  beneath — here.
- **Sites + roles.** *Definitions*: statements 12–21 (call + gate +
  ordered imports). *Single owners composed by name*: the primitive
  (F1), the app registry. *Oracles*:
  `test_package_and_middleware_imports_stay_clean_without_toolbar` +
  `test_leaf_reimports_after_restore` (independent: fresh parent import
  under absence stays clean; two-sided restore holds one object).
  *Projections*: module docstring opt-in paragraph, marker docstring,
  [spec-042][spec-042] Decisions 4/5.
- **Challenges.** C4 → 1 definition (call + block reorder together).
- **Owner + lifetime.** The leaf module body (existing owner by
  responsibility: the opt-in boundary Django's `import_string` reaches).
  No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Import-time (this leaf, DRF leaf) vs lazy-symbol
  (router PEP 562) timing is the spec's divided rule — a top-level module
  innocent walkers must traverse lazies; a dedicated opt-in leaf guards
  at import. This leaf is the latter (nothing imports it except a
  `MIDDLEWARE` string or an explicit import — both are the opt-in).
- **Behavioral proof.** `static-reviewed`. Rejects "guard can move below
  the submodule imports" (then a toolbar-less machine fails raw instead
  of hinted — the absence test would go red) and "second ordering owner
  exists" (grep: one bare call).
- **Structural gate.** Pre-existing clean-import + restore tests — no new
  gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`,
  [middleware-init][middleware-init] `6e1b64ca…`,
  [utils-imports][utils-imports] `291ecedd…`.

### F5 — view detection with the non-class guard (file-local)

- **Contract + variation.** `process_view` tags
  `request._is_graphiql = isinstance(view, type) and issubclass(view,
  BaseView)` where `view = getattr(view_func, "view_class", None)` (the
  attribute `View.as_view()` sets; `functools.wraps`-copying decorators
  such as `ensure_csrf_cookie` preserve). The `isinstance(view, type)`
  guard is the module's first deliberate divergence from upstream
  (spec-042 Decision 7): this middleware runs for ALL global traffic, and
  a non-class `view_class` must not `TypeError`/500 an unrelated view.
  No `super()` chain: the stock toolbar defines no `process_view` hook.
  Detection target is engine-owned (`strawberry.django.views.BaseView`
  covers `GraphQLView` + `AsyncGraphQLView`, subclassed or not) — never
  a package-owned class. Legitimate variation: target class, guard
  shape — here.
- **Sites + roles.** *Definitions*: statement 24-`process_view` (+
  statement 21 `BaseView` binding). No second tagger in the package
  (grep: `_is_graphiql` single-sited here; the three other `process_view`
  hits are the boundary family — R5). *Oracles*: live HTML negatives
  (real class + function views through the decorated fakeshop URL) +
  `test_process_view_tolerates_non_class_view_class` (the 200-less guard
  the stock `RequestPanel` still denies downstream). *Projections*:
  method docstring + module docstring divergence note +
  [spec-042][spec-042] Decisions 6/7.
- **Challenges.** C5, C6, C19-class-half → 1 definition each (`None`
  and every real view class resolve identically to upstream — the guard
  changes no legitimate detection).
- **Owner + lifetime.** `DebugToolbarMiddleware.process_view` (existing
  owner by responsibility: the only writer of the tag). Per-request flag
  lifetime: set here, read in `_postprocess`; no persistence.
- **Migration.** None.
- **Distinct behavior.** `False` for function views / non-class
  attributes vs `True` for any `BaseView` subclass through any decorator
  is this rule; stock's later `AttributeError` on a string `view_class`
  is downstream of it, not part of it (pinned in the unit's docstring).
- **Behavioral proof.** `static-reviewed`. Rejects "bare `issubclass`
  suffices" (reproduced `TypeError` — spec) and "second tag site exists"
  (grep: none).
- **Structural gate.** Pre-existing non-class unit + live negatives —
  no new gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`,
  [test-debug-toolbar][test-debug-toolbar] `692f1ef9…`,
  [test-debug-toolbar-api][test-debug-toolbar-api] `ce31c090…`.

### F6 — payload builder with response-shape bails (file-local)

- **Contract + variation.** `_get_payload` builds the `debugToolbar`
  payload for a JSON operation response, or `None`: `None` when the
  toolbar assigned no `request_id`; `None` on any response-shape failure
  (bytes undecodable under the response's own charset, text unparsable,
  body not a JSON object — the module's second deliberate divergence
  from upstream, which decodes/subscript-assigns unconditionally);
  otherwise the body gains `debugToolbar: {panels, requestId}` from
  `reversed(toolbar.enabled_panels)` — per panel, `title` only when
  `panel.has_content` (else `None` = frontend touches nothing) and
  `nav_subtitle`, each called when callable; `TemplatesPanel` skipped
  (upstream's deliberate exclusion: nav churn floods the payload).
  Legitimate variation: bail set, key spellings, skip set, title policy
  — here.
- **Sites + roles.** *Definitions*: statement 23 (+ statements 2–3, 15,
  17–18, 20 bindings). No second builder in the package (grep:
  `_get_payload` / `debugToolbar` / `TemplatesPanel` single-sited here).
  *Consumers*: the `_postprocess` JSON branch calls it by name (same
  file). *Oracles*: package bails (no-`request_id`, non-object body,
  malformed/undecodable bodies through the full postprocess) +
  live named-payload rows (panels present, `TemplatesPanel` absent,
  `RedirectsPanel` `null`, callable title/subtitle). *Projections*:
  function + module docstrings, [spec-042][spec-042] Decision 6.
- **Challenges.** C7, C8, C9, C10 → 1 definition each.
- **Owner + lifetime.** `_get_payload` (existing owner by
  responsibility: the one place spelling the wire object). No stored
  derivation (per-call local `payload`); no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** Leave-untouched (dev diagnostic never 500s an
  unusual declared-JSON response) vs upstream's unconditional decode is
  the documented fidelity split; verbatim panel mapping otherwise.
- **Behavioral proof.** `static-reviewed`. Rejects "second payload
  spelling exists" (grep: none) and "subscript-assign suffices" (the
  non-object unit would 500 — pinned).
- **Structural gate.** Pre-existing bail + live payload tests — no new
  gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`,
  [test-debug-toolbar][test-debug-toolbar] `692f1ef9…`,
  [test-debug-toolbar-api][test-debug-toolbar-api] `ce31c090…`.

### F7 — postprocess branches with encoding + introspection + length policy (file-local)

- **Contract + variation.** `_postprocess` chains FIRST to
  `super()._postprocess(...)` (the knowingly borrowed coupling upstream
  carries too — spec-042 Risks; the stock pass generates stats/timing,
  renders/stores the toolbar for every response incl. JSON, adds headers,
  inserts the handle into processable HTML), then: streaming responses
  untouched; encoded bodies (`Content-Encoding` present) untouched (the
  module's third deliberate divergence — appending the bridge script to
  a compressed body, or re-encoding one as JSON, corrupts it); tagged
  200 HTML (`_HTML_TYPES` first-segment sniff + `_is_graphiql` +
  status 200) gets `render_to_string(...)` appended via `response.write`
  with `Content-Length` refreshed only when present; tagged
  `application/json` non-HTML gets `operationName` read from
  `request.body` (any exception → `None` — malformed/multipart/GET
  bodies degrade to "inject"), skipped when `"IntrospectionQuery"`
  (spec-042 Decision 8: IDE pollers would flood history), else
  `_get_payload` injection with `DjangoJSONEncoder` re-encode
  (lazy proxies/datetimes) and same conditional length refresh.
  Legitimate variation: bail set, sniff set, skip name, encoder, length
  policy — here.
- **Sites + roles.** *Definitions*: statement 24-`_postprocess` (+
  statements 3, 14, 16–19, 22 bindings). No second mutator in the
  package (grep: `_postprocess` single-sited). *Consumers*: Django's
  middleware chain (stock `__call__`/`__acall__` invoke it). *Oracles*:
  live HTML/JSON/introspection/panel-route/encoding rows + package
  streaming/malformed units (the branches no live request reaches).
  *Projections*: method + module docstrings, [spec-042][spec-042]
  Decisions 6/8.
- **Challenges.** C11, C12, C13, C14 → 1 definition each (C14's two
  `Content-Length` sites are one rule, two call sites — counted once).
- **Owner + lifetime.** `DebugToolbarMiddleware._postprocess`
  (existing owner by responsibility: the only mutator of GraphQL
  responses for this surface). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** View-scoped injection (every tagged JSON
  operation, GraphiQL or programmatic — the bridge strips the key only
  inside the GraphiQL page) vs IDE-scoped is stated on the class; the
  stock-first ordering (history rows + `render_panel` content exist
  because the stock pass ran) is the load-bearing sequence.
- **Behavioral proof.** `static-reviewed`. Rejects "stock pass can be
  skipped for JSON" (then history/`render_panel`/`NoReverseMatch`
  behavior diverges — spec) and "second mutation site exists" (grep:
  none).
- **Structural gate.** Pre-existing live + unit branches — no new gate
  owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`,
  [test-debug-toolbar][test-debug-toolbar] `692f1ef9…`,
  [test-debug-toolbar-api][test-debug-toolbar-api] `ce31c090…`,
  [debug-toolbar-html][debug-toolbar-html] `087cd9cb…`.

### F8 — class identity as the dotted-path surface (file-local)

- **Contract + variation.** The class is named `DebugToolbarMiddleware`,
  matching both upstream's subclass and the stock class it extends; the
  distinctly-ours identity is the dotted path
  (`...middleware.debug_toolbar.DebugToolbarMiddleware`), the Django
  middleware convention consumers pattern-match. No package-root or
  marker re-export: the consumer surface is the full leaf path in a
  `MIDDLEWARE` string (spec-042 Decision 3). Legitimate variation: class
  name, module path — here (a rename moves this statement; settings
  strings follow as consumers).
- **Sites + roles.** *Definitions*: statement 24-class (one subclass).
  No second middleware class for this surface (grep: one
  `class DebugToolbarMiddleware` in the package besides the stock/upstream
  externals). *Related index row*: `middleware-no-reexport-opt-in-surface`
  (file-local at [middleware-init][middleware-init]) owns the cross-file
  omission contract; this file holds the mechanism half (guard call +
  module-global class), not a second definition. *Oracles*: star-import
  cleanliness (`DebugToolbarMiddleware not in namespace`) + live
  `MIDDLEWARE` wiring (fakeshop ships this path, replacing the stock
  entry — listing both runs the toolbar twice). *Projections*: class +
  module docstrings, marker prose, [spec-042][spec-042] Decision 3.
- **Challenges.** C19 → 1 here (root/marker omissions follow as
  projections, never counted).
- **Owner + lifetime.** `DebugToolbarMiddleware` (existing owner by
  responsibility: the dotted-path identity). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Same-name ecosystem convention vs uniquely-ours
  path is the stated split; the `middleware/` singular (vs upstream
  plural) follows the package's subsystem convention (spec-042 Decision
  4).
- **Behavioral proof.** `static-reviewed`. Rejects "root re-export
  suffices" (then toolbar-less `import *` pays the soft dep — the
  cleanliness test would go red) and "second class exists" (grep: none
  in-package).
- **Structural gate.** Pre-existing cleanliness + live wiring — no new
  gate owed.
- **Coupling.** None.
- **Freshness.** Target `5360149b…`,
  [middleware-init][middleware-init] `6e1b64ca…`.

### R1 — debug-toolbar vs debug-extension counterpart (rejected)

Considered: one "debug surface" rule spanning this file and
[extensions-debug][extensions-debug]`::DjangoDebugExtension` (the plan
item names it; the debug-side artifact records it as R5). Contract
difference, re-derived from THIS side: this file injects a `debugToolbar`
payload into tagged HTTP responses + HTML over the middleware chain
(server-side seam, toolbar opt-in at leaf import, panels/history store
via stock, `IntrospectionQuery` skip to protect history); the extension
publishes per-operation SQL + exceptions INSIDE the GraphQL response
extensions map under `debug` (engine seam, fail-closed under `DEBUG`,
bounded text, no soft dep). Transport, key, gating posture, and payload
all differ — unifying them couples the response contract to the toolbar's
presence. Trigger to reconsider: a decision to drive both surfaces from
one switch (contradicts both fail-closed postures today). Durable home:
the module docstring paragraph 1 (already names the extension as the
in-response counterpart it ports graphene's capability alongside of —
relation stated, not shared) + the debug-side class docstring
list-order passage.

### R2 — `typed-rejection-value-tail` (indexed family: checked, not inherited)

Considered: composing `describe_value` tails onto this file's raises
(the plan item names it). No surface: 0 `describe_value` occurrences,
0 typed rejections raised — the only raises are the `ImportError` hint
(F2) and the `ImproperlyConfigured` app hint (F3), both with static
strings. The family's 12-file population was swept; every member raises
a value-carrying rejection this file never raises. Contract difference:
the family owns "a typed rejection's `got <this>` tail must render
without ever raising"; this file has no value to render. Trigger to
reconsider: raising a consumer-supplied value here (a validator-style
refusal) would open a genuine tail site owned here. Durable home: this
artifact (nothing in the target states a tail because there is none to
state).

### R3 — `operation-bound-extension-mechanism` (indexed family: checked, not inherited)

Considered: binding payload/tag state through
[extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`
(the plan item names it). No surface: 0 uses, 0 imports, 0 state
subclasses — tag lifetime is one request attribute (`_is_graphiql` set in
`process_view`, read in `_postprocess`); payload lifetime is one call
local. The family's 5-file population (optimizer extension + three
extension siblings + carrier) was swept on mechanism, not name. Contract
difference: the family owns per-operation extension state with runner
binding + reconstruction refusal; this file's state is per-request
middleware tagging with no runner, no resume, no refusal. Trigger to
reconsider: per-operation scratch surviving beyond `_postprocess` (a
resume registrar, a budget) would open a genuine state site. Durable
home: this artifact.

### R4 — `one-sync-boundary` (indexed family: checked, not inherited)

Considered: routing the charset decode / body parse through
`utils/querysets.py::run_in_one_sync_boundary`. No surface: 0 calls —
`force_str` + `json.loads`/`json.dumps` only, no ORM execution, no
`sync_to_async`, and the hook is two sync overrides serving both colors
via the stock chain rather than a sync/async twin pair. The family's
8-file population was swept. Contract difference: the family owns "ORM
work must not interleave with awaits inside a transaction"; this file's
rule is "observe/decode the body for exactly this response" with no
transaction and no await. Trigger to reconsider: queryset execution
inside either override would make the boundary rule reach it. Durable
home: this artifact (the stock-called-sync fact is stated in Matrix
axis 2).

### R5 — request-body `process_view` resemblance (rejected)

Considered: one shared `process_view` rule with
[request-body][request-body]`::GraphQLRequestBodyBoundaryMiddleware.process_view`
(same hook name, same file-population grep). Contract difference: that
hook runs a package view's body cap + CSRF ordering from the chain
(marker/`view_class`/`view_initkwargs`/boundary-method probe, stamp +
exemption bookkeeping, misordering refusal); this hook tags
`_is_graphiql` via engine-owned `BaseView` with a non-class guard and
chains to nothing. Same Django hook, opposite responsibilities — posit a
cap-limit change → only the boundary side moves; posit a detection-target
change → only this file moves (C5 moves one side). Trigger to
reconsider: a single hook owning both tagging and boundary enforcement
(an ordering the chain cannot express) would make the sites one rule.
Durable home: each method's docstring (both already state their own
contract) + `_boundary_ordering.py` marks (the boundary side's stated
owner).

### R6 — upstream borrow resemblance (classified, not duplication)

Considered: one shared rule with upstream
`strawberry_django/middlewares/debug_toolbar.py` (`process_view` +
`_postprocess` + `_get_payload` + `_HTML_TYPES`) and the stock toolbar's
`_postprocess`. Not package duplication: the population is package
source under `django_strawberry_framework/`; upstream + stock are
external oracles/owners. The borrow is verbatim except the three named
divergences (`isinstance` guard, `_get_payload` shape bails,
`Content-Encoding` bail) + floor + module rename + dropped `@override` +
template guard family — each documented in [spec-042][spec-042] and the
module docstring rather than counted. Trigger to reconsider: vendoring
the stock panel/history machinery in-package would make the borrow a
package-owned copy. Durable home: the module docstring borrowing
paragraph + [spec-042][spec-042] Decision 6 + `## Borrowing posture`.

## Defects

None. Checked claims, all held: two-override shape (no other override in
the class — AST-verified); import-time guard + clean root/marker imports
(pinned by the cleanliness oracle); wiring trio semantics (stock-replace,
URLconf `NoReverseMatch`, app-gate `ImproperlyConfigured` — spec + oracle
corroboration); all three divergences present as stated; hint floor trio
agrees (`rows == [_HINT_SUBSTRING]`, hint contains it — read in both
files); top-level-only vs broken-submodule-raw split (dedicated oracle);
`_HTML_TYPES` verbatim; panel mapping (`TemplatesPanel` skip,
`has_content`-false `None`, callable titles — live + unit corroboration);
introspection name-skip with broad-`except` degrade; conditional
`Content-Length` refresh on both paths; streaming + encoding early-outs.
The axis-6 sweep finds no member lacking a guard its contract requires.

## Pending execution

None. No `execution-deferred` proof: all findings are `static-reviewed`
on read-only probes, and every behavior is exercised by the two existing
tiers on every suite run.

## Judgment

Zero-edit file item. Eight rules traced: one indexed family confirmed
member (`soft-dependency-require-guard`, F1 — files-covered already names
this file, no index change owed) with body/hint/floor verified; seven
file-local with proving challenges (C1–C14, C19); three indexed families
checked with no surface and not inherited (R2–R4); two cross-file
resemblances rejected with difference + trigger + home (R1 counterpart
from this side, R5 boundary hook); one external resemblance classified
as borrow (R6). No defects, no pending execution, no production edits.
Worker 0 owes seven `## Responsibility index` file-local rows (F2–F8);
F1 confirms the existing family row unchanged; R1/R5 triggers ride their
existing items; R2–R4 and R6 need no rows (homes in this artifact +
standing prose).

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `2b0a87c0b9ef3e1a097b0fd2c501955b3fcc1fbb`:
`git diff <baseline> -- django_strawberry_framework/middleware/debug_toolbar.py`
empty; working blob `5360149bfa207e707c98985e9a1d79672220b210` matches
`HEAD:django_strawberry_framework/middleware/debug_toolbar.py` — target
CLEAN, so no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-middleware__debug_toolbar.md`) is a new untracked
file, the item's only output. No `uv run ruff format .` / `ruff check`
run (no edits to format). No shared-tree pytest run. No
`docs/dry/temp-tests/` scratch created (read-only probes only — see
`### Challenges` note; a probe could distinguish nothing a mutating run
would change). Concurrent dirt listed in the dispatch (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, IN-FLIGHT `filters/inputs.py` range hunk +
`tests/filters/test_inputs.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) plus the other untracked `dry-file-*.md`
artifacts were left untouched; the `## Owned changes` ledger (walker D1
fix + 2 live test files) gains no row from this item. No commit.

## Independent verification (Worker 2)

Method note: the batch read exposed `## Findings` before consumer reads
finished; I re-derived counts, greps, and hashes from the target/blob
first and reconciled against W1 only afterwards. No
`docs/dry/worker-memory/` read. No probe ran (dispatch: inline analysis
only); every proof below is `static-reviewed` against the pinned blob
plus the two permanent oracle tiers, which execute the behavior every
suite run.

### Own trace (before reconciling)

Target: 301 lines, HEAD `9031cb3d`, working blob
`5360149bfa207e707c98985e9a1d79672220b210` == `HEAD:` blob (re-hashed
myself). Rules re-derived with definition counts and the owner I would
choose:

- T1 soft-dep guard wrapper: `middleware/debug_toolbar.py::require_debug_toolbar`
  delegates to `utils/imports.py::require_optional_module` with its own
  module name + hint. Twins read: `rest_framework/__init__.py::require_drf`
  (import-time), `routers.py::require_channels` (import-time),
  `auth/sessions.py::require_channels` (lazy), `keyset.py::_cursor_crypto_types`
  (2 direct primitive calls, no wrapper). Posit a new leaf dep -> 1 here;
  posit a primitive signature change -> 1 at the primitive. Owner:
  `utils/imports.py::require_optional_module`. Member, not copy. (Agrees F1.)
- T2 install hint + floor: one source string
  `middleware/debug_toolbar.py::_DEBUG_TOOLBAR_INSTALL_HINT` naming
  `django-debug-toolbar>=7.0.0` (re-extracted from blob, test literal,
  and the `pyproject.toml` dev-group row — all three read `7.0.0`).
  Reword/floor-bump -> 1 definition; comparators follow gated. Owner: the
  hint string. (Agrees F2.)
- T3 `INSTALLED_APPS` gate: `apps.is_installed("debug_toolbar")` pre-check
  raising `ImproperlyConfigured` with the single
  `middleware/debug_toolbar.py::_DEBUG_TOOLBAR_APP_HINT`. Reword/retime ->
  1. Owner: the leaf `if` block. (Agrees F3.)
- T4 import-time ordering: bare `require_debug_toolbar()` first, app gate
  second, sub-guard imports beneath (`E402` silenced). Move-guard-into-methods
  -> 1 (call + block reorder together). Owner: the leaf module body.
  (Agrees F4.)
- T5 view detection: `DebugToolbarMiddleware.process_view` tags
  `request._is_graphiql = isinstance(view, type) and issubclass(view, BaseView)`
  with `view = getattr(view_func, "view_class", None)`. Narrow-target /
  drop-guard -> 1 each. Owner: `process_view`. (Agrees F5.)
- T6 payload builder: `middleware/debug_toolbar.py::_get_payload` with
  `request_id` bail + 3 shape bails (charset decode / JSON parse /
  non-object refusal), `OrderedDict` `debugToolbar{panels, requestId}`,
  `reversed(enabled_panels)`, `TemplatesPanel` skip, `has_content`-false
  `None` + callable title/subtitle policy. Bail/key/skip/title changes ->
  1 each. Owner: `_get_payload`. (Agrees F6.)
- T7 postprocess: `DebugToolbarMiddleware._postprocess` chains
  `super()._postprocess` first, then streaming bail, `Content-Encoding`
  bail, tagged-200-HTML bridge append (`_HTML_TYPES` first-segment sniff,
  `render_to_string`, conditional `Content-Length` refresh), tagged
  `application/json` branch with `operationName != "IntrospectionQuery"`
  -> `_get_payload` inject + `DjangoJSONEncoder` re-encode + same
  conditional refresh. Skip/encoding/bridge/length changes -> 1 each
  (two length sites = one rule, two call sites). Owner: `_postprocess`.
  (Agrees F7.)
- T8 identity: class `DebugToolbarMiddleware`, same name as stock/upstream
  by convention; identity is the dotted leaf path; no marker/root
  re-export (omission halves live at `middleware/__init__.py` + root).
  Rename -> 1 here. Owner: the class statement. (Agrees F8.)
- Checked, not inherited: `typed-rejection-value-tail` (0 `describe_value`,
  0 value-carrying raises in target — grep empty), no surface;
  `operation-bound-extension-mechanism` (0 uses/imports/subclasses —
  tag lifetime is one request attr, payload one call local), no surface;
  `one-sync-boundary` (0 calls — `force_str` + `json.loads`/`dumps` only,
  no ORM, no `sync_to_async`), no surface. (Agrees R2/R3/R4.)
- Rejected resemblances: debug-extension counterpart (middleware-chain
  `debugToolbar` HTTP+HTML surface vs engine-seam per-operation `debug`
  extensions map; transport, key, gating, payload all differ — unifying
  couples the response contract to toolbar presence); request-body
  `process_view` (body cap + CSRF ordering vs `_is_graphiql` tag — same
  hook name, opposite contracts); upstream/stock borrow (external
  population, verbatim except the 3 named divergences). (Agrees R1/R5/R6.)

### Enumeration (member-by-member vs own count)

Instrument re-run myself: `ast.parse` over the working blob ->
**25 `ast.Module.body` members**, matching W1's 25 (0–24). Per-member
agreement: 0 module docstring -> prose projection; 1 `__future__` ->
binding; 2 `collections` -> F6; 3 `json` -> F6/F7; 4 `Callable` ->
F5/F7; 5 `Any` -> F1; 6 `apps` -> F3; 7 `ImproperlyConfigured` -> F3;
8 `require_optional_module` -> F1; 9 install-hint string -> F1+F2;
10 app-hint string -> F3; 11 `require_debug_toolbar` -> F1; 12 bare guard
call -> F4; 13 `is_installed` gate -> F3; 14–21 ordered imports ->
F4 (+F5/F6/F7 consumer annotations as listed); 22 `_HTML_TYPES` -> F7;
23 `_get_payload` -> F6; 24 class + 2 overrides (`process_view`,
`_postprocess` AST-confirmed as the only methods) -> F5+F7+F8. Every
member lands in a family row, file-local row, or rejection. No gap, no
double-count. Count confirmed: 25/25.

### Matrix vs real surface (counterpart FIRST)

1. Cross-flavor: counterpart-first comparison done from both sides
   (target full + `extensions/debug.py::DjangoDebugExtension` full:
   862 lines, `extensions["debug"]`, fail-closed `DEBUG`, bounded text,
   no soft dep). Different transports/keys/gating/payloads — R1 stands.
   Request-body sibling (full `process_view` + `__call__`/`__acall__`
   twin read): different contract — R5 stands. `soft-dependency-require-guard`
   member confirmed against all 4 wrapper bodies + 2 direct calls;
   R2/R3/R4 populations swept by grep (20 `require_optional_module`
   hits; `_get_payload`/`debugToolbar`/`TemplatesPanel` single-sited
   here modulo the HTML asset's scrub reads). Discharged.
2. Sync/async: 0 `async def`, 0 `await` in target (grep over target
   returns only the request-body twin's hits elsewhere). Both overrides
   sync by hook shape; no `__call__`/`__acall__`,
   `sync_capable`/`async_capable`, ORM, or `sync_to_async`. Stock
   `__call__`/`__acall__` bodies unreadable in this env (`debug_toolbar`
   not installed outside the dev group) — accepted as corroboration, not
   load-bearing: the no-twin-owed verdict follows from the target alone
   plus the request-body contrast. `one-sync-boundary`: 0 calls. Discharged.
3. Derived knowledge: wire keys deliberate literals; floor single-sourced
   (whole-package grep: each `_HINT` single-sited in code); media type
   derived once per call. Discharged.
4. Round-trip: decode+build (`_get_payload`) vs re-encode (`_postprocess`
   `json.dumps`) under one owner; no cross-module split. Discharged.
5. Other media: spec-042 (Decisions 3–9 + borrowing posture) is the
   contract source; oracles independent (package tier re-types
   `_HINT_SUBSTRING` rather than importing it — confirmed lines 37–53 of
   `tests/middleware/test_debug_toolbar.py`; live tier keys on markers,
   named panels, `TemplatesPanel` absence, `null` title, introspection
   skip, length refresh, encoding early-out through real `/graphql/`
   HTTP); projections listed, never counted. No oracle rewritten to read
   from its owner. Discharged.
6. Omission: all contract-required guards present (F1/F4, F3, F5, F6
   bails, F7 early-outs/tag/media/status/introspection/length); 4
   absences resolved with contract reasons (R2 no value to render; R3 no
   per-operation state; R4 no ORM; F8 omission halves are the surface
   contract). No member lacks a required guard. Discharged.

### Counts + roles; equivalence; zero-edit

Challenges C1–C19 re-judged: C1–C14/C19 -> 1 definition each (C14's two
`Content-Length` sites correctly counted once); C15 -> 1 here (member);
C16–C18 -> 0 (no surface, correctly not inherited). Roles confirmed:
1 raising-primitive definition + 4 wrapper members + 2 direct calls
(F1); single hint/app strings as definitions (F2/F3); leaf body as
ordering owner (F4); `process_view`/`_get_payload`/`_postprocess`/class
as behavior owners (F5–F8); stock/upstream as external oracles, not
definitions (R6). Consumers/oracles/projections listed, never counted.
Principle 8: no consolidation, so no observable-equivalence migration
to prove; `static-reviewed` is adequate because every behavior is pinned
by a permanent oracle that runs each suite (absence/broken/guard/floor,
app gate, clean-import/restore, non-class unit, payload bails, live
HTML/JSON/introspection/encoding/panel-route rows, template contract,
cleanliness + live wiring). No `execution-deferred` proof owed.
Item-scoped diff confirmed empty myself (`git diff
2b0a87c0b9ef3e1a097b0fd2c501955b3fcc1fbb --
django_strawberry_framework/middleware/debug_toolbar.py` prints nothing;
blob equals `HEAD:` blob; file absent from `git status --short`).
Coverage + assignment validated (25/25, above). Routing: F1 reuses the
indexed `soft-dependency-require-guard` row (files-covered already names
this file — no index change owed, confirmed); F2–F8 are file-local
(proposed rows below); R1/R5 triggers ride existing items; R2/R3/R4/R6
need no rows (homes in artifact + standing prose). No production edit
owed by a file item — correctly none demanded.

### Rejections, fingerprints, gates, Pending, coupling

R1/R2/R3/R4/R5 carry concrete contract differences + reconsideration
triggers + durable homes (module/method docstrings, spec-042, boundary
marks, this artifact); R6 classified as external borrow with trigger
(vendoring stock machinery). Fingerprints re-hashed myself — all match
W1 prefixes: target `5360149b…`, `utils/imports.py` `291ecedd…`,
`middleware/__init__.py` `6e1b64ca…`, `rest_framework/__init__.py`
`45cf7b63…`, `routers.py` `a18c5001…`, `auth/sessions.py` `fad7feb8…`,
`keyset.py` `df4b5e2f…`, `tests/middleware/test_debug_toolbar.py`
`692f1ef9…`, `examples/fakeshop/test_query/test_debug_toolbar_api.py`
`ce31c090…`, template asset `087cd9cb…`, `pyproject.toml` `9be86493…`.
W1 omits blobs for spec-042/contract prose and external stock/BaseView
bodies — noted, not a defect: package-production inputs are all
fingerprinted; externals are oracles, not definitions. Negative
controls judged adequate on inspection (no probe authorized): evicted
`debug_toolbar` -> hint-carrying `ImportError` with chained cause;
broken submodule -> raw `ImportError` naming `debug_toolbar.middleware`
with no hint and no cause; drifted floor literal/row -> floor-gate row
fails; app removed + leaf evicted -> `ImproperlyConfigured`; guard moved
below imports -> absence test goes red; second hint/app-gate/payload/
mutation site -> single-sited greps fail; stock pass skipped ->
history/`render_panel`/`NoReverseMatch` divergence per spec; root
re-export -> cleanliness test goes red. `## Pending execution` absent —
adequate: no deferred proof exists. Coupling: none marked — correct
(no cross-finding landing dependency).

### AGENTS.md prose check

Item-scoped diff is empty: no commit, no test/process/metadata edits, no
formatting/lint/line-length surface, no `pragma`, no CHANGELOG, no
branch. Artifact citations use `path::Symbol` (spot-checked F1/R5/R6),
no raw `path:NN` outside the allowed per-cycle artifact scope; link
block is reference-style with all 10 canonical group headers. No
violation. Concurrent dirt preserved: every `git status --short` entry
(connection/extensions/filters/forms/mutations/resource-policy hunks,
staged querysets row, in-flight filters range hunk + companions, plan +
bug-hunt docs, untracked dry-file artifacts) left untouched; the only
writes are this artifact's `Status:` line + this section. No commit.

### Defects (Worker 2)

None. Spot-checks held: 25-member enumeration, 2-method class shape,
hint floor trio agreement, thin-wrapper bodies identical with distinct
hints/floors, single-sited hints/payload/mutator/tagger, all three
divergences present as stated, conditional length refresh on both
paths, streaming + encoding early-outs, `TemplatesPanel` skip +
`has_content`-false `None` + callable policy. No enforcement gap found.

### Verdict

`Status: verified`. Zero-edit file item: 1 indexed-family membership
(F1, no index change), 7 file-local rules (F2–F8, rows below), 3
checked-not-inherited (R2–R4), 2 cross-file rejections (R1/R5), 1
external-borrow classification (R6). No pending execution.

### Exact plan rows Worker 0 should write

Seven `## Responsibility index` file-local rows (append; F1 row
unchanged):

| `debug-toolbar-install-hint-and-floor-gate` | `django_strawberry_framework/middleware/debug_toolbar.py::_DEBUG_TOOLBAR_INSTALL_HINT` | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |
| `debug-toolbar-installed-apps-gate` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware` #"apps.is_installed" gate block | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |
| `debug-toolbar-import-time-guard-ordering` | `django_strawberry_framework/middleware/debug_toolbar.py` leaf module body (bare `require_debug_toolbar()` + ordered sub-guard imports) | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |
| `debug-toolbar-view-detection-guard` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view` | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |
| `debug-toolbar-payload-builder-bails` | `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload` | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |
| `debug-toolbar-postprocess-branches` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess` | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |
| `debug-toolbar-dotted-path-identity` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware` (class identity; omission halves at the marker) | `django_strawberry_framework/middleware/debug_toolbar.py` | File `middleware/debug_toolbar.py` | file-local |

### Scratch

No `docs/dry/temp-tests/` scratch created (read-only probes only).
Workspace recipe not invoked (nothing mutates source). Shared-tree
pytest not run (not authorized; existing tiers discharge behavior each
suite run).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[debug-toolbar-html]: ../../django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[keyset]: ../../django_strawberry_framework/keyset.py
[middleware-init]: ../../django_strawberry_framework/middleware/__init__.py
[request-body]: ../../django_strawberry_framework/middleware/request_body.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[routers]: ../../django_strawberry_framework/routers.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-debug-toolbar]: ../../tests/middleware/test_debug_toolbar.py

<!-- examples/ -->
[test-debug-toolbar-api]: ../../examples/fakeshop/test_query/test_debug_toolbar_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
