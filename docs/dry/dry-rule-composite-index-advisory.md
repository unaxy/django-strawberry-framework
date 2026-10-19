# DRY review: `composite-index-advisory`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is the composite-index advisory: for a planned
nested Relay connection window, inspect the child model's represented
physical index shapes against the window's leading `(content_type_id?,
connector, order terms..., pk)` shape and, under `settings.DEBUG`,
log a one-time-per-shape WARNING recommending the covering composite
when absence is PROVEN from fully-inspectable metadata -- silent on
any UNKNOWN at either end of the comparison. Re-derived fresh at WT
bytes (HEAD `5c3496e0` + concurrent dirt), not inherited: the
population is the mechanism (the emission call, the tri-state
classify, the inventory reads, the order/index parsers, the serving
rules, the render, the dedup store, the DEBUG gate, the B-tree type
inventory, the backend probe), swept package-wide by exact-match
spelling across all 119 package files, not just the six indexed ones.

What the trace found is an already-consolidated rule in one home:

- The advisory body in `optimizer/nested_planner.py:100-698`: the
  B-tree type inventory (`_PostgresBTreeIndex`,
  `_BTREE_INDEX_TYPES`), the backend probe
  (`_every_backend_supports_index_column_ordering`), the order-side
  parse (`_concrete_order_terms`), the index-side parse
  (`_index_leading_terms`), the tri-state vocabulary (`_INDEX_COVERED`
  / `_INDEX_ABSENT` / `_INDEX_UNKNOWN`), the serving rules
  (`_terms_serve_order`, `_index_serves_window`), the directionless
  mapping (`_plain_field_terms`), the inventory
  (`_model_index_shapes`), the classifier (`_index_coverage`), the
  render (`_describe_index_columns`), the bounded dedup
  (`_MAX_INDEX_ADVISORY_KEYS`, `_IndexAdvisoryKey`,
  `_index_advisory_seen`, `_index_advisory_already_emitted`,
  `clear_index_advisory_dedup`), and the owner
  (`_advise_composite_index`: M2M / unresolved-connector silence,
  morph-first equality build, equality-strip, ABSENT-gated
  DEBUG-level emission). 20 member definitions in 11 sub-decisions
  (F1); every helper is composed by name inside the body, never
  re-spelled.
- The sole production call site in the same module
  (`plan_connection_relation:1485`), behind the `advised` latch:
  field-static emission after the FIRST window a strategy accepts.
  The latch position and the deferral are orchestration-owned
  (verified `nested-connection-plan-orchestration`, X12); the
  emission verdict is this family's (verified
  `nested-fetch-strategy-seam`, R19 -- trigger trigger-checked
  fresh below, not met).
- Composed owners, never re-derived: the order-entry vocabulary in
  `optimizer/plans.py` (`order_entry_name_and_direction`,
  `order_entry_has_explicit_nulls`, `append_unique`), the soft
  import in `utils/imports.py` (`import_attr_if_importable`, one
  call at `:115`), the join facts in
  `optimizer/join_taxonomy.py` (`through_model`,
  `parent_join_column`, `content_type_column` reads), and the
  emission channel (`optimizer/__init__.py::logger`, owned by
  verified `logger-single-sourcing`). The advisory is the only
  `logger.warning` site in the optimizer (census below).

Verified siblings enter as INPUT and are never re-litigated:
`nested-connection-plan-orchestration` (loop, latch, deferral),
`nested-fetch-strategy-seam` (seam vs emission, R19),
`plan-time-window-slice-resolution` (the `order_by` input),
`prefetch-attach-column-projection` (E2/E10: attach order vs
advisory order, loading vs recommendation),
`window-partition-resolution` (E10: derivation vs reading),
`logger-single-sourcing` (channel), File `utils/imports.py`
(consumer-only edge), File `optimizer/join_taxonomy.py` (R16),
File `_request_body.py` (J1/J2 standing except/exact-type rows).
Queued siblings are excluded, never absorbed:
`relation-connection-to-attr-grammar`,
`scalar-only-window-projection`, `keyset-cursor-column-projection`
(R14).

Prior record, adjudicated fresh (never evidence): File
`optimizer/nested_planner.py` named this family (F3, 20 members)
and recorded R1/R6/R7/R8/R9 plus D1 (the M2M advisory defect,
observed-not-homed with a fixed-concurrent closeout condition).
The fresh census below re-derives membership symbol by symbol and
CONFIRMS all 20 members; every standing rejection is
trigger-checked against WT bytes (R1-R6); D1 is now
fixed-by-hunt at WT (see `## Defects`), which doubles as the
empirical change challenge: a real silence-arm change moved
exactly one production definition.

## Verification

### Matrix

Each axis discharged against the family's real surface (the
emission, the tri-state, both parsers, the serving rules, the
dedup, the DEBUG gate):

1. Cross-flavor policy mirroring -- DISCHARGED by census. The
   advisory fires once per plan shape regardless of backend: the
   dedup key is `(model label, equality prefix, order terms)` and
   deliberately excludes strategy, and `_advise_composite_index`
   takes no strategy argument (f18 R19 trigger: advisory
   interpreting strategy identity -- not met at WT). Root
   connections carry no advisory vocabulary (`connection.py`
   grep 0, R10: unpartitioned root vs per-partition window).
   Relation flavors: reverse FK / reverse O2O advise;
   `GenericRelation` advises morph-first; M2M stays silent
   (hunt gate at `:654`, README contract); forward-single never
   windows so never reaches the call site (orchestration-owned;
   no window means no window index to advise). The
   `single_parent_fetch` fast path degrades at fetch, never
   re-advises (grep 0, R11).
