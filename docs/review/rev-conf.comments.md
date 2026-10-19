# Review · Comments: `django_strawberry_framework/conf.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=0ec338aef4e12fe5930ce0839d10d93ec3403c6d

## Trace

Read the whole live target (`django_strawberry_framework/conf.py`, 570 lines:
module docstring, 11 key-constant comment blocks, `_LIVE_UNSET` comment,
`_normalize_user_settings` + 13 function/method docstrings, 9 inline comments,
the pytest-guard comment, the import-time wiring comment) and the whole own
test module (`tests/base/test_conf.py`, 605 lines: module docstring, 29 test
docstrings, 8 undocumented tests, 6 section banners, 7 inline comments).
No sibling axis records existed at dispatch (only `rev-conf.md`, `Status:
reviewing`); required reading was AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan, and `rev-conf.md`. The target and its test module
are dirty with concurrent work (per the dispatch and `git status`); every
grade below is against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/conf/comments/inspect/` plus
`docs/review/temp-tests/conf/comments/conf.json`.
`build_tree_md.py --list-docstrings` passes on the target and on
`tests/base/test_conf.py` (1 module, 0 breaking, each).
`check_citations.py --paths <file> --substrings --json` reports 16
citations, 0 violations in the target and 1 citation, 0 violations in the
test module. Provenance sweep (REVIEW.md pattern, regex mode) on the
target hits only `no longer` (module docstring, R2), five kept
spec-Decision pointers (all verified below), and on the test module only
`discarded` (a `card` substring false positive). No `we`/`you`/`I`, no
`Tests that`/`Ensures`, no `.py:NN`, no public symbol without a docstring
in either file.

Contract trace, each claim checked against its body and one real caller:
`types/base.py::_meta_optimizer_hints` (None → `{}`) and
`_validate_relation_shapes` (key-guard precedent); the optimizer's
`getattr(..., None) or {}` sites (walker, selections, nested_planner,
extension); the four patch `apply()` gates (each calls
`upstream_patches_enabled` exactly once, with its own name; nothing else
in production calls it; not exported from the package `__init__`);
`_strawberry_patches.py` + `_cross_web_patches.py` module docstrings
(joint ownership, envelope guard riding the gate on package mounts);
`views.py::_resolved_max_request_body_bytes` (precedence + validation),
`_RawBodyRequestAdapter` + `_RequestBodyBoundaryMixin` (wire-contract
scoping); `testing/client.py` (precedence ladder, construction + per-call
reads, `TestClient.__test__` guard); `filters/inputs.py::_build_input_fields`
(`bool()` coercion at the consumer) plus upstream
`django_graphene_filters/conf.py` (`HIDE_FLAT_FILTERS: False`);
`types/relay.py::_validated_globalid_setting` (shared validator, snapshot)
and `types/base.py::DEFAULT_GLOBALID_STRATEGY`; `resource_policy.py` /
`error_policy.py` resolvers (kwarg > setting > defaults, once at schema
construction) and their `__post_init__` messages; `ResourcePolicy` fields
(every bound a positive int except the default-None deadline: no
off-switch spelling); `extensions/error_policy.py` (DEBUG-conditional
masking); `optimizer/nested_fetch.py::resolve_strategy` (setting read +
unknown-name `ConfigurationError`) called at extension construction;
`optimizer/single_parent_fetch.py` (fetch-time read);
`schema.py::DjangoSchema`, `testing/__init__.py`, `types/definition.py`,
`types/finalizer.py`, `utils/inputs.py`, `orders/inputs.py`,
`optimizer/hints.py`, `utils/policies.py` prose (all consistent);
spec-043 Decision 7, spec-031 Decision 5, spec-046 Decisions 7 (incl. step
4) and 8, spec-048 Decision 7 (all resolve and say what the comments
claim); every live-tier and package-tier pin named by the test module
docstring (all exist; the `ERROR_POLICY` / `RESOURCE_POLICY` settings keys
have zero live pins — only `DEFAULT_*` hits); 47 docstrings in other test
modules mentioning conf symbols (extracted to
`docs/review/temp-tests/conf/comments/other-prose.txt`, graded in
Findings/Rejected).

Cells: sharded and pg `inapplicable by construction` — the target reads
Django settings only and reaches no database, alias, or dialect decision.
One workspace run, default cell (mechanism probe for F2).

Fingerprints (`git hash-object`; target + own tests full, rest 12-char):
target `ae3de0a36e2f7737a2c8350e532cdb761b295bcf`;
`tests/base/test_conf.py`
`55b333eb2fff714365058d0a8651fc3a57c603e3`;
spec-043 `a31a06f1322f`, spec-031 `45f43dfee647`, spec-046
`8d8adaf2f2f0`, spec-048 `c1a11bdbd632`; `types/base.py`
`dc67f084cbc9`, `optimizer/walker.py` `d5759ef8533a`,
`optimizer/nested_fetch.py` `1678609e8f33`, `optimizer/extension.py`
`39a8739c7e56`, `optimizer/single_parent_fetch.py` `e995270af9b2`,
`optimizer/hints.py` `8b545718c2f7`, `optimizer/selections.py`
`b189fa156399`, `optimizer/nested_planner.py` `d32d1b7bd872`,
`views.py` `48ee582ecdba`, `testing/client.py` `b14394431f88`,
`testing/__init__.py` `48b45d1b4332`, `filters/inputs.py`
`a932dbf85d89`, `types/relay.py` `4b2a9df59d6c`,
`types/definition.py` `1c59a3feec53`, `types/finalizer.py`
`b9d8acb2b942`, `resource_policy.py` `cc3f9d80b9d5`,
`error_policy.py` `57a0bed1ba73`, `extensions/error_policy.py`
`a1defd394d8e`, `_django_patches.py` `6918a213170e`,
`_strawberry_patches.py` `90f711fb420b`, `_cross_web_patches.py`
`52bf8f5712d6`, `_graphql_core_patches.py` `90ac4f3cc15b`,
`utils/policies.py` `0a2b7dbad965`, `utils/inputs.py`
`b5af8255dfa1`, `orders/inputs.py` `2d258da74ee36`, `schema.py`
`84f2d5aa51a1`, `registry.py` `492654d219d1`, `exceptions.py`
`206e9f8d914f`, `__init__.py` `0ef72601ecac`, `apps.py`
`8ae1a3a3b12f`; `tests/test_views.py` `3f9c81153f4f`,
`tests/test_apps.py` `fe912987087b`, `tests/test_django_patches.py`
`6e62c784389b`, `tests/test_strawberry_patches.py` `c06add916e03`,
`tests/test_cross_web_patches.py` `70c16389aa5d`,
`tests/test_graphql_core_patches.py` `53dca51737e6`,
`tests/test_error_policy.py` `0f0fec24b03c`,
`tests/test_resource_policy.py` `585c536e65ab`,
`tests/testing/test_client.py` `517cf1e680f1`,
`tests/filters/test_inputs.py` `c5422da54cf3`,
`tests/filters/__init__.py` `7d727220a1de`,
`tests/optimizer/test_nested_fetch.py` `0b65aa963f03`,
`tests/types/test_base.py` `bb56c89bbcad`,
`tests/types/test_relay_interfaces.py` `3ffb75b82487`,
`test_transport_api.py` `6d65274f9e7b`, `test_library_api.py`
`2cd1b6dd1a2f`, `test_client_api.py` `4a04369dcae7`,
`test_products_api.py` `fe78cf9d4862`, `test_error_policy_api.py`
`6763a5814987`, `test_resource_policy_api.py` `ae7bef601732`,
`test_single_parent_fastpath_api.py` `492fac736277`. A finding's
Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

- Observation: the `UPSTREAM_PATCH_DEPENDENCIES` comment states `A
  package view is unaffected by every state of this setting`. That is
  false for the body-envelope guard. A package view rides the gate for
  the scalar/non-object-batch guard exactly as Strawberry's own view
  does: with the `strawberry` half off, the same scalar body 500s on a
  package mount. Only the strict UTF-8 wire contract (decode + body
  source) survives every state.
- Evidence: `_strawberry_patches.py` module docstring (`What the gate
  does NOT scope is the mount ... with the gate off, b"42" and b"[1,2]"
  come back out of a real DjangoGraphQLView's parse_json ... turns each
  into an unhandled 500 there too - pinned on the wire, against the
  package mount`; `What a package view keeps in every state of this
  setting is the strict UTF-8 wire contract`); the live pin
  `test_transport_api.py::test_the_upstream_bug_workaround_still_respects_its_own_opt_out`
  (unguarded 500 vs guarded 400 on the same mount); `views.py`
  `_RawBodyRequestAdapter` / `_RequestBodyBoundaryMixin` docstrings,
  which scope the every-state claim to the wire contract (`so the
  decode is reached in every patch state`; `Both are permanent package
  policy ... neither depends on ... APPLY_UPSTREAM_PATCHES` — of the
  cap and the decode).
- Impact: a consumer trusting the sentence believes opting out changes
  nothing on a package mount; opting out `strawberry` turns scalar-body
  400s into 500s there. Wrong contract for the switch's scope.
- Severity: Medium (stale comment stating the wrong contract; a comment,
  not a docstring, so below High).
- Recommendation: scope the sentence to the wire contract and name the
  envelope-guard exception; see text-after.
- Must not change: n/a.
- Proof: `grep -c "A package view is unaffected by every"
  django_strawberry_framework/conf.py` prints `0` (1 today, line 69);
  the rewritten comment earns grade true (wire contract in every
  state, envelope guard riding the gate, both halves named).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/conf.py::UPSTREAM_PATCH_DEPENDENCIES`.
