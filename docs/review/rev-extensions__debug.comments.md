# Review · Comments: `django_strawberry_framework/extensions/debug.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=2dae90d03c0749ebc2f4a512dd7668b1706b51bc

## Trace

Read the whole live target (863 lines: 32 docstrings, 10 comment sites) and its
own test module `tests/extensions/test_debug.py` whole (1679 lines). Main
artifact `docs/review/rev-extensions__debug.md` read; no sibling axis records
existed at pass time. Target and own test module are dirty with concurrent work;
every grade below is against the live bytes fingerprinted here.

Other test prose about the target's symbols, read whole or as noted:
`examples/fakeshop/test_query/test_debug_extension_api.py` (whole, 752 lines),
`tests/test_ci_governance.py` (forbidden-form classifier excerpts),
`tests/extensions/test_operation_state.py` (constructor-refusal excerpt),
`tests/test_error_policy.py` (debug-factory excerpt),
`examples/fakeshop/test_query/test_multi_db.py` (debug-schema fixture),
`tests/extensions/__init__.py` (whole). Package prose about the target:
`django_strawberry_framework/extensions/__init__.py` (whole),
`django_strawberry_framework/extensions/error_policy.py` (mask-seam excerpt),
`django_strawberry_framework/schema.py::_admitted_chain` (excerpt),
`django_strawberry_framework/consumers.py` (stream-seam excerpts),
`django_strawberry_framework/utils/private_state.py` (whole),
`django_strawberry_framework/utils/typing.py` (peel excerpts),
`django_strawberry_framework/__init__.py` + `error_policy.py` (excerpts).
One real caller per graded symbol (re-export, schema chain, error-policy seam,
consumers stream seam, both test tiers, governance sweep).

Instruments (shared tree, static): `review_inspect.py` (orientation only;
`docs/review/temp-tests/extensions-debug/comments/inspect/` +
`debug.json`); `build_tree_md.py --list-docstrings` on target and own tests:
both `ok`; `check_citations.py --paths <target|tests> --substrings --json`:
1 citation each, both resolve; provenance searches for
spec/card/round/worker/legacy/no-longer/previously/now/fix-for vocabulary.
Corroborated externally: graphene `tracking.py` (`is_slow: duration > 10`,
seconds; `is_select` verbatim shape), installed Django 6.1
(`queries_limit = 9000`, `deque(maxlen=...)`), pyproject floor
`strawberry-graphql>=0.316.0`, fakeshop has no `config/asgi.py` (plus the
test-tier README "No WebSocket mount" row), spec-044 Decision 9 / rule-of-three
passage, `git log -S` peel archaeology (2 typing peels + this walk at
spec-044 slice 1; 4 typing peels + this walk at HEAD).

No workspace run: every Proof is a static `grep -c` plus the grade the
rewritten text must earn. No database opened; cells are n/a for this pass.

Looks-for discharges (`none` with reason): public symbol without a docstring -
none (`__all__` carries one member, documented; the undocumented
`_CursorCaptureCoordinator.__init__` is private); docstring restating the
signature - none; "we"/"you"/"I" - none in target or own tests (grep 0);
test docstring beginning "Tests that"/"Ensures" - none (grep 0; every test
docstring states behavior); line-number source reference - none (grep 0);
unrecorded intentional separation - none (the typing-ceiling separation and
the narrow-peel specializations are recorded at their owners).

Fingerprints (`git hash-object`, live bytes at read time):
`django_strawberry_framework/extensions/debug.py`
054e04df5915ed12c49ef63e4710feebca7388aa (dirty);
`tests/extensions/test_debug.py`
93843bd3deae18c0dce234990ce14d3594a85000 (dirty);
`examples/fakeshop/test_query/test_debug_extension_api.py`
8417985a690906b8b49d4a002cc9515322c5a57e;
`tests/test_ci_governance.py`
cfc66f6e028b3dabdabfdfd13bebd1ada656e3e0;
`tests/extensions/test_operation_state.py`
6ce414b6d74b8988aeb3b1d74e7cb49913e52585;
`tests/test_error_policy.py`
9a72cdb83d4739be4018a3c58d0bf2736b63f569;
`examples/fakeshop/test_query/test_multi_db.py`
893956aa9eb6cd52446bf6388f506c5663313a14;
`tests/extensions/__init__.py`
6adda9e8b860ace03c375a162fb0c320010141c8;
`django_strawberry_framework/extensions/__init__.py`
dc3ebdc24b4817a64ea360d92bbbed340ad30bcc;
`django_strawberry_framework/extensions/error_policy.py`
a1defd394d8eda9b698964030a09efe6914278db;
`django_strawberry_framework/schema.py`
f4e807e9e64c1a38e03942705299f5636ba2dd35;
`django_strawberry_framework/consumers.py`
0791c04a6c7b2619562f33dc707b002cde718c6b;
`django_strawberry_framework/utils/private_state.py`
b3c45503c3e2f648640b95ecad4d71a8315abb51;
`django_strawberry_framework/utils/typing.py`
a672cd6b4f5cf6c207bd4f65ecad4d71a8315abb98;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1bc335a;
`django_strawberry_framework/error_policy.py`
57a0bed1ba730f8e4c1f4c879d852274eac39f12;
`docs/SPECS/spec-044-debug_extension-0_0_14.md`
702afffcaf5c9e13dd27f75ccd7d0178fcbbf1d5.

