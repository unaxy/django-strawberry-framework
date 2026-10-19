# DRY review: `upstream-patch-refusal-wording`

Status: verified
Run: 0.0.15 2026-10-01-9

Family `upstream-patch-refusal-wording`. Owner re-derived here, not
inherited: none cross-module; each patch module owns its own install-refusal
messages (rejection, so no consolidation owner exists). Indexed files (4):
`django_strawberry_framework/_cross_web_patches.py`,
`django_strawberry_framework/_django_patches.py`,
`django_strawberry_framework/_strawberry_patches.py`,
`django_strawberry_framework/_graphql_core_patches.py`.
Trace at HEAD `5c3496e0`; `ITEM_BASELINE=65ed56412fb80ab496b6b2a7a8dd3a6142ff55ed`
(resolves). The four modules carry concurrent worktree dirt (truth-migration
plus docstring/prose); a diff-grep proof below shows zero dirt lines touch any
refusal literal, so traced bytes equal HEAD bytes for this rule. Prior record
(run-2 File `_cross_web_patches.py` naming this open family over 11 raise
sites / 4 wordings, W2-endorsed; run-9 e10 `upstream-patch-lifecycle`
re-deriving 11 refusal decision points 3+3+3+2 with django's teardown-guard
raise homed at plan row 344 file-local) used only as a population hint; every
count, role, and verdict below re-derived fresh. Never read any
`worker-memory/`. Lifecycle shapes and counts are e10's, untouched here; this
item owns refusal message text only.

Verdict in one line: REJECT - the 11 install refusals are 11 single-owned
messages sharing a parallel-construction convention, not definitions of one
wording rule; every functional change moves at most one wording definition,
and the only cross-site change (global glue rewording) is aesthetic, forced
by no contract. Zero edits; no consolidation confirmed, so nothing is
blocked-on-hunt.

## System trace

The queued rule is the refusal/wording of upstream-patch install refusals:
the `RuntimeError` text each patch module raises from `_validate_upstream_shape`
(or `_upstream_captures`) when the installed upstream no longer matches the
shape the patch assumes. Mechanism sweep over the whole package
(`django_strawberry_framework/**/*.py`): the literal `Cannot apply` occurs
exactly 11 times, all inside the four indexed modules (3+3+3+2); `Disable this
patch` occurs 11 times in the same statements (one split across two literals);
no fifth module raises an install refusal. `apps.py::ready` dispatches the
four `apply()` calls and carries no refusal text of its own.

The 11 sites, each a definition of its own complete message (reasons differ at
every site; envelopes differ per module and, for strawberry, per refusal):

Cross-web (`_cross_web_patches.py::_validate_upstream_shape`):
CW1 `:271` symbol-missing - `Cannot apply django-strawberry-framework's
cross_web patch: expected cross_web.DjangoHTTPRequestAdapter. Disable this
patch with APPLY_UPSTREAM_PATCHES = {"cross_web": False} or use a supported
cross_web version.`
CW2 `:278` property-shape - same envelope; reason `DjangoHTTPRequestAdapter.body
is no longer a readable property.`
CW3 `:286` signature - same envelope; reason `DjangoHTTPRequestAdapter.body no
longer has the expected (self) getter signature.`

Django (`_django_patches.py::_validate_upstream_shape`):
DJ1 `:260` symbols-missing - `Cannot apply django-strawberry-framework's Django
patch: expected django.test.testcases._DatabaseFailure and
SimpleTestCase._remove_databases_failures as a classmethod. Disable this patch
with APPLY_UPSTREAM_PATCHES = {"django": False} or use a supported Django
version.`
DJ2 `:269` signature - same envelope; reason
`SimpleTestCase._remove_databases_failures no longer has the expected (cls)
signature.`
DJ3 `:280` body-mismatch - same envelope; reason
`SimpleTestCase._remove_databases_failures no longer matches any audited
upstream body this patch supersedes.`

Strawberry (`_strawberry_patches.py::_upstream_captures` /
`_validate_upstream_shape`):
SB1 `:567` captures - `Cannot apply django-strawberry-framework's Strawberry
patch: expected BaseView.parse_json, BaseView.parse_query_params,
SyncBaseHTTPView.parse_multipart, AsyncBaseHTTPView.parse_multipart,
strawberry.file_uploads.utils.replace_placeholders_with_files, and
cross_web.HTTPException. Disable this patch with APPLY_UPSTREAM_PATCHES =
{"strawberry": False} or use supported dependency versions.`
SB2 `:617` signature loop over four methods - `Cannot apply
django-strawberry-framework's Strawberry patch: {name} no longer has the
expected (self, {argument}) signature. Disable this patch with
APPLY_UPSTREAM_PATCHES = {"strawberry": False} or use a supported Strawberry
version.` with `(name, argument)` one of `(BaseView.parse_json, data)`,
`(BaseView.parse_query_params, params)`,
`(SyncBaseHTTPView.parse_multipart, request)`,
`(AsyncBaseHTTPView.parse_multipart, request)`.
SB3 `:628` body-mismatch - `Cannot apply django-strawberry-framework's
Strawberry patch: BaseView.parse_query_params no longer matches the upstream
body this patch supersedes. Disable this patch with APPLY_UPSTREAM_PATCHES =
{"strawberry": False} or use a supported Strawberry version.`

