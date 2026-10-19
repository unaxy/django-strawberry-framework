# DRY review: `filters/factories.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

Target owns the filter Layer-5/6 declarations (`django_strawberry_framework/filters/factories.py`, 177 lines,
blob `366e0490`; absent from `git status --short`, target CLEAN): the `FilterArgumentsFactory`
BFS subclass declaration (8 class attrs + the operator-bag `_build_input_triples` hook), the
family-owned Layer-6 dynamic-FilterSet cache dict + reserved-keys literal, and the thin
`get_filterset_class` public delegate over the shared `make_dynamic_set_getter` product.
No BFS walk, no collision check, no cache-key hashing, no `type(...)` skeleton, no namespace-clear
body lives here — all of that is owned by [utils/inputs.py][utils-inputs].

Traced end to end, orders twin FIRST (whole `orders/factories.py`, 155 lines, blob `4f35b66b`):
the two factories are behavior-plus-contract twins — same base class, same 8-attr parameterization
shape, same Layer-6 getter construction, deliberately disjoint caches/registries/suffixes, and
exactly one semantic divergence (the operator bag, spec-028 Decision 8). Owner bodies in
[utils/inputs.py][utils-inputs] (`GeneratedInputArgumentsFactory`, `make_dynamic_set_getter`,
`make_set_meta_cache_key`, `normalize_set_meta_for_factory`, `create_dynamic_set_class`,
`resolve_set_meta_fields`, `promote_set_meta_fields`, `clear_generated_input_namespace`,
`FILTERSET_FIELDS_ALIAS`), the triple/logic builders in [filters/inputs.py][filters-inputs]
(`_build_input_fields`, `_build_logic_fields`, `LOGIC_OPERATORS`), the metaclass write-back in
[filters/sets.py][filters-sets] (`promote_set_meta_fields` call) and its order mirror in
[orders/sets.py][orders-sets], the phase-2.5 consumer in [finalizer.py][finalizer]
(`_bind_filtersets` reading `FilterArgumentsFactory(...).arguments`), the non-consumer in
[connection.py][connection] (`Meta.filterset_class` sidecar read directly, never routed here),
the export parity in [orders/__init__.py][orders-init] (factory via submodule only, both sides),
the naming owner in [sets_mixins.py][sets-mixins] (`ClassBasedTypeNameMixin.type_name_for`),
oracles in [test_factories.py][test-filter-factories] (828 lines) and
[test_composition.py][test-composition] (both factories' ledgers asserted together), contract
sources spec-027 (Decisions 4/6/9, Layer 5/6) and spec-028 (Decision 8/12), and the upstream
cookbook ports (`filter_arguments_factory.py`, `filterset_factories.py`) as out-of-population
sources.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — searched, twin read FIRST whole. `FilterArgumentsFactory`
vs `OrderArgumentsFactory`: shared substrate (direct subclasses of
[utils/inputs.py][utils-inputs]`::GeneratedInputArgumentsFactory`, 8 hook attrs each, one
`_build_input_triples` override each) with one genuine semantic divergence — the filter hook
splices `_build_logic_fields` (the `and_`/`or_`/`not_` bag), the order hook returns bare triples
(spec-028 Decision 8; rejection R1). Layer-6 twins: both built by
[utils/inputs.py][utils-inputs]`::make_dynamic_set_getter` with disjoint caches
(`_dynamic_filterset_cache` / `_dynamic_orderset_cache`), disjoint reserved literals
(`{"filterset_base_class"}` / `{"orderset_base_class"}`), disjoint suffixes
(`AutoFilter` / `AutoOrder`), and the filter-only `require_fields_or_exclude=True` +
`fields_alias=FILTERSET_FIELDS_ALIAS` vs order `None` defaults (rejections R2, R6). Disjointness
is the documented rule on both sides ("a filter clear cannot drop an order class (and the
reverse)").
2. **Sync/async twins** — inapplicable with reason: zero `async def`, zero `await` in target
(verified by search); the BFS build + `type(...)` construction are pure sync construction at
finalize time executing inside no queryset boundary (verified: no `base_queryset`, no
`run_in_one_sync_boundary`, no `model_for` definition/call in target). The base factory likewise
carries no async surface.
3. **Derived rather than repeated knowledge** — searched. `FILTERSET_FIELDS_ALIAS` imported from
its owner (compose by name, never re-spelled); input type names derived via the base `__init__`
through `set_input_type_name` → `ClassBasedTypeNameMixin.type_name_for` (family F-3, consumer);
cache keys via `make_set_meta_cache_key` (owner F-2); Meta synonym rule via `resolve_set_meta_fields`
(owner); class-Meta write-back via `promote_set_meta_fields` (owner, shared with both metaclasses
— verified call sites [filters/sets.py][filters-sets] and [orders/sets.py][orders-sets]). No local
re-derivation of any shared fact.
4. **Inverse / round-trip pairs** — searched. `get_filterset_class` explicit-passthrough vs
dynamic-build halves are two arms of ONE owner getter (`make_dynamic_set_getter`'s
`get_set_class`), not a pair; normalize (`normalize_set_meta_for_factory`) vs key
(`make_set_meta_cache_key`) halves both live in [utils/inputs.py][utils-inputs] under one family.
No local pair, no second half to twin.
5. **Contracts in another medium** — searched. Oracles: [test_factories.py][test-filter-factories]
(BFS reachability, cycle/diamond dedup, collision refusal wording naming `FilterArgumentsFactory` /
`FilterSet`, cache-key equivalences incl. alias/set/exclude-None/reserved-keys arms) and
[test_composition.py][test-composition] (both factories' `input_object_types` asserted in one test)
exercise literal behavior; per spec-027 Decision 9 they address the `input_object_types` /
`_type_filterset_registry` caches directly — that addressability IS the specified contract, not
oracle-rot. Projections: module-docstring Layer 5/6 + spec decision pointers, spec-027 Decisions
4/6/9, spec-028 Decisions 8/12. Upstream cookbook twins are out-of-population sources (R4). No test
or doc restates a package rule as an independently maintained definition.
6. **Enforcement by omission** — enumerated. `require_fields_or_exclude=True` is filter-only by
documented split ([utils/inputs.py][utils-inputs]`::create_dynamic_set_class` records the
django-filter metaclass assertion vs the order plain-metaclass lifecycle; rejection R6).
`fields_alias` filter-only (`None` on orders — no cookbook synonym; verified
[orders/factories.py][orders-factories]). Neither Layer-6 cache dict carries a clear hook — the
documented lifecycle on both sides (keys embed model identity, test-isolation nicety only,
"add a clear hook here only if a consumer reload path ever demands it"); the package test
fixture clears `_dynamic_filterset_cache` directly. No contract source (spec, glossary anchor,
owner prose, oracle) establishes a clear-hook rule for the unconsumed deferred surface, so no
defect is filed — correct per axis 6.

### Enumeration

Instrument: every name in `ast.Module.body` that defines a rule or binds a value — top-level
`ClassDef` / `FunctionDef` / `Assign` (incl. `AnnAssign`) plus every member (`FunctionDef` /
`Assign` / `AnnAssign`) under the class. Module docstring (projection) and the 5 import
statements (references, not definitions) excluded with reason. **Count: 14 members**, every one
assigned below (F = family incl. proposed, L = file-local, R = rejection).

| # | Member | Home |
|---|---|---|
| 1 | `_dynamic_filterset_cache` | F-2 (family-owned cache declaration; disjointness rule at owner) |
| 2 | `_RESERVED_FACTORY_KEYS` | L-a (family vocabulary literal; order twin differs by design) |
| 3 | `FilterArgumentsFactory` | F-1 (subclass declaration over the shared substrate) |
| 4 | `input_object_types` | F-1 (family cache) / F-5 (clear-bus consumer) |
| 5 | `_type_filterset_registry` | F-1 (family collision registry) / F-5 (clear-bus consumer) |
| 6 | `_collision_registry_attr` | F-1 (hook-param declaration) |
| 7 | `_factory_label` | F-1 (hook-param declaration) |
| 8 | `_family_label` | F-1 (hook-param declaration) |
| 9 | `_rename_noun` | F-1 (hook-param declaration) |
| 10 | `_related_attr` | F-1 (hook-param declaration) / F-4 (names the `RelatedFilter` collection seam) |
| 11 | `_related_target_attr` | F-1 (hook-param declaration) / F-4 (names the target-attr seam) |
| 12 | `_build_input_triples` | F-1 (filter adapter; order twin separate per R1) |
| 13 | `_get_filterset_class` | F-2 (declaration over the owner getter) |
| 14 | `get_filterset_class` | F-2 (thin public delegate; cookbook-mirror contract in docstring) |

Static probe (AST walk, read-only): `register_subsystem_clear`, `__all__`, `resolve_lazy_class`,
`model_for`, `base_queryset`, `run_in_one_sync_boundary`, `promote_set_meta_fields`,
`make_set_meta_cache_key` appear **zero** times as definitions in the target — no second owner
for any indexed family machinery. The clear registration lives in
[filters/inputs.py][filters-inputs] (`clear_filter_input_namespace`, owner `filters.input_namespace`);
the factory is deliberately absent from `filters/__init__.py` `__all__` (export parity, verified).

### Challenges

Authoritative definitions only; consumers, oracles, projections that also move listed but not counted.

- **BFS traversal** (queue discipline, enqueue/seen gates, collision rule, subclass-rejection
guard): posit FIFO→LIFO or a new seen-gate → 1 definition moves
([utils/inputs.py][utils-inputs]`::GeneratedInputArgumentsFactory`); 0 here. Consumers (finalizer
subpass 4 both sides, both clear fns, both test modules) follow by construction.
- **New factory-wide hook parameter** (collision message needs a new token): posit adding a ninth
hook attr → 1 definition (base declares + reads it) + 2 family declarations (this file, order
twin) — declarations, not definitions (principle 1 shape, already realized).
- **Cache-key shape** (new unordered container, new Meta key): posit `frozenset`-valued `exclude`
handling change → 1 definition (`make_set_meta_cache_key` / `_hashable_meta_value`); 0 here.
Posit a new `fields` synonym → 1 definition (`resolve_set_meta_fields`); the alias constant is
owned in [utils/inputs.py][utils-inputs], this module passes it unchanged.
- **Dynamic-class build rule** (model validation, fields/exclude gate wording): posit the gate
accepting `exclude`-only on the filter side → 1 definition (`create_dynamic_set_class`);
`require_fields_or_exclude=True` here is a declaration (0 definitions).
- **Getter signature** (new named construction param): posit the owner gaining a param →
1 definition (`make_dynamic_set_getter` / `normalize_set_meta_for_factory`) + 2 reserved-key
declarations move (each names its family's explicit-param sibling — R2).
- **Operator bag** (new logic operator): posit a fourth operator → 1 definition
([filters/inputs.py][filters-inputs]`::LOGIC_OPERATORS`); the hook here splices
`_build_logic_fields` wholesale, 0 definitions here.
- **Type-name rule** (new suffix, new empty-token policy): posit renaming every generated input
→ 1 definition ([sets_mixins.py][sets-mixins]`::ClassBasedTypeNameMixin.type_name_for`); the
base `__init__` derives via `set_input_type_name`, 0 here.

All probes static-reviewed (body inspection + population greps + AST walk). No mutating proof:
no ordering, transactional, or async behavior is decided in this file.

## Findings

**F-1 `set-arguments-factory-bfs` (NEW FAMILY, for Worker 0 index).** Contract: every reachable
set-family root BFS-builds its Strawberry input classes through one walk + per-class collision
check + idempotent cache + subclass-rejection guard, parameterized per family by 8 hook attrs and
one `_build_input_triples` override. Owner:
[utils/inputs.py][utils-inputs]`::GeneratedInputArgumentsFactory` (walk, collision, cache,
`__init_subclass__` guard, `__init__`/`arguments`/`_ensure_built`/`_build_class_type`).
Declarations: [filters/factories.py][filters-factories]`::FilterArgumentsFactory` (members 3–12),
[orders/factories.py][orders-factories]`::OrderArgumentsFactory`. Consumers: finalizer phase-2.5
both sides, both `clear_generated_input_namespace` wrappers, [test_factories.py][test-filter-factories]
+ order twin tests + [test_composition.py][test-composition]. Challenges above (1 definition per
change; family attrs are declarations). Migration: none (already compose by inheritance + hooks).
Distinct behavior: the filter `_build_input_triples` operator-bag splice vs the order bare return
(R1); per-family cache/registry namespaces (sharing them would cross-contaminate builds — the
`__init_subclass__` guard exists precisely to forbid it). Proof: static-reviewed (subclass bodies
are attrs + one hook each; no walk/collision/cache spelling in either). Gate: none owed here
(zero-edit file item; family-item gate belongs to the family item). Freshness: target `366e0490`,
twin `4f35b66b`, owner `ee31d360`, finalizer `77fd9a2d`, HEAD `9031cb3d`.

**F-2 `dynamic-set-class-getter` (NEW FAMILY, for Worker 0 index).** Contract: the deferred
auto-set surface builds a synthetic set class from a `Meta` dict through one normalize → key →
`type(...)` skeleton over a family-owned cache, parameterized by base class, reserved keys, name
suffix, synonym alias, and fields/exclude gate. Owner:
[utils/inputs.py][utils-inputs]`::make_dynamic_set_getter` (+ `normalize_set_meta_for_factory`,
`make_set_meta_cache_key`, `create_dynamic_set_class`). Declarations: `_get_filterset_class` /
`get_filterset_class` + `_dynamic_filterset_cache` (members 1, 13, 14) and the order-twin triple.
Consumers: none in source (both surfaces deferred, build-and-test-only — verified: no
`get_filterset_class` / `get_orderset_class` caller outside tests); oracles: Layer-6 arms of
[test_factories.py][test-filter-factories] + order twin tests. Challenges above (1 definition per
change). Migration: none (already single-sited; the hoist the prior cycle deferred has landed —
both factories consume the owner by name, verified fresh). Distinct behavior: filter-only
`require_fields_or_exclude=True` + `FILTERSET_FIELDS_ALIAS` vs order defaults (R6); disjoint
cache dicts by design (R3). Proof: static-reviewed (both call sites are one `make_dynamic_set_getter`
invocation each with family params). Gate: none owed here (family item owns it). Freshness: target
`366e0490`, twin `4f35b66b`, owner `ee31d360`, HEAD `9031cb3d`.

**F-3 `set-type-naming` (REUSE, index: open).** Owner:
[sets_mixins.py][sets-mixins]`::ClassBasedTypeNameMixin`. Target role: pure consumer — the base
`__init__` derives `input_type_name` via `set_input_type_name`, and `_build_input_triples`
receives `type_name` from the base walk; no naming rule defined here (AST-verified: no
`type_name_for` definition). Nothing to consolidate. Freshness: target `366e0490`, owner
`ad8987ea`, HEAD `9031cb3d`.

**F-4 `related-set-target-lifecycle` (REUSE, index: open).** Owner:
[sets_mixins.py][sets-mixins]`::RelatedSetTargetMixin`. Target role: seam-naming consumer —
`_related_attr = "related_filters"` / `_related_target_attr = "filterset"` parameterize the
owner-walked BFS adjacency (`related_map` / target read live in the base `_ensure_built`); the
`RelatedFilter` adapter itself lives in [filters/base.py][filters-base]. No consolidation in a
file item; adapters stay per family (principle 5). Freshness: target `366e0490`, owner
`ad8987ea`, mirror [orders/factories.py][orders-factories] `4f35b66b`, HEAD `9031cb3d`.

**F-5 `subsystem-clear-lifecycle` (REUSE, index: open).** Owner: `registry.py` bus
(`register_subsystem_clear` / `iter_subsystem_clears`). Target role: state contributor —
`input_object_types` + `_type_filterset_registry` (members 4–5) are reset through the family
wrapper [filters/inputs.py][filters-inputs]`::clear_filter_input_namespace` over the owner
[utils/inputs.py][utils-inputs]`::clear_generated_input_namespace` (verified: no local
`register_subsystem_clear`, no local clear body). The Layer-6 `_dynamic_filterset_cache` carries
NO hook by documented intent (keys embed model identity; trigger recorded in the comment: "Add a
clear hook here only if a consumer reload path ever demands it"), mirrored on the order side —
not an omission defect (axis 6: no contract source demands it). Freshness: target `366e0490`,
inputs wrapper `82b52d97`, owner `ee31d360`, registry `9cc8bb55`, HEAD `9031cb3d`.

**F-6 checked non-memberships — do not inherit.** `lazy-related-class-resolution`: target never
calls `resolve_lazy_class` (expansion lives in [filters/sets.py][filters-sets]); `queryset-seed-and-model-read`:
no `model_for`/`base_queryset` here; `one-sync-boundary`: no import, no call, no `async def`/`await`.
Zero definitions, zero calls — correctly absent from the index for this file.

**L-a `reserved-factory-keys literal` (file-local).** `_RESERVED_FACTORY_KEYS =
frozenset({"filterset_base_class"})` names this family's stripped factory kwarg. Challenge: posit
the owner getter gaining a named param → both family literals move (2 declarations, R2) while the
stripping rule stays single-sited in `normalize_set_meta_for_factory` (1 definition). Values are
family vocabulary tied to each side's `explicit_param`; unifying them would couple the families
over nothing. No second package definition of this literal (verified: sole `filterset_base_class`
source hit package-wide is this line).

**Rejections R1–R6** (difference + trigger + home): R1 operator-bag hook merge (filter splices
logic fields, order returns bare triples — different contracts per spec-028 Decision 8; trigger:
orders gaining an operator bag; home: [utils/inputs.py][utils-inputs]`::GeneratedInputArgumentsFactory._build_input_triples`
docstring). R2 reserved-key literal unification (per-family vocabulary tied to `explicit_param`;
trigger: getter params unified across families; home: member 2 comment). R3 shared Layer-6 cache
dict (disjointness is the rule — a filter clear must not drop order classes; trigger: a unified
clear hook that partitions by family; home: member 1 comment, mirrored order-side). R4 cookbook
twins (`filter_arguments_factory.py` / `filterset_factories.py` — external repos,
out-of-population sources/oracles; trigger: none). R5 twin module-docstring prose (explanation,
out of population). R6 `require_fields_or_exclude` asymmetry (django-filter metaclass assertion
vs order plain-metaclass lifecycle, documented at `create_dynamic_set_class`; trigger: order
metaclass gaining a fields/exclude assertion; home: that docstring).

## Defects

None. One probed edge released without a defect: the Layer-6 caches' missing clear hook is
documented intent on both sides with a recorded trigger, unreachable from any source consumer
(both surfaces deferred), and covered by direct clearing in the package test fixture — no
wire-reachable contract broken, no contract source establishing a stricter rule.

## Pending execution

None. Every proof is static-reviewed (body inspection, population greps, AST walk). Inspection
suffices because the target decides no ordering, transactional, or async behavior: the BFS FIFO
order and collision raise live in the owner, the cache-key canonicalization lives in the owner,
and `type(...)` construction is pure. No execution-deferred entry exists.

## Judgment

Zero-edit result: matrix discharged against the real surface (orders twin read first whole;
Meta/lookup-grammar/async absences verified, not assumed), 14/14 members assigned (2 new families
named, 3 reused as consumer, 3 non-memberships correctly withheld, remainder file-local or
rejected with difference + trigger + home), challenges recorded with definition counts, no defect
with a wire-reachable contract found. Both genuine cross-file rules (BFS substrate, dynamic-set
getter) already compose by name through [utils/inputs.py][utils-inputs] — verified fresh, not
inherited from prior-cycle prose.

## Implementation (Worker 1)

No production edits (file item; target CLEAN throughout — working blob `366e0490` == HEAD blob,
absent from `git status --short`). No new tracked files besides this artifact (untracked until
Worker 0 records it). Item-scoped diff vs `ITEM_BASELINE`
`9ae142d4cbd58c5e088df7ef9bfa67e5c277668e` for
`django_strawberry_framework/filters/factories.py` + this artifact path: empty on the target;
artifact is new (`??`). Concurrent dirt explicitly untouched: working-tree
`django_strawberry_framework/connection.py` hunk (working `3c4d5dcb`, fingerprinted as-read),
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` (+31),
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` — none opened, none attributed here.
No pytest run (not authorized by the entry command; no edits to verify). No ruff run (no edits).
No scratch files created (all probes read-only inline: content search, AST walk, blob hashes); no
`docs/dry/temp-tests/` directory was needed.

## Independent verification (Worker 2)

Own trace (recorded from direct reads before reconciling with `## Findings` below;
target + `orders/factories.py` twin read whole FIRST, then owners/consumers/tests).

Target `django_strawberry_framework/filters/factories.py` (177 lines, working blob
`366e0490c83fcb70dbdf4a9bfe74b882a62cf716` == `HEAD` blob; absent from
`git status --short`, CLEAN) owns exactly two declaration groups and no machinery:

- Layer-5 BFS declaration: `FilterArgumentsFactory`, a direct subclass of
  `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`
  carrying 8 hook attrs (`input_object_types`, `_type_filterset_registry`,
  `_collision_registry_attr`, `_factory_label`, `_family_label`, `_rename_noun`,
  `_related_attr`, `_related_target_attr`) plus one `_build_input_triples` override
  that splices `django_strawberry_framework/filters/inputs.py::_build_input_fields`
  with `django_strawberry_framework/filters/inputs.py::_build_logic_fields`. No
  queue, no seen-gate, no collision raise, no cache write, no subclass-guard body
  lives here; all of that is in the base (`_ensure_built`, `_build_class_type`,
  `__init_subclass__`, `_collision_registry`, `arguments`). Owner I would choose:
  `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`.
  Agrees with W1 F-1 owner.
- Layer-6 dynamic-set declaration: `_dynamic_filterset_cache` (family-owned dict),
  `_RESERVED_FACTORY_KEYS` (`{"filterset_base_class"}`), `_get_filterset_class` /
  `get_filterset_class` as a one-call construction over
  `django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter` with
  `set_base_class=FilterSet`, `auto_name_suffix="AutoFilter"`,
  `fields_alias=FILTERSET_FIELDS_ALIAS`, `require_fields_or_exclude=True`. No
  normalize, key, hash, or `type(...)` body lives here; all of that is
  `normalize_set_meta_for_factory` / `make_set_meta_cache_key` /
  `create_dynamic_set_class` / `make_dynamic_set_getter` in
  `django_strawberry_framework/utils/inputs.py`. Owner I would choose:
  `django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`
  (+ helpers). Agrees with W1 F-2 owner.
- Naming/lifecycle/clear consumers: type names arrive via the base `__init__`
  through `set_input_type_name` to
  `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`
  (consumer, F-3 — agree); related adjacency (`related_filters`/`filterset`)
  parameterizes the owner-walked BFS with the adapter in
  `django_strawberry_framework/filters/base.py::RelatedFilter` (consumer, F-4 —
  agree); `input_object_types` + `_type_filterset_registry` reset through
  `django_strawberry_framework/filters/inputs.py::clear_filter_input_namespace`
  over `django_strawberry_framework/utils/inputs.py::clear_generated_input_namespace`
  on the `registry.py` bus (state contributor, F-5 — agree). Reserved keys are
  per-family vocabulary for each side's `explicit_param` (file-local L-a —
  agree). Layer-6 dicts on both sides carry no clear hook by documented intent
  (keys embed model identity; trigger recorded in comments) — agree no defect
  (axis 6: no spec, glossary, owner-prose, or oracle source establishes a
  clear-hook rule for the deferred unconsumed surface).

Definition counts per posited change (authoritative definitions only): BFS
discipline change (FIFO/gate/collision/guard) 1 in the base, 0 here; ninth hook
attr 1 base declaration + 2 family declarations (declarations, not definitions);
cache-key/`frozenset`-exclude/synonym changes 1 in
`make_set_meta_cache_key`/`_hashable_meta_value`/`resolve_set_meta_fields`, 0
here; dynamic-build gate change 1 in `create_dynamic_set_class`, 0 here; getter
param change 1 in `make_dynamic_set_getter`/`normalize_set_meta_for_factory` + 2
reserved-key declarations; new logic operator 1 in `LOGIC_OPERATORS`, 0 here;
rename-every-input 1 in `type_name_for`, 0 here. All agree with W1 challenges.

Enumeration (own AST count): top-level binds other than docstring/imports =
`_dynamic_filterset_cache`, `_RESERVED_FACTORY_KEYS`, `FilterArgumentsFactory`,
`_get_filterset_class`, `get_filterset_class` (5); class members other than the
docstring = `input_object_types`, `_type_filterset_registry`,
`_collision_registry_attr`, `_factory_label`, `_family_label`, `_rename_noun`,
`_related_attr`, `_related_target_attr`, `_build_input_triples` (9). Total 14.
Module docstring (projection) + 5 imports (references) excluded with reason.
W1's 14-member table assigns every one (members 1–14: 5 top-level + 9 class
members with the class itself as member 3). Counting the container plus its
members is the instrument as stated, so no double-count. 14/14 agree; no
orphan, no missing member. Static probe claims re-checked: no
`register_subsystem_clear`, `__all__`, `resolve_lazy_class`, `model_for`,
`base_queryset`, `run_in_one_sync_boundary`, `promote_set_meta_fields`,
`make_set_meta_cache_key` definitions in the target. Factory absent from
`filters/__init__.py` `__all__`; order twin absent from `orders/__init__.py`
`__all__` — export parity holds, both via submodule only.

Matrix vs real surface (orders twin read FIRST whole, 155 lines): axis 1
searched — twin comparison above; one semantic divergence (operator bag,
spec-028 Decision 8) plus disjoint caches/registries/suffixes/reserved
literals and filter-only `require_fields_or_exclude`/`fields_alias`
(R1/R2/R3/R6) all verified in both bodies. Axis 2 inapplicable with reason —
zero `async def`/`await` in target, sync finalize-time construction, no
queryset-boundary symbol defined or called; base likewise sync-only. Axis 3
searched — alias constant, type names, cache keys, synonym rule, Meta
write-back all composed by name, none re-derived. Axis 4 searched — explicit
vs dynamic arms are one owner getter; normalize vs key halves share one
family in the owner. Axis 5 searched — oracles assert literal behavior
(`input_object_types`/`_type_filterset_registry` addressability is the
spec-027 Decision 9 contract, not rot); no test or doc restates a package
rule as a second definition; cookbook ports out of population (R4); twin
docstrings are explanation (R5). Axis 6 enumerated — filter-only gate/alias
documented at the owner; Layer-6 no-clear-hook documented intent on both
sides with trigger, unreachable from any source consumer, fixture clears the
dict directly; no contract source demands more, so no defect. Matrix
discharged; no unsearched axis, no found consolidation excusing another axis.

Roles + oracles: F-1/F-2 declarations vs owner definitions confirmed by body
inspection; F-3/F-4/F-5 pure-consumer/contributor roles confirmed (no local
`type_name_for`, no adapter, no clear body). Oracles
(`tests/filters/test_factories.py`, `tests/orders/test_composition.py` et al.)
expect literal names/wordings/behaviors and address the Decision-9 caches
directly per the specified contract; none derives expectations from the owner
it checks. No oracle rewritten.

Equivalence (principle 8): zero production edits, so no behavior to preserve
across a change. The two genuine cross-file rules already compose by name
(subclass hooks; one getter invocation each) — verified fresh, not inherited.

Zero-edit + baselines: `git diff deb98aef484487692fd87d3074a599f6ec1f0a6b --
django_strawberry_framework/filters/factories.py` is byte-empty (re-ran
myself, exit 0). `git diff 9ae142d4cbd58c5e088df7ef9bfa67e5c277668e -- <same>`
is likewise empty. `9ae142d4` resolves via `git cat-file -t` to a `commit`
object: `WIP on t3code/1cc21548: 9031cb3d ...` dated 2026-09-18 16:36:15 -0400,
i.e. W1's own fresh `git stash create` ITEM_BASELINE, not a typo and not a
moved target. The dispatch baseline `deb98aef` is the same shape (`WIP on
t3code/1cc21548: 9031cb3d ...`, 16:35:43 -0400); both stash commits share
parent `9031cb3d`, identical 6-file stat, and an empty diff between them. Both
baselines are equivalent for this item; the target moved under neither.

New families ruling: F-1 `set-arguments-factory-bfs` ENDORSED as its own
family — BFS walk/collision/cache/guard with per-family hook parameterization
is a distinct contract from the Layer-6 normalize/key/`type(...)` skeleton;
folding F-1 into F-2 would couple unrelated lifecycles over a shared owner
file, and folding either into F-3/F-4/F-5 would merge naming/adjacency/clear
concerns with construction. F-2 `dynamic-set-class-getter` ENDORSED as its
own family — deferred auto-set surface with its own variation axes (base,
suffix, reserved keys, alias, fields/exclude gate) and disjoint-cache rule;
folding into F-1 would hide the build-vs-declare split, and the order twin
confirms the family spans both flavors. Owners (`GeneratedInputArgumentsFactory`,
`make_dynamic_set_getter` both in `utils/inputs.py`) verified by body
location, not prose inheritance.

Rejections R1–R6: each carries a concrete contract difference + trigger +
home; homes verified to exist (R1 base `_build_input_triples` docstring; R2
member-2 comment; R3 member-1 comment mirrored order-side; R4 external repos,
trigger none; R5 twin docstring prose as explanation; R6
`create_dynamic_set_class` docstring split). Fingerprints re-hashed myself:
target `366e0490`, twin `4f35b66b`, owner `ee31d360`, finalizer `77fd9a2d`,
inputs wrapper `82b52d97`, registry `9cc8bb55`, sets-mixins `ad8987ea`, HEAD
`9031cb3d` — all match. Gates: none owed in this zero-edit file item (family
item owns any future gate); consistent with verified file-item precedent, so
no negative control is outstanding here. `## Pending execution: None` is
adequate: every proof is static-reviewed and the target decides no ordering,
transactional, or async behavior (FIFO/collision in the owner, key
canonicalization in the owner, `type(...)` pure); no mutating probe was owed
and none was run. Coupling: nothing must land together (no consolidation, no
shared slot); correctly unmarked.

AGENTS.md prose check: no process provenance (the only pytest/ruff sentence
states no run, which is the required record for zero edits); citations are
`path::Symbol` with no raw `path:NN`; links are reference-style under the
existing 10-group `LINK DEFINITIONS` block (no new link targets added by this
section); no tests owed for a zero-edit file item; concurrent dirt untouched
(only this untracked artifact edited; no commit).

Defects (Worker 2): none. The Layer-6 no-clear-hook edge was probed and
released on the same grounds as W1: documented intent both sides, trigger
recorded, no source consumer, no wire-reachable contract, fixture clears
directly.

Judgment (Worker 2): `verified`. Zero-edit file item; 14/14 members assigned;
both new families endorsed with the index/Families rows below; no defect; no
pending execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-composition]: ../../tests/orders/test_composition.py
[test-filter-factories]: ../../tests/filters/test_factories.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
