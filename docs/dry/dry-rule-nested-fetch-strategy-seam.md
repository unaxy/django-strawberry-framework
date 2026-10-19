# DRY review: `nested-fetch-strategy-seam`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is the nested-fetch strategy SEAM: how the selected
strategy crosses into execution. Three parts, re-derived below, not
inherited: (a) the strategy object (the `NestedConnectionStrategy`
protocol, the plan/False verdict contract, the three in-tree backends);
(b) the handoff to fetch paths (the single `strategy.plan` call with its
isolated candidate plan, the shared windowed floor every backend funnels
through, the request record that carries the window); (c) the boundary
where selection ends and fetching begins on both sides -- the planner
loop that builds one request per window and merges only on acceptance,
and the resolve-time wrapper that hands landed rows to
`resolve_connection` with a recoverable fallback.

Selection stays in the verified sibling
`nested-connection-strategy-selection` (f17), taken as input and never
re-litigated: `resolve_strategy`, `_select_nested_strategy`,
`nested_connection_strategy_setting`, `active_strategy`,
`StrategySelection`, and the extension/hint/frame consumers. The hint
value contract and the skip read stay in verified f15/f16. The
recognized-queryset skeleton (`RecognizedFetchQuerySet`: clone, rebind,
fetch-all dispatch, window signature) is the queued sibling
`recognized-fetch-queryset-skeleton`: this item converges the two
rebind call sites as consumers and excludes the machinery with a
contract difference (R1). The range arithmetic (`window_range_plan`,
`split_window_rows`, the fetch-mode assert, `FetchMode`) is the queued
sibling `window-range-fetch-derivation`, composed by name at every seam
touchpoint (R2).

Traced at HEAD bytes (`5c3496e0`) with a working-tree cross-check.
Four of the seven indexed files are dirty with concurrent work (the
bug-hunt truth migration, typing, maintainer deletions, the
windowed-fallback factory rework -- none of it in the plan's
`## Owned changes` ledger, which names none of the seven paths);
`optimizer/lateral_fetch.py` (`a48cb0a4`),
`optimizer/single_parent_fetch.py` (`3a4bb89b`), and
`utils/connections.py` (`5bf8f5fa`) are clean. The dirt attribution by
content: `nested_fetch.py` (4 hunks: truth import, one classifier
spelling, one suppression comment, the `resolve_strategy` truth
rewrite -- all f17/sibling ground, zero seam-region lines);
`nested_planner.py` (3 hunks: truth import, the M2M advisory silence,
the fallback-log `type(strategy).__name__` to `truth.name` spelling);
`plans.py` (3 hunks: truth import, `resolver_key`, one `_meta` read --
zero seam-region lines); `connection.py` (truth migration, the
`source` to `source_factory` fallback rework plus its call site, the
edge-class cache, the negative-cursor guard, keyset wording, identity
caches, one probe-condition reorder). Two seam-region lines differ in
spelling across the states (the planner log line, the fallback builder
signature); no hunk adds, removes, re-homes, or re-counts a seam site,
so every count below holds at both states. Line numbers cited are HEAD
lines. Prior file/family records were read as orientation and
adjudicated fresh; standing rejections enter only as triggers to
check, and every trigger below was checked against HEAD bytes.

Sites found, by role. One definition per seam sub-decision; every other
site composes by name.

- Definitions.
  - `django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionStrategy`
    (`:279`): the strategy interface. `name: str` plus `plan(request, plan)
    -> bool`; the docstring owns the verdict contract (`True` = directives
    attached, `False` = window left unplanned with no leakage, spec-033
    Decision 6) and the `to_attr` row contract (an ordered instance list
    carrying `_dst_row_number`, plus `_dst_total_count` when requested).
  - `django_strawberry_framework/optimizer/nested_fetch.py::attach_windowed_prefetch`
    (`:315`): the shared windowed floor. Threads the request into the one
    `apply_window_pagination` renderer and attaches the one windowed
    `Prefetch(lookup, queryset, to_attr)` (`:352`); the optional `wrap`
    rebinds the windowed body for a backend rider. Always returns `True`.
  - `django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionRequest`
    (`:227`): the handoff record. Fourteen fields carrying the resolved
    window; `__post_init__` (`:268`) enforces the probe/count exclusion
    through the shared `assert_window_fetch_mode_for`. One production
    construction site (the planner loop, `:1452`).
  - The plan-side handoff enforcement
    (`optimizer/nested_planner.py:1468-1483`): one isolated
    `OptimizationPlan` candidate per window, the single `strategy.plan`
    call (`:1469`), `merge_from` on `True` (`:1470`), no-leak plus the
    `strategy.name` refusal log on `False` (`:1477-1483`). The loop body
    belongs to the queued `nested-connection-plan-orchestration`
    sibling; the verdict handling is this seam's single enforcement
    site (R8).
  - `django_strawberry_framework/connection.py::_WindowedConnectionRows`
    (`:267`): the resolve-time marker (rows plus a zero-arg fallback).
    One construction site (`:2348`).
  - `django_strawberry_framework/optimizer/plans.py` window constants
    (`:797-809`): the single source of the `_dst_row_number`,
    `_dst_total_count`, `_dst_row_number_reversed`,
    `_dst_row_number_abs`, and `_dst_keyset_seek_count` spellings. Every
    other production occurrence is ``-quoted prose or docstring SQL.
- Consumers (compose by name, restate nothing).
  - The three in-tree backends: `WindowedPrefetchStrategy.plan` (`:380`,
    floor bare or with the single-parent wrap), `LateralPrefetchStrategy.plan`
    (`lateral_fetch.py:986`, floor with the lateral wrap or downgrade
    delegation to `WINDOWED_STRATEGY.plan`), `AutoNestedConnectionStrategy.plan`
    (`:414`, delegation to `LATERAL_STRATEGY.plan`). All three declare `name`;
    all three funnel every planned window through the floor.
  - `connection.py::_build_windowed_fallback` (`:295`): the single fallback
    builder (per-parent pipeline re-run, empty sidecars). One caller
    (`:2350`).
  - `connection.py::_consume_window` (`:657`): the single wrapper dispatch
    (`isinstance` at `:688`, shared bounds derivation, `_resolve_from_window`,
    `fallback()` recovery, one `_consume_fallback` tail). Single caller:
    the one `resolve_connection` override (`:1280`).
  - `connection.py::_window_rows_are_annotated` (`:2207`): the single
    integrity gate (row-number presence; count deliberately unprobed).
    One caller (the resolver handoff guard, `:2340`).
  - `connection.py::_resolve_from_window` (`:343`): the single
    edge/cursor/pageInfo/totalCount derivation from landed rows. Composes
    `split_window_rows`, `window_range_plan`, and the range-plan
    predicates by name (R2 ground).
  - The synthesized resolver's probe (`:2312-2331`): per-key attr first,
    shared attr second, both derived through the sibling to_attr grammar
    (R7); the strictness `_check_n1` call (`:2364`) reads the same probed
    attr under its own lazy-verdict contract (R16).
  - `plans.py::OptimizationPlan.merge_from` (`:340`): the generic
    plan-commit operation the handoff invokes; `append_prefetch_unique`
    (`:540`): the generic prefetch append the floor invokes.
