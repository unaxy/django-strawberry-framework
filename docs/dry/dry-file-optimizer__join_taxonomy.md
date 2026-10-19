# DRY review: `optimizer/join_taxonomy.py`

Status: verified
Run: 0.0.15 2026-09-22-5

## System trace

Target `django_strawberry_framework/optimizer/join_taxonomy.py` owns the
parent/child join-condition taxonomy: one classifier
(`classify_relation_join`) mapping one relation field to one frozen
`RelationJoinDescriptor` carrying every join-derived fact the fetch
strategies need (windowable partition, child connector, lateral shape,
link fields, through table, generic morph column, attach-complete
projection). Five private readers derive the facts
(`_partition_expr`, `_parent_join_column`, `_through_model`,
`_through_link_fields`, `_generic_child_attname`); `LateralJoinShape`
is the correlated-join vocabulary; `WINDOWABLE_RELATION_KINDS` is the
fetch-strategy windowability set; three lenient aliases
(`_safe_getattr`, `_safe_truthy`, `_safe_flag`) declare the never-raises
read policy once over the shared `utils/relations.py` bodies; and
`_first_truthy` is the guarded first-true picker.

Trace subject is HEAD bytes only (blob
`9b355a5090ce471e373849dd0a61da8f808e78b9`, 347 lines). The worktree
file (blob `e1cbb3e327785de3b59ccafef6b463df52e06396`) carries a
concurrent bug-hunt session's uncommitted edits (`+35/-4`: new
`_child_link_is_virtual` helper plus virtual-ForeignObject degrade arms
in `_partition_expr` / `_parent_join_column` / `classify_relation_join`)
that are NOT traced, NOT edited, NOT reverted, and NOT worked around;
both fingerprints are recorded under Freshness in every finding. The
hunt-dirtied neighbors (`utils/relations.py`, `optimizer/hints.py`,
`optimizer/nested_fetch.py`, `optimizer/nested_planner.py`,
`tests/optimizer/test_join_taxonomy.py`) are read via `git show HEAD:`
throughout; clean neighbors are read from the worktree.

Sites and roles, HEAD bytes:

- Definition `optimizer/join_taxonomy.py::classify_relation_join` (+ the
  five readers, the enum, the set, the record): the single
  join-condition classifier. No second classifier exists
  package-wide (mechanism census over `classify_relation_join`,
  `RelationJoinDescriptor`, `LateralJoinShape`,
  `WINDOWABLE_RELATION_KINDS`, `remote_field`, `.through`,
  `m2m_field_name`, morph slots, `partition_by`).
- Production classify call sites, exactly five in three modules, each
  composing by name: `optimizer/plans.py::window_partition_for_prefetch`
  (partition shim), `optimizer/nested_planner.py::_connector_only_field`
  (connector shim), `optimizer/nested_planner.py::plan_connection_relation`
  (raw-leg classify feeding the windowable gate and the strategy
  request), `optimizer/nested_planner.py::_project_scalar_only_window`
  (attach columns for scalar-only windows),
  `optimizer/walker.py::_ensure_connector_only_fields` (attach columns
  for prefetch child plans).
