# Ruffing

The standing tracker for ruff, the project's linter and formatter. ruff checks and formats every tracked Python file,
as configured in `pyproject.toml` `[tool.ruff]`. This file records:

- what is on;
- where each rule is relaxed and why;
- how many `# noqa` comments each part of the tree carries;
- what is still to do.

Rules of the road:

- A rule family is selected whole. A site the rule is wrong about carries `# noqa: CODE - reason`.
- A folder the rule is wrong about gets a per-file ignore, with its reason in `pyproject.toml`.
- A rule is off only by design (see [Off by design](#off-by-design)).
- Update the numbers below in the same change that moves them; [Measuring](#measuring) has the commands.
- `scripts/check_noqa_suppressions.py` (pre-commit and the CI lint job) holds every site to the generated ledger
  `scripts/noqa_suppressions.toml`: each code suppressed there, and its `# noqa` lines with no reason (`bare`). A
  count may only fall; a new suppression, or a new one without a reason, fails. It also refuses a file-level
  `# ruff: noqa` and a blanket `# noqa`.

## Status

Measured 2026-11-11 on the tree after 21cc9c7f, ruff 0.17.4; `# noqa` counts include items 42-47.

| | Count |
| --- | --- |
| Stable rules | 815: 806 on, 9 off by design |
| Preview-only rules | 142, all off (`preview` is not enabled) |
| Lines carrying `# noqa` | 375, in 121 files |
| `# noqa` lines with no reason | 0 |
| Site ledger (`scripts/noqa_suppressions.toml`) | 385 suppressed codes and 0 `bare` lines, at 313 sites |
| `# ruff: disable[...]` fences | 9, every one `ERA001` around a TODO-anchored pseudo block |
| File-level `# ruff: noqa` | 0 |
| Complexity ratchets | `max-complexity` 45, `max-branches` 39, `max-returns` 20, `max-args` 18, `max-statements` 133, `max-positional-args` 10 |

The complexity settings are ratchets at today's maxima: no new function may exceed the worst one. Lowering a
threshold lists the functions above it.

## Coverage by area

Every area runs all 806 rules except the per-file ignores listed for it. The density is the number of `# noqa` lines
per 1,000 lines of source.

| Area | Files | Lines | `# noqa` lines | Per 1k lines | Per-file ignores |
| --- | --- | --- | --- | --- | --- |
| Package (`django_strawberry_framework/`) | 131 | 115,070 | 164 | 1.43 | none |
| tests/ | 217 | 257,748 | 102 | 0.40 | 17 codes, plus `D102` / `D103` on `test_*.py` |
| examples/ | 266 | 202,432 | 94 | 0.46 | 12 codes, plus `D102` / `D103` on `test_*.py`, `D` / `DJ008` on migrations, `INP001` / `UP031` by folder |
| scripts/ | 46 | 45,205 | 12 | 0.27 | 6 codes |
| Root (`conftest.py`, `line_count.py`, `docs/dry/export_dry_review.py`) | 3 | 2,254 | 4 | 1.77 | `TID253`, `T201`, `INP001` per file |

### Package, by subpackage

| Part | Files | Lines | `# noqa` lines | Per 1k lines |
| --- | --- | --- | --- | --- |
| top-level modules | 28 | 22,356 | 51 | 2.28 |
| `utils/` | 28 | 21,571 | 10 | 0.46 |
| `filters/` | 6 | 18,529 | 23 | 1.24 |
| `optimizer/` | 14 | 13,128 | 11 | 0.84 |
| `rest_framework/` | 9 | 8,663 | 2 | 0.23 |
| `types/` | 8 | 8,674 | 32 | 3.69 |
| `forms/` | 5 | 5,725 | 1 | 0.17 |
| `mutations/` | 7 | 5,111 | 12 | 2.35 |
| `extensions/` | 5 | 4,431 | 3 | 0.68 |
| `orders/` | 5 | 2,141 | 1 | 0.47 |
| `auth/` | 4 | 2,084 | 7 | 3.36 |
| `testing/` | 4 | 1,049 | 9 | 8.58 |
| `management/` | 5 | 876 | 0 | 0 |
| `middleware/` | 3 | 732 | 2 | 2.73 |

`types/` is mostly `finalizer.py` (22 lines: local imports that break cycles). `testing/` is the PascalCase field
factories and the unittest mixin.

### `# noqa` by code

| Code | Lines | Package | Tests | Examples | Scripts / root | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `PLC0415` | 121 | 80 | 27 | 6 | 8 | a local import: an import cycle, an optional dependency (Channels, DRF, the Postgres driver), or a subsystem bound only when imported |
| `A002` | 71 | 9 | 2 | 60 | 0 | a `filter` / `id` parameter that is the GraphQL argument name or a public keyword |
| `FBT001` | 5 | 2 | 2 | 1 | 0 | Django's positional `execute_wrapper(..., many, ...)` |
| `BLE001` | 24 | 21 | 1 | 1 | 1 | deliberate containment: consumer code may raise anything, a boundary fails closed, cleanup must not mask the primary error |
| `N802` | 14 | 10 | 4 | 0 | 0 | PascalCase field factories (graphene-django parity), unittest vocabulary |
| `FBT003` | 12 | 0 | 11 | 1 | 0 | the bool is the value under test, or mirrors `execute_wrapper` |
| `S101` | 11 | 11 | 0 | 0 | 0 | django-filter's own asserts, upstream invariants |
| `S102` | 11 | 0 | 11 | 0 | 0 | `exec` of a literal program the test runs |
| `S610`, `S611` | 20 | 0 | 9 | 11 | 0 | the hostile `.extra()` / `RawSQL` member term is the input under test |
| `N815` | 11 | 0 | 6 | 5 | 0 | camelCase model fields the naming-collision tests need |
| `E501` | 8 | 0 | 6 | 2 | 0 | a `path::Symbol` citation wider than the limit on its own line |
| `DJ001` | 7 | 0 | 5 | 2 | 0 | NULL as fixture input |
| `ANN401` | 6 | 6 | 0 | 0 | 0 | an `Any` the package does not own, each with a basedpyright reason |
| Others | 55 | 25 | 18 | 5 | 7 | 31 codes, one to five lines each |

### Most `# noqa` per file

| File | Lines |
| --- | --- |
| `tests/utils/test_errors.py` | 34 |
| `examples/fakeshop/apps/kanban/schema.py` | 23 |
| `django_strawberry_framework/types/finalizer.py` | 22 |
| `django_strawberry_framework/filters/inputs.py` | 13 |
| `examples/fakeshop/test_query/test_library_shapes_api.py` | 13 |
| `examples/fakeshop/apps/library/schema.py` | 12 |
| `tests/filters/test_sets.py` | 12 |
| `examples/fakeshop/apps/glossary/schema.py` | 10 |
| `tests/forms/test_resolvers.py` | 10 |
| `tests/utils/test_querysets.py` | 10 |

## Per-file ignores

Each row gives the number of sites the ignore hides today and the reason.

| Code | Tests | Examples | Scripts | Why |
| --- | --- | --- | --- | --- |
| `S101` | 20,396 | 10,618 | | assert is the pytest idiom |
| `D102`, `D103` (`test_*.py`) | 1,468 | 419 | | the test name is the summary; most tests carry a contract docstring anyway |
| `RUF012` | 1,232 | 969 | | `Meta.fields = [...]`, `permission_classes = [...]`, `Meta.ordering`: the consumer idiom, not a `ClassVar` |
| `PLR2004` | 462 | 1,048 | 39 | assertions and reports compare against literal expected values |
| `TC001`-`TC003` | 294 | 459 | | strawberry / `DjangoType` classes built inside functions, mostly without `from __future__ import annotations`; the fix would quote about 790 annotations |
| `D401` | 544 | 431 | | a test docstring states the contract declaratively |
| `TID253` | 197 | 378 | | pytest-django sets up Django and the fakeshop `pythonpath` before collection (also `conftest.py`) |
| `DJ008` | 316 | 22 (migrations) | | throwaway test models; a migration's `TYPE_CHECKING`-only row shapes |
| `D106` | 53 | 298 | | every site is `class Meta:` |
| `N806` | 159 | | | a class built by `type(...)` or a factory binds to a PascalCase local |
| `INP001` | | 120 | 46 | folders with no `__init__.py` by design: scripts/, fakeshop's top-level modules, `examples/fakeshop/tests/`, `test_query/` |
| `D` (migrations) | | 80 | | `makemigrations` writes them |
| `UP031` (`test_query/`) | | 78 | | GraphQL text is all braces; `str.format` / f-strings would double them |
| `SLOT000`, `SLOT001` | 52 | 4 | | hostile `str` / `tuple` subclasses model consumer values, which carry an instance `__dict__` |
| `S603`, `S607` | 87 | | 42 | a fixed argv of git, uv, ruff or `sys.executable` |
| `S105`-`S107` | 5 | 13 | | fixture credentials and the example's dev `SECRET_KEY` |
| `T201` | | | 325 | print is the CLI output (also `line_count.py`, `docs/dry/export_dry_review.py`) |
| `PERF` | | | 22 | one-shot scripts are not a performance surface |

## Off by design

| Code | Sites | Why |
| --- | --- | --- |
| `SLF001` | 3,454 | the package shares underscore names across its modules (basedpyright's `reportPrivateUsage` is off for the same reason) |
| `TRY003`, `EM101`, `EM102` | 2,784 | exception-message style only |
| `CPY001` | 663 | no copyright headers |
| `FIX002`, `TD003` | 9 each | a TODO is the `TODO(spec-NNN slice N): ...` anchor, which names a spec or backlog entry, not an issue link; the rest of `TD` and `FIX` is on |
| `D203`, `D213` | | the opposites of `D211` / `D212`, which the Google convention selects |

## Config settings

- `logger-objects`: the package logger, so `BLE001` and `LOG` see a handler that logs.
- `flake8-annotations.allow-star-arg-any`: clears `*args: Any, **kwargs: Any` forwards.
- `flake8-boolean-trap.extend-allowed-calls`: `utils/_narrowing.py::read_attr`, which is `getattr` typed `object`.
- `flake8-import-conventions.aliases`: ruff's default map minus `datetime = dt`.
- `flake8-tidy-imports`:
  - `ban-relative-imports = "parents"`: siblings stay relative.
  - `banned-module-level-imports`: the fakeshop top-level modules, so the package can never import the example
    project.
- `flake8-type-checking`: `quote-annotations`, `runtime-evaluated-decorators` / `-base-classes` (the Strawberry
  decorators and `DjangoType`), and `exempt-modules` (`strawberry`, since a resolver's `Info` is read from its
  annotation at schema build).
- `pep8-naming.classmethod-decorators`: Django's `classonlymethod`.
- `D400`, `D401`, `D404`, `D413` and `D204` / `D215` / `D406`-`D409` are selected by code: the Google convention
  drops them from a `D` prefix select.

## Files ruff skips

`ruff check --show-files` lists exactly the tracked Python files plus `pyproject.toml`. The files it skips are:

- git-ignored scratch trees (`docs/shadow/`, `.venv/`, `.work/`), through `respect-gitignore`;
- `hunt-ws/` (`extend-exclude`), the untracked bug-hunt evidence copies, which a repo-wide `--fix` would otherwise
  rewrite.

`[tool.ruff.format]` excludes `*.md`, because fenced Python in Markdown is verbatim example content.

`force-exclude = true` applies every exclusion to paths named on the command line too. So `ruff format <paths>`
leaves a named `.md` or `hunt-ws/` file alone, and a `--check` naming only excluded paths checks nothing.

`scripts/check_trailing_commas.py` reads `extend-exclude` at run time and skips the same trees. Its own
`ruff format` calls pass `--no-force-exclude`, so every file its `--fix` edits is reflowed.

## Custom formatter interplay

`scripts/check_trailing_commas.py` (hook `source-layout`, CI `--check`) and ruff share one pipeline, in this order:

1. the script's `--fix`;
2. `ruff check --fix`;
3. `ruff format`.

The script's `--fix` reruns `ruff format` on the files it rewrote. It repeats the comma edit and the format until
nothing changes (`MAX_FIX_ROUNDS`, 3). A file still changing after that is an `unfixable` error, never a pass. The
pipeline reaches a fixpoint: neither side undoes the other's edits.

What each side owns:

- **Single-line collection and signature layout belongs to the script.**
  - It explodes at 4 items (2 in `models.py`).
  - It collapses below that when the one-line form fits `line-length` (99, not E501's 110), measured in ruff's
    display columns.
  - `COM812` only adds commas to constructs that are already multi-line.
- **Imports belong to isort and the formatter.** A parenthesized import stays exploded after a trailing comma
  (`split-on-trailing-comma`).
- **String literals, docstrings (`D2xx` / `D4xx`) and quotes (`Q`) are out of the script's reach.**
- **The script's ASCII check is stricter than `RUF001`-`RUF003`**, which stay on.

Suppressions go on the element, not after a closing bracket:

- The script refuses to explode a line that ends in `# noqa`, `# pyright: ignore` or `# type: ignore`. After the
  explode the diagnostic moves to an element line, so `RUF100` would delete the noqa and basedpyright would report
  the ignore as unneeded.
- `--check` reports the line as not fixable, and `--fix` as an `unfixable` error.
- The refusal holds in every `--fix` round. A construct that `ruff format` collapses onto such a line fails that
  round too, so `--fix` never exits 0 on a file `--check` then rejects.

Ruff against itself:

- After a lengthening autofix (a `TC` quote, a `TID252` absolute import), run `ruff check --fix` and `ruff format`
  twice.
- Collapsing a wrapped implicit concatenation in a short collection fires `ISC001`; its fix joins the strings in the
  same pass.
- After any `--unsafe-fixes` pass, rerun the whole pipeline: `PLR1714`, `SIM101` and `C4` can write a single-line
  4-item literal.
- A future `CPY001` header would have to come from
  `scripts/build_kanban_tracked_path_constants.py::render_constants`, since the module it generates passes the same
  pipeline.

## To do

Nothing open.

## Waiting on you

- The 60 example `filter:` / `id:` resolver parameters (`A002`). A fakeshop-level Strawberry `NameConverter` that
  strips a trailing `_` would let them read `filter_` with the wire name unchanged. But `FilterInput`'s docstring
  prescribes `filter:` for consumers. Adopt the converter in the example project?
- Keep the per-file ignores that are policy calls?
  - `DJ008`, `SLOT000` / `SLOT001` and `S105`-`S107` for tests/ and examples/;
  - `S603` / `S607` for tests/ and scripts/;
  - `N806` (159 PascalCase class bindings in tests, which would read as instances if renamed lowercase);
  - `D102` / `D103` on test functions (1,887 functions without a docstring; turning the rule on means writing that
    many true contract docstrings).

## Done

Each item's commit holds the detail (`git log -S '<code>' -- pyproject.toml`).

1. `E`, `W`: the formatter wraps at 99; `E501` flags only lines past 110.
2. `F`.
3. `I`, with `django_strawberry_framework` first-party.
4. `UP`, targeting py310.
5. `ANN`, everywhere (item 31 annotated the tests: about 10,100 return types, no `Any`).
6. `D`, Google convention.
7. `A`.
8. `ARG`, with `*args` / `**kwargs` padding exempt; an unused parameter a framework passes by keyword is `del`eted.
9. `ASYNC`.
10. `B`.
11. `N`.
12. `C4`.
13. `ERA`: TODO-anchored pseudo blocks sit inside a `# ruff: disable[ERA001]` / `enable` fence (AGENTS.md).
14. `FLY`.
15. `PERF`, except scripts/.
16. `Q`, `RSE`.
17. `RUF`, including `RUF100` (unused noqa) and `RUF001`-`RUF003`.
18. `SIM`.
19. `COM`, `ISC`: `COM812` pairs with `scripts/check_trailing_commas.py`.
20. `PL`.
21. Every other stable family with no site at the time.
22. Dead config ignores deleted.
23. `T201`, except scripts/ and the root tools.
24. Every remaining family selected, so the config names every stable rule.
25. `ISC004`, `PYI055`.
26. `ICN001`, `INP001`.
27. `TD002`, `TD004`, `TD005`.
28. The small real-signal codes (about 340 sites), fixed at the root.
29. `DJ012`, `DJ001`.
30. Security and boundaries (`S`, `BLE001`).
31. Per-file ignores for tests/ and examples/ shrunk from 21 and 14 codes to today's lists.
32. `ANN401`, `D107`.
33. `FBT002`.
34. `FBT001`.
35. `FBT003`.
36. `D400`, `D404`, `D401`, and the complexity ratchets.
37. `# noqa` refactored away (410 to 302 lines): `utils/truth.py` identity reads, `_logger.py`, `id_` parameters.
38. `D413` and `TID252` everywhere; `TC001`-`TC003` and `PLR2004` outside tests/ and examples/.
39. `PLC0415`: 2,074 imports hoisted; the rest are local with a reason.
41. Two redundant re-export paths dropped before the first release, `types.relay.SyncMisuseError` and
    `filters.base.LazyRelatedClassMixin` (2 `PLC0414`); every public path to both names stays.
42. Two `filters/inputs.py` local imports (`PLC0415`) moved to the module's existing top-level imports of
    `types.converters` and `utils.querysets`; no cycle remained.
43. The last `PLC0414` re-export paths dropped: the four decode kinds from `forms.converter` and
    `rest_framework.serializer_converter`, `FieldError` / `NON_FIELD_ERROR_KEY` from `mutations.inputs` (10 lines).
    Every import names the defining module, `utils.inputs` or `utils.errors`; `FieldError` stays public at the
    package root and `mutations`.
44. Parametrized boolean test columns are keyword-only (`*` before the first one), so `FBT001` no longer fires: 64
    `# noqa` lines in 58 test functions.
45. The `# noqa` site ledger, `scripts/noqa_suppressions.toml`, held by `scripts/check_noqa_suppressions.py` (hook
    and CI lint) the way `check_type_suppressions.py` holds basedpyright's: counts per site and code, plus `bare`,
    may only fall, and a commit raising a total needs the `Suppression-Growth-Approved:` trailer.
46. Every `A002` carries its reason (71 lines): the `filter` / `id` parameter name is the GraphQL argument name.
40. A reason on every `# noqa`: the last 47 bare lines carry one, and one redundant test-local import in
    `tests/test_resource_policy.py` joined its module's top-level import. The ledger holds `bare` at 0, so a new bare
    `# noqa` fails.

## Measuring

```bash
uv run ruff --version
uv run ruff rule --all --output-format json     # count by "status": Stable / Preview / Removed
uv run ruff check --show-settings django_strawberry_framework/__init__.py   # linter.rules.enabled
uv run ruff check --exit-zero --statistics --config 'lint.per-file-ignores={}' --select <codes> tests   # sites a per-file ignore hides
uv run ruff check --exit-zero --statistics --select SLF001,TRY003,EM101,EM102,CPY001,FIX002,TD003 .
git grep -c '# noqa' -- '*.py'                  # then group by path prefix
uv run python scripts/check_noqa_suppressions.py   # suppressed codes and bare lines, from comment tokens
```

Sum `scripts/noqa_suppressions.toml` by path prefix or by code for the per-area and per-code tables: each key is a
site (`path::QualifiedName`), each value its counts.

Count `# noqa` from comment tokens, not raw grep, so a docstring that quotes one is not counted. Run every
command in a `work.py` copy, never in the shared checkout.

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
