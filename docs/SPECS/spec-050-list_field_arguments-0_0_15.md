# Spec: `DjangoListField` argument surface (`offset`, `limit`, and `orderBy`)

Target card: [`DONE-050-0.0.15`][kanban]
Status: **Shipped** in the `0.0.15` line; it ships in the `0.0.15` release. This `Status:`
line is the lifecycle source of truth; the Slice checklist is the contract ledger and its
boxes stay unticked by repository convention.

Deliberation and rejected alternatives live in its companion
[`spec-050-list_field_arguments-0_0_15-rationale.md`][rationale].

Predecessors: [`spec-020`][spec-020] (the non-Relay list field),
[`spec-028`][spec-028] (the ordering subsystem the list field's `orderBy` reuses),
[`spec-030`][spec-030] (the connection field's Meta-derived sidecar signature),
and [`spec-047`][spec-047] (the execution resource policy and raw-list bound).

Release: [`django_strawberry_framework.__version__`][package-init] reads `"0.0.15"`, the open
`0.0.15` development line, and this card's glossary rows read `shipped (0.0.15)`.
[`TODO-ALPHA-053-0.0.15`][kanban] cuts the `0.0.15` release: the
[`CHANGELOG.md`][changelog] release notes and the release-status flips.

## Key glossary references

- [`DjangoListField`][glossary-djangolistfield] - the public field factory that carries the
  arguments.
- [`DjangoType`][glossary-djangotype] - the Meta-first model type that owns the ordering
  sidecar.
- [`Meta.model`][glossary-metamodel] and [`Meta.fields`][glossary-metafields] - the
  declaration keys used by the consumer example; the list field adds no Meta key.
- [`OrderSet`][glossary-orderset], [`Meta.orderset_class`][glossary-metaorderset_class],
  [`order_input_type`][glossary-order_input_type], and [`Ordering`][glossary-ordering] - the
  ordering pipeline the list field reuses without a second input system.
- [`get_queryset` visibility hook][glossary-get_queryset] - the row-visibility boundary that
  runs before ordering and slicing.
- [Execution resource policy][glossary-execution-resource-policy] and
  [`ResourcePolicy`][glossary-resourcepolicy] - the request ceiling from which both accepted
  limit and maximum skip are derived.
- [`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension] - the
  pre-execution document-cost guard, which charges a raw list at its policy ceiling rather
  than trusting an arbitrary argument named `limit`.
- [`DjangoConnectionField`][glossary-djangoconnectionfield], its
  [`DjangoConnection`][glossary-djangoconnection] return shape, and
  [connection-aware optimizer planning][glossary-connection-aware] - permanent boundaries:
  connections and nested windows carry no offset pagination.
- [Live-first coverage mandate][glossary-live-first] - every wire-reachable branch is covered
  in the fakeshop HTTP suite.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] - the root-list planning
  path, which receives the final sliced queryset unchanged.
- [`strawberry_config`][glossary-strawberry_config] - the supported schema naming boundary;
  error payloads use the argument spelling the executable schema published.
- [Joint version cut][glossary-joint-version-cut] - the release rule under which
  `TODO-ALPHA-053-0.0.15` cuts the `0.0.15` release this card ships in.
- The [visibility boundary][glossary-visibility-boundary] and its
  [sealed execution queryset][glossary-sealed-execution-queryset] - the shared seam whose
  `require_unevaluated` and `carry_result_cache` options the list field's seals use.
- [`ListArgumentError`][glossary-listargumenterror], the
  [list offset order precondition][glossary-list-offset-order-precondition], and the
  [async queryset completion adapter][glossary-async-queryset-completion-adapter] - this
  card's three glossary concepts.

## Slice checklist

- [ ] **Slice 1 - argument normalization and typed runtime rejection**
  - [ ] [`django_strawberry_framework/list_field.py`][list-field] synthesizes `offset: Int` and
        `limit: Int` on every `DjangoListField`; both are nullable and optional.
  - [ ] A package-owned [`ListArgumentError`][glossary-listargumenterror] rejects negative
        and over-ceiling runtime values with stable `extensions`; GraphQL's standard `Int`
        coercion owns wire type rejection before the resolver.
  - [ ] That class is exported from
        [`django_strawberry_framework/__init__.py`][package-init], and
        [`tests/base/test_init.py`][test-base-init] pins it in the `__all__` tuple and the
        export-identity row.
  - [ ] Argument wire names are resolved only while building an error, never on a successful
        request.
  - [ ] The offset ceiling is `ResourcePolicy.max_list_rows`; no settings key governs it.
  - [ ] Error payloads read argument names from the executable schema's published argument
        map rather than assuming the default camel-case converter.
- [ ] **Slice 2 - Meta-derived `orderBy` and list pipeline**
  - [ ] A target carrying `Meta.orderset_class` gains nullable, optional
        `orderBy: [<OrderSet>InputType!]`; a target without that sidecar publishes no
        `orderBy`.
  - [ ] The offset/order guard reads ONE classification of the sealed queryset, mirroring
        `SQLCompiler._order_by_pairs`'s precedence, so a random model default disqualifies an
        active-input request and a random term the compiler does not select disqualifies
        nothing. That classification certifies positively, against an explicit list of approved
        forms matched by exact type - named compositions, pure Django functions, the
        `Min` / `Max` aggregates the `OrderSet` emits and the `Count` a consumer ordering may
        annotate, readable leaves (a column, the `*` of a row count, a literal, and the
        framework's own visibility test), the `F` and `Q` reference forms, and the approved
        transforms and lookups a predicate applies - and refuses every other node, subclasses
        of approved ones included. Which arm a term takes is decided by `resolve_expression`,
        the way the compiler decides it, so a name that is an expression is classified as
        one. A string name ending on a relation expands where the compiler expands it,
        decided on the field `Query.names_to_path` ends on, so a many-to-many or generic
        relation name always expands.
  - [ ] Sync and async paths run visibility, then `OrderSet`, then the offset/order guard,
        then the one raw-list slice.
  - [ ] The result of a public `OrderSet.apply_*` override is validated as an unevaluated,
        unsliced, non-projection model queryset, a combinator served as its primary-key set,
        before the final window; the seal's `require_unevaluated` option carries the
        `evaluated` defect, and the post-sidecar message site arms every code it can reach.
  - [ ] Nonzero offset requires a materially active `orderBy` or still-effective model
        `Meta.ordering` on the post-visibility queryset; no pk tiebreaker and no `DISTINCT`
        are injected.
- [ ] **Slice 3 - SQL and unit contracts**
  - [ ] [`tests/test_list_field.py`][test-list-field] pins signature shape, direct-call
        runtime errors, helper mechanics, and model-ordering state; the cap arithmetic is
        pinned by
        `tests/test_resource_policy.py::test_effective_bound_takes_the_tighter_of_the_two_unless_trusted`,
        and no-argument SQL parity live in `examples/fakeshop/test_query/test_list_field_api.py`;
        wire-reachable sync and async wrapper behavior stays in the live tier.
  - [ ] The live async suite
        ([`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async])
        sets no `DJANGO_ALLOW_ASYNC_UNSAFE`, so it cannot mask a regression in safe async
        queryset completion. In the package tier one test sets it:
        `tests/test_relay_connection.py::test_async_fast_path_last_zero_serves_the_first_zero_page`.
  - [ ] Order input construction uses the `OrderSet` factory and orphan ledger rather than a
        list-field-specific input class.
  - [ ] The shared target validator accepts only the definition the type registry holds for
        the target, compared by identity; list, connection, and Relay node fields enter
        through it, and the generated-connection cache verifies the definition that produced
        each entry on every warm hit.
  - [ ] The optimizer carries the child definition the relation was resolved through into the
        nested planner, and no optimizer decision about a relation target reads
        `__django_strawberry_definition__` off the target class.
  - [ ] The order-normalization ledger closes terminally: a descendant holding the copied
        context can neither publish into nor claim from a closed ledger.
  - [ ] The raw-list seam windows a source that arrives evaluated from the rows it already
        holds, exact queryset and rebuilt subclass alike, with the query count pinned at zero
        in the package tier and the fakeshop `Loan` model's override-free
        `LoanQuerySet.as_manager()` declaration pinned live at an absolute two-query prefetch
        cost, its pending
        reverse-relation predicate baked onto the rebuild by the same unbound `Query.add_q` an
        exact queryset's is, and a deferred-filter state Django never writes refused with the
        typed error at both tiers. The dynamic manager stays migration-safe through Django's
        `use_in_migrations=False` default.
  - [ ] `tests/test_connection.py::test_the_optimizer_plans_a_relation_without_reading_the_target_class`
        swaps the target's definition attribute for a decoy over a different model after a
        real `DjangoSchema` with the optimizer is built, parametrized over hook flavour and
        relation vocabulary (list and connection), and asserts the planned rows, that a
        custom hook RAN, and the plan cache's hits/misses/size on the cold and the warm
        request; the live siblings in `examples/fakeshop/test_query/test_products_visibility_api.py`
        and `examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_window_hides_embargoed_rows_and_counts_them_out`
        pin the rows a mis-answered plan would serve.
- [ ] **Slice 4 - live acceptance**
  - [ ] `examples/fakeshop/test_query/test_list_field_api.py` drives the sync surface over
        `/graphql/`: ordered offset pages, `orderBy` lists, visibility-before-order,
        limit/cap/error cases, converter naming, and the exceptional holder-mounted source
        shapes. It is the sync counterpart of the async suite.
  - [ ] [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy]
        pins request-policy narrowing over the same field surface.
  - [ ] A test-local [`AsyncDjangoGraphQLView`][glossary-djangographqlview] mount proves safe
        async queryset completion, configured argument names, async iterable cleanup, and
        async pipeline parity over HTTP without `DJANGO_ALLOW_ASYNC_UNSAFE`. Cleanup is
        proven for a deadline rejection too, on the default window and on `limit: 0`, with
        zero advances and exactly one close.
  - [ ] Both wrong verdicts of a collection-scanning offset guard are pinned live in both
        colorings - a random model default under a no-op public override, and a dormant random
        term superseded by a deterministic `extra` ordering - each beside its control.
  - [ ] Both live suites are listed in the tracked-path constants
        ([`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants]).
  - [ ] [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] indexes both
        suites and the async suite's `AsyncTestClient` transport.
- [ ] **Slice 5 - documentation fold-in**
  - [ ] The list-field docstring, [`docs/GLOSSARY.md`][glossary],
        [`docs/README.md`][docs-readme], and [`README.md`][readme] describe the arguments.
  - [ ] `ResourcePolicy` and bounding-helper docstrings distinguish returned/skip ceilings
        from total database rows scanned.
  - [ ] [`docs/README.md`][docs-readme] states the trust contract of Decision 19 in the
        production security profile, and the extension contract of Decision 20 beside the
        optimizer recipe: enforcement through `resource_policy=` / `error_policy=`, class or
        factory for ordinary extensions, the instance spelling carrying upstream's deprecation
        unchanged, and per-operation isolation of the package's own extensions - the
        singleton-in-a-factory recipe included - as the guarantee this package adds.
  - [ ] Every quick-start and schema-setup example that passes `extensions=[lambda: _optimizer]`
        builds a `DjangoSchema`, the only schema the isolation guarantee holds for; none pairs
        that factory with a plain `strawberry.Schema`.
  - [ ] The board shows card 050 Done, and [`TODAY.md`][today] lists the `offset` / `limit` /
        `orderBy` arguments as available and live-tested.

## Problem statement

`DjangoListField` is the package's bounded non-Relay collection field. A client that wants an
ordered subset of its rows needs ordering and a window on the field itself. Without
package-owned arguments a schema author would write a Strawberry resolver accepting `orderBy`,
which duplicates the sidecar machinery; slice a queryset by hand, which moves resource
validation into consumer code; or turn the field into a Relay connection, which changes the
response shape rather than adding a list argument. The field's `offset`, `limit` and `orderBy`
arguments serve that need on the existing `list[T]` response.

Both upstream families make offset pagination available, in different shapes.
`graphene-django` publishes `offset: Int` on every connection and converts it into an
`after` cursor in
[`graphene_django/fields.py::DjangoConnectionField.resolve_connection`][upstream-graphene-fields].
The package refuses that connection surface because it keeps the cursor response shape
while retaining the instability and scan cost of skip pagination.
`strawberry-graphql-django` instead ships `OffsetPaginationInput`, `OffsetPaginated[T]`, and
windowed relation pagination in
[`strawberry_django/pagination.py`][upstream-strawberry-pagination].
This package keeps the `list[T]` response and adds bounded list arguments; nested pagination
is a connection concern.

Pagination and ordering share one wrapper seam: one signature builder and one pipeline carry
both, using the signature-synthesis approach `DjangoConnectionField` uses for Meta-derived
sidecars.

## Goals

1. Give every `DjangoListField` nullable optional `offset` and `limit` GraphQL arguments
   without changing its `list[T]` return shape.
2. Publish a Meta-derived `orderBy` argument wherever the target `DjangoType` declares
   `Meta.orderset_class`, using the exact input type and permission pipeline connections
   use.
3. Bound requested rows by the effective raw-list ceiling and skipped rows by the request
   policy, rejecting invalid requests rather than silently clamping them.
4. Require [an active order for nonzero offset][glossary-list-offset-order-precondition],
   because a skip counted over an undefined order names no particular page. The surface is
   **ordered offset**, not stable or repeatable pagination; Decision 7 records why, and the
   field docstring, the glossary, and [`docs/README.md`][docs-readme] each state the
   distinction.
5. With `offset`, `limit`, and `orderBy` all omitted, the sync path's behavior and SQL are
   byte-identical to the coordinate-free bound: the same low mark, high mark, ordering, and
   parameters, so the request policy's `LIMIT` is still present. The async path completes the
   same query through the async queryset completion adapter, with the same data.
6. Keep visibility before ordering and every slice after both for queryset/manager sources;
   keep the visibility bypass for plain iterable returns while bounding them.
7. Complete bounded querysets safely through sync and async GraphQL views, so that
   framework-owned final queryset completion performs no synchronous ORM evaluation inside
   the event loop. The field neither can nor does promise the same of a plain `def` consumer
   resolver that runs synchronous ORM calls in its own body; a synchronous `get_queryset`
   hook runs in a `sync_to_async` worker
   (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_async`), so its
   body may.
8. Cover the reachable production lines through live GraphQL HTTP tests and keep package
   tests only for construction and execution shapes unavailable from that mount.

## North-star and cookbook fit

The list field's arguments serve success criteria 2, 5, and 7 in the project
[`GOAL.md`][goal]: schema authors expose a model collection through `DjangoListField` without
a hand-written list resolver, the optimizer receives the consumer-shaped lazy queryset, and a
Graphene migration keeps its one-line field declaration and Meta-owned order sidecar. They do
not by themselves establish the separate [cookbook-parity][glossary-cookbook-parity] target.

The working cookbook's
[`~/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py::Query`][cookbook-schema]
declares all four root collections as `AdvancedDjangoFilterConnectionField`, while each node
owns `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`,
through its nested `Meta` declaration and defines `get_queryset` as a class hook beside that
declaration. The parity path for those fields is therefore this package's
`DjangoConnectionField` and cursor response, not a flat list. `DjangoListField` is the other
collection shape the north star requires: it is chosen when the schema author wants a direct
`list[T]` response.

For valid requests, the list field's ordering preserves the reference's security boundary.
The cookbook
[`AdvancedDjangoFilterConnectionField.resolve_queryset`][cookbook-connection-field]
implementation applies the node's `get_queryset` before filtering and ordering, then the
Graphene connection paginates; the list field applies `get_queryset` before `OrderSet` and the
one list window. The cookbook's staff / model-permission / cascade branches remain
consumer-authored hook behavior rather than roles hard-coded into the field factory.
Filtering, search, aggregates, and [fieldset][glossary-fieldset] behavior are
connection/parity work and are not inferred onto a raw list.

Two pagination differences are deliberate. Graphene's connection-level `offset` accepts an
unordered source and the cookbook connection adds its own duplicate-removal behavior after
filtering/order application. The flat-list surface instead requires a visible declared order
for nonzero offset and never injects `DISTINCT`. Those choices make the page coordinate
meaningful and keep the `OrderSet` result-row contract; neither claims wire-compatible
Graphene connection pagination, and neither promises a repeatable page when the declared
order contains ties (Decision 7). Decision 11 records the required migration choice between a
flat list with direct offset arguments and a Relay connection with cursors.

## Non-goals

- **Offset on a Relay connection.** Permanent refusal. Neither
  `DjangoConnectionField` nor synthesized relation connections have an `offset` argument.
  Positional and keyset cursors are the only connection page coordinates.
- **Nested/windowed raw-list pagination.** A nested collection that needs its own page uses
  the relation connection. The package does not port
  [`strawberry_django/pagination.py::apply_window_pagination`][upstream-strawberry-pagination]
  to generated raw-list relations. `DjangoListField` is the documented root Query factory;
  manually assigned nested usage without arguments is "functional but not root-optimized",
  as the glossary states. The arguments in a nested position are unspecified: they are
  neither supported nor tested there, and a consumer relying on them nested is outside the
  contract.
- **An `OffsetPaginated[T]` envelope.** `DjangoListField` returns `list[T]`; there is no
  `pageInfo`, `totalCount`, or `results` object.
- **Filtering or search on `DjangoListField`.** They are separate public-surface decisions.
  The list field infers no filter argument from
  [`Meta.filterset_class`][glossary-metafilterset-class].
- **Dynamic `OrderSet` generation.** A target without `Meta.orderset_class` gets no
  `orderBy`; [`django_strawberry_framework/orders/factories.py`][orders-factories]
  builds input classes for declared `OrderSet`s only and has no auto-generation path.
- **A total-order proof.** Nonzero offset requires an active order, not a mathematical
  uniqueness proof. Lists do not mint cursors, and this surface appends no pk tiebreaker.
- **An offset-policy setting.** `ResourcePolicy.max_list_rows` bounds both returned raw
  rows and maximum skip; [`django_strawberry_framework/conf.py`][conf] has no list-offset key.
- **A client-limit discount in document collection-cost accounting.** The generic raw-list
  walker charges `ResourcePolicy.max_list_rows`; recognizing an argument named `limit` as
  this field's validated runtime contract requires field metadata the walker does not carry,
  and applying that assumption to arbitrary GraphQL lists would undercharge them.
- **Silent clamping.** A client value wider than its effective ceiling is an error. The
  package does not pretend the request was honored while returning a different page.
- **Containing hostile application code.** Python running in the Django process can import,
  monkeypatch and rebind any name in this package, so "the package holds the bound against a
  resolver written to defeat it" is not a promise any check can keep, and the package does
  not make it. The bound holds against the wire and against ordinary application code; a
  construction built to defeat a check is a robustness row where one is cheap and never a
  reason for another admission layer (Decision 19).
- **Release notes.** The `0.0.15` [`CHANGELOG.md`][changelog] notes belong to
  `TODO-ALPHA-053-0.0.15`'s release cut.

## Borrowing posture

### From `graphene-django` - borrow discoverability, refuse connection semantics

The installed source at
[`graphene_django/fields.py::DjangoConnectionField.__init__`][upstream-graphene-fields]
adds `offset: Int` to every connection.
[`graphene_django/fields.py::DjangoConnectionField.resolve_connection`][upstream-graphene-fields]
pops it, combines it with `after`, and converts the result back to a Relay offset cursor;
[`graphene_django/fields.py::DjangoConnectionField.connection_resolver`][upstream-graphene-fields]
additionally rejects `before` plus `offset`. The useful migration property is
discoverability: a migrant expects `offset` to be a normal nullable integer argument. The
package borrows that spelling on the flat-list field only. It refuses cursor conversion,
`before` composition, and the connection-wide publication (*why each was declined: see the
[rationale][rationale-borrowing]*).

### From `strawberry-graphql-django` - borrow offset arithmetic, keep this package's shape

The checkout at
[`strawberry_django/pagination.py::OffsetPaginationInput`][upstream-strawberry-pagination]
uses `offset=0` and optional `limit`;
[`strawberry_django/pagination.py::apply`][upstream-strawberry-pagination] slices a root
queryset as `[offset:offset + limit]`, while
[`strawberry_django/pagination.py::apply_window_pagination`][upstream-strawberry-pagination]
expresses the same bounds with `RowNumber` for nested prefetches. The root arithmetic is the
part borrowed. Its silent max-limit clamp, negative-limit unbounded spelling, generated
result envelope, decorator surface, and nested raw-list window are refused (*why each was
declined: see the [rationale][rationale-borrowing]*). This package has a fail-closed resource
policy, a Meta-class public API, and connections for nested windows.

### From this package - reuse the connection signature proof, not its page rules

[`django_strawberry_framework/connection.py::_synthesized_signature`][connection] proves
that Strawberry publishes Meta-derived lazy sidecar inputs from a wrapper's assigned
`__signature__` and `__annotations__`. The list field uses that mechanism and the
`order_input_type` call. It does not use the connection's filter input, total-order
tiebreaker, cursor codec, Strawberry's `ConnectionExtension`, or page-size rules (*see the
[rationale][rationale-borrowing]*).

## User-facing API

The consumer declaration stays Meta-first. Its
[`Meta.model`][glossary-metamodel] and [`Meta.fields`][glossary-metafields] keys keep their
usual meanings:

```python
class BranchOrder(OrderSet):
    class Meta:
        model = Branch
        fields = ("id", "name", "city")


class BranchType(DjangoType):
    class Meta:
        model = Branch
        fields = ("id", "name", "city")
        orderset_class = BranchOrder


@strawberry.type
class Query:
    branches: list[BranchType] = DjangoListField(BranchType, max_rows=50)
```

With the default [`strawberry_config()`][glossary-strawberry_config] name converter, its SDL
is:

```graphql
type Query {
  branches(offset: Int = null, limit: Int = null, orderBy: [BranchOrderInputType!] = null): [BranchType!]!
}
```

A target without `Meta.orderset_class` publishes only `offset` and `limit`. With
`auto_camel_case=False`, the Python `order_by` parameter renders as `order_by`; a custom
Strawberry name converter may rename all three arguments. The examples in this document use
the default spelling, while runtime error payloads always report the active schema spelling.
`orderBy` is the one conditional argument: GraphQL arguments require a concrete input type,
and the package refuses both untyped JSON ordering and automatic `OrderSet` generation.
Publishing a dummy or always-rejected `orderBy` would make SDL introspection lie.

`offset` is published universally, at a stated cost. On a target with neither
`Meta.orderset_class` nor still-effective model `Meta.ordering`, `offset: 0` is accepted and
every positive value fails `order_required`, permanently. The capability rule is therefore
**publish the coordinate universally and gate it at runtime**: a published `offset` is a
runtime-precondition argument, not a claim that the field can page. Decision 2 records the
two rejected alternatives. The field docstring, the glossary entry, and
[`docs/README.md`][docs-readme] each say so in those terms, and the acceptance suite pins
both shapes - a target with no order source, where positive offset is always rejected, and a
target with stable model `Meta.ordering` and no `OrderSet`, where offset is usable without
`orderBy` ever being published.

The client shape is direct:

```graphql
{
  branches(
    offset: 20
    limit: 10
    orderBy: [
      {
        name: ASC
      }
      {
        id: ASC
      }
    ]
  ) {
    id
    name
  }
}
```

`offset: 0` is valid and WINDOW-identical to omission - the same rows in the same order - but it
is not MODE-identical: any non-null argument, `offset: 0` and `limit: 0` and `orderBy: []`
included, selects the argument-bearing pipeline (Decision 3). `limit` equal to the effective
ceiling is window-identical on the same terms. `limit: 0` is valid and the pagination seam
consumes or fetches no row from a lazy queryset/iterator; work a consumer resolver already
performed to build a materialized list cannot be undone. The operation must also pass the
independent pre-execution document budget before the field runs. `null` and omission are
equivalent for all three arguments. The consumer `resolver=` is invoked as
`resolver(root, info)`; the wrapper owns the arguments and does not forward them into a
consumer function. An async consumer return is awaited exactly once; residual awaitables fail
closed rather than being recursively awaited.

## Caps and error table

Let `P = info`'s `ResourcePolicy.max_list_rows`, `F = max_rows`, and
`T = trusted_max_rows`.

| Quantity | Effective ceiling | Accepted values | Rejection |
|---|---|---|---|
| Returned rows, no client `limit` | `F` when `T` and `F` is set; otherwise `min(P, F)` when `F` is set; otherwise `P` | Derived, always positive | [`ConfigurationError`][glossary-configurationerror] validation owns invalid declarations. |
| Client `limit` | The same effective returned-row ceiling | GraphQL `Int` coercing to `0..ceiling`, or null/omitted | Negative or over ceiling: `ListArgumentError`; other values follow standard GraphQL `Int` coercion. |
| Client `offset` | `P`, regardless of trusted field widening | GraphQL `Int` coercing to `0..P`, or null/omitted | Negative or over `P`: `ListArgumentError`; other values follow standard GraphQL `Int` coercion. |
| Result window | `[offset:offset + limit]`; omitted limit uses the effective returned-row ceiling | At most the effective returned-row ceiling | No clamp after validation. |

`trusted_max_rows` widens returned rows only. It is not a trusted skip declaration: a field
may deliberately return more than the request policy but may not force the database to
discard an arbitrarily large prefix, so the skip a client can request stays bounded by the
request policy.

A client `limit` can reach the widened ceiling, so the opt-in is held to the literal `True`.
`django_strawberry_framework/resource_policy.py::effective_bound` widens on `trusted is True`,
never on a truthy value: it is the one primitive in the package whose answer may exceed the
request's own policy, so a stray `1`, a misspelled `"false"`, or any object with a truthy
`__bool__` narrows like every other non-opt-in caller.
`django_strawberry_framework/resource_policy.py::validate_trusted_flag` additionally rejects a
non-`bool` at the line that CONSTRUCTS the field, so a typo fails where it was written rather
than as a silently raised ceiling on every request the field serves; the primitive keeps its
own check because it must stay safe for an internal caller with no factory in front of it.

Runtime package rejections use one type, exported from the package root so a consumer can catch it:

```python
class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError):
    ...
```

The declaration carries no `# noqa: N818`, and adding one is a lint error. N818 fires only on
an exception name that does not end in `Error`, which is why the
[`django_strawberry_framework/resource_policy.py::ResourceLimitExceeded`][resource-policy]
precedent suppresses it; `ListArgumentError` already ends in `Error`, so the suppression
would be unused and `RUF100`, which [`pyproject.toml`][pyproject] selects through its `RUF`
block, would reject the file. The precedent this class follows is the dual-base shape and the
pickle contract, not the neighbour's noqa comment.

Like that precedent and the package's other dual-base errors, the concrete class defines
`__reduce__` to preserve its constructor arguments and instance state across pickle round
trips; default pickling is not trusted across the `GraphQLError` plus package-error
inheritance shape. The reduce tuple is the class, the complete constructor argument list, and
the instance dictionary. `extensions` is a `GraphQLError` slot rather than an
instance-dictionary entry, so the reconstructing `__init__` rebuilds it from those arguments
rather than carrying it in the state mapping.

`ListArgumentError` is PUBLIC and catchable, exported from
[`django_strawberry_framework/__init__.py`][package-init] beside `ResourceLimitExceeded` and
`SyncMisuseError`. Its stable name, glossary entry, pickle contract, and documented
`extensions` payload only matter to someone who can name the class. A consumer writing a
custom view, an error formatter, or middleware that separates an invalid page request from a
genuine failure uses `except ListArgumentError`, the same contract the two other exported
precedents offer, rather than string-matching `extensions["code"]`. The root module imports
it and lists it in `__all__`, and the pinned `__all__` tuple in
[`tests/base/test_init.py`][test-base-init], together with that file's export-identity row,
carries it. The supported catch surface is `ListArgumentError` itself, its `GraphQLError`
base, or `extensions["code"] == "LIST_ARGUMENT_INVALID"` - all three deliberately. The
package's `DjangoStrawberryFrameworkError` base is a second base rather than a supported root
import; the package root does not export it.

Its `extensions` are stable:

```json
{
  "code": "LIST_ARGUMENT_INVALID",
  "argument": "offset",
  "reason": "over_ceiling",
  "ceiling": 100,
  "value": 101
}
```

For numeric-domain failures, `reason` is `negative` or `over_ceiling`; both carry `value`
and only the latter carries `ceiling`. A direct Python call that bypasses GraphQL coercion
uses `non_integer` and a safe string value rendered by
[`django_strawberry_framework/utils/truth.py::describe`][truth].
`order_required` carries the rejected offset as `value`. The source-shape reason
`queryset_required` carries neither `value` nor `ceiling`, because serializing an order input
is not a stable wire contract. Pre-sliced querysets are the shared sealed visibility
boundary's `ConfigurationError`, not a second list-field classification.
`argument` always uses the active schema's GraphQL wire spelling. The wrapper starts from the
Python parameter name (`offset`, `limit`, or `order_by`), obtains its Strawberry argument
definition from
[`strawberry/types/info.py::Info.get_argument_definition`][strawberry-info], and reads the
name the executable schema PUBLISHED for that definition: the field's `GraphQLField.args` map
is keyed by the converter's answer at build time and each entry carries its
`StrawberryArgument` under
[`strawberry/schema/schema_converter.py::GraphQLCoreConverter.DEFINITION_BACKREF`][strawberry-schema-converter],
so the key whose back-reference IS the definition is the argument's wire name. A direct helper
call without executable-schema metadata falls back to the default spelling (`offset`, `limit`,
or `orderBy`) and tests identify that fallback explicitly. The wire message names the
field, argument, requested value when the payload carries one, and the accepted contract. A
string, boolean, out-of-range integer, non-integral/non-finite float variable, or float
literal never reaches this constructor: GraphQL declares both numeric arguments as `Int`, so
graphql-core rejects the operation during validation/coercion with a `GraphQLError`.
[`graphql/type/scalars.py::coerce_int`][graphql-scalars] in graphql-core 3.2.8 accepts a
finite integral-valued float variable such as `1.0` and delivers the integer `1` to the
resolver; the acceptance suite pins that upstream contract instead of promising origin-type
rejection after coercion. Replacing `Int` with a stricter custom scalar merely to attach the
package code would change the SDL and is rejected.

## Architectural decisions

### Decision 1 — synthesize one resolver signature; do not widen consumer resolvers

`DjangoListField` builds its resolver signature with a private builder,
`django_strawberry_framework/list_field.py::_synthesized_list_signature`, parallel in mechanism
to [`django_strawberry_framework/connection.py::_synthesized_signature`][connection]. It
starts with a `root` positional-or-keyword parameter defaulting to `None` and a keyword-only
`info: Info`, then always adds keyword-only `offset: int | None = None` and
`limit: int | None = None`. It adds `order_by: list[order_input_type(...)] | None = None` only
when the target definition has `orderset_class`. Strawberry's active schema converter maps those
Python names to wire names; the default converter produces `offset`, `limit`, and `orderBy`,
`auto_camel_case=False` produces `order_by`, and a custom converter may rename any argument.
The factory assigns both `__signature__` and `__annotations__`, because Strawberry inspects the
callable once during schema construction. The executable wrapper takes `offset`, `limit` and
`order_by` as its own keyword parameters and calls a consumer resolver with only
`(root, info)`; `__signature__` alone does not change Python's call acceptance.

Unlike the connection builder, the list signature installs no return annotation: the
synthesized signature keeps `inspect.Signature.empty` and the annotation map omits `return`. The
consumer's class-attribute annotation is the single owner of `list[T]` versus
`list[T] | None`; synthesizing `list[target_type]` here would erase the nullable-outer spelling.

The wrapper, not the consumer resolver, consumes all three arguments. Consumers implement
`resolver(root, info)`. *Alternatives rejected: see the [rationale][rationale-d1] (forwarding
arguments to consumer resolvers, inspecting consumer signatures).*

The field reads its target's definition EXACTLY ONCE, at construction, and that one object is
the field's SOLE construction and execution dependency. The shared target validator
(`django_strawberry_framework/list_field.py::_validate_djangotype_target`) performs the one read
and returns it; the factory captures the target's model
(`django_strawberry_framework/list_field.py::_model_from_definition`) and its
`Meta.orderset_class` (`django_strawberry_framework/list_field.py::_orderset_class_from_definition`)
off it, and those two values are what the default resolver seeds
(`django_strawberry_framework/utils/querysets.py::base_queryset`, never the type-keyed
`initial_queryset`), what both visibility seals and the post-sidecar seal validate against
(the captured-model seam `django_strawberry_framework/utils/querysets.py::_captured_model`,
which type-keyed callers omit), what the signature builder publishes, and what every resolver
dispatch runs through. The validator rejects anything that is not the registry's own
definition, and the model read rejects a definition whose model is not a Django model class. A
second read is where a reassigned definition attribute could move the query to another table,
make the source seal and the result seal disagree about which table this resolution is over,
or remove `orderBy` from SDL after validation had proved the target declares one.

The connection field holds the same invariant on the same object, because it shares the
validator. `DjangoConnectionField` threads its captured definition into the generated
connection class (`django_strawberry_framework/connection.py::_generate_connection_class`, and
through it `django_strawberry_framework/connection.py::_connection_type_for` and
`django_strawberry_framework/connection.py::_build_total_count_connection`), into its
synthesized signature, into both pipelines, and into the resolve-time total order
(`django_strawberry_framework/connection.py::_finalize_queryset`, whose model and `cursor_field`
both come from it). The keyset vocabulary is fixed at class generation from that definition
(`django_strawberry_framework/keyset.py::declared_cursor_state_for_definition`), so the class
carries the default (declared) vocabulary its cursors mint and decode under; a page ordered
otherwise (an `orderBy:`, a `get_queryset` / manager order) derives its own vocabulary from it
through `django_strawberry_framework/optimizer/plans.py::effective_cursor_state`. That declared
derivation is definition-keyed and single-sited: the plan-time nested window reaches it through
the child definition the walker resolved the relation through, so there is no type-keyed way
in. A Phase-2.5 synthesized relation connection takes its target's definition from the
REGISTRY (`django_strawberry_framework/registry.py::TypeRegistry.get_definition`) at
finalization and threads it the same way, so it never asks the target class.

The registry is what "the target's definition" MEANS. `origin is target_type` proves only that
whatever answered the class read names this class, and anything can name it, so the shared
validator accepts only `django_strawberry_framework/registry.py::TypeRegistry.registered_own_definition`:
the object the registry holds for the target, which the class attribute IS (identity) and whose
`origin` is the target. `django_strawberry_framework/testing/relay.py::global_id_for` and
`manage.py inspect_django_type` ask the same predicate.
A fabricated same-origin object, a copy of the real definition, and a definition for a type the
registry has never seen are each rejected with `ConfigurationError` at the line that constructed
the field, rather than surfacing later as an engine runtime-type error over a GraphQL type and a
Django model that are unrelated. List, connection, and Relay node fields all enter through that
one validator, so "registered target" cannot drift by factory.

Every identity fact the validator and the predicate read is read truthfully through
[`django_strawberry_framework/utils/truth.py`][truth]. The class and subclass gates read the
target's real type and MRO, so a `__class__` property that raises or lies is the typed
`requires a DjangoType class` rejection. The definition attribute is read by
`django_strawberry_framework/utils/truth.py::static_attr` from the real class namespaces,
without running a metaclass `__getattribute__`, a metaclass property or a descriptor. The
registry stores definitions in a `django_strawberry_framework/utils/truth.py::IdentityMap`, so
the lookup compares the class object itself and never runs a target metaclass's `__hash__` or
`__eq__` (`tests/test_list_field.py::test_djangolistfield_registry_lookup_never_hashes_the_target`).
The attribute is compared to the registry's object before `origin` is read, so `origin` is only
ever read off the registry's own definition.

The generated-connection cache carries the same rule.
`django_strawberry_framework/connection.py::_connection_type_for` keys on target identity, so a
warm hit returns a class whose shape, SDL name and keyset vocabulary were fixed by whichever
definition arrived first; an entry therefore records the definition that generated it and a
caller arriving with a different one is rejected instead of being handed the earlier field's
shape beside its own published arguments.

The optimizer plans the same field from the same one answer.
`django_strawberry_framework/optimizer/walker.py::_resolve_relation_target` returns the child
definition beside its origin rather than collapsing the pair, and the nested planner spends
that object on every decision it makes about the target: whether the visibility hook runs over
the child queryset (`django_strawberry_framework/optimizer/walker.py::_target_has_custom_get_queryset`),
which model that queryset's seals validate against (the same `model=` seam, threaded through
`django_strawberry_framework/optimizer/walker.py::_build_child_queryset`), and which cursor
vocabulary the window derives through. A relation the walker PLANS is served to the generated
resolver as already-scoped rows
(`django_strawberry_framework/types/resolvers.py::_optimizer_scoped_relation`), so a plan that
answered the hook question from a second read and got the wrong answer would build the window
from the unscoped default manager and the resolver would serve it unfiltered.

