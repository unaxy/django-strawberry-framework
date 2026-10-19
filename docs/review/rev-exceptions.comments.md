# Review · Comments: `django_strawberry_framework/exceptions.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=c78eb5f150bcd2a5f448a135e078ef58a5594cf4

## Trace

Read the whole live target (`django_strawberry_framework/exceptions.py`,
232 lines: module docstring, 8 symbol docstrings, 2 inline `# truth: ok`
comments, no section banners, no TODOs) and the whole own test module
(`tests/test_exceptions.py`, 212 lines: module docstring, 7 test/helper
docstrings, 1 inline comment). The target is dirty vs HEAD (the concurrent
`_safe_*` → `utils/truth.py` message-builder migration) but byte-identical
to ITEM_BASELINE (`git diff c78eb5f1 --` the two graded files is empty);
every grade below is against the live text at these fingerprints.

Also graded: the prose about the target's symbols held by other test
modules — every docstring/comment line naming `ConfigurationError`,
`OptimizerError`, `PathResolutionError`, `LookupValidationError`,
`DjangoStrawberryFrameworkError`, or `SyncMisuseError` across `tests/`,
`examples/fakeshop/test_query/`, `examples/fakeshop/tests/`, and the
per-app `tests/` trees (behavior pins, sampled to the claims about the
exception classes themselves), plus a 436-file sweep for stale
references to the removed `_safe_*` / `describe_value` / `<unprintable>`
machinery (no live hits) and a hostile/`unprintable` prose sweep for
stale guard-behavior pins (all live hits describe the current
`utils/truth.py` contract). Package neighbors read for the trace (prose
defects there would be Routed leads, not findings; none found):
`utils/truth.py` (whole), `utils/__init__.py` (whole),
`utils/relations.py` (`classify_path`, `validate_lookup_expr`,
`path_traverses_to_many`, `_traverses_to_many`,
`_lenient_traverses_to_many`, `_resolve_segment_field`,
`_is_traversable_relation`, `relation_bool`),
`utils/connections.py` (`window_range_plan`,
`assert_window_fetch_mode`), `optimizer/plans.py`
(`window_partition_for_prefetch`, `apply_window_pagination`,
`_reverse_order_by`), `optimizer/predicates.py` (`attach_exists`),
`optimizer/field_meta.py` (`FieldMeta.from_django_field`),
`utils/querysets.py` (`SyncMisuseError`), `__init__.py` (re-exports),
`types/base.py` (Meta validation, `from_django_field` call site),
`registry.py` + `types/finalizer.py` (primary semantics, grep level),
`conf.py` (non-mapping settings prose),
`types/resolvers.py` (`_check_n1` + callers), `types/converters.py` +
`optimizer/walker.py` (`from_django_field` call sites),
`utils/sessions.py` (`session_store_class`), `orders/sets.py`
(`{exc}` interpolation arm), `keyset.py` (`repr(entry)` arm),
`optimizer/join_taxonomy.py` (grep level). Contract prose checked:
the four live suites the own-test docstring names (module docstrings
plus the rows the parentheticals characterize), `docs/TREE.md`
(exception rows, in sync). Sibling records: Performance read whole
(`no-findings`, cold, Handoff + Routed lead noted; its fingerprints
match mine on all ten shared files, so nothing drifted mid-pass);
Mechanics absent at review time (concurrent dispatch).

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/exceptions/comments/inspect/` plus
`exceptions.json` (10 docstrings, 2 comments, 0 TODOs, 3 symbol-cite
docstrings). `build_tree_md.py --list-docstrings` passes on the
target and the own test module (1 module, 0 breaking, each).
`check_citations.py --paths django_strawberry_framework/exceptions.py
--substrings --json` reports 8 citations, 0 violations.
Provenance sweep (REVIEW.md pattern) hits only substring accidents
(`worker` inside `FrameworkError`, `round` inside `roundtrip`).
No `we`/`you`/`I`, no `Tests that`/`Ensures`, no `.py:NN` cites, no
public symbol without a docstring in the target (the two
`__init__` dunders are covered by R4). No docstring restates its
signature or type hints; the one intentional separation (strict error
vs lenient boolean) is recorded at the owner — F1's paragraph.

Cells: default, sharded, and pg are all inapplicable by construction —
every Proof below is a static shared-tree command over prose; no
command in this pass imported the package, opened a database, or
measured. No workspace runs were made; no run ids exist for this
record.

Fingerprints (`git hash-object` of every repo file read):

- `django_strawberry_framework/exceptions.py` 206e9f8d914f640134cf72e374fadeac41d13a39
- `tests/test_exceptions.py` 4b5818c22d24865a38a44e73782b49ee3dc9f94d
- `django_strawberry_framework/utils/truth.py` d5c96bc8d191d3fce0a20140d8e91063bb466ec9
- `django_strawberry_framework/utils/__init__.py` 1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee
- `django_strawberry_framework/utils/relations.py` 05ff55b098382a4a7aafe5a097c3b5e906f8f985
- `django_strawberry_framework/utils/connections.py` efcf749a26dc7d3fa9b3cc142789a11de2647070
- `django_strawberry_framework/optimizer/plans.py` 33140a766cd3fb2484a40fe499d466c8ced8b4a6
- `django_strawberry_framework/optimizer/predicates.py` 4673e81bc65013f5391682fb482bbb07f9c89345
- `django_strawberry_framework/optimizer/field_meta.py` bcddf517b0145be6c06c717d5379e29c271cfea5
- `django_strawberry_framework/utils/querysets.py` 8fc556d582b313e4aed7cddaa15f9a8480d88a46
- `django_strawberry_framework/__init__.py` 0ef72601ecac300ac87ff993af1b04a4f1bc335a
- `django_strawberry_framework/types/base.py` dc67f084cbc969d64b7b1f1ef18c388095d394f7
- `django_strawberry_framework/registry.py` 492654d219d1061fef33f186d962dc5369b71ebe
- `django_strawberry_framework/types/finalizer.py` b9d8acb2b9428cc8297550414ff86bdd98e0d1a7
- `django_strawberry_framework/conf.py` 3820c575bfd4e3c384244d1bed460b75d3bb7681
- `django_strawberry_framework/types/resolvers.py` 640905c63f465db4de16c3a07492b27f3d12d3ad
- `django_strawberry_framework/types/converters.py` f6cadb0856c725d96ce316abb4418b4c9d55bf9d
- `django_strawberry_framework/optimizer/walker.py` d5759ef8533a6218942a0a2a33e64f59599a93a7
- `django_strawberry_framework/utils/sessions.py` 21041723250de58876d95eaec14e1078a6f16a4f
- `django_strawberry_framework/orders/sets.py` 60859f2d54525acfdb3dc997d3e931ff3d58d956
- `django_strawberry_framework/keyset.py` 279ad7b089de282e52b8210ad9c61101c8b3e401
- `django_strawberry_framework/optimizer/join_taxonomy.py` 57165577ad7f3add11f90a111a747186d9d3bc9c
- `docs/TREE.md` 769c274392d055c566a2b2d3006afc7baa5d0a9c
- `examples/fakeshop/test_query/test_error_policy_api.py` 071b113feeaf9cee30ccda5941614c423251459c
- `examples/fakeshop/test_query/test_connection_pagination_api.py` d6a4f720fba01ae436bd1a30af4a40c6bae4539a
- `examples/fakeshop/test_query/test_products_api.py` fe78cf9d4862123442611444d44bf81b5187ec6d
- `examples/fakeshop/test_query/test_transport_api.py` 6d65274f9e7b5589d60777d7e0484b3ad10df394
- `tests/mutations/test_resolvers.py` eeab4fbe67bec4ae8835f0c33344002046f3c3f9
- `tests/test_views.py` 3f9c81153f4fa742479d1b8d7792a18e294e6253
- `tests/mutations/test_permissions.py` a4472aee93454e446cfcb2773b840e7e247bc05e
- `docs/review/rev-exceptions.performance.md` fad61523581432becdd25935062f99265f603d64

## Findings

### High

None. The public contracts grade true: the module import-graph
paragraph matches `utils/truth.py` (stdlib-only) and
`utils/__init__.py` (which runs `relations`/`strings`, both importing
this module); the base-class rendering paragraph matches the deleted
`__str__`/`__repr__` guards plus the f-string-exact raise sites
(R3); every `ConfigurationError` example resolves to its raise
(`types/base.py` model/fields-exclusive/deferred-key arms,
`registry.py` duplicate-primary/flip arms,
`types/finalizer.py::_audit_primary_ambiguity`,
`conf.py::_normalize_user_settings`) and the `SyncMisuseError`
paragraph matches `utils/querysets.py` plus the root re-export; the
`PathResolutionError` hierarchy paragraph matches the bases and the
lattice test; each of its four raise bullets matches its
`classify_path` arm (`FieldDoesNotExist` incl. `related_name="+"`,
scalar-mid-path, GFK without `path_infos` at any position,
empty/non-sequence `path_infos`); the `LookupValidationError`
distinction paragraph and its three `validate_lookup_expr` bullets
match the body; six of the seven `OptimizerError` bullets match
their owners (`FieldMeta.from_django_field` guard,
`_check_n1` strictness arm incl. the `connection_to_attr` kind,
`assert_window_fetch_mode`, `window_range_plan`,
`window_partition_for_prefetch`, `apply_window_pagination`
reversed-keyset guard, `attach_exists` triple); both `__reduce__`
docstrings match the `(type, args, vars(self))` bodies; both
`# truth: ok` markers state the read they suppress.

