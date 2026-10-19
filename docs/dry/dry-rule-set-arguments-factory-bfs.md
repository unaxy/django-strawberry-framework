# DRY review: `set-arguments-factory-bfs`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is the set-arguments factory BFS: every reachable
set-family root BFS-builds its Strawberry input classes through one
walk plus per-class collision check plus idempotent cache plus
subclass-rejection guard, parameterized per family by hook attributes
and one `_build_input_triples` override; per-field emission, input
naming, materialization, namespace clear, sidecar binding, and the
Decision-11 lazy helper ride the same shared substrate. The owner
candidate, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`,
is re-derived below, not inherited.

Scope held in this item: the BFS walk, the collision rule, the
idempotent caches, the subclass guard, the per-field emission
scaffold, the input-name delegate, the materialize/clear lifecycle,
the sidecar bind driver, and the lazy-annotation helper. The Layer-6
dynamic-set-class machinery (`make_dynamic_set_getter`,
`normalize_set_meta_for_factory`, `make_set_meta_cache_key`,
`create_dynamic_set_class`, both `get_*_class` getters, both Layer-6
caches, both reserved-key literals) is the queued sibling
`dynamic-set-class-getter`; class-creation and input-build are
different contracts, and the sibling owns the first. Set-type naming
(`ClassBasedTypeNameMixin.type_name_for`) and the related-target
lifecycle (`RelatedSetTargetMixin`) are composed here by name and
homed with their owners. Each is excluded with a contract difference
below, never absorbed.

Traced at current bytes (HEAD `5c3496e0` plus working tree).
Fingerprints (short blob ids; full ids in the report-back):

| File | WT `git hash-object` | HEAD `git rev-parse HEAD:` | Baseline `f2cc9bb9:` |
|---|---|---|---|
| `utils/inputs.py` | `0575e9b2` | `0caa3416` | `0575e9b2` |
| `filters/factories.py` | `7576caea` | `7576caea` | `7576caea` |
| `orders/factories.py` | `17204c27` | `17204c27` | `17204c27` |
| `filters/inputs.py` | `afad6451` | `d8febb10` | `afad6451` |
| `orders/inputs.py` | `6d97fc75` | `db124623` | `6d97fc75` |
| `types/finalizer.py` | `0807fea7` | `662826eb` | `0807fea7` |

Baseline equals WT on all six files: the item baseline captured the
working tree at dispatch, so every hunk below predates this item. Four
of six files are dirty versus HEAD; all dirt is concurrent work,
attributed by diff content: the bug-hunt truth migration
(`truth.qualname` / `truth.is_instance` / `truth.static_attr` /
`truth.name` / `truth.kind` / `truth.render` / `truth.label` /
`truth.bases` / `truth.text` / `truth.static_attr` replacing
`__qualname__` / `isinstance` / `getattr` / `_safe_arg_repr` /
`_safe_type_name` reads), `except BaseException` narrowing to
`TypeError`, the `_META_CONTAINER_TYPES` / `_UNORDERED_TYPES` /
`_is_one_of` extraction, and typing/docstring reflow. None of it
appears in the plan's `## Owned changes` ledger (which holds only the
walker D1 fix and adopted orphans in `mutations/inputs.py`,
`types/resolvers.py`, `inspect_django_type.py`, `list_field.py`,
`registry.py`, `relay.py`, `types/relay.py`, plus tests), so all of it
is untouchable here and left alone. Both factories files are clean
(WT equals HEAD).

The rule-region census is identical at WT and HEAD: all 16 family
symbols count equal under both states (`_ensure_built` 1,
`_build_input_triples` 3, `_build_class_type` 1,
`emit_set_input_field_triples` 1, `_bind_sidecar_sets` 1,
`materialize_generated_input_class` 1, `duplicate_name_message` 1,
`clear_generated_input_namespace` 1, `make_set_input_namespace` 1,
`set_input_type_name` 1, `build_lazy_input_annotation` 1,
`_build_logic_fields` 1, `_audit_unregistered_related_filter_targets`
1, and the three factory classes 1 each). The dirt respells
definition interiors without adding, removing, or re-homing any site,
so the verdict holds at both states. Line numbers cited are WT lines.
Prior file/family records were read as orientation and every claim
below is re-derived fresh; nothing is inherited.

Sites found, by role. One definition per mechanism; every other site
composes by name.

- Definitions (all in `django_strawberry_framework/utils/inputs.py`
  unless noted).
  - `GeneratedInputArgumentsFactory` (`:1745`): the BFS substrate.
    Its parts are one definition, not several: `__init_subclass__`
    (`:1793`, direct-subclass-only guard),
    `_collision_registry` (`:1816`, spec-named registry read),
    `arguments` (`:1825`), `_ensure_built` (`:1833`, FIFO walk plus
    enqueue-time seen gate plus per-class collision raise plus
    idempotent build), `_build_class_type` (`:1884`, triples to
    `build_strawberry_input_class` to both caches), and the
    `_build_input_triples` family hook (`:1920`, raising
    `NotImplementedError`).
  - `emit_set_input_field_triples` (`:177`): the per-field emission
    scaffold (flatten to camel-case to optional kwargs to related
    lazy-ref versus leaf, plus the python-attr and GraphQL-name
    collision arms, plus staged `FieldSpec` commit).
  - `set_input_type_name` (`:116`): the naming delegate over
    `ClassBasedTypeNameMixin.type_name_for`.
  - `materialize_generated_input_class` (`:1450`) plus
    `duplicate_name_message` (`:1493`): the module-global pinning
    plus the one collision sentence both claim sites share.
  - `make_set_input_namespace` (`:462`) plus
    `clear_generated_input_namespace` (`:1674`): the heavy ledger
    quartet plus the heavy clear (ledgers, factory caches,
    per-subclass `_lifecycle` binding attrs).
  - `build_lazy_input_annotation` (`:1596`): the Decision-11
    validate-plus-ledger-plus-forward-ref body.
  - `types/finalizer.py::_bind_sidecar_sets` (`:1775`): the ordered
    five-subpass sidecar driver over `_SidecarBindingSpec`.
  - `filters/inputs.py::_build_logic_fields` (`:981`): the filter
    operator-bag splice (LOGIC_OPERATORS-driven, inside-list shape).