- Shared vocabulary. The `WINDOW_*` constants above annotate the
  extension of the seam: `apply_window_pagination` (ORM render),
  `build_lateral_sql` + `_instantiate_row` (raw-SQL render),
  single-parent synthesis (Python render), and the resolve reads all
  name the same constants; presence-per-medium stays per codec (R11).
- Excluded decisions (different contract, recorded under Findings,
  never absorbed). The skeleton machinery (R1); the range/fetch-mode
  derivation (R2); the slice/bounds/seek derivation (R3); the child
  column projections (R4); hint-arm dispatch (R5); the attached-lookups
  read (R6); the to_attr grammar (R7); the orchestration loop (R8); the
  child-queryset classifier (R9); the join-shape vocabulary (R10); the
  row codecs (R11); the spec-builder gates (R12); the `__post_init__`
  twins (R13); the rebind wraps (R14); the keyset `plan` token (R15);
  the strictness read (R16); the walker prefetch sites and the `$`
  grammar (R17); the single-parent runtime gate (R18); the index
  advisory emission (R19).
- Oracles. `tests/optimizer/test_nested_fetch.py` (18 tests: strategy
  acceptance `:43`, floor attach `:52`, request probe/count rejection
  `:65`, conditional count `:79`, consumer-instance drive `:226`, plus
  the f17 selection rows); `tests/optimizer/test_lateral_fetch.py` and
  `tests/optimizer/test_single_parent_fetch.py` (backend execution);
  `tests/test_connection.py`, `tests/test_relay_connection.py`,
  `tests/test_keyset_connection.py` (resolve side: fast path, markers,
  probe, drift guards); `tests/optimizer/test_walker.py` (frame-bound
  strategy consumers, per the verified f17 record); live
  `examples/fakeshop/test_query/test_optimizer_auto_api.py` (per-field
  override both directions over `/graphql`, per f17),
  `test_single_parent_fastpath_api.py`, and the visibility suites.
  Every oracle spells its own expectation; none reads the owner's
  internals.
- Projections. The `nested_fetch.py` module docstring (the seam
  contract: Prisma lesson, planner/strategy split, the `to_attr` row
  promise, per-instance selection, auto design, indexing compact);
  the `NestedConnectionStrategy`, `NestedConnectionRequest`,
  `attach_windowed_prefetch`, and backend docstrings; the lateral and
  single-parent module docstrings (backend contracts); the planner
  handoff comments (`:1403-1425`, `:1486-1489`); the resolver and
  marker docstrings; `docs/README.md:334` (the pluggable-strategy
  paragraph); spec-033 and its rationale plus the build-033 record
  (contract sources).

Connected behavior examined: selection (f17, input only); hint shape
and skip (f15/f16, input only); the skeleton (queued sibling, R1);
window-range derivation (queued sibling, R2); slice resolution,
projections, hint dispatch, attached reads, the to_attr grammar, plan
orchestration, the classifier, join shapes, the advisory (queued
siblings, R3-R10, R19); the walker generic prefetches and the
`$` grammar (R17); the seal machinery (verified, read-only);
`KeysetSeek.plan` (R15).

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched. No other public surface
   carries a strategy seam: list fields plan unwindowed prefetches
   (`walker.py:1132`), mutations/forms/rest-framework have no fetch
   backends, and the only other `def plan(` (`keyset.py:162`) builds a
   value-seek plan under a disjoint contract (R15). The walker
   prefetch constructions (`:1132`, `:1439`, `:1467`) carry generic or
   consumer shapes, never a windowed `to_attr` (R17). No second seam
   exists to mirror.
2. Sync/async twins: discharged with reason. The plan side is sync-only
   by construction: the protocol's `plan` is a sync method, all three
   in-tree `plan` bodies are sync, and no async strategy-planning path
   exists. The window resolve branch is sync-only because its rows are
   already materialized: the one `resolve_connection` override funnels
   both cursor modes through the single `_consume_window`, whose
   window branch builds the connection from in-memory rows;
   `AwaitableOrValue` enters only in the non-window fallback pipeline
   (sibling ground: `_pipeline_async`, the keyset async slicer), which
   is the recovery tail both outcomes share, not a twin of the seam.
   No twin exists to drift.
3. Derived rather than repeated knowledge: searched. The `to_attr`
   strings are never concatenated at a seam site: the floor attaches
   `request.to_attr` (built once by the planner through the sibling
   grammar) and the resolver probes through the sibling grammar
   functions (R7). The row-attribute spellings are never re-derived:
   every code site names the `WINDOW_*` constants (C7 proof). The
   `strategy.name` read is a single telemetry read with a type-name
   fallback (`nested_planner.py:1481`); the registry keys are literals,
   never re-derived from `.name`. No site re-derives seam knowledge.
4. Inverse / round-trip pairs: searched, one pair, single-owned halves.
   The attach/read pair: the floor attaches the windowed `Prefetch`
   under the grammar name (one construction, `nested_fetch.py:352`),
   the resolver reads it back through the same grammar (R7). The
   wrap/recognize pair (rebind plus signature capture vs fetch-time
   recognition) belongs to the skeleton sibling: the seam contributes
   only the two one-line wraps (R14 trigger-clean). No second half of
   either pair exists.
5. Contracts restated in another medium: counted. Production (the six
   definitions above), oracles (seven package test files plus the live
   suites, each spelling its own expectation), projections (module and
   function docstrings, the README paragraph, spec-033). A seam change
   legitimately moves all three media together -- a contract change,
   not duplication.
6. Enforcement by omission: enumerated, no gap. Strategy
   implementations: the three in-tree backends all declare `name` and
   conform to the protocol signature; consumer-authored strategies pass
   the structural `plan` check (f17) while `name` stays best-effort
   telemetry via the defensive read -- absence degrades the log line,
   never a decision, so there is no unenforced member. Fetch paths:
   every planned window funnels through the floor (bare, wrapped, or
   via the downgrade/delegation chain -- proven by the three-body
   census). Resolve paths: the single `resolve_connection` override
   detects the marker for both cursor modes; the marker has exactly
   one producer. No seam member lacks its enforcement.

### Enumeration