### Medium

- Observation: `django_strawberry_framework/exceptions.py::PathResolutionError`
  docstring describes the lenient twin as `which swallows resolution
  failure and answers ``False```. It does not answer `False`: on a
  `PathResolutionError`,
  `django_strawberry_framework/utils/relations.py::path_traverses_to_many`
  answers from the legacy lenient walk, which returns `True` the
  instant a many-side hop precedes the failure (`genres__nonexistent`
  and `genres__name__icontains` both answer `True`). `False` is only
  the no-many-hop-yet answer. The distinction paragraph's whole job
  is to define this error's boundary against that helper, and its
  mechanism clause states the helper's contract wrongly.
- Evidence: `django_strawberry_framework/utils/relations.py::_traverses_to_many`
  (`except PathResolutionError: return _lenient_traverses_to_many(...)`);
  `django_strawberry_framework/utils/relations.py::path_traverses_to_many`
  docstring (`falls back to the legacy lenient walk rather than a
  bare ``False```, with the two `True` examples);
  `django_strawberry_framework/utils/relations.py::_lenient_traverses_to_many`
  docstring (`returning ``True`` the instant a many-side relation is
  reached - even if garbage follows it`).
- Impact: a reader trusting the clause believes the lenient answer on
  malformed input is always `False`; taken literally it motivates
  collapsing the fallback ladder to a bare `False`, which regresses
  the 32-path matrix the owner pins (many-then-garbage must stay
  `True` for the `distinct`/aggregate consumers).
