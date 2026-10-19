# Review · Comments: `django_strawberry_framework/error_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=59dad4a566f3718e6d99572ef853455d0aabc101

## Trace

Read the whole live target (`django_strawberry_framework/error_policy.py`, 191
lines: module docstring, 3 symbol docstrings, 2 doc-comment blocks, no inline
`#` comments, no section banners) and the whole own test module
(`tests/test_error_policy.py`, 1061 lines: module docstring, every test,
helper-class and helper-function docstring, 10 section banners, 4 inline
comments). The target is dirty vs HEAD (the concurrent `describe_value` →
`truth.describe` migration, 4 insertions / 3 deletions, prose-untouched) but
byte-identical to ITEM_BASELINE (`git diff 59dad4a5 --` the three graded files
is empty); every grade below is against the live text at these fingerprints.

Also graded: every docstring and comment in the live tier holding prose about
the target's symbols (`examples/fakeshop/test_query/test_error_policy_api.py`,
1387 lines, read whole), and the prose about the target's symbols in
`tests/utils/test_policies.py`, `tests/forms/test_resolvers.py`,
`tests/auth/test_mutations.py`, `tests/mutations/test_write_transaction.py`,
`tests/mutations/test_permissions.py`, `tests/test_schema.py`,
`tests/extensions/test_debug.py`, `tests/test_exceptions.py`,
`tests/extensions/test_operation_state.py`, and `tests/test_ci_governance.py`.
Package neighbors read for the trace (prose defects there are Routed leads,
not findings): `extensions/error_policy.py` (whole),
`utils/policies.py` (whole), `resource_policy.py` (module docstring,
`_require_positive_int`, `ResourcePolicy`, `DEFAULT`/`_PACKAGE` blocks,
`resolve_resource_policy`, `ResourceLimitExceeded` bases), `schema.py`
(class error-policy paragraphs, `error_policy` property,
`_masked_return`, `_refused_chain`, execute overrides),
`conf.py` (`ERROR_POLICY_KEY` block, `error_policy_setting`),
`consumers.py` (streaming-seam paragraphs, import paragraph),
`extensions/debug.py` (masking-order prose, grep level),
`extensions/operation_state.py` (`_OperationBoundExtension` hooks, grep
level), `__init__.py` (re-exports, grep level). Contract sources:
spec-048 Decisions 7–11 (read, not grep level),
`docs/GLOSSARY.md` `ErrorPolicy` anchor (twin check only; standing docs
are outside this axis's population). Upstream behavior verified in the
installed strawberry-graphql 0.324.0 (`schema/schema.py`,
`extensions/context.py`, `extensions/runner.py`,
`extensions/base_extension.py`, `types`) and the floor 0.316.0
(ephemeral `--no-project` env), plus a Django-only unconfigured-settings
probe. Sibling records landed mid-pass and were read whole with their
Handoffs (both `no-findings`; Performance: cold; Mechanics: four
rejections and one glossary Routed lead that corroborates M1 — see it).

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/error_policy/comments/inspect/` plus
`error_policy.json` (blob `57a0bed1`, line count 191, matches the live
read). `build_tree_md.py --list-docstrings` passes on the target, the own
test module, and the live module (1 module, 0 breaking, each).
`check_citations.py --paths <file> --substrings --json` reports 8
citations, 0 violations in the target, 1 citation, 0 violations in the own
test module, and 0 citations in the live module. Provenance sweep
(REVIEW.md pattern) hits only kept spec-Decision pointers, two `now`
present-tense hits, and two `around` substring false positives. No
`we`/`you`/`I` in target or own test module (one `your` in the live tier
is L6; one quoted wire-text `you` is R9), no `Tests that`/`Ensures`, no
`.py:NN`, no public symbol without a docstring in the target.

Cells: default, sharded, and pg are all inapplicable by construction —
every Proof below is a static shared-tree command over prose, and the two
engine probes import strawberry/django only (never the package) and open
no database. No workspace runs were made; no run ids exist for this
record.

Fingerprints (`git hash-object` of every repo file read):

- `django_strawberry_framework/error_policy.py` 57a0bed1ba730f8e4c1f4c879d852274eac39f12
- `tests/test_error_policy.py` 0f0fec24b03ca8472f224cc7cefc3b6062f147bb
- `examples/fakeshop/test_query/test_error_policy_api.py` 6763a5814987bb41f326ec3326dab5015814b55f
- `django_strawberry_framework/extensions/error_policy.py` a1defd394d8eda9b698964030a09efe6914278db
- `django_strawberry_framework/utils/policies.py` 0a2b7dbad96594b5d668774218809c6a94d136be
- `django_strawberry_framework/resource_policy.py` cc3f9d80b9d55af8b725a77c73aba3d8110e0037
- `django_strawberry_framework/schema.py` 84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1
- `django_strawberry_framework/conf.py` 3820c575bfd4e3c384244d1bed460b75d3bb7681
- `django_strawberry_framework/consumers.py` 0791c04a6c7b2619562f33dc707b002cde718c6b
- `django_strawberry_framework/extensions/debug.py` 054e04df5915ed12c49ef63e4710feebca7388aa
- `django_strawberry_framework/extensions/operation_state.py` d9ed9cc67fea892afa2dd22a33236a52fc061fb1
- `django_strawberry_framework/__init__.py` 0ef72601ecac300ac87ff993af1b04a4f1bc335a
- `tests/utils/test_policies.py` 9ec80053095b70f35421e946cd9d54edbd497f29
- `tests/forms/test_resolvers.py` 6cab42c2ff6779e1a64e98bdc055d24ac6389378
- `tests/auth/test_mutations.py` ff8a261d09ca63a0f606673bf11b9262f2bb1f35
- `tests/mutations/test_write_transaction.py` 689e31f47ae0dc010e67386e4a076b782afac5ff
- `tests/mutations/test_permissions.py` a4472aee93454e446cfcb2773b840e7e247bc05e
- `tests/test_schema.py` 3676f7e8a9370966c3159264825857a599cdf085
- `tests/extensions/test_debug.py` 93843bd3deae18c0dce234990ce14d3594a85000
- `tests/test_exceptions.py` 4b5818c22d24865a38a44e73782b49ee3dc9f94d
- `tests/extensions/test_operation_state.py` 7509c1ccaa1c56c50be2ca3bc4337b75bcca90ce
- `tests/test_ci_governance.py` cfc66f6e028b3dabdabfdfd13bebd1ada656e3e0
- `docs/SPECS/spec-048-secure_output_defaults-0_0_14.md` c1a11bdbd632800103c2f67e0413b4442befeb0e

Upstream evidence (not git-tracked): strawberry 0.324.0 vs 0.316.0
`Schema.execute_sync` / `get_extensions` sources quoted in M3, and
`docs/review/temp-tests/error_policy/comments/floor_early_return_probe.py`
(`b1e55cdf2dc00ed8d6dfd6ee6cc95e8034a76bd`) printing
`teardown_saw=ExecutionResult(ExecutionResult)` on 0.324.0 and
`teardown_saw=None` on 0.316.0.

## Findings

### High

None. Every docstring and comment in the target grades true: the
classification paragraph matches
`django_strawberry_framework/extensions/error_policy.py::_is_unexpected`
and spec-048 Decision 8; the frozen paragraph matches the copy-per-read
`django_strawberry_framework/schema.py::DjangoSchema.error_policy` plus
`django_strawberry_framework/schema.py::_SCHEMA_ENFORCEMENT` off-schema
record; the `__post_init__` exact-type rationale cites the rule
`django_strawberry_framework/resource_policy.py::_require_positive_int`
actually states; the template/canonical separation matches the readers
(`default=_PACKAGE_ERROR_POLICY` in the resolver,
`django_strawberry_framework/extensions/error_policy.py::schema_error_policy`,
`_FALLBACK_ENFORCEMENT`); the `resolve_error_policy` precedence and
either-slot instance path match
`django_strawberry_framework/utils/policies.py::resolve_policy`
(including the setting-slot instance branch); `new_correlation_id`
matches `uuid4().hex` and its per-masked-error call site.

### Medium

- Observation: `tests/test_error_policy.py::test_the_policy_is_frozen_so_a_resolver_cannot_widen_its_own_request`
  docstring states `Frozen is the point: a request holding the policy cannot
  loosen it.` Both halves invert the documented boundary. The production
  `django_strawberry_framework/error_policy.py::ErrorPolicy` class
  docstring states the opposite mechanism verbatim (`Frozen is not what
  establishes that: it rejects setattr and admits
  policy.__dict__["enabled"] = False`), and the very next test in this
  file loosens the object it holds (`reached.__dict__["enabled"] = False`,
  then `assert reached.enabled is False`) while the stored policy stays
  masked. What a request cannot loosen is the stored enforcement record,
  and that is established by the copy boundary plus the off-schema
  record, not by frozenness. The test NAME shares the defect (`..._frozen_so_a_resolver_cannot_...`
  attributes the consequence to frozenness).
- Evidence: target class docstring frozen paragraph (lines 85-93) vs test
  docstring (line 211); sibling test
  `tests/test_error_policy.py::test_reading_schema_error_policy_answers_a_copy`
  (lines 342-346) proving the held object IS loosenable;
  `django_strawberry_framework/schema.py::DjangoSchema.error_policy`
  returning `copy_policy(...)` per read. The Mechanics sibling
  independently found the same inversion in the GLOSSARY `ErrorPolicy`
  anchor (`it is **frozen**, so a resolver holding it cannot loosen its
  own request's policy`) and routed it to Decisions; this finding is the
  test-prose twin, owned here.
- Impact: a reader trusting the sentence misjudges what enforces the
  masking boundary; taken literally it motivates deleting the copy
  boundary as redundant (`frozen is the point`), which would put one
  `__dict__` write away from unmasking every later request. Wrong
  stated mechanism for a security boundary (DRY principle 10: worse
  than none).
- Severity: Medium (stale behavioral claim in test prose inverting the
  target's authority mechanism).
- Recommendation: restate the docstring as the accident-vs-adversary
  distinction the bodies pin, and rename the test to match (the old
  node id is referenced nowhere else in the repo, so the rename is
  safe); see text-after.
- Must not change: n/a.
- Proof: `grep -c "Frozen is the point" tests/test_error_policy.py`
  prints `0` (1 today) and `grep -c
  "test_the_policy_is_frozen_so_a_resolver_cannot_widen_its_own_request"
  tests/test_error_policy.py` prints `0` (1 today); the rewritten
  docstring and name earn grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_error_policy.py::test_the_policy_is_frozen_so_a_resolver_cannot_widen_its_own_request`.
- Grade: stale (states the opposite of the production mechanism; false
  under the plain reading and contradicted by the adjacent test).
- Text-before:
  `Frozen is the point: a request holding the policy cannot loosen it.`
  (docstring) and the test name above.
- Text-after:
  `Frozen rejects the accident, not the adversary: a plain attribute assignment raises, while the __dict__ write frozen admits touches only the writer's own copy.`
  (docstring) and the test renamed in plain text to
  test_the_policy_is_frozen_so_a_plain_assignment_raises in
  tests/test_error_policy.py.

- Observation: `tests/test_error_policy.py::test_the_schema_resolves_and_exposes_its_policy_once`
  docstring states ``schema.error_policy`` `is the single resolved
  object the extension reads.` Identity-wise there is no single
  object: every attribute read answers a fresh
  `django_strawberry_framework/utils/policies.py::copy_policy`
  duplicate, the extension reads its own further copy through
  `django_strawberry_framework/extensions/error_policy.py::schema_error_policy`,
  and the stored record sits off-schema. In a file whose recurring
  theme is `is` vs `==`, `the single resolved object` reads as an
  identity claim, and it contradicts this module's own tier bullet
  (`the schema attribute answering a duplicate of the stored policy`)
  and the next test's `The object a resolver can reach is not the
  stored policy.` The test name (`resolves ... once`) is true and
  stays; only the docstring overclaims.
- Evidence: `django_strawberry_framework/schema.py::DjangoSchema.error_policy`
  body (`return copy_policy(_enforcement(self).error_policy)`);
  `django_strawberry_framework/extensions/error_policy.py::schema_error_policy`
  re-reading the attribute per operation; the module docstring bullet
  (lines 20-21) and the adjacent test docstring (lines 336-341).
- Impact: a reader trusting the sentence believes attribute reads are
  identical (`schema.error_policy is schema.error_policy` is False)
  and that the extension shares the caller's object; same hazard
  family as the finding above (the copy boundary looks redundant).
- Severity: Medium (stale identity claim in test prose about the
  target's contractual copy boundary).
- Recommendation: restate as value resolution without the identity
  claim; see text-after.
- Must not change: n/a.
- Proof: `grep -c "the single resolved object the extension reads"
  tests/test_error_policy.py` prints `0` (1 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_error_policy.py::test_the_schema_resolves_and_exposes_its_policy_once`.
- Grade: stale (false identity claim under the plain reading).
- Text-before:
  ` ``schema.error_policy`` is the single resolved object the extension reads. `
- Text-after:
  `The schema resolves its policy once, at construction, and exposes the resolution for the extension to read.`

- Observation: `tests/test_error_policy.py::_run_teardown` docstring
  states the harness builds directly `because the two cases below are
  exactly the ones no request produces: a sync parse/validation early
  return leaves execution_context.result at None, and Strawberry never
  hands the hook a result object it did not build.` The mechanism
  sentence is wrong on both ends of the supported engine range, in
  opposite directions. On the installed 0.324.0 the sync early return
  ASSIGNS the pre-execution result before the hooks unwind
  (`execution_context.result = pre_execution_result`, inside
  `operation()`), so teardown-over-None is unreachable and `leaves ...
  at None` is false. On the floor 0.316.0 the early return assigns
  nothing, so EVERY sync parse/validation-error request drives the
  teardown over result `None` and `no request produces` is false.
  Only the second conjunct (engine-built results only) holds on both.
- Evidence: upstream `Schema.execute_sync` sources (floor: bare
  `return ExecutionResult(...)` inside `operation()` with
  `result: ... = None` default; 0.324.0: assignment plus `Match the
  async path by exposing pre-execution results to operation extensions
  before their hooks unwind`); `SchemaExtensionsRunner.operation`
  `contextmanager`/`ExitStack` wrap (post-yield body runs on normal
  completion only, which always has result assigned on 0.324.0);
  behavioral probe
  `docs/review/temp-tests/error_policy/comments/floor_early_return_probe.py`
  printing `teardown_saw=ExecutionResult(ExecutionResult)` on 0.324.0
  and `teardown_saw=None` on 0.316.0. The sentence's model dates to
  the spec era (spec-048 Decision 11 still parenthesizes `A result
  that is None (a sync parse/validation early return)`); upstream
  changed under it.
- Impact: a reader trusting `no request produces` could delete the
  None-tolerance test as dead defense, but on the floor that path is
  live on every parse/validation error; a reader trusting `leaves at
  None` misdescribes the current engine to the next probe. The test
  itself is valid on both engines; only the stated reason is stale.
- Severity: Medium (wrong stated engine mechanism plus wrong
  reachability claim; deletion hazard for a floor-live path).
- Recommendation: restate version-agnostically (the None-visibility
  IS engine-version behavior; the direct harness stands because no
  request can be RELIED on to produce these shapes); see text-after.
- Must not change: n/a.
- Proof: `grep -cF 'leaves ``execution_context.result`` at ``None``'
  tests/test_error_policy.py` prints `0` (1 today); the rewritten
  docstring earns grade true (no engine-version claim beyond
  `engine-version behavior`, which the probe pair proves).
- Freshness: none beyond Trace.
- Symbol: `tests/test_error_policy.py::_run_teardown`.
- Grade: stale (upstream changed under it; false mechanism on
  latest, false conclusion on the floor).
- Text-before:
  `Built directly rather than through a schema because the two cases below are exactly the ones no request produces: a sync parse/validation early return leaves ``execution_context.result`` at ``None``, and Strawberry never hands the hook a result object it did not build.`
- Text-after:
  `Built directly rather than through a schema because a request cannot be relied on to hand the hook these shapes: whether the hooks see ``execution_context.result`` at ``None`` on a parse/validation early return is engine-version behavior, and Strawberry never hands the hook a result object it did not build.`

- Observation: `examples/fakeshop/test_query/test_error_policy_api.py::_masked_error`
  docstring states `Every masking row funnels through here, so "the
  error was masked" always means the same three things: the policy's
  message verbatim, a well-formed correlation id under the configured
  extensions key, and no other extension keys smuggled alongside it.`
  The helper asserts two of the three (message equality, id
  fullmatch); nothing asserts the extensions key set, so an error
  carrying `{"correlationId": ..., "code": ...}` passes the gate
  that claims to exclude it. (The system satisfies the third leg
  today —
  `django_strawberry_framework/extensions/error_policy.py::_masked`
  builds exactly one key — which is why the suite is green; the leg
  is true but unenforced.)
- Evidence: helper body (lines 593-598: length, message, key read,
  fullmatch; no key-set assertion) vs docstring (lines 587-590).
- Impact: the uniformity promise governs every masking row's meaning
  (30+ rows funnel through here); a key-smuggling regression in the
  replacement builder would pass the whole live tier's masked-shape
  gate while the docstring claims otherwise.
- Severity: Medium (stale uniformity claim in test prose about what
  the tier's central gate enforces).
- Recommendation: preferred — add the missing enforcement,
  `assert set(error["extensions"]) == {key}`, after the fullmatch
  line, keeping the docstring (true once the assert lands);
  fallback — weaken the docstring to two things. See text-after.
- Must not change: n/a.
- Proof: `test $(grep -cF "no other extension keys"
  examples/fakeshop/test_query/test_error_policy_api.py) -eq 0 -o
  $(grep -cE "assert .*extensions.*key"
  examples/fakeshop/test_query/test_error_policy_api.py) -ge 1`
  succeeds (today: first count 1, second 0); the landed
  helper-plus-docstring earns grade true (three-claim prose iff a
  key-set assertion is present).
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_error_policy_api.py::_masked_error`.
- Grade: stale (overclaims the helper's assertions two-vs-three).
- Text-before:
  `Every masking row funnels through here, so "the error was masked" always means the same three things: the policy's message verbatim, a well-formed correlation id under the configured extensions key, and no other extension keys smuggled alongside it.`
- Text-after (fallback; preferred is the assertion with prose
  unchanged):
  `Every masking row funnels through here, so "the error was masked" always means the same two things: the policy's message verbatim and a well-formed correlation id under the configured extensions key.`

- Observation: `examples/fakeshop/test_query/test_error_policy_api.py::test_debug_true_restores_the_original_message_end_to_end`
  docstring states the gate `is read per operation rather than
  captured at construction - which this row proves incidentally,
  since the schema is built while the override is already active but
  the sibling rows above built theirs under the ambient DEBUG=False.`
  The row proves nothing about read time: the mount builds the schema
  per request INSIDE the override, so build-time and request-time
  DEBUG coincide here (True/True) and in every sibling (False/False);
  a capture-at-construction regression passes all of them. The system
  property is true and spec-pinned (spec-048 Decision 9: `Read at
  operation time`), but this row is consistent with both models.
- Evidence: `_probe_view` builds per request (lines 210-212);
  `_override_settings` wraps the whole `_post` (line 975); sibling
  rows build under ambient False and request under ambient False.
  No row in either tier builds under one DEBUG value and requests
  under another.
- Impact: a reader believes per-operation DEBUG read is pinned live
  and would not add the build-then-flip row that actually pins it;
  the capture regression the sentence dismisses passes silently.
- Severity: Medium (false proof claim in test prose about a
  spec-pinned read-time property).
- Recommendation: drop the false proof clause (the remaining
  sentences state the true system property); the build-under-one-value
  / request-under-another row that would make the original claim true
  is noted here for Worker-2's judgment, not required by this Proof.
- Must not change: n/a.
- Proof: `grep -c "which this row proves"
  examples/fakeshop/test_query/test_error_policy_api.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_error_policy_api.py::test_debug_true_restores_the_original_message_end_to_end`.
- Grade: stale (false `proves` claim; the row cannot distinguish
  the models).
- Text-before:
  `The local traceback is the reason the setting exists, and the gate is read per operation rather than captured at construction - which this row proves incidentally, since the schema is built while the override is already active but the sibling rows above built theirs under the ambient ``DEBUG=False``.`
- Text-after:
  `The local traceback is the reason the setting exists, and the gate is read per operation rather than captured at construction.`

### Low

- Observation: `tests/test_error_policy.py::_HostileMessage` docstring
  states `A str SUBCLASS: isinstance-valid, and consumer code in every
  dunder.` This double overrides one dunder (`__format__`); the rest
  are `str`'s. The categorical `in every dunder` overstates what the
  double carries, and this file's own
  `tests/test_error_policy.py::_PolicySubclass` shows the precise
  house phrasing (`its field reads would be code of its own`,
  conditional). The operative belief instilled (distrust subclass
  dunders) is correct; only the letter overreaches.
- Evidence: class body (lines 160-164: one method) vs docstring
  (line 161); `_PolicySubclass` docstring (line 608) for the
  conditional precedent.
- Impact: bounded clarity; a reader takes the category rule as a
  description of the double.
- Severity: Low (categorical wording where the house uses the
  conditional).
- Recommendation: describe the double, not the category (the test
  docstring below already carries the category rationale); see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "consumer code in every dunder"
  tests/test_error_policy.py` prints `0` (1 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_error_policy.py::_HostileMessage`.
- Grade: stale (categorical claim false of the double; instills the
  right rule with the wrong letter).
- Text-before:
  `A ``str`` SUBCLASS: ``isinstance``-valid, and consumer code in every dunder.`
- Text-after:
  `A ``str`` SUBCLASS: ``isinstance``-valid, with a hostile ``__format__``.`

- Observation: `tests/test_error_policy.py::_UnreadableSettings`
  docstring states `The shape settings presents when the whole wrapped
  holder is gone - what an unconfigured process answers, and what the
  gate must survive as surely as it survives a deleted DEBUG.` An
  unconfigured process answers `ImproperlyConfigured`, not the
  `AttributeError` this double raises (verified: bare
  `settings.DEBUG` with no settings module raises
  `ImproperlyConfigured: Requested setting DEBUG, but settings are
  not configured...`, and it is not an `AttributeError` subclass);
  and the test REPLACES the holder rather than the holder being
  gone. The gate catches both exceptions so the test is valid and
  the test docstring below it is precise; only this motivation
  paragraph misidentifies the doubled shape.
- Evidence: double body (lines 737-738: `__getattr__` raising
  `AttributeError`) vs Django behavior (probe above);
  `django_strawberry_framework/extensions/error_policy.py::masking_is_active`
  catching `(AttributeError, ImproperlyConfigured)`.
- Impact: bounded clarity; a gate author reading only this paragraph
  takes unconfigured-DEBUG for an `AttributeError` shape. Contained:
  the gate docstring and the test docstring state both failures
  correctly.
- Severity: Low (misidentified doubled failure mode in a motivation
  paragraph).
- Recommendation: describe what the double delivers and what it must
  survive, without the unconfigured identification; see text-after.
- Must not change: n/a.
- Proof: `grep -c "an unconfigured process answers"
  tests/test_error_policy.py` prints `0` (1 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_error_policy.py::_UnreadableSettings`.
- Grade: stale (wrong exception identity for the doubled shape).
- Text-before:
  `The shape ``settings`` presents when the whole wrapped holder is gone - what an unconfigured process answers, and what the gate must survive as surely as it survives a deleted ``DEBUG``.`
- Text-after:
  `One unreadable-``DEBUG`` shape: the wrapped holder answers ``AttributeError`` to every read, which the gate must survive as surely as a deleted ``DEBUG``.`

- Observation: the `HOOK_HALVES` comment in
  `examples/fakeshop/test_query/test_error_policy_api.py` states
  `Every hook and half a consumer extension can fail at where the
  failure escapes into upstream's own error conversion rather than
  into a located field error.` Under the plain (existence-quantified)
  reading this claims completeness, but the parse halves,
  operation-setup, and execute-teardown also escape into upstream
  conversion — hook failures never become located field errors, so
  the `where` clause excludes nothing and the complete set is eight
  halves, not four. True only under the `the witness's armed points`
  reading, which the sentence does not state.
- Evidence: the four `_fail_hook` call sites in `_HookFailure`
  (`validate-setup`, `validate-teardown`, `operation-teardown`,
  `execute-setup`) vs the unlisted halves, all of which unwind the
  operation lifecycle into `except Exception` conversion exactly the
  same way (per the extensions module's own `an exception escaping
  any HOOK` paragraph).
- Impact: bounded; a reader takes the four rows for the complete
  conversion-escaping taxonomy. No test gap follows: every half is
  wire-identical at the return seam, so unlisted halves would be
  redundant rows.
- Severity: Low (false completeness under the plain reading).
- Recommendation: quantify over the witness's armed points; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "Every hook and half a consumer extension can fail
  at" examples/fakeshop/test_query/test_error_policy_api.py` prints
  `0` (1 today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_error_policy_api.py::HOOK_HALVES`.
- Grade: stale (false completeness under the plain reading).
- Text-before:
  `Every hook and half a consumer extension can fail at where the failure escapes into upstream's own error conversion rather than into a located field error.`
- Text-after:
  `The hook halves the witness can fail at, each escaping into upstream's own error conversion rather than into a located field error.`

- Observation: `examples/fakeshop/test_query/test_error_policy_api.py::test_an_exception_from_a_consumer_hook_is_masked_like_a_resolver_exception`
  docstring states `The four halves are their own rows because each
  escapes from a DIFFERENT place - the validation stage, the
  execution stage, and the operation teardown ...`. Four halves,
  three places: validate-setup and validate-teardown share the
  validation stage, so `each ... a DIFFERENT place` is false on its
  face, and the enumeration names stages for two halves but a half
  (`operation teardown`) for the third.
- Evidence: `HOOK_HALVES` (two validation halves, one execution
  half, one operation half) vs the sentence's `DIFFERENT place`
  plus three-place enumeration.
- Impact: bounded clarity; the rows are correctly split, only the
  count in the rationale is off.
- Severity: Low (self-inconsistent enumeration).
- Recommendation: name halves, not stages; see text-after.
- Must not change: n/a.
- Proof: `grep -c "each escapes from a DIFFERENT place"
  examples/fakeshop/test_query/test_error_policy_api.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_error_policy_api.py::test_an_exception_from_a_consumer_hook_is_masked_like_a_resolver_exception`.
- Grade: stale (four halves cannot each escape from a different one
  of three places).
- Text-before:
  `The four halves are their own rows because each escapes from a DIFFERENT place - the validation stage, the execution stage, and the operation teardown the masking authority itself unwinds behind - and a masked surface with a hole shaped like any one of them looks identical to a correct one on every resolver row in this file.`
- Text-after:
  `The four halves are their own rows because each escapes from a different half - both halves of the validation stage, execution setup, and the operation teardown the masking authority itself unwinds behind - and a masked surface with a hole shaped like any one of them looks identical to a correct one on every resolver row in this file.`

- Observation: `examples/fakeshop/test_query/test_error_policy_api.py::test_a_malformed_relation_globalid_is_masked_with_a_correlation_id`
  docstring states `All three write flavors share the one input
  scalar, so they answer byte-identically apart from path.` The
  correlation ids are minted fresh per masked error, so no two rows
  are byte-identical even apart from `path` — and the test asserts
  per-row shape only, never a cross-row comparison.
- Evidence: `django_strawberry_framework/error_policy.py::new_correlation_id`
  (`uuid4().hex` per `_masked` call) vs `byte-identically`; test
  body asserting shape per flavor, no inter-row equality.
- Impact: bounded; a reader could write a byte-comparison across
  rows from this sentence and watch it fail on the random ids.
- Severity: Low (false `byte-identically` under the plain reading).
- Recommendation: state shape sameness with the id exception; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "byte-identically apart from"
  examples/fakeshop/test_query/test_error_policy_api.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_error_policy_api.py::test_a_malformed_relation_globalid_is_masked_with_a_correlation_id`.
- Grade: stale (random ids defeat byte-identity).
- Text-before:
  `All three write flavors share the one input scalar, so they answer byte-identically apart from ``path``.`
- Text-after:
  `All three write flavors share the one input scalar, so they answer the same masked shape apart from ``path`` (and the fresh correlation id).`

- Observation: `examples/fakeshop/test_query/test_error_policy_api.py::test_the_explicit_opt_out_returns_the_original_message_under_debug_false`
  docstring states the opt-out `is the recorded decision to own your
  own masking.` Second person addressing the reader; the axis bans
  `you`/`your`, and the target's own
  `django_strawberry_framework/error_policy.py::ErrorPolicy`
  `enabled` paragraph shows the house third person (`A consumer who
  owns their own masking`).
- Evidence: first line (line 1046) vs the axis voice rule and the
  target docstring's `their` phrasing.
- Impact: bounded voice defect in one contract sentence.
- Severity: Low (voice defect: `your` addressing the reader).
- Recommendation: de-pronominalize into the target's third person;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c "to own your own masking"
  examples/fakeshop/test_query/test_error_policy_api.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_error_policy_api.py::test_the_explicit_opt_out_returns_the_original_message_under_debug_false`.
- Grade: voice defect (`your` addressing the reader).
- Text-before:
  ```error_policy={"enabled": False}`` is the recorded decision to own your own masking.`
- Text-after:
  ```error_policy={"enabled": False}`` is the recorded decision of a consumer who owns their own masking.`

## Rejected

- R1 — Target module `Spec:` + `Target release: 0.0.14` lines.
  Standing multi-module convention (the connection pass records seven
  modules carrying it; the spec pointer beside it is kept, and every
  spec-Decision pointer in the graded files was content-verified
  against Decisions 8/9/10/11). Trigger: the convention retired.
- R2 — `cannot match anything else` (target `new_correlation_id`
  docstring; own-test `test_a_correlation_id_is_thirty_two_lowercase_hex_characters`).
  An accidental 32-hex collision in these logs is cryptographically
  excluded, and the intended contrast (fixed-width vs
  substring-matching counters/timestamps) holds; the absolute
  `cannot` reads against that contrast. Trigger: a realistic
  longer-hex token appearing in these logs.
- R3 — `Nothing in the package reads this name`
  (`DEFAULT_ERROR_POLICY` doc-comment). Scoped by its own sentence
  to fallback reads (`what the fallbacks read is
  _PACKAGE_ERROR_POLICY`); the single import-time minting read is
  stated in the adjacent `_PACKAGE_ERROR_POLICY` block, and the
  Mechanics sibling independently upheld the sentence for masking
  reads. Trigger: a masking-time read of the exported name.
- R4 — 4 undocumented test functions
  (`test_the_setting_supplies_the_policy_when_no_argument_does`,
  `test_a_non_mapping_policy_setting_is_rejected`,
  `test_a_non_mapping_policy_argument_is_rejected`,
  `test_the_extension_replaces_a_result_that_rejects_safe_field_adoption`)
  plus the one-line `_resolve` passthrough (live tier). Names state
  the expected behavior; no looks-for entry requires test or
  private-helper docstrings. Trigger: none.
- R5 — 12 nominal factory-helper first lines (live tier:
  `_probe_query_type`, `_probe_async_view`, `_error_policy_factory`,
  `_hook_exception`, `_deliberate_hook_exception`,
  `_shared_error_extension`, `_shared_consumer_extension`,
  `_fresh_consumer_extension`, `_shared_entry_entry`,
  `_shared_entry_schema`, `_assert_masked_and_clean`,
  `_package_error_records`). Factory-describer family convention
  (`The X...` = `this returns the X`); rewriting one site would make
  it inconsistent with its eleven siblings. Trigger: a maintainer
  decision enforcing mood on test helpers.
- R6 — `which it used to answer as absence`
  (`_SneakyError` docstring). Regression motivation with true
  behavioral claims (a defaulted `getattr` swallows the
  `AttributeError`; the old answer was the deliberate-delivery
  branch), same accepted shape as prior `Pre-fix`/`The old ...`
  records. Trigger: the design changing under it.
- R7 — Bare `(spec-048 Decision N)` pointers (own-test Decisions 10
  and 11; live-tier Decisions 8, 9, 11; module `three columns`
  pointer). Spec named at each use; every one content-verified
  against the Decision text (order/LIFO/debug-rows, one
  implementation/both shapes, structural table/completion,
  DEBUG-gate/path-retained/id-pinned/log-pinned). Trigger: an anchor
  removed or renumbered.
- R8 — `now` hits (target line 144 `holds now`; live line 278 `for
  the row running now`) and `Around`/`around` substring noise.
  Present-tense state descriptions naming no process artifact.
  Trigger: none.
- R9 — `you may not do this` (live permission-denial docstring,
  line 866). Quotation of the wire-visible denial text, not an
  address to the reader. Trigger: none.
- R10 — `A parse or validation early return has nothing to mask.`
  (`test_a_none_result_is_a_no_op`). Literally true on both engines
  (floor: `None` fails the shape gate; latest: the pre-execution
  result's errors are all deliberate). The stale
  None-means-early-return association lives in `_run_teardown`'s
  docstring (the Medium finding above), not here. Trigger: that
  finding's fix reframing this test.
- R11 — `A consumer's own extension keeps its order relative to its
  peers.` (single-entry chain test). True (order preserved;
  trivially with one entry); weak in that it does not name the
  policy/resource sandwich the body pins, but weakness is not
  falsity. Trigger: a multi-entry order test superseding it.
- R12 — `a fresh entry` (`ENTRY_SPELLINGS` comment). Consistent
  with this file's `entry` vocabulary (an `extensions=[...]` list
  member); the plain reading in context is the fresh-factory
  spelling, which does resolve per operation. Trigger: none.

## Routed leads

- Routed: `django_strawberry_framework/extensions/error_policy.py::is_maskable_result`
  — `What the gate excludes is what makes it necessary ... The
  operation-teardown seam meets a sync parse or validation
  early-return, which has nothing masked to begin with.` On the
  installed engine the early return is ADMITTED (a strawberry
  `ExecutionResult`, as the docstring's own preceding sentence
  states for `PreExecutionError`), so listing it under `what the
  gate excludes` is the same floor-model staleness as this
  record's `_run_teardown` finding (behaviorally proven split
  0.316.0 vs 0.324.0). Owner: the `extensions/error_policy.py`
  item (pending).
- Routed: `django_strawberry_framework/conf.py::ERROR_POLICY_KEY`
  (doc-comment) — `The deployment's production error policy, as a
  mapping of ErrorPolicy option names to values`. The setting slot
  also accepts an `ErrorPolicy` instance (deliberate:
  `django_strawberry_framework/utils/policies.py::resolve_policy`
  setting-instance branch with its own rationale comment, pinned
  by `tests/utils/test_policies.py::test_an_instance_through_the_setting_slot_is_taken_on_the_same_terms`,
  and stated publicly by this target's `An ErrorPolicy instance
  from either override slot`), so `as a mapping` omits a
  supported spelling; the twin `RESOURCE_POLICY_KEY` comment and
  the GLOSSARY `ErrorPolicy` anchor (`then the
  ...["ERROR_POLICY"] mapping`) share the omission. Owner: the
  `conf.py` item is verified/closed, so Worker-0's call
  (dispatch or `## Decisions`).

Handoff: Comments review is closed with 5 Medium and 6 Low findings,
all in test prose — the 191-line target itself grades true throughout,
and both siblings closed `no-findings` (Performance: cold; Mechanics:
four rejections). Read beyond the record's trace: the GLOSSARY
`ErrorPolicy` anchor (twin-check for the frozen finding only; the
glossary instance itself is the Mechanics sibling's routed lead, not
mine), the refusal chain in `schema.py` (to judge the live witness
docstrings true), and floor-vs-installed upstream sources plus two
strawberry-only behavioral probes (no package import, no database, no
workspace runs). Conclusions the findings do not state: the
`_run_teardown` staleness is upstream drift inside the supported range
(the floor still behaves the spec-era way), so its fix must stay
version-agnostic; the `_masked_error` preferred fix adds one
assertion rather than weakening prose; the DEBUG-read-time property
has no live pin anywhere and that gap is noted, not owned. Open
threads: the two Routed leads above; the `_masked_error` Proof is
disjunctive by design (assertion present OR third clause gone) so
either Worker-2 outcome verifies. No Cross-axis findings: nothing in
this pass belongs to Performance or Mechanics.

## Verification (Comments)

Step 1 — item diff identity. `git diff
59dad4a566f3718e6d99572ef853455d0aabc101 -- tests/test_error_policy.py
examples/fakeshop/test_query/test_error_policy_api.py` hashes
`sha256:364ed475b177c422db80426ba8c0dcee8f082119300000afb79c6d8897e01b2a`,
identical to `docs/review/temp-tests/error_policy/diff/pass-1.diff`
(+32/-23, 2 files). The tree did not move under the pass. Ordering
note: orientation read `## Implementation (Worker-2)` before the Proof
lines below were executed; the Proofs are verbatim mechanical counts
taken from this record alone, so no verdict depends on that order.

Proof lines — all 11 run verbatim in the shared tree (this record's
Trace establishes every Proof as a static shared-tree command; no
record carries a `## Cross-axis (for Comments)` section — confirmed by
grep: the only `Cross-axis` mentions are Handoff/verification prose
stating none exists). Results: M1a `0`, M1b `0`, M2 `0`, M3 `0`, M4
disjunction SUCCEEDS via the preferred disjunct (`no other extension
keys` count 1 kept, `assert .*extensions.*key` count 1 added), M5 `0`,
L1 `0`, L2 `0`, L3 `0`, L4 `0`, L5 `0`, L6 `0`. (The trailing `grep
-c` exit 1 is zero-matches, as designed.)

Worker-2 numbers — none owed for this axis (Comments findings; no
before/after). The change-safety evidence (reconstructions + suites)
is judged below instead.

Whole-diff read — 11 hunks in 2 files, target absent (`git diff
<ITEM_BASELINE> -- django_strawberry_framework/error_policy.py` is 0
bytes; blob `57a0bed1` matches all three review fingerprints): 10
docstring/comment prose hunks, the M1 test-function rename, the M4
key-set assertion. The prose-diff instrument
(`review_changed_python_diffs_against_head.py --prose`, output under
my scratch `diff/`) marks exactly the M1 hunk `[code changed too]`
and 9 pure-prose hunks; the M4 assert-only hunk carries no prose and
appears only in the full diff — the REVIEW.md shape.

Grades — every docstring/comment the diff wrote or moved, each as the
whole docstring it sits in, against its body and one real caller:

- M1 (rename + docstring): true. `a plain assignment raises` is pinned
  by the body (`pytest.raises(Exception, match="cannot assign to
  field")` on the frozen template). The generalized second sentence
  (`touches only the object held, never the stored enforcement
  record`) holds for the template object this test writes (pinned by
  sibling `test_a_written_exported_default_reaches_no_resolution`)
  AND for a resolver-held copy (pinned by sibling
  `test_reading_schema_error_policy_answers_a_copy`) — strictly more
  accurate than the text-after's `writer's own copy` for this test's
  object. The new name states the expected behavior, no banned voice.
- M2: true. Verbatim text-after. `resolve_error_policy` is called once
  at `schema.py:862` (`__init__`); reads answer
  `copy_policy(_enforcement(self).error_policy)` (`schema.py:996`).
  No identity claim remains; the kept test name stays true.
- M3: true. Verbatim text-after. Version-agnostic: its only engine
  claim is `engine-version behavior`, which this record's probe pair
  (0.324.0 `ExecutionResult` vs 0.316.0 `None`) proves.
- M4 (preferred assertion, docstring unchanged): true as
  helper-plus-docstring. The helper now enforces all three claimed
  things (message equality, id fullmatch, `set(error["extensions"])
  == {key}`); the assert reuses the same `key` parameter the
  docstring's `configured extensions key` names, so prose and gate
  stay consistent under any spelling. Liveness is corroborated by the
  Mechanics verifier's smuggle probe (a `"code"` key fails exactly
  the declared live row at the new assert).
- M5: true. False `which this row proves` clause gone; the remainder
  states the spec-048 Decision 9 system property with no proof claim.
  The build-then-flip row stays unadded, correctly: the Proof
  requires only the clause's removal (concur with Worker-2 and the
  Mechanics verifier).
- L1: true. `with a hostile __format__` describes exactly the double's
  one override; the categorical overreach is gone.
- L2: true. First line kept; the motivation paragraph now delivers one
  `AttributeError`-on-every-read shape, matching the `__getattr__`
  body, with no unconfigured-process identification.
- L3: true. Quantified over the witness's armed points; the 4
  `_fail_hook(...)` call sites equal the 4 `HOOK_HALVES` entries.
- L4: true. `each escapes from a different half` plus the 2+1+1
  enumeration is self-consistent for four halves.
- L5: true. `the same masked shape apart from path (and the fresh
  correlation id)` excepts exactly what `uuid4().hex` per `_masked`
  call defeats.
- L6: true. Third-person `of a consumer who owns their own masking`
  matches the target's house phrasing; the rest of the docstring is
  untouched and true.

M1 rename hygiene — old node id: 0 hits across the live tree
(`tests/`, `examples/`, `django_strawberry_framework/`, `scripts/`);
it survives only in per-cycle review prose and Worker-2's baseline
scratch copy (both exempt artifacts). New node id: exactly one live
site (the `def` line). `check_citations.py --cited-by` reports 0
citing sites for each across 550 files. The new node runs 1 passed
at my address (`review-20260929T041317-fd6c23`) — collected exactly
once.

Two-diff evidence shape — judged sound, rebuilt independently. My own
reconstructions under `verify-comments-1/` (ITEM_BASELINE text plus
one line each; `diff` proves each is a single line) give
`--code-digest` exit 0 against the live files with digests identical
to Worker-2's (`e3e57697...`, `9a19bd5e...`); whole-file digests exit
1 with identical baselines (`d6861ddb...`, `a5b4beed...`). Exactly two
AST-significant lines changed; all 10 prose hunks moved no code.
Suites re-run first-hand at my address, both green and unchanged in
shape: own module 66 passed (`review-20260929T041326-0464c2`),
live module 74 passed (`review-20260929T041331-14ae36`).

Instruments — `build_tree_md.py --list-docstrings`: 1 module, 0
breaking, on each changed file (same as review time); both module
first lines are byte-identical baseline-vs-live, so no TREE.md row is
owed (`git diff <ITEM_BASELINE> -- docs/TREE.md` is empty).
`check_citations.py --paths <file> --substrings --json`: own test 1
citation resolves, 0 violations (the pre-existing
`resource_policy.py::_require_positive_int` cite, untouched by the
diff); live tier 0 citations, 0 violations — matching review-time
counts. Added-lines sweeps over the item diff: process provenance 0,
line-number citations 0, `we`/`you`/`I` 0, `Tests that`/`Ensures` 0.

Sibling gaps routed to Comments — Performance: none (`no new finding,
no gap, no open thread`). Mechanics: the M1 generalized second
sentence and the M5 text-after, deliberately ungraded there — both
graded true above. Its 13-vs-12 call-site census correction is report
accuracy only: no landed prose states a count, and all 13 sites use
the default key with the suite executing every one green, so no
grade depends on the number.

Attacks on the landed prose — M4 bypass hunt: the two
`DEFAULT_ERROR_POLICY.message` assertions outside `_masked_error`
are (a) the two-error id-uniqueness row, a multi-error shape the
`len == 1` helper never served (outside the `masking row`
vocabulary the review pass graded), and (b) a line inside
`_assert_masked_and_clean`, which funnels through the helper on its
first line. Both fail as bypasses; no finding. M2 resolve-once: a
single `resolve_error_policy` call site in `__init__` — holds. L3
armed-points census: 4 call sites, 4 tuple entries — holds. M1
generalization under both held objects (template, handed-out copy)
— holds via the two sibling pins, both green.

Disputes — none. No `disputed:` line in `## Implementation
(Worker-2)`; Worker-2 reports zero disputes.

Cells — default exercised (three workspace runs above); sharded and
pg remain inapplicable by construction (static prose proofs plus
suites over a target that reaches no database, alias, or dialect
decision — concur with the review). Cells unverified: none.

New findings — none. Rejections R1-R12 and both Routed leads stand
untouched; no hunk bears on any of them.

Fingerprints (`git hash-object`, post-verify):
`tests/test_error_policy.py`
`9a72cdb83d4739be4018a3c58d0bf2736b63f569`;
`examples/fakeshop/test_query/test_error_policy_api.py`
`071b113feeaf9cee30ccda5941614c423251459c`;
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12`;
`scripts/review_inspect.py`
`d00ccd080d8ec07a20787ae83fed01f00d5d8f34` — all four match
Worker-2's post-edit values, so nothing drifted after the pass.

Scratch: `docs/review/temp-tests/error_policy/verify-comments-1/`
holds `baseline_test_error_policy.py`,
`baseline_test_error_policy_api.py`, `recon_rename_only.py`,
`recon_assert_only.py`, and the prose-diff instrument output under
`diff/`. Run ids: `review-20260929T041317-fd6c23` (renamed node),
`review-20260929T041326-0464c2` (own module, 66 passed),
`review-20260929T041331-14ae36` (live module, 74 passed).

Handoff: Comments verify pass 1 is closed with `Status: verified`.
All 11 findings landed (M4 via the preferred assertion, M1 with the
rename plus a strictly-more-accurate generalization), every landed
docstring grades true whole, the rename is retired cleanly and
collected once, and the two-diff evidence shape reproduces exactly
from independent reconstructions. Read beyond this section's trace:
the whole item diff, the whole live `_masked_error` helper with its
call-site census, the two bypass-candidate assertion sites, the
sibling M1 pins, and both sibling verifiers' `## Verification`
sections. Open threads: none. The two Routed leads belong to other
items and are untouched by this diff.
