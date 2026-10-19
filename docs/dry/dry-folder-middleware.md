# DRY review: `middleware/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

Zero-edit CONFIRM. The folder's 16 unassigned rules are each
single-owned at current bytes (C1–C26 all count ≤1, each with
its proving challenge); the 12 standing index rows holding
folder members re-derive to their recorded verdicts (FC-1..FC-9,
including the e9 open family whose hunt block persists); one
cross-artifact convergence holds (FC-10); 8 plausible merges
dissolve on contract differences with triggers (FR-1..FR-8); 6
tree-falsified record details flagged for closeout homing
(FF-1..FF-6, no row reopened, nothing re-applied). 0 new
defects; 1 homed defect persists (D-W2-1). 16 index rows named
below supersede the never-transcribed member proposals.

HEAD `23b5f421` (detached, intended).
`ITEM_BASELINE=9d22e2203e2d748966c0e9fb5b12c3b642dbba17`
(before copy in warm slot-1). Blobs are `git hash-object` (WT),
`git show HEAD:<path> | git hash-object --stdin` (HEAD), `git show
ITEM_BASELINE:<path> | git hash-object --stdin` (BASE), short-8.
Status count 529 at dispatch; this untracked artifact is the +1.

| File | WT | HEAD | BASE | Artifact-era |
|---|---|---|---|---|
| `middleware/__init__.py` | `6e1b64ca` | `6e1b64ca` | `6e1b64ca` | `6e1b64ca` (identical) |
| `middleware/debug_toolbar.py` | `301e43dc` | `63b8765e` | `301e43dc` | `5360149b` |
| `middleware/request_body.py` | `7422cee9` | `e038bdd1` | `7422cee9` | `e6e32e78` |

Attribution by diff content. The WT-vs-HEAD deltas on both
leaves are the hunt's truth migration, nothing else:
`truth.static_attr` / `is_type` / `is_instance` / `is_subclass` /
`name` reads plus their prose, and two deleted broad `except
Exception` guards in `request_body.py` (mount handoff,
recognition wrapper) — concurrent work, untouched, and any
consolidation touching those lines would be blocked-on-hunt
(none confirmed). The HEAD drift since the artifact era is the
maintainer's committed typing series (`b20277fe`, `5c3496e0`,
`849f67bc`, `fef11e64`, `d7e5c094`, `0c76625a`, `19ad615c`,
`899cb35b`, `2915250d`): `-> ModuleType` returns, the
`_IS_GRAPHIQL` constant, `object` annotations, `@override`,
`iscoroutinefunction` → `is_marked_coroutine_function` — all
behavior-neutral at the bodies this item judges. No `## Owned
changes` row covers the folder. The marker file is byte-identical
across all four states.

What the folder owns. The marker (`__init__.py`, 11 lines) owns
import-cleanliness plus the no-re-export dotted-path surface
posture. The toolbar leaf (`debug_toolbar.py`, 316 lines) owns
the server-side HTTP+HTML toolbar surface: soft-dep guard +
app gate + import-time ordering, `BaseView` tagging,
`debugToolbar` payload build, two-shape response mutation,
dotted-path identity. The boundary leaf (`request_body.py`, 364
lines) owns the chain position of the request-body boundary:
publish twin, boundary-run hook, package-view recognition,
ordering audit, setup fidelity, refusal render, leaf manifest.
It defines no protocol name and no policy — those live in
[ordering][ordering] and [views][views].

Index coverage re-derived, not inherited. Zero rows carry a
`File middleware/*` holding item and zero hits for any of the 16
proposed family spellings: the member artifacts'
[file-init][file-init] F1/F2, [file-toolbar][file-toolbar] F2–F8,
[file-boundary][file-boundary] L1–L7 were never transcribed
(FF-1). Twelve existing rows hold folder members: 2
consolidated (`request-body-boundary-ordering`,
`soft-dependency-require-guard`), 1 open (`prepared-view-handoff-shape`,
blocked-on-hunt e9), 9 rejected (boundary-vs-toolbar read,
shared-except J1, measurement-colocated J6, 2 rest-framework
guard rows, 2 leaf-vs-sibling-manifest rows,
execution-mode-fact-vs-shape, extensions-debug-surface-split).
Each is re-checked under FC-1..FC-9.

