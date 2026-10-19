# Project integration — trace + consolidate

Status: verified
Run: 0.0.15 2026-10-09-13
Item: Project integration (LAST integration item before the gate)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `2b980d83f512c9de9ef91b34c3b02a706f0d9baa` (resolves as commit)
HEAD: `23b5f42106ffd14805936560f5155dd90d7568da`
Slot: slot-2 `dry/project/consolidate`
 (`~/dry/ws/c3af387fc1324a21/dry/slots/slot-2`,
 run `dry-20261010T092733-355184`, fresh)

## Scope

24 tracked package-root files: every ticked member File under
`## Package root` — `__init__`, `_boundary_ordering`,
`_cross_web_patches`, `_django_patches`, `_graphql_core_patches`,
`_request_body`, `_strawberry_patches`, `apps`, `conf`,
`connection`, `consumers`, `error_policy`, `exceptions`, `keyset`,
`list_field`, `permissions`, `registry`, `relay`,
`resource_policy`, `routers`, `scalars`, `schema`, `sets_mixins`,
`views` — plus `_multipart.py` (UNTRACKED but ledgered run-11
f39: owned DRY work, traced fresh in full as project remainder,
NOT concurrent). `utils/truth.py` + `utils/lazy.py` are OUT OF
SCOPE (untracked concurrent hunt work: never traced, never
touched; blocking references noted only). Member artifacts
(run-0..run-8 era inputs, every pin re-derived):
[file-init][file-init], [file-boundary][file-boundary],
[file-cross-web][file-cross-web], [file-django][file-django],
[file-graphql-core][file-graphql-core],
[file-request-body][file-request-body],
[file-strawberry][file-strawberry], [file-apps][file-apps],
[file-conf][file-conf], [file-connection][file-connection],
[file-consumers][file-consumers],
[file-error-policy][file-error-policy],
[file-exceptions][file-exceptions], [file-keyset][file-keyset],
[file-list-field][file-list-field],
[file-permissions][file-permissions],
[file-registry][file-registry], [file-relay][file-relay],
[file-resource-policy][file-resource-policy],
[file-routers][file-routers], [file-scalars][file-scalars],
[file-schema][file-schema],
[file-sets-mixins][file-sets-mixins], [file-views][file-views].
Traced against [plan][plan].

Item-scoped diff check: `git diff 2b980d83 --stat --
django_strawberry_framework/` is EMPTY (BASE=WT over the package;
no BASE→WT move anywhere in the tree since dispatch). Slot-2
verified byte-identical to the worktree on all 25 targets before
any tracing (per-file `git hash-object` comparison, 25/25).

| File | WT blob | HEAD blob | WT / HEAD lines | Dirt |
|---|---|---|---|---|
| `__init__.py` | `b688e2fa` | =WT | 192 / 192 | clean |
| `_boundary_ordering.py` | `f91ccd73` | =WT | 152 / 152 | clean |
| `_cross_web_patches.py` | `70195744` | `c8a0929d` | 366 / 365 | 3 hunks, hunt |
| `_django_patches.py` | `553cbada` | `44a83af1` | 448 / 444 | 7 hunks, hunt |
| `_graphql_core_patches.py` | `a8d1b625` | `3da8d3d1` | 217 / 215 | 4 hunks, hunt |
| `_multipart.py` | `ea88e966` | UNTRACKED | 29 / — | ledgered f39 |
| `_request_body.py` | `5672658f` | `99312893` | 578 / 588 | 6 hunks, hunt |
| `_strawberry_patches.py` | `bbc9dd1e` | `4f8b67ba` | 1013 / 1008 | 8 hunks, hunt |
| `apps.py` | `024739c5` | =WT | 56 / 56 | clean |
| `conf.py` | `903d3523` | `944279c7` | 587 / 627 | 7 hunks, hunt |
| `connection.py` | `d537ab99` | `b984ca99` | 2446 / 2478 | 29 hunks, hunt |
| `consumers.py` | `69b60dba` | `3fc91439` | 1833 / 2200 | 19 hunks, hunt |
| `error_policy.py` | `b8c9c2e5` | `7fc87d9f` | 190 / 189 | 2 hunks, hunt |
| `exceptions.py` | `9c02e960` | `f3793258` | 249 / 424 | 12 hunks, hunt |
| `keyset.py` | `a1890813` | `ec694bc8` | 747 / 738 | 11 hunks, hunt |
| `list_field.py` | `b5cfe957` | `c84cefb2` | 1820 / 1872 | 26 hunks, 3 mixed |
| `permissions.py` | `826330cb` | `b7ab8c69` | 756 / 750 | 24 hunks, hunt |
| `registry.py` | `c5aa2050` | `47b52c52` | 685 / 640 | 16 hunks, 1 mixed |
| `relay.py` | `9257a51b` | `025f2a6a` | 853 / 720 | 20 hunks, 1 mixed |
| `resource_policy.py` | `0ec4e891` | `bf9e3757` | 1571 / 1577 | 12 hunks, hunt |
| `routers.py` | `d354218c` | `f8ec8c98` | 607 / 591 | 15 hunks, 1 mixed |
| `scalars.py` | `072432e6` | `5837c6dc` | 194 / 214 | 6 hunks, hunt |
| `schema.py` | `3b68d694` | `a2321304` | 1419 / 1423 | 21 hunks, f47 lines |
| `sets_mixins.py` | `616dbf20` | `dd358f85` | 951 / 928 | 26 hunks, hunt |
| `views.py` | `72ec3e2d` | `0492167d` | 1158 / 1162 | 4 hunks, f39 + hunt |

278 `@@` hunks total. Ledger rows naming root paths
(Owned changes read in full): exactly eight — the three
adopted-orphan prose rows (`list_field.py`
relay-node-target-guard, `registry.py`
relay-node-name-decode, `relay.py` typed-globalid-decode),
routers.py e1, `_multipart.py` f39 (new file), views.py f39,
schema.py + list_field.py f47, list_field.py f55. Every other
hunk attributes to the hunt by diff content
(truth/lazy-migration spelling, guard deletion, prose), never
by filename. The e1/f39/f47/f55 ledger lines sit INSIDE
hunt-rewritten hunks (line-level mixed); attribution below is
per line.

## Method

Four read-only deep-tracers covered disjoint file groups (A:
connection + consumers; B: list_field + resource_policy; C:
schema + views + _strawberry_patches; D: sets_mixins + relay +
permissions + keyset + registry), each re-deriving pins,
enumeration, dirt, drift, member verdicts, and in-group twins
from WT bytes. All four packs arrived intact via session-log
extraction (the result envelopes truncated in delivery); every
load-bearing claim in them was re-verified first-hand (spot
censuses below). The small
files (13: `__init__` through `scalars.py` above plus
`_multipart.py`) are traced FIRST-HAND in this artifact: full
source reads of all 13 at WT bytes, member-artifact Findings
re-read, every index row re-checked against bytes. All
root-level attribution, composition censuses, FAM verdicts,
and falsifications are Worker-1's own bytes-derived work
regardless of group.

## Attribution (per file, `git diff HEAD -- <path>`)

- `__init__.py`, `_boundary_ordering.py`, `apps.py` (0):
  clean, WT=HEAD.
- `_cross_web_patches.py` (3): truth import + 2×
  `__dict__`→`truth.class_dict` — hunt.
- `_django_patches.py` (7): truth import, `__dict__`/
  `__func__`-getattr→truth reads ×3, prose rewords ×3 — hunt.
- `_graphql_core_patches.py` (4): truth import,
  `__dict__`→`truth.class_dict` ×2, guard-conjunct reorder —
  hunt.
- `_request_body.py` (6): truth import, 2×
  `type().__name__`→`truth.name`, getattr-guard deletions in
  the capability halves + docstring trims — hunt.
- `_strawberry_patches.py` (8, pack C): truth import, 5×
  `truth.class_dict`, docstring rewords — hunt, bodies
  untouched.
- `conf.py` (7): import swap (`_safe_type_name`→truth),
  prose updates, guard deletions in `_normalize_user_settings`
  + `__getattr__` + `upstream_patches_enabled` — hunt.
- `connection.py` (29, pack A): truth/lazy migration +
  guard deletions + prose — hunt, zero owned (no ledger row
  names this path).
- `consumers.py` (19, pack A): admission/outbound/refresh/
  revoke/adapter decontainments + truth migration + prose —
  hunt, zero owned.
- `error_policy.py` (2): `describe_value`→`truth.describe` +
  import swap — hunt.
- `exceptions.py` (12): `_safe_type_name`/`_unprintable`/
  `_safe_arg_repr`/`_safe_text`/`describe_value`/
  `_safe_class_name`/`_safe_model_label`/
  `_safe_terminal_label` deleted; `_model_label`/
  `_terminal_label` added on truth; base `__str__`/
  `__repr__` deleted; docstring updates — hunt.
- `list_field.py` (26, pack B): 3 MIXED hunks carrying the
  ledger lines (`is_supplied` + `coded_error_extensions`
  imports; adopted-orphan trigger docstring; f55 ×3
  compositions; f47 `coded_error_extensions` composition)
  inside hunt-rewritten regions; 23 hunt-only.
- `resource_policy.py` (12, pack B): all hunt (truth
  tails, `narrowed` rework, `except BaseException`→`except
  Exception`, `_attach_cleanup_note` rewrite +
  `_is_cleanup_diagnostic` deletion).
- `routers.py` (15): 1 MIXED hunk carrying the e1 ledger
  lines (disposal comment + `_dispose_sync_awaitable`
  call, WT :333-341) beside hunt `truth.describe`/
  `truth.is_instance` swaps; the ledger import
  (`utils.querysets._dispose_sync_awaitable`) sits beside
  the hunt truth/types imports; 14 hunt-only.