Family item: the population is the rule's mechanism, swept
package-wide by spelling (`NestedConnectionStrategy`,
`NestedConnectionRequest`, `attach_windowed_prefetch`, `def plan(`,
`strategy.plan(`, `strategy_plan`, `to_attr`, `_WindowedConnectionRows`,
`_build_windowed_fallback`, `_consume_window`, `_resolve_from_window`,
`_window_rows_are_annotated`, `WINDOW_ROW_NUMBER`, `WINDOW_TOTAL_COUNT`,
`merge_from`, `.rebind(`, `_fetch_recognized_rows`, `window_range_plan`,
`split_window_rows`, `assert_window_fetch_mode`, `FetchMode`,
`relation_connection_to_attr`, `LATERAL_STRATEGY`, `WINDOWED_STRATEGY`,
`AUTO_STRATEGY`). 22 production files carry a hit: the 7 indexed
files plus `optimizer/walker.py` (grammar re-export, generic
prefetches, hinted-`to_attr` refusal, merge absorb -- R5/R7/R8/R17),
`optimizer/extension.py` and `optimizer/_context.py` (f17
selection-side, input only), `optimizer/hints.py` (f15/f17, input
only), `optimizer/join_taxonomy.py` (join vocabulary -- R10),
`keyset.py` (seek `plan` token plus one prose mention -- R15),
`types/resolvers.py` (strictness consumer -- R16),
`types/finalizer.py` (one prose mention),
`utils/querysets.py` (seal mechanics -- R17),
`utils/strings.py` (one `$`-grammar prose line -- R17),
`exceptions.py` (one fetch-mode prose mention -- R2),
`conf.py` (f17 plus the fast-path toggle read -- R18),
`optimizer/selections.py` (prose mentions -- R3),
`orders/sets.py` (one prose mention), and
`extensions/operation_state.py` (`rebind_on_resume`, a different
subject -- operation-scope binding, already rejected). Each was read
and either roled or excluded with a contract difference under
Findings. Nothing reachable was left unassigned: 6 definitions, 7
consumer groups, 1 shared vocabulary, 19 exclusions, 7 oracle files
plus live suites, projections.

### Challenges

Each variation axis of the seam rule, posited change plus the
authoritative definitions forced to move (consumers, oracles,
projections listed, never counted):

- C1, a fourth in-tree backend (e.g. a correlated-subquery strategy):
  one new declaration (a class with `name` + `plan`, registered by
  its own selection spelling). No existing definition moves: the
  protocol, the floor, the request, the handoff, and the resolve path
  are unchanged. Count 1 (the new member alone).
- C2, refusal recording gains context (e.g. the log must name the
  window bounds): the handoff enforcement site only
  (`nested_planner.py:1477-1483`). Strategies still return `False`;
  the protocol is untouched. Count 1.
- C3, a new window parameter through the floor (e.g. a second probe
  flag): the request record gains the field and the floor threads it
  -- one shape definition plus one attach definition, each
  single-owned, no second of either. Listed, not counted: the
  sibling-owned range derivation, the orchestration-owned
  construction, and the per-codec renders. Seam count: 1 + 1 across
  two rules, 1 per rule.
- C4, the attach shape changes (e.g. the windowed `Prefetch` gains an
  option): `attach_windowed_prefetch` only; all three backends inherit
  through the floor (bare, wrapped, downgrade, delegation). Count 1.
- C5, the fallback threads a new input: `_build_windowed_fallback`
  only, plus its single caller passing the argument (enforcement,
  listed). Count 1.
- C6, wrapper detection changes (e.g. the marker gains a field): the
  `_WindowedConnectionRows` definition only; the `isinstance` consumer
  and the single producer follow by name. Count 1.
- C7, a row-attribute rename (e.g. `_dst_row_number`): the
  `WINDOW_ROW_NUMBER` literal only (`plans.py:797`); the ORM, raw-SQL,
  Python, and resolve sites all name the constant, proven by the
  literal census (every other production occurrence is ``-quoted
  prose). Prose and oracle spellings move as listed media. Count 1.

Execution: none owed and none used. Every challenge above is decided
by an exact-match single-site census (definition counts, not
behavioral equivalence), which needs no execution; nothing lands, so
no failability proof is owed. All oracle citations are
static-reviewed. No workspace run, no shared-tree run was needed for
this zero-edit verdict.

## Findings

### F1: the nested-fetch strategy seam is single-owned (CONFIRM, zero-edit)

Contract + variation. Five sub-decisions, each owned once: (a) the
strategy interface and verdict contract (`NestedConnectionStrategy`:
`name` plus `plan`, `True` = attached, `False` = unplanned without
leakage, the `to_attr` row promise); (b) the plan-side handoff
enforcement (one isolated candidate per window, merge on `True`,
no-leak plus refusal log on `False`); (c) the shared windowed floor
(`attach_windowed_prefetch`: window the child queryset, attach the
one `Prefetch`, optional backend wrap); (d) the handoff record
(`NestedConnectionRequest`: fourteen fields, one construction site,
fetch-mode validation composed from the sibling owner); (e) the
resolve-time wrapper (marker, fallback builder, `isinstance`
dispatch, integrity gate, single row derivation -- one site each).
The rule varies on the backend set, the verdict recording, the floor
threading, the record shape, the fallback inputs, the detection, and
the row vocabulary -- one challenge each (C1-C7), every count 1.

Sites + roles. Under System trace: 6 definitions, 7 consumer groups
(3 backend bodies, fallback builder, wrapper dispatch, integrity
gate, row derivation, resolver probe, plan mechanics), 1 shared
vocabulary, oracles, projections.

Challenges. C1-C7, each count 1, all static census.

Owner + lifetime. Ownership is already at the narrowest cohesive
owner per sub-decision (principle 7): the interface, floor, and
record beside each other in `nested_fetch.py`, which every consumer
can import without reversing a dependency (the verified acyclic
runtime import the `StrategySelection` comment documents); the
handoff enforcement at its sole call site's loop in
`nested_planner.py`, which owns the per-key planning the verdict
serves; the marker, fallback, dispatch, gate, and derivation in
`connection.py` beside the `resolve_connection` override they serve;
the row vocabulary in `plans.py` beside the ORM renderer that mints
it. No stored derivation beyond the windowed-body queryset itself
(lifetime: the plan that carries it) -- nothing to move.

Migration. None owed: there is no second definition to migrate.
Every backend, probe, and reader already composes by name.

Distinct behavior. The excluded decisions below stay separate; the
f17 selection verdicts, the f15 value contract, and the f16 skip read
stay owned by their verified siblings (this item consumes the
selected strategy and honors the prior gates without restating any
of them).

Behavioral proof. The in-tree oracles pin every seam verdict
independently of the owner's spelling: strategy acceptance, floor
attach, request validation, conditional count, consumer-instance
drive, backend execution both dialects, the resolve fast path with
markers/probe/drift guards, frame-bound consumers, and the live
override rows. All citations static-reviewed; no `proof:` entry:
nothing lands, so no failability proof is owed.

