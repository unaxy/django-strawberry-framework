# DRY review: `django_strawberry_framework/orders/factories.py`

Status: verified
Run: 0.0.15 2026-09-22-5

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is assigned to an adopted family for Worker 0 to index, recorded
file-local with its proving challenge, routed to a verified holding family,
or is a rejection carrying its contract difference + trigger. Zero production
edits; zero tracked files changed.

## System trace

Target owns the order Layer-5/6 declarations
(`django_strawberry_framework/orders/factories.py`, 155 lines, blob
`4f35b66b`; worktree == HEAD, target CLEAN): the `OrderArgumentsFactory`
BFS subclass declaration (8 class attrs + the bare-triples
`_build_input_triples` hook), the family-owned Layer-6 dynamic-OrderSet
cache dict + reserved-keys literal, and the thin `get_orderset_class`
public delegate over the shared `make_dynamic_set_getter` product. No BFS
walk, no collision check, no cache-key hashing, no `type(...)` skeleton, no
namespace-clear body, no name derivation lives here — all of that is owned
by [utils-inputs][utils-inputs] and [sets-mixins][sets-mixins].

Traced end to end, filter twin FIRST (whole
[filters-factories][filters-factories], 177 lines, blob `366e0490`): the two
factories are behavior-plus-contract twins — same base class, same 8-attr
parameterization shape, same Layer-6 getter construction, deliberately
disjoint caches/registries/suffixes, and exactly one semantic divergence
(the operator bag, spec-028 Decision 8). Owner bodies in
[utils-inputs][utils-inputs] (`GeneratedInputArgumentsFactory`,
`make_dynamic_set_getter`, `make_set_meta_cache_key`,
`normalize_set_meta_for_factory`, `create_dynamic_set_class`,
`resolve_set_meta_fields`, `promote_set_meta_fields`,
`read_set_meta_fields`, `clear_generated_input_namespace`,
`build_strawberry_input_class`, `set_input_type_name`,
`emit_set_input_field_triples`), the triples builder in
[orders-inputs][orders-inputs] (`_build_input_fields`, `build_input_class`
alias, `_materialized_names`, `clear_order_input_namespace`), the filter
alias production calls in [filters-inputs][filters-inputs], the metaclass
write-backs in [orders-sets][orders-sets] and [filters-sets][filters-sets],
the phase-2.5 consumer in [finalizer][finalizer] (`_bind_ordersets` reading
`OrderArgumentsFactory(...).arguments`), the non-consumer in
[connection][connection] (`Meta.orderset_class` sidecar read directly, never
routed here), the export parity in [orders-init][orders-init] and
[filters-init][filters-init] (factory via submodule only, both sides), the
naming owner in [sets-mixins][sets-mixins]
(`ClassBasedTypeNameMixin.type_name_for`), the related-target seam in
[orders-base][orders-base] (`RelatedOrder`, verified file-local row
`orders-related-target-adapter-declarations`), oracles in
[test-order-factories][test-order-factories] (666 lines),
[test-composition][test-composition] (both factories' ledgers asserted
together), and [test-utils-inputs][test-utils-inputs] (twin-closure gate),
contract sources spec-028 (Decisions 3/8/9/12) plus the
[spec-028-rationale][spec-028-rationale] (B2/M1/H4, Layer-5 revision notes),
and the verified holding/trigger artifacts
[dry-filters-factories][dry-filters-factories] (F-1/F-2/R1-R6 as orientation
triggers, re-derived fresh below), [dry-orders-base][dry-orders-base] (seam
convention), [dry-orders-init][dry-orders-init] (shape convention),
[dry-mutid][dry-mutid] (R2 trigger, checked fresh), and
[dry-clear-lifecycle][dry-clear-lifecycle] (member-6 census).

Dirt note (all hunt-dirtied paths read via `git show HEAD:<path>`, never
touched): [utils-inputs][utils-inputs] (`47b2af21…`, hardening campaign
inside the judged owner bodies — `except BaseException` guard arms,
`__class__`/`__eq__` interrogation guards, `__qualname__`→`_safe_*` label
swaps; 37 added hardening-marker lines, 46 removed lines all of those two
shapes; no definition moved, no signature changed, no count affected),
[orders-inputs][orders-inputs] (`889b5971…`, import-block +
`normalize_input_value` hunks — outside every judged region),
[orders-sets][orders-sets] (`f09d9983…`, label swaps + one `__eq__`-guard arm
whose `read_set_meta_fields` call line itself is unchanged context),
[sets-mixins][sets-mixins] (`48b8ca20…`, `isinstance` guards +
`_bind_related_declaration` — all below the judged `type_name_for`
region), [finalizer][finalizer] (`35ff5286…`, `_field_surface_names` hunk —
outside the judged subpass passage), [connection][connection] (`9c5b8724…`,
import + `_consume_*` hunks — outside the judged sidecar reads),
[filters-inputs][filters-inputs] (`06797dc7…`, one `_normalize_range_value`
hunk — outside both judged alias call sites), [filters-sets][filters-sets]
(`c1a0f1b2…`, `FilterSet`-body hunks — outside the judged write-back call),
[registry][registry] (`612bea87…`, `TypeRegistry`-body hunk — the bus
contract is cited by reference only), and
[test-utils-inputs][test-utils-inputs] (`049cb40c…`, import hunk + 358
appended lines — outside the judged twin-gate test). Every judgment below
is against HEAD bytes; the dirt changes no count (details per finding).
The target itself is CLEAN: worktree
`4f35b66b06fe67e800ac43dabe8a1733b221168d` equals
`HEAD:django_strawberry_framework/orders/factories.py`.

Excluded with reason: every other indexed family whose files-covered list
was scanned for this path — only `subsystem-clear-lifecycle` covers this
file's caches (member 6, `orders.input_namespace`; routed below as a
convergence, no new row). `one-sync-boundary`, `queryset-seed-and-model-read`,
`sync-boundary-recourse-wording`, and `field-value-coercion` were judged on
their mechanisms against this target's REAL surface and found to have none
here (negatives verified: zero `async`/`await`/`sync_to_async`/`queryset`/
`model_for`/`base_queryset`/`coerce`/`clear`/`recourse` tokens in the
target). No index row named `set-arguments-factory-bfs`,
`dynamic-set-class-getter`, `set-type-naming`, or
`related-set-target-lifecycle` exists in the current plan; the verified
filters-twin artifact's F-1–F-4 treatment was orientation only (prior
verdicts are triggers to check), and each mechanism is re-derived fresh
below on HEAD evidence — F-1/F-2 adopted as families with fresh boundaries,
naming as no-surface (C10), the related seam as F-1 hook-param declarations
with a cross-reference to the verified orders/base F2 row.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Twin read FIRST whole
([filters-factories][filters-factories], 177 lines, CLEAN `366e0490`).
Shared substrate: direct subclasses of
[utils-inputs][utils-inputs]`::GeneratedInputArgumentsFactory`, 8 hook
attrs each, one `_build_input_triples` override each, one
`make_dynamic_set_getter` construction each — with one genuine semantic
divergence (the filter hook splices `_build_logic_fields`, the order hook
returns bare triples per spec-028 Decision 8; rejection R-bag) and
deliberately disjoint caches (`_dynamic_filterset_cache` /
`_dynamic_orderset_cache`), registries, suffixes (`AutoFilter` /
`AutoOrder`), and reserved literals (rejections R-keys, R-cache), plus the
filter-only `require_fields_or_exclude=True` + `fields_alias` vs the order
defaults (rejection R-gate). Disjointness is the documented rule on both
sides ("a filter clear cannot drop an order class (and the reverse)").
One asymmetry found fresh (D1 evidence, not a second definition): the
filter `build_input_class` alias carries TWO production call sites
(range-input + operator-bag builders inside
[filters-inputs][filters-inputs]), while the order alias has ZERO
production call sites (tests only) — orders builds no per-field bag/range
classes (Decisions 5/8), so its alias is addressability-only, pinned
`is`-identical to the owner by oracle.

