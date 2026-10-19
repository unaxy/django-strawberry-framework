# DRY review: `django_strawberry_framework/_request_body.py`

Status: verified
Run: 0.0.15 2026-09-21-2

Item kind: FILE (inventory backstop). No consolidation is performed inside a
file item; every rule below lands in a file-local record with its proving
challenge, or in a rejected shared form with contract difference, trigger,
and durable home. Zero production edits; zero tracked files changed.

Item baseline: `ITEM_BASELINE=e3ed5189c1c9d953419e80ae8bd6efad426c09d9`
(read-only object, resolves). HEAD `69a253690002fdd413704a7879528c3ded363020`
at start (tripwire; finish recorded in `## Judgment`). Target clean at HEAD
blob `a70571ff5b3849afd01b6ae44e38416acdb27dd0` (working tree equals HEAD;
probe-verified). This artifact overwrites a `Run: 0.0.15 2026-09-18-1`
orphan record: per the worktree-entry ruling that record served as
rejected-candidate triggers to check only, and every number below was
re-derived fresh at this HEAD — none imported.

## System trace

Mid-size target (582 lines, 20 top-level statements): the one place the
package touches Django's private request-body internals. It DEFINES exactly
one public rule —
`django_strawberry_framework/_request_body.py::body_exceeds_limit`, the
boolean answer to "is this request body larger than `limit` bytes?" — plus
the private machinery that answer is built from: the three-outcome probe
vocabulary (`::_Probe`, `::_measured_remaining`, `::_declares_seekable`,
`::_lacks_seek`, `::_position_restored`), the bounded-read pair
(`::_bounded_read_exceeds_limit`, `::_measured_by_bounded_read`), the chunk
ceiling (`::_READ_CHUNK_BYTES`), the two operator signals
(`::_CORRUPTED_PROBE_LOG_MESSAGE`,
`::_UNREADABLE_STREAM_LOG_MESSAGE`), and the leaf manifest (`__all__`). It
ENFORCES nothing on the wire itself: every refusal returns as a `bool` and
is translated to the `413` by its one consumer,
`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`
(`views.py:645`, via the one leaf import at `views.py:102`).

Sites found, all at HEAD:

- The seven private-attribute code touches, all in-module: `hasattr`
  (`:263`), `request._body` read (`:264`), `getattr _stream` (`:265`),
  `getattr _read_started` (`:266`), `stream.close()` (`:579`),
  `request._stream` install (`:580`), `request._read_started` reset
  (`:581`). Package-wide quoted sweep (`"_body"` / `"_stream"` /
  `"\_read_started"`) returns exactly four hits, all in the target (`:46`
  prose, `:263`, `:265`, `:266`); package-wide attribute sweep returns only
  the target's code touches plus `schema.py:1114` `super()._stream(...)` —
  the response-frame streaming override, a different rule (body read).
- One entry `def` (`:209`), one `__all__` (`:133`), one production importer
  (`views.py:102`), one production call (`views.py:645`). No root
  re-export (`__init__.py` carries zero `body_exceeds_limit` /
  `_request_body` hits). Test-side importer: `tests/test_views.py` only;
  the live tier reaches the target exclusively through the views over HTTP.
- Zero `_BOUNDARY_` hits in the target (exit-1 grep): this module is
  measured BY the boundary, never a party to its ordering — the open
  family `prepared-view-handoff-shape` gains no site here.
- Zero patch tokens (`_patched_`, `_captured_`, `APPLY_UPSTREAM_PATCHES`),
  zero async tokens (`async def`, `await`, `coroutine`, `sync_to_async`,
  `run_in_one_sync_boundary`), zero ORM/seal tokens (`queryset`,
  `QuerySet`, `models.`, `seal`) in the whole file, prose included. The
  two upstream-patch families, `one-sync-boundary`, and all eight
  queryset/seal families gain no site here.
- Five exact-type gates (`:401`, `:416`, `:485`, `:490`, `:571`) plus two
  `type(stream).__name__` log-arg uses (`:270`, `:531`); seven
  `except Exception` guards (`:399`, `:407`, `:440`, `:448`, `:473`,
  `:491`, `:530`) and no other `except` shape — no `BaseException` catch,
  no bare `except`.
- One code site each for `os.SEEK_END` (`:406`), `exc_info=True` (`:531`),
  `request.read(` (`:570`; `:572` is the error message naming it),
  `_READ_CHUNK_BYTES` store (`:140`) and use (`:570`), `from . import
  logger` (`:128`), `BytesIO` install (`:580`); two `logger.warning` calls
  (`:270`, `:531`). Zero reads in code of settings, `HTTPException`,
  `CONTENT_LENGTH`, `content_params`, `META`, `parse_json`, CSRF, or the
  mount kwarg (AST string-aware sweep over docstring-stripped code).

Connected code read for judgment, outside the item: `views.py` (mixin
docstring `:388-469`, `_resolved_max_request_body_bytes` `:159-202`,
`_declared_content_length` `:205-216`, `_RawBodyRequestAdapter` `:340-385`,
`_enforce_request_boundary` `:584-603`,
`_enforce_request_boundary_once` `:605-623`,
`_enforce_request_body_limit` `:625-646`, the multipart/charset guards
`:648-710`, both `run` overrides `:995-1005` / `:1046-1055`, both
`parse_multipart` overrides, `_run_after_csrf_check` `:823+` vicinity via
grep); `middleware/request_body.py` (full read: `__call__` / `__acall__`
twins, `process_view`, `_package_view_instance`, `_require_boundary_before_csrf`);
`_boundary_ordering.py` (defs census; the verified run-2 artifact
`dry-file-_boundary_ordering.md` read as the record for marks, the
prepared-view handoff, and the open family); `consumers.py`
(revocation-close `logger.exception` `:767` vicinity, `revalidate_operation_actor`
`:779` with its `logger.exception` cluster `:1549-1573`); `types/finalizer.py`
(`logger.warning` `:487`, via `git show HEAD:` — dirty in tree);
`optimizer/nested_planner.py` (`logger.warning` `:645-646`, via HEAD —
dirty); `extensions/resource_policy.py` (`limit + 1` evidence site `:422`,
via HEAD — dirty); `optimizer/single_parent_fetch.py` (`limit + 1`th
probe-row comment `:283`); top-level `resource_policy.py` (`seconds + 1`
`:922`, same evidence family); `schema.py::_stream` (`:1098-1117`,
response frames); `middleware/debug_toolbar.py` (`:282`, the one public
`request.body` read — diagnostics tagging); `tests/test_views.py` (oracle
imports `:89-91`, driver `:1362-1400` + twins `:1403-1416`, past-end
`:1420-1459`, foreign-initial `:1463-1475`, unit `:1477-1481` read
body-by-body; all 24 body-row def names `:1158-1930` censused);
`test_transport_api.py` (body-limit wire rows censused by name);
spec-046 Decision 7 (`:1094-1261` read: steps 1-4, measurement ladder,
zero-is-failure, three outcomes, totality, single-siting; Decision 18
heading `:2401` + ordering via the boundary record; Decision 9
non-attributability via the `views.py:660-662` / `:703-705`, middleware
`:200-202`, and driver `:1371-1374` prose, not via the Decision 9 body
itself); glossary `Request-body cap` anchor (`:1724-1740` read);
installed Django 6.1 (`http/request.py`: `hasattr(self, "_body")` x3,
`_read_started` x4, `RawPostDataException` x2, `UnreadablePostError` x4,
`BytesIO(self._body)` x2; `LimitedStream(IOBase)`; `_read_started = False`
in both request constructors).

Inputs fingerprinted (full HEAD blobs; CLEAN = working tree equals HEAD,
facts read from the tree; DIRTY = concurrent work, facts read via
`git show HEAD:`):

| Input | HEAD blob | State |
|---|---|---|
| `_request_body.py` | `a70571ff5b3849afd01b6ae44e38416acdb27dd0` | CLEAN |
| `views.py` | `9f85b0df26a17e800ec392aa13f6848e07633895` | CLEAN |
| `middleware/request_body.py` | `e6e32e785ec84360c63c9ff529a58f8d63bc8898` | CLEAN |
| `_boundary_ordering.py` | `197eea8e01cb405f38b21022689ed54970efcb97` | CLEAN |
| `consumers.py` | `936210e2993ddca4b77ffebf65e728f59d17079c` | CLEAN |
| `types/finalizer.py` | `77fd9a2dd229eb9de5f29188c5058035d3606323` | DIRTY |
| `optimizer/nested_planner.py` | `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04` | DIRTY |
| `extensions/resource_policy.py` | `52084078ac166d8116b9e4bb2522e8ce193251ea` | DIRTY |
| `optimizer/single_parent_fetch.py` | `e995270af9b213b7f931c03d7dc8f7c084819e1b` | CLEAN |
| `schema.py` | `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5` | CLEAN |
| `middleware/debug_toolbar.py` | `5360149bfa207e707c98985e9a1d79672220b210` | CLEAN |
| `tests/test_views.py` | `4dc9a25723501cd1f84161423a1aefbf00ff7eb9` | CLEAN |
| `test_transport_api.py` | `818b639b538df98dd4c9d4571ebfc694bedc221a` | CLEAN |
| `spec-046-transport_security-0_0_14.md` | `8d8adaf2f2f07cbc6cd3d434a029b2419b7d4704` | CLEAN |
| `docs/GLOSSARY.md` | `bc51debc54cf3ed142b45fa9feda1b99bce60c79` | CLEAN |