- Family declarations (parameterize the owners; define no rule).
  - `filters/factories.py::FilterArgumentsFactory` (`:79`) and
    `orders/factories.py::OrderArgumentsFactory` (`:61`): fresh
    `input_object_types` dicts, fresh spec-named collision
    registries, seven hook attributes each, one
    `_build_input_triples` override each (filter splices the
    operator bag, order returns bare triples).
  - `filters/inputs.py::_build_input_fields` (`:1007`) and
    `orders/inputs.py::_build_input_fields` (`:217`): entry-shape
    adapters (filter groups `get_filters()` plus the
    HIDE_FLAT_FILTERS pre-filter; order walks `get_fields()`
    directly) delegating emission to the shared scaffold through
    four family closures each.
  - `types/finalizer.py::_bind_filtersets` (`:1996`) and
    `_bind_ordersets` (`:1848`): `_SidecarBindingSpec` declarations
    over the shared driver.
  - Re-export aliases, all `is`-identical bindings, zero
    definitions: `FieldSpec`, `build_input_class`, `_camel_case`,
    `_input_type_name_for`, `_iter_filterset_subclasses` /
    `_iter_orderset_subclasses` in both family `inputs` modules.
- Consumers composing by name (restate nothing).
  - Finalizer subpass 4 (`:1837`-`:1845`): touches `.arguments`,
    materializes every built class from `input_object_types`.
  - `materialize_input_class` / `clear_filter_input_namespace` /
    `clear_order_input_namespace`: thin spec-named wrappers over
    the namespace quartet (Decision-9 addressability).
  - `filter_input_type` / `order_input_type`: thin leaf wrappers
    over `build_lazy_input_annotation` with six family params each.
  - `_expand_filterset` / `_expand_orderset` bound as the
    driver `expand` arm; `_bind_filterset_owner` /
    `_bind_orderset_owner` bound as the driver `bind_owner` arm
    over the shared `_bind_set_owner_common` (`:1142`).
  - `sets_mixins.py` (`:201`) and `filters/base.py` (`:1398`):
    docstring references to `_ensure_built` (projections, not
    calls); `orders/__init__.py` (`:14`) and the filter leaf note
    the factory stays out of `__all__` by spec Decision 2.
- Oracles (independent: spell literals and drive behavior, never
  read the owners to compute expectations).
  `tests/filters/test_factories.py` pins BFS reachability, cycle
  handling, double-enqueue dedupe, collision-refusal wording,
  flattened and GraphQL-name collisions, idempotency,
  subclass rejection, placeholder skip, and the filter empty
  guard; `tests/orders/test_factories.py` pins the order twin
  (reachability, cycles, leaf/related shapes, collision wording,
  idempotency, shared-across-instances cache, subclass rejection,
  placeholder skip, three empty-guard arms, dedupe);
  `tests/utils/test_inputs.py` (62 tests) pins the shared
  substrate; `tests/filters/test_finalizer.py`,
  `tests/orders/test_finalizer.py`, and
  `tests/orders/test_composition.py` pin bind/materialize
  composition. Per spec Decisions 9 the oracles address
  `input_object_types` and the collision registries directly;
  that addressability is the specified contract, not oracle rot.
- Projections. Factory class docstrings (cookbook-BFS attribution,
  FIFO-versus-LIFO note, cache/registry contract), the
  `_SidecarBindingSpec` subpass docstrings, spec-027/spec-028
  Decision passages, and the glossary `FilterSet` / `OrderSet`
  entries.

## Verification

### Matrix

1. Cross-flavor policy mirroring. The twin was read first and whole:
   both factories files (186 and 161 lines), both `_build_input`
   adapters, both `_bind_*` declarations, both leaf helpers. Every
   shared mechanism is one body in `utils/inputs.py` or the
   finalizer driver with per-family declarations at the call sites;
   every remaining twin difference is an exclusion below with a
   contract difference (operator bag, leaf shape, entry shape,
   pre-filter, audit arm, owner axes, model slot, reserved
   vocabulary, cache/registry/ledger namespaces). No second walk,
   no second collision rule, no second cache discipline found.
2. Sync/async twins. Inapplicable with reason: zero `async def`,
   zero `await`, zero `sync_to_async` in either factories file
   (token sweep); the BFS build plus `type(...)` construction are
   pure synchronous construction at finalize time, executing inside
   no queryset boundary (no `base_queryset`,
   `run_in_one_sync_boundary`, `model_for`, or queryset token in
   either factory). The base factory and the emission scaffold
   likewise carry no async surface.
3. Derived rather than repeated knowledge. Searched. Input type
   names arrive only via `set_input_type_name` to
   `type_name_for`: the sole `f"..."InputType` construction in the
   package outside the naming owner is the filter-only
   `RangeFilter` sub-input name (`filters/inputs.py:878`), which is
   a per-filterset-scoped embedded class name with no twin and no
   registry participation (documented at the site), not a
   re-derivation. Cache keys, the Meta synonym rule, and class-Meta
   write-back all route to the sibling-owned helpers. No local
   re-derivation of any shared fact.