**2. Sync/async twins.** Inapplicable with reason: zero `async def`, zero
`await`, zero `sync_to_async` in the target (verified by token sweep);
the BFS build + `type(...)` construction are pure sync construction at
finalize time executing inside no queryset boundary (verified: no
`base_queryset`, no `run_in_one_sync_boundary`, no `model_for`, no
`queryset` token defined or called in the target). The base factory
likewise carries no async surface. `one-sync-boundary` names the
`apply_*` path, never this file.

**3. Derived rather than repeated knowledge.** Searched. Input type names
arrive via the base `__init__` through `set_input_type_name` →
`ClassBasedTypeNameMixin.type_name_for` (0 definitions here — C10);
cache keys via `make_set_meta_cache_key` (owner F-2); the Meta synonym
rule via `resolve_set_meta_fields` (owner); class-Meta write-back via
`promote_set_meta_fields` (owner, shared with both metaclasses —
verified call sites [orders-sets][orders-sets] without alias and
[filters-sets][filters-sets] with `FILTERSET_FIELDS_ALIAS`);
class-Meta expansion reads the same fingerprint through
`read_set_meta_fields` (verified call in [orders-sets][orders-sets];
the concurrent hunk there leaves the call line intact). The construction
call is the owner's `build_strawberry_input_class`, reached module-locally
by the base — the target's docstring attribution of that call to the
orders alias is D1. No local re-derivation of any shared fact.

**4. Inverse / round-trip pairs.** Searched. `get_orderset_class`
explicit-passthrough vs dynamic-build halves are two arms of ONE owner
getter (`make_dynamic_set_getter`'s `get_set_class`), not a pair;
normalize (`normalize_set_meta_for_factory`) vs key
(`make_set_meta_cache_key`) halves both live in [utils-inputs][utils-inputs]
under one family. No local pair, no second half to twin.

**5. Contracts restated in another medium.** Searched. Four media carry
this file's contracts: production code (declarations here, machinery at
the owners); authoritative contract sources (spec-028 Decisions 3/8/9/12
for the subclass-plus-shared-base split, the no-operator-bag posture,
the Decision-9 cache names + clear lifecycle + ledger/registry split,
and the deferred Layer-6 non-goal); independent oracles
([test-order-factories][test-order-factories]: BFS reachability,
cycle/diamond/dedup, collision-refusal wording naming
`OrderArgumentsFactory` / `OrderSet`, empty-guard wording, cache-key
equivalences incl. set/exclude-None/reserved-keys arms, fields-less-Meta
acceptance, dynamic-build round-trip; [test-composition][test-composition]:
both factories' `input_object_types` asserted in one test;
[test-utils-inputs][test-utils-inputs]: twin-closure `__code__`-identity +
disjoint-caches + no-private-hashing-aliases gate — all spelling literals
and driving behavior, never reading the owners to compute expectations);
projections (module/class/docstring prose, spec code blocks, rationale
passages). Per spec-028 Decision 9 the oracles address the
`input_object_types` / `_type_orderset_registry` caches directly — that
addressability IS the specified contract, not oracle-rot. Cookbook twins
(`order_arguments_factory.py` LIFO port) are out-of-population sources.
No test or doc restates a package rule as an independently maintained
definition.