Installed Django 6.1 shape recorded as counts above (environment, not a
blob). Searched population for every package-wide count: 117 tracked
`django_strawberry_framework/**/*.py` files (probe-verified).

## Verification

### Enumeration

Instrument: `ast.parse` over the target (working tree, probe-verified
byte-identical to HEAD), counting `ast.Module.body` members — **20
top-level statements**. The class contributes its two members, counted
with their owner. Every member lands below; every challenge in
`### Challenges` ends in a file-local row or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (private-Django contract, probe rationale, policy split) | (none) | projection, F1-F9 |
| 2 | `from __future__ import annotations` | (none) | machinery |
| 3 | `import os` | `os` | machinery for F3 (`os.SEEK_END`, one code site) |
| 4 | `from enum import Enum` | `Enum` | machinery for F3 |
| 5 | `from io import BytesIO` | `BytesIO` | machinery for F6 |
| 6 | `from typing import TYPE_CHECKING, Any` | (annotations) | machinery |
| 7 | `from . import logger` | `logger` | consumer by name (root logger), F8 |
| 8 | `if TYPE_CHECKING: from django.http import HttpRequest` | (annotation only) | machinery (zero runtime import) |
| 9 | `__all__ = ("body_exceeds_limit",)` | public name | F9, file-local |
| 10 | `_READ_CHUNK_BYTES = 64 * 1024` | chunk ceiling | F7, file-local |
| 11 | `_CORRUPTED_PROBE_LOG_MESSAGE = (...)` | probe signal text | F8, file-local |
| 12 | `_UNREADABLE_STREAM_LOG_MESSAGE = (...)` | read-failure signal text | F8, file-local |
| 13 | `class _Probe` + `UNMEASURABLE` + `CORRUPTED` | probe vocabulary | F3, file-local |
| 14 | `def body_exceeds_limit` | entry ladder | F1 (attr sites), F2 (ladder), file-local |
| 15 | `def _measured_remaining` | probe body | F3, file-local |
| 16 | `def _declares_seekable` | capability half 1 | F4, file-local |
| 17 | `def _lacks_seek` | capability half 2 | F4, file-local |
| 18 | `def _position_restored` | restore verifier | F5, file-local |
| 19 | `def _bounded_read_exceeds_limit` | totality wrapper | F6, file-local |
| 20 | `def _measured_by_bounded_read` | loop + reinstall | F1 (attr sites), F6, file-local |

Rules: F1 private-attribute centralization; F2 the four-rung ladder with
two deferrals; F3 the three-outcome probe; F4 the capability halves; F5
restore verification; F6 the bounded-read measurement; F7 the chunk
ceiling; F8 the operator signals; F9 the leaf manifest.

Open-plan-family traffic check (fresh; assign where a rule matches — none
does, so no open row gains a site and no new family is named):

| Open family | Sweep over this target | Verdict |
|---|---|---|
| `prepared-view-handoff-shape` | `_BOUNDARY_` hits: 0 (probe + exit-1 grep); no tuple packed/unpacked | no traffic |
| `upstream-patch-lifecycle` | patch tokens (`_patched_`, `_captured_`, `APPLY_UPSTREAM_PATCHES`): 0 in code and prose | no traffic |
| `upstream-patch-refusal-wording` | same zero sweep; target raises only the chunk `TypeError`, converted in-module to fail-closed `True` | no traffic |
| `one-sync-boundary` | `sync_to_async`, `run_in_one_sync_boundary`: 0; 0 async nodes | no traffic |
| `awaitable-refusal-and-disposal` | `await`, `coroutine`, `async def`: 0; fail-closed `bool` is a different contract (J-note in F2) | no traffic |
| `sealed-execution-queryset` | `seal`, `queryset`, `QuerySet`: 0 | no traffic |
| `seal-defect-code-wording` | same zero sweep | no traffic |
| `recomposition-illegal-source-rejection` | same zero sweep | no traffic |
| `related-object-visibility-recheck` | `queryset`, `models.`: 0 | no traffic |
| `child-queryset-alias-inheritance` | same zero sweep | no traffic |
| `async-only-queryset-row-adapter` | zero async + zero queryset | no traffic |
| `post-set-apply-result-validation` | no set/apply vocabulary (full 582-line read) | no traffic |
| `queryset-seed-and-model-read` | `queryset`, `models.`: 0 | no traffic |
| `orm-lookup-path-resolution` | zero ORM vocabulary (full read) | no traffic |

The consolidated row (`request-body-boundary-ordering`) gains no site
(zero marks — this module is measured BY the boundary, never a party to
its ordering), and no rejected or file-local index row names a mechanism
on this surface. The 15 DRY-adopted ledger paths and all hunt dirt are
concurrent work for this item and were touched by nothing here.

### Matrix

Discharged against the target's real surface (a sync measurement module:
no ORM, no I/O beyond the request stream, no async body of its own).

**1. Cross-flavor policy mirroring.** Searched every sibling flavor for a
second body-measurement vocabulary. None exists: the only production
reader of `body_exceeds_limit` is
`views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit` (one
import `:102`, one call `:645`, probe-verified), which owns the limit,
the `413`, and the wire reason and never names a private request
attribute itself (quoted + attribute sweeps over `views.py`: zero).
`middleware/request_body.py` owns chain position only: it invokes the
boundary by method name through `_BOUNDARY_METHOD` (`:230`) and
translates the identical `HTTPException` to the identical `text/plain`
response from the caught exception's own `reason` (`:231-236`) — it
composes the refusal, never restates it, and names no private attribute
(sweeps: zero). No filter/order/mutation/form/rest/auth/testing/types
surface measures bodies (helper-name census: zero non-target hits
package-wide for all ten helper/message names; body-vocabulary sweep:
zero). The toolbar's `:282` `json.loads(request.body)` reads the PUBLIC
property for operation-name tagging — diagnostics, post-boundary, a
different rule. The four patch modules carry zero traffic here (patch
tokens: zero). Mechanism/policy split confirmed, no mirror to
consolidate.

**2. Sync/async twins.** The target defines no colored pair: zero
`AsyncFunctionDef` / `Await` / `AsyncFor` / `AsyncWith` nodes
(probe-verified by AST walk, not by shape). Both package views call the
one sync function first from their respective `run` paths (sync `:1004`,
async `:1054`); the async view's own docstring states the single
difference is the `await`. The middleware `__call__` / `__acall__` twins
never touch measurement. No twin machinery lives here; nothing to
consolidate here. A future async byte source would be a new rule (see
C3), not a twin of this one.

**3. Derived rather than repeated knowledge.** The `limit + 1` bound is
computed once in code (`:570`); its appearances in the `views.py` mixin
docstring (`:442`, `:478`, `:1037`), the target's own docstrings (`:137`,
`:233`, `:536`, `:544`), and the test assertions are projections and
oracles, never second computations. The two other `limit + 1` spellings
package-wide are different rules, verified at their bodies:
`extensions/resource_policy.py:422` over-collects by one as
error-reporting evidence (`actual` of `ResourceLimitExceeded`) for a
bound violation, `optimizer/single_parent_fetch.py:283` names the window
probe row for `_resolve_from_window` re-inference — pagination/lookahead
idioms, not body-cap bounds (J4; the top-level `:922` `seconds + 1` is
the same evidence family). No reconstructed private-attribute knowledge:
every production read/write of `_body` / `_stream` / `_read_started` is
in this file (probe-verified over all 117 package files; the lone
`schema.py:1114` `._stream` hit is a response-frame method name).

