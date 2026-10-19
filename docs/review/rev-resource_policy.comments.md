# Review · Comments: `django_strawberry_framework/resource_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e3af18216bc75ecbd6bd080d78cdb1b209458e79

## Trace

Read the whole live target (`django_strawberry_framework/resource_policy.py`,
1371 lines: module docstring, 41 function/method/class docstrings, 9 `#:` comment
blocks, 9 inline comments) and the whole own test module
(`tests/test_resource_policy.py`, 3956 lines: module docstring, ~110 test/helper
docstrings, 14 section banners, ~60 inline comments). No sibling axis records
existed at dispatch (only `rev-resource_policy.md`, `Status: reviewing`);
required reading was AGENTS.md, START.md, REVIEW.md, worker-1.md, the plan, and
`rev-resource_policy.md`. The target and its test module are dirty with
concurrent work (per the dispatch and `git status`); every grade below is
against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/resource_policy/comments/inspect/` plus
`docs/review/temp-tests/resource_policy/comments/resource_policy.json`.
`build_tree_md.py --list-docstrings` passes on the target (1 module,
0 breaking). `check_citations.py --paths <file> --substrings --json` reports
16 citations, 0 violations in the target and 2 citations, 0 violations in the
test module. Provenance sweep (REVIEW.md pattern, regex mode) on the target
hits only `Spec:` (kept pointer), `silently` x3 (behavioral), `shipped`
(R3), `no longer` (R4), `reused`; on the test module `spec-keyed`,
`silently` x4 (behavioral), `Probed by the hunt` (F5), `(spec-050
Decision 8)` (kept, verified against the spec text), `used to return`
(R2). No `we`/`you`/`I`, no `Tests that`/`Ensures`, no `.py:NN`, no TODO,
no public symbol without a docstring in either file.

Contract trace, each risky claim checked against its body and one real caller:
the `check_deadline` caller inventory (all 10 call sites: `_raw_list_bound`,
`connection.py::DjangoConnection.resolve_connection`,
`relay.py::DjangoNodeField` / `DjangoNodesField` resolvers,
`mutations/resolvers.py::run_write_pipeline_sync`, five
`types/resolvers.py` single-object arms — the last family is F2);
`resolve_policy` precedence (explicit > setting > default);
`_ValueBudget._charge_upload` limit/charged spelling (F6);
`_page_bound` page-ceiling fallback + `multiplier * rows` (the 10**8 claim,
true); `ValidationCache` unconditional `pre_execution_errors` overwrite
(installed wheel, true); `_bounded_members` exact-type/islice mechanism (F1);
the `/iso-survivor/` live worker test (F3); `MAX_RESOURCE_BOUND` vs
`sys.maxsize` (R5); the 0.319.0 `Schema.stream` floor note (floor is 0.316.0,
true); spec-050 Decision 8 (names this exact test file, true).
Other-test prose: module docstrings + every docstring/comment naming a target
symbol in 15 further test modules (extraction under
`docs/review/temp-tests/resource_policy/comments/other_test_prose.txt`).
Package prose: every docstring/comment naming a target symbol in 19 further
package modules (`package_prose.txt`); all grade true, no Routed lead.

Fingerprints (`git hash-object`) of every file inspected:

- `django_strawberry_framework/resource_policy.py` `cc3f9d80b9d55af8b725a77c73aba3d8110e0037`
- `tests/test_resource_policy.py` `585c536e65aba030c920d86dfaf95dbabe95807e`
- `django_strawberry_framework/extensions/resource_policy.py` `0134d83a9aa2db580b7b8180ded27a3d31b115c7`
- `django_strawberry_framework/connection.py` `1fca6266cd5f748915875badf1881680b599de37`
- `django_strawberry_framework/relay.py` `f5760b45f161cccf9dce6d2c84b45311b5b03291`
- `django_strawberry_framework/mutations/resolvers.py` `c9cff0590157de85bd9374ab85588b00e62080e0`
- `django_strawberry_framework/types/resolvers.py` `640905c63f465db4de16c3a07492b27f3d12d3ad`
- `django_strawberry_framework/schema.py` `84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1`
- `django_strawberry_framework/conf.py` `3820c575bfd4e3c384244d1bed460b75d3bb7681`
- `django_strawberry_framework/utils/policies.py` `0a2b7dbad96594b5d668774218809c6a94d136be`
- `django_strawberry_framework/utils/querysets.py` `8fc556d582b313e4aed7cddaa15f9a8480d88a46`
- `django_strawberry_framework/list_field.py` `f5b0183e290322952fd2dad1f76ab9b2de9736ba`
- `django_strawberry_framework/error_policy.py` `57a0bed1ba730f8e4c1f4c879d852274eac39f12`
- `django_strawberry_framework/types/base.py` `dc67f084cbc969d64b7b1f1ef18c388095d394f7`
- `django_strawberry_framework/utils/connections.py` `efcf749a26dc7d3fa9b3cc142789a11de2647070`
- `django_strawberry_framework/utils/context.py` `edebf0ea1423569a098704aa1193e0c276507622`
- `django_strawberry_framework/utils/errors.py` `6a389474293cbd471b732fd73ba2b8632205c938`
- `django_strawberry_framework/utils/private_state.py` `b3c45503c3e2f648640b95ecad4d71a8315abb51`
- `django_strawberry_framework/optimizer/_context.py` `dbc306305256fd5f0631b29d440a72b1c9ba1abf`
- `django_strawberry_framework/extensions/__init__.py` `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`
- `django_strawberry_framework/extensions/operation_state.py` `d9ed9cc67fea892afa2dd22a33236a52fc061fb1`
- `django_strawberry_framework/consumers.py` `0791c04a6c7b2619562f33dc707b002cde718c6b`
- `tests/base/test_init.py` `239648ed635fa67baa10bf5bd428cd127098088b`
- `tests/extensions/test_operation_state.py` `7509c1ccaa1c56c50be2ca3bc4337b75bcca90ce`
- `tests/forms/test_resolvers.py` `6cab42c2ff6779e1a64e98bdc055d24ac6389378`
- `tests/test_error_policy.py` `9a72cdb83d4739be4018a3c58d0bf2736b63f569`
- `tests/test_list_field.py` `d78aa5e79fee14b37564f856d3d4bc74e7d9630b`
- `tests/test_schema.py` `3676f7e8a9370966c3159264825857a599cdf085`
- `tests/utils/test_connections.py` `65d540271d5b8b8e959fda2d1b5f6132541dfcc9`
- `tests/utils/test_policies.py` `9ec80053095b70f35421e946cd9d54edbd497f29`
- `examples/fakeshop/test_query/test_error_policy_api.py` `071b113feeaf9cee30ccda5941614c423251459c`
- `examples/fakeshop/test_query/test_extension_isolation_api.py` `2744212cf0693cc283253aa9e786882304cfdd44`
- `examples/fakeshop/test_query/test_list_field_api.py` `4c85f77971fcf352b7c8eb0c46cd2268184a0b4a`
- `examples/fakeshop/test_query/test_list_field_async_api.py` `49e423ea593b8883c4c07593accd822390e82468`
- `examples/fakeshop/test_query/test_relation_deadline_api.py` `71e5c03df88d071b567ca04c721a0b91dd9d48c5`
- `examples/fakeshop/test_query/test_relations_async_api.py` `7f5492b428a0c826eab3345c7f7c990287751357`
- `examples/fakeshop/test_query/test_resource_policy_api.py` `ae7bef60173211f55d3e09e022228f69747fa846`
- `docs/spec-050-list_field_arguments-0_0_15.md` `73fe1127a280bfcf791632f2b40dfd2f805b12ec`

## Findings

### High

None.

### Medium

- Observation: the `test_bounded_rows_bounds_a_mapping_shaped_result`
  docstring claims the unsliceable fallback "must absorb `KeyError`
  alongside `TypeError`". No such absorption exists in the current body:
  `_windowed_rows` classifies by exact type
  (`_bounds_by_its_own_slice`) and counts every non-sliceable shape
  through `islice`; a mapping is never subscripted, so no `KeyError`
  can arise to be absorbed. `resource_policy.py` contains zero
  `KeyError`/`TypeError` mentions. The test still passes (mappings are
  bounded via `islice`), but its rationale paragraph describes the
  superseded `except (TypeError, KeyError)` mechanism.
- Evidence: body read (`_windowed_rows`, `_bounds_by_its_own_slice`);
  archaeology: the `except (TypeError, KeyError)` arm lived at
  `a8f31a2d` and is gone after the exact-type rewrite (`11928077`
  "enforce every bound through operations the package owns",
  `3efa11a9` "Own the row source"); the docstring was never updated.
  The first line ("bounded via `islice`, never a raw `KeyError`") is
  still true and stays.
- Impact: a reader maintaining the bound learns a mechanism that is not
  there and will look for a `try`/`except` around a subscript that no
  longer exists.
- Severity: Medium (stale behavioral claim in test prose).
- Recommendation: rewrite the rationale paragraph as the exact-type
  classification rule; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'absorb' tests/test_resource_policy.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_resource_policy.py::test_bounded_rows_bounds_a_mapping_shaped_result`.
