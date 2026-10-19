# DRY review: `filters/base.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Target owns the filter Layer-1/2 primitives (`django_strawberry_framework/filters/base.py`, 1212 lines,
blob `ba52351c`; working blob == `HEAD` blob, target CLEAN): graphene-parity typed ports
(`TypedFilter`/`ArrayFilter`/`RangeFilter`/`ListFilter`), integer hardening pair
(`IntegerInFilter`/`IntegerRangeFilter`), GlobalID decode-validate-apply trio
(`_decode_and_validate_global_id` + `GlobalIDFilter`/`GlobalIDMultipleChoiceFilter`), the
non-pk-`to_field` boolean-marker rule, and `RelatedFilter` (the `RelatedSetTargetMixin`
family adapter). No `Meta` handling (that is
[FilterSet][filters-sets]), no lookup-name grammar (that is
[filters/inputs.py][filters-inputs]`::LOOKUP_NAME_MAP`), no async surface.

Traced end to end: owner/consumer bodies in [sets_mixins.py][sets-mixins]
(`LazyRelatedClassMixin`, `RelatedSetTargetMixin`, `collect_related_declarations`), the
[orders/base.py][orders-base] mirror (`RelatedOrder`, `_order_set_class`), generation/stamp
consumers in [filters/sets.py][filters-sets] (`filter_for_field`, `filter_for_lookup`,
`_expand_related_filter`), the shared decode owner in [types/relay.py][types-relay]
(`decode_global_id`) and its node-path wrapper in [relay.py][relay]
(`_decode_or_graphql_error`, `_coerce_pk_or_none`), the strategy tables owned by
[types/relay.py][types-relay] (`MODEL_LABEL_STRATEGIES`, `TYPE_NAME_STRATEGIES`), the
build-time audit in [finalizer.py][finalizer] (`_audit_globalid_filter_strategies`),
the coercion/seed owners in [utils/querysets.py][utils-querysets]
(`coerce_field_value_or_none`, `base_queryset`), the input-key producer in
[filters/inputs.py][filters-inputs] (`normalize_input_value`, range patch), the public
re-export in [filters/__init__.py][filters-init], oracles in
[test_sets.py][test-filter-sets], and the upstream graphene ports
(`graphene_django/filter/filters/`, `django_graphene_filters/mixins.py`,
`django_graphene_filters/filters.py`) as out-of-population contract sources.

## Verification

### Matrix