4. Inverse / round-trip pairs. Searched. Build versus normalize is
   the pair: the emission scaffold is the single writer of the
   `_field_specs` provenance grammar, and both families read it
   through one shared traversal mechanic
   (`utils/input_values.py::iter_active_fields` driven by each
   family's `_permission` traversal config). One grammar, one
   writer, two lifecycle-separated halves (finalize-time build,
   request-time read); not two definitions. `get_*_class`
   explicit-passthrough versus dynamic-build halves are two arms
   of one sibling-owned getter, not a pair.
5. Contracts restated in another medium. Searched. Four media carry
   this family's contracts: production code (definitions plus
   declarations), authoritative contract sources (spec-027 /
   spec-028 Decisions 3/6/8/9/11/12 for the shared-base split, the
   no-operator-bag posture, the Decision-9 cache names plus clear
   lifecycle plus ledger/registry split, the Decision-11 helper,
   and the deferred Layer-6 non-goal), independent oracles (named
   above), and projections (docstrings, spec passages, glossary).
   Cookbook twins (`filter_arguments_factory.py` /
   `order_arguments_factory.py`) are out-of-population sources.
   No test or doc restates a package rule as an independently
   maintained definition.
6. Enforcement by omission. Enumerated. The order side lacks an
   operator bag by spec-028 Decision 8 (rejection, not a gap);
   lacks a post-expand audit because it has no visibility scoping
   or related-target registration rule (rejection, not a gap);
   carries `_ensure_field_specs` without a filter twin, but that
   warm-up belongs to the normalize path already judged file-local
   to `orders/inputs.py`, and no contract source in THIS family's
   rule demands it on the filter side, so no defect is filed.
   Neither factory appears in its leaf `__all__` by spec Decision
   2 on both sides (verified absent). No omission in this family's
   rule lacks its guard where a contract source requires one.

### Enumeration

Instrument: exact `def` / `class` census by `grep` over
`django_strawberry_framework/`, plus exact-call-site census for
each shared helper, plus a whole-package sweep for the rule's
mechanism vocabulary (`pending.pop`, `seen.add`, `visited`,
`input_object_types`, collision registries, `_build_input_fields`,
`RangeInputType`). Population: 16 definition sites plus 2
entry-shape adapters plus 2 bind declarations plus 4 thin leaf
wrappers plus 10 re-export aliases plus 6 mechanism-adjacent walks
audited and excluded. Every member lands below: one CONFIRM
finding, 14 exclusions each with contract difference plus trigger,
zero unassigned.

### Challenges

Authoritative definitions only; consumers, oracles, and projections
that also move are listed, never counted. All challenges
static-reviewed at WT bytes; the FIFO-ordering behavior is
additionally pinned by executed oracles (one re-run fresh in the
shared venv: `tests/orders/test_factories.py::test_factory_handles_cycles_via_seen_set`,
1 passed).

- C1 BFS traversal. Posit FIFO to LIFO or a new seen gate: 1
  definition moves (`_ensure_built`). Consumers (finalizer subpass
  4 both sides, both clear wrappers, both factory test modules)
  follow by construction.
- C2 Factory collision wording and rule. Posit a factory-only
  wording change: 1 definition (the `_factory_label` prepend in
  `_ensure_built`). Posit a skeleton change: 1 definition
  (`duplicate_name_message`) with 2 consumers following
  (materialize plus factory). No per-family collision spelling
  exists to move.
- C3 Per-field emission. Posit a flatten, camel-case, optional,
  placeholder-skip, or collision-arm change: 1 definition
  (`emit_set_input_field_triples`). Both `_build_input_fields`
  adapters follow; their closures move only if family leaf
  semantics change, which is a different rule.
- C4 Logic operator vocabulary. Posit a fourth operator: 1
  definition (`LOGIC_OPERATORS`); the filter hook splices
  `_build_logic_fields` wholesale (0), the order side is
  unreachable by construction.
- C5 Materialization. Posit an idempotency or distinct-class
  rule change: 1 definition
  (`materialize_generated_input_class`). Both family
  `materialize_input_class` wrappers follow.
- C6 Heavy clear. Posit a population change (new ledger, new
  binding attr): 1 definition
  (`clear_generated_input_namespace`); binding names come from
  each base's `_lifecycle` descriptor (0 re-spellings).
- C7 Sidecar bind order. Posit a subpass reorder or a new shared
  subpass: 1 definition (`_bind_sidecar_sets`). Both `_bind_*`
  declarations follow; a family-only audit stays a `post_expand`
  arm (0 shared movement).
- C8 Input-class naming. Posit a suffix or empty-token change: 1
  definition (`ClassBasedTypeNameMixin.type_name_for`); the
  delegate plus both re-exports follow (0).
- C9 Decision-11 helper. Posit a validation, ledger, or
  forward-ref change: 1 definition
  (`build_lazy_input_annotation`); both leaf wrappers follow (0).
- C10 Owner-bind skeleton. Posit a first-bind, idempotency, or
  target-agreement change: 1 definition
  (`_bind_set_owner_common`); both `bind_owner` adapters follow
  (0), family check arms move only on their own axis.

## Findings

### F1: the set-arguments factory BFS is single-owned (CONFIRM, zero-edit)

Contract plus variation. Every reachable set-family root
BFS-builds its Strawberry input classes through one FIFO walk with
an enqueue-time seen gate, one per-class collision check, one
idempotent cache per family namespace, and one subclass-rejection
guard; per-field emission, input naming, materialization,
namespace clear, sidecar binding, and lazy-helper construction
ride the same substrate. The rule legitimately varies on family
namespace (filter versus order caches, registries, ledgers,
module paths), family hook attributes (labels, related seams),
leaf semantics (operator bags versus `Ordering`), the filter-only
operator bag, the filter-only pre-filter and audits, and the
family owner-check axes. All variation is declared, never
re-spelled.

