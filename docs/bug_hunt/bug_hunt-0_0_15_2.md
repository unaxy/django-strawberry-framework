# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 380 done, 217 to do.

## Done

- [x] 1. Multi-column `ForeignObject` links (`fe6a6df0`, `337b3317`)
- [x] 2. Negative offset cursor, and the page-cap bypass behind it (`a57bd826`)
- [x] 3. M2M composite-index advisory names the wrong column (`269b80c0`)
- [x] 4. Filter lookups binding to the wrong field on overlapping names (`754ed263`, `9f7ea5dd`)
- [x] 5. Serializer list nulls and blank choice (`a5dc6ea3`)
- [x] 6. `reject_combined` on list-relation children: replaced by a better design (`5c5e32c5`)
- [x] 7. Directive and default-value cost charging: already fixed on main
- [x] 8. Fragment-spread cost charging: already fixed on main
- [x] 9. Cursor presence checked by truthiness: already fixed on main
- [x] 10. Mutation window under interruption: already fixed on main
- [x] 11. Mutation errors name the Django field instead of the input field (`7517eab2`)
- [x] 13. Consumer `Prefetch` hint over a type that hides rows: already fixed on main (`5d4cdb3b`, `00563dd0`)
- [x] 30. Flat `RelatedFilter` leaf returned hidden rows (`90fc7118`)
- [x] 31. Relations without a `RelatedFilter` returned hidden rows (`37dcbf70`, `eddfeab1`, `c7d0ca02`)
- [x] 32. Ordering by a hidden related row (`70118090`)
- [x] 33. spec-058 builders and `graph.apply` re-entrancy (`d58420d8`, `adacb26c`)
- [x] 34. `RelatedFilter` pointing at a model its relation does not reach (`9131486f`)
- [x] 35. Serializer choice field accepting values the column's enum can't show (`a6ace786`)
- [x] 36. `MultipleChoiceField` over a single-value choice column (`f218d7ee`)
- [x] 37. Combined hook queryset rejecting `F()` / `OrderBy` ordering (`22900492`)
- [x] 38. `Choices.__empty__` produced a `_None` enum member (`3ed5ee48`)
- [x] 39. Offset page-cap bypass (`a57bd826`)
- [x] 40. Five leads closed as not bugs (Django's own behavior in each case)
- [x] 41. `test_relations` tests failing when run alone (`cab934a0`, other session)
- [x] 58. HIGH. Fragment spreads expanded but never charged: an 857-byte request cost 1.9 s of CPU, doubling per level (`3cc1b249`)
- [x] 59. Two `RelatedFilter` / `RelatedOrder` declarations on one relation made flat leaves and order terms read the wrong one;
  a set now declares each relation once, and refuses a longer declaration that takes over a branch's paths (`ddf8ef8b`)
- [x] 60. One `OrderSet` on two types of the same model kept the first type's visibility; a second owner is now refused when
  either hides rows, as on the filter side, and a subclass binds its own owner (`8ab6c921`)
- [x] 72. A set bound to a type over a proxy model read the concrete model's primary type on a path re-entering its table; re-entry
  now matches by table, and a set shared by an MTI parent and child type is refused (`9d5e2a04`)
- [x] 62. A declared flat `ChoiceField` over a grouped-choices column was refused since item 35; the write-side check now reads the
  column's flattened values, and its refusal no longer claims a GraphQL enum exists (`bf112a0c`)
- [x] 65. `iExact: BLANK` and every other single-value lookup on a choice column dropped the predicate; every enum member now
  reaches the filter as a typed value, so `""` is never skipped and a `"null"` member is never `IS NULL` (`1f4993eb`)
- [x] 48. `BLANK_CHOICE` marker broke under copy / pickle; replaced by the `EnumMemberValue` value object (`1f4993eb`)
- [x] 52. Connection resolvers sent row-hydration and consumer-source exception text to the client; pagination validators now
  raise `PaginationArgumentError` themselves and nothing rewraps a foreign exception (`41969bc3`)
- [x] 12. Nested forward-FK / OneToOne resolvers never checked the request deadline; every package seam that reaches the database
  now checks it first, which also covers the session-auth `login` / `logout` / `me` fields and the `resolve_node` /
  `resolve_nodes` defaults Strawberry's `relay.node()` reaches (`8d4f66bd`)
- [x] 14. `in: []` matched every row on every generated `in` except GlobalID and relation keys (35 families: integer, text,
  choice, date/time/UUID/decimal, FK-id paths, nested branches, nested connection arguments), and a logical arm that constrained
  nothing was TRUE (`not: {}` no rows, `or: [{}, real]` every row). Now `[]` is the empty set as in Django, strawberry-django and
  graphene-django, an inert arm is `Q()`, a raw `?x__in=` keeps django-filter's no-constraint rule (`e09b5ef1`)
- [x] 15. `filters/inputs.py` robustness row (not a defect: the wire cannot deliver the shape): a hand-built range value the
  range filter cannot read (a list, a scalar, an object, a mapping with a key other than `start` / `end`, so also a misspelled
  lookup under a range head) dropped the constraint and `apply_sync` returned every row, against the GLOSSARY / spec-027
  promise that an unknown lookup raises; it now raises `ConfigurationError`, as the list and dict arms already did
  (`a54ad7c8`, in the body of the FBT ratchet commit)
- [x] 16. `forms/` robustness rows (not defects: application Python, no wire input). A `get_form_fields` hook value (or a
  `base_fields` value) whose `__class__` raises escaped `_form_field_basis` raw at declaration and finalize, against the
  `get_form_fields` / `_form_basis_content_identity` docstrings; it is now an invalid field in the typed error (`32b66897`).
  The eight raw `__name__` reads in `forms/sets.py` need no code: no contract row, and the label question is item 26's
- [x] 17. `mutations/` and `auth/mutations.py` robustness rows (not defects: application Python, no wire input). A protected
  `USERNAME_FIELD` / `REQUIRED_FIELDS` entry that is a `str` subclass (an enum member, or one whose repr or ordering raises)
  escaped `derive_register_fields` raw or rendered as an enum repr, against the GLOSSARY / spec-040 refusal naming the
  field; `DjangoMutationField` checked ledger membership by equality, so a drained class equal to its redeclaration built a
  schema whose requests failed. Both fixed (`b4d6e06a`). The raw `__name__` labels, the protocol probe and the Payload
  name need no code: no contract row, and the name question is item 26's
- [x] 18. `optimizer/` robustness rows (not defects: application Python and settings values, no wire input). A
  `prefetch_obj` whose `__class__` raised escaped `_require_prefetch` raw; a strategy selection or `strictness=` value whose
  `__class__` raised or claimed `str` (and a lazy proxy of a name) escaped `resolve_strategy` / `_is_valid_strictness` raw on
  every route, the `NESTED_CONNECTION_STRATEGY` setting included, against their docstrings' typed-error promises. The
  Prefetch test is now a guarded `isinstance` (subclasses and proxies still pass); the str and class tests ask the real
  type (`utils/_narrowing.py::is_str`, `is_class`) (`f788edcf`). `unwindowable_child_queryset_reason` needs no code: no
  contract row, Django-private input
- [x] 19. `rest_framework/` robustness rows (not defects: consumer hook and serializer Python, no wire input). A field-map,
  `nested_fields` or hook-return value whose `__class__` raised, a non-string hook key whose `__repr__` raised, a hostile
  `write_alias` and a hostile `save()` return escaped raw against their docstring / GLOSSARY / spec-039 typed-error
  promises; the frozen hook view passed `__class__` spoofs and lazy proxies of immutables by reference against its
  fails-closed promise; and a kept serializer field named by a non-identifier or a keyword passed class creation, then raised
  an unnamed `SyntaxError` at finalize. Mapping and Field tests are now guarded `isinstance` (proxies still pass); the
  freeze, the alias and the saved result ask the real type; renders use the guarded repr; kept input names are checked at
  class creation, root and nested (`5cbe15de`). The raw `__name__` labels need no code (item 26's); `_error_node_children`'s
  `str(key)` needs none: no contract row, and DRF keeps detail keys as given
- [x] 20. Filter and order set robustness rows (not defects: application Python, no wire input). The `Meta.fields` shape
  gate let a value whose `__class__` raises escape raw on both families (fixed with item 23). The rest need no code: the
  set-class, owner and Filter-class name reads are message labels (item 26's question), and a hostile `__eq__` / `__ne__`
  on `Meta.fields` or a raising `__bool__` owner in `resolve_lazy_class` meets no contract row (django-filter and
  django-graphene-filters read them the same way)
- [x] 21. `list_field.py` and `routers.py` robustness rows (not defects: application Python, no wire input). A field target
  whose `__class__` raised or claimed `type`, or whose registry lookup or replaced definition raised, escaped
  `_validate_djangotype_target` raw on all four field factories against its docstring and spec-020 Decision 5; a factory
  return whose `__class__` raised escaped `_factory_application` raw against spec-046 Decision 11. The class test now asks
  the real type (`is_class`), both definition reads sit inside the contained read with `origin` read only off the
  registry's own definition, and the coroutine test is a guarded `isinstance` (a lazy-proxied coroutine is still closed)
- [x] 22. `types/` robustness rows (not defects: application Python and settings, no wire input). A `Meta` value or entry
  whose `__class__` raised or claimed a type (`model`, `name`, `description`, `primary`, `connection`, `cursor_field`,
  `relation_shapes`, `globalid_strategy` and `RELAY_GLOBALID_STRATEGY`, `interfaces`, `fields` / `exclude` and the other
  field sequences, `optimizer_hints`), a class attribute shadowing a model field, a non-string annotation key whose
  `__repr__` raised, and a `resolve_id_attr` result that is not really a string escaped raw against the GLOSSARY /
  docstring typed-error promises. Each gate is now a guarded `isinstance` (lazy proxies still pass), `Meta.name` /
  `Meta.description` and annotation keys ask the real type, keys render through the guarded repr, and the
  `resolve_id_attr` result is normalized inside its fail-closed guard. Labels, hostile iteration, `__mro__` reads and
  hostile `str`-subclass methods need no code (no contract row)
- [x] 23. `utils/` robustness rows (not defects: application Python and settings, no wire input). A `Meta.fields` whose
  `__class__` raised now gets the typed re-readable rejection on both set families (`canonicalize_set_meta_fields`,
  `FilterSet.get_fields`, `is_re_readable_field_declaration`); `normalize_field_name_sequence`,
  `filter_input_type` / `order_input_type`, the string helpers, `session_store_class`, `resolve_policy`,
  `validated_field_directives`, the `ValidationError` mapper, the input-walk field name and depth label, and the SQL
  statement classifier now keep their documented typed outcome for a value whose `__class__` raises or claims `str`. The
  dynamic-set-class rows were stale (code deleted in `899cb35b`); the `__name__` labels in `utils/inputs.py`,
  `querysets.py` and `write_transaction.py` and the depth-cap knob reads need no code (no contract row)
- [x] 24. Trailing-comma lint rows: t3-only (both were in t3's own hunks); `scripts/check_trailing_commas.py --check` passes on
  main
- [x] 25. Stale test-fixture row: already fixed on main (`a01a2ab8` gave the proxy-target fixtures a private `Meta.apps`)
- [x] 27. Unfiled robustness leads: the `str(key)` and `save()` repr leads were item 19's; the annotation-key, cursor-field,
  adjacent-gate and `__mro__` leads were item 22's; the `Meta.fields` liar was item 23's; the cross-model unwired subclass
  is item 73's question. The relay-seam `__mro__`, `resolve_lazy_class` `__module__` and the orders-skip-unknown-key
  divergence need no code (no contract row; hand-built input only for the last)
- [x] 28. Deep dive 3 (authorization on deferred paths): findings 12 and 13 done; `VenueBadgeType` and `VenueSponsorType` now
  hide marked rows, and live rows prove none leaks through the no-`related_name` reverse accessors (`16a8c179`)
- [x] 50. A SKIP hint (and a consumer-assigned relation, and the nested-connection SKIP arm) left the relation's key column out of
  `.only()`, so each row refetched it before the relation's own query (2N+1, async errors on a non-pk link); every traversed
  relation now keeps its link columns, as does a consumer `prefetch_related` (generic foreign keys included) (`548059b3`)
- [x] 74. A consumer `select_related` the selection never reads made the optimizer's `.only()` defer the column the JOIN traverses
  (masked "cannot be both deferred and traversed", even for `{ allLibraryPrefetchedBooks { title } }`); the `.only()` writers now load
  each joined row whole: root, planned children, scalar-only nested windows, both one-to-one directions, second hops (`13de7c4c`)
- [x] 83. A consumer `.only()` / `.defer()` met the plan's projection badly on both sides: the root dropped the plan's columns
  (every selected column outside the consumer's set lazy-loaded per row, async errors) and a planned child replaced its hook's
  `.only()`. Both now load the union under a `QUERY` operation; a hook's `prefetch_related` no longer collides with the
  planned `Prefetch`, and `{ allLibraryPatrons { name card { __typename } } }` no longer hits the masked FieldError shipped
  since 0.0.7 (`548059b3`)
- [x] 42. `auto_camel_case=False` keeps every generated input camelCase (82 mutation, 3,487 filter, 124 order fields) while
  Strawberry-owned names follow it; FieldError keys still match the published names. Not a defect under rule 37 (no shipped doc
  says inputs follow the converter): the maintainer's 2026-09-25 decision already homes it on `TODO-BETA-077-0.1.7`, no code
- [x] 43. A serializer `ListField(child=ChoiceField(...))` published `[String!]`; it now publishes the field's generated enum like a
  `MultipleChoiceField`. Fixed with it: `MultipleChoiceField(allow_blank=True)` refused its own `BLANK` (list members reached DRF
  unwrapped); `raw_choice_value` now unwraps a list element-wise (`a9dec21d`)
- [x] 44. A `DjangoModelFormMutation` over a non-text choice column with `blank=True, null=False` answered `null` (or an omitted
  field with no default) with a masked top-level error, since `form.save()` raised `ValueError` / `ValidationError`; it now returns
  the field-keyed `null` FieldError the model flavor gives. Django keeps the shape on purpose, so no startup check (`6c31c5e3`)
- [x] 49. `serializer_field_description` converts (does not re-raise) a `KeyboardInterrupt` from hostile field metadata into
  `ConfigurationError`, by design and pinned since `3470fb7f`. Not a defect under rule 37 (no contract row, application Python, no
  wire input), no code; the package-wide policy question is item 94
- [x] 95. A nested keyset connection whose target `get_queryset` (or manager) orders differently from `Meta.cursor_field`
  windowed by that order but sought and minted by the declared one, so a forward page 2 silently dropped rows; the window now
  derives its cursor vocabulary from the order it pages by through the resolver the root uses (`5197d03d`)
- [x] 51. An `OrderSet` leaf over a multi-column forward `ForeignObject` raised a masked `FieldError` on every `orderBy`, and
  `"__all__"` dropped every forward `ForeignObject` (a side effect of `7000d920`); a leaf now orders by one term per carrier
  column as Django's `order_by` does, `"__all__"` publishes it again, and a link naming no visible target sorts as missing
  instead of being dropped by an inner join (`0eb96efe`)
- [x] 99. A connection target whose `get_queryset` (or manager) returns a `.reverse()`d queryset compiled reversed SQL while
  the keyset seek, the minted cursors and the optimized nested window (keyset and offset) read the forward terms, so pages
  repeated and lost rows with no error; the order ladder now materializes the reverse of the forward total order as explicit
  terms first, keeping the page-1 `ORDER BY` byte-identical (`b005a7ee`)
- [x] 56. Two writable serializer fields aliasing one model field (`category` beside `source="category_id"`, a pk field
  beside `source="pk"`) passed every ownership guard, which compared spellings; the class-creation guard, the input walker
  and the runtime guard now key a source by the model field it resolves to, at every depth (`bcfe561e`)
- [x] 80. Four connection catches turned a consumer source or `Meta.ordering` fault into a deliberate `GraphQLError` naming the
  exception class (no `correlationId`, no log line); they are deleted, so the fault reaches the error policy as itself and is
  masked with a `correlationId`, as on the list field and the optimized nested path (`29c1f670`)
- [x] 81. A `DjangoConnection` subclass whose edge class declares its own `CURSOR_PREFIX` (mounted with `relay.connection`)
  refused its own offset cursors past page 1 and served or masked a foreign `arrayconnection:` cursor; every offset decode
  now reads the connection's own edge-class prefix, so it pages and a foreign cursor gets the cursor error (`23a9229c`)
- [x] 87. A ModelForm field over a choice column published the column's read enum whatever the form admitted, so a declared
  narrower `ChoiceField` advertised members the form refused; it now publishes exactly the column values the form's own
  `valid_value` admits (a generated `<InputTypeName><FieldName>Enum` when fewer), and a field admitting no non-empty column
  value, or a `MultipleChoiceField` over a single-value choice column, is refused at schema build (`889e7c7a`)
- [x] 103. A writable relation field bound to its `attname` (`cat = PrimaryKeyRelatedField(source="category_id")`, or a
  `category_id` field with the source defaulted) published a create input every request failed with a masked TypeError; it
  is refused at schema build with the remedy `source="category"`, root, nested and injected (`f8ff159c`)
- [x] 116. Under `globalid_strategy="type"` a `NameConverter` that renames object types broke GlobalID round trips: ids
  carried the converted name while `node`, `nodes`, mutations and GlobalID filters decoded by the plain name (refused, or
  another type's rows read and written on a collision); they now decode by the executing schema's published name
  (`e05b2436`)
- [x] 119. Two `prove_failability.py` runs on one tree could both own it: `RUN.lock` was created empty and its pid
  written after, so a second run read no pid, unlinked the lock as stale and claimed it (a silent 0-row proof, or a
  mutation left in the tree with a passing restore proof), and a run without `--scratch-root` took no lock at all; a
  kernel `flock` on the repository root is now held for the whole run (`ce338eec`)
- [x] 106. A `to_field` ForeignKey written through a declared `PrimaryKeyRelatedField` failed every non-null create and
  update (the attestation compared the stored `to_field` value with the pk) and, with an integer `to_field`, passed a
  wrong-row write; the snapshot captures the key the relation stores, the walk refuses it re-pointed in place and the
  attestation compares the column with it (`4ce779e1`)
- [x] 88. A lone surrogate inside a list element or a JSON key or value skipped the decode text preflight (top-level `str`
  only) and reached the backend raw as a masked top-level `UnicodeEncodeError` (fakeshop `setCardFiles` paths; on Postgres an
  `ArrayField` of text or an `HStoreField` in every write flavor; a serializer `ListField(child=CharField())` element was
  already refused by DRF); the preflight now walks every list element and dict key and value, keyed to the leaf's dotted path
  (`ea0eea70`)
- [x] 130. A model `DjangoMutation` (and register) wrote the related pk into a `to_field` relation's column: a wrong row
  linked silently (including one the visibility scope hides) or a payload FieldError, for a FK, a OneToOne and an M2M whose
  through model's target-side foreign key has a `to_field`; the one visibility query now also reads the key the relation
  stores and that key is written (`6a8713d6`)
- [x] 89. The serializer refusal of a field taking a grouped-choices column's read enum offered "declare a flat
  ChoiceField" over an `ArrayField` whose `base_field` is grouped too, where a `ChoiceField` writes one value into the list
  column; over such an array it now names a declared `MultipleChoiceField` or `ListField(child=ChoiceField)`, each element
  checked against the `base_field`'s flattened values (`6f1a6cd4`)
- [x] 139. Two `workspace.py` runs of one address started during the copy's first sync both synced it: the second decided
  its sync before waiting for the copy's lock and resynced over the first run's edits (silently, its header said "copy is
  fresh"); a killed `--fresh` sync left the copy marked ready and half-mirrored, and a run whose copy was released while it
  waited ran in another address's copy; the sync is now decided under the copy's lock, every sync marks the copy syncing
  first, and a run whose copy no longer holds its address refuses with exit 125 (`4ed767bb`)
- [x] 140. `workspace.py release` and `gc` probed a copy's lock, dropped it and then unbound or deleted: `gc` without
  `--force` deleted active work (about 98% of runs started with it), deleted the lock files a waiter held so two runs owned
  one copy, and a probe or a racing run recreated an unmarked flow folder; every command now holds a shared lock on the
  flow folder, `gc` holds it exclusive through the removal (marker last), `release` keeps each copy's lock through its
  state write, `lock_is_busy` and `gc --force` are gone (`4ed767bb`)
- [x] 90. Nested list-of-choice serializer shapes (`ListField(child=MultipleChoiceField)`,
  `ListField(child=ListField(child=ChoiceField))`) publish `[[String!]!]` by spec-039's one-level peel
  (`serializer_choice_source`). Not a defect under rule 37 (no contract row: spec-039 states `list[list[str]]`; no wire input
  writes a wrong value): they are reachable only as serializer-only fields, DRF checks every leaf with a field-keyed error
  (`f.0.0` under `ListField(child=ListField(child=ChoiceField))`, `f.1` under `ListField(child=MultipleChoiceField)`),
  declared over any column they are refused at build, and neither graphene-django nor strawberry-django types nested choice
  lists as enums; no code. Found probing it: items 151-154
- [x] 128. `testing/relay.py::global_id_for` annotated `schema` with a `TYPE_CHECKING`-only `Schema` in a module without
  `from __future__ import annotations`, so importing the public module raised `NameError` on Python 3.10-3.13 (the CI floor
  cell failed collection; nothing static caught it); the annotation is quoted (`7413c7b5`) and ruff `TC004` (quoting fix)
  now fails an eager annotation naming a `TYPE_CHECKING`-only import (`1cee08c4`); unreleased (no CHANGELOG
  entry). Found fixing it: item 212
- [x] 131. A ModelForm update that omitted a declared `ModelChoiceField` without `to_field_name` over a
  `ForeignKey(to_field=...)` / `OneToOneField(to_field=...)` refilled it with the stored `to_field` value where the field
  resolves by pk: "Select a valid choice" on every such partial update, or, when that value equals another row's pk, a
  silent re-link to that row (including one the related type hides); the refill now reads `model_to_dict` only when the
  form field's key names the column the FK stores, and otherwise rebinds the related row by the field's own key, as a
  provided value decodes (`b2f8d05c`). Released in 0.0.13 and 0.0.14: item 214
- [x] 61. `RelatedFilter` cycles (two or more `FilterSet`s, and sets pointing into one) published flat filters decided by
  which type registered first: the first-expanded set's re-entry fallback was cached into every other member, so a flat
  filter validated in one registration order and was unknown in another (fakeshop's library inputs moved with it). A flat
  path now follows `RelatedFilter`s until it reaches a filter set already on it, whose own filters end it there, so each set
  publishes one surface in every order, the largest any order published (`6b5d43d4`); CHANGELOG item 215; filed 216, 217
- [x] 63. An offset `after` cursor whose page ended on `sys.maxsize` failed Strawberry's last-only `assert last is not None`
  (the cursor at `sys.maxsize - 1 - N`, N the page the engine is handed: `first: N`, `last: 0` as `first: 0`, the cap with no
  page argument), and one ending past it overran `islice`'s stop on a generator source or a 64-bit `LIMIT` under a
  `sys.maxsize` page cap: a masked unexpected error on root, consumer-resolver and per-parent connections, sync and async.
  `offset_engine_arguments` now hands the engine every forward page ending at most at `sys.maxsize - 1`, so every accepted
  cursor serves the past-the-end page the optimized window serves (`60825338`); CHANGELOG item 218; filed 219
- [x] 64. Not a defect at HEAD (every malformed offset cursor answered the cursor error), but the decoder's `isascii` term
  was load-bearing, not redundant: `str.isdigit` admits 128 digits `int()` raises on (U+00B2), which without it escaped as a
  masked error on every entry point and past the planner's `PaginationArgumentError`-only catch, and no test failed. The
  decoder now matches the index against `0|[1-9][0-9]*` in full (same accepted set); live rows pin the superscript and the
  mixed non-ASCII digit on the root, and every malformed cursor on the planned nested `booksConnection` window (the nested
  field's `errors[].path`, no window statement)
- [x] 66. The composite-index advisory recommended child-table indexes on columns the child's table does not hold: an MTI
  child declaring its own FK or generic link and ordered by an inherited column (explicit order, `Meta.ordering`,
  `Meta.cursor_field`) was told to add `(holder_id, name, ptr)`, which Django refuses (models.E016), and a generic link whose
  content type sits on the parent got `content_type_id` named on the child. The advisory now resolves every column it names
  as the window does (`Query.resolve_ref`, the query's base table only) and stays silent when any lives off the child's
  table; `pk` orders and spans Django trims to a local column now advise, and an MTI `id` names the parent-link column;
  CHANGELOG item 233; filed 234, 235
- [x] 67. A Django `ValidationError` names no model and no nested item, so a save-time error about a child or related row
  was re-keyed through the backing model's map (a child's `name` landing on the root's renamed `title`, on every flavor)
  while the README, spec-036, spec-039 and the GLOSSARY promised the input the client sent at every depth. The docs now state
  the backing-model reading and the route for failing a nested item at save time (DRF `ValidationError` in the nested shape,
  keyed `shelves.<i>.code`, shown by the fakeshop nested-shelves `create()`); the save-time key map is one level (it built an
  unread child map against the root model). No package wire key moves; CHANGELOG item 238
- [x] 70. Robustness, not a defect (no contract row bounds the admission walk's CPU): a shape walk passed over every
  directive of a node at every fragment expansion, though an argument-less one charges nothing, so 500 spreads of a fragment
  carrying 1495 bare directives (3999 tokens, default policy) walked 85 ms before validation and were admitted (1.8 s at 4x
  tokens and selections). A node's directives are now read once and only those carrying arguments are revisited, each
  charging at least one input node (0.6 ms; 2.5 ms at 4x); no verdict changed across 23,650 differential documents; filed
  241
- [x] 188. Re-checked at `8ca6a481`: a nested list whose `get_queryset` returns `union()` / `intersection()` /
  `difference()` no longer raises `NotSupportedError`; the combined result is served as its pk set, optimizer on and off
  (`5c5e32c5`, item 6; `test_combined_visibility_api.py` 199 passed)
- [x] 189. Re-checked at `8ca6a481`: an overlapping declared and generated lookup runs the generated one, two lookups on
  one key both apply, and `{"id": {"gt": 999}}` on a generated-only field filters (`754ed263`, `9f7ea5dd`, item 4)
- [x] 192. Re-checked at `8ca6a481`: an `allow_blank` serializer `ChoiceField` publishes a `BLANK` member that writes `""`
  (`a5dc6ea3`, item 5)
- [x] 195. Re-checked at `8ca6a481`: `test_audit_marks_target_parse_failure_as_incomplete` and the three `async_executor`
  rows in `tests/utils/test_querysets.py` pass; no fix commit identified (possibly stale when filed)
- [x] 92. A Django `ValidationError` raised at save time (a consumer `Model.save()` / `delete()`, a save / delete /
  `m2m_changed` signal, `ModelForm.save()`, `perform_mutate`, register's user save) reached the client as a masked
  top-level error on the model, ModelForm, plain-form and register flavors, while the serializer flavor mapped it; every
  flavor now returns the `FieldError` envelope, keyed like `full_clean()` / `form.errors` and rolled back, through one
  catch in `mutations/resolvers.py::save_or_field_errors` (plus the forced-update and delete wrappers), with no new
  savepoint and no query-count change; a `ValueError` still propagates. The kanban example's hand-written mapping is gone;
  CHANGELOG item 232; filed 230, 231
- [x] 97. `isnull` declared on a relation key django-filter's table does not name (a forward `ForeignObject` of any link
  width, its reverse, a `GenericRelation`) raised "unrecognized field type" at class creation (dropped under WARN /
  IGNORE) while a `ForeignKey` built a `BooleanFilter`; `filters/sets.py::FilterSet.filter_for_lookup` now replays
  upstream's isnull branch from the merged `BooleanField` selection for those keys (`_null_test_filter_for_relation`),
  so every relation key's `isNull` is a Boolean null test (carrier columns on the raw path, "no visible related row" on
  a scoped target, as on a `ForeignKey`); the policy table still mirrors django-filter. Live row: fakeshop
  `ShelfLabelFilter` `shelf` through the new `allLibraryShelfLabelsFiltered` root; CHANGELOG item 240; filed 239
- [x] 211. A repo-wide `ruff check --fix .` / `ruff format .` rewrote untracked hunt evidence; `[tool.ruff]` now
  `extend-exclude`s `hunt-ws`, so ruff checks only the tracked tree (git-ignored copies such as `.claude/worktrees/` were
  already skipped); `docs/ruffing.md` "Files ruff skips" says so
- [x] 208. Not synced: the hunt worktree `t3code-1cc21548` and its branch are removed (0 commits ahead of main). The
  whole tree, `hunt-ws/` evidence and untracked records included, is archived in `~/t3code-1cc21548-final-2026-10-15.tgz`,
  its uncommitted diff in `~/t3code-1cc21548-uncommitted-2026-10-15.patch`; the remaining cleanup decisions are item 242
- [x] 209. Moot: the owned-changes ledger belonged to the removed hunt worktree (archived with it, item 208)
- [x] 210. Not taken to main: every robustness row it served is decided on main; the migration survives only in item
  208's archive
- [x] 213. The `filters/` docstrings and comments (`filters/inputs.py` x3, `filters/base.py`, `filters/sets.py`) and the
  `tests/filters/` docstrings that narrated an earlier implementation ("previously", "used to", "the old", "before the
  fix", "pre-gate") state the invariant instead; 25 `test_c4_` / `test_r6_` names lose the review label
- [x] 221. `derive_register_fields` reads `USERNAME_FIELD` and every `REQUIRED_FIELDS` entry as plain text (real-type
  `str` gate, base-slot read and iteration), so no consumer dunder decides the dedup or the protected refusal and the
  derived tuple holds base `str` only; a `REQUIRED_FIELDS` that is not a list or tuple (Django's `auth.E001`) or a
  non-string entry raises `ConfigurationError` naming the model; spec-040 Decision 6 and Test plan say so
- [x] 222. Class membership over class objects is an identity scan wherever a consumer metaclass reaches it:
  `TypeRegistry.register` / `_detach_type_from_model`, `FilterSet._filters_along`, `apply_interfaces`,
  `guard_nested_recursion`, `apply_cascade_permissions`, the auth `permission_classes` conflict key and the
  `GeneratedInputArgumentsFactory` subclassing check; an always-equal or raising metaclass `__eq__` no longer drops a type,
  removes the wrong one, truncates a flat filter path, drops an interface, reports a false cycle, admits a different
  permission set or escapes raw; specs 001, 015, 018, 027, 034, 039 and 040 say so (before Python 3.12 `inspect` still
  compares a class with `type` / `object` by equality when Strawberry reads its signature)
- [x] 244. A lone surrogate in a raw relation id over a text-pk target (`editionId: "\ud800"`, a `boundWith` member) or
  in an update / delete `id` over a text-pk non-Relay primary escaped as the masked "An unexpected error occurred." in the
  model, form and serializer flavors (the text preflight ran on scalar leaves only): `type_check_relation_id` and
  `coerce_lookup_id` now run it on the coerced pk before any query, keyed `editionId`, `boundWith.<i>` or `id`, `invalid`;
  well-formed non-ASCII ids still write; fakeshop gains `Printing.bound_with` and the Printing / Edition write mutations
  that reach it; specs 038 and 039 say so
- [x] 224. A `str`-subclass value (a `StrEnum` member, an honest subclass, one whose `__eq__` lies or raises) is read as
  its text: `DjangoOptimizerExtension(strictness=)` stores the vocabulary's own constant, so a lying `__eq__` no longer
  disarms the N+1 guard and a raising one no longer fails every request; `FilterSet` / `OrderSet` `Meta.fields` (list,
  tuple, set, dict keys and lookup values, `filter_fields`, `"__all__"`, any re-readable collection) and `FilterSet`
  `Meta.exclude` read through `utils/inputs.py::plain_set_meta_fields`, so the field its text spells is filtered,
  ordered or excluded instead of refused with a false message or escaping raw; a plain declaration keeps its identity
  and kind; specs 027 and 028 say so
- [x] 100. A random order on a nested connection's target (`"?"` from a hook or `Meta.ordering`, a `Random()` bare,
  composed, behind an alias / `F` / transform, or read in a `When` condition) went into the optimizer window, which
  evaluates the order up to three times per statement: `"?"` raised a masked "Cannot resolve keyword '?'" at plan time
  (the whole root field lost) and `Random()` served wrong cursors and pageInfo, while the root and the optimizer-off
  path served both; `optimizer/plans.py::has_random_term` now leaves such a relation to the per-parent pipeline
  (strictness-visible, a keyset target keeps its own error and its `cursor_field` window), a condition's string value
  stays a literal; spec-033 lists the arm
- [x] 101. `manage.py import_spec_terms --check` was red: spec sweeps rewrote terms CSVs without the writing importer
  (14 extra / 5 missing rows on 8 done cards, 119 order shifts, 462 stale `notes`), and `--check` compared anchors only,
  stopped at the first card and missed orphans; it now passes exactly when the writing run writes nothing (every
  written column, every card and planning error in one run, orphan mentions reaped, no restamp of unchanged rows), a
  pre-commit hook and the CI lint step run it, `check_spec_glossary.py` refuses a repeated anchor, the DB is re-synced
  and card 056 / 053 board text it falsified is corrected
- [x] 107. `DjangoModelFormMutation` and `SerializerMutation` published the model's primary key (a one-to-one
  `primary_key=True`, a text key, a serializer field whose source resolves to it) on the update input, so another row's
  key wrote that row and the post-write guard answered a masked error, while `DjangoMutation` dropped every key on
  create too (a text-key create committed `""` and the next one overwrote it); an update input now never carries the
  primary key (update `fields` naming it raises at class creation, `exclude` naming it is accepted), a model create
  takes a client-assigned key under the default / `db_default` required rule (a `db_default` column is optional), a
  nested serializer field and a non-editable form key are not the key, `build_form_inputs` is gone; specs 036, 038, 039
  say so
- [x] 110. The item-56 alias message labelling an owner `'category_id' (source 'category_id')`: not a defect (cosmetic,
  no contract row): the label comes from `rest_framework/inputs.py::raise_writable_source_ownership_errors` and the
  refusal stays the typed `ConfigurationError`
- [x] 113. The consumer pipeline running before the deadline on a connection: duplicate of 114; `8d4f66bd` documents
  `get_queryset`, `check_*_permission` and consumer `FilterSet` / `OrderSet` running before the deadline as trusted
  application code
- [x] 115. Item 12's hot-path AFTER number and a `check_deadline` early return: not a defect (an unmeasured
  micro-optimization; no contract row, only a budget figure)
- [x] 122. `prove_failability.py`'s shared `pristine/<label-digest>__<path>` name per tree: not a defect: the tree lock
  excludes concurrent runs, so no two runs hold the path at once
- [x] 124. ModelForm: an explicit `null` on a non-required choice field or `CharField` over a non-blank text choice
  column stores `""`: not a defect (upstream-matching): Django's `BaseModelForm._get_validation_exclusions` skips model
  validation of an empty value on a non-required form field, and the write rolls back
- [x] 125. ModelForm: no check that a declared field's kind agrees with its column: a defect, superseded by 295 (the
  build refuses a field of another kind than its column on any field the operation binds; a scalar field over a
  relation column agrees)
- [x] 126. A plain `Form` `ChoiceField` publishing `String`: not a defect (upstream-matching): graphene-django's
  `forms/converter.py::convert_form_field_to_string` registers `forms.ChoiceField`
- [x] 127. Lead: a serializer single `ChoiceField` over an `ArrayField` skipping the column's choice check: not a
  defect: a hand-declared single `ChoiceField` cannot write an array column at all (item 45 holds the save failure)
- [x] 144. `workspace.py gc`'s Postgres `stop_if_idle` racing another flow's database create: not a defect:
  `scripts/workspace.py` makes no cross-flow promise and the next run recreates the database
- [x] 148. `scripts/census_test_models.py::_import_map` folding imports into one flat map: not a defect: a documented
  approximation (`_census_tree` states the flow limit, `FACTORY_BEFORE_REBINDING_SEES_FINAL` pins it) that no gate
  depends on
- [x] 151. A declared choice field over a nested `ArrayField(ArrayField(<choices>))` building: not a defect
  (infeasible): a misconfiguration, since the declared field cannot describe a 2-D column;
  `rest_framework/serializer_converter.py::_model_backed_scalar_annotation` returns the declared enum before the nested
  refusal
- [x] 152. `ListField(child=ChoiceField(allow_null=True))` over an `ArrayField` whose element is NOT NULL storing a
  `null` element: not a defect (intended): the declared `allow_null` is the contract and
  `rest_framework/serializer_converter.py::_reject_choice_values_the_column_does_not_list` leaves `None` to it
- [x] 153. A `get_fields()` / `Meta.extra_kwargs` field read as generated, not consumer-declared: not a defect
  (intended): `rest_framework/serializer_converter.py::_is_consumer_declared` fails closed (every mismatched write is
  refused field-keyed) and declaring the field publishes its own type
- [x] 154. `rest_framework/inputs.py::_fingerprint_converter_extra` missing a nested `ListField` leaf drift: not a
  defect: only a nondeterministic `get_serializer_for_schema()` reaches it and schema construction still fails loud;
  `rest_framework/inputs.py::serializer_schema_fingerprint`'s docstring over-promises with "This captures EVERY axis the
  generated input / SDL / reverse map depends on"
- [x] 156. `CaptureQueriesContext` recording no queries on the async transport: not a defect: Django's
  `CaptureQueriesContext` cannot see the asgiref worker thread's connection, and no async query-count assertion relies
  on it
- [x] 157. A winning consumer `Prefetch` issuing more queries optimizer-on than off: not a defect (intended): spec-035's
  consumer-wins rule (`optimizer/plans.py::diff_plan_for_queryset`); BACKLOG B8 holds the opt-in merge
- [x] 159. A combined default manager left unplanned on the nested-relation path: not a defect: the designed fallback
  (`optimizer/nested_fetch.py` returns `"combined"`, served per parent); such a manager breaks Django's own related
  managers too
- [x] 164. Fakeshop's plain `strawberry.field` QuerySet roots raising `SynchronousOnlyOperation` on `/graphql-async/`:
  duplicate of 53 (a hand-written `@strawberry.field` returning a QuerySet runs synchronously)
- [x] 167. Native `relay.node()` failing on a model-label GlobalID: not a defect (intended): spec-032 Decision 3
  dispatches root node fields through the package decode because native `relay.node()` looks ids up by GraphQL type name
- [x] 168. `types/relay.py::_resolve_id_default` lazy-loading a deferred `NodeID` column: not a defect: only a consumer
  `.only()` defers it, which is application configuration
- [x] 169. `workspace.py release` / `gc` raising `NotADirectoryError` on a regular file at the flow path: not a defect
  (infeasible): only a hand-planted file reaches `scripts/workspace.py::_lock_flow_dir`
- [x] 171. No tool measuring coverage of a diff's changed lines: not a defect (a tooling wish, no broken contract)
- [x] 172. START.md's resource-gate probe: not a defect: `pgrep -fl '[p]ytest|[b]asedpyright'` does not match itself and
  the `memory_pressure` reading works, erring conservative
- [x] 175. spec-050 Decision 9 saying only "a positive offset raises the low mark": not a defect: incomplete, not false
  (row 21, C19, states the high mark)
- [x] 176. Async nested connection under a `DjangoListField` root leaving a coroutine: already fixed: not reproducible
  at `43208c0c` on either schema, optimizer on and off
- [x] 177. The test clients refusing a nested non-dict `Mapping` in `variables`: not a defect (upstream-matching): the
  variables go through `json.dumps`, which refuses it as upstream test clients do
- [x] 179. Test strength (the C31 ledger lock row, the C9 gate's `typing.cast` blind spot, a mocked `fcntl.flock` row):
  not a defect: no contract row; test-quality notes only
- [x] 180. Strictness `"raise"` counting a refused-keyset hook-order cursor as malformed: not a defect (intended): the
  page is correct and `test_hook_order_cursor_on_a_refused_keyset_relation_keeps_its_per_parent_page` pins it
- [x] 182. `scripts/clean_up.py` and the `review_*` generators deleting their folders unlocked: not a defect: each
  folder has one owning script and no concurrent writer is known
- [x] 184. `tests/base/test_conf.py` crashing the coverage tracer on Python 3.14: not a defect: an old CPython patch
  release in the local venv; CI is green
- [x] 191. A malformed relation GlobalID nulling the response after a committed sibling mutation: duplicate of 135 (the
  top-level coercion error decides both)
- [x] 193. Directive argument values, variable-definition directives, untyped-position defaults and a 200 KB literal
  uncharged: already fixed by `0c0537e2` (11 positions probed at `43208c0c`)
- [x] 194. An unreproduced enter-side cancel defect: not a defect: the report names no site; the plausible referent, the
  async mutation window, is `1b6a09b1`
- [x] 212. No static gate for a `TYPE_CHECKING`-only name in an eager annotation: not a defect: the floor run of
  `tests/base/test_init.py` is the documented catch (START.md "Toolchain"), and every such name in a module without
  `from __future__ import annotations` is quoted
- [x] 225. `forms/inputs.py::_form_field_basis` checking identifiers before `Meta.fields` narrowing: not a defect
  (infeasible): it needs a form field named by a non-identifier
- [x] 226. A nested serializer's `.fields` skipping the root field-map checks: not a defect (infeasible): it is DRF's
  `BindingDict`, and a bad value lands as a typed `ConfigurationError`
- [x] 227. `exceptions.py::_safe_predicate(isinstance, ...)` evaluating a lazy `save()` return: already fixed:
  `rest_framework/resolvers.py::_checked_saved_result` reads `issubclass(type(saved), model)` (`5cbe15de`)
- [x] 228. `exceptions.py::_safe_arg_repr` not bounding length: not a defect (infeasible): only a custom `save()`
  returning a huge object reaches it, and the wire sees the masked error
- [x] 230. Lead: a `ValidationError` from login's `user_logged_in` -> `update_last_login` -> `User.save()`: not a
  defect: `auth/mutations.py::_django_http_login_establish` compensates fail-closed and re-raises, as Django's `login()`
  propagates
- [x] 239. Lead (perf): the always-empty first arm of a scoped relation `isNull: true`: not a defect: a redundant arm;
  the result is correct
- [x] 243. Exact-type checks written as tuple membership: not a defect (infeasible): only a metaclass whose `__eq__`
  lies reaches them
- [x] 246. `DjangoType` `Meta` names and vocabulary values keeping the consumer's `str` subclass: not a defect
  (infeasible): `TextChoices`, `(str, Enum)` and `StrEnum` members work; only a lying or raising `__eq__` fails
- [x] 247. `Meta.operation` accepted by frozenset membership: not a defect (infeasible): a `StrEnum` member works; only
  a lying `__eq__` fails
- [x] 248. `permissions.py::apply_cascade_permissions(fields=)` comparing `str`-subclass entries by their own dunders:
  not a defect (infeasible): `StrEnum` entries work, and the argument is trusted application Python
- [x] 250. A set-family `Meta.fields` / `Meta.exclude` whose `__class__` claims `dict`: duplicate of 237: the feasible
  shape, a `SimpleLazyObject` declaration, is 237's regression from `53001bdd`; a crafted `__class__` is infeasible
- [x] 237. A `SimpleLazyObject` `Meta.fields` / `Meta.exclude` raised a raw `TypeError` on both set families: fixed,
  `utils/inputs.py::plain_set_meta_fields` reads a lazy declaration (list, tuple, set, frozenset, dict, lazy lookup list,
  a nested proxy) as the object it stands for, so `FilterSet` and `OrderSet` accept every lazy declaration their
  evaluated twin accepts and django-filter's list/tuple declared-filter allowance answers as for the target; 250 is its
  duplicate
- [x] 252. A nested connection ordered by a relation name windowed on the key column while the pipeline compiled the
  related model's `Meta.ordering`: fixed, `utils/querysets.py::expand_relation_order` gives the window, the reversed
  window, the lateral column map, the random-order arm, the scalar-only projection and the index advisory the order as
  Django's compiler runs it (forward, one-to-one, nullable, reverse, many-to-many, multi-hop and recursive names); a
  related `Random()` goes per parent; an expanding one-to-one key name gets the pk tiebreak on every path; a multi-column
  `ForeignObject` name windows on its carrier columns instead of raising; the keyset vocabulary still refuses a relation
  name on both paths
- [x] 259. A `RelatedFilter` flat copy was deferred when its form field cleaned an absent key to a value that filters (a
  consumer field class whose `clean` / `to_python` returns a default, a `TypedChoiceFilter` or `CharFilter` with a nonempty
  `empty_value`), so the parent connection dropped the constraint a full copy applies: fixed,
  `filters/sets.py::_absence_filters_nothing` defers only after `_absent_cleaned_value` proves the cleaned absent value
  from Django's, django-filter's or the package's own field classes (whole MRO) and `_filter_skips` proves the filter
  skips it; a two-state `BooleanField`, a multi-widget on a single-value field and an empty string reaching a package
  filter stay eager too; the shipped schema's deferred set is unchanged
- [x] 260. A partial `ModelForm` update omitting a FK whose stored key names no row (a `db_constraint=False` key left
  dangling) read the stored key under the form's lookup field and could link an unrelated row: fixed,
  `forms/resolvers.py::_reconstruct_partial_data` reports it as the form field's own `invalid_choice` error before the form
  is bound, so nothing is written; a NULL FK still binds the empty value
- [x] 261. `scripts/check_trailing_commas.py --fix` exited 0 when a later round's reflow stranded an explode behind a
  suppression comment: fixed, `_classify_round` classifies every round (round 1, the on-disk rounds and the `--diff`
  rounds) and reports each stranded explode once from the file's final pass, at its line in the settled text; `--diff`
  raises the same errors as `--fix`
- [x] 265. Residual of 259: the deferral proof read the field class and `extra`, never the form field the filter had
  already built (`Filter.field` caches it in `_field`), so a filter whose `__init__` edited `self.field` (an `empty_value`,
  `required`, `disabled`, widget or method) was still deferred: fixed, `filters/sets.py::_absence_filters_nothing` proves
  from the cached field when there is one, and `_runs_as` walks a projected copy to the filter it runs at every hop, so a
  copy run inside a child set with its own `__init__` two or more hops down stays eager too (fakeshop defers 4706 copies,
  was 4885)
- [x] 266. Residual of 260: a single form relation whose form-key value the field cleans to empty (a stored or supplied
  key `""`, row present or not) bound as a clear: fixed, `forms/resolvers.py::_unrepresentable_choice` is the one check
  every stored and provided single form key passes, refusing it as the field's `invalid_choice` error with nothing written
- [x] 267. An M2M form list element in the field's `empty_values` (a raw pk `""`) was skipped as a clear and bound
  undecoded, linking a row its type hides or reading a pk as a `to_field_name` value: fixed,
  `forms/resolvers.py::_decode_form_relation_multi` decodes every element; only the whole value can be a clear
- [x] 268. A filter whose instance carries its own `filter` was judged by the class `filter` and deferred: fixed,
  `filters/sets.py::_own_filter_skips` accepts only the bound `FilterMethod` `method=` installs
- [x] 257. A list-field `offset` was certified over a `Meta.ordering` path ending on a forward many-to-many or generic
  relation whose target orders at random, since the guard read the relation's own `attname`, not the join field the
  compiler expands on: fixed, `utils/querysets.py::resolve_order_name` is the one reading of a relation order name for
  the offset guard, the connection window and `optimizer/plans.py::ends_in_unique_column`; a many-to-many loop is refused
- [x] 181. A `get_queryset` hook or manager `extra(order_by=[...])` ordering was dropped by every connection (root,
  keyset, nested window, per-parent), forward and reversed, since the order ladder read `applied_order` (blind to the
  extra ordering the compiler selects first) and rewrote it with `order_by()`, which empties it: fixed,
  `optimizer/plans.py::normalize_order_direction` first moves the extra ordering into `order_by` terms that compile the
  same SQL (a raw `table.column` term only under an audited `SQLCompiler._order_by_pairs` body), and
  `utils/querysets.py::selected_order` is the one reading of the compiler's order precedence
- [x] 109. `PrimaryKeyRelatedField(source="pk")` over a relation primary key (`PatronProfile.patron`, the MTI parent
  link `LendingDesk.venue_ptr`, DRF's auto-built `pk` field) built a create input every create failed with a masked
  `TypeError` (Django's `pk` writes the key's column, as plain DRF also fails); `utils/relations.py::written_model_field`
  is now the one source-to-written-field reading (`write_source_key`, `_writes_primary_key`, the column guard), and
  `_reject_relation_column_source` refuses the `pk` alias at schema build like the `attname` (remedy `source="patron"`);
  scalar `source="pk"` fields build and write as before
- [x] 111. A writable `PrimaryKeyRelatedField(queryset=...)` over a `GenericForeignKey` name or source
  (`TaggedItem.content_object`, `CirculationDesk.content_object`) failed the schema build (an `AttributeError`, then a
  `ConfigurationError` naming model `'NoneType'`) because the column branch read the GFK's `related_model`; a column naming
  no target model now types from the field's `queryset.model` as a serializer-only relation, so the shape plain DRF writes
  works (visibility applies to the decoded id; `many=True` and non-PK fields stay refused); the fakeshop library
  serializers share a `ModelSerializerBase` carrying the one `Meta` suppression
- [x] 274. A create naming a client-assigned primary key with no `default` / `db_default` (model `DjangoMutation`,
  register over a user model keyed by a client-named pk, `DjangoModelFormMutation`) saved through Django's
  UPDATE-then-INSERT, so a row committed concurrently under that key was overwritten and reported as created (a
  competing account's password hash replaced; an MTI parent row overwritten): fixed,
  `mutations/resolvers.py::save_new_row` saves with `force_insert=(Model,)` exactly when `adds_by_update_first` says
  Django would try an UPDATE, so the race is the `__all__` `constraint` envelope; the ModelForm flavor splits such a
  create as Django's admin does (`form.save(commit=False)`, the forced save, `save_m2m()`); auto, default and
  `db_default` keys and every update are unchanged; the serializer flavor already inserted through `objects.create`
- [x] 120. `prove_failability.py` had no SIGTERM / SIGHUP handler: a terminated run left its mutation in the tree and
  its `ACTIVE-MUTATION.json` marker, and a signal to the run alone orphaned the pytest scope: fixed, `main` routes
  SIGINT / SIGTERM / SIGHUP / SIGQUIT (an inherited `SIG_IGN` stays ignored) to a handler that records the stop and
  forwards it to the scope, now in its own session (a repeat after `STOP_REPEAT_GRACE` kills the group); the run then
  restores and proves the tree through the existing `finally`, writes no record and exits `128 + N` (a direct script
  run dies by the signal); only `SIGKILL` or an interpreter crash still leaves the marker and `restore_with`
- [x] 282. An update whose located row a concurrent transaction deleted after the locate (`Meta.select_for_update =
  False`, or a backend without `FOR UPDATE`) was re-inserted and reported as updated on a `DjangoModelFormMutation`
  (`form.save()` runs UPDATE, 0 rows, then INSERT) and on a model `DjangoMutation` over a multi-table row whose parent
  row vanished (`force_update` covers only the child table), and was a masked top-level `ConfigurationError` on a
  `SerializerMutation`: fixed, `mutations/resolvers.py::save_located_row` saves with `force_update=True` plus
  `update_fields` naming every loaded non-key column of every table on a multi-table row (an existence check first when
  a table contributes no column), the ModelForm update splits as Django's admin does (`form.save(commit=False)`, the
  located save, `save_m2m()`) inside `forced_save_or_field_errors`, and the serializer flavor answers a witnessed INSERT
  under the authorized pk as `conflict`; every flavor now returns the in-band `conflict` envelope on `id`, rolled back;
  single-table rows keep `update_fields=None`; fakeshop gains the three `UpdateLendingDesk` flavors
- [x] 121. A crashed `prove_failability.py` run left its `ACTIVE-MUTATION.json` marker where no later run looked (a
  fresh `failability-*` dir per default-mode run; an explicit `--scratch-root` was checked only under that same root),
  so a rerun on another entry of the mutated file copied the mutated bytes as pristine and printed a byte-comparison
  restore claim: fixed, the live crash state (pristine copies, the marker, `RESTORE-FAILED.json`) lives in one per-tree
  state directory under `$XDG_STATE_HOME` or `~/.local/state`, which every run checks under the tree lock whatever its
  scratch root (8 of 10 crash-then-rerun cells ran at HEAD, 10 of 10 are refused now); the directory is 0700, empty at
  rest (a proved restore moves the copies into scratch, a run with no marker sweeps leftovers), and default scratch is
  `failability/tree-<digest>` under the system temporary directory, refused unless a real directory owned by the user
- [x] 123. BUILD.md "Mechanized: `scripts/prove_failability.py`" called the tool's default scratch "a bare `/tmp` path":
  fixed with 121, it names `failability/tree-<digest>` under the system temporary directory and the state directory
- [x] 132. A `SerializerMutation` whose `Meta.fields` narrowing keeps a relation to a Relay-Node type fails schema build
  (`TypeError: Mutation fields cannot be resolved. '<...>PartialInput'`), create and update, e.g. `Shelf.branch`; a non-Relay
  target builds: fixed, the cause was the `data:` reference's name, derived when the root `Mutation` body ran, before
  finalization made a `Meta.interfaces = (relay.Node,)` target a node, so a digest-named shape (`fields` / `exclude` /
  `optional_fields` / nested narrowing) folded `Int` into the reference and `ID` into the bound class; the reference now
  names the mutation's own `<Mutation>Data` slot (`rest_framework/inputs.py::serializer_input_slot`), under which
  `SerializerMutation.build_input` also publishes the class each bind builds, so a rebuild never resolves a parked `Int`
  input and a relation target may be declared after the root `Mutation` (69 of 69 grid cells failed "no registered
  primary" at HEAD); GraphQL type names are unchanged; fakeshop gains `updatePatronProfileGenreViaSerializer`
- [x] 285. An update or delete whose located row a concurrent transaction deleted after authorization
  (`Meta.select_for_update = False`, or a backend without `FOR UPDATE`) answered a misleading field error when decode or
  validation failed before the save (an omitted relation re-read as empty or as a key that vanished with the row on
  ModelForm / model; a named relation that vanished with the row), or a masked top-level `DoesNotExist` from DRF's
  `UniqueTogetherValidator` on a serializer: fixed, `mutations/resolvers.py::run_write_pipeline_sync` probes a located
  row only when its step fails (`utils/write_transaction.py::located_row_vanished`, which the save's own conflict check
  now reuses) and answers the `conflict` envelope on `id` when the row is gone; a `DoesNotExist` escaping the step is
  `conflict` the same way, and propagates while the row is present and on create (22 of 102 row-gone cells were not
  `conflict` at HEAD, 102 of 102 are now; a success runs no extra query, a failure one); a model or serializer update
  writing back a stale omitted key after a concurrent `SET_NULL` under the opt-out is Django's whole-row-save lost
  update, refused by the database, and stays out of scope
- [x] 133. A `PrimaryKeyRelatedField` to a model whose pk is a `OneToOneField` (`PatronProfile`) was refused at schema
  build, and the defect was wider: a relation id into any non-Relay or unregistered target whose primary key is itself a
  key (a one-to-one pk, a multi-table-inheritance parent link or grandchild chain, `ForeignKey(primary_key=True)`, a
  `to_field` naming a key) was refused in every write flavor (280 of 768 grid cells, 54 of 132 column-less), and an id
  past the range of the column such a key stores was a masked `OverflowError` on `node`, relation GlobalID decode,
  update `id` (both arms, live on `updatePatronProfile` / `updateLendingDesk`), filter identity and raw write ids:
  fixed, `utils/relations.py::stored_value_column` follows a key to the column storing its value (the walk the filters
  already made, now shared), `mutations/inputs.py::relation_id_scalar` types from it and
  `utils/querysets.py::coerce_field_value_or_none` runs the key's own validators then that column's; all 280 refused
  cells build and store the right row, the 280 that built keep identical SDL; fakeshop gains `KioskFault` with
  `createKioskFault` / `ViaForm` / `ViaSerializer`
- [x] 137. The ModelForm (pk-keyed `ModelChoiceField`) and serializer (`PrimaryKeyRelatedField`) flavors stored `NULL`
  for a relation id naming a visible row whose `to_field` key is `NULL`, silently clearing an optional FK or one-to-one
  (16 grid cells; required FKs and M2M gave "cannot be null", a generic constraint error or a raw `ValueError`), where the
  model flavor refused it since item 130; and `forms/resolvers.py::_to_form_key_value` fell back to `obj.pk` when
  `to_field_name` did not resolve on the row, linking a colliding row, even a hidden one: fixed,
  `utils/querysets.py::linkable_rows` drops `NULL`-key rows at every visible-relation read (the single spine, the batched
  model path, DRF's lookup) from the stored column each builder records on `InputFieldSpec.key_attname`, so all 80
  `NULL`-key cells are the relation error with nothing written; a `to_field_name` that is not `pk` or a concrete field is
  a schema-build `ConfigurationError` on any field the operation binds (every declared field for an update) and the
  fallback is gone (the item's `to_field_name`-keyed half was already fixed by item 266); fakeshop gains `Branch.isil` and
  `InterlibraryLoan` with create / update in all three flavors
- [x] 143. The `.dsf-ws` marker was a regular file written once and only `.exists()`-checked, so its atime never moved
  and the macOS daily `$TMPDIR` purge (regular files whose atime is over 3 days old; directories never removed) deleted
  it 3 days after the flow's first command: `gc` then refused the flow, `release` freed nothing while `state.json` kept
  the bindings, and `status` dropped the flow: fixed, the marker is an empty directory, `Layout.ensure_marked` turns a
  marker file into it under `pool.lock` (re-checking inside the lock), and `_remove_flow_dir` removes it last with
  `rmdir` or `unlink`; `gc` still refuses an unmarked folder (13-row grid: 7/13 at the parent, 13/13 after)
- [x] 147. `scripts/build_kanban_md.py::GlossaryInliner._protected` lexed only single-backtick code spans, so a
  glossary link was written inside a URI / email autolink, raw HTML (tag, attribute, comment, PI, declaration), a
  multi-backtick or multi-line code span, or a GitHub bare URL / `www.` / bare email, a `]` inside an autolink or
  attribute closed real link text early, and a construct holding a term spent its one link per card (40 of 84 grid
  rows; latent, no card text held such a shape; `09d0caa0` never lexed double-backtick spans, contrary to the earlier
  tracker claim): fixed, `_protected_regions` makes one leftmost-wins pass per paragraph (CRLF blank lines included)
  over escapes, equal-width backtick runs, autolinks and CommonMark 6.6 raw HTML (unclosed openers linear), masks each
  atomically before bracket pairing, then an over-matching GitHub bare-URL guard; a held mention no longer spends the
  slot and `_find` retries so nothing linked at the parent stops linking; KANBAN.md renders byte-identical
- [x] 145. `workspace.py::_read_json_object` and `::load_runs` tested `exists()` and then read, and `status`, `audit`
  and `gc`'s busy branch read with no lease by design, so a concurrent `gc` raised an uncaught `FileNotFoundError` (16
  in 43,919 `status` calls racing `gc` for 10 s at the parent; 0 in 57,913 after): fixed, `_read_text_if_present` makes
  the read the existence check (only `FileNotFoundError` reads as absent; an unreadable file still raises), and
  `_admit` reads the slot manifest itself under `pool.lock`, so a manifest gone before the run uses the copy resyncs it
  instead of yielding `{}` and a run record with false provenance
- [x] 142. Every `workspace.py` lock was an `flock` held only by the wrapper's own descriptors, and `::stream`,
  `::_run_checked` (`uv sync`) and `::probe` started their children without them, so after a SIGKILL of the wrapper the
  child kept working in the copy with no lease and `gc` / `release` proceeded under it: fixed with 284, the command and
  every `uv sync` receive the held flow lease and copy lock (`pass_fds`; `gate`'s sync also `gate.lock`), so a lease lives
  as long as anything holding it; a daemon the command leaves behind keeps the run RUNNING and `gc` / `release` refuse
  until it ends (stated in the docstring)
- [x] 284. `workspace.py run` / `prove` (`::stream`) started the command in the wrapper's process group and forwarded
  no signal, so a SIGTERM / SIGHUP / SIGQUIT / SIGINT to the wrapper's pid alone ended the wrapper and dropped its lease
  while pytest or the prover kept running in the copy (a `gc` under a live mutation left a `RESTORE-FAILED.json`), and
  no run record was written; terminal Ctrl-C, group-mode `timeout` and `TaskStop` already reached the whole group:
  fixed, the command runs in its own session and the wrapper relays each stop signal to its group
  (`scripts/_stop_signals.py`, shared with `prove_failability.py`; an inherited SIG_IGN stays ignored, a repeat inside
  1 s is uv's duplicate and dropped, no SIGKILL escalation) until the command and whatever holds its output have ended;
  Ctrl-Z stops the group with the run and `fg` continues both; the record keeps the command's exit and adds
  `stopped_by`, the wrapper ends by the signal (`128 + N`); a closed output sink no longer hangs the run (36-cell
  matrix: 0 survivors after, the defect on every relay cell before)
- [x] 296. `tests/test_workspace.py::test_the_lint_gate_suite_runs_the_ci_lint_job_commands_in_order` failed on main:
  `9a97127c` made CI's lint job run `scripts/check_citations.py --check --substrings` while the `gate` lint suite still
  ran `--check`: fixed in `8e191ea3`, `scripts/workspace.py #"LINT_COMMANDS"` runs `--check --substrings` as CI does
- [x] 249. A set-shaped `FilterSet` `Meta.fields` (or `filter_fields`, or a set of lookups in a dict declaration)
  expanded in hash order, so `base_filters`, the generated filter input and each lookup sub-input moved with
  `PYTHONHASHSEED`: fixed, `filters/sets.py::FilterSet.get_fields` reorders django-filter's field map by
  `utils/inputs.py::canonicalize_set_meta_fields` (the names upstream kept, `Meta.exclude` applied, in
  `canonical_sort_key` order; a set of lookups as a sorted list); the declaration is never rewritten as a `list`, so
  django-filter's declared-filter allowance still refuses a set, and a list / tuple / dict of lists keeps its order. The
  OrderSet twin's pin now fails without canonicalization in every process
- [x] 234. The index advisory on a proxy target (or a proxy of a proxy) read the proxy's own empty `Meta.indexes` /
  `Meta.constraints` / `unique_together`, recommended an index the concrete model already declares, named the proxy
  (where `models.E016` forbids declaring it) and deduplicated under the proxy's label: fixed,
  `optimizer/nested_planner.py::_advise_composite_index` reads the table-owning `_meta.concrete_model` once and feeds it
  to the window columns, the order terms, the coverage check, the dedup key and the message, so a covered proxy is
  silent and an uncovered one warns once naming the concrete model; a non-proxy model is unchanged
- [x] 241. Duplicate input-object field names escaped the value budget: `charge_arguments` charged
  `value_from_ast_untyped`'s dict, which dropped an earlier same-named field's subtree uncharged at every spread
  expansion: fixed, `extensions/resource_policy.py::_DocumentWalk` charges each argument as its AST (`_popped_value`
  keeps a literal list / object as its node and resolves a variable through graphql-core's own lookup;
  `_ValueBudget._charge_container` counts an `ObjectValueNode`'s width as every spelled field, a repeated name
  included), and an unused or used variable default is charged as its literal AST, so a duplicate-name document over a
  bound gets the resource rejection (spread, untyped, typed-order, directive, unused-default and used-default rows) and
  one within budget reaches graphql-core's "only one input field" validation; no new bound, code or message
- [x] 271. Fixed with 272: `utils/querysets.py::_raw_sql_node_defect`'s `ExtraWhere` arm admits `params is None`
  (Django's documented `extra(where=[...])` spelling, read by `ExtraWhere.as_sql` as `self.params or ()`); `RawSQL(sql,
  None)` stays refused, since Django raises `TypeError` compiling it
- [x] 272. A `TextChoices` / `StrEnum` member where Django takes any `str` was refused by the visibility seal: fixed,
  one text-term predicate (`utils/querysets.py::_is_text_term`, an `is_str` with no `resolve_expression`) reads
  `order_by` / `distinct` / `extra(order_by=, tables=)` and `ExtraWhere` fragments, and a raw-SQL param leaf passes when
  inert or under the direct-RHS type rule (`_plain_data_leaf_defect`, extracted from `_direct_rhs_defect`); containers
  in params and an expression-`str` stay refused, the sealed query compiles Django's SQL byte for byte, and every
  still-refused message is unchanged
- [x] 294. A member in a name slot (annotation / alias / `extra(select=)` keys, FilteredRelation aliases, `table_map`,
  `using()`, `values()` fields, prefetch lookups and `Prefetch` through / to_attr) was refused at eight exact-type
  sites: fixed with 272, every site reads `is_str` and the seal carries the normalized exact text (`_normalized_str`,
  `_normalized_db`, `_normalized_fields`; `_prefetch_path_or_defect` reads a `Prefetch` path once and
  `_rebuilt_prefetch` cannot fail), so a deep walk finds no `str` subclass in sealed state and the live genre-books
  connection, root list, cascaded `values()` hook and enum-routed managers serve what their exact-text twins serve
- [x] 291. A ModelForm whose bound relation field disagreed with the class-level field the decode reads was bound
  unchecked (an `__init__` / `get_form` override setting or clearing `to_field_name` linked a hidden row with `errors:
  []`; a queryset swapped to another model handed `perform_mutate` that model's row): fixed,
  `forms/resolvers.py::_assert_bound_choice_agreement` runs after `get_form()` and before `is_valid()` over every bound
  name (a reconstructed update relation included) and raises `ConfigurationError` when the bound queryset's model is not
  the decode target (a subclass, proxy or MTI child, passes) or the bound key resolves to another column than the basis
  (every pk spelling is one key); a model-choice field over a scalar column stays unchecked
- [x] 292. A relation `to_field_name` naming a concrete non-unique column passed the build guard and then raised
  `MultipleObjectsReturned` (single) or linked every row with the key, a hidden one included (many-to-many): fixed with
  291, `forms/inputs.py::require_readable_choice_keys` requires `pk` or a column unique on its own (`unique=True`, a
  one-field `unique_together`, or an unconditional one-field `UniqueConstraint`), Django's fields.E311 rule; the guard's
  tests moved to unique columns (Branch.name, MembershipCard.patron) and Book.title / shelf are refusal rows
- [x] 254. Not a code defect: the fingerprint only guards the class-validation vs bind drift of a nondeterministic
  `get_serializer_for_schema()` hook, and the input, descriptor name and reverse map are built from the bind-time read
  alone, so a drift on an unrecorded axis (a nested `ListField` grandchild's class or `allow_null`, an attribute a
  registered converter reads outside the listed axes) builds a self-consistent input instead of failing loud (item 154's
  "fails loud" holds for recorded axes only). Retracted "EVERY axis" in
  `rest_framework/inputs.py::serializer_schema_fingerprint`, `_fingerprint_field_map`, `_fingerprint_converter_extra`,
  the `NestedSerializerConfig` docstring, `rest_framework/sets.py::_checked_schema_field_map` and spec-039's fingerprint
  section and nested bullet; code digest unchanged.
- [x] 160. Still live on HEAD: `filters/base.py::RangeFilter` had no `filter()`, so a range input with one bound left
  out or `null` reached the declared `range` lookup as `[x, None]` and compiled to `BETWEEN x AND NULL`, matching no
  row. `RangeFilter.filter` now applies a lone start as `__gte` and a lone end as `__lte` through `_apply_lookups`
  (django-filter's semantics; `exclude` / `distinct` honoured, no instance mutation), keeps the declared lookup for two
  bounds and skips a range with neither; pinned by unit rows in `tests/filters/test_base.py` (zero bounds included) and
  live rows in `test_scalars_filter_api.py` (flat, `not`, `partner` branch, explicit nulls).
- [x] 300. `scripts/workspace.py::stream` now runs its command in `with subprocess.Popen(...)`, so both pipes close on
  every path once their pump threads are joined; an error out of the start or wait step first SIGKILLs the command's
  process group (the `subprocess.run` idiom), so closing never waits on a still-running command, and the output sinks
  are resolved before the command starts, so a caller without byte stdout starts nothing. Pinned by seven in-process
  rows in `tests/test_workspace.py` (success, non-zero, interrupted wait, failed thread start, no byte stdout, slow
  reader on both paths).
- [x] 150. `docs/bug_hunt/pbugs.md` item 20's `Scrutiny:` line now states the placement as
  `orders/inputs.py::Ordering`'s docstring does: a bare `ASC` / `DESC` leaves it to the database, SQLite and MySQL sort
  `NULL`s first on `ASC` and last on `DESC`, Postgres last on `ASC` and first on `DESC`. Docs only; the behaviour stays
  pinned on both vendors by `_ordered_with_missing`.
- [x] 299. The `scripts/workspace.py` module docstring's `status` bullet now says what `status` prints: copies,
  bindings, active runs and Postgres leases. `MUSE.md`'s Disk bullet drops its claim that `status` shows the 6 GB
  free-space refusal. Docstring and prose only; the docstring-stripped code digest and both `--help` outputs are
  unchanged.
- [x] 174. BACKLOG.md no longer carries `stable_cursor_field` or `permission_aware_cursor_decoding`, both shipped as
  `Meta.cursor_field` (spec-030 `## Keyset cursors`); its "Moved out of this file" section records the move, and the
  `polymorphic_interface_connections` and `cascade_permission_prefetch_enforcement` entries name the shipped surface.
  The same future-work claim is gone from spec-010's slot table, spec-032 (viewer-scoped decode folded into its
  `Meta.cursor_field` sentences), `test_library_api.py::test_stale_after_cursor_no_error`'s docstring and the board
  (CardItems 1386 and 432, card 24's planning note and CardReference 15, re-rendered). Docs and board only; no
  executable line changes.
- [x] 155. Already fixed by `a9e7963d`: none of the nine sentences names `0.324.0` any more; specs 030, 031, 032 and the
  spec-030 / spec-032 rationale companions now carry no locked Strawberry version literal (0 hits under `docs/SPECS/`
  and `docs/spec-*.md`). The citation-gate rule the item left open stays unbuilt.
- [x] 235. Already fixed by `9a97127c`: both `optimizer/nested_planner.py` comments now state the invariant without the
  "P2-3" review label ("covering the general page;", "naming a duplicated column."); 0 hits for `P2-3` in the file.
- [x] 269. A filter holding a `filter` of its own (a `Filter` subclass whose `__init__` stores `self.filter`) raised
  `FieldError` on every walked path and was negated twice under `exclude=True`, because `filters/sets.py` tested
  `method` where the condition is "holds a `filter` of its own": fixed, `sets.py::_own_filter` reads the instance
  `filter` and replaces the `method` test in `_owner_bound_child` (a child-expanded leaf is projected and runs inside
  its child set), `FilterSet._flat_leaf_walk` (a parent-declared leaf is not walked, as a parent `method=`),
  `FilterSet._apply_active_leaf`'s negate line (its `filter` owns `exclude`) and `_decodes_before_binding`, which also
  reads a projected copy through to the child filter it runs (a GlobalID filter holding its own `filter` refuses
  unstorable text `FILTER_INVALID` flat, nested and on its own set; one whose `filter` delegates to the decode now
  answers it `FILTER_INVALID`, not `GLOBALID_INVALID`, as `method=` does); null extension and a class-level `filter`
  override unchanged. Live rows on `BookFilter.title_starts` (an example own-`filter` `CharFilter`), package grid,
  mutations M1-M7 red
- [x] 290. A GlobalID filter into a type whose `relay.NodeID[...]` names a column other than the primary key (fakeshop
  `PublisherType.house_code`) coerced the id against `_meta.pk` and compiled on the pk path, refusing the id the
  server emits or selecting the row whose pk equals it: fixed, `filters/base.py::_globalid_target` resolves the
  target, its row path and its id slot once per call, the node id coerces through `relay.py::_coerce_pk_or_none` and
  compiles on `<row path>__<id_attr>` (over the `__pk` to_field marker) in `GlobalIDFilter` and both
  `GlobalIDMultipleChoiceFilter` arms; a slot over a `get_queryset` annotation compares on the type's own rows and a
  relation key into it refuses `GLOBALID_UNVALIDATABLE`; `FilterSet._leaf_applies` reads a terminal its unscoped probe
  cannot compile as active, which also repairs a flat leaf onto a filter over a target-type annotation. Primary-key
  targets byte-identical. Fixture `Series`, `Printing.licensor` / `co_publishers` / `series` (migration 0017), live
  grid, mutations M1-M8 red
- [x] 173. fixed: the KANBAN release-readiness checklist (BoardDoc 11) runs `ruff check --fix .` before `ruff format .`,
  as AGENTS and pre-commit do; CardItem 1248 states the same pair in that order (its stale `AGENTS.md:15` line cite
  dropped) and CONTRIBUTING.md lists the hooks as ruff-check then ruff-format. Both rows written with `.update()`
  (`updated_date` kept), KANBAN.md / KANBAN.html re-rendered; archived specs keep the old order as history
- [x] 178. fixed: `scope` and `--changed` resolve a changed path through one resolver,
  `scripts/review_plan.py::_changed_folder` / `_changed_item`, so a deleted path or a rename's old path names its
  nearest surviving folder's item (else Project integration) in `build_scope`'s committed `item` fields, and
  `ScopeReport.folders` counts every rename's old folder (staged ones too); dirty paths stay lexical and the JSON shape
  is unchanged. REVIEW.md and the module docstring say so;
  `tests/test_review_plan.py::test_scope_resolves_deleted_and_renamed_paths_like_changed` (10 rows) pins it, mutations
  M1-M4 red
- [x] 276. A model-backed `SerializerMutation` field whose serializer kind disagreed with its column (a
  `PrimaryKeyRelatedField` or `FileField` over a scalar column, anything but a `FileField` over a file column, a
  relation over a scalar primary key's `pk` alias) built as the column's kind and failed every write with a masked
  error: fixed, `rest_framework/serializer_converter.py::serializer_field_fits_kind` is the one kind reading (shared
  with `resolvers.py::_assert_field_agreement`) and `_reject_kind_mismatch` refuses the field at schema build, declared,
  auto-generated or added in `get_fields()`, as `get_serializer_for_schema()` returns it; existing refusal texts
  unchanged. Two shapes that wrote at the parent now refuse: a relation over a text primary key's `pk` alias (it stored
  the related row's `str()` as the key) and a schema-map field of another kind than its runtime twin (spec-039
  Decision 7)
- [x] 163. fixed in code, not docs (the `queryset & Model.objects.<method>()` recipe drops annotations and slices):
  `utils/querysets.py::_seal_or_defect` takes `keep_class`, passed only by `apply_type_visibility_sync` / `_async`, so
  the hook's input is rebuilt from the source's validated state as the source's own `QuerySet` class (Django's `_clone`
  constructor shape) and a project method works on every read path (root, connection, node, nested, sync and async,
  optimizer on or off); the hook's result and the cascade's source seal stay plain. spec-045 Decision 1, spec-020,
  `DjangoType.get_queryset`, README and GLOSSARY pks 468 / 553 / 554 say so, including the limit (instance attributes
  set outside the constructor arguments are not carried). Fakeshop `LoanQuerySet.with_note()` behind a default-off
  `LoanType` hook flag; live sync + async rows and package rows, mutations M1-M5 red
- [x] 333. The KANBAN release-readiness checklist (BoardDoc 11) asked for a local `uv run pytest` passing with 100%
  package coverage, against AGENTS rule 16 (the full suite and the coverage gate run only in GitHub Actions): fixed: the
  bullet requires the full dispatched `django.yml` matrix (`gh workflow run django.yml`: every Python / Django cell,
  single-DB and `FAKESHOP_SHARDED=1`, the lint job) to pass on the release commit, the `fail_under = 100` coverage gate
  included; BoardDoc 11 written with `.update()`, KANBAN.md / KANBAN.html re-rendered
- [x] 334. CONTRIBUTING.md's pre-commit hook list named six of the twelve hooks (no basedpyright, basedpyright-floor,
  check-type-suppressions, check-public-types, truthful-reads, import-spec-terms-check) and said the hooks check "things
  ruff does not" while listing ruff: fixed: the list names every hook of `.pre-commit-config.yaml` in config order with
  what each checks, and the lead-in says they run in that order and CI's lint job runs the same checks
- [x] 335. spec-039's "Relation-decode core" helper row (and the batched-decode prose) printed
  `visible_related_object(related_model, pk, info)` / `visible_related_objects(related_model, pks, info)`, missing
  `async_recourse` and `key_attname` and the batched form's `dict[str, object]` result: fixed: both sites print the
  helpers' signatures from `utils/querysets.py` and say the batched form maps each visible pk, stringified, to the key
  the relation stores; spec-036 / spec-038 carry no signature spelling
- [x] 336. GLOSSARY (the `DjangoNodesField` term) and spec-032 said the `nodes(ids:)` width charge runs on
  "coerced-shape input", while `extensions/resource_policy.py` charges a literal argument as its parsed AST and a
  variable by its supplied value: fixed: both say the charge runs at operation admission, before validation, on the
  input as the request spelled it (a literal list as its AST, a variable by its supplied value or its default's
  literal), still before any `GlobalID` decode; GlossaryTerm 520 through the DB, GLOSSARY.md re-rendered
- [x] 337. `utils/querysets.py::_prefetch_path_or_defect` refused with "prefetch path is not an exact str" / "prefetch
  to_attr is not an exact str or None" while its `is_str` guard admits a `str` subclass: fixed: the messages say "is not
  a str" / "is not a str or None"; the three pinned tests in `tests/utils/test_querysets.py` move with them (411 passed)
- [x] 338. BACKLOG.md carried the unused link definition `[card-full-relay-story-node-connection-root-validation]`:
  fixed: the definition is dropped; the LINK DEFINITIONS block has no unused or undefined reference and keeps its ten
  group headers
- [x] 295. A `ModelForm` field named after a model column but of another kind (a relation field over a scalar, JSON or
  file column, a file field over a non-file column, a scalar field over a file column, a single / multi relation
  mismatch) typed, decoded and routed by the column while the bound form read by its own kind: it wrote the chosen
  row's `str()` unchecked (a row the type hides included), dropped the value while reporting success, or never
  succeeded, and one left out of an update input failed every update: fixed,
  `forms/inputs.py::require_column_kind_agreement` refuses the field at schema build on every field the operation
  binds (an update: every declared field), reading the field through `forms/converter.py::form_field_kind` (class, or
  a `forms.FileInput` widget; `convert_form_field` reads the same, so a column-less `FileInput` field is an `Upload`);
  a scalar field over a relation column still takes the relation id. Supersedes 125. Three shapes that built at the
  parent now refuse: a `FileField` over text or a `CharField` over a file column left out of an update-only input
  (inert there), and a custom widget that reads `files` without subclassing `forms.FileInput` (remedy: subclass it).
  Mutations M1-M7 red
- [x] 303. A partial update or create over a `DjangoMutation` skipped Django's uniqueness and constraint checks a
  provided field joined when the declaration sat on a parent (a proxy, a proxy of a proxy, a multi-table child, a proxy
  of one), when a `UniqueConstraint`'s condition or expressions named the unprovided column, for every
  `CheckConstraint` reading one, and for `unique_for_date` / `_month` / `_year`; the duplicate reached the database and
  answered the generic `constraint` envelope (not a raw `IntegrityError`), or was saved silently for `unique_for_*`:
  fixed, `mutations/resolvers.py::_constraint_groups` (was `_unique_constraint_groups`) walks the model and
  `_meta.all_parents` and takes every column each constraint's `validate()` tests against `exclude`, and
  `::_full_clean_or_field_errors` runs `full_clean` with two excludes (`CleanExcludes`: `clean_fields` / `clean` skip
  every unprovided column, `validate_unique` / `validate_constraints` keep the co-members), as Django's
  `ModelForm._post_clean` splits them; `forms/inputs.py::_names_one_row` reads the `to_field_name` target's inherited
  declarations too. The `updateItem` rejected-save paths run one query fewer (no co-member field validation).
- [x] 304. A selected annotation whose node had run a row fetch was refused by the visibility seal on every policy
  ("binds a function bound value"): Django caches the row converter `BaseExpression.convert_value` (a function) in the
  node's `__dict__` at row fetch, and canonical reconstruction carried it to
  `utils/querysets.py::_normalized_bound_value`. Wider than filed: any selected non-`Col` expression, a plain
  `QuerySet` and a project subclass alike, evaluated or fetched only through a clone sharing the node (Django clones
  share annotation nodes); plainest reach a consumer `Prefetch("loans", queryset=Loan.objects.annotate(...))` with no
  hook: fixed, `utils/querysets.py::_reconstructed_value` leaves out of a rebuilt node exactly the caches Django's own
  copy leaves out (`_EXPRESSION_COPY_DROPPED`, `BaseExpression.__getstate__`; `_QUERY_CLONE_DROPPED`, plus
  `sql.Query.clone`'s `base_table`), pinned against the running Django, so the rebuilt node recomputes them and a
  value planted under those names is never carried or called; the outer query still refuses one. A sidecar result that
  was evaluated now answers `evaluated` instead of `untrusted`. Mutations M1-M3 red
- [x] 301. `workspace.py`'s locks (`pool.lock`, `slots/slot-N.lock`, `gate.lock`) were regular files, and the macOS
  `$TMPDIR` purge (`dirhelper`, 03:35 daily: a regular file whose birth time and access time are both over 3 days old,
  held or not; directories never) unlinked one a command held, so a later command locked a new inode beside it: two
  holders of one copy or of `state.json`, `release` freeing a copy a command runs in, `status` reading it free, a
  `bind` race losing a binding, two gates at once (7 of 12 probe rows at the parent): fixed, every lock is an empty
  directory (`workspace.py::file_lock` through `_lock_directory`, as the flow lease and 143's marker), and a lock file
  an older version left is replaced by its directory under that file's own lock (`_replace_lock_file`), so an older
  opener fails loudly instead of holding another inode (0 of 12 after; mutations red)
- [x] 149. `scripts/count_queries.py` exited 1 (its "scales with cardinality" code) by traceback on a missing or
  unmatched operation, an empty or fragment-only document, and an unreadable `--query`, `--compare` or `--json` path:
  `select_operation` (Strawberry's rule) and `load_baseline` refuse up front through `parser.error` (exit 2) before
  bootstrap, a syntax error no longer writes per-cell rows or failure JSON, `_bench_common.read_text_input` and
  `report_destination` give the same exit-2 refusal to every bench script that reads `--query` or writes `--json`, and a
  `--compare` baseline that measured no cell is refused
- [x] 306. `scripts/build_kanban_md.py::_link_tail_end` was quadratic on repeated unterminated inline-link tails
  (`[a](` x 5000 about 3.4 s per lex, `[a](` plus 31 `(` 30.9 s; each `](` rescanned the same whitespace-free run, a
  loop older than 147). Robustness row, not a defect under rule 37 (maintainer-authored card text, no contract bounds
  the render's time): fixed anyway, a destination nested past `LINK_DESTINATION_MAX_NESTING` (32, the limit cmark and
  markdown-it apply) fails the link, so every tail lexes in linear time; nesting up to 32 is unchanged (fuzz 0 diffs,
  0 disagreements with markdown-it past the cap) and KANBAN.md renders byte-identical
- [x] 146. `workspace.py::item_diff` stitched `git diff <baseline>` over the real index's tracked paths with per-file
  `--no-index` renders of untracked files, so staging, `rm --cached`, assume-unchanged and an unstaged move changed its
  bytes and seal, and its stat refresh rewrote the shared `.git/index`: it is now `content_tree` (a private
  `GIT_INDEX_FILE` holding the baseline overlaid with the working content; symlinks, gitlinks, a force-added ignored
  file and a sparse checkout kept) then one `diff-tree` against the baseline, the shared index is never written, and
  every `_git` call runs under `REPOSITORY_CONFIG_ONLY`
- [x] 298. Git's default XDG global ignore and attributes files still apply under `GIT_CONFIG_GLOBAL=/dev/null`, and
  `workspace.py::_git` isolated no config at all, so `wanted_files` and `item_diff` depended on the caller (a globally
  ignored package file made `sync_copy` refuse every sync; the `.claude/settings.local.json` example was already hidden
  by the repo's own `.gitignore`): fixed with 146, whose `REPOSITORY_CONFIG_ONLY` (global and system config off,
  `XDG_CONFIG_HOME` the null device, git 2.32 or later) covers every `_git` call
- [x] 297. `scripts/review_changed_python_diffs_against_head.py --against worktree` stitched `git diff -M --name-status
  <base>` with `ls-files --others`, so a file the baseline held but the index did not read D plus A and aborted on
  `_check_stem_collisions`, an unstaged move read D plus A, `rm --cached` read twice, and its stat refresh rewrote the
  shared `.git/index`: the new side is `workspace.content_tree` and one `diff-tree -r -M --name-status` over the scope,
  every git call runs through `workspace._git`
- [x] 141. `workspace.py baseline` and `gate` took their sha from the shared tree before the copy was mirrored (`git
  stash create`, which never records untracked files or `.python-version`), so the sha never named the copy (17 of 17
  probed shapes differed) and `diff` reported a pre-existing untracked file as the item's own addition:
  `snapshot_commit` commits the mirrored copy under its lock (parent HEAD read after the sync; for `gate`, its `head`)
  through `content_tree`, refuses a copy edited since the sync, never moves the shared index or refs, and the gate
  result's key is `snapshot`
- [x] 339. `scripts/bug_hunt.py::_final_gate_block` rendered "Run `uv run pytest`; require a passing suite and 100%
  configured package coverage" into every generated hunt, against AGENTS rules 15 / 16, and the same drift (missed
  by the rule-16 rewrite) sat in HUNT.md, REVIEW.md, the DRY / hunt worker docs, `scripts/review_plan.py::_GATE_ITEM`
  and `scripts/workspace.py`'s `gate --suites` default (every suite): fixed at the root, a bare `workspace.py gate`
  runs CI's lint job only (`LOCAL_GATE_SUITE`; a maintainer still names other suites), and every agentflow gate reads
  "lint locally, every other suite in the dispatched `django.yml` matrix" in BoardDoc 11's words; closed per-cycle
  hunt and review docs left as written
- [x] 340. A `ModelForm` relation field whose class-level queryset is over another model than its column's target
  (neither the target nor a subclass) built and failed every request that bound it with the request-time
  `ConfigurationError`: fixed, `forms/inputs.py::require_class_choice_models` refuses it at `finalize_django_types()`
  with the same subclass rule and target, only where the refusal is certain: the form keeps Django's `__init__` and
  `order_fields` (`form_binds_class_fields`), the mutation keeps the default `get_form`, and the field is bound by every
  write (any update; a create whose input requires it). A queryset assigned in `__init__` / `order_fields` /
  `get_form`, an optional create field (omitted works, sent is refused at request time) and a class-level `None` are
  unchanged
- [x] 343. The visibility seal dropped Django 6.1's `QuerySet._fetch_mode`, so a `get_queryset` hook or manager
  returning `.fetch_mode(FETCH_PEERS)` / `FETCH_RAISE` read `FETCH_ONE` on every sealed surface (PEERS 1+3 patron
  loads for 3 loans, RAISE never raised), against `_seal_or_defect`'s "reproduce what `QuerySet._clone` copies"
  comment: fixed, `utils/querysets.py::_seal_or_defect` carries the mode, admitting only an exact Django `FetchOne` /
  `FetchPeers` / `FetchRaise` (`utils/_queryset_private.py::is_django_fetch_mode`; any other object is the
  `untrusted` defect), so the source seed, hook, sidecar, prefetch-child and subclass seals all keep it, and
  `utils/write_transaction.py::base_visible_queryset` carries the validated mode onto the locked locate; Django 5.2
  (no fetch modes) is unchanged
- [x] 162. a declared `RangeFilter` handed its raw bounds to the ORM (`RangeField.to_python` cleaned nothing), so a
  Decimal "NaN" / "Infinity" bound answered a masked `ValidationError`: `RangeField(bound_field=...)` cleans each
  non-None bound with the form field of the column's django-filter `gte` filter (`filters/base.py::_column_form_field`;
  `gte`, not `exact`, so a choice column's off-choice bound still compares), so a non-finite or past-1e50 bound is
  `FILTER_INVALID`, a naive datetime is made aware and text is stripped; relation bounds pass through as sent (an
  existence oracle otherwise), and a class-level declaration's `.field` is built by `unkept_form_field` without writing
  to it
- [x] 370. `ListFilter` / `ArrayFilter` elements are cleaned by the same column `gte` form field through `_ElementField`
  (an ArrayField column's `base_field`), so a non-finite or past-1e50 element is `FILTER_INVALID` as on the generated
  `in`; relation elements, a non-list value and an unbound filter pass through; `_ElementField` joins
  `sets.py::_NONE_CLEANING_FIELDS` so a deferred flat copy stays deferred
- [x] 161. `filters/inputs.py::_normalize_range_value` hardcoded `_0` / `_1`, so a declared django-filter `RangeFilter`
  and its date / time families (widgets reading `_min` / `_max`, `_after` / `_before`) ignored every bound:
  `filters/base.py::multi_widget_keys` reads the keys from the filter's own built widget (`SuffixedMultiWidget.suffixed`
  per `suffixes`, else `widgets_names`; audited django-filter 21.1-26.2, Django 5.2.16-6.1.2),
  `inputs.py::range_form_keys` refuses a widget not reading exactly two keys at schema build, and
  `sets.py::_absent_widget_value` reads the same keys
- [x] 158. the operation gate (`walker.py::_enable_only_for_operation`) stopped every projection writer under a
  mutation, so a hook / manager / resolver `.only()` or `.defer()` was never widened (a hook `.only("name")` ran 77
  statements where the query ran 2; the async `DjangoMutation` re-fetch raised `SynchronousOnlyOperation`): writers
  record columns under every operation and the plan carries a cached `introduce_projection`
  (`walker.py::_introduces_projection_for_operation`), so `plans.py::apply_projection(..., introduce=False)` leaves an
  unprojected queryset whole and widens a consumer projection; mutation counts now equal the query's, the hook-free
  mutation stays one full-row statement, QUERY SQL is byte-identical; the prune (`prune_unsupportable_select_related`,
  `_select_path_traversable`, `select_path_resolver_keys`, `_record_select_path_keys`) is deleted;
  `types/resolvers.py::_FK_ELISION_UNSAFE` stays for a row the plan did not project (a consumer-owned `Prefetch`),
  pinned live; specs 002, 004, 033, 035, 036, 038, 039, 040 and GLOSSARY / KANBAN restated
- [x] 371. `walker.py::_ensure_connector_only_fields(base_queryset=...)` records the attach columns whenever the child
  plan reads a column or the child base queryset carries a consumer projection, so a typename-only child over a
  projecting hook loads its connector with the hook's columns (27 statements -> 2, query and mutation); the hook-free
  child SQL is unchanged; live row `test_library_child_reading_no_column_keeps_the_attach_connector` (sync; the async
  per-row load runs inside the sync evaluation thread and never raised)
- [x] 165. no defect: a payload relation hop past a deadline that ends after the write failing and rolling the mutation
  back, and every later subscription frame's relation hop failing once the stream's budget is spent, are spec-047
  Decision 9's contract; pinned by live sync / async rows in `test_query/test_relation_deadline_api.py` (the budget
  narrowed after the write by a resolve hook per Decision 2; each hop rejects at its own path past the written node and
  0 rows remain, the hop-free selection commits), live async rows with an already-loaded forward / reverse one-to-one
  hop that tell the head `check_deadline` from one inside the `_resolve_async` body, and
  `tests/test_resource_policy.py::test_a_budget_spent_between_frames_fails_every_later_frames_relation_hop`; the
  GLOSSARY `check_deadline` entry states both
- [x] 170. no defect: `workspace.py prove` was pinned only through `run`'s shared `execute`, so its own routing (flow,
  layout, cell, fresh, manifest refusal, exit code) had no row; 13 rows in `tests/test_workspace.py` drive
  `main(["prove", ...])` in-process (the proof command on the flow's copy under the flow lease and the copy lock,
  relative and `~` manifests resolved, the command's exit code returned and logged, cell / fresh forwarded, a missing or
  directory manifest refused before a copy binds) and through the actor harness (gc refuses while a prove waits for its
  copy; a second prove waits for the first)
- [x] 166. no defect: the async many-side rows answered the same rows whether `many_resolver` found the prefetch cache
  or missed it (a miss falls through to the manager), so they pinned neither the lookup key nor the `_check_n1` probe
  key; the async planned row now asserts its exact SELECT count over a childless venue (a missed lookup re-reads through
  the target hook), the async consumer-prefetch row also runs under `strictness="raise"`, the sync strictness row also
  prefetches the reverse FK `repairticket_set`, and one `test_query/conftest.py::record_compiled_sql` recorder serves
  the async suites; gaps (b)-(d) need no rows: an unhooked reverse M2M miss is an equivalent mutant, the window
  resolver-key collision needs a second shipped keyset type and is pinned by the async twin plus package key rows, and
  the C11 hook-order rows are live on a holder mount
- [x] 183. `[tool.ruff.format] exclude` bound only directory discovery, so `ruff format <x.md>` (the touched-paths
  command the process docs prescribe) rewrote fenced blocks (27 tracked `.md` would change, the rendered GLOSSARY among
  them): `force-exclude = true` under `[tool.ruff]` binds every exclude to named paths and `--stdin-filename`;
  `scripts/check_trailing_commas.py` reads `[tool.ruff] extend-exclude` at run time (repo-relative name segments, an
  anchored entry refused) and its own `ruff format` calls pass `--no-force-exclude`, so every file `--fix` edits is
  reflowed; rows in `tests/test_ci_governance.py` and `tests/test_check_trailing_commas.py`; START and docs/ruffing.md
  state it
- [x] 185. no defect:
  `tests/mutations/test_write_transaction.py::test_every_success_payload_under_steady_pings_is_a_committed_row` is
  selected by `postgres.yml`'s `package-core` shard and passed in every Postgres run since `1b6a09b1` (11 of 11), and
  fails 3 of 3 against the pre-fix `schema.py`; the blocked-sync-caller nesting is documented in `schema.py` and pinned,
  so docs/README.md, GLOSSARY `DjangoSchema`, the KANBAN card item and the spec-044 rationale now carry that exception
  instead of an unconditional private window; the async window has no owning spec, card 079 owns the surrounding
  transaction
- [x] 186. docs/README.md now states how the optimizer cooperates with a consumer queryset (kept `select_related` /
  `prefetch_related`, a consumer `Prefetch` in place of the planned one and unused on a joined forward relation, a
  prefetch onto a hooked target re-read per parent, a consumer `.only()` / `.defer()` widened under every operation, a
  consumer `Prefetch(queryset=...)` never widened and its deferred column failing on async), the identity arm ("Five
  empty-value rules"), and the nested-connection shapes that resolve per parent (`filter:` / `orderBy:`, a backward page
  from a cursor, an unwindowable target queryset; it was unqualified); GLOSSARY `queryset-diffing` and
  `Meta.relation_shapes` match; live rows pin the async deferred-column failure and `orderBy:` under
  `strictness="raise"`
- [x] 231. fixed in the kanban DB by `CardItem` 1479 (the FieldError keying scope bullet now states the per-flavor key
  maps from `utils/errors.py::build_error_key_map`, the package-tier multi-word matrix in
  `tests/utils/test_error_keys.py` and the live rows per flavor), `CardItem` 1500 (card 72's gap list no longer calls
  the keying a wire format no test can see; it still owes its `CAMELCASE_ERRORS` disposition row) and `CardReference`
  23-25 (copies of `CardItem` 142 that still said a model field name); a sweep of every kanban text column finds no
  stale sentence of the family left
- [x] 302. `scripts/check_spec_glossary.py::auto_link_terms` (NEXT.md Step 7 `--auto-link`) protected only column-0
  backtick fences and inline links, matched with no term boundary and never retried past a protected mention, so it
  wrote `[term][glossary-x]` into code spans, headings, reference text, autolinks, raw HTML, URLs and longer
  identifiers (39 of 63 probe rows; replaying every spec's CSV over link-stripped specs put 69 of 1216 writes in a
  protected shape), and `spec_link_anchors` counted a link inside code as a use: fixed, the KANBAN inliner's lexer
  moved verbatim to the stdlib-only `scripts/_markdown_lex.py` (KANBAN.md byte-identical), which adds a CommonMark
  block scanner (`block_regions` / `mask_blocks`: ATX and setext headings, link-reference definitions, backtick and
  tilde fences and HTML blocks inside list items and block quotes, ending with their container, indented code, tabs
  counted from their real column); the writer masks blocks, matches with `PROSE_TERM_BOUNDARY_AFTER` and moves to the
  next mention past a protected one, the checker counts only links outside code (`headings=False`); NEXT.md Step 7
  reads "non-code, non-link, non-heading" (protected writes 69 -> 0, the 57 archived specs check as before,
  markdown-it block oracle 0 under-masks over 1229 shapes and 210 files)
- [x] 187. test gap closed: the C11 live rows run on Postgres only under the default windowed strategy, so
  `tests/test_lateral_pg_parity.py::test_hook_ordered_window_pages_in_branch_with_parity` now pages hook-ordered and
  reversed keyset and offset windows (fk and m2m; title, -id and a bare `.reverse()`) through `CROSS JOIN LATERAL` with
  windowed parity, the exact `ROW_NUMBER` order and the seek operator; 53 of 53 pass on Postgres 17 locally, and the
  rows fail under the pre-fix `effective_cursor_state` (8), a dropped `normalize_order_direction` reversal (12), a
  flipped seek (10) and a flipped window direction (20); no lateral defect found; `postgres.yml`'s `package-core` shard
  (Postgres 16) runs them
- [x] 255. fixed: both terms CSVs moved to `docs/SPECS/appx/` and spec-068's `[templates-terms]` definition points
  there; `tests/test_ci_governance.py::_misplaced_archive_files` now refuses any file in `docs/SPECS/` other than an
  archived spec and `NEXT.md`, and anything in `docs/SPECS/appx/` other than a spec's `-terms.csv` or `-rationale.md`
  companion, with a live-tree row that cannot pass on an empty walk
- [x] 256. fixed: `scripts/check_all_spec_glossaries.py` runs `check_spec_glossary.py` in-process over every spec (never
  `--auto-link`) and refuses a terms CSV no spec owns or an empty population; it runs as pre-commit hook 12
  `check-spec-glossaries`, as a `django.yml` lint step after the `import_spec_terms` check and in
  `scripts/workspace.py::LINT_COMMANDS`; the item's "all 57 pass" was wrong: spec-034 failed (a `Meta.relation_shapes`
  CSV row and link definition left after its body link was dropped), so both are removed and DONE-034's glossary rows
  re-imported; START and CONTRIBUTING list the hook
- [x] 378. A killed `workspace.py prove` no longer locks its copy: a resync (first bind, rebind, `--fresh`) and `gc`
  remove the copy's `prove_failability.py` state directory (one function names it for both scripts), first restoring
  a `.venv` mutation (which the mirror keeps) from its pristine copy with a byte compare; a marker that cannot be read
  or restored is kept with a stderr notice and the resync completes; a `prove` extra that argparse would bind to
  `--workspace` / `--scratch-root` / `--json` is refused; `uv`, `git` or `docker` missing from PATH is a refusal
  before the header (it was a raw traceback, raised before the header, not after), and the prover refuses a missing
  scope executable before writing anything
- [x] 379. A consumer `Prefetch(queryset=...)` owns its path's rows on a forward relation too: the planned JOIN, the
  FK-id elision and the `only()` columns at that path are withdrawn with their resolver keys, JOINs beneath it become
  prefetch lookups over the consumer's rows, and the consumer queryset is not widened, so a row it hides stays hidden
  and an annotation it adds is served (the same answer as without the optimizer); a plain string, a queryset-less or
  `to_attr` Prefetch, or a path the consumer's own `select_related` joins keeps the JOIN
- [x] 380. A consumer `Prefetch(queryset=...)` onto a planned relation whose target type has a `get_queryset` hook is
  sealed through the hook as the seed in one batched query (two statements at any parent count, sync and async) and
  the relation's key stays planned; a seed over another model is still re-read per parent, a sliced one fails as it
  does without the optimizer; a hint seal is recorded only for a generated resolver at the relation's own accessor
- [x] 305. A ModelForm `MultipleChoiceField` / `TypedMultipleChoiceField` over a single-value column that lists no
  choices (neither an `ArrayField` nor a `JSONField`) is typed as the same form field off-column (`[String!]!` on
  create, `[String!]` on update; `forms/inputs.py::_writes_list_over_single_value`), and an update build logs one
  `logger.warning` per such field; an update omitting it binds the built form's `get_initial_for_field` under
  `form.add_prefix` (a `QueryDict` from `get_form` is copied and given the initial with `setlist`, any other mapping
  merged into a `dict`), so a form splitting the stored value into its initial keeps it and one that does not is
  refused "Enter a list of values." with nothing written; a `JSONField` column keeps `JSON`, the serializer twin is
  unchanged (spec-039); spec-038 Decision 7 and 8 and the `DjangoModelFormMutation` glossary entry say so (create 0/3
  and update 0/4 before, all green after, live under `FAKESHOP_TEST_BRANCH_CITY_PICKS`)
- [x] 326. A Django `ValidationError` raised at save time on the primary key of a serializer field written through
  `source="pk"` (integer or text key), declared as `pk`, or on a multi-table child (the parent link and its attname)
  arrives under the renamed input instead of the model's pk name (`id`, `isbn_13`, `venue_ptr`):
  `rest_framework/serializer_converter.py::written_model_field` moved verbatim to `utils/relations.py` (no shim) and
  `utils/errors.py::save_time_error_key_map` resolves the spec's source through it; the docstring and the spec-039
  citation say so (the 4 wrong grid rows flip, the 7 correct rows stay; live under
  `FAKESHOP_TEST_PK_SOURCE_SERIALIZERS`)
- [x] 190. fixed: a temporal filter value the database the queryset runs on cannot bind answers `FILTER_INVALID` keyed
  to its form field (`"Enter a value the database can represent."` / `"invalid"`) instead of the masked uncoded error:
  `FilterSet._validate_form_or_raise` asks that connection's own operations through
  `utils/errors.py::unbindable_temporal`, resolving the alias lazily and only for a temporal leaf; refused on SQLite,
  MySQL and Oracle are an aware datetime outside years 1..9999 once projected (a naive one made aware under a non-UTC
  `TIME_ZONE` included), any aware datetime when `USE_TZ` is false and an aware time, and on every backend a `year` /
  `iso_year` comparison bound outside 1..9999; Django's PostgreSQL adapters pass those datetimes and times through;
  generated leaves, `not` / `or` / `and`, relation paths, declared filters, list and range members, sync and async
  (`node` -> `decisionsConnection`) all answer it; spec-027, docs/README.md and the GLOSSARY FilterSet entry state the
  rule
- [x] 328. Every floor run installs each soft dependency at its pinned lower bound, not only Django and
  strawberry-graphql: the CI floor cell (`django.yml`, every `compatibility_only` node) gains a step installing
  `channels[daphne]==4.3.2`, `cryptography==44.0.0`, `django-debug-toolbar==7.0.0` and `djangorestframework==3.17.0`
  after `uv sync`, `scripts/workspace.py::floor_pins` reads them from pyproject `[dependency-groups].dev`
  (`SOFT_FLOOR_PACKAGES`, `_floor_declarations`; a pin that is not `>=`, a dropped extra or a missing soft dependency
  is a `WorkspaceError`), a `tests/test_ci_governance.py` row gates every floor literal in `django.yml` (the
  strawberry ones included) against pyproject, and BUILD.md "Floor verification" (recipe, supported floor, and a soft
  dependency's seam in "When it is required") and START.md say so (each soft dependency probed green at its floor on
  Python 3.10)
- [x] 312. fixed: the visibility seal accepts a `TextChoices` / `StrEnum` / plain `str`-subclass member wherever Django
  serves one as SQL text (a `RawSQL` text, a `Func` function / template / argument joiner / base template and its
  `extra` keys and values, a combined expression's operator, a `Meta.db_table` the base table is baked from, a lookup
  value's mapping key) and seals it to the exact text it spells, so the sealed query holds no `str` subclass and
  compiles to the exact-text twin's SQL; a pending deferred filter's arguments are rebuilt before they are baked (a
  consumer-held subquery is never relabelled; an opaque bound value or an unrebuildable graph fails closed) and a
  combinator's `pk__in` rewrite is rebuilt in turn; spec-045 and the GLOSSARY prove-then-clone entry state it
- [x] 313. fixed: reproduced (a database router whose `db_for_read` / `db_for_write` answers a `TextChoices` / `StrEnum`
  alias was refused with `ConfigurationError` on an `orderBy` read through the sidecar);
  `utils/querysets.py::_snapshot_routing_intent` admits a member and keeps its exact text as the routed alias, a
  non-string answer is still refused; spec-050 states it
- [x] 323. Inside a `get_queryset` hook, `apply_cascade_permissions` / `aapply_cascade_permissions` return a fresh
  instance of the source's own `QuerySet` class, so a project method chains after the cascade (it raised
  `AttributeError`): the source is still sealed plain and narrowed plain, so no consumer `filter` override sees the
  cascade predicate (the FilterEraser pin unedited), and the walked result is restated as the source's class at both
  exits (the walk and the re-entrant `fields=[]` return) by `utils/querysets.py::_restated_as_source_class`, sharing
  the walked `sql.Query` (no clone, no SQL, about 2.5 us; a plain source is returned as is) through `_built_queryset`,
  now the one constructor path `_seal_or_defect` uses too; both signatures take and return a QuerySet-bound TypeVar;
  README, spec-034, spec-045 Decision 1, the module docstring and the `apply_cascade_permissions` and
  sealed-execution-queryset glossary entries say so (live under `FAKESHOP_TEST_LOAN_CASCADE_BEFORE_METHOD`, every
  shape including the sync root list)
- [x] 314. Not a defect: only application Python (a `get_queryset` hook, a project `QuerySet` method) puts a value in
  `extra(params=)` / `RawSQL` params, and a model instance there fails in the driver exactly as in plain Django; the
  seal admits a raw-SQL parameter by plain-data ancestry, never by driver adaptability (an exact `UUID`, `time` or
  `timedelta` passes it and fails in the driver, as before 272), and refusing a model instance would break a project
  that registered a driver adapter for it. The `utils/querysets.py` retention and raw-parameter docstrings and
  spec-045 state that a model instance in a raw-SQL parameter is retained and reaches the driver as is, and
  `tests/utils/test_querysets.py::test_raw_sql_parameter_model_instance_is_retained_by_reference` pins the admission
- [x] 409. not a defect: a `check_<field>_permission` gate is application Python (GOAL "Trust boundary") and no wire
  input produces its slot; a non-callable non-`None` slot already fails closed, since
  `utils/permissions.py::invoke_permission_method` raises `ConfigurationError` on every request that names the gated
  input (masked to the client, never recorded in `fired`), pinned by
  `tests/utils/test_permissions.py::test_invoke_permission_method_rejects_a_non_callable_gate_slot`; a class-creation
  `callable()` check would refuse the shipped `classmethod` gate and a `property` gate and cannot see a slot set after
  creation, and DRF and django-graphene-filters check at call time too
- [x] 410. not a defect: only a write through `object.__setattr__` / `type.__setattr__` passes the seal, and that is
  trusted application code (GOAL "Trust boundary"); the sentence promising more is retracted, so
  `write_mixins.py::_ValidatedMutationMeta.__delattr__`'s message ends "captured once at class creation." (pinned
  verbatim by `tests/test_write_mixins.py::test_validated_mutation_meta_record_refuses_slot_writes_and_deletes`) and
  the seal family's docstrings, comments and test prose (`make_meta_validating_metaclass`,
  `_AuthMutationMetaSnapshot`, the comment above `_SealedAuthHolderMeta`) say the record's or class's own
  `__setattr__` / `__delattr__` refuse reassignment and deletion, with no release provenance
- [x] 307. fixed: a Ctrl-Z (`SIGTSTP`, `SIGTTIN`, `SIGTTOU`) that lands while `workspace.py` is starting its command
  waits in `scripts/_stop_signals.py::_JobControl` (`pending`) and `stream` delivers it through `settle()` once the
  command's group is recorded, so the command stops with the run (it ran on, holding its leases, until `fg`); a
  `SIGCONT` before then drops it. A reader gone from the output (`| head`, `2>&1 | head`, a closed terminal) no
  longer turns the run's exit into 120: `_pump` points every one of the sink's fd, 1 and 2 that shares the dead file
  at `/dev/null` on `EPIPE` / `EIO` only, so `run` and `prove` return the command's own code and a full disk still
  surfaces. The suspend-before-recorded, continue-before-recorded, shared-fd reader-gone and errno rows pin it, a
  `gate(layout, ["floor"])` row pins the floor install's lock holding, and the two `SIGCONT` routes were already
  told apart by their own rows (not a defect)
- [x] 135. fixed: a malformed GlobalID in a relation input, single (`categoryId: "not-base64!!"`) or an `[ID!]`
  element (`genres: ["not-base64!!"]`), is the field-keyed relation `FieldError` (`Invalid id for relation ...`) in
  the payload in the model, ModelForm and serializer flavors, never a masked top-level error: a relation into a Relay
  target is typed `strawberry.ID` and decoded server-side, the decode branching on the target
  (`utils/write_values.py::relation_takes_global_id`), and a consumer override of such a relation must be
  `strawberry.ID` (a `relay.GlobalID` override is refused at finalize). The error-policy, products and library
  live rows pin it; spec-036, 038, 039, 053 and the `input-type-generation` glossary term say so
- [x] 324. fixed: `tests/utils/test_querysets.py::test_additive_only_subclass_result_is_sealed_to_plain_queryset`
  states behaviour only: the hook result is rebuilt as a plain `QuerySet` from its validated state, the subclass
  identity dropped whatever methods the subclass defines, the predicate kept; the same file's other history phrasings
  ("previously", "used to", "pre-fix", "the old inventory", "before the accessor scan existed", "new guard") are
  restated the same way, each counterfactual checked by running the test's probe with its guard patched out. Comments
  and docstrings only (code digest unchanged)
- [x] 424. fixed: a `DjangoModelFormMutation` whose form carries a prefix (a class-level `prefix`, a
  `get_form_kwargs` `prefix=`, or a `get_form` passing the package's data or a copy of it to a prefixed form) is bound
  under it: the package keys the client's values through the form's `add_prefix`, so the form reads every value sent
  and the explicit-`null` and required-file checks answer as on an unprefixed form; only renamed form-field keys move,
  no consumer mapping is mutated, and a mapping already holding a prefixed key is kept as bound. The products
  prefixed-form live rows and the forms resolver rows pin it; spec-038, the README and the `djangomodelformmutation`
  glossary term say so
- [x] 408. fixed: a `SerializerMutation` hook returning a mapping keyed by a `TextChoices` or `StrEnum` member is
  admitted: `rest_framework/resolvers.py::_hook_mapping` refuses only a non-`str` key and keys the result by each key's
  exact text, so the member answers like its plain-`str` twin and a member spelling a reserved, undeclared or
  model-field name is refused with the plain name's message. The library member-key live rows pin it; spec-039 says so.
  The `rest_framework/sets.py` Meta-map key gates stay exact-`str` (dry-0_0_15_3 item 44)
- [x] 429. fixed: under the async executor a plain sync root or nested resolver that returns a lazy `QuerySet` to a list
  field answers with the sync view's rows and SQL: the dependency-owned `_graphql_core_patches` list-completion arm wraps
  a Django `QuerySet` in the async completion adapter so it is fetched through `__aiter__` off the loop (a sentinel
  retires it once graphql-core completes async-first), and `DjangoOptimizerExtension.resolve` builds a sync root's plan
  in one `sync_to_async` worker, so planned targets' `get_queryset` hooks never run on the loop. The library loan grid
  (all 15 cases), the fetched-annotation twin and the scalars, kanban and generic-connection async rows pin it; the
  README, spec-002, 035, 050 and the glossary say so
- [x] 390. fixed with 429: `allScalarSpecimens` and `allCards` answer on the async view with the sync view's rows and SQL.
  A plain `def` resolver still runs on the loop, so code that evaluates a queryset, and an `apply_sync` call's
  validation, permission gates and related `get_queryset` hooks, belong in an `async def` resolver awaiting
  `apply_async`; the README and the `djangographqlview` and `get_queryset` glossary terms say so, and the
  eager-evaluation library root pins the raise
- [x] 53. superseded by 429: a hand-written `@strawberry.field` returning a lazy QuerySet completes off the loop on the
  async executor, and the README async paragraph under `DjangoListField` says so
- [x] 318. fixed: the cited row (`tests/filters/test_sets.py::test_an_unordered_meta_fields_expands_in_canonical_order[set
  of lookups in a dict]` under `PYTHONHASHSEED=28`) already passes since `bf370934`; the residual is fixed here. Every
  row that needs a set iterating out of canonical order now builds it through one shared helper,
  `tests/_idioms.py::scrambled` (subsets x layouts: the constructor, `dict.fromkeys`, sets grown through padding, and
  `frozenset` copies of them; fails loudly when none scrambles, and asserts the result really does), with
  `canonical_order` beside it. The filters (`_CATEGORY_COLUMNS` plus `"id"`, both kinds), orders and utils rows use it,
  the two `read_set_meta_fields` rows over 4-name pools, so the frozenset rows no longer flake (seed 10332), the orders
  twin no longer flakes (4124 / 4176 / 18433), and the utils rows fail on every seed with `_sorted_meta_values`
  unsorted (they passed on 25% / 50%). 0 misses over seeds 0..20000 for every pool used (3.14), 0..4999 on 3.10;
  `tests/test_idioms.py` pins the helper
- [x] 330. fixed: `scripts/prove_failability.py::_resolve_scratch_root` names the default scratch parent per user,
  `<system temporary directory>/failability-<uid>` (`DEFAULT_SCRATCH_DIRECTORY_PREFIX` plus `os.getuid()`, as pytest's
  `pytest-of-<user>`), so a second user on a shared Linux `/tmp` gets a parent of their own instead of a refusal on
  every default run; the owner / symlink refusal is unchanged and still guards a squatted per-user name, and an
  explicit `--scratch-root` behaves as before. A two-uid row pins it (it fails through the real refusal with the
  shared name); the module docstring, the `--scratch-root` help and `docs/builder/BUILD.md` say per user
- [x] 585. Not a defect under rule 37: no contract row covers a `RawQuerySet`. The async completion arm, the
  `async-queryset-completion-adapter` glossary term and spec-050 Decision 12 adapt a Django `QuerySet` only and leave
  every other value on graphql-core 3.2's synchronous completion, and the `get_queryset` seal already refuses a
  `RawQuerySet`; the README async sentence now says "lazy `QuerySet`". Fact finding: a plain or `async def` root, or a
  nested resolver, returning `.raw(...)` raises `SynchronousOnlyOperation` on the async executor with the optimizer on
  or off and answers on the sync one; a `DjangoListField` / `DjangoConnectionField` `resolver=` returning one raises
  there in the package's own row iteration. Widening the arm to `RawQuerySet` is two lines, and graphql-core 3.3
  completes it async-first
- [x] 583. not a defect: a hook's mapping keys are application Python (GOAL "Trust boundary") and no wire input
  reaches them; `utils/truth.py::render` documents that a value outside the builtin scalars renders through its own
  `__repr__`, which is what a lazy translation proxy's `'a'` is, and the refusal states the rule ("every key must be a
  string") beside it, so no code
- [x] 580. not a defect: a `check_<field>_permission` name is application Python (GOAL "Trust boundary"), and no
  contract row says a FilterSet / OrderSet gate whose name matches no gated input is detected; gates are dispatched by
  name at request time, as DRF's `validate_<field>` methods are, so a misspelled one is never called there either.
  A finalize audit of gate names would be a new card, not a fix
- [x] 331. fixed: `scripts/workspace.py::ensure_floor_venv` decides reuse with one read
  (`_read_text_if_present(key_path) == key`), so a key the macOS `$TMPDIR` purge removes after the check reads as "no
  key, rebuild" instead of a `FileNotFoundError` traceback out of `gate`. The same file's other purge-reachable
  check-then-act windows read a vanished entry as already gone: `gc`'s size sum (`_stat_key`), `_remove_flow_dir`'s
  file and legacy-marker-file unlinks, `_same_entry` (one `_stat_key` read; a destination gone before its hash reads
  as not the same, so it is copied), and the `_copy_entry` / `_remove_unwanted` unlinks (`missing_ok`); only a
  missing entry is absorbed. One row per window (`_run_once_before_reading` / `_run_once_after_checking`), each red
  with its fix reverted
- [x] 406. not a defect: the README "Single-parent fast path" paragraph promises the fast path for exactly one parent
  and calls every other shape "a performance downgrade, never a wrong page"; a root `first: N` page's probe row
  (Strawberry's `ListConnection` overfetch, the keyset `NEXT_PAGE_PROBE_ROWS`) is a fetched parent, so its pk joins
  the nested prefetch's parent `IN` list and the planned window runs. Every page is correct and the statement count
  is unchanged; a plain list relation prefetches the probe parent's children too. Upstream strawberry-django
  prefetches the probe row the same way. Prefetching only the page rows touches every root connection path (offset,
  keyset, async, `hasNextPage`); that is a new card, not a fix
- [x] 407. test gap closed, not a defect (behaviour matches the README transport-support paragraph and the "younger
  than" window in `consumers.py` / spec-046): `tests/auth/test_sessions.py` pins that a custom client-side engine
  outside the signed-cookie hierarchy reads as server-side (WebSocket logout supported), and `tests/test_routers.py`
  pins `_actor_is_current`'s strict window edge (ages 7.5 / 8.0 / 8.5 on an 8.0 window: 0 / 1 / 1 session reads, the
  stamp rewritten only on a read) and that a 0.0 window never writes the revalidation stamp; each row kills a mutant
  the suite let through (a non-DB-store test, `<=`, an unconditional write-back). Package tier: fakeshop has no
  WebSocket mount
- [x] 329. fixed: no signal-forwarding `uv` sits in the process group a stop is sent to.
  `scripts/_stop_signals.py::uv_run_launch` resolves the environment `uv run` gives a command once (`uv run ... --
  env -0`, the same sync) and the command is started directly in it, so `scripts/prove_failability.py`'s scope is
  pytest itself and `scripts/workspace.py`'s `run` / `prove` and the gate's non-floor suites start their command with
  no uv between; each process gets each stop once. The second `SIGINT` uv sent about 0.2 s later aborted a pytest
  teardown still running (a `-n0` scope's finalizer, interrupted 0.07 s in), which now completes; group signalling,
  the grandchild ending on the first stop and the `SIGKILL` escalation are unchanged, and the env, cwd, `sys.path`,
  plugins and settings match `uv run`'s field for field. The docstrings say `SIGINT`'s teardown is allowed to finish
  and `SIGTERM` / `SIGHUP` / `SIGQUIT` end pytest without one; a wrapper a user's own command starts still
  double-delivers. Uv-shaped forwarding stand-in rows pin both tools, and the gate row pins the suite's cwd
- [x] 404. fixture gap closed for the reverse-FK serializer path (not a defect): fakeshop's library app gains
  `BranchShelvesSerializer` (`shelves = PrimaryKeyRelatedField(many=True)` over the reverse FK) and
  `createBranchViaShelvesSerializer` / `updateBranchViaShelvesSerializer`, whose live rows pin the `[Int!]` input, one
  batched visibility read, attach-only writes and the hidden-shelf `shelves` relation error with no write; the
  package stand-in `test_many_pk_related_field_over_reverse_fk_column_emits_multi` is deleted, its lines and mutants
  all covered live. The `CompositePrimaryKey` and `db_column=` gaps are `docs/builder/TODO.md` item 27's
- [x] 405. the package row was not yet redundant, so it is promoted, then deleted: the live
  `_NEGATIVE_CURSOR_ROWS` gain a `before` + `last` row (sync and async sequence resolvers; the only live killer of a
  `before` decode skipped unless `first` is set or `last` is unset), and `test_minted_offset_cursors_still_page` now
  pages the root `QuerySet`, the list resolver and the tuple resolver from a minted `after` (a valid `after` serving
  an empty sequence page now fails live). `tests/test_connection.py::
  test_consumer_resolver_sequence_negative_cursor_raises_graphql_error` is deleted, every mutant it killed failing a
  live row
- [x] 319. fixed at the root: a flat copy of a child leaf (`books__probe`, from a `RelatedFilter`) is a spelling of
  the request, never a field of the parent's form. `filters/sets.py::FilterSet.get_filters` defers every copy, a
  request binds only the copies whose widgets read a key it sends (`ExpansionSnapshot.copy_keys`, exact keys:
  `__low` / `_min` widget keys included, so `booksProbeMin` never binds `books__probe`), `get_form_class` builds the
  bound form from the set's own filters and those named copies, and `_apply_flat_leaves` never applies an unnamed
  one; the static "absence filters nothing" proof (`_absence_filters_nothing` and its helpers) and the form-reading
  exemption are gone. A leaf whose absence acts (`required`, a checkbox, `empty_value`, `null_value`, a disabled
  `initial`, a project `filter` that does not skip the empty value) acts only on the form of the set that declares
  it: its own root, or an active nested branch. So `{}` and unrelated leaves no longer return nothing or
  `FILTER_INVALID`, `books: {probe: ...}` answers as `booksProbe` does (it ran the leaf twice, once with the absent
  value), and `or` / `not` arms agree; a nested sibling leaf still runs the child's form. A project form `clean` that
  reads an unnamed copy uses `.get`, and an unnamed copy on a form of your own is never applied but still validates.
  Package rows pin the grid, the gate and async paths and the exact naming; fakeshop gains `IssueFilter`
  (`embargoed`, a `CheckboxInput` `BooleanFilter`) and `PeriodicalFilter` (`issues = RelatedFilter`) with live
  rows, sync and async. README, the `filterset` glossary term and spec-027 say so. Breaking (pre-1.0)
- [x] 332. fixed: `scripts/workspace.py::_remove_flow_dir` clears the marker's contents before `marker.rmdir()`, through
  the one per-entry loop it empties the flow folder with (`_empty_folder`: a real directory through `rmtree`, anything
  else unlinked, a symlink never followed), so a Finder `.DS_Store`, a stray folder or a symlink inside `.dsf-ws` no
  longer makes `gc` raise `OSError` (Errno 66) on every rerun; the marker proves ownership by existing, never by being
  empty. A `.dsf-ws` that is itself a symlink is unlinked, never emptied through. The marker still goes last (a new
  row pins it: a `gc` cut short inside the flow folder keeps the marker and the next one finishes), and the parametrized
  litter row covers a file, a folder, a symlink inside and a symlinked marker, outside targets intact
- [x] 345. fixed: `scripts/workspace.py` keeps a flow's bindings in the XDG state home
  (`<state home>/dsf-ws/<sha16 of the workspace base>/<flow>/state.json`, through the prover's `state_home`, folders
  at `0o700`), never in the system temporary directory, so neither the macOS `$TMPDIR` purge (birth time and atime
  both over 3 days; a read does not renew atime on APFS, so a flow used only through `run` aged out) nor a Linux
  `/tmp` that a reboot empties (tmpfs) or systemd-tmpfiles cleans loses them: the next command no longer renumbers
  slots, resyncs other slots over their edits or runs a duplicate of a held address. `gc` and `release` remove or
  rewrite the state, also for a flow whose temporary folder is gone, and `status` lists flows from both; a state file
  an older version left in the flow folder moves to the state home under `pool.lock`. The module docstring and
  START.md say what survives where on macOS and Linux. Rows pin the location and mode, a purge of every file, a
  removed base, the lifecycle, the migration and its read race
- [x] 402. not a defect, confirmed: `mutations/inputs.py::build_mutation_input` reads
  `relation_bool(field, "many_to_many")`, and only the model and user flavors call it, over
  `editable_input_fields`, which drops every reverse and virtual relation (no column or `editable=False`) and
  refuses one named in `Meta.fields` / `exclude` with `ConfigurationError`; a reverse kind never reaches the read. Over
  775 reaching (model, operation, field) rows the read and `model_column_write_kind(...) == RELATION_MULTI` agree,
  and routing it through the classifier leaves the printed schema and every generated input byte-identical. The
  forward-M2M optional rule is pinned live by `test_input_shapes_api.py`. No code
- [x] 403. fixed (docs): spec-027 and spec-028 gain an Edge-cases row each, and the `filterset` and `orderset`
  glossary terms one sentence each, stating that a one-shot (`iter(...)`, a generator, `map(...)`) or bare-string
  `Meta.fields` / `filter_fields` / `Meta.exclude` is a `ConfigurationError`: a FilterSet's at class creation, an
  OrderSet's at the first `get_fields()` expansion (finalize); a `SimpleLazyObject` is judged as the object it stands
  for and `filter_fields` is reported as `Meta.fields`. No code
- [x] 381. fixed: a write input datetime or time the target database cannot store (on SQLite / MySQL / Oracle the
  values `unbindable_temporal` refuses; on PostgreSQL also an aware datetime whose wall clock in the connection's zone
  leaves years 1..9999, stored but not loadable at the re-fetch; each element of an `ArrayField` of either) is the
  field-keyed `FieldError` "Enter a value the database can represent." code `invalid` in the payload, nothing
  written, in the model, ModelForm and serializer flavors, checked on the value each flavor will store after its own
  validation (`utils/errors.py::unstorable_temporal`, `utils/write_values.py::unstorable_temporal_error`) against the
  pinned write alias; the serializer cells where DRF itself raises a raw `OverflowError` stay masked (540). A new
  fakeshop scalars write surface and its live rows pin it, with package rows for PostgreSQL and the MySQL / Oracle
  adapters; the README, spec-036, 038, 039 and the `fielderror-envelope` glossary term say so
- [x] 401. fixed: the model flavor's create answers an input that leaves out a `blank=True, null=False` column with
  no default (fakeshop `createItemHold` without `itemId`) with that column's field-keyed `null` error (`itemId`, "This
  field cannot be null.", code `null`), nothing written, as the ModelForm flavor does; the diagnosis reads the
  in-memory instance after the failed INSERT (`mutations/resolvers.py::_created_row_integrity_errors`), so a
  consumer `save()` that fills the value still writes, and shares one predicate with the ModelForm
  (`utils/write_values.py::unstorable_columns`). Live rows pin omitted and `null` on both flavors, sync and async;
  spec-036, spec-038, the README and the `DjangoMutation` / `fielderror-envelope` glossary terms say so
- [x] 586. fixed: an update input over a model with a `CompositePrimaryKey` leaves out every member column of the
  key, as it does a `OneToOneField(primary_key=True)` or a text key, in the model, ModelForm and serializer flavors;
  one predicate (`utils/relations.py::is_row_key_column`: the column's own pk flag, or membership in its declaring
  model's `pk_fields`) answers row identity for the three input builders and `located_row_update_fields`. Package
  rows pin the predicate over auto, one-to-one, text, multi-table and composite keys, each flavor's input and a sync
  and async update over a real composite table; the live row waits on a fakeshop composite model
  (`docs/builder/TODO.md` item 27). The README, spec-036, 038, 039 and three glossary terms say so
- [x] 353. fixed: `nodes(ids:)` keeps Django 6.1 peer batching. `relay.py::_stamp_nodes` stamps each `resolve_nodes`
  group, then gives the copies whose originals shared one `_state.peers` list a fresh list of weak references to the
  copies, so a lazy FK across 3 loans under `FETCH_PEERS` costs 1 query instead of 3 (sync and async, a repeated id
  included), as the connection and list roots already did; a consumer `resolve_nodes` override's rows batch the same
  way, a row with no peers is left alone, and the shallow copy that keeps a shared row free of the routing hint
  stays. The `_state.peers` read and write live in `utils/_queryset_private.py`. Found verifying 353: row 506
- [x] 503. fixed: a `FILTER_INVALID` error's `errors` keys carry the field's path from the filter root, so a nested
  `RelatedFilter` branch's leaf is `<declared branch>__<leaf>` (`shelf__branch__name`, the flat copy's own key), an
  `and` / `or` arm's is `<op>_<index>__<leaf>` with `not` bare (`or_0__title`, `not__title`, upstream's arm token),
  nesting either way in request order, and a nested form's non-field error is `<path>____all__`; root keys stay
  bare. One owner spells the segment (`filters/sets.py::_branch_key`, the arm token by
  `filters/inputs.py::LogicOperatorDescriptor.arm_key`), the path rides where the nesting depth already travels, and
  the one raise site keys every entry, sync and async alike. Permission denials are unchanged and not a defect: the
  documented message names the gate, which the nested and flat spellings already answer identically. Live rows pin
  branches, arms, both nestings, flat copies inside each and a fakeshop `ShelfFilter` form-level refusal, sync and
  async; the README, spec-027 and the `FilterSet` glossary term say so
- [x] 383. fixed: a per-field `"__all__"` publishes Django's text-pattern lookups (`iexact`, `contains`,
  `startswith`, `endswith`, `regex` and their case-insensitive forms) only on a text column, one whose package default
  filter is `CharFilter` (`CharField` and subclasses, `TextField`, `GenericIPAddressField`, `FilePathField`); a date,
  time, number, Boolean or UUID column keeps `exact`, `in`, `isNull` and its comparisons. A column whose filter the
  consumer supplies (`Meta.filter_overrides`, a `FILTER_DEFAULTS` of its own) keeps the whole bag as before. A pattern
  lookup listed by name on a non-text column generates a `TextPatternFilter` (a `CharFilter`) typed `String`, matched
  against the backend's text rendering of the column as Django's ORM matches it, so no generated leaf answers the masked
  error or a silent `[]` for a value the backend cannot use; the right-hand side of a leaf is typed by what Django
  compares (spec-027). Live rows on SQLite and PostgreSQL, sync and async; package rows per column kind and override
  shape; README, spec-027 and the `FilterSet` glossary term say so
- [x] 423. fixed: a `DjangoModelFormMutation` input is typed by the shape its form field reads wherever that shape
  disagrees with the column: besides 305's multiple-choice field over a single-value column, a built-in single-value
  form field (`ChoiceField`, `TypedChoiceField`, `CharField`, `IntegerField`, `DecimalField`, ...) over an `ArrayField`
  takes one value (a `ChoiceField` over an `ArrayField` whose base field lists choices takes that element enum,
  narrowed by the form's choices), the form's `clean_<field>` turning it into the column's list; the package never
  wraps it. Which form fields read a list is one converter-owned fact
  (`forms/converter.py::form_field_reads_list`, `form_field_reads_one_value`), so the default `SimpleArrayField`,
  `SplitArrayField`, `MultipleChoiceField`, `JSONField` and any form field the converter does not register stay typed
  by the column as before. An omitted update binds the form's initial, one build warning per such field names its
  direction, and the predicate and helpers are renamed for the shape disagreement. Package rows on SQLite and a real
  PostgreSQL `ArrayField`; spec-038 Decisions 7 and 8, the README and the `DjangoModelFormMutation` glossary term say
  so
- [x] 372. fixed: a declared package `RangeFilter(lookup_expr="range")` with both bounds on an integer column applies
  them as `gte` + `lte` in one `_apply_lookups` call (as `filters/base.py::IntegerRangeFilter` does), so a bound past
  the column's range widens or matches nothing through Django's range-aware lookups instead of reaching `BETWEEN` as a
  masked `OverflowError`; other column types keep `BETWEEN`. A declared `ListFilter(lookup_expr="in")` on an integer
  column drops the members outside the column's integer range on the queryset's database
  (`filters/base.py::_backend_storable_int_members`) and matches nothing when none is left, without applying the
  column's own validators. Each declared cell on `ScalarSpecimen.signed_big` / `unsigned_big` answers as the generated
  `range` / `in` does, flat and under `not`. Found verifying 372: rows 507-509
- [x] 375. Not a defect under AGENTS rule 37 (no wire input reaches it): a declared `RangeFilter` / `ListFilter` whose
  `field_name` names a relation (`fk`, `fk_id`, a reverse or many-to-many accessor) fails the schema build with a
  `ConfigurationError` (`filters/inputs.py::_scalar_from_model_field`) for every primary key type, so no GraphQL
  request carries a bound; a `<relation>__id` path resolves to the target's column, whose `gte` form field cleans it
  (`FILTER_INVALID` for `NaN` / `Infinity`), and on every shape that builds a target row its `get_queryset` hides
  answers `[]` as a missing one does, so no existence oracle exists. The pass-through is spec-027's written
  `RangeFilter` / `ListFilter` rule ("a relation's bound reaches the ORM as sent"), pinned by
  `tests/filters/test_base.py::test_range_filter_without_a_column_form_field_passes_bounds_through`. Under a
  consumer's `DjangoFilterBackend` (no schema build) a range on a relation raises `FieldError` for every value, valid
  ones included, as django-filter's own `RangeFilter` does. Probed over 5 primary key types x 6 relation kinds x 4
  spellings. Found checking it: rows 510-512
- [x] 376. A package `RangeFilter` / `ListFilter` / `ArrayFilter` declared on a plain `django_filters.FilterSet`
  (a consumer view with DRF's `DjangoFilterBackend`) cleaned no bound or element: `filters/base.py::_column_form_field`
  answered a cleaner only under a package `FilterSet` parent, so a query-string bound the column cannot hold
  (`?price_span_0=NaN`, a malformed UUID or datetime, a NUL on PostgreSQL) reached the ORM and raised (HTTP 500). Any
  django-filter `FilterSet` parent now cleans, so the backend answers the form error with its 400; the field is the
  one the parent's class selects without the package `FilterSet`'s own `filter_for_lookup` override (a package
  subclass reads the method behind that override as before, any other set its own `filter_for_lookup`). A package
  parent's generated filters and cleaners are unchanged. Found verifying it: row 514
- [x] 382. fixed: on PostgreSQL a temporal filter or write value whose UTC offset the server refuses answers the
  documented envelope (`FILTER_INVALID` "Enter a value the database can represent." on the read side, the field-keyed
  `FieldError` on the write side, nothing written) instead of the masked error:
  `utils/errors.py::unbindable_temporal` reads the connection's binding mode without opening it; an aware time is
  refused at an offset of 16:00 or more, and, when the connection binds on the client (psycopg2, psycopg 3's default),
  an aware datetime or time also at a sub-second offset; under server-side binding a datetime's offset never refuses
  it. An `ArrayField` write element is bound as text in either mode, so it is held to the client-side rule through
  `unstorable_temporal`. A `date` / `year` transform never binds the offset and keeps filtering. Live rows on SQLite and
  PostgreSQL (filter and the three write flavors, sync and async), package rows per binding mode on a real server;
  spec-027, spec-036, spec-039, the README and the `FilterSet` and `FieldError` envelope glossary terms say so
- [x] 509. fixed: an identity decode (the generated integer `in` and the declared `ListFilter`, `node` / `nodes`, the
  GlobalID filter, the raw-pk relation filters, raw-pk and GlobalID write ids) finds a stored row whose value a
  validator would refuse: `utils/querysets.py::coerce_field_value_or_none` never runs validators; it casts with
  `to_python`, binds through `Field.get_db_prep_value` on the database the lookup reads (the queryset's `db`, else
  `lookup_read_alias`), and holds the value to the column's storage domain (PostgreSQL's refused UTC offsets, the
  integer range, a decimal the column can hold, read by value not spelling), so a value the backend cannot bind still
  names no row. Fakeshop `signed_big` and `Publisher.house_code` carry validators; live rows pin flat and `not`
  parity, `node` / `nodes`, the GlobalID filter and `createEdition`; spec-032 Decision 5 says so.
- [x] 400. fixed: a `FilterSet` whose `Meta.exclude` is set and whose `Meta.fields` is not is the whole-set sweep,
  exactly as `fields = "__all__"` with the same exclude: the primary key is added (a Relay owner's own pk as its
  GlobalID filter) and every forward many-to-many is removed, where it published django-filter's raw sweep (no auto pk,
  many-to-many keys included). A primary key named in `Meta.exclude` is never added back by the sweep (auto, non-auto,
  a multi-table child's parent link), under either spelling. One owner (`filters/sets.py::FilterSet.get_fields`); an
  explicit field list or dict with `Meta.exclude` is unchanged. The library example gains an exclude-only and a
  pk-excluding whole-set filterset on secondary types; live rows plus package rows over the shape grid; spec-027, its
  rationale, the README and the `FilterSet` glossary term say so
- [x] 373. A declared `django_filters.LookupChoiceFilter` filters by a value plus a `<name>_lookup` key, which no
  GraphQL input carries, so it refused every non-empty value; declared without `lookup_choices` it was worse: building
  the schema read `.field` on the class-level declaration (`filters/inputs.py` catch-all and `method=` fallback, and an
  unbound projected child leaf in `filters/sets.py::ProjectedChildFilter.field`), which cached a half-built field there,
  so every later request raised an unmasked `AttributeError` and a `DjangoFilterBackend` view on the same `FilterSet`
  broke too. Those reads now run on a deep copy (`filters/base.py::copied_form_field`), so building the schema writes
  nothing to any declaration, and a `LookupChoiceFilter` (or subclass) on a served `FilterSet` is refused with
  `ConfigurationError` at schema build, before its field is read; the declaration still filters under django-filter
  and DRF
- [x] 399. fixed: a hop-walking flat leaf (an owner-bound projected copy or a plain walked copy) whose value is
  supplied runs its child filter body once per value, over the hop's visible rows, where it ran twice (an unscoped
  activity probe whose result was discarded, then the apply), so a consumer `method=` body ran twice and one reading
  the database cost a query more flat than nested; a result that is its input by identity is inactive and leaves the
  parent unchanged, the hop chain is derived once, and a supplied-but-inactive leaf (`""`) now derives its hops once
  on sync as on async. An absent leaf keeps the unscoped probe (an inactive one runs no `get_queryset`), so a consumer
  filter acting on an omitted value behaves as before. A projected copy through an unresolved `RelatedFilter(None,
  ...)` hop answers `ConfigurationError` like a plain walked leaf, where it raised `RecursionError`. One owner
  (`filters/sets.py::FilterSet._apply_relation_leaf`); package rows count body runs, queries and derivations sync and
  async, live empty-value rows pin the identity exit; spec-027 and the `FilterSet` glossary term say so

- [x] 500. fixed: `tests/test_ci_governance.py::test_no_comment_docstring_or_name_carries_a_provenance_phrase` refuses
  `pre-fix`, `post-fix`, `before the fix`, `after the fix`, `formerly`, `exactly as before`, `used to`, `previously`
  and `as of 0.0.` in every comment, docstring and def/class name of the sweep corpus (case-insensitive, word-bounded,
  matched across line wraps; no exclusion, no marker), with a planted row per phrase and per wrap shape; the 137 hits
  it found (package, four test trees, examples and scripts) state behaviour, each counterfactual checked against the
  test that asserts it or a guard-removed probe, the 16 non-historical uses rephrased; the item's named sites, the
  rest of their functions and 324's two residual sites restated too, with the `apply_cascade_permissions` glossary
  twin. Code digest unchanged outside the gate row and two renamed tests; START's rule names the gate and its phrases
- [x] 567. fixed: the flow docs cite each prose rule at its home: no process provenance at START.md "Style the
  maintainer cares about", `path::Symbol` citations and the test tier at AGENTS.md (`docs/bug_hunt/HUNT.md`
  step 8, `docs/bug_hunt/worker-2.md` and `docs/dry/worker-2.md` step 7, `docs/dry/DRY.md` Worker-2,
  `docs/review/REVIEW.md`'s process-provenance grade); no rule is added to AGENTS.md
- [x] 506. fixed: `tests/base/test_init.py::test_annotations_evaluate_without_django_stubs_ext_patch` binds the real
  object for every `if TYPE_CHECKING:` import that resolves at runtime to a class or module (per alias, nested
  `if`/`try` branches included, `django_stubs_ext` never bound, the process asserted unpatched after the binding), so
  a TYPE_CHECKING-only head hides no subscript; the 25 annotations it then finds (the item's five plus 20
  masked ones: `Options` x16, `BaseIterable` x2, `UploadedFile`, `Lookup`, `Field` x2 in
  `utils/write_values.py::unstorable_columns`) go through a module-private `if TYPE_CHECKING:` alias with a bare-class
  `else:`, so no package annotation subscripts a Django class without `__class_getitem__`; static types unchanged; red
  on every Python/Django cell, not only the floor
- [x] 549. not a defect: no README, GLOSSARY, spec or test row promises what a pattern value the backend refuses
  answers; `FILTER_INVALID` covers a closed list (a value the form field rejects, text the package refuses to store, a
  temporal value the database cannot bind, an unholdable range or list bound) and spec-027 keeps pattern lookups out
  of the temporal check, while a `regex` / `iRegex` operand is a plain `CharField` value the form accepts and the
  backend refuses only when the lazy queryset runs (SQLite: `OperationalError` from Django's Python `re` user
  function, only when a non-NULL row is scanned; PostgreSQL: `DataError` SQLSTATE 2201B on any table), masked as
  GOAL's error policy intends. Django, django-filter, DRF `SearchFilter`, graphene-django, django-graphene-filters and
  strawberry-graphql-django validate no pattern and map no such error. The promise question is row 571
- [x] 541. fixed: on PostgreSQL a `DjangoModelFormMutation` whose optional single-value form field (`ChoiceField`,
  `TypedChoiceField`, `CharField`, with no `clean_<field>` or one wrapping only a non-empty value) cleans `""`, an
  explicit `null` or an omitted create value to `""` over a `blank=True, null=False` `ArrayField` answers that
  column's field-keyed `null` error with nothing written (create, update, client-assigned-key create, sync and async),
  since the save-time diagnosis runs on the save's `DataError` (malformed array literal) as on an `IntegrityError` /
  `ValueError`; a `DataError` no column explains propagates. Not a defect: a non-empty value the consumer's form
  leaves un-wrapped fails inside `is_valid()` with Django's own `JSONDecodeError` / `TypeError`, as the docs now say
  (the form owns the wrap, as upstream). README, GLOSSARY and spec-038 name the `ArrayField` beside the non-text
  choice column; package rows on PostgreSQL
- [x] 551. not a defect: spec-038 Decision 7 types a model-less form field by its registered class through a
  `type(field).__mro__` walk, with no row for a PostgreSQL form field, so `SimpleArrayField` (a `CharField` subclass)
  is `String`, pinned by `tests/forms/test_converter.py::test_postgres_array_form_fields_read_a_list`; no README,
  GLOSSARY or spec row gives it another type, `form_field_reads_list` is read only for a field over an `ArrayField`
  column (423), and graphene-django publishes it as `String` too. Every wire value either cleans (delimited text split
  on the field's `delimiter`, each item cleaned by the base field; an empty or omitted optional value is `[]`) or
  answers a field-keyed `required` / `item_invalid` error. Whether it should publish the base field's list is row 576
- [x] 542. not a defect: on PostgreSQL only a consumer-declared DRF `ChoiceField` reaches it (every other single-value
  DRF field over an `ArrayField` is refused at build, row 46); `is_valid()` accepts the choice and the save fails on
  the scalar the serializer never wrapped (`DataError` on a text array, `ProgrammingError` on an integer one), which
  plain DRF answers with a 500 and the README answers as a top-level error ("any other exception from that code ... is
  a top-level error"); no README, GLOSSARY or spec-039 row types the field or promises a field-keyed answer. Whether
  it should build at all, or carry a documented `validate_<field>` wrap as the form flavor's `clean_<field>` does, is
  Waiting row 45 (now with the Postgres evidence). The serializer's own empty-value and omitted-create gap is row 577
- [x] 552. not a defect: the refusal is the converter's written fail-loud contract; spec-038 Decision 7 registers each
  supported form-field class individually and "requires NOT registering a base-`forms.Field` catch-all", so a field
  with no registered ancestor raises `ConfigurationError` naming the field and class
  (`forms/converter.py::_unsupported_form_field`), and `SplitArrayField` subclasses `forms.Field` directly (Django
  5.2.16 and 6.1.2 alike). graphene-django types it `String` only through the catch-all the package refuses. Whether a
  column-less PostgreSQL form field should publish a type is Waiting row 576 (facts gathered fixing 551)
- [x] 553. fixed: a `ModelForm` field over a column whose widget reads other keys than its name is bound under the
  keys that widget reads, at every place the package puts a value into the form's data (the decoded input, the
  omitted-update reconstruction, an omitted field's initial, the prefix re-key, and a mapping a `get_form` hook keyed
  itself, a `QueryDict` holding a list per key included): a `SplitArrayWidget` reads `<key>_0 .. <key>_{size-1}`,
  padded with `None` so an explicit `[]` is not omitted, and a `MultiWidget` its own suffixes, split by its
  `decompress` (recursively); the whole value stays under the field's key beside its parts, and a `disabled` field is
  bound whole. So a `SplitArrayField` over an `ArrayField` writes the list sent (where every write answered "This
  field is required.", or an optional field reported success writing `[]`, the column default or `[null, ...]`, and an
  update omitting it erased the stored list), and a `SplitDateTimeField` over a `DateTimeField` writes the datetime
  sent; a list longer than `size`, sent or reconstructed, is refused with `ArrayMaxLengthValidator`'s `max_length`
  error instead of being truncated. `utils/widgets.py` owns which keys a widget reads for filters and forms
  (`multi_widget_keys` moved there unchanged; Django 5.2.16 to 6.1.2 audited). Live rows through a fakeshop scalars
  split-datetime form, package rows on PostgreSQL; README, GLOSSARY and spec-038 say so
- [x] 507. not a defect: spec-027's integer-range promise names the package's `RangeFilter` and `ListFilter` (and the
  generated `IntegerRangeFilter` / `IntegerInFilter`), README keeps a filter you declare yourself on django-filter's
  own rules, and `FilterSet._apply_flat_leaves` runs a declared django-filter class byte-for-byte, so django-filter's
  `RangeFilter`, a `BaseRangeFilter` or `BaseInFilter` over `NumberFilter` on a `BigIntegerField` /
  `PositiveBigIntegerField` column (the only columns whose `BigInt` input carries a value past int64) answers a
  two-bound range or a member past int64 as Django and plain django-filter answer it: a masked `OverflowError` on
  SQLite and on PostgreSQL under server-side binding, the right rows under psycopg 3 client-side binding; a lone bound
  and `exact` / `gt` / `lt` are right everywhere. spec-027's `RangeFilter` row claimed django-filter's bounds are
  cleaned by the column's `gte` field and held to its `1e50` cap; it now scopes that to the package's class and states
  django-filter's own `RangeField` cleaning. Whether to hold declared django-filter range / `in` classes to the
  backend's integer range is Waiting row 622
- [x] 554. not a defect: the write is the stated contract. spec-038 Decision 8 binds an omitted shape-disagreeing
  field from the form's initial (`forms/resolvers.py::_bind_omitted_shape_disagreeing_initials`), so a form presenting
  one stored element keeps the row and one that does not fails validation or, through a field that accepts the stored
  list itself (a `CharField` reads its text, a `BooleanField` its truthiness), "writes the value it makes of it"; the
  GLOSSARY `DjangoModelFormMutation` term says the same, and the update's schema build logs a warning naming the field
  and the initial it needs (`forms/inputs.py::_advise_shape_disagreement`). The form owns the wrap and its initial, as
  for 541 and 542. Whether the package should refuse such an update instead is Waiting row 623
- [x] 508. parked into Waiting row 316, which asks the maintainer this same question; 316 now carries the evidence and
  a third option (two bounds compare as a range, input unchanged), prototyped and verified with no cell narrowed
- [x] 510. fixed: a declared filter whose `field_name` is `pk` or `<relation>__pk` reads the column the key stores, as
  the column's own name does: `filters/base.py::_filterset_resolved_field` resolves the path through the package's own
  walker (`utils/relations.py::_classify_path_cached`, which reads `pk` at any segment; a path it refuses keeps
  django-filter's `get_model_field` answer) and follows a relation-valued key (a multi-table parent link, a one-to-one
  primary key) to its stored column with `utils/relations.py::stored_value_link`. So a `RangeFilter` / `ListFilter` /
  `IntegerInFilter` / `CharFilter` leaf on `pk` is typed by that column (`Int`, `BigInt`, `Decimal`, `UUID`, where it
  was `String`), its bounds and elements are cleaned by the column's form field (`FILTER_INVALID` or a coercion error
  where a malformed value was a masked error), the integer range rules apply, and a `RangeFilter` over a
  relation-valued key binds every bound on the stored column's path (`pk__id`) with no added join, where a two-bound
  range was Django's refusal. 375's refusal for a relation named explicitly stands. Live rows on library `ShelfFilter`
  / `PatronProfileFilter` `pk` leaves, package rows for Decimal, UUID, multi-table and composite keys; spec-027 says
  so
- [x] 593. AGENTS.md is cited by content, not by line ordinal: 32 drifted cites (6 "rule 27" in `django.yml`,
  `.pre-commit-config.yaml`, `scripts/check_citations.py`, `scripts/review_inspect.py`; 3 in
  `docs/review/REVIEW.md`; 6 in `MUSE.md`; 17 in 13 KANBAN `CardItem` rows) and the still-correct ones
  (HUNT.md, FIX.md, FIX-PROMPT.md, spec-048, `tests/test_ci_governance.py`, gated `AGENTS.md #"..."` pinpoints
  there) now name the rule; `docs/builder/ARTIFACT.md` sends the kept spec-pointer rule to START.md "Style the
  maintainer cares about"; FIX.md phase 4 sends exported surface to docs/TREE.md and the check-public-types
  hook; START.md stops calling AGENTS numbered; three stale AGENTS-heading cites in scripts/tests fixed.
  Closed history left as written
- [x] 511. fixed: a raw-key relation filter coerces its key through the column the compared key stores, wherever the
  leaf runs: a to-many key leaf (forward many-to-many, reverse foreign key, reverse many-to-many) walking a visibility
  hop (a target type with its own `get_queryset`, or a `RelatedFilter` declared on the relation) compares the target
  rows' own key column, and `filters/base.py::_raw_identity_column` now reads that column (a plain column, or a
  relation-valued primary key followed to the column it stores, a one-to-one onto a non-pk `to_field` included), where
  `_coerce_relation_identity` passed the value through. So a `Decimal` key `NaN` / `Infinity` or an aware datetime the
  backend cannot hold matches nothing there, as it does on the unhopped leaf, instead of a masked error, and a visible
  key into a target keyed by a one-to-one onto a non-pk `to_field` matches its rows instead of nothing. Single-valued
  relation leaves, marked non-pk `to_field` forward keys (still the target's primary key) and the published types are
  unchanged. The item named forward many-to-many only; every to-many kind behind a hop failed alike. Package rows over
  Decimal, DateTime and one-to-one-onto-`to_field` keyed targets, scoped and declared, with the unhopped leaf as
  control
- [x] 547. A `date`, or a naive `datetime`, held by a `DateTimeField` column escaped the temporal storability
  preflight: `utils/errors.py::unstorable_temporal` let every `date` through and read a naive datetime as already
  made aware, so a `SerializerMutation` whose serializer `validate_<field>` returns `value.date()` (or a naive wall
  clock), a `DateField` subclass under `serializer_field_mapping`, and an `ArrayField(DateTimeField)` date element
  reached `save()`, where Django makes the value aware in the default zone and the adapter's `OverflowError` (year 1
  under a zone such as `Asia/Tokyo`, year 9999 under a `DATABASES` `TIME_ZONE`) answered the masked error. The shared
  rule now checks such a value as the datetime Django binds for it (a date as its midnight, made aware in the default
  zone when the connection runs under `USE_TZ`), so it is the field's `invalid` `FieldError` with nothing written;
  a date in a `DateField` column and every aware datetime take the same path as before. The item overstated the
  reach: the `ModelForm` scalar path was already covered (`Model.clean_fields` writes the aware midnight back before
  the preflight reads the instance), a declared `serializers.DateField` over a `DateTimeField` is a build-time
  `ConfigurationError`, and the model flavor never carries a date. Package rows in `tests/utils/test_errors.py` and
  `tests/rest_framework/test_resolvers.py`; README, spec-038, spec-039 and the `fielderror-envelope` glossary term
- [x] 512. A declared `ListFilter` or `ArrayFilter` read raw form data (a `QueryDict`: DRF's `DjangoFilterBackend`,
  a django-filter view) through Django's default `TextInput`, so every `?name=` value, valid ones included, reached
  `ListFilter.filter` as a string and answered `GraphQLError("Invalid filter value: expected a list.")`, a 500,
  under a package or a plain django-filter `FilterSet` parent. Their form field (`filters/base.py::_ElementField`)
  now reads raw form data by the generated `in`'s rule (`_MembershipCSVWidget`): `?name=a,b` is the list
  `["a", "b"]`, `?name=` and an absent key apply no constraint, a list or tuple passes through unchanged (the
  GraphQL input, so an explicit `[]` keeps its meaning), each element is cleaned by the column's `gte` form field
  (a junk element is that form's error, a 400 under the backend), and a consumer `widget=` wins. The shared widget
  now passes a non-text value through and reads a lazy translation string as text. The item's mechanism was wrong:
  no schema build is involved (the build mutates no filter; the answers are identical before and after it). Its
  `RangeFilter` half is not a defect: only a `RangeFilter` whose `field_name` is the relation itself raises
  `FieldError` (with both bounds), a consumer declaration django-filter's own `RangeFilter` refuses the same way and
  the schema build refuses; a relation path to a column filters with no build. Package rows in
  `tests/filters/test_base.py` (both parents, through a real `DjangoFilterBackend` view and a `QueryDict`); spec-027.
- [x] 514. Not a defect (AGENTS defect rule: no contract row). A declared `RangeFilter` bound or `ListFilter` element
  on a `BooleanField` is cleaned by the column's `gte` form field, django-filter's `BooleanFilter` field, Django's
  `forms.NullBooleanField`, whose documented `to_python` reads any unrecognized string (`"yes"`, `"junk"`, `""`) as
  `None`. That is the raw-form rule of every Boolean filter under `DjangoFilterBackend`: the package's generated
  Boolean `exact` (`filters/sets.py` maps `models.BooleanField` to django-filter's `BooleanFilter`) and
  django-filter's own `BooleanFilter` read `?flag=yes` as no constraint the same way, and spec-027 promises the
  declared filters exactly that column cleaner. GraphQL types the value `Boolean` and cannot send the string. No code.
- [x] 556. On PostgreSQL through psycopg 3 an `ArrayField(TimeField)` write mixing naive and aware times escaped
  the temporal storability preflight: psycopg picks one array type for the whole list from its elements (in 3.3.4
  the last non-`None` one, `types/array.py::BaseListDumper._find_list_element`), so `[naive, aware]` went to the
  `timetz[]` dumper, whose `DataError` "cannot calculate the offset of tzinfo 'None' without a date" answered a
  masked top-level error on every write flavor (model, `ModelForm` `SimpleArrayField` / `SplitArrayField`, DRF
  `ListField`), nothing written, while `[aware, naive]` stores. `utils/errors.py::unstorable_temporal` now also asks
  the driver about an `ArrayField` list as a whole (`_psycopg_refuses_list`): the flattened list, each element as
  the column stores it (a `DateTimeField` element through `_stored_datetime`, a datetime in a `TimeField` list as
  its naive `.time()`), is dumped as text with the open connection's adapters or the driver's, and only when every
  element is `None` or the column's stored type; the driver's `DataError` is the field's `invalid` `FieldError`
  "Enter a value the database can represent.", any other exception propagates, psycopg 2 is not asked, and no
  connection is opened. Restating psycopg's ordering was rejected (it differs across psycopg 3 versions), and so was
  refusing every mixed list (it would refuse `[aware, naive]`, which stores). Whether PostgreSQL stores
  `[aware, naive]` into `time[]` is unchanged and unverified on a server. Package rows in
  `tests/utils/test_errors.py` (a stand-in driver and the real psycopg module); README, spec-036, spec-038,
  spec-039 and the `fielderror-envelope` glossary term
- [x] 545. `scripts/prove_failability.py::_pattern_matches` matched an `expect_failing` pattern by equality or plain
  `fnmatch`, which reads `[*]` as a character class, so a glob over a parametrized id (`test_x[*]`) never matched
  and the module docstring offered "node id or glob" without saying so. A pattern now also matches when `fnmatch`
  matches it with every `[` read literally: `test_x[*]` names every parametrized row of `test_x`, `test_x[a-*]` the
  rows whose id starts `a-`, and equality and plain `fnmatch` stay first, so every pattern that matched still
  matches (a character class such as `test_[ab]` included; an exhaustive parent-vs-change grid lost no pair).
  `isolates` stays equality only. Rows in `tests/test_prove_failability.py`; the module and function docstrings
- [x] 557. Not a defect (AGENTS defect rule; GOAL "Trust boundary": application Python is trusted). The package
  never iterates a queryset with a named cursor (`rg '\.iterator\(|aiterator\(' django_strawberry_framework` finds
  nothing), so every query it evaluates binds the way `utils/errors.py::unbindable_temporal` reads the connection
  (server-side under a consumer `OPTIONS["cursor_factory"]` that is not a `ClientCursor`), and a filter value at an
  offset of 16:00 or more filters there as the README says. Only consumer code that takes a package-filtered
  queryset and calls `QuerySet.iterator()` under such a cursor factory gets Django's client-bound named cursor and
  the server's refusal, which is that code's own choice of cursor. No code.
- [x] 543. `utils/errors.py` and `types/converters.py` each soft-imported `django.contrib.postgres`'s `ArrayField`
  and unwrapped `base_field` their own way, and tests patched each copy separately, so a test patching one left the
  other unpatched. One private owner, `utils/_array_field.py` (`ARRAY_FIELD_CLS`, `array_element_field`), now serves
  `types/converters.py`, `utils/errors.py` (`_array_leaf`), `forms/inputs.py`, `rest_framework/serializer_converter.py`
  and `filters/base.py`, and every test patches it through `tests/_postgres_fields.py::patch_array_field`. No
  behaviour changes: test verdicts, the schema SDL and a 131,904-cell `unstorable_temporal` grid over nested arrays
  are identical to the parent. A `tests/utils/test_errors.py` row pins that a non-list item inside an outer array
  list holds no element. spec-017, spec-019, docs/TREE.md, the kanban tracked-path constants and the type-suppression
  ledger follow the move
- [x] 591. Under Django 6.1 a `DecimalField` with no `max_digits` is an unconstrained `numeric` on PostgreSQL, and
  `utils/querysets.py::_stored_decimal_or_none` passed its value through, so an identity decode (a Relay `node` /
  `nodes` id, a raw pk, a raw-pk or GlobalID relation filter, a relation write id) carrying `"1e1000000"`,
  `"1e-1000000"` or `"1E+131072"` bound a value PostgreSQL's `numeric_in` refuses ("value overflows numeric
  format"), a masked `DataError` where `coerce_field_value_or_none` names no row. On PostgreSQL such a value now binds
  as written when its spelling fits numeric's format (up to 131072 digits before the point and 16383 after); a
  spelling past it loses its trailing fractional zeros exactly, without rounding, a zero becomes `0`, and what still
  does not fit names no row (`None`). Other backends bind the value as given, and bounded columns are unchanged. The
  generated `"1e1000000"` filter value never reached the bind (django-filter caps a positive value at `1e50`); the
  negative and tiny spellings that do reach it on any `DecimalField`, and the write flavors, are filed below. The
  limits are source-derived (`numeric.c`), not checked on a server. Package rows in `tests/utils/test_querysets.py`
  (a PostgreSQL stand-in alias and SQLite); spec-032 Decision 5 and the `coerce_field_value_or_none` docstring
- [x] 558. `OrderSet` accepted `Meta.exclude` and read it nowhere, so `fields = "__all__"` with `exclude` still
  published and ordered by the excluded column (a column the type never returns ranked rows over a real query) and an
  exclude-only set expanded to nothing and failed at `finalize_django_types()`. The order family now honours
  `Meta.exclude` as the filter family does (README: `exclude` means what a DRF user thinks; no upstream order surface
  defines it, `AdvancedOrderSet` ignores it): `orders/sets.py::OrderSet._expand_meta_fields` drops a listed name, the
  primary key included, from the `"__all__"` sweep or the declared names by exact name; `exclude` with no
  `Meta.fields` is the sweep minus those names, `RelatedOrder` branches or not, so it needs `Meta.model`; a
  `RelatedOrder` declared under an excluded name stays; a name matching no field drops nothing; a bare string, a
  one-shot iterator or a non-string entry raises `ConfigurationError` (`_read_meta_exclude`, the filter family's shape
  gate). Excluding a `ForeignObject` carrier column keeps the link, which still orders by it. Live rows in
  `test_library_api.py` over a new fakeshop `PublicPatronOrder` (mirrors `PublicPatronType.Meta.exclude`; the public
  patrons field takes `orderBy`), package rows in `tests/orders/test_sets.py`; spec-028, README, fakeshop README,
  GlossaryTerm 474 and 489
- [x] 517. The catch-all's `ConfigurationError` for a `method=` filter with no form field
  (`filters/inputs.py::convert_filter_to_input_annotation`) advised `Filter(method=..., field_class=...)`, a spelling
  whose `.field` raises `TypeError` at schema build (django-filter forwards `field_class` to the form field). It now
  names the declared filter's class and advises the spellings that work: a typed primitive (`CharFilter(method=...)`,
  `NumberFilter(method=...)`, `ListFilter(method=...)` for a list value) or a `Filter` subclass declaring
  `field_class` at class level. What reaches it is a filter whose form field cannot be built on the unbound
  declaration (`AllValuesMultipleFilter(method=...)`); a bare `Filter(method=...)` types as `String`. The message is
  pinned in `tests/filters/test_inputs.py`; live holder rows in `test_library_api.py` prove each advised spelling
  filters, column-backed and not
- [x] 518. The choice refusal (`filters/inputs.py::_choice_enum_from_filter`) named "ChoiceFilter" for every reacher
  and advised a `Choices` enum or a `SCALAR_MAP` scalar, neither of which the arm reads. It now names the declared
  filter's class (`AllValuesFilter`, `DateRangeFilter`, `TypedChoiceFilter`, a consumer subclass) and states the cause
  that holds for each: no model field declaring `choices` backs it. Its advice is to declare `choices` on the column,
  or to filter the column through a non-choice filter (`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its
  `Meta.fields` lookups, `CharFilter(method=...)`). No refused or typed shape moved. Pinned by equality in
  `tests/filters/test_inputs.py`; spec-027's ChoiceFilter row follows
- [x] 516. Not a defect under the AGENTS defect rule: no contract row breaks. spec-027 Decision 4's `BaseCSVFilter`
  row covers the `in` / `range` lookups django-filter generates from `Meta.fields`; a consumer-declared bare
  `class CharCSV(BaseCSVFilter, CharFilter)` keeping `exact` is a declaration django-filter itself never makes match.
  Plain django-filter 26.1 runs the same `title = '[''aa'']'` SQL for `?title=aa` and returns 0 rows, and raises the
  same `TypeError` for a `NumberFilter` element. The schema publishes the list the declared form field cleans, and a
  scalar would change nothing, because `BaseCSVWidget` still splits it into a list. The same declaration is
  meaningful with `in`, with `range`, and with `method=` (the method receives the list), so a class-keyed refusal
  would break working shapes. Build-time refusal of a list-shaped filter over a lookup that cannot consume a list is
  folded into robustness row 625, which now covers the bare CSV family beside `ListFilter`
- [x] 519. A declared filter a deep copy refuses (a bound `method=` over an object holding a lock or a Django cache
  handler, a `functools.partial` over one, a lock in `extra` or in a `Meta.filter_overrides` `extra`) is refused at
  schema build by a `ConfigurationError` naming the set, the attribute and the filter's class, with the copy's error
  as `__cause__`. A new finalizer subpass 1.5 (`types/finalizer.py::_audit_filter_copies`) copies every served set's
  `base_filters` through `filters/base.py::copied_declared_filter` before expansion, and `_expand_related_filter`
  copies a `RelatedFilter` child through the same helper, naming the `RelatedFilter` it was reached through. A
  `ListFilter(method=...)` of that kind, which built and failed every filtered request on its set with a raw
  `TypeError`, is now refused at build too. The advice names the `method=` spellings only when the method itself
  refuses the copy. Class-level service objects, string method names, plain functions and shallow-copy widgets
  build and filter as before. spec-027's Decision 6, Error shapes and Layer 4 text follow; package rows in
  `tests/filters/test_finalizer.py`
- [x] 520. A filter a `RelatedFilter` expansion copies from a child set, rebound or projected as a
  `ProjectedChildFilter`, is named as the child set declares it in every input-conversion refusal: the declared class
  (never `Projected<Class>`), its attribute on the child set, and each `RelatedFilter` it was reached through,
  outermost first (`ShelfFilter.code_l: LookupChoiceFilter on 'code' (reached through BookFilter.shelf)`). One
  helper owns the answer (`filters/sets.py::_leaf_declaration`); `_expand_related_filter` records each rebound
  copy's origin in a weakly held side map, so nothing rides the copy's state, deepcopy or pickle. The LookupChoice,
  raw-pk, model-choice, choice-enum, `method=` and range-widget refusals use it, and the hand-built-value errors
  (`apply_sync` list / range / dict values) name the declared class. A filter declared on the set that holds it
  keeps byte-identical messages; filtering results and the fakeshop SDL are unchanged. spec-027's LookupChoiceFilter
  row states the rule; package rows in `tests/filters/test_inputs.py` and `tests/filters/test_sets.py`
- [x] 560. Not a defect: the repeated predicate is what keeps an arm's meaning. `FilterSet.filter_queryset` builds
  each `and` / `or` / `not` arm's sibling over the flat-narrowed queryset (`_q_for_branch`, `cls(data=...,
  queryset=queryset)`), so an arm selects among the rows the flat leaves kept, and composes it onto that same
  queryset, keeping the annotations, ordering and `distinct()` the flat leaves and consumer methods put on it.
  Building the arms over the unnarrowed queryset would drop the inner copy only for row-local predicates: a
  consumer `method=` or `qs` override that is not row-local (a top-N slice, an aggregate over the rows it is given)
  answers differently, and a `not` arm over a wider base removes rows by what they match outside the flat set.
  Dropping the outer copy instead would lose the flat queryset's shape and is wrong for `not`, whose complement
  is not a subset of the flat rows. Same rows, no contract row; the planner sees a redundant conjunct inside a
  semi-join
- [x] 515. A declared `MultipleChoiceFilter` / `TypedMultipleChoiceFilter` / `AllValuesMultipleFilter` (or one
  `Meta.filter_overrides` names) publishes a list typed from its column: `filters/inputs.py` gains a
  `MultipleChoiceFilter` kind-table row, last before the catch-all so every class another row dispatched (the
  GlobalID / model / relation-pk multiple filters, the generated `in` / `range` wrappers, a consumer class pairing
  it with a range, list, array, choice or `TypedFilter` kind) keeps that row. Convert gives
  `list[<column enum on a choices column, the column scalar otherwise, str with no column>]`, never typed from
  `coerce`; normalize hands the form a list, each enum member unwrapped, a non-list refused. The catch-all still
  builds every leaf's form field at schema build, and `AllValuesMultipleFilter(method=)` keeps its refusal. A bare
  `TypedFilter` normalizes as the scalar it converts to. spec-027 Decision 4 and GLOSSARY "Choice leaves" state the
  family and that `AllValues*` choices come from the default manager; live rows over a holder schema in
  `examples/fakeshop/test_query/test_library_api.py`, package rows in `tests/filters/test_inputs.py` and
  `tests/filters/test_sets.py`
- [x] 640. A flat field copied from a child set's declared filter fires its nested spelling's gates whatever
  the `RelatedFilter` attribute is called: `PrintingFilter.in_series = RelatedFilter("SeriesFilter",
  field_name="series")` let `inSeriesHandle` past `SeriesFilter.check_handle_permission` and
  `PrintingFilter.check_in_series_permission`, which `inSeries { handle }` fires (the gate path walked the key
  by declaration `field_name`, so a renamed hop walked nothing). Every expanded copy, rebound or projected,
  now carries one `filters/sets.py::ChildProjection` (child set, child name, branch) that rides deepcopy and
  pickle; gates (`FilterSet._leaf_gates`, `_supplied_leaf_gates`), the declared-head test
  (`filters/inputs.py::_is_declared_head`) and refusal naming (`_leaf_declaration`) all read it, so a
  `get_filters()` override that deep-copies or re-keys the copies keeps both.
  `FilterGenerationProvenance.expanded_from`, the weak `_REBOUND_ORIGINS` map and
  `FilterSet._expansion_origin` are gone. A copy borrowed onto a set that does not expand that branch into
  that child set is that set's own filter (`ChildProjection.holds_in`). spec-027 states it; live rows in
  `examples/fakeshop/test_query/test_library_api.py`, package rows in `tests/filters/test_sets.py` and
  `tests/filters/test_inputs.py`
- [x] 346. Every git call in `scripts/` (and `tests/test_ci_governance.py`'s committable listings) runs through one
  runner, `scripts/_git.py::run_git`, under `scripts/_git.py::repository_env`: only the repository's own config and
  ignore/attribute files count (`REPOSITORY_CONFIG_ONLY` drops global, system and XDG config and the system
  attributes file), every `GIT_*` variable except the repository-locating ones is dropped (a hook's or the private-index
  procedure's `GIT_INDEX_FILE` still reaches the generators), and `GIT_OPTIONAL_LOCKS=0` keeps every `status` from
  rewriting the shared index. `bug_hunt.py` reuses `_plan_common.git_status_short`, `check_type_suppressions` lists
  with `-z`, `workspace.py` takes its mapping from the same module, and `.gitignore` gains
  `**/.claude/settings.local.json` (a file only a caller-global rule hid). Tests: `tests/test_git.py` (hostile caller
  setups per site, index untouched, private index, trust)
- [x] 348. The caller's ownership trust is kept under the isolation: `scripts/_git.py::caller_safe_directories` reads
  `safe.directory` from the caller's protected sources only (system, global, command scope; never `GIT_CONFIG` or
  repository config) and passes it as command scope, so `workspace.py` and every other script read a checkout the
  caller marked safe and refuse one the caller did not, exactly as the caller's git does. Fixed with 346
- [x] 347. `scripts/workspace.py::item_diff` keeps the baseline's blob for every name `is_excluded` reports (cycle
  scratch, a parked `*-ws` copy, `output/`, `docs/shadow/`), the rule `snapshot_commit` already applies, so a
  pre-existing untracked file there is never the item's addition and a tracked one's edit or deletion is never the
  item's; the filter is `content_index`'s keyword-only `excluded`, applied to the default listing only (explicit
  `names` are never filtered). The `diff` manual, START.md's scripts row and the item-diff sentences in HUNT.md,
  DRY.md and REVIEW.md say so. Tests: `tests/test_workspace.py` (untracked and tracked edit/delete rows per excluded
  shape at scope `.` and narrower, snapshot agreement, explicit names refreshed)
- [x] 349. `scripts/workspace.py::audit_record` turns an unreadable record (missing, a directory, no permission, not
  UTF-8) into a refusal: `workspace: audit <path>: <reason>` on stderr, exit 1, no traceback; records audited before
  it keep their report lines. The `audit` manual says so. Tests: `tests/test_workspace.py` (each unreadable shape,
  the CLI refusal, a readable record before a missing one)
- [x] 374. A one-value filter whose form field's widget reads other form-data keys (`django_filters.NumericRangeFilter`,
  any lookup or `method=`; a consumer `Filter` over a `MultiValueField`; a `CharFilter`, `ModelChoiceFilter` or
  `DateTimeFilter` given a `MultiWidget`) is refused when the schema is built, naming the declaration, the keys its
  widget reads and the `RangeFilter` remedy (`filters/inputs.py::_refuse_widget_reading_other_keys`, every arm but the
  range arm); it used to publish one scalar under `<name>`, which the widget never read, so every send answered every
  row. Routing it as a range was not taken: upstream rewrites a lone bound to a text `startswith` / `endswith`, and
  PostgreSQL range columns stay unsupported. spec-027 row. Tests: `tests/filters/test_inputs.py`
- [x] 566. The four test trees state behaviour where they narrated history: about 300 comment, docstring and name
  sites ("now X instead of Y", "the old / previous implementation", "the fix", "(hardened)", "hoisted", "relocated",
  "this slice", "Pins finding-2", review-doc and severity attributions, "(#N)" review tags, version banners) restate
  what the enclosing test asserts, counterfactuals the test does not assert becoming positive statements; 16 test and
  helper names renamed with their spec, DONE-plan and suppression-ledger citers. The provenance gate
  `tests/test_ci_governance.py::test_no_comment_docstring_or_name_carries_a_provenance_phrase` also refuses `the
  hardening pass`, `(hardened)`, `(hardening)`, `pre-0.0.`, `the old implementation`, `the previous implementation`,
  `task report` and `finding-` (17 phrases; `historically`, `this slice`, `the original implementation`, `hoisted`,
  `relocated`, `this card` and `the old <noun>` have behaviour uses and stay ungated), with the package and example
  sites they caught restated and START.md's bullet listing the set. Executable code unchanged (code digest per file).
  Out of scope, filed: 629, 630
- [x] 570. Fixed by the shard split (`d0073edf`): every `django.yml` test cell runs as two jobs on separate runners
  (`library-keyset`: `test_library_api.py` + `test_keyset_api.py`, `--dist load`; `remainder`: the rest, `--dist
  loadscope`) and a `coverage` job combines the latest cell's two traces and owns the gate; the 45-minute
  `timeout-minutes` is unchanged. Measured on the three push runs since (`40301105850`, `40339630011`,
  `40405314085`): the slowest shard job took 17 minutes (floor `remainder`), the rest 8 to 14; none was cancelled.
  Trimming the suite itself stays the maintainer's call
- [x] 573. not a defect: no contract row covers it. README, the GLOSSARY `DjangoModelFormMutation` and `FieldError`
  terms and spec-038 Decision 8 scope the save-time `null` answer to a `blank=True, null=False` column, and nothing
  pins a `null=True` one. The shape needs a consumer-declared form field cleaning `""` (`ChoiceField`,
  `TypedChoiceField(empty_value="")`, `CharField`) over a nullable non-text column, since Django's own form field
  cleans `""` to `None` there (`empty_value=None`), and plain Django's `save()` raises on it (graphene-django
  likewise). Measured on SQLite and PostgreSQL, sync and async: those 30 cells plus 3 PostgreSQL `ArrayField` cells
  answer the field-keyed "This field cannot be null." (code `null`), nothing written. A client reaches it only by an
  omitted create value or an explicit `null` (plus `""` on an `ArrayField`), since every other input is typed by the
  column. Which answer a nullable column should give is row 631
- [x] 420. `scripts/_markdown_lex.py::block_regions` reads each line's containers as CommonMark appendix A does: one
  stack of block quotes and list items opened in any order (a quote inside a list item, a list inside a quote inside
  a list), matched outermost first, with lazy continuation and a fence or HTML block ending when its container closes;
  a link reference definition is read when its paragraph closes (4.7: label, destination and title each on its own
  line, a title spanning lines), so neither shape can take a term link. A CRLF line's `\r` ends a list or heading
  marker. All 652 CommonMark 0.31.2 examples mask as the spec renders them (HEAD: 270 of 286 in 4.1-5.3); over the
  repo's `.md` files only the `.claude/agents` front matter's opening `---` moves (now a thematic break). Tests:
  `tests/test_check_spec_glossary.py`
- [x] 599. A FilterSet's `get_filters()` override is the set's filter table everywhere: its own input and
  form, a direct `Set(data, queryset)`, the nested branch, the parent's flat copies (rebound or projected) and
  a cycle member's contribution. `FilterSet.get_filters` published `base_filters` and the expansion snapshot
  from inside the override's `super()` call, so an added filter was published on the input and filtered
  nothing (all rows, no error), a child with an `__init__` override raised `KeyError` at schema build, a cycle
  member's rename or removal raised `KeyError`, and an in-place `del` override raised on its second call. Now
  `filters/sets.py::FilterSet._publish_filters` runs the override once and publishes its result,
  `FilterSet._filter_table` is the one read (input lookup table, projections, finalizer audits, `__init__`),
  cycle contributions pass through the override (`FilterSet._reshape`), `get_filters()` returns a fresh map
  per call, and the override runs twice at schema build and never per request. A flat copy is deferred by its
  `ChildProjection` record, not by its name, so a copy under a key the set's own `Meta.fields` also generates
  is deferred and a filter the override adds is the set's own. spec-027 and docs/README state it; live rows in
  `examples/fakeshop/test_query/test_library_api.py` (`PatronFilter` and `IssueFilter` overrides), package
  rows in `tests/filters/test_sets.py`
- [x] 598. `HIDE_FLAT_FILTERS` hides each flat copy of a `RelatedFilter` expansion, under whatever key a
  `get_filters()` override holds it, and never a filter the set holds itself.
  `filters/inputs.py::_build_input_fields` decided by the key's first segment, so a re-keyed copy stayed
  published and a set's own filter spelled under a relation's name was hidden: fakeshop `PrintingFilter`
  `edition__printings__co_publishers` had no nested twin and was unreachable, against spec-027's "Nothing
  becomes unreachable". The skip now asks `filters/sets.py::_is_flat_copy` per lookup, so a head mixing an own
  lookup with copies keeps only its own; the lookup table and gates do not depend on the setting. spec-027,
  docs/README and GLOSSARY (`RelatedFilter`) state it; the library example adds a re-keyed alias
  (`PatronFilter.borrowed_title`) and a mixed head (`PrintingFilter` `edition__imprint` istartswith); live
  rows in `examples/fakeshop/test_query/test_library_api.py` replace the pin that hid `bookLoansPatronEmail`;
  a package row in `tests/filters/test_inputs.py` pins a borrowed copy
- [x] 646. Not a defect under the AGENTS defect rule: `scripts/_markdown_lex.py` states its contract as
  CommonMark (its module docstring cites CommonMark 4.1-4.7 for `block_regions`), and on a type-7 HTML tag
  line in a lazy continuation position it does what the CommonMark spec, commonmark.js and markdown-it do
  (lazy paragraph text); only cmark-gfm opens an HTML block there. No repo markdown file has the shape
  (measured verifying 420), so no feasible project input reaches the difference. Lexing to cmark-gfm's reading
  instead would be a new card
- [x] 630. `examples/fakeshop/test_query/README.md` states its teaching as present practice: each worked
  example keeps its lesson in present tense and cites the live row it describes by `path::Symbol` (no copied
  test bodies, which had drifted from the rows); the Before / What moved narration, the deleted-test list and
  the eleven citations of package rows that no longer exist are gone; "Gotchas the sweep surfaced" is
  "Gotchas" without the bullets stated elsewhere in the file; the "Second sweep" section is deleted, its queue
  empty with every row moved or kept by design, so no row needed a card. The one leftover package row it named
  is filed as 603
- [x] 603. The package stand-in `tests/optimizer/test_relay_id_projection.py` is deleted: a mutation table
  over the walker's Relay-id projection, `_resolve_id_default`, the id-attr stamp and `encode_typename` found
  no mutant only it killed (one statement, no lazy load and the node id are pinned by the live
  `test_library_shapes_api.py` twin, the GlobalID type name by four live rows, the `only()` projection by the
  two `tests/optimizer/test_walker.py` relay-id rows), and every line it ran is reached by other rows.
  spec-015 and spec-031 cite those rows; docs/TREE.md and the kanban tracked-path constants are regenerated.
  Writing a live pin for a non-pk `NodeID` found 604
- [x] 604. A Relay `id` selection projects the column the type's id reads, at every page, join and prefetch
  position: `optimizer/walker.py::_walk_selections` routes `id` on a `relay.Node` type first to
  `_relay_id_column`, which reads `types/relay.py::_node_id_slot` (a concrete field's attname; an id read by a
  consumer `resolve_id` or from no concrete column resolves through the field map). It matched the model field
  literally named `id` first and looked the id column up only among `Meta.fields`, so fakeshop `PublisherType`
  (`house_code: relay.NodeID[str]`) loaded `id` and refetched `house_code` once per row, and on the async
  executor that refetch raised `SynchronousOnlyOperation` (field error, data null). spec-015 Decision 7 states
  the id-column projection; live rows in `examples/fakeshop/test_query/test_library_shapes_api.py` (six
  positions, the Series annotation control) and `test_library_api.py` (async), package rows in
  `tests/optimizer/test_walker.py` for a NodeID column outside `Meta.fields`, a reverse-key child, a consumer
  `resolve_id` and a property NodeID
- [x] 421. The board and the spec auto-linker share one `scripts/_markdown_lex.py` after-boundary,
  `TERM_BOUNDARY_AFTER`: a `.`, `:`, `/` or `-` run after a term bars the link only when an identifier character
  follows the run, so a term ending a sentence or clause is linked (`... a DjangoType.`) and one opening a path or
  compound is not (`Meta.fields.get`, `DjangoType-style`, `Term.5`). The strict variant and the `PROSE_` name are gone.
  `KANBAN.md` re-rendered: 182 glossary links against 175 (7 first mentions newly linked, 10 links moved to the true
  first mention, 0 links on a non-mention); `KANBAN.html` is unchanged (it embeds stored glossary rows). Tests:
  `tests/test_build_kanban_md.py`
- [x] 422. (robustness) `scripts/check_spec_glossary.py::_insert_glossary_ref_def` slots the new
  `[glossary-<anchor>]: ...` def before the group's first def whose label sorts after it (codepoint), else at the
  group's end, and never re-sorts the rest: every existing line keeps its order and bytes. The whole-line `sorted()`
  rebuild reordered hand-written lines in 44 of the 188 tracked `.md` files with a `<!-- docs/ -->` group (whole-line
  order puts `[foo-bar]` before `[foo]`); a census of 2186 inserts across those files adds one line each and moves
  none. Tests: `tests/test_check_spec_glossary.py`
- [x] 568. The provenance gate reads every string statement: a docstring, an attribute docstring after an assignment,
  a later or nested string statement and an f-string's literal parts (a replacement field splits a phrase); a `+` or
  bytes statement (refused by ruff B018 and basedpyright `reportUnusedExpression`) and a t-string stay unread, and a
  trailing comment never joins the full-line comment below it (0 of 66 such pairs is one sentence), all stated in the
  gate's limits. Five planted rows and the permitted-form row pin it; 20 more segments are read, 0 hits.
  `scripts/review_inspect.py::PROVENANCE_PATTERNS` stays a separate report-only list (one shared word), each list's
  comment naming the other; START's provenance bullet names string statements
- [x] 564. The four error strings state the invariant without a release: the `RelatedFilter` `lookups=` TypeError
  names the remedy (the target FilterSet's `Meta.fields`), `Meta.connection`'s unknown-sub-key error reads "Only
  'total_count' is recognized.", `decode_global_id` gives the rejecting strategy's own reason (it decodes only a
  model-label or only a type-name payload, or is encode-only) where it appended the callable / custom note to every
  rejection, and the router hint keeps its migration prose without the number. The first three are pinned exactly;
  the docstrings, spec-046 "Error shapes" and the GLOSSARY `Meta.connection` body are restated; dry-0_0_15_3 item 28
  is ticked
- [x] 575. A create's build advises like an update's: `forms/inputs.py::build_form_input_class` runs
  `_advise_shape_disagreement` for every input it builds, over the fields that input binds, with the first clause
  (the form must turn the input into the column's value) for both and the omitted-field initial advice for the
  update only; one warning per input build, so a form serving a create and an update logs one of each. Package rows
  in `tests/forms/test_inputs.py` pin the texts and counts; the docstrings, spec-038 and the GLOSSARY
  `DjangoModelFormMutation` body are restated
- [x] 634. No release number of this package is left in .py source: the seven `Target release:` module lines, the
  "shipped / since 0.0.N" banners, the release-history narration in `mutations/sets.py`, the "0.0.9 model-label
  default", "(hunt 0.0.15)" and the format examples in scripts are restated as behaviour, and release-carrying card ids
  in prose (the `needs TODO-BETA-...` labels included) name their spec or the card's topic. A new gate,
  `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_carries_a_release_of_this_package`,
  refuses a release of the current series (pattern built from `__version__`) or a release-carrying card id in every
  comment, string statement and name of the sweep corpus and in every package string but `__version__`; upstream
  ranges, IPs and test data pass. 90 sites to 0; the `types/finalizer.py` strictness paragraph, false at HEAD, now
  states the rule (spec-033 Decision 8). Maintainer request. The road-to-1.0.0 vocabulary of `scripts/_kanban_lib.py`
  is refused once `__version__` reaches 1.0
- [x] 460. A hinted `OptimizerHint.prefetch(Prefetch(lookup, queryset=...))` without `to_attr` whose queryset is not
  over the lookup's leaf target (or a proxy of it sharing its table) is refused when the type is built, naming
  `Type.field`, the row model and the target (`types/base.py::_hinted_prefetch_seed_defect`, read by
  `_validate_optimizer_hints`): both the `Query.model` Django builds rows from and `QuerySet.model` must pass, a
  `TextChoices` lookup is read as its text, and a non-QuerySet seed fails closed. It filled the relation with rows the
  target type's `is_type_of` refuses (a `Branch` seed on a `ProxyBranch` target, a sibling proxy, an MTI child or
  parent, an unrelated table), hooked or not, FK or M2M. A `to_attr` Prefetch stays the consumer resolver's own; an
  unresolvable leaf (generic FK) is left to Django. The consumer `prefetch_related(Prefetch(...))` path keeps its
  per-parent re-read. spec-045 row. Tests: `tests/types/test_base.py`, `test_library_api.py`
- [x] 462. A reverse relation whose `related_query_name` differs from its accessor is planned in both of Django's
  spellings: the walker carries a query-name prefix for `select_related`, `only()` and select keys and an accessor
  prefix for every prefetch lookup, prefetch key, seal, hint rebase and nested-connection window
  (`optimizer/walker.py::_walk_selections` `lookup_prefix`, `optimizer/plans.py::JoinPrefix`), and the diff readers
  (`_consumer_owned_paths`, `_withdraw_owned_select_paths`, `_release_select_related_to_prefetches`) compare consumer
  paths respelled through Django's relation metadata (`utils/relations.py::respell_relation_path`). It served a row a
  consumer `Prefetch` hid (the planned JOIN kept the reverse one-to-one), joined past a target type's `get_queryset`
  hook (a consumer `select_related` never released), raised `AttributeError` for a prefetch planned beneath the JOIN,
  and refused an accessor-spelled hinted `Prefetch` beneath a JOIN. Tests:
  `tests/optimizer/test_relation_spelling_execution.py`, `test_walker.py`, `test_plans.py`, `tests/utils/test_relations.py`
- [x] 384. A filter value the database cannot bind is refused by asking Django, not a model of it: each temporal leaf's
  predicate is built by its own shipped `filter()` over the filterset's queryset with its WHERE and limits cleared, and
  only that clause is compiled on `queryset.db` (`filters/sets.py::_unbindable_predicate`); a build `OverflowError` /
  `ValueError` / `TypeError` / `ValidationError` or a compile `OverflowError` / `ValueError` is the coded
  `FILTER_INVALID`, and the compiled params meet the PostgreSQL server-offset rule
  (`utils/errors.py::refuses_utc_offset`, the one rule no Django call answers). A declared filter whose value kind
  differs from its column (a `date` on a `DateTimeField` east of UTC, a `datetime` on a `DateField` or through
  `__date`) overflowed as the masked uncoded error. The value-kind walk, lookup and year tables in
  `unbindable_temporal` are gone (-80 lines). spec-027 row. Tests: `tests/filters/test_sets.py`,
  `tests/utils/test_errors.py`, `test_scalars_filter_api.py`
- [x] 388. A class-level `Filter.filter()` override owns its value like `method=`: the unbindable-value ask runs only a
  `filter` defined by django-filter or this package (`filters/sets.py::_runs_shipped_filter`, the MRO owner's module),
  so consumer code never runs to validate; documented in `_unbindable_temporal_errors`. Tests: `tests/filters/test_sets.py`
- [x] 398. A class-level `GlobalIDFilter.filter` override is read by `filters/sets.py::_decodes_before_binding` through
  `utils/truth.py::overrides`, so its lone-surrogate value is the coded `FILTER_INVALID` instead of a masked
  `UnicodeEncodeError`. Tests: `tests/filters/test_sets.py`
- [x] 385. A filter value that compiles but carries an integer the connection's driver cannot bind is the coded
  `FILTER_INVALID`: after 384's build and compile, every integer each bound lookup's own `process_rhs` yields (found
  through expressions and into subquery WHEREs, `filters/sets.py::_bound_value_lookups`) is held to the connection's
  `integer_field_range` for the type its lookup binds (`utils/querysets.py::binds_integer`, shared with
  `coerce_field_value_or_none`). A declared `ListFilter` `in` / `RangeFilter` over `__year` / `__iso_year` with a member
  past the range (2**63 on SQLite) raised the masked `OverflowError` at bind. Non-numeric / inf / nan members were
  already refused by 384's build; `Decimal("1E+300000")` reaches no shipped filter (django-filter's 1e50 cap). Tests:
  `tests/filters/test_sets.py`, `test_scalars_filter_api.py` (new `occurredYearAmong` / `occurredYearSpan` filters)
- [x] 386. A `DurationField` filter leaf is asked like a temporal one: on a backend that binds durations as integer
  microseconds (SQLite, MySQL) a value past 64 bits of microseconds is the coded `FILTER_INVALID` instead of the masked
  bind `OverflowError` (`filters/sets.py::_unbindable_temporal_errors` gate, `binds_integer` with the
  `BigIntegerField` range). Tests: `tests/filters/test_sets.py`
- [x] 389. A PostgreSQL `ArrayField` of datetimes, times or durations (nested too) is asked like a temporal column:
  the gate reads its innermost element (`utils/_array_field.py::array_leaf_field`, shared with the write side), and
  `utils/errors.py::refuses_utc_offset` holds a list param's elements to the text rule (psycopg dumps a list as text
  even under server-side binding) while an `ARRAY[...]`-wrapped element or an index value keeps the binding-mode rule;
  a list param psycopg cannot dump (a naive and an aware time) is refused through `_psycopg_refuses_list`. An element
  whose UTC offset PostgreSQL refuses raised the masked `DataError` at evaluation. By source and the recorded real-server
  facts; the pg-marked rows run on the PostgreSQL tier. Tests: `tests/filters/test_sets.py`, `tests/utils/test_errors.py`
- [x] 427. (robustness) The django.yml floor-cell check (`tests/test_ci_governance.py::_floor_cell_problems`) holds
  step order (the Django install, the strawberry floor step and the soft-floor step each after `uv sync`, the floor
  steps after the Django install), refuses a later `uv sync` or `uv run` without `--no-sync` that would put the lock
  back over the pins, and finds floor nodes by their `(python, django)` content so every one must carry
  `compatibility_only` and every marked node must be at the floor; mutation rows pin each. `scripts/workspace.py::
  _lower_bounds` refuses a dependency stated by two or more rows (a marker-split floor) instead of the last winning, and
  the `[dependency-groups]`-not-a-table / `dev`-not-an-array refusals have rows. Tests: `tests/test_ci_governance.py`,
  `tests/test_workspace.py`
- [x] 428. (robustness) `tests/test_workspace.py`'s stop-relay rows drive the repeat-stop grace with a held clock
  instead of wall-clock sleeps: `scripts/workspace.py::_StopRelay` takes a `clock` (default `time.monotonic`), the
  child harness swaps in a relay whose clock reads a file the test writes and which records each stop it handles, and
  the test waits until the relay has handled a stop before moving the clock past `STOP_REPEAT_GRACE` (which pins the
  `<` boundary). Waits on real child events are bounded by `_LOADED_WAIT` (60 s), and every stand-in command outlives
  it so a stop that never lands still fails. Green 15/15 at load ~100 where the parent failed 2-3. Tests:
  `tests/test_workspace.py`
- [x] 392. `utils/querysets.py::_where_tree_defect` holds a where-node connector to the text-term rule
  (`_is_text_term`, the rule `CombinedExpression.connector` takes): a `TextChoices` / `StrEnum` member seals and is
  rebound as exact `str`, its SQL equal to Django's; a hostile object stays refused. Tests: `tests/utils/test_querysets.py`
- [x] 393. A `QuerySet` as a pending deferred-filter value seals on every Django version: reconstruction retains
  Django's own fetch-mode singleton in a `QuerySet`'s `_fetch_mode` slot only (exact class, `is_django_fetch_mode`), so
  a fetch mode bound anywhere else (a `Value` payload) or a project subclass stays refused. The pre-bake proof
  (`_deferred_value_defect`) carries `_DEFERRED_VALUE_FRAME_BUDGET` and a pending value whose expression graph
  exhausts the recursion limit is caught, so a deferred filter nested too deeply is the typed `untrusted` defect, never
  `RecursionError`. Floor rows on Django 5.2. Tests: `tests/utils/test_querysets.py`
- [x] 394. `utils/querysets.py::_base_table_defect` reads the model's `db_table` once and returns the typed `table`
  defect (its kind) for a non-text value, as the alias side does, instead of raising `TypeError`. Tests:
  `tests/utils/test_querysets.py`
- [x] 397. Every `scripts/workspace.py` command keeps its own exit code when its reader is gone: `_cli` installs a
  stdout / stderr whose raw writer (`_ReaderGoneTolerant`) drops a write that meets EPIPE / EIO and points the fd at
  `/dev/null` through `_quiet_dead_sink` (the rule `_pump` uses), keeping encoding, line buffering and an unbuffered
  stream unbuffered. `status`, `audit`, a large `diff`, and `run` with stderr gone before or after its header exited
  120 or 1 with a traceback, and `run` with stderr gone before the header never started its command. Tests:
  `tests/test_workspace.py`
- [x] 501. (robustness) The workspace pool's default root is claimed as this user's own: `scripts/workspace.py::
  default_root` resolves the temp dir first and keeps `dsf-ws` when that dir is a real directory this user owns (so
  macOS keys do not move) and names it `dsf-ws-<uid>` on a shared one; `workspace_base` refuses a symlinked or foreign
  root as a typed `WorkspaceError` and creates nothing, and `_make_flow_dir` claims it (mode 0700, owner, lstat)
  through `prove_failability.py::claim_private_directory`, shared with the prover's scratch parent and state home and
  `forget_proof_state`'s check. A foreign root raised an uncaught `PermissionError`; a planted symlink was followed.
  `DSF_WS_ROOT` stays the caller's. Tests: `tests/test_workspace.py`, `tests/test_prove_failability.py`
- [x] 502. (robustness) `scripts/prove_failability.py::_new_capture` and `_read_probe` read their temp-resident file
  once (`_read_text_if_present`), a missing one counting as absent, so the purge removing it between a check and the
  read no longer raises `FileNotFoundError`. Tests: `tests/test_prove_failability.py`
- [x] 505. (robustness) A ready copy whose manifest is gone while its folder still holds a regular file (an edit, or
  any file written in the last three days, outlives the purge) is refused with a typed `WorkspaceError` naming
  `--fresh` / `gc` instead of being resynced over its edits (`scripts/workspace.py::_admit`, `_holds_a_file` walks
  without following symlinks); a copy gone with its manifest (a reboot, or a purge that left only folders and links)
  resyncs into its slot. The manifest is not renewed on reuse, so it stays the copy's age canary. Module docstring and
  START.md "Machine budget" say so. Tests: `tests/test_workspace.py`
- [x] 587. A lazy translation string (any `Promise`) in a set's field declaration is read as text, never iterated:
  `utils/_narrowing.py::is_text_atom` (char-wise, or a real `Promise` class, read without evaluating it; the rule
  `utils/errors.py::_str_list` already used) backs `sets_mixins.py::is_re_readable_field_declaration`, so FilterSet
  `Meta.exclude`, OrderSet `Meta.exclude` and OrderSet `Meta.fields` refuse a lazy string as the bare-string
  `ConfigurationError` (it excluded by substring, excluded nothing, or expanded per character), and a lazy `"__all__"`
  is the shorthand in both families' `Meta.fields`. spec-027 and spec-028 say so. Tests: `tests/filters/test_sets.py`,
  `tests/orders/test_sets.py`, `tests/test_sets_mixins.py`, `tests/utils/test_narrowing.py`
- [x] 900. The lookup iterator's return annotation uses a private runtime-safe alias, preserving
  `Lookup[object]` for static checking without subscripting Django's runtime class. The unpatched annotation gate
  passes; no filtering behavior or supported introspection contract changes. Tests: `tests/base/test_init.py`.
- [x] 659. Not a package defect under GOAL's trust boundary: the two repeat-stop tests in
  `tests/test_prove_failability.py` use wall-clock sleeps, but name no broken supported configuration or wire
  contract. Deterministic test timing is a tooling robustness task; the signal relay's behavior is unchanged.
- [x] 607. Not a defect against the shipped contract: spec-015 explicitly leaves optimizer cooperation
  out of both node defaults, and the glossary states that node refetch receives no optimizer plan. The capability
  decision and its query-count evidence remain under Waiting item 327; this row adds no separate defect.
- [x] 540. (robustness) The serializer flavor answers DRF's own field-keyed `overflow` ("Datetime value out of range.")
  for a datetime DRF's `DateTimeField.enforce_timezone` cannot place (a naive one near year 1 or 9999 under a non-UTC
  `TIME_ZONE`, an aware out-of-range one under `USE_TZ=False`), at every depth (`ListField` child, nested, `many=True`):
  `rest_framework/resolvers.py::_translate_datetime_overflow` wraps each request's own `DateTimeField` instances'
  `to_internal_value` and turns a raw `OverflowError` into `fail("overflow")`, the answer DRF gives the sibling cell;
  a consumer override that answers it itself is left to it. These answered the masked top-level error. One walk
  (`_validation_tree`) shared with `_pin_validator_querysets`. Live grid cells, README, spec-039 and the
  `fielderror-envelope` glossary term say so. Tests: `examples/fakeshop/test_query/test_scalars_mutation_api.py`,
  `tests/rest_framework/test_resolvers.py`
- [x] 569. (robustness) `scripts/check_annotation_subscripts.py` (pre-commit hook, `django.yml` lint step,
  `workspace.py` `LINT_COMMANDS`) sweeps every annotation by AST, strings inside annotations, runtime `TypeAlias`
  values and unquoted `cast` arguments, resolves each subscripted name through its imports, and fails closed on a
  class absent from its audited `SUBSCRIPTABLE` table (version-gated: `classmethod` / `staticmethod` take a hook only
  from Python 3.14), on a hookless class at an evaluated site, and on an unaudited or stale never-evaluated site
  (`AUDITED_SITES`, the item's seven). `tests/base/test_init.py` re-checks both tables at runtime without the
  `django_stubs_ext` patch on every cell. The sweep found `utils/truth.py`'s overloads subscripting `classmethod` /
  `staticmethod` (evaluable on 3.11-3.13), now `TYPE_CHECKING` aliases. Tests:
  `tests/test_check_annotation_subscripts.py`, `tests/base/test_init.py`
- [x] 562. (robustness) The async pre-pass derives a hop only for a flat leaf the form data names: a range naming no
  bound (`{start: null, end: null}`, `{}`, inside `or_` / `not_` arms, package or django-filter `RangeFilter`,
  `DateFromToRangeFilter`) writes no form key, so `apply_async` runs the hop target's `get_queryset` no more than
  `apply_sync` does. `filters/sets.py::FilterSet._leaf_form_data` (the keys one lookup writes, shared with
  `_normalize_input`) backs `_named_leaf_filters`, which `_derive_flat_hop_visibility_async` reads; a malformed value
  raises before any hop hook. `_supplied_leaf_filters` and the permission walk are unchanged. spec-027 says so. Tests:
  `tests/filters/test_sets.py`
- [x] 628. A many-to-many leaf, forward or reverse, whose through model's foreign key onto the leaf's target has a
  non-pk `to_field` is compared by the target's primary key, as its wire type says: `filters/base.py::
  _relation_uses_non_pk_to_field` asks `utils/relations.py::non_pk_forward_link` of that foreign key
  (`m2m_through_link_fields` resolves the side), so the leaf carries 511's marker and compiles through `<relation>__pk`
  in plain, scoped-hop and declared modes and as a Relay GlobalID leaf. It compared the `to_field` column: a linked
  row's pk matched nothing unless it equalled that row's `code`, and a code value matched some other row. A pk-target
  or source-side `to_field` link compiles byte-identically. spec-027 and the `filterset` glossary term say so. Tests:
  `tests/filters/test_base.py`
- [x] 577. A `SerializerMutation` save refused over a `blank=True, null=False` column the input left out, or a declared
  `allow_null` field set to `None`, is that column's field-keyed `null` error ("This field cannot be null."), as in the
  model and `ModelForm` flavors: `rest_framework/resolvers.py::_write_witness` records this write's attempted
  backing-model rows (a `pre_save` receiver scoped to the write's thread; a completed save drops out), and
  `_attempted_row_integrity_errors` runs `utils/write_values.py::unstorable_columns` over the row whose save was
  refused, falling back to the `"__all__"` `constraint` error. It answered that `"__all__"` error for every such cell.
  The `""`-over-`ArrayField` cell stays with row 45. A fakeshop `createItemHoldViaSerializer` pins it live; README,
  spec-039 and the `fielderror-envelope` / `djangomodelformmutation` glossary terms say so. Tests:
  `tests/rest_framework/test_resolvers.py`, `examples/fakeshop/test_query/test_products_api.py`
- [x] 523. A `DjangoModelFormMutation` whose form declares a built-in temporal field over a temporal column whose value
  it cannot read is refused at build (`forms/inputs.py::_require_temporal_reader`, beside the kind check, over the same
  binding sets): a Time column takes only the `TimeField` its own `formfield()` builds; a Date column also takes a
  `DateTimeField`; a DateTime column also takes a `SplitDateTimeField` (admin's pairing), and refuses a `DateField`,
  which stored midnight. Those pairs answered the masked `AttributeError` / `TypeError` (on every update too), a
  useless field-keyed error, or a silent truncation. A `CharField`, a subclass overriding `to_python` / `clean`, and a
  Duration column pass. spec-038, README and the `djangomodelformmutation` glossary term say so. Tests:
  `tests/forms/test_inputs.py`
- [x] 645. Async generated-mutation completion drains running field/list siblings inside its atomic after
  ordinary failures, preserving shared awaitables; caller cancellation cancels them once and drains cleanup across
  repeated cancellation. Active production masking snapshots managed and standalone result error lists at teardown,
  before result collection or an awaiting result hook can publish late resolver errors. Tests:
  `examples/fakeshop/test_query/test_completion_lifecycle.py`, `tests/test_completion.py`, `tests/test_error_policy.py`
- [x] 662. The state-folder retry and duplicated text reader belong to repository workspace/proof tooling,
  with no supported package wire/configuration path or public contract row. Closed as tooling robustness outside
  the package defect gate; no runtime fix is claimed (`scripts/workspace.py::_make_state_dir`).
- [x] 661. Closed-reader exit codes in repository check/build/review scripts are tooling robustness, with no
  supported package API or GraphQL wire/configuration path. The workspace command's own exit-code contract does
  not extend to those entry points; no script runtime fix is claimed.
- [x] 643. Corrupt run-log/state evidence is an input to repository workspace tooling, not a supported
  package API or GraphQL wire/configuration path. Closed as tooling robustness outside the package defect gate;
  no malformed-evidence runtime fix is claimed (`scripts/workspace.py::load_runs`).
- [x] 529. A decimal filter value whose spelling falls outside PostgreSQL `numeric`'s format (more than 131072 digits
  before the point or 16383 after, a huge negative or a tiny exponent) is refused by the filter ask as the field-keyed
  `FILTER_INVALID` "Enter a value the database can represent." on every filter family (generated `exact` / `in` /
  `range` / comparisons, declared `ListFilter` / `RangeFilter`, nested, `not`, decimal `ArrayField` elements) instead
  of the masked `DataError`: the filter ask (`filters/sets.py::_unbindable_value_errors`) reads each compiled
  `Decimal` through `utils/errors.py::refuses_numeric_format`, the one model of `numeric_in` the identity decode (591)
  shares; a zero is held only by its scale and its written exponent's bound. Other backends bind as given.
  spec-027, README and the `filterset` glossary term say so. Tests: `tests/utils/test_errors.py`,
  `tests/filters/test_sets.py`
- [x] 531. `node` / `nodes` and the relation-id decodes of the model (FK and M2M) and serializer (M2M) flavors match a
  requested id to its row by the id column's own value (`utils/querysets.py::identity_key`, the column's `to_python`,
  on both sides of `types/relay.py::_order_nodes`, `utils/querysets.py::pks_present` / `pks_all_present` and
  `utils/write_values.py::decode_visible_relation_ids`), not by `str()`: an unconstrained decimal key spelled with other
  trailing zeros or an exponent (`"2.50"` for a stored `2.5`, `"7E+1"` for `70`; PostgreSQL's kept scale) and an aware
  datetime key spelled in another UTC offset find their row instead of answering null or "Invalid id". A NodeID slot
  naming no model field keeps the string. spec-032, spec-036 and spec-039 say so. Tests:
  `tests/test_relay_node_field.py`, `tests/mutations/test_resolvers.py`, `tests/rest_framework/test_resolvers.py`,
  `tests/utils/test_querysets.py`
- [x] 534. `FilterSet` and `OrderSet` refuse an unknown `Meta` key at class creation, through the one typo guard every
  write flavor runs (`utils/inputs.py::reject_unknown_meta_keys`): a `FilterSet` takes the keys django-filter's
  `FilterSetOptions` reads plus the `filter_fields` synonym, an `OrderSet` `model`, `fields` and `exclude`; a `Meta` that
  is not a class is refused too. spec-027, spec-028 and the `filterset` / `orderset` glossary terms say so. Tests:
  `tests/filters/test_sets.py`, `tests/orders/test_sets.py`, `tests/utils/test_inputs.py`
- [x] 535. A `Meta.exclude` name is held in both set families (`sets_mixins.py::reject_unknown_exclude_names`): a name
  the set declares, own or inherited, is refused with the remedy (remove it, or `<name> = None`), as DRF refuses an
  excluded declared field; any other name outside the model's fields and the `Meta.fields` entries is refused naming
  the legal ones, as on a `DjangoType`. A non-string `Meta.exclude` or `Meta.fields` entry is a `ConfigurationError`
  naming the set in both families (`sets_mixins.py::require_field_name`), not a raw `AttributeError`. The `meta.exclude`
  glossary term, spec-027, spec-028 and the README say so. Tests: `tests/filters/test_sets.py`,
  `tests/orders/test_sets.py`
- [x] 536. A model-less `FilterSet` whose `Meta` sweeps (`"__all__"`, or `Meta.exclude` without `Meta.fields`) raises a
  `ConfigurationError` naming the set from `get_fields` (`sets_mixins.py::require_sweep_model`, the wording an
  `OrderSet` uses), not upstream's raw `AttributeError`; a model-less base whose subclass supplies `Meta.model` still
  builds in both families. Tests: `tests/filters/test_sets.py`
- [x] 629. Test prose in `tests/filters/test_sets.py`, `tests/test_routers.py`, `tests/test_strawberry_patches.py` and
  fakeshop's `test_transport_api.py`, `test_products_api.py` and `test_library_api.py` cites each contract by its
  content (the spec-046 Decision a test pins, the equivalence-matrix case it proves, the named test it defers to)
  instead of a test-plan row, matrix row, gap or test ordinal; comments and docstrings only (stripped ASTs and
  collected node ids identical).
- [x] 596. A `ProjectedChildFilter` a set does not hold (borrowed from another set's `get_filters()` without the
  branch it projects through) is a `ConfigurationError` at publish naming the set, the key, the donor child set and
  the branch (`filters/sets.py::FilterSet._reject_foreign_projection`), instead of a raw `KeyError` on supply or, under
  a same-named branch, the donor's child filter run silently across the borrower's branch. `FilterSetMetaclass`
  deep-copies a class-body filter another set already owns before stamping it, as django-filter never writes
  set-specific state on a shared filter, so the donor's record stays its own. spec-027 and the `filterset` glossary
  term say so. Tests: `tests/filters/test_sets.py`
- [x] 597. A declared head's name is never walked as a relation path: `run_active_input_permission_checks` asks the
  set's `_gate_path_spells_relations` seam, which a `FilterSet` answers "no" for a declared head, and
  `FilterSet._gate_path_walk_gates` walks a non-declared leaf's `field_name` even where a declared name spells the
  same string; so a flat expanded copy (`shelf__named` beside `real_shelf = RelatedFilter(..., field_name="shelf")`)
  and a plain declared filter named like another branch's accessor fire exactly their nested twin's gates. spec-027
  says so. Tests: `tests/filters/test_sets.py`
- [x] 650. The write-side check `utils/errors.py::unstorable_temporal` asks Django's own save-time preparation
  (`Field.get_db_prep_save` on the write connection) for every date, date-time, time and duration value it converts,
  instead of hand-modelling the conversions: an aware datetime a `DateField` cannot make naive in the default zone
  (year 1 / 9999 across an offset) is the field-keyed "Enter a value the database can represent." instead of the
  masked `OverflowError`. A naive datetime or a date bound to a date-time column is projected as Django binds it (the
  adapted `DateTimeField` naive branch; `LICENSE.django` ships beside ours), so no warnings filter is touched; the
  PostgreSQL rules run over the prepared values. spec-036, spec-038, spec-039, README and the `fielderror-envelope`
  glossary term say so. Tests: `tests/utils/test_errors.py`, `tests/rest_framework/test_resolvers.py`
- [x] 653. A `DurationField` write past 64 bits of microseconds on a backend without a native interval (SQLite, MySQL)
  is the field-keyed "Enter a value the database can represent." in every write flavor instead of the masked
  `OverflowError` at bind: `unstorable_temporal` holds the integer `get_db_prep_save` prepares to
  `utils/errors.py::binds_integer` (moved down from `utils/querysets.py`); PostgreSQL and Oracle bind any `timedelta`.
  Tests: `tests/utils/test_errors.py`, `tests/rest_framework/test_resolvers.py`
- [x] 606. FK-id elision fires into a Relay target whenever its GlobalID reads the primary key: the walker counts the
  `id` selection as the id slot's own model field (`optimizer/walker.py::_relay_id_field`, shared with
  `_relay_id_column`), so `parent { child { id } }` answers from the stored key column with no JOIN when the target's
  `Meta.fields` omit the pk or the pk is not named `id` (`isbn_13`); a NodeID on another column or a consumer
  `resolve_id` keeps the JOIN. spec-015, spec-004 and the `fk-id-elision` glossary term say so. Tests:
  `tests/optimizer/test_walker.py`, `examples/fakeshop/test_query/test_library_api.py`
- [x] 652. Generated integer `in` / `range` leaves over a transform (`year`, `iso_year`, `month`, `day`, `week`,
  `week_day`, `iso_week_day`, `quarter`, `hour`, `minute`, `second`, an `ArrayField`'s `len`) bind the transform's own
  output: `filters/base.py::IntegerInFilter` hands a transform's members to the lookup's own prep instead of coercing
  them through the column (which dropped every member), and `IntegerRangeFilter` applies its bounds through the
  transform (`<col>__year__gte`), so `year__in` / `year__range` answer the rows of those years; the value field is
  upstream's `django_filters.utils.resolve_field` output (`_bound_value_field`, cached). A member or bound past the
  database's integer range of any integer transform (a project-registered one and `len` included, whatever the column)
  is the field-keyed `FILTER_INVALID` through the filter ask (`filters/base.py::_reads_integer_transform`). spec-027,
  README and the `filterset` glossary term say so. Tests: `tests/filters/test_base.py`, `tests/filters/test_sets.py`
- [x] 663. Every configuration slot that reads a field-name or entry sequence refuses a whole text atom by its class
  (`utils/_narrowing.py::is_text_atom`, after `unwrap_lazy_object`): a lazy translation string (`gettext_lazy("name")`),
  any lazy `Promise` whatever it wraps, bytes, `bytearray`, `memoryview` and a `SimpleLazyObject` over any of them are
  the bare-string refusal instead of being read one name per character, at `utils/inputs.py::
  normalize_field_name_sequence` (all three mutation flavors' `Meta.fields` / `exclude` / `optional_fields` /
  `injected_fields` and the nested serializer config; the message names the slot), `utils/directives.py::
  validated_field_directives`, `permissions.py::_validate_fields`, `mutations/inputs.py::_frozenset_of_attr_names`,
  `utils/write_values.py::materialize_relation_id_container`, `write_mixins.py::_validate_permission_classes` and
  `types/converters.py::_unpack_choice_entry` (a lazy choice label stays a label). Specs 020, 029, 034, 038, 039 and
  053 and the `apply_cascade_permissions` glossary term say so. Tests: `tests/utils/test_inputs.py`,
  `tests/test_permissions.py`, `tests/utils/test_directives.py`, `tests/mutations/test_inputs.py`,
  `tests/utils/test_write_values.py`, `tests/test_write_mixins.py`, `tests/types/test_choice_entry_shapes.py`, and one
  lazy `Meta.exclude` row per mutation flavor
- [x] 579. The filter side names a flat copy and reads a supplied leaf by every form-data key its widget reads
  (`utils/widgets.py::widget_keys`): `filters/sets.py::_widget_keys` and `FilterSet._leaf_absent` read a
  `SplitArrayWidget`'s per-index keys (`<name>_0 ..`) and a nested `MultiWidget`'s deeper keys, so a child set's
  split-array copy on a set built outside the schema is bound and filters by `<prefix>-shelves__arr_0 ..` instead of
  being dropped, and the leaf reads as supplied; a widget reading no key keeps its bare name. Range bounds keep the
  two-key `multi_widget_keys`. spec-027 and the `utils/widgets.py` module docstring say so. Tests:
  `tests/filters/test_sets.py`
- [x] 654. The filter ask reads only the lookups a leaf binds for the user's value: `filters/sets.py::
  _bound_value_lookups` skips every expression that is one of the queryset's own annotations (by identity, per query
  and subquery), so a consumer annotation's out-of-range constant a leaf goes through never refuses an in-range value,
  while a leaf filtering on an annotation is still asked; and `utils/errors.py::binds_integer` holds no range for an
  `IntegerField` subclass whose internal type the backend states none for, instead of raising `KeyError` (the filter
  ask and `utils/querysets.py::coerce_field_value_or_none`). spec-027, spec-032 and README say so. Tests:
  `tests/filters/test_sets.py`, `tests/utils/test_errors.py`, `tests/utils/test_querysets.py`
- [x] 657. An `ArrayField` of integers is asked like the temporal and decimal arrays: each integer a lookup over the
  array or a slice of it binds for its right-hand side (an `ARRAY[...]` element, a slice element, a member of a list
  parameter) is held to its element column's range (`utils/errors.py::refuses_integer_range`) and a member past it is
  the field-keyed `FILTER_INVALID`, never dropped; a slice's bounds are no element, and an index `in` member or an
  array's `len` is held to its transform's own output range. A flat integer column stays unasked. spec-027, README
  and the `filterset` glossary term say so. Tests: `tests/filters/test_sets.py` (real `ArrayField` rows and a
  prepared-element double that runs without psycopg), `tests/utils/test_errors.py`
- [x] 670. A `DjangoModelFormMutation` form declaring `forms.DateTimeField` over a `DateField` column is refused at
  schema build (`forms/inputs.py::_TEMPORAL_COLUMN_FORM_CLASSES`, `_require_temporal_reader`), as the serializer flavor
  refuses the pair: the wire is the column's `Date`, and the form field made it midnight in the current time zone, so a
  zone ahead of the default stored an earlier day, also on an update omitting the field. A subclass overriding
  `to_python` or `clean` still builds. README, spec-038 and the `djangomodelformmutation` glossary term say so. Tests:
  `tests/forms/test_inputs.py`

## Outside review of the fixes

An outside review of the fixes since the hunt, by finding id (C-number). History only: not counted in Progress. Items with a
tracker number are recorded there; open remainders and new defects are filed as items 146-150.

| Finding | Outcome | Commits |
|---|---|---|
| C11. A nested keyset window paged by `get_queryset`'s order but sought and minted by `Meta.cursor_field` | Item 95 | `5197d03d` |
| C11, reversed. A `.reverse()`d `get_queryset` order paged with forward cursor terms | Item 99 | `b005a7ee` |
| C8. A relation pk prefix on a GlobalID filter path skipped model validation | Fixed | `d03a7c79` |
| C45. A nested combinator projecting `.values()` raised a raw SQL error | Fixed | `1bd0f0f4` |
| C48. The public test clients could not serialize a `Mapping` of variables | Fixed | `d5f0d6f7` |
| C54. The `RangeFilter` input cache failed on an unhashable filter subclass | Fixed: the cache is gone | `702c6b67` |
| C57. A renaming `NameConverter` broke type-strategy GlobalID round trips | Item 116 | `e05b2436` |
| C33. Relay's sync refusal left the async `resolve_node` coroutine unawaited | Fixed | `f35a441c` |
| C41. `review_plan --changed` omitted deleted modules | Fixed | `96164e29` |
| C53. `count_queries` compared reports of different executed operations | Fixed | `48ca8bec` |
| C46. Two `prove_failability.py` runs could both own the tree | Item 119 | `ce338eec` |
| C3. A run queued during a copy's first sync resynced over the edits made since | Item 139 | `4ed767bb` |
| C4. `workspace.py release` / `gc` dropped active work after their busy check | Item 140 | `4ed767bb` |
| C9. A qualified or aliased `DjangoOptimizerExtension` evaded the governance gate | Fixed | `40a0fb96` |
| C55. A negative definition test passed with its production guard removed | Fixed | `ae18e793` |
| C31. A concurrent ledger test shared one `Context` across threads | Fixed | `dfc32247` |
| C40. A reverse one-to-one visibility test lost the planned optimizer path | Fixed | `962c61b9` |
| C6. Docs: MySQL's ASC `NULL` placement was reversed | Fixed | `f4c9f78a` |
| C16. Docs: the migration plan mapped the page cap to the raw-list cap | Fixed | `fce3ab31` |
| C17. Docs: explicit-null update timing promised no earlier DB work | Fixed | `e1b1e202` |
| C18. Docs: the edges-only rationale claimed an N+1 fetch | Fixed | `fe884e44` |
| C19. Docs: the offset-only plan left the high mark unchanged | Fixed | `4a736809` |
| C20. Docs: the limit-only plan promised null on a non-null outer list | Fixed | `affe41dc` |
| C25. Docs: the live-test README reversed the ruff fix / format order | Fixed | `56ecb877` |
| C28. Docs: the serializer reverse one-to-one cardinality example was inverted | Fixed | `00bb2482` |
| C42. The item-diff check omitted new untracked files (now included); staging alone still changes its seal | Partial; remainder item 146 | `acb6c25a` |
| C24. The KANBAN glossary inliner linked terms inside existing links | Fixed; remainder closed by item 147 | `09d0caa0` |
| C44. The test-model census conflated same-named classes across scopes (fixed); imports still resolve through one flat map | Partial; remainder item 148 | `f7000986` |
| C15. An in-place change to the settings `OrderedDict` stays stale | Not a defect: configuration is trusted after construction; only an exact `dict` source is held by reference (other mappings are copied by design, per `conf.py::_normalize_user_settings`), and replacing or overriding the setting reloads (`override_settings` fires `setting_changed`) | none |

## To do: found along the way

- [ ] 387. Generated opt-in `year` / `iso_year` filter leaves are typed as the column's scalar (`Date` / `DateTime`), so
  every wire value cleans to `"Enter a number."`; and the generated `time` leaf on a `DateTimeField` raises
  `AttributeError: 'datetime.datetime' object has no attribute 'strip'` in `forms.TimeField` clean before the filter
  seam

- [ ] 563. Package comments and docstrings outside the gated phrases still narrate history: "now", "no longer", "the
  former", "byte-unchanged" (634 removed every release number and gates it); judge each against START's provenance rule (dry-0_0_15_3 items 31 and 71 cover part of it; 566 restated the
  `(hardened)`, `(hardening)` and `historically` sites in `schema.py` and `rest_framework/`). Found fact-finding 500
- [ ] 565. Optimizer plan labels (B1-B8, O2-O6, G1-G3) label 177 comment and docstring sites, 15 of them in the
  package (`optimizer/extension.py`, `optimizer/plans.py`, `optimizer/walker.py`, `types/resolvers.py`) and most in
  `tests/optimizer/test_extension.py` and `test_walker.py`; the clause after each label already states the behaviour,
  so drop the label. Found fact-finding 500
- [ ] 574. (robustness) A `blank=False` column a `required=False` form field cleans to `""` (Django's
  `_get_validation_exclusions` leaves it out of `full_clean`) answers the masked error at save (a raw `DataError` on
  an `ArrayField`, measured); `_is_unstorable_blank` needs `blank=True`, so no column that stores no empty string is
  named in this shape. Found fixing 541
- [ ] 620. (robustness) On a `null=True` `ArrayField`, a `ModelForm` explicit `null`, or an update omitting the field
  over a stored NULL, writes `[]` instead of NULL, with the default `SimpleArrayField` and a `SplitArrayField` alike.
  Found verifying 553
- [ ] 621. (robustness) A `get_form` hook binding `QueryDict(urlencode(data))` turns a `SplitDateTimeField`'s datetime
  into text, which `SplitDateTimeWidget.decompress` cannot split: the request answers a top-level `AttributeError` (it
  silently stored NULL before 553's binding). Found verifying 553
- [ ] 624. A package `RangeFilter` whose `lookup_expr` carries a transform (`date__range`, `date__exact`, `date`)
  applies a lone bound as `<field_name>__gte` / `__lte` without it: `RangeFilter(field_name="occurred_at",
  lookup_expr="date__range")` sent `{end: "2021-12-31"}` compares the datetime with midnight and leaves out a
  2021-12-31 09:30 row that both bounds include; spec-027's RangeFilter row says a lone bound applies as `gte` / `lte`
  of the declared range. Its bounds are also cleaned by the column's own `gte` field whatever the transform, so a
  `year` lookup refuses a year as "Enter a valid date/time.". Found verifying 508
- [ ] 625. (robustness) A package `ListFilter` declared with a lookup other than `in` (the default `exact`, `gte`)
  hands the list to a scalar lookup: a masked `ValidationError` / `TypeError` over a decimal or number column and
  silently no rows over text, even for one element. A consumer-declared bare `BaseCSVFilter` subclass does the same
  with `exact` / `iexact` / `icontains` / `startswith` (as plain django-filter does), and with `range` a one-element
  list raises `IndexError` from `Range.get_rhs_op`. A build-time refusal must allow every list-consuming lookup (`in`,
  `range`, transforms ending in either, `ArrayField` `contains` / `contained_by` / `overlap`, `has_keys` /
  `has_any_keys`, a consumer-registered lookup) and every `method=` filter. Found fixing 508; widened triaging 516
- [ ] 524. (robustness) A `ModelForm` update that omits a field whose declared form field is lossier than its column
  (`forms.DateField` over a `DateTimeField`) rebinds the stored value through that field and rewrites the row: a
  stored `03:04:05` becomes the default-zone midnight, and a stored year-1 value under `Asia/Tokyo` answers an
  `invalid` `FieldError` keyed to a field the client did not send. Found fact-finding 547
- [ ] 527. (robustness) A declared `ListFilter` (or `RangeFilter`) whose `field_name` is a relation itself keeps
  its elements uncleaned ("a relation's elements reach the ORM as sent"), so under `DjangoFilterBackend` a junk raw
  value (`?tag=x` on a ForeignKey to an integer key) answers Django's `ValueError`, a 500, where a column path
  (`tag__pk`) answers the form's 400; the schema build refuses such a declaration, so GraphQL cannot send it. Found
  verifying 512
- [ ] 530. (robustness) The three write flavors accept `"1e1000000"` (or `"1e-1000000"`) for a Django 6.1
  `DecimalField` with no `max_digits` (a serializer through an explicit `serializers.DecimalField(max_digits=None,
  decimal_places=None)`): PostgreSQL refuses the bind with a masked `DataError`, and SQLite stores it as `Infinity`
  or `0` without a word. Found verifying 591
- [ ] 537. (robustness) `AllValuesMultipleFilter(field_name=<column>, method=...)` is refused at schema build ("exposes
  no form field") though its column alone would type it, as the same filter without `method=` is typed: its form field
  reads the per-request `model`, so the unbound copy builds none and the catch-all refuses before the column is
  consulted. Found implementing 517
- [ ] 538. (robustness) A `DateRangeFilter` declared on a `Choices` column builds and types as the column's enum, while
  its own form field accepts only its fixed date-range keys, so every enum member answers `FILTER_INVALID` "Select a
  valid choice"; the same filter on a plain column is refused at schema build. Found verifying 518
- [ ] 656. A whole-array `ArrayFilter` over an `ArrayField` column (generated through `Meta.filter_overrides`, or
  declared) fails the schema build: `filters/inputs.py::_element_annotation` asks `_scalar_from_model_field` of the
  `ArrayField` itself (`types/converters.py::scalar_for_field` raises "Unsupported Django field type 'ArrayField'")
  instead of its element (`array_element_field`); only index / slice / `len` leaves publish (F11 area). Found
  fact-finding 389
- [ ] 666. A declared hop-walking flat filter whose `filter` constrains on an absent or no-bound value raises
  `SyncMisuseError` on `apply_async` when the hop target's `get_queryset` is async-only: the async pre-pass awaits only
  the leaves the form data names, and the sync `.qs` absent-leaf probe then derives the hop inside the sync boundary
  (spec-027: an async-only `get_queryset` never runs there). An omitted leaf raised before 562; a no-bound range joins
  it. Await the hops of every declared walking leaf whose filter acts on an absent value. Found verifying 562
- [ ] 668. (robustness) The save-time `null` diagnosis (serializer `_attempted_row_integrity_errors`, model
  `_created_row_integrity_errors`) reads every unstorable column of the refused row, so a consumer save with
  `update_fields` excluding the `None` column, or a refused save the consumer swallows before a different
  `IntegrityError` escapes, reports that column's `null` for another constraint; read `update_fields` from the
  `pre_save` kwargs and skip columns outside it. Found verifying 577
- [ ] 672. (robustness) On SQLite a decimal filter value past float range or below its smallest subnormal binds as
  REAL: `"1e-1000000"` underflows to 0.0 (`exact` matches a stored 0, `lt` drops it) and `"-1e1000000"` becomes -inf,
  so the filter answers wrong rows without a word. Found fact-finding 529
- [ ] 673. (robustness) A generated `NumberFilter` leaf on an `IntegerField` / `FloatField` column cleans
  `"-1e1000000"` to a `Decimal` that reaches the bind as a huge int (integer column) or -inf (float column); the
  filter ask reads only temporal and decimal columns. Unmeasured: the client-visible answer per backend. Found fixing
  529
- [ ] 675. (robustness) SQLite stores an unconstrained `DecimalField` key past 15 significant digits as a float (read
  back rounded), so `node` / `nodes` answer null for an id spelling the written value. Found fixing 531
- [ ] 676. (robustness) A naive datetime id on a `DateTimeField`-pk Relay type answers the masked error on `node` and
  `nodes` (unexamined: possibly the naive-datetime bind warning). Found fact-finding 531
- [ ] 679. Ordinal citations outside 629's six files: `_strawberry_patches.py` names its shields "gap 1" / "gap 2"
  (the shield comment, the retirement-diagnostic docstring, its "GAP 1 STILL NEEDED" print literals) where the tests
  say "decode failure" / "non-envelope body"; plan-section labels "C.3 / C.3a", "C.4 -", "C.4 fixtures" in
  `tests/filters/test_sets.py` and "C.5 expanded-origin" in `test_library_api.py`; `(#4 / #13)` /
  `(#10 happy path)` tags in `tests/rest_framework/test_resolvers.py` / `test_sets.py`, `#6` / `#7` / `#11` in
  `test_library_api.py`, "Test-6 identity flake" in `tests/test_routers.py`, and "DoD item N" / "Goal N" in about 12
  test lines; restate each by its contract. Found fixing 629
- [ ] 680. `filters/inputs.py::_is_declared_head`'s docstring says a set borrowing a copy "restamps" it; 596 copies an
  owned filter at declaration, so the clause is false (one-clause fix, held for the `filters/inputs.py` refactor).
  Found fixing 596
- [ ] 681. (robustness) A `DjangoModelFormMutation` whose `forms.DateTimeField` over a `DateField` column (a pairing
  the build accepts), or whose `clean_<field>` hook, yields an aware datetime Django cannot make naive in the default
  zone (year 1 / 9999 across an offset) raises `OverflowError` inside `form.is_valid()` (`DateField.to_python`), the
  masked error, before the package's unstorable check runs (`forms/resolvers.py`). Found fact-finding 650
  The `forms/resolvers.py` docstrings describing the write-side check as "datetime or time" columns go stale with 650
  (DateField and DurationField columns are held too): fix them with this row.
- [ ] 682. (robustness) `types/definition.py::origin_has_custom_id_resolver` counts any class-dict attribute named after
  the primary key as a consumer `resolve_id`, including the relation resolver the framework installs for a listed
  one-to-one pk, so FK-id elision never fires into such a type (fakeshop `annotation { profile { id } }` on
  `PatronProfileType` keeps its JOIN). Found fixing 606
- [ ] 683. (robustness) `nodes(ids:)` over a type selecting a to-one relation's `id` (`AnnotationType`, `profile { id }`)
  runs one query per row: the node fields dispatch without an optimizer pass, so the relation is never planned.
  Decide planning the node root fields or documenting the cost. Found fixing 606
- [ ] 684. (robustness) A declared `ListFilter` / `RangeFilter` with a transform in `lookup_expr`
  (`field_name="occurred_at", lookup_expr="year__in"`) cleans each member through the column's form field
  (`filters/base.py::_column_form_field` reads `_bound_model_field`), so `"2020"` answers "Enter a valid date/time."
  (F6 area). Found fact-finding 652
- [ ] 685. (robustness) A fractional member of a generated integer `in` leaf truncates to a matching integer
  (`signed_big__in="1.5"` matches 1; `IntegerField.to_python`), where the exact leaf refuses it. Found fact-finding 652
- [ ] 688. (robustness) A declared `ListFilter(field_name="<col>__year", lookup_expr="in")` refuses an integral
  decimal member (`"2020.0"`, `"2.02e3"`) with "Enter a value the database can represent." where the generated
  `year__in` leaf matches the 2020 rows. Found verifying 652
- [ ] 692. (robustness) A nested integer `ArrayField` filter (`ArrayField(ArrayField(IntegerField))`, `contains`)
  cleans its members as text (`[["1", "9223372036854775808"]]`) and binds them as strings, so the integer ask never
  reads them and PostgreSQL refuses the cast at execution (the element form field, `filters/base.py`). Found
  verifying 657
- [ ] 693. (robustness) `filters/sets.py::_unbindable_predicate`'s params-wide rules (`refuses_utc_offset`,
  `refuses_numeric_format`, `psycopg_refuses_list_parameter`) read the compiled params of the whole clause, so a
  constant inside a consumer annotation the leaf goes through (a `Value(Decimal(...))` past `numeric`'s format) can
  refuse the user's in-range value; hold them to the leaf's own bound lookups as 654 does for integers. Found
  verifying 654

## To do: holes found re-checking the fixes


## Waiting on you

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
  represent." instead of a masked error; the release ships Django's license text (`LICENSE.django`)
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
- [ ] 655. Decide: on PostgreSQL a `year` / `month` transform `in` member or `range` bound between 2**31 and 2**63 is
  refused as `FILTER_INVALID` (the transform binds an `IntegerField`, int32 there; 385), while Django's own
  `IntegerFieldOverflow` answers `month__gt=2**31` as no / every row and the package's integer-column `in` drops such
  a member. Keep the refusal, or answer it as Django does (drop the member; clamp the bound)?
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
- [ ] 601. Decide whether a filter a `get_filters()` override adds (undeclared, so absent from
  `declared_filters`) gates on its own name (`check_<name>_permission`) like a declared filter, or on its
  `field_name` as it does now (`filters/inputs.py::leaf_gate_path`; pinned by
  `tests/filters/test_sets.py::test_a_filter_a_get_filters_override_adds_is_gated_on_its_field_name`): moving
  a declaration into an override silently swaps `check_extra_permission` for `check_topic_permission`. Found
  researching 599
- [ ] 631. Decide what a `DjangoModelFormMutation` answers when a consumer-declared form field cleans `""` (an
  omitted create value, an explicit `null`, or `""` on an `ArrayField`) over a `null=True, blank=True` column that
  stores no empty string. Today `forms/resolvers.py::_is_unstorable_blank` ignores `null`, so the column answers "This
  field cannot be null." (code `null`), false on a column that takes NULL, while the model flavor and DRF store NULL
  for the same client input. Options:
  - (a) write NULL. This overrides the form's cleaned value ("the form is the input source of truth") and needs a
    savepointed retry after a PostgreSQL `DataError`.
  - (b) a truthful field-keyed `invalid` error: the column's own `to_python("")` message (integer, float, decimal,
    date, UUID) and a package message where it has none (`ArrayField`).
  - (c) keep it and say so in README / GLOSSARY / spec-038, with `null=True` twins of
    `tests/forms/test_resolvers.py::test_modelform_blank_choice_save_failure_is_field_keyed_null_error` and the
    `ArrayField` row pinning it.
  - (d) narrow the predicate to `not field.null`. This leaves a masked `ValueError` / `DataError`, or an `__all__`
    `invalid`, depending on the column kind.
  Row 572's parenthetical follows the answer. Found fixing 573
- [ ] 377. Decide whether the package supersedes graphql-core 3.2's `ExecutionContext.execute_fields` and
  `complete_list_value` bodies in `django_strawberry_framework/_graphql_core_patches.py` so every awaitable an operation
  created settles inside it before an error propagates. Today a sync field raising on a non-null position after an
  async sibling drops the sibling's coroutine unstarted ("coroutine ... was never awaited" at GC for graphql-core's
  `execute_field.<locals>.await_result` plus the resolver's own: the package's `many_resolver._resolve`,
  `list_field.py::_execute_queryset_pipeline_async`, `connection.py::_pipeline_async`, or strawberry's
  `_async_resolver` for any consumer `async def` field); the same holds for a `[T!]!` item. Identical bodies across
  3.2.0-3.2.13; graphql-core 3.3 settles them in the background (`settle_in_background`). A package-side lazy
  awaitable removes only the package's coroutine (graphql-core's `await_result` still warns); `close()` cannot reach
  the inner coroutine. Recommended shape (prototyped on 3.2.8): settle before re-raising (`gather(...,
  return_exceptions=True)` then raise the first error in declaration order), also at both `gather` sites, with
  audited-body pins and retirement sentinels like the existing `complete_list_value` arm; data and error paths
  measured identical for nullable, non-null, root and list parents. Costs: about 90 lines of upstream body
  superseded; the failure path now runs the sibling work instead of failing fast; under `execute_sync` a consumer
  `async def` field beside a raising non-null field answers strawberry's "failed to complete synchronously" instead
  of `data: null`; 3.3's background settle loses the in-operation guarantee unless its `async_work_finished` hook is
  wired. Not taken: 3.3-style background settle (late errors would land after `MaskErrors` and after the operation's
  atomic and leases closed). No contract row: the response is identical, so this is a robustness question of scope
- [ ] 644. CHANGELOG entry for item 374: a declared `django_filters.NumericRangeFilter`, or any one-value filter whose
  widget reads other form-data keys (a `MultiWidget` on a `CharFilter`, a consumer `Filter` over a `MultiValueField`),
  now fails the schema build with a `ConfigurationError` instead of publishing an input whose value was ignored
- [ ] 595. CHANGELOG entry for item 640: a flat filter field copied from a child set's declared filter through
  a `RelatedFilter` whose attribute differs from its `field_name` (`inSeriesHandle` over `in_series =
  RelatedFilter(..., field_name="series")`) now fires the branch gate and the child filter's own gate its
  nested spelling fires; such a query a denying `check_*_permission` refused only when nested is now refused
  flat too
- [ ] 641. `AllValuesFilter` / `AllValuesMultipleFilter` build their choices from the model's unscoped
  `_default_manager.distinct()` (django-filter's rule), so over a type whose `get_queryset` hides a row a value only
  that row holds answers no rows while a value no row holds answers `invalid_choice`: an existence oracle, live at
  the parent on choice columns and, after 515, on text columns through `AllValuesMultipleFilter`; it also runs one
  DISTINCT per filtered request even when the leaf is unsent. GLOSSARY "Choice leaves" documents it and the
  consumer remedy. Should the package scope the choices to the bound copy's `parent.queryset` (in
  `sets.py::FilterSet._copy_filter`, honouring a consumer `field` override; a flat hop leaf needs its hop's
  visibility), changing what a DRF view over the same `FilterSet` sees, or keep django-filter's rule?
- [ ] 642. CHANGELOG entry for item 515: a declared `MultipleChoiceFilter` / `TypedMultipleChoiceFilter` /
  `AllValuesMultipleFilter` publishes `exact: [<column type>!]` (it published a scalar and answered every wire value
  with `FILTER_INVALID` "Enter a list of values."); `apply_sync` with a non-list for one raises `ConfigurationError`
  where it answered `FILTER_INVALID`
- [ ] 594. A model whose `Meta.db_table` is a lazy translation string (`gettext_lazy("products_category")`):
  Django serves `all()`, `order_by()`, `filter()` and both `union()` forms over it, but
  `utils/querysets.py::_seal_or_defect` refuses `filter()` and a baked `union()` ("query alias_refcount has
  a non-string key") and an unbaked `all().union(all())` ("QuerySet binds a __proxy__ bound value"),
  while `all()` and `order_by()` seal. Should the seal admit a lazy table name as the exact text it spells,
  as it admits a `TextChoices` / `StrEnum` member (d1bb1e97), refuse it at schema build, or treat a lazy
  `db_table` as outside the supported shapes (Django documents a string)? Pinned refused by
  `tests/utils/test_querysets.py::test_lazy_db_table_combination_rewrite_fails_closed_typed`
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
- [ ] 623. Decide whether a partial `DjangoModelFormMutation` update that omits a built-in single-value field over an
  `ArrayField`, whose form sets no initial for it, should be refused instead of writing what the field makes of the
  stored list (`CharField`: its text, `["['x']"]`; `BooleanField`: its truthiness, `[True]` over `[False]`). Today
  spec-038 Decision 8, the GLOSSARY and the update's build warning state the write, and a form presenting one stored
  element in `self.initial` keeps the row; a refusal would need the package to tell "the field accepted the stored
  list" from "the form chose that value", and changes a documented answer. Found fixing 554
- [ ] 622. Decide whether a declared django-filter range / `in` class (`django_filters.RangeFilter`, a
  `BaseRangeFilter` or `BaseInFilter` over `NumberFilter`) on an integer column is held to the backend's integer
  range. Today it answers as plain django-filter: a two-bound range or a member past int64 on a `BigIntegerField` is a
  masked `OverflowError` on SQLite and under PostgreSQL server-side binding, and the right rows under psycopg 3
  client-side binding, while the package's `RangeFilter` / `ListFilter` widen, match nothing or drop the member (372).
  Options: refuse it with `FILTER_INVALID` at the `FilterSet._unbindable_temporal_errors` seam, which already reads
  every declared filter's cleaned value (backend-independent, so it narrows what PostgreSQL client-side answers
  today); or document django-filter's behaviour and name the package's `RangeFilter` / `ListFilter` as the remedy.
  Rewriting the declared filter's own `filter()` call would bypass a consumer subclass and its `exclude` / `distinct`.
  Found fixing 507
- [ ] 578. CHANGELOG entry for item 553: a `DjangoModelFormMutation` field whose widget reads several keys is bound
  under them: a `SplitArrayField` over an `ArrayField` and a `SplitDateTimeField` over a `DateTimeField` now write the
  value sent (they answered "This field is required.", or an optional `SplitArrayField` wrote `[]` and an update
  omitting it erased the stored list); a list longer than a `SplitArrayField`'s `size` answers the field's
  `max_length` error instead of being truncated
- [ ] 576. Decide how a PostgreSQL form field with no model column behind it (a plain `Form` field or a `ModelForm`
  extra field) is published. Today `SimpleArrayField` is `String` by its `CharField` ancestry: the client sends
  delimited text, cannot send an element holding the delimiter, and JSON text is split on commas, while the same field
  over an `ArrayField` column takes the column's list and the sibling list readers off-column are lists
  (`MultipleChoiceField` `[String!]`, `JSONField` `JSON`, the serializer flavor's `ListField` `list[child]`);
  `SplitArrayField` (552) and the range form fields raise `ConfigurationError` at build, `HStoreField` is `String`.
  Publishing `SimpleArrayField` as the base field's list changes existing schemas' SDL and needs the element type from
  `base_field` (nested arrays, element nullability); graphene-django publishes `String` for all of them. Found fixing
  551
- [ ] 572. CHANGELOG entry for item 541: on PostgreSQL, a `DjangoModelFormMutation` whose optional single-value form
  field over a `blank=True, null=False` `ArrayField` cleans an empty, `null` or omitted value to `""` now answers that
  column's field-keyed `null` error instead of the masked error (a `null=True` such column answers it too, as a
  nullable non-text choice column already did)
- [ ] 571. Decide whether a `regex` / `iRegex` filter operand the backend refuses answers `FILTER_INVALID` keyed to
  its leaf instead of the masked error. Every refused filter value the package codes today is checked before the
  queryset runs (`FilterSet._validate_form_or_raise`), and only the filter step knows the leaf; after execution the
  error carries no field (and on SQLite not even its `re.error`). A faithful check has to ask the backend, as
  `utils/errors.py::unbindable_temporal` does: Python `re.compile` (warnings caught) is exact for SQLite only, and
  depends on the interpreter; PostgreSQL needs its own probe (`SELECT '' ~ %s`, savepointed inside a transaction),
  since `re` both refuses valid ARE (`\m`, `\y`, `(?b)`, POSIX classes) and accepts invalid ones (`(?P<n>...)`, atomic
  groups, `\z`); MySQL and Oracle have no probe measured. Promising it changes SQLite's empty-table or all-NULL `[]`
  into `FILTER_INVALID`. Upstream answers the raw error everywhere. Found fixing 549
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
- [ ] 522. Feature card? A value plus lookup input for `LookupChoiceFilter` (lookup as an enum of its
  `lookup_choices`), so it filters over GraphQL instead of being refused at build; no upstream (graphene-django,
  django-graphene-filters, strawberry-django) publishes one.
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
- [ ] 327. Design call: should `node(id:)` / `nodes(ids:)` roots be optimizer-planned, in this hunt or as a card?
  `types/relay.py::_resolve_node_default` / `_resolve_nodes_default` (and the async twins) return model rows the
  optimizer never plans (`optimizer/extension.py::DjangoOptimizerExtension._optimize` passes a non-`QuerySet` through),
  so every nested relation lazy-loads per parent: `nodes(ids: [5 books]) { ... on BookType { loans { id } } }` is 6
  statements against 2 under `allLibraryBooks` (a forward `shelf` 11 against 2), the root SELECT is unprojected, the
  async path is the same, and under `strictness="raise"` every nested relation raises `Unplanned N+1: <field>`, one
  parent included. Documented as a limit (spec-015 "not wired ... the seam stays open", GLOSSARY "a single-node
  refetch receives no optimizer plan", pinned by
  `examples/fakeshop/test_query/test_library_api.py::_LOAN_QUERYSET_METHOD_HOOK_CASES`), and no card owns it, while
  GOAL.md's `astronomy` paragraph pairs `DjangoNodeField` roots with "N+1-safe planning across every nested selection,
  with `strictness="raise"`". Fix shape: plan through `optimizer/extension.py::apply_connection_optimization` /
  `_async` (the seam `mutations/resolvers.py::refetch_optimized` uses). The typed `DjangoNodeField(T)` /
  `DjangoNodesField(T)` roots need about 70-120 source lines; the bare `relay.Node` form needs the per-type fragment
  narrowing (`optimizer/selections.py` G3) that spec-035 Decisions 6/7 defer to BACKLOG
  `polymorphic_interface_connections`, about 400-800 lines across three test trees in all. AGENTS rule 5 bars landing the
  typed form alone ahead of the bare one. Row 353 (`_stamp_node_type`) lands first either way. Fact-found at `116b57f6`
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
- [ ] 411. Design call: should `types/base.py::_is_auto_annotation` recognize aliased `auto` spellings under
  `from __future__ import annotations` by resolving a Name / Attribute annotation against the defining module's
  globals? Today they fail loud with a raw Strawberry `TypeError`; the documented policy (here and for `NodeID`) is
  spelling-match without evaluation
- [ ] 412. Design call: generated names join `<TypeName><Pascal(field)>` with no separator, so prefix-related names
  collide: a `Product.category_kind` choice and a `ProductCategory.kind` choice both produce `ProductCategoryKindEnum`
  and schema build fails with `DuplicatedTypeName`; the same shape applies to `FilterInputType`, `RangeInputType` and
  narrowed `<Model>...Input` names. It fails loud; the fix is a name-contract change
- [ ] 413. CI: `makemigrations --check --dry-run` reports no changes at HEAD, but nothing gates it; add it to the lint
  job
- [ ] 414. Tooling: `.envrc` exports `DJANGO_SETTINGS_MODULE=config.settings` while `pytest.ini` names
  `config.test_settings`, and the env var wins; drop the export or assert the module under pytest
- [ ] 415. CI: `postgres.yml` has no Postgres x `FAKESHOP_SHARDED` cell, so `lateral_fetch`'s Postgres-only path never
  runs sharded; add one and run the Postgres tier once per release
- [ ] 416. CI: only the 5.2.16 / 3.10 cell pins strawberry 0.322.2; add a cell pinning it on Django 6.x
- [ ] 417. CI: run the weekly Postgres tier with `--cov` and diff its executed lines against SQLite's
- [ ] 418. CI: a periodic `-n0` run with randomized module order, to catch order-dependent process state
- [ ] 419. CI: a Postgres-tier keyset round-trip over a Decimal and an aware-DateTime `cursor_field`
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
- [ ] 461. Decide whether `strictness` reports the per-parent re-reads that remain after 380 (a consumer `Prefetch`
  seed over another model, a consumer lookup deeper than the planned path or on a `SKIP`-hinted relation onto a hooked
  target): each answers correctly but costs one query per parent and `types/resolvers.py::_check_n1` stays silent
  (it asks only the instance cache); reporting them under `strictness="raise"` would error queries that answer today
- [ ] 352. CHANGELOG entry for item 343: on Django 6.1, a `get_queryset` hook or default manager returning
  `.fetch_mode(FETCH_PEERS)` or `.fetch_mode(FETCH_RAISE)` keeps that mode through the visibility seal (root lists,
  connections, nested relations, prefetch children, `node(id:)` and `nodes(ids:)`, the mutation locate), so lazy loads
  batch or raise as the project set; a fetch mode object other than Django's three is refused as an unsealable queryset
- [ ] 351. A column-backed `ModelChoiceField` / `ModelMultipleChoiceField` declared with a class-level `queryset=None`
  that no `__init__` or `get_form` assigns builds, and every request binding it fails with Django's raw
  `AttributeError` (`'NoneType' object has no attribute 'model'` / `'filter'`) inside `is_valid()`, because
  `forms/resolvers.py::_assert_bound_choice_agreement` leaves a queryset-less bound field to the form (the documented
  row; Django's own form fails the same way). Found landing 340. Decide: keep it Django's error, or refuse a bound
  queryset-less field with a `ConfigurationError` at request time
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
- [ ] 321. The write side passes a `relay.NodeID` over a non-column attribute (one the type's `get_queryset`
  annotates) through as the raw primary key (`relay.py::_resolve_real_pk`, pinned by
  `tests/test_relay_node_field.py::test_decode_model_global_id_passes_raw_value_for_non_field_node_id`), so a relation
  write naming such a type stores whichever row's pk equals the id's text, while the filter side now refuses that slot
  across a relation (`GLOBALID_UNVALIDATABLE`). Refuse it on writes too, or keep the pass-through? Found landing 290
- [ ] 316. `filters/base.py::RangeFilter` declared with the default `lookup_expr` (`exact`), the django-filter
  spelling `RangeFilter(field_name="x")`, publishes the `{start, end}` input under an `exact` key, applies a lone
  bound as `__gte` / `__lte`, and hands two bounds as one list to the declared lookup: a masked error over a number,
  decimal, date, datetime or relation-key column and silently wrong rows over text (`exact` none, `gte` all on
  SQLite); nothing validates the declaration (also filed as 508, with a 3738-cell grid). Options: (a) default
  `lookup_expr` to `range` (the input key becomes `range`); (b) refuse a non-`range` lookup with `ConfigurationError`
  at class build; (c) keep the declaration and its input key and compare two bounds as a range whatever the terminal
  lookup (except a declared `range` or `in`), keeping a transform prefix (`date__exact` -> `date__range`) and 372's
  integer `gte` + `lte`, as django-filter's `RangeFilter` does: prototyped and verified, 668 two-bound cells change
  (448 masked errors and 220 wrong answers become the declared-`range` answer), no other cell changes; it would also
  make 315's "both bounds keep the declared lookup" false
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
- [ ] 281. A `GenericForeignKey` written beside its carriers: a serializer with writable `content_object` and writable
  `object_id` / `content_type` builds, and a request pairing a visible object's id with another row's `objectId` stores
  that row (a writable `object_id` alone is already a raw write); post-save attestation covers single-column FK /
  one-to-one and many-to-many only, so a custom `update()` dropping `content_object` succeeds unattested. Refuse
  carriers beside their GFK (and a `ForeignObject` beside its carriers, accepted on purpose today), attest the GFK
  columns, or keep?
- [ ] 277. CHANGELOG entry for item 109: a `SerializerMutation` relation field bound to the `pk` alias of a relation primary
  key (`PrimaryKeyRelatedField(source="pk")` over a one-to-one or multi-table parent-link key, or DRF's auto-built `pk`
  field there) now raises `ConfigurationError` at schema build for a create input (0.0.14 built it and every create
  answered a masked error); `source="<relation name>"` keeps the GraphQL name
- [ ] 278. A `SerializerMutation` create through a declared writable multi-table parent link (`venue_ptr =
  PrimaryKeyRelatedField(queryset=Venue.objects.all())`, or `source="venue_ptr"`) naming an existing parent row overwrites
  that row's columns with the child's defaults and answers `errors: []` (plain DRF does the same; DRF never auto-builds a
  writable parent link). The model flavor leaves a parent link out of create inputs; refuse it on the serializer flavor
  too, or keep the declared serializer as the input source of truth? The attname / `pk`-alias remedies name
  `source="venue_ptr"` today
- [ ] 279. The column-spelled relation refusal (`attname` and `pk` alias) fires at schema build regardless of a consumer
  `create()` / `update()` that handles the key itself (a nested child `pid = PrimaryKeyRelatedField(source="pk")` under an
  `update()` that ignores it ran at 0.0.14); make the whole family override-aware, or keep refusing (spec-039: "at every
  opted-in nesting depth")? Same question as item 108 for column-less sources
- [ ] 26. A mutation class whose `__name__` raises, is not a `str`, is a format-hostile `str` subclass, or is not a
  GraphQL name: fail at declaration with a typed error, or keep? At HEAD the model and form flavors fail raw at declaration
  (`mutations/sets.py::DjangoMutation._validate_meta`, `forms/sets.py::DjangoModelFormMutation._validate_meta`,
  `forms/sets.py::DjangoFormMutation._validate_meta`), and a hostile form class name fails a valid declaration through
  `forms/inputs.py::resolve_effective_form_fields`. Only a rename after declaration reaches `DjangoMutationField` (the
  `<Name>Payload` ref), `bind_mutation_outputs` and every request (`mutations/resolvers.py::run_write_pipeline_sync`). A
  non-identifier name (`type("Create Item", ...)`) raises a raw `SyntaxError` at `DjangoMutationField`, and
  `"Create-Item"` fails only at schema build. Input and payload names derive from `__name__`, so the answer covers every
  flavor, the auth riders' user-model labels (`auth/mutations.py::derive_register_fields`,
  `_resolve_user_primary_or_raise`, and the eager subject in `mutations/inputs.py::editable_input_fields`) and the GraphQL
  names. The same question covers `FilterSet` / `OrderSet` / `Filter` class names: the `Meta.fields` rejection, the
  related-target owner label, the order-input leaf rejection, the set-class labels in `filters/sets.py` /
  `orders/sets.py` / `utils/inputs.py`, and the `Projected<Filter>` class name
- [ ] 229. Input field names that are Python identifiers but not GraphQL names (`"é"`, a leading `__`, and on Python
  3.10-3.13 NFKC-unnormalized identifiers such as `"ａ"`) pass both mutation flavors' class-creation checks and fail later
  with graphql-core's or the stdlib's raw error. Add a GraphQL-name check on kept input names in both flavors, or keep the
  identifier-only rule?
- [ ] 220. A `Meta.permission_classes` entry whose `__name__` raises is accepted at declaration, then every request raises it
  raw: `mutations/permissions.py::run_permission_classes` computes `owner=permission_class.__name__` before it knows the
  result is a bool (the request user's class name in `DjangoModelPermission.has_permission` likewise), and the conflict
  message in `auth/mutations.py` renders permission-class names raw. Read the label only on the failure branch, reject at
  declaration, or keep?
- [ ] 54. Docs (parked): glossary, a sliced combinator branch on SQLite raises Django's own `DatabaseError`
- [ ] 57. CHANGELOG entry for item 11: model, ModelForm, plain-form and register errors, and a `ValidationError` raised
  during a serializer save, now use the input name (`categoryId`, not `category`)
- [ ] 68. A model's default manager hides rows from declared filter hops but not from undeclared filter hops or ordering. Make them
  agree, or keep?
- [ ] 69. CHANGELOG entry for item 1: `Meta.exclude=["parent"]` on a mutation over a `ForeignObject` model now raises
- [ ] 71. CHANGELOG entry for item 59: two `RelatedFilter`s or `RelatedOrder`s naming one relation now raise at class creation, and a
  longer one (`shelf__branch` beside `shelf`) raises at expansion when the shorter branch's target set reaches `branch`
- [ ] 75. CHANGELOG entry for item 72: a `FilterSet` or `OrderSet` shared by an MTI parent and child type now raises at finalize, and
  a concrete type's path through an FK declared to a proxy (`BranchNote.branch`) reads the bound type, not the proxy's type
- [ ] 76. CHANGELOG entry for item 62: a `SerializerMutation` whose serializer declares a flat `ChoiceField` over a grouped-choices
  column binds again (checked against the column's flattened values); a refused value now reads "which does not list it", and a
  serializer field taking a grouped column's read enum is refused with a remedy to declare a flat `ChoiceField` (over an
  `ArrayField` whose `base_field` is grouped, a `MultipleChoiceField` or `ListField(child=ChoiceField)`)
- [ ] 77. The read enum refuses a grouped-choices column, though group labels are presentation like choice labels. Flatten it on
  the read side too (retires the `str`-override carve-out and the write-side grouped refusal), or keep?
- [ ] 78. CHANGELOG entry for item 65: every single-value lookup on a choice column (`exact`, `iExact`, `contains`, `gt`,
  ...) treats each enum member as a value (`iExact: BLANK`
  matches blank rows only, a `"null"` member matches `"null"`); raw form data and declared `ChoiceFilter`s are unchanged
- [ ] 79. CHANGELOG entry for item 52: connection fields no longer send consumer-source or row-hydration exception text to the
  client; pagination rejections keep their messages and are the new public `PaginationArgumentError`
- [ ] 73. A set subclass used only as a `RelatedFilter` / `RelatedOrder` target, never wired to a type, inherits its base's owner and
  that owner's visibility. Keep, or fall back to the target model's registered type? It also crosses models: an unwired
  `Sub(Base)` on another model reads `Base`'s owner, so its own-pk filter becomes a `GlobalIDFilter` under a relay owner
- [ ] 84. `range: []` applies no constraint on every generated `range` (and `range: [1]` is a validation error), where Django
  raises on both. Make `[]` an arity error like `[1]`, or keep?
- [ ] 85. A nested branch that constrains nothing (`shelves: {}`, `shelves: { condition: { in: null } }`) still keeps only parents
  with a visible child (`_apply_related_constraints`), at the top level and inside `and` / `or` / `not`; strawberry-django treats
  it as no condition. Make it the identity, or keep (and state it in spec-027 Decision 8)?
- [ ] 86. CHANGELOG entry for item 14: an explicit `in: []` on every generated membership lookup matches no rows (integer, text,
  choice, date and every other column type used to return every row); `not: {}` matches every row and `or: [{}, real]` is the real
  arm; a declared `ModelMultipleChoiceFilter` `[]` inside `not` now matches every row; raw `?x__in=` is unchanged
- [ ] 91. CHANGELOG entry for item 43: a serializer `ListField(child=ChoiceField)` publishes a list of the field's generated enum
  (clients send enum names, not strings: `[a]`, `[MEMBER_1]`), and `MultipleChoiceField(allow_blank=True)` accepts `BLANK` as `""`
- [ ] 45. Postgres (run fixing 542): a consumer-declared DRF `ChoiceField` over an `ArrayField` builds (the early
  `_serializer_choice_annotation` branch of `rest_framework/serializer_converter.py::_model_backed_scalar_annotation`)
  and publishes a single-value enum, while `_reject_read_enum_over_grouped_column` says a `ChoiceField` "writes one
  value, never the list the array stores"; with no `validate_<field>` returning a list its save fails with the masked
  error (text column: `DataError` "malformed array literal"; integer column: `ProgrammingError`), as plain DRF answers
  500, and `allow_blank`'s `BLANK` fails the same way even through a `validate_<field>` wrapping only a non-empty
  value. No doc states a serializer `validate_<field>` duty (the form flavor's `clean_<field>` duty is documented, 423
  / 541). Decide: refuse it at build like every other single-value DRF field over an `ArrayField` (46), or keep it and
  document the `validate_<field>` wrap
- [ ] 46. Postgres (run fixing 542): a declared DRF `CharField`, `IntegerField`, `BooleanField`, `JSONField` or
  `ListField(child=<non-choice scalar>)` over an `ArrayField` is refused at build ("Unsupported Django field type
  'ArrayField'": the agreement check in `_model_backed_scalar_annotation` calls `scalar_for_field`, which has no
  `ArrayField` entry), a `source=` rename included; a `ChoiceField`, `MultipleChoiceField` or
  `ListField(child=ChoiceField)` builds (45); decide whether a list-writing `ListField` of a non-choice scalar should
  build
- [ ] 47. Postgres: `serializer_choice_field=MultipleChoiceField` over an `ArrayField` is unusable (parked: needs a Postgres run)
- [ ] 93. CHANGELOG entry for item 44: a ModelForm mutation over a non-text choice column with `blank=True, null=False` answers
  `null` (or an omitted field with no default) with a field-keyed `null` FieldError instead of "An unexpected error occurred."
- [ ] 94. The package's 231 `except BaseException` guards follow two postures: about 90 hostile-metadata guards turn a
  `KeyboardInterrupt` / `SystemExit` into a typed error (pinned, e.g. `serializer_field_description`), while `utils/directives.py`
  and the await-side guards let control signals propagate (pinned the other way). No upstream library converts them at
  configuration time. One policy (re-raise control signals first, or narrow to `Exception`), or keep the split?
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
- [ ] 197. The per-parent visibility paths (`types/resolvers.py::_visible_many_rows`, `_visible_related_object`, relation
  connections, `resolver=`) never narrow the hook's result to the source's rows, so a hook that ignores its input shows other
  parents' rows or the wrong to-one object. Decide the contract (narrow at the five seams, with a live row for an
  input-ignoring hook)
- [ ] 198. Under strictness `"raise"`, a backward keyset page whose hook order cannot anchor a cursor reports the N+1 error
  instead of the keyset error; decide and state it in spec-033 and GLOSSARY
- [ ] 199. A nested keyset window given a cursor minted under a third order calls the target `get_queryset` hook one extra
  time on the error path (same query count and error as before); accept or fix
- [ ] 200. After item 14, a list with one valid member gives the wrong answer in two grid cells; pin the contract, then fix or
  record it
- [ ] 201. C57 choices awaiting your ruling: `schema=` stays optional; under a swap converter four cross-schema cells stay wrong
  (documented); an ambiguous unpublished plain type name now refuses where it was accepted. Accept or change
- [ ] 202. Failability rows that each kill a mutant with one row only: C3+C4 mutants 4, 5, 7 and 8 (8 only by a 30 s timeout),
  C57's rebased run at 1 of 10 entries, three precedence mutants graded weakly pinned. Accept or add rows
- [ ] 203. Fold the implementer notes into START.md: items 14 and 83, C11, C46, C57 and C3+C4 (plan-to-resolver channels key
  by `resolver_key`, never `to_attr`; a nested window under the async view needs an async `DjangoConnectionField` root; a
  harness written against a prototype API fails as a `TypeError` that reads as a regression; a subprocess test that signals
  before its syscall flakes)
- [ ] 204. Dive-3 HIGH (a consumer `Prefetch` hint over a hiding target bypassed its `get_queryset`, fixed as item 13): decide
  disclosure and give SECURITY.md a path for a maintainer-found finding; 0.0.14 is affected (its
  `optimizer/walker.py::_apply_hint` installs the consumer `Prefetch` queryset and marks the relation planned)
- [ ] 205. Upstream Strawberry: interface `resolve_type` looks Node-subclass instances up by raw name, so a converter that
  renames interfaces breaks their GlobalIDs; `ConnectionExtension` runs the resolver before `SliceMetadata` validates
  `first` / `last` (context #4510). File upstream or record as known gaps
- [ ] 206. spec-045 was amended in place with no new card, while card 045 asks a numbered security decision for such changes
- [ ] 207. Earlier open questions with no row: nullable payloads (card 056), and the HUNT negative-offset cursor fix on
  list sources being off by one (the `FieldError.field` name was settled by item 11; items 1 and 51 support a multi-column
  `ForeignObject`, the reverse fallback kept)
- [ ] 216. A dense `RelatedFilter` graph publishes a flat surface factorial in its size (path-relative expansion over every
  simple path: six sets each related to every other give about 11k flat keys per set, seven about 94k); decide a stated
  bound or a per-declaration opt-out of flat copies
- [ ] 217. A subclass of a `FilterSet` in a `RelatedFilter` cycle publishes one lap more than its parent (the cycle closes at
  the parent class, not the subclass); decide whether a subclass should close the cycle at itself
- [ ] 219. Strawberry's own `ListConnection` (0.327.7 and 0.334.4) fails `assert last is not None` when `after + 1 + first`
  equals `sys.maxsize` (its `SliceMetadata` last-only sentinel) and overruns `islice`'s stop past it on an iterator source;
  the package now keeps its pages clear of both. Report it upstream?
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
- [ ] 262. Decide whether a partial `ModelForm` update promises to keep an omitted NULL text column NULL: Django's
  `TextField.formfield` sets no `empty_value=None` (`CharField.formfield` does), so a `title`-only `updateBookViaForm` on a
  book whose `subtitle` (`TextField(blank=True, null=True)`) is NULL writes `''`; spec-038 Decision 8 step 4 says omitted
  scalars are preserved, while the reconstruction binds the stored value and lets the form clean it as a provided one
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
- [ ] 108. A serializer-only source over the default `create()` / `update()` (`gs = PrimaryKeyRelatedField(many=True,
  source="genres_id")`) builds; create raises a masked TypeError and update is a silent no-op. Refuse a column-less
  writable source at class creation, as item 103 does for an `attname` source, or leave it to DRF's default `create()` /
  `update()`?
- [ ] 114. Request-rejection precedence: is the admission-seam rewrite still wanted? It changes only which rejection a
  request past the deadline gets (item 113: `FILTER_INVALID` instead of the deadline rejection), touches about 31 files,
  and D-A / D-B below were never ratified. The design (approved 2026-10-08, all 7 decisions;
  `~/dst-handoff/2026-10-08/admission-design.md`, which also holds the wire-change table and the CHANGELOG text):
  - One order: P0 document admission, P1 field-argument errors, P2 the deadline, P3 the consumer pipeline, P4 slice and database.
    One seam: a new `admission.py` (`admit_connection_page`, `admit_list_page`, `admit_node_refetch`); connections enter it
    through a package `DjangoConnectionExtension(ConnectionExtension)` built with `strawberry.field(extensions=...)`, replacing
    both `relay.connection(` calls (`connection.py`, `types/finalizer.py`). Node fields decode the id before the deadline;
    `first` + `last` keeps `PaginationArgumentError` and its message. Doc home: spec-047 Decision 14, a glossary entry
    "Request rejection precedence", one AGENTS.md line.
  - Draft: `refs/scratch/admission-wip` (`970d054a`), unfinished and never run, cut before many landings; its glossary,
    KANBAN and constants may be half-regenerated. Still to write: `examples/fakeshop/test_query/test_admission_api.py`,
    `tests/test_admission.py`, failability (swap P1 and P2; move admission after `next_`).
  - Watch: reproduce everything `relay.connection()` sets up beyond the extension; never leak the admitted page across parents
    or concurrent async fields; `bounded_rows` / `bounded_rows_async` are public and keep their deadline check; the keyset
    cursor's shape and signature are P1 while the column-fingerprint match stays at the seek; the walker's plan-time catch in
    `optimizer/nested_planner.py`.
  - Text this changes: `8d4f66bd` documents `get_queryset`, `check_*_permission` and consumer `FilterSet` / `OrderSet`
    running before the deadline (connections, `DjangoListField`, the many-side re-check) as trusted application code. Under
    strictness `"raise"` past the deadline a forward FK / OneToOne hop reports the deadline while a many-side hop reports the
    N+1 error (`_check_n1` runs before `bounded_rows`). A generated mutation's transaction opens before the write pipeline's
    check (an audited exclusion in `8d4f66bd`).
  - Open: decision D-A (a deferred pending-source marker instead of the approved `DjangoConnectionExtension` subclass) was
    never ratified and D-B (the keyset rejection class) never chosen; this item's seam text follows the answer. The verified
    31-file implementation of the marker design is on no commit or ref and was not found in scratch; recover or re-create it.
    Also: it adds a second deadline read per parent (about 270 ns on many-side relations, unmeasured); writes check the
    deadline before `coerce_lookup_id`, and this item never names writes; nested resolvers call
    `getattr(root, accessor).all()` before admission, so consumer manager code runs ahead of P1 / P2.
- [ ] 236. One guarded-`isinstance` idiom and one set of hostile test values: `types/base.py` keeps private TypeIs-typed
  `_guarded_isinstance` / `_guarded_issubclass` / `_guarded_narrow`, while `utils/inputs.py`, `filters/sets.py`,
  `sets_mixins.py` and `routers.py` call `exceptions.py::_safe_predicate(isinstance, ...)` and `cast` after it; move the
  typed helpers beside `_safe_predicate` and drop the casts. `tests/_idioms.py::ClassReadRaises` / `ClaimsClass` are
  re-declared locally in `tests/types/test_base.py`, `test_definition_relations.py`, `tests/test_list_field.py`,
  `test_routers.py`, `tests/utils/test_directives.py`, `test_errors.py`, `test_input_values.py` and
  `tests/mutations/test_write_transaction.py`. No defect rides on it (a refactor of private helpers and test idioms): do
  it now, outside a DRY cycle, or leave it to the next DRY cycle?

## Hunt not finished in t3

- [ ] 29. The hunt's final test gate was never run (the Postgres and sharded runs included)
- [ ] 242. Decide removing the dry-0015 worktree, `~/t3code-1cc21548-pre-ff.tgz` and, after item 114 lands,
  `refs/scratch/admission-wip`

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