**6. Enforcement by omission.** Enumerated. `require_fields_or_exclude`
and `fields_alias` are absent on the order side by documented split
([utils-inputs][utils-inputs]`::create_dynamic_set_class` records the
django-filter metaclass assertion vs the order plain-metaclass lifecycle;
rejection R-gate; the fields-less acceptance is pinned by oracle).
Neither Layer-6 cache dict carries a clear hook — the documented
lifecycle on both sides (keys embed the model identity via the hashed
model first element, test-isolation nicety only; the package test fixture
clears `_dynamic_orderset_cache` directly). No contract source (spec,
glossary anchor, owner prose, oracle) establishes a clear-hook rule for
the unconsumed deferred surface (spec-028 Decision 12: no package path
calls either symbol — verified by census), so no defect is filed —
correct per axis 6. The factory stays out of the leaf `__all__` by
spec-028 Decision 2 (verified absent on both sides; the orders leaf
documents the exclusion). No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **11 top-level statements** — plus every member of the
`OrderArgumentsFactory` class body — **10 members** (docstring + 9 named).
**14 named rule-bearing members** in total (same 14-shape as the verified
filter twin). Every member lands below; every challenge in `### Challenges`
ends in a family row, a file-local row, a rejection, or a verified
no-surface routing.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (Layer-5/6 prose + twin + Decision pointers) | (none) | prose projection, F-1/F-2 + D1 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from typing import Any, ClassVar` | 2 names (annotations) | F-1/F-2 signatures |
| 4 | `from ..utils.inputs import (...)` | 2 names (machinery) | F-1/F-2 consumer rows |
| 5 | `from .inputs import _build_input_fields` | 1 name | F-1 hook delegate |
| 6 | `from .sets import OrderSet` | 1 name | F-2 base (annotation + construction base) |
| 7 | `_dynamic_orderset_cache` | 1 name | F-2 |
| 8 | `_RESERVED_FACTORY_KEYS` | 1 name | L-a + R-keys |
| 9 | `class OrderArgumentsFactory(...)` | 1 name + 10 members | F-1 (+ F-5c, seam note, R-bag) |
| 10 | `_get_orderset_class = make_dynamic_set_getter(...)` | 1 name | F-2 |
| 11 | `def get_orderset_class` | 1 name | F-2 |

| # | `OrderArgumentsFactory` member | Binds | Home |
|---|---|---|---|
| 9.1 | class docstring (substrate + cache + wording prose) | (none) | prose projection, F-1 |
| 9.2 | `input_object_types` | family cache | F-1 / F-5c |
| 9.3 | `_type_orderset_registry` | family collision registry | F-1 / F-5c |
| 9.4 | `_collision_registry_attr` | hook param | F-1 |
| 9.5 | `_factory_label` | hook param | F-1 |
| 9.6 | `_family_label` | hook param | F-1 |
| 9.7 | `_rename_noun` | hook param | F-1 |
| 9.8 | `_related_attr` | hook param (seam name) | F-1 (+ seam note) |
| 9.9 | `_related_target_attr` | hook param (seam name) | F-1 (+ seam note) |
| 9.10 | `def _build_input_triples` | 1 name | F-1 + R-bag |

Rules: R1 BFS-substrate declarations (statements 4–5, 9); R2
dynamic-set-getter declarations (statements 4, 6–8, 10–11); R3
clear-bus membership (9.2–9.3); R4 related-seam hook names (9.8–9.9).
Two families adopted for Worker 0 (F-1, F-2 — names adopted from the
verified twin artifact, boundaries re-derived fresh on HEAD evidence),
one file-local row (L-a), one verified-family convergence (F-5c, no new
row), five rejections (R-bag/R-keys/R-cache/R-gate/R-mutid), two
no-surface checks (C10 naming, cookbook out-of-population).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. All bodies judged at HEAD bytes (the worktree dirt sits
inside the owner bodies as additive hardening and changes no count —
the judged walk/collision/key/skeleton shapes are the HEAD bytes).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 BFS substrate | FIFO→LIFO, new seen-gate, new collision rule, subclass-guard reword | **1** ([utils-inputs][utils-inputs]`::GeneratedInputArgumentsFactory`; 0 here — finalizer subpass 4 both sides, both clear fns, both test modules follow by construction) | independent |
| C2 | R1 hook shape | ninth hook attr (collision message needs a new token) | **1** (base declares + reads it) + 2 family declarations (this file, filter twin — declarations, not definitions, per principle 1) | independent — proves declaration shape |
| C3 | R1 empty guard | reword/rescope the zero-field rejection | **1** (base `_build_class_type`; 0 here — orders-only reachable since the filter hook always appends the operator bag) | independent |
| C4 | R1 hook merge | give orders an operator bag (unify the two hooks) | separation stands (R-bag: this hook + [orders-inputs][orders-inputs] would move; the filter hook untouched — opposite files under opposite changes today) | rejected-merge — proves adapters |
| C5 | R2 key shape | new unordered container, new Meta key | **1** (`make_set_meta_cache_key` / `_hashable_meta_value`; 0 here) | independent |
| C6 | R2 synonym | orders gains a `fields` synonym | **1** (`resolve_set_meta_fields`) + 1 declaration flip (`fields_alias=None`→value here); trigger-checked: no synonym exists on orders | independent |
| C7 | R2 build gate | order gains `require_fields_or_exclude` (or gate reword) | **1** (`create_dynamic_set_class`) + declaration flip here (R-gate) | independent — proves declaration |
| C8 | R2 getter signature | owner gains a named construction param | **1** (`make_dynamic_set_getter` / `normalize_set_meta_for_factory`) + 2 reserved-key declarations (each names its family's explicit-param sibling — R-keys) | independent |
| C9 | R2 generated name | change the `<Model>Auto<Order>` rule | **1** (`create_dynamic_set_class` f-string); the suffix here is a declaration (0 definitions) | independent |
| C10 | naming check | change the `Foo` → `FooOrderInputType` derivation | **0 here** (owned at [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin.type_name_for` via `set_input_type_name`; the base is the consumer, this file not even that) | no surface — do not inherit |
| C11 | identity merge | shape-derived (`<Model>Input`) naming for set inputs | separation stands (R-mutid: class-derived naming + same-name-collide is the opposite rule; trigger checked fresh) | rejected-merge — proves grammars |
| C12 | R3 clear contract | change the `register_subsystem_clear` contract | **1** ([registry][registry] bus; 0 here — this file holds no registration, only the reset state) | independent |

No executable proof was run: the target is declarations + one delegating
hook + one delegating function whose every behavior is pinned by the read
oracles in [test-order-factories][test-order-factories] plus the
composition and twin-closure oracles, and every census above is a
byte-level `git grep` over HEAD blobs or an `ast.parse` enumeration — all
read-only, none mutating, none capable of distinguishing anything the
cited oracles do not already pin. The entry command authorizes a focused
`--no-cov` run only where it could settle a judgment; every judgment here
is static-decidable (declaration shapes, census counts, body reads), so
none was run. No `docs/dry/temp-tests/` scratch was created. All claims
below are therefore `static-reviewed`; there is no `execution-deferred`
proof.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site (adopted families
carry fresh boundaries for the family item to work from).

### F-1 — `set-arguments-factory-bfs` (ADOPTED FAMILY, for Worker 0 index + Families)

- **Contract + variation.** Every reachable set-family root BFS-builds
  its Strawberry input classes through one walk + per-class collision
  check + idempotent cache + subclass-rejection guard, parameterized per
  family by 8 hook attrs and one `_build_input_triples` override.
  Legitimate variation: the per-family hook values + the hook body only.