- Grade: stale.
- Text-before:
  `A package view is unaffected by every state of this setting - it owns both its strict decode and its own body source (``views.py::_RawBodyRequestAdapter``).`
- Text-after:
  `A package view keeps the strict UTF-8 half of that hardening in every state of this setting - it owns both its strict decode and its own body source (``views.py::_RawBodyRequestAdapter``) - but it rides the gate for the body-envelope guard: with the ``strawberry`` half off, a scalar or non-object-batch body is an unhandled ``500`` on a package mount too.`

- Observation: the `__getattr__` inline comment claims the internal
  `self.user_settings` read must stay a `@property` `to avoid recursive
  lookup on malformed config raising ConfigurationError inside this
  handler`. No such recursion exists. A `ConfigurationError` propagates
  straight out of the handler (only `AttributeError` retries lookup);
  the single re-entry happens when the lazy load raises
  `AttributeError`, retries once as `"user_settings"`, and is cut by
  the guard set above — not by `@property`-ness.
- Evidence: the guard set (`user_settings`, `_user_settings`,
  `_live_source`, `_django_backed`, dunders) terminates any re-entry;
  `tests/base/test_conf.py::test_settings_normalization_attribute_error_does_not_recurse`
  (AttributeError surfaces as `AttributeError("user_settings")`,
  proving the one guarded re-entry) and
  `::test_django_backed_resync_fails_loud_after_silent_bad_replacement`
  (malformed config raises `ConfigurationError` directly through both
  `user_settings` and attribute reads, repeatedly); both pass in the
  workspace probe `review-20260928T234638-42d1fa` (2 passed). No
  construction makes `ConfigurationError` re-enter lookup.
