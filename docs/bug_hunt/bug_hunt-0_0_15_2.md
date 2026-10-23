# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 216 done, 142 to do.

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
  `TypeError` (Django's `pk` writes the key's column, as plain DRF also fails); `serializer_converter.py::written_model_field`
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

- [ ] 165. Item 12's deadline checks fail forward-FK and one-to-one hops inside a mutation payload (rolling back a write that
  used to commit) and error subscription frames past the budget; spec-047 Decision 9 states both (`8d4f66bd`) but no test
  pins either; the async deadline rows also cannot tell a head check from a check inside the `sync_to_async` closure
- [ ] 166. Fixture gap: the async many-side tests miss a broken prefetch-cache lookup in
  `types/resolvers.py::many_resolver` (gaps (b)-(d) are optional fixture work, not defects: the
  reverse many-to-many without `related_name`, the window resolver-key collision (pinned by a two-root-field row) and
  the C11 hook-order rows (on a test-local schema))
- [ ] 170. No test runs `workspace.py prove` (`scripts/workspace.py::_cmd_prove`); its flow lease and copy lock are pinned only
  through `execute`; add a `main(["prove", ...])` row and a two-run contention row
- [ ] 183. `ruff format` on an explicit `.md` path rewrites its fenced blocks: pyproject's `exclude` does not stop explicit
  paths
- [ ] 185. WebSocket residual after `1b6a09b1`: the Postgres steady-ping lost-write test has never run (Not defects: a
  sync caller blocked in `async_to_sync` keeping the shared connection is documented behaviour, and the async mutation
  window having no owning spec or card breaks no contract row.)
- [ ] 186. docs/README.md has no consumer-`Prefetch` / `.only()` cooperation sentence and no inert-arm sentence (GLOSSARY has
  both: "`only()` cooperation", from item 83's `548059b3`, and "Membership leaves")
- [ ] 187. The C11 keyset fixes were never run on PostgreSQL's LATERAL path (The workspace / prove_failability `flock`
  rows on Linux or NFS are not a defect: CI runs them on ubuntu.)
- [ ] 190. Seen at `87dc1df7`, re-check: an out-of-range datetime filter value raises an uncoded error (The invalid
  regex and the regex on a UUID field are not defects: both follow django-filter's `regex` lookup, which sends a text
  pattern to the database and types a UUID column's value as a UUID.)
- [ ] 231. KANBAN.md's "`FieldError` keying" card (rendered from the kanban DB) still says
  `validation_error_to_field_errors` is an identity pass-through and that no test covers a multi-word snake_case
  field; both are stale (the key maps and `tests/utils/test_error_keys.py` landed before)
- [ ] 255. `docs/SPECS/spec-058-graph_substrate-0_1_1-terms.csv` and
  `docs/SPECS/spec-068-structural_templates-0_1_6-terms.csv` sit beside their archived specs instead of in
  `docs/SPECS/appx/` (the importer and `check_spec_glossary.py` still find them through the sibling lookup)
- [ ] 256. Nothing runs `scripts/check_spec_glossary.py` over every terms CSV (all 57 pass today); its repeated-anchor
  refusal and term / anchor checks bite only when a cycle runs it by hand
- [ ] 302. `scripts/check_spec_glossary.py::auto_link_terms` (the NEXT.md Step 7 `--auto-link` run) protects only
  fenced code and `[label](target)` links and matches a term with no boundary: a spec's first unlinked mention inside a
  code span, a double-backtick span, reference-link text, an autolink, a raw HTML attribute, a bare URL, a heading, or as
  the prefix of a longer identifier (`DjangoListFieldExtra`) gets `[term][glossary-x]` written into it (8 of 8 probed
  shapes). Fix: reuse the KANBAN inliner's CommonMark lexer (`build_kanban_md.py::_protected_regions`, extracted to a
  shared script module then), add block exclusions (headings, link-definition block, fenced and indented code) and the
  term boundary
- [ ] 305. A ModelForm `MultipleChoiceField` declared over a single-value column that lists no choices (`description =
  MultipleChoiceField(...)` over a `TextField`) builds as `description: String!` and every create and update fails with
  "Enter a list of values.": `forms/inputs.py::_form_choice_narrowing` returns before its list-over-single-value refusal
  when the column lists no choices; the serializer twin is unchecked on purpose (spec-039), so say whether the form
  flavor refuses at build or types the field as a list
