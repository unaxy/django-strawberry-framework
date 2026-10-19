# DRY review: `django_strawberry_framework/routers.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a REUSED plan family (re-challenged fresh on the consumer
side), one NEWLY NAMED family for Worker 0 to index (no production edit here;
the family item owns the sweep and the decision), a file-local record with its
proving challenge, or a recorded rejection with difference + trigger + home.
Zero production edits; zero tracked files changed. Target is CLEAN against the
item baseline (`03fd30aa`, probe `item-diff-empty`).

## System trace

Small target (537 lines, 30 top-level statements, working == item baseline).
The package's Channels transport-composition module: it owns no transport
policy of its own and implements no consumer-facing behavior beyond
construction. What it owns is the composition itself -
`routers.py::_build_router_class_uncached` building
`routers.py::DjangoGraphQLProtocolRouter` (function-local, import-unreachable
except through the guard) with `"http"` bound verbatim to the consumer's own
Django ASGI application and `"websocket"` bound to the Host-outside-Origin-
outside-Auth-outside-URLRouter stack - plus every construction-time rejection
on the two seams (`django_application`, `websocket_consumer_class` /
`websocket_revalidation_window` / `websocket_url_pattern`), the lazy soft-guard
materialization (`routers.py::__getattr__`, `routers.py::_ROUTER_CLASS` cache),
and the prose of all eight failure hints, each single-sited.

It CONSUMES by name every other rule it touches: the package consumer factory
and window validator (`consumers.py::build_revalidating_consumer_class`,
`consumers.py::resolved_revalidation_window`,
`consumers.py::_DEFAULT_REVALIDATION_WINDOW`,
`consumers.py::DjangoWebSocketHostValidator`), the tail renderer
(`exceptions.py::describe_value`) with `exceptions.py::ConfigurationError` as
the rejection type, and the optional-import primitive plus both floors
(`utils/imports.py::require_optional_module`,
`utils/imports.py::CHANNELS_FLOOR`,
`utils/imports.py::STRAWBERRY_FLOOR`). Upstream Channels / Strawberry names
(`ProtocolTypeRouter`, `URLRouter`, `AuthMiddlewareStack`,
`AllowedHostsOriginValidator`, `GraphQLWSConsumer`, `re_path`) are read inside
the guarded builder only, never at module level.

