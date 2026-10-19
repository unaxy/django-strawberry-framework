# DRY review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, rejection
re-checked fresh against its trigger), two NEW families (named for Worker 0
to add, both proposed `rejected`), or a file-local record. Zero production
edits; zero tracked files changed.

## System trace

Large target (850 lines, 32 top-level statements): the `strawberry`
dependency's defensive patch module — one of four one-module-per-dependency
patch modules (`_django_patches.py`, `_cross_web_patches.py`,
`_graphql_core_patches.py`, this one), each applied once from
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
behind its own `APPLY_UPSTREAM_PATCHES` gate. The target DEFINES three
behavior rules (the decode-error translation, the body-envelope guard with
its GET shield, the multipart structural delegates with provenance scoping)
plus its own install lifecycle (import-time capture, shape + body validation,
idempotent self-healing 4-member atomic install); it ENFORCES the three
rules process-wide on Strawberry's views once installed, and nothing else.

What the target owns: `BaseView.parse_json` widened to translate the two
client-input raises upstream's `except json.JSONDecodeError` misses
(`UnicodeDecodeError`, `RecursionError`) into Strawberry's existing
`HTTPException(400, ...)`; rejection of non-envelope bodies (scalars,
non-object batch elements) with the same `400`; a source-pinned
reimplementation of `parse_query_params` keeping that guard off the GET
path; sync/async multipart delegates translating upload-utility traversal
failures (provenance-scoped) into Strawberry's native multipart `400`.

Connected code read for judgment, outside the item: `_cross_web_patches.py`
(full read, 347 lines), `_django_patches.py` (full read, 423 lines),
`_graphql_core_patches.py` (full read, 127 lines) — behavior/contract
comparison before calling anything here unique;
`django_strawberry_framework/conf.py::upstream_patches_enabled` (full body
read) + `UPSTREAM_PATCH_DEPENDENCIES`; `django_strawberry_framework/apps.py`
(full read: four-applier dispatch);
`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json`
+ `::_RawBodyRequestAdapter` (full bodies read: the strict-decode twin and
permanent body source);
`django_strawberry_framework/views.py::_JSON_PARSE_REASON` (the reason-literal
twin); `tests/test_strawberry_patches.py` (full read, 35 top-level test
functions); `tests/test_views.py` wire-constancy + reason-literal rows
(bodies read); `test_transport_api.py::test_the_upstream_bug_workaround_still_respects_its_own_opt_out`
+ multipart-map rows (existence + names verified);
`test_products_api.py::test_post_non_object_json_body_returns_400_not_500` +
batch-element row (existence verified); installed upstream
`strawberry.http.base` / `sync_base_view` / `async_base_view` /
`file_uploads.utils` (sources read + executed; strawberry-graphql 0.324.0);
`django_strawberry_framework/__init__.py` (verified patch-free).

