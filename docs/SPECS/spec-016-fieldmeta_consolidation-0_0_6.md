# Spec: FieldMeta single-source-of-truth consolidation and mirror retirement

Target release: `0.0.6` (per [KANBAN.md][kanban] card `DONE-016-0.0.6`).
Status: shipped.
Owner: package maintainer.

Why relation shape has one store and why the free relation classifiers are deliberately called on raw Django fields lives in its companion [rationale file][spec-016-rationale].

## Card snapshot

- Card: `DONE-016-0.0.6`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

### Single source of truth

`FieldMeta` on `DjangoTypeDefinition.field_map` is the canonical store of relation shape — cardinality, nullability, `attname`, `related_model`, FK target columns, a link's carrier columns and the columns they target (`link_carrier_attnames` / `link_target_attnames`, for a forward single relation and a reverse FK / reverse OneToOne), and the non-pk source columns a reverse, M2M or generic link targets (`source_target_attnames`), all three read through `django_strawberry_framework/utils/relations.py::relation_link` — for every registered [`DjangoType`][glossary-djangotype]. It is built once per type at class-creation time. No consumer of [relation shape][glossary-relation-handling] re-derives that shape from raw `getattr` reads on a Django field descriptor when a canonical `FieldMeta` is reachable.

Six reader sites hold that rule, two in `types/` and four in `optimizer/`. `django_strawberry_framework/types/base.py::_build_annotations` reads none: the `PendingRelation` record it builds for each auto-synthesized relation carries only the raw `field_name` that keys `field_map`, and no cardinality or nullability.

- `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"field_meta = definition.field_map[pending.field_name]" — performs the canonical read and passes it explicitly into `django_strawberry_framework/types/converters.py::resolved_relation_annotation` as its first argument. `resolved_relation_annotation` itself reads only `field_meta.is_many_side` / `field_meta.nullable` and derives nothing.
- `django_strawberry_framework/types/resolvers.py::_make_relation_resolver` — reads `registry.get_definition(parent_type).field_map[field.name]` for the registered `parent_type` it is built for, and consumes that `FieldMeta`'s `relation_kind`, `is_many_side`, `related_model`, and `attname`.
- `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` — resolves the registered `DjangoType` and returns `definition.field_map`. When no type is registered, the same helper stamps `FieldMeta.from_django_field` over `model._meta.get_fields()`, keyed by raw `f.name`. Both paths yield `FieldMeta`; the brittle Django-private `_meta` access is centralized here.
- `django_strawberry_framework/optimizer/walker.py::_walk_selections` reads `definition.optimizer_hints`, and the nested-connection planner reads the same slot off the same definition (`django_strawberry_framework/optimizer/nested_planner.py` #"hints_map = definition.optimizer_hints if definition is not None else {}"), so the planner reads the canonical store rather than opening a second source.
- `django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` — gates schema reachability on `registry.get_definition(origin) is not None`.
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema` — reads `definition.field_map` and `definition.optimizer_hints` for every schema-reachable type.

### Bounded exceptions to the single-source rule

None exists: every reader above takes its `FieldMeta` from the owning definition, with no fallback that re-derives it.

Unregistered-model planning is not an exception: `optimizer/walker.py::_resolve_field_map` stamps the fallback map through `FieldMeta.from_django_field` over every `get_fields()` entry, a multi-column forward `ForeignObject` included (`tests/optimizer/test_walker.py::test_unregistered_field_map_stamps_a_multi_column_forward_foreign_object`), so walker callers read the same shape as the registered path. The nested-connection window partition re-fetches the live descriptor through `model._meta.get_field` in `optimizer/nested_planner.py::plan_connection_relation` because the forward-M2M reverse query name lives only on the descriptor's `remote_field`, which `FieldMeta` does not carry.

### No class-attribute mirror

`DjangoType.__init_subclass__` writes no class-attribute mirror of the field map or the optimizer hints; the optimizer resolves metadata through `registry.get_definition(...)` at every site listed above. A class-attribute mirror survives `registry.clear()`, so its absence is what makes the registry the only lifetime that field metadata has.

### Out of scope

Calling the shared classifiers `relation_kind(field)` / `is_many_side_relation_kind(...)` from `django_strawberry_framework/utils/relations.py` on a **raw Django field descriptor** is outside this card's scope and is correct. Those helpers are the one implementation of the classification, and `FieldMeta.relation_kind` / `FieldMeta.is_many_side` delegate to them rather than duplicating the ladder. This card's contract is narrower and specific: where relation shape is needed for a field belonging to a registered `DjangoType`, read the `FieldMeta` the definition already holds instead of re-deriving it. A site that classifies a raw descriptor it obtained outside a definition — a filter-set builder, a join-taxonomy walk, a connection-shape check — is not a duplicated reader and does not fall under this rule.

## Why it matters

- Re-deriving relation shape at each reader multiplies the drift surface of every future relation flag or descriptor-attribute change by the reader count. One canonical `FieldMeta` read makes that a one-site change.
- Two parallel metadata stores with no enforced consistency is a correctness hazard rather than a tidiness one: a class-attribute mirror survives `registry.clear()`, so a cleared registry and a live mirror could disagree about the same type's fields with nothing to detect it.
- The consolidation is a prerequisite for any later feature that reads per-field metadata — cost analysis, resource policy weighting, new relation kinds — each of which would otherwise widen the duplication before narrowing it.

## Compatibility

Internal metadata architecture. No `Meta` key and no public export is involved, and there is no consumer-visible behavior: the field map and optimizer hints are read only through `registry.get_definition(...)`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling

<!-- docs/SPECS/ -->
[spec-016-rationale]: appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