- `scalars.py` (6): truth migration (`_safe_*`→truth.*),
  `BaseException`-guard deletion in `strawberry_config`,
  `_safe_scalar_map_key_label` deletion — hunt.
- `schema.py` (21, pack C): 2 f47 ledger lines (owner
  import :98, `_refusal` composition :710); 19 hunt-only
  (truth migration, `_is_class` deletion, prose).
- `views.py` (4, pack C): f39 ledger lines (owner import
  :103, definition + comment deleted); 2 hunt-only (truth
  swap + docstring).
- `keyset.py` (11, pack D): truth migration (message-only)
  + prose — hunt, zero owned.
- `permissions.py` (24, pack D): truth migration + 2 perf
  hunks (single `.filter(*conditions)`) + prose — hunt,
  zero owned.
- `registry.py` (16, pack D): 1 MIXED hunk carrying the
  adopted-orphan trigger paragraph (relay-node-name-decode,
  WT :526-529) beside concurrent prose; 15 hunt-only
  (truth migration, `IdentityMap` stores, `clear()`
  live-view).
- `relay.py` (20, pack D): 1 MIXED hunk carrying the
  adopted-orphan trigger paragraph (typed-globalid-decode,
  WT :430-434) beside concurrent prose; 19 hunt-only
  (truth/lazy migration, `slot=` threading,
  `_decode_and_coerce` + `_resolve_real_pks_batched`
  feature, guard deletions).
- `sets_mixins.py` (26, pack D): truth migration + prose +
  `_validated_target_memo` memoization — hunt, zero owned
  (no ledger row names this path).

## Matrix

1. **Cross-flavor policy mirroring — SEARCHED.** The write
   flavors (model/form/serializer) compose the decode spine,
   the scalar leaf order, and the preflight by name; the
   folder items hold each flavor's colorings intentional.
   Root-side: the list/connection split (list_field vs
   connection pipelines), the error/resource policy twins
   (mechanism shared at f12/f13, vocabulary per side),
   the four patch lifecycles (e10/e11 rejected). No
   mirrored rule; the two nearest pairs are rejected fresh
   (FR-CHECKPOINTS, FR-DUAL).
2. **Sync/async twins — SEARCHED.** AST census at root: every
   `async def` pairs with its sync half in-file (connection
   pipelines, list_field pipelines + wraps, permissions
   apply/aapply, relay stamp pair, resource_policy window
   entries, schema executors/views runs, keyset none,
   registry none, sets_mixins none). All held per-color
   (Strawberry freezes color at build; async awaits where
   sync cannot). No cross-file twin.
3. **Derived rather than repeated — SEARCHED.** Gate names
   derive once (conf vocabulary + 4 callsites); the
   boundary method name derives once (`_BOUNDARY_METHOD` +
   2 middleware uses); the multipart pair derives once
   (f39 owner + 2 consumers); fingerprints derive once
   (FC-CANONICAL). The `_is_one_of` sextet is the single
   re-derivation found and is already rowed (utils FAM-1,
   blocked; sixth site re-confirmed at sets_mixins.py:626).
4. **Inverse / round-trip pairs — SEARCHED.** `graphql_camel_name`
   / `snake_case` exact-inverse pair (member-verified,
   oracle-pinned); keyset encode/decode + serialize round
   trip + keyset seek dialects; registry register/get
   halves; `relation_connection_to_attr` grammar (f28
   gate-only). No unowned inverse.
5. **Contracts in another medium — SEARCHED.** Witnesses
   re-run green in slot-2 (see Verification); census gates
   (f39 pair, f45 9-hit, f47 single-site, f51 assert, f53
   store census, f55 supplied rows) + behavior oracles
   (manifest, settings, dispatch, routers, scalars,
   exceptions, error_policy, list_field, registry, auth
   queries) all green.
   Docstring-vs-body re-read on all 13 first-hand files +
   pack regions: 3 riding prose defects listed under
   Defects, 1 closure recorded, no new defect.
6. **Enforcement by omission — SEARCHED.** Root re-exports
   exactly one name from utils/ (`PaginationArgumentError`,
   dotted-submodule import — FF-P1 revises the folder
   census, rule intact); zero executable star imports
   package-wide (2 prose mentions only); the 7-name
   `utils/__init__.py` manifest intact with zero
   short-spelling production consumers. No omission gap.
7. **Boundary ContextVars — SEARCHED.**
   `_boundary_middleware_request`, `_cascade_state`,
   `_ORDER_NORMALIZATION_CAPTURE`, `_execution_frames`,
   `_RUNNER_SCOPES`/`_RESUME_REGISTRARS`,
   `OperationLease` machinery each single-owned with
   disjoint scopes (row 333 re-verified: all six
   present). No shared driver.
8. **Exception-shape twins — SEARCHED.** `except
   BaseException`: 10 sites in 4 files
   (extensions/operation_state ×3, auth/mutations ×4,
   resource_policy ×2, schema ×1 — all deliberate
   control-signal splits per their file/folder verdicts);
   `except Exception`: 34 (was 85 — hunt deletions);
   `type(x) is`: 104 (was 116). The J1/J2 rejections hold
   on the narrower populations (no shared driver
   emerged); the three wire dual-inheritance pairs +
   one sync pair held separate (FR-DUAL).

## Member verdicts

Verdict vocabulary: CONVERGE (row's family/standing verdict
re-confirmed at WT bytes), STAND (file-local row intact),
REVISE (verdict stands with refreshed evidence/counts/pins),
SPENT (subject extinct), FALSIFIED (verdict contradicted —
always with the superseding record). Fresh pins re-derived;
artifact pins cited only to confirm or correct.

### `__init__.py` (first-hand: full WT read; clean)

WT 192 lines, blob `b688e2fa`=HEAD. F1 REVISE (manifest
38→40 names — `PaginationArgumentError` committed since;
the artifact-era blob `0ef72601` already holds 39, so the
"38" was off-by-one at its own bytes; exact tuple pinned
by tests/base/test_init.py:194-224). F2/F3/F4/F5/F6/F7
STAND (version :67; logger :14 + before-subimports order;
7-name table :79-96; non-memoizing hook :120-148; debug
exclusion :61-62; no runtime orders/rest_framework/auth
imports — TYPE_CHECKING only :105-116). R1/R2 CONVERGE
(auto :16, Filter filters/__init__.py:23, Upload :46;
root-vs-routers opposite memo/`__all__` polarity intact).
R3 REVISE (tokens now differ — routers narrowed to
`-> type[ProtocolTypeRouter]` :603; rejection stands a
fortiori). R4 STAND (identical miss lines :148 +
routers.py:607).

### `_boundary_ordering.py` (first-hand: full WT read; clean)

WT 152 lines, blob `f91ccd73`=HEAD. F1–F7 CONVERGE (marks
:70/:76/:80/:85, method name :95, ContextVar :103-106,
exemption :109-147, singleton :152; row-331 pin refreshes
views.py:584→:624). F8 STAND (stdlib-only imports :57-60).
R1 STAND (rejection recorded; middleware halves converge
per the verified middleware item). R2 CONVERGE (all six
ContextVars present — matrix axis 7). R3 STAND (marks
cooperative vs f53-consolidated `PrivateAuthority`;
opposite threat models intact). D1 rides (KANBAN.md:371
bullet verbatim stale, card-owned, not a blocker).
D-W2-1 rides ("two marks" middleware/request_body.py:46
vs four marks, prose).

### `_cross_web_patches.py` (first-hand: full WT read)

WT 366 lines. F1/F2-assign CONVERGE (e10/e11 rejected;
lifecycle intact — capture :228, validate :259,
probe :340, apply :348, gate :358). R1 CONVERGE (patched
getter :295 vs views adapter :358; kill-switch split
holds). L1/L2 STAND (retirement prose; property-kind
spelling :239/:345/:366).

### `_django_patches.py` (first-hand: full WT read)

WT 448 lines. F1/F2-assign CONVERGE (e10/e11 rejected).
L1–L6 STAND (guard :336, predicate :292, source set
:220, teardown read :297, capture :149, framing prose).
R1 CONVERGE (SET :220 vs RANGE filters/sets.py:487 +
`_release_is_audited` :490 — both intact).

### `_graphql_core_patches.py` (first-hand: full WT read)

WT 217 lines. F1/F2-assign CONVERGE (e10/e11 rejected).
L1 REVISE (completion :158 intact; hunt swapped the guard
conjunct order :175-179 — same conjunction, short-circuit
order changed, noted per principle 8). L2/L3 STAND
(plain-method spelling :83/:202/:217; status prose).
R1/R2 CONVERGE (mirror vs `is_async_only_iterable`
utils/querysets.py:462; completion vs disposal — opposite
actions intact). R3 STAND (Decision-13 home; 4
independent gate callsites re-censused).

### `_request_body.py` (first-hand: full WT read)

WT 578 lines. F1 CONVERGE (sole namer of the three
private attributes — package census). F2/F3/F5/F6/F7/F8
STAND (ladder :211; probe :280; restore :470; bounded
read :488/:529; ceiling :142; signals :158/:176 with
tails now `truth.name`). F4 REVISE (halves :427/:450
intact, getattr guards deleted — narrowed). F9 STAND
(manifest :135; views imports by name :104). J1 REVISE
(5 guards here + 0 middleware; 34-site population;
rejection holds narrower). J2 REVISE (5 exact-type
checks :404/:419/:478/:483/:565; 104-site population;
views gate :213 intact). J3 STAND (out-of-`except`
WARNING ×2 vs in-`except` consumers log — kinds
intact). J4 CONVERGE (trio intact: :564,
extensions/resource_policy.py:888,
optimizer/single_parent_fetch.py:295). J5/J6/J7 STAND
(0 `_BOUNDARY_` hits; views/middleware name no
private; 0 META/content-type/charset code reads).