- Grade: stale.
- Text-before:
  `A mapping answers a slice subscript with ``KeyError`` on interpreters where slices hash - a plain ``dict`` there, and a dict subclass whose ``__getitem__`` guards its keys everywhere - so the unsliceable fallback must absorb ``KeyError`` alongside ``TypeError``. The alternative was a raw ``KeyError`` escaping a collection resolver exactly because the result was a shape nobody anticipated, which is the same "bound silently stops applying" failure the fallback exists to prevent.`
- Text-after:
  `A mapping is never subscripted: the shape is classified by exact type, so a mapping - and a ``dict`` subclass whose ``__getitem__`` guards its keys - is counted into a fresh list via ``islice``. No ``KeyError`` can escape a collection resolver from a subscript that never runs, which is the same "bound silently stops applying" failure the classification exists to prevent.`
- Observation: the `ResourcePolicy` `execution_deadline_seconds` field
  doc presents its seam list as exhaustive ("every seam that is about
  to hand work to the database calls `check_deadline` first" - the
  raw-list spellings, the connection head, the Relay refetch fields,
  and the write pipelines) but omits the generated single-object
  relation resolvers, which call `check_deadline` directly at five
  sites in `types/resolvers.py` (`forward_resolver` sync + two async
  arms, `reverse_one_to_one_resolver` sync + async). The
  `test_relation_deadline_api.py` live suite pins exactly those seams,
  so they are real deadline seams a reader auditing coverage from this
  docstring would miss.