Graphql-core (`_graphql_core_patches.py::_upstream_captures` /
`_validate_upstream_shape`):
GQ1 `:99` captures - `Cannot apply django-strawberry-framework's graphql-core
patch: expected ExecutionContext.complete_list_value and
graphql.pyutils.is_iterable. Disable this patch with APPLY_UPSTREAM_PATCHES =
{"graphql_core": False} or use a supported graphql-core version.`
GQ2 `:114` signature - same envelope; reason
`ExecutionContext.complete_list_value no longer has the expected (self,
return_type, field_nodes, info, path, result) signature.`

Envelope anatomy: prefix `Cannot apply django-strawberry-framework's {dep}
patch: ` (4 displays: `cross_web`, `Django`, `Strawberry`, `graphql-core`) +
reason (unique per site) + hint `Disable this patch with APPLY_UPSTREAM_PATCHES
= {"{key}": False} ` (4 keys, each its module's
`conf.py::UPSTREAM_PATCH_DEPENDENCIES` member) + tail `or use {tail}.` (5
distinct tails: one per module, plus strawberry's captures tail `supported
dependency versions` differing from its validate tail `a supported Strawberry
version`).

Connected behavior examined and excluded (each with its contract difference in
Findings): django's teardown-guard raise (`_django_patches.py:328`, no
opt-out clause, raised at teardown not install); strawberry's five runtime
`HTTPException(400, ...)` raises (`_strawberry_patches.py:668,670,747,873,887`,
consumer-visible request hardening, not install refusal);
`conf.py::upstream_patches_enabled` (`ConfigurationError`/`ValueError` for a
malformed setting, not upstream drift); module docstrings (projections of the
opt-out shape, describing, never owning).

## Verification

### Matrix

1. Cross-flavor policy mirroring - discharged by the census itself: the four
patch modules ARE the flavors. Every `Cannot apply` in the package sits in the
11 inventoried sites; sibling flavors excluded with contract differences:
`conf.py` config errors read in full, `views.py` strict-decode 400s examined
via `views.py::_JSON_PARSE_REASON` (def `:152`, raises `:711,754,801,864`) and
the strawberry module's documented deliberate-duplicate note (~~D1 below
recorded that note's stale test pointer - struck, see Defects~~).
2. Sync/async twins - inapplicable with reason: every refusal raises
synchronously from `apply()` at app load; no async twin exists. The
sync/async multipart delegates differ in runtime 400 translation, which is
outside this family (R-400).
3. Derived rather than repeated knowledge - discharged: the setting-name and
dependency-key tokens inside the messages are projections of
`conf.py::APPLY_UPSTREAM_PATCHES_KEY` and `conf.py::UPSTREAM_PATCH_DEPENDENCIES`
(R-KEY, counted 0 here). Dependency display names are NOT derivable from keys
by one function: `django`->`Django`, `strawberry`->`Strawberry`,
`graphql_core`->`graphql-core`, `cross_web`->`cross_web` (capitalize fails two,
underscore-to-hyphen fails three) - each display is its module's own wording
decision.
4. Inverse / round-trip pairs - inapplicable with reason: messages are
terminal (raised at startup, never parsed by any code). The one genuine pair -
the hint spelling the mapping shape `conf.py::upstream_patches_enabled` parses
- belongs to the config-shape rule owned there; the hints are its projections
(R-KEY).
5. Contracts restated in another medium - discharged: oracles pin
per-module reason fragments only (full inventory in Challenges C1; the sole
hint pin is `tests/test_django_patches.py:752` matching `{"django": False}`);
no test or example pins the full envelope (`Cannot apply` / `Disable this
patch` / `or use supported` all zero hits across `tests/`, `examples/`, and
standing docs). Module docstrings restate the opt-out shape as projections.
6. Enforcement by omission - discharged: every install-refusal decision point
in the four modules carries the envelope (11 of 11 raises enumerated above).
The raises without it are different rules, each excluded on a contract
difference (R-TEARDOWN, R-400, R-CONF), not omissions: no contract source
requires the install-refusal envelope on a teardown invariant, a runtime 400,
or a config-shape error.

### Enumeration

Family item: no file-member enumeration owed. Mechanism-sweep census stands in
its place. Instruments and populations: literal search `Cannot apply` over
`django_strawberry_framework/**/*.py` (11 hits / 4 files, every hit homed
above); literal search `Disable this patch` over the package (11 hits, same
statements); regex `or use (a )?supported` over the package (10 single-line
hits plus CW1's literal-split 11th); regex `raise \w+` over the four modules
(17 code raises: 11 envelope + 1 teardown + 5 HTTPException, each homed);
literal searches for all three envelope markers over `tests/`, `examples/`,
`docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `KANBAN.md` (0 hits outside
cycle scratch). Nothing unassigned.

### Challenges

Each challenge posits a functional change on one variation axis and counts
authoritative WORDING definitions forced to move. Key/setting tokens move as
projections of `conf.py` rules (listed, not counted, per DRY.md).

C1 reason axis - reword one module's reason (e.g. CW3 names a new getter
arity): count 1 (CW3 alone). Moving but not counted: its reason-fragment oracle
(`tests/test_cross_web_patches.py:183` matching `expected \(self\) getter
signature`). Oracle coverage is complete across all 11: CW1 `:176`, CW2 `:202`;
DJ1 `tests/test_django_patches.py:310`, DJ2 `:325`, DJ3 `:367`+`:459`+`:609`;
SB1 `tests/test_strawberry_patches.py:455`+`:469`+`:482`+`:496`+`:510`, SB2
`:503`+`:517`+`:539`, SB3 `:572`+`:597`; GQ1
`tests/test_graphql_core_patches.py:113-116` (3 params), GQ2 `:101`.
C2 key-identity axis - rename one dependency key (e.g. `django`): wording
count 0. The key literals move as projections of
`conf.py::UPSTREAM_PATCH_DEPENDENCIES` (single-owned); the stale gate call
fails loud via `upstream_patches_enabled`'s `ValueError`, which is the
package's chosen drift enforcement for key spellings. Listed: 3 message
literals, the gate call (lifecycle, e10's), docstrings, the constant.
C3 tail axis - strawberry's captures span narrows to strawberry-only names, so
SB1's tail becomes `a supported Strawberry version`: count 1 (SB1 alone; SB2
and SB3 keep their tail). Proves tails are per-refusal decisions: two tails
already coexist inside one module for one key.
C4 glue axis - global rewording (`Disable this patch with` -> `Opt out with`):
wording-rule count 0. Eleven literals move textually, but no contract forces
joint movement: each message stays independently correct, no oracle pins the
glue, no code parses it. Shared text without a shared change reason is
convention, not a rule (DRY principle 3: same-today agreement with separate
reasons to change stays separate).
C5 new-member axis - a fifth patch module lands: count 0 existing definitions
move (pure addition). The convention scales by copying three lines; a shared
helper would instead demand a table row plus an import edge into the new
module's retirement lifecycle.

