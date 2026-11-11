# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 490 done, 117 to do. The CHANGELOG entries filed here moved to
[`CHANGELOGTODO.md`][changelogtodo], numbers kept.

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
- [x] 18. `optimizer/` robustness rows (not defects, no wire input): a hostile `__class__` on a `prefetch_obj`,
  strategy selection or `strictness=` value (the `NESTED_CONNECTION_STRATEGY` setting included) escaped
  `_require_prefetch` / `resolve_strategy` / `_is_valid_strictness` raw against their typed-error promises. Now a
  guarded `isinstance` and real-type tests (`utils/_narrowing.py::is_str`, `is_class`) (`f788edcf`);
  `unwindowable_child_queryset_reason` needs no code.
- [x] 19. `rest_framework/` robustness rows (not defects, no wire input): hostile `__class__` / `__repr__` values in
  field maps, `nested_fields`, hook returns, `write_alias` and `save()` returns escaped raw, the frozen hook view
  passed spoofs by reference, and a non-identifier kept serializer field raised an unnamed `SyntaxError` at finalize.
  Now guarded `isinstance`, real-type reads, the guarded repr, and kept names checked at class creation (`5cbe15de`).
  The raw `__name__` labels (item 26's) and `_error_node_children` need no code.
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
- [x] 22. `types/` robustness rows (not defects, no wire input): a `Meta` value whose `__class__` raised or claimed a
  type, a class attribute shadowing a model field, a hostile annotation key and a non-string `resolve_id_attr` result
  escaped raw against typed-error promises. Each gate is now a guarded `isinstance` (lazy proxies pass), `Meta.name` /
  `Meta.description` and annotation keys ask the real type, and the `resolve_id_attr` result is normalized inside its
  fail-closed guard.
- [x] 23. `utils/` robustness rows (not defects, no wire input): a `Meta.fields` whose `__class__` raised now gets the
  typed re-readable rejection (`canonicalize_set_meta_fields`, `FilterSet.get_fields`,
  `is_re_readable_field_declaration`), and `normalize_field_name_sequence`, the string helpers, `resolve_policy` and
  the other listed helpers keep their typed outcome for a hostile value. The dynamic-set-class rows were stale (code
  deleted in `899cb35b`); the `__name__` labels need no code.
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
- [x] 90. Not a defect under rule 37 (no contract row): nested list-of-choice serializer shapes
  (`ListField(child=MultipleChoiceField)`, `ListField(child=ListField(child=ChoiceField))`) publish `[[String!]!]` by
  spec-039's one-level peel (`serializer_choice_source`); DRF checks every leaf with a field-keyed error and over a
  column they are refused at build; no code. Found probing it: items 151-154.
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
- [x] 66. The composite-index advisory named child-table indexes on columns the child's table does not hold (an MTI
  child ordered by an inherited column; a generic link whose content type sits on the parent), which Django refuses
  (models.E016). It now resolves every column as the window does (`Query.resolve_ref`, base table only) and stays
  silent when one lives off the child's table; `pk` orders now advise. CHANGELOG item 233; filed 234, 235.
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
- [x] 92. A Django `ValidationError` raised at save time (consumer `save()` / `delete()`, signals, `ModelForm.save()`,
  `perform_mutate`) was a masked top-level error on the model, ModelForm, plain-form and register flavors; every
  flavor now returns the `FieldError` envelope keyed like `full_clean()`, rolled back, through
  `mutations/resolvers.py::save_or_field_errors`; a `ValueError` still propagates. CHANGELOG item 232; filed 230, 231.
- [x] 97. `isnull` on a relation key django-filter's table does not name (a forward `ForeignObject`, its reverse, a
  `GenericRelation`) raised "unrecognized field type" at class creation;
  `filters/sets.py::FilterSet.filter_for_lookup` now replays upstream's isnull branch for those keys
  (`_null_test_filter_for_relation`), so every relation key's `isNull` is a Boolean null test as on a `ForeignKey`.
  Live row: fakeshop `ShelfLabelFilter` via `allLibraryShelfLabelsFiltered`; CHANGELOG item 240; filed 239.
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
- [x] 222. Class membership over class objects is now an identity scan wherever a consumer metaclass reaches it
  (`TypeRegistry.register` / `_detach_type_from_model`, `FilterSet._filters_along`, `apply_interfaces` and others), so
  a lying or raising metaclass `__eq__` no longer drops or removes the wrong type, truncates a filter path, reports a
  false cycle or escapes raw. Docs: specs 001, 015, 018, 027, 034, 039, 040 (before Python 3.12 `inspect` still
  compares by equality).
- [x] 244. A lone surrogate in a raw relation id over a text-pk target (`editionId: "\ud800"`, a `boundWith` member) or
  in an update / delete `id` over a text-pk non-Relay primary escaped as the masked "An unexpected error occurred." in the
  model, form and serializer flavors (the text preflight ran on scalar leaves only): `type_check_relation_id` and
  `coerce_lookup_id` now run it on the coerced pk before any query, keyed `editionId`, `boundWith.<i>` or `id`, `invalid`;
  well-formed non-ASCII ids still write; fakeshop gains `Printing.bound_with` and the Printing / Edition write mutations
  that reach it; specs 038 and 039 say so
- [x] 224. A `str`-subclass value (a `StrEnum` member, one whose `__eq__` lies or raises) is read as its text:
  `DjangoOptimizerExtension(strictness=)` stores the vocabulary's own constant, so a lying `__eq__` no longer disarms
  the N+1 guard, and `FilterSet` / `OrderSet` `Meta.fields` and `Meta.exclude` read through
  `utils/inputs.py::plain_set_meta_fields`, so the spelled field is filtered, ordered or excluded. Docs: specs 027,
  028.
- [x] 100. A random order on a nested connection's target (`"?"` or `Random()`) went into the optimizer window, which
  evaluates the order up to three times: `"?"` lost the root field to a masked error and `Random()` served wrong
  cursors and pageInfo. `optimizer/plans.py::has_random_term` now leaves such a relation to the per-parent pipeline
  (strictness-visible). Docs: spec-033.
- [x] 101. `manage.py import_spec_terms --check` was red: spec sweeps rewrote terms CSVs without the writing importer
  (14 extra / 5 missing rows on 8 done cards, 119 order shifts, 462 stale `notes`), and `--check` compared anchors only,
  stopped at the first card and missed orphans; it now passes exactly when the writing run writes nothing (every
  written column, every card and planning error in one run, orphan mentions reaped, no restamp of unchanged rows), a
  pre-commit hook and the CI lint step run it, `check_spec_glossary.py` refuses a repeated anchor, the DB is re-synced
  and card 056 / 053 board text it falsified is corrected
- [x] 107. `DjangoModelFormMutation` and `SerializerMutation` published the model's primary key on the update input
  (another row's key wrote that row), while `DjangoMutation` dropped every key on create (a text-key create committed
  `""`). An update input now never carries the pk (update `fields` naming it raises at class creation), a model create
  takes a client-assigned key under the default / `db_default` rule, and `build_form_inputs` is gone. Docs: specs 036,
  038, 039.
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
- [x] 175. spec-050 Decision 9 saying only "a positive offset raises the low mark": not a defect: incomplete, not
  false (row 21, fixed in `4a736809`, states the high mark)
- [x] 176. Async nested connection under a `DjangoListField` root leaving a coroutine: already fixed: not reproducible
  at `43208c0c` on either schema, optimizer on and off
- [x] 177. The test clients refusing a nested non-dict `Mapping` in `variables`: not a defect (upstream-matching): the
  variables go through `json.dumps`, which refuses it as upstream test clients do
- [x] 179. Test strength (the concurrent ledger lock row of `dfc32247`, the optimizer governance gate's `typing.cast`
  blind spot of `40a0fb96`, a mocked `fcntl.flock` row): not a defect: no contract row; test-quality notes only
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
- [x] 252. fixed: a nested connection ordered by a relation name windowed on the key column while the pipeline
  compiled the related model's `Meta.ordering`; `utils/querysets.py::expand_relation_order` now gives the window,
  reversed window, lateral map, random arm, projection and index advisory the order Django's compiler runs. A related
  `Random()` goes per parent; a multi-column `ForeignObject` name windows on its carrier columns; keyset still refuses
  a relation name.
- [x] 259. fixed: a `RelatedFilter` flat copy was deferred when its form field cleaned an absent key to a value that
  filters (a `clean` returning a default, a nonempty `empty_value`), so the parent connection dropped the constraint.
  `filters/sets.py::_absence_filters_nothing` now defers only after `_absent_cleaned_value` and `_filter_skips` prove
  the absent value is skipped; the shipped schema's deferred set is unchanged.
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
- [x] 274. fixed: a create naming a client-assigned pk with no `default` / `db_default` saved through Django's
  UPDATE-then-INSERT, so a concurrently committed row under that key was overwritten and reported as created.
  `mutations/resolvers.py::save_new_row` saves with `force_insert=(Model,)` when `adds_by_update_first` says Django
  would UPDATE, so the race is the `__all__` `constraint` envelope; the ModelForm flavor splits the save as Django's
  admin does.
- [x] 120. `prove_failability.py` had no SIGTERM / SIGHUP handler: a terminated run left its mutation in the tree and
  its `ACTIVE-MUTATION.json` marker, and a signal to the run alone orphaned the pytest scope: fixed, `main` routes
  SIGINT / SIGTERM / SIGHUP / SIGQUIT (an inherited `SIG_IGN` stays ignored) to a handler that records the stop and
  forwards it to the scope, now in its own session (a repeat after `STOP_REPEAT_GRACE` kills the group); the run then
  restores and proves the tree through the existing `finally`, writes no record and exits `128 + N` (a direct script
  run dies by the signal); only `SIGKILL` or an interpreter crash still leaves the marker and `restore_with`
- [x] 282. fixed: an update whose located row a concurrent transaction deleted (`Meta.select_for_update = False`, or
  no `FOR UPDATE`) was re-inserted and reported as updated (ModelForm; multi-table model) or a masked
  `ConfigurationError` (serializer). `mutations/resolvers.py::save_located_row` saves with `force_update=True` plus
  per-table `update_fields`, and every flavor returns the in-band `conflict` envelope on `id`, rolled back; fakeshop
  gains three `UpdateLendingDesk` flavors.
- [x] 121. fixed: a crashed `prove_failability.py` run left its `ACTIVE-MUTATION.json` marker where no later run
  looked, so a rerun copied mutated bytes as pristine. The crash state now lives in one per-tree 0700 state directory
  under `$XDG_STATE_HOME` or `~/.local/state`, checked by every run under the tree lock; default scratch is
  `failability/tree-<digest>` under the system temporary directory.
- [x] 123. BUILD.md "Mechanized: `scripts/prove_failability.py`" called the tool's default scratch "a bare `/tmp` path":
  fixed with 121, it names `failability/tree-<digest>` under the system temporary directory and the state directory
- [x] 132. fixed: a `SerializerMutation` whose `Meta.fields` narrowing keeps a relation to a Relay-Node type (e.g.
  `Shelf.branch`) failed schema build, because the `data:` reference's name was derived before finalization made the
  target a node. It now names the mutation's own `<Mutation>Data` slot
  (`rest_framework/inputs.py::serializer_input_slot`), so a target may be declared after the root `Mutation`; type
  names unchanged; fakeshop gains `updatePatronProfileGenreViaSerializer`.
- [x] 285. fixed: an update or delete whose located row was deleted concurrently after authorization answered a
  misleading field error, or a masked `DoesNotExist` from DRF's `UniqueTogetherValidator`.
  `mutations/resolvers.py::run_write_pipeline_sync` probes the row only when its step fails
  (`utils/write_transaction.py::located_row_vanished`) and answers the `conflict` envelope on `id`; a success runs no
  extra query. A stale omitted key after a concurrent `SET_NULL` stays out of scope.
- [x] 133. fixed: a relation id into a non-Relay or unregistered target whose pk is itself a key (one-to-one pk, MTI
  parent link, `ForeignKey(primary_key=True)`, a `to_field` key) was refused in every write flavor, and an
  out-of-range id was a masked `OverflowError`. `utils/relations.py::stored_value_column` follows a key to its storing
  column, `mutations/inputs.py::relation_id_scalar` types from it and `utils/querysets.py::coerce_field_value_or_none`
  validates; fakeshop gains `KioskFault`.
- [x] 137. fixed: the ModelForm and serializer flavors stored `NULL` for a relation id naming a row whose `to_field`
  key is `NULL` (the model flavor refused it since item 130), and `forms/resolvers.py::_to_form_key_value` fell back
  to `obj.pk`. `utils/querysets.py::linkable_rows` drops `NULL`-key rows at every visible-relation read, so those are
  the relation error; a non-`pk`, non-concrete `to_field_name` is a build `ConfigurationError` (the other half fixed
  by item 266).
- [x] 143. The `.dsf-ws` marker was a regular file written once and only `.exists()`-checked, so its atime never moved
  and the macOS daily `$TMPDIR` purge (regular files whose atime is over 3 days old; directories never removed) deleted
  it 3 days after the flow's first command: `gc` then refused the flow, `release` freed nothing while `state.json` kept
  the bindings, and `status` dropped the flow: fixed, the marker is an empty directory, `Layout.ensure_marked` turns a
  marker file into it under `pool.lock` (re-checking inside the lock), and `_remove_flow_dir` removes it last with
  `rmdir` or `unlink`; `gc` still refuses an unmarked folder (13-row grid: 7/13 at the parent, 13/13 after)
- [x] 147. fixed: `scripts/build_kanban_md.py::GlossaryInliner._protected` lexed only single-backtick code spans, so a
  glossary link could land inside autolinks, raw HTML, multi-backtick spans or bare URLs (latent; `09d0caa0` never
  lexed double-backtick spans). `_protected_regions` now masks escapes, backtick runs, autolinks and CommonMark raw
  HTML in one pass before bracket pairing; KANBAN.md renders byte-identical.
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
- [x] 284. fixed: `workspace.py run` / `prove` (`::stream`) ran the command in the wrapper's process group and
  forwarded no signal, so a stop signal to the wrapper's pid left pytest or the prover running without its lease. The
  command now runs in its own session and the wrapper relays each stop signal to its group
  (`scripts/_stop_signals.py`, shared with `prove_failability.py`); the run record adds `stopped_by` and the wrapper
  exits `128 + N`.
- [x] 296. `tests/test_workspace.py::test_the_lint_gate_suite_runs_the_ci_lint_job_commands_in_order` failed on main:
  `9a97127c` made CI's lint job run `scripts/check_citations.py --check --substrings` while the `gate` lint suite still
  ran `--check`: fixed in `8e191ea3`, `scripts/workspace.py #"LINT_COMMANDS"` runs `--check --substrings` as CI does
- [x] 249. fixed: a set-shaped `FilterSet` `Meta.fields` expanded in hash order, so `base_filters` and the generated
  inputs moved with `PYTHONHASHSEED`; `filters/sets.py::FilterSet.get_fields` reorders by
  `utils/inputs.py::canonicalize_set_meta_fields` (`canonical_sort_key` order) without rewriting the declaration, and
  a list / tuple / dict keeps its order. The OrderSet twin's pin now fails without canonicalization.
- [x] 234. The index advisory on a proxy target (or a proxy of a proxy) read the proxy's own empty `Meta.indexes` /
  `Meta.constraints` / `unique_together`, recommended an index the concrete model already declares, named the proxy
  (where `models.E016` forbids declaring it) and deduplicated under the proxy's label: fixed,
  `optimizer/nested_planner.py::_advise_composite_index` reads the table-owning `_meta.concrete_model` once and feeds it
  to the window columns, the order terms, the coverage check, the dedup key and the message, so a covered proxy is
  silent and an uncovered one warns once naming the concrete model; a non-proxy model is unchanged
- [x] 241. fixed: duplicate input-object field names escaped the value budget, since `charge_arguments` charged a dict
  that dropped earlier same-named subtrees. `extensions/resource_policy.py::_DocumentWalk` now charges each argument
  as its AST (`_ValueBudget._charge_container` counts every spelled field), variable defaults included, so a
  duplicate-name document over a bound gets the resource rejection; no new bound, code or message.
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
- [x] 291. fixed: a ModelForm whose bound relation field disagreed with the class-level field the decode reads (an
  `__init__` / `get_form` changing `to_field_name` or swapping the queryset's model) was bound unchecked and linked a
  hidden or wrong-model row. `forms/resolvers.py::_assert_bound_choice_agreement` runs between `get_form()` and
  `is_valid()` and raises `ConfigurationError` on a model or key mismatch.
- [x] 292. A relation `to_field_name` naming a concrete non-unique column passed the build guard and then raised
  `MultipleObjectsReturned` (single) or linked every row with the key, a hidden one included (many-to-many): fixed with
  291, `forms/inputs.py::require_readable_choice_keys` requires `pk` or a column unique on its own (`unique=True`, a
  one-field `unique_together`, or an unconditional one-field `UniqueConstraint`), Django's fields.E311 rule; the guard's
  tests moved to unique columns (Branch.name, MembershipCard.patron) and Book.title / shelf are refusal rows
- [x] 254. Not a code defect: the fingerprint guards only the recorded axes of a nondeterministic
  `get_serializer_for_schema()` hook, so a drift on an unrecorded axis builds a self-consistent input instead of
  failing loud (item 154's "fails loud" holds for recorded axes only). "EVERY axis" retracted in
  `rest_framework/inputs.py::serializer_schema_fingerprint`, `rest_framework/sets.py::_checked_schema_field_map` and
  spec-039; code digest unchanged.
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
  `Meta.cursor_field` (spec-030); the same future-work claim is gone from spec-010, spec-032,
  `test_library_api.py::test_stale_after_cursor_no_error`'s docstring and the board (re-rendered). Docs and board
  only; no executable line changes.
- [x] 155. Already fixed by `a9e7963d`: none of the nine sentences names `0.324.0` any more; specs 030, 031, 032 and the
  spec-030 / spec-032 rationale companions now carry no locked Strawberry version literal (0 hits under `docs/SPECS/`
  and `docs/spec-*.md`). The citation-gate rule the item left open stays unbuilt.
- [x] 235. Already fixed by `9a97127c`: both `optimizer/nested_planner.py` comments now state the invariant without the
  "P2-3" review label ("covering the general page;", "naming a duplicated column."); 0 hits for `P2-3` in the file.
- [x] 269. fixed: a filter holding its own `filter` (a `Filter` subclass storing `self.filter`) raised `FieldError` on
  every walked path and was negated twice under `exclude=True`, because `filters/sets.py` tested `method`.
  `sets.py::_own_filter` now replaces that test in `_owner_bound_child`, `FilterSet._flat_leaf_walk`,
  `FilterSet._apply_active_leaf` and `_decodes_before_binding`. Live rows on `BookFilter.title_starts`; mutations
  M1-M7 red.
- [x] 290. fixed: a GlobalID filter into a type whose `relay.NodeID[...]` names a non-pk column
  (`PublisherType.house_code`) coerced and compiled against the pk, refusing the server's own id or selecting the
  wrong row. `filters/base.py::_globalid_target` resolves the target, row path and id slot once and compiles on `<row
  path>__<id_attr>` in `GlobalIDFilter` and `GlobalIDMultipleChoiceFilter`; pk targets byte-identical; fixture
  `Series` (migration 0017).
- [x] 173. fixed: the KANBAN release-readiness checklist (BoardDoc 11) runs `ruff check --fix .` before `ruff format .`,
  as AGENTS and pre-commit do; CardItem 1248 states the same pair in that order (its stale `AGENTS.md:15` line cite
  dropped) and CONTRIBUTING.md lists the hooks as ruff-check then ruff-format. Both rows written with `.update()`
  (`updated_date` kept), KANBAN.md / KANBAN.html re-rendered; archived specs keep the old order as history
- [x] 178. fixed: `scope` and `--changed` resolve a changed path through one resolver
  (`scripts/review_plan.py::_changed_folder` / `_changed_item`), so a deleted or renamed-away path names its nearest
  surviving folder's item and `ScopeReport.folders` counts every rename's old folder; JSON shape unchanged. Pinned by
  `tests/test_review_plan.py::test_scope_resolves_deleted_and_renamed_paths_like_changed`.
- [x] 276. fixed: a model-backed `SerializerMutation` field whose serializer kind disagreed with its column built as
  the column's kind and failed every write masked.
  `rest_framework/serializer_converter.py::serializer_field_fits_kind` is the one kind reading (shared with
  `resolvers.py::_assert_field_agreement`) and `_reject_kind_mismatch` refuses the field at schema build; a relation
  over a text pk's `pk` alias now refuses too (spec-039 Decision 7).
- [x] 163. fixed in code, not docs: `utils/querysets.py::_seal_or_defect` takes `keep_class` (passed only by
  `apply_type_visibility_sync` / `_async`), so the hook's input is rebuilt as the source's own `QuerySet` class and a
  project method works on every read path; instance attributes set outside the constructor are not carried. Docs:
  spec-045, README; fakeshop `LoanQuerySet.with_note()` live rows; mutations M1-M5 red.
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
- [x] 295. fixed: a `ModelForm` field named after a model column but of another kind was typed and decoded by the
  column while the form read its own kind, writing a row's `str()` unchecked or dropping the value.
  `forms/inputs.py::require_column_kind_agreement` refuses it at schema build, reading
  `forms/converter.py::form_field_kind`; a scalar field over a relation column still takes the id. Supersedes 125;
  three shapes that built now refuse.
- [x] 303. fixed: a partial `DjangoMutation` write skipped uniqueness and constraint checks a provided field joined
  when declared on a parent, named in a `UniqueConstraint` condition, a `CheckConstraint` or `unique_for_*`, so the
  duplicate hit the database or saved silently. `mutations/resolvers.py::_constraint_groups` walks `_meta.all_parents`
  and `::_full_clean_or_field_errors` runs `full_clean` with split excludes (`CleanExcludes`) as Django's
  `ModelForm._post_clean` does.
- [x] 304. fixed: a selected annotation whose node had run a row fetch was refused by the visibility seal ("binds a
  function bound value"), because Django caches `BaseExpression.convert_value` in the node and reconstruction carried
  it; reachable from a plain consumer `Prefetch` with an annotated queryset.
  `utils/querysets.py::_reconstructed_value` now drops exactly the caches Django's own copy drops; an evaluated
  sidecar answers `evaluated`.
- [x] 301. fixed: `workspace.py`'s lock files could be unlinked by the macOS `$TMPDIR` purge while held, so a later
  command locked a new inode (two holders of a copy or `state.json`, two gates at once). Every lock is now an empty
  directory (`workspace.py::file_lock` through `_lock_directory`, as 143's marker), and an older version's lock file
  is replaced under its own lock (`_replace_lock_file`).
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
- [x] 339. fixed: `scripts/bug_hunt.py::_final_gate_block`, several process docs, `scripts/review_plan.py::_GATE_ITEM`
  and `workspace.py gate`'s default told agents to run the full `uv run pytest` locally, against AGENTS rules 15 / 16.
  A bare `workspace.py gate` now runs CI's lint job only (`LOCAL_GATE_SUITE`), and every gate reads "lint locally,
  every other suite in the dispatched `django.yml` matrix".
- [x] 340. fixed: a `ModelForm` relation field whose class-level queryset is over a model other than the column's
  target (or a subclass) built and failed every request. `forms/inputs.py::require_class_choice_models` refuses it at
  `finalize_django_types()` where the refusal is certain (default `__init__`, `order_fields` and `get_form`; bound by
  every write); runtime-assigned querysets and optional create fields are unchanged.
- [x] 343. fixed: the visibility seal dropped Django 6.1's `QuerySet._fetch_mode`, so a hook returning
  `.fetch_mode(FETCH_PEERS)` / `FETCH_RAISE` read `FETCH_ONE`. `utils/querysets.py::_seal_or_defect` carries the mode,
  admitting only an exact Django mode (`utils/_queryset_private.py::is_django_fetch_mode`), and
  `utils/write_transaction.py::base_visible_queryset` carries it to the locked locate; Django 5.2 unchanged.
- [x] 162. A declared `RangeFilter` handed raw bounds to the ORM, so a Decimal "NaN" / "Infinity" bound answered a
  masked `ValidationError`. Each non-None bound is now cleaned with the column's `gte` form field
  (`filters/base.py::_column_form_field`), so a non-finite bound is `FILTER_INVALID`; relation bounds pass through as
  sent.
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
- [x] 158. The operation gate (`walker.py::_enable_only_for_operation`) stopped projection writers under a mutation,
  so a consumer `.only()` / `.defer()` was never widened (77 statements vs 2; an async re-fetch raised
  `SynchronousOnlyOperation`). Writers now record under every operation and `plans.py::apply_projection(...,
  introduce=False)` widens a consumer projection; mutation counts equal the query's; the select-path prune is deleted.
  Docs: spec-002 and others.
- [x] 371. `walker.py::_ensure_connector_only_fields(base_queryset=...)` records the attach columns whenever the child
  plan reads a column or the child base queryset carries a consumer projection, so a typename-only child over a
  projecting hook loads its connector with the hook's columns (27 statements -> 2, query and mutation); the hook-free
  child SQL is unchanged; live row `test_library_child_reading_no_column_keeps_the_attach_connector` (sync; the async
  per-row load runs inside the sync evaluation thread and never raised)
- [x] 165. no defect: a relation hop past a deadline after the write failing and rolling back, and later subscription
  frames' hops failing once the budget is spent, are spec-047 Decision 9's contract; pinned by
  `test_query/test_relation_deadline_api.py` and
  `tests/test_resource_policy.py::test_a_budget_spent_between_frames_fails_every_later_frames_relation_hop`.
- [x] 170. no defect: `workspace.py prove` was pinned only through `run`'s shared `execute`, so its own routing (flow,
  layout, cell, fresh, manifest refusal, exit code) had no row; 13 rows in `tests/test_workspace.py` drive
  `main(["prove", ...])` in-process (the proof command on the flow's copy under the flow lease and the copy lock,
  relative and `~` manifests resolved, the command's exit code returned and logged, cell / fresh forwarded, a missing or
  directory manifest refused before a copy binds) and through the actor harness (gc refuses while a prove waits for its
  copy; a second prove waits for the first)
- [x] 166. no defect: the async many-side rows answered the same whether `many_resolver` hit or missed the prefetch
  cache, so they pinned no key; the async planned row now asserts its exact SELECT count, the consumer-prefetch row
  also runs under `strictness="raise"`, and one `test_query/conftest.py::record_compiled_sql` recorder serves the
  async suites; gaps (b)-(d) need no rows.
- [x] 183. `[tool.ruff.format] exclude` bound only directory discovery, so `ruff format <x.md>` rewrote fenced blocks;
  `force-exclude = true` now binds every exclude to named paths, and `scripts/check_trailing_commas.py` reads
  `extend-exclude` and passes `--no-force-exclude` to its own `ruff format` calls. Rows in
  `tests/test_ci_governance.py` and `tests/test_check_trailing_commas.py`.
- [x] 185. no defect:
  `tests/mutations/test_write_transaction.py::test_every_success_payload_under_steady_pings_is_a_committed_row` runs
  in `postgres.yml`'s `package-core` shard and passed in every run since `1b6a09b1`; docs/README.md, GLOSSARY
  `DjangoSchema` and spec-044 now carry the blocked-sync-caller exception instead of an unconditional private window;
  card 079 owns the surrounding transaction.
- [x] 186. docs/README.md now states how the optimizer cooperates with a consumer queryset (kept `select_related` /
  `prefetch_related`, a consumer `Prefetch`, `.only()` / `.defer()` widened, a `Prefetch(queryset=...)` never
  widened), the identity arm, and which nested-connection shapes resolve per parent; GLOSSARY matches; live rows pin
  the async deferred-column failure and `orderBy:` under `strictness="raise"`.
- [x] 231. fixed in the kanban DB by `CardItem` 1479 (the FieldError keying scope bullet now states the per-flavor key
  maps from `utils/errors.py::build_error_key_map`, the package-tier multi-word matrix in
  `tests/utils/test_error_keys.py` and the live rows per flavor), `CardItem` 1500 (card 72's gap list no longer calls
  the keying a wire format no test can see; it still owes its `CAMELCASE_ERRORS` disposition row) and `CardReference`
  23-25 (copies of `CardItem` 142 that still said a model field name); a sweep of every kanban text column finds no
  stale sentence of the family left
- [x] 302. fixed: `scripts/check_spec_glossary.py::auto_link_terms` protected only column-0 fences and inline links
  with no term boundary, so it wrote glossary links into code spans, headings, autolinks, HTML and identifiers. The
  KANBAN lexer moved to `scripts/_markdown_lex.py` with a CommonMark block scanner (`block_regions` / `mask_blocks`);
  the writer masks blocks and matches on `PROSE_TERM_BOUNDARY_AFTER`, and the checker counts only links outside code.
- [x] 187. test gap closed, no lateral defect:
  `tests/test_lateral_pg_parity.py::test_hook_ordered_window_pages_in_branch_with_parity` pages hook-ordered and
  reversed keyset and offset windows through `CROSS JOIN LATERAL` with windowed parity; it passes on Postgres 17
  locally and fails under each seeded mutant; `postgres.yml`'s `package-core` shard (Postgres 16) runs it.
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
- [x] 378. A killed `workspace.py prove` no longer locks its copy: a resync and `gc` remove the copy's
  `prove_failability.py` state directory after restoring a `.venv` mutation byte-compared from its pristine copy; an
  unreadable marker is kept with a notice. A `prove` extra argparse would bind to a wrapper flag is refused, and
  missing `uv` / `git` / `docker` is a refusal, not a traceback.
- [x] 379. A consumer `Prefetch(queryset=...)` owns its path's rows on a forward relation too: the planned JOIN, the
  FK-id elision and the `only()` columns at that path are withdrawn with their resolver keys, JOINs beneath it become
  prefetch lookups over the consumer's rows, and the consumer queryset is not widened, so a row it hides stays hidden
  and an annotation it adds is served (the same answer as without the optimizer); a plain string, a queryset-less or
  `to_attr` Prefetch, or a path the consumer's own `select_related` joins keeps the JOIN
- [x] 380. A consumer `Prefetch(queryset=...)` onto a planned relation whose target type has a `get_queryset` hook is
  sealed through the hook as the seed in one batched query (two statements at any parent count, sync and async) and
  the relation's key stays planned; a seed over another model is still re-read per parent, a sliced one fails as it
  does without the optimizer; a hint seal is recorded only for a generated resolver at the relation's own accessor
- [x] 305. A ModelForm `MultipleChoiceField` / `TypedMultipleChoiceField` over a choice-less single-value column is
  now typed as the form field (`[String!]!` create, `[String!]` update;
  `forms/inputs.py::_writes_list_over_single_value`), with one build warning per field; an update omitting it binds
  the form's initial, so an unsplittable stored value is refused with nothing written. Docs: spec-038 Decisions 7, 8;
  live under `FAKESHOP_TEST_BRANCH_CITY_PICKS`.
- [x] 326. A save-time `ValidationError` on the pk of a serializer field written through `source="pk"`, declared as
  `pk`, or on an MTI child arrived under the renamed input instead of the model's pk name;
  `rest_framework/serializer_converter.py::written_model_field` moved to `utils/relations.py` and
  `utils/errors.py::save_time_error_key_map` resolves the source through it. Live under
  `FAKESHOP_TEST_PK_SOURCE_SERIALIZERS`.
- [x] 190. fixed: a temporal filter value the queryset's database cannot bind (an aware datetime outside years 1..9999
  on SQLite / MySQL / Oracle, any aware datetime when `USE_TZ` is false, an out-of-range `year`) answers
  `FILTER_INVALID` "Enter a value the database can represent." instead of a masked error:
  `FilterSet._validate_form_or_raise` asks the connection through `utils/errors.py::unbindable_temporal`. Docs:
  spec-027, README.
- [x] 328. Every floor run installs each soft dependency at its pinned lower bound: the CI floor cell installs the
  `channels[daphne]`, `cryptography`, `django-debug-toolbar` and `djangorestframework` floors after `uv sync`,
  `scripts/workspace.py::floor_pins` reads them from pyproject (`SOFT_FLOOR_PACKAGES`), and a
  `tests/test_ci_governance.py` row gates every floor literal in `django.yml` against pyproject. Docs: BUILD.md,
  START.md.
- [x] 312. fixed: the visibility seal accepts a `TextChoices` / `StrEnum` / `str`-subclass member wherever Django
  serves one as SQL text (`RawSQL`, `Func` parts, operators, `Meta.db_table`, lookup mapping keys) and seals it to its
  exact text, so the sealed query compiles to the exact-text twin's SQL; pending deferred-filter arguments and a
  combinator's `pk__in` rewrite are rebuilt before baking. Docs: spec-045.
- [x] 313. fixed: reproduced (a database router whose `db_for_read` / `db_for_write` answers a `TextChoices` / `StrEnum`
  alias was refused with `ConfigurationError` on an `orderBy` read through the sidecar);
  `utils/querysets.py::_snapshot_routing_intent` admits a member and keeps its exact text as the routed alias, a
  non-string answer is still refused; spec-050 states it
- [x] 323. Inside a `get_queryset` hook, `apply_cascade_permissions` / `aapply_cascade_permissions` return the
  source's own `QuerySet` class, so a project method chains after the cascade (it raised `AttributeError`); the walked
  result is restated by `utils/querysets.py::_restated_as_source_class`, sharing the walked query, through
  `_built_queryset`. Docs: README, spec-034, spec-045; live under `FAKESHOP_TEST_LOAN_CASCADE_BEFORE_METHOD`.
- [x] 314. Not a defect: only application Python puts a value in `extra(params=)` / `RawSQL` params, and a model
  instance there fails in the driver exactly as in plain Django (an exact `UUID` passes the seal and fails there, as
  before 272); refusing it would break a registered driver adapter. The docstrings and spec-045 say so, pinned by
  `tests/utils/test_querysets.py::test_raw_sql_parameter_model_instance_is_retained_by_reference`.
- [x] 409. not a defect: a `check_<field>_permission` gate is application Python and no wire input sets its slot; a
  non-callable slot already fails closed through `utils/permissions.py::invoke_permission_method` raising
  `ConfigurationError`, pinned by
  `tests/utils/test_permissions.py::test_invoke_permission_method_rejects_a_non_callable_gate_slot`; a class-creation
  check would refuse `classmethod` / `property` gates.
- [x] 410. not a defect: only a write through `object.__setattr__` / `type.__setattr__` passes the seal, and that is
  trusted application code; the overpromising sentence is retracted, so
  `write_mixins.py::_ValidatedMutationMeta.__delattr__`'s message ends "captured once at class creation." (pinned by
  `tests/test_write_mixins.py::test_validated_mutation_meta_record_refuses_slot_writes_and_deletes`).
- [x] 307. fixed: a Ctrl-Z landing while `workspace.py` starts its command waits in
  `scripts/_stop_signals.py::_JobControl` and is delivered by `settle()` once the group is recorded, so the command
  stops with the run; a reader gone from the output (`| head`) no longer turns the exit into 120, since `_pump` points
  the dead fds at `/dev/null` on `EPIPE` / `EIO` only. The two `SIGCONT` routes were not a defect.
- [x] 135. fixed: a malformed GlobalID in a relation input (single or an `[ID!]` element) is the field-keyed relation
  `FieldError` in the payload in the model, ModelForm and serializer flavors, not a masked top-level error: a
  Relay-target relation is typed `strawberry.ID` and decoded server-side
  (`utils/write_values.py::relation_takes_global_id`), and a `relay.GlobalID` override is refused at finalize. Docs:
  spec-036, 038, 039, 053.
- [x] 324. fixed: `tests/utils/test_querysets.py::test_additive_only_subclass_result_is_sealed_to_plain_queryset`
  states behaviour only: the hook result is rebuilt as a plain `QuerySet` from its validated state, the subclass
  identity dropped whatever methods the subclass defines, the predicate kept; the same file's other history phrasings
  ("previously", "used to", "pre-fix", "the old inventory", "before the accessor scan existed", "new guard") are
  restated the same way, each counterfactual checked by running the test's probe with its guard patched out. Comments
  and docstrings only (code digest unchanged)
- [x] 424. fixed: a `DjangoModelFormMutation` whose form carries a prefix (class-level, `get_form_kwargs` or
  `get_form`) is bound under it: values are keyed through the form's `add_prefix`, so every value is read and the
  explicit-`null` and required-file checks answer as unprefixed; no consumer mapping is mutated. Pinned by the
  products prefixed-form live rows and forms resolver rows; docs: spec-038, README.
- [x] 408. fixed: a `SerializerMutation` hook returning a mapping keyed by a `TextChoices` or `StrEnum` member is
  admitted: `rest_framework/resolvers.py::_hook_mapping` refuses only a non-`str` key and keys the result by each key's
  exact text, so the member answers like its plain-`str` twin and a member spelling a reserved, undeclared or
  model-field name is refused with the plain name's message. The library member-key live rows pin it; spec-039 says so.
  The `rest_framework/sets.py` Meta-map key gates stay exact-`str` (dry-0_0_15_3 item 44)
- [x] 429. fixed: under the async executor a sync resolver returning a lazy `QuerySet` to a list field answers with
  the sync rows and SQL: the `_graphql_core_patches` list-completion arm fetches a Django `QuerySet` through
  `__aiter__` off the loop, and `DjangoOptimizerExtension.resolve` builds a sync root's plan in one `sync_to_async`
  worker. Pinned by the library loan grid and async rows; docs: README, spec-002, 035, 050.
- [x] 390. fixed with 429: `allScalarSpecimens` and `allCards` answer on the async view with the sync view's rows and SQL.
  A plain `def` resolver still runs on the loop, so code that evaluates a queryset, and an `apply_sync` call's
  validation, permission gates and related `get_queryset` hooks, belong in an `async def` resolver awaiting
  `apply_async`; the README and the `djangographqlview` and `get_queryset` glossary terms say so, and the
  eager-evaluation library root pins the raise
- [x] 53. superseded by 429: a hand-written `@strawberry.field` returning a lazy QuerySet completes off the loop on the
  async executor, and the README async paragraph under `DjangoListField` says so
- [x] 318. fixed: the cited row already passes since `bf370934`; the residual flakes are fixed by building every
  out-of-order set through one helper, `tests/_idioms.py::scrambled` (with `canonical_order`), which fails loudly when
  nothing scrambles; the filters, orders and utils rows use it and no longer flake. `tests/test_idioms.py` pins the
  helper.
- [x] 330. fixed: `scripts/prove_failability.py::_resolve_scratch_root` names the default scratch parent per user,
  `<system temporary directory>/failability-<uid>` (`DEFAULT_SCRATCH_DIRECTORY_PREFIX` plus `os.getuid()`, as pytest's
  `pytest-of-<user>`), so a second user on a shared Linux `/tmp` gets a parent of their own instead of a refusal on
  every default run; the owner / symlink refusal is unchanged and still guards a squatted per-user name, and an
  explicit `--scratch-root` behaves as before. A two-uid row pins it (it fails through the real refusal with the
  shared name); the module docstring, the `--scratch-root` help and `docs/builder/BUILD.md` say per user
- [x] 585. Not a defect under rule 37: no contract row covers a `RawQuerySet`; the async completion arm adapts a
  Django `QuerySet` only and the `get_queryset` seal refuses a `RawQuerySet`, so the README async sentence now says
  "lazy `QuerySet`". A resolver returning `.raw(...)` still raises `SynchronousOnlyOperation` on the async executor.
- [x] 583. not a defect: a hook's mapping keys are application Python (GOAL "Trust boundary") and no wire input
  reaches them; `utils/truth.py::render` documents that a value outside the builtin scalars renders through its own
  `__repr__`, which is what a lazy translation proxy's `'a'` is, and the refusal states the rule ("every key must be a
  string") beside it, so no code
- [x] 580. not a defect: a `check_<field>_permission` name is application Python (GOAL "Trust boundary"), and no
  contract row says a FilterSet / OrderSet gate whose name matches no gated input is detected; gates are dispatched by
  name at request time, as DRF's `validate_<field>` methods are, so a misspelled one is never called there either.
  A finalize audit of gate names would be a new card, not a fix
- [x] 331. fixed: `scripts/workspace.py::ensure_floor_venv` decides reuse with one read
  (`_read_text_if_present(key_path) == key`), so a key the macOS `$TMPDIR` purge removes reads as "rebuild" instead of
  a `FileNotFoundError`; the file's other purge-reachable check-then-act windows (`gc` sizes, `_remove_flow_dir`,
  `_same_entry`, `_copy_entry` / `_remove_unwanted`) read a vanished entry as gone. One red row per window.