### `_multipart.py` (fresh trace, no artifact)

WT 29 lines, blob `ea88e966`, UNTRACKED but ledgered
f39. 4 members: module docstring (grammar + upstream-
backstop record), `_MULTIPART_OPERATIONS_FIELD` :20,
`_MULTIPART_MAP_FIELD` :23, derived
`_MULTIPART_CONTROL_FIELDS` :29. f39 CONSOLIDATED holds:
both consumers compose by name (views.py:103 pair
import, definition deleted; testing/client.py:44-47
triple import + guard :292 + emission :306); the AST
census gate + derivation pin live in
tests/test_multipart.py. Single-owner rule, no second
spelling (literals `"operations"`/`"map"` appear only
here in production — the census gate pins it). Zero
defects.

### `apps.py` (first-hand: full WT read; clean)

WT 56 lines, blob `024739c5`=HEAD. F1 CONVERGE (4
appliers, same order :48-56; e10/e11 rejected). R2
REVISE-pins (identity literals :15/:18; `verbose_name`
now `StrOrPromise`-annotated — committed typing).
R3/R4/R5/R6 STAND (negative shape; absent from root;
4 function-local imports; pointer-only docstring).

### `conf.py` (first-hand: full WT read)

WT 587 lines, 35 top-level members (artifact 34 +
truth import). F1 CONVERGE (gate vocabulary intact
:61/:76/:361; 4 callsites; `resolve_policy` routing
refused — both owners intact). R1 REVISE (normalize
:171 intact; isinstance-guard + copy-guard deleted;
tails `truth.kind`). R2 STAND (lifecycle :215-321).
R3 REVISE (contract :323 intact; generic containment
deleted). R4 STAND (signal wiring :567-587). R6–R13
STAND (8 thin readers :450/:463/:473/:502/:514/:528/
:543/:555 — each present and thin). R14/C31 STAND
(pytest guard :499 + client twin; no read driver
emerged — 9 one-liners intact).

### `error_policy.py` (first-hand: full WT read)

