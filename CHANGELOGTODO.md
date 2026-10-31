# CHANGELOG to-do

Every [`CHANGELOG.md`][changelog] entry still to write, moved here from the trackers that filed them:
[`docs/dry/dry-0_0_15_3.md`][dry-0_0_15_3], [`docs/bug_hunt/bug_hunt-0_0_15_2.md`][bug-hunt-0_0_15_2] and
[`docs/dry/dry-upstream-0_0_15.md`][dry-upstream-0_0_15]. Each item keeps its number from its source tracker, so "item
N" inside an entry, and a "CHANGELOG: item N" note left in the source, mean that tracker's item N. The
dry-upstream-0_0_15 tracker files no entries of its own, so its entries are numbered from 101, clear of its items.
The test-compliance-review entries have no tracker in the repository; they continue from 106, clear of every other
section's numbers. Tick an entry once it is written into `CHANGELOG.md`.

Progress: 0 done, 159 to do.

## From dry-0_0_15_3

- [ ] 53. CHANGELOG entry for item 3: an unwired `FilterSet` / `OrderSet` subclass of a wired set is unbound like any
  unwired set: as a `RelatedFilter` / `RelatedOrder` target it reads its model's registry type, not its base's owner
  (rows, order positions, own-pk GlobalID vs scalar, relation GlobalID validation), and a target model with no
  registered type now raises at finalize. With items 50 and 83: a wrong-type relation GlobalID through an unwired target
  set, or through a hop no type exposes, is refused ("GlobalID type mismatch"), and a callable / custom-strategy target
  behind such a hop is refused at finalize
- [ ] 57. CHANGELOG entry for item 4: a `Meta.input_class` field declared without `name=` keys its `FieldError`s to
  the name the schema published (`isbn10` by default, `isbn_10` under `auto_camel_case=False`), and the mutation
  resource policy charges it like a generated field (word the second clause per [SECURITY.md][security])
- [ ] 59. CHANGELOG entry for item 35: `DjangoOptimizerExtension.plan_relation` is removed (the optimizer never called
  it, so an override had no effect; `Meta.optimizer_hints` is the per-relation control), and
  `optimizer.walker.plan_relation` no longer takes `info`
- [ ] 64. CHANGELOG entry for item 14: `inspect_django_type`'s converter column names `DjangoFilePathType` /
  `DjangoImagePathType` for a `Meta.filesystem_path_fields` column, matching its type column
- [ ] 60. CHANGELOG entry for item 43: a filter value holding a lone surrogate or an embedded NUL answers
  `FILTER_INVALID` keyed to its form field on every backend, instead of an unexpected error (and, for a NUL in a
  plain-`Field` filter such as a text-pk relation key on SQLite, instead of an empty result); such a request reports
  only the refused fields, and a `ModelChoiceFilter` with `to_field_name` answers with that message instead of
  "Select a valid choice"
- [ ] 62. CHANGELOG entry for item 1: the default `DjangoModelPermission` checks the model the mutation class resolved
  at declaration (a `_resolve_model` override is consulted only then), the same model the write uses (word it per
  [SECURITY.md][security]); with item 39, a model-less auth field given `DjangoModelPermission` is refused at
  declaration
- [ ] 76. CHANGELOG entry for items 7 and 39: `login_mutation`, `logout_mutation` and `current_user` refuse at
  declaration a `DjangoModelPermission` (or a subclass) that does not override `has_permission`, instead of failing
  every request; `DjangoFormMutation` now admits a subclass that overrides it; a bad `permission_classes` names its
  own surface (`DjangoFormMutation`, `SerializerMutation`, the auth factory keyword) instead of `DjangoMutation`
- [ ] 78. CHANGELOG entry for item 63: `inspect_django_type` prints a `(not a GraphQL field)` row for a selected column
  whose annotation Strawberry publishes no field for (`relay.NodeID`, `strawberry.Private`, `ClassVar`) instead of
  raising `StopIteration`, and a Relay type's `relay.NodeID` pk reads as the interface's `id` row
- [ ] 79. CHANGELOG entry for item 66: a GlobalID filter whose target type does not resolve answers `GLOBALID_INVALID`
  for a node id its compared column cannot hold, or for any id over a multi-column link, instead of a raw Django
  `ValueError`; a declared `RelationPkFilter` / `RelationPkMultipleFilter` over a `to_field` or one-column
  `ForeignObject` link types its input from that column and matches by it, and one over a multi-column link raises
  `ConfigurationError` at build
- [ ] 80. CHANGELOG entry for item 61: a `DjangoModelFormMutation` whose `get_form` returns a form over another model, or
  whose `save()` leaves another model's row on the form, raises `ConfigurationError` before writing (or rolls the write
  back) instead of writing that model's table
- [ ] 82. CHANGELOG entry for items 38 and 69: a `Meta.name`'d `DjangoType`'s choice enum is named after its published
  name (`<Meta.name><Field>Enum`) on the read side too, two same-named types split by `Meta.name` no longer collide,
  and an unwired filter set's choice enum is `<SetClass><Field>Enum` instead of `Filter<Field>Enum`
- [ ] 84. CHANGELOG entry for item 40: a write mutation's `Meta.exclude`, and a `SerializerMutation`'s
  `optional_fields` / `injected_fields` (and a `NestedSerializerConfig`'s `exclude` / `optional_fields`), accept a set
  or frozenset, stored in canonical order; `Meta.fields` still requires a list or tuple
- [ ] 85. CHANGELOG entry for items 51 and 52: a dotted `FilterSet` `Meta.fields` key ending on the set model's pk is
  that row's plain column filter (Int, every lookup) instead of a GlobalID own-pk filter, and a dotted relation key
  whose leaf shares a name with another relation on the set's model takes its own relation's target type
- [ ] 86. CHANGELOG entry for item 65: a generated relation read under `schema.execute_sync()` over a target with an
  `async def get_queryset` raises `SyncMisuseError` naming `await schema.execute()` (or the async view), instead of the
  Relay node defaults' recourse
- [ ] 87. CHANGELOG entry for item 77: a declared `ArrayFilter` / `ListFilter` over a PostgreSQL `ArrayField` column
  builds a list of its element type (`exact`, `contains`, `contained_by`, `overlap`) instead of failing the schema build,
  and any other filter or lookup over the column is refused at build with a message naming those lookups
- [ ] 88. CHANGELOG entry for item 72: a `DjangoType` that selects a visible reverse generic relation (a
  `GenericRelation` with `related_query_name`, seen from the generic-key model) is refused at declaration instead of
  publishing a field that failed every query, and a `RelatedFilter` through it no longer matches rows of another
  content type
- [ ] 89. CHANGELOG entry for items 44 and 73: a form or serializer field-map key that is a `StrEnum` / `TextChoices` /
  `(str, Enum)` member is read as its text (the serializer used to refuse it; a `(str, Enum)` form key failed the build),
  and a malformed `FilterSet` `Meta.fields` lookup value is a `ConfigurationError` at class creation
- [ ] 90. CHANGELOG entry for item 37: a GlobalID filter reads a model-label type slot's model name
  case-insensitively (`library.GENRE` filters like `library.genre`, as `node` already decoded it); the app label stays exact
- [ ] 91. CHANGELOG entry for item 45: a `Meta`-less subclass of a concrete `DjangoType` raises `ConfigurationError` at
  class creation (it used to publish as its parent with its own fields dropped); shared hooks go on a `Meta`-less base
  under `DjangoType` or a plain mixin. Reading `resolve_id_attr()` on a class finalize has not stamped raises
  `ConfigurationError` instead of a `TypeError`
- [ ] 95. CHANGELOG entry for items 81 and 92: a filter leaf is typed by the field its lookup compares to. Generated
  `year` / `year__gt` / `year__in` leaves take `Int` / `[Int!]` (they took `DateTime` and refused every value) and `date`
  takes `Date`; a declared filter whose `field_name` or `lookup_expr` goes through a transform (`occurred_at__year`, an
  `ArrayField` index or slice, `len`) takes the transform's output (`Int`, the element type or enum) where its own form
  cleans the output's kind or passes any value through. Past `year`, a `NumberFilter` takes `Int` (with
  `lookup_expr="year"` it took the column's own type, `Date` on a date column and `DateTime` on a datetime column such
  as `occurred_at`; with `field_name="<column>__year"` it took `Decimal`), and so do a bare django-filter `Filter` and
  the package's `TypedFilter` (they took the column's own type with `lookup_expr="year"` and `String` with
  `field_name="<column>__year"`), so a client sending those a date or a text year sends an int. A declared filter whose
  own form cleans another kind publishes what its form cleans: a `CharFilter` takes `String` (it took the column's own
  type with `lookup_expr="year"`; `field_name="<column>__year"` is unchanged), `DateFilter(lookup_expr="year")` and a
  `TypedFilter` subclass whose `field_class` is a `DateField` take `Date` (unchanged on a date column; on a datetime
  column they took `DateTime`), each member of a CSV filter (a `BaseInFilter` + `DateFilter` class on `year__in` takes
  `[Date!]`, unchanged on a date column and `[DateTime!]` before on a datetime column: an `Int` member stays GraphQL's
  coercion error, and a date member, which failed the request with "An unexpected error occurred.", is now
  `FILTER_INVALID`) and each axis of a django-filter range filter
  (`DateFromToRangeFilter(field_name="occurred_on__year")` takes `Date` bounds; it took `String`); a django-filter
  range filter whose two axes clean different kinds (`fields=(forms.DateField(), forms.IntegerField())`) past a
  transform raises `ConfigurationError` when the schema is built instead of publishing `String` bounds one axis cannot
  clean. A `RangeFilter` on `year__range` takes `Int` bounds (it took `DateTime`) and a lone bound applies through the
  transform (a lone `start` added no condition, so every row came back). On an `ArrayField` column,
  `NumberFilter(field_name="<column>__len")` takes `Int` (it took `Decimal`), a `lookup_expr="len"` filter builds, and
  a `lookup_expr` that is no GraphQL name (an index, `lookup_expr="0"`) raises a `ConfigurationError` naming the
  `field_name` spelling to use; both raised `ConfigurationError: Unsupported Django field type 'ArrayField'`