## Findings

### F-WORD (REJECT): cross-module refusal-envelope consolidation

Contract + variation - candidate rule: every install refusal renders
prefix(dep) + reason + hint(key) + tail. Legitimate variation: dep display (4),
key (4), reason (11 unique), tail (5 over 11 sites). A shared helper would
take all four as parameters - every argument varies at every call.
Sites + roles - 11 definitions, each of its own complete message (CW1-CW3,
DJ1-DJ3, SB1-SB3, GQ1-GQ2); 11+ oracles (reason-fragment pins, C1 inventory);
projections: module docstrings, this section. No consumer parses the text.
Challenges - C1 count 1, C2 count 0 (projections), C3 count 1, C4 count 0
(convention), C5 count 0. No functional change forces two wording definitions
to move together.
Owner + lifetime - considered owner: a helper on `conf.py` (already imported
by all four, owns the key constant and dependency set). Rejected under DRY
principle 7: the helper would own glue tokens only, while the content it
formats (dep story, key, tail distribution logic, reason) stays per-module -
distinct decisions stay at adapters. Reads/effects: the helper would read four
varying arguments per call and effect string formatting with no enforcement
authority (no reader requires sameness). Lifetime: no stored derivation exists
(messages constructed inline at raise; pure construction, not cached), so
principle 4 adds nothing. Chosen: none cross-module; each module owns its
messages. Dependency-direction note: a shared owner would also couple the four
independent retirement lifecycles e10 established (each module is deleted when
its upstream fixes the bug; the last deletion would owe helper+table+test
removal - a new change obligation, not fewer).
Migration - none; nothing moves.
Distinct behavior - each module keeps its full message text inline, including
strawberry's twin tails and cross-web's literal-split first site (renders
byte-identical glue; examined-and-cleared, not a defect).
Behavioral proof - zero-edit, so no equivalence to prove. Census
(static-reviewed): the five searches under Enumeration, each naming its
population. Oracle completeness (static-reviewed): every install refusal has
at least one reason-fragment oracle (C1 inventory). One execution witness
(execution-verified, shared project venv):
`uv run pytest tests/test_django_patches.py::test_django_dependency_opt_out_silences_drifted_pin_abort --no-cov -n0`
- 1 passed; witnesses DJ3's hint rendering plus gate-before-validation
precedence. Type gates (shared project venv, corroborating tree health):
`uv run mypy` clean (119 files), `uv run basedpyright` 0/0/0,
`uv run python scripts/check_any.py` 130 uses at 90 sites, all exit 0.
Cells sharded/pg: inapplicable by construction - the rule's code path
(import-time capture plus `apply()` at app load) reaches no database, alias,
or dialect decision.
Structural gate - none owed: a rejection has nothing to bypass, and per-message
sameness has no plausible bypass population (no reader depends on the glue;
DRY.md forbids a bespoke existence test per helper). The existing
reason-fragment oracles already fail if any message drops its reason.
Coupling - none.
Freshness - traced bytes equal HEAD bytes for the rule (proof: worktree-vs-HEAD
diff over the four modules contains zero added/removed lines matching `Cannot
apply|Disable this patch|or use (a )?supported|without a validated
upstream|Unable to parse`; same for the canonical key literals in `conf.py`).
Fingerprints (`git hash-object` work / `git rev-parse HEAD:`):
`_cross_web_patches.py` 16c05c78e10457d824fbf2e303bd8f05c131dbb6 /
e5a69a5500bb96465ac8934b2287df69206dbd62;
`_django_patches.py` 5ca5493ffa4973dc0ce97f8f36a73051ce7a48ab /
20bfb1f87de2d59876cd09f1d5cca671c99caa03;
`_strawberry_patches.py` ec4926749e9e0f17f045e518ccc41362982dfde3 /
aa08b628c84a6280e2bfed9291a5c4061060a5dc;
`_graphql_core_patches.py` 2d1dd0cd6331189f942ea500e50eefa627147920 /
8ede2487994c0bc5675725adcb22238e3f6786ac;
`conf.py` d239302afaa55213f42ca7d430fed52dcb42490c /
eccddc21c635dd9a2cf282a3d22e50847e62ef84;
`apps.py` 64e82ce1e9e7dd832602477f2e5bca54f0073304 (clean);
`tests/test_cross_web_patches.py` 70c16389aa5d2a14746dba1612c909263bffd822
(clean); `tests/test_django_patches.py`
6e62c784389b0490e174ae5825d9ebdb9428199a /
e26a26099c12efb2e2cab1e324b73226eab5dd76 (dirt avoids all cited oracle lines -
zero diff lines match `match=` or refusal-test defs);
`tests/test_strawberry_patches.py` 1da2333dc91bb10328e2fc75adfb7ea06bc05405 /
64f25eeb77b15459eaa53da1b309fe3d1182c032 (same oracle-line stability);
`tests/test_graphql_core_patches.py` 53dca51737e6163c09549d015713ebf9dfcdec88
(clean). Searched populations: whole package for envelope markers; `tests/`,
`examples/`, standing docs for cross-medium pins. Excluded on body strength:
`conf.py::upstream_patches_enabled`, `apps.py::ready`, strawberry runtime 400
sites, django teardown guard. Any fingerprint change reopens.
Trigger - reconsider if (a) a fifth patch module copies the envelope AND one
edit must change the glue in all five for correctness rather than style; (b)
the opt-out mechanism changes shape (not just a key rename, which stays a
`conf.py` projection change) forcing all hints to move together; or (c) an
oracle starts pinning the full envelope across modules.