WT 190 lines. F1 STAND (record consumed by the
masking sibling; family verified). F2 REVISE (tails
retargeted to `truth.describe` :116/:122; the
`typed-rejection-value-tail` tag was never an index
row — no row change). F3–F6 STAND (0 seal/recourse/
logger/patch vocabulary — censused). R1 STAND (record
:64 + boundary prose). R2 REVISE (exact-type arms
:114/:120 per the run-7 note; tails truth-based). R3
REVISE (template :138 + `_PACKAGE_ERROR_POLICY` :145
per the run-7 note). R4/R5/R6 STAND (ladder :152;
mint :178; 4-name manifest :56). J1 REVISE (all three
arms exact-type now — :114, extensions/debug.py:716,
resource_policy.py:1542, corroborated by pack B;
refusal re-rests on defaults + per-site wordings).
J2 REVISE (ladders/copies/canonicalization still
shared; shared-tail limb survives on the truth basis
— both policies' tails render via `truth.describe`).

### `exceptions.py` (first-hand: full WT read)

WT 249 lines (HEAD 424 — hunt deleted 175). F1 SPENT
(`describe_value` extinct package-wide; successor is
`truth.describe` with the exact 10-file F1 consumer
census — member-only falsification, FF-P2, no index
row). F2–F5 STAND (0 awaitable/seal-wording/recourse/
DRF vocabulary — censused). R1–R5 SPENT (render
helpers extinct). R6 REVISE-renamed (`_model_label`
:66 + `_terminal_label` :82 on truth; one use each).
R7 REVISE (lattice intact :23/:39/:92/:154/:207;
base call-time guards deleted; typed ctors + pickle
pair intact; dual pairs now 3 wire + 1 sync —
FR-DUAL). R8 REVISE (5-name manifest :14 intact;
bottom-of-graph now "only `utils/truth`" :4-7).
J1 SPENT (trio extinct — plan row 310 retires, FF-P3).

### `routers.py` (first-hand: full WT read)

WT 607 lines. F1 CONVERGE (e1 LANDED — composes
`_dispose_sync_awaitable` :341). F2 REVISE (6
consumers :228/:234/:272/:329/:343/:387; renderer now
`truth.describe`). F3 CONVERGE (f34 — 4 wrappers +
keyset ×2 direct, all re-verified). R1/R2/R4/R5/R6/
R7/R8/R9 STAND (composition :568; gate :546;
3 shapes :376; pre-check :251; floor :277; window
:556; lazy cache :211/:391 + `__all__` :105; guard
split :405). R3 REVISE (pattern gate intact;
`BaseException`→`(re.error, OverflowError,
RecursionError)` :233). J1 CONVERGE (both hooks
intact; opposite polarity holds). J2 REVISE (local
cache intact; remote locks extinct at BOTH bytes —
committed removal predates HEAD; rejection moot-kept).
J3 STAND (no boundary import — censused).

### `scalars.py` (first-hand: full WT read)

WT 194 lines. R1 STAND (grammar :53/:56-102;
exact-str fast path added — verdict-preserving).
R2/R3/R4 STAND (serializer :105; NewType :133 +
binding :135; 1-entry map :141, Upload absent).
R5 REVISE (factory :146 intact; containment
deleted; collisions package-names-only :182;
`_safe_scalar_map_key_label` deleted). R6/R7 STAND
(Upload re-export :26/:35; 4-name manifest :43).
F-reuse STAND (Strawberry-contract raises, not typed
rejections :56-130). J1 SPENT (trio extinct —
same FF-P3). J2 STAND as member-held (4 converter
tables intact: converters :247, scalars :141,
forms :187, serializer :227 — row proposal
endorsed for Worker-0). Handoff homed (f42 +
`types/converters` member; no project action).

### `connection.py` (pack A, claims re-verified)

WT 2446 lines. F1 CONVERGE (5 connection flavor
rules converge; MEMBER list_graphql_fields renamed
Form :250). F2 REVISE (sync-only `policy=` removed
— RECORD; remainder intact, zero `policy=`).
F3 REVISE (guard intact :1729; hunt deleted the
fail-soft hostile arm + tolerant import split —
RECORD). F4 CONVERGE (scalar leaf census by line).
F5 CONVERGE (e7: applies + validate hook +
`validate_offset_pagination` import :124 + calls).
F6 STAND (hybrid granted via owner call). F7 STAND
(order-path resolver :878; `relation_kind` sole
relations import). F8 REVISE (windows intact;
`sealed` kwarg deleted :1218 — RECORD). X1 CONVERGE
(cursor guard LANDED via committed drift —
closeout). L1/L2/R1 STAND. In-group twins: sync/async
ladders + duplicated-keyword conformance pair
held-separate (exact-duplicated-shape rationale
stands).

### `consumers.py` (pack A, claims re-verified)

WT 1833 lines. F1 CONVERGE (2 reserved-name tuples
intact). F2/F3 STAND (revocation lifecycle; 4
appliers). F4 REVISE (truth bodies moved to utils;
the three via-sibling calls remain — file-locality
survives on the via-sibling basis). F5 REVISE
(operation catalog 12→8 by hunt deletion — RECORD).
F6 REVISE (adapter import retained :86; use sites
1→2 by hunt — RECORD). R1/R2/R4–R7/R9/R10 STAND.
R3 SPENT-record (claimed OverlayError removed —
run-11 FF already). R8 REVISE (checkpoints
decontained :875/:942; single/dual shape basis
extends). J1/J2/J4/J5 STAND. J3 trigger FIRED by
committed `ccaa7fc6` (SPENT-record — split-rule
verdict direction unchanged). D1 rides (docstring
"two application sites" vs 3 live calls). Twin
candidate REJECTED on the merits (FR-CHECKPOINTS):
the shared decision already has one owner; the
remaining common lines are two responsibilities'
mechanism coincidence with a load-bearing lease-
span difference.

### `list_field.py` (pack B, claims re-verified)

WT 1820 lines, 84 members (artifact 71 + 13). F1
REVISE (5→4 GRAPHENE validators — RECORD; 3
retained local with dual-home). F2 CONVERGE
(s18 observers intact). F3 REVISE (`__init__` body
re-based on f47 + hunt narrowing; owned lines
verify). F4 CONVERGE (wraps + use sites by name).
F5 CONVERGE (9 UNSET sites, 8 spelled/`is_supplied`
×3 composes f55). F6 CONVERGE (supply ladders
compose f55). F7 STAND (non-import triangle).
F-NEW(f55) CONVERGE (owner intact; ×3 compose).
F8 ADOPTED (f44 composes owner). R2 CONVERGE
(`__reduce__` holds on the narrowed body;
f47/f12/f13 oracles cited). R3 REVISE
(coded-shape basis extends to quote-shape +
REDUCE-ctor-tuple). In-group: pipelines/wraps/
`__reduce__` trio + 6 ladder pairs held-separate
(per-contract evidence); zero merge candidates.

### `resource_policy.py` (pack B, claims re-verified)

WT 1571 lines, 57 members (artifact 54 − 2 + 5).
F1 CONVERGE (window protocol + entries by name).
F2 STAND (11 switches; `append` registration).
F3 CONVERGE (f58 order ladder intact). F4 STAND
(`resolve_resource_policy` entry + narrowing).
F5 STAND (`narrowed` subclass + errors latch).
R1/R2 STAND (error/tail records — except-shape
limb widened by committed drift, verdict holds).
R3 STAND (ctor ladder + 4 residual fields).
R4 STAND (window entries per-policy). R5 REVISE
(stash deleted, `clear()` drains live view —
SPENT-limb recorded). R6 STAND (failure detector
4 conditions). R7 STAND (unowned sentinel arm).
R8 STAND (thread-safe collector machinery). R9
STAND (anchor identity by `id()`). R10 CONVERGE
(globals record). R11 REVISE (dual-stream SPENT
via drift; jitter/`total_seconds` limbs hold).
R12 STAND (leak drains). R13 STAND (filtering).
J1 REVISE (all three exact-type — same record as
error_policy J1; refusal re-rests). J2 STAND
(ladder split per-owner-name holds).

### `schema.py` (pack C, claims re-verified)

WT 1419 lines, 31 members (artifact 29 + 2). F1
CONVERGE (singleton registry intact). F2 CONVERGE
(5 `truth.describe`; the `describe_value` tail
migrated). F3/F4 STAND (aliases; mutation entry).
R1/R2/R3 STAND (verbatim contract block; biconditional
names; no `__all__`). R4 STAND (`_depth_limited_copy`
unused-intact + still uncalled). R5 REVISE (`_refusal`
composes the f47 owner :710). In-group: executor pair
+ `_is_operation_kind` twice-composed ladder pair
held-separate (color + per-color rationale).

### `views.py` (pack C, claims re-verified)

WT 1158 lines, 86 members (artifact 57 + 29). L1/L2/
L4/L5/L7 STAND (sentinel :147; error-shape ladder
pre-arm :231-252; markdown :294-305; 1 humanize use
:505; `_CSRF_EXEMPT` name :140). L3 STAND (lossy
guard as multipart consumer; owned lines verify).
L6 REVISE — homed to `_multipart.py` (f39 LANDED;
tuple subs carry the constant). F1–F3 STAND (async
load-bearing :1133/:1120; user helper :999 NEW as
one-sync-boundary consumer; `_CSRF_EXEMPT` name).
R1–R5 STAND (dup contexts; multistage diagnosis;
`_asgi_date_value` :423; cheap `is_async_request`;
PRETTY_JSON gate :44). R6/R7 CONVERGE (`type() is`
gate :213; f47 envelope assistant). F4/J1 CONVERGE
(lossy content-type + `_is_multipart_form_post`
:336; f39 joins the joined contract). R8–R10/J2
STAND (helpers; `run_until_complete` webhook twin
rejections; user-sync twins; docs-vs-code held).

### `_strawberry_patches.py` (pack C, claims re-verified)

WT 1013 lines. Member rows: F1 STAND (lifecycle →
e10/e11 rejected; `_StrawberryPatchValidationError`
:177; `_PendingRegistration` :190; `_is_class`
SPENT into `truth.is_type` — RECORD), L1–L8 STAND
(all by-line/number), R1/R2 CONVERGE, R3 STAND
(UPSTREAM-MIGRATION prose). In-group: capture/
validate/install skein + sort pairs + registry
guard triple held-separate (kind + lifecycle
rationale).

### `sets_mixins.py` (pack D, claims re-verified)

WT 951 lines, 46 members (artifact 39 + 7). F1/F2/
F4/F5/F6/F9 STAND (status :128; proxy :167;
optimizer link :543; `_is_one_of`-shape site :626
= utils-FAM-1 sixth, blocked; operation reads
:642). F3 REVISE (validation single-owned;
hunt-added `_validated_target_memo` narrows
"every read"→"every distinct value" — RECORD,
observation OB-P1). F7 REVISE (changelog prose
retargeted durable — RECORD). F8 REVISE
(`_active_permission_field_paths` gone — HEAD-era
rename to `_permission_walk_gates` :589 —
RECORD). F10 CONVERGE (4 HEAD-era rule sites named
as the NEW file-local captured-branch/cross-
relation rejection rule). R1/R2 STAND. J1 STAND
(project `_cascade_state` half intact). In-group:
allowed-permission pair + convenience `vars`
twins + forwarding-quartet per-half twins
held-separate (kind + basis rationale).

### `relay.py` (pack D, claims re-verified)

WT 853 lines, 33 members (artifact 19 + 14). F1
CONVERGE (seed `model_for` ×4 :76/:118/:246/:325;
e8-F1 inputs verified). F2 STAND (node decode :-
:282; boundary half intact despite rewrites).
F3 REVISE (guid adapter basis extends —
`:real_pk` non-empty + `slot=` threading —
RECORD). F4 STAND (globalid stamp + heuristic
parse + interfaces triple intact). F5 CONVERGE
(`_coerce_pk_or_none` intact; e4 relay
contribution). F6 REVISE (CY :415 + CP :345 —
CP moved to unaudited Generalize :672..841 —
RECORD; f63 block persists). F7 CONVERGE (split
halves :332+:372 composed by `write_values` by
name). J1–J3 STAND (connections :462 `first`
scalar; async mutation twins; stamp pair). Run-8
D1 SPENT-record (consumer name deleted by
concurrent reword — closeout, FF-P6). In-group:
coerce pair + decode twins + globalid pair +
execution/static twins + globalid adapters held-
separate (raw/typed + atomicity rationale).

### `permissions.py` (pack D, claims re-verified)

WT 756 lines, 54 members (artifact 53 + 1). F1
REVISE (2 extractions ×2 arities split by
exact-shape census — RECORD; `combined` text now
`_COMBINED_WHAT` BY NAME :395 — composition
extends, s18 strengthened). F2 STAND (apply/aapply
sync/async locked :659/:716 + 2 boundary calls
:750/:773). F3 STAND (observer consensus 5). F4
REVISE (consumer ∪ producer single-assert +
seal-cipher excluding delta records; model_for
×1 :594, base_queryset ×1 :597; docstring tip
RETIRED-record — the "receipt" :590 is now a
parameter note). F5 CONVERGE–REVISE (seal-
cipher holds BY NAME :384; `.filter` 2→1 perf —
observer/seal-region/measured-time :230-:353
still ordered-blocking; the limits region is a
THIRD shared clause feeding from `_COMBINED_WHAT`
— s18 extends). In-group: scalar/vector twins +
guard/walk pairs held-separate (arity/shape
rationale).

### `keyset.py` (pack D, claims re-verified)

WT 747 lines, 69 members (artifact 56 + 13). F1/
F2/F3/F5 CONVERGE (crypto gate + read-flavor
switch; seek dialects = e6 by-name composition;
cursor halves; seek-dialect ∈ resolution-order —
all intact). J-series STAND (view/middleware
never import crypto/seal privately — frame halves
intact). R-series STAND (message-only bodies;
payload-bounds check intact :543; seek-dialect
guards intact). Cleanest file in the group —
dirt message-only.

### `registry.py` (pack D, claims re-verified)

WT 685 lines, 27 members (artifact 18 + 9). F1
REVISE (`IdentityMap` stores deeper meaning —
RECORD). F2 CONVERGE (clear() subscribers ×4
:139/:176/:222/:330 intact). F3 CONVERGE
(`assigned_name` by-name; `_frozen_namespaces`
consumers ×5). F4 REVISE (2 enum maps —
filtering entry :254 intact — RECORD). F5
CONVERGE (management half validation + error
shapes). F6 CONVERGE/J1–J3 STAND (owners
registered/deleted by name; path vocabulary
untouched). F7 REVISE (`clear()` drains LIVE
views not snapshots — behavior move, but the
`_ResettableLazyObject` half is gone the same
way — RECORD). F8 REVISE (single-inverse
trigger para :526-529 IS the adopted-orphan
ledger row — owned lines verify inside the
mixed hunk). F9 REVISE (`_DEFINED_SENTINEL`
stays put; sentinel RULE renamed Lazy→
Resettable — RECORD). In-group: reset triple +
bad-clear-defense pair + unregister twins
held-separate (kind rationale).

## Findings — compositions (FC)

Root-involved consolidated/open families re-verified with
fresh WT censuses (owner + every root consumer re-derived;
non-root consumers converge per the verified endpoint
folder items):

- FC-PATCH-GATE: conf vocabulary (`APPLY_UPSTREAM_PATCHES_KEY`
  :61, dependency frozenset :76-83, gate reader :361-447)
  + exactly 4 callsites (django :415, strawberry, cross_web
  :358, graphql_core) + apps dispatch (4 appliers :48-56).
  e10/e11 rejections hold (4 lifecycles × distinct kinds
  intact). CONVERGE.
- FC-LOGGER: root `logger` :14 + 3 re-exports
  (extensions/error_policy :87, extensions/debug :109,
  optimizer/__init__ :26) + exactly 1 `getLogger` :14.
  CONVERGE.
- FC-BOUNDARY: 5 marks + method name + ContextVar +
  exemption (all present) + middleware 2 `_BOUNDARY_METHOD`
  uses (:242/:325) + views method def :624 (pin refresh
  from :584, FF-P10). CONVERGE.
- FC-MULTIPART (f39): owner + views pair import :103 +
  client triple import :44-47 with guard :292 + emission
  :306; census gate green (see Verification). CONVERGE.
- FC-TAIL: `truth.describe` + 10 composing files — the
  exact `describe_value` F1 census (consumers, views,
  routers, error_policy, resource_policy,
  extensions/debug, utils/policies, utils/sessions,
  schema, list_field). The F1 consumer EDGE survives;
  the renderer migrated (FF-P2). CONVERGE-basis.
- FC-DISPOSAL (e1): owner + auth/mutations composes +
  routers composes :341 (ledger lines verify inside the
  mixed hunk). CONVERGE.
- FC-SEAL (s17 + s18 EXTENDED): seal body :3632 +
  `_SealPolicy` :2920 + `_defect_message` :4217 +
  `_UNSEALABLE_STATE_CAUSES` :4121 + `_COMBINED_WHAT`
  :4133 — all single-owned in utils/querysets.py and each
  composed BY NAME from permissions.py (:384/:385/:395/
  :453) and the walker. Third shared clause discovered
  and already single-sourced (pack D F5). CONVERGE,
  strengthened.
- FC-COERCE (e4): owner `coerce_field_value_or_none` +
  5 by-name composers in 5 files (relay, types/relay,
  write_values, querysets, filters/base) + transitive
  edge (write_transaction, keyset). Relay halves intact
  (`_coerce_pk_or_none` :205, `_resolve_real_pk` :275).
  CONVERGE.
- FC-ROWS (e6): adapter + wrap/unwrap/is trio + predicate
  `is_async_only_iterable` :462; keyset seek dialects
  compose by name (pack D F2); list_field/extension/
  resource_policy/connection compose. CONVERGE.
- FC-VALIDATE (e7): validator :3194 + 4 appliers
  :3373/:3391/:3412/:3437 + gate; list_field composes
  ×2 (:1445/:1491), connection composes (pack A F5).
  CONVERGE.
- FC-POLICY (f12/f13): `resolve_policy`/`canonical_policy`/
  `copy_policy` + root consumers (error_policy mint
  :178, resource_policy entries, 2 conf readers
  :543/:555, schema record, list_field/connections
  seams). CONVERGE.
- FC-BOUNDARY-ASYNC (open): owner :545 + 8 consuming
  files (auth/queries + testing/client dropped since
  rowed; views added :1145). Family stays open;
  census REVISED (FF-P5).
- FC-SEED (e8): F2 single `model_for` + 21 call sites /
  7 files (census refreshed, FF-P12); F1 relay seeds
  ×4 (:76/:118/:246/:325) + batched twin WT-only —
  block persists (twin-consistency bars migration).
- FC-HANDOFF (e9): pack :251 + consume views :587;
  count-2 persists; the pack line sits inside a hunt
  truth-migration hunk (re-derived above). Block
  persists.
- FC-REQUIRE (f34): 4 wrappers compose by name
  (routers :248, sessions :127, rest_framework :58,
  debug_toolbar :118) + keyset ×2 direct (:447/:451).
  CONVERGE.
- FC-CURSOR (X1): connection imports :124 + calls
  (pack A F5) — LANDED via committed drift; closeout.
- FC-SUPPLIED (f55): owner + list_field ×3 (:539/:573/
  :597); gate green. CONVERGE.
- FC-CODED (f47): owner + schema :710 + list_field
  :320; gates green. CONVERGE.
- FC-ORDER (f58): ladder intact (pack B F3). CONVERGE.
- FC-RELAY-NODE (4 adopted orphans): trigger docstrings
  present (list_field :230, relay :454, types/relay
  :97, registry :539-clause). CONVERGE.
- FC-WINDOW-ATTR (f28, gate-only): grammar intact +
  finalizer marker :723. CONVERGE.
- FC-PREFETCH (f61 + f65): owner + plans adapter +
  alias intact (utils/optimizer/type folders verify);
  connection/list_field carry prose mentions only —
  no root composition edge. Holds per endpoints.

Non-root cross-folder families (no root definition or
consumer): endpoint folder items verified run 13 and
agree; project confirms the agreement + no root edge —
f33 (orders, persists count-2), f40/f41/f42 (testing/
types, open+blocked), f43 (retired count-1), f44
(consolidated), f46 (open, 2 definitions), f60
(filters, blocked count-2), f64 (filters+utils,
blocked), f66/f67 (consolidated), mutation-discovery
(open+blocked), suppression-mirror (rowed). No new
rows; no reopen.

## Findings — rejected merges (FR)

- FR-CHECKPOINTS (consumers.py:875 + :942): REJECT the
  checkpoint-core merge pack A proposed. The shared
  DECISION already has one owner (`_actor_is_current`
  :858, composed by both); the remaining common lines
  are two responsibilities' mechanism coincidence —
  admission returns a bool verdict with a pre-ack arm
  and no payload (:888-894), outbound gates a send
  that MUST execute inside the same lease span
  (:975-980), and the revoke targets differ
  (`handler.websocket` :936 vs `websocket` :980). A
  shared helper would take the continuation as a
  parameter and obscure the send-inside-lease
  invariant — machinery hiding ownership. Trigger: a
  third checkpoint with the lease+decide+revoke shape
  and no payload continuation (then the bool-verdict
  core becomes the shared rule).
- FR-DUAL (list_field.py:249 + resource_policy.py:123 +
  utils/connections.py:98 + utils/querysets.py:180):
  REJECT unifying the dual-inheritance pairs. Three
  wire pairs (each: GraphQLError catchability + the
  package base for a different error vocabulary with
  different codes/messages) + one sync pair
  (ConfigurationError + RuntimeError — a different
  contract, not a wire error). Each error's dual
  catchability is its own contract; unifying bases
  couples three vocabularies. Extends the standing
  exceptions-R7 verdict to the third wire pair
  (committed drift). Trigger: a new error needing
  both bases for the SAME reason as an existing pair
  (then the pairing rule consolidates).
- FR-REDUCE (`__reduce__` ×4: list_field :330,
  resource_policy :163, exceptions :145/:198):
  REJECT. Per-class pickle ctor tuples by necessity
  (each preserves its own constructor + state); the
  identical `# truth: ok` comments are checker
  vocabulary each site owes for its own read, not a
  shared rule. Trigger: two classes sharing an
  identical ctor tuple (then a shared reduce helper).
- FR-CSRF-NAME (views.py:140 + _boundary_ordering.py:109):
  REJECT. Name vs value: `_CSRF_EXEMPT` is the
  attribute NAME Django reads; `_CSRF_ORDERING_EXEMPTION`
  is the VALUE the package sets — composed, not
  duplicated, at views.py:619. Trigger: a second
  exemption VALUE for the same attribute.

## Findings — families (FAM)

Zero new FAM-N. The single re-derivation found (the
`_is_one_of` sextet) is already rowed (utils FAM-1,
blocked; sixth site re-confirmed at sets_mixins.py:626).
Every other candidate pair holds separate with a
contract difference (FR-CHECKPOINTS/FR-DUAL/FR-REDUCE/
FR-CSRF-NAME above + pack in-group verdicts). No
Families row is owed.

## Falsifications (FF)

Record-only for closeout; verdict direction unchanged
unless noted:

- FF-P1: utils folder matrix axis-6 census ("root
  re-exports nothing from utils/ — 0 hits") is stale:
  1 hit — `PaginationArgumentError`
  (`__init__.py:59`, dotted-submodule import,
  committed drift). The leaf-withholding RULE holds
  (none of the 7 manifest names re-exported; the
  import is dotted-submodule-shaped per the layering
  note). Census REVISE.
- FF-P2: `describe_value` extinct package-wide (0
  hits, def + consumers). Successor `truth.describe`
  with the exact 10-file F1 consumer census. Member
  rows affected: exceptions F1 (SPENT), routers F2
  (REVISE), error_policy F2 (REVISE), schema F2
  (CONVERGE-migrated), conf R1 consumer limb,
  list_field tails. No index row — closeout note.
- FF-P3: plan row 310 (Hostile-metaclass-safe
  class-name rendering at the boundary) — both
  nominated sites extinct (`_safe_class_name` 0
  hits, `_safe_scalar_map_key_label` 0 hits). Row
  retires at closeout; member J1s (exceptions,
  scalars) SPENT likewise.
- FF-P4: J1/J2 populations narrowed by hunt
  deletions — `except Exception` 85→34,
  `type(x) is` 116→104 (re-censused). Rejections
  hold narrower (rows 363/386/408/421/422/447/448).
  Record-only REVISE.
- FF-P5: one-sync-boundary consumers 9→8 files
  (auth/queries.py + testing/client.py dropped to 0
  hits; views.py added :1145). Row 307 REVISE.
- FF-P6: relay run-8 D1 SPENT — the consumer name
  the defect cited was deleted by a concurrent
  reword (pack D). Plan already homes D1 to
  closeout; now spent. Defect closure (1).
- FF-P7: `relation_attr` extinct (0 hits) +
  `_safe_getattr`/`_safe_flag` extinct — rows 399 +
  409 retire at closeout. Convergent with optimizer
  FF-5 + utils FF-9 (both endpoint folders already
  recorded); project confirms at WT bytes.
- FF-P8: routers J2 remote half
  (`_ASYNC_MUTATION_LOCKS`) extinct at BOTH bytes
  (committed removal predates HEAD — 0 LOCK hits in
  HEAD schema.py too). Rejection moot-kept;
  member-only.
- FF-P9: `__init__` F1 "38 names" was off-by-one at
  its own bytes (artifact blob holds 39); committed
  +1 (`PaginationArgumentError`) → 40 at WT.
  Row REVISE.
- FF-P10: row 331 pin views.py:584→:624 (committed
  drift). Record-only.
- FF-P11: consumers J3 trigger fired by committed
  `ccaa7fc6` (pack A re-derived). Split-rule verdict
  direction unchanged; member-only SPENT-record.
- FF-P12: e8 F2 consumer census refreshed — 21 call
  sites / 7 files at WT (relay ×4, permissions ×1,
  + orders/sets, types/relay, mutations/resolvers,
  filters/sets). Single-ownership holds. Row REVISE.

## Defects

Riding (3, all prose, none a blocker): consumers D1
(docstring "two application sites" vs 3 live calls
:1106/:1379/:1580 — pack A re-derived); boundary D1
(KANBAN.md:371 bullet verbatim stale, card-owned);
boundary D-W2-1 (middleware/request_body.py:46 "two
marks" vs four marks). Closed (1): relay run-8 D1
(FF-P6). Narrowed (0). New (0).

## Family-holds + transcription (for Worker-0)

No new hold. Blocked families re-confirmed with the
block re-derived at WT bytes: e8 F1 (batched twin
WT-only), e9 (pack line in hunt hunk), f36/f37/f38
(decode span hunt-dirtied across relay :146-469),
f63 (batched twin WT dirt), utils FAM-1 (sixth site
persists :626). Consolidated landings re-confirmed:
e1, s17(+s18 extended), e4, e6, e7, f12/f13, f28,
f34, f35, f39, f44, f45, f47, f51, f53, f55, f57,
f58, f61, f65, f66, X1 + the 4 adopted orphans.

Transcription: this artifact proposes new index rows
only for drift-new rules + new rejections, per the
utils precedent (all other verdicts converge on
standing rows or stay homed in their verified member
artifacts):

1. NEW file-local: sets_mixins captured-branch/cross-
   relation rejection rule (pack D F10: 4 HEAD-era
   rule sites, single rule, kind-separated).
2. NEW rejected: scalars converter-table separation
   (member-proposed J2, endorsed: 4 tables intact —
   converters :247, scalars :141, forms :187,
   serializer :227 — with per-table triggers).
3. NEW rejected: FR-CHECKPOINTS / FR-DUAL / FR-REDUCE /
   FR-CSRF-NAME (4 rows with triggers as recorded
   above).
4. REVISE existing rows per FF-P1/FF-P3/FF-P4/FF-P5/
   FF-P7/FF-P9/FF-P10/FF-P12 (censuses, pins,
   retirements as noted); FF-P2/P6/P8/P11 are
   member-only closeout notes.

CC-N: none. Copy edits: NONE — zero-edit submission
(slot-2 untouched; no diff).

## Observations (no verdict impact)

- OB-P1: `_validated_target_memo` (sets_mixins.py:223)
  is hunt-added memoization narrowing the validation
  rule's evidence ("every read"→"every distinct
  value"). The rule stays single-owned (memo is a
  cache: identity key, failures never memoized,
  stated lifetime). Hunt behavior change, recorded
  for the hunt's own review, not a DRY finding.
- OB-P2: `_graphql_core_patches.py:175-179` — hunt
  swapped a guard conjunction's short-circuit order
  (`not-iterable ∧ async-iterable` → `async-iterable ∧
  not-iterable`). Same verdict set, different probe
  order; both predicates pure on the result. Noted
  per principle 8; no behavior claim.
- OB-P3: `PaginationArgumentError` (utils/connections
  :98) is the third wire dual-inheritance pair and
  the first root←utils dotted re-export — both via
  committed drift (X1 era), both verdict-preserving
  extensions of rowed rules.

## Verification

- Witnesses (slot-2 `dry/project/consolidate`, run
  `dry-20261010T095202-18061e`, via heavy): 17 files —
  base/test_init, base/test_conf, test_apps,
  test_routers, test_scalars, test_multipart,
  test_exceptions, test_error_policy, test_list_field,
  test_registry, auth/test_queries, utils/test_errors,
  utils/test_connections, utils/test_canonical,
  utils/test_private_state, filters/test_sets,
  utils/test_input_values — **1395 passed, 0 failed**
  in 64s. (Exit 1 is the subset-coverage gate at 55%,
  expected for a focused set; `fail_under = 100`
  applies to the full suite.)
- basedpyright all-mode (`-p pyproject.toml`, slot-2,
  run `dry-20261010T095332-bc05ca`): **0 errors, 0
  warnings, 0 notes**.
- basedpyright floor (`-p pyrightconfig.floor.json`,
  slot-2, run `dry-20261010T095514-0ccb9f`): **0
  errors, 0 warnings, 0 notes**.
- `check_truthful_reads.py --check` (slot-2, run
  `dry-20261010T095638-d47b5a`): 120 files, tier-1 0,
  **errors 0**.
- `check_public_types.py`: NOT OWED (zero edits; no
  public symbol touched).
- Ruff: NOT OWED (zero `.py` edits — no touched
  paths).
- One-heavy-job rule kept throughout (witnesses, then
  all-mode, then floor + truthful-reads, serialized;
  `pressure` GREEN before each heavy call; no
  competing suite observed).
- Pins re-verified stable after the gates (relay /
  sets_mixins / connection blobs unchanged) — no
  package drift during the trace; the 2 files the
  workspace noted as moved are docs-only (this
  artifact + concurrent plan edits).

## Judgment

**CONFIRM, zero-edit.** All 25 targets re-traced fresh
at WT bytes: 112 indexed rows re-checked (63
cross-folder: 19 consolidated + 5 open + 38 rejected
+ 1 superseded; plus 49 single-folder root rows), 22
cross-root-file compositions hold with fresh censuses
(FC-*), 4 merges rejected with triggers (FR-*), 0 new
families, 12 falsifications recorded for closeout
(FF-P1..FF-P12 — 3 row retirements, 1 member-rule
extinction, 8 census/pin/trigger refreshes), 3 riding
prose defects (none a blocker),
1 defect closure, 0 new defects. Every consolidation
candidate either converges on a rowed landing or
holds separate on a contract difference; the
strongest twin (consumers checkpoints) is rejected
on the merits with the lease-span evidence. The
blocked families stay blocked with the block
re-derived at current bytes. Single ownership holds
on every rule examined — no composition to land,
slot-2 untouched. No ledger row is owed.

## Implementation (Worker-1)

None — zero-edit submission. No copy edits exist to
port (slot-2 diff vs worktree: empty on all 25
targets; `git status` in the copy shows only the
synced shared state).

## Independent verification (Worker-2)

Verdict: **verified** (zero-edit CONFIRM stands;
no D-N; CC-1..CC-20 carry exact transcribable
corrections; OB-W2-1..OB-W2-5 are verdict-neutral
notes). No consolidation is owed: my own twin-hunt
(duplicate-body scan over all 25 targets + trigger
re-checks + residue censuses) found zero new FAM-N
and every candidate pair holds separate, rowed, or
blocked on independently re-derived blocks.

Sequencing disclosure: the dispatch brief ordered
the submission artifact read before any other work,
so blind expectation-first tracing was impossible
(same deviation the folder-utils pass-1 verification
recorded). Mitigation: every load-bearing pin,
count, census, and block below was re-derived with
my own commands at current bytes BEFORE reconciling
against W1's numbers; where my first grep disagreed
with W1 the discrepancy was chased to bytes and is
recorded as a CC. The volume of CCs below is itself
evidence the reconciliation was independent.

Copy: slot-3 `dry/project/verify-1`
(`~/dry/ws/c3af387fc1324a21/dry/slots/slot-3`),
first run synced post-submission, reported fresh on
every run. Byte-identity proven first-hand:
per-file `git hash-object` over all 25 targets
identical across WT and slot-3 (25/25, 0 mismatches),
and full-tree `--exclude=__pycache__` diff of
`django_strawberry_framework/` empty for both slot-2
and slot-3 vs WT (no drift since W1's trace;
`__pycache__` bytes differ only).

### Pins, dirt, zero-edit (re-derived)

All 25 WT blobs + HEAD blobs + WT/HEAD line counts
+ `@@` hunk counts re-derived with my own loop:
25/25 match W1's table AND the dispatch pins
exactly (incl. `_multipart.py` `ea88e966`,
UNTRACKED, 29 lines). Hunk total re-sums to 278.
HEAD unmoved (`23b5f421`); status 541 = dispatch
540 + this artifact; no target drifted since
dispatch. CC-1: the ledger holds NINE bullets
naming root paths (3 adopted-orphan prose rows +
routers.py e1 + `_multipart.py` f39 + views.py f39
+ schema.py f47 + list_field.py f47 + list_field.py
f55) — W1's "exactly eight" groups the two f47
bullets; every bullet is named and attributed, so
this is wording only, no index change.

Zero-edit CONFIRMED three ways: (1) `git diff
2b980d83 --stat -- django_strawberry_framework/
tests/ examples/` is EMPTY; (2) the three untracked
package files (`_multipart.py`, `utils/truth.py`,
`utils/lazy.py`) all predate the item (present in
slot-1 `dry/project/before`, `_multipart.py` byte
`ea88e966` there too); (3) slot-3 == WT on all 25
targets (above). No ledger row is owed. Ruff /
public-types gates correctly not owed (zero `.py`
edits anywhere).

### Censuses (my instrument vs W1; verdicts hold)

- Sextet: 3 `def _is_one_of` (inputs.py:529,
write_transaction.py:848, resolvers.py:755) + 3
same-shape sites (errors.py:197 `_is_text_atom`,
directives.py:68, sets_mixins.py:626) — all 6
present at pins; rowed as Family
`real-class-membership-test` (plan line 1826,
blocked-on-hunt, count-6). The per-site tables are
deliberately DIFFERENT sets (errors adds Promise,
write_values adds Mapping; sets_mixins vs
directives share content under different documented
contracts), so the rowed "landing keeps per-site
tables" stands. 0 new FAM-N CONFIRMED.
- `except Exception`: 34/34 EXACT (scope-independent;
0 in truth/lazy). `describe_value`: 0 ✓ extinction.
`truth.describe`: exactly the 10 named files ✓
set-exact (FF-P2). `_safe_class_name`,
`_safe_scalar_map_key_label`: 0 ✓ (FF-P3 row 310
retires). `relation_attr`, `_safe_getattr`,
`_safe_flag`: 0 ✓ (FF-P7 rows 399+409 retire).
`_ASYNC_MUTATION_LOCKS`: 0 at WT and 0 `LOCK` hits
in HEAD schema.py ✓ (FF-P8). `__init__` manifest:
40 names ✓; artifact blob holds 39 ✓ (FF-P9,
off-by-one proven). `PaginationArgumentError` at
`__init__.py:59`, dotted-submodule ✓ (FF-P1); zero
short-spelling production consumers ✓ (only dotted
`mutations/sets.py:98` + prose). Row 331 pin
views.py:624 ✓ (FF-P10). Patch callsites: 4 files
×1 call each ✓ but CC-13 (django :415→:438; record
graphql_core :212, strawberry :1005).
- CC-2 (`except BaseException`): W1's "10 sites in 4
files" MISSES list_field.py:1331 (spec-050
Decision-8 cleanup + re-raise in
`_handle_non_queryset_rejections_async`; committed
lines — HEAD :1383 identical; deliberately broad,
same control-signal class as the other 10). Correct
census: 11 sites in 5 files (operation_state ×3,
auth/mutations ×4, resource_policy ×2, schema ×1,
list_field ×1). Rejection direction stands (no
shared driver; the cleanup helper is already
single-owned and composed by name). Member + pack
both missed it (no BaseException mention in the
list_field member artifact).
- CC-3 (`type(x) is`): W1's "104" reproduces under no
instrument (text 107 incl. 5 non-code lines; AST
115 comparisons). Code-aware census at WT,
excluding out-of-scope truth.py/lazy.py: 110 code
lines / 115 `Is`/`IsNot` comparisons (3 docstring
prose: _request_body.py:315, forms/converter.py:257,
utils/querysets.py:1586; 2 substring false
positives: mutations/sets.py:1824,
schema.py:1374; 8 subscript/attribute/call-arg code
sites the word-arg grep misses). Direction holds
(all figures < artifact-era 116). Transcribe 110
lines (115 comparisons) with this instrument note
(rows 363/386/408/421/422/447/448).
- CC-4 (FF-P12): "21 call sites / 7 files" → 20/7
(the 21st hit is the utils/querysets.py:348
docstring cite; def at :275). Per-file:
mutations/resolvers ×5, types/relay ×4, relay ×4
(:168/:325/:360/:410 — see CC-6), orders/sets ×2,
filters/sets ×1, permissions ×1, querysets-internal
×3 (:355/:4329/:4727). Single-ownership holds.
- CC-5 (FF-P5 vs FC text): FF-P5 "9→8 files" STANDS
(row 307 counts the owner file + consumers; file
list revises to owner + permissions, orders/sets,
filters/sets, mutations/resolvers, auth/mutations,
types/resolvers, views). But FC-BOUNDARY-ASYNC's "8
consuming files" → 7 consuming files + owner
(consumers.py:1376 + schema.py:388 are prose-only;
auth/queries.py + testing/client.py at 0 hits).
- CC-18 (star imports): "2 prose mentions" → 4 prose
lines in 3 files (rest_framework/__init__.py:4,
__init__.py:73/:137, routers.py:103); zero
executable ✓ stands.
- CC-19 (FC-BOUNDARY): "5 marks" → 4 marks
(:70/:76/:80/:85) + method-name constant (:95; the
module docstring states it is not a mark) + views
def (:624). Middleware uses :242/:325 exact.

### Blocked families (blocks re-derived at WT bytes)

- CC-6 (e8 F1 — substantive record revision; family
stays blocked). W1's "F1 relay seeds ×4
(:76/:118/:246/:325)" is wrong in framing and pins:
e8-F1 has TWO seed instances, not four, and :76 is
the import while :118/:246 match no `model_for`
line at WT or HEAD. Current bytes: the SINGLE
instance MIGRATED via committed drift —
`_resolve_real_pk` now composes
`base_queryset(model_for(resolved_type),
using=using)` by name (WT :324-329, HEAD :305-310
identical), and the owner's relay-exclusion clause
is gone with it. The BATCHED instance remains
inline (manager + conditional `.using()`, WT
:407-413) inside WT-only `_resolve_real_pks_batched`
(:372-424; absent at HEAD). Count 2→1 inline.
Family stays BLOCKED (batched lines are
uncommitted hunt dirt; host hunk `@@ -310,6
+329,99` spans both new functions as pure WT
additions), but the twin-consistency rationale is
SUPERSEDED — twins already diverged by committed
evolution; the block is hunt-dirt only. Relay
`model_for` calls re-pinned: :168 (`_node_id_slot`),
:325 (seed), :360 (`_decode_and_coerce` — the
expected-model check moved here from
`decode_model_global_id` by hunt rewrite), :410
(batched — WT-only). Transcribe the above as the
e8-F1 refresh.
- e9 CONFIRMED: pack
`middleware/request_body.py:251` (only prepared-view
setattr; 3 `setattr(request` package-wide as rowed)
inside hunt hunk `@@ -245,10 +246,7` (truth
migration directly above the pack line); consume
views.py:583-588 (pin :587 lands inside the block);
count-2 persists. Block persists.
- CC-8 (f36/f37/f38): blocks persist, but W1's gloss
"(decode span hunt-dirtied across relay :146-469)"
names the WRONG files — that span is the e8/f63
neighborhood. Re-derived blocks: f36 restatement
f-string at rest_framework/resolvers.py:1290
(family pin :1306 moved) inside hunt hunk `@@
-1275,7 +1287,7` (base `type(...).__name__` →
`truth.name(...)`); f37 D1 template at
types/converters.py:938 inside
except-BaseException-deletion hunk `@@ -944,32
+929,15` (both `try/except BaseException` arms
deleted); f38 forms/sets.py `@@ -194,55 +199,78`
exact-persisting + rest_framework/sets.py blocking
hunk moved `@@ -796,17 +777,31` → `@@ -788,20
+769,27` (same discovery rewrite, WT :769-795).
- CC-7 (f63): verdict (blocked) stands; row text
defective. "CY :415 + CP :345 — CP moved to
unaudited Generalize :672..841" uses shorthand
defined NOWHERE (absent from member + family
artifacts) and mislabels member F6
(subsystem-clear-lifecycle). Replace with: D-a
relay.py:315-323 + D-b relay.py:404-406, BOTH
pin-exact to the family record, shapes matching;
D-b sits in the WT-only batched function; host
hunk `@@ -310,6 +329,99` blocks. My trigger
hunt: the only other `current_write_pipeline()`
readers (querysets.py:4458, write_transaction.py:
1195) pin already-built querysets — no `using`
recovery shape, so the cross-module-third-site
trigger has NOT fired.
- utils FAM-1 (`real-class-membership-test`): sixth
site sets_mixins.py:626 persists ✓; blocked row
(plan line 1826) stands as rowed.

### Compositions + rejections (all hold; pins corrected)

Compositions re-censused by name, all HOLD:
FC-PATCH-GATE (4×1 call; CC-13 django pin),
FC-LOGGER (1 `getLogger` + 3 re-exports, pins
exact), FC-BOUNDARY (CC-19 wording; uses exact),
FC-MULTIPART (views :103, client :44-47/:292/:306,
zero literal residue — all exact), FC-TAIL (10
files set-exact), FC-DISPOSAL (routers :341 +
auth/mutations :529, ledger lines verify),
FC-COERCE/FC-ROWS/FC-VALIDATE/FC-POLICY/FC-ORDER/
FC-WINDOW-ATTR/FC-PREFETCH/FC-RELAY-NODE (spot
re-censused; owner + root consumers compose by
name; non-root legs converge per verified endpoint
items, trusted), FC-SEAL (by-name composition
CONFIRMED; CC-17 pins :360/:376/:385/:421/:441/
:453 + imports :122-124 — W1's :384/:395 are prose
/def lines).

- CC-10 (f55): count ×3 CONFIRMED but pins
:539/:573/:597 point at unrelated code → true pins
:452/:453/:454. "9 UNSET sites, 8 spelled" →
9 UNSET-related lines: 5 `strawberry.UNSET`
defaults + 3 `is_supplied` calls + 1 import (:88).
No residue: the 4 remaining `is not None and`
spellings are different rules (2 compose
`is_supplied`, 2 differ in the second conjunct);
`is_supplied` census 16 package-wide matches the
family "16 post-change" exactly.
- CC-11 (f47): schema :710 ✓; list_field :320→:326
(`extensions=coded_error_extensions(
"LIST_ARGUMENT_INVALID", **detail)`).
- CC-12 (f34): "sessions :127" → auth/sessions.py:127
(utils/sessions.py has zero require hits); other
pins exact (routers :248, rest_framework :58,
debug_toolbar :118, keyset :447/:451 — full census
6/6, no fifth wrapper).
- CC-9 (X1): label CONVERGE is wrong. Bespoke
`_reject_negative_offset_cursor` /
`_offset_cursor_prefix` ABSENT both bytes
package-wide and never committed (`git log -S`
empty) — the bespoke form never landed. The CONCERN
landed via e7 `validate_offset_pagination`
composition in `_consume_fallback`
(connection.py:124 import + :837 call). Closeout
record: X1 SPENT, subsumed by FC-VALIDATE (fold
FC-CURSOR into it; W1's "(pack A F5)" evidence
accidentally cites the true landing mechanism
without establishing the subsumption).

Rejections: all four AGREED on substance, each with
a sound contract difference + well-formed trigger.
CC-15 (FR-CHECKPOINTS): owner def :858→:986 (its
docstring states "The ONE decision both checkpoints
await" — un-cited corroboration); pre-ack arm
:888-894→:922-924; revoke calls :936/:980→:938
(`handler.websocket`) / :983 (`websocket`);
send-inside-lease :975-980→:979-982. FR-DUAL:
all 4 pins exact; wire-pair census complete at 3
(no fourth). FR-REDUCE: all 4 pins exact; census
complete package-wide; the 4 identical
`# truth: ok` comments verified. CC-16
(FR-CSRF-NAME): value pin :109→:152 (the
`_CSRF_ORDERING_EXEMPTION` instance; :109 is its
class).

### Own twin-hunt (no FAM-N owed)

Exact-duplicate function-body scan (docstring-
stripped AST hash, sync/async separated) over all
25 targets: 431 functions, 3 duplicate buckets,
all adjudicated: (1) sets_mixins.py:861/:866/:880
no-op hook defaults — three distinct extension
points (depth cap, logic recursion, input
provenance), different signatures/overriders;
separate by contract, no row owed. (2)
_cross_web_patches.py:295 vs views.py:406
(`return self.request.body`) — RE-FINDS rowed R1
(patch payload vs owned adapter; kill-switch /
lifecycle split holds; W1 cites the class pin
:358, the body pair is :295/:406). (3)
consumers.py:1434/:1480 `__init__` forwards — fall
under rowed R10 (per-handler install composes the
shared `_install_stop_aware_schema`; the 2-line
forwards stay per-class: different upstream bases,
zero-arg `super()` binding, per-protocol
evolution). Further hunts: `_safe_*` survivors (3
defs, distinct file/model/import domains — idiom,
not rule); error lattice (`RelatedDeclarationError`
rowed file-local FL5, internal caller-translated);
sync/async pairs all in-file (connection
:1562/:1582, list_field :1422/:1469, permissions
:563/:733; no cross-file twin shape; dup scan found
zero cross-color buckets); `__getattr__` exactly 2
(root :120, routers :603 — opposite polarity as
rowed). No missed consolidation; zero-edit stands.

### Falsifications + defects

FF-P1 ✓, FF-P2 ✓ (extinction + 10-file census
set-exact), FF-P3 ✓ (both 0), FF-P4 (counts per
CC-2/CC-3; direction holds), FF-P5 ✓ (9→8 files
stands; FC wording per CC-5), FF-P6 ✓
(`_decode_relation_id_set` 0 hits WT, present at
HEAD relay.py — spent by concurrent reword;
closure CONFIRMED), FF-P7 ✓ (all 0; rows 399+409
retire), FF-P8 ✓ (0 both bytes), FF-P9 ✓ (blob 39
proven), FF-P10 ✓ (:624), FF-P11 (trigger fired
per pack A; split-rule direction re-checked
intact — member-record detail, trusted), FF-P12
per CC-4 (20/7). Added falsifications from this
verification: e8-F1 half-landing (CC-6), X1
subsumption (CC-9), f38 hunk move (CC-8) — all
recorded with bytes above for closeout.

Defects: 3 riding CONFIRMED persisting, none a
blocker (consumers D1 docstring :1117 vs 3 live —
CC-14: member-era pins 410/1385/1083 drifted to
error_policy.py:410, consumers.py:1178,
schema.py:1181; W1's :1106/:1379/:1580 are a
signature line + 2 docstring lines, all bogus;
D1 rides; KANBAN.md:371 bullet present
verbatim, card-owned; request_body.py:46 "two
marks" vs four marks). 1 closure CONFIRMED
(FF-P6). 0 new defects found by Worker-2 (no
`## Defects` entry owed). J4 trio pins exact
(:564/:888/:295); J1/J2 rejection directions hold
on corrected populations.

### Transcription (for Worker-0)

- CC-20 (count): "7 new rows (1 drift-new rule + 6
rejections)" → 6 new rows (1 file-local + 5
rejections). Only six are named anywhere (1+1+4);
no 7th row exists in the artifact. All six
CONFIRMED transcribable: (1) sets_mixins F10
captured-branch/cross-relation rule — 4 sites
verified HEAD-era (def :417 + delegates :778/:791
+ export :948; all present at HEAD, single rule,
kind-separated from `_reject_shared_relations`);
(2) scalars J2 converter-table separation — 4
tables pin-exact (:247/:141/:187/:227) with
disjoint key/value spaces + member trigger
verbatim; (3-6) the 4 FRs, AGREED, transcribe with
CC-15/CC-16 pin corrections and triggers as
recorded.
- The 8 FF revisions CONFIRMED with figures per
CC-2/CC-3/CC-4/CC-5 (FF-P1/P3/P7/P9/P10 as
stated). Worker-0 additionally transcribes: e8-F1
refresh (CC-6), f63 row-text replacement (CC-7),
f36/f37/f38 block refresh (CC-8), X1 SPENT (CC-9),
FC wording fixes (CC-5/CC-17/CC-19), pin refreshes
(CC-10/CC-11/CC-12/CC-13/CC-14/CC-15/CC-16).
CC-1 (ledger wording) + CC-18 (star-prose count)
correct this artifact's record for closeout
Outcomes (no index row holds those figures). No new
Family holds; blocked pool unchanged (e8 F1, e9,
f36, f37, f38, f63, FAM-1) with re-derived blocks.
- OB-W2-1: "112 indexed rows" is unverifiable as
stated — my cuts give 45 member-held / 71
+family / 90 +folder / 163 mention-based; 112
matches none and no row list is supplied.
Verdict-neutral (coverage is demonstrated per-file,
which this verification substantially re-derived);
do not transcribe the figure.
- OB-W2-2: per-file "member" counts use an unstated
instrument and reproduce under none of five AST
cuts I tried (views "86" exceeds its 44 top-level
statements; relay/registry counts look swapped:
W1 relay 33 = registry defclass+methods,
W1 registry 27 = relay alldefs). Verdict-neutral
scene-setting; do not transcribe.

### Gates (slot-3, serialized via heavy)

`pressure` GREEN before the sequence (0/2 heavy
jobs); one suite at a time throughout. Witnesses
(same 17 files): **1395 passed** in 58.71s
(run dry-20261010T102323-21394b; exit 1 is the
expected subset-coverage gate at 55%).
basedpyright all-mode (`-p pyproject.toml`): **0
errors, 0 warnings, 0 notes** (run
dry-20261010T102433-40d272, 83.95s). Floor (`-p
pyrightconfig.floor.json`): **0/0/0** (run
dry-20261010T102603-d4f885, 83.51s).
`check_truthful_reads.py --check`: 120 files,
tier-1 0, **errors 0** (run
dry-20261010T102731-6780cf). All four match W1's
slot-2 results exactly. Shared tree moved during
the gates by 1 file (docs/dry/dry-0_0_15.md,
concurrent Worker-0 edits) — docs-only; all 25
package pins re-confirmed stable (OB-W2-5).

### Method, cells, judgment

Tracer method (OB-W2-4): 12 files via 4 disjoint
read-only tracers + W1 first-hand re-verification
of load-bearing claims, with 13 files fully
first-hand. ACCEPTED for verdicts: every family,
composition, rejection, and block re-decided above
on bytes I re-read myself, and my independent
twin-hunt found no missed consolidation in
pack-covered files — depth was sufficient for the
zero-edit verdict. Pin discipline was NOT
sufficient: the CCs concentrate in pack-covered
regions (relay, list_field pins, seal, D1), and
pack-D shorthand (CY/CP/Generalize) reached the
artifact undefined. The verdict below rests on my
re-derivation, not on the packs.

Cells (OB-W2-3): sharded + pg are UNVERIFIED. W1
states nothing about cells; "inapplicable by
construction" would be FALSE here (root code paths
in relay/connection/permissions/registry reach
databases, aliases, and `.using()` decisions) and
no maintainer authorization for `--cell` runs is cited.
For a zero-edit item this gates nothing at item
level; Worker-0 carries "cells unverified" to
`## Outcomes`. No `proof:` entries exist (nothing
deferred); the witness runs are `gate:`-class
evidence, all green.

