# Review · Comments: `django_strawberry_framework/schema.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5ef09ed4565b774a3f9cda2f473514732bf12064

## Trace

Read the whole live target (`django_strawberry_framework/schema.py`, 1408
lines: module docstring, 37 function/method/class docstrings, 16 `#`/`#:`
comment blocks) and the whole own test module (`tests/test_schema.py`, 2161
lines: module docstring, 100+ test/helper docstrings, section banners, inline
comments). Required reading in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for this
target and no Routed lead on this item), `docs/review/rev-schema.md`
(skeleton, `Status: reviewing`), then the sibling axis records
(`rev-schema.performance.md`, `rev-schema.mechanics.md`: absent when read,
siblings run concurrently). The target and its test module are dirty vs HEAD
(the truthful-reads migration, `+22/-116` across both) but byte-identical to
ITEM_BASELINE (`git diff 5ef09ed4 -- <both>` empty); every grade below is
against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/schema/comments/inspect/` plus
`docs/review/temp-tests/schema/comments/schema.json`.
`build_tree_md.py --list-docstrings` passes on both graded-whole files
(1 module each, 0 breaking). `check_citations.py --paths <file>
--substrings --json` reports 7 citations, 0 violations in the target and 5
citations, 0 violations in the own test module (full JSON under
`docs/review/temp-tests/schema/comments/cites-*.json`). Provenance sweep
(REVIEW.md pattern, regex mode) hits only `spec-048 Decision 10` (kept),
`round` inside `around` (noise), `now` x2 (scenario/state, R7),
`no longer` x3 (present-tense state rules, kept), `worker` x3 (thread
vocabulary, kept). No `we`/`you`/`I`, no `Tests that`/`Ensures`, no
`.py:NN`, no TODO, no `legacy`/`previously`/`moved from`/`fix for` in
either file. No finding touches a module first line: no TREE.md row moves.

Contract trace, each risky claim against its body and one real caller or
contract source. Upstream wheels fetched from PyPI into
`docs/review/temp-tests/schema/comments/pkgs/` (graphql-core 3.2.9/10/11/12/13
+ 3.3.0, strawberry-graphql 0.318.0/0.319.0, asgiref 3.8.1/3.12.1, plus the
PyPI metadata for Django 5.2.16): the `CollectedErrors` boundary is 3.2.10
not 3.2.9 (M1; 3.2.8/3.2.9 still carry plain `self.errors`, 3.2.10-13 carry
the class, 3.3.0 moved it to `executor.py`); strawberry requires
graphql-core `>=3.2.0,<3.4.0`, so the supported range spans both shapes.
`Schema.stream` lands in 0.319.0 exactly (0 in 0.318.0, 1 in 0.319.0;
`subscribe` subscribes alone below it), corroborated by spec-048 Decision
11 and the `consumers.py::_StopAwareSchema.stream` docstring. asgiref
3.8.1/3.11.1(installed)/3.12.1 carry the three audited attributes and a
textually identical executor-selection block; Django 5.2.16 requires
`asgiref>=3.8.1`, so both ends of the docstring's audited range hold.
Installed-tree reads: strawberry 0.324.0 `get_extensions` resolution
(`ext if isinstance(ext, SchemaExtension) else ext()`, verbatim as quoted),
`self.extensions = tuple(extensions)` in `__init__`, all three
`get_extensions` call sites before the converted `try`, the
`except`-builds-fresh-result + `context.result` assignment after unwind,
`subscribe` as a thin wrapper over `stream`, `allowed_operation_types`
on exactly three entry points (`subscribe` passes a fixed tuple),
`operation_name` as a read-only property over `_provided_operation_name`,
one authorization test per operation (sync/async twins),
`getattr(type(extension), HOOK_NAME)` hook dispatch, `ValidationCache`;
Django `closed_in_transaction` + `Atomic.__exit__` skip-without-raise;
graphql-core `execute_fields_serially`. One workspace probe,
`docs/review/temp-tests/schema/comments/probe_class_member.py`, run
`review-20260929T123513-356cea` (address `review/schema.py/comments`, cell
default): int/object factory products escape `AttributeError` at the
assignment loop, a class product survives it and escapes `TypeError` from
result collection after an `AttributeError` at hook lookup - every shape
escapes every seam, corroborating the `get_extensions` docstring (R12).
Cells: default run for the probe, which opens no database. Sharded and pg
are `inapplicable by construction`: the graded prose reaches no database,
alias, or dialect decision (verifier judges).

Package prose about the target's symbols, every site read whole against
its body: `resource_policy.py` (construction-once, `__post_init__` gate,
precedence, `_SCHEMA_ENFORCEMENT` citation), `error_policy.py` (ditto +
copy-per-read), `utils/write_transaction.py` (module seam paragraph,
`managed_write_transaction` entry order, alias `ContextVar`, refusal
message), `utils/policies.py` (retained-argument duplication),
`utils/private_state.py` (owner vocabulary, box-as-`MethodType` evidence),
`utils/execution_mode.py` (mode carried via `get_extensions`),
`mutations/fields.py` (marker stamping + readback, both true),
`mutations/resolvers.py` (managed-transaction gate comment),
`conf.py` (argument-outranks comments),
`extensions/error_policy.py` (`is_maskable_result` gate,
`mask_execution_result` identity-on-clean + fail-closed containment,
`_is_unexpected` classifier, `_masked` dropping `original_error`,
`DjangoErrorPolicyExtension` install/declaration paragraph),
`extensions/resource_policy.py` (`_policy` property reading the private
record + canonical copy, backref-bridge comment),
`extensions/operation_state.py` (assignment-to-runner directness, marker
semantics, runner-factory override, managed-branch prose),
`extensions/debug.py` ("list after any masking extension", verified
word-for-word; the singleton-in-a-factory usage example),
`extensions/__init__.py` (default-recipe install),
`consumers.py` (`_masked_return` seam citation),
`optimizer/extension.py` (documented singleton-behind-factory). All grade
true; no Routed lead. spec-048 Decision 10 content-verified (error FIRST,
resource LAST, debug-teardown rationale).

Other-test-module prose about the target's symbols, graded in this record:
`tests/mutations/test_write_transaction.py` (module contract paragraph,
every window-behavior docstring, `_CLOSED_WINDOW_MESSAGE` re-type
comment - byte-identical to the package text; M1 twin),
`tests/test_resource_policy.py` (three `_consumer_extension_entries`
docstrings, true), `tests/base/test_init.py` (the two schema-symbol
sentences, true; the `card adds` framing rejected at R10; the 0.0.14
narrative stays homed on Project per the plan),
`tests/extensions/test_operation_state.py` (module bullets, runner-handoff
and marker docstrings, true),
`tests/utils/test_execution_mode.py` (authoritative-spelling row, true),
`tests/test_error_policy.py` (chain-position, factory, return-seam
docstrings, true), `tests/test_ci_governance.py` (once-per-operation
upstream fact, true),
`examples/fakeshop/test_query/test_error_policy_api.py` (factory-masker
refusal, true), `examples/fakeshop/test_query/test_extension_isolation_api.py`
(read whole, 867 lines: M5/M6/M7, remainder true),
`examples/fakeshop/test_query/test_mutation_atomicity.py` (read whole, 493
lines: M8/L4, remainder true). `docs/dry/dry-file-*.md` hits are that
flow's untracked work, deliberately unswept (registry-F10 precedent).

Sibling correlation: none (no sibling record exists yet). The findings
below are prose-only; no Performance/Mechanics disturbance is expected
from any of them.

Looks-for discharge (REVIEW.md "Comments"): whole-target + whole-module
grading - this record; other-test prose - above (8 findings, rest true);
package prose - true throughout, no route; grades - below; module first
lines - both pass; function mood - R1 (standing 9-item rejection);
class mood - L5 (no standing rejection; three items file it); public
symbol w/o docstring - none (`__init__`s rejected at R4); signature
restatement - none; `we`/`you`/`I` - none; `Tests that`/`Ensures` -
none; line-number/dead-name refs - L2/L3; contradicted stated reasons -
M2/M3/M4/M8 (+M1/M5/M6/M7 counts); unrecorded separations - none (the
admitted/refused chain split, the box evidence, the per-read policy
copies are each recorded at the owner).

Fingerprints (`git hash-object`, live) of every file inspected:

- `django_strawberry_framework/schema.py` `84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1`
- `tests/test_schema.py` `3676f7e8a9370966c3159264825857a599cdf085`
- `tests/mutations/test_write_transaction.py` `689e31f47ae0dc010e67386e4a076b782afac5ff`
- `tests/test_resource_policy.py` `a52bfb890c5bc5979c997410ee5d7ab5cd79dfff`
- `tests/base/test_init.py` `239648ed635fa67baa10bf5bd428cd127098088b`
- `tests/extensions/test_operation_state.py` `7509c1ccaa1c56c50be2ca3bc4337b75bcca90ce`
- `tests/utils/test_execution_mode.py` `bbe5f97eac7483fa78c716b942e0aa3951d138de`
- `tests/test_error_policy.py` `9a72cdb83d4739be4018a3c58d0bf2736b63f569`
- `tests/test_ci_governance.py` `cfc66f6e028b3dabdabfdfd13bebd1ada656e3e0`
- `examples/fakeshop/test_query/test_extension_isolation_api.py` `2744212cf0693cc283253aa9e786882304cfdd44`
- `examples/fakeshop/test_query/test_mutation_atomicity.py` `3b94b136cf6a18928c1adb209ce69a93e9db8bb3`
- `examples/fakeshop/test_query/test_error_policy_api.py` `071b113feeaf9cee30ccda5941614c423251459c`
- `django_strawberry_framework/extensions/error_policy.py` `a1defd394d8eda9b698964030a09efe6914278db`
- `django_strawberry_framework/extensions/resource_policy.py` `0134d83a9aa2db580b7b8180ded27a3d31b115c7`
- `django_strawberry_framework/extensions/operation_state.py` `d9ed9cc67fea892afa2dd22a33236a52fc061fb1`
- `django_strawberry_framework/extensions/debug.py` `054e04df5915ed12c49ef63e4710feebca7388aa`
- `django_strawberry_framework/extensions/__init__.py` `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`
- `django_strawberry_framework/resource_policy.py` `5b4a80f0e03674b3ae105a03bb21774b602bfa38`
- `django_strawberry_framework/error_policy.py` `57a0bed1ba730f8e4c1f4c879d852274eac39f12`
- `django_strawberry_framework/utils/private_state.py` `b3c45503c3e2f648640b95ecad4d71a8315abb51`
- `django_strawberry_framework/utils/write_transaction.py` `4a83f43dfd8970ade29f4c89a021ae7adf88645b`
- `django_strawberry_framework/utils/policies.py` `0a2b7dbad96594b5d668774218809c6a94d136be`
- `django_strawberry_framework/utils/truth.py` `d5c96bc8d191d3fce0a20140d8e91063bb466ec9`
- `django_strawberry_framework/utils/execution_mode.py` `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9`
- `django_strawberry_framework/mutations/fields.py` `0e4d5ed1c7efbcbb4e70db9162f2ffc85460a699`
- `django_strawberry_framework/mutations/resolvers.py` `c9cff0590157de85bd9374ab85588b00e62080e0`
- `django_strawberry_framework/conf.py` `3820c575bfd4e3c384244d1bed460b75d3bb7681`
- `django_strawberry_framework/consumers.py` `0791c04a6c7b2619562f33dc707b002cde718c6b`
- `django_strawberry_framework/optimizer/extension.py` `39a8739c7e568e89aff030d98d0ba31d9f04371c`
- `docs/SPECS/spec-048-secure_output_defaults-0_0_14.md` `c1a11bdbd632800103c2f67e0413b4442befeb0e`
- `docs/review/review-0_0_15.md` `648170305d979962d8d43217a27d85b5a582e6c7`
- `docs/review/rev-schema.md` `088e6c8e390de80b667542286e4f9189637e6801`

Installed-tree reads (no git blob): strawberry-graphql 0.324.0
(`schema/schema.py` init/resolution/`get_extensions` sites/`execute`/
`execute_sync`/`stream`/`subscribe`/`_prepare_operation_*`/
`_handle_execution_result`, `types/execution.py`,
`extensions/runner.py`, `extensions/context.py`,
`extensions/validation_cache.py`), graphql-core 3.2.8
(`execution/execute.py`), Django 6.1 (`db/backends/base/base.py`,
`db/transaction.py`), asgiref 3.11.1 (`sync.py`). Fetched wheels under
`docs/review/temp-tests/schema/comments/pkgs/` (graphql-core
3.2.9/3.2.10/3.2.11/3.2.12/3.2.13/3.3.0, strawberry-graphql
0.318.0/0.319.0, asgiref 3.8.1/3.12.1; PyPI metadata for Django 5.2.16).

## Findings

### High

None.

### Medium

#### M1: `_execution_errors` pins the `CollectedErrors` relocation at 3.2.9; it landed in 3.2.10

- Observation: the docstring says "graphql-core < 3.2.9 stores located
  errors directly as ``ExecutionContext.errors`` (a plain list); 3.2.9
  replaced that attribute with a ``CollectedErrors`` container". 3.2.9
  carries no `CollectedErrors` (its `ExecutionContext` still sets plain
  `self.errors`); the class first appears in 3.2.10. The same wrong
  boundary is repeated in the other-test-module twin,
  `tests/mutations/test_write_transaction.py::test_execution_errors_reads_both_graphql_core_error_shapes`
  ("bridges the graphql-core 3.2.9 errors relocation", "< 3.2.9 ...;
  3.2.9 moved it behind"). The code itself is version-agnostic
  (`getattr` fallbacks), so this is prose-only: no behavior changes.
- Evidence: wheels fetched from PyPI into
  `docs/review/temp-tests/schema/comments/pkgs/`, `class CollectedErrors`
  grepped per release - absent in 3.2.8 (installed) and 3.2.9, present
  in 3.2.10/3.2.11/3.2.12/3.2.13 (in `execute.py`) and 3.3.0 (moved to
  `executor.py`). The 3.2.10+ shape matches the docstring's other
  claims (`collected_errors.errors` property over an append-only list).
  Strawberry 0.324.0 requires `graphql-core>=3.2.0,<3.4.0`, so the
  supported range spans both shapes and the boundary matters.
- Impact: a maintainer auditing which releases take which branch (or
  whether the fallback arm is dead) reads the wrong cutoff in both
  places. False version boundary on internal prose, twice over.
- Severity: Medium (stale version boundary; false on its own date, no
  code change owed).
- Recommendation: re-pin both docstrings at 3.2.10; see text-after.
  (Non-binding note: the twin test's `errors=["legacy"]` sentinel
  shares the framing - the plain-list shape is the live shape on
  3.2.0-3.2.9, most of the supported range - but a string literal is
  outside the graded population, so renaming it is optional polish,
  not part of the Proof.)
- Must not change: n/a.
- Proof: `grep -c '3.2.9' django_strawberry_framework/schema.py tests/mutations/test_write_transaction.py` prints `0` on both reported lines (`:2` and `:3` today); both rewritten docstrings grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execution_errors`
  + `tests/mutations/test_write_transaction.py::test_execution_errors_reads_both_graphql_core_error_shapes`.
