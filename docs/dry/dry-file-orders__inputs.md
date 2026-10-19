# DRY review: `django_strawberry_framework/orders/inputs.py`

Status: verified
Run: 0.0.15 2026-09-22-5

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an open or
verified family holding item, or is a rejection carrying its contract
difference + trigger. Zero production edits; zero tracked files changed.

## System trace

Target owns the order input namespace
(`django_strawberry_framework/orders/inputs.py`, 395 lines, HEAD blob
`6f6ec946`): the public direction enum (`Ordering` + `is_ascending` +
`resolve`), the five substrate aliases (`FieldSpec` / `build_input_class` /
`_camel_case` / `_iter_orderset_subclasses` / `_input_type_name_for`), the
lazy-path constant (`INPUTS_MODULE_PATH`), the Decision-9 namespace quartet
binding (`_materialized_names` / `_field_specs` /
`materialize_input_class` / `clear_order_input_namespace` + the
`register_subsystem_clear` row), the leaf converter
(`convert_order_field_to_input_annotation`), the triples hook body
(`_build_input_fields` + `_leaf_of` closures over the shared emit
scaffold), the whole-value normalizer (`normalize_input_value`) with its
lazy-provenance gate (`_ensure_field_specs`), and the `Meta.fields =
"__all__"` helper (`_get_concrete_field_names_for_order`). No BFS walk, no
collision check, no cache-key hashing, no `type(...)` skeleton, no Layer-6
getter, no queryset, no transport, no sync/async machinery lives here — all
of that is owned by [utils-inputs][utils-inputs], [sets-mixins][sets-mixins],
and [input-values][input-values].

Traced end to end, filter twin FIRST (whole
[filters-inputs][filters-inputs], 1073 lines, HEAD blob `82b52d97`):
identical substrate-alias shape, identical heavy-quartet binding with
disjoint family params, identical `before_bind=True` registration with
disjoint owners, identical emit-scaffold call — and five documented
divergences (rejections R-conv/R-norm/R-build plus the R-e direction and
the HIDE skip, each re-derived fresh below). Owner bodies in
[utils-inputs][utils-inputs] (`make_set_input_namespace`,
`emit_set_input_field_triples`, `GeneratedInputFieldSpec`,
`build_strawberry_input_class`, `set_input_type_name`,
`materialize_generated_input_class`, `clear_generated_input_namespace`,
`GeneratedInputArgumentsFactory` docstring), the traversal mechanics in
[input-values][input-values] (`RELATED`, `iter_active_fields`), the naming
+ traversal-config owners in [sets-mixins][sets-mixins]
(`ClassBasedTypeNameMixin.type_name_for`, `ActiveInputPermissionAttrs`,
`ActiveInputPermissionMixin._input_traversal`,
`._active_permission_field_paths`), the pipeline consumers in
[orders-sets][orders-sets] (`_normalize_input`, `_prepare_permission_input`,
`_permission` traversal config, `_validate_normalized_terms`,
`_resolve_order_expressions`, `get_flat_orders`, `_expand_meta_fields`,
`_apply_orderings`), the hook consumer in
[orders-factories][orders-factories] (`OrderArgumentsFactory._build_input_triples`
+ import block), the declaration seam in [orders-base][orders-base]
(`RelatedOrder` constructor + `.orderset` reads), the leaf consumers in
[orders-init][orders-init] (import block + helper call), the opposite-selection
separation in [mutations-inputs][mutations-inputs]
(`editable_input_fields` docstring + body), the phase-2.5 consumer in
[finalizer][finalizer] (materialize import + ledger passage, by reference),
oracles in [test-order-inputs][test-order-inputs] (48 tests at HEAD) plus
the live `orderBy:` population (10 `test_query` modules carry the token),
contract sources [spec-028][spec-028] (Decisions 2/3/5/8/9/12/13, Edge
cases, Test plan — read), and the verified holding/trigger artifacts
[dry-filters-inputs][dry-filters-inputs] (F-1..F-6/R-a..R-g as orientation
triggers, re-derived fresh below), [dry-orders-base][dry-orders-base] (F4
fallback + seam convention), [dry-orders-factories][dry-orders-factories]
(F-1/F-2/R-bag/R-mutid/D1 as triggers, re-derived fresh; the bilateral
inputs-comment note ADJUDICATED below as D1), [dry-orders-init][dry-orders-init]
(shape convention), [dry-clear-lifecycle][dry-clear-lifecycle] (member-6
census), and [dry-mutid][dry-mutid] (R2 trigger, checked fresh).

Dirt note (all hunt-dirtied paths read via `git show HEAD:<path>`, never
touched): the worktree target (`889b5971…`, +2/-2: `_safe_class_name`
import + adoption in `normalize_input_value`'s owner-name read) is
concurrent-external dirt — every judgment below is against HEAD bytes
`6f6ec946…`, which govern. Likewise read at HEAD bytes only:
[filters-inputs][filters-inputs] (`06797dc7…`, `_normalize_range_value`
hunk — outside every judged region), [utils-inputs][utils-inputs]
(`47b2af21…`, label-hardening + guard arms incl. inside the judged emit /
materialize bodies — no definition moved, no count affected),
[input-values][input-values] (`d4ebeeb6…`, depth-hunk outside
`iter_active_fields`), [sets-mixins][sets-mixins] (`a4b301c3…`, mixin-body
hunks below/around but outside the judged `type_name_for` / traversal /
facade regions), [orders-sets][orders-sets] (`f09d9983…`, label swaps incl.
inside the judged guard bodies + one `__eq__`-guard arm — no definition
moved, no count affected), [orders-base][orders-base] (`afd55efd…`,
`_validate_target` hunk outside the judged constructor/property lines),
[finalizer][finalizer] (`f866fcf0…`, `_field_surface_names` hunk outside
the orphan passage), [definition][definition] (`01f78d93…`, body hunks —
judged use is annotation-only), [utils-strings][utils-strings]
(`ffa4fee0…`, `__all__` hunk outside `graphql_camel_name`),
[filters-sets][filters-sets] (`c1a0f1b2…`, body hunks outside the judged
import block + `"__all__"` prose), [mutations-inputs][mutations-inputs]
(`fcbb964d…`, relation-index hunks below the judged selector),
[test-order-inputs][test-order-inputs] (`a0300a00…`, appended
hostile-`__qualname__` tests targeting the DIRTY owner-name line —
outside the judged HEAD oracle blocks), and
`django_strawberry_framework/filters/base.py` (`0236c495…` vs HEAD
`ba52351c…`, newly dirtied since the sibling artifacts; not a judged
region here). Clean witnesses re-hashed both sides:
[orders-factories][orders-factories] (`4f35b66b…`),
[orders-init][orders-init] (`ed546f9c…`),
[filters-factories][filters-factories] (`366e0490…`),
[exceptions][exceptions] (`e06b0b7f…`), [spec-028][spec-028]
(`94a3141c…`).

Excluded with reason: every other indexed family whose files-covered list
was scanned for this path — only `set-arguments-factory-bfs` lists
`orders/inputs.py`, and it is routed below (F-BFS hook-body convergence;
C9/C10 end with 1 definition at the stated owners, never here).
`dynamic-set-class-getter` does NOT list this file, and the task-named
interplay check DIVERGES as membership on fresh evidence (C15: zero
Layer-6 tokens in the target — correctly absent). `subsystem-clear-lifecycle`
(verified, member 6) is routed as a lawful convergence (F-NS). `one-sync-boundary`,
`queryset-seed-and-model-read`, `sync-boundary-recourse-wording`, and
`field-value-coercion` were judged on their mechanisms against this
target's REAL surface and found to have none here (negatives verified:
zero `async`/`await`/`sync_to_async`/`queryset`/`model_for`/`base_queryset`/
`coerce`/`recourse` tokens in the target). No index row named
`lookup-name-spelling-grammar`, `filter-logic-operators`,
`active-input-permission-facade`, or `set-type-naming` exists in the
current plan; the filters-twin artifact's F-1/F-2/F-4/F-6 treatment was
orientation only (prior verdicts are triggers to check), and each
mechanism is re-derived fresh below — the lookup/logic surfaces as
rejection evidence (R-conv/R-norm/R-build), naming as a no-surface
pass-through (C17), the traversal config as an already-single-sited
contributor note (F-NORM), never a new family (no second definition
exists to consolidate).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Twin read FIRST whole
([filters-inputs][filters-inputs], 1073 lines). Shared substrate: five
substrate aliases (same right-hand sides; the set-iterator left-hand
name is family-prefixed on both sides), heavy quartet via
`make_set_input_namespace` with disjoint family params, `before_bind=True`
rows under disjoint owners, emission via `emit_set_input_field_triples`
with family closures — with five genuine semantic divergences, each
re-derived fresh with this file's own difference: fixed `Ordering | None`
leaves vs the kind ladder (R-conv, CONVERGE filters R-a/R-c); whole-value
walk + direction check vs per-instance kind dispatch (R-norm, fresh
same-name pair); bare-triples build vs grouping + operator-bag + HIDE
skip (R-build, CONVERGE factories R-bag); orders-only `_ensure_field_specs`
lazy populate (F-ENS; filters R-e trigger checked — filters builds specs
at bind and its fallbacks hold, so no twin is owed); no lookup/logic
vocabulary on the order side by Decisions 5/8 (rejection evidence inside
R-conv/R-norm). The write flavors ride the LIGHT `make_input_namespace`
— different lifecycle, not a twin (filters R-g trigger checked; the
`editable_input_fields` opposite-selection separation verified fresh
against both bodies, durable at its owner already — no new row).

**2. Sync/async twins.** Inapplicable with reason: zero `async def`, zero
`await`, zero `sync_to_async` in the target (verified by token sweep);
construction runs at finalize time, normalization + `resolve` are pure
sync construction producing unevaluated `OrderBy` objects (verified: no
`base_queryset`, no `run_in_one_sync_boundary`, no `model_for`, no
`queryset` token defined or called in the target). The `apply_sync` /
`apply_async` pair lives at [orders-sets][orders-sets]; `one-sync-boundary`
names that module, never this file.

