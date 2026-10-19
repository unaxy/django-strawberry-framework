# DRY review: `filters/inputs.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Target owns the filter input namespace
(`django_strawberry_framework/filters/inputs.py`, 1073 lines, blob `82b52d97`;
absent from `git status --short`, target CLEAN): the one lookup-spelling grammar
table (`LOOKUP_NAME_MAP`), the logical-operator vocabulary
(`LogicOperatorDescriptor` + `LOGIC_OP_*` + `LOGIC_OPERATORS` + both derived
maps), the convert/normalize kind ladder (`_FILTER_INPUT_KIND_TYPES` + strict-zip
prechecks + fallthrough), the converter/normalizer twin passes
(`convert_filter_to_input_annotation` / `normalize_input_value`) with their
scalar/enum/range/GlobalID/list-guard helpers, the per-filterset operator-bag +
logic-field builders (`_build_input_fields` / `_build_logic_fields` /
`construct_search`), the Decision-9 namespace quartet binding
(`_materialized_names` / `_field_specs` / `materialize_input_class` /
`clear_filter_input_namespace` + the `register_subsystem_clear` row), and the
domain-alias re-exports (`FieldSpec` / `build_input_class` / `_camel_case` /
`_iter_filterset_subclasses` / `_input_type_name_for`).

Traced end to end, orders twin FIRST (whole `orders/inputs.py`, 395 lines, blob
`6f6ec946`): identical substrate-alias shape, identical heavy-quartet binding
with disjoint family params, identical `before_bind=True` registration with
disjoint owners, identical `emit_set_input_field_triples` scaffold — and five
documented divergences (rejections R-a..R-e). Owner bodies in
[utils/inputs.py][utils-inputs] (`make_set_input_namespace`,
`emit_set_input_field_triples`, `GeneratedInputFieldSpec`,
`build_strawberry_input_class`, `set_input_type_name`, `optional_field_kwargs`,
`iter_set_subclasses`, `convert_with_mro` via [utils/converters.py][utils-converters]),
naming owner in [sets-mixins.py][sets-mixins] (`ClassBasedTypeNameMixin.type_name_for`)
plus [utils/strings.py][utils-strings] (`graphql_camel_name`,
`pascal_case_or_raise`), reverse-grammar + normalizer consumer in
[filters/sets.py][filters-sets] (`_FORM_KEY_BY_PYTHON_ATTR`,
`_form_key_for_python_attr`, `_normalize_input`, `_permission` traversal,
`_LOGIC_PYTHON_ATTRS`), hook consumer in
[filters/factories.py][filters-factories] (`FilterArgumentsFactory._build_input_triples`
splicing `_build_input_fields` + `_build_logic_fields`), lazy-ref consumer in
[filters/__init__.py][filters-init] (`filter_input_type` via `INPUTS_MODULE_PATH`),
scalar/enum delegates in [types/converters.py][types-converters]
(`scalar_for_field`, `convert_choices_to_enum`), name-attribute reader in
[types/definition.py][types-definition] (`graphql_type_name`), GlobalID
validate-side in [filters/base.py][filters-base], setting reader in
[conf.py][conf] (`hide_flat_filters_setting`), sentinel classifier in
[input-values.py][input-values] (`is_inactive_value`), oracles in
[test-filter-inputs.py][test-filter-inputs] (1689 lines) and live wire spellings in
[test-library-api.py][test-library-api] (`iContains`, `isNull`, `and:`) and
[test-kanban-api.py][test-kanban-api], contract sources spec-027 (Decisions
2/3/4/9) and spec-028 (Decisions 5/8/12/13) plus the spec-060 `TODO` pointer.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — searched, twin read FIRST whole. Shared:
five substrate aliases (same right-hand sides, family-prefixed left-hand names
`_iter_filterset_subclasses` vs `_iter_orderset_subclasses`), heavy quartet via
`make_set_input_namespace` with disjoint `factory_module` / `factory_class_name` /
`collision_registry_attr` / `set_module` / `set_class_name`, `before_bind=True`
rows under disjoint owners (`filters.input_namespace` vs
`orders.input_namespace`), emission via `emit_set_input_field_triples` with
family closures. Divergent by documented contract: no lookup vocabulary (R-a),
no logic operators (R-b), no kind ladder — every leaf `Ordering | None` (R-c),
no `HIDE_FLAT_FILTERS` skip (R-d), orders-only `_ensure_field_specs` lazy
populate (R-e). Write flavors (`mutations`/`forms`/`serializer`) ride the LIGHT
`make_input_namespace` — different lifecycle, not a twin (R-g).
2. **Sync/async twins** — inapplicable with reason: zero `async def`, zero `await`
in target (grep count 0); construction runs at finalize time; no
`base_queryset`, `model_for`, `run_in_one_sync_boundary` definition or call, no
`sync_to_async`. The Q-compose functions build unevaluated `models.Q` objects —
pure sync construction, no ORM execution.
3. **Derived rather than repeated knowledge** — searched. `INPUTS_MODULE_PATH`
pinned once, read by `_build_logic_fields`, `filter_input_type`, and the factory
side; type names derived via `type_name_for` (bag names direct, related refs via
`_input_type_name_for` → `set_input_type_name`); range-name guard shared via
`pascal_case_or_raise` (own error per consumer); `_owner_type_name` delegates to
`graphql_type_name` (base + finalizer read the same property — verified, not a
second derivation); `_model_field_for_filter` delegates to upstream
`get_model_field` (library call, out of population); `_scalar_from_model_field`
delegates to `scalar_for_field`; `_choice_enum_from_filter` delegates to
`convert_choices_to_enum`; hide-flag via the `conf.py` named reader with local
truthiness coercion. No fact re-derived.
4. **Inverse / round-trip pairs** — searched, both directions verified. Forward:
`LOOKUP_NAME_MAP.get(lookup, (lookup, lookup))` in `_build_input_fields`;
reverse: `_FORM_KEY_BY_PYTHON_ATTR` built once from the map (`reversed` view,
first-wins) + `_form_key_for_python_attr` with verbatim fallthrough — symmetric
unknown-token behavior both ways. Convert/normalize ride ONE kind table
(spec-053 C3); GlobalID encode (object → wire string, type preserved) pairs with
the bound-filter decode-and-validate path in `filters/base.py` (deliberate
non-decode, documented); range class build (`start`/`end`) pairs with the
positional `{name_0, name_1}` patch.
5. **Contracts in another medium** — searched. Oracles pin literals, never derive
from the owner: `test_lookup_name_map_full_table_matches_spec` compares a
verbatim literal dict against the map (map change → test fails, oracle needs no
update unless the contract intentionally moves); bag wire-name pins
(`i_contains`→`iContains`, `is_null`→`isNull`, `in_`→`in`) spell literals;
live tier sends `iContains` / `isNull` / `and:` over the wire. No test iterates
the map to build expectations (verified: sole `LOOKUP_NAME_MAP` hits are the
import, the literal pin, and a docstring). Projections: module docstring,
spec-027 Decision pointers, spec-060 `TODO` at `filters/sets.py`
(`construct_search` unconsumed in source by documented deferral — released, not
a defect). Upstream cookbook trim rule re-expressed as the in-loop skip (R-f).
6. **Enforcement by omission** — enumerated. Orders lacks lookup/logic/kind/HIDE
surfaces by contract (spec-028 Decisions 5/8/12; triggers recorded R-a..R-d).
`_ensure_field_specs` exists orders-only because filters builds specs at
bind time while orders normalizes direct-called mappings (R-e; no contract
source demands a filters-side twin — filters `_normalize_input` already falls
back when `spec is None`). `TypedFilter` normalize arm returns `MRO_CONTINUE`
(convert-only by documented design, ChoiceFilter/catchall still fire). No
missing guard with a contract source behind it — no defect filed.

### Enumeration

Instrument: every name in `ast.Module.body` that defines a rule or binds a
value — top-level `Assign` / `AnnAssign` / `FunctionDef` / `ClassDef` plus every
member under the class. Module docstring (projection), 25 import statements
(references), and the `TYPE_CHECKING` guard (type-only) excluded with reason.
**Count: 44 top-level members + 4 class fields = 48 units**, every one assigned
below (F = family incl. proposed, L = file-local, R = rejection).