Connected sources read whole or by cited body at WT bytes, with
WT/HEAD short blobs: [ordering][ordering] `f91ccd73`/`f91ccd73`
(clean), [views][views] `72ec3e2d`/`0492167d` (dirt confined to
lines 100–217, clear of the boundary halves at 538–663),
[request-body-lib][request-body-lib] `5672658f`/`99312893`,
[imports][imports] `3ea52b16`/`3ea52b16` (clean),
[typing-util][typing-util] `b7e69600`/`3a5dae39`,
[exceptions][exceptions] `9c02e960`/`f3793258`,
[ext-debug][ext-debug] `7cf521f9`/`78e662f9`,
[rf-init][rf-init] `0fff4c42`/`0fff4c42` (clean),
[routers][routers] `d354218c`/`f8ec8c98`,
[sessions][sessions] `6e5fadb7`/`1dc65564`, package root
`b688e2fa`/`b688e2fa` (clean), [toolbar-tests][toolbar-tests]
`f322d953`/`f322d953` (clean), `tests/test_views.py`
`6461503f`/`cb374adf`, [toolbar-api][toolbar-api]
`afb91332`/`afb91332` (clean), `test_transport_api.py`
`ce099d5a`/`1a6a5808`, [settings][settings] `aa739c9c`/`aa739c9c`
(clean), [spec-042][spec-042] `362e1a40`/`362e1a40` (clean),
`pyproject.toml` `21cccc6d`/`f7622bc7`, [tree][tree]
`175d6834`/`a97e2187`, [tree-render][tree-render]
`240d2ba8`/`240d2ba8` (clean). Package-wide mechanism sweeps ran
over all 121 `django_strawberry_framework/**/*.py` (the member
artifacts' 117-file figure is artifact-era, FF-6).

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched. The toolbar leaf's
   HTTP+HTML surface vs the debug extension's in-response surface
   re-derived from both bodies (FC-4, rejected); the two
   `process_view` hooks compared by contract (FR-1, rejected);
   the guard wrapper against its three twins (FC-3, member);
   the marker against all 13 sibling leaves (FC-6, rejected).
   No flavor policy hides here. Discharged.
2. Sync/async twins: searched. One colored pair exists under
   the folder: `__call__` / `__acall__` in `request_body.py`,
   mechanism-forced (C13 refused by construction — a shared sync
   body resets the publish mark in `finally` before the
   downstream coroutine resolves). The toolbar leaf holds 0
   `async def` / 0 `await`, no `__call__` / `__acall__`, and
   inherits both colors from the stock chain (FR-5, rejected).
   `process_view` is one sync body on both leaves serving both
   transports. Discharged.
3. Derived rather than repeated knowledge: searched. Five
   protocol literals live in exactly one file ([ordering][ordering]:
   `graphql_request_body_boundary*` has no second file); the
   boundary method name is read through `_BOUNDARY_METHOD` at
   probe + invoke with zero literals here; `_is_graphiql` is
   spelled once (the `_IS_GRAPHIQL` binding, FF-4); the floor
   trio agrees (`7.0.0` in hint, test literal, dev-group row);
   media type derived once per `_postprocess` call; the audit
   compares classes, never dotted-path strings; the mount token
   is identity, never derived. Discharged.
4. Inverse / round-trip pairs: searched. Four stamp/read pairs
   single-owned at [ordering][ordering] with halves split across
   modules by construction (ENFORCED, PREPARED_VIEW, channel,
   MARKER/MOUNT) — this folder holds three write halves + one
   read half, all composing by name (FC-1). Payload
   decode/build vs re-encode live under one leaf owner.
   Discharged.
5. Contracts restated in another medium: counted 16
   definitions; everything else classified. Contract sources:
   [spec-042][spec-042] Decisions 3/4/5 (toolbar surface,
   leaf shape, guard shape — re-read verbatim), spec-046
   Decisions 7/9/18 (boundary policy + chain ordering),
   [ordering][ordering] module prose (protocol). Oracles: the
   toolbar package tier (71 tests, run green this item) + live
   tier, the boundary package tier (by-name imports re-read) +
   live shipped-chain rows — all independent (re-typed
   literals, behavior reads, never owner imports for
   expectations). Projections: module/method docstrings, marker
   prose, [tree][tree] folder lines (rendered without import),
   glossary anchors, README chain snippet, shipped settings
   chain. No medium holds an independently maintained copy.
   Discharged.
6. Enforcement by omission: searched. Boundary family
   {package, foreign} × {sync, async} × {no-CSRF, misordered,
   duplicate} all covered; decline-untouched is the contract
   (pinned by oracles), not a gap. Toolbar guards all present
   (import guard, app gate, non-class guard, 4 payload bails,
   streaming/encoding/tag/media/status/introspection/length
   gates). The `__all__` asymmetry (boundary leaf has one,
   toolbar leaf does not) carries no contract source requiring
   uniformity — [spec-042][spec-042] Decision 3 blesses the
   toolbar's absence (FR-3). Absence of a shared sentinel
   driver across 19 `object()` sites is per-site contract, not
   a gap (FR-4). No member lacks a guard its contract
   requires. Discharged.

### Challenges

Each change posited against the rule's own variation axes at
current bytes; the count is authoritative definitions only.
Consumers, oracles, projections listed, never counted. Line
numbers are WT.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | marker wording | reword the import-clean paragraph | **1** (marker docstring; [tree][tree] lines re-render as projection) | file-local |
| C2 | marker violation | add an eager leaf import | **1** here (trips the cleanliness oracle) | file-local, load-bearing |
| C3 | marker omission | re-export either leaf | **1** here (Decision 3 prose + leaf guard move not at all) | file-local |
| C4 | omission lift | lift Decision 3 (root-export the toolbar) | **0** here (root + leaf guard move; this prose follows) | independent |
| C5 | hint text/floor | reword hint / floor `7.0.0` → `8.0.0` | **1** (the hint string; test literal + dev row follow gated) | file-local |
| C6 | app gate | reword hint / retime to call time | **1** (the `if` block + string) | file-local |
| C7 | guard order | move the guard from import into each method | **1** (bare call + sub-guard block reorder together) | file-local |
| C8 | tag target/guard | narrow to `GraphQLView` / drop the non-class guard | **1** (toolbar `process_view`; engine base untouched) | file-local |
| C9 | payload bail/key/skip/title | fifth bail / rename key / unskip panel / title policy | **1** each (`_get_payload`; re-encode is opaque) | file-local |
| C10 | postprocess skip/encoding/bridge/length | rename skip / lift encoding bail / repath template / unconditional length | **1** each (`_postprocess`; the two length sites are one rule) | file-local |
| C11 | protocol mark | rename one mark string / sixth per-request fact | **1** (owner constant; middleware follows) | independent here |
| C12 | method name | probe one name, invoke another / rename the method | **1** new owner name / **1** name + **1** referent, **0** here | independent here |
| C13 | publish twin | one shared body for `__call__`/`__acall__` | refused by mechanism (sync `finally` resets pre-await) | intentional separation |
| C14 | hook order | skip the ENFORCED stamp / run boundary without `setup` | **1** body here (refused by idempotence + request-local contracts) | file-local |
| C15 | recognition | stop at bookkeeping / probe the instance / broaden `TypeError` | **1** body here (each refused: 500s, foreign `__init__`, cap's own errors) | file-local |
| C16 | audit | compare dotted paths / judge every entry | **1** body here (each refused: subclass evasion, first-entry semantics) | file-local |
| C17 | refusal render | JSON envelope instead of `text/plain` | **1** body here (refused: non-attributability contract) | file-local |
| C18 | leaf manifest | add a second public name | **1** (the tuple) | file-local |
| C19 | hook merge | one shared `process_view` rule for both leaves | rejected: tag vs boundary-run (FR-1) | no second definition |
| C20 | read merge | one shared `view_class`-read rule | rejected: tag input vs recognition step; both WT lines hunt-dirtied (FR-2) | no second definition |
| C21 | manifest merge | unify the `__all__` posture | rejected: Decision 3 blesses the asymmetry (FR-3) | no second definition |
| C22 | sentinel merge | one shared sentinel rule | rejected: 19 sites, distinct contracts (FR-4) | no second definition |
| C23 | guard membership | second optional dep on the toolbar leaf | **1** here (new wrapper + hint; primitive + twins untouched) | member, not copy |
| C24 | tag spelling | rename the `_is_graphiql` attribute | **1** (`_IS_GRAPHIQL`; tests follow as oracles) | file-local |
| C25 | class identity | rename either middleware class (keep the dotted path) | **1** here (the class statement; settings strings follow as consumers) | file-local |
| C26 | setup fidelity | call `setup` unconditionally | **1** body here (refused: 500s minimal foreign callbacks) | file-local |

Execution this item: one authorized focused run —
`heavy uv run pytest -n0 tests/middleware/test_debug_toolbar.py
--no-cov -q` → 71 passed. All other claims are
`static-reviewed` against the pinned blobs plus the permanent
oracle tiers, which execute the behavior every suite run.
Read-only probes (non-mutating, shared tree): `ast` census,
whole-package `rg` sweeps per population (each published figure
states its pattern + population), blob-to-blob diffs for drift
attribution. No `docs/dry/temp-tests/` scratch; no workspace
copy was needed (zero source-mutating proofs).

## Findings

### Single-ownership confirmations (the unassigned remainder)

Each rule below was file-local in its member artifact and is
re-derived here at current bytes with a fresh challenge count;
all count ≤1, so each stays file-local. The `Row` column points
at the `## Index rows for Worker-0` table, which supersedes the
never-transcribed member proposals (FF-1).

| # | Rule | Owner (unchanged) | Challenge | Drift since member artifact |
|---|---|---|---|---|
| 1 | `middleware-import-clean-marker` | marker file | C1, C2 → 1 | none (blob identical) |
| 2 | `middleware-no-reexport-opt-in-surface` | spec-042 D3; leaf + root mechanism | C3 → 1, C4/C7-analog → 0 | none (blob identical) |
| 3 | `debug-toolbar-install-hint-and-floor-gate` | `_DEBUG_TOOLBAR_INSTALL_HINT` | C5 → 1 | typing only; `-> ModuleType` converged |
| 4 | `debug-toolbar-installed-apps-gate` | the `is_installed` block | C6 → 1 | none (body identical) |
| 5 | `debug-toolbar-import-time-guard-ordering` | leaf module body | C7 → 1 | import list re-sorted by typing series |
| 6 | `debug-toolbar-view-detection-guard` | toolbar `process_view` | C8 → 1 | hunt: `truth.static_attr`/`is_subclass` at WT |
| 7 | `debug-toolbar-payload-builder-bails` | `_get_payload` | C9 → 1 each | typing annotations only |
| 8 | `debug-toolbar-postprocess-branches` | `_postprocess` | C10 → 1 each | `_IS_GRAPHIQL` read (FF-4); `@override` added |
| 9 | `debug-toolbar-dotted-path-identity` | the class statement | C25 → 1 | none (identity unchanged) |
| 10 | `middleware-publish-twin` | `__call__` + `__acall__` | C13 refused by mechanism | `is_marked_coroutine_function` (committed) |
| 11 | `boundary-run-hook` | boundary `process_view` | C14 → 1 | hunt: mount read + `truth.name` at WT |
| 12 | `package-view-recognition` | `_package_view_instance` | C15 → 1 | hunt: truthful reads, guards deleted, at WT |
| 13 | `ordering-audit` | `_require_boundary_before_csrf` | C16 → 1 | hunt: `truth.is_type`/`is_subclass` at WT |
| 14 | `setup-lifecycle-fidelity` | `_NO_SETUP` + setup block | C26 → 1 | `setup: Any` annotation (committed) |
| 15 | `refusal-render` | the `except HTTPException` arm | C17 → 1 | none (arm identical; sole `HttpResponse(` site) |
| 16 | `middleware-leaf-manifest` | `__all__` | C18 → 1 | none (tuple identical) |

Behavioral proof for all 16: `static-reviewed` against the
pinned blobs; each rule's permanent oracles (named under
Matrix axis 5) execute every suite run and reject the
wrong result its challenge posits (violation → oracle red;
lift → 0 here). Structural gates are those pre-existing
oracles; no new gate is owed (a hand copy of any single-owned
body passes every behavior oracle and fails only a census the
family item would own — and every census re-run here returns
1). Coupling: none. Freshness: target blobs per the System
trace table; connected blobs listed there; searched population
121 package `.py` + both test tiers + shipped settings.

### FC-1 — `request-body-boundary-ordering` (consolidated, CONFIRM)

- **Contract + variation.** Five protocol names + channel +
  exemption live once in [ordering][ordering]; the boundary
  leaf publishes two marks per request and reads two off the
  callback; the method name is probed + invoked through the
  constant.
- **Sites + roles.** *Definitions*: the six bindings at the
  owner (unchanged). *Consumers (this folder)*: the six-name
  import + ENFORCED/PREPARED_VIEW writes + MOUNT/MARKER reads
  + probe/invoke + twin publish (all in `request_body.py`).
  Zero protocol literals in this folder (the
  `graphql_request_body_boundary*` prefix occurs in exactly one
  package file, the owner). *Oracles*: by-name imports in
  `tests/test_views.py` re-read (lines 93–107); live
  shipped-chain rows present.
- **Challenges.** C11, C12 → 1 owner definition each, 0 here.
- **Owner + lifetime.** Unchanged: [ordering][ordering].
- **Behavioral proof.** `static-reviewed`. Rejects "a call
  site restates a protocol string" (prefix census: 1 file).
- **Structural gate.** Pre-existing by-name oracles; no new
  gate owed. Coupling: none. Migration: none.
- **Freshness.** Owner `f91ccd73` clean; leaf WT `7422cee9`.

### FC-2 — `prepared-view-handoff-shape` (open, block persists, CONFIRM)

- **Contract + variation.** The `(mount, view)` payload
  grammar spelled at the pack site (`request_body.py:249–252`)
  and the unpack site (`views.py:584–588`): e9 CONFIRMED
  count-2 with owner [ordering][ordering] via pack + consume
  helpers, blocked-on-hunt, verified pending execution.
- **Re-check from this side.** Pack half at WT reads the
  mount through `truth.static_attr` (hunt dirt on the exact
  lines the migration must rewrite); consume half unchanged
  (token check + `delattr`). The e9 block assessment
  (unlandable, not partially landable) still holds: touching
  the pack lines is touching hunt dirt.
- **Challenges.** e9 C1 count 2 stands; no new challenge run
  (re-derivation, not re-litigation).
- **Behavioral proof.** `static-reviewed`. Migration: none
  (blocked). Coupling: the e9 family item owns the landing.
- **Freshness.** Leaf WT `7422cee9`; views WT `72ec3e2d`
  (dirt clear of the consume half).

### FC-3 — `soft-dependency-require-guard` (consolidated f34, CONFIRM)

- **Contract + variation.** One raising primitive
  ([imports][imports]`::require_optional_module`), four
  one-line wrapper declarations, keyset + root composing
  directly, five single-sited hints.
- **Re-check from this side.** The toolbar wrapper is still
  one line delegating with its own module name + hint
  (`debug_toolbar.py:118`); all four wrappers now return
  `-> ModuleType` (committed typing convergence, verified at
  [rf-init][rf-init]:39, [routers][routers]:239,
  [sessions][sessions]:118); both `_HINT` strings single-sited;
  floor trio agrees (`7.0.0` × 3); bare call + sub-guard
  imports still ordered (C7 → 1).
- **Challenges.** C5, C7 → 1; C23 → 1 here (member, not copy).
- **Owner + lifetime.** Unchanged: the primitive. Migration:
  none. Behavioral proof: `static-reviewed` + the 71 green
  oracles run this item (absence/broken/guard/floor rows
  among them). Coupling: none.
- **Freshness.** Leaf WT `301e43dc`; primitive `3ea52b16`
  clean; wrappers per System trace.

### FC-4 — `extensions-debug-surface-split` (rejected, CONFIRM)

Re-derived from the toolbar side: the leaf injects a
`debugToolbar` payload into tagged HTTP responses over the
middleware chain (toolbar opt-in at leaf import, stock
panels/history, `IntrospectionQuery` skip); the extension
publishes per-operation SQL + exceptions INSIDE the GraphQL
response extensions map under `debug` (engine seam,
fail-closed under `DEBUG` + `allow_unsafe_production`
acknowledgement, bounded text, no soft dep — re-read at
[ext-debug][ext-debug]). Transport, key, gating, payload all
differ; unifying couples the response contract to the
toolbar's presence. Trigger unfired (no one switch drives
both). Durable home: this clause + the standing row.