- Grade: stale.
- Text-before:
  `graphql-core < 3.2.9 stores located errors directly as ``ExecutionContext.errors`` (a plain list); 3.2.9 replaced that attribute with a ``CollectedErrors`` container exposing the same list as ``collected_errors.errors``.` /
  ` ```_execution_errors`` bridges the graphql-core 3.2.9 errors relocation. graphql-core < 3.2.9 exposes the located-error list as ``ExecutionContext.errors``; 3.2.9 moved it behind a ``CollectedErrors`` container at ``collected_errors.errors``.`
- Text-after:
  `graphql-core < 3.2.10 stores located errors directly as ``ExecutionContext.errors`` (a plain list); 3.2.10 replaced that attribute with a ``CollectedErrors`` container exposing the same list as ``collected_errors.errors``.` /
  ` ```_execution_errors`` bridges the graphql-core 3.2.10 errors relocation. graphql-core < 3.2.10 exposes the located-error list as ``ExecutionContext.errors``; 3.2.10 moved it behind a ``CollectedErrors`` container at ``collected_errors.errors``.`

#### M2: `_SCHEMA_ENFORCEMENT` comment counts "two policies and two flags"; the record holds one flag

- Observation: the comment says "two policies and two flags point at
  nothing". `_SchemaEnforcement` today fields two policies and ONE flag
  (`extensions_settled`); the `auto_resource_extension` /
  `auto_error_extension` flags the count was written against are gone
  (0 hits in the live file).