- Severity: Medium (stale sibling-behavior clause in a public
  symbol's boundary paragraph; the class's own raise contract is
  correct, so not High).
- Recommendation: restate the parenthetical as the fallback ladder;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c "swallows resolution failure and answers"
  django_strawberry_framework/exceptions.py` prints `0` (1 today);
  the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/exceptions.py::PathResolutionError`.
- Grade: stale (contradicted by the cited helper's own docstring and body).
- Text-before:
  `Distinct from the lenient boolean
  ``utils/relations.py::path_traverses_to_many`` walk (which swallows
  resolution failure and answers ``False``) so strict callers never
  turn a malformed declaration into a lenient "does not traverse many"
  answer by accident.`
- Text-after:
  `Distinct from the lenient boolean
  ``utils/relations.py::path_traverses_to_many`` walk (which answers a
  ``PathResolutionError`` from the legacy lenient walk - ``True`` once
  a many-side hop precedes the failure, ``False`` otherwise) so strict
  callers never turn a malformed declaration into a lenient answer by
  accident.`

- Observation: `tests/test_exceptions.py::test_empty_args_render_empty_string`
  docstring ends `and never hits the placeholder path.` No placeholder
  path exists: the base `__str__`/`__repr__` overrides and the shared
  `<unprintable ...>` fallback they carried were deleted by the
  `truth` migration (the diff at HEAD removes them whole), and
  `str()` of an empty-args error goes through CPython's default. The
  clause is a leftover naming a mechanism the file no longer owns.
- Evidence: `git diff HEAD -- django_strawberry_framework/exceptions.py`
  deleting `DjangoStrawberryFrameworkError.__str__`,
  `.__repr__`, `_safe_arg_repr`, `_safe_text`, `_unprintable`,
  `describe_value`; the live base class carrying no render override;
  the 436-file sweep (Trace) finding no live placeholder path in the
  exception surface (remaining `<unprintable ...>` spellings belong
  to `utils/truth.py`, which this render never touches).
- Impact: a reader hunting `the placeholder path` finds nothing and
  must re-derive whether the test pins a live branch or a deleted
  one; the title half (`str is empty`) stays true and stays.
- Severity: Medium (stale clause naming a deleted mechanism).
- Recommendation: restate the tail as the standard-`Exception`
  behavior the base docstring promises; see text-after.
- Must not change: n/a.
- Proof: `grep -c "never hits the placeholder path"
  tests/test_exceptions.py` prints `0` (1 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_exceptions.py::test_empty_args_render_empty_string`.
- Grade: stale (names a mechanism deleted by the concurrent migration).
- Text-before:
  `No message args: ``str`` is empty and never hits the placeholder path.`
- Text-after:
  `No message args: ``str`` is empty, exactly as with any other exception.`

### Low

- Observation: the `django_strawberry_framework/exceptions.py::OptimizerError`
  `Raise sites:` list omits the eighth site:
  `optimizer/plans.py::apply_window_pagination` rejects (via its
  `_reverse_order_by` helper) an order entry carrying neither a
  `descending` flag nor a callable `desc()`, since no reversed
  row-number window can express it. The list is otherwise exhaustive
  (every other `raise OptimizerError` in the package is named,
  including the adjacent reversed-keyset guard in the same function),
  so a reader auditing the contract misses this arm.
- Evidence: full-package `raise OptimizerError` census (14 sites:
  `field_meta.py` x3, `plans.py` x4, `predicates.py` x3,
  `types/resolvers.py` x1, `utils/connections.py` x3); the
  `plans.py::_reverse_order_by` raise with its own `Raises
  OptimizerError` docstring paragraph; the call at `plans.py`
  inside `apply_window_pagination`.
- Impact: bounded clarity — the site is documented at its owner, so
  no behavior is misdescribed; only the central list is incomplete.
- Severity: Low.
- Recommendation: add the bullet after the reversed-keyset bullet;
  same touch also fixes `a fall back` → `a fallback` in the
  window-partition bullet; see text-after.
- Must not change: n/a.
- Proof: `grep -c "_reverse_order_by"
  django_strawberry_framework/exceptions.py` prints `1` (0 today)
  and `grep -c "a fall back to per-parent"
  django_strawberry_framework/exceptions.py` prints `0` (1 today);
  the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/exceptions.py::OptimizerError`.
- Grade: stale (incomplete central list; everything stated is true).
- Text-before: the seven-bullet `Raise sites:` list (no
  backward-window order-reversal entry) plus `(both signal a fall
  back to per-parent resolution).`
- Text-after: the same list with this bullet after the reversed-keyset
  bullet:
  `- Backward-window order reversal:
  ``optimizer/plans.py::apply_window_pagination`` rejects (via
  ``_reverse_order_by``) an order entry carrying neither a
  ``descending`` flag nor a callable ``desc()``, which no reversed
  row-number window can express.`
  and `(both signal a fallback to per-parent resolution).`

- Observation: the `django_strawberry_framework/exceptions.py::PathResolutionError`
  message sentence ends `so a lenient caller cannot silently downgrade
  it.` Naming the model, path, and segment does not prevent
  downgrading — raising (vs answering a boolean) does, and that
  distinction is established two paragraphs up. The purpose clause
  attributes the strictness property to the message content.
- Evidence: the distinction paragraph above it (strict error vs
  lenient boolean is what forces handling); the parallel
  `LookupValidationError` sentence stating the same message-content
  property correctly (`so the failure is actionable`).
- Impact: a wrong stated reason for a true sentence (worse than
  none); one-clause fix aligning the twins.
- Severity: Low.
- Recommendation: restate the purpose clause as actionability; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "cannot silently downgrade"
  django_strawberry_framework/exceptions.py` prints `0` (1 today);
  the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/exceptions.py::PathResolutionError`.
- Grade: stale (wrong stated reason; the factual claims are true).
- Text-before:
  `The message always names the model label, the complete declared
  path, and the offending segment so a lenient caller cannot silently
  downgrade it.`
- Text-after:
  `The message always names the model label, the complete declared
  path, and the offending segment so the failure is actionable.`

## Rejected

- R1: `_model_label` / `_terminal_label` descriptive (non-imperative)
  first lines. Rejected as style preference: the package convention,
  including the newest `utils/truth.py` (~30 identical descriptive
  helper first lines), accepts descriptive mood for small helpers,
  and forcing `Return ...` onto these two degrades them while
  leaving dozens standing. Trigger: a package-wide mood gate lands;
  these two ride it.
- R2: the `PathResolutionError` / `LookupValidationError` raise lists
  omitting the defensive arms (non-`str` `field_path` /
  `lookup_expr` guards, the `relation_bool` `ConfigurationError`
  conversion, the `FieldError` conversion). Rejected: unreachable
  from typed callers (tests reach the non-`str` guard deliberately),
  and the owner docstrings (`classify_path`, `validate_lookup_expr`)
  agree in omitting them. Trigger: an owner starts listing guards,
  or a typed caller reaches one.
- R3: the base-class `Every message the framework raises is built as
  an exact ``str`` at the raise site` universal. Rejected: every
  sampled raise site interpolates exact `str`s, framework labels, or
  `truth` renders, and f-string results are exact `str` by
  construction, so `str`/`repr` of a framework-raised error never
  runs consumer code as promised. `truth.render` propagating a
  hostile non-scalar `__repr__` at build time is `truth.py`'s
  documented contract, about construction, not about `str`/`repr`.
  Trigger: a reachable raise interpolating a consumer dunder without
  `truth`.
- R4: the two `__init__` dunders carrying no docstring (the inspect
  census flags them). Rejected: repo convention documents dunder
  inits on the class; both classes do. No trigger (convention).
- R5: the identical `__reduce__` one-liners as duplication.
  Rejected: twin pickle-protocol methods; a shared base for one line
  each is overkill, and the sentence explains the why (roundtrips),
  not the code. Trigger: a third twin or diverging logic.
- R6: the Performance sibling's caller-census observations (no
  production caller of `window_partition_for_prefetch`, no
  production caller of `validate_lookup_expr`) as prose defects.
  Rejected: the `OptimizerError` bullet states the raise's signal
  meaning (tests pin it; the owner already frames the shim as
  historical), and the `LookupValidationError` docstring states the
  validator's contract (tests pin it). Caller count changes neither
  grade. Trigger: an owner redefines either contract.

Handoff: Review pass closed with `Status: findings-recorded` (0
High, 2 Medium, 2 Low, 6 rejections, no Routed leads, no Cross-axis
findings). Read beyond this record's trace: the full `raise
OptimizerError` / `raise PathResolutionError` / `raise
LookupValidationError` censuses, the `from_django_field` four-site
caller list, the `_check_n1` connection-kind callers, the
`_reverse_order_by` single caller, and the sibling Performance
record whole (Mechanics was absent). Conclusions the findings do
not state: the file is otherwise in unusually good shape — the
concurrent `truth` migration left exactly one stale test clause
(F2) and zero stale helper references across 436 live files. Open
threads for other axes, explicitly not findings (no reachable input
demonstrated, so per rule 35 neither is a defect): (a) Mechanics
may want to judge whether `classify_path`'s non-`str` guard
rendering through `truth.render` (which propagates a hostile
`__repr__`, where the old `_safe_arg_repr` degraded) is the
intended posture for a validator whose typed callers only pass
`str`; (b) same question for `keyset.py`'s `repr(entry)` over
consumer-declared `cursor_field` entries. Cells unverified: none
(all inapplicable by construction). No workspace runs; scratch is
`docs/review/temp-tests/exceptions/comments/` (`inspect/` +
`exceptions.json`).

## Verification (Comments)

Pass 1, address `review/exceptions.py/verify-comments-1`, scratch
`docs/review/temp-tests/exceptions/verify-comments-1/` (holds
`diff/` from the prose-diff command below; every other instrument
is a static shared-tree command).

Step 1 — item diff integrity: `git diff
c78eb5f150bcd2a5f448a135e078ef58a5594cf4 --
django_strawberry_framework/exceptions.py tests/test_exceptions.py`
sha256 `f2acd1efc5f70cb073f6a4e0806a9b1287d1814cc4408f41f5b03971d451d256`
hash-equals `docs/review/temp-tests/exceptions/diff/pass-1.diff`
(same sha256, `cmp` HASH_EQUAL, 4160 bytes each); live blobs
`93401220` / `1374fef5` match Worker-2's fingerprints. The tree
did not move under the pass. Grade proceeds.

Proofs run verbatim before reading `## Implementation (Worker-2)`,
in the shared tree and again at the verify address (fresh copy,
slot-4, package digest `sha256:b164b5bc...1c3f10`, shared unmoved
since sync; exit 1 on a 0-count grep is grep's no-match exit, the
expected outcome — the count is the verdict):

- M1 `grep -c "swallows resolution failure and answers"
  django_strawberry_framework/exceptions.py` prints `0` (was `1`):
  hold. Run `review-20260929T044351-7e1578`.
- M2 `grep -c "never hits the placeholder path"
  tests/test_exceptions.py` prints `0` (was `1`): hold. Run
  `review-20260929T044351-626121`.
- L1 `grep -c "_reverse_order_by"
  django_strawberry_framework/exceptions.py` prints `1` (was `0`)
  and `grep -c "a fall back to per-parent"
  django_strawberry_framework/exceptions.py` prints `0` (was `1`):
  hold. Runs `review-20260929T044356-5ddc32`,
  `review-20260929T044356-fd296a`.
- L2 `grep -c "cannot silently downgrade"
  django_strawberry_framework/exceptions.py` prints `0` (was `1`):
  hold. Run `review-20260929T044356-a2c07d`.
- C1 `grep -c "_reverse_order_by" ...` prints `1`: hold (same run
  as L1's first count; jointly implemented once, both Proofs
  govern).
- C2 `grep -c "relation_bool"
  django_strawberry_framework/exceptions.py` prints `1` (was `0`):
  hold. Run `review-20260929T044357-b7bd8d`.
- C3 `grep -c "FieldError"
  django_strawberry_framework/exceptions.py` prints `1` (was `0`):
  hold. Run `review-20260929T044357-dc6afb`.

All 8 counts hold on both sides. No other record holds a Proof
for Comments.

Numbers reproduced: Worker-2 claims no bench figure moves and the
two `--code-digest` pairs. Both reproduce exit 0 with its exact
digests: `django_strawberry_framework/exceptions.py`
`sha256:2c01d220...8b8d10` both sides;
`tests/test_exceptions.py` `sha256:bdbf204b...c4714c5` both
sides. Direct baseline comparison (no other axis changed code in
these files — Performance and Mechanics landed nothing here).
Prose-only proven; no before/after, no permanent test, no
failability owed.

Whole-diff reading through Comments: the prose diff (REVIEW.md
"Comments" command, one `--path` per item file, under
`verify-comments-1/diff/`) shows 7 prose hunks and zero `[code
changed too]` markers: five target hunks across three docstrings
(M1 paragraph, C2 bullet, L2 sentence, C3 bullet, C1/L1 bullet
plus the `fallback` fix) and one test-docstring hunk (M2).

Grades, each as the whole docstring it sits in (landed text
judged against body plus one real caller/owner, per the record's
Proof contract):

- `django_strawberry_framework/exceptions.py::PathResolutionError`
  — true. M1's ladder ("answers a `PathResolutionError` from the
  legacy lenient walk — `True` once a many-side hop precedes the
  failure, `False` otherwise") matches
  `utils/relations.py::_traverses_to_many` (`except
  PathResolutionError: return _lenient_traverses_to_many(...)`),
  `_lenient_traverses_to_many` (True the instant a many-side hop
  is reached, False on every other exit), and
  `path_traverses_to_many`'s docstring (which names the same
  fallback with the same `genres__nonexistent` /
  `genres__name__icontains` True examples). C2's guard-arms bullet
  matches `classify_path`: the non-`str` guard raises before
  segmentation naming the whole value as the segment, and the
  `is_relation` conversion catches `relation_bool`'s
  `ConfigurationError` (whose own docstring calls a non-`bool`
  "malformed metadata"); with it the six-statement census is
  fully indexed and the "all in `classify_path`" header still
  holds. L2's "so the failure is actionable" matches the
  unconditional `__init__` naming (model label, full path,
  segment) and aligns the `LookupValidationError` twin. The
  untouched paragraphs keep their review-time true grades.