Sites plus roles. Definitions: `GeneratedInputArgumentsFactory`
(walk, collision, cache, guard, `__init__` / `arguments` /
`_ensure_built` / `_build_class_type`), the
`_build_input_triples` hook signature, `emit_set_input_field_triples`,
`set_input_type_name`, `materialize_generated_input_class` plus
`duplicate_name_message`, `make_set_input_namespace` plus
`clear_generated_input_namespace`, `build_lazy_input_annotation`,
`_bind_sidecar_sets`, `_build_logic_fields`. Declarations: both
factory subclasses (members: caches, registries, seven hook
attributes, one hook override each), both `_build_input_fields`
adapters, both `_bind_*` declarations, the re-export aliases.
Consumers, oracles, and projections as inventoried under System
trace.

Challenges. C1 through C10 above: 1 definition per change across
ten variation axes; family attributes and adapters are
declarations (principle 1 shape, already realized).

Owner plus lifetime. `GeneratedInputArgumentsFactory` owns the
walk; the emission scaffold, naming delegate, materialize/clear
lifecycle, and lazy helper are co-sited in `utils/inputs.py`
because both families import that module without a cycle (same
contract as `utils/connections.py`), and the bind driver is
co-sited in `types/finalizer.py` because binding is finalization.
No stored derivation outlives a finalize except the class-level
caches and module-global pins, whose lifetime is the documented
Decision-9 clear bus (`registry.clear()` resets ledgers, factory
caches, and `_lifecycle` binding; parked globals are replaced in
place, never stripped).

Migration. None: every site already composes by inheritance,
delegation, or declaration. Zero-edit verdict.

Distinct behavior. The exclusions below; each stays separate and
is recorded at its owner prose or in this artifact.

Behavioral proof. Static-reviewed throughout (subclass bodies are
attributes plus one hook each; adapters are entry-shape plus
closures; no walk, collision, cache, emission, naming,
materialize, clear, bind, or helper spelling appears outside its
owner), corroborated by executed independent oracles: the BFS
reachability, cycle, dedupe, collision, idempotency, placeholder,
empty-guard, subclass-rejection, and bind/materialize pins named
above, all of which fail on any second definition that drifts
(they spell literals and drive both families). One oracle
re-run fresh in the shared venv passes
(`test_factory_handles_cycles_via_seen_set`). No
execution-deferred proof: nothing here decides ordering beyond
the oracle-pinned FIFO discipline, and no change is proposed.

Structural gate. None owed beyond the existing oracles: the
single-owner shape is already pinned by tests that address both
families' caches and registries directly and by the
`__init_subclass__` guard that rejects the plausible bypass (a
grand-subclass inheriting shared mutable caches). A bespoke
existence test per helper would be machinery, not a gate.

Coupling. None: zero edits, zero new symbols, zero import moves.

Freshness. Family-file fingerprints as tabled under System trace
(WT, HEAD, and item-baseline states); searched population is the
whole `django_strawberry_framework/` tree; contract sources are
spec-027/spec-028 Decisions 3/6/8/9/11/12; tests are the oracle
modules named above; every module excluded on the strength of its
body is named in the exclusions with its mechanism. Any
fingerprint change reopens this finding.

### Exclusions (contract difference plus reconsideration trigger each)

- E1 Operator-bag hook merge. Filter `_build_input_triples`
  splices `_build_logic_fields`; order returns bare triples.
  Difference: the filter input contract includes `and_` / `or_` /
  `not_` (spec-027) while the order contract has no operator bag
  (spec-028 Decision 8); merging is a mode flag (principle 5).
  Trigger: either family changes its operator-bag posture.
  Durable home: the base hook docstring plus this artifact.
- E2 Leaf-semantics merge. Filter leaves build per-field
  operator-bag classes (plus range sub-inputs); order leaves are
  uniformly `Ordering | None` (spec-028 Decision 5). Difference:
  operator-bag versus scalar-direction contracts. Trigger: a
  shared leaf shape across families. Home: both `_leaf_of`
  closures plus this artifact.
- E3 Entry-shape merge. Filter entries are grouped lookup bags
  from django-filter expansion; order entries are
  `RelatedOrder | None` from `OrderSet.get_fields()`.
  Difference: upstream expansion contracts (django-filter flat
  map versus own metaclass map). Trigger: a unified Layer-4
  entry shape. Home: both `_build_input_fields` docstrings.
- E4 Pre-filter port. `HIDE_FLAT_FILTERS` expanded-child skip
  exists only on the filter side. Difference: only the filter
  family exposes flat `*__lookup` paths through django-filter
  expansion. Trigger: the order family gains flat paths. Home:
  the `_visible_entries` docstring.
- E5 Post-expand audit port. The finalizer runs
  `_audit_filterset_subpass_2_5` for filters and `None` for
  orders. Difference: only the filter family scopes related
  branches through target `get_queryset` (registration rule) and
  types GlobalID inputs (strategy rule). Trigger: the order
  family gains either rule. Home: the driver call sites.
- E6 Audit-walk versus BFS-walk merge.
  `_audit_unregistered_related_filter_targets` walks the related
  graph with its own LIFO stack. Difference: audit versus build
  contracts (the audit needs `(filterset, field_name)` pairs for
  messages and must run before any build populates
  `input_object_types`; the BFS needs FIFO build order plus the
  collision registry). Trigger: the audit reuses the factory's
  reachable set while keeping message pairs and failure
  atomicity. Home: the audit docstring plus this artifact.