Connected code read for judgment, outside the item:
`django_strawberry_framework/consumers.py` (import block,
`consumers.py::_DEFAULT_REVALIDATION_WINDOW` literal,
`consumers.py::resolved_revalidation_window` contract shape, the
`_ROUTER_CLASS`-cache lifetime paragraph naming this module's cache);
`django_strawberry_framework/exceptions.py::describe_value` (full body + scope
docstring claiming exactly this file's three rejections);
`django_strawberry_framework/utils/imports.py` (whole module, 139 lines:
`utils/imports.py::require_optional_module`,
`utils/imports.py::CHANNELS_FLOOR`,
`utils/imports.py::STRAWBERRY_FLOOR`);
`django_strawberry_framework/__init__.py::__getattr__` +
`__init__.py::_DRF_SOFT_EXPORTS` (the PEP 562 twin, full bodies);
`django_strawberry_framework/auth/sessions.py::require_channels` +
its `_CHANNELS_INSTALL_HINT` (sibling guard, full bodies);
`django_strawberry_framework/rest_framework/__init__.py::require_drf` +
its hint (sibling guard, whole module);
`django_strawberry_framework/middleware/debug_toolbar.py::require_debug_toolbar`
(sibling guard, def body);
`django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable` +
`utils/querysets.py::_disposed_awaitable` +
`utils/querysets.py::reject_async_in_sync_context` (def lines + docstrings);
`django_strawberry_framework/schema.py` extension-entry region (def lines
around the `describe_value` tails) and `_ASYNC_MUTATION_LOCKS_GUARD`
(the threading.Lock twin candidate);
`django_strawberry_framework/views.py::_resolved_max_request_body_bytes`
gate line (the int-gate contrast);
`tests/test_routers.py` (117-test census; bodies read for the
async-factory-coroutine row, the http-identity row, the star-import row, and
the concurrent-cache row; titles for the rest); `pyproject.toml`
`channels[daphne]>=4.3.2` row (the floor's second written copy).

Excluded with reason: in-flight spec bodies behind the Decision pointers
(spec-041/046 cited as pointers, behavior pinned by the 38 oracles instead);
`docs/` prose (projections, not relied upon); `connection.py`,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` (concurrent dirt -
read never, touched never); the package-wide exact-type-gate idiom and the
package-wide `except BaseException` mechanism beyond the two sites here (each
site's contract differs; any mechanism sweep belongs to a family item, which
may use the populations recorded in the matrix); the floor wheel for
`strawberry-graphql==0.316.0` (no verdict depends on it); live
`test_transport_api.py` (docstring-cited sibling only, bodies unread - stated
honestly).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The router composes siblings, never
mirrors them. HTTP has no twin here by design (Django's URLconf owns it; the
probe asserts `GraphQLHTTPConsumer` absent and `"http"` verbatim). The
`callable(` floor idiom was swept package-wide (14 sites): every site carries
per-seam prose and a different accepted shape (`seekable`, `hook`,
`get_arg_def`, boundary method, `has_perm`, plan callables, registry
clear/teardown, serializer converter, ASGI application) - one spelling, a
dozen contracts, no shared definition (R2/R6 record the two here). The
`re.compile` population (routers, scalars, four types modules) splits the
same way: grammar decoding elsewhere vs construction-time route validation
here (R3). The `signature.bind` population is this file alone (probe
`sigbind-pop`), so the pre-check has no twin to drift from (R5).

**2. Sync/async twins.** None in target, by construction: zero `async def`
(probe `async-defs-zero`), zero `sync_to_async`, zero
`run_in_one_sync_boundary`, zero `QuerySet`. The one sync-shaped rule this
file touches is negative space by deliberation - router construction is
synchronous and cannot await, so an `async def` factory is rejected rather
than awaited (R6, J3 records the refused inheritance of
`one-sync-boundary`). No behavioral pair to compare.

**3. Derived rather than repeated knowledge.** Four facts this file could
have respelled are composed by name, each probe-pinned: the revalidation
default IS `consumers.py::_DEFAULT_REVALIDATION_WINDOW` by import, never a
second literal (probe `default-import`, `no-second-default-literal`); both
floors are interpolated f-string expressions, never re-typed literals (probe
`no-floor-literal`); the window domain itself is delegated to
`consumers.py::resolved_revalidation_window` (R7); Host matching stays
Django's inside the composed validator (composition only, R1). No
reconstructed copy found.

**4. Inverse / round-trip pairs.** No encode/decode grammar lives here.
Checked and ruled out: hint prose vs raise sites are one wording each, not a
pair; `_build_router_class` / `_build_router_class_uncached` are a
synchronized entry vs its body, not inverses (R8); factory invocation vs
return validation are two phases of one seam with one error type (R5/R6);
`__getattr__` has no setter half. No second half anywhere.

**5. Contracts restated in another medium.** Three media carry this file's
contracts: production code (target); oracles that spell expectations
independently - `tests/test_routers.py` (38 rows: coroutine-`cr_frame`-is-None
row, http-identity row, star-import split row, barrier-concurrency row bodies
read; the window/factory/host/pattern/absence rows titles censused), each
asserting identities and failure types a production change would break rather
than follow; projections (the module/class/function docstrings, which name
every wrapper, seam shape, and guard ordering asserted below - verified
against bodies). Fakeshop mounts no WebSocket endpoint and no `asgi.py`, so
the package tier (in-process construction + communicator rows) is the
strongest reachable tier - stated, not smuggled.

**6. Enforcement by omission.** Three omission shapes checked, each with its
contract source: (a) futures returned by a factory are rejected but NOT
cancelled, while coroutines are closed (F1) - deliberate narrowness, not a
gap: only coroutines emit the un-awaited `RuntimeWarning` the close exists
to suppress, and the docstring states the floor explicitly; (b) the factory's
OWN exceptions propagate un-normalized (R6) - the docstring's stated
contract, pinned by the body-raises oracle row; (c) un-introspectable
callables skip the signature pre-check and are judged by the call (R5) -
the docstring's stated contract, pinned by the two un-introspectable oracle
rows. No missing guard beyond what is recorded and deliberate; no defect.

### Enumeration

Instrument: `ast.parse` over the working-tree blob, counting
`ast.Module.body` - **30 top-level statements** (working == item baseline;
the item-baseline diff is empty, probe `item-diff-empty`) - plus the "or
better" nested census: 1 factory-nested class
(`DjangoGraphQLProtocolRouter`) with 1 method (`__init__`, 3 positional + 3
keyword-only parameters). Every member lands below; every challenge in
`### Challenges` ends in a family row, a file-local record, or a recorded
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (transport contract + guard + seam prose) | (none) | projection |
| 1-5 | imports: future, inspect, re, threading, typing | machinery names | machinery |
| 6 | `from .consumers import (4 names)` | default + validator + factory + window | consumer (R1, R7) |
| 7 | `from .exceptions import (2 names)` | rejection type + tail | consumer (F2; R2-R6) |
| 8 | `from .utils.imports import (3 names)` | guard primitive + both floors | consumer (F3) |
| 9 | `if TYPE_CHECKING` (ASGIHandler, BaseSchema) | annotations only | machinery |
| 10 | `__all__ = ("DjangoGraphQLProtocolRouter",)` | lazy-export manifest | R8 |
| 11 | `_CHANNELS_INSTALL_HINT` | absence prose | F3 (hint text) |
| 12 | `_CHANNELS_BROKEN_HINT` | channels-half breakage prose | R9 |
| 13 | `_STRAWBERRY_CHANNELS_BROKEN_HINT` | strawberry-half breakage prose | R9 |
| 14 | `_MISSING_DJANGO_APPLICATION_HINT` | migrant-mode prose | R2 |
| 15 | `_UNUSABLE_WEBSOCKET_CONSUMER_HINT` | seam-shape prose | R4 |
| 16 | `_FACTORY_CONTRACT_HINT` | factory contract prose | R5 + R6 |
| 17 | `_ASYNC_FACTORY_HINT` | coroutine-mistake addendum | R6 (+ F1 context) |
| 18 | `_WINDOW_WITH_INJECTED_CONSUMER_HINT` | knob-combination prose | R7 |
| 19 | `_INVALID_WEBSOCKET_URL_PATTERN_HINT` | pattern prose (stem) | R3 |
| 20 | `_ROUTER_CLASS` | cached class slot | R8 |
| 21 | `_ROUTER_CLASS_LOCK` | build serialization | R8 |
| 22 | `def _validated_websocket_url_pattern` | pattern gate | R3 |
| 23 | `def require_channels` | soft guard | F3 (consumer) |
| 24 | `def _require_factory_calling_convention` | call pre-check | R5 |
| 25 | `def _factory_application` | invoke + return floor | R6 + F1 (member) |
| 26 | `def _websocket_application` | three-shape selector | R4 |
| 27 | `def _build_router_class` | synchronized entry | R8 |
| 28 | `def _build_router_class_uncached` (+ nested class + `__init__`) | guard order + composition | R1 (root), R2/R4/R7 enforced here |
| 29 | `def __getattr__` | lazy construct-one | J1 (rejected) + R8 (mechanism) |

Cross-cutting: F1 (the coroutine detect-then-dispose inside statement 25);
F2 (the six `describe_value(` tails inside statements 22/24/25/26); F3 (the
guard + hint interpolation inside statements 11/23/28). Rules F1-F2 reuse two
existing plan names; F3 is one NEW name proposed below for Worker 0 to index;
R1-R9 are file-local; J1-J3 are recorded rejections.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 disposal | factory-returned coroutine gains a second cleanup need (e.g. future-cancel) | **1** (`utils/querysets.py::_dispose_sync_awaitable`; this site's narrow close follows only if the family extends it) | member |
| C2 | F2 tail | placeholder grammar changes | **1** (`exceptions.py::describe_value`; all six sites follow by call) | consumer |
| C3 | F3 guard | absence must carry a new signal beside the hint | **1** (`utils/imports.py::require_optional_module`; four wrappers follow) | consumer |
| C4 | F3 floors | verified Channels floor bumps | **2 writes** (owner const + `pyproject.toml` row; hints follow by interpolation, 0) | consumer |
| C5 | R1 composition | a fourth wrapper joins the WebSocket stack | **1** (the composition literal; oracles move) | file-local |
| C6 | R1 http | HTTP needs a wrapper after all | **1** (the `"http"` value; the migrant prose moves with it) | file-local |
| C7 | R2 app gate | a new usable-application shape (e.g. a factory) | **1** (the predicate + hint) | file-local |
| C8 | R3 pattern | a compiled-pattern object becomes acceptable | **1** (the exact-type gate + eager compile) | file-local |
| C9 | R4 selector | a fourth seam shape (e.g. a mounted instance) | **1** (the selector; the class-first order moves with it) | file-local |
| C10 | R5 pre-check | the seam admits a second calling convention | **1** (the bind + allow-through arms) | file-local |
| C11 | R6 return floor | ASGI conformance becomes checkable at construction | **1** (the callable floor + the no-arity-check rationale) | file-local |
| C12 | R7 combination | the window starts configuring injected classes | **1** (the combination rejection; delegation untouched) | file-local |
| C13 | R8 cache | a second lazy export joins the module | **1** (the slot + lock + `__getattr__` arm) | file-local |
| C14 | R9 split | a third import half can break independently | **1** (the hint pair becomes a triple) | file-local |
| C15 | J1-J3 | the three refused shared forms | **0 moves - refused**, differences + triggers in findings | refused |

**Experiments.** Read-only probes only (no source mutation, no SQL, no
Django setup, no shared-tree pytest - the workspace recipe is for mutating
proofs, of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-routers/probe_w1.py
```

Output (`39 checks, 0 failed`): 30-member AST with the full def-name list;
nested census (1 class, 1 method, 6 parameters); zero `async def`; six
`describe_value(` sites; default-by-import with no second literal; floors
interpolated, never re-typed; `__getattr__` construct-one vs root
import-seven with opposite `__all__` decisions and no memoization either
side; coroutine-only close (no future arm) against the owner's close+both
arms; signature pre-check with allow-through; double-checked cache with the
eviction paragraph; Host > Origin > Auth > URLRouter order with `"http"`
verbatim and no `GraphQLHTTPConsumer`; guard-first ordering with three hint
names; no ORM / no boundary import; five-file `__getattr__`, four-file
`require_*`, single-file `signature.bind`, eleven-file `describe_value(`,
four-file `threading.Lock()`, five-file `re.compile` populations;
item-baseline diff empty. Status: `execution-verified` for every
identity/count/shape/absence/import claim below. Rejects the wrong results
"a second definition lives here", "the target drifted from its baseline",
"the default or a floor is respelled", "a twin guard owns this symbol".
Four further read-only sweeps (plain `uv run python` heredocs, same
restrictions): exact-type-gate census (40+ sites, per-domain predicates -
no shared definition); `callable(`-floor census (14 sites, per-seam shapes);
`_ROUTER_CLASS`-in-consumers context (docstring lifetime paragraph, not a
second cache); `tests/test_routers.py` 117-name census plus
`channels[daphne]>=4.3.2` floor-row match. Status: `execution-verified`
for the populations cited. Oracle bodies are `static-reviewed` (four bodies
read, titles censused) and the final gate executes them.

## Findings

No production edit is owed by a file item; F1-F2 reuse the plan's existing
families, F3 is one NEW name proposed for the index, the rest are file-local
records and three recorded rejections.

### F1 - awaitable refusal and disposal (existing family `awaitable-refusal-and-disposal`, stays `open`)

- **Contract + variation.** A refused awaitable is detected, then disposed
without awaiting (native coroutine closed, future cancelled), then refused
with the seam's own error. Variation: which awaitable kinds a seam can meet;
which error type the seam speaks.
- **Sites + roles.** *Definition*:
`utils/querysets.py::_dispose_sync_awaitable` (owner side; family item's
surface). *Inline member here*:
`routers.py::_factory_application` - `inspect.iscoroutine(application)` then
`application.close()`, then `ConfigurationError` with the contract hint plus
the async addendum. The raise correctly stays at the caller (the owner's own
docstring reserves `SyncMisuseError` for sync ORM boundaries; a construction
seam speaks `ConfigurationError`). *Oracles*: the async-factory row asserting
`cr_frame is None` (body read) - the disposal made directly observable.
*Projections*: the close-rationale comment at the site.
- **Challenges.** C1 - the disposal half would move at the owner; the raise
stays here whatever the owner does.
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
derivation here; the coroutine is closed and dropped within the raise path.
- **Migration.** None (zero-edit item; the family item decides whether this
narrow site (coroutine-only, no future arm) composes the owner or stays
spelled out).
- **Distinct behavior.** The narrowness is deliberate and recorded: a factory
returning a future is rejected without cancellation because only coroutines
emit the un-awaited `RuntimeWarning` the close exists to suppress; the
callable floor, the no-arity-check rationale, and the own-exception
passthrough are R6's, not this family's.
- **Behavioral proof.** `static-reviewed` (site body + owner bodies read);
`execution-verified` for the census (coroutine-only here, close+cancel at
the owner). Rejects "this site disposes futures" and "this site awaits".
- **Structural gate.** The `cr_frame is None` row. Negative control: deleting
the `close()` passes every message-shape oracle and fails exactly that row
(family item's gate to execute).
- **Coupling.** None.
- **Freshness.** Target `a18c5001…` + `utils/querysets.py` `1539b66c…`
(def lines + docstrings) + `tests/test_routers.py` `17842b60…`
(coroutine row body read).

### F2 - typed rejection value tail (existing family `typed-rejection-value-tail`, stays `open`)

- **Contract + variation.** Every typed rejection whose value came from
outside the package renders its `got` tail through
`exceptions.py::describe_value`, so the message cannot raise while being
formatted. Variation: per-domain prose; the renderer is fixed.
- **Sites + roles.** *Definition*: `exceptions.py::describe_value` (its scope
docstring already claims exactly this file's three factory/consumer
rejections - verified). *Consumers verified here* (all six call sites,
probe-counted): `routers.py::_validated_websocket_url_pattern` (both arms),
`routers.py::_require_factory_calling_convention` (the bind-failure tail),
`routers.py::_factory_application` (received-value read + returned tail),
`routers.py::_websocket_application` (the selector tail). *Second-side
population for the family item*: eleven files carry `describe_value(`
(consumer census: schema 5, list_field 3, resource_policy 3, error_policy 2,
policies 2, five singles). *Oracles*: the hostile-pattern-repr row (title
censused; the `10**10000` chaining shape is pinned on the consumer side).
*Projections*: per-hint prose stays per site - only the tail is shared.
- **Challenges.** C2 - 1 at the renderer; zero definitions here.
- **Owner + lifetime.** `exceptions.py` (unchanged). Pure derivation, never
cached (principle 4: "not cached" stated by use).
- **Migration.** None (file item).
- **Distinct behavior.** Per-domain prose stays per site - only the tail is
shared; unifying messages would couple unrelated deployment knobs' docs.
- **Behavioral proof.** `static-reviewed` (renderer body + scope paragraph +
all six call sites read); `execution-verified` for the counts. Rejects "this
file interpolates a rejected value itself".
- **Structural gate.** The hostile-repr row (a direct interpolation raises
instead of `ConfigurationError`). Negative control: `f"{value!r}"` at any
site passes every small-value oracle and fails exactly that row.
- **Coupling.** None.
- **Freshness.** Target `a18c5001…` + `exceptions.py` `e06b0b7f…` (body +
scope) + `tests/test_routers.py` `17842b60…` (row title).

### F3 - soft-dependency require guard (NEW family `soft-dependency-require-guard`, proposed `open`)

- **Contract + variation.** Absence of an optional dependency raises one
actionable install-hint `ImportError` (original chained) at the first moment
the integration is reached for; presence returns the module unchanged; no
memoization, so eviction-simulated absence re-fires in one process.
Variation: the guarded module name and the feature-keyed hint text, each
single-sited at its feature owner; hint strings interpolate (never re-type)
the floors owned beside the primitive.
- **Sites + roles.** *Definition*:
`utils/imports.py::require_optional_module` (whole body read; its docstring
already names this file's guard as the wrapped example). *Thin-wrapper
consumers*: `routers.py::require_channels` (own `_CHANNELS_INSTALL_HINT`),
`auth/sessions.py::require_channels` (own hint, Channels-branch-only call),
`rest_framework/__init__.py::require_drf` (own hint, import-time call),
`middleware/debug_toolbar.py::require_debug_toolbar` (own hint, import-time
call) - all four bodies read, all four delegate by name with no hand-rolled
pattern. *Direct consumers*: `keyset.py::_cursor_crypto_types` (two calls,
same hint - read). *Floor facts*: `utils/imports.py::CHANNELS_FLOOR`
(`"4.3.2"`, matching the `pyproject.toml` `channels[daphne]>=4.3.2` row) and
`utils/imports.py::STRAWBERRY_FLOOR`, both interpolated into this file's
three hints with no literal restatement (probe `no-floor-literal`).
*Oracles*: the absence/eviction rows (titles censused; the star-import split
row body read). *Projections*: each wrapper's docstring naming the shared
primitive (verified all four directions).
- **Challenges.** C3 - 1 at the primitive; zero definitions here. C4 - a
floor bump moves 2 writes (owner const + `pyproject.toml` row); every hint
follows by interpolation (0).
- **Owner + lifetime.** `utils/imports.py` (unchanged). No stored derivation
anywhere on this path (each call re-runs the import - the docstrings state
the non-memoization as the eviction-test property).
- **Migration.** None (file item; the family item owns the decision, which
is expected to be keep-the-wrappers: the hint-per-feature split is the
documented single-siting rule).
- **Distinct behavior.** Guard timing differs per feature and stays per site:
router guards lazily at first symbol access, DRF/debug-toolbar guard at leaf
import, auth guards after transport classification - unifying the call moment
would move each feature's import contract.
- **Behavioral proof.** `static-reviewed` (primitive + all four wrappers +
both floor consts + keyset calls read); `execution-verified` for the
populations and the no-literal facts. Rejects "this file hand-rolls an
import pattern" and "a floor is re-typed here".
- **Structural gate.** The absence rows (a hand-rolled `import channels`
passes every present-path oracle and fails exactly the hint-match rows).
Negative control: inlining the hint at the call site passes all absence
oracles and fails the next floor-bump sweep (family item's gate to name).
- **Coupling.** None.
- **Freshness.** Target `a18c5001…` + `utils/imports.py` `291ecedd…`
(whole module) + `auth/sessions.py` `fad7feb8…` (guard + hint) +
`rest_framework/__init__.py` `45cf7b63…` (whole module) +
`middleware/debug_toolbar.py` `5360149b…` (guard body) +
`pyproject.toml` `9be86493…` (floor row) + `tests/test_routers.py`
`17842b60…` (absence-row titles).

### File-local records (no second definition after the matrix)

- **R1 - transport composition.** Host-outside-Origin-outside-Auth-outside-
URLRouter with `"http"` verbatim (C5, C6 - 1 each). Order and verbatimness
are each pinned by dedicated oracles (wrapper-order + http-identity rows,
bodies read). Trigger: a wrapper added/removed/reordered upstream.
Freshness: target only.
- **R2 - application gate.** Omission is Python's `TypeError` (required
parameter, deliberately); `None`/non-callable is `ConfigurationError`
carrying the 0.0.14-migration prose (C7 - 1). Trigger: a new usable shape.
Freshness: target only.
- **R3 - URL pattern gate.** Exact-type `str` rejection plus eager
`re.compile` turning malformed regexes into the same typed boundary, both
tails through F2 (C8 - 1). The `except BaseException` around compile is
fail-closed at construction (a display/compile-time escape must not pass a
route that never matches). Trigger: accepting compiled patterns.
Freshness: target only.
- **R4 - seam selector.** Exactly three shapes (`None` / consumer subclass
/ factory), class-before-callable order so a class never enters the factory
branch with a surprising keyword (C9 - 1). Trigger: a fourth shape.
Freshness: target only.
- **R5 - calling-convention pre-check.** `bind(schema=schema)` before the
call (a `TypeError` from inside a correct factory's body must not be
misdiagnosed), un-introspectable callables allowed through to be judged by
the call (C10 - 1). Single `signature.bind` site package-wide. Trigger: a
second calling convention. Freshness: target only.
- **R6 - factory return floor.** Callable-only mount check with no arity
probe (arity would falsely reject `*args` middleware, partials, and C-slot
`__call__`), coroutine addendum, own-exception passthrough (C11 - 1; F1
owns the disposal half). Trigger: construction-time conformance becoming
honestly checkable. Freshness: target only.
- **R7 - window combination rule.** Domain validation delegated to
`consumers.py::resolved_revalidation_window` by call; the positive-window-
with-injected-class combination rejected rather than silently ignored, with
`0.0`-with-class staying legal (C12 - 1). Trigger: the window ever
configuring injected classes. Freshness: target + `consumers.py`
`18f3ea16…` (default literal + contract shape).
- **R8 - lazy cache.** Double-checked `_ROUTER_CLASS` under
`_ROUTER_CLASS_LOCK`, eviction-drops-cache lifetime (module global, stated
at the slot), `__all__` listing the lazy name so star-import opts into the
guard (C13 - 1; J1 refuses the root twin). Trigger: a second lazy export.
Freshness: target only.
- **R9 - guard-error split.** `require_channels()` first, then per-half
breakage hints (channels pieces vs `strawberry.channels`), so a broken
install is never misreported as a missing one (C14 - 1). Trigger: a third
independently breakable half. Freshness: target only.

### J1 - routers `__getattr__` vs root `__getattr__` (rejection, not a family)

`routers.py::__getattr__` vs `django_strawberry_framework::__getattr__`.
Considered shared form: one lazy soft-export guard. Contract difference:
construct-one (single name, builder call, zero table) vs import-seven
(name-to-`(submodule, attr)` table plus `require_drf` plus
`import_module`/`getattr`); `__all__` lists the lazy name here (star-import
opts INTO the channels guard, oracle-pinned) while the root deliberately
omits all seven (star stays DRF-free) - opposite decisions, not one rule
with two spellings; this side memoizes the built class (double-checked
cache), the root never memoizes (each access re-fires the guard).
Reconsideration trigger: a second lazy router export (a table here), or the
root needing a constructed rather than importable symbol. Durable home: both
`__getattr__` docstrings (each already states its own `__all__`/memoization
contract) + this finding. The plan's `drf-soft-export-guard` row stays
`open` for its own members; this rejects only routers' membership.

### J2 - router class cache vs schema alias locks (rejection, not a family)

`routers.py::_ROUTER_CLASS` + `_ROUTER_CLASS_LOCK` vs
`schema.py::_ASYNC_MUTATION_LOCKS` + `_ASYNC_MUTATION_LOCKS_GUARD`.
Considered shared form: one `threading.Lock` cache. Contract difference: a
single lazily-built class slot with double-checked identity (plus the
barrier-concurrency oracle) vs a per-alias lock dictionary populated under
its guard - different stored shapes, different lookup keys, different
lifetimes (eviction-drops-cache vs process-lived). Reconsideration trigger:
a second single-slot lazy class, or the alias map collapsing to one slot.
Durable home: the `_ROUTER_CLASS` lifetime comment + this finding.

### J3 - construction synchrony vs the one sync boundary (rejection, not a family)

`routers.py::_factory_application`'s "construction cannot await" vs
`utils/querysets.py::run_in_one_sync_boundary`. Considered shared form: the
factory joins the one-boundary rule. Contract difference: no ORM, session,
or IO exists on this path (probe: no boundary import, no `QuerySet`), so
there is nothing to keep inside one `sync_to_async` hop - the constraint is
construction-time (no event loop exists to await on), not thread-affinity
(no awaits may interleave inside a transaction); the errors differ
(`ConfigurationError` vs `SyncMisuseError`) and the lifetimes differ (build
once vs per-operation). Checked per the item brief ("check don't inherit") -
not inherited. Reconsideration trigger: the router ever performing
ORM/session IO at construction. Durable home: the `_factory_application`
docstring's construction paragraph + `_ASYNC_FACTORY_HINT` + this finding.
The plan's `one-sync-boundary` row stays `open`; this rejects only a routers
membership that was never taken.

## Defects

None. Every claim checked while tracing held: all four consumer imports
consumed; the default flows by import, never respelled; both floors
interpolated, never re-typed; all six tails routed; the wrapper order and
http verbatimness match the docstrings; the selector's class-first order
matches its rationale; the pre-check's allow-through matches its docstring;
the return floor's no-arity-check rationale matches the rejection set; the
cache's eviction paragraph matches the slot shape; the 38 oracles pin each
seam (four bodies read). Three deliberately-narrow shapes were examined as
possible gaps and each is contracted, not missing: futures rejected without
cancellation (only coroutines warn - F1); factory own-exceptions un-
normalized (pinned by oracle - matrix axis 6b); `except Exception` (not
`BaseException`) around `inspect.signature` (only ordinary failures are
evidence-neutral - R5). No guard any contract requires is missing; the
concurrent-dirt pattern does not apply (target diff is empty).

(Worker 2) No production defect found on re-trace. One artifact prose
correction is recorded under `## Independent verification (Worker 2)`
(oracle-file test count: 38 stated vs 117 measured at the fingerprinted
blob) - prose only, not a production defect, verdict unaffected.

## Pending execution

None. The execution proofs (39-check read-only probe plus four read-only
sweep heredocs, commands in `### Challenges`) already ran green against the
shared tree; they mutate no source and open no database, so no workspace
copy was owed and no `__file__`/DB `NAME` record applies. No pytest was run
in the shared tree, per item rules; oracle bodies are `static-reviewed`
(four bodies read, 34 titles censused) and the final gate executes them. No
`FAKESHOP_SHARDED` or Postgres cell is owed: this artifact's
execution-verified claims (statement counts, import census,
absence/single-site facts, baseline diff, whole-tree byte populations)
touch no database, alias, or dialect decision (`inapplicable by
construction` - the target performs no query, opens no connection, and
branches on no alias or dialect).

## Judgment

Single-owner composition module with all shared rules consumed by name and
nothing to consolidate: two existing families reused as consumer/member
(F1, F2), one new guard family proposed (F3), nine file-local rules with
their proving challenges, three rejections with contract differences,
triggers, and homes. Zero edits; ready for verification.

## Implementation (Worker 1)

No production edits (file item; target CLEAN vs `03fd30aa`). Untracked
outputs owned by this item: `docs/dry/dry-file-routers.md` (this artifact)
and the read-only scratch probe
`docs/dry/temp-tests/dry-file-routers/probe_w1.py` (39 checks green; Worker
0 removes by explicit path after `verified`). Item-scoped diff: `git diff
03fd30aac42094527e2ace256be2617009c9af86 --
django_strawberry_framework/routers.py` is empty; concurrent dirt
(`django_strawberry_framework/connection.py`,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) untouched by
content attribution, never listed, never edited. No commit.

## Independent verification (Worker 2)

Own trace, re-derived from the target and package-wide greps before
reconciling with `## Findings` above. Instrument: own `ast.parse` count
(30, confirmed), own grep censuses below, and a fresh re-run of the
read-only probe (`uv run python
docs/dry/temp-tests/dry-file-routers/probe_w1.py` -> `39 checks, 0
failed`, re-executed by Worker 2 against the shared tree; no source
mutation, no DB, no pytest).

### Own rule derivation (counts + owners I would choose)

- **Awaitable inline member (1 site here).** `routers.py::_factory_application`
detects `inspect.iscoroutine(application)` then `application.close()`,
then raises `ConfigurationError`. Owner I choose:
`utils/querysets.py::_dispose_sync_awaitable` (close + cancel both arms;
verified both literals present there, coroutine-only here, no
`isfuture`/`iscancel` in target). The raise stays here: the owner's own
docstring reserves `SyncMisuseError` for sync ORM boundaries, a
construction seam speaks `ConfigurationError`. Reconciles with **F1**
(member, narrowness deliberate). Agree.
- **Tail consumers (6 call sites here).** Own grep: exactly 6
`describe_value(` lines (pattern-gate both arms, bind-failure tail,
received-value read + returned tail, selector tail). Owner I choose:
`exceptions.py::describe_value` (body + scope paragraph read; scope
already claims exactly this file's three factory/consumer rejections).
Package population: 11 files (schema 5, routers 6, list_field 3,
resource_policy 3, error_policy 2, policies 2, views/consumers/sessions/
debug 1 each, plus the definition). Reconciles with **F2** (consumer).
Agree.
- **Require-guard wrappers (4) + keyset-direct (2 calls, 1 hint).** Own
grep: `def require_channels` in routers.py + auth/sessions.py,
`def require_drf` in rest_framework/__init__.py,
`def require_debug_toolbar` in middleware/debug_toolbar.py - all four
bodies read, all four delegate to `require_optional_module` by name with
a per-feature hint, no hand-rolled pattern; `keyset.py::_cursor_crypto_types`
calls the primitive twice directly with one hint (read). Floors
`CHANNELS_FLOOR`/`STRAWBERRY_FLOOR` live beside the primitive and are
interpolated (never re-typed) into this file's three hints; second
written copies are the `pyproject.toml` rows. Owner I choose:
`utils/imports.py::require_optional_module`. Reconciles with **F3**
(NEW family `soft-dependency-require-guard`). Endorsed - see coherence
ruling below. Agree.
- **Composition (1 literal).** Host-outside-Origin-outside-Auth-outside-
URLRouter with `"http"` verbatim; order and verbatimness confirmed by
read. File-local (**R1**). Agree.
- **Application gate (1 predicate + hint).** Omission is Python's
`TypeError` (required parameter); `None`/non-callable is
`ConfigurationError` with the 0.0.14-migration prose. File-local
(**R2**). Agree.
- **URL-pattern gate (1 gate).** Exact-type `str` rejection + eager
`re.compile` mapping malformed regexes into the same typed boundary,
both tails through F2; `except BaseException` around compile is
fail-closed at construction. File-local (**R3**). Agree.
- **Seam selector (3 shapes).** `None` / consumer subclass / factory,
class-before-callable order verified by read. File-local (**R4**).
Agree.
- **Signature pre-check (1 site package-wide).** Own grep:
`signature.bind` occurs in exactly this file. `bind(schema=schema)`
before the call; un-introspectable callables allowed through (verified
`except Exception: return` arm). File-local (**R5**). Agree.
- **Return floor (1 floor).** Callable-only mount check, no arity probe
(rationale read: `*args` middleware, partials, C-slot `__call__`),
coroutine addendum, own-exception passthrough. File-local (**R6**;
disposal half is F1's). Agree.
- **Window combination (1 rejection + 1 delegation).** Domain delegated
to `consumers.py::resolved_revalidation_window` by call (body shape
read); positive-window-with-injected-class rejected, `0.0`-with-class
legal. File-local (**R7**). Agree.
- **Lazy cache (1 slot + 1 lock + 1 `__getattr__` arm).** Double-checked
`_ROUTER_CLASS` under `_ROUTER_CLASS_LOCK` (both `is not None` arms +
`with` verified); eviction-drops-cache lifetime stated at the slot;
`__all__` lists the lazy name so star-import opts into the guard
(oracle row exists, ~line 3168). File-local (**R8**). Agree.
- **Guard-error split (1 order + 1 hint pair).** `require_channels()`
first in the builder (verified before `from channels.auth`), then
per-half breakage hints (channels pieces vs `strawberry.channels`).
File-local (**R9**). Agree.
- **Lazy `__getattr__` vs root guard.** Own grep: 5 `def __getattr__`
sites (routers, root, plus conf.py / utils/permissions.py / consumers.py
methods, which are unrelated dunder delegations, not lazy-export
guards). The two lazy-export shapes differ in contract (construct-one
vs import-seven table; opposite `__all__` decisions, star opts IN here
vs stays DRF-free at root; builder cache here vs none at root). Refuse
shared family (**J1**). Agree.
- **Schema alias-lock vs router cache.** Single-slot class cache with
identity vs per-alias lock dict under its guard; different shapes, keys,
lifetimes (eviction-drops-cache vs process-lived). Refuse (**J2**).
Agree.
- **One-sync-boundary inheritance.** No ORM/session/IO on this path
(verified: no `sync_to_async`, no `run_in_one_sync_boundary`, no
`QuerySet` in target); the constraint is construction-time (no event
loop), not thread-affinity; errors differ (`ConfigurationError` vs
`SyncMisuseError`). Refuse (**J3**). Agree.

### Enumeration check (member by member vs own count)

Own `ast.Module.body` count: **30** (matches W1). Cross-foot: 1 module
docstring + 5 plain imports (future/inspect/re/threading/typing) + 3
from-imports + 1 `TYPE_CHECKING` if + 10 manifest/hint assigns
(`__all__` + 9 hint consts) + 1 annotated assign (`_ROUTER_CLASS`) + 1
lock assign + 8 defs = 30. Nested census: 1 factory-nested class
(`DjangoGraphQLProtocolRouter`) with 1 method (`__init__`, 3
positional + 3 keyword-only params incl. `self` = 6 names) - matches W1
and the probe's `nested-class-one` / `init-params` checks, and own read
of the signature. W1's table rows 0-29 account for every member: 0
projection, 1-5 + 9 machinery, 6-8 consumers (R1/R7, F2, F3), 10-29
hints/cache/defs each homed (R2-R9, F1-F3, J1). No member unassigned.
Agree.

### Matrix vs real surface

1. Cross-flavor: swept by own greps (`callable(` per-seam shapes differ;
`re.compile` 5 files split grammar-decode vs route-validation;
`signature.bind` single-file). Discharged. Agree.
2. Sync/async twins: zero `async def` in target (probe + own read);
the one sync-shaped rule is deliberate negative space (construction
cannot await; J3 refuses inheritance). No pair exists. Agree.
3. Derived knowledge: default by import (no second `= 0.0` literal -
probe + own read), floors interpolated (no `>=digit` literal), window
domain delegated, Host matching stays Django's. No respelling. Agree.
4. Round-trip: no encode/decode grammar; builder/entry are
synchronized pair not inverses; factory invoke/return-validate are two
phases of one seam, one error type. Nothing to pair. Agree.
5. Other media: oracles live in `tests/test_routers.py` (independence
checked - no `describe_value`/`require_optional_module` import to build
expectations; the `_DEFAULT_REVALIDATION_WINDOW == 0.0` row asserts a
literal, pinned bodies for the coroutine-close, http-identity,
star-import, and barrier-concurrency rows); projections are the module/
class/function docstrings, verified against bodies. Fakeshop mounts no
WebSocket endpoint, so the package tier is the strongest reachable -
stated honestly. Agree in substance; one prose correction below.
6. Omission: the three narrow shapes (futures rejected un-cancelled,
factory own-exceptions un-normalized, un-introspectables allowed
through) are each contracted in the docstring and pinned by oracle
rows. No missing guard; no defect. Agree.

Prose correction (Worker 2, non-blocking): the artifact states a
"38-test census" / "38 rows" for `tests/test_routers.py`. Own AST count
at the fingerprinted blob (`17842b60`, re-hashed match - see below) is
**117 top-level test functions** (93 async + 24 sync test defs; 18
helper classes excluded). The four bodies W1 names all exist under
their stated names, and the key seam rows are real, so coverage of the
argument is unaffected - but Worker 0 should amend "38" to the measured
117 (titles censused in substance for the seam rows) rather than carry
the number into `## Outcomes`.

### Counts + roles; oracles

C1-C15 definition counts re-derived: C1 1 at the owner; C2 1 at the
renderer; C3 1 at the primitive; C4 2 writes (owner const + pyproject
row, hints 0); C5-C14 1 each file-local; C15 0 refused. Consumers,
oracles, projections listed, never counted - confirmed. No oracle
rewritten (zero production edits; test file untouched, blob still
`17842b60`). Agree.

### Equivalence (principle 8)

Zero-edit item: no behavior to preserve across a change. The only
observable claims are census/identity/absence facts, all
`execution-verified` by the re-run probe (39/39). Oracle bodies remain
`static-reviewed`; the final gate executes them. Agree.

### Zero-edit + coverage/assignment

Item-scoped diff confirmed empty by Worker 2 (`git diff
03fd30aac42094527e2ace256be2617009c9af86 --
django_strawberry_framework/routers.py` = 0 bytes; `routers.py` absent
from `git status --short`). All 30 members homed; no consolidation owed
by a file item; F1/F2 route to existing families, F3 proposed for the
index. Validated.

### F3-vs-J1 coherence ruling (endorsed)

W1 both refuses J1 and names F3, which is coherent rather than
double-counting: they are different rules with different owners and
different change challenges. F3 = the RAISING primitive
(`require_optional_module`: absence -> hinted `ImportError`, presence ->
module unchanged, no memoization) with per-feature hint strings
single-sited at each wrapper; change challenge "absence needs a new
signal" moves exactly 1 definition. J1 = the lazy-EXPORT mechanism
shape (table + `require_drf` + import/getattr vs single-name builder
call; opposite `__all__` decisions; builder cache vs none); its
challenge is "a second lazy export", a different axis. Folding F3 into
the plan's `drf-soft-export-guard` (owner `__init__.py::_DRF_SOFT_EXPORTS`,
DRF-specific table + root timing + star-stays-DRF-free) would couple
independent domains (channels/auth/DRF/toolbar/crypto) and reverse the
dependency (routers cannot import the root for its machinery); principle
7 picks `utils/imports.py` as the narrowest importable owner. Keep F3
separate; keep J1 refused. Worker 0 should index F3 as a NEW family
row (exact lines in the verdict report).

### Rejections

J1/J2/J3 each carry considered-shared-form + contract difference +
reconsideration trigger + durable home (both `__getattr__` docstrings /
`_ROUTER_CLASS` lifetime comment / `_factory_application` docstring +
finding). `drf-soft-export-guard` and `one-sync-boundary` plan rows
correctly stay `open` for their own members. Agree.

### Freshness re-hashes (Worker 2)

`routers.py a18c5001` match; `utils/imports.py 291ecedd` match;
`exceptions.py e06b0b7f` match; `consumers.py 18f3ea16` match;
`auth/sessions.py fad7feb8` match; `rest_framework/__init__.py 45cf7b63`
match; `middleware/debug_toolbar.py 5360149b` match; `pyproject.toml
9be86493` match; `tests/test_routers.py 17842b60` match. No fingerprint
went stale. (`__init__.py` root-guard bodies re-read for J1; no blob
pinned by W1 there, nothing to stale.)

### Structural gates (negative controls judged plausible)

F1 `cr_frame is None` row: deleting `close()` passes message-shape
oracles, fails exactly that row. F2 hostile-repr row: `f"{value!r}"`
passes small-value oracles, fails exactly that row (the `10**10000`
chaining shape is the load-bearing case). F3 absence/hint rows: a
hand-rolled `import channels` passes present-path oracles, fails
exactly the hint-match rows. Execution of these controls belongs to the
holding family items (file item owes none). `## Pending execution`
correctly absent (read-only probes already ran green; no
execution-deferred proof; target performs no query/connection/alias
decision so no sharded/Postgres cell is owed - `inapplicable by
construction`, endorsed). Coupling `None` everywhere: correct, no
landing couples findings.

### AGENTS.md prose check

Item diff empty, so no production/test prose to check. Artifact: no
process provenance, no `feedback` mention, no `path:NN` line citations
(grep-clean), `path::Symbol` citations throughout, test tier stated at
the mandated tier with the fakeshop-gap sentence, no commit, concurrent
dirt (`connection.py`, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) untouched - Worker 2 opened `connection.py`'s
neighbourhood only via read-only grep, never edited. One docs-only
edit (this artifact, the item's own untracked output): no `ruff`
run - `ruff format`/`check --fix` operate on Python and a repo-wide
`--fix` would risk touching the concurrent dirt above; nothing in this
change can violate them. Pass.

### Judgment (Worker 2)

Verified. Single-owner composition module; shared rules consumed by
name (F1 member, F2 consumer, F3 proposed consumer-of-new-family);
R1-R9 file-local with proving challenges; J1-J3 refused with
differences, triggers, homes. Zero edits, zero pending execution, zero
defects. The single prose correction (38 -> 117 oracle count) is for
Worker 0 to amend in the artifact and keep out of `## Outcomes`.