Excluded with reason: `consumers.py` (WebSocket never enters `parse_json` —
its own docstring states the translation does not reach it);
`middleware/`, `_boundary_ordering.py`, `_request_body.py` (boundary
protocol; no patch vocabulary — the `upstream_patches_enabled("strawberry")`
gate call and the `{"strawberry": False}` hint each occur in exactly one
production file, this one, probe-verified over all 117 package files);
`testing/_wrap.py` (consumes only `_django_patches::_is_database_failure`);
filter/order/mutation/form/rest_framework flavors (no patch vocabulary —
same sweeps); PyPI-latest re-check of strawberry (installed-tree shape
verified instead, and it is stronger: the docstring's "unfixed as of
0.317.2" claims all re-verified against installed 0.324.0). Concurrent dirt
(`connection.py`, `tests/test_connection.py`,
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) left untouched; none is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** All three sibling patch modules read
in full and compared by behavior/contract, not shape. Same skeleton
(gate, validate, installed-check, install; owner-attr marks; import-time
capture; try/except-None import fallback — the owner-attr literal occurs in
exactly the four patch modules, probe-verified over all 117 package files),
different contracts: this module WRAPS three methods by delegation but
REIMPLEMENTS `parse_query_params` (pins that one body; installs four members
atomically — the scalar guard must never run without its GET shield);
`_django_patches` REIMPLEMENTS a teardown loop (pins a SET of two audited
bodies + stores the validated source for teardown-time reads);
`_graphql_core_patches` WRAPS one executor method by pure delegation;
`_cross_web_patches` REPLACES one property with the async contract and never
calls the captured getter. Fresh difference supporting the existing
rejection: install arities 4-atomic vs 1/1/1, and three independent
retirement lifecycles inside THIS module alone (decode translation,
envelope-guard+shield, multipart delegates — the module docstring's "Three
lifecycles" section). No type/filter/order/mutation/form/rest surface
carries patch vocabulary. Search performed; shared skeleton stays rejected
under the existing family (F1 — trigger re-checked, see Findings).

**2. Sync/async twins.** Two twin pairs, opposite correct answers (principle
5, recorded here and at each owner). (a) The multipart delegates
(`django_strawberry_framework/_strawberry_patches.py::_patched_sync_parse_multipart`
vs `::_patched_async_parse_multipart`) are two colored bodies because each
must await (or not) its own transport's parser — but they share every pure
decision first: the `_MULTIPART_TRAVERSAL_ERRORS` tuple and the
`_raised_inside_the_upload_utility` provenance predicate are single-owned
and both delegates compose them by name. Compared by behavior: both executed
over the same malformed `[{}]` map → identical `400`; both pass a
traversal-typed server bug through. (b) The sync/async POST-body sites share
ONE `BaseView` method, so one install covers both transports by
construction (unlike the multipart pair). No async twin lives anywhere else
for this module's rules. Axis discharged against the real surface as stated.

**3. Derived rather than repeated knowledge.** The four `(self, argument)`
signatures are derived once via `inspect` at validate time, never restated.
The `{"strawberry": False}` opt-out hint occurs in production only here
(probe-verified); the gate name `"strawberry"` is consumed by passing the
string to single-owned
`django_strawberry_framework/conf.py::upstream_patches_enabled`, while the
canonical set itself is single-owned at
`django_strawberry_framework/conf.py::UPSTREAM_PATCH_DEPENDENCIES` —
compose-by-name, no second definition. The `_PATCH_OWNER` literal equals the
module `__name__` but is spelled once with no second site. Two verbatim
copies exist by contract and are handled as such: the pinned
`_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE` (a reimplementation MUST spell the
body it supersedes; pinned + fail-loud, not a hidden dup — R4) and the JSON
parse reason literal (second production spelling in
`django_strawberry_framework/views.py::_JSON_PARSE_REASON` — new rejected
family F3). No reconstructed copies found.

**4. Inverse / round-trip pairs.** Capture-at-import / validate-at-apply is
one in-module pipeline (capture recovers the genuine method across reloads
via the owner mark; validate pins the capture, never the live descriptor).
No uninstall API exists (tests revert by `__dict__` identity restore;
oracles, not a second definition). The docstring's three retirement probes
(live scalar/batch rows, live multipart-map rows, captured-callable probes)
are the install's check pairs, not second implementations. The shield's
pinned source vs the live upstream body is a standing equality pair:
probe-verified byte-equal against installed 0.324.0 today. Each pair's
halves are consumers of one definition.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target + `apps.py` dispatch + `conf.py` gate
vocabulary + `views.py` strict-decode twin); oracles that compose by name —
`tests/test_strawberry_patches.py` (35 top-level functions: lifecycle +
idempotence/self-heal, gap-1 translation incl. `__cause__`, gap-2
scalar/batch semantics incl. the upstream-semantics-preservation rows, GET
falsy-skip, multipart structural vs server-bug rows, drift refusals incl.
body-drift + sourceless, global + per-dependency toggles, the behavioral
opt-out row), `test_products_api.py` non-object rows (wire delta for gap 2),
`test_transport_api.py` opt-out + multipart-map rows (mount-level proof),
`tests/test_views.py` wire-constancy rows (package mount indifferent in
every patch state) + the reason-literal pin (both copies against upstream's
actual raise); prose projections (the ~370-line module docstring — three
gaps, three lifecycles, upstream status with permalinks, re-check recipes —
plus mirror paragraphs in `views.py`, `conf.py`, `_cross_web_patches.py`,
GLOSSARY dispatch/kill-switch entries, CHANGELOG entries). Every oracle
restatement imports the module by name and pins behavior; none respells the
rule. The upstream "still unfixed" claims re-verified against the installed
0.324.0 tree (narrow `except` present; query-params source byte-equal;
upload utility still unguarded `.items()`).

**6. Enforcement by omission.** Three enumerations, none gapped. (a) Patch
members: all four (`parse_json`, `parse_query_params`, sync + async
multipart) install atomically — `_patch_is_installed` reports `False` on
any partial revert (pinned by oracles), so the guard never runs without its
shield and the two transports never diverge. (b) `parse_json` call-site
inventory on the installed tree: 9 call sites, matching the docstring's
"nine in total" (0.316.0 pin) on 0.324.0 — 7 body/multipart sites guarded,
2 GET sites shielded, of which the multipart-subscriptions body site is dead
code (`parse_multipart_subscriptions` defined at `async_base_view.py:565`
with zero callers, probe-verified). The dead site inherits the guard
harmlessly through the shared helper. (c) Package-view path: the strict
decode runs first, so the delegate here only ever receives `str` from that
path and the translation is unreachable there — the omission is the
lifecycle split, pinned by the opted-out constancy rows. No member lacks a
guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **32 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row or a file-local record.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (3 gaps, 3 lifecycles, probes, upstream status) | (none) | projection, F1/F2/F3 |
| 1 | `import inspect` | `inspect` | machinery for F1 validation |
| 2 | `import textwrap` | `textwrap` | machinery (source pin) |
| 3 | `from typing import Any` | `Any` | machinery (annotations) |
| 4 | `from .conf import upstream_patches_enabled` | gate consumer | machinery, F1 (composes `conf.py` by name) |
| 5 | `try/except ImportError` fallback binding `None` | `BaseView`, `HTTPException`, both views, utility | R7, file-local |
| 6 | `_PATCH_OWNER_ATTRIBUTE = "…_patch_owner"` | mark name | R1, F1 |
| 7 | `_PATCH_ORIGINAL_ATTRIBUTE = "…_original"` | mark name | R1, F1 |
| 8 | `_PATCH_OWNER = "…_strawberry_patches"` | owner identity | R1, F1 |
| 9 | `def _captured_upstream_method` | reload-proof capture | R1, F1 |
| 10 | `_original_parse_json = …(BaseView, "parse_json")` | stored derivation | R1, F1 (principle-4 fields in F1) |
| 11 | `_original_parse_query_params = …` | stored derivation | R1, F1 |
| 12 | `_original_sync_parse_multipart = …` | stored derivation | R1, F1 |
| 13 | `_original_async_parse_multipart = …` | stored derivation | R1, F1 |
| 14 | `_UPSTREAM_JSON_PARSE_REASON = "…"` | reason literal | R6, F3 |
| 15 | `_UPSTREAM_MULTIPART_PARSE_REASON = "…"` | reason literal | R6, file-local |
| 16 | `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE = dedent(…)` | pinned body | R4, file-local |
| 17 | `def _validate_upstream_shape` | drift refusal (sigs + body pin) | R1, F1 |
| 18 | `def _translated_parse_json` | decode-error translation | R2, F2 |
| 19 | `def _patched_parse_json` | translation + envelope guard | R2/R3, F2 + file-local |
| 20 | `def _patched_parse_query_params` | GET shield reimplementation | R4, file-local |
| 21 | `_MULTIPART_TRAVERSAL_ERRORS = (…)` | shared error set | R5, file-local |
| 22 | `def _raised_inside_the_upload_utility` | provenance predicate | R5, file-local |
| 23 | `def _patched_sync_parse_multipart` | sync delegate | R5, file-local |
| 24 | `async def _patched_async_parse_multipart` | async twin delegate | R5, file-local |
| 25 | `def _mark_patch_replacement` | owner stamping (no loop vars) | machinery, F1 |
| 26–29 | four `_mark_patch_replacement(…)` calls | stamps | machinery, F1 |
| 30 | `def _patch_is_installed` | 4-member atomic probe | R1, F1 |
| 31 | `def apply` | gated idempotent self-healing install | R1, F1 |

Rules: R1 upstream-patch install lifecycle (marks + capture + validate +
installed-check + gated install, shared skeleton with the three siblings);
R2 decode-error translation (`UnicodeDecodeError` / `RecursionError` → 400);
R3 body-envelope guard (scalar / non-object-batch rejection); R4 GET shield
(pinned reimplementation routing around the guard); R5 multipart structural
delegates (provenance-scoped translation, sync/async twins); R6 reason
literals; R7 import-fallback sentinel shape; R8 opt-out hint clause. The
plan's `## Responsibility index` already carries
`upstream-patch-install-lifecycle` (rejected) covering R1 and this target —
reused, not renamed. No other existing family touches this target. F2–F3
below are NEW families named for Worker 0 to add; no existing family name
is reused for them.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 retirement | upstream fixes all three gaps (broadened `except`, #3398 `isinstance` checks, map validation) | **1** (this module deletes outright; other three patch modules untouched; three lifecycles retire independently) | independent |
| C2 | R1 gate rename | `APPLY_UPSTREAM_PATCHES` key renamed | **1** (`conf.py` owns the key; each `apply` passes only its dependency name as consumer) | independent |
| C3 | R1 sequence change | log/lock every install (the only change moving >1 skeleton) | 4 skeletal sites (no such change exists or is planned — the reconsideration trigger, not a count owed today) | independent (see F1) |
| C4 | R1 mark rename | rename the owner-attr string | **1** per module (stamps + capture read co-move in-module; siblings unaffected) | independent |
| C5 | R1 validation depth | `parse_json` starts needing a body pin, or the shield becomes delegating | **1** (this module's validate deepens/shallows alone; siblings untouched) | independent |
| C6 | R2 translation width | a third client-input raise escapes (or one arm proves unreachable) | **1** (`_translated_parse_json`; wrapper + shield follow by name) | independent |
| C7 | R2/view divergence | view changes strict-decode codec policy (e.g. new alias rule) | **1** (`views.py` only; translator untouched — same wire answer, separate reasons to change) | independent (see F2) |
| C8 | R3 envelope shape | allow a new top-level shape, or tighten batch element kinds | **1** (guard; shield routes around it by construction so it does not co-move — C9) | independent |
| C9 | R3/shield coupling | guard change forcing shield review | **1** module (shield calls the translator, never the guard — verified in source + probe: scalar params still pass) | independent |
| C10 | R4 upstream drift | new query param / changed falsy-skip semantics | **1** (pinned source + oracles here; `apply()` fails loud before installing) | independent |
| C11 | R5 traversal shape | new utility error type, or utility restructured past the provenance frame | **1** (tuple / predicate co-move in-module; loud refusal covers the moved-utility half) | independent |
| C12 | R5 transport seam | async parser changes its await seam | **1** (async delegate only; sync untouched — the twin justification) | independent |
| C13 | R6 reason reword | upstream rewords the parse reason | **2** maintained spellings (this module + `views.py`; oracles pin both to upstream's actual raise) | duplication, REJECTED (see F3) |
| C14 | R7/R8 hint/sentinel | reword the opt-out hint; change the `None` sentinel | **1** each (hint: adjacent literals in one function; sentinel: fallback + reads co-move in-module) | file-local |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
settings, no shared-tree pytest — the workspace recipe is for mutating
proofs, of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-_strawberry_patches/probe_w1.py
```

Output (`ALL OK`, 39 sections): target `__file__` printed as the shared-tree
copy; 32-member AST count (10 `FunctionDef` + 1 `AsyncFunctionDef`);
upstream `parse_json` still catches only `JSONDecodeError`; pinned
query-params source byte-equal to installed 0.324.0; all four captures are
the live unmarked upstream methods with `(self, argument)` all-`POSITIONAL_OR_KEYWORD`
shape (`_patch_is_installed()` False in the setup-free process, as expected
without `ready()`); reason literal == upstream's actual raise == views twin;
multipart reason == native async raise; real undecodable bytes → 400 with
`UnicodeDecodeError` cause; real 200 KB nested doc → 400 with
`RecursionError` cause; scalars + non-object batches → 400 while dict /
well-typed batch / `[]` pass and UTF-16 bytes keep auto-detection; GET
`null` → `None`, scalar `42` passes the shield, `""` skipped, malformed →
upstream 400; sync AND async `[{}]` maps → identical 400 while a
traversal-typed server bug keeps its `TypeError` on both; provenance
predicate True inside / False outside the utility frame; traversal tuple
exact; 117-file sweeps (owner-attr ×4, gate + hint single-sited); installed
call-site inventory (9 sites + def; dead-code site confirmed callerless).
Status: `execution-verified` for every identity/count/shape/behavior claim
below. Rejects the wrong results "upstream already catches the decode",
"the capture wrapped a previous package install", "a second production site
spells the gate or the hint", "the shield routes through the guard",
"the delegates downgrade server bugs", "a top-level async twin exists".

## Findings

No production edit is owed by a file item; each finding names the family
that will own it. F1 is REUSED from the plan (rejection re-checked fresh);
F2–F3 are NEW families (Worker 0 to add to the plan's
`## Responsibility index`).

### F1 — upstream-patch install lifecycle (existing family `upstream-patch-install-lifecycle`, status stays `rejected`)

- **Contract + variation.** The per-dependency install shape — gate by
dependency name, fail loud on drift, install idempotently, self-heal a
third-party revert, retain the replaced callable across reloads — repeated
as a skeleton in four modules with per-module validation depth and install
arity. Legitimate variation axes: what is validated (presence+sig vs +body
pin vs +body-SET pin vs +SET-with-teardown-retention), what is installed (1
vs 4 members, atomicity), which gate name, which retirement conditions.
- **Sites + roles.** *Definitions*: the four `_validate_upstream_shape`,
`_patch_is_installed`, `apply`, capture, and `_PATCH_OWNER*` triples — one
set per patch module. *Consumers*:
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
(dispatches the four `apply` calls; deliberately repeats no patch
inventory),
`django_strawberry_framework/conf.py::upstream_patches_enabled` +
`UPSTREAM_PATCH_DEPENDENCIES` (the gate vocabulary, single-owned).
*Oracles*: each module's `tests/test_*_patches.py` lifecycle rows,
`tests/test_apps.py` dispatch + double-reload rows,
`tests/base/test_conf.py` gate-shape rows, plus the live transport rows.
*Projections*: each module's docstring (own bug inventory; the django +
strawberry modules prose-record the delegator/reimplementer depth split;
all three prior file artifacts record the same rejection).
- **Challenges.** C1, C2, C4, C5, C14-hint → 1 each; C3 → the trigger.
- **Trigger re-checked fresh (not inherited).** The recorded trigger is "a
sequence-level change needed in two or more patch modules, or a fifth patch
module arriving with an identical install shape". Measured today: package
still 117 `.py` files (probe); `apps.py` still dispatches exactly 4
appliers (full read); all four `apply()` bodies re-read — still
gate→validate→check→install with no logging, locking, or ordering
additions; this module still the only 4-member atomic install. No fifth
module, no sequence change: the rejection stands on fresh evidence.
- **REJECTED shared form (unchanged):** one driver owning the
gate→validate→check→install sequence and the owner-mark machinery.
Contract differences, this member's share: (a) this module both WRAPS
(three delegations, call-shape pins) and REIMPLEMENTS (one body pin) —
validation depth is per-upstream-contract (C5 moves one module by design);
(b) its 4-member completeness check exists so the scalar guard never runs
without its GET shield and the two transports never diverge — no sibling
has arity-coupled members; (c) per-dependency gates and independent
outright deletion per lifecycle (this module carries THREE retirements that
do not retire together; sharing a driver couples modules with disjoint end
dates); (d) the gate key itself is already single-owned in `conf.py` (C2),
so the only truly shared token already has one owner. Reconsideration
trigger unchanged. Durable home: plan's rejected index row + this module's
docstring (delegator/reimplementer contract + atomicity paragraph) + the
three prior file artifacts' F1 sections + this finding.
- **Owner + lifetime.** No new owner (rejected — each module keeps its
lifecycle). Principle-4 fields for this module's stored derivations (four
captured originals): owner — the module import; validity key — the
installed strawberry release (0.324.0 verified; any drift fails loud at
`apply()`); publish point — import time, before `apply()` can replace; who
may mutate — nobody (rebound only by reload, which re-captures through the
owner mark); invalidated — never within a process.
- **Migration.** None (zero-edit item; rejection, not consolidation).
- **Distinct behavior.** The four lifecycles agree on skeleton, not on
contract: C1/C5 retire or deepen one member without moving the others.
- **Behavioral proof.** `execution-verified` for skeleton population +
capture identity + gate/hint uniqueness + pinned-source equality (probe).
`static-reviewed` for per-module depth differences (four full bodies read)
and oracle bodies (not run; no shared-tree pytest per item rules). Rejects
"a fifth install site exists" and "the capture wrapped a prior package
install".
- **Structural gate.** None owed beyond the existing per-module oracles
(each module's lifecycle rows + `test_apps.py` dispatch row). Negative
control (honest): a shared driver would pass every current behavioral
oracle — the rejection rests on lifecycle/retirement contracts, not on a
behavioral gate, which is why the trigger above is a change obligation,
not a test.
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/_strawberry_patches.py`
`f77df3499eb96051d70055266a677ca3cde5b219`,
`django_strawberry_framework/_cross_web_patches.py`
`6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`,
`django_strawberry_framework/_django_patches.py`
`ba98f5859ec32971c3aa566c221bdc4db392e137`,
`django_strawberry_framework/_graphql_core_patches.py`
`1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`,
`django_strawberry_framework/conf.py`
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`,
`django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f`,
installed upstream `strawberry.http.base`
`ec0126e2aaf416c01b4986c979619afdccce3285`, `sync_base_view`
`620dbec1a56e2fe8d673c6b7f8d26726de2b8338`, `async_base_view`
`7c3cc4d2c86d5ab8a002dbd4bb0d858ae602f1f4`, `file_uploads.utils`
`c15722ad76a09cad814adef134df8fe16037d4c0` (strawberry-graphql 0.324.0).

### F2 — client-body decode failure → controlled 400 (new family `decode-failure-400-translation`, proposed status `rejected`)

- **Contract + variation.** "A client body that cannot be decoded becomes
`HTTPException(400, <json-parse reason>)`, never an unhandled `500`" —
spelled twice: once as an error TRANSLATION for failures escaping
upstream's `json.loads` (temporary, gated, retires with upstream), once as
the package view's own strict UTF-8 DECODE of raw bytes (permanent policy,
ungated, spec-046 Decision 9). The `RecursionError` arm has no view twin
(the view's decode cannot recurse) — it rides the same translator by
construction.
- **Sites + roles.** *Definitions* (rejected pair):
`django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`
(process scope, both transports) and
`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json`
`#"data.decode(\"utf-8\")"` (mount scope). *Contract oracle*: upstream
`BaseView.parse_json`'s `except json.JSONDecodeError → 400` (the shape both
extend, verified narrow on the installed tree). *Consumers*: the wrapper +
shield (first, by name), both package views via `super().parse_json`
(second). *Oracles*: `tests/test_strawberry_patches.py` translation rows
(first, incl. `__cause__` discrimination),
`tests/test_views.py` encoding-matrix + opted-out-constancy rows (second),
the behavioral opt-out row (the pair separates exactly at the switch).
*Projections*: both docstrings' "why not here / why the policy lives here"
paragraphs + spec-046 Decision 9.
- **Challenges.** C6 → 1 (translator); C7 → 1 (view only).
- **REJECTED shared form:** one decode-failure vocabulary both mounts
compose (either the view delegating its decode errors to the translator, or
the patch calling the view's decode). Contract differences: opposite
lifecycles — the translator is a workaround behind `APPLY_UPSTREAM_PATCHES`
that deletes outright on retirement, the decode is permanent wire-contract
enforcement that must hold with the switch off (pinned by the opted-out
constancy oracle); a shared source makes the permanent policy reachable
only through the temporary switch (the exact defect the spec-046 split
fixed) or makes the workaround un-retirable. Opposite mechanisms too:
translating a foreign raise vs performing an own decode with
str-passthrough. Reconsideration trigger: a neutral transport-error
vocabulary both sides already depend on with no lifecycle coupling (today
none exists: the patch must not import the view surface — deletability —
and the view does not import the patch). Durable home:
`views.py::_RequestBodyBoundaryMixin.parse_json` docstring ("Why the policy
lives here and not in the patch module") + this module's docstring ("Where
the strict UTF-8 wire contract lives") + spec-046 Decision 9 + this
finding.
- **Owner + lifetime.** No new owner (rejected — translation stays with the
patch module, decode with `views.py`). No stored derivation beyond F1's
captures; no lifetime fields owed (pure translation, "not cached" by
construction).
- **Migration.** None.
- **Distinct behavior.** On a package view the strict decode runs first, so
the delegate here only ever receives `str` and the translation is
unreachable from that path (probe: UTF-16 bytes keep auto-detection HERE
while the view's matrix 400s them THERE — the pair demonstrably disagrees
where the contracts differ, which is the point of the split).
- **Behavioral proof.** `execution-verified` (probe: real undecodable bytes
→ 400/`UnicodeDecodeError` cause; real 200 KB nested doc →
400/`RecursionError` cause; shield scalar params pass unguarded). Rejects
"the translator decodes" and "the view translation reaches upstream's
view".
- **Structural gate.** The opted-out constancy oracle (view 400s while the
uninstalled translator raises/ignores, same body) + the behavioral opt-out
row (translator really stops hardening when off). Negative control: moving
the strict decode back behind the gate fails the constancy row; deleting
the translator fails only the upstream-mount rows — each definition is
pinned independently, which is the shape a rejection wants.
- **Coupling.** None.
- **Freshness.** Target as in F1 +
`django_strawberry_framework/views.py`
`9f85b0df26a17e800ec392aa13f6848e07633895` +
`tests/test_strawberry_patches.py`
`b431de7728769d24828b90ea59591fa7fb08af6c` +
`tests/test_views.py`
`fa97efdf3309c2944431390a36e7da464c3de327` + upstream fingerprints as in F1.

### F3 — request-body JSON parse reason literal (new family `request-body-json-parse-reason`, proposed status `rejected`)

- **Contract + variation.** "The wire reason for a refused JSON body is
byte-identical everywhere" — spelled twice in-package: this module's
`_UPSTREAM_JSON_PARSE_REASON` and `views.py::_JSON_PARSE_REASON`. (The
multipart reason's only twin is upstream's own code — an external contract
pinned by oracle, not a maintained second spelling; it stays file-local.)
- **Sites + roles.** *Definitions* (rejected pair): the two literals above.
*Authoritative oracle*: upstream's actual raise (both copies assert identity
with it, they do not assert identity with each other).
*Consumers/oracles*: `tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal`
(pins both copies against what upstream actually raises — the gate).
*Projections*: both docstrings' verbatim-reproduction paragraphs.
- **Challenges.** C13 → 2 maintained spellings (honest count — this IS
textual duplication, kept deliberately).
- **REJECTED shared form:** one literal home both modules import. Contract
differences: import direction + deletability — this module must stay
importable (and deletable outright on retirement) without reaching into the
package's view surface, and `views.py` must not import a temporary patch
module for a permanent policy's literal (both docstrings record this); the
copies are each pinned to a THIRD spelling (upstream's) that neither side
can move, so sharing a home removes no change obligation on an upstream
reword (all three move anyway — the oracle, not the sharing, carries that).
Reconsideration trigger: a neutral literals home both sides already import
with no lifecycle coupling. Durable home: both docstrings' reproduction
paragraphs + the pinning test + this finding.
- **Owner + lifetime.** No new owner (rejected). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** C13 moves both spellings + the oracle expectation;
no behavioral divergence is possible by construction (equality is the
contract, probe-asserted).
- **Behavioral proof.** `execution-verified` (probe: this module's literal
== upstream's actual raise == views twin). Rejects "either copy drifted".
- **Structural gate.** The existing reason-literal pin (fails on any of the
three rewordings). Negative control (honest): a shared home would pass the
same oracle — the rejection rests on import-direction/deletability, not on
a behavioral gate.
- **Coupling.** None.
- **Freshness.** Target + `views.py` + `tests/test_views.py` blobs as in
F2 + upstream `strawberry.http.base` as in F1.

### File-local records (no second site after the matrix)

- **R3 — body-envelope guard.** The scalar / non-object-batch rejection in
`_patched_parse_json` (C8, C9 → 1 each; well-typed batches pass through so
upstream's `_validate_batch_request` keeps enablement/size ownership —
probe-executed). Upstream's batch validator is NOT a second definition (it
checks config/size, never element types — the gap). The view's multipart
loss-marker rejection is a different rule (Django-decoded loss detection,
not JSON-envelope shape). Trigger: a second envelope-shape enforcement site
would make it a family. Freshness: target +
`examples/fakeshop/test_query/test_products_api.py`
`8f415dd168b4e13ee5d4d94a5493f61057c389c8`.
- **R4 — GET shield + pinned source.** The source-pinned reimplementation
(C10 → 1; drift fails loud at `apply()` before installing — pinned by the
body-drift + sourceless oracles). The pinned constant is a necessary
reimplementation spelling, not a hidden dup (matrix axis 3). Trigger: a
second consumer of the pinned source would reopen the row, still
single-owned.
- **R5 — multipart delegates + provenance scoping.** The sync/async twins
(share tuple + predicate, differ only by await — matrix axis 2), the
traversal tuple, the provenance predicate (C11, C12 → 1 each;
probe-executed both colors incl. server-bug passthrough). Trigger: a third
multipart seam needing the same translation would make it a family.
Freshness: target +
`examples/fakeshop/test_query/test_transport_api.py`
`17320f1ff335a868d5ed324a49f1d7c4ee899cfc` + upstream
`file_uploads.utils` as in F1.
- **R6b — multipart reason literal.** `_UPSTREAM_MULTIPART_PARSE_REASON`
(C13-adjacent: single in-package spelling, probe-verified; its twin is
upstream's own raise — the oracle, pinned by
`test_the_multipart_reason_is_upstreams_own_native_literal`). Trigger: a
second in-package spelling would join F3's shape.
- **R7 — import-fallback sentinel shape.** `try/except ImportError → None`
(C14: per-module self-consistent; couples only to this module's own
callability reads — same verdict as all three sibling items' sentinel rows,
kept consistent deliberately). Trigger: a shared import-time contract would
make it a family.
- **R8 — opt-out hint clause.** The `Disable this patch with
APPLY_UPSTREAM_PATCHES = {"strawberry": False} …` clause in the drift errors
(C14: one maintenance point; production spelling single-sited,
probe-verified; test spellings are oracles). Per-module dependency names
make cross-module sharing a different contract (F1(d)).
- **R9 — status + retirement-probe prose.** Three-gap narrative, three
lifecycles, upstream tickets (#3398 open; decode gap untracked), re-check
recipes: projections with no second definition; the falsifiable halves
re-verified against installed 0.324.0 (probe). The nine-site inventory holds
on the installed tree (9 call sites + def; dead site callerless).

## Defects

None. Every claim checked while tracing held: the installed 0.324.0
`parse_json` still catches only `JSONDecodeError`; the pinned query-params
source is byte-equal to the installed body; all four captures are the live
unmarked upstream methods; the gate reads its own dependency name; `ready()`
dispatches all four appliers with function-local imports and no inventory
repetition; `__init__.py` never mentions the patch modules; the nine-site
inventory reproduces on the installed tree (7 guarded + 2 shielded + 1 of
the 7 dead); the reason literals equal upstream's actual raise; the upload
utility still traverses without shape checks (probe-executed). The one
candidate nit — docstring pins "0.316.0" / "0.317.2" while 0.324.0 is
installed — is version-scoped prose, not a live contradiction: every
falsifiable half was re-verified stronger against 0.324.0 above. Nothing
routed to any owner.

## Pending execution

None. The execution proofs (read-only probe driving the REAL captured and
patched callables plus the installed-tree inventory, command in
`### Challenges`) already ran green against the shared tree; they mutate no
source and open no database, so no workspace copy was owed. No pytest was
run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items.

## Judgment

Backstop discharged: 32/32 `ast.Module.body` members enumerated, 14
challenges run, every rule terminating in the one existing rejected family
it belongs to (`upstream-patch-install-lifecycle`, trigger re-checked fresh
— still rejected, no new row owed for R1), two new rejected families
(`decode-failure-400-translation`, `request-body-json-parse-reason`), or a
file-local record (R3, R4, R5, R6b, R7, R8, R9) — no consolidation owed, no
defect found. Both new rejections carry contract differences,
reconsideration triggers, and durable homes already prose-recorded at their
owners and cited, not moved. Zero-edit result is legitimate.

Proposed `## Responsibility index` rows for Worker 0 to add:

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `decode-failure-400-translation` | translation at `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`; decode at `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json` | `_strawberry_patches.py`, `views.py` | Family `decode-failure-400-translation` | rejected |
| `request-body-json-parse-reason` | `django_strawberry_framework/views.py::_JSON_PARSE_REASON` + `django_strawberry_framework/_strawberry_patches.py::_UPSTREAM_JSON_PARSE_REASON` (both pinned to upstream's raise) | `_strawberry_patches.py`, `views.py` | Family `request-body-json-parse-reason` | rejected |

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
4c5d83752d64356a5e793fdeeefc4de4f876b01e --
django_strawberry_framework/_strawberry_patches.py` is empty (0 bytes); the
working blob `f77df3499eb96051d70055266a677ca3cde5b219` equals the item
baseline, `HEAD:`, and all three sibling artifacts' recorded fingerprint —
the target is clean, so no hunk attribution was owed. The
`## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never touched;
concurrent dirt (`connection.py`, `tests/test_connection.py`,
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was never edited, reverted, or tidied. Dirt
elsewhere left alone, not a stop. No commit. Untracked scratch created (not
tracked changes): this artifact
`docs/dry/dry-file-_strawberry_patches.md` and the read-only probe
`docs/dry/temp-tests/dry-file-_strawberry_patches/probe_w1.py` (`ALL OK`,
39 sections; no source mutation, no DB, no shared-tree pytest). No ruff run
owed (no tracked edits in scope).

## Independent verification (Worker 2)

Recorded before opening `## Findings`. Instrument: own `ast` count,
own read-only probe
(`docs/dry/temp-tests/dry-file-_strawberry_patches-w2/probe_w2.py`,
`ALL OK`, 39 checks, no mutation, no DB, no pytest), full reads of
`conf.py`, `apps.py`, `_cross_web_patches.py`, the two pin tests, and
the decision-relevant `views.py` regions, plus structural reads of
`_django_patches.py` / `_graphql_core_patches.py` and live upstream
sources at strawberry-graphql 0.324.0.

### Own trace (sites, roles, counts, owner)

| Posited change | Sites | Roles | Defs forced | Owner I would choose |
|---|---|---|---|---|
| Gate key renamed | `conf.py::upstream_patches_enabled` + 4 `apply` gates | def / consumers | 1 | `conf.py` (already owns it) |
| Log/lock every install | 4 `apply` bodies (arities 4 vs 1/1/1, confirmed live) | defs | 4 skeletal (trigger, not owed) | none (rejected, F1) |
| Translator widens / view codec changes | `_translated_parse_json` vs `views.py::parse_json` strict decode | rejected pair | 1 each | keep split (lifecycles oppose) |
| New top-level envelope shape | `_patched_parse_json` guard; shield calls translator (src lines confirmed) | def / deliberate non-consumer | 1 | target (file-local, R3) |
| Upstream QP drift | pinned source vs live body (byte-equal today) | def+pin / oracle | 1 | target (file-local, R4) |
| New traversal error / moved utility | tuple + provenance predicate + twins | defs | 1 | target (file-local, R5) |
| Upstream rewords parse reason | two literals + upstream raise (third spelling) | rejected pair / authoritative oracle | 2 spellings | none (rejected, F3) |
| Hint / sentinel reword | one function / in-module fallback | file-local | 1 each | target (R7/R8) |

Reconciliation: identical to Worker 1 on every row — F1 reused
rejected, F2/F3 new rejected with the same owners (no new owner in
both cases), R3/R4/R5/R6b/R7/R8/R9 file-local. No difference to
reconcile; the UTF-16 split (patch auto-detects, view 400s) I
re-executed live, confirming F2's "demonstrably disagrees" claim.

### Enumeration (member-by-member)

Own count: 32 `ast.Module.body` members, 10 `FunctionDef` + 1
`AsyncFunctionDef`, 4 `_mark_patch_replacement(...)` `Expr` calls —
matches the artifact's table row for row (0 docstring … 31 `apply`).
Every member lands in a family row or file-local record. Agree.

### Matrix vs real surface

Axis 1: sibling skeletons compared by contract (4-atomic vs 1/1/1
installs confirmed live; wrap-vs-reimplement depths differ). Axis 2:
multipart twins share tuple + predicate, differ only by await (both
colors executed → identical 400; server `TypeError` passes through
both); POST sites share one `BaseView` method. Axis 3: signatures
derived via `inspect`, gate/hint single-sited (own sweeps over 117
files agree), pinned source necessary. Axis 4: capture/validate one
pipeline; shield pin byte-equal to installed 0.324.0. Axis 5: oracles
pin to live upstream raises (both pin tests read in full — they
assert against the captured upstream callables, never against an
owner literal alone). Axis 6: 4-member atomicity in source; 9
`parse_json(` call lines found independently (2 GET shielded, 7
body/multipart of which the subs site is def-only, callerless);
package-view strict-decode-first confirmed in `views.py` source.
All six discharged. Agree.

### Counts, roles, oracles, equivalence

All 14 challenge counts confirmed (load-bearing ones re-executed:
C6/C7, C8/C9, C10, C11/C12, C13). Roles correctly tagged; no oracle
rewritten to read from its owner (the `test_views.py:2117`
cross-equality sits behind the `2116` upstream pin). Principle-8
equivalence re-verified by execution: same 400s/reasons/causes on
real undecodable bytes, a real 200 KB nested doc, scalars,
non-object batches, both multipart colors, and GET shield rows.
Zero-edit accepted: item-baseline diff re-confirmed empty by me (0
bytes; worktree blob = `HEAD` = baseline `f77df349…`); 32/32
covered and assigned; nothing routed nowhere. No production edit
owed or demanded.

### Rejections, fingerprints, gates, pending, coupling

F1/F2/F3 each carry a concrete contract difference,
reconsideration trigger, and prose-recorded durable home (both
docstring paragraphs read). Freshness: all 11 in-repo blob ids
re-hashed by me — exact match, including both fakeshop live-test
files. The 4 upstream `.venv` blob ids are irreproducible from the
live tree (recorded `ec0126e2…`/`620dbe…`/`7c3cc4…`/`c15722…` vs
live `05df08…`/`48ca38…`/`1027f6…`/`ea08c2…`); every
decision-relevant upstream property they support was re-verified
green live (narrow `except`, QP byte-equality, unguarded
traversal, native reasons), so no finding reopens — Worker 0 note
below. Gates: F1 honestly gateless (rejection on lifecycle
contracts); F2/F3 gates are the named pin/constancy oracles whose
bodies I read (failability evident by construction; full
`prove_failability` execution not owed on a zero-edit file item —
oracles `static-reviewed`, consistent with the verified
`utils/querysets.py` precedent). `## Pending execution`: absent,
correct — both read-only probes already ran green. Coupling: all
`None`, correct. Probe hygiene note: my `E5`-first tautology line
is vacuous; the substantive second `E5` (view 400s UTF-16) passed
and carries the claim.

### AGENTS.md prose check

Empty item-scoped diff: no provenance, no citations, no test tier
owed. Artifact uses `path::Symbol`; the one raw `path:NN` ref is
permitted in per-cycle scratchpad artifacts. No pytest run, no
commit, concurrent dirt untouched. No ruff owed (no tracked edits).

## Defects (Worker 2)

None. The version-pinned prose (`0.316.0`/`0.317.2` vs installed
`0.324.0`) is historical record whose falsifiable halves re-verify
green live — concur with Worker 1, not a defect. The upstream
fingerprint note above is artifact freshness, not a production
defect: no owner, no card.

## Judgment (Worker 2)

`verified`, no pending execution. Zero-edit backstop legitimately
discharged. Worker 0 rows: tick File `_strawberry_patches.py`;
append the two proposed `## Responsibility index` rows and two
`## Families` items exactly as drafted under `## Judgment`; ledger
unchanged (no owned changes); optionally re-hash or annotate the 4
upstream `.venv` fingerprints (live values listed above).
Scratch left on disk:
`docs/dry/temp-tests/dry-file-_strawberry_patches-w2/probe_w2.py`.