**3. Derived rather than repeated knowledge.** Searched. Input type names
arrive via the passed-through `_input_type_name_for` delegate →
`ClassBasedTypeNameMixin.type_name_for` (0 definitions here — C17); the
module path is pinned once (19) and read by name at the quartet build,
the emit call, and the leaf helper (0 re-derivations — the string
literal occurs exactly once as a definition package-wide, C6); triple
emission + `FieldSpec` rows via the emit scaffold (owner F-BFS);
materialization + heavy clear via the quartet owner (F-NS); traversal
mechanics via `iter_active_fields` + `_input_traversal` (F-NORM);
renderings via the shared `_safe_*` helpers (composed by name). The
`field_name or top_name` closure reads the base-owned `None` default
(verified [orders-base][orders-base] F4 pair: base declares the default,
this closure is its fallback — complementary, not duplicated). No local
re-derivation of any shared fact.

**4. Inverse / round-trip pairs.** Searched: no local pair. `Ordering.resolve`
is encode-only (direction → `OrderBy`; no `OrderBy` → direction decode
exists package-wide — the census finds `resolve(` consumers only in
[orders-sets][orders-sets]). `convert_*` (field → annotation) vs
`normalize_input_value` (value → tuples) share a name-stem, not a
round-trip (different domains, neither inverts the other).
`materialize_input_class` idempotency + collision raise are one
directional pin owned at `materialize_generated_input_class`, not a
pair. No second half to twin anywhere in the target.

**5. Contracts restated in another medium.** Searched. Four media carry
this file's contracts: production code (definitions here, machinery at
the owners); authoritative contract sources ([spec-028][spec-028]
Decisions 2/3/5/8/9/12/13, Edge cases, Test plan — each cited decision
read and checked against the body; D2 records the one cite that fails);
independent oracles ([test-order-inputs][test-order-inputs]: 48 tests
spelling literals — six enum members, `True`-or-`None` sentinels,
`"shelf__code"` paths, `"received invalid order direction"` wording,
idempotency/collision/parking pins — plus the live `orderBy:` population
over 10 `test_query` modules; none reads an owner body to compute
expectations); projections (module/class/function docstrings, spec code
blocks — Decision 5 quotes the enum verbatim and the tree matches it).
A new direction moves the enum once; every medium follows (C1–C3).

**6. Enforcement by omission.** Enumerated. Orders lacks the lookup
vocabulary, logic operators, kind ladder, and HIDE skip by contract
([spec-028][spec-028] Decisions 5/8/12; triggers recorded R-conv/R-norm/R-build).
`_ensure_field_specs` exists orders-only because filters builds specs at
bind time while orders normalizes direct-called mappings (F-ENS; no
contract source demands a filters-side twin). `build_input_class` has
ZERO production call sites on the order side (tests only — fresh census;
the filter twin's alias carries two intra-module production calls, so
the asymmetry is real and load-bearing for D1). Neither the enum nor the
converter nor the normalizer lacks a guard its contract requires: the
leaf check fires on every non-`Ordering` leaf (pinned), the exact-type
boundary + resolve-time guards live at their own seams (R-guards), and
the Layer-6 surface is absent by Decision 12 (C15). No missing guard
with a contract source behind it — no omission defect filed.

### Enumeration

Instrument: `ast.parse` over the pinned HEAD blob, counting
`ast.Module.body` members — **31 top-level statements** — plus every
member of the `Ordering` class body — **9 members** (docstring + 6
enum members + 2 methods). **26 named rule-bearing members** in total
(+ 1 nested closure counted within its owner). Every member lands
below; every challenge in `### Challenges` ends in a family row, a
file-local row, a rejection, or a verified no-surface routing.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (namespace + enum + trio + adapters + helper + ledger prose) | (none) | prose projection, all findings |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3–7 | `import enum`, typing, strawberry, `F`, `OrderBy` imports | 5 names (machinery) | F-ENUM signatures |
| 8 | `from ..exceptions import (...)` | 3 names (machinery) | F-CONC/F-NORM consumer rows |
| 9 | `from ..registry import register_subsystem_clear` | 1 name (machinery) | F-NS consumer row |
| 10 | `from ..utils.input_values import RELATED, iter_active_fields` | 2 names (machinery) | F-NORM/F-ENS consumer rows |
| 11 | `from ..utils.inputs import (...)` | 6 names (machinery) | F-BFS/F-NS/F-ALIAS feeds |
| 12 | `from ..utils.strings import graphql_camel_name` | 1 name (machinery) | F-ALIAS feed |
| 13 | `if TYPE_CHECKING:` guard | 2 names (type-only) | annotations, F-CONV/F-BFS/F-NORM |
| 14–18 | five substrate aliases | `FieldSpec`, `build_input_class`, `_camel_case`, `_iter_orderset_subclasses`, `_input_type_name_for` | F-ALIAS (+ D1 comment) |
| 19 | `INPUTS_MODULE_PATH` | 1 constant | F-PATH |
| 20 | `class Ordering` + 9 members | enum + 6 members + `is_ascending` + `resolve` | F-ENUM |
| 21–22 | `_materialized_names` / `_field_specs` annotations | 2 names (declared) | F-NS |
| 23 | quartet unpack `= make_set_input_namespace(...)` | 4 names (ledger, specs, materializer, clear fn) | F-NS |
| 24 | `def _get_concrete_field_names_for_order` | 1 name | F-CONC |
| 25 | `def convert_order_field_to_input_annotation` | 1 name | F-CONV + R-conv |
| 26 | `def _build_input_fields` (+ nested `_leaf_of`) | 1 name + closure | F-BFS + R-build |
| 27 | `def normalize_input_value` | 1 name | F-NORM + R-norm + R-guards (+ D2 docstring) |
| 28 | `def _ensure_field_specs` | 1 name | F-ENS |
| 29 | `def materialize_input_class` | 1 name | F-NS |
| 30 | `def clear_order_input_namespace` | 1 name | F-NS |
| 31 | `register_subsystem_clear(...)` call | bus row, owner `orders.input_namespace` | F-NS |