- [ ] 75. CHANGELOG entry for item 55: a generated payload, connection or narrowed merged input whose name carries an
  underscore publishes that name verbatim (`Create_CategoryPayload`, `Cat_NodeConnection`, `ItemIs_uprivateNameInput`)
  instead of Strawberry's re-casing (`CreateCategorypayload`, `CatNodeconnection`, `ItemIsUprivatenameinput`), and two
  narrowed merged inputs that re-cased alike no longer fail the schema build. With item 96: a `DjangoType` with no
  `Meta.name` whose class name carries an underscore (`Cat_Node`, published `CatNode`) names its connection, filter
  inputs and choice enums after `CatNode`, not `Cat_Node`

## From bug_hunt-0_0_15_2

- [ ] 697. CHANGELOG entry for item 668: a `SerializerMutation` save whose model `save()` narrows `update_fields` away
  from a `None` column and hits another constraint answers the `"__all__"` constraint envelope instead of that
  column's field-keyed `null`
- [ ] 698. CHANGELOG entry for item 670 (breaking): a `DjangoModelFormMutation` form declaring `forms.DateTimeField`
  over a `DateField` column is refused at schema build instead of storing a different day when the
  request's time zone differs from the default
- [ ] 694. CHANGELOG entry for items 654 and 657: an out-of-range integer member of an `ArrayField` of integers filter
  is `FILTER_INVALID` instead of a masked database error; a consumer annotation's constant no longer refuses an
  in-range filter value through it; an `IntegerField` subclass whose type the backend states no range for filters
  instead of raising `KeyError`
- [ ] 691. CHANGELOG entry for item 579: on a `FilterSet` used outside the schema (a django-filter view, a direct
  construction), a related child filter whose widget is a `SplitArrayWidget` or a nested `MultiWidget` filters by the
  keys the widget reads instead of being silently dropped
- [ ] 690. CHANGELOG entry for item 663: a lazy translation string (or bytes-like value) given as a mutation flavor's
  `Meta.fields` / `Meta.exclude` / `optional_fields` / `injected_fields`, a field's `directives=`,
  `apply_cascade_permissions(fields=)` or `permission_classes` is refused as a bare string instead of read one name
  per character (a form or serializer `exclude=_("ab")` dropped fields `a` and `b`); a lazy `Promise` wrapping a list
  is refused the same way
- [ ] 689. CHANGELOG entry for item 652: generated `year__in` / `year__range` (and every other integer transform's
  `in` / `range`) filter leaves answer the rows of the values given instead of no rows or a refusal; a member past the
  database's integer range of any integer transform is `FILTER_INVALID`
- [ ] 687. CHANGELOG entry for items 650 and 653: a write of an aware datetime a `DateField` cannot store, or of a
  duration past 64 bits of microseconds on SQLite / MySQL, is the field-keyed "Enter a value the database can
  represent." instead of a masked error
- [ ] 686. CHANGELOG entry for items 596 and 597: a `ProjectedChildFilter` borrowed into a set without its branch is a
  `ConfigurationError` at schema build; a flat filter key or declared filter whose name spells another branch's
  relation no longer fires that branch's permission gates
- [ ] 678. CHANGELOG entry for items 534, 535 and 536 (breaking): a `FilterSet` / `OrderSet` with an unknown `Meta`
  key, a `Meta.exclude` naming no field of the model and no `Meta.fields` entry, or a `Meta.exclude` naming a declared
  filter / `RelatedOrder` raises `ConfigurationError` instead of being ignored
- [ ] 677. CHANGELOG entry for item 531: `node` / `nodes` and model / serializer relation ids find a row whose
  decimal or aware-datetime key they spell differently (trailing zeros, exponent, UTC offset) instead of answering null
  or "Invalid id"
- [ ] 674. CHANGELOG entry for item 529: on PostgreSQL a decimal filter value outside `numeric`'s format is the
  field-keyed `FILTER_INVALID` "Enter a value the database can represent." instead of a masked error
- [ ] 901. CHANGELOG entry for item 645: async generated mutations drain abandoned running field/list siblings and
  their cancellation cleanup inside the atomic; active production masking snapshots the published error list so
  an ordinary awaiting result hook cannot expose late resolver exception text, including the standalone extension
- [ ] 671. CHANGELOG entry for item 523 (breaking): a `DjangoModelFormMutation` form declaring a built-in temporal
  field over a date, date-time or time column it cannot read (a `DateField` over a `TimeField` or `DateTimeField`
  column, a `TimeField` over a date column, ...) is refused at schema build instead of answering a masked error or
  storing midnight
- [ ] 669. CHANGELOG entry for item 577: a `SerializerMutation` save refused over a `blank=True, null=False` column the
  input left out, or a declared `allow_null` field set to `None`, answers that column's field-keyed `null` error
  instead of the `"__all__"` `constraint` error, as the model and `ModelForm` flavors do
- [ ] 667. CHANGELOG entry for item 628: a many-to-many filter leaf (forward or reverse, raw key or Relay GlobalID)
  whose through model's foreign key onto the target has a non-pk `to_field` matches by the target's primary key, as
  its wire type says; it matched the `to_field` column and returned the wrong rows
- [ ] 665. CHANGELOG entry for item 540: a serializer-flavor datetime DRF cannot place in the configured zone (a naive
  value near year 1 or 9999 under a non-UTC `TIME_ZONE`, an aware out-of-range one under `USE_TZ=False`) answers DRF's
  field-keyed `overflow` error instead of the masked top-level error
- [ ] 664. CHANGELOG entry for item 587: a lazy translation string as FilterSet / OrderSet `Meta.exclude` or OrderSet
  `Meta.fields` is refused at class creation like a bare string (it excluded by substring, excluded nothing, or was
  expanded per character); a lazy `"__all__"` stays the shorthand
- [ ] 660. CHANGELOG entry for items 392, 393, 394: the queryset seal admits a `TextChoices` / `StrEnum` where-node
  connector, seals a `QuerySet` as a pending deferred-filter value on Django 6.1 as on 5.2, and refuses a deferred
  filter nested too deeply, or a non-text model `db_table`, as a typed defect instead of a raw `RecursionError` /
  `TypeError`
- [ ] 658. CHANGELOG entry for item 389: on PostgreSQL an `ArrayField` filter element of datetimes or times whose UTC
  offset the server refuses (16:00 or more, or a fraction of a second, per binding mode) is now the coded
  `FILTER_INVALID` instead of a masked error