- Descriptor-field reader census (HEAD-true): `kind` (plans shim
  membership gate); `windowable` (planner gate; request contract "True
  by construction" held at the sole production builder);
  `partition_expr` (plans shim; `nested_fetch.py` windowed-body
  `partition_by`); `parent_join_column` (connector shim; index
  advisory equality prefix); `lateral_shape` + `parent_link_field` +
  `through_child_field` (lateral spec builder; single-parent spec);
  `content_type_column` (advisory equality prefix; attach property
  interior); `prefetch_attach_columns` (walker + planner projection
  writers). `through_model` is SET by the classifier and pinned by
  oracles but read by ZERO production sites at HEAD (family-item
  principle-11 question in F2, not a defect).
- The production input contract is DUAL, and each leg reads only what
  its shape resolves (verified by a walker provenance chain read
  end to end, plus both planner legs):
  - RAW leg: plans shim (documented raw; test-only callers),
    planner `plan_connection_relation` via
    `nested_planner.py::_raw_relation_field` (explicit re-resolve
    because `field_map` holds `FieldMeta`), connector shim
    (test-only callers). Full fidelity: partition, connector,
    through, link fields, morph.
  - FieldMeta leg: walker `_ensure_connector_only_fields` (field-map
    values proven by the `target_pk_name` slot read) and planner
    `_project_scalar_only_window` (also `field_map.get`). Resolves
    kind + connector (fallback slots) + generic morph (parity slots);
    partition/lateral/through degrade to `None`/`False`, which
    neither leg reads (both read attach columns only).
  The module docstring's blanket "takes the RAW Django relation
  field, not a `FieldMeta`" denies the FieldMeta leg production
  depends on: defect D1, filed below, HEAD-clean lines, normal
  homing. It does NOT reopen the standing routing rejections (R2).
- Oracles (all spell expectations independently; no oracle feeds a
  `FieldMeta` to the classifier): `tests/optimizer/test_join_taxonomy.py`
  at HEAD (14 tests: 1 set pin, 6 kind/shape pins over 6 real
  models, three degrade doubles, three fail-closed hostile targets,
  one parametrized hostile-flag test); shim pins (`test_plans.py` six
  partition rows, `test_walker.py` connector + writer rows);
  strategy/keyset/parity builders feeding raw fields; live suites
  `test_single_parent_fastpath_api.py` (DIRECT_FK + link engagement
  over HTTP) and `test_optimizer_auto_api.py` (window `PARTITION BY`
  SQL over HTTP). No live suite pins a generic windowed connection
  (family question in F3, not a defect).
- Projections: the module taxonomy table + member docstrings, both
  shim docstrings, the request/lateral/single-parent/advisory
  consumer docstrings stating composition, spec-033 Decision 4
  (partition derivation; raw-field rule), the spec-033 rationale
  Non-Decision deliberation + KANBAN open question on the plans
  shim's zero-caller existence, the `exceptions.py` window-partition
  bullet, TREE module lines. No GLOSSARY anchor names this module
  (searched).

Established inputs (verified rows, used as triggers to check, never
re-litigated): family `relation-kind-taxonomy` (R-A windowability vs
many-side, R-B raw-vs-snapshot layers, R-C read-body sharing, the
morph detect/carry/resolve tri-split, kind-token USES); File
`optimizer/field_meta.py` FL5/FL7 (slot ownership; taxonomy fallbacks
as consumers) and R1 (routing rejection); File `optimizer/plans.py`
F-M `window-partition-resolution` (family NAME adopted in F1 with its
candidate owner; owner-side sites recorded here extend, never
narrow, its census); File `optimizer/lateral_fetch.py` F-G
`join-vocabulary` WITHDRAWN in favor of owner-item naming ("No index
row owed"); File `optimizer/single_parent_fetch.py` HF-E (owner
join_taxonomy, consistent); File `optimizer/extension.py`
(zero taxonomy vocabulary); File `_request_body.py` J1 (shared
except-guard rejected). File `optimizer/walker.py` is REOPENED: its
F-W9 `prefetch-attach-column-projection` and R5 are prior evidence
only; both boundaries are re-derived fresh below (F3 and R5) and
converged, and the names are adopted to avoid forking.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. No flavor outside the
   optimizer derives join facts: the package-wide vocabulary census
   (`classify_relation_join`, descriptor/enum/set names,
   `remote_field`, `.through`, `m2m_field_name`, morph slots,
   `partition_by`) hits only optimizer modules (the target plus
   its six consumers: plans, nested_planner, nested_fetch,
   lateral_fetch, single_parent_fetch, walker) plus oracles and
   prose. Nearest neighbors each own a
   distinct contract and are rejected with triggers: filters
   to-field read (R9), write-surface kind screens (standing R-D),
   serializer cardinality (standing R-E), cascade predicates
   (standing R-F) — all three trigger-checked via this file: the
   taxonomy introduces no write-surface coupling (zero taxonomy
   vocabulary outside the optimizer), so none of their triggers is
   met — `instance_accessor`
   vs partition query-name (R7), pk-attname readers (R8, R15),
   FieldMeta slot stamp vs fallback reads (standing FL5/FL7 +
   R1/R-B, trigger-checked). The strategy vocabulary
   (`nested_fetch.py` names/instances) composes with the shape
   vocabulary as a strategy-times-shape matrix, not a second shape
   rule (R6). No mirrored second definition.
2. Sync/async twins — NO SUCH SURFACE. HEAD bytes contain zero
   `async`/`await` (grep-verified); the target is pure derivation
   over in-memory relation metadata plus contained truth tests.
   There is no colored twin to drift.
3. Derived rather than repeated knowledge — SEARCHED. Every
   derivation composes its owner by name: `relation_kind` for
   cardinality (never re-decided from flags); `WINDOWABLE_RELATION_KINDS`
   for the plans-shim kind gate (never re-listed); descriptor fields
   for every fetch fact (never re-derived from the field at a
   consumer); `parent_link_field.model` for the lateral through
   table (the carried `through_model` is the one unread spelling —
   F2 question, not a second derivation); `_raw_relation_field`
   re-resolves raw from `_meta` (never via `FieldMeta`, the
   carriage gap). The dual input legs resolve disjoint-needed
   subsets from one body, not two spellings. No reconstructed fact
   found a second definition.
4. Inverse / round-trip pairs — NO SUCH SURFACE. One-way
   classification: no un-classify, no parse-back, no encode/decode
   halves. The descriptor is never re-fed as classifier input
   (producer direction verified at every call site).
5. Contracts restated in another medium — SEARCHED. Every medium a
   change moves is classified in System trace: oracles (package
   pins spelling literals and inline doubles; shim pins; strategy
   builders; two live suites asserting wire SQL, never helper
   bodies) and projections (target + consumer docstrings, spec-033
   Decision 4 + rationale, exceptions bullet, TREE lines, KANBAN
   open question). The bilateral raw-field rationale (target
   clause + planner/shim/spec restatements) is one carriage-gap
   decision projected at each site that must honor it; a contract
   change moves production + prose together legitimately. The
   "not a `FieldMeta`" clause is inaccurate prose, filed as D1,
   not a second definition.
6. Enforcement by omission — SEARCHED. All five input shapes
   enumerated against every descriptor fact: reverse FK / reverse
   O2O (full raw fidelity; FieldMeta leg resolves connector, drops
   partition); forward M2M / reverse M2M (partition by query/field
   name; connector is target pk; through + link pair or
   `(None, None)`); forward single (connector resolves, partition
   `None`, shape `UNSUPPORTED`); generic (partition + attach on
   `object_id`, morph column, lateral shape with `None` link);
   hostile/missing metadata (fully unresolved descriptor, pinned).
   Every `None`/`False` has exactly one handling consumer: shim
   raises (plans) / returns `None` (connector), planner degrades
   to unplanned, lateral refuses on `None` link or non-DIRECT_FK
   visibility shape, single-parent refuses on shape-or-`None`,
   walker logs and skips, advisory silences, scalar window
   appends nothing. `lateral_shape` has exactly two production
   readers and both refuse the generic `None`-link shape (census);
   `windowable` gates the sole production request builder with no
   reassignment between gate and build. No member lacks its guard;
   no gap found, no defect filed on this axis.

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`9b355a50`, 347 lines), read via `git show HEAD:` plus an AST
dump. Count: 19 nodes. Every member lands below; nothing is
unassigned.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (graph-node table + raw-field clause + fallback paragraph) | Projection at the owner; supports F1/F2/F3 (prose, not a definition); the raw-field clause is D1's subject |
| 1-4 | `__future__`, `enum`, `dataclasses`, `typing` imports | Mechanics L1; no rule |
| 5 | `..utils.relations` import (`RelationKind`, `relation_attr`, `relation_bool`, `relation_kind`, `safe_truthy`) | Consumer links to relations-owned rules (L1); kind-token USES per the verified family (F1) |
| 6 | `LateralJoinShape` | F2 (`lateral-join-shape`) |
| 7 | `WINDOWABLE_RELATION_KINDS` | F1 (`window-partition-resolution`); standing separation from the many-side set (R1) |
| 8 | `_safe_getattr` | L1 (lenient-alias declaration; R13) |
| 9 | `_safe_truthy` alias | L1 (alias; R13) |
| 10 | `_safe_flag` | L1 (lenient-alias declaration; R13) |
| 11 | `_first_truthy` | L1 (file-local guarded picker; R4) |
| 12 | `RelationJoinDescriptor` (9 slots + `prefetch_attach_columns`) | Split: `kind`/`windowable`/`partition_expr`/`parent_join_column` to F1; `lateral_shape`/`parent_link_field`/`through_child_field`/`through_model` to F2; `content_type_column` + property to F3; frozen-record form to L1 |
| 13 | `_partition_expr` | F1 |
| 14 | `_parent_join_column` | F1 |
| 15 | `_through_model` | F2 |
| 16 | `_through_link_fields` | F2 (R10 records the resolving mechanism) |
| 17 | `_generic_child_attname` | F3 (F1 composes the `object_id` call as shared derivation) |
| 18 | `classify_relation_join` | Split: kind/windowable/partition/connector arms + kind-fallback to F1; lateral arms + generic `None`-link degrade to F2; generic attach/morph arms to F3; never-raises posture stated in each family's contract |

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed, never
counted):

- Partition derivation: posit forward-M2M partitioning by the
  accessor instead of the reverse query name — 1 definition
  (`_partition_expr`). The shim, the fetch `partition_by` read, and
  the shim test pins follow by construction. Posit a second
  `remote_field.attname`-or-name derivation — none exists (the
  only other `remote_field` code read package-wide is the filters
  to-field rule, R9; the rest is prose).
- Connector derivation: posit M2M attach needing through-table
  columns instead of the child pk — 1 definition
  (`_parent_join_column`). The connector shim and both projection
  writers follow. Posit a second connector derivation — none
  exists (the walker attname append is the source-local column,
  R5; the scalar-window pk is edge identity, R8).
- Windowability: posit admitting a sixth kind or flipping
  reverse-O2O out — 1 definition (the set + the classify arm move
  as one module). The shim gate and the planner gate follow.
  Posit deriving windowability from the many-side set — the
  standing R-A split (reverse O2O) forbids it; trigger not met.
- Kind fallback: posit a hostile field raising instead of sinking
  to `forward_single` — 1 definition (the classify `except` arm).
- Lateral shape: posit a fourth shape arm — 1 definition (the enum
  + classify arms move as one module); the two backend selectors
  extend as enforcement sites. Posit a second shape vocabulary —
  none exists (the strategy vocabulary is the other axis of the
  matrix, R6).
- Link-field resolution: posit resolving through-FK pairs by
  scanning through-model FK targets — 1 definition
  (`_through_link_fields`); rejected at the owner for
  self-referential ambiguity (R10). Posit a second link
  resolution — none exists (no other `m2m_field_name` reader;
  lateral derives the through table from the resolved link).
- Generic lateral degrade: posit resolving a lateral link for
  generic relations — 1 definition (the generic arm); both
  backend refusals key off the same `None` (R11 records the
  no-GENERIC-arm decision).
- Attach projection: posit a third attach column — 1 definition
  (the property + helper calls); both writers follow. Posit a
  second attach derivation — none exists (both writers compose
  the property; census).
- Morph resolution: posit resolving morph names without
  `related_model` — 1 definition (`_generic_child_attname`,
  shared by F1's partition call and F3's attach calls). Posit a
  second morph-column resolution — none exists (detect/carry/
  resolve tri-split stands, R14).