- **Sites + roles.** *Definition*:
  [utils-inputs][utils-inputs]`::GeneratedInputArgumentsFactory` (walk,
  collision, cache, `__init_subclass__` guard, `__init__`/`arguments`/
  `_ensure_built`/`_build_class_type` — read in full at HEAD).
  *Declarations*: this file's statement 9 (members 9.2–9.10) and the
  filter-twin class. *Hook delegates*:
  [orders-inputs][orders-inputs]`::_build_input_fields` (bare triples;
  this file's 9.10 returns them as-is) and the filter pair
  (`_build_input_fields` + `_build_logic_fields`). *Consumers*:
  [finalizer][finalizer] phase-2.5 both sides (subpass 4 reads
  `OrderArgumentsFactory(orderset_cls).arguments`), both
  `clear_generated_input_namespace` wrappers. *Oracles*:
  [test-order-factories][test-order-factories] BFS/wording/empty-guard
  arms + [test-composition][test-composition] (both factories'
  `input_object_types` in one test) — independent (literal pins, never
  read the owner). *Projections*: 9.1 docstring, spec-028 Decisions 3/9,
  rationale Layer-5 notes.
- **Challenges.** C1 → 1 (base; 0 here); C2 → 1 base + 2 family
  declarations (not definitions); C3 → 1 (base; orders-only reachable);
  C4 → separation stands (R-bag).
- **Owner + lifetime.** The base (existing owner by responsibility: the
  walk/collision/cache/guard machinery both families' finalizers and
  clears already depend on; the narrowest site every legitimate consumer
  can import). Lifetime: the per-family class-level dicts (9.2–9.3) are
  process-global build caches; validity key = registry generation (reset
  through the F-5c row); published at class creation; mutated by the base
  walk on each build and by the clear wrapper on clear — never removed.
- **Migration.** None (already compose by inheritance + hooks; the family
  item decides gate-only vs consolidation on its own sweep).
- **Distinct behavior.** The order 9.10 bare return vs the filter
  operator-bag splice (R-bag); per-family cache/registry namespaces
  (sharing them would cross-contaminate builds — the
  `__init_subclass__` guard exists precisely to forbid it). Seam note:
  9.8/9.9 name the adjacency the base walk reads (`getattr` on the
  related map and on each entry's target); the adapter itself
  ([orders-base][orders-base]`::RelatedOrder`) is covered by the verified
  file-local row `orders-related-target-adapter-declarations` — no
  `related-set-target-lifecycle` index row exists, and per the run-5
  convention these stay hook-param declarations here, not a new family.
- **Behavioral proof.** `static-reviewed` (subclass body is attrs + one
  delegating hook; no walk/collision/cache spelling in either twin).
  Rejects "the twins duplicate the walk" (C1 proves a discipline change
  touches one definition) and "the hook re-derives triples" (9.10 is one
  call to the named delegate).
- **Structural gate.** None owed here (zero-edit file item; the family
  item owns any future gate). Pre-existing pins the family item
  inherits: the collision-wording oracles (family labels) and the
  Decision-9 cache-addressability oracles.
- **Coupling.** None.
- **Freshness.** Target `4f35b66b06fe67e800ac43dabe8a1733b221168d`
  (worktree == HEAD; CLEAN),
  [filters-factories][filters-factories] `366e0490…` (CLEAN; twin read
  whole), [utils-inputs][utils-inputs] HEAD
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` (worktree `47b2af21…` hunt
  hardening inside the judged base body — label swaps + guard arms; no
  definition moved, no count affected),
  [orders-inputs][orders-inputs] HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (worktree `889b5971…` dirt
  outside the judged delegate),
  [orders-sets][orders-sets] HEAD
  `6044ab1a11c77a42b715f0d0722fe7c9695064bc` (judged `get_fields`
  consumption only), [finalizer][finalizer] HEAD
  `77fd9a2dd229eb9de5f29188c5058035d3606323` (worktree `35ff5286…` dirt
  outside the judged passage), [orders-base][orders-base] HEAD
  `4736fda0228ee723aada11bfe374f81036ac4c30` (seam cross-reference),
  [test-order-factories][test-order-factories]
  `4ec2ec05…` (CLEAN), [test-composition][test-composition] `d0cc8722…`
  (CLEAN), [spec-028][spec-028] `94a3141c…` (CLEAN; Decisions 3/8/9),
  HEAD `5ee86193`. Searched population for a second BFS walk /
  collision / subclass-guard definition: whole package (`_ensure_built`
  / `_build_class_type` / `_collision_registry` defined exactly once,
  at the base; both families inherit). Excluded on strength of body:
  the cookbook `order_arguments_factory.py` (external, out of
  population) and the write-flavor shape caches (different rule —
  `get_or_store_shape_build` spine, see R-mutid).

### F-2 — `dynamic-set-class-getter` (ADOPTED FAMILY, for Worker 0 index + Families)

- **Contract + variation.** The deferred auto-set surface builds a
  synthetic set class from a `Meta` dict through one normalize → key →
  `type(...)` skeleton over a family-owned cache, parameterized by base
  class, reserved keys, name suffix, synonym alias, and fields/exclude
  gate. Legitimate variation: the per-family construction parameters +
  cache identity only.
- **Sites + roles.** *Definitions*:
  [utils-inputs][utils-inputs]`::make_dynamic_set_getter` (+
  `normalize_set_meta_for_factory`, `make_set_meta_cache_key`,
  `create_dynamic_set_class`, `resolve_set_meta_fields` — all read at
  HEAD). *Declarations*: this file's statements 7, 10, 11 and the
  filter-twin triple. *Write-back sharers*: both set metaclasses call
  `promote_set_meta_fields` (verified call sites with/without alias).
  *Consumers*: none in source (both surfaces deferred,
  build-and-test-only — verified: no `get_orderset_class` /
  `get_filterset_class` caller outside tests; [connection][connection]
  reads the sidecars directly). *Oracles*: Layer-6 arms of
  [test-order-factories][test-order-factories] +
  [test-utils-inputs][test-utils-inputs] twin-closure gate
  (`__code__`-identity, disjoint caches, no private hashing aliases —
  independent). *Projections*: statement-1 Layer-6 paragraph, statement
  7/8/11 docstrings, spec-028 Decision 12.
- **Challenges.** C5 → 1 (key fn; 0 here); C6 → 1 (resolve) + 1
  declaration flip; C7 → 1 (create) + declaration flip; C8 → 1
  (getter/normalize) + 2 reserved-key declarations; C9 → 1 (create
  f-string; suffix here is a declaration).
- **Owner + lifetime.** `make_dynamic_set_getter` + helpers (existing
  owners by responsibility: the skeleton Decision 12 mandates stay
  single-sited "rather than being copied the day a caller lands").
  Lifetime: the family cache dicts (statement 7 + twin) are
  process-global, build-and-test-only, with NO clear hook by documented
  intent — keys embed the model identity (hashed model first element),
  so a rebuilt model gets a fresh key rather than a wrong hit; the
  package test fixture clears statement 7 directly.
- **Migration.** None (already single-sited; both factories consume the
  owner by name — verified fresh, not inherited).
- **Distinct behavior.** Filter-only `require_fields_or_exclude=True` +
  `FILTERSET_FIELDS_ALIAS` vs the order defaults (R-gate); disjoint
  cache dicts by design (R-cache); disjoint suffixes and reserved
  literals (declarations).
- **Behavioral proof.** `static-reviewed` (both call sites are one
  `make_dynamic_set_getter` invocation each with family params; both
  delegates are one-line returns). Rejects "the twins duplicate the
  skeleton" (the twin-closure oracle pins `__code__`-identity) and
  "the caches could merge" (R-cache: disjointness is the rule).
- **Structural gate.** None owed here (family item owns it).
  Pre-existing pins the family item inherits: the twin-closure gate
  above (already in tree at HEAD bytes; the worktree dirt on that file
  is import-block + appended tests, outside the gate).
- **Coupling.** None.
- **Freshness.** Target `4f35b66b…` (CLEAN), twin `366e0490…` (CLEAN),
  [utils-inputs][utils-inputs] HEAD `ee31d360…` (worktree `47b2af21…`
  hardening inside the judged normalize/key/create bodies — guarded
  `isinstance` reads + label swaps; no definition moved, no count
  affected), [orders-sets][orders-sets] HEAD `6044ab1a…` (write-back
  call site), [filters-sets][filters-sets] HEAD
  `722e0c77…` (worktree `c1a0f1b2…` dirt outside the judged call site),
  [connection][connection] HEAD
  `4894f90fb2963a44d25b0eabc649c67d04afa587` (worktree `9c5b8724…` dirt
  outside the judged sidecar reads; non-consumer evidence),
  [test-order-factories][test-order-factories] `4ec2ec05…` (CLEAN),
  [test-utils-inputs][test-utils-inputs] HEAD
  `598f14406dbb27f6d7e9246e89827113e79c526f` (gate region clean),
  [spec-028][spec-028] `94a3141c…` (CLEAN; Decision 12), HEAD
  `5ee86193`. Searched population for a second normalize/key/`type(...)`
  skeleton: whole package (each helper defined exactly once, at the
  owner; the write-flavor `type(...)` sites build different shapes —
  see R-mutid).

### F-5c — `subsystem-clear-lifecycle` convergence (verified family; no new row)

Members 9.2–9.3 are reset state on the verified bus family: statement 9
holds no registration (verified: zero `register_subsystem_clear` tokens
in the target) and no clear body — reset rides the
`orders.input_namespace` row
([orders-inputs][orders-inputs]`::clear_order_input_namespace` over
[utils-inputs][utils-inputs]`::clear_generated_input_namespace`, which
addresses 9.3 through the `collision_registry_attr` string + 9.2
directly). The verified family census (member 6) already covers the
factory caches as reset state; this artifact records the contribution.
Challenge C12 → 1 (the bus; 0 here). The Layer-6 statement 7 carries NO
hook by documented intent on both sides (keys embed model identity;
fixture clears directly; no source consumer) — not an omission defect
(axis 6: no contract source demands it). No new index row owed.

### L-a — `orders-factory-reserved-keys` (file-local)

`_RESERVED_FACTORY_KEYS = frozenset({"orderset_base_class"})` (statement
8) names this family's stripped factory kwarg. Challenge C8: posit the
owner getter gaining a named param → both family literals move (2
declarations, R-keys) while the stripping rule stays single-sited in
`normalize_set_meta_for_factory` (1 definition). Values are family
vocabulary tied to each side's `explicit_param`
(`"orderset_class"`/`"filterset_class"`); unifying them would couple the
families over nothing. No second package definition of this literal
(verified: sole `orderset_base_class` source hit package-wide is
statement 8; the remaining hits are oracles spelling the kwarg).
Freshness: target `4f35b66b…` (CLEAN), twin literal `366e0490…` (CLEAN),
owner HEAD `ee31d360…` (dirt as F-2).

### R-bag — order bare hook vs filter operator-bag hook (rejection; CONVERGE filters R1)

Considered: merge 9.10 with the filter `_build_input_triples` into one
shared hook. Contract difference here: the filter hook splices the
`and_`/`or_`/`not_` operator bag (`_build_logic_fields`), the order hook
returns bare triples — different contracts per spec-028 Decision 8
(ordering has no operator bag; every leaf is `Ordering | None` per
Decision 5). C4 proves opposite change responses (a bag change moves the
filter hook + [filters-inputs][filters-inputs]; a triple-shape change
moves 9.10 + [orders-inputs][orders-inputs]). Adapters by design, one per
family, fired by the shared walk. CONVERGE with verified filters R1 on
fresh evidence. Trigger to reconsider: orders gaining an operator bag.
Durable home: the base `_build_input_triples` docstring (already states
the split) + this artifact. Named for Worker 0 as rejected index row
`orders-bfs-hook-vs-filter-operator-bag`.

### R-keys — reserved-key literal unification (rejection; CONVERGE filters R2)

Considered: unify statement 8 with the filter literal into one shared
reserved-keys set. Contract difference here: per-family vocabulary tied
to each side's `explicit_param` (`"orderset_base_class"` guards the
`orderset_class` construction param; the twin guards
`filterset_class`). C8 proves the stripping rule is already single-sited
(the owner); the literals are declarations. CONVERGE with verified
filters R2 on fresh evidence. Trigger to reconsider: the getter params
unified across families. Durable home: the statement-8 comment + this
artifact. Named for Worker 0 as rejected index row
`orders-reserved-keys-vs-filter-twin`.

### R-cache — shared Layer-6 cache dict (rejection; CONVERGE filters R3)

Considered: merge statement 7 with `_dynamic_filterset_cache` into one
shared dict. Contract difference here: disjointness IS the rule — "a
filter clear cannot drop an order class (and the reverse)", stated on
both sides; the twin-closure oracle pins `filt is not order` for
equivalent meta. A unified dict would need family-partitioned keys for
zero benefit (both surfaces are unconsumed). CONVERGE with verified
filters R3 on fresh evidence. Trigger to reconsider: a unified clear
hook that partitions by family. Durable home: the statement-7 comment
(mirrored twin-side) + this artifact. Named for Worker 0 as rejected
index row `orders-layer6-cache-vs-filter-twin`.

### R-gate — `require_fields_or_exclude` asymmetry (rejection; CONVERGE filters R6)

Considered: align the order construction (statement 10) with the filter
gate (or drop the filter gate into the default). Contract difference
here: django-filter's metaclass hard-asserts `fields`/`exclude`, while
the order plain `type` metaclass accepts a fields-less Meta whose
zero-field rejection stays at the BFS construction site — documented at
[utils-inputs][utils-inputs]`::create_dynamic_set_class`, pinned by the
fields-less-Meta oracle (builds, then the BFS rejects with "no fields").
C7 proves the gate is already single-sited (the owner); statement 10
carries the order declaration (default off). CONVERGE with verified
filters R6 on fresh evidence. Trigger to reconsider: the order metaclass
gaining a fields/exclude assertion. Durable home: the
`create_dynamic_set_class` docstring (already states the split) + this
artifact. Named for Worker 0 as rejected index row
`orders-getter-defaults-vs-filter-gate`.

### R-mutid — orders class-derived input identity vs mutation shape identity (rejection; CONVERGE mutid R2)

Considered: unify this file's generated-input identity (class-derived
names via `set_input_type_name`, same-name-collide registry, Layer-6
`(model, fields, extra)` keying) with verified family
`generated-mutation-input-identity` (shape-derived `<Model>Input` /
`<Model>PartialInput` naming via `mutation_input_shape`). Contract
difference here, checked fresh (trigger, not verdict, inherited): set
inputs name by DECLARING CLASS (`BookOrder` → `BookOrderInputType`) with
no shape axis — two distinct Meta declarations against the same model
land at the SAME generated `__name__` and collide through 9.3 by design
(statement-11 docstring; the anti-shape-identity behavior), while
mutation inputs name by EFFECTIVE FIELD SET (same shape → one shared
class; distinct shapes → distinct deterministic names). C11 proves
opposite change responses (a narrowing-axis change moves
[mutations-inputs][mutations-inputs]`::mutation_input_shape`; a
class-rename moves the declaring class + collisions here). CONVERGE with
verified [dry-mutid][dry-mutid] R2/C7 on fresh evidence. Trigger to
reconsider (standing, re-checked): a set family gaining a
narrowing-derived name axis — absent here (verified: no shape token in
the target; the Layer-6 key distinguishes cache slots, never names).
Durable home: [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin` per
the family R2 home + this artifact. Named for Worker 0 as rejected index
row `orders-input-identity-vs-mutation-shape`. Freshness: target
`4f35b66b…` (CLEAN), owner-name rule [sets-mixins][sets-mixins] HEAD
`ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3` (worktree `48b8ca20…` dirt
below the judged region), family artifact `7533c0cf`.

## Defects

### D1 — module docstring names a `build_input_class` path the BFS never takes (HEAD defect, clean lines — file for normal homing)

- **What.** The statement-1 paragraph describes the BFS as building
  "every reachable Strawberry input class via `_build_input_fields` +
  `build_input_class` from `orders/inputs.py`". The second half is
  false: NOTHING on the orders BFS path calls
  [orders-inputs][orders-inputs]`::build_input_class`. Verified against
  HEAD bodies: the construction call is
  [utils-inputs][utils-inputs]`::GeneratedInputArgumentsFactory._build_class_type`'s
  module-local `build_strawberry_input_class(...)` call — the only
  construction site on the path — and this factory does not even import
  the orders alias (statements 4–6 import the base, the getter maker,
  `_build_input_fields`, and `OrderSet` only). The package-wide
  `build_input_class` census finds ZERO production call sites of the
  orders alias (tests only, plus the `is`-identity pin); the alias and
  the owner are the same object, but the PATH the docstring names —
  "from `orders/inputs.py`" — is not taken. A reader relying on the
  sentence (wrap or intercept the orders alias to change BFS
  construction) silently affects nothing — a wrong stated path, which
  principle 10 ranks below none. The asymmetry sharpens it: the FILTER
  twin's alias carries TWO production call sites (range-input +
  operator-bag builders inside [filters-inputs][filters-inputs]), so
  the orders sentence states the filter-side shape as this file's own.
- **Lines.** Statement-1 docstring lines — CLEAN at HEAD (the target is
  fully clean; worktree == HEAD). HEAD defect on clean lines → normal
  closeout homing, no conditional.
- **Owner.**
  `django_strawberry_framework/orders/factories.py` module docstring
  (fix = restate as `_build_input_fields` ([orders-inputs][orders-inputs])
  + shared `build_strawberry_input_class` ([utils-inputs][utils-inputs],
  via the base); prose-only, no behavior change). Note for the homing
  card: [spec-028][spec-028] #"classes are emitted `@strawberry.input`-decorated
  via" echoes the same path — the card decides
  whether that spec sentence needs the same touch; the docstring is
  independently false against the tree either way.
- **Bilateral note (not homed here).** The
  [orders-inputs][orders-inputs] alias comment claims "Tests and
  `factories.py` import these ... names from this module" — this factory
  imports NONE of the five aliases (verified: statements 4–6). That
  comment lives in a file with a pending dedicated item; recorded here
  so it is not dropped, routed to the pending File `orders/inputs.py`
  item for fresh adjudication (no homing instruction from this item).
- **Freshness.** Target `4f35b66b06fe67e800ac43dabe8a1733b221168d`;
  [orders-inputs][orders-inputs] HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (alias block outside the
  dirt); [utils-inputs][utils-inputs] HEAD `ee31d360…` (construction
  site); [filters-inputs][filters-inputs] HEAD
  `82b52d97…` (twin alias production calls outside the dirt).
- **Not fixed.** File items never fix; recorded for Worker 0 to home on
  a NAMED owning card at closeout.

No other defects. Every remaining docstring claim checked held: the
`get_fields()`-consumption clause (hook → delegate → `get_fields()`),
the finalizer-materializes / build-only clause (zero `setattr` /
`sys.modules` / `materialize` calls in the target — the 3 `materialize`
hits are prose), the Layer-6 no-consumer clause (census-empty outside
tests; [connection][connection] sidecar reads verified), the Decision 9
cache-name clause (spec + oracles), the FIFO-vs-LIFO clause (base
`pending.pop(0)` + rationale), the subclass-rejection clause (base
`__init_subclass__` + oracle), the ledger/registry-split clause
(`_materialized_names` name→input-class vs 9.3 name→source-class, per
Decision 9 + rationale M1), and the distinct-Meta-collide clause
(true by construction of the `<Model>AutoOrder` name rule + 9.3 check).
The axis-6 sweep finds no missing guard.

## Pending execution

None. No `execution-deferred` proof: all claims are `static-reviewed`
from HEAD bytes (byte-level greps, `ast.parse` enumeration, full-body
reads), every target behavior is pinned by executed oracles on every
suite run, and no probe was created that could distinguish anything
further. Sharded / Postgres cells are inapplicable by construction: the
target reaches no database, alias, or dialect decision (pure
declarations + sync construction delegation; zero queryset tokens).

## Judgment

Zero-edit file item. Two rules adopted as families with fresh boundaries
(F-1 BFS substrate, C1–C4; F-2 dynamic-set getter, C5–C9), one routed to
its verified holding family (F-5c clear membership → C12), one file-local
with its proving challenge (L-a reserved literal, C8), five rejections
each converging onto a verified separation on fresh evidence (R-bag→R1,
R-keys→R2, R-cache→R3, R-gate→R6, R-mutid→mutid-R2), and two mechanisms
checked fresh with no surface (C10 set-naming pass-through — the base is
the consumer, this file not even that; cookbook twins out of
population). Enumeration covers 11/11 statements and 14/14 named members
(same 14-shape as the verified twin). One HEAD defect on clean lines
(D1 stale construction-path prose) filed for normal homing, plus one
bilateral observation routed to the pending inputs item without a homing
instruction. No pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `ITEM_BASELINE=6407bd4e71ee2317277146c6e4674b7a909d5b6d`:
`git diff <baseline> -- django_strawberry_framework/orders/factories.py`
is EMPTY (exit 0, zero hunks) — the target was never edited, reverted,
or worked around; worktree blob `4f35b66b…` equals HEAD throughout.
Window diff vs baseline over `django_strawberry_framework tests examples`
is EMPTY (no concurrent changes landed inside the item window). The
artifact itself (`docs/dry/dry-file-orders__factories.md`) is a new
untracked file, the item's only output. No `uv run ruff` run (no `.py`
edits; `.md` is outside ruff format scope; no `.py` scratch created). No
shared-tree pytest run (static-decidable — see `### Challenges` note).
No `docs/dry/temp-tests/` scratch created. HEAD confirmed `5ee86193` at
start and at artifact completion. Concurrent dirt (hunt edits across
`django_strawberry_framework/`, `tests/utils/test_inputs.py`) left
untouched; the `## Owned changes` ledger gains no row from this item.
No commit.

