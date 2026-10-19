# DRY review: `unwindowable-child-queryset-classification`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule, re-derived fresh at WT bytes (HEAD `5c3496e0` plus the
truth-migration dirt fingerprinted below): how a nested-connection child
queryset is judged unwindowable and with what reason -- the refusal
vocabulary, its producers, and the boundary where classification ends and
fallback begins.

The one authoritative definition is
`django_strawberry_framework/optimizer/nested_fetch.py:94`
(`unwindowable_child_queryset_reason`, lines 94-145). It maps a child
queryset to one of five stable reason strings or `None` (windowable),
reading the live query leniently in fixed order:

- `sliced` (`query.is_sliced`) -- reorder/re-slice would raise Django's raw
  `TypeError` inside the window build;
- `select_for_update` -- a lock the lateral raw-SQL path must not silently
  drop;
- `combined` (`query.combinator`) -- union/intersection/difference takes no
  window annotations or per-partition filters;
- `distinct` -- SQL evaluates window functions before `DISTINCT`, so the
  `_dst_total_count` `Count(1) OVER` annotation would over-count (the
  correctness-critical arm; spec-033 Decision 6);
- `values` (`_iterable_class` not a `ModelIterable` subclass) -- no model
  instances to carry the window attributes.

The contract source is
`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` Decision 6 (line 290;
the five reasons named at lines 258 and 401, with the whole-relation
unplanned fallback), which also records the upstream analogue (upstream
`get_total_count`'s `if queryset.query.distinct` guard, spec line 148).

Three production consumers, all by name, all boolean-only (`is not None`;
no production site reads a reason string):

1. `django_strawberry_framework/optimizer/nested_planner.py:1301`
   (`plan_connection_relation`): the plan-time gate. A reason returns the
   candidate plan untouched -- whole-relation refusal, no prefetch, no
   resolver keys, per-parent fallback stays strictness-visible. The gate
   runs on the base child queryset built exactly once (:1294) and feeds the
   same value into child-plan application on success.
2. `django_strawberry_framework/optimizer/lateral_fetch.py:640`
   (`_recognize_lateral_fetch`): the fetch-time first gate. A reason
   returns `None` -- the carried windowed body runs instead.
3. `django_strawberry_framework/optimizer/single_parent_fetch.py:244`
   (`_fetch_single_parent_rows`): same shape -- a reason returns `None`,
   the windowed body runs.

The enforcement is complete by construction, not by audit: the window
builder `optimizer/plans.py::apply_window_pagination` has exactly ONE
production caller (`nested_fetch.py::attach_windowed_prefetch`, line 336),
reached only through strategy `plan` bodies fed requests built AFTER the
plan-time gate; both built-in strategies funnel through it (windowed
directly, lateral via `wrap`); a consumer-authored strategy receives the
same post-gate request. The fetch-time recognizers re-gate by name because
the fetch-time query is the planned body plus prefetch/Django mutations,
not the value the planner classified.

Classification ends where the boolean is consumed; what follows is
fallback, never a second classification. At plan time the fallback is the
per-parent pipeline -- which re-seals the hook result under its own
surface policy and raises ITS OWN typed defect there (proved live: the
sliced-hook connection test observes the identical seal message only after
the parent genre query has run, where the list-relation twin refuses
before any query at all). At fetch time the fallback is the identical
windowed body. The reason string itself is telemetry/oracle vocabulary:
spelled once in the definition, matched nowhere in production.

Seal layering (why no arm is dead and none is doubled). Under
`has_custom_qs=True` the walker builds the base through
`_build_connection_child_queryset` under `_PREFETCH_CHILD_POLICY`
(`reject_sliced=False`, `rewrite_combined=True` kept,
`require_model_rows=True` kept), so the classifier observes hook results
AFTER the seal: sliced passes (licensed), locking and distinct pass
through (the seal has no such arms), combined arrives already rewritten to
its pk set (or raised), values never arrives (the seal's `projection`
defect raises first). Under `has_custom_qs=False` no seal runs -- a custom
default manager's `.all()` can hand every one of the five shapes straight
to the gate (the planner says so at lines 1288-1293; the distinct-manager
live test proves it end to end). The classifier and the seal are layered
guards with disjoint verdicts (degrade vs raise/rewrite), not rival
definitions (see R1).

HEAD-vs-WT delta on rule lines (concurrent truth-migration dirt, traced
but untouched): the classifier's `values` arm reads
`truth.is_subclass(iterable_class, ModelIterable)` at WT line 143 vs
`isinstance(...) and issubclass(...)` at HEAD line 142 -- same predicate,
same verdict. The other four arms, all three call sites, and the
seal-code lines cited in R1 are byte-identical modulo renderer-only
`truth.name`/`truth.kind` swaps. The verdict holds under both spellings.

## Verification

### Matrix

1. Cross-flavor policy mirroring -- swept every sibling surface for a twin
   classifier. The connection ROOT has `_guard_source_not_pre_sliced`
   (sliced-only, raises `GraphQLError` -- R2). The list field has no
   classifier (seal only). The seal (`_seal_or_defect`) classifies its own
   defect codes under different predicates and verdicts (R1). Mutations,
   forms, DRF, and write-transaction `select_for_update` populations are
   write-path lock CONFIGURATION, not read-path lock detection (R12).
   No second unwindowable-child classifier in any flavor.
2. Sync/async twins -- inapplicable with reason: the classifier is a pure
   predicate on in-memory queryset state (no I/O, no awaits, no alias or
   dialect read). One sync body serves the sync planner and both fetch
   colors; there is no await boundary to twin across.
3. Derived rather than repeated knowledge -- the five states are derived
   from query slots in exactly one place. The seal derives ITS codes from
   reconstructed instance state under different predicates (exact-identity
   `iterable is not ModelIterable` vs the classifier's subclass-accepting
   read; a `ModelIterable` subclass passes the classifier and fails the
   seal -- mechanically different rules, R1). No second derivation of
   THESE five.
4. Inverse / round-trip pairs -- none exists and none is owed: the mapping
   is one-way. Literal census proves it: the five reason strings are
   RETURNED only in the definition (5 `return` lines) and MATCHED only in
   tests (oracles below); no enum, no from-string parse, no production
   `== "sliced"` anywhere.
5. Contracts restated in another medium -- the classifier docstring
   (projection), spec-033 Decision 6 (contract), and the tests below
   (oracles) each restate the vocabulary. Listed under Findings, not
   counted: an intentional vocabulary change moves the definition plus its
   oracle/projection tail, which is one definition, not five.
6. Enforcement by omission -- enumerated every path that windows a child
   (Matrix preamble above): single `apply_window_pagination` caller,
   post-gate requests only, fetch-time re-gates by name. No path windows
   an unclassified child. `single_parent_spec` and `_build_lateral_spec`
   check disjoint request-level/backend-expressibility rules on the
   post-gate request (R7, R8), never the five states.

### Enumeration

Instruments (all `muse.search`, regex, WT bytes) and their disposition:

- `unwindowable_child_queryset_reason`: 12 reference lines = 1 definition
  (`nested_fetch.py:94`), 3 imports, 3 call expressions (the consumers
  above), 5 prose references (module/seam docstrings and comments --
  projections). Every member homed.
- `return "(sliced|select_for_update|combined|distinct|values)"`: 5 lines,
  all inside the definition. Zero production matchers (R1--R12 carry the
  lookalikes).
- `is_sliced|select_for_update|combinator`: 60+ lines across 12 files --
  seal machinery + defect wordings (R1), `_guard_source_not_pre_sliced`
  (R2), `attach_exists` guard (R4), combined-root passthrough (R5),
  hint-prefetch rewrite (R6), write-path lock config (R12), plus prose.
  Every production site homed in an R-row or named prose.
- `_iterable_class|ModelIterable`: classifier arm + seal iterable
  machinery (R1). Homed.
- `UnwindowableConnection`: slice-arithmetic signal only (R3). Homed.
- `apply_window_pagination`: 1 production caller (completeness proof for
  axis 6). Homed.

### Challenges

- C1 (shape axis -- add a sixth unwindowable state, e.g. a grouped query):
  1 definition moves (one arm in the classifier body). The 3 consumers are
  untouched (boolean-only); the matrix oracle gains a row (oracle, not
  counted); the planner's shape-list comment and the docstring bullet move
  as projections (not counted). Count: 1.
- C2 (vocabulary axis -- rename a reason or split `values` into
  `values`/`values_list`): 1 definition moves (return sites) plus oracle
  expectations (not counted). Zero production string readers, so no
  consumer moves. Count: 1.
- C3 (mechanics axis -- replace the lenient `getattr` reads with strict
  slot reads, or track a renamed Django slot): 1 definition moves. The
  seal's audited slot census (`querysets.py` combinator/payload
  reconstruction) does NOT move -- it is the seal-reconstruction rule,
  not this classification. Count: 1.