- Attach order: posit morph-first attach — 1 definition (the
  property); the advisory prefix order is the deliberate
  counter-rule (R16).
- Lenient aliases: posit a strict taxonomy read — moves the three
  one-line declarations (1 module); the policy body stays shared
  (R3). Posit a second lenient consumer — none exists (sole-
  consumer census; R13 trigger).
- Guarded pick: posit unguarded `or` — 1 definition
  (`_first_truthy`); inline `or` cannot express the contained
  truth test (R4).

No read-only probe was needed: every claim above is decided
statically against HEAD bytes (AST census, HEAD-true
package-wide reader censuses, body reads, provenance-chain
reads), so no `docs/dry/temp-tests/dry-file-optimizer__join_taxonomy/`
scope was created and no pytest ran.

## Findings

### F1 — Window partition resolution (ADOPTED family `window-partition-resolution`, open)

Family name and candidate owner adopted from File
`optimizer/plans.py` F-M (verified): the parent-side partition
expression a windowed prefetch groups by, the child-side
connector column Django's prefetch attach reads, the
windowability predicate gating both, the hostile-kind sink, and
the never-raises posture over all of them. Owner-side sites
recorded here extend F-M's consumer-side census (derivations,
set, planner gate, oracles); the family item reconciles scope.
Varies per relation shape, kind vocabulary, partition/connector
derivation, fallback sink.

Sites and roles: definition `optimizer/join_taxonomy.py`
(`WINDOWABLE_RELATION_KINDS`, `_partition_expr`,
`_parent_join_column`, the kind/windowable/partition/connector
arms of `classify_relation_join` incl. the `object_id` generic
partition call and the `forward_single` sink; HEAD `9b355a50`).
Consumers composing by name: `optimizer/plans.py::`
`window_partition_for_prefetch` (classify + kind-gate + dual
`OptimizerError`, zero production callers; test-only callers are
six `test_plans.py` pins plus one two-call `test_walker.py`
test),
`optimizer/nested_planner.py::_connector_only_field`
(`parent_join_column` projection, zero production callers, one
test pin), `optimizer/nested_planner.py::plan_connection_relation`
(raw-leg classify + `windowable` gate + request carriage),
`optimizer/nested_fetch.py` windowed body (`partition_by`). The
kind-token comparisons are USES of the shared vocabulary (verified
family). Oracles: `tests/optimizer/test_join_taxonomy.py`
partition/connector/windowable/hostile rows, `test_plans.py` shim
rows, `test_walker.py` connector rows, live window-SQL suites.
Projections: module table, shim + gate docstrings, spec-033
Decision 4 + rationale, exceptions bullet, KANBAN open question.

Challenges: all F1 rows in `### Challenges` count 1 definition;
no second partition, connector, windowability, or fallback
definition exists. Owner by responsibility:
`classify_relation_join` beside the set and readers — the
narrowest module every consumer already imports downward with no
reversal (verified F-M candidate). The family item audits the
rule whole and decides the structural gate; this file item makes
no edit. Family-item questions carried, not decided: (a) the
plans-shim existence (HOMED: spec-033 rationale Non-Decision
deliberation + KANBAN open question; maintainer picks delete /
route-production / keep-as-introspection); (b) the connector-shim
existence (UNHOMED: zero production callers, one pin, no standing
record — the family item routes to the maintainer); (c) D1's corrected dual
input contract is the contract the family verifies against
(cross-reference, no landing coupling).

Freshness: target HEAD
`9b355a5090ce471e373849dd0a61da8f808e78b9` (worktree
`e1cbb3e327785de3b59ccafef6b463df52e06396`, concurrent hunt dirt
in `_partition_expr` / `_parent_join_column` / classify arms —
NOT traced); `optimizer/plans.py` `cce98531`,
`optimizer/nested_planner.py` HEAD `b4dfd4a6` (worktree
`225011b6` hunt dirt in the advisory — NOT traced),
`optimizer/nested_fetch.py` HEAD `4d8d37a7` (worktree `29ce5201`
hunt dirt — NOT traced), `utils/relations.py` HEAD `7662b0bb`
(worktree `1cf81e58` hunt dirt — NOT traced),
`tests/optimizer/test_join_taxonomy.py` HEAD `481294c3`
(worktree `ff3c7fe8` hunt dirt — NOT traced),
`tests/optimizer/test_plans.py` `1e09d6d8`,
`tests/optimizer/test_walker.py` `78c0f7a4`,
`test_optimizer_auto_api.py` `ca9fea06`, spec-033 `5c6b9a8b`,
rationale `cf74ca17`, KANBAN `dae7e797`.

### F2 — Lateral join shape (NEW family `lateral-join-shape`, open)

Contract: which correlated-join shape a relation takes
(`DIRECT_FK` child-carries-parent-id, `THROUGH_TABLE` join-table
attach, `UNSUPPORTED` single-valued) plus the resolved link
FIELD OBJECTS expressing it (child-side FK; through parent/child
FK pair from the forward field's own naming API, sides swapping
on the reverse rel; `None` when unresolvable), the carried
through table, and the generic lateral degrade (`DIRECT_FK`
shape with `None` link so both backends refuse — no GENERIC
arm). Never-raises throughout. Varies per relation shape, shape
vocabulary, link-resolution mechanism, degrade posture. (File
`optimizer/lateral_fetch.py` F-G `join-vocabulary` was
withdrawn in favor of owner-item naming; single-parent HF-E
points at this owner consistently.)

Sites and roles: definition `optimizer/join_taxonomy.py`
(`LateralJoinShape`, `_through_model`, `_through_link_fields`,
the lateral arms + generic degrade of `classify_relation_join`;
HEAD `9b355a50`). Consumers composing by name:
`optimizer/lateral_fetch.py::_build_lateral_spec` (shape
selector + link reads + `None`-link refusal + DIRECT_FK-only
visibility shape) and `optimizer/single_parent_fetch.py::`
`single_parent_spec` (shape-plus-link eligibility conjunction);
no third `lateral_shape` reader exists (census). Oracles: the
shape/link/through pins in `tests/optimizer/test_join_taxonomy.py`
(incl. the raising-`get_field` no-pair row), strategy/lateral/
keyset/parity builders, live fastpath + auto suites.
Projections: module table, backend docstrings stating taxonomy
ownership of link resolution. `through_model` rides the
descriptor but has ZERO production readers at HEAD (only oracle
pins): principle-11 keep-or-delete question for the family item
at its own HEAD — concurrent hunt work adds a first production
reader in the index advisory (observed worktree dirt, NOT
evidence, NOT relied upon).

Challenges: all F2 rows count 1 definition; no second shape
vocabulary, through resolution, or link resolution exists.
Owner: the enum beside the classifier — the narrowest module
both backends already import. The family item audits the rule
whole (shape, enum, resolutions, degrade, both backend
read-disciplines, the `through_model` question) and decides the
gate; this file item makes no edit.

Freshness: target HEAD `9b355a50` (worktree `e1cbb3e3` hunt
dirt in the link arm — NOT traced);
`optimizer/lateral_fetch.py` `db1ea315`,
`optimizer/single_parent_fetch.py` `e995270a`,
`optimizer/nested_fetch.py` HEAD `4d8d37a7` (worktree `29ce5201`
dirt NOT traced), `utils/relations.py` HEAD `7662b0bb`
(worktree `1cf81e58` dirt NOT traced),
`tests/optimizer/test_join_taxonomy.py` HEAD `481294c3`
(worktree `ff3c7fe8` dirt NOT traced),
`tests/optimizer/_builders.py` `567defa9`,
`tests/optimizer/test_lateral_fetch.py` `67431054`,
`tests/test_keyset.py` `e5655de7`,
`tests/test_lateral_pg_parity.py` `c66aead2`,
`test_single_parent_fastpath_api.py` `492fac73`,
`test_optimizer_auto_api.py` `ca9fea06`.