- [x] 406. not a defect: the README "Single-parent fast path" promises it for one parent only; a root `first: N`
  page's probe row is a fetched parent, so the planned window runs, every page is correct and the statement count is
  unchanged. Prefetching only page rows would be a new card, not a fix.
- [x] 407. test gap closed, not a defect: `tests/auth/test_sessions.py` pins that a custom engine outside the
  signed-cookie hierarchy reads as server-side, and `tests/test_routers.py` pins `_actor_is_current`'s strict window
  edge and that a 0.0 window never writes the revalidation stamp; each row kills a surviving mutant. Package tier:
  fakeshop has no WebSocket mount.
- [x] 329. fixed: no signal-forwarding `uv` sits in the stopped process group:
  `scripts/_stop_signals.py::uv_run_launch` resolves `uv run`'s environment once and starts the command directly in it
  (`scripts/prove_failability.py`, and `scripts/workspace.py`'s `run` / `prove` and non-floor gate suites), so each
  process gets each stop once and a `SIGINT` teardown completes. A wrapper a user's own command starts still
  double-delivers.
- [x] 404. fixture gap closed for the reverse-FK serializer path (not a defect): fakeshop's library app gains
  `BranchShelvesSerializer` (`shelves = PrimaryKeyRelatedField(many=True)` over the reverse FK) and
  `createBranchViaShelvesSerializer` / `updateBranchViaShelvesSerializer`, whose live rows pin the `[Int!]` input, one
  batched visibility read, attach-only writes and the hidden-shelf `shelves` relation error with no write; the
  package stand-in `test_many_pk_related_field_over_reverse_fk_column_emits_multi` is deleted, its lines and mutants
  all covered live. The `CompositePrimaryKey` and `db_column=` gaps are `docs/builder/TODO.md` item 27's
- [x] 405. The package row is promoted, then deleted: the live `_NEGATIVE_CURSOR_ROWS` gain a `before` + `last` row
  (sync and async) and `test_minted_offset_cursors_still_page` pages the root `QuerySet`, list and tuple resolvers
  from a minted `after`;
  `tests/test_connection.py::test_consumer_resolver_sequence_negative_cursor_raises_graphql_error` is deleted, every
  mutant it killed failing a live row.
- [x] 319. fixed at the root (breaking, pre-1.0): a flat copy of a child leaf (`books__probe`) is a spelling of the
  request, not a parent form field: `filters/sets.py::FilterSet.get_filters` defers every copy, a request binds only
  copies whose widget keys it sends (`ExpansionSnapshot.copy_keys`), and `_absence_filters_nothing` is gone. `{}` and
  unrelated leaves no longer return nothing or `FILTER_INVALID`, and `books: {probe: ...}` answers as `booksProbe`;
  fakeshop gains `IssueFilter` / `PeriodicalFilter`.
- [x] 332. fixed: `scripts/workspace.py::_remove_flow_dir` empties the marker through `_empty_folder` (symlinks never
  followed) before `marker.rmdir()`, so a `.DS_Store`, stray folder or symlink inside `.dsf-ws` no longer makes `gc`
  raise `OSError` on every rerun; a symlinked marker is unlinked, and the marker still goes last.
- [x] 345. fixed: `scripts/workspace.py` keeps a flow's bindings under the XDG state home (`<state home>/dsf-ws/<sha16
  of the workspace base>/<flow>/state.json`, `0o700`), not the temporary directory, so the macOS `$TMPDIR` purge or a
  cleaned Linux `/tmp` no longer loses them (renumbered slots, resynced edits, duplicate addresses); `gc` / `release`
  / `status` handle both locations and an older state file migrates under `pool.lock`.
- [x] 402. not a defect, confirmed: `mutations/inputs.py::build_mutation_input` reads `relation_bool(field,
  "many_to_many")` only over `editable_input_fields`, which drops every reverse and virtual relation, so a reverse
  kind never reaches it; routing it through the classifier leaves every generated input byte-identical. No code.
- [x] 403. fixed (docs): spec-027 and spec-028 gain an Edge-cases row each, and the `filterset` and `orderset`
  glossary terms one sentence each, stating that a one-shot (`iter(...)`, a generator, `map(...)`) or bare-string
  `Meta.fields` / `filter_fields` / `Meta.exclude` is a `ConfigurationError`: a FilterSet's at class creation, an
  OrderSet's at the first `get_fields()` expansion (finalize); a `SimpleLazyObject` is judged as the object it stands
  for and `filter_fields` is reported as `Meta.fields`. No code
- [x] 381. fixed: a write datetime or time the target database cannot store (SQLite / MySQL / Oracle per
  `unbindable_temporal`; on PostgreSQL also an aware datetime leaving years 1..9999 in the connection's zone;
  `ArrayField` elements) is the field-keyed `FieldError` "Enter a value the database can represent." with nothing
  written in all three flavors (`utils/errors.py::unstorable_temporal`,
  `utils/write_values.py::unstorable_temporal_error`); DRF's raw `OverflowError` cells stay masked (540).
- [x] 401. fixed: the model flavor's create answers an input omitting a `blank=True, null=False` column with no
  default (`createItemHold` without `itemId`) with that column's field-keyed `null` error, nothing written, as the
  ModelForm flavor does; the diagnosis reads the instance after the failed INSERT
  (`mutations/resolvers.py::_created_row_integrity_errors`), sharing `utils/write_values.py::unstorable_columns`.
  Docs: spec-036, spec-038, README.
- [x] 586. fixed: an update input over a `CompositePrimaryKey` model leaves out every key member column in all three
  flavors; one predicate (`utils/relations.py::is_row_key_column`) answers row identity for the input builders and
  `located_row_update_fields`. Package rows pin it; the live row waits on a fakeshop composite model
  (`docs/builder/TODO.md` item 27).
- [x] 353. fixed: `nodes(ids:)` keeps Django 6.1 peer batching. `relay.py::_stamp_nodes` stamps each `resolve_nodes`
  group, then gives the copies whose originals shared one `_state.peers` list a fresh list of weak references to the
  copies, so a lazy FK across 3 loans under `FETCH_PEERS` costs 1 query instead of 3 (sync and async, a repeated id
  included), as the connection and list roots already did; a consumer `resolve_nodes` override's rows batch the same
  way, a row with no peers is left alone, and the shallow copy that keeps a shared row free of the routing hint
  stays. The `_state.peers` read and write live in `utils/_queryset_private.py`. Found verifying 353: row 506
- [x] 503. fixed: `FILTER_INVALID` `errors` keys carry the field's path from the filter root (`shelf__branch__name`,
  `or_0__title`, `not__title`, `<path>____all__` for a nested non-field error); root keys stay bare. Segments are
  spelled by `filters/sets.py::_branch_key` and `filters/inputs.py::LogicOperatorDescriptor.arm_key`. Permission
  denials unchanged, not a defect; docs: README, spec-027.
- [x] 383. fixed: a per-field `"__all__"` publishes Django's text-pattern lookups only on a text column (package
  default `CharFilter`); other columns keep `exact`, `in`, `isNull` and comparisons, and a consumer-supplied filter
  keeps the whole bag. A pattern lookup listed by name on a non-text column generates a `TextPatternFilter` typed
  `String`, so no leaf answers a masked error or a silent `[]`. Docs: spec-027, README.
- [x] 423. fixed: a `DjangoModelFormMutation` input is typed by the shape its form field reads where it disagrees with
  the column: besides 305's case, a built-in single-value form field over an `ArrayField` takes one value, the form's
  `clean_<field>` making it a list. One converter-owned fact (`forms/converter.py::form_field_reads_list`,
  `form_field_reads_one_value`); unregistered fields stay column-typed. Docs: spec-038 Decisions 7, 8.
- [x] 372. fixed: a declared `RangeFilter(lookup_expr="range")` on an integer column applies both bounds as `gte` +
  `lte`, so an out-of-range bound widens or matches nothing instead of a masked `OverflowError`, and a declared
  `ListFilter(lookup_expr="in")` drops members outside the column's range
  (`filters/base.py::_backend_storable_int_members`). Found verifying 372: rows 507-509.
- [x] 375. Not a defect under AGENTS rule 37: a declared `RangeFilter` / `ListFilter` on a relation fails schema build
  with `ConfigurationError` (`filters/inputs.py::_scalar_from_model_field`), so no request carries a bound, and a
  `<relation>__id` path is cleaned by the target's form field; spec-027's pass-through rule, pinned by
  `tests/filters/test_base.py::test_range_filter_without_a_column_form_field_passes_bounds_through`. Found checking
  it: rows 510-512.
- [x] 376. A package `RangeFilter` / `ListFilter` / `ArrayFilter` on a plain `django_filters.FilterSet` (DRF
  `DjangoFilterBackend`) cleaned nothing, so a bad bound raised an HTTP 500; `filters/base.py::_column_form_field` now
  cleans under any django-filter parent, so the backend answers its 400; package-parent filters are unchanged. Found
  verifying it: row 514.
- [x] 382. fixed: on PostgreSQL a temporal filter or write value whose UTC offset the server refuses answers the
  documented envelope (`FILTER_INVALID`, or the field-keyed `FieldError` with nothing written) instead of a masked
  error: `utils/errors.py::unbindable_temporal` reads the binding mode without opening the connection and refuses by
  offset per mode; `ArrayField` elements follow the client-side rule. Docs: spec-027, 036, 039, README.
- [x] 509. fixed: an identity decode (integer `in`, `ListFilter`, `node` / `nodes`, GlobalID and raw-pk filters and
  write ids) finds a stored row a validator would refuse: `utils/querysets.py::coerce_field_value_or_none` never runs
  validators, casting with `to_python` and binding through `Field.get_db_prep_value` on the read database within the
  column's storage domain. Live rows on fakeshop `signed_big` / `Publisher.house_code`; docs: spec-032 Decision 5.
- [x] 400. fixed: a `FilterSet` with `Meta.exclude` and no `Meta.fields` is the whole-set sweep, exactly as `fields =
  "__all__"` with that exclude (pk added, forward many-to-many removed), and a pk named in `Meta.exclude` is never
  added back; one owner (`filters/sets.py::FilterSet.get_fields`); explicit field lists unchanged. Docs: spec-027,
  README.
- [x] 373. A declared `django_filters.LookupChoiceFilter` refused every non-empty value (no GraphQL input carries
  `<name>_lookup`), and without `lookup_choices` schema build cached a half-built `.field` on the declaration,
  breaking later requests and a `DjangoFilterBackend` view. Those reads now run on a deep copy
  (`filters/base.py::copied_form_field`), and a `LookupChoiceFilter` on a served `FilterSet` is a schema-build
  `ConfigurationError`.
- [x] 399. fixed: a supplied hop-walking flat leaf runs its child filter body once per value over the hop's visible
  rows, not twice (a discarded unscoped probe, then the apply), so a consumer `method=` body no longer runs twice; an
  absent leaf keeps the probe, and a projected copy through an unresolved `RelatedFilter(None, ...)` hop answers
  `ConfigurationError`, not `RecursionError`. Owner: `filters/sets.py::FilterSet._apply_relation_leaf`.

- [x] 500. fixed: `tests/test_ci_governance.py::test_no_comment_docstring_or_name_carries_a_provenance_phrase` refuses
  provenance phrases (`pre-fix`, `formerly`, `previously`, `as of 0.0.` and others) in every comment, docstring and
  def/class name of the sweep corpus; the 137 hits it found now state behaviour, 324's two residual sites included.
  Code digest unchanged outside the gate row and two renamed tests.
- [x] 567. fixed: the flow docs cite each prose rule at its home: no process provenance at START.md "Style the
  maintainer cares about", `path::Symbol` citations and the test tier at AGENTS.md (`docs/bug_hunt/HUNT.md`
  step 8, `docs/bug_hunt/worker-2.md` and `docs/dry/worker-2.md` step 7, `docs/dry/DRY.md` Worker-2,
  `docs/review/REVIEW.md`'s process-provenance grade); no rule is added to AGENTS.md
- [x] 506. fixed: `tests/base/test_init.py::test_annotations_evaluate_without_django_stubs_ext_patch` binds the real
  object for every runtime-resolvable `if TYPE_CHECKING:` import, and the 25 annotations it finds subscripting a
  Django class without `__class_getitem__` (e.g. in `utils/write_values.py::unstorable_columns`) go through a private
  `TYPE_CHECKING` alias with a bare-class `else:`; static types unchanged.
- [x] 549. not a defect: no contract row promises what a pattern value the backend refuses answers; a `regex` /
  `iRegex` operand is a plain `CharField` value the backend refuses only when the queryset runs (SQLite
  `OperationalError`, PostgreSQL `DataError`), masked as GOAL's error policy intends, and no upstream validates
  patterns. The promise question is row 571.
- [x] 541. fixed: on PostgreSQL a `DjangoModelFormMutation` optional single-value form field cleaning to `""` over a
  `blank=True, null=False` `ArrayField` answers that column's field-keyed `null` error with nothing written, since the
  save-time diagnosis also runs on the save's `DataError`; an unexplained `DataError` propagates. Not a defect: a
  non-empty value the consumer's form leaves un-wrapped fails in `is_valid()`, as the docs now say.
- [x] 551. not a defect: spec-038 Decision 7 types a model-less form field by its registered class, so
  `SimpleArrayField` (a `CharField` subclass) is `String`, pinned by
  `tests/forms/test_converter.py::test_postgres_array_form_fields_read_a_list`; graphene-django agrees, every wire
  value cleans or gets a field-keyed error, and `form_field_reads_list` applies only over an `ArrayField` column
  (423). Whether it should publish a list is row 576.
- [x] 542. not a defect: on PostgreSQL only a consumer-declared DRF `ChoiceField` over an `ArrayField` reaches it
  (others are refused at build, row 46); the save fails on the unwrapped scalar, a top-level error as the README
  promises, with no contract row for a field-keyed answer. Whether it should build is Waiting row 45 (now with the
  Postgres evidence); the serializer's empty-value gap is row 577.
- [x] 552. not a defect: the refusal is the converter's written fail-loud contract; spec-038 Decision 7 registers each
  supported form-field class individually and "requires NOT registering a base-`forms.Field` catch-all", so a field
  with no registered ancestor raises `ConfigurationError` naming the field and class
  (`forms/converter.py::_unsupported_form_field`), and `SplitArrayField` subclasses `forms.Field` directly (Django
  5.2.16 and 6.1.2 alike). graphene-django types it `String` only through the catch-all the package refuses. Whether a
  column-less PostgreSQL form field should publish a type is Waiting row 576 (facts gathered fixing 551)
- [x] 553. fixed: a `ModelForm` field whose widget reads other keys than its name (`SplitArrayWidget`, `MultiWidget`)
  is bound under the keys that widget reads wherever the package fills form data, so a `SplitArrayField` over an
  `ArrayField` writes the list sent (it answered "This field is required.") and a `SplitDateTimeField` the datetime
  sent; an over-`size` list gets `max_length`. `utils/widgets.py` owns widget keys (`multi_widget_keys` moved there).
  Live fakeshop split-datetime form rows, package rows on PostgreSQL; spec-038
- [x] 507. not a defect: a declared django-filter `RangeFilter` / `BaseRangeFilter` / `BaseInFilter` over a
  `BigIntegerField` answers a value past int64 as Django and plain django-filter do (`FilterSet._apply_flat_leaves`
  runs it byte-for-byte); spec-027's `RangeFilter` row now scopes the `1e50` cap to the package's class. Whether to
  hold declared range / `in` classes to the backend's integer range is Waiting row 622
- [x] 554. not a defect: spec-038 Decision 8 binds an omitted shape-disagreeing field from the form's initial
  (`forms/resolvers.py::_bind_omitted_shape_disagreeing_initials`), so such an update keeps the row, fails validation,
  or writes the value the field makes of the stored list; the build warns
  (`forms/inputs.py::_advise_shape_disagreement`). As for 541 and 542. Whether to refuse such an update is Waiting row
  623
- [x] 508. parked into Waiting row 316, which asks the maintainer this same question; 316 now carries the evidence and
  a third option (two bounds compare as a range, input unchanged), prototyped and verified with no cell narrowed
- [x] 510. fixed: a declared filter on `pk` or `<relation>__pk` reads the column the key stores:
  `filters/base.py::_filterset_resolved_field` resolves the path through `utils/relations.py::_classify_path_cached`
  and follows a relation-valued key with `utils/relations.py::stored_value_link`, so the leaf is typed by that column
  (`Int`, `Decimal`, `UUID`, where it was `String`) and cleaned by its form field. 375's refusal stands. Live rows on
  library `ShelfFilter` / `PatronProfileFilter` `pk` leaves, package rows; spec-027
- [x] 593. AGENTS.md is cited by content, not line ordinal: 32 drifted cites (CI, scripts, REVIEW.md, MUSE.md, KANBAN
  `CardItem` rows) and the still-correct ones now name the rule; START.md stops calling AGENTS numbered. Closed
  history left as written
- [x] 511. fixed: a raw-key to-many relation leaf behind a visibility hop compares the target rows' own key column:
  `filters/base.py::_raw_identity_column` reads that column (a relation-valued pk followed to its stored column),
  where `_coerce_relation_identity` passed the value through. So a `Decimal` `NaN` or unstorable datetime key matches
  nothing instead of a masked error, and a target keyed by a one-to-one onto a non-pk `to_field` matches its rows.
  Package rows with the unhopped leaf as control
- [x] 547. A `date` or naive `datetime` in a `DateTimeField` column escaped the temporal preflight
  (`utils/errors.py::unstorable_temporal`) and answered a masked `OverflowError` at `save()`; it is now checked as the
  datetime Django binds, so an unstorable one is the field's `invalid` `FieldError`, nothing written. The `ModelForm`
  scalar path was already covered. Tests: `tests/utils/test_errors.py`, `tests/rest_framework/test_resolvers.py`
- [x] 512. A declared `ListFilter` / `ArrayFilter` read raw form data through `TextInput`, so every `?name=` answered
  "expected a list." (a 500); `filters/base.py::_ElementField` now reads it by the generated `in`'s rule
  (`_MembershipCSVWidget`): `?name=a,b` is `["a", "b"]`, each element cleaned by the column's form field (a junk one
  is a 400). The `RangeFilter` half is not a defect. Tests: `tests/filters/test_base.py`; spec-027
- [x] 514. Not a defect: a declared `RangeFilter` bound or `ListFilter` element on a `BooleanField` is cleaned by
  `forms.NullBooleanField`, which reads an unrecognized string as `None`, the raw-form rule of every Boolean filter
  under `DjangoFilterBackend`; GraphQL types it `Boolean`. No code
- [x] 556. On PostgreSQL through psycopg 3 an `ArrayField(TimeField)` write mixing naive and aware times answered a
  masked `DataError`; `utils/errors.py::unstorable_temporal` now asks the driver about the whole list
  (`_psycopg_refuses_list`), so a list psycopg refuses is the field's `invalid` `FieldError`, nothing written. Whether
  PostgreSQL stores `[aware, naive]` into `time[]` is unverified on a server. Tests: `tests/utils/test_errors.py`
- [x] 545. `scripts/prove_failability.py::_pattern_matches` read `[*]` as a character class, so a glob over a
  parametrized id never matched; a pattern now also matches with every `[` literal (`test_x[*]` names every row),
  equality and plain `fnmatch` first, so every pattern that matched still matches. Tests:
  `tests/test_prove_failability.py`
- [x] 557. Not a defect (application Python is trusted): the package never iterates with a named cursor, so a filter
  value at offset 16:00 or more filters as the README says; only consumer code calling `QuerySet.iterator()` under a
  server-side cursor factory gets the server's refusal. No code
- [x] 543. `utils/errors.py` and `types/converters.py` each soft-imported `ArrayField`, so tests patched each copy
  separately; one private owner, `utils/_array_field.py` (`ARRAY_FIELD_CLS`, `array_element_field`), now serves every
  site and tests patch it through `tests/_postgres_fields.py::patch_array_field`. No behaviour changes. Tests:
  `tests/utils/test_errors.py`
- [x] 591. Under Django 6.1 an unconstrained `DecimalField` identity decode (Relay id, raw pk, relation filter or
  write id) carrying `"1e1000000"` bound a value PostgreSQL's `numeric` refuses (masked `DataError`);
  `utils/querysets.py::_stored_decimal_or_none` now binds a fitting spelling as written, trims trailing fractional
  zeros otherwise, and answers no row (`None`) for what still does not fit. Limits are source-derived, not checked on
  a server. Tests: `tests/utils/test_querysets.py`
- [x] 558. `OrderSet` ignored `Meta.exclude`, so an excluded column stayed orderable and an exclude-only set failed at
  finalize; `orders/sets.py::OrderSet._expand_meta_fields` now drops listed names (pk included) from the sweep or
  declared names, and a malformed `exclude` raises `ConfigurationError` (`_read_meta_exclude`). Live rows in
  `test_library_api.py` over a new fakeshop `PublicPatronOrder`, package rows in `tests/orders/test_sets.py`; docs:
  spec-028, README
- [x] 517. The `ConfigurationError` for a `method=` filter with no form field
  (`filters/inputs.py::convert_filter_to_input_annotation`) advised a `field_class=` spelling that raises `TypeError`;
  it now names the filter's class and advises the spellings that work (a typed primitive, or a `Filter` subclass
  declaring `field_class`). Tests: `tests/filters/test_inputs.py`, live rows in `test_library_api.py`
- [x] 518. The choice refusal (`filters/inputs.py::_choice_enum_from_filter`) named "ChoiceFilter" for every filter
  and gave advice the arm never reads; it now names the declared class and the real cause (no `choices` column backs
  it) and advises declaring `choices` or a non-choice filter. No shape moved. Tests: `tests/filters/test_inputs.py`;
  spec-027
- [x] 516. Not a defect: a consumer-declared bare `BaseCSVFilter` keeping `exact` runs as plain django-filter runs it
  (same SQL, 0 rows; same `TypeError`), and the declaration is meaningful with `in`, `range` and `method=`, so a
  class-keyed refusal would break working shapes. Build-time refusal of a list over a non-list lookup is folded into
  robustness row 625
- [x] 519. A declared filter a deep copy refuses (a `method=` bound over a lock or cache handler, a lock in `extra`)
  is refused at schema build with a `ConfigurationError` naming set, attribute and class, where it failed every
  request with a raw `TypeError`: finalizer subpass `types/finalizer.py::_audit_filter_copies` copies each set's
  filters through `filters/base.py::copied_declared_filter`. Tests: `tests/filters/test_finalizer.py`; spec-027
- [x] 520. A filter a `RelatedFilter` expansion copies is named as the child set declares it in every input-conversion
  refusal (class, attribute, the `RelatedFilter` chain it was reached through), never `Projected<Class>`; one helper,
  `filters/sets.py::_leaf_declaration`, owns it. Own-set messages are byte-identical. Tests:
  `tests/filters/test_inputs.py`, `tests/filters/test_sets.py`; spec-027
- [x] 560. Not a defect: `FilterSet.filter_queryset` builds each `and` / `or` / `not` arm over the flat-narrowed
  queryset (`_q_for_branch`), and the repeated predicate keeps an arm's meaning for non-row-local consumer methods and
  for `not`. Same rows, no contract row; the planner sees a redundant conjunct
- [x] 515. A declared `MultipleChoiceFilter` / `TypedMultipleChoiceFilter` / `AllValuesMultipleFilter` publishes a
  list typed from its column (its enum, scalar, or `str`): `filters/inputs.py` gains a `MultipleChoiceFilter`
  kind-table row before the catch-all, and normalize hands the form a list. Live rows in
  `examples/fakeshop/test_query/test_library_api.py`, package rows in `tests/filters/test_inputs.py`,
  `tests/filters/test_sets.py`; spec-027
- [x] 640. A flat copy of a child set's filter fires its nested spelling's permission gates whatever the
  `RelatedFilter` attribute is called (a renamed hop let `inSeriesHandle` past
  `SeriesFilter.check_handle_permission`): every copy now carries one `filters/sets.py::ChildProjection`, read by
  `FilterSet._leaf_gates` and `filters/inputs.py::_is_declared_head`. Live rows in
  `examples/fakeshop/test_query/test_library_api.py`, package rows in `tests/filters/test_sets.py`; spec-027
- [x] 346. Every git call in `scripts/` runs through `scripts/_git.py::run_git` under
  `scripts/_git.py::repository_env`: only repository config counts, non-locating `GIT_*` variables are dropped
  (`GIT_INDEX_FILE` kept), and `GIT_OPTIONAL_LOCKS=0` stops `status` rewriting the shared index. Tests:
  `tests/test_git.py`
- [x] 348. The caller's ownership trust is kept under the isolation: `scripts/_git.py::caller_safe_directories` reads
  `safe.directory` from the caller's protected sources only (system, global, command scope; never `GIT_CONFIG` or
  repository config) and passes it as command scope, so `workspace.py` and every other script read a checkout the
  caller marked safe and refuse one the caller did not, exactly as the caller's git does. Fixed with 346
- [x] 347. `scripts/workspace.py::item_diff` keeps the baseline's blob for every `is_excluded` name, as
  `snapshot_commit` does, so a pre-existing file there is never the item's addition or edit; explicit `names` are
  never filtered. Tests: `tests/test_workspace.py`
- [x] 349. `scripts/workspace.py::audit_record` turns an unreadable record (missing, a directory, no permission, not
  UTF-8) into a refusal: `workspace: audit <path>: <reason>` on stderr, exit 1, no traceback; records audited before
  it keep their report lines. The `audit` manual says so. Tests: `tests/test_workspace.py` (each unreadable shape,
  the CLI refusal, a readable record before a missing one)
- [x] 374. A one-value filter whose widget reads other form keys (`NumericRangeFilter`, a `MultiWidget` field) is
  refused at schema build naming the keys and the `RangeFilter` remedy
  (`filters/inputs.py::_refuse_widget_reading_other_keys`), where it published a scalar the widget never read and
  answered every row. Tests: `tests/filters/test_inputs.py`; spec-027
- [x] 566. The four test trees state behaviour where they narrated history (about 300 sites, 16 tests renamed), and
  `tests/test_ci_governance.py::test_no_comment_docstring_or_name_carries_a_provenance_phrase` refuses 17 phrases.
  Executable code unchanged. Out of scope, filed: 629, 630
- [x] 570. Fixed by the shard split (`d0073edf`): every `django.yml` test cell runs as two jobs on separate runners
  (`library-keyset`: `test_library_api.py` + `test_keyset_api.py`, `--dist load`; `remainder`: the rest, `--dist
  loadscope`) and a `coverage` job combines the latest cell's two traces and owns the gate; the 45-minute
  `timeout-minutes` is unchanged. Measured on the three push runs since (`40301105850`, `40339630011`,
  `40405314085`): the slowest shard job took 17 minutes (floor `remainder`), the rest 8 to 14; none was cancelled.
  Trimming the suite itself stays the maintainer's call
- [x] 573. not a defect: no contract row covers a consumer form field cleaning `""` over a nullable non-text column
  (plain Django's `save()` raises on it too); measured on SQLite and PostgreSQL it answers the field-keyed "This field
  cannot be null.", nothing written. Which answer a nullable column should give is row 631
- [x] 420. `scripts/_markdown_lex.py::block_regions` reads containers as CommonMark appendix A does (one stack of
  quotes and list items, lazy continuation) and link reference definitions per 4.7, so neither takes a term link; all
  652 CommonMark 0.31.2 examples mask as the spec renders them. Tests: `tests/test_check_spec_glossary.py`
- [x] 599. A FilterSet's `get_filters()` override is the set's filter table everywhere (an added filter was published
  but filtered nothing; renames raised `KeyError`): `filters/sets.py::FilterSet._publish_filters` runs the override
  once and publishes its result, read through `FilterSet._filter_table`. Live rows in
  `examples/fakeshop/test_query/test_library_api.py`, package rows in `tests/filters/test_sets.py`; spec-027
- [x] 598. `HIDE_FLAT_FILTERS` hides each flat copy of a `RelatedFilter` expansion under any key and never the set's
  own filter: `filters/inputs.py::_build_input_fields` decided by the key's first segment (hiding fakeshop
  `PrintingFilter` `edition__printings__co_publishers`); it now asks `filters/sets.py::_is_flat_copy` per lookup. Live
  rows in `examples/fakeshop/test_query/test_library_api.py`, a package row in `tests/filters/test_inputs.py`;
  spec-027
- [x] 646. Not a defect under the AGENTS defect rule: `scripts/_markdown_lex.py` states its contract as
  CommonMark (its module docstring cites CommonMark 4.1-4.7 for `block_regions`), and on a type-7 HTML tag
  line in a lazy continuation position it does what the CommonMark spec, commonmark.js and markdown-it do
  (lazy paragraph text); only cmark-gfm opens an HTML block there. No repo markdown file has the shape
  (measured verifying 420), so no feasible project input reaches the difference. Lexing to cmark-gfm's reading
  instead would be a new card
- [x] 630. `examples/fakeshop/test_query/README.md` states its teaching as present practice, citing live rows by
  `path::Symbol`; history narration, stale citations and the "Second sweep" section are gone. The leftover package row
  it named is filed as 603
- [x] 603. `tests/optimizer/test_relay_id_projection.py` is deleted: a mutation table found no mutant only it killed,
  and live and `tests/optimizer/test_walker.py` rows reach its lines. Writing a live pin for a non-pk `NodeID` found
  604
- [x] 604. A Relay `id` selection projects the column the type's id reads at every position:
  `optimizer/walker.py::_walk_selections` routes `id` to `_relay_id_column` (via `types/relay.py::_node_id_slot`),
  where fakeshop `PublisherType` loaded `id` and refetched its NodeID column per row (`SynchronousOnlyOperation`
  async). Live rows in `examples/fakeshop/test_query/test_library_shapes_api.py`, `test_library_api.py`, package rows
  in `tests/optimizer/test_walker.py`; spec-015
- [x] 421. The board and the spec auto-linker share `scripts/_markdown_lex.py` `TERM_BOUNDARY_AFTER`: a punctuation
  run after a term bars the link only when an identifier character follows, so a sentence-ending term is linked and
  `Meta.fields.get` is not. `KANBAN.md` re-rendered. Tests: `tests/test_build_kanban_md.py`
- [x] 422. (robustness) `scripts/check_spec_glossary.py::_insert_glossary_ref_def` slots the new
  `[glossary-<anchor>]: ...` def before the group's first def whose label sorts after it (codepoint), else at the
  group's end, and never re-sorts the rest: every existing line keeps its order and bytes. The whole-line `sorted()`
  rebuild reordered hand-written lines in 44 of the 188 tracked `.md` files with a `<!-- docs/ -->` group (whole-line
  order puts `[foo-bar]` before `[foo]`); a census of 2186 inserts across those files adds one line each and moves
  none. Tests: `tests/test_check_spec_glossary.py`
- [x] 568. The provenance gate reads every string statement (docstrings, attribute docstrings, nested strings,
  f-string literal parts), its limits stated; five planted rows pin it.
  `scripts/review_inspect.py::PROVENANCE_PATTERNS` stays a separate report-only list
- [x] 564. Four error strings state the invariant without a release number (`RelatedFilter` `lookups=`,
  `Meta.connection`'s sub-key, `decode_global_id`'s per-strategy reason, the router hint); the first three are pinned
  exactly. dry-0_0_15_3 item 28 is ticked
- [x] 575. A create's build advises like an update's: `forms/inputs.py::build_form_input_class` runs
  `_advise_shape_disagreement` for every input it builds, over the fields that input binds, with the first clause
  (the form must turn the input into the column's value) for both and the omitted-field initial advice for the
  update only; one warning per input build, so a form serving a create and an update logs one of each. Package rows
  in `tests/forms/test_inputs.py` pin the texts and counts; the docstrings, spec-038 and the GLOSSARY
  `DjangoModelFormMutation` body are restated
- [x] 634. No release number of this package is left in .py source (90 sites to 0);
  `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_carries_a_release_of_this_package`
  refuses a current-series release or release-carrying card id in comments, strings and names. Maintainer request
- [x] 460. A hinted `OptimizerHint.prefetch(Prefetch(...))` without `to_attr` whose queryset is not over the lookup's
  target is refused at type build naming `Type.field` (`types/base.py::_hinted_prefetch_seed_defect`), where it filled
  the relation with rows the target's `is_type_of` refuses. Tests: `tests/types/test_base.py`, `test_library_api.py`;
  spec-045
- [x] 462. A reverse relation whose `related_query_name` differs from its accessor is planned in both spellings
  (`optimizer/walker.py::_walk_selections` `lookup_prefix`, `optimizer/plans.py::JoinPrefix`,
  `utils/relations.py::respell_relation_path`), where it served rows a consumer `Prefetch` hid, joined past
  `get_queryset`, or raised `AttributeError`. Tests: `tests/optimizer/test_relation_spelling_execution.py`,
  `tests/utils/test_relations.py`
- [x] 384. A filter value the database cannot bind is refused by asking Django: each temporal leaf's predicate is
  built by its own `filter()` and compiled on `queryset.db` (`filters/sets.py::_unbindable_predicate`), and a failure
  is the coded `FILTER_INVALID` where a kind-mismatched value overflowed as a masked error;
  `utils/errors.py::refuses_utc_offset` keeps the PostgreSQL offset rule. Tests: `tests/filters/test_sets.py`,
  `tests/utils/test_errors.py`
- [x] 388. A class-level `Filter.filter()` override owns its value like `method=`: the unbindable-value ask runs only a
  `filter` defined by django-filter or this package (`filters/sets.py::_runs_shipped_filter`, the MRO owner's module),
  so consumer code never runs to validate; documented in `_unbindable_temporal_errors`. Tests: `tests/filters/test_sets.py`
- [x] 398. A class-level `GlobalIDFilter.filter` override is read by `filters/sets.py::_decodes_before_binding` through
  `utils/truth.py::overrides`, so its lone-surrogate value is the coded `FILTER_INVALID` instead of a masked
  `UnicodeEncodeError`. Tests: `tests/filters/test_sets.py`
- [x] 385. A filter integer the driver cannot bind (a `__year` `in` / range member past 2**63) is the coded
  `FILTER_INVALID` instead of a masked `OverflowError`: after 384's compile, `filters/sets.py::_bound_value_lookups`
  holds each bound integer to the connection's range via `utils/querysets.py::binds_integer`. Tests:
  `tests/filters/test_sets.py`, `test_scalars_filter_api.py`
- [x] 386. A `DurationField` filter leaf is asked like a temporal one: on a backend that binds durations as integer
  microseconds (SQLite, MySQL) a value past 64 bits of microseconds is the coded `FILTER_INVALID` instead of the masked
  bind `OverflowError` (`filters/sets.py::_unbindable_temporal_errors` gate, `binds_integer` with the
  `BigIntegerField` range). Tests: `tests/filters/test_sets.py`
- [x] 389. A PostgreSQL `ArrayField` of datetimes, times or durations is asked like a temporal column
  (`utils/_array_field.py::array_leaf_field`; `utils/errors.py::refuses_utc_offset` holds list elements to the text
  rule), so an element whose offset PostgreSQL refuses is refused instead of a masked `DataError`. By source and
  recorded server facts; pg rows run on the PostgreSQL tier. Tests: `tests/filters/test_sets.py`,
  `tests/utils/test_errors.py`
- [x] 427. (robustness) The django.yml floor-cell check (`tests/test_ci_governance.py::_floor_cell_problems`) holds
  step order, refuses a later `uv sync` that puts the lock back over the pins, and finds floor nodes by content;
  `scripts/workspace.py::_lower_bounds` refuses a marker-split floor. Tests: `tests/test_ci_governance.py`,
  `tests/test_workspace.py`
- [x] 428. (robustness) `tests/test_workspace.py`'s stop-relay rows use a held clock instead of sleeps:
  `scripts/workspace.py::_StopRelay` takes a `clock`, and the test moves it past `STOP_REPEAT_GRACE` only after the
  relay handled a stop. Green 15/15 under load where the parent failed 2-3
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
- [x] 501. (robustness) The workspace pool root is claimed as this user's own: `scripts/workspace.py::default_root`
  names it `dsf-ws-<uid>` on a shared temp dir, `workspace_base` refuses a symlinked or foreign root as
  `WorkspaceError`, and `_make_flow_dir` claims it through `prove_failability.py::claim_private_directory`. Tests:
  `tests/test_workspace.py`, `tests/test_prove_failability.py`
- [x] 502. (robustness) `scripts/prove_failability.py::_new_capture` and `_read_probe` read their temp-resident file
  once (`_read_text_if_present`), a missing one counting as absent, so the purge removing it between a check and the
  read no longer raises `FileNotFoundError`. Tests: `tests/test_prove_failability.py`
- [x] 505. (robustness) A ready copy whose manifest is gone while its folder still holds a regular file (an edit, or
  any file written in the last three days, outlives the purge) is refused with a typed `WorkspaceError` naming
  `--fresh` / `gc` instead of being resynced over its edits (`scripts/workspace.py::_admit`, `_holds_a_file` walks
  without following symlinks); a copy gone with its manifest (a reboot, or a purge that left only folders and links)
  resyncs into its slot. The manifest is not renewed on reuse, so it stays the copy's age canary. Module docstring and
  START.md "Machine budget" say so. Tests: `tests/test_workspace.py`
- [x] 587. A lazy translation string in a set's field declaration is read as text: `utils/_narrowing.py::is_text_atom`
  backs `sets_mixins.py::is_re_readable_field_declaration`, so FilterSet / OrderSet `Meta.exclude` and OrderSet
  `Meta.fields` refuse it as a bare string (it excluded by substring or expanded per character), and a lazy
  `"__all__"` is the shorthand. Tests: `tests/filters/test_sets.py`, `tests/orders/test_sets.py`
- [x] 900. The lookup iterator's return annotation uses a private runtime-safe alias, preserving
  `Lookup[object]` for static checking without subscripting Django's runtime class. The unpatched annotation gate
  passes; no filtering behavior or supported introspection contract changes. Tests: `tests/base/test_init.py`.
- [x] 659. Not a package defect under GOAL's trust boundary: the two repeat-stop tests in
  `tests/test_prove_failability.py` use wall-clock sleeps, but name no broken supported configuration or wire
  contract. Deterministic test timing is a tooling robustness task; the signal relay's behavior is unchanged.
- [x] 607. Not a defect against the shipped contract: spec-015 explicitly leaves optimizer cooperation
  out of both node defaults, and the glossary states that node refetch receives no optimizer plan. The capability
  decision and its query-count evidence remain under Waiting item 327; this row adds no separate defect.
- [x] 540. (robustness) The serializer flavor answers DRF's field-keyed `overflow` for a datetime `enforce_timezone`
  cannot place, at every depth, instead of the masked error:
  `rest_framework/resolvers.py::_translate_datetime_overflow` turns a raw `OverflowError` into `fail("overflow")`.
  Tests: `examples/fakeshop/test_query/test_scalars_mutation_api.py`, `tests/rest_framework/test_resolvers.py`
- [x] 569. (robustness) `scripts/check_annotation_subscripts.py` sweeps every annotation and fails closed on a
  subscripted class outside its audited `SUBSCRIPTABLE` table or an unaudited site; it found `utils/truth.py`
  subscripting `classmethod` / `staticmethod`, now `TYPE_CHECKING` aliases. Tests:
  `tests/test_check_annotation_subscripts.py`, `tests/base/test_init.py`
- [x] 562. (robustness) The async pre-pass derives a hop only for a flat leaf the form data names, so a range naming
  no bound runs the hop target's `get_queryset` no more than `apply_sync`:
  `filters/sets.py::FilterSet._leaf_form_data` backs `_named_leaf_filters`. Tests: `tests/filters/test_sets.py`;
  spec-027
- [x] 628. A many-to-many leaf whose through model's FK onto the target has a non-pk `to_field` is compared by the
  target's pk, as its wire type says (`filters/base.py::_relation_uses_non_pk_to_field` via
  `utils/relations.py::non_pk_forward_link`, 511's marker), where it compared the `to_field` column and matched the
  wrong rows. Tests: `tests/filters/test_base.py`; spec-027
- [x] 577. A `SerializerMutation` save refused over a `blank=True, null=False` column left out or set to `None` is
  that column's field-keyed `null` error, not the `"__all__"` `constraint` error:
  `rest_framework/resolvers.py::_write_witness` records attempted rows and `_attempted_row_integrity_errors` runs
  `utils/write_values.py::unstorable_columns` over the refused one. The `""`-over-`ArrayField` cell stays with row 45.
  Tests: `tests/rest_framework/test_resolvers.py`, `examples/fakeshop/test_query/test_products_api.py`
- [x] 523. A `DjangoModelFormMutation` form declaring a built-in temporal field that cannot read its temporal column
  (a `DateField` over a DateTime column, a non-`TimeField` over a Time column) is refused at build
  (`forms/inputs.py::_require_temporal_reader`), where it answered masked errors or silently truncated. Tests:
  `tests/forms/test_inputs.py`; spec-038
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
- [x] 529. A decimal filter value outside PostgreSQL `numeric`'s format is refused as the field-keyed `FILTER_INVALID`
  on every filter family instead of the masked `DataError`: `filters/sets.py::_unbindable_value_errors` reads each
  compiled `Decimal` through `utils/errors.py::refuses_numeric_format`, shared with 591's identity decode. Other
  backends bind as given. Tests: `tests/utils/test_errors.py`, `tests/filters/test_sets.py`
- [x] 531. `node` / `nodes` and relation-id decodes match a requested id by the id column's own value
  (`utils/querysets.py::identity_key`), not `str()`, so `"2.50"` for a stored `2.5` or an aware datetime in another
  offset finds its row instead of null or "Invalid id". Tests: `tests/test_relay_node_field.py`,
  `tests/utils/test_querysets.py`
- [x] 534. `FilterSet` and `OrderSet` refuse an unknown `Meta` key at class creation, through the one typo guard every
  write flavor runs (`utils/inputs.py::reject_unknown_meta_keys`): a `FilterSet` takes the keys django-filter's
  `FilterSetOptions` reads plus the `filter_fields` synonym, an `OrderSet` `model`, `fields` and `exclude`; a `Meta` that
  is not a class is refused too. spec-027, spec-028 and the `filterset` / `orderset` glossary terms say so. Tests:
  `tests/filters/test_sets.py`, `tests/orders/test_sets.py`, `tests/utils/test_inputs.py`
- [x] 535. A `Meta.exclude` name is checked in both set families (`sets_mixins.py::reject_unknown_exclude_names`): a
  declared name is refused with the remedy, an unknown one naming the legal ones; a non-string entry is a
  `ConfigurationError` (`sets_mixins.py::require_field_name`), not `AttributeError`. Tests:
  `tests/filters/test_sets.py`, `tests/orders/test_sets.py`
- [x] 536. A model-less `FilterSet` whose `Meta` sweeps (`"__all__"`, or `Meta.exclude` without `Meta.fields`) raises a
  `ConfigurationError` naming the set from `get_fields` (`sets_mixins.py::require_sweep_model`, the wording an
  `OrderSet` uses), not upstream's raw `AttributeError`; a model-less base whose subclass supplies `Meta.model` still
  builds in both families. Tests: `tests/filters/test_sets.py`
- [x] 629. Test prose in `tests/filters/test_sets.py`, `tests/test_routers.py`, `tests/test_strawberry_patches.py` and
  fakeshop's `test_transport_api.py`, `test_products_api.py` and `test_library_api.py` cites each contract by its
  content (the spec-046 Decision a test pins, the equivalence-matrix case it proves, the named test it defers to)
  instead of a test-plan row, matrix row, gap or test ordinal; comments and docstrings only (stripped ASTs and
  collected node ids identical).
- [x] 596. A `ProjectedChildFilter` borrowed without its branch is a `ConfigurationError` at publish naming set, key,
  donor and branch (`filters/sets.py::FilterSet._reject_foreign_projection`), instead of a raw `KeyError` or the
  donor's filter run silently; `FilterSetMetaclass` deep-copies a filter another set owns. Tests:
  `tests/filters/test_sets.py`
- [x] 597. A declared head's name is never walked as a relation path: `run_active_input_permission_checks` asks the
  set's `_gate_path_spells_relations` seam, which a `FilterSet` answers "no" for a declared head, and
  `FilterSet._gate_path_walk_gates` walks a non-declared leaf's `field_name` even where a declared name spells the
  same string; so a flat expanded copy (`shelf__named` beside `real_shelf = RelatedFilter(..., field_name="shelf")`)
  and a plain declared filter named like another branch's accessor fire exactly their nested twin's gates. spec-027
  says so. Tests: `tests/filters/test_sets.py`
- [x] 650. `utils/errors.py::unstorable_temporal` asks Django's `Field.get_db_prep_save` for every temporal value
  instead of modelling conversions, so an aware datetime a `DateField` cannot make naive is the field-keyed "Enter a
  value the database can represent." instead of a masked `OverflowError`; `LICENSE.django` ships for the adapted
  branch. Tests: `tests/utils/test_errors.py`, `tests/rest_framework/test_resolvers.py`
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
- [x] 652. Generated integer `in` / `range` leaves over a transform (`year`, `month`, `len`, ...) bind the transform's
  output: `filters/base.py::IntegerInFilter` hands members to the lookup's prep (it dropped every member) and
  `IntegerRangeFilter` applies bounds through the transform, so `year__in` answers those years; a value past the
  integer range is `FILTER_INVALID` (`filters/base.py::_reads_integer_transform`). Tests:
  `tests/filters/test_base.py`, `tests/filters/test_sets.py`
- [x] 663. Every configuration slot reading a field-name sequence refuses a whole text atom (lazy string, bytes,
  `memoryview`, a `SimpleLazyObject` over one) as the bare-string refusal instead of reading it per character, via
  `utils/_narrowing.py::is_text_atom` at `utils/inputs.py::normalize_field_name_sequence` and six other slots. Tests:
  `tests/utils/test_inputs.py`, `tests/test_permissions.py`, one lazy `Meta.exclude` row per mutation flavor
- [x] 579. The filter side reads a supplied leaf by every key its widget reads (`utils/widgets.py::widget_keys`):
  `filters/sets.py::_widget_keys` and `FilterSet._leaf_absent` read a `SplitArrayWidget`'s per-index keys, so a child
  set's split-array copy is bound and filters instead of being dropped. Tests: `tests/filters/test_sets.py`; spec-027
- [x] 654. The filter ask reads only lookups a leaf binds for the user's value:
  `filters/sets.py::_bound_value_lookups` skips the queryset's own annotations, so an annotation's out-of-range
  constant never refuses an in-range value; `utils/errors.py::binds_integer` holds no range for an `IntegerField`
  subclass the backend gives none, instead of `KeyError`. Tests: `tests/filters/test_sets.py`,
  `tests/utils/test_errors.py`
- [x] 657. An integer `ArrayField` is asked like the temporal and decimal arrays: each bound element is held to its
  element column's range (`utils/errors.py::refuses_integer_range`) and a member past it is `FILTER_INVALID`, never
  dropped. Tests: `tests/filters/test_sets.py`, `tests/utils/test_errors.py`
- [x] 670. A `DjangoModelFormMutation` form declaring `forms.DateTimeField` over a `DateField` column is refused at
  schema build (`forms/inputs.py::_TEMPORAL_COLUMN_FORM_CLASSES`, `_require_temporal_reader`), as the serializer flavor
  refuses the pair: the wire is the column's `Date`, and the form field made it midnight in the current time zone, so a
  zone ahead of the default stored an earlier day, also on an update omitting the field. A subclass overriding
  `to_python` or `clean` still builds. README, spec-038 and the `djangomodelformmutation` glossary term say so. Tests:
  `tests/forms/test_inputs.py`
- [x] 668. A refused serializer save reports a field-keyed `null` only for a column the save writes:
  `rest_framework/resolvers.py::_write_witness` records each attempted row with its `pre_save` `update_fields`, and
  `utils/write_values.py::unstorable_columns` skips a column outside them (by name or attname) before reading it, so a
  consumer save narrowed to other columns answers the constraint envelope and a deferred column the save left out is
  never loaded. spec-039 says so. Tests: `tests/rest_framework/test_resolvers.py`. The swallowed-save half and the
  ModelForm flavor are rows 695 and 696
- [x] 672. Documented, no refusal rule: on SQLite a decimal filter value is compared as a double, so `1e-1000000`
  compares as zero and values differing past 15-17 digits can compare equal; the row's `-1e1000000` half did not hold.
  docs: README, spec-027, `utils/errors.py::refuses_numeric_format`; pinned by
  `tests/filters/test_sets.py::test_decimal_filter_value_compares_as_a_double_on_sqlite`
- [x] 666. `FilterSet.apply_async` awaits the hops of every absent walking leaf that acts on its absent value: the
  first sync boundary probes each once (`_probe_absent_relation_leaves`) and the async code awaits them via
  `_await_hop_visibility_async`, so consumer filter bodies and an async `get_queryset` run as often as on
  `apply_sync`. Tests: `tests/filters/test_sets.py`; spec-027
- [x] 675. On SQLite a `DecimalField` key is not reliably addressable by `node` / `nodes` or a relation id: SQLite
  stores a non-integral or past-64-bit value as a float, Django reads decimals through 15 significant digits (an
  integral one too before Django 6.1), and a column with decimal places binds even an integral key in a spelling SQLite
  compares as a float, so neither the written spelling nor the emitted id need name the row. README's Relay paragraph
  and spec-032 say so with the remedy (a key the column holds exactly); `tests/test_relay_node_field.py` pins it. No code
  change: the key does not round-trip through Django itself
- [x] 676. A naive datetime id on a `DateTimeField` key is read aware in the default zone as Django binds it, with no
  warning (`utils/querysets.py::column_python_value`), and `identity_key` keys an aware datetime by its instant, so
  `node`, `nodes` and relation ids find the row across DST; an out-of-range id answers null. Tests:
  `tests/utils/test_querysets.py`, `tests/test_relay_node_field.py`
- [x] 682. FK-id elision fires into a type listing its relation primary key:
  `types/definition.py::origin_has_custom_id_resolver` / `has_custom_id_resolver_for` (`pk_is_relation`) ignore the
  framework-installed relation resolver, so `profile { id }` reads the stored key with no JOIN. Tests:
  `tests/types/test_definition_relations.py`, `tests/optimizer/test_walker.py`; spec-015
- [x] 693. The filter ask's params-wide rules read only what the leaf's own lookups bind: `filters/sets.py::
  _unbindable_predicate` runs `refuses_utc_offset`, `refuses_numeric_format` and `psycopg_refuses_list_parameter` over
  each `_bound_value_lookups` lookup's `process_rhs` params, as the integer rules do, so a constant inside a consumer
  annotation the leaf goes through never refuses the user's value, while the user's own past-rule value is still
  refused. spec-027, the `filterset` glossary term and the `utils/errors.py` docstrings say so. Tests:
  `tests/filters/test_sets.py`
- [x] 699. The absent-leaf verdict is request-wide (`FilterSet._probed_filterset`, reused by arms in `_q_for_branch`),
  so an arm never derives an unawaited hop, and a filter-path `SyncMisuseError` names `FilterSet.apply_async`
  (`_FILTER_ASYNC_RECOURSE`). Tests: `tests/filters/test_sets.py`. Arm-only absent leaves are row 700
- [x] 685. A fractional number on an integer column names no row: `utils/querysets.py::truncates_to_integer` checks
  integrality, `coerce_field_value_or_none` answers None, and `filters/base.py::IntegerInFilter` drops it, so
  `signed_big__in=1.5,2` drops the member instead of truncating it. Tests: `tests/utils/test_querysets.py`,
  `tests/filters/test_base.py`. Comparison leaves are row 701; a huge negative decimal's cost is row 673
- [x] 700. `FilterSet.apply_async` awaits the hops of an absent leaf only an arm asks about: `_probe_logic_arms`
  probes every `and` / `or` / `not` arm inside `_probed_filterset` and `_q_for_branch` reuses the probed sibling
  (`_ProbedArm`), so a consumer `__init__`, form `clean` and filter body run once per arm on both colors. Tests:
  `tests/filters/test_sets.py`; spec-027
- [x] 702. Both colors answer the same first error for a filter input carrying several: `apply_sync` derives every
  `and` / `or` / `not` arm's related branches in tree order before the permission pass and form validation, as
  `apply_async` does (`FilterSet._iter_logic_arms`, read by `_collect_nested_visibility_querysets_sync` and its async
  twin), so an arm branch's `FILTER_INVALID` answers before an arm or root form error or a permission denial on both,
  and the depth cap raises from the same set. spec-027 says so. Tests: `tests/filters/test_sets.py`,
  `examples/fakeshop/test_query/test_library_api.py`
- [x] 701. Documented, not changed: on raw form data integer comparisons truncate a fractional value toward zero as a
  stock `NumberFilter` does (`gte=1.5` matches 1), while an `in` member is dropped (685); GraphQL `Int` refuses a
  fraction first. Pinned by `tests/filters/test_sets.py::test_integer_comparison_truncates_a_fractional_value`
- [x] 679. Ordinal citations outside 629's six files name their contract: `_strawberry_patches.py`'s three gaps by
  content, and the plan-section labels, `#N` tags, "Test-6" and "DoD item N" tags in tests by what they pin. Comments
  and docstrings only; ASTs and node ids unchanged
- [x] 574. fixed: a `DjangoModelFormMutation` `required=False` field over a `blank=False, null=False` non-text column
  cleaning to `""` answers the column's field-keyed `null` error instead of the masked save error
  (`_is_unstorable_blank` keys on storage, not `blank`); `JSONField` / `HStoreField` are never named. Pinned by
  `tests/forms/test_resolvers.py::test_is_unstorable_blank_names_only_a_column_that_stores_no_empty_string`
- [x] 696. A refused `ModelForm` save reports a field-keyed `null` only for a column the save of `form.instance`
  writes: `utils/write_values.py::attempted_saves` (shared with the serializer witness) records `update_fields`, which
  `forms/resolvers.py::_unstorable_cleaned_fields` passes on, so a narrowed or pre-save failure answers the constraint
  envelope. Tests: `tests/forms/test_resolvers.py`; spec-038
- [x] 387. Already fixed by dry item 92 (dry-0_0_15_3): `filters/inputs.py::_build_input_fields` types each leaf
  through `filters/base.py::_filterset_value_field`, so a generated `year` / `iso_year` leaf takes `Int`, `time`
  `Time`, `date` `Date`, and filters by the value sent. Pinned live by
  `examples/fakeshop/test_query/test_scalars_filter_api.py::test_generated_year_leaf_is_typed_by_the_transforms_output`
  and `::test_generated_iso_year_time_and_date_leaves_filter_by_the_value_sent`
- [x] 563. Package comments, docstrings and strings state the invariant where they narrated history (about 107 sites);
  the renamed gate
  `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_carries_a_provenance_phrase` reads
  every package runtime string and refuses 11 more phrases. Docstring-stripped ASTs unchanged
- [x] 565. Optimizer plan labels (O1-O6, B1-B8, G1-G3) no longer tag .py prose or test names (about 83 sites, 14 tests
  renamed);
  `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_carries_an_optimizer_plan_label`
  refuses one in prose and def / class names. Specs, the board and BACKLOG keep the labels
- [x] 620. fixed: a `DjangoModelFormMutation` write over a `null=True` column whose form field cleans `None` to a
  value (`[]`, `False`) stores `NULL` for an explicit `null` and keeps a stored `NULL` on omission
  (`forms/resolvers.py::_coerced_null_fields`, `_store_nulls`; text `""` kept, Waiting 262). Not yet run on
  PostgreSQL: `tests/forms/test_resolvers.py::test_modelform_null_on_a_nullable_array_column_stores_null` needs a
  `postgres.yml` run
- [x] 621. fixed: a value a `MultiWidget`'s `decompress` cannot split (a hook rebinding a datetime as text) is a
  `ConfigurationError` naming the key and part keys, raised at bind with nothing written, instead of Django's raw
  `AttributeError`; `utils/widgets.py::widget_entries` splits through `_decompressed`. Live rows in
  `test_scalars_mutation_api.py`, `test_filter_widget_binding_api.py`, package rows in `tests/utils/test_widgets.py`;
  spec-038
- [x] 624. fixed: the `date__range` lone bound was already right at HEAD (7bd478bf); a package `RangeFilter` whose
  `lookup_expr` ends on a transform (`date`, `year`, ...) now applies a lone bound through it
  (`filters/base.py::_lookup_lhs_path`), where it hit the bare column and dropped rows or answered `FILTER_INVALID`;
  an unwalkable `lookup_expr` is `LookupValidationError`. Two bounds unchanged (Waiting 316). Live rows in
  `test_scalars_filter_api.py`; spec-027
- [x] 625. not a defect: no contract row names a package `ListFilter`'s lookup, so one keeping `exact` or `gte` hands
  the whole list to it as graphene-django does (0 rows, masked `TypeError`); `in`, a two-element `range` and `method=`
  answer right, and bare CSV declarations run as plain django-filter (507 and 516). Whether to default `in`, refuse,
  or reinterpret is Waiting row 716, beside 316
- [x] 524. fixed: a `DjangoModelFormMutation` update keeps each omitted column at its stored value where the form
  field's own cleaning rewrote it (a stripped text, a midnight, `""` for `NULL`):
  `forms/resolvers.py::_omitted_column_values` snapshots, `::_keep_omitted_columns` restores; a hook- or clean-set
  value is written. Pinned by `test_scalars_mutation_api.py::test_update_omitting_a_column_keeps_its_stored_value`,
  `tests/forms/test_resolvers.py`; spec-038. Closes 711's and 262's omitted halves
- [x] 711. fixed with 524 for the omitted case: an update omitting `payload` through fakeshop
  `updateNullableScalarSpecimenViaForm` keeps a stored JSON object or list
  (`test_scalars_mutation_api.py::test_update_omitting_a_column_keeps_its_stored_value[json-object|json-list]`).
  The `str()` of a `payload` the client sends is item 720
- [x] 527. fixed (the `ListFilter` / `ArrayFilter` half; `RangeFilter` on a relation stays, item 375): a declared list
  filter over a relation cleans each element as the target column the relation compares on
  (`filters/base.py::_compared_value_column`), so a junk raw element is the form's 400 instead of a 500, and
  overflowing or fractional `in` elements drop (`::_integer_in_column`). Live rows in `test_raw_filter_forms_api.py`,
  package rows in `tests/filters/test_base.py`; spec-027
- [x] 530. fixed (PostgreSQL half; SQLite's nearest-double storage documented): a decimal its validators accept but
  PostgreSQL `numeric` refuses is refused before the write on every flavor as the field's `invalid` error, nothing
  written, instead of a masked `DataError`, via `utils/errors.py::unstorable_value` (new `unstorable_decimal`). Tests:
  `tests/utils/test_errors.py`, `tests/{mutations,forms,rest_framework}/test_resolvers.py`; the live `pg` row is unrun
  locally
- [x] 537. A `method=` filter whose form field is built only per request (`AllValuesMultipleFilter`) is typed from its
  `field_name` column instead of refused at build, and the per-request form field validates each value before the
  method runs (`filters/inputs.py::_refuse_method_without_form_field`). Live rows in `test_library_api.py`, package
  rows in `tests/filters/test_inputs.py`; spec-027
- [x] 538. A declared choice filter whose form field accepts no member of its column's enum (`DateRangeFilter`, a
  disjoint `choices=`) refuses the schema with `ConfigurationError` naming the column
  (`filters/inputs.py::_refuse_choices_off_the_column`) instead of answering every value `invalid_choice`; leaf
  refusals name the declaration via `_declaration_subject`. Live rows in `test_filter_declarations_api.py`, package
  rows in `tests/filters/test_inputs.py`; spec-027
- [x] 656. Not a defect on main: already fixed by dry-0_0_15_3 item 77 (commit 7bd478bf): a list filter over an
  `ArrayField` is typed from its `base_field` (`filters/inputs.py::_array_element_column`) and other filters over the
  column are refused at build. Pinned by
  `tests/filters/test_inputs.py::test_an_array_column_filter_is_typed_from_its_element_column`. No code change
- [x] 673. A decimal a filter's form cleans past an integer column's range (`"-1e1000000"`) was converted with `int()`
  in quadratic time (`MemoryError` at `1e18`); it is now held to the integer one past the range end and compared,
  never converted, keeping every prior answer (`filters/sets.py::_held_integer_value`,
  `filters/base.py::_held_column_value`, `utils/errors.py::integer_past_range`). Live rows in
  `test_raw_filter_forms_api.py`, package rows in `tests/filters/test_sets.py`; spec-027
- [x] 680. `filters/inputs.py::_is_declared_head`'s docstring no longer says a set borrowing the same filter object
  restamps it: since 596 a class-body filter another set owns is deep-copied before it is stamped, and a
  `get_filters()` override sharing an object writes nothing to it. It now states why the child set's declarations
  answer rather than the copy's provenance stamp (`origin="declared"` says a consumer owns the object, not which set
  declares it). Docstring only; pinned by
  `tests/filters/test_sets.py::test_a_borrowed_expanded_copy_is_its_borrowers_own_filter`
- [x] 681. A value a write flavor's own validation makes unstorable (a `clean()`'s aware datetime on a `DateField`)
  answers the field's `invalid` "Enter a value the database can represent.", nothing written, instead of the masked
  error (`forms/resolvers.py::_bound_form_or_field_errors`, `mutations/resolvers.py::_unstorable_cleaned_errors`); a
  `SplitDateTimeWidget` value outside years 1..9999 in the current zone is `invalid` too. Live rows in
  `test_scalars_mutation_api.py`, `test_filter_widget_binding_api.py`