Corroboration (not the proof -- the proof is the census): the committed
matrix oracle
`tests/optimizer/test_nested_fetch.py::test_unwindowable_child_queryset_reason_matrix`
was run once in the shared tree (`--no-cov`, default cell): 1 passed.
It spells all five reasons plus the subclass-accepting `values` edge
(custom `ModelIterable` subclass maps to `None`, a non-type maps to
`values`), independently of the owner -- it fails if the map changes.

## Findings

F1: unwindowable-child-queryset classification -- CONFIRM, single-owned,
zero-edit.

- Contract + variation. A nested-connection child queryset maps to
  `sliced | select_for_update | combined | distinct | values | None`.
  Any reason degrades (plan time: whole-relation unplanned per spec-033
  Decision 6; fetch time: windowed body). Varies on three axes: the shape
  set (C1), the reason vocabulary (C2), the read mechanics (C3).
- Sites + roles. Definition (1): `nested_fetch.py` lines 94-145.
  Consumers (3, by name, boolean-only): `nested_planner.py:1301`,
  `lateral_fetch.py:640`, `single_parent_fetch.py:244`. Oracles:
  `test_nested_fetch.py::test_unwindowable_child_queryset_reason_matrix`
  (spells all five reasons + None cases);
  `test_walker.py::test_connection_child_seam_still_admits_a_sliced_hook_result`
  (seal admits, classifier flags);
  `test_walker.py::test_unsafe_child_queryset_left_unplanned_under_both_strategies`
  (sliced + locking unplanned under windowed AND lateral);
  `test_walker.py::test_combined_child_queryset_is_planned_as_its_primary_key_set`
  (seal rewrite precedes the gate -- pins the layering);
  `test_library_shapes_api.py::test_patron_profile_annotations_connection_is_left_unplanned_and_fetched_per_parent`
  (live: distinct manager, no window SQL, per-parent pages correct);
  `test_library_api.py` sliced-hook pair (live: list refuses pre-query,
  connection refuses post-parent-query -- pins the classification/fallback
  boundary). Projections: classifier + module docstrings, walker/seal
  seam prose, spec-033 Decision 6/Decision 4 text.