- Impact: wrong stated reason for keeping `@property` (DRY principle
  10: worse than none); a reader trusting it misunderstands both the
  `ConfigurationError` path (direct propagation) and the actual
  recursion guard (the name set).
- Severity: Medium (stale comment on internal code).
- Recommendation: keep the true first clause, replace the reason with
  the real mechanism; see text-after.
- Must not change: n/a.
- Proof: `grep -c "recursive lookup on malformed config"
  django_strawberry_framework/conf.py` prints `0` (1 today, line 339);
  the rewritten comment earns grade true (descriptor fact kept;
  AttributeError re-entry + guard cut + ConfigurationError
  straight-out all stated).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/conf.py::Settings.__getattr__`.
- Grade: stale (wrong stated reason).
- Text-before:
  ` ``self.user_settings`` is a descriptor (``@property``), not a ``__getattr__``-driven lookup; keep it a ``@property`` to avoid recursive lookup on malformed config raising ``ConfigurationError`` inside this handler.`
- Text-after:
  ` ``self.user_settings`` is a descriptor (``@property``), so this internal read resolves without routing through ``__getattr__`` - until the lazy load itself raises ``AttributeError``, which retries lookup once as ``"user_settings"`` and is cut by the guard above. A ``ConfigurationError`` from the lazy load propagates straight out.`

- Observation: the `_normalize_user_settings` docstring's sharer
  inventory — `Shared by Settings.__init__ (eager construction),
  Settings.user_settings (lazy read ...), and Settings.reload
  (signal-driven and direct cache replacement) so a single shape
  contract applies across every cache write site` — misattributes the
  signal path and omits a sharer. The setting-changed receiver uses
  `_reload_from_django`, not `reload` (`reload`'s own docstring says
  so); `reload` only meets the signal path on the `None` leg
  (`_reload_from_django` delegates `reload(None)`). And
  `_reload_from_django` calls `_normalize_user_settings` itself, so it
  is a fourth sharer and cache write site the `every cache write site`
  sentence does not name.
- Evidence: call-site census of `_normalize_user_settings` in the
  target: `__init__` (line 232), `user_settings` (277), `reload`
  (299), `_reload_from_django` (308) — four writers, three named;
  `reload_settings` delegates to `settings._reload_from_django`;
  `reload` docstring (`The setting-changed receiver uses
  _reload_from_django instead`).
- Impact: a reader auditing `every cache write site` via this list
  misses the actual signal writer and misattributes signal-driven
  replacement to `reload`, whose mapping leg would break django
  backing if used as the receiver.
- Severity: Medium (stale docstring on internal code).
- Recommendation: complete the inventory and attribute the signal path
  to `_reload_from_django`; see text-after.
- Must not change: n/a.
- Proof: `grep -c "signal-driven and direct cache replacement"
  django_strawberry_framework/conf.py` prints `0` (1 today, line 190);
  the rewritten sentence earns grade true (all four sharers named;
  signal path attributed to `_reload_from_django` with its
  keeps-backing note).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/conf.py::_normalize_user_settings`.
