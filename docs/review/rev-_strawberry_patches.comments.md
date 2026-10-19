# Review · Comments: `django_strawberry_framework/_strawberry_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=f3d32be142a493b44bf522d75471843f2fc86285

## Trace

Read the whole live target (853 lines), the whole own test module
`tests/test_strawberry_patches.py` (747 lines, prose = module docstring +
38 test/class docstrings + 1 inline comment), and every prose passage other
test modules hold about the target's symbols: `tests/test_apps.py`
(dispatch + reload docstrings, module pointers, `_PATCHED_SLOTS`
comment), `tests/test_views.py` (opt-out helper, wire-matrix and
reason-pin docstrings), `tests/test_routers.py` (WebSocket refusal
docstring), `tests/test_cross_web_patches.py` (raw-bytes getter
docstring), `examples/fakeshop/test_query/test_transport_api.py` (spy
mount, both opt-out helpers, wire-contract, cross-web-half, multipart
and async rows), and
`examples/fakeshop/test_query/test_products_api.py` (envelope, shield,
depth and wire-contract rows plus section banners). Followed the trace
out to the package modules that cite the target:
`django_strawberry_framework/apps.py` (`ready` dispatch),
`django_strawberry_framework/conf.py` (joint-ownership comment +
`django_strawberry_framework/conf.py::upstream_patches_enabled`),
`django_strawberry_framework/views.py` (reason comment, shield
comment, ownership section),
`django_strawberry_framework/_cross_web_patches.py` (joint-ownership
and retirement prose),
`django_strawberry_framework/consumers.py` (WebSocket-containment
prose), and `django_strawberry_framework/middleware/request_body.py`
(twin-convention cite only). Verified upstream facts against the
installed third party read statically in `.venv` (strawberry-graphql
0.324.0 `sync_base_view.py` / `async_base_view.py` multipart bodies
and the channels `ws_handler.py` decode seam; no fingerprint),
`docs/GLOSSARY.md` (the `Upstream patches` anchor), `conftest.py`
(depth-probe comment), and `examples/fakeshop/test_query/README.md`
sections 13/15 (historical promotion narrative; docs, out of scope).
Also read the plan, the main artifact skeleton, and both sibling axis
records whole (Performance `no-findings`, Mechanics `no-findings`,
each with its `Handoff:`; neither carries a `## Cross-axis` section,
so no sibling Proof names this axis).

The target is dirty with concurrent work at read time: the live tree
differs from `HEAD` by the `truth` helper migration only
(`truth.class_dict` in
`django_strawberry_framework/_strawberry_patches.py::_captured_upstream_method`
and
`django_strawberry_framework/_strawberry_patches.py::_patch_is_installed`,
plus the import), and `git diff <ITEM_BASELINE> -- <target>` is empty,
so the tree reviewed is the item baseline. No prose hunk is dirty;
every finding below reproduces identically at `HEAD` and at
`ITEM_BASELINE`. The plan's `## Owned changes` holds no row for this
target.

Instruments (all static, shared tree, no package import, no database):
the cut-off pass's `review_inspect.py` orientation kept at
`docs/review/temp-tests/_strawberry_patches/comments/inspect/` and
`docs/review/temp-tests/_strawberry_patches/comments/_strawberry_patches.json`
(blob `2b39199b`, the live text);
`build_tree_md.py --list-docstrings` on the target and the own test
module (both first lines pass);
`check_citations.py --paths ... --substrings --json` on the target (8
`path::Symbol` citations, all resolve) and the own test module (1,
resolves); the REVIEW.md provenance sweep plus pronoun, mood
("Tests that" / "Ensures"), twin-convention, bare-spec and
selector-resolution sweeps (hits adjudicated in `## Findings` and
`## Rejected`); `git log -S` archaeology for staleness direction;
`-k` selector checks against live test names. Database cells:
inapplicable by construction for the whole axis — prose grading
opens no database and reaches no alias or dialect decision; no
`workspace.py` run was made and no run id is owed.

Looks-for discharge (REVIEW.md "Comments"): module first lines (target
+ own tests) pass the instrument; function mood: 3 Low findings (L1-L3),
every other function opens imperative, the async-twin pointer follows
the repo twin convention (R7); test class docstrings are descriptions;
no test docstring begins "Tests that" or "Ensures" (swept, 0 hits); no
source reference by line number anywhere in scope (swept); no public
symbol lacks a docstring (`apply` + module); stated design reasons
checked against bodies (the F-cluster + R17); we/you/I examined (R3);
provenance swept (L5, L6 + R2 keeps).

Fingerprints (`git hash-object`, live tree as read):

- `django_strawberry_framework/_strawberry_patches.py`: 2b39199bb2de42e40ae49d62bd24cc8a7a962c1b
- `tests/test_strawberry_patches.py`: 94a5bfa489029328cda91dff893882bf8fc93e6f
- `tests/test_apps.py`: 5ca8b62c53185343ebfec95315f59ec6104fc851
- `tests/test_views.py`: c542cf1b21c5f275eae171108bdcad0a369afa3d
- `tests/test_routers.py`: 36c962b1a3c8ba8c879e7d89c44bfe17b4a31c71
- `tests/test_cross_web_patches.py`: 70c16389aa5d2a14746dba1612c909263bffd822
- `examples/fakeshop/test_query/test_transport_api.py`: b1681e8c725ceb46a0243c770a7dcd295edefc06
- `examples/fakeshop/test_query/test_products_api.py`: f57d9a0a602ee349316b3346f47102d50c4b81bd
- `examples/fakeshop/test_query/README.md`: 0dbf3a35b92ca8d0f8fe6ad0745d29c06f74daab
- `django_strawberry_framework/consumers.py`: 67887b5be1bc80cfc4f051de54d38fde00396ff3
- `django_strawberry_framework/views.py`: 48ee582ecdba41d49beb2434f2a9e0af992d39d4
- `django_strawberry_framework/_cross_web_patches.py`: 52bf8f5712d632817587f93c4eeb881fd74ffaae
- `django_strawberry_framework/apps.py`: 8ae1a3a3b12f0c9792094959c573ea6fab5d804f
- `django_strawberry_framework/conf.py`: ae3de0a36e2f7737a2c8350e532cdb761b295bcf
- `django_strawberry_framework/middleware/request_body.py`: 3bc5c6730ef70e9e58853a0f03ff62ec9fca8d
- `docs/GLOSSARY.md`: 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd
- `conftest.py`: b625bf0cd063fd59d984850cbd4660a4d3792e81