- Evidence: full `check_deadline(` caller inventory: 10 call sites in
  5 files; all are listed except the `types/resolvers.py` five. The
  many-side relation resolver needs no entry (it rides `bounded_rows`,
  already listed), and there is no second write pipeline (async runs
  the sync pipeline in one boundary).
- Impact: incomplete coverage inventory on the policy's most-audited
  field; a coverage audit from this docstring concludes nested single
  relations are unchecked.
- Severity: Medium (stale inventory; the contract stated is right).
- Recommendation: add the single-object relation family to the list;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'single-object relation' django_strawberry_framework/resource_policy.py` prints `1` (0 today); the rewritten field doc earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/resource_policy.py::ResourcePolicy`.
- Grade: stale.
- Text-before:
  `first - ``bounded_rows`` (both raw-list spellings), ``connection.py::DjangoConnection.resolve_connection`` (the head every connection shape passes through), the Relay refetch fields (``relay.py::DjangoNodeField`` / ``DjangoNodesField``), and the write pipelines (``mutations/resolvers.py::run_write_pipeline_sync``) before their transaction opens.`
- Text-after:
  `first - ``bounded_rows`` (both raw-list spellings), ``connection.py::DjangoConnection.resolve_connection`` (the head every connection shape passes through), the Relay refetch fields (``relay.py::DjangoNodeField`` / ``DjangoNodesField``), the generated single-object relation resolvers in ``types/resolvers.py`` (forward and reverse-one-to-one, sync and async arms), and the write pipelines (``mutations/resolvers.py::run_write_pipeline_sync``) before their transaction opens.`