Rules: R-enum direction vocabulary (statement 20); R-aliases substrate
addressability (14–18); R-path lazy-module constant (19); R-conc
column-backed expansion (24); R-conv leaf annotation (25); R-build
triples hook body (26); R-norm whole-value normalization (27); R-ens
lazy provenance gate (28); R-ns namespace lifecycle (21–23, 29–31).
Two convergences onto existing rows (F-BFS → open family
`set-arguments-factory-bfs`, whose files-covered already lists this
file; F-NS → verified family `subsystem-clear-lifecycle`, member 6),
seven file-local rows, four rejected rows — all named for Worker 0
(see `## Index rows for Worker 0`). No NEW family is named: every
shared mechanism below already has its single-sited owner, and every
mirror pair converges onto a verified separation or a fresh rejection
on HEAD evidence.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. All bodies judged at HEAD bytes (the worktree dirt —
target + connected — is label-hardening/guard arms that move no
definition and change no count; details per finding).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-enum members | seventh direction member | **1** (the enum; `resolve`/`is_ascending` + both sets-side consumers follow by construction; member-count + sentinel oracles follow as oracles) | independent |
| C2 | R-enum discrimination | prefix rule → membership table | **1** (`is_ascending`; `resolve` + `_resolve_order_expressions` follow — the two-consumer rationale Decision 5 states) | independent |
| C3 | R-enum resolve | sentinel semantics change (e.g. bare ASC forces NULLS LAST) | **1** (`resolve`; portability prose + sentinel oracles follow) | independent |
| C4 | R-aliases substrate | shared helper rename | **0 here-definitions** (5 declarations follow; twin's 5 follow; owners move once) | independent — proves declarations |
| C5 | R-aliases addressability | drop the orders aliases, import substrate directly | breaks this file's consumers (tests import all 5; `__init__` imports 1; intra-module use at 19-annotation/emit call) — proves per-family addressability, not redundancy | independent |
| C6 | R-path rename | module rename | **1 here** (the constant; quartet build + emit call + helper/driver/finalizer readers follow by name; the literal pin oracle follows) | independent |
| C7 | R-conc selection | selection change (e.g. admit M2M, drop pk) | **1 here** (the mutations `editable_input_fields` opposite-selection stands untouched — verified different predicate, different return type) | independent |
| C8 | R-conv shape | per-type leaf annotations (choices → enum, FK → id) | **1 here** (the filter kind-ladder converter untouched — opposite change responses prove distinct rules) | independent + R-conv |
| C9 | R-build scaffold | emission mechanics change (kwargs rule, collision wording, flatten rule) | **0 here, 1** at [utils-inputs][utils-inputs]`::emit_set_input_field_triples` (both families' hook bodies unchanged) | independent — proves single ownership |
| C10 | R-build closures | related-path rule change (`field_name or top_name` → other) | **1 here** (the closure; filter `top_name` closure untouched) | independent — proves family declarations |
| C11 | R-norm leaf check | leaf-check reword/rescope (e.g. name the GraphQL alias too) | **1 here** (both sets-side guards untouched — different seams, different loci) | independent + R-guards |
| C12 | R-norm traversal | new classification/mechanics (new kind, new skip rule) | **0 here, 1** at [input-values][input-values]`::iter_active_fields` (+ the config derivation at `_input_traversal`) | independent — proves single ownership |
| C13 | R-ens gate | warm-up gate change (sentinel derivation, build trigger) | **1 here** (no filter twin exists — filters builds at bind) | independent |
| C14 | R-ns lifecycle | clear-contract change (new reset slot, replay posture) | **1** (the bus + `make_set_input_namespace`; 0 here — unpack + wrappers + row follow) | independent — proves single ownership |
| C15 | `dynamic-set-class-getter` check | Layer-6 skeleton/key/gate change | **0 here** (zero `make_dynamic_set_getter`/`make_set_meta_cache_key`/`type(` tokens — DIVERGE as membership, correctly absent per Decision 12) | no surface — do not inherit |
| C16 | boundary/seed/coercion checks | change `one-sync-boundary` / seed / recourse / coercion rules | **0 here** (verified negatives: no colored pair, no seed call, no recourse token, no literal coercion — leaves are direction enums) | no surface — do not inherit |
| C17 | naming + mutid checks | change the `Foo` → `FooOrderInputType` derivation; add a narrowing-derived name axis | **0 here** (owned at `ClassBasedTypeNameMixin.type_name_for` via `set_input_type_name`; this file passes the delegate through — C4-shaped; no shape token in the target, [dry-mutid][dry-mutid] R2 trigger checked) | no surface — do not inherit |
| C18 | R-norm merge | unify the two `normalize_input_value` functions | separation stands (R-norm: different signatures, different returns, different recursion — opposite files under opposite changes today) | rejected-merge — proves distinct rules |
| C19 | R-build merge | unify the two `_build_input_fields` bodies | separation stands (R-build: grouping + bag + HIDE vs direct + fixed-leaf — opposite files under opposite changes today) | rejected-merge — proves adapters |

No executable proof was run: the target is an enum + declarations +
thin wrappers + three single-predicate/single-walk functions whose
every behavior is pinned by the 48 read oracles in
[test-order-inputs][test-order-inputs] plus the live `orderBy:`
population, and every census above is a byte-level `git grep` over
HEAD blobs or an `ast.parse` enumeration — all read-only, none
mutating, none capable of distinguishing anything the cited oracles do
not already pin. No `docs/dry/temp-tests/` scratch was created. All
claims below are therefore `static-reviewed`; there is no
`execution-deferred` proof.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site (convergences name
their holding family; rejections carry difference + trigger).

### F-ENUM — direction enum + discrimination + resolve (file-local)

- **Contract + variation.** `Ordering` is the six-member direction
  vocabulary (`ASC` / `DESC` × bare / `NULLS_FIRST` / `NULLS_LAST`);
  `is_ascending` is the single ASC/DESC discriminator (member-name
  prefix rule); `resolve(value)` compiles a direction + ORM path into
  an `F(value).asc/desc(...)` with `True`-or-`None` null sentinels.
  Legitimate variation: membership, the discrimination rule, and the
  sentinel mapping only.
- **Sites + roles.** *Definition*: this file's statement 20 (all three).
  *Consumers*: `resolve` internally consumes `is_ascending`;
  [orders-sets][orders-sets]`::OrderSet._resolve_order_expressions`
  consumes both by name (`direction.is_ascending` for Min/Max,
  `direction.resolve(...)` for the `OrderBy`); `normalize_input_value`
  consumes the enum for the leaf `isinstance` check (F-NORM);
  [orders-init][orders-init] re-exports the enum (consumer row recorded
  in that artifact's F1). *Out-of-population source*: upstream
  `strawberry_django/ordering.py::Ordering` (Decision 5: borrowed
  verbatim — external, never a second definition). *Oracles*: member /
  value / classification / resolve-shape tests — independent (they
  spell literals and introspect `OrderBy.as_sql`, never read the
  property). *Projection*: Decision 5 code block (byte-matches the
  tree) + the portability note (matches Decision 5's note).
- **Challenges.** C1 → 1 here; C2 → 1 here (2 consumers follow — the
  property exists BECAUSE there are two, per Decision 5); C3 → 1 here.
  The ASC-discrimination census finds exactly one definition
  package-wide (`startswith("ASC")` once; every other site reads the
  property).
- **Owner + lifetime.** This enum (existing owner by responsibility: the
  narrowest site every legitimate consumer — normalizer, resolver,
  leaf — can depend on). No stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owner stands.
- **Distinct behavior.** The prefix-vs-substring split is deliberate and
  asymmetric by contract: `is_ascending` anchors on the prefix (so a
  future member embedding `ASC` elsewhere still classifies), while
  `resolve`'s `NULLS_FIRST` / `NULLS_LAST` substring tests match the
  only two sentinel infixes the vocabulary defines. No filter twin
  exists (filters have no direction vocabulary — R-conv evidence).
- **Behavioral proof.** `static-reviewed`. Rejects "a third site
  re-discriminates" (census: one definition) and "bare ASC forces a
  NULLS clause" (sentinel oracles pin `None`/`None`).
- **Structural gate.** The pre-existing member + classification +
  sentinel oracles (no failability run owed by this zero-edit item).
- **Coupling.** None.
- **Freshness.** Target HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (worktree `889b5971…`
  dirt at the import block + `normalize_input_value` — outside this
  finding's statement), [orders-sets][orders-sets] HEAD
  `6044ab1a11c77a42b715f0d0722fe7c9695064bc` (worktree `f09d9983…`
  label-swap dirt — the judged `is_ascending`/`resolve` consumer
  lines are the HEAD bytes), [orders-init][orders-init]
  `ed546f9c70d56d73e0d84a029e9e04f27da3934b` (clean; re-export),
  [spec-028][spec-028] `94a3141c02b92265779d8f3f7a2eefc019f765d8`
  (clean; Decision 5), [test-order-inputs][test-order-inputs] HEAD
  `baf23440b8c1701b70b4c828e29c8eaf87626488` (worktree `a0300a00…`
  appended tests — outside the judged enum oracles).

### F-ALIAS — substrate aliases (file-local)

- **Contract + variation.** The five module-level aliases re-export the
  shared generated-input substrate under spec-028 Decision 9 names so
  order-side callers stay pinned to this module: `FieldSpec`,
  `build_input_class`, `_camel_case`, `_iter_orderset_subclasses`,
  `_input_type_name_for`. Legitimate variation: none — pure
  declarations (a substrate rename moves the owners once; the aliases
  follow).
- **Sites + roles.** *Definitions*: the substrate owners
  ([utils-inputs][utils-inputs] ×4, [utils-strings][utils-strings]
  ×1). *Declarations*: this file's statements 14–18. *Consumers*
  (fresh census at HEAD): tests import all five from this module;
  [orders-init][orders-init] imports `_input_type_name_for`;
  intra-module use at the `_field_specs` annotation + the emit call.
  [orders-factories][orders-factories] imports NONE of the five (only
  `_build_input_fields` — verified; this is D1). *Sibling
  declarations*: the twin's five aliases (same right-hand sides).
- **Challenges.** C4 → 0 here-definitions (owners move once); C5 proves
  the aliases are load-bearing addressability (dropping them breaks
  the censused consumers), not redundancy.
- **Owner + lifetime.** The substrate owners (existing owners); this
  file owns its five declaration bindings. No stored derivation.
- **Migration.** None (zero-edit item): declarations stand.
- **Distinct behavior.** Considered: one shared alias module both
  families import. Difference: per-family addressability IS the rule —
  order consumers import from `orders.inputs` (Decision 2 subpackage
  layout; the twin's consumers import from `filters.inputs`), and the
  set-iterator names are deliberately family-prefixed
  (`_iter_orderset_subclasses` vs `_iter_filterset_subclasses`) so a
  merge would collide. Unifying would couple the families over
  nothing. Trigger to reconsider: the families merging into one set
  family. Durable home: the alias comment (once D1 corrects its
  consumer clause) + this artifact. No separate rejected index row:
  the candidate is vacuous (different names, disjoint consumers) and
  the durable home is the corrected comment itself.
- **Behavioral proof.** `static-reviewed`. Rejects "the aliases
  duplicate the substrate" (each is one binding; C4 proves a
  substrate change touches one definition) and "the order alias is
  called on the BFS path" (fresh census: ZERO production call sites
  of the order `build_input_class` — tests only — vs the twin's two
  intra-module production calls).
- **Structural gate.** The pre-existing `is`-identity + per-alias
  oracles (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6f6ec946…` (dirt as F-ENUM — outside
  this finding's lines), [utils-inputs][utils-inputs] HEAD
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` (worktree `47b2af21…`
  hardening — no definition moved), [utils-strings][utils-strings]
  HEAD `3ec3b262ea8666d4ba36cf83807ca377fee5a680` (worktree
  `ffa4fee0…` `__all__` hunk — outside `graphql_camel_name`),
  [filters-inputs][filters-inputs] HEAD
  `82b52d97b8f8b26d2846df24dabcabb793507c87` (worktree `06797dc7…`
  range hunk — outside the twin alias block),
  [orders-factories][orders-factories] `4f35b66b…` (clean; none-of-five
  witness), [orders-init][orders-init] `ed546f9c…` (clean; one-of-five
  witness), [test-order-inputs][test-order-inputs] `baf23440…` (dirt
  as F-ENUM — outside the judged alias imports).

### F-PATH — lazy-module-path constant (file-local)

- **Contract + variation.** `INPUTS_MODULE_PATH` pins the
  `"django_strawberry_framework.orders.inputs"` string once so the
  factory (through the hook body), every per-resolver
  `Annotated[..., strawberry.lazy(...)]` reference (through the
  helper driver), and `materialize_input_class` (through the quartet
  closure) stay in sync. Legitimate variation: the string value only.
- **Sites + roles.** *Definition*: this file's statement 19 (the
  literal occurs exactly once as a definition package-wide — every
  other hit is an import path, prose, or the oracle pin).
  *Readers*: the quartet build (23), the emit call (26),
  [orders-init][orders-init]'s helper call, the finalizer passage.
  *Mirror*: the twin constant (same shape, family value — two
  constants, not one rule, since the VALUES must differ).
- **Challenges.** C6 → 1 here (all readers + the literal oracle follow
  by name).
- **Owner + lifetime.** This constant (existing owner: the module whose
  path it names — no narrower site exists). No lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The factory reaches the constant THROUGH the
  hook body (`_build_input_fields` → emit scaffold), not by direct
  import — the comment's "so the factory ... stay in sync" holds via
  that path (verified call chain), so no defect attaches to it.
- **Behavioral proof.** `static-reviewed`. Rejects "a second literal
  defines the path" (census: one definition) and "the twin constant
  could serve" (different module `__dict__` — resolving through the
  wrong path misses every materialized global).
- **Structural gate.** The pre-existing literal-pin oracle (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6f6ec946…` (dirt as F-ENUM — outside),
  twin HEAD `82b52d97…` (dirt as F-ALIAS — outside the twin
  constant), [orders-init][orders-init] `ed546f9c…` (clean; reader),
  [orders-factories][orders-factories] `4f35b66b…` (clean; call-chain
  witness), [finalizer][finalizer] HEAD
  `77fd9a2dd229eb9de5f29188c5058035d3606323` (worktree `f866fcf0…`
  hunk outside the passage; cited by reference).

### F-CONC — column-backed field-name expansion (file-local)

- **Contract + variation.** `_get_concrete_field_names_for_order`
  returns every column-backed field name for `Meta.fields =
  "__all__"`: forward FK/O2O columns included, reverse relations +
  M2M managers + virtual `GenericRelation`/`GenericForeignKey`
  (`column = None`) excluded; rejects a non-model with a typed
  `ConfigurationError`. Legitimate variation: the selection
  predicate only.
- **Sites + roles.** *Definition*: this file's statement 24.
  *Consumer*: [orders-sets][orders-sets]`::_expand_meta_fields`
  (sole production caller — verified census). *Contract source*:
  [spec-028][spec-028] Decision 3 + the `"__all__"` Edge case (both
  read; the Edge case's include/exclude list matches the body
  exactly). *Standing separation*:
  [mutations-inputs][mutations-inputs]`::editable_input_fields`
  (opposite selection: excludes `editable=False`, includes forward
  M2M; different return type — `Field` objects, not names —
  verified fresh against both bodies; durable home already at its
  owner docstring, so no new row). *Oracle*: the direct-helper test
  + the `"__all__"` expansion tests — independent (they spell model
  fields and assert name lists). No filter twin exists (filter
  `"__all__"` rides django-filter machinery — verified: no
  package-defined concrete-names helper on the filter side).
- **Challenges.** C7 → 1 here (mutations selector untouched).
- **Owner + lifetime.** This helper (existing owner by
  responsibility: the expansion rule lives beside the input
  namespace it feeds; the sets-side call site is its only
  consumer). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** The `column is not None` (not mere
  `hasattr`) check is the load-bearing hardening over the cookbook
  idiom (the cookbook would admit virtuals); the `many_to_many`
  conjunct drops M2M managers. Both verified against the body.
- **Behavioral proof.** `static-reviewed`. Rejects "the cookbook
  idiom suffices" (virtuals expose `column = None` — pinned by the
  exclusion list) and "the write selector could serve" (opposite
  selection + different return type — C7).
- **Structural gate.** The pre-existing direct + expansion oracles
  (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6f6ec946…` (dirt as F-ENUM — outside),
  [orders-sets][orders-sets] HEAD `6044ab1a…` (worktree `f09d9983…`
  `__eq__`-guard + label dirt around the call site — the judged
  call line is the HEAD bytes), [mutations-inputs][mutations-inputs]
  HEAD `fc4420475f404297822d7d94bee7bdd275700803` (worktree
  `fcbb964d…` relation-index hunks below the judged selector),
  [filters-sets][filters-sets] HEAD
  `722e0c773dcb1fb806d1fde4837bff4d6c988fba` (worktree `c1a0f1b2…`
  body hunks — the judged `"__all__"` prose + import block are the
  HEAD bytes), [spec-028][spec-028] `94a3141c…` (clean; Decision 3
  + Edge case), [test-order-inputs][test-order-inputs] `baf23440…`
  (dirt as F-ENUM — outside the judged oracles).

### F-CONV — leaf annotation converter (file-local)

- **Contract + variation.** `convert_order_field_to_input_annotation`
  always returns `Ordering | None` regardless of model-field type —
  the only legal leaf value is a direction, never the field's value.
  The `(model_field, owner_definition)` parameters are kept unused
  for shape-symmetry with the filter converter (NOT for a DISTINCT
  ON extension — Decision 12 ships none). Legitimate variation: the
  leaf annotation only.
- **Sites + roles.** *Definition*: this file's statement 25.
  *Consumer*: the `_leaf_of` closure (statement 26; passes
  `(None, None)` — the discovery affordance the converter ignores).
  *Sibling definition*:
  [filters-inputs][filters-inputs]`::convert_filter_to_input_annotation`
  (the kind-ladder converter — a different rule, see R-conv).
  *Oracles*: the table-driven converter test (scalar / choice / FK /
  PK / `BigIntegerField` all → `Ordering | None`) — independent
  (spells the expectation, never reads the body).
- **Challenges.** C8 → 1 here (filter converter untouched).
- **Owner + lifetime.** This function (existing owner: the order
  leaf-annotation rule). No stored derivation.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed`. Rejects "the converter
  differentiates column types" (table oracle pins one shape) and
  "the unused params are vestigial" (shape-symmetry is the stated
  contract; removing them breaks the documented call-shape parity).
- **Structural gate.** The pre-existing table oracle (no failability
  run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6f6ec946…` (dirt as F-ENUM — outside),
  twin converter HEAD `82b52d97…` (dirt as F-ALIAS — outside the
  judged converter), [spec-028][spec-028] `94a3141c…` (clean;
  Decisions 5/12), [test-order-inputs][test-order-inputs]
  `baf23440…` (dirt as F-ENUM — outside the judged oracle).
- **Rejection (nested R-conv).** Considered: unify with the filter
  converter into one shared leaf-annotation rule (same name-stem,
  same "field → annotation" shape — the verified filters artifact
  rejected the same candidate as R-a/R-c; compared fresh here, not
  inherited). Contract difference here: fixed `Ordering | None`
  for every leaf vs an 8-kind MRO dispatch (Relay / CSV / range /
  list / typed / choice / catch-all) with per-kind annotations,
  per-kind helpers, and a `filterset_cls` name-qualifying fourth
  parameter — different signatures, different helpers, opposite
  reasons to change (C8: a per-type change moves this file only; a
  kind-table change moves the twin only). Same stem, not the same
  rule. CONVERGE with verified filters R-a/R-c on fresh evidence.
  Trigger to reconsider: ordering leaves diverging by column type
  (a kind axis on the order side). Durable home: this function's
  docstring (already states the fixed-leaf rule + the symmetry
  clause) + this artifact. Named for Worker 0 as rejected index row
  `orders-converter-vs-filter-kind-ladder`.

### F-BFS — triples hook body (convergence onto open family `set-arguments-factory-bfs`; no new row)

Hook-body contributor to the adopted family (whose files-covered
already lists this file — CONVERGE on fresh evidence per the brief).
Statement 26 walks `orderset_cls.get_fields()` and returns the emit
scaffold's triples with the order-family closures: `related_target_of`
(`entry is not None` → `entry.orderset`), `related_source_path_of`
(`entry.field_name or top_name`), `_leaf_of` (fixed `Ordering | None`
via F-CONV + `top_name` source path), plus the pass-through delegate,
module path, and `_field_specs` sink. The scaffold owns ALL mechanics
(flatten → camel-case → kwargs → related-vs-leaf branch →
placeholder skip → triple + `FieldSpec` + collision staging); the
closures carry ONLY the order semantics — the scaffold's own
docstring names both families' semantics explicitly. Challenges C9 →
0 here / 1 at the owner; C10 → 1 here (filter closures untouched).
The factory hook ([orders-factories][orders-factories]`::_build_input_triples`)
is the one-line consumer (returns these triples as-is); the finalizer
subpass-4 both sides consume the factory output. Behavioral proof
`static-reviewed` (one scaffold call + three closures; no mechanics
spelled here). Freshness: target HEAD `6f6ec946…` (dirt as F-ENUM —
outside), scaffold [utils-inputs][utils-inputs] HEAD `ee31d360…`
(worktree `47b2af21…` label-hardening inside the judged body — no
definition moved, no count affected), twin hook body
[filters-inputs][filters-inputs] HEAD `82b52d97…` (dirt as F-ALIAS —
outside the judged build), [orders-factories][orders-factories]
`4f35b66b…` (clean; consumer), [orders-base][orders-base] HEAD
`4736fda0228ee723aada11bfe374f81036ac4c30` (worktree `afd55efd…`
`_validate_target` hunk — outside the judged `field_name` default +
`.orderset` lines), [spec-028][spec-028] `94a3141c…` (clean;
Decision 3 + flat-shorthand Edge case), HEAD `5ee86193`. No new index
row owed (holding item is the open family).

- **Rejection (nested R-build).** Considered: unify the two
  `_build_input_fields` bodies into one shared build (same name,
  same scaffold call — the verified factories artifact rejected the
  same divergence as R-bag at the hook level; compared fresh here
  at the body level, not inherited). Contract difference here: the
  filter body groups by top-level name, splices nothing itself (its
  FACTORY splices `_build_logic_fields`), builds a per-field
  operator-bag class per leaf, derives source paths by the
  declared-vs-autogen rule, and pre-filters through the HIDE skip;
  this body passes entries direct, returns fixed leaves, and derives
  source paths by `field_name or top_name` — different closures,
  different pre-processing, opposite change responses (C19; a bag
  change moves the twin + its factory splice, this file does not).
  Adapters by design, one per family, fired by the shared scaffold.
  CONVERGE with verified factories R-bag on fresh evidence (same
  divergence, one level down). Trigger to reconsider: orders gaining
  an operator bag. Durable home: the scaffold docstring (already
  states the split) + this artifact. Named for Worker 0 as rejected
  index row `orders-build-fields-vs-filter-bag-build`.

### F-NORM — whole-value normalization + leaf check (file-local)

- **Contract + variation.** `normalize_input_value` flattens a
  Strawberry order input into `[(field_path, Ordering | None), ...]`:
  warms provenance (F-ENS), walks active fields through the family's
  canonical traversal, recurses into `RelatedOrder` branches with the
  django source path as prefix, and appends
  `(django_source_path, Ordering)` per leaf — rejecting a non-`Ordering`
  leaf with a field-naming `ConfigurationError`. The dataclass-vs-dict
  walk, top-level-list flattening, `None` skip, spec lookup, and
  leaf/related classification are owned by
  [input-values][input-values]`::iter_active_fields` driven by the ONE
  canonical config from `OrderSet._permission`
  ([sets-mixins][sets-mixins]`::_input_traversal`); this function keeps
  ONLY the order-side leaf semantics + recursion. Legitimate
  variation: the leaf semantics, the recursion prefixing, and the
  check wording only.
- **Sites + roles.** *Definition*: this file's statement 27 (leaf
  semantics + recursion + check). *Mechanics owners*:
  `iter_active_fields` (walk) + `_input_traversal` (config
  derivation — already single-sited: a read of the contained
  traversal, verified against the mixin body; the permission walkers
  classify through the same object, so no second derivation exists
  to consolidate — contributor note, no family row). *Consumers*:
  [orders-sets][orders-sets]`::_normalize_input` (one-line
  delegate), the apply pipeline downstream. *Sibling definition*:
  [filters-inputs][filters-inputs]`::normalize_input_value` (a
  different rule — R-norm). *Oracles*: the walk / flatten / skip /
  dict-parity / rejection / 3-tier-chain tests — independent (they
  drive values and spell paths/wording, never read the walker).
- **Challenges.** C11 → 1 here (sets guards untouched); C12 → 0 here
  / 1 at the walker (+ config owner).
- **Owner + lifetime.** This function for the leaf semantics (existing
  owner: the order normalization rule); the walker + config owners
  for the mechanics (existing owners). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** The `field.spec is None → continue` arm is a
  defensive post-finalize impossibility (pinned by the no-spec
  oracle); the `child_orderset is None` arm skips placeholder
  branches (pinned). Both verified against the body + oracles.
- **Behavioral proof.** `static-reviewed`. Rejects "the walk re-spells
  traversal" (one `iter_active_fields` call; C12 proves a mechanics
  change touches one definition) and "a bad leaf passes silently"
  (check + rejection oracle pin the loud path).
- **Structural gate.** The pre-existing walk + rejection oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6f6ec946…` — the judged body is the HEAD
  bytes INCLUDING the HEAD owner-name line (`getattr(orderset_cls,
  "__qualname__", ...)`); the worktree `889b5971…` dirt replaces
  exactly that line with the `_safe_class_name` adoption
  (concurrent-external, changes no count: predicate, loci, and
  message skeleton judged are the HEAD bytes),
  [input-values][input-values] HEAD
  `f25666098b86249ec54461e5134127987ec65529` (worktree `d4ebeeb6…`
  depth hunk — outside `iter_active_fields`),
  [sets-mixins][sets-mixins] HEAD
  `ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3` (worktree `a4b301c3…`
  mixin hunks — outside the judged traversal regions),
  [orders-sets][orders-sets] HEAD `6044ab1a…` (worktree `f09d9983…`
  label dirt — the judged delegate + guard lines are the HEAD
  bytes), twin normalizer HEAD `82b52d97…` (dirt as F-ALIAS —
  outside the judged normalizer),
  [test-order-inputs][test-order-inputs] `baf23440…` (worktree
  `a0300a00…` appended hostile-`__qualname__` tests target the
  DIRTY owner-name line — the judged rejection oracle is the HEAD
  block), [spec-028][spec-028] `94a3141c…` (clean; Decisions 5/8 +
  Edge cases).
- **Rejection (nested R-norm).** Considered: unify the two
  `normalize_input_value` functions into one shared normalizer (same
  NAME — the strongest textual lure in this file; no prior verdict
  names this pair, so this rejection is fresh). Contract difference
  here: `(orderset_cls, input_value) → [(field_path, Ordering |
  None)]` whole-value walk with branch recursion and a direction
  check vs `(filter_instance, raw_value, field_name?) → scalar /
  list / dict-patch` per-instance kind dispatch over the 8-kind MRO
  table — different signatures, different returns, different
  recursion (the order side recurses, the filter side strips the
  branch for `_apply_related_constraints`), opposite change
  responses (C18: a leaf-shape change moves the twin only; a
  direction-check change moves this file only). Same name, not the
  same rule. Trigger to reconsider: both families normalizing
  through one shared walker entry point (today they share only the
  field-iteration mechanics, which is already single-sited).
  Durable home: this function's docstring (already states the
  order-side leaf semantics + the shared-mechanics boundary, once
  D2 corrects its decision cite) + this artifact. Named for Worker 0
  as rejected index row `orders-normalize-vs-filter-normalize`.
- **Rejection (nested R-guards).** Considered: unify the leaf check
  with the two sets-side `Ordering`-membership guards into one
  direction-validation rule (same predicate family, near-identical
  message skeletons — fresh candidate, no prior verdict). Contract
  difference here: THREE seams, not one — (a) this check guards the
  Strawberry-deserialized VALUE at normalize time (`isinstance`,
  names the FIELD); (b)
  [orders-sets][orders-sets]`::_validate_normalized_terms` guards
  the `_normalize_input` RETURN at the pipeline boundary
  (exact-`type()`, names `_normalize_input` — the hostile-subclass
  discipline); (c) `_resolve_order_expressions` guards the flat
  TERMS at resolve time (`isinstance`, names the PATH —
  reachable via `get_flat_orders` overrides that never passed
  normalize). Different inputs, different predicates, different
  loci, opposite change responses (C11: a normalize-time reword
  moves this file only; dropping the resolve-time guard moves the
  sets side only). Three guards, not one rule. Trigger to
  reconsider: the pipeline collapsing to a single validation point
  (e.g. normalize becoming total so downstream guards are dead).
  Durable home: this artifact + the three existing seam docstrings
  (each already states its own locus). Named for Worker 0 as
  rejected index row `orders-normalize-check-vs-resolve-guards`.

### F-ENS — lazy provenance gate (file-local)

- **Contract + variation.** `_ensure_field_specs` populates `_field_specs`
  before direct normalization or permission checks: answers "is
  anything supplied?" THROUGH the family classifier (so the sentinel
  + list-shape grammar reads only from `orderset_cls._permission`),
  then builds specs iff the class has `get_fields` and owns no rows
  yet. Legitimate variation: the warm-up trigger only.
- **Sites + roles.** *Definition*: this file's statement 28.
  *Consumers*: statement 27 (normalize entry) +
  [orders-sets][orders-sets]`::_prepare_permission_input` (facade
  hook — verified call). *Oracles*: the sentinel-derivation test +
  the direct-mapping / model-free build tests — independent (they
  drive subclass `_permission` overrides and assert build/skip).
  No filter twin exists (filters builds at bind; filters R-e
  trigger checked fresh — the twin side needs none).
- **Challenges.** C13 → 1 here.
- **Owner + lifetime.** This function (existing owner: the order
  lazy-populate rule). Mutates `_field_specs` in place at most once
  per class per generation (reset by F-NS).
- **Migration.** None.
- **Distinct behavior.** The classifier-driven (not hardcoded)
  sentinel read is the load-bearing fix the docstring records: a
  hardcoded `strawberry.UNSET` gate disagreed with consumer
  `_permission.unset_sentinel` overrides and silently discarded
  gated fields. Verified against the body (traversal → walker →
  `any`).
- **Behavioral proof.** `static-reviewed`. Rejects "the gate can
  hardcode the sentinel" (override oracle pins derivation) and "a
  double build duplicates rows" (ownership check precedes the
  build; emit stages-then-commits).
- **Structural gate.** The pre-existing sentinel + build oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6f6ec946…` (dirt as F-ENUM — outside),
  [input-values][input-values] HEAD `f2566609…` (dirt as F-NORM —
  outside), [sets-mixins][sets-mixins] HEAD `ad8987ea…` (dirt as
  F-NORM — outside), [orders-sets][orders-sets] HEAD `6044ab1a…`
  (dirt as F-NORM — the judged hook line is the HEAD bytes), twin
  HEAD `82b52d97…` (absence verified: zero `_ensure_field_specs`
  tokens), [test-order-inputs][test-order-inputs] `baf23440…` (dirt
  as F-NORM — outside the judged oracles).

### F-NS — namespace lifecycle (convergence onto verified family `subsystem-clear-lifecycle`; no new row)

State contributor to the verified bus family (member 6 of its census:
`orders.input_namespace` / order ledger + `_field_specs` + factory
caches + `OrderSet` binding attrs / heavy clear — CONVERGE, lawful:
this file holds no registration contract, only the reset state +
wrappers + row). Statements 21–23 declare the ledger + provenance
table over the `make_set_input_namespace` quartet with the
order-family params; 29/30 are one-line wrappers over the owner
materializer / heavy clear; 31 registers the row
(`owner="orders.input_namespace"`, `before_bind=True`). Challenge C14
→ 1 (the bus + quartet owner; 0 here). The heavy-clear body
(ledger + specs + factory caches + `_lifecycle` binding attrs, parked
globals, best-effort lookups) and the materialize contract (LazyType
`__dict__` pin, `(name, cls)` idempotency, distinct-class raise) were
both verified against the owner bodies at HEAD — the wrapper
docstrings match them clause for clause. `_field_specs` doubles as
the provenance the traversal config points at by reference (the
`OrderSet._permission` declaration names this module's table) —
read by F-NORM through the walker and indirectly by
`_active_permission_field_paths` through the facade; the declaration
itself is this finding's reset state. Behavioral proof
`static-reviewed` (declarations + one-line wrappers + one
registration; no clear body spelled here). Freshness: target HEAD
`6f6ec946…` (dirt as F-ENUM — outside),
[utils-inputs][utils-inputs] HEAD `ee31d360…` (worktree `47b2af21…`
hardening inside the judged quartet/materialize/clear bodies — no
definition moved, no count affected),
[orders-factories][orders-factories] `4f35b66b…` (clean; cache
witness), [orders-sets][orders-sets] HEAD `6044ab1a…` (dirt as
F-NORM — the judged `_lifecycle`/`_permission` declarations are the
HEAD bytes), [sets-mixins][sets-mixins] HEAD `ad8987ea…` (dirt as
F-NORM — outside the judged facade delegate), [spec-028][spec-028]
`94a3141c…` (clean; Decision 9), family artifact
[dry-clear-lifecycle][dry-clear-lifecycle] (member-6 census),
[test-order-inputs][test-order-inputs] `baf23440…` (dirt as F-NORM —
outside the judged idempotency/collision/parking/clear oracles).
No new index row owed (holding item is the verified family).

## Defects

### D1 — alias comment names a `factories.py` consumer that imports none of the five (HEAD defect, clean lines — file for normal homing)

- **What.** The statements-14–18 comment claims "Tests and
  `factories.py` import these spec-028 Decision 9 names from this
  module". The Tests clause holds (fresh HEAD census: tests import
  all five aliases from this module); the `factories.py` clause is
  false for ALL five: [orders-factories][orders-factories] imports
  exactly one name from `.inputs` (`_build_input_fields` — verified
  at its import block, clean file). The actual second production
  consumer is [orders-init][orders-init] (`_input_type_name_for` —
  one of five), which the comment never names. A reader relying on
  the sentence (remove an alias thinking only tests use it, or
  rewire the factory's imports expecting alias breakage) reasons
  from a false consumer map — a wrong stated consumer, which
  principle 10 ranks below none. Same "states the filter-side shape
  as this file's own" pattern as the sibling D1s: the twin comment
  is byte-parallel, but the twin's `build_input_class` alias
  carries two intra-module production call sites while this one's
  carries zero (fresh census).
- **Bilateral-note outcome (carried from factories D1): FILED.** The
  factories item routed this comment here for fresh adjudication
  with no homing instruction; judged against this target's HEAD
  body, the comment's `factories.py` clause is false — filed below
  for normal homing. This closes the carried note; nothing rides
  further.
- **Lines.** Statements-14–18 comment lines — CLEAN at HEAD (the
  concurrent dirt sits at the statement-8 import line + inside
  statement 27 only, verified by the item diff). HEAD defect on
  clean lines → normal closeout homing, no conditional.
- **Owner.** `django_strawberry_framework/orders/inputs.py` alias
  comment (fix = restate the consumer map per the census above:
  tests all five + `__init__.py` one + intra-module two; prose-only,
  no behavior change).
- **Freshness.** Target HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516`;
  [orders-factories][orders-factories]
  `4f35b66b06fe67e800ac43dabe8a1733b221168d` (clean; import block);
  [orders-init][orders-init]
  `ed546f9c70d56d73e0d84a029e9e04f27da3934b` (clean; import block);
  [orders-sets][orders-sets] HEAD `6044ab1a…` (none-of-five witness);
  [test-order-inputs][test-order-inputs] HEAD `baf23440…` (all-five
  witness); twin [filters-inputs][filters-inputs] HEAD `82b52d97…`
  (contrast witness: two production calls).
- **Not fixed.** File items never fix; recorded for Worker 0 to home
  on a NAMED owning card at closeout.

### D2 — normalize docstring cites Decision 13 for a contract that lives in Decisions 5/8 (HEAD defect, clean lines — file for normal homing)

- **What.** The statement-27 docstring prefixes its three behavioral
  bullets (top-level-list flatten + concatenate; per-element walk
  with `None` short-circuit + permission-gate coupling; `RelatedOrder`
  recursion with source-path prefix) with "Per spec-028 Decision 13".
  Decision 13 is "Live HTTP coverage strategy" (verified: read in
  full — coverage plan + test list + rationale pointer; zero
  normalization semantics). The cited behaviors live in Decision 5
  (list shape + element-order tie-breaker), Decision 8 steps 3/6/7
  (cookbook walk, active-input-only scope, term-less pass-through),
  and Edge cases (null-direction no-op). A reader chasing the
  contract's rationale or rejected alternatives lands in the coverage
  plan instead of the pipeline contract — a wrong stated home,
  principle-10 class. (The rationale confirms Decision 13 was the
  coverage strategy from the initial draft, so this is not a
  renumbering fossil the spec explains — the cite was never right.)
- **Bilateral note (not homed here).** The
  [orders-sets][orders-sets] `apply_sync` docstring carries a twin
  cite (`None` directions filtered per "spec-028 Decision 13 --
  null-direction edge case") — a softer claim (that edge case IS
  enumerated in Decision 13's test list), but the same number for
  adjacent semantics. That cite lives in a file with a pending
  dedicated item; recorded here so it is not dropped, routed to the
  pending File `orders/sets.py` item for fresh adjudication (no
  homing instruction from this item).
- **Lines.** Statement-27 docstring lines — CLEAN at HEAD (the
  concurrent dirt sits inside the statement-27 BODY at the
  owner-name line + at statement 8; the docstring is untouched,
  verified by the item diff). HEAD defect on clean lines → normal
  closeout homing, no conditional.
- **Owner.** `django_strawberry_framework/orders/inputs.py`
  `normalize_input_value` docstring (fix = re-point the cite at the
  true homes above; prose-only, no behavior change).
- **Freshness.** Target HEAD `6f6ec946…`; [spec-028][spec-028]
  `94a3141c…` (clean; Decisions 5/8/13 + Edge cases read);
  [orders-sets][orders-sets] HEAD `6044ab1a…` (twin-cite witness).
- **Not fixed.** File items never fix; recorded for Worker 0 to home
  on a NAMED owning card at closeout (D1 may share the card — same
  file, both prose-only — at Worker 0's discretion; the sets.py twin
  cite is explicitly NOT part of either homing).

No other defects. Every remaining docstring claim checked held: the
module-docstring member map (all 7 groups present); the enum's
single-source + sentinel + portability clauses (Decision 5
byte-match, two consumers verified); the `_field_specs` comment
(normalize reads via the walker, `_active_permission_field_paths`
via the facade through the inherited mixin method, clear empties
it); the `__all__` helper's include/exclude list (Edge-case match);
the converter's fixed-leaf + symmetry clauses (Decision 5/12
match); the build docstring's triple shapes + flat-shorthand mapping
+ three simplifications (twin-verified); the `_ensure` classifier
clause (body-verified); the materialize/clear wrapper clauses
(owner-verified); the INPUTS_MODULE_PATH sync clause (call-chain
verified — the factory reaches it through the hook body). The axis-6
sweep finds no missing guard.

## Pending execution

None. No `execution-deferred` proof: all claims are `static-reviewed`
from HEAD bytes (byte-level greps, `ast.parse` enumeration,
full-body reads), every target behavior is pinned by executed
oracles on every suite run, and no probe was created that could
distinguish anything further. Sharded / Postgres cells are
inapplicable by construction: the target reaches no database, alias,
or dialect decision (pure enum + declarations + sync construction +
single-walk normalization; zero queryset tokens).

## Judgment

Zero-edit file item. Nine rules traced: seven file-local with proving
challenges (F-ENUM C1–C3; F-ALIAS C4–C5; F-PATH C6; F-CONC C7; F-CONV
C8; F-NORM C11–C12; F-ENS C13), two routed to existing holding
families on fresh evidence (F-BFS → open `set-arguments-factory-bfs`
as hook-body contributor, C9–C10 — CONVERGE per the brief; F-NS →
verified `subsystem-clear-lifecycle` member 6, C14), four rejections
with contract differences + triggers (R-conv CONVERGE filters R-a/R-c;
R-norm fresh same-name pair; R-build CONVERGE factories R-bag one
level down; R-guards fresh three-seam split), and the task-named
`dynamic-set-class-getter` interplay DIVERGED as membership (C15:
zero Layer-6 tokens — correctly absent per Decision 12). Enumeration
covers 31/31 statements and 26/26 named members. Two HEAD defects on
clean lines filed for normal homing (D1 closes the carried bilateral
inputs-comment note as FILED; D2 carries a twin-cite note to the
pending sets item). No pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `ITEM_BASELINE=6f41bd1e117fdeff37095fec429778b8c4b11d3b`:
`git diff <baseline> -- django_strawberry_framework/orders/inputs.py`
is EMPTY (exit 0, zero hunks) — the baseline captured the concurrent
hunt hunk (+2/-2), and the worktree blob is still byte-identical to
the dispatch record (`889b5971…`); the target was never edited,
reverted, or worked around. The artifact itself
(`docs/dry/dry-file-orders__inputs.md`) is a new untracked file, the
item's only output. No `uv run ruff` run (no `.py` edits; `.md` is
outside ruff format scope; no `.py` scratch created — the only
execution was a read-only `ast.parse` enumeration over a `/tmp` HEAD
extract). No shared-tree pytest run (static-decidable — see
`### Challenges` note; the entry command authorizes a focused
`--no-cov` run only where it could settle a judgment, and here it
could settle nothing). No `docs/dry/temp-tests/` scratch created.
HEAD confirmed `5ee86193` at start and at artifact completion.
Concurrent dirt (hunt edits across `django_strawberry_framework/`,
`tests/orders/`, `docs/dry/dry-0_0_15.md`) left untouched; the
`## Owned changes` ledger gains no row from this item. No commit.

## Index rows for Worker 0

Worker-0 instructions: (a) tick the plan item
`File orders/inputs.py — dry-file-orders__inputs.md` as verified under
Run `0.0.15 2026-09-22-5` once Worker 2 agrees; (b) add these eleven
`## Responsibility index` rows verbatim (holding item
`File orders/inputs.py`); (c) home D1 + D2 on NAMED owning card(s) at
closeout (both HEAD defects, clean lines — normal homing, no
conditional; D1 closes the carried bilateral note; D2's sets.py twin
cite rides with the pending File `orders/sets.py` item, not the
card). No `## Families` item: zero new families were named (every
shared mechanism already has its single-sited owner; F-BFS/F-NS are
convergences onto existing rows).

| `orders-direction-enum` | `django_strawberry_framework/orders/inputs.py::Ordering` | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-input-substrate-aliases` | `django_strawberry_framework/utils/inputs.py` substrate (machinery; order owns its five alias declarations at `django_strawberry_framework/orders/inputs.py`) | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-inputs-module-path` | `django_strawberry_framework/orders/inputs.py::INPUTS_MODULE_PATH` | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-concrete-field-names` | `django_strawberry_framework/orders/inputs.py::_get_concrete_field_names_for_order` | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-leaf-annotation` | `django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation` | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-normalize-leaf-semantics` | `django_strawberry_framework/orders/inputs.py::normalize_input_value` | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-ensure-field-specs` | `django_strawberry_framework/orders/inputs.py::_ensure_field_specs` | `django_strawberry_framework/orders/inputs.py` | File `orders/inputs.py` | file-local |
| `orders-converter-vs-filter-kind-ladder` | `django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation` (rejection recorded here; CONVERGE with verified filters/inputs R-a/R-c on fresh evidence) | `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/filters/inputs.py` | File `orders/inputs.py` | rejected |
| `orders-normalize-vs-filter-normalize` | `django_strawberry_framework/orders/inputs.py::normalize_input_value` (rejection recorded here; fresh same-name pair, no prior verdict) | `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/filters/inputs.py` | File `orders/inputs.py` | rejected |
| `orders-build-fields-vs-filter-bag-build` | `django_strawberry_framework/orders/inputs.py::_build_input_fields` (rejection recorded here; CONVERGE with verified orders/factories R-bag on fresh evidence, one level down) | `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/filters/inputs.py` | File `orders/inputs.py` | rejected |
| `orders-normalize-check-vs-resolve-guards` | `django_strawberry_framework/orders/inputs.py::normalize_input_value` (rejection recorded here; fresh three-seam split, no prior verdict) | `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/orders/sets.py` | File `orders/inputs.py` | rejected |

(F-BFS needs no new row: open family `set-arguments-factory-bfs`
already covers this file; this artifact records the hook-body
contribution. F-NS needs no new row: verified family
`subsystem-clear-lifecycle` already covers this file as member 6.)

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-clear-lifecycle]: dry-rule-subsystem-clear-lifecycle.md
[dry-filters-inputs]: dry-file-filters__inputs.md
[dry-mutid]: dry-rule-generated-mutation-input-identity.md
[dry-orders-base]: dry-file-orders__base.md
[dry-orders-factories]: dry-file-orders__factories.md
[dry-orders-init]: dry-file-orders____init__.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[definition]: ../../django_strawberry_framework/types/definition.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[input-values]: ../../django_strawberry_framework/utils/input_values.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-order-inputs]: ../../tests/orders/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