- Grade: stale.
- Text-before:
  `Shared by ``Settings.__init__`` (eager construction), ``Settings.user_settings`` (lazy read from ``django.conf.settings``), and ``Settings.reload`` (signal-driven and direct cache replacement) so a single shape contract applies across every cache write site.`
- Text-after:
  `Shared by ``Settings.__init__`` (eager construction), ``Settings.user_settings`` (lazy read from ``django.conf.settings``), ``Settings.reload`` (direct cache replacement) and ``Settings._reload_from_django`` (the ``setting_changed`` path, which keeps django backing) so a single shape contract applies across every cache write site.`

### Low

- Observation: the `test_transport_api.py` module docstring's final
  section describes the broad-switch state as
  `(APPLY_UPSTREAM_PATCHES = False, both patch modules un-installed)`.
  The switch governs four patch modules
  (`UPSTREAM_PATCH_DEPENDENCIES`: `cross_web`, `django`,
  `graphql_core`, `strawberry`); `both` is the body-parse pair under
  test, but the parenthetical reads as the switch's scope. The file's
  own helper vocabulary (`takes both halves out`) scopes it correctly.
- Evidence: `UPSTREAM_PATCH_DEPENDENCIES` (four names); the helper
  `_every_upstream_patch_opted_out` (`takes both halves out`, two
  `_patch_is_installed` probes); the simulated state uninstalls the
  pair while the literal broad-`False` state uninstalls all four.
- Impact: bounded clarity; a reader learning the switch's scope from
  this sentence learns two members instead of four.
- Severity: Low.
- Recommendation: adopt the file's own `halves` vocabulary; see
  text-after. Expect `deferred` if no higher finding touches this file.
- Must not change: the surrounding `used to ... It is now` clauses
  (graded true, R7).