| # | Member | Home |
|---|---|---|
| 1 | `FieldSpec` | L-k (re-export declaration over owner) |
| 2 | `build_input_class` | L-k (re-export declaration over owner) |
| 3 | `_camel_case` | L-k (re-export declaration over owner) |
| 4 | `_iter_filterset_subclasses` | L-k (re-export declaration over owner) |
| 5 | `_input_type_name_for` | L-k (re-export declaration) + F-4 consumer |
| 6 | `INPUTS_MODULE_PATH` | L-a (one constant, read by name) |
| 7 | `LOOKUP_PREFIXES` | L-b (deferred search vocabulary + `construct_search`) |
| 8 | `LOOKUP_NAME_MAP` | F-1 (NEW; the one grammar definition) |
| 9 | `_compose_and` | F-2 (NEW; composed by descriptor record) |
| 10 | `_compose_or` | F-2 (NEW; composed by descriptor record) |
| 11 | `_compose_not` | F-2 (NEW; composed by descriptor record) |
| 12 | `LogicOperatorDescriptor` + fields `python_attr` / `wire_name` / `is_sequence` / `compose` | F-2 (NEW; record shape, 4 fields) |
| 13 | `LOGIC_OP_AND` | F-2 (NEW; operator declaration) |
| 14 | `LOGIC_OP_OR` | F-2 (NEW; operator declaration) |
| 15 | `LOGIC_OP_NOT` | F-2 (NEW; operator declaration) |
| 16 | `LOGIC_OPERATORS` | F-2 (NEW; the one tuple) |
| 17 | `LOGIC_OPERATORS_BY_WIRE` | F-2 (NEW; derived map, same-file comprehension) |
| 18 | `LOGIC_OPERATORS_BY_PYTHON_ATTR` | F-2 (NEW; derived map, same-file comprehension) |
| 19 | `_materialized_names` | F-3 (REUSE; ledger declaration over owner quartet) |
| 20 | `_field_specs` | F-3 (REUSE; provenance declaration) + F-6 contributor |
| 21 | quartet unpack (`_materialize_input`, `_clear_input_namespace` bindings) | F-3 (REUSE; owner product bindings) |
| 22 | `_pascal_case` | F-4 consumer (shared guard, RangeFilter-specific error) |
| 23 | `_scalar_from_form_field` | L-e (form-field → scalar table, single site) |
| 24 | `_scalar_from_model_field` | L-e (delegate to `scalar_for_field`) |
| 25 | `_choice_enum_from_filter` | L-e (delegate to `convert_choices_to_enum`) |
| 26 | `_element_annotation` | L-e (model-field-first element rule) |
| 27 | `_FILTER_INPUT_KIND_TYPES` | L-c (the one kind table) |
| 28 | `_filter_input_prechecks` | L-c (strict-zip, fails loud on drift) |
| 29 | `_unexpected_filter_dispatch` | L-c (fallthrough factory, never reached) |
| 30 | `convert_filter_to_input_annotation` | L-d (convert pass over the one table) |
| 31 | `normalize_input_value` | L-d (normalize pass over the one table) + F-6 classified |
| 32 | `_require_list_container` | L-f (list-shape fail-loud guard) |
| 33 | `_encode_global_id_input` | L-f (object → wire string, type preserved) |
| 34 | `_unwrap_enum_member` | L-f (structural `enum.Enum` unwrap) |
| 35 | `_build_range_input_class` | L-g (owner-scoped naming + instance cache) |
| 36 | `_normalize_range_value` | L-f (positional `{name_0, name_1}` patch) |
| 37 | `_owner_type_name` | L-m (thin delegate to `graphql_type_name`) |
| 38 | `_build_logic_fields` | F-2 (iterates the one tuple) + F-5 hook body |
| 39 | `_build_input_fields` | F-5 hook body + F-1 forward consumer + F-4 naming consumer + F-6 provenance writer |
| 40 | `_model_field_for_filter` | L-i (upstream delegate + guards) |
| 41 | `construct_search` | L-b (deferred surface, tested directly) |
| 42 | `materialize_input_class` | F-3 (REUSE; thin wrapper) |
| 43 | `clear_filter_input_namespace` | F-3 (REUSE; heavy-clear wrapper) |
| 44 | `register_subsystem_clear(...)` call | F-3 (REUSE; verified `owner="filters.input_namespace"`, `before_bind=True`) |

Static probe (AST walk, read-only): `type_name_for`, `register_subsystem_clear`
(defined — only called), `make_dynamic_set_getter`, `make_set_meta_cache_key`,
`model_for`, `base_queryset`, `run_in_one_sync_boundary`, `resolve_lazy_class`
appear **zero** times as definitions in the target — no second owner for any
indexed machinery. `get_filterset_class` / `Ordering` / `_ensure_field_specs`
absent — correctly not inherited from the twin.

### Challenges

Authoritative definitions only; consumers, oracles, projections that also move
listed but not counted.

- **Lookup spelling** (new lookup, renamed wire name, e.g. `week_day` alias
change): posit the change → 1 definition moves
([filters/inputs.py][filters-inputs]`::LOOKUP_NAME_MAP`); 0 here beyond it.
Consumers follow by construction: forward `.get` in `_build_input_fields`,
reverse `_FORM_KEY_BY_PYTHON_ATTR` (built from the map at import), both
`_form_key_for_python_attr` call sites, bag emission. Oracles pinning literals
(package pin test, bag wire-name test, live `iContains`/`isNull`) fail —
projections (spec-027 Decision 3) move with an intentional change.
- **New logical operator** (fourth, e.g. `xor` with its Q compose): posit the
change → 1 definition (the `LOGIC_OPERATORS` tuple + its descriptor; both
`BY_*` maps derive by comprehension in the same edit). Consumers (`_build_logic_fields`,
`_LOGIC_PYTHON_ATTRS`, `_iter_logic_branches`, `_normalize_input` wire mapping,
factory hook splice, `_permission` `logic_keys`) iterate, 0 definitions.
- **New filter primitive kind** (e.g. a JSON filter needing distinct
convert+normalize arms): posit the change → 1 definition (append to
`_FILTER_INPUT_KIND_TYPES`) + 2 handler declarations (one per pass —
declarations, not definitions; the strict zip fails loud if a pass forgets
one). Orders twin: 0 (no ladder by R-c).
- **New namespace lifecycle slot** (family-specific cached binding): posit the
change → 1 definition
([utils/inputs.py][utils-inputs]`::make_set_input_namespace` /
`clear_generated_input_namespace`); the quartet unpack here is a declaration
(0 definitions).
- **Input-name rule** (rename every generated input; new empty-token policy):
posit the change → 1 definition
([sets-mixins.py][sets-mixins]`::ClassBasedTypeNameMixin.type_name_for` for the
rule, [utils/strings.py][utils-strings]`::pascal_case_or_raise` for the guard);
bag names, related refs, and `_pascal_case` here are consumers with
per-consumer errors (0 definitions).
- **New traversal/permission axis** (sixth `SetInputTraversal` axis): posit the
change → 1 definition (traversal shape + mixin read); `_field_specs` here is
the family ledger declaration the config points at by reference (0
definitions); both normalizers and all walkers reclassify through the one
object.
- **New search prefix** (e.g. `~` → `icontains`): posit the change → 1
definition (`LOOKUP_PREFIXES`); `construct_search` follows; the spec-060 `TODO`
consumer follows when it lands.

All probes static-reviewed (body inspection + population greps + AST walk). No
mutating proof: the target decides no ordering beyond Q-object construction
(unevaluated), no transactions, no async behavior.

## Findings

**F-1 `lookup-name-spelling-grammar` (NEW FAMILY, for Worker 0 index).**
Contract: every Django-lookup ↔ GraphQL/python-attr spelling flows through one
table in both directions, with verbatim fallthrough for unknown tokens.
Owner: [filters/inputs.py][filters-inputs]`::LOOKUP_NAME_MAP` (member 8; the
table DRY.md vocabulary already cites as the one grammar). Reverse half:
[filters/sets.py][filters-sets]`::_FORM_KEY_BY_PYTHON_ATTR` (built once from
the map, `reversed` first-wins) +
[filters/sets.py][filters-sets]`::FilterSet._form_key_for_python_attr`
(verbatim fallthrough). Forward consumer: member 39 (`.get` with identical
fallthrough). Oracles: literal pin test + bag wire-name test + live
`iContains`/`isNull` (all independent — none iterates the map). Challenges
above (1 definition per change). Migration: none (already compose by name;
reverse built from the owner at import). Distinct behavior: the unknown-token
verbatim fallthrough is shared grammar, not divergence. Proof:
static-reviewed (both halves read the one table; fallthrough symmetry
verified). Gate: none owed here (zero-edit file item; family item owns it).
Freshness: target `82b52d97`, reverse `4ab65a26`, twin `6f6ec946`, HEAD
`9031cb3d`.

**F-2 `filter-logic-operators` (NEW FAMILY, for Worker 0 index).** Contract:
the filter logical-operator vocabulary (python attr, wire name, sequence
cardinality, Q composition) is declared once as immutable records; emission,
normalization, permission traversal, and factory splicing all iterate the one
tuple. Owner: [filters/inputs.py][filters-inputs]`::LOGIC_OPERATORS` (member
16) with `LogicOperatorDescriptor` (member 12) + `LOGIC_OP_*` (members 13–15)
+ derived `BY_*` maps (members 17–18) + `_compose_*` (members 9–11). Consumers:
member 38 (emission), [filters/sets.py][filters-sets] (`_LOGIC_PYTHON_ATTRS`,
`_iter_logic_branches`, `_normalize_input` wire copy, `_permission`
`logic_keys`), [filters/factories.py][filters-factories] (hook splice).
Challenges above (1 definition per change). Migration: none (already single
table + derived maps). Distinct behavior: `not_` single (non-sequence) vs
`and_`/`or_` list shape — one `is_sequence` axis, not a fork. Proof:
static-reviewed. Gate: none owed here. Freshness: target `82b52d97`, sets
`4ab65a26`, factories `366e0490`, HEAD `9031cb3d`.