The signature builder calls
[`django_strawberry_framework/orders/__init__.py::order_input_type`][orders-init] with
that captured class rather than constructing an annotation itself. That call is
load-bearing: it registers the helper reference in the orphan ledger and ensures
[finalization][glossary-finalize_django_types] materializes the same input class a
hand-written resolver or connection uses.
The import stays inside the signature builder, as in the connection implementation;
the list-field module is imported from the package root, so a module-level `.orders` import
would break the [lazy-subpackage contract][glossary-pep-562-lazy-export] even for consumers that
never construct an order-capable field.

The builder is parallel code, not an import from
[`django_strawberry_framework/connection.py::_synthesized_signature`][connection]: the
connection module imports the shared DjangoType target guards from
[`django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`][list-field], so
reversing that edge would close a module cycle. A neutral parameter-construction helper is
extractable only if it is genuinely smaller and lives below both modules; the list field
never imports the connection module merely to avoid a few `inspect.Parameter` calls.

### Decision 2 — sidecar-conditional `orderBy` is the only truthful Meta-first surface

Three optional arguments on every `DjangoListField` and ordering from the target's
`orderset_class` cannot both hold for a type without that sidecar. The collision resolves in
favor of the package's DRF-first public API and [`spec-028`][spec-028] Decision 12:
`offset` and `limit` are universal; `orderBy` is present exactly when `Meta.orderset_class`
supplies its type and semantics. A published `offset` is a runtime-precondition coordinate
(Decision 6), not a claim that every field can serve a positive offset.

*Alternatives rejected: see the [rationale][rationale-d2] (auto-generating OrderSets, JSON
argument, dummy input, mandatory orderset_class, conditional offset publication, a
resolver's own `.order_by(...)` as the offset contract).*

### Decision 3 — one validation record computes both window and errors

A private immutable normalized-arguments record
(`django_strawberry_framework/list_field.py::_ListArguments`) holds `offset`, `limit`, the order
input, whether that input was supplied, and whether any argument was supplied. Material order
activity comes from the `OrderSet`-owned
`django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms`, not a
list-field input walker. One list-argument normalizer
(`django_strawberry_framework/list_field.py::_normalize_list_arguments`) runs after `info` is
available and before any queryset slicing. It treats `None` and `strawberry.UNSET` as omission,
requires an EXACT `int` (which rejects `bool` and every other subclass, so no consumer `__lt__` /
`__gt__` / `__format__` can run inside the range checks or the error rendering), and performs
the cap checks in the table above. Every numeric value the rejection wording interpolates
renders through `truth.render`, so an integer CPython refuses to stringify cannot replace the
typed error with a raw `ValueError`. It validates `offset` before `limit`, matching the
synthesized signature and SDL order, so a direct call with both values invalid has one
deterministic first failure.

The record answers distinct questions with distinct fields, and no consumer of one reads
another as a proxy for it. `any_argument_supplied` is true when any of the three arrived
non-null; it selects the argument-bearing pipeline and nothing else. The `window` fields
(`offset`, `limit`) say which rows are returned, and `offset: 0` with an omitted limit produces
the same window as omission - which is why Decision 9's fast path is a MODE decision and never a
window comparison. `order_by_supplied` says whether an order argument arrived at all, and it,
never material activity, drives the `queryset_required` source check, because an empty list is
still a supplied order argument. Material order activity is the fourth question and is answered
only after public apply succeeds. Collapsing any pair of these into one bit would let one
question answer another - `orderBy: []` is a supplied order argument with no material activity -
so the record keeps them apart by construction, and
`tests/test_list_field.py::test_list_field_record_independence` pins each field's independent
effect.

Argument wire names are resolved LAZILY, only while constructing a `ListArgumentError`, and
never by running the converter again.
[`strawberry/schema/name_converter.py::NameConverter.from_argument`][strawberry-name-converter]
is a consumer-supplied hook on custom-converter schemas, exercised per argument during schema
construction and by Strawberry's own argument mapping on each execution; the framework adds no
third call site. Invoking a shared, possibly stateful consumer object from the error path would
run it concurrently across simultaneous rejections and could report a spelling the built schema
does not use, so the error path reads the published argument map instead
(`django_strawberry_framework/utils/typing.py::published_argument`).
`tests/test_list_field.py::test_resolve_argument_wire_name_never_runs_the_schema_name_converter`
asserts zero converter calls on a valid normalization and on a rejection; the live rows
`examples/fakeshop/test_query/test_list_field_api.py::test_holder_naming_converters` and
`examples/fakeshop/test_query/test_list_field_async_api.py::test_async_rejection_reports_the_published_name_without_extra_converter_calls`
assert that a rejected request costs exactly the converter calls a successful one costs and
that the reported `argument` is the published name.

The record lives in [`django_strawberry_framework/list_field.py`][list-field], the argument
owner. The shared resource-policy module does not import a list-field type (which would
reverse the dependency and create a cycle); the wrapper passes only validated
`offset` / `limit` scalars into the package-private coordinate-bearing seam,
[`django_strawberry_framework/resource_policy.py::_windowed_rows`][resource-policy] and its
async sibling `django_strawberry_framework/resource_policy.py::_windowed_rows_async`. The
exported `bounded_rows` / `bounded_rows_async` have coordinate-free signatures -
positional-or-keyword `declared`, keyword-only `trusted` - and are thin callers of that seam
with no window; neither accepts a coordinate. The seam calls the one `effective_bound`
implementation when it builds the final slice.

The window inherits the request deadline from those helpers. Both raw-list spellings reach
`effective_bound` through the shared
[`django_strawberry_framework/resource_policy.py::_raw_list_bound`][resource-policy] helper,
whose first statement is `check_deadline(info)` - the "last look at the clock before rows are
fetched", and the reason `ResourcePolicy.execution_deadline_seconds` names `bounded_rows` (both
spellings) among its cooperative seams. Routing the client `offset` / `limit` through the same
helpers keeps one deadline check in the same position relative to row fetching. The list field
makes no `check_deadline` call of its own, and the window arithmetic does not move ahead of that
one: an argument-bearing request gets the same clock behavior as a bare one. The pre-bound
rejection paths in Decision 8 hand no work to the database and reach no deadline check at all.

The client coordinate handed to the private seam is a distinct `requested_limit`
parameter; it is not routed through the positive-only field-declaration validator.
`limit=0` is a valid client coordinate while `max_rows=0` is an invalid schema declaration.
The effective returned-row ceiling comes from
[`django_strawberry_framework/resource_policy.py::effective_bound`][resource-policy]; there is
no second `min(policy, field)` implementation. Validation rejects `limit > effective_ceiling`
before constructing the window. The subsequent minimum is therefore the client value when
supplied and the effective ceiling when omitted: a client can ask for less, never more, and
nothing is silently clamped.

### Decision 4 — `max_list_rows` also bounds skip; trusted widening does not

The maximum accepted offset is the request's `max_list_rows`. *Alternatives rejected: see the
[rationale][rationale-d4] (a dedicated max_list_offset setting).*

`trusted_max_rows` is not consulted for offset. It states that a schema author trusts a field
to return more rows; it says nothing about the cost of making the database discard rows.
Treating it as both declarations would widen the skip dimension under an option that declares
only returned rows.

An offset greater than the result set is valid when it is within the policy ceiling and
returns an empty list. It is not an error: the request stayed inside the accepted
coordinate ceiling, and concurrent deletes can make any valid page overshoot.

Skip and return ceilings are independent dimensions. The request may therefore have
`offset + effective_limit > max_list_rows`; the maximum untrusted endpoint is twice the
policy value, while each of the two kinds of work remains separately bounded. Trusted field
widening can raise the return half but never the skip half. *Why requiring the sum to fit
under max_list_rows and single scan budgets were rejected: see the [rationale][rationale-d4].*

`max_list_rows` therefore has a returned/materialized-row meaning on the return dimension and
is reused as a separate accepted-skip ceiling. Both are ACCEPTED COORDINATE CEILINGS, not scan
budgets: they bound what a client may ask for, never what the backend plan does to satisfy it.
This spec says "accepted coordinate ceiling" rather than "work budget" for both dimensions, and
the `ResourcePolicy` `max_list_rows` entry, the `bounded_rows` docstring and the
`_windowed_rows` / `_windowed_rows_async` docstrings say the same, so "evaluate" cannot be read
as a total scan guarantee. *Derivation: see the [rationale][rationale-d4].*

The pre-execution collection-cost walker charges a raw list `ResourcePolicy.max_list_rows`
whatever the operation supplies. That charge is a SCHEMA-GENERIC FIXED ESTIMATE. Runtime row
fetch and serialization honor the smaller client limit. *Derivation of the fixed estimate and
why argument-name matching was rejected: see the [rationale][rationale-d4].*

### Decision 5 — validate, then visibility, ordering, and exactly one slice

For a request carrying any non-null list argument, the color-specific queryset pipeline is:

1. Validate and normalize `offset` / `limit` from `info` before invoking a consumer resolver
   (active wire names are resolved lazily only if constructing an error).
2. Invoke the default or consumer resolver and normalize a `Manager` to a `QuerySet`. A sync
   resolver returning an awaitable has it disposed and rejected, and an async resolver is
   awaited once with a residual awaitable disposed and rejected rather than recursively
   awaited.
3. Apply the target's `get_queryset` visibility hook through the shared sealed boundary,
   under `_DEFAULT_SEAL_POLICY` whether or not arguments are supplied. Its source seal
   rejects an already-sliced queryset before the consumer hook runs, and its result seal
   rejects a hook-returned sliced queryset before later ordering or pagination. A combined
   queryset (`union`, `intersection`, or `difference`) is served at both seals as the set of
   primary keys it selects (the `rewrite_combined` axis of
   [`django_strawberry_framework/utils/querysets.py::_SealPolicy`][querysets], built by
   `django_strawberry_framework/utils/querysets.py::_pk_membership_query_or_defect`), so the
   hook, `OrderSet` and the optimizer narrow, order and window a query Django can compose; a
   combined shape that rewrite would change fails closed with the `combined` defect's
   `ConfigurationError`, which both visibility message sites render. The rewrite runs inside
   `_seal_or_defect`, after the pre-clone and post-bake `_combined_query_table_defect` proof
   passes, not in a list-field pre-check. The seal is a rebuild boundary whose complete
   combined-branch proof runs twice when deferred filters are baked, and the list field does not
   weaken it into a one-off validator.
4. If supplied, run the canonical public `OrderSet.apply_sync` / `apply_async` path. The
   async wrapper calls `apply_async` without assuming that an override kept `async def`:
   a non-awaitable return is a schema-author defect and raises an actionable
   `ConfigurationError` naming `OrderSet.apply_async`; an awaitable is awaited exactly once,
   and a residual awaitable is disposed and rejected rather than recursively awaited.
   The resulting value is validated before active order state is consulted, through the shared
   queryset sealing machinery with surface-specific error text, under
   `django_strawberry_framework/utils/querysets.py::_SIDECAR_RESULT_POLICY`, the post-sidecar
   policy that sets `require_unevaluated`. The requirement is on the SEALED OUTPUT, never on the
   candidate's class. The shared seal accepts a sealable `QuerySet` SUBCLASS and rebuilds it
   into a framework-owned plain `models.QuerySet`; that is a central feature of the boundary and
   is not narrowed here. A custom `OrderSet.apply_*` returning a project's own `QuerySet`
   subclass is therefore accepted, and what the pipeline carries forward is the plain sealed
   rebuild rather than the subclass itself. That sealed output is unevaluated, unsliced,
   non-projection, and over the same model and concrete table, with the input's effective
   database routing; a combined result is served as its primary-key set, as a combined source
   is. A `Manager`, list, `None`, wrong-model queryset, values/values-list queryset, populated
   `_result_cache`, or malformed query state is a schema-author defect and raises an actionable
   `ConfigurationError` naming the public apply method. A pending `_deferred_filter` is not a
   failure on any class: the seal bakes it onto the detached clone for a subclass exactly as for
   an exact queryset, and what fails closed as `untrusted` is a deferred-filter STATE that is not
   the exact shape Django writes (Decision 8). A sync-path awaitable is disposed and rejected
   under the one-await policy. The require-unevaluated option is enforced inside
   [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets] and emits its
   own `evaluated` defect rather than reusing another code: no seal that recomposes onto its
   result carries `_result_cache` forward, so without the option an evaluated candidate would
   be silently normalized into a fresh unevaluated queryset - an override that ran its own SQL
   and returned rows would be turned into a second identical query instead of rejected. The
   raw-list row source is the one policy that does carry it, and it recomposes nothing
   (Decision 8). The option defaults off; `_SIDECAR_RESULT_POLICY` is the one policy that sets
   it.

   The seal's defect codes have one canonical ordering every message site shares: `type`,
   `table`, `untrusted`, `routing`, `evaluated`, `sliced`, `projection`, `combined`, `alias`.
   That ordering is the vocabulary each site renders from, not the order the checks run. In
   `_seal_or_defect` the checks run: `type` (the real class is not a `QuerySet` subclass);
   `table` (the candidate's `model` slot is not over the concrete table); `untrusted` (the
   `_query` slot is not exactly `sql.Query`, then a retained `QuerySet.__dict__` slot fails
   `_queryset_state_defect`); `routing` (only under a frozen routing record); then the query
   graph walk (`_combined_query_table_defect`, reporting `table` or `untrusted`), the clone's
   reconstruction, the deferred-filter bake and its re-walk, the row-iterable class, the
   prefetch lookups and, under the carry policy, the `_result_cache` shape (each `untrusted`);
   then `evaluated`, `sliced`, `projection`, `combined` and `alias` in that order. Routing is
   therefore compared once the outer query type and the retained slots are proven, and before
   any graph walk, clone or reconstruction. Each message-building site renders only the subset
   it can reach: the post-sidecar site,
   `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result`, renders
   `routing` and `combined` in their own wording and `type`, `table`, `untrusted`, `evaluated`,
   `sliced` and `projection` under one shape wording, with no `alias` arm because the routing
   check subsumes it there; the two visibility sites,
   [`django_strawberry_framework/utils/querysets.py::_visibility_result_error`][querysets] and
   [`django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`][querysets],
   reach neither `evaluated` nor `routing`, because no `get_queryset` seal sets
   `require_unevaluated` or carries a frozen routing record. No ladder ends in an unconditional
   branch for its last code -
   `django_strawberry_framework/utils/querysets.py::_defect_message` dispatches exhaustively, so a
   code added without an arm self-names as a framework defect rather than mislabelling an
   evaluated-result rejection as an alias mismatch or a wrong-table error. The failure is
   legible rather than silent, but an unarmed code still reaches the schema author as an
   unactionable message, so every code a site can reach owes that site an arm. The
   retained-state helper `_queryset_state_defect` is not the home of `evaluated`: that helper
   pins the `QuerySet.__dict__` fields every seal carries forward (`_db`, `_hints`, `_fields`,
   `_sticky_filter`, `_for_write`) and emits only `untrusted`, and `_result_cache` is not among
   them - the one policy that carries it pins its exact `list` shape in the seal itself
   (Decision 8).

   Same-route needs its own definition, because `_db` equality alone is not it. Django
   resolves an unrouted queryset's alias through the database router using both the model and
   `_hints`, so two querysets can each carry `_db is None` and still resolve to different
   databases when their hints differ - and the seal preserves whatever hints the candidate
   carried, copying them into the rebuild.

   The invariant is therefore stated on the CONNECTION, not on the hint contents. Before the
   public `apply_*` call runs,
   `django_strawberry_framework/utils/querysets.py::_snapshot_routing_intent` freezes a routing
   record carrying the sealed source's `_db`, a copy of its `_hints`, and the EFFECTIVE ALIAS
   that state answers to: the source's own `_db` when it is set, otherwise the answer of the
   same `ConnectionRouter` method Django's own `QuerySet.db` property would use. The accepted
   result is then reconstructed PINNED to that frozen alias. Hint comparison remains part of the
   seal (`django_strawberry_framework/utils/querysets.py::_routing_hints_equal`: the candidate's
   `_db` must equal the snapshot's, `None` included, and every hint value must be the SAME OBJECT
   the snapshot holds, because a router is free to tell two equal tokens apart by identity), but
   it is not what carries the attestation. It cannot be: a hint value is an arbitrary consumer
   object handed to the router untouched, and a standard `instance` hint is itself mutable, so an
   override can edit state INSIDE a hint it preserves by identity and change the router's answer
   without changing anything the seal can see. Deep-copying hint values is not the
   alternative - it would dispatch consumer code, has no defined equality for arbitrary
   objects, and breaks Django's ordinary `instance` hint semantics (*alternatives rejected:
   see the [rationale][rationale-d5]*). Resolving once, early, and pinning the output is what
   makes "the ordered result reads the source's database" mechanical.

   Timing is part of the contract: at most one router call, taken at the snapshot and only for
   an unrouted source, and none during validation. A router exception propagates unchanged; a
   router answer that is not a string alias fails the ordering call closed with a
   `ConfigurationError`. The sharded live suite
   ([`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db]) covers the
   `.using("shard_b")` source an override re-routes
   (`test_post_orderset_routing_mismatch_rejected_on_sharded_db`), the unrouted hint-driven
   mismatch (`test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db`), an in-place
   rewrite of the handed-over queryset
   (`test_post_orderset_in_place_routing_mutation_rejected_on_sharded_db`), an
   equal-but-distinct hint token under an identity-sensitive router
   (`test_post_orderset_equal_but_distinct_hint_token_rejected_under_identity_router`), and the
   mutable token whose internal state the router reads
   (`test_post_orderset_mutable_hint_cannot_reroute_the_completed_read`) - the row that proves
   the pin, because it is ACCEPTED and still completes on the source's alias.
5. Ask that same `OrderSet` implementation whether its normalized input contains an active
   term, then enforce the nonzero-offset ordering precondition.
6. Apply one combined raw-list window.
7. Return the lazy result for the
   [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] and GraphQL completion
   path.

Visibility precedes order permissions and the page window: an order permission may use
request context, and slicing before visibility is both a data leak and illegal to refilter
in Django. Ordering precedes slicing so the page coordinates refer to the ordered set.
The window is last so queryset SQL receives one `LIMIT/OFFSET` pair and no intermediate
query is evaluated. Scalar/cap validation runs first because it needs no source and an
invalid package-owned argument must not invoke a consumer resolver with possible side
effects.

Mechanical post-apply validation proves result shape, model/table, routing, laziness, and
slice safety. It cannot prove that arbitrary custom Python preserved the incoming `WHERE`
predicates. Overriding `OrderSet.apply_sync` or `apply_async` is therefore an explicit trusted
schema-author boundary, like writing `get_queryset`: the override must derive from the
[sealed queryset][glossary-sealed-execution-queryset] it receives and preserve its
visibility predicates and routing. The base implementation and conforming overrides keep the
framework visibility guarantee; a malicious override that discards the input and starts from
a fresh manager is outside it. The tests prove conforming delegation and every mechanically
enforceable violation rather than claiming to authenticate arbitrary consumer code.

This third seal is a full graph walk and rebuild, not an `isinstance` guard, and its cost is
accepted (*derivation: see the [rationale][rationale-d5]*). It runs on every public `apply_*`
return; there is no fast path. The list field never duplicates the seal's state reads locally
in order to skip it.

The client window is applied by the one raw-list bounding seam rather than sliced locally in
[`django_strawberry_framework/list_field.py`][list-field], and it is not on the exported
helper's signature. `offset` / `limit` are values the seam cannot check: a window wider than
the request's own ceiling would silently widen the bound
[`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] advertises
to everyone who imports it, and the argument normalizer is the single owner of that check,
rejecting an out-of-range value with a typed, argument-named error before any of it reaches the
seam. So the coordinate-bearing seam is package-private, and the exported helper and its
[`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
sibling delegate to it with no window - keeping their advertised bound unconditionally true
for a direct caller, with no second ceiling and no second error contract. That private seam is
the one raw-list window implementation for root and relation lists; callers without client
arguments take its coordinate-free branch. [`spec-047`][spec-047]'s invariant that the exported
pair is the only raw-list bound is read through this delegation:
[`django_strawberry_framework/resource_policy.py::_raw_list_bound`][resource-policy] is the
one place a limit is derived, and the private seam is the body those two names run, not a
second bound beside them. *Alternatives rejected: see the [rationale][rationale-d5] (a fresh
pagination helper).*

Async queryset completion needs one additional representation boundary.
[`graphql/execution/execute.py::ExecutionContext.complete_list_value`][graphql-execute]
checks synchronous `Iterable` before `AsyncIterable`, while Django querysets implement both;
returning a queryset directly from `AsyncDjangoGraphQLView` would invoke synchronous ORM
iteration inside the event loop. After the final slice, the async list path wraps a queryset
in a package-internal
[async-only queryset-row adapter][glossary-async-queryset-completion-adapter] whose
`__aiter__` delegates to Django's safe
[`django/db/models/query.py::QuerySet.__aiter__`][django-queryset] iteration. The adapter is
not a public collection type, and it does not implement `__iter__`: a synchronous iterator on
it would put it straight back on the branch this boundary exists to leave.

[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] recognizes it, applies the
root plan to its inner final sliced queryset, and rewraps the optimized queryset; without the
optimizer the same adapter completes safely. Optimization therefore sees the low/high marks,
and the async list suite
([`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async])
sets no `DJANGO_ALLOW_ASYNC_UNSAFE` escape hatch.

