# Review · Comments: `django_strawberry_framework/routers.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=eb71162ba7be2797bf4dbdb4e7d24da989e96eed

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-routers.md` (skeleton: `Status: reviewing`, blank Path
class), all three axis records, then the WHOLE live target. Sibling
`rev-routers.performance.md` read whole (Status: no-findings, Path class
cold, six rejections R1-R6, no `## Cross-axis` section; its Handoff flags
R1's double compile and R5's unmemoized module hook as revisitable
judgments, both cold contract costs, no Comments content; it judges the
plan's Routed lead out-of-axis). Sibling `rev-routers.mechanics.md` read
whole (Status: no-findings, seven rejections R1-R7; its `## Cross-axis
(for Comments)` routing note judges the plan's Routed lead to carry no
mechanics content and routes the three wordings onward; its Handoff routes
the `require_drf` "three guards" count OUT to that pending item, which
this record independently confirms as Routed R1). Sibling
`rev-routers.comments.md` did not exist (this record creates it; a first
attempt left no record, and its `inspect/` orientation plus `routers.json`
scratch under `docs/review/temp-tests/routers/comments/` was reused
without being redone, per the dispatch).

Target read whole (543 lines, blob `e18772f7`, same bytes both siblings
fingerprinted). The target is dirty vs HEAD (`+24/-18`, concurrent work,
reviewed as it stands, no hunk attributed here: the truthful-reads
migration on construction and raise paths only) and byte-identical to
ITEM_BASELINE (`git diff eb71162b -- <target> <tests>` empty). Own test
module `tests/test_routers.py` read whole (6551 lines, blob `f513d869`,
same bytes both siblings fingerprinted; dirty vs HEAD, identical to
ITEM_BASELINE).

Scope coordination with `rev-consumers.comments.md` (read whole, Status:
verified): that pass grades `tests/test_routers.py` prose about
*consumers* symbols (2 findings implemented and verified; rejections for
"moved from `subscribe` + `execute`", "no longer matches" /
"previously authorized" / "no longer exists", and "pre-hook", all kept).
This record defers to every one of those rulings and judges the rest of
the module: routers-subject prose, general harness prose, and
consumers-subject prose its flag scan saw but it left unruled (it read
only the six claim-densest bodies fully). The plan's Routed lead (the
`_ws_communicator`, keyword-only-pattern, and factory-body wordings) is
judged here as F2, F3/F4, and F5. The two docstrings the consumers item
already rewrote in this module (subscribe-before-init, legacy
revalidation) grade true as they stand and are not re-filed.

Instruments (all static; no workspace run was needed): the reused
`review_inspect.py` census for the target (10 symbols, 10 docstrings, 27
comment blocks, 14 flagged) plus a fresh `review_inspect.py` census of
the own test module under `docs/review/temp-tests/routers/comments/`
(279 symbols, 200 docstrings, 435 comments) to close the mood sweep;
`build_tree_md.py --list-docstrings` on both files (1 module, 0 breaking,
each); `check_citations.py --paths <file> --substrings --json` (target 7
citations, own tests 10 citations, 0 violations); the REVIEW.md
provenance pattern plus `used to` / `Before ` / voice scans over both
files; first-line mood census over all 200 test docstrings. Every grade
below is against the live text at the fingerprints in this section, each
claim checked against its body and one real caller or authority:
installed Django 6.1 (`RegexPattern` / `LocaleRegexDescriptor`,
`ASGIRequest`), installed channels 4.3.2 (== the package floor) with
Django 6.1, installed strawberry-graphql 0.324.0 (`strawberry.channels`
module-level `channels.db` import), spec-046 and its rationale companion
(Decision 2 / Decision 4 texts and the four `#` pinpoints, all resolved),
`pyproject.toml` classifiers (Django 5.2, 6.0, 6.1) and the
`channels[daphne]>=4.3.2` row, and a stdlib `inspect.signature(...).bind`
probe for the T6 rationale (verbatim in that finding).