### F-LOCAL (REJECT): module-local envelope helpers

Within cross-web, django, and graphql-core the envelope is verbatim-shared
across 3/3/2 raises with only the reason varying, so a one-parameter local
helper (`_refusal(reason)`) is the strongest consolidation shape this family
admits. Rejected: the envelope's fixed content has no per-module functional
change driver. Reasons move singly (C1); keys move as `conf.py` projections
(C2); tails move singly (C3); glue moves globally-or-not-at-all (C4) - a
within-module helper relieves 3-to-1 only for a change that never occurs
per-module, so it relieves no change obligation (a finding relieving none is
not a finding). Strawberry fragments the shape further: its twin tails need a
second parameter or a second helper, proving the frame is not one rule even
within a module. Three new private symbols plus call indirection to save glue
repetition is machinery under DRY principle 11. Count for every functional
change: at most 1. Owner stays each module's raise sites as-is. Trigger: one
module's envelope gains a second functional change driver shared by all its
raises (e.g. a per-module reason-code registry the messages must encode).

### R-KEY (exclusion): setting-key and dependency-key tokens in message text

The `APPLY_UPSTREAM_PATCHES` and `{"<key>": False}` tokens inside the 11
messages are projections of `conf.py::APPLY_UPSTREAM_PATCHES_KEY` and
`conf.py::UPSTREAM_PATCH_DEPENDENCIES`, not wording definitions - counted 0 in
C2. Interpolating the constants via f-strings would relieve only the literal
half of a key rename while docstring projections (dozens of spellings across
five module docstrings) still move by hand, and static literal text keeps every
consumer-facing spelling greppable. Trigger: a key rename lands with a message
literal missed - name the key-spelling family then.

### R-CONF (exclusion): `conf.py` config-validation wording

`upstream_patches_enabled`'s `ConfigurationError`/`ValueError` messages are a
different rule: raised for a malformed setting (non-bool, non-mapping,
non-string key, unknown name, non-bool value), read at gate time, with the
recourse "fix the setting shape" - versus install refusals raised for upstream
drift at validate time with the recourse "opt out or use supported versions".
Different exception types, triggers, and recourses; no shared content beyond
the setting name both must spell. Trigger: the two recourses merge (e.g. drift
auto-disables with a warning quoting the config grammar).

