# Review · Comments: `django_strawberry_framework/relay.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=04fd0769352ba604a1db2942738f8dab9f630b18

## Trace

Read the whole live target (634 lines: module docstring, 15 docstrings, 2 member
comments, 1 ledger comment, 14 inline comments) and its own test module
`tests/test_relay_node_field.py` whole (877 lines: module docstring, 30
docstrings, section banners, inline comments). Sibling axis records
(`rev-relay.performance.md`, `rev-relay.mechanics.md`) did not exist at read
time. Traced every behavioral prose claim to its body plus one real caller:
`django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`
(guard census),
`django_strawberry_framework/utils/directives.py::validated_field_directives`
(gate mechanics),
`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`
(coercion mechanics),
`django_strawberry_framework/types/relay.py::install_is_type_of` (stamp honor),
`django_strawberry_framework/types/finalizer.py` ledger check (message +
rationale),
`django_strawberry_framework/mutations/resolvers.py::coerce_lookup_id` and
`django_strawberry_framework/utils/write_values.py::type_check_relation_id`
(decode consumers, `using` threading), the installed Strawberry 0.324.0 /
graphql-core sources for the quoted `Any`-annotation `TypeError`, and
spec-031 Decision 11, spec-032 Decisions 3/4/5/8/11 plus Edge cases, spec-047
Decision 9 for every spec pointer. Graded the plan-routed
`tests/test_relay_connection.py` wordings in place, plus the prose other test
modules hold about the target's symbols (live-tier node rows in
`test_library_api.py`, bound rows in `test_resource_policy_api.py`, the
mutation/serializer `decode_model_global_id` prose, `test_products_api.py`
precedent comment), and swept the other-package-module prose census naming the
target's symbols (13 files) for staleness. `git log -S` archaeology decoded
the `P1` / `P2` / `S2` ordinals. Instruments, all static in the shared tree:
`review_inspect.py` (`docs/review/temp-tests/relay/comments/relay.json` +
`inspect/`), `build_tree_md.py --list-docstrings` (`ok` on both graded
files), `check_citations.py --paths ... --substrings` (6 target cites + 1
test cite, 0 violations), the REVIEW.md provenance `rg`. No workspace runs;
default / sharded / pg cells are inapplicable by construction (prose-only
review; nothing imports the package or opens a database).

Fingerprints (`git hash-object`): `django_strawberry_framework/relay.py`
`e75e2b66`, `tests/test_relay_node_field.py` `af4866a1`,
`tests/test_relay_connection.py` `fe2b2d24`. A finding's Freshness lists only
files beyond these.

## Findings

### High

None.

### Medium

None.

### Low

- Observation: the two deadline comments in
  `django_strawberry_framework/relay.py::DjangoNodeField` (line 481) and
  `django_strawberry_framework/relay.py::DjangoNodesField` (line 565) carry
  bare `(spec-047)` parentheticals, the bare form REVIEW.md names provenance.
- Evidence: spec-047 `### Decision 9 — The execution deadline is cooperative,
  and says so` enumerates `relay.py::DjangoNodeField / DjangoNodesField —
  before the decode` as a seam, in the comments' own words
  (`which is the step that makes a visibility-scoped query inevitable (after
  the empty-ids short circuit ...)`). Same verified upgrade the connection
  item's L5 applied to its identical deadline comment.
- Impact: bounded; kept Decision pointers replace bare spec tags.
- Severity: Low.
- Recommendation: attach each pointer to its Decision; see text-after.
- Must not change: n/a.
- Proof: `grep -c '(spec-047)' django_strawberry_framework/relay.py` prints
  `0` (2 today); both rewritten comments earn grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/relay.py::DjangoNodeField`,
  `django_strawberry_framework/relay.py::DjangoNodesField`.
- Grade: process provenance (bare spec tags; exact upgrade verified).
- Text-before:
  `# The cooperative deadline (spec-047) before the decode: a refetch is a`
  and
  `# The cooperative deadline (spec-047), after the empty-list short`.
- Text-after:
  `# The cooperative deadline (spec-047 Decision 9) before the decode: a refetch is a`
  and
  `# The cooperative deadline (spec-047 Decision 9), after the empty-list short`.