- `django_strawberry_framework/exceptions.py::LookupValidationError`
  — true. C3's guard-arms bullet matches `validate_lookup_expr`:
  the non-`str` guard raises before splitting, and the
  `FieldError` arm converts Django's refusal (the `e.g.` clause
  tracks the owner's inline comment nearly verbatim); the six
  raises are now fully indexed. The untouched distinction
  paragraph, three bullets, and message sentence keep their
  review-time true grades.
- `django_strawberry_framework/exceptions.py::OptimizerError` —
  true. The C1/L1 bullet tracks the owner's Raises paragraph and
  the raise message nearly verbatim (`_reverse_order_by` rejects
  an entry with neither a `descending` flag nor a callable
  `desc()`; the raise statement lives in `_reverse_order_by`
  itself, single production caller in `apply_window_pagination`);
  placement after the reversed-keyset bullet keeps the two
  backward-window bullets adjacent. `a fallback` is the correct
  noun spelling and matches the owner's "falling back to
  per-parent" language. Own 14-statement census groups into
  exactly the 8 listed logical sites — the list is now complete.
- `tests/test_exceptions.py::test_empty_args_render_empty_string`
  — true. The body asserts `str(...) == ""`, standard
  `Exception()` semantics, mirroring the base-class docstring's
  own "exactly as with any other exception"; states the expected
  behavior, no "Tests that". The deleted-mechanism clause is gone
  (the base carries no render override).