- [ ] 307. Leftovers from 284 / 142 (`ca9273d3`, landed on the implementer's evidence: the FIX-round delta for F1 job
  control, F2 the late stop, F3 gate's sync holding and F5 the docs had no second verifier pass, by the maintainer's
  call): a Ctrl-Z landing between `Popen` returning and `_StopRelay.started` stops only the wrapper, and the command
  runs on until `fg`; `_JobControl.suspend`'s SIGCONT to the group and the SIGCONT route overlap (only the
  sigcont-ignored row tells them apart); the D10, gate, F2 and F3 mutations are each pinned by one row; F4's optional
  `dup2` of `/dev/null` onto a dropped output sink's fd (accepted without it: `| head` ends with rc 120 and a complete
  log). Re-verify the delta and decide each, or close them as robustness rows
- [ ] 312. `utils/querysets.py::_node_metadata_defect` still refuses `RawSQL(<TextChoices member>, params)` (the SQL
  text slot read by exact type), which Django serves; the 272 text-term predicate covers order / extra / where slots but
  not `RawSQL.sql`. Found landing 294
- [ ] 313. Unprobed: a database router whose `db_for_read` returns a `StrEnum` alias may be refused by
  `utils/querysets.py::_snapshot_routing_intent` (exact-type read of the routed alias) after 294 normalized
  `using(<member>)`; probe it live and seal by `is_str` plus normalization if so. Found landing 294
- [ ] 314. Under 272's raw-param leaf rule a model instance in `extra(where=..., params=[obj])` now passes the
  visibility seal and fails in the database adapter ("Error binding parameter") instead of the typed
  `ConfigurationError`; Django fails the same way, so decide whether the seal should keep refusing non-adaptable leaves
  with its own message. Found landing 294
- [ ] 318. `tests/filters/test_sets.py::test_an_unordered_meta_fields_expands_in_canonical_order[set of lookups in a
  dict]` fails under `PYTHONHASHSEED=28` ("no set over ('exact', 'icontains', 'istartswith', 'iendswith') iterates out
  of canonical order"): its `_scrambled` helper cannot build an out-of-order set for every seed, so the row flakes with
  the hash seed (seen at `feb83d59` and `144a64ee`; the code under test is not involved). Robustness row (test harness).
  Found verifying 269
- [ ] 319. Unprobed cause: a child `GlobalIDFilter` subclass whose own `filter` binds the raw value
  (`qs.filter(title=value)`), reached through a `RelatedFilter`, answers `"plain"` with a matching parent flat
  (`books__gid`) and no row nested (`books: {gid: ...}`), before 269 and after it alike, against README's "the two
  spellings agree on every lookup except `isNull: true` and `exclude=True`". Found verifying 269
- [ ] 323. Inside a `get_queryset` hook, `apply_cascade_permissions(cls, queryset, info)` returns a plain `QuerySet`
  even when handed the project `QuerySet` class the hook receives (the cascade seals its source with the recomposing
  policy), so a project method chained after the cascade raises `AttributeError`; README says the cascade returns "a
  queryset of the same model and row type it was given". Decide whether the cascade's output keeps the class, or the
  docs say it does not
- [ ] 324. `tests/utils/test_querysets.py::test_additive_only_subclass_result_is_sealed_to_plain_queryset`'s docstring
  carries process provenance ("now", "The old contract"); restate it as behaviour
- [ ] 326. A Django `ValidationError` raised at save time about the primary key of a serializer field written through
  `source="pk"` (`key = IntegerField(source="pk")` over `Item`, a model `save()` calling `full_clean()` and raising
  `{"id": [...]}`) is keyed `id`, a name no input exposes, instead of the renamed `key` input:
  `utils/errors.py::save_time_error_key_map` reads the spec's source through `model._meta.get_field`, which rejects
  `"pk"` (`FieldDoesNotExist` keeps the spelling), while `rest_framework/serializer_converter.py::written_model_field`
  and `rest_framework/inputs.py::write_source_key` already resolve `"pk"` to the key column. Probed: a create answers
  `("id", [...])`; `source="category"` answers the wire name. Contract row: the `save_time_error_key_map` docstring and
  docs/README (an error raised on the model field behind a `source=` arrives under the renamed input). Fix: resolve the
  spec source through `written_model_field` in `model_names`, with a package row beside
  `test_save_time_django_validation_error_uses_source_aware_wire_name`; a scalar `source="pk"` on a text key
  (`Edition.isbn_13`) takes the same row
- [ ] 327. Relay refetch plans nothing: `types/relay.py::_resolve_nodes_default` / `_resolve_node_default` return model
  instances, `optimizer/extension.py::DjangoOptimizerExtension._optimize` passes a non-`QuerySet` through unchanged and
  `relay.py::DjangoNodesField` / `DjangoNodeField` never call `DjangoOptimizerExtension.apply_to`, so every nested
  relation under `node(id:)` / `nodes(ids:)` lazy-loads per parent: `nodes(ids: [b1..bN]) { ... on BookType { loans { id
  } } }` is 1 + N statements (same for `loansConnection`, `genresConnection`; a forward `shelf` costs 1 + 2N) against 2
  under `allLibraryBooks` or a root connection, the root SELECT is unprojected, and under `strictness="raise"` every
  nested relation under `node` / `nodes` raises `Unplanned N+1`. A documented limit (spec-015 Decision 3 "not wired ...
  the seam stays open"; glossary "Relay Node integration"; pinned by
  `test_library_api.py::_LOAN_QUERYSET_METHOD_HOOK_CASES`), but GOAL.md's `astronomy` paragraph (`strictness="raise"`
  with `DjangoNodeField` roots) cannot run as written and no board card owns it. Fix shape if taken: plan the per-type
  queryset before `list()` through the connection field's plan application, re-order over it, and rewrite spec-015
  Decision 3, the glossary sentence and the pinned statement counts (card candidate)