### F3 — Prefetch attach column projection (ADOPTED family `prefetch-attach-column-projection`, open)

Family boundary re-derived fresh against HEAD and CONVERGED with
File `optimizer/walker.py` F-W9 (prior evidence only — nothing
inherited); the name is adopted to avoid forking. Contract: the
attach-complete column set projection writers must `.only()`
(connector, plus the generic morph half), the generic child-column
resolution primitive, the connector-first attach-key order, and
the never-raises posture. Varies per relation shape, morph
presence, projection-completeness policy, order. The generic
`object_id` PARTITION call stays F1's (partition is the grouping
rule); this family owns the attach set, the morph column, and
the resolution helper F1 composes.

Sites and roles: definition `optimizer/join_taxonomy.py`
(`_generic_child_attname`, `content_type_column`, the generic
attach/morph classify arms,
`RelationJoinDescriptor.prefetch_attach_columns`; HEAD
`9b355a50`). Consumers composing by name:
`optimizer/walker.py::_ensure_connector_only_fields` (prefetch
child plans; log-and-skip on empty) and
`optimizer/nested_planner.py::_project_scalar_only_window`
(scalar-only windows; same-owner comment); the index advisory
composes the morph + connector facts for its morph-first
equality prefix (R16). Both attach readers feed FieldMeta legs
(provenance-chained). Oracles: generic attach/morph pins in
`tests/optimizer/test_join_taxonomy.py`, walker writer rows in
`test_walker.py`; no live suite pins a generic windowed
connection (census over `test_query/`; whether the shape is
live-reachable through the finalizer synthesis gate is the
family item's question, not a defect). Projections: member
docstrings (incl. the attach-vs-advisory order contrast),
writer comments.

Challenges: all F3 rows count 1 definition; no second attach
derivation, morph resolution, or attach order exists. Owner:
the property beside the helper — the narrowest module both
writers already import. The family item audits the rule whole
and decides the gate; this file item makes no edit.

Freshness: target HEAD `9b355a50` (worktree `e1cbb3e3` hunt
dirt — NOT traced); `optimizer/walker.py` `e8d80005` (REOPENED
file; bodies read fresh at HEAD, artifact used as trigger
only), `optimizer/nested_planner.py` HEAD `b4dfd4a6`
(worktree `225011b6` dirt NOT traced),
`optimizer/field_meta.py` `7215c887` (parity-slot carriage),
`utils/relations.py` HEAD `7662b0bb` (worktree `1cf81e58` dirt
NOT traced), `tests/optimizer/test_join_taxonomy.py` HEAD
`481294c3` (worktree `ff3c7fe8` dirt NOT traced),
`tests/optimizer/test_walker.py` `78c0f7a4`.

### L1 — Module mechanics (file-local)

Import mechanics (future/enum/dataclasses/typing), the
`..utils.relations` consumer import (five names, sole
lenient-mode consumer — census), the frozen-record form (nine
slots, three defaulted), the enum form (three string-valued
members), the three lenient-alias declarations (one-line policy
pins over the shared bodies), and the guarded picker. Single
definition each, single module, no second site. Challenge: posit
a second frozen join record, a second shape enum, a second
lenient-policy declaration, a second guarded picker — none
exists (package-wide censuses). Note (not a defect): the alias
comment's "22 call sites" counts 23 direct AST uses
(18 + 3 + 2), 22 only if the picker's own interior use is
excluded; ambiguous, no behavior, the family item may reword.

Freshness: target HEAD `9b355a50`; `utils/relations.py` HEAD
`7662b0bb` (sole-lenient-consumer census over the HEAD package
tree).

### R1 — `WINDOWABLE_RELATION_KINDS` vs `MANY_SIDE_RELATION_KINDS` (rejected, standing)

Family `relation-kind-taxonomy` R-A (verified) already separates
them: windowability is a fetch-strategy predicate, not
cardinality — reverse O2O is windowable (child carries the
parent id) yet single-valued, so it cannot derive from the
many-side set. Trigger checked against HEAD, not met: the sets
still differ exactly on `reverse_one_to_one`, and the fetch
strategy still distinguishes grouping from rendering. The
standing rejection and its trigger stand; home stays the set
comment plus the module taxonomy table.

### R2 — Routing taxonomy reads through `FieldMeta` (rejected, standing)

File `optimizer/field_meta.py` R1 plus family
`relation-kind-taxonomy` R-B (both verified) already reject
replacing the raw reads with snapshot reads: partition and
through facts need `remote_field` / `through`, neither carried
on `FieldMeta` by design, under a never-raises lenient policy
the strict stamp cannot offer. Trigger checked against HEAD,
not met: `FieldMeta` still carries neither slot (full slot
census), and the planner still re-resolves raw precisely for
that gap. D1 (the FieldMeta attach leg) does NOT reopen this:
subset-tolerance for connector/morph facts is not routing the
partition/through reads through the snapshot. The standing
rejections and their trigger stand.

### R3 — Strict/lenient read bodies (rejected, standing: already one body)

Family `relation-kind-taxonomy` R-C (verified): two failure
policies, one read body — already shared at
`utils/relations.py::relation_attr` / `::relation_bool`, not two
families. Trigger checked against HEAD, not met: the taxonomy
still composes both bodies with `lenient=True`, still the sole
lenient consumer package-wide (census), and no third policy
exists. The standing record stands.

### R4 — `_first_truthy` vs inline `or` chains (rejected)

The picker's rule is "the first value testing true, a raising
truth test counting as `False`" — inline `or` cannot express
the contained second half, and the package holds no second
named guarded-picker (census). Contract difference: contained
truth-test policy vs boolean short-circuit idiom.
Reconsideration trigger: a second site needs raising-tolerant
first-pick — then the helper (not the idiom) is the shared
definition.

### R5 — `_record_relation_access` attname vs the connector shim (rejected, re-verified fresh)

File `optimizer/walker.py` R5 (prior evidence only) claimed
"different columns for different joins"; re-derived fresh at
HEAD and converged: `_record_relation_access` appends the
SOURCE-row local column (`FieldMeta.attname` — the forward FK
`category_id`, `None` for reverse relations, feeding the
select-side projection and FK-id elision), while the connector
shim projects the CHILD-side attach column (reverse child FK,
forward target pk, M2M related pk). For a forward FK both fire
with different values (`category_id` vs `id`); for reverse
shapes only the connector fires. Contract difference:
select-side local projection vs prefetch attach key.
Reconsideration trigger (adopted from prior): a join needing
BOTH columns from one call site.

### R6 — `LateralJoinShape` vs `NestedConnectionStrategy` (rejected)

Join shape (`DIRECT_FK` / `THROUGH_TABLE` / `UNSUPPORTED`) and
fetch strategy (`windowed` / `lateral` / `auto` + instances)
are the two axes of one matrix, not one vocabulary: a
lateral-strategy request over a `THROUGH_TABLE` shape joins the
through table INSIDE the lateral subquery. Contract difference:
how the child joins vs which backend plans and executes.
Reconsideration trigger: the two vocabularies merge into one
enum.

### R7 — Partition query-name vs lookup accessor (rejected)

The forward-M2M partition uses the target's reverse QUERY name
(`Book.genres` -> `"books"`, pinned NOT-accessor), while the
prefetch LOOKUP string uses `instance_accessor` (`"book_set"`
where they split). Both owners state the split: the partition
is the prefetch attach key Django resolves, the lookup is the
instance-attribute path `prefetch_related` walks. Contract
difference: grouping key vs traversal path. Reconsideration
trigger: Django unifies the two vocabularies.

### R8 — The six `pk.attname` readers (rejected)

Six production sites read `pk.attname` under six contracts:
this module's M2M connector (attach key), the lateral
`"pk"`-order-term resolution (order columns), the scalar
window's unconditional pk (Relay edge identity — the nearest
miss, adjacent to the attach append in one statement block but
deduped by `append_unique` precisely because the REASONS stay
separate), the order rule's unique terminator, the Relay
`id_attr` projection, and id resolution. Contract difference:
same column value, six reasons to read it. Reconsideration
trigger: any two reasons collapse by construction (then those
two — not all six — merge).