2. Sync/async twins -- DISCHARGED, no twin. All 20 member
   definitions are sync; the module carries zero `async def` /
   `await` (census). Planning runs once per plan build on the
   sync path; the advice is a pure derivation plus a log call
   with no await boundary to twin across.
3. Derived rather than repeated knowledge -- DISCHARGED by
   census. `meta.indexes` is read at exactly one site
   (`:465`); `supports_index_column_ordering` at exactly one
   (`:149`); the B-tree inventory derives once at import
   (`:113-120`). The `unique_together` / `UniqueConstraint`
   reads in `mutations/resolvers.py:783-815` derive write-path
   validation groups, a different rule (R7). Order parsing is
   composed from the plans owner, never re-spelled (R8 names
   the intentional keyset twin).
4. Inverse / round-trip pairs -- DISCHARGED. The dedup key has
   one construction site (`:683-685`); `_describe_index_columns`
   renders one way with zero parse-back sites (oracles assert
   substrings, never re-parse); the `to_attr` grammar is the
   queued sibling's (R14). No pair has two owners.
5. Contracts restated in another medium -- DISCHARGED. One
   oracle file (`tests/optimizer/test_nested_index_advisory.py`,
   independent expectations: spelled model shapes, spelled
   verdicts, caplog level + substring pins); projections are
   the owner docstrings, the `nested_fetch.py:48-62` indexing
   section, the `plans.py:853` consumer cite, the
   `join_taxonomy.py` descriptor cites, the `keyset_seek_q`
   design cite (one-way prose), the `docs/README.md:350-354`
   paragraph, and the TREE oracle line. No medium restates a
   definition: the D1 README row now agrees with the fixed
   body (see `## Defects`).
6. Enforcement by omission -- DISCHARGED by enumeration. Every
   windowable shape reaching the latch is covered: direct-FK
   advises, generic advises with morph prefix, M2M silent by
   gate, unresolved connector silent, uninspectable order or
   index silent by tri-state, covered silent, DEBUG-off
   demoted to debug. Forward-single and UNSUPPORTED joins
   never plan a window (orchestration), so omission there is
   by construction, not a gap. Offset and keyset windows
   share the one call; the order input differs, the emission
   rule does not. No member lacks its guard.

### Enumeration

Family item: the population is the rule's mechanism, swept
package-wide (119 files) by exact-match spelling:
`_advise_composite_index`, `_index_coverage`,
`_model_index_shapes`, `_index_serves_window`,
`_terms_serve_order`, `_index_leading_terms`,
`_plain_field_terms`, `_concrete_order_terms`,
`_describe_index_columns`, `_index_advisory_already_emitted`,
`clear_index_advisory_dedup`, `_index_advisory_seen`,
`_INDEX_COVERED`, `_INDEX_ABSENT`, `_INDEX_UNKNOWN`,
`_BTREE_INDEX_TYPES`, `_PostgresBTreeIndex`,
`_every_backend_supports_index_column_ordering`,
`_MAX_INDEX_ADVISORY_KEYS`, `Advisory only`,
`no represented index`, `would let the database`,
`supports_index_column_ordering`, `meta.indexes`,
`through_model`, `content_type_column`,
`logger.warning`, `settings.DEBUG` (optimizer),
`move_to_end`, `popitem(last=False)`,
`import_attr_if_importable`,
`order_entry_name_and_direction`,
`order_entry_has_explicit_nulls`, `async def` /
`await` (module), `composite` (word census).

Hits land in 12 production files: the 6 indexed files (owner
body + call site in `nested_planner.py`; descriptor facts in
`join_taxonomy.py`; composed parsers in `plans.py`; composed
soft-import in `utils/imports.py`; the two compared LRUs in
`extension.py` -- R3; the indexing-section prose in
`nested_fetch.py`) plus `keyset.py` (intentional twin + prose
cite -- R8), `mutations/resolvers.py` (different rule -- R7),
`connection.py` (parser consumer; advisory grep 0 -- R10),
`optimizer/lateral_fetch.py` (parser consumer with its own
scan -- R6/R12), `types/converters.py` (import consumer
sibling -- R9), and `optimizer/__init__.py` (channel).
`single_parent_fetch.py` and `walker.py` grep 0 on every
advisory spelling (R11, orchestration input). Each hit was
read and either roled or excluded with a contract difference
under Findings. Nothing reachable was left unassigned: 20
member definitions in 11 sub-decisions, 1 enforcement site,
4 composed owners, 14 exclusions, 1 oracle file, projections.

### Challenges

Each variation axis of the advisory rule, posited change plus
the authoritative definitions forced to move (consumers,
oracles, projections listed, never counted):

- C1, the coverage inventory gains or loses a shape kind
  (e.g. a new constraint type counts as covering): S7
  (`_model_index_shapes`) plus its arm (S4/S6) only. The
  classifier, the owner, and the oracles follow by name.
  Count 1.
- C2, the B-tree type set changes (a new backend index
  class): S1 (`_PostgresBTreeIndex` / `_BTREE_INDEX_TYPES`)
  only. The exact-type gate reads the tuple. Count 1.
- C3, the order vocabulary gains a kind (a new expression
  the window can order by): S3 (`_concrete_order_terms`)
  only; the shared dash/expression parse moves under the
  plans family. Count 1.
