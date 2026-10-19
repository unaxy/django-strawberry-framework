# Review · Comments: `django_strawberry_framework/list_field.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8d5cb7ac968f96f5123ad24c3eb2e72c7249b897

## Trace

Read the whole live target (1748 lines: module docstring, 30 symbol
docstrings, the ordering-set comments, every inline comment) and the whole
own test module (`tests/test_list_field.py`, 2199 lines: module docstring,
every test/helper/class docstring, every comment). Required reading in
dispatch order (AGENTS.md, START.md, REVIEW.md, worker-1.md, the plan,
`rev-list_field.md`); sibling axis records appeared mid-pass, both
`no-findings` with no `Cross-axis` section — their handoffs leave the
plan's routed lead to this pass, and their discharges independently
corroborate three true-grades below (error-path-only wire-name reads,
floor-to-latest backref stability, `__all__` exactness). Target and own
tests are dirty vs HEAD (concurrent work on the plan's run-3 Drift lines)
but byte-identical to ITEM_BASELINE (empty
`git diff ITEM_BASELINE --` on both paths); every grade is against the
live text at the fingerprints below.

Instruments, all static in the shared tree: `review_inspect.py`
orientation + stripped source + JSON for the target and the own test
module under `docs/review/temp-tests/list_field/comments/inspect/`;
`build_tree_md.py --list-docstrings` passes on both (1 module,
0 breaking, each); `check_citations.py --paths <file> --substrings`
reports 7 citations / 0 violations in the target and 12 / 0 in the own
tests; the REVIEW.md provenance pattern plus `we`/`you`/`I`,
`Tests that`/`Ensures`, and `.py:NN` sweeps (all clean in both files);
an AST census of other-module prose naming `DjangoListField`,
`ListArgumentError`, or `list_field` (27 files, 49 units, kept in
`other-prose.txt`), every genuine unit graded below or routed.

Contract trace, each load-bearing claim against its body plus one real
caller or contract source: `relay.py::_validate_node_target` wraps
`_validate_relay_djangotype_target`, which delegates to
`_validate_djangotype_target` (node sharing is live, M1);
`connection.py:2330` shares the relay validator;
`types/base.py::__init_subclass__` (own-namespace-`Meta` early return,
one-object register-plus-assign) and `_validate_meta` (`Meta.model`
required); `_is_relay_shaped` (interfaces OR direct inheritance);
`base_queryset` (`model._default_manager.all()`); `effective_bound`
(only literal-`True` widens); `require_orderset_class` (first line of
`apply_orderset_sync`); `_input_has_active_terms` (sole production
caller is the offset guard); the capture scope (open condition ==
guard condition); `OrderSet` Min/Max to-many annotation;
`Count`/`Star` appearing in no shipped ordering path (M3); the
connection pk tiebreaker (`connection.py::_finalize_queryset`) with no
`.distinct()` in any connection or list path (M4); the optimizer
extension root gate; spec-020 Decisions 1/2/3/5/8 and spec-050
Decisions 3/5/7/8 plus DoD 17/22 (M2, M4, L1, L2, L4); the DRY
`relay-node-target-guard` trigger record; installed Django 6.1
(`_order_by_pairs`, `find_ordering_name`, `resolve_ref`,
`try_transform`, `build_lookup`, `solve_lookup_type`,
`refs_expression`, `names_to_path` pk handling, `setup_joins`,
`ordered`, the `EmptyQuerySet` instance-check metaclass) and
strawberry 0.324.0 (`DEFINITION_BACKREF`, `from_argument`,
`from_field`) for every mirrored upstream behavior; the
`validated_field_directives` caller census (connection missing from
the enumeration — routed); the two `test_library_api.py` phantom
names (zero live `.py` hits, M5/M6); the parity-block vocabulary
(36 lines, all in-block, spec-050 mirror noted, L4).

Cells: no workspace run was needed and none was taken — every
instrument above is static and every Proof is a static `grep -c`
plus a grade judgment; Worker-2's prose edits owe `--code-digest`
identity, not cell runs. Sharded and pg are inapplicable by
construction (no database-reaching probe). Cells unverified: none.

Fingerprints (`git hash-object`; target and own tests full):
target `450e87cde13edc1bfc3c4d4a161c5540d1ac5277`;
`tests/test_list_field.py`
`d78aa5e79fee14b37564f856d3d4bc74e7d9630b`;
`connection.py` `1fca6266`, `relay.py` `e75e2b66`,
`utils/querysets.py` `8fc556d5`, `resource_policy.py` `cc3f9d80`,
`types/base.py` `dc67f084`, `types/finalizer.py` `b9d8acb2`,
`orders/sets.py` `60859f2d`, `utils/directives.py` `84f770d4`,
`utils/relations.py` `05ff55b0`, `mutations/fields.py` `0e4d5ed1`,
`optimizer/extension.py` `39a8739c`, `auth/mutations.py`
`84183c89`, `__init__.py` `0ef72601`;
`test_list_field_api.py` `4c85f779`,
`test_list_field_async_api.py` `49e423ea`, `test_library_api.py`
`2cd1b6dd`, `test_glossary_api.py` `17800287`, test_query
`README.md` `0dbf3a35`, `products/models.py` `02d3ea18`;
`tests/base/test_init.py` `239648ed`,
`tests/utils/test_querysets.py` `77d45a48`,
`tests/utils/test_errors.py` `8c763a7a`,
`tests/optimizer/test_extension.py` `8b3e2e1c`,
`tests/orders/test_sets.py` `d66b482d`, `tests/test_connection.py`
`8e08b23f`, `tests/test_relay_connection.py` `fe2b2d24`,
`tests/test_resource_policy.py` `585c536e`,
`tests/test_sets_mixins.py` `23946eb5`,
`tests/utils/test_directives.py` `c8428955`,
`tests/utils/test_execution_mode.py` `bbe5f97e`,
`tests/utils/test_typing.py` `70a257a1`,
`tests/orders/test_factories.py` `4ec2ec05`,
`tests/test_graphql_core_patches.py` `53dca517`,
`tests/test_permissions.py` `c22af728`; spec-050 `73fe1127`,
spec-020 `9fdf09b1`, `dry-rule-relay-node-target-guard.md`
`5f4b74f3`; upstream Django 6.1 + strawberry 0.324.0 (mechanics
R9 covers the 0.316.0 floor for the backref seam). A finding's
Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

- Observation: `_validate_djangotype_target` opens `Shared by
  DjangoListField and DjangoConnectionField (and any future node
  field)`. The node fields exist and share it today, so the future
  framing is spent (the plan's routed lead from connection.py
  Comments). The docstring's own later sentence already says the
  registry answer `cannot mean different things to the list,
  connection and Relay node entry points`.
- Evidence: `relay.py::_validate_node_target` (backing
  `DjangoNodeField` / `DjangoNodesField`) wraps
  `_validate_relay_djangotype_target`, which delegates its base
  checks to `_validate_djangotype_target` (list_field.py line 223).
- Impact: a reader looking for the node-field sharing finds a
  future that already happened, and may duplicate the guard for a
  new node flavor instead of importing it.
- Severity: Medium (stale sharing claim on internal code).
- Recommendation: name the three live sharers; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'and any future'
  django_strawberry_framework/list_field.py` prints `0` (1 today,
  line 128); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/list_field.py::_validate_djangotype_target`.
- Grade: stale.
- Text-before:
  `Shared by ``DjangoListField`` and ``DjangoConnectionField`` (and any future node field).`
- Text-after:
  `Shared by ``DjangoListField``, ``DjangoConnectionField``, and the Relay node fields (via ``_validate_relay_djangotype_target``).`

- Observation: the factory-site async-commitment comment cites
  `(Decision 3; spec-020 Decision 1 "Async-detection asymmetry -
  intentional, not a harmonization candidate")`. Two defects in one
  parenthetical: the asymmetry section lives under spec-020
  Decision 2 (`### Decision 2 — Default resolver shape`, the
  `**Async-detection asymmetry**` paragraph), while Decision 1 is
  `Module location, mechanism, & public export` — so `spec-020
  Decision 1` misdirects; and bare `Decision 3` is ambiguous now
  that two specs govern this module (spec-020 D3 is `get_queryset
  and async symmetry`, spec-050 D3 is `one validation record
  computes both window and errors`).
- Evidence: spec-020 headings at its Decision 1/2/3 lines; spec-050
  Decision 3 title; spec-030 D3 (Relay `first`+`last` guard) and
  spec-032 D3 (root-field dispatch) excluded as unrelated to
  factory-site async commitment, leaving spec-020 D3 (`get_queryset
  and async symmetry`) the only same-subject Decision 3.
- Impact: a maintainer following the pointer lands on module
  location instead of the asymmetry rationale, and cannot tell
  which spec's Decision 3 is meant without checking both.
- Severity: Medium (wrong pointer plus R5-trigger ambiguity on
  internal code; the connection R5 exemption fails on its own
  trigger — a second same-named Decision exists).
- Recommendation: anchor both numerals to spec-020 with the
  corrected number; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Decision 3; spec-020 Decision 1'
  django_strawberry_framework/list_field.py` prints `0` (1 today,
  line 1547); the rewritten parenthetical earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/list_field.py::DjangoListField`
  (factory-site async-commitment comment).
- Grade: stale (wrong decision number; bare numeral).
- Text-before:
  `# Factory-site async commitment (Decision 3; spec-020 Decision 1`
  `# "Async-detection asymmetry - intentional, not a harmonization candidate"):`
- Text-after:
  `# Factory-site async commitment (spec-020 Decision 3; spec-020 Decision 2`
  `# "Async-detection asymmetry - intentional, not a harmonization candidate"):`

- Observation: `_APPROVED_ORDER_AGGREGATES` is introduced as
  `listed because the shipped surface emits them`, with `Min` /
  `Max` annotated `for a to-many ordering path, and a row count
  orders by Count`. Only the Min/Max half is true: no shipped
  surface orders by `Count`. `models.Count` occurs nowhere else in
  the package, and the sole `Count("*")` ordering is the live
  test control (`test_list_field_api.py::test_shipped_branches_offset_accepts_a_row_count_order`,
  which monkeypatches an `OrderSet` to annotate it) — a test
  double, not an emitter.
- Evidence: package-wide `Count` census (one hit: the set
  itself); the live control's monkeypatch body; the Min/Max
  emission at `orders/sets.py::OrderSet._resolve_order_expressions`
  (true half, kept).
- Impact: the set's own discipline (`Nothing is listed for being
  harmless-looking`, two comments up) is contradicted by its
  neighbor; a reader takes `Count` for shipped-surface output.
- Severity: Medium (wrong stated reason on internal code).
- Recommendation: scope the emission claim to Min/Max and state
  what `Count` is admitted for; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'and a row count orders by'
  django_strawberry_framework/list_field.py` prints `0` (1 today,
  line 609); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/list_field.py::_APPROVED_ORDER_AGGREGATES`.
- Grade: stale (false emission claim for `Count`).
- Text-before:
  `#: Aggregates under the same rule, listed because the shipped surface emits them:`
  `#: ``orders/sets.py::OrderSet._resolve_order_expressions`` annotates ``Min`` /`
  `#: ``Max`` for a to-many ordering path, and a row count orders by ``Count``.`
- Text-after:
  `#: Aggregates under the same rule:`
  `#: ``orders/sets.py::OrderSet._resolve_order_expressions`` annotates ``Min`` /`
  `#: ``Max`` for a to-many ordering path, and ``Count`` admits the row-count`
  `#: aggregate a consumer ordering may annotate.`

- Observation: the `DjangoListField` ordering contract says
  `Unlike Relay connection fields, flat lists do not inject a
  primary-key tiebreaker or DISTINCT`. The `Unlike` attaches to
  both halves, but only the tiebreaker half holds for the
  connection side: connections close the order with a pk terminal
  tiebreaker (`connection.py::_finalize_queryset`), while no
  connection path injects `DISTINCT` — the sole package
  `.distinct()` call is the to-many filter application in
  `filters/base.py`, a consumer-filter effect, not a connection
  injection. The contract source (spec-050 Decision 7) draws the
  contrast on the tiebreaker alone.
- Evidence: `.distinct(` census over the package (one hit,
  `filters/base.py:138`); `DISTINCT` census over
  `connection.py` (one unrelated prose hit, `distinct
  Meta.name`); `DISTINCT` census over `list_field.py` (this
  sentence only — the flat-list half is true); spec-050
  Decision 7 text.
- Impact: bounded; the field's own contract (no tiebreaker, ties
  unordered, consumer adds a unique final term) is correct, but
  the sentence teaches a false fact about connection fields on a
  public docstring.