### R9 — Filters to-field read vs partition derivation (rejected)

`filters/sets.py::_forward_relation_extra` reads
`field.remote_field.field_name` for the filter `to_field_name`
extra. That is filter vocabulary (which target column a
relation filter addresses), not fetch grouping. It is also the
only other `remote_field` code read package-wide (census; the
rest is prose citing this module's need). Contract difference:
filter addressing vs prefetch grouping. Reconsideration
trigger: a filter consumer needs the prefetch partition key.

### R10 — `m2m_field_name` resolution vs scanning through-model FKs (rejected, at owner)

`_through_link_fields` resolves the through pair from the
forward field's own naming API rather than scanning
through-model FKs by target. The owner docstring records why:
self-referential M2Ms make target-scanning ambiguous while the
naming API stays correct. Contract difference: declared naming
vs inferred targets. Reconsideration trigger: Django removes
or breaks the `m2m_field_name` naming API.

### R11 — No `GENERIC` lateral arm (rejected, at owner)

A generic relation classifies `DIRECT_FK` with a `None` link so
both lateral backends refuse and the strategy degrades to the
windowed body; the classifier comment states no
`LateralJoinShape.GENERIC` arm exists or is wanted, and the
oracle pins the `None`-link refusal contract. Contract
difference: degrade-by-absence vs a morph-capable join arm.
Reconsideration trigger: a backend that can express the
content-type-constrained join natively.

### R12 — Shared `except` guard (rejected, standing)

File `_request_body.py` J1 (verified) already rejects one
shared `except Exception` guard across its 85-site population:
per-site failure policies with distinct answers. This file's
four contained reads (kind sink, M2M `None`, link-pair
`(None, None)`, morph `None`) are per-site fail-closed answers
under the never-raises contract, each pinned. Trigger checked
against HEAD, not met: no new shared-guard mechanism adopted.
The standing rejection and its trigger stand.

### R13 — Lenient aliases vs a shared lenient-readers module (rejected)

The three local names are a 3-line policy declaration ("lenient
here") over the already-shared bodies, kept local so the 23
call sites read as taxonomy code. Extracting a "lenient
readers" module would couple this file to machinery serving one
consumer. Contract difference: local policy pin vs shared
machinery. Reconsideration trigger: a second `lenient=True`
consumer appears — then the declaration moves to the shared
owner with it.

### R14 — Morph detect / carry / resolve tri-split (rejected, standing)

Family `relation-kind-taxonomy` (verified W2 section): the
generic slots are DETECTED by `relation_kind`, CARRIED by
`FieldMeta`, RESOLVED to attnames by `_generic_child_attname`
(consuming `kind`) — three contracts over one slot pair.
Trigger checked against HEAD, not met: still exactly these
three readers (census), each still owning its contract. The
standing separation stands.

### R15 — M2M pk-ATTNAME vs `_target_pk_name` pk-NAME (rejected)

The M2M connector reads the target pk's ATTNAME (the column
attribute the attach protocol loads); `field_meta.py::`
`_target_pk_name` reads the pk's NAME (the field identifier for
the to-field-vs-pk comparison). Equal on stock pks, different
contracts where they split (relation primary keys: name
`"user"` vs attname `"user_id"`). Contract difference: loaded
column attribute vs field identifier. Reconsideration trigger:
a seam needing both projections from one read.

### R16 — Attach order vs advisory order (rejected, at owner)

`prefetch_attach_columns` orders connector-first (Django's
attach-key order); the index advisory prefixes morph-first
(the B-tree equality-prefix order). The property docstring
states the contrast deliberately: two orders for two readers
of the same two columns. Contract difference: attach protocol
order vs index-prefix order. Reconsideration trigger: either
order's owner changes its rule.

## Defects

### D1 — Module input contract denies the production FieldMeta leg (HEAD defect — home normally)

The module docstring states the classifier "takes the RAW
Django relation field (or rel descriptor), not a `FieldMeta`",
and the fallback paragraph frames the `reverse_connector_attname`
/ `target_field_attname` arms as preserving "the exact
test-double contract the two shims' direct callers rely on".
Production contradicts both framings: the walker feeds live
`FieldMeta` snapshots to `classify_relation_join` on every
prefetch child plan (`walker.py::_ensure_connector_only_fields`
<- `_build_prefetch_child_queryset_from_base` <-
`_build_prefetch_child_queryset` <- `_plan_prefetch_relation`
<- `_dispatch_single_relation` <- `_walk_selections` <-
`_resolve_selection_target` over the `FieldMeta` field map —
chain read end to end, `FieldMeta` shape proven by the
`target_pk_name` slot read), and the nested planner feeds
`FieldMeta` from `_project_scalar_only_window`; both legs read
attach columns that resolve ONLY through the fallback slots
(reverse connector, forward target attname) and parity slots
(generic morph). The fallback arms are production load-bearing,
not double-only.

Contract row broken: the module's own input contract. Feasible
project shape: any consumer schema with a list relation or
nested connection (universal — every fakeshop app). Wire input
reaching it: any GraphQL query planning a list prefetch or a
scalar-only window. Blast radius if trusted: a maintainer
removing the "double-only" fallback arms silently degrades
every walker-planned connector projection to log-and-skip
(deferred per-row refetch; no error), and NO oracle would
catch it — no test feeds a `FieldMeta` to the classifier
(complete call-site census: raw fields and namespace/class
doubles only).