## Index rows for Worker 0

Worker-0 instructions: (a) tick the plan item
`File orders/factories.py — dry-file-orders__factories.md` as verified
under Run `0.0.15 2026-09-22-5` once Worker 2 agrees; (b) add these eight
`## Responsibility index` rows verbatim (holding item
`File orders/factories.py`) plus the two `## Families` items; (c) home D1
on a NAMED owning card at closeout (HEAD defect, clean lines — normal
homing, no conditional; the bilateral inputs-comment note rides with the
pending File `orders/inputs.py` item, not the card).

| `set-arguments-factory-bfs` | `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory` | `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/types/finalizer.py` | Family `set-arguments-factory-bfs` | open |
| `dynamic-set-class-getter` | `django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter` | `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/orders/sets.py` | Family `dynamic-set-class-getter` | open |
| `orders-factory-reserved-keys` | `django_strawberry_framework/orders/factories.py::_RESERVED_FACTORY_KEYS` | `django_strawberry_framework/orders/factories.py` | File `orders/factories.py` | file-local |
| `orders-bfs-hook-vs-filter-operator-bag` | `django_strawberry_framework/orders/factories.py::OrderArgumentsFactory._build_input_triples` (rejection recorded here; CONVERGE with verified filters/factories R1 on fresh evidence) | `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/filters/factories.py` | File `orders/factories.py` | rejected |
| `orders-reserved-keys-vs-filter-twin` | `django_strawberry_framework/orders/factories.py::_RESERVED_FACTORY_KEYS` (rejection recorded here; CONVERGE with verified filters/factories R2 on fresh evidence) | `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/filters/factories.py` | File `orders/factories.py` | rejected |
| `orders-layer6-cache-vs-filter-twin` | `django_strawberry_framework/orders/factories.py::_dynamic_orderset_cache` (rejection recorded here; CONVERGE with verified filters/factories R3 on fresh evidence) | `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/filters/factories.py` | File `orders/factories.py` | rejected |
| `orders-getter-defaults-vs-filter-gate` | `django_strawberry_framework/orders/factories.py::_get_orderset_class` (rejection recorded here; CONVERGE with verified filters/factories R6 on fresh evidence) | `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/utils/inputs.py` | File `orders/factories.py` | rejected |
| `orders-input-identity-vs-mutation-shape` | `django_strawberry_framework/orders/factories.py::OrderArgumentsFactory` (rejection recorded here; CONVERGE with verified generated-mutation-input-identity R2 on fresh evidence — trigger checked, no narrowing-derived name axis here) | `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/mutations/inputs.py` | File `orders/factories.py` | rejected |