- Evidence: dataclass body at blob `84f2d5aa` (lines 506-508) vs the
  comment; `git show 5b7177e8:...` shows the phrase born beside the
  three-bool record (the two `auto_*` flags plus `extensions_settled`).
  Code moved, comment did not.
- Impact: a reader sizing the "points at nothing" invariant counts a
  second flag that does not exist. Wrong count about the record's own
  shape.
- Severity: Medium (stale count on internal prose).
- Recommendation: recount; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'two policies and two flags' django_strawberry_framework/schema.py` prints `0` (1 today); the rewritten sentence grades true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/schema.py` (`_SCHEMA_ENFORCEMENT` doc-comment).
- Grade: stale (code moved).
- Text-before:
  `Holding it here is what the record's own shape permits: two policies and two flags point at nothing, so this mapping retains a schema's configuration without retaining the schema, and the weak reference filed beside each record drops the entry when its schema dies.`
- Text-after:
  `Holding it here is what the record's own shape permits: two policies and a flag point at nothing, so this mapping retains a schema's configuration without retaining the schema, and the weak reference filed beside each record drops the entry when its schema dies.`

#### M3: refusal-message comment names "the population that was ambiguous"; no such reason survives

- Observation: the `_UNREADABLE_CONFIGURATION` / `_UNRESOLVED_CHAIN`
  comment enumerates the log-only diagnostics as "the object that was
  invalid, the exception a factory raised, and the population that was
  ambiguous". The four live `_refused_chain` reasons are the unreadable
  entries, the raising factory, the non-instance member, and the
  claimed authority - none is a population, and none is ambiguous. The
  phrase matched the removed `_ambiguous_authority` reason set (0 hits
  in the live file).
- Evidence: all four `_refused_chain` call sites read (reasons quoted
  verbatim); `git show 3e5296f6:...` shows the phrase born beside
  `_ambiguous_authority`. Code moved, comment did not.
- Impact: a reader auditing what the wire withholds looks for an
  ambiguity diagnostic that no refusal logs, and misses the live
  fourth diagnostic (the claimed authority). Wrong enumeration of the
  module's own reasons.