Structural gate: no new gate owed, and the rule currently holds (the
HEAD/WT census above is the first-run check). The plausible bypass is
a second seam site -- a strategy attaching outside the floor, a
second `strategy.plan` caller, a second marker producer, or a second
row-vocabulary literal. No natural mechanical census closes that
beyond a bespoke literal/AST existence test per helper, which is the
forbidden shape; the in-tree oracles instead pin every contract
verdict (acceptance, attach, validation, probe inference, drift
fallback) so a divergent second site fails behaviorally where it
matters. Negative control reasoned: a hand copy of the floor body
passes every behavior oracle (the copy is correct), which is exactly
why no new oracle is proposed as a gate.

Coupling: none. No defect blocks landing because nothing lands.

Freshness: input pins under Judgment; any fingerprint change reopens
the finding. The WT dirt (truth migration, typing, fallback rework)
was censused at both states and moves no seam site count -- verdict
identical at HEAD and WT.

### Rejections and exclusions (contract difference + trigger each)

- R1, recognized-queryset skeleton (queued sibling
  `recognized-fetch-queryset-skeleton`): the clone/rebind/fetch-all
  execution machinery shared by backends (`_clone` survival, the
  `rebind` chain-then-reclass, `_fetch_all` dispatch,
  `_fetch_recognized_rows`, the window signature, `rebind_on_resume`
  excluded as a different subject). The seam's strategies consume it
  through the two one-line wraps; the seam never branches on a
  queryset class. Trigger: the seam branches on a queryset class, or
  the skeleton starts interpreting strategy identity.
- R2, window-range derivation (queued sibling
  `window-range-fetch-derivation`): the range arithmetic
  (`window_range_plan`, `WindowRangePlan.fetch_*`, `split_window_rows`,
  `assert_window_fetch_mode`, `FetchMode`). The seam composes it at
  every touchpoint: request/spec construction through
  `assert_window_fetch_mode_for`, the floor through
  `apply_window_pagination`, single-parent eligibility through a
  `plain_first_page` read, resolve classification through `split_`
  plus the range-plan predicates. Range math vs strategy carriage.
  Trigger: a seam site hardcodes a bound or shape instead of composing
  the plan.
- R3, plan-time slice resolution (queued sibling
  `plan-time-window-slice-resolution`): derives the bounds, seek, and
  count/probe mode the planner puts INTO the request. Slice computes;
  the seam carries. Trigger: the seam re-derives bounds from
  pagination arguments.
- R4, child column projections (queued siblings
  `scalar-only-window-projection`, `keyset-cursor-column-projection`):
  column inputs to `request.child_queryset`. The seam carries the
  queryset opaquely and never branches on its projection. Trigger: a
  projection feeds back into carriage (the floor or a backend branches
  on it).
- R5, hint-arm dispatch (queued sibling `optimizer-hint-dispatch`):
  the walker decides WHICH hint arm fires per relation; the seam
  carries the backend f17 selected. The hinted-Prefetch `to_attr`
  refusal (`walker.py:1278-1294`) guards consumer hints; the seam
  attaches package windows. Guard vs carriage. Trigger: dispatch
  resolves strategy instances, or the refusal starts naming window
  attributes.
- R6, attached-lookups read (queued sibling
  `attached-prefetch-lookups-read`): reads already-attached lookups
  downstream of planning. The seam WRITES the windowed attach; the
  sibling reads attached state. An inverse pair with no shared body.
  Trigger: the read interprets window attributes, or the write
  branches on attached state.
- R7, to_attr grammar (queued sibling
  `relation-connection-to-attr-grammar`): derives the shared and
  per-key attr names. The seam attaches under `request.to_attr` and
  probes through the grammar functions; the walker re-export composes
  the same functions. Names vs mechanics. Trigger: a seam site
  concatenates a `to_attr` string inline.
- R8, plan orchestration (queued sibling
  `nested-connection-plan-orchestration`): owns recognition, the
  refusal arms, request construction, metadata absorb, and resolver
  identities. The verdict handling inside its loop (candidate,
  single call, merge, log) is this seam's single enforcement site at
  the consumer boundary -- enforcement stays where the rule must
  hold, not a second definition. Trigger: a second `strategy.plan`
  caller appears.
- R9, child-queryset classifier (queued sibling
  `unwindowable-child-queryset-classification`): classifies shapes no
  strategy may window. Planning input plus execution gate; the seam's
  contract assumes a windowable request and never classifies.
  Trigger: a strategy or the floor starts classifying instead of
  receiving the verdict.
- R10, join-shape vocabulary (queued sibling `lateral-join-shape`):
  how the child joins (`DIRECT_FK` / `THROUGH_TABLE`). The request
  carries the descriptor opaquely; only the backend spec builders
  interpret it (execution, R12). Standing join_taxonomy-R6 /
  nested_fetch-R8 trigger-checked clean at HEAD: still two separate
  vocabularies (shape enum vs strategy registry plus instances).
  Trigger: the vocabularies merge into one enum.
- R11, row-attribute codecs (standing single_parent R-c /
  nested_fetch-R14): pristine-clone Python synthesis vs lateral
  `from_db` plus converters plus aliases vs the ORM annotation are
  three media rendering one named contract, not three definitions of
  it. Names shared through the constants (C7); presence conditions
  stay per medium (annotate vs SELECT vs setattr vs getattr) because
  the media admit no shared presence table without coupling
  independent renderers (principle 11). Trigger-checked clean at
  HEAD: still distinct mechanisms. Trigger: one medium decides a
  presence condition twice, or a shared presence table lands that all
  codecs compose.
- R12, spec-builder gates (standing single_parent R-d /
  nested_fetch-R13): `single_parent_spec` (degenerate-shape
  eligibility) vs `_build_lateral_spec` (SQL-expressibility) are not
  one gate; the custom-subclass arms share rationale, each stated at
  its site. Trigger-checked clean at HEAD: v1 scope unchanged
  (single-parent still refuses keyset, counted, reversed, M2M, and
  custom subclasses). Trigger: a scope change merging the gates.
- R13, the two `__post_init__` twins (standing nested_fetch-R11):
  `NestedConnectionRequest.__post_init__` and
  `LateralWindowSpec.__post_init__` are each one line composing the
  sibling-owned assert by name. Two consumers, not two definitions.
  Trigger-checked clean at HEAD. Trigger: either body adds logic
  beyond the delegation.
- R14, the two rebind wraps (standing nested_fetch-R12): the windowed
  and lateral `wrap` lambdas are one-line compositions with different
  subclass receivers. Two call sites, not two definitions.
  Trigger-checked clean at HEAD (exactly two wraps, both one line).
  Trigger: a wrap adds logic beyond `Subclass.rebind(qs, spec)`, or a
  third wrap shape appears.