- C4, the serving semantics change (e.g. a partial flip
  becomes servable): S5 (`_terms_serve_order` /
  `_index_serves_window`) only. Count 1.
- C5, the emission policy changes (a new silence arm, new
  wording, a new level): S11 (`_advise_composite_index`)
  only. Empirical proof: the M2M-silence change landed as
  exactly the `:654` gate + its docstring paragraph + 2
  oracle tests, zero other production sites. Count 1.
- C6, the dedup key or lifetime changes (a new key
  ingredient, a new cap): S10 only. Count 1.
- C7, the backend probe changes (a new capability bit):
  S2 only. Count 1.
- C8, the recommendation render changes (e.g. a new DESC
  annotation): S9 only. Count 1.

Execution: none owed and none used. Every challenge above is
decided by an exact-match single-site census (definition
counts, not behavioral equivalence), which needs no
execution; nothing lands, so no failability proof is owed.
All oracle citations are static-reviewed. No workspace run
and no shared-tree run was needed for this zero-edit
verdict. The three static gates were run against the traced
tree (shared venv): `uv run mypy` (no issues, 119 files),
`uv run basedpyright` (0 errors/warnings/notes),
`uv run python scripts/check_any.py` (130 allowed at 90
sites) -- all exit 0.

## Findings

### F1: composite-index advisory is single-owned (CONFIRM, zero-edit)

Contract + variation: for one planned nested window, the
advisory recommends the `(content_type_id?, connector, order
terms...)` composite when no represented physical index shape
serves it, warns once per shape at WARNING under DEBUG
(debug otherwise), and stays silent on M2M windows,
unresolved connectors, covered shapes, and any UNKNOWN at
either end. It varies on: inventory kinds, B-tree types,
order vocabulary, serving semantics, emission policy, dedup
key/lifetime, backend probe, render -- one sub-decision each
(S1-S11), every challenge count 1 (C1-C8).

Sites + roles. Definitions (20, all in
`optimizer/nested_planner.py`): S1 `_PostgresBTreeIndex` /
`_BTREE_INDEX_TYPES` (`:113-120`); S2
`_every_backend_supports_index_column_ordering` (`:123-152`);
S3 `_concrete_order_terms` (`:243-300`); S4
`_index_leading_terms` (`:303-360`); S5 `_terms_serve_order`
/ `_index_serves_window` (`:375-416`); S6
`_plain_field_terms` (`:419-440`); S7 `_model_index_shapes`
(`:443-506`); S8 `_INDEX_*` + `_index_coverage`
(`:370-372`, `:509-532`); S9 `_describe_index_columns`
(`:535-548`); S10 `_MAX_INDEX_ADVISORY_KEYS` /
`_IndexAdvisoryKey` / `_index_advisory_seen` /
`_index_advisory_already_emitted` /
`clear_index_advisory_dedup` (`:569-597`); S11
`_advise_composite_index` (`:600-698`, owner). Enforcement
site: the `:1485` call + `advised` latch (orchestration-owned
loop). Consumers of composed owners: S1 -> `utils/imports.py`
(one call); S3 -> `optimizer/plans.py` (two parsers);
S11 -> `optimizer/join_taxonomy.py` (three descriptor reads)
and the optimizer logger (sole `logger.warning` in the
optimizer; every other optimizer emission is `logger.debug`).
Oracles: `tests/optimizer/test_nested_index_advisory.py`
(spelled shapes, spelled verdicts, caplog pins; the
`_INDEX_*` imports name the vocabulary, the expectations do
not read the owner). Projections: owner docstrings,
`nested_fetch.py:48-62`, `plans.py:853`,
`join_taxonomy.py` descriptor prose, the `keyset_seek_q`
one-way cite, `docs/README.md:350-354`, the TREE oracle line.

Challenges: C1-C8 above, each count 1; C5 additionally
proved by the landed M2M-silence change (one gate + prose +
2 tests, zero other production sites).

Owner + lifetime: `optimizer/nested_planner.py::
_advise_composite_index`, CONFIRMED fresh (principle 7: the
narrowest symbol every legitimate consumer reaches -- the
sole caller is its own module's orchestration, and the
helpers it fronts compose four owners no single lower home
can host without reversing a dependency). Stored-derivation
lifetime (principle 4) for S10: owner
`_index_advisory_seen`; validity key `(model label, equality
prefix, order terms)`; publish point: first ABSENT verdict
per plan build; may mutate: the LRU insert/promote/evict
only; invalidated by cap eviction or
`clear_index_advisory_dedup` (test seam, zero production
callers). Every other member is a pure derivation, not
cached.

Migration: none -- already composed by name everywhere;
zero edits.

Distinct behavior: the skip-policy projection walk (R1),
the attach-order property (R6), the extension LRUs (R3),
the keyset twin (R8), the fallback log (R13), and the
queued siblings (R14) stay separate, each recorded below
and at its owner prose.

Behavioral proof: static-reviewed. The verdict is a
definition-count verdict over exact-match censuses, each
reproducible by the Enumeration spellings; behavioral
equivalence needs no proof because nothing moves. The
independent behavior oracles (tri-state tables per model
shape, warn/silent arms, DEBUG toggle, dedup + eviction
pins, the M2M gate) fail on divergence by spelled
expectation. No `proof:` entry owed.