Other-module prose census: every package mention of the target's symbols
(`consumers.py` module docstring + validator prose, `views.py` module
docstring, `utils/imports.py::require_optional_module` docstring,
`rest_framework/__init__.py::require_drf` docstring,
`auth/sessions.py` hint comment + guard + error string) and every other
test module's prose about them (`tests/auth/test_mutations.py`,
`tests/auth/test_sessions.py`, `tests/mutations/test_write_transaction.py`,
`tests/utils/test_imports.py`; `tests/test_consumers.py` and the live
tier hold none) was read and graded: true stays unfiled, one stale
sentence is filed here (G1, about this target's symbol), two stale
censuses about other modules' symbols are Routed (R1, R2).

Cells: default, sharded, and pg are all `inapplicable by construction`
for this Comments pass (no database-reaching probe; every Proof is a
static count plus a grade judgment; Worker-2's prose edits owe
`--code-digest` identity, not cell runs). Cells unverified: none. Run
ids: none (no `workspace.py` runs).

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/routers.py`
`e18772f76beed8f42cc5bba0d7b9a4e7c7f77bd2` (live, whole, dirty, ==
ITEM_BASELINE); `tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (live, whole, dirty, ==
ITEM_BASELINE); `django_strawberry_framework/consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (module docstring, validator
prose); `django_strawberry_framework/views.py`
`48ee582ecdba41d49beb2434f2a9e0af992d39d4` (module docstring);
`django_strawberry_framework/utils/imports.py`
`291ecedd30c7d8af9c007758112e867c09d031eb`
(`require_optional_module` docstring);
`django_strawberry_framework/rest_framework/__init__.py`
`45cf7b63a2b768421b80b99ee78ec048a03641e1` (`require_drf` docstring);
`django_strawberry_framework/auth/sessions.py`
`865d6e704d2df50bcad465ad3005eccb39e8c545` (hint comment, guard,
classifier); `tests/auth/test_mutations.py`
`ff8a261d09ca63a0f606673bf11b9262f2bb1f35` (`_channels_router`
docstring); `tests/utils/test_imports.py`
`e39ac485ca7253ebd1ec2f07b26d164a480ac3d7` (module docstring);
`tests/auth/test_sessions.py`
`b71c84ecd4dc90b9af37518d186716f1d64d9a96` (error-string assertion);
`tests/mutations/test_write_transaction.py`
`689e31f47ae0dc010e67386e4a076b782afac5ff` (socket-harness region);
`docs/SPECS/spec-046-transport_security-0_0_14.md`
`8d8adaf2f2f07cbc6cd3d434a029b2419b7d4704` (Decisions 2 and 4);
`docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`
`63f2f1f601fe47f9e7a96254bfe2e5dd084f58a2` (Decision 4 rationale);
`docs/review/rev-routers.performance.md`
`1023ed524d3c0aa6fac881bfc55175017906df95` (whole);
`docs/review/rev-routers.mechanics.md`
`b957bda42641ff422ed2f66df61aa2dc2e344cf4` (whole);
`docs/review/rev-consumers.comments.md`
`20dd334645dae9b075dc1669c134962ee56f2f78` (whole);
`docs/review/rev-routers.md` `aaf32dd8163a5985aa3c679cf7d97d296a4586b5`;
`pyproject.toml` `964c13392fd19e521decafdbffb87a9bc35a6a27`
(classifiers, channels row). A finding's Freshness lists only files
beyond these: none.

## Findings

### High

None.

### Medium

- Observation: three unscoped "the single" install-hint claims, all
  rotted the same way. The `_CHANNELS_INSTALL_HINT` comment calls it
  "The single channels-ABSENT install hint", the `require_channels`
  docstring says it passes "the single `_CHANNELS_INSTALL_HINT`
  string", and the `_build_router_class_uncached` docstring says every
  true-absence path routes through "the single install hint". Since
  `c8346750` (2026-07-21) a second feature-keyed absent-hint exists,
  `auth/sessions.py::_CHANNELS_INSTALL_HINT` ("The single
  channels-ABSENT install hint for the auth transport"), deliberately
  scoped to its feature per the Mechanics R1 ruling. Each routers claim
  is true of its own module or builder and false as written
  package-wide.
- Evidence: live `auth/sessions.py` hint block read (second hint plus
  second `require_channels` wrapper over the same primitive);
  `require_optional_module` caller census (four named thin wrappers).
- Impact: a reader auditing the install-hint surface from any of the
  three sentences undercounts it and may "consolidate" the auth hint
  into the router's, misdirecting the consumer the auth guard is trying
  to help.
- Severity: Medium (stale census on internal code; same class as the
  consumers Medium enumeration).
- Recommendation: scope each claim to its module or builder and name
  the twin once; see text-after.
- Must not change: n/a.
- Proof: `grep -c -i 'the single' django_strawberry_framework/routers.py` prints `0` (3 today); the rewritten sentences earn grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py`
  (`_CHANNELS_INSTALL_HINT` comment;
  `django_strawberry_framework/routers.py::require_channels`;
  `django_strawberry_framework/routers.py::_build_router_class_uncached`).
- Grade: stale.
- Text-before:
  `The single channels-ABSENT install hint (spec-041 Decision 5).`
  and
  `passing the single ``_CHANNELS_INSTALL_HINT`` string`
  and
  `so every true-absence path routes through the single install hint`
- Text-after:
  `This module's single channels-ABSENT install hint (spec-041 Decision 5). The auth transport carries its own feature-keyed twin (``auth/sessions.py``).`
  and
  `passing this module's ``_CHANNELS_INSTALL_HINT`` string`
  and
  `so every true-absence path of this builder routes through its single install hint`

- Observation: the `_CHANNELS_INSTALL_HINT` comment bounds the floor's
  Django coverage as "the package's whole advertised Django range
  through 6.0", but the package advertises 5.2, 6.0, AND 6.1
  (`Framework :: Django` classifiers). The bound was born true in
  `d46e68b9` (2026-07-06) and rotted when `2b44819d` (2026-08-06)
  advertised 6.1 without updating it. The floor genuinely covers 6.1:
  the shared `.venv` pairs floor channels 4.3.2 with Django 6.1 and
  the suite is green on it.
- Evidence: `pyproject.toml` classifier rows read; both commits dated
  via `git log`; installed `channels.__version__` / `django.__version__`
  (`4.3.2` / `6.1`) read from the live interpreter.
- Impact: a reader takes 6.0 for the ceiling of the floor's coverage
  and may mistrust or needlessly raise the floor for a 6.1 deployment.
- Severity: Medium (stale bound on internal code).
- Recommendation: extend the bound to the advertised ceiling; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'through 6\.0' django_strawberry_framework/routers.py` prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py`
  (`_CHANNELS_INSTALL_HINT` comment).
- Grade: stale.
- Text-before:
  `One floor covers the package's whole advertised Django range through 6.0.`
- Text-after:
  `One floor covers the package's whole advertised Django range through 6.1.`

### Low

- Observation: the module docstring's soft-dependency paragraph ends
  "The HTTP half of the card needs none of it". "The card" is board
  residue: it names the kanban card that delivered the split, not a
  property of the code, and the sentence is complete without it.
- Evidence: first-line-plus-body read; "card" is REVIEW.md provenance
  vocabulary with no other hit in either graded file.
- Impact: trivial process residue in the module's standing contract
  paragraph.
- Severity: Low.
- Recommendation: drop the filler; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'half of the card' django_strawberry_framework/routers.py` prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py` (module docstring,
  soft-dependency paragraph).
- Grade: process provenance.
- Text-before:
  `The HTTP half of the card needs none of it: ``views.py`` is channels-free, so a WSGI-only project adopts the GraphQL view without the soft dependency.`
- Text-after:
  `The HTTP half needs none of it: ``views.py`` is channels-free, so a WSGI-only project adopts the GraphQL view without the soft dependency.`

- Observation: the `_MISSING_DJANGO_APPLICATION_HINT` comment ends its
  two-place-repair gloss with "migration is no longer one line". The
  temporal contrast is gratuitous: the comment already states the
  two-place repair, and "no longer" describes how the migration came to
  be rather than the hint's present contract.
- Evidence: comment read against the hint string it describes (which
  carries the versioned migration prose itself, where it belongs).
- Impact: trivial temporal residue in a construction-boundary comment.
- Severity: Low.
- Recommendation: delete the trailing clause; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'no longer one line' django_strawberry_framework/routers.py` prints `0` (1 today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py`
  (`_MISSING_DJANGO_APPLICATION_HINT` comment).
- Grade: process provenance.
- Text-before:
  `flagged, and the two-place repair (the asgi.py argument AND the URLconf entry - migration is no longer one line).`
- Text-after:
  `flagged, and the two-place repair (the asgi.py argument AND the URLconf entry).`

- Observation: the `_validated_websocket_url_pattern` docstring says a
  non-string value would "silently install a route that never matches".
  The stringification half is exactly true (Django's
  `LocaleRegexDescriptor` compiles `str(pattern)` lazily, so an
  arbitrary `__str__` runs at the first handshake), but "never matches"
  overclaims: `str(7)` is `"7"`, which matches path `"7"` - the route
  matches the stringified value instead of the intended pattern, which
  is a stronger reason to reject it than never matching at all.
- Evidence: installed Django 6.1 `resolvers.py` (`RegexPattern` stores
  `_regex` verbatim; the descriptor compiles `str(pattern)` on first
  access) read against the docstring sentence.
- Impact: a reader takes away a weaker, false mechanism (fail-closed
  non-match) for a boundary whose true mechanism (wrong-path match) is
  the sharper justification.
- Severity: Low (bounded prose precision; the rejection it justifies is
  correct).
- Recommendation: state the stringified-match mechanism; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'route that never matches' django_strawberry_framework/routers.py` prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py::_validated_websocket_url_pattern`.
- Grade: stale (false on its own date, not by a body change since).
- Text-before:
  `That makes ``None``, a number, or an arbitrary object silently install a route that never matches (and runs an arbitrary object's ``__str__`` later, during the first handshake).`
- Text-after:
  `That makes ``None``, a number, or an arbitrary object silently install a route matching the stringified value instead of the intended pattern (and runs an arbitrary object's ``__str__`` later, during the first handshake).`

- Observation: the `_factory_application` docstring's rejected
  alternative says arity-checking the RESULT with `bind(scope, receive,
  send)` "would falsely reject legitimate `*args` middleware,
  `functools.partial` mounts and callable instances whose `__call__` is
  a C slot". Two of the three would NOT be rejected: `bind` accepts
  `*args` shapes and `partial` mounts exactly as the call does
  (probed below), so the check would only ever fire on wrong-arity
  callables, which fail at the handshake with their own traceback
  anyway. Only the un-introspectable C result is a real dilemma, and
  only because it would force the same pass-through the convention
  check already grants.
- Evidence: stdlib probe, installed interpreter, no package import:
  `inspect.signature(f).bind({}, {}, {})` binds for an
  `(scope, receive, send)` function, a `(*args)` function, a
  `functools.partial` of the first, and a `(*args)`-`__call__`
  instance, and `inspect.signature` raises `TypeError` for a C-slot
  object. (`**kwargs`-only rejects, but it would fail the call too,
  so rejecting it is correct, not false.)
- Impact: a reader takes away a false mechanism for a sound decision;
  the next arity-check proposal argues against examples that would
  not have failed.
- Severity: Low (bounded prose precision; the floor-not-proof
  conclusion stands).
- Recommendation: restate the alternative with the accurate
  mechanism; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'falsely reject legitimate' django_strawberry_framework/routers.py` prints `0` (1 today); the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py::_factory_application`.
- Grade: stale (wrong stated reason, DRY principle 10; false on its
  own date).
- Text-before:
  `Rejected alternative: arity-checking the RESULT with ``bind(scope, receive, send)``, which would falsely reject legitimate ``*args`` middleware, ``functools.partial`` mounts and callable instances whose ``__call__`` is a C slot - a real cost for no security gain.`
- Text-after:
  `Rejected alternative: arity-checking the RESULT with ``bind(scope, receive, send)``. ``bind`` accepts ``*args`` shapes and ``functools.partial`` mounts exactly as the call does, so the check would only fire on wrong-arity callables - which fail at the handshake with their own traceback anyway - while an un-introspectable result (a C-defined ``__call__``) would force the same pass-through the convention check already grants: a real cost for no security gain.`

- Observation: the `DjangoGraphQLProtocolRouter` class docstring opens
  "The ASGI entrypoint, which now pairs with one URLconf entry". The
  "now" contrasts the removed 0.0.14 asgi-only arrangement; the
  arrangement sentence is complete and present-tense without it, and
  the spec-Decision pointer already anchors the design.
- Evidence: class-docstring read; no runtime sequence reading is
  available (it describes the static arrangement).
- Impact: trivial temporal residue on the public class's contract
  paragraph.
- Severity: Low.
- Recommendation: drop the temporal; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'which now pairs' django_strawberry_framework/routers.py` prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/routers.py::_build_router_class_uncached.DjangoGraphQLProtocolRouter`.
- Grade: process provenance.
- Text-before:
  `The ASGI entrypoint, which now pairs with one URLconf entry (spec-046 Decisions 2, 3, 4 and 6)::`
- Text-after:
  `The ASGI entrypoint, which pairs with one URLconf entry (spec-046 Decisions 2, 3, 4 and 6)::`

- Observation: the own-test-module docstring's transport-ownership
  paragraph says "the router no longer serves GraphQL over HTTP". The
  "after spec-046" pointer already scopes the design era; "no longer"
  adds a then/now contrast the present rule ("serves no GraphQL over
  HTTP") does not need.
- Evidence: module-docstring read; the behavior claim itself is true
  (Mechanics verified the bare-Django HTTP value).
- Impact: trivial temporal residue in the module's framing paragraph.
- Severity: Low.
- Recommendation: state the present rule; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'no longer serves GraphQL' tests/test_routers.py`
  prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py` (module docstring,
  transport-ownership paragraph).
- Grade: process provenance.
- Text-before:
  `Transport ownership after spec-046: the router no longer serves GraphQL over HTTP, so ``HttpCommunicator`` here proves *delegation*`
- Text-after:
  `Transport ownership after spec-046: the router serves no GraphQL over HTTP, so ``HttpCommunicator`` here proves *delegation*`

- Observation: the `_ws_communicator` docstring carries both halves of
  the plan's Routed lead: "now that the HTTP branch no longer carries
  one" and "the branch now carries two independent handshake checks".
  Both behavior claims are true (Mechanics verified the bare-Django
  HTTP value and the Host-outside-Origin checks), but both are phrased
  as then/now contrasts with the pre-046 composition.
- Evidence: docstring read against the `__init__` composition; the
  Mechanics `## Cross-axis (for Comments)` routing note judged these
  wording-only, which this finding implements.
- Impact: temporal residue in the module's one handshake-site
  docstring, read by every row that opens a socket.
- Severity: Low.
- Recommendation: state both present-tense rules; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'now that the HTTP branch no longer' tests/test_routers.py` prints `0` (1 today) and `grep -c 'because the branch now' tests/test_routers.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::_ws_communicator`.
- Grade: process provenance.
- Text-before:
  `session reaches ``AuthMiddlewareStack`` now that the HTTP branch no longer carries one.`
  and
  `because the branch now carries two independent handshake checks (spec-046 Decision 19)`
- Text-after:
  `session reaches ``AuthMiddlewareStack`` - the HTTP branch carries no middleware stack.`
  and
  `because the branch carries two independent handshake checks (spec-046 Decision 19)`

- Observation: the keyword-only-pattern test docstring quotes Decision
  4 as "a single parameter that no longer affects HTTP would be a name
  that lies". The sentence is verbatim - but from the rationale
  companion's Decision 4 section ("Why rename rather than keep one
  shared parameter"), not the Decision text, and its "no longer" is
  the spec's change-contemporary contrast. The test's contract (rename
  without alias, keyword-only) carries fully in present tense, and a
  reworded rationale must drop the quote marks rather than silently
  alter a quotation.
- Evidence: spec-046 Decision 4 text read (no such sentence);
  rationale companion lines 242-243 read (verbatim match); the kept
  `(Decision 4)` pointer preserves attribution.
- Impact: temporal spec language enshrined in a test docstring; the
  next reader parses history to find the pinned rule.
- Severity: Low.
- Recommendation: convert to a present-tense paraphrase without quote
  marks; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'parameter that no longer' tests/test_routers.py`
  prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias`.
- Grade: process provenance.
- Text-before:
  `Decision 4 renames rather than aliases - "a single parameter that no longer affects HTTP would be a name that lies" - and makes the replacement keyword-only.`
- Text-after:
  `Decision 4 renames rather than aliases - a single parameter name spanning a protocol it does not affect would be a name that lies - and makes the replacement keyword-only.`

- Observation: the same test's NAME uses "legacy" for the removed
  parameter spelling
  (`..._with_no_legacy_url_pattern_alias`). Every other "legacy" in
  this module names the `graphql-ws` protocol (kept per the consumers
  ruling); here it labels the pre-rename spelling, where the
  docstring's own vocabulary is "rename" / "alias" and "legacy" adds
  no information `url_pattern` does not already carry.
- Evidence: test-name read; citer census: no standing doc or module
  cites the name (only truncated `...` mentions in per-cycle review
  records, which close with their cycle), so the rename is safe.
- Impact: banned age-label in a test name, inconsistent with the
  docstring it heads.
- Severity: Low.
- Recommendation: rename to the present-tense contract (plain-text
  name below, since the new symbol does not exist yet); Worker-2
  sweeps citers as postcondition.
- Must not change: n/a.
- Proof: `grep -c 'no_legacy_url_pattern_alias' tests/test_routers.py`
  prints `0` (1 today) and `grep -c 'def test_the_websocket_pattern_is_keyword_only_with_no_url_pattern_alias' tests/test_routers.py` prints `1`; the renamed test earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias`.
- Grade: process provenance.
- Text-before:
  `test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias`
- Text-after:
  `test_the_websocket_pattern_is_keyword_only_with_no_url_pattern_alias`

- Observation: the factory-body test docstring paraphrases the avoided
  misdiagnosis as `"your factory has the wrong signature"`. The
  second person addresses the reader-as-consumer; "the factory" loses
  nothing (this is the docstring author's paraphrase, not quoted wire
  text, so the consumers hypothetical exception does not apply).
- Evidence: docstring read; the file's only other second-person hit
  is F16, and the target's two "your" hits are user-facing error
  text, out of scope (see Rejected).
- Impact: trivial voice inconsistency in a contract sentence.
- Severity: Low.
- Recommendation: de-pronominalize; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'your factory has the wrong signature' tests/test_routers.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_factory_that_raises_from_its_body_is_not_normalized`.
- Grade: voice defect (`your` addressing the reader).
- Text-before:
  `"your factory has the wrong signature", which is the wrong diagnosis.`
- Text-after:
  `"the factory has the wrong signature", which is the wrong diagnosis.`

- Observation: the factory-RESULT test docstring opens "Before this
  row the router mounted whatever the factory handed back" and
  continues "The rejection now happens at construction". Both clauses
  narrate the fix; the failure mode (a non-application installed as a
  route callback, failing deep in Channels routing) carries fully as a
  counterfactual present.
- Evidence: docstring read against `_factory_application` (the
  construction rejection it pins is true).
- Impact: change-history framing around an otherwise true contract
  explanation.
- Severity: Low.
- Recommendation: recast as counterfactual-present plus present;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'now happens at construction' tests/test_routers.py`
  prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_factory_returning_a_non_application_fails_at_construction`.
- Grade: process provenance.
- Text-before:
  `Before this row the router mounted whatever the factory handed back, so a ``None`` or a scalar became a URL route callback and the first matching handshake failed deep inside Channels' routing with no mention of the seam. The rejection now happens at construction and names both the factory and the received value, which are the two things a migrant needs.`
- Text-after:
  `Mounting whatever the factory hands back would install ``None`` or a scalar as a URL route callback, failing the first matching handshake deep inside Channels' routing with no mention of the seam. The rejection happens at construction and names both the factory and the received value, which are the two things a migrant needs.`

- Observation: the window-domain test docstring says "the validator
  used to hand it to `math.isfinite` and escape the typed boundary" and
  "Both arms are now inside the boundary". The clauses narrate our own
  superseded behavior (unlike the kept "used to kill" failure modes,
  which describe upstream behavior that is still true underneath the
  guard); the failure mode carries as counterfactual-present.
- Evidence: docstring read; contrasted with the kept upstream-behavior
  clauses (see Rejected).
- Impact: change-history narrative in a domain-pinning docstring.
- Severity: Low.
- Recommendation: recast as counterfactual-present plus present;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Both arms are now inside' tests/test_routers.py`
  prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_the_revalidation_window_rejects_unusable_values`.
- Grade: process provenance.
- Text-before:
  `with no ``float`` image passes every ``isinstance`` check, so the validator used to hand it to ``math.isfinite`` and escape the typed boundary with a raw ``OverflowError``; rendering it into the rejection then raised ``ValueError`` from CPython's 4300-digit integer-to-string guard. Both arms are now inside the boundary, and the negative twin is here because its ``value < 0`` check could never run either.`
- Text-after:
  `with no ``float`` image passes every ``isinstance`` check, so handing it to ``math.isfinite`` escapes the typed boundary with a raw ``OverflowError``, and rendering it into the rejection raises ``ValueError`` from CPython's 4300-digit integer-to-string guard. Both arms are inside the boundary, and the negative twin is here because its ``value < 0`` check could never run either.`

- Observation: the session-mint helper's history is narrated twice:
  `_make_user_and_session` opens "Lifted verbatim out of the
  authenticated-session round trip's local `make_user_and_session_cookie`
  when the revalidation rows needed a fifth copy of it", and the
  round-trip test docstring adds "The mint itself now lives at module
  level, where the revalidation rows share it; the assertions are
  unchanged." Both are pure file history (where the code lived, that a
  refactor changed nothing); neither states a present rule.
- Evidence: both docstrings read whole; the helper's contract (three
  session keys, save, cookie spelling, key returned) is fully stated
  without the history sentence.