### R-TEARDOWN (exclusion): django teardown-guard raise

`_django_patches.py:328` (`django-strawberry-framework's Django patch ran
without a validated upstream _remove_databases_failures body.`) is OUTSIDE
this family - plan row 344 file-local stands, confirmed fresh. Contract
differences: no `Cannot apply` prefix, no opt-out hint, no tail; raised at
test-teardown time when prior validation state is unexpected (an internal
invariant: `apply()` must have validated first), not at install when upstream
drifted. Its oracle (`tests/test_django_patches.py:589` matching `without a
validated upstream`) pins that invariant. Trigger: the guard gains consumer
recourse text (an opt-out hint or version pointer), making it a refusal.

### R-400 (exclusion): strawberry runtime request-hardening rejections

The five `HTTPException(400, ...)` raises (`_strawberry_patches.py:668, 670,
747, 873, 887`) are consumer-visible request rejections owned per-gap (decode
translation, envelope guard, multipart traversal), each with its own reason
constant (`_UPSTREAM_JSON_PARSE_REASON`, the envelope sentence,
`_UPSTREAM_MULTIPART_PARSE_REASON`). Contract differences: raised per-request
at runtime with a 400 status the client sees, versus raised once at startup
with a traceback the deployer sees; no patch name, no opt-out hint, no tail.
Trigger: a runtime rejection starts quoting install-refusal recourse.

## Defects

~~D1 (minor, doc-only): struck - factually false. The pass-1 claim that
`_strawberry_patches.py:484-492`'s test pointer is stale is wrong: the pin
`test_the_wire_reason_is_upstreams_own_parse_json_literal` exists at
`tests/test_views.py:2070` (HEAD `:2104`), imports both constants, raises
upstream's live `parse_json`, and asserts both equalities, exactly as the
comment claims. Full proof in `## Independent verification (Worker-2)`,
`### D1 (own pre-reading)` plus the `D1: REJECT` reconciliation; no File
`_strawberry_patches.py` routing is owed.~~ Freshness pins (confirmed
correct, retained): `tests/test_views.py`
a1de514154a5e010c306f6251a9ae65ae01d2d4d /
715f3808c50a73099f8fdd62e16f8c07167552f6;
`django_strawberry_framework/views.py`
d1ff2aba3ca64a9879f69ccf3ee2427ebd39af69 /
d627d5dd98663f3906e25292900eecb373ad28f4 (strawberry-module fingerprint in
F-WORD above).

Examined-and-cleared (not filed): strawberry's twin tails (`supported
dependency versions` on SB1 spanning strawberry plus cross_web names versus `a
supported Strawberry version` on SB2/SB3 covering strawberry methods only) are
deliberate per-refusal reasoning, corroborated by SB1's symbol list; cross-web
CW1's literal-split shape renders byte-identical glue to CW2/CW3 (source-split
cosmetic only, no reader observes it).

## Judgment

REJECT the consolidation, zero-edit verdict. Eleven install refusals, eleven
single-owned messages: reasons move singly, keys move as `conf.py`
projections, tails move singly (one module already carries two), and the
shared glue has no functional change driver - global rewording is taste, not
contract. Both consolidation horns fail: cross-module sharing needs an
all-varying formatter coupled to four independent retirement lifecycles
(F-WORD); module-local helpers relieve a per-module change that never occurs
(F-LOCAL). Four exclusions carry contract differences plus triggers (R-KEY,
R-CONF, R-TEARDOWN, R-400). Sharded/pg cells inapplicable by construction.
Recommended plan-row owner: none (rejected as one rule; each module owns its
messages) - Worker-0's edit to make.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (header + section outline only; W1's
verdict was already known from the dispatch brief, nothing else inherited).
Trace at WT bytes; refusal literals verified identical to HEAD `5c3496e0` by
the fingerprint check below (WT pins match dispatch pins; dirt attribution by
content in `### Fingerprints`).

### Census (own)

Install-refusal `raise RuntimeError` sites (all `Cannot apply ...` prefixed,
all carrying a per-key opt-out sentence + a `supported ... version` tail):

- `_cross_web_patches.py::_validate_upstream_shape`: 3 (missing adapter
  symbol; body no longer a readable property; `(self)` getter signature).
- `_django_patches.py::_validate_upstream_shape`: 3 (missing
  `_DatabaseFailure`/classmethod descriptor; `(cls)` signature; body outside
  the audited set).
- `_strawberry_patches.py`: 3 (`_upstream_captures` missing-symbol refusal;
  `_validate_upstream_shape` per-method `(self, argument)` signature loop;
  `parse_query_params` body mismatch).
- `_graphql_core_patches.py`: 2 (`_upstream_captures` missing-symbol refusal;
  `_validate_upstream_shape` 6-parameter signature check).