- Challenges. C1/C2/C3 above; every count is 1.
- Owner + lifetime. Owner: `unwindowable_child_queryset_reason` in
  `optimizer/nested_fetch.py` (principle 7: the fetch-seam module every
  legitimate consumer already imports -- planner, both recognizers --
  with no dependency reversal; the narrowest home for a
  strategy-independent gate). No stored derivation (pure function;
  "not cached").
- Migration. None -- already composed by name at all three sites.
- Distinct behavior (exclusions, each with contract difference +
  reconsideration trigger):
  - R1 seal defect codes (`querysets.py::_seal_or_defect`:
    `sliced`/`projection`/`combined`/`evaluated`/`alias`/...). Different
    vocabulary (`projection`, not `values`; no distinct/locking arms),
    different verdict (raise `ConfigurationError` or rewrite to pk set,
    never degrade), different subject (any consumer queryset at any
    surface vs the nested child only), different predicate
    (exact-identity vs subclass-accepting; arm order differs). Standing
    File `optimizer/nested_fetch.py` row "Classifier vs seal rejection"
    trigger-checked clean at WT. Trigger: the seal gains distinct/locking
    arms AND a non-raising degrade verdict for the nested child.
  - R2 `_guard_source_not_pre_sliced` (`connection.py:1750`; file-local
    family `connection-pre-sliced-source-guard`, stands). Sliced-only,
    raises `GraphQLError` at the `resolver=` contract, guards the ROOT
    source, not a prefetch child. Trigger: the guard generalizes past the
    slice or stops raising.
  - R3 `UnwindowableConnection` (`utils/connections.py:84`). A typeless
    control-flow signal for slice WINDOW ARITHMETIC (pagination args the
    offset/keyset engines cannot express), never a queryset-state
    verdict. Standing File `utils/connections.py` row
    `unwindowable-signal-vs-error-taxonomy` trigger-checked clean.
    Trigger: the signal starts carrying queryset-state reasons.
  - R4 `optimizer/predicates.py::attach_exists` combinator arm (:175).
    Caller-contract misuse (reserved-alias attachment onto a combined
    outer) raising `OptimizerError`; existence-predicate concern, one
    shape, no vocabulary. Trigger: the guard degrades instead of raising.
  - R5 combined-root passthrough (`optimizer/extension.py:1288`).
    Combinator-only, ROOT queryset, log-and-pass-through-unplanned.
    Trigger: it extends to children or past the combinator.
  - R6 `_hint_prefetch_over_pk_set` (`walker.py:1401`). Hinted-Prefetch
    combinator rewrite delegating to the seal's
    `_pk_membership_query_or_defect`, raising `ConfigurationError`
    naming the hint. Trigger: it classifies the five states instead of
    delegating one shape.
  - R7 `_build_lateral_spec` expressibility checks
    (`lateral_fetch.py:1062-1091`: select_related/annotations/extra/
    group_by/visibility-WHERE shape). Per-backend SQL expressibility on
    the POST-GATE request; verdict is downgrade-to-windowed (still
    planned), slots disjoint from the five. Trigger: a future classifier
    arm lands on one of those slots -- revisit the boundary then.
  - R8 `single_parent_spec` eligibility
    (`single_parent_fetch.py:137-153`). Request-level attributes
    (count/reverse/queryset class/join shape/window shape); reads no
    queryset state. Trigger: it gains queryset-state arms.
  - R9 `classify_relation_join` windowability (`join_taxonomy.py`;
    verified f21, taken as input). Relation KIND classification
    (forward-M2M vs DIRECT_FK vs ...), not queryset STATE. Trigger: kinds
    start depending on queryset state.
  - R10 cascade field-specific `distinct_fields` guard
    (`permissions.py:518`). Cascade-subquery concern; `distinct_fields`
    (field list), not `distinct` (flag). Trigger: the cascade starts
    windowing children.
  - R11 lenient-read mechanics (HEAD `join_taxonomy.py::_safe_getattr`
    (`:100`) / `_safe_flag` (`:108`); WT-dirt `_attr` (`:92`) / `_flag`
    (`:97`); classifier uses bare `getattr`). No shared lenient-readers
    module exists at either state; each site's leniency is local to its
    subject (synthetic field doubles vs possibly-synthetic querysets).
    Standing File `optimizer/nested_fetch.py` row "Lenient query-attr
    reads vs a lenient-readers module" (plan:432/R16, which never cited
    the symbol; the plan:409 join_taxonomy-R13 citation is HEAD-correct)
    holds in substance (see D1). Trigger: a third lenient-read site with
    the SAME subject (queryset state) appears.
  - R12 `Meta.select_for_update` validation/consumption (mutations, forms,
    DRF, write-transaction). Write-path lock CONFIGURATION (bool on a
    mutation Meta), not read-path detection of a locked queryset.
    Trigger: the write path starts classifying read shapes.