- Impact: refactor narrative occupying the first line a revocation-row
  reader meets.
- Severity: Low.
- Recommendation: delete the history (the helper keeps its contract
  sentences; the test keeps its transport and assertion paragraphs);
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Lifted verbatim' tests/test_routers.py` prints `0`
  (1 today) and `grep -c 'now lives at module level' tests/test_routers.py` prints `0` (1 today); both rewritten docstrings earn grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::_make_user_and_session` and
  `tests/test_routers.py::test_authenticated_session_round_trip_reaches_the_resolver`.
- Grade: process provenance.
- Text-before:
  `Lifted verbatim out of the authenticated-session round trip's local ``make_user_and_session_cookie`` when the revalidation rows needed a fifth copy of it: same three session keys, same ``session.save()``, same cookie spelling.`
  and
  `The mint itself now lives at module level (``_make_user_and_session``), where the revalidation rows share it; the assertions are unchanged.`
- Text-after:
  `Three session keys, ``session.save()``, the session-cookie spelling.`
  and
  `(sentence deleted)`

- Observation: the import-boundary test docstring says "the old
  `from .auth.sessions import session_store_class` made the FIRST
  authenticated operation ... import and register the whole opt-in
  GraphQL auth surface" and "The resolver now lives in
  `utils/sessions.py`". Past-behavior plus temporal; the hazard (an
  auth-subsystem import on the event loop to read one settings string)
  carries as counterfactual-present. (Consumers-subject prose this
  module owns; the consumers pass left it unruled.)