- E7 Owner-check merge. Filter `bind_owner` enforces own-PK
  Relay identity plus `get_queryset` safety; order enforces
  related-target agreement only (spec-028 Decision 6: `ORDER BY
  id` uses the column). Difference: owner-dependent axes differ
  by family. Trigger: a unified owner-dependence rule. Home: both
  `bind_owner` docstrings.
- E8 Model-slot merge. Filter `get_model` reads django-filter's
  `_meta.model`; order reads `Meta.model`. Difference: the model
  lives on different slots by upstream construction. Trigger: a
  shared model-slot contract. Home: the call sites plus this
  artifact.
- E9 Layer-6 merge. Dynamic-set caches, getters, reserved
  literals, and the normalize/key/`type(...)` skeleton are the
  sibling family `dynamic-set-class-getter`. Difference:
  class-creation versus input-build contracts. Trigger: owned by
  that item. Home: that family's artifact.
- E10 Ledger/registry/cache merge. The collision registry maps
  name to source set class (cross-root collision detection); the
  factory cache maps name to built input (build idempotency
  across instances); the materialization ledger maps name to
  pinned input (module-global pinning plus finalize idempotency).
  Difference: three lifecycles (build versus pin versus detect)
  under one key shape; merging couples build to materialization
  and breaks the build-only/materialize phase split. Trigger: a
  single lifecycle covering all three. Home: the Decision-9
  prose plus this artifact.
- E11 Thin-wrapper removal (`materialize_input_class`,
  `clear_*_input_namespace`, `filter_input_type`,
  `order_input_type`). Difference: these are spec-named boundary
  names oracles and specs address (Decision 9/11); removing them
  deletes addressability, not duplication (principle 11).
  Trigger: the specs drop the names. Home: the wrapper
  docstrings.
- E12 Alias unification (`FieldSpec`, `build_input_class`,
  `_camel_case`, `_input_type_name_for`, `_iter_*_subclasses`,
  `INPUTS_MODULE_PATH`). Difference: `is`-identical re-exports
  plus per-module identity literals, not definitions. Trigger:
  none (aliases cannot drift). Home: the alias lines.
- E13 `types/base.py::__init_subclass__` and
  `mutations/sets.py` wrapper-peeling `seen` loop. Difference:
  DjangoType registration and Strawberry-wrapper peeling are
  different rules that share only the tokens `__init_subclass__`
  and `seen`. Trigger: none (different populations). Home: this
  artifact.
- E14 Range sub-input naming. The `RangeFilter` embedded-class
  name is a single filter-only site with no twin (order leaves
  have no range shape) and deliberate non-participation in the
  registries (embedded directly, per-filterset-scoped).
  Difference: embedded sub-input versus materialized input
  contracts. Trigger: a second embedded-naming site or registry
  participation. Home: the builder docstring.

No new index row is owed: every member homes in this family and
every exclusion homes in this artifact plus its cited owner
prose or the sibling family. Two prior verdicts were taken as
trigger-checks and both hold fresh: the operator-bag split
(filters/factories R1, orders/factories R-bag) and the
Layer-6/disjointness splits (R2/R3/R6, R-keys/R-cache/R-gate);
the order-alias production-call asymmetry noted in the twin
artifact is addressability-only and pins `is`-identical by
oracle, requiring no row.

## Defects

None. Two probed edges were released without a defect. The
filter side has no `_ensure_field_specs` warm-up twin, but that
helper belongs to the request-time normalize path already judged
file-local to `orders/inputs.py`, and no contract source in this
family's finalize-time build rule demands it on the filter side.
The `cls._meta.model` versus `Meta.model` read asymmetry in the
two `bind_owner` adapters reflects different upstream model
slots, is parameterized through one shared skeleton, and breaks
no wire-reachable contract.

## Pending execution

None. No `proof:` entry (zero-edit verdict; every proof is
static-reviewed over bodies composed by name, corroborated by the
existing executed oracles) and no `gate:` entry. Cell typing:
`default`, `sharded`, and `pg` are all `inapplicable by
construction` — the family decides pure construction-time
derivation (graph walk, naming, class construction, ledger
discipline) and reaches no queryset, database alias, or dialect
decision. The one focused oracle re-run in the shared venv is
corroboration recorded under Challenges, not a pending proof.

## Judgment

CONFIRM: the set-arguments factory BFS is single-owned by
construction. One walk, one collision rule, one idempotent cache
discipline per family namespace, one subclass guard, one emission
scaffold, one naming delegate, one materialize/clear lifecycle,
one bind driver, one lazy helper — ten challenges each moving
exactly one definition, fourteen exclusions each carrying a
contract difference plus trigger, zero defects, zero edits.
Worker-2 is asked to re-derive the exclusions fresh and to judge
the cell typing.

## Implementation (Worker-1)

No production edits (zero-edit verdict) and no new tracked files
besides this artifact (untracked until Worker-0 records it). No
ruff run (no edits). One focused `--no-cov` oracle re-run in the
shared tree plus one AST-only workspace probe, both recorded
above. Concurrent dirt explicitly untouched: the truth-migration
hunks in all four dirty family files plus the remainder of the
478-entry `git status` list.

Type gates (shared venv, read-only): `mypy` clean (119 source
files, no issues), `basedpyright` clean (0 errors, 0 warnings,
0 notes), `check_any.py` clean (130 allowed uses at 90 sites).
Vacuous as consolidation gates — zero-edit verdict, no symbol
added, moved, or removed — reported here per convention for the
verifier to re-run.

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

Recorded BEFORE opening `## Findings` (artifact lines 301-488 unread at trace
time; plan dispatch summary + target bytes + own greps only). Worktree HEAD
`5c3496e0`; WT pins re-verified 6/6 vs dispatch pins (`0575e9b2`/`7576caea`/
`17204c27`/`afad6451`/`6d97fc75`/`0807fea7`); item diff vs `f2cc9bb9` is the
plan edit alone (f30 closeout + f31 dispatch + W1-submitted note, all Worker-0
text); artifact untracked scratch (562 lines, 8 `##` sections, tail link
block intact).

