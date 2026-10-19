# DRY review: `window-range-fetch-derivation`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is window-range fetch derivation: how a window
range plan is derived for fetching -- a slice `(offset, limit,
reverse)` (f19's output, entering here as INPUT) into the fetch
decisions every window dialect renders and the resolver consumes:
normalized bounds, the ambiguous-shape marker decision, the
count-free probe decision and its fetch bounds, the `FetchMode`
count/probe policy, the probe/count mutual-exclusion gate, and the
page-vs-sentinel row split. Re-derived fresh at WT bytes
(`5c3496e0` + concurrent dirt), not inherited: the population is
the mechanism (the builder, the plan record + its derived
bounds/predicates/mode, the two shape predicates, the enum, the
gate + delegate, the splitter, the sentinel count, every
bound-arithmetic spelling), swept package-wide by exact-match
spelling, in every module, not just the seven indexed files.

What the trace found is an already-consolidated rule in ONE home
with seven consumer groups composing by name:

- The owner in `utils/connections.py` (clean at HEAD blob
  `5bf8f5fa`): the builder `window_range_plan`, the record
  `WindowRangePlan` (+ `_probe_increment`, `fetch_upper_bound`,
  `fetch_limit`, `probe_shape`, `constant_false_shape`,
  `fetch_mode`), the shape predicates `_is_probe_shape` and
  `is_ambiguous_empty_window`, the `FetchMode` enum, the gate
  `assert_window_fetch_mode` + delegate
  `assert_window_fetch_mode_for` (+ `_RawWindowArguments`), the
  splitter `split_window_rows`, and the sentinel count
  `NEXT_PAGE_PROBE_ROWS`. 16 member definitions in 12
  sub-decisions, each count 1 (Challenges C1-C10 + carriers S12).
- The consumers, all proven composing by name (zero re-derivation):
  the ORM renderer (`plans.py::apply_window_pagination` +
  `_apply_keyset_counted_window`), the lateral SQL renderer
  (`lateral_fetch.py::build_lateral_sql`), the single-parent fast
  path (`single_parent_fetch.py::single_parent_spec` +
  `_fetch_single_parent_rows`), the planner fetch-mode decision
  (`nested_planner.py::plan_connection_relation` loop), the
  strategy-seam carriers (`nested_fetch.py::NestedConnectionRequest`
  + `attach_windowed_prefetch` threading + `LateralWindowSpec`,
  each gated at construction), the resolve-side reconstruction +
  split + flags (`connection.py::_consume_window` /
  `_resolve_from_window`), and the value-domain keyset page
  (sentinel count only).

Verified siblings enter as INPUT and are never re-litigated: f19
(`plan-time-window-slice-resolution`) owns the slice the builder
consumes (`ConnectionWindowBounds` from `derive_*_window_bounds`;
the planner loop and the resolve probe both compose it by name);
f17 (`nested-connection-strategy-selection`) owns strategy
selection (`resolve_strategy`, called once per field, upstream of
the per-window loop); f18 (`nested-fetch-strategy-seam`) owns the
request/wrapper seam that carries the raw slice
(`NestedConnectionRequest`, `LateralWindowSpec`,
`attach_windowed_prefetch`, the windowed floor). f15/f16 hint
shape/skip and f12/f13 policy bounds enter transitively through
the planner, never re-derived here.

Queued siblings converge or exclude with a contract difference,
never absorbed silently: `nested-connection-plan-orchestration`
converges as the orchestrator consumer; the recognition cluster
converges onto `recognized-fetch-queryset-skeleton`;
`scalar-only-window-projection`,
`keyset-cursor-column-projection`, `window-partition-resolution`,
`lateral-join-shape`, `prefetch-attach-column-projection`,
`unwindowable-child-queryset-classification`,
`composite-index-advisory`, `relation-connection-to-attr-grammar`,
`optimizer-hint-dispatch`, `attached-prefetch-lookups-read` are
each excluded under Findings on a projection / partition /
selection vs range-derivation difference with a stated trigger.

Prior record, adjudicated fresh (never evidence): the run-6 item
that named 9 symbols into this open family, transcribing nothing.
The fresh census below re-derives membership symbol by symbol (16
member definitions, 12 sub-decisions) and CONFIRMS the owner
candidate `utils/connections.py::window_range_plan`. Flat symbol
counts from prior runs are not reproduced -- the verdict rests on
the challenge counts in C1-C10.

## Verification

### Matrix

Each axis searched or ruled inapplicable, for the family as a whole.

1. Cross-flavor policy mirroring. Package-wide exact-match greps
   for the family vocabulary (`window_range_plan`,
   `WindowRangePlan`, `split_window_rows`, `FetchMode`,
   `fetch_mode`, `assert_window_fetch_mode`,
   `is_ambiguous_empty_window`, `NEXT_PAGE_PROBE_ROWS`,
   `fetch_upper_bound`, `fetch_limit`, `add_marker_rows`,
   `next_page_probe`, `keyset_counted`, `WINDOW_ROW_NUMBER`,
   `offset + limit`, `sys.maxsize`) return production hits only
   in the 9 files enumerated below; every other flavor directory
   (`types/`, `filters/`, `orders/`, `mutations/`, `forms/`,
   `rest_framework/`, `testing/`, `middleware/`,
   `management/`, `auth/`, plus `relay.py`, `views.py`,
   `schema.py`, `list_field.py` except as noted) greps 0. The one
   adjacent flavor with offset/limit machinery is
   `list_field.py` (ordered-offset list paging: exact-int
   validation, the deterministic-order guard, plain slicing) --
   no window functions, no markers, no probes, no plan record
   (R9). The value-domain keyset page
   (`connection.py:1139-1143`) shares ONLY the sentinel COUNT by
   name (`page_size + NEXT_PAGE_PROBE_ROWS`, unconditional by
   documented design); its page derivation is a different rule
   (R7). No mirror rule found in any sibling flavor.

2. Sync/async twins. The derivation is pure: `utils/connections.py`
   carries zero `async def`, and each family member has exactly
   one `def` (single-`def` census per member; no `async` twin of
   the builder, the mode, the gate, or the splitter exists
   package-wide). Both resolve colors funnel through the one
   sync window branch: `_consume_window` has exactly one caller
   (`connection.py:1396`), `_resolve_from_window` exactly one
   caller (`:744`). No twin derivation; nothing to unify.

3. Derived rather than repeated knowledge. Four candidates, each
   discharged (not counted):
   - `keyset_counted` construction (`plans.py:1134`, from request
     fields) vs inference (`connection.py:482`, from physical
     rows): same meaning from disjoint evidence in disjoint
     domains; each single in its domain; agreement enforced at
     runtime by the drift guards (`connection.py:570-602`),
     which fall back per-parent (byte-identical) instead of
     diverging silently (R2).
   - `next_page_probe=count_absent` (`connection.py:481`):
     consumer input inference, not a bound derivation (R3).
   - The marker `rn == 1` literals (3 rendering arms): shared
     VALUE with no joint change obligation -- any real witness
     change rewrites each arm bespoke (Q-object vs SQL text vs
     abs annotation), and a single-arm change fails existing
     edge oracles loudly (R1).
   - The `None`-guard spellings (`upper_bound is not None` in
     the ORM arms vs `fetch_upper_bound is not None` lateral):
     reliance on the owned `None <-> None` equivalence, never
     restated (R12).

4. Inverse / round-trip pairs. Build vs parse, both single:
   renderers emit range predicates from the plan; recognizers
   SKIP window quals through the single `_is_window_qual`
   (`lateral_fetch.py:708`, imported by `single_parent_fetch.py`)
   and prove the planned range through the single
   `window_predicate_signature` (`lateral_fetch.py:772`) --
   neither parses bound VALUES, so neither re-derives the range
   (R4, home `recognized-fetch-queryset-skeleton`). The row
   classifier `split_window_rows` reads the plan's offset/upper
   bounds and never re-spells `rn == 1`. The lateral SQL text
   mirrors the ORM Q-objects branch for branch with parity
   oracles (`tests/test_lateral_pg_parity.py`,
   `tests/optimizer/test_lateral_fetch.py`), not a restated
   derivation. No encode/decode pair lives in this family (the
   cursor codec is `keyset.py`'s).

5. Contracts restated in another medium. A change to the range
   rule moves production (count 1, F1) + oracles (listed, never
   counted: `tests/utils/test_connections.py` owner pins,
   `tests/test_keyset.py` keyset semantics,
   `tests/optimizer/test_plans.py` ORM-window behavior,
   `tests/optimizer/test_lateral_fetch.py` + `test_nested_fetch.py`
   + `test_walker.py` + `test_selections.py` seam/planner prose
   and behavior, `tests/test_lateral_pg_parity.py` dialect
   parity, live `test_query/test_products_api.py` +
   `test_optimizer_auto_api.py` end-to-end windows) +
   projections (module + member docstrings, spec-033 Decisions
   4/5/6, `exceptions.py:224-239` error catalog, lateral
   module-docstring `:23` prose, test prose). Oracles spell
   literal outcomes (modes, flags, row lists), never read the
   owner they check.

6. Enforcement by omission. Family enumerated member by member;
   every window entry point is gated and every unrenderable
   shape is refused loudly, not omitted:
   - The probe/count gate fires at all 3 window entries:
     `plans.py:1142` direct, `NestedConnectionRequest` and
     `LateralWindowSpec` `__post_init__` via the shared
     `_for` delegate (`nested_fetch.py:277`,
     `lateral_fetch.py:245`).
   - The counted-keyset shape: ORM renders it (`plans.py:1134-1141`),
     lateral downgrades to windowed (`_build_lateral_spec:1053-1059`
     returns `None` before the sole `LateralWindowSpec(`
     construction at `:1153` -- "downgrade to windowed rather
     than grow a second marker/count arithmetic"),
     single-parent excludes keyset (`:137-138`), and
     reverse+keyset raises loudly (`plans.py:1128-1133`).
   - Single-construction censuses: `WindowRangePlan(` exactly
     once in production (`utils/connections.py:493`, zero in
     tests -- oracles build through the builder);
     `LateralWindowSpec(` once (`lateral_fetch.py:1153`);
     `NestedConnectionRequest(` once
     (`nested_planner.py:1462`; test builders construct
     fixtures, still gated by `__post_init__`).
   No member lacks its guard; no second site hides behind an
   absence.

### Enumeration

Family item: the population is the rule's mechanism, swept
package-wide by exact-match spelling (`window_range_plan`,
`WindowRangePlan`, `_is_probe_shape`,
`is_ambiguous_empty_window`, `FetchMode`, `fetch_mode`,
`assert_window_fetch_mode`, `assert_window_fetch_mode_for`,
`_RawWindowArguments`, `split_window_rows`,
`NEXT_PAGE_PROBE_ROWS`, `lower_bound`, `upper_bound`,
`fetch_upper_bound`, `fetch_limit`, `_probe_increment`,
`probe_shape`, `constant_false_shape`, `plain_first_page`,
`next_page_probe`, `keyset_counted`, `add_marker_rows`,
`offset + limit`, `sys.maxsize`, `RowNumber()`,
`WINDOW_ROW_NUMBER`, `WINDOW_TOTAL_COUNT`,
`WINDOW_ROW_NUMBER_REVERSED`, `WINDOW_ROW_NUMBER_ABS`,
`WINDOW_KEYSET_SEEK_COUNT`, `with_total_count=`,
`next_page_probe=`, `_resolve_from_window`, `_consume_window`,
`LateralWindowSpec(`, `NestedConnectionRequest(`,
`WindowRangePlan(`, `connection_count_required`,
`connection_total_count_selected`,
`connection_has_next_page_selected`, `_has_next_page_requested`,
`window_predicate_signature`, `_is_window_qual`,
`_window_rows_are_annotated`, `_reverse_order_by`). Hits land in
9 production files: the 7 indexed files plus
`optimizer/selections.py` (observer inputs + `FetchMode` prose --
composed, never re-derived) and `exceptions.py` (error-catalog
prose only). Each hit file was read and every symbol roled or
excluded with a contract difference under Findings. Grep-cleared
with a stated population (0 family-vocabulary hits):
`list_field.py` (offset/limit read as validation+guard+threading,
R9), `walker.py` (one `_optimizer_*` vocabulary collision, R14),
`keyset.py` (codec + seek carrier, f19/input), `relay.py`,
`optimizer/predicates.py`, `optimizer/extension.py` (no range
logic), and every remaining flavor directory (axis 1). Nothing
reachable was left unassigned: 16 member definitions in 12
sub-decisions, 7 consumer groups, 2 f-verified inputs (f19 slice,
f17/f18 selection+seam), 15 exclusions, 9 oracle files plus live
suites, projections.

### Challenges

Each variation axis of the range rule, posited change plus the
authoritative definitions forced to move (consumers, oracles,
projections listed, never counted). All line numbers are WT bytes
at `5c3496e0` in `utils/connections.py` unless named.

- C1, bound validity/normalization changes (e.g. a negative
  direct-call offset clamps instead of raising, or a second
  no-upper-bound sentinel joins `None`/`sys.maxsize`):
  `window_range_plan` only (`:477-482`). All 6 call sites follow
  by construction (0 re-spells). Count 1.
- C2, bound derivation changes (e.g. the reverse bound becomes
  offset-relative, or the keyset floor moves off row 0):
  `window_range_plan` only (`:483-484`). The 3 renderers and the
  resolve reconstruction read `lower_bound`/`upper_bound`
  fields, unmoved. Count 1.
- C3, the ambiguity rule changes, split per sub-decision: an
  offset/limit-shape change moves `is_ambiguous_empty_window`
  only (`:249-269`); a keyset-ambiguity change moves the
  `keyset_counted or ...` extension only (`:485`); a
  presence-gate change moves `:499` only. The direct
  `is_ambiguous_empty_window` caller census is exactly one
  (`:485`). Count 1 each.
- C4, the probe-shape rule changes (e.g. the bounded forward
  offset page stops probing): `_is_probe_shape` only
  (`:231-246`). The honor-gate (`:487-492` + `:501`) and
  `probe_shape` (`:380-385`) follow by name. Count 1.
- C5, the probe increment changes (sentinel depth 1 -> 2):
  `NEXT_PAGE_PROBE_ROWS` only (`:81`). `_probe_increment`
  (`:340`), both fetch bounds (`:352`, `:364`), and the
  value-domain page (`connection.py:1143`) follow by name.
  Count 1.
- C6, the fetch-mode policy changes (e.g. a fifth mode, or
  `PROBED` gains a further precondition): `fetch_mode` only
  (`:402-429`) + the `FetchMode` enum it returns. The planner's
  `COUNTED`/`PROBED` reads (`nested_planner.py:1460-1461`) and
  the resolver's shape-predicate reads follow. Count 1.
- C7, the probe/count exclusion changes (e.g. probe+marker
  composition narrows, or the error becomes a warning):
  `assert_window_fetch_mode` only (`:505-536`). The `_for`
  delegate (`:554-572`) and all 3 entry-point calls follow.
  Count 1.
- C8, the row-split classification changes (e.g. the composed
  page keeps the marker): `split_window_rows` only (`:575-635`).
  The single consumer (`connection.py:509`) follows. Count 1.
- C9, the constant-false rule changes (e.g. a bounded shape
  joins the constant-false set): `constant_false_shape` only
  (`:388-400`). `fetch_mode` (`:427`) and the resolver drift
  guard (`connection.py:582`) follow by name. Count 1.
- C10, the plain-first-page rule changes (e.g. it admits
  `offset == 0` with `limit is None`): `:486` only. The lateral
  fast branch (`lateral_fetch.py:397`), single-parent
  eligibility (`single_parent_fetch.py:152`), and the probe
  predicate (`:487-492`) follow. Count 1.

Execution: none owed and none used. Every challenge above is
decided by an exact-match single-site census (definition counts,
not behavioral equivalence), which needs no execution; nothing
lands, so no failability proof is owed. All oracle citations are
static-reviewed. No workspace run and no shared-tree test run was
needed for this zero-edit verdict; the three static type gates
were re-run read-only in the shared venv (mypy Success/119,
basedpyright 0/0/0, check_any 130/90 -- all exit 0).

## Findings

### F1: window-range fetch derivation is single-owned (CONFIRM, zero-edit)

Contract + variation. One rule: a slice `(offset, limit,
reverse)` plus the probe request and the counted-keyset mark
resolve into the fetch plan every window dialect renders and
the resolver consumes. Legitimate variation axes: bound
validity/normalization (C1), bound derivation (C2), ambiguity
(C3), probe shape (C4), probe increment (C5), fetch-mode policy
(C6), probe/count exclusion (C7), row split (C8), constant-false
(C9), plain-first (C10), and the record/enum/protocol carriers
(S12). 16 member definitions in 12 sub-decisions, each count 1.

Sites + roles. Definitions (all `utils/connections.py`):
`window_range_plan` (`:432-502`), `WindowRangePlan` (`:272-327`),
`_probe_increment` (`:328-340`), `fetch_upper_bound`
(`:342-352`), `fetch_limit` (`:354-364`), `probe_shape`
(`:366-385`), `constant_false_shape` (`:387-400`), `fetch_mode`
(`:402-429`), `_is_probe_shape` (`:231-246`),
`is_ambiguous_empty_window` (`:249-269`), `FetchMode`
(`:191-228`), `assert_window_fetch_mode` (`:505-536`),
`assert_window_fetch_mode_for` (`:554-572`),
`_RawWindowArguments` (`:539-551`), `split_window_rows`
(`:575-635`), `NEXT_PAGE_PROBE_ROWS` (`:81`). Consumers (7
groups, each composing by name): the ORM renderer
(`plans.py:1135-1142` + `_apply_keyset_counted_window`,
rendering `lower_bound`/`upper_bound`/`fetch_upper_bound`/
`add_marker_rows`/`reverse`); the lateral SQL renderer
(`lateral_fetch.py:391-430`, rendering `plain_first_page`/
`fetch_limit`/`lower_bound`/`fetch_upper_bound`/`reverse`/
`add_marker_rows`); the single-parent fast path
(`single_parent_fetch.py:146-162` reading `plain_first_page`/
`fetch_limit`, `:287-291` slicing the pristine query by it);
the planner mode decision (`nested_planner.py:1440-1461`,
`fetch_mode` -> `with_total_count`/`next_page_probe` --
the ONLY construction of those flags from shape+selection);
the seam carriers (`NestedConnectionRequest` threading +
`__post_init__` gate, `attach_windowed_prefetch` threading,
`LateralWindowSpec` threading + `__post_init__` gate); the
resolve side (`connection.py:477-483` reconstruction,
`:509-513` split, `:582` + `:644` shape reads); the value-domain
keyset page (`connection.py:1143`, sentinel count only).
Upstream inputs: f19's slice (`bounds.offset/limit/reverse`),
f17's strategy, f18's seam, selections observers.
Oracles/projections: Matrix axis 5.

Challenges. C1-C10 above; every count is 1. Consumers that also
move: none (all read owned fields/flags). Oracles spelling the
old behavior move (listed, never counted); projections move.

Owner + lifetime (principle 7). `utils/connections.py`, the
existing cycle-safe home both the planner and the resolver
import: the module docstring states the responsibility (the two
sides must spell the window IDENTICALLY or optimizer-on/off
behavior splits), and no narrower owner is importable from both
sides without reversing a dependency. Lifetime (principle 4):
pure derivation, not cached -- the plan is constructed
call-locally at each of the 6 call sites from raw slice
arguments (requests/specs carry RAW args, never a stored plan),
so there is no validity key, no publish point, no mutation, and
no invalidation to name.

Migration. None -- zero-edit; every site already composes by
name.

Distinct behavior. The per-dialect renderings stay per-dialect
(Q-objects vs SQL text vs plain `LIMIT` vs row classification):
principle 5 adapters over the one shared decision, each
necessary to its medium. The value-domain probe derivation
stays value-domain (R7). The plan-vs-resolve evidence split
stays split (R2/R3).

Behavioral proof. Static-reviewed censuses: single-`def`,
single-construction, and single-call-site censuses per member
above, each naming the wrong result it rejects (a second
bound-arithmetic site, a second mode decision, an ungated
window entry, an unrefused unrenderable shape). No execution:
counts, not equivalence. The drift guards
(`connection.py:570-602`) and the planned-signature proof
(`lateral_fetch.py:658-659`,
`single_parent_fetch.py:260-261`) are the runtime checks that
turn any future plan/resolve disagreement into a byte-identical
fallback instead of a silent divergence.

Structural gate: none proposed, deliberately. A name-census test
per helper (e.g. "exactly one `offset + limit` spelling") is
the bespoke existence test DRY.md forbids; the plausible bypass
(a renderer re-deriving bounds inline) has no population beyond
the enumerated consumers, all proven composing by name, and a
wrong inline re-derivation fails the independent behavior
oracles (edge/flag/parity pins) loudly. Consistent with the
verified f12-f19 zero-edit precedent (f19's gate paragraph
verbatim in shape).

Coupling: none -- zero-edit lands nothing.

Freshness. HEAD `5c3496e0`, ITEM_BASELINE
`818fd32a6a41570669726589ae1ab080da86d048`. Pins (WT /
HEAD, `git hash-object` / `git rev-parse HEAD:`): indexed
`utils/connections.py`
`5bf8f5fa533f4c075cbb9915d471dedf028ff41e` (clean, both states);
`optimizer/lateral_fetch.py`
`a48cb0a45dc228dfa55d9bbe5b0a6dfb9a35848` (clean);
`optimizer/single_parent_fetch.py`
`3a4bb89b93fc92753cc2b8ab279593d09093f482` (clean);
`connection.py`
`48de0243613555312478aaeb7b1a2f198923e91a` /
`999696529e18160aff1e465951ebe7e88dd4613b`;
`optimizer/nested_planner.py` `b6ff0a0e998291c5acdf204fd363fd015bb1e1bb`
/ `8c3a45f55533cbaf9697013e5d87f599aae65adb`;
`optimizer/plans.py`
`2e962ae2dd0a5be4d05a52cc48334904e1511249` /
`97a524e2a8ec0a160f1ed649bb96df019928d6bc`;
`optimizer/nested_fetch.py`
`c36826bb6954642590185ac83deba10cc1423177` /
`bedaa76ebf24d010c4535dddbd1f8e5aa26f621a` -- all 7 match the
dispatch pins byte-for-byte (no drift since dispatch).
Exclusions/consumers read: `keyset.py` `7d43c6b1` /
`6af980b8`, `list_field.py` `6c0992f2` / `37d2e6dc`,
`optimizer/walker.py` `4fd8077f` / `13e1be20`, `relay.py`
`63bbba0b` / `037723cd`, `optimizer/selections.py` `1f6d3e04` /
`f49ea7fa`, `exceptions.py` `34e2e6be` / `7a4fb661`,
`optimizer/predicates.py` `d9e2f789` / `965d1282`,
`optimizer/extension.py` `8e3fe7c1` / `b7b6c434`.
Dirt attribution (by diff content vs `git show HEAD:`): every
dirty hunk in the indexed files is concurrent hunt work (the
`truth.py` migration + prose + the `_advise_composite_index`
M2M-silence arm + `_reject_negative_offset_cursor` +
`_window_edge_class` cache + `_WindowedConnectionRows`
`source_factory`), none of it a range-derivation definition;
ONE hunt hunk touches a family consumer line (the
`not range_plan.next_page_probe and _has_next_page_requested`
conjunct reorder in the `connection.py` drift guard) and is
behavior-preserving (both conjuncts pure). No ledger row covers
that line; as a zero-edit item nothing is touched, so no
blocked-on-hunt arises. Searched population: the full
`django_strawberry_framework/` tree (exact-match greps above);
oracle files cited by path (pins not taken -- behavior pins,
not derivation inputs).

### Rejections and exclusions (contract difference + trigger each)

- R1, the marker `rn == 1` literals (`plans.py:1211` ORM
  forward, `plans.py:1259` ORM keyset-abs,
  `lateral_fetch.py:430` SQL forward). Shared VALUE, not a
  shared change obligation: "keep the FIRST row" is spelled
  once per dialect because dialects cannot share a body
  (Q-object vs SQL text vs abs annotation), and any real
  witness change rewrites each arm bespoke -- a shared
  constant would not survive it. A single-arm change fails
  existing edge oracles loudly (a wrong marker leaks into the
  page or voids the empty-parent proof), so no silent
  divergence hazard exists. Consistent with f18's verified
  per-dialect-construction rejections. Trigger: a
  witness-identity change that moves all arms through one
  value becomes plausible -- single-source it then.
- R2, `keyset_counted` construction (`plans.py:1134`, from
  request fields) vs inference (`connection.py:482`, from
  physical rows). Consumer input logic in disjoint domains
  (decisions vs evidence), each single in its domain; neither
  derives bounds. Agreement is runtime-enforced by the drift
  guards (disagreement falls back byte-identical, never
  diverges). Trigger: the resolver gains the planned request
  (evidence unifies) -- the inference folds into the
  construction.
- R3, `next_page_probe=count_absent` (`connection.py:481`).
  Consumer input inference from the count annotation's
  physical absence, not a probe-shape derivation (the shape
  gate stays in `window_range_plan:501`). Trigger: same as R2.
- R4, the recognition cluster (`window_predicate_signature`,
  `_is_window_qual`, `_parent_in_values`,
  `_recognize_lateral_fetch`, `_single_parent_where_ids`,
  `_keyset_seek_quals_match`). Fail-closed structural proof
  over the Django WHERE AST ("this fetch-time WHERE is the
  planned range + parent IN"), converging onto queued
  `recognized-fetch-queryset-skeleton` -- never absorbed here.
  It SKIPS window quals and proves the signature; it parses no
  bound values. Trigger: a recognizer starts reading bound
  VALUES to decide -- that arm joins this family.
- R5, the slice kernel (`derive_connection_window_bounds`,
  `derive_keyset_window_bounds`, `page_arguments`,
  `is_backward_shape`, `ConnectionWindowBounds`,
  `assert_relay_pagination_bound`, cap dig/resolve). f19 INPUT:
  arguments into slice. This family consumes
  `bounds.offset/limit/reverse` and never re-derives them.
  Trigger: none (verified; a row found factually wrong would
  be a closeout finding -- none was).
- R6, strategy selection + seam (`resolve_strategy`,
  `NestedConnectionStrategy`, `NestedConnectionRequest`,
  `LateralWindowSpec`, `attach_windowed_prefetch`). f17/f18:
  selection decides the backend, the seam carries RAW slice
  args and gates them. The seam threads
  (`nested_fetch.py:342-347`, `lateral_fetch.py:1170-1172`)
  without normalizing. Trigger: the seam starts normalizing
  bounds instead of threading them.
- R7, the value-domain keyset page (`connection.py:1139-1143`,
  `page_size + NEXT_PAGE_PROBE_ROWS`). Deliberate cross-domain
  sharing of the sentinel COUNT only; the page derivation
  (unconditional increment, `len`-based flags) differs from
  the window domain (gated increment, row-number flags) by
  documented design at both sites. Trigger: the value domain
  adopts window bounds.
- R8, cursor/flag derivation over resolved rows
  (`cursor = rn - 1` at `connection.py:624`, `rn < total`
  `:653`/`:656`, `first_rn > 1` `:662`). Connection-FIELD
  rules over page ROWS (cursor codec + upstream
  forward-window flag comparisons), not fetch-RANGE rules
  over slice BOUNDS: disjoint inputs, disjoint change
  reasons (a marker-identity change does not move them).
  Trigger: a cursor/flag rule starts computing a fetch range.
- R9, `list_field.py` offset/limit paging (exact-int
  validation, deterministic-order guard, plain slicing).
  Ordered-offset LIST paging with no window functions,
  markers, probes, or plan record. Trigger: list fields
  adopt windowed prefetch.
- R10, `_window_rows_are_annotated`
  (`connection.py:2225-2242`). Recognition (integrity probe:
  "these rows are the walker's window"), not derivation.
  Trigger: the probe starts classifying ranges.
- R11, order-reversal rendering
  (`plans.py::_reverse_order_by`, lateral
  `order_sql(descending_flip=True)`). ORDER rendering per
  dialect; the reverse DECISION (flag + bound-is-limit) lives
  in f19's slice + this family's plan. Trigger: order
  rendering starts computing bounds.
- R12, the `None`-guard spellings (`upper_bound is not None`
  in the ORM arms vs `fetch_upper_bound is not None`
  lateral). Both rely on the owned `None <-> None`
  equivalence (`fetch_upper_bound:350-352`) without
  restating it; no change moves them jointly. Trigger:
  `None`-propagation becomes non-trivial.
- R13, `connection_count_required`
  (`selections.py:784-824`, test-only OR of the two
  observers). Selections-domain helper that decides no
  fetch mode anywhere in production (the planner splits the
  observers directly into `fetch_mode`). Trigger: a second
  `with_total_count`/`next_page_probe` decision site appears
  -- that is a bypass DEFECT, not a consolidation.
- R14, walker `_optimizer_*` markers
  (`walker.py:1628-1629`). Vocabulary collision: selection
  bookkeeping, unrelated subject. No trigger (no shared
  meaning).
- R15, queued sibling mechanisms, each excluded on a
  mechanism difference: `scalar-only-window-projection` +
  `keyset-cursor-column-projection` (COLUMN projection --
  which attributes load -- vs RANGE derivation -- which row
  numbers fetch); `window-partition-resolution` (partition
  MEMBERSHIP -- which rows belong to a parent -- vs the row
  RANGE within the partition);
  `prefetch-attach-column-projection` (attach columns);
  `lateral-join-shape` (join-shape record);
  `unwindowable-child-queryset-classification` (refusal
  classification); `composite-index-advisory` (index advice);
  `relation-connection-to-attr-grammar` (attr naming);
  `optimizer-hint-dispatch` (hint reads);
  `attached-prefetch-lookups-read` (lookup reads).
  `nested-connection-plan-orchestration` CONVERGES as the
  orchestrator consumer (it calls the builder + `fetch_mode`
  among its steps). Trigger per row: the sibling starts
  deriving fetch bounds instead of its own projection.

## Defects

None. The trace found no non-duplication defect at HEAD bytes.
(The one hunt-dirtied consumer line -- the drift-guard
conjunct reorder in `connection.py` -- is concurrent work,
behavior-preserving, and not a HEAD defect; see Freshness.)

## Pending execution

None. Zero-edit census verdict: no `proof:` entry owed
(definition counts need no execution), no `gate:` entry. Cells
per the run-9 f18 typing ruling: the canonical binary binds and
the range paths reach the database (windowed prefetch
querysets, lateral SQL, the single-parent re-query), while
inapplicable-by-construction is NOT claimed -- so both cells
read `unverified` (`--cell sharded` and `--cell pg` were not
authorized; the gate lists them). The verdict itself is
cell-independent (source censuses are identical across cells).

## Judgment

CONFIRM: window-range fetch derivation is one rule with one
owner (`utils/connections.py::window_range_plan` +
`WindowRangePlan` + satellites), 16 member definitions in 12
sub-decisions each count 1, every consumer composing by name,
no bypass found. Zero-edit; no gate proposed deliberately (the
f12-f19 precedent); no defects. Ready for verification.

## Independent verification (Worker-2)

### W2 pre-reading trace (written before opening ## Findings; all sites re-derived by fresh grep at WT bytes)

Population: the window-range fetch derivation -- how a slice
`(offset, limit, reverse)` (f19's output, entering here as INPUT)
is derived into the fetch decisions every window dialect renders
and the resolver consumes. Mechanism sweep: exact-match grep for
`window_range_plan|WindowRangePlan|FetchMode|assert_window_fetch_mode|split_window_rows`,
`_probe_increment|fetch_upper_bound|fetch_limit|probe_shape|constant_false_shape`,
`NEXT_PAGE_PROBE_ROWS|is_ambiguous_empty_window|_is_probe_shape`,
`lower_bound|upper_bound`, `plain_first_page|add_marker_rows|keyset_counted`,
`offset + limit|sys.maxsize|limit is None or|offset == 0|offset > 0|limit == 0`
across `django_strawberry_framework/` (+ `split_window_rows(` in
`tests/` + `examples/fakeshop/test_query/` for the consumer census).

DEFINITIONS (all in `django_strawberry_framework/utils/connections.py`):

- D1 `window_range_plan` head: negative-offset guard, negative-limit
  guard (`OptimizerError`), `sys.maxsize` -> `None` fold.
- D2 `lower_bound` (`offset if (offset or keyset_counted) else None`).
- D3 `upper_bound`
  (`(limit if reverse else offset + limit) if limit is not None else None`).
- D4 `is_ambiguous_empty_window`
  (`not reverse and (offset > 0 or limit == 0)`).
- D5 marker planning (`ambiguous and (lower/upper bounded)`; the
  `keyset_counted` input arm).
- D6 `plain_first_page`
  (`not reverse and offset == 0 and limit is not None and limit > 0`).
- D7 `_is_probe_shape` (+ `WindowRangePlan.probe_shape` delegating
  property + the builder's honoring call: one body, two readers).
- D8 probe honoring
  (`request and probe_shape and not keyset_counted`).
- D9 `NEXT_PAGE_PROBE_ROWS` (= 1, shared with the value domain).
- D10 `_probe_increment` + `fetch_upper_bound` + `fetch_limit`
  (one primitive, two readers).
- D11 `constant_false_shape` (`limit is None or reverse`).
- D12 `FetchMode` (4 members) + `fetch_mode` precedence ladder
  (COUNTED > PROBED > CONSTANT_FALSE > NONE).
- D13 `assert_window_fetch_mode` (probe XOR count) +
  `assert_window_fetch_mode_for` (raw-args delegate).
- D14 `split_window_rows` (4 arms: composed / marker-only /
  probe-only / passthrough).

CONSUMERS (production, every one composing by name):

- `connection.py::_resolve_from_window`: builds the plan (physical
  `count_absent` -> `next_page_probe`, rows+seek+count -> keyset
  input), SOLE production `split_window_rows` caller, reads
  `constant_false_shape` / `next_page_probe` / `probe_shape`
  (via builder honoring). Never re-derives a bound or predicate
  inline (the `limit is None or reverse` spelling appears ONLY in
  D11 plus one prose comment citing the delegation).
- `optimizer/plans.py::apply_window_pagination`: builds, enforces
  the D13 gate, renders lower/upper/fetch_upper/marker as Q
  objects (forward, reversed, keyset-counted arms); computes the
  plan-time `keyset_counted` input (`seek and with_total_count`).
- `optimizer/lateral_fetch.py`: `LateralWindowSpec.__post_init__`
  enforces D13; `build_lateral_sql` builds, branches on
  `plain_first_page` (`fetch_limit`), binds
  `lower_bound`/`fetch_upper_bound`, renders the marker `OR rn=1`.
- `optimizer/nested_planner.py::plan_connection_relation`: builds,
  calls `fetch_mode` once, maps COUNTED->`with_total_count` /
  PROBED->`next_page_probe` (the ONLY `FetchMode` value reads
  outside prose).
- `optimizer/nested_fetch.py`: `NestedConnectionRequest.__post_init__`
  enforces D13; `attach_windowed_prefetch` threads the raw flags.
- `optimizer/single_parent_fetch.py::single_parent_spec`: builds,
  gates on `plain_first_page`, reads `fetch_limit`; the fetcher
  synthesizes rn 1..N and never sets the count (the absence the
  resolver re-infers).
- Oracles: `tests/utils/test_connections.py` `split_window_rows`
  calls (projection/oracle, not counted).

Builder call-site census: 6 (`plans.py`, `lateral_fetch.py`,
`nested_planner.py`, `single_parent_fetch.py`, `connection.py`,
+ the D13 delegate's internal resolve). Gate enforcement: 3
(`plans.py` direct call + 2 `__post_init__`). Splitter
consumers: 1 production. `FetchMode` producers: 1 (`fetch_mode`).

CHANGE CHALLENGES (W2's own; C-W11/C-W12 stress beyond the brief):

- C-W1 change the upper-bound formula -> D3 only (every renderer
  reads the derived bound; the per-dialect predicate spellings
  are medium renderings, not derivations). Count 1.
- C-W2 change the maxsize fold / negative guards -> D1 only. Count 1.
- C-W3 change ambiguous / marker gate -> D4+D5 only. Count 1.
- C-W4 change plain-first-page -> D6 only (lateral + single-parent
  follow by name). Count 1.
- C-W5 change probe-shape / honoring -> D7+D8 only. Count 1.
- C-W6 change sentinel count 1->2 -> D9 only (both domains follow;
  the gatings differ -- see exclusions). Count 1.
- C-W7 change fetch ladder precedence -> D12 only. Count 1.
- C-W8 change gate (allow probe+count) -> D13 only. Count 1.
- C-W9 change splitter arm -> D14 only. Count 1.
- C-W10 posit a bypassing renderer (inline `offset + limit`,
  inline `offset == 0 and limit > 0`, inline
  `limit is None or reverse`, inline `+ 1` on a window bound):
  grep finds NONE -- every spelling is single-sited at the
  D-owner with consumers reading attributes. Count 1 (no landing).
- C-W11 change "what counts as a counted keyset window": two
  FLAG computations exist (`plans.py` plan-time intent
  `seek and with_total_count` vs `connection.py` resolve-time
  observation `rows and seek and count-present`). Pre-reading
  position: NOT a second definition of the range rule -- they
  are per-lifecycle INPUTS (request vs physical rows), the same
  intent-vs-observation split as the probe inference; the keyset
  range SEMANTICS (floor/ambiguity/no-probe) is single-sited in
  D2/D5/D8. No landable owner serves both (plan time has no
  rows; resolve time has no request flags). Awaiting W1's text
  to rule finally (expect an R row or a member note).
- C-W12 split the record (move `fetch_mode` off the plan): 1
  producer + 1 consumer + prose. Count 1.

EXCLUSIONS (W2's own boundary list, contract differences sketched;
triggers to rule after reading):

- E-a value-domain keyset page (`connection.py` fetch
  `page_size + NEXT_PAGE_PROBE_ROWS`, len-based flags): shares
  the D9 COUNT, always probes, different derivation + media.
- E-b slice kernel (`derive_connection_window_bounds` /
  `SliceMetadata`, f19): INPUT `(offset, limit, reverse)`, not
  the fetch derivation. f19 boundary.
- E-c selection observability (`selections.py`
  `connection_count_required` + the two observer walks; the
  f18 seam carrying the flags): INPUT observers, different
  subject (GraphQL selection vs range arithmetic). f15/f18
  boundary.
- E-d keyset construction (`keyset.py` seek Q/SQL, cursor codec):
  value-seek construction vs range derivation; the builder takes
  only the `keyset_counted` flag.
- E-e cursor derivation (offset `rn - 1`, keyset value codec):
  cursor minting vs fetch bounds.
- E-f `_reverse_order_by` (ORM `OrderEntry` reversal with NULLS)
  vs lateral `order_sql` bool flip: different input/output
  contracts per dialect; reversal RENDERING, not range derivation.
- E-g list-field paging guards (`list_field.py` `offset > 0`
  order-required rejection): argument validation vs window ranges.
- E-h annotation presence (`_window_rows_are_annotated`, wrapper
  recognition): wrapper detection vs range derivation.
- E-i walker bookkeeping (`planned_resolver_keys`, to_attr
  grammar): plan/attach contract vs fetch derivation; queued
  families own the grammar rows.
- E-j per-dialect range-predicate renderings (splitter Python,
  ORM Q, lateral SQL, keyset Q) + marker `OR rn = 1` in 3
  media: applications of D-decisions gated on plan booleans,
  not re-derivations (no landing: media cannot merge).
- E-k `None`-guard / `is None` spellings across the files: shared
  idiom, not a rule.
- E-l queued sibling families on these files
  (`window-partition-resolution`, `lateral-join-shape`,
  `prefetch-attach-column-projection`,
  `recognized-fetch-queryset-skeleton`,
  `unwindowable-child-queryset-classification`,
  `nested-connection-plan-orchestration`, `composite-index-advisory`,
  `relation-connection-to-attr-grammar`,
  `scalar-only-window-projection`,
  `keyset-cursor-column-projection`, `connection-order-ladder`,
  `attached-prefetch-lookups-read`, `optimizer-hint-dispatch`):
  boundaries to check W1 names as REAL open rows.

OWNER (principle 7, W2's own): `utils/connections.py`
(`window_range_plan` + `WindowRangePlan` + satellites). State
contract: pure derivation, no stored lifetime beyond the call
(no principle-4 cache fields). Real consumers: all six sites
above import it today. Dependency direction wins: it is the
cycle-safe leaf every consumer (resolver, planner, seam,
both renderers, fast path) can import; `plans.py` would force
the resolver/fetch-seam to import an ORM renderer for a
renderer-agnostic derivation (wrong responsibility), and
`connection.py` would force the planner to import down.
No narrower cohesive home serves all six.

ZERO-EDIT PRE-READING CHECKS (re-verified by W2 before reading):

- No `## Implementation` (grep: 0).
- 7/7 WT pins match dispatch pins; HEAD pins match too
  (`5bf8f5fa` clean, `48de0243`, `b6ff0a0e`, `2e962ae2`,
  `a48cb0a4` clean, `c36826bb`, `3a4bb89b` clean).
- `git diff ITEM_BASELINE --name-only` = `docs/dry/dry-0_0_15.md`
  alone (the dispatch + submission record).
- `git status --short` = 468 lines; the f20 artifact is untracked
  scratch (expected); all other dirt is concurrent work.
- Head unmoved (`5c3496e0`).
- Indexed-file dirt (HEAD vs WT) is all concurrent hunt work
  (`truth` module, try/except removals, edge-class cache,
  `source_factory`, `_reject_negative_offset_cursor`, prose):
  none touches a builder call site, a gate, the splitter, or a
  bounds read. The one consumer-line change (drift-guard
  conjunct reorder in `connection.py`) is a pure-`and`
  commutation of three total predicates (two bool reads + one
  side-effect-free selection walk) -- behavior-preserving by
  inspection; pre-reading position: concurrent work, not a HEAD
  defect. Awaiting W1's text to rule finally.
- Cells pre-reading position: `unverified` per the run-9 f18
  ruling (canonical binary binds; range paths reach the
  database -- windowed prefetch querysets, lateral SQL,
  single-parent re-query -- while inapplicable-by-construction
  is NOT claimed). Awaiting W1's text to rule finally.
- Gate pre-reading position: deliberate no-gate consistent with
  the f12-f19 precedent (a per-helper name-census test is the
  bespoke existence test DRY.md forbids); the bypass question is
  answered by the grep sweep above, not by a test. Awaiting
  W1's text to rule finally.

### W2 reconciliation (after reading Findings; every difference explicit)

FINDINGS READ in full (System trace + Verification + Findings +
Defects + Pending + Judgment). Reconciliation against the
pre-reading trace above:

- F1 verdict + owner: FULL AGREEMENT. W1's 16 members in 12
  sub-decisions vs W2's D1-D14 is grouping granularity only:
  W1 counts symbols (record + builder + `_RawWindowArguments`
  as members; `_probe_increment`/`fetch_upper_bound`/
  `fetch_limit` as 3; gate + delegate as 2), W2 counted
  derivation groups (D10, D13 folded; record folded into the
  builder's decisions). Every W1 challenge C1-C10 maps onto a
  W2 challenge (C1->C-W2, C2->C-W1, C3->C-W3, C4-C5->C-W5/C-W6,
  C6->C-W7, C7->C-W8, C8->C-W9, C9->D11 covered, C10->C-W4/C-W12)
  and every count is 1 on both sides. Owner reasoning agrees
  (cycle-safe leaf both sides import; dependency direction
  wins; W2's rejected alternatives -- `plans.py` renderer home,
  `connection.py` resolver home -- are consistent with W1's
  "no narrower owner importable from both sides"). W1's
  principle-4 lifetime note (pure, call-local, requests/specs
  carry RAW args never a stored plan) matches W2's. ENDORSED.
- No-bypass sweep: FULL AGREEMENT. W2's C-W10 grep sweep
  (inline `offset + limit`, inline `offset == 0 and limit > 0`,
  inline `limit is None or reverse`, inline `+ 1` on a window
  bound) found NONE independently; W1's per-dialect-adapter
  framing (principle 5) matches W2's E-j. The gate-or-reject
  resolves to CONFIRM-single on both sides. ENDORSED.
- Builder/gate/splitter censuses: FULL AGREEMENT, each
  re-verified fresh by W2 post-reading: 6 builder call sites
  (5 production + the D13 delegate's internal resolve);
  3 gate enforcements (`plans.py:1142` + both `__post_init__`);
  1 production splitter consumer (`connection.py:509`, test
  calls are oracles); 1 `FetchMode` producer (`fetch_mode`)
  with the ONLY value reads at `nested_planner.py:1460-1461`;
  `WindowRangePlan(` / `LateralWindowSpec(` /
  `NestedConnectionRequest(` each exactly once in production
  (`:493` / `:1153` / `:1462`) with zero `WindowRangePlan(`
  in tests/examples; `is_ambiguous_empty_window` one direct
  caller (`:485`); `.fetch_mode(` one caller (`:1456`);
  `_resolve_from_window` / `_consume_window` one caller each
  (`:744` / `:1396`). ENDORSED.
- C-W11 (counted-keyset flags): RESOLVED by W1's R2/R3, which
  match W2's pre-reading position exactly (disjoint
  domains -- decisions vs evidence -- each single; drift
  guards runtime-enforce agreement; no landable joint owner).
  W2's split (one stress case) vs W1's split (R2 construction
  vs R3 probe inference) is granularity; both triggers
  ("resolver gains the planned request") are concrete.
  ENDORSED; no revision candidate.
- R1 (marker literals): AGREEMENT. W2's E-j + W1's R1 agree
  (per-dialect VALUE, media cannot merge); W1 adds the
  fail-loud argument (single-arm change breaks edge oracles)
  and the f18-precedent consistency -- ADOPTED as stronger.
  Trigger concrete. ENDORSED.
- R4 (recognition cluster): AGREEMENT. Recognizers skip quals
  and prove signatures, parse no bound values; convergence
  target `recognized-fetch-queryset-skeleton` is a REAL open
  index row (plan line 413). Trigger concrete. ENDORSED.
- R5/R6 (f19 slice / f17+f18 selection+seam): AGREEMENT.
  Both are INPUT boundaries (W2's E-b/E-c); R6's
  thread-without-normalizing verified at the cited lines.
  Triggers concrete. ENDORSED.
- R7 (value-domain page): FULL AGREEMENT (W2's E-a: shared
  COUNT, unconditional increment, len-based flags, documented
  at both sites). Trigger concrete. ENDORSED.
- R8 (cursor/flag derivation): AGREEMENT (W2's E-e extended:
  rows-vs-bounds disjoint inputs/change reasons). Trigger
  concrete. ENDORSED.
- R9/R10/R11 (list-field / annotation probe / order reversal):
  AGREEMENT with W2's E-g/E-h/E-f, each re-verified at the
  cited lines (order-required guard, integrity probe,
  per-dialect NULLS-carrying reversal). W1's R11 note that
  the reverse DECISION lives in f19 + this family's plan is
  exact. Triggers concrete. ENDORSED.
- R12 (None-guards): AGREEMENT, W1 sharper -- the owned
  `None <-> None` equivalence (`fetch_upper_bound:350-352`)
  relied on, never restated. ADOPTED. Trigger concrete.
  ENDORSED.
- R13 (`connection_count_required`): AGREEMENT. W2 verified
  fresh: ZERO production calls (def + prose mentions only),
  called only by `tests/optimizer/test_selections.py` --
  W1's "test-only OR" is exact. The trigger (a second
  count/probe decision site = bypass DEFECT, not a
  consolidation) is the correct shape. ENDORSED.
- R14 (walker markers): AGREEMENT. `:1628-1629` is selection-
  bookkeeping prose; the whole `_optimizer_*` cluster is
  context/selection vocabulary, mechanism-disjoint. No
  trigger -- correct (no shared meaning). ENDORSED.
- R15 (queued siblings): AGREEMENT with one W2 self-correction.
  Every named row is REAL and open
  (`scalar-only-window-projection`,
  `keyset-cursor-column-projection`,
  `window-partition-resolution`,
  `prefetch-attach-column-projection`, `lateral-join-shape`,
  `unwindowable-child-queryset-classification`,
  `composite-index-advisory`, `relation-connection-to-attr-grammar`,
  `optimizer-hint-dispatch`, `attached-prefetch-lookups-read`
  excluded; `nested-connection-plan-orchestration` converged
  as orchestrator consumer). W2's pre-reading E-l over-listed
  by one (`connection-order-ladder`): file-adjacent but
  mechanism-disjoint (order is a parallel INPUT to renderers
  alongside the range plan; no shared vocabulary or change
  axis with any C-challenge; its open row fences its own
  trace). W1's mechanism cut is the correct one; nothing
  dropped. The uniform per-row trigger ("starts deriving
  fetch bounds") is concrete. ENDORSED.
- f15-f19 boundary: ENDORSED. W1 names f19/f17/f18 as inputs,
  f15/f16 + f12/f13 as transitive, and re-litigates nothing
  (no hint/policy/strategy/seam verdict touched; f18's
  D1+O3 homing unmentioned and intact).
- Matrix: ENDORSED. All six axes discharged against the REAL
  surface (flavor sweep with the list-field adjacent read;
  pure-sync single-`def` census + one-caller colors; four
  derived-knowledge candidates with homes; render/recognize
  round-trip with the no-bound-values finding; media census
  with oracle/projection roles and no oracle reading its
  owner; omission as gates + loud refusals + single-
  construction censuses). W2's independent sweeps land in
  the same 9 production files (7 indexed + `selections.py`
  prose + `exceptions.py` prose). No axis unsearched.
- Hunt-line call: AGREEMENT on the verdict (behavior-
  preserving concurrent work, not a HEAD defect), with one
  scratch-prose slip noted: W1 writes "both conjuncts pure"
  for a THREE-conjunct reorder (two bool reads + the
  side-effect-free `_has_next_page_requested` selection
  walk, verified pure at `connection.py:1241-1249` /
  `:1282-1298`). Substance exact; the count word is loose.
  Record-only; the verdict does not spend on scratch prose.
- Index-rows-owed: NONE -- ENDORSED. R4/R15 converge onto or
  exclude against EXISTING open rows; no new family,
  rejection, or file-local row is named or owed. Worker-0
  acts on this endorsement: no row to add.
- Pending-execution "None": CORRECT -- census verdict,
  nothing moves, no gate proposed, so no `proof:`/`gate:`
  owed. Verdict: `verified` PLAIN (no `proof:` correctly
  remains).
- Cells `unverified`: CORRECT application of the run-9 f18
  typing ruling (canonical binary binds; range paths reach
  the database -- windowed prefetch querysets, lateral SQL,
  single-parent re-query -- while
  inapplicable-by-construction is NOT claimed; `--cell`
  runs unauthorized). Cell-independent verdict. ENDORSED.
- Structural no-gate: ACCEPTED. The bespoke-existence-test
  argument + behavior-oracle fail-loud + the verified
  f12-f19 zero-edit precedent; no gate means no negative
  control owed. ENDORSED.
- Freshness: byte-for-byte. All 7 indexed pins + all 8
  exclusion-file pins re-verified by W2 (`git hash-object`
  vs `git rev-parse HEAD:`) and match W1's text AND the
  dispatch pins; `git diff ITEM_BASELINE --name-only` is the
  plan edit alone; `git status` 468 lines with the f20
  artifact as the expected untracked scratch; HEAD
  `5c3496e0` unmoved. Dirt attribution by content agrees
  (hunt-owned `truth` migration + caches + new guard +
  prose; the one consumer-line hunk is the reorder above).
  Oracle files cited by path without pins: ACCEPTED (behavior
  pins, not derivation inputs -- no oracle byte can create a
  second production definition).
- Ruff: VACUOUS -- zero-edit, no tracked `.py` touched
  (artifact is per-cycle scratch; raw `path:NN` allowed, no
  style cleanup owed). Not run over `.` per constraint.
- Type gates (Worker-2 re-ran whole-package, shared venv --
  slots 1-3 damaged, slot-4 unselectable, so the shared venv
  per the KNOWN constraint; static gates, slot damage
  irrelevant): `uv run mypy` -> Success, no issues, 119
  files, exit 0; `uv run basedpyright` -> 0 errors / 0
  warnings / 0 notes, exit 0;
  `uv run python scripts/check_any.py` -> 130 allowed Any at
  90 sites, exit 0. All match W1's numbers. (No pytest: not
  authorized by this task. No workspace run: no
  source-mutating proof exists for a zero-edit census
  verdict.)
- Defects: NONE (Worker-2). No `## Defects` entry owed.

No standing disagreement on any claim; no `revision-needed`
candidate (every stress change counts 1 or has no landable
owner, and no landing would hit concurrent dirt because no
landing is owed); nothing `blocked`.

VERDICT: `verified` (plain -- no `proof:` correctly remains).