- Proof: `grep -c "both patch modules un-installed"
  examples/fakeshop/test_query/test_transport_api.py` prints `0` (1
  today, line 46); the rewritten parenthetical earns grade true
  (names the simulated pair state without restating the switch's
  cardinality).
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_transport_api.py::<module>`.
- Grade: stale (imprecise cardinality).
- Text-before:
  `(``APPLY_UPSTREAM_PATCHES = False``, both patch modules un-installed)`
- Text-after:
  `(``APPLY_UPSTREAM_PATCHES = False``, both body-parse patch halves un-installed)`

## Rejected

- R1 — `Whether ...` (3) and `The configured ...` (6) function first
  lines are not imperative. Package-wide convention for predicates
  (66 `Whether`-opening function docstrings) and a uniform file-local
  family convention for the thin readers (all 6 `The configured`
  openings are this file's); rewriting to `Return ...` is style
  preference, and changing 3 of 66 would make the file inconsistent
  with the package. Trigger: a maintainer decision enforcing
  imperative mood on predicates/readers, applied package-wide.
- R2 — module docstring `*Other* invalid shapes are no longer
  defensively coerced here ... rather than the old or {} collapse`.
  True stated reason: warns future editors against reintroducing
  falsy-coercion where the optimizer's `or {}` idiom (verified live
  sites) tempts it. Same accepted shape as a verified item's `used to
  live ... no longer does`. Trigger: a rewrite to pure present tense.
- R3 — module docstring `Tightening the None cases to raise is
  deferred; until then ...`. Records deliberate leniency (preempts
  `why doesn't this raise?`); names no process artifact (no card,
  round, worker, review); the contract sentence stands on its own.
  Trigger: the tightening landing, or the maintainer barring
  plan-language in module docstrings.
- R4 — `test_conf.py` `once leaked TypeError ... the key-type guard
  runs first`. True stated reason for the guard order, verified
  against the body and pinned by the `{1: False, "x": False}` test;
  history serves the present design fact. Trigger: guard order change.
- R5 — `test_conf.py` `Closes the old bool() coercion's silent
  wrong-shape acceptance`. States the rejection rows' purpose; every
  present-tense claim true and pinned. Trigger: none (purpose stands).
- R6 — `test_conf.py` `keeps its pre-mapping semantics (back-compat)`.
  Present contract (`False` disables all) with lineage gloss; true.
  Trigger: the bool shape removed.
- R7 — `test_transport_api.py` module `the state in which the sync
  transport used to answer 500. It is now the same controlled 400`.
  Both clauses true (historical wire measurement + present constancy
  pin the rows prove); wire-behavior history motivating regression
  rows, not process residue (names no round/worker/review/card/site).
  Trigger: an owning item de-narrating; wording stands as true.
- R8 — `tests/test_views.py` `With APPLY_UPSTREAM_PATCHES = False that
  made the mounted sync view answer 500 ... measured`. Same class as
  R7; the views item is out of scope this run, wording is its to
  judge. Trigger: the views item scoping.
- R9 — `_normalize_user_settings` `preserves identity so tests that
  capture the same dict by reference observe their mutations`. True
  under the generic-conditional reading (identity is real: `type(x)
  is dict` returns as-is; any capturer observes mutations); the
  `user_settings` docstring states the same semantic
  beneficiary-free. No in-tree test captures-then-mutates, but none is
  claimed existentially. Trigger: an existential reading adopted.
- R10 — `single_parent_fast_path_setting` docstring missing
  double-backtick markup around the key and terser than its siblings.
  Markup/style only; content true; no looks-for entry covers markup.
  Trigger: a markup-consistency pass.
- R11 — 8 undocumented test functions (attribute-error, preset-value,
  mapping-values, reload x3, set-true rows). Names state the expected
  behavior; no looks-for entry requires test docstrings. Trigger: none.
- R12 — `upstream_patches_enabled` `the only callers are the four
  patch modules' apply() gates`. Production callers: verified 4 call
  sites, each once, each inside its module's `apply()`; test callers
  of an internal API do not make it public. Trigger: a fifth
  production caller.
- R13 — module docstring's optimizer `or {}` sentence vs the
  `definition.optimizer_hints or {}` sites (walker, extension). Those
  are framework-internal, not reflective upstream reads, so outside
  the sentence's subject; the coercion there is vacuous-but-correct.
  Trigger: the sentence reworded to quantify over all `or {}`.
- R14 — `_every_upstream_patch_opted_out` `takes both halves out`.
  `halves` precisely scopes the body-parse pair (contrast F4's
  `modules`). True; lends F4's text-after its vocabulary. Trigger: none.

## Routed leads

- Routed: `django_strawberry_framework/_cross_web_patches.py` module
  docstring — `The gate covers upstream defects only, and a package
  view does not consult it`. Literally true (package views never call
  the gate: the only production call sites are the four `apply()`
  gates), but it implies the behavioral independence F1 disproves for
  the envelope guard (a defect workaround the package mount rides).
  Owner: the `_cross_web_patches.py` item, out of scope this run, so
  Worker-0 to `## Decisions`. Suggested judgment: scope to the wire
  contract the way `views.py` does, or clarify `consult` as `call`.