### Own census (sites + roles)

Rule posited: breadth-first construction of every reachable set-family
Strawberry input class for a root set, with name-claim collision rejection,
idempotent caching, finalize-time materialization, and namespace-clear
lifecycle.

Definitions (each count 1, all in `django_strawberry_framework/`):

- D-walk: `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`
  (`:1833`). Only FIFO related-graph BFS in the package: single `pop(0)` at
  `:1845`; no other `while pending` walk over related sets (sweep below).
- D-claim: the claim-collision check inside `_ensure_built` (`:1851-1865`) +
  `duplicate_name_message` (`:1493`, 1 def, 2 internal callers `:1479`/`:1857`).
- D-cache: the idempotent cache discipline — base declares
  `input_object_types` annotation-only (`:1784`); each family owns a fresh
  dict; get-or-build at `:1867`, store at `:1917`, read at `:1831`, cleared
  at `:1717`, iterated by finalizer subpass 4. Two dicts, ONE discipline.
- D-guard: `__init_subclass__` (`:1792`) — allows the 2 direct family
  factories, rejects grand-subclasses. Whole-repo subclass census: exactly
  the 2 production subclasses + test-local `_ProbeFactory` (oracle, see
  below); shadow/temp-tree hits are regenerable copies, not sources.
- D-scaffold: `emit_set_input_field_triples` (`:177`) — 1 def, 2 callers
  (filter + order `_build_input_fields`), each passing family closures.
