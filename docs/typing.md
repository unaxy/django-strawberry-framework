# Typing

The standing tracker for basedpyright, the project's one type checker. It records:

- which rules are on where;
- how many suppressions (`# pyright: ignore[...]` comments and `typing.cast` calls) each part of the tree holds;
- what is still to do.

Rules of the road:

- basedpyright runs in `all` mode on every Python file, in two passes:
  - the main pass at Python 3.11;
  - the floor pass at 3.10 (`pyrightconfig.floor.json`).

  A warning fails either pass.
- Every suppression carries a `# basedpyright: <why>` line naming its real cause.
- A diagnostic is fixed at the root, never silenced to make room.
- `scripts/check_type_suppressions.py` (pre-commit and the CI lint job) holds the line:
  - It refuses an ignore naming a rule `pyproject.toml` marks `# Locked`.
  - It refuses any file-level `# pyright:` directive.
  - It refuses any per-site count above the generated ledger `scripts/type_suppressions.toml`. A count may only
    fall.
  - In CI, a commit that raises a total (casts, or one rule's ignores) fails unless it carries the maintainer's
    `Suppression-Growth-Approved:` trailer. Moving a suppression between sites with the totals unchanged needs none.
- The ledger sees syntax only. `scripts/typing_delta.py <base-rev>` reports the weakenings it cannot see:
  - narrowing predicates claiming more than they check;
  - signatures widened to `object` / `Any`;
  - declared attributes read with a default;
  - suppressions moved into an `object` parameter.

  Run it on any change that touches typing.
- Update the numbers below in the same change that moves them; [Measuring](#measuring) has the commands.

## Status

Measured 2026-11-11 on the tree after 21cc9c7f, basedpyright 1.40.2 (pyright 1.1.414).

| | Count |
| --- | --- |
| Errors, main and floor passes | 0 / 0 |
| Rules locked (on everywhere, no suppression left) | 67 |
| Ignore comments (rule hits) | 698, on 646 lines in 157 files (1,897 at the start of the 0.0.15 sweep) |
| `typing.cast` calls | 103 (432 at the start of the cast work) |
| Public API type completeness (`check_public_types.py`) | 100% |

## Coverage by area

basedpyright reads every tracked Python file. The table shows what each area checks and how many suppressions it
holds. The density is the number of suppressions (ignore lines plus casts) per 1,000 lines of source.

| Area | Files | Lines | Rules relaxed | Ignore lines | Casts | Per 1k lines |
| --- | --- | --- | --- | --- | --- | --- |
| Package (`django_strawberry_framework/`) | 131 | 115,070 | none | 116 | 70 | 1.62 |
| tests/ | 217 | 257,748 | `reportUnannotatedClassAttribute`, `reportUnusedCallResult` | 472 | 22 | 1.92 |
| examples/ | 266 | 202,432 | `reportUnannotatedClassAttribute`; `reportUnusedCallResult` in its test folders | 55 | 0 | 0.27 |
| scripts/ | 46 | 45,205 | none | 3 | 11 | 0.31 |
| Root (`conftest.py`, `line_count.py`, `docs/dry/export_dry_review.py`) | 3 | 2,254 | none | 0 | 0 | 0 |

Rules relaxed in every area are listed under [Rules off](#rules-off).

### Package, by subpackage

| Part | Files | Lines | Ignore lines | Casts | Per 1k lines |
| --- | --- | --- | --- | --- | --- |
| top-level modules | 28 | 22,356 | 27 | 16 | 1.92 |
| `utils/` | 28 | 21,571 | 26 | 13 | 1.81 |
| `filters/` | 6 | 18,529 | 22 | 9 | 1.67 |
| `optimizer/` | 14 | 13,128 | 4 | 16 | 1.52 |
| `rest_framework/` | 9 | 8,663 | 11 | 3 | 1.62 |
| `types/` | 8 | 8,674 | 4 | 2 | 0.69 |
| `forms/` | 5 | 5,725 | 4 | 2 | 1.05 |
| `mutations/` | 7 | 5,111 | 5 | 1 | 1.17 |
| `extensions/` | 5 | 4,431 | 4 | 2 | 1.35 |
| `orders/` | 5 | 2,141 | 2 | 0 | 0.93 |
| `auth/` | 4 | 2,084 | 3 | 5 | 3.84 |
| `testing/` | 4 | 1,049 | 1 | 1 | 1.91 |
| `management/` | 5 | 876 | 1 | 0 | 1.14 |
| `middleware/` | 3 | 732 | 2 | 0 | 2.73 |

Where the package suppressions sit:

- `utils/_queryset_private.py` (15 ignore lines) is the one seam reading Django's private QuerySet state.
- `auth/` holds the `AUTH_USER_MODEL` and `SESSION_ENGINE` casts. Django does not check the type of either, so a
  runtime check would refuse a project that works today.
- `optimizer/` casts are reads of Django's own slots on package-built querysets, on per-row paths.

### Ignores by rule

From the ledger. Lines naming two rules count once per rule.

| Rule | Hits | Package | Tests | Examples | Scripts |
| --- | --- | --- | --- | --- | --- |
| `reportArgumentType` | 252 | 20 | 220 | 12 | 0 |
| `reportAttributeAccessIssue` | 103 | 21 | 81 | 1 | 0 |
| `reportIncompatibleVariableOverride` | 63 | 8 | 47 | 8 | 0 |
| `reportIncompatibleMethodOverride` | 52 | 7 | 41 | 4 | 0 |
| `reportAny` | 36 | 10 | 10 | 16 | 0 |
| `reportExplicitAny` | 28 | 26 | 0 | 1 | 1 |
| `reportAssignmentType` | 28 | 0 | 25 | 1 | 2 |
| `reportUnknownMemberType` | 23 | 19 | 4 | 0 | 0 |
| `reportReturnType` | 21 | 0 | 20 | 1 | 0 |
| `reportUnknownVariableType` | 19 | 17 | 2 | 0 | 0 |
| `reportUnsafeMultipleInheritance` | 12 | 6 | 4 | 2 | 0 |
| `reportUnknownArgumentType` | 12 | 3 | 2 | 7 | 0 |
| `reportCallIssue` | 11 | 1 | 9 | 1 | 0 |
| `reportIndexIssue` | 10 | 0 | 10 | 0 | 0 |
| `reportInvalidTypeArguments` | 5 | 1 | 4 | 0 | 0 |
| `reportPropertyTypeMismatch` | 5 | 5 | 0 | 0 | 0 |
| `reportUndefinedVariable` | 5 | 0 | 5 | 0 | 0 |
| `reportGeneralTypeIssues` | 4 | 0 | 4 | 0 | 0 |
| `reportMissingSuperCall` | 3 | 2 | 0 | 1 | 0 |
| `reportUnnecessaryIsInstance` | 2 | 2 | 0 | 0 | 0 |
| `reportDeprecated` | 2 | 1 | 1 | 0 | 0 |
| `reportFunctionMemberAccess` | 1 | 1 | 0 | 0 | 0 |
| `reportIncompatibleUnannotatedOverride` | 1 | 1 | 0 | 0 | 0 |

Most test ignores are deliberately ill-typed input: hostile values, forged classes and rejected writes that the test
exists to send. The package's `reportExplicitAny` / `reportAny` lines are `Any`s the package does not own:

- the permission hooks' `data` / `instance`, kept `Any` so an override can narrow them;
- `DjangoType.get_queryset`'s `info`;
- the root `__getattr__`;
- Strawberry's overloaded `run`.

### Most ignores per file

| File | Lines |
| --- | --- |
| `tests/utils/test_querysets.py` | 51 |
| `tests/test_resource_policy.py` | 20 |
| `tests/rest_framework/test_resolvers.py` | 16 |
| `tests/test_list_field.py` | 16 |
| `django_strawberry_framework/utils/_queryset_private.py` | 15 |
| `tests/optimizer/test_hints.py` | 15 |
| `tests/types/test_relay_interfaces.py` | 15 |
| `tests/filters/test_sets.py` | 14 |
| `tests/optimizer/test_extension.py` | 13 |
| `django_strawberry_framework/filters/sets.py` | 12 |

## Rules off

Off by design, everywhere: `reportImplicitStringConcatenation`, `reportPrivateUsage`, `reportUnusedFunction`,
`reportImportCycles`, `reportUninitializedInstanceVariable`. The reasons are in `pyproject.toml`.

Off by design in tests/ and examples/:

- `reportUnannotatedClassAttribute`. The flagged attributes are declarative configuration a framework reads by name
  (`Meta`, admin options, declared filters, migrations, `AppConfig`) on classes nothing subclasses. Satisfying the
  rule means `@final` or `ClassVar[...]` on each, which changes the bare `class Meta:` the READMEs teach.
- `reportUnusedCallResult`, in tests/ and the example test folders only. A test calls for side effects.

Off at the 3.10 floor only: the five `reportUnknown*` rules and `reportUnnecessaryTypeIgnoreComment`. django-stubs
imports `typing.Self` (3.11), so at 3.10 every stub `-> Self` reads as `Unknown`. The main pass enforces them.

## To do

Do the items in order; each lands as its own commit.

- [ ] 42. Strict by default for a new file. The root `[tool.basedpyright]` sets `reportUnannotatedClassAttribute`
  and `reportUnusedCallResult` to `"none"`, so a `.py` outside every listed environment gets the tests' leniency.
  - Set both to `"error"` at the root, and give tests/ and the example test folders explicit environments that turn
    them off.
  - Drop the root-file environments that exist only to turn them on (`conftest.py`, `line_count.py`,
    `docs/dry/export_dry_review.py`), where import roots allow it.
  - Both passes stay at 0 errors. The off-by-default count must match before and after: about 18,100 with both rules
    forced on in tests and examples.
- [ ] 43. Lazy-export typing parity. The package root's `__getattr__` returns `Any`, so a lazy export missing from
  its `TYPE_CHECKING` mirror types a consumer import as `Any`.
  - Add a test row asserting that the `_DRF_SOFT_EXPORTS` keys equal the names the `TYPE_CHECKING` block imports,
    both read from the module's AST.
  - `tests/rest_framework/test_soft_dependency.py` pins the key set only.
- [ ] 45. The reason rule, gated. About 37 ignore lines carry no reason (2026-11-02 count).
  - `check_type_suppressions.py` refuses an ignore with no comment text on its line and no `#` line directly above
    (or above its decorators).
  - It also refuses an inert `# type: ignore`, which `enableTypeIgnoreComments = false` never reads.
  - Write each missing reason with its real cause, and add the gate's rows to
    `tests/test_check_type_suppressions.py`. The ledger counts do not move.
- [ ] 47. Gates for what the ledger cannot see. `typing_delta.py` reports these today; the gates would refuse them:
  - a truthful-reads rule refusing a `getattr` default on a declared attribute;
  - a ledger kind for parameterized predicate claims (`TypeIs[...]` / `TypeGuard[...]` over a generic, 43 sites).
- [ ] 48. Re-measure the pre-commit hooks, every hook with today's scope and timing (the last table was
  4ce779e1, nine hooks). Do it after items 42 and 45, which change hook scope.
- [ ] 49. Public reads that infer `Any`. A consumer gets `Any` rows from each of these, and none can be pinned
  without a `reportExplicitAny` ignore:
  - `DjangoType.get_queryset` on a type that does not override it returns `QuerySet[Any, Any]`. The base's comment
    says a TypeVar return was rejected because overrides return `super().get_queryset(...)` non-generically, so
    this needs a design.
  - django-filter's `FilterSet.qs` reads `QuerySet[Any, Any]`.
  - `testing.Response.data` / `.extensions` read `dict[str, Any] | None`, inherited from Strawberry's `Response`.

  Narrow each with a package type (a typed `qs`, `dict[str, object] | None`), then pin it in
  `tests/test_public_inference.py`.

## Waiting on upstream

- [ ] 23. drf-stubs declares a stub-only `ModelSerializer.Meta` (typeddjango/djangorestframework-stubs#689).
  - #1101 makes the fix (CI green, no review yet); #1069 closed unmerged.
  - Measured with #1101's `serializers.pyi`: nine `reportIncompatibleVariableOverride` ignores go unneeded and nothing
    else moves.
  - Once a release ships it, bump the lock, drop the nine ignores, and retire both `ModelSerializerBase` classes
    (`tests/_idioms.py`, `examples/fakeshop/drf_serializers.py`).
- django-stubs: declare `QuerySet`'s private `_db`, `_hints`, `_fields`, `_prefetch_related_lookups`, `_clone`,
  `_chain`. This retires 6 lines in `utils/_queryset_private.py`. Draft below; the maintainer files it.

### Upstream drafts (the maintainer posts)

drf-stubs, a comment on PR #1101:

```text
Confirming this from a downstream project that type-checks with basedpyright in `all` mode: against 3.18.1 with
this PR's `serializers.pyi`, the nine `reportIncompatibleVariableOverride` suppressions we carry on `class Meta:`
declarations (and the shared base class that exists only to hold one) become unnecessary, and no other diagnostic
changes anywhere in the project. Would be glad to see it land.
```

django-stubs, a new issue titled "Declare QuerySet's private state attributes (_db, _hints, _fields,
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

## Verdicts: don't re-try

These approaches were measured and rejected. Each needs new evidence before it is raised again.

- **A `stubPath` overlay of django-stubs.** It splits class identity (1,044 errors).
- **Asserting through public behaviour instead of private state.** It weakens the tests' claims.
- **Making `DjangoType` generic over its model.** Rows and GraphQL types stay unrelated classes.
- **`unchecked()` / `plant()` escape helpers.** Each is a cast by another name.
- **Collapsing keyword-called hook parameters into `**_kwargs`.** The signature stops documenting the hook.
- **`@final` / `ClassVar` on every `Meta` attribute, or a basedpyright baseline.** See Rules off; a baseline is a
  frozen diagnostic list, not a fix.
- **Typing `DjangoType.get_queryset`'s `info` or the visibility helpers.** `object` is the run-time contract, and
  typing 6 helpers adds 189 `reportArgumentType` sites.
- **A `QuerySet | Awaitable[QuerySet]` `get_queryset` return.** Every direct sync call would have to narrow, to
  retire 7 override ignores.
- **`MultiValueDict[str, UploadedFile]` for uploads.** The `Upload` input delivers non-file values that the form's
  own validation rejects; `dict[str, object]` is the contract.
- **`ClassVar` on metaclass-filled attributes.** Writes through the built class become errors.
- **Narrowing django-stubs' `ConcreteField` / `ForeignKeyField` aliases or the DRF / `FieldMap` / `ModelForm`
  aliases.** These are contravariant or invariant stub TypeVars. Measured: `Never` gives 6 errors and `object` 31;
  the DRF / `FieldMap` / `ModelForm` narrowings give 348, 2 and 81.
- **A runtime check on the `_User` / `SESSION_ENGINE` casts.** Django admits both without a type check, so a check
  would refuse projects that work today.
- **Not taken, by cost:**
  - a mypy cross-check;
  - typing at the declared dependency floors;
  - typing without django-stubs;
  - measuring `reportImportCycles`;
  - `always_run` on the typing hooks (16s per commit; CI catches a deletion-only commit).
- **Third-party bare generics.** Strawberry's `Executor` alias, graphql-core's `GraphQLList` / `GraphQLNonNull`, the
  M2M `_To` default (django-stubs #1802), drf-stubs, django-debug-toolbar, pytest and asgiref were re-checked at the
  graphql-core 3.3.1 / strawberry-graphql 0.328.0 floor. Nothing retires.

## Done

Each item's commit holds the detail (`git log --grep 'item <N>'` or `git log -S` on the symbol).

1. `reportExplicitAny` on for the package, the example project and scripts.
2. tests/ passes `all` mode in both passes; scope is every Python file.
3. Package annotations state their run-time contract.
4. Resolvers declare `graphql_type=` and return honest model rows (94 ignores).
5. `definition_raises`, `module_binding`, direct module patching, `blocked_modules` (239 ignores).
6. The walker hands `get_queryset` a real `strawberry.Info` on the prefetch path.
7. `reportAny` on everywhere, through the typed slots in `utils/_narrowing.py` (`read_attr`, `pk_of`, `dict_of`,
   `list_of`, `call_method`), `utils/typing.py::call_forwarded` / `object_result`, and the test JSON readers.
8. Closed: `reportUnannotatedClassAttribute` stays off in tests/ and examples/.
9. `reportUnusedCallResult` on everywhere but the tests.
10. `reportUnusedParameter` locked.
11. `reportUnknownMemberType` on: model fields annotated with their solved generic, gated by
    `tests/test_model_field_annotations.py`.
12. `reportUnknownVariableType` on: containers typed where they are born; narrowing predicates in place of
    `isinstance` on `object`.
13. `reportUnknownArgumentType` on.
14. `utils/_queryset_private.py` is the one seam for Django's private QuerySet state (156 ignore lines to 35).
15. Real `User` / `AnonymousUser` objects instead of stand-ins.
16. `tests/_idioms.py::relay_hooks` / `async_relay_hooks`.
17. `tests/_info.py` builds real Strawberry `Info` objects.
18. `FilterSet.__init__` overrides spell out their parameters.
19. The field factories declare the value they resolve to.
20. `tests/_execution.py` / `tests/_definition.py` build real execution contexts and definitions.
21. Real objects in place of the other stand-ins; every kept ignore states its real cause (272 ignores).
22. The queryset-state check accepts only a tuple `_fields`.
24. Closed: `get_queryset`'s `info` stays `Any` (see Verdicts).
25. `_CrLampKiosk` renamed.
26. `schema_config_from_info`'s docstring names the real fallback caller.
27. spec-020 and spec-023 show resolvers in the item-4 spelling.
28. Closed: no awaitable `get_queryset` return (see Verdicts).
29. Closed: uploads stay `dict[str, object]` (see Verdicts).
30. Closed: third-party stub gaps; one django-stubs issue drafted (above).
31. Ignore sweep, 1,158 to 927 lines.
32. `testing/client.py`'s `Response` is generic in its raw response.
33. Closed: no `ClassVar` on metaclass-filled attributes.
34. `reportUnreachable` locked.
35. Moved to the board as `TODO-ALPHA-054-0.0.15`: a `get_queryset` hook sees the planning resolver's `info` on the
    prefetch path, a behaviour change rather than a typing one.
36. Cast sweep, phase 1: 399 to 239 package casts, with no new branch and no behaviour change.
37. Cast sweep, phase 2: 191 to 85 package casts, each new raise or branch landing with its test.
38. Cast sweep, phase 3: 85 to 70 package casts, and example and script casts 19 to 11. The kept casts are sorted
    into upstream-only (16) and keep (55), each with its reason.
39. `reportUntypedFunctionDecorator` and `reportOptionalMemberAccess` locked.
40. CI installs exactly the lock (`uv sync --locked` everywhere but the Postgres Django bump).
41. `Typing :: Typed` classifier; `**/hunt-ws` excluded; whole-repo readers skip ruff-excluded trees.
44. `tests/test_public_inference.py` pins what a consumer's checker infers, with `assert_type` (a no-op at run
    time, so both basedpyright passes are the check). It covers:
    - the field factories (`DjangoListField`, `DjangoConnectionField`, `DjangoNodeField`, `DjangoNodesField`, bare
      and typed) and `current_user()`;
    - `FilterSet` / `OrderSet` `apply_sync` / `apply_async`, which keep `QuerySet[Model]`;
    - `TestClient` / `AsyncTestClient` / `GraphQLTestMixin` `query()` and the `Response` reads.

    A change to any of those types is a `reportAssertTypeFailure`. `DjangoType.get_queryset` declares
    `QuerySet[Any, Any]`, which no pin can spell without an ignore, so it is checked by assignment instead: its
    return, inherited or through `super()`, must assign to the caller's `QuerySet[Genre]`, and the README override
    spelling must pass `@override`. The `Any`-typed reads are item 49.
46. Weakenings the ledger could not see were retired:
    - `related_queryset` proves its rows are model instances (`_yields_model_rows`) and raises
      `ConfigurationError` otherwise;
    - one shared `is_lookup`;
    - `BindAskingFilterForm` flags read as attributes;
    - the `_HopKey` alias;
    - `typing_delta.py` written to catch the class.

## Measuring

```bash
uv run basedpyright && uv run basedpyright -p pyrightconfig.floor.json
uv run python scripts/check_type_suppressions.py          # prints the ignore and cast totals
uv run python scripts/typing_delta.py <base-rev> --worktree
```

To get the per-area and per-rule tables, sum `scripts/type_suppressions.toml` by path prefix: each key is
`path::Symbol` and each value maps `cast` or a rule to a count. To get ignore lines and the per-file table, count
`# pyright: ignore[` in comment tokens, not raw grep, so docstrings that quote one are skipped. Run every command
in a `work.py` copy, never in the shared checkout.

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