## Findings

### High

None.

### Medium

#### F1 - module no-key sentence states read timing as the reason (wrong reason)

- **Observation** - `django_strawberry_framework/extensions/debug.py` module
  docstring (:36-38): "the engine reads extension results before this hook's
  teardown on those paths" is presented as why parse/validation failures carry
  no `debug` key. The enforcing mechanism is the result-shape guard in
  `django_strawberry_framework/extensions/debug.py::_stash_payload_if_executed`
  (publish only for a graphql-core `ExecutionResult`; sync leaves `result`
  `None`, async assigns `PreExecutionError`): the engine's recovery path calls
  `get_results` a SECOND time after teardown, which timing alone would publish
  on. A maintainer trusting this sentence would deem the guard redundant.
- **Evidence** - `_stash_payload_if_executed` body (`isinstance(result,
  GraphQLExecutionResult)`); its docstring; the class lifecycle paragraph;
  `tests/extensions/test_debug.py::test_validation_failure_with_raising_teardown_calls_get_results_twice`
  (both calls `{}`).
- **Impact** - wrong stated reason for a true contract; invites deleting the
  load-bearing guard.
- **Severity** - Medium: the contract (no key) is true, only the reason is
  wrong; the true mechanism is stated in the same file.
- **Recommendation** - replace the timing clause with the guard:
- **Must not change** - n/a.
- **Proof** - `grep -c "engine reads extension results before this hook" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten sentence grades true against `_stash_payload_if_executed`. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: module docstring; grade: stale (wrong reason); text before: "Parse
  and validation failures carry **no** ``debug`` key: nothing executed, and
  the engine reads extension results before this hook's teardown on those
  paths."; text after: "Parse and validation failures carry **no** ``debug``
  key: nothing executed, and the stash writer publishes only for a graphql-core
  ``ExecutionResult`` (sync leaves ``result`` as ``None``; async assigns a
  strawberry ``PreExecutionError``)."

#### F2 - module masking-order bullet unscoped against the streaming seam

- **Observation** - module docstring (:85-89): "Listed before it,
  ``exceptions`` reads ``[]``." holds only on the non-streaming paths. On the
  streaming seam the engine reads extension results inside the still-open
  operation context, before any `on_operation` teardown, so
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.on_execute`'s
  stash is pre-masking whatever the list order - the class docstring's own
  streaming paragraph says streaming transports "receive the pre-masking
  payload the executing hook saw". The module bullet omits the carve-out the
  class paragraph carries.
- **Evidence** - class docstring streaming paragraph (:651-664) vs module
  bullet; `on_execute` docstring; streaming tests in own test module.
- **Impact** - a deployment serving WebSocket that lists debug first is told
  `exceptions` reads `[]`; it does not on that transport.
- **Severity** - Medium: wrong for one reachable transport; consequence is
  mild (dev-only diagnostic; WS frame errors are masked per-frame regardless).
- **Recommendation** - scope the bullet to the non-streaming paths and point at
  the streaming carve-out:
- **Must not change** - n/a.
- **Proof** - `grep -c "whatever the order" django_strawberry_framework/extensions/debug.py` prints 1 (0 today); the rewritten bullet grades true against the class streaming paragraph. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: module docstring; grade: stale (unscoped rule); text before:
  "Listed before it, ``exceptions`` reads ``[]``."; text after: "Listed before
  it, ``exceptions`` reads ``[]`` on the non-streaming paths; the streaming
  seam carries the pre-masking payload whatever the order (see the class
  docstring)."

#### F3 - caps comment claims a character ceiling is a byte ceiling (backwards)

- **Observation** - `django_strawberry_framework/extensions/debug.py` payload-caps
  comment (:136-138): "one character is at least one byte, so a character
  ceiling is a byte ceiling". The inference is backwards: bytes >= chars in
  UTF-8/JSON means chars <= N does NOT imply bytes <= N (multi-byte
  characters and JSON escaping expand past the character count). The next
  paragraph contradicts it, correctly disclaiming a ceiling "on the encoded
  payload's own size".
- **Evidence** - comment text vs `_row_cost` (`len()` of pre-encoding Python
  strings); the following paragraph's own disclaimer.
- **Impact** - states a false byte-size guarantee a reader could rely on for
  response budgeting.
- **Severity** - Medium: wrong stated reason in an internal comment.
- **Recommendation** - restate as encoder-independence plus the honest
  non-ceiling:
- **Must not change** - n/a.
- **Proof** - `grep -c "so a character ceiling is a byte" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten paragraph grades true and agrees with the following paragraph. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `_MAX_PAYLOAD_TEXT_CHARS` comment; grade: stale (wrong reason);
  text before: "Every limit counts CHARACTERS - the payload is JSON-encoded
  downstream, where one character is at least one byte, so a character ceiling
  is a byte ceiling that does not depend on the encoder."; text after: "Every
  limit counts CHARACTERS of the pre-encoding text, so the budget does not move
  with encoder choice (separators, escaping, UTF-8 vs UTF-16); it is not a byte
  ceiling - multi-byte characters and JSON escaping expand past the character
  count."

#### F4 - `on_execute` docstring names a nonexistent `_snapshots` attribute

- **Observation** -
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.on_execute`
  docstring (:821): "``_snapshots`` is ``None``". No `_snapshots` symbol
  exists; the code checks `state.snapshots is None`. A grep for the documented
  name finds only this docstring.
- **Evidence** - `grep -c "_snapshots"` prints 1 (this line); `on_execute`
  body reads `state.snapshots`.
- **Impact** - misdirects a maintainer to a name that exists nowhere.
- **Severity** - Medium: stale name in a hook docstring (the contract sentence
  around it is true).
- **Recommendation** - name the real attribute:
- **Must not change** - n/a.
- **Proof** - `grep -c "_snapshots" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten sentence grades true against the `on_execute` body. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol:
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.on_execute`;
  grade: stale; text before: "instances never bracketed: ``_snapshots`` is
  ``None`` and the hook contributes nothing."; text after: "instances never
  bracketed: ``state.snapshots`` is ``None`` and the hook contributes nothing."

### Low

#### F5 - module "can no longer" (process provenance)

- **Observation** - module docstring (:14): "so a single production
  schema-list entry can no longer silently publish the disclosure." "no
  longer" narrates history; the rule is present-tense.
- **Evidence** - the fail-closed gate in `on_operation` (withhold + warn).
- **Impact** - provenance in the module's second paragraph.
- **Severity** - Low: one temporal phrase; the rule beside it is true.
- **Recommendation** - restate as the present-tense rule:
- **Must not change** - n/a.
- **Proof** - `grep -c "no longer" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten sentence grades true against `on_operation`. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: module docstring; grade: process provenance; text before: "the
  misconfiguration, so a single production schema-list entry can no longer
  silently publish the disclosure."; text after: "the misconfiguration, so a
  single production schema-list entry withholds the payload unless the
  deployment acknowledged the disclosure."

#### F6 - hop-ceiling trigger population unstated; the natural count already fired it

- **Observation** - `django_strawberry_framework/extensions/debug.py`
  `_MAX_ORIGINAL_ERROR_HOPS` comment (:121-125): "until a fourth chain-peel
  motivates a shared extraction". At spec-044 slice 1 that counted 2 typing
  peels + this walk; today `utils/typing.py` carries 4 bounded peels plus this
  walk (5 total), so under the natural reading the trigger has fired without
  extraction or a recorded re-decision. The concurrent DRY pass judged the
  trigger unfired by counting only independent peels (the `NonNull`/container
  peels specialize the `of_type` peel), but that population lives in per-cycle
  scratch, invisible to a code reader.
- **Evidence** - `git show 06094ad9:.../typing.py` (2 `range()` peels) vs HEAD
  (4); the sibling docstrings ("narrow sibling", "container-scoped sibling");
  spec-044 rule-of-three passage; DRY R6/R8 rows.
- **Impact** - a reader counting peels concludes the promised extraction is
  overdue; the comment defers a decision whose trigger reads as met.
- **Severity** - Low: bounded clarity; the separation itself is correct and the
  failure-policy difference is truly stated.
- **Recommendation** - pin the population the trigger counts (this proposes no
  extraction):
- **Must not change** - n/a.
- **Proof** - `grep -c "until a fourth chain-peel motivates" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten comment grades true against the typing module's four peels. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `_MAX_ORIGINAL_ERROR_HOPS` comment; grade: stale (unstated
  population); text before: "helper until a fourth chain-peel motivates a
  shared extraction)."; text after: "helper until a fourth independent
  chain-peel motivates a shared extraction (the narrow ``NonNull``/container
  specializations of the ``of_type`` peel do not count)."

#### F7 - truncation-marker comment overclaims with "always"

- **Observation** - `_TRUNCATION_MARKER` comment (:154-155): "so a consumer
  reading the payload can always tell a cut value from a short one." A short
  value that naturally ends with the marker (e.g. SQL text containing the
  literal) is indistinguishable from a cut one; the marker is always PRESENT
  on cuts, not always diagnostic.
- **Evidence** - `_truncate` (appends only when cutting; never inspects
  content).
- **Impact** - universal claim with a reachable counterexample.
- **Severity** - Low: one-word overclaim in an internal comment.
- **Recommendation** - state what the marker does, not what the consumer can
  always infer:
- **Must not change** - n/a.
- **Proof** - `grep -c "can always tell a cut value" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten comment grades true against `_truncate`. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `_TRUNCATION_MARKER` comment; grade: stale (overclaim); text before:
  "The single marker appended to every truncated string, so a consumer reading
  the payload can always tell a cut value from a short one."; text after: "The
  single marker appended to every cut string, so a truncated value reads as
  truncated."

#### F8 - `_row_cost` first line nominal, not imperative

- **Observation** -
  `django_strawberry_framework/extensions/debug.py::_row_cost`: "The
  serialized character cost of one row, counting its string values only." A
  function first line takes the imperative; the file's own query helpers
  (`_truncate`, `_query_log_entries_since`, `_collect_exceptions`) all do.
- **Evidence** - first-line census over the target's 21 function/method
  docstrings: 17 imperative, these 3 nominal (plus the R1 property).
- **Impact** - mood outlier in its own module.
- **Severity** - Low: first-line mood.
- **Recommendation** - verb-first, same content:
- **Must not change** - n/a.
- **Proof** - `grep -c "The serialized character cost of one row" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten first line grades true (imperative). Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `django_strawberry_framework/extensions/debug.py::_row_cost`;
  grade: duplicates the code (mood); text before: "The serialized character
  cost of one row, counting its string values only."; text after: "Return the
  serialized character cost of one row, counting its string values only."

#### F9 - per-row degrade docstring "which is what it used to be" (provenance)

- **Observation** -
  `django_strawberry_framework/extensions/debug.py::_serialized_sql_row_or_dropped`
  docstring (:478): "(or sitting outside a generator expression feeding
  ``list.extend``, which is what it used to be)". "used to be" narrates the
  superseded shape; the why (generator abandonment) survives as a
  present-tense counterfactual.
- **Evidence** - `_build_payload` entry loop (per-row append of successes).
- **Impact** - history residue in the degrade contract's rationale.
- **Severity** - Low: temporal vocabulary; the rationale itself is true.
- **Recommendation** - counterfactual tense, same why:
- **Must not change** - n/a.
- **Proof** - `grep -c "used to be" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten paragraph grades true against `_build_payload`. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol:
  `django_strawberry_framework/extensions/debug.py::_serialized_sql_row_or_dropped`;
  grade: process provenance; text before: "(or sitting outside a generator
  expression feeding ``list.extend``, which is what it used to be) abandons
  the generator on the first refusal and so drops every remaining entry along
  with the offending one"; text after: "(or sitting outside a generator
  expression feeding ``list.extend``) would abandon the generator on the first
  refusal and so drop every remaining entry along with the offending one".

#### F10 - class docstring first line imperative, not a description

- **Observation** -
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension`:
  "Attach Django query-log SQL and execution exceptions to
  ``extensions["debug"]``." A class first line is a description; every other
  class in the module opens descriptively.
- **Evidence** - sibling class first lines (`_DebugSQLRow`,
  `_CursorCaptureCoordinator`, `_DebugOperationState`), all descriptions.
- **Impact** - mood outlier; the class is the module's public surface.
- **Severity** - Low: first-line mood.
- **Recommendation** - description, same content:
- **Must not change** - n/a.
- **Proof** - `grep -c "Attach Django query-log SQL" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten first line grades true (description). Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol:
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension`;
  grade: duplicates the code (mood); text before: "Attach Django query-log SQL
  and execution exceptions to ``extensions["debug"]``."; text after:
  "Development-only extension publishing Django query-log SQL and execution
  exceptions under ``extensions["debug"]``."

#### F11 - `_acknowledged` first line nominal, not imperative

- **Observation** -
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._acknowledged`:
  "The settled acknowledgement, ``False`` for an extension that settled none."
  Same mood rule as F8; the method is called for its answer, so it commands.
- **Evidence** - in-file imperative majority (same census as F8).
- **Impact** - mood outlier in its own module.
- **Severity** - Low: first-line mood.
- **Recommendation** - verb-first, same content:
- **Must not change** - n/a.
- **Proof** - `grep -c "The settled acknowledgement," django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten first line grades true (imperative). Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol:
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._acknowledged`;
  grade: duplicates the code (mood); text before: "The settled acknowledgement,
  ``False`` for an extension that settled none."; text after: "Return the
  settled acknowledgement, ``False`` for an extension that settled none."

#### F12 - `_disclosure_permitted` first line nominal, not imperative

- **Observation** -
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._disclosure_permitted`:
  "Whether this operation may publish the debug payload (spec-048 Decision
  5)." Same mood rule as F8; "Whether..." describes where the imperative
  commands.
- **Evidence** - in-file imperative majority (same census as F8).
- **Impact** - mood outlier in its own module.
- **Severity** - Low: first-line mood.
- **Recommendation** - verb-first, same content and kept spec-Decision pointer:
- **Must not change** - n/a.
- **Proof** - `grep -c "Whether this operation may publish" django_strawberry_framework/extensions/debug.py` prints 0 (1 today); the rewritten first line grades true (imperative). Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol:
  `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._disclosure_permitted`;
  grade: duplicates the code (mood); text before: "Whether this operation may
  publish the debug payload (spec-048 Decision 5)."; text after: "Return
  whether this operation may publish the debug payload (spec-048 Decision 5)."