## Findings

### High

None.

### Medium

#### F1 — module docstring says the shield calls the captured original directly

- Observation: the shield paragraph of the module docstring states the
  two nested GET parses "call the captured `_original_parse_json`
  directly, restoring exact upstream GET semantics". Both claims are
  false today: the shield calls
  `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`,
  and GET semantics are therefore not exact-upstream (a deep param
  meets the shared translator's controlled `400` where upstream
  answers `500`).
- Evidence: the shield body
  (`django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`,
  target lines 689/695) calls `_translated_parse_json`, whose
  docstring names both callers; the shield's own docstring says the
  nested calls "go through `_translated_parse_json`" and the
  recursion half "is real". Direction: pre-`e9ee7af5` the shield
  body called `_original_parse_json` directly (verified at
  `e9ee7af5^`), so the sentence described that body; `e9ee7af5`
  ("fix(transport): reject unparseable and unmeasurable request
  bodies with a 400", 2026-08-25) introduced the shared translator
  and updated the shield docstring but not this paragraph. F2-F5 are
  the same root in four sibling sentences.
- Impact: a reader touching the shield or the translator follows a
  direct-call model that no longer exists, and "exact upstream GET
  semantics" hides the deliberate deep-param hardening — the
  misunderstanding that files the deep-param `400` as a bug or
  "simplifies" the translator away.
- Severity: Medium (stale docstring on an internal symbol; the module
  is private and the GLOSSARY anchor documents the consumer contract,
  which this sentence does not state).
- Recommendation: name the translator and the error channel it keeps.
- Must not change: n/a (Comments).
- Proof: `grep -c 'captured ``_original_parse_json`` directly' django_strawberry_framework/_strawberry_patches.py` prints `0`; the rewritten paragraph earns grade true (it routes the nested parses through the shared translator and no longer claims exact-upstream semantics).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_strawberry_patches.py` module docstring, shield paragraph.
- Grade: stale.
- Text-before:
  `of upstream's ``parse_query_params`` whose two nested parses call the`
  `captured ``_original_parse_json`` directly, restoring exact upstream`
  `GET semantics while the wrapper keeps hardening the seven`
- Text-after:
  `of upstream's ``parse_query_params`` whose two nested parses call`
  `:func:`_translated_parse_json`, keeping the envelope guard off the GET`
  `path while the shared translator still owns gap 1's error channel;`
  `upstream's per-param handling keeps ownership of validity there while`
  `the wrapper keeps hardening the seven`

#### F2 — `_patched_parse_json` docstring routes the shield through the captured original

- Observation: the guard-coverage paragraph says the GET sites are
  kept off "which `_patched_parse_query_params` routes through the
  captured original". The shield routes them through
  `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`.
- Evidence: same body and direction as F1 (shield lines 689/695;
  true pre-`e9ee7af5`, stale since).
- Impact: same wrong wiring model as F1, on the docstring a reader
  opens to learn where the guard does and does not fire.
- Severity: Medium (stale docstring on an internal symbol).
- Recommendation: name the shared translator instead of the captured original.
- Must not change: n/a (Comments).
- Proof: `grep -c 'routes through the captured original' django_strawberry_framework/_strawberry_patches.py` prints `0`; the rewritten paragraph earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json`.
- Grade: stale.
- Text-before:
  ```parse_query_params``, which :func:`_patched_parse_query_params``
  `routes through the captured original so upstream's own per-param`
  `handling keeps ownership there.`
- Text-after:
  ```parse_query_params``, which :func:`_patched_parse_query_params``
  `routes through the shared translator instead of the guard, so upstream's`
  `own per-param handling keeps ownership of validity there.`

#### F3 — own test module docstring routes the shield through the captured original

- Observation: the test module docstring describes the shield as
  "routing its two nested parses through the captured original
  `parse_json`". Same false mechanism as F1/F2.
- Evidence: same body and direction (the sentence is byte-identical
  at `e9ee7af5^`, line 38; the body it described changed under it).
- Impact: a reader learning the suite's organization is taught the
  pre-translator wiring; the sentence sits two paragraphs above the
  coverage map that must send them to the right tier.
- Severity: Medium (stale wiring claim in the target's own test module).
- Recommendation: route the sentence through the shared translator.
- Must not change: n/a (Comments).
- Proof: `grep -c 'the captured original ``parse_json``' tests/test_strawberry_patches.py` prints `0`; the rewritten sentence earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_strawberry_patches.py` module docstring, shield paragraph.
- Grade: stale.
- Text-before:
  `of ``BaseView.parse_query_params`` routing its two nested parses through`
  `the captured original ``parse_json`` - so the guard never fires on`
- Text-after:
  `of ``BaseView.parse_query_params`` routing its two nested parses around`
  `the guard through the shared gap-1 translator - so the guard never fires on`

#### F4 — live object-variables row repeats the captured-original wiring

- Observation: `test_get_query_with_object_variables_executes_like_upstream`
  says "the shield's two nested parses still route through the
  captured original `parse_json` rather than the envelope guard".
  They route through the shared translator, around the guard.
- Evidence: same shield body as F1. Direction differs: the sentence
  landed in `18f2446f` ("test: promote package-only rows to live
  /graphql coverage", 2026-09-12), after `e9ee7af5` (2026-08-25) —
  born-false, copying the stale framing of F1-F3 into the new live
  row.
- Impact: the live tier is the authoritative pin of shield behavior;
  its docstring teaches wiring the body never had at this tier's
  birth.
- Severity: Medium (stale behavioral claim in test prose about the target's symbol).
- Recommendation: route the sentence around the guard through the translator.
- Must not change: n/a (Comments).
- Proof: `grep -c 'still route through the captured original' examples/fakeshop/test_query/test_products_api.py` prints `0`; the rewritten docstring earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `examples/fakeshop/test_query/test_products_api.py::test_get_query_with_object_variables_executes_like_upstream`.
- Grade: stale.
- Text-before:
  `shield's two nested parses still route through the captured original`
  ``parse_json` rather than the envelope guard: a shield that stopped parsing (or`
- Text-after:
  `shield's two nested parses still route around the envelope guard through`
  `the shared gap-1 translator: a shield that stopped parsing (or`

#### F5 — live malformed-param row denies the shield's error handling

- Observation: `test_get_query_with_malformed_variables_param_is_the_upstream_parse_400`
  opens "The shield adds no error handling of its own: the failure
  is raised inside the delegated original `parse_json`". The
  shielded path translates deep-param `RecursionError` escapes to
  the controlled `400` via the shared translator — error handling
  beyond upstream's, pinned by the adjacent deep-param row ("it
  shares gap 1's error channel"), which this sentence contradicts.
- Evidence: shield body routes through
  `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`
  (F1); the deep-param live row asserts the translated `400` on the
  shielded path. Born-false in `18f2446f` like F4: true only of the
  pre-`e9ee7af5` direct-call shield.
- Impact: two adjacent live rows teach opposite contracts about the
  same path; a reader trusting this sentence reads the deep-param
  `400` as upstream behavior and the translator as dead weight on
  GET.
- Severity: Medium (stale behavioral claim in test prose about the target's symbol).
- Recommendation: scope the transparency claim to the envelope guard
  and route the delegation via the translator.
- Must not change: n/a (Comments).
- Proof: `grep -c 'adds no error handling of its own' examples/fakeshop/test_query/test_products_api.py` prints `0`; the rewritten docstring earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `examples/fakeshop/test_query/test_products_api.py::test_get_query_with_malformed_variables_param_is_the_upstream_parse_400`.
- Grade: stale.
- Text-before:
  `The shield adds no error handling of its own: the failure is raised inside the`
  `delegated original `parse_json`, so an unparseable GET param answers with the`
- Text-after:
  `The shield adds no envelope guard of its own: the failure is raised inside the`
  `delegated original `parse_json` via the shared gap-1 translator, so an`

#### F6 — views opt-out helper claims the exact opted-out state while two delegates stay installed

- Observation: `tests/test_views.py::_strawberry_patch_opted_out`
  closes "What is left running is exactly what a consumer who opted
  out would be running." The helper restores only the `BaseView`
  pair; the sync/async multipart delegates stay installed. A genuine
  opted-out consumer (whose `apply()` no-op'd from the start) runs
  none of the four members, so for any multipart request the states
  observably differ.
- Evidence: the helper body saves and restores `parse_json` and
  `parse_query_params` only; the multipart slots are untouched, and
  the delegates consult no setting once installed. Direction: the
  "exactly" sentence predates the delegates (present at
  `18550f5d^`, when the patch was the pair and the sentence was
  true); `18550f5d` (2026-08-16) added
  `django_strawberry_framework/_strawberry_patches.py::_patched_sync_parse_multipart`
  and its async twin without updating it. The rows using the helper
  never post multipart, so only the claim is wrong, not the rows.
- Impact: a reader auditing patch state inside the block is told no
  member runs; two do. The sentence also teaches that the patch has
  two members.
- Severity: Medium (stale behavioral claim in test prose about the target's symbols).
- Recommendation: scope the "exactly" to the JSON-body path the rows
  exercise and name the still-installed delegates.
- Must not change: n/a (Comments).
- Proof: `grep -c 'exactly what a consumer who opted out would' tests/test_views.py` prints `0`; the rewritten docstring earns grade true (it states the pair is restored, the delegates stay installed and unreachable here).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_views.py::_strawberry_patch_opted_out`.
- Grade: stale.
- Text-before:
  `duration. What is left running is exactly what a consumer who opted out would`
  `be running.`
- Text-after:
  `duration. The two multipart delegates stay installed: no row in`
  `this block posts multipart, so they are unreachable here, and what the rows`
  `observe is exactly what an opted-out consumer observes on the JSON-body path.`

#### F7 — live opt-out helper makes the same exact-state overclaim

- Observation: the `test_transport_api.py` twin of F6's helper
  closes "what remains running is exactly what an opted-out
  consumer runs", while likewise restoring only the `BaseView`
  pair and leaving both multipart delegates installed.
- Evidence: same as F6 (helper body restores two slots; sentence
  present at `18550f5d^`; delegates arrived in `18550f5d`; no
  using row posts multipart).
- Impact: same as F6, on the live tier's canonical opt-out
  simulation.
- Severity: Medium (stale behavioral claim in test prose about the target's symbols).
- Recommendation: same as F6.
- Must not change: n/a (Comments).
- Proof: `grep -c 'exactly what an opted-out consumer runs' examples/fakeshop/test_query/test_transport_api.py` prints `0`; the rewritten docstring earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `examples/fakeshop/test_query/test_transport_api.py::_strawberry_patch_opted_out`.
- Grade: stale.
- Text-before:
  `block stays a no-op and what remains running is exactly what an opted-out consumer runs.`
- Text-after:
  `block stays a no-op. The two multipart delegates stay installed: no row in`
  `this block posts multipart, so they are unreachable here, and what the rows`
  `observe is exactly what an opted-out consumer observes on the JSON-body path.`

#### F8 — "the latest release" currency claim aged past the installed 0.324.0

- Observation: "Upstream status" opens "Unfixed upstream as of
  `strawberry-graphql` 0.317.2 (the latest release) and `main`
  (checked 2026-06-18)." 0.317.2 is no longer the latest release;
  the installed upstream is 0.324.0.
- Evidence: installed strawberry-graphql is 0.324.0; the Mechanics
  record re-verified every gap still present there, so only the
  parenthetical is stale, not the substance (its Handoff names this
  exact sentence). The dated audit remainder ("0.317.2 and `main`
  (checked 2026-06-18)") stays true as history.
- Impact: a reader checking retirement is told the audit is current;
  it is two minor versions behind.
- Severity: Medium (stale currency claim on internal prose).
- Recommendation: drop the parenthetical; the dated audit note
  carries the fact.
- Must not change: n/a (Comments).
- Proof: `grep -c '(the latest$' django_strawberry_framework/_strawberry_patches.py` prints `0`; the rewritten sentence earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_strawberry_patches.py` module docstring, Upstream status.
- Grade: stale.
- Text-before:
  `Unfixed upstream as of ``strawberry-graphql`` 0.317.2 (the latest`
  `release) and ``main`` (checked 2026-06-18).`
- Text-after:
  `Unfixed upstream as of ``strawberry-graphql`` 0.317.2 and ``main```
  `(checked 2026-06-18).`

#### F9 — own test module's gap-1 summary omits the RecursionError half

- Observation: the module docstring's gap-1 paragraph summarizes the
  translation as `UnicodeDecodeError`-only ("The wrapper translates
  it into the same `HTTPException(400, ...)`"). Gap 1 is two
  escapes: the wrapper equally translates `RecursionError`, with
  dedicated `__cause__` rows in this file.
- Evidence: the translator body catches both; this file pins both
  causes. Direction: the paragraph is byte-identical at
  `e9ee7af5^`, where the body translated only `UnicodeDecodeError`
  (the `UnicodeDecodeError`-only era runs `c7cb5f5c` through
  `e9ee7af5^`); `e9ee7af5` added the second escape without updating
  the summary.
- Impact: the paragraph teaches gap 1 as one escape; the file's own
  depth rows then look scope-less.
- Severity: Medium (stale summary in the target's own test module).
- Recommendation: name both escapes in the summary.
- Must not change: n/a (Comments).
- Proof: `grep -c 'The wrapper translates it' tests/test_strawberry_patches.py` prints `0`; the rewritten paragraph earns grade true (it names both translated escapes).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_strawberry_patches.py` module docstring, gap-1 paragraph.
- Grade: stale.
- Text-before:
  `upstream's ``except`` and becomes a ``500``. The wrapper translates it`
  `into the same ``HTTPException(400, ...)`` Strawberry already raises for`
- Text-after:
  `upstream's ``except`` and becomes a ``500``; a pathologically nested`
  `document likewise escapes as ``RecursionError``. The wrapper translates`
  `both into the same ``HTTPException(400, ...)`` Strawberry already raises for`

#### F10 — own test module's rows-inventory omits the RecursionError-cause rows

- Observation: the coverage-map paragraph inventories "the rows
  here" and names only "the `UnicodeDecodeError` `__cause__` a
  live JSON 400 cannot isolate". This file equally pins the
  `RecursionError` `__cause__` (nested-body and deep-param rows),
  which no live row isolates either — the live deep rows assert
  status and body only.
- Evidence: `test_patched_parse_json_translates_a_pathologically_nested_body`
  and `test_patched_parse_query_params_translates_a_deep_param`
  assert `type(...__cause__) is RecursionError`; the live twins
  assert no cause. Direction: the inventory predates `e9ee7af5`,
  which added the depth rows.
- Impact: the docstring's own organizing principle (wire-observable
  pins live; non-isolable pins here) sends a reader looking
  live-ward for cause pins that exist only here.
- Severity: Medium (stale inventory in the target's own test module).
- Recommendation: extend the cause clause to both escapes.
- Must not change: n/a (Comments).
- Proof: `grep -c 'validator), the UnicodeDecodeError' tests/test_strawberry_patches.py` prints `0`; the rewritten inventory earns grade true (it names both causes).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_strawberry_patches.py` module docstring, coverage-map paragraph.
- Grade: stale.
- Text-before:
  `validator), the UnicodeDecodeError ``__cause__`` a live JSON 400 cannot`
  `isolate from the view's own decode, multipart structural vs`
- Text-after:
  `validator), the UnicodeDecodeError and RecursionError ``__cause__`` values`
  `a live JSON 400 cannot isolate from the view's own decode, multipart structural vs`

### Low

#### L1 — `_translated_parse_json` first line is a description, not an imperative

- Observation: the function docstring opens "The captured original
  plus the raises its `except` lets escape as 500s.", a noun phrase.
  The axis requires the imperative mood for functions ("Return ...");
  ruff leaves D401 unchecked, so the reviewer is the gate. Every
  sibling opener except L2/L3 is imperative.
- Evidence: first line of
  `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`;
  contrast the imperative opens of `_captured_upstream_method`,
  `_validate_upstream_shape`, `_raised_inside_the_upload_utility`,
  `_patched_sync_parse_multipart`, `_mark_patch_replacement`,
  `_patch_is_installed`, `apply`.
- Impact: bounded clarity; the summary states what the object is
  rather than what it does.
- Severity: Low.
- Recommendation: open with the behavior the body implements.
- Must not change: n/a (Comments).
- Proof: `grep -c 'The captured original plus the raises' django_strawberry_framework/_strawberry_patches.py` prints `0`; the rewritten first line earns grade true (imperative, states the delegate-and-translate behavior).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json`.
- Grade: duplicates the code (states the object's role, which the name plus the second paragraph already establish, instead of its behavior).
- Text-before:
  `The captured original plus the raises its ``except`` lets escape as 500s.`
- Text-after:
  `Return the captured original's result, translating the raises its ``except`` lets escape as 500s.`

#### L2 — `_patched_parse_json` first line is a description, not an imperative

- Observation: the function docstring opens "Wrapper around
  `BaseView.parse_json` closing two upstream gaps.", a noun phrase
  (same mood defect as L1).
- Evidence: first line of
  `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json`.
- Impact: bounded clarity.
- Severity: Low.
- Recommendation: open with the hardening behavior.
- Must not change: n/a (Comments).
- Proof: `grep -c 'Wrapper around ``BaseView.parse_json`` closing two upstream gaps' django_strawberry_framework/_strawberry_patches.py` prints `0`; the rewritten first line earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json`.
- Grade: duplicates the code (states the object's role instead of its behavior).
- Text-before:
  `Wrapper around ``BaseView.parse_json`` closing two upstream gaps.`
- Text-after:
  `Harden ``BaseView.parse_json`` against two upstream gaps.`

#### L3 — `_patched_parse_query_params` first line is a description, not an imperative

- Observation: the function docstring opens "Source-pinned
  reimplementation of `BaseView.parse_query_params`.", a noun phrase
  (same mood defect as L1/L2).
- Evidence: first line of
  `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`.
- Impact: bounded clarity.
- Severity: Low.
- Recommendation: open with the reimplement-and-route behavior.
- Must not change: n/a (Comments).
- Proof: `grep -c 'Source-pinned reimplementation of ``BaseView.parse_query_params``' django_strawberry_framework/_strawberry_patches.py` prints `0`; the rewritten first line earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`.
- Grade: duplicates the code (states the object's role instead of its behavior).
- Text-before:
  `Source-pinned reimplementation of ``BaseView.parse_query_params``.`
- Text-after:
  `Reimplement ``BaseView.parse_query_params`` with the nested parses routed around the envelope guard.`

#### L4 — coverage-map sentence equates a request body with a test file

- Observation: "The POST body `{not json` is
  `examples/fakeshop/test_query/test_transport_api.py`." The sentence
  is missing its verb: a request body cannot *be* a test file. The
  pointer target exists (the `{not json` POST row at
  `examples/fakeshop/test_query/test_transport_api.py:1424`), so only
  the sentence is broken. Born-garbled in `a01a2ab8`.
- Evidence: the sentence as quoted; the target row exists and asserts
  upstream's parse `400` on a POST body.
- Impact: bounded clarity; the coverage map's one transport-api
  pointer is ungrammatical.
- Severity: Low.
- Recommendation: give the pointer its verb.
- Must not change: n/a (Comments).
- Proof: `grep -c 'The POST body ``{not json`` is' tests/test_strawberry_patches.py` prints `0`; the rewritten sentence earns grade true (it points at the live row with a verb).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_strawberry_patches.py` module docstring, coverage-map paragraph.
- Grade: stale (born-false equation of a body with a file).
- Text-before:
  `The POST body ``{not json`` is`
  ```examples/fakeshop/test_query/test_transport_api.py``.`
- Text-after:
  `The POST-body ``{not json`` row lives in`
  ```examples/fakeshop/test_query/test_transport_api.py``.`

#### L5 — bare `(spec-046)` parenthetical is process provenance

- Observation: the ownership-split live row carries "the deliberate
  scope of the ownership split (spec-046)". A bare `(spec-NNN)` is
  process provenance; the kept form is a spec Decision pointer, and
  Decision 9 is the decision this sentence means. The only bare
  `(spec-0NNN)` in the file (census-verified).
- Evidence: the sentence states the rule fully; the parenthetical
  adds only vehicle attribution. Every other spec pointer in scope
  names Decision 9 or 10.
- Impact: bounded precision; a bare spec number points at a whole
  spec where a Decision points at the rationale.
- Severity: Low.
- Recommendation: name the Decision.
- Must not change: n/a (Comments).
- Proof: `grep -c '(spec-046)' examples/fakeshop/test_query/test_transport_api.py` prints `0`; the rewritten parenthetical earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `examples/fakeshop/test_query/test_transport_api.py::test_the_utf8_wire_contract_survives_the_upstream_patch_kill_switch`.
- Grade: process provenance.
- Text-before:
  `the deliberate scope of the ownership split (spec-046), pinned`
- Text-after:
  `the deliberate scope of the ownership split (spec-046 Decision 9), pinned`

#### L6 — "Before spec-046" dates behavior by vehicle instead of rule

- Observation: the UTF-16 live row opens its history "Before
  spec-046 this request *succeeded*". The spec number dates the
  behavior change by vehicle; the kept form names the rule (the
  wire contract, Decision 9 — cited properly in the next
  paragraph).
- Evidence: the sentence's mechanism ("the cross_web patch handed
  the raw bytes...") is true history; only the "Before spec-046"
  anchor is provenance.
- Impact: bounded precision, same as L5.
- Severity: Low.
- Recommendation: anchor the contrast on the rule, keeping the Decision pointer.
- Must not change: n/a (Comments).
- Proof: `grep -c 'Before spec-046 this request' examples/fakeshop/test_query/test_products_api.py` prints `0`; the rewritten anchor earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `examples/fakeshop/test_query/test_products_api.py::test_post_utf16_json_body_is_rejected_as_400`.
- Grade: process provenance.
- Text-before:
  `The history is the point of keeping this row. Before spec-046 this request`
- Text-after:
  `The history is the point of keeping this row. Before the wire contract (spec-046 Decision 9) this request`

## Rejected

- R1 — "no longer" (`_validate_upstream_shape` first line, both drift
  error strings): present-tense shape-drift claims, true in each case
  (a reshaped upstream raises exactly these). Follows the
  `_django_patches.py` Comments R1 precedent. Trigger: wording that
  dates the change itself.
- R2 — past-tense mechanism narratives ("It used to live in this
  function", "Two owners now", "previously escaped ... and now gets",
  "previously-uncaught", "has no live diagnostic any more",
  "previously 400'd", "used to live inside", "used to escape",
  "now owned by the view", "pre-fix this escaped"): each carries the
  mechanism or behavior contrast the reader needs and names no
  change vehicle (no card, round, worker, commit). Follows the
  `_django_patches.py` Comments R6 precedent. Trigger: naming the
  vehicle that made the change.
- R3 — "we" / "you" / "our" ("the method shapes we patch", "our
  replacement(s)", "You do not need to redo the research", "so you
  can exercise each gap"): examined; idiomatic possessives and
  direct how-to address with no impact beyond preference (the
  "our"-forms distinguish package code from upstream's, which is
  load-bearing clarity). The verifier's "no we" governs prose
  Worker-2 writes, not these lines. Trigger: a reading under which
  one of them misattributes ownership.
- R4 — "~150 KB body on this interpreter" (module + translator
  docstrings): illustrative figure corroborated by `conftest.py`'s
  macOS measurement (74k depth, two bytes per level); platform
  variance is owned and documented at the probe site, and
  duplicating its table in two docstrings would create a second
  owner. Trigger: the figure asserted as universal, or the macOS
  figure moving.
- R5 — "0.316.0" audit pins ("the installed 0.316.0 package",
  "verbatim at strawberry-graphql 0.316.0", "dead code at 0.316.0"):
  dated version pins, true as history, and the Mechanics record
  re-verified every pinned substance (dead-code site, shield
  source) still holds at 0.324.0. Only F8's parenthetical claims
  present currency. Trigger: re-audit at a newer upstream, at which
  point the pins move together.
- R6 — site counts ("seven body/multipart sites" x2, "nine call
  sites", "nine in total ... eight reachable"): consistent
  arithmetic (9 = 7 non-GET including 1 dead + 2 GET), and the
  Mechanics record verified the nine-site inventory plus the
  dead-code site at 0.324.0. Trigger: an upstream call-site change.
- R7 — `_patched_async_parse_multipart` one-line twin pointer
  ("Async twin of ..."): the repo's established twin convention
  (`django_strawberry_framework/middleware/request_body.py:171` has
  the same shape); the sync docstring carries the imperative
  contract, and forcing mood here would duplicate it. Trigger: the
  twins diverging beyond the `await`.
- R8 — `_django_patches._AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`
  dotted ref: resolves (the symbol exists), Sphinx-short-form,
  ungated; follows the `_django_patches.py` Comments R9 precedent.
  Trigger: the audited set being renamed.
- R9 — Sphinx `:mod:` / `:meth:` / `:func:` roles throughout:
  ungated, and every named symbol resolves today; `path::Symbol`
  citations check 8/8 on the target and 1/1 on the own tests. No
  line-number reference anywhere in scope (swept). Trigger: a cited
  symbol being renamed.
- R10 — "It used to live in this function" naming no function: the
  section context plus the `_patched_parse_json` "used to live
  here" line resolve it within two paragraphs; not worth churn.
  Trigger: a reader misattributing the prior site.
- R11 — "while the patch is off" in-row shorthand (wire-contract
  live row): scoped reading covered by F7's fix; the row posts no
  multipart. Trigger: a multipart row using the opt-out helper.
- R12 — `tests/test_apps.py` prose (live-row pointers, dispatch and
  reload-test docstrings, `_PATCHED_SLOTS` comment): every pointer
  resolves and every contract stated matches the bodies (the
  "installed at collection via `ready()`" masking analysis is
  exact). Trigger: a dispatch line or slot changing.
- R13 — WebSocket prose (`consumers.py` module + containment
  docstrings, `test_routers.py` refusal docstring): true —
  installed `ws_handler.py` iterates `view.decode_json` inside
  `iter_json` and never enters `parse_json`, so the HTTP-tier
  translation is correctly out of scope there. Trigger: upstream
  routing socket frames through `parse_json`.
- R14 — `views.py` prose about the target (reason comment, shield
  comment, ownership section): true; the reason duplication and the
  lifecycle split match the Mechanics R2/R3 contracts and their
  pins. Trigger: a reason rewording (fails the pin loud first).
- R15 — `_cross_web_patches.py` prose about the target (joint
  ownership, translation routing, installed/not-installed states,
  retirement): true against the bodies and the live
  cross-web-half row. Trigger: either half's behavior changing.
- R16 — `apps.py`, `conf.py` and GLOSSARY prose (four-module
  dispatch, gate shapes, joint ownership, `Upstream patches`
  anchor): true; the "request-hardening" looseness in
  `upstream_patches_enabled` concurs with the `_graphql_core_patches`
  Comments R6 rejection. Trigger: a fifth patch module or a gate
  reshape.
- R17 — "the patch's original `UnicodeDecodeError`-only widening"
  and "used to escape ... was not installed" (live depth rows):
  true history — the `UnicodeDecodeError`-only era runs `c7cb5f5c`
  through `e9ee7af5^`, and the pre-`e9ee7af5` shield called the
  original directly. Mechanism narrative, no vehicle named.
  Trigger: evidence either shape never existed.
- R18 — re-check commands and probe snippet (`-k non_object`, `-k
  multipart_map`, the `_original_parse_json` probe): both selectors
  match their rows (2 + 2 tests by name), the cited test names
  exist, and the probe's invalid byte drives the documented
  `UnicodeDecodeError` arm. Trigger: a row rename (the `-k`
  strings would select nothing).
- R19 — `except ImportError` pragma wording ("exercised via
  monkeypatch in tests"): true, and byte-consistent with the
  fixed sibling wording (`_graphql_core_patches` F1). Trigger: a
  test-mechanism change.
- R20 — "# `apply()` raised during validation, before the install
  step" (drift-test comment): states where the raise happened,
  which the following `is False` assert does not; intent, not
  duplication. Trigger: none in scope.
- R21 — multipart-reason comment ("the async view already uses this
  reason ..."): true, pinned against the native raise by
  `test_the_multipart_reason_is_upstreams_own_native_literal`.
  Trigger: an upstream rewording (fails the pin loud first).
- R22 — traversal-errors comment ("the utility's own logic is
  iterative ... never wears its frame"): true — the utility takes
  no callbacks, and the Mechanics probe pinned the helper
  True-inside / False-outside. Trigger: the utility gaining a
  callback seam.
- R23 — "pair" wording for the `BaseView` duo (partial-revert test
  name, "the patch pair un-installed"): accurate scope — the
  guard/shield pair is a genuine unit distinct from the four-member
  install. Trigger: the shield gaining an independent lifecycle.
- R24 — spy-mount, section-banner, multipart and async-row prose
  (live tier): every chain, count and attribution verified true
  against the MRO, the constants and the bodies. Trigger: a chain
  reordering.
- R25 — `test_cross_web_patches.py` translation pointer ("inside a
  `parse_json` that can translate it") plus its two live pointers:
  true, both rows exist. Trigger: a behavior move off `parse_json`.

## Cross-axis

None. Every behavioral claim checked against a body held; the
stale sentences misdescribe wiring the bodies implement correctly,
and the two "exactly" overclaims sit on rows whose outcomes equal
true-opt-out outcomes (no using row posts multipart), so no
Mechanics defect rides with them. No performance observation: the
hot-path prose (single parse, no re-parse, shield routing) matches
the Performance record's measured shapes.

Handoff: I graded the live tree (target hash `2b39199b`; the
concurrent `truth`-migration dirt touches code only, no prose) and
found 10 Mediums and 6 Lows. Two commits explain nearly all of it:
`e9ee7af5` (2026-08-25) introduced the shared translator and the
second escape but updated only the shield docstring, stranding F1-F5
plus F9/F10; `18550f5d` (2026-08-16) added the multipart delegates
without updating the two "exactly" helpers (F6/F7). The live-tier
F4/F5 were born-false in `18f2446f` (2026-09-12), copying the
already-stale framing. Everything else is unusually clean: the
nine-site inventory, the lifecycle split, the joint-ownership and
reason-duplication contracts, and every test pointer verified true,
several against installed upstream read statically. Facts for later
passes: (1) F10 and L4 share one paragraph but distinct sentences
with independent Proofs; (2) no finding moves a module first line,
so no TREE.md render is owed; (3) all text-afters avoid "we" per
the verifier's diff check; (4) zero Routed leads — every
other-package-module passage graded true; (5) the README promotion
narrative (sections 13/15) was read and is docs, out of scope. No
open threads beyond the sixteen findings.

## Verification (Comments)

Pass 1. Implement landed prose-only hunks for all 16 findings
(F1-F10 + L1-L6) across 5 files; Performance and Mechanics closed
no-findings, so no code hunk exists on any axis.

Ordering note: the required reading (plan, artifact, all three axis
records) was done up front, so the Worker-2 sections were read
before Verify step 1's hash check completed. The pre-read obligation
was near-vacuous: this record's 16 Proofs are static `grep -c`
commands with fixed expected outputs, and no record carries a
`## Cross-axis (for Comments)` section (Performance and Mechanics
have none; this record's reads `None`), so no expectation-setting
run existed whose result a read could shape. The hash check then
passed, so the read order cannot have affected the verdict.

Checks and results:

1. Item-diff identity (Verify step 1): `git diff
   f3d32be142a493b44bf522d75471843f2fc86285 -- <the five touched
   paths>` is byte-identical to
   `docs/review/temp-tests/_strawberry_patches/diff/pass-1.diff`
   (`sha256:210d05598a2aff7f2a007763876a3e1a4e00edd3a8adb30d459e40
   93a6fd4e23` both sides, 12095 bytes, `cmp` silent). The tree did
   not move under the pass.
2. Proof lines: all 16 run verbatim in the shared tree (static
   commands per REVIEW.md "Worker-1 verifies"; nothing here imports
   the package or opens a database, so no address run was made).
   Every one prints `0` (exit 1 throughout, grep's no-match status,
   expected): F1, F2, F8, L1, L2, L3 on the target; F3, F9, F10, L4
   on `tests/test_strawberry_patches.py`; F6 on `tests/test_views.py`;
   F4, F5, L6 on `test_products_api.py`; F7, L5 on
   `test_transport_api.py`. No Cross-axis Proof for this axis exists
   anywhere. L5's BRE pattern `(spec-046)` matches the literal bare
   form only, so the kept `(spec-046 Decision 9)` correctly prints 0.
3. Grades, each as the whole docstring the changed lines sit in
   (what landed, including the two judgment calls): all 16 true.
   - F1 (module shield paragraph): the nested parses call
     `:func:`_translated_parse_json`` (shield body lines 691/697),
     the guard stays off the GET path, the translator owns gap 1's
     error channel, per-param validity stays upstream's, and the
     "seven body/multipart sites" continuation keeps the verified
     9 = 7 + 2 inventory. The Sphinx `:func:` role matches the
     docstring's existing unqualified usage.
   - F8 (Upstream status): the dated audit note stands as history;
     Mechanics re-verified every gap present at 0.324.0, so only
     the parenthetical was stale. No other currency claim in the
     module docstring names "latest".
   - L1/L2/L3 (three function first lines): imperative mood, each
     stating its body's behavior (delegate-and-translate, harden
     against two gaps, reimplement routing around the guard).
   - F2 (guard-coverage paragraph): routes through the shared
     translator instead of the guard; the "Both views inherit ..."
     continuation stays grammatical on its 91-char line.
   - F3/F9 (own-test shield sentence, gap-1 summary): translator
     routing and both escapes named; the file's depth rows now
     read as in-scope.
   - F10 (cause inventory, reworded): "the ``__cause__`` values for
     UnicodeDecodeError and RecursionError [that] a live JSON 400
     cannot isolate" names both causes and stays grammatical. The
     record's text-after would have kept its own Proof printing 1
     (Worker-2 verified this before repairing); the governing
     Proof forced the rewording, which prints 0. Upheld.
   - L4 (coverage pointer): "row lives in" gives the pointer its
     verb; the target row exists.
   - F5 (malformed-param row, reflowed): "no envelope guard of its
     own" plus "via the shared gap-1 translator" resolves the
     contradiction with the adjacent deep-param row; the restored
     "same body" clause is wire-true (attack 2); the reflowed
     closing sentence is the same sentence, grammatical. Upheld.
   - F4 (object-variables row): translator routing, consistent
     with F5's fixed twin.
   - F6/F7 (both opt-out helpers): pair restored, delegates named
     as installed-but-unreachable, the "exactly" scoped to the
     JSON-body path the rows exercise (attack 4). The
     `tests/test_views.py` helper's descriptive first line is
     pre-existing prose the change did not make false: not graded,
     not a gap.
   - L5/L6 (Decision pointer, wire-contract anchor): kept
     `(spec-046 Decision 9)` form both sites; the L6 history
     mechanism was already true.
4. Instruments: `build_tree_md.py --list-docstrings` on all five
   files passes (5 modules, 0 breaking, exit 0);
   `check_citations.py --paths <five> --substrings` resolves 39/39
   with 0 violations and 0 warnings; `review_inspect.py
   --code-digest f3d32be1...:<path> <path>` exits 0 with equal
   digests on all five (`6d124535...6f4b61e`,
   `9cd25a75...2a220ca`, `98eeaeb6...6d7ad0ec`,
   `c4bc802f...6d7ee`, `f282ed6d...1963b3d`), matching every digest
   Worker-2 claimed — direct baseline comparison, since no other
   axis changed code in these files. Full output kept at
   `docs/review/temp-tests/_strawberry_patches/verify-comments-1/code-digests.txt`.
5. Diff read whole through this axis (15 hunks, 5 files, +36/-29):
   every hunk sits inside a docstring; no module first line changed
   (first hunks start at target:177, products:3138, transport:1800,
   own tests:10, views:1938), so no TREE.md render is owed and none
   is in the diff. Added-line sweeps: no process provenance (the two
   `spec-` hits are the kept Decision-pointer form; the `round` hits
   are "around" substrings), no line-number citation, no standalone
   `we` / `you` / `I`. Added lines over 99 chars: L1 104, L3 107,
   L6 109 — all inside the 110 E501 grace, and the four lint gates
   already ran green on these bytes (Mechanics verification).
6. Attacks on the landed prose, all passing:
   - F10 inventory: the own module asserts
     `type(...__cause__) is UnicodeDecodeError` (line 180) and
     `is RecursionError` twice (lines 694/715: nested body, deep
     param); the live tier asserts `__cause__` nowhere (its two
     mentions are docstring prose).
   - F5 same-body: the GET row asserts
     `b"Unable to parse request body as JSON"`, byte-identical to
     five POST-body rows across both live files.
   - Residual "captured original" in scope: 4 hits, each a true
     distinct sense (the new L1 line; validation/drift prose
     about the captured source). No stale wiring remains.
   - Residual bare-spec/latest: no `(spec-046)` bare, no "latest
     release". Other bare specs in `test_products_api.py`
     (spec-033/034/043) are pre-existing, about other features, in
     symbols this item did not touch: remarked in the Handoff, not
     a gap.
   - F6/F7 premise, independently: all four
     `with _strawberry_patch_opted_out():` blocks post JSON bytes
     only (`view.parse_json(body)`, `_post_bytes`); the one
     "multipart" token within 60 lines of `tests/test_views.py:2011`
     is the next test's docstring prose, outside the block. Concurs
     with the Mechanics verifier's attack.
7. Disputes: none recorded (`grep -c 'disputed:'` on the main
   artifact prints 0); nothing to judge. The two judgment calls
   (F5 reflow, F10 rewording) are dispositions with reasons, both
   upheld above.
8. Sibling verifiers: Performance Verification routes nothing
   ("Nothing routes elsewhere"); Mechanics Verification routes
   nothing and assigns the F8 parenthetical's truth grade to this
   axis (graded true in 3). No gap rides to Comments.
9. Cells: `sharded` and `pg` inapplicable by construction — prose
   grading opens no database and reaches no alias or dialect
   decision; concur with the record's stated reason. No
   `workspace.py` run was made and no run id is owed. Cells
   unverified: none.

No new problem on this axis; no `verify 1` finding; no gap for
`## Decisions`; nothing routes to another item.

Fingerprints (`git hash-object`, live tree as verified): target
`90f711fb420b8902434406735c2e367f011e4177`, own tests
`c06add916e033bd1e8e43211541d21bb1619ab14`, `tests/test_views.py`
`3f9c81153f4fa742479d1b8d7792a18e294e6253`,
`test_products_api.py` `fe78cf9d4862123442611444d44bf81b5187ec6d`,
`test_transport_api.py` `6d65274f9e7b5589d60777d7e0484b3ad10df394`
(all five equal Worker-2's after-hashes; its before-hashes equal
this record's `## Trace`); unchanged and equal to `## Trace`:
`apps.py` `8ae1a3a3...`, `conf.py` `ae3de0a3...`, `views.py`
`48ee582e...`, `_cross_web_patches.py` `52bf8f57...`.

Scratch: `docs/review/temp-tests/_strawberry_patches/verify-comments-1/`
(`code-digests.txt`). No workspace copy was created.

Handoff: Verification is complete with no new finding: 16/16 Proofs
print 0, 16/16 landed docstrings grade true, prose-only identity
independently confirmed on all five files, five attacks pass, no
dispute to judge, no failability or test tier owed, no cell left
unverified. Three remarks for Worker-0, none a gap: (1) the record's
L5 Symbol line names the kill-switch test but the sentence lives in
`test_only_the_package_mount_answers_the_same_way_in_both_patch_states`
— the Proof was file-scoped and correct and the fix landed in the
right sentence, so this is a record nit only; (2) Worker-2's report
miscounts three line lengths (L3 97→107, F2 continuation 89→91, L6
107→109) — all still inside the 110 grace with the lint gates green,
so a report nit only; (3) pre-existing bare `(spec-033/034/043)`
pointers in `test_products_api.py` sit in symbols about other
features that this item did not touch — they belong to their owning
items' Comments passes, not to this diff. Open threads: none on
Comments.