That recognition has one exact seam, and naming it is load-bearing because the failure mode is
silent. The unwrap/rewrap arm sits in
[`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`][optimizer-extension],
ahead of that method's documented step 1, so its `normalize_query_source` coercion, its
evaluated-queryset guard, and its return-type resolution all read the inner queryset rather
than the wrapper. An adapter reaching an `_optimize` without that arm would take its
documented step 2, where a non-`QuerySet` result passes through unchanged: every row and every
SQL assertion would still succeed while root-list optimization was silently gone, which is why
the package tier pins the unwrap identity and the inner queryset's low/high marks rather than
only asserting the response.

Rewrapping is an obligation of every return path out of `_optimize`, not only the optimized
tail. That method also returns early and unchanged on an already-evaluated queryset and again
when the return type resolves to no registered [`DjangoType`][glossary-djangotype]; either
path would hand graphql-core the bare inner queryset - the synchronous-`Iterable` completion
this adapter exists to prevent - if only the plan-applying tail rewrapped. The arm therefore
wraps whatever `_optimize` returns for an adapter input.
`tests/test_list_field.py::test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns`
pins the unwrap identity, the inner low/high marks and the wrapper on both early returns, and
`tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_evaluated_cache`,
`tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_unresolved_type` and
`tests/optimizer/test_extension.py::test_optimizer_preserves_async_adapter_optimized_tail` pin
each return path on its own. The sibling
[`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`][optimizer-extension]
awaits an async resolver result before calling `_optimize`, so the arm needs no async branch
of its own.

The adapter exists to keep the final sliced queryset lazy across the resolver boundary.
*Alternatives rejected: see the [rationale][rationale-d5] (in-coroutine list materialization
via many_resolver).* Sync execution, materialized values, `None`, and genuine async-only
consumer sources keep their own result shapes. Adapter selection keys off the runtime
execution context for every final queryset, including a plain `def` consumer returning a
`Manager`/`QuerySet` under an async view; it does not change the callable-color rule for
whether a consumer or visibility hook is awaited.

The safety claim is scoped to FRAMEWORK-OWNED FINAL QUERYSET COMPLETION and is written that
way everywhere it appears. The adapter removes the one iteration the framework itself hands to
graphql-core. It cannot stop a plain `def` consumer resolver from calling `list(qs)`,
`.exists()`, `.count()`, or any other synchronous ORM method while already running on the
event-loop thread, and the field keeps the callable-color rule for that resolver. A
synchronous `get_queryset` hook is not on the loop: it runs in a `sync_to_async` worker, so
its body may call those methods. The async acceptance suite accordingly exercises CONFORMING lazy sync
resolvers - ones that return a queryset or manager without evaluating it
(`test_async_queryset_completion_sync_manager_resolver`,
`test_async_queryset_completion_sync_queryset_resolver`) - and never implies that an
evaluating sync resolver is made safe by the adapter's presence.

### Decision 6 — nonzero offset requires a materially active order

`offset > 0` succeeds only when at least one of these is true on the post-visibility
queryset:

- a supplied `orderBy` contains at least one non-null `Ordering` leaf that survives
  `OrderSet` normalization and the validated post-apply queryset reports an effective SQL
  order this package can read term by term; or
- the target model declares non-empty `Meta.ordering` that reads the same way, and the
  sealed queryset still has that default ordering materially enabled.

`orderBy: []` and `orderBy: [{ name: null }]` are no-ops under the order contract and
therefore do not satisfy the explicit-order branch. They do not disable the independent
model-default branch: an effective stable `Meta.ordering` may still satisfy the guard. Merely
declaring `Meta.orderset_class` is not an order. A resolver-returned queryset carrying ad hoc
`.order_by(...)` does not satisfy the model-default branch: the page's order contract is
VISIBLE through `orderBy` or model metadata, and hidden resolver order alone cannot explain why
one otherwise-identical field accepts offset and another rejects it. When active input is
supplied, the public `OrderSet.apply_*` contract requires a custom override to honor it;
mechanical validation can prove that the returned queryset is ordered but cannot prove which
arbitrary Python statements produced that order, the same trusted-override limitation
Decision 5 records for visibility lineage.

The model declaration is not enough when the actual query has stopped using it. After
visibility, the plain sealed queryset must select the model's ordering: default ordering is
enabled, no explicit or extra ordering has replaced it, and a grouping shape has not
suppressed it. A consumer resolver or `get_queryset` hook that calls `.order_by()` clears the
model default; one that installs a private explicit order replaces it. Neither can cite
`Meta.ordering` as the public offset guarantee. This state is read only after the visibility
boundary has rebuilt a framework-owned plain queryset, so the list field does not inspect
hostile consumer queryset internals or create another source classifier.

Both branches read ONE classification of the sealed queryset, and it is the classification
Django's own compiler makes (`django_strawberry_framework/utils/querysets.py::selected_order`,
the one spelling of it, which the connection order ladder reads too).
`SQLCompiler._order_by_pairs` selects a single collection by
precedence - `query.extra_order_by`, else `query.order_by`, else the model's `Meta.ordering`
while `query.default_ordering` stands - and ignores the others entirely. They are
alternatives, never a union. A term sitting in a collection the compiler did not select is
DORMANT: it never reaches SQL and cannot make a page unrepeatable, so it cannot reject an
offset. A term in the selected collection does reach SQL whichever collection that is, so a
random model default is exactly as disqualifying as a random `orderBy`-derived one. Scanning
the explicit collections and leaving model defaults out gets both verdicts wrong in opposite
directions, and the guard does not answer from a population the database does not run. The
selection is read from the already-sealed queryset's own state; the guard never invokes the
compiler, evaluates rows, or borrows `effective_connection_order`, which rewrites ordering to
the connection's total-order contract and therefore answers a different question.

Two named predicates keep these branches separate. The post-apply explicit-order check
(`django_strawberry_framework/list_field.py::_has_deterministic_ordering`, inside
`django_strawberry_framework/list_field.py::_check_nonzero_offset_guard`) accepts an active
normalized input only when its mechanically validated queryset reports `QuerySet.ordered` and
every term of the selected ordering is certified by the classifier below; an explicitly
ordered, known-empty `.none()` queryset may satisfy this branch vacuously because the
client-visible order contract still exists. The model-default predicate
(`django_strawberry_framework/list_field.py::_is_model_default_ordering_active`) is Django's own
default-ordering rule plus a stability requirement, not a parallel reimplementation of it. It
requires that the model's `Meta.ordering` be the collection the precedence above SELECTS:
empty `query.extra_order_by`, empty `query.order_by`, and a non-empty ordering read by
`django_strawberry_framework/utils/querysets.py::default_order` - the sealed queryset's
`model._meta.ordering`, by truthiness, reached only while `query.default_ordering` is truthy.
It then requires `query.default_ordering is True` as an exact identity rather than a
truthiness test, and Django's grouping rule spelled exactly as
[`django/db/models/query.py::QuerySet.ordered`][django-queryset] spells it, `not
query.group_by`. That last condition is a falsiness test, never `query.group_by is None`:
`group_by` is `None` on a plain query but a tuple of expressions once a `values().annotate()`
grouping exists, and Django itself builds it through `tuple(...)`, so an identity test against
`None` would reject a queryset Django considers ordered the moment that tuple is empty. Every
selected term must then be certified.

The model-default predicate does not read `QuerySet.ordered`, because that property
short-circuits `True` for an `EmptyQuerySet` regardless of ordering - a `Branch.objects.none()`
on a model declaring no `Meta.ordering` reports ordered. `query.standard_ordering is False` is
not a rejection: `.reverse()` reverses the model terms and remains a valid visible order, and
the terms are classified the same way in either direction. Live tests pin the reversed stable
default
(`examples/fakeshop/test_query/test_list_field_api.py::test_holder_reversed_model_default_ordering_still_pages`)
and both empty-queryset verdicts
(`examples/fakeshop/test_query/test_list_field_api.py::test_holder_empty_model_ordered_queryset_still_pages`,
`examples/fakeshop/test_query/test_list_field_api.py::test_holder_empty_unordered_queryset_still_requires_order`).

Django permits `Meta.ordering = ("?",)` and expression-based random ordering. Those terms
are active SQL ordering but cannot make an offset page repeatable, so a literal `"?"` or a
Django `Random()` expression does not satisfy the guard, alone or mixed with other terms,
whether they came from model metadata or a custom apply override. The exact string is `"?"`
and only `"?"`. The comparison lives in
[`django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`][django-compiler], the
generator that `SQLCompiler.get_order_by` consumes, and it tests `field == "?"` exactly, so a
descending spelling such as `"-?"` is not a random order at all - Django resolves it as a
column named `?` and raises `FieldError`. The classifier carries no `"-?"` arm.

A term is classified by the form the compiler resolves it into, never by its own top level.
`_order_by_pairs` reads a string through `query.annotations` (the whole name, then the head
of a transform chain) and then through `query.extra` before it reads any name as a field
path, and it compiles an expression from that expression's whole source tree. The random
form therefore sits one indirection away from what the ordering collection holds whenever it
arrives as an annotation alias, an `F` naming one, or a `Random()` nested inside a
composition, and a classifier reading the term as written certifies all three as ordinary
column orders. Only a name that survives every resolution step orders by a column.

A STRING name surviving to a field path is still not a column when that path ends on a
relation whose model declares `Meta.ordering`.
[`django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`][django-compiler] does not
order by such a relation: unless the last piece is the `attname` of the field the join walk
ends on, the whole name is `pk`, or a transform intervenes, it REPLACES the term with the
related model's `Meta.ordering` and resolves each of those terms against that model,
recursively. A relation whose model declares no `Meta.ordering` orders by its key column(s).
The classifier reads the same condition through
`django_strawberry_framework/utils/querysets.py::resolve_order_name`, whose final field is the
one `Query.names_to_path` ends on, not the relation as declared: a many-to-many ends on the
through table's key to its target and a generic relation on its reverse relation, which has no
`attname`, so either name expands whenever the related model declares an ordering, while a
multi-column `ForeignObject` ends on itself and orders by its carrier columns. A relation name
is therefore one more indirection of exactly the kind the annotation and `extra` steps are: a
model declaring `Meta.ordering = ("branch",)` over a branch declaring
`Meta.ordering = (Random(),)` compiles to a random order, and a classifier built from the term
as written certifies a related default it never read. Such a name is classified by every term
of the ordering it expands into, read against the RELATED model - a string as a field path
against that model, with no annotations and no `extra` to consult at that depth, an expression
by the same positive certification below, and an `OrderBy` through the expression it wraps.
Naming the column rather than the relation - `branch_id`, or `branch__pk` - is an ordinary
column order and backs the window. Three shapes are refused: a piece that is not a field of the
model in hand (a transform or lookup left over, which this package does not read), a path that
does not resolve, and an expansion Django rejects with
`FieldError("Infinite loop caused by ordering.")`
(`django_strawberry_framework/list_field.py::_is_deterministic_order_field_path`). The
compiler threads one `already_seen` set through the whole expansion of a top-level term,
sibling items of every related ordering included, keyed by the join columns of the join the
expansion starts from and of every join its path adds; the classifier keeps the same shared set
under the same key through
`django_strawberry_framework/utils/querysets.py::take_order_expansion_step`, the step the
connection order ladder's expansion takes, so a related ordering naming the same relation twice
(`("branch", "-branch")`) is refused exactly as a chain leading back on itself is.

Only a string expands. An expression REFERENCE naming the same relation is a column order:
`find_ordering_name` reads strings, while
[`django/db/models/sql/query.py::Query.resolve_ref`][django-query] resolves an `F` - bare,
wrapped in an `OrderBy`, or nested anywhere inside a composition - as the whole name against
`query.annotations`, then the head of a transform chain, and otherwise as a field path against
the QUERY's own meta, which yields a column and never a related model's `Meta.ordering`. So
`Meta.ordering = (F("branch").asc(),)` orders by the foreign key column whatever the branch
model declares, while the string `("branch",)` orders by the branch's own default, and a
classifier reading the two the same way inverts one of them. The annotation and `extra` steps
still apply to a reference, so an `F` naming a `Random()` annotation is refused. A reference the
compiler lifts out of an expanded ordering is rewritten through `prefix_references` and
resolved against the outer query under the relation path that reached it, so an `F("name")` in
the branch's ordering reached through `("branch",)` is the outer query's `F("branch__name")`
and is read at that full name.

Certification is positive and its boundary is an explicit list of APPROVED FORMS. Holding
source expressions is not a promise about a node's own SQL: `Func`, `Transform`, `Aggregate`
and `Window` each emit SQL around their sources, and any of them can be subclassed with an
`as_sql` emitting anything at all, so "transparent because its children are readable" would
certify a one-class project expression spelling `RANDOM()` over a column. A node is read
through only when it is a form this package names, and only if every source expression it
holds is certified too - an approved wrapper launders nothing, so `Coalesce(Random(),
Random())` is refused through its children. The named forms are: the transparent compositions
`Case`, `When`, `CombinedExpression`, `ExpressionWrapper` and `OrderBy`, whose own SQL is
punctuation around their sources; the pure database functions `Cast`, `Coalesce`, `Concat`,
`ConcatPair`, `Length`, `Lower` and `Upper`, each a deterministic function of its arguments;
the aggregates `Min` and `Max`, which an `OrderSet` annotates for a to-many path, and `Count`,
the row-count aggregate a consumer ordering may annotate; an `F` reference; and a `Q`
predicate. The readable leaves
(`django_strawberry_framework/list_field.py::_READABLE_ORDER_LEAVES`) carry all of their own
SQL and are named outright: a column reference, the `*` of a row count, a literal value, and
the framework's own visibility test
`django_strawberry_framework/utils/querysets.py::VisibleRowExists`. That test is an `Exists`
under its own exact type; it decides only whether an `OrderSet` term reads its column or
`NULL`, and its rows are a target type's `get_queryset`, which the guard already trusts for the
parent rows.

Every match is by EXACT type, the two reference forms included. A subclass of an approved
class is a different `as_sql` under an approved name and is refused, which is the difference
between naming a form and recognizing a family; a subclass of `F` or of `Q` is a different
`resolve_expression` under an ordinary name or an ordinary set of children, which is that same
difference one step earlier, because what the compiler receives is whatever that method returns
rather than the reference or the predicate this package read. Only `F` and `Q` themselves
therefore enter the reference and the predicate arms. Which arm a term takes at all is decided
the way `_order_by_pairs` decides it: a term carrying `resolve_expression` is an expression and
is read as one, and only a term without it is read as a string name - so a `str` subclass
carrying that method is classified as the expression Django resolves it to, never as the field
path it spells. Everything unlisted is refused: `Random()`, a bare or custom `Func` naming a
database function, a `Transform`, an aggregate outside the three, a `Window`, a `RawSQL`
fragment, and every `Subquery` other than `VisibleRowExists`, whose inner `Query` the classifier
does not read. A term it cannot read is one it must not certify as repeatable across the two
queries an offset window spans. A classifier built instead as a list of known volatile classes
certifies every spelling nobody put on the list, and `Random()` is only Django's name for one of
them; the approved list inverts that exposure, because a form nobody listed costs a refused
request rather than a re-shuffled page.

Raw SQL reached through `extra` - a name that is a key in `query.extra`, or the dotted form
the compiler hands through as `RawSQL` - is unreadable for the same reason: those strings are
passed through verbatim and reading SQL is the thing this package does not do. An `extra`
ordering naming a real field is an ordinary column order and satisfies the guard, as does a
conditional order whose predicate and results are themselves certified forms.
A predicate is read on BOTH sides of every comparison, and on the value side to the depth a
lookup can carry SQL. The lookup string names what is compared, and that reference is compiled
into the statement exactly as the value it is compared against is, so a `Case` picking its
result by `coin__gt` orders the rows by whatever `coin` is - reading only the value certifies
a random alias as an ordinary comparison against a literal and hands back the very page
ordering on `coin` directly is refused for. The lookup is separated into reference and lookups
the way [`django/db/models/sql/query.py::Query.solve_lookup_type`][django-query] separates them
when a `When` condition is built: the SHORTEST leading run of pieces naming an annotation wins,
and otherwise as many leading pieces as resolve to fields are the reference and the rest are
lookups and transforms. An annotation is classified like any other term, a field path is a
column order and is not expanded into its related model's default (a reference is not a string
ordering term), and a head naming neither is refused. The pieces that FOLLOW the reference are
classified too, because a transform wraps it in a function call and the lookup is the operator
around the comparison: `code__jitter__gt` resolves a column and then orders the rows by
whatever `jitter` emits. Each is matched by exact type the same way a node is - a transform
against the approved transform set (`Length`, `Lower`, `Upper`, `ExtractDay`, `ExtractMonth`,
`ExtractYear`, `TruncDate`, `TruncMonth` and `TruncYear`) and the final lookup against the
approved lookup set (Django's comparison, membership and null tests, including the integer- and
relation-specific spellings Django substitutes by field type) - so a project transform or lookup
registered on a built-in field is refused rather than skipped, while a reference with no
trailing pieces is compared under Django's implicit `exact`. On the value side a lookup taking a
sequence holds its operands one bracket deeper - `name__in` a list, `created__range` a pair -
and the container itself resolves as no expression at all, so a predicate read only at its top
level would report a fragment boxed inside one as a comparison against literals.
The shared post-apply seal rejects consumer-defined expression classes as untrusted query
state. For approved forms over readable leaves that pass the seal, volatility in what the
database makes of them is the schema author's responsibility under Decision 7's
weaker-than-total-order contract; the list field reads terms and reverse-engineers no SQL.
The `OrderSet` input emits only certified forms
(`django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions`): a declared
field path as a column order (one key per carrier column for a carrier-backed relation),
`Min` / `Max` aggregates for a to-many path, and, for a path crossing a type whose
`get_queryset` hides rows, the `Case` / `When` value
`django_strawberry_framework/optimizer/predicates.py::visible_value` builds over
`VisibleRowExists` tests.

Django model default ordering may traverse a to-many relation and duplicate parent model
instances. The field keeps that documented ORM result-row behavior: offset counts SQL result
rows, not distinct parent identities, and no `DISTINCT` is injected. A consumer that requires
one row per parent uses an aggregate `OrderSet` term (the `Min`/`Max` behavior) or a connection
rather than relying on a to-many `Meta.ordering` fallback.

The rejection is
`ListArgumentError(argument=<active offset wire name>, reason="order_required")`, with the
same stable code and no ceiling. Offset zero never requires ordering. Omitted offset does not
require ordering even when a limit is supplied.

*Alternatives rejected: see the [rationale][rationale-d6] (among them unordered offset as shipped in
Graphene-Django, primary-key tiebreaker injection as shipped in
Strawberry-GraphQL-Django).*

### Decision 7 — active order is not total order; no pk tiebreaker is appended

An active `orderBy` or `Meta.ordering` may contain ties. The list field preserves the exact
declared terms and does not append primary key. This is intentionally weaker than
`DjangoConnectionField`, whose positional cursor contract requires a deterministic total order
and obtains one in
[`django_strawberry_framework/connection.py::_finalize_queryset`][connection].

That gap is a contract limit, named here once so the rest of this document, the docstring, the
glossary, and the tests use the same words for it. What the field delivers is **ordered
offset**: the skip is counted over an order the client can see and reason about. It is NOT
stable or repeatable pagination. Ordering by `city` alone is a deterministic ordering
EXPRESSION, but it does not determine which of two tied rows falls on either side of an offset
boundary; a database may return tied rows in either order between equivalent executions, and no
concurrent write is required for that. Concurrent inserts and deletes make the problem worse
but are not its cause. Nothing in this spec, the field docstring, the glossary entry, the
consumer docs, or the error text promises a stable or repeatable page.

Keeping the active-order guard while declining the stronger promise is the field's minimal
shape, and it makes a unique final term a CONSUMER obligation the framework documents and does
not enforce. *Alternatives rejected: see the [rationale][rationale-d7] (requiring a provably
total order, appending a deterministic terminal pk tiebreaker).*

Django 6.1 ships a `QuerySet.totally_ordered` helper covering common field cases. It is not a
portable substitute for the declared policy: the package supports Django 5.2 through latest,
and the helper cannot speak for arbitrary expressions on any version. Its availability is not a
guarantee this field makes.

Consumers that page through tied values add a unique final term themselves, for example
`orderBy: [{ city: ASC }, { id: ASC }]`, or declare it in model `Meta.ordering`. The field
docstring and the [consumer docs][docs-readme] carry that as the recommendation it is.

### Decision 8 — queryset and iterable sources have explicit, different capabilities

`limit` and zero offset work on querysets, materialized sequences, and ordinary iterables.
The public list-field pipeline permits nonzero offset only for a queryset carrying the
visible order guarantee below; an opaque Python iterable cannot establish it. Once the
single bounding seam is handed validated coordinates, the window is applied with an operation
the package owns the meaning of. A value whose exact type is one of
`django_strawberry_framework/resource_policy.py::_SLICE_BOUNDED_ROW_TYPES` - `list`, `tuple`,
`str`, `bytes`, `bytearray` or `django.db.models.QuerySet` - receives `[start:stop]`: on the
queryset, slicing is what carries the bound into SQL as `LIMIT`, and each built-in sequence keeps
its type. Every other shape - a subclass of one of those sequence types, a mapping, a
non-subscriptable iterable - is counted into a fresh list with `itertools.islice(start, stop)`.
Which operation applies follows from what the value IS, never from whether a subscript happened
to answer, because `__getitem__` on a consumer's own sequence type is consumer code and a bound
enforced by calling it is a bound the bounded party decides.

A `QuerySet` SUBCLASS is the one shape that is neither sliced as itself nor counted. It is
normalized first, by the one shared seam every raw-list caller runs
(`django_strawberry_framework/utils/querysets.py::normalized_row_source`), which rebuilds it into
a plain framework-owned queryset through the same sealer the visibility boundary uses -
preserving model, query graph, routing, row iterable and prefetch state - and then slices that.
A subclass whose declared model is not a model class, or whose state cannot be faithfully
rebuilt, is refused with a typed `ConfigurationError`; the fallback is never its own
`__getitem__`.

A pending reverse-relation predicate is not that case. Django's related-manager machinery leaves
a `_deferred_filter` - the `(negate, args, kwargs)` tuple it has not yet baked into the query -
on every relation queryset it builds, whatever class the model's manager was made from, so
refusing it for a subclass would refuse `Manager.from_queryset` at every relation it is used on.
The rebuild resolves it identically for every candidate: each argument is proven inert or a
genuine, unshadowed Django expression first, and the predicate is then added to the DETACHED
clone through the UNBOUND `sql.Query.add_q`, never through the candidate's own methods and never
mutating the candidate. What fails closed is the pending STATE rather than the class holding it -
a shape Django never writes (a non-3-tuple, a `negate` that is not an exact `bool`, a `kwargs`
that is not an exact `dict`, an `args` that is neither `tuple` nor `list`, a non-string kwarg
key, a prohibited connector kwarg, a value that is neither inert nor genuine Django, or a
predicate `add_q` cannot resolve) is the typed `ConfigurationError`, never a raw exception. The
`negate` slot is pinned to an exact `bool` for the same reason the others are pinned: it is
truth-tested to decide whether the predicate is negated, and an object planted there would decide
that through its own `__bool__`. Sealability therefore does not depend on which surface seals: a
`Manager.from_queryset` relation is admitted at the raw-list row source, at the visibility
boundary, and at the post-sidecar result seal alike.