Judgment: W1's CONFIRM is CORRECT on every
verdict that matters — single ownership holds on
every rule examined, the four rejections are
sound, the blocked families stay blocked (one,
e8-F1, on a revised rationale with half its
duplication closed by committed drift), and no
landable consolidation was missed. The artifact's
weakness is record precision (pins, counts,
glosses), not analysis: all 20 CCs are
transcribable by Worker-0 from the exact text
above, with no W1 rework needed — hence verified,
not revision-needed. What I re-derived vs trusted:
re-derived every pin/count/census/block/trigger in
this appendix with my own commands; trusted only
non-root composition legs (converge per verified
endpoint folder items), member-record prose
details (FF-P11 trigger mechanics), and prior-run
history quotes. Status set to verified.

<!-- LINK DEFINITIONS -->

[file-apps]: dry-file-apps.md
[file-boundary]: dry-file-_boundary_ordering.md
[file-conf]: dry-file-conf.md
[file-connection]: dry-file-connection.md
[file-consumers]: dry-file-consumers.md
[file-cross-web]: dry-file-_cross_web_patches.md
[file-django]: dry-file-_django_patches.md
[file-error-policy]: dry-file-error_policy.md
[file-exceptions]: dry-file-exceptions.md
[file-graphql-core]: dry-file-_graphql_core_patches.md
[file-init]: dry-file-__init__.md
[file-keyset]: dry-file-keyset.md
[file-list-field]: dry-file-list_field.md
[file-permissions]: dry-file-permissions.md
[file-registry]: dry-file-registry.md
[file-relay]: dry-file-relay.md
[file-request-body]: dry-file-_request_body.md
[file-resource-policy]: dry-file-resource_policy.md
[file-routers]: dry-file-routers.md
[file-scalars]: dry-file-scalars.md
[file-schema]: dry-file-schema.md
[file-sets-mixins]: dry-file-sets_mixins.md
[file-strawberry]: dry-file-_strawberry_patches.md
[file-views]: dry-file-views.md
[plan]: dry-0_0_15.md