- Observation: the "A copied context is not an armed one" banner points
  its live sibling at `/iso-budget/`, a mount that never existed: the
  live file was born with `/iso-survivor/` in the same commit
  (`3e5296f6`) that added this banner. The real sibling is
  `test_a_worker_that_outlived_a_request_is_bounded_and_published_for_itself`
  in `test_extension_isolation_api.py`, which pins exactly what the
  banner describes (an outlived worker reads its own context's default
  bound, not the completed request's `max_list_rows=1`).
- Evidence: repo-wide grep finds `iso-budget` only in this banner;
  `git show 3e5296f6` adds the banner with `iso-budget` while adding
  the live mount as `iso-survivor`; the survivor schema + worker body
  read.
- Impact: a reader verifying live-first coverage follows the pointer to
  a mount that does not exist, which reads as missing live coverage.
- Severity: Medium (stale cross-reference; false on its own date).
- Recommendation: repoint the banner at the survivor test; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'iso-budget' tests/test_resource_policy.py` prints
  `0` (1 today); the rewritten banner earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_resource_policy.py` section banner "A copied context is not an armed one".
- Grade: stale.
- Text-before:
  `# Live sibling: a background task cannot raise the row bound a request was admitted under, on ``/iso-budget/``.`
- Text-after:
  `# Live sibling: ``test_a_worker_that_outlived_a_request_is_bounded_and_published_for_itself`` on ``/iso-survivor/`` (``test_extension_isolation_api.py``): a background task reads its own context, not the budget of the request it outlived.`
- Observation: the `test_resource_policy_api.py` module docstring
  claims "`examples/fakeshop/tests` and `tests/test_resource_policy.py`
  hold what a live request cannot reach". `examples/fakeshop/tests/`
  holds no resource-policy content at all (four project/config
  modules; case-insensitive grep for the policy vocabulary is empty),
  so half the pointer sends the reader to a tree with nothing relevant.
- Evidence: directory listing + case-insensitive grep over
  `examples/fakeshop/tests/`; the pointer was born in `567cc6d0`.
- Impact: misdirects the package-tier lookup the sentence exists to
  give; the package tier is `tests/test_resource_policy.py` alone.
- Severity: Medium (stale cross-reference).
- Recommendation: drop the false half-pointer and fix the agreement;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'examples/fakeshop/tests' examples/fakeshop/test_query/test_resource_policy_api.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_resource_policy_api.py` module docstring.
- Grade: stale.
- Text-before:
  ``` ``examples/fakeshop/tests`` and ``tests/test_resource_policy.py`` hold what a live request cannot reach: ```
- Text-after:
  ``` ``tests/test_resource_policy.py`` holds what a live request cannot reach: ```

### Low

- Observation: the `test_an_instance_through_the_setting_slot_resolves_on_the_same_terms`
  docstring carries process provenance: "(Probed by the hunt:
  rejecting it here produced ...)". "Probed by the hunt" names the
  bug-hunt flow as the change vehicle. This is the Routed lead from
  `conf.py` Comments, judged here: finding. The behavioral claims
  around it are true; only the attribution goes, with the WHY kept as
  a plain clause.
- Evidence: docstring read against `resolve_policy` (setting-instance
  branch admits and duplicates); the self-contradictory-message
  rationale verified as the reason instance rejection would be wrong.
- Impact: flow attribution in a contract sentence; the next reader must
  factor out process to find the rule.
- Severity: Low (provenance/tense; claims true).
- Recommendation: rewrite as the present-tense counterfactual; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'Probed by' tests/test_resource_policy.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_resource_policy.py::test_an_instance_through_the_setting_slot_resolves_on_the_same_terms`.
- Grade: process provenance.
- Text-before:
  `(Probed by the hunt: rejecting it here produced a typed message naming ``ResourcePolicy`` as the received type while claiming the value must be a ``ResourcePolicy``.)`
- Text-after:
  `(Rejecting it here would produce a typed message naming ``ResourcePolicy`` as the received type while claiming the value must be a ``ResourcePolicy``.)`
- Observation: the `check_deadline` docstring attributes the
  limit/charged `n`/`n+1` precedent to "this module": "the spelling
  this module already uses for an upload whose size cannot be read".
  The precedent exists but lives in
  `extensions/resource_policy.py` (the value-budget walk's
  unmeasurable-upload rejection, limit `max_upload_file_bytes`,
  charged `+1`); `resource_policy.py` contains no upload code. A reader
  looking for the spelling in this module will not find it.
- Evidence: `_charge_upload` body read (limit/charged `X`/`X+1`
  confirmed); `resource_policy.py` has no upload path.
- Impact: misattributed precedent pointer; the behavior described
  (configured-seconds reporting) is true.
- Severity: Low (bounded clarity; location wrong, contract right).
- Recommendation: repoint at the admission walk; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'admission walk already uses' django_strawberry_framework/resource_policy.py` prints `1` (0 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/resource_policy.py::check_deadline`.
- Grade: stale.
- Text-before:
  `past it (the "exceeded an unmeasurable-in-integers budget" spelling this module already uses for an upload whose size cannot be read).`
- Text-after:
  `past it (the "exceeded an unmeasurable-in-integers budget" spelling the admission walk already uses for an upload whose size cannot be read).`

## Rejected

- R1 — Module docstring `Target release: 0.0.14.` Seven-module standing
  convention; the `Spec:` pointer beside it is kept. Follows the
  `connection.py` Comments R2 precedent. Trigger: the convention
  retired.
- R2 — Past-tense mechanism narratives, each stating the guarded failure
  mode or the contrast the reader needs while naming no change vehicle:
  "The extension used to return its explicit `_policy` raw from every
  hook" (test line 3310: per-hook re-read disagreement, the reason for
  read-once acceptance); "Handing a truthy non-string to the lexer
  raised ...", "Materializing the container asked ...",
  "Reaching for it as ..." / "replaced ...", "was that method's return
  value", "Copying the container first charged ...", "The alternative
  was ..." (failure modes of the naive shape); "the list sibling that
  used to bypass the connection cap" (live module TOC; the bypass rows
  exist); "The pre-card list pipeline ... did before the argument
  surface existed" (oracle identity); "retains old prefix bound"
  (preserved no-coordinates contract). Follows the
  `_strawberry_patches.py` Comments R2 and `connection.py` R3
  precedents. Trigger: naming the vehicle that made the change.