### Trace-first record (written before opening `## Findings`)

HEAD pinned at `5ee86193`: `git rev-parse --short HEAD` printed `5ee86193`
at session start. Target `django_strawberry_framework/orders/inputs.py`:
HEAD blob `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (395 lines, governs);
worktree blob `889b59712e7d05d427129d79e95a61f3418ee687` (+2/-2 hunt dirt:
`_safe_class_name` import + adoption in `normalize_input_value`'s
owner-name read) — never touched, never traced. All production/test reads
below are HEAD bytes (`git show HEAD:<path>`, `git grep <pat> HEAD`).
Artifact observed at `Status: ready-for-verification/1`,
`Run: 0.0.15 2026-09-22-5`, untracked (66,869 bytes).

Peek disclosure: before recording this trace I read the artifact's
`##`/`###` HEADERS ONLY (section map via grep) plus the dispatch brief's
own summary (7 file-local, F-BFS/F-NS convergences, D1/D2 shapes). No
Finding, Enumeration, Challenge, Matrix, Defect, or Index-row BODY was
read. Sites, roles, counts, and owner choices below are fresh derivations
from HEAD bytes with censuses; the module's own layout (not W1's labels)
drives the grouping.

Window-diff attribution (re-verified from content, hunk by hunk):
`git diff --name-only ITEM_BASELINE -- <package tests examples>` names
exactly `sets_mixins.py`, `types/finalizer.py`, `tests/test_sets_mixins.py`,
`tests/types/test_finalizer.py` (15/38/265/53-line stat). Every hunk is
concurrent-external hostile-hardening, zero relation to this item:
`sets_mixins.py` gains the `_safe_class_name` import, an
`except BaseException` truthiness guard in `resolve_lazy_class` (+prose),
and a `_safe_class_name` label in `require_re_readable_field_declaration`;
`types/finalizer.py` gains guarded `__mro__`/`__strawberry_definition__`
interrogation with a typed `ConfigurationError`; the two test files gain
companion hostile-metaclass pins (refusing/unformattable `__qualname__`,
bool-boom owners, unreadable MRO/definition). No hunk touches
`orders/inputs.py`, names any rule it owns, or reads like Worker 1's.
Attribution CONFIRMED all-hunt; zero tracked edits by Worker 1 stands.