- Behavioral proof. Static-reviewed: single definition established by
  exhaustive literal/reference census; boolean-only consumption proved by
  the zero-production-matcher census; layering pinned by committed oracles
  (one re-executed green above). No behavior changes, so no equivalence
  execution is owed.
- Structural gate. None proposed, justified: all three consumers already
  compose the owner by name, so a second-definition census would be the
  forbidden bespoke-existence-test shape (f24 precedent: no-new-gate
  ENDORSED). The matrix oracle independently pins the vocabulary (it
  spells literals; a map change fails it).
- Coupling. None -- zero edits, no landing order.
- Freshness. HEAD `5c3496e0`. WT/HEAD blob pairs (all match dispatch):
  `nested_fetch.py` WT `c36826bb` / HEAD `bedaa76e`;
  `nested_planner.py` WT `b6ff0a0e` / HEAD `8c3a45f5`;
  `lateral_fetch.py` `a48cb0a4` clean; `single_parent_fetch.py`
  `3a4bb89b` clean; `querysets.py` WT `3e392d48` / HEAD `69ac3ea3`;
  `walker.py` WT `4fd8077f` / HEAD `13e1be20`. Rule-line dirt is confined
  to the truth-migration one-liners named in System trace (verified via
  `git diff HEAD` hunk census). Searched population: whole
  `django_strawberry_framework/` tree (6 instruments, counts in
  Enumeration). Contract sources: spec-033 Decision 6 + the upstream
  DISTINCT-guard analogue. Excluded modules (read, not members):
  `connection.py`, `utils/connections.py`, `optimizer/predicates.py`,
  `optimizer/extension.py`, `optimizer/join_taxonomy.py`,
  `permissions.py`, `mutations/*`, `forms/*`, `rest_framework/*`,
  `utils/write_transaction.py`, `keyset.py`, `filters/sets.py`.
  Cells: default executed (matrix test green); sharded/pg `unverified`
  (not authorized; f24 precedent -- the finding's proof is construction
  census, but the binary binds).

## Defects

- D1 (record note CORRECTED on re-pass; no product change, NO closeout
  action): the as-submitted D1 erred twice over. (1) HEAD absence is
  REFUTED: `def _safe_getattr` EXISTS at HEAD `join_taxonomy.py:100`
  plus 15 use-lines (`git show
  HEAD:django_strawberry_framework/optimizer/join_taxonomy.py | grep -n
  _safe_getattr` returns 16 lines; the WT diff's minus-side `def
  _safe_getattr` is the same proof). Only the WT absence holds (`_attr`
  at WT `join_taxonomy.py:92`, `_flag` at WT `:97`), and that rename is
  concurrent hunt dirt -- no `## Owned changes` row owns
  `join_taxonomy.py` (ledger grep empty), and the diff replaces the
  lenient-mode shared readers with plain `getattr` (102+/88-,
  uncommitted). (2) The standing File `optimizer/nested_fetch.py`
  rejection row "Lenient query-attr reads vs a lenient-readers module"
  (plan:432/R16) never cited the symbol at all (`grep -n _safe_getattr`
  over its artifact is empty) -- it names the classifier with a standing
  join_taxonomy-R13 trigger note. The symbol IS cited by the join_taxonomy
  R13 row (plan:409), which is CORRECT at HEAD. Both row SUBSTANCES
  re-verify clean. The "citation repair" routing is VOID: closeout owes
  nothing at HEAD bytes -- repairing correct HEAD citations to dirt-only
  names would corrupt the record; citations follow hunt's own landing,
  never a DRY closeout edit.

## Pending execution

None.

## Judgment

CONFIRM: `unwindowable_child_queryset_reason` is the single owner of
unwindowable-child-queryset classification -- one definition, three
by-name boolean-only consumers, vocabulary pinned by an independent
matrix oracle, twelve exclusions with triggers. Zero edits; the
consolidation the family names already holds by construction.

## Independent verification (Worker-2)

### Part A -- Own trace (recorded before opening `## Findings`)

Trace subject: HEAD bytes (`5c3496e0`) + WT bytes; fingerprints below.
Owner candidate re-derived, not inherited.

Sites found package-wide for the mechanism "classify a child queryset
as unwindowable" (searched: `unwindowable_child_queryset_reason`,
`is_sliced`, `combinator`, `select_for_update`, `distinct` in
`optimizer/`, `_iterable_class`, `return "sliced"|"combined"|...`):