- R15, `KeysetSeek.plan` token collision (`keyset.py:162`): binds
  decoded values into a seek plan. Shared `plan` token with the
  strategy method; disjoint contracts (value binding vs fetch
  directives), zero shared mechanism. Trigger: one calls the other.
- R16, strictness read vs resolver probe read
  (`types/resolvers.py::_check_n1` vs `connection.py:2328-2331`): two
  `getattr` reads of the probed attr under two contracts
  (lazy-query verdict vs row handoff). Reads, not rules; neither
  defines the attach. Trigger: strictness starts classifying rows.
- R17, walker prefetch sites and the `$` grammar: the generic child
  prefetch (`walker.py:1132`) and the shape-preserving rebuilds
  (`:1439`, `:1467`) carry unwindowed or consumer shapes under
  different contracts; the generated-Prefetch `$` grammar
  (`utils/strings.py:280`, querysets seal) governs descent paths, a
  different namespace from window attrs. Trigger: a walker site
  attaches a windowed `to_attr`, or one grammar parses the other's
  names.
- R18, single-parent runtime gate (the `SINGLE_PARENT_FAST_PATH`
  toggle plus the len==1 check): execution detail WITHIN the windowed
  backend, deciding whether the degenerate re-query runs at fetch
  time. The seam sees only plan-`True` plus contract-satisfying rows.
  Trigger: the gate selects a backend.
- R19, composite-index advisory (queued sibling
  `composite-index-advisory`): owns WHAT is emitted and its dedup.
  The handoff loop keys the field-static emission off first
  acceptance (the `advised` latch); the latch position is
  orchestration, the verdict is this seam's. Trigger: the advisory
  starts interpreting strategy identity beyond acceptance.

No new index rows owed: every member is the family rule itself, a
consumer of it, or a named queued/verified row above.

## Defects

D1 (record accuracy, verdict-neutral, for closeout homing -- never a
reopen): the verified f17 artifact's matrix axis 3 states the `.name`
class attributes "are unread in production (no `strategy.name`
reader package-wide)". A fresh HEAD trace finds exactly one
production read: `optimizer/nested_planner.py:1481`
(`getattr(strategy, 'name', type(strategy).__name__)` in the
refusal-log line; WT spelling `truth.name(type(strategy))`).
The read feeds telemetry only -- no decision consumes it -- so f17's
verdict-relevant claim (renaming a backend cannot move selection)
stands verbatim; only the absolute "no reader" wording is stale.
Owner: the f17 artifact record. Suggested closeout wording: "one
telemetry read, no decision reader".

No non-duplication production defect was found while tracing. The
no-ticked-row-wrong check passes: the plan's family row (owner
candidate `optimizer/nested_fetch.py::NestedConnectionStrategy`,
seven indexed files) matches HEAD -- the candidate re-derives to the
same module (protocol, floor, and record co-owned there), and every
indexed file carries a seam-role site (the fetch-mode assert and
splitter in `utils/connections.py` are composed-by-name touchpoints,
which is why that file is indexed here and owned in R2).

## Pending execution

None. No `proof:` entry (nothing lands, so no failability proof is
owed) and no `gate:` entry. The `--cell sharded` and `--cell pg`
cells get no verdict: this item makes no execution-backed claim, so
no cell run is owed (the seam's fetch paths do reach the database,
which is precisely why the inapplicable-by-construction label is NOT
claimed here). No workspace run and no shared-tree test run was used;
evidence is source reads plus exact-match grep censuses at HEAD
bytes with WT cross-checks.

## Judgment

CONFIRM: the nested-fetch strategy seam is single-owned -- five
sub-decisions, one definition each (C1-C7 all count 1), every backend,
probe, and reader composing by name -- and the consolidation is
therefore a proved zero-edit verdict: no tracked file changed, no
test added, no `## Owned changes` row owed, no `## Implementation`
section. Nineteen exclusions carry contract differences plus
triggers (R1-R19, including eight standing records trigger-checked
clean and eleven queued-sibling boundary rows); f15/f16/f17 verdicts
taken as input, never re-litigated; one verdict-neutral record note
(D1) for closeout homing; no new index rows.

Freshness fingerprints (HEAD `5c3496e0`; WT pins match dispatch):

- `django_strawberry_framework/optimizer/nested_fetch.py`:
  HEAD `bedaa76e`, WT `c36826bb`
- `django_strawberry_framework/optimizer/lateral_fetch.py`:
  HEAD/WT `a48cb0a4` (clean)
- `django_strawberry_framework/optimizer/single_parent_fetch.py`:
  HEAD/WT `3a4bb89b` (clean)
- `django_strawberry_framework/optimizer/nested_planner.py`:
  HEAD `8c3a45f5`, WT `b6ff0a0e`
- `django_strawberry_framework/connection.py`: HEAD `99969652`,
  WT `48de0243`
- `django_strawberry_framework/optimizer/plans.py`: HEAD `97a524e2`,
  WT `2e962ae2`
- `django_strawberry_framework/utils/connections.py`: HEAD/WT
  `5bf8f5fa` (clean)
- Adjacent readers censused (both states pinned):
  `optimizer/walker.py` (HEAD `13e1be20`, WT `4fd8077f`),
  `optimizer/extension.py` (HEAD `b7b6c434`, WT `8e3fe7c1`),
  `optimizer/_context.py` (HEAD/WT `274a138b`, clean),
  `optimizer/hints.py` (HEAD `f6776564`, WT `ee68ae03`),
  `optimizer/join_taxonomy.py` (HEAD `8026dc8d`, WT `aa289013`),
  `types/resolvers.py` (HEAD `09d40f34`, WT `a8c6a46e`),
  `types/finalizer.py` (HEAD `662826eb`, WT `0807fea7`),
  `utils/querysets.py` (HEAD `69ac3ea3`, WT `3e392d48`),
  `utils/strings.py` (HEAD `a326167d`, WT `f5ce0784`),
  `keyset.py` (HEAD `6af980b8`, WT `7d43c6b1`),
  `exceptions.py` (HEAD `7a4fb661`, WT `34e2e6be`),
  `conf.py` (HEAD `eccddc21`, WT `d239302a`),
  `optimizer/selections.py` (HEAD `f49ea7fa`, WT `1f6d3e04`)
- Searched population: the 25 spelling instruments under
  `### Enumeration`, run over `django_strawberry_framework/` at HEAD
  bytes via `git grep`, plus the oracle sweep over `tests/`,
  `examples/`, `docs/`
- ITEM_BASELINE `306d96f05c1b364e50d9e265725ef2bd3cca59d2`;
  no item-scoped diff (zero-edit; artifact untracked)