### FC-5 — boundary recognition vs toolbar `view_class` read (rejected, CONFIRM)

Re-derived at WT: the boundary read feeds exact-mount
recognition ending in construction + a boundary run (MARKER →
bookkeeping → callable probe → build); the toolbar read feeds
a boolean tag (`is_subclass(view, BaseView)`) with no
construction and no chain. Same hook vocabulary, opposite
contracts — posit a cap-limit change → only the boundary
side moves (C14); posit a detection-target change → only the
toolbar side moves (C8). Note: both WT read lines are
`truth.static_attr(view_func, "view_class", None)` — identical
spelling imposed by the same concurrent hunt edit, which
changes nothing about the contracts and would block any
merge regardless. Trigger (one hook owning tagging +
enforcement) unfired. Durable home: this clause + each
method's docstring + the standing row.

### FC-6 — leaf-vs-sibling-manifest rejections (CONFIRM, both rows)

The marker still binds nothing (blob identical): no manifest
table exists here to unify with any eager leaf's, and the
rest-framework guard-only posture is a different rule (a
guard call vs an absence). Both triggers unfired. Durable
home: the standing rows ([file-types][file-types] R2,
[file-utils][file-utils] R2); no row edit.

### FC-7 — `execution-mode-fact-vs-shape-classification` (rejected, CONFIRM)

The boundary leaf consumes
[typing-util][typing-util]`::is_marked_coroutine_function` by
name at exactly two call sites (`__init__` mark,
`__call__` dispatch); the `bool(...)` wrap + comment is
consumer hygiene against TypeGuard narrowing, not a second
classifier. No execution-mode fact is derived here. Trigger
unfired. Durable home: the standing row.

### FC-8 — rest-framework guard rows (rejected, CONFIRM)

Both rejections converge on the f34 shape: four wrappers are
declarations over one primitive, not copies (FC-3 re-verified
bodies + hints + floors). The return-idiom row's subject
(`-> ModuleType` on every wrapper, committed) now holds
uniformly. No second site; triggers unfired. No row edit.

### FC-9 — J1 shared-except + J6 measurement-colocated (rejected, CONFIRM)