Instruments: `build_tree_md.py --list-docstrings` passes on both
files (0 breaking each); `check_citations.py --paths ... --substrings
--json` reports 10 citations, 0 violations on the target (was 8;
the two new cites `optimizer/plans.py::_reverse_order_by` and
`utils/relations.py::relation_bool` resolve) and 0/0 on the test
module. No module first line changed (both byte-identical to
ITEM_BASELINE), so no TREE.md row is owed; the item diff touches
no TREE.md.

Diff hygiene: the added lines carry no process provenance (the
one pattern hit, "legacy lenient walk", mirrors the owner's own
established name — `_lenient_traverses_to_many`'s first line is
"Legacy lenient to-many walk" — in a present-tense rule, not
history narration; the remaining file-wide hits are the known
`worker`-in-`FrameworkError` and hunk-header accidents), no
line-number citation, no `we`/`you`/`I`, no "Tests that"/"Ensures".

Sibling verifiers: Performance Verification and Mechanics
Verification read whole. Neither routes a gap to Comments (both
state none). The Mechanics Handoff leaves the C1-C3 framing to
this pass: judged — the text-after bullets landed and grade true
above, and the Proofs govern over the header-scoping alternative.
The C2/C3-over-R2 tension is not a dispute (no `disputed:`
marker exists anywhere in the artifact): R2 permits omission but
forbids nothing, the Medium Proofs demand the bullets, and landed
true bullets cannot grade stale. R2's trigger is untouched (the
raise-site owners still omit the guards; the central index is
not the owner). The review Handoff's two open threads stay
non-findings (no reachable input demonstrated; untouched by this
diff).