**4. Inverse / round-trip pairs.** Two, both in-module by construction.
Probe/restore: the end-seek moves the stream (`:406`), `_position_restored`
re-seeks and verify-`tell`s before the pair is judged (`:412-413`), so
every `UNMEASURABLE` verdict provably starts the bounded read where the
request started. Install/re-read: the bounded branch installs a rewound
`BytesIO` (`:579-581`) and Django's own `HttpRequest.body` re-reads it
downstream, pinned by the oracle that reads the body back byte-for-byte
with `_body` absent until then (`:1275` rewound-stream row). Django's own
close-and-`BytesIO` replacement is the upstream shape this matches
(verified in installed `request.py`: `BytesIO(self._body)` x2), not a
second definition. Each pair's halves are consumers of one definition.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: the contract source (spec-046 Decision 7 `:1094-1261`
measurement paragraphs incl. the three-outcome and totality
requirements, read; Decision 9 non-attributability via the `views.py`,
middleware, and driver prose cited in System trace); production code
(target + the one `views.py` call site); oracles in `tests/test_views.py`
that compose the module by name only for identity/structure
(`_CORRUPTED_PROBE_LOG_MESSAGE`, `_UNREADABLE_STREAM_LOG_MESSAGE`,
`_position_restored` imports `:89-91`; the shared
`_assert_one_unmeasurable_body_was_recorded` driver `:1362-1400`
parameterized by the one axis the signals differ on) and pin behavior
per request shape with literally-spelled expectations (`WARNING`,
class-name args, `exc_info` split, `delivered == limit + 1`, `unread >
0`, `hasattr(request, "_body") is False`, `RawPostDataException`
preservation, `413` + reason) across 24 defs `:1158-1930`, plus the live
`test_transport_api.py` wire rows (declared trio `:1258`, WSGI `:1288`,
ASGI `:1323`, cumulative `:1360`, 413-vs-400 `:1398`, two-ceilings
`:1525`, async cap `:1756`); prose projections (the target's
module/function docstrings, the mirror paragraphs in the `views.py`
mixin docstring `:434-452`, the glossary `Request-body cap` anchor).
The `hasattr(request, "_body")` spellings in tests pin Django's contract
and this module's rung-1 reading — oracles, listed never counted. No
medium restates the rule as a second definition.