- D-name: `set_input_type_name` (`:116`) — 1 def; callers are the BFS x3
  (`:1813`, `:1850`, `:1886`) + 2 re-export aliases. Thin delegate to
  `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` (naming rule owned
  elsewhere; this is the factory's delegate, not a second derivation).
- D-lifecycle: `materialize_generated_input_class` (1 def, 1 code caller via
  `make_input_namespace`), `make_set_input_namespace` (1 def, 2 callers),
  `clear_generated_input_namespace` (1 def, 1 caller). Family
  `materialize_input_class` / `clear_*_input_namespace` x2 are thin
  pass-through declarations.
- D-driver: finalizer `_bind_sidecar_sets` (1 def, 2 callers) +
  `_bind_set_owner_common` (1 def, 2 callers) +
  `_format_orphan_sets_error` (1 def, 2 partials) +
  `_format_owner_target_mismatch_error` (1 def, 2 partials).
- D-lazy: `build_lazy_input_annotation` (`:1596`) — 1 def, 2 callers
  (`filter_input_type`, `order_input_type`; both thin declarations, bodies
  read in full).
- D-hook: `_build_input_triples` — 1 base raising `NotImplementedError`
  (`:1920`) + 2 overrides (filter appends `_build_logic_fields`; order
  returns as-is). Principle-5 adapters, not rival definitions.

Consumers: the 2 family factories (each: 2 cache dicts + 7 hook attrs + 1
override), finalizer subpass 4, `clear_generated_input_namespace`, the 2
namespace wrappers per family.

Oracles (independent, pin wording without reading the owner): independent
oracle census includes `tests/filters/test_factories.py` (incl. the
subclass-guard message assertion `:788`), `tests/orders/test_inputs.py`,
`tests/utils/test_inputs.py` (incl. test-local direct subclass
`_ProbeFactory` at `:1023` — consumes the walk with a stub hook; its
`_collision_registry = {}` class attr shadows the base property by MRO
order, which is why no `_collision_registry_attr` is needed; verified by
execution, 1 passed). Projections: module/class docstrings incl. the
intentional-separation clauses (each verified against its body, see E-clauses).

### Own challenges (count per posited change)

- C1 FIFO->LIFO / visited-gate variant: forces D-walk only. The finalizer
  `_audit_unregistered_related_filter_targets` LIFO walk does NOT move
  (audit vs build, unregistered-target vs name-claim trigger). Count 1.
- C2 collision wording/verb change: forces `duplicate_name_message` only;
  the 2 call sites pass threaded nouns (consumers). Count 1.
- C3 per-namespace cache-variant split: the discipline is one body; a
  variant ADDS an adapter, moves nothing twice. Count 1.
- C4 second walk site: swept `while pending|stack`, `seen.add`, `popleft`,
  `deque` package-wide. `iter_set_subclasses` (subclass-tree DFS for clear),
  the finalizer audit walk (LIFO, filter-only), `iter_active_fields`
  (request-time input-data walk), optimizer/keyset/mutation `seen` walks
  (unrelated domains) — none encodes "build every reachable input class".
  Count 1.
- C5 second bind driver: `_bind_sidecar_sets` 1 def / 2 specs;
  `mutations/sets.py:27` documents deliberate divergence (iterates the
  declaration registry, not definitions — different population). Count 1.
- C6 second collision rule: emission guard (seen-dicts over specs),
  construction backstop (`build_strawberry_input_class` dup check),
  `iter_input_field_collisions` (write flavors), mutation surface audit
  (resolved Strawberry fields) — the scaffold docstring (`:226-235`) states
  the 4-point split with reason (independent-backstop value; different
  artifacts, different lifecycle points). Count 1 for the BFS claim rule.
- C7 second materialize/clear lifecycle: write flavors ride light
  `make_input_namespace` (no BFS graph, no `_lifecycle`);
  `mutations/inputs.py:26` states the divergence. Count 1 for heavy set
  lifecycle.
- C8 second lazy helper / naming path: 1 def each; re-exports are aliases.
  Count 1.
- C9 Layer-6 getter folded into the factory: `make_dynamic_set_getter` is
  the separately indexed open family `dynamic-set-class-getter` (dynamic
  synthesis + meta-hash cache vs declared-set BFS build). Excluded here.
- C10 orders `_ensure_field_specs` warm-up given a filter twin: request-time
  normalize path, not construction; filter entry differs. Released-edge
  candidate — judged after reading W1's edge record.

### Owner I would choose

`utils/inputs.py::GeneratedInputArgumentsFactory` for the BFS core (walk +
claim + cache + guard + scaffold-call + hook), with lifecycle, scaffold,
naming delegate, and lazy helper co-sited in `utils/inputs.py` (neutral
mechanics both families import cycle-free), and the bind driver owned by
`types/finalizer.py` (phase-2.5 authority; local-imports families so load
order cannot cycle — dependency direction wins per principle 7). Matches the
plan's owner candidate. No consolidation owed: every sub-rule counts 1.

### Own exclusion list (14, each with contract difference + trigger)

- E1 finalizer audit walk: audit-vs-build (above C1). Trigger: either side
  takes the other's job.
- E2 `iter_set_subclasses`: subclass-tree DFS for clear vs related-graph BFS
  for build. Trigger: clear walks related targets or build walks subclasses.
- E3 Layer-6 getter + meta-hash machinery: dynamic synthesis vs declared-set
  build; own open index row. Trigger: either side takes the other's job.
- E4 write-flavor light namespace: no BFS graph / no lifecycle state.
  Trigger: a write flavor gains related-set traversal.
- E5 construction backstop dup check: independent guard AT the build site;
  non-shared body is the value. Trigger: the package abandons
  defense-in-depth at construction.
- E6 `iter_input_field_collisions`: write-input spec audit, serializer-only
  third arm. Trigger: set emission routes through it.
- E7 mutation surface audit: reads post-decoration Strawberry fields.
  Trigger: set emission moves post-decoration.
- E8 mutation bind: declaration-registry iteration vs type sidecars.
  Trigger: mutations become type sidecars.
- E9 the two `bind_owner` adapters: different model slots (`cls._meta.model`
  validated vs raw `Meta.model` admitting lazy strings) + different
  second-owner axes (Relay identity + get_queryset vs neither); skeleton
  handles non-class. Adapters per principle 5. Trigger: OrderSet gains a
  validating metaclass AND an owner-dependent axis.
- E10 filter operator bag (`_build_logic_fields`, no order twin): absence is
  contract (spec-028 Decision 8), not a gap — axis 6 discharged by spec.
- E11 orders `_ensure_field_specs` (no filter twin): request-time warm-up
  gate, not construction; each family's normalize entry owns its shape.
  Trigger: filter normalize gains a spec-warm-up miss (see C10).
- E12 threaded wording nouns at the 2 `duplicate_name_message` call sites:
  consumers, not definitions. No trigger (counting rule).
- E13 `convert_filter_to_input_annotation` vs order converter: operator-bag
  typing vs fixed `Ordering` (already rejected: `orders-converter-*` row).
- E14 filter vs order `normalize_input_value`: different runtime shapes
  (already rejected: `orders-normalize-vs-filter-normalize` row).

### Own matrix pass

1. Cross-flavor: mutations/forms/serializer checked — light namespace, no
   BFS, divergences documented at both owners. Discharged by search.
2. Sync/async: construction path is all-sync class building; no await
   boundary, no twin. Inapplicable with reason.
3. Derived knowledge: names via D-name (single delegate), field sets from
   each family's single expansion, defaults from `optional_field_kwargs`;
   no re-derivation found. The `_ProbeFactory` stub `type_name_for` is
   oracle-local. Discharged by search.
4. Inverse pairs: build (BFS) vs normalize (request-time decode) — separate
   contracts/media; materialize-pin vs ledger-reset under the stated
   parked-globals lifecycle. Discharged by search.
5. Other media: separation clauses verified against bodies (4-point split,
   mutations divergence, parked globals); oracles pin wording independently
   (guard message `:788`, `iContains`-style spellings). Discharged by search.
6. Omission: operator bag (contract absence, E10), `_ensure_field_specs`
   (E11/C10, to judge), Layer-6 no-clear-hooks (pre-existing file-local
   lifecycle rows, documented keys-embed-model rationale — not this family).
   Discharged by search + contract sources.

### Pre-read positions (to reconcile after reading Findings)

- P1 F1 census: walk + claim + cache + guard + scaffold + delegate +
  lifecycle + driver + helper + hook = my 10 definition units vs the
  dispatch summary's 9 (hook unnamed there). Reconcile naming, not substance.
- P2 Cells: family path reaches no queryset execution, alias selection, or
  dialect branch (expansion is `_meta` inspection + annotation derivation;
  bind reads registry/bools, never executes `get_queryset`). Whether even
  the DEFAULT cell is `inapplicable by construction` (novel — f28/f29 ran
  default green) vs default-executed: STRICT judgment owed after reading
  W1's reason + a query-count probe of the BFS path.
- P3 Gate: owner already single → gate-only shape. In-tree mechanical
  enforcement exists for inheritance-bypass (`__init_subclass__` +
  annotation-only caches, oracle-pinned); the "exactly one walk" half needs
  W1's population justification or an explicit gate-none rationale. Judge
  after reading.
- P4 The 2 released edges (filter-side `_ensure_field_specs` twin;
  `get_model` asymmetry): my E9/E11 agree in shape; verify W1's non-defect
  reasoning holds on the bodies, else a defect is owed (recorded by me, not
  demanded of W1).

### Reconciliation (Worker-2; after reading Findings, lines 301-488)

- F1 census + owner: AGREE on fresh evidence. W1's 9 units vs my 10 is
  naming only: W1 lists the `_build_input_triples` hook signature among
  definitions and covers the hook merge in E1; my D-hook names it
  separately. Same owner (`GeneratedInputArgumentsFactory`, lifecycle /
  scaffold / delegate / helper co-sited in `utils/inputs.py`, bind driver
  in `types/finalizer.py`) with the same principle-7 reasoning. All ten
  challenges on both traces move exactly 1 def; my extra stress probes
  (cache-discipline split, Layer-6 fold, warm-up twin) confirm count-1 /
  excluded. No change forces count > 1 with a landable owner: no
  revision candidate, no `blocked` positions.
- `_build_logic_fields` framing: W1 counts it a family definition, I
  framed it via E10/D-hook. Same substance (single site, no twin, no
  consolidation); no spend.
- 14 exclusions: W1's E1-E14 each carry contract difference + trigger +
  home; all sound on the bodies. My sweep maps onto them with remainder:
  `iter_set_subclasses` (E2), write-flavor light namespace (E4),
  construction backstop (E5), `iter_input_field_collisions` (E6), mutation
  surface audit (E7), mutation bind (E8), `_ensure_field_specs` absence
  (E11), normalize twins (E14) — recorded with differences + triggers in
  my trace above; none is a second definition. W1's "6
  mechanism-adjacent walks" leaves 3 unnamed (only E6 + the E13 pair are
  named): record-accuracy observation, W2-supplied here, not a verdict
  spend (f30 precedent: remainder mapped, still verified). E12/E13
  "Trigger: none" accepted (aliases / token twins cannot reunite by
  contract change; matches my E12).