- Severity: Medium (false contrast implication; the operative
  contract for this field is right, so not High).
- Recommendation: scope the `Unlike` to the tiebreaker and keep
  the true flat-list `DISTINCT` fact; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'or ``DISTINCT``'
  django_strawberry_framework/list_field.py` prints `0` (1 today,
  line 1505); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/list_field.py::DjangoListField`.
- Grade: stale (false implication about connection fields).
- Text-before:
  `Unlike Relay connection fields, flat lists do not inject a primary-key tiebreaker or ``DISTINCT``.`
- Text-after:
  `Unlike Relay connection fields, which close the order with a primary-key tiebreaker, flat lists inject neither a tiebreaker nor ``DISTINCT``.`

- Observation: `test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http`
  pins the shared `Manager.all()` coercion `(reached via
  ``_post_process_consumer_sync``)`. That symbol exists nowhere
  in any live `.py` file — only in archived specs, rationale,
  DRY, and build history. The live consumer-resolver entry is
  `prepared_resolver_source` (both `_wrap` colorings call it;
  the Manager coercion it runs is the pinned
  `normalize_query_source` seam).
- Evidence: repo-wide `**/*.py` grep for
  `_post_process_consumer_sync` (one hit: this docstring);
  both `_wrap` bodies in the target.
- Impact: a reader hunting the coercion's list-field entry
  finds a name the tree does not contain.