- Evidence: docstring read against the eviction-based proof it
  describes (true).
- Impact: change-history narrative in an import-boundary proof
  docstring.
- Severity: Low.
- Recommendation: recast as counterfactual-present plus present;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'resolver now lives in' tests/test_routers.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package`.
- Grade: process provenance.
- Text-before:
  `so the old ``from .auth.sessions import session_store_class`` made the FIRST authenticated operation on ANY socket import and register the whole opt-in GraphQL auth surface on the event loop - to read one settings string. The resolver now lives in ``utils/sessions.py``.`
- Text-after:
  `so resolving the store through ``auth.sessions`` would import and register the whole opt-in GraphQL auth surface on the event loop the first time an authenticated socket ran an operation - to read one settings string. The resolver lives in ``utils/sessions.py``.`

- Observation: the odd-cased-header test docstring opens "Its own row
  rather than a tail on the duplicate-header row, which is where it
  used to live". Where the assertion used to sit in the file is pure
  organization history; the rationale after the colon (two independent
  projection items, one row cannot fail for two reasons) stands alone.
  (Consumers-subject prose this module owns; the consumers pass left
  it unruled.)
- Evidence: docstring read whole.
- Impact: file-history clause heading an otherwise present-tense
  rationale.
- Severity: Low.
- Recommendation: delete the history clause; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'used to live' tests/test_routers.py` prints `0` (1
  today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_an_odd_cased_host_header_still_reaches_the_boundary`.
- Grade: process provenance.
- Text-before:
  `Its own row rather than a tail on the duplicate-header row, which is where it used to live: casing normalization and duplicate reduction are two independent projection items, and one row cannot fail for two reasons and still say which.`
- Text-after:
  `Its own row rather than a tail on the duplicate-header row: casing normalization and duplicate reduction are two independent projection items, and one row cannot fail for two reasons and still say which.`

- Observation: the running-subscription test docstring opens "Before
  the outbound checkpoint existed this row's `frames` would carry
  result 2" and closes the paragraph with "`Subscription.tick` ...
  could not detect it". The "Before X existed" frame is change
  history; the load-bearing content (upstream's result loop never
  returns through admission) is present-tense and still true, and
  `tick` still cannot detect it. (Consumers-subject prose this module
  owns; the consumers pass left it unruled.)
- Evidence: docstring read; upstream loop behavior corroborated by the
  paragraph's own present-tense sentence.
- Impact: history framing plus a past-tense modal for a present
  property.
- Severity: Low.
- Recommendation: drop the frame, fix the modal; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Before the outbound checkpoint existed' tests/test_routers.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_running_subscription_cannot_emit_a_result_after_revocation`.
- Grade: process provenance.
- Text-before:
  `Before the outbound checkpoint existed this row's ``frames`` would carry result 2 - upstream's ``run_operation`` / ``handle_async_results`` loop sends every later result without returning through the admission method, which is why ``Subscription.tick`` (one yield, then completion) could not detect it.`
- Text-after:
  `Without the outbound checkpoint this row's ``frames`` would carry result 2: upstream's ``run_operation`` / ``handle_async_results`` loop sends every later result without returning through the admission method, which is why ``Subscription.tick`` (one yield, then completion) cannot detect it.`

- Observation: the non-dispatchable-frame test docstring's second
  sentence opens "Now each is refused with the invalid-message close".
  The opening "used to kill" sentence stays (guarded failure mode,
  still true of upstream underneath the guard - see Rejected); only
  the "Now" is gratuitous history-contrast. (Consumers-subject prose
  this module owns; the consumers pass left it unruled.)
- Evidence: docstring read; contrasted with the kept failure-mode
  clause in the same paragraph.
- Impact: trivial temporal residue.
- Severity: Low.
- Recommendation: drop the temporal; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Now each is refused' tests/test_routers.py` prints
  `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_non_dispatchable_frame_is_refused_and_the_connection_ends`.
- Grade: process provenance.
- Text-before:
  `leaving the socket open with nothing reading it. Now each is refused with the invalid-message close`
- Text-after:
  `leaving the socket open with nothing reading it. Each is refused with the invalid-message close`

- Observation: the missing-payload test docstring opens "Before the
  containment the two protocols disagreed here" (past-tense natives)
  and closes "The refusal is now the same shape on both". The native
  behaviors are still true today (upstream unchanged; the containment
  wraps them), so both halves carry in present tense. (Consumers-subject
  prose this module owns; the consumers pass left it unruled.)
- Evidence: docstring read against the per-protocol containment rows
  (transport-ws `except KeyError` still upstream's; legacy loop still
  unguarded underneath).
- Impact: history framing for behaviors that are present facts.
- Severity: Low.
- Recommendation: recast both halves present-tense; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'now the same shape on both' tests/test_routers.py`
  prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_missing_payload_is_refused_per_protocol`.
- Grade: process provenance.
- Text-before:
  `Before the containment the two protocols disagreed here: transport-ws's own ``except KeyError`` turned a missing payload into its 4400 refusal, while the legacy loop crashed with a raw ``KeyError('payload')`` and went silent. The refusal is now the same shape on both.`
- Text-after:
  `The two protocols' native behaviors disagree here: transport-ws's own ``except KeyError`` turns a missing payload into its 4400 refusal, while the legacy loop would crash with a raw ``KeyError('payload')`` and go silent. The refusal is the same shape on both.`

- Observation: the unmaskable-frame test docstring opens "The seam now
  covers `schema.stream`". The "now" contrasts the pre-`stream`
  seam; the coverage sentence is complete without it. (Consumers-subject
  prose this module owns; the consumers pass left it unruled.)
- Evidence: docstring read; no runtime-sequence reading available.
- Impact: trivial temporal residue.
- Severity: Low.
- Recommendation: drop the temporal; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'seam now covers' tests/test_routers.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_a_streamed_value_the_policy_cannot_mask_reaches_the_transport_unchanged`.
- Grade: process provenance.
- Text-before:
  `The seam now covers ``schema.stream``, which yields more shapes than a subscription's events`
- Text-after:
  `The seam covers ``schema.stream``, which yields more shapes than a subscription's events`

- Observation: the request-contract section comment quotes Decision 2
  as "the Channels request adapter is now a WebSocket-only shape".
  The spec sentence has no "now" ("is a WebSocket-only shape in the
  package's own composition", spec-046 line 973): the quotation adds a
  temporal the source does not contain.
- Evidence: spec-046 lines 960-985 read; the quoted sentence compared
  word for word.
- Impact: a misquotation, however small, in a spec pointer whose
  value is fidelity.
- Severity: Low.
- Recommendation: quote the spec sentence faithfully; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'adapter is now a WebSocket-only' tests/test_routers.py` prints `0` (1 today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py` (request-contract section comment).
- Grade: stale (misquotation).
- Text-before:
  `(spec-046 Decision 2 - "the Channels request adapter is now a WebSocket-only shape")`
- Text-after:
  `(spec-046 Decision 2 - "the Channels request adapter is a WebSocket-only shape in the package's own composition")`

- Observation: the control-frame test carries the comment "The
  acknowledgement is already behind us". First-person plural in a
  comment; "already past" states the same sequence without it.
- Evidence: comment read in situ (the `_open_ws` acknowledgement is
  behind the test in scenario order).
- Impact: trivial voice inconsistency; the file's only `us` hit.
- Severity: Low.
- Recommendation: drop the pronoun; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'behind us' tests/test_routers.py` prints `0` (1
  today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::test_connection_control_frames_never_reach_the_outbound_checkpoint`
  (inline comment).
- Grade: voice defect (first-person `us` in a comment).
- Text-before:
  `The acknowledgement is already behind us (``_open_ws`` asserts it) and it cost nothing: no operation has run yet.`
- Text-after:
  `The acknowledgement is already past (``_open_ws`` asserts it) and it cost nothing: no operation has run yet.`

- Observation: nineteen helper, resolver, and probe-method docstrings
  open nominal ("The ...", "A ...", "An ...", "One ...", "Every ...",
  "Whether ...") where the axis mood rule requires imperative for a
  function or method (ruff leaves mood unchecked, so this review is
  the gate; the consumers pass enforced the same rule on a method
  twin). Each site is listed with its before/after below; test
  *functions* are unaffected (their rule is behavior statements, and
  all state behavior).
- Evidence: AST first-line census over all 200 docstrings in the
  module (every function/method/class first line enumerated in
  Trace's scratch JSON); each site read in place.
- Impact: systematic mood inconsistency across the module's helper
  layer.
- Severity: Low.
- Recommendation: recast each first line imperative, keeping every
  contract clause; see text-after list.
- Must not change: n/a.
- Proof: `grep -c -e '"""A well-formed GraphQL POST envelope' \
  -e '"""The ..asyncio' -e '"""The single WS route' \
  -e '"""The ASGI application a CORRECT factory' -e '"""The two ASGI keys' \
  -e '"""Django'"'"'s Host verdict' -e '"""An ASGI app that RECORDS' \
  -e '"""The source text of upstream'"'"'s two WebSocket' \
  -e '"""The result-source names' -e '"""The two generated handler classes' \
  -e '"""Whether the configured engine' -e '"""Whether ANYONE holds' \
  -e '"""The authenticated-session probe' -e '"""The revalidation-freshness probe' \
  -e '"""A query whose RESPONSE is held' -e '"""One value, then completion\.' \
  -e '"""An unbounded subscription whose every result' \
  -e '"""A subscription whose every later result is ALREADY available' \
  -e '"""Every message committed AFTER the' tests/test_routers.py` prints `0` (19 today; each anchor verified to match exactly its site); every rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::_graphql_post`,
  `tests/test_routers.py::_actor_lease`,
  `tests/test_routers.py::_mounted_ws_callback`,
  `tests/test_routers.py::_valid_asgi_application`,
  `tests/test_routers.py::_handshake_scope`,
  `tests/test_routers.py::_django_asgi_host_verdict`,
  `tests/test_routers.py::_recording_websocket_application`,
  `tests/test_routers.py::_upstream_handler_sources`,
  `tests/test_routers.py::_wrapped_schema_reads`,
  `tests/test_routers.py::_revalidating_handler_classes`,
  `tests/test_routers.py::_session_row_still_exists`,
  `tests/test_routers.py::_actor_lease_held`,
  `tests/test_routers.py::Query.username`,
  `tests/test_routers.py::Query.actor_identity`,
  `tests/test_routers.py::Query.controlled_ping`,
  `tests/test_routers.py::Subscription.tick`,
  `tests/test_routers.py::Subscription.controlled`,
  `tests/test_routers.py::Subscription.burst`,
  `tests/test_routers.py::_TransportLog.after_the_revocation_close`.
- Grade: duplicates the code (mood defect; nominal or `Whether` first
  line on a function or method, which the rule requires as
  imperative).
- Text-before / text-after, per site in Symbol order:
  `A well-formed GraphQL POST envelope aimed at ``/graphql`` over HTTP.` /
  `Build a well-formed GraphQL POST envelope aimed at ``/graphql`` over HTTP.`
  `The ``asyncio.Lock`` object serving as this connection's actor lease.` /
  `Return the ``asyncio.Lock`` object serving as this connection's actor lease.`
  `The single WS route's callback, after asserting all three wrappers are in place.` /
  `Return the single WS route's callback, after asserting all three wrappers are in place.`
  `The ASGI application a CORRECT factory returns: an async callable.` /
  `Provide the ASGI application a CORRECT factory returns: an async callable.`
  `The two ASGI keys the Host projection reads, plus what ``ASGIRequest`` demands.` /
  `Build the two ASGI keys the Host projection reads, plus what ``ASGIRequest`` demands.`
  `Django's Host verdict for a handshake, with Django supplying the projection too.` /
  `Return Django's Host verdict for a handshake, with Django supplying the projection too.`
  `An ASGI app that RECORDS being reached, then accepts the socket.` /
  `Build an ASGI app that RECORDS being reached, then accepts the socket.`
  `The source text of upstream's two WebSocket protocol handler modules.` /
  `Return the source text of upstream's two WebSocket protocol handler modules.`
  `The result-source names ``_StopAwareSchema`` actually overrides.` /
  `Return the result-source names ``_StopAwareSchema`` actually overrides.`
  `The two generated handler classes off the mounted consumer class.` /
  `Return the two generated handler classes off the mounted consumer class.`
  `Whether the configured engine still holds a record for ``session_key``.` /
  `Return whether the configured engine still holds a record for ``session_key``.`
  `Whether ANYONE holds this connection's shared actor lease.` /
  `Return whether ANYONE holds this connection's shared actor lease.`
  `The authenticated-session probe: the session actor's username.` /
  `Return the session actor's username for the authenticated-session probe.`
  `The revalidation-freshness probe (spec-046 row 26): two identity reads.` /
  `Probe revalidation freshness (spec-046 row 26) with two identity reads.`
  `A query whose RESPONSE is held until the test body releases it.` /
  `Hold this query's RESPONSE until the test body releases it.`
  `One value, then completion.` /
  `Emit one value, then complete.`
  `An unbounded subscription whose every result is released by the test.` /
  `Emit an unbounded stream with every result released by the test.`
  `A subscription whose every later result is ALREADY available.` /
  `Yield every later result with no suspension between them: all ALREADY available.`
  `Every message committed AFTER the ``4403``; fails if there was no close.` /
  `Return every message committed AFTER the ``4403``; fail loudly if there was no close.`

- Observation: three helper-class docstrings open imperative ("Own
  ...", "Hold ...", "Count ...") where the rule requires a
  description for a class (same gate as above; the consumers pass
  enforced it on the Host validator class).
- Evidence: AST first-line census (every class first line
  enumerated); each site read in place.
- Impact: minor mood inconsistency on three helper classes.
- Severity: Low.
- Recommendation: recast each first line as a description; see
  text-after list.
- Must not change: n/a.
- Proof: `grep -c -e '"""Own one in-flight' -e '"""Hold every operation on its schema' -e '"""Count the revalidation'"'"'s session reads' tests/test_routers.py` prints `0` (3 today; each anchor verified to match exactly its site); every rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_routers.py::_OperationController`,
  `tests/test_routers.py::_GatedOperationExtension`,
  `tests/test_routers.py::_RevalidationProbe`.
- Grade: duplicates the code (mood defect; imperative first line on a
  class, which the rule requires as a description).
- Text-before / text-after, per site in Symbol order:
  `Own one in-flight operation's timeline from the test body.` /
  `One in-flight operation's timeline, owned from the test body.`
  `Hold every operation on its schema between admission and its first frame.` /
  `A schema extension holding every operation between admission and its first frame.`
  `Count the revalidation's session reads, and optionally hold or poison one.` /
  `The revalidation's session-read count, with an optional hold or poison.`

- Observation: prose in another test module about this target's
  symbol: `tests/auth/test_mutations.py::_channels_router` opens
  "Through `0.0.14` this borrowed the package's
  `DjangoGraphQLProtocolRouter`, whose HTTP branch was exactly the
  composition below", then "the router no longer serves GraphQL over
  HTTP". The behavior claims are true (the router serves no GraphQL
  over HTTP since spec-046 Decision 2), but the first sentence is
  pure file history and "no longer" is temporal.
- Evidence: docstring read whole against the target's HTTP
  delegation (bare-Django `"http"` value, verified by Mechanics).
- Impact: version-dated harness history heading another suite's
  transport docstring.
- Severity: Low.
- Recommendation: delete the history sentence, state the present
  rule with the kept spec pointer; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'this borrowed' tests/auth/test_mutations.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py::_channels_router`.
- Grade: process provenance.
- Text-before:
  `Through ``0.0.14`` this borrowed the package's ``DjangoGraphQLProtocolRouter``, whose HTTP branch was exactly the composition below. spec-046 Decision 2 gave HTTP to the consumer's own Django ASGI application, so the router no longer serves GraphQL over HTTP and cannot be the harness for a Channels-HTTP auth round trip.`
- Text-after:
  `The package's ``DjangoGraphQLProtocolRouter`` serves no GraphQL over HTTP (spec-046 Decision 2 gave HTTP to the consumer's own Django ASGI application), so it cannot be the harness for a Channels-HTTP auth round trip.`

## Rejected

- Bare `(spec-041)` twice in the target (the `__all__` comment, the
  broken-hint comment): repo-wide convention, not a defect - some
  fifty bare `(spec-NNN)` pointers stand across the package, and
  spec-041's Decisions are named repeatedly on the reader's path
  through this file. Trigger: a second spec gaining bare pointers in
  this module without its Decisions on the path.
- `now` / `previously` as runtime or scenario sequence, each kept:
  target "compile the string now" (construction-time); tests "the
  payload it now holds" (revocation state), "anonymous now but was
  not always" (scope state), "which is now the FIRST protected
  checkpoint" (scenario order), the ` upstream now type-tests`
  assertion message (the detected hypothetical). Trigger: none.
- "can no longer put `next` / `data`" (test module docstring,
  outbound-checkpoint bullet): revocation-state mechanics ("after
  revocation, an admitted operation cannot emit"), phrased as a
  present-tense rule, same class as the three wordings the consumers
  record kept ("no longer matches", "previously authorized", "no
  longer exists" - all deferred to here). Trigger: none.
- "used to kill the message-loop task" twice (non-dispatchable-frame
  and legacy-`stop` rows): each states the guarded failure mode of
  upstream dispatch that is still true underneath the containment,
  corroborated by the rows' own `TypeError` / `KeyError` probes -
  the kept class from the consumers record ("that escape used to
  kill the message loop"). Only the adjacent "Now"/"Before" framings
  are filed (F12, F13). Trigger: upstream containing either shape
  itself.
- `legacy` as the `graphql-ws` protocol's own name throughout both
  files (constants, parameters, test names, docstrings): kept per the
  consumers 19-hit ruling; only the age-label use in the
  keyword-only test name is filed (F4). Trigger: none.
- "moved from `subscribe` + `execute` to `stream`" (stop-aware
  partition row): deferred to the consumers rejection (upstream
  history load-bearing to the assertion, wheel-corroborated).
  Trigger: none.
- "pre-hook" jargon in `tests/test_routers.py`: deferred to the
  consumers rejection (descriptive, no `::` citation to rot).
  Trigger: none.
- The two landed docstrings the consumers item rewrote in this
  module (subscribe-before-init, legacy revalidation): grade true as
  they stand (de-pronominalized, present-tense, behavior claims
  verified); not re-filed. Trigger: a body change falsifying either
  claim.
- `your` inside the target's `_MISSING_DJANGO_APPLICATION_HINT`
  string ("from your asgi.py", "from your URLconf"): user-facing
  error text addressing the migrating consumer, not a docstring or
  comment; the axis grades prose, and conventional reader address in
  an actionable hint is not a voice defect. Trigger: none.
- `DjangoGraphQLProtocolRouter.__init__` without its own docstring:
  every parameter is documented on the class docstring (required
  application, pattern, seam, window), which is where the reader
  lands. Trigger: a parameter gaining behavior the class docstring
  does not state.
- Property first lines left nominal
  (`_TransportLog.frame_types`): a property documents its value like
  an attribute, so description mood is appropriate. Trigger: the
  project adopting imperative-property convention.
- Undocumented test-local scaffolding (the `Query` / `Subscription`
  schema shells, `Mutation`, handler/consumer doubles, `Injected` /
  `Extended` subclasses, `_Unintrospectable`, `_BrokenSignature`,
  `_route_patterns`, `_package_logger_records`, `_window_router`,
  `_ch_post`): unreachable single-use doubles and self-evident
  one-liners whose contracts live in the docstrings that use them.
  Trigger: any of them becoming importable or asserted on directly.
- `consumers.py` module docstring "built by
  `routers.py::_build_router_class`": loose (materialization happens
  in `_build_router_class_uncached` on first call) but not false -
  the cited accessor is what builds-and-caches, and the load-bearing
  substance (same guard, same `_ROUTER_CLASS` cache, lifetime
  exactly the router class's, nothing cached in `consumers.py`) is
  true. No route. Trigger: the builder splitting cache from
  materialization.
- "The HTTP half needs none of it" network: `views.py` module
  docstring on `routers.py` (URLconf independence,
  `require_channels`-guarded soft dependency, leaf-module list),
  `utils/imports.py::require_optional_module` docstring (singular
  illustrative guard cite), `auth/sessions.py` hint comment plus
  error-string directions, and the `tests/auth/test_sessions.py`
  error-string assertion plus
  `tests/mutations/test_write_transaction.py::_no_http_application`
  docstring: all read, all true of the live bodies. Trigger: a body
  change falsifying any of them.
- "The single WS route's callback" (`_mounted_ws_callback` first
  line): "single" here counts the route list (one `re_path`, asserted
  by `_route_patterns` in the same helper), not the install-hint
  census of T1; only its nominal mood is filed (M-methods). Trigger:
  a second route joining the mount.
- "The factory half of that seam, spelled once and shared by BOTH of
  its construction-time rejections": verified true (both raise sites
  interpolate `_FACTORY_CONTRACT_HINT`). Trigger: a third factory
  rejection site.
- "The `require_drf()` contract generalized" (`require_channels`
  docstring): the DRF guard (spec-039) predates this one and both are
  thin wrappers over the shared primitive, so the direction reads
  true, if compressed. Trigger: the primitive gaining a shape one
  wrapper cannot express.
- "Pre-binding ... accepts exactly what the call accepts"
  (`_factory_application` docstring): true of `bind` versus the call
  for introspectable factories, with the un-introspectable
  pass-through stated in the next sentence. Trigger: none.
- "neither dispatches into consumer code" (`callable` plus the
  truthful coroutine check): true (`callable` reads the type slot;
  `truth.is_instance` reads the real class). Trigger: none.
- "The router never calls `get_asgi_application()` itself": true (no
  such call in the module; the name appears only in the hint string
  and this docstring). Trigger: a call site appearing.
- "rungs 1-3" shorthand in every test docstring tail: the standing
  test-tier ladder vocabulary (the three stronger tiers cannot
  observe this router), true in each use, not review-process residue.
  Trigger: fakeshop gaining an ASGI mount.
- "migrant" for the 0.0.14-migration reader (target hint comment,
  `__init__` guard comment, F6's kept tail): input-role
  characterization matching the hint's own versioned migration text,
  not change-process narrative. Trigger: the hint dropping its
  version.
- "The class test comes first on purpose" / "four-branch selector" /
  "`GraphQLWSConsumer` is only in scope inside that builder"
  (`_websocket_application` docstring): all true of the live body
  (None / subclass / factory / raise; function-local upstream
  import). Trigger: a fifth seam shape.
- Routed (owner: the `rest_framework` item's Comments pass;
  confirming the Mechanics cross-item route, not duplicating its
  evidence): `django_strawberry_framework/rest_framework/__init__.py::require_drf`
  says "the three soft-dependency guards are identical thin wrappers"
  while four named wrappers over `require_optional_module` exist
  (`routers.require_channels`, `auth.sessions.require_channels`,
  `require_drf`, `middleware.debug_toolbar.require_debug_toolbar`,
  plus `keyset.py`'s two direct call sites which are not named
  guards). Pre-existing phrasing; whether the count means names or
  sites is for that pass to judge.
- Routed (owner: the `utils/imports` item's Comments pass):
  `tests/utils/test_imports.py` module docstring "(``routers.py::require_channels()``
  / ``rest_framework::require_drf()``)" names two of the four wrappers;
  written 2026-07-08, rotted when the auth (2026-07-21) and
  debug-toolbar guards landed. The sentence is about
  `require_optional_module`'s clientele (that item's symbol; the
  routers half of it is true), so it belongs to the pass grading that
  module whole.

Handoff: Comments review is closed with 2 Medium and 24 Low findings
and 2 Routed leads. The judgment calls a verifier could revisit are
the F3 quotation (faithful to the rationale companion, filed only for
tense: the alternative is keeping a verbatim spec quote), the F15
misquotation (one added word, filed as stale), the kept-vs-filed
"used to" split (upstream behavior still true underneath the guard
stays; our superseded behavior and file organization go), and the
22-site mood batch (explicit gate plus twin precedents, but the
largest single block). Everything else was discharged by first-hand
reads: every docstring and comment in both graded files, every
package and test mention of the target's symbols, all four spec
pinpoints resolved, both module first lines passing
`--list-docstrings`, all 17 citations resolving, no `Tests
that`/`Ensures`, no line-number cites. The target and own tests are
byte-identical to ITEM_BASELINE, so no concurrent-work
reconciliation was needed. No defects; no cross-axis text placed or
owed; the Mechanics routing note is implemented here as F2/F3/F5.
Cells unverified: none (all three inapplicable by construction).

## Verify comments

Pass 1, 2026-09-29. Fully static (no workspace copy bound). Item diff
vs ITEM_BASELINE touches `django_strawberry_framework/routers.py` only
(23+/17-, live `299da0f5`); both deferred files byte-identical to
ITEM_BASELINE. Code-digest identity
`sha256:38c32db58e89f01bad17c719bdea9fac43bf9f1e986406e590eef031bd28c65c`
both sides, exit 0: the pass is prose-only. Scratch:
`docs/review/temp-tests/routers/verify-comments-1/` (fingerprints only;
all commands ran in the shared tree and are re-runnable verbatim).

Implemented findings (7), each Proof re-run live plus a grade of the
landed sentence against its body:

- T1 Medium, 3-site "the single" census: PASS. `grep -c -i 'the
  single' django_strawberry_framework/routers.py` prints `0` (3 at
  baseline). Landed: `_CHANNELS_INSTALL_HINT` comment "This module's
  single channels-ABSENT install hint (spec-041 Decision 5). The auth
  transport carries its own feature-keyed twin
  (``auth/sessions.py``)."; `require_channels` "passing this module's
  ``_CHANNELS_INSTALL_HINT`` string"; `_build_router_class_uncached`
  "every true-absence path of this builder routes through its single
  install hint". Grade true: the live twin exists
  (`auth/sessions.py:67` "The single channels-ABSENT install hint for
  the auth transport" plus a second `require_channels` at :110; two
  `def require_channels` in the package, routers:203 and
  auth/sessions:110), so each scoped claim plus the one twin pointer
  is exactly the Mechanics R1 shape.
- T2 Medium, "through 6.0" ceiling: PASS. `grep -c 'through 6\.0'
  django_strawberry_framework/routers.py` prints `0` (1 at baseline).
  Landed "through 6.1". Grade true: `pyproject.toml` advertises
  `Framework :: Django` 5.2, 6.0, 6.1; the floor row is
  `channels[daphne]>=4.3.2`; the live interpreter pairs
  channels 4.3.2 with Django 6.1.
- L1 Low, module docstring "half of the card": PASS. `grep -c 'half of
  the card' django_strawberry_framework/routers.py` prints `0` (1 at
  baseline). Landed "The HTTP half needs none of it: ``views.py`` is
  channels-free, ..." - complete without the board residue. Module
  first line byte-identical to baseline, so no TREE.md render owed.
- L2 Low, `_MISSING_DJANGO_APPLICATION_HINT` "no longer one line":
  PASS. `grep -c 'no longer one line'
  django_strawberry_framework/routers.py` prints `0` (1 at baseline).
  Landed "... (the asgi.py argument AND the URLconf entry)." -
  complete, temporal gone, versioned migration prose stays in the
  hint string where it belongs.
- L3 Low, `_validated_websocket_url_pattern` "never matches": PASS.
  `grep -c 'route that never matches'
  django_strawberry_framework/routers.py` prints `0` (1 at baseline).
  Landed "... silently install a route matching the stringified value
  instead of the intended pattern ...". Grade true: installed Django
  6.1 `RegexPattern` stores `_regex` verbatim and
  `LocaleRegexDescriptor.__get__` compiles `str(pattern)` lazily for
  non-`str`; `str(7)` is `"7"`, which matches path `"7"` (True) and
  not `"other"` (False).
- L4 Low, `_factory_application` "falsely reject legitimate": PASS.
  `grep -c 'falsely reject legitimate'
  django_strawberry_framework/routers.py` prints `0` (1 at baseline).
  Landed restatement ("``bind`` accepts ``*args`` shapes and
  ``functools.partial`` mounts exactly as the call does, so the check
  would only fire on wrong-arity callables ... while an
  un-introspectable result ... would force the same pass-through ...").
  Grade true: stdlib probe binds a 3-arg function, a `(*args)`
  function, a `functools.partial` of the first, and a
  `(*args)`-`__call__` instance (all BIND); a C-slot object is
  un-introspectable (`ValueError` on this interpreter, inside the
  module's `(TypeError, ValueError)` pass-through pair); a
  `**kwargs`-only shape rejects the positional bind, correctly (the
  call would fail too).
- L5 Low, `DjangoGraphQLProtocolRouter` "which now pairs": PASS.
  `grep -c 'which now pairs'
  django_strawberry_framework/routers.py` prints `0` (1 at baseline).
  Landed "The ASGI entrypoint, which pairs with one URLconf entry
  (spec-046 Decisions 2, 3, 4 and 6)" - temporal gone, Decision
  pointer kept.

Deferred findings (19 test-file Lows): PASS, all correctly untouched.
`tests/test_routers.py` `f513d869c78247d103a2e52d32b053d98ddc1f0d` and
`tests/auth/test_mutations.py`
`ff8a261d09ca63a0f606673bf11b9262f2bb1f35` both byte-identical to
ITEM_BASELINE; `git diff <ITEM_BASELINE> --` over the three item paths
names only `routers.py`. Every deferred Proof still prints its
baseline count (18 single-site counts print `1`, the 19-helper mood
census prints `19`, the 3-class mood census prints `3`, the renamed
test symbol prints `0`, `this borrowed` in `test_mutations.py` prints
`1`) - the ride rule holds: no higher finding touches either file.

Cross-checks:

- `check_citations.py --paths
  django_strawberry_framework/routers.py --substrings --json`: `OK:
  7 citations resolve`, 0 violations, 0 warnings (same 7 as the
  review census).
- Provenance sweep over added lines: the only `spec-` hits are the two
  kept Decision pointers (`spec-041 Decision 5`, `spec-046 Decisions
  2, 3, 4 and 6`), both pre-existing in the text-before; no `card` /
  `round` / `worker` / `legacy` / `moved from` / `no longer` /
  `previously` / `now` / `fix for` / `Tests that` / `Ensures` /
  voice-pronoun / line-number cite introduced. Full-file `no longer |
  previously | moved from | fix for`: no hits.
- Handoffs obeyed: Performance R1/R5 judgments untouched (no code
  moved, no per-request caller added, no bench figure moves);
  Mechanics R5/inner-lock untouched and the routed-OUT `require_drf`
  "three soft-dependency guards" wording intact
  (`rest_framework/__init__.py` `45cf7b63`, empty diff vs
  ITEM_BASELINE, for that pending item); Comments F3/F15/mood-batch
  judgment calls all sit in the deferred files and stand as filed.
- `ruff check` + `ruff format --check` on `routers.py`: clean.

No new defects found. The whole landed docstring of each changed line
grades true; no touched symbol was made false.

Status: verified