Total 11 = 3+3+3+2. A 12th `RuntimeError` raise exists
(`_django_patches.py::_disallowed_connection_methods`, "ran without a
validated upstream body"): teardown-time invariant, no `Cannot apply` prefix,
no opt-out sentence, fires post-install at `tearDownClass` - a different
contract, excluded (expectation: R-TEARDOWN or equivalent).

Roles: each of the 11 literals is a candidate definition of one posited
wording rule. Oracles: per-module `match=` pins of reason fragments only
(`tests/test_cross_web_patches.py`, `tests/test_django_patches.py`,
`tests/test_strawberry_patches.py`, `tests/test_graphql_core_patches.py`;
e.g. django `:752` pins only its own `{"django": False}` token) - no test
pins the shared prefix/suffix glue across modules, so no oracle forces
uniform wording. `apps.py::ready` dispatches the four `apply()`s without
catching or rewording: no fifth site. No doc-medium restatement of the
wording as a contract (`Cannot apply` appears in `docs/` only in prior DRY
scratch describing the shape, never as a stated rule).

### Challenges (own; each change posited + definitions forced)

- C1 security redaction ("strip private upstream symbol names from
  refusals"): moves differ per module (public `DjangoHTTPRequestAdapter` /
  private `_DatabaseFailure` / public-ish `parse_json` family); shared glue
  does not move. No uniform multi-definition move - supports reject.
- C2 support-URL rotation: messages contain no URLs; 0 definitions.
  Inapplicable.
- C3 error-code prefix ("DSF-701: " on every refusal): 11 literals move
  textually, but no contract (test, doc, AGENTS.md grammar) requires uniform
  prefixes; the change is aesthetic and hypothetical (no such policy
  exists). A shared prefix owner would couple four independent retirement
  lifecycles to save a future sed - machinery, not a finding.
- C4 dependency-key rename (e.g. `graphql_core`): the 2 same-module
  message literals + that module's `apply()` gate + `conf.py`'s canonical
  `UPSTREAM_PATCH_DEPENDENCIES` + its docstring + tests. The key tokens in
  messages consume conf's vocabulary; the rename itself is a breaking
  documented-setting change (~never), and retirement deletes the module.
  Module-local `_DISABLE_HINT` constants relieve a change that never
  occurs; runtime-deriving the hint from the key adds machinery for zero
  change obligation.
- C5 single-module glue reword (reword only cross_web's opt-out
  sentence): 3 literals in one module - the strongest count-against (3 >
  1). Still not a finding: no trigger rewords one module's glue alone;
  each message's reason clause is its content, so a `_refusal(reason)`
  helper owns glue only; a new-condition change costs 1 edit with or
  without the helper; retirement deletes all three together. The helper
  relieves no change obligation.
- C6 "every refusal names its opt-out" as a package rule (11 enforcement
  sites?): the policy is inferred from parallel construction, stated
  nowhere as a rule; each opt-out names its own key. Without an
  established rule there is no single owner, so no gate-only finding
  either - a gate here would legislate parallel construction as law. At
  most a trigger: if a stated policy ever requires it (e.g. a fifth patch
  module), revisit.

Owner I would choose: none cross-module. Each patch module owns its own
install-refusal messages; `conf.py::UPSTREAM_PATCH_DEPENDENCIES` owns the
key vocabulary the messages quote. Reject decomposition, zero-edit.

### Matrix (own pre-discharge)

1. Cross-flavor: the four patch modules ARE the flavors; read all four
   whole. Covered by the F-WORD-equivalent rejection above.
2. Sync/async twins: inapplicable - every refusal raises synchronously at
   `apply()` time; no async twin exists.
3. Derived knowledge: key tokens quoted from conf's registry (R-KEY
   shape); the `Cannot apply` prefix restated 11x is the rejected rule
   itself, not a second derivation.
4. Round-trip: inapplicable - messages are write-only (raised, never
   parsed by any consumer or test).
5. Other media: oracles pin per-module reason fragments (independent,
   uncounted); no doc states the wording as a contract.
6. Omission: swept - every `apply()` gates before validating in all four
   modules; the one shape-deviant raise (teardown guard) differs by
   contract (post-install invariant, no opt-out to name), not by omission.

### Cells + gates (own expectation)

Refusal construction/raising reaches no database, alias, or dialect
decision (django's `connections` iteration is patched-teardown behavior,
not wording; zero-edit changes nothing under any cell), so sharded/pg
`inapplicable by construction` is acceptable IF W1 states the reason
(which the brief says it does). No tracked `.py` touched means
ruff-on-touched-paths is vacuous; W2 re-runs the three whole-package type
gates for comparability (results in `### Gates` below).

### D1 (own pre-reading)

The brief says W1's D1 calls the `_strawberry_patches.py:484-492` comment
a stale test pointer (pin claimed absent from `tests/test_views.py`). Own
evidence disagrees: `test_the_wire_reason_is_upstreams_own_parse_json_literal`
exists at WT `tests/test_views.py:2070` (= HEAD `:2104`, file concurrently
dirty but the test present in both), imports both constants
(`views::_JSON_PARSE_REASON` via the `:99-107` import, `patches` via `:81`),
exercises upstream's live raise through `patches._original_parse_json`,
and asserts BOTH `excinfo.value.reason == _JSON_PARSE_REASON` and
`patches._UPSTREAM_JSON_PARSE_REASON == _JSON_PARSE_REASON` - exactly what
the comment claims. Reconciliation with W1's exact D1 text below; if the
artifact says the pin "does not exist", D1 is factually false and must be
struck, not routed (a false defect routed to File `_strawberry_patches.py`
spawns bogus closeout work).