The fakeshop acceptance model uses that declaration directly: `Loan` declares
`objects = LoanQuerySet.as_manager()` over an override-free `LoanQuerySet`, so Django's ordinary
manager and reverse-relation machinery hand the live plan a `QuerySet` subclass. The dynamic
manager is left out of migration state through Django's `use_in_migrations=False` default.

Counting a sealable subclass into a Python list would restore the row ceiling but lose the SQL
`LIMIT` for a legitimate project queryset class. The shape is read from `type(value)` rather
than `isinstance`, because `isinstance` falls back to a consumer-defined `__class__` and an object
that merely claims to be a queryset would select the slice arm. `isinstance` results and consumer
`__getitem__` results define no part of the ceiling. The same rule governs the relation cache:
the generated many-side resolver normalizes the cached source before reading the rows it already
fetched, so that read is Django's own slot on an object the package owns rather than an
attribute lookup the subclass answers. *Derivation and rejected alternatives: see the
[rationale][rationale-d8].*

Evaluation state travels with the source. A queryset that reaches the seam already evaluated - a
warm prefetch cache, a manager result a caller iterated before handing it over - is windowed from
the rows it holds, with no further query, for the exact type and for a rebuilt subclass alike.
The rows are read from the instance dictionary through
`django_strawberry_framework/utils/truth.py::instance_state`, the read the sealer takes, never
through attribute access. The generated many-side resolver hands that fetched `list` itself to
`bounded_rows` (`django_strawberry_framework/utils/querysets.py::materialized_rows`), and an
evaluated exact or rebuilt queryset reaching `_windowed_rows` is sliced by Django's own
`QuerySet.__getitem__`, which answers from the populated cache. Re-querying a project queryset
class for rows it had already fetched would make `Manager.from_queryset` cost one query per
parent row more than Django's manager at every relation it is used on, and on the prefetched
branch of the generated many-side resolver it would hand graphql-core an unevaluated rebuilt
source that is iterated on the event loop under async, where Django raises
`SynchronousOnlyOperation`. The rebuild therefore carries the fetched rows forward when the
source it rebuilt held them, and drops nothing but the subclass's own methods. A source whose
query selects an annotation is served the same way: the row converter Django caches on the
annotation's node at the fetch is a derived cache the rebuilt node recomputes, not state the
rebuild carries (spec-045 Decision 8). That carry
belongs to the raw-list seam alone, the one place where nothing is composed after the rebuild.
No other seal carries it, and what the others do with an evaluated source is two rules, not one.
`require_unevaluated` - the axis that refuses an evaluated candidate outright - is on for the
post-sidecar result seal
(`django_strawberry_framework/utils/querysets.py::_SIDECAR_RESULT_POLICY`) alone, which seals
every public `FilterSet.apply_*` and `OrderSet.apply_*` return; a `DjangoListField` reaches it
through `orderBy` alone. The field invoked that method one step earlier and takes its window on
what comes back, so rows already fetched mean the override filtered, ordered or paged something
other than the query about to run. A visibility seal ADMITS an evaluated source and drops its
`_result_cache` in the rebuild, on the hook's input and on the hook's result alike, so no cached
or injected row crosses the boundary and a consumer that evaluates inside the hook pays one
extra query - a cost, not a broken seal. That hook's contract is shared with the Relay node,
connection and relation surfaces, so holding it to the stricter rule here would make one hook's
verdict depend on which field called it.

The lower-level window arithmetic is shape-complete and unit-pinned, but it does not widen the
list field's order precondition, and the two tiers are kept apart: positive-offset arithmetic
over an async iterator is pinned against the helper directly
([`tests/test_resource_policy.py::test_bounded_rows_async_positive_offset_arithmetic`][test-resource-policy]),
while a live async-only source through the public field succeeds only as a limit-only or
`offset: 0` request, because the field rejects positive offset there. A live case pairing an
async generator with a positive offset is a rejection case, never a success. `limit == 0`
never iterates: a slice-bounded shape receives `[start:start]`, a counted shape the empty list,
and neither calls `islice`, `__next__`, or `__anext__`; an async source only has its iterator
acquired and optional `aclose` invoked as part of the shared cleanup contract.

`orderBy` is a queryset operation. Supplying it when a consumer resolver returns a
non-queryset raises
`ListArgumentError(argument=<active wire name>, reason="queryset_required")` rather than silently
ignoring the argument; this applies even to an empty, otherwise-no-op list, matching the
connection sidecar guard. A nonzero offset over a non-queryset fails the active-order
precondition: model `Meta.ordering` cannot establish the ordering of an arbitrary Python
iterable. Limit-only and zero-offset requests are valid for every iterable shape. A
nullable resolver result of `None` follows the same rule: limit/zero-offset preserve `None`,
nonzero offset requires order, and non-null `orderBy` requires a queryset.

That `None` rule is a deliberate product choice rather than an oversight of GraphQL null
propagation: argument validation is CAPABILITY validation and outranks the nullable result. A
client that always sends pagination variables can therefore turn a legitimate `null` into an
error, and that is the intended behavior. `orderBy` over a source that cannot be ordered, and
a positive `offset` over a source whose order cannot be established, are both requests the
field cannot honor; answering them with `null` would report success for a page that was never
produced. *Why short-circuiting None was rejected: see the [rationale][rationale-d8].*
Because the surprise is real, both outer annotations are pinned live over the same
`None`-returning source
(`examples/fakeshop/test_query/test_list_field_api.py::test_holder_nullability_propagation_over_none_source`).
A limit-only request hands `None` to GraphQL completion unchanged, as a request without
arguments does: the nullable outer list answers `null`, the non-null one graphql-core's
`Cannot return null for non-nullable field` error, which the error policy masks on the wire. A
rejected argument raises its typed error on both.

Error precedence follows the pipeline rather than incidental exception timing. Numeric
validation (`offset`, then `limit`) runs before the consumer resolver. After source
normalization, a supplied `orderBy` over a non-queryset raises `queryset_required` before a
nonzero-offset `order_required` check. On a queryset, the source seal rejects a sliced source,
or a combined one its primary-key rewrite cannot represent, before invoking visibility; the hook
and result seal then run; `OrderSet` permission/application and its result validation follow;
the offset guard is last before the window. Thus a rejected source wins over a simultaneous hook
or order-permission failure, a rejected hook result wins before OrderSet, and malformed
post-apply output wins over offset rejection. Live rows with two simultaneously-invalid
conditions pin four of these boundaries in
`examples/fakeshop/test_query/test_list_field_api.py`:
`test_shipped_branches_a_negative_offset_is_named_before_a_negative_limit`,
`test_shipped_branches_a_materialized_source_is_named_before_the_order_requirement`,
`test_shipped_branches_a_presliced_source_is_named_before_the_ordering_runs`, and
`test_shipped_branches_an_order_permission_denial_precedes_the_order_requirement`. This is
resolver-local precedence after GraphQL validation and the schema's pre-execution
resource-policy checks; a document-level budget rejection can stop the operation before any
field wrapper runs.

If an async-only source is rejected for supplied ordering or nonzero offset before it reaches
the async raw-list seam, the list pipeline
(`django_strawberry_framework/list_field.py::_handle_non_queryset_rejections_async`) obtains its
iterator and invokes/awaits `aclose` when that optional method exists, without calling
`__anext__`. The `ListArgumentError` remains the primary exception; an ordinary failure to obtain
or close the iterator is attached as a diagnostic note, and every such note names the seam that
produced it, because more than one reaches the shared utility. This uses the same
package-private cleanup utility
(`django_strawberry_framework/resource_policy.py::_cleanup_rejected_async_iterable`) and
primary-error precedence as `bounded_rows_async`, so rejection cannot leak a generator or grow a
second cleanup policy. The close is owed on every rejecting exit, including when constructing
the `ListArgumentError` itself fails (malformed schema metadata behind the wire-name lookup):
that failure becomes the primary exception and the same cleanup runs before it propagates.

The same close is owed one seam later, for the same reason. The async raw-list seam
(`django_strawberry_framework/resource_policy.py::_windowed_rows_async`, the body
`bounded_rows_async` runs) reads the request's deadline and row bound AFTER the consumer
resolver has already produced its source, so a deadline that expired while that resolver awaited
rejects while holding an async-only iterable nothing else will ever see. No row has been
requested, but an async source may own an open external resource from the moment it is
constructed, so the rejection acquires its iterator solely to close it. The
`ResourceLimitExceeded` stays primary and complete - its `bound`, `limit` and `charged`
extensions are what the client acts on - and an acquisition or closure failure rides as a
diagnostic note. This is the SAME cleanup utility, which therefore lives below both callers
rather than being restated in a second module, and it is reached through the one deadline check:
there is no second clock read, and no caller-specific catch in the list field, where the other
callers of the shared bounding seam would stay exposed. `limit: 0` is included, because the
empty-window short-circuit sits downstream of the clock and so never gets to perform the close
it promises on a healthy request.

Primary-error precedence stops at ordinary failures. Cleanup runs while a useful error is
already on its way out, so a cleanup `Exception` is demoted to a note on it; a `BaseException`
that is not an `Exception` is not a cleanup diagnostic at all but a control signal addressed
to the task - cancellation, interrupt, interpreter exit - and it propagates instead. Demoting
one would let a cancelled request finish carrying an ordinary field error, reporting a
completed operation to a client whose task was torn down with the source still being closed.
Both cleanup seams share the one rule, and the primary error stays reachable as the signal's
`__context__`.

The symmetric SYNC contract is declined, and the decline is stated rather than left as an
implied promise. A retained sync generator consumed through
`list(islice(generator, start, stop))` stays suspended after the accepted stop: its `finally`
block does not run until something closes or exhausts it, and CPython reference counting is
not a cross-runtime resource-management contract - it does nothing at all while the caller
keeps its own reference. *Why sync early-exit close() is declined: see the
[rationale][rationale-d8].* The Definition of done promises leak-free early-exit cleanup for
async-only sources only. A resource-policy unit test pins the declined behavior as the current
contract - a retained sync generator remains suspended and resumable after truncation
([`tests/test_resource_policy.py::test_bounded_rows_declined_sync_cleanup_resumable`][test-resource-policy]).

An already-sliced queryset is under the sealed visibility contract. Its source seal rejects the
query before invoking `get_queryset`; its result seal also rejects a hook that returns a sliced
queryset. Both are `ConfigurationError` paths in
[`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`][querysets]
and its async sibling, and they apply whether arguments are active or omitted. The list
field does not read `source.query.is_sliced`, import the private seal, or translate the
failure into a list-argument reason (*alternatives rejected: see the
[rationale][rationale-d8]*). This also rejects limit-only composition safely. Django can narrow an
existing slice, but `get_queryset` may need to filter first and cannot legally filter a
sliced query; accepting it only for identity hooks would make one public argument
source-dependent and could bypass visibility.

### Decision 9 — a request with no list argument runs the plain bounded path; async only adapts completion