Family items (no artifact on disk; undispatched; queue per Worker 0):

- [ ] Family `set-arguments-factory-bfs` — [dry-rule-set-arguments-factory-bfs.md](dry-rule-set-arguments-factory-bfs.md) — no artifact on disk; undispatched
- [ ] Family `dynamic-set-class-getter` — [dry-rule-dynamic-set-class-getter.md](dry-rule-dynamic-set-class-getter.md) — no artifact on disk; undispatched

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-clear-lifecycle]: dry-rule-subsystem-clear-lifecycle.md
[dry-filters-factories]: dry-file-filters__factories.md
[dry-mutid]: dry-rule-generated-mutation-input-identity.md
[dry-orders-base]: dry-file-orders__base.md
[dry-orders-init]: dry-file-orders____init__.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-028-rationale]: ../SPECS/appx/spec-028-orders-0_0_8-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-composition]: ../../tests/orders/test_composition.py
[test-order-factories]: ../../tests/orders/test_factories.py
[test-utils-inputs]: ../../tests/utils/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

### Own trace (recorded before opening `## Findings`)

HEAD pinned `5ee86193` confirmed (`git rev-parse --short HEAD` prints it).
Target CLEAN: worktree `4f35b66b06fe67e800ac43dabe8a1733b221168d` ==
`HEAD:django_strawberry_framework/orders/factories.py`, 155 lines. Window
`git diff --name-only ITEM_BASELINE -- django_strawberry_framework tests
examples` EMPTY at trace time. Hunt-dirtied reach (`orders/inputs.py`,
`orders/sets.py`, `utils/inputs.py`, `registry.py`, `types/finalizer.py`,
`tests/orders/test_inputs.py`) read via `git show HEAD:<path>` only.