Structural gate: none proposed, deliberately. A name-census
test per helper (e.g. "exactly one `_index_coverage` call")
is the bespoke existence test DRY.md forbids; the plausible
bypass (an inline re-derivation of coverage or a second
emission) has no population beyond the enumerated consumers,
all proven composing by name, and the landed M2M change
demonstrates new arms land inside S11 rather than beside
it. The literal-spelling behavior oracles are the guard
that fails on divergence. Consistent with the verified
f12-f19 zero-edit precedent.

Coupling: none -- zero-edit lands nothing.

Freshness. HEAD `5c3496e0`, ITEM_BASELINE
`d0d994074ec26ec3c72894857682f07a2480736b`. Pins (WT /
HEAD / BASELINE; `git hash-object` / `git rev-parse HEAD:`
/ `git rev-parse <baseline>:`; WT == BASELINE on all):
indexed `optimizer/nested_planner.py`
`b6ff0a0e998291c5acdf204fd363fd015bb1e1bb` /
`8c3a45f55533cbaf9697013e5d87f599aae65adb`;
`optimizer/join_taxonomy.py`
`aa2890133eb86fd63233214ca9ac2f88a1f00892` /
`8026dc8d3e5b0e47de61e63810e9343155619434`;
`optimizer/plans.py`
`2e962ae2dd0a5be4d05a52cc48334904e1511249` /
`97a524e2a8ec0a160f1ed649bb96df019928d6bc`;
`utils/imports.py` `3ea52b16ce8744e742f9b18289f2c43459877586`
(clean, all three states);
`optimizer/extension.py`
`8e3fe7c1fbc2d854cfcb805beb132e5639650e4d` /
`b7b6c4342e71ec1dbb4047f697745d2796272f6e`;
`optimizer/nested_fetch.py`
`c36826bb6954642590185ac83deba10cc1423177` /
`bedaa76ebf24d010c4535dddbd1f8e5aa26f621a`.
Body-excluded: `optimizer/lateral_fetch.py` `a48cb0a45`
(clean); `keyset.py` `7d43c6b1` / `6af980b8`;
`mutations/resolvers.py` `2ff49673` / `d77a6c68`;
`connection.py` `48de0243` / `99969652`;
`types/converters.py` `22919a32` / `d26ea98f`;
`optimizer/__init__.py` `d400569a` (clean);
`optimizer/single_parent_fetch.py` `3a4bb89b` (clean).
Oracle: `tests/optimizer/test_nested_index_advisory.py`
`66159a29c27e3636245800c26282ff2e79375eed` /
`a6d59a769dcffaa95edb323567056195b1e54927`.
Projection: `docs/README.md` `cdb927d5` / `a3deca98`.
Population: 119 package files (`find | wc -l`).

Dirt attribution (by diff content vs `git show HEAD:`; no
ledger row names these paths, so every hunk below is
concurrent work, untouched): `nested_planner.py` -- the
hunt-owned M2M gate (`:654-655` + docstring `:647-652`)
and truth-migration import/call (`truth.name`, `:1491`);
`plans.py` -- two truth-migration hunks (none in the
composed parsers); `join_taxonomy.py` -- lenient-reader
removal + virtual-link arms (descriptor facts intact);
`extension.py` -- truth/hardening hunks, LRU bodies
untouched; `nested_fetch.py` -- truth-migration only,
indexing section untouched; oracle -- the 2 hunt tests.
The advisory verdict reads WT bytes including the hunt
gate; no landing is proposed, so no hunt line is edited.

### Rejections and exclusions (contract difference + trigger each)

- R1, projection walk vs advisory walk (standing File-R1;
  trigger-checked fresh, not met): `_concrete_order_columns`
  (`:200-222`) SKIPS unrepresentable terms -- forgoing a
  column a scalar-only selection never reads is harmless --
  while `_concrete_order_terms` (`:243-300`) returns None --
  a coverage claim from a partial order is unsound. The
  difference is intact at WT, stated in the S3 docstring.
  Trigger: both walks converging on one unknown policy.
- R2, order-walk name/attname index (standing File-R6;
  trigger-checked fresh, not met): the two-line
  `{name: attname}` + value-set index is a per-site loop
  idiom feeding divergent unknown-policies (R1); lateral
  `_order_columns` (`:1205-1208`) still runs its own linear
  scan with its own contract (db columns, `?`/`pk`/table
  arms). Trigger: a change moving the index content
  identically at both planner sites without touching
  either policy.
- R3, advisory dedup LRU vs the extension LRUs (standing
  File-R7; trigger-checked fresh, not met): emission-dedup
  SET (module-level, values None, hit suppresses, cap 512,
  evict-one) vs deterministic-value MEMO (module-level, hit
  returns, no-source bypass, cap 256, evict-one) vs
  instance plan STORE (cacheability-gated, quarter-sweep,
  counters). Extension dirt is truth-only; all three LRU
  bodies are byte-identical to HEAD. Trigger: two sites
  converging on identical insert/promote/evict/race
  semantics with no per-site bypass.
- R4, exact-type B-tree gate (standing File-R8/J2;
  trigger-checked fresh, not met): `type(index) not in
  _BTREE_INDEX_TYPES` (`:335`) is a per-domain capability
  gate (an uninspected subclass may change the access
  method), beside the deliberate `isinstance` for
  `UniqueConstraint` (`:472`). Trigger: the standing J2
  trigger (a new foreign-object protocol needing
  exclusion).
- R5, fail-soft backend probe guard (standing File-R9/J1;
  trigger-checked fresh, not met): `except Exception:
  return False` (`:151`) is per-domain fail-soft by
  contract (unproven support degrades to UNKNOWN, never to
  a coverage claim). Trigger: the standing J1 trigger.