- Severity: Medium (stale enumeration on internal prose).
- Recommendation: name the live third diagnostic; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'population that was ambiguous' django_strawberry_framework/schema.py` prints `0` (1 today); the rewritten sentence grades true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/schema.py` (`_UNREADABLE_CONFIGURATION` doc-comment).
- Grade: stale (code moved).
- Text-before:
  `One message per cause and nothing more: the object that was invalid, the exception a factory raised, and the population that was ambiguous are all diagnostics for the deployment's own logs, and a wire field carrying any of them hands a client the shape of a schema's configuration.`
- Text-after:
  `One message per cause and nothing more: the object that was invalid, the exception a factory raised, and the authority a resolved member claimed are all diagnostics for the deployment's own logs, and a wire field carrying any of them hands a client the shape of a schema's configuration.`

#### M4: "one function away" spans 24 definitions

- Observation:
  `tests/test_schema.py::test_a_refused_request_never_asks_a_transport_policy_whether_it_is_empty`
  says "The same posture the accepted-entry reader takes one function
  away". The accepted-entry reader is `_consumer_extension_entries`
  (the no-truthiness normalization comment); it sits 24 `def`/`class`
  lines below `_refuse_operation_document`, not one function away.
- Evidence: live layout at blob `84f2d5aa` (`_refuse_operation_document`
  line 609, `_consumer_extension_entries` line 1301, 24 definitions
  between); the posture match itself (read, never truth-test) is true,
  only the distance is false.
- Impact: a reader looking one function away from either site finds the
  wrong neighbor. False layout claim in a test docstring.
- Severity: Medium (stale layout claim on internal prose).
- Recommendation: name the function instead of the distance; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'one function away' tests/test_schema.py` prints `0` (1 today); the rewritten docstring grades true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_schema.py::test_a_refused_request_never_asks_a_transport_policy_whether_it_is_empty`.
- Grade: stale.
- Text-before:
  `The same posture the accepted-entry reader takes one function away: a container supplied by a consumer is normalized by being read, never by being truth-tested.`
- Text-after:
  `The same posture the accepted-entry reader takes in ```_consumer_extension_entries``: a container supplied by a consumer is normalized by being read, never by being truth-tested.`

#### M5: live isolation module opens "Two claims ... both" over four bullets

- Observation: the module docstring of
  `examples/fakeshop/test_query/test_extension_isolation_api.py` opens
  "Two claims a package-only schema cannot make, both reached from a
  resolver holding ``info.schema`` in a real request and read back off
  the wire" - then lists FOUR bullets (next-request enforcement,
  authority refusal, factory ladder, optimizer nesting), the last of
  which involves no resolver-held `info.schema` at all.
- Evidence: bullet census over lines 1-27 (four `- ` top-level
  bullets); each bullet's subject verified against the tests below
  (widen/unmask tampers, `/iso-chain/` refusals, `/iso-ladder-*/`
  ladder, `/iso-nesting/` consumer-extension operation).
- Impact: the module's own opener miscounts its contents and overstates
  the shared shape ("both ... resolver"). False count governing live
  prose about the target's enforcement/refusal subjects.
- Severity: Medium (stale count on internal prose).
- Recommendation: count four, state the shape all four share; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c -e 'Two claims a package-only schema' -e 'both reached from a resolver' examples/fakeshop/test_query/test_extension_isolation_api.py` prints `0` (1 today; both phrases share line 3); the rewritten opener grades true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_extension_isolation_api.py` module docstring.
- Grade: stale.
- Text-before:
  `Two claims a package-only schema cannot make, both reached from a resolver holding ```info.schema`` in a real request and read back off the wire:`
- Text-after:
  `Four claims a package-only schema cannot make, each reached from a real request and read back off the wire:`

#### M6: live factory ladder claims "Every factory shape" but mounts no error-authority row

- Observation: the `_LADDER_FACTORIES` comment says "Every factory
  shape short of an ordinary extension instance, and the reason the
  package logs for refusing it." The ladder mounts seven shapes whose
  logged reasons are `raised` / `not a SchemaExtension instance` /
  `claims the resource-policy authority` - but `_claimed_authority`
  also returns `error-policy`, and no ladder row logs `claims the
  error-policy authority` (the package tier pins that shape in
  `tests/test_schema.py` via `_SelectingErrorFactory`, but the live
  ladder does not mount it). "Every" overclaims by a whole logged
  reason.
- Evidence: ladder census (7 entries, 3 distinct reasons) vs
  `_claimed_authority` (2 roles) and the live mounts
  (`/iso-ladder-*/`); the error-claim shape verified mountable and
  unmounted.
- Impact: a reader auditing live refusal coverage believes every
  factory shape is pinned over HTTP, while the error-authority
  resolution has no live row. False census on live prose about the
  target's resolution subjects.
- Severity: Medium (stale census on internal prose).
- Recommendation: drop the universal; see text-after (Worker-2 may
  instead mount the missing row, which would make "Every" true - the
  Proof governs the prose either way).
- Must not change: n/a.
- Proof: `grep -c 'Every factory shape short of' examples/fakeshop/test_query/test_extension_isolation_api.py` prints `0` (1 today); the rewritten comment grades true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_extension_isolation_api.py` (`_LADDER_FACTORIES` doc-comment).
- Grade: stale.
- Text-before:
  `Every factory shape short of an ordinary extension instance, and the reason the package logs for refusing it.`
- Text-after:
  `The factory shapes short of an ordinary extension instance that this ladder mounts, and the reason the package logs for refusing each.`

#### M7: live refused-name census claims "Every operationName ... in a request body" but lists strings only

- Observation: the live `_REFUSED_OPERATION_NAMES` comment says "Every
  ``operationName`` a client can put in a request body, including the
  ones no document can carry." The dict holds four STRING categories
  (empty, invalid punctuation, unicode, valid-but-absent); a JSON body
  can also carry `null` and non-string values, which the package-tier
  twin (`tests/test_schema.py`, six names incl. `None` and `0`)
  covers and this census omits. The view does no `operationName`
  coercion (`views.py` carries no `operation_name` handling), so the
  omitted shapes reach the schema.
- Evidence: live census (4 string categories) vs package-tier census
  (6 incl. non-strings) vs JSON-body value space; `views.py` grep for
  `operation_name` empty.
- Impact: same as M6 - "Every" promises an exhaustive live census with
  identifiable missing members. False census on live prose about the
  target's refusal subjects.
- Severity: Medium (stale census on internal prose).
- Recommendation: qualify to the string space the census covers; see
  text-after (the non-string shapes ride the package-tier rows).
- Must not change: n/a.
- Proof: `grep -c 'operationName`` a client can put in a request body' examples/fakeshop/test_query/test_extension_isolation_api.py` prints `0` (1 today); the rewritten comment grades true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_extension_isolation_api.py` (`_REFUSED_OPERATION_NAMES` doc-comment).
- Grade: stale.
- Text-before:
  `Every ```operationName`` a client can put in a request body, including the ones no document can carry.`
- Text-after:
  `Every string ```operationName`` a client can put in a request body, including the ones no document can carry.`

