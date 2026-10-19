# DRY review: `django_strawberry_framework/testing/client.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to one named
holding family, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Mid-size target [testing-client][testing-client] (568 lines at HEAD): the
consumer-facing GraphQL test-client family. It DEFINES the endpoint-precedence ladder composition, the JSON /
multipart body builder with its guard stack (empty-`variables`, reserved
envelope fields, per-path placeholder walker), the sync/async `query()` twin
over one shared uncolored tail, the transport `request()` seam (per-call
`url=` routing + the content-type omission switch), the `login()` session
bracket pair, the graphene-shaped mixin delegation with its flipped default
and two assertion helpers, the two concrete two-line combinations, the
`Response` ride-along shape, the module manifest, and the pytest collection
guard. It COMPOSES by name the engine base (`BaseGraphQLTestClient`:
`_decode`, the `Response` field schema, the abstract `request()` seam), the
`TESTING_ENDPOINT` setting reader + default (both owned at [conf][conf]),
and the hostile-render containment (`_safe_arg_repr`, owned at
[exceptions][exceptions]) — 12 render sites, zero `{x!r}`.

Connected code read for judgment, outside the item: [testing-init][testing-init]
(full, CLEAN — the re-export consumer + bullet projection),
[testing-wrap][testing-wrap] (full, CLEAN — zero client tokens),
[testing-relay][testing-relay] (full worktree read + HEAD token grep — zero
client tokens at both revisions), [conf][conf] (the `TESTING_ENDPOINT` key +
`testing_endpoint_setting()` body + guard comment at both revisions —
byte-identical; the 40+/86- dirt sits elsewhere),
[exceptions][exceptions] (the `_safe_arg_repr` owner body at HEAD; the
worktree deleted the owner in the hunt `truth` migration — judged region is
HEAD-only), [views][views] (the `_MULTIPART_CONTROL_FIELDS` def + its one
reader loop at both revisions — byte-identical; dirt elsewhere),
[strawberry-patches][strawberry-patches] (the scalar-`operations`/`map`
prose at both revisions — prose-only both), [test-client][test-client] (all
oracle bodies at HEAD; worktree dirt characterized below),
[test-client-api][test-client-api] (full, CLEAN — every live node id),
[graphql-client][graphql-client] (full, CLEAN — the routing consumer + the
raw-envelope exemption), [uploads-api][uploads-api] (usage census only, CLEAN
— 13 `TestClient(` calls, zero raw multipart posts), contract source
[spec-043][spec-043] (Decisions 3–11 + helper-reuse obligations D1–D5 /
D-N1–D-N3 + test plan — CLEAN), projections [glossary][glossary] (both
entries — CLEAN), [docs-readme][docs-readme] (the testing section —
HEAD-identical, dirt elsewhere), CHANGELOG (the 0.0.14 entry — CLEAN),
[tree][tree] (one-liner presence only — both hashes recorded, verdict
independent of its content), the installed `strawberry.test.client` base
(full read, strawberry-graphql 0.324.0), the strawberry-django
`test/client.py` shape source (full read, external checkout), the
graphene-django `utils/testing.py` mixin source (full read, external
checkout), the verified [one-sync-boundary][one-sync-boundary] family
artifact (R1 as trigger input — every verdict below re-derived fresh),
the verified testing [init-artifact][init-artifact] and
[wrap-artifact][wrap-artifact] (leaf-manifest + per-subject-guard directions
as trigger inputs only), and the prior-evidence [views-artifact][views-artifact]
(R7 — the views item is REOPENED, so prior evidence only, reckoned with
explicitly at FC1 rather than converged).

Dirt note (traced at HEAD bytes `d8feebb2`, worktree `b1439443`
fingerprinted; nothing touched): the 9 worktree hunks are the concurrent
hunt `truth` migration (`_safe_arg_repr` import → `truth` import, 8 render
call-site retargets, 1 docstring reflow) plus the hunt's deletion of the
unreadable-`len` guard arm and the maintainer's adjacent test-oracle edits —
all absent from the `## Owned changes` ledger and the cycle baseline,
attributed by diff content against `git show HEAD:<path>` as
concurrent-external. Every judgment below holds at HEAD bytes; where a claim
also holds at worktree bytes it says so (D1, R1, the zero-token sweeps).
The `for segment in key.split(".")` line (D1) is byte-identical at both
revisions (HEAD :338, worktree :337).

Excluded with reason: `sealed-execution-queryset` and the other queryset
families (no queryset, seal, or alias surface in the full read),
`soft-dependency-require-guard` (hard `strawberry`/`django` deps only, per
spec-043 Decision 5 — no guard owed), `subsystem-clear-lifecycle` (no bus
row), `hostile-mapping-hardening` (no mapping read by key — `body`/`file_map`
are writes, `files` is iterated), `upstream-patch-lifecycle` /
`upstream-patch-refusal-wording` (no capture/install/probe/validate/`apply()`
— not a patch module), the set/input families (no set class, factory, or
converter here), `canonical-input-provisional-name`,
`generated-choice-enum-name-template`, `mutation-discovery-own-snapshot-read`
(no input materialization), `schema-construction-policy-ladder` as an
adoption (different contract — the ladder pair is rejected at R6, not
adopted), `serializer-*` / `hook-*` / `relation-*` / `optimizer-*` /
`nested-*` / `window-*` / `lateral-*` / `plan-*` families (zero mechanism
tokens: no serializer, hook context, relation walk, hint, plan, or strategy
surface — the full read + the `git grep HEAD` sweeps below). Sibling
`testing/relay.py` internals beyond the zero-token sweep, the debug-toolbar
`operationName` display read, and the three upstream sources (external
precedents, shapes verified, not package sites) are excluded on strength of
body. The `isdecimal` version-parse guard at [filters-sets][filters-sets]:440
is a different domain (release auditing, not object-path indexing) — no
canonical-index twin exists.

Fingerprint table (pins for every finding; `W` = worktree `git hash-object`,
`H` = `git rev-parse HEAD:<path>`; `—` = untracked, no HEAD side):

| Input | H | W | State |
|---|---|---|---|
| `testing/client.py` (target) | `d8feebb2…` | `b1439443…` | hunt-dirty, traced at HEAD |
| `testing/__init__.py` | `48b45d1b…` | same | CLEAN |
| `testing/_wrap.py` | `0df97813…` | same | CLEAN |
| `testing/relay.py` | `df0dc72a…` | `f807bf92…` | hunt-dirty, judged sweep 0/0 |
| `conf.py` | `c6ad46aa…` | `ae3de0a3…` | dirty elsewhere, judged region identical |
| `exceptions.py` | `e06b0b7f…` | `206e9f8d…` | owner HEAD-only (worktree migrated) |
| `views.py` | `9f85b0df…` | `48ee582e…` | dirty elsewhere, judged regions identical |
| `_strawberry_patches.py` | `f77df349…` | `2b39199b…` | prose-only mention both |
| `tests/testing/test_client.py` | `fe01478e…` | `517cf1e6…` | 3 oracle deletions + 1 rework, rest identical |
| `test_query/test_client_api.py` | `4a04369d…` | same | CLEAN |
| `graphql_client.py` | `3cd94f4b…` | same | CLEAN |
| `test_query/test_uploads_api.py` | `dcbcbf61…` | same | CLEAN |
| `spec-043-test_client-0_0_14.md` | `a31a06f1…` | same | CLEAN |
| `docs/GLOSSARY.md` | `3413edc3…` | same | CLEAN |
| [CHANGELOG][changelog] | `d4e10355…` | same | CLEAN |
| `docs/README.md` | `1497164f…` | `30978c34…` | judged testing lines HEAD-identical |
| `docs/TREE.md` | `5d562733…` | `769c2743…` | projection-only, verdict-independent |
| `dry-rule-one-sync-boundary.md` | — | `3904d760…` | untracked trigger input |
| `dry-file-testing____init__.md` | — | `7829edeb…` | untracked trigger input |
| `dry-file-testing___wrap.md` | — | `0c8831c5…` | untracked trigger input |
| `dry-file-views.md` (prior evidence) | — | `26fc5c5f…` | untracked, REOPENED item |
| installed `strawberry/test/client.py` | `f2abe800…` (installed bytes) | — | strawberry-graphql 0.324.0 |
| strawberry-django `test/client.py` | md5 `ad7a1131…` (external) | — | shape source, not package |
| graphene `utils/testing.py` | md5 `2e441da3…` (external) | — | shape source, not package |

Searched population for every `git grep HEAD` census below: the 117 tracked
`django_strawberry_framework/**/*.py` at HEAD (the run-7 inventory figure),
each pattern with its hit count and positive control (the target's own lines
hit, so an empty sweep is a true negative, never an empty corpus).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The testing subsystem's three modules
own disjoint surfaces, each fully read: this file (HTTP-client family),
[testing-relay][testing-relay] (GlobalID mint/decode — zero client tokens at
both revisions), [testing-wrap][testing-wrap] (connection-slot installer —
zero client tokens). The leaf re-export at [testing-init][testing-init] is a
consumer row owned by verified init-F1 (R5). Whole-package sweeps for the
target's mechanisms: `force_login` hits only this file (2 code sites +
docstrings); `.logout()` exactly 1 code site (:414; the async color routes
through `sync_to_async`); `assertResponseNoErrors|assertResponseHasErrors`
only this file + projections; `GRAPHQL_URL` only this file + [conf][conf]
prose; `operationName` EMITTER only :274 (the [toolbar][debug-toolbar] reads it for display,
[resource-policy][resource-policy] mentions it in prose — different rules,
folded into F10); `files:` transport params only this file (forms/filters
`files: Any` is server-side value plumbing, a different layer); `TestCase`
concrete combos only :558/:562. No second client, bracket, mixin, or
assertion-helper site exists. The fakeshop [graphql-client][graphql-client]
routes through this file's builder (consumer, 1 call) and deliberately stays
raw only for the raw-envelope subject (documented exemption, spec-043) —
different rule, not a twin.

**2. Sync/async twins.** Two colored pairs, both compared by behavior: the
`query()` twin (F7 — shared `_build_body` + `_finish_response`, only the
`request()` await differs) and the `login()` twin (F12 — `force_login` /
`logout` vs `sync_to_async`-wrapped, `finally` logout both). The `.client`
accessor pair (F6) differs in annotation only. The async `query()` re-color
mirrors upstream's own re-implementation shape (verified at installed
external bytes) rather than calling `super().query()` — one body is
impossible across the await, so the sharing sits BELOW the color line
(builder + tail), exactly the principle-5 shape. No drift: both colors pin
the same guards live and DB-free (`test_async_files_without_variables…`,
the async raise direction, both logout-on-raise arms).

**3. Derived rather than repeated knowledge.** The endpoint default
(`/graphql/`) is read from its [conf][conf] owner, never re-spelled (the
`"/graphql/"` literals in oracles are independent expectations); the
per-call `url=` default routes through `self.path`, never re-derives the
ladder; the no-`variables` guard reads the just-built body's membership,
never re-tests the argument (the one emission site owns member existence —
C3-adjacent, oracle-pinned with the falsy-dict case); the map rule computes
each entry from the key (`"variables." + key`), never from a folder
heuristic (the base's heuristic is the documented insufficiency, spec-043
D-N4); message rendering composes `_safe_arg_repr` (12 sites, zero `{x!r}`
— spec-043 D5, `git grep HEAD` census 13 hits = 1 import + 12 renders). No
fact is reconstructed by a second means.

**4. Inverse / round-trip pairs.** Three pairs examined. (a) Emit
(`_build_body` + map + reserved set) vs parse ([views][views] control-field
read + loss/charset/ordering enforcement): the BODIES are different rules
(R7 — different contracts, reasons, lifecycles), but the control-field NAME
SET is one external-grammar fact spelled twice → holding family FC1 (count
2). (b) Builder vs engine `_decode`: the decode half is engine-owned and
composed at exactly one call site (:202 — sole `self._decode(` hit); the
triple construction shadows the base's deliberately (documented, D1 ground
2) — upstream shadow, owned here (F8), no package twin. (c) Mint vs decode
of test ids lives in [testing-relay][testing-relay] (different module,
different contract) — no inverse half here. The `True`/`False` and
JSON/multipart mode switches are single-site truthiness gates, not
separated halves (R8).

**5. Contracts restated in another medium.** Five media: production code;
contract source ([spec-043][spec-043] Decisions 3–11 + D1–D5/D-N1–D-N3 —
every reuse obligation verified holding at HEAD: D1 `_decode`/seam
composition, D2 conf precedent, D3 one builder + one decoder, D4 seed
helpers first-line in the live file, D5 12 `_safe_arg_repr` renders,
D-N1/D-N2/D-N3 zero-hit sweeps); independent oracles (36 test functions in
[test-client][test-client] at HEAD + 13 live test functions in
[test-client-api][test-client-api] + the uploads-suite consumer rows — each
spells its own literals and drives the real `request()`/builder, never
reads the owner body); and projections (in-target docstrings, the
[testing-init][testing-init] bullets, [conf][conf] ladder prose, the
[glossary][glossary] entries, [docs-readme][docs-readme] testing section,
CHANGELOG, [tree][tree] one-liners, spec code blocks). The ladder ORDER
prose repeats across media (module docstring, conf docstring, README,
CHANGELOG) — projections of one enforced ladder (F5), listed never counted;
a rung change moves 1 enforcement (C1) + projections. The worktree deleted 3
hostile-containment oracles + reworked 1 (hunt wave, concurrent-external);
the HEAD census (36 test functions) is the evidence this trace judges.

