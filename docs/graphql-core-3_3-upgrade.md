# graphql-core 3.3 upgrade notes

The package pins `graphql-core>=3.2.0,<3.3` (`pyproject.toml`), and `.github/dependabot.yml` ignores graphql-core
`>=3.3` and strawberry-graphql `>=0.328.0` (the first strawberry release that requires graphql-core 3.3). The upgrade
is on hold: the package gains nothing from 3.3 today, and 3.3.0 ships a request-reachable leak. This file holds what
was measured against graphql-core 3.3.0 and strawberry 0.334.4 so the port does not start from zero. Delete it in the
change that raises the pin.

## Gate

- **Wait for a graphql-core release that fixes [graphql-core#287][gqlcore-287]** (open fix:
  [graphql-core#288][gqlcore-288]). graphql-core 3.3.0 keeps one module-level
  `validation_aborted_error`, and every request that stops validation re-raises it, appending its frames to the same
  traceback, so memory grows per request for the life of the process. It was introduced in 3.3.0a3 (`aab6d50`). If
  the package ever has to ship on an unfixed release, the measured containment is clearing that error's traceback
  (`with_traceback(None)`) after validation, which held memory flat.

## Must change

- **`DjangoMutationExecutionContext`.** `schema.py` imports `ExecutionContext` from `graphql.execution.execute`, which
  3.3 removes, so the package does not import. Rebase the class onto
  `strawberry.schema.schema.StrawberryGraphQLCoreExecutionContext` (strawberry's default execution context, not in its
  `__all__`); basing it on graphql-core's bare `Executor` fails every operation on the `operation_extensions` keyword.
  Port `execute_field` to `(parent_type, source, field_details_list, path, position_context)`, reduce
  `_execution_errors` to `collected_errors.errors`, and delete the test that pins both error-list shapes. A consumer's
  3.2-shaped `execute_field` override breaks, so the release note says so.
- **`extensions/resource_policy.py::_page_bound`.** 3.3 parses an absent argument or directive list as `None`, not
  `()`, so `for argument in node.arguments:` crashes every connection field queried with no arguments
  (`{ allItems { edges { node { name } } } }`). Make it `node.arguments or ()`. It is the only unguarded read of the
  19 AST collection reads audited.
- **`DjangoConnection`.** strawberry 0.334 raises on it unless it carries `@strawberry.type`. Decorating it was
  rejected: the package exists to avoid decorators, so the port needs a route that adds none.

## Can be deleted on 3.3

- `_graphql_core_patches.py`, its tests and its setting (its startup check crashes on 3.3 anyway).
- `optimizer/selections.py::ast_to_converted_selections`.
- `DjangoSchema.stream` and the `DjangoStreamResult` alias, which exist only to type the 3.2 frame.

## Must stay

The five strawberry patches (their upstream bugs still reproduce on 0.334), the resource policy, the request deadline,
the selection walk, and the refusal of incremental execution (`schema.py::_refuse_incremental_execution`).

## Re-check on 3.3

- **Validation literal echo.** One early probe reported that 3.3 validation errors echo a whole input literal, about
  80 MB of error text for an 800 KB document. It was never reproduced afterwards; measure it before sizing any
  error-volume bound.
- **`hide_suggestions`, `max_coercion_errors`, `enable_early_execution`.** New in 3.3, and strawberry 0.334 forwards
  none of them. Turning off suggestions under a production profile would be a new feature with its own seams (the
  package running `validate` and building the executor), not part of the port.

## Settled, do not redo

- **GlobalID error classification.** strawberry 0.331.6 and later raise an `InvalidGlobalIDError` that the error
  policy does not mask. It no longer reaches the package: relation inputs into Relay targets are `strawberry.ID` and
  decoded server-side (`utils/write_values.py::relation_takes_global_id`), like the root `id:`
  (`types/relay.py::decode_global_id`).
- **Comment tokens.** `extensions/resource_policy.py::scan_document_text` counts no `#` comments, so a document of
  comments passes the token bound with zero tokens. Not a bypass: `max_request_body_bytes` already caps it, and
  graphql-core 3.2 does not count comments as tokens either.

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
[gqlcore-287]: https://github.com/graphql-python/graphql-core/issues/287
[gqlcore-288]: https://github.com/graphql-python/graphql-core/pull/288