- R6, attach order vs advisory order (standing
  join_taxonomy-R16; trigger-checked fresh, not met):
  `prefetch_attach_columns` orders connector-first (the
  attach-key protocol) while S11 builds morph-first (the
  B-tree prefix); both docstrings state the contrast, and
  verified `prefetch-attach-column-projection` E2/E10 holds
  the consumer side. Trigger: either order's owner
  changing its rule.
- R7, mutations unique-group derivation (fresh):
  `mutations/resolvers.py:783-815` derives write-path
  co-validation GROUPS from constraints/unique_together/
  unique, while S7 derives ORDERED leading-term shapes for
  physical coverage. Different inputs consumed
  differently, different consumers, different reasons to
  change. Trigger: a change that must move both
  derivations identically.
- R8, keyset `split_order_ref` (fresh, converge-at-owner):
  `keyset.py:192-217` is the documented intentional twin
  of the plans string branch -- malformed is a
  CONFIGURATION error (loud, declaration-time,
  string-only), never a fallback signal. Trigger: the
  keyset path adopting a fallback policy.
- R9, optional-import helpers (fresh, consumer edge):
  S1 composes `import_attr_if_importable` by name (one
  call; the oracle pins `is`-identity with the shared
  result). Contract difference: best-effort import vs
  advisory. Converges with the verified File
  `utils/imports.py` consumer-only edge; `converters.py`
  postgres symbols are consumer siblings, not twins.
  Trigger: the advisory growing local import handling.
- R10, root-connection advice absence (fresh):
  `connection.py` carries zero advisory vocabulary; a root
  page has no partition, so per-partition window advice
  cannot apply. Trigger: root pages gaining
  partition-scoped index advice.
- R11, single-parent fast path (fresh):
  `single_parent_fetch.py` carries zero advisory
  vocabulary; the fetch-time degradation runs a plain
  filtered LIMIT the plan-time recommendation still
  serves. Trigger: the fast path needing its own
  recommendation.
- R12, lateral `_order_columns` (fresh):
  `lateral_fetch.py:1177-1213` maps the order onto db
  COLUMNS for SQL render with a downgrade policy, while S3
  maps onto attname TERMS for coverage with a silence
  policy; both compose the shared entry parser. Trigger:
  the lateral backend consuming coverage verdicts.
- R13, fallback logging (fresh):
  `_log_connection_fallback` (`:1041-1055`) is an
  always-debug per-KEY fallback notice (orchestration),
  while S11 is a WARNING-under-DEBUG per-SHAPE deduped
  recommendation. Trigger: either gaining the other's
  content.
- R14, queued siblings (fresh):
  `relation-connection-to-attr-grammar` (attach-name
  grammar), `scalar-only-window-projection` (window
  `.only()` masking), `keyset-cursor-column-projection`
  (cursor-column masking) vs recommendation. Triggers:
  the grammar driving advice content; a projection
  deriving its own connector or coverage.

Converged without rows: `nested-connection-plan-orchestration`
(loop/latch/deferral), `nested-fetch-strategy-seam` R19
(seam vs emission -- strategy-identity trigger re-checked,
not met), `plan-time-window-slice-resolution` (order input),
`window-partition-resolution` E10 (derivation vs reading),
`logger-single-sourcing` (channel).

## Defects

- D-prior (CONVERGED, no homing owed by this item): File
  `optimizer/nested_planner.py` D1 -- HEAD bytes recommended a
  child-table composite for M2M windows that cannot serve the
  through-partitioned page. At WT bytes the hunt's silent gate
  (`:654-655` + docstring `:647-652`, hunt-owned dirt) plus 2
  oracle tests (`test_m2m_window_stays_silent`,
  `test_real_m2m_joins_carry_a_through_model`) implement the
  fix on D1's exact lines, and the README row
  (`docs/README.md:350-354`) agrees with the fixed body. D1's
  closeout condition (home only if the concurrent arm does not
  land, else fixed-concurrent) is therefore met as
  fixed-concurrent; Worker-0 decides the closeout tick. Owner:
  `optimizer/nested_planner.py::_advise_composite_index`.

No new defects found. The trace surfaced no behavior defect,
no stale contract prose at an owner, and no ticked plan row
that is factually wrong.

## Pending execution

None. Zero-edit census verdict: no `proof:` entry owed
(definition counts need no execution), no `gate:` entry.
Cells per the run-9 f18 typing ruling: the canonical binary
binds and inapplicable-by-construction is NOT claimed --
S2 reads per-alias backend capability
(`connections[alias].features`), an alias/dialect decision
-- so both cells read `unverified` (`--cell sharded` and
`--cell pg` were not authorized; the gate lists them). The
verdict itself is cell-independent (source censuses are
identical across cells).

## Judgment