Independent enumeration (instrument: `ast.Module.body` of the HEAD bytes):
31 body nodes — 1 module docstring, 11 imports (incl. `__future__`), 1
`TYPE_CHECKING` guard, 5 alias `Assign`s (L53-57), 1 `AnnAssign`
(`INPUTS_MODULE_PATH`), 1 `ClassDef` (`Ordering`: 6 members +
`is_ascending` + `resolve`), 2 ledger `AnnAssign`s, 1 tuple `Assign`
(4 bindings: 2 ledger rebinds + `_materialize_input` +
`_clear_input_namespace`), 7 `FunctionDef`s, 1 `register_subsystem_clear`
`Expr`. Named code surface: 5 aliases + 1 constant + enum(+2 methods) +
4 namespace bindings + 7 functions + 1 register call.

Rule groups traced (sites + roles + challenges + my owner choice):

T1 — Direction enum (`Ordering`, `is_ascending`, `resolve`).
Definition: this module only. `F().asc(` / `.desc(` occur package-wide
only here (L125-126; all other hits prose); `is_ascending` defined once,
consumed by name at `orders/sets.py::OrderSet._resolve_order_expressions`
(Min/Max pick) and inside `resolve`; every other `Ordering` mention
package-wide is prose. Oracles: `tests/orders/test_inputs.py` member +
resolve pins; live `test_library_api.py` NULLS-positioning (21 order
tests). Challenges: new member (e.g. case-insensitive ASC) → 1
definition (enum + both methods move together); new discrimination rule
→ 1 (`is_ascending`; both consumers follow); new OrderBy construction →
1 (`resolve`). Owner: `orders/inputs.py::Ordering`. Home: file-local.