- DEFINITION (1): `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
  (`nested_fetch.py:94-145`): five reason arms in fixed order --
  `sliced` (`query.is_sliced`), `select_for_update`
  (`query.select_for_update`), `combined` (`query.combinator`),
  `distinct` (`query.distinct`), `values`
  (`_iterable_class` not a `ModelIterable` subclass, defaulting the
  missing attr to `ModelIterable`) -- else `None`. Each
  `return "<reason>"` literal is unique package-wide (one hit each).
- CONSUMERS, code (3), all boolean-only (`is not None`, never reading
  the string): `optimizer/nested_planner.py:1301` (plan-time whole-
  relation gate before any strategy builds), `optimizer/lateral_fetch.py:640`
  (fetch-time recognizer first gate, degrades to windowed body),
  `optimizer/single_parent_fetch.py:244` (same shape). Each imports the
  name from `.nested_fetch` (`lateral_fetch.py:93`,
  `nested_planner.py:56`, `single_parent_fetch.py:62`).
- No string-value reader of the vocabulary exists in production: no
  `== "sliced"` / `in (...)` / log-format over the classifier's
  output anywhere under `django_strawberry_framework/`.
- PROJECTIONS (prose only, no calls): `nested_fetch.py:18-19` +
  `:128-131` (module + function docstrings),
  `optimizer/walker.py:600` + `:651` (slice-licence comments),
  `utils/querysets.py:2918` + `:2984` (seal-policy comments),
  `optimizer/nested_planner.py:1288-1293` (gate comment).
- ORACLES: `tests/optimizer/test_nested_fetch.py:316`
  `test_unwindowable_child_queryset_reason_matrix` (spells all five
  strings literally + `None` arms + two `_iterable_class` edge cases:
  `ModelIterable` subclass -> `None`, non-type -> `"values"` --
  independent, never reads the owner); `tests/optimizer/test_walker.py:1435`
  (seam admits sliced; boolean `is not None` use); live-query behavior
  oracles `examples/fakeshop/test_query/test_library_shapes_api.py:368`
  (distinct manager -> unplanned, per-parent pages correct) and
  `examples/fakeshop/test_query/test_library_api.py:863`
  (sliced hook on connection -> resolve-time typed defect, parent
  query already run). Both cite the classifier by `path::Symbol`
  in prose only.
- Completeness of the consumer census: exactly two
  `RecognizedFetchQuerySet` subclasses exist (`lateral_fetch.py:482`,
  `single_parent_fetch.py:171`), each gated; the windowed strategy is
  itself the fallback body (no recognizer to omit the check); the
  planner gate covers every strategy at plan time. No enforcement-by-
  omission gap.

Exclusions re-derived independently (each: contract difference):

- X1 seal defect vocabulary
  (`utils/querysets.py::_sealed_execution_queryset` defect codes
  `sliced` / `combined` / `projection` / `untrusted` / ...,
  `:3644-3680`): policy-gated hook-return guards for safe
  RECOMPOSITION; the seal SERVES a rewritable combinator as its
  pk-set (`:3669-3674`) where the classifier REFUSES every
  combinator; seal `sliced` is `reject_sliced`-gated (`:3846`),
  classifier `sliced` unconditional. Different outcomes,
  populations, reasons to change.
- X2 `connection.py::_guard_source_not_pre_sliced` (`:1750-1772`):
  top-level connection-source guard raising `GraphQLError`;
  different level (root source vs nested child), different effect.
- X3 `optimizer/predicates.py::attach_exists` combinator arm
  (`:175-181`): alias-attachment caller contract raising
  `OptimizerError`; guards `.alias()`, not windowing.
- X4 `optimizer/extension.py:1288` root combined passthrough:
  combined ROOT runs unplanned + debug log; root vs child level.
- X5 `optimizer/walker.py::_hint_prefetch_over_pk_set` (`:1401-1441`):
  hinted-Prefetch combined REWRITE via
  `_pk_membership_query_or_defect`; serves, never refuses.
- X6 `_pk_membership_query_or_defect` /
  `_combined_lost_property` (`utils/querysets.py:3478-3560`): the
  rewrite machinery; its nested `is_sliced` (`:3487`) /
  `select_for_update` (`:3518`) reads are rewrite preconditions,
  not windowability.
- X7 `optimizer/join_taxonomy.py::classify_relation_join` (`:331`):
  static FIELD kind -> `RelationJoinDescriptor(windowable=...)`;
  disjoint input (field vs queryset) and output (descriptor vs
  reason string) domains from queryset-STATE classification.
- X8 `utils/connections.py::derive_connection_window_bounds`
  (`:652`): pagination-argument arithmetic ->
  `(offset, limit, reverse)`; disjoint domain.
- X9 `resolve_strategy` (`nested_fetch.py:437`) /
  `active_strategy` (`nested_fetch.py:489`): strategy SELECTION
  (name/setting/frame -> backend), same module, distinct rule.
- X10 recognizer-specific fetch-time guards
  (`lateral_fetch.py:643-660`, `single_parent_fetch.py:247-269`:
  select_related / extra / group_by / order / annotations /
  projection / signature): per-strategy shape proofs AFTER the
  shared gate; strategy-specific vs strategy-independent.
- X11 standing R16 (lenient-reads rejection, plan:432): substance
  is the classifier's plain-`getattr` reads vs shared lenient
  machinery; trigger re-check below in Part B. The CITATION
  question is D1 (position below).
- X12 `window_partition_resolution` family (f21,
  `window_partition_for_prefetch`): partition-EXPRESSION
  resolution vs queryset-STATE classification.

Challenges (definition counts; consumers/oracles listed, uncounted):

- C1 sixth reason (e.g. a new unsafe shape): 1 edit (owner arm)
  + 1 matrix case (oracle). Consumers boolean -> untouched. Count 1.
- C2 reason-string rename: 1 definition edit + matrix update
  (oracle). Zero consumer edits (boolean-only). Count 1.
- C3 predicate change (e.g. `values` via `query.values_select`
  instead of `_iterable_class`): 1 edit. Count 1.
- C4 drop a reason (e.g. `distinct` support via subquery count):
  1 edit + oracle/behavior updates. Count 1.
- C5 second vocabulary reader (e.g. telemetry matching strings):
  new consumer BY NAME; count stays 1 unless it re-derives
  (none exists). Count 1, conditional.
- C6 split into per-reason predicates: would CREATE count > 1
  for one rule -- correctly rejected; the single function is the
  narrowest cohesive owner. No such split exists.

Owner choice (principle 7): CONFIRM
`optimizer/nested_fetch.py::unwindowable_child_queryset_reason`. The
strategy-seam module owns strategy-independent fetch decisions; all
three consumers already depend on it (planner + both fetch backends
import from it); moving to `querysets.py` would couple the seal's
hook-validation responsibility with fetch windowing; a new module
would be machinery for one function with three same-subsystem
consumers. Dependency direction + narrowest-valid-owner agree.

D1 position (record note; evidence gathered pre-read): the standing
citation is CORRECT at HEAD -- `def _safe_getattr` EXISTS at HEAD
`join_taxonomy.py:100` (+15 use-lines; `git show
HEAD:django_strawberry_framework/optimizer/join_taxonomy.py | grep -n
_safe_getattr`). The WT `_attr` (`:92`) / `_flag` (`:97`) names are a
concurrent-dirt rename (no `## Owned changes` row owns
`join_taxonomy.py`; the WT diff replaces the lenient-mode shared
readers with plain `getattr`). A claim of absence "under neither
HEAD nor WT" would be refuted for HEAD; closeout owes NO citation
repair at HEAD bytes. Full adjudication in Part B after reading W1's
D1 text.