Attacks on the landed prose, all passing (recorded, not
findings):

- A1 (C1/L1 string carve-out): a string order entry carries
  neither flag nor `desc()` yet never raises (toggled branch).
  Passing: the bullet mirrors the owner's own Raises paragraph
  verbatim; the carve-out lives in the owner's three-shapes
  paragraph where the full contract belongs. Demanding it in the
  one-line index would contradict the owner's phrasing — style
  preference, not a finding.
- A2 (M1 "precedes the failure", hyper-literal): on an
  empty-`path_infos` many segment the lenient True can coincide
  with (not strictly precede) strict's failure point. Passing:
  the operative claim (may answer True, never a bare False) is
  exactly true, and the phrasing matches the owner's contract
  language plus its pinned many-then-garbage examples.
- A3 (C2 scope): the unwrapped `relation_bool` calls in
  `classify_path` (`m2m` over `path_infos`, the five
  `relation_kind` flags) propagate as `ConfigurationError`, not
  this error. Passing: the bullet names only the `is_relation`
  flag arm, which is precisely the converted one — no overclaim.
- A4 (census): the Mechanics record's "12 raise statements in 6
  modules" miscounts its own enumeration (14 lines, 5 modules).
  Passing as an attack on the landed text: the slip is record
  prose, and both records agree on the operative fact (7 bullets,
  exactly `_reverse_order_by` missing); own census confirms 14
  statements grouping into the 8 now-listed sites.