- [ ] 651. CHANGELOG entry for items 385, 386: a filter `in` / `range` value over a `year` / `iso_year` transform past
  the database's integer range, and a `DurationField` filter value past 64 bits of microseconds (SQLite, MySQL), are
  now the coded `FILTER_INVALID` instead of a masked error
- [ ] 649. CHANGELOG entry for items 384, 388, 398: a declared filter whose value kind differs from its column (a
  `date` on a `DateTimeField`, a `datetime` on a `DateField` or through `__date`) out of the database's range is now the
  coded `FILTER_INVALID`; a class-level `filter()` override is never run to validate a value; a class-level
  `GlobalIDFilter.filter` override's lone-surrogate value is `FILTER_INVALID`
- [ ] 648. CHANGELOG entry for item 462: on a reverse relation declared with its own `related_query_name`, the optimizer
  now keeps a consumer `Prefetch` and a related type's `get_queryset` in charge of the joined row, plans a prefetch
  beneath that relation's JOIN, and accepts a hinted `Prefetch` spelled by accessor beneath a JOIN
- [ ] 647. CHANGELOG entry for item 460: a `Meta.optimizer_hints` `OptimizerHint.prefetch(Prefetch(...))` without
  `to_attr` whose queryset is over another model than the relation's target (or a proxy of it) now fails the type build
  with a `ConfigurationError` instead of serving rows the target type refuses at execution
- [ ] 633. CHANGELOG entry for item 575: a `DjangoModelFormMutation` create whose form binds a single-value field
  over an `ArrayField` (or a `MultipleChoiceField` over a single-value column) logs the shape warning at schema
  build, as an update does, without the update's advice on the omitted field's initial value
- [ ] 632. CHANGELOG entry for item 564: four error messages drop their release number. The `RelatedFilter`
  `lookups=` error names the target FilterSet's `Meta.fields`; `Meta.connection`'s unknown-sub-key error and the
  router's missing-`django_application` hint keep their text without it; `decode_global_id`'s refusal names the
  candidate strategy's own reason (it decodes only a model-label or only a type-name payload, or is encode-only)
  instead of a callable / custom note on every rejection
- [ ] 605. CHANGELOG entry for item 604: a Relay type whose `NodeID` is a non-pk column (`house_code:
  relay.NodeID[str]`) answers an `id` selection from the row the page, join or prefetch loads (one statement
  where it cost one more per row), and the async executor no longer fails that `id` with
  `SynchronousOnlyOperation`
- [ ] 602. CHANGELOG entry for item 598: with `HIDE_FLAT_FILTERS = True` a filter input hides each
  `RelatedFilter` expansion's flat copy under whatever key a `get_filters()` override holds it, and keeps
  every filter the set holds itself, including a `Meta.fields` path spelled under a `RelatedFilter`'s name
  (now published; it had been hidden and, with no nested twin, unreachable); a head mixing the set's own
  lookup with copies keeps only its own lookups
- [ ] 600. CHANGELOG entry for item 599: a FilterSet's `get_filters()` override is now its filter table
  everywhere (own input, direct construction, nested branch, flat copies, cycles): a filter it adds filters
  where it was published and ignored, a key it renames or removes is gone from every spelling, and a cycle
  member's override reshapes what it contributes. A parent `Meta.fields` key that a `RelatedFilter` expansion
  copy also takes is now deferred like every flat copy, so an absent required child filter under that key no
  longer answers `FILTER_INVALID` on an unrelated request
- [ ] 644. CHANGELOG entry for item 374: a declared `django_filters.NumericRangeFilter`, or any one-value filter whose
  widget reads other form-data keys (a `MultiWidget` on a `CharFilter`, a consumer `Filter` over a `MultiValueField`),
  now fails the schema build with a `ConfigurationError` instead of publishing an input whose value was ignored
- [ ] 595. CHANGELOG entry for item 640: a flat filter field copied from a child set's declared filter through
  a `RelatedFilter` whose attribute differs from its `field_name` (`inSeriesHandle` over `in_series =
  RelatedFilter(..., field_name="series")`) now fires the branch gate and the child filter's own gate its
  nested spelling fires; such a query a denying `check_*_permission` refused only when nested is now refused
  flat too
- [ ] 642. CHANGELOG entry for item 515: a declared `MultipleChoiceFilter` / `TypedMultipleChoiceFilter` /
  `AllValuesMultipleFilter` publishes `exact: [<column type>!]` (it published a scalar and answered every wire value
  with `FILTER_INVALID` "Enter a list of values."); `apply_sync` with a non-list for one raises `ConfigurationError`
  where it answered `FILTER_INVALID`
- [ ] 539. CHANGELOG entry for item 519: a served `FilterSet` filter that cannot be deep-copied (a `method=` bound
  to an object holding a lock or a cache handler, such an object in `extra`) fails the schema build with a
  `ConfigurationError` naming the set and attribute; a `ListFilter(method=...)` of that kind built and failed every
  filtered request with a raw `TypeError`
- [ ] 533. CHANGELOG entry for item 558: an `OrderSet` honours `Meta.exclude` (it was accepted and ignored), so a
  set declaring it publishes fewer `orderBy` keys: a model-backed set of `RelatedOrder` branches only with `exclude`
  now also sweeps the model's columns, and a model-less one with `exclude` raises `ConfigurationError`
- [ ] 532. CHANGELOG entry for item 591: on PostgreSQL under Django 6.1, an id or relation filter value for a
  `DecimalField` with no `max_digits` past numeric's format (`"1e1000000"`) names no row instead of a masked error
- [ ] 528. CHANGELOG entry for item 556: on PostgreSQL through psycopg 3 an `ArrayField` write whose list psycopg
  cannot dump as a whole (an `ArrayField(TimeField)` list such as `[naive, aware]`) is the field's `invalid`
  `FieldError` instead of a masked error, on every write flavor
- [ ] 526. CHANGELOG entry for item 512: a declared `ListFilter` / `ArrayFilter` under DRF's `DjangoFilterBackend`
  (or any raw form data) reads `?name=a,b` as a list and `?name=` as no constraint, as the generated `in` does,
  where every value answered a 500; the generated `in`'s raw-form widget also passes a tuple through and
  reads a lazy translation string as text
- [ ] 525. CHANGELOG entry for item 547: a `date` or naive `datetime` a `DateTimeField` column holds (a serializer
  `validate_<field>` hook returning `value.date()` or a naive wall clock, an `ArrayField(DateTimeField)` date
  element) whose default-zone projection the database cannot store is the field's `invalid` `FieldError` instead
  of a masked error
- [ ] 627. CHANGELOG entry for item 511: a raw-key relation filter on a to-many key (forward many-to-many, reverse
  foreign key, reverse many-to-many) whose target type has its own `get_queryset`, or that a `RelatedFilter` walks,
  coerces each key through the target key column: a `Decimal` `NaN` / `Infinity` or an out-of-range aware datetime key
  now matches nothing instead of a masked error, and a target keyed by a one-to-one onto a non-pk `to_field` matches a
  visible key's rows instead of nothing
- [ ] 626. CHANGELOG entry for item 510 (breaking): a declared filter on `pk` or `<relation>__pk` is typed, cleaned
  and range-checked by the column the key stores, as the column's own name is: its leaf moves from `String` to the
  column's scalar, so `pk: {in: ["2"]}` over an integer key is now a GraphQL coercion error, a malformed Decimal or
  UUID value answers `FILTER_INVALID` or a coercion error instead of the masked error, and a `RangeFilter` over a
  multi-table parent link or one-to-one primary key compares its stored column
- [ ] 578. CHANGELOG entry for item 553: a `DjangoModelFormMutation` field whose widget reads several keys is bound
  under them: a `SplitArrayField` over an `ArrayField` and a `SplitDateTimeField` over a `DateTimeField` now write the
  value sent (they answered "This field is required.", or an optional `SplitArrayField` wrote `[]` and an update
  omitting it erased the stored list); a list longer than a `SplitArrayField`'s `size` answers the field's
  `max_length` error instead of being truncated