- [x] 683. Not a defect: spec-015 Decision 3 leaves both node defaults without an optimizer pass
  (`types/relay.py::_resolve_nodes_default`), so FK-id elision never runs under a node root, the same call as 607. The
  capability decision stays under Waiting item 327
- [x] 684. Already fixed on main by 7bd478bf: `filters/base.py::_column_form_field` reads `_bound_value_field`, so a
  declared `ListFilter` / `RangeFilter` with a transform in `lookup_expr` cleans each member as the transform's output
  (`"2020"` matches, `"abc"` is "Enter a number."). Pinned by
  `tests/filters/test_sets.py::test_declared_filter_through_a_lookup_expr_transform_cleans_values_as_its_output`.
  Residuals filed as 758 and 759
- [x] 688. Already fixed on main by 7bd478bf, pinned here: a declared `year` `ListFilter` / `RangeFilter` cleans
  members as the transform's integer output (`filters/base.py::_column_form_field`), so `"2021.0"` selects the
  `"2021"` rows. Live rows in `examples/fakeshop/test_query/test_scalar_predicate_binding_api.py`. No production
  change. Filed 760
- [x] 692. A `ListFilter` / `ArrayFilter` over an `ArrayField` cleans every member as the innermost column at any
  depth (`filters/base.py::_column_form_field`, `::_ElementField`), and under `ArrayInLookup` each member is one whole
  array (a non-list member is `invalid_list` where `.qs` raised `TypeError`); `LICENSE.django` now ships. Pinned in
  `tests/filters/test_sets.py`; the live PostgreSQL rows are unverified until the PostgreSQL tier runs them. Filed 761
  and 762