- Already homed, not re-raised: `testing/_wrap.py` module docstring
  (`AppConfig.ready installs unconditionally` vs the
  `APPLY_UPSTREAM_PATCHES = False` early return) sits in the plan's
  `## Decisions` (owner: `testing/_wrap.py`).

## Cross-axis

None. No performance or mechanics finding arose from this pass: the
module is settings plumbing (dict reads, one copy per validation),
every cost-relevant shape (`type(x) is dict` fast path, single-copy
validation, fetch-time flag read) is deliberate and documented, and
the aliasing semantics (identity-preserving caches) are stated in the
docstrings that establish them.

Handoff: I graded every docstring and comment in the target (1 module
docstring, 11 key comments, 14 function/method docstrings, 12 inline
comments) and its own test module whole (module docstring, 29 test
docstrings, 6 banners, 7 inline comments), plus 47 docstrings in other
test modules mentioning conf symbols and every package module citing
the conf surface: 3 Mediums (F1 package-view overclaim, F2 wrong
recursion reason, F3 sharer inventory) and 1 Low (F4 switch
cardinality in the transport module docstring, likely deferred — no
higher finding touches that file). Everything else grades true,
including all five spec-Decision pointers (each verified against its
spec's decision text), all 17 `path::Symbol` citations (0 violations),
the `Whether`/`The configured` first-line families (R1: package and
file conventions beat the imperative rule here), and the wire-history
clauses (R7/R8: true regression motivation, distinct from the
review-residue wording the flow routes). One workspace run
(`review-20260928T234638-42d1fa`, 2 passed) empirically pins F2's
mechanism. Open threads for Worker-0: the cross_web routed lead (its
item is out of scope → `## Decisions`); the true-but-narrative
wordings in `tests/types/test_base.py` (`no longer reads`),
`tests/types/test_relay_interfaces.py` (`new fail-loud scope`,
`prior ... design`), `tests/test_resource_policy.py` (`Probed by the
hunt`) and `tests/filters/test_inputs.py` (bare `Decision 11`) belong
to their items' Comments passes, not this one — observed, not graded.
On verify: F1's fix must keep the joint-ownership first half intact;
F2's must not reintroduce a `ConfigurationError`-causes-lookup claim
in any form; F3's must name all four writers (census: conf.py lines
232/277/299/308).

## Verification (Comments)

Verify pass 1, address `review/conf.py/verify-comments-1`, item
scratch root `docs/review/temp-tests/conf/`, this pass under
`verify-comments-1/`. Required reading done in order (AGENTS.md,
START.md, REVIEW.md, worker-1.md, the plan incl. its `## Owned
changes`, the artifact header, all three axis records with every
Handoff and Cross-axis section) plus the whole live target.

Step 1: `git diff
0ec338aef4e12fe5930ce0839d10d93ec3403c6d --
django_strawberry_framework/conf.py tests/base/test_conf.py` hashes
equal to `docs/review/temp-tests/conf/diff/pass-1.diff`
(sha256 `6baebb463903ce27a91002aa444afc0957497cebca2cbf6d004896e2f61703d9`
both sides, `diff` empty). The tree did not move under the pass.

Proof lines, run verbatim BEFORE reading `## Implementation (Worker-2)`
(static greps, shared tree, no run ids by construction):

- F1: `grep -c "A package view is unaffected by every"
  django_strawberry_framework/conf.py` prints `0`. Landed.
- F2: `grep -c "recursive lookup on malformed config"
  django_strawberry_framework/conf.py` prints `0`. Landed.
- F3: `grep -c "signal-driven and direct cache replacement"
  django_strawberry_framework/conf.py` prints `0`. Landed.
- F4: `grep -c "both patch modules un-installed"
  examples/fakeshop/test_query/test_transport_api.py` prints `1`.
  Deferred, still present — confirmed and stated.
- Other records' Cross-axis (for Comments): the Performance record
  carries no `## Cross-axis` section and the Mechanics record carries
  none either; this record's own `## Cross-axis` states `None`.
  Nothing to run.

Grades, each as the whole docstring or comment block it sits in:

- F1 (`UPSTREAM_PATCH_DEPENDENCIES` comment block, conf.py lines
  63-75): true. The rewritten sentence scopes the every-state claim
  to the strict UTF-8 wire half, names the body-envelope-guard
  exception with its `500`-on-a-package-mount consequence, and both
  halves are named (`strawberry` in the new sentence, `cross_web`
  in the intact joint-ownership lead, lines 65-68, byte-unchanged
  per the diff). The `views.py::_RawBodyRequestAdapter` citation
  sits whole on one line and resolves (citations below).
- F2 (`Settings.__getattr__` comment, conf.py lines 342-347): true.
  Descriptor fact kept; the `AttributeError` re-entry plus guard
  cut plus `ConfigurationError`-straight-out mechanism all stated,
  each verified against the body (Attacks). No
  `ConfigurationError`-causes-lookup claim in any form.
- F3 (`_normalize_user_settings` docstring, conf.py lines 171-197):
  true. All four sharers named with the signal path attributed to
  `_reload_from_django` and its keeps-backing note; the untouched
  remainder (Branches inventory, R9 identity sentence) still reads
  true against the body. All three texts-after match the record
  sentences verbatim modulo line wrapping (mechanical join-and-
  compare; F1's first slice overran into adjacent sentences and
  was re-bounded, then matched).
- New test row docstring
  (`test_setting_reader_helpers_return_wrong_typed_values_verbatim`,
  test_conf.py lines 375-383): true. States the expected behavior
  (no `Tests that`/`Ensures`), counts right (the other five
  readers; the single-parent rows live where it points), and every
  downstream site it names exists (`optimizer/nested_fetch.py:417`,
  `views.py:160`, `types/relay.py:388`,
  `filters/inputs.py:873`); the endpoint's `None` is wrong-typed
  against the declared `-> str` contract the row pins past.