J1: the toolbar's `except Exception` (operationName degrade,
upstream-verbatim) and the boundary's `except HTTPException`
/ `except TypeError` arms are per-site contracts, not a
shared driver — and the boundary's two broad guards are
deleted at WT by hunt dirt (present at HEAD), so the J1
files-covered population needs a closeout refresh either way
(FF-2). Verdict unaffected: no shared driver exists at any
state. J6: measurement still lives in
[request-body-lib][request-body-lib] + [views][views]; this
folder invokes by name and translates the refusal (zero
measurement tokens at WT — the only `_body` hit is the
module's own dotted path in its docstring). Durable home:
the standing rows.

### FC-10 — management FR-1 convergence (CONFIRM)

[folder-mgmt][folder-mgmt] FR-1 rejects the
marker merge from the management side (discovery convention
vs import-cleanliness/opt-in; trigger: a shared
marker-posture driver or one grammar). Converged from this
side: no such driver exists (each marker is its own
docstring), and positing dropping the toolbar soft-dep moves
only this marker (C1/C5 vs management C2 counting 0 here).
Trigger unfired. No row edit either side.

### FR-1 — the two `process_view` hooks (REJECTED, folder-new)

Considered: one shared `process_view` rule (same Django hook
name, same `def process_view` spelling, exactly two
package-wide). Contract difference: the boundary hook runs a
package view's body cap + CSRF ordering from the chain
(guard → recognition → setup → invoke → refuse → handoff →
stamp); the toolbar hook tags `_is_graphiql` via
engine-owned `BaseView` and chains to nothing. C19 moves one
side per change; the signatures differ accordingly (the
boundary names `view_args`/`view_kwargs` because it forwards
them to `setup()`; the toolbar ignores them). Trigger: a
single hook owning both tagging and boundary enforcement.
Durable home: this clause.

### FR-2 — the two `view_class` reads (REJECTED, folder-new)

Considered: one shared read rule (identical WT spelling
`truth.static_attr(view_func, "view_class", None)` in both
leaves; identical HEAD spelling `getattr(view_func,
"view_class", None)` before that). Contract difference: the
toolbar read answers "tag this request?" and its answer is
final; the boundary read is step two of a five-step
recognition ending at construction, whose answer is
provisional until the probe + build succeed. C20 moves one
side per change. Both WT lines are hunt dirt in any case.
Trigger: the tag becoming an input to the recognition (or
vice versa). Durable home: this clause.

### FR-3 — the `__all__` asymmetry (REJECTED, folder-new)

Considered: unifying the manifest posture (boundary leaf
exports exactly its class; toolbar leaf has no `__all__`).
Contract difference: the boundary `__all__` is the leaf's own
import surface for by-name oracle imports; the toolbar's
surface is the dotted settings string plus a module global
that needs "no `__all__` gymnastics" per [spec-042][spec-042]
Decision 3. No contract source requires uniformity, and the
star-import oracle passes either way. Trigger: a decision
that every leaf owns an `__all__`. Durable home: this clause.

### FR-4 — `_NO_SETUP` vs package `object()` sentinels (REJECTED, folder-new)

Considered: one shared sentinel rule (19 `= object()`
bindings package-wide, pattern ``=\s*object\(\)``: `_ABSENT` × 4
(mutations/fields, forms/sets, truth, field_meta), plus
`_MISSING`, `_LIVE_UNSET`, `_META_ABSENT`, `_ATTR_MISSING`,
`_ID_NOT_CACHED`, `_FK_ELISION_UNSAFE`,
`_MISSING_CLASS_MEMBER`, `_OMITTED`, `_OVERSIZED`,
`_NOT_SCALAR`, `MISSING`, two lowercase `missing` locals, the
views mount token, and `_NO_SETUP`).
Contract difference: each sentinel's meaning is its site's
contract (`_NO_SETUP` = "no Django setup lifecycle" vs
"shadows setup with a non-callable" — a setup-fidelity
distinction no other site shares). Posit changing one
meaning → the other 18 do not move (C22). Trigger: two
sites coming to share one absence contract. Durable home:
this clause.

### FR-5 — publish twin vs inherited async chain (REJECTED, folder-new)

Considered: sharing the color split (boundary leaf: explicit
`__call__`/`__acall__` pair; toolbar leaf: sync-only
overrides served in both colors by the stock chain).
Contract difference: the boundary pair exists because its
reset must happen after the downstream response exists (C13
refused by mechanism); the toolbar pair does not exist
because nothing there awaits — async support is inherited,
not doubled. There is no second twin to share with.
Trigger: queryset execution (or any await) inside a toolbar
override. Durable home: this clause.

### FR-6 — per-leaf hint strings (REJECTED, folder-new)

Considered: one shared hint rule (`_MISORDERED_MIDDLEWARE_MESSAGE`
vs `_DEBUG_TOOLBAR_INSTALL_HINT` / `_DEBUG_TOOLBAR_APP_HINT`).
Contract difference: a chain-ordering `ConfigurationError`
text vs an install hint vs a settings-error hint — different
failures, different audiences, different exception types
(C5 vs C6 vs C16 each move one string). Trigger: a shared
message grammar across leaves. Durable home: this clause.

### FR-7 — request-attribute read shape (REJECTED, folder-new)

Considered: one shared "read a request flag" rule
(`getattr(request, _BOUNDARY_ENFORCED, False)` vs
`getattr(request, _IS_GRAPHIQL, False)`). Contract difference:
a cross-module protocol stamp with one writer and two
readers vs a module-private tag with one writer and one
reader; posit renaming either attribute → the other does
not move (C24 counts 1). Same builtin, not the same rule.
Trigger: the tag joining the ordering protocol. Durable
home: this clause.

### FR-8 — refusal render vs dispatch translation (REJECTED, folder-new)

Considered: one package-owned render rule (the middleware's
`HttpResponse(reason, status, text/plain)` vs upstream
`dispatch`'s identical translation). Not package duplication:
the shape's owner is upstream (cross_web/strawberry
`dispatch`); the middleware deliberately produces the same
bytes so the wire shape does not depend on which side of the
CSRF check refused (C17, refused by the non-attributability
contract). One rule read twice, externally owned. Trigger:
vendoring the dispatch translation in-package. Durable home:
this clause + the hook docstring.

### FF-1 — member proposals never transcribed (record gap, no reopen)

The [file-init][file-init] (2 rows), [file-toolbar][file-toolbar]
(7 rows), and [file-boundary][file-boundary] (7 rows) proposed
`## Responsibility index` rows were never added: the index
holds zero `File middleware/*` holdings and zero hits for any
of the 16 family spellings (grep-verified over plan lines
286–1480). The 16 rows under `## Index rows for Worker-0`
re-derive all of them at current bytes under this folder's
holding and SUPERSEDE the member proposals — Worker-0 must
not additionally transcribe the file artifacts' tables, or
every rule rows twice. No row reopened (none exists);
corrections list carries the instruction.

### FF-2 — J1 files-covered stale at WT (population refresh owed)

The `Shared except Exception guard driver` row names
`middleware/request_body.py` in files-covered. At HEAD the
leaf holds two broad guards (mount handoff, recognition
wrapper); at WT the hunt deleted both (replaced by
`truth.static_attr`). The rejection verdict (no shared
driver) holds at every state — the remaining arms are
per-site contracts — but the row's population is HEAD-true
and WT-false. Closeout refreshes the population once the
hunt lands or reverts; until then the row stands as written.
No row reopened.

### FF-3 — toolbar F1 exclusion detail gone (verdict-neutral)

[file-toolbar][file-toolbar] F1 excludes "[rf-init][rf-init]'s
prose mention of this guard" on strength of body. At WT
`require_debug_toolbar` has zero mentions outside its own
leaf (grep over 121 package files): the mention was removed
by later edits. Fewer sites, not more — the F1 membership
verdict is unaffected. Recorded so the next cycle does not
hunt a vanished citation.

### FF-4 — `_is_graphiql` spelling detail stale (verdict-neutral)

[file-toolbar][file-toolbar] F5/F7 record the attribute
spelled at the stamp + read sites. Committed `b20277fe`
introduced `_IS_GRAPHIQL` (single binding at
`debug_toolbar.py:154`, two constant reads): the F5/F7
spelling prose is stale while their single-ownership verdicts
are strengthened (C24 counts 1). No row exists to correct;
recorded as drift context for the closeout pass.

### FF-5 — plan file rows pin a commit as a blob (correction owed)

Plan lines 157–159 record each middleware file item as
"target blob unchanged at `5ee86193`" — but `5ee86193` is a
commit (`test(connection): give the repeated rejection
assertion a name`), not a blob. Same record error as the
forms / management-commands / management FF-1s. Closeout
should re-pin the three rows to the artifact-era blobs
(`6e1b64ca` / `5360149b` / `e6e32e78`) or drop the pins
(corrections list). No row reopened.

### FF-6 — artifact-era population figures stale (verdict-neutral)

The member artifacts' "117 package `.py` files" population is
artifact-era: the package holds 121 at WT. Every census in
this artifact was re-run over the current tree (each figure
states its pattern + population); the `def process_view`
count re-confirms at exactly 2. Figures, not verdicts, moved.

## Defects

No new defects. Every docstring/comment claim checked while
tracing held at its own state, with one standing exception:

- D-W2-1 persists (not re-homed, not fixed):
  `middleware/request_body.py:45-46` says the exemption lives
  in [ordering][ordering] "together with the two marks" while
  the protocol holds four marks (MARKER, ENFORCED, MOUNT,
  PREPARED_VIEW) plus the method name, channel, and
  exemption. Already homed to closeout per the plan (run-2
  File `_boundary_ordering.py` section); the prose sits on
  hunt-clean lines but the repair belongs to the homed owner,
  and defects are never fixed inside an item. Count-free fix,
  still owed.

Checked and held: two-override toolbar shape (AST: exactly
`process_view` + `_postprocess`); import-time guard + clean
root/marker imports (pinned by the cleanliness oracle, run
green); all three upstream divergences present as stated
(non-class guard in truthful form at WT, shape bails,
encoding bail); hint floor trio agreement; top-level-only vs
broken-submodule-raw split; conditional `Content-Length`
refresh on both paths; streaming early-out; `TemplatesPanel`
skip + `has_content`-false `None` + callable policy; no
`views.py` import in either direction involving the boundary
leaf; twin set/reset shape with `finally` on both; hook
statement order; audit class-comparison / first-entry-wins /
function-skip / no-CSRF pass; `_NO_SETUP` identity check; no
`or {}` default; root and marker never import either leaf.

## Pending execution

No `proof:` entry (zero consolidations, zero
`execution-deferred` claims). Four `gate:` witnesses for the
final gate, typed as listed:

- `gate: heavy uv run pytest -n0 tests/middleware/test_debug_toolbar.py --no-cov -q`
  (in-folder toolbar oracles; ran green 71/71 this item —
  final gate re-runs against the merged tree)
- `gate: heavy uv run pytest -n0 tests/test_views.py --no-cov -q`
  (boundary package-tier oracles incl. the 17+ middleware
  rows; not run this item — the one authorized shared-tree
  run is spent above)
- `gate: heavy uv run pytest -n0 examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q`
  (live toolbar surface: HTML marker, named panels,
  introspection skip, encoding rows; not run this item)
- `gate: heavy uv run python scripts/build_tree_md.py --check`
  (the [tree][tree] projection over the marker docstring)

Cells: sharded and pg are INAPPLICABLE by construction —
neither leaf performs a query, connection, alias, or dialect
decision (the boundary leaf reads only `settings.MIDDLEWARE`
at chain-build time; the toolbar leaf decodes JSON and maps
panels; the audit + guards touch no database), so cell
variation cannot change a behavior this item judges. The
live tiers' database use is incidental fixture traffic. The
boundary file item established the same inapplicability and
its Worker-2 agreed; Worker-2 judges the folder-wide claim.

## Judgment

Zero-edit CONFIRM. Sixteen folder rules re-derived at
current bytes, each single-owned (C1–C26 all ≤1); twelve
standing cross-boundary rows re-checked to their recorded
verdicts with concurrent hunt dirt correctly routed around
them (FC-2's block persists; FC-5/FR-2 note the
imposed spelling without inheriting it); one cross-artifact
convergence holds (FC-10); eight merges rejected with
contract differences + triggers + durable homes (FR-1..FR-8);
six record details flagged for closeout homing without
reopening any row (FF-1..FF-6). The e9 open family is
undisturbed; no new family is named (every cross-file rule
already has a holding family, and every folder resemblance
dissolves on contract). One homed defect persists (D-W2-1);
zero new defects. Submission `ready-for-verification/1`.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for
verification). Item-scoped diff vs
`ITEM_BASELINE=9d22e2203e2d748966c0e9fb5b12c3b642dbba17`:
`git diff <baseline> -- django_strawberry_framework tests
examples` empty; target blobs match dispatch pins exactly
(marker `6e1b64ca` clean at all three states; toolbar WT/BASE
`301e43dc` vs HEAD `63b8765e`; boundary WT/BASE `7422cee9`
vs HEAD `e038bdd1`). The artifact itself
(`docs/dry/dry-folder-middleware.md`) is a new untracked
file, the item's only output. The `## Owned changes` ledger
gains no row from this item. Concurrent dirt (the hunt's
truth migration on both leaves, plus connected-source dirt
on views/typing/request_body-lib/exceptions/routers/sessions
and their tests) was left untouched by content attribution.
No `uv run ruff` run (no `.py` touched). One authorized
focused pytest run (above). No `docs/dry/temp-tests/`
scratch; no workspace copy was needed (no source-mutating
proof exists for a zero-edit audit). No commit, no stash, no
branch operation.