Type gates (observed, read-only, shared tree, WT bytes): `uv run
mypy` clean (`Success: no issues found in 119 source files`);
`uv run basedpyright` clean (`0 errors, 0 warnings, 0 notes`);
`uv run python scripts/check_any.py` clean (`130 allowed use(s) of
Any at 90 site(s)`). Zero-edit verdict, so no symbol was added,
moved, or removed; the gates confirm the verdict changes nothing
they check.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (skeleton-only peek: Status
`ready-for-verification/1`, Run `0.0.15 2026-10-01-9`, no
`## Implementation`, 634 lines). All pins below are Worker-2's own
re-derivation at HEAD `5c3496e0` bytes unless marked WT.

### W2 site census (fresh exact-match grep, whole package)

S1. Seam protocol: `optimizer/nested_fetch.py::NestedConnectionStrategy`
(1 def: `plan(request, plan) -> bool` + `name: str`, lines 280-297).
S2. Backend `plan` bodies (3, each its backend's own fetch decision, not
copies): `WindowedPrefetchStrategy.plan` (nested_fetch.py:381),
`AutoNestedConnectionStrategy.plan` (nested_fetch.py:415),
`LateralPrefetchStrategy.plan` (lateral_fetch.py:986).
S3. `.plan(request, ...)` production call sites (3):
`nested_planner.py:1479` (the handoff enforcement: fresh
`OptimizationPlan`, merge only on `True`), `lateral_fetch.py:990`
(lateral downgrade returns `WINDOWED_STRATEGY.plan`, verdict composed),
`nested_fetch.py:421` (auto delegates to `LATERAL_STRATEGY.plan`,
verdict composed). The latter two return the inner verdict verbatim;
they are composition, not a second enforcement.
S4. Request record: `NestedConnectionRequest` (1 def, nested_fetch.py:228;
`__post_init__` composes `assert_window_fetch_mode_for` by name); SOLE
construction site `nested_planner.py:1462`.
S5. Shared floor: `attach_windowed_prefetch` (1 def,
nested_fetch.py:316); call sites (3): nested_fetch.py:389 (bare),
nested_fetch.py:390 (single-parent wrap), lateral_fetch.py:993
(lateral wrap). Always returns `True` (the "planned" verdict).
S6. Recognized-fetch skeleton: `RecognizedFetchQuerySet` (1 def,
nested_fetch.py:148); subclasses (2): `LateralQuerySet`
(lateral_fetch.py:482), `SingleParentWindowQuerySet`
(single_parent_fetch.py:171); `rebind` call sites (2, both as the
floor's `wrap=` lambda): lateral_fetch.py:996, nested_fetch.py:393;
`_fetch_recognized_rows` overrides (2, distinct recognizers, not
copies): lateral_fetch.py:496, single_parent_fetch.py:187.
S7. `_fetch_all` override (1, the skeleton's
recognized-rows-or-windowed-body contract, nested_fetch.py:214). No
async twin: Django's `QuerySet.__aiter__` awaits
`sync_to_async(self._fetch_all)()` (verified in
`.venv/lib/python3.14/site-packages/django/db/models/query.py:437-441`),
so the one body serves both colors.
S8. `unwindowable_child_queryset_reason` (1 def, nested_fetch.py:94);
consumers (3, first-gate reuse by name): nested_planner.py:1301,
lateral_fetch.py:640, single_parent_fetch.py:244.
S9. `active_strategy` (1 def, nested_fetch.py:489); sole production
reader `nested_planner.py:240` (via `_select_nested_strategy`).
S10. `resolve_strategy` (1 def, nested_fetch.py:437); readers:
nested_planner.py:239, extension.py:1018/:1045, hints.py:108 -- all
f17 SELECTION ground, taken as input.
S11. `.name` identity: protocol decl (1, nested_fetch.py:293); member
attrs (3, per-backend data, expected): nested_fetch.py:379
(`"windowed"`), nested_fetch.py:413 (`"auto"`), lateral_fetch.py:984
(`"lateral"`). Production readers of a strategy's name: exactly 1 --
`getattr(strategy, 'name', ...)` in the refusal-log line
(HEAD `nested_planner.py:1481` spelling
`type(strategy).__name__`, WT `nested_planner.py:1491` spelling
`truth.name(type(strategy))`), feeding `_log_connection_fallback`
-> `logger.debug` (telemetry only; no decision branches on it).
Census instrument: `grep -rn "getattr(strategy"` package-wide = 1
hit; `grep -rn "STRATEGY.plan|.plan(request|strategy.plan("` = the
3 S3 sites; `grep -rn "NestedConnectionRequest("` = the 1 S4 site.
S12. Row-contract read side: `connection.py::_resolve_from_window`
(the `to_attr` consumer: `_dst_row_number` / `_dst_total_count`) --
a resolve-time consumption decision, distinct contract, not a
second fetch definition.
S13. Fetch-mode guard: `assert_window_fetch_mode_for` (1 def,
utils/connections.py:554); in-seam callers (2, both `__post_init__`
composing by name): nested_fetch.py:277, lateral_fetch.py:245.
(The ORM-window entry `apply_window_pagination` takes the
plan-carrying `assert_window_fetch_mode` variant -- window-range
sibling ground.)

### W2 challenges (posited before reading Findings; each stresses count-1)

- C-W1, fourth backend (e.g. a portable correlated-subquery
`"correlated"`): new class + new `plan` body (expected: new
backend behavior) + one registry row (f17 ground); consumes the
request record, the floor, and the skeleton by name. Seam defs
forced: 0 new protocol / request / floor defs. Count stays 1 each.
- C-W2, split the bool verdict contract (e.g. `plan` returns a
refusal reason instead of `bool`): the contract is defined once
(protocol signature + docstring, 1); the handoff (S3-first) and
the two delegations (S3-rest, verbatim pass-through) adapt as
consumers. No second verdict definition exists to move. Count 1.
- C-W3, second request record (e.g. split keyset fields into a
sibling record): today 1 def + 1 construction site + 4 consuming
bodies (3 plans + 2 spec builders share the one shape); a fork
would be a NEW rule, not a latent second owner. Count today 1.
- C-W4, new window parameter threaded to every backend: the floor
(S5) owns the `apply_window_pagination` argument threading once;
the request gains one field (1 def); spec builders adapt. Count 1.
- C-W5, rename/drop a strategy `.name`: protocol decl (1) + 3
member attrs (principle-1 member data, not copies) + 1 telemetry
reader (S11). No decision reader exists. Count of the identity
rule: 1 (the protocol decl).
- C-W6, a second handoff enforcement (another caller making
plan/no-plan merge decisions): none exists; S3 has 1 enforcement
+ 2 verbatim delegations. Count 1.
- C-W7, lateral develops its own fetch-mode exclusion: today
both `__post_init__`s compose the one guard (S13); a split would
CREATE a second def. Count today 1.
- C-W8, async iteration path: Django routes `__aiter__` through
the one `_fetch_all` (S7); no twin to drift. Count 1.

### W2 owner (principle 7, derived not inherited)

`optimizer/nested_fetch.py::NestedConnectionStrategy`. The protocol,
the request record, the floor, the skeleton, and two of three
backends already live in `nested_fetch.py`; every legitimate
consumer (planner, lateral, single-parent, hints, extension,
_context) already depends on it, so no dependency reverses; it is
the narrowest cohesive module all of them can import. The
resolve-time row reader (`connection.py::_resolve_from_window`)
stays a consumer (distinct resolve decision); the fetch-mode
guard stays owned by `utils/connections.py` (window-range
sibling); selection stays f17 ground. This matches the plan's
owner candidate.

### W2 matrix pre-discharge (target's real surface)

1. Cross-flavor: the seam is optimizer-internal; the GlobalID
"type-slot vocabulary" (f17 ground) never resolves to a strategy.
No second flavor fetches nested connections. Searched via the S3
census (3 sites, 1 enforcement).
2. Sync/async: single-bodied by framework construction (S7); no
twin exists.
3. Derived knowledge: `.name` read once, telemetry-only (S11);
unknown-name message derives from the registry (f17 ground). No
site re-derives request/floor/verdict.
4. Round-trip: request->plan and spec->SQL are one-way per
backend; the planned-vs-fetch signature check
(`window_predicate_signature`) is a fail-closed proof, not an
inverse grammar. No inverse half.
5. Other media: oracles (tests/optimizer/test_nested_fetch.py,
test_lateral_fetch.py, test_single_parent_fetch.py, test_hints.py,
test_walker.py, _builders.py; tests/test_lateral_pg_parity.py,
tests/test_keyset.py, tests/base/test_conf.py) spell
expectations; projections (module + function docstrings) describe.
Listed, not counted; a seam change legitimately moves all three.
6. Omission: every PLANNED nested connection flows through the
single handoff (S3-first); the per-parent fallback in
connection.py is the intentional non-seam path (refusal
fallback, distinct contract), not a missing enforcement.

### W2 zero-edit + typing pre-position (before reading Findings)

Tracked diff check (done pre-read): `git diff ITEM_BASELINE
(306d96f0...) --name-only` = `docs/dry/dry-0_0_15.md` alone; 7/7
WT pins match dispatch pins; artifact untracked (expected for a
new scratch file). No `## Implementation` (skeleton grep: 0).
W2 searched for a real consolidation independently (C-W1..C-W8):
none found; every sub-decision counts 1 with a landable owner
nowhere (each hypothetical second def would be a NEW rule, and
no landing hits concurrent dirt because no landing is owed).
On the cells typing question (DRY.md binary: `unverified`
unless `inapplicable by construction` with a stated reason): W2's
pre-reading position is that the binary binds -- a zero-run item
whose fetch paths reach the database (S7/S12 execute real SQL
under Postgres/SQLite) cannot be `inapplicable by construction`,
so the cells MUST read `unverified` (with the sharded/pg
authorization note), NOT a third "no verdict" option. Awaiting
W1's text to rule finally.

### W2 reconciliation (after reading Findings; every difference explicit)

Scope framing: W1's seam is broader than the W2 pre-trace -- it
counts the resolve-time wrapper (marker, fallback builder,
`isinstance` dispatch, integrity gate, row derivation) and the
`WINDOW_*` vocabulary as seam definitions, where W2 pre-registered
only the resolve derivation as a consumer (S12). No factual
conflict: W2 verified every additional definition fresh at BOTH
states (HEAD defs connection.py:267/:295/:343/:657/:2207,
`isinstance` :688, singletons :2348/:2350/:2340/:1349-inside-
`:1280`-override; WT singletons :274/:302/:356/:669/:701/:2225/
:2347/:2355/:2357/:1396; plans.py constants HEAD :797/:798/:799/
:807/:808; C7 literal census reproduced: all 52 non-constant
production occurrences are ``-quoted prose/docstring-SQL, code
sites name the constants). AGREE: the wrapper parts exist solely
to land strategy rows (one producer, one consumer each) and the
vocabulary is single-sourced -- W1's six-definition set is
correct and W2's narrower frame is subsumed. Consequence for the
owner: W1's per-sub-decision owners (interface/floor/record in
nested_fetch, handoff in the planner loop, wrapper in
connection.py, vocabulary in plans.py) are compatible with the
single family owner `nested_fetch.py::NestedConnectionStrategy`
-- enforcement stays at its boundary per the DRY consumer-site
rule; the plan row is not wrong. ENDORSED.