- Severity: Medium (reference by a name that no longer
  exists, in live prose about the target's pipeline).
- Recommendation: name the live entry; see text-after.
- Must not change: n/a.
- Proof: `grep -c '_post_process_consumer_sync'
  examples/fakeshop/test_query/test_library_api.py` prints `0`
  (1 today); the rewritten clause earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http`.
- Grade: stale.
- Text-before:
  `shared ``Manager.all()`` coercion (reached via ``_post_process_consumer_sync``) before`
- Text-after:
  `shared ``Manager.all()`` coercion (reached via ``prepared_resolver_source``) before`

- Observation: `test_library_api.py::test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves`
  claims `the same list_field.py lines stay pinned by the
  package companion
  test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`.
  No test by that name exists anywhere in live `.py`: spec-020's
  test plan named it, but it was never written under any name
  (no outer-nullability test exists in `tests/test_list_field.py`
  at all). The same sentence's `the throwaway-schema package
  test lacked` points at the same phantom.
- Evidence: repo-wide `**/*.py` grep for the name (one hit:
  this docstring); `outer|nullable|NON_NULL` census over
  `tests/test_list_field.py` (one unrelated hit, an ordering
  classifier comment).
- Impact: a reader hunting the package pin finds nothing; the
  live test is in fact the only pin, which is the correct
  live-first shape, not a gap.
- Severity: Medium (phantom test pin in live prose about the
  target; fix is prose-only — no package stand-in is owed).
- Recommendation: drop the companion clause; see text-after.
- Must not change: n/a.
- Proof: `grep -c
  'test_djangolistfield_non_nullable_outer_default_via_consumer_annotation'
  examples/fakeshop/test_query/test_library_api.py` prints `0`
  (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves`.
- Grade: stale.
- Text-before:
  ```text
  ``DjangoListField`` itself has no outer-nullability branch, so the same ``list_field.py`` lines stay pinned by the package companion ``test_djangolistfield_non_nullable_outer_default_via_consumer_annotation``; this live test adds the real-stack pressure the throwaway-schema package test lacked - introspection over the *composed* schema plus an end-to-end resolve over the wire.
  ```
- Text-after:
  ```text
  ``DjangoListField`` itself has no outer-nullability branch; this live test pins the rendering over the *composed* schema plus an end-to-end resolve over the wire.
  ```

### Low

- Observation: `_handle_non_queryset_rejections_async` opens
  `Decision 8 promises a rejected async-only source is never
  advanced and is closed when possible`. The summary is a true
  account of spec-050 Decision 8 (verified against its
  never-`__anext__` + `aclose`-when-present + primary-precedence
  + constructor-failure text), but the bare numeral is
  ambiguous: spec-020 Decision 8 (`Out-of-scope boundary with
  DjangoConnectionField`) exists with unrelated content, and
  both specs are named in the module docstring.
- Evidence: spec-050 Decision 8 full text (true half);
  spec-020 Decision 8 title (ambiguity); connection R5, whose
  bare-numeral exemption fails on exactly this trigger — a
  second same-named Decision.
- Impact: bounded; one wrong guess lands on an unrelated
  boundary decision.
- Severity: Low.
- Recommendation: anchor the spec; see text-after.
- Must not change: n/a.
- Proof: `grep -c '^    Decision 8 promises'
  django_strawberry_framework/list_field.py` prints `0` (1
  today, line 1261); the rewritten opening earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/list_field.py::_handle_non_queryset_rejections_async`.
- Grade: ambiguous pointer (bare spec-Decision numeral).
- Text-before:
  `Decision 8 promises a rejected async-only source is never advanced and is`
- Text-after:
  `spec-050 Decision 8 promises a rejected async-only source is never advanced and is`

- Observation: the own test module's validation banner reads
  `# Validation tests (Decision 5).` Bare numeral, same
  ambiguity: spec-020 Decision 5 (`Validation & error shapes`,
  the section's evident subject — constructor
  `ConfigurationError` rows) vs spec-050 Decision 5 (`validate,
  then visibility, ordering, and exactly one slice`), with both
  specs named in the module docstring.
- Evidence: both Decision 5 titles; the section's test bodies
  (constructor guards, matching spec-020 D5); connection R5
  trigger, as above.
- Impact: bounded; anchoring here also resolves the `the
  spec's validation test plan` pointer two lines down, which
  then has its anchor on the reader's path.
- Severity: Low.
- Recommendation: anchor the spec; see text-after.
- Must not change: n/a.
- Proof: `grep -c '# Validation tests (Decision 5)'
  tests/test_list_field.py` prints `0` (1 today, line 120);
  the rewritten banner earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_list_field.py` (validation banner).
- Grade: ambiguous pointer (bare spec-Decision numeral).
- Text-before:
  `# Validation tests (Decision 5).`
- Text-after:
  `# Validation tests (spec-020 Decision 5).`

- Observation: the two `ListArgumentError` export pins in
  `tests/base/test_init.py` narrate process: `# Package
  version literal; card 050 lands on 0.0.15 where
  ListArgumentError is exported from the package root` names
  a card, and `the 0.0.15 version cut adds ListArgumentError
  (spec-050) to this public surface` names a version cut plus
  a bare spec tag. Both pins are otherwise true (the export
  exists at the package root `__all__`).
- Evidence: read verbatim (lines 28-29, 187-188);
  `django_strawberry_framework/__init__.py` re-export +
  `__all__` entry.
- Impact: bounded; card/version-cut narrative where the
  present-tense pin belongs.
- Severity: Low.
- Recommendation: keep each pin, drop the process nouns;
  see text-after. The surrounding 0.0.14 card narrative
  (lines 180-187) is another subject's prose, observed for
  its owning item below, not graded here.
- Must not change: n/a.
- Proof: `grep -c -e 'card 050 lands' -e 'version cut adds'
  tests/base/test_init.py` prints `0` (2 today); both
  rewritten comments earn grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/base/test_init.py::test_version` +
  the `__all__` assertion comment.
- Grade: process provenance (card name, version cut, bare
  spec tag).
- Text-before:
  `# Package version literal; card 050 lands on 0.0.15 where ListArgumentError`
  `# is exported from the package root.`
  and
  `All of these cards shipped in ``0.0.14``; the ``0.0.15`` version cut adds`
  `# ``ListArgumentError`` (spec-050) to this public surface.`
- Text-after:
  `# Package version literal; this release exports ListArgumentError`
  `# from the package root.`
  and
  `All of these cards shipped in ``0.0.14``; ``ListArgumentError`` is part of`
  `this public surface.`

- Observation: the omitted/all-null parity-oracle block in
  `test_list_field_api.py` (lines 2851-3155) narrates the card
  that built it — 36 matching lines, every one inside the
  block: `legacy` across three test names, five
  helper/class/constant identifiers, one dict key, one local,
  and fourteen prose units; `pre-card` in seven docstring
  lines; `the card's` / `the card promises` in two more.
  `legacy` and card-naming are explicitly banned provenance;
  the oracle's contract (omitted/all-null spellings reproduce
  the reference pipeline byte-for-byte) is statable without
  them.
- Evidence: full 36-line census (see Proof); no live pin
  outside the file constrains a rename (the only external
  mentions name a test id that no longer exists, in frozen
  history docs); the vocabulary mirrors in-flight spec-050
  (DoD 17/22 `legacy branch` / `pre-card baseline`), so
  Worker-0 may alternatively defer this to the spec's close
  rather than drift test↔spec vocabulary mid-flight.
- Impact: bounded; one vocabulary with one mechanical fix.
  Excluded from this finding under connection R3/R4: `did
  before the argument surface existed` (line 2855) and `the
  old pipeline used` (line 2982) — past-tense threat
  accounts naming no process artifact.
- Severity: Low.
- Recommendation: rewrite to reference vocabulary per the
  map below; identifiers, test names, and prose together.
- Must not change: n/a.
- Proof: `grep -c -i -e 'legacy' -e 'pre-card' -e 'the card'
  examples/fakeshop/test_query/test_list_field_api.py` prints
  `0` (36 today, all lines 2851-3155); every rewritten unit
  earns grade true.
- Freshness: none beyond Trace.
- Symbol: the parity-oracle block in
  `examples/fakeshop/test_query/test_list_field_api.py`
  (helpers `_legacy_reference_resolver`,
  `_build_legacy_parity_schema`, `_legacy_branch_oracle`;
  class `_LegacyParityQuery`; constant
  `_COMBINED_LEGACY_QUERIES`; local `legacy_schema`; key
  `"legacy_marks"`; three test names; fourteen prose units
  including `_combined_branch_oracle`'s docstring).
- Grade: process provenance (`legacy`, `pre-card`, card
  naming).
- Text-before (prose units; identifiers follow the same map):
  `The pre-card list pipeline, composed from shipped public primitives only.`
  `The card's field, published under the GraphQL name branches.`
  `The pre-card reference resolver, published under the SAME GraphQL name.`
  `and the pre-card pipeline shipped with it too.`
  `The reference envelope's own spelling, and the one the card promises is the same request. Each is compared against the SAME legacy reference, so each owns a node rather than sharing one that stops at the first divergence.`
  `Seed the rows, run the pre-card reference, and hand back its every claim.`
  `The oracle is a test-local legacy schema publishing the same branches field name, ...`
  `Omitted and all-null arguments reproduce the PRE-CARD pipeline, not merely each other.`
  `The all-null form is compared against the legacy OMITTED response because ...`
  `The two spellings that take the combined source's legacy policy path. ...`
  `Run the pre-card reference over a union source and hand back its every claim.`
  `so the oracle is the legacy response's RAW BYTES - ...`
  `The combined-source legacy branch is held to the pre-card oracle, not to "no new error".`
  `A union source under omitted / all-null arguments takes the legacy policy path; ...`
- Text-after (map; `legacy`/`pre-card`/`the card('s)` ->
  reference vocabulary):
  `The reference list pipeline, composed from shipped public primitives only.`
  `The holder field under test, published under the GraphQL name branches.`
  `The reference-pipeline resolver, published under the SAME GraphQL name.`
  `and the reference pipeline carries it too.`
  `The reference envelope's own spelling, and the spelling held to behave as the same request. Each is compared against the SAME reference response, so each owns a node rather than sharing one that stops at the first divergence.`
  `Seed the rows, run the reference pipeline, and hand back its every claim.`
  `The oracle is a test-local reference schema publishing the same branches field name, ...`
  `Omitted and all-null arguments reproduce the reference pipeline, not merely each other.`
  `The all-null form is compared against the reference OMITTED response because ...`
  `The two spellings that take the combined source's reference policy path. ...`
  `Run the reference pipeline over a union source and hand back its every claim.`
  `so the oracle is the reference response's RAW BYTES - ...`
  `The combined-source reference branch is held to the recorded oracle, not to "no new error".`
  `A union source under omitted / all-null arguments takes the reference policy path; ...`
  Identifiers: `_legacy_reference_resolver` ->
  `_reference_pipeline_resolver`,
  `_build_legacy_parity_schema` ->
  `_build_reference_parity_schema`, `_LegacyParityQuery` ->
  `_ReferenceParityQuery`, `_legacy_branch_oracle` ->
  `_reference_branch_oracle`, `_COMBINED_LEGACY_QUERIES` ->
  `_COMBINED_REFERENCE_QUERIES`, `legacy_schema` ->
  `reference_schema`, `"legacy_marks"` -> `"reference_marks"`;
  test names drop their `legacy`/`pre-card` words the same way
  (`..._reproduces_the_reference_bytes`,
  `..._matches_the_reference`,
  `..._a_combined_reference_spelling_matches_the_reference`).

### Verify 1

- Observation (V1): the M5 docstring cites
  ``examples/fakeshop/test_query/README.md #"Coverage rule"``, but that
  quoted text no longer exists in the cited file: `**Coverage rule.**`
  was deleted from the README by the manual rewrite in `8b3b9ae1`
  (added in `b2b08daa`), and no case-insensitive match remains. The
  live rule is the `Live-first, both verdicts, and the must-not`
  paragraph (README line 42). The sentence's claim — this coverage
  must land in `test_query/`, not `tests/test_list_field.py` — is
  still true; only the pinpoint is stale. Pre-existing (identical at
  ITEM_BASELINE), but it sits in a symbol this item touched, so it
  rides per worker-1 Verify step 6.
- Evidence: `grep -i -c 'coverage rule'
  examples/fakeshop/test_query/README.md` prints `0`;
  `check_citations.py --paths ... --substrings` reports the line-1059
  pinpoint unresolvable (`--check` stays green: substring pinpoints
  are ungated); `git log -S'Coverage rule'` shows the add/remove pair.
- Impact: a reader following the pinpoint finds nothing in the README.
- Severity: Low (stale pinpoint in test prose; the claim it pins is
  true). Rides `test_library_api.py`, changed for Mediums M5/M6, so it
  is implemented, not deferred.
- Recommendation: re-pin to live one-line README text, kept on one
  source line; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'README.md #"Coverage rule"'
  examples/fakeshop/test_query/test_library_api.py` prints `0` (1
  today); the rewritten pinpoint resolves.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http`.
- Grade: stale (pinpoint only; claim true).
- Text-before:
  `The README rule at ``examples/fakeshop/test_query/README.md #"Coverage rule"```
  `requires this coverage`
- Text-after:
  `The README rule at ``examples/fakeshop/test_query/README.md #"Live-first, both verdicts"```
  `requires this coverage`

## Rejected

- R1 — Module docstring `Target release: 0.0.7.` Standing
  seven-module convention per connection R2 (this file's 0.0.7
  is the cited exemplar); the spec pointers beside it are
  kept. Trigger: the convention retired.
- R2 — Temporal language serving a present fact, no process
  artifact named (connection R3/R4 shapes, each content-
  verified): `The field now refuses at the call that caused
  it` (own tests line 2178; live async line 2313 — the
  refusal IS the test's subject, true per the SyncMisuseError
  assertions); `applying it used to mean calling that value's
  __getitem__` plus its past-tense threat paragraph (live
  line 1872-1878 — true per spec-050 Decision 8's
  never-`__getitem__` rule); `did before the argument surface
  existed` and `the old pipeline used` (live lines 2855,
  2982); `the historical speculative ... query ... no longer
  runs` (test_library_api query-count derivation — true per
  the consumer-override planning rule); `the new field`
  (test_library_api recompute-N note — the field under test
  in that test's context). Trigger: a rewrite to pure
  present tense.
- R3 — `_is_deterministic_order_name` docstring omits the
  compiler's SELECT-alias step (`selected_exprs.get(col)`
  ahead of the annotation lookup in `_order_by_pairs`).
  Rejected: in every constructed case the verdict agrees —
  a name hitting a select alias resolves to the same
  annotation/field the classifier reads (annotated aliases
  share the annotation; values aliases share the field;
  extra-select aliases refuse on both sides via the
  `query.extra` arm). The prose simplification is
  verdict-preserving. Trigger: a term whose SELECT-alias
  resolution and annotation/field-path resolution disagree
  on determinism.
- R4 — `(spec #"...")` pins in the own tests (four
  message-shape pins). Established cross-test idiom
  (`tests/test_scalars.py`, `tests/types/test_converters.py`
  share it); each quoted shape matches its live message.
  Trigger: a maintainer decision to name specs in pins.
- R5 — Bare `the spec` (target line 411 `the spec also
  promises to keep typed`; own tests line 123 `the spec's
  validation test plan`). Unambiguous in context (the
  argument surface; the Decision-5 section once L2 anchors
  its banner). Trigger: genuine ambiguity.
- R6 — `Factory for ...` non-imperative first line on
  `DjangoListField`. Joins the 4-site field-factory family
  convention per connection R1 (list, connection, two node
  fields); rewriting one site would make it inconsistent.
  Trigger: a maintainer mood decision enforced
  package-wide.
- R7 — No docstring on `_build_non_queryset_rejection_error`
  and the two `_execute_queryset_pipeline_*` twins. Private
  helpers; no looks-for entry requires them (connection
  R11). Trigger: none in this flow.
- R8 — `_is_deterministic_order_value` calls any
  non-expression, non-container value `a plain literal`,
  which over-reads for exotic iterables (a dict, a
  generator). The sentence describes the classification
  boundary the body implements; no constructed wire or
  direct input places expression members inside a
  non-container value (Django compiles `__in`/`__range`
  from sequences/pairs). Trigger: such an input reaching
  classification.

## Routed leads

- Routed: `django_strawberry_framework/utils/directives.py`
  module docstring — `Every field factory in the package
  (DjangoListField, DjangoMutationField and
  register_mutation()'s passthrough, the auth fixed-field
  factories, and the Relay root DjangoNodeField /
  DjangoNodesField)`. The census omits a real caller:
  `DjangoConnectionField` takes `directives=` and calls
  `validated_field_directives` (connection.py lines 2301,
  2347). The `register_mutation()` passthrough half was
  verified true. Owner: the `utils/directives.py` item.

## Observed (not graded)

- `tests/optimizer/test_extension.py` line 1927:
  `(spec line 350: ...)` — a line-number citation to an
  unnamed spec, in optimizer-subject prose (cache-key
  rule). For the `optimizer/extension.py` Comments pass,
  which owns both the helper and the decision it cites.
- `tests/base/test_init.py` lines 180-187: the 0.0.14 card
  narrative (`The secure-output card (spec-048) ... All of
  these cards shipped in 0.0.14`) surrounding the L3
  `ListArgumentError` tail. Project-subject prose (the
  public-surface assertion's history); for whichever pass
  owns `tests/base/test_init.py`.

Handoff: Comments review closed with six Mediums and four
Lows, all with static greps plus grade judgments as Proofs;
both siblings were read (no-findings, no cross-axis, no open
threads) and three of their discharges corroborate true-grades
in this record. Beyond the record's trace: the full
other-prose census (49 units, all discharged — true, finding,
routed, or observed), the KANBAN-cited dead-pinpoint audit
(all five `tests/test_list_field.py` sites already fixed in
the live text), and the rival-Decision-3 exclusions behind
M2. Open threads for Worker-0: L4's vocabulary mirrors
in-flight spec-050 DoD 17/22, so it may belong at the spec's
close rather than mid-flight; L2/L3/L4 touch files no higher
finding reaches, so they may defer under the Low rule (M5/M6
are Mediums and ride regardless). No workspace run was taken
and none is owed; every Proof re-runs from the record alone
in the shared tree.

## Verification (Comments)

Pass 1. Order note: this pass read the whole main artifact (including
`## Implementation (Worker-2)`) after Verify step 1 passed, then ran
every Proof below verbatim; worker-1 step 1 orders the Proof runs
before that read. The Proofs are mechanical count greps recorded
verbatim, so the order carries no bias; disclosed, not hidden.

Step 1 — item diff freshness: `git diff
8d5cb7ac968f96f5123ad24c3eb2e72c7249b897 --
django_strawberry_framework/list_field.py
examples/fakeshop/test_query/test_library_api.py` is byte-identical to
`docs/review/temp-tests/list_field/diff/pass-1.diff` (sha256
`e2855a5e71b34f320a52ca37c38f857678573c5071bdcada3f96d37451ed98bf`
both sides). The tree did not move under the pass. The unfiltered
ITEM stat adds only `docs/dry/dry-0_0_15.md` and
`docs/review/review-0_0_15.md` (Worker-0/other-flow bookkeeping,
matching Worker-2's attribution).

Proof lines (all verbatim, static, shared tree — no workspace run owed
or taken; no `## Cross-axis (for Comments)` section exists in any of
the three axis records, so the ten record Proofs are the whole set):

- Implemented, each prints `0`: M1 `and any future`, M2 `Decision 3;
  spec-020 Decision 1`, M3 `and a row count orders by`, M4 `or
  ``DISTINCT```, M5 `_post_process_consumer_sync`, M6
  `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`,
  L1 `^    Decision 8 promises`. All hold.
- Deferred, still at their today counts: L2 `# Validation tests
  (Decision 5)` prints `1` in `tests/test_list_field.py`; L3 `card
  050 lands` / `version cut adds` prints `2` in
  `tests/base/test_init.py`; L4 `legacy` / `pre-card` / `the card`
  prints `36` in
  `examples/fakeshop/test_query/test_list_field_api.py`. Confirmed and
  stated so.

Grades (each changed unit as the whole docstring or comment block it
sits in; every landed claim re-attacked against its body):

- M1 `_validate_djangotype_target` docstring: true. The three sharers
  check out (`relay.py` imports `_validate_relay_djangotype_target`,
  `_validate_node_target` wraps it behind `DjangoNodeField` /
  `DjangoNodesField`, the relay validator delegates at
  `list_field.py:224`, `connection.py:2330` calls it), and the
  sentence agrees with the docstring's own later `list, connection
  and Relay node entry points` line.
- M2 factory-site comment: true. spec-020 Decision 1 is `Module
  location, mechanism, & public export` (line 310), the asymmetry
  paragraph sits at line 453 under Decision 2 (line 326), and
  Decision 3 is `get_queryset and async symmetry` (line 466) — both
  landed numerals anchor correctly, and the block's subject matches
  D3.
- M3 `_APPROVED_ORDER_AGGREGATES` comment: true. Min/Max emission
  confirmed at `orders/sets.py:733-734`; the package `Count` census
  shows only total-count window annotations, never an ordering term;
  the classifier admits a `Count`-annotated consumer ordering by
  exact-type membership (line 666), which is what `admits` now says.
- M4 `DjangoListField` ordering contract (landed deviation — `flat
  lists inject no tiebreaker and no ``DISTINCT```): true on both
  halves. Connections close the order with a pk terminal tiebreaker
  (`connection.py::_finalize_queryset` via `effective_connection_order`);
  the sole package `.distinct()` is the consumer-filter effect in
  `filters/base.py:138`, and the only `distinct` hit in
  `connection.py` is the unrelated `Meta.name` prose — no connection
  path injects `DISTINCT`. The deviation is approved: the record's
  text-after retains the Proof's keyed substring, so Proof governs
  and the Proof now prints `0`.
- M5 Manager-coercion docstring: the M5 fix landed true
  (`prepared_resolver_source` runs in both `_wrap` colorings, lines
  1660 and 1707; `_branches_manager_resolver` returns
  `Branch.objects`; the `normalize_query_source
  #"_coerced_manager_queryset(source)"` pinpoint resolves to a real
  seam), BUT the same docstring carries the stale `README.md
  #"Coverage rule"` pinpoint — new finding V1 under `## Findings`
  (verify 1), Low, Proof prints `1` today.
- M6 nullable-outer docstring: true. No outer-nullability test exists
  anywhere in `tests/test_list_field.py`, so the live test standing
  as the only pin is the correct live-first shape, and the rewritten
  sentence says exactly that.
- L1 `_handle_non_queryset_rejections_async` docstring: true. The
  `spec-050` anchor resolves the real ambiguity (spec-020 Decision 8
  is the unrelated `Out-of-scope boundary with
  DjangoConnectionField`); the summary matches the body, which closes
  on every exit including constructor failure.

Deferrals judged: L2/L3/L4 correctly deferred. All three files diff
0 bytes vs ITEM_BASELINE, and no higher finding in this item touches
them (the item diff holds exactly 2 files; Performance and Mechanics
had no findings). L1 correctly rides `list_field.py`, changed for
M1-M4. L4's second reason (vocabulary mirrors in-flight spec-050
DoD 17/22) stands as recorded.

Instruments:

- `build_tree_md.py --list-docstrings` on both changed files: 1
  module, 0 breaking, each; both module first lines byte-identical to
  ITEM_BASELINE, so no TREE.md render is owed.
- `check_citations.py --paths <file> --substrings`: target 7
  citations / 0 violations; `test_library_api.py` 19 checked / 1
  violation — the V1 pinpoint (pre-existing, ungated: `--check`
  stays green on substring pinpoints).
- `review_inspect.py --code-digest <ITEM_BASELINE>:<path> <path>`:
  exit 0 with equal digests on both files, reproducing Worker-2's
  values exactly (`95fb1b0d…` target, `43b8fbed…` test file). Direct
  baseline comparison — no other axis changed code in these files, so
  no reconstruction is owed.
- Prose diff via the REVIEW.md command into
  `verify-comments-1/diff/`: 7 prose hunks, zero `[code changed too]`
  markers.
- Diff hygiene on added lines: no process provenance (the two
  `spec-020`/`spec-050` hits are kept spec-Decision pointers), no
  line-number citation, no `we`/`you`/`I`.

Sibling verifiers' sections: Performance owns no wording grade and
routes nothing; Mechanics leaves M2/M3/M6 entirely to this pass
(all graded true above), concurs on the M4 `no/and` halves, and
routes nothing further. No gaps were routed to Comments beyond the
grading itself.

Disputes: none recorded (Worker-2 disputed nothing).

Gaps for `## Decisions` (on this axis but outside the item's reach —
untouched symbols/files, so not `revision-needed`):

- G1 (owner: the `list_field.py` item — Worker-0 may route into pass
  2, else a later Comments pass): `_is_deterministic_order_term`
  docstring, `one of the aggregates the shipped surface emits
  (``_APPROVED_ORDER_AGGREGATES``)` — the M3 twin in a symbol this
  pass did not touch. Same falsity for `Count` (Medium if filed).
- G2 (owner: the item that next owns `test_products_api.py` prose):
  `test_products_api.py:4710` `(the README "Coverage rule.")` — the
  V1 vocabulary twin in a file this item does not touch.

Cells: sharded and pg inapplicable by construction (static greps
plus grade judgments; prose-only diff). Cells unverified: none.

Fingerprints (`git hash-object` at verify time): `list_field.py`
`6a1dba1af04428d4fc67864c2beb1af755fc387c`,
`test_library_api.py`
`4acc4821d8adb23b2de8a743d351f94567932c14` (both equal Worker-2's
after-values); `rev-list_field.md` `42fc4e72`, `.performance.md`
`98645808`, `.mechanics.md` `0f3543b4`, `.comments.md` `a3ccbf82`
(pre-section). Scratch:
`docs/review/temp-tests/list_field/verify-comments-1/` (prose diff
under `diff/`; no probe — nothing executable was owed). No workspace
runs, no run ids.

Verdict: revision-needed on V1 alone (Low, one-line re-pin riding an
already-touched file and symbol). Every implemented finding landed
true, including the approved M4 deviation; all three deferrals are
correct.

Handoff: Comments verify pass 1 closes `revision-needed` with exactly
one named gap: V1, the stale `README.md #"Coverage rule"` pinpoint in
the M5 docstring, Proof `grep -c 'README.md #"Coverage rule"'
examples/fakeshop/test_query/test_library_api.py` printing `1` today.
A pass-2 Worker-2 re-pins it (suggested `#"Live-first, both verdicts"`,
kept on one source line) and a fresh verifier re-runs the ten record
Proofs plus the V1 Proof; nothing else in this section constrains
pass 2. Beyond the record's trace: the `8b3b9ae1` README rewrite is
the pinpoint's killer, confirmed via `git log -S`; the G1 twin
(`_is_deterministic_order_term` docstring) and G2 twin
(`test_products_api.py:4710`) are named above for Worker-0 to route.
Open threads: none on this axis. No workspace copy was opened.

## Verification (Comments) pass 2

Pass 2. Order note (same disclosure as pass 1): this pass
read the whole main artifact (including `Implement pass 2`)
after Verify step 1 passed, then ran every Proof below
verbatim; worker-1 step 1 orders the Proof runs before that
read. The Proofs are mechanical count greps recorded
verbatim, so the order carries no bias; disclosed, not
hidden.

Step 1 — item diff freshness: `git diff
8d5cb7ac968f96f5123ad24c3eb2e72c7249b897 --
django_strawberry_framework/list_field.py
examples/fakeshop/test_query/test_library_api.py` is
byte-identical to
`docs/review/temp-tests/list_field/diff/pass-2.diff`
(`cmp` IDENTICAL, sha256
`4a2735a79423507f963bba1752b0605628913be368fe97c6054da643dcb5417c`
both sides, 6827 bytes, 8 hunks: the 7 pass-1 regions
with V1 merged into the M5 hunk, plus the new G1 hunk).
The tree did not move under the pass. The unfiltered ITEM
stat adds only `docs/dry/dry-0_0_15.md` and
`docs/review/review-0_0_15.md` (Worker-0/other-flow
bookkeeping, matching the pass-2 attribution).

Proof lines (all verbatim, static, shared tree — no
workspace run owed or taken; no
`## Cross-axis (for Comments)` section exists in any of
the three axis records, so the record Proofs plus V1/G1
are the whole set):

- V1: `grep -c 'README.md #"Coverage rule"'
  examples/fakeshop/test_query/test_library_api.py`
  prints `0` (was `1` at pass 1). Holds.
- G1 (derived the same way; exact grep):
  `grep -c 'aggregates the shipped surface'
  django_strawberry_framework/list_field.py` prints `0`
  (`1` at ITEM_BASELINE, line 872). The full stale
  sentence wraps across baseline lines 872-873, so no
  single-line grep can key on the whole sentence; this
  substring is its longest single-line distinctive
  phrase, and the same shape Worker-2 reported. Holds.
- Pass-1 implemented, each still `0`: M1 `and any
  future`, M2 `Decision 3; spec-020 Decision 1`, M3 `and
  a row count orders by`, M4 `or ``DISTINCT```, L1
  `^    Decision 8 promises` (all in `list_field.py`);
  M5 `_post_process_consumer_sync`, M6
  `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`
  (both in `test_library_api.py`). All hold.
- Pass-1 deferred, still at their today counts: L2 `1`
  in `tests/test_list_field.py`; L3 `2` in
  `tests/base/test_init.py`; L4 `36` in
  `examples/fakeshop/test_query/test_list_field_api.py`.
  All three files diff 0 bytes vs ITEM_BASELINE, so the
  ride rule still applies and the deferrals stand.

Grades (each reworked unit as the whole docstring it
sits in; every landed claim re-attacked against its
body):

- V1 M5 docstring
  (`test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http`,
  lines 1050-1061): true. Everything outside the
  re-pinned line is unchanged since the pass-1 true
  grade. The pinpoint resolves: README line 42 carries
  `Live-first, both verdicts` on one physical line, in
  the paragraph stating `Any
  django_strawberry_framework/ line a real fakeshop
  query reaches MUST be covered from this dir` — exactly
  the rule the sentence states (`requires this coverage
  to land here, not in the package-internal
  tests/test_list_field.py`). The citing line (1059) is
  one source line, 98 chars. `check_citations.py
  --paths ... --substrings` on the file now reports 19
  checked / 0 violations (was 1: the V1 pinpoint).
- G1 `_is_deterministic_order_term` docstring (lines
  842-902): true. First line imperative; the changed
  sentence matches the M3 fix shape exactly — emission
  scoped to ``Min`` / ``Max``, ``Count`` admitted for
  consumer annotation (M3 landed: `and ``Count`` admits
  the row-count aggregate a consumer ordering may
  annotate`; G1 landed:
  ```text
  (``_APPROVED_ORDER_FUNCTIONS``), an approved aggregate
  (``_APPROVED_ORDER_AGGREGATES``: ``Min`` / ``Max`` the shipped surface emits,
  ``Count`` a consumer ordering may annotate), an ``F`` reference, or a ``Q``
  ```
  ). Min/Max emission confirmed in code
  (`orders/sets.py:734`, `aggregate = models.Min if
  direction.is_ascending else models.Max`); the package
  `Count` census shows only window/total-count
  annotations (`Count(1) OVER`, `Count("pk",
  filter=...)`), never an ordering term, so no shipped
  surface orders by `Count`; the classifier admits a
  `Count`-annotated consumer ordering by exact-type
  membership (`_APPROVED_ORDER_NODES` unions the set at
  line 666; read at lines 905-912), which is what
  `admits`/`may annotate` says; all three set members
  are Django aggregates, so `an approved aggregate` is
  exact. The untouched remainder re-attacks clean: the
  exact-type paragraph matches the body (`node is
  models.F`, `node in _READABLE_ORDER_LEAVES`, `node not
  in _APPROVED_ORDER_NODES`); the `Star` census (import
  + `_READABLE_ORDER_LEAVES` only) matches `the ``*``
  of a row count`; the only other `emits` hit in that
  docstring family (line 976, `whatever that transform
  emits`) is about transform SQL, not aggregates — no
  third twin.

Deferrals and routed gaps: L2/L3/L4 correctly deferred
(files untouched, counts unchanged). G1 is now
implemented, closing the pass-1 gap. G2
(`test_products_api.py:4710`, the V1 vocabulary twin)
still stands in a file this item does not touch (0-byte
diff vs ITEM_BASELINE) — correctly outside the fence,
stays routed under `## Decisions`.

Instruments:

- `build_tree_md.py --list-docstrings` on both changed
  files: 1 module, 0 breaking, each; both module first
  lines byte-identical to ITEM_BASELINE, so no TREE.md
  render is owed.
- `check_citations.py --paths <file> --substrings`:
  target 7 citations / 0 violations; `test_library_api.py`
  19 / 0 (V1 resolved).
- `review_inspect.py --code-digest <ITEM_BASELINE>:<path>
  <path>`: exit 0 with equal digests on both files,
  reproducing the pass-1/Worker-2 values exactly
  (`95fb1b0d…` target, `43b8fbed…` test file). Direct
  baseline comparison — no axis changed code in these
  files, so no reconstruction is owed.
- Prose diff via the REVIEW.md command into
  `verify-comments-2/diff/`: 2 per-file diffs, zero
  `[code changed too]` markers.
- Pass-2-only added lines (the V1 line + the 3 G1
  lines): no process provenance (`0`), no line-number
  citation (`0`), no `we`/`you`/`I` (`0`). The
  whole-item added-line sweep carries only the two kept
  spec-Decision pointers from pass-1 regions (L1, M2).

Sibling verifiers' sections: Performance verified and
Mechanics verified (pass 1) stand — this pass is
prose-only by digest identity, which trips no
Performance or Mechanics trigger, and Worker-2 disputed
nothing in either pass.

Disputes: none recorded (Worker-2 disputed nothing).

New problems: none. No new finding, no gap for
`## Decisions` (G2 already sits there).

Cells: sharded and pg inapplicable by construction
(static greps plus grade judgments; prose-only diff).
Cells unverified: none.

Fingerprints (`git hash-object` at verify time):
`list_field.py`
`f5b0183e290322952fd2dad1f76ab9b2de9736ba`,
`test_library_api.py`
`26dd0abb537df74f06fe864bd0e3c22634307541`
(both equal Worker-2's pass-2 after-values);
`rev-list_field.md` `09980924`, `.performance.md`
`98645808`, `.mechanics.md` `0f3543b4`, `.comments.md`
`748d4cbc` (pre-section); `test_query/README.md`
`0dbf3a35` and `orders/sets.py` `60859f2d` (both equal
the Trace values). Scratch:
`docs/review/temp-tests/list_field/verify-comments-2/`
(prose diff under `diff/`; no probe — nothing
executable was owed). No workspace runs, no run ids.

Verdict: verified. V1 re-pinned per the record's
text-after and resolving; G1 fixed in the M3 shape;
every pass-1 Proof re-confirmed; all three deferrals
still correct.

Handoff: Comments verify pass 2 closes `verified` with
nothing open: the V1 pinpoint now resolves to README
line 42 (`Live-first, both verdicts`), the G1 sentence
is the M3 twin fixed the M3 way, and the ten pass-1
Proofs plus the two new Proofs all print their governed
counts (`0` x9, then 1/2/36 deferred). Beyond the
record's trace: the G1 proof keys on `aggregates the
shipped surface` because the stale sentence wraps
across baseline lines 872-873; the line-976 `emits`
was checked and is transform SQL, not a third twin;
G2 stays routed. Open threads: none on this axis. No
workspace copy was opened.