F4 deferral judgment: the ride rule is correctly applied. F4 is Low;
no finding of any severity touches `test_transport_api.py`
(Performance: none; Mechanics F1: conf.py + test_conf.py; Comments
F1-F3: conf.py), the file's blob is unchanged
(`6d65274f9e7b5589d60777d7e0484b3ad10df394`, equal to this
record's Trace fingerprint), Worker-2 recorded the deferral with
its reason, and the Proof still prints `1`. It stays visible for
`## Outcomes`.

Inverse prose-only proof (own rebuild, Worker-2's file not reused):
`verify-comments-1/reconstruction/conf.py` is the ITEM_BASELINE
text plus exactly the 7 Mechanics code hunks (import + 6
annotations), each replacement asserted to match exactly once at
build time. It hashes `ef7f2f9e...`, identical to Worker-2's
independently built file; `diff` reconstruction-vs-live shows only
the three prose hunks above; `review_inspect.py --code-digest
<reconstruction> <live>` prints two equal digests
(`sha256:9dd8dac3...`, exit 0). The Comments hunks move no code.

Instruments (shared tree, no run ids by construction):

- `build_tree_md.py --list-docstrings` on conf.py and test_conf.py:
  1 module, 0 breaking, each.
- `check_citations.py --paths <file> --substrings --json`: conf.py
  16 citations, 0 violations, 0 warnings (the F1 citation resolves
  at its new line 71); test_conf.py 2 citations, 0 violations —
  both pre-existing at ITEM_BASELINE (lines 78, 272), so this
  record's Trace line saying "1 citation" undercounted by one;
  not a gap, neither is in the diff and both resolve.
- Prose diff via the REVIEW.md Comments command into
  `verify-comments-1/diff/diff/`: exactly the 3 conf.py prose
  hunks (none `[code changed too]`) plus the new test row
  (marked `[code changed too]`, as a new test must be).
- Added-lines sweep (56 `+` lines): 0 provenance hits (REVIEW.md
  pattern), 0 `we`/`you`/`I`, 0 `.py:NN` refs, 0 `Tests
  that`/`Ensures`.
- No module first line changed: both baseline first lines are
  byte-identical to live, the diff touches no module docstring,
  and it names only the two owned paths — no TREE.md row owed.

Sibling verifiers: no gaps routed to Comments. Performance
Verification routes nothing; Mechanics Verification concurs on the
F2/F3 mechanisms (its own AST census matches mine) and states
prose-truth is this pass's grade with no contradiction.

Attacks (all hold, recorded, owing nothing):

- A1 F1 wire claim: `_strawberry_patches.py` lines 27-33 state the
  unguarded `data.get("query")` turns scalar/non-object bodies
  into `an unhandled 500 there too - pinned on the wire, against
  the package mount`, naming the same live pin the finding cites.
- A2 F1 citer rot (Worker-2 handoff thread 2): `--cited-by
  views.py::_RawBodyRequestAdapter` reports 10 citing sites, 0
  unresolved; citations are symbol-addressed, so the rewrap to a
  new line cannot rot any citer by construction.
- A3 F2 mechanism: the guard set holds `"user_settings"` (conf.py
  lines 334-339); only `KeyError` is caught (341-350); the
  `__getattr__` docstring independently states the
  `ConfigurationError` propagation (325-329).
- A4 F3 inventory: `_normalize_user_settings(` call sites are
  exactly lines 237/282/304/313 (`__init__`, `user_settings`,
  `reload`, `_reload_from_django`), no fifth; the receiver
  `reload_settings` (557, connected at 577) delegates to
  `_reload_from_django` (569); backing is kept on both its legs
  (`_django_backed = True` at 316; `reload(None)` at 311, backed
  at 302).
- A5 new-row docstring: 5 readers asserted, 5 named in the
  parenthetical's downstream map modulo the endpoint (whose
  `None` surfaces at `Client.post` per the endpoint docstring —
  the "surfaces downstream, never here" claim holds for all
  five); bare `resolve_strategy` is unambiguous in context (the
  nested-strategy consumer).
- A6 whole-diff read: 10 conf.py hunks + 1 test hunk, all
  attributed (7 Mechanics code, 3 Comments prose, 1 Mechanics
  test); no prose hunk touches code, no code hunk touches prose.

Disputes: none. `grep -ci 'disputed:' docs/review/rev-conf.md`
prints `0`; Worker-2 records no `disputed:` and implemented every
in-scope finding.

Cells: sharded and pg `inapplicable by construction` — concur
with all three axis records (settings-plumbing prose plus one
package-tier test asserting pure-Python return values; no
database, alias, or dialect decision). Cells unverified: none.
No workspace run was needed: every proof above is static.

Fingerprints (`git hash-object`): conf.py live
`3820c575bfd4e3c384244d1bed460b75d3bb7681` (== Worker-2's
post-edit print); test_conf.py live
`7275af6887559055b90f4d83a088abfcd6c0ff5f` (== Worker-2's);
pass-1.diff `c90e8a93ebd0ac7dd67902d606e138518710d7f4`; own
reconstruction `ef7f2f9e692d7cde8991765371e1557e5f307514` (==
Worker-2's); rev-conf.md `fc6938cb9703a972023e6183b80d2ba6d3127964`;
rev-conf.comments.md `dee8785d037c7e3df673172019eeb79734d16854`
(pre-verification); rev-conf.mechanics.md
`0e98fff9bbe27b6c82ead7c540dbec6e2b47a8b6`;
rev-conf.performance.md `7051416263523c610bb6475c81df81bef2b1b487`;
review-0_0_15.md `cb20da7e98d0d060ec7f6799527c7e917cab25c1`;
HEAD `0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`.

Verdict: `Status: verified`. Comments F1-F3 implemented as
proposed and grade true as landed; F4 correctly deferred with
its file untouched; the prose hunks move no code.

Handoff: Verification is closed with no new findings and no gaps.
Everything beyond this record's trace that I read: the plan's
ledger (no row for this target yet — Worker-0 writes it at
closeout), Worker-2's Implementation (whole-diff claims checked
against pass-1.diff hunk by hunk), the live target and test
module in the changed regions, the `_strawberry_patches.py`
envelope-guard paragraph, and both sibling verifications (no
routed gaps; mechanisms concur). Two notes for Worker-0, neither
a gap: (1) this record's Trace says "1 citation" for
test_conf.py but the file holds 2, both pre-existing and
resolving — the review count, not the tree, was off; (2) the F4
deferral stands unless a later item touches
`test_transport_api.py`, per Worker-2's open thread. Scratch kept
under `docs/review/temp-tests/conf/verify-comments-1/`
(reconstruction, prose diff, added-lines sweep); no workspace
copy was created, so nothing needs releasing.