F1 sub-decisions (all five + owner): ENDORSED. (a) interface +
verdict contract 1 (S1; C-W2 stresses the split, count stays 1);
(b) handoff enforcement 1 (S3: 1 enforcement + 2 verbatim
delegations; C-W6); (c) floor 1 (S5: 1 def, 3 composed calls;
C-W4); (d) request record 1 (S4: 1 def, sole construction HEAD
:1452 / WT :1462; C-W3); (e) resolve wrapper 1 site each
(singletons above; C5/C6). C1-C7 all reproduce count 1; W2's
harder C-W1..C-W8 (fourth backend, verdict split, second record,
new param, name drop, second enforcement, guard split, async
color) all count 1 with no landable second owner. Owner
`nested_fetch.py::NestedConnectionStrategy` re-derived
independently (principle 7: co-located protocol/floor/record,
all consumers already depend on it, no reversal). ENDORSED.

R1-R19: ALL ENDORSED. Eleven queued-sibling rows (R1/R2/R3/R4/
R5/R6/R7/R8/R9/R10/R19) name REAL open plan rows, each `- [ ]`
undispatched, each with a contract difference + a concrete
trigger (verified row by row against `## Families`). Eight
standing records trigger-checked clean, each label confirmed to
exist (nested_fetch file artifact R8/R11/R12/R13/R14,
single_parent R-c/R-d, join_taxonomy R6) and each check
reproduced fresh: vocabularies still separate (R10); three codec
media still distinct mechanisms (R11); v1 scope pins hold --
single_parent still refuses keyset/counted/reversed/M2M/custom
(read fresh), lateral downgrade arms unchanged (R12); both
`__post_init__` one-line delegations (R13); exactly two one-line
wraps (R14, HEAD :996/:392, WT :996/:393). R15 (`KeysetSeek.plan`
disjoint value binding), R16 (two reads, two contracts --
resolvers.py:261 vs the :2328/:2331 probe), R17 (walker generic
prefetches :1132/:1439/:1467 + `$` prose strings.py:280), R18
(toggle + len==1, execution inside the windowed backend) --
sites verified, differences + triggers concrete. ENDORSED.

