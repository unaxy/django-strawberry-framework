# Typing 0.0.15: to-do list

basedpyright runs in `all` mode on every Python file, in two passes (3.11 and the 3.10 floor). This file tracks the
rules still switched off and the `# pyright: ignore[...]` comments still in the tree.
Each item is fixed at the root, gated (both passes 0 errors, full suite in one pass at 100% coverage), then committed.
A split suite run on a tree other sessions are editing can drop modules from every part, so it is not a coverage gate.
Locked rules and the budget: `scripts/check_type_suppressions.py` (pre-commit and the CI lint job) refuses a
`# pyright: ignore[...]` naming any rule `pyproject.toml` marks `# Locked` (the 63 rules on everywhere with no
suppression left), every file-level `# pyright:` directive, and any per-site count off the generated ledger
`scripts/type_suppressions.toml`: each site (`path::QualifiedName`) holds its `typing.cast` calls and its ignore
comments per unlocked rule (130 casts in all), every count may only fall, and a suppression cannot move to new code by
giving one up elsewhere. A rule whose last ignore is cleared leaves the ledger and gains the marker. In CI, a commit that raises a
total (casts, or one rule's ignores) fails unless it carries a `Suppression-Growth-Approved:` trailer, the
maintainer's consent.

Progress: 29 done, 6 closed (survey verdicts), 2 open (one waits on upstream, one is a behavior change outside
typing). Ignore comments: 715 lines (1897 at the start of 0.0.15's ignore
sweep); `typing.cast` calls: 130 (432 at the start of the cast work).

## Pre-commit (`uvx pre-commit run --all-files`, 4ce779e1, clean clone)

| Hook | Result | Time | Scope |
| --- | --- | --- | --- |
| kanban tracked path constants | pass | 0.1s | whole tracked set |
| source layout | pass | 3.4s | 633 files checked, 81 excluded, 0 violations |
| ruff check | pass | 0.4s | 511 files |
| ruff format | pass | 0.1s | 511 files |
| basedpyright | pass | 16.4s | 511 files, 0 errors |
| basedpyright floor (3.10) | pass | 14.6s | 511 files, 0 errors |
| public API type completeness | pass | 4.8s | 100%, 2 allowlisted warnings |
| kanban anchors | pass | 1.1s | 77 cards, 149 glossary anchors |
| citations | pass | 3.4s | 3400 citations |
| **Total** | **9/9 pass** | **45s wall** | |

## Done

- [x] 1. `reportExplicitAny` on for the package, the example project and scripts
- [x] 2. tests/ passes `all` mode in both passes; scope is every Python file
- [x] 3. Package annotations state their run-time contract
- [x] 4. Resolvers declare `graphql_type=` and return honest model rows (94 ignores)
- [x] 5. `definition_raises`, `module_binding`, direct module patching, `blocked_modules` (239 ignores)
- [x] 6. Walker hands `get_queryset` a real `strawberry.Info` on the prefetch path; bare `Info` in place of
  `Info[Any, Any]` (4 ignores)
- [x] 18. `FilterSet.__init__` overrides spell out their parameters instead of `*args, **kwargs` (10 ignores)
- [x] 25. `_CrLampKiosk` renamed `CrLampKiosk`, clearing its `reportUnusedClass` (1 ignore)
- [x] 22. The queryset-state check accepts only a tuple `_fields`, as Django stores it
- [x] 14. `utils/_queryset_private.py` reads and writes Django's private QuerySet attributes; 156 ignore lines to 35
- [x] 15. Real `User` / `AnonymousUser` objects instead of stand-in users (39 ignores)
- [x] 16. `tests/_idioms.py::relay_hooks` / `async_relay_hooks` read the Relay methods the finalizer installs (26
  ignores; one kept, below)
- [x] 17. `tests/_info.py` builds real Strawberry `Info` objects (`make_info`, `response_path`) and `unread_info()`,
  a real `Info` that fails on any read (35 ignores: the 22 `Info` stand-ins and 13 other stand-ins)
- [x] 26. `schema_config_from_info`'s docstring names the real Strawberry `Info` as the fallback's caller; the
  `info.schema.config` fallback stays (a real `Info`'s `schema` is the Strawberry `Schema`)
- [x] 27. spec-020 and spec-023 show resolvers in the item-4 spelling (`graphql_type=`, model-row return)
- [x] 19. The field factories declare the value they resolve to: `DjangoListField(T)` is `list[T]`,
  `DjangoConnectionField(T)` is `DjangoConnection[T]`, `DjangoNodeField(T)` is `T | None`, `DjangoNodesField(T)` is
  `list[T | None]`, and `current_user()` is `object` (5 ignores)
- [x] 20. `tests/_execution.py::make_execution_context` and `tests/_definition.py::make_definition` build real
  `ExecutionContext` / `DjangoTypeDefinition` objects; hostile stand-ins keep their ignores (43 ignores, 15 of them
  other stand-ins)
- [x] 21. The other stand-ins and the uncategorized rest: real objects and models in place of stand-ins, real
  functions marked with `vars(fn).update(...)`, Django wrapper plants through `monkeypatch`, and `make_info` builds
  `operation` / `document` / `operation_name`; `Meta.description` takes a `str` or a lazy translation string; every
  kept ignore's reason line states its real cause (272 ignores)
- [x] 11. `reportUnknownMemberType` on everywhere: every Django model field annotated with the generic the django-stubs
  plugin would solve, gated against the field call by `tests/test_model_field_annotations.py`; typed DRF reads in
  `rest_framework/accessors.py`
- [x] 12. `reportUnknownVariableType` on everywhere: containers declared with their element type where they are born,
  and the narrowing predicates in `utils/_narrowing.py` in place of `isinstance` on `object` values; write-pipeline
  steps fail through a tagged `StepFailure` instead of a bare list
- [x] 13. `reportUnknownArgumentType` on everywhere: typed unbound slots (`dict_items`, `mapping_get`), per-view
  `as_view` returns, and checker-only shape classes for the bases the consumer factory reads at run time; 76
  suppression lines carry one of the three rules, each naming the third-party defect
- [x] 31. Ignore sweep (1158 to 927 lines): the DRF `ModelSerializer.Meta` stub gap is held by one ignore on
  `tests/_idioms.py::ModelSerializerBase`, which the DRF tests subclass (124 ignores); the registry-isolation wrappers
  are a module `usefixtures` mark; `db` / `transactional_db` taken for their side effect are `django_db` marks;
  hostile test doubles conform to the Protocol or subclass the real type (`-> NoReturn` properties, raising
  `__getattribute__`); `tests/_django_private.py` narrows Django's private attributes with `TypeIs`; probe resolvers
  `del` the argument Strawberry reads; unused package parameters are `del`eted; `_request_body.py` types its stream as a Protocol;
  the runtime `T | None` widening keeps its reason-tagged `reportInvalidCast` at each site
- [x] 10. `reportUnusedParameter` on everywhere: a parameter the caller passes by position is renamed `_name`, a
  fixture requested for its side effect moves to `@pytest.mark.usefixtures`, an optional Strawberry `root` / `info`
  or unread private parameter is removed, and `NestedConnectionStrategy.plan` takes its arguments positional-only;
  a parameter a caller binds by name is `del`eted in the body with its reason (`del info, required  # ...`), which
  leaves no suppression
- [x] 9. `reportUnusedCallResult` on everywhere but the tests: the example project outside its test folders (122
  sites) joins scripts/, the package and the root files. A result taken only for the call's side effect is bound to
  `_`; a `setdefault` chain on factory `**fields` is one dict merge; a `QueryDict` key is `del`eted, not popped
- [x] 34. `reportUnreachable` locked: a trust-boundary check on an annotated argument moves into a validator that
  takes `object` (`_require_django_application`, `_registered_field_class`, `_required_acknowledgement`,
  `_require_callable_wrapper`), as `_validated_websocket_url_pattern` already did; an async generator that fails
  before its first yield loops over `()` first. Same pass: a test double that skips its constructor is built with
  `cls.__new__(cls)` instead of an `__init__` that never calls `super` (5 of 7 `reportMissingSuperCall`); the two
  raising-`__dict__` querysets share `tests/_idioms.py::UnreadableStateQuerySet`; the `strawberry.lazy` target is
  imported under `TYPE_CHECKING`, Strawberry's documented spelling; the validation-cache wrapper is narrowed with
  `isinstance(..., _lru_cache_wrapper)` (7 ignore lines)
- [x] 7. `reportAny` on everywhere: scripts/ and the root files (their execution environments in `pyproject.toml`): every
  script parses into a typed `argparse.Namespace` subclass, JSON goes through a `Callable[[str], object]` alias and
  is narrowed, and `scripts/_kanban_lib.py::fetch_graphql_data` returns `dict[str, object]`; the kanban and glossary
  payloads enter their `TypedDict`s through a `cast` per decoded list (three in `fetch_dashboard_data`, one in
  `fetch_glossary_data`), each tagged with the query that fixes the row shape. On for the package too (648 sites
  to 10 suppressions): an upstream ``Any`` read goes through a typed slot in `utils/_narrowing.py` (`read_attr` for
  `getattr`, `pk_of`, `enum_value`, `dict_of` / `list_of`, `instance_dict`, `class_dict` / `type_mro` /
  `type_attr`, `call_method`, `is_awaitable`) and is narrowed, or through `require_instance` / `require` when its
  source guarantees the class; `strawberry.UNSET` is `utils/input_values.py::UNSET` typed `UnsetType`; settings
  reads go through `conf.py::django_setting`; a verbatim forward to an upstream method is `*args: object,
  **kwargs: object` and `utils/typing.py::call_forwarded`, and a call the package composes spells its arguments
  (`DjangoSchema.execute_sync` / `execute` spell Strawberry's parameters, unchanged from the floor to the latest
  release), with a counted `cast` where a runtime mapping meets a constructor no stub can check; a stub's
  `-> Any` call is `utils/typing.py::object_result`; graphql-core's field maps are `graphql_fields` /
  `graphql_input_fields`. Four suppressions are the permission hooks' `data` / `instance` parameters
  (`DjangoModelPermission.has_permission`, `DjangoMutation.check_permission`), kept `Any` so a consumer override
  can narrow them, plus the default `check_permission`'s forward of them. The other 5 each sit on an existing
  `reportExplicitAny` line: the module `__getattr__` (the dormant `apps/products/fields.py` subclasses a planned
  `AdvancedFieldSet` through it), `DjangoType.get_queryset`'s `info` (item 24), the async view's `run` (Strawberry
  overloads `run(HttpRequest)` to two response types) and the runner's `operation` / `on_stream_result` (they wrap
  upstream's scopes rather than subclass them). On for the example project outside its test folders too (650 sites,
  380 of them in migrations, to 13 suppressions): a data migration binds each `apps.get_model(...)` (`type[Any]`) to
  a declared `type[...]`, `models.Model` when only the manager is used and otherwise a `TYPE_CHECKING`-only shape
  class naming the historical columns that migration reads (ruff `DJ008` off for migrations); an `aggregate()` or
  `values_list()` result is bound to a declared `dict[str, int | None]` / `QuerySet[M, <row>]`; a `cleaned_data` read
  is `.get(...)` narrowed by `isinstance` (`apps/kanban/schema.py::_cleaned`); the request user is the documented
  `getattr` chain on an `Info[object, object]`, narrowed by `isinstance(user, AbstractUser)`; JSON goes through a
  `Callable[..., object]` alias; `pk` is declared `int | None` on every concrete example model (`Edition.pk: str`, its
  ISBN); the ModelForm / ModelSerializer forwards take `*args: object,
  **kwargs: object` with a `reportArgumentType` ignore on the forward (11 `reportExplicitAny` ignores gone); a resolver
  field is the call form `name: <return type> = strawberry.field(resolver=_name, graphql_type=...)`, whose
  `resolver=` overload is typed where the decorator factory returns `Any`, listed after a class's annotated fields
  (where Strawberry puts an unannotated decorator field). The 13: `BranchType.shelves`'s
  `@staticmethod`-stacked `@strawberry.field(graphql_type=...)` decorator on a `DjangoType` and 6 resolver-less
  `strawberry.field(...)` attributes
  (Strawberry's no-resolver overload returns `Any`), the dormant `apps/products/fields.py`'s 4 `AdvancedFieldSet`
  bases, `seed_shards`' read
  of `settings.DATABASES` (django-stubs types every setting `Any`) and typeshed's `inspect.Parameter.default`. On
  for tests/ too (2852 sites to 14 suppressions): a saved row's `pk` is `tests/_idioms.py::saved_pk` (`pk_of`
  narrowed to `int`, failing on an unsaved row); JSON and `result.data` walks go through `json_loads` / `json_at` /
  `json_object` / `json_list` there (or a file's private copy); `typing.get_args` is `type_args`; a hostile double's
  `super().__getattribute__` returns through `object_result`; an `Info` whose `context` is read is `Info[object,
  object]`. The 14: the `name=` decorator on a `DjangoType` column
  (`tests/types/test_definition_order.py`) and 3 resolver-less `strawberry.field(...)` attributes, `strawberry.UNSET` as an input default or omitted argument under its
  declared annotation (7 `@strawberry.input` defaults and two module `_OMITTED` bindings), and the
  `TestClient` probe through the package root's PEP 562 `__getattr__`. On for the example
  project's test folders too (3579 sites to 2 suppressions, decorators the call form cannot replace: a
  `@staticmethod`-stacked one on a `DjangoType`, and `test_library_shapes_api.py`'s `parents`, whose class lists an
  unannotated `DjangoConnectionField` over a run-time type first):
  `graphql_client.py`'s `JSONObject` is `dict[str, object]`, and a response is read through its `response_json` /
  `json_at` / `json_object` / `json_list` / `json_str` / `json_int` / `json_bool`, each asserting the container or
  value kind; `saved_pk` narrows a saved row's `pk`; settings and other `Any` attributes go through its `read_attr`
  (`getattr` typed `-> object`) and an `isinstance` check, `MIDDLEWARE` through `middleware()` /
  `middleware_without_debug_toolbar()`; `User` rows are re-fetched by `username` (auth's `User.pk` is `Any`)
- [x] 32. `testing/client.py`'s `Response` is generic in its raw `response` field (no default): `TestClient.query()`
  and the mixin return `Response[_MonkeyPatchedWSGIResponse]`, `AsyncTestClient.query()`
  `Response[_MonkeyPatchedASGIResponse]` (spec-043 Decision 6)
- [x] 36. Cast sweep, phase 1: 160 package casts retired (399 to 239) with no new branch and no behavior change. Shared
  typed helpers in `utils/_narrowing.py` (`is_concrete_field`, `is_queryset` claiming `QuerySet[Model, object]`,
  `optional_annotation` in place of the `OptionalWidenable` cast target, `get_item` / `set_item` / `del_item`,
  `iter_of`, `is_real_mapping` / `is_real_collection`); value-or-defect producers typed
  `tuple[X, None] | tuple[None, Defect]` and narrowed by index; an existing raising helper (`require`,
  `require_instance`) where the value's source proves the class; a raising validator returns what it proved. Kept:
  a cast on a line a KANBAN row quotes, and two casts on security paths (`consumers.py::_ConnectionRevocation.close`,
  `schema.py::_consumer_extension_entries`) where the replacement would be a dead `is not None` that fails silently
- [x] 37. Cast sweep, phase 2: the fixes phase 1 left because each writes a new raise or branch (with its test),
  changes a public annotation, changes behavior for an input accepted today, or sits on a per-row path that needs a
  benchmark. First pass done (package casts 191 to 153): generic `RelatedSetTargetMixin` and `convert_with_mro`
  (`MroContinue` is the sentinel's public name), `decode_visible_relation_ids` typed as a value-or-defect pair,
  `DecodeResult` as `DecodeOk | DecodeRefusal`, a generic `is_supplied` TypeGuard (a TypeIs would narrow the False
  branch of an `object` argument to `Never`), `is_concrete_field` folds, and single raises through `require` /
  `require_instance` with their tests. Second pass (package casts 152 to 130): `types/finalizer.py`'s registry reads
  (`_definition_or_raise`, `declaration_map` over the related-declaration maps, `require` / `require_instance` where
  the source guarantees the class), the bind-slot readers (`mutations/resolvers.py::_bound_model_fields`,
  `types/base.py::_is_django_type_class`, `rest_framework/inputs.py::_is_serializer_class`, the hook-built form and
  serializer constructor calls through `call_forwarded`), `_resolve_model` / `resolve_meta_model` answering the
  unchecked `object` that `write_mixins.py::resolve_backed_model_or_raise` gates through `require_model_class`, and
  `rest_framework/inputs.py::serializer_model` refusing a non-class nested `Meta.model` as a `ConfigurationError`.
  Third pass (package casts 130 to 116): `utils/permissions.py::RelationHop` split into `DeclaredHop` (owner a set
  class, declaration as collected) and `UndeclaredHop` (model always set, `scope` its own), the walker overloaded so the
  declared reading returns `DeclaredHop`s (`relation_path_gates` reads each owner uncast), `isinstance` in place of the
  `declared` property, and `filters/sets.py::_filter_declaration` / `_hop_target_set` reading a declared hop's
  `FilterSet`, `RelatedFilter` and target set through `require` / `require_instance` (an active leaf crossing a `None`
  hand-assigned into `related_filters`, which no collector stores, now raises `TypeError` there; with no other hop
  in the walk it ran raw, and with declared hops before it it already raised `AttributeError`); the
  `_LeafChain` reads go through `require_instance`. Fourth pass (package casts 116 to 107): the
  `mutations/resolvers.py` write pipeline, whose statement order is a security invariant, left unmoved: the skeleton
  holds a `_WriteTarget` (primary type, payload slot, model; `None` for the model-less plain form) and, once an
  update / delete locates, a `_Located` (model, row), so its six reads of `primary_type` / `model` need no cast; a
  model-backed write step's product and the delete rider's located row pass `require_instance(..., Model)` after the
  permission gate (no shipped flavor answers anything else: the model and register steps return the decoded row, and
  the `ModelForm` step and the serializer's `_checked_saved_result` already require a model instance; a product
  without `pk` died with `AttributeError` at the same stage); `_model_write_step` takes either decode tuple and raises `ValueError` on any length but three, as the strict unpack it replaces did, and
  `auth/mutations.py::_register_decode_step` raises `ValueError` on any length but four. Its user read keeps one
  `cast("_User", ...)`: Django admits an `AUTH_USER_MODEL` that is not an `AbstractBaseUser` subclass and the
  register bind refuses none, so a runtime check would refuse a project that works today. Fifth pass (package casts
  107 to 98), the security-path singles, every check order kept: `utils/permissions.py::set_bound_definition` reads
  the owner slot through `optional_instance(..., DjangoTypeDefinition)`;
  `utils/permissions.py::run_active_input_permission_checks` requires a related target other than `None` to be a set
  class carrying `ActiveInputPermissionMixin` (real MRO) and raises `TypeError` before the child dispatch and the
  parent's branch gate, where a target without `_run_permission_checks` was skipped and the branch gate still fired;
  `consumers.py::_ConnectionRevocation.close` requires the attempt task in `CLOSING`,
  `consumers.py::_actor_is_current` reuses a revalidation only for an exact `float` stamp (anything else falls through
  to the session read), and `consumers.py::_refreshed_actor` requires a `str` or `None` `session_key` (a failure the
  checkpoint already answers fail-closed); `resource_policy.py::begin_resource_budget`'s scope carries the armed
  snapshot `on_operation` scans with, `_DocumentWalk.operation` keeps its `read` set in a typed local,
  `_DocumentWalk.walk` requires a `FieldNode` once both fragment kinds are handled, and
  `_ValueBudget._charge_container` looks up only a `str` key in an input object's field map (a non-name key is charged
  and classifies no spec, where an unhashable one raised `TypeError`). `auth/sessions.py::require_session` keeps its
  cast: Django never checks that a custom `SESSION_ENGINE` store is a `SessionBase`, so a runtime check would refuse a
  duck-typed store that works today, the reasoning that keeps the `_User` cast. Sixth pass (package casts 98 to
  85), the per-row reads, each benchmarked: `utils/querysets.py::_reconstructed_value` keeps its `value_type`
  identity cascade and asks the exact predicate only inside a taken branch (`is_exact_tuple_or_frozenset` is new),
  and allocates a rebuilt node from `type(value)`, since the cascade leaves the cached class typed as a possible
  container (seal time unchanged within noise); `optimizer/_context.py` reads the stashes through
  `planned_resolver_keys`, `fk_id_elision_keys` and `stashed_strictness` (a stash of any other shape than a
  `set` / `frozenset` or a `str` raises `TypeError` rather than reading as absent or `"off"`, so a wrong-shape stash
  never disarms the N+1 guard); `utils/lazy.py::unwrap_lazy_object` is overloaded checker-only, `LazyObject[_T]` to `_T` and `_T` to
  itself, so `relay.py::_stamp_node_type` reads the unwrapped row uncast; the
  async many-side reads (`types/resolvers.py::_visible_many_rows` and the many resolver) take the bound through
  `require(..., is_queryset)`, since `bounded_rows_async` honestly answers a `list` for an evaluated queryset and
  only the caller knows its source is unevaluated. Not taken: `optimizer/selections.py`'s `is_fragment` (its
  `hasattr` check matches no class claim), `bind_auth_mutations`'s ledger (holders and the register rider share one
  metaclass), the walker's hook-type reads (threading the type through four callers on the visibility path),
  `ends_in_unique_column` / `TypeRegistry.unregister` (the check solves to `Unknown` type arguments),
  `testing/client.py::_finish_response` (a TypedDict member has no runtime check), `strawberry_schema_from_info` /
  `schema_config_from_info` (tests pass namespace stand-ins), `payload_cls_for` (the keyword constructor has no
  runtime check). Upstream-only (re-verified against the lock): types-django-filter (`FilterSetMetaclass.__new__`
  returning `Self`, `get_fields`, `FilterSetOptions.fields`, `Filter.filter`), django-stubs (`Options.concrete_model`
  optional, `QuerySet(hints=)`, `Window(order_by=)`), Strawberry (`SliceMetadata.from_arguments` reading `info` only
  without `max_results`, `Edge.node`, `Info._raw_info`)