CONFIRM: the composite-index advisory is already
single-owned -- 20 member definitions in 11 sub-decisions,
every challenge count 1, every other site composing by
name -- so the consolidation is proved with ZERO edits.
The index owner
`optimizer/nested_planner.py::_advise_composite_index` is
CONFIRMED fresh (principle 7), the M2M-silence change
stands as empirical proof that new arms land inside the
owner, all six standing rejections were trigger-checked
fresh and stand, eight fresh exclusions carry contract
differences, and the prior D1 converges as fixed-concurrent.
No `## Implementation` section: nothing tracked was touched.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (lines 239-523
unread at trace time; only the `^#` heading list plus
the `## Judgment` tail above were read, the tail to
locate this append point -- W1 sections above stay
byte-intact). WT bytes at trace time; HEAD bytes via
`git show HEAD:` for the D-prior. Fingerprints: WT/HEAD
`b6ff0a0e`/`8c3a45f5` (nested_planner),
`aa289013`/`8026dc8d` (join_taxonomy),
`2e962ae2`/`97a524e2` (plans),
`3ea52b16`/`3ea52b16` (utils/imports),
`8e3fe7c1`/`b7b6c434` (extension),
`c36826bb`/`bedaa76e` (nested_fetch) -- 6/6 match the
dispatch pins. Item diff:
`git diff d0d99407 --name-only` is the plan edit alone.

### Own member census (WT `nested_planner.py`)

20 definitions, all in `optimizer/nested_planner.py`:

- D1 `_PostgresBTreeIndex` (:113) soft-import binding
- D2 `_BTREE_INDEX_TYPES` (:118) B-tree type set
- D3 `_every_backend_supports_index_column_ordering`
  (:123) every-alias capability probe, fail-soft False
- D4 `_concrete_order_terms` (:243) order walk,
  None on any non-local-concrete term / explicit nulls
- D5 `_index_leading_terms` (:303) index walk,
  None on non-B-tree / condition / opclass / empty /
  lagged / desc-without-capability
- D6-D8 `_INDEX_COVERED` / `_INDEX_ABSENT` /
  `_INDEX_UNKNOWN` (:370-372) tri-state vocabulary
- D9 `_terms_serve_order` (:375) exact-or-full-reverse
- D10 `_index_serves_window` (:397) equality
  permutation + D9
- D11 `_plain_field_terms` (:419) directionless
  unique names to ascending terms
- D12 `_model_index_shapes` (:443) physical-shape
  inventory + saw_uninspectable
- D13 `_index_coverage` (:509) tri-state verdict
- D14 `_describe_index_columns` (:535) DESC-annotated
  renderer
- D15 `_MAX_INDEX_ADVISORY_KEYS` (:569) LRU cap 512
- D16 `_IndexAdvisoryKey` (:570) key record
- D17 `_index_advisory_seen` (:571) LRU store
- D18 `clear_index_advisory_dedup` (:574) reset seam
- D19 `_index_advisory_already_emitted` (:579) LRU
  record-or-suppress
- D20 `_advise_composite_index` (:600) orchestrator:
  M2M silence (WT gate :654-655 + docstring
  :647-652, hunt dirt), connector-None silence,
  morph-first equality build, order-unknown silence,
  effective-order strip, coverage gate, dedup gate,
  DEBUG log level, message wording

My 11 sub-decision grouping: S1 B-tree set
(D1+D2+exact-type check), S2 capability probe (D3),
S3 order walk (D4), S4 index parse (D5), S5 tri-state
verdict (D6-D8+D13), S6 serve rules (D9+D10),
S7 directionless uniques (D11), S8 inventory (D12),
S9 renderer (D14), S10 dedup (D15-D19), S11 emission
orchestration (D20 + sole call-site latch :1482-1486).

Production call graph is a linear chain with single
callers throughout (package-wide search): D3<-D5,
D4<-D20, D5<-D12, D9<-D10, D10<-D13, D11<-D12 (x2),
D12<-D13, D13<-D20, D14<-D20, D19<-D20, D20<-the
first-accepted-window latch alone (:1485). Test
imports are oracle reads (see below), not second
production definitions.

Consumers composing by name (not definitions):
taxonomy connector/morph/through facts
(`parent_join_column`, `content_type_column`,
`through_model`); plans entry parser +
explicit-nulls predicate + `append_unique`;
`utils/imports.py::import_attr_if_importable`;
package logger + `settings.DEBUG`; the F1 latch
caller. Oracles:
`tests/optimizer/test_nested_index_advisory.py`
(literal expectations; helper imports incl. the
tri-state sentinels are the pre-existing oracle
shape, untouched by this zero-edit item).
Projections: member docstrings, the README indexing
paragraph, `nested_fetch.py` module indexing prose,
the taxonomy `content_type_column` advisory note.

### Own challenges (each with count)

- CH1 new represented shape (covering INCLUDE /
  new constraint kind): D12 (+D5 arm) -- count 1.
- CH2 new order-term kind (collation-aware OrderBy):
  D4 -- count 1.
- CH3 new silence arm (another relation kind /
  strategy): D20 body, M2M-gate precedent -- count 1.
- CH4 serve-rule change (partial flip serves):
  D9 -- count 1.
- CH5 emission-policy change (dedup key / cap /
  log level / wording): S10/S11 -- count 1.
- CH6 twelfth-sub-decision stress (through-table
  advisory for M2M instead of silence): lands
  inside D20 + D12 generalized to the through
  model -- still the one chain, no second site
  to touch -- count 1.
- CH7 second-call-site stress: package-wide
  search finds the sole production caller :1485;
  per-window-vs-per-shape emission changes the
  latch only -- count 1.
- CH8 split-verdict stress: equality-permutation
  vs order-serve already split (D10 vs D9);
  changing either touches one -- count 1.
- CH9 second-silence-gate stress: a new
  kind-based silence lands beside the M2M gate
  inside D20 -- count 1.

No posited change forces count > 1. No landable
second owner exists: the chain, the latch, and
the tests are the whole population.

### Owner I would choose