T2 — Substrate aliases (5 re-exports). Each RHS names its single-sited
owner (`utils/inputs.py::GeneratedInputFieldSpec` /
`build_strawberry_input_class` / `iter_set_subclasses` /
`set_input_type_name`; `utils/strings.py::graphql_camel_name`). Twin
block in `filters/inputs.py` (only other `Domain-local aliases` site)
considered: bilateral one-token re-exports, not independent definitions
— posit substrate rename → aliases follow (0 definitions here). The
`is`-identity gate in `tests/utils/test_inputs.py` mechanically pins all
ten aliases to their owners. Consumers: tests import all five orders
aliases; production imports exactly one (`orders/__init__.py` takes
`_input_type_name_for`); `orders/factories.py` imports NONE (verified:
its only `.inputs` import is `_build_input_fields`; its `build_input_class`
mention is docstring prose). The alias comment's `factories.py` half is
therefore false at HEAD (Tests half true) — defect territory, see D1
reconciliation. Home: file-local declarations.

T3 — `INPUTS_MODULE_PATH`. Single constant; per-flavor values necessarily
differ (filters/forms/mutations/rest_framework each pin their own).
Literal census: one definition, prose mentions, one independent-literal
test oracle, zero code rebuilds by concatenation. Challenges: rename the
module → constant + name-readers move (consumers: factory BFS lazy refs,
`order_input_type`, materializer); filter constant untouched. Owner:
here. Home: file-local.