**F-3 `subsystem-clear-lifecycle` (REUSE, index: open).** Owner: `registry.py`
bus. Target role: state contributor — members 19–21 (ledger + provenance
declarations over the owner quartet), members 42–43 (thin wrappers), member 44
(registration; verified `owner="filters.input_namespace"`, `before_bind=True`,
matching the twin's disjoint `orders.input_namespace` row). No local clear
body (verified: no `ledger.clear()` spelling outside the owner product).
Freshness: target `82b52d97`, owner `ee31d360`, registry `9cc8bb55`, HEAD
`9031cb3d`.

**F-4 `set-type-naming` (REUSE, index: open).** Owner:
[sets-mixins.py][sets-mixins]`::ClassBasedTypeNameMixin`. Target role: pure
consumer — bag names via `filterset_cls.type_name_for` (member 39), related
refs via member 5 → `set_input_type_name`, range stems via member 22 sharing
the `pascal_case_or_raise` guard with per-consumer errors. No naming rule
defined here (AST-verified: no `type_name_for` definition). Freshness: target
`82b52d97`, owner `ad8987ea`, strings `3ec3b262`, HEAD `9031cb3d`.

**F-5 `set-arguments-factory-bfs` (REUSE, index: open).** Owner:
[utils/inputs.py][utils-inputs]`::GeneratedInputArgumentsFactory`. Target role:
hook-body side — members 38–39 are the bodies the factory's
`_build_input_triples` override splices (recorded in the factories artifact as
R1 divergence vs the order bare return). No walk/collision/cache spelling here.
Freshness: target `82b52d97`, owner `ee31d360`, factories `366e0490`, HEAD
`9031cb3d`.

**F-6 `active-input-permission-facade` (REUSE, index: open).** Owner:
[sets-mixins.py][sets-mixins]`::ActiveInputPermissionMixin`. Target role:
provenance contributor — member 20 is the ledger the family's ONE traversal
config (`FilterSet._permission`, declared in `filters/sets.py`) points at by
reference; member 31 classifies through `cls._input_traversal()` (the same
object the permission walkers use); member 39 populates the ledger at bind.
No permission rule defined here. Freshness: target `82b52d97`, owner
`ad8987ea`, sets `4ab65a26`, input-values `f2566609`, HEAD `9031cb3d`.

**F-7 checked non-memberships — do not inherit.** `dynamic-set-class-getter`:
no Layer-6 getter, cache, reserved keys, or `type(...)` here (the deferred
surface lives in factories). `queryset-seed-and-model-read`: no `model_for` /
`base_queryset` here (`_model_field_for_filter` resolves a field, not a
queryset seed). `one-sync-boundary`: no import, no call, no async surface.
Zero definitions, zero calls.

**L-a..L-m file-local rows** (one file + proving challenge each): L-a module
path (posit rename → the constant + its three readers move together; readers
are consumers); L-b search vocabulary (posit a fifth prefix → the map + helper
move, spec-060 `TODO` follows; unconsumed in source by documented deferral);
L-c kind ladder (posit a ninth kind → table + two handler declarations; strict
zip fails loud); L-d twin passes (posit a per-kind annotation-shape change →
the pass's handler moves, the table unchanged — same-file pair, one owner);
L-e scalar/element table (posit a new form-field shape → the `isinstance` chain
gains one arm; model/choice arms delegate outward); L-f normalize helpers
(posit a new wire container → the guard + arms move together, same file);
L-g range naming (posit a range-name collision rule → the qualifier + cache key
move; mirrors bag naming by documented forward path); L-i model-field resolver
(posit a new guard → the two early returns move; traversal delegates to
upstream); L-k substrate aliases (posit a substrate rename → aliases follow;
declarations, not definitions); L-m owner-name reader (posit a rename rule →
the property moves; two readers here + base/finalizer read the same property).
Each: full-package grep found no second definition (probes above).

**Rejections R-a..R-g** (difference + trigger + home): R-a orders lookup
vocabulary (no leaf-shape divergence — every leaf `Ordering | None` per
spec-028 Decision 5; trigger: ordering leaves diverging by column type; home:
[orders/inputs.py][orders-inputs]`::convert_order_field_to_input_annotation`
docstring). R-b orders logic bag (no `and_`/`or_`/`not_` per spec-028 Decision
8; trigger: orders gaining an operator bag; home: member 38 vs the order hook's
bare return). R-c orders kind ladder (same contract difference as R-a; home:
member 27 docstring + order converter docstring). R-d `HIDE_FLAT_FILTERS` skip
(filter-only: orders expose no flat `*__lookup` paths; trigger: orders gaining
flat paths; home: member 39 `_visible_entries` closure). R-e
`_ensure_field_specs` lazy populate (orders-only: filters builds at bind,
orders normalizes direct-called mappings; trigger: filters supporting
pre-bind direct normalization; home:
[orders/inputs.py][orders-inputs]`::_ensure_field_specs` docstring). R-f
cookbook twins (`connection_field.py` trim rule re-expressed as the in-loop
skip; `get_model_field` is a library call — external, out of population;
trigger: none). R-g light vs heavy namespace (write flavors derive from one
declaration, no BFS/factory/`_lifecycle` state; trigger: a write flavor gaining
a related-set graph; home:
[utils/inputs.py][utils-inputs]`::make_input_namespace` docstring).

## Defects

None. Three probed edges released without a defect: (1) the literal pin test
reads `LOOKUP_NAME_MAP` but pins a verbatim expectation — it fails on map
change rather than deriving from the owner, so it is an independent oracle,
not rot; (2) `_owner_type_name`'s "three callers" docstring — verified the
three sites all read the one `graphql_type_name` property (the helper is its
thin delegate), so the sharing claim holds; (3) `construct_search`
unconsumed in source — documented deferral with the consumer `TODO` and direct
tests, owned by spec-060, unreachable from any wire path today.

## Pending execution

None. Every proof is static-reviewed (body inspection, population greps, AST
walk). Inspection suffices because the target decides no ordering beyond
unevaluated Q construction, no transactions, and no async behavior; both
genuine cross-file rules (lookup grammar, logic operators) already compose by
name through the single table, verified fresh.

## Judgment

Zero-edit result: matrix discharged against the real surface (orders twin read
first whole; lookup grammar verified in both directions; input-name derivation
vs `type_name_for` traced call by call; sync/async absence verified by grep,
not assumed), 48/48 units assigned (2 new families named, 4 reused as
consumer/contributor, 1 non-membership correctly withheld, remainder
file-local or rejected with difference + trigger + home), challenges recorded
with definition counts, no defect with a wire-reachable contract found. Both
genuine cross-file rules already compose by name — verified fresh, not
inherited from prior-cycle prose.

## Implementation (Worker 1)

No production edits (file item; target CLEAN throughout — working blob
`82b52d97` == HEAD blob, absent from `git status --short`). No new tracked
files besides this artifact (untracked until Worker 0 records it). Item-scoped
diff vs `ITEM_BASELINE` `612f079ef17681d6122de4d55b22e97486e7ae82` for
`django_strawberry_framework/filters/inputs.py` + this artifact path: empty on
the target; artifact is new (`??`). Concurrent dirt explicitly untouched:
working-tree `django_strawberry_framework/connection.py` hunk, staged
`tests/utils/test_querysets.py` (+31), `tests/test_connection.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` — none opened,
none attributed here. No pytest run (not authorized by the entry command; no
edits to verify). No ruff run (no edits). No scratch files created (all probes
read-only inline: content search, AST walk, blob hashes); no
`docs/dry/temp-tests/` directory was needed.

## Independent verification (Worker 2)

Own trace, derived before reconciling with `## Findings` above. Instrument:
`ast.Module.body` walk of the target plus package-wide greps over
`django_strawberry_framework/`, `tests/filters/test_inputs.py` (1689 lines,
verified by `wc`), `examples/fakeshop/test_query/test_library_api.py`, and the
orders twin read whole (`orders/inputs.py`, 395 lines, verified by `wc`).

**Own rule derivation (owners I would choose):**

- Lookup spelling: one table
  (`filters/inputs.py::LOOKUP_NAME_MAP`, 27 entries) + reverse half built from
  it at import (`filters/sets.py::_FORM_KEY_BY_PYTHON_ATTR` via `reversed`
  first-wins + `_form_key_for_python_attr` verbatim fallthrough) + forward
  consumer (`_build_input_fields` `.get(lookup, (lookup, lookup))`).
  Challenge (rename a wire name, e.g. `week_day`): 1 definition. Owner:
  `LOOKUP_NAME_MAP` — the grammar DRY.md already cites. Consumers follow by
  construction; literal-pin oracles fail on change.
- Logic operators: records (`LogicOperatorDescriptor` + 3 `_compose_*` +
  `LOGIC_OP_*` + `LOGIC_OPERATORS` tuple + 2 `BY_*` derived maps, all
  same-file/one-edit) consumed by `_build_logic_fields`,
  `filters/sets.py` (`_LOGIC_PYTHON_ATTRS`, `_iter_logic_branches`,
  `_normalize_input` wire copy, `_permission` `logic_keys`), and the factories
  hook splice. Challenge (4th operator): 1 definition. Owner:
  `LOGIC_OPERATORS`. `is_sequence` vs single is one record axis, not a fork.
- Namespace lifecycle: owner the `registry.py` bus;
  `make_set_input_namespace` mechanics in `utils/inputs.py`. Target holds
  ledger/provenance declarations (bare `AnnAssign` pair, values bound by the
  quartet unpack), thin wrappers, and the registration row
  (`owner="filters.input_namespace"`, `before_bind=True`, disjoint from the
  twin's `orders.input_namespace`). No local clear body. Owner: registry bus.
- Type naming: owner
  `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` (+
  `pascal_case_or_raise` guard). Target is pure consumer (bag names direct,
  related refs via `_input_type_name_for` → `set_input_type_name`, range stems
  via `_pascal_case` sharing the guard with per-consumer errors). Zero local
  definitions (AST-verified: no `type_name_for` def/assign).
- Factory BFS: owner `utils/inputs.py::GeneratedInputArgumentsFactory`.
  Target members `_build_input_fields` / `_build_logic_fields` are the hook
  bodies `FilterArgumentsFactory._build_input_triples` splices. Zero
  walk/collision/cache spelling here.
- Permission provenance: owner `ActiveInputPermissionMixin` + the
  `FilterSet._permission` traversal config. `_field_specs` is the ledger the
  config points at by reference; `normalize_input_value` classifies through
  `cls._input_traversal()`, the same object the walkers use. No permission
  rule defined here.
- File-local singles (each: full-package grep, no second definition):
  `INPUTS_MODULE_PATH` (1 const, readers by name); `LOOKUP_PREFIXES` +
  `construct_search` (deferred surface, consumer `TODO(spec-060` in sets.py,
  direct tests); kind ladder + strict-zip + fallthrough factory; twin passes
  over the one table; scalar/element delegates outward (`scalar_for_field`,
  `convert_choices_to_enum`); normalize guards/helpers (list-shape fail-loud,
  GlobalID re-encode preserving `type_name`, structural enum unwrap, positional
  range patch); range build + instance cache + per-filterset naming; upstream
  `get_model_field` delegate + guards (external call, out of population); 5
  substrate aliases (declarations over `utils/inputs.py` mechanics);
  `_owner_type_name` thin delegate (all three readers verified against the one
  `graphql_type_name` property).
- Non-memberships: no `type_name_for` / `register_subsystem_clear` /
  `make_dynamic_set_getter` / `make_set_meta_cache_key` / `model_for` /
  `base_queryset` / `run_in_one_sync_boundary` / `resolve_lazy_class` /
  `get_filterset_class` / `Ordering` / `_ensure_field_specs` def or assign
  (AST-verified) — correctly withheld.

Reconciliation: no assignment difference vs W1 on any of the 48 units, any
owner, or any rejection. Two wording notes, both below the defect bar:
L-lettering skips `h`/`j`/`l` (labels, not ordinals — harmless), and R-f
states `trigger: none` where I would write "no in-population trigger (both
compared sites are external libraries)" — same verdict.

**Enumeration (member-by-member vs own count):** own walk: `body` 71 −
docstring 1 − imports 25 − `TYPE_CHECKING` guard 1 = **44 top-level**;
`LogicOperatorDescriptor` fields **4**; total **48 units**. Matches W1's
44 + 4 exactly. Every table row lands: #1–5 aliases, #6 module path, #7–8
search vocab + grammar, #9–18 logic records/tuple/maps (with #12 = class + 4
fields), #19–21 ledger declarations + quartet unpack (note #20 is
annotation-only, values arrive via #21 — W1 distinguishes this correctly),
#22–26 naming/scalar/element, #27–31 kind table + passes, #32–36 normalize
helpers + range, #37 owner-name, #38–39 builders, #40 field resolver, #41
search helper, #42–44 materialize/clear/register. Exclusions (docstring as
projection, 25 imports as references, `TYPE_CHECKING` as type-only) judged
sound. Dual-homed rows (#5, #20, #31, #38, #39) are one unit with two roles,
not double counts.

**Matrix vs real surface:** (1) Mirroring discharged against the whole twin
FIRST — five shared substrate shapes plus seven documented divergences
(R-a..R-e, R-g); write flavors correctly placed on the light lifecycle, not
the twin. (2) Sync/async inapplicable with reason — verified 0 `async def` /
`await` by grep; Q objects built unevaluated; no queryset/seed/boundary
def/call. (3) Derived knowledge searched — one looseness: W1's "factory side"
reader of `INPUTS_MODULE_PATH` is really the namespace-construction call plus
the `__init__` helper and emit call passing it by name; the substance (pinned
once, never re-derived) holds. (4) Round-trips verified both directions —
symmetric verbatim fallthrough on the spelling grammar; one kind table for
convert/normalize; GlobalID encode vs deliberate non-decode documented;
range build vs positional patch. (5) Oracles independent — the pin test
spells a 27-entry verbatim literal (`assert expected == LOOKUP_NAME_MAP`;
map change fails it); sole other map-adjacent test mentions the map only in
its docstring; bag pins (`i_contains`→`iContains`, `is_null`→`isNull`,
`in_`→`in`) and live wire (`iContains`, `isNull`, `and:`) spell literals;
no test iterates the map to build expectations. (6) Omission enumerated —
orders gaps carried by spec-028 contract with triggers; `TypedFilter`
convert-only by documented design; no contract-backed missing guard, so no
defect.

**Counts + roles:** all seven challenges re-derived at count 1 (kind-table
growth = 1 table + 2 per-pass handler *declarations*, strict-zip fails loud
— correctly not counted as definitions). No oracle rewritten to read its
owner. Roles (definition / consumer / oracle / projection) concur in every
finding.

**Equivalence (principle 8):** zero-edit, so the proof owed is that the two
cross-file rules already compose by name — verified fresh: reverse map built
from the owner at import (no fork to drift); logic consumers iterate the one
tuple (no restatement). No ordering, transaction, async, cancellation, or
actor/time-observation surface exists beyond unevaluated Q construction, so
static review discharges execution. `execution-deferred`: none; Pending
absent — adequate, and the dispatch's "NO probe — inline read-only analysis"
was honored (no scratch, no mutating proof, none needed).

**Zero-edit + families:** item-scoped diff confirmed empty by re-run
(`git diff 612f079ef17681d6122de4d55b22e97486e7ae82 --
django_strawberry_framework/filters/inputs.py` prints nothing, exit 0;
target absent from `git status --short`; working blob `82b52d97…` ==
HEAD blob). 48/48 units assigned; no unassigned remainder. New-family
rulings: **endorse `lookup-name-spelling-grammar`** — forward + reverse halves
are one round-trip contract with one change trigger (new/renamed lookup), not
two families; folding it into `set-type-naming` would merge distinct reasons
to change (lookup rename vs class-naming policy). **Endorse
`filter-logic-operators`** — one vocabulary (identity + cardinality + Q
semantics) with one trigger (new operator); record columns change together,
so not over-splitting. Both route to family items, which own their gates —
no gate owed here, correctly none claimed.

**Rejections R-a–R-g:** each carries difference + trigger + home, verified:
R-a/R-c grounded in `convert_order_field_to_input_annotation` (every leaf
`Ordering | None`, spec-028 Decision 5); R-b in the order hook's bare return
vs member 38 (spec-028 Decision 8); R-d in the `_visible_entries` closure
(filter-only flat paths); R-e in orders-only `_ensure_field_specs` (filters
builds at bind; no contract source demands a filters twin); R-g in
`make_input_namespace` vs `make_set_input_namespace` docstrings. R-f's
`trigger: none` judged adequate — both compared sites are external to the
population (graphene cookbook trim rule, `django_filters.utils`
`get_model_field` library call), so no in-population reunification change
exists; its in-package half is documented at the member-39 closure.

**Fingerprints re-hashed (all match):** target `82b52d97` (full
`82b52d97b8f8b26d…`), sets `4ab65a26`, twin `6f6ec946`, factories `366e0490`,
`utils/inputs.py` `ee31d360`, registry `9cc8bb55`, sets-mixins `ad8987ea`,
strings `3ec3b262`, input-values `f2566609`, HEAD `9031cb3d` (via
`git rev-parse`). No fingerprint changed; nothing reopens.

**AGENTS.md prose:** citations use `path::Symbol` with reference-style links
and all 10 canonical link groups; no `feedback.md` mention (grep hits are
spec-060 `TODO` pointers only); no process provenance; zero edits so no
format/test obligations arose (correctly no pytest/ruff run); concurrent
dirt untouched — status shows only pre-existing dirt plus untracked DRY
artifacts, target clean.

**Defects (Worker 2):** none. Concur on all three W1-released edges: (1)
literal pin is an independent oracle, not rot; (2) the "three callers" sharing
claim verified — `filters/base.py:711`, `types/finalizer.py` comparisons, and
the helper all read the one `graphql_type_name` property; (3)
`construct_search` unconsumed in source is a documented spec-060 deferral
with direct tests and no wire path, not a defect.

Judgment: zero-edit file item complete. Coverage 48/48, matrix discharged
against the real surface, challenges at count 1, oracles independent,
fingerprints fresh, prose compliant. `Status: verified`, no pending
execution.

## Run 0.0.15 2026-09-30-8 re-trace (Worker-1)

Scoped re-trace of queue item s8 at HEAD bytes. The run-7 artifact above is
prior evidence only: every finding below was re-derived against current HEAD
bytes with fresh `git grep HEAD` / `git show HEAD:` populations and an AST
enumeration. No production edits (file item, reviewer role).

ITEM_BASELINE `8346655631d312debde1a8657593024854770547`.
Item-scoped diff vs baseline for
`django_strawberry_framework/filters/inputs.py`: empty. No owned ledger hunk
names this file; all dirt is concurrent (attributed by diff content below).

### Freshness fingerprints

- HEAD blob `2c853e24a5a97b2e14768411c3278e94a6967a68` (1206 lines) — traced
  bytes. Every body cited below is HEAD bytes.
- Worktree hash `c933bb5d673e2ff0524283203240abdb1c1af841` (1236 lines).
- `9aaaad5d` bytes blob `a932dbf85d89791280774b0600a40b5fb43b89e4`
  (1103 lines, "dry-0015 pre-ff snapshot", not an ancestor of HEAD).
- Drift base `0c0537e2` blob `82b52d97b8f8b26d2846df24dabcabb793507c87`
  (1073 lines) — byte-identical to the prior artifact's traced bytes, so
  every delta below is the 7-commit drift plus concurrent dirt.

`9aaaad5d` vs drift base on this target is 54+/24- (net +30); HEAD-vs-worktree
is 59+/29- (net +30): the same dirt shape (pre-merge bytes carry 17 `truth.`
refs with 0 `RelationPk` / `ModelChoiceFilter` / `_safe_*` refs — drift-base
bytes plus the concurrent truth/range dirt; the worktree is HEAD bytes plus
that same dirt). Neither was traced; both are read-only attribution evidence.

Connected sources (HEAD blobs, all traced via `git show HEAD:`):
`filters/sets.py` `3d307402`, `filters/base.py` `e2e683a8`,
`filters/factories.py` `c400d646`, `filters/__init__.py` `8ce8b96d`,
`orders/inputs.py` `39e39d29`, `utils/inputs.py` `7b88d358`,
`registry.py` `9d2021eb`, `sets_mixins.py` `6764d455`,
`utils/strings.py` `a326167d`, `utils/input_values.py` `3c17224f`,
`conf.py` `10096f84`, `types/converters.py` `d146b23f`,
`types/definition.py` `5bf257c3`; oracle `tests/filters/test_inputs.py`
`769e7b45`.

### Dirt attribution by diff content

HEAD-vs-worktree (59+/29-, all concurrent, none traced): a `utils/truth.py`
migration (import swap `_safe_*` out / `truth` in, `_safe_arg_repr` /
`_safe_type_name` → `truth.render` / `truth.kind`, `getattr` →
`truth.static_attr` x3, `isinstance` → `truth.is_instance` x1, `__name__` →
`truth.name` x2, `__class__.__name__` → `truth.kind` x1; worktree carries 22
`truth.` refs and 0 `_safe_*`) plus the `_normalize_range_value` fail-loud
rewrite (unknown-axes + non-range `ConfigurationError` arms with an extended
docstring contract) plus one comment reword (the duck-typed sentence). No
owned ledger row covers it.

Drift-base-vs-HEAD (+133 net, 7 commits, the re-trace subject): the two
behavior commits from the queue brief plus typing-only drift. Verified by
content: `bbe54687` (46+/1-: 3-name import, +`_relation_identity_annotation`,
+2 kind entries, +2 convert / +2 normalize arms, docstring line);
`57131b99` (65+/3-: ModelChoice import pair + `model_choice_identity_column`,
+`_model_choice_takes_list` + `_model_choice_identity_annotation`, +1 kind
tuple, +1 convert / +1 normalize arm, comment + docstring). The other five
commits were scanned hunk by hunk and move no behavior: `999a1aab`
(type-ignore comments), `b20277fe` (casts + annotations only),
`dd3a10b1` (`GenericAlias(list, ...)` for `list[...]` — runtime-identical —
plus ignore drops), `dfbea72b` (annotation widens + ignore), `fef11e64`
(`Annotated` → `Any` + `GenericAlias`). No `return` / branch / call changed
outside the two behavior bodies.

### Enumeration (fresh, HEAD bytes)

Instrument: same as run 7 — top-level `Assign` / `AnnAssign` /
`FunctionDef` / `ClassDef` in `ast.Module.body` plus every class member,
executed against HEAD bytes. Module body: 74 statements = 1 docstring + 25
imports + 1 `TYPE_CHECKING` block + 47 rule/value tops. Excluded scaffolding
with reason: the module docstring (projection), 25 imports (references, not
definitions; 20 `ImportFrom` + 5 `Import`), the `TYPE_CHECKING` block
(type-only, including the `_TypeForm` Protocol). **Count: 47 tops + 4 class
fields = 51 units** (48 at drift base + 3 new functions). Every member
assigned below (F = family incl. s7-named, L = file-local, R = rejection).

| # | Member | Home (run 8) |
|---|---|---|
| 1 | `FieldSpec` | L-k (re-export declaration over owner) |
| 2 | `build_input_class` | L-k (re-export declaration over owner) |
| 3 | `_camel_case` | L-k (re-export declaration over owner) |
| 4 | `_iter_filterset_subclasses` | L-k (re-export declaration over owner) |
| 5 | `_input_type_name_for` | L-k (re-export declaration) + F-4 consumer |
| 6 | `INPUTS_MODULE_PATH` | L-a (one constant, read by name) |
| 7 | `LOOKUP_PREFIXES` | L-b (deferred search vocabulary + `construct_search`) |
| 8 | `LOOKUP_NAME_MAP` | F-1 (the one grammar definition; 26 entries) |
| 9 | `_compose_and` | F-2 (composed by descriptor record) |
| 10 | `_compose_or` | F-2 (composed by descriptor record) |
| 11 | `_compose_not` | F-2 (composed by descriptor record) |
| 12 | `LogicOperatorDescriptor` + fields `python_attr` / `wire_name` / `is_sequence` / `compose` | F-2 (record shape, 4 fields) |
| 13 | `LOGIC_OP_AND` | F-2 (operator declaration) |
| 14 | `LOGIC_OP_OR` | F-2 (operator declaration) |
| 15 | `LOGIC_OP_NOT` | F-2 (operator declaration) |
| 16 | `LOGIC_OPERATORS` | F-2 (the one tuple) |
| 17 | `LOGIC_OPERATORS_BY_WIRE` | F-2 (derived map, same-file comprehension) |
| 18 | `LOGIC_OPERATORS_BY_PYTHON_ATTR` | F-2 (derived map, same-file comprehension) |
| 19 | `_materialized_names` | F-3 (ledger declaration over owner quartet) |
| 20 | `_field_specs` | F-3 (provenance declaration) + F-6 contributor |
| 21 | quartet unpack (`_materialize_input`, `_clear_input_namespace` bindings) | F-3 (owner product bindings) |
| 22 | `_pascal_case` | F-4 consumer (shared guard, RangeFilter-specific error) |
| 23 | `_scalar_from_form_field` | L-e (form-field → scalar table, single site) |
| 24 | `_scalar_from_model_field` | L-e (delegate to `scalar_for_field`; 5 call sites now) |
| 25 | `_relation_identity_annotation` | F-9 consumer NEW (relation → column → scalar arm) |
| 26 | `_model_choice_takes_list` | L-n NEW (list-ness predicate, 2 in-file consumers) |
| 27 | `_model_choice_identity_annotation` | F-9 consumer NEW (column → scalar arm) |
| 28 | `_choice_enum_from_filter` | L-e (delegate to `convert_choices_to_enum`) |
| 29 | `_element_annotation` | L-e (model-field-first element rule) |
| 30 | `_FILTER_INPUT_KIND_TYPES` | L-c (the one kind table; 11 entries now) |
| 31 | `_filter_input_prechecks` | L-c (strict-zip, fails loud on drift) |
| 32 | `_unexpected_filter_dispatch` | L-c (fallthrough factory, never reached) |
| 33 | `convert_filter_to_input_annotation` | L-d (convert pass over the one table; 11 arms now) |
| 34 | `normalize_input_value` | L-d (normalize pass over the one table; 11 arms now) + F-6 classified |
| 35 | `_require_list_container` | L-f (list-shape fail-loud guard; 5 call sites now; D1a) |
| 36 | `_encode_global_id_input` | L-f (object → wire string, type preserved) |
| 37 | `_unwrap_enum_member` | L-f (structural `enum.Enum` unwrap) |
| 38 | `_build_range_input_class` | L-g (owner-scoped naming + instance cache) |
| 39 | `_normalize_range_value` | L-f (positional `{name_0, name_1}` patch; HEAD body unchanged) |
| 40 | `_owner_type_name` | L-m (thin delegate to `graphql_type_name`) |
| 41 | `_build_logic_fields` | F-2 (iterates the one tuple) + F-5 hook body |
| 42 | `_build_input_fields` | F-5 hook body + F-1 forward consumer + F-4 naming consumer + F-6 provenance writer |
| 43 | `_model_field_for_filter` | L-i (upstream delegate + guards; F-10 examined-and-excluded) |
| 44 | `construct_search` | L-b (deferred surface, tested directly) |
| 45 | `materialize_input_class` | F-3 (thin wrapper) |
| 46 | `clear_filter_input_namespace` | F-3 (heavy-clear wrapper) |
| 47 | `register_subsystem_clear(...)` call | F-3 (verified `owner="filters.input_namespace"`, `before_bind=True`) |

Static zero-probe at HEAD bytes (one combined pattern, count 0):
`type_name_for` / `register_subsystem_clear` / `make_dynamic_set_getter` /
`make_set_meta_cache_key` / `model_for` / `base_queryset` /
`run_in_one_sync_boundary` / `sync_to_async` / `resolve_lazy_class` /
`get_filterset_class` / `_dynamic_filterset_cache` / `Ordering` /
`_ensure_field_specs` appear zero times as definitions or references in the
target — no second owner for any indexed machinery, and the twin-only
members are correctly not inherited.

### Matrix (current target)

1. **Cross-flavor mirroring** — searched, twin re-read whole at HEAD
(blob `39e39d29`, 406 lines; drift-base→HEAD is 21+/10- typing-only:
`Any` → `object`, one `cast`, `TYPE_CHECKING` `RelatedOrder`, comments).
Shared substrate shapes unchanged (5 aliases, heavy quartet with disjoint
family params, disjoint `before_bind=True` rows, shared emission
scaffold). All seven divergences stand on fresh anchors: every order leaf
still `Ordering | None` (single `return`, R-a/R-c); the order hook still
bare-returns with its "no operator bag (spec-028 Decision 8)" docstring
(R-b); 0 `hide_flat` / `LOOKUP` / `LOGIC` tokens in the twin (R-d);
`_ensure_field_specs` present in the twin (def line 351) and 0 times here
(R-e); the trim skip + library `get_model_field` call unchanged (R-f);
mutations + forms + rest_framework still call light `make_input_namespace`
while filters + orders call heavy `make_set_input_namespace` (R-g). The
twin carries 0 `ModelChoice` refs and no pk arms — the drift adds no
mirror surface.
2. **Sync/async twins** — inapplicable with reason: 0 `async def` / 0
`await` at HEAD bytes; no `run_in_one_sync_boundary` / `sync_to_async` /
`base_queryset` / `model_for` import or call (zero-probe above). The new
arms build annotations and form-data values only — pure sync
construction, no ORM execution.
3. **Derived knowledge** — searched. `INPUTS_MODULE_PATH` pinned once, read
by name (3 in-file readers + the `filters/__init__.py` import/use). Type
names still via `type_name_for`; the range guard still shared with
per-consumer errors. Every new identity link composes by name:
`_relation_identity_annotation` → `relation_identity_column` →
`_scalar_from_model_field`; `_model_choice_identity_annotation` →
`model_choice_identity_column` → `_scalar_from_model_field`;
`_scalar_from_model_field` ← 5 in-file call sites, 1 definition. Package
caller counts match s7 exactly: `relation_identity_column` ← 2
(`_relation_identity_column_for`, member 25),
`model_choice_identity_column` ← 1 (member 27). The one re-derivation on
this target's seam is the F-10 runtime pair in base.py; member 43 is the
examined-and-excluded build-time third spelling (recorded below, not
counted with the pair).
4. **Inverse / round-trip pairs** — searched, both directions verified.
Forward `.get(lookup, (lookup, lookup))` unchanged; reverse still built
from the map at import (`reversed` first-wins) with verbatim fallthrough
(`.get(python_attr, python_attr)`) — symmetric unknown-token behavior both
ways. Convert/normalize ride ONE 11-kind table with strict-zip arity
verified by count (11 handlers per pass, 22 total); `TypedFilter` is
still convert-only (`return MRO_CONTINUE`, ChoiceFilter/catchall still
fire). GlobalID encode (object → wire string, type preserved) still pairs
with the bound-filter decode-and-validate path in base.py. Range class
build still pairs with the positional patch; the range body is unchanged
drift→HEAD (the fail-loud rewrite exists only in concurrent worktree
dirt, out of scope).
5. **Contracts in another medium** — searched. Oracles pin literals, never
derive from an owner: the pin test spells a 26-entry verbatim literal
against the 26-entry map; sole other `LOOKUP_NAME_MAP` hits are the
import, a section comment, and a docstring — no test iterates the map.
Bag wire-name pins and live `iContains` / `isNull` / `and:` spellings
stand; new-shape oracles spell literals too (package isinstance/marker/
annotation/behavior tests plus live raw-pk wire rows and the declared
model-choice live row). The `tests/rest_framework/test_resolvers.py`
`relation_identity` hit is `_relation_identity_intact` (the serializer
intent ledger — a different rule, correctly excluded). Projections: module
docstring, spec Decision pointers, the spec-060 `TODO` (member 44 still
production-unconsumed: only the sets.py comment + direct tests). Two
docstrings undercount their consumers after the drift — defect D1.
6. **Enforcement by omission** — enumerated. Orders lacks the
lookup/logic/kind/HIDE surfaces by contract (spec-028; triggers carried
R-a..R-d); the new pk/model-choice arms extend R-a/R-c with no twin
(orders carry no identity). `_ensure_field_specs` stays orders-only with
no contract source demanding a filters twin. `TypedFilter` normalize
still convert-only by documented design. No missing guard with a contract
source behind it — no behavior defect filed.

### CONFIRM / REVISE per prior finding

- **F-1 `lookup-name-spelling-grammar`** — CONFIRM rule, REVISE count.
The one-table grammar with symmetric verbatim fallthrough stands in both
directions (forward + built-from-map reverse re-verified above). Count
correction: the map holds **26** entries at drift base and HEAD, and the
oracle literal spells 26 — the prior "27" on both sides was a
prior-evidence slip, and the pin still matches exactly.
- **F-2 `filter-logic-operators`** — CONFIRM: records + tuple + derived
maps + consumers (member 41, sets.py traversal/normalize/permission,
factories splice) all unchanged in shape; `is_sequence` still the one
axis.
- **F-3 `subsystem-clear-lifecycle`** — CONFIRM: ledger/provenance
declarations + thin wrappers + registration re-verified
(`owner="filters.input_namespace"`, `before_bind=True`); no local clear
body (0 `ledger.clear` / map-`.clear()` spellings).
- **F-4 `set-type-naming`** — CONFIRM: pure consumer (bag names, related
refs, range stems); 0 `type_name_for` definitions (zero-probe).
- **F-5 `set-arguments-factory-bfs`** — CONFIRM: members 41–42 are still
the bodies the factory splices (import + splice line re-verified at
factories HEAD blob); 0 walk/collision/cache spelling here.
- **F-6 `active-input-permission-facade`** — CONFIRM: member 20 is still
the ledger the traversal config points at by reference; member 34 still
classifies through `cls._input_traversal()`; member 42 still populates
the ledger at bind. No permission rule defined here.
- **F-7 non-memberships** — CONFIRM with fresh zero-probes (count 0):
no Layer-6 getter/cache/keys, no queryset-seed machinery (member 43
resolves a field, not a seed), no sync-boundary surface.
- **L-a module path** — CONFIRM (pinned once; readers by name; W2's
"factory side" looseness note still accurate).
- **L-b search vocabulary** — CONFIRM (member 44 still deferred with the
consumer `TODO` and direct tests; unreachable from any wire path).
- **L-c kind ladder** — CONFIRM mechanics, REVISE census: 8 → 11 table
entries (+pk pair + model-choice tuple); strict zip still fails loud
(11 + 11 handlers verified by count).
- **L-d twin passes** — CONFIRM mechanics, REVISE census: 8 → 11 arms per
pass (+`_pk_multi` / `_pk` / `_model_choice` each); `TypedFilter`
convert-only intact; convert docstring kind order matches table order.
- **L-e scalar/element table** — CONFIRM mechanics, REVISE census:
`_scalar_from_model_field` callers → 5 (the 2 identity arms join element
+ range + fallback); model/choice arms still delegate outward.
- **L-f normalize helpers** — CONFIRM mechanics, REVISE census:
`_require_list_container` call sites 3 → 5 (+pk-multi, +model-choice);
GlobalID/enum/range helpers unchanged; D1a filed on the guard docstring.
- **L-g range naming** — CONFIRM (qualifier + cache key + documented
forward path untouched).
- **L-i model-field resolver** — CONFIRM mechanics + F-10 exclusion (sole
caller member 42; upstream delegate + guards intact; third spelling
named in the family, not counted with the runtime pair — see below).
- **L-k substrate aliases** — CONFIRM (5 aliases, same right-hand sides).
- **L-m owner-name reader** — CONFIRM: the `graphql_type_name` population
is byte-identical drift→HEAD in every file (10 files, same counts), so
the trio-sharing claim stands exactly as at drift base.
- **R-a..R-g** — all CONFIRM on fresh anchors (matrix axis 1): R-a/R-c in
the single-`return` order converter; R-b in the bare-return hook; R-d in
the 0-token twin grep; R-e in twin-def-here-absent; R-f in the intact
skip + library call; R-g in the light/heavy call census (3 light, 2
heavy).
- **Released edges (1)(2)(3)** — all CONFIRM: the literal pin is an
independent oracle (26/26, fails on change); the sharing claim holds
(populations identical); `construct_search` is still a documented
deferral with direct tests and no production consumer.

### This file's side of the s7 families (the family items own their rows)

- **F-9 `relation-identity-column`** (named by s7; owner the base.py
trio): this file holds exactly the 2 consumer annotation arms s7
counted — member 25 (called from the 2 pk convert arms) and member 27
(called from the 1 model-choice convert arm). `_model_choice_takes_list`
(member 26) is this file's own file-local list-ness predicate feeding
both model-choice arms, not an identity link. 0 identity definitions
here; every link composes the base.py owner by name.
- **F-10 `bound-filter-model-field-walk`** (named by s7; count-2 runtime
pair in base.py): member 43 examined-and-excluded with fresh counts —
its root is the FilterSet *class* (`filterset_cls._meta.model`) at
*build* time under member 42 (its sole caller), while the counted pair
roots at the bound filter's *parent* at *runtime*. Posit a runtime
parent-binding change → the pair moves, member 43 does not (0 here);
posit a class-root change → member 43 alone moves. The related third
spelling is named in the family, never merged into the count.

### Challenges (definition counts)

Authoritative definitions only; consumers, oracles, projections listed,
not counted.

- **Lookup spelling** (new lookup, renamed wire name): → 1 definition
(member 8). Consumers follow: forward `.get`, built-from-map reverse,
both `_form_key_for_python_attr` call sites, bag emission. Literal-pin
oracles fail; spec-027 Decision 3 projection moves intentionally.
- **New logical operator** (fourth, e.g. `xor`): → 1 definition (member
16 + its descriptor; both `BY_*` maps derive by comprehension in the
same edit). Emission/normalize/traversal/splice consumers iterate (0).
- **New filter primitive kind** (e.g. a JSON filter): → 1 definition
(append to member 30) + 2 handler declarations (one per pass; the
strict zip fails loud if a pass forgets one). Orders twin: 0 (R-c).
- **New namespace lifecycle slot**: → 1 definition
(`utils/inputs.py::make_set_input_namespace` /
`clear_generated_input_namespace`); the quartet unpack is a declaration
(0).
- **Input-name rule** (rename every generated input; new empty-token
policy): → 1 definition (`type_name_for` for the rule,
`pascal_case_or_raise` for the guard); bag/related/range consumers here
are 0.
- **New traversal axis** (sixth axis): → 1 definition (traversal shape +
mixin read); member 20 is the pointed-at ledger declaration (0); both
normalizers and all walkers reclassify through the one object.
- **New search prefix** (e.g. `~`): → 1 definition (member 7); member 44
follows; the spec-060 `TODO` consumer follows when it lands.
- **New relation-identity source** (e.g. a further key shape): → the F-9
trio in base.py (1 family); members 25/27 follow by construction (0
definitions here).
- **Bound-filter walk change** (parent binding): → the F-10 pair in
base.py (2, the family's count); member 43 does not move (0 here).
**Class-root change** (filterset `_meta` access): → member 43 alone
(1) — the exclusion that keeps it out of F-10's count.
- **Model-choice list-ness change** (e.g. the CSV wrapper stops counting
as list-taking): → member 26 only (1); its 2 in-file consumers (convert
+ normalize model-choice arms) follow. Single-sited package-wide (the
sole `isinstance(..., BaseCSVFilter)` spelling).

All probes static-reviewed (HEAD-bytes body inspection, `git grep HEAD`
populations, AST walk). No mutating proof: the target decides no
ordering beyond Q-object construction (unevaluated), no transactions, no
async behavior.

### New families / rows for Worker-0 (plan edits are Worker-0's)

- **L-n `model-choice-list-ness`** (NEW file-local row): member 26 —
whether a consumer model-choice filter's form field cleans a list.
Owner: member 26 itself (single-sited; sole `BaseCSVFilter` isinstance
spelling package-wide; 2 in-file consumers). Challenge count 1.
- No new families: F-9/F-10 are owned by s7 (this file contributes the 2
consumer arms + the examined-and-excluded third spelling recorded
above). No further cross-file rule found.
- **D1** (doc-only defect, 2 docstring censuses) for closeout homing.

### Defects (run 8)

- **D1 (filters/inputs.py owner; two docstring censuses undercount their
consumers after the drift).** (a) `_require_list_container` names 4
filter classes ("GlobalIDMultipleChoiceFilter / BaseCSVFilter /
ListFilter / ArrayFilter") but serves 5 normalize call sites covering 6
(+`RelationPkMultipleFilter`, +model-choice list). (b)
`normalize_input_value` names 3 list-returning classes
("GlobalIDMultipleChoiceFilter / ListFilter / ArrayFilter") but 5 arms
covering 6 return lists (+pk-multi, +model-choice, +CSV — the CSV
omission predates the drift, the other two are drift-new). No behavior
is wrong; each miscounted census is a docstring-contradicts-body record
for Worker-0 homing. Never fixed inside this item.

### Pending execution

None. Every proof is static-reviewed; no ordering / transactional / async
behavior is decided here, so no execution-deferred entry exists. The
sharded/Postgres cells are inapplicable by construction (no alias /
`using=` decision, no dialect branch in this file).

### Judgment (run 8)

Zero-edit re-trace: matrix discharged against the current surface (orders
twin re-read at HEAD, async absence re-verified, identity/marker
populations counted at HEAD bytes), 51/51 units assigned (2 s7-family
consumer arms + 1 new file-local row recorded, remainder CONFIRM or
census-REVISE of run-7 rows), challenges recorded with definition
counts, one doc-only defect filed, no pending execution. The drift's two
behavior bodies compose the existing single-sited helpers by name at
every link (identity chain, scalar/enum delegates, shape gate, kind
table + strict zip); the one genuine re-derivation on this seam (F-10)
and the two stale censuses (D1) are routed out, not fixed here.

### Implementation (run 8)

No production edits (file item; reviewer role — no edit rights on
production code). No new tracked files besides this artifact (untracked
`??`, as in run 7). Item-scoped diff vs `ITEM_BASELINE`
`8346655631d312debde1a8657593024854770547` for
`django_strawberry_framework/filters/inputs.py`: empty. The worktree's
59+/29- on the target is concurrent truth/range dirt, attributed by
content above and untouched. No pytest run (a zero-edit file item needs
none — every claim is a HEAD-bytes count or body reading; the one
authorized focused test is unneeded). No `workspace.py` runs (no
source-mutating proof exists for this target). No repo scratch files
(all probes read-only: `git show HEAD:`, `git grep HEAD`, AST walk on
HEAD bytes via a throwaway `/tmp` copy only).

## Run-8 verification (Worker 2)

Traced at HEAD `83998e08` bytes against
`ITEM_BASELINE 8346655631d312debde1a8657593024854770547`. No
worker-memory read; sources were HEAD bytes (`git show HEAD:`), HEAD
populations (`git grep HEAD`), and two AST instruments of my own.
Worktree bytes were read only for dirt attribution. All line numbers
below are HEAD lines of
`django_strawberry_framework/filters/inputs.py` unless named otherwise.

### Fingerprints (re-hashed)

- Target: HEAD blob `2c853e24` (1206 lines) is the traced bytes;
  worktree `c933bb5d` (1236 lines); drift base `0c0537e2` blob
  `82b52d97` (1073 lines, identical to the run-7 traced bytes);
  pre-merge `9aaaad5d` blob `a932dbf8` (1103 lines). All match the
  re-trace record.
- Connected sources re-hashed, all 13 match: `filters/sets.py`
  `3d307402`, `filters/base.py` `e2e683a8`, `filters/factories.py`
  `c400d646`, `filters/__init__.py` `8ce8b96d`, `orders/inputs.py`
  `39e39d29` (406 lines), `utils/inputs.py` `7b88d358`, `registry.py`
  `9d2021eb`, `sets_mixins.py` `6764d455`, `utils/strings.py`
  `a326167d`, `utils/input_values.py` `3c17224f`, `conf.py`
  `10096f84`, `types/converters.py` `d146b23f`,
  `types/definition.py` `5bf257c3`; oracle
  `tests/filters/test_inputs.py` `769e7b45`.
- Item-scoped diff `git diff 83466556... -- filters/inputs.py` is 0
  bytes. No `## Owned changes` row names this file.

### Own trace of the drift delta (expectation-first)

Expected from the queue brief: two behavior bodies (raw-pk input
shapes; ModelChoice identity arms + dispatch entries) atop typing-only
drift. My instrument: per-symbol AST dump with annotations, docstrings,
defaults, and `cast` wrappers stripped, drift base vs HEAD. Result: 18
of 21 compared functions stripped-identical; the three that differ are
`convert_filter_to_input_annotation` (+3 arms), `normalize_input_value`
(+3 arms), and `_build_logic_fields` (`list[x]` → `GenericAlias`,
runtime-identical, plus an annotation + comment — verified by hand).
HEAD adds exactly 3 top-level symbols
(`_relation_identity_annotation`, `_model_choice_takes_list`,
`_model_choice_identity_annotation`) plus 3 kind-table entries and the
import deltas. `git log 0c0537e2..HEAD` on the target names exactly the
two behavior commits (`bbe54687` 46+/1-, `57131b99` 65+/3-, both stats
re-verified) plus five typing commits. The drift is therefore purely
additive behavior plus typing/prose — a mechanical form of the
re-trace's hunk-by-hunk reading.

### Own counts (re-derived, HEAD bytes)

- Lookup map: 26 entries at HEAD and at drift base (AST count both);
  oracle literal 26 entries; dicts proved equal mechanically. Sole
  `LOOKUP_NAME_MAP` hits in the oracle file: import :54, section
  comment :90, assert :124, docstring :342 — no test iterates the map.
- Kind ladder: 8 entries at drift base → 11 at HEAD
  (+`RelationPkMultipleFilter`, +`RelationPkFilter`, +model-choice
  tuple); 11 handlers per pass, 22 total (counted at both
  `_filter_input_prechecks(...)` call sites); strict-zip body
  stripped-identical.
- Scalar helper: `_scalar_from_model_field` called from 5 lines (:373
  member 25, :409 member 27, :473 element arm, :478 method-filter
  fallback, :591 range arm).
- Guard: `_require_list_container` called from 5 normalize arms (:686
  gid-multi, :693 pk-multi, :703 model-choice, :709 csv, :716 list) vs
  3 at drift base (+pk-multi, +model-choice).
- List-returning normalize arms: 5 (:687, :694, :704, :710, :717) vs 3
  at drift base; covering 6 class groups.
- Identity chain: `relation_identity_column` code callers 2
  (base.py:1166 + :365 here); `model_choice_identity_column` code
  callers 1 (:399 here); `_relation_identity_annotation` callers 2
  (:573, :576, both convert pk arms);
  `_model_choice_identity_annotation` callers 1 (:579, convert
  model-choice arm); `_model_choice_takes_list` callers 2 (:580
  convert, :701 normalize), zero outside the target; the
  `isinstance(..., BaseCSVFilter)` spelling is single-sited (:384).
- Third spelling: `_model_field_for_filter` callers 1 (:1077 inside
  `_build_input_fields`); root `filterset_cls._meta.model` (:1145).
- `graphql_type_name`: 10 files, per-file counts identical drift→HEAD.
- Async tokens: 0 `async def` / 0 `await`; 0
  `run_in_one_sync_boundary` / `sync_to_async` / `base_queryset` /
  `model_for` refs.

### Per-row judgments

Every row below is CONFIRM on my own evidence unless noted; counts
are mine from the section above.

- F-1 CONFIRM rule, REVISE count 26-not-27 (both sides recounted,
  dicts equal; the run-7 "27" was a slip with the oracle still
  matching).
- F-2 CONFIRM (records + tuple + derived maps + consumers unchanged
  in shape; the logic-fields body differs only by the
  runtime-identical `GenericAlias` spelling).
- F-3 CONFIRM (registration re-verified
  `owner="filters.input_namespace"`, `before_bind=True`; no local
  clear body).
- F-4 CONFIRM (pure consumer; 0 `type_name_for` definitions — C2
  notes the probe wording).
- F-5 CONFIRM (factories :45 import + :125 splice re-verified; 0
  walk/collision/cache spelling here).
- F-6 CONFIRM role, REVISE one supporting clause (C1): the ledger
  link (sets.py `_permission` config :1262-1270 pointing at the :237
  ledger by reference) and the bind-time populate (:1116)
  re-verified; no permission rule defined here.
- F-7 CONFIRM non-memberships (zero-probe re-run; member 43
  resolves a field, not a seed).
- L-a CONFIRM; L-b CONFIRM (sets.py:1424 comment + direct tests
  only, no production call); L-c/L-d CONFIRM mechanics, REVISE
  census 8→11 (11+11 handlers counted); L-e CONFIRM mechanics,
  REVISE census (scalar callers 5); L-f CONFIRM mechanics, REVISE
  census (guard sites 3→5; D1a filed); L-g CONFIRM (both range
  bodies stripped-identical); L-i CONFIRM mechanics + F-10
  exclusion; L-k CONFIRM (5 aliases, same right-hand sides); L-m
  CONFIRM (10-file population identical).
- R-a..R-g CONFIRM on fresh anchors (single-`return` order
  converter :207; bare-return hook with the Decision-8 docstring in
  orders/factories.py:109; 0 hide/lookup/logic tokens in the twin;
  `_ensure_field_specs` twin-:351 vs 0 here; intact skip + library
  call; light/heavy call census 3/2 in the R-g population).
- Released edges (1)(2)(3) CONFIRM (26/26 pin; sharing populations
  identical; deferral with direct tests, no production consumer).

### Adversarial focus

1. F-9 — challenged both arms. Read member 25 (:354-373) and member
   27 (:387-409) whole: each resolves its column through exactly one
   base.py call (`relation_identity_column(model_field)` /
   `model_choice_identity_column(filter_instance, model_field)`),
   fails loud with `ConfigurationError` on `None`, and maps the
   column through the shared `_scalar_from_model_field`. No `_meta`
   walk, no `to_field_name` read, no FK-follow loop in either body
   — 0 identity definitions here. Caller counts re-derived: 2 + 1,
   all inside the convert pass; the normalize model-choice arm
   calls only the L-n predicate, never the annotation. Counts match
   s7 exactly (2 and 1). Verdict stands.
2. F-10 — read all three spellings myself. Member 43 (:1120-1150)
   roots at the passed-in FilterSet *class*
   (`filterset_cls._meta.model`, :1145) and runs at *build* time
   under member 42 (sole caller :1077, inside
   `_build_input_fields`, which runs at finalize). The counted pair
   roots at the bound filter's *parent* instance at *filter* time
   (`IntegerInFilter.filter`'s parent→meta→model→`get_model_field`,
   and `_relation_identity_column_for`'s identical parent root).
   Posit a parent-binding change → the pair moves, member 43 does
   not (0 here); posit a class-root change → member 43 alone
   moves. Different roots, different lifetimes: correctly
   excluded, correctly named-but-uncounted. Verdict stands.
3. L-n — warranted, correctly homed. Single definition (:376), 2
   in-file consumers feeding both passes (:580 convert list-wrap,
   :701 normalize list-vs-scalar), zero callers elsewhere, sole
   `BaseCSVFilter` isinstance spelling package-wide (:384).
   Folding targets rejected: not F-9 (list-ness, not column
   resolution); not L-d (spans both passes, neither pass owns it);
   not L-f (convert consumes it too); not L-e (no scalar/enum
   delegation). Narrowest cohesive owner is this file — no base.py
   consumer exists. New file-local row owed. Verdict stands.
4. F-1 — recounted by AST at both revisions (26/26) with dict
   equality proved mechanically; oracle hits enumerated (import,
   comment, assert, docstring — no iteration). The run-7 "27" was
   wrong on both sides with the pin still green. REVISE stands.
5. D1 — both miscounts verified at HEAD bytes. (a) Guard docstring
   (:751-752) names 4 classes; 5 call sites serving 6 groups
   (+`RelationPkMultipleFilter`, +model-choice list) — drift-new.
   (b) Normalize docstring (:656-660) names 3; 5 list-returning
   arms serving 6 (+pk-multi, +model-choice, +CSV). The CSV
   omission predates the drift (drift-base docstring
   byte-identical, 3 arms serving 4 then). Doc-only, minor, moves
   nothing. Homing: ENDORSE Worker-0 homing the doc-only repair to
   the closeout homing pass. Neither D1 paragraph is concurrently
   rewritten (the :762 worktree hunk touches the guard's raise
   message, not its docstring; no worktree hunk falls in :640-746),
   so the repair authors cleanly against HEAD bytes.

### Enumeration (member-by-member)

My instrument (top-level Assign/AnnAssign/FunctionDef/ClassDef plus
class members): 74 module statements = 1 docstring + 25 imports (20
`ImportFrom` + 5 `Import`) + 1 `TYPE_CHECKING` block + 47 rule/value
tops; the class carries 4 AnnAssign fields; 47 + 4 = 51. Every one
of my 51 maps onto a re-trace row 1–47 exactly once (row 12 folds
the class + 4 fields; row 21 is the tuple unpack at :238).
Dual-homed rows (#5, #20, #34, #41, #42) are one unit with two
roles, not double counts. Exclusions (docstring as projection, 25
imports as references, `TYPE_CHECKING` as type-only) judged sound.
51/51 assigned, none doubled.

### Matrix

All six axes discharged against the real surface — agree on each,
on my own evidence above (twin re-read at HEAD with all seven
divergences re-anchored; async absence re-verified; identity links
compose by name with caller counts matching s7; round-trips
symmetric in both directions with strict-zip arity counted; oracles
literal, including the `_relation_identity_intact` exclusion;
omission enumerated with the new arms extending R-a/R-c and no
twin).

### Dirt attribution

HEAD-vs-worktree 59+/29- in 14 regions, all concurrent-external: no
ledger row names this file, and added-line vocabulary is confined
to the truth migration (`truth.*` refs, narrowed imports —
worktree carries 22 `truth.` refs and 0 `_safe_*`; HEAD's single
`truth.` hit is the "source of truth" prose at :451) plus the
range fail-loud rewrite (unknown-axes + non-range
`ConfigurationError` arms with the extended docstring contract)
plus one comment reword. No new definition, call, or branch
outside the range arms. Behavior-site contact (worktree bytes
differ; the HEAD-bytes trace is unaffected, out of scope): member
39 `_normalize_range_value` body, and error-message spellings
inside members 22/25/27/28/29/32/33/35/38/42/43 plus the import
block. The drift's new decision structure (column links, kind
entries, arms, guards) is intact in the worktree — message
spellings only. The pre-merge `9aaaad5d` bytes (54+/24-, 17
`truth.` refs, 0 new-shape refs) served read-only attribution and
no verdict depends on them.

### Defects (Worker 2)

None. D1 endorsed as filed (see homing above).

### Record-precision notes (no resubmission; move no verdict, index row, or decision)

- C1: F-6's "member 34 still classifies through
  `cls._input_traversal()`" names a call that does not exist in
  this file — the symbol appears 0 times in the target at HEAD and
  at drift base (verified by grep both revisions; the clause is
  carried from the run-7 text). Member 34 classifies the inactive
  sentinel through imported `is_inactive_value` (:682; shared
  input-values rule, still 0 local definitions). The
  `cls._input_traversal()` walkers live in sets.py (:2430) and
  read the ledger member 20 points at — the F-6 contributor
  verdict stands; the family record should carry the corrected
  mechanism.
- C2: the static zero-probe's "or references" wording overclaims:
  `type_name_for` / `register_subsystem_clear` have 9 substring
  hits (alias, docstring prose, the :1073 consumer call, the
  register import + call). The probe proves 0 DEFINITIONS (no
  second owner) — which is what the verdict needs — and the
  references are the recorded consumer roles (F-3 member 47, F-4
  member 42). Twin-only members (`Ordering`,
  `_ensure_field_specs`, `get_filterset_class`,
  `_dynamic_filterset_cache`) are 0 references as claimed.

### Pending execution

None. Every proof is HEAD-bytes body inspection, HEAD
populations, or AST comparison; no ordering / transactional /
async behavior is decided here. The sharded and Postgres cells are
inapplicable by construction (no alias / `using=` decision, no
dialect branch in this file) — agreed.

### Verdict

`Status: verified`. Zero-edit re-trace: matrix discharged, 51/51
members assigned, every verdict row survives on independent
evidence with my own counts, one doc-only defect endorsed for
closeout homing, no pending execution. Family impact: F-9
consumer arms recorded (2, this file's side), F-10 exclusion held
(third spelling named, uncounted), 1 new file-local row L-n
`model-choice-list-ness` owed; F-1 count REVISE and kind-ladder
census REVISEs carried as recorded; zero owned changes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[input-values]: ../../django_strawberry_framework/utils/input_values.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-filter-inputs]: ../../tests/filters/test_inputs.py

<!-- examples/ -->
[test-kanban-api]: ../../examples/fakeshop/test_query/test_kanban_api.py
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
