# Review · Mechanics: `django_strawberry_framework/_strawberry_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=f3d32be142a493b44bf522d75471843f2fc86285

## Trace

Target read whole at blob `2b39199b` (live; equals ITEM_BASELINE;
HEAD and CYCLE_BASELINE are `f77df349`). The HEAD-to-live delta is the
truthful-reads switch at five sites (four `SomeClass.__dict__.get` become
`truth.class_dict`, plus the `truth` import); the dispatch notes the target
dirty with concurrent work, and this review fingerprints the live text it
graded. Orientation: `review_inspect.py` into
`docs/review/temp-tests/_strawberry_patches/mechanics/inspect/` (json
`docs/review/temp-tests/_strawberry_patches/mechanics/_strawberry_patches.json`),
leads only.

Callers and contracts followed:
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
(dispatches
`django_strawberry_framework/_strawberry_patches.py::apply` second of
four, behind function-local imports);
`django_strawberry_framework/conf.py::upstream_patches_enabled` (the
`APPLY_UPSTREAM_PATCHES` gate, its whole-mapping validation, and the
strawberry/cross_web joint-ownership comment);
`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json`
(the strict UTF-8 decode that delegates through `super()` to the patched
`BaseView.parse_json`, so a package view rides this gate for the envelope
guard) and `django_strawberry_framework/views.py::_RawBodyRequestAdapter`
(the body source that makes the wire contract hold in every patch state);
`django_strawberry_framework/utils/truth.py::class_dict` scope and
`django_strawberry_framework/utils/__init__.py` plus its leaves
(`relations`, `strings`, `typing`: `exceptions` / `truth` / Django-ORM /
stdlib only, no cycle back to `conf` or the patch); sibling scaffolds
`django_strawberry_framework/_cross_web_patches.py::apply` (the pair half
that routes the sync bytes into `parse_json`),
`django_strawberry_framework/_django_patches.py::apply`, and
`django_strawberry_framework/_graphql_core_patches.py::apply` (with the
same-named
`django_strawberry_framework/_graphql_core_patches.py::_captured_upstream_method`
twin) for capture, validation, installed-check, and gate comparison;
`django_strawberry_framework/__init__.py` (imports no patch module: the
module loads only via `ready()`). Oracles read whole:
`tests/test_strawberry_patches.py` (idempotence, three self-heal rows,
gap-1 translation + bytes-semantics preservation + str identity, batch
passthrough, the multipart structural/non-structural/server-bug/deepcopy
matrix, the native multipart-reason pin, the falsy skip, the installed
short-circuit, nine drift/signature/body/sourceless refusals, both gate
shapes plus the django-key independence row, the behavioral opt-out row,
the None-owner capture row, the five depth rows),
`tests/test_apps.py` (dispatch plus the four-module double-reload
capture-retention rows), the `upstream_patches_enabled` rows of
`tests/base/test_conf.py` (via the sibling reads), the opt-out and
reason-pin rows of `tests/test_views.py`, and the live rows
`test_the_upstream_bug_workaround_still_respects_its_own_opt_out`,
`test_the_cross_web_half_turns_upstreams_own_500_into_a_400`,
`test_post_non_object_json_body_returns_400_not_500`,
`test_post_batch_with_non_object_elements_returns_400_not_500`, and
`test_a_multipart_map_must_be_an_object_not_a_batched_body`. Standing
contracts: spec-046 Decision 9 (wire contract owned by the view plus its
body source; this module decodes nothing) with its slice checklist (the
gate-states paragraph this module's docstring must carry),
`docs/GLOSSARY.md` anchors "Upstream patches" (four appliers,
validate-before-replace, idempotent; the kill switch with whole-mapping
validation; strawberry/cross_web joint ownership), "Django AppConfig"
(four-module dispatch order, gate-inside-`apply()`), and "UTF-8 wire
contract" (permanent policy on the view, not on the kill switch);
`docs/README.md` (production error policy and mutation envelope: neither
reaches an app-load patch path). Installed seams read in `.venv` at
strawberry-graphql 0.324.0 / cross-web 0.7.0: `BaseView.parse_json` (still
`except json.JSONDecodeError` only, via `decode_json`),
`BaseView.parse_query_params` (byte-identical to the pinned source),
sync/async `parse_http_body` (still unguarded `data.get` / `item.get`),
sync/async `parse_multipart` (still `KeyError`-only around the utility;
the async native multipart reason still byte-identical to the delegate's),
`replace_placeholders_with_files` (unvalidated `.items()` / `.split()` /
`int()` / index, unconditional `copy.deepcopy`), the nine `parse_json`
call sites (one, `parse_multipart_subscriptions`, defined once and never
called anywhere in the installed package - the dead-code claim holds at
0.324.0). Plan `docs/review/review-0_0_15.md` `## Owned changes` holds no
`_strawberry_patches.py` rows (item `reviewing`). Sibling axis records
absent at read time (only `docs/review/rev-_strawberry_patches.md`
skeleton exists): no Handoff or Cross-axis sections to absorb.

Workspace runs, address `review/_strawberry_patches.py/mechanics`, package
digest `sha256:a5e0fd4e9d4271889bcc1320ab915c8b7c68957010827aa750c9ff572565396d`,
cell `default`, each copy `fresh`, shared tree unmoved since sync except
the last run (`shared=moved 1`, concurrent work outside this pass; its
package digest matches the other six, so the measured tree is
identical):

- `review-20260928T221135-d82b75`:
  `pytest tests/test_strawberry_patches.py tests/test_apps.py --no-cov -q`,
  54 passed, 5 errors. All five error in session-fixture setup, before any
  target line runs: the copy's `json.loads` parsed a 262144-deep document
  without overflowing, so `pathological_json_text` raises its designed
  loud `RuntimeError` (`conftest.py`, clean at `b625bf0c`). The
  RecursionError-via-real-`json.loads`-input rows are unverifiable in this
  cell; the probe below pins their wiring plus a real deepcopy-overflow
  input instead. Not a target defect: the fixture fails loud by design
  rather than passing without exercising anything.
- `review-20260928T221327-2cd1ec`: `probe_capture_strictness.py` v1, exit
  1 on the probe's own bug (dummy owner carried `parse_json` while the
  graphql-core half queried `complete_list_value`); fixed, never a target
  behavior.
- `review-20260928T221356-51ca86`: `probe_capture_strictness.py`, ALL OK
  (6/6: own-stamp recovery identical in both twins; sibling-stamp
  divergence pinned - this twin keeps the stamped method, the
  graphql-core twin unwraps to the foreign original; unstamped
  passthrough in both).
- `review-20260928T221404-e9f45e`: `probe_translation_wiring.py`, ALL OK
  (11/11: delegate-`RecursionError` translated with upstream's reason and
  chained cause through the wrapper and the shield; plain `ValueError` and
  `JSONDecodeError` pass through untranslated; a real
  loads-accepts/deepcopy-overflows document becomes the multipart 400
  through the patched sync parser and the raw `RecursionError` through
  the captured original; the provenance helper answers True inside the
  utility frame, False outside).
- `review-20260928T221409-b181de`:
  `pytest tests/test_views.py::test_the_wire_contract_holds_with_the_upstream_patches_opted_out tests/test_views.py::test_the_sync_view_hands_parse_json_raw_bytes_in_every_patch_state --no-cov -q`,
  19 passed.
- `review-20260928T221415-7caa3f`: the live opt-out row plus the live
  cross-web-half row, 3 passed.
- `review-20260928T221435-813004`: the live scalar-body, non-object-batch,
  and multipart-map rows, 11 passed.

Cells: `sharded` and `pg` inapplicable by construction. The module parses
request bytes, installs at app load, and validates upstream shapes; it
opens no database, names no alias, reads no vendor flag, and branches on
nothing dialect- or alias-count-dependent. The live rows above ran in the
default cell. The verifier judges.

Fingerprints (`git hash-object`):

`django_strawberry_framework/_strawberry_patches.py`
2b39199bb2de42e40ae49d62bd24cc8a7a962c1b;
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/_cross_web_patches.py`
52bf8f5712d632817587f93c4eeb881fd74ffaae;
`django_strawberry_framework/_django_patches.py`
6918a213170ea902386a5845da8c6cd1f901baf2;
`django_strawberry_framework/_graphql_core_patches.py`
90ac4f3cc15be1c24dc1f0281206e260d7555cb6;
`django_strawberry_framework/views.py`
48ee582ecdba41d49beb2434f2a9e0af992d39d4;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`django_strawberry_framework/utils/__init__.py`
1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee;
`django_strawberry_framework/utils/relations.py`
05ff55b098382a4a7aafe5a097c3b5e906f8f985;
`django_strawberry_framework/utils/strings.py`
5a4f481132f87cc83abeb2a4a4a679990fa5b9bc;
`django_strawberry_framework/utils/typing.py`
a672cd6b4f5cf6c207bd4f65eb080acd971a6b98;
`tests/test_strawberry_patches.py`
94a5bfa489029328cda91dff893882bf8fc93e6f;
`tests/test_apps.py` 5ca8b62c53185343ebfec95315f59ec6104fc851;
`tests/test_views.py` c542cf1b21c5f275eae171108bdcad0a369afa3d;
`examples/fakeshop/test_query/test_transport_api.py`
b1681e8c725ceb46a0243c770a7dcd295edefc06;
`examples/fakeshop/test_query/test_products_api.py`
f57d9a0a602ee349316b3346f47102d50c4b81bd;
`docs/SPECS/spec-046-transport_security-0_0_14.md`
8d8adaf2f2f07cbc6cd3d434a029b2419b7d4704;
`docs/GLOSSARY.md` 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd;
`docs/README.md` 30978c34f63a833ffcc0fa11c80b773d241921be;
`conftest.py` b625bf0cd063fd59d984850cbd4660a4d3792e81;
installed `strawberry/http/base.py`
05df08e8035850096769983abcb931d3d6c97ca5;
installed `strawberry/http/sync_base_view.py`
48ca38b7a42a74d58381030988d59f213ab7dd07;
installed `strawberry/http/async_base_view.py`
1027f60db50a79c564b00d1f658f3fbb54b462cc;
installed `strawberry/file_uploads/utils.py`
ea08c2200b8ba4db228d8d4cd2d8af534d066e5a.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

- **R1: capture requires exact owner where the graphql-core twin accepts
  any `django_strawberry_framework.*` prefix.** No contract source
  establishes cross-module wrapper recovery, and the package-wide grep
  shows no two modules patch the same method (the only writers to
  `parse_json`, `parse_query_params`, and both `parse_multipart` slots
  are this module's
  `django_strawberry_framework/_strawberry_patches.py::apply`), so both
  spellings behave identically on every real input; the reload rows pin
  the reachable (own-owner) half for all four modules. The probe
  (`review-20260928T221356-51ca86`) pins what the unreachable half would
  do: under a hypothetical second package writer, this twin's exact
  spelling keeps the stamped method and would delegate through it, while
  the twin unwraps the sibling's fix back to the foreign original - the
  exact arm is the fail-closed one here (a foreign wrapper validates as
  drift and raises rather than being silently unwrapped). Reopen: a
  second package writer to one slot, or a retirement moving a patch
  across modules.
- **R2: `_UPSTREAM_JSON_PARSE_REASON` duplicates
  `views.py::_JSON_PARSE_REASON`.** DRY change challenge ("upstream
  rewords its reason"): both copies change - count 2 - but they have
  different reasons to change beyond that event (this copy retires with
  the patch module; the view's is permanent policy under spec-046
  Decision 9), and consolidating would couple the patch module's import
  and deletion to the package's view surface, which the comment at the
  definition forbids for exactly that lifecycle reason. Drift cannot go
  silent: `tests/test_views.py` pins both literals against upstream's
  live raise. Reopen: retirement of this module (one copy remains), or a
  shared constants owner that preserves importability and deletability.
- **R3: the envelope guard lives in the gated patch although a package
  view rides it via `super().parse_json`.** Moving the guard into the
  ungated view would make a temporary workaround for upstream #3398
  permanent package surface, and spec-046's slice checklist explicitly
  requires this module's docstring to name both gate states instead -
  the behavior is specified, not drifted, and pinned on the wire by
  `test_the_upstream_bug_workaround_still_respects_its_own_opt_out`
  (3 passed, `review-20260928T221415-7caa3f`). Reopen: upstream #3398
  lands the `isinstance` checks (the guard retires), or a spec re-homes
  the guard.
- **R4: `_patched_parse_query_params` reimplements upstream's body
  instead of delegating.** Delegation is what the shield exists to
  avoid: routing the GET parses through the patched method would fire
  the request-body guard on `?variables=null` (200 -> 400) and shadow
  upstream's per-param message. Because it supersedes rather than wraps,
  the body source is pinned and any drift - new params, changed
  falsy-skip, unreadable source - raises at `apply()` (three dedicated
  rows). Reopen: an upstream body change (loud refusal per contract), or
  the guard re-homed off `parse_json` (the shield deletes with it).
- **R5: `_MULTIPART_TRAVERSAL_ERRORS` catches types a server-side bug
  can share.** The translation is scoped by provenance, not by type
  alone: the traceback must pass through the upload utility's own
  frame, which is exactly the call upstream wraps in its
  `KeyError`-only `except`. Both arms are pinned (four malformed-map
  shapes plus the deep-document rows translate; the traversal-typed
  server-bug rows on both transports keep their raise), and the probe
  (`review-20260928T221404-e9f45e`) pins the helper True-inside /
  False-outside directly. Reopen: an upstream utility refactor moving
  the raise out of its frame (the structural rows would 500), or a
  supported third-party wrapper changing the frames.
- **R6: the ImportError fallback never runs on supported envs.** It is a
  drift guard, not dead code: without it an env missing the symbols
  fails at `ready()` import time with a bare ImportError instead of the
  targeted RuntimeError naming the per-dependency opt-out. The
  `None`-states it enables are pinned via monkeypatch (the missing
  symbol, multipart-view, and utility rows). Reopen: a supported env
  missing the symbols.
- **R7: the Sync/Async-None conjuncts of `_patch_is_installed` are
  unpinned.** `apply()` validates before the installed check, so they
  can only answer `False` to direct callers (the BaseView-None half is
  pinned directly; the multipart-None rows reach only validation).
  Correct and fail-closed (an absent owner reports "not installed"),
  statement coverage passes, and the gap is hardening, not a code
  defect, so no finding - the sibling items' R9/R3 shape. Reopen: a
  direct caller needing the path pinned, or branch coverage enforced.
- **R8: `apply()` validates before the installed check, so a re-entrant
  call revalidates rather than pure-no-op.** Correct: drift fails loud
  even when the patch is already installed. The "no-op" contract means
  "no reinstall", which the installed check delivers. Reopen:
  validation cost matters (it runs at app-load cold frequency).
- **R9: the shape check pins arity and kinds but not parameter names,
  and would false-positive on POSITIONAL_ONLY params.** The delegation
  calls are positional, so names genuinely cannot break them; kinds pin
  the audited shape, and refusing an unseen shape is the house
  fail-closed stance (a positional-only upstream raises the drift
  RuntimeError naming the opt-out rather than patching blind). Reopen:
  an upstream signature drift - validation raises per contract, and the
  retirement probes own the re-audit.
- **R10: capture, validation, installed-check, and `apply` scaffolds
  look alike across siblings.** They pin different upstream contracts:
  different methods, arities (`(self, data)`, `(self, params)`, `(self,
  request)` here), descriptor kinds (plain methods and one pinned
  reimplementation vs the siblings' classmethod / property / executor
  slots), and validation depths (delegators pin call shape;
  reimplementers pin body source - this module's
  `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape`
  pins the shield body because
  `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`
  supersedes it). Similar shape, separate reasons to change. Reopen: a
  shared helper that preserves per-module retirement and the
  delegator-vs-reimplementer depth distinction.
- **R11: patch-owner attribute literals repeated across the four patch
  modules.** Each module's capture, stamp, and installed-check reference
  only its own constants, and no two modules patch the same method, so
  each can rename alone - a stale in-flight wrapper under the old name
  misreads as upstream and fails loud at validation rather than
  silently corrupting. A shared owner would couple the
  one-module-per-dependency retirement lifecycles (this module deletes
  outright once its three gaps retire). Reopen: a second protocol
  attribute appears, or two modules patch one method.
- **R12: the sync/async multipart delegates are near-identical twins.**
  The four-line bodies differ only by `await`, which the language
  requires; the error set (`_MULTIPART_TRAVERSAL_ERRORS`), the reason,
  and the provenance helper are single-sourced, and the twin pair
  mirrors upstream's own sync/async method pair. Each transport's
  translate / server-bug / deepcopy arms are pinned separately, so a
  twin-only drift fails its own rows. Reopen: twin-only logic appears
  (then share it or justify the split).
- **R13: stamp reads use plain `getattr`, and the provenance helper
  reads `__code__` by attribute lookup.** Upstream view classes and the
  upload utility are framework objects, not consumer classes; `truth`
  scope is consumer identity facts. The `class_dict` reads (where a
  hostile metaclass could intercept the namespace lookup) are the ones
  that went truthful in the HEAD-to-live delta, and every oracle row
  passes on the live text. Reopen: the truthful-reads gate flags these
  sites, or a hostile-metaclass upstream shim becomes a supported
  input.
- **R14: catching `RecursionError` and then running Python (raise,
  traceback walk).** Empirically sound on this interpreter: the probe
  (`review-20260928T221404-e9f45e`) drives a real
  loads-accepts/deepcopy-overflows document through the patched sync
  parser to its 400 (and through the captured original to the raw
  escape, the positive control), and the translator's post-catch work
  is one raise. The five suite depth rows that need a real
  `json.loads` overflow error loudly in fixture setup on this
  interpreter instead of passing hollow. Reopen: an interpreter where
  the post-catch raise re-overflows (those rows fail loud).
- **R15: refusal RuntimeError wordings repeat per module.** Each names
  its own dependency key plus its own shape clause, and the oracles pin
  the fragments (`parse_json`, `parse_query_params`, `parse_multipart`,
  `replace_placeholders_with_files`, `upstream body`); a shared helper
  would couple the per-module retirement lifecycles. Reopen: a shared
  helper that preserves per-module retirement and per-key opt-out
  naming.

Looks-for discharge (REVIEW.md "Mechanics"):

- rule at a caller instead of its owner: none. The gate lives in each
  `apply()` via
  `django_strawberry_framework/conf.py::upstream_patches_enabled`, not in
  the `ready()` dispatcher; the translation lives in the wrapper that
  owns the slot (`_translated_parse_json` shared by the wrapper and the
  shield so the two cannot drift); the envelope guard lives beside the
  translation it rides with (R3); validation lives in
  `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape`,
  not at callers; batch enablement/size stays with upstream's
  `_validate_batch_request` (well-typed lists pass through).
- policy in an adapter / mechanism in a policy layer: none. The module is
  pure mechanism; gating policy lives in `conf`; the permanent UTF-8
  policy lives in the view, not here, per spec-046 Decision 9 (R2); the
  per-dependency independence holds (this key drops only the Strawberry
  body hardening, with the documented cross_web pairing).
- contract sources vs body: none. Spec-046 Decision 9 plus its slice
  checklist, the three GLOSSARY anchors, every owner docstring, and all
  five oracle files match the body; `docs/README.md` error and mutation
  contracts reach no app-load path. The installed 0.324.0 seams match
  every audited claim re-checked (narrow `except`, unguarded `.get`
  sites, `KeyError`-only multipart, pinned shield source, dead
  subscription site, native multipart reason).
- branch no real path reaches: none. Every branch has a pinned or guarded
  path: ImportError fallback is the R6 drift guard; owner-None via its
  row; own-stamp recovery via the reload rows (sibling-stamp half
  unreachable, R1, probe-pinned); all four validation tiers via the
  drift, signature, body, and sourceless rows; both translator arms via
  the Unicode row and the RecursionError wiring (suite rows where the
  interpreter offers a depth, probe wiring where it does not); all three
  guard outcomes via the passthrough, batch, and live scalar/batch rows;
  both shield outcomes per param via the falsy-skip and live GET rows;
  all three multipart outcomes via the valid-batch, structural, and
  server-bug rows on both transports; all three install states via the
  installed, reverted, and BaseView-None rows (multipart-None halves
  R7); both gate outcomes via the global and per-dependency rows plus
  the behavioral opt-out row.
- mode flag standing in for a named adapter: none (the mapping keys are
  the adapter names per the one-module-per-dependency rule).
- state owned in two places: none. The import-time captures
  (validation/delegation sources), the function-carried originals
  (reload channel), and the live class attributes (install state) are
  three roles joined by the reload protocol, pinned by the reload and
  double-reload rows (R11 for the shared literals, R10 for the
  scaffolds).
- dependency direction: none. Target to `conf` and to stdlib-only
  `truth` (no cycle; the `utils` package `__init__` pulls only
  relations/strings/typing, whose imports are `exceptions` / `truth` /
  Django-ORM / stdlib; `conf` never imports the patch); no
  `TYPE_CHECKING`; function-local `ready()` imports keep the package
  import free of the patch and its Strawberry imports.
- `django.conf.settings` at import: none (no `django.conf` import; the
  setting is read inside `apply()` through the gate).
- `__all__` vs public surface: none. The private module carries no
  `__all__`, like all three siblings; `apply` is exported for `ready()`
  and the regression tests, and no star-import surface exists.
- two sites implementing one rule: none. DRY challenges run, each count
  1 or deliberately split with a pin: the JSON reason literal (R2, count
  2 with differing lifecycles and a live-raise pin); the multipart
  reason (single-owned copy with a native-raise pin); capture/validate/
  install scaffolds (R10); stamp literals (R11); refusal wordings
  (R15); the shield body (upstream owns the original; the pin fails
  loud on drift, not a package rule twice); the multipart twins (R12);
  `_RawBodyRequestAdapter.body` vs the cross_web getter (different
  contracts - permanent per-view body source vs gated process-global
  workaround - documented at both sites, each retiring alone).
- sync/async twins: none (R12; the shield/wrapper share
  `_translated_parse_json`, and the package views share the mixin, so
  the only twinning is the `await` the language requires).
- guard one flavor has and a sibling lacks: none. Capture, validation,
  and installed-check differences track descriptor kinds and
  delegator-vs-reimplementer depths (shape-only is correct for the three
  delegators because bodies flow through; the shield pins its body
  because it supersedes); the owner-breadth difference is R1 and the
  truth-scope difference is R13, neither established by a contract
  source as a missing guard.

No `--cited-by` sweep is owed: zero findings recommend moving or
renaming any symbol. No Proof line is owed: zero findings carry one.

Handoff: read beyond the record the installed 0.324.0 multipart,
query-param, and upload-utility bodies (why R5's frame scope is exact
and R9's positional delegation is sound), the spec-046 Decision 9 text
with its checklist (why R2/R3 are specified rather than drifted), the
`conf` gate implementation with its whole-mapping validation, the
`test_views.py` reason-pin row (why R2 cannot split silently), and the
sibling `_django_patches` / `_graphql_core_patches` mechanics records
(why R1/R6/R7/R8/R10/R11/R13/R15 share their triggers). Conclusions the
rejections do not state: every drift seam in the file fails loud with
the opt-out named; the HEAD-to-live truthful-reads switch preserves
behavior (54 package rows plus 19 view rows plus 14 live rows green on
the live text, with the one fixture caveat below); the three retirement
lifecycles are genuinely independent (translation, guard+shield,
multipart delegates) and the module deletes outright once all three
retire. Open threads: none on Mechanics. Two notes for siblings, not
findings: (1) for Comments - the module docstring's "0.317.2 (the latest
release)" currency claim has aged past the installed 0.324.0, but every
gap it dates was re-verified still present at 0.324.0 in this pass, so
only the parenthetical is stale, not the substance; (2) for Worker-0 -
the five depth rows error in fixture setup on this run's interpreter
(`review-20260928T221135-d82b75`), the fixture's designed loud signal,
and the gap-1 RecursionError arm rests on probe wiring here rather than
a real overflowing input. No Mechanics lead routes to another item, and
no Cross-axis finding: Performance and Comments siblings were absent at
read time, and nothing observed belongs to them. Scratch kept:
`docs/review/temp-tests/_strawberry_patches/mechanics/` (`inspect/`,
`_strawberry_patches.json`, `probe_capture_strictness.py`,
`probe_translation_wiring.py`).

## Verification (Mechanics)

Pass 1. Implement landed prose-only hunks for 16 Comments findings
across 5 files; Performance and Mechanics closed no-findings, so no
production hunk exists on this axis.

Ordering note: the Worker-2 sections were read before Verify step 1's
hash check completed. The pre-read obligation was vacuous - this
record carries zero Proof lines and no record carries a `## Cross-axis
(for Mechanics)` section (Performance has none; Comments' reads
`None`), so no expectation-setting run existed to place before the
read. The hash check then passed, so the read order cannot have
affected the verdict.

Checks and results:

1. Item-diff identity (Verify step 1): `git diff
   f3d32be142a493b44bf522d75471843f2fc86285 -- <the five touched
   paths>` hash-equals
   `docs/review/temp-tests/_strawberry_patches/diff/pass-1.diff`
   (`sha256:210d05598a2aff7f2a007763876a3e1a4e00edd3a8adb30d459e40
   93a6fd4e23` both sides, `cmp` silent). The tree did not move
   under the pass.
2. Proof lines: none owed, none run. Zero findings carry one, and
   no sibling `## Cross-axis (for Mechanics)` section exists.
3. Behavior preservation: `--code-digest` identity reproduced on
   all five files (exit 0, equal digests each, matching Worker-2's
   reported prefixes): target `sha256:6d124535...6f4b61e`, own
   tests `sha256:9cd25a75...2a220ca`, `tests/test_views.py`
   `sha256:98eeaeb6...6d7ad0ec`, `test_products_api.py`
   `sha256:c4bc802f...6d7ee`, `test_transport_api.py`
   `sha256:f282ed6d...1963b3d`. Full output kept at
   `docs/review/temp-tests/_strawberry_patches/verify-mechanics-1/code-digests.txt`.
   A revert proof is vacuous: with no production hunk there is no
   `prove` manifest to write and no test the change relies on, so
   no failability, no test-tier judgment, and no before/after
   number is owed.
4. Diff read through this axis (whole `pass-1.diff`, 5 files, 15
   hunks): every hunk sits inside a docstring; a grep of all `+`/`-`
   lines for `def` / `class` / `import` / `from` / decorator /
   statement keywords returns zero hits. No symbol moved or was
   renamed, so no `--cited-by` sweep is owed. No module first line
   changed, so no TREE.md render is owed. No contract source this
   record cites (spec-046 Decision 9, the three GLOSSARY anchors,
   owner docstrings, `docs/README.md`) is touched by the diff, and
   none of R1-R15's pinned sites changed meaning. The one stale
   sentence this record's Handoff named (the F8 parenthetical)
   landed in prose; its truth grade belongs to Comments.
5. Attacks on the current state, all passing:
   - Smuggled-code grep over the item diff: clean (see 4).
   - Opt-out-block soundness (the F6/F7 scoping premise): all four
     `with _strawberry_patch_opted_out():` blocks (one in
     `tests/test_views.py`, three in `test_transport_api.py`) post
     JSON bytes only - `view.parse_json(body)` or `_post_bytes`,
     which posts `content_type="application/json"`. No block posts
     multipart, so the still-installed delegates are unreachable
     there as the new prose states.
   - Current-state behavior:
     `review-20260928T225158-ba5db0` at
     `review/_strawberry_patches.py/verify-mechanics-1` (fresh
     copy, shared unmoved, cell default, package digest
     `sha256:41e15d13...52a54c`) reran the two view-tier nodes this
     record pinned at review time
     (`test_the_wire_contract_holds_with_the_upstream_patches_opted_out`,
     `test_the_sync_view_hands_parse_json_raw_bytes_in_every_patch_state`):
     19 passed, exit 0 - identical to the review-time count.
6. Disputes: none recorded (`grep -c 'disputed:'` on the main
   artifact prints 0); nothing to judge.
7. Lint gates (`--check` forms only), all green: `ruff check` on
   the five touched paths (All checks passed); `ruff format
   --check` (5 files already formatted); `check_trailing_commas.py
   --check` on the five paths (0 violations, ASCII clean);
   `check_citations.py --check` tree-wide (1297 citations
   resolve).
8. Cells: `sharded` and `pg` inapplicable by construction - concur
   with the record's reason (the module parses request bytes and
   opens no database, names no alias, reads no vendor flag), and
   the change itself is prose-only. Cells unverified: none.

No new problem on this axis; no gap for `## Decisions`; nothing
routes to another item. Touched-file fingerprints now equal
Worker-2's reported after-hashes byte for byte (target `90f711fb`,
own tests `c06add91`, `test_views.py` `3f9c8115`,
`test_products_api.py` `fe78cf9d`, `test_transport_api.py`
`6d65274f`).

Handoff: this verification rests on digest identity plus one live
attack run, not on re-running the review's probes: identical
code-digest pairs mean the capture-strictness and translation-wiring
behavior the review pinned cannot have moved, and the 19-node rerun
confirms the edited tree still passes the view-tier pins. The one
ordering deviation (Worker-2 sections read before the step-1 hash
check) is recorded above with why it is immaterial. Scratch kept:
`docs/review/temp-tests/_strawberry_patches/verify-mechanics-1/`
(`code-digests.txt`). Open threads: none on Mechanics.
