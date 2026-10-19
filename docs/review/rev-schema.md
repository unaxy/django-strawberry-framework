# Review: `django_strawberry_framework/schema.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - chain build + runner construction per operation; marker check per field; mutation windows per field; resume gate per streamed op

## Implementation (Worker-2)

Pass 1, address `review/schema.py/implement`. F1 disposition: fixed per the
mechanics prescription (bind the floor seam the same way) - the
qualify-the-glossary alternative was not taken.

- `django_strawberry_framework/schema.py::DjangoSchema._subscribe` added
  beside `_stream`, mirroring its body: `super()._subscribe(...)` wrapped in
  `resumed_stream` when the runner is a `DjangoExtensionsRunner`, else passed
  through untouched. Stays private; no new public names. Ceiling-inert: the
  ceiling upstream never calls `_subscribe`, so the override is dead there
  (the full `tests/test_schema.py` + `tests/extensions/test_operation_state.py`
  run passes 187/188 with it reverted, failing exactly the new pin).
- Un-skipped 11 subscribe-only `_SKIP_WITHOUT_STREAM` rows in
  `tests/extensions/test_operation_state.py` (every row whose body calls no
  `schema.stream`: the two Proof nodes plus the frame/asend/close/cancel/
  athrow/mode/outer-budget/child-context rows and the execute_sync-only
  forged-assignment row). The 4 rows genuinely needing `Schema.stream` stay
  skipped, as do all 4 `_SKIP_WITHOUT_STREAM` rows in `tests/test_schema.py`.
- New direct-call pin
  `tests/test_schema.py::test_a_subscribe_whose_runner_is_not_the_packages_is_handed_back_untouched`
  (package runner -> `_ResumedStream`, foreign runner -> identity), covering
  the override body; no new pragma.
- C2: the `_stream` coverage sentence restated as the shipped override set
  (two overrides, each firing where its upstream exists).
- C1/M1 re-pinned at 3.2.10 in both docstrings; M2-M8 and L1-L5 landed per
  their text-afters, except L5's `DjangoMutationExecutionContext` first line,
  which lands as a summary plus the record's sentence as its description: the
  record's 117-character one-liner exceeds the E501 110 grace and a naive
  wrap trips D205/D415, so the sentence is kept verbatim behind a
  lint-compliant summary line.
- M6 choice: prose reword (the smaller correct change); no live row mounted.
- M7 note for the verifier: the record's Proof pattern
  (`operationName`` a client can put in a request body`) matches the
  text-after's own tail, so it prints 1 both before and after; the
  discriminating pattern `Every ``operationName`` a client` (no `string`)
  goes 1 -> 0, and the text-after landed exactly.

Wheel audit, 0.317 + 0.318 (wheels fetched from PyPI into
`docs/review/temp-tests/schema/implement/wheels/`; both carry an identical
`strawberry/schema/schema.py`, sha256
`beef81019948755883d55d454854014ab6b371b0747f7120fd833a76fccdd72d`):

| Release | `subscribe` | `_subscribe` | `stream` | `_stream` |
|---|---|---|---|---|
| 0.316.0 (floor, mech record) | yes | yes, routed to | no | no |
| 0.317.0 (this audit) | yes | yes, routed to | no | no |
| 0.318.0 (this audit) | yes | yes, routed to | no | no |
| 0.319.0 (mech record) | yes | no | yes | yes, routed to |
| 0.324.0 (ceiling, mech record) | yes | no | yes | yes, routed to |

So the floor band 0.316-0.318 routes subscriptions through `_subscribe`
alone, and the `_subscribe` override fires on exactly that band while
`_stream` fires on 0.319+: each override covers where its upstream exists,
as the restated docstrings state. The floor `_subscribe` signature
`(execution_context, extensions_runner, middleware_manager,
execution_context_class=None, operation_extensions=None)` is accepted by the
override's `(execution_context, extensions_runner, *args, **kwargs)` and
passed through untouched.