## Index rows for Worker-0

Sixteen new `file-local` rows (holding item `Folder
integration `middleware/``; re-derived at the WT/HEAD/BASE
blobs in System trace; transcribe verbatim). They SUPERSEDE
the member artifacts' proposed tables (FF-1) — do not
transcribe those additionally.

| `middleware-import-clean-marker` | `django_strawberry_framework/middleware/__init__.py` (docstring-only marker; zero imports, binds nothing) | `django_strawberry_framework/middleware/__init__.py` | Folder integration `middleware/` | file-local |
| `middleware-no-reexport-opt-in-surface` | spec-042 Decision 3 (mechanism: `django_strawberry_framework/middleware/debug_toolbar.py::require_debug_toolbar` + root omission) | `django_strawberry_framework/middleware/__init__.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-install-hint-and-floor-gate` | `django_strawberry_framework/middleware/debug_toolbar.py::_DEBUG_TOOLBAR_INSTALL_HINT` | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-installed-apps-gate` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware` #"apps.is_installed" gate block | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-import-time-guard-ordering` | `django_strawberry_framework/middleware/debug_toolbar.py` leaf module body (bare `require_debug_toolbar()` + ordered sub-guard imports) | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-view-detection-guard` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view` | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-payload-builder-bails` | `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload` | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-postprocess-branches` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess` | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `debug-toolbar-dotted-path-identity` | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware` (class identity; omission halves at the marker) | `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `middleware/` | file-local |
| `middleware-publish-twin` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.__call__` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |
| `boundary-run-hook` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |
| `package-view-recognition` | `django_strawberry_framework/middleware/request_body.py::_package_view_instance` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |
| `ordering-audit` | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |
| `setup-lifecycle-fidelity` | `django_strawberry_framework/middleware/request_body.py::_NO_SETUP` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |
| `refusal-render` | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |
| `middleware-leaf-manifest` | `django_strawberry_framework/middleware/request_body.py::__all__` | `django_strawberry_framework/middleware/request_body.py` | Folder integration `middleware/` | file-local |

### Corrections to existing rows

1. The three `File middleware/*` plan checklist rows (plan
   lines 157–159) pin "target blob unchanged at `5ee86193`"
   — `5ee86193` is a commit sha, not a blob (FF-5).
   Closeout should re-pin the rows to the artifact-era blobs
   (`6e1b64ca` / `5360149b` / `e6e32e78`) or drop the pins.
   No row reopened.
2. The `Shared except Exception guard driver` row's
   files-covered names `middleware/request_body.py`: true at
   HEAD, false at WT (hunt deleted the broad guards). No
   verdict change (rejection stands at every state); closeout
   refreshes the population once the hunt lands or reverts
   (FF-2). No row reopened.
3. No other existing-row correction: the 12 cross-boundary
   rows holding folder members keep their verdicts (FC-1..FC-9
   carried as findings, not row edits), and the member file
   items' ticked `verified` states stand (their assignments
   re-derive at current bytes modulo the verdict-neutral FF-3,
   FF-4, FF-6 details).

## Independent verification (Worker-2)

### Sequencing note (Worker-2)

Slip to disclose: before writing this trace I ran `rg -n '^#{1,3} '` over the
artifact to learn its shape plus `sed -n '1,10p'` for the Status block. That
exposed W1's finding TITLES (candidate inventory + dispositions, e.g. FR-5's
framing) but no finding body, evidence, or reasoning. Mitigation, all checkable
in the tool record: (a) every derivation read below (target bodies, pins, diffs,
plan rows, upstream sources) predates that grep; (b) every claim cites that
evidence; (c) the two framings I would not have named unprompted (M10, M11) are
marked [title-primed] and re-derived from bodies I had already read; (d) the
FC-10 management convergence is NOT pre-derived here and is verified only after
reading. M1-M9 rest on pre-exposure greps (sentinels, Content-Length, setup
wording, MIDDLEWARE census, strawberry dispatch arms, `__all__` asymmetry note).

### Fingerprints (Worker-2, own derivation)

- HEAD `23b5f421`, ITEM_BASELINE `9d22e2203e2d748966c0e9fb5b12c3b642dbba17`
  (`git cat-file -t` = commit).
- WT blobs: `middleware/__init__.py` `6e1b64ca`, `middleware/debug_toolbar.py`
  `301e43dc`, `middleware/request_body.py` `7422cee9` — match dispatch pins.
- HEAD blobs: `6e1b64ca` / `63b8765e` / `e038bdd1` — match dispatch pins.
- ITEM_BASELINE blobs: `6e1b64ca` / `301e43dc` / `7422cee9` (= WT: baseline
  carries the pre-existing hunt dirt).
- `git diff ITEM_BASELINE -- django_strawberry_framework/ tests/ examples/` is
  EMPTY (zero-edit confirmed); `git diff ITEM->HEAD -- middleware/` shows only
  the hunt's truth-migration hunks in reverse. Plan `## Owned changes` has zero
  rows naming `middleware/` (ledger grep empty). Untracked package files
  (`_multipart.py`, `utils/lazy.py`, `utils/truth.py`) are hunt-concurrent, not
  item-added (status delta vs dispatch = the artifact alone).
- WT-vs-HEAD dirt by content: toolbar = truth import + `truth.static_attr` /
  `truth.is_subclass` in `process_view` + docstring reword; request_body =
  truth import + `truth.name` / `truth.static_attr` / `is_type` / `is_instance`
  replacing `getattr`+`except Exception` arms + docstring reword. Both are the
  hunt's truth migration, pre-baseline concurrent, correctly untouched.

### Folder census (Worker-2 instrument: `ast.Module.body` + full line reads)

- `middleware/__init__.py`: 1 node (module docstring, 11 lines, zero code).
- `middleware/debug_toolbar.py`: 28 nodes — 2 hint consts,
  `require_debug_toolbar` + import-time call + `apps.is_installed` gate,
  8 post-guard imports, `_HTML_TYPES`, `_IS_GRAPHIQL`, `_get_payload`,
  `DebugToolbarMiddleware` (`process_view`, `_postprocess`).
- `middleware/request_body.py`: 20 nodes — `__all__`,
  `_MISORDERED_MIDDLEWARE_MESSAGE`, `_NO_SETUP`,
  `GraphQLRequestBodyBoundaryMiddleware` (caps, `__init__`, `__call__`,
  `__acall__`, `process_view`), `_package_view_instance`,
  `_require_boundary_before_csrf`.

### My rule census: 15 folder rules, each single-owned (Worker-2)

Toolbar leaf — `django_strawberry_framework/middleware/debug_toolbar.py`:

- T1 install-hint wording (`::_DEBUG_TOOLBAR_INSTALL_HINT`). Owner: this
  module (declaration; raiser owned by f34). Challenge: floor bump → 1 def
  moves; oracle `_HINT_SUBSTRING` + pyproject row move (listed, not counted).
- T2 app-hint wording (`::_DEBUG_TOOLBAR_APP_HINT`). Owner: this module.
  Challenge: reword → 1 def. No second site (only `ImproperlyConfigured` text).
- T3 wrapper + import-time guard sequence (`::require_debug_toolbar`, call at
  :121, app gate :132-133, E402 imports beneath). Owner: this module.
  Challenge: 4th soft-dep leaf → new declaration, primitive untouched. The
  wrapper is 1 line composing `utils/imports.py::require_optional_module` by
  name — a declaration, not a second raising definition.
- T4 sniff constants + stamp pairing (`::_HTML_TYPES`, `::_IS_GRAPHIQL`,
  stamp :248 / read :285). Owner: this module. Challenge: rename stamp →
  1 def, 2 use sites same module.
- T5 tagging rule (`::DebugToolbarMiddleware.process_view`). Owner: this
  module. Challenge: tag only sync views → 1 def. Consumers: `_postprocess`
  read (same module). Oracle: `tests/middleware/test_debug_toolbar.py`.
- T6 payload builder (`::_get_payload`). Owner: this module. Challenge: skip
  another panel / add a shape guard → 1 def.
- T7 postprocess orchestration (`::_postprocess`: stock-first chain,
  streaming/encoding early-outs, HTML bridge + JSON injection,
  `IntrospectionQuery` skip, twin Content-Length refreshes :290-291/:313-314).
  Owner: this module. Challenge: second skipped operation → 1 def;
  Content-Length policy change → 1 maintenance point (twin lines, one method;
  extraction would be machinery, principle 11).

Boundary leaf — `django_strawberry_framework/middleware/request_body.py`:

- R1 `__all__` manifest (:106). Owner: this module. Challenge: export a
  helper → 1 def.
- R2 misordered-chain message (`::_MISORDERED_MIDDLEWARE_MESSAGE`). Owner:
  this module. Challenge: reword → 1 def.
- R3 `_NO_SETUP` sentinel contract (:117-121: foreign-no-setup vs
  shadowed-non-callable). Owner: this module. Challenge: third setup case →
  1 def.
- R4 dual-chain lifecycle (caps :138-139, `::__init__`, `::__call__`,
  `::__acall__`, ContextVar publish/reset). Owner: this module. Challenge:
  change publish/reset semantics → 2 spellings under 1 recorded decision —
  the twin is justified (reset must follow the downstream response;
  `__acall__` docstring :179-184 states the await boundary, principle 5).
  No consolidation.
- R5 `::process_view` orchestration (early-out :227-228, recognition :229,
  setup + request-check :233-240, boundary invoke via `_BOUNDARY_METHOD`
  :242, HTTPException→text/plain :243-248, mount pack :249-251, stamp :252).
  Owner: this module. Challenge: middleware-side-only Content-Type change →
  1 def. The refusal arm mirrors an EXTERNAL owner (installed
  strawberry 0.327.7 `strawberry/django/views.py` :165-170 and :225-230,
  identical `HttpResponse(reason, status, text/plain)` twins, inline with no
  public translator) — convergent wire, 1 package def. The setup wording
  (:238-239) and mount pack ride this rule (pack half held by e9, below).
- R6 recognition chain (`::_package_view_instance`: marker `is not True`,
  `view_class`/`view_initkwargs` shape, boundary-callable probe, construct,
  `TypeError`→None). Owner: this module. Challenge: require a 4th
  bookkeeping field → 1 def.
- R7 chain-order validator (`::_require_boundary_before_csrf`: first-entry
  comparison, subclass-aware, function-skip, no-CSRF silent). Owner: this
  module. Only `settings.MIDDLEWARE` code reader in the package (:351).
  Challenge: warn-not-raise → 1 def.

Marker leaf — `django_strawberry_framework/middleware/__init__.py`:

- I1 import-clean marker prose + no-re-export posture. Owner: this module.
  Challenge: add a re-export → 1 def. Sibling-manifest triggers unfired
  (still docstring-only).

Held elsewhere (excluded from folder-local census by standing rows): the five
`_BOUNDARY_*` constants + `_boundary_middleware_request` (S1 owner
`_boundary_ordering.py`; folder consumes by name, never restates); the
prepared-view pack (R5 :249-251) + consume (`views.py` :583-587) pair (S3/e9
open); the raising primitive (S6 owner `utils/imports.py`).

### Standing cross-boundary rows re-derived (Worker-2): 12, verdicts expected

S1 `request-body-boundary-ordering` (consolidated) — middleware imports all
five constants + ContextVar by name, invokes via `_BOUNDARY_METHOD`; CONFIRM.
S2 recognition vs toolbar `view_class` read (rejected) — boundary-or-decline
vs tag-bool, different questions/answers; CONFIRM. S3 `prepared-view-handoff-shape`
(open e9) — pack + consume spellings both present, count 2, pack lines
hunt-dirtied (`truth.static_attr` vs HEAD try/except) → block persists;
CONFIRM. S4 shared-except driver J1 (rejected) — no driver introduced
(`_request_body.py` top level = measurement fns only); toolbar
`except Exception` (:298, upstream-verbatim degrade-to-inject) still inline;
request_body's two `except Exception` arms are GONE at WT (hunt replaced with
truth reads) — population shrank, rejection stands (fewer sites cannot create
a driver) but the row's files/population prose is stale; CONFIRM + flag. S5
J6 measurement-colocated (rejected) — leaf still states no policy (limit /
status / reasons reached via the built instance); CONFIRM. S6 f34
require-guard (consolidated) — wrapper still 1-line compose, hint
single-sited, no 4th pattern; CONFIRM. S7 shared-guard-consolidation
(rejected) — wrapper still a declaration; CONFIRM. S8 guard-return-idiom
(rejected) — wrapper still returns the module; CONFIRM. S9/S10
types/utils-leaf-vs-sibling-manifest (rejected) — marker still
docstring-only; CONFIRM both. S11 execution-mode-fact-vs-shape (rejected) —
`is_marked_coroutine_function` reads in `__init__`/`__call__` still
shape-classification; CONFIRM. S12 extensions-debug-surface-split (rejected)
— `debugToolbar` payload vs response `debug` key still separate switches;
CONFIRM.

### Merge candidates I considered (Worker-2): 11, all rejected

M1 two `process_view` hooks: tag-bool-for-all-traffic vs
boundary-or-decline-for-package-views. Trigger: a package-owned
middleware-hook protocol. REJECT. M2 two `view_class` reads: subclass
question vs boundary question (folds into S2). Trigger: one predicate
serving both. REJECT. M3 `__all__` asymmetry (boundary leaf has one,
toolbar leaf none): per-module export needs. Trigger: a package manifest
policy. REJECT. M4 `_NO_SETUP` vs the ~15 package `object()` sentinels:
identity-per-subject; sharing conflates distinct absences. Trigger: a
subject whose absence MEANS another's. REJECT. M5 refusal render vs
dispatch translation: paired shape is upstream-owned with no public
translator (verified at installed strawberry 0.327.7). Trigger: upstream
exposes the translator. REJECT. M6 Content-Length twin: one maintenance
point. Trigger: third refresh site. REJECT. M7 `__call__`/`__acall__`
unification: await boundary, documented. Trigger: sync-only deployment
(a deployment decision, not DRY). REJECT. M8 setup-mirror vs Django
`as_view`: framework-behavior mirror; the instance is needed pre-dispatch.
Trigger: Django exposes an instance-building hook. REJECT. M9 hint
unification (install vs app vs sibling leaves): per-subject wordings under
one raiser. Trigger: a hint consumed by 2+ leaves. REJECT. M10 [title-primed]
`getattr(request, mark, default)` read shape (toolbar `_IS_GRAPHIQL` vs
boundary `_BOUNDARY_ENFORCED` reads): shared idiom, separately-owned marks;
re-derived from bodies :227/:285 + `views.py` once-guard. Trigger: one
mark read as one decision by 2 rules. REJECT. M11 [title-primed]
publish-twin vs toolbar's inherited (sync-only stock) chain behavior:
dual-capable entry vs stock subclass; re-derived from caps :138-139 +
twin bodies vs toolbar's absent chain code. Trigger: stock toolbar gains
async hooks this leaf overrides. REJECT.

### Matrix discharge (Worker-2, against the folder's real surface)

A1 cross-flavor mirroring: the leaves share Django-middleware vocabulary
(`process_view`, `view_class`, MIDDLEWARE installation) — compared pairwise
(M1/M2), contracts differ. SEARCHED. A2 sync/async twins: R4 twin examined
and justified; toolbar leaf is sync-only with no async path introduced, so
no twin is owed (stock-subclass transport). SEARCHED + reasoned. A3 derived
knowledge: boundary name via constant (composed ✓), hints single-sited ✓,
template path single-spelled (leaf + test oracle + mechanical kanban
constant) ✓, `view_class` read twice for different questions (M2) ✓.
SEARCHED. A4 round-trip pairs: decode (`_get_payload`, `OrderedDict`) vs
encode (`_postprocess`, `DjangoJSONEncoder`) — JSON grammar is stdlib-owned,
both halves per spec-042; ContextVar set/reset (finally, both colors);
ENFORCED write/read (S1-owned); PREPARED_VIEW pack/consume (S3-owned).
SEARCHED. A5 other media: spec-042 (toolbar contract + borrowing posture +
Decisions 3/4/5/6/7/8) and spec-046 (boundary Decisions 7/9/18) as contract
sources; oracles `tests/middleware/test_debug_toolbar.py` (14 fns incl. the
`_HINT_SUBSTRING` drift-catch, which re-types the floor — independent),
`tests/test_views.py` boundary/misordering rows, live
`test_debug_toolbar_api.py` + `test_transport_api.py`; deployment composition
in fakeshop `MIDDLEWARE` (toolbar early, boundary immediately before CSRF —
the ordering rule consumed); kanban constants mechanical; module docstrings
projections (D-W2-1 lives here). CLASSIFIED. A6 enforcement by omission:
(i) boundary runs for sync+async package views (`process_view` is
color-agnostic; publish exists in both `__call__`/`__acall__`); (ii) toolbar
tags all `BaseView` subclasses regardless of color; (iii) declined callbacks
keep the view-local arrangement (boundary+CSRF still run in-view — no gap);
(iv) CSRF-less chains pass silent with the view continuation protecting the
endpoint (documented). ENUMERATED, no gap.

### Remainder (Worker-2)

- D-W2-1 (request_body docstring "two marks" vs four): PERSISTS UNCHANGED —
  :46 still reads "together with the two marks" while `_boundary_ordering.py`
  still carries the four stamp constants (`_BOUNDARY_MARKER`,
  `_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`) plus
  `_BOUNDARY_METHOD` + the ContextVar. Still homed correctly to File
  `middleware/request_body.py` (the prose lives in that file's docstring);
  count-free prose fix, closeout-owned. Not re-homed.
- e9: pack (`request_body.py` :249-251) + consume (`views.py` :583-587, clean
  at HEAD — the 14-line views dirt is the unrelated `_multipart` /
  `truth.describe` hunt move) spellings both present; pack side hunt-dirtied
  → migration still unlandable → block persists, family undisturbed.
- Oracle independence: scoped diff empty → nothing rewritten at all; the
  drift-catch re-types rather than imports the floor. Holds.
- Cells: SOUND BY CONSTRUCTION on my own reason — zero hits for
  `connections` / `objects.` / `using(` / `raw(` / `QuerySet` / `django.db`
  across all three folder files; the leaves touch request attributes,
  settings strings, response bytes, and a template render only. Inherited
  stock-toolbar storage is upstream's, not the folder's. (W1's stated reason
  judged after reading.)
- FC-10 management convergence: not pre-derived; verified after reading
  (needs the management folder artifact, outside my derivation set).

### Reconciliation (Worker-2, after reading Findings)

Verdict: VERIFIED. W1's zero-edit CONFIRM stands on every load-bearing
claim; my trace agrees on all 12 standing rows, all 8 merge rejections,
the census composition modulo two explicit facet-mappings, and the
cells judgment. Differences below are (a) facet-mapping for two
leaf-private constants + C24 homing, (b) four row-caption corrections,
(c) seven verdict-neutral figure/provenance corrections — all carried
by Worker-0, none needing W1 authorship, hence no revision pass.

Census (mine 15 vs W1 16): 13 map cleanly (T1/T2/T3/T5/T6/T7,
R1/R3/R4/R5/R6/R7, I1-part). W1 legitimately splits I1 (rows 1-2) and
R5 (rows 11+15, distinct variation axes C14 vs C17) and names one rule
I missed (row 9 class identity — dotted-path consumers make it
cross-site; conceded). Remaining delta is my T4/R2, which I map as
FACETS rather than rows under this stated principle: an index row is
owed where a rule's variation spans modules/consumers (hints→f34,
`__all__`→by-name importers, identity→settings strings), joins a
cross-medium agreement (the floor trio + drift-catch), or encodes a
subtle record-worthy distinction (`_NO_SETUP`'s two-case contract);
leaf-private plain data fully contained in a rowed rule's body is a
facet of that row. (i) `_HTML_TYPES` (binding :150 + sole read :284,
no pins, upstream-verbatim) → facet of row 8; W2 challenge "add a
third type → 1 def" stands as its proof. (ii) `_MISORDERED_…`
(single raise :364 + 3 oracle pins at `tests/test_views.py`
:3340/:3369/:3392, listed-not-counted; pins test the audit's
behavior, no cross-medium agreement) → facet of row 13; W2 challenge
"reword → 1 def, 3 pins follow" stands as its proof. (iii) C24
(stamp rename → 1) was homeless → homed JOINTLY to rows 6+8 (write
half + read half; binding :154 + reads :248/:285 all leaf-private).
Standalone rows would exceed both the members' verified granularity
(16-for-16 exact swap, members folded identically) and the
cross-module/significance bar above, relieving zero change
obligation. Worker-0: record this mapping in Outcomes; transcribe 16.

Standing rows: S1-S12 = FC-1..FC-9 (FC-6/FC-8/FC-9 each cover 2).
All 12 CONFIRMs endorsed on fresh evidence: FC-1 prefix census = 1
file (re-run); FC-2 block persists (pack hunt-dirt on :249-251
verified by hunk; consume half clean — views dirt is lines 100-217
only, verified by hunk ranges; ledger empty for the folder); FC-3
all four `-> ModuleType` refs verified (:104/:39/:239/:118), hints
single-sited, floor trio agrees; FC-4 extension side verified
(`extensions["debug"]`, SQL+exceptions payload,
`allow_unsafe_production` gating); FC-5 contracts differ with the
imposed identical WT spelling correctly routed around; FC-6 marker
still binds nothing; FC-7 exactly two `is_marked_coroutine_function`
call sites; FC-8 converges on FC-3; FC-9 J1 holds at HEAD/BASE/WT
(no driver at any state — HEAD guards inline per-site, WT guards
deleted by hunt) and J6 holds (zero measurement tokens by direct
grep). FC-10 convergence holds: mgmt FR-1 text matches W1's quote
verbatim and the opposite-direction challenge (mgmt C2 → 0 here)
is consistent.

Merges: M1→FR-1, M2→FR-2, M3→FR-3, M4→FR-4, M5→FR-8, M9→FR-6,
M10→FR-7, M11→FR-5 — all 8 carry contract difference + trigger,
all endorsed (FR-3's Decision 3 blessing verified verbatim in
spec-042:913-932 incl. "no `__all__` gymnastics"; FR-4's 19
re-derived exactly under the stated pattern incl. `_META_ABSENT` /
`_OMITTED` / `_MISSING` spot-checks; FR-1's "exactly two"
re-derived). My M6/M7 fold into C10/C13 (same verdicts). My M8
(setup-mirror vs `as_view`) converges to reject (Django owns the
closure; the instance is needed pre-dispatch; trigger: Django
exposes an instance-building hook). Correction to MY trace: the
stock toolbar IS dual-chain (`sync_capable`+`async_capable` with
`__call__`/`__acall__` in the installed middleware) — W1's
"inherits both colors" is literally correct; my "sync-only/Django
adapts" aside was wrong (verdict unaffected; members already knew).

Challenges C1–C26: every count re-derived correct; refusals (C13,
C19–C22) carry mechanism/contract reasons. Matrix A1–A6: all six
discharges sound against the real surface (twin examined, stamp
pairs owned, oracles independent — drift-catch re-types the floor,
never imports it; omission enumeration covers sync/async ×
package/foreign × no-CSRF/misordered/duplicate).

Rows (16): ENDORSE 1, 2 (mechanism-span note: marker facet rowed,
leaf+root mechanism acknowledged in-cell), 3, 5, 6, 7, 8, 9, 11,
12, 13, 16. CORRECT 4 (owner cites `::DebugToolbarMiddleware` for
a module-level line — drop the class: owner should read
`` `django_strawberry_framework/middleware/debug_toolbar.py`
#"apps.is_installed" gate block ``), 10 (twin rule owned by
`__call__` alone — append `+ __acall__`), 14 (rule spans sentinel
+ setup block — append `+ the setup() block in
::GraphQLRequestBodyBoundaryMiddleware.process_view`), 15
(duplicate owner of row 11 — append ` #"except HTTPException"`).
REJECT none. Worker-0 transcribes 12 verbatim + 4 as corrected.

Corrections list: (1) FF-5 re-pin — ENDORSED (`5ee86193` verified a
commit with the quoted message; `6e1b64ca`/`5360149b`/`e6e32e78`
verified blobs head-matching the right files). (2) FF-2 refresh —
ENDORSED (verdict stands at all three states per FC-9 above;
closeout refreshes once the hunt lands or reverts). (3) No other
correction — ACKNOWLEDGED, plus the carried corrections below.

FF-1..FF-6: FF-1 VERIFIED (zero `File middleware/*` holdings, zero
spelling hits in plan; member tables exist with the 16 spellings;
SUPERSEDE endorsed — W1's 16 cover the member tables completely
with owner-cell enrichments, and transcribing both would double
every rule). FF-2 VERIFIED (evidence + non-reopening correct).
FF-3 EVIDENCE FALSE, verdict-neutral: the rf-init prose mention
PERSISTS at WT (`rest_framework/__init__.py:52`) and existed at
`5ee86193`-era (:49) — "zero mentions" and "removed by later
edits" are wrong (no pattern stated, either). F1's exclusion
stands AS WRITTEN (present-and-excluded is exactly what F1
recorded). Worker-0: carry the corrected sentence. FF-4 DRIFT
TRUE, COMMIT WRONG: `_IS_GRAPHIQL` (binding + 2 reads verified)
was introduced by `999a1aab`, not `b20277fe` (whose 95-line
toolbar diff has zero occurrences — re-confirmed); the
typing-series list omits `999a1aab`. Verdict-neutral. FF-5
VERIFIED (above). FF-6 VERIFIED (121 files; `def process_view`
exactly 2; members said 117).

Further verdict-neutral slips carried: FR-7 "two readers" → three
(:227, exemption, `views.py:661`); FR-8 "cross_web/strawberry
dispatch" → strawberry's sync+async dispatch twins own the
translation (verified enclosing methods), cross_web owns only the
exception; FC-9 J6 parenthetical → three `_body` hits (:10 dotted
path + `max_request_body_bytes` mentions :206/:270), zero
measurement tokens by direct grep; FC-2 pack range 249–252 →
249–251 (:252 is the S1 stamp); FC-5 durable home drops "each
method's docstring" (neither states the separation — homes are
this clause + standing row); FR-6's C16 citation doesn't move the
message string (rejection stands on contract difference; the
missing message challenge is supplied by my facet-mapping above).

Pending execution: COMPLETE (no `proof:` owed — zero
consolidations, every finding `static-reviewed` + permanent tiers;
e9's proof correctly lives in its family artifact, not duplicated
here) and correctly typed (4 `gate:` witnesses; consistent with
the management precedent of selective listing). Cells:
INAPPLICABLE judged SOUND on the merits — my own zero-hit DB
grep across all three files corroborates W1's stated reason;
inherited stock-toolbar storage is upstream's, not the folder's.

Gates re-run in MY copy (`dry/folder-middleware/verify-1`,
slot-2, all exit 0): toolbar oracles 71 passed
(`dry-20261010T030924-bdbc88`); basedpyright all-mode 0/0/0
(`dry-20261010T030931-c94255`); floor 0/0/0
(`dry-20261010T031044-438f0b`); truthful-reads `--check` 0
errors / 120 files (`dry-20261010T031157-3cbd54`). Zero-edit →
ambient tree state; no item-attributable failure. check_any not
run (gone). Ruff: touched `.py` set is EMPTY (zero-edit; the only
changed file is this `.md`, which source-layout excludes) —
stated explicitly, no run owed. AGENTS.md prose: production diff
empty (vacuous); artifact header is the DRY.md-mandated block.

Defects: NONE new (agree with W1). D-W2-1 persists unchanged at
:45-46 with the four stamp constants + method + channel still in
`_boundary_ordering.py`, correctly homed to File
`middleware/request_body.py`, count-free, closeout-owned —
verified, not re-homed. No `(Worker-2)` defect entries.

Maintainer needs: nothing blocking. Closeout carries: FF-2
population refresh, FF-5 re-pin-or-drop, the 13 carried
corrections above (4 row captions + C24/facet mapping + 8
figure/provenance repairs), and D-W2-1's prose fix. Copies:
verify-1 slot-2 + 4 evidence logs retained for Worker-0's
release (not released by me).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-boundary]: dry-file-middleware__request_body.md
[file-init]: dry-file-middleware____init__.md
[file-toolbar]: dry-file-middleware__debug_toolbar.md
[file-types]: dry-file-types____init__.md
[file-utils]: dry-file-utils____init__.md
[folder-mgmt]: dry-folder-management.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[ext-debug]: ../../django_strawberry_framework/extensions/debug.py
[imports]: ../../django_strawberry_framework/utils/imports.py
[ordering]: ../../django_strawberry_framework/_boundary_ordering.py
[request-body-lib]: ../../django_strawberry_framework/_request_body.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[routers]: ../../django_strawberry_framework/routers.py
[sessions]: ../../django_strawberry_framework/auth/sessions.py
[typing-util]: ../../django_strawberry_framework/utils/typing.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[toolbar-tests]: ../../tests/middleware/test_debug_toolbar.py

<!-- examples/ -->
[settings]: ../../examples/fakeshop/config/settings.py
[toolbar-api]: ../../examples/fakeshop/test_query/test_debug_toolbar_api.py

<!-- scripts/ -->
[tree-render]: ../../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