- [ ] 572. CHANGELOG entry for item 541: on PostgreSQL, a `DjangoModelFormMutation` whose optional single-value form
  field over a `blank=True, null=False` `ArrayField` cleans an empty, `null` or omitted value to `""` now answers that
  column's field-keyed `null` error instead of the masked error (a `null=True` such column answers it too, as a
  nullable non-text choice column already did)
- [ ] 561. CHANGELOG entry for item 399: a flat filter field walking a `RelatedFilter` hop runs its filter body once
  per supplied value (a consumer `method=` or `filter` override ran twice); a supplied value that constrains nothing
  (`""`) now runs the hop target type's `get_queryset` once per request on `apply_sync` too, as on `apply_async`, so
  it raises there what the nested branch and the async path raise (an unregistered hop target or an unresolved
  `RelatedFilter(None, ...)` hop: `ConfigurationError`; an async-only `get_queryset`: the `RuntimeError` naming
  `apply_async`); a projected leaf through an unresolved placeholder hop raises `ConfigurationError` instead of
  `RecursionError`
- [ ] 521. CHANGELOG entry for item 373: a `django_filters.LookupChoiceFilter` on a `FilterSet` the schema serves is
  refused with `ConfigurationError` when the schema is built (no GraphQL input carries its value plus lookup), and
  building the schema no longer writes a cached form field into any class-level declared filter. GOAL.md (the
  `BaseFilterSet` line saying every django-filter primitive carries over unchanged) may want the same qualification.
- [ ] 559. CHANGELOG entry for item 400: a `FilterSet` declaring only `Meta.exclude` now publishes the same sweep as
  `fields = "__all__"`: it gains the primary key filter and loses its forward many-to-many filter keys (declare them in
  a dict `Meta.fields` or through a `RelatedFilter` instead); and a primary key named in `Meta.exclude` is no longer
  added back under `fields = "__all__"`
- [ ] 592. CHANGELOG entry for item 509: a stored row whose value a field validator would refuse (written by
  `objects.create`, `bulk_create`, `QuerySet.update` or before the validator existed) is now found by `node` /
  `nodes`, the GlobalID filter, a generated integer `in` (and its `not`), the raw-pk relation filters and write ids,
  where it answered null, an invalid-id error or no match; a decimal id is read by value (`1.500` names `1.50`), and
  a value the backend cannot bind still names no row.
- [ ] 555. CHANGELOG entry for item 382: on PostgreSQL a filter or write value that is an aware datetime or time whose
  UTC offset the server refuses (16:00 or more; a sub-second offset under client-side binding; a datetime under
  server-side binding never) now answers `FILTER_INVALID` / the field-keyed `FieldError` "Enter a value the database
  can represent." instead of the masked error