T4 — Namespace lifecycle (quartet unpack, `materialize_input_class`,
`clear_order_input_namespace`, register row `owner="orders.input_namespace"`,
`before_bind=True`). Mechanics single-sited in
`utils/inputs.py::make_set_input_namespace` (composes
`make_input_namespace` + heavy `clear_generated_input_namespace`);
parked-globals lifecycle stated once on `make_input_namespace`; this
module keeps declarations + thin wrappers + the bus row. The verified
`subsystem-clear-lifecycle` family already lists member 6
(`orders.input_namespace`, narrow, heavy clear) — same rule, same
membership. Finalizer subpass 4 drives BFS + `materialize_input_class`
through the shared `_bind_sidecar_sets` helper. Challenges: new cached
slot → 1 definition (the factory/clear pair); new lifecycle phase → the
bus, not here. Owner: `registry.py` clear bus; target role: state
contributor. Home: CONVERGE onto verified `subsystem-clear-lifecycle`,
transcribes nothing.

T5 — `_get_concrete_field_names_for_order`. Single derivation (names
list; column-backed + not M2M). Second sites hunted: mutations
`editable_input_fields` (owner docstring records the OPPOSITE selection
— fields list, editable-only, forward-M2M included — as deliberate
non-duplication; verified against both bodies); filter `__all__`
NARROWS django-filter's upstream sweep (add-PK/remove-M2M, no `_meta`
derivation of its own); rest_framework rejects bare `"__all__"` loud;
every other `column` read answers a different question (partial-update
exclude math, uniqueness groups, per-field backing resolution,
forward-single predicate, join-column match). Challenges: exclude a new
virtual kind → 1 definition; change orderable scope → 1. Owner: here.
Home: file-local.

T6 — `convert_order_field_to_input_annotation`. Constant return
(`Ordering | None`) over a 2-param shape vs the twin's 8-kind
`convert_with_mro` dispatch over 4 params. Contract difference:
no leaf-shape divergence per spec-028 Decision 5 (twin R-a/R-c cover the
same pair from the other side; triggers re-checked fresh — no divergence
at HEAD). Challenges: thread new converter context → each side moves
independently (no shared signature definition); diverge one leaf kind →
this function alone. Owner: here. Home: file-local.

T7 — `_build_input_fields` (+ `_leaf_of`). Triple-supply hook body: the
emission scaffold (flatten/camel/kwargs/collision guards/spec keying) is
single-sited in `utils/inputs.py::emit_set_input_field_triples`; the
closures carry order semantics (`field_name or top_name` related paths,
fixed `Ordering | None` leaves). Consumed by the BFS factory hook
(`OrderArgumentsFactory._build_input_triples` → this body → base
`_ensure_built` walk). Twin deltas verified in both bodies (operator-bag
build, `HIDE_FLAT` skip absent here; the logic-bag splice lives in the
twin FACTORY hook, not the twin `_build_input_fields` — the
"no `_build_logic_fields` call" note reads pipeline-vs-pipeline, true in
substance). Challenges: new emission mechanic → 1 (the scaffold); new
order leaf shape → the `_leaf_of` closure. The hook-body aspect is the
open `set-arguments-factory-bfs` rule (owner
`utils/inputs.py::GeneratedInputArgumentsFactory`; index row already
covers this file). Home: CONVERGE onto the open family, transcribes
nothing; closure semantics stay file-local notes.

T8 — `normalize_input_value` (whole-value walk + leaf check). Walk
mechanics (`iter_active_fields` + `orderset_cls._input_traversal()`)
composed by name from already-single-sited substrate — 0 definitions
here for the traversal; the one-object-per-family config lives in each
family's `_permission` (no second definition anywhere; the twin
artifact's F-6 names no index row and no consolidation). Second sites
hunted: (a) `filters/inputs.py::normalize_input_value` — different
contract (per-filter value translation, different arity/return); the
docstring's "operator-bag layer removed" names the real leaf-shape
delta; (b) `FilterSet._normalize_input` — structural whole-value twin
with a different output contract (form-data dict vs pair list), LOGIC
arms, RELATED strip-vs-recurse, spec-None fallback-vs-ensure; posit any
change to either side's contract → the other doesn't move; (c) the
leaf-acceptance trio: this emission check (`isinstance`, field context)
vs `sets.py::_resolve_order_expressions` (same predicate, resolution
intake, path context, guards direct callers/overrides) vs
`sets.py::_validate_normalized_terms` (exact-type return-contract gate,
hostile-subclass rationale — rejects subclasses the other two accept).
Three boundaries, one-token predicate, per-raiser messages (standing
per-message-grammars class); no shared definition to extract without
machinery. Challenges: new accepted leaf shape → emission moves (C
unchanged — different strictness); new traversal mechanic → the
substrate once. Owner: here. Home: file-local.

T9 — `_ensure_field_specs`. Single warm-up gate; no twin (zero `ensure`
in `filters/inputs.py`; the filter side tolerates spec-None with a
`_form_key_for_python_attr` fallback — design difference, and no
contract source requires a filter gate, so axis 6 is investigated with
no defect). Consumers: `normalize_input_value` + the mixin hook
`OrderSet._prepare_permission_input`. Twin R-e covers the same pair
from the other side; trigger re-checked fresh (no pre-bind filter
normalization at HEAD). Oracle pins the derived-sentinel invariant
against the hardcoded-gate failure mode. Challenges: new grammar fact →
the `_permission.traversal` derivation, read here by reference (0
definitions). Owner: here. Home: file-local.