Enumeration (mine, `ast.parse` over the worktree file): 11
`ast.Module.body` nodes — 1 docstring Expr + 5 `ImportFrom` + 5
definitions (`_dynamic_orderset_cache`, `_RESERVED_FACTORY_KEYS`,
`OrderArgumentsFactory`, `_get_orderset_class`, `get_orderset_class`);
`OrderArgumentsFactory` body holds 10 members (docstring + 2 caches + 6
hook attrs + `_build_input_triples`). Named rule-bearing total: 14
(10 module-level incl. 5 import groups + ... counting precisely: 4
module-level rule names [`_dynamic_orderset_cache`,
`_RESERVED_FACTORY_KEYS`, `_get_orderset_class`, `get_orderset_class`]
+ 1 class + 9 named class members = 14).

Sites + roles (mine):

- `OrderArgumentsFactory` + `input_object_types` /
  `_type_orderset_registry` + 6 hook attrs: DECLARATION of the shared BFS
  substrate. W2 owner choice:
  `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`
  (walk, collision check, idempotent cache, `__init_subclass__` guard —
  verified at HEAD bytes lines 1653-1823; exactly 2 direct subclasses
  package-wide: filter + order; 1 test probe subclassing the base
  directly, which the guard allows).
- `_build_input_triples` override: DECLARATION carrying the
  no-operator-bag contract (spec-028 Decision 8); the filter twin splices
  `_build_logic_fields`. Distinct adapters, not a merge.
- `_dynamic_orderset_cache` + `_get_orderset_class` +
  `get_orderset_class`: DECLARATIONs of the dynamic-set skeleton. W2 owner choice:
  `django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`
  (+ `normalize_set_meta_for_factory`, `make_set_meta_cache_key`,
  `create_dynamic_set_class` — verified at HEAD bytes lines 715-892);
  exactly 2 source call sites (filter + order). No source consumer of
  `get_orderset_class` outside tests (census verified); the deferred
  Layer-6 surface is build-and-test-only on both sides.
- `_RESERVED_FACTORY_KEYS`: file-local family vocabulary
  (`{"orderset_base_class"}` vs filter `{"filterset_base_class"}`), tied
  to each side's `explicit_param`.
- Consumers: finalizer phase 2.5 (`_bind_ordersets` reads
  `OrderArgumentsFactory(...).arguments` + `input_object_types` — verified
  at HEAD bytes); `clear_order_input_namespace` over
  `clear_generated_input_namespace` resets 9.2/9.3 (verified at HEAD
  bytes); no local clear body, no local registration here.