- [ ] 513. CHANGELOG entry for item 376: a package `RangeFilter`, `ListFilter` or `ArrayFilter` declared on a plain
  `django_filters.FilterSet` (for example under DRF's `DjangoFilterBackend`) cleans each bound or element with its
  column's comparison form field, so a value the column cannot hold is the form's error (a 400 through the backend)
  instead of a database error.
- [ ] 550. CHANGELOG entry for item 423: a `DjangoModelFormMutation` built-in single-value form field (`ChoiceField`,
  `TypedChoiceField`, `CharField`, `IntegerField`, `DecimalField`, ...) over a PostgreSQL `ArrayField` now takes one
  value (a `ChoiceField` over a choice-listing base field takes the element enum) instead of the column's list, which
  its own `clean` refused, so every write through it failed; the form's `clean_<field>` turns it into the list. An
  update build warns once per such field, and the warning for 305's multiple-choice field over a single-value column is
  reworded; the default `SimpleArrayField` and every list-reading form field keep the column's list
- [ ] 548. CHANGELOG entry for item 383: a per-field `"__all__"` on a date, time, number, Boolean or UUID column no
  longer publishes the text-pattern leaves (`iExact`, `contains`, `startsWith`, `endsWith`, `regex` and their
  case-insensitive forms), so a client sending one gets a GraphQL validation error and django-filter form data naming
  one (a `DjangoFilterBackend` query string such as `price__contains=`) is ignored like any unknown key; a pattern
  lookup listed by name on such a column is now a `String` input matched against the backend's text rendering of the
  column, where it was typed by the column (or its choice enum); a column whose filter `Meta.filter_overrides` or a
  project `FILTER_DEFAULTS` supplies is unchanged
- [ ] 590. CHANGELOG entry for item 503 (breaking): `FILTER_INVALID` `extensions.errors` keys carry the field's path
  from the filter root: a leaf inside a nested `RelatedFilter` branch is `<branch>__<leaf>` (equal to the flat copy's
  key), a leaf inside an `and` / `or` / `not` arm is `and_<i>__<leaf>` / `or_<i>__<leaf>` / `not__<leaf>`, composing
  in request order, and a nested non-field error is `<path>____all__`; root-level and flat-copy keys, the message, the
  code and permission denials are unchanged. A project `apply_sync` / `apply_async` override on a `RelatedFilter`
  target that spells out the private keywords must accept `_branch_path`
- [ ] 589. CHANGELOG entry for item 586 (breaking, composite primary keys only): an update input over a model with a
  `CompositePrimaryKey` no longer offers the key's member columns in the model, ModelForm and serializer flavors, so
  re-sending them (even unchanged) is a GraphQL validation error; an update `Meta.fields` naming a member raises the
  row-identity `ConfigurationError`, and an update over a composite model with no non-key column fails at class
  creation ("narrowed the editable column set to empty"); a create still takes every member
- [ ] 588. CHANGELOG entry for item 401: a model-flavor create that leaves out a `blank=True, null=False` column with
  no default now answers that column's field-keyed `null` error (code `null`, "This field cannot be null.") instead
  of the unattributed `__all__` `constraint` error, nothing written; a `save()` that fills the column still writes
- [ ] 546. CHANGELOG entry for item 381: a write input datetime or time the database cannot store (out of the
  backend's range, an aware time on SQLite, an aware stamp PostgreSQL stores but cannot read back) is now the
  field-keyed `FieldError` "Enter a value the database can represent." code `invalid` in every write flavor, nothing
  written, instead of the masked top-level error; DRF's own `overflow` answers are unchanged
- [ ] 504. CHANGELOG entry for item 319 (breaking): a `RelatedFilter`'s flat copy of a child leaf is applied, and is
  on the parent's form, only when the request names it. A child leaf whose absence acts (`required`, a checkbox,
  `empty_value`, `null_value`, a disabled `initial`, a project `filter` that does not skip the empty value) no longer
  constrains or fails every parent request (`{}`, unrelated leaves, the nested spelling, `or` / `not` arms); it acts
  only at the set that declares it and inside an active nested branch. A project `Meta.form.clean` /
  `filter_queryset` that reads an unnamed copy's key must use `.get`
- [ ] 584. CHANGELOG entry for item 429: under `AsyncDjangoGraphQLView` (or `await schema.execute`) a plain sync resolver
  returning a lazy `QuerySet` or `Manager` to a list field answers instead of raising `SynchronousOnlyOperation` (the
  masked "An unexpected error occurred."), and the optimizer builds a sync root's plan in a `sync_to_async` worker;
  code that evaluates a queryset, or calls `apply_sync`, in a plain `def` resolver still runs on the event loop
- [ ] 582. CHANGELOG entry for item 408: a `SerializerMutation` hook may return a mapping keyed by `TextChoices` or
  `StrEnum` members, each read as its exact text; before, any key that was not exactly `str` was a
  `ConfigurationError`. The non-string-key refusal now says "every key must be a string"
- [ ] 544. CHANGELOG entry for item 424: a `DjangoModelFormMutation` whose form carries a prefix (class-level
  `prefix`, `get_form_kwargs` `prefix=`, or a `get_form` binding the package's data to a prefixed form) is now bound
  under it, so the form reads every value the client sent and an explicit `null` or a required-file clear is answered
  as on an unprefixed form; before, a class-level or `get_form_kwargs` prefix hid every sent value (required fields
  answered `required`, the rest stored defaults with a success payload) and those two checks never fired on any
  prefixed form
- [ ] 581. CHANGELOG entry for item 410: deleting an attribute of a sealed mutation `Meta` snapshot raises a
  `ConfigurationError` that no longer calls the configuration immutable; the existing CHANGELOG bullet saying "the
  sealed authorization record cannot be edited after the schema is built" makes the same absolute claim and may want
  the same narrowing
- [ ] 430. CHANGELOG entry for item 323: inside a `get_queryset` hook, `apply_cascade_permissions` /
  `aapply_cascade_permissions` now return the queryset's own `QuerySet` class (a fresh instance, same model and row
  type), so project methods chain after the cascade; the permission filter is still applied on a framework-owned plain
  rebuild, and attributes set outside Django's constructor arguments are not carried
- [ ] 396. CHANGELOG entry for item 313: a database router answering a `TextChoices` / `StrEnum` alias now routes an
  `orderBy` read instead of raising `ConfigurationError` ("an alias must be a string")
- [ ] 395. CHANGELOG entry for item 312: a `TextChoices` / `StrEnum` member used as SQL text in a hook's or consumer
  `Prefetch` queryset (`RawSQL(...)`, `Func(function=...)`, a combined expression's operator, a `Meta.db_table`, a JSON
  lookup's mapping key) is now served instead of refused with `ConfigurationError` ("cannot be sealed")
- [ ] 391. CHANGELOG entry for item 190: a temporal filter value the queryset's database cannot bind (on SQLite, MySQL
  and Oracle an aware datetime outside years 1..9999 once projected, any aware datetime when `USE_TZ` is false, an aware
  time; on every backend a `year` / `iso_year` bound outside 1..9999) now answers `FILTER_INVALID` keyed to its filter
  instead of the uncoded "An unexpected error occurred."
- [ ] 426. CHANGELOG entry for item 326: a Django `ValidationError` raised at save time on the primary key behind a
  serializer field with `source="pk"` (or a field named `pk`, or a multi-table child's parent link) is now keyed to
  that input's wire name instead of the model's primary-key name
- [ ] 425. CHANGELOG entry for item 305: a ModelForm `MultipleChoiceField` / `TypedMultipleChoiceField` over a
  single-value column that lists no choices now types as a list (`String` -> `[String!]`), so an input that sent a
  comma string (e.g. a `django_filters.widgets.CSVWidget` field) must send a list; an update build warns that an
  omitted such field binds the form's initial, which the form must present as a list
- [ ] 463. CHANGELOG entry for items 379 and 380: a consumer `Prefetch(queryset=...)` (from a `get_queryset` hook or a
  resolver) now owns its path on a forward relation (the optimizer no longer joins over it, so its filter and
  annotations apply) and onto a target type with its own `get_queryset` hook (sealed through that hook in one query
  instead of one query per parent)
- [ ] 352. CHANGELOG entry for item 343: on Django 6.1, a `get_queryset` hook or default manager returning
  `.fetch_mode(FETCH_PEERS)` or `.fetch_mode(FETCH_RAISE)` keeps that mode through the visibility seal (root lists,
  connections, nested relations, prefetch children, `node(id:)` and `nodes(ids:)`, the mutation locate), so lazy loads
  batch or raise as the project set; a fetch mode object other than Django's three is refused as an unsealable queryset
- [ ] 350. CHANGELOG entry for item 340: a `DjangoModelFormMutation` whose `ModelForm` declares a relation field with a
  class-level queryset over another model than its column's (neither the target nor a subclass) is refused at schema
  build with `ConfigurationError`, when the form keeps Django's `__init__` / `order_fields`, the mutation keeps the
  default `get_form`, and every write binds the field (any update, a create whose input requires it), instead of
  failing every such request
- [ ] 344. CHANGELOG entry for item 304: a queryset carrying a selected annotation (`Count`, `Sum`, `F() + 1`,
  `Value`, `Case`, `Subquery`, ...) whose query already fetched rows, itself or through a clone, is served by every
  visibility seal instead of being refused as "binds a function bound value" (a consumer `Prefetch` with an
  annotation, an evaluated project queryset class, a `get_queryset` hook that fetched before returning); an evaluated
  `FilterSet` / `OrderSet` `apply_*` result is refused as evaluated
- [ ] 342. CHANGELOG entry for item 303: a `DjangoMutation` write validates every uniqueness and constraint check a
  provided field joins, including declarations inherited by a proxy or multi-table child, conditional / expression
  `UniqueConstraint`s, `CheckConstraint`s and `unique_for_date` / `_month` / `_year`, answering Django's own error in
  the `FieldError` envelope instead of the generic `constraint` error (or a silent `unique_for_*` duplicate); an
  unprovided column is no longer field-validated; a `ModelForm` `to_field_name` unique through the target's parent
  builds.
- [ ] 341. CHANGELOG entry for item 295: a `ModelForm` field named after a model column but of another kind (a
  `ModelChoiceField` / `ModelMultipleChoiceField` over a non-relation column or a relation of the other cardinality, a
  file field over a non-file column, a scalar field over a file column) is refused at schema build with
  `ConfigurationError` naming both kinds, on every field the operation binds (an update binds every declared field),
  instead of writing the chosen row's `str()`, a row the type hides included, or dropping the value; a field rendered
  with a `forms.FileInput` is a file field, so a column-less one is an `Upload` input; a scalar field over a relation
  column is unchanged
- [ ] 325. CHANGELOG entry for item 163: a `DjangoType.get_queryset` hook receives an instance of the source's own
  `QuerySet` class (the default manager's, e.g. `as_manager()` / `Manager.from_queryset`), so a project `QuerySet`
  method is callable inside the hook; the hook's return is still rebuilt into a plain `QuerySet`
- [ ] 322. CHANGELOG entry for item 276: a `SerializerMutation` field whose kind disagrees with the model column it
  writes (a relation or file field over a scalar column, anything but a `FileField` over a file column, a relation over
  a scalar primary key's `pk` alias) is refused at schema build with `ConfigurationError` naming both kinds, instead of
  building as the column's kind and failing every write with "An unexpected error occurred"; a relation over a text
  primary key's `pk` alias no longer stores the related row's `str()` as the key
- [ ] 320. CHANGELOG entry for item 290: a GlobalID filter into a type whose `relay.NodeID[...]` names a
  non-primary-key column compares that column on the type's own `id` key and through every relation (forward,
  `to_field`, to-many), so the id the server emits matches its row and an id no row carries matches nothing; a node id
  that column cannot hold answers `GLOBALID_INVALID` ("... not a valid <Model> id value"); a `relay.NodeID` over a
  `get_queryset` annotation compares on the type's own rows and through a `RelatedFilter` hop, and a relation key into
  that type answers `GLOBALID_UNVALIDATABLE`. A flat leaf through a `RelatedFilter` onto a filter over a target-type
  annotation no longer fails with an unexpected error
- [ ] 317. CHANGELOG entry for item 269: a `Filter` subclass that stores its own `filter` on the instance now works
  reached through a `RelatedFilter` (flat, projected and nested) and beside one, runs inside its own filter set, and is
  never negated by the package under `exclude=True`; a GlobalID filter holding its own `filter` refuses unstorable text
  with `FILTER_INVALID` (before: a masked error, or `GLOBALID_INVALID` when its `filter` delegated to the decode)
- [ ] 315. CHANGELOG entry for item 160: a declared `RangeFilter` given only `start` (or only `end`, or the other side
  `null`) filters `>= start` (`<= end`) instead of matching no row; both bounds keep the declared lookup and a range
  with neither bound filters nothing
- [ ] 309. CHANGELOG entry for items 291 and 292: a `DjangoModelFormMutation` whose bound relation field disagrees with
  the field the input decodes against (an `__init__` or `get_form` override changing `to_field_name`, or a queryset over
  another model) raises `ConfigurationError` before validation instead of linking whichever row the bound key names; a
  relation `to_field_name` must be `pk` or a column unique on its own, refused at schema build instead of
  `MultipleObjectsReturned` or linking every row sharing the key
- [ ] 311. CHANGELOG entry for item 294: a `get_queryset` hook, manager or raw-list resolver naming a `TextChoices` /
  `StrEnum` member as an annotation or alias name, an `extra(select=)` key, a `FilteredRelation` alias, a `using()`
  alias, a `values()` field or a prefetch lookup / `to_attr` is served like its exact text instead of a visibility-seal
  `ConfigurationError`
- [ ] 310. CHANGELOG entry for items 271 and 272: a `get_queryset` hook using `extra(where=[...])` without `params=`, or
  a `TextChoices` / `StrEnum` member in `order_by` / `distinct`, `extra(order_by=, tables=, where=)` or as a raw-SQL
  parameter, is served as Django serves it instead of a visibility-seal `ConfigurationError`
- [ ] 308. CHANGELOG entry for item 241: under `ResourcePolicy` a document repeating an input-object field name
  (directly, through a fragment spread or in a variable default) is charged for every spelled occurrence, so an
  over-budget one gets the resource rejection (`max_input_nodes` / `max_container_width`) instead of reaching validation
  with the repeated subtrees uncharged; a within-budget one still gets graphql-core's "only one input field" error
- [ ] 293. CHANGELOG entry for item 137: in `DjangoModelFormMutation` and `SerializerMutation` a relation id naming a
  visible row whose `to_field` key is `NULL` is the relation error instead of silently storing `NULL` (required
  relations and many-to-many give that error instead of a field, constraint or raw error); a form `ModelChoiceField`
  whose `to_field_name` is not `pk` or a concrete field of its target is refused at schema build on any field the
  operation binds, instead of linking the row whose pk collides
- [ ] 289. CHANGELOG entry for item 133: write inputs (model, ModelForm, serializer) into a non-Relay or unregistered
  target whose primary key is a one-to-one key or a multi-table-inheritance parent link now build, typed from the column
  that key stores (0.0.14 refused the schema build); an id past that column's range on `node`, an update `id`, a relation
  id or a filter is not-found / invalid instead of an unexpected error; GraphQL type names are unchanged
- [ ] 288. CHANGELOG entry for item 285: an update or delete whose row a concurrent transaction deleted before its
  validation finished (`Meta.select_for_update = False` or no `FOR UPDATE`) is the `conflict` error instead of a field
  error about the vanished data or a masked `DoesNotExist` (serializer); a failed update / delete runs one more query
- [ ] 287. CHANGELOG entry for item 132: a `SerializerMutation` narrowed by `Meta.fields` / `exclude` /
  `optional_fields` / `nested_fields` that keeps a relation to a `Meta.interfaces = (relay.Node,)` type builds (0.0.14
  failed the schema build, or after a rebuild served a stale `Int` relation id), and a serializer relation target may be
  declared after the root `Mutation`; GraphQL type names are unchanged
- [ ] 286. CHANGELOG entry for item 282: an update whose row a concurrent transaction deleted (`Meta.select_for_update =
  False` or no `FOR UPDATE`) is the `conflict` error on every flavor instead of a re-inserted row reported as updated
  (ModelForm; model over a multi-table row) or a masked `ConfigurationError` (serializer); a ModelForm update now calls
  the form's `save(commit=False)` (work an override does only when committing does not run), and the model's `save()`
  receives `force_update` (plus `update_fields` on a multi-table row) and must pass keyword arguments through
- [ ] 283. CHANGELOG entry for item 274: a create naming a client-assigned primary key (model, register, ModelForm)
  saves with `force_insert`, so a row committed concurrently under that key is the `__all__` `constraint` error instead
  of being overwritten; a model `save()` override receives `force_insert` there, and a ModelForm `save()` override is
  called with `commit=False` (work it does only when committing does not run), as under Django's admin
- [ ] 280. CHANGELOG entry for item 111: a `SerializerMutation` field `PrimaryKeyRelatedField(queryset=...)` over a
  `GenericForeignKey` now builds and writes the queryset's model (0.0.14 failed the schema build)
- [ ] 277. CHANGELOG entry for item 109: a `SerializerMutation` relation field bound to the `pk` alias of a relation primary
  key (`PrimaryKeyRelatedField(source="pk")` over a one-to-one or multi-table parent-link key, or DRF's auto-built `pk`
  field there) now raises `ConfigurationError` at schema build for a create input (0.0.14 built it and every create
  answered a masked error); `source="<relation name>"` keeps the GraphQL name
- [ ] 57. CHANGELOG entry for item 11: model, ModelForm, plain-form and register errors, and a `ValidationError` raised
  during a serializer save, now use the input name (`categoryId`, not `category`)
- [ ] 69. CHANGELOG entry for item 1: `Meta.exclude=["parent"]` on a mutation over a `ForeignObject` model now raises
- [ ] 71. CHANGELOG entry for item 59: two `RelatedFilter`s or `RelatedOrder`s naming one relation now raise at class creation, and a
  longer one (`shelf__branch` beside `shelf`) raises at expansion when the shorter branch's target set reaches `branch`
- [ ] 75. CHANGELOG entry for item 72: a `FilterSet` or `OrderSet` shared by an MTI parent and child type now raises at finalize, and
  a concrete type's path through an FK declared to a proxy (`BranchNote.branch`) reads the bound type, not the proxy's type
- [ ] 76. CHANGELOG entry for item 62: a `SerializerMutation` whose serializer declares a flat `ChoiceField` over a grouped-choices
  column binds again (checked against the column's flattened values); a refused value now reads "which does not list it", and a
  serializer field taking a grouped column's read enum is refused with a remedy to declare a flat `ChoiceField` (over an
  `ArrayField` whose `base_field` is grouped, a `MultipleChoiceField` or `ListField(child=ChoiceField)`)
- [ ] 78. CHANGELOG entry for item 65: every single-value lookup on a choice column (`exact`, `iExact`, `contains`, `gt`,
  ...) treats each enum member as a value (`iExact: BLANK`
  matches blank rows only, a `"null"` member matches `"null"`); raw form data and declared `ChoiceFilter`s are unchanged
- [ ] 79. CHANGELOG entry for item 52: connection fields no longer send consumer-source or row-hydration exception text to the
  client; pagination rejections keep their messages and are the new public `PaginationArgumentError`
- [ ] 86. CHANGELOG entry for item 14: an explicit `in: []` on every generated membership lookup matches no rows (integer, text,
  choice, date and every other column type used to return every row); `not: {}` matches every row and `or: [{}, real]` is the real
  arm; a declared `ModelMultipleChoiceFilter` `[]` inside `not` now matches every row; raw `?x__in=` is unchanged
- [ ] 91. CHANGELOG entry for item 43: a serializer `ListField(child=ChoiceField)` publishes a list of the field's generated enum
  (clients send enum names, not strings: `[a]`, `[MEMBER_1]`), and `MultipleChoiceField(allow_blank=True)` accepts `BLANK` as `""`
- [ ] 93. CHANGELOG entry for item 44: a ModelForm mutation over a non-text choice column with `blank=True, null=False` answers
  `null` (or an omitted field with no default) with a field-keyed `null` FieldError instead of "An unexpected error occurred."
- [ ] 96. CHANGELOG entry for item 95: a nested keyset connection over a type whose `get_queryset` or manager orders pages and
  mints cursors under that order, so its cursors now replay on the root connection
- [ ] 98. CHANGELOG entry for item 51: an `OrderSet` over a forward `ForeignObject` orders it by every carrier column (a
  multi-column link no longer errors) and `Meta.fields = "__all__"` publishes the `ForeignObject` leaf
- [ ] 102. CHANGELOG entry for item 99: a connection over a type whose `get_queryset` or manager returns a `.reverse()`d
  queryset pages every row once and its cursors replay, root and nested; the order served is unchanged, an `orderBy:` beside
  such a hook stays inverted (Django `order_by()` semantics)
- [ ] 104. CHANGELOG entry for item 56: a `SerializerMutation` whose serializer has two writable fields writing one model
  field through an alias (`source="category_id"` beside `category`, `source="pk"` beside the pk field) now raises
  `ConfigurationError` at class creation, and again at runtime when `get_fields()` adds the alias
- [ ] 105. CHANGELOG entry for item 80: a connection whose source or model ordering raises (a project `QuerySet` whose `query`
  raises, a related manager on an unusable pk, a non-iterable `Meta.ordering`) is masked with the policy message and a
  `correlationId` instead of a `GraphQLError` naming the exception class
- [ ] 112. CHANGELOG entry for item 103: a `SerializerMutation` whose serializer binds a writable relation field to its
  `attname` (`source="category_id"`, or a `category_id` `PrimaryKeyRelatedField` with no `source`) now raises
  `ConfigurationError` at schema build; bind the relation instead (`source="category"`)
- [ ] 117. CHANGELOG entry for item 116: under `globalid_strategy="type"` with a `NameConverter` that renames object types,
  ids decode by the schema-published type name; `decode_global_id` and `testing.global_id_for` take an optional `schema=`
  (`global_id_for(..., schema=)` emits the published name and raises `ConfigurationError` for a type the schema does not
  publish), and the inherited-closure `type` child emits the published name
- [ ] 118. CHANGELOG entry for item 81: a `DjangoConnection` subclass whose edge class declares its own `CURSOR_PREFIX` pages
  with its own offset cursors and answers a foreign `arrayconnection:` cursor with the cursor error; stock connections are
  unchanged
- [ ] 129. CHANGELOG entry for item 87: a ModelForm mutation whose form declares a choice field narrower than its column
  publishes a generated enum of only the column values the form admits (static choices; callable and `__init__`-assigned
  choices keep the column enum), and a field admitting none of the column's non-empty values, or a `MultipleChoiceField`
  over a single-value choice column, raises `ConfigurationError` at schema build
- [ ] 134. CHANGELOG entry for item 106: a `SerializerMutation` writing a `ForeignKey(to_field=...)` through a declared
  `PrimaryKeyRelatedField` now saves (every non-null create and update was a masked error); a validator, nested write or
  custom `create()` / `update()` that re-points a validated relation's stored key is refused with `ConfigurationError`
- [ ] 136. CHANGELOG entry for item 88: a lone surrogate anywhere in a list or `JSON` input value (an element, a dict key or
  value, any depth) is a field-keyed `invalid` error at decode, keyed to the leaf's dotted path (`tags.1`; a bad dict key to
  the dict); a `JSON` value carrying one is refused on every backend, and a serializer `ListField(child=CharField())` element
  gets the package's message instead of DRF's
- [ ] 138. CHANGELOG entry for item 130: a model `DjangoMutation` or register mutation writing a `ForeignKey(to_field=...)`
  / `OneToOneField(to_field=...)`, or an M2M whose through model keys the target by a `to_field`, stores the key of the row
  its id names (it stored the pk: a wrong row, or a payload error); a visible row whose `to_field` key is `NULL` is the
  relation error
- [ ] 214. CHANGELOG entry for item 131: a `ModelForm` update omitting a declared `ModelChoiceField` without
  `to_field_name` over a `ForeignKey(to_field=...)` / `OneToOneField(to_field=...)` keeps the stored relation (it failed
  "Select a valid choice", or re-linked the row whose pk equals the stored key); an omitted generated relation field no
  longer reads the related row
- [ ] 215. CHANGELOG entry for item 61: through a `RelatedFilter` cycle each filter set publishes the same flat filters
  whichever type is registered first (a flat path ends at the first set it reaches twice); flat filter inputs on cycle
  members grow (fakeshop: +965 flat fields), none is removed
- [ ] 218. CHANGELOG entry for item 63: an offset `after` cursor near `sys.maxsize` serves the empty past-the-end page under
  `first: N`, `last: 0` or no page argument on every source (one index per page size, and on a generator source every
  index past it, raised a masked unexpected error); a page cap of `sys.maxsize` serves its rows with no page argument
- [ ] 223. CHANGELOG entries for items fixed before an entry was filed with each fix (each changes 0.0.14 behaviour;
  confirm each against the tag when writing): 2 (a negative or malformed offset cursor is refused and no longer bypasses
  the page cap), 4 (a filter lookup binds to its own filter when declared and generated names overlap), 5 (a serializer
  list's elements follow the child's `allow_null`), 13 (a consumer `Prefetch` hint over a type whose `get_queryset` hides
  rows is scoped by that hook), 30 and 31 (a flat `RelatedFilter` leaf, and a relation no `RelatedFilter` declares, no
  longer return rows the target type hides), 32 (`orderBy` through a relation no longer sorts by rows the target type
  hides), 34 (a `RelatedFilter` whose target model its relation does not reach raises at expansion), 35 (a serializer
  choice field admitting a value the column's read enum cannot represent raises `ConfigurationError` at build), 36 (a
  serializer `MultipleChoiceField` over a single-value choice column is refused at build), 38 (a `Choices.__empty__` enum
  no longer carries a `_None` member), 58 (a fragment spread is charged against `max_selections`, and only the selected
  operation's walk expands) and 60 (one `OrderSet` on two types is refused when either hides rows)
- [ ] 196. CHANGELOG entries for items 6 (combined querysets served as their pk set), 12 (the deadline message reads
  "before this field reached the database"; login, logout, me and `relay.node()` reject past the deadline; a forward FK
  / one-to-one payload hop past a spent deadline fails and rolls the mutation back, and every later subscription frame's
  relation hop fails once the stream's budget is spent), 50 and 83 (planned `.only()` writers no longer drop selected
  columns), 74 (a consumer `select_related` the selection never reads no longer errors), 15 (a hand-built range filter
  value that is not a `start` / `end` mapping or input object raises `ConfigurationError` instead of filtering nothing),
  16 (a form field basis value whose `__class__` raises is reported as an invalid field in `ConfigurationError`) and 17
  (`register_mutation()` names a protected field declared as a `str` subclass by its value; `DjangoMutationField`
  refuses a class drained by `registry.clear()` even when it compares equal to its redeclaration) and 18
  (`OptimizerHint` prefetch and strategy values, `nested_connection_strategy=`, `NESTED_CONNECTION_STRATEGY` and
  `strictness=` values whose `__class__` raises or claims `str`, and lazy proxies of a strategy or strictness name,
  raise the typed error instead of a raw `RuntimeError` / `TypeError`) and 19 (a kept serializer input field named by a
  non-identifier or a keyword is refused at class creation instead of a raw `SyntaxError` at finalize; serializer hook
  values whose `__class__` raises are typed; lazy proxies and `__class__` spoofs in hook data fail the frozen view
  closed; a non-`str` `context["write_alias"]` is a conflict) and 21-23 (field targets, factory returns, `Meta` values,
  set `Meta.fields`, input and policy helpers whose `__class__` raises or claims a type now raise the typed error
  instead of a raw `RuntimeError` / `TypeError`; `Meta.name` / `Meta.description`, a string-helper input and a
  `SESSION_ENGINE` that is a lazy proxy of a `str` are typed rejections; a lazy proxy of a class as a field target now
  reads "requires a DjangoType class") and 221 (`register_mutation()` refuses a protected field declared as a `str`
  subclass whatever its `__eq__`, and a `REQUIRED_FIELDS` that is not a list or tuple or holds a non-string entry, with
  a `ConfigurationError` naming the model instead of a raw `TypeError` / consumer exception)
- [ ] 232. CHANGELOG entry for item 92: a Django `ValidationError` raised at save time (`Model.save()` / `delete()`,
  signals, `ModelForm.save()`, `perform_mutate`, register's user save) now returns the `FieldError` envelope on the model,
  form and register flavors instead of "An unexpected error occurred." (0.0.14 masked it); whether to mark it BREAKING
  (a client branching on the top-level error sees `errors` instead) is your call
- [ ] 233. CHANGELOG entry for item 66: the nested-connection composite-index advisory (`WARNING` under `DEBUG`) no longer
  recommends an index naming a multi-table-inheritance parent's column (an inherited order or content-type column), now
  advises for orders naming `pk` or a span Django trims to a local column (`shelf__id`), and names an MTI child's
  parent-link column for an `id` order term
- [ ] 238. CHANGELOG entry for item 67: the docs state that a Django `ValidationError` raised at save time is read as naming
  the mutation's own model fields (one level, never a nested path) and that a serializer fails a nested item at save time by
  raising DRF's `ValidationError` in the nested shape (keyed `shelves.<i>.code`); the fakeshop nested-shelves create reports a
  duplicate shelf code at `shelves.<i>.code` instead of the `__all__` constraint error
- [ ] 240. CHANGELOG entry for item 97: `isNull` on a relation key over a forward `ForeignObject` (any link width), its
  reverse or a `GenericRelation` now builds a Boolean null test like a `ForeignKey`'s instead of raising django-filter's
  "unrecognized field type" `AssertionError` at `FilterSet` class creation (0.0.14 raised for every lookup on a
  `ForeignObject` key); under `unknown_field_behavior` WARN / IGNORE the leaf is now built instead of dropped
- [ ] 245. CHANGELOG entry for item 244: a lone surrogate in a text-keyed relation id or update / delete `id` is a
  field-keyed `invalid` error on every mutation flavor (0.0.14 masked it as "An unexpected error occurred.")
- [ ] 251. CHANGELOG entry for item 224: a `str`-subclass `strictness` (a `StrEnum` member) is stored as the plain mode,
  and `FilterSet` / `OrderSet` `Meta.fields` and `FilterSet` `Meta.exclude` accept `str`-subclass names as the fields they
  spell (0.0.14 refused them as "Cannot classify path" / "entries must be field-name strings")
- [ ] 253. CHANGELOG entry for item 100: a nested connection whose target orders at random (`"?"`, `Random()`) is served
  per parent with the optimizer on, as it is without it (0.0.14 raised "Cannot resolve keyword '?'" for `"?"` and
  minted wrong cursors and pageInfo for `Random()`); under `strictness="raise"` it is an unplanned N+1
- [ ] 258. CHANGELOG entry for item 252: a nested connection whose target orders by a relation name pages and mints
  cursors as it does without the optimizer (0.0.14 windowed on the key column while the page was sorted by the related
  model's `Meta.ordering`, and raised for a multi-column `ForeignObject` name); a related `Random()` ordering is served
  per parent; an order naming a one-to-one key whose model declares `Meta.ordering` gains the pk tiebreak
- [ ] 263. CHANGELOG entry for item 259: a flat `RelatedFilter` copy whose form field cleans an absent key to a value that
  filters (a consumer field class, a nonempty `empty_value`) constrains the parent connection as a full copy does (0.0.14
  dropped the constraint when the request did not name the copy); also covers 265 and 268 (a field or `filter` the
  filter's `__init__` set, a child set's own `__init__` at any depth)
- [ ] 264. CHANGELOG entry for item 260: a partial `ModelForm` update omitting a FK whose stored key names no row is that
  field's `invalid_choice` error with nothing written (0.0.14 could link the row whose form key equals the stored key); also covers
  266 and 267 (a stored or supplied single key `""` is that error instead of a clear; an M2M element `""` is decoded
  and visibility-checked)
- [ ] 270. CHANGELOG entry for item 257: a nonzero list-field `offset` over a `Meta.ordering` path ending on a
  many-to-many or generic relation is refused when the target's `Meta.ordering` is random or loops back (0.0.14 served
  the page over a random or erroring order), and served as before when that ordering is stable
- [ ] 273. CHANGELOG entry for item 181: a connection over a `get_queryset` hook or manager `extra(order_by=[...])`
  ordering serves that ordering (made total by the pk tiebreaker, reversed by `.reverse()` and `last:`) on root, keyset
  and nested connections alike (0.0.14 served the pk or `Meta.ordering` order instead, and a keyset hook that also
  called `order_by()` could repeat and skip rows); a keyset target whose extra ordering names no anchorable field gets
  the keyset order error
- [ ] 275. CHANGELOG entry for item 107: a `DjangoModelFormMutation` or `SerializerMutation` update input no longer
  carries a field that writes the primary key (0.0.14 published it and answered a masked error for another row's key),
  update `Meta.fields` naming it raises at class creation, an update whose only field is the key raises "has no fields";
  a `DjangoMutation` create takes a client-assigned key (0.0.14 left it out: a text-key create committed `""`), and a
  `db_default` column is optional on create; input type names move where explicit `fields` now equal or differ from the
  canonical shape (a canonical `<Model>Input` over a client-assigned key gains it); `build_form_inputs` is removed

## From dry-upstream-0_0_15

- [ ] 101. CHANGELOG entry for item 22: the debug-toolbar middleware and its GraphiQL bridge template are adapted from
  strawberry-graphql-django, itself based on django-graphiql-debug-toolbar; both projects' MIT license texts now ship
  beside the package's (`LICENSE.strawberry-django`, `LICENSE.django-graphiql-debug-toolbar`)
- [ ] 102. CHANGELOG entry for item 5 (spec-051 Slice 2): a Django `GeneratedField` converts, filters, orders, pages
  by cursor and refetches as a `relay.NodeID` like the column its `output_field` describes (nullable when either the
  field or its output field says so; never in a write input), where any type, `FilterSet` or `"__all__"` selecting one
  used to fail to build; a file / image output, an output no conversion publishes and an array output with element
  choices are refused at build, naming the generated field
- [ ] 103. CHANGELOG entry for item 37: under a custom `NameConverter`, form, serializer and `register` mutation
  errors key `field` / `path` to the input field names the executing schema published (the names the client sent),
  nested serializer fields included, as model mutations already did; and on DRF 3.18 a nested list serializer's item
  errors keep their camelCase child keys (`shelves.1.altBranches`, not `shelves.1.alt_branches`) under any converter
- [ ] 104. CHANGELOG entry for item 38: under a custom `NameConverter`, an update / delete mutation's `id` errors
  (`not_found`, `invalid`, `conflict`) key `field` / `path` to the name the schema published for the `id` argument
  (`ID` under an upper-casing converter) instead of the literal `id`, in every model-backed flavor
- [ ] 105. CHANGELOG entry for item 39: under a custom `NameConverter`, a connection's pagination errors (page size,
  offset and keyset cursors, `first` with `last`) and its sliced-source and `filter` / `orderBy` refusals name the
  argument as the schema published it rather than `first` / `last` / `after` / `before`

## From test-compliance-review

- [ ] 106. CHANGELOG entry: a filter value from the GraphQL input reaches the widgets of the form the `FilterSet`
  actually builds (`Meta.form`, a `get_form_class` override, a consumer widget reading other or several keys such as a
  `SplitDateTimeWidget` range axis), where it used to be written only under the filter's canonical form-data key and
  read as absent; `FilterSet.form` builds that consumer form class and binds the normalized values to its widgets, a
  subclass `__init__` editing or removing a value winning, and a flat copy is named by the keys its widget reads
- [ ] 107. CHANGELOG entry: a `ListConnection` page (the package's offset connections, root and resolved per parent,
  its keyset page, and plain Strawberry `ListConnection` fields) resolves its rows by the Python names `edges` /
  `page_info` were declared under, so a `NameConverter` respelling both, or `auto_camel_case=False` with only
  `page_info { has_next_page }` selected, no longer gets empty `edges` and `hasNextPage: false`; a `__typename`-only
  page reached through a fragment spread named `edges` fetches no rows, and an anonymous inline fragment around `edges`
  no longer raises `AttributeError`
- [ ] 108. CHANGELOG entry: under the async executor a connection selecting only `totalCount`, or only `__typename`, no
  longer fetches its node rows (the package's offset pages and plain Strawberry `ListConnection` fields)
- [ ] 109. CHANGELOG entry: a Strawberry release whose `ListConnection.resolve_connection` signature or source differs
  from the audited ones, or that no longer calls `should_resolve_list_connection_edges`, fails at app load with a
  `RuntimeError` naming the `APPLY_UPSTREAM_PATCHES = {"strawberry": False}` opt-out; that opt-out (decided at app
  load) restores the empty-page and async row-fetch defects of entries 107 and 108 on offset pages
- [ ] 110. CHANGELOG entry: beside entry 101, `FilterSet.form` adapts django-filter's `BaseFilterSet.form` (BSD) and the
  Relay `ListConnection.resolve_connection` replacement adapts Strawberry's (MIT); both license texts now ship beside
  the package's (`LICENSE.django-filter`, `LICENSE.strawberry`)
- [ ] 111. CHANGELOG entry: a `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` whose `field_name` names a
  `GenericForeignKey` is refused with a `ConfigurationError` naming the set, the filter and the field when the set
  publishes its filters (at schema build for a served set, at first use for one applied unbound), where it used to
  build and then answer every filtered request with the masked error of the `FieldError` Django raises filtering
  through it; a GlobalID filter through a `GenericRelation` is unchanged

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: CHANGELOG.md
[security]: SECURITY.md

<!-- docs/ -->
[bug-hunt-0_0_15_2]: docs/bug_hunt/bug_hunt-0_0_15_2.md
[dry-0_0_15_3]: docs/dry/dry-0_0_15_3.md
[dry-upstream-0_0_15]: docs/dry/dry-upstream-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