Matrix pre-discharge (against the real surface): axis 1 via the twin
reads above (every member's twin considered); axis 2 inapplicable —
pure CPU + lazy queryset construction, no await boundary in the
module (async coloring lives in `sets.py::apply_async`, sharing
`_apply_orderings`); axis 3 — no re-derivation found (name/path/default
all read by name; literal + camel + column censuses clean); axis 4 —
build/parse halves share `_field_specs`/`FieldSpec` in-file with the
grammar single-sited in `utils/inputs.py`; axis 5 — spec-028 Decisions
3/5/8/9/12 + edge cases + independent oracles at package + live tiers
(see D2 reconciliation for the Decision 13 citation); axis 6 —
family census done (Ordering/ensure/`__all__`/logic-bag/HIDE_FLAT
absences each traced to a contract source or a no-source design
difference; no enforcement gap).

Probes: none run — every claim above is structural (imports, call
sites, docstring/spec texts) and fully determined by HEAD-byte reads
plus the package's own oracles; execution would add no evidence. No
scratch dir created. Ruff on touched paths and prose-rule checks follow
in reconciliation (touched path is the `.md` artifact only).

### Reconciliation (after reading `## Findings`) + verdict

Read in full after the trace above: System trace, Matrix, Enumeration,
Challenges, all nine Findings, both Defects, Pending execution,
Judgment, Implementation, Index rows, link block. Every reconciliation
below is explicit.

(a) Homes agree 9/9 with my independent trace: T1↔F-ENUM, T2↔F-ALIAS,
T3↔F-PATH, T4↔F-NS (verified-family converge, transcribes nothing),
T5↔F-CONC, T6↔F-CONV, T7↔F-BFS (open-family converge, transcribes
nothing), T8↔F-NORM, T9↔F-ENS. Definition counts agree on every
challenge (C1–C19 re-derived against the same HEAD bodies; C4/C9/C12/C14
correctly count 0 here with the definition at the named owner).

(b) The dispatch brief's "ZERO rejections" does NOT describe this
artifact: it carries FOUR nested rejections (R-conv, R-norm, R-build,
R-guards), each with contract difference + trigger + durable home +
named index row. All four are sound on fresh evidence: R-conv CONVERGEs
verified filters R-a/R-c (fixed-leaf vs 8-kind dispatch verified in
both bodies); R-build CONVERGEs verified factories R-bag one level down
(the logic splice verified at the twin FACTORY hook, exactly as W1
states); R-norm (same-name pair) and R-guards (three-seam split) are
fresh and correctly reasoned — the trio loci/strictness split in
R-guards matches my independent T8(c) analysis seam for seam. Worker 0
must transcribe the four rejected rows, not zero. F-ALIAS's declined
alias-mirror row is accepted (vacuous candidate: family-prefixed names,
disjoint consumers; twin L-k precedent identical).

(c) Enumeration: W1's 31/31 statements + 26/26 unique names agree with
my independent `ast.Module.body` walk member by member (26 recomputed:
5 aliases + 1 const + class + 6 members + 2 methods + 2 annotations +
2 fresh quartet bindings + 7 functions). Every member homed; the nested
`_leaf_of` counted within F-BFS. Complete.

(d) Matrix, per axis: (1) twin read whole first, every member's twin
considered — agree, with O1 below as the one unnamed pair; (2)
inapplicable with verified reason (zero async/await/sync_to_async/
queryset tokens — confirmed by full read); (3) no re-derivation —
agree (censuses for literal/camel/column/naming all reproduce); (4) the
three disproved pairs are correctly disproved, but the most
axis-4-shaped halves (build-emits ↔ normalize-consumes over
`_field_specs`) go unnamed — see O2; (5) four media with the one failing
cite filed as D2 — agree; (6) absences each traced to a contract source
or a no-source design difference — agree, no omission defect owed.

(e) F-BFS convergence (open family): lawful on fresh evidence. Same
rule (the BFS triple-supply contract: factory hook splices these hook
bodies; walk/collision/cache in the base); the hook-body aspect routes
to the holding family while closure semantics stay file-local notes;
index row already covers this file. F-NS convergence (verified
family): lawful — member-6 membership reproduced from the family
census; no new assertion about the bus; the verified verdict is
untouched. Neither convergence transcribes a row.

(f) File-local sweep, tested hard: I hunted second sites for every
member with package-wide HEAD censuses (direction reads, alias blocks,
path literal, column idiom, leaf trio, ensure analogues, `__all__`
handlers, OrderBy builders, BFS drivers, ledger writers). Every W1
engagement reproduced — EXCEPT one unnamed pair, recorded as W2
correction rejection O1 (policies-run precedent: on-record correction,
item still verifies since no home changes).

(g) D1: the carried bilateral inputs-comment note is CONFIRMED and
FILED — outcome: filed. My census agrees on every clause (tests import
all five; factories imports none — only `_build_input_fields`;
`__init__` imports one; intra-module two; twin contrast two-vs-zero
production calls verified at twin L748/L963). HEAD defect on clean
lines (dirt verified at stmt-8 import + stmt-27 body only) → normal
closeout homing. This closes the carried note; nothing rides further.
D2: CONFIRMED and correctly filed. Decision 13 verified as the coverage
strategy (read in full); true homes verified (D5 list shape, D8 steps
3/6/7, Edge no-op cases); the rationale draft-history claim verified
(rev1 pinned D13 as coverage); the sets.py twin cite verified present
at HEAD (`orders/sets.py` L797–798) and correctly ROUTED (not homed) to
the pending sets item. Both defects meet the sibling HEAD-defect bar.

(h) Pending execution: empty with an inapplicable-by-construction
reason — accepted (verified: zero database/alias/dialect tokens in the
target; construction lazy, normalization pure). No `proof:`/`gate:`
owed. Item is plain `verified` (no pending-execution qualifier).

(i) Freshness: every HEAD + worktree pin re-hashed — all match except
the C6 note below. Target HEAD `6f6ec946…` governs throughout; all
judged lines verified as HEAD bytes. HEAD stayed `5ee86193` for the
whole verification (re-checked before verdict).

(j) Prose/shape rules: link block carries all 10 canonical headers;
citations use the sibling `path::Symbol` convention; no tests created
(tier N/A); no feedback mention; item diff is `.md`-only so
process-provenance/test-tier/production-format rules are vacuous.
`uv run ruff format --check` → `1 file already formatted`, exit 0;
`uv run ruff check` → `No Python files found / All checks passed`,
exit 0 (artifact is `.md`, ruff-excluded in effect). The layout script
reports docs/dry artifacts excluded — not checked. Post-link-block
placement matches the verified init artifact precedent.

Corrections (all non-structural; homes, counts, and defects stand):

- C1: C5 "intra-module use at 19-annotation/emit call" misnumbers the
  statement — the alias-in-annotation use is `FieldSpec` at statement
  22 (`_field_specs` annotation), plus `_input_type_name_for` at the
  emit call. F-ALIAS states it correctly; the C5 row does not.
- C2: F-ENUM "Decision 5 code block (byte-matches the tree)" overstates
  — the enum BODIES match, but both method docstrings differ (the tree
  carries the two-consumer + Min/Max rationale absent from the spec
  block). Read "bodies match" for "byte-matches".
- C3: "10 `test_query` modules carry the token" is irreproducible —
  HEAD census is 13 `.py` modules (141 hits; 14 incl. README; 12 with
  `orderBy: [`), identical on the worktree. Oracle-population
  characterization only; the relied-upon oracles (48 package tests +
  named live tests) are unaffected.
- C4: F-CONV "table-driven converter test (scalar/choice/FK/PK/
  BigIntegerField)" misdescribes the oracle — the single converter
  test drives 2 cases (title field + `None`); the 5-type list is
  docstring prose. Proof conclusion unaffected (the body `del`s its
  args and returns a constant, so differentiation is impossible).
- C5: F-ENUM "introspect `OrderBy.as_sql`, never read the property"
  misdescribes the mechanism — zero `as_sql` in the test file; the
  resolve oracles assert spelled attributes (`descending`,
  `nulls_first/last`, `expression.name`) and the classification test
  necessarily invokes the property under test with spelled
  expectations. Independence holds; mechanism wording does not.
- C6: dirt note pins `types/definition.py` by worktree hash only
  (`01f78d93…`); HEAD pin `fa6c4d33` missing. Judged use is
  annotation-only so no finding depends on it — record-only gap.

Observations (analyzed here; no home changes):

- O1 — W2 CORRECTION REJECTION `orders-normalize-vs-filterset-normalize`
  (pair W1 never names; verified absent from the artifact text).
  Considered: unify `orders/inputs.py::normalize_input_value` with
  `FilterSet._normalize_input` (filters/sets.py L2238) — the structural
  whole-value twin: both walk `iter_active_fields` + their family's
  `_input_traversal`. Contract difference: pair-list emission
  (`[(field_path, Ordering | None)]`) with RELATED recursion +
  direction check + spec-None defensive skip vs form-data-dict
  emission with LOGIC arms, RELATED strip (owned by
  `_apply_related_constraints`), and spec-None fallback derivation;
  the shared traversal mechanics are already single-sited substrate
  both compose by name (0 definitions there). Opposite change
  responses: any output/branch/policy change moves exactly one side.
  Trigger to reconsider: both families emitting one normalized shape
  through one shared walker entry point. Durable home: this section +
  the index row below (no docstring change owed). F-NORM stays
  file-local. Named for Worker 0 as one additional rejected index row.
- O2 — W1's axis-4 sweep omits the build/parse halves
  (`_build_input_fields` emits `FieldSpec` rows;
  `normalize_input_value` consumes them). Analyzed: co-located halves
  over the module's own table with the `FieldSpec` grammar + keying
  single-sited in `utils/inputs.py` — a spec-shape change moves the
  owner once (count 1). No pair to twin, no home change, no row owed.

Defects found by Worker 2: none. (O1 is a correction rejection, not a
production defect; both W1 defects confirmed as filed.)

VERDICT: `verified` (zero-edit file item; no pending execution; no
production edits; no scratch created; nothing to remove; no commit).
Worker 0: tick the row; transcribe TWELVE index rows (W1's eleven +
`orders-normalize-vs-filterset-normalize` per O1); home D1 + D2 on
NAMED owning card(s) at closeout (D1 may share D2's card at Worker 0's
discretion — same file, both prose-only); D2's sets.py twin cite rides
with the pending File `orders/sets.py` item, not the card. No
`## Families` item. Plan correction owed: the run-5 dispatch line's
"ZERO rejections" misstates this artifact, which carries four nested
rejections (+ this one W2 correction rejection).