- [ ] 328. The serializer floor is never run: `pyproject.toml` pins `djangorestframework>=3.17.0`
  (`utils/imports.py::DRF_FLOOR`, spec-039 Decision 12) but `docs/builder/BUILD.md` "Floor verification" and the CI
  floor cell (`django.yml`, `compatibility_only`) install only Django and strawberry-graphql at the floor, so every
  floor run resolves the locked DRF. Probed with `djangorestframework==3.17.0`, Python 3.10.19, Django 5.2.16,
  strawberry-graphql 0.322.2: `tests/rest_framework` 782 passed, so nothing is broken today. Check: add the DRF floor
  point to the BUILD.md recipe and the floor cell, or state in both that the soft dependency's floor is unexercised
- [ ] 329. `scripts/prove_failability.py` forwards the first stop signal to the scope's whole process group, which holds
  `uv` as well as pytest, so `uv run` hands pytest the Ctrl-C a second time and a `-n 0` scope whose teardown takes
  longer than about 0.2 s loses it, while the module docstring says the forwarded signal "lets pytest tear down".
  Decide: signal the group leader on the first stop and keep `killpg(SIGKILL)` for the escalation
  (`scripts/_stop_signals.py::signal_group`, `scripts/prove_failability.py::_request_stop`), or qualify the docstring.
  Robustness row (pytest-django recreates a leftover test database)
- [ ] 330. `scripts/prove_failability.py::_resolve_scratch_root` names the default scratch parent `<system temporary
  directory>/failability` for every user, and `_claim_private_directory` refuses a directory another user owns, so on a
  shared Linux `/tmp` the first user to run the tool owns the name and every default run of a second user is refused
  (only the owner can remove it). macOS's per-user `TMPDIR` is unaffected and an explicit `--scratch-root` always works.
  Name the parent per user (`failability-<uid>`) or fall back to a private parent when the shared one is foreign; keep
  the owner / symlink refusal. Check on Linux (read from the code, unprobed)
- [ ] 331. `scripts/workspace.py::ensure_floor_venv` decides reuse with `python.exists() and key_path.is_file() and
  key_path.read_text(...) == key`, a check followed by a separate read, the shape item 145 removed from
  `_read_json_object` / `load_runs`; the macOS `$TMPDIR` purge can unlink the key between the two calls, which raises
  `FileNotFoundError` out of `gate` instead of reading as "no key, rebuild". Robustness row (a two-statement window):
  read through `_read_text_if_present`; family of items 143, 145 and 301
- [ ] 332. `scripts/workspace.py::_remove_flow_dir` removes the marker with `marker.rmdir()` and no handling: a
  non-empty `.dsf-ws` directory (a stray `.DS_Store`) makes `gc` raise a raw `OSError` (Errno 66) after emptying the
  rest of the flow, leaving only the marker, and every rerun fails the same way. Robustness row (nothing in the script
  writes there): refuse with a `WorkspaceError` naming the contents, or remove them