#### F13 - own test module "which is now" (process provenance)

- **Observation** - `tests/extensions/test_debug.py` module docstring (:27):
  "which is now the extension's fail-closed condition". "now" dates the rule;
  the posture is present-tense.
- **Evidence** - the fail-closed gate (same behavior F5 cites from the target
  side).
- **Impact** - provenance in the test module's posture paragraph.
- **Severity** - Low: one temporal word; the posture claim is true.
- **Recommendation** - drop the temporal:
- **Must not change** - n/a.
- **Proof** - `grep -c "which is now the extension" tests/extensions/test_debug.py` prints 0 (1 today); the rewritten sentence grades true against the gate. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `tests/extensions/test_debug.py` module docstring; grade: process
  provenance; text before: "The suite runs with ``settings.DEBUG`` false,
  which is now the extension's fail-closed condition"; text after: "The suite
  runs with ``settings.DEBUG`` false, which is the extension's fail-closed
  condition".

#### F14 - three test-helper first lines describe instead of commanding

- **Observation** - `tests/extensions/test_debug.py::default_wrapper` ("The
  current thread's concrete ..."), `::_sql_row` ("A wire-shaped SQL row ..."),
  `::_exception_row` ("A wire-shaped exception row ...") open nominally. The
  axis rule takes the imperative for functions, and the reviewed test modules'
  helper convention is imperative (fixture/builder verbs); all three move
  together, so the file stays uniform either way.
- **Evidence** - helper-mood census over the own test module (each first line
  read): exactly these three docstring'd function helpers, all nominal; the
  one docstring'd helper class (`_MarkerSQLExtension`) correctly descriptive;
  test docstrings state behavior descriptively per the axis.
- **Impact** - bounded clarity; three first lines break the reviewed
  convention for helpers.
- **Severity** - Low.
- **Recommendation** - re-mood each to the imperative; see text-after.
- **Must not change** - n/a.
- **Proof** - `grep -c -e "The current thread's concrete" -e "A wire-shaped SQL row" -e "A wire-shaped exception row" tests/extensions/test_debug.py` prints 0 (3 today, one per site); all three rewritten first lines grade true. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `tests/extensions/test_debug.py::default_wrapper`,
  `::_sql_row`, `::_exception_row`; grade: duplicates the code (mood, x3);
  text before: "The current thread's concrete ``default`` wrapper, flag
  restored after the test." / "A wire-shaped SQL row whose ONLY string cost is
  ``sql`` (empty vendor/alias)." / "A wire-shaped exception row whose string
  cost is ``message`` plus ``stack``."; text after: "Yield the current
  thread's concrete ``default`` wrapper, restoring its flag after the test." /
  "Build a wire-shaped SQL row whose ONLY string cost is ``sql`` (empty
  vendor/alias)." / "Build a wire-shaped exception row whose string cost is
  ``message`` plus ``stack``."

#### F15 - NaN-row test docstring "used to be abandoned" (provenance)

- **Observation** -
  `tests/extensions/test_debug.py::test_a_nan_duration_costs_only_its_own_row_and_the_rest_keep_their_order`
  docstring: "the rows logged AFTER the bad one used to be abandoned with it".
  Same "used to be" vocabulary as F9; the per-row why survives as a
  counterfactual.
- **Evidence** - the test's middle-NaN shape (both good rows survive, in log
  order); F9's production rationale.
- **Impact** - history residue in the degrade test's rationale.
- **Severity** - Low: temporal vocabulary; the rationale is true.
- **Recommendation** - counterfactual tense, same why:
- **Must not change** - n/a.
- **Proof** - `grep -c "used to be abandoned" tests/extensions/test_debug.py` prints 0 (1 today); the rewritten sentence grades true against the test body. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol:
  `tests/extensions/test_debug.py::test_a_nan_duration_costs_only_its_own_row_and_the_rest_keep_their_order`;
  grade: process provenance; text before: "the rows logged AFTER the bad one
  used to be abandoned with it and a single hostile duration silently
  truncated the diagnostic from that point on."; text after: "the rows logged
  AFTER the bad one would be abandoned with it and a single hostile duration
  would silently truncate the diagnostic from that point on."

#### F16 - live-tier module docstring "now the extension's fail-closed condition"

- **Observation** -
  `examples/fakeshop/test_query/test_debug_extension_api.py` module docstring
  (:25-26): "now the extension's fail-closed condition". Same "now" as F13,
  in the live tier's posture paragraph about the target's gate.
- **Evidence** - same gate behavior as F5/F13.
- **Impact** - provenance twin of F13 in the tier that pins the gate live.
- **Severity** - Low: one temporal word; the posture claim is true.
- **Recommendation** - drop the temporal:
- **Must not change** - n/a.
- **Proof** - `grep -c "now the extension's" examples/fakeshop/test_query/test_debug_extension_api.py` prints 0 (1 today); the rewritten sentence grades true against the gate. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: live `test_debug_extension_api.py` module docstring; grade: process
  provenance; text before: "Because the suite runs with ``settings.DEBUG``
  false - now the extension's fail-closed condition"; text after: "Because the
  suite runs with ``settings.DEBUG`` false - the extension's fail-closed
  condition".