- R3 — `spec-047` "shipped" vocabulary ("stay exactly as spec-047
  shipped them", `_active_budget` comment): spec-anchored present
  contract (the keys remain a mirror + fallback), no code history
  narrated. "Shipped" as present contract follows `connection.py` R3.
  Trigger: none.
- R4 — "no longer has a binding of its own" (`_BudgetScope`): runtime
  state of an adopted scope, not code history. Same accepted shape as
  the verified consumers `no longer` records. Trigger: none.
- R5 — "`MAX_RESOURCE_BOUND` is `sys.maxsize`" (test line 2898 and its
  `_bounded_members` twin): exact on every 64-bit interpreter, which is
  the whole executed matrix (no architecture axis; CI/dev all 64-bit);
  the sentence states the relationship the bounded reader relies on.
  Trigger: a 32-bit cell or support claim.
- R6 — `bounded_rows_async` "stay on `bounded_rows`" (the body calls
  `_windowed_rows` directly): the same seam with no coordinates, the
  same ceiling, the SQL `LIMIT` claim true. Trigger: the two diverging.
- R7 — Kept pointers: module `Spec:` line and `(spec-050 Decision 8)`
  (Decision 8 names this exact test file for positive-offset async
  arithmetic, verified in the spec body); `(spec-047 Decision N)`
  pointers in call-site comments, all inside spec-047's narrative.
  Trigger: a spec renumber.
- R8 — Descriptive function first lines (`The ...` return-contract
  openings on seven private helpers/readers): clear, true, and stating
  what comes back; rewriting a mixed file to uniform imperative is
  churn. The `Whether` predicate family is package convention (conf.py
  R1 precedent). Trigger: a maintainer mood decision applied
  package-wide.
- R9 — "silently" throughout (9 hits): each describes a behavioral
  failure mode (a bound becoming 1, a disarmed budget, an absorbed row),
  never a code-age judgment. Trigger: none.
- R10 — `tests/base/test_init.py` lines 175-187 card narrative ("The
  resource-policy card (spec-047) adds ..."): already homed on the
  Project integration item (plan Routed, from `list_field.py`
  Comments). Not re-raised.
- R11 — `conf.py::RESOURCE_POLICY_KEY` "as a mapping" twin omission:
  already recorded in the plan's `## Decisions` (from `error_policy.py`
  Comments). Not re-raised.
- R12 — `extensions/resource_policy.py` module docstring "this module is
  the one place that spends it": true under spend-as-charge (the three
  accumulating passes live there; `bounded_rows`/`check_deadline`
  enforce point ceilings without accumulating). Considered for routing,
  not routed. Trigger: a charge-accumulating seam landing outside the
  extension.

## Routed leads

None. Every package module's prose about the target's symbols grades
true (see Trace); the two already-homed twins sit under R10/R11, not
here.

## Cross-axis

None. No performance or mechanics finding arose from this pass: the
prose audit surfaced inventories and pointers only, and every mechanism
they describe was verified in place rather than found wanting.