When all three arguments are omitted or null,
[`django_strawberry_framework/list_field.py::_normalize_list_arguments`][list-field] returns an
all-`None` record with `any_argument_supplied=False` before it reads the policy. Both pipelines,
[`django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync`][list-field] and
[`django_strawberry_framework/list_field.py::_execute_queryset_pipeline_async`][list-field],
test that flag after visibility and delegate to the coordinate-free raw-list window,
`_windowed_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)` - the body
`bounded_rows` runs. Nothing calculates `offset=0` or rebuilds an equivalent slice. Under the
synchronous executor that result is returned unchanged. Under the asynchronous executor a final
queryset is wrapped in Decision 5's async-only completion adapter, including when arguments are
omitted; that representation change is what keeps graphql-core's completion off the event-loop
thread, so the async path is not byte-for-byte resolver parity.
`examples/fakeshop/test_query/test_list_field_api.py::test_branches_a_null_spelling_reproduces_the_legacy_reference_bytes`
and
`examples/fakeshop/test_query/test_list_field_api.py::test_branches_the_shipped_field_matches_the_legacy_reference`
compare response bytes or rows, the `library_branch` SQL, the visibility-hook count, and the
final queryset's `str(query)` / `low_mark` / `high_mark` against a test-local reference
resolver composed from `apply_type_visibility_sync` and one `bounded_rows` call; the
`test_async_queryset_completion_*` rows in
[`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async]
prove the adapter's safe transport.

The SDL carries the optional arguments. Sync resolver behavior, SQL, ordering, nullability, and
response data match the no-argument reference; async response data and SQL match it while the
raw-queryset result representation is the adapter. No-argument raw lists carry a policy `LIMIT`
through [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy]
([`spec-047`][spec-047]), so the window contract is: omission keeps the policy `LIMIT`
unchanged, a smaller client limit lowers the high mark, and a positive offset raises the low
mark (*derivation: see the [rationale][rationale-d9]*). Tests pin exactly those three, and the
no-argument SQL is byte-for-byte the reference's, asserted live.

### Decision 10 — coercion errors stay GraphQL-owned; runtime domain errors are package-owned

GraphQL `Int` rejects strings, booleans, integers outside the signed 32-bit wire range, float
literals, and non-integral or non-finite float variables before a field resolver runs. Those
failures are already typed `GraphQLError` instances but cannot carry
`LIST_ARGUMENT_INVALID` without replacing the scalar or adding a schema-wide error-rewrite
layer. [`graphql/type/scalars.py::coerce_int`][graphql-scalars] accepts finite integral float
variables and coerces them to Python `int`, so `{"offset": 1.0}` reaches the wrapper as `1`;
origin-type rejection is impossible after standard coercion and is not promised. The spec
promises standard GraphQL error shape for actual coercion failures, not a package extension
code.

Negative and over-ceiling values are valid GraphQL integers but invalid list arguments, so
the wrapper raises `ListArgumentError` with package extensions. Direct unit calls that
bypass GraphQL also reject anything that is not an exact `int` - bools and `int` subclasses
included - through the same type, because internal callers do not receive GraphQL coercion
for free and a subclass would otherwise dispatch consumer code inside the boundary.

Under `DjangoSchema`'s production error policy both kinds reach the client untouched by
[structural error classification][glossary-structural-error-classification]: a coercion
failure carries no `original_error`, and a `ListArgumentError` raised in the resolver is
itself a `GraphQLError`.

*Alternatives rejected: see the [rationale][rationale-d10] (a custom stricter integer scalar,
a schema extension rewriting all Int coercion errors).*

### Decision 11 — migration maps upstream roots here and nested pagination to connections

Upstream offset surfaces map onto this package as follows:

| Upstream surface | Package mapping |
|---|---|
| `graphene_django.DjangoConnectionField(..., offset:)` | Prefer `DjangoListField(..., offset:, limit:, orderBy:)` when a flat list is the desired response; otherwise keep `DjangoConnectionField` and migrate to cursor arguments. |
| `strawberry_django.field(pagination=True)` / `OffsetPaginationInput` | `DjangoListField` with direct `offset` and `limit` arguments; no wrapper input object. |
| `OffsetPaginated[T]` / `offset_paginated()` | No envelope equivalent ships; choose flat `DjangoListField`, or a connection when count/page metadata is required. |
| Nested [`apply_window_pagination`][upstream-strawberry-pagination] | A synthesized nested `DjangoConnectionField`; raw nested offset windows do not ship. |

The mapping carries the order precondition and recommends a unique final order term.
Unlike upstream strawberry-django, `orderBy` is rejected on non-querysets, a positive offset
requires an active order (`OrderSet` terms or eligible model `Meta.ordering`), and pagination
arguments are flat rather than wrapped in a pagination input object. Two graphene-django
differences change response data rather than SDL: `DjangoListField.list_resolver` there
forwards the field's arguments into the consumer resolver (`resolve_x(self, info, **kwargs)`
receives `offset`), while here a consumer resolver never receives a list argument
(Decision 1); and there a resolver returning `None` is replaced by the model's default
manager, while here `None` stays `None`, and `orderBy` or a positive `offset` over it is
rejected as `queryset_required` / `order_required` (Decision 8). The written migration guide
belongs to card [`TODO-BETA-071-0.1.8`][kanban].

### Decision 12 — graphql-core workarounds have a dependency-owned lifecycle

The async-only queryset adapter exposes an upstream executor defect rather than creating it:
graphql-core's `ExecutionContext.complete_list_value` materializes an `AsyncIterable`,
recursively completes the list, and returns the recursive completion awaitable without
awaiting it. The workaround is
`django_strawberry_framework/_graphql_core_patches.py::apply`, a delegating wrapper that awaits
that residual value and otherwise preserves upstream behavior; it is separate from
Strawberry's HTTP-view patch module and has no HTTP-view lifecycle coupling.
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` dispatches it
beside the other three patch modules, and it self-gates on its own `APPLY_UPSTREAM_PATCHES`
key, `"graphql_core"` (`django_strawberry_framework/conf.py #"UPSTREAM_PATCH_DEPENDENCIES = frozenset("`),
so `APPLY_UPSTREAM_PATCHES = {"graphql_core": False}` disables only this dependency boundary.

The retirement sentinel,
`tests/test_graphql_core_patches.py::test_captured_upstream_still_returns_a_residual_awaitable`,
calls the captured upstream method on the bug shape and asserts that awaiting it once still
yields a residual awaitable. When upstream fixes the defect, that sentinel fails and the module
can be removed without disturbing Strawberry body parsing. See the [rationale][rationale-d12]
for the rejected shared-gate design.

### Decision 13 — configuration authority is schema state; everything per-request is operation state

Two kinds of state meet on every operation and never merge. **Configuration** - the resource
policy a request is bounded by, the error policy it is masked by, and the extension entries a
schema was accepted with - belongs to the schema and is read-only to every resolver.
**Operation state** - the engine context, the armed budget, the optimizer's frame, the executor
driving the request - belongs to the runner built for that one operation and is reachable only
through a task-local binding while that runner owns it.

The seam between them is what a resolver can reach. A resolver holds every shared extension
through `info.schema.extensions` and can assign over its attributes, so an attribute is not
where either kind of state can live. The two policies alone are canonicalized at construction
into [`django_strawberry_framework/schema.py::_SchemaEnforcement`][schema], a frozen record of
primitives held by
[`django_strawberry_framework/utils/private_state.py::PrivateAuthority`][private-state] under
the schema's identity and answered through `DjangoSchema.resource_policy` /
`DjangoSchema.error_policy` as a copy per read. The consumer extension entries are not
canonicalized: the schema holds them, and
[`django_strawberry_framework/utils/private_state.py::PrivateMembership`][private-state] holds
one piece of weak identity evidence per accepted entry
(`django_strawberry_framework/schema.py #"_SCHEMA_EXTENSIONS: PrivateMembership"`), so each
operation resolves the entries the evidence points at and an entry written over the attribute
is never run. Operation state is held by
[`django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner`][operation-state].
A schema whose evidence no longer resolves cannot read its own configuration back and refuses
the operation rather than falling back to a wider one. See the [rationale][rationale-d13] for
the rejected extension-attribute and engine-assignment designs.

### Decision 14 — an enforcement authority is a declaration, never an extension entry

`DjangoSchema` installs its own error-policy and resource-policy extension on every operation,
built from the construction record, and a consumer entry naming either kind is read once as a
DECLARATION that does not travel into the chain. Identity evidence about an entry authenticates
the object, not its future behavior, and the two authorities are the one place that difference
is fatal: a factory, a closure over a mutable cell, a singleton selector and a subclass all keep
identity while changing what runs next.

So the admission ladder is exact, and every rung is decided where it is actionable:

| Entry spelling | Where it is answered | Answer |
|---|---|---|
| exact class or exact instance of an authority | schema construction | what it declares (an exact resource-policy instance's own policy) is folded into the record; the entry is dropped |
| subclass of an authority, as a class or as an instance | schema construction | `ConfigurationError` |
| factory resolving to either authority, subclasses included | `get_extensions` | the operation is refused |
| factory that raises, or resolves to anything that is not a `SchemaExtension` instance (a class included) | `get_extensions` | the operation is refused |
| any other class, instance or factory | unchanged | runs between the two authorities |

A factory cannot be typed without calling it, and calling it at construction would break its
fresh-per-operation lifecycle, so what a factory PRODUCES can only be admitted at resolution -
which is why that boundary is one transaction: the factories run once, through upstream, and
every check reads the members that came back. See the [rationale][rationale-d14] for the
rejected identity-deduplication, subclass-admission and construction-time factory-call designs.

### Decision 15 — the runner owns every binding, for the operation's whole lifetime

One state object per (package-managed resolved extension, runner) - the package's own
authorities, its optimizer, its debug extension - bound by the runner around the operation
scope, around result collection, around the streaming-result hook, and around every resumption
of a streamed operation. Each binding is a LEASE on a weak reference, so a task that merely
copied the context stops reading at the instant the scope ends rather than when the owner is
collected; each is also a token, so a nested operation restores its caller's answer on the way
out. No token spans a `yield`: a stream is rebound in the task that drives it, because Python
resumes an async generator in the caller's context.

A plain `strawberry.Schema` never creates that runner and is not promised what it cannot be
given: a class entry and a fresh factory are operation-local there because the object is, and a
shared instance on a raw schema is outside the isolation guarantee. See the
[rationale][rationale-d15] for the rejected bare-`ContextVar` and operation-scope-only designs.

### Decision 16 — a refused request's document, selector and transport policy are all package-owned

A refusal runs nothing, and that has to include the parser: a document is arbitrary-length
consumer input that graphql-core parses recursively, so a deployment whose configuration broke
must not be the one shape that still lexes and nests whatever it is sent. The parse stage is
therefore handed a package-owned document, parsed once at import, one per operation type.

Three values are replaced together, because replacing one leaves the others authoritative:

1. **The document.** The request's own text stays on the execution context as an inert
   diagnostic and takes no further part in parsing, selection, validation or execution.
2. **The operation selector.** Upstream picks the operation to run by looking the REQUESTED
   name up in whatever document the parse stage left behind, so a substitute reached by a name
   still belonging to the request is a second error over the published refusal. The substitute
   carries one anonymous operation and the provided name is cleared, so the selector is the
   package's own.
3. **The transport policy.** `allowed_operation_types` is annotated `Iterable[OperationType]`
   and upstream tests the settled operation against it ONCE, after parsing. It is read once
   here, materialized into an exact built-in `tuple`, and that tuple is assigned back to the
   execution context before the substitute is selected from it - so package selection and
   upstream authorization read one immutable fact, and a one-shot iterable is not consumed
   twice. It is never asked whether it is empty: truthiness is consumer code.

See the [rationale][rationale-d16] for the rejected post-parse publication, name-copying,
per-request parse, policy-read-at-selection, and truthiness-normalization designs.

### Decision 17 — the refusal is stable, and the transport's own policy is the one exception

Every refused request answers with the published `SCHEMA_CONFIGURATION_UNAVAILABLE` code and
one of two fixed messages, one per cause:
`django_strawberry_framework/schema.py #"_UNREADABLE_CONFIGURATION = ("` when the accepted
extension entries can no longer be read back, and
`django_strawberry_framework/schema.py #"_UNRESOLVED_CHAIN = ("` when they do not resolve into
an admissible chain (a factory raised, returned something that is not a `SchemaExtension`
instance, or returned an authority). The message depends on the schema's cause alone, never on
the request: a malformed document, a name no document can carry (absent, invalid, empty,
non-ASCII, or not a string), a one-shot transport policy, and a hostile container all get the
same answer, and the failing object and any factory exception text go to the deployment's log
rather than the wire. The refusal is PUBLISHED as a pre-execution error and restated where
execution would begin, which is the pair of seams every transport renders - an exception out of
a hook leaves a streamed operation with no frame at all.

Two things still outrank it, and both are deliberate. The resource extension stays in the
refused chain, so the pre-parse token and depth scan still bounds the document being refused.
And a transport policy that genuinely allows nothing stays a policy that allows nothing:
upstream refuses that operation type as it would on a healthy schema. Widening the policy,
appending a default, or swallowing that refusal would make a broken configuration the one shape
that accepts what the transport forbids. See the [rationale][rationale-d17] for the rejected
unbounded-refusal, policy-widening and detail-interpolating designs.

### Decision 18 — execution mode is operation state; the ambient event loop is a different fact

Which GraphQL executor is driving a resolver decides what that resolver may hand back, and it is
NOT the same question as whether an event loop is running in this thread. `Schema.execute_sync`
is callable under a running loop - most directly from a resolver inside an asynchronous
operation, a nesting shape the runner supports - and there the loop says "async" while the
synchronous executor holds the operation. A field reading the loop there would return a
coroutine or an async-only adapter to an executor that cancels top-level awaitables, and the
client would get a generic completion failure while the inner coroutines went unawaited.

So the mode is carried rather than sampled.
[`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`][schema] receives the
authoritative `sync` flag and puts it in both the admitted and the refused chain; the runner
reads it once and binds it wherever it binds state.
[`django_strawberry_framework/utils/execution_mode.py`][execution-mode] owns the one definition
and answers two questions of it: `operation_is_async` states the fact for code with its own
answer to every outcome, and `async_execution` is the dispatch decision, which refuses the
disagreement with `SyncMisuseError` - naming `await schema.execute(...)` and a worker thread -
rather than building a value the executor cannot complete or driving the ORM on the event-loop
thread.

The whole census is classified, not just the list field. Every site that dispatches on execution
color - `auth/mutations.py`, `mutations/fields.py`, `relay.py`, `types/relay.py`,
`types/resolvers.py`, `connection.py`, `list_field.py` and `schema.py` - asks the same question:
may this resolver hand the executor an awaitable or an async-only value? None of them is an
ORM-safety read; the ORM safety lives inside the branches each one picks, and every one is wrong
in the same way when the loop and the executor disagree. So all of them read the canonical
helper and `strawberry.utils.inspect.in_async_context` has exactly one caller in the
package: the module that owns the fallback. Where the conjunction also carries a cheaper
question - a relation that is already loaded needs no query whatever executor is driving - that
question is asked FIRST, so the executor is consulted only where a coroutine would actually be
built.

A plain `strawberry.Schema` binds no mode, both readers fall back to ambient dispatch, and the
disagreement stays reachable there exactly as upstream leaves it. `DjangoSchema` is the spelling
that makes execution mode authoritative. See the [rationale][rationale-d18] for the rejected
ambient-predicate, field-local, loop-blocking, and silent-sync-fallback designs.

### Decision 19 — application code is trusted, the wire is not; a finding is admitted by reachability

Four parties meet on every operation. The contract names what is relied on from each and what
this package answers for, because a guarantee no layer owns is one every layer assumes the
other keeps.

| Layer | Relied on | Owned here |
|---|---|---|
| Django | ORM semantics, parameterized SQL, transactions, the auth primitives | visibility preserved through every composition, routing, transaction boundaries, safe async ORM use |
| Strawberry / graphql-core | schema construction, coercion, validation, execution, the extension lifecycle, the transports | using those contracts correctly and carrying this package's guarantees across their lifecycle |
| this package | - | Meta-driven generation, the optimizer, the resource and error policies, the list pipeline: correct defaults, bounded collections, isolated per-operation state, one enforcement path |
| the application | custom resolvers, hooks, extensions, authorization decisions | the documented result contracts are validated mechanically; the code itself is trusted |

The boundary is owned by [`GOAL.md`][goal]'s "Trust boundary" section and the admission rule by
[`AGENTS.md`][agents]; this decision applies both to the list surface. The line is Django's own,
and this package cannot sit above the foundation it runs on. Django's security policy admits a
report only when the code under test could feasibly exist in a Django project, and refuses one
that depends on calling private internals unsafely
([`docs.djangoproject.com` - internals/security][django-security-policy]). Read onto this
package: a finding is a defect here when the code it needs could feasibly exist in a project
using supported public API, and the input that triggers it arrives over the wire or through
ordinary configuration. Three trust levels follow.

- **Untrusted: the wire.** Every GraphQL document, variable, header, upload and transport
  frame. Every bound in this spec and in [`spec-047`][spec-047] exists for that input.
- **Validated, then trusted: configuration.** The two policies are canonicalized at
  construction and read back as copies; the extension entries are held by per-entry identity
  evidence; a configuration that cannot be read back is refused (Decision 13).
- **Trusted: application Python.** A resolver, a `get_queryset` hook, an `OrderSet.apply_*`
  override, a project `QuerySet` class, an extension factory. The package validates what it
  can establish mechanically about their RESULTS - shape, model, routing, evaluation state -
  and states the contract each must keep; it does not promise to contain what they do.

What the hardening guards is the ordinary-mistake class reachable through supported
spellings. A singleton inside a factory is the documented optimizer recipe; a `ResourcePolicy`
subclass, or a `__dict__` write on a frozen dataclass, is a line of ordinary Python; a `Manager.from_queryset` class is standard Django; a nested or concurrent operation
is a normal deployment. Each is application code behaving as application code does, and each
is answered so the request stays bounded and the state stays isolated. What is NOT guarded is a
deliberate adversary already inside the process: a `__class__` property that lies, a
`__getitem__` that ignores its slice, an object forged to look like a policy. Where such a
row is cheap to keep it stays as a robustness row - a fail-closed typed error is better than
an untyped one - but it is never a release blocker and never grounds for another admission
layer.

A finding is a defect against this contract only when it names all three of: (a) the
Definition-of-done row it breaks; (b) a project shape that could feasibly exist under
supported API; (c) the wire or configuration input that reaches it. A finding missing any of
the three is a robustness row in [`BACKLOG.md`][backlog] or its own card with its own
evidence, never a release blocker. Upstream defects are dependency defects: reproduce against
upstream, pursue the fix, and constrain or work around narrowly with a stated removal condition
(Decision 12 is the shape); a known exploitable upstream defect still blocks shipping the
affected configuration. See the [rationale][rationale-d19] for the rejected hostile-process
threat model and the rejected architectural rewrite.

### Decision 20 — the extension contract is upstream's; per-operation isolation is the guarantee this package adds

Strawberry's `extensions=[...]` resolves a class, a factory callable or an instance; the
instance spelling is deprecated upstream - `strawberry.Schema.__init__` warns on it
([`strawberry/schema/schema.py::Schema.__init__`][strawberry-schema],
[upstream issue 4369][upstream-strawberry-extension-isolation]) - and upstream's guide warns
that a factory returning one long-lived object shares request state across concurrent
operations. The contract here has three parts, stated separately because they are not the
same rule.

**Enforcement is configured, not installed.** The resource and error policies are declared
through `DjangoSchema(resource_policy=..., error_policy=...)`; the schema builds its own
authority extension per operation from that record (Decision 14). An exact instance of an
authority in `extensions=[...]` is a package-specific compatibility reading - read once as a
declaration, dropped from the chain before upstream sees it, so upstream's deprecation warning
does not fire for it. A SUBCLASS of either authority is refused at schema construction with
`ConfigurationError` - supplied as a class or as an instance, and whether or not it supplies a
policy of its own, because what disqualifies it is the override it may carry on the hook that
charges or masks. Only a factory is opaque until it is called, so a factory resolving to an
authority, subclasses included, is the one spelling refused at the operation instead, with the
stable `SCHEMA_CONFIGURATION_UNAVAILABLE` code (Decision 14's ladder). Moving such an instance
into a factory is therefore NOT a migration; the migration is to the keyword argument, and the
docs say so.

**Ordinary extensions follow upstream's spellings.** A class or a factory; an instance carries
upstream's `DeprecationWarning` unchanged, because `DjangoSchema` passes ordinary entries to
upstream as they were given and defines no instance-only semantics a consumer could come to
depend on.

**Isolation is added for the package's own extensions.** `DjangoSchema` gives every
package-managed resolved extension - its authorities, its optimizer under a class entry or a
factory result, the documented singleton-in-a-factory optimizer recipe included, its debug
extension - one state per operation through the runner (Decision 15), so
`extensions=[lambda: _optimizer]` is safe here where upstream says a shared instance is not.
That guarantee is this package's own: stated in the docs as its own, tested here, and not a
claim about upstream or about a third-party extension. A stranger's extension gets exactly
upstream's lifecycle: the package records the entries it was constructed with and answers its
configuration from that record (Decision 13), refuses an operation only where its own authority
cannot be established (Decision 14), and does not make another author's mutable attributes
thread-safe or claim to. See the [rationale][rationale-d20] for the rejected package-defined
instance semantics.

## Implementation plan

Where each part of the surface lives, keyed to the slice checklist:

| Slice | Files | Carries |
|---|---|---|
| 1 | [`django_strawberry_framework/list_field.py`][list-field], [`django_strawberry_framework/resource_policy.py`][resource-policy], [`django_strawberry_framework/__init__.py`][package-init] | `list_field.py`: the synthesized list signature (`_synthesized_list_signature`), argument normalization into `_ListArguments` with independent supplied/window/order fields and the no-argument fast path (`_normalize_list_arguments`), wire names read from the executable schema only on the error path (`_resolve_argument_wire_name` over `utils/typing.py::published_argument`), and `ListArgumentError`. `resource_policy.py`: the package-private window seams `_windowed_rows` / `_windowed_rows_async` beneath the exported coordinate-free `bounded_rows` / `bounded_rows_async`, and the shared async-iterator cleanup (`_cleanup_rejected_async_iterable` over `_close_async_iterator`) that keeps control signals out of its note path. `__init__.py`: the root `ListArgumentError` export. |
| 2 | [`django_strawberry_framework/list_field.py`][list-field], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/utils/querysets.py`][querysets], [`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`][optimizer-extension] | `list_field.py`: the sync/async queryset pipelines, the positive-offset guard and its order-normalization scope. `orders/sets.py`: `OrderSet._input_has_active_terms` and the invocation-scoped attestation ledger (`capture_applied_order_normalization`). `utils/querysets.py`: `apply_orderset_sync` / `apply_orderset_async`, the post-apply seal under `_SIDECAR_RESULT_POLICY`, `selected_order`, and the async-only queryset completion adapter (`wrap_async_queryset_adapter` / `unwrap_async_queryset_adapter`). `optimizer/extension.py`: the one unwrap/rewrap arm that preserves optimization through the adapter. |
| 3 | [`tests/test_list_field.py`][test-list-field], [`tests/test_resource_policy.py`][test-resource-policy], [`tests/orders/test_sets.py`][test-orders-sets], [`tests/base/test_init.py`][test-base-init] | Package-tier rows HTTP cannot isolate: construction/direct-call mechanics, naming fallback, the `ListArgumentError` pickle round trip, active-term/override call counts, post-apply validator arms, exact iterator consumption and cleanup precedence, model-order state, query low/high marks, and the root export. |
| 4 | `examples/fakeshop/test_query/test_list_field_api.py`, [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async], [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy], [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db], [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants] | Live rows over the library schema's three Branch list fields (`allLibraryBranchesViaListField` and its nullable and manager-resolver variants), with exceptional fields mounted only in test-local schemas: ordered pages, visibility, caps, errors, naming, sync/async shapes, routing, and SQL. The kanban constants module carries both list-field suites' tracked paths. |
| 5 | [`docs/GLOSSARY.md`][glossary] (DB), [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`README.md`][readme], [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme], KANBAN DB/exports | The argument, returned-row and skip semantics; the live-tier guide's entries for both list-field suites and the async suite's `AsyncTestClient` transport; the generated tree entries for both suites. |

## Helper-reuse obligations (DRY)

- [`django_strawberry_framework/resource_policy.py::effective_bound`][resource-policy]
  is the only field/policy ceiling rule.
- One package-private window seam per execution color is the only raw-list window
  implementation, and
  [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] and
  [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
  are coordinate-free delegations to it rather than a second body. Relation-list callers pass
  no client window and get the coordinate-free bound. The iterator-close/error-note logic is
  one package-private utility beside them,
  `django_strawberry_framework/resource_policy.py::_cleanup_rejected_async_iterable` over
  `django_strawberry_framework/resource_policy.py::_close_async_iterator`, below every caller:
  the list pipeline rejecting an async-only source before bounding, and the bounding seam's own
  deadline/row rejection, which abandons a source the resolver has already produced. Neither
  restates the acquisition, diagnostic-note or close policy, and no second cleanup
  implementation exists. The seam reads the deadline once; a rejection is routed through the
  utility rather than met by a second clock check or a caller-local catch, which would leave
  every other caller of the shared seam uncovered.
- `django_strawberry_framework/utils/querysets.py::selected_order` is the only place the
  effective-ordering precedence is spelled; the list field reads it through
  `django_strawberry_framework/list_field.py::_selected_ordering` and the connection order
  ladder through `django_strawberry_framework/utils/querysets.py::applied_order`. Both
  offset-guard predicates - the term-determinism check and the model-default eligibility
  rule - read its answer; neither scans `query.order_by`, `query.extra_order_by` or
  `Meta.ordering` on its own, because a second scan could disagree with the first and with
  `SQLCompiler._order_by_pairs`. The guard does not reuse
  `django_strawberry_framework/optimizer/plans.py::effective_connection_order`: that helper
  intentionally REWRITES ordering to the connection's total-order contract, so it answers a
  different question and sharing it would make the list field's verdict depend on a
  transformation it never applies.
- The list field builds its `orderBy` annotation through
  [`django_strawberry_framework/orders/__init__.py::order_input_type`][orders-init]. That
  helper and `django_strawberry_framework/orders/__init__.py::OrderInput.__class_getitem__`
  both reach `django_strawberry_framework/orders/__init__.py::_order_input_annotation` over
  `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`, which validates
  the class, writes the `_helper_referenced_ordersets` orphan ledger, and builds the lazy
  annotation; the list field has no annotation builder or ledger writer of its own.
- [`django_strawberry_framework/orders/sets.py::OrderSet.apply_sync`][orders-sets] /
  [`django_strawberry_framework/orders/sets.py::OrderSet.apply_async`][orders-sets] are the
  consumer-facing order permission and queryset application pipeline, and the list field
  calls those exact methods so a subclass override keeps the same behavior it has on a
  connection or hand-written resolver. The order module carries one package-internal
  `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms` classmethod
  that reuses its own normalization and flat-order machinery; the list field never walks an
  order input itself. The helper runs only after public apply succeeds, preserving permission
  and validation precedence. Re-normalizing the small input is the deliberate compatibility
  cost of honoring an overridden public apply method, in place of a parallel state-returning
  entry point that would bypass that override. Active input
  must also leave the returned queryset materially ordered, so a malformed no-op override
  cannot satisfy the offset guard on an otherwise unordered source merely by receiving a
  non-null input. `_normalize_input` overrides are therefore required to be pure and
  deterministic, and that is an explicit COMPATIBILITY CONSTRAINT on the method rather than
  merely a test counter: a request that reaches the active-term helper invokes normalization
  once inside public apply and once inside the helper, so a stateful override can otherwise
  produce different application and activity verdicts from one request. That second
  normalization is what the constraint is about, and it exists on exactly one path - an
  `orderBy` arriving with a positive `offset` through a field carrying an `OrderSet`. The
  check is therefore scoped to that path by construction rather than by omission: everywhere
  else normalization runs once, and a single verdict has nothing to disagree with. The
  requirement is documented on
  `django_strawberry_framework/orders/sets.py::OrderSet._normalize_input` itself. Over the wire
  the input it re-normalizes is already bounded: on a `DjangoSchema` every field argument is
  charged against the resource policy's value bounds (`max_input_nodes`,
  `max_container_width`, `max_value_depth`) by
  `django_strawberry_framework/extensions/resource_policy.py::_DocumentWalk.charge_arguments`
  before execution. An override whose second normalization disagrees with its first surfaces
  an actionable `ConfigurationError` naming the method rather than silently deciding the offset
  guard on an incidental verdict. Instrumented tests in
  [`tests/orders/test_sets.py`][test-orders-sets] pin the call counts, the purity requirement,
  and the disagreement error. The base
  `django_strawberry_framework/orders/sets.py::OrderSet._apply_orderings` hands its validated
  terms to the helper through one invocation-scoped ATTESTATION LEDGER
  (`django_strawberry_framework/orders/sets.py::_NormalizationLedger`, bound to a `ContextVar`
  that `django_strawberry_framework/orders/sets.py::capture_applied_order_normalization` opens
  around public ordering and the offset guard, CLOSING the ledger and then resetting the
  binding in nested `finally` blocks): when a scope is active the base implementation APPENDS
  an immutable `_AppliedNormalization` naming the orderset class, the input OBJECT, and its
  terms, and the
  helper CLAIMS the entries matching its own class and input object, then re-normalizes once to
  prove purity. Outside any scope - a connection, a hand-written resolver, any direct public
  call - publishing is a no-op, so a public `apply_*` call never writes, overwrites, or clears
  anything on the consumer's `info.context`, and a concurrent resolution that opened its own
  scope has its own ledger.

  The transport is a LEDGER rather than a slot because two requirements pull in opposite
  directions. A supported public `apply_async` override may delegate to `super()` inside a
  child task, and the ordering the client receives is then built there, so the guard must
  receive an attestation published from a child task, a copied context, or a `sync_to_async`
  worker thread - otherwise it compares its own second and third normalizations to each other,
  agrees, and blesses a page cut from terms it never saw. At the same time an UNRELATED
  application in any of those, or a different `OrderSet` invoked between publication and check,
  must not be able to displace the one the guard is waiting for. A shared mutable slot loses the
  parent's record to the last writer; a rebinding-only slot loses a legitimate child's record to
  context isolation. So nothing ever overwrites: every application appends, entries are matched
  by class AND input IDENTITY (never equality - a consumer `__eq__` has no say in whether an
  attestation applies), claiming is once per class-and-input pair for the whole resolution, and
  two applicable attestations that DISAGREE fail the claim closed rather than picking one.
  Appends and claims are lock-synchronized, because a copied context genuinely reaches one
  ledger from two threads.

  Closure is TERMINAL, not merely emptying. A descendant created while the scope was live holds
  the ledger OBJECT through the context it copied and may not resume until after the owning
  resolution has ended; an emptied-but-open ledger would let it append, claim its own
  attestation, and keep the input object alive in an orphan context past the resolution the
  records describe. `close()` therefore sets a tombstone and clears both collections under one
  lock acquisition, after which publishing is inert and claiming answers nothing - exactly what
  an application outside any scope already does. Closure runs before the binding reset and in
  its own `finally`, so a descendant observes the tombstone the moment the scope ends and a
  failing reset cannot skip it.

  The scope is opened only for the request shape whose guard can consume it: an `orderBy`
  arriving WITH a positive `offset` on a field that captured an `OrderSet` to normalize through.
  Every other argument-bearing request takes an inert context and pays for neither the ledger
  nor the deferred `orders` import; the no-`OrderSet` condition is DECIDABLE there rather than
  asserted, because the field's captured sidecar is passed to the predicate. An override that
  does not delegate to the base implementation attests nothing and the helper takes the
  double-normalization path, so public override dispatch is honored without a parallel
  state-returning entry point.
- [`django_strawberry_framework/utils/typing.py::schema_config_from_info`][typing-utils]
  is the neutral schema-config lookup for the optimizer and connection readers. Argument
  error names combine Strawberry `Info.get_argument_definition` with the executable schema's
  published argument map (`Info._raw_info.parent_type` -> `GraphQLField.args`, matched by
  `DEFINITION_BACKREF` identity); list code never re-runs `name_converter.from_argument` and
  does not reimplement wrapped/direct schema traversal.
- Manager-to-queryset coercion and visibility stay in
  [`django_strawberry_framework/utils/querysets.py`][querysets]; pagination does not grow
  another source classifier. Post-OrderSet validation reuses the same hardened seal under
  `_SIDECAR_RESULT_POLICY` (require-unevaluated, a combinator served as its primary-key set),
  plus a surface-specific `ConfigurationError` renderer; visibility runs the default policy at
  both source and result seals in every argument mode, and list code never reads hostile
  queryset state itself.
  That module also owns the internal async-only queryset-row adapter shared with the
  optimizer; the optimizer side of that pair is one unwrap/rewrap arm inside
  [`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`][optimizer-extension],
  never a second adapter class or a parallel planning path.
- The list-field signature builder,
  `django_strawberry_framework/list_field.py::_synthesized_list_signature`, owns list
  arguments and builds its own parameters; the connection's filter argument and return
  annotation do not reach the list field.
- One `ListArgumentError` constructor owns every runtime domain rejection and extension
  payload.

## Edge cases and constraints

- `offset: null`, `limit: null`, and `orderBy: null` are omission, not zero or empty input.
- `offset: 0` is accepted without ordering; `limit: 0` yields an empty list. A `limit: 0`
  request over an async-only source still closes it, and still closes it when the deadline
  rejects the request before the empty-window short-circuit is reached.
- A deadline that expires while the consumer resolver awaits rejects at the shared async
  bounding seam holding a source that was never advanced; that source is closed, zero
  `__anext__` calls are made, and the resource error keeps its complete extensions.
- `True` is rejected in direct calls even though Python treats it as integer `1`.
- `offset == max_list_rows` is accepted; `offset == max_list_rows + 1` is rejected.
- `limit == effective_ceiling` is accepted; the next integer is rejected.
- An offset beyond the available row count returns `[]` when it remains within policy.
- `trusted_max_rows=True` with no `max_rows` is inert: the limit ceiling and the returned-row
  bound stay the request policy's `max_list_rows`.
- `trusted_max_rows=True, max_rows=P+N` widens returned rows but not accepted offset.
- The row window is applied only through an operation the package owns. A queryset and an
  exact `list` / `tuple` / `str` / `bytes` / `bytearray` are sliced; a subclass of one of
  those, a mapping, and any other iterable are counted through `islice` into a fresh list, so
  a sequence type whose `__getitem__` ignores the slice cannot answer a bounded request with
  every row it holds. The zero-width window follows the same split, because
  `result[start:start]` is as much a consumer call as `result[start:stop]`.
- The exported `bounded_rows` / `bounded_rows_async` take no `offset` or `requested_limit`;
  supplying either is a `TypeError` from the signature itself. The client window rides only
  on the package-private seam beneath them, behind the argument normalizer's ceiling check.
- Empty and all-null order inputs do not satisfy the explicit-order branch; an independently
  effective stable model default may still satisfy the guard.
- A model whose `Meta.ordering` is empty (`Branch`'s) has no active default; a non-empty
  non-random ordering is active only while the post-visibility queryset still uses Django's
  default-ordering path.
- A model ordering containing `"?"` or a `Random()` expression is not an active
  stability order, even when another term follows it. This holds under an ACTIVE `orderBy` too:
  an override that returns the queryset unchanged leaves the random default as the order the
  page will actually run under, and the request is rejected.
- Ordering the compiler does not select is dormant and cannot reject an offset. A queryset
  carrying `.order_by("?")` under an `extra(order_by=[...])` that supersedes it is accepted;
  the mirror shape - a stable explicit order under a superseding random `extra` ordering - is
  rejected. An explicit stable `orderBy` over a random model default is accepted, because the
  explicit order is the one the compiler selects.
- A selected term is judged by what the compiler resolves it into. An annotation alias, an
  `F` naming one, and a `Random()` nested inside a composition all carry the random verdict;
  an alias naming a deterministic expression is an ordinary column order and satisfies the
  guard.
- A STRING term naming a relation is judged by the related model's own `Meta.ordering`, which
  the compiler expands it into: a relation whose target orders at random carries the random
  verdict, and one whose target orders by a column satisfies the guard. A many-to-many and a
  generic relation expand the same way, since neither name is the `attname` of the field the
  join walk ends on. The expansion is recursive, so a random default two relations away
  decides the same way. Naming the foreign key column instead - `branch_id`, or `branch__pk` -
  is an ordinary column order and is unaffected. An expansion that repeats a join already
  expanded anywhere under the same top-level term - a chain leading back on itself, or a
  sibling item of a related ordering naming the same relation again - is refused rather than
  followed, as Django raises `FieldError("Infinite loop caused by ordering.")` for it, and so
  is a path piece that is not a field of the model in hand.
- An expression REFERENCE to the same relation does not expand and is a column order. Only a
  string reaches the compiler's expansion; an `F` - bare, inside an `OrderBy`, or nested in a
  composition - resolves to the foreign key column, so `F("branch").asc()` satisfies the guard
  over a randomly ordered branch while the string `"branch"` does not. The annotation and
  `extra` steps still apply to it, so an `F` naming a random annotation is still refused, and a
  reference lifted out of an expansion is read at the prefixed name the outer query resolves.
- A term resolving into `query.extra` - a select alias, or the dotted form handed through as
  `RawSQL` - is opaque rather than deterministic and cannot back an offset window. An
  `extra` ordering naming a real field is unaffected.
- A term is certified only when it is a NAMED approved form whose sources are themselves
  certified: a transparent composition (`Case`, `When`, `CombinedExpression`,
  `ExpressionWrapper`, `OrderBy`), a pure Django function (`Cast`, `Coalesce`, `Concat`,
  `ConcatPair`, `Length`, `Lower`, `Upper`), an approved aggregate (`Count`, `Max`, `Min`), or
  a readable leaf (a column, the `*` of a row count, a literal `Value`, and the framework's own
  `VisibleRowExists` visibility test), each matched by exact type. A `RawSQL` fragment, a bare
  `Func` naming a database function, and the inner query a `Subquery` wraps are each refused
  as unreadable rather than accepted for matching no known random class; so are a project
  `Func`, a `Transform`, a `Window`, any other aggregate, and any SUBCLASS of an approved
  class, because a subclass is a different `as_sql` under an approved name. The two reference
  forms are matched exactly for the same reason one step earlier: a subclass of `F` or of `Q`
  resolves to an expression of its own whatever name or children it was built with, so only
  `F` and `Q` themselves are read as a reference and a predicate, and a term is read as a
  string name only when it carries no `resolve_expression` at all. A composition of approved
  forms over readable leaves is read end to end and satisfies the guard, including a
  conditional order's predicate and the slots an aggregate leaves unfilled, and an approved
  wrapper launders nothing - `Coalesce(Random(), Random())` is refused through its children.
- A conditional order's predicate is read on BOTH sides of every comparison, and on the value
  side to the depth a lookup can carry SQL. The lookup's reference is separated from its
  trailing lookups and transforms the way the compiler separates them: an annotation reference
  carries that annotation's verdict, so `coin__gt` over `alias(coin=Random())` is refused while
  the same predicate over `alias(coin=F("code"))` is served; a field-path reference such as
  `code__gt` is a column order; a head naming neither is refused. The trailing pieces are
  classified as well, by exact type against the approved transform set (`ExtractDay`,
  `ExtractMonth`, `ExtractYear`, `Length`, `Lower`, `TruncDate`, `TruncMonth`, `TruncYear`,
  `Upper`) and Django's own comparison, membership and null lookups, so a project transform or
  lookup registered on a built-in field (`code__jitter__gt`) is refused while an approved chain
  (`stamp__year__gt`) satisfies the guard. A fragment inside a sequence a lookup takes - the
  list `name__in` takes, the pair a `__range` takes - is refused, while a sequence of ordinary
  literals is as readable as one literal and satisfies the guard.
- Reversing a stable model default remains stable; `standard_ordering=False` changes direction
  and does not by itself disable the fallback.
- A consumer queryset's private `.order_by(...)` does not substitute for the public order
  precondition: an order only the resolver applied leaves a positive offset `order_required`.
- To-many `OrderSet` terms keep their `Min`/`Max` aggregate behavior. Pagination adds no
  `DISTINCT`, before or after the order.
- Ordering permission denial happens before any slice and retains its existing error.
- A non-queryset with `orderBy` fails rather than returning input-order rows.
- `None` from a nullable resolver stays `None` under limit/zero-offset, but it cannot satisfy
  `orderBy` or a nonzero-offset order precondition.
- The shared [visibility boundary][glossary-visibility-boundary] rejects a pre-sliced source
  before the hook and a sliced hook result afterward, under active and omitted arguments
  alike and in both execution colors, before any ordering runs; the list field adds no
  parallel slice-state classifier.
- A combined queryset is served as its primary-key set under every argument shape, omitted
  and all-null included; a combined shape that rewrite would change (`union(all=True)`, for
  one) fails closed with the `combined` defect.
- A custom `OrderSet.apply_*` result must SEAL to a lazy, unsliced, model-row-shaped,
  same-model, same-route plain queryset, a combinator served as its primary-key set. A sealable
  `QuerySet` SUBCLASS is accepted and normalized into that plain rebuild rather than rejected
  for its class. Same-route is a claim about the CONNECTION: the candidate's `_db` must equal
  the sealed source's (`None` included) and every hint value must be the same OBJECT, and the
  accepted rebuild is pinned to the effective alias resolved before the override ran, so a hint
  object mutated behind a preserved identity cannot move the read. Arbitrary custom code is
  trusted to preserve the sealed source predicates.
- An async-only iterable's iterator is closed when it exposes `aclose` and consumption does
  not reach natural exhaustion: the accepted exclusive stop (`offset + effective_limit`) is
  reached, iteration errors, or the source is otherwise stopped/rejected early. A naturally
  exhausted iterator is deliberately left alone. Cleanup failure precedence is as
  [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
  specifies for ordinary `Exception` failures. A control signal raised during cleanup -
  `asyncio.CancelledError` and the other non-`Exception` `BaseException` values - propagates
  rather than becoming a note, at either cleanup seam.
- `limit: 0` guarantees framework-owned work only: after the resolver returns, no source
  advancement and no row-fetch query occurs. It consumes no lazy sync or async iterable item
  and still invokes `aclose` when available. It is not a guarantee of zero database work - the
  resolver is still invoked and may query internally, and visibility hooks and permission
  checks still run - and the pre-execution document budget may reject the operation before
  this seam.
- A retained sync generator truncated by a client window stays SUSPENDED; its `finally` does
  not run. Early-exit cleanup is promised for async-only sources only (Decision 8).
- Rejected async-only sources are not advanced and are closed when possible; the domain
  error stays primary if cleanup fails.
- Async consumer results are awaited once. Sync-path awaitables and residual async-path
  awaitables are disposed and rejected before visibility/order/window handling.
- A nullable outer list keeps its consumer annotation; arguments do not alter nullability.
- The optimizer observes the final sliced queryset with its low/high marks intact.
- Multiple aliases with different arguments are independent resolver invocations; there is
  no connection-window merge or shared prefetch plan for root list fields.
- [Multi-database cooperation][glossary-multi-database] stays on the source queryset. Slice
  arithmetic neither evaluates nor recreates it from the target model's default manager.
- Existing [relation handling][glossary-relation-handling] keeps nested raw-list pagination
  out of this root-only surface; nested pages remain connections.
- A target whose class attribute answers with a fabricated same-origin object, a copy of the
  real definition, or a definition for a type the registry does not hold is rejected at the
  constructing line, not at schema build. The definition attribute is read from the real class
  namespaces without consulting the metaclass, and the registry lookup is by identity, so no
  target hook runs during the check.
- A second connection field over one target holding different metadata is rejected rather
  than served the warm cache's shape; `registry.unregister` and `registry.clear` evict the
  entry, so a fresh registration regenerates rather than collides.
- A relation target the registry holds WITHOUT a definition keeps the planner's
  class-predicate fallback. `DjangoType.__init_subclass__` registers type and definition in
  one atomic call, so no real `DjangoType` presents that shape; a bare class registered
  directly has no definition to read.
- A descendant task or worker thread that resumes after the ordering scope has exited
  publishes nothing and claims nothing, so its own active-term check takes the standalone
  double-normalization path - identical to applying outside any scope. A live descendant
  inside an open scope keeps the delegation and A/B/B rejection behavior.

## Test plan

### Live HTTP tier

The sync surface has its own module, `examples/fakeshop/test_query/test_list_field_api.py`,
beside [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library], the broad
library APPLICATION suite (FK and reverse-FK traversal, M2M, enum and nullable scalar
serialization, optimizer SQL shape, the `filter:` / `orderBy:` surfaces, GlobalID rejection,
and the row-preserving predicate oracle). A field factory's whole argument matrix lives in its
own module so the feature stays discoverable, and the sync module pairs with the async one,
`examples/fakeshop/test_query/test_list_field_async_api.py`. Both drive the apps'
already-registered library types and inline library models.

Both modules create `Branch`, `Shelf`, and library users inline with
`Model.objects.create(...)` / `create_user(...)`, following the library tier's explicit
repository exception; they do not import `apps.products.services` merely to satisfy the
products catalog/auth seed rule. A row that also creates products catalog models begins with
[`seed_data(N)`][glossary-seed-data] for that products half, as
[`test_resource_policy_api.py`][fakeshop-test-resource-policy] does.

The sync suite drives three shipped fields in
[`examples/fakeshop/apps/library/schema.py::Query`][fakeshop-library-schema]:
`all_library_branches_via_list_field`, `all_library_branches_via_list_field_nullable`, and
`all_library_branches_via_list_field_manager_resolver`. The first is the primary paging
surface and also anchors the `max_list_rows` acceptance rows in
[`test_resource_policy_api.py`][fakeshop-test-resource-policy]; the nullable and manager
variants carry the outer-nullability and manager-coercion roles with the same arguments.
Exceptional source shapes and custom converters live only in
[holder-mounted][glossary-probe-urlconf] test-local schemas, outside the shipped SDL.

Test names below are functions in `test_list_field_api.py` unless prefixed `test_async_`,
which are functions in `test_list_field_async_api.py`, or given with their module path.

1. `test_shipped_branches_introspection_arguments` shows `offset`, `limit`, and `orderBy` on
   `allLibraryBranchesViaListField`, with nullable `Int`, nullable `Int`, and the Branch order
   input respectively under the default schema naming config, and the nullable and
   manager-resolver siblings publishing the same arguments;
   `test_shipped_branches_introspection_return_types` pins that the annotation, not the
   arguments, decides each field's outer nullability.
2. `test_shipped_branches_staff_ordered_offset_limit`: under staff context,
   `orderBy: [{ name: ASC }, { id: ASC }], offset: 1, limit: 2` returns the second and third
   visible rows in that exact order, with one `library_branch` statement carrying
   `LIMIT 2 OFFSET 1`; `limit: 2` alone carries `LIMIT 2` and no `OFFSET`.
3. `test_shipped_branches_anonymous_visibility_before_offset`: an anonymous request orders by
   the unguarded `city`, then `id`, and proves a restricted Branch is removed by `get_queryset`
   before offset is counted; `city` avoids the example's staff-only `name` order gate while
   keeping visibility active.
4. `test_shipped_branches_order_by_alone`: `orderBy` alone arranges the whole policy-bounded
   list and exercises the order permission path under staff context.
5. `test_shipped_branches_nonzero_offset_without_order_rejected`: nonzero offset with no order
   returns `LIST_ARGUMENT_INVALID` and `reason=order_required`.
6. `test_shipped_branches_offset_bounds_rejected` and
   `test_shipped_branches_limit_bounds_rejected`: negative and over-ceiling values return the
   package error extensions (`code`, `reason`, `argument`, `value`, and `ceiling` for the
   over-ceiling arm).
7. String and bool variables, non-integral float variables, and float literals produce
   GraphQL `Int` coercion errors and no resolver SQL
   (`test_shipped_branches_a_limit_variable_outside_int_is_refused_before_sql`,
   `test_shipped_branches_an_offset_variable_outside_int_is_refused_before_sql`,
   `test_shipped_branches_a_float_limit_literal_is_refused_before_sql`,
   `test_shipped_branches_a_float_offset_literal_is_refused_before_sql`); an integral-valued
   float variable is coerced to an integer and executes with the resulting coordinate
   (`test_shipped_branches_an_integral_float_limit_variable_coerces_and_runs`).
8. `test_shipped_branches_limit_zero_short_circuits_sql`: `limit: 0` returns an empty list and
   performs no row-fetch query. `test_shipped_branches_offset_with_limit_zero_precondition`:
   `offset: 1, limit: 0` still obeys the order precondition, and with an active order it
   returns an empty list without fetching a row.
9. The cap matrix: `test_holder_trusted_widened_field` returns beyond policy when no client
   limit is supplied and still rejects an offset beyond policy;
   `test_holder_trusted_max_rows_rejects_a_limit_above_the_field_bound`,
   `test_holder_untrusted_max_rows_caps_an_omitted_limit`, and
   `test_holder_untrusted_max_rows_is_the_limit_ceiling` pin the field bound with and without
   the opt-in; `test_holder_trusted_max_rows_without_max_rows_keeps_the_policy_ceiling` pins
   the trusted flag with no `max_rows` as inert - a two-row policy serves two rows under
   `LIMIT 2`, and `limit: 3` is `over_ceiling` with `ceiling` 2.
10. Holder-mounted test-local fields named `branches_materialized`, `branches_nullable_none`,
    `branches_presliced`, `branches_trusted`, and `branches_combined` provide the exceptional
    source shapes without altering the shipped fakeshop SDL.
    `test_holder_materialized_and_nullable_none_fields` proves the materialized/`None` fields'
    limit/zero-offset behavior, any non-null `orderBy` (including `[]`) returning
    `queryset_required`, and nonzero offset returning `order_required`, with the nullable field
    preserving `None` under limit/zero offset.
    `test_holder_materialized_sequence_subclass_is_still_row_bounded` proves the row ceiling
    holds over a `list` SUBCLASS overriding `__getitem__`, with the unwindowed, windowed, and
    zero-limit requests each bounded.
11. `test_holder_presliced_configuration_error_under_pass_through` proves, under the
    [error-policy pass-through][glossary-production-error-policy] fixture, that both omitted
    and active arguments receive the shared visibility boundary's actionable
    `ConfigurationError` before the hook runs. Malformed public overrides are a matrix, one
    node per defect: `test_holder_branches_a_malformed_apply_sync_result_names_its_own_defect`
    covers an evaluated, an evaluated annotated (its fetch ran a selected `Count`; still the
    `evaluated` defect), materialized-list, `None`, projection, wrong-model, sliced,
    `union(all=True)`, awaitable, routing-rewritten-in-place, and malformed-deferred-filter
    `apply_sync` result, and
    `test_async_holder_branches_a_malformed_apply_async_result_names_its_own_defect` covers the
    same shapes on `apply_async` with a non-awaitable and a residual-awaitable result in place
    of the sync-only awaitable row; each asserts the exact typed `ConfigurationError`. The wrong-route overrides also run in the `FAKESHOP_SHARDED=1`
    [`test_multi_db.py`][fakeshop-test-multi-db] mount, where they reach a real `shard_b`
    alias.
12. On Branch's no-default-order model,
    `test_shipped_branches_an_ordering_with_no_terms_does_not_satisfy_an_offset` gives empty
    and all-null order input plus nonzero offset `order_required`, one node each;
    `test_shipped_branches_an_order_permission_denial_precedes_the_order_requirement` gives an
    anonymous staff-gated `name` order plus nonzero offset the order-permission denial first.
13. `test_shipped_branches_aggregate_order_no_distinct_in_sql`: under staff context, a to-many
    aggregate order through `shelves` plus limit/offset returns one row per Branch, and no
    captured statement carries `DISTINCT`. The single `LIMIT`/`OFFSET` pair is pinned by
    `test_shipped_branches_staff_ordered_offset_limit` and
    `test_shipped_branches_offset_alone_bounds`.
14. The wire-reachable precedence pairs from Decision 8:
    `test_shipped_branches_a_negative_offset_is_named_before_a_negative_limit`,
    `test_shipped_branches_a_materialized_source_is_named_before_the_order_requirement`
    (`queryset_required` before `order_required`), and
    `test_shipped_branches_a_presliced_source_is_named_before_the_ordering_runs`, whose async
    twin `test_async_a_sliced_hook_result_is_refused_before_the_ordering_runs` has
    `BranchType.get_queryset` return a sliced queryset under `orderBy` plus `offset: 1` and
    requires the sliced-source error with zero `BranchOrder.apply_async` calls.
15. `test_holder_branches_serve_a_combined_source_and_result_as_their_primary_key_sets`: a
    `union` source under a non-null argument is served as the rows it selects - the source
    seal rewrites it to its primary-key set, the visibility hook runs once over it, and the
    window applies - and an `OrderSet.apply_*` override returning a `union` is served the same
    way at the post-sidecar seal;
    `test_holder_branches_an_argument_windows_the_combined_source_after_visibility` pins the
    argument path's window after visibility.
16. Converter naming. `test_holder_naming_converters` proves, under
    `strawberry_config(auto_camel_case=False)` and an upper-casing custom `NameConverter`, that
    introspection publishes all three parameters in the converter's spelling and that an
    `offset` rejection names the converted argument; under a counting converter a rejected
    request costs no more `from_argument` calls than a successful one.
    `test_holder_naming_converters_name_the_order_argument` pins the three `order_by` wire-name
    sites under the upper-casing converter: `ORDERBY: []` over the materialized field is
    `queryset_required` naming `ORDERBY`, and `OFFSET: 1` over the materialized field and over
    the queryset field is `order_required` whose message names `ORDERBY`. The async colour
    carries `test_async_a_rejection_names_the_argument_in_the_schema_spelling` and
    `test_async_rejection_reports_the_published_name_without_extra_converter_calls`.
17. Both verdicts of the model-default predicate are live.
    `test_holder_model_default_ordering_verdicts` mounts `terms_default_ordered` over the
    glossary app's `GlossaryTermType`, whose model declares a stable non-random
    `Meta.ordering` (`Branch` declares none): nonzero offset succeeds with no `orderBy` and with
    no injected pk term, while the sibling `terms_cleared_ordering`, whose resolver calls
    `.order_by()`, flips the identical request to `order_required`.
    `test_holder_offset_refuses_an_order_only_the_resolver_applied` gives a resolver returning
    `Branch.objects.order_by("name")` plus `offset: 1` `order_required` naming `offset`, with no
    row SQL. The remaining live states: a random model default
    (`test_shipped_branches_offset_rejects_a_random_model_default`,
    `test_shipped_branches_offset_rejects_a_random_expression_model_default`,
    `test_async_offset_rejects_a_random_model_default`), `.reverse()` on a stable default
    (`test_holder_reversed_model_default_ordering_still_pages`), and an empty source with and
    without a model ordering (`test_holder_empty_model_ordered_queryset_still_pages`,
    `test_holder_empty_unordered_queryset_still_requires_order`).
18. The capability rule from both sides: `test_holder_target_without_orderset_or_model_ordering`
    mounts `MembershipCardType`, which declares neither `Meta.orderset_class` nor a model
    default ordering; it publishes `offset` and `limit` and NO `orderBy`, and every positive
    offset returns `order_required` with no `orderBy` named in the message. Its counterpart is
    row 17's `terms_default_ordered`, whose target publishes no `orderBy` either yet accepts a
    positive offset from model `Meta.ordering` alone. A published `offset` is a runtime
    precondition, not a capability claim.
19. `test_shipped_branches_offset_alone_bounds`: offset alone, with `limit` omitted, returns
    `[offset:offset + effective_ceiling]`; the captured SQL keeps the policy `LIMIT` and adds
    the `OFFSET` (`LIMIT 100 OFFSET 2` under the default policy and offset 2).
    `tests/test_resource_policy.py::test_bounded_rows_window_parameter_matrix` and
    `::test_bounded_rows_slices_with_offset_and_requested_limit` pin the same arithmetic at the
    bounding seam.
20. The omitted/all-null branch is asserted against a LEGACY REFERENCE FIELD mounted beside
    the current one, not against the absence of an argument error and not against a second
    run of the current implementation. The test-only field's resolver composes the no-argument
    pipeline from public primitives alone (the source queryset, `apply_type_visibility_sync`,
    one `bounded_rows` call with no client window) and records its final queryset's
    `str(query)`, `low_mark`, and `high_mark`; the current field's final marks are recorded at
    its one `_windowed_rows` call. Where the reference publishes the SAME GraphQL field name -
    `test_branches_a_null_spelling_reproduces_the_legacy_reference_bytes` (omitted and
    all-null against the legacy omitted response) and
    `test_holder_branches_a_combined_legacy_spelling_matches_the_reference` - one request
    envelope reaches both and the rows assert equality of the RAW `HttpResponse.content` bytes,
    the captured `library_branch` SQL, the marks, and the `get_queryset` call count.
    `test_branches_the_shipped_field_matches_the_legacy_reference` holds the shipped field,
    whose published name differs from the reference's, to the same oracle through its parsed
    rows, SQL, marks, and hook count. "Not `LIST_ARGUMENT_INVALID`" is not a sufficient oracle
    here, because a combined Branch queryset also meets `BranchType.get_queryset` filtering
    before pagination and can legitimately produce either data or a pre-existing error.
21. `test_shipped_branches_independent_aliases`: two aliases of the same field in one
    document, with different `offset` / `limit` pairs, return independent pages.
22. `test_holder_nullability_propagation_over_none_source`: a nullable and a non-null outer
    list over the same `None`-returning holder field; a limit-only request hands `None` to
    GraphQL completion unchanged, so the nullable list answers `null` and the non-null one the
    masked `Cannot return null for non-nullable field` error (as with no arguments); a rejected
    argument raises its typed error on both.
23. `test_holder_orderset_override_returning_queryset_subclass`: a conforming test-local
    `OrderSet` override returning a `QuerySet` SUBCLASS derived from its sealed input succeeds
    and returns the correct ordered page.
24. Under `FAKESHOP_SHARDED=1`, `test_multi_db.py` proves the same-route invariant on its
    harder half: `test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db` rejects a
    candidate whose `_db` is `None` on both sides but whose `_hints` differ, beside the explicit
    `.using("default")` versus `.using("shard_b")` mismatch
    (`test_post_orderset_routing_mismatch_rejected_on_sharded_db`).
    `test_post_orderset_in_place_routing_mutation_rejected_on_sharded_db` and
    `test_post_orderset_equal_but_distinct_hint_token_rejected_under_identity_router` capture
    SQL on both aliases and assert no `library_branch` statement runs. The accepted half is
    `test_post_orderset_mutable_hint_cannot_reroute_the_completed_read`: an override that
    mutates state INSIDE a hint object it preserves by identity still completes on the source's
    alias. `test_async_mutable_hint_cannot_reroute_the_completed_read` carries the accepted half
    on the `apply_async` seam in the default suite, with the hint mutated to name an alias the
    project does not configure.
25. The offset guard's selected-order rule, pinned live against the shipped
    `allLibraryBranchesViaListField` field with a public `apply_sync` / `apply_async` override
    in place. The rejection half: a model declaring `Meta.ordering = ("?",)` under an override
    that returns its input unchanged is refused for a positive offset even though `orderBy`
    input is active, with no row SQL. The acceptance half:
    `test_shipped_branches_offset_accepts_extra_ordering_over_a_dormant_random_order` serves
    `queryset.order_by("?").extra(order_by=["id"])` with the captured SQL carrying the id order
    and the raised low mark, and
    `test_shipped_branches_offset_accepts_an_explicit_order_over_a_dormant_random_model_default`
    serves `orderBy: [{ city: ASC }, { id: ASC }]` with `offset: 1, limit: 1` over
    `Branch._meta.ordering = ("?",)` in one statement carrying `OFFSET 1` and no random
    function. The controls are `test_shipped_branches_offset_accepts_a_stable_model_default`
    and `test_shipped_branches_offset_rejects_extra_random_ordering_over_a_stable_order`. The
    async colour carries `test_async_offset_rejects_a_random_model_default`,
    `test_async_offset_accepts_extra_ordering_over_a_dormant_random_order`, and
    `test_async_offset_rejects_extra_random_ordering_over_a_stable_order` through the same
    guard. Accepting rows carry the SQL witness, not just the returned row: three rows put the
    expected name at the requested offset often enough that a re-shuffled result set can
    return it by chance. The async colour cannot read the sync suite's
    `CaptureQueriesContext`, which sits on the sync side of the
    [async SQL-capture boundary][glossary-async-sql-capture-boundary]; it records statements at
    `SQLCompiler.execute_sql`, where the statement is built in whichever thread builds it. The
    must-not half of that witness reads the vendor-independent PREFIX `RAND` of the random
    function, because Django spells it `RAND()` on SQLite and MySQL and `RANDOM()` on
    PostgreSQL.

    Resolution and readability, on the same field and override surface: an annotation alias
    over `Random()` (`test_shipped_branches_offset_rejects_an_annotated_random_order`), an `F`
    naming that alias (`..._rejects_an_f_reference_to_a_random_annotation`), the alias under a
    leading `-` or a lookup suffix (`..._rejects_a_desc_or_lookup_random_alias`), an `extra`
    select alias and the dotted `extra` form (`..._rejects_an_extra_select_ordering`,
    `..._rejects_a_dotted_extra_order`), a `Random()` nested in a composition
    (`..._rejects_a_composed_random_order`), a `RawSQL` fragment
    (`..._rejects_a_raw_sql_order`), a bare `Func` naming the same database function
    (`..._rejects_a_bare_database_function_order`), a `Subquery`
    (`..._rejects_a_subquery_order`), and a fragment boxed inside a predicate's `__in` sequence
    (`..._rejects_raw_sql_inside_a_predicate_container`) are each refused with no row SQL. The
    controls - an alias naming a deterministic expression
    (`..._accepts_a_stable_annotated_order`), a conditional order over columns and literals
    (`..._accepts_a_conditional_order`), an `__in` sequence of literals
    (`..._accepts_a_container_predicate_of_readable_leaves`), and `Count("*")`
    (`..._accepts_a_row_count_order`) - are each served with the raised low mark and no random
    function. The async colour carries the alias shape, the `extra` select, and the raw SQL leaf
    (`test_async_offset_rejects_an_annotated_random_order`,
    `test_async_offset_rejects_an_extra_select_ordering`,
    `test_async_offset_rejects_a_raw_sql_order`).

    Relation expansion, on a holder schema over a type whose model owns a foreign key, in both
    colours, with both `Meta.ordering` values supplied for the request: a parent ordering by the
    relation under a related model ordering by `Random()` is refused with no row SQL
    (`test_holder_offset_rejects_a_relation_default_that_expands_to_a_random_order`), while the
    same relation term under a related model ordering by a column
    (`test_holder_offset_accepts_a_relation_default_that_expands_to_a_stable_order`) and the
    foreign key's own `attname` under a related model ordering at random
    (`test_holder_offset_accepts_a_relation_attname_over_a_random_related_default`) are each
    served with the raised low mark and no random function. Django compiles no nested `"?"`
    (it resolves as a column named `?` and raises), so the random related default is written as
    the expression. The three expression spellings of the same relation - `F("branch").asc()`,
    `OrderBy(F("branch"))`, and a bare `F("branch")` - are each SERVED under the same randomly
    ordered related model (`test_holder_offset_accepts_an_expression_reference_to_a_relation`).
    The to-many relations: a shelf ordering through its books to their genres, or through its
    branch to the branch's generic tags, under a target ordering by `Random()` is refused with
    no row SQL (`test_holder_offset_rejects_a_to_many_relation_default_that_expands_to_an_unstable_order`),
    and the same names under a target ordering by a column are served
    (`test_holder_offset_accepts_a_to_many_relation_default_that_expands_to_a_stable_order`);
    the sync view adds two many-to-many walks that repeat a join Django rejects - a genre
    ordering leading back to the shelf, and a branch ordering repeating the branch's own walk -
    refused with no row SQL, and the genre's `pk` under a random genre default, served. Every
    patched ordering passes Django's system check, since a bare many-to-many or generic name in
    `Meta.ordering` is `models.E015`. Each relation row has its `test_async_offset_` twin.

    The predicate's left-hand side, on the same holder: a `Case` picking its result by
    `coin__gt` over a source carrying `alias(coin=Random())` - and, on the sync view, over the
    `annotate` spelling of the same alias - is refused with no row SQL
    (`test_holder_offset_rejects_a_conditional_order_over_a_random_predicate`,
    `test_async_offset_rejects_a_conditional_order_over_a_random_predicate`), while the same
    predicate over `alias(coin=F("code"))`
    (`test_holder_offset_accepts_a_conditional_order_over_a_column_alias_predicate` and its
    async twin) and one naming `code__gt` with no alias
    (`test_holder_offset_accepts_a_conditional_order_over_a_plain_column_predicate`) are served
    with the raised low mark and no random function. A random alias compared one predicate
    deeper is refused while the same nesting over columns is served
    (`test_holder_offset_reads_a_predicate_nested_inside_a_predicate`), and a reference naming
    an `extra` select alias is refused
    (`test_holder_offset_refuses_a_reference_naming_an_extra_select_alias`).

    The approved-form boundary, through `Meta.ordering` alone:
    `test_holder_offset_reads_an_expression_by_its_approved_form` refuses a project expression
    class emitting its own SQL around a readable column and, on the sync view, a SUBCLASS of an
    approved function, each beside `Lower("code")` served;
    `test_holder_offset_rejects_a_predicate_chain_of_project_sql` refuses a project transform
    and, on the sync view, a project lookup registered on a built-in field, beside
    `stamp__year__gt` (`test_holder_offset_accepts_a_predicate_chain_of_approved_forms`) and a
    chain ending in a transform (`test_holder_offset_accepts_a_predicate_chain_ending_in_a_transform`)
    served. The reference forms: `test_holder_offset_reads_a_term_by_the_form_it_resolves_into`
    refuses a subclass of `F` resolving to the random function and a `str` subclass carrying
    `resolve_expression`, beside `F("code")` served, and
    `test_holder_offset_reads_a_conditional_predicate_by_its_exact_type` refuses a subclass of
    `Q` inside the approved `Case` / `When` composition beside a plain `Q` served. The async
    colour carries each of these three with its `test_async_offset_` twin and the project
    transform row.
26. `test_async_deadline_rejection_closes_the_source_it_never_advanced`: a live async request
    whose deadline expires after its resolver has obtained an async-only source closes that
    source exactly once and advances it zero times, for the default window and for `limit: 0`
    alike, with the complete `execution_deadline_seconds` extensions on the rejection. The
    expiry is handed over by an `async def` resolver that records its iterator, awaits, and only
    then ends the budget, so the rejected request has crossed the async handoff, and the row
    asserts the resolver reached that await. The witness is the externally counted iterator,
    never an async generator's body `finally`.
27. The request's budget is not reachable from the request's own context.
    `test_async_a_resolver_cannot_widen_the_row_bound_through_the_context` replaces
    `DST_RESOURCE_POLICY` with a wider policy after a real `await` and requires the schema's
    row count; `test_async_a_resolver_cannot_buy_more_wall_clock_through_the_context` pushes
    `DST_RESOURCE_DEADLINE` into the far future after sleeping past its budget and requires the
    `execution_deadline_seconds` rejection, under a far-future instant and a narrowing `float`
    subclass alike. Nor is the budget reachable from any policy OBJECT the request can name:
    `test_a_resolver_cannot_widen_the_row_bound_by_writing_a_policy_it_can_reach` and its
    `test_async_` twin have a sibling field write `max_list_rows` on each of
    `policy_from_info`'s answer, `info.schema.resource_policy`, and the `dst_resource_policy`
    mirror, and require the bounded field to answer with the operation's ceiling;
    `test_a_policy_a_resolver_widened_does_not_outlive_its_own_request` requires the request
    after it to answer with the same ceiling.

Every test-local sync/async schema mount uses the module-level current-schema holder under
`override_settings(ROOT_URLCONF=...)`, resets that holder in `finally`, and uses the
repository's registry/finalization cleanup fixtures under the
[schema reload discipline][glossary-schema-reload-discipline]. Test-local fields are declared
over already-registered app `DjangoType`s; a throwaway `DjangoType` would mutate the registry
and trip the acceptance conftest's registration identity guard. The exceptional fields and
custom converters never leak into the shipped app schema or a later test.

Live-first placement is fixed per branch. The package tier may assert internal identity and
exact call counts, but the FINAL verdict of each of the following is reachable live and is
pinned live: every public `ListArgumentError.reason`; custom name-converter spelling; both
verdicts of the model-default order predicate; order permission denial preceding offset
rejection; combined-source and combined-result service as primary-key sets; post-order
evaluated / projection / combined / wrong-model result classification; and optimizer-on and
optimizer-off async queryset completion.

The implementation reads private or semi-private behavior in three dependencies - Django query
state (`default_ordering`, `order_by`, `extra_order_by`, `group_by`, `combinator`,
`_result_cache`, `_hints`), Strawberry argument definitions and name conversion, and
graphql-core list completion. The CI matrix, not a local run, is the contract for those reads:
every push and PR runs the whole suite on the exact-floor cell and the latest cell, and manual
dispatch runs it across the full supported matrix.

The resource-policy mount in [`test_resource_policy_api.py`][fakeshop-test-resource-policy]
pins that a legal client limit narrows the field and the first over-ceiling value rejects
(`test_list_argument_limit_at_and_over_narrowed_policy_ceiling`), that offset consults the
request-specific policy rather than
[`django_strawberry_framework/resource_policy.py::DEFAULT_RESOURCE_POLICY`][resource-policy]
(`test_list_argument_offset_at_and_over_narrowed_policy_ceiling`), that the pre-execution
collection-cost charge stays the raw-list policy ceiling when the operation supplies a smaller
`limit` (`test_list_argument_smaller_limit_serializes_subset_and_charges_full_collection_cost`),
and that rejections and `limit: 0` perform no SQL
(`test_list_argument_rejections_and_limit_zero_perform_no_sql`).

`examples/fakeshop/test_query/test_list_field_async_api.py` mounts a test-local schema through
`AsyncDjangoGraphQLView` and posts through the package's own `AsyncTestClient`, following the
fakeshop async-test pattern in
[`examples/fakeshop/test_query/test_relations_async_api.py`][fakeshop-test-relations-async]:
the shipped fakeshop URLconf mounts the sync view, so the module supplies its own async mount
over the apps' already-registered types and declares only test-local fields. Every case
carries `@pytest.mark.django_db(transaction=True)`, which the tier's async suites require for
ORM access inside the event loop. The shared
[`examples/fakeshop/graphql_client.py`][fakeshop-graphql-client] helpers are synchronous by
construction ([`django_strawberry_framework.testing.TestClient`][glossary-testclient] over
`django.test.Client`) and expose no async post, so the module drives `AsyncTestClient`
directly. No case sets `DJANGO_ALLOW_ASYNC_UNSAFE`, and
neither does `tests/test_relay_connection.py`. The module proves the default resolver
(`test_async_queryset_completion_default_resolver`), a CONFORMING LAZY sync consumer returning
`Manager` / `QuerySet` - one that does not evaluate, since the adapter cannot make an
evaluating sync resolver safe (Decision 5) - and an `async def` consumer returning `QuerySet`
(`test_async_queryset_completion_sync_manager_resolver`,
`test_async_queryset_completion_sync_queryset_resolver`,
`test_async_queryset_completion_async_def_queryset_resolver`), an awaited `get_queryset`
(`test_async_get_queryset_is_awaited`), visibility -> order -> window
(`test_async_pipeline_parity`), optimizer-on and optimizer-off completion of the same rows
(`test_async_queryset_completion_windows_the_same_rows`), nullable behavior
(`test_async_nullable_none_resolver_returns_null`), limit-only windowing
(`test_async_limit_alone_windows_without_order_by`), async-generator and async-only iterable
bounds (`test_async_http_partial_async_generator_resolver_is_bounded`,
`test_async_generator_cleanup_and_finally_witness`,
`test_async_iterator_aclose_witness_on_limit_zero_and_rejection`), and serialized
source-shape/order errors. Positive offset over an async-only source appears here only as the
`order_required` rejection Decision 8 requires; its accepted arithmetic is pinned against the
bounding helper in [`tests/test_resource_policy.py`][test-resource-policy]
(`test_bounded_rows_async_positive_offset_arithmetic`).

Finalization assertions respect Python's async-generator semantics. `aclose()` on an async
generator that has never been advanced does NOT enter its body: neither its setup nor its
`finally` block runs, so a body-level `finally` witness after zero advances is unobservable,
and advancing the generator to make it observable would destroy the zero-consumption guarantee
those same rows prove. The tests therefore separate two facts. That `aclose()` WAS INVOKED is
proven with a custom async iterator whose own `aclose()` increments a counter, asserted beside
zero `__anext__` calls (`test_async_iterator_aclose_witness_on_limit_zero_and_rejection`).
That a generator BODY FINALIZED is proven with a real async generator only after at least one
item has been requested (`test_async_generator_cleanup_and_finally_witness`), and natural
exhaustion leaves `aclose` uncalled
(`test_async_generator_natural_exhaustion_does_not_call_aclose`).

Cleanup diagnostics stay out of the HTTP assertions. The production GraphQL JSON error envelope
does not serialize `BaseException.__notes__`, so exact note content and precedence are
package-tier subjects; live HTTP asserts the public `extensions` payload and that a cleanup
failure did not displace the primary domain error
(`test_async_a_failing_aclose_does_not_displace_the_argument_rejection`). Package-level
adapter inspection pins the optimized inner queryset's SQL/low/high marks without pretending a
[thread-local async DB capture][glossary-async-sql-capture-boundary] observes worker-thread
SQL.

### Package tier

[`tests/test_list_field.py`][test-list-field] covers construction and exact mechanics a real
sync or async HTTP request cannot isolate:

- generated callable signatures with and without `Meta.orderset_class`
  (`test_list_field_signature_without_orderset`, `test_list_field_signature_with_orderset`);
  importing `django_strawberry_framework` alone does not import the orders subpackage
  (`tests/base/test_init.py::test_orders_submodule_not_imported_at_package_root`);
- direct-call non-integer, bool, and `int`-subclass rejection, including a hostile subclass
  whose comparison and formatting hooks never fire, and an integer too large for CPython to
  stringify (`test_normalize_list_arguments_rejects_int_subclasses_before_their_hooks_can_run`,
  `test_normalize_list_arguments_renders_an_unprintable_large_int_without_raising`,
  `test_normalize_list_arguments_rejects_values_graphql_int_never_supplies`,
  `test_list_field_direct_call_safe_non_integer_rendering`);
- `ListArgumentError.__reduce__` preserving constructor arguments, extensions, and instance
  state across a pickle round trip (`test_list_field_error_pickle_round_trip`), and an unknown
  reason refused (`test_list_argument_error_rejects_an_unknown_reason_and_renders_bools`);
- direct-call schema-name fallback and argument-definition lookup
  (`test_list_field_direct_call_schema_name_fallback_and_definition_lookup`,
  `test_list_field_wire_name_resolution_falls_back_without_a_usable_definition`);
- error-lazy wire-name resolution: neither a valid normalization nor a rejection invokes the
  schema's `NameConverter`
  (`test_resolve_argument_wire_name_never_runs_the_schema_name_converter`), and malformed
  published-argument metadata is a `ConfigurationError`
  (`tests/utils/test_typing.py::test_published_argument_reads_the_executable_schemas_argument_map`); the live converter-counting
  rows are row 16's counting converter and
  `test_async_rejection_reports_the_published_name_without_extra_converter_calls`;
- a sync resolver returning an `asyncio.Future` has it cancelled
  (`test_djangolistfield_sync_resolver_returning_future_cancels_it`); awaitable disposal and
  the one-await rule are live rows
  (`test_async_http_rejects_a_sync_resolver_that_returns_a_coroutine`,
  `test_async_http_rejects_a_sync_resolver_that_returns_a_custom_awaitable`,
  `test_async_http_rejects_an_async_resolver_that_resolves_to_another_awaitable`);
- exact rejected-async-iterator no-advance and optional-`aclose` counts and
  primary-versus-cleanup exception notes, whose exact `__notes__` content and precedence live
  only here (`test_list_field_rejected_async_iterator_cleanup_and_notes`,
  `test_list_field_rejected_async_iterator_is_closed_when_building_the_rejection_fails`,
  `test_async_iterable_early_cleanup_hostile_aclose_lookup_notes`);
- async-only queryset adapter protocol - `__aiter__` present, `__iter__` absent
  (`test_async_completion_adapter_semantics`) - and the
  `DjangoOptimizerExtension._optimize` unwrap/rewrap identity and inner low/high marks,
  including the rewrap on that method's two early returns, an already-evaluated inner
  queryset and an unresolvable return type
  (`test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns`);
- `check_deadline` invoked in pre-fetch position for argument-bearing requests
  (`test_list_field_deadline_check_position`);
- the model-default predicate's two states no live mount constructs as distinct verdicts:
  grouping suppresses the default
  (`test_is_model_default_ordering_active_rejects_a_grouped_queryset`), and
  `default_ordering` must be exactly `True`
  (`test_is_model_default_ordering_active_exact_bool_identity`);
- the term classifier's boundary by type
  (`test_order_term_classifier_admits_only_named_forms`: an approved function accepted and its
  subclass refused, an approved aggregate and a row count accepted, an unlisted aggregate and a
  `Window` refused, `F` and `Q` accepted and their subclasses refused, a name that resolves
  refused), a term that is no expression at all and an `F` whose name is not a `str`
  (`test_order_term_classifier_rejects_a_non_expression_term`,
  `test_order_term_classifier_refuses_a_reference_with_a_non_str_name`), and the relation and
  reference forms that need no second wire spelling: a relation ordering cycle refused
  (`test_order_term_classifier_refuses_a_relation_ordering_cycle`), a join repeated by sibling
  items of one related ordering refused while a column beside it is served
  (`test_order_term_classifier_refuses_a_join_repeated_by_sibling_terms`), a path piece that
  is not a field refused (`test_order_term_classifier_refuses_a_piece_that_is_not_a_field`), a
  reverse relation read through to its target's default
  (`test_order_term_classifier_reads_a_reverse_relation_target_ordering`), a chain of two
  relations whose far end decides
  (`test_order_term_classifier_follows_a_chain_of_relation_defaults`), an `F` naming a random
  annotation refused (`test_order_reference_classifier_reads_the_annotation_a_reference_names`),
  a reference lifted out of an expansion read as a column
  (`test_order_reference_classifier_keeps_an_expanded_reference_a_column_order`), a predicate
  head naming neither an annotation nor a field refused
  (`test_order_predicate_classifier_refuses_an_unresolvable_reference`), and a transform chain
  whose verdict follows the annotation it names, in both directions
  (`test_order_predicate_classifier_reads_the_annotation_under_a_transform_chain`);
- the normalized record's independent fields - `any_argument_supplied` selecting argument mode,
  the window fields, `order_by_supplied` driving `queryset_required` for an empty list - and
  its immutability and the policy-free omitted path (`test_list_field_record_independence`,
  `test_list_arguments_immutability`, `test_omitted_list_arguments_do_not_resolve_policy`,
  `test_normalize_list_arguments_treats_unset_as_omitted`);
- seal-axis mechanics: a sealable `QuerySet` SUBCLASS post-apply result normalized into a
  plain queryset and routing intent enforced
  (`test_list_field_seal_axis_subclass_and_routing_intent`), and routing intent extracted with
  no consumer dispatch (`test_list_field_post_orderset_validator_zero_consumer_dispatch`);
- a retained sync generator truncated by a client window still suspended and resumable
  afterward - the sync cleanup contract Decision 8 declines
  (`test_list_field_declined_sync_cleanup_generator_suspended`, beside
  `tests/test_resource_policy.py::test_bounded_rows_declined_sync_cleanup_resumable`);
- the target guard: a fabricated same-origin definition, a copy of the real definition, a
  target the registry has never seen, and a definition registered for another class are each
  rejected at construction, the accepted object IS `registry.get_definition(target)`, and the
  registry lookup never hashes the target
  (`test_djangolistfield_rejects_a_fabricated_same_origin_definition`,
  `test_djangolistfield_rejects_a_copy_of_the_real_definition`,
  `test_djangolistfield_rejects_a_target_the_registry_has_never_seen`,
  `test_djangolistfield_rejects_a_definition_registered_for_another_class`,
  `test_djangolistfield_accepts_and_captures_the_registrys_exact_object`,
  `test_djangolistfield_registry_lookup_never_hashes_the_target`);
- the executor read: a list field completes synchronously outside an event loop and
  asynchronously inside one, and refuses a synchronous operation inside an event loop
  (`test_a_list_field_completes_synchronously_outside_an_event_loop`,
  `test_a_list_field_completes_asynchronously_inside_an_event_loop`,
  `test_a_list_field_refuses_a_synchronous_operation_inside_an_event_loop`), with the live
  nested-operation row `test_async_a_nested_synchronous_operation_refuses_a_list_field`.

[`tests/utils/test_querysets.py`][test-querysets] owns the shared seal mechanics the list field
routes through:

- sliced hook-result rejection
  (`test_sliced_hook_result_fails_closed_with_typed_error`); the live pre-sliced field and its
  async twin (rows 11 and 14) prove this list surface routes through that shared boundary;
- the post-`OrderSet` validator arms, one test each: valid, non-queryset, `None`, wrong model,
  evaluated, sliced, a served combined result and a refused lost property, a combined result
  ordered through a hiding type, projection, `_db` and `_hints` routing mismatch, a hint with a
  hostile `__eq__` / `__repr__`, `None` versus empty hints, and zero consumer dispatch on
  `__getattribute__` (`test_validate_post_orderset_result_*`); the evaluated and combined arms
  assert the message text, not only the exception class;
- routing intent as a frozen RECORD - `_db`, copied `_hints`, and the effective alias resolved
  through `ConnectionRouter` - taken before the public apply call: the accepted result is
  pinned to the alias resolved before a hint could be mutated
  (`test_routing_intent_pins_the_alias_resolved_before_a_hint_could_be_mutated`), a
  write-marked source resolves through `db_for_write`
  (`test_routing_intent_resolves_a_write_marked_source_through_the_write_router`), a router
  that raises propagates its own error (`test_routing_intent_propagates_the_router_error`), and
  a non-string router answer is a typed `ConfigurationError`
  (`test_routing_intent_fails_closed_on_a_non_string_router_answer`);
- deferred-filter state: a subclass carrying a well-formed pending `_deferred_filter` seals
  with that predicate baked into the compiled SQL
  (`test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked`), and a
  deferred-filter state Django never writes fails closed as `untrusted` on a subclass and on an
  exact queryset alike - a wrong-arity tuple, a `negate` that is not an exact `bool` (refused
  without reaching its own `__bool__`), a non-`dict` `kwargs`, and a value that is neither
  inert nor genuine Django (`test_a_subclass_deferred_filter_state_django_never_writes_fails_closed`,
  `test_a_deferred_filter_negate_that_is_not_a_bool_fails_closed_on_an_exact_queryset`,
  `test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`,
  `test_deferred_filter_wrong_arity_tuple_fails_closed`,
  `test_bake_deferred_non_dict_kwargs_fails_closed`,
  `test_deferred_value_arbitrary_object_fails_closed`); the malformed case is also live on both
  public overrides (row 11);
- the sealer's own admission: a value whose `__class__` raises and one whose `__class__` names
  `QuerySet` are both the typed `type` defect rather than a raw exception or an admission
  (`test_a_value_whose_class_property_raises_is_a_typed_seal_defect`,
  `test_a_value_that_only_claims_to_be_a_queryset_is_a_typed_seal_defect`).

[`tests/test_resource_policy.py`][test-resource-policy] pins the generic sequence,
non-subscriptable iterable, and async-iterable behavior at the one raw-list seam: sequence
slicing, the non-subscriptable-iterable bound, trusted widening, `None` preservation on both
colors, `aclose` after the effective prefix, an exhausted iterator that is left untruncated,
and the cleanup-failure precedence arms. It also pins the window arms. An accepted client
`limit: 0` is the only spelling that produces a zero-length window, because
[`django_strawberry_framework/resource_policy.py::validate_collection_bound`][resource-policy]
and `ResourcePolicy` construction both reject a bound below `1`, so those rows pin
zero-limit/no-consumption on sequence, non-subscriptable, and async-only sources - no
`islice`, no `__next__`, no `__anext__` - with the optional `aclose` still invoked on the
async source (`test_bounded_rows_zero_window_does_not_advance_generator`,
`test_bounded_rows_async_zero_window_closes_without_next`), plus nonzero-offset window
arithmetic at the same seam (`test_bounded_rows_window_parameter_matrix`,
`test_bounded_rows_slices_with_offset_and_requested_limit`,
`test_bounded_rows_slices_unsliceable_iterable_with_offset_and_requested_limit`,
`test_bounded_rows_async_slices_with_offset_and_requested_limit`,
`test_bounded_rows_async_positive_offset_arithmetic`). Positive-offset async behavior belongs
here: the public field refuses it, the helper supports it. The same module pins:

- the cap arithmetic: `effective_bound` takes the tighter of the policy and field bounds unless
  trusted, and only the literal `True` widens
  (`test_effective_bound_takes_the_tighter_of_the_two_unless_trusted`,
  `test_only_the_literal_true_widens_a_declared_bound_past_the_request_policy`,
  `test_a_falsy_non_bool_opt_in_also_narrows`);
- the exported raw-list bound taking no client window, parametrized over both colors and both
  coordinates: passing `offset` or `requested_limit` is a `TypeError` from the signature, with
  the no-window call beside it still returning the policy-bounded rows
  (`test_the_exported_raw_list_bound_takes_no_client_window`);
- the deadline at the bounding seam: a directly expired deadline closes a source never
  advanced (`test_bounded_rows_async_closes_a_source_the_deadline_rejects_before_any_row`),
  and a failing close leaves the resource error primary with the cleanup failure attached as a
  note (`test_bounded_rows_async_keeps_the_deadline_primary_when_the_close_fails`), beside
  the natural-exhaustion control (`test_bounded_rows_async_exhausted_iterator_without_truncation`);
- cancellation during async cleanup staying observable: a task cancelled while `aclose` is
  suspended, after the source has already raised, ends cancelled with nothing written onto the
  source error (`test_bounded_rows_async_lets_a_cancellation_during_cleanup_reach_the_task`),
  and an acquisition interrupted by cancellation at the pre-iteration seam propagates
  instead of annotating the rejection
  (`test_cleanup_rejected_async_iterable_lets_a_cancelled_acquisition_through`); an ordinary
  `Exception` raised by cleanup is still demoted to a note
  (`test_bounded_rows_async_preserves_source_errors_when_cleanup_fails`);
- the budget arms a request cannot express: a cleared deadline key
  (`test_deleting_the_deadline_key_outright_does_not_disarm_the_budget`,
  `test_an_armed_deadline_cannot_be_widened_or_cleared_from_the_context`), `nan` and infinite
  deadlines (`test_a_non_finite_deadline_with_no_budget_armed_fails_closed`), the narrowing
  positive control (`test_a_resolver_may_shorten_its_own_request`), a nested budget restoring
  the outer one on exit (`test_ending_a_budget_restores_the_one_it_was_opened_inside`), the
  bound read from inside a `sync_to_async` worker thread
  (`test_the_armed_budget_reaches_a_sync_to_async_worker_thread`), and a `float` subclass
  written as an instant already past
  (`test_a_numeric_subclass_written_deadline_cannot_outlive_an_expired_budget`);
- exact built-in policy bounds: a typed `ConfigurationError` for an `int` subclass whose
  comparison is BENIGN (`test_a_benign_comparison_int_subclass_is_still_refused_a_policy_field`),
  a hostile subclass reaching `narrowed()`
  (`test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected`), and a `float` subclass
  whose reflected `__radd__` would otherwise turn the derived absolute deadline into `nan`
  (`test_a_float_subclass_cannot_reach_the_derived_deadline_arithmetic`); an upload whose
  reported `size` is not an exact non-negative `int` is refused rather than charged as zero
  (`test_an_upload_that_cannot_report_its_size_is_rejected`, beside
  `test_a_measurable_upload_is_charged_its_bytes`), and a `first` / `last` page bound supplied
  as an `int` subclass narrows nothing
  (`test_a_page_size_variable_outside_the_integers_narrows_nothing`).

[`tests/orders/test_sets.py`][test-orders-sets] pins that the active-term helper shares the
canonical normalization/flat-order rules, reports false for empty/all-null input, and does not
replace either public apply method (`test_input_has_active_terms_contract`,
`test_input_has_active_terms_public_apply_override_independence`), the documented double
normalization of pure/deterministic `_normalize_input` overrides
(`test_input_has_active_terms_independent_query_and_double_normalization`), and ledger closure:
a descendant delayed past scope exit through `asyncio.create_task` and through
`contextvars.copy_context()` plus a worker thread finds the closed ledger empty, claims
nothing, and leaves its term check on the standalone path
(`test_a_task_that_outlives_the_scope_cannot_reopen_the_closed_ledger`,
`test_a_worker_thread_that_outlives_the_scope_cannot_reopen_the_closed_ledger`). Live child
delegation inside an open scope is `test_async_child_delegated_ordering_still_orders_and_pages`
and `test_async_child_delegated_impure_ordering_is_rejected`.

Metadata integrity is proven at the boundary it lives on. The validator rows above hand the
factory a fabricated same-origin object, a `copy.copy` of the registered definition, and a
target the registry has dropped. `tests/test_connection.py::test_a_warm_connection_cache_refuses_alternate_metadata_for_its_target`
warms an entry from the real definition, then presents a `copy.copy` of it carrying
`connection = {"total_count": True}` and asserts the rejection rather than the earlier shape,
with the real definition's entry intact afterward.
`tests/test_connection.py::test_the_optimizer_plans_a_relation_without_reading_the_target_class`
is parametrized over hook flavour and relation vocabulary on a `DjangoSchema`: once the schema
is built, the relation target's definition attribute is replaced by a decoy over a DIFFERENT
MODEL, so a residual read would move the planned prefetch to another table. The list and
connection vocabularies run from separate documents because they forward the captured model
from separate call sites. The custom-hook rows require the hook to have RUN; the cold and warm
requests are asserted apart, each against the plan-cache counters (hits, misses, size) that say
which state it ran in, because a plan carrying a hook is deliberately not cacheable and calling
a second request "warm" without reading those counters would pass equally well if caching had
stopped. Live coverage takes the same claims to the wire over a PLANNED relation, where the
plan is the only thing scoping the rows:
`examples/fakeshop/test_query/test_products_visibility_api.py` asserts that a planned `items`
list and a planned `itemsConnection` window both hide the target's private rows
(`test_anonymous_planned_list_relation_omits_the_targets_private_rows`,
`test_anonymous_planned_relation_connection_window_omits_the_targets_private_rows`, beside their
staff controls), and
`examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_window_hides_embargoed_rows_and_counts_them_out`
asserts the same for the keyset vocabulary's nested window.

### The raw-list row source

The ceiling's ownership is proven at both tiers, because the seam is shared and the relation
branch that reaches it has no visibility rebuild in front of it.

Package rows in [`tests/test_resource_policy.py`][test-resource-policy] take a `QuerySet`
subclass whose slice returns every row through `bounded_rows` and `bounded_rows_async`
(`test_a_queryset_subclass_cannot_answer_its_own_row_bound` and its `_when_awaited` twin), and
through the private `_windowed_rows` / `_windowed_rows_async` arms with a coordinate window
(`test_a_windowed_queryset_subclass_is_windowed_on_the_rebuilt_queryset`) and a zero-width one
(`test_a_zero_width_window_on_a_queryset_subclass_returns_no_rows` and its `_when_awaited`
twin). Beside them: an exact-queryset control asserting the SQL `high_mark` is still the
effective ceiling (`test_an_exact_queryset_still_carries_the_row_bound_into_sql`), a sealable
subclass asserting the rebuild keeps that `high_mark` rather than counting the rows in Python
(`test_a_sealable_queryset_subclass_keeps_the_row_bound_in_sql`), an unrebuildable subclass
asserting a typed `ConfigurationError` rather than a fallback to its own subscript
(`test_a_queryset_subclass_that_cannot_be_sealed_is_refused_not_sliced`), a class-spoofing
non-queryset asserting it reaches the counting arm
(`test_a_value_that_only_claims_to_be_a_queryset_cannot_reach_the_slice`), and a source whose
declared model is not a model class refused
(`test_a_queryset_subclass_without_a_model_class_is_refused`). The warm cache is pinned both
ways: an exact queryset's fetched rows are read out of Django's slot
(`test_rows_a_source_already_fetched_are_read_from_the_frameworks_own_slot`), and a subclass
answers none (`test_a_queryset_subclass_is_never_asked_what_it_has_already_fetched`).

Evaluation state is pinned beside them: an evaluated exact queryset and an evaluated project
queryset class with no overrides are each windowed through `bounded_rows` and
`bounded_rows_async` with the query count asserted zero and the rows asserted equal to the
leading window of what the source held
(`test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds`,
`test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds`, and their
`_from_its_own_rows_when_awaited` twins), and a `_result_cache` that is not a list is refused
(`test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`).
`QuerySet.as_manager()` and `Manager.from_queryset` name the same shape throughout this spec -
a project queryset class behind a model's default manager - and a row proving one proves the
other.

The pending reverse-relation predicate every relation queryset carries is pinned at the same
tier. `test_a_relation_source_from_a_project_queryset_class_keeps_its_relation_predicate`
builds a no-override subclass whose predicate Django's own `_apply_rel_filters` leaves
pending, windows it from the rows it holds, and asserts the SQL its rebuild compiles carries
the relation predicate.

Live rows in [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy]
mount a `DjangoListField` root over `PatronType`, whose many-side `loans` target declares no
custom `get_queryset`, at `max_list_rows=1` over a patron seeded with four loans. The reverse
manager's `.all()` is made to return a `QuerySet` subclass, and the complete wire payload
carries one loan on the sync transport and one on `AsyncDjangoGraphQLView`
(`test_a_relation_manager_cannot_widen_the_raw_list_bound_with_its_own_slice`,
`test_a_relation_manager_cannot_widen_the_raw_list_bound_on_the_async_transport`); the same
document with Django's own manager is the control
(`test_an_ordinary_relation_manager_is_bounded_the_same_way`). A second pair exercises the
fakeshop `Loan` model's override-free `LoanQuerySet.as_manager()` declaration under a
prefetching plan at two parent cardinalities and asserts the expected payload and an ABSOLUTE two-query count -
one parent query plus one prefetch
(`test_a_project_queryset_class_relation_costs_two_prefetch_queries`); equality alone would be
vacuous, and the second cardinality is what distinguishes a prefetch from an N+1. The async
transport row asserts the same rows rather than a count
(`test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited`), because a query
capture opened on the event-loop thread cannot see work a `sync_to_async` worker thread does.
No test mounts a manager by rewriting `_meta` or calls `_expire_cache()`, and the declared
manager sets no `use_in_migrations`, so no library migration carries it.

A source whose selected annotation's node already ran a row fetch (an evaluated `Prefetch`
cache, or a hook result a sibling clone fetched) is pinned live in
[`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]. A consumer
`Prefetch("loans", queryset=Loan.objects.annotate(...))`, an aggregate and a non-aggregate
expression, is served from the prefetch cache Django filled in one book statement plus one
loan statement (`test_library_consumer_loans_prefetch_carrying_an_annotation_is_served`), and a
`LoanType.get_queryset` returning an annotated queryset whose node a sibling clone already
fetched answers the no-hook rows on the root connection, the per-parent nested list and
connection, the node refetch, and the plain-list relation and nested connection planned
under `allLibraryBooks`, at each case's fixed no-hook statement count plus the hook's own reads
(`test_library_loan_get_queryset_returning_an_annotation_a_clone_fetched_is_served`).

### Assertions

SQL rows assert the captured `library_branch` statements - their count, the `LIMIT` /
`OFFSET` marks, and the absence of `DISTINCT` or a random function where the row says so.
Error rows assert the `extensions` fields the rejection carries (`code`, `reason`,
`argument`, and `value` / `ceiling` where present).

## Doc updates

- [`django_strawberry_framework/list_field.py::DjangoListField`][list-field] - the docstring
  documents the argument surface and nonzero-offset precondition, conditional default-named
  `orderBy` publication, active name conversion, cap behavior, no pk append, and the
  recommendation for a unique final order term. It states the contract as ORDERED OFFSET
  rather than stable or repeatable pagination, and says a published `offset` is a runtime
  precondition - usable only where an order source exists - not a promise that the field can
  page.
- [`django_strawberry_framework/resource_policy.py`][resource-policy] - the `ResourcePolicy`
  `max_list_rows` field and the bounding-helper docstrings describe returned/accepted-skip
  ceilings as accepted-coordinate ceilings, not a total database scan guarantee. The
  `execution_deadline_seconds` field names `bounded_rows` in both raw-list spellings among its
  cooperative seams; the client coordinates ride the private seam beneath them, and neither
  helper stops being a deadline seam.
- [`docs/GLOSSARY.md`][glossary] (DB-backed) - the `DjangoListField` entry carries the
  argument surface, the ordered-offset contract with no stable/repeatable wording, the
  asymmetric coordinate ceilings in its row-bound paragraph, and its nested-usage sentence;
  the `OrderSet` entry states its reuse by `DjangoListField` with no pk tiebreaker or
  `DISTINCT`. The card's three entries - [`ListArgumentError`][glossary-listargumenterror], the
  [list offset order precondition][glossary-list-offset-order-precondition], and the
  [async queryset completion adapter][glossary-async-queryset-completion-adapter] - read
  shipped (`0.0.15`). The adapter entry scopes its safety claim to framework-owned final
  queryset completion rather than to async safety generally. The offset-precondition entry
  states that a published `offset` is a runtime precondition rather than a per-field
  capability claim.
- [`docs/README.md`][docs-readme] - the `DjangoListField` section states the argument surface,
  the coordinate ceilings, the offset precondition and the readable-order rule, and the
  ordered-offset contract; its extension and trust-boundary paragraphs state the class or
  factory extension spelling, the per-operation isolation guarantee, and the
  trusted/validated/untrusted parties.
- [`README.md`][readme] - the root-field example states the `offset` / `limit` arguments, the
  conditional `orderBy`, and the ordered-offset contract.
- [`TODAY.md`][today] - records the `DjangoListField` `offset` / `limit` / `orderBy` arguments
  as available and live-tested, and lists
  [`Meta.aggregate_class`][glossary-metaaggregate-class],
  [`Meta.fields_class`][glossary-metafields-class], and
  [`Meta.search_fields`][glossary-metasearch-fields] as not accepted.
- [`docs/TREE.md`][tree] - lists `test_list_field_api.py` and `test_list_field_async_api.py`
  under `examples/fakeshop/test_query/`.
- [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants] - its tracked-path
  constants, written by
  [`scripts/build_kanban_tracked_path_constants.py`][build-kanban-tracked-paths], include both
  live list-field suites.
- [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] - the suite map
  indexes BOTH suites, and its clients section names execution colour (an
  `AsyncDjangoGraphQLView` mount) as the reason an async row drives `AsyncTestClient` rather
  than [`examples/fakeshop/graphql_client.py`][fakeshop-graphql-client].
- [`django_strawberry_framework/__init__.py`][package-init] and
  [`tests/base/test_init.py`][test-base-init] - the `ListArgumentError` root export beside
  `ResourceLimitExceeded` and `PaginationArgumentError`, and the pinned `__all__`, star-import,
  and export-identity rows.
- KANBAN DB and generated exports - card 050's Scope states the conditional `orderBy`
  surface, and its Definition of done states the SDL change as nullable `offset` / `limit`
  plus `orderBy` where the target declares `Meta.orderset_class`, and the `LIMIT` / `OFFSET`
  window contract (Decisions 2 and 9).

## Risks and open questions

*Preferred answers are in the spec; fallbacks are in the companion [rationale][rationale-risks].*

- **`orderBy` is published only where the target declares `Meta.orderset_class`.** Preferred
  answer: the conditional surface in Decision 2. *Fallback: see the
  [rationale][rationale-risks].*
- **GraphQL coercion errors cannot carry the package runtime code.** Preferred answer:
  Decision 10's split - all cases are `GraphQLError`, while only field-domain errors carry
  package extensions. *Fallback: see the [rationale][rationale-risks].*
- **Active order does not prove uniqueness, so the delivered contract is weaker than the
  words "stable subset" suggest.** Preferred answer: the contract is named ORDERED OFFSET
  everywhere (Decision 7), a visible order is required, the unique-final-term recommendation
  is documented, and the shipped docs carry no stable/repeatable wording. *Fallback: see the
  [rationale][rationale-risks].*
- **The sync early-exit cleanup contract is declined, not solved.** Preferred answer:
  leak-free early exit is promised for async-only sources only, the declined sync behavior is
  pinned in a test, and the Definition of done says so. *Fallback: see the
  [rationale][rationale-risks].*
- **Document collection-cost accounting and the runtime coordinate ceilings are two different
  budgets and visibly disagree.** Preferred answer: the document charge is a schema-generic
  fixed estimate, the accepted logical window bounds are stated outright (Decision 4), and
  neither mechanism changes. *Fallback: see the [rationale][rationale-risks].*
- **Nested `DjangoListField` arguments are unspecified while the glossary promises nested
  usage is functional.** Preferred answer: nested usage keeps the no-argument behavior, the
  arguments are unspecified in that position, and the glossary promise stands. *Fallback: see
  the [rationale][rationale-risks].*
- **`max_list_rows` may be too small as a migration offset ceiling.** Preferred answer: the
  offset ceiling is `max_list_rows` (Decision 4). *Fallback: see the
  [rationale][rationale-risks].*
- **Ordering an already-sliced consumer queryset is a migration trap.** Preferred answer: the
  shared sealed visibility boundary rejects it before the hook, under active and omitted
  arguments alike. *Fallback: see the [rationale][rationale-risks].*
- **Arbitrary custom `OrderSet.apply_*` code can discard visibility predicates.** Preferred
  answer: unsafe output shapes are rejected mechanically, and the override is documented as a
  trusted schema-author boundary that transforms the supplied sealed queryset. *Fallback: see
  the [rationale][rationale-risks].*
- **Django combined querysets do not compose uniformly with order and optimizer operations.**
  Preferred answer: a combined source or result is served as the set of primary keys it
  selects under every argument shape, and a combined shape that rewrite would change fails
  closed. *Fallback: see the [rationale][rationale-risks].*
- **Upstream is retiring the instance spelling Decision 14 reads as a declaration.** Preferred
  answer: Decision 20 - the deprecation is inherited, class and factory are documented, and the
  per-operation isolation of the package's own extensions is stated as the guarantee this
  package adds. *Fallback: see the [rationale][rationale-risks].*

## Out of scope (explicitly tracked elsewhere)

- The other upstream parity gaps and an `extensions.code` on connection pagination rejections
  belong to [`TODO-ALPHA-051-0.0.15`][kanban].
- Debug-extension extraction belongs to [`TODO-ALPHA-052-0.0.15`][kanban].
- The boundary/DRY squeeze and the `0.0.15` release cut belong to
  [`TODO-ALPHA-053-0.0.15`][kanban].
- The complete migration/adoption guide, including the mapping table in Decision 11,
  belongs to [`TODO-BETA-071-0.1.8`][kanban].
- Beta-release verification and the final parity claim belong to
  [`TODO-ALPHA-057-0.1.0`][kanban].
- Filtering/search arguments on `DjangoListField`, response envelopes, list `totalCount`,
  and nested raw-list windows are uncarded and not implied by this surface.

## Definition of done

- [ ] Every `DjangoListField` publishes nullable optional `offset` and `limit`; targets with
      `Meta.orderset_class` also publish the typed `orderBy` input.
- [ ] With all arguments omitted/null, sync resolver behavior, queryset low/high marks, SQL,
      query count, ordering, and response bytes match a no-argument reference resolver
      mounted under the SAME GraphQL field name in its own schema, so one request envelope
      reaches both and raw `HttpResponse.content` is what is compared; the shipped field,
      under its own name, matches the same reference's rows, SQL, marks, and hook count. Async
      no-argument completion runs the same visibility and window through the safe completion
      adapter (`test_async_queryset_completion_default_resolver`,
      `test_async_get_queryset_is_awaited`,
      `test_async_a_query_source_resolver_still_applies_target_visibility`,
      `tests/test_list_field.py::test_async_completion_adapter_semantics`,
      `::test_list_field_optimizer_adapter_unwrap_rewrap_and_early_returns`). SDL gains the
      arguments.
- [ ] Limit is accepted through the effective policy/field/trusted ceiling and rejected
      above it; offset is accepted through request `max_list_rows` and rejected above it;
      `trusted_max_rows=True` with no `max_rows` keeps the policy ceiling.
- [ ] The ceiling both of those read is the budget the operation started with, not a value
      the request can rewrite: a resolver that replaces `DST_RESOURCE_POLICY` on `info.context`
      changes neither the returned-row bound nor the `offset` ceiling derived from the same
      field, and one that pushes `DST_RESOURCE_DEADLINE` forward or clears it does not outlive
      its budget. A resolver writing an EARLIER deadline still shortens its own request; a
      numeric deadline that is not finite, or that is not an exact built-in number, is refused
      rather than read as a distant future - a subclass answers both the comparison the
      narrowing rule is decided by and the one deciding whether time is up.
- [ ] No policy object a resolver can name is the object a bound is read from. The schema
      attributes answer with a copy, the operation's budget is a private snapshot, the
      published mirror is a third object, and `policy_from_info` returns a copy - so a
      `__dict__` write on any of them, which a frozen dataclass admits, changes only the
      writer's own duplicate and nothing a later request reads. A `ResourcePolicy` or
      `ErrorPolicy` SUBCLASS is read out once at schema construction and replaced by an exact
      instance. The extension that arms the budget is the schema's own, built per operation
      from that construction record: an enforcement authority is never an extension ENTRY, so
      no factory, closure, singleton selector or subclass a resolver can reach through
      `info.schema` decides what a later request is bounded by. A subclass supplied directly,
      as a class or as an instance, is refused with `ConfigurationError` at construction, and
      an entry that RESOLVES into one refuses the operation instead.
- [ ] A bound stored on a `ResourcePolicy`, and a field's declared `max_rows`, is an exact
      built-in `int` (or `float` for the deadline); every numeric subclass is refused with a
      typed `ConfigurationError` before any comparison, arithmetic or formatting runs, so no
      consumer dunder can reach the derived deadline or a rejection's rendered `limit`. An
      upload's reported `size` that is not an exact non-negative `int` is refused rather than
      charged as zero, and a `first` / `last` page bound supplied as an `int` subclass narrows
      nothing.
- [ ] Negative and over-ceiling values raise `ListArgumentError` with stable extensions;
      active schema naming determines `argument` and the `orderBy` name a rejection reports;
      string, bool, non-integral float and float-literal coercion failures perform no SQL,
      while integral float variables retain graphql-core's standard coercion.
- [ ] Nonzero offset requires a materially active `orderBy` or still-effective model
      `Meta.ordering` on the post-visibility queryset, judged against the ONE collection
      Django's compiler selects by precedence rather than against a union of the explicit
      ones: a random model default disqualifies an active-input request whose override leaves
      it selected, an explicit stable order over a random model default backs the window, and
      a random term the compiler does not select cannot disqualify anything. An order only the
      resolver applied never authorizes an offset. A selected term is judged by the form the
      compiler resolves it into and is certified only when that form is one this package
      NAMES - a listed composition, function or aggregate, or a readable leaf (a column, the
      `*` of a row count, a literal, the framework's `VisibleRowExists`), matched by exact
      type - and every source it holds is certified too. So an annotation alias over a random
      expression, an `F` naming one, a nested `Random()`, a `RawSQL` fragment, a bare or
      project `Func`, a `Transform`, a `Window`, an unlisted aggregate, a SUBCLASS of an
      approved class - of the `F` and `Q` reference forms as much as of a function - and a
      `Subquery`'s inner query all disqualify as a literal `"?"` does, while a composition of
      approved forms over readable leaves still backs the window. A term is read as a string
      name only when it carries no `resolve_expression`, which is the order the compiler
      dispatches in. A predicate's trailing transforms and its final lookup are matched against
      approved sets the same way. A STRING term naming a relation is judged by the related
      model's own `Meta.ordering`, which the compiler expands it into and which the term as
      written never shows, so a random default one or more relations away disqualifies the
      request while the foreign key column named directly does not; a many-to-many or generic
      relation name always expands, since the field its join walk ends on carries no `attname`
      it spells, and an expansion repeating a join anywhere under one top-level term is
      refused rather than followed; an expression reference to that same relation does NOT
      expand, resolving to the foreign key column, so it still backs the window. A conditional
      order's predicate is read on both sides, so the reference a lookup compares FROM
      disqualifies the request exactly as the value compared against does and a random alias
      cannot be laundered through `When(coin__gt=...)`. Empty/null order input, cleared or
      replaced model ordering, random ordering, grouping that suppresses the default, and
      opaque Python iterables cannot fake the condition. The contract is stated as ORDERED
      OFFSET; no spec, docstring, glossary, or error text promises a stable or repeatable page,
      and a published `offset` is documented as a runtime precondition rather than a per-field
      pagination capability.
- [ ] No raw-list row source decides its own ceiling. An unevaluated exact `QuerySet` is
      sliced and keeps its SQL `LIMIT`; a `QuerySet` SUBCLASS is rebuilt into a plain
      framework-owned queryset through the shared sealer and sliced there, so a sealable,
      unevaluated project queryset class keeps that `LIMIT` and an unrebuildable one is
      refused with a typed `ConfigurationError` instead of falling back to its own
      `__getitem__`. A pending reverse-relation predicate does not make a subclass
      unrebuildable: Django leaves one on every relation queryset it builds whatever class the
      manager was made from, and the seal bakes it onto the detached clone, while a
      deferred-filter state that is not the exact shape Django writes - the `negate` slot's
      exact `bool` included, refused without reaching its own `__bool__` - is refused with
      that same typed error. An object whose `__class__` merely claims to be a queryset cannot
      select the slice arm at all. The shape is read from `type(value)` at every admission,
      including the sealer's own, so a `__class__` property can neither be consulted nor raise
      out of a shape proof.
- [ ] The generated many-side relation resolver reaches that seam on its no-custom-visibility
      branch too - the one path with no visibility rebuild in front of it - and normalizes the
      relation cache before reading the rows it holds. Proven live on both transports with a
      relation manager returning a `QuerySet` subclass over a `DjangoListField` root: the
      response carries `max_list_rows` rows, not the relation's.
- [ ] A source that arrives evaluated is windowed from the rows it holds with no further
      query, exact queryset and rebuilt subclass alike, through `bounded_rows` and
      `bounded_rows_async`; the fakeshop `Loan` model's override-free
      `LoanQuerySet.as_manager()` declaration returns the expected rows at an ABSOLUTE two-query prefetch cost at two
      parent cardinalities, and returns those same rows on the async transport (Decision 8).
      The declared manager sets no `use_in_migrations`, so no library migration carries it.
- [ ] Visibility runs before order; order runs before one combined slice; order permission
      failures occur before slicing.
- [ ] Public `OrderSet.apply_*` results are mechanically validated as unevaluated, unsliced,
      non-projection, same-model/same-route plain querysets, a combinator served as its
      primary-key set, with the accepted result pinned to the effective alias frozen before
      the override ran; custom overrides are documented as trusted to preserve the sealed
      input's predicates.
- [ ] The shared visibility boundary rejects a pre-sliced source before the hook and a sliced
      hook result afterward for both active and omitted arguments and in both execution
      colors, before any ordering runs; the list field adds no parallel query-state
      classifier. Non-queryset/`None` sources follow the explicit limit/order contracts and
      never silently ignore `orderBy`.
- [ ] No pk tiebreaker and no `DISTINCT` are injected; to-many ordering keeps the `Min` /
      `Max` aggregate behavior.
- [ ] Unevaluated querysets retain SQL `LIMIT/OFFSET`, and a source that arrives evaluated is
      windowed from the rows it holds instead (Decision 8); sequences, iterables, and
      async-only iterables are bounded without over-consuming beyond the accepted window.
      Leak-free early-exit cleanup is promised for ASYNC-ONLY sources on every exit that
      abandons the source, argument rejection and deadline rejection alike, through one shared
      cleanup utility that sits below both callers and demotes only an ordinary `Exception` to
      a note on the primary error, letting a control signal propagate; a retained sync
      generator is documented and tested as still suspended after truncation, and the
      symmetric sync contract is declined.
- [ ] The exported `bounded_rows` / `bounded_rows_async` signatures carry no client window;
      the coordinate-bearing seam is package-private, called only by the list field and by
      the exported pair, and the exported names are tested to refuse both coordinates.
- [ ] Async queryset results complete over `AsyncDjangoGraphQLView` through an async-only
      adapter, with optimizer-on/off parity; no list-field async suite and no
      `tests/test_relay_connection.py` row sets `DJANGO_ALLOW_ASYNC_UNSAFE`.
- [ ] A refused request is answered by the package end to end: the document it arrived with
      reaches no parser, the operation selector is the package's own anonymous one, and the
      transport policy is read ONCE into an exact built-in `tuple` that is put back on the
      execution context before the substitute document is selected from it. A one-shot
      iterable survives `execute_sync`, `execute` and `stream` with the stable configuration
      code; a container with a hostile `__bool__` is never truth-tested; a policy that allows
      nothing still gets upstream's operation-type refusal rather than a widened one
      (Decisions 16 and 17, [`tests/test_schema.py`][test-schema]).
- [ ] Which GraphQL executor drives a resolver is carried from the entry point into the chain
      and bound by the runner for the operation, result collection, every streamed frame and
      every stream resume, restoring the enclosing operation's answer on the way out and
      answering nothing from a copied context after the lease closes. Every executor-dispatch
      reader in the package reads the one canonical helper; `execute_sync` under a running
      event loop raises `SyncMisuseError` at the call that caused it rather than handing the
      synchronous executor a coroutine, and a plain `strawberry.Schema` is documented as
      retaining ambient dispatch (Decision 18,
      [`django_strawberry_framework/utils/execution_mode.py`][execution-mode],
      [`tests/utils/test_execution_mode.py`][test-execution-mode],
      [`tests/extensions/test_operation_state.py`][test-operation-state],
      [`tests/test_list_field.py`][test-list-field], and the live nested-operation row in
      [`examples/fakeshop/test_query/test_list_field_async_api.py`][fakeshop-test-list-field-async]).
- [ ] Live HTTP coverage exercises ordered paging, `orderBy`, visibility, cap interplay, and
      runtime/coercion errors under default and configured naming, plus both verdicts of the
      model-default order predicate, with wire-reachable async behavior in
      `examples/fakeshop/test_query/test_list_field_async_api.py`; package-only coverage is
      limited to construction, exact helper mechanics, and predicate states no live mount can
      construct.
- [ ] `ListArgumentError` is exported from the package root beside its two precedents, and
      the pinned `__all__`, star-import, and export-identity governance rows include it; wire
      names are resolved only on the error path and never by running the schema's
      `NameConverter`, proven by a zero-call converter assertion on successful and rejected
      normalizations.
- [ ] Card 050's Scope and Definition of done in the KANBAN database state the conditional
      `orderBy` surface and the `LIMIT` / `OFFSET` window contract this spec describes.
- [ ] CI gates the suite in `.github/workflows/django.yml`: every push and PR runs it on the
      exact-floor cell and the latest cell, the latest cell owning `fail_under = 100`, beside
      the lint job's formatting, type and structural checks; manual dispatch runs the full
      supported Python/Django matrix in both the single-database and `FAKESHOP_SHARDED=1`
      layouts.
- [ ] The list-field docstring and shipped docs state the argument, cap, and order contracts.
- [ ] The shipped docs state the trust contract where a deployer reads it: application Python
      is trusted and its documented result contracts are validated; the wire and configuration
      are the bounded parties; a class or a factory is the documented extension spelling, the
      instance spelling carries upstream's deprecation unchanged, and per-operation isolation
      of the package's own extensions - the singleton-in-a-factory optimizer recipe included -
      is stated as the guarantee this package adds (Decisions 19 and 20).
- [ ] The type registry is the one canonical metadata source: every field factory accepts only
      the definition it holds for the target (by identity), the generated-connection cache
      proves each warm entry's provenance, and the optimizer plans a relation from the child
      definition it resolved the relation through - leaving no request-time
      `__django_strawberry_definition__` read keyed by a target class on the planned path.
- [ ] Ledger closure is terminal, proven for a descendant task and a worker thread that each
      resume after the owning scope ended, without regressing live child delegation or the
      disagreement rejection inside an open scope.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-async-queryset-completion-adapter]: ../GLOSSARY.md#async-queryset-completion-adapter
[glossary-async-sql-capture-boundary]: ../GLOSSARY.md#async-sql-capture-boundary
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cookbook-parity]: ../GLOSSARY.md#cookbook-parity
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangographqlview]: ../GLOSSARY.md#djangographqlview
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangoresourcepolicyextension]: ../GLOSSARY.md#djangoresourcepolicyextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-execution-resource-policy]: ../GLOSSARY.md#execution-resource-policy
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_queryset]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-list-offset-order-precondition]: ../GLOSSARY.md#list-offset-order-precondition
[glossary-listargumenterror]: ../GLOSSARY.md#listargumenterror
[glossary-live-first]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-metaaggregate-class]: ../GLOSSARY.md#metaaggregate_class
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafields-class]: ../GLOSSARY.md#metafields_class
[glossary-metafilterset-class]: ../GLOSSARY.md#metafilterset_class
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-metasearch-fields]: ../GLOSSARY.md#metasearch_fields
[glossary-multi-database]: ../GLOSSARY.md#multi-database-cooperation
[glossary-order_input_type]: ../GLOSSARY.md#order_input_type
[glossary-ordering]: ../GLOSSARY.md#ordering
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-pep-562-lazy-export]: ../GLOSSARY.md#pep-562-lazy-export
[glossary-probe-urlconf]: ../GLOSSARY.md#probe-urlconf
[glossary-production-error-policy]: ../GLOSSARY.md#production-error-policy
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-resourcepolicy]: ../GLOSSARY.md#resourcepolicy
[glossary-schema-reload-discipline]: ../GLOSSARY.md#schema-reload-discipline
[glossary-sealed-execution-queryset]: ../GLOSSARY.md#sealed-execution-queryset
[glossary-seed-data]: ../GLOSSARY.md#seed_data
[glossary-strawberry_config]: ../GLOSSARY.md#strawberry_config
[glossary-structural-error-classification]: ../GLOSSARY.md#structural-error-classification
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-visibility-boundary]: ../GLOSSARY.md#visibility-boundary
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale]: appx/spec-050-list_field_arguments-0_0_15-rationale.md
[rationale-borrowing]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#borrowing-posture--what-was-deliberately-not-borrowed-and-why
[rationale-d1]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-1--synthesize-one-resolver-signature-do-not-widen-consumer-resolvers
[rationale-d10]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-10--coercion-errors-stay-graphql-owned-runtime-domain-errors-are-package-owned
[rationale-d12]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-12--graphql-core-workarounds-have-a-dependency-owned-lifecycle
[rationale-d13]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-13--configuration-authority-is-schema-state-everything-per-request-is-operation-state
[rationale-d14]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-14--an-enforcement-authority-is-a-declaration-never-an-extension-entry
[rationale-d15]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-15--the-runner-owns-every-binding-for-the-operations-whole-lifetime
[rationale-d16]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-16--a-refused-requests-document-selector-and-transport-policy-are-all-package-owned
[rationale-d17]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-17--the-refusal-is-stable-and-the-transports-own-policy-is-the-one-exception
[rationale-d18]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-18--execution-mode-is-operation-state-the-ambient-event-loop-is-a-different-fact
[rationale-d19]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-19--application-code-is-trusted-the-wire-is-not-a-finding-is-admitted-by-reachability
[rationale-d2]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-2--sidecar-conditional-orderby-is-the-only-truthful-meta-first-surface
[rationale-d20]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-20--the-extension-contract-is-upstreams-per-operation-isolation-is-the-guarantee-this-package-adds
[rationale-d4]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-4--max_list_rows-also-bounds-skip-trusted-widening-does-not
[rationale-d5]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-5--validate-then-visibility-ordering-and-exactly-one-slice
[rationale-d6]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-6--nonzero-offset-requires-a-materially-active-order
[rationale-d7]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-7--active-order-is-not-total-order-no-pk-tiebreaker-is-appended
[rationale-d8]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-8--queryset-and-iterable-sources-have-explicit-different-capabilities
[rationale-d9]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#decision-9--a-request-with-no-list-argument-runs-the-plain-bounded-path-async-only-adapts-completion
[rationale-risks]: appx/spec-050-list_field_arguments-0_0_15-rationale.md#risks-and-open-questions--the-fallback-positions
[spec-020]: spec-020-list_field-0_0_7.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-030]: spec-030-connection_field-0_0_9.md
[spec-047]: spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[list-field]: ../../django_strawberry_framework/list_field.py
[operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[package-init]: ../../django_strawberry_framework/__init__.py
[private-state]: ../../django_strawberry_framework/utils/private_state.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[truth]: ../../django_strawberry_framework/utils/truth.py
[typing-utils]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-execution-mode]: ../../tests/utils/test_execution_mode.py
[test-list-field]: ../../tests/test_list_field.py
[test-operation-state]: ../../tests/extensions/test_operation_state.py
[test-orders-sets]: ../../tests/orders/test_sets.py
[test-querysets]: ../../tests/utils/test_querysets.py
[test-resource-policy]: ../../tests/test_resource_policy.py
[test-schema]: ../../tests/test_schema.py