Matrix axes discharged against the real surface: (1) cross-flavor --
sibling flavors never window child querysets; seal is the sibling
mechanism, excluded X1; (2) sync/async -- pure function, no twin;
(3) derived knowledge -- no second "windowable?" derivation
(`return "<reason>"` literals unique); (4) round-trip -- reason
strings terminal, no decode partner; (5) other media -- oracles
spell literals, projections cite by name; (6) omission -- census
complete (2/2 recognizers + planner gate + windowed-is-fallback).

Freshness (Worker-2 pins): HEAD `5c3496e0` unmoved; WT
`git hash-object` short pins -- `nested_fetch.py` `c36826bb`,
`nested_planner.py` `b6ff0a0e`, `lateral_fetch.py` `a48cb0a4`,
`single_parent_fetch.py` `3a4bb89b`, `querysets.py` `3e392d48`,
`walker.py` `4fd8077f` (6/6 match dispatch); HEAD pins
`bedaa76e` / `8c3a45f5` / `a48cb0a4` / `3a4bb89b` / `69ac3ea3` /
`13e1be20` likewise. `git diff ITEM_BASELINE --name-only` is the
plan edit alone; `git status --short` count 473 with the single
untracked f25 artifact as the +1; no `## Implementation` section
(header/shape check only -- Findings not yet opened).

### Part B -- Reconciliation (after reading `## Findings`) + adjudication

F1 CONFIRM: ENDORSED in full. My independent census matches W1's on
every load-bearing point: one definition (`nested_fetch.py:94-145`,
five arms + `None`), exactly three consumers, all boolean-only
(`nested_planner.py:1301`, `lateral_fetch.py:640`,
`single_parent_fetch.py:244`), zero production string readers (each
`return "<reason>"` unique package-wide), same principle-7 owner
reasoning (seam module every consumer already imports; querysets.py
would couple seal duty with fetch duty; a new module would be
machinery). My challenges C1-C6 all count 1 (C2's rename-count-1 is
airtight precisely because consumption is boolean-only); W1's
C1/C2/C3 agree. Matrix axes 1-6: W1's discharge judged correct on
each reason (axis-2 pure-predicate inapplicability and axis-4
no-round-trip hold; axis-6 completeness via the single
`apply_window_pagination` caller + post-gate requests + fetch-time
re-gates is sound -- I additionally proved 2/2 recognizer subclasses
gated, windowed-is-fallback). Enumeration instruments/counts
reproduced (12 reference lines = 1 def + 3 imports + 3 calls + 5
prose; 5 return lines). Owner + "not cached" lifetime: endorsed.

Oracles: W1's census is MORE complete than mine and every member
verified. The matrix oracle re-ran green under my hand (shared venv,
`--no-cov`, default cell: 1 passed). The two `test_walker.py` oracles
I had not found both exist and match W1's glosses:
`test_unsafe_child_queryset_left_unplanned_under_both_strategies`
(`:5692`, windowed/lateral x sliced/locking -> no `_dst_*` prefetch,
empty resolver keys) and
`test_combined_child_queryset_is_planned_as_its_primary_key_set`
(`:5757`, seal rewrite precedes the gate). No oracle reads the owner
(reason strings appear only as literals/labels/prose). The live-query
pair pins the classification/fallback boundary as claimed. No new
oracle owed.

Exclusions R1-R12: ALL TWELVE ENDORSED on substance, each re-verified
against the cited bytes (contract difference + trigger both hold):

- R1 seal codes: endorsed. Extra-mechanical proof of W1's sharpest
  claim: seal `:3848` is exact-identity
  (`iterable is not ModelIterable`) vs the classifier's
  subclass-accepting read -- a `ModelIterable` subclass passes one
  and fails the other. Standing plan:426 row genuinely clean
  (seal has no distinct/locking arms, no degrade verdict).