- Observation: the empty-batch comment in
  `django_strawberry_framework/relay.py::DjangoNodesField` (line 563) says
  `(spec Edge cases)` — bare `spec` vocabulary with no number and no rule
  named, where the spec states the exact rule.
- Evidence: spec-032 Edge cases `- **`nodes(ids: [])`** — returns `[]`
  without touching the database, and without checking the execution
  deadline`. The comment's claim is true; only the pointer is vague (the
  connection item's L4 shape).
- Impact: bounded; vague pointer where exact spec vocabulary exists.
- Severity: Low.
- Recommendation: attach the pointer to the spec and its rule; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c '(spec Edge cases)' django_strawberry_framework/relay.py`
  prints `0` (1 today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/relay.py::DjangoNodesField`.
- Grade: process provenance (vague bare-spec vocabulary).
- Text-before:
  `# Zero database access (spec Edge cases).`
- Text-after:
  `# Zero database access (spec-032 Edge cases, the nodes(ids: []) rule).`

- Observation: the own-test module docstring
  (`tests/test_relay_node_field.py` lines 3-5) calls the layout `the
  card-named two-file split` — board residue: it attributes the naming to a
  card, a process artifact.
- Evidence: read verbatim; the kept spec pointer beside it (spec-032
  Decision 11) already anchors the split. AGENTS.md bans card mentions in
  standing prose (the connection item's L1 shape).
- Impact: bounded; one module-docstring clause (renders into `docs/TREE.md`
  rows, so re-render if the first line moves — it does not here).
- Severity: Low.
- Recommendation: drop the attribution, keep the pointer; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'card-named' tests/test_relay_node_field.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_relay_node_field.py` module docstring.
- Grade: process provenance (board residue).
- Text-before:
  `Mirrors the top-level ``django_strawberry_framework/relay.py`` (the card-named`
  `two-file split over a strict ``docs/TREE.md`` mirror -`
- Text-after:
  `Mirrors the top-level ``django_strawberry_framework/relay.py`` (the two-file`
  `split over a strict ``docs/TREE.md`` mirror -`

- Observation:
  `tests/test_relay_node_field.py::test_bare_nodes_field_multi_type_model_typenames_follow_gids`
  (line 179) is `Batch sibling of the S2 regression` — `S2` is a stranded
  review-round ordinal no reader can decode.
- Evidence: `git log -S"S2 regression"` lands on `1f16d963`, whose hunks
  spell it `Round-4 S2 multi-type shape` / `Round-4 review S2`: a review
  finding id. Prior passes already retired its three siblings (`Round-4
  S2` in the helper and single-node docstrings, `Round-4 minor` in the
  generator docstring); this is the last survivor. The sentence's
  behavioral half (per-position `__typename` routing) is true and stays.
- Impact: bounded; one test first line.
- Severity: Low.
- Recommendation: name the regression, not the round; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'S2 regression' tests/test_relay_node_field.py` prints
  `0` (1 today); the rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol:
  `tests/test_relay_node_field.py::test_bare_nodes_field_multi_type_model_typenames_follow_gids`.
- Grade: process provenance (review-round ordinal).
- Text-before:
  `"""Batch sibling of the S2 regression: per-position ``__typename`` routing."""`
- Text-after:
  `"""Batch sibling of the single-node multi-type regression: per-position ``__typename`` routing."""`

- Observation:
  `tests/test_relay_node_field.py::test_node_custom_node_id_attr_resolves`
  (line 345) ends a behavioral sentence with `(the P2 bug)` — a stranded
  review ordinal: spec-032 carries the label 0 times and its rationale
  companion 47, and neither obvious candidate matches (Revision 7 P2 is
  the uncoercible-pk leak / SyncMisuseError discrimination, not
  coerce-against-`resolve_id_attr()`).
- Evidence: `git log -S"the P2 bug"` lands on `3e247237` (`fix: complete
  spec-032 full relay implementation`, `post-build code review`); the
  ordinal is that review's P2. KANBAN `TODO-ALPHA-056-0.0.17` catalogues
  this plus F6 as its whole spec-032 stranded-ordinal population with a
  per-spec retirement rule — both sites live in this one file, so both
  findings together are that card's complete spec-032 half. The
  sentence's behavioral claim is true and stays.
- Impact: bounded; one parenthetical (Worker-0: retiring F5+F6 together
  discharges that card's spec-032 row).
- Severity: Low.
- Recommendation: delete the parenthetical; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'the P2 bug' tests/test_relay_node_field.py` prints `0`
  (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol:
  `tests/test_relay_node_field.py::test_node_custom_node_id_attr_resolves`.
- Grade: process provenance (review ordinal).
- Text-before:
  ```text
  ``None`` -> a spurious ``null`` for a row that exists (the P2 bug). The
  ```
- Text-after:
  ```text
  ``None`` -> a spurious ``null`` for a row that exists. The
  ```

- Observation:
  `tests/test_relay_node_field.py::test_decode_model_global_id_resolves_custom_node_id_to_real_pk`
  (line 419) ends with `(the P1 bug). The fix resolves it to ``row.pk``
  here.` — a stranded review ordinal plus `The fix` narration of a
  historical change.
- Evidence: `git log -S"the P1 bug"` lands on `cf3293cf` (`Fix 5
  release-review findings`, `relay (#1)`); the ordinal is that review's
  #1. Same KANBAN `TODO-ALPHA-056-0.0.17` spec-032 population as F5 (see
  there for the per-spec rule). The behavioral claims (wrong-column
  targeting, resolution to `row.pk`) are true and stay.
- Impact: bounded; one sentence.
- Severity: Low.
- Recommendation: delete the ordinal, de-tense the fix narration; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'the P1 bug' tests/test_relay_node_field.py` prints `0`
  (1 today) and `grep -c 'The fix resolves it'
  tests/test_relay_node_field.py` prints `0` (1 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol:
  `tests/test_relay_node_field.py::test_decode_model_global_id_resolves_custom_node_id_to_real_pk`.
- Grade: process provenance (review ordinal + fix narration).
- Text-before:
  ```text
  targets the wrong column (the P1 bug). The fix resolves it to ``row.pk`` here.
  ```
- Text-after:
  ```text
  targets the wrong column. The value resolves to ``row.pk`` here.
  ```

## Rejected

- R1 — Routed temporal wordings in `tests/test_relay_connection.py`: `The
  walker no longer plans the shape` (`::test_resolve_from_window_last_zero_stays_a_defensive_guard`),
  `No live path produces it anymore`
  (`::test_consume_window_unservable_window_runs_the_sync_fallback`), `The
  count-free hasNextPage shapes that USED to fall back here ... are now
  SERVED count-free`
  (`::test_count_less_window_with_count_observer_falls_back_defensively`).
  Temporal language serving a present fact with no process artifact named
  (connection R3 precedent). Each claim verified true: `last: 0` is fully
  unplanned (this run's connection H1), and the count-free shapes are
  served by the probe / constant-False `hasNextPage` per the count-policy
  overhaul. Trigger: a rewrite to pure present tense.
- R2 — Routed bare `(Decision 5)` pointers in the same file (lines 1651,
  1828; same-section `Decision 5:` at 1483 and `(Decision 4)` at 1449).
  The anchor is on the reader's path: the section banner at line 631
  (`spec-033 - connection-class fast path (Decision 5)`) plus repeated
  `spec-033 Decision 5` anchors (lines 843, 1668, 1697, 1796), and the
  content matches spec-033 Decision 5 in each use (connection R5
  precedent; START.md bare-Decision convention). Trigger: an anchor
  removed or a second same-named Decision.
- R3 — Temporal words serving present facts in graded scope: `now keyed
  on the real resolution field` (test line 382), `still constructs and
  declares` (test line 575), `keep the historical default-manager
  behavior` (`relay.py` line 277), `the pre-032 behavior` (`relay.py`
  line 138). None names a process artifact; each states what the code
  does today (connection R3 precedent). Trigger: a rewrite to pure
  present tense.
- R4 — Past-tense regression narratives with true behavioral claims: the
  multi-type `__typename` history (test lines 149-158), the directives
  character-wise history (test lines 556-565), the unconditional-await
  `TypeError` history (test lines 614-621); observed same-shape
  `pre-fix` banner in `tests/mutations/test_resolvers.py` (verified
  true against `cf3293cf`). Regression motivation, not detachable tags
  (connection R4 precedent). Trigger: the design changing under any of
  them.
- R5 — Bare Decision numerals with the anchor on the reader's path:
  `relay.py` module `Decisions 3/4/5/11` (spec-032 named at line 4) plus
  bare `Decision 4` / `Decision 5` at 9 further sites in the same file;
  live-tier `(Decision 4)` x2 / `(Decision 5)` x1 in
  `test_library_api.py`, each resolvable via the relay symbol it
  describes (`_check_typed_match` says Decision 4, the `strawberry.ID`
  argument is Decision 5's Rationale-Revision-7-P1 shape) and each
  content-verified against the body. Trigger: an anchor removed or a
  second same-named Decision.
- R6 — `(Edge cases "Async end-to-end")` (`relay.py` line 494). Unlike
  F2 it quotes the exact rule title (verified verbatim in spec-032 Edge
  cases), and the governing spec-032 anchor is on the reader's path in
  the module docstring — the R5 shape, not the L4 vague-pointer shape.
  Trigger: the module's spec-032 anchor removed, or a second spec
  gaining an `Async end-to-end` section.
- R7 — `Reconsideration triggers (Family typed-globalid-decode)` with
  `T-pipeline` / `T-status` / `T-shape` (`relay.py` lines 314-317). A
  standing 3-site package convention (`types/relay.py:79`,
  `list_field.py:214` identical in form) whose triggers are spelled out
  as content, not a pointer at flow scratch. Trigger: the convention
  retired.
- R8 — `the decode is the step that makes one inevitable` (`relay.py`
  lines 481-483). Verbatim spec-047 Decision 9 language
  (`which is the step that makes a visibility-scoped query inevitable`),
  quoting the decision the placement implements — not an overstatement
  to grade. Trigger: Decision 9 reworded.
- R9 — `DECODE_FAILED = "decode_failed"  # malformed / unresolvable
  type slot.` A true summary (strategy-forbidden and no-recorded-strategy
  failures are unresolvable-type-slot cases); the full enumeration lives
  once at the decode contract both callers cite. Trigger: the decode
  failure set changing.
- R10 — Spot-verified true vocabulary, each checked against its source:
  module docstring (factory mechanism, unconditional `required=False`
  dispatch at lines 498/603/615, `GLOBALID_INVALID` boundary, the
  `Any`-annotation `TypeError` quoted byte-exact against installed
  Strawberry 0.324.0 `schema_converter.py:1203` + graphql-core
  `definition.py:837`, no annotation cross-validation, the
  `Schema(types=[...])` engine note); spec-031 Decision 11 reservation;
  ledger comment (both factories append, emptiness check in the
  finalizer, co-clear registration); narrow decode scope incl. the
  `SyncMisuseError` carve-out; `_node_id_slot` single-statement claim
  (both consumers call it); coerce-field selection incl. the composite-pk
  escape hatch; no-extensions wrong-type error; `DecodeResult` field
  conditions; `_resolve_real_pk` default-manager + pipeline-recovery +
  using mechanics (recovery path confirmed: `type_check_relation_id`
  calls without `using`, `coerce_lookup_id` threads it); single-source
  decode claim (both named consumers call it); four-plus-fifth guard
  census (corroborates connection R10); interleave / length-check /
  stamp docstrings incl. the `install_is_type_of` precedence half and
  the lazy-proxy copy order; `DjangoNodesField` override contract incl.
  the per-type batching and the `SyncMisuseError` / `ConfigurationError`
  arms; committed-at-construction contrast (spec-032 Edge cases pins it
  as deliberate); every test helper + section docstring incl. the live-tier
  coverage map (holder at `/graphql-test/`, async rows at
  `/graphql-async/`, all present); all 7 `path::Symbol` citations (0
  violations); no `we` / `you` / `I`, no `Tests that` / `Ensures`, no
  line-number references in either graded file. Trigger: the named
  source changing.
- R11 — `_clear_node_fields_declared` carries no docstring. Private one-line
  body documented by the ledger comment plus the `register_subsystem_clear`
  call; no looks-for entry requires docstrings on private helpers
  (connection R11 precedent). Same for the nested `_resolve` / `_gather`
  closures and the `_SYNC_RESOLVER_RECOURSE` string. Trigger: none in this
  flow.
- R12 — Non-imperative first lines. `DjangoNodeField` / `DjangoNodesField`
  (`Factory for ...`) join the 4-site field-factory family;
  `_await_and_stamp` (`... (async sibling)`) joins the async-twin family;
  `GlobalIDDecode` / `DecodeResult` read as class descriptions. Package and
  family conventions beat the imperative rule here (connection R1
  precedent); every other function first line is imperative. Trigger: a
  maintainer decision enforcing mood package-wide.

## Routed leads

- Routed:
  `tests/test_relay_connection.py::test_count_less_window_with_count_observer_falls_back_defensively`
  — lines 2372-2374 read `The conditional-count drift guard in
  _resolve_from_window, narrowed by / The count-policy overhaul leaves
  only a totalCount observer ...`: a fused sentence (two finite verbs).
  Connection-subject prose in a verified/closed item, outside the routed
  wordings this pass owns — no open item owns it. Owner: `## Decisions`
  (Worker-0 routes).

Handoff: I graded every docstring and comment in the target (16 docstrings,
17 comment sites) and its own test module whole (31 docstrings, all banners
and inline comments), plus the routed connection-test wordings, the
live-tier and mutation/serializer prose about the target's symbols, and a
13-file other-package-module prose census: 6 Lows (F1 bare spec-047 pair,
F2 vague spec pointer, F3 card residue, F4 Round-4 S2 survivor, F5/F6
stranded P2/P1 ordinals), 10 rejections, 1 routed lead. Everything else
grades true, including the module docstring's long contract (each load-bearing
claim source-verified), all spec-Decision pointers (each verified against
its spec's text), and the mood/tense families (calibrated to the
connection item's verified R3/R4/R5 records). Two sequencing notes for
Worker-0: (1) F5+F6 together are KANBAN TODO-ALPHA-056-0.0.17's complete
spec-032 stranded-ordinal population — landing both discharges that card's
spec-032 row per its own per-spec rule, and landing one without the other
violates it; (2) the fused-sentence routed lead sits in the same file as
the routed wordings but is connection-subject prose the closed connection
item owns, hence Decisions, not this item. Observed true for owning items,
not graded here: `pre-032` in `types/relay.py:106` (same R3 shape as this
record's R3), `now shares` in `forms/resolvers.py` (forms-subject, forms
item judges), the bare `(spec-036)` in
`tests/mutations/test_resolvers.py::test_relation_field_index_excludes_generic_foreign_key`
(mutations-subject, mutations item judges), and the `S4` shape reference in
`test_resource_policy_api.py` (policy-subject, resource_policy item judges).
No workspace runs (all instruments static); scratch under
`docs/review/temp-tests/relay/comments/` (`inspect/`, `relay.json`,
`cites-relay.json`, `cites-relay.err`); live text equals ITEM_BASELINE on
all three fingerprinted files. On verify: every finding is prose-only and
owes `--code-digest` identity; F1's fix must keep both Decision 9 anchors;
F5/F6 must land as a pair.

## Verify comments

Pass 1, fully static (no workspace copy bound; `rg` is absent in this
environment so the Perf C1 Proof ran as its `grep` equivalent). Pass diff
`docs/review/temp-tests/relay/diff/pass-1.diff` read whole (699 lines); the
live item diff over the four touched files is byte-identical (`cmp`
IDENTICAL), so the tree still carries exactly the change under grade.
Scratch: `docs/review/temp-tests/relay/verify-comments-1/` (`diff/`,
`proofs.txt`, `added-lines.txt`, `cites.err`). Fingerprints at verify (`git
hash-object`): `django_strawberry_framework/relay.py`
`f5760b45f161cccf9dce6d2c84b45311b5b03291`,
`django_strawberry_framework/utils/write_values.py`
`13548c76605ec264cf95e7d10dc6a8bc813b360d`,
`tests/test_relay_node_field.py`
`d4ce0c7d0293bfb7ec1f12f3bf13559d2ae51f0e`,
`tests/utils/test_write_values.py`
`9f459e2f4c148a15a459b8748dfab4c54e0f7b9e`.

- F1 pass. `grep -c '(spec-047)' django_strawberry_framework/relay.py`
  prints `0`. Both Decision 9 anchors kept per the record's Handoff
  (lines 590, 674). Both comments grade true: the single comment's
  `check_deadline` sits before `_decode_or_graphql_error`; the batch
  comment's sits after `if not ids: return []` and before the batch
  decode; the "inevitable" wording is the verbatim Decision 9 language
  R8 pins.
- F2 pass. `grep -c '(spec Edge cases)'` prints `0`. Landed `# Zero
  database access (spec-032 Edge cases, the nodes(ids: []) rule).`
  grades true: `if not ids: return []` touches no DB, and the pointer
  names the spec and the exact rule.
- F3 pass. `grep -c 'card-named' tests/test_relay_node_field.py`
  prints `0`. Landed parenthetical keeps the spec-032 Decision 11
  pointer and drops the card attribution; module first line unchanged,
  so no TREE.md render is owed (all four module first lines verified
  byte-identical baseline-vs-live).
- F4 pass. `grep -c 'S2 regression'` prints `0`. Landed `Batch sibling
  of the single-node multi-type regression: per-position __typename
  routing.` names the regression (the single-node multi-type sibling)
  with no ordinal, and the behavioral half matches the body. True.
- F5 pass. `grep -c 'the P2 bug'` prints `0`. Parenthetical deleted,
  behavioral sentence intact and true.
- F6 pass. `grep -c 'the P1 bug'` prints `0` and `grep -c 'The fix
  resolves it'` prints `0`. Landed `targets the wrong column. The
  value resolves to row.pk here.` is the present-tense rule. True.
  Pair rule honored: F5+F6 both landed, discharging KANBAN
  TODO-ALPHA-056-0.0.17's spec-032 row per its per-spec rule.
  Judgment call: the surviving `feeds every WRITE consumer` lead-in was
  already loose pre-pass in the same dimension (raw-pk members bypass
  via `coerce_relation_pk_or_none`) and its load-bearing clause (`all
  of which treat result.pk as an actual primary key`) holds exactly for
  the batched path too, so the change made nothing false.
- Perf C1 pass. `grep -n 'Neither branch touches the DB'
  django_strawberry_framework/utils/write_values.py` prints no lines;
  first line is now `Type-check + coerce ONE relation id to a pk.`
  with no unconditional WITHOUT claim (`WITHOUT` greps empty). Landed
  docstring grades true whole: caller census is exactly
  `decode_visible_relation` (the form + serializer single wrappers) and
  the set decoder's raw-pk arm (line 323); the raw-pk branch is a pure
  coerce (no DB); the GlobalID query sentence plus the batching
  parenthetical reads true beside the `calls it per raw-pk element`
  sentence (the set path batches via its own mapping step, named in the
  `decode_visible_relation_ids` docstring); visibility stays
  caller-confirmed on both branches.
- Mech C1 pass. `grep -c '_decode_relation_id_set'
  django_strawberry_framework/relay.py` prints `0`. Live-consumer
  census: production `decode_model_global_id(` call sites are exactly
  `mutations/resolvers.py:1281` (`coerce_lookup_id`) and
  `write_values.py:152` (`type_check_relation_id`); `_decode_and_coerce(`
  call sites are exactly `relay.py:432` and `write_values.py:318`. The
  landed docstring names only these. True. (R10's `both named consumers
  call it` described the pre-pass text; this grades the landed text per
  dispatch. The surviving `tests/mutations/test_resolvers.py:1173`
  mention is the Handoff-routed twin in a file this diff does not touch
  — out of fence.)
- Mech C2 pass. `grep -c 'NON-concrete attr yields'` prints `0`. The
  three sub-cases grade true against the bodies: non-field yields
  `None` (the `FieldDoesNotExist` arm) with raw passthrough at every
  consumer including the batched one; a reverse relation yields its
  `Rel` object, which the coercer maps to `None` (the `isinstance`
  gate, `querysets.py:325`) — read `null` with no query, write
  `UNCOERCIBLE_PK`; a GFK yields the field object with identity coerce
  and the raw literal flows onward to the filter. Each matches the
  R11/GFK probe behavior the Mechanics record cites; the new first line
  (`get_field result or None`) and the three-consumer sharing sentence
  are true of the rule-value flow.
- Code-disturbance re-grades (F1/F2/F3/L1 vs every touched docstring):
  `decode_model_global_id`'s composed-behavior sentences hold through
  the `_decode_and_coerce` + `_resolve_real_pk` delegation (`using`
  pinned); `_decode_and_coerce` is query-free, shared by exactly the
  two named callers, and its OK-carries-coerced / no-row-becomes-
  `UNCOERCIBLE_PK` contract names the true terminal surface on both
  paths (literal status single, same uniform error set — spelled out in
  the sibling docstring); `_resolve_real_pks_batched` issues one query
  per non-trivial `(type, id_attr)` group, passes the pk/non-field
  shapes through query-free, takes first-match-wins, maps no-row to the
  same not-found surface, and recovers `using` from the pipeline —
  each sentence true of its body; `_resolve_real_pk`'s `once per
  decode instead of twice` and `naming no model field at all` narrowing
  are true; `_coerce_pk_or_none`'s slot-threading sentence names the
  true memoize sites with a true fallback; `decode_visible_relation_ids`
  (i)–(iv) plus the function-local-imports sentence are true of the new
  body. F2's `isawaitable` guards keep the `SyncMisuseError` /
  `ConfigurationError` arms with identical arguments (no docstring
  claimed eager naming); L1's hoist moves no behavioral sentence (the
  `function-local` sentence refers to write_values' own imports, still
  local). Judgment call: `DecodeResult`'s docstring stays true — it
  scopes itself to `decode_model_global_id` (`The structured result of
  ...`), whose OK still carries the real pk, while the intermediate
  OK-carries-coerced reuse is explicitly warned at the producer (`NOT
  yet the real primary key`). No gap.
- New test prose grades true: both F1 pin docstrings state their bodies'
  counts (2 queries across K=1/2/4; 1 query + uniform error on no-row;
  pipeline-alias recovery via `using`), both F2/F3 pin docstrings state
  theirs (zero `truth.name` calls over single + batch; one slot
  computation per path), and `_CountingTruth` delegates-while-counting
  as written. No `Tests that`/`Ensures`; the `other subsystems name
  eagerly` parenthetical is corroborated by the package-wide
  `truth.name` census (unconditional sites abound). Whole-diff reading:
  every other added line is code with no new comment; every moved
  comment is graded above.
- Gates: `check_citations.py --paths <relay.py, write_values.py,
  test_relay_node_field.py> --substrings` exits 0 — 14 citations, 0
  violations, 0 warnings (the fourth file adds 0 cites; the new cites
  at relay.py:315/406/408/409 all resolve). Provenance sweep over the
  diff's 404 added lines: only the three kept spec-Decision pointers;
  no card/round/worker/legacy/moved-from/no-longer/previously/now/
  fix-for, no we/you/I, no `Tests that`/`Ensures`, no line-number
  citations. No `--code-digest` identity is owed: this pass carries
  F1/F2/F3/L1 code by design (the other axes' findings), so it is not a
  prose-only pass; the code is the Performance/Mechanics verifiers'.

Status: verified. Open threads: (1) F5+F6 landed as a pair —
TODO-ALPHA-056-0.0.17's spec-032 row is discharged (Worker-0 records).
(2) The mutations-docstring C1 twin and the GFK-filter lead stay routed
per the Mechanics Handoff; both files untouched here. No new defects;
no added or moved text grades below true.

Handoff: Comments pass 1 verifies clean, fully static. Graded the six
Comments findings, the three cross-axis prose findings (Perf C1, Mech
C1/C2), and every docstring the F1/F2/F3/L1 code edits touch, against
live bodies plus caller censuses; the two judgment calls (F6 lead-in
looseness, `DecodeResult` intermediate scope) both resolve true with
reasons recorded above. No re-pass prose is owed by any axis. Evidence
under `docs/review/temp-tests/relay/verify-comments-1/`.