- Oracles: `tests/orders/test_factories.py` (27 tests + `_isolate_state`
  fixture, CLEAN, spells literals and drives behavior),
  `tests/orders/test_composition.py` (both factories' ledgers),
  `tests/utils/test_inputs.py` twin-closure gate (HEAD bytes),
  `tests/orders/test_inputs.py` clear-behavior arms (HEAD bytes).
- Projections: module/class/function docstrings; cookbook
  `*_arguments_factory.py` references are out-of-population (no such file
  in-tree; external source).

Definition counts per posited change (mine): BFS walk/collision/cache/
guard change → 1 (the base); ninth-hook-attr change → 1 + 2 family
declarations; empty-guard reword → 1 (base `_build_class_type`,
orders-only reachable); key-shape change → 1
(`make_set_meta_cache_key`); synonym/gate flips → 1 + a declaration flip
here; generated-name rule → 1 (`create_dynamic_set_class` f-string);
clear-contract change → 1 (registry bus), 0 here. Every count agrees the
target holds declarations only.

Matrix (mine): (1) filter twin read whole first — both cross-file rules
already compose by name through `utils/inputs.py`; per-family deltas are
contract (Decision 8, plain-metaclass fields-less lifecycle, no synonym
alias, disjoint caches by documented rule); (2) inapplicable — zero
`async`/`await`/`sync_to_async`/queryset tokens in the target, pure
finalize-time construction; (3) no local derivation — names via
`set_input_type_name`, keys/synonym/write-back via owner functions, the
`build_input_class` alias in `orders/inputs.py` is a re-export alias with
zero callers (census below), not a derivation; (4) no local pair — the
explicit/dynamic arms are one owner getter, normalize/key halves both in
the owner; the emit/normalize round-trip grammar lives in
`orders/inputs.py`, neither half here; (5) oracles spell expectations
(Decision-9 direct-cache addressability is the specified contract);
cookbook is out-of-population; docstrings are projections — one of them
breaks (D1, mine, below); (6) Layer-6 no-clear-hook is documented intent
both sides with no contract source demanding a hook on the unconsumed
deferred surface — no defect; `require_fields_or_exclude`/`fields_alias`
absence is the documented owner-side split — no defect.

D1 (mine, independent): the module docstring (lines 3-5) claims Layer 5
builds "via ``_build_input_fields`` + ``build_input_class`` from
``orders/inputs.py``". Half false: `orders/inputs.py::build_input_class`
(alias at HEAD line 54) has ZERO callers — the BFS construction path is
base `_build_class_type` → `utils/inputs.py::build_strawberry_input_class`
module-locally, never routed through the orders alias (census: only
docstring mentions package-wide). Docstring contradicts the body on clean
lines → HEAD defect for normal homing. Contract row: DRY.md "Defects
found while tracing" (docstring contradicting its body) + principle 10
(wrong stated reason < none).

### Reconciliation (after opening `## Findings`)

Every independent conclusion above agrees with the artifact; differences
reconciled explicitly:

- Enumeration: W1's 11/11 statements + 10 class members + 14/14 named
  rule-bearing members match mine exactly, member by member (module
  docstring + 5 imports + 5 definitions; 9.1–9.10 all homed). No gap.
- Matrix: all six axes discharged against the real surface. Axis 2
  inapplicability judged on its reason (zero async/queryset tokens —
  probe-verified) and accepted; axis 3/4 searched with the derivation
  sites and the no-local-pair ruling both confirmed fresh; axis 5 media
  census confirmed (oracles spell literals; Decision-9 direct-cache
  addressability is the specified contract); axis 6 enumerated with the
  no-hook intent re-checked on both sides. The axis-1 D1 asymmetry
  (filter alias 2 production calls vs orders alias 0) re-verified at
  HEAD bytes.
- Definition counts: C1–C12 agree with my posits one for one (1 per
  change at the owner, declarations here, C4/C11 separations standing).
- Sites + roles: identical owner choices (base, `make_dynamic_set_getter`
  + helpers, registry bus). Consumer/clear/oracle/projection roles all
  confirmed at HEAD bytes or clean-tree reads.
- F-1/F-2 adoptions: prior-evidence source is the verified
  `dry-file-filters__factories.md` F-1/F-2 (Status: verified, accepted
  under the ruling; twin fingerprint `4f35b66b` matches this target).
  Name fit confirmed on fresh evidence: same owners, same contracts, the
  order side is the declared second member of each rule; boundaries
  re-derived here (C1–C9, full owner-body reads at HEAD), not inherited.
  Lawful adoptions; Worker 0 adds the two family rows + family items.
- F-5c convergence: same rule (clear-bus membership) with a fresh
  trigger check (zero registration tokens here, reset rides the
  `orders.input_namespace` row, Layer-6 no-hook intent re-checked) —
  not a citation. Lawful; no new row (member 6 already covers).
- R-bag/R-keys/R-cache/R-gate convergences: each carries its contract
  difference + trigger with fresh evidence (C4 opposite-change proof,
  C8 single-sited stripping rule, twin-closure `filt is not order` pin,
  C7 single-sited gate + fields-less oracle). Lawful.
- R-mutid convergence: prior source verified (`Status: verified`, blob
  `7533c0cf`, R2 = class-derived naming with no shape axis, trigger = a
  set family gaining a narrowing-derived name axis). W1 re-checked the
  trigger fresh rather than inheriting the verdict. Lawful, with one
  W2 precision (P1, below) that does not disturb the trigger.
- D1: my independent D1 matches W1's D1 exactly — same sentence, same
  census (orders alias zero production callers; construction via the
  base's module-local owner call), same contract row (DRY.md Defects +
  principle 10). Filed as HEAD defect on clean lines for normal homing:
  correct. The spec-028 echo is correctly flagged for the homing card
  to decide, and the bilateral inputs-comment note is correctly routed
  to the pending inputs item with no homing instruction from this item.
- Freshness: all 16 cited HEAD/worktree fingerprints re-verified
  (`4f35b66b`, `366e0490`, `ee31d360`, `6f6ec946`, `6044ab1a`,
  `77fd9a2d`, `4736fda0`, `82b52d97`, `722e0c77`, `4894f90f`,
  `ad8987ea`, `4ec2ec05`, `d0cc8722`, `598f1440`, `94a3141c`,
  `7533c0cf`). Dirt-region disjointness claims spot-checked at HEAD
  (alias block, gate region, sidecar reads, write-back call lines).
- Pending execution: None, correctly — all proofs static-reviewed over
  declarations + delegating bodies; sharded/Postgres inapplicable by
  construction with the stated reason (zero queryset tokens), judged
  and accepted.
- AGENTS.md prose: no process-provenance words in W1 prose;
  `path::Symbol` citations throughout; reference-style links with all
  10 canonical group headers; no tests created (file item N/A).
  `uv run ruff format --check` → "1 file already formatted";
  `uv run ruff check` → "No Python files found … All checks passed" —
  the artifact is `.md`, outside ruff scope. Recorded.
- Probes: read-only census
  `docs/dry/temp-tests/dry-file-orders__factories-w2/census.py` (4 KB,
  no package import, no DB) — 15/15 PASS, exit 0. No mutating proof
  was needed; no `$TMPDIR/dry-ws` copy taken. Scratch path reported
  for Worker 0 removal by explicit path.

Reconciled differences (mine corrected on the record):

- W2 test-count correction: my trace said "27 tests" for
  `tests/orders/test_factories.py`; the file holds 29 `^def test`
  functions. W1 stated no count (666 lines only — confirmed), so no
  artifact change is owed.
- P1 (W2 precision, nothing structural): R-mutid's "verified: no shape
  token in the target" overstates — 4 prose tokens match
  case-insensitively ("runtime order shape", "GraphQL input shape",
  "shapes for Meta.fields", "Meta-shaped keys"). None is a
  narrowing-derived NAME axis: the Layer-6 key distinguishes cache
  slots, never names. The trigger re-check passes; the convergence
  stands. Recorded here, not edited into W1's section.

W2 defects: none. My independent D1 duplicates W1's filed D1, so no
separate `(Worker 2)` entry is owed under `## Defects`.

Index rows: the `## Index rows for Worker 0` content (8 rows + 2
family items) transcribes VERBATIM — owners, files-covered, holding
item, and rejected-row CONVERGE notes all match the verified findings.
No corrections.

### Verdict

`verified` (zero-edit file item; no `proof:` entries, no `gate:`
entries). HEAD `5ee86193` confirmed at verdict; window diff vs
`ITEM_BASELINE` over `django_strawberry_framework tests examples`
EMPTY at verdict; target still clean; the artifact is the item's only
output. No commit; plan untouched (Worker 0 ticks the row, adds the 8
index rows + 2 family items, and removes the W2 scratch dir by
explicit path).