<!-- examples/ -->
[fakeshop-graphql-client]: ../../examples/fakeshop/graphql_client.py
[fakeshop-kanban-constants]: ../../examples/fakeshop/apps/kanban/constants.py
[fakeshop-library-schema]: ../../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-list-field-async]: ../../examples/fakeshop/test_query/test_list_field_async_api.py
[fakeshop-test-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py
[fakeshop-test-query-readme]: ../../examples/fakeshop/test_query/README.md
[fakeshop-test-relations-async]: ../../examples/fakeshop/test_query/test_relations_async_api.py
[fakeshop-test-resource-policy]: ../../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->
[build-kanban-tracked-paths]: ../../scripts/build_kanban_tracked_path_constants.py

<!-- .venv/ -->
[django-compiler]: ../../.venv/lib/python3.14/site-packages/django/db/models/sql/compiler.py
[django-query]: ../../.venv/lib/python3.14/site-packages/django/db/models/sql/query.py
[django-queryset]: ../../.venv/lib/python3.14/site-packages/django/db/models/query.py
[graphql-execute]: ../../.venv/lib/python3.14/site-packages/graphql/execution/execute.py
[graphql-scalars]: ../../.venv/lib/python3.14/site-packages/graphql/type/scalars.py
[strawberry-info]: ../../.venv/lib/python3.14/site-packages/strawberry/types/info.py
[strawberry-name-converter]: ../../.venv/lib/python3.14/site-packages/strawberry/schema/name_converter.py
[strawberry-schema]: ../../.venv/lib/python3.14/site-packages/strawberry/schema/schema.py
[strawberry-schema-converter]: ../../.venv/lib/python3.14/site-packages/strawberry/schema/schema_converter.py

<!-- External -->
[cookbook-connection-field]: ../../../django-graphene-filters/django_graphene_filters/connection_field.py
[cookbook-schema]: ../../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[django-security-policy]: https://docs.djangoproject.com/en/5.2/internals/security/#code-under-test-must-feasibly-exist-in-a-django-project
[upstream-graphene-fields]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py
[upstream-strawberry-extension-isolation]: https://github.com/strawberry-graphql/strawberry/issues/4369
[upstream-strawberry-pagination]: ../../../strawberry-django-main/strawberry_django/pagination.py