`optimizer/nested_planner.py::_advise_composite_index`
beside its helper chain (principle 7): the sole
production caller lives in the same module; moving
down to `plans.py` would reverse the window->plan
dependency; taxonomy/parse/soft-import facts are
already owned below and composed by name; a new
module would be indirection with one caller.
Narrowest cohesive owner every legitimate consumer
already imports.

### Own matrix discharge

- Ax1 cross-flavor: package-wide "advisory /
  composite index / Advisory only" census -- the
  planner is the sole emitter; no sibling surface
  advises indexes. Searched, not inapplicable.
- Ax2 sync/async: plan-time sync-only, no await
  boundary, no twin. Inapplicable with reason.
- Ax3 derived knowledge: equality / order /
  B-tree facts composed by name from their
  owners; no re-derivation. Searched.
- Ax4 round-trip: `_describe_index_columns`
  renders `(equality, order)` with DESC suffixes
  while `_index_leading_terms` parses dash
  prefixes -- different vocabularies, not an
  encode/decode pair; the `to_attr` grammar is a
  separate family. Searched.
- Ax5 other media: oracles literal; README +
  nested_fetch prose are projections; the D1
  README-vs-body contradiction resolves at WT
  (body fixed, see D-prior). Searched.
- Ax6 omission: window-kind x proof-state
  enumeration -- reverse FK / forward single /
  generic advise; M2M / connector-None /
  order-unknown / index-unknown / covered stay
  silent, each with its guard; M2M was the gap
  and the WT gate closes it. Searched.

### Own exclusion set (pre-read)

Standing rejections expecting trigger re-checks:
ST1 skip-vs-None walk (`_concrete_order_columns`
vs D4); ST2 advisory dedup LRU vs extension
LRUs; ST3 J2 exact-type gate vs shared
exact-type population; ST4 J1 fail-soft except
vs shared except population; ST5 R16 attach
order vs advisory order; ST6 full-flip match vs
order-reversal rendering. Fresh exclusions I
posit: FR1 `ends_in_unique_column` vs coverage;
FR2 `connection.py::_keyset_order_ref`
nulls-raise vs advisory nulls-silence; FR3
`effective_connection_order` production vs
advisory consumption; FR4
`_log_connection_fallback` wording vs advisory
wording; FR5 `keyset_seek_q` redundant-bound
design parallel; FR6 GenericRelation
content-type routing vs morph-first prefix; FR7
soft-import consumer edge (no second
soft-import); FR8 instance-bound plan-cache
strategy keying vs strategy-independent dedup
key; FR9 `lateral_fetch._order_columns`
resolution vs D4; FR10 name/attname index
mechanism cousins.

### Own D-prior read (pre-read)