Owner: `optimizer/join_taxonomy.py` module docstring
+ fallback paragraph (this file; HEAD-clean lines, NOT
hunt-owned — normal homing, no closeout condition). Fix
direction (not this item's): state the dual input contract at
the owner (raw descriptor -> full fidelity incl. partition,
through, link fields; `FieldMeta` snapshot -> kind + connector
+ morph subset) and add `FieldMeta`-fed oracle pins for all
five shapes. Worker 0: home on a NAMED card at closeout. Note:
this does NOT reopen standing field_meta-R1/R-B (filed as R2
above): subset-tolerance is not routing.

Near-misses considered against HEAD bytes and NOT filed: (a)
`through_model` with zero production readers at HEAD — a
carried, oracle-pinned fact, not broken behavior; F2's
principle-11 question (concurrent work adds a reader —
observed, not relied upon). (b) The HEAD M2M index advisory
recommending a child-table composite for a through-partitioned
window — advisory-only prose (no behavior), on hunt-owned
lines the maintainer's hunt is deciding; not filed. (c) The
"22 call sites" comment counting 23 direct AST uses — ambiguous
(22 exact excluding the picker's interior use), no behavior;
L1 note. (d) No live pin for a generic windowed connection —
reachability through the finalizer gate unproven, tier
placement is family-item territory; F3 question. (e) Both
shims' zero production callers — test-pinned boundary names,
nothing broken; F1 family questions (one homed, one routed by
the family item).

Freshness: target HEAD `9b355a50` (worktree `e1cbb3e3` hunt
dirt — NOT traced; D1's lines are the HEAD-clean docstring);
`optimizer/walker.py` `e8d80005`, `optimizer/field_meta.py`
`7215c887`, `optimizer/nested_planner.py` HEAD `b4dfd4a6`
(worktree `225011b6` dirt NOT traced), `utils/relations.py`
HEAD `7662b0bb` (worktree `1cf81e58` dirt NOT traced),
`tests/optimizer/test_join_taxonomy.py` HEAD `481294c3`
(worktree `ff3c7fe8` dirt NOT traced),
`tests/optimizer/test_walker.py` `78c0f7a4`.

## Pending execution

None. All conclusions are static against HEAD bytes; no probe,
no pytest, no scratch scope. Sharded and Postgres cells are
inapplicable by construction: the target reaches no database,
alias, or dialect decision (pure derivation over in-memory
relation metadata; the PG-marked lateral/keyset/parity rows pin
fetch SQL with descriptors as input, and no claim here depends
on their execution).

## Judgment

Zero-edit file item: the target single-owns the join-condition
classification across three rules (window partition resolution,
lateral join shape, attach column projection), consumed by name
at all five production call sites with no second definition on
any variation axis. One rule adopted from a verified neighbor
family name (F1), one boundary re-derived fresh converging with
reopened prior evidence (F3), one named here (F2); one
file-local row; sixteen rejections (five standing rejections
trigger-checked, one prior rejection re-verified fresh, ten
fresh). One HEAD defect filed with owner and fix direction
(D1: docstring denies the production FieldMeta leg). No pending
execution, no production edit, no test edit. HEAD stayed
`5ee86193` throughout; the item touched nothing tracked.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.)

- Family `window-partition-resolution` | Owner
  `optimizer/join_taxonomy.py::classify_relation_join` (with
  `WINDOWABLE_RELATION_KINDS`, `_partition_expr`,
  `_parent_join_column`) | Files `optimizer/join_taxonomy.py`,
  `optimizer/plans.py`, `optimizer/nested_planner.py`,
  `optimizer/nested_fetch.py` | Holding item Family
  `window-partition-resolution` (name + candidate owner from File
  `optimizer/plans.py` F-M; owner-side evidence this artifact) |
  open
- Family `lateral-join-shape` | Owner
  `optimizer/join_taxonomy.py::LateralJoinShape` (with
  `_through_model`, `_through_link_fields`, the lateral classify
  arms) | Files `optimizer/join_taxonomy.py`,
  `optimizer/lateral_fetch.py`,
  `optimizer/single_parent_fetch.py`, `optimizer/nested_fetch.py`
  | Holding item Family `lateral-join-shape` | open
- Family `prefetch-attach-column-projection` | Owner
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
  (with `_generic_child_attname`, `content_type_column`) | Files
  `optimizer/join_taxonomy.py`, `optimizer/walker.py`,
  `optimizer/nested_planner.py` | Holding item Family
  `prefetch-attach-column-projection` (boundary re-derived fresh
  here, converged with walker F-W9 prior evidence; name adopted)
  | open
- Module mechanics (imports, frozen-record form, enum form,
  lenient-alias declarations, guarded picker) |
  `optimizer/join_taxonomy.py` | `optimizer/join_taxonomy.py` |
  File `optimizer/join_taxonomy.py` | file-local
- `WINDOWABLE_RELATION_KINDS` vs `MANY_SIDE_RELATION_KINDS` |
  `optimizer/join_taxonomy.py::WINDOWABLE_RELATION_KINDS`
  (standing R-A trigger-checked here) |
  `optimizer/join_taxonomy.py`, `utils/relations.py` | File
  `optimizer/join_taxonomy.py` | rejected
- Taxonomy reads routed through `FieldMeta` |
  `optimizer/join_taxonomy.py` (standing field_meta-R1 + R-B
  trigger-checked here) | `optimizer/join_taxonomy.py`,
  `optimizer/field_meta.py` | File `optimizer/join_taxonomy.py`
  | rejected
- Strict/lenient read bodies |
  `utils/relations.py::relation_attr` (standing R-C
  trigger-checked here; already one body) |
  `utils/relations.py`, `optimizer/join_taxonomy.py` | File
  `optimizer/join_taxonomy.py` | rejected
- `_first_truthy` vs inline `or` |
  `optimizer/join_taxonomy.py::_first_truthy` (rejection recorded
  here) | `optimizer/join_taxonomy.py` | File
  `optimizer/join_taxonomy.py` | rejected
- `_record_relation_access` attname vs connector shim |
  `optimizer/walker.py::_record_relation_access` (rejection
  recorded here, re-verified fresh) | `optimizer/walker.py`,
  `optimizer/nested_planner.py`, `optimizer/join_taxonomy.py` |
  File `optimizer/join_taxonomy.py` | rejected
- `LateralJoinShape` vs `NestedConnectionStrategy` |
  `optimizer/join_taxonomy.py::LateralJoinShape` (rejection
  recorded here) | `optimizer/join_taxonomy.py`,
  `optimizer/nested_fetch.py` | File `optimizer/join_taxonomy.py`
  | rejected
- Partition query-name vs lookup accessor |
  `optimizer/join_taxonomy.py::_partition_expr` (rejection recorded
  here) | `optimizer/join_taxonomy.py`, `utils/relations.py` |
  File `optimizer/join_taxonomy.py` | rejected
- The six `pk.attname` readers |
  `optimizer/join_taxonomy.py::_parent_join_column` (rejection
  recorded here) | `optimizer/join_taxonomy.py`,
  `optimizer/lateral_fetch.py`, `optimizer/nested_planner.py`,
  `optimizer/plans.py`, `optimizer/walker.py`, `types/relay.py` |
  File `optimizer/join_taxonomy.py` | rejected
- Filters to-field read vs partition derivation |
  `filters/sets.py::_forward_relation_extra` (rejection recorded
  here) | `filters/sets.py`, `optimizer/join_taxonomy.py` | File
  `optimizer/join_taxonomy.py` | rejected
- `m2m_field_name` resolution vs scanning through-model FKs |
  `optimizer/join_taxonomy.py::_through_link_fields` (rejection
  recorded here, at owner) | `optimizer/join_taxonomy.py` | File
  `optimizer/join_taxonomy.py` | rejected
- No `GENERIC` lateral arm |
  `optimizer/join_taxonomy.py::classify_relation_join` (rejection
  recorded here, at owner) | `optimizer/join_taxonomy.py`,
  `optimizer/lateral_fetch.py`,
  `optimizer/single_parent_fetch.py` | File
  `optimizer/join_taxonomy.py` | rejected
- Shared `except` guard |
  `optimizer/join_taxonomy.py::classify_relation_join` (standing
  J1 trigger-checked here) | `optimizer/join_taxonomy.py`,
  `django_strawberry_framework/_request_body.py` | File
  `optimizer/join_taxonomy.py` | rejected
- Lenient aliases vs a shared lenient-readers module |
  `optimizer/join_taxonomy.py::_safe_getattr` (rejection recorded
  here) | `optimizer/join_taxonomy.py`, `utils/relations.py` |
  File `optimizer/join_taxonomy.py` | rejected
- Morph detect / carry / resolve tri-split |
  `optimizer/join_taxonomy.py::_generic_child_attname` (standing
  tri-split trigger-checked here) | `optimizer/join_taxonomy.py`,
  `optimizer/field_meta.py`, `utils/relations.py` | File
  `optimizer/join_taxonomy.py` | rejected
- M2M pk-ATTNAME vs `_target_pk_name` pk-NAME |
  `optimizer/join_taxonomy.py::_parent_join_column` (rejection
  recorded here) | `optimizer/join_taxonomy.py`,
  `optimizer/field_meta.py` | File `optimizer/join_taxonomy.py`
  | rejected
- Attach order vs advisory order |
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
  (rejection recorded here, at owner) |
  `optimizer/join_taxonomy.py`, `optimizer/nested_planner.py` |
  File `optimizer/join_taxonomy.py` | rejected

## Independent verification (Worker 2)

Trace recorded BEFORE opening the artifact's `## Findings` (only the
`##`/`###` heading list, `Status:`/`Run:` lines, and file tail were seen
for the append anchor).

### W2 trace subject and fingerprints

- `git rev-parse --short HEAD` = `5ee86193` at W2 start; HEAD unmoved.
- Target HEAD bytes:
  `git rev-parse HEAD:django_strawberry_framework/optimizer/join_taxonomy.py`
  = `9b355a50` (347 lines) — governs the verdict.
- Worktree `git hash-object` =
  `e1cbb3e3` (+35/-4 vs HEAD: `_child_link_is_virtual` + virtual-link
  degrade arms) — concurrent hunt dirt, never touched, never traced as
  subject; every consumer citation below is re-checked against HEAD bytes
  (`git grep`/`git show 5ee86193:`), and the one worktree-only consumer
  line found (`nested_planner.py` `getattr(join, "through_model", ...)`)
  is excluded from the trace as hunt dirt.
- `tests/optimizer/test_join_taxonomy.py` never touched (read-only as
  oracle evidence).

### W2 enumeration (own instrument: `ast.Module.body` of the HEAD bytes)

13 named definitions, imports and module docstring excluded:

1. `LateralJoinShape` (class, 3 members)
2. `WINDOWABLE_RELATION_KINDS` (const)
3. `_safe_getattr` (func)
4. `_safe_truthy` (alias assign to `safe_truthy`)
5. `_safe_flag` (func)
6. `_first_truthy` (func)
7. `RelationJoinDescriptor` (class; nested `prefetch_attach_columns`
   property counted with its class)
8. `_partition_expr`
9. `_parent_join_column`
10. `_through_model`
11. `_through_link_fields`
12. `_generic_child_attname`
13. `classify_relation_join`

### W2 sites and roles

Definitions (all in
`django_strawberry_framework/optimizer/join_taxonomy.py` at HEAD):

- D-a `LateralJoinShape` — the lateral join-shape vocabulary.
- D-b `WINDOWABLE_RELATION_KINDS` — windowable membership set.
- D-c `classify_relation_join` with private helpers `_partition_expr`,
  `_parent_join_column`, `_through_model`, `_through_link_fields`,
  `_generic_child_attname` — one join classifier; the helpers are its
  decomposition, not separate rules.
- D-d `RelationJoinDescriptor` + `prefetch_attach_columns` — the carried
  record plus the attach-complete column projection.
- D-e `_first_truthy` — first-true selector with
  raising-truth-counts-false semantics; 3 call sites, all inside the
  target, no package twin (`git grep` for `first_truthy|coalesce`
  finds only this module).
- `_safe_getattr` / `_safe_flag` / `_safe_truthy` — lenient-mode
  compositions over `utils/relations.py::relation_attr` /
  `::relation_bool` / `::safe_truthy` (bodies owned upstream; the local
  names declare the `lenient=True` policy once). Consumer-by-name, not
  definitions.

Consumers (compose by name; verified at HEAD):

- `optimizer/plans.py::window_partition_for_prefetch` — shim: kind
  membership against the SHARED `WINDOWABLE_RELATION_KINDS` plus
  `partition_expr` projection under the historical raise contract.
- `optimizer/nested_planner.py::_connector_only_field` — shim:
  `parent_join_column` projection.
- `optimizer/nested_planner.py::plan_connection_relation` — `windowable`
  gate + descriptor build from the raw field.
- `optimizer/nested_planner.py::_advise_composite_index` — reads
  `parent_join_column` + `content_type_column`.
- `optimizer/nested_planner.py::_project_scalar_only_window` — reads
  `prefetch_attach_columns`.
- `optimizer/walker.py::_ensure_connector_only_fields` — reads
  `prefetch_attach_columns`.
- `optimizer/nested_fetch.py::NestedConnectionRequest.join` + windowed
  body `partition_by=request.join.partition_expr`.
- `optimizer/lateral_fetch.py::_build_lateral_spec` (+ visibility gate)
  — reads `lateral_shape`, `parent_link_field`, `through_child_field`;
  derives `through_table` from `parent_link_field.model`, never from
  `through_model`.
- `optimizer/single_parent_fetch.py::single_parent_spec` — reads
  `lateral_shape` + `parent_link_field`.
- Upstream definitions consumed: `utils/relations.py::relation_kind`
  (strict, fail-closed to `"forward_single"`),
  `::relation_attr`/`::relation_bool` (lenient mode), `::safe_truthy`,
  `::RelationKind`.

Oracles (pin literals, never read the owner):

- `tests/optimizer/test_join_taxonomy.py` (exact descriptor pins),
  `tests/optimizer/test_plans.py` (shim pins),
  `tests/optimizer/test_walker.py` (connector-writer pins),
  `tests/optimizer/test_nested_index_advisory.py`
  (`content_type_column` + `through_model` pins),
  `tests/optimizer/test_lateral_fetch.py`, `tests/test_keyset.py`,
  `tests/test_lateral_pg_parity.py` (compose `classify_relation_join`
  for lateral specs), `tests/optimizer/_builders.py` (test composer).

Projections (describe, never own):

- Module docstring taxonomy table + member docstrings;
  `optimizer/plans.py` partition docstring; lateral/single-parent
  docstrings citing taxonomy ownership; `exceptions.py` shim cross-ref.

Not a second definition (checked by `git grep` at HEAD):

- `utils/relations.py::MANY_SIDE_RELATION_KINDS` — different contract
  (GraphQL-list representation) from `WINDOWABLE_RELATION_KINDS`
  (partitionable prefetch; adds `reverse_one_to_one`). Similar set,
  different rule.
- `walker.py` / `field_meta.py` `relation_kind` branches — prefetch-vs-
  select plan shape and snapshot stamping, never join facts.
- `optimizer/field_meta.py` slots (`reverse_connector_attname`,
  `target_field_attname`, morph names) — snapshot INPUTS the
  classifier's fallbacks read; no join derivation there.
- `related_model._meta.pk.attname` readers elsewhere (lateral child
  join column, order tiebreak, id attr) — different rules over shared
  Django metadata.
- `LateralWindowSpec.parent_link_field` — lateral's own record slot
  populated FROM the descriptor, not a re-derivation.
- `.through` attribute reads, `m2m_field_name` resolution,
  `remote_field.attname/name` partition reads, generic
  name-to-attname resolution — each single-sited in the target.

### W2 change challenges (definition counts)

- C1 — lateral eligibility change (new arm or scope widening):
  taxonomy 1 (`LateralJoinShape` + classifier arm); the
  lateral/single-parent/visibility branches are enforcement sites
  applying the vocabulary to their own eligibility contracts. Count 1.
- C2 — windowable membership change: `WINDOWABLE_RELATION_KINDS` 1;
  the plans shim composes the shared set; `MANY_SIDE` does not move.
  Count 1.
- C3 — connector derivation change (new fallback slot):
  `_parent_join_column` 1; shim + attach projection + advisory compose.
  Count 1.
- C4 — lenient read-policy change: `utils/relations.py` bodies 1; the
  `_safe_*` names delegate. Count 1.
- C5 — through-link resolution change: `_through_link_fields` 1;
  lateral reads resolved objects. Count 1.
- C6 — generic arm change (partition/attach/morph rule):
  `_generic_child_attname` + classifier generic arm, one rule at one
  site. Count 1.

### W2 owner choice

Keep every join rule in `optimizer/join_taxonomy.py`: it is the
narrowest cohesive owner every legitimate consumer (lateral,
single-parent, nested fetch/planner, plans, walker) already imports
with no dependency reversal. Shims stay at their historical owners;
lenient read bodies stay in `utils/relations.py`.

### W2 matrix (own discharge)

1. Cross-flavor mirroring — inapplicable with reason: the target is
   optimizer-internal fetch-planning vocabulary; no public surface
   (types, filters, orders, mutations, forms, `rest_framework`)
   encodes join conditions (filters' correlated-`EXISTS` adapter is a
   different mechanism, not a mirror).
2. Sync/async twins — inapplicable by construction: pure sync
   classifier, no awaits, no twin.
3. Derived-not-repeated — discharged by search: every join derivation
   single-sited (see "Not a second definition"); consumers compose by
   name.
4. Round-trip pairs — inapplicable: one-way classification, no
   encode/decode half.
5. Other media — oracles pin literals; projections describe; no oracle
   reads the owner.
6. Enforcement by omission — all 3 shape members armed at every
   consumer (`_build_lateral_spec` handles both plannable shapes +
   `else -> None`; DIRECT_FK-only gates carry stated v1 scope); all 5
   kinds classified (`forward_single -> UNSUPPORTED` stated: nothing
   to window). No gap.

### W2 candidate defect (pre-findings)

- W2-D1: at HEAD `RelationJoinDescriptor.through_model` is populated
  but has NO production reader (`git grep through_model 5ee86193`
  outside the target finds only an unrelated test name; lateral
  derives the through table from `parent_link_field.model`; the one
  worktree `through_model` read in `nested_planner.py` is hunt dirt),
  while the module docstring still presents `through_model` as half
  of the lateral join-SQL selector. Docstring-vs-body mismatch and/or
  write-only slot (principle 11 question). Routes to the
  `optimizer/join_taxonomy.py` owner. Reconciled against W1's D1
  below after reading `## Findings`.

### W2 reconciliation (after reading `## Findings`)

(a) W2-D1 (`through_model`) vs W1 near-miss (a) + F2 question —
CONVERGED, not filed. W1 records the same zero-reader census and
routes the slot to F2 as a principle-11 keep-or-delete question at
the family item's own HEAD. W2 accepts the triage over a defect
filing: oracle pins would catch a removal (no silent breakage, unlike
D1), the docstring over-claim has nil blast radius (reading the
carried slot additionally harms nothing), and the concurrent hunt
adds a first production reader (observed worktree dirt), so a defect
filed now would be mooted or duplicated by the family decision
either way. No `## Defects` entry from W2.

(b) Enumeration base — CONVERGED. W1 counts 19 `ast.Module.body`
nodes (docstring + 5 imports + 13 named); W2 counts 13 named.
Identical coverage: W2 re-checked member-by-member and every named
member lands in F1/F2/F3, L1, or a rejection (the descriptor and
the classifier split across families with explicit cross-refs; no
member unassigned, none sampled).

(c) One-rule (W2) vs three-family (W1) split — ACCEPTED. W1's
F1/F2/F3 follows the three consumer clusters (window/partition,
lateral, attach) with distinct variation axes and records the
sharing joints explicitly (F1 composes F3's helper; F2/F3 carry
their own questions). A file item names families; the family items
reconcile scope. W2's challenges C1–C6 map onto W1's challenge rows
1:1 with the same count-1 verdicts.

(d) D1 scope — W2 independently verified the FieldMeta-leg chain at
HEAD (`walker.py::_resolve_field_map` "Map values are `FieldMeta`
on both paths" -> `_resolve_selection_target` ->
`_ensure_connector_only_fields`; planner `field_map.get` ->
`_project_scalar_only_window`), the fallback/parity-slot
resolution that makes both legs work, the zero-production-caller
census for both shims, and the no-`FieldMeta`-fed-oracle census.
D1's contract row (module's own input contract), feasible shape
(universal list relations), wire input (any prefetch-planning
query), blast radius (silent log-and-skip degradation, oracle-blind),
and HEAD-clean owner lines all hold. Homing: normal, on a NAMED
card at closeout. W1's non-reopening of R2 is correct
(subset-tolerance is not routing).