#### M8: live atomicity module says graphql-core "historically committed" the transaction

- Observation: the module docstring of
  `examples/fakeshop/test_query/test_mutation_atomicity.py` says "a
  ``DjangoMutation`` runs its write inside a transaction that
  graphql-core historically committed when the resolver returned".
  graphql-core commits no database transaction; the old pipeline's
  `atomic` exit stood committed at resolver-return. The owner states
  it precisely ("historically after that transaction had already
  committed", agentless passive); the live twin misattributes the
  commit to graphql-core. The same paragraph carries release/card
  provenance ("shipped at 0.0.14 (commit 1b06c39e; tracked pre-renumber
  as card BETA-055)") and a "now holds" framing.
- Evidence: paragraph read against the target module docstring (the
  owner, lines 3-9 at blob `84f2d5aa`) and the pipeline's atomic
  mechanics; no spec, card, or glossary anchor survives for the
  parenthetical to cite (BETA-055 absent from KANBAN.md, no window
  anchor in GLOSSARY.md).
- Impact: a reader learns the wrong agent for the old commit timing on
  live prose about the target's core subject, plus unresolvable
  release archaeology. Wrong stated mechanism with provenance riders.
- Severity: Medium (wrong stated mechanism; the provenance tokens ride
  the same rewrite).
- Recommendation: correct the agency (agentless, as the owner), drop
  the archaeology and the "now"; see text-after. "Used to" is kept:
  regression motivation with true claims (error_policy-R6/conf-R2
  precedent).
- Must not change: n/a.
- Proof: `grep -c -e 'graphql-core historically committed' -e 'tracked pre-renumber as card' -e 'execution context now' examples/fakeshop/test_query/test_mutation_atomicity.py` prints `0` (3 today, lines 4/5/8); the rewritten paragraph grades true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_mutation_atomicity.py` module docstring.
- Grade: stale.
- Text-before:
  `Pins the mutation-atomicity contract shipped at 0.0.14 (commit 1b06c39e; tracked pre-renumber as card BETA-055): a ```DjangoMutation`` runs its write inside a transaction that graphql-core historically committed when the resolver returned - BEFORE the returned payload was *completed* (serialized) - so a completion failure left the write committed while the client saw ```data: null`` + a top-level error. ```DjangoSchema``'s execution context now holds each generated top-level mutation field's transaction open THROUGH value completion and rolls it back when completion adds an error.`
- Text-after:
  `Pins the mutation-atomicity contract: a ```DjangoMutation`` runs its write inside a transaction that used to stand committed once the resolver returned - BEFORE the returned payload was *completed* (serialized) - so a completion failure left the write committed while the client saw ```data: null`` + a top-level error. ```DjangoSchema``'s execution context holds each generated top-level mutation field's transaction open THROUGH value completion and rolls it back when completion adds an error.`

### Low

#### L1: module docstring opens "The 0.0.14 mutation-atomicity commit-gap fix"

- Observation: the second sentence of the module docstring dates the
  module to its release ("The 0.0.14 ... fix"). The version token is
  process provenance: it states when the module shipped, nothing about
  what it does. (Twin site with the same true-but-dated shape:
  `django_strawberry_framework/utils/write_transaction.py:3` "The
  0.0.14 mutation write-hardening seam" - true, for that item's own
  pass; no route, since routing requires staleness.)
- Evidence: sentence read whole; the remainder of the docstring states
  the present-tense rule the version decorates. Distinct from the
  `Spec:`/`Target release:` metadata convention (connection-R2), which
  this narrative sentence is not.
- Impact: release archaeology heading the module every consumer of the
  mutation surface reads. Bounded provenance strip.
- Severity: Low (process provenance; correct release, history prose).
- Recommendation: drop the version token; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'The 0.0.14 mutation-atomicity commit-gap fix' django_strawberry_framework/schema.py` prints `0` (1 today); the rewritten sentence grades true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/schema.py` module docstring.
- Grade: process provenance.
- Text-before:
  `The 0.0.14 mutation-atomicity commit-gap fix.`
- Text-after:
  `The mutation-atomicity commit-gap fix.`

#### L2: `(spec plan "Implementation Changes")` cites a section that exists nowhere

- Observation: the module docstring heads the execution-mode split
  with `(spec plan "Implementation Changes")`. No spec number is
  named, and no `Implementation Changes` section exists in any
  standing doc (searched `docs/`, KANBAN.md: only DRY-flow temp copies
  of this same file match). The pointer was born in 1b06c39e beside a
  card (`BETA-055`), not a spec, and the card number did not survive
  renumbering. It is neither a kept spec-Decision pointer nor a bare
  tag - an unresolvable citation.
- Evidence: repo-wide grep for the section title (0 standing hits);
  KANBAN.md grep for `BETA-055` (0 hits); GLOSSARY.md grep for a
  window anchor (0 hits). Both bullets it heads are self-contained
  and verified true, so deletion loses nothing.
- Impact: a reader chasing the pointer finds no plan. Dangling
  citation on a public module's docstring.
- Severity: Low (unresolvable reference; no false behavior claim).
- Recommendation: delete the parenthetical; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'spec plan "Implementation Changes"' django_strawberry_framework/schema.py` prints `0` (1 today); the reworded heading grades true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/schema.py` module docstring.
- Grade: stale (dangling reference).
- Text-before:
  `Execution-mode split (spec plan "Implementation Changes"):`
- Text-after:
  `Execution-mode split:`

#### L3: dead test-name reference `test_a_slotted_callable_factory_is_accepted_and_enforces`

- Observation:
  `tests/test_schema.py::test_an_extension_entry_strawberry_could_not_resolve_is_refused`
  ends "see
  ``test_a_slotted_callable_factory_is_accepted_and_enforces``". No
  test by that name exists; the layout rule it means lives in
  `tests/test_schema.py::test_a_slotted_callable_factory_is_accepted_and_runs`.
  The reference is a bare backticked name (not `path::Symbol`), so the
  citation gate never saw it rot.
- Evidence: repo-wide grep for `accepted_and_enforces` (exactly the
  one reference); the `..._and_runs` definition at line 1050;
  `git log -S` shows the `and_enforces` spelling predating the
  rename. Test renamed, reference did not follow.
- Impact: a reader chasing the memory-layout rule lands nowhere.
  Dangling reference in a test docstring.
- Severity: Low (dangling reference; no false behavior claim).
- Recommendation: repoint at the live name; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'accepted_and_enforces' tests/test_schema.py` prints `0` (1 today); the rewritten docstring grades true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_schema.py::test_an_extension_entry_strawberry_could_not_resolve_is_refused`.
- Grade: stale (dangling reference).
- Text-before:
  ` ```test_a_slotted_callable_factory_is_accepted_and_enforces``.`
- Text-after:
  ` ```test_a_slotted_callable_factory_is_accepted_and_runs``.`

#### L4: live atomicity module carries the xfail-to-XPASS biography

- Observation: the module docstring of
  `examples/fakeshop/test_query/test_mutation_atomicity.py` narrates
  "These began life as ``xfail(strict=True)`` regressions; the 0.0.14
  mutation-atomicity work landed, they XPASSed, and the markers were
  removed". Pure change-process biography: how the tests came to be,
  not what they pin.
- Evidence: paragraph read whole; the present-tense contract it
  decorates ("the assertions encode the shipped contract (...)")
  stands alone.
- Impact: release-process narrative heading live prose about the
  target's core subject. Bounded provenance strip.
- Severity: Low (process provenance).
- Recommendation: delete the biography, keep the contract sentence;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'began life as' examples/fakeshop/test_query/test_mutation_atomicity.py` prints `0` (1 today); the rewritten paragraph grades true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_mutation_atomicity.py` module docstring.
- Grade: process provenance.
- Text-before:
  `These began life as ```xfail(strict=True)`` regressions; the 0.0.14 mutation-atomicity work landed, they XPASSed, and the markers were removed - the assertions encode the shipped contract (no 500, the completion error is surfaced, the write rolled back).`
- Text-after:
  `The assertions encode the shipped contract (no 500, the completion error is surfaced, the write rolled back).`

#### L5: two class docstrings open imperative ("Hold ...", "Refuse ...")

- Observation: two target class docstrings open imperative where the
  axis requires a description for a class (ruff leaves mood unchecked,
  so this review is the gate):
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext`
  ("Hold each generated mutation field's transaction open through
  value completion.") and
  `django_strawberry_framework/schema.py::_RefusedConfiguration`
  ("Refuse every operation on a schema that cannot produce its
  accepted chain."). No standing rejection covers class mood (the
  R1 consensus is functions-only); three items file it (consumers
  implemented, apps + routers stand deferred).
- Evidence: first lines read in place; every other class first line
  in both graded files is descriptive.
- Impact: minor mood inconsistency on two public-adjacent classes.
- Severity: Low.
- Recommendation: recast both first lines as descriptions; see
  text-after list.
- Must not change: n/a.
- Proof: `grep -c -e '"""Hold each generated mutation' -e '"""Refuse every operation on a schema that cannot produce' django_strawberry_framework/schema.py` prints `0` (2 today; each anchor verified to match exactly its site); both rewritten first lines grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/schema.py::DjangoMutationExecutionContext`,
  `django_strawberry_framework/schema.py::_RefusedConfiguration`.
- Grade: duplicates the code (mood defect; imperative first line on a
  class, which the rule requires as a description).
- Text-before / text-after, per site in Symbol order:
  `Hold each generated mutation field's transaction open through value completion.` /
  `The execution context that holds each generated mutation field's transaction open through value completion.`
  `Refuse every operation on a schema that cannot produce its accepted chain.` /
  `An extension refusing every operation on a schema that cannot produce its accepted chain.`

## Rejected

- R1 - Non-imperative first lines on functions and methods (target 10:
  `_enforcement`, `_RefusedConfiguration._refusal`, `_refused_chain`,
  `_operation_mode`, `_is_resolvable_extension_entry`,
  `_is_extension`, `_admitted_chain`, `_declared_authority`,
  `_entry_resource_policy`, `_entry_type`; own-test helpers 14:
  `_rollback_probe_row_exists`, `_assert_entry_survives_a_replacement_attempt`,
  `_reachability_after_dropping`, `_schema_holding_an_unnamed_entry`,
  `_widening_factory`, `_closure_resource_factory`,
  `_narrow_resource_factory`, `_wide_resource_factory`,
  `_first_error_factory`, `_singleton_error_factory`,
  `_fresh_marker_factory`, `_singleton_marker_factory`,
  `_optimizer_singleton_factory`, `_assert_configuration_refusal`).
  Rejected as style preference per the standing 9-item consensus
  (connection-R1, relay-R12, list_field-R6, resource_policy-R8,
  error_policy-R5, exceptions-R1, keyset-R1, conf-R1, scalars-R1):
  package and family conventions (66 `Whether`-opening predicates,
  `The`-opening return-contract readers, factory describers) beat the
  imperative rule, and rewriting these sites would make both files
  inconsistent with the package. Trigger: a maintainer decision
  enforcing mood package-wide (the routers 19-site batch stands
  deferred under the same trigger).
- R2 - Nine undocumented test functions in the own test module (the
  init shapes, entry-matches adversarial, marked-class safety,
  errors-fallback, policy-resolution, both exception-rollbacks,
  get-extensions sync/async rows). Rejected: names state the expected
  behavior; no looks-for entry requires test docstrings
  (error_policy-R4 precedent). Trigger: none in this flow.
- R3 - Undocumented test-local scaffolding (the `DummyQuery` /
  `_RowQuery` / `DummyMutation` shells and their fields, dunder
  methods, `_SKIP_WITHOUT_STREAM` consumers). Rejected: single-use
  doubles and self-evident one-liners whose contracts live in the
  docstrings that use them (routers precedent). Trigger: any of them
  becoming importable or asserted on directly.
- R4 - `__init__` dunders carrying no docstring (target:
  `_MutationWindowThread`, `_RefusedConfiguration`, `DjangoSchema`;
  tests: `_FactorySchema`, `_OneShotPolicy`, `_HostileBoolPolicy`,
  `_Nester`). Rejected: repo convention documents dunder inits on the
  class; every parameter-bearing one is covered there (routers
  precedent). Trigger: a parameter gaining behavior the class
  docstring does not state.
- R5 - Property first lines left nominal (`extensions`,
  `resource_policy`, `error_policy`). Rejected: a property documents
  its value like an attribute, so description mood is appropriate
  (routers precedent). Trigger: the project adopting
  imperative-property convention.
- R6 - Test-function first lines stating behavior descriptively
  ("The control: ...", "Two declarations of one ceiling ...").
  Rejected: test functions are unaffected by the mood rule; their rule
  is behavior statements, and all state behavior (routers precedent).
  Trigger: none.
- R7 - `now` as present-tense state (`_MarkerExtension` "now that
  neither enforcement authority is an entry"; extensions property
  "whatever the attribute holding them carries now") and `no longer`
  as a present-tense rule (three accepted-entry staleness wordings).
  Kept: present-tense state descriptions naming no process artifact
  (error_policy-R8 precedent). Trigger: none.
- R8 - "Used to" regression motivation with true behavioral claims
  (`test_a_retained_policy_argument_is_not_the_one_the_schema_enforces`
  "used to pass through configuration intake unchanged";
  `test_an_exact_policy_corrupted_before_intake_is_rejected_at_construction`
  "made the type the evidence and the fields an assumption"). Kept:
  the threat model (retained-argument aliasing, post-validation
  corruption) is live and true; same accepted shape as prior
  `Pre-fix`/`The old ...` records (error_policy-R6, conf-R2
  precedents). Trigger: the design changing under either.
- R9 - "Still" as synchronic contrast (`DjangoSchema` "Supplying
  ... still works"; `_ConsumerExtension` "the thing an entry is still
  allowed to be"). Kept: contrasts accepted vs refused spellings, not
  past vs present; names no process artifact. Trigger: none.
- R10 - `tests/base/test_init.py` "card adds" / "spec-NNN adds"
  framing around the two schema-symbol sentences. Rejected: the
  behavioral claims (REQUIRED class, holds-each-transaction-open,
  subclassing seam) are true, and the attribution verbs are the
  block's own uniform convention across every export group -
  rewriting two lines would make them inconsistent with their
  siblings (error_policy-R5 family precedent). The 0.0.14 narrative
  tail stays homed on Project per the plan. Trigger: the convention
  retired, or the Project item rewording the block.
- R11 - "The refusal names the consumer factory's exception by its
  real class and its own ``repr``" (target inline comment). Kept:
  loose but not false (routers precedent) - the refusal construction
  names it in the logged `reason`, and the wire/message split is
  stated precisely beside it (`_refused_chain` "It never reaches
  ``message``") and in the pinning test. `truth.describe` verified
  (`kind` = real class, `render` = own `__repr__`). Trigger: the
  reason reaching the wire message.
- R12 - `get_extensions` "an integer, a bare object or a class
  produces an ``AttributeError`` ... outside every seam". Kept: every
  load-bearing clause corroborated by workspace probe
  `review-20260929T123513-356cea` (int/object escape `AttributeError`
  at the assignment loop; a class survives it and escapes `TypeError`
  from result collection after an `AttributeError` at hook lookup -
  all three shapes escape every masking/refusal seam, which is what
  the sentence exists to establish). Trigger: an upstream release
  converting any of the three shapes into a returned result.
- R13 - "The sealed holder" (`test_a_slotted_entry_does_not_root_...`)
  and "What owns a record is therefore the schema itself"
  (`test_a_schema_stays_collectable_...`). Kept: "sealed" accurately
  describes the unrewritable `MethodType` box, and "owns a record" is
  `utils/private_state.py`'s own owner vocabulary (the weak-ref-to-
  owner edge both sentences rest on verified in `PrivateAuthority` /
  `PrivateMembership`). Trigger: the private-state mechanics changing
  under either.
- R14 - Version-dated twins in other modules, all true:
  `utils/write_transaction.py:3` "The 0.0.14 mutation write-hardening
  seam", `mutations/fields.py` "(mutation atomicity, shipped 0.0.14)"
  x2, `mutations/resolvers.py` "(mutation atomicity, shipped 0.0.14)".
  Read whole with their claims (all true of the live bodies); no
  route, since routing requires staleness and each module's own
  Comments pass grades its own file whole. Trigger: any of the four
  claims going false.

## Routed leads

None. Every package module's prose about the target's symbols grades
true (see Trace); the version-dated twins sit under R14, not here.

Handoff: Comments review is closed at findings-recorded (8 Medium, 5
Low, 14 rejections, no cross-axis findings, no routed leads). Nothing
was bound, run, or edited beyond this record and the scratch below:
the verdict rests on shared-tree reads and greps, PyPI-wheel
diffs, and one workspace probe (review-20260929T123513-356cea). Two
observations carried, neither a defect: (a) the M1 boundary fix
touches a docstring in `tests/mutations/test_write_transaction.py`,
which its owning mutations item grades whole - if that item is
mid-pass when Worker-2 lands this one, the two-line hunk is this
item's, attributed here; (b) the M5/M6/M7/M8/L4 fixes touch two live
test modules shared with every folder item - same attribution note.
The class-mood batch (L5) follows the file-it precedent (consumers,
apps, routers) against the function-mood rejection consensus (R1);
if Worker-0 unifies the two, L5 rides the same package-wide trigger.
Rejections R1-R14 were proven where stated and need no re-proof
absent a body change at their sites.

## Verify comments

Pass 1, fully static (no workspace copy bound; shared-tree greps and
reads only). Item diff `git diff 5ef09ed4 -- <6 paths>` matches
`docs/review/temp-tests/schema/diff/pass-1.diff` hunk for hunk; live
fingerprints: `schema.py` f4e807e9, `tests/test_schema.py` 83877a6a,
`tests/extensions/test_operation_state.py` 6ce414b6,
`tests/mutations/test_write_transaction.py` 96416deb,
`test_extension_isolation_api.py` 61d57bab,
`test_mutation_atomicity.py` 69d7cc4d. Every Proof below ran live;
outputs saved under `docs/review/temp-tests/schema/verify-comments-1/`
(`proofs.log`, `landed.log`, `citations.log`, `sweeps.log`,
`added.log`, `diff/`). Each grade covers the whole docstring the
changed line sits in.

Mech C1 (3.2.10 re-pin): pass. `grep -n "3\.2\.9"
django_strawberry_framework/schema.py
tests/mutations/test_write_transaction.py` exits 1 (no matches).
Both docstrings read 3.2.10 and grade true: `class CollectedErrors`
re-grepped absent in the fetched 3.2.9 wheel (`gql329/.../execute.py`,
count 0) and present in 3.2.10 (count 1).

Mech C2 (override-set restatement): pass. `grep -n "one override
covers every streamed operation"
django_strawberry_framework/schema.py` exits 1. Graded against the F1
disposition recorded in `## Implementation (Worker-2)` (fixed: bind
the floor seam): the landed `_stream` sentence ("both come through
here at 0.319 and above ... below that subscriptions run through
`_subscribe` instead ... Two overrides, each firing where its
upstream exists and dead where it does not") matches the wheel map
(0.316-0.318 `_subscribe`-only; 0.319+ `_stream`-only) and both
bodies (identical `resumed_stream`-iff-`DjangoExtensionsRunner`
shape), so it grades true on every supported band.

M1: pass. `grep -c '3.2.9'` prints 0 on both files (exit 1).
Both rewritten docstrings grade true (same wheel evidence as C1).

M2: pass. `grep -c 'two policies and two flags'` prints 0 (exit 1).
"Two policies and a flag" grades true: `_SchemaEnforcement` fields
exactly `resource_policy`, `error_policy`, `extensions_settled`, and
`auto_*` counts 0 in the live file.

M3: pass. `grep -c 'population that was ambiguous'` prints 0
(exit 1). The rewritten enumeration grades true against the four live
`_refused_chain` reasons (unreadable entries, raising factory,
non-instance member, claimed authority); `_ambiguous_authority`
counts 0 in the live file.

M4: pass. `grep -c 'one function away' tests/test_schema.py` prints
0 (exit 1). The named function `_consumer_extension_entries` exists
(`schema.py:1330`) and the posture match (read, never truth-test)
stands; the false distance is gone.

M5: pass. `grep -c -e 'Two claims a package-only schema' -e 'both
reached from a resolver'` prints 0 (exit 1). "Four claims ... each
reached from a real request and read back off the wire" grades true:
four top-level bullets, each verified against the tests below.

M6: pass. `grep -c 'Every factory shape short of'` prints 0
(exit 1). "The factory shapes ... that this ladder mounts" grades
true: 7 entries, 3 distinct logged reasons, no error-authority row
(prose-reword choice; no live row mounted, as disclosed).

M7: pass. The record's Proof pattern (`operationName`` a client can
put in a request body`) prints 1 - it matches the text-after's own
tail, so it is non-discriminating (1 both before and after), a
record-Proofer defect, not an implement defect. The discriminating
pattern `Every ``operationName`` a client` prints 0 (exit 1), and the
landed sentence is verbatim the text-after modulo wrap ("Every string
``operationName`` ..."). It grades true: the dict holds exactly four
string categories (empty, invalid-punctuation, unicode,
valid-but-absent); non-string shapes ride the package-tier rows.

M8: pass. `grep -c -e 'graphql-core historically committed' -e
'tracked pre-renumber as card' -e 'execution context now'` prints 0
(exit 1). Agency fixed ("used to stand committed"), archaeology and
"now" dropped, kept "Used to" per the recommendation; true.

L1: pass. `grep -c 'The 0.0.14 mutation-atomicity commit-gap fix'`
prints 0 (exit 1). Version token dropped, rule sentence intact; true.

L2: pass. `grep -c 'spec plan "Implementation Changes"'` prints 0
(exit 1). Dangling parenthetical deleted, heading true.

L3: pass. `grep -c 'accepted_and_enforces' tests/test_schema.py`
prints 0 (exit 1). Repointed at
`test_a_slotted_callable_factory_is_accepted_and_runs`, defined at
`tests/test_schema.py:1053`; true.

L4: pass. `grep -c 'began life as'` prints 0 (exit 1). Biography
deleted, contract sentence kept verbatim; true.

L5: pass (disclosed adaptation accepted). Both record anchors print
0 (exit 1). The record's one-liner as a single docstring line
measures 114 chars (sentence 107 + `    """`), exceeding the E501 110
grace - the implement's "117" is off by 3 but the conclusion holds,
so the split was required, not optional. Landed site 1 keeps the
record's sentence verbatim as the description behind the descriptive
summary "Generated-mutation execution context." (D205 blank line,
D415 period, both present); site 2 lands the record's description
verbatim (96 chars). Both first lines are now descriptive; the mood
defect is fixed in substance.

New `_subscribe` docstring: true. Imperative first line; "below
0.319 ... through upstream `_subscribe` rather than `_stream`"
matches the wheel map; the wrapper-reason sentence mirrors `_stream`'s
corroborated claim; "passed through untouched, exactly as there"
matches the body (`return source` on a foreign runner).

New test docstring
(`test_a_subscribe_whose_runner_is_not_the_packages_is_handed_back_untouched`):
true. Behavior statement, no "Tests that"; the `_stream` row sits
immediately above; the 0.319 seam split, the wrap/identity pair, and
the "called directly with a stubbed upstream"
(`patch.object(..., create=True)`, itself evidencing ceiling absence)
all match the body.

F1 code disturbs no graded claim: `_stream`'s body is byte-identical
apart from its restated docstring; no surviving "one override" /
sole / only-`_stream` claim in any touched file (grep exit 1); the 11
un-skips remove decorators only (the item prose diff shows 0 prose
lines for `test_operation_state.py`, `[code changed too]` only at
`_stream` and the new test); the `test_schema.py` import hunk carries
no prose.

Gates: `check_citations.py --paths <6 files> --substrings` exits 0
("OK: 16 citations resolve, 0 violations"); provenance sweep over all
97 added lines hits only "around" (substring noise); no we/you/I,
no "Tests that"/"Ensures", no `.py:NN` refs in added lines; module
first lines untouched in all 6 files (no TREE.md move owed) and
`build_tree_md.py --list-docstrings` reports ok on all five
docstring-touched files.

Status: verified. Open threads: none. Notes (not defects): (1) the M7
record Proof pattern is non-discriminating as written; future
Proofs should anchor the word the fix adds or removes ("Every ``"
vs "Every string ``"). (2) The L5 one-liner measures 114 chars, not
the 117 stated in `## Implementation (Worker-2)`; the E501
conclusion is unaffected.