#### F17 - governance prose "forbids a pre-built instance" overstates the docstring

- **Observation** - `tests/test_ci_governance.py` characterizes the target's
  docstring twice (comment :367, docstring :412) as "REQUIRES the bare class
  and forbids a pre-built instance". The target docstring requires per-operation
  freshness (class or building factory) and leaves a pre-built instance
  "outside the guarantee" - it forbids nothing: shared entries demonstrably
  serve under `DjangoSchema` (per-operation state binding), and only the
  engine warns (`DeprecationWarning`) on the instance spelling.
- **Evidence** - class docstring operation-locality paragraph (:616-626);
  `tests/extensions/test_debug.py::test_one_operations_payload_is_not_the_extensions`
  (shared instance serves two operations); the live parse-failure
  singleton-factory row.
- **Impact** - a reader concludes instance entries are rejected; they are
  served-but-unguaranteed (plain schema) or fully isolated (`DjangoSchema`).
- **Severity** - Low: overstatement in classifier rationale prose.
- **Recommendation** - "leaves ... outside the guarantee" at both sites:
- **Must not change** - n/a.
- **Proof** - `grep -c "forbids a" tests/test_ci_governance.py` prints 0 (2 today, one per site); both rewritten sentences grade true against the class docstring. Run at `review/extensions/debug.py/verify-comments-<n>`.
- **Freshness** - see Trace fingerprints.
- Symbol: `tests/test_ci_governance.py` negative-controls comment +
  `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_ignores_the_permitted_shapes`;
  grade: stale (overstatement, x2); text before: "the debug extension's own
  docstring REQUIRES the bare class and forbids a pre-built instance" /
  "``DjangoDebugExtension``'s docstring REQUIRES the bare class and forbids a
  pre-built instance"; text after: "the debug extension's own docstring
  REQUIRES the bare class and leaves a pre-built instance outside the
  guarantee" / "``DjangoDebugExtension``'s docstring REQUIRES the bare class
  and leaves a pre-built instance outside the guarantee".

## Rejected

- **R1 - `allow_unsafe_production` property nominal opener.** "The
  acknowledgement this extension was constructed with, as a read." A read-only
  property answers with a value and reads nominally; the imperative rule
  governs callables (F8/F11/F12), which take verbs at their call sites.
  Trigger: an imperative-property precedent in a reviewed module.
- **R2 - "Scenario N" section banners.** Bare scenario ordinals throughout both
  test tiers name no spec, but they are the repo's scenario convention (same
  family as bare `Decision N`), anchored for this file by the module
  docstrings' spec-044/spec-048 pointers. Trigger: a gate covering scenario
  ordinals.
- **R3 - "Since spec-048 Decision 5" (live capture test).** A pointer to a
  spec Decision is the kept form; the "Since" dating alone is outside the
  provenance vocabulary, and the sentence's operative content is the
  present-tense gate rule. Trigger: Since-dating ruled provenance.
- **R4 - streaming-test past-tense regression shape.** "Without that stash a
  WS-served schema published no debug key at all ... and the same schema
  diverged by transport" is an anchored counterfactual (the invariant "the
  payload must be stashed at the executing hook's teardown" sits in the same
  docstring) with no banned vocabulary; filed equivalents (F9/F15) rest on
  explicit "used to be". Trigger: a tense rule covering pure-past
  counterfactuals.
- **R5 - live off-by-default "0.0.13" scope note.** Names the superseded
  byte-identity contract the scenario deliberately does NOT pin; a test-scope
  rationale, not prose about the target's symbols. Trigger: version-dating
  ruled provenance for test scopes.
- **R6 - module "bounded serialized size" vs the budget disclaimer.** No
  contradiction: the payload is bounded by the combination of caps (row
  counts, per-row truncation, text budget), while 262144 is not itself the
  encoded-size bound - which is all the disclaimer claims. Trigger: an
  encoded-byte-size pin.
- **R7 - own test module factory/posture rule vs streaming rows.** "the
  acknowledgement factory ... only where keeping ``DEBUG`` false is itself
  the point": every factory row runs DEBUG-false and no bare-class-semantics
  row uses the factory, so the operative discipline holds; point/posture
  looseness is style. Trigger: a stricter wording rule for test-posture
  claims.
- **R8 - "the only code"/"single owner"/"one place" phrasings.** Production
  scope is the convention (tests necessarily touch seams to pin them); the
  claims hold over production code. No trigger: convention.