- [ ] 345. `workspace.py`'s `state.json` is a regular file the macOS `$TMPDIR` purge removes once its birth and access
  times pass 3 days (`_write_json` replaces it, so each write renews it): a command holding its copy past 3 days with
  no state write in between loses every binding of the flow while the copy's lock (a directory since 301) survives.
  Robustness row, not a defect under rule 37 (the module docstring documents the purge for idle stretches and asks for
  `gc` after one); found implementing 301
- [ ] 346. Git calls outside `scripts/workspace.py` still read the caller's global and system config and the XDG ignore
  and attributes files, unlike `workspace.py::_git`'s `REPOSITORY_CONFIG_ONLY`:
  `check_trailing_commas.py::git_visible_scope`, `review_plan.py::_untracked_python` and `::_worktree_blobs`, the
  `status --short` baselines (`_plan_common.py::git_status_short`, `bug_hunt.py`, `review_plan.py`; a global
  `status.showUntrackedFiles=no` empties the concurrent-work baseline), `review_inspect.py::_blob_id` (`hash-object`
  applies a global `core.autocrlf`), `check_type_suppressions.py::tracked_python_files` (`core.quotePath`) and
  `review_historical_package_snapshot_at_commit.py::_run_git`; the review diff script's `--list` mode
  (`_dirty_python_files`) also rewrites the shared `.git/index` through `git status`. Robustness row: no caller config
  in this repo changes a result today. Fix shape: route them through one shared isolated runner
- [ ] 347. `workspace.py::item_diff` applies no `is_excluded`, so a pre-existing untracked file under `temp-tests/`,
  `worker-memory/` or a `*-ws` folder shows as the item's addition when the diff scope covers it (the `-- .`
  interrupted-diff command in `docs/review/worker-0.md`), and a tracked file `is_excluded` drops from the copy keeps its
  parent blob in `snapshot_commit`'s tree (0 such tracked files today). Robustness row
- [ ] 348. Under `REPOSITORY_CONFIG_ONLY`, git reads `safe.directory` only from global or system config, so
  `workspace.py` refuses a checkout owned by another user that the caller's global config had marked safe. Robustness
  row (not this setup)
- [ ] 349. `workspace.py audit <missing file>` exits by a `FileNotFoundError` traceback instead of a refusal. Robustness
  row
- [ ] 353. Relay `nodes(ids:)` loses `FETCH_PEERS` batching after 343: `relay.py::_stamp_node_type` `copy.copy`s each
  resolved node and Django's `ModelState.__getstate__` drops `peers`, so a lazy FK across 3 loans costs 3 queries
  instead of 1 (`FETCH_RAISE` is carried). Found landing 343
- [ ] 372. A declared package `RangeFilter` with both bounds on an integer column passes an out-of-int64 bound to
  `BETWEEN` and the backend raises a masked `OverflowError` (`range: {start: "0", end: "18446744073709551616"}` on a
  BigInt column); `filters/base.py::IntegerRangeFilter` decomposes into `gte` + `lte`, the declared primitive does not