- Released edges: both genuinely non-defective on fresh body reads. (1)
  Filter `_normalize_input` degrades to `_form_key_for_python_attr` on
  spec-None (`filters/sets.py:2516`) — no silent drop; no contract source
  demands a warm-up twin, so axis 6 releases it without even a maintainer route.
  (2) `get_model` asymmetry reflects genuinely different upstream slots
  (validated `_meta.model` vs raw `Meta.model` admitting lazy strings);
  the skeleton turns non-class into the family mismatch error; adapters
  per principle 5. No defect owed by me either.
- Index rows: ENDORSE "none owed" (F1/E-rows/sibling/prior rows home all).
- Pending-"None": CORRECT → plain. No `proof:` owed (proofs are static
  over unchanged bodies; corroborating executions cannot prove
  single-ownership — a twin copy passes them too). No `gate:` owed
  (gate-none accepted: production `__init_subclass__` guard +
  annotation-only caches, negative controls oracle-pinned per family at
  `tests/filters/test_factories.py:788` +
  `tests/orders/test_factories.py:248`, both re-grepped; f30 precedent).
- Cells all-three-`inapplicable by construction`: ACCEPTED under strict
  judgment. Fresh evidence: (1) /tmp scratch probe drives the BFS +
  materialize over real 4-class-per-family graphs (root + 3 related
  targets, operator bag included — reach printed, non-vacuous) inside
  `CaptureQueriesContext`: ZERO queries, with a sensitivity control
  proving the instrument observes (2 passed, shared venv); (2)
  line-by-line path analysis: clear is dict-clears + `delattr`, bind
  reads registry / `_meta` / stamped bools and never executes
  `get_queryset`, helper is `is_subclass` + `set.add` — no queryset
  construction, no alias read, no dialect branch; (3) oracles pin
  cell-invariant construction outcomes. f28/f29 ran default green
  because those items HAD behavior proofs; f31's proofs are all
  static, so crediting corroboration as "executed" would be false
  precision. Novel typing RIGHT.
- Matrix: all six axes discharged against the real surface. Axis-2
  zero-async-token claim re-grepped (0/0); axis-3 sole-`RangeInputType`
  construction re-grepped (only `:878` + its docstring; no `%`/`.format`/
  concat twins); axis-4 shared-traversal claim verified at both call
  sites (`filters/sets.py:2507`, orders mirror); axis-6 omissions each
  carry a contract source or a correct release.
- Freshness: 18/18 fingerprints corroborated (6 files x WT/HEAD/baseline;
  baseline == WT on all six); rule-region census identical at HEAD and WT
  on every spot-checked symbol; dirt attribution spot-checked (truth
  migration + typing/docstring reflow, matches W1's content claim).
- Zero-edit: re-verified — 6/6 WT pins match dispatch pins, HEAD
  `5c3496e0` unmoved, item diff vs `f2cc9bb9` is the plan edit alone
  (Worker-0 text), status count 479 = 478 + artifact, Implementation
  section read and claims no landing.
- Gates: ruff vacuous (zero tracked `.py` touched — recorded, no run
  owed); `mypy` clean (119 files), `basedpyright` 0/0/0, `check_any.py`
  130/90 — all three re-run whole-package in the shared venv, exact
  match to W1's report. W1's oracle re-run re-executed green (1
  passed); my own oracle probe green (1 passed).
- Workspace: copy OBTAINABLE at `dry/setargs-f31/verify` (slot-3, fresh,
  run `dry-20261001T121318-5ce87c`); AST-only probe ran exit 0; no
  mutating proof needed. Execution probes ran in the shared venv
  (per KNOWN slot constraints); probe files live under `/tmp`, never
  the repo root.
- Diff rules: tracked diff empty of item edits; artifact is per-cycle
  scratch (raw `path:NN` allowed, no style spend); no production
  provenance/pragma/ASCII surface (vacuous).

No new defect found; no `(Worker-2)` entry is owed under `## Defects`.
W1 sections byte-intact (only this section appended after the link block
— it adds no reference links, so the scaffold is unaffected — plus the
`Status:` flip below).

Worker-2 verdict: `verified` (plain).