## Rules off

Off by design (not planned): `reportImplicitStringConcatenation`, `reportPrivateUsage`, `reportUnusedFunction`,
`reportImportCycles`, `reportUninitializedInstanceVariable`. The reasons are in `pyproject.toml`.

Off for tests and the example project by design: `reportUnannotatedClassAttribute` (tests/, the example project and
its test folders: 9033 sites, 6948 of them in a nested `class Meta`; on for scripts/, the package and the root files):
the flagged attributes are declarative configuration a framework reads by name at run time (`Meta`, admin options,
declared filters, migrations, `AppConfig`) on classes nothing subclasses, so no inferred type reaches an override, and
every satisfier at that scale (`@final` on each `class Meta`, `Final` or `ClassVar[...]` on each attribute) changes the
bare `class Meta:` the READMEs teach. `reportUnusedCallResult` (tests/ and the example project's test folders, about
4300 sites): a test calls for side effects (fixture rows, `delete()`, a call inside `pytest.raises`).

Off at the 3.10 floor only: the five `reportUnknown*` rules and `reportUnnecessaryTypeIgnoreComment`. django-stubs needs
`typing.Self` (3.11), so at 3.10 every `-> Self` reads as unknown.

## Ignore refactors: survey verdicts

Survey verdicts recorded so nothing is re-tried blind:

- Item 14, rejected: a `stubPath` overlay of django-stubs (splits class identity, 1044 errors), a django-stubs PR for
  the private attributes (too slow), and asserting through public behavior instead (weakens the tests' claims)
- Item 16 keeps one ignore of its own: the plain-function `resolve_typename` planted before finalize in
  `tests/types/test_relay_interfaces.py` (an attribute set, not a read)
- Keep, reason lines accurate: `check_permission`'s `Any`; the `schema.py` / `consumers.py` verbatim forwards; the
  ModelForm / ModelSerializer forwards in examples; Django model `Meta` on proxy / MTI children; `connection.py`'s two
  ignores the Strawberry survey looked at
- Rejected: making `DjangoType` generic over its model (rows and GraphQL types stay unrelated classes)
- Item 31, not taken: dropping the test `__hash__ = None` lines (CPython already sets it beside `__eq__`, but ruff
  `PLW1641` then fires, so their `reportAssignmentType` ignores stay); `unchecked()` / `plant()` escape helpers (a cast
  by another name); collapsing keyword-called hook parameters into `**_kwargs` (the signature stops documenting the
  hook); widening `DjangoType.get_queryset` for async overrides (item 28)
- Item 21, not taken: aliasing asgiref's coroutine marker; `is_marked_coroutine_function` keeps its two suppressions
  with their real reasons (typeshed deprecates `asyncio.iscoroutinefunction` from 3.11; asgiref picks its check by
  `hasattr`)

- Kept after the ignore-refactor survey's fixes landed: `middleware/request_body.py`'s `setup` read (routing it
  through `require` replaces Django's "not callable" error a test pins); `list_field.py`'s model check and
  `utils/querysets.py`'s manager `all()` check (an `object` read narrows to `type[Unknown]` / `QuerySet[Model, object]`,
  a new diagnostic or cast); the two `query.annotations` plants in `tests/utils/test_querysets.py` (`.annotate()`
  refuses the hostile inner query, so the plant is the input)

- Item 34, kept budgeted (each at its floor): `reportMissingSuperCall` 3 (the `TYPE_CHECKING` router and consumer
  declarations, and a test form whose `__init__` forwards through `call_forwarded`; a forwarding `super().__init__` body trades it for four ruff `ARG002` or six `reportArgumentType`);
  `reportPropertyTypeMismatch` 5 (setters that take a lazy target or the stop-aware schema wrapper and getters
  that return the resolved value, the django-filter idiom); `reportFunctionMemberAccess` 4 (the `__test__` pytest
  guard spec-043 Decision 7 fixes, and the django-filter `Filter.method` stub); `reportGeneralTypeIssues` 5
  (resolver-only Strawberry fields typed from run-time annotations, a class annotation would win over them; the
  hostile `__dict__`, the refused sync iteration, the string `_meta.model`); `reportInvalidTypeArguments` 5 (`FilterInput[...]` / `OrderInput[...]`
  refusing a non-set, and `DjangoConnection`'s unbounded `NodeType`); `reportUndefinedVariable` 5 (unresolvable
  annotation strings that are the input under test)

- Item 8, closed (off by design, above): rejected `@final` on every flagged class (a scripted pass leaves a few hundred
  hand sites and a decorator on the consumer `class Meta:`), `Final` / `ClassVar[...]` on each `Meta` attribute (a bare
  `ClassVar` does not satisfy the rule), and a basedpyright baseline (a frozen diagnostic list, not a fix)
- Item 24, closed: the visibility helpers read only `info.context` (`utils/permissions.py::request_from_info` takes any
  object whose context carries a request and raises `ConfigurationError` otherwise), so `object` is the run-time
  contract; `DjangoType.get_queryset`'s `info` is `Any`, so a consumer's forward gains no check; typing 6 of the
  helpers adds 189 `reportArgumentType` sites
- Item 28, closed: a `QuerySet | Awaitable[QuerySet]` return makes every direct sync call (`docs/README.md`, fakeshop)
  narrow, to retire 7 `reportIncompatibleMethodOverride` ignores on async overrides
- Item 29, closed: the `Upload` input delivers non-file values (null, str) that the form's own validation rejects as
  invalid files; `MultiValueDict[str, UploadedFile]` needs a guard that changes that error, to retire 1 test ignore;
  Django's `FileInput` reads a plain mapping, so `dict[str, object]` is the run-time contract
- Item 30, closed: one issue worth filing (the maintainer posts it), django-stubs declaring `QuerySet`'s private
  `_db`, `_hints`, `_fields`, `_prefetch_related_lookups`, `_clone`, `_chain` (6 lines in
  `utils/_queryset_private.py`; the stub already declares `_result_cache` and `_iterable_class`). Not filed, reason
  lines kept: the M2M `_To` default (7 migration lines; django-stubs #1802 is open), `re_path` with an ASGI
  application (Channels usage), drf-stubs' bare generics, Strawberry's bare generics, django-debug-toolbar, pytest,
  asgiref. Waits on the graphql-core cap: Strawberry's `_graphql_core.py` alias rebinding (11 lines; 0.336.0 drops the
  `ImportError` fallback but requires graphql-core >= 3.3 and Python >= 3.11) and graphql-core 3.2's bare
  `GraphQLWrappingType` / `GraphQLList` (3 lines): re-check both when the cap admits 3.3 and the lock resolves
  Strawberry 0.336.0 or later. `Prefetch` is generic in django-stubs 6.1.1 and no ignore names it
- Item 33, closed (off by design, above): 24 package sites; `ClassVar` is the wrong spelling for the metaclass-filled
  attributes (each is an attribute of the built class, so writes through it become errors), and the `bound_*` slots
  absent until the bind, the `__weakref__` slots and the `consumers.py` shape classes keep about 14 ignores for nothing
  the checker proves
- `Any` survey (the `reportAny` / `reportExplicitAny` lines outside tests/), taken: the package owns `auto` as
  `Annotated[object, StrawberryAuto()]` (7 ignores). Not taken: the resolver call form for a resolver-less
  `@strawberry.field(graphql_type=...)` (type-checks, 3 lines, but the examples would stop mirroring the decorator
  form `docs/README.md` teaches). Kept, measured: `utils/typing.py`'s `ConcreteField` / `ForeignKeyField` (django-stubs'
  `_ST` is contravariant: `Never` 6 errors, `object` 31), the DRF, `FieldMap` and `ModelForm` aliases (invariant stub
  TypeVars: 348, 2 and 81 errors), `scripts/_kanban_lib.py::_JSONRow` (5), `DjangoType.get_queryset`'s queryset
  (108), `_ConnectionT` (37), `is_marked_coroutine_function` (3), `AsyncDjangoGraphQLView.run` and
  `operation_state.py`'s two returns (no single honest type), a resolver-less `strawberry.field(...)` (declared
  `-> Any` upstream). The package root's `__getattr__ -> Any` waits on spec-059:
  `examples/fakeshop/apps/products/fields.py` derives from the planned `AdvancedFieldSet`, which reaches it only through that `Any`, and an `object` return trips
  the locked `reportUntypedBaseClass`