Handoff: Read beyond the record's trace: the DRY per-cycle notes on the
chain-peel trigger (judged unfired there; F6 pins that reading into the
comment rather than relitigating it), both prior reviewed test modules'
helper-mood censuses (the F14 convention call), graphene `tracking.py` and
installed Django 6.1 sources, and the `0.316.0`-era typing module for the
peel count. Conclusions the findings do not state: the file is otherwise
unusually well-described - every wire shape, degrade, ordering, and gate
claim verified against body, caller, or upstream; the four Mediums are all
bounded prose defects (two module-docstring reasons, one backwards
inequality, one dead name), no contract a test pins is misstated. Open
threads: F16/F17 touch files no higher finding touches (likely deferred
under the ride rule - Worker-0's call); no `Routed:` leads (every
neighboring package site verified true); no `## Cross-axis` section (no
out-of-axis finding: the untruncated `vendor`/`alias`/`excType` strings are
still budget-admitted, so F3 has no Mechanics defect underneath). No
production code or test was edited; the only writes are this record and
scratch under `docs/review/temp-tests/extensions-debug/comments/`.

## Verification (Comments)

Address `review/extensions/debug.py/verify-comments-1`. Implement pass 1
landed F1-F15 plus Mechanics C1's three sites; F16/F17 deferred untouched.
No workspace run: every check below is a static grep or a read-only
instrument in the shared tree. No `workspace.py` run id exists for this
pass; `workspace.py audit` has no run to check.

Step-1 note: the dispatch carried no expected item-diff hash, so the
hash-equality gate had nothing to compare against; the item scope was taken
as the two files below and every Proof was run verbatim there instead.
(`rg` is not installed in this environment; the one `rg` Proof ran as its
`grep -E` equivalent, same pattern.)

Proof results (all run verbatim at the address above; `grep -c` exit 1 on
a 0 count is the count, not a failure):

- F1: `grep -c "engine reads extension results before this hook"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F2: `grep -c "whatever the order"
  django_strawberry_framework/extensions/debug.py` prints 1. Pass.
- F3: `grep -c "so a character ceiling is a byte"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F4: `grep -c "_snapshots"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F5: `grep -c "no longer"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F6: `grep -c "until a fourth chain-peel motivates"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F7: `grep -c "can always tell a cut value"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F8: `grep -c "The serialized character cost of one row"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F9: `grep -c "used to be"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F10: `grep -c "Attach Django query-log SQL"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F11: `grep -c "The settled acknowledgement,"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F12: `grep -c "Whether this operation may publish"
  django_strawberry_framework/extensions/debug.py` prints 0. Pass.
- F13: `grep -c "which is now the extension"
  tests/extensions/test_debug.py` prints 0. Pass.
- F14: `grep -c -e "The current thread's concrete" -e "A wire-shaped SQL
  row" -e "A wire-shaped exception row" tests/extensions/test_debug.py`
  prints 0. Pass.
- F15: `grep -c "used to be abandoned" tests/extensions/test_debug.py`
  prints 0. Pass.
- C1 (Mechanics `## Cross-axis (for Comments)`): `grep -E -n "leave
  .*result.* as None" django_strawberry_framework/extensions/debug.py`
  prints no line. Pass with a note (below): the literal pattern matches
  neither the live text nor the pre-image (both spell ``None`` with RST
  double backticks, which the pattern's ` as None` never matches), so the
  Proof's letter holds vacuously and the substance is the manual grade of
  the four reworded sentences, all true (see F1/C1 grade).
- F16 deferred: `grep -c "now the extension's"
  examples/fakeshop/test_query/test_debug_extension_api.py` prints 1, same
  line 25 as the fingerprint; the file has an empty diff-stat against
  ITEM_BASELINE. Pass (still present, untouched).
- F17 deferred: `grep -c "forbids a" tests/test_ci_governance.py` prints 2,
  same lines 367/412; empty diff-stat against ITEM_BASELINE. Pass (still
  present, untouched).

Grades of the landed text (each as the whole docstring or comment it sits
in; known deviations from record text-after accepted where noted):

- F1 (converged with C1): the module sentence now reads "the stash writer
  publishes only for a graphql-core ``ExecutionResult`` (sync leaves
  ``result`` as ``None`` or a strawberry pre-execution shape,
  version-dependent; async assigns a strawberry ``PreExecutionError``)".
  True. The guard clause matches `_stash_payload_if_executed`'s
  `isinstance(result, GraphQLExecutionResult)`; the sync disjunction holds
  on installed strawberry-graphql 0.324.0 (`execute_sync` assigns the
  strawberry pre-execution `ExecutionResult` at `execution_context.result`
  before the operation context unwinds, with the "Match the async path"
  comment) and covers the 0.316.0 floor either way it behaves; the async
  half matches `_prepare_operation_async` returning `PreExecutionError`,
  assigned via `_handle_execution_result`. The no-key outcome stays pinned
  by the existing tests on all colors.
- C1's three sites (class Lifecycle paragraph, `on_operation` teardown
  comment, `_stash_payload_if_executed` docstring): each now reads
  "``None`` or a strawberry pre-execution shape (version-dependent)" for
  sync and keeps the async `PreExecutionError` half. True, same engine
  evidence as F1; the gate sentence beside each already handles both
  shapes, and the no-key contract sentence is unchanged.
- F2: the scoped bullet agrees with the class streaming paragraph
  (streaming transports receive the pre-masking payload whatever the list
  order) and `on_execute`'s stash. True.