- [x] 695. A save-time failure is diagnosed only from the save that raised it:
  `utils/write_values.py::attempted_saves` records each save's frame and `::refused_save` picks the innermost one on
  the exception's traceback or cause (all three flavors); any other failure answers the `"__all__"` `constraint`
  envelope. Pinned by `examples/fakeshop/test_query/test_save_time_refused_row_api.py`. PostgreSQL rows unverified.
  Bundles 707; filed 764
- [x] 706. Not a defect (GOAL "Trust boundary", spec-038 Decision 8 step 5 "the refused save of the form's instance"):
  a field-keyed error claims the client's input field, and only `form.instance` is established as built from it
  (`ModelForm._post_clean`); a row a consumer `save()` builds and returns is the consumer's, so its refusal is the
  envelope. `tests/forms/test_resolvers.py::test_modelform_save_time_null_is_read_from_the_refused_row_only` pins it.
  No code
- [x] 707. One rule: `utils/write_values.py::refused_save` is the row picker every flavor calls; each keeps its spec's
  row scope (model target, `form.instance`, any serializer backing-model row). Landed with 695
- [x] 703. Spec-section ordinals in first-party prose are restated by content or as the gated `spec-NNN Decision N`:
  `optimizer/nested_planner.py::plan_connection_relation`, the `orders/sets.py` module and `OrderSet` docstrings,
  `_cross_web_patches.py` (named gaps: the undecodable body, the transport asymmetry),
  `filters/sets.py::FilterSet.filter_queryset`, `mutations/resolvers.py::CleanExcludes` and
  `rest_framework/sets.py::SerializerMutation.get_serializer_kwargs` (a dangling spec-039 step), and test prose in
  `test_relation_connections_api.py`, `tests/test_connection.py`, `test_connection_fields_api.py` and
  `test_multi_db.py`; the retired capture script needed nothing (f9dc0724). `OrderSet`'s false "no sync-misuse path"
  claim is corrected (`apply_sync` lets an async-only related target's `SyncMisuseError` out directly), with spec-028
  DoD 4(c) and a new Edge-cases row. New gate
  `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_cites_a_spec_section_by_number`
  refuses DoD / Goal / Slice ordinals (live `TODO(spec-NNN slice N)` anchors exempt), with planted and permitted-form
  rows; START names it. Stripped ASTs and node ids otherwise unchanged. Filed 766, 767
- [x] 704. fixed: a `DjangoModelFormMutation` form field cleaning a client's explicit `null`, or a create's omission
  (nothing bound under any key its widget reads) of a `null=True` column with no `default`, to a value (a consumer
  `CharField`'s, `ChoiceField`'s or `TypedChoiceField`'s `""` over an integer, float, decimal, date, time or UUID
  column included) stores `NULL` before the save instead of the false "This field cannot be null."
  (`forms/resolvers.py::_is_unstorable_blank` gains the `null=False` gate; `::_coerced_null_fields` names the create
  omission through `::_binds_nothing` and `::_omission_stores_null` and reads a `null=True` column's instance through
  `::_holds_own_cleaning`); a `""` consumer code sets on a `null=True` column the save refuses answers the column's
  own `to_python("")` `ValidationError` (code `invalid`, Django's message), keyed like the `null` error
  (`::_blank_type_errors`, `::_unstorable_column_errors`), and names no column where `to_python` raises nothing or
  another type. Live rows in `examples/fakeshop/test_query/test_scalars_mutation_api.py` (the fakeshop flag form
  gains `score`), package rows in `tests/forms/test_resolvers.py`; spec-038, GLOSSARY. PostgreSQL array rows unrun
  locally. Filed 768
- [x] 631. decided with 704: client input (explicit `null`, create omission) on a `null=True` column stores `NULL`
  before the save (no retry); a `""` consumer code sets there is the column's own `to_python` refusal (`invalid`),
  never `null`
- [x] 705. fixed with 704: the GLOSSARY `djangomodelformmutation` and `fielderror-envelope` entries scope the
  save-time `null` mapping to `null=False` (`blank=True`, or `blank=False` behind a consumer `required=False` field)
  and state the `null=True` answers
- [x] 710. fixed with 704: a create omitting a `null=True` column with no `default` stores `NULL` whatever its form
  field cleans the absent key to (a checkbox `False`, a JSON `""`, `[]`, `{}`, a `TypedChoiceField` empty value); a
  value a hook binds under the widget's own keys is written, and a column with a `default` keeps Django's handling
- [x] 717. fixed with 704: on a `null=True` column a model `clean()` value the instance holds in place of the form
  field's own cleaning is written, never replaced by `NULL` (`forms/resolvers.py::_holds_own_cleaning`); the parity
  pin
  `tests/forms/test_resolvers.py::test_update_omitting_an_empty_column_a_model_clean_fills_never_converts_it[null-true]`
  now expects the model's value
- [x] 708. fixed: a declared or `Meta.filter_overrides` filter applied to its column with no transform whose own form
  and lookup answer no value of the column (a `TimeFilter` on a `DateTimeField`, a `UUIDFilter` or `DurationFilter` on
  an integer column, a `BooleanFilter` on a date) is refused with `ConfigurationError` when the schema is built,
  naming the declaration, the column, the form field and the lookup
  (`filters/inputs.py::_refuse_form_serving_no_value`: each sample of the published scalar, or every member of the
  published choice enum, through the filter's own `field.clean` with validators and `validate` off and its own
  `filter` on a fresh queryset of the declaring set's model, `::_answers_sample`; preparation errors shared with
  `_unbindable_predicate` as `filters/sets.py::_PREPARATION_REFUSALS`). Not asked: generated, `method=`,
  `filter`-override and consumer-parser leaves, a column (a relation through the keys it points at,
  `::_django_converts`) converting in its own `to_python` / `get_prep_value`, a lookup preparing in its own
  `get_prep_lookup`; a lookup no field registers is not judged; a `RelatedFilter` copy is asked on its child set
  (`_LeafDeclaration.filterset`). 418 grid cells refused (411 failing every value, 7 matching every row); every
  working, partial and warning cell builds. Package rows in `tests/filters/test_inputs.py`; spec-027, README, GLOSSARY
  `FilterSet`. PostgreSQL columns unrun locally. Filed 770, 771, 772, 774
- [x] 733. A declared filter publishing a value kind its own form refuses for every value: duplicate of 770 (the
  `NumberFilter(lookup_expr="isnull")` half) and 772 (the `AllValuesMultipleFilter(lookup_expr="year")` half)
- [x] 709. fixed: a `FilterSet` a connection serves (a root `DjangoConnectionField`, a nested `<relation>Connection`,
  and every set reached through a `RelatedFilter` branch the set's published filter table still holds or a flat copy
  the schema publishes, each judged on itself) is refused with `ConfigurationError` when the schema is built if a
  leaf's lookup path resolves to a transform or lookup class that is not Django's own, naming the declaring set, the
  filter, the path it is reached through, the lookup and the class, with the remedies
  (`filters/inputs.py::_refuse_unsealable_served_leaves`, run by `types/finalizer.py::_audit_filterset_subpass_2_5`;
  served sets recorded by `connection.py::_synthesized_signature`, which refuses a connection declared after finalize
  itself; hidden copies read through `filters/inputs.py::_is_hidden_flat_copy`, shared with the input builder). The
  predicate is `utils/querysets.py::_type_is_genuinely_django` itself and the classes are Django's own
  `get_transform` / `get_lookup` walk (`utils/relations.py::_LookupWalk`, reverse relation keys included); a leaf
  whose `filter` is consumer code on its own set is left to the request seal, which is unchanged. `"__all__"` leaves
  out every lookup class that is not Django's own on every set (`filters/sets.py::_lookups_for_field`). A set no
  connection serves keeps building and answering through `FilterInput[...]` + `apply_sync`; a served set the project
  also applies from its own resolver is refused (GOAL "Trust boundary"). 65 sealed grid cells refused at build, 118
  working cells unchanged. Package rows in `tests/filters/test_finalizer.py` and `tests/filters/test_all_lookups.py`;
  README, spec-027, spec-045 and its rationale, GLOSSARY `FilterSet` and prove-then-clone. `django.contrib.postgres`
  lookups typed only, unrun. Filed 776
- [x] 714. (robustness) fixed: a `FilterSet` declaring no `Meta.model` named as a `DjangoType`'s
  `Meta.filterset_class` is refused with `ConfigurationError` when it binds at `finalize_django_types()`, naming the
  set, the owner type, its model and the remedy (`Meta.model`, with `Meta.fields = []` for declared filters only):
  `types/finalizer.py::_bind_filterset_owner`, spec-027 Decision 4's owner-model rule, which the common binder skipped
  for a `None` model. It built and published an input every request refused (36 of 36 grid requests). Serving it
  instead (django-filter / graphene-django shape, absent from strawberry-graphql-django) walked no relation visibility
  and skipped the build refusals a backed set gets. A model-less base set still builds; a model-less unbound set
  applied with a leaf names the missing `Meta.model` (`filters/sets.py::FilterSet._leaf_form_entries`) and its
  `RelatedFilter` branches still apply; a model-less related-only `OrderSet` stays a legal `Meta.orderset_class`
  (spec-028). The now-unreachable `model is None` arm of `FilterSet._is_own_pk_under_relay_owner` is gone. Tests:
  `tests/filters/test_finalizer.py`, live `test_filter_apply_arguments_api.py` and `test_order_apply_arguments_api.py`;
  spec-027, spec-028, README, GLOSSARY `FilterSet` and `Meta.filterset_class`. Filed 777

- [x] 776. fixed: a declared filter running a shipped `filter` (not `method=`, not a `filter` override) whose
  `field_name` and `lookup_expr` Django resolves on no queryset is refused with `ConfigurationError` when its set
  publishes its filters: at schema build for a set a type serves (root, nested `<relation>Connection`,
  `RelatedFilter`-reached, bound for `FilterInput`), at first use for an unbound set
  (`filters/base.py::refuse_unresolvable_lookup`, called from `filters/sets.py::FilterSet._publish_filters` beside
  `refuse_identityless_relation`). The predicate asks Django's own split and walk over a fresh `Query` of the model
  (`filters/base.py::_unresolvable_lookup`: `utils/querysets.py::split_lookup`,
  `utils/relations.py::lookup_transform_parts`, `lookup_target_fields`), uncached: a path ending on a column whose
  walk refuses the leftover is refused (`signed_big__gt`, `occurred_at__year__gt`, `parent__label__icontains`); a
  to-one key is asked on the relation's own lookups (`parent` + `icontains`), a range filter applying its bounds as
  `gte` / `lte` asked `gte` (`filters/base.py::_BOUNDED_RANGE_FILTERS`), the package `RangeFilter` on its resolved
  column path; a to-many key is refused only when every key column its join compares and the target pk refuse too.
  Not judged: a first name the model lacks (a queryset annotation, a `FilteredRelation` alias), a name past a
  relation (a walked hop reads it on rows a type's `get_queryset` annotates), a model-less set (714's refusals). A
  lazy `field_name` / `lookup_expr` is read as its text. Raw `FilterSet(data=...)` keeps django-filter's
  `FieldError`. A queryset alias spelled `<own column>__<lookup>` and a lookup registered after the set publishes are
  refused by design. 24 grid cells plus forward key `icontains` refused in every serving shape, every working cell
  unchanged. `filters/inputs.py::_answers_sample`'s `FieldError` arm is gone. Tests:
  `tests/filters/test_finalizer.py::test_a_declared_leaf_django_resolves_on_no_queryset_is_refused` and its
  registration, lazy, name-past-a-hop, reverse-key and range-bounds rows, `test_a_served_leaf_the_build_does_not_walk_builds`;
  live `test_declared_key_primitives_api.py::test_an_integer_range_over_a_forward_key_applies_its_bounds_through_the_relation`;
  spec-027, README, GLOSSARY `FilterSet` and `ConfigurationError`. Filed 779, 780
- [x] 774. fixed with 776: a declared `lookup_expr` no field registers (`unaccent` without `django.contrib.postgres`)
  is refused by `filters/base.py::refuse_unresolvable_lookup` when its set publishes, naming the lookup and the field;
  the build pin moved to `tests/filters/test_inputs.py::test_a_declared_lookup_no_field_registers_is_refused_before_its_form_is_asked`
- [x] 719. fixed: a `DjangoModelFormMutation` update keeps a `disabled` field's column at its stored value whether
  the input omits the field or sends a value Django ignores. The keep-stored check read Django's presented initial
  (`BaseForm.get_initial_for_field` zeroes microseconds under `DateTimeInput` / `TimeInput` / `SplitDateTimeWidget`,
  django-trac 22502) against the raw stored value, so an omitted disabled `DateTimeField` / `TimeField` lost its
  microseconds; and only omitted names were checked, so a sent disabled field wrote the cleaning of its initial
  (stripped text, `""` for `NULL`). `forms/resolvers.py::_set_initial` asks the form's own `get_initial_for_field`
  for a field copy whose widget keeps microseconds; `::_omitted_column_values` reads every disabled non-file column
  on an update and `::_keep_omitted_columns` compares it to the instance's stored value. An initial consumer code sets
  (`initial=`, `__init__`, a `get_initial_for_field` override) is still written; a disabled file field stays out
  (its cleaning is the stored file, and checking it would read storage again). Live
  `test_scalars_mutation_api.py::test_update_through_disabled_fields_keeps_their_stored_values` (sync, async, omitted,
  sent) over the new fakeshop `updateScalarSpecimenViaLockedStampForm`; package rows in
  `tests/forms/test_resolvers.py`; spec-038, README, GLOSSARY `DjangoModelFormMutation`

- [x] 780. fixed: a declared filter on a to-many relation key (reverse FK, many-to-many either way,
  `GenericRelation`) answers only what Django answers for its declaration, walked hop or not. A lookup the relation's
  last join does not register (`icontains`, `startswith`, `iexact`, `regex`, a whole `range`) is refused when the set
  publishes: `filters/base.py::_unresolvable_lookup` asks every relation on `split_lookup`'s join field (776's
  to-many key-column loop gone; the range-as-`gte` rewrite applies to every relation), and the refusal names the
  related column to spell past the relation (`children__id`, `filters/base.py::_related_column_hint`). A raw
  `FilterSet(data=...)` raises Django's own `FieldError` walked or not: `filters/sets.py::_LeafChain.terminal_value`
  first builds the declared predicate, without SQL, for shipped `filter` code (`_ToManyKey`; a class-level consumer
  override runs once, as unwalked). The same build makes a model-choice `in` on a text key raise Django's `TypeError`
  instead of matching rows by the key's characters. 610 walked/unwalked grid cells disagreeing went to 0; no cell
  answering unwalked stopped answering. Tests in `tests/filters/test_finalizer.py`
  (`test_a_declared_leaf_django_resolves_on_no_queryset_is_refused`,
  `test_a_raw_to_many_key_lookup_the_relation_refuses_raises_djangos_error`, the any-class, text-key `in`, range,
  lazy and `test_a_class_level_override_on_a_to_many_key_runs_once_per_request` rows); spec-027, README, GLOSSARY
  `FilterSet`. Filed 783, 784
- [x] 720. (robustness) fixed: a `ModelForm` field that reads one value (`CharField` family, `ChoiceField`,
  `IntegerField`, `BooleanField`, ...) over a `JSONField` listing no choices that converts nothing it is handed is typed
  by the form field (`String`, `Int`, `Boolean`), as graphene-django types form inputs and as the package's filters
  over such a column already were; it was typed `JSON`, so a decoded object sent to a `CharField` was stored as its
  Python text (`"{'a': 1}"`), a `BooleanField` stored the truthiness of an object, and a field reading JSON text raised
  `JSONDecodeError`. A non-string sent to a `String` is now GraphQL's coercion error (a wire-type change before 1.0).
  An update omitting such a field binds the form's presentation of the stored value (`prepare_value` of its initial),
  and the keep-stored restore compares against it, so a plain `CharField` keeps a stored object and a JSON-text field
  partially updates over one; a choice column keeps its choice enum. `forms/inputs.py::_reads_one_value_of_held_json`,
  `::held_json_column`, `forms/resolvers.py::_bind_omitted_json_presentations`, the column predicate moved to
  `types/converters.py::holds_values_as_given`. Live rows in `test_scalars_mutation_api.py` over fakeshop
  `NullableScalarSpecimenFlagForm` (its `payload` now `String`) and the new `NullableScalarSpecimenJsonTextForm`
  mutations; package rows in `tests/forms/test_inputs.py` and `test_resolvers.py`; spec-038, spec-027 citations, README,
  GLOSSARY `DjangoModelFormMutation`. Filed 786 and 787

- [x] 784. fixed: a class-level `filter` override on a relation key a flat leaf walks (to-many at any hop count, a
  forward key two or more relations away) runs once as declared, with its own `field_name`, the value its form
  cleaned (model instances, not pks) and the declaring set's rows, as unwalked, and keeps only the parents that reach,
  through each hop's visible rows, a visible last-hop row its value names (every one for `conjoined`; a raw key or
  GlobalID named through the leaf class's nearest shipped `filter` on the column Django's relation lookup compares, a
  non-pk `to_field` included). So a `value.pk` reader no longer raises walked, a hardcoded-path override answers its
  unwalked rows, `icontains` raises Django's `FieldError` walked as unwalked, and a hidden named row matches nothing.
  A value naming no row of the target (an empty, `null` or absent model-choice value, instances of a model the
  relation does not accept per Django's `check_rel_lookup_compatibility`, a raw or GlobalID value the shipped
  comparison skips or refuses) and an `isnull` override run over the visible related rows exactly as before
  (`FilterSet._request_chain`, `_LeafChain.fallback`). The value names the rows the override keeps (`exclude=True`
  negates, applied at the parent); a path the override's own Python reaches beyond its value is its own scoping, as
  for `method=`. Changed `filters/sets.py::FilterSet._leaf_chain`, `::FilterSet._apply_relation_leaf`,
  `::FilterSet._absent_leaf_applies`; new `::FilterSet._request_chain`, `::FilterSet._reaches_key`,
  `::FilterSet._folded_key_chain`, `::_KeyMatch`, `::_model_choice_members`, `::_shipped_filter_class`,
  `::_defines_shipped_filter`, `::_SHIPPED_COMPARISON_REFUSALS`. Grid: 0 regressions, 0 hidden-row leaks, query
  counts unchanged. Pinned by `examples/fakeshop/test_query/test_relation_key_overrides_api.py` (sync, async, form,
  nested and flat child); spec-027, README, GLOSSARY `FilterSet`. Filed 789, 790
- [x] 721. (robustness) fixed, the crossing half: a declared filter whose `lookup_expr` continues across a relation
  (`ListFilter("shelf", lookup_expr="tier__in")`, `("venue", "opened_on__year__in")`) is typed and cleaned as the
  column the path Django walks reaches, on every driver and under a stock django-filter parent, so a junk raw element
  is the form's error and an out-of-range one names no row, where they were Django's `ValueError` / `OverflowError`
  (a 500). `filters/base.py::_filterset_walked_lookup` asks Django's own path walk (`utils/querysets.py::split_lookup`,
  cached per model) at read time; the filter object keeps its declared `field_name` / `lookup_expr` and the published
  input key keeps the declared token. The `FilteredRelation` alias half is item 792. Tests:
  `tests/filters/test_base.py`, live `test_crossing_lookup_filters_api.py`, `test_raw_filter_forms_api.py`; spec-027,
  README, GLOSSARY `FilterSet`
- [x] 749. fixed with 721: the flat-leaf walk, gates, terminal, captured-branch check, GlobalID target and the
  finalizer's GlobalID audit read the walked path (`FilterSet._flat_leaf_walk`, `::_leaf_gates`, `::_bound_terminal`,
  `::_filter_paths`, `types/finalizer.py::_audit_globalid_filter_strategies`), so a crossed hop is scoped by its target
  type's `get_queryset` and gated as its `field_name="<rel>__<col>"` spelling is (a restricted branch no longer matches
  for anon), a gate fires on the compared column, and a to-many crossing answers valid input instead of `FieldError`.
  A class-level `filter` override on a column crossing runs on the walked per-request copy; one ending on a relation
  key runs once as declared (784's rule); a `method=` filter reads its pair as declared. A crossing leaf entering a
  longer sibling `RelatedFilter`'s continuation is refused at build, as its joined spelling is; a GlobalID crossing
  validates the crossed relation's type. Tests: `tests/filters/test_sets.py`, `test_finalizer.py`,
  `tests/test_sets_mixins.py`, live `test_crossing_lookup_filters_api.py`. Filed 792 and 793
- [x] 797. fixed: a declared hop's target `get_queryset` runs once per request however many nested branches (at every
  level), logical arms and flat leaves walk it. `filters/sets.py::FilterSet._declared_hop_rows` /
  `FilterSet._await_declared_hop_rows` are the one derivation, keyed `(id(<RelatedFilter>), alias)` in the request hop
  map `FilterSet.apply_sync` / `FilterSet.apply_async` create before the first nested derive and hand each nested
  child's `apply_*` (private `_hop_visibility`); `FilterSet._derive_related_visibility_querysets_sync` / `_async`,
  `FilterSet._hop_visible_rows` and `FilterSet._await_hop_visibility_async` read it, and `FilterSet._iter_visibility_steps`
  yields each branch's declaration (`FilterSet._branch_visibility_seed` raises the unresolved-target error). Rows and
  errors are unchanged; a declared hop and an undeclared relation to one type stay two hops; projection children read
  no hop (spec-027 corrected). Tests: live
  `test_relation_filter_defaults_api.py::test_one_declared_hop_runs_its_target_scope_once_however_many_branches_and_leaves_walk_it`
  (sync, async, async-only hooks; exact statement counts), `tests/filters/test_sets.py::test_each_arm_branch_derives_once_on_both_colors`
  (one run for four arms)
- [x] 796. fixed: a class-level `filter` override on a to-many relation key a flat leaf walks, whose value names no row
  of the target (empty, `null` or absent, a value the shipped comparison skips or refuses, instances or a key of another
  model), runs once as declared over its own set's rows with its `field_name` bound to a chained `FilteredRelation`
  alias of its relation (`<segment>_visible`, numbered past a name the query or the model holds) whose joins admit only
  each hop's visible rows, its intermediate models' visible rows and its `RelatedFilter(queryset=...)` rows, a
  many-to-many joining its through rows by an alias conditioned on the visible targets, and its `lookup_expr` the walked
  lookup. So instance, queryset and single-instance defaults, `<field_name>__pk__in`, `<field_name>__<column>`, a
  crossing `lookup_expr` and `<field_name>__isnull=True` answer as unwalked over visible rows (they were a masked
  `TypeError` / `Unsupported lookup` or hidden-row dependent), another model's key raises Django's own `ValueError` as
  unwalked (it matched by pk coincidence), and the to-many 795 shape keeps every parent. Forward keys and `isnull`
  overrides are unchanged. A relation the override's own Python names reads every row (stated contract). A many-to-many
  whose through key onto its source Django gives no reverse name of its own (an auto-created self-referential one read
  forward) keeps the re-bound fallback (item 800). A GlobalID copy resolves its target from the declared path and
  compares an off-pk `NodeID` through the alias. Changed `filters/sets.py::FilterSet._leaf_chain`,
  `::FilterSet._apply_relation_leaf`, `::FilterSet._absent_leaf_applies`, `::_LeafChain` (`view`); new
  `::FilterSet._relation_view`, `::_free_alias`, `::_through_link`, `::_names_every_through`;
  `filters/base.py::_globalid_target`, `::_globalid_predicate_path`, new `::_RelationView`, `::_relation_view_of`.
  Pinned by `examples/fakeshop/test_query/test_relation_key_overrides_api.py` (names-no-row rows sync, form and async;
  off-key NodeID; a declared hop over two relations with `queryset=` and an `and_` arm; connection count, order and
  pages) and `tests/filters/test_sets.py` (`_free_alias` over a model field, `_through_link`, the unnameable-through
  fallback); spec-027, README, GLOSSARY `FilterSet`. Filed 799, 800, 801
- [x] 801. not a defect (AGENTS defect rule: no contract row). Rows never multiply: an `OrderSet` order over a to-many
  path is a `Min` / `Max` annotation grouped per parent (`orders/sets.py::OrderSet._resolve_order_expressions`, spec-028
  Decision 12), so `totalCount`, paging and node counts held in all 144 live cells (Branch `shelves`, Book `genres`;
  walked, unwalked, hiding). Only the ordering key differs: an unwalked plain filter (a shipped
  `ModelMultipleChoiceFilter`, a key override) shares its join with the order's `Min` by Django's own join reuse and
  sorts by the matched related rows, while a walked leaf, 796's relation view and an unwalked generated column leaf (the
  row-preserving `EXISTS` fold, GLOSSARY `FilterSet`) sort by every visible related row; d7171ad0 answered the same. No
  doc, spec or upstream promises filter-matched ordering (django-filter, django-graphene-filters and strawberry_django
  `order_by` plainly and duplicate parents). The contract question is filed as 803
- [x] 724. (robustness) fixed with 743: the filter form runs the bind ask as its own clean, so a raw `ListFilter` /
  `ArrayFilter` `in` over a `DurationField` (and every other lookup on it) refuses a duration past 64 bits of
  microseconds on SQLite and MySQL with the typed input's "Enter a value the database can represent." (`invalid`),
  never a 500; the over-range member is refused, not dropped, as the generated `in` refuses it, and the integer
  column's drop rule is unchanged. PostgreSQL and Oracle bind a native interval and answer as before. The `in` gate
  (`filters/base.py::_integer_in_column`) is unchanged: widening it cleared only the declared `in` cells and split the
  declared filter from the generated one. Pinned by
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_raw_duration_past_the_backends_range_is_refused_by_the_form`
  (every generated lookup, `ListFilter` include / exclude, `ArrayFilter`, `RangeFilter`, `DurationFilter`,
  `BaseInFilter` + `DurationFilter`, mixed lists, in-range control) and the `tests/filters/test_base.py` DRF 400 /
  `FilterView` strict rows
- [x] 743. (robustness) fixed: the filter form runs the bind ask and the unstorable-text refusal in its own clean
  (`filters/form_binding.py::BindAskingFilterForm`, built by `filters/sets.py::FilterSet.form` through
  `::bind_asking_form_class` with the asks in `::FilterFormAsks`), so `FilterSet(data=...)` `is_valid()` / `errors`,
  `DjangoFilterBackend` (400) and `FilterView` (`strict`: no rows) refuse what the typed input refuses: a year
  comparison past 9999, a duration past the backend's range, a lone surrogate or NUL, with the typed messages; a bare
  `.qs` read of an invalid form applies the leaves that cleaned (none once text is refused), as django-filter's own
  contract. A text refusal skips cleaning through the reset adapted from Django's `BaseForm.full_clean` (identical
  5.2.16 through 6.1.2); an unbound or unchanged empty-permitted form runs Django's own `full_clean`, so a consumer
  `Meta.form` `full_clean` / `clean` runs wherever Django runs it. A form error and a bind refusal are reported
  together (typed `FILTER_INVALID` payload too). A consumer override of the set's `form` property keeps its own raw
  form; `FilterSet._validate_form_or_raise` asks it itself. Changed `filters/sets.py::FilterSet.form`,
  `::FilterSet._validate_form_or_raise`, `::_unbindable_value_errors` (takes the form, returns `ValidationError`s), new
  `::_unstorable_text_errors`, `::_json_errors`. Pinned by
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_raw_form_refuses_what_its_typed_input_refuses`,
  `test_declared_temporal_bindability_api.py::test_a_form_error_and_a_bind_refusal_are_reported_together` and
  `tests/filters/test_base.py` (DRF 400, `FilterView` strict, consumer form override, consumer `full_clean` counts,
  widget reads, unbound, empty-permitted); spec-027, README, GLOSSARY `FilterSet`. Filed 804, 805
- [x] 807. fixed: 796's to-many relation view dropped a parent whose first related row is hidden when the walked path
  starts at a non-null forward key: Django joins that key inner, so the view's condition left the parent out
  (`Book.shelf__alt_branches` under a type hiding a shelf: an empty choice an override reads as
  `alt_branches__isnull=True` lost the book on the hidden shelf). The view now joins such a key round its target when
  the database enforces it, onto a model or a proxy of one (`<fk>_round`: the key, its reverse relation back to the row,
  then the key again, an outer join), so the parent is kept and reads its hidden row as none. A `related_name="+"` key,
  a bare `ForeignObject`, a `db_constraint=False` key and a key onto a multi-table-inheritance child keep the inner join
  (decision 809). Changed `filters/sets.py::FilterSet._relation_view`; new `::_inner_forward`, `::_round_trip`. Pinned
  by `examples/fakeshop/test_query/test_relation_key_overrides_api.py` (`shelf__alt_branches` and the `VisibleBranch`
  proxy `branch__shelves` names-no-row rows, sync, form and async; `ShelfLabel.shelf__books` and
  `KioskFault.kiosk__repairticket` on the inner join) and
  `tests/filters/test_sets.py::test_which_forward_keys_the_relation_view_joins_round_their_target`. Docs: spec-027,
  README, GLOSSARY `FilterSet`. Found researching 799; filed 809