**6. Enforcement by omission.** Four families enumerated member by member.
(a) Colors: every guard (builder, walker, reserved, `assert_no_errors`) is
enforced on BOTH colors by shared-body construction — the async color pins
each live or DB-free; no omission. (b) The `files=` contract's shapes
(top-level, nested, list-index, tuple, empty-segment, hostile-`__len__`,
hostile-`__repr__` ×2, reserved ×3, missing-variables ×3) each carry an
oracle at HEAD; the one shape NO guard covers — a non-`str` key — escapes
as `AttributeError`, filed as D1 (contract source: the uniform-type
docstring clause; proven execution-verified). (c) The mixin deliberately
drops `input_data` (graphene's convenience) — by design per spec-043 D10
with the rewrite spelled out, zero package consumers need it (sole hit is
the docstring line) — a deliberate absence, not a gap. (d) `AsyncTestClient`
inherits `__test__ = False` (no own guard needed — oracle-pinned on both
classes); the two concrete combos inherit the whole mixin (nothing to
re-enforce — the `TransactionTestCase` smoke test pins the wiring). No
member lacks a guard its contract requires, except D1.

### Enumeration

Instrument: `ast.parse` over the HEAD blob (`d8feebb2…`, 568 lines),
counting `ast.Module.body` members — **20 top-level statements**, binding
**24 module-level names** (14 import-bound + 3 `TYPE_CHECKING`-only +
`__all__` + 6 class statements), with **18 method/attribute members**
(1 + 9 + 4 + 4 across the four behavioral classes). Every member lands
below; every challenge in `### Challenges` ends in a file-local row, the
one holding family, or a rejection. Line numbers are HEAD bytes (`:NN`
scratchpad convention).

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (family framing + ladder order + upstream-shape notes) | (none) | prose, F1 (ladder order participates in F5 as projection) |
| 1 | `from __future__ import annotations` | (none) | F1 |
| 2 | `import contextlib` | `contextlib` | F1 (consumed by F12) |
| 3 | `import json` | `json` | F1 (consumed by F10) |
| 4 | `from dataclasses import dataclass` | `dataclass` | F1 (consumed by F3) |
| 5 | `from typing import TYPE_CHECKING, Any` | `TYPE_CHECKING`, `Any` | F1 |
| 6 | `from asgiref.sync import sync_to_async` | `sync_to_async` | F1 (consumed by F12; R1 convergence) |
| 7 | `from django.test import AsyncClient, Client, TestCase, TransactionTestCase` | 4 names | F1 (consumed by F5/F12/F13/F16) |
| 8 | `from strawberry.test import BaseGraphQLTestClient` | `BaseGraphQLTestClient` | F1 (consumed by F5/F7/F13; D1) |
| 9 | `from strawberry.test.client import Response as _EngineResponse` | `_EngineResponse` | F1 (consumed by F3; D1) |
| 10 | `from ...conf import testing_endpoint_setting` | `testing_endpoint_setting` | F1 (consumed by F5; D2) |
| 11 | `from ...exceptions import _safe_arg_repr` | `_safe_arg_repr` | F1 (consumed by F10/F11; D5) |
| 12 | `if TYPE_CHECKING:` (+ 2 nested imports) | `AsyncIterator`, `Iterator`, `AbstractBaseUser` | F1 |
| 13 | `__all__` (6 names) | `__all__` | F2 (R5 pair) |
| 14 | `class Response(_EngineResponse)` + `response` field | `Response` | F3 |
| 15 | `class TestClient(BaseGraphQLTestClient)` | `TestClient` | `__test__` → F4; `__init__` → F5; `client` → F6; `query` → F7; `_finish_response` → F8; `request` → F9; `_build_body` → F10 (+ FC1 participant); `_assert_file_placeholders` → F11; `login` → F12 |
| 16 | `class AsyncTestClient(TestClient)` | `AsyncTestClient` | class stmt + `__init__` → F13; `client` → F6; `query` → F7; `login` → F12 |
| 17 | `class GraphQLTestMixin` | `GraphQLTestMixin` | `GRAPHQL_URL` + `query` → F14; both helpers → F15 |
| 18 | `class GraphQLTestCase(GraphQLTestMixin, TestCase)` | `GraphQLTestCase` | F16 |
| 19 | `class GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase)` | `GraphQLTransactionTestCase` | F16 |

Rules: F1 module mechanics (docstring + import totality + `TYPE_CHECKING`
names + the three verified non-reuse obligations); F2 module manifest (the
6-name `__all__`); F3 `Response` ride-along shape; F4 collection guard;
F5 endpoint ladder (init rungs + presence selection + base forwarding,
with the request arm and mixin rungs as same-file participants); F6
wrapped-client accessor pair; F7 query twin; F8 finish tail; F9 request
transport; F10 body builder; F11 placeholder walker; F12 login bracket;
F13 async twin shape; F14 mixin delegation; F15 assertion helpers; F16
concrete combos; FC1 the cross-file control-field name set (holding
family); R1–R12 rejections below. One family named for Worker-0 to add
(FC1); one adoption of nothing (the composed owners stay owned where they
are — no index edit owed for consumers); three convergences recorded as
rejections (R1 → verified `one-sync-boundary` R1, R2 →
per-subject-rejection-grammars, R3 → the shared-except-guard J1 direction),
each re-derived fresh with its trigger re-checked unfired. 29 index rows
are named for Worker-0 (16 file-local + 12 rejected + 1 open).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. All bodies judged at HEAD bytes; D1 + the R1/sweep claims
verified holding at worktree bytes too (see Dirt note + the workspace run).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C-FC1 | control-field name set | the multipart spec adds a third control field | **2** ([views][views] tuple + this file's set; builder emission + views loss loop follow as consumers of the set) | holding family FC1 |
| C1 | F5 ladder shape | add a sixth rung (e.g. an env var) | **1** (the composition here; setting + default composed by name from [conf][conf]) | independent |
| C2 | F5 default | change `"/graphql/"` | **1** ([conf][conf] reader; every rung follows; oracle literals follow as oracles) | independent — consumer by name |
| C3 | F5 non-persistence | per-call `url=` persists on the client | **0** (refused by contract; the non-persistence oracle pins the refusal) | no definition — prohibited change |
| C4 | F4 guard mechanism | one helper for the class guard + [conf][conf]'s function guard | refused R4 (one token each, different mechanisms, nothing to share) | rejected — no shared machinery |
| C5 | F3 ride-along | the raw response carries a headers-only shape | **1** (here; the engine triple stays composed) | independent |
| C6 | F6 accessor | rename the `_client` slot | **2 spellings, 1 rule, same file** (identical bodies, annotation-only delta — the pair IS finding F6) | independent — same-file pair |
| C7 | F7 colors | add a third color reusing builder + tail | **1** new color here; **0** new builder/decoder defs (spec-043 D3 holds) | independent |
| C8 | F7 extensions | add a third keyword-only extension | **1** per signature, same file (both `query()`s + the mixin forward move together) | independent |
| C9 | F8 triple | the wire gains a fourth member | **1** (here; the engine shadow is deliberate, D1 ground 2) | independent |
| C10 | F9 post shape | Django renames the `content_type` kwarg | **1** in-package (here; the examples raw poster is example-population, out of count) | independent |
| C11 | F10 operationName | the wire gains a batch `operationName` array | **1** (gate + envelope here) | independent |
| C12 | F10 variables gate | emission switches from truthiness to `is not None` | **1** (here; the falsy-dict oracle flips as oracle) | independent |
| C13 | F10 map rule | a file gains two variable paths | **1** (the one-rule comprehension here) | independent |
| C14 | F11 container set | admit a fourth container kind | **1** (walk + message arms here; the `isdecimal` version guard is a different domain) | independent |
| C15 | F11 index grammar | admit leading-zero indexes | **1** (the canonical check here; the noncanonical oracle flips) | independent |
| C16 | F11 key type | admit non-`str` keys | **1** + D1 (today the shape escapes as `AttributeError` — defect, not second def) | independent + defect D1 |
| C17 | F12 session scope | session writes need transaction pinning | **R1 trigger FIRES** (route to verified `one-sync-boundary`; today 1 per side, rejected) | rejected — trigger stated |
| C18 | F12 logout arm | drop logout-on-raise | **1** per color, same file (the two `finally` arms move together) | independent |
| C19 | F13 default arm | `AsyncClient()` gains a required argument | **1** (here; upstream parity noted, not inherited) | independent |
| C20 | F14 state | the mixin caches its delegate | **1** (here; the call-time oracle pins per-call construction) | independent |
| C21 | F14 surface | carry graphene's `input_data=` | **1** + the positional-order breakage (refused by spec-043 D10) | independent — deliberate drop |
| C22 | F15 NoErrors | drop the status check | **1** (here; graphene parity breaks — spec-043 D10 owns both checks) | independent |
| C23 | F15 msg shape | unify the two msg fallbacks | refused R10 (structured details vs graphene passthrough) | rejected — behavior differs |
| C24 | F16 combos | add a third combination | **1** declaration here (zero new machinery) | independent |
| C25 | F2 membership | add a seventh export | **1** here (the leaf import + `__all__` entry follow as consumer rows per verified init-F1) | independent |
| C26 | F1 imports | add an eleventh import | **0** new rules (homed by the rule consuming it) | no definition — homed elsewhere |
| C27 | F1 isolation | a runtime module imports `testing.*` | **0** — prohibited (spec-043 D-N2; sweep hits 0) | no surface — must stay 0 |
| C28 | R2 guard types | one driver for `AssertionError` + `TypeError` + policy grammars | **1** per subject (refused: types + messages + reasons differ) | rejected — N subjects, not 1 rule |
| C29 | R3 len guard | route the `len()` guard through a shared except driver | refused (CONVERGE J1: each site owns its guard + message + chain) | rejected — standing direction |
| C30 | R6 ladders | merge the endpoint + policy ladders | **1** per side (URL selection vs policy resolution — different contracts) | rejected — 2 rules |
| C31 | R7 halves | merge multipart emit + parse bodies | **1** per side (refused; the shared NAME SET routes to FC1, not the bodies) | rejected — 2 rules + 1 set |
| C32 | R8 gates | one gate shape for `operationName`/`variables`/`files` | refused (provided-vs-absent vs member-emission vs mode-switch) | rejected — 3 domains |
| C33 | R9 defaults | normalize both `assert_no_errors` defaults | refused (spec-043 D10: breaks every ported `HasErrors` test) | rejected — spec-owned split |
| C34 | R11 intersections | one helper over the three `& set(` sites | refused (the `&` operator IS the sharing; populations + verdicts differ) | rejected — operator-level |
| C35 | R12 walks | merge placeholder + budget walks | refused (single-path verify vs full-traversal charge) | rejected — behavior differs |
| C36 | R5 manifests | merge module + leaf manifests | refused (each level owns its surface) | rejected — 2 levels |
| C37 | R1 routing | run the bracket through `run_in_one_sync_boundary` | refused (CONVERGE verified R1: thread-insensitive, no transaction) | rejected — standing verdict |
| C38 | F10/F11 render | render one guard message with `{x!r}` | **0** new defs (spec-043 D5 violated; the hostile-`repr` oracles fail) | no definition — prohibited change |

One workspace run was executed (run `dry-20260928T220857-cf276f` at address
`dry/dry-file-testing__client/consolidate`, exit 0, copy fresh, shared
unmoved): the D1 probe (`_assert_file_placeholders` with a non-`str` key →
`AttributeError`) plus two controls (valid path silent, bad `str` path →
`AssertionError`). One read-only shared-tree `uv run python -c` (the
`AsyncClient`/`Client` subclass check → `False`, non-mutating). Everything
else is inspection + `git show`/`git grep HEAD` reads. Every owned behavior
is pinned by the 36 HEAD oracles + 13 live test functions, which the cycle gate
runs; a file item owes no equivalence proof for edits it does not make.
Every other claim below is `static-reviewed`. No `docs/dry/temp-tests/`
scratch created, no shared-tree pytest run.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site (file-local), the one
rule that has one (FC1, routed to a holding family), or the considered
unification that was refused (rejections).

### FC1 — multipart control-field name set (holding family `multipart-control-field-names`)

- **Contract + variation.** The envelope's control-field names — the
`{"operations", "map"}` set from the external multipart request spec. Varies
only with the spec (a third control field, a rename).
- **Sites + roles.** *Definitions (2)*: [views][views]:143
`_MULTIPART_CONTROL_FIELDS = ("operations", "map")` (parse side: iterated
by the lossy-field loop at :754) and this file's :303 `reserved =
{"operations", "map"} & set(files)` (emit side: refused as `files=` keys).
*Consumers*: the builder emission (:314), the views loss loop (:754–757).
*Oracles*: the reserved-guard rows here (`test_files_key_shadowing…`, 3
ids) + the views multipart suite (not inspected — the family item
inventories it) + the hand-built envelopes in `tests/test_views.py` /
`test_transport_api.py` (independent: they must NOT read either owner).
*Projections*: the [strawberry-patches][strawberry-patches] scalar
prose (verified prose-only at both revisions — not a third definition).
- **Challenges.** C-FC1 count **2**; C31 refuses the BODY merger (emit vs
parse stay separate — R7), routing only the name set.
- **Owner + lifetime.** TBD by the family item. Candidates: the views tuple
(parse side), or a shared home both import. Constraint: the
client must not inherit views' import weight (consumer test suites import
this module; spec-043 D-N2's direction is one-way but the weight concern
stands) — dependency direction may force the shared home (principle 7).
Lifetime: import-time constant, never mutated.
- **Migration.** TBD by the family item (one side becomes the owner, the
other composes by name; containers may stay shape-adapted — tuple for
iteration, set for intersection — over one owned member list).
- **Distinct behavior.** The emit and parse BODIES stay separate (R7); the
patch delegates stay retirable (views-R7's reason, untouched).
- **Behavioral proof.** `static-reviewed` (both spellings read at HEAD
bytes; the views reader loop read; oracles cited, not executed — a file
item proves no equivalence). The family item owes execution proof.
- **Structural gate.** TBD by the family item, with the negative control it
owes (a hand-spelled third-site literal the gate catches).
- **Coupling.** Couples to the REOPENED views item: its R7 re-adjudication
must see this candidate. No contradiction with prior views-R7 (different
pair — guards-vs-delegates there, tuple-vs-set here; its C31 "moves only
the tuple" counted within its own pair and never swept the emit side).
- **Freshness.** Target + [views][views] + [strawberry-patches][strawberry-patches]
pins (table above). Population closed by the `"operations"` literal census
at HEAD: exactly :303 + :314 (this file — one definition, the emission at
:314 consuming the set at :303) and [views][views]:143 (+ prose mentions
only, excluded as projections); `consumers.py`, forms/filters `files`
plumbing (value-level, not envelope-level), and the `test-wrap` /
`testing/relay` modules carry zero code tokens. Any byte change reopens
the count.

### F1 — module mechanics (file-local)

- **Contract + variation.** The module's non-rule surface: the family
docstring, 10 import statements binding 14 names, the `TYPE_CHECKING`
block (3 annotation-only names), `__future__` annotations. Varies only by
member addition, each homed by its consuming rule (C26).
- **Sites + roles.** *Definition*: stmts 0–12. *Composed owners* (by name,
staying owned where they are): the engine base + `_decode` + field schema
(spec-043 D1), `testing_endpoint_setting` ([conf][conf], D2),
`_safe_arg_repr` ([exceptions][exceptions], D5). *Verified absences*
(spec-043 non-reuse, all re-derived at HEAD): D-N1 `request_from_info`
(zero hits), D-N2 runtime importers of `testing.*` (zero hits
package-wide outside `testing/`), D-N3 `is_async_callable` (zero hits).
- **Challenges.** C26 count **0**; C27 prohibited (must stay 0).
- **Owner + lifetime.** This file (mechanics row). No stored derivation.
- **Migration.** Stays. **Distinct behavior.** Each import's RULE lives in
its finding (F3/F5/F10/F11/F12); this row homes the MEMBERS.
- **Behavioral proof.** `static-reviewed` (import census 24/24 bound names;
the three zero-hit sweeps with positive controls elsewhere in the tree).
- **Structural gate.** Gate-only: no oracle pins mechanics and none is
owed — no plausible bypass population (never a bespoke existence test per
helper). **Coupling.** None. **Freshness.** Target pin; the D-N2 sweep ran
over the full 117-file HEAD population.

### F2 — module manifest (file-local)

- **Contract + variation.** `__all__` admits exactly the 6 client-family
names (both clients, `Response`, mixin + 2 combos). Varies by member
addition (C25).
- **Sites + roles.** *Definition*: :50–57. *Consumer*: the leaf re-export
(verified init-F1 owns the leaf side). *Oracle*:
`test_export_surface_is_the_testing_root_not_the_package_root` (spells all
six + the root-absence shapes).
- **Challenges.** C25 count **1** (+ leaf consumer rows).
- **Owner + lifetime.** This file (module level owns the module surface —
R5). Import-time constant. **Migration.** Stays. **Distinct behavior.**
The leaf manifest (7 names incl. `safe_wrap_connection_method`) is the
adjacent level's own rule (R5).
- **Behavioral proof.** `static-reviewed` (oracle body read at HEAD).
- **Structural gate.** Gate-only: the export oracle fails on drift; no new
gate. **Coupling.** None. **Freshness.** Target + [test-client][test-client]
+ [testing-init][testing-init] pins.

### F3 — Response ride-along shape (file-local)

- **Contract + variation.** `Response(_EngineResponse)` inherits the
engine's `errors`/`data`/`extensions` triple and adds `response` (the raw
`HttpResponse`; the `None` default is never observed — clients always
populate it). Assert-on-fields posture (whole-object equality is
meaningless over a live response). Varies with the wire triple (C9) and
the ride-along (C5).
- **Sites + roles.** *Definition*: :60–77 (sole `Response(` construction
package-wide is :204; sole `_EngineResponse` subclass). *Composed*:
engine field schema (spec-043 D1/D6). *Oracles*: the extensions row
(present-or-`None`) + every live `res.response.status_code` read.
- **Challenges.** C5/C9 count **1** each.
- **Owner + lifetime.** This file. Per-response instance state, no cache.
- **Migration.** Stays. **Distinct behavior.** The engine triple is
upstream's contract (composed, never re-declared).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only:
the extensions + status oracles; no new gate. **Coupling.** None.
- **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] + installed-base pins.

### F4 — pytest collection guard (file-local)

- **Contract + variation.** `__test__ = False` on `TestClient` (:106;
`AsyncTestClient` inherits it — no own guard needed). Varies with pytest
collection semantics only.
- **Sites + roles.** *Definition*: :106. *Oracle*:
`test_clients_carry_the_pytest_collection_guard` (asserts `is False` on
BOTH classes — the inheritance is pinned, not assumed).
- **Challenges.** C4 routes to R4 (no shared machinery with the
[conf][conf] function guard).
- **Owner + lifetime.** This file (class level). Import-time marker.
- **Migration.** Stays. **Distinct behavior.** Upstream carries the same
guard (verified at external bytes — parity, not inheritance).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only:
the guard oracle fails the moment collection breaks; no new gate.
- **Coupling.** None. **Freshness.** Target + [test-client][test-client] pins.

### F5 — endpoint ladder (file-local)

- **Contract + variation.** Five rungs, highest first: per-call `url=` >
constructor `path=` > `GRAPHQL_URL` > `TESTING_ENDPOINT` setting >
`"/graphql/"` default (spec-043 D7). Constructor resolves once and never
mutates (`self.path`); the per-call override routes one request without
persisting. Presence (`is not None`), never truthiness, selects explicit
values; the resolved endpoint forwards to the base `url` attribute so the
inherited seam never reads the base default. Varies by rung addition (C1);
the default varies only at [conf][conf] (C2).
- **Sites + roles.** *Definition*: `__init__` :108–114 (rungs 2/4/5 +
presence + forwarding) with same-file rung participants: the `request()`
`url=` arm (rung 1, homed F9), `GRAPHQL_URL` + the mixin forward (rungs
3/1, homed F14). *Composed by name*: setting + default ([conf][conf]).
*Oracles*: 4 endpoint tests (default/settings/constructor/per-call +
non-persistence) + 3 mixin rung tests + the live probe-marker tests (rungs
1 + 3 by positive hit). *Projections*: ladder-order prose (module +
conf + README + CHANGELOG docstrings — listed, never counted).
- **Challenges.** C1 count **1**; C2 consumer-by-name; C3 prohibited.
- **Owner + lifetime.** This file (composition); [conf][conf] owns rungs
4–5's values. Resolved per construction / per mixin call — live reads, no
cache (the override-exit oracle pins liveness).
- **Migration.** Stays. **Distinct behavior.** Upstream's `client or
Client()` truthiness is deliberately NOT borrowed (zero package sites;
the falsy-transport oracle pins presence) — fold noted, no row (upstream
out of population).
- **Behavioral proof.** `static-reviewed` (7 DB-free + 2 probe-marker live node ids
read). **Structural gate.** Gate-only: the rung oracles (each rung its own
node id) + the probe-marker positives; no new gate. **Coupling.** None.
- **Freshness.** Target + [conf][conf] + [test-client][test-client] +
[test-client-api][test-client-api] + [spec-043][spec-043] pins.

### F6 — wrapped-client accessor pair (file-local)

- **Contract + variation.** `.client` exposes the wrapped Django client
(the base stores it as `_client`); the async override re-annotates the
return (`AsyncClient`) over a byte-identical body. Varies with the base
slot name (C6).
- **Sites + roles.** *Definition*: :116–119 + :430–433 (the pair IS the
rule — 2 spellings, 1 rule, same file). *Oracles*: presence-selection
rows (identity pins) + every recording-transport test (reads through the
accessor).
- **Challenges.** C6 count 2-spellings-1-rule, same file.
- **Owner + lifetime.** This file. Read-through, no state. **Migration.**
Stays. **Distinct behavior.** The annotation delta is the override's whole
reason (kept for type precision — the one-caller-wrapper question,
principle 11, answered: the boundary name callers depend on).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** None. **Freshness.** Target + [test-client][test-client] pins.

### F7 — query twin (file-local)

- **Contract + variation.** `query()` posts one operation and returns the
typed `Response`: five positionally upstream-compatible params + two
keyword-only package extensions (`operation_name=`, `url=`), orchestrated
as build → request → finish. The async color re-implements the flow
(upstream's own shape) with an awaited `request()`; both colors share
`_build_body` + `_finish_response`. Varies by extension (C8) and color
(C7).
- **Sites + roles.** *Definition*: :121–184 + :435–462. *Composed*:
builder (F10), transport (F9), tail (F8). *Oracles*: the sync raise live,
the async happy-path + raise live, the falsy-transport behavioral rows,
the builder-delegation rows.
- **Challenges.** C7 **1** new color / **0** new builder defs; C8 same-file.
- **Owner + lifetime.** This file. Per-call, no state. **Migration.**
Stays. **Distinct behavior.** The async docstring points at the sync
docstring (reference, not restatement); `super().query()` is deliberately
not called (documented — the tail factors BELOW that decision).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only:
both colors' raise directions + the async transport rows; no new gate.
- **Coupling.** None. **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] + installed-base + strawberry-django pins.

### F8 — finish tail (file-local)

- **Contract + variation.** The uncolored tail both `query()` colors share:
`_decode` → `Response` construction → the EXPLICIT `AssertionError(errors)`
raise (never a bare `assert` — survives `python -O`). Varies with the
triple (C9).
- **Sites + roles.** *Definition*: :186–214. *Composed*: engine `_decode`
at the sole `self._decode(` site (:202). *Oracles*: both raise directions
(sync/async, DB-free + live) + the extensions row. *Shadow*: the base's
`query()` triple + bare assert (upstream, deliberately not called).
- **Challenges.** C9 count **1**.
- **Owner + lifetime.** This file. Per-call. **Migration.** Stays.
- **Distinct behavior.** The base's bare `assert` is the documented
insufficiency (D1 ground 2); the message carries the errors LIST (oracle
pins `"nope" in str`).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** None. **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] + installed-base pins.

### F9 — request transport (file-local)

- **Contract + variation.** `request()` POSTs `body` to `url ?? self.path`
(rung 1) through the wrapped client: JSON posts carry
`content_type="application/json"`; when `files` is truthy the argument is
OMITTED so Django falls back to multipart (the omission IS the switch).
Upstream's `format="multipart"` kwarg (inert on Django's client) is
deliberately dropped — documented, do-not-restore. Varies with the post
shape (C10).
- **Sites + roles.** *Definition*: :216–243 (sole in-package conditional
poster). *Consumers*: both `query()` colors + the mixin forward.
*Oracles*: the recording-transport rung test (selection read off the real
`request()`), the `files={}` JSON test (content type + body shape), the
live multipart uploads (omission proven by successful parse).
- **Challenges.** C10 count **1** in-package.
- **Owner + lifetime.** This file. Per-call. **Migration.** Stays.
- **Distinct behavior.** The examples raw poster (explicit JSON) is the
documented raw-envelope exemption (different rule — its subject is the
wire, which this client abstracts away); upstream's `format=` is the
documented drop (spec-043 D9).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** None. **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] + [graphql-client][graphql-client] pins.

### F10 — body builder (file-local)

- **Contract + variation.** `_build_body` builds the JSON envelope, or the
multipart `operations`/`map` envelope: `operationName` gated on `is not
None` (explicit `""` IS sent for the server to reject; `None` omits the
key — never `null`); `variables` emitted on truthiness; falsy `files` = a
plain JSON post; multipart without a `variables` member refused; reserved
`operations`/`map` keys refused (FC1 participant); placeholders verified
(F11); the uniform map rule `map[key] = ["variables." + key]`; file parts
spread last, identity-preserved; `operationName` injected BEFORE the
`operations` JSON-encoding. Varies per gate (C11/C12/C13).
- **Sites + roles.** *Definition*: :245–314 (sole builder — spec-043 D3
verified: one `_build_body`, one `_decode` site). *Composed*: placeholder
verification (F11), `_safe_arg_repr` (1 render here, D5). *Oracles*: the
map-uniform row (3 shapes + `operationName`-inside), the empty-name row
(sent-vs-omitted), the no-`variables` rows (None/`{}`/falsy-dict + async),
the reserved rows (3 ids), the `files={}` row, the live nested uploads
(sync + async, the latter with `operation_name=`).
- **Challenges.** C11/C12/C13 count **1** each; C38 prohibited (`{x!r}`).
- **Owner + lifetime.** This file. Pure derivation, not cached.
- **Migration.** Stays. **Distinct behavior.** The base's builder is the
documented insufficiency (no `operationName`, empty nested maps — D-N4);
the no-`variables` guard reads the EMITTED member (stronger than the
base's `assert variables is not None` — the falsy-dict oracle proves the
split); graphene's `if operation_name:` truthiness is deliberately NOT
borrowed (fail-at-the-source).
- **Behavioral proof.** `static-reviewed` (12 node ids read). **Structural
gate.** Gate-only: the builder rows (each gate its own node ids); no new
gate. **Coupling.** FC1 (the reserved set's second spelling).
- **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] + [uploads-api][uploads-api] (consumer
census) + [spec-043][spec-043] + both upstream pins.

### F11 — placeholder walker (file-local)

- **Contract + variation.** `_assert_file_placeholders` verifies each
`files=` path resolves to a `None` placeholder in `variables`, walking the
post-serialization shape: dict (+ subclass) descent, list/tuple indexed
descent with canonical object-path indexes (`int()` guarded + `str(index)
!= segment` + range), empty segments refused, non-containers refused with
the UNIFORM `AssertionError` (never the TRY004-suggested `TypeError` — one
malformed call, one type), unreadable `len()` failed closed with the cause
chained, every message rendering through `_safe_arg_repr`. Varies by
container set (C14), index grammar (C15), key type (C16/D1).
- **Sites + roles.** *Definition*: :316–399 (sole path walker — the
`isdecimal` version guard and the budget walk are different domains, R12).
*Composed*: `_safe_arg_repr` (11 renders, D5). *Oracles*: top/nested
missing rows, the 4-id scalar row, the 6-id noncanonical row, the range
row, the not-`None` row, both hostile-`repr` rows (HEAD-only — hunt-deleted
in worktree), the 3-id empty-segment row, the tuple row, the hostile-`len`
row (HEAD-only).
- **Challenges.** C14/C15 count **1**; C16 **1** + D1.
- **Owner + lifetime.** This file. Pure walk, not cached. **Migration.**
Stays. **Distinct behavior.** The `(list, tuple)` closed set models
`json.dumps` rendering (verified against the tuple oracle — the JSON path
accepts the same values); the uniform-type clause is the D1 contract
source.
- **Behavioral proof.** `static-reviewed` for the pinned shapes;
`execution-verified` for D1's escape (workspace run
`dry-20260928T220857-cf276f`: `AttributeError` + 2 controls).
- **Structural gate.** Gate-only: the 22 walker node ids; no new gate.
- **Coupling.** D1 (filed, blocks nothing). **Freshness.** Target +
[test-client][test-client] + [spec-043][spec-043] pins; excluded:
[filters-sets][filters-sets]:440 (version domain),
[resource-policy][resource-policy]:544 (budget walk — R12).

### F12 — login bracket (file-local)

- **Contract + variation.** `login(user)` brackets a block as `user`:
`force_login` on entry, `logout` on exit, the logout in `finally` so a
raising block still clears the session. The async color wraps both session
writes in thread-insensitive `sync_to_async` (ORM work, no transaction, no
alias choice). Varies by arm (C18) and session scope (C17 → R1 trigger).
- **Sites + roles.** *Definition*: :401–414 + :464–475 (the package's only
`force_login` sites and only `.logout()` site — sweeps prove no twin).
*Oracles*: the sync clean-exit bracket (referenced via the live docstring —
bytes not inspected, verdict independent of it), the sync raise-logout
live, the async bracket live (denied/granted/denied-again), the async
raise-logout live.
- **Challenges.** C18 same-file; C17 fires R1's trigger (not fired today).
- **Owner + lifetime.** This file. Bracket-scoped session state; the
`finally` owns the cleanup lifetime. **Migration.** Stays. **Distinct
behavior.** Upstream's bracket has no `finally` (divergence, live-pinned);
the one-sync-boundary owner is the refused routing (R1/C37).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only:
the 3 read live bracket node ids (+1 referenced clean-exit row); no new gate. **Coupling.** R1 (standing
verdict, trigger stated).
- **Freshness.** Target + [test-client-api][test-client-api] +
[one-sync-boundary][one-sync-boundary] pins; the `sync_to_async(` code-call
census is exactly owner + these 2 sites (all other hits prose).

### F13 — async twin shape (file-local)

- **Contract + variation.** `AsyncTestClient(TestClient)` inherits the
builder, guards, tail, and transport, overriding only construction
(`AsyncClient()` default, presence-selected), the accessor annotation
(F6), the `query()` color (F7), and the `login()` color (F12). Drives
Django's in-process `AsyncClientHandler` — no `asgi.py`, no Channels.
Varies by default arm (C19).
- **Sites + roles.** *Definition*: class stmt :417 + `__init__` :427–428.
*Oracles*: the default-transport row (`AsyncClient`, not `Client`) + the
presence rows + every live async node id.
- **Challenges.** C19 count **1**.
- **Owner + lifetime.** This file. Construction-time. **Migration.** Stays.
- **Distinct behavior.** The shape mirrors upstream's subclass (verified at
external bytes); a sync transport under the async color (or vice versa)
fails loud as `TypeError` (caller error, upstream parity — near-miss
cleared, no contract row).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** None. **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] pins.

### F14 — mixin delegation (file-local)

- **Contract + variation.** `GraphQLTestMixin` composes over any
`TestCase`-family base, state-free beyond `GRAPHQL_URL` (default `None` →
falls through to setting → default): `query()` builds a `TestClient` over
the case's OWN `self.client` per call (login/cookie/CSRF state applies;
settings read at call time), keyword-only after the query string, with the
FLIPPED `assert_no_errors=False` default (graphene parity) and the
per-call `url=` forward (rung 1). Graphene's `input_data=` is deliberately
not carried (rewrite spelled out). Varies by state (C20) and surface
(C21).
- **Sites + roles.** *Definition*: `GRAPHQL_URL` :501 + `query` :503–534.
*Composed*: the delegate client (F5/F7/F9 — the mixin owns NO
body/decoding/endpoint logic, spec-043 D3/D10). *Oracles*: the delegation
row (bare-probe: reads only `self.client`), the 3 rung rows (class-attr /
per-call / call-time-settings), the live e2e (seeded + invalid + probe +
class-attr + smoke).
- **Challenges.** C20/C21 count **1** each.
- **Owner + lifetime.** This file. Per-call delegate construction (the
call-time-settings oracle pins no caching). **Migration.** Stays.
- **Distinct behavior.** Graphene binds `GRAPHQL_URL` at import from its
settings object; this file defaults `None` and reads live (divergence,
call-time oracle); graphene's positional order cannot survive the
`input_data` drop (spec-043 D10 — the kw-only signature is the uniform
replacement).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** R9 (the flipped default's standing refusal). **Freshness.**
Target + [test-client][test-client] + [test-client-api][test-client-api] +
[spec-043][spec-043] + graphene pins.

### F15 — assertion helpers (file-local)

- **Contract + variation.** `assertResponseNoErrors` asserts HTTP 200 AND
`errors is None`, failing with the decoded `{"errors","data"}` (or `msg`);
`assertResponseHasErrors` asserts non-empty `errors` with deliberately NO
status check (GraphQL returns 200 with errors), failing with the decoded
`data` (or `msg`). Graphene's names kept (N802 noqa'd), typed-`Response`
shaped. Varies by check (C22) and message shape (C23 → R10).
- **Sites + roles.** *Definition*: :536–555 (sole assertion vocabulary —
zero package twins). *Oracles*: 5 failure-direction rows (canned
responses, incl. the non-200-without-errors readability row and both
custom-`msg` rows) + the live passing directions.
- **Challenges.** C22 count **1**; C23 routes to R10.
- **Owner + lifetime.** This file. Pure checks. **Migration.** Stays.
- **Distinct behavior.** Graphene checks key absence (`assertNotIn`) over
raw content; this file checks `is None` over the typed shape — SPEC-OWNED
(spec-043 D10 pins `resp.errors is None`; near-miss cleared with contract
source). `extensions` stays out of the failure details (no contract
requires it — near-miss cleared).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** R10. **Freshness.** Target + [test-client][test-client] +
[test-client-api][test-client-api] + [spec-043][spec-043] + graphene pins.

### F16 — concrete combos (file-local)

- **Contract + variation.** `GraphQLTestCase` / `GraphQLTransactionTestCase`
are the two-line `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)`
combinations (spec-043 D3/D10) — Django's own commit split, unchanged.
Varies by combo (C24).
- **Sites + roles.** *Definition*: :558–568 (declarations only — zero new
machinery). *Oracles*: the live e2e classes (driven through the combos)
+ the `TransactionTestCase` smoke test.
- **Challenges.** C24 count **1** declaration.
- **Owner + lifetime.** This file. Class level. **Migration.** Stays.
- **Distinct behavior.** None — pure composition (principle 11: the
boundary names consumers depend on).
- **Behavioral proof.** `static-reviewed`. **Structural gate.** Gate-only.
- **Coupling.** None. **Freshness.** Target +
[test-client-api][test-client-api] + graphene pins.

### R1 — login bracket vs the one-sync-boundary owner (rejected, CONVERGE)

Considered shared form: run the async `login()` session writes through
`utils/querysets.py::run_in_one_sync_boundary`. Contract difference
(re-derived fresh at HEAD bytes): the bracket's hops are
thread-INSENSITIVE (`thread_sensitive` absent at :459/:463 — read, not
remembered), test-harness session writes outside any transaction and every
resolver surface; the owner's hop pins one `thread_sensitive=True` worker
per async operation for resolver ORM work. The code-level `sync_to_async(`
census is exactly owner + these 2 sites (all other package hits prose —
sweep re-derived, positive control hits). Trigger (verified R1's, re-checked
unfired): the test client ever needing transaction-pinned sessions — no
transaction, no boundary call, no `using=` in the full read. Durable homes:
the verified family artifact (R1) + this record; no source edit (file item
owes none). Challenges C17/C37.

### R2 — guard types vs sibling rejection grammars (rejected, CONVERGE)

Considered shared form: one rejection-type driver over this file's uniform
`AssertionError` guards, [testing-wrap][testing-wrap]'s `TypeError`, and
the policy per-subject grammars. Contract difference (fresh pair +
standing direction): each subject owns its type for its own reason — a
malformed TEST CALL fails as `AssertionError` so `pytest.raises`
catches every bad shape here (9 sites, oracle-pinned); a non-callable
WRAPPER fails as `TypeError` at the wrap site (spec-024 Decision 8);
policy subjects fail with their own grammars. C28 moves 1 per subject.
Trigger re-checked unfired for this pair: no unification appeared; both
sides' types/messages unchanged at HEAD vs the recorded verdicts (the
wrap side CLEAN; this side's 9 raises read). Durable homes: the
per-subject-rejection-grammars row + this record.

### R3 — unreadable-`len` guard vs a shared except driver (rejected, CONVERGE)

Considered shared form: route the walker's `except Exception` around
`len()` (:359–370) through a shared except-guard driver. Contract
difference: each site owns its guard + message + chain — here a hostile
`__len__` must fail as the guard's uniform `AssertionError` WITH the cause
chained (`from exc`), naming the path and segment (oracle pins
`match="unreadable length"` + the no-leak assertions). CONVERGE with the
standing J1 direction (each `except` site keeps its guard; witnessed at
`_request_body.py` J1 through the prior verified artifacts). Trigger
re-checked unfired: no shared driver exists; the arm's message/chain
contract is HEAD-pinned. Durable homes: the J1 row + this record. Note:
the worktree DELETED this arm (hunt) along with its oracle — the verdict
judges HEAD bytes; the deletion is concurrent-external dirt, not a
verdict change. Challenge C29.

### R4 — collection guard vs the conf function guard (rejected, fresh)

Considered shared form: one collection-guard helper for `:106`
(`__test__ = False` on a `Test*` CLASS — pytest would collect it as a
suite) and [conf][conf]'s `testing_endpoint_setting.__test__ = False` (a
`test*` FUNCTION returning `str` — pytest would collect it as a test and
fail on the return). Contract difference: different collection mechanisms,
different failure modes (suite-collect warning vs
`PytestReturnNotNoneWarning`), each fixed by a one-token assignment with
nothing shareable between them — no helper is conceivable, only two
adjacent comments (which already cite each other). Trigger: pytest
changing collection semantics for one shape but not the other (diverges
further, never merges) or a third guard site with a different mechanism.
Durable homes: both comments (each already names the other's hazard) +
this record. Challenge C4.

### R5 — module manifest vs the leaf manifest (rejected, fresh)

Considered shared form: one manifest for this file's 6-name `__all__` and
the leaf's 7-name `__all__` (the six + `safe_wrap_connection_method`).
Contract difference: each level owns its surface — the module declares
what it defines, the leaf declares what it re-exports (verified init-F1
owns the leaf side; the standing leaf-manifest direction holds across
orders/filters/rest-framework). A merged manifest would couple the
module's definition set to the leaf's export policy. C25 moves 1 + leaf
consumer rows. Trigger: a package-wide single-manifest mechanism (none
exists; every leaf owns its own). Durable homes: verified init-F1 + this
record. Challenge C36.

### R6 — endpoint ladder vs the policy ladder (rejected, fresh)

Considered shared form: one ladder driver for the F5 endpoint precedence
(URL selection across call/constructor/class/settings/default) and the
open `schema-construction-policy-ladder` (policy resolution across
explicit/settings/default). Contract difference: different domains (URL
strings vs policy records), different rung shapes, different
variation (a sixth endpoint rung vs a new policy source), different
consumers (test transports vs schema construction). The shared token is
the word "ladder", not a rule. C30 moves 1 per side. Trigger: a second
URL-selection ladder appearing (then the two URL ladders — not this pair —
are the candidate). Durable home: this record (the policy family item
judges its own side).

### R7 — multipart emit vs parse bodies (rejected, fresh)

Considered shared form: one multipart owner for this file's emit body
(builder + map + guards) and [views][views]' parse body (control-field
read + loss/charset/ordering enforcement). Contract difference: emitting
a valid envelope for the test process vs refusing invalid envelopes at
the serving boundary — different directions, reasons to change (a new
emit shape vs a new refusal), lifecycles (consumer utility vs permanent
wire policy), and failure postures (fail-at-the-source `AssertionError`
vs attributeless 400s). C31 moves 1 per side. The shared NAME SET is
explicitly NOT refused here — it routes to FC1. Trigger: the emit side
needing parse-grade refusal (or vice versa) — a collapse to one survivor,
never a merger. Durable homes: the builder docstring + the views guard
docstrings + this record.

### R8 — the three gate shapes (rejected, fresh, same-file separation)

Considered shared form: one gate shape for `operationName is not None`
(:273), `if variables:` (:276), `if not files:` (:281 + :240 + :202).
Contract difference: three domains — provided-vs-absent (an explicit `""`
is malformed-but-provided, sent for the server to reject), member-emission
(the falsy-dict oracle proves truthiness is load-bearing: a falsy mapping
holding a real placeholder is refused because the ENVELOPE is spec-invalid
without the member), mode-switch (three truthiness switches must agree or
`files={}` produces a mixed envelope — the JSON-post oracle pins the
agreement). C32 refused. Trigger: a fourth gate joining the builder (it
takes whichever of the three domains it belongs to — the split stands).
Durable home: the builder's gate comments (each already states its domain)
+ this record.

### R9 — flipped `assert_no_errors` default (rejected, fresh, same-file separation)

Considered shared form: one default for `TestClient.query()` (`True`) and
`GraphQLTestMixin.query()` (`False`). Contract difference (spec-owned):
each flavor matches its own upstream — strawberry-django raises,
graphene never auto-asserted and its documented flow is "call, then assert
helpers" (spec-043 D10: normalizing to `True` breaks every ported
`assertResponseHasErrors` test at the call site). C33 refused. Trigger: a
spec row retiring the graphene flow (or either upstream flipping its own
default). Durable homes: spec-043 D10 + both docstrings (each already
names the other's default) + this record.

### R10 — the two msg fallbacks (rejected, fresh, same-file separation)

Considered shared form: one fallback for NoErrors' `msg if msg is not None
else {"errors","data"}` (:544) and HasErrors' `msg or resp.data` (:555).
Contract difference: structured details (a mapping that must never be a
bare `None` — the non-200 readability oracle pins both fields riding the
message) vs graphene passthrough (`msg or content` is graphene's own
idiom, kept verbatim). C23 refused. Near-miss cleared inside the verdict:
falsy-but-provided `msg` behaves differently per helper and is unpinned
either way — no contract source distinguishes it, so no defect. Trigger: a
spec row pinning falsy-`msg` behavior. Durable home: this record.

### R11 — reserved intersection vs sibling intersections (rejected, fresh)

Considered shared form: one collision helper over the three `& set(`
sites: :303 (`{"operations","map"} & set(files)` → refuse shadowing),
`rest_framework/resolvers.py:1478` (save-kwarg shadowing),
`rest_framework/sets.py:667` (injected-field exposure). Contract
difference: disjoint populations, disjoint verdicts (refuse-a-key,
shadow-guard, exposure-set) — the `&` operator IS the sharing; no package
rule remains once the operands are parameters. C34 refused. Trigger: a
fourth site colliding on the SAME population as one of the three (then
those two — not this trio — are the candidate). Durable home: this record.

### R12 — placeholder walk vs the budget walk (rejected, fresh)

Considered shared form: one JSON-shape walker for F11 (single-path
descent verifying `None` placeholders, :316–399) and
[resource-policy][resource-policy]:544 (stack-based full traversal charging
untyped containers for width/nodes with no family classification).
Contract difference: verify-one-path vs charge-every-node — different
traversals, different verdicts, different inputs (test-call shapes vs
decoded input values). The shared token is `(list, tuple)` membership, a
Python idiom with 17 package hits, not a rule. C35 refused. Trigger: the
placeholder walk needing full-tree traversal (or the budget walk needing
path-keyed verification). Durable home: this record.

## Defects

### D1 — non-`str` `files=` key escapes the uniform guard as `AttributeError` (minor)

Owner: `django_strawberry_framework/testing/client.py::_assert_file_placeholders`
(:338 `key.split`). A `files=` key that is not a `str` (e.g. the int `0`
for a top-level list variable — a plausible typo for `"0"`) never reaches
a placeholder failure: `key.split(".")` raises `AttributeError: 'int'
object has no attribute 'split'`, escaping the documented uniform boundary
("`pytest.raises(AssertionError)` catches every bad shape"; the TRY004
clause promises one malformed-call type). Still fails loud — wrong type,
not silent — so minor. Wire input: `TestClient().query(m,
variables={"tags": [None]}, files={0: object()})`. Proof:
`execution-verified` — workspace run `dry-20260928T220857-cf276f`
(`AttributeError` observed; controls: valid path silent, bad `str` path →
uniform `AssertionError`). The `.split` line is byte-identical at HEAD
(:338) and worktree (:337), so the defect exists at both revisions. UNFIXED
(file item owes no production edit); Worker-0 homes it on a NAMED owning
card before closeout. Couples to nothing (C16 counts 1 + D1; no
consolidation depends on it).

Near-misses cleared (not defects — each checked against a contract source,
no card owed): N1 `errors: null` passes while graphene's key-check would
fail — spec-043 D10 owns `resp.errors is None`, cleared with contract
source. N2 falsy-`msg` differs per helper — unpinned either way, graphene
parity holds for the pinned shapes (R10). N3 transport/color mismatch
(sync-over-async or vice versa) fails loud as `TypeError` — caller error,
upstream parity, cleared. N4 `request()` says "provided" where the rule is
truthiness — the `files={}` JSON rule is stated explicitly and
oracle-pinned, cleared. N5 `extensions` absent from NoErrors details — no
contract requires it, cleared. N6 unconditional `headers=` — Django floor
is 5.2 (≥ 4.2 where the kwarg landed; pin HEAD-identical), cleared. N7
`AsyncTestClient` passes `AsyncClient` to a `Client | None` param
(`issubclass` is `False`, read-only probe) and narrows the `client`
property — upstream carries `# type: ignore`s there; no type gate exists
in CI (ruff + custom hooks only), runtime correct — latent annotation
tension, no contract row, cleared.

## Judgment

Zero-edit file item with one genuine cross-file count-2: the multipart
control-field name set (FC1 → holding family `multipart-control-field-names`;
C-FC1 moves the views tuple + this file's set). Everything else is
single-owned here (16 file-local rules, C1–C38 each count ≤1 or end refused,
with honest same-file participants) or a refused unification with a contract
difference + trigger (12 rejections: 3 convergences re-derived fresh with
triggers unfired — R1/R2/R3 — and 9 fresh). Enumeration covers 20/20
statements, 24/24 bound names, and 18/18 method/attribute members. One
minor HEAD defect filed (D1, execution-verified, unfixed), seven
near-misses cleared against contract sources, no pending execution, no
production edits. The ladder-order prose spanning five media is projection,
not definition — listed, never counted.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs `ITEM_BASELINE=0026ab6e573b7f9701e209c0f97938e89ddb3502`:
`git diff <baseline> --stat` names only `docs/dry/dry-0_0_15.md` (Worker-0's
own), `docs/review/review-0_0_15.md`, and
`django_strawberry_framework/_graphql_core_patches.py` (both concurrent
review-flow work, attributed by path, out of scope, left alone) — no hunk
in any path this item touches besides the artifact itself, so the item
never stopped. The target's worktree dirt (9 hunt hunks, `b1439443…` vs
HEAD `d8feebb2…`) predates the baseline, sits in neither the ledger nor the
cycle baseline, and was attributed by diff content as concurrent-external;
the trace judges HEAD bytes throughout. The artifact is a new untracked
file at the exact dispatched path `docs/dry/dry-file-testing__client.md`,
the item's only output. The `## Owned changes` ledger gains no row from
this item. No `uv run ruff` run (no `.py` touched; `.md` is outside ruff
scope; no `.py` scratch created). One workspace run
(`dry-20260928T220857-cf276f`, exit 0) + one read-only shared-tree `python
-c` (subclass check); no shared-tree pytest run (inspection + the oracles
settle every judgment except D1, which the workspace run proves). No
`docs/dry/temp-tests/` scratch created. No commit.

Worker-0 instructions: (a) tick the plan item `File testing/client.py` as
verified under Run `0.0.15 2026-09-28-7` once Worker 2 agrees; (b) add the
29 `## Responsibility index` rows under `## Index rows for Worker-0`
verbatim (holding item `File testing/client.py`, except the FC1 row whose
holding item is the new family); (c) add the `## Families` item under
`## Families`. No commit.

## Index rows for Worker-0

| `testing-client-module-mechanics` | `django_strawberry_framework/testing/client.py` (family docstring + 10 import statements + `TYPE_CHECKING` names + verified D-N1/D-N2/D-N3 absences) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-module-manifest` | `django_strawberry_framework/testing/client.py::__all__` (exactly the 6 client-family names) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-response-shape` | `django_strawberry_framework/testing/client.py::Response` (engine triple + raw `response` ride-along + assert-on-fields posture) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-collection-guard` | `django_strawberry_framework/testing/client.py::TestClient` (`__test__ = False`, inherited by the async twin — pinned on both) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-endpoint-ladder` | `django_strawberry_framework/testing/client.py::TestClient.__init__` (5-rung composition + presence selection + base `url` forwarding; setting + default composed from `conf.py`) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-wrapped-accessor` | `django_strawberry_framework/testing/client.py::TestClient.client` + `django_strawberry_framework/testing/client.py::AsyncTestClient.client` (byte-identical bodies, annotation-only delta — the pair is the rule) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-query-twin` | `django_strawberry_framework/testing/client.py::TestClient.query` + `django_strawberry_framework/testing/client.py::AsyncTestClient.query` (5 compat params + 2 keyword-only extensions over one shared builder + tail) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-finish-tail` | `django_strawberry_framework/testing/client.py::TestClient._finish_response` (shared uncolored `_decode` → `Response` → explicit-raise tail) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-request-transport` | `django_strawberry_framework/testing/client.py::TestClient.request` (per-call `url=` routing + content-type omission switch + dropped `format=` kwarg) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-body-builder` | `django_strawberry_framework/testing/client.py::TestClient._build_body` (gate trio + no-`variables` guard + uniform map rule + envelope; reserved set participates in FC1) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-placeholder-walker` | `django_strawberry_framework/testing/client.py::TestClient._assert_file_placeholders` (post-serialization walk + canonical indexes + uniform `AssertionError` + D1) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-login-bracket` | `django_strawberry_framework/testing/client.py::TestClient.login` + `django_strawberry_framework/testing/client.py::AsyncTestClient.login` (force-login/logout bracket pair, `finally` logout both colors) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-async-twin-shape` | `django_strawberry_framework/testing/client.py::AsyncTestClient` (subclass + `AsyncClient()` default over inherited builder/guards/tail) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-mixin-delegation` | `django_strawberry_framework/testing/client.py::GraphQLTestMixin` (`GRAPHQL_URL` + per-call delegate over `self.client` + flipped default, state-free) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-assertion-helpers` | `django_strawberry_framework/testing/client.py::GraphQLTestMixin.assertResponseNoErrors` + `django_strawberry_framework/testing/client.py::GraphQLTestMixin.assertResponseHasErrors` (graphene names, typed-`Response` checks) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-concrete-combos` | `django_strawberry_framework/testing/client.py::GraphQLTestCase` + `django_strawberry_framework/testing/client.py::GraphQLTransactionTestCase` (two-line combinations, zero new machinery) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `multipart-control-field-names` | TBD by family item (candidates: `django_strawberry_framework/views.py::_MULTIPART_CONTROL_FIELDS`, or a shared home both import — client must not inherit views' import weight) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/views.py` | Family `multipart-control-field-names` | open |
| `testing-client-login-vs-one-sync-boundary` | `django_strawberry_framework/testing/client.py::AsyncTestClient.login` (rejection recorded here; CONVERGE with verified `one-sync-boundary` R1 on fresh evidence — thread-insensitive, no transaction; trigger: transaction-pinned sessions) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/utils/querysets.py` | File `testing/client.py` | rejected |
| `testing-client-guard-type-vs-sibling-guards` | `django_strawberry_framework/testing/client.py::TestClient._assert_file_placeholders` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence; durable home the standing row) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/utils/policies.py` | File `testing/client.py` | rejected |
| `testing-client-len-guard-vs-shared-except` | `django_strawberry_framework/testing/client.py::TestClient._assert_file_placeholders` (rejection recorded here; CONVERGE with the standing shared-except-guard J1 direction on fresh evidence; HEAD-pinned message + chain) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | rejected |
| `testing-client-collection-guard-vs-conf-guard` | `django_strawberry_framework/testing/client.py::TestClient` (rejection recorded here; fresh pair, no prior verdict — different collection mechanisms, one token each, nothing to share) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/conf.py` | File `testing/client.py` | rejected |
| `testing-client-manifest-vs-leaf-manifest` | `django_strawberry_framework/testing/client.py::__all__` (rejection recorded here; fresh pair — each level owns its surface; standing leaf-manifest precedent noted) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/testing/__init__.py` | File `testing/client.py` | rejected |
| `testing-client-ladder-vs-policy-ladder` | `django_strawberry_framework/testing/client.py::TestClient.__init__` (rejection recorded here; fresh pair, no prior verdict — URL selection vs policy resolution) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/utils/policies.py` | File `testing/client.py` | rejected |
| `testing-client-emit-vs-parse-bodies` | `django_strawberry_framework/testing/client.py::TestClient._build_body` (rejection recorded here; fresh pair — envelope emission vs boundary refusal; the name set routes to FC1, not the bodies) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/views.py` | File `testing/client.py` | rejected |
| `testing-client-gate-trio-split` | `django_strawberry_framework/testing/client.py::TestClient._build_body` (rejection recorded here; same-file intentional separation — provided-vs-absent vs member-emission vs mode-switch) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | rejected |
| `testing-client-flipped-default-split` | `django_strawberry_framework/testing/client.py::GraphQLTestMixin.query` (rejection recorded here; same-file intentional separation, spec-043 D10 — each flavor matches its own upstream) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | rejected |
| `testing-client-msg-fallback-split` | `django_strawberry_framework/testing/client.py::GraphQLTestMixin.assertResponseNoErrors` (rejection recorded here; same-file intentional separation — structured details vs graphene passthrough) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | rejected |
| `testing-client-intersection-vs-sibling-intersections` | `django_strawberry_framework/testing/client.py::TestClient._build_body` (rejection recorded here; fresh pair, no prior verdict — the `&` operator is the sharing; populations + verdicts differ) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/rest_framework/sets.py` | File `testing/client.py` | rejected |
| `testing-client-walk-vs-budget-walk` | `django_strawberry_framework/testing/client.py::TestClient._assert_file_placeholders` (rejection recorded here; fresh pair, no prior verdict — single-path verify vs full-traversal charge) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/extensions/resource_policy.py` | File `testing/client.py` | rejected |

## Families

One item for Worker-0 to add (queue after the 11, per the run-7 queue
convention):

- [ ] Family `multipart-control-field-names` — [dry-rule-multipart-control-field-names.md](dry-rule-multipart-control-field-names.md) — no artifact on disk; undispatched

No adoption into an open family (the composed owners — engine base,
[conf][conf] setting, [exceptions][exceptions] renderer, the
`one-sync-boundary` owner — stay owned where they are; this file is their
by-name consumer and no index edit is owed for consumers).

## Independent verification (Worker-2)

Work order (worker-2.md): AGENTS.md, DRY.md, worker-2.md, the plan item
plus `## Run 0.0.15 2026-09-28-7`, the complete target at HEAD bytes
(`d8feebb2…`, 568 lines, extracted to `/tmp` and read whole; the worktree
`b1439443…` dirt diffed hunk-by-hunk first — 9 hunks: import retarget, 6
render-retarget hunks over 10 sites, 1 docstring reflow, 1 len-guard
deletion — so every cite below is HEAD-exact), the item-scoped window,
then the connected sites (testing leaf/wrap/relay, conf, exceptions,
views, strawberry-patches, both test tiers, graphql_client, uploads,
spec-043, the installed engine base, the one-sync-boundary rule
artifact), and only then this artifact's `## Findings`. Section 1 is the
pre-findings trace; section 2 reconciles every difference. Three
workspace runs at `dry/dry-file-testing__client/verify-1`, all exit 0:
`dry-20260928T222850-f592cc` (D1 probe), `dry-20260928T222908-275435`
(D1 body-level), `dry-20260928T223749-4297db` (N3 directions).

### 1. Own trace

Enumeration (own instrument, `ast` over HEAD bytes): 20 top-level
statements (docstring + future + 10 imports + TYPE_CHECKING if +
`__all__` + 6 classes); 24 names (mine: 18 import-bound including the
`annotations` future-flag and 3 TC-only + 6 class names); 18
method/attribute members (Response 1, TestClient 9, Async 4, Mixin 4,
combos 0+0). Every member homes to exactly one rule below.

Matrix (own discharge): (1) flavors — pytest client vs unittest mixin
vs engine base vs strawberry-django/graphene shapes (external, read);
no second package owner for any rule; (2) twins — query/query share
builder + tail with only the transport await colored (principle-5
exemplary), login/login share the finally-bracket, accessor pair
annotation-only; (3) derivations — endpoint default composed from
conf (no literal restated in code), member-emission read off the built
body, map rule computed from the key, messages via the owned renderer;
(4) round-trips — control-name pair spelled at client `:303`/`:314`
and views `_MULTIPART_CONTROL_FIELDS` (my sweep: no other package code
tokens; patches prose-only; consumers/relay/wrap zero) → 1 new family,
count 2; bodies separate; operationName write vs toolbar display-read
distinct; (5) media — spec-043 + 36 HEAD unit oracles + 13 live oracles
+ projections, ladder prose listed-never-counted; (6) omission —
colors share every guard by construction; the one uncovered shape
(non-`str` key → `AttributeError` off `:338`) is a minor defect;
deliberate absences (no `mutate()`, no `input_data=`, GRAPHQL_URL only
on the mixin, dict/list/tuple-only walk) each carry a contract source.

Homes I would choose: FC-new family `multipart-control-field-names`
(count 2: this file's one-edit region + the views tuple; owner TBD —
views cannot depend on consumer-test API, client must not inherit
views' weight); 16 file-local (mechanics, manifest, Response,
`__test__`, ladder, accessor pair as 2-spellings-1-rule, query twin,
tail, transport, builder, walker, bracket, async shape, delegation,
helpers, combos); convergences onto verified `one-sync-boundary` R1
(trigger: transaction-pinned sessions), per-subject-rejection-grammars,
shared-except-guard J1; fresh rejections for guard-vs-conf-guard,
module-vs-leaf manifest, ladder-vs-policy-ladder, emit-vs-parse bodies,
gate-trio split, flipped default, msg fallbacks, `& set(` trio,
placeholder-vs-budget walk; D1 minor filed unfixed; N1–N7 cleared.

### 2. Reconciliation — per-area verdicts

- Enumeration: AGREE (20/20 + 24/24 + 18/18, member-by-member). One
instrument note: W1 counts `__all__` as a name and excludes the
`annotations` future-flag; I counted the reverse. Total identical,
every member homed under both; W1's is the better instrument.
- Matrix: AGREE all six axes. Every census re-derived at HEAD:
`force_login` file-exclusive (5 hits), `.logout()` exactly 1 call
site, GRAPHQL_URL file + conf prose, operationName emitter only
`:274` (toolbar `:282` is a display read), 36 + 13 oracles, 13 =
1 import + 12 renders with zero `{x!r}`, D-N1/D-N3 target-zero with
package-wide positive controls (10 / 6 files), D-N2 zero runtime
importers outside testing/, `self._decode(` sole site, `& set(`
exactly the 3 cited lines.
- New family: AGREE (count 2, owner-TBD, import-weight constraint
sound, views `:143`/`:754` cites HEAD-exact, R7 split correct,
coupling to the REOPENED views item correct). Note n1: `:314` is
mislabeled a "consumer of the set" — it co-spells the literals
rather than reading `:303`. Same one-edit definition, so the count
stands; wording only.
- Convergences: AGREE on all three verdicts (homes, counts,
triggers re-checked unfired, incl. the `sync_to_async(` code census
= owner + these 2 sites, every other package hit prose). With
erratum E-W2-1 (below): R1/F12/C37 "thread-insensitive" is
behaviorally false — installed asgiref 3.11.1 defaults
`thread_sensitive=True` (`sync.py:425`), so the kwarg's absence is
true but the hops ARE thread-sensitive — and R1's `:459`/`:463`
are worktree bytes (HEAD `:471`/`:475`). The separation stands on
the remaining differences (no transaction, harness-only,
bracket-vs-one-boundary); the trigger is correctly stated and
genuinely unfired (no transaction/`using` in the full read). R2
(9 raises recounted; wrap `TypeError` side CLEAN-verified) and R3
(HEAD `:359`–`:370` + `match="unreadable length"` oracle read;
worktree deletion correctly judged dirt) agreed without note.
- Rejections R4–R12: AGREE all nine (difference + trigger + home
each, siblings re-read fresh: R11 pair at HEAD `:1478`/`:667`
with verdicts confirmed; R12 budget `:544` + `isdecimal` `:440`
HEAD-exact; the 17-count reproduced exactly for the
`isinstance`-form population — note n5). R5 correctly filed
fresh rather than converged (no prior verdict covers
module-vs-leaf). Note n6: R4's "each already names the other's
hazard" is half-wrong — conf's comment names the client side,
but the client's comment names upstream, not conf. Verdict
unaffected (difference + trigger sound; spec edge-case prose is
the contract source for both).
- D1: ENDORSE as filed (minor, unfixed, clean-line). Trust-boundary
test passes: contract row = the uniform-`AssertionError` clause
(walker docstring + TRY004 note); feasible shape = `files={0: f}`
via supported `TestClient.query`; reaching input = the call arg;
still loud (wrong type, not silent). Proven by W1's run plus my
two runs; the `.split` line byte-identical at both revisions
(HEAD `:338`, worktree `:337`).
- Near-misses N1–N7: AGREE all clearances, each re-checked: N1
spec-043 pins `res.errors is None`; N2 no contract source either
way; N3 clearance stands with corrected precision — execution
shows async-over-sync `TypeError` but sync-over-async
`AttributeError`, both loud caller errors (note n7); N4 the
truthiness rule is explicit in-module + oracle-pinned; N5 no
contract; N6 Django floor `>=5.2.16` HEAD-identical, `headers=`
since 4.2; N7 runtime-correct, no type gate in CI.
- Index rows: AGREE 29/29 match their findings
(16 file-local + 1 open + 12 rejected); Families item
format-correct. Transcription directions for Worker-0: (a) the
R1 row must not carry "thread-insensitive" — transcribe as
"kwarg-absent (thread-sensitive by default), no transaction;
trigger: transaction-pinned sessions"; (b) the F6 row
"byte-identical bodies" overstates — the docstrings differ
(Client vs AsyncClient); transcribe as "identical return lines,
annotation + docstring delta".

Further record notes (all immaterial, none moving a home/count):
n3 F8 "(D1 ground 2)" mislabels Decision 5 ground 2 (D-N4's
justification); the insufficiency itself is documented + verified.
n4 the obligation range "D-N1–D-N3" omits D-N4, which F10
nevertheless cites and discharges correctly (base folder heuristic
verified at installed bytes). n8 the dirt note's "8 render
call-site retargets" is 10 (`truth.render` worktree count; 12
HEAD renders minus the 2 deleted with the len arm); the 9-hunk
count is exact. n9 the test-dirt author split (hunt vs
maintainer) is unevidenced — all of it is concurrent-external
regardless (3 hostile-oracle deletions verified absent in
worktree + the 1 message-string rework read). n10 FC1's
views-side oracles are explicitly not inspected and routed to
the family item — acceptable routing for a file item.

### 3. Freshness repairs (inputs W1 read but did not pin)

Per the run-7 wrap precedent, repaired in my section with regions
re-verified at HEAD bytes: `rest_framework/resolvers.py`
H `0d302782…` W `c49ce3c2…` (R11 `:1478` shadow guard);
`rest_framework/sets.py` H `2c4c4930…` W `2b88fe58…` (R11 `:667`
exposure set); `extensions/resource_policy.py` H `19e2309d…` W
`0134d83a…` (R12 `:544` budget walk); `filters/sets.py` H
`993e887a…` W `e47c6758…` (F11 exclusion `:440`); `middleware/debug_toolbar.py`
H `5360149b…` W `ffda621e…` (operationName display read `:282`).
Every W1-table pin re-derived digit-for-digit (target, init, wrap,
relay, conf, exceptions, views, patches, both test tiers,
graphql_client, uploads, spec-043, glossary, CHANGELOG, README,
TREE, all four untracked artifacts, installed base `f2abe800…`
at strawberry-graphql 0.324.0).

### 4. Window, ruff, pending execution, cells

Window vs `ITEM_BASELINE=0026ab6e…`: the plan (Worker-0's dispatch
record), `docs/review/review-0_0_15.md` (concurrent review-flow:
graphql-patches tick + strawberry-patches dispatch + ledger row +
drift line), `django_strawberry_framework/_graphql_core_patches.py`
(one pragma-comment wording hunk, matching the review record) —
all re-attributed hunk-by-hunk as concurrent/out-of-scope; the
untracked artifact is this item's only output. Zero `.py` touched
→ ruff not owed (confirmed, not run). `## Pending execution`
absent = correct (no `proof:`/`gate:` owed; D1's proof is
execution-verified). Cells: the D1 proof path is DB-free (no ORM,
alias, or dialect decision) → sharded/PG inapplicable by
construction, stated here to close the Tests clause W1 left
implicit.

### 5. Verdict

Zero-edit file item, fully homed, one genuine count-2 holding
family, three sound convergences, twelve sound rejections, one
endorsed minor defect, seven sound clearances. No W2 defects. The
E-W2-1 erratum and notes above are record-level and move no
home, count, trigger, or defect verdict; Worker-0 may apply the
E1-precedent in-place wording corrections (3 W1-text occurrences:
F12, R1, C37) and must apply the two transcription directions.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../CHANGELOG.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[init-artifact]: dry-file-testing____init__.md
[one-sync-boundary]: dry-rule-one-sync-boundary.md
[tree]: ../TREE.md
[views-artifact]: dry-file-views.md
[wrap-artifact]: dry-file-testing___wrap.md

<!-- docs/SPECS/ -->
[spec-043]: ../SPECS/spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[strawberry-patches]: ../../django_strawberry_framework/_strawberry_patches.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-client]: ../../tests/testing/test_client.py

<!-- examples/ -->
[graphql-client]: ../../examples/fakeshop/graphql_client.py
[test-client-api]: ../../examples/fakeshop/test_query/test_client_api.py
[uploads-api]: ../../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Run-8 scoped re-trace (Worker 1, s13)

Run: 0.0.15 2026-09-30-8. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh at the
sibling-base topology: scopes the drift delta commit by commit,
CONFIRMs or REVISEs every run-7 finding (19 CONFIRM + 10 REVISE),
re-derives the client rules citing their new homes, re-pins D1 by
execution, files one new doc-only defect, and attributes every
worktree hunk by content. Zero production edits; zero tracked files
changed.

### Scope and fingerprints

Drift base `0c0537e2` is an ancestor of HEAD `83998e08`
(`83998e08d48c911199527ed0411ab8041805c8b5`, verified at start and
again unmoved at finish). Three states fingerprinted (`git rev-parse`
/ `git hash-object`; line counts from `git show` bytes):

- Drift base `0c0537e2:testing/client.py` blob `d8feebb2` (568 lines;
  == run-7 HEAD — run-7 traced the drift base).
- HEAD `testing/client.py` blob `2466edae` (635 lines).
- Worktree blob `2d9aa737` (623 lines) vs HEAD: 6 hunks, 15+/27-, the
  hunt truth-migration + the len-guard deletion by content (attributed
  below); `ITEM_BASELINE=94b57959…`
  (`94b5795928a9130da8df1f344e3854ba3f646ebc`) resolves and its target
  blob equals the worktree blob, so every hunk pre-dates the item.
- Pre-merge `9aaaad5d:testing/client.py` blob `b1439443` (== run-7
  worktree: truth-adopted, pre-drift).

Committed delta since the drift base is exactly five commits
(`git log --oneline 0c0537e2..HEAD -- <target>`), in order:

- `999a1aab` (53+/13- on target): `TypedDict`/`Protocol` shells,
  `_User`, `cast`s, the `_ClientPostKwargs` kwargs type, the 4
  async-twin `type: ignore`s. Runtime-neutral (annotations, casts
  and comments are inert).
- `b20277fe` (17+/12-): `Any`→`object`, `Mapping` variables,
  accessor casts. Runtime-neutral.
- `1a17dca5` (behavior-bearing): siblings over
  `_GraphQLTestClientBase`; removes the 4 ignores; every body moved
  verbatim (verified hunk-by-hunk: finish/request/builder/walker/
  query/login bodies identical modulo the typing above; the
  `__init__` split preserves presence semantics on both arms). The
  ONE observable change: `issubclass(AsyncTestClient, TestClient)`
  is now `False` (commit message + three code docstrings record it).
- `849f67bc` (5+): the `override` import + 4 markers.
  Runtime-neutral (attribute marker).
- `fef11e64` (8+/3-): Protocol `...` → docstrings (`TYPE_CHECKING`
  only). Runtime-neutral.

Total drift `0c0537e2..HEAD`: 182+/115-. The four oracle/consumer
files carry zero drift commits (byte-identical to run-7 pins).

Fingerprint table (`H` = HEAD blob, `W` = worktree hash, `S` =
`9aaaad5d` blob; short hashes):

| Input | H | W | S | State |
|---|---|---|---|---|
| `testing/client.py` (target) | `2466edae` | `2d9aa737` | `b1439443` | drift + hunt dirt, traced at HEAD |
| `testing/__init__.py` | `48b45d1b` | same | same | CLEAN |
| `testing/_wrap.py` | `9351a74e` | same | `0df97813` | typing drift, zero tokens re-swept |
| `testing/relay.py` | `8e5f9c9d` | `0c48f0a9` | `f807bf92` | typing drift + dirt, zero tokens re-swept |
| `conf.py` | `10096f84` | `8092d80b` | `3820c575` | typing drift, judged region intact |
| `exceptions.py` | `f27e1f91` | `34e2e6be` | `93401220` | typing drift, renderer byte-identical |
| `views.py` | `60dea561` | `efaa57ff` | `48ee582e` | drift + dirt, FC1 region intact |
| `_strawberry_patches.py` | `1e9323ac` | `3b2da766` | `90f711fb` | prose-only mention, re-verified |
| `tests/testing/test_client.py` | `fe01478e` | `517cf1e6` | `517cf1e6` | H == run-7 H; W == run-7 W |
| `test_query/test_client_api.py` | `4a04369d` | same | same | CLEAN |
| `graphql_client.py` | `3cd94f4b` | same | same | CLEAN |
| `test_query/test_uploads_api.py` | `dcbcbf61` | same | same | CLEAN |
| `spec-043-test_client-0_0_14.md` | `7797a2fe` | same | `a31a06f1` | 3 citation re-homes; D8 text stale (D2) |
| `spec-043-rationale.md` | `a7c3049e` | same | `450a7107` | 1 re-home; D8 + 1 cite stale (D2) |
| `docs/GLOSSARY.md` | `431ca7ba` | same | `3413edc3` | drift elsewhere, entries re-read intact |
| [CHANGELOG][changelog] | `d4e10355` | same | same | CLEAN |
| `docs/README.md` | `a3deca98` | `cdb927d5` | `30978c34` | drift elsewhere, testing lines intact |
| `docs/TREE.md` | `163e364b` | `1a5b528b` | `5c9d6066` | projection-only, verdict-independent |
| `middleware/debug_toolbar.py` | `0d8019e1` | `d7906f94` | `ffda621e` | display read re-pinned `:292` |
| `filters/sets.py` | `3d307402` | `ec278851` | `e47c6758` | exclusion re-pinned `:459-464` |
| `extensions/resource_policy.py` | `5cc373ec` | `8944e79e` | `0134d83a` | budget walk re-pinned `:515/:524` |
| `rest_framework/resolvers.py` | `420fc3ca` | `3fc6a366` | `c49ce3c2` | R11 sibling re-pinned `:1555` |
| `rest_framework/sets.py` | `8fa4b52a` | `bde23da9` | `2b88fe58` | R11 sibling re-pinned `:696` |
| `types/resolvers.py` | `574e9768` | `7a953c53` | `640905c6` | R1 census sites `:642/:715/:786` |
| `schema.py` | `bba03d7d` | `abad5795` | `f4e807e9` | R1 census sites `:394/:406` (new) |
| `utils/querysets.py` | `392e50d0` | `cfc773ba` | `8fc556d5` | R1 owner `:536` |
| installed `strawberry/test/client.py` | `f2abe800` | — | — | 0.324.0, == run-7 |
| strawberry-django `test/client.py` | md5 `ad7a1131` | — | — | external, == run-7 |
| graphene `utils/testing.py` | md5 `2e441da3` | — | — | external, == run-7 |

Method: every claim reads HEAD bytes (`git show HEAD:` + AST over
that text via `/tmp/s13_head_client.py`, pure reads); worktree-state
claims read the shared worktree file; the D1/topology/guard probe ran
in the disposable copy at `dry/client-retrace-s13/probe` (run
`dry-20260930T171751-553aa2`, exit 0, copy fresh). No shared-tree
pytest; no `.py` scratch in the repo.

### Enumeration at HEAD bytes

Instrument: `ast.parse` over the HEAD blob (`2466edae`, 635 lines),
counting `ast.Module.body` members — **23 top-level statements**
(base 20 + exactly 3: the `override` import, the `_ClientT` assign,
the base class), binding **35 module-level names** (18 import-bound
+ 8 `TYPE_CHECKING`-only incl. 2 class shells + `__all__` + `_ClientT`
+ 7 class statements), with **18 method/attribute members** — the same
18 as run-7, re-homed (1 + 7 + 3 + 3 + 4 across Response, the base,
the two leaves, the mixin). Every member lands below. Line numbers
are HEAD bytes (`:NN` scratchpad convention).

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (siblings sentence reworded; ladder order intact) | (none) | prose, F1 |
| 1 | `from __future__ import annotations` | (none) | F1 |
| 2 | `import contextlib` | `contextlib` | F1 (consumed by F12) |
| 3 | `import json` | `json` | F1 (consumed by F10) |
| 4 | `from dataclasses import dataclass` | `dataclass` | F1 (consumed by F3) |
| 5 | `from typing import … Generic, TypeVar, cast` | 5 names | F1 |
| 6 | `from asgiref.sync import sync_to_async` | `sync_to_async` | F1 (consumed by F12) |
| 7 | `from django.test import …` | 4 names | F1 |
| 8 | `from strawberry.test import BaseGraphQLTestClient` | `BaseGraphQLTestClient` | F1 |
| 9 | `from strawberry.test.client import Response as _EngineResponse` | `_EngineResponse` | F1 (consumed by F3) |
| 10 | `from typing_extensions import override` | `override` | F1 (F7/F9/F10 markers) |
| 11 | `from ...conf import testing_endpoint_setting` | `testing_endpoint_setting` | F1 (consumed by F5) |
| 12 | `from ...exceptions import _safe_arg_repr` | `_safe_arg_repr` | F1 (consumed by F10/F11) |
| 13 | `if TYPE_CHECKING:` (3 abc + 2 typing + `_User` + 2 shells) | 8 names | F1 |
| 14 | `__all__` (6 names) | `__all__` | F2 |
| 15 | `_ClientT = TypeVar(…)` | `_ClientT` | F1 (consumed by base/F5/F6) |
| 16 | `class Response(_EngineResponse)` + `response` field | `Response` | F3 |
| 17 | `class _GraphQLTestClientBase(…)` (7 members) | base | guard→F4; `__init__`→F5; `client`→F6; `_finish_response`→F8; `request`→F9; `_build_body`→F10 (+FC1); `_assert_file_placeholders`→F11 |
| 18 | `class TestClient(_GraphQLTestClientBase[Client])` (3 members) | `TestClient` | `__init__`→F5; `query`→F7; `login`→F12 |
| 19 | `class AsyncTestClient(_GraphQLTestClientBase[AsyncClient])` (3 members) | `AsyncTestClient` | class stmt + `__init__`→F13; `query`→F7; `login`→F12 |
| 20 | `class GraphQLTestMixin` | `GraphQLTestMixin` | `GRAPHQL_URL` + `query`→F14; both helpers→F15 |
| 21 | `class GraphQLTestCase(GraphQLTestMixin, TestCase)` | `GraphQLTestCase` | F16 |
| 22 | `class GraphQLTransactionTestCase(…)` | `GraphQLTransactionTestCase` | F16 |

### Worktree-dirt attribution (all 6 hunks, by content)

All concurrent-external: no `## Owned changes` ledger row names this
file (verified by a `testing/client` grep over the plan — hits are
index rows + dispatches only), and every hunk pre-dates the item
(ITEM_BASELINE blob == worktree `2d9aa737`). Content is the hunt
`truth` migration + the len-guard deletion — run-7's dirt rebased
onto the sibling topology (worktree-vs-`9aaaad5d` is the drift plus
this same migration):

- H1 (`@@ -42`): the import retargets `_safe_arg_repr` → `truth`.
- H2 (`@@ -268`): the reserved-message render → `truth.render`.
- H3 (`@@ -297`): the walker docstring drops the len-guard
  sentence (follows H5).
- H4 (`@@ -312`): the empty-segment render → `truth.render`.
- H5 (`@@ -325`, 30→19): the `len()` guard arm DELETED (message +
  `from exc` chain) with `size = len(current)` direct; the index +
  dict renders → `truth.render`.
- H6 (`@@ -357`): the descend + not-`None` renders (4 sites) →
  `truth.render`.

Render math: HEAD 1 import + 12 renders; worktree 1 import + 10
`truth.render` (12 minus the 2 deleted with the len arm) with zero
`_safe_arg_repr` — the run-7 W2-n8 shape, re-derived. Every judgment
below holds at HEAD bytes; D1 + the topology + guard inheritance
also hold at worktree bytes (the probe ran worktree bytes; the D1
line is byte-identical at HEAD :307 / worktree :306).

### D1 re-verification (execution-verified re-pin)

One workspace run at `dry/client-retrace-s13/probe`
(`dry-20260930T171751-553aa2`, exit 0, copy fresh, shared unmoved):
`/tmp/s13_d1_probe.py` (read-only, DB-free — the pure staticmethod
plus class topology, no settings, no queries) observed
`AttributeError: 'int' object has no attribute 'split'` for
`files={0: object()}`, silence for the valid path, the uniform
`AssertionError` for the bad `str` path, `issubclass` `False` in
both directions between the leaves with both subclassing the base,
and `__test__ is False` on both leaves inherited (absent from both
`__dict__`, present on the base). Fresh slots cannot import the
package unaided (see Infrastructure note), so the run carries
`PYTHONPATH=<shared-venv site-packages>` to supply the missing
`typing_extensions` 4.15.0 shim — the imported `client.py` is the
copy's own file (provenance header + `m.__file__`), the package
digest matches, the copy stayed fresh, and the command is recorded
verbatim in the run log. The D1 line (`for segment in
key.split("."):`) is byte-identical at HEAD :307 and worktree :306,
so the defect exists at both revisions. D1 persists; routing
unchanged (closeout homing).

### CONFIRM verdicts (file-local: F2 F3 F7 F12 F14 F15 F16)

- F2 manifest: the 6-name `__all__` (:81-88) + the leaf consumer
  (leaf byte-identical) + the export oracle (byte-identical). Count
  1. STANDS.
- F3 Response: the class body is untouched by drift (no hunk). The
  engine triple stays composed (installed base byte-identical
  `f2abe800`). STANDS.
- F7 query twin: both colors intact (:396-460 / :493-521) over the
  shared builder + tail (now via the base), `@override` added, the
  async docstring still references the sync contract. C7/C8 counts
  intact. STANDS.
- F12 login bracket: one bracket per leaf (:462-475 / :523-534),
  `finally` logout both, `force_login` package-exclusive (5 hits,
  this file only), `.logout()` sole code site :475. E-W2-1 carries
  (kwarg-absent, thread-sensitive by default). STANDS.
- F14 mixin: `GRAPHQL_URL` :560 + the forward :562-593 (sole
  in-package `TestClient(` construction :584); `self:
  _GraphQLTestHost` is annotation-only. D10 + oracles byte-identical.
  STANDS.
- F15 helpers: both bodies byte-identical (:595-622); graphene names
  + typed checks. STANDS.
- F16 combos: both declarations untouched (:625-635). STANDS.

### CONFIRM verdicts (FC1)

FC1 control-field name set: count **2** — this file's one-edit
region (:267 definition + :280 emission co-spelling + the :271
message mention; W2-n1 carries) and the [views][views] tuple (:162,
iterated :797-800, body re-read identical). Population re-closed at
HEAD: every other package `operations` hit is prose, a message
string, or another domain (GraphQL/mutation/execution `operations`,
schema `allowed_operations`, the patches hits prose-only including
the :686 message literal). The R7 body split holds. STANDS, owner
still TBD by the family item.

### CONFIRM verdicts (rejections R2-R12)

- R2 guard types: 9 `raise AssertionError` recounted here; the wrap
  `TypeError` :139 intact across typing-only drift; the standing
  per-subject row holds. Trigger unfired. STANDS.
- R3 len guard: the arm is intact at HEAD :328-339 (`from exc` +
  message); its oracle is byte-identical. The worktree deletion is
  dirt (H5). STANDS.
- R4 collection vs conf guard: one token each, different mechanisms.
  Conf's comment cite of `testing/client.py::TestClient` still
  resolves via inheritance (probe-proven `TestClient.__test__ is
  False`) — imprecise, not wrong (record note, no defect: the
  attribute exists). STANDS.
- R5 manifests: module vs leaf levels unchanged; the leaf file is
  byte-identical. STANDS.
- R6 ladders: URL selection vs policy resolution; the policy family
  is untouched by drift. STANDS.
- R7 emit vs parse: the bodies stay separate; the name set routes to
  FC1. STANDS.
- R8 gate trio: `is not None` :237 / truthiness :240 / mode-switch
  :245 with :201/:162 agreeing; the `files={}` oracle is
  byte-identical. STANDS.
- R9 flipped default: `True` (:403/:500) vs `False` (:571); D10
  intact. STANDS.
- R10 msg fallbacks: both bodies byte-identical (:607 vs :622).
  STANDS.
- R11 intersections: exactly the 3 `& set(` sites, re-pinned — :267
  (refuse-a-key) vs `rest_framework/resolvers.py:1555` (save-kwarg
  shadow guard, verdict re-read) vs `rest_framework/sets.py:696`
  (injected-field exposure set, re-read). The `&` IS the sharing.
  STANDS.
- R12 walks: single-path verify (:282-368) vs full-traversal charge
  (stack entry :515, loop :524, node/depth/width arms re-read).
  STANDS.

### REVISE verdicts (F1 F4 F5 F6 F8 F9 F10 F11 F13 R1)

- F1 mechanics: 12 import statements binding 18 runtime names
  (+`override`, `Generic`/`TypeVar`/`cast`), a `TYPE_CHECKING` block
  binding 8 names (2 class shells), +`_ClientT` :92. D-N1/D-N3 zero
  re-derived in-target; D-N2 zero runtime importers re-derived
  package-wide. The absences hold; the census is revised.
- F4 guard: the owner moved `TestClient` → the base (:126-130, the
  comment reworded to both names); both siblings inherit it
  (probe-proven); the oracle asserts both (byte-identical). Guard
  parity is with strawberry-django's `test/client.py:16` (external
  md5 unchanged); installed strawberry 0.324.0 carries no `__test__`
  (whole `strawberry/test/` grepped) — a precision note, verdict
  unaffected.
- F5 ladder: the `__init__` split — base :132-138 (path presence +
  `url` forwarding, both args required) + per-leaf transport
  defaults (:393-394 `Client()`, :490-491 `AsyncClient()`). Five
  rungs, presence selection, non-persistence: unchanged, oracles
  byte-identical. Owner cites revised.
- F6 accessor: the pair is GONE — one generic `client` (:140-144)
  with `cast` on the base. C6 revises 2 spellings → 1; the
  "pair is the rule" shape is superseded by construction (W2's
  transcription correction is moot). The rule is now single-sited
  here.
- F8 tail: moved → the base verbatim (:146-174); the sole
  `self._decode(` site :162; both raise directions pinned by
  byte-identical oracles. Re-homed.
- F9 transport: moved → the base (:176-206);
  `_ClientPostKwargs` + the headers-narrowing ignore comment are
  runtime-inert; the omission switch + the dropped `format=` are
  intact; the mixin forward is the sole in-package construction.
  Re-homed.
- F10 builder: moved → the base (:208-280); `Mapping`/`object`/
  `cast` are runtime-neutral; every gate + the map rule + the
  reserved set intact; FC1 participant. Re-homed.
- F11 walker: moved → the base (:282-368); D1 re-pinned :307
  (execution-verified); the `isdecimal` exclusion re-pinned
  ([filters-sets][filters-sets] :459-464, version domain).
  Re-homed.
- F13 async shape: subclass → SIBLING (:478). The `isinstance`
  break is real and documented (:485-487) but unreferenced — zero
  subclassers + zero `isinstance`/`issubclass` hits package-wide
  (1 docstring mention). The contract source moves: spec-043
  Decision 8 still pins the port (see D2); the live record is the
  `1a17dca5` rationale + the three code docstrings.
- R1 one-sync-boundary: the verdict STANDS (harness-only session
  writes, no transaction; the trigger is unfired — the full
  635-line read has no transaction/`using`), but the code-level
  `sync_to_async(` census is CORRECTED: the owner
  (`utils/querysets.py:536`) + `types/resolvers.py` ×3
  (:642/:715/:786) + `schema.py:406` (new in drift) + this file ×2
  (:530/:534), plus `async_to_sync(` at `schema.py:394` (new).
  The prior "exactly owner + 2" was already wrong at the drift
  base — the types/resolvers trio (`ddd5dbb9`, 2026-08-23)
  predates the run-7 trace. Slip corrected; the separation is
  unaffected. (E-W2-1 + the W2 transcription direction carry.)

### Challenges and matrix deltas

C6 revises (1 spelling, same file); C16 re-pins (:307 + D1); C4 /
C17 / C37 carry their rejections with the notes above; every other
C-count (C1-C3, C5, C7-C15, C18-C36, C38, C-FC1) holds with re-homed
cites — each still ≤1 or refused as recorded. Matrix,
re-discharged at HEAD: (1) the three testing modules stay disjoint
(wrap/relay zero client tokens re-swept at HEAD; the leaf is a
byte-identical consumer); no second client, bracket, mixin, or
assertion-helper site (sweeps above); the mixin forward is the sole
in-package construction; (2) both colors share builder + tail below
the color line, the bracket pair shares `finally`; (3) the endpoint
default, `url=`, member emission, map rule, and `_safe_arg_repr`
(13 hits = 1 import + 12 renders, zero `{x!r}`) are composed, never
re-derived; (4) FC1 count 2 with R7 bodies separate, `_decode` sole
site :162; (5) the contract source (3 citation re-homes) + 36 unit
oracles + 13 live oracles (files byte-identical) + projections
([glossary][glossary] entries + [docs-readme][docs-readme] ladder
prose re-read intact at drifted blobs); (6) both colors share every
guard by construction; the one uncovered shape is D1; the deliberate
absences (no `mutate()`, no `input_data=`, mixin-only
`GRAPHQL_URL`, dict/list/tuple-only walk) hold with contract
sources.

### Defects

- D1 (persists, minor): a non-`str` `files=` key escapes the uniform
  guard as `AttributeError` (:307 `key.split`). Re-pinned by
  execution (run `dry-20260930T171751-553aa2` + the HEAD/worktree
  byte-bridge). UNFIXED; closeout homing still owed. Couples to
  nothing.
- D2 (NEW, minor, doc-only): [spec-043][spec-043] Decision 8 (:1220,
  "subclasses … Pinned: the port") + rationale D8 (:518-531, "IS
  the sync client", flat base rejected) still pin the shape
  `1a17dca5` reversed; the reversal lives only in the commit message
  + the code docstrings. Companion: rationale :179 keeps a stale
  `::TestClient._assert_file_placeholders` short-cite while its
  sibling cite on the same line was re-homed (half-applied). No wire
  input reaches a spec sentence — not a release blocker
  (trust-boundary rule); closeout homes it (a spec-text update, or a
  ruling that commit + docstrings are the record). Couples to F13's
  contract source only.

Near-misses: N1/N2/N4/N5 clearances CONFIRM (regions + oracles
byte-identical); N3 CONFIRMS (both color-mismatch paths
verbatim-moved, W2's TypeError/AttributeError precision carries as
static-carry); N6 CONFIRMS (`Django>=5.2.16` re-read at HEAD
pyproject :34, `headers=` since 4.2); N7 is RESOLVED by construction
(the 4 ignores removed in `1a17dca5`, verified in-commit; each
concrete `__init__` names its own transport; the remaining :206
ignore is headers-narrowing, runtime-inert, unrelated) — closed, not
merely cleared.

Record notes (immaterial): conf's guard comment cites
`::TestClient` (resolves via inheritance — R4); W2-n1/n3/n4/n6-n10
carry (n8's arithmetic re-derives as 12−2=10 at this worktree).

### Infrastructure note (copy venv; no verdict impact)

Fresh run-8 slots cannot import the package: `uv sync --frozen
--group pg` exits 0 yet the venv lacks `typing_extensions`
(`ModuleNotFoundError` on `import strawberry`; reproduced in two
fresh slots at both copy addresses). The lock pins 4.15.0, the
shared venv has it, and `pyproject.toml` dirt is a config block
only. Execution evidence above was obtained via a disclosed
`PYTHONPATH=<shared-venv site-packages>` shim (the copy's own
module file imported, digest match, copy fresh — the run log
records the command verbatim). Worker-0: this item's proofs stand,
but the gate and later execution items need a working slot venv.

### Pending execution

None owed. D1 is execution-verified; the proof path is DB-free (no
ORM, alias, or dialect decision) → sharded/PG inapplicable by
construction. No pytest per dispatch.

### Judgment

Zero-edit re-trace: 19 CONFIRM (7 file-local + FC1 + 11 rejected) +
10 REVISE (9 file-local + R1) — every prior row accounted for. The
drift's new shape (sibling base, one generic accessor, split
`__init__`, the `isinstance` break) is homed; every moved body is
verbatim with behavior-neutral typing; oracles + leaf + CHANGELOG
are byte-identical; projections re-read intact. D1 persists
(execution-verified, still closeout-homed); D2 filed (doc-only,
closeout-homed); N7 closed by construction. No new family, no
adoption; the FC1 holding stands. No production edits.

## Implementation (Worker-1, run-8 s13)

No tracked changes made (zero-edit re-trace submitted for
verification). Item-scoped attribution vs
`ITEM_BASELINE=94b5795928a9130da8df1f344e3854ba3f646ebc`: the
artifact path is untracked (never in the baseline diff) and
`git diff <baseline> -- <target>` is empty (baseline blob equals
worktree `2d9aa737`), so the item never stopped; the `## Owned
changes` ledger names no path this item touches (grep-verified) and
gains no row. The artifact diff is the `Status:` swap + this append
(prior sections byte-preserved). No `uv run ruff` run (no `.py`
touched; `.md` is outside ruff scope; probes live in `/tmp`).
Workspace runs at `dry/client-retrace-s13/consolidate` (diagnostic
probes of the venv defect) + `dry/client-retrace-s13/probe`
(`dry-20260930T171726-106470` import check,
`dry-20260930T171751-553aa2` D1 probe, both exit 0). No shared-tree
pytest run. No commit.

Worker-0 instructions: (a) tick `File testing/client.py` back to
verified under `Run: 0.0.15 2026-09-30-8` once Worker 2 agrees; (b)
apply the 17 `## Index rows for Worker-0 (run-8 s13)` revised rows
as exact replacements (10 verdict/shape revisions + 7 path-only
anchor re-homes); (c) home D1 (unchanged) + D2 (new, doc-only)
before closeout. No commit.

## Index rows for Worker-0 (run-8 s13)

Revised rows (exact replacement text for the live plan rows — 10
verdict/shape revisions):

| `testing-client-module-mechanics` | `django_strawberry_framework/testing/client.py` (family docstring + 12 import statements + `TYPE_CHECKING` names incl. 2 class shells + `_ClientT` + verified D-N1/D-N2/D-N3 absences) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-collection-guard` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase` (`__test__ = False`, inherited by both siblings — pinned on both) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-endpoint-ladder` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase.__init__` + per-leaf transport defaults (5-rung composition + presence selection + base `url` forwarding; setting + default composed from `conf.py`) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-wrapped-accessor` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase.client` (one generic accessor + `cast` — the run-7 pair collapsed to a single site) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-finish-tail` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._finish_response` (shared uncolored `_decode` → `Response` → explicit-raise tail) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-request-transport` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase.request` (per-call `url=` routing + content-type omission switch + dropped `format=` kwarg) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-body-builder` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._build_body` (gate trio + no-`variables` guard + uniform map rule + envelope; reserved set participates in FC1) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-placeholder-walker` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._assert_file_placeholders` (post-serialization walk + canonical indexes + uniform `AssertionError` + D1) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-async-twin-shape` | `django_strawberry_framework/testing/client.py::AsyncTestClient` (sibling over the shared base + `AsyncClient()` default; `isinstance(x, TestClient)` is `False` — spec-043 Decision 8 reversed, text stale per D2) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | file-local |
| `testing-client-login-vs-one-sync-boundary` | `django_strawberry_framework/testing/client.py::AsyncTestClient.login` (rejection recorded here; CONVERGE with verified `one-sync-boundary` R1 on fresh evidence — kwarg-absent (thread-sensitive by default), no transaction; code census corrected: owner + types/resolvers ×3 + schema + 2; trigger: transaction-pinned sessions) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/utils/querysets.py` | File `testing/client.py` | rejected |

Anchor re-homes (path-only; verdict text verbatim — the anchor
symbol moved to the base):

| `testing-client-guard-type-vs-sibling-guards` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._assert_file_placeholders` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence; durable home the standing row) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/utils/policies.py` | File `testing/client.py` | rejected |
| `testing-client-len-guard-vs-shared-except` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._assert_file_placeholders` (rejection recorded here; CONVERGE with the standing shared-except-guard J1 direction on fresh evidence; HEAD-pinned message + chain) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | rejected |
| `testing-client-ladder-vs-policy-ladder` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase.__init__` (rejection recorded here; fresh pair, no prior verdict — URL selection vs policy resolution) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/utils/policies.py` | File `testing/client.py` | rejected |
| `testing-client-emit-vs-parse-bodies` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._build_body` (rejection recorded here; fresh pair — envelope emission vs boundary refusal; the name set routes to FC1, not the bodies) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/views.py` | File `testing/client.py` | rejected |
| `testing-client-gate-trio-split` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._build_body` (rejection recorded here; same-file intentional separation — provided-vs-absent vs member-emission vs mode-switch) | `django_strawberry_framework/testing/client.py` | File `testing/client.py` | rejected |
| `testing-client-intersection-vs-sibling-intersections` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._build_body` (rejection recorded here; fresh pair, no prior verdict — the `&` operator is the sharing; populations + verdicts differ) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/rest_framework/sets.py` | File `testing/client.py` | rejected |
| `testing-client-walk-vs-budget-walk` | `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._assert_file_placeholders` (rejection recorded here; fresh pair, no prior verdict — single-path verify vs full-traversal charge) | `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/extensions/resource_policy.py` | File `testing/client.py` | rejected |

CONFIRM notes (no new text; live rows stand, cites re-pinned
above): F2, F3, F7, F12, F14, F15, F16 unchanged in contract; FC1
`multipart-control-field-names` open (owner still TBD); R4, R5, R9,
R10 unchanged in verdict. No `## Owned changes` rows (zero-edit
re-trace).

## Run-8 verification (Worker 2)

Run: 0.0.15 2026-09-30-8. Work order: DRY.md, worker-2.md, the
s13 dispatch, the drift delta commit-by-commit at shared-tree HEAD
bytes (read-only `git show`/`git grep`/AST over `/tmp` extracts —
the slot copy carries no `.git`, so history reads cannot run there),
the full HEAD target (635 lines), every connected site below, and
only then the run-8 claim. Execution ran solely at
`dry/client-retrace-s13/verify` (runs `dry-20260930T173609-662095`,
`dry-20260930T173609-f7521a`, `dry-20260930T173642-c511b4`,
`dry-20260930T173645-475baf`, all exit 0, copy fresh, shared
unmoved; one earlier run exited 128 proving the slot has no `.git`).
HEAD `83998e08` verified at start and unmoved at finish. Section 1
is the pre-claim trace; section 2 reconciles every difference.

### 1. Own trace

Topology: drift base `0c0537e2` is an ancestor of HEAD; target
blobs base `d8feebb2` (568 lines) / HEAD `2466edae` (635) /
worktree `2d9aa737` (623) / `9aaaad5d` `b1439443`; committed delta
exactly the five commits in order with per-target stats 53+/13-,
17+/12-, 124+/112-, 5+/0, 8+/3- (total 182+/115-). Drift re-scope
(my instruments): `999a1aab` annotations + `cast`s + comments only
(`cast` is identity, TC-block inert); `b20277fe` annotation
narrowing + two `cast` returns only; `849f67bc` exactly 5 added
lines (1 import + 4 `@override`); `fef11e64` TC-only Protocol
bodies — all four runtime-neutral. `1a17dca5`: all 8 moved method
bodies AST-identical pre/post (my docstring-stripped dump
comparison; both `query` docstrings also byte-identical), the
`__init__` split preserves presence semantics compositionally on
both arms, the accessor merge is `cast`-identity both sides, and
exactly the 4 parity ignores are removed (pre 5 → post 1, the
headers arg-type ignore surviving to HEAD :206). The one
*behavioral* observable is the `isinstance` flip (plus MRO);
introspection deltas (`__qualname__` of moved methods,
`__override__ = True` on 4 methods) are not behavior under
principle 8. One-observable / all-bodies-verbatim: AGREE with that
precision.

Enumeration (own `ast` instrument over HEAD bytes): 23 top-level
statements, 35 module names (18 import-bound excl. the
`annotations` flag + 8 TC incl. 2 shells + `__all__` + `_ClientT`
+ 7 classes), 18 members (1 + 7 + 3 + 3 + 4). Every member homes to
exactly one rule: the base owns guard/`__init__`/accessor/tail/
transport/builder/walker, each leaf owns `__init__`/`query`/
`login`, the mixin + combos as before.

Matrix (own discharge at HEAD): (1) wrap/relay zero client tokens
re-swept, leaf byte-identical consumer; `force_login` 5 hits this
file only, `.logout()` sole site :475, `TestClient(` sole
construction :584, zero `AsyncTestClient(` constructions, zero
subclassers; (2) both colors share builder + tail below the color
line, bracket pair shares `finally`; (3) default/`url=`/member
emission/map rule composed, 13 `_safe_arg_repr` hits = 1 import +
12 renders with zero `{x!r}`; (4) FC1 count 2 with R7 bodies
separate, `self._decode(` sole site :162; (5) 36 + 13 oracles in
byte-identical files + zero drift commits on all four
oracle/consumer files + projections re-read intact; (6) D1 is the
one uncovered shape, deliberate absences hold with contract
sources. Full-package `sync_to_async(` code census, re-derived
with a directory pathspec: owner `utils/querysets.py:536` +
`types/resolvers.py` ×3 (:642/:715/:786) + `schema.py:406` + this
file ×2 (:530/:534) — every other hit prose (incl. a
`permissions.py:83` prose hit a `**/*.py` glob silently misses;
see note m1). The trio predates run 7 (`ddd5dbb9`, 2026-08-23,
present at the drift base); `schema.py:394/:406` are new in drift;
the `auth/mutations.py` `async_to_sync` pair pre-dates drift.
E-W2-1 re-verified on fresh evidence (asgiref 3.11.1,
`thread_sensitive=True` default).

Homes I would choose: FC1 stays open count 2; 16 file-local with
the base re-homes (F6 single-sited, F13 sibling); R1 rejection
stands on the corrected census; R2–R12 stand; D1 persists minor;
D2 doc-only filed; N7 closed by construction.

### 2. Reconciliation — per-area verdicts

- Drift scope: AGREE (1 behavior-bearing + 4 typing-only, stats
digit-for-digit, S-blob identity `b1439443` == run-7 worktree).
- Enumeration: AGREE 23/23 + 35/35 + 18/18, member-by-member, with
erratum E-W2-3 (below): the F1 text and mechanics index row say
"12 import statements" — the table's own stmts 2–12 are 11
(stmt 1 is `__future__`, excluded under the run-7 convention).
- CONFIRM file-local (F2 F3 F7 F12 F14 F15 F16): AGREE all, cites
re-pinned from my full read (:81-88, untouched Response body,
:396-460/:493-521, :462-475/:523-534, :560/:562-593/:584,
:595-622 byte-identical bodies, :625-635).
- FC1: AGREE count 2 (:267 + :280 co-spelling + :271 message vs
views :162 iterated :797-800, loop re-read); population re-closed
(`"operations"` exactly those sites; every other package hit prose,
message string, or another domain; patches :666 prose + :686
message literal verified by context).
- CONFIRM rejections (R2–R12): AGREE all eleven — 9 raises
recounted; R3 arm :328-339 + `match="unreadable length"` oracle;
R4 mechanisms + the inheritance-resolving cite (record note
agreed); R5 leaf byte-identical; R6/R7 splits; R8
:237/:240/:245 with :201/:162 agreeing; R9 `:403/:500` vs `:571`;
R10 :607 vs :622 byte-identical; R11 exactly 3 sites with both
sibling verdicts re-read; R12 stack :515 / loop :524 vs
single-path verify, `isdecimal` :459-464 version domain.
- REVISE (F1 F4 F5 F6 F8 F9 F10 F11 F13): AGREE all nine — census
revised (E-W2-3 aside); guard → base :126-130 (probe-proven
inheritance; strawberry-django `:16` parity + zero-`__test__`
installed-`strawberry/test/` sweep both re-derived); split
`__init__` :132-138/:393-394/:490-491; F6 pair superseded by the
one generic site :140-144 (C6 revision accepted; run-7
transcription correction moot); F8/F9/F10/F11 verbatim re-homes
(:146-174/:176-206/:208-280/:282-368); F13 sibling with the
unreferenced break (zero subclassers, zero package
`isinstance`/`issubclass` hits beyond the :486 docstring, zero in
tests + examples).
- R1 REVISE: AGREE verdict + corrected census (owner + 3 + schema
+ 2, each site re-derived above; trigger genuinely unfired — the
full 635-line read has no transaction/`using`).
- D1: ENDORSE (minor, unfixed, clean-line). Re-pinned :307 by my
own run `dry-20260930T173645-475baf` (`AttributeError: 'int'
object has no attribute 'split'` + both controls) on worktree
bytes, bridged by the byte-identical :306 line; every dirt hunk
is downstream of the defect line. Trust boundary passes as
before.
- D2: AGREE as filed (minor, doc-only, closeout-homed, not a
release blocker — no wire input reaches a spec sentence), with
erratum E-W2-2: the stale short-cite is rationale :180 (not
:179), on the line *adjacent to* (not the same as) the re-homed
:179 — the half-applied fact is exactly as described, and the
`1a17dca5` rationale hunk confirms it. Spec D8 (:1219-1223,
"Pinned: the port"), rationale D8 (:518-531, "IS the sync
client"), and the 3 + 1 re-homes all re-derived; spec :1342
`::TestClient.request` names upstream's class, correctly
un-re-homed.
- Near-misses: N1/N2/N4/N5/N6 AGREE (regions + oracles
byte-identical; floor `Django>=5.2.16` re-read at pyproject
:34); N3 now *execution-verified* at the current topology by my
probe (sync-over-async `AttributeError: 'coroutine' object has
no attribute 'json'`, async-over-sync `TypeError` on a
non-awaitable — both loud caller errors; DB-free); N7 AGREE
closed by construction (4 parity ignores removed in-commit, each
leaf `__init__` names its own transport, :206 unrelated).
- Index rows: the 10 revised + 7 re-home rows are exact
replacement text modulo E-W2-3 ("11" for "12" in the mechanics
row); all 7 anchors resolve at HEAD and all 7 verdict texts are
verbatim against the live plan rows (checked all 7); the R1 row
faithfully extends the run-7-transcribed text; 10 + 7 + 12 = 29
closes. Required transcription direction t3: re-home R4's anchor
`::TestClient` → `::_GraphQLTestClientBase` for consistency with
the F4 row (same guard token; verdict text untouched) — the live
anchor resolves via inheritance, so this is precision, not a
verdict change.
- Fingerprints: every H/W/S pin re-derived digit-for-digit (26
table inputs incl. rationale `a7c3049e`/`450a7107`; externals
`f2abe800` at 0.324.0, md5 `ad7a1131…`/`2e441da3…` at both
graphene-venv paths).
- Dirt: all 6 worktree hunks re-attributed by content (H1 import,
H2 reserved render, H3 docstring, H4 empty-segment render, H5
len-arm deletion + 2 retargets, H6 4-site retargets); render math
12−2=10 re-derived (10 `truth.render`, zero `_safe_arg_repr`);
15+/27- exact. Note: the "worktree-vs-`9aaaad5d`" parenthetical
is loose — that diff (185+/118-) is the drift rebased onto
migrated bytes, not drift-plus-migration; the operative
attribution stands on the hunk contents.
- Window: `ITEM_BASELINE=94b57959…` resolves, its target blob
equals worktree `2d9aa737`, `git diff <baseline> -- <target>`
empty; no `## Owned changes` row names the target (ledger
1426–1501 swept; later plan hits are index rows, dispatches,
baselines, drift notes). Zero-edit CONFIRMED.
- Infrastructure: W1's slot-venv defect does NOT reproduce at my
address — `typing_extensions` imports and the package imports
unaided (runs `...-662095`, `...-f7521a`), so my execution proof
is shim-free and strictly stronger; W1's shimmed runs stand on
their own recorded provenance. No `proof:`/`gate:` owed
(DB-free → sharded/PG inapplicable by construction); no pytest
per dispatch; ruff not owed (no `.py` touched, probes in
`/tmp`).

Further notes (all immaterial): m1 — a `git grep -- '**/*.py'`
pathspec silently misses top-level files (`schema.py`,
`permissions.py`); W1's censuses evidently used a covering
instrument (all counts reproduce) but future sweeps should use
the directory pathspec. m2 — for s20 (`one-sync-boundary`
re-trace): the run-2 ledger row claiming `types/resolvers.py`
arms route through the owner is stale in committed history (only
`ddd5dbb9` + `b20277fe` ever touched the trio region); the
direct-call census above is the live evidence. m3 — W2-n1/n3/n4/
n6-n10 carries agreed (n8's 12−2=10 re-derived at this worktree).

### 3. Verdict

Zero-edit re-trace, fully re-derived: 19 CONFIRM + 10 REVISE all
survive on independent evidence; drift homed; D1 persists
(execution-verified); D2 filed; N7 closed. No W2 defects. E-W2-2
(D2 :180, adjacent lines), E-W2-3 ("11 import statements" in the
F1 text + mechanics row), and t3 (R4 anchor → base) are
record-level and move no home, count, trigger, or defect verdict;
Worker-0 applies them as in-place corrections + transcription
directions under the run-7 E1 precedent.

Worker-0 instructions: (a) tick `File testing/client.py` back to
verified under `Run: 0.0.15 2026-09-30-8`; (b) apply the 17 index
rows with the E-W2-3/t3 corrections; (c) home D1 (unchanged) + D2
(new, doc-only) before closeout. No commit.