- F3: encoder-independence plus the honest non-ceiling agrees with
  `_row_cost` (`len()` of pre-encoding Python strings) and with the
  following paragraph's own disclaimer; the backwards inference is gone.
  True.
- F4: `state.snapshots` is the name the `on_execute` body reads; no
  `_snapshots` symbol exists anywhere. True.
- F5: present-tense withhold rule, true against the `on_operation`
  fail-closed gate (withhold + warn). True, no provenance.
- F6: "a fourth independent chain-peel ... (the narrow
  ``NonNull``/container specializations of the ``of_type`` peel do not
  count))" — the population matches `utils/typing.py` (4 bounded peels;
  the "narrow sibling" and "container-scoped sibling" docstrings), and the
  added closing paren rebalances the outer "(deliberately NOT imported"
  paren: two opens, two closes. True.
- F7: "appended to every cut string, so a truncated value reads as
  truncated" matches `_truncate` (marks only when cutting, never inspects
  content). True.
- F8/F11/F12/F14: "Return ..."/"Yield ..."/"Build ..." imperative
  first lines, same content; F12 keeps the spec-048 Decision 5 pointer.
  True, mood rule holds.
- F10: "Development-only extension publishing query-log SQL and exceptions
  under ``extensions["debug"]``." — description, same content, D205-clean
  (period + blank line), 104 chars within the E501 grace for a line the
  formatter cannot break. The shortening from the 121-char record
  text-after is accepted. True.
- F9/F15: counterfactual rewordings, same why, true against
  `_build_payload`'s per-row append and the middle-NaN test shape. True.
- F13: temporal dropped, posture claim true against the gate. True.
- (d) `_query_log_entries_since` docstring ("indexed tail access over the
  clamped window", budget bound, kept rollover disclaimer): true against
  the landed bounded-drain body and the `remaining`-budget caller.
- New prose inside the out-of-scope hunks (the Mech gate comment, the
  three Perf/Mech proof-test docstrings): each graded true as found — the
  gate comment states the present-tense two-exception rule the body
  implements, the test docstrings state behavior descriptively per the
  axis — and none carries banned vocabulary, a line reference, or `we`.

Axis instruments on the changed files: `build_tree_md.py
--list-docstrings` ok on both (module first lines byte-identical to
baseline, so no TREE.md row owed); `check_citations.py --paths ...
--substrings` 1 citation each, both resolve, 0 unresolved (same as the
review pass); provenance sweep over both files shows only kept
spec-Decision pointers, `threading.Thread`/`max_workers` code tokens, the
rejected R2 scenario banner, and `discard`/`rounded` substring
false-positives; `we`/`you` 0 hits; "Tests that"/"Ensures" 0 hits;
added-line vocab sweep (provenance + `we`/`you` + test-mood) clean;
`ruff check` and `ruff format --check` pass on both files;
`check_trailing_commas.py --check` 0 violations. The item prose diff
(`review_changed_python_diffs_against_head.py ... --prose`, under
`verify-comments-1/diff/`) enumerates exactly the F1-F15 + C1 + (d)
hunks plus the four expected `[code changed too]` sites (the gate, three
proof tests) — no surprise prose.

Behavior preservation (code-digest identity): the Perf/Mech code hunks
are out of Comments scope and were excluded by hunk. Reconstruction =
ITEM_BASELINE text plus only those code hunks (built by
`verify-comments-1/build_recon.py`, every replacement exact-once):
`review_inspect.py --code-digest recon_debug.py` vs the live target
prints `sha256:a9fbb73c...` twice, exit 0; recon vs live tests prints
`sha256:0e235c2a...` twice, exit 0. Control: baseline-vs-live digest
exits 1 (the Perf/Mech code moved), so the inverse proof is sound — the
F1-F15 + C1 + (d) prose hunks move no executable code.

No new finding under step 6 and no routed gap: every docstring Worker-2
wrote or moved in these files grades true, and no touched symbol was made
false.

Fingerprints (live bytes verified): `extensions/debug.py` da22bf47,
`tests/extensions/test_debug.py` 445e4ac3, live tier 8417985a (unchanged),
`tests/test_ci_governance.py` cfc66f6e (unchanged), `utils/typing.py`
a672cd6b (unchanged); engine strawberry-graphql 0.324.0.

Handoff (verify-comments-1): all fifteen implemented findings pass their
record Proofs and grade true as landed, with the four dispatch-noted
deviations (F1/C1 convergence, F10 shortening, F6 paren rebalance, (d)
bounded-drain docstring) each verified true. F16/F17 confirmed deferred
and byte-untouched. Code-digest identity holds on both files. One
standing note for Worker-0: C1's literal Proof pattern never matched the
backticked prose (0 lines pre- and post-image), so its letter is vacuous;
the grade carried the substance. Scratch kept under
`docs/review/temp-tests/extensions-debug/verify-comments-1/`
(`baseline_*.py`, `recon_*.py`, `build_recon.py`, `diff/`).