- [x] 725. (robustness) fixed: the form and serializer flavors hold each column before their own validation binds it.
  A form mutation's `is_valid()` runs with per-instance shadows of `form.instance.clean_fields` / `validate_unique` /
  `validate_constraints` (`forms/resolvers.py::_unstorable_values_kept_from_checks`, `::_storability_checked`): each
  runs the write rule on the instance values, adds the field's `invalid` "Enter a value the database can represent."
  with `add_error`, joins the refused name to one set shared by the three (Django 5.2 runs constraints inside
  `full_clean` with its own `exclude`) and to `exclude`, then delegates to the bound original, so a consumer override
  runs once; an omitted or disabled column an update keeps, and a column with no form field, join `exclude` without an
  error. So a `unique=True` / `UniqueConstraint` (single, two-field, conditional, functional) / `unique_together`
  column answers the field error where SQLite's adapter `ValueError` (an aware time under either `USE_TZ`, an aware
  datetime under `USE_TZ = False`) or PostgreSQL's `DataError` (a decimal past `numeric`) escaped as a masked error and
  a conditional constraint answered a wrong `__all__` violation; 681's `except OverflowError` seam in
  `::_bound_form_or_field_errors` is deleted (its causes are refused first; a hook's own exception propagates). A
  serializer mutation wraps each written top-level field's `to_internal_value` and `run_validators`
  (`rest_framework/resolvers.py::_hold_unstorable_values`, `::_unstorable_written_values`), so a value the rule refuses
  fails its field before DRF's `UniqueValidator` / `UniqueTogetherValidator` bind it: a unique duration past 64 bits
  of microseconds and a `validate_<field>` datetime past year 9999 in UTC answered SQLite's `OverflowError`
  (`qs_exists` catches no `OverflowError`), and on PostgreSQL a `DataError` it swallows aborts the transaction
  (unverified). The model flavor was already ordered. New fakeshop `scalars.UniqueScalarSpecimen` (migration 0004, not
  applied to the tracked board DB, as library 0019 / 0020 and products 0004) with form and serializer mutations.
  Pinned by `examples/fakeshop/test_query/test_scalars_mutation_api.py::test_value_a_uniqueness_check_would_bind_is_the_field_error`
  and its pg rows (unrun locally), `tests/forms/test_resolvers.py` (stand-in decimal rows, consumer override counts, a
  `get_form` instance override kept, `clean()` without `super()`, disabled and unfielded columns) and
  `tests/rest_framework/test_resolvers.py` (duration via `SCALAR_MAP`, `validate()` after `is_valid()`, a non-mapping
  `to_internal_value`); spec-038, spec-039, README, GLOSSARY `FieldError` envelope. Filed 810
- [x] 804. fixed: a declared `ListFilter`, `ArrayFilter` or `RangeFilter` (and a `GlobalIDFilter` or key primitive)
  whose path the model names no field for now reads the path over `filter.parent.queryset`, the queryset the set was
  handed, under either parent; the model's walk stays first and the queryset is read only where the model answers no
  field and the filter has no `method=`. Members and bounds over an annotation, a `FilteredRelation` alias (a reverse
  relation's answered as the model answers the relation's own name) or a column past one are cleaned, held, dropped and
  range-rewritten as that queryset compares them: duration values filter and junk is the form's error where HEAD gave
  `AttributeError`, `ValueError` or `OverflowError`, masked over GraphQL; a GlobalID past a key annotation's range is
  `GLOBALID_INVALID`. The schema is unchanged (`String`); a set handed no queryset is unchanged (`FieldError`). New
  `filters/base.py::_bound_lookup_operand`, `::_model_unresolved_query`, `::_bound_query`, `::_query_path_field`,
  `::_query_lookup_operand`, `::_bound_lookup_lhs_path`, `::_query_lookup_lhs_path`; `::_bound_resolved_field` and
  `::_bound_value_field` read the fallback; `::_ElementCleanedFilter._hand_column_field`, `::_integer_compared_column`
  and `::_compared_value_column` read the new root; `filters/sets.py::_queryset_integer_column` rebuilt on
  `_query_lookup_operand`, kept for an annotation a consumer `filter_queryset` adds and answering `None` for a link
  several columns carry. Fakeshop: `ScalarSpecimenParentStampFilter` `parent_lag_*` / `child_count_*` over the
  resolver's annotations. Pinned live by `test_scalars_filter_api.py`, `test_raw_filter_forms_api.py`,
  `test_scalar_predicate_binding_api.py` (the reverse alias and the key annotation included),
  `test_declared_key_primitives_api.py` and `test_filter_apply_arguments_api.py` (`apply_sync` and `apply_async`, a
  target type's `get_queryset` through a `RelatedFilter`), and
  `tests/filters/test_sets.py::test_a_queryset_alias_of_a_multi_column_link_holds_nothing`. Docs: spec-027, README,
  GLOSSARY `FilterSet`. Closes 792's element half
- [x] 726. (robustness) fixed: on SQLite a decimal its column's validators accept but SQLite stores as a value the
  backend's read-back converter refuses is the field's `invalid` "Enter a value the database can represent." on every
  flavor, create and update, nothing written, where the post-write re-fetch (`mutations/resolvers.py::refetch_optimized`)
  raised a masked `decimal.InvalidOperation` from `get_decimalfield_converter` (15-digit rounding, then `quantize`
  under `Context(prec=max_digits)`) and rolled the write back. Two shapes, one root: an infinity (`1E+309` in
  `DecimalField(400, 0)`, any `max_digits >= 309 + decimal_places`) and a double carried past a bounded column's digits
  at capacity (`9999999999999999.9999` in `(20, 4)`, live on fakeshop `ScalarSpecimen.price` and
  `UniqueScalarSpecimen.amount`; any `max_digits >= 16`; on Django 5.2 / 6.0 also an integer past 15 digits, read
  through a float). `utils/errors.py::_refused_read_back`, a branch of `::unstorable_decimal` after `_validated`,
  stores the values in a private in-memory database opened through the backend's own driver under the alias's
  `detect_types` (`get_connection_params`), with the column's `db_type` and `get_db_prep_save`, and reads them back
  through `connection.ops.get_db_converters(column.cached_col)`, catching only `InvalidOperation`: no Django query, the
  write alias never opened. `CAST(... AS NUMERIC)` on the alias was rejected (it answers REAL where the column stores
  INTEGER past 2**51) and so was a `float()` model (SQLite's text-to-double is not correctly rounded near the largest
  double). An unbounded column's `Infinity` read-back stays accepted; a converter the backend cannot build (a digitless
  column below Django 6.1.1) propagates its `TypeError`. A row already holding such a value fails every read selecting
  the column, but only trusted code outside the package writes one (`update()`, raw SQL, `loaddata`) and Django's own
  ORM cannot load it either: not a defect. 727 untouched. Pinned by
  `examples/fakeshop/test_query/test_scalars_mutation_api.py::test_decimal_sqlite_cannot_read_back_is_the_field_error`
  and its unique-amount cells, `tests/utils/test_errors.py` (`::test_unstorable_decimal_refuses_what_sqlite_cannot_read_back`,
  the digitless rows, the zero-statement row, `::test_unstorable_decimal_reads_back_under_the_alias_detect_types`,
  `::test_unstorable_decimal_raises_where_the_backend_cannot_build_the_converter`); spec-036, spec-038, spec-039,
  README, GLOSSARY `FieldError` envelope. Filed 813
- [x] 810. (robustness) fixed: the serializer flavor holds each value a DRF uniqueness validator binds, at every level.
  `django_strawberry_framework/rest_framework/resolvers.py::_hold_unstorable_values` walks
  `django_strawberry_framework/rest_framework/resolvers.py::_validation_tree` and visits each owning
  `Serializer` once. `django_strawberry_framework/rest_framework/resolvers.py::_hold_serializer_values`
  holds actual writable root columns to the save rule
  (`django_strawberry_framework/utils/errors.py::unstorable_value`) and guards field validators at
  their fields and serializer validators at their owning level.
  `django_strawberry_framework/rest_framework/validator_guard.py::guard_uniqueness_validator`
  leaves each original DRF validator call in control of required, changed, null and condition
  decisions. Its copied pinned queryset uses
  `django_strawberry_framework/rest_framework/query_bind.py::guard_query` to follow
  Django's actual lookup preparation and one compiler execution; only parameters surviving final
  executable SQL are checked by
  `django_strawberry_framework/rest_framework/query_bind.py::_refused_params`, with the lookup's source retained for the
  field error. SQLite's signed driver range, PostgreSQL's actual typed parameter or integer-array
  cast, server offset and numeric-format refusals are distinct from a column's storage check;
  psycopg list-dump `DataError` before execution remains DRF's recoverable no-match case. A
  nested item's unbindable value is its field's `invalid` error at its dotted path, nothing
  written; a value no validator prepares or binds stays the consumer's `create()` / `update()`'s. Pinned by
  `examples/fakeshop/test_query/test_scalars_mutation_api.py::test_nested_value_a_uniqueness_validator_cannot_bind_is_the_item_field_error`
  (new fakeshop `createScalarSpecimenTagWithUniqueSpecimens`) and `tests/rest_framework/test_resolvers.py` /
  `tests/utils/test_errors.py` rows. Docs: spec-039, README, GLOSSARY `FieldError` envelope. CHANGELOGTODO 815
- [x] 730. (robustness) fixed: a filter declared over a field no `SCALAR_MAP` entry covers is refused at schema build
  in the FilterSet's own words instead of the DjangoType advice to add a `SCALAR_MAP` entry or exclude the field via
  `Meta.exclude`. `filters/inputs.py::_scalar_from_model_field` asks `types/converters.py::_registered_scalar_entry` first
  and raises `::_unscalared_field_refusal`, which opens with the declaration (its set, class, `field_name` and route) and
  names the remedy its field takes: a relation joined on one column, the relation in `Meta.fields`, a
  `ModelChoiceFilter` / `ModelMultipleChoiceFilter`, the related column named past it (`filters/base.py::_related_column_path`,
  where that column is not itself a relation) or a `RelatedFilter`; one linked by several columns, a `RelatedFilter`
  (`::_linked_by_columns`, shared with the raw-pk refusal); a `GenericForeignKey`, the `GenericRelation` reversing it or
  its content type and object id columns; a `CompositePrimaryKey`, its columns by name; any other column (a related key
  column reached through a raw-pk or model-choice filter included), a `SCALAR_MAP` entry for its class. `method=` is
  never offered (it does not escape the refusal). The exception type, the raise points and every build or refuse
  verdict are unchanged (358 grid cells moved message only); the converter text stays for its DjangoType, mutation and
  serializer callers. Pinned by `tests/filters/test_inputs.py::test_a_declared_filter_over_a_relation_is_refused_naming_filter_remedies`,
  `::test_every_remedy_a_relation_refusal_names_builds`, `::test_a_filter_over_a_field_with_no_scalar_is_refused_naming_its_remedy`,
  `::test_a_filter_over_a_django_column_with_no_scalar_is_refused_naming_its_remedy`, the `relation` leaf-refusal case,
  `tests/filters/test_base.py`'s relation-key and composite-key rows and
  `tests/filters/test_sets.py::test_an_object_sent_to_an_unserved_relation_leaf_is_refused_naming_its_remedies`. Docs:
  spec-027 Decision 4, README, GLOSSARY `FilterSet` and `ConfigurationError`. Filed 816. CHANGELOGTODO 817
- [x] 734. A flat field that walks a relation now runs on a copy bound to the last hop's target model as well as its
  target set, as django-filter's `BaseFilterSet.__init__` binds `model` and `parent` together: a filter that resolves
  its path against `self.model` while it filters (django-filter's `AllValuesMultipleFilter` copied flat from a
  `RelatedFilter` child set, a consumer `MultipleChoiceFilter` reading `get_model_field(self.model, ...)`, a consumer
  `filter()` re-cleaning with its own field) answers the nested branch's rows instead of an uncoded "Cannot resolve
  keyword ... into field", on every hop shape (forward, reverse, to-many key, key-folded), sync, async and through a raw
  `FilterSet(data, queryset, request).qs`; a set's own leaf walking a scoped undeclared relation too. New
  `filters/sets.py::_bind_filter` binds both; `FilterSet._bound_terminal` binds the terminal to `_hop_model(hop)` and
  gives it its own `extra`, so the set's per-request copy stays bound to the parent; `FilterSet._copy_filter` binds
  through the helper. Pinned by `examples/fakeshop/test_query/test_flat_copy_binding_api.py` (34 rows) and
  `tests/filters/test_sets.py::test_a_walked_terminal_binds_the_target_model_and_leaves_the_sets_copy_as_bound`; the
  late-copy and deferred-choices pins hold. Docs: spec-027 Layer 4 and Decision 8, README, GLOSSARY `FilterSet` and
  `RelatedFilter`. Filed 818, 819, 820. CHANGELOGTODO 821
- [x] 735. (robustness) fixed. Item 708's no-value ask (`filters/inputs.py::_refuse_form_serving_no_value`)
  already refused the Date / DateTime / Time / Float `in` shapes the item named, declared and `Meta.filter_overrides`
  alike. The rest built and served no non-empty value because the ask exited on proxies: it now asks every form whose
  cleaning is all Django's or django-filter's code (`::_cleans_in_shipped_code`, replacing the `_cleaned_kind is None`
  exit, so a consumer parser keeps the exit), and on a column without `choices` asks a choice form its own eager keys,
  the empty and null keys included, when its `validate` and `valid_value` are shipped (`::_asked_samples`,
  `::_form_choice_samples`, `::_validates_its_keys`; a consumer validation keeps the scalar-sample verdict). Callable,
  lazy and `QuerySet` choices are never evaluated at build (`::_defers_choices`, shared with 538's check, whose
  `QuerySet` build query goes too), a model-choice form is never asked, and a `coerce=Decimal` key no decimal spells
  answers no (`::_answers_sample`). Refused at build now: a `DateRangeFilter` in a text CSV `in` (its keys answered a
  masked `TypeError`) and in every `range` wrapper, CSV `MultipleChoiceFilter` members, a CSV `ChoiceFilter` whose keys
  spell no value of a typed column, a bare `in` `Filter`, `GenericIPAddressField` / `URLField` forms on an integer and
  a `MultipleChoiceField` form; 24 of 81 research-grid shapes and 5 of 68 verifier-grid shapes, every one answering
  `FILTER_INVALID` or a masked error for every non-empty value, no served shape lost, no build query. Pinned by
  `examples/fakeshop/test_query/test_filter_declarations_api.py::test_a_csv_declaration_no_value_of_its_column_answers_refuses_the_schema`,
  `::test_a_csv_declaration_some_value_of_its_column_answers_serves_it` and `tests/filters/test_inputs.py`'s
  `_NO_VALUE_CASES`, coerce, consumer-clean, deferred-choices, model-choice and propagation rows. Docs: spec-027
  Decision 4, README, GLOSSARY `FilterSet`. Filed 822, 823, 824. CHANGELOGTODO 825
- [x] 738. (robustness) fixed: a filter's deferred `choices` are never evaluated at schema build, whatever its form
  field class. Django's own choice fields (`TypedChoiceFilter`, `TypedMultipleChoiceFilter`, their CSV / range wrappers,
  a `field_class` naming `forms.ChoiceField` and kin) normalize `choices` at construction, forcing a `SimpleLazyObject`
  and running a `QuerySet` up to five times per leaf, so a project whose choices read a table could not run `check` /
  `migrate` on a fresh database. Every form field the build reads is now built on `filters/base.py::copied_filter`'s
  copy, which hands such choices over in `::_UnreadChoices` (Django's `CallableChoiceIterator`, answering `len()` by
  iterating and true unread); `copied_form_field` and `filters/inputs.py::_answers_sample` build through it, and the
  request path keeps the declared choices. `::defers_choices` moved to `filters/base.py`, covers `BaseChoiceIterator`
  instances (a callable-choices column's `Field.choices`) and reads classes through `utils/truth.py`. Item 735's
  regressions go too: Typed + `SimpleLazyObject` evaluated twice at build, and a bare `TypeError` for a CSV
  `ChoiceFilter` / `MultipleChoiceFilter` over a column without `choices` whose `choices` are a `CallableChoiceIterator`
  or an iterator (`_form_choice_samples` flattens an iterator). A consumer `field_class` or `field` override reading
  its own choices, `len()` included, evaluates them where it is built at the declared value's count. Grid: 77 of 419
  cells evaluating at build down to those 12 consumer cells; 0 request counts moved; fresh-database `check` / `migrate`
  10 of 10. Pinned by
  `examples/fakeshop/test_query/test_filter_declarations_api.py::test_deferred_choices_are_evaluated_per_request_never_at_schema_build`
  (six classes by four shapes), `::test_queryset_choices_are_run_per_request_never_at_schema_build`,
  `::test_consumer_code_counting_its_choices_at_build_builds_and_serves` and `tests/filters/test_inputs.py`'s deferred,
  iterator, expanded-child, override, `defers_choices` and `copied_filter` rows. Docs: spec-027 Decision 4. Filed 826,
  827. CHANGELOGTODO 828
- [x] 739. Fixed by restating the rule, not by narrowing the generated set: a `Meta.filter_overrides` filter class
  keeps the column's whole lookup set, since it owns the lookups it accepts, and the schema build refuses what a
  served set's input cannot type. Over an `ArrayField` a list filter types only `exact`, `contains`, `contained_by` and
  `overlap`, and the catch-all null test (a `BooleanFilter`, or any scalar filter naming `isnull`) types `Boolean`, so
  a served set's per-field `"__all__"` (the dict form; the list form and the top-level `"__all__"` generate `exact`
  only) is refused at `iexact`, and listing the lookups builds. Narrowing the set would have stopped an unserved set
  (`FilterSet(...).qs`, `apply_sync`) from serving `gt` / `in` / `range` over an array, which run on PostgreSQL. A
  list, CSV, typed or choice filter testing `isnull` over an array column stays refused, its advice now naming
  `BooleanFilter(lookup_expr="isnull")` (`filters/inputs.py::_array_column_refusal`); only that advice text moves on a
  real `ArrayField`. The test double `tests/_postgres_fields.py::FakeArrayField` registers `contained_by` /
  `overlap`. Pinned by `tests/filters/test_inputs.py`'s whole-array-lookup, override-route (`"__all__"` refused at
  `iexact`, the four listed building, `gt` listed refused), null-test-advice, range and `BooleanFilter` rows,
  `tests/filters/test_all_lookups.py::test_override_selected_array_column_keeps_the_whole_lookup_catalog` and the
  PostgreSQL-tier
  `examples/fakeshop/test_query/test_postgres_array_filter_bindability_api.py::test_an_array_filter_override_listing_the_whole_array_lookups_answers_each`.
  Docs: spec-027 Decisions 3 and 4, README, GLOSSARY `FilterSet`. Filed 829. CHANGELOGTODO 830
- [x] 741. A JSON integer literal past CPython's int-digit limit (4301+ digits at the default; the limit is
  runtime-configurable) anywhere a request's JSON is parsed now gets upstream's own refusal, in every
  `APPLY_UPSTREAM_PATCHES` state: both package views answer HTTP 400 "Unable to parse request body as JSON" (POST body
  in any position, GET `variables` / `extensions`, multipart `operations` / `map`, sync, async, under ASGI) instead of
  a 500, and the package WebSocket consumer closes `graphql-transport-ws` 4400 "WebSocket message must be valid JSON"
  (legacy `graphql-ws` drops the frame) instead of 1011 with a logged server failure. Both override Strawberry's
  `decode_json` seam (`views.py::_RequestBodyBoundaryMixin.decode_json`, the consumer's in
  `consumers.py::build_revalidating_consumer_class`) through `_json_decode.py::decode_json`, which turns only an exact
  `ValueError` raised inside upstream's `BaseView.decode_json` into `json.JSONDecodeError` (no message match: the text
  differs between 3.10 and 3.11+); a consumer `decode_json`'s own `ValueError` and a subclass pass through. The nested
  `RecursionError` stays with `_strawberry_patches.py` (spec-046 Decision 9); Strawberry's own view keeps upstream's
  answer; the inline query literal is Waiting 742. Research grid: 124 HTTP 500 cells to 400, 6 + 6 WebSocket cells, no
  other move. Pinned by `examples/fakeshop/test_query/test_transport_api.py`'s over-limit integer rows,
  `tests/test_routers.py`'s frame rows and `tests/test_views.py`'s `__cause__`, subclass and consumer-override rows.
  Docs: spec-046, spec-047 Decision 13 (now scoped: a document literal fails only in an `Int` position), the view
  docstrings, the KANBAN card 55 item, GLOSSARY `DjangoGraphQLView` and "Upstream patches". CHANGELOGTODO 831
- [x] 745. The finalizer's encode-only GlobalID audit now asks the filter a request executes, where it decodes:
  `types/finalizer.py::_audit_globalid_filter_strategies` reads every set a wired filterset serves
  (`filters/inputs.py::_served_reach`, the reach the unsealable-leaf audit walks, now shared), resolves each GlobalID
  leaf through the request's own routing (`filters/sets.py::FilterSet._routed_leaf_chain`, shared by
  `FilterSet._leaf_chain` and the build-time `FilterSet._globalid_decode_sites`, which binds a declared hop to a bare
  instance of the target set class and an undeclared hop to its face) and `filters/base.py::_globalid_target(...,
  stable=True)`, asks projected copies in the child set that runs them, and skips consumer decoders
  (`_decodes_before_binding`: `method=`, a class-level `filter` override). Now refused at build: a `RelatedFilter`
  into an unwired set whose key reaches a `callable` / `custom` type (an MTI descendant's reverse key, a key into an
  MTI child) and a scoped re-entry onto a callable secondary, each of which refused every nonempty value with
  `GLOBALID_UNVALIDATABLE`; their `null` and `[]` requests, which served, go with them. Now built and serving: consumer
  decoders over an encode-only type and a declared re-entry onto a decodable secondary with a callable primary. The
  message names the serving filterset, the request key, the declaring filter and the `RelatedFilter` path, and offers
  `method=`. `resolve_globalid_target_definition` is deleted; the `None`-strategy and non-Relay arms stay runtime-only.
  Pinned by `tests/filters/test_finalizer.py`'s refusal (twelve-plus shapes, whole message), admission and
  projected-copy rows and `examples/fakeshop/test_query/test_projected_owned_filters_api.py`'s consumer-decoder and
  secondary re-entry rows. Docs: spec-027, spec-031 and its rationale, GLOSSARY `Meta.globalid_strategy`, the 216 plan.
  Filed 832, 833. CHANGELOGTODO 834
- [x] 746. The finalizer's deep-copy probe now copies the table every request copies:
  `types/finalizer.py::_audit_filter_copies` runs first in subpass 2.5, after every served set has published, walks
  `filters/inputs.py::_served_reach` and copies every entry of each set's published `_filter_table()` (own filters,
  flat copies, `RelatedFilter` heads, and what a `get_filters()` override adds, borrows, re-keys or edits over the
  expanded surface) through `filters/base.py::copied_declared_filter`, naming the set, the published key and the
  `RelatedFilter` path. Subpass 1.5 and `_SidecarBindingSpec.pre_expand_audit` are removed. Grid: 32 cells that raised
  an unnamed pickle `TypeError` inside `finalize_django_types()` and 40 that built and raised it on every filtered
  request (masked) now refuse with the named `ConfigurationError`; an override editing a copied head or a hidden flat
  copy in place is refused too (django-filter's own constructor copies the published table whole outside the
  pipeline); a lock-holding declaration the override drops now builds. On a schema with two defects the first error can
  differ (still a build refusal). About +32 ms on the fakeshop build. Pinned by `tests/filters/test_finalizer.py`'s
  published-table, edited-copy, reached-path, ordering and dropped-filter rows and the live `expansion-override`
  parameter of
  `examples/fakeshop/test_query/test_filter_declarations_api.py::test_a_copyable_declared_filter_answers_a_real_filtered_request`.
  Docs: spec-027 Decision 6, the 216 plan. CHANGELOGTODO 835
- [x] 750. A `FilterSet` built outside the apply pipeline with `request=` (DRF's `DjangoFilterBackend`, django-filter's
  `FilterView`, a consumer's own `FilterSet(data, queryset, request=...)`) now hands every `DjangoType.get_queryset` its
  walked keys, relation keys, undeclared hops and logical arms reach an `info` whose `context.request` is that request
  (DRF's `Request` under the backend, the user DRF's authentication attaches): `FilterSet.__init__` stashes
  `filters/sets.py::_DirectRequestInfo` over `_DirectRequestContext(request)` (a plain dataclass adapted from
  Strawberry's `StrawberryDjangoContext`, read as `.request`, `["request"]` or `.get("request")`, writable for a hook's
  memo, `response` `None`, no schema). Staff and permission holders get the rows they get over GraphQL where they were
  filtered as anonymous, a hook reading `info.context.request.user` no longer raises, and a nested branch inside a
  logical arm no longer raises `ConfigurationError`; built with no request, each hook still receives `None`. Pipeline
  instances keep the resolver's `info`; projection children and logical-arm siblings share their root's. Grid: 473 raw
  and DRF cells moved, each onto its GraphQL twin; no GraphQL, `request=None` or head cell moved; a security probe
  (rejected and lazy DRF credentials, denying permissions, stale staff sessions, `FilterView`) found no cell wider than
  its twin. Pinned by `examples/fakeshop/test_query/test_direct_filter_actor_api.py` (DRF and `FilterView` against the
  `/graphql/` twin, logical arms, context reads and memo, `request=None`, the DRF-authenticated user). Docs: spec-027
  Decision 8, README, GLOSSARY `FilterSet` and `get_queryset` visibility hook. Unblocks 748. Filed 836. CHANGELOGTODO
  837
- [x] 793. Fixed with 836 (one root): an unserved set's refusals (`filters/base.py::refuse_unresolvable_lookup`,
  `::refuse_identityless_relation`) run at its first construction, so `FilterSet(data=...)`, `DjangoFilterBackend` or
  `FilterView` over a set declaring a refused filter raises `ConfigurationError` at construction and at every later
  one until it is fixed, where a raw set raised Django's own `FieldError` at `.qs` only for requests naming it. First
  use is defined once (GLOSSARY `FilterSet`, spec-027 Decision 4, both docstrings): the set's first construction or
  the package's first read of it (`get_filters()`, `apply_sync` / `apply_async`); the rows saying a raw set never
  publishes are deleted. Pinned by
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_raw_set_declaring_a_refused_filter_is_refused_at_its_first_construction`
  (three drivers; a `RangeFilter` over a relation, a `GlobalIDFilter` over a `GenericForeignKey`) and
  `tests/filters/test_finalizer.py::test_a_raw_to_many_key_lookup_the_relation_refuses_is_refused_at_first_construction`
  / `::test_a_raw_reverse_key_lookup_any_filter_class_applies_is_refused_at_first_construction`. CHANGELOGTODO 842
- [x] 836. A `FilterSet` no `DjangoType` names (a plain subclass of a wired set such as `class _Plain(BookFilter):
  pass`, or an unserved set) now publishes its filter table at its first construction:
  `filters/sets.py::FilterSet.__init__` reads `_filter_table()` when the class has no snapshot, before django-filter's
  `BaseFilterSet.__init__` deep-copies `base_filters`, so `FilterSet(data, queryset, request=...)`, DRF's
  `DjangoFilterBackend` and django-filter's `FilterView` copy the expanded table and answer every walked key with the
  served set's rows, where they ignored it as an unknown key and answered the view's unfiltered rows. A class still
  unable to publish (a construction re-entering its own build, a second thread mid-build, a model-less set with a lazy
  target) shadows the instance's `base_filters` with the table that read answered. A plain subclass publishes its own
  expansion (605 keys for `_Plain(BookFilter)`, not `BookFilter`'s 189: the path-relative cycle rule compares
  classes). A `base_filters` entry assigned on the class before first use is replaced by the published table, as a
  served set's is at finalize; `get_filters()` is the override seam. A raw walked key over a hop whose target has no
  registered `DjangoType` follows the walked-key rule (`FilterSet._branch_visibility_seed`'s `ConfigurationError`).
  Grid: 180 of 600 cells moved from the view's unfiltered rows to the served answer, for all three drivers; wired
  sets, their statement counts and answers did not move. Pinned by
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_raw_set_no_type_names_answers_a_walked_key_as_book_filter`
  (three drivers, plain subclass and unserved set, walked and two-hop keys, anonymous and staff) and
  `tests/filters/test_sets.py::test_a_construction_inside_a_sets_own_build_copies_the_surface_the_build_publishes`,
  `::test_a_construction_racing_a_sets_first_build_copies_the_surface_the_build_publishes` and
  `::test_a_sets_constructions_publish_its_table_once`. Docs: README `FilterSet`, GLOSSARY `FilterSet`, spec-027
  Decisions 4 and 8. Filed 841. CHANGELOGTODO 842
- [x] 841. Not a defect (AGENTS defect rule, GOAL "Trust boundary"): no contract row covers a third-party schema
  generator, and no wire input reaches it. The README's raw-driver promise names `FilterSet(data, queryset,
  request=...)`, DRF's `DjangoFilterBackend` and django-filter's `FilterView`. All three construct the set, and since
  836 the construction publishes. drf-spectacular's `contrib/django_filters.py` reads `filterset_class.base_filters`
  at schema generation, a startup-time configuration read, not a request. The contract question (whether a class-level
  read should publish) is parked as 843
- [x] 748. A raw-form `RelatedFilter` head (a `FilterSet` built outside the apply pipeline: `FilterSet(data, queryset,
  request=...)`, DRF's `DjangoFilterBackend`, django-filter's `FilterView`) that the data names, own (`BookFilter.shelf`)
  or copied (`shelves__books__shelf`), now reads its relation as a walked relation key: `filters/sets.py::_flat_leaf_walk`
  and `filters/base.py::_walks_declared_lookup` no longer exclude a `RelatedFilter`, so a named head runs through the
  target type's `get_queryset`, every intermediate hop and the `queryset=` scope of the path above it, and
  `FilterSet.form` narrows a named head's choices to the last hop's visible rows (`FilterSet._scope_supplied_heads`,
  lazily on the bound form: one hook per hop, none for a request naming no head; a sliced `queryset=` is left
  unnarrowed). Under a `null_label` the null value walks as the relation's null test over the rows each relation shows
  and each declaration's `queryset=` admits (`_head_null_test`); a head overriding `filter` receives its own
  `null_value` unchanged over its relation joined to those rows (`_KeyMatch.named_rows` to-many,
  `_head_null_view` / `_LeafChain.null_view` forward) and otherwise follows the overridden relation-key rule. A head
  whose walk reads a target model with no registered `DjangoType` keeps its declaration's queryset, unwalked (only a
  set no type serves holds one; 839). `_admitted_rows` intersects a sliced declaration `queryset=` through
  `pk__in=<slice>.values("pk")`, so a walk or a nested branch (GraphQL or `apply_sync`) through it answers the visible
  rows the slice holds where it raised `TypeError`. GraphQL names no head and is unchanged. Grid: 44 DRF and 44 raw
  head cells moved, each onto its walked twin or to `invalid_choice`; no walked, GraphQL, visible or missing cell moved.
  Narrowings matching the walked key: a set built without `request=` hands a named head's hooks `None` (a strict
  `info.context` hook raises), an async-only target `get_queryset` raises `SyncMisuseError`, and a head whose
  `queryset=` is of another model raises `ConfigurationError`. Pinned by
  `examples/fakeshop/test_query/test_direct_filter_actor_api.py` (own, to-many, M2M and copied heads; DRF, `FilterView`
  and a consumer-built set x anonymous / staff against the `/graphql/` twin; hook counts) and `tests/filters/test_sets.py`
  (null sentinel, overriding heads forward and to-many, unregistered target, `method=` head, non-`ModelChoiceField`
  head, declared `ModelChoiceFilter` override, sliced `queryset=` walks and nested branches). Docs: README raw-form
  paragraphs, spec-027 Decision 8 `#raw-form-heads` with its Edge case, Test plan, checklist and DoD 30, GLOSSARY
  `RelatedFilter`, the 216 plan. Fixes 751. Filed 838, 839, 844. CHANGELOGTODO 845