- R2 root sliced-guard: endorsed (plan:297 file-local row stands).
- R3 `UnwindowableConnection`: endorsed (`connections.py:84-93`,
  Decision-5 slice-arithmetic signal, raised by the bounds
  derivation -- never a queryset verdict; plan:970 row clean).
- R4 `attach_exists`: endorsed (alias-attachment contract,
  `OptimizerError`).
- R5 root combined passthrough: endorsed (extension.py:1288,
  log-and-pass-through).
- R6 hint-prefetch rewrite: endorsed (serves via pk-set, raises
  naming the hint).
- R7 lateral spec checks: endorsed (`lateral_fetch.py:1062-1091`,
  post-gate expressibility, slots disjoint, downgrade verdict).
- R8 single-parent spec: endorsed (`:137-153` eligibility reads
  request scalars + exact-type + join + range plan -- no query
  STATE slot).
- R9 relation-kind taxonomy: endorsed (f21 input; kind vs state).
- R10 cascade `distinct_fields`: endorsed (`permissions.py:518`,
  `DISTINCT ON` field-list guard for cascade re-projection --
  different slot, different concern; W1's package-wide sweep
  caught what my optimizer-scoped one missed).
- R11 lenient-read mechanics: SUBSTANCE endorsed (no shared module
  at either state; trigger correctly drawn) -- but its dependent
  naming line ("its cited symbol name has drifted (see D1)") and
  unqualified `_attr`/`_flag` naming inherit D1's error: see the
  revision candidate below.
- R12 write-path lock config: endorsed (Meta-bool configuration vs
  read-path detection; sample-checked
  `mutations/sets.py::validate_select_for_update`).

My adjacents X6/X8/X10/X12 need NO rows: X6 is covered by R1+R6
(rewrite internals), X8 by R3 (the signal IS the lookalike; the
bounds derivation is its raiser), X10's fetch-time conjuncts are
consumer-internal (covered by the consumer census + R7's trigger
logic), X12 by R9's f21-input reference. Index rows owed: NONE --
endorsed ("none owed"); every standing row cited (plan:297/409/426/
432/970) keeps its current disposition.

Structural gate (none proposed): ENDORSED with W1's justification.
A second-definition census for one helper is the forbidden
bespoke-existence-test shape; the literal-spelling matrix oracle
pins the vocabulary (a map change fails it by construction).
`prove_failability.py` proportionate to skip on a zero-edit CONFIRM
(run-9 f21-f24 precedent; no workspace run used here either).

Cells: ENDORSED -- default executed (matrix green under both hands;
behavior oracles ride the default suite), sharded/pg `unverified`
(canonical binary; `--cell` unauthorized). `unverified` over
`inapplicable` is RIGHT here despite the classifier's purity: the
lateral consumer's fetch-time gate is backend-sensitive (lateral
SQL engages on Postgres), so the finding's proof genuinely varies
by cell. Pending execution "None.": CORRECT -- no `proof:` owed
(static census + committed oracles; nothing ordering/transactional/
async), no `gate:` owed. But for the D1 candidate below, the item
would be plain `verified`.

D1: HALF-REFUTED + MISATTRIBUTED -- the revision candidate. W1
claims the nested_fetch row "cites
`optimizer/join_taxonomy.py::_safe_getattr`, which exists under
neither HEAD nor WT bytes" and routes "citation repair" to closeout.
Fresh byte evidence refutes this twice over: (1) `_safe_getattr`
EXISTS at HEAD -- `def _safe_getattr` at HEAD
`join_taxonomy.py:100` plus 15 use-lines (`git show
HEAD:django_strawberry_framework/optimizer/join_taxonomy.py | grep -n
_safe_getattr`; the WT diff's minus-side `def _safe_getattr` is the
same proof). Only the WT absence holds (`_attr`/:92 + `_flag`/:97),
and that rename is CONCURRENT HUNT DIRT -- no `## Owned changes`
row owns `join_taxonomy.py`, and the diff replaces the lenient-mode
shared readers with plain `getattr` (semantic rewrite, uncommitted).
(2) The cited row does not cite the symbol at all: plan:432/R16 name
the CLASSIFIER with a join_taxonomy-R13 trigger note, and
`grep -n _safe_getattr docs/dry/dry-file-optimizer__nested_fetch.md`
is empty. The symbol IS cited by the join_taxonomy R13 row
(plan:409) -- which is CORRECT at HEAD. W1's R11 drift line inherits
the error. The row SUBSTANCES re-verify clean (agreed) -- but the
routing is VOID: closeout owes NO citation repair at HEAD bytes.
Repairing correct HEAD citations to dirt-only names would corrupt
the record against the committed tree. Correct routing: no action;
if hunt lands its rename, citations follow that landing, never a
DRY closeout edit. (W1's HEAD-vs-WT values-arm note -- HEAD
`isinstance and issubclass` vs WT `truth.is_subclass`, same
predicate -- is CORRECT, so this is a localized D1 slip, not
systematic WT-only inspection.)

REVISION CANDIDATE (single; reproducible): correct D1 -- (a) strike
"exists under neither HEAD nor WT" (HEAD: `def _safe_getattr`,
join_taxonomy.py:100 + 15 use-lines; prove with the `git show` grep
above); (b) fix the attribution (the nested_fetch row never cited
the symbol; plan:409's citation is HEAD-correct); (c) void the
"citation repair" routing (no closeout action at HEAD; WT rename =
concurrent dirt per the ledger check + `git diff HEAD` content);
(d) qualify R11's helper naming per state (HEAD `_safe_getattr` /
`_safe_flag`; WT-dirt `_attr` / `_flag`) or drop the drift line.
Resubmission returns to this Worker-2 for a fast tick; nothing else
in the artifact is disputed.