HEAD bytes (via `git show HEAD:`) lack the M2M
gate and paragraph -- the D1 defect as filed.
WT carries the +9 gate + docstring on D1's
exact lines plus 2 oracle tests
(`test_m2m_window_stays_silent`,
`test_real_m2m_joins_carry_a_through_model`,
hunt dirt in
`tests/optimizer/test_nested_index_advisory.py`).
README M2M row (two indexes, pk terminal)
agrees with the fixed body, not the HEAD body.
Routing fixed-concurrent with Worker-0 deciding
the closeout tick matches D1's own recorded
closeout condition ("close as fixed-concurrent
if the concurrent session lands its arm") -- no
live defect is owed now: the fix exists as
concurrent work this item must neither duplicate
nor disturb, and D1 already sits observed-not-homed
with that condition.

### Reconciliation with `## Findings` (post-read)

Read lines 6-523 whole after the trace above. Every
adjudication below is on fresh Worker-2 evidence, never
W1's word.

- F1 counts + owner: AGREE. My census re-derived the
  SAME 20 symbols (D1-D20 above vs W1's S1-S11
  roster) -- identical membership; only the
  sub-decision NUMBERING differs (my S5-S8 order vs
  W1's), no substance. All eight W1 challenges
  re-counted at 1 from the single-caller chain; my
  CH6-CH9 stresses (twelfth sub-decision, second
  call site, split verdict, second silence gate)
  also count 1, no landable second owner. Owner
  choice identical with identical principle-7
  reasoning. On C1's "S7 plus its arm -- count 1":
  consistent with the f19 convention (cross-helper
  movement inside one chain = one maintained unit);
  no second owner exists either way.
- Empirical-proof claim: AGREE, genuine. `git diff
  HEAD` shows the M2M change as exactly the `:654`
  gate + `:647-652` paragraph (the `truth.name`
  hunk is separate concurrent dirt, correctly
  excluded by W1) plus the 2 oracle tests; the
  bug-hunt record corroborates one gate +
  docstring + tests. The gate reads the taxonomy
  `through_model` fact by name and lands inside
  D20 -- a real arm landing inside the owner.
- R1-R6 standing rejections: ALL STAND, triggers
  correctly re-checked. R1 skip-vs-None intact at
  WT with the S3 docstring stating it; R2
  lateral `:1205-1208` linear scan body-verified
  with its own db-column contract; R3 all three
  LRU bodies clear of every `extension.py` diff
  hunk (WT ranges `:638-651`, `:1386-1424`
  untouched); R4 `:335` exact-type beside the
  deliberate `:472` isinstance, J2 trigger text
  matches the standing record; R5 `:151`
  fail-soft intact, J1 trigger referenced
  correctly; R6 attach-vs-advisory order contrast
  stated in both docstrings, descriptor facts
  intact under doc-only dirt.
- R7-R14 fresh exclusions: ALL ENDORSED, each
  contract difference body-verified. R7
  write-path co-validation groups
  (`:783-815`); R8 `split_order_ref` intentional
  twin per its own docstring (loud config
  error, never fallback); R9 one-call consumer
  edge converging with the verified File
  `utils/imports.py` row; R10/R11 grep-0
  confirmed case-insensitively (plus walker,
  lateral, keyset, converters); R12 lateral
  render-vs-coverage policies; R13
  always-debug per-key notice `:1041-1055`;
  R14 the three queued rows confirmed open in
  the plan. Every trigger is the change that
  would genuinely reunite the sites.
- D-prior + routing: AGREE fixed-concurrent.
  HEAD bytes lack gate + paragraph (defect as
  filed); WT carries gate + docstring + the 2
  named oracle tests on D1's exact lines; the
  README M2M row (two indexes, pk terminal,
  silent-when-unproven) agrees with the fixed
  body. "Worker-0 decides the closeout tick" is
  the RIGHT routing -- it executes D1's own
  recorded closeout condition; no live defect is
  owed now because the fix exists as concurrent
  work this item must not duplicate, and D1
  already sits observed-not-homed with that
  condition.
- Stale-prose / ticked-row claims: AGREE on
  spot-check. R19, X12, prefetch E10,
  window-partition E10 rows read as cited;
  `nested_fetch.py:48-62` prose claims nothing
  the WT body contradicts; R19's "the verdict
  is this seam's" reads as the acceptance
  verdict (consistent with its head sentence
  giving WHAT/dedup to this family) -- no
  action. No stale owner prose found.
- Matrix: AGREE on all six axes against the
  real surface. Ax1 census + R19 trigger check
  verified (no strategy argument, key excludes
  strategy); Ax2 zero-`async` census verified;
  Ax3 single-site reads verified (`:465`,
  `:149`, `:113-120`); Ax4 one-way render
  verified; Ax5 oracle/projection roles
  verified incl. the TREE line; Ax6 enumeration
  verified -- with one correction OWED TO MYSELF:
  my pre-read trace said "forward single
  advises"; W1 is RIGHT (forward_single is
  UNSUPPORTED / non-windowable per the
  taxonomy table, refused at `:1267`, never
  reaches the latch). My error, corrected here;
  verdict unaffected (omission by construction).
- Index rows: endorse NONE OWED. No new family
  named; convergences reuse existing verified /
  queued rows. Worker-0 owes no index write.
- Pending-execution: "None" CORRECT -- census
  verdict, no execution-backed claim, no
  `proof:`/`gate:` owed. Verdict is plain
  `verified`, not pending-execution.
- Cells: both `unverified` CORRECT under the
  f18 ruling (verified at the f18 artifact:
  DB/alias reachable + inapplicable not claimed
  => `unverified`). S2's per-alias read makes
  inapplicable unclaimable; `--cell` runs were
  unauthorized; the verdict is cell-independent.
- Structural gate + negative control: endorse
  NONE-PROPOSED. The reasoning is sound
  (bespoke existence tests forbidden, no
  plausible bypass population beyond enumerated
  by-name consumers, literal oracles guard
  divergence) and matches the f12-f19 zero-edit
  precedent. No negative control runs because
  no gate is proposed.
- Freshness: ALL RE-VERIFIED. Six indexed pins
  (full hashes match, WT == BASELINE on all 6),
  eight body-excluded pins, oracle
  `66159a29`/`a6d59a76`, README
  `cdb927d5`/`a3deca98`, population 119 --
  every fingerprint comparable, none drifted
  since W1's trace.
- Tracked diff: EMPTY, re-verified. No
  `## Implementation` section; 6/6 WT pins
  match dispatch pins; `git diff
  d0d99407 --name-only` is the plan edit alone
  (Worker-0's); status count 475 = 474 +
  artifact. AGENTS.md prose rules: artifact is
  per-cycle scratch (raw `path:NN` allowed, no
  style cleanup owed -- none spent); no
  production provenance (nothing written);
  ASCII-only `.py` untouched; no `pragma`.
- Ruff: VACUOUS on touched tracked paths (none
  touched). Courtesy read-only check on the
  owner path passes (`format --check`: already
  formatted; `check`: all passed).
- Type gates (Worker-2 re-run, shared venv, this
  session): `uv run mypy` -- "Success: no
  issues found in 119 source files"; `uv run
  basedpyright` -- "0 errors, 0 warnings, 0
  notes"; `uv run python scripts/check_any.py`
  -- "130 allowed use(s) of Any at 90 site(s)".
  All exit 0, matching W1's record.
- Probe path: shared venv for the static gates
  (per the KNOWN slots note; no import-execution
  probe was needed -- census verdict); stdlib
  `git`/`grep`/`sed` for censuses. No
  `workspace.py` run (nothing mutates source),
  no `--cell` run (unauthorized), no other
  item's slot touched. No scratch files left
  behind (all probes were read-only shell).

Worker-2 defects found: NONE -- no `## Defects`
entry owed (the D-prior convergence above is
W1's record, endorsed, not a new defect).

VERDICT: `verified` (plain). Zero-edit CONFIRM
sustained on independent evidence: 20/20 census
match, every challenge count 1, owner confirmed,
empirical proof genuine, 6/6 rejections standing,
8/8 exclusions endorsed, D-prior fixed-concurrent
with correct routing, no rows owed, no execution
pending, cells correctly `unverified`.