- Trust-boundary guards that read the guarded value through `utils/_narrowing.py` (`read_attr`, `list_of`) instead of
  an annotated read plus a `reportUnnecessaryIsInstance` ignore: kept (no parameter widened; the value is typed
  `object`, the guard stays live, and `read_attr` is `getattr`, `list_of` is `list` at run time)

## Open

- [ ] 23. Waits on upstream: drf-stubs declares a stub-only `ModelSerializer.Meta`
  (typeddjango/djangorestframework-stubs#689, open; the fix, #1069, closed unmerged; a comment asking whether a fresh
  PR would be accepted is the maintainer's to post). Once a release drops it: bump the lock, retire
  `tests/_idioms.py::ModelSerializerBase`, `examples/fakeshop/apps/library/serializers.py::ModelSerializerBase` (which
  every library serializer derives from) and the two `products/serializers.py` `Meta` ignores, and lower
  `reportIncompatibleVariableOverride` by 4
- [ ] 35. Behavior, not typing (item 6's open question): on the prefetch path a `get_queryset` hook reads the planning
  resolver's `info.field_name` / `selected_fields`; run by the relation's own resolver it reads the relation's. The
  optimizer should not change what a hook observes: build a per-relation raw info, as strawberry_django's
  `optimizer.py::_generate_selection_resolve_info` does (index key only on a list-valued relation), thread it through
  `optimizer/walker.py::_hook_info`, `_build_child_queryset` and `optimizer/nested_planner.py`, pin both paths at depth
  1 and 2 in `examples/fakeshop/test_query/`, and rewrite the `docs/README.md` sentence and its glossary entry. Needs
  its own KANBAN card

### Upstream drafts (the maintainer posts)

drf-stubs, a comment on PR #1069 (item 23):

```text
#1069 looks like the right fix for #689, and it was closed ten minutes after it opened with the downside question
unanswered. Under pyright/basedpyright every `class Meta:` on a `ModelSerializer` subclass reports
`reportIncompatibleVariableOverride` against the stub-only nested `Meta`; every project carries a suppression for it.

If the author does not return, would a fresh PR with the same change be accepted (drop the stub-only
`ModelSerializer.Meta` and its stubtest allowlist entry; assert a subclass's own `Meta` attributes keep their
declared types)? If reading `.Meta` off a bare `type[ModelSerializer]` should keep type-checking, the alternative is
declaring it on the class as `Meta: ClassVar[type[Any]]`, which pyright accepts any nested `class Meta:` against.
```

django-stubs, a new issue (item 30), titled "Declare QuerySet's private state attributes (_db, _hints, _fields,
_prefetch_related_lookups, _clone, _chain)":

```text
`QuerySet` in the stubs declares `_result_cache` and `_iterable_class`, but not the other private state that
libraries extending the ORM read and copy: `_db`, `_hints`, `_fields`, `_prefetch_related_lookups`, `_clone()` and
`_chain()`. Under pyright's strict modes every read is `reportAttributeAccessIssue` plus the three
`reportUnknown*` rules.

Proposed declarations, from Django's own `QuerySet.__init__` / `values()` / `_clone()`:

    _db: str | None
    _hints: dict[str, Any]
    _fields: tuple[str, ...] | None
    _prefetch_related_lookups: tuple[str | Prefetch, ...]
    def _clone(self) -> Self: ...
    def _chain(self) -> Self: ...

Checked against django-stubs 6.1.2 and master. Happy to send a PR if this is welcome.
```

## Ignore breakdown

Lines carrying a `# pyright: ignore[...]` comment: 715 (785 rule hits): tests 531, package 124, examples 57,
scripts 3. By rule and by file are measured at 715 lines; by cause at 881.

### By cause

Classified by each line's reason comment; rows other than the DRF one were measured before item 31. "Unknown too"
counts the lines whose bracket also names one of the three Unknown rules because the expression already suppressed for
another rule evaluates to Unknown.

| Cause | Lines | Unknown too | Plan |
| --- | --- | --- | --- |
| Deliberately ill-typed test input (hostile values, forged classes, stand-ins, rejected writes) | 426 | 4 | keep |
| DRF stubs declare `ModelSerializer.Meta` (the test base plus the example serializers) | 26 | 0 | item 23 |
| Django private QuerySet attributes (seam, `super()._clone()`, hostile writes, planted shapes) | 17 | 8 | keep |
| Verbatim forwards (schema, consumers, ModelForm, ModelSerializer, field and `strawberry.type` forwards) | 42 | 0 | keep |
| Django model `Meta` on proxy / MTI children | 10 | 0 | keep |
| Third-party annotations only the Unknown rules report: Strawberry 16 (11 the `_graphql_core.py` alias rebinding, 5 bare generics), django-stubs 9 (7 migration M2M `_To`, `Prefetch`, a `re_path` route list), drf-stubs 8, graphql-core 3.2 bare generics 3, django-debug-toolbar 3, pytest 3, asgiref 1 | 43 | 43 | item 30 verdict |
| Parameters a caller binds by name that the body never reads (keyword-called hooks and callbacks, Strawberry argument probes, upstream-verbatim signatures, fixtures a fixture requests for setup or teardown order, parametrize columns); three more share lines counted elsewhere | 95 | 0 | keep |
| The rest, reviewed in item 21 or added since, each reason line stating its cause (framework `Meta` reads, mixin `__init__` chains, filter overrides, `Any` forwards, django-stubs / typeshed omissions) | 356 | 21 | keep |

### By rule

| Rule | Hits | Package | Tests | Examples | Scripts | Root |
| --- | --- | --- | --- | --- | --- | --- |
| `reportArgumentType` | 275 | 23 | 240 | 12 | 0 | 0 |
| `reportAttributeAccessIssue` | 113 | 25 | 87 | 1 | 0 | 0 |
| `reportIncompatibleVariableOverride` | 70 | 6 | 56 | 8 | 0 | 0 |
| `reportIncompatibleMethodOverride` | 64 | 7 | 52 | 5 | 0 | 0 |
| `reportAny` | 37 | 10 | 11 | 16 | 0 | 0 |
| `reportUnknownMemberType` | 32 | 26 | 4 | 2 | 0 | 0 |
| `reportAssignmentType` | 28 | 0 | 25 | 1 | 2 | 0 |
| `reportExplicitAny` | 28 | 26 | 0 | 1 | 1 | 0 |
| `reportReturnType` | 23 | 1 | 21 | 1 | 0 | 0 |
| `reportUnknownVariableType` | 20 | 18 | 2 | 0 | 0 | 0 |
| `reportCallIssue` | 14 | 1 | 12 | 1 | 0 | 0 |
| `reportUnknownArgumentType` | 14 | 5 | 2 | 7 | 0 | 0 |
| `reportUnsafeMultipleInheritance` | 13 | 6 | 5 | 2 | 0 | 0 |
| `reportIndexIssue` | 10 | 0 | 10 | 0 | 0 | 0 |
| `reportGeneralTypeIssues` | 5 | 0 | 5 | 0 | 0 | 0 |
| `reportInvalidTypeArguments` | 5 | 1 | 4 | 0 | 0 | 0 |
| `reportPropertyTypeMismatch` | 5 | 5 | 0 | 0 | 0 | 0 |
| `reportUndefinedVariable` | 5 | 0 | 5 | 0 | 0 | 0 |
| `reportFunctionMemberAccess` | 4 | 4 | 0 | 0 | 0 | 0 |
| `reportUnusedVariable` | 4 | 0 | 4 | 0 | 0 | 0 |
| `reportMissingSuperCall` | 3 | 2 | 1 | 0 | 0 | 0 |
| `reportOptionalMemberAccess` | 3 | 3 | 0 | 0 | 0 | 0 |
| `reportUntypedFunctionDecorator` | 3 | 2 | 1 | 0 | 0 | 0 |
| `reportDeprecated` | 2 | 1 | 1 | 0 | 0 | 0 |
| `reportUnnecessaryIsInstance` | 2 | 2 | 0 | 0 | 0 | 0 |
| `reportIncompatibleUnannotatedOverride` | 1 | 1 | 0 | 0 | 0 | 0 |
| `reportRedeclaration` | 1 | 0 | 1 | 0 | 0 | 0 |
| `reportUnusedCallResult` | 1 | 0 | 1 | 0 | 0 | 0 |

### Most ignores per file

| File | Lines |
| --- | --- |
| `tests/utils/test_querysets.py` | 51 |
| `tests/test_resource_policy.py` | 20 |
| `tests/filters/test_sets.py` | 18 |
| `tests/optimizer/test_hints.py` | 17 |
| `tests/rest_framework/test_resolvers.py` | 17 |
| `tests/filters/test_inputs.py` | 16 |
| `tests/test_list_field.py` | 16 |
| `tests/types/test_relay_interfaces.py` | 16 |
| `django_strawberry_framework/utils/_queryset_private.py` | 15 |
| `django_strawberry_framework/filters/sets.py` | 14 |


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