- A5 (owner drift): `utils/relations.py`, `optimizer/plans.py`,
  `utils/truth.py`, `orders/sets.py` hash-identical to all three
  records' fingerprints — every owner read at review still stands.

Disputes: none recorded ("No finding disputed, discharged, or
deferred"). Nothing to judge.

Cells unverified: none. Default, sharded, and pg remain
inapplicable by construction — every Proof and instrument here is
a static shared-tree command over prose; the workspace runs only
re-ran the static greps inside the address copy.

Fingerprints (`git hash-object`, live tree at verify time):
`django_strawberry_framework/exceptions.py`
`93401220b5e2c528a421481721f0e2ac460aa0bd`;
`tests/test_exceptions.py`
`1374fef552bcc5c34c47d921a6db2f1f9c7ae07f`;
`django_strawberry_framework/utils/relations.py`
`05ff55b098382a4a7aafe5a097c3b5e906f8f985`;
`django_strawberry_framework/optimizer/plans.py`
`33140a766cd3fb2484a40fe499d466c8ced8b4a6`;
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9`;
`django_strawberry_framework/orders/sets.py`
`60859f2d54525acfdb3dc997d3e931ff3d58d956`.

Handoff: Comments verify pass 1 closed `verified`. Read beyond
the record's trace: the item diff whole (7 prose hunks), the four
landed docstrings whole against `classify_path`,
`validate_lookup_expr`, `relation_bool`, `_traverses_to_many`,
`_lenient_traverses_to_many`, `path_traverses_to_many`, and
`_reverse_order_by` bodies, Worker's `## Implementation` after
the proof step, and both sibling verifications whole (no gaps
routed to Comments). Conclusions not stated above: the C1/L1
hybrid and the C2/C3-over-R2 landings are upheld as true text
under governing Proofs; the file's prose is now complete
(OptimizerError 8/8 sites, both typed errors 6/6 raises indexed).
Open threads: none on Comments.