Handoff: I graded every docstring and comment in the target (1371 lines)
and its own test module whole (3956 lines), plus the target-symbol prose
in 15 other test modules and 19 other package modules: 4 Mediums (F1
stale KeyError-absorption rationale, F2 deadline-seam inventory missing
the single-object relation family, F3 stillborn `/iso-budget/` mount
pointer, F4 false `examples/fakeshop/tests` half-pointer) and 2 Lows
(F5 the routed "Probed by the hunt" provenance, judged a finding; F6
the upload-precedent pointer naming the wrong module). Everything else
grades true, including all 16+2 `path::Symbol` citations (0 violations),
both spec pointers (Decision 8 verified word-for-word), the
`ValidationCache` overwrite claim (installed wheel), the 10**8 default
(ceiling fallback times the ancestor product), and the `sys.maxsize`
identity (R5, matrix-true). Open threads for Worker-0: F4 touches a file
no other finding touches (`test_resource_policy_api.py`), so as a Medium
it is implemented, not deferred; F5 discharges the plan's Routed lead on
this item. On verify: F2's fix must keep the four existing cites intact
and add only the relation family; F1's must preserve the first line and
the `_GuardedDict`/`plain-dict` coverage both params pin.

## Verify comments

Verify pass 1, fully static (no workspace copy bound; every command below
runs in the shared tree and imports nothing). Read in order: AGENTS.md,
START.md, REVIEW.md, worker-2.md, the plan incl. `## Owned changes`, all
four records whole with every Handoff, `docs/review/temp-tests/resource_policy/diff/pass-1.diff`
whole, then the three live touched files. Live item diff
(`git diff e3af1821 -- <3 paths>`) is byte-identical to pass-1.diff
(modulo `index` lines; both captured under scratch), so the pass diff is
the whole change under test and no concurrent hunk rides in these files.

Fingerprints (`git hash-object`, live): target `5b4a80f0`,
`tests/test_resource_policy.py` `a52bfb89`,
`test_resource_policy_api.py` `56b70d75` — each matches pass-1.diff's
`index` post-image. ITEM_BASELINE pre-images (`cc3f9d80`/`585c536e`/`ae7bef60`)
match the record's Trace fingerprints.

Per-finding verdicts (Proof run verbatim, then the grade-true re-check):

