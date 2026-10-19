# DRY review: `django_strawberry_framework/views.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in a plan-indexed family (reused where the same rule appears
elsewhere, re-derived never inherited) or in a file-local row with its proving
challenge. Zero production edits; zero tracked files changed.

## System trace

Large target (1066 lines): the package's Django GraphQL HTTP endpoint. It OWNS
the transport surface two views mount in a consumer URLconf
(`django_strawberry_framework/views.py::DjangoGraphQLView`,
`::AsyncDjangoGraphQLView`, thin subclasses of Strawberry's Django views), the
cumulative request-body cap and its per-mount precedence ladder (spec-046
Decision 7), the strict UTF-8 wire contract for non-multipart bodies (Decision
9) with the sync body source that makes it reachable in every patch state, the
multipart codec guards plus the lossy-control-document detector, and the
view-local half of the CSRF ordering (withdrawable exemption stamp,
boundary-then-CSRF continuations per transport). It CONSUMES, by name, the
ordering protocol (`_boundary_ordering.py` marks/method-name/exemption),
the body measurement (`_request_body.py::body_exceeds_limit`), the setting rung
(`conf.py::max_request_body_bytes_setting`), and the typed tail
(`exceptions.py::describe_value`). It ENFORCES nothing belonging to another
module: the patch modules' translations, the middleware's chain position, and
Django's own upload ceilings stay theirs.

Connected code read for judgment, outside the item (whole bodies, not samples):
`_boundary_ordering.py` (full: marks, method name, exemption predicate),
`middleware/request_body.py` (full: twins, `process_view`, recognition,
misordering guard), `_request_body.py` (contract half: private-Django pin,
probe ladder, bounded read; bodies), `_strawberry_patches.py` (full: three
lifecycles, translator, envelope guard, GET shield, multipart delegates),
`_cross_web_patches.py` (full: bare-decode bug, raw-bytes getter, retirement
probes), `conf.py` (setting rungs: `max_request_body_bytes_setting`,
`upstream_patches_enabled` contract), `exceptions.py::describe_value` (full:
raise-site failure mode, transport-boundary scope), `consumers.py`
(`resolved_revalidation_window` + `_unusable_window_error`, full bodies),
`routers.py` (docstring mount example; `describe_value` tails),
`resource_policy.py` (int-gate + `describe_value` tails),
`middleware/debug_toolbar.py` (sibling recognizer, read for the axis-1 sweep),
installed upstream `strawberry/http/base.py` (`parse_json`, `decode_json`,
`is_request_allowed`), `strawberry/http/sync_base_view.py` (`run`,
`parse_http_body`), `strawberry/http/async_base_view.py` (`run`),
`strawberry/django/views.py` (both `dispatch` bodies, both view classes, full
import list), `cross_web/request/_django.py` (both adapters, full),
installed Django `http/request.py` (`_load_post_and_files`,
`_set_content_type_params`, `parse_file_upload`), `http/multipartparser.py`
(`__init__` encoding default, `_parse` FIELD/FILE branches),
`utils/decorators.py` (`make_middleware_decorator` coroutine branch),
`views/generic/base.py` (`as_view` keyword guard), `middleware/csrf.py`
(`csrf_exempt` truthiness read). Oracles: `tests/test_views.py` (82/82 titles
censused; 6 bodies fully read: wire-reason pin, sync-adapter patch-state pin,
async-no-override pin, shared-`parse_json` MRO pin, str-handoff attribution,
declared-length reader), `examples/fakeshop/test_query/test_transport_api.py`
(61 titles censused across cap/wire/multipart/CSRF/ordering/chain sections).
Projections: `docs/README.md` transport paragraphs, `docs/GLOSSARY.md`
`DjangoGraphQLView` / request-body-cap / UTF-8-wire-contract entries, the
`routers.py` mount example, archived spec-046 (historical only, never relied
upon). Excluded with reason: filter/order/mutation/form/rest_framework
surfaces (no transport vocabulary; verified by package-wide name sweeps, not
by body audit), optimizer/types/schema internals (no body path; the schema
`describe_value` tails are the typed-tail family's, already indexed),
`auth/sessions.py::require_channels` (sibling guard, different transport),
`utils/imports.py::require_optional_module` (mechanism precedent only),
`connection.py` + `tests/test_connection.py` + staged
`tests/utils/test_querysets.py` + `docs/bug_hunt/bug_hunt-0_0_15.md` +
`docs/dry/dry-0_0_15.md` (concurrent dirt per the plan item: never read for
verdicts, never touched).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Package-wide sweeps (117 files,
`docs/dry/temp-tests/dry-file-views/probe_views.py` sections 3-4): `def
parse_json` occurs exactly once (`views.py::_RequestBodyBoundaryMixin`);
`max_request_body_bytes` / `_BODY_LIMIT_REASON` occur only here (plus oracle
imports); no filter/order/mutation/form/rest_framework module names the body,
the cap, the wire reason, or the boundary method. The two apparent siblings
are both recorded rejections, re-derived below: `consumers.py`'s window
validator (R5: different domain, different `None`/coercion semantics) and the
patch modules' translator/guard/getter (R1-R3: opposite lifecycles). The
toolbar recognizer (`middleware/debug_toolbar.py`, class-based over global
traffic) vs the boundary's exact-mount recognition is the already-indexed
F1 separation; nothing new found from this side.

**2. Sync/async twins.** Three colored pairs, one shared core, one deliberate
asymmetry — compared by behavior, not shape. `run` sync/async: identical order
(boundary-once, then CSRF continuation, then upstream `run`); the `await` and
the second continuation exist because `csrf_protect` branches on
`iscoroutinefunction` (verified in installed `make_middleware_decorator`
source). `parse_multipart` sync/async: policy lives once on the mixin
(`_reject_lossy_multipart_control_fields`); the overrides differ only where
upstream's own signatures differ (verified: sync returns `dict`, async is a
coroutine taking `AsyncHTTPRequestAdapter`). `parse_json`: NO twin — one mixin
method serves both (probe: `view_class.parse_json is mixin.parse_json` on both,
MRO owners exactly `[mixin, BaseView]`). Asymmetry:
`DjangoGraphQLView.request_adapter_class is _RawBodyRequestAdapter` while the
async view keeps upstream's adapter — pinned, not drifted: upstream's sync
`body` property bare-decodes (`self.request.body.decode()`, verified) while
async `get_body` already returns raw bytes (verified). Both `dispatch` bodies
catch `HTTPException` into `text/plain` (verified sync + async), so the
413/400 translation holds on both transports.

**3. Derived rather than repeated knowledge.** No reconstructed copies found.
The 1 MiB default lives in `conf.py::max_request_body_bytes_setting`; views.py
never restates the number (probe: no `1048576` literal) and the resolver reads
the setting live per request. `_UTF8_CODEC_NAME` is `codecs.lookup("utf-8")`
evaluated once, so unknown aliases are accepted by canonicalization, never by
an alias list (probe matrix: `utf8`/`U8` accepted, `utf-8-sig`/Latin-1/unknown/
non-string refused). The effective form encoding is read live
(`request.encoding or settings.DEFAULT_CHARSET`, Django's own expression
verified at both use sites), so a project reconfiguring `DEFAULT_CHARSET`
moves behavior with zero code edits (challenge C8 moves 0 definitions). The
mount token is a per-`as_view`-call `object()` (identity, not knowledge).
`max_request_body_bytes` is declared once, on the mixin (probe: absent from
both views' `vars`), satisfying Django's `hasattr` keyword guard on both.

**4. Inverse / round-trip pairs.** Three pairs, each single-owned here or
already indexed. Stamp/read round trips (MARKER/MOUNT/ENFORCED/PREPARED_VIEW)
are F1's; this side verified as pure consumer (probe: zero mark literals in
views.py). Refusal/render round trip: `run` raises `HTTPException`, upstream
`dispatch` renders `text/plain` — verified on both transports' `dispatch`
bodies; the middleware's `process_view` renders the same shape itself
(read at its body), so a refusal is indistinguishable across the CSRF check.
Bytes/text round trip: adapter hands `bytes`, `parse_json` decodes strictly to
`str`, upstream `decode_json` (`json.loads`) never sees `bytes` from a package
view (probe: recorder sees exactly `str`), which is what makes RFC 8259
auto-detection unreachable by construction rather than by a rejection branch.

**5. Contracts restated in another medium.** Production (this file + the two
patch modules + the middleware); oracles that compose by name
(`tests/test_views.py` imports `_JSON_PARSE_REASON`, `_RawBodyRequestAdapter`,
the boundary constants rather than respelling values; the wire-reason oracle
pins BOTH reason constants against upstream's live raise, so a message change
fails loudly); live oracles (`test_transport_api.py`: 11 cap rows, 8 UTF-8
rows, 7 body rows, multipart/CSRF/ordering/chain rows); projections
(`docs/README.md`, `docs/GLOSSARY.md`, `routers.py` example — describe, never
own). The one string-spelling in tests that matters is the principle-9 gate
for F2 (def-vs-constant identity, owned there). No test restates a boundary
string, a mark, or the 1 MiB default.

**6. Enforcement by omission.** Family enumerated: {sync view, async view} x
{cap, strict decode, multipart-encoding guard, charset-declaration guard,
lossy-control guard, CSRF ordering}. Every cell enforced on both: both `run`
methods call `_enforce_request_boundary_once` (cap + both header guards);
`parse_json` resolves to the mixin on both (MRO oracle); both
`parse_multipart` overrides call the lossy check (sync via `post_data`, async
via awaited `get_form_data` — Django caches POST/FILES, verified pattern);
both `run` methods continue through their CSRF continuation. Deliberate
non-coverages, each with a contract source: GET skips cap + encoding guards
(the view reads no body on GET; Django decodes no GET form — hostile-length
oracle pins the no-materialize direction); multipart skips the counted check
(reading it would defeat streaming upload handlers; Django's own upload
settings own that shape — stated co-requirement, live upload-streaming
oracle); multipart skips the charset guard (the form-encoding guard owns that
shape — intentional non-overlap, C11 moves 0). Checked shape that stays parity
rather than a gap: a *negative* `CONTENT_LENGTH` on a non-multipart body is
safe by construction (the counted check decides); on a multipart body it
reaches Django's `MultiPartParser`, which raises exactly as it does under
Strawberry's own view — no package contract names that shape, and no oracle
owes it. No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **36 top-level statements**. Class methods counted with their
owners (mixin 8, adapter 1, sync view 2, async view 2). Every member lands
below; every challenge in `### Challenges` ends in a family row, a file-local
row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (transport + boundary prose) | (none) | projection, F1-F4/R1-R3/L1/L7/L10 |
| 2 | `from __future__ import annotations` | (none) | machinery |
| 3 | `import codecs` | `codecs` | machinery for L3 |
| 4 | `from functools import wraps` | `wraps` | machinery for L7/L8 |
| 5 | `from typing import ...` | names | machinery (annotation guard) |
| 6 | `from cross_web import ...` | adapters/exception | machinery for R1/L9 |
| 7 | `from django.conf import settings` | `settings` | machinery for L4 (live read) |
| 8 | `from django.utils.decorators import classonlymethod` | decorator | machinery for L8 |
| 9 | `from django.views.decorators.csrf import csrf_protect` | decorator | machinery for L7 |
| 10 | `from strawberry.django.views import ...` | view bases | machinery for L8/L9 |
| 11 | `from _boundary_ordering import ...` | 5 names | consumer import, F1/F2/F3 |
| 12 | `from _request_body import body_exceeds_limit` | predicate | consumer import, L1 |
| 13 | `from conf import max_request_body_bytes_setting` | setting rung | consumer import, L1 |
| 14 | `from exceptions import ConfigurationError, describe_value` | error + tail | consumer import, L1/F4 |
| 15 | `if TYPE_CHECKING:` + 3 imports | (annotations) | machinery (zero runtime import; channels-free evidence) |
| 16 | `__all__` | 2 view names | L10 |
| 17 | `_BODY_LIMIT_REASON = ...` | 413 reason | L1 |
| 18 | `_JSON_PARSE_REASON = ...` | 400 reason | R3 (re-derive) |
| 19 | `_MULTIPART_CONTENT_TYPE = ...` | media type | L2 |
| 20 | `_MULTIPART_CONTROL_FIELDS = ...` | `operations`/`map` | L6 |
| 21 | `_REPLACEMENT_CHARACTER = ...` | loss marker | L6 |
| 22 | `_UTF8_CODEC_NAME = ...` | canonical name | L3 |
| 23 | `def _resolved_max_request_body_bytes` | cap ladder | L1 (+F4 consumer, R5/R6) |
| 24 | `def _declared_content_length` | fast path | L1 |
| 25 | `def _canonicalizes_to_utf8` | codec predicate | L3 |
| 26 | `def _declared_charset_is_unhonourable` | declaration predicate | L5 (shared by L4) |
| 27 | `def _form_encoding_is_utf8` | 2-condition gate | L4 |
| 28 | `def _is_multipart_form_post` | POST+type gate | L2 (shared by L1/L4/L5) |
| 29 | `class _RawBodyRequestAdapter` + `body` | sync body source | R1 (re-derive) |
| 30a | `...Mixin.as_view` | ordering stamp | F1/F3 (consumer) |
| 30b | `...Mixin._enforce_request_boundary` | 3-guard order | F2 (behavior referent) + L1 (order) |
| 30c | `...Mixin._enforce_request_boundary_once` | skip-if-stamped | F1 (consumer) + L8 (shared) |
| 30d | `...Mixin._enforce_request_body_limit` | cap enforcement | L1 |
| 30e | `...Mixin._enforce_multipart_form_encoding` | form guard | L4 |
| 30f | `...Mixin._enforce_body_charset_declaration` | charset guard | L5 |
| 30g | `...Mixin._reject_lossy_multipart_control_fields` | marker check | L6 |
| 30h | `...Mixin.parse_json` | strict decode | R2 (re-derive) |
| 31 | `def _run_after_csrf_check` | sync continuation | L7 |
| 32 | `async def _async_run_after_csrf_check` | async continuation | L7 |
| 33 | `_csrf_protected_run = csrf_protect(...)` | wrapped instance | L7 |
| 34 | `_csrf_protected_async_run = csrf_protect(...)` | wrapped instance | L7 |
| 35 | `class DjangoGraphQLView` + `run` + `parse_multipart` | sync mount | L8/L9 (seam: R1) |
| 36 | `class AsyncDjangoGraphQLView` + `run` + `parse_multipart` | async mount | L8/L9 |

Rules: L1 cap ladder + limit order; L2 multipart identity; L3 codec
canonicalization; L4 form-encoding gate; L5 charset-declaration gate; L6 lossy
control rejection; L7 CSRF continuation twin; L8 view `run` twin; L9
multipart-parse twin; L10 leaf manifest + channels-free discipline. Reused
families: F1 `request-body-boundary-protocol-marks`, F2
`boundary-method-name-single-sourcing`, F3 `csrf-ordering-exemption`, F4
`typed-rejection-value-tail` (all indexed `open`). Re-derived rejections: R1
`sync-adapter-raw-body-source`, R2 `decode-failure-400-translation`, R3
`request-body-json-parse-reason`, R4 `upstream-patch-install-lifecycle`
(checked, not a member), R5 window-vs-cap validator, R6 exact-type idiom, R7
multipart structure-vs-encoding split (new), R8 GET query-param semantics
absence (new).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted. Execution claims below are `execution-verified` by
`docs/dry/temp-tests/dry-file-views/probe_views.py` (58 sections green, shared
tree, no settings, no DB); oracle bodies named are `static-reviewed` except
where the probe re-proves the property.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | L1 ladder | add a fourth rung (e.g. per-request override) | **1** (the resolver; `conf.py` thin reader untouched) | independent |
| C2 | L1 gate | `0` disables the cap instead of failing loud | **1** (the `<= 0` arm; docstring pins the refusal) | independent |
| C3 | L1 order | skip the counted check whenever a declaration is present | **1** (the limit method; refused — a declaration cannot buy a larger body) | independent |
| C4 | L1 reason | reword the 413 reason | **1** (the constant; live tier imports it by name) | independent |
| C5 | L2 identity | treat a GET multipart content type as a form | **1** (the discriminator; Django parses no GET form and upstream 405s non-GET/POST — both verified) | independent |
| C6 | L3 codec | accept `utf-8-sig` | **1** (the predicate; the constant untouched — a different codec, verified) | independent |
| C7 | L3 codec | support a brand-new UTF-8 alias | **0** (`codecs.lookup` derives it; probe matrix) | independent |
| C8 | L4 encoding | project sets `DEFAULT_CHARSET=latin-1` | **0** (reads Django's live expression; behavior follows the deployment) | independent |
| C9 | L4 encoding | honor a per-part charset | **0** (refused — Django consults it in the FILE branch only, verified) | independent |
| C10 | L5 charset | decode with the declared charset instead of refusing | **1** (the guard; refused — reopens the Decision 9 success set) | independent |
| C11 | L5 overlap | also check the charset here for multipart | **0** (excluded by construction; L4 owns that shape) | independent |
| C12 | L6 loss | client sends the six-char ASCII escape for U+FFFD | **0** (preserved exactly; only the literal marker refused — live oracles) | independent |
| C13 | L6 loss | control value arrives as `bytes` | **0** (left alone for the strict decode by construction) | independent |
| C14 | L7 continuation | add a step to the CSRF re-entry | **2** bodies, **1** rule, 2 colors (principle-5 two-machines: `csrf_protect`'s `iscoroutinefunction` branch forces the split, verified) | intentional separation |
| C15 | L7 continuation | drop the async twin and wrap the sync one | breaks (a coroutine reaches `process_response`; installed branch + async CSRF rows) | refused by mechanism |
| C16 | L8 run | reorder boundary/CSRF/upstream | **2** bodies, **1** rule, 2 colors (the `await` is the only difference; twin docstring states it) | intentional separation |
| C17 | L8 run | skip `_once` on one transport | omission defect on that transport (both call it; no contract allows skipping — the middleware stamp is the only skip, read inside `_once`) | shared, enforced |
| C18 | L9 multipart | change the lossy policy | **1** (the mixin method; both overrides follow as consumers) | independent |
| C19 | L9 multipart | unify the two overrides into one body | refused (upstream's own sync/async split; signatures verified different) | refused by mechanism |
| C20 | F1 consumer | rename one protocol mark | **1** (owner constant; views.py follows — probe: zero mark literals here) | independent here |
| C21 | F2 referent | rename `_enforce_request_boundary` | **1** name definition + **1** behavior referent here (agreement gated by the def-vs-constant oracle) | independent here |
| C22 | F3 consumer | stamp plain `csrf_exempt = True` | breaks withdrawal (probe: no plain stamp; both-state oracles pin) | consumer, correct |
| C23 | F4 consumer | change the `got` tail grammar | **1** (`exceptions.py::describe_value`; this call site follows) | independent here |
| C24 | R1 retirement | upstream stops eager-decoding the sync body | patch deletes, subclass stays (**1** survivor, not a shared abstraction) | rejection stands |
| C25 | R1 sharing | point the subclass at the patched getter | refused (couples permanent policy to the switchable workaround) | refused |
| C26 | R2 new mode | a third client-input raise escapes upstream's `except` | **1** (the translator; the view's decode raises only `UnicodeDecodeError` by construction + delegates `str`) | rejection stands |
| C27 | R2 sharing | view delegates decode errors to the translator | refused (kill-switch coupling — the exact split defect) | refused |
| C28 | R3 message | upstream changes its parse-failure message | **2** literals move, pinned by **1** oracle that fails loud (deliberate; imports would couple deletability both ways) | rejection stands |
| C29 | R4 membership | gate views.py behavior on `APPLY_UPSTREAM_PATCHES` | **0** (no gate vocabulary here — prose mentions only; verified by import/call sweep) | not a member |
| C30 | R5/R6 sharing | one numeric validator / one exact-type helper for views + consumers (+ resource_policy) | refused (different admitted sets `{int}` vs `{int,float}`, different `None`/coercion/overflow semantics, different refused outcomes; Python idiom, not a package rule) | rejection stands |
| C31 | R7/R8 split | third control document / new query param | **1** each at the already-owning site (tuple / shield source pin); the other side moves **0** | rejection stands |

## Findings

### F1 — request-body-boundary protocol marks (existing family `request-body-boundary-protocol-marks`, stays `open`)

- **Contract + variation.** The four ordering-protocol names live once in
`_boundary_ordering.py`; views.py stamps/reads them by name. Variation: one
row per mark, same reason to change (the ordering protocol).
- **Sites + roles.** *Definitions*: the four constants (owner elsewhere;
probe-verified sole spellings, zero literals here). *Consumers (this file)*:
`views.py::_RequestBodyBoundaryMixin.as_view` (stamps MARKER/MOUNT, assigns
the exemption, consumes PREPARED_VIEW via the `prepared_view` closure),
`::_enforce_request_boundary_once` (reads ENFORCED). *Oracles*: the
`tests/test_views.py` ordering rows + `test_transport_api.py` marker rows
(static-reviewed by title; bodies verified under the F1 owner's item).
*Projections*: this module's ordering paragraphs.
- **Challenges.** C20 → 1 here-relevant definition (the owner); C21-adjacent
rename coupling gated by the def-vs-constant oracle.
- **Owner + lifetime.** Unchanged: `_boundary_ordering.py` (dependency
direction — neither side may import the other, re-verified by import sweep:
views.py imports the protocol module, never the middleware, and vice versa).
No stored derivation here beyond the per-call mount token (`object()`
identity, no lifetime).
- **Migration.** None (zero-edit file item).
- **Distinct behavior.** The `prepared_view` consume-once closure
(`delattr` after read) is this file's own handoff hygiene, not a second
protocol definition: posit deleting the `delattr` → stale prepared instances
reused across dispatches — 1 body here, protocol untouched.
- **Behavioral proof.** `execution-verified` (probe: marker+mount stamped on
both callbacks, exemption singleton assigned, no plain-`True`, no literals).
Rejects "a call site restates a protocol string".
- **Structural gate.** The by-name import discipline + the callback-mark
oracles on both transports. Negative control (static): hand-spelling any
literal at the stamp site passes every behavioral oracle and fails only a
literal-count search — the family item owes that search (already recorded at
the owner).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/views.py`
`9f85b0df26a17e800ec392aa13f6848e07633895`,
`django_strawberry_framework/_boundary_ordering.py`
`197eea8e01cb405f38b21022689ed54970efcb97`,
`django_strawberry_framework/middleware/request_body.py`
`e6e32e785ec84360c63c9ff529a58f8d63bc8898`, `tests/test_views.py`
`fa97efdf3309c2944431390a36e7da464c3de327`. Population: 117 package files
(probe section 5).

### F2 — boundary-method-name single-sourcing (existing family `boundary-method-name-single-sourcing`, stays `open`)

- **Contract + variation.** The name the chain may run IS the name probed:
one constant drives probe + invoke; the behavior `def` lives here and never
spells the string.
- **Sites + roles.** *Definition*: `_BOUNDARY_METHOD` (owner elsewhere).
*Behavior referent (this file)*:
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary` (the `def`;
probe: no string spelling in this file). *Consumers*: the middleware's probe
and invoke (read at their bodies). *Oracle*: the def-vs-constant identity row
(static-reviewed title + verified account at the owner item).
- **Challenges.** C21 → 1 protocol-name definition + 1 cross-rule referent
here; the 3-guard call order inside the `def` (size first, headers-only next)
is L1's, not a second name owner — posit reordering the guards → only this
body moves, constant untouched.
- **Owner + lifetime.** Unchanged: NAME with `_boundary_ordering.py`,
BEHAVIOR here. No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Guard order (size → multipart-encoding →
charset-declaration) is a safety property of this body: the size gate must run
before anything touches the body; the two header-only checks parse nothing.
- **Behavioral proof.** `execution-verified` for no-second-spelling (probe);
behavioral order `static-reviewed` at the body (calls read in order).
- **Structural gate.** The def-vs-constant + probe-vs-invoke oracles (owner
item). Negative control (static): spelling the literal at an invoke site
passes both and fails only a package-wide string-count search — owed by the
family item.
- **Coupling.** None.
- **Freshness.** Same four hashes as F1.

### F3 — CSRF-ordering exemption (existing family `csrf-ordering-exemption`, stays `open`)

- **Contract + variation.** Per-request answer (chain already ordered this
request?) owned elsewhere; this file assigns the singleton and supplies the
view-local re-entry both states compose.
- **Sites + roles.** *Definitions*: channel + predicate + instance (owner
elsewhere). *Consumers (this file)*: `as_view` (`view.csrf_exempt =
_CSRF_ORDERING_EXEMPTION` — probe: identity with the singleton, no plain
stamp), `_run_after_csrf_check` / `_async_run_after_csrf_check` (the re-entry
both arrangements share), both `run` methods (call order). Django's own
`CsrfViewMiddleware.process_view` reads the mark for truthiness (verified in
installed `django/middleware/csrf.py`, Django 6.1; floor axis with CI).
*Oracles*: the both-transports callback-mark rows, the declined-callback and
no-CSRF-entry matrix rows (titles censused; bodies under the owner item).
- **Challenges.** C22 → consumer-correct (no definition here); C14/C15 (twin
shape) → L7.
- **Owner + lifetime.** Unchanged: `_boundary_ordering.py`. The wrapped
continuations' one-`CsrfViewMiddleware`-instance-per-transport lifetime is
L7's (module-level decoration, stateless delegates — read at the body).
- **Migration.** None.
- **Distinct behavior.** The continuations add no policy: they exist so the
boundary runs before Django's `request.POST` read on the fallback
arrangement. The two documented non-guarantees (consumer middleware parsing
first; no cookie refresh on in-continuation refusals) are stated limits, not
second rules.
- **Behavioral proof.** `execution-verified` (probe: singleton identity +
truthiness outside a chain on both callbacks). Rejects "the view stamps a
bypass".
- **Structural gate.** The both-states CSRF-matrix oracles (owner item).
Negative control (static): `csrf_exempt = True` passes the no-middleware
rows and fails exactly the chain-supplies-ordering rows.
- **Coupling.** None.
- **Freshness.** Same four hashes as F1 plus installed
`django/middleware/csrf.py`
`3c709f2f4b276fdf837377e93e7f104c46b53dc4` (Django 6.1; floor with CI).

### F4 — typed-rejection value tail (existing family `typed-rejection-value-tail`, stays `open`)

- **Contract + variation.** Every typed rejection on the transport boundary
renders its `got` tail through `exceptions.py::describe_value`, because the
f-string runs at the raise site where a hostile `__repr__` or an unrenderable
int would replace the promised `ConfigurationError`.
- **Sites + roles.** *Definition*: `exceptions.py::describe_value` (owner
elsewhere; scope docstring names this file first). *Consumer (this file)*:
`views.py::_resolved_max_request_body_bytes` (`got {describe_value(value)}`).
Sibling consumers verified present (not re-audited): `consumers.py`,
`routers.py`, `resource_policy.py`, `schema.py`, `list_field.py`,
`error_policy.py`, `extensions/debug.py`, `utils/policies.py`,
`utils/sessions.py` (import sweep). *Oracle*: the too-large-to-render cap row
(title + body read) — plus this cycle's probe accident: formatting the
negative-`10**10000` probe label with a plain f-string raised `ValueError`,
which is the failure mode the helper exists to remove.
- **Challenges.** C23 → 1 (the helper); C2/C30 (gate arms) → L1/R6.
- **Owner + lifetime.** Unchanged: `exceptions.py`. No stored derivation
(pure renderer).
- **Migration.** None.
- **Distinct behavior.** The helper owns the tail grammar; this file owns
which values reach it (untrusted configured values only).
- **Behavioral proof.** `execution-verified` (probe: all 8 invalid-cap cases
raise `ConfigurationError`, including the unrenderable int; the tail names
`bool True`). Rejects "the message raises while rejecting".
- **Structural gate.** The unrenderable-int oracle. Negative control
(static): interpolating `{value!r}` directly passes every small-value oracle
and fails only the huge-int row.
- **Coupling.** None.
- **Freshness.** views.py `9f85b0df…` (above),
`django_strawberry_framework/exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`, `tests/test_views.py`
`fa97efdf…`.

### R1 — sync-adapter raw-body source (existing family `sync-adapter-raw-body-source`, stays `rejected`; re-derived, not inherited)

- **Contract difference (re-derived from this side).** Process scope
(`_cross_web_patches.py::_patched_body`: whole-process property replacement
for Strawberry's own view; gated; deletes on retirement) vs mount scope
(`views.py::_RawBodyRequestAdapter.body`: one-property subclass feeding this
view's own decode; permanent; must hold with the switch off). Opposite
lifecycles, opposite mounts. Byte-identical bodies (`return
self.request.body`) do not make one rule: posit upstream fixing the eager
decode → the patch deletes and the subclass stands (C24: 1 deletion, 0
shared moves). Posit pointing the subclass at the patched getter (C25) →
the permanent wire contract becomes reachable only through the temporary
switch — the exact defect the spec-046 split fixed.
- **Trigger check.** Reconsideration trigger was "upstream fixing the
defect": installed `cross_web` 0.7.0 still bare-decodes in the sync `body`
property while async `get_body` returns raw bytes (both verified in source;
installed hash `fa2a5bef…`). Trigger NOT fired — rejection stands.
- **Sites + roles.** Rejected pair as indexed. Contract oracle: upstream
async `get_body` (not a third definition). Oracles: the patches-off
constancy row (body read: reinstalls the eager getter and asserts the
package adapter still yields bytes) + the async-no-override pin (body read)
— both `static-reviewed` here, `execution-verified` at the owning item.
- **Owner + lifetime.** No owner (rejected). Durable homes (already prose):
`views.py::_RawBodyRequestAdapter` "Why this is not the ``cross_web`` patch
again" + `_cross_web_patches.py` "Who this patch is for" + this record.
- **Behavioral proof.** `execution-verified` (probe: seam identity,
subclass relation, async adapter untouched).
- **Freshness.** views.py `9f85b0df…`,
`django_strawberry_framework/_cross_web_patches.py`
`6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`, `tests/test_views.py`
`fa97efdf…`, installed `cross_web/request/_django.py`
`fa2a5bef5a6b0a63143247305718a94c33542aa0` (0.7.0).

### R2 — decode-failure-400 translation (existing family `decode-failure-400-translation`, stays `rejected`; re-derived)

- **Contract difference (re-derived from this side).** Translation of a
foreign raise (`_strawberry_patches.py::_translated_parse_json`: widens
upstream's `except json.JSONDecodeError` over `UnicodeDecodeError` /
`RecursionError`; gated; retires with upstream) vs performance of an own
decode (`views.py::_RequestBodyBoundaryMixin.parse_json`: strict
`data.decode("utf-8")` on `bytes`, `str` passed through untouched; permanent;
ungated). Opposite mechanisms (translating vs decoding), opposite lifecycles.
On a package view the strict decode runs first, so the delegate only ever
receives `str` and the translation is unreachable from that path (probe:
recorder sees exactly `str`; UTF-16/UTF-32/BOM bodies 400 THERE while
`json.loads` auto-detection still accepts them at the translator — the pair
demonstrably disagrees where the contracts differ, C26: translator 1, view
0). Posit routing the view's decode errors through the translator (C27) →
kill-switch coupling — refused.
- **Trigger check.** Trigger was "a neutral transport-error vocabulary both
sides already depend on": import sweep shows the patch module never imports
the view surface (deletability) and views.py never imports the patch module
— no such vocabulary exists. Trigger NOT fired — rejection stands.
- **Oracles.** Translation rows (`tests/test_strawberry_patches.py`) vs the
encoding matrix + opted-out-constancy rows (titles censused; str-handoff body
read). The `RecursionError` arm has no view twin (a strict decode cannot
recurse) — rides the translator by construction.
- **Owner + lifetime.** No owner (rejected). Durable homes: the two "why not
here / why the policy lives here" docstrings + this record.
- **Freshness.** views.py `9f85b0df…`,
`django_strawberry_framework/_strawberry_patches.py`
`f77df3499eb96051d70055266a677ca3cde5b219`, `tests/test_views.py`
`fa97efdf…`, installed `strawberry/http/base.py`
`05df08e8035850096769983abcb931d3d6c97ca5` (literal still narrow — see R3).

### R3 — request-body JSON parse reason (existing family `request-body-json-parse-reason`, stays `rejected`; re-derived)

- **Contract difference (re-derived).** Two deliberate spellings of one
upstream literal: `views.py::_JSON_PARSE_REASON` (strict-decode rejection)
and `_strawberry_patches.py::_UPSTREAM_JSON_PARSE_REASON` (widened-`except`
rejection). Identity on the wire is the contract (`__cause__` the only
discriminator); importing either from the other would couple the permanent
policy to the retirable workaround in one direction and break the patch
module's view-surface independence (deletability) in the other. Posit an
upstream message change (C28) → both literals move together, failing loudly
via the one oracle that pins both against the live raise (body read) —
deliberate, not drift.
- **Trigger check.** Trigger was an upstream message change or a neutral
home: executed upstream `BaseView().parse_json("{not valid json")` still
raises `HTTPException` with reason `"Unable to parse request body as JSON"`
(probe: equality on all three sides). Trigger NOT fired — rejection stands.
- **Freshness.** views.py `9f85b0df…`, `_strawberry_patches.py`
`f77df349…`, `tests/test_views.py` `fa97efdf…`, installed base.py
`05df08e8…` (above).

### R4 — upstream-patch install lifecycle (existing family `upstream-patch-install-lifecycle`, stays `rejected`; checked, not a member)

Import/call sweep over views.py: no `upstream_patches_enabled` import, no
gate call, no `APPLY_UPSTREAM_PATCHES` code reference — six prose mentions in
docstrings only (why the policy does NOT ride the switch). The temporary-vs-
permanent split is therefore intact from this side: every permanent rule here
holds with the switch off (constancy oracles), every temporary behavior lives
in the patch modules. Not a member; no index change.

### R5 — window validator vs body-cap validator (recorded rejection, stands; re-derived from this side)

`consumers.py::resolved_revalidation_window` vs
`views.py::_resolved_max_request_body_bytes`. Considered shared form: one
numeric-setting validator. Contract difference (re-derived): float window
`>= 0.0` with int-coercion, finiteness arms, and no `None` (a window is always
a number) vs int byte-count `> 0` with two-rung `None` coalescing
(constructor > setting) plus a project-wide disable spelling and a digit-limit
rendering arm; different prose, different overflow paths (`OverflowError` on
float conversion vs `ValueError` on message rendering — the latter
probe-verified here). One shape, two domains; unifying couples WS
revocation-delay policy to HTTP body-cap evolution (C30 refused). Trigger
re-check: no third bare-numeric validator appeared (population sweep:
`type(value) is not int` only here + `resource_policy.py` with a different
bound/outcome; `type(value) not in` only consumers/querysets predicates with
different admitted sets). Trigger NOT fired. Durable homes: both resolvers'
docstrings (each already names the other) + this record.

### R6 — exact-type admission idiom (refused shared form, recorded here)

Considered shared form: one `is_exact_int`-style helper over the
`type(value) is not int` / `type(value) not in (...)` sites (views.py:197,
`resource_policy.py:253`, `consumers.py:572`, `utils/querysets.py:758,2051`).
Contract difference: different admitted sets (`{int}` byte-count vs
`{int,float}` window vs `{int}` policy bound vs template/set predicates),
different refused outcomes (`ConfigurationError` with different prose), and
— the load-bearing one — the exactness rationale is per-site (bool exclusion
for the cap; `__float__`-override containment for the window; hostile
`__le__` containment here). The shared token is Python `type()` idiom, not a
package rule (conf-C31 / schema-J2 precedent, same verdict from this side).
Trigger: a mechanism change touching three or more predicates at once (e.g. a
new hostile-metadata shape the idiom must cover). Durable homes: the per-site
docstrings (each already records its own reason) + this record.

### R7 — multipart structure-vs-encoding split (new rejection, recorded here)

Considered shared form: one multipart-control owner for views.py's encoding
guards (`_form_encoding_is_utf8`, `_reject_lossy_multipart_control_fields`)
and `_strawberry_patches.py`'s sync/async `parse_multipart` delegates (map
container/path structure). Contract difference: which codec the bytes decode
under (a property of Django's decode, decided before parsing) vs whether the
parsed map traverses (a property of the JSON shape, decided after parsing);
different reasons to change in both directions (C31: a third control document
moves only the tuple here; a new map-shape failure moves only the delegates
there — 1 and 0 respectively). A shared owner would couple permanent wire
policy to retirable workaround lifecycle (R2's reason, one level up).
Trigger: upstream fixing the map traversal (delegates retire; guards stand —
a collapse to one survivor, never a merger). Durable homes:
`views.py::_reject_lossy_multipart_control_fields` "Why the check lives here
rather than in a private parser" + the patch module's provenance-scoping
paragraph + this record.

### R8 — GET query-param semantics absence (new rejection, recorded here)

Considered shared form: one GET-semantics owner for the patch shield
(`_patched_parse_query_params`: routes GET parses through the captured
original), the view's `str` passthrough in `parse_json`, and the GET
early-returns in the cap/charset guards. Contract difference: each is the
ABSENCE of its own guard, owned by a different lifecycle — the shield keeps
the envelope guard off GET (retires with gap 2), the passthrough keeps
decoding off already-decoded text (permanent: Django decoded the URL, not a
body), the early-returns keep measurement off an unread body (permanent:
nothing is parsed). There is no shared body to own, only three independent
decisions not to act. C31: a new upstream query param moves the shield's
source pin (1) and nothing here (0). Trigger: upstream reshaping
`parse_query_params` (shield already pins the body and fails loud) or a
package decision to parse GET bodies (none exists). Durable homes: the
shield's docstring + `views.py::parse_json` GET paragraph + this record.

### L1 — view cap ladder, declared fast path, and limit order (file-local)

`views.py::_resolved_max_request_body_bytes` (+ `max_request_body_bytes`
attr, `_BODY_LIMIT_REASON`, `_declared_content_length`,
`_enforce_request_body_limit`, `_enforce_request_boundary` call order).
Single ladder (kwarg > setting > 1 MiB default), single validator, single
reason literal (probe: spelled once package-wide), single enforcement order
(declared gate → multipart carve-out → counted check). Challenges C1-C4 move
1/1/1/1 (C3 refused by the spoofing contract). The setting rung is conf-owned
(thin reader, never validates — read at its body); the measurement is
`_request_body.py`-owned (one boolean call — read at its contract). Neither
is a second definition of this ladder. Gate: the precedence-ladder oracles +
the invalid-cap rows (titles censused; ladder + unrenderable-int bodies
read). Negative control (static): admitting `bool` passes every oracle whose
fixture uses small ints and fails only the exact-type row. Freshness: views.py
`9f85b0df…`, `conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`,
`tests/test_views.py` `fa97efdf…`.

### L2 — multipart identity discriminator (file-local)

`views.py::_is_multipart_form_post` + `_MULTIPART_CONTENT_TYPE`. One
discriminator shared by the cap carve-out and both encoding guards so they
cannot drift on what "multipart" means (C5 → 1; C11 → 0). Both halves
verified load-bearing against installed Django (`_load_post_and_files` parses
only on POST; verified) and upstream (`is_request_allowed` is GET/POST-only
with 405 otherwise; verified) — a stray multipart type on GET is parsed by
nobody, so refusing it would invent a rejection. Gate: the GET-hostile-length
+ multipart-never-materialized oracles (titles). Freshness: views.py
`9f85b0df…`, installed `django/http/request.py`
`414aa38de3ca5ebabda300325efaa7b274a53771`, installed
`strawberry/http/base.py` `05df08e8…`.

### L3 — codec canonicalization (file-local)

`views.py::_canonicalizes_to_utf8` + `_UTF8_CODEC_NAME`. One predicate over
`codecs.lookup`, no alias list (C6 → 1, C7 → 0 — probe matrix green on 9
cases). Gate: the alias-matrix oracles (titles) + probe matrix
(`execution-verified`). Negative control (static): a name-comparison
implementation passes every common-alias oracle and fails only an unlisted
alias row. Freshness: views.py `9f85b0df…`.

### L4 — multipart form-encoding gate (file-local)

`views.py::_form_encoding_is_utf8` + `_enforce_multipart_form_encoding`.
Two independent conditions joined with `and`, deliberately not a fallback
chain (C8 → 0 derivations owed — reads Django's live expression; C9 → 0 by
Django's FILE-branch-only contract — both Django behaviors verified in
installed source: single promotion in `_set_content_type_params`,
`encoding or settings.DEFAULT_CHARSET` in `MultiPartParser.__init__`,
`errors="replace"` in the FIELD branch, per-part charset in the FILE branch
only). Gate: the per-condition oracles incl. the declaration-masks-encoding
row (titles) + the live malformed-byte/Latin-1/multibyte rows. Freshness:
views.py `9f85b0df…`, installed `django/http/request.py` `414aa38d…`,
installed `django/http/multipartparser.py`
`f901084a1029f98af4f56d54596954c8ac1e9b13`.

### L5 — charset-declaration gate (file-local)

`views.py::_declared_charset_is_unhonourable` +
`_enforce_body_charset_declaration`. One shared declaration predicate (also
L4's first condition, so the two guards cannot disagree — C10 → 1, C11 →
0). Refusal (not honoring) is the contract: honoring reopens the multi-
encoding success set. Gate: the non-multipart declaration rows (titles).
Freshness: views.py `9f85b0df…`.

### L6 — lossy control-field rejection (file-local)

`views.py::_reject_lossy_multipart_control_fields` +
`_MULTIPART_CONTROL_FIELDS` + `_REPLACEMENT_CHARACTER`. One marker check over
exactly the two JSON control fields, before `json.loads` (a replaced byte
often repairs the document into parseable shape — read at the body). C12/C13
→ 0 (escape preserved; `bytes` delegated). The deliberate narrowness (literal
U+FFFD-as-data must be escaped) is stated at the body with its rationale.
Gate: the live malformed-control + escaped-marker + genuine-multibyte rows
(titles) + the marker-scoping row. Negative control (static): checking after
`json.loads` passes every well-formed oracle and fails only the
repairs-into-valid rows. Freshness: views.py `9f85b0df…`,
`test_transport_api.py`
`17320f1ff335a868d5ed324a49f1d7c4ee899cfc`.

### L7 — CSRF continuation twin (file-local, intentional separation)

`views.py::_run_after_csrf_check`, `::_async_run_after_csrf_check`,
`::_csrf_protected_run`, `::_csrf_protected_async_run`. One rule (re-enter
the configured CSRF check from inside the view, after the boundary) in two
mechanism-forced colors: `csrf_protect` branches on `iscoroutinefunction`
(verified), so the wrapped callable must itself be a coroutine on the async
transport (C14: 2 bodies / 1 rule — principle-5 two-machines record; C15
breaks, refused by mechanism). Module-level single decoration (one
`CsrfViewMiddleware` instance per transport, stateless delegates) is read at
the body. Gate: the per-transport continuation-match rows + async CSRF rows
(titles). Freshness: views.py `9f85b0df…`, installed
`django/utils/decorators.py`
`7e4d724b462e08cae9186e324615d3d0f2ff0caa`.

### L8 — view `run` twin (file-local, intentional separation)

`views.py::DjangoGraphQLView.run` +
`views.py::AsyncDjangoGraphQLView.run` (+ `_enforce_request_boundary_once`
shared). One order (boundary-once → CSRF continuation → upstream `run`) in
two colors differing only by `await` (C16: 2 bodies / 1 rule; C17: skipping
`_once` on either transport is an omission defect — both call it, and the
middleware stamp is the only licensed skip, read inside `_once`). The
413-before-CSRF property falls out of the order (raise precedes the
continuation — read at both bodies). Gate: the boundary-before-CSRF rows on
both transports (titles) + the duplicate-entry idempotence row. Freshness:
views.py `9f85b0df…`, installed `strawberry/django/views.py`
`3a3d1d1056180dd50ead70f0b7cb1d3fe736d39e`
(`dispatch` catches `HTTPException` on both), installed sync/async
`run` hashes `48ca38b7…` / `1027f60d…`.

### L9 — multipart-parse twin (file-local, intentional separation)

Both `parse_multipart` overrides. Policy lives once on the mixin (C18 → 1);
the overrides are pass-throughs differing only where upstream's own split
forces them to (C19 refused by mechanism — signatures verified). The sync
override reads `request.post_data`, the async one awaits `get_form_data`;
both hand the same adapter upstream so upstream stays the only multipart
reader (read at both bodies). Gate: the lossy-control rows on both
transports incl. the async-refuses-same-documents live row (titles).
Freshness: views.py `9f85b0df…`.

### L10 — leaf manifest + channels-free discipline (file-local)

`views.py::__all__` (exactly the two view classes; deliberately not
package-root exports — probe-adjacent: root `__init__.py` never imports this
module, verified by read), the `TYPE_CHECKING`-only cross_web/Django typing
imports (zero runtime cost), and the channels-free import set (runtime
imports: stdlib + asgiref + cross_web + django + strawberry + 3 first-party
leaf modules — verified by AST + execution; `strawberry.django.views` itself
imports no channels — verified; first-party `conf`/`exceptions` reach only
`django.conf`/`django.test.signals`/stdlib — verified). The
channels-absence oracle (`test_views_module_imports_with_channels_absent`,
title) owns this property. No second site defines the manifest. Freshness:
views.py `9f85b0df…`, `tests/test_views.py` `fa97efdf…`.

## Defects

None. Every docstring/comment claim checked while tracing held against
installed source or execution: the single `request_adapter.body` read site in
upstream `parse_http_body` (verified — the claim the adapter seam rests on);
the 405/allowed-methods shape (verified); both `dispatch` translations
(verified); the Django promotion/encoding/replace/FILE-branch-only chain
(verified line by line); the `csrf_protect` coroutine branch (verified); the
`hasattr` keyword-guard shape behind the mixin-first rationale (verified —
mixin-last would bind identically, so precedence over upstream is indeed the
operative reason, as stated); the no-plain-`True` stamp (probe); the
prepare/consume-once handoff (read). The negative-declaration shape was
checked (axis 6) and stays parity, not a defect. Nothing routes to any owner.

## Pending execution

None. The single execution proof (read-only probe, command in
`### Challenges` head) already ran green (58/58) against the shared tree; it
mutates nothing, opens no database, touches no settings, and runs no pytest.
No `execution-deferred` items. No shared-tree pytest was run (item rules).

## Judgment

Backstop discharged: 36/36 `ast.Module.body` members enumerated, 31
challenges run, every rule terminating in a reused indexed family (F1-F4,
all `open`, consumer/referent records from this side), a re-derived
rejection (R1-R3 with triggers checked unfired; R4 checked non-member; R5-R6
re-derived against the same trigger; R7-R8 newly recorded with triggers and
durable homes), or a file-local row with its proving challenge (L1-L10). No
existing family is renamed; no new family is named (the only cross-file rules
here already have holding families; the twin pairs are mechanism-forced
intra-file separations, recorded not consolidated). Zero-edit result is
legitimate.

Proposed `## Responsibility index` rows for Worker 0 to add (all
`file-local`, holding item `File views.py`):

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `view-cap-precedence-and-validation` | `django_strawberry_framework/views.py::_resolved_max_request_body_bytes` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `declared-length-fast-path` | `django_strawberry_framework/views.py::_declared_content_length` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `multipart-identity-discriminator` | `django_strawberry_framework/views.py::_is_multipart_form_post` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `codec-canonicalization` | `django_strawberry_framework/views.py::_canonicalizes_to_utf8` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `multipart-form-encoding-gate` | `django_strawberry_framework/views.py::_form_encoding_is_utf8` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `body-charset-declaration-gate` | `django_strawberry_framework/views.py::_declared_charset_is_unhonourable` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `lossy-control-field-rejection` | `django_strawberry_framework/views.py::_reject_lossy_multipart_control_fields` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `csrf-continuation-twin` | `django_strawberry_framework/views.py::_run_after_csrf_check` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `view-run-twin` | `django_strawberry_framework/views.py::DjangoGraphQLView.run` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `view-leaf-manifest` | `django_strawberry_framework/views.py::__all__` | `django_strawberry_framework/views.py` | File `views.py` | file-local |

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
b18d489ed4af0936260f8f7290af592b369c599b --
django_strawberry_framework/views.py` is empty (0 lines); the working blob
`9f85b0df26a17e800ec392aa13f6848e07633895` equals both the item baseline and
`HEAD:` — the target is clean against both, so no hunk attribution was owed.
Untracked scratch created (not tracked changes):
`docs/dry/temp-tests/dry-file-views/probe_views.py` (this item's read-only
probe, 58/58 green; `uv run ruff format` + `uv run ruff check --fix` applied
to that path only — remaining annotation/import-position nits live in
untracked scratch, not shipped) and this artifact
`docs/dry/dry-file-views.md`. Concurrent dirt listed in the plan item
(`django_strawberry_framework/connection.py`,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never read
for verdicts, never edited, reverted, or tidied. No commit.

## Independent verification (Worker 2)

Own trace re-derived from the target, package-wide greps, and a fresh
re-run of the read-only probe BEFORE reading `## Findings` above.
Every difference vs W1 is reconciled per row below.

### Own rule derivation (counts + owners I would choose)

- **Boundary marks (4 names).** views.py imports all four by name
(`_BOUNDARY_ENFORCED`, `_BOUNDARY_MARKER`, `_BOUNDARY_MOUNT`,
`_BOUNDARY_PREPARED_VIEW`) plus `_CSRF_ORDERING_EXEMPTION`; stamps/reads
only through those bindings; no plain `csrf_exempt = True` anywhere.
Owner: `_boundary_ordering.py`. Agree F1 (consumer).
- **Method name (1 name + 1 behavior def).** The `def
_enforce_request_boundary` lives here; no string spelling of the name in
this file; middleware probes/invokes via `_BOUNDARY_METHOD` (read at its
body). Owner: NAME elsewhere, BEHAVIOR here. Agree F2 (referent).
- **Exemption (1 singleton).** `view.csrf_exempt =
_CSRF_ORDERING_EXEMPTION` by identity; continuations shared by both
arrangements. Owner: `_boundary_ordering.py`. Agree F3 (consumer).
- **Raw-body adapter (1 property).** `_RawBodyRequestAdapter.body`
returns `self.request.body` undecoded; mount-scoped subclass, permanent;
async needs no twin (upstream `get_body` already raw). Opposite
lifecycle to `_cross_web_patches.py::_patched_body` (process scope,
gated, retirable). Owner: none (rejected pair). Agree R1.
- **Decode (1 method) + translation (elsewhere).** `parse_json`
strict-decodes `bytes`, passes `str` through, delegates upstream;
translator widens upstream's `except` for other transports. Opposite
mechanisms, opposite lifecycles. Agree R2.
- **Parse reason (2 literals, 1 oracle).** Both spell upstream's
literal; importing either way couples permanent policy to retirable
workaround or breaks patch deletability. Agree R3.
- **Patch lifecycle (0 members).** No gate import/call/code reference
in views.py (prose mentions only). Agree R4 (not a member).
- **Tail (1 call site).** Single `describe_value(value)` at the raise
site; owner `exceptions.py::describe_value`. Agree F4 (consumer).
- **Cap ladder (1 resolver + 1 attr + 1 reason + 1 order).** kwarg >
setting > default; `conf.py::max_request_body_bytes_setting` verified a
thin reader (no validation, live default `1_048_576`); measurement is
one boolean call to `_request_body.py::body_exceeds_limit`; no
`1048576` literal here. Owner here. Agree L1.
- **Multipart/charset/form/codec gates (4 predicates + 1 shared).**
`_is_multipart_form_post` (POST + type, both halves verified
load-bearing), `_canonicalizes_to_utf8` (`codecs.lookup`, no alias
list), `_form_encoding_is_utf8` (2 independent conditions over
Django's live expression), `_declared_charset_is_unhonourable`
(shared by both guards). Owners here. Agree L2-L5.
- **Lossy control rejection (1 check over 2 fields).** Marker check
before `json.loads`; escape preserved; `bytes` left for the decode.
Owner here. Agree L6.
- **Continuation/run/multipart twins (2 + 2 + 2 bodies, 3 rules).**
Each pair differs only where the mechanism forces it
(`iscoroutinefunction` branch; `await`; upstream's own sync/async
`parse_multipart` split). Principle-5 two-machines, intra-file;
nothing to consolidate. Agree L7-L9 (file-local separations).
- **Manifest (1 `__all__`, 2 names).** Exactly the two views; root
`__init__.py` never imports this module (verified by grep);
channels-free import set as stated. Owner here. Agree L10.

### Reconciliation vs W1, per row

F1/F2/F3/F4: agree on all four (consumer/referent records, owners
unchanged, `open`). R1/R2/R3: agree (re-derived differences +
unfired triggers hold; installed `cross_web` 0.7.0 still bare-decodes
sync, async raw — re-verified hashes below). R4: agree (non-member).
R5 (window-vs-cap): agree — different admitted sets, different
`None`/coercion/overflow semantics, different outcomes; Python-level
resemblance only. R6 (exact-type idiom): agree — per-site rationales
(bool exclusion vs hostile `__le__` containment), different refused
outcomes; idiom, not a package rule. R7/R8: agree as REJECTIONS, and
agree NO new family is named — see family-vs-rejection ruling below.
L1-L10: agree on all ten (single owners here, challenges move 1/0 as
stated; twin pairs mechanism-forced). One clerical gap, verdict-neutral:
the proposed index-row list omits L9 (see Worker-0 instructions).

### R7/R8 family-vs-rejection ruling (endorse W1)

R7 (structure-vs-encoding): a shared owner would couple permanent wire
policy (which codec Django decodes under) to a retirable workaround
lifecycle (map-shape traversal), repeating the exact defect R2 split.
Different reasons to change in both directions (C31: 1 and 0). No
driver could own both lifecycles (principle 7). Rejection correct; no
family owed. R8 (GET-absence triple): there is no shared body to own —
three independent decisions NOT to act, each owned by its own lifecycle
(retirable shield vs two permanent passthroughs/early-returns). A
family with no shared definition is not a family (principle 1).
Rejection correct; no family owed. L7/L8/L9 twins likewise correctly
stay file-local: mechanism-forced colors with no second owner possible.

### Enumeration check (member by member vs own count)

Own `ast.parse` count: **36** top-level statements (matches W1).
Cross-foot: 1 module docstring + 12 `ImportFrom` + 1 `Import` + 1
`If` + 9 `Assign` + 7 `FunctionDef` + 1 `AsyncFunctionDef` + 4
`ClassDef` = 36. Bound top-level defs/classes: **12** (matches W1's
"12 bound defs/classes"). Methods with owners: adapter 1, mixin 8,
sync view 2, async view 2. W1's table rows 1-36 home every member
(machinery / consumer imports / L1-L10 / F1-F4 / R1-R3); no member
unassigned. Agree.

### Matrix vs real surface

Axes 1-6 re-derived against the real surface: no second `parse_json`
def or cap vocabulary package-wide; three colored pairs + one shared
core + one pinned asymmetry compared by behavior; no reconstructed
knowledge (live setting read, canonicalization, live Django
expression, per-call mount token); round trips single-owned or
indexed; oracles compose by name (package tier imports reason
constants/adapter/boundary names; live tier pins behavior); omission
sweep over {sync, async} x {cap, decode, 2 header guards, lossy
guard, CSRF} all enforced, non-coverages each contract-sourced.
Discharged. Agree.

### Counts + roles; oracles

C1-C31 definition counts re-derived: agree (multi-body rows C14/C16
are 2-bodies/1-rule two-machines; C21 is 1 name + 1 referent).
Consumers/oracles/projections listed, never counted — confirmed. No
oracle rewritten: zero production edits, test files untouched, and the
oracles import owner symbols by name rather than respelling values
(verified at `tests/test_views.py` import block). Oracle census
re-measured: 82 top-level `test_` fns in `tests/test_views.py`
(matches W1's 82/82), 61 in `test_transport_api.py` (matches W1's 61).
Agree.

### Equivalence (principle 8)

Zero-edit item: no behavior to preserve across a change. Observable
claims are census/identity/absence facts, all `execution-verified` by
the re-run probe (58/58 green, `uv run python
docs/dry/temp-tests/dry-file-views/probe_views.py`, shared tree,
read-only, no settings, no DB). Oracle bodies stay `static-reviewed`;
the final gate executes them. Agree.

### Zero-edit + coverage/assignment

Item-scoped diff confirmed empty by Worker 2 (`git diff
b18d489ed4af0936260f8f7290af592b369c599b --
django_strawberry_framework/views.py` = 0 bytes; views.py absent from
`git status --short`). Working blob `9f85b0df…` equals item baseline
and `HEAD:` (canonical `9031cb3d`). All 36 members homed; no
consolidation owed by a file item; F1-F4 route to existing `open`
families; R1-R8 carry differences + triggers + homes. Validated.

### Freshness re-hashes (Worker 2, all match)

views.py `9f85b0df…` match; `_boundary_ordering.py` `197eea8e…`
match; `middleware/request_body.py` `e6e32e78…` match;
`tests/test_views.py` `fa97efdf…` match; `_cross_web_patches.py`
`6b3a7c35…` match; `_strawberry_patches.py` `f77df349…` match;
`exceptions.py` `e06b0b7f…` match; `conf.py` `c6ad46aa…` match;
`test_transport_api.py` `17320f1f…` match. Installed:
`django/middleware/csrf.py` `3c709f2f…`, `strawberry/http/base.py`
`05df08e8…`, `cross_web/request/_django.py` `fa2a5bef…`,
`django/http/request.py` `414aa38d…`,
`django/http/multipartparser.py` `f901084a…`,
`django/utils/decorators.py` `7e4d724b…`,
`strawberry/django/views.py` `3a3d1d10…` — all match. No fingerprint
stale.

### Structural gates (negative controls judged plausible)

L1 exact-type row, L3 alias-matrix row, L4 per-condition rows, L6
repairs-into-valid rows, L7/L8 per-transport rows, L9 both-transport
lossy rows, F4 unrenderable-int row: each fails exactly its guarding
row under the stated hand-copy (static judgment). Execution of these
controls belongs to the holding family items; file item owes none.
`## Pending execution` correctly absent (probe already ran green;
no `execution-deferred` proof; no sharded/Postgres cell owed —
target performs no query/connection/alias decision, `inapplicable by
construction`). Coupling `None` throughout: correct.

### AGENTS.md prose check

Item diff empty, so no production/test prose to check. Artifact: no
process provenance, no `feedback` mention, `path::Symbol` citations
throughout (51 `::` sites). The R6 `views.py:197`-style bare line
cites sit inside a `docs/dry/dry-*.md` artifact, which AGENTS.md
explicitly permits for raw `path:NN` — pass, no change owed. Test
tier stated at the mandated tier with the fakeshop-gap sentence
(package tier strongest where fakeshop has no fixture). No commit;
concurrent dirt untouched (verified via `git status --short` before
and after; this edit touches only the item's own artifact). Docs-only
edit: no `ruff` run — `ruff format`/`check --fix` operate on Python
and a repo-wide `--fix` would risk the concurrent dirt above; nothing
here can violate them.

### Routers-citation ruling (owed)

W1's claim is TRUE: `docs/dry/dry-file-routers.md:69` cites
`views.py::resolved_max_request_body_bytes` (missing leading
underscore); the real symbol, defined at views.py:159 and called at
views.py:637, is `views.py::_resolved_max_request_body_bytes`.
RULING: Worker 0 MAY correct that single token in place in the
already-verified routers artifact. The routers item stays verified —
no reopen. Reasons: the citation sits in the System-trace read-list,
not in any finding's Sites/owner/gate field; no definition count,
owner, challenge, gate, or freshness fingerprint depends on the
spelling; the referent is unambiguous in context (the int-gate
contrast; exactly one such gate exists in views.py). Precedent: the
routers artifact's own W2 prose correction (38 → 117) was likewise
ruled amend-in-place. Condition: correct only that token; keep the
fix out of `## Outcomes` reasoning beyond one line.

### Defects (Worker 2)

None. Every docstring/comment claim spot-checked while tracing held
(single `request_adapter.body` read site, 405 shape, both `dispatch`
translations, Django promotion/encoding/replace/FILE-branch chain,
`csrf_protect` coroutine branch, `hasattr` guard rationale,
no-plain-`True` stamp, consume-once handoff). One verdict-neutral
observation for Worker 0 (not a defect): the proposed index-row list
covers L1 (split in two), L2-L8, L10 but omits L9
(multipart-parse twin) — L9 itself is fully homed in Enumeration
(rows 35/36) and Findings with owner, challenges C18/C19, gate, and
freshness, so coverage/assignment validate; Worker 0 simply adds the
missing row from the exact line below.

### Judgment (Worker 2)

Verified. Single-owner transport-boundary module; shared rules
consumed by name (F1-F4, all `open`); rejections re-derived with
unfired triggers (R1-R3, R5-R8; R4 non-member); ten file-local rules
with proving challenges (L1-L10, twins as intentional separations);
zero edits, zero pending execution, zero defects. Worker 0 owes two
in-place amendments (L9 index row; routers-citation token), neither of
which reopens any item.

Worker-0 instructions. (a) Add these `## Responsibility index` rows
(W1's ten as proposed, plus the missing L9 row — eleven lines
total), all file-local, holding item `File views.py`:

| `view-cap-precedence-and-validation` | `django_strawberry_framework/views.py::_resolved_max_request_body_bytes` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `declared-length-fast-path` | `django_strawberry_framework/views.py::_declared_content_length` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `multipart-identity-discriminator` | `django_strawberry_framework/views.py::_is_multipart_form_post` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `codec-canonicalization` | `django_strawberry_framework/views.py::_canonicalizes_to_utf8` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `multipart-form-encoding-gate` | `django_strawberry_framework/views.py::_form_encoding_is_utf8` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `body-charset-declaration-gate` | `django_strawberry_framework/views.py::_declared_charset_is_unhonourable` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `lossy-control-field-rejection` | `django_strawberry_framework/views.py::_reject_lossy_multipart_control_fields` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `csrf-continuation-twin` | `django_strawberry_framework/views.py::_run_after_csrf_check` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `view-run-twin` | `django_strawberry_framework/views.py::DjangoGraphQLView.run` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `multipart-parse-twin` | `django_strawberry_framework/views.py::DjangoGraphQLView.parse_multipart` | `django_strawberry_framework/views.py` | File `views.py` | file-local |
| `view-leaf-manifest` | `django_strawberry_framework/views.py::__all__` | `django_strawberry_framework/views.py` | File `views.py` | file-local |

(b) In `docs/dry/dry-file-routers.md:69`, correct
`views.py::resolved_max_request_body_bytes` to
`views.py::_resolved_max_request_body_bytes` in place; routers stays
verified.

One observation for Worker 0, not a defect: `docs/dry/dry-file-routers.md`
line 69 cites `views.py::resolved_max_request_body_bytes` (missing the
leading underscore; the symbol is
`views.py::_resolved_max_request_body_bytes`). Scratchpad citation in another
item's read-list; left alone per item fencing.