Execution record (Worker-2, shared venv per KNOWN slots note; no
workspace run; no `--cell`): matrix oracle 1 passed (`--no-cov`,
default cell); `uv run mypy` clean (119 files, exit 0);
`uv run basedpyright` 0/0/0 (exit 0);
`uv run python scripts/check_any.py` 130/90 (exit 0). Ruff
`format --check` + `check` on touched tracked paths: VACUOUS (zero
tracked `.py` touched -- the item diff is the plan edit alone; this
verification's only edit is this scratch section + the Status flip).
`## Defects`: no new entry -- zero code defects found; the D1
correction rides this verdict (e11 "false D1 struck on re-pass"
precedent), not a competing entry. W1 sections byte-intact.

VERDICT: revision-needed (D1 single candidate above). All of F1,
R1-R12 substance, owner, oracles, challenges, matrix, enumeration,
gate-justification, freshness (W1's six blob pairs match mine
byte-for-byte), cells, pending-None, and index-rows-none are
ENDORSED and need no re-proof on re-pass.

## Re-pass verification (Worker-2, re-pass)

Fast tick on the single D1 revision candidate. All proofs below
reproduced fresh at current bytes (shared-tree read-only commands;
shared venv for the gates per the KNOWN slots note; no workspace
run, no `--cell` -- nothing here mutates source).

Delta proofs (one line per sub-point):

- (a) HEAD `def _safe_getattr` EXISTS: `git show
  HEAD:django_strawberry_framework/optimizer/join_taxonomy.py |
  grep -n _safe_getattr` returns 16 lines -- line 100 is the
  `def`, plus 15 use-lines (194/199/200/220/221/228/229/232/
  244/249/269/272/307/308/366). The "neither HEAD nor WT" claim
  is refuted for HEAD. HOLDS.
- (b) Misattribution fixed: `grep -n _safe_getattr
  docs/dry/dry-file-optimizer__nested_fetch.md` is empty (exit
  1); plan:432 names only the classifier with a standing
  join_taxonomy-R13 trigger note, while plan:409 cites
  `optimizer/join_taxonomy.py::_safe_getattr` -- CORRECT at HEAD
  per (a). HOLDS.
- (c) Repair routing VOID, "no closeout action" RIGHT: the 76-line
  `## Owned changes` ledger greps empty for `join_taxonomy`
  (no row owns it); WT shows the concurrent-dirt rename (`def
  _attr` at `:92`, `def _flag` at `:97`, zero `_safe_getattr`
  hits) inside a 102+/88- uncommitted diff whose minus side
  carries `def _safe_getattr`. Citations are correct against
  the committed tree; rewriting them to dirt-only names would
  corrupt the record. HOLDS.
- (d) R11 qualified per state: the rewritten R11 names HEAD
  `_safe_getattr` (`:100`) / `_safe_flag` (`:108`) and WT-dirt
  `_attr` (`:92`) / `_flag` (`:97`) -- I verified HEAD `:108`
  (`def _safe_flag`) and both WT defs independently. HOLDS.

The rewritten D1 (record note CORRECTED, both errors struck, both
row substances re-verified clean) holds on this fresh evidence.

Intactness (artifact is untracked, so judged by reading, not by
git diff): `Status:` was `ready-for-verification/2` before this
tick's flip; the prior W2 section still quotes the ORIGINAL D1
wording and ends `revision-needed` (pre-revision bytes intact);
W1's non-D1 sections carry no revision markers and match the
dispatch description, with F1 freshness pins identical to mine;
no `^## Implementation` header (zero-edit holds; the one prose
mention is W2's own). Only sanctioned edits present: D1 + R11 +
Status.

Item scope still clean: HEAD unmoved at `5c3496e0`; `git diff
ITEM_BASELINE --name-only` is the plan edit alone; 6/6 WT pins
match dispatch (`nested_fetch.py` `c36826bb`, `nested_planner.py`
`b6ff0a0e`, `lateral_fetch.py` `a48cb0a4`, `single_parent_fetch.py`
`3a4bb89b`, `querysets.py` `3e392d48`, `walker.py` `4fd8077f`);
HEAD pins likewise; `git status --short` count 473 steady.

Gates (whole-package, shared venv): `uv run mypy` clean (119
files, exit 0); `uv run basedpyright` 0/0/0 (exit 0); `uv run
python scripts/check_any.py` 130/90 (exit 0) -- all identical to
the prior W2's record. Ruff on touched tracked paths: VACUOUS
(zero tracked `.py` touched; the item diff is the plan `.md`
edit alone; this tick's only edit is this scratch section plus
the Status flip).

Inheritance: I inherit the prior W2's endorsements (F1 census,
owner, all 12 exclusion substances + triggers, oracles,
challenges, matrix, enumeration, gate justification, cells
`unverified`, pending-None, index-rows-none, freshness) -- my
delta re-verification gives me no reason to doubt any of them,
and I disagree with the prior W2 on nothing load-bearing.

VERDICT: verified (plain -- no `proof:` remains, pending-None
stands).