### Fingerprints (own)

- WT `git hash-object`: `_cross_web_patches.py` `16c05c78…`,
  `_django_patches.py` `5ca5493f…`, `_strawberry_patches.py` `ec492674…`,
  `_graphql_core_patches.py` `2d1dd0cd…` - 4/4 match dispatch pins.
- HEAD `git rev-parse HEAD:`: `e5a69a55…`, `20bfb1f8…`, `aa08b628…`,
  `8ede2487…` - 4/4 match dispatch pins.
- Refusal literals byte-identical WT-vs-HEAD: every `Cannot apply` /
  teardown-guard / `HTTPException(400` literal read above sits outside the
  truth-migration + prose dirt hunks (dirt touches imports, `truth.*`
  call sites, docstrings, and comments; no raise line differs - verified
  by reading both states' raise blocks, not by line numbers alone).
- Exclusion bodies fingerprinted by the same reads: `conf.py`
  `:61-83` (`APPLY_UPSTREAM_PATCHES_KEY`, `UPSTREAM_PATCH_DEPENDENCIES`),
  `:361-419` (`upstream_patches_enabled` gate + `ValueError` +
  `ConfigurationError` wordings); `views.py:152` (`_JSON_PARSE_REASON` +
  `:140-151` contract comment); `tests/test_views.py:2070-2086` (pin);
  `apps.py:48-56` (dispatch); per-module oracle `match=` lines cited above.

### Gates (own runs, shared project venv via `uv run`)

- `uv run mypy`: `Success: no issues found in 119 source files`.
- `uv run basedpyright`: `0 errors, 0 warnings, 0 notes`.
- `uv run python scripts/check_any.py`: `130 allowed use(s) of Any at 90
  site(s)`.
All three match the run-9 tree-state baseline (119 / 0-0-0 / 130-at-90).
Ruff on touched tracked paths: vacuous (zero-edit; no tracked `.py`
touched, artifact is per-cycle scratch md). No pytest run (not authorized
beyond `workspace.py` proofs; none needed - all proofs static). Slot 1-3
venvs damaged per brief; execution used the shared `.venv` only.

### Reconciliation (post-read: every difference vs `## Findings`)

Census: AGREE - W1's CW1-CW3/DJ1-DJ3/SB1-SB3/GQ1-GQ2 with 3+3+3+2 matches
mine site for site; envelope anatomy (4 displays, 11 unique reasons, 4
keys, 5 tails incl. strawberry's twin tails, CW1's literal-split) matches
my reads (SB2's `(name, argument)` loop, SB1's `supported dependency
versions` vs SB2/SB3's `a supported Strawberry version`, all verified).
Challenges: AGREE - W1 C1 (count 1), C2 (count 0, projections), C3 (count
1, twin-tail proof), C4 (count 0, convention), C5 (count 0, pure addition)
are consistent with my C1-C6; my extra hard-tests (redaction, URL
rotation, error-code prefix, key rename, single-module reword, opt-out
policy) corroborate rather than conflict - none forces count > 1 with a
landable owner. F-WORD: AGREE (all-varying formatter, `conf.py` considered
and rejected under principle 7, four-retirement coupling, triggers (a/b/c)
cover my C6 trigger and add the mechanism-shape trigger (b)). F-LOCAL:
AGREE (strongest shape admitted and still reliefless; strawberry's twin
tails fragment even the within-module frame). R-KEY/R-CONF/R-TEARDOWN/R-400:
AGREE on all four contract differences + triggers; R-TEARDOWN is
consistent with plan row 344 (confirmed fresh, not inherited), R-400's
startup-vs-runtime split is real (`:668,670,747,873,887` verified), and
the e10 watch-site (teardown guard, neither install-refusal nor
lifecycle-template) is homed, not dropped - no wording sub-rule lost
between e10 and this item. Matrix: AGREE on all six axes (mine discharged
identically pre-read); W1's display-name non-derivability note strengthens
axis 3. Enumeration: AGREE - 11/11/10-plus-split/17 counts reproduce mine
(3+4+8+2 raises); cross-medium zero-hits re-verified by me for all three
markers over `tests/`, `examples/`, and the named standing docs (0/0/0).
Oracle completeness: AGREE - my independent samples all land on W1's cited
lines, and dirt-avoidance re-verified (0 `match=`/refusal-test-def diff
lines in the two dirty oracle files). Cells: AGREE - reason stated, and
correct (install-time path reaches no DB/alias/dialect; zero-edit changes
nothing under any cell). Structural gate: AGREE - none owed for a
rejection; negative control n/a. Pending-execution absence: AGREE - proofs
are static-reviewed plus one authorized `--no-cov` execution-witnessed
test; no `proof:` entry remains. Freshness: AGREE - every pin re-verified
by me both states (4/4 module pins both states; `conf.py`, clean
`apps.py`, all four oracle files, `tests/test_views.py`, `views.py` -
exact match, so W1 read the same bytes I did). Twin-tails and CW1-split
examined-and-cleared: AGREE, both corroborated above.

D1: REJECT - factually false, must be struck, not routed. The pin W1 says
does not exist exists at WT `tests/test_views.py:2070` (= HEAD `:2104`)
and does exactly what the comment claims: it raises upstream's live
`parse_json` through `patches._original_parse_json` and asserts BOTH
`excinfo.value.reason == _JSON_PARSE_REASON` and
`patches._UPSTREAM_JSON_PARSE_REASON == _JSON_PARSE_REASON`. Every
alternative of W1's claimed-empty sweep is present in that file at both
states: `_JSON_PARSE_REASON` 13 hits, `UPSTREAM_JSON_PARSE_REASON` 1 hit
(`:2086`; HEAD likewise 1), `against what upstream` 1 hit (`:2071`),
`strawberry_patches` 1 hit (`:81` import) - contra "never mentions either
constant, `strawberry_patches`, or the reason string". Only the bare
reason literal is absent (0 hits), which is correct oracle shape (an
independent oracle reads upstream's live raise, never restates the
literal), not staleness. Probable cause: the sweep ran in literal mode
(pipe-joined pattern as one string finds nothing) - the same trap a first
W2 probe hit and corrected. Knock-on: Matrix axis 1's "D1 below records
that note's stale test pointer" inherits the error. The comment
(`_strawberry_patches.py:484-492`, mirrored accurately at
`views.py:140-151`) is correct; the prescribed fix (re-point at wire
assertions or add the promised pin) would churn a working pin's
documentation. No File `_strawberry_patches.py` routing is owed; Worker-0
should drop the plan's "D1 homing owed" note at closeout.

Verdict driver: D1 alone. The REJECT verdict, zero-edit, all findings,
exclusions, triggers, cells, and gates are endorsed; the artifact's only
flaw is the false defect with its bogus fix shape. W1 sections stay
byte-intact per role rules, so W1 must strike D1 itself: replace it with a
struck note citing this section (keep the freshness pins, which are
correct), and correct the Matrix axis-1 pointer. No production edit is
demanded or needed; re-verify scope is the D1 strike only.

### Re-pass (Worker-2, re-pass; scope: the D1 strike only)

Pass-1 trace above stands untouched. Revision check: D1 is struck in
`## Defects` with a struck note citing this section's `### D1
(own pre-reading)` plus the `D1: REJECT` reconciliation, and the Matrix
axis-1 pointer is corrected (struck inline, pointing at Defects); the
`## Iterations` pass-2 entry is present. Freshness pins retained in the
struck note and still exact: WT `git hash-object` reproduces
`tests/test_views.py` `a1de5141…` and `views.py` `d1ff2aba…` (shared
project venv unused - read-only probes only; slot 1-3 venvs damaged per
brief). Nothing else changed in any verdict-relevant way: section
structure intact, endorsed heads spot-read (census 3+3+3+2, envelope
anatomy, C1-C5, triggers, examined-and-cleared), and every remaining
`D1`/`stale` occurrence is accounted for (struck text, pass-1 trace,
Iterations, or C2's unrelated "stale gate call"). Own spot-read evidence
(WT state, regex mode): the pin
`test_the_wire_reason_is_upstreams_own_parse_json_literal` exists at
`tests/test_views.py:2070`, raises upstream's live `parse_json` via
`patches._original_parse_json`, and asserts both equalities; sweep over
that file gives `_JSON_PARSE_REASON` 13 hits, `UPSTREAM_JSON_PARSE_REASON`
1 (`:2086`), `against what upstream` 1 (`:2071`), `strawberry_patches`
1 (`:81` import), bare literal 0 - reproducing pass-1 W2 exactly, so no
standing disagreement arises. Zero-edit holds: HEAD unmoved at
`5c3496e0`, `git diff ITEM_BASELINE --name-only` names the plan edit
(`docs/dry/dry-0_0_15.md`) alone, and the four indexed-file WT pins
reproduce `16c05c78`/`5ca5493f`/`ec492674`/`2d1dd0cd`. Verdict:
`verified`.

## Iterations

Pass 2 (Worker-1 revision): struck pass-1 D1 as factually false per W2's
correction, verified independently first - the pin test exists at
`tests/test_views.py:2070` (HEAD `:2104`), raises upstream's live
`parse_json`, and asserts both equalities, exactly as the
`_strawberry_patches.py:484-492` comment claims (per-alternative sweep hit
counts reproduce W2's at both states; the pass-1 sweep evidently ran in
literal mode). Struck note cites the W2 section; freshness pins retained
(W2-confirmed correct); Matrix axis-1 pointer corrected. Nothing else in
the artifact changed; no tracked file touched. Status:
`ready-for-verification/2`.