- [ ] 375. A package `RangeFilter` / `ListFilter` over a relation column passes its bounds / elements to the ORM
  uncleaned (django-filter's `exact` for a relation is a `ModelChoiceFilter`, whose clean would be an existence oracle
  past the target's `get_queryset`), so a NaN bound on a Decimal-pk target still raises a masked error; candidate owner:
  the relation identity column's form field with the matches-nothing semantics of `_coerce_relation_identity`. A range
  on an FK column fails the schema build (`scalar_for_field`), so the reach is form data / `apply_sync` only: check it
  under AGENTS rule 37 first
- [ ] 376. A package `RangeFilter` / `ListFilter` under a plain `django_filters.FilterSet` (no package FilterSet parent,
  e.g. the DRF backend path) cleans nothing; check the reach under AGENTS rule 37 first
- [ ] 373. `django_filters.LookupChoiceFilter` publishes a bare scalar input, so django-filter's `lookup_required`
  refuses every request (`FILTER_INVALID` "Select a lookup."); its input needs a value + lookup pair. Feature card, not
  a defect
- [ ] 374. `django_filters.NumericRangeFilter` on a non-range column publishes a bare `exact` and silently ignores the
  value (all rows answered). Robustness row: PostgreSQL range columns are unsupported

## To do: holes found re-checking the fixes


## Waiting on you

- [ ] 352. CHANGELOG entry for item 343: on Django 6.1, a `get_queryset` hook or default manager returning
  `.fetch_mode(FETCH_PEERS)` or `.fetch_mode(FETCH_RAISE)` keeps that mode through the visibility seal (root lists,
  connections, nested relations, prefetch children, `node(id:)`, the mutation locate), so lazy loads batch or raise as
  the project set; a fetch mode object other than Django's three is refused as an unsealable queryset
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
- [ ] 316. `filters/base.py::RangeFilter` declared with the default `lookup_expr` (`exact`) raises a raw
  `ValidationError` for a two-bound range (`price__exact=[a, b]`), while a one-sided range now works through `__gte` /
  `__lte`; nothing validates the declaration. Default `lookup_expr` to `range` (django-filter's `RangeFilter` ignores
  the declared lookup), or refuse a non-`range` lookup with `ConfigurationError` at class build?
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
- [ ] 53. Docs (parked): docs/README.md, the async paragraph under `DjangoListField`:
  a hand-written `@strawberry.field` returning a QuerySet runs synchronously
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
- [ ] 45. Postgres: plain `ChoiceField` over an `ArrayField` builds, then the save fails (parked: needs a Postgres run)
- [ ] 46. Postgres: a declared `ListField(child=<non-choice scalar>)` over an `ArrayField` is refused at build ("Unsupported
  Django field type 'ArrayField'": the agreement check in `_model_backed_scalar_annotation` calls `scalar_for_field`, which
  has no `ArrayField` entry); a `ChoiceField` child builds (parked: needs a Postgres run)
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
- [ ] 196. CHANGELOG entries for items 6 (combined querysets served as their pk set), 12 (the deadline message reads "before
  this field reached the database"; login, logout, me and `relay.node()` reject past the deadline), 50 and 83 (planned
  `.only()` writers no longer drop selected columns), 74 (a consumer `select_related` the selection never reads no
  longer errors), 15 (a hand-built range filter value that is not a `start` / `end` mapping or input object raises
  `ConfigurationError` instead of filtering nothing), 16 (a form field basis value whose `__class__` raises is reported
  as an invalid field in `ConfigurationError`) and 17 (`register_mutation()` names a protected field declared as a `str`
  subclass by its value; `DjangoMutationField` refuses a class drained by `registry.clear()` even when it compares equal
  to its redeclaration) and 18 (`OptimizerHint` prefetch and strategy values, `nested_connection_strategy=`,
  `NESTED_CONNECTION_STRATEGY` and `strictness=` values whose `__class__` raises or claims `str`, and lazy proxies of a
  strategy or strictness name, raise the typed error instead of a raw `RuntimeError` / `TypeError`) and 19 (a kept
  serializer input field named by a non-identifier or a keyword is refused at class creation instead of a raw `SyntaxError`
  at finalize; serializer hook values whose `__class__` raises are typed; lazy proxies and `__class__` spoofs in hook data
  fail the frozen view closed; a non-`str` `context["write_alias"]` is a conflict) and 21-23 (field targets, factory
  returns, `Meta` values, set `Meta.fields`, input and policy helpers whose `__class__` raises or claims a type now raise
  the typed error instead of a raw `RuntimeError` / `TypeError`; `Meta.name` / `Meta.description`, a string-helper input
  and a `SESSION_ENGINE` that is a lazy proxy of a `str` are typed rejections; a lazy proxy of a class as a field target
  now reads "requires a DjangoType class") and 221 (`register_mutation()` refuses a protected field declared as a `str`
  subclass whatever its `__eq__`, and a `REQUIRED_FIELDS` that is not a list or tuple or holds a non-string entry, with a
  `ConfigurationError` naming the model instead of a raw `TypeError` / consumer exception)
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
- [ ] 135. A malformed GlobalID in a relation input, single (`categoryId: "not-base64!!"`) or an `[ID!]` element
  (`genres: ["not-base64!!"]`), is a masked top-level error with `data: null` in the model, ModelForm and serializer
  flavors: Strawberry raises `GlobalIDValueError` at the mutation resolver before any package decode, so the field-keyed
  envelope (which a well-formed but missing, wrong-type or hidden id gets) never applies;
  `test_products_api.py::test_create_item_malformed_category_id_is_top_level_coercion_error` pins the outcome but its
  docstring says variable coercion. Return the field-keyed `FieldError` (spec-036 says a malformed relation id surfaces a
  `FieldError` on the field), or keep the top-level error and correct spec-036 and that docstring? Item 191 (a
  committed sibling mutation beside `data: null`) follows the answer
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