- F1 (Medium, mapping-rationale rewrite): PASS. `grep -c 'absorb'
  tests/test_resource_policy.py` prints `0`. First line preserved
  verbatim (`tests/test_resource_policy.py:1012`: "A MAPPING-shaped result
  is bounded via ``islice``, never a raw ``KeyError``."). Rationale true
  against the body: `_bounds_by_its_own_slice` classifies by exact type
  (`type(result) in _SLICE_BOUNDED_ROW_TYPES`), a mapping is never
  subscripted, and the non-slice path is `list(islice(result, ...))`
  (`resource_policy.py:1062,1069`); target holds zero `KeyError`/`TypeError`
  mentions (both `grep -c` print `0`). `_GuardedDict`/`plain-dict` coverage
  intact: parametrize ids `plain-dict` / `guarded-mapping-subclass` still
  pin both shapes through the same assertion, and the docstring names both
  ("a mapping - and a ``dict`` subclass whose ``__getitem__`` guards its
  keys"). Landed text matches the record's text-after modulo reflow.
- F2 (Medium, deadline-seam inventory): PASS. `grep -c 'single-object
  relation' django_strawberry_framework/resource_policy.py` prints `1`.
  All four pre-existing cites intact (each `grep -c` prints `1`):
  `bounded_rows` raw-list spellings, `connection.py::DjangoConnection.resolve_connection`,
  `relay.py::DjangoNodeField`, `mutations/resolvers.py::run_write_pipeline_sync`;
  the added clause is the relation family only, matching text-after modulo
  reflow. Inventory now true: `types/resolvers.py` carries exactly the five
  `check_deadline` call sites the clause claims (lines 630, 635, 687, 711,
  784 plus the import at 57 — forward sync + two async arms, reverse-O2O
  sync + async).
- F3 (Medium, survivor pointer): PASS. `grep -c 'iso-budget'
  tests/test_resource_policy.py` prints `0`, and `iso-budget` is gone
  repo-wide in `*.py`. Pointer resolves three ways: test
  `test_a_worker_that_outlived_a_request_is_bounded_and_published_for_itself`
  at `test_extension_isolation_api.py:843`, mount `iso-survivor/` at :532
  (and the `_post_async` default mount at :68), and the pinned behavior
  matches the banner (spawn schema admits `max_list_rows=1` at :496; the
  outlived worker reports `DEFAULT_RESOURCE_POLICY.max_list_rows` at :865 —
  its own context, not the completed request's budget).
- F4 (Medium, live-tier half-pointer): PASS. `grep -c
  'examples/fakeshop/tests'
  examples/fakeshop/test_query/test_resource_policy_api.py` prints `0`.
  Agreement fixed: "``tests/test_resource_policy.py`` holds what a live
  request cannot reach:" (singular subject, `holds`). Spot-confirmed the
  dropped claim was false: `examples/fakeshop/tests/` holds four
  project/config modules and zero policy-vocabulary hits
  (`resource_policy|max_list_rows|bounded_rows|check_deadline` case-insensitive).
- F5 (Low, hunt provenance): PASS. `grep -c 'Probed by'
  tests/test_resource_policy.py` prints `0`. Counterfactual landed
  ("(Rejecting it here would produce a typed message naming
  ``ResourcePolicy`` as the received type while claiming the value must be
  a ``ResourcePolicy``.)", wrapped at lines 340-342, matching text-after
  modulo reflow); the WHY survives as a plain clause, no attribution left.
- F6 (Low, upload-precedent pointer): PASS. `grep -c 'admission walk
  already uses' django_strawberry_framework/resource_policy.py` prints `1`;
  the old spelling (`this module already uses for an upload`) prints `0`.
  Pointer true: the limit/charged X/X+1 unmeasurable-upload rejection lives
  in `extensions/resource_policy.py::_charge_upload` (lines 821-827), and
  `resource_policy.py` defines no upload path (`def .*upload` has no hits).

Code-edit disturbance (Perf F1 None-first guard + Mech L1 widen
simplification vs graded prose): none. `_deadline_expired`'s docstring
claims only the outcome table ("Absent, cleared, ``bool``, or anything
non-numeric ... leaves the request running") — `None → None` preserves
it, and no docstring describes branch order. `check_deadline`'s docstring
("an absent, cleared, or non-numeric deadline leaves the request running")
likewise holds (`None` is falsy at the `if not _deadline_expired(...)`
seam). `narrowed`'s docstring states the narrowing contract only, never
the conjunct shape; `__post_init__`'s "an invalid policy cannot exist" is
the invariant the simplification relies on and is untouched. Every
docstring claim graded true in the record still reads true over the new
bodies.

Citations: `check_citations.py --paths <3 touched files> --substrings
--json` → `OK: 18 citations resolve (18 in 3 named file(s); 0 of them
substring pinpoints)`, 0 violations, 0 warnings (16 target + 2 test-module,
matching the record's baseline; full JSON under scratch).

Provenance sweep over the 26 added lines (REVIEW.md pattern): the only
hits are the F3 live-test identifier containing "worker" (the test's own
name, not process attribution); "background task" is behavioral. No
`we`/`you`/`I`, no `Tests that`/`Ensures`, no `.py:NN` refs. The one
`silently` in added text ("bound silently stops applying") is the kept
behavioral phrase carried verbatim from text-before (R9 shape).

No new defects found on this axis; no `verify <n>` finding owed. The two
routed/home-elsewhere twins (R10/R11) are untouched, correctly — out of
this item's fence.

Scratch: `docs/review/temp-tests/resource_policy/verify-comments-1/`
(`added.txt`, `citations.json` + `.stderr`, `fingerprints.txt`,
`live-item.diff`, `pass-noindex.diff`, `live-noindex.diff`).

Status: verified

Handoff: This pass is complete and self-contained: all six Proofs print
their prescribed counts, every landed docstring/banner re-grades true
against its body plus one real caller or sibling artifact, citations are
clean, and the item diff is drift-free versus live. Beyond the verdict:
the F2 clause's `types/resolvers.py` cite is a bare-module cite (no
`::Symbol`), consistent with its neighbours' mixed cite styles and
outside the citation gate's `::Symbol`-only scope — true but ungated, so
a future resolver rename would stale it silently; no action (R7 trigger
covers spec pointers only). No open threads.