1. **Cross-flavor mirroring** — searched. Read [orders/base.py][orders-base] first (151 lines,
whole file). `RelatedFilter` vs `RelatedOrder`: shared seam
(`RelatedSetTargetMixin` subclass, `_target_attr`/`_owner_attr` params, `_bind_owner` /
`_resolved_target` / `_set_target` thin wrappers, per-family `_validate_target` gate) with
genuinely different adapters: filter twin adds the `lookups=` rejection,
`_has_explicit_queryset`, and `get_queryset` (orders carry no queryset — verified: no
`get_queryset`, no `queryset` in [orders/base.py][orders-base]); `_filter_set_class` vs
`_order_set_class` are per-family deferred bases (rejection R1). Orders-side hostile-input
shape (`orders/sets.py::OrderSet._validate_normalized_terms` exact-type pins) shares only
the fail-closed direction with `_materialize_list_shaped_values`, not a body (rejection R8).
2. **Sync/async twins** — inapplicable with reason: the file contains no `async def` and no
`await` (verified by search); django-filter `.filter()` bodies are sync-only by framework
contract and execute inside the single sync boundary owned by
[filters/sets.py][filters-sets]`::FilterSet.apply_async`. Not a `one-sync-boundary`
consumer (verified: no import, no call).
3. **Derived knowledge** — searched. `FRAMEWORK_GLOBALID_STRATEGIES` composes the owner sets
by name (`MODEL_LABEL_STRATEGIES | TYPE_NAME_STRATEGIES`); `ENCODE_ONLY_GLOBALID_STRATEGIES`
is deliberately a local literal (rejection R5 note in F-e). `_marked_pk_field_name` derives
`f"{live field_name}__pk"` at filter time (never a stored path — rebase-immune by
construction). `IntegerInFilter` resolves its column via `get_model_field` (which-field
stays at the caller per the coercion owner's contract).
4. **Round-trip pairs** — searched. Range positional keys: sole producer
[filters/inputs.py][filters-inputs]`::normalize_input_value` (range patch) emits
`{<name>_0, <name>_1}`; sole consumer `filters/base.py::_RangeWidget` reads them — one
grammar, two halves, producer/consumer (file-local F-g). Omission round-trip:
`_AbsentGlobalIDMultipleChoiceWidget.value_from_datadict` (`None` for absent key) →
`_GlobalIDMultipleChoiceField.to_python`/`validate` (`None` preserved) → `filter`
(`None` = skip, `[]` = match-none) — single-sited chain (file-local F-h).
Encode/decode: encoder ([types/relay.py][types-relay]) vs filter validation
(`_decode_and_validate_global_id` + `_accepted_globalid_type_names`); build-time audit
([finalizer.py][finalizer]`::_audit_globalid_filter_strategies`) and runtime backstop share
the single-sited `resolve_globalid_target_definition` by name in both directions.
5. **Contracts in another medium** — searched. Oracles: [test_sets.py][test-filter-sets]
(RelatedFilter binding/expansion, GlobalID marking/rebase, `IntegerInFilter` empty semantics,
range positional keys) exercise behavior without reading owner internals. Projections:
spec-027/spec-031 decision pointers in docstrings, module docstring port notes. Upstream
graphene ports are out-of-population oracles/sources (rejection R7). No test or doc
restates a package rule as an independently maintained definition.
6. **Enforcement by omission** — enumerated. List-shape gate covers `ListFilter`,
`IntegerInFilter`, GlobalID multi; `IntegerRangeFilter` deliberately skips (different
contract, F-d); scalar `GlobalIDFilter` needs none (scalar shape). `_match_none_queryset`
serves exactly the three restrictive-empty producers in the file; explicit-`[]` skip and
`None` omission are different contracts, each documented at its site. Empty-list-aware
`method=` swap exists exactly where `method=` meets list shapes (`ArrayFilter`,
`ListFilter`); no other filter in the file takes a list value under `method=`. The
`globalid-decode-input-hardening` asymmetry (family F-8) is named for the family item,
not filed as a defect: wire (`str`) inputs cannot diverge; only hand-built hostile
objects via direct-Python calls reach it.

### Enumeration

Instrument: every name in `ast.Module.body` that defines a rule or binds a value —
top-level `ClassDef` / `FunctionDef` / `Assign` plus every method (`FunctionDef` under a
`ClassDef`). 17 imports, the module docstring, and the `TYPE_CHECKING` block are
non-rule scaffolding, excluded with reason. **Count: 56 members**, every one assigned
below (F = family incl. proposed, L = file-local, R = rejection).

| # | Member | Home |
|---|---|---|
| 1 | `FRAMEWORK_GLOBALID_STRATEGIES` | F-e (derives owner sets by name) |
| 2 | `ENCODE_ONLY_GLOBALID_STRATEGIES` | F-e (intentionally local literal) |
| 3 | `TypedFilter` | L-a (marker port) |
| 4 | `_EmptyListAwareFilterMethod` + 5 `__call__` | F-a |
| 6 | `_install_empty_list_aware_method` | F-a (single owner of the setter body) |
| 7 | `_apply_lookups` | F-b |
| 8 | `_apply_lookup_predicate` | F-b |
| 9 | `_match_none_queryset` | F-c |
| 10 | `_materialize_list_shaped_values` | F-d |
| 11 | `_globalid_multiple_choice_values` | F-d (thin code-binding wrapper) |
| 12 | `_GLOBALID_RELATION_PK_ATTR` | F-7 (proposed `globalid-relation-pk-marker`) |
| 13 | `_relation_uses_non_pk_to_field` | F-7 (stamp predicate; called from [filters/sets.py][filters-sets]) |
| 14 | `_marked_pk_field_name` | F-7 (single read/derive home) |
| 15 | `ArrayFilterMethod` | F-a (parity type identity) |
| 16 | `ArrayFilter` + 17 `method` setter + 18 `filter` | F-a (setter) / F-b (predicate) / L-a (hostile-`__eq__` guard inside `filter`) |
| 19 | `validate_range` | L-a |
| 20 | `_RangeWidget` + 21 `__init__` + 22 `decompress` | F-g (round-trip consumer half) |
| 23 | `RangeField` + 24 `to_python` | F-g |
| 25 | `RangeFilter` | L-a (marker port) |
| 26 | `ListFilterMethod` | F-a (parity type identity) |
| 27 | `ListFilter` + 28 `method` setter + 29 `filter` | F-a (setter) / F-d (shape gate) / F-c (empty arm) |
| 30 | `_coerce_int_in_members` | F-1 (`field-value-coercion` consumer) |
| 31 | `IntegerInFilter` + 32 `filter` | F-d (shape gate) / F-c (fully-dropped arm) / F-1 (coercion call) |
| 33 | `IntegerRangeFilter` + 34 `filter` | F-b (decomposed `gte`+`lte` via `_apply_lookups`) / R5 (inline skip, different contract) |
| 35 | `_target_definition_for` | F-e (owner/target routing, single-sited) |
| 36 | `resolve_globalid_target_definition` | F-e (shared by runtime + finalizer audit by name) |
| 37 | `_accepted_globalid_type_names` | F-e (strategy-aware acceptance) |
| 38 | `_decode_and_validate_global_id` | F-e (validate) / F-1 (pk coercion call) / F-8 (hardening asymmetry site) / R4 (message wording) |
| 39 | `GlobalIDFilter` + 40 `filter` | F-e (decode call) / F-7 (pk-marker read) / F-b (pk-branch predicate) |
| 41 | `_AbsentGlobalIDMultipleChoiceWidget` + 42 `value_from_datadict` | F-h (omission round-trip) |
| 43 | `_GlobalIDMultipleChoiceField` + 44 `valid_value` + 45 `to_python` + 46 `validate` | F-h |
| 47 | `GlobalIDMultipleChoiceFilter` + 48 `filter` | F-d (container gate) / F-c (empty arm) / F-e (per-element decode) / F-7 (pk-marker read) / F-b (pk-branch predicate) |
| 49 | `_filter_set_class` | R1 (per-family deferred base; mirror recorded at owner) |
| 50 | `RelatedFilter` + 51 `__init__` (`lookups=` guard, `_has_explicit_queryset`) + 52 `bind_filterset` + 53 `_validate_target` + 54/55 `filterset` property/setter + 56 `get_queryset` | F-2 (re-export/indirect lazy-consumer context) / F-3 (lifecycle adapter) / F-4 (seed consumer) / L-b (`lookups=` guard + explicit-queryset intent) / R2 + R3 (order-twin separations) |

Static probe (AST walk, read-only): `resolve_lazy_class`, `_bind_owner`,
`_resolved_target`, `_set_target`, `collect_related_declarations`,
`run_in_one_sync_boundary`, `model_for`, `import_string` appear **zero** times as
definitions in the target — no second owner for any indexed family machinery.
`LazyRelatedClassMixin as LazyRelatedClassMixin` is a pure re-export (no body).

### Challenges

- **Coercion mechanics** (`coerce_field_value_or_none` callers): posit range-check accepted
for a new field kind → 1 definition moves ([utils/querysets.py][utils-querysets]); posit
changing WHICH field the `__in` path coerces against → caller-side decision, not counted
(per owner contract). Consumers, not copies — matches index `rejected`.
- **Lazy resolution**: posit a new accepted reference shape (e.g. lazy object) →
`sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class` only; target has no
definition to move (0 here, 1 system-wide). Re-export needs no change.
- **Target lifecycle**: posit a new bind policy (e.g. first-bind-wins → last-bind-wins) →
`sets_mixins.py::RelatedSetTargetMixin._bind_owner` only; posit FilterSet accepting a new
target shape → `RelatedFilter._validate_target` (adapter, 1 of 2 family adapters — the
order twin's gate is a different family's rule, R2).
- **Seed**: posit alias-pinned seeding (`using=`) for related branches →
`utils/querysets.py::base_queryset` already takes `using`; callers opt in — target passes
no alias because `ModelChoiceFilter.get_queryset(request)` carries none (F-4, not F-6).
- **Empty-list-aware install**: posit a third list-shaped filter kind → add one
`*FilterMethod` identity + one `_install_empty_list_aware_method` call (declaration, not
a method); posit changing wrapper semantics → 1 definition. (Principle 1 shape,
already realized.)
- **Whole-value predicate**: posit honoring `distinct` differently → `_apply_lookups`
only (then `IntegerRangeFilter` + `_apply_lookup_predicate` follow); posit per-element OR
→ would touch the single `_apply_lookup_predicate`, which exists precisely to forbid it.
- **Match-none**: posit a fourth restrictive-empty producer → route it to
`_match_none_queryset` (declaration); posit changing exclude-complement → 1 definition.
- **Materialize**: posit a new accepted container shape → `_materialize_list_shaped_values`
only; posit `IntegerRangeFilter` rejecting malformed shapes → intentional difference (R5),
not drift.
- **GlobalID strategy set**: posit a new framework strategy (`type+model+app`) → owner
sets in [types/relay.py][types-relay] change; `FRAMEWORK_GLOBALID_STRATEGIES` follows by
construction (0 edits here); acceptance arms in `_accepted_globalid_type_names` extend
(mechanics, not policy). Posit deriving `ENCODE_ONLY_*` by exclusion → rejected (R5/F-e):
a new encode-only strategy would be silently absorbed; the literal names it for the
reject message.
- **PK marker**: posit a new non-pk relation shape needing qualification → stamp predicate
`_relation_uses_non_pk_to_field` only; derivation `_marked_pk_field_name` follows; posit
renaming `field_name` mid-flight → derived-at-read survives (rebase-immunity is the
test-pinned property in [test_sets.py][test-filter-sets]).
- **Decode hardening** (F-8): posit requiring an input gate + slot normalization at every
GlobalID decode entry → 1 definition exists ([types/relay.py][types-relay]) and 1 site
lacks it (here) — family item decides consolidate vs intentional separation; wire inputs
(`str`) cannot distinguish the two today.
- **Deferred family base**: posit unifying `_filter_set_class`/`_order_set_class` →
rejected (R1): each imports its own sibling `sets` module; one shared helper would couple
the families and close an import cycle the deferral exists to keep open.

All probes static-reviewed (body inspection + `rg` population counts + AST walk). No
mutating proof was needed: no ordering, transactional, or async behavior is decided in
this file. No execution-deferred entries.

## Findings

**F-1 `field-value-coercion` (REUSE, index: rejected).** Contract: raw literal → Django
field value or `None` ("identifies no row"). Owner:
[utils/querysets.py][utils-querysets]`::coerce_field_value_or_none`. Consumers in target:
`filters/base.py::_coerce_int_in_members` (per-member coerce + drop) and
`filters/base.py::_decode_and_validate_global_id` (node-id coerce against target pk;
rejects as `GLOBALID_INVALID` on `None`). Challenges above (1 definition per change).
Migration: none (already compose by name). Distinct behavior: which-field choice stays at
each call site per owner contract. Proof: static-reviewed (call sites pass a field and
branch on `None`; no local `to_python`/`run_validators` spelling). Gate: none owed
(rejected family; consumers already fail closed through the owner). Freshness: target
`ba52351c`, owner `1539b66c`, HEAD `9031cb3d`.

**F-2 `lazy-related-class-resolution` (REUSE, index: open).** Owner:
[sets_mixins.py][sets-mixins]`::LazyRelatedClassMixin`. Target role: pure re-export
(`LazyRelatedClassMixin as LazyRelatedClassMixin`, surfaced via
[filters/__init__.py][filters-init]) + indirect consumer (`RelatedFilter` inherits
resolution through `RelatedSetTargetMixin`; zero direct `resolve_lazy_class` calls —
AST-verified). No definition here; nothing to consolidate. Freshness: target `ba52351c`,
owner `ad8987ea`, HEAD `9031cb3d`.

**F-3 `related-set-target-lifecycle` (REUSE, index: open).** Owner:
[sets_mixins.py][sets-mixins]`::RelatedSetTargetMixin`. Target adapter:
[filters/base.py][filters-base]`::RelatedFilter` (`_target_attr`/`_owner_attr` params,
`bind_filterset`, `filterset` property/setter, `_validate_target` FilterSet-only gate).
Mirror adapter: [orders/base.py][orders-base]`::RelatedOrder`. No consolidation in a file
item; adapters stay per family (principle 5). Freshness: target `ba52351c`, owner
`ad8987ea`, mirror `4736fda0`, HEAD `9031cb3d`.

**F-4 `queryset-seed-and-model-read` (REUSE, index: open).** Owner:
[utils/querysets.py][utils-querysets]`::model_for` (+ `base_queryset`). Target consumer:
`RelatedFilter.get_queryset` seeds the derived branch via `base_queryset(model)` (the
relation-model seed the owner docstring names); `IntegerInFilter.filter` reads its column
via `parent._meta` + `get_model_field` (which-field at caller, per contract);
`resolve_globalid_target_definition` walks `_meta`/relation targets single-sited here and
is consumed by name from both runtime and
[finalizer.py][finalizer]`::_audit_globalid_filter_strategies`. No `model_for` call here
(no registered-type seed at this seam). Freshness: target `ba52351c`, owner `1539b66c`,
sets consumer `4ab65a26`, finalizer `77fd9a2d`, HEAD `9031cb3d`.

**F-5 `one-sync-boundary` — NOT a consumer, do not list.** Verified: no import, no call,
no `async def`/`await` in target. Filter bodies run inside the boundary owned by
[filters/sets.py][filters-sets]`::FilterSet.apply_async`.

**F-6 `child-queryset-alias-inheritance` — checked, NOT a member, do not inherit.**
`RelatedFilter.get_queryset` calls `base_queryset(model)` without `using=`; no alias
decision exists at the `ModelChoiceFilter.get_queryset(request)` seam, and the family
index does not cover this file. No second site, no omission.

**F-7 `globalid-relation-pk-marker` (NEW FAMILY, for Worker 0 index).** Contract: a
forward FK/O2O bound on a non-pk `to_field` carries a boolean flag (never a frozen path);
GlobalID predicates derive `f"{live field_name}__pk"` at filter time. Owner:
[filters/base.py][filters-base]`::_GLOBALID_RELATION_PK_ATTR` +
`::_relation_uses_non_pk_to_field` + `::_marked_pk_field_name` (single stamp predicate,
single read/derive home). Enforcement/stamp consumer:
[filters/sets.py][filters-sets]`::FilterSet.filter_for_field`. Read consumers:
`GlobalIDFilter.filter`, `GlobalIDMultipleChoiceFilter.filter`. Oracles:
[test_sets.py][test-filter-sets] (marker stamping, deepcopy rebase survival). Challenges
above (1 definition per change). No consolidation owed (already single-sited); holding
item for the cross-file rule. Freshness: target `ba52351c`, sets `4ab65a26`,
HEAD `9031cb3d`.

**F-8 `globalid-decode-input-hardening` (NEW FAMILY, for Worker 0 index).** Contract:
a GlobalID decode entry rejects non-`(GlobalID, str)` input before parsing and normalizes
hostile `str`-subclass slots before probing. Owner-side definition:
[types/relay.py][types-relay]`::decode_global_id` (input gate + `str.__str__`
normalization). Second site lacking both:
[filters/base.py][filters-base]`::_decode_and_validate_global_id` (`except ValueError`
only; unguarded `in EMPTY_VALUES`/membership probes on decoded slots). Same accepted
pair per both docstrings; same fail-closed direction claimed. Divergence is unreachable
from wire inputs (GraphQL delivers `str`; `GlobalID` objects arise only via direct-Python
calls), so no defect is filed — the family item runs the change challenge and decides
consolidate vs intentional separation. Trigger to re-litigate: a wire-reachable
non-`str` GlobalID input shape. Freshness: target `ba52351c`, relay-types `52439862`,
HEAD `9031cb3d`.

**L-a through L-c, F-a through F-d, F-g, F-h, L-b (file-local).** Each single-sited
(package-wide `rg` + AST walk found no second package definition; upstream graphene /
django-filter twins are out-of-population external sources — R7):
- **F-a `empty-list-aware-method-install`** (`_EmptyListAwareFilterMethod`,
`_install_empty_list_aware_method`, `ArrayFilterMethod`, `ListFilterMethod`, both
`method` setters): one setter body; per-filter subclasses are graphene-parity public
type identities (separation recorded in the `_install` docstring). Challenge above.
- **F-b `whole-value-lookup-application`** (`_apply_lookups`, `_apply_lookup_predicate`):
`distinct`-then-one-predicate seam; callers `ArrayFilter.filter`, both GlobalID pk
branches, `IntegerRangeFilter`. Challenge above.
- **F-c `restrictive-empty-match-none`** (`_match_none_queryset` + 3 call sites).
Challenge + axis-6 coverage above.
- **F-d `list-shape-fail-closed-materialization`** (`_materialize_list_shaped_values`,
`_globalid_multiple_choice_values`, `ListFilter`/`IntegerInFilter` gates). Challenge above.
- **F-g `range-positional-round-trip (consumer half)`** (`_RangeWidget`,
`RangeField.to_python`): sole consumer of [filters/inputs.py][filters-inputs]' single
producer; `MultiWidget` `_0`/`_1` suffix contract. No second reader package-wide.
- **F-h `globalid-multi-omission-chain`** (`_AbsentGlobalIDMultipleChoiceWidget`,
`_GlobalIDMultipleChoiceField` trio): `None`-for-absent preserved end to end; only
`MultipleChoiceField` shape in the package that does so (verified: no other
`value_from_datadict` override in package).
- **L-a `typed-port surface`** (`TypedFilter`, `RangeFilter`, `ArrayFilter.filter`
hostile-`__eq__` guard, `ListFilter.filter` body, `validate_range`): per-class lookup
contracts; a change to one lookup's semantics moves that class only.
- **L-b `related-explicit-queryset-intent`** (`RelatedFilter.__init__` `lookups=` guard +
`_has_explicit_queryset`; `get_queryset` explicit/derived branch): no order-twin
counterpart (orders have no queryset); seed step itself is F-4.
- **F-e `globalid-target-resolution-and-acceptance`** (treated as file-owned rule with
cross-file consumers, single-sited): `_target_definition_for`,
`resolve_globalid_target_definition`, `_accepted_globalid_type_names`,
`FRAMEWORK_GLOBALID_STRATEGIES` union, `ENCODE_ONLY_*` literal. Consumers by name:
runtime filters + [finalizer.py][finalizer] audit. `ENCODE_ONLY` locality is
intentional (message names; exclusion would absorb new strategies silently).

**Rejections R1–R8** (difference + trigger + home): R1 deferred family bases
(different bases/edges; sharing couples families + closes the cycle; trigger: a third
family still keeps its own — home: `filters/base.py::_filter_set_class` docstring). R2
per-family `_validate_target` gates (adapters by design; trigger: none). R3
`get_queryset` vs no order queryset (trigger: orders gaining querysets — no spec). R4
malformed-payload message prefixes (context projections; code shared via
`GLOBALID_INVALID_ERROR_CODE` + `coded_error_extensions`; trigger: unifying message
context). R5 range inline skip vs materialize-reject (different contracts; trigger:
range gaining a reject contract). R6 twin docstring prose (explanation, out of
population). R7 graphene/django-filter ports (external sources/oracles, different repo).
R8 hostile-container mechanics vs `orders/sets.py::_validate_normalized_terms`
(different shapes, shared direction only; trigger: a shared hostile-input policy owner).

## Defects

None. Two probed edges were released as robustness observations, not defects (no
wire-reachable contract broken, no contract source establishing the stricter rule for
this entry): (1) a non-`(str, GlobalID)` scalar (e.g. `int`) reaches
`relay.GlobalID.from_id`, whose `except ValueError` does not catch `TypeError` — direct-
Python calls only, GraphQL coerces to `str`; (2) a hand-built `GlobalID` carrying a
hostile `str`-subclass slot reaches unguarded membership probes — same reachability;
named as family F-8 for the family item. Owner of both observations:
[filters/base.py][filters-base]`::_decode_and_validate_global_id`.

## Pending execution

None. Every proof is static-reviewed (body inspection, `rg` populations, AST walk);
no ordering / transactional / async behavior is decided here, so no execution-deferred
entry exists.

## Judgment

Zero-edit result: matrix discharged against the real surface (orders mirror read first;
`Meta`/lookup-grammar/async absences verified, not assumed), 56/56 members assigned
(4 reused families as consumer/re-export, 1 reuse correctly withheld, 1 checked
non-membership, 2 new families named, remainder file-local or rejected with
difference + trigger + home), challenges recorded with definition counts, no defect
with a wire-reachable contract found. The two genuine cross-file rules already compose
by name (`coerce_field_value_or_none`, `resolve_globalid_target_definition`,
strategy sets); the one real asymmetry (F-8) is routed to its family item, not fixed here.

## Implementation (Worker 1)

No production edits (file item; target CLEAN throughout). No new tracked files besides
this artifact (untracked until Worker 0 records it). Item-scoped diff vs `ITEM_BASELINE`
`f5e5896f1dabe9c11847bc431f0dd91bf5f9304c` for `django_strawberry_framework/filters/base.py`
+ this artifact path: empty. Concurrent dirt explicitly untouched: working-tree
`django_strawberry_framework/connection.py` hunk, `tests/test_connection.py`,
staged `tests/utils/test_querysets.py` (+31), `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md` — none opened, none attributed here. No pytest run (not
authorized by the entry command; no edits to verify). No scratch files created (all
probes read-only inline: `rg`, AST walk, installed-`.venv` source reads); no
`docs/dry/temp-tests/` directory was needed.

## Independent verification (Worker 2)

Verified at `HEAD` `9031cb3d` against `ITEM_BASELINE`
`f5e5896f1dabe9c11847bc431f0dd91bf5f9304c`. No `worker-memory/` read;
sources were the target, the item-scoped diff, consumers/tests, and the
artifact's claims checked against the tree.

### Own trace (recorded before reconciling with ## Findings)

| Rule re-derived | Sites + roles | Definitions per posited change | Owner I would choose |
|---|---|---|---|
| Lookup-name grammar | None in target (no `Meta`, no `LOOKUP_NAME_MAP` symbol); grammar owned by [filters/inputs.py][filters-inputs] | 0 here | `filters/inputs.py::LOOKUP_NAME_MAP` (not this file) |
| `Meta` handling | None in target | 0 here | [filters/sets.py][filters-sets]`::FilterSet` (not this file) |
| Field-value coercion mechanics | Consumer: `_coerce_int_in_members` (per-member coerce + drop), `_decode_and_validate_global_id` (pk coerce, `None` = reject); definition in [utils/querysets.py][utils-querysets]`::coerce_field_value_or_none` | New field-kind range rule → 1 (owner); which-field choice → caller-side per owner contract, not counted | `utils/querysets.py::coerce_field_value_or_none` |
| Lazy related-class resolution | Pure re-export (`LazyRelatedClassMixin as LazyRelatedClassMixin`) + indirect consumer (`RelatedFilter` inherits resolution via `RelatedSetTargetMixin`); zero `resolve_lazy_class` definitions in target (AST-verified) | New accepted reference shape → 1 system-wide, 0 here | `sets_mixins.py::LazyRelatedClassMixin` |
| Related-set target lifecycle | Adapter: `RelatedFilter` (`_target_attr`/`_owner_attr`, `bind_filterset`, `filterset` property/setter, FilterSet-only `_validate_target`); mirror adapter [orders/base.py][orders-base]`::RelatedOrder` | New bind policy → 1 (owner `_bind_owner`); new FilterSet target shape → 1 of 2 family adapters | `sets_mixins.py::RelatedSetTargetMixin`, adapters per family |
| Queryset seed + model read | Consumer: `RelatedFilter.get_queryset` seeds via `base_queryset(model)` with no `using=` (no alias decision exists at the `ModelChoiceFilter.get_queryset(request)` seam); `IntegerInFilter` reads its column via `get_model_field`; `resolve_globalid_target_definition` single-sited here, consumed by runtime + [finalizer.py][finalizer] audit by name; no `model_for` call here | Alias-pinned seeding → callers opt in at owner (0 here) | `utils/querysets.py::base_queryset` |
| GlobalID relation pk-marker | Definition trio `_GLOBALID_RELATION_PK_ATTR` + `_relation_uses_non_pk_to_field` + `_marked_pk_field_name`; stamp consumer [filters/sets.py][filters-sets]`::FilterSet.filter_for_field` (single stamp site); read consumers `GlobalIDFilter`/`GlobalIDMultipleChoiceFilter`; oracles in [test-filter-sets] | New non-pk relation shape → 1 (stamp predicate); mid-flight `field_name` rename → 0 (derived-at-read survives) | The base.py trio (single stamp predicate + single read/derive home) |
| GlobalID decode input hardening | Gate + `str.__str__` slot normalization defined in [types/relay.py][types-relay]`::decode_global_id`; lacking in `_decode_and_validate_global_id` (`except ValueError` only; unguarded `in EMPTY_VALUES`/membership probes); same accepted `(GlobalID, str)` pair per both docstrings; wire `str` inputs cannot distinguish the two | Input gate at every decode entry → 1 exists + 1 site lacks it; family item decides | Gate owner `types/relay.py::decode_global_id`; filter site composes or records intentional separation |
| GlobalID target resolution + acceptance | `_target_definition_for` + `resolve_globalid_target_definition` + `_accepted_globalid_type_names` + `FRAMEWORK_GLOBALID_STRATEGIES` (union by name) + `ENCODE_ONLY_*` (deliberate local literal); strategy sets owned by [types/relay.py][types-relay]; consumers: runtime filters + finalizer audit | New framework strategy → owner sets change, union follows by construction (0 here) | Strategy sets in `types/relay.py`; resolution/acceptance single-sited here |

Reconciliation: ownership matches Worker 1 on every row (F-1 through F-8,
F-e, L-a/L-b, R-series). No difference to record on owners, roles, or counts.

### Enumeration (member-by-member vs own count)

Own instrument (same as Worker 1's): top-level `ClassDef`/`FunctionDef`/`Assign`
in `ast.Module.body` + every method (`FunctionDef` under a `ClassDef`).
Result: 34 tops (16 classes + 15 functions + 3 assigns) + 22 methods = **56**,
agreeing with Worker 1's 56. Exclusions (17 imports, module docstring,
`TYPE_CHECKING` block) are justified: imports are references not definitions,
the docstring is projection, the `TYPE_CHECKING` block holds type-only imports
(`pragma: no cover`). Module body length 53 = 1 + 17 + 1 + 34, consistent.
Every one of my 56 maps onto Worker 1's table (tops rows 1–3, 6–16, 19–20,
23, 25–27, 30–31, 33, 35–39, 41, 43, 47, 49–50; methods rows 5, 17–18, 21–22,
24, 28–29, 32, 34, 40, 42, 44–46, 48, 51–56). Class-body assigns (`widget`,
`field_class`, `_target_attr`/`_owner_attr`, `default_validators`,
`empty_values`) fold into their enclosing class rows — legitimate under the
instrument, and spot-checked: no hidden rule (e.g. `RangeField.empty_values`
is covered by the F-g row's home). No member unassigned, none double-counted.

### Matrix (against the real surface, orders mirror first)

1. Cross-flavor mirroring — discharged, agree. Read [orders/base.py][orders-base]
whole (151 lines): shared seam (`RelatedSetTargetMixin`, params, thin
wrappers, per-family gate) with genuine adapter differences confirmed by body:
filter twin's `lookups=` rejection + `_has_explicit_queryset` + `get_queryset`
have no orders counterpart (verified: no `get_queryset`/`queryset` in
orders/base.py); `_filter_set_class` vs `_order_set_class` are per-family
deferred bases (R1). Orders hostile-input shape (`_validate_normalized_terms`
exact-type pins + `ConfigurationError`) vs `_materialize_list_shaped_values`
(`isinstance` + coded `GraphQLError`): shared fail-closed direction only (R8).
2. Sync/async twins — inapplicable, reason accepted: verified zero `async def`
/ `await` in target and no `run_in_one_sync_boundary` import or call; filter
bodies run inside the boundary owned by
[filters/sets.py][filters-sets]`::FilterSet.apply_async`.
3. Derived knowledge — searched, agree: `FRAMEWORK_GLOBALID_STRATEGIES`
unions owner sets by name; `ENCODE_ONLY_*` locality is intentional (exclusion
would silently absorb a new encode-only strategy); `_marked_pk_field_name`
derives at filter time (rebase-immune); which-field stays at callers per the
coercion owner's contract.
4. Round-trip pairs — searched, agree: range producer
[filters/inputs.py][filters-inputs]`::normalize_input_value` (positional
`_0`/`_1` patch) / sole consumer `_RangeWidget` (+ `RangeField.to_python`
`None`-collapse); omission chain (`_AbsentGlobalIDMultipleChoiceWidget` →
field trio → `None`-skip vs `[]`-match-none) single-sited (verified: sole
`value_from_datadict` override package-wide); encode vs filter-validation
halves share `resolve_globalid_target_definition` by name in both directions
(finalizer imports it; runtime calls it).
5. Contracts in another medium — searched, agree: oracles in
[test-filter-sets] / `tests/filters/test_base.py` / `tests/filters/test_inputs.py`
assert literal behavior (coded errors, predicates, `None` vs `[]`); grep
confirms no test reads `LOOKUP_NAME_MAP`, `MODEL_LABEL_STRATEGIES`,
`TYPE_NAME_STRATEGIES`, `FRAMEWORK_GLOBALID_STRATEGIES`, or
`coerce_field_value_or_none` to compute expectations (`resolve_globalid_target_definition`
imports are the target's own function under test, not a foreign owner).
Projections are spec pointers + port notes. Upstream graphene/django-filter
twins are out-of-population sources (R7). No oracle rewritten.
6. Enforcement by omission — enumerated, agree: list-shape gate covers the
three list consumers; `IntegerRangeFilter` skip is a different contract (R5);
scalar `GlobalIDFilter` needs none; `_match_none_queryset` serves exactly the
three restrictive-empty producers; `method=` swap exists exactly where
`method=` meets list shapes. No contract source establishes a missing guard,
so no defect filed — correct per axis 6.

### Counts + roles; equivalence

Definition counts confirmed per row in the trace table above; site roles
(definition / consumer / oracle / projection) match Worker 1 throughout, with
F-5 correctly withheld (not a consumer) and F-6 correctly a checked
non-membership (no `using=` at this seam; index does not cover this file).
Zero-edit result: no observable-behavior change exists to prove, so principle 8
needs no execution — challenges with counts plus the standing oracles suffice.
`## Pending execution: None` is adequate: no ordering, transactional, or async
behavior is decided in this file, and the sharded/Postgres cells are
inapplicable by construction (no alias/`using=` decision, no dialect branch).

### Zero-edit + fingerprints (re-hashed)

`git diff f5e5896f1dabe9c11847bc431f0dd91bf5f9304c --
django_strawberry_framework/filters/base.py` is byte-empty (0 bytes); working
blob `ba52351c…` == `HEAD:filters/base.py` `ba52351c…`; target absent from
`git status --short` (clean). Artifact path is untracked (`??`), as expected
for a new artifact. No `docs/dry/temp-tests/` scratch created for this item
(all probes read-only: body inspection, `git grep` populations, AST walk) —
Worker 1's no-probe report is accurate and adequate. Concurrent dirt listed by
Worker 1 (connection.py hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) is untouched in the tree. Re-hashed fingerprints —
target `ba52351c`, `sets_mixins.py` `ad8987ea`, `orders/base.py` `4736fda0`,
`utils/querysets.py` `1539b66c`, `types/relay.py` `52439862`, `relay.py`
`c3c5aea5`, `filters/sets.py` `4ab65a26`, `filters/inputs.py` `82b52d97`,
`types/finalizer.py` `77fd9a2d`, `filters/__init__.py` `86b25818`, `HEAD`
`9031cb3d` — all match the artifact's claims.

### Rulings on the 2 new families

- F-7 `globalid-relation-pk-marker` — ENDORSED as its own family (not folded
into `typed-globalid-decode` or F-e). Distinct contract (boolean flag, never a
frozen path; derive-at-read) and distinct variation axis (new non-pk relation
shape → stamp predicate only) from target resolution/acceptance (F-e: new
strategy → owner sets) and from the write-side pk-mapper
(`relay.py::_resolve_real_pk`, a different seam). Single stamp site
(`filters/sets.py::FilterSet.filter_for_field` #"if _relation_uses_non_pk_to_field(field)"), single read/derive home, two read consumers —
verified by grep. Already single-sited; holding item for the cross-file rule.
- F-8 `globalid-decode-input-hardening` — ENDORSED as its own family (not
folded into `typed-globalid-decode`). That indexed family owns the write-side
typed-id pipeline (`relay.py::decode_model_global_id` + `DecodeResult`); F-8's
owner-side definition is the read-side `types/relay.py::decode_global_id`
(input gate + slot normalization), a different function with a different
contract. The gate is a separable responsibility with its own axis (which
shapes rejected, how slots normalized); folding the whole filter decode in
would conflate validation/coercion contracts. Routed to the family item with
trigger (wire-reachable non-`str` GlobalID input), not fixed here — correct.

### Rejections R1–R8

Each carries difference + trigger (+ home); all agree with the tree:
R1 deferred bases (sharing couples families + closes the cycle the deferral
keeps open; trigger: a third family still keeps its own — home: `_filter_set_class`
docstring); R2 per-family `_validate_target` gates (adapters by design —
suggest Worker 0 record the trigger as "filter/order families merge into one
set family" rather than "none"; prose nit, not a defect); R3 `get_queryset`
vs no order queryset (trigger: orders gaining querysets, no spec); R4 message
prefixes (context projections; code shared via `GLOBALID_INVALID_ERROR_CODE` +
`coded_error_extensions` — verified both sites use it); R5 range inline skip
vs materialize-reject (different contracts; trigger: range gaining a reject
contract); R6 twin docstring prose (explanation, out of population); R7
graphene/django-filter ports (external repos, out of population); R8
hostile-container mechanics vs exact-type pins (different shapes/contracts —
coded `GraphQLError` vs `ConfigurationError`, runtime filter vs normalize
boundary; trigger: a shared hostile-input policy owner). Negative controls:
no structural gates are owed — zero-edit file item; reused families already
fail closed through their owners; the two new families' gates belong to their
family items, and no bespoke existence test was created. Coupling: none to
mark (no landings).

### AGENTS.md prose check

Pass. No process provenance; citations use `path::Symbol` (no raw `path:NN`
hits by regex); reference-style links with the 10 canonical group headers and
a bottom `LINK DEFINITIONS` block; no production/test edits so no test-tier,
ruff, line-length, or changelog obligations arise; no pytest run (correct —
not authorized); concurrent dirt preserved.

### Defects (Worker 2)

None. Ruling on Worker 1's two released robustness observations (non-`str`
scalar reaching `relay.GlobalID.from_id` raising uncaught `TypeError`;
hand-built `GlobalID` with hostile `str`-subclass slots reaching unguarded
probes): AGREE they are not defects under the GOAL.md trust-boundary
rule. No contract row establishes the stricter rule for this entry (the
docstring's accepted pair is `(GlobalID, str)`, and the filter entry's
reachable input is form-cleaned data); no feasible project shape under
supported public API delivers them — the wire delivers `str` (GraphQL scalar
coercion), and direct-Python hostile calls are trusted application Python,
which the package explicitly does not promise to contain. Releasing them as
observations + family F-8 (rather than a defect or a behavior-changing guard
here) is the correct disposition.

### Verdict

`Status: verified`. Zero-edit file item: matrix discharged against the real
surface, 56/56 members assigned, challenges with definition counts, oracles
independent, fingerprints match, no defect, no pending execution.

## Run 0.0.15 2026-09-30-8 re-trace (Worker-1)

Scoped re-trace of queue item s7 at HEAD bytes. The run-7 artifact above is
prior evidence only: every finding below was re-derived against current HEAD
bytes with fresh `git grep HEAD` / `git show HEAD:` populations and an AST
enumeration. No production edits (file item, reviewer role).

ITEM_BASELINE `6c231d3e0825d717800a92ec665abbdc163c71d6` (WIP commit on
detached HEAD `83998e08`, intended). Item-scoped diff vs baseline for
`django_strawberry_framework/filters/base.py`: empty. No owned ledger hunk
names this file; all dirt is concurrent (attributed by diff content below).

### Freshness fingerprints

- HEAD blob `e2e683a8fabc5fac318ba2fa78abdf92c872973c` (1466 lines) — traced
  bytes. Every body cited below is HEAD bytes.
- Worktree hash `fc1cf61f3536c4f6ed916ad544c8f12c6afeeb5f` (1431 lines).
- `9aaaad5d` bytes blob `3b1dcbced1069e0faf1abeb33661e94a296f94ba`
  (1177 lines, "dry-0015 pre-ff snapshot", not an ancestor of HEAD).
- Drift base `0c0537e2` blob `ba52351c284425336262ae6c2b82b262f6586fc0`
  (1212 lines) — identical to the prior artifact's traced bytes.

`9aaaad5d` vs drift base on this target is 45+/80-, the same hunk shape as
HEAD-vs-worktree (verified: same 16 `@@` regions, 16 `truth.` refs,
0 `_safe_*` refs, 0 `RelationPk` mentions): the pre-merge snapshot is
drift-base bytes plus the concurrent truth/containment dirt, and the
worktree is HEAD bytes plus that same dirt. Neither was traced; both are
read-only attribution evidence.

Connected sources (HEAD blobs, all traced via `git show HEAD:` because the
worktree copies are concurrently dirty): `filters/sets.py` `3d307402`,
`filters/inputs.py` `2c853e24`, `orders/base.py` `d4cc9129`,
`sets_mixins.py` `6764d455`, `utils/querysets.py` `392e50d0`,
`types/relay.py` `968fb95a`, `relay.py` `a09485a1`,
`types/finalizer.py` `cb2dde6b`, `filters/__init__.py` `8ce8b96d`,
`utils/typing.py` `1ce032f1`, `utils/errors.py` `793855e0`;
oracles `tests/filters/test_base.py` `2c507b75`,
`tests/filters/test_sets.py` `19d508bd`,
`tests/filters/test_inputs.py` `769e7b45`.

### Dirt attribution by diff content

HEAD-vs-worktree (45+/80-, all concurrent, none traced): a `utils/truth.py`
migration (`getattr` → `truth.static_attr`, `_safe_*` → `truth.*`, new
`truth` import) plus removal of the hostile-container containment
(`_materialize_list_shaped_values` try/except, `ArrayFilter.filter` probe
guard, `IntegerRangeFilter.filter` materialize guard) with matching
docstring rewrites. No owned ledger row covers it.

Drift-base-vs-HEAD (310+/56-, 35 hunks, the re-trace subject): the two
behavior commits from the queue brief plus typing-only drift. Verified
hunk by hunk: every hunk outside the two behavior bodies is
annotations / `@override` / casts / `TYPE_CHECKING` / comments with zero
body change (the full non-behavior hunk list was read; no `return` / branch
/ call changed). Behavior bodies:

- `bbe54687`: `relation_identity_column`,
  `_relation_identity_column_for`, `_coerce_relation_identity`,
  `_RelationIdentityListField`, `RelationPkFilter`,
  `RelationPkMultipleFilter`; the marker comment gains the raw-pk-sibling
  sentence; module docstring gains the sibling bullet.
- `57131b99`: `relation_identity_column` delegates to the new
  `_model_identity_column`; new `model_choice_identity_column`.

Correction to the brief's paraphrase: at HEAD bytes
`relation_identity_column` still returns `None` for a non-relation (the
`is_relation` guard is intact); the queryset-model read lives in
`model_choice_identity_column` (queryset `model`, callable-queryset
fallback to the relation target). The brief's "accepts a non-relation
queryset" describes the `model_choice_identity_column` source, not a
`relation_identity_column` shape change (verified: the bbe54687 body and
the HEAD body differ only by delegation to `_model_identity_column`).

### Enumeration (fresh, HEAD bytes)

Instrument: same as run 7 — top-level `ClassDef` / `FunctionDef` /
`Assign` in `ast.Module.body` plus every method (`FunctionDef` under a
`ClassDef`), executed against HEAD bytes. Module body: 63 statements =
1 docstring + 18 imports + 4 assigns + 1 `TYPE_CHECKING` block +
19 classes + 20 functions. Excluded scaffolding with reason: the module
docstring (projection), 18 imports (references, not definitions; 17 at
drift base + `typing_extensions.override`), the `TYPE_CHECKING` block
(type-only). **Count: 43 tops + 25 methods = 68 members** (56 at drift
base + 12: 5 functions, 3 classes, 3 methods, 1 `_M` TypeVar assign).
Every member assigned below (F = family incl. proposed, L = file-local,
R = rejection, D = defect note).

| # | Member(s) | Home (run 8) |
|---|---|---|
| 1 | `FRAMEWORK_GLOBALID_STRATEGIES` | F-e (union by name, unchanged) |
| 2 | `ENCODE_ONLY_GLOBALID_STRATEGIES` | F-e (intentional literal, unchanged) |
| 3 | `_M` | scaffolding (TypeVar binding, no rule) |
| 4 | `TypedFilter` | L-a (marker port) |
| 5 | `_EmptyListAwareFilterMethod` + `__call__` | F-a |
| 6 | `_install_empty_list_aware_method` | F-a |
| 7 | `_apply_lookups` | F-b (3 call sites now) |
| 8 | `_apply_lookup_predicate` | F-b (4 call sites now; D1 census note) |
| 9 | `_match_none_queryset` | F-c (5 call sites now; D1 census note) |
| 10 | `_materialize_list_shaped_values` | F-d (4 call sites now; D1 census note) |
| 11 | `_globalid_multiple_choice_values` | F-d (thin wrapper) |
| 12 | `_GLOBALID_RELATION_PK_ATTR` | F-7 (flag now carried by 4 filter classes) |
| 13 | `_relation_uses_non_pk_to_field` | F-7 (single stamp predicate) |
| 14 | `_marked_pk_field_name` | F-7 (single read/derive home; 4 consumers; D1) |
| 15 | `ArrayFilterMethod` | F-a (parity identity) |
| 16 | `ArrayFilter` + `method` + `filter` | F-a / F-b / L-a (containment intact at HEAD) |
| 17 | `validate_range` | L-a |
| 18 | `_RangeWidget` + `__init__` + `decompress` | F-g |
| 19 | `RangeField` + `to_python` | F-g |
| 20 | `RangeFilter` | L-a |
| 21 | `ListFilterMethod` | F-a |
| 22 | `ListFilter` + `method` + `filter` | F-a / F-d / F-c |
| 23 | `_coerce_int_in_members` | F-1 (consumer) |
| 24 | `IntegerInFilter` + `filter` | F-d / F-c / F-1 + F-10 (walk half) |
| 25 | `IntegerRangeFilter` + `filter` | F-b / R5 (containment intact at HEAD) |
| 26 | `_target_definition_for` | F-e |
| 27 | `resolve_globalid_target_definition` | F-e (finalizer still consumes by name) |
| 28 | `_accepted_globalid_type_names` | F-e |
| 29 | `_decode_and_validate_global_id` | F-e / F-1 / F-8 / R4 (body unchanged) |
| 30 | `GlobalIDFilter` + `filter` | F-e / F-7 / F-b |
| 31 | `_AbsentGlobalIDMultipleChoiceWidget` + `value_from_datadict` | F-h (2 field consumers now) |
| 32 | `_GlobalIDMultipleChoiceField` + 3 methods | F-h |
| 33 | `GlobalIDMultipleChoiceFilter` + `filter` | F-d / F-c / F-e / F-7 / F-b |
| 34 | `relation_identity_column` | F-9 NEW (relation→column; 2 consumers) |
| 35 | `_model_identity_column` | F-9 NEW (follow-loop owner; 2 callers) |
| 36 | `model_choice_identity_column` | F-9 NEW (queryset/relation→column; 1 consumer) |
| 37 | `_relation_identity_column_for` | F-9 + F-10 NEW (walk half + identity reader) |
| 38 | `_coerce_relation_identity` | F-9 + F-1 NEW (owner-composing coercion) |
| 39 | `_RelationIdentityListField` + `to_python` | F-h (widget) + R11 NEW (to_python separation) |
| 40 | `RelationPkFilter` + `filter` | F-7 / F-b / F-c / F-9 NEW |
| 41 | `RelationPkMultipleFilter` + `filter` | F-7 / F-d / F-c / F-9 + R9 / R10 NEW |
| 42 | `_filter_set_class` | R1 (mirror drift typing-only) |
| 43 | `RelatedFilter` + 6 methods | F-2 / F-3 / F-4 / L-b / R2 + R3 |

Static zero-probe at HEAD bytes (definitions in target):
`resolve_lazy_class`, `_bind_owner`, `_resolved_target`, `_set_target`,
`collect_related_declarations`, `run_in_one_sync_boundary`, `model_for`,
`import_string`: 0 each. `async def` / `await`: 0. The one
`get_queryset` token inside the RelationPk region is docstring prose, not
a method. No second owner for any indexed family machinery.

### Matrix (current target)

1. **Cross-flavor mirroring** — searched. Orders mirror re-read whole at
HEAD: drift is typing-only (annotations/`@override`/cast/`_OrderSetTarget`
alias), still 0 `queryset`/`get_queryset` tokens. R1/R2/R3 separations
stand. The RelationPk pair has no orders twin (orders carry no identity).
`model_choice_identity_column` vs
`django_strawberry_framework/forms/resolvers.py::_to_form_key_value`: same
`to_field_name` vocabulary, opposite directions (key→column at type time
vs object→key at write time) — new rejection R12. The
`extra.get("to_field_name")` read is single-sited package-wide.
2. **Sync/async twins** — inapplicable with reason: 0 `async def` /
`await` at HEAD bytes, no `run_in_one_sync_boundary` import or call;
django-filter bodies stay inside the boundary owned by
`django_strawberry_framework/filters/sets.py::FilterSet.apply_async`.
3. **Derived knowledge** — searched. `FRAMEWORK_GLOBALID_STRATEGIES`
still unions the owners by name; `_marked_pk_field_name` still derives at
filter time. Every new identity link composes by name:
`relation_identity_column` → `_model_identity_column`,
`model_choice_identity_column` → `_model_identity_column`,
`_relation_identity_column_for` → `relation_identity_column`,
`_coerce_relation_identity` → `_relation_identity_column_for` +
`coerce_field_value_or_none`. The FK-follow `while` loop is single-sited
(the `lateral_fetch.py` `target_field` reads are spec fields, not a
follow loop). The ONE re-derivation: `_relation_identity_column_for`
re-spells the bound-filter walk `IntegerInFilter.filter` uses — new
family F-10 (`django_strawberry_framework/filters/inputs.py::_model_field_for_filter`
is the related third spelling on a different root/seam; named in the
family for Worker-0).
4. **Round-trip pairs** — searched. Range positional producer/consumer
unchanged. Omission chain extended: `_AbsentGlobalIDMultipleChoiceWidget`
now serves 2 fields by reference (no copy). `_RelationIdentityListField`
vs `MultipleChoiceField.to_python`: Django str-coerces members; the new
field preserves them so column coercion sees typed values — intentional
separation R11. Encode/decode halves still share
`resolve_globalid_target_definition` by name in both directions
(`types/finalizer.py::_audit_globalid_filter_strategies` + runtime). RelationPk-multi always-`__in` vs
GlobalID-multi lookup-honoring — intentional separation R9.
5. **Contracts in another medium** — searched. New oracles spell literal
expectations: `tests/filters/test_base.py` (isinstance selection, marker
stamping, pk/title behavior), `test_factories.py` / `test_inputs.py` /
`test_sets.py` (generation + annotation), live
`examples/fakeshop/test_query/test_scalars_filter_api.py` (raw-pk wire
values) and `test_library_api.py` (declared model-choice). No oracle
computes expectations from an owner (`relation_identity_column` direct
tests assert the target itself, the run-7 precedent). Projections: module
docstring + commit-message prose + README/GLOSSARY relation-key rows
(describe, never define). Five docstrings undercount their consumers —
defect D1 (projections contradicting bodies).
6. **Enforcement by omission** — enumerated. `_match_none_queryset`
serves 5 producers (was 3); materialize gate serves 4 (was 3);
`method=` swap still exactly Array/List (RelationPk-multi follows the
GlobalID-multi precedent of no setter — consistent, no omission);
`IntegerRangeFilter` skip still the different contract (R5); scalar
RelationPk needs no shape gate (scalar precedent);
`filters/__init__.py` exports unchanged (RelationPk follows the
IntegerIn/IntegerRange generated-only precedent — consistent). No
contract source establishes a missing guard: no defect.

### CONFIRM / REVISE per prior finding

- **F-1 `field-value-coercion`** — CONFIRM + extend: third consumer
  `django_strawberry_framework/filters/base.py::_coerce_relation_identity`
  composes `coerce_field_value_or_none` by name (3 call sites in target:
  int members, GlobalID decode, relation identity). Which-field stays at
  callers per owner contract.
- **F-2 `lazy-related-class-resolution`** — CONFIRM: still pure re-export
  + indirect consumer; zero new `resolve_lazy_class` references.
- **F-3 `related-set-target-lifecycle`** — CONFIRM: `RelatedFilter`
  drift is typing-only; mirror adapter unchanged in shape.
- **F-4 `queryset-seed-and-model-read`** — CONFIRM + note:
  `RelatedFilter.get_queryset` still seeds via `base_queryset(model)`
  without `using=`; `resolve_globalid_target_definition` still
  single-sited and consumed by the finalizer audit by name. The
  IntegerInFilter walk half of this finding is now shared with
  `_relation_identity_column_for` — carried as new family F-10.
- **F-5 / F-6** — CONFIRM non-membership (not consumers; no alias
  decision at either seam; RelationPk adds no `get_queryset`).
- **F-7 `globalid-relation-pk-marker`** — CONFIRM rule, REVISE census.
  This file's side (the s19 family re-trace owns the family row): the
  flag READ is still single-sited — exactly 1 production `getattr` on
  `_GLOBALID_RELATION_PK_ATTR`, inside `_marked_pk_field_name`. The two
  RelationPk filters are consumers composing the marker home by name, not
  new definitions: `_marked_pk_field_name` call sites 2→4
  (`GlobalIDFilter.filter`, `GlobalIDMultipleChoiceFilter.filter`,
  `RelationPkFilter.filter`,
  `RelationPkMultipleFilter.filter` — the last composes as
  `_marked_pk_field_name(self) or self.field_name`). The stamp is still
  single-sited (`filters/sets.py::FilterSet.filter_for_field`, predicate
  call + `setattr`, covering `type(default)` for both GlobalID and
  raw-pk primitives). No new definition of stamp, flag, or derivation.
- **F-8 `globalid-decode-input-hardening`** — CONFIRM: decode body
  byte-identical apart from the `-> object` annotation; the asymmetry
  routing stands (family item verified zero-edit per the plan).
- **F-a `empty-list-aware-method-install`** — CONFIRM (typing-only).
- **F-b `whole-value-lookup-application`** — CONFIRM mechanics, REVISE
  census: `_apply_lookup_predicate` call sites 3→4 (+RelationPkFilter);
  `_apply_lookups` call sites 2→3 (+RelationPkMultipleFilter).
- **F-c `restrictive-empty-match-none`** — CONFIRM mechanics, REVISE
  census: call sites 3→5 (+RelationPkFilter, +RelationPkMultipleFilter).
- **F-d `list-shape-fail-closed-materialization`** — CONFIRM mechanics,
  REVISE census: call sites 3→4 (+RelationPkMultipleFilter).
- **F-g `range-positional-round-trip`** — CONFIRM (untouched).
- **F-h `globalid-multi-omission-chain`** — CONFIRM chain, REVISE
  census: widget consumers 1→2 (+`_RelationIdentityListField` by
  reference); the new field's `to_python` is intentionally separate
  (R11).
- **F-e `globalid-target-resolution-and-acceptance`** — CONFIRM
  (untouched; union still by name).
- **L-a `typed-port surface`** — CONFIRM: the `ArrayFilter.filter`
  hostile-`__eq__` containment is intact at HEAD bytes (its removal
  exists only in concurrent worktree dirt, out of scope).
- **L-b `related-explicit-queryset-intent`** — CONFIRM (typing-only).
- **R1–R8** — all CONFIRM on fresh evidence: mirror drift typing-only
  (R1/R2/R3); message-code sharing intact (R4); range skip still the
  different contract with containment intact at HEAD (R5); prose still
  out of population (R6); graphene ports still external (R7); orders
  hostile-input shape still the separate fail-closed spelling (R8).

### Identity-column readers: verdict

Single-sited at every link, composing by name throughout. Caller counts
(production, HEAD): `_model_identity_column` ← 2
(`relation_identity_column`, `model_choice_identity_column`);
`relation_identity_column` ← 2 (`_relation_identity_column_for`,
`filters/inputs.py::_relation_identity_annotation`);
`model_choice_identity_column` ← 1
(`filters/inputs.py::_model_choice_identity_annotation`);
`_relation_identity_column_for` ← 1 (`_coerce_relation_identity`);
`_coerce_relation_identity` ← 2 (both RelationPk `filter` bodies). No
second definition of any link (`git grep HEAD` populations above); the
FK-follow loop has exactly one spelling. Named as new family F-9 for
Worker-0 (already single-sited; holding row for the cross-file rule, the
F-7 precedent).

### Challenges (definition counts)

- New relation-valued key shape in identity resolution →
  `_model_identity_column` only = 1 (both public helpers follow).
- New identity model source (e.g. runtime queryset read for the RelationPk
  path) → `_relation_identity_column_for` = 1; build-time source change →
  `model_choice_identity_column` = 1.
- Bound-filter parent-binding change → `IntegerInFilter.filter` +
  `_relation_identity_column_for` = 2 → new family F-10.
- New non-pk relation shape → `_relation_uses_non_pk_to_field` = 1;
  derivation follows; a fifth marked consumer composes the home = 0 new
  definitions.
- Raw-pk scalar uncoercible verdict (match-none → raise) →
  `RelationPkFilter.filter` = 1 (GlobalID malformed-raise is the
  different input class, R13).
- Raw-pk multi member verdict (drop → reject) →
  `RelationPkMultipleFilter.filter` = 1; all-dropped / explicit-`[]`
  verdict → shared `_match_none_queryset` = 1 (moves all 5 producers by
  construction, intended).
- New accepted list container → `_materialize_list_shaped_values` = 1
  (4 consumers follow); omission-widget behavior →
  `_AbsentGlobalIDMultipleChoiceWidget` = 1 (2 fields follow).
- Per-field member coercion (preserve vs str) → intentionally 2 (R11);
  multi `__in`-always vs lookup-honoring → intentionally 2 (R9);
  explicit-`[]` match-none (RelationPk-multi) vs skip (IntegerIn) →
  intentionally 2 contracts (R10).

All probes static-reviewed (HEAD-bytes body inspection, `git grep HEAD`
populations, AST walk). No mutating proof was needed: no ordering,
transactional, or async behavior is decided in this file. No
`workspace.py` run, no shared-tree test run (the authorized focused test
is unneeded for a zero-edit file item whose every claim is a HEAD-bytes
count or body reading).

### New families / rows for Worker-0 (plan edits are Worker-0's)

- **F-9 `relation-identity-column`** (NEW FAMILY): relation/queryset →
  identity-column resolution. Owner: the base.py trio
  (`relation_identity_column` + `_model_identity_column` +
  `model_choice_identity_column`). Consumers: `filters/inputs.py` (2
  annotation arms) + the runtime `_relation_identity_column_for` /
  `_coerce_relation_identity` chain (2 RelationPk bodies). Already
  single-sited; holding row for the cross-file rule.
- **F-10 `bound-filter-model-field-walk`** (NEW FAMILY): the
  parent→`_meta.model`→`get_model_field` derivation spelled twice at
  runtime (`IntegerInFilter.filter`, `_relation_identity_column_for`;
  the new helper's own docstring claims "the same walk
  `IntegerInFilter.filter` uses"). Owner candidate: base.py (both
  consumers live here; `inputs.py` cannot host — it imports from base.
  `inputs.py::_model_field_for_filter` is the related third spelling on
  a class root at build time; named in the family, not counted with the
  runtime pair). Challenge count 2.
- **R9** always-`__in` (RelationPk-multi) vs lookup-honoring
  (GlobalID-multi): different contracts (many-side `exact` means
  related-to-any); trigger: a shared multi-predicate policy owner.
- **R10** explicit-`[]` match-none (RelationPk-multi, README membership
  rules) vs skip (IntegerIn, django-filter default): different contracts;
  trigger: unifying the membership rules.
- **R11** `_RelationIdentityListField.to_python` member preservation vs
  `MultipleChoiceField.to_python` str-coercion: different contracts (raw
  pks must stay typed for column coercion); trigger: none (upstream
  shape).
- **R12** `model_choice_identity_column` (key→column, type time) vs
  `forms/resolvers.py::_to_form_key_value` (object→key, write time):
  opposite directions; trigger: a shared to-field policy owner.
- **R13** RelationPk scalar uncoercible → match-none vs GlobalID
  malformed → raise: different input classes (names-no-row vs
  wire-format error); trigger: a shared invalid-value policy owner.

### Defects (run 8)

- **D1 (filters/base.py owner; docstring censuses undercount consumers
  after the drift).** Five projections contradict their bodies at HEAD
  bytes: the `_GLOBALID_RELATION_PK_ATTR` comment block ("`GlobalIDFilter.filter` /
  `GlobalIDMultipleChoiceFilter.filter` read it" — now 4 readers via the
  home); `_marked_pk_field_name` ("shared by ..." naming 2 — now 4);
  `_materialize_list_shaped_values` ("Shared by ..." naming 3 — now 4);
  `_match_none_queryset` ("shared by ..." naming 3 — now 5);
  `_apply_lookup_predicate` ("the two call sites" — now 4; already 3 at
  drift base, so this census predates the drift). No behavior is wrong;
  each miscounted census is a docstring-contradicts-body record for
  Worker-0 homing. Never fixed inside this item.

### Pending execution

None. Every proof is static-reviewed; no ordering / transactional / async
behavior is decided here, so no execution-deferred entry exists. The
sharded/Postgres cells are inapplicable by construction (no alias/
`using=` decision, no dialect branch in this file).

### Judgment (run 8)

Zero-edit re-trace: matrix discharged against the current surface (orders
mirror re-read at HEAD, async absence re-verified, identity/marker
populations counted at HEAD bytes), 68/68 members assigned (2 new
families named, 5 new rejections with difference + trigger, remainder
CONFIRM or census-REVISE of run-7 rows), challenges recorded with
definition counts, one doc-only defect filed, no pending execution. The
drift's two behavior bodies compose the existing single-sited helpers by
name at every link (identity chain, marker home, shape gate, match-none,
predicate seam); the one genuine re-derivation (F-10) and the five stale
censuses (D1) are routed out, not fixed here.

### Implementation (run 8)

No production edits (file item; reviewer role — no edit rights on
production code). No new tracked files besides this artifact (untracked
`??`, as in run 7). Item-scoped diff vs `ITEM_BASELINE`
`6c231d3e0825d717800a92ec665abbdc163c71d6` for
`django_strawberry_framework/filters/base.py`: empty. The worktree's
45+/80- on the target is concurrent truth/containment dirt, attributed by
content above and untouched. No pytest run (a zero-edit file item needs
none; the one authorized focused test is unneeded). No `workspace.py`
runs (no source-mutating proof exists for this target). No scratch files
(all probes read-only: `git show HEAD:`, `git grep HEAD`, AST walk on
HEAD bytes, installed-`.venv` source read for Django's
`MultipleChoiceField.to_python`).

## Run-8 verification (Worker 2)

Traced at HEAD `83998e08` bytes against
`ITEM_BASELINE 6c231d3e0825d717800a92ec665abbdc163c71d6`. No
worker-memory read; sources were HEAD bytes (`git show HEAD:`), HEAD
populations (`git grep HEAD`), the installed Django source for one upstream
body, and two AST instruments of my own. Worktree bytes were read only for
dirt attribution. All line numbers below are HEAD lines of
`django_strawberry_framework/filters/base.py` unless named otherwise.

### Fingerprints (re-hashed)

- Target: HEAD blob `e2e683a8` (1466 lines) is the traced bytes; worktree
  `fc1cf61f` (1431 lines); drift base `0c0537e2` blob `ba52351c` (1212
  lines, identical to the run-7 traced bytes); pre-merge `9aaaad5d` blob
  `3b1dcbce` (1177 lines). All match the re-trace record.
- Connected sources re-hashed, all match: `filters/sets.py` `3d307402`,
  `filters/inputs.py` `2c853e24`, `orders/base.py` `d4cc9129`,
  `types/relay.py` `968fb95a`, `types/finalizer.py` `cb2dde6b`,
  `tests/filters/test_base.py` `2c507b75`,
  `tests/filters/test_sets.py` `19d508bd`.
- Item-scoped diff `git diff 6c231d3e... -- filters/base.py` is 0 bytes.
  No `## Owned changes` row names this file.

### Own trace of the drift delta (expectation-first)

Expected from the queue brief: two behavior bodies (the raw-pk relation key
with its marker-carrying RelationPk pair; the ModelChoice identity arms)
atop typing-only drift. My instrument: per-symbol AST dump with docstrings,
annotations, decorators, bases, `cast` wrappers, and the `_M` TypeVar
binding stripped, drift base vs HEAD. Result: all 31 pre-existing top-level
symbols stripped-identical, zero deletions, HEAD adding exactly 8 symbols
(`relation_identity_column`, `_model_identity_column`,
`model_choice_identity_column`, `_relation_identity_column_for`,
`_coerce_relation_identity`, `_RelationIdentityListField`,
`RelationPkFilter`, `RelationPkMultipleFilter`). Module assigns unchanged
except the new `_M`; the strategy union and the marker constant are
byte-identical modulo line shift. `git log 0c0537e2..HEAD` on the target
names exactly the two behavior commits plus five typing commits. The drift
is therefore purely additive behavior plus typing/prose — a mechanical form
of the re-trace's hunk-by-hunk reading — and it CONFIRMs the brief
correction (the `is_relation` guard is intact: non-relations still return
`None`).

### Own counts (re-derived, HEAD bytes)

- Marker flag: 1 production `getattr` read (:327, inside
  `_marked_pk_field_name`); 1 production `setattr` stamp
  (`filters/sets.py:1790`, inside `filter_for_field`, guarded by the
  predicate at :1789); predicate production callers: 1; `__pk` code
  spelling: 1 (:330; every other hit is prose, and the nested_planner hit
  is unrelated prose). `_marked_pk_field_name` call sites: 4, owned by
  `GlobalIDFilter.filter` (:953), `GlobalIDMultipleChoiceFilter.filter`
  (:1096), `RelationPkFilter.filter` (:1237),
  `RelationPkMultipleFilter.filter` (:1275).
- Identity chain: `_model_identity_column` called from 2 sites;
  `relation_identity_column` from 2 (:1166 plus `filters/inputs.py:365` in
  `_relation_identity_annotation`); `model_choice_identity_column` from 1
  (`filters/inputs.py:399` in `_model_choice_identity_annotation`);
  `_relation_identity_column_for` from 1; `_coerce_relation_identity` from
  2 (:1234, :1270). FK-follow `while` loop: 1 spelling.
- Predicate seam: `_apply_lookup_predicate` 4 (:397/:955/:1097/:1237),
  `_apply_lookups` 3 (:200 self-composition/:659/:1276). Match-none: 5
  (:514/:604/:1080/:1236/:1274). Materialize gate: 4 (:255 wrapper/:508/
  :580/:1263). Omission widget: 2 by reference (:1003/:1194). Field-value
  coercion: 3 (:541/:898/:1179).
- `method` setters: exactly `ArrayFilter` (:370) plus `ListFilter` (:487).
  Async tokens: 0. `run_in_one_sync_boundary` refs: 0. Imports 17→18
  (`typing_extensions.override` only). `extra.get("to_field_name")`: 1
  package-wide (:1150).

### Per-row judgments

Every row below is CONFIRM on my own evidence unless noted; counts are
mine from the section above.

- F-1 CONFIRM + extend (third consumer :1179 composes the owner by name).
- F-2, F-3 CONFIRM (re-export :49 intact; `RelatedFilter`
  stripped-identical).
- F-4 CONFIRM + note (seed call unchanged; the walk half is carried to
  F-10).
- F-5/F-6 CONFIRM non-membership (0 async/boundary tokens; the one
  `get_queryset` token in the RelationPk region is docstring prose).
- F-7 CONFIRM rule, REVISE census (single read site, single stamp site,
  2→4 consumers — each re-derived above).
- F-8 CONFIRM (`_decode_and_validate_global_id` stripped-identical).
- F-a CONFIRM; F-b/F-c/F-d CONFIRM mechanics plus the censuses above;
  F-g CONFIRM; F-h CONFIRM plus 1→2; F-e CONFIRM (union by name :72; the
  finalizer consumes `resolve_globalid_target_definition` by name at
  `types/finalizer.py:1968`/:1977).
- L-a CONFIRM (`ArrayFilter.filter` probe guard, `IntegerRangeFilter.filter`
  shape plus materialize guard, and the `_materialize_list_shaped_values`
  try/except are all intact at HEAD); L-b CONFIRM.
- R1–R8 CONFIRM (`orders/base.py` stripped-identical drift→HEAD with 0
  queryset tokens; R4 code shared at :258/:844/:893/:904; R5 containment
  intact; R6 prose; R7 import delta typing-only; R8 orders shape present).

### Adversarial focus

1. F-7 — challenged all three legs. Read-single-site: test-side
   getattr/setattr spell the flag to set up and assert stamping —
   independent oracles, not definitions. Stamp-single-site: read the
   `filters/sets.py` site myself (predicate call plus setattr inside
   `filter_for_field`; the `type(default)` comment covers the GlobalID and
   raw-pk primitives). Census 2→4: owning classes re-derived. The `:1275`
   fallback spelling composes the home. Verdict stands.
2. F-9 — holding row OWED. The bar (DRY.md inventory backstop): a finding
   naming a second site is a family or a rejection, never file-local. The
   rule spans base.py (trio plus runtime chain) and inputs.py (two
   annotation arms selecting between the two public helpers — genuine
   cross-file definition, not one-line consumption, which separates it
   from the artifact-local F-e treatment and matches the F-7 precedent).
   Owner (base.py trio) correct by import direction: inputs.py imports
   from base.py.
3. F-10 — count-2 CONFIRM. Read both spellings: common core
   parent→`_meta`→model→`get_model_field`. The None-policy difference
   (one side asserts non-None per its mypy note, the other guards) is
   defensive spelling at the same filter-time seam — same reachable
   contract. `inputs.py::_model_field_for_filter` correctly EXCLUDED from
   the count: class root at build time vs bound instance at filter time
   (different roots, different lifetimes). Owner candidate base.py
   correct: inputs.py already imports from base.py, so hosting the shared
   walk there would reverse the dependency. Record gaps C1/C2 below move
   nothing.
4. R9–R13 — each disputed, each held. R9: always-`__in` (:1276) vs
   lookup-honoring (:1081–1084) is a real predicate-selection difference;
   terminal application is already shared via `_apply_lookups`, so the
   stated separation point is accurate; trigger sound. R10: probed the
   README membership sentence as a same-contract source — released: the
   IntegerIn skip dates to 06-26 with explicit reasoning, the README
   sentence (07-11) left it intact, and the integer-`in`-specific rule
   beside it scopes to all-invalid inputs; specific governs general. No
   defect. R11: Django's `to_python` str-coercion verified in installed
   source; the preservation contract is genuine; trigger wording C3. R12:
   directions verified (key→column at type time vs object→key at write
   time); trigger sound. R13: match-none (:1235–1236) vs decode-raise
   follows the coercion/decode contracts; trigger sound.
5. D1 — all five miscounts verified at HEAD bytes (ATTR comment block
   naming 2 readers; `_marked_pk_field_name` "two siblings";
   `_materialize_list_shaped_values` "three list-shaped consumers";
   `_match_none_queryset` naming 3; `_apply_lookup_predicate` "two call
   sites"). The fifth was already 3 at drift base (verified:
   :361/:896/:1032 there) — the pre-drift note is accurate. Doc-only,
   minor, moves nothing. Homing: ENDORSE Worker-0 homing the doc-only
   repair to the closeout homing pass; the `_materialize_list_shaped_values`
   paragraph is concurrently rewritten in the worktree, so the repair is
   authored against HEAD bytes with the closeout pass confirming whether
   the landed rewrite carries it (relay-D1 precedent).

### Enumeration (member-by-member)

My instrument (top-level ClassDef/FunctionDef/Assign plus methods): 63
module statements = 1 docstring + 18 imports + 4 assigns + 1 TYPE_CHECKING
block + 19 classes + 20 functions; 43 tops + 25 methods = 68. Every one of
my 68 maps onto a re-trace row 1–43 exactly once (method folds in rows
5/16/18/19/22/24/25/30/31/32/33/39/40/41/43 hold
1+2+2+1+2+1+1+1+1+3+1+1+1+1+6 = 25). Exclusions justified as in run 7.
68/68 assigned, none doubled.

### Matrix

All six axes discharged against the real surface — agree on each, on my
own evidence above (orders mirror re-derived stripped-identical; async
absence re-verified; identity links compose by name; omission chain
extended by reference; oracles literal, including direct-target identity
tests and live raw-pk/model-choice coverage; `method=` swap exactly
Array/List; RelationPk follows the IntegerIn/IntegerRange generated-only
export precedent — `filters/__init__.py` exports neither).

### Dirt attribution

HEAD-vs-worktree 45+/80- in 16 regions, all concurrent-external: no ledger
row names this file, and added-line vocabulary is confined to the truth
migration (`truth.*`, narrowed imports) and the containment removal (guard
deletions plus docstring rewrites). No new definition, call, or branch.
Behavior-site contact (worktree bytes differ; the HEAD-bytes trace is
unaffected, out of scope): `_materialize_list_shaped_values` body,
`ArrayFilter.filter` guard, `IntegerRangeFilter.filter` guard,
`_relation_uses_non_pk_to_field` reader, `IntegerInFilter.filter` reader
plus docstring, `_decode_and_validate_global_id` message spellings,
`RelatedFilter` message spellings. The pre-merge `9aaaad5d` bytes served
read-only attribution and no verdict depends on them.

### Defects (Worker 2)

None. D1 endorsed as filed (see homing above).

### Record-precision notes (no resubmission; move no verdict, index row, or decision)

- C1: F-10's record should name `filters/sets.py:1548` (`get_fields`
  `"__all__"` expansion: `model = cls._meta.model`, a direct class-root
  read with no parent walk) as examined-and-excluded — a fourth
  `get_model_field` call the family record never mentions. Exclusion
  correct (different root/seam); the family item needs the note.
- C2: F-10's inputs.py exclusion states its contract difference but owes
  a reconsideration trigger (e.g. a shared (model, field) resolution seam
  spanning build and filter time).
- C3: R11's trigger ("none") should name the upstream change that would
  reopen it (Django changing `MultipleChoiceField.to_python` member
  handling), per the run-7 R2 handling.

### Pending execution

None. Every proof is HEAD-bytes body inspection, HEAD populations, or AST
comparison; no ordering/transactional/async behavior is decided here. The
sharded and Postgres cells are inapplicable by construction (no
alias/`using=` decision, no dialect branch) — agreed.

### Verdict

`Status: verified`. Zero-edit re-trace: matrix discharged, 68/68 members
assigned, every verdict row survives on independent evidence with my own
counts, one doc-only defect endorsed for closeout homing, no pending
execution. Family impact: F-9 holding row endorsed as named; F-10 new
family endorsed with count 2 (C1/C2 note-shaped for the family item);
F-7 consumer evidence carried to s19 as recorded; R9–R13 stand as
rejections; zero owned changes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[relay]: ../../django_strawberry_framework/relay.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-filter-sets]: ../../tests/filters/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