(e) Near-miss (b) (HEAD M2M advisory wording) — ACCEPTED as
recorded-not-filed: advisory-only output on lines the concurrent
hunt is deciding, on-record with freshness, re-verified by the
family items at their own HEAD. Same for near-misses (c)–(e).

### W2 judgments

- Enumeration: PASS member-by-member (see (b)).
- Matrix, per axis: (1) SEARCHED with a package-wide vocabulary
  census — the six-consumer population matches W2's own trace;
  (2) no-surface, zero-`async` grep reason — sound;
  (3) SEARCHED, every derivation composes its owner — matches W2's
  single-site censuses; (4) no-surface, producer-direction verified
  at every call site — sound; (5) SEARCHED, oracles pin literals
  (W2 spot-verified pins and the 14-test census) and projections
  classified — sound; (6) SEARCHED, five shapes × every fact with
  exactly one handling consumer each — matches W2's member
  enumeration. No axis excused by a found consolidation.
- Adoption basis: F1 ADOPTED from File `optimizer/plans.py` F-M —
  VERIFIED (`dry-file-optimizer__plans.md`, Status `verified`,
  names `window-partition-resolution` with candidate owner
  `optimizer/join_taxonomy.py::classify_relation_join`; owner-side
  evidence here extends its census). F3 ADOPTED from walker F-W9 —
  VERIFIED as prior-evidence-only convergence (walker is REOPENED;
  W1 re-derived the two-writer boundary fresh at HEAD and the name
  match avoids forking; W2's own writer census agrees). F2 NEW
  `lateral-join-shape` — VERIFIED necessary (lateral F-G
  `join-vocabulary` WITHDRAWN verbatim with "No index row owed";
  single-parent HF-E points at this owner). None of the three names
  exists in the plan index: all three are new Family items for
  Worker 0 to add.
- Standing-trigger re-checks, each on its reason: R1 (family R-A,
  sets still differ exactly on `reverse_one_to_one` — re-verified),
  R2 (field_meta R1 + family R-B, `FieldMeta` still carries
  neither slot — re-verified via the slot census), R3 (family
  R-C, still one body + sole lenient consumer — re-verified via
  the 2-site `lenient=True` census), R12 (`_request_body` J1,
  no shared-guard mechanism adopted — reason sound), R14
  (detect/carry/resolve tri-split, still exactly three readers —
  re-verified), R5 (walker prior R5 re-derived fresh — W2 read
  `_record_relation_access` at HEAD and agrees: source-local
  `attname` vs child-side attach column). Matrix R-D/R-E/R-F
  trigger checks (zero taxonomy vocabulary outside the optimizer)
  match W2's own flavor sweep.
- Freshness: every finding carries HEAD + dirt fingerprints; W2
  re-resolved all 15 package/test blobs, both live-suite blobs,
  all 4 dirt blobs, and spec/rationale/KANBAN ids — ALL MATCH.
- Pending execution: none listed; W2 accepts the static-only basis
  (every claim decided by AST/body/census reads) and the
  inapplicable-by-construction cells (pure derivation, no DB/alias/
  dialect reach). No `proof:`/`gate:` entries owed.
- Prose/rules: no process-provenance language (dirt attribution +
  `Worker 0` routings match the verified sibling bar);
  `path::Symbol` citations throughout; no markdown links hence no
  scaffold owed (`check_trailing_commas.py --check`:
  "excluded from the source-layout rules"); test tier N/A (zero
  test edits). `uv run ruff format --check` passes;
  `uv run ruff check` reports "No Python files" (`.md` excluded).
- Item-scoped diff: W1 touched NOTHING tracked — the diff is the
  new untracked artifact alone. Window-diff re-attribution
  VERIFIED: all six files (`extensions/resource_policy.py`,
  `filters/base.py`, `filters/sets.py`,
  `examples/.../test_resource_policy_api.py`,
  `tests/filters/test_base.py`, `tests/test_resource_policy.py`)
  carry concurrent-hunt content only (directive-charging arms,
  `__class__`/safe-name guards + matching tests); none touches
  the target or its tests. NOTE a brief correction: the dispatch
  record names "three test files" plus two production files but
  the window holds THREE production files — `filters/sets.py`
  included; attribution unaffected.
- Probes: none run by W1 or W2 (static verification; censuses via
  read-only `git grep`/`git show`; no `temp-tests/` scope, no
  workspace copy, no pytest).

### W2 verdict

`verified`. Zero-edit file item: coverage complete (19/19 nodes,
13/13 named members homed), assignment sound (3 families, 1
file-local, 16 rejections each with contract difference +
trigger), D1 correctly filed as a HEAD defect for normal homing.
No W2 defects. No pending execution. HEAD `5ee86193` unmoved;
nothing tracked touched.