**6. Enforcement by omission.** Family enumerated, every member pinned by
a verified oracle name: seekable over (`:1158`) and under byte-for-byte
(`:1201`); 3.10 undeclared-seekable probed (`:1228`); non-seekable over
to exactly `limit + 1` (`:1251`) and under rewound (`:1275`);
unmeasurable-position fallback (`:1312`); zero-probe read-not-believed
(`:1330`, body read); past-end refused-unread (`:1420`, body read);
foreign initial position bounded-without-seeking (`:1463`, body read);
foreign-position unit zero-call (`:1477`, body read); lying restored
position (`:1486`); non-callable marker bounded (`:1502`);
fail-without-moving fallbacks (`:1525`); numeric-protocol-raising
rejection (`:1567`); unrestorable refuse + log (`:1605`); no-seek
measured (`:1642`, under) and bounded (`:1677`, over); unreadable-seek
conservative path (`:1701`); genuinely-empty allow (`:1728`);
unreadable-read refused (`:1780`); non-bytes chunk (`:1833`);
cached measured-and-refused (`:1877`); consumed defer (`:1908`);
streamless defer (`:1930`). Deliberate non-measurement is the contract
with its owner elsewhere: multipart never reaches here (`views.py`
returns first at `:643-644`, spec step 3), GET returns first (`:638`),
declarations are never inspected here (code-level token sweep: zero).
No member lacks a guard its contract requires.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 attr identity | Django renames `_stream` (or either sibling) | **1** (this module; the 7 touches co-move; `views.py` call site + oracles follow as consumer/oracle) | independent |
| C1b | F1 read vs write | reinstall shape change (other than `BytesIO` swap) | **1** (`:579-581`; reads untouched) | independent |
| C2 | F2 ladder | a new materialization state needs its own rung | **1** (the one function body) | independent |
| C3 | F3 verdict set | the probe needs a fourth verdict | **1** (`_Probe` + `_measured_remaining` co-move in-module) | independent |
| C3b | F3 zero policy | answer a zero probe as "empty" | **0** moves — refused by contract (fail-open at the 5.2 floor; `:1330` oracle pins the bounded fallback) | refused |
| C4 | F4 capability | a new interpreter spool / wrapper shape | **1** (the capability halves; both views unaffected — axis-2 evidence) | independent |
| C5 | F5 verify-vs-infer | infer restore from no-raise instead of verify-`tell` | **1** (the predicate; inference is the documented rejected shape) | independent |
| C6 | F3/F5/F6 gate strictness | admit `int` subclasses (`isinstance` relaxation) | 5 in-module checks move together; `views.py:197` untouched (different rule, J2) | independent |
| C7 | F6 read ownership | `stream.read` instead of `request.read` | **1** site (`:570`; ownership choice, not duplication) | independent |
| C8 | F6 reinstall shape | pre-fill `request._body` instead of `BytesIO` swap | **0** moves — refused by contract (disables Django's ceiling; live `:1525` two-ceilings oracle pins) | refused |
| C9 | F7 chunk policy | per-mount chunk tuning | **1** (the constant becomes a parameter; no second site today) | independent |
| C10 | F8 signal policy | one shared refusal emitter / new level | refused shared form (J3: 2 literals, one module, distinct `exc_info` axis) | rejected |
| C11 | F9 manifest | a second public helper | **1** place (`__all__` + def co-located; no such change exists) | independent |

**Experiment.** Read-only probe (no source mutation, no settings, no DB,
no shared-tree pytest — the workspace recipe is for mutating proofs, of
which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-_request_body-r2-w1/probe_request_body.py
```

Output (`ALL OK (70 checks)`): target byte-identical to HEAD; 20-member
AST count with member-kind list, all 7 function names in order, both
`_Probe` members, all 4 module assigns; zero async nodes; the 7
private-attribute code touches at their exact lines; package-wide quoted
sweep returning only the target (4 hits); zero `_BOUNDARY_` hits; one
entry `def` + one `views.py` import + one call; 7 `type()` calls with
exactly the 5 exact-type gates; 7 `except Exception` guards and 7 total
handlers; one code site each for `os.SEEK_END`, `exc_info=True`,
`request.read(`, `_READ_CHUNK_BYTES` store/use, `from . import logger`,
`BytesIO` install; two `logger.warning` calls; zero code-level policy
tokens (AST string-aware, 12 tokens); 117-file population; 8 `_Probe`
returns; zero non-target hits for all 10 helper/message names. Six probe
bugs found and fixed during the pass, all in the probe (attribute name,
noisy hash print, basic-regex alternation, two sort orders, error-message
mention vs call site) — the target never implicated. Status:
`execution-verified` for every identity/count claim below. Rejects the
wrong results "a second production site names a private attribute",
"the middleware spells a mark here", "a twin body exists", "policy is
read in code", "a helper is used outside".

## Findings

No production edit is owed by a file item; each record below is
file-local (single definition, challenge-proved) or a rejected shared
form. Nine file-local rules, seven considered-and-rejected shared forms.
No new families named; no open family gains a site.

### F1 — private-Django body-attribute centralization (file-local)

- **Contract + variation.** Every production read/write of
  `HttpRequest._body`, `HttpRequest._stream`, `HttpRequest._read_started`
  lives in this module: rung-1 `hasattr(request, "_body")` + length
  measure (`:263-264`), `getattr(request, "_stream", None)` +
  `getattr(request, "_read_started", False)` deferrals (`:265-266`),
  consumed-stream close + `BytesIO` install + `_read_started` reset
  (`:579-581`). Variation axes: the three attributes, read vs write.
- **Sites + roles.** *Definitions*: the seven code touches above, all in
  the target (probe-verified: quoted sweep returns only the target;
  attribute sweep returns only the target plus the `schema.py:1114`
  response-frame method name). *Consumers*:
  `views.py::_enforce_request_body_limit` (one boolean call, never names
  an attribute), Django's own `HttpRequest.body` (re-reads the installed
  stream). *Oracles*: the `hasattr(request, "_body") is False` rows and
  the rewound-stream rows in `tests/test_views.py` (pin the contract,
  compose the attribute names as the protocol demands). *Projections*:
  the target module docstring's contract paragraphs (`:36-67`); spec-046
  Decision 7's single-siting sentence.
- **Challenges.** C1 → 1 definition; C1b → 1.
- **Owner + lifetime.** This module, by responsibility: the narrowest
  module every legitimate consumer can depend on, and the only file
  allowed to name the privates (spec-046 pins the single-siting). No
  stored derivation beyond the request's own stream; no lifetime fields
  owed (the request owns its lifecycle; this module borrows it per call).
- **Migration.** None (zero-edit item): single owner stands.
- **Distinct behavior.** Reads vs reinstall are one lifecycle, not two
  rules: the reinstall is what makes the reads honest downstream
  (Django's ceiling still fires). Never writing `_body` is the
  load-bearing half, pinned by the live two-ceilings oracle (`:1525`).
- **Behavioral proof.** `execution-verified` for single-siting (probe:
  quoted + attribute sweeps, exact touch lines). Oracle bodies
  `static-reviewed` (bodies read, not run; zero pytest runs in this
  item). Rejects "a second production site touches a private attribute".
- **Structural gate.** The quoted-attribute + attribute-access count
  search over all 117 package files (each spelling exactly where the
  probe says). Negative control: a hand copy of any private-attribute
  read — quoted OR unquoted (`request._stream = ...`) — into `views.py`
  passes every behavioral oracle and fails ONLY the count, so the
  search, not the tests, owns this finding; a family item must own that
  search as a check.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `views.py` `9f85b0df…`,
  `tests/test_views.py` `4dc9a257…`, spec-046 `8d8adaf2…` (full blobs in
  System trace); searched populations: 117 package files (quoted sweep,
  attribute sweep, helper census). Excluded on body strength:
  `schema.py::_stream` (response operation frames, `:1098-1117` read —
  `execution_context` / `extensions_runner` / `resumed_stream`, zero
  request-attribute traffic); `middleware/debug_toolbar.py:282` (public
  `request.body` read for diagnostics tagging, different rule); every
  filter/order/mutation/form/rest/auth/testing/types flavor (helper +
  body-vocabulary sweeps: zero).

### F2 — the four-rung answer ladder with two deferrals (file-local)

- **Contract + variation.** `body_exceeds_limit` answers cheapest-first:
  already-materialized (measure the cache, still refuse), seekable probe
  (no read), bounded read (`limit + 1`), fail-closed `True` (corrupted
  probe, unreadable read); defers with `False` on no `_stream` and on
  already-consumed streams. Variation axes: the request's
  materialization state.
- **Sites + roles.** *Definition*: the one function body (`:209-274`).
  *Consumer*: the `views.py` call site (`:645`, 413 translation).
  *Oracles*: the per-rung rows (cached `:1877`, seekable `:1158` /
  `:1201`, bounded `:1251` / `:1275`, both fail-closed rows with logs,
  both defer rows `:1908` / `:1930`). *Projections*: the function
  docstring's numbered rungs; the `views.py` mixin docstring's counting
  paragraphs (`:434-452`); the glossary anchor.
- **Challenges.** C2 → 1 definition.
- **Owner + lifetime.** This module (the ladder IS the entry rule). Pure
  function per call; "not cached" by construction.
- **Migration.** None.
- **Distinct behavior.** The two `False` deferrals are not failed
  measurements: `HttpRequest.body` itself raises on a consumed stream,
  and a streamless request has no byte source Django tolerates —
  translating either into a `413` would misattribute another component's
  state. The fail-closed `True` answers a different question than the
  `awaitable-refusal-and-disposal` family's refusals (no awaitable, no
  sync boundary here — unmeasurable bytes vs undisposable coroutines),
  which is why no open row is assigned.
- **Behavioral proof.** `execution-verified` for structure (single
  `def`, single call site; probe). Oracles `static-reviewed`. Rejects
  "a rung lives elsewhere".
- **Structural gate.** The per-rung oracles (each rung has an allow and
  a refuse direction; the defer rows assert the honest outcomes).
  Negative control: deleting the consumed-deferral passes the status
  oracles and fails the `:1908` row — the row, not the status, owns the
  rung.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `views.py` `9f85b0df…`,
  `tests/test_views.py` `4dc9a257…`, `test_transport_api.py`
  `818b639b…`, spec-046 `8d8adaf2…`, glossary `bc51debc…`; searched
  populations: entry-name census package-wide (1 def + 1 import + 1
  call), both `run` overrides. Excluded on body strength: the
  middleware twins (chain position + refusal translation, full read —
  never measure); the `awaitable-refusal-and-disposal` family (zero
  async vocabulary, probe-verified).

### F3 — the three-outcome probe (file-local)

- **Contract + variation.** `_measured_remaining` answers a positive
  `int`, `UNMEASURABLE` (stream provably untouched, bounded read
  licensed), or `CORRUPTED` (position unprovable, nothing may read); a
  probed zero or less is `UNMEASURABLE`, never "empty" (`:419-420`); the
  position is restored before the pair is judged (`:412-413`). `_Probe`
  names the two non-numeric outcomes apart. Variation axes: probe
  capability, position integrity, pair coherence.
- **Sites + roles.** *Definitions*: `_Probe`, `_measured_remaining`
  (both in-module; 8 `_Probe` returns, probe-verified). *Consumers*:
  `body_exceeds_limit` (three-way branch `:269-274`),
  `_bounded_read_exceeds_limit` (the fallback `UNMEASURABLE` selects).
  *Oracles*: the zero-belief row (`:1330`, body read), the past-end row
  (`:1420`, body read: `requested == []`, `delivered == 0`, `413`, log),
  the unrestorable row (`:1605`), the empty-body control (`:1728`, one
  bounded read, allowed). *Contract source*: spec-046 Decision 7 (three
  outcomes, zero verification — read).
- **Challenges.** C3 → 1; C3b → refused by contract; C6 (position/end
  gates) moves the 5 in-module checks together.
- **Owner + lifetime.** This module. Pure derivation per call; "not
  cached" stated by the code.
- **Migration.** None.
- **Distinct behavior.** `UNMEASURABLE` vs `CORRUPTED` is the finding the
  two-state version got wrong (bounded read from an unknown offset
  handing Strawberry bytes that are not the request's); collapsing them
  re-creates it. Both `CORRUPTED` shapes pin the log independently
  (`:1420`, `:1605`).
- **Behavioral proof.** `execution-verified` (single `def`, enum
  membership via AST, 8 returns; probe); oracles `static-reviewed`.
  Rejects "a second probe exists" and "zero means empty".
- **Structural gate.** The zero-belief and past-end oracles with their
  `delivered == limit + 1` / `requested == []` bounds (status-only
  assertions would pass the clamping version). Negative control:
  restoring `max(end - position, 0)` passes every status oracle and
  fails the bound assertions.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `tests/test_views.py`
  `4dc9a257…`, spec-046 `8d8adaf2…`; searched populations: helper-name
  census (`_Probe`, `_measured_remaining`: zero non-target hits),
  117-file population. Excluded on body strength: `views.py` config
  gate (different domain — J2); the `prepared-view-handoff-shape`
  family (zero mark traffic — the probe/restore pair is an in-module
  round trip, not a cross-module handoff).

### F4 — the capability halves (file-local)

- **Contract + variation.** `_declares_seekable` believes `seekable()
  == True` and the absent method (the 3.10 spool fallback to `tell()`),
  never a `False` / raising / non-callable marker; `_lacks_seek`
  decides absence before anything moves so an unmovable stream is
  `UNMEASURABLE`, never `CORRUPTED`. Variation axes: declaration
  presence, marker shape.
- **Sites + roles.** *Definitions*: the two functions (in-module; zero
  non-target uses, probe-verified). *Consumer*: `_measured_remaining`
  (first gate `:395` + pre-move absence check `:403`). *Oracles*: the
  undeclared-seekable row (`:1228`, probed not read), the
  non-callable-marker row (`:1502`, bounded), the no-seek rows
  (`:1642` measured / `:1677` bounded, no false log), the
  raising-descriptor row (`:1701`, conservative path). *Contract
  source*: spec-046 Decision 7 floor paragraphs (3.10 spool shape) +
  the target docstring's seekability section.
- **Challenges.** C4 → 1.
- **Owner + lifetime.** This module. Pure predicates; no state.
- **Migration.** None.
- **Distinct behavior.** Believing a missing `seekable` admits
  position-reporting non-seekers, which is exactly why absence of
  `seek` is decided separately and after the position gate: the order
  is the contract (absence proved harmless vs raise proved nothing).
- **Behavioral proof.** `execution-verified` (single defs, call sites
  in `_measured_remaining` only — helper census); oracles
  `static-reviewed`. Rejects "the probe requires `seekable`".
- **Structural gate.** The four sibling rows (undeclared / non-callable
  / no-seek / raising-descriptor) with their divergent verdicts — one
  shared helper returning one answer would fail three of them. Negative
  control: routing the no-seek shape through the end-seek path refuses
  an under-limit body and logs a false movement claim (`:1642` fails).
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `tests/test_views.py`
  `4dc9a257…`, spec-046 `8d8adaf2…`; searched populations: helper-name
  census (zero non-target hits for both halves). Excluded on body
  strength: WSGI's `LimitedStream` (declares `seekable()` `False` —
  never reaches the halves; verified in installed Django as an
  `IOBase` subclass); the middleware recognition guards (different
  question — J1).

### F5 — restore verification (file-local)

- **Contract + variation.** `_position_restored` seeks back and
  verify-`tell`s; both the input position and the restored reading must
  be exactly built-in `int` (`:485`, `:490`), or the answer is `False`
  without calling the stream. Variation axis: none (one predicate).
- **Sites + roles.** *Definition*: the one function. *Consumers*:
  `_measured_remaining` (the `CORRUPTED` gate `:412-413`, incl. the
  end-seek-raised path). *Oracles*:
  `test_position_restored_rejects_a_foreign_position_before_calling_the_stream`
  (`:1477`, direct unit pin, body read: `False`, zero stream calls) +
  the lying-restored rows (`:1486`, `:1605`). *Projection*: the function
  docstring (why verify, not infer).
- **Challenges.** C5 → 1; C6 (both exact-int checks co-move).
- **Owner + lifetime.** This module. Pure predicate; no state.
- **Migration.** None.
- **Distinct behavior.** Verification vs inference is the whole rule: a
  coherent-accepting incoherent-coordinate stream passes "seek did not
  raise" and fails the second `tell`.
- **Behavioral proof.** `execution-verified` (single `def`, single
  consumer — helper census); the unit oracle composes it by name
  (`static-reviewed`). Rejects "restore is inferred from no-raise".
- **Structural gate.** The foreign-position unit row (zero stream calls
  asserted). Negative control: trusting no-raise passes every status
  oracle and fails only the lying-restored rows.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `tests/test_views.py`
  `4dc9a257…`; searched populations: helper-name census (zero
  non-target hits). Excluded on body strength: none beyond the
  census — the predicate's only consumer is in-module.

### F6 — the bounded-read measurement (file-local)

- **Contract + variation.** `_bounded_read_exceeds_limit` wraps
  `_measured_by_bounded_read` so the loop stays a straight line while
  the verdict stays total: any `Exception` (stream read, `close`,
  replacement install, chunk validation) is the fail-closed `True` with
  the operator record (`:528-532`). The loop reads through
  `request.read` (Django keeps `_read_started` bookkeeping and the
  `OSError` → `UnreadablePostError` translation), stops at `limit + 1`
  without ever joining over-limit chunks, validates each chunk is
  exactly built-in `bytes` before truth or length testing (`:571-572`),
  and on allow closes the consumed stream and installs a rewound
  `BytesIO` with `_read_started` reset (`:579-581`). Variation axes:
  failure moment, chunk shape.
- **Sites + roles.** *Definitions*: the two functions (in-module; zero
  non-target uses, probe-verified). *Consumer*: `body_exceeds_limit`
  (the `UNMEASURABLE` arm `:272-273`). *Oracles*: the at-most-one-byte-past
  row (`:1251`: never-joined, unread remainder), the rewound-stream row
  (`:1275`: no `_body`, closed stream, reset flag, byte-for-byte
  re-read, Django body still serving), the unreadable-read row
  (`:1780`: no partial install, `RawPostDataException` preserved), the
  non-bytes-chunk row (`:1833`: zero protocol executions, finite
  `TypeError` record). *Contract source*: spec-046 Decision 7 (bounded
  chunks, totality — read).
- **Challenges.** C7 → 1 site; C8 → refused by contract; C6 (chunk gate
  co-moves with the probe gates).
- **Owner + lifetime.** This module. The collected prefix lives for the
  call only; dropped with the request on refusal, installed as the
  request's stream on allow (ownership transferred to Django).
- **Migration.** None.
- **Distinct behavior.** `request.read` vs `stream.read` is deliberate
  (translation kept for Django's sake); never-join vs install are the
  two directions of one bound (over: no over-limit `bytes` ever
  allocated; under: Django's own ceiling still applies).
- **Behavioral proof.** `execution-verified` (single call/read/close/
  install sites; probe). Oracles `static-reviewed`. Rejects "a second
  bounded reader exists" and "the prefix is cached".
- **Structural gate.** The `delivered == limit + 1` + `unread > 0` +
  `hasattr(request, "_body") is False` triple on every over-limit row,
  and the `RawPostDataException` preservation on the broken-read rows.
  Negative control: an unguarded `request.read` passes the happy rows
  and escapes the broken-stream rows as `500` (the documented pre-fix
  shape, `:511-518`).
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `tests/test_views.py`
  `4dc9a257…`, `test_transport_api.py` `818b639b…` (two-ceilings
  `:1525`), spec-046 `8d8adaf2…`; searched populations: helper-name
  census (zero non-target hits for both functions), `limit + 1`
  census (1 code site here). Excluded on body strength:
  `extensions/resource_policy.py:422` (error-evidence count — J4),
  `optimizer/single_parent_fetch.py:283` (pagination probe — J4),
  `views.py` declared-length gate (declaration pre-check, different
  rule — `:640-642`).

### F7 — the chunk ceiling (file-local)

- **Contract + variation.** `_READ_CHUNK_BYTES = 64 * 1024` caps one
  `read()` allocation on the way to `limit + 1` (`:140`, `:570`); total
  bytes never exceed `limit + 1` regardless. No variation axis today
  (one scalar).
- **Sites + roles.** *Definition*: the one constant. *Consumer*: the
  loop's `min(...)` sizing (same module). *Oracles*: the
  `max(requested) <= limit + 1` assertions (bound, not value, pinned —
  the constant itself is intentionally unpinned so tuning needs no
  oracle edit).
- **Challenges.** C9 → 1.
- **Owner + lifetime.** This module. Tuning constant; no lifetime.
- **Migration.** None.
- **Distinct behavior.** Single-allocation ceiling vs total bound are
  two numbers with different jobs; conflating them re-opens the
  large-limit allocation the constant exists to close.
- **Behavioral proof.** `execution-verified` (one def, one use; probe).
  `static-reviewed` for the bound assertions. Rejects "a second
  chunk-size rule exists".
- **Structural gate.** The `max(requested)` assertions. Negative
  control: a single `read(limit + 1)` passes total-bound assertions on
  small limits and fails the per-call ceiling on a large one.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `tests/test_views.py`
  `4dc9a257…`; searched populations: helper-name census (zero
  non-target hits). Excluded on body strength: none — the constant's
  only consumer is in-module.

### F8 — the operator signals (file-local)

- **Contract + variation.** Two `WARNING` records for the two refusals
  the wire deliberately cannot distinguish (Decision 9
  non-attributability, via the `views.py` / middleware / driver prose):
  `_CORRUPTED_PROBE_LOG_MESSAGE` without traceback (a wrong position
  never raised — no exception exists) and
  `_UNREADABLE_STREAM_LOG_MESSAGE` with `exc_info=True` (a failed read
  always has one — the traceback names which stream died). Same level
  for the same reason (a deployment should see it; not this process's
  error — the level the package already uses in the `types/finalizer.py`
  `:487` and `optimizer/nested_planner.py` `:645-646` advisories, both
  read at HEAD); `logger.exception` / `ERROR` stays with `consumers.py`'s
  in-`except` revalidations that carry a live traceback (`:1549-1573`
  cluster read). The module composes the package root's `logger` by name
  (`from . import logger`, `:128`) — no plan family claims the logger;
  this is composition, not an assignment. Variation axis: the `exc_info`
  presence, parameterized — not copied — in the shared test driver.
- **Sites + roles.** *Definitions*: the two message constants + two
  `logger.warning` calls (in-module; zero non-target uses,
  probe-verified). *Consumers*: none in production (fire-and-record).
  *Oracles*: `_assert_one_unmeasurable_body_was_recorded` (the
  oracle-side driver, body read: identity of `msg`, class-name args,
  level, `exc_type` parameter) + its two thin twins. *Projections*: the
  two message docstrings (level rationale, `consumers.py` contrast).
- **Challenges.** C10 → refused shared form (J3).
- **Owner + lifetime.** This module (signal texts + call sites
  co-owned; the `logger` object stays with the package root).
  Emit-once per refusal; no retention.
- **Migration.** None.
- **Distinct behavior.** The `exc_info` axis is a contract difference,
  not a flag: attaching a traceback to the probe signal would fabricate
  evidence; dropping it from the read signal would hide the only
  actionable detail. The test driver already shares the setup while
  keeping the axis explicit — the DRY shape, on the oracle side.
- **Behavioral proof.** `execution-verified` (two calls, one
  `exc_info`; probe); oracles `static-reviewed`. Rejects "a signal is
  missing its record" and "both signals share one text".
- **Structural gate.** The `msg is MESSAGE` identity assertions (a
  reworded copy passes status oracles, fails identity) + the
  `exc_info is None` vs `isinstance(..., UnreadablePostError)` split.
  Negative control: emitting the probe record at `ERROR` passes
  behavior and fails the level assertion — the level IS the contract.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `consumers.py` `936210e2…`,
  `types/finalizer.py` `77fd9a2d…` (via HEAD — dirty),
  `optimizer/nested_planner.py` `0ad8ff5d…` (via HEAD — dirty),
  `tests/test_views.py` `4dc9a257…`; searched populations:
  `logger.warning` / `logger.exception` censuses at HEAD over the four
  modules. Excluded on body strength: `consumers.py` revalidations
  (in-`except` `ERROR` with live traceback — J3); the two advisories
  (deployment guidance, no refusal attached — same level, different
  rule).

### F9 — the leaf manifest (file-local)

- **Contract + variation.** `__all__ = ("body_exceeds_limit",)` — the
  leaf's one public name. No variation axis.
- **Sites + roles.** *Definition*: the one tuple (`:133`). *Consumer*:
  `views.py` imports the name from the leaf (`:102`; never the root —
  verified: zero hits in `__init__.py`). *Oracles*: none pin the tuple
  (behavior oracles pin the function through the boundary).
  *Projection*: none.
- **Challenges.** C11 → 1 place.
- **Owner + lifetime.** This module. Import-time manifest.
- **Migration.** None.
- **Distinct behavior.** Leaf-direct import (not root re-export) keeps
  the private-compatibility surface out of the package's public root —
  the same leaf-module posture the `views.py` docstring claims for the
  endpoint.
- **Behavioral proof.** `execution-verified` (one tuple, one def, one
  importer; probe + root sweep). Rejects "a second public name
  exists".
- **Structural gate.** The by-name import in `views.py` (a renamed
  function without a manifest update fails at import). No bespoke gate
  owed beyond it: an existence test for the tuple would relieve no
  change obligation.
- **Coupling.** None.
- **Freshness.** Target `a70571ff…`, `views.py` `9f85b0df…`; searched
  populations: root re-export sweep (zero), test-side importer census
  (`tests/test_views.py` only). Excluded on body strength: the package
  root export surface (verified `dry-file-__init__.md` record: 38
  names, none this one).

### Rejected shared forms (no consolidation; durable homes cited)

- **J1 — one driver for every `except Exception` guard.** Considered:
  the 7 probe/read guards here plus the 2 recognition guards in
  `middleware/request_body.py::_package_view_instance` (`:329-343`)
  plus the ~80 other package `except Exception` sites (85 total at
  HEAD, `git grep -c` population). Contract differences: each guard's
  post-failure outcome is position-state-specific (`UNMEASURABLE`
  before anything moved, `CORRUPTED` after, `False` for a capability
  read, fail-closed `True` for the read) while the middleware's decline
  to `None` answers a different question (a read that cannot be
  completed recognized nothing); a shared helper would need an outcome
  mode flag, which principle 5 forbids (a branch no real path reaches).
  Trigger: a new guard needing the same position-state classification.
  Durable home: the target module docstring's totality paragraphs
  (`:102-112`) + `_measured_remaining` / `_bounded_read_exceeds_limit`
  docstrings. Freshness: target `a70571ff…`, middleware `e6e32e78…`.
- **J2 — one shared exact-type gate.** Considered: the 5 checks here
  (`type(position)`, `type(end)`, `type(restored)` x2, `type(chunk)`;
  `:401` / `:416` / `:485` / `:490` / `:571`) with
  `views.py::_resolved_max_request_body_bytes`'s config gate (`:197`)
  and the wider 114-site `type(x) is` population. Contract differences:
  foreign-stream arithmetic/truth-protocol exclusion (a subclass may run
  consumer code inside the boundary) vs constructor/setting validation
  vs per-domain config gates — different validated domains, different
  reasons to change (C6 moves the 5 here and leaves `views.py`
  untouched by design). Trigger: a new foreign-object protocol needing
  exclusion inside a boundary. Durable home: `_measured_remaining`'s
  numeric-protocol paragraphs (`:296-314`) +
  `_measured_by_bounded_read`'s chunk-validation paragraph
  (`:506-509`) — both already cite `views.py` as same-reason precedent,
  not shared code. Freshness: target `a70571ff…`, `views.py`
  `9f85b0df…`.
- **J3 — one shared refusal-signal emitter.** Considered: the two
  `logger.warning` calls here with each other and with `consumers.py`'s
  `logger.exception` revalidation cluster (`:1549-1573`, in-`except`,
  `ERROR`, live traceback). Contract differences: no-exception vs
  always-exception (F8), out-of-`except` `WARNING` vs in-`except`
  `ERROR` with live traceback (recorded in both modules' docstrings).
  The consolidation that WAS owed already happened on the oracle side
  (the shared test driver with the `exc_type` parameter). Trigger: a
  third wire-indistinguishable refusal. Durable home: the two message
  docstrings (`:142-182`) + `_assert_one_unmeasurable_body_was_recorded`'s
  docstring (`tests/test_views.py:1369-1390`). Freshness: target
  `a70571ff…`, `consumers.py` `936210e2…`, `tests/test_views.py`
  `4dc9a257…`.
- **J4 — one shared `limit + 1` helper.** Considered: the bounded-read
  bound (`:570`) with `extensions/resource_policy.py:422`'s evidence
  over-collection and `optimizer/single_parent_fetch.py:283`'s probe
  row (plus the top-level `resource_policy.py:922` `seconds + 1`
  cousin, same evidence family). Contract differences:
  least-information security bound (never-joined over / `BytesIO`
  reinstall under) vs error-report count vs pagination probe (verified
  at all three bodies). Trigger: a new bounded-read measurement.
  Durable home: `_measured_by_bounded_read`'s docstring
  (least-information paragraph, `:544-559`). Freshness: target
  `a70571ff…`, extensions `52084078…` (via HEAD — dirty),
  `single_parent_fetch.py` `e995270a…`, top-level `resource_policy.py`
  (cousin only, no blob recorded — mention, not input).
- **J5 — owning protocol marks here.** Considered: the consolidated
  `request-body-boundary-ordering` row and the open
  `prepared-view-handoff-shape` family. Check fresh: zero `_BOUNDARY_`
  hits in the target (probe-verified, exit-1 grep) — this module is
  measured BY the boundary, never a party to its ordering; the
  probe/restore pair is an in-module round trip, not a cross-module
  handoff. Trigger: a measurement-phase handshake needing a new
  per-request mark. Durable home: `_boundary_ordering.py` module
  docstring (owner by dependency direction; verified run-2 record).
  Freshness: target `a70571ff…`, `_boundary_ordering.py` `197eea8e…`.
- **J6 — moving the measurement into `views.py` or the middleware.**
  Considered: colocating the boolean with its policy (views) or its
  chain position (middleware). Contract differences: views owns
  limit/413 policy and must never name a private attribute
  (probe-verified zero); the middleware owns chain position and must
  never import `views.py`; this module owns the Django-version
  compatibility surface both depend on (spec-046 pins the
  single-siting; the module docstring pins the audited releases
  `:36-60`). Trigger: Django publishing a public bounded-measure API
  at the supported floor (the module deletes or delegates; it does not
  move). Durable home: the target module docstring's Django-contract
  section + spec-046 Decision 7. Freshness: target `a70571ff…`,
  `views.py` `9f85b0df…`, middleware `e6e32e78…`, spec-046
  `8d8adaf2…`.
- **J7 — owning decode/charset/multipart rules here.** Considered: the
  strict-decode and declaration guards living with the measurement.
  Contract difference: this module answers one boolean about bytes and
  never inspects their meaning — code-level sweep confirms zero reads
  of `META`, content type, charset, or multipart state (all mentions
  are docstring prose stating the exclusion, `:90-100`). Trigger: a
  measurement that genuinely depends on the body's declared type.
  Durable home: `views.py::_RequestBodyBoundaryMixin` docstring
  (boundary read twice, `:404-409`) + the target module docstring's
  "deliberately does not do" section. Freshness: target `a70571ff…`,
  `views.py` `9f85b0df…`.

## Defects

None. Every claim checked while tracing held: the single-siting of all
three private attributes (probe-verified over 117 files, quoted AND
attribute instruments); the one importer / one call site of the entry
(probe-verified); zero async, boundary-protocol, patch, policy, or
wire-status code in the target (AST string-aware sweep); upstream shape
at installed Django 6.1 (`hasattr(self, "_body")` x3, `_read_started`
guard x4 with `RawPostDataException` x2, close-and-`BytesIO` replacement
x2, `OSError` → `UnreadablePostError` x4, `_read_started = False` in both
request constructors, `LimitedStream` as an `io.IOBase` subclass) all
matching the module docstring. Floor-version claims (5.2's absent
seekable check, 3.10's absent `seekable` on the spool) rest on the
package's floor CI and the floor-shape oracles (`:1228`, `:1288`), not
on the installed tree — stated as a freshness caveat, not a defect. Axis
6 enumerated clean (no guard-missing member); no docstring contradicts
its body; no layering violation (leaf-direct import, no root re-export,
`os`/`enum`/`io`/`typing` + root `logger` + `TYPE_CHECKING`-only Django
closure). Nothing routed to any owner.

## Pending execution

None. The single execution proof (read-only probe, command in
`### Challenges`) already ran green (`ALL OK (70 checks)`) against the
shared tree; it mutates nothing and opens no database, so no workspace
copy was owed. No pytest was run in the shared tree (zero runs; oracle
bodies were read, not executed). No `execution-deferred` items, no
`gate:` entries (zero production edits, so no regression witness is
owed). Sharded and Postgres cells: inapplicable by construction — the
target reaches no database, alias, or dialect decision (its runtime
closure is stdlib + the root logger + typing-only Django; the probe
runs without Django settings and imports nothing from the package),
stated here for Worker 2's judgment.

Probe custody: `docs/dry/temp-tests/dry-file-_request_body-r2-w1/`
(git-ignored scratch per `.gitignore`; sole file `probe_request_body.py`)
is this item's only scratch scope — retained for Worker 2, for Worker 0
to remove by explicit path after `verified`. The earlier-cycle
`dry-file-_request_body/` scope was never touched (read-only by rule;
not needed). No other scope touched.

## Index rows for Worker 0

Nine file-local rows plus seven rejection rows. Suggested exact rows for
the plan's `## Responsibility index`:

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `request-body-private-attribute-centralization` | `django_strawberry_framework/_request_body.py::body_exceeds_limit` (+ bounded pair) | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-measurement-ladder` | `django_strawberry_framework/_request_body.py::body_exceeds_limit` | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-size-probe` | `django_strawberry_framework/_request_body.py::_measured_remaining` (+ `_Probe`) | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-stream-capability-halves` | `django_strawberry_framework/_request_body.py::_declares_seekable` (+ `_lacks_seek`) | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-stream-restore-verification` | `django_strawberry_framework/_request_body.py::_position_restored` | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-bounded-read` | `django_strawberry_framework/_request_body.py::_measured_by_bounded_read` (+ wrapper) | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-read-chunk-ceiling` | `django_strawberry_framework/_request_body.py::_READ_CHUNK_BYTES` | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-fail-closed-operator-signals` | `django_strawberry_framework/_request_body.py::_CORRUPTED_PROBE_LOG_MESSAGE` (+ twin) | `_request_body.py` | File `_request_body.py` | file-local |
| `request-body-leaf-manifest` | `django_strawberry_framework/_request_body.py` (`__all__`) | `_request_body.py` | File `_request_body.py` | file-local |
| Shared `except Exception` guard driver | `_request_body.py` (rejection recorded here; J1) | `_request_body.py`, `middleware/request_body.py` (+ 85-site population) | File `_request_body.py` | rejected |
| Shared exact-type gate | `_request_body.py` (rejection recorded here; J2) | `_request_body.py`, `views.py` (+ 114-site population) | File `_request_body.py` | rejected |
| Shared refusal-signal emitter | `_request_body.py` (rejection recorded here; J3) | `_request_body.py`, `consumers.py` | File `_request_body.py` | rejected |
| Shared `limit + 1` helper | `_request_body.py` (rejection recorded here; J4) | `_request_body.py`, `extensions/resource_policy.py`, `optimizer/single_parent_fetch.py` | File `_request_body.py` | rejected |
| Ordering-protocol marks in the measurement module | `_request_body.py` (rejection recorded here; J5) | `_request_body.py`, `_boundary_ordering.py` | File `_request_body.py` | rejected |
| Measurement colocated in views/middleware | `_request_body.py` (rejection recorded here; J6) | `_request_body.py`, `views.py`, `middleware/request_body.py` | File `_request_body.py` | rejected |
| Decode/charset/multipart rules in the measurement module | `_request_body.py` (rejection recorded here; J7) | `_request_body.py`, `views.py` | File `_request_body.py` | rejected |

No `## Families` item is owed: no new family is named, and every open
row was traffic-checked fresh with zero hits (table under
`### Enumeration`) — including `prepared-view-handoff-shape`, which this
target does not touch.

## Judgment

Proved zero-edit result. Backstop discharged: 20/20 `ast.Module.body`
members enumerated, 13 challenges run, every rule terminating in a
file-local record (F1-F9) or a rejected shared form with difference,
trigger, and durable home (J1-J7) — no existing plan family gains a
site, no new family named, no consolidation owed, no defect found. The
matrix is discharged against the real surface (six searches, each with
its instrument and population), the 70-check probe is `execution-verified`
with replay command, oracles are `static-reviewed` from bodies read at
HEAD, and every finding carries its gate with negative control plus
freshness fingerprints over 15 inputs (3 read HEAD-pinned for concurrent
dirt). `Status: ready-for-verification/1`.

Tripwire: HEAD `69a253690002fdd413704a7879528c3ded363020` at start,
`69a253690002fdd413704a7879528c3ded363020` at finish — unmoved. Target
still blob `a70571ff5b3849afd01b6ae44e38416acdb27dd0` (no hunk by
anyone). Item-scoped diff vs
`ITEM_BASELINE=e3ed5189c1c9d953419e80ae8bd6efad426c09d9` contains only
this untracked artifact (overwrite of the orphan record) plus the one
git-ignored probe scope `docs/dry/temp-tests/dry-file-_request_body-r2-w1/`
(sole file `probe_request_body.py`, ruff check + format clean, scoped);
zero tracked files changed, zero `## Owned changes` rows. All 15
DRY-adopted ledger paths and all hunt dirt left untouched; the
`inspect_django_type` module was never imported. No pytest run, no
commit, no plan edit, no CHANGELOG.

## Independent verification (Worker 2)

Continuation pass at HEAD `24e6b4d3e74b104779225cd6bbff713880bc48e3`
(run-3 dispatch; the run-2 Worker 2 completed Phase A blind and ended
before Phase B). I adopt
`docs/dry/temp-tests/dry-file-_request_body-r2-w2/phase_a_expectations.md`
as my own already-recorded expectations (R-A..R-I, X-1..X-8, matrix
discharge, 20/20 homing, and its containment note all stand as the
blindness record) and `probe_w2_rederive.py` in the same scope as my own
probe. No `worker-memory/` was read. This section is Phase B only:
reconciliation of the adopted expectations against `## Findings`, member
by member over the full enumeration, never by sample.

### Probe re-verification at the new HEAD

The first run of the adopted probe at the new HEAD fired its head
tripwire, as expected rather than as a failure: `FAIL head: expected
'69a253690002fdd413704a7879528c3ded363020', got
'24e6b4d3e74b104779225cd6bbff713880bc48e3'`. I edited the adopted probe
in place (the scope is mine now; `docs/dry/temp-tests/` was listed
first, no successor scope created, no other scope touched) and re-pinned
head to `24e6b4d3`, the 4 moved blobs (table below), and the type
population 114 -> 116.

Correction to the dispatch brief, grounded in bytes: the adopted probe
was NOT green at the old HEAD. It carried 10 latent instrument defects,
each failing deterministically at BOTH heads (proven by replaying the
old instruments against `69a25369` bytes, whose target/test/views blobs
are identical to the new HEAD's): the `entry-nondef` right-split parse
(colon-bearing `:func:` / `::` / trailing-colon content), the
`exact-gates` `"type(" in ast.dump(n)` test (the substring never
occurs), 6 pin tokens in shorthand rather than the literal def-name
substrings (`non_seekable`, `probes_as_empty`, `to_lie`,
`cannot_restore`, `cannot_be_read`, `no_stream_at_all`), and the
`schema-stream` / `toolbar-body-read` off-by-one on the
revision-prefixed grep format (`[1]` -> `[2]`). Every underlying
expectation held — the 5 entry lines, the 5 gates, all 24 pinned rows,
both exclusions — only the instruments were broken, so this is probe
repair, not a verdict change. The repaired probe also gains 2
`grep`-rc checks (silencing RUF059) and a full `ruff format` pass.
Final: `ALL OK (122 checks)`, exit 0, at `24e6b4d3`. W1's independent
probe re-run read-only at the new HEAD: `ALL OK (70 checks)`.

### Carried delta: 4 of 15 inputs moved — CONFIRM + re-pin

Each cite re-derived from HEAD bytes (`git show HEAD:` / `git grep
HEAD`); the brief's pointers checked, never trusted.

| Input | Old -> new blob | Cite at new HEAD | Range hunk | Verdict |
|---|---|---|---|---|
| `optimizer/nested_planner.py` | `0ad8ff5d` -> `b4dfd4a6` | F8 advisory `:645-646` intact (`log = logger.warning if settings.DEBUG else logger.debug` + call) | docstring-only edit at `:1073`, below the cite | CONFIRMED |
| `extensions/resource_policy.py` | `52084078` -> `38801833` | J4 evidence site `:422` intact (`limit + 1` as `actual` of `ResourceLimitExceeded`; body re-read) | 1-for-1 `DEFAULT_RESOURCE_POLICY` -> `_PACKAGE_RESOURCE_POLICY` swaps at `:103` / `:1271` | CONFIRMED |
| `schema.py` | `c2e1b748` -> `19f90bf5` | F1 exclusion `:1114` intact (`super()._stream`) | 1-for-1 policy renames at `:63` / `:75` / `:466-467` / `:1078`, all above the cite | CONFIRMED |
| `docs/GLOSSARY.md` | `bc51debc` -> `d3ef357c` | F2 anchor `## Request-body cap` `:1724` intact; entry `:1724-1740` byte-identical (hash `b2338841` at both heads) | hunks at `:24` / `:838` / `:1124` / `:1555` / `:1571` (version, policy, prefetch entries) | CONFIRMED |

The other 11 inputs are byte-identical (all 15 blobs re-derived and
probe-pinned). Two derived values re-pin with cause: the exact-type
population 114 -> 116, from 2 new gates in `error_policy.py:114` /
`:120` (the range's exact-type close; every other per-file row
identical; J2's contract difference untouched — a population size is not
a definition count); and the unblobbed cousin mention `seconds + 1` in
top-level `resource_policy.py`, `:922` -> `:946` (same
`ResourceLimitExceeded` evidence shape, re-read — mention only, the
finding never depended on its line).

### Reconciliation: adopted R/X vs artifact F/J over the 20/20

Enumeration agrees 20/20 (adopted #0-19 = artifact #1-20, same binds,
same instrument). Definition counts agree on every rule:

| Adopted | Artifact | Count verdict |
|---|---|---|
| R-A private-attr centralization | F1 | agree, file-local, C1/C1b -> 1 |
| R-B measurement ladder | F2 | agree, file-local, C2 -> 1 |
| R-C three-outcome probe | F3 | agree, file-local, C3 -> 1, C3b refused by contract both sides |
| R-D capability-gate pair | F4 | agree, file-local, C4 -> 1 |
| R-E restore verification | F5 | agree, file-local, C5 -> 1 |
| R-F bounded-read pair | F6 | agree, file-local, C7 -> 1, C8 refused by contract both sides |
| R-G chunk ceiling | F7 | agree, file-local, C9 -> 1 |
| R-H operator signals | F8 | agree, file-local, C10 refused shared form both sides |
| R-I leaf manifest | F9 | agree, file-local, C11 -> 1 |
| X-1 exact-type | J2 | agree (adopted adds `views.py:556` + `consumers.py:572` as further same-idiom sites — consistent, no conflict) |
| X-2 `except Exception` | J1 | agree (85-population re-derived intact) |
| X-3 WARNING signals | J3 | agree (adopted adds the `resolvers.py` alias + `debug.py:768` siblings — consistent) |
| X-4 `limit + 1` | J4 | agree (evidence-site body re-read at new HEAD) |
| X-5 bounded-vs-adapter | F6 exclusion + matrix axis 1 | same verdict (different rule); W1 records the legs as body-strength exclusions rather than a standalone row — record-shape difference only, accept |
| X-6 ordering/colocation/decode | J5/J6/J7 | adopted expected no rows ("absence is conformance"); W1 wrote explicit rejections. Per the adopted note itself this stands provided each names second site + trigger — J5/J6/J7 each name both plus a durable home. Accept; the explicitness aids the next cycle's trigger check |
| X-7/X-8 logger/scaffolding | machinery rows + F9 | agree, no shared form considerable |

Adopted-expectation errata (my own lines, corrected from HEAD bytes;
the frozen Phase-A record stands as history): `finalizer.py` `:502` ->
`:487`, `nested_planner.py` `:654` -> `:645-646`,
`extensions/resource_policy.py` `:426` -> `:422`. W1's lines verify
correct at BOTH heads (old-HEAD bytes included). The substance of all
three adopted claims holds at the corrected lines. Expectation errata,
not `## Defects` entries — no system bug in any of them.

Open-plan-row traffic: agree with the artifact's table — no open row
gains a site, no new family, nothing to route to any holding family.
`prepared-view-handoff-shape` gains nothing (zero `_BOUNDARY_` hits,
probe-verified); the patch, sync-boundary, queryset, and lookup rows
gain nothing (zero-vocabulary instruments re-derived green).

### Matrix, gates, pending execution, prose rules

- **Matrix.** Axes 1/3/4/5/6 searched with named instruments and
  populations; axis 2 inapplicable-by-construction (zero async nodes
  probe-verified; one sync body reached from both view colors) — judged
  sound against the target's real surface. Axis 6 enumerates all 24
  oracle rows plus the deliberate passthroughs with contract sources.
- **Site roles.** Agree throughout. Zero test edits in the item diff, so
  no oracle could have been rewritten to read from its owner. The root
  re-export absence is re-derived (exit-1).
- **Gates + negative controls.** All nine findings carry a gate with a
  control that fails while behavior oracles pass (F1 count-search vs a
  hand copy; F2 the `:1908` row; F3 bound assertions vs `max()`; F4
  divergent sibling rows; F5 the zero-call unit row; F6 the
  over-limit triple + `RawPostDataException` preservation vs an
  unguarded read; F7 `max(requested)`; F8 identity + the `exc_info`
  split vs ERROR level; F9 the by-name import, with a bespoke gate
  explicitly refused as obligation-free). No gate-only findings; F1's
  package-wide check is correctly deferred to a family item. Judged
  sufficient for a zero-edit file item.
- **`## Pending execution`.** Correctly `None`. Both probe replays below
  are `execution-verified` with commands; the sharded/Postgres
  inapplicability reason is judged sound (the target's runtime closure
  is stdlib + the root logger + TYPE_CHECKING-only Django; both probes
  import nothing from the package and open no database).
- **Item diff vs `ITEM_BASELINE=e3ed5189`.** Zero tracked files (the
  target diff is empty); the diff is this untracked artifact plus the
  two git-ignored probe scopes. No production or test file touched —
  correct for a zero-edit file item. The baseline-to-worktree drift
  elsewhere is concurrent work by content, untouched here.
- **AGENTS.md prose.** Citations use `path::Symbol` plus scratchpad
  `:NNN` (allowed in `dry-*.md`); no tests added (tier N/A). Banned
  words over the item diff: zero test files, so the test-tier ban holds
  — remaining tokens are DRY-required vocabulary (`plan` rows, `Worker`
  roles, `sweep` instruments), the `nested_planner` module name, and one
  domain phrase (`audited releases`); zero hits for the rest. My own
  writes add no banned-list token outside that vocabulary.
- **Ruff.** `uv run ruff check` and `uv run ruff format --check` both
  clean on the one `.py` path touched (the adopted probe; the
  check-fix-format cycle ran scoped to that file only).

Replay commands, both `execution-verified` at `24e6b4d3`:

```shell
uv run python docs/dry/temp-tests/dry-file-_request_body-r2-w1/probe_request_body.py
uv run python docs/dry/temp-tests/dry-file-_request_body-r2-w2/probe_w2_rederive.py
```

Scratch custody: the adopted scope
`docs/dry/temp-tests/dry-file-_request_body-r2-w2/`
(`phase_a_expectations.md` frozen as the blindness record;
`probe_w2_rederive.py` re-pinned, repaired, formatted) is retained for
Worker 0 to remove by explicit path after `verified`. The W1 scope was
read and executed read-only, never written.

### Verdict

`Status: verified`. The zero-edit stands: 20/20 coverage, every rule
file-local or rejected with trigger + home, no open plan row gains a
site, no new family named, no candidate to route, no defects found (no
`## Defects` entries). Freshness at close: HEAD `24e6b4d3`, target
`a70571ff` clean in tree, 15/15 blobs re-pinned above (11 identical, 4
moved-and-confirmed), populations 117 files / 85 `except Exception` /
116 exact-type.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