- [x] 751. A raw-form `RelatedFilter` head answers a key the target type hides with the same "Select a valid choice"
  as a missing key (`filters/sets.py::FilterSet._scope_supplied_heads` narrows the head's `ModelChoiceField.queryset`
  to the last hop's visible rows), so a raw-form client no longer tells hidden rows from missing ones. A `form`
  override that skips `super()` keeps the walk (no leak) but validates over the declaration's queryset. Pinned by the
  live 751 rows of `examples/fakeshop/test_query/test_direct_filter_actor_api.py` (hidden payload equals missing
  payload, five heads). Fixed with 748
- [x] 316. Two bounds of a declared `RangeFilter` compare as a range whatever lookup it declares (django-filter's
  `RangeFilter.filter` rule), so `RangeFilter(field_name="price")` with the default `exact`, a declared `gte`, `in`,
  `iexact` or a text pattern keeps the rows between the bounds where it raised a masked error, answered
  `FILTER_INVALID` or returned wrong rows; the published key is unchanged. `filters/base.py::RangeFilter.filter`
  compares `{bound_path}__range` through the declared transforms (`date` -> `date__range`, a package divergence from
  django-filter's string replacement, kept because the bounds are cleaned as the transform's output), `gte` + `lte`
  over an integer column with no transform between, and redirects a relation itself (raw form) to the column its
  values are compared on (`_compared_value_column`), so a bound past it widens or matches nothing as over
  `<relation>__id` instead of an unmasked `OverflowError`; `filters/base.py::_integer_compared_column` holds a
  `RangeFilter`'s bounds whatever it declares, so a raw `-1e400000` under `iexact` / `contains` no longer runs an
  unbounded `int()`. Pinned by `examples/fakeshop/test_query/test_range_filter_declared_lookup_api.py` (kinds x
  lookups x two bounds over flat, `not` and raw; relation-valued key; `parent__id`; relation itself forward and reverse
  past the column against a `<relation>__id` control; the hold with a 1.0 s limit),
  `test_scalars_filter_api.py::test_price_window_declared_with_no_lookup_compares_its_bounds_as_a_range` and
  `::test_range_through_a_filtered_relation_alias_compares_two_bounds_through_its_transform`, and
  `test_scalars_api.py::test_signed_big_window_declared_with_no_lookup_answers_a_bound_past_the_column_as_the_span`
  (new fakeshop `ScalarSpecimenFilter.price_window` / `signed_big_window`). Docs: spec-027 Decision 4 row, two Edge
  cases, Test plan, checklist and DoD 3. Fixes 508. Filed 846, 847. CHANGELOGTODO 848
- [x] 840. Not a defect (AGENTS defect rule): the item's "masked `IntegrityError`, outside the `FieldError` envelope"
  is false at HEAD. `mutations/resolvers.py::_model_write_step` runs `_assign_m2m` inside `save_or_field_errors`, so a
  custom `through=` model with a required extra column (an `IntegerField`, `BooleanField`, `DateField`, `JSONField` or
  non-null `ForeignKey` with no default) answers the in-band `__all__` `constraint` leaf ("A database constraint was
  violated.") with the write rolled back, the spec-036 contract for an `IntegrityError` at write; a `CharField()` extra
  is filled with `""` and succeeds, as Django does. Repro grid: 336 cells x SQLite and PostgreSQL 17 over the model,
  form and serializer flavors, 30 constraint cells, 0 masked errors, every row restored; DRF's own `ModelSerializer`
  keeps a custom-through relation read-only and never publishes it. Refusing the declaration at mutation class
  creation is spec-052 Slice 1 (`required_through_columns`, Decision 2), unbuilt and tracked by the KANBAN 052 DoD;
  no fakeshop mutation writes a custom-through relation
- [x] 833. A to-many relation-key GlobalID leaf whose walk re-enters its set's table under a type other than the
  relation's registered target now accepts the ids that registered type mints, as its unscoped twin does. The shapes
  are a set wired to a secondary with a scoping `get_queryset` on the path, a declared `RelatedFilter` last hop into a
  set bound to the secondary (hook or not), and a proxy-typed root. It used to refuse every nonempty value whenever
  the two types' accepted ids were disjoint, the proxy root even under (model, model). Root: two resolvers for one
  key. The declared predicate (item 780's pre-build in `filters/sets.py::_LeafChain.terminal_value`) validated against
  the relation's registry type, and the terminal `FilterSet._routed_leaf_chain` rebinds onto the target pk validated
  against the walking set's bound type. The key terminal and its `_KeyMatch` / fallback copies now carry their leaf as
  declared, and `filters/base.py::_globalid_target` resolves such a copy through `::_key_leaf_of` (same definition and
  NodeID slot, `row_path=""`). Both decodes stay and agree. An undeclared hop's face
  (`filters/sets.py::_UndeclaredHopSet`) carries the walking set as `_projection_owner`, so
  `filters/base.py::_filter_schema` reads the executing schema's published names for every walked terminal, forward
  keys past a scoped hop included (under a renaming `NameConverter` these took the plain spelling and refused the
  published one). A callable or custom secondary on such a set now builds. Grids (merged with 748/751): 84 of 1152, 9
  of 132 and 12 of 44 cells moved, each onto its unscoped twin; nothing that built was refused, no unscoped cell
  moved. Pinned by
  `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py::test_a_reentry_key_serves_the_id_its_relation_target_type_mints`,
  `::test_a_reentry_key_refuses_an_id_its_relation_target_type_does_not_mint` and
  `::test_a_walked_to_many_key_into_a_model_no_type_exposes_compares_the_node_id_alone` (live, `apply_sync`, raw
  form), and
  `tests/filters/test_finalizer.py::test_phase_2_5_admits_a_reentry_key_decoding_against_the_primary_its_relation_reaches`.
  Docs: spec-031 Decision 13, spec-027. Filed 849. CHANGELOGTODO 850
- [x] 216. `RelatedFilter(..., flat=False)` (keyword-only, an exact `bool` checked at construction, read-only through
  `filters/base.py::RelatedFilter.flat`) keeps a declaration's nested branch while copying none of its target's filters
  flat: `filters/sets.py::FilterSet._expand_along` skips the copy after the relation and correlation checks, so the
  target still builds, publishes and is audited (746's copy audit and 745's GlobalID audit reach it through the
  published head), its own traversals stay, a copied terminal head survives, and an own key the copy would replace is
  the set's own filter again with its own behaviour (omitted value, `required` on a form that holds it, `lookup_expr`,
  `exclude`, widget, the HIDE direction; an own `method=` runs on the parent ungated). Raw form data naming a withdrawn
  key is ignored, as django-filter ignores any unknown key. `MAX_FLAT_FILTERS` is documented as net key growth per
  expansion call (own population excluded, a replacing copy zero, a copied head counted, override additions on the set
  itself excluded), and its message names `flat=False` as the first remedy. `_reachable_filtersets` keeps following
  every declaration: restricting it to flat edges made refusals depend on build order (7 of 20 ring cells), against
  spec-027's cycle edge case. Fakeshop: `ReadingListEntryFilter.reading_list` is `flat=False` beside an enabled
  `ReadingListFilter.entries` and an own `reading_list__title` traversal. Pinned by
  `examples/fakeshop/test_query/test_related_filter_flat_api.py`, the `flat` rows of `test_filter_absence_api.py`,
  `test_filter_publication_api.py`, `test_projected_owned_filters_api.py`, `test_raw_filter_forms_api.py` and
  `test_relation_authority_worlds_sharded_api.py`, and `tests/filters/test_base.py`, `test_sets.py` (the 217 lap
  characterization, ring and dense surfaces in every build order, cap accounting) and `test_finalizer.py` (deep copy,
  cycles, GlobalID under both flags). Docs: spec-027 Decision 3 Layer 4 and its other homes, spec-028 Layer 4, README,
  `conf.py`, GLOSSARY `FilterSet` and `RelatedFilter`. The plan file is deleted (last at `771c299f`); BACKLOG
  `related_filter_flat_opt_out` becomes `related_filter_copy_once`. Filed 852. CHANGELOGTODO 853
- [x] 818. A declared branch's explicit `queryset=` is read as an `IN` subquery of its keys and never combined
  through `&`: `filters/sets.py::_admitted_rows` returns `child_rows.filter(pk__in=explicit.values("pk"))` for every
  explicit queryset (the sliced case folded in, the form Django's own `QuerySet.__or__` falls back to) and keeps its
  typed model-identity `ConfigurationError` with a reworded reason. A child filter django-filter runs `distinct()`
  for, a target `get_queryset` returning `distinct()` rows, and a `distinct()`, `union()`, DISTINCT ON or `values()`
  explicit queryset answer the queryset's rows nested, flat, under `not` / `and` / `or` and raw, where Django's
  `Query.combine` raised a masked "Cannot combine a unique query with a non-unique query." (128 of 880 grid cells and
  44 edge cells on SQLite and PostgreSQL; the shipped `allLibraryBranches(filter: {shelves: {homeBranches: ...}})`
  reached it). A `.using()`-pinned `queryset=` on another alias is refused (spec-045 Decision 4), where it was read
  on the request's alias. Pinned by `examples/fakeshop/test_query/test_flat_copy_binding_api.py::
  test_a_scoped_branch_admits_its_child_rows_the_queryset_holds` (+ `_async`) and
  `::test_a_raw_filterset_walks_a_scoped_branch_to_the_rows_its_queryset_holds`,
  `test_library_api.py::test_library_branches_shelves_queryset_bounds_a_distinct_model_choice_leaf_over_http`,
  `test_multi_db.py::test_a_related_filter_queryset_pinned_to_another_alias_is_refused_on_shard_b` (sharded) and the
  reworded `test_filter_consumer_contracts_api.py::test_related_queryset_requires_the_exact_child_model_only_when_the_branch_is_active`.
  Docs: spec-027 Decision 8 step 4a, raw-form heads, checklist, Edge cases, Test plan and DoD 31. Filed 854, 855.
  CHANGELOGTODO 856
- [x] 849. A consumer flat `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` ending on a re-entry's primary key
  (`shelf__books__id`, `__pk`, `genres__books__id`, `card__patron__id`), on a set whose walk an undeclared hop scopes
  (a `get_queryset` on the walking set's type or on an earlier hop's type), now decodes against the type registered
  for the relation's target, as its unscoped twin and the `shelf__books` key do, on live, `apply_sync`, `apply_async`
  and the raw form. It validated against the walking set's bound secondary, so the scoped and unscoped spellings
  accepted disjoint ids. `filters/base.py::_globalid_target`'s face branch takes the id authority from `registry.get`
  of the face's model and keeps the face's `_owner_definition` (the walking set's type) for the rows;
  `_GlobalIDTarget.foreign_rows` marks that case, and `::_decode_and_validate_global_id` refuses an annotation-held
  `NodeID` there with `GLOBALID_UNVALIDATABLE`, as the twin does. An encode-only secondary on such a set now builds,
  and an isnull key over it is admitted. The declared nested spelling (`shelf: {books: {id}}`) and a declared hop's
  own `id` keep decoding against the child set's bound type (spec-031 Decision 13 restated; spec-027 rows, the
  `filters/sets.py::_UndeclaredHopSet` docstring and the live README map follow). Grids: 1080 cell groups (3240
  records) and 240 off-key cells moved, each onto its unscoped twin; 192 build refusals now build; no unscoped, key,
  nested or `+decl` cell moved. Pinned by `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py` (nine
  trailing-pk worlds served and refused on three drivers, the annotation refusal, the owned-rows compare,
  `apply_async`) and
  `tests/filters/test_finalizer.py::test_phase_2_5_admits_a_reentry_isnull_key_decoding_against_the_primary_its_relation_reaches`
- [x] 858. A `GlobalID` relation key into a type whose `relay.NodeID` is an attribute its own `get_queryset` annotates
  (`books`, `book`, `genres`, `shelf__books`, fakeshop `Printing.series`; declared or generated, forward or to-many)
  now compares that id over the rows the type answers for, as its trailing-pk spelling (`books__id`) and a
  `RelatedFilter` hop's `id` (`inSeriesId`) do, in the same single statement (byte-equal SQL), on live, `apply_sync`,
  `apply_async` and the raw form; a well-formed id of another type answers the type mismatch. It refused every value
  `GLOBALID_UNVALIDATABLE` because the key's routing compiled the declared leaf on the walking set's own rows: the
  to-many pre-build (`filters/sets.py::_LeafChain.terminal_value`) and the forward fold
  (`FilterSet._folded_key_chain`). `FilterSet._routed_leaf_chain` now routes such a key as its trailing-pk twin
  (`filters/base.py::_compares_target_annotation`, 833's key-leaf marker, no pre-build, no fold), and the key copy's
  `foreign_rows` reads `filters/base.py::_rows_definition` (the face's rows type, else the set's binding, else the
  model's primary), so a key over rows another type scopes still refuses, as its flat twin does; a key whose class
  overrides `filter` keeps running as declared and refuses. The error message is unchanged. GLOSSARY `FilterSet` (pk
  463), docs/README.md, spec-027 (the annotation-held rule, the non-pk-id bullet, the walked-key rule, the test plan),
  the fakeshop `Series` / `Printing` docstrings and the live README map are restated. Grids: 552 of 4890, 87 of 408
  and 20 of 60 cells moved, each a key spelling onto its flat twin (16 of them forward / one-to-one multi-key `[]`
  cells going from 0 to 1 statement, as their twins and the to-many keys run); no flat, hop, plain-pk, foreign-rows,
  override or column-held `NodeID` cell moved. Pinned by
  `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py` (the keyed worlds' key shapes, compare,
  refuse, wrong type, coded refusal, `apply_async`) and `examples/fakeshop/test_query/test_library_api.py` (the
  `series` key rows, `::test_library_series_key_runs_the_statement_its_hop_twin_runs`)
- [x] 716. A package `ListFilter` / `ArrayFilter` whose Django lookup compares one value is refused when its set
  publishes, naming that lookup: django-filter's default `exact`, `gte`, `iexact`, `icontains`, `startswith`,
  `isnull`, a transform ending in one (`year`, `date`), an `ArrayField`'s `len` or index (item 740) and a
  `Meta.filter_overrides` `ListFilter` for `exact` / `gte`, where it built, published `[<scalar>!]` and answered wrong
  rows, a masked `TypeError` / `ValidationError` or `FILTER_INVALID` (80 of 146 grid cells, none correct).
  `filters/sets.py::FilterSet._publish_filters` asks `filters/base.py::refuse_listless_lookup` after
  `refuse_unresolvable_lookup` under the same guard: a served set at schema build, an unserved one at first use; over
  a relation the message names the related column (`parent__id`). `filters/base.py::_takes_list` admits Django's
  `get_db_prep_lookup_value_is_iterable` (`in`, `range`, transforms ending in either), `has_keys` /
  `has_any_keys`, and a `JSONField`'s, `RangeField`'s or `CompositePrimaryKey`'s comparisons (a list is one value
  there); `method=` filters, `filter` overrides, project lookup and field classes, `ArrayField` columns (left to the
  input gate) and stock django-filter parents are not judged. A `range` list of other than two members is the form's
  `invalid_values` error "Range query expects two values." (`_ElementField.validate`, adapted from django-filter's
  `BaseRangeField`), so `FILTER_INVALID` where one or three members raised a masked `IndexError` / `TypeError`,
  including a flat copy over a child `get_queryset` annotation (`FilterSet._install_source_comparison`,
  `install_comparison_cleaner`). Pinned by `tests/filters/test_finalizer.py::test_a_declared_list_filter_whose_lookup_compares_one_value_is_refused`
  and its siblings (admitted served and unserved, `filter_overrides`, project field class, composite key, stock
  parent), `tests/filters/test_inputs.py::test_a_list_filter_over_an_arrays_count_or_element_compared_by_one_value_is_refused`
  and `examples/fakeshop/test_query/test_list_filter_range_bounds_api.py`. Docs: spec-027 (Decision 4 row and
  paragraph, Edge cases, the `RangeFilter` "no declaration is refused" sentence narrowed to `RangeFilter`, Test plan,
  checklist, DoD 23), docs/README.md, GLOSSARY `FilterSet` (pk 463) and `ConfigurationError` (pk 444). Filed 862,
  863, 864. CHANGELOGTODO 865
- [x] 740. Fixed with 716: `ArrayFilter` / `ListFilter` over an `ArrayField`'s `len` or index compared by one value
  (`lookup_expr="len"`, `field_name="ints__len"`, `field_name="ints__0"`) is refused when its set publishes;
  `ints__len__in` and `ints__0__in` build. Pinned by
  `tests/filters/test_inputs.py::test_a_list_filter_over_an_arrays_count_or_element_compared_by_one_value_is_refused`
  and `::test_a_list_filter_over_an_arrays_count_element_or_whole_array_taking_the_list_builds`
- [x] 819. Not a defect (AGENTS defect rule, upstream parity): django-filter itself raises the same `ValueError`
  for `ModelMultipleChoiceFilter(field_name="branch", to_field_name="name")`. Its
  `MultipleChoiceFilter.get_filter_predicate` builds `{field_name: getattr(value, to_field_name)}` (`branch="South"`),
  which Django compares against the relation's target key; `to_field_name` picks the column the form cleans by, not
  the one the predicate compares. A stock `django_filters.FilterSet` and the package's root, nested, flat, `not` /
  `or` / `and` and raw spellings all raise it (masked over GraphQL), so the walked spellings add nothing. Repro grid:
  1554 cells (9 relations x model-choice, CSV model-choice and model-multiple-choice x every `to_field_name` x 8
  channels) against stock on SQLite, 2 mismatches (filed as 870); `ModelChoiceFilter` compares the cleaned instance
  and matches everywhere; `field_name="branch__name"` with `to_field_name="name"` (the django-filter idiom) answers
  on every channel. django-filter 25.2 to 26.2 ship the same `filters.py`. Graphene-django and
  django-graphene-filters do not handle `to_field_name`. The shipped fakeshop `ShelfFilter.home_branches_named`
  declares the failing shape (filed as 869)
- [x] 752. A `RelatedOrder` whose target `OrderSet` is bound to a type of a model its relation does not reach is
  refused with a `ConfigurationError` naming the owner, the declaration, its `field_name`, the reached model and the
  bound type, where `orders/sets.py::OrderSet._scoped_hops` scoped the hop by that type (a plain wrong type let rows
  the real type hides order visible parents; a hiding one read every term as missing). `types/finalizer.py::
  _audit_related_order_targets`, now the orders subpass-2.5 `post_expand_audit` (made required), walks from each
  wired set's type model through every declaration transitively; `OrderSet._scoped_hops` refuses the same at apply for
  a set a resolver applies directly or a `.orderset` reassigned after finalize. Both read
  `orders/sets.py::_require_scoped_order_target` over the new `optimizer/predicates.py::correlates_joined_rows` (the
  joined rows' model, a proxy, or a multi-table-inheritance parent or child keyed by the same stored column), compared
  on the bound type's model; unbound and `None` targets keep falling back to the relation's own type. The filter
  side's `correlates_related_rows` is not shared: it refuses an ancestor set across a reverse one-to-one, which the
  order test (the joined row's key) answers correctly. `optimizer/predicates.py::visible_row_exists` now takes the
  relation: rows whose model lacks a `to_field` target column (an MTI parent of the related model) match the related
  row the carriers name inside the subquery, from the related model's base manager, where the term raised `FieldError`
  per request; no row drops, an unconstrained key naming no row included. Grid: 39 of 87 cells moved, every one a
  mismatched or deliberate shape; no correlated cell moved; SDL unchanged. Pinned by
  `tests/orders/test_finalizer.py::test_related_order_whose_target_type_the_hop_cannot_scope_by_is_refused_at_finalize`,
  `::test_related_order_whose_target_type_shares_the_reached_rows_finalizes`,
  `::test_apply_refuses_a_target_reassigned_after_finalize_to_an_unscopable_set`,
  `tests/orders/test_sets.py::test_a_hop_scoped_by_an_ancestor_lacking_the_to_field_hides_through_the_related_row`,
  `::test_a_hop_through_an_inherited_to_field_reads_only_rows_of_the_related_model` and
  `examples/fakeshop/test_query/test_order_target_scope_api.py`. Docs: spec-028 (Decision 6 subpass 2.5, Decision 8
  step 4, Error shapes, Edge cases, checklist, Test plan, DoD 10) and its rationale, spec-060, docs/README.md, GLOSSARY
  `RelatedOrder` (pk 496). Filed 866, 867. CHANGELOGTODO 868
- [x] 777. Fixed with 752: a wired set's `RelatedOrder` whose `field_name` is not a path of relations (a column, a
  missing name, a segment past a column, or such a declaration two sets down) is refused when types finalize
  (`orders/sets.py::_require_order_relation_path`, in the subpass-2.5 audit); a set applied directly keeps the
  per-request "invalid order path" error. Pinned by
  `tests/orders/test_finalizer.py::test_related_order_whose_field_name_is_not_a_path_of_relations_is_refused_at_finalize`
  and `::test_a_declaration_two_sets_down_is_audited_from_the_model_the_outer_relation_reached`
- [x] 869. The fakeshop `ShelfFilter.home_branches_named` declares django-filter's `to_field_name` idiom
  (`field_name="branch__name"`, `to_field_name="name"`), so root, `not`, nested, flat (`shelfHomeBranchesNamed`) and
  genres spellings answer the named branches' rows, where every valid name list answered the masked `ValueError`; a
  restricted or unknown name stays the form's `invalid_choice` under the same key; the leaf walks `branch` as a hop
  under `BranchType` visibility; the SDL is byte-identical. Pinned by
  `examples/fakeshop/test_query/test_library_api.py::test_library_declared_model_multiple_choice_filter_takes_its_to_field_name_values_over_http`
  (root, `not`, nested, genres nested and flat; exact statement counts) and the `shelfHomeBranchesNamed` row of
  `::test_library_flat_expanded_declared_filter_keeps_its_own_validation_over_http`. Example-only, no CHANGELOG entry.
  Filed 871
- [x] 753. (docs) A `RelatedFilter`'s `queryset=` bounds exactly the paths whose walk crosses that declaration (its
  nested branch, flat copies, a `Meta.fields` key or relation-key leaf walking it, a raw head, and a path entering it
  through an outer declared branch); a dotted key whose walk crosses no declaration of it (another set's
  `branch__shelves__topic` declaring no `branch`, `alt_shelves__topic`, `alt_shelves__branch__shelves__topic`) answers
  for its hops' target types' `get_queryset` alone, so rows no route may reach belong in `get_queryset`. Stated in
  spec-027 Decision 8 (preamble and step 3), its borrowing line, Edge cases, Test plan, Doc updates and DoD 31,
  docs/README.md and GLOSSARY `FilterSet` (pk 463) and `RelatedFilter` (pk 495); no package change. Pinned by
  `examples/fakeshop/test_query/test_relation_filter_boundaries_api.py::test_declaration_queryset_bounds_only_a_dotted_key_whose_walk_crosses_it`
  (both sides, anonymous and staff)
- [x] 754. (docs, fakeshop) Not a package defect (GOAL "Trust boundary": a `get_queryset` hook is trusted code whose
  contract is to cascade, and the package cannot tell whether it does). The contract and its consequence are now stated:
  a type with a non-null forward key into a type whose hook hides rows cascades (`apply_cascade_permissions`, or
  narrowing by hand an edge the helper cannot walk: a `GenericForeignKey`, a `ForeignObject` that is not a
  `ForeignKey`); otherwise such a row reads as one whose related row is missing (the relation resolves `null`, a
  non-null field is a masked completion error, `data: null` with one error at the relation's path under a non-null
  list) and `isNull: true` on the key matches it. Stated in docs/README.md "Visibility and permissions" and the
  filtering `isNull` sentence, GLOSSARY `apply_cascade_permissions` (pk 440), `FilterSet` (pk 463), `get_queryset`
  visibility hook (pk 468) and Relation handling > Resolver behavior (pk 497, the contract spec-034 Decision 6 cites),
  and the `DjangoType.get_queryset` and `types/resolvers.py::_visible_related_object` docstrings. Fakeshop's library
  `BookType`, `CatalogueBookType`, `ShelfType` and `ShelfLabelType` keep the uncascaded shape on purpose (the
  visible-world filter and order rows need a visible book on a hidden shelf; `ShelfLabelType.shelf` is a `ForeignObject`
  the helper cannot walk), as their docstrings and the fakeshop README say. The item's Book `isNull` half does not
  reproduce: no Book filter publishes an edge `isNull`; the `ShelfLabel` key is that half
  (`test_library_inheritance_api.py::test_shelf_labels_filter_shelf_isnull_over_the_shelves_the_viewer_sees`). The
  masked half is pinned by `test_library_api.py::test_uncascaded_book_on_a_hidden_shelf_reads_its_shelf_as_missing_for_anonymous`,
  `::test_uncascaded_book_on_a_hidden_shelf_serves_its_shelf_to_staff` and
  `test_library_inheritance_api.py::test_shelf_label_on_a_hidden_shelf_reads_its_shelf_as_missing_for_anonymous` /
  `::test_shelf_label_on_a_hidden_shelf_serves_its_shelf_to_staff`
- [x] 860. A `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` declared as a leaf ending on a relation target's
  primary key (`books__id`, `__pk`, at any depth), past a declared `RelatedFilter` hop into a filter set no type wires
  (plain, `flat=False`, `queryset=`, an unwired subclass of a wired set), or declared on such a set past its own
  unwired hop, now validates against the type registered for the relation's target and compares the column or
  annotation that type's id carries, as its relation key, its undeclared twin and its wired-hop twin do, on live,
  `apply_sync`, `apply_async` and the raw form. The routing rebased it onto the unbound child as `id`, so
  `filters/base.py::_globalid_target` read it as that set's own key and decoded node-id-only: no type check (a
  wrong-type id matched rows), `GLOBALID_INVALID` for every id a column or annotation `NodeID` carries, a right-type
  id holding the row's pk digits accepted, and an encode-only target behind the hop built.
  `filters/sets.py::FilterSet._routed_leaf_chain` now marks such a pk-tail terminal with 833's key-leaf marker unless
  it stands for the child set's own key (`::_stands_for_own_key`, read off the leaf's declaration), so it resolves as
  declared; the unbound set's own key, nested or as a hop's flat copy, keeps the node-id-only reading (dry-0_0_15_3
  item 50), and a hop into a set a secondary type wires is unchanged (filed as a question). spec-031 Decision 13 (all
  homes), spec-027 (the unbound sentence, the annotation-held list, Decision 6 subpass 3, Decision 8 step 3, the test
  plan), the docstrings and the live README map are restated. Grids: 5124 of 57696, 2196 of 21168 and 1008 of 13464
  cells moved, all in the unwired flat family, each onto its twin; no key, nested, hop-copy, undeclared or wired cell
  moved. Pinned by `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py` (the unbound-hop keyed
  shapes, `apply_async`, the secondary-wired rows),
  `examples/fakeshop/test_query/test_library_api.py::test_an_unwired_target_filterset_runs_a_leaf_ending_on_its_key_as_the_relation_type`
  / `::test_an_unwired_target_filterset_refuses_a_wrong_type_id_on_a_leaf_ending_on_its_key` and
  `tests/filters/test_finalizer.py` (the encode-only refusal,
  `::test_phase_2_5_admits_a_key_of_the_hop_target_set_decoding_against_that_set`)
- [x] 871. A `ModelChoiceFilter` / `ModelMultipleChoiceFilter` / CSV model-choice filter with a callable `queryset` is
  typed from the model its `field_name` path ends on over the declaring set's model (the last relation's target, the
  set's own model for a path crossing none; a path ending on Django's `pk` alias ends on the model the part before it
  reaches, never on a multi-table-inheritance parent link), so django-filter's `field_name="branch__name",
  to_field_name="name"` idiom builds and answers as the same declaration with a model queryset does, where every
  column-ending path was refused at schema build (117 of 177 grid shapes now build, all equal to the model arm and
  stock; nothing that built changed). `to_field_name="pk"` is the primary key on both arms (Django's
  `to_field_name or "pk"`); a `to_field_name` naming no column of the model, a callable queryset whose `field_name` is
  no path of fields (or on a set without `Meta.model`) and an unset queryset on a non-relation or `pk` path raise
  `ConfigurationError` naming the set and filter, replacing a raw `FieldDoesNotExist` and the remedy that steered to
  `field_name="branch"`. `filters/base.py::model_choice_model` replaces `model_choice_identity_column`;
  `_model_identity_column`, `relation_identity_column` and `filters/inputs.py::_model_choice_identity_annotation`
  follow; `choice_key_field` moved from `forms/inputs.py` to `utils/relations.py`. Fakeshop adds
  `ShelfFilter.home_branches_named_for_request`, `ShelfFilter.home_branch_pks_for_request`,
  `BranchFilter.names_for_request` and `BranchFilter.pks_for_request`. Pinned live by `examples/fakeshop/test_query/test_library_api.py::test_library_declared_model_multiple_choice_filter_takes_its_to_field_name_values_over_http`
  (callable and hop-less rows, root / nested / flat), `::test_library_declared_model_choice_filter_over_the_pk_alias_with_a_callable_queryset`
  and `::test_library_declared_model_choice_filters_take_the_column_their_form_cleans_over_http`, and in the package
  by the `tests/filters/test_inputs.py` rows for the `pk` alias, unknown `to_field_name`, column paths (inheritance
  child, `kiosk__pk`, two hops, no hop), unset `pk` paths and a model-less set. Docs: README, GLOSSARY `FilterSet`
  (pk 463, "Relation leaves"), spec-027 (Decision 4 row, Edge case, Test plan). Filed 875. CHANGELOGTODO 876
- [x] 755. (docs) Not a package defect (GOAL "Trust boundary": each type's `get_queryset` is its own declaration). The
  docs now say which hook a refetch runs: a model-label id decodes to the model's primary type and runs its hook; a
  type-name id decodes to the type it names and runs that class's hook, declared or inherited, so a `type`-strategy
  secondary (or a `type+model` one reached by its type-name id) with no hook of its own serves, through `node` /
  `nodes` and its own roots, rows the primary's hook hides; the remedy is a hook on the secondary calling the
  primary's. Stated in docs/README.md (the secondary-type blockquote and the `node` paragraph) and GLOSSARY
  `DjangoNodeField` (pk 458), `Meta.globalid_strategy` (pk 518) and `DjangoNodesField` (pk 520). Pinned by
  `examples/fakeshop/test_query/test_library_api.py::test_a_type_strategy_secondary_refetches_through_its_own_get_queryset_over_http`,
  its async twin `::test_async_a_type_strategy_secondary_refetches_through_its_own_get_queryset` and
  `tests/test_relay_node_field.py::test_a_type_model_secondary_type_name_id_runs_its_own_hook_not_the_primarys`
- [x] 851. A leaf walking a `RelatedFilter(None)` placeholder hop again answers spec-027 Decision 8 step 3 (the
  `ConfigurationError` when supplied, no effect when absent or inactive) instead of a masked `TypeError` from
  `utils/_narrowing.py::require` in `_hop_target_set`, over raw form, `apply_sync` and `apply_async`. `93679177` added
  `FilterSet._leaf_chain` callers that run during form cleaning before the hops are derived
  (`_unbindable_value_errors` through `_bind_ask_terminal_source`, `FilterSet._necessary_annotation_hop`), plus an
  async pre-pass reading `_hop_model` (`FilterSet._derive_flat_hop_visibility_async`), none applying the rule
  `_absent_leaf_applies` applied (bisect: 11 rows pass at `62c68ea7`, 8 fail at `93679177`; its targeted run never
  ran the module). The rule is one predicate, `FilterSet._walks_unresolved_hop`, now asked by those three, by
  `_absent_leaf_applies` and by `FilterSet._install_source_comparison` (a list / range / array leaf over a name no
  column holds); binding through resolved hops is unchanged (411-row grid: every active-placeholder row equals
  `62c68ea7`). Pinned by the eight item rows of
  `examples/fakeshop/test_query/test_relation_filter_defaults_api.py`,
  `::test_a_raw_form_list_leaf_through_a_forward_placeholder_refuses_only_when_cleaned` and
  `::test_a_pipeline_leaf_through_a_forward_placeholder_refuses_only_when_supplied` (column, annotation list and
  range leaves x supplied / absent x sync / async, exact statement counts). A GlobalID leaf through a placeholder is
  refused earlier at schema build (`types/finalizer.py::_audit_unregistered_related_filter_targets`). Unreleased
  regression, no CHANGELOG entry
- [x] 875. A `ModelChoiceFilter` / `ModelMultipleChoiceFilter` whose `field_name` names a `GenericForeignKey` (on the
  set's model or past a relation; django-filter's CSV wrapper and a `Meta.filter_overrides` selection included) is now
  refused with the GlobalID filter's `ConfigurationError` when its set publishes its filters: at schema build for a
  served set, at first use for an unbound one. With a model `queryset` it built and answered every request with
  Django's masked `FieldError`; a callable or unset one was refused only when served, in input-build words, and failed
  per request unbound. `filters/base.py::refuse_identityless_relation` now also asks the model-choice family, when its
  `filter` is shipped code (`filters/sets.py::FilterSet._publish_filters` passes `_runs_shipped_filter`) and it
  declares no `method`; a `method=`, a class-level `filter` override and a `GenericRelation` keep serving, and
  GlobalID's gate is unchanged. The other half is not a defect: a model-queryset model-choice filter whose
  `field_name` the model does not carry (a typo, a queryset annotation, a `FilteredRelation` alias) is left to the
  request like every filter class (`filters/base.py::refuse_unresolvable_lookup`'s stated exemption); an alias and a
  text annotation serve rows. spec-027 (the `_publish_filters` checklist item, the Decision 4 model-choice row, the
  declared-predicate paragraph, the test plan) and the live README map are restated. Grids: 6 of 144 and 15 of 30
  shapes moved, all model-choice on a GFK. Pinned by
  `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py`
  (`::test_a_model_choice_filter_on_a_generic_foreign_key_is_refused_when_the_schema_builds`, the unserved first-use,
  consumer-code, `GenericRelation` and served-annotation rows) and
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_raw_set_declaring_a_refused_filter_is_refused_at_its_first_construction`
- [x] 756. A model-choice filter (`ModelChoiceFilter`, `ModelMultipleChoiceFilter`, a CSV wrapper, or one a
  `Meta.filter_overrides` entry without an `extra` queryset selects) given no queryset is refused with a
  `ConfigurationError` naming the set, the filter and its `field_name` when its set publishes (schema build for a
  served set, every construction or first package read for an unserved one), where a served set typed and published
  its input and every request raised Django's `TypeError` building the form. `filters/base.py::
  refuse_querysetless_choice` (with `::_field_needs_a_queryset`), asked by `filters/sets.py::FilterSet._publish_filters`
  right after `refuse_identityless_relation` (whose `GenericForeignKey` refusal, item 875, answers first), judges only
  an absent queryset (no attribute, no `extra` key) and trusts consumer code that can supply one per request: a filter
  `get_queryset` / `field` override, a form field class running its own `__init__` before Django's (read by MRO, not
  run: building the field at publish cannot tell a missing queryset from any other `TypeError` and runs consumer code),
  and a set overriding `__init__`, `get_form_class` or `form`. An explicit `queryset=None` keeps its behaviour (filed
  879); 871's input-build arm stays for exempt shapes on non-relation paths. Grid: 230 of 665 cells moved, all in the
  19 unset shapes; no working or stock cell moved; SDL unchanged. Pinned by
  `tests/filters/test_finalizer.py::test_a_model_choice_filter_with_no_queryset_is_refused_when_its_set_publishes`,
  `::test_a_model_choice_filter_consumer_code_can_give_a_queryset_builds`,
  `::test_a_filter_overrides_entry_whose_extra_gives_a_queryset_builds`,
  `::test_an_explicit_none_queryset_is_a_passed_value_and_is_not_judged`,
  `::test_a_model_choice_filter_with_no_queryset_on_a_generic_key_takes_the_generic_key_refusal`,
  `tests/filters/test_inputs.py::test_an_expanded_child_model_choice_with_no_queryset_is_refused_when_its_set_publishes`,
  `::test_an_expanded_child_set_overriding_init_keeps_its_querysetless_model_choice` and the
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py` `_REFUSED_SETS` rows (three raw drivers). Docs: spec-027
  (Decision 4 model-choice row, checklist, Edge cases, Test plan, DoD 32), docs/README.md, GLOSSARY `ConfigurationError`
  (pk 444) and `FilterSet` (pk 463). Filed 879. CHANGELOGTODO 880
- [x] 877. A filter running shipped code whose `field_name` ends on a `GenericForeignKey` (on the set's model or past
  a relation, whatever its class or lookup: `CharFilter`, `NumberFilter`, `BooleanFilter` and its `isnull`, typed,
  list, CSV, range, choice, `LookupChoiceFilter`, a generated `Meta.fields` key) is now refused when its set publishes
  its filters, in the served input build's words naming the set that declares it: at schema build for a served set, at
  first use for a set no type serves (a raw `FilterSet(data=...)`, `DjangoFilterBackend`, `FilterView` and
  `apply_sync` included). Unserved, such a filter built and failed every request carrying a value with Django's
  `FieldError` (masked over a resolver), and a served `isnull` one built and failed alike. New
  `filters/inputs.py::refuse_joinless_relation`, asked under `_runs_shipped_filter` in
  `filters/sets.py::FilterSet._publish_filters`; a `method=` filter and a class-level `filter` override keep filtering
  as they choose, and the content type / object id columns and a `GenericRelation` build. Served choice-family filters
  on a GFK now carry the GFK text, and a `RelatedFilter` route names its own set. The spec-027 / GLOSSARY sentence
  about an unserved set's `apply_sync` refusal is restated to its true scope (an object sent to a scalar, typed or
  `method=` leaf; a list, CSV, range or multiple-choice leaf rejects it as no list or range). spec-027 (the
  `SCALAR_MAP` edge case, the Decision 4 catch-all and list rows, the declared-predicate paragraph, the checklist, the
  raw-set edge case, the DoD, the test plan), GLOSSARY `FilterSet` (pk 463) and the live README map follow. Grids: 608
  of 3027 rows moved, all on the four GFK shapes. Pinned by
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py` (four new refused sets,
  `::test_a_raw_set_filtering_the_columns_beside_a_generic_key_answers_their_rows`), the GFK block of
  `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py` and `tests/filters/test_sets.py`
  (`::test_a_column_filter_on_a_relation_django_joins_publishes`,
  `::test_an_exact_list_on_a_generic_foreign_key_is_refused_for_the_relation`)
- [x] 757. The root `node` / `nodes` fields now refuse a well-formed id naming a Relay type the executing schema does
  not publish (a registered type no root, relation or `types=` entry reaches; an id another schema over the same
  registry minted; a model-label id whose model's primary the schema omits) with `GLOBALID_INVALID`, before any query,
  consumer `resolve_node` / `resolve_nodes`, `resolve_id_attr` or `DATABASE_ROUTERS` read routing, where they ran that
  type's queryset and answered graphql-core's uncoded "Abstract type 'Node' must resolve to an Object type at runtime"
  error for a visible row and `null` otherwise. Such an id anywhere in `nodes` fails the whole field (spec-032 Decision
  5); the typed form still reports its wrong-node-type mismatch first. `relay.py::_require_published` over the new
  public `types/relay.py::require_published_node` (one message source with `node_definition_for_published_name`), run
  after `_check_typed_match` in both resolvers; the resolvers read the executing schema as required
  (`relay.py::_executing_schema`). The decode fallback stays for mutations, filters, the typed mismatch message and the
  public helpers (spec-031 Decision 8). Reproduced live on the `FAKESHOP_TEST_BOUND_SETS` Shelf secondaries; grid 94 of
  223 rows moved, every one an unpublished id. Pinned by
  `examples/fakeshop/test_query/test_library_api.py::test_node_refuses_a_registered_relay_type_the_shipped_schema_does_not_publish`,
  `::test_nodes_with_an_unpublished_relay_type_id_fails_the_whole_field`, its async twin,
  `test_globalid_naming_api.py::test_bare_node_refuses_an_unpublished_types_id_before_any_query` (+ `nodes`, typed),
  and `test_node_refetch_api.py::test_an_id_another_schema_emitted_is_refused_before_any_resolver_runs`,
  `::test_a_model_label_id_decoding_to_an_unpublished_primary_is_refused`,
  `::test_nodes_refuses_an_unpublished_id_before_reading_any_id_slot`,
  `::test_nodes_refuses_an_unpublished_id_before_routing_any_read`. Docs: README node paragraph and secondary
  blockquote, GLOSSARY `DjangoNodeField` (pk 458) and `DjangoNodesField` (pk 520), spec-031 Decision 8, spec-032
  (checklist, Error shapes, Decision 5, Edge cases, Test plan, DoD 3). Filed 883, 884. CHANGELOGTODO 885
- [x] 883. The root `node` / `nodes` fields now refuse, as `GLOBALID_INVALID` before any query, read routing or
  consumer hook, an id whose published type the field's annotated return type cannot hold (a bare field annotated with
  a union, a narrower interface or a plain Strawberry object type; a typed field annotated with another type), asked
  of the executing schema (`GraphQLSchema.is_sub_type` for an abstract return; an object return holds only itself),
  hidden and missing rows included, failing the whole `nodes` field. Such a visible row ran the type's queryset and
  answered graphql-core's or Strawberry's uncoded engine error, a hidden one null. `DjangoSchema` also refuses at
  construction a typed `DjangoNodeField(T)` / `DjangoNodesField(T)` whose annotation cannot return `T`, or whose `T`
  it publishes nowhere; a plain `strawberry.Schema` builds it and refuses its ids at request time. New
  `types/relay.py::node_type_returned_by` / `::require_returned_node` (asked in `relay.py::_require_published` after
  `require_published_node`), `relay.py::refuse_unreturnable_node_targets` (called from
  `schema.py::DjangoSchema.__init__`, reading the `NODE_TARGET_MARKER` the typed factories stamp) and
  `utils/typing.py::field_return_type`. Grid: 31 of 180 cells per mode moved, every one an id outside the annotation,
  to the coded refusal at 0 queries. README "Node refetch", GLOSSARY `DjangoNodeField` / `DjangoNodesField` /
  `DjangoSchema` (pk 458, 520, 589), spec-032 (the five homes) and the `relay.py` / `schema.py` docstrings follow.
  Pinned by `examples/fakeshop/test_query/test_node_refetch_api.py` (unions, the library `Named` interface, one other
  type, type-name and model-label slots, a union without the primary, whole-field batches, an alias, an uncoercible
  literal, a plain `strawberry.Schema`) and `tests/test_relay_node_field.py` (the construction refusals and builds,
  `::test_a_plain_object_annotation_holds_no_relay_type`)
- [x] 792. A declared filter whose path starts at a `FilteredRelation` alias of the queryset the set filters
  (`CharFilter("vshelf__code")`, `ListFilter("vshelf", lookup_expr="in")`, reverse, many-to-many, past the alias, an
  alias over several relations or over another alias; added by a type's `get_queryset`, the queryset handed to the set
  or a `filter_queryset` override) now reads the visibility of each relation the alias joins, its condition read by
  Django's own join of the alias, on GraphQL, `apply_sync`, `apply_async` and raw forms, where the anonymous viewer
  matched through rows the target type's `get_queryset` hides. `filters/sets.py::_query_aliases` reads
  `Query._filtered_relations` off the queryset the leaves run over; `utils/permissions.py::_walk_undeclared_hops`
  walks the alias as one `UndeclaredHop` (`alias`, `via`), and `::_alias_hop` refuses an alias joining no relation
  path with `ConfigurationError`; `filters/sets.py::FilterSet._reaches_alias` reaches rows over
  `optimizer/predicates.py::correlated_inner_root`, which hands the inner root the outer aliases and annotations
  (`::resolving_filtered_relations`, adapted from Django's `Query.split_exclude`); `isnull=True` and `exclude` keep
  Django's INNER-join answer (`_reaches_none`, `_alias_joins`). An annotation a condition reads over a table alias the
  filter's own joins also define (read off Django's `Query.alias_map`: a relation the alias crosses, the alias it
  starts at, a join Django numbers, a many-to-many through table) is refused with `ConfigurationError` naming the
  alias, the annotation and the table alias (`optimizer/predicates.py::refuse_rebound_annotations`), unless every step
  from the base is the same `Join` over a forward key (`::_same_forward_chain`). Under `apply_async` an alias only
  `filter_queryset` adds is not awaited, so an async-only target hook raises `SyncMisuseError`. Grid: anonymous leaks
  1256 to 0 and inverse 180 to 0 of 1548 alias cells; real-relation, staff and no-hidden-rows cells and statement
  counts unchanged. README, spec-027 (Decision 8 step 3, Slice 4a, Edge cases, Test plan, DoD 33) and GLOSSARY
  `FilterSet` (pk 463) follow. Pinned by `examples/fakeshop/test_query/test_filter_apply_arguments_api.py`
  (`::test_a_flat_path_starting_at_a_filtered_relation_alias_reads_each_relations_visibility`,
  `::test_an_alias_only_filter_queryset_adds_is_not_awaited_before_an_async_only_hook`,
  `::test_a_filtered_relation_alias_joining_no_relation_is_refused_when_a_leaf_walks_it`,
  `::test_an_absent_alias_key_whose_filter_reads_its_path_answers_over_the_visible_rows`,
  `::test_an_alias_condition_reading_an_annotation_its_joins_would_rebind_is_refused`) and
  `examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_raw_key_over_a_filtered_relation_alias_reads_the_shelfs_visibility`.
  Filed 906. CHANGELOGTODO 905

- [x] 68. A model's filtering (or annotating) default manager no longer shapes reads that reach its model across a
  relation. Filter hops (declared, nested and flat, and undeclared over a hooked target), related order hops, the
  visibility cascade and single-valued relations (the optimizer's planned forward FK / O2O / reverse O2O child and the
  unplanned re-check) now start from every row of the model, as Django's join reads them, in the class the default
  manager's own `get_queryset` returns; the override contributes only that class there (no filter, annotation,
  ordering or other query state), and the type's `get_queryset` still runs on every hop, so a row a type's hook hides
  stays hidden. Reads that start at the model (roots, connections, Relay id lookups, writes) and nested many-side
  lists and connections keep the default manager. A filtering `Meta.base_manager_name` is not read; a filter or hook
  naming a column only the manager annotates answers Django's `FieldError` across a hop. New
  `utils/querysets.py::related_queryset`, read by `filters/sets.py::FilterSet._branch_visibility_seed`,
  `::_scoped_seed_rows`, `::_hop_visible_rows`, `::_projection_child`, `::_bind_ask_terminal_source`,
  `::_absent_leaf_applies`, `::_chain_base`, `orders/sets.py::OrderSet._visible_rows_sync` / `_visible_rows_async`,
  `permissions.py::_walk`, `optimizer/walker.py::_relation_child_seed` and
  `types/resolvers.py::_visible_related_object`; `_LeafChain.terminal_value` and `RelatedFilter.get_queryset`'s
  fallback keep `base_queryset`. Fakeshop `VisibleBranchType.get_queryset` now declares the city-less exclusion the
  `VisibleBranch` manager used to supply to the cascade (SDL unchanged). README hook-class paragraph,
  `types/base.py::DjangoType.get_queryset`, GLOSSARY pk 440 / 468 / 553, START "Verified and rejected", specs 003,
  023 (+ rationale), 027 (Decision 8 step 3, DoD 34), 033, 034 (+ rationale, the deviation from
  django-graphene-filters' `_default_manager`), 045, 060 and 062 follow. Pinned by
  `examples/fakeshop/test_query/test_library_inheritance_api.py`
  (`::test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_type_hook`,
  `::test_signage_filter_through_the_declared_branch_hop_reads_every_branch`,
  `::test_signage_filter_across_an_undeclared_hooked_branch_hop_reads_every_branch`,
  `::test_signage_order_by_a_hooked_branch_hop_reads_every_branch`,
  `::test_signage_cascade_over_an_identity_branch_type_reads_every_branch`,
  `::test_signage_branch_through_a_hooked_branch_type_resolves_every_branch`, sync and async) and package rows over
  `from_queryset`, hand-written and polymorphic-shaped managers in `tests/utils/test_querysets.py`,
  `tests/filters/test_sets.py` (`::test_declared_hop_reads_no_default_manager_annotation`,
  `::test_flat_hop_value_check_reads_no_default_manager_annotation`), `tests/orders/test_sets.py`,
  `tests/test_permissions.py`, `tests/optimizer/test_walker.py` and `tests/types/test_resolvers.py`. CHANGELOGTODO 907
- [x] 758. Already fixed by 70d4b42f (item 316): `filters/base.py::RangeFilter.filter` applies two bounds as
  `<bound_path>__range` through the transforms the declaration names, so a declared bare `year` / `date` over a
  datetime column and `year` over a date column keep the rows between the bounds on GraphQL, `apply_sync`,
  `apply_async`, raw form data and `DjangoFilterBackend`; reversed bounds answer no rows and equal bounds one year or
  day. At the filing commit f66d8216 all five reaches failed as the item says. Re-checked at 30bfb464 over 7
  declarations x 5 bound shapes x 5 reaches, every cell correct. Pinned by
  `examples/fakeshop/test_query/test_range_filter_declared_lookup_api.py::test_two_bounds_keep_the_rows_between_them_whatever_lookup_is_declared`
  (`occurred_on-year`, `occurred_at-date`, `occurred_at-year`; flat, `not` and raw form). No production change
- [x] 759. The `date` transform half of 684 is pinned: a declared `date` transform over a datetime column cleans its
  values as a date (`filters/base.py::_column_form_field` reads `_bound_value_field`), so a datetime stamp is refused
  and a day keeps its rows under an active zone ahead of UTC. Pinned live by
  `examples/fakeshop/test_query/test_range_filter_declared_lookup_api.py::test_two_date_bounds_keep_the_rows_between_them_in_a_zone_ahead_of_utc`
  (`date`, `date__exact`, `date__range`, `date__gte` two bounds under Asia/Tokyo; flat, `not` and raw) and
  `examples/fakeshop/test_query/test_scalars_filter_api.py::test_a_date_through_the_date_transform_keeps_its_day_in_a_zone_ahead_of_utc`
  (a declared `date__in` member and a bare `date` lone end; the UTC `date-list-in` row joins
  `::test_lookup_expr_transform_leaf_filters_by_its_output_and_a_method_by_its_column`), and at the package tier by
  `tests/filters/test_sets.py::test_a_datetime_stamp_through_a_declared_date_transform_is_no_valid_date` (a stamp
  refused "Enter a valid date." for `date__in`, `date__range` and a bare `date` lone end through raw form data and
  `apply_sync`; the live `Date` scalar refuses it first). The mutant `_bound_value_field` -> `_bound_model_field` now
  fails 9 new date rows on 6 shapes. Tests only
- [x] 847. A package `FilterSet` whose `filter_queryset` override adds or replaces a path before `super()` (an
  annotation or alias, one shadowing a name the handed queryset holds, a column past a `FilteredRelation` alias it
  adds) now cleans and bind-asks each `ListFilter` / `ArrayFilter` / `RangeFilter` value over the queryset the
  override passes on, before any flat leaf applies (`filters/sets.py::FilterSet._clean_late_comparisons`, first in
  `::FilterSet._apply_flat_leaves`): junk, `1.5` over an integer, an empty range box, `-1e1000000` and a range list of
  other than two members answer the form's error on raw drivers (DRF 400, a strict FilterView no row, a bare `.qs`
  applies the leaves that cleaned) and `FILTER_INVALID` under `apply_sync` / `apply_async`, logical-arm keys included,
  as over the handed queryset, where they raised an unmasked `ValueError` / `ValidationError` / `OverflowError` or
  silently dropped a junk list member. `FilterSet.is_valid` / `errors` build `qs` first to report the refusal
  (`::FilterSet._settle_late_comparisons`) only on a set that overrides `filter_queryset`
  (`utils/truth.py::overrides`) and only when no native form error already refuses the form; the bare
  `form.is_valid()` sees it only after `.qs`, and a `.qs` read before `is_valid()` runs the override twice with the
  same rows (the maintainer's consent is needed for a `qs` override, so none was added). `query` is threaded through
  `filters/base.py::_model_unresolved_query`, `::_bound_lookup_operand`, `::_bound_value_field`,
  `::_column_form_field` and the `_hand_column_field` implementations; `filters/sets.py::_unbindable_value_errors`
  takes `rows=` / `names=`; new `::_model_value_field` and `::FilterSet._late_comparison_names`. Grid: 450 of 4780
  cells move from an exception or a masked error to the handed answer, 0 row changes, late equal to handed in every
  cell. README, spec-027 (slice checklist, Decision 4, Decision 8, Edge cases, Test plan, DoD), the test README and
  GLOSSARY `FilterSet` (pk 463) follow. Pinned by `examples/fakeshop/test_query/test_raw_filter_forms_api.py`
  (`::test_a_raw_value_over_a_queryset_annotation_is_cleaned_as_the_queryset_compares_it`,
  `::test_a_path_the_filter_queryset_override_does_not_add_is_left_to_django`,
  `::test_a_package_set_asks_the_database_about_an_annotation_value`,
  `::test_a_bare_qs_read_applies_the_leaves_that_clean_and_reports_the_rest`,
  `::test_a_bare_qs_read_runs_the_sets_filter_queryset_once_more_than_is_valid_first`,
  `::test_the_bare_form_sees_a_late_refusal_only_once_qs_is_built`,
  `::test_a_set_with_no_filter_queryset_override_builds_no_qs_to_validate`,
  `::test_an_override_replacing_a_handed_annotation_cleans_the_value_it_compares`,
  `::test_a_native_form_error_answers_alone_beside_a_late_refusal`,
  `::test_a_raw_value_over_an_annotation_filter_queryset_adds_is_cleaned_by_every_driver`),
  `examples/fakeshop/test_query/test_scalar_predicate_binding_api.py::test_a_served_value_over_an_annotation_filter_queryset_adds_is_cleaned_as_it_compares`
  and `tests/filters/test_sets.py::test_an_unbound_set_is_invalid_and_holds_no_error_as_django_filters_is`. CHANGELOG:
  item 908

## To do: found along the way

- [ ] 762. (robustness) A ragged or over-deep member of an `in` over a nested `ArrayField` (`[[[1, [2]]]]` through an
  `apply_sync` JSON `where`, or raw form data) raises an unmasked `TypeError` ("Field 'igrid' expected a number") from
  `.qs` and `apply_sync` instead of a field-keyed `FILTER_INVALID`; the same at the parent of 692. PostgreSQL refuses
  ragged arrays anyway. Found verifying 692
- [ ] 764. (robustness) `utils/write_values.py::attempted_saves` connects `sender=model` exactly, so a serializer
  `create()` / `update()` saving a proxy or subclass row of the backing model leaves no record and a refused save of
  it answers the envelope where its `None` column's `null` applies (spec-039 Decision 8). Envelope at the parent and
  after 695. Found researching 695
- [ ] 766. `Decision N step M` sub-ordinals in first-party prose are ungated: 53 sites plus one `spec-NNN step M`, 52
  resolving (703 fixed the dangling spec-039 Decision 7 step 4 and the Decision-less spec-036 step). Root-cause fix:
  restate each by content and refuse `Decision N step M` in the citation gate, amending START.md's "a Decision's step
  ... judged by hand" in the same change; resolving step ordinals in `scripts/check_citations.py` would make them a
  second gated ordinal against START.md's "Cite contract by CONTENT, never ordinal". Found fixing 703
- [ ] 767. spec-040's Helper-reuse labels in first-party prose: `spec-040 D<N>` 26 sites, bare `D<N>` 17, `P<N>` 2
  (mainly `auth/mutations.py`, `mutations/resolvers.py`, `mutations/fields.py`, `mutations/inputs.py`); a plan-label
  family (565's class): name the behaviour and widen the plan-label row (START.md "Rule w/o gate rots"). Found
  fixing 703
- [ ] 768. (robustness) A `DjangoModelFormMutation` create omitting a column with a `db_default` writes `NULL`
  through Django's own form field (and a checkbox over a `BooleanField(default=True)` writes `False`, Django's
  checkbox exception in `construct_instance`) where the model flavor writes the default; pinned as Django's answer by
  `tests/forms/test_resolvers.py::test_modelform_create_omitting_a_nullable_column_with_a_default_keeps_djangos_answer`.
  Found fixing 704
- [ ] 770. (robustness) A declared non-Boolean filter with `lookup_expr="isnull"` publishes `Boolean`, and its own
  form cleans the bool as its own kind: 205 of 240 grid cells answer every value with an error (96 masked). Django's
  `IsNull` refuses a non-bool only at SQL compile, so 708's probe does not decide it
  (`filters/inputs.py::_catchall_element`'s null test). Found fixing 708
- [ ] 771. (robustness) A declared `class X(BaseInFilter, BooleanFilter)` answers every value with the masked
  `TypeError` from django-filter's `BooleanWidget.value_from_datadict` hashing the list the package binds, on every
  column; the generated `in` (`MembershipInFilter`) answers (`{"cBool": {"in": [true]}}` matches). Found fixing 708
- [ ] 772. (robustness) A declared filter past a transform whose own form cleans a kind the transform's lookup cannot
  prepare (`DateFilter(field_name="occurred_on", lookup_expr="year")`, published `Date`) answers `FILTER_INVALID` for
  every value; pinned as such by `examples/fakeshop/test_query/test_declared_temporal_bindability_api.py::_REFUSALS`
  (`year-of-a-date`, `typed-year-of-a-date`, `years-of-csv-dates`, `year-span-of-dates`), so refusing it at build
  moves pinned behaviour. A plain `AllValuesMultipleFilter(lookup_expr="year")` is the same class: it publishes the
  transform's `[Int!]` while its choices are the column's dates (`invalid_choice` for every year; from 733). Found
  fixing 708
- [ ] 779. A `NumberFilter(field_name="parent__twice")` past an undeclared hop whose target type's `get_queryset`
  annotates `twice` answers a masked `AttributeError: 'IntegerField' object has no attribute 'model'`
  (`filters/sets.py::_held_integer_value` -> `_queryset_integer_column` -> `utils/relations.py::_walk_lookup_expr`
  reads `cached_col` on the annotation's unbound `output_field`); the same name past a declared `RelatedFilter` hop
  answers. Found researching 776
- [ ] 783. (robustness) A declared `MultipleChoiceFilter` / `ModelMultipleChoiceFilter` (`exact`) with a lazy
  `field_name` (`gettext_lazy("children__label")`) gives one declaration two answers: unwalked, django-filter's
  `MultipleChoiceFilter.get_filter_predicate` keys the predicate by the lazy object and the request raises
  `TypeError: keywords must be strings`; walked, `filters/sets.py::FilterSet._bound_terminal` rebinds `field_name` to
  a str path and the request answers rows. 780 aligns a to-many relation key only; a target path and a two-hop walk
  still split. Found researching 780
- [ ] 786. (robustness) A `ModelForm`'s default `forms.JSONField` over a `JSONField` re-parses a decoded JSON
  string as JSON text: the JSON string `"hi"` sent is refused "Enter a valid JSON.", the JSON string `'{"a": 1}'` is
  stored as the object, and an update omitting the field over a stored JSON string is refused the same way, though the
  input is typed `JSON` by the column (docs/README.md "Form mutations"). Likely fix: bind the form field's
  `prepare_value` of the decoded value. Found researching 720
- [ ] 787. (robustness, lead, unprobed) A `DateField` / `DecimalField` / `UUIDField` form field over a `JSONField` with
  no encoder hands the column a value its JSON encoder cannot encode, failing at save; the filter side refuses the
  same kind at build (`filters/inputs.py::_refuse_kind_json_cannot_encode`), the form side does not. Found researching
  720
- [ ] 789. (robustness) A shipped `ModelMultipleChoiceFilter(conjoined=True)` on a to-many relation key a flat leaf
  walks (a `RelatedFilter` on the relation, or a target type with its own `get_queryset`) answers no row where
  unwalked answers (`ScalarSpecimen.children` naming two children: walked `[]`, unwalked `['p1']`): each AND is re-read
  on the target key column over a single target row (`filters/sets.py::FilterSet._leaf_chain`,
  `_LeafChain.terminal_value`). One declaration, two answers (GOAL "Trust boundary"). Found researching 784
- [ ] 795. (robustness) A consumer `filter` override on a flat leaf a hop walks, on a forward relation key or a path
  into a target column, that returns a new queryset when it constrains nothing (`return qs.distinct()` or `qs.all()` on
  an empty value) reads as constraining, so supplied empty or left out it keeps only the parents that reach a visible
  related row, where unwalked and django-filter keep every row: the identity-as-no-op rule on the rebound rows plus the
  EXISTS fold, not the double run. A to-many key's override answers as unwalked (item 796). Found researching 790
- [ ] 813. (robustness) On SQLite a stored `GeneratedField` whose `output_field` is a bounded `DecimalField`
  (`GeneratedField(expression=F("price") * 1000, output_field=DecimalField(20, 4), db_persist=True)`) computes a value
  its read-back converter refuses (`price` `9999999999999.9999`), and Django's `INSERT ... RETURNING` converters raise
  `decimal.InvalidOperation` inside `save()`: a masked top-level error on every write flavor. The write rule never asks
  it (the column is computed, not written); PostgreSQL stores it. Found verifying 726
- [ ] 816. (robustness) A filter declared over a `GeneratedField` whose `output_field` no filter converts (a consumer
  column class with no `SCALAR_MAP` entry, or a `FileField`) is refused at build with the DjangoType advice
  (`types/converters.py::generated_output_field`: "Add an entry to SCALAR_MAP or exclude this field via Meta.exclude." /
  "Exclude the field via Meta.exclude."), raised inside `_registered_scalar_entry` before the FilterSet's own refusal
  (`filters/inputs.py::_unscalared_field_refusal`) can name the filter and a remedy a `FilterSet` has. Pinned on the
  filter path by `tests/types/test_converters.py::test_generated_column_refuses_an_output_no_conversion_publishes`.
  Found fixing 730
- [ ] 854. (robustness) A `RelatedFilter(queryset=...)` pinned with `.using()` to an alias the request does not read
  is refused with Django's cross-database `ValueError` from the `IN` subquery (masked on the wire, bare from a raw
  `FilterSet(...).qs`), where the same pin from a target type's `get_queryset` gets a typed `ConfigurationError`
  naming the alias (`utils/querysets.py`). A primary/replica router with `queryset=Model.objects.using("default")`
  while reads route to a replica reaches it. Found researching 818
- [ ] 822. (robustness) `AllValuesMultipleFilter` inside a CSV wrapper (`class X(BaseInFilter,
  AllValuesMultipleFilter)`, declared, on a text column) builds and answers `FILTER_INVALID` `invalid_list` ("Enter a
  list of values.") for every value: its form field is built per request, so the build-time no-value ask
  (`filters/inputs.py::_refuse_form_serving_no_value`) never sees it. Found fixing 735
- [ ] 823. (robustness) A scalar `TypedChoiceFilter` on a choice column whose `coerce` turns its keys into no value of
  the column (`TypedChoiceFilter(field_name="condition", choices=[("good", ...), ("1", ...)], coerce=int)` on
  `Shelf.condition`) builds and serves nothing: the choice arm of `filters/inputs.py::convert_filter_to_input_annotation`
  never runs the no-value ask, and 538's `valid_value` check accepts `good` before the coerce. Found fixing 735
- [ ] 824. (robustness) A `TypedChoiceFilter` (or its CSV wrapper) with `coerce=decimal.Decimal` and a key no decimal
  spells (`choices=[("all", ...), ("1.5", ...)]` on a `DecimalField`) answers a masked `decimal.InvalidOperation` when
  a request sends that key: Django's `TypedChoiceField._coerce` turns only `ValueError` / `TypeError` /
  `ValidationError` into its `invalid_choice`. The schema builds (the key `1.5` answers). Found verifying 735
- [ ] 826. (robustness) A CSV `MultipleChoiceFilter` (`class X(BaseInFilter, MultipleChoiceFilter)`) with deferred
  `choices` (a callable, a `lazy()` promise, a `SimpleLazyObject`, a `QuerySet` or a `CallableChoiceIterator`) on a text
  column builds and answers `FILTER_INVALID` `invalid_list` for every value: its refusal does not depend on the choices,
  but the no-value ask (`filters/inputs.py::_refuse_form_serving_no_value`) skips a choice form's keys when they are
  deferred, and a text column has no scalar samples. Found fixing 738
- [ ] 827. (robustness) A declared filter's `field` override that reads its deferred `choices` as the declared type
  (`self.extra["choices"].filter(...)` on a `QuerySet`) raises `AttributeError` on the schema build's copy, whose
  choices are `filters/base.py::_UnreadChoices`; `filters/inputs.py::_declared_form_field` and
  `filters/sets.py::_widget_keys` read that `AttributeError` as "builds no field", so the build's widget and no-value
  checks are skipped for the leaf without a word. The schema and every request answer as without the package. Found
  verifying 738
- [ ] 829. (robustness) On a set no connection serves (`FilterSet(data, queryset).qs`, `apply_sync`), a
  `Meta.filter_overrides={ArrayField: {"filter_class": ArrayFilter}}` text-pattern leaf over an `ArrayField`
  (`arr__icontains=1`, from a per-field `"__all__"` or listed) cleans its value into a list and compiles a match
  against that list's Python repr (`UPPER("arr"::text) LIKE '%[DECIMAL('1')]%'`), silently matching nothing a consumer
  means; Django compares the column's text rendering (`{1,2}`) with a string. Found fixing 739
- [ ] 832. (robustness) A flat key into a `RelatedFilter` target set over a multi-table-inheritance descendant
  answers a Django `FieldError` for every nonempty value, whatever its GlobalID strategy: `RepairTicketFilter.venue =
  RelatedFilter(SelfServeDeskFilter, field_name="venue")` publishes `venueFaults`, which applies `venue__faults` from a
  `Venue` relation where only `venue__lendingdesk__selfservedesk__faults` resolves ("Unsupported lookup 'faults' for
  ForeignKey or join on the field not permitted", `filters/sets.py::_apply_relation_leaf`; a class-level `filter`
  override answers "Venue has no field named 'faults'" from `::_names_every_through`). The nested branch serves. Found
  fact-finding 745
- [ ] 838. (robustness) An unbound or absent `RelatedFilter` head's rendered form field (django-filter's `FilterView`
  page, DRF's browsable API through `DjangoFilterBackend.to_html`) lists every row of the declaration's queryset as a
  choice, rows the target type's `get_queryset` hides included, so the rendered page names hidden rows; a bound named
  head narrows its choices to the visible rows (748). Found fixing 748
- [ ] 844. (robustness) A walked relation-key null sentinel, a declared `ModelChoiceFilter` /
  `ModelMultipleChoiceFilter` under `null_label` (forward or to-many, shipped or overriding `filter`) sent its
  `null_value`, matches nothing, where django-filter answers the relation's null test (`<relation>=None`); a raw head
  under `null_label` answers it since 748. A to-many `ModelChoiceFilter(null_label=...)` overriding `filter`, sent
  `null` or its `null_value="0"`, answers `[]` at `fe4eb38f`, pinned as unchanged by
  `tests/filters/test_sets.py::test_a_declared_model_choice_override_keeps_its_null_value_routing`. Found fixing 748
- [ ] 852. (robustness) A `required=True` own filter of a served set is not enforced over GraphQL when the request
  omits it: `filter: {}` (or a `filter:` naming only other keys) answers every row, under the package's and
  django-filter's form builders alike, while README says a `required` filter acts on the form of the set that declares
  it, at that set's root, and a directly built set refuses it
  (`tests/filters/test_sets.py::test_a_directly_built_set_takes_required_from_the_keys_owner`). Found fixing 216
- [ ] 862. (robustness) The `ArrayField` input gate (`filters/inputs.py::_array_element_column` /
  `_array_column_refusal`) runs only at input build, so on a set no connection serves a `ListFilter` / `ArrayFilter`
  with `iexact` / `icontains` / `startswith` / `regex` / `isnull` over an `ArrayField` (and a CSV, choice or scalar
  filter over one) builds and fails per request. Found fixing 716
- [ ] 863. (robustness) A `ListFilter` / `ArrayFilter` whose path ends on an annotation or a `FilteredRelation`
  alias resolves no lookup when its set publishes, so `filters/base.py::refuse_listless_lookup` does not judge it and
  a scalar lookup (`exact`) there fails per request; a request-time check through `_bound_lookup_operand` would reach
  it. Found fixing 716
- [ ] 864. (robustness) The `ArrayField` input gate judges a `method=` filter over an array by its key name: a
  `method=` `ListFilter` with `lookup_expr="in"` over an `ArrayField` is refused, though the method reads the list and
  applies no lookup. Found fixing 716
- [ ] 866. An order term ending on a `to_field` column under a declared hop (`[{kiosk_rel: {kiosk_code:
  ASC}}]`, path `kiosk__kiosk_code`) whose target set is bound to a hiding type of the related model drops a row whose
  non-null `db_constraint=False` key names no row, for every actor, where Django's `order_by("kiosk__kiosk_code")`
  trims the join and keeps it (spec-028 Decision 8 step 4: a test never removes a row the plain term keeps). The
  visibility test joins through `<relation>__pk`; passing the relation when the term's column is its target column
  would correlate on the carriers. Found verifying 752
- [ ] 867. (robustness) A wired `OrderSet` whose `RelatedOrder` two sets down names a lazy target that cannot import
  raises a bare `ImportError` at `finalize_django_types()`, where a direct unresolved target is rewrapped as a
  `ConfigurationError` naming the declaration and the filter family rewraps both
  (`tests/orders/test_finalizer.py::test_an_unresolved_target_two_sets_down_raises_its_import_error_at_finalize` pins
  the bare error). Found fixing 752
- [ ] 870. (robustness) A `ModelMultipleChoiceFilter` with a `to_field_name` on a to-many relation key answers by the
  `to_field_name` column walked and by the target key unwalked: `field_name="issues", to_field_name="number"` on a
  `Periodical` set answers `[]` at the root (django-filter's `issues=100` against the Issue pk) and the issues
  numbered 100 / 101 through a flat or raw parent key (`filters/sets.py::_LeafChain.terminal_value` /
  `_relation_key_value` re-read the cleaned instances' keys). One declaration, two answers, the 789 family; a forward
  key (`CardItem.card`, `number`) answers `[]` both ways. Found fact-finding 819
- [ ] 879. (robustness) A model-choice filter declared with an explicit `queryset=None` builds its form (its set's
  other keys answer), then a request supplying it raises a bare `AttributeError` at clean (`'NoneType' object has no
  attribute 'model'`; a `ModelMultipleChoiceFilter` raises it cleaning an empty value too), masked over GraphQL, where
  the absent-queryset shape is refused when its set publishes (756). Stock django-filter fails the same way. Found
  verifying 756
- [ ] 881. (robustness) A shipped filter whose `field_name` continues past a `GenericForeignKey`
  (`CharFilter(field_name="content_object__name")`) builds on a served and an unserved set alike (the input types it
  `String` from no field) and fails every request carrying a value with Django's `FieldError` (`Query.names_to_path`),
  masked over a resolver; `filters/inputs.py::refuse_joinless_relation` judges only a path ending on one. Found
  researching 877
- [ ] 906. (robustness) A `GlobalIDFilter` whose `field_name` names a `FilteredRelation` alias (`field_name="vshelf"`)
  is not judged when its set publishes: the build-time GlobalID checks (`filters/sets.py::_globalid_decode_sites`)
  cannot see an alias, which only the queryset holds, so its key checks no type name against the alias's target and an
  encode-only target over the alias is refused per request instead of at build. Found fixing 792
- [ ] 909. (robustness) A `FilteredRelation` alias a package `FilterSet.filter_queryset` override adds
  (`super().filter_queryset(queryset.alias(kids=FilteredRelation("issues")))`), compared as the relation itself by
  `ListFilter(field_name="kids", lookup_expr="in")` or `RangeFilter(field_name="kids", lookup_expr="exact")`, is not
  cleaned: raw `?kid=abc` / `?kidr_0=abc`, `kid=4.5` and `kid=-1e1000000,4` raise Django's unmasked `ValueError` (a
  masked error over GraphQL under `apply_sync` / `apply_async`), where the same set handed the alias answers the
  form's error or drops the member. `filters/base.py::_compared_value_column` (through `_bound_lookup_lhs_path`) and
  `::_integer_in_column` read the handed queryset; cleaning alone leaves `kid=4.5` answering a truncated key's row, so
  the filter-time member drop takes the receiving query too. Found fixing 847
- [ ] 910. (robustness) A stock `django_filters.FilterSet` parent declaring the package's `RangeFilter` / `ListFilter`
  / `ArrayFilter` over an annotation its own `filter_queryset` adds before `super()`
  (`qs.annotate(n=Count("issues"))`), served by `DjangoFilterBackend` / `FilterView` or called directly, never cleans
  the value: `?n_0=abc`, `?n_0=1.5`, `?n_1=` and `?n_0=-1e1000000` raise an unmasked `ValueError` / `ValidationError`
  / `OverflowError` and `?n=1,abc` silently drops the junk member, while README promises the package filters clean
  under any django-filter `FilterSet` parent (it holds for a handed annotation). The stock parent has no
  `_apply_flat_leaves` / `is_valid` seam, so the fix site is the filter (`RangeFilter.filter` / `ListFilter.filter`
  cleaning over `qs.query`). Found fixing 847

## To do: holes found re-checking the fixes


## Waiting on you

- [ ] 839. Decide: a declared hop whose target model has no registered `DjangoType`. A walked key through it is refused
  (spec-027 Decision 8, `FilterSet._branch_visibility_seed`'s `ConfigurationError`); since 836 a raw `FilterSet`
  (`FilterSet(data=...)`, `DjangoFilterBackend`, `FilterView`) carries its walked keys, so a raw walked key over such a
  hop follows the same rule and a DRF-only project with no `DjangoType` gets a 500 for that key, while own keys and a
  raw `RelatedFilter` head reading it keep only the declaration's queryset, unwalked (748 kept the shape that worked).
  Refuse the head too, or let walked keys apply the declaration scope alone? (Found fixing 748)
- [ ] 820. Decide: which values a choices-reading filter copied flat from a `RelatedFilter` child set validates
  against. Its form field is built once for the parent's copy, so a flat copy validates against the values the
  parent's rows reach, while the nested branch validates against the child's own: `shelfCodeValues: ["D-4"]` (a code
  only an unreached shelf holds) is `invalid_choice` flat and rows `[]` nested, and a nullable key's `["None"]` is rows
  `[]` flat and `FILTER_INVALID` nested. Rebuilding the field on the walk's target changes what the flat copy refuses,
  a validation contract no rule settles. (Found fixing 734)
- [ ] 729. Decide: the to-one shape for the relation-quantifier contract change. The ruled part: `{}` constrains
  nothing everywhere and a to-many `RelatedFilter` is typed as a per-target `some` / `none` / `every` wrapper (Prisma's
  shape), which retires spec-027's contradictory `apply_async` sentence (a present nested branch is active whatever its
  inner value, `utils/permissions.py::active_related_branches`, so `{shelves: {}}` keeps only the parents with a
  visible, admitted shelf today). Once `{}` constrains nothing, a bare to-one `branch: {}` loses its only nested
  "has a branch" spelling, so the to-one input changes too, and the plan
  (`docs/relation-quantifiers-plan.md` D3) leaves it open: (a) a to-one wrapper `{is, isNot, isNull}`, which reshapes
  every nested to-one query; (b) the bare nested input stays plus a parent-level `<rel>IsNull: Boolean` sibling, refused
  at build where it collides with a flat copy or own filter of that name (recommended there); or (c) an explicit
  `branch: null` meaning "has no branch". The names are a one-way door no rule settles. Also open there: does an empty
  wrapper `shelves: {}` still fire the parent's `check_<rel>_permission` (D6, recommended yes), and the plan, still v1
  and unreviewed, recommends that 216 land first. (Found planning 216)
- [ ] 809. Decide: the to-many relation view cannot join some first keys round their target, so a to-many override whose
  value names no row, on a path starting at such a key, still drops a parent whose first related row is hidden: a
  non-null forward key whose reverse Django names no way (`related_name="+"`), a bare `ForeignObject` or a
  `db_constraint=False` key (its key may name no row, and the round trip's first join is inner), and a non-null key onto
  a multi-table-inheritance child or a proxy of one (Django joins the child's parent tables ahead of the round trip's
  outer join, which the database refuses). Pinned: `ShelfLabel.shelf__books` and `KioskFault.kiosk__repairticket` live;
  the `_round_trip` unit cases. Keep it as a stated limit, an `EXISTS`-based absence predicate for these keys (breaks
  path continuations past the alias), or a private `Join.nullable` promotion (not a public seam)? (Found fixing 807)
- [ ] 799. Decide: should a class-level `filter` override on a walked relation key run through the relation view (items
  796, 807) in two more cases, an `isnull` override whatever its value and a forward key's override whose value names no
  row? Today both keep the earlier re-bind: a `null` or left-out value an `isnull` override reads as `True` answers `[]`
  where unwalked answers the parents with no related row, and a forward override reading an empty choice as `None`, a
  default, `<field_name>_id` or `qs.distinct()` drops parents with a `NULL` or hidden key. Routing the `isnull` override
  alone fixes 752 cells of the research grid; adding the forward fallback fixes 2534, plus 2800 in a wider isnull probe.
  The cost: the view's alias is a `FilteredRelation`, so an override's `only()` / `prefetch_related(self.field_name)`
  raises Django's `ValueError` (470 cells correct today from the `isnull` routing alone; the fallback adds 36 grid and
  90 probe cells), and `<field_name>_id` past a to-many hop raises `FieldError` (the override must read
  `<field_name>__pk`). Route both and state those as the override's contract, route neither (today), or route only the
  forward fallback? The round-trip limits of 809 apply. (The maintainer chose "nothing breaks" for this pass; the routed
  design was built and verified)
- [ ] 800. Decide: a class-level `filter` override on a many-to-many key a flat leaf walks, where Django gives the
  through key onto the source no reverse name of its own (an auto-created self-referential many-to-many read forward,
  symmetrical or not; an explicit through whose two keys onto the model share `related_name="+"`), still runs on the
  key-column fallback when its value names no row (`filters/sets.py::_names_every_through`): an instance or queryset
  default raises a masked `TypeError`, a path past the relation raises `Unsupported lookup`, and an `isnull=True`
  default answers `[]` where unwalked answers rows. No public Django construction conditions that through join
  (`ManyToManyField._get_path_info` conditions the target join only; `Query.add_filtered_relation` refuses paths outside
  the relation; the shared hidden name resolves to the other key; checked on 5.2.16 to 6.1.3). A target-join-only
  `FilteredRelation` makes a NULL test depend on a through row onto a hidden target; reading a symmetrical relation's
  mirrored side answers a one-direction through row (Django's documented through access writes them) differently from
  HEAD. A private construction that writes the condition into the through join's ON clause answers every
  single-reference cell exactly, but Django's join reuse then either gives a second reference in one `filter()` call its
  own join pair (an AND of two conditions on the alias matches rows unwalked does not, where HEAD raised) or, if the
  conditioned join is made reusable, lets later joins on the returned queryset (`order_by`, `annotate`) read only
  visible-target through rows and changes row counts HEAD answers correctly. Keep the fallback (and state it), accept
  one of those trade-offs, or take a deeper private rewrite of Django's join bookkeeping? (Found fixing 796)
- [ ] 803. Decide: should a to-many `orderBy` read only the related rows a filter on the same relation matched? Today an
  unwalked plain filter (a shipped `ModelMultipleChoiceFilter` or a key override on `shelves`) sorts `shelvesCode` by
  the matched shelves (Django reuses the filter's join for the order's `Min`), while a walked leaf, a key override's
  names-no-row relation view (796) and an unwalked generated column leaf (`shelvesCode: {in: ...}`, the row-preserving
  `EXISTS` fold) sort by every visible shelf; fakeshop `allLibraryBranches(filter: {altShelves: ...}, orderBy:
  [{altShelvesTopic: ASC}])` shows it. No doc states either reading and no upstream aggregates (each `order_by`s plainly
  and duplicates parents). Pick one reading for every filter kind, or state that a to-many order reads every visible
  related row (and accept the unwalked join-reuse exception)? (item 801)
- [ ] 805. Decide whether the package's own `ListFilter` / `ArrayFilter` / `RangeFilter` declared on a plain
  `django_filters.FilterSet` parent hold a duration member or bound to the backend's integer range. The bind ask lives
  on the package `FilterSet`'s form, so on a plain parent a `ListFilter` `in` over a `DurationField` sent
  `999999999 00:00:00` through `DjangoFilterBackend` raises `OverflowError` on SQLite and MySQL, as django-filter's own
  `BaseInFilter` + `DurationFilter` does there. Options: drop the member in the class (as an integer column's `in`
  drops, `filters/base.py::_identifying_members`), which diverges from the package parent's refusal; or document that a
  foreign parent answers as django-filter. (item 724)
- [ ] 790. Decide: a flat leaf the request leaves out, whose path a hop walks (a `RelatedFilter`, a target type's own
  `get_queryset`), runs a consumer `filter` override that acts on the empty value twice
  (`filters/sets.py::FilterSet._absent_leaf_applies` runs it over the unscoped rows to learn whether it constrains,
  then `_apply_relation_leaf` runs it over the visible rows), where unwalked and django-filter run it once (a default
  read twice, its query doubled; three to four runs in a logical arm, six for a `ModelMultipleChoiceFilter` key whose
  fresh empty `QuerySet` never equals the recorded verdict). Item 399 scoped "once per value" to supplied values and
  kept this probe on purpose. Every one-call fix measured narrows a shape that works today:
  reusing the probe's result (`visible & result`) fails on every `.distinct()` terminal, and `pk__in` reuse lets a
  hidden row decide a visible answer for an override reading the queryset's latest row; caching where rows provably
  match covers only a one-forward-hop key. The best candidate derives the hops of an absent leaf whose terminal runs
  consumer code and runs it once over the visible rows, as a supplied value does (561), keeping the probe for shipped
  code and for a hop with no resolvable child set or registered type: consumer runs equal unwalked in all 2352 walked
  grid cells and the arm re-probe closes, but an inert absent consumer leaf now runs the target `get_queryset` (+1 hook
  per hop; spec-027 "derives nothing unless it does"), `apply_sync` / raw form `.qs` over an async-only `get_queryset`
  turn rows into the `RuntimeError` naming `apply_async`, and an override reading queryset state decides activity on
  the visible rows. Accept that trade (561's own precedent for a supplied `""`), or keep two runs and state them where
  the README, the `FilterSet` glossary row, `filters/sets.py::_KeyMatch` and CHANGELOGTODO 791 say a key override
  "runs once as declared"?
- [ ] 655. Decide: on PostgreSQL a `year` / `month` transform `in` member or `range` bound between 2**31 and 2**63 is
  refused as `FILTER_INVALID` (the transform binds an `IntegerField`, int32 there; 385), while Django's own
  `IntegerFieldOverflow` answers `month__gt=2**31` as no / every row and the package's integer-column `in` drops such
  a member. Keep the refusal, or answer it as Django does (drop the member; clamp the bound)?
- [ ] 601. Decide whether a filter a `get_filters()` override adds (undeclared, so absent from
  `declared_filters`) gates on its own name (`check_<name>_permission`) like a declared filter, or on its
  `field_name` as it does now (`filters/inputs.py::leaf_gate_path`; pinned by
  `tests/filters/test_sets.py::test_a_filter_a_get_filters_override_adds_is_gated_on_its_field_name`): moving
  a declaration into an override silently swaps `check_extra_permission` for `check_topic_permission`. Found
  researching 599
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
- [ ] 641. `AllValuesFilter` / `AllValuesMultipleFilter` build their choices from the model's unscoped
  `_default_manager.distinct()` (django-filter's rule), so over a type whose `get_queryset` hides a row a value only
  that row holds answers no rows while a value no row holds answers `invalid_choice`: an existence oracle, live at
  the parent on choice columns and, after 515, on text columns through `AllValuesMultipleFilter`; it also runs one
  DISTINCT per filtered request even when the leaf is unsent. GLOSSARY "Choice leaves" documents it and the
  consumer remedy. Should the package scope the choices to the bound copy's `parent.queryset` (in
  `sets.py::FilterSet._copy_filter`, honouring a consumer `field` override; a flat hop leaf needs its hop's
  visibility), changing what a DRF view over the same `FilterSet` sees, or keep django-filter's rule?
- [ ] 594. A model whose `Meta.db_table` is a lazy translation string (`gettext_lazy("products_category")`):
  Django serves `all()`, `order_by()`, `filter()` and both `union()` forms over it, but
  `utils/querysets.py::_seal_or_defect` refuses `filter()` and a baked `union()` ("query alias_refcount has
  a non-string key") and an unbaked `all().union(all())` ("QuerySet binds a __proxy__ bound value"),
  while `all()` and `order_by()` seal. Should the seal admit a lazy table name as the exact text it spells,
  as it admits a `TextChoices` / `StrEnum` member (d1bb1e97), refuse it at schema build, or treat a lazy
  `db_table` as outside the supported shapes (Django documents a string)? Pinned refused by
  `tests/utils/test_querysets.py::test_lazy_db_table_combination_rewrite_fails_closed_typed`
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
  Options: refuse it with `FILTER_INVALID` at the `filters/sets.py::_unbindable_value_errors` seam, which already
  reads every declared filter's cleaned value and, as part of the filter form's clean, reaches the raw drivers too
  (backend-independent, so it narrows what PostgreSQL client-side answers today); or document django-filter's
  behaviour and name the package's `RangeFilter` / `ListFilter` as the remedy.
  Rewriting the declared filter's own `filter()` call would bypass a consumer subclass and its `exclude` / `distinct`.
  Found fixing 507
- [ ] 576. Decide how a PostgreSQL form field with no model column behind it (a plain `Form` field or a `ModelForm`
  extra field) is published. Today `SimpleArrayField` is `String` by its `CharField` ancestry: the client sends
  delimited text, cannot send an element holding the delimiter, and JSON text is split on commas, while the same field
  over an `ArrayField` column takes the column's list and the sibling list readers off-column are lists
  (`MultipleChoiceField` `[String!]`, `JSONField` `JSON`, the serializer flavor's `ListField` `list[child]`);
  `SplitArrayField` (552) and the range form fields raise `ConfigurationError` at build, `HStoreField` is `String`.
  Publishing `SimpleArrayField` as the base field's list changes existing schemas' SDL and needs the element type from
  `base_field` (nested arrays, element nullability); graphene-django publishes `String` for all of them. Found fixing
  551
- [ ] 571. Decide whether a `regex` / `iRegex` filter operand the backend refuses answers `FILTER_INVALID` keyed to
  its leaf instead of the masked error. Every refused filter value the package codes today is checked before the
  queryset runs (`FilterSet._validate_form_or_raise`), and only the filter step knows the leaf; after execution the
  error carries no field (and on SQLite not even its `re.error`). A faithful check has to ask the backend, as
  `utils/errors.py::unbindable_temporal` does: Python `re.compile` (warnings caught) is exact for SQLite only, and
  depends on the interpreter; PostgreSQL needs its own probe (`SELECT '' ~ %s`, savepointed inside a transaction),
  since `re` both refuses valid ARE (`\m`, `\y`, `(?b)`, POSIX classes) and accepts invalid ones (`(?P<n>...)`, atomic
  groups, `\z`); MySQL and Oracle have no probe measured. Promising it changes SQLite's empty-table or all-NULL `[]`
  into `FILTER_INVALID`. Upstream answers the raw error everywhere. Found fixing 549
- [ ] 522. Feature card? A value plus lookup input for `LookupChoiceFilter` (lookup as an enum of its
  `lookup_choices`), so it filters over GraphQL instead of being refused at build; no upstream (graphene-django,
  django-graphene-filters, strawberry-django) publishes one.
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
- [ ] 461. Decide whether `strictness` reports the per-parent re-reads that remain after 380 (a consumer `Prefetch`
  seed over another model, a consumer lookup deeper than the planned path or on a `SKIP`-hinted relation onto a hooked
  target): each answers correctly but costs one query per parent and `types/resolvers.py::_check_n1` stays silent
  (it asks only the instance cache); reporting them under `strictness="raise"` would error queries that answer today
- [ ] 351. A column-backed `ModelChoiceField` / `ModelMultipleChoiceField` declared with a class-level `queryset=None`
  that no `__init__` or `get_form` assigns builds, and every request binding it fails with Django's raw
  `AttributeError` (`'NoneType' object has no attribute 'model'` / `'filter'`) inside `is_valid()`, because
  `forms/resolvers.py::_assert_bound_choice_agreement` leaves a queryset-less bound field to the form (the documented
  row; Django's own form fails the same way). Found landing 340. Decide: keep it Django's error, or refuse a bound
  queryset-less field with a `ConfigurationError` at request time
- [ ] 321. The write side passes a `relay.NodeID` over a non-column attribute (one the type's `get_queryset`
  annotates) through as the raw primary key (`relay.py::_resolve_real_pk`, pinned by
  `tests/test_relay_node_field.py::test_decode_model_global_id_passes_raw_value_for_non_field_node_id`), so a relation
  write naming such a type stores whichever row's pk equals the id's text, while the filter side now refuses that slot
  across a relation (`GLOBALID_UNVALIDATABLE`). Refuse it on writes too, or keep the pass-through? Found landing 290
  - Premise changed by 858: the filter side now compares such an id across a relation on the rows the type's
    `get_queryset` returns (refusing only over rows another type scopes, or in a key whose class overrides
    `filter`); regrade before working this.
- [ ] 281. A `GenericForeignKey` written beside its carriers: a serializer with writable `content_object` and writable
  `object_id` / `content_type` builds, and a request pairing a visible object's id with another row's `objectId` stores
  that row (a writable `object_id` alone is already a raw write); post-save attestation covers single-column FK /
  one-to-one and many-to-many only, so a custom `update()` dropping `content_object` succeeds unattested. Refuse
  carriers beside their GFK (and a `ForeignObject` beside its carriers, accepted on purpose today), attest the GFK
  columns, or keep?
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
- [ ] 77. The read enum refuses a grouped-choices column, though group labels are presentation like choice labels. Flatten it on
  the read side too (retires the `str`-override carve-out and the write-side grouped refusal), or keep?
- [ ] 73. A set subclass used only as a `RelatedFilter` / `RelatedOrder` target, never wired to a type, inherits its base's owner and
  that owner's visibility. Keep, or fall back to the target model's registered type? It also crosses models: an unwired
  `Sub(Base)` on another model reads `Base`'s owner, so its own-pk filter becomes a `GlobalIDFilter` under a relay owner
- [ ] 84. `range: []` applies no constraint on every generated `range` (and `range: [1]` is a validation error), where Django
  raises on both. Make `[]` an arity error like `[1]`, or keep?
- [ ] 85. A nested branch that constrains nothing (`shelves: {}`, `shelves: { condition: { in: null } }`) still keeps only parents
  with a visible child (`_apply_related_constraints`), at the top level and inside `and` / `or` / `not`; strawberry-django treats
  it as no condition. Make it the identity, or keep (and state it in spec-027 Decision 8)?
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
- [ ] 94. The package's 231 `except BaseException` guards follow two postures: about 90 hostile-metadata guards turn a
  `KeyboardInterrupt` / `SystemExit` into a typed error (pinned, e.g. `serializer_field_description`), while `utils/directives.py`
  and the await-side guards let control signals propagate (pinned the other way). No upstream library converts them at
  configuration time. One policy (re-raise control signals first, or narrow to `Exception`), or keep the split?
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
- [ ] 201. Item 116 (`e05b2436`) choices awaiting your ruling: `schema=` stays optional; under a swap converter four
  cross-schema cells stay wrong (documented); an ambiguous unpublished plain type name now refuses where it was
  accepted. Accept or change
- [ ] 202. Failability rows that each kill a mutant with one row only: items 139 and 140 (`4ed767bb`) mutants 4, 5, 7
  and 8 (8 only by a 30 s timeout), item 116's rebased run at 1 of 10 entries, three precedence mutants graded weakly
  pinned. Accept or add rows
- [ ] 203. Fold the implementer notes into START.md: items 14, 83, 95, 116, 119, 139 and 140 (plan-to-resolver
  channels key by `resolver_key`, never `to_attr`; a nested window under the async view needs an async
  `DjangoConnectionField` root; a harness written against a prototype API fails as a `TypeError` that reads as a
  regression; a subprocess test that signals before its syscall flakes)
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
- [ ] 217. A subclass of a `FilterSet` in a `RelatedFilter` cycle publishes one lap more than its parent (the cycle closes at
  the parent class, not the subclass); decide whether a subclass should close the cycle at itself
- [ ] 219. Strawberry's own `ListConnection` (0.327.7 and 0.334.4) fails `assert last is not None` when `after + 1 + first`
  equals `sys.maxsize` (its `SliceMetadata` last-only sentinel) and overruns `islice`'s stop past it on an iterator source;
  the package now keeps its pages clear of both. Report it upstream?
- [ ] 262. Decide whether a partial `ModelForm` update's explicit `null` on a `null=True` text column stores `NULL`:
  Django's `TextField.formfield` sets no `empty_value=None` (`CharField.formfield` does), so `subtitle: null` on a
  book whose `subtitle` is `TextField(blank=True, null=True)` writes `''`, as a `CharField` over a `null=True`
  `CharField` does. 620 stores `NULL` for every other `null=True` column whose form field cleans the `None` to a
  value, and keeps a text column's `""` by one clause in `forms/resolvers.py::_coerced_null_fields`
  (`field.null and field.empty_strings_allowed and value == ""`), so deciding "store NULL" is deleting that clause.
  The omitted half closed with 524: an update omitting the column keeps its stored `NULL`

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
- [ ] 722. Decide whether a `RangeFilter` whose `field_name` is a relation should continue to its key column. Since
  527 a lone bound under a non-range `lookup_expr` (`gte`, `exact`) is cleaned as the key column, but an overflowing
  bound still binds raw through Django's related lookups (`OverflowError`, a 500); continuing to the key column would
  fix that and also make a two-bound `range` on a relation work, which reverses item 375 (Django registers no
  `range` lookup on a relation, and django-filter's own `RangeFilter` fails the same way). Found fixing 527
- [ ] 727. Decide what a serializer field laxer than its bounded column gets: a declared
  `serializers.DecimalField(max_digits=None, decimal_places=None)` over `DecimalField(max_digits=10,
  decimal_places=2)` passes values the column refuses, and DRF runs no model validator on a declared field, so the
  write ends masked (PostgreSQL's typmod `DataError`; on SQLite the re-fetch's `InvalidOperation` after the write).
  Refuse the laxer declaration at construction (GOAL "Configuration is validated at construction"), or run the
  column's own validators in the write preflight? Since 530 the docs tell the consumer to declare each such field as
  strict as its column. The same shape exists for a `CharField` without `max_length` over a bounded column. Found
  fixing 530 (16 cells of its probe grid)
- [ ] 731. Decide whether a `method=` filter with no model field whose form field is built only per request is typed
  like its plain twin instead of refused (`filters/inputs.py::_refuse_method_without_form_field`): a `field` reading
  `self.parent.queryset` over a queryset annotation alias, a consumer `Filter` whose `field` reads `self.model`, a
  transform path (`opened_on__year`) and a JSON key path (`payload__k`) each build without `method=` (`String`, `Int`,
  `[JSON!]`) and are refused with it, though the alias and consumer shapes serve requests; a columnless
  `AllValuesMultipleFilter` breaks every request on its set with or without `method=`, as in django-filter. Typing
  them retires a documented `ConfigurationError` (spec-027 Decision 4). Found fixing 537
- [ ] 736. Decide whether a fixed-choice filter whose choices are not its column's (`DateRangeFilter` above all, a
  `ChoiceFilter(choices=...)` off the column's) is served through the typed input, typed by its own form (`String`, as
  graphene-django's `get_filtering_args_from_filterset` does) or by an enum of its own keys, instead of refused at
  build. spec-027 Decision 4 refuses it on a column without `choices` and, since 538, on a choice column whose values
  it shares none of, and says the filter's own `choices` never feed the enum; GOAL success criterion 7 and "Coming
  from DRF + django-filter" lean toward serving it, and no `DateRangeFilter` spelling is served through the typed
  input today (it is through `apply_sync`'s JSON `where`). Found fixing 538
- [ ] 742. Decide: in production a literal validation error carrying a scalar's parse exception is masked as "An
  unexpected error occurred.": graphql-core's `validate_input_literal` attaches the exception as `original_error`,
  which `extensions/error_policy.py::_is_unexpected` reads as unexpected, contrary to its docstring and spec-048
  Decision 8 (a parse, syntax or validation error is not masked). A `BigInt` literal `-1e50` / `1.5` / `NaN` and an
  `Int` literal of 4301+ digits reach it (1,120 cells of 673's production grid; DEBUG shows "Expected value of type
  ..."). But examples/fakeshop/test_query/README.md "The error policy masks validation errors too: `BigInt` literals"
  documents the masking as shipped and
  `test_scalars_api.py::test_filter_specimens_by_bigint_exact_rejects_non_integer_literal`'s docstring pins it.
  Unmask, and rewrite that README section and docstring; or keep the masking, and amend spec-048 Decision 8 and the
  `_is_unexpected` docstring? Found researching 673
- [ ] 760. A declared `ListFilter(field_name="occurred_on__year", lookup_expr="in")` handed a fractional member
  (`"2021.5"` through an `apply_sync` JSON `where`) truncates it and returns the 2021 rows, where the generated
  `year__in` leaf drops it and returns none, as 685's outcome says an integer `in` does:
  `filters/base.py::_integer_in_column` reads `_bound_model_field` (the `DateField`), so `ListFilter.filter`'s
  fractional-drop branch never runs for a declared transform path. Reading `_bound_value_field` there instead fails
  existing refusal rows in `test_scalar_predicate_binding_api.py` (past-int64 members, the `in-below-min` /
  `in-above-max` bounds), so the fix needs its own ruling. Found verifying 688
- [ ] 761. Decide the contract for a fractional member of an integer `ArrayField` element: flat `["1.5"]` binds
  `int(1)` (Django's `IntegerField.get_prep_value` truncates), nested `[["1.5"]]` and `[[1.5]]` bind `Decimal("1.5")`,
  which PostgreSQL's numeric-to-integer cast rounds to 2 (a JSON `1.5` already reached that cast nested before 692).
  Against 685's drop rule for a fractional integer `in` member. Unwired `apply_sync` / raw form only. Found fixing 692
- [ ] 843. Decide: should reading a `FilterSet`'s class-level `base_filters` publish the set, so a tool that reads the
  table without constructing it sees the published surface? drf-spectacular's `contrib/django_filters.py` does this
  when it generates OpenAPI parameters. Before the set's first construction, a set no `DjangoType` names answers that
  read with django-filter's class-creation table (no walked keys); after it, with the published table. The options:
  (a) a lazy class-level `base_filters` (a data descriptor on `FilterSetMetaclass` that routes django-filter's
  metaclass write and `_publish_filters` to a private slot, and a non-data descriptor for instance reads, so the
  instance shadow keeps working), which covers every reader but replaces django-filter's plain class attribute; (b)
  document that such a set publishes at its first construction and that a project calls `MySet.get_filters()` at
  startup (`AppConfig.ready`) to publish it earlier; (c) leave it as is. No rule settles a contract for readers
  outside the three drivers the README names. (Found fixing 836)
- [ ] 846. The package's `filters/base.py::RangeFilter` reads raw form bounds as `<name>_0` / `<name>_1` (Django's
  `MultiWidget`), where django-filter's `RangeFilter` reads `<name>_min` / `<name>_max`: a DRF client sending
  `?price_min=1&price_max=5` to a set that swapped `django_filters.RangeFilter` for the package's gets every row and
  no error (154 cells of the 316 grid). spec-027 Decision 4 documents `_0` / `_1` and django-filter ignores unknown
  keys the same way, so it fails the defect gate. Should the package's range widget also read `_min` / `_max`
  (GOAL success criterion 7), or should the migration docs say to keep `django_filters.RangeFilter` under DRF?
  Evidence: `.work/evidence/spike-i316-range/grid-after.jsonl` (`raw_pkg_minmax`). Found researching 316
- [ ] 855. Should a `RelatedFilter(queryset=...)` of a proxy or multi-table-inheritance relative of the target set's
  model be admitted? Since 818 the explicit queryset is read as an `IN` subquery of its keys, so a proxy's or an MTI
  child's `pk` names the same rows; `filters/sets.py::_admitted_rows` still refuses any model but the target set's
  own with a `ConfigurationError` (pinned by `test_filter_consumer_contracts_api.py::
  test_related_queryset_requires_the_exact_child_model_only_when_the_branch_is_active` [active-proxy]). Admitting
  them widens a pinned refusal. Found researching 818
- [ ] 872. Decide: a consumer `GlobalIDFilter` ending on the target's primary key past a declared `RelatedFilter` hop
  into a filter set a SECONDARY type wires (`bid = GlobalIDFilter(field_name="books__id")` with `books =
  RelatedFilter(BookChild)`, `BookChild` wired by the secondary `BookS`, primary `BookP`) validates against `BookS`,
  the hop set's binding: it accepts `BookS` ids and refuses `BookP`, while its relation key `books` and its undeclared
  twin validate against `BookP` (on an annotation-held id both answer `GLOBALID_UNVALIDATABLE`). spec-031 Decision 13
  sends "a flat copy of a declared hop's own id" to the hop set's secondary; GLOSSARY `FilterSet` says the key
  compares "as a leaf ending on the type's primary key (`books__id`) does". (a) The parent's leaf follows the
  relation's registered type, as the key does (one authority per declaration; narrows: a `BookS` id is refused); (b)
  keep: a leaf past a declared hop follows that hop set's binding, as its nested spelling does (the GLOSSARY sentence
  is restated). Pinned as (b) today by
  `examples/fakeshop/test_query/test_globalid_filter_strategies_api.py::test_a_leaf_past_a_hop_into_a_secondary_wired_set_decodes_against_that_secondary`
  and `tests/filters/test_finalizer.py::test_phase_2_5_admits_a_key_of_the_hop_target_set_decoding_against_that_set`
  [secondary-wired-key]; 860's routing marker applies under (a) by dropping its unwired-set condition. Found
  researching 860
- [ ] 874. Decide: on a relation whose target's primary key is itself a relation (an MTI child's parent link,
  `KioskFault.kiosk` to `SelfServeDesk` keyed by `lendingdesk_ptr`; a one-to-one pk, `Annotation.profile` to
  `PatronProfile` keyed by `patron`), which type does a `GlobalIDFilter` ending on that key past the hop validate
  against (`kiosk__pk`, `kiosk__lendingdesk_ptr`, `kiosk__lendingdesk_ptr_id`, `kiosk__id`; `profile__pk`,
  `profile__patron`)? Today the pk segment is walked as the relation it is
  (`filters/base.py::_resolve_globalid_target`, and for visibility `utils/permissions.py::leading_relation_hops`;
  GLOSSARY `FilterSet`: "a `pk` segment on a model keyed by a one-to-one or a parent link is that relation"): it names
  the type registered for the model the pk points at, or validates nothing when that model has none. So with only
  `SelfServeDesk` typed any type's id carrying the desk's pk matches, with `LendingDesk` typed too only a
  `LendingDesk` id matches and the desk's own id is refused, and `kiosk__id` (the inherited `Venue.id`) validates
  nothing in every world, while the key `kiosk` validates `SelfServeDesk` (833 / 849 / 860: a relation key compares
  "as a leaf ending on the type's primary key (`books__id`) does"). The same shape holds on every hop shape and driver
  and for the one-to-one pk; a plain pk is at parity. (a) A trailing segment naming the reached model's own key past a
  hop (`pk`, the pk by name or attname, the scalar end of its parent-link chain) names the reached type, as the key
  does: a researched prototype does this in the walk and in routing, which also stops such a trailing pk reading the
  pointed-at type's `get_queryset` rows (observable only when the target type does not cascade, item 754: a
  `NumberFilter("kiosk__pk")` then answers as `kiosk__id` does) and moves `kiosk__lendingdesk_ptr__pk` from `Venue` to
  `LendingDesk`; `profile__patron` would then stop being a relation key into `Patron`. (b) Keep the relation reading
  and restate the parity sentences for relation-valued keys (and decide `kiosk__id`). Related, either way: the owner's
  own key on its own set (a `GlobalIDFilter(field_name="pk")` on a set bound to a Relay `SelfServeDesk` type, or the
  generated `lendingdesk_ptr` key) validates the parent's type and refuses the child type's own emitted id; it matches
  the generated relation key (`filters/sets.py::FilterSet._is_own_pk_under_relay_owner`) and
  `tests/filters/test_base.py::test_resolve_globalid_target_walks_a_relation_primary_key`. Grids: 30200 MTI cells
  (5076 move under (a), all consumer flat leaves), 9058 one-to-one and plain cells (1152 move, 0 plain). Found
  verifying 860
- [ ] 884. Decide: under a schema that publishes only a secondary over a model (its primary unpublished), a
  model-label id (`products.category:<pk>`, which a model-strategy secondary itself emits) is refused by `node` /
  `nodes` as `GLOBALID_INVALID` (757; before, the engine's abstract-type error). Should a model-label id instead route
  to the one Relay type the executing schema publishes over its model, so a secondary-only schema can refetch the ids it
  emits? That changes the model-label decode contract (README secondary blockquote, spec-031) for mutations and filters
  too, and is ambiguous with several published secondaries. Found fixing 757

## Hunt not finished in t3

- [ ] 29. The hunt's final test gate was never run (the Postgres and sharded runs included)
- [ ] 242. Decide removing the dry-0015 worktree, `~/t3code-1cc21548-pre-ff.tgz` and, after item 114 lands,
  `refs/scratch/admission-wip`

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelogtodo]: ../../CHANGELOGTODO.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