f15/f16/f17 input boundary: ENDORSED. Selection machinery
consumed as input, never re-counted; hint shape/skip untouched;
nothing dropped (touchpoints acknowledged); D1 touches only f17's
record wording, verdict-neutral, homed to closeout, never a
reopen. Nothing re-litigated.

D1: ENDORSED in full. f17 axis-3 wording quoted verbatim
(artifact lines 152-153); the HEAD :1481 read verified byte-exact
(`getattr(strategy, 'name', type(strategy).__name__)`); WT
spelling `truth.name(type(strategy))` at :1491 verified;
package-wide `getattr(strategy` census = exactly 1 hit;
telemetry-only verified (`_log_connection_fallback` ->
`logger.debug`, no decision consumer); verdict-relevant claim
intact (registry keys are module-owned plain-str literals,
linear content-equality scan -- renaming a backend cannot move
selection). Owner routing to the f17 ARTIFACT record: CORRECT
(production code is right; f17's prose is stale). Suggested
closeout wording "one telemetry read, no decision reader":
ACCURATE, endorsed. Supplement O3 (below): f17 axis 4 shares the
staleness -- closeout should reword both axes.

Matrix: ENDORSED on all six axes (axis 1: S3 census, no second
seam, keyset token disjoint; axis 2: conclusion endorsed --
W1's plan+resolve reason covers the stated surface and W2's S7
independently closes the adjacent fetch color via Django's
`__aiter__` -> `sync_to_async(_fetch_all)` single body, no twin;
axis 3: C7 census + single telemetry read reproduced; axis 4:
attach/read halves single-owned, wrap/recognize homed to R1;
axis 5: 6 defs + 7 oracle files (all exist) + live suites +
projections, counted not duplicated; axis 6: 3 backends declare
`name`, consumer `name` best-effort via the defensive read,
floor funnel proven, single override + single producer).

No-new-index-rows: ENDORSED. Every member maps to the family
rule, a consumer, an existing open row, a verified sibling, a
standing rejection, or a recorded-here exclusion; W2's
independent trace found no unrowed rule.

Pending-"None": CORRECT -> plain `verified`. No `proof:` owed
(static census verdict, nothing lands, no failability proof
exists to run); no `gate:` owed (endorsed per the verified f17
precedent: no natural census beyond the forbidden bespoke
existence-test shape; behavior oracles pin every verdict;
negative control reasoned; first-run census holds -- reproduced
by W2). No `proof:`/`gate:` entry strings in the artifact
(grep-clean).

Structural gate + negative control: ENDORSED (identical in shape
to the verified-accepted f17 position; first-run check
reproduced fresh by W2 at both states).

Freshness: ENDORSED and comparable. 7/7 indexed pins + 13/13
adjacent pins recomputed identical at both states;
ITEM_BASELINE recorded; searched population stated (with O1
correction); oracles + contract sources named. Any fingerprint
change reopens.

Cells TYPING RULING (explicit): W1's third option ("no verdict")
is REJECTED. DRY.md "Tests" states the binary: without the maintainer's
word the cells stay `unverified` unless `inapplicable by
construction` with a stated reason. W1 concedes the fetch paths
reach the database and explicitly does NOT claim inapplicable --
so the cells MUST read `unverified` (sharded + pg await the maintainer's
word; the gate lists them). W1's underlying facts are all
correct (no run owed, DB reachable, inapplicable not claimed);
only the label is off. RULING FOR WORKER-0: record both cells
`unverified`. This changes no verdict: the CONFIRM rests on
source-level censuses identical across cells, and no `proof:`
exists, so Status stays plain `verified`. Both positions are on
record (W1: no-verdict; W2: unverified per the canonical
binary); the canonical text resolves it -- no maintainer routing
needed, no W1 edit needed (scratch label; W2 ruling governs).

W2 observations (scratch nits, verdict-neutral, f17-O1/O2
precedent -- no Defects entry, no revision):
O1: `### Enumeration` claims "22 production files carry a hit"
under the 25 instruments; W2's faithful reproduction (same 25
patterns, `git grep` at HEAD tree AND WT) yields 18 files at
both states. The 4 deltas (join_taxonomy.py, conf.py,
orders/sets.py, extensions/operation_state.py) carry no
instrument hit -- they were reached by adjacent traces (R10
vocabulary, R18/f17 toggle, C7 raw-spelling prose, R1-adjacent
`rebind_on_resume`) and are all correctly homed, so nothing is
unassigned; only the "carry a hit" count is overstated (18 via
instruments + 4 via adjacent traces = 22 examined).
O2: two pin-range precisions -- C7's "plans.py:797-809" block is
:797/:798/:799/:807/:808 (trailing :809 is blank); nested_fetch
dirt is 5 git hunk headers / 4 semantic changes (the
resolve_strategy rewrite spans 2 headers), all truth-migration
in f17/sibling ground, zero seam-region lines -- substance
verified.
O3: D1's closeout homing should cover f17's matrix axis 4 as
well as axis 3: axis 4's "no production path maps an instance
back to a name" is stale by the same single telemetry read (an
instance->name mapping for logging); its verdict-relevant claim
(selection is one-way, no inverse half feeds a decision) stands
likewise. Suggested closeout covers both axes with D1's wording.

Zero-edit + AGENTS.md: CONFIRMED. No `## Implementation`
(grep 0); 7/7 WT pins match dispatch pins; `git diff
ITEM_BASELINE --name-only` = `docs/dry/dry-0_0_15.md` alone (the
plan edit); status count 466 = 465 + the artifact
(`git status --short | wc -l`, 272 untracked + 194 modified);
HEAD unmoved (`5c3496e0`). Item-scoped diff is the plan edit
alone (Worker-0's text, not W1's) + the untracked scratch
artifact (raw `path:NN` allowed, no style cleanup owed). Ruff on
touched tracked paths: VACUOUS (zero `.py` touched -- no run
owed, none run). No ASCII/.py, pragma, or provenance concern
(zero-edit). Type gates re-run whole-package by W2 (shared
tree, WT bytes): `uv run mypy` clean (119 files), `uv run
basedpyright` 0/0/0, `uv run python scripts/check_any.py`
130/90 -- all exactly matching W1's claimed figures.

Independent consolidation search: W2 posited eight seam changes
(C-W1..C-W8, incl. ones W1 did not: verdict-contract split,
second enforcement, guard split, async color) -- every count is
1, no landable second owner exists, no landing owed, no
concurrent-dirt intersection. No `revision-needed` candidate;
no `blocked` (no verdict-affecting disagreement -- the typing
ruling and O1/O2/O3 are resolved on record by canonical text
and fresh evidence, requiring no W1 action).

VERDICT: verified (plain).
