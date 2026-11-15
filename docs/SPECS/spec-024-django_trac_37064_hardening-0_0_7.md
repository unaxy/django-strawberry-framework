# Spec: Django Trac #37064 and [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method]

Target release: `0.0.7` (per the [`KANBAN.md`][kanban] card `DONE-024-0.0.7`).
Status: shipped (`0.0.7`, 2026-05-27); archived. Each Decision's derivation and rejected alternatives live in [`spec-024-django_trac_37064_hardening-0_0_7-rationale.md`][spec-024-rationale].
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entry [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method]); [`KANBAN.md`][kanban] card `DONE-024-0.0.7`; sibling card spec [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (the multi-database cooperation contract whose consumers this bug reaches); joint-cut policy [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] ([Decision 10][spec-020-decision-10--joint-007-cut], reused in [Decision 4](#decision-4--joint-007-cut) here).

## Key glossary references

Skim this [`docs/GLOSSARY.md`][glossary] entry first — it anchors the vocabulary used throughout the spec:

- [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method] — the consumer-facing helper that declines to clobber Django's `_DatabaseFailure` wrapper.

It is this spec's project-specific term; the companion [`docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-terms.csv`][spec-024-terms] binds it to the `docs/GLOSSARY.md` heading above, and `scripts/check_spec_glossary.py` validates that this spec links the anchor.

Project conventions to follow:

- [`AGENTS.md`][agents] — #"Test placement:" (package tests live under `tests/`; live HTTP tests under `examples/fakeshop/test_query/`); #"Test through real usage, prefer the example project" (with the unreachable-from-a-query fallback this card takes, see [Decision 3](#decision-3--coverage-lives-in-the-package-test-tree)); #"Source refs in docs and code comments use symbol paths never line numbers".
- [`KANBAN.md`][kanban] — card-ID format and the `DONE-024-0.0.7` card body.
- [`docs/TREE.md`][tree] — rendered from module docstrings; the summary lines of this card's two surface modules are inputs to it — `django_strawberry_framework/testing/_wrap.py` and `tests/testing/test_wrap.py` — so a docstring edit to either is followed by a regenerate.

## Slice checklist

Boxes are left unticked; the `Status:` line above is the source of truth for what shipped.

- [ ] Slice 1: the helper — `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`, exported from `django_strawberry_framework.testing`, with `tests/testing/test_wrap.py` ([Decision 1](#decision-1--the-helper-declines-to-clobber-djangos-wrapper), [Decision 2](#decision-2--the-helper-is-a-submodule-export-only)).
- [ ] Slice 2: doc updates — the [`docs/GLOSSARY.md`][glossary] entry plus the `Public exports` line for the `testing` subpackage; the [`KANBAN.md`][kanban] `DONE-024-0.0.7` card; the [`CHANGELOG.md`][changelog] entry for `0.0.7` ([Doc updates](#doc-updates)).

## Problem statement

`django.test.testcases.SimpleTestCase._add_databases_failures` wraps every "disallowed" connection method on every non-permitted alias in a private `_DatabaseFailure` object at `setUpClass`. Its symmetric partner `_remove_databases_failures` unwraps them at `tearDownClass` by reading `method.wrapped` **unconditionally**.

If anything replaces `connection.<method>` between the two hooks — a consumer `setUp`, debug middleware, an instrumentation library, a mock — the attribute is no longer a `_DatabaseFailure` and teardown raises:

```
AttributeError: 'function' object has no attribute 'wrapped'
```

The test body itself passes; the crash is at class teardown and is unrecoverable. Django closed the ticket <https://code.djangoproject.com/ticket/37064> as `wontfix`, on the position that a third party which replaces Django's wrapper is responsible for restoring it. The package takes Django's position: it ships a cooperative wrap helper and leaves Django's teardown as Django ships it.

## Current state

`django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` is exported from `django_strawberry_framework.testing`. Neither upstream integration library ships a cooperative connection-wrap helper.

## Goals

1. Well-behaved wrap sites have a cooperative helper that declines to clobber Django's wrapper in the first place, so Django's own teardown finds the wrapper it installed.

## Non-goals

1. Restoration on the consumer's behalf. `safe_wrap_connection_method` handles the wrap step only.
2. Changing Django's teardown. A wrapper installed some other way and left in place crashes Django's `tearDownClass` exactly as it does without the package.
3. Upstreaming. Already attempted and closed `wontfix`.
4. Any consumer-facing pytest plugin or multi-database test-case base class.

## Borrowing posture

### From `strawberry-django` — no precedent to borrow

It ships no cooperative connection-wrap helper.

### From `graphene-django` — no precedent to borrow

Same.

### Borrowed from `django-debug-toolbar`

- **The wrap-time `isinstance` check.** `debug_toolbar.panels.sql.tracking.wrap_cursor` refuses to install its cursor wrapper when it finds a `_DatabaseFailure` already in place. `safe_wrap_connection_method` is the same check exposed as a consumer API.

### Explicitly do not borrow

Widening `TransactionTestCase.databases` / `TestCase.databases` to `"__all__"` in a repo-root `conftest.py`. That suppresses the wrapping rather than cooperating with it, and it is project-local boilerplate every consumer would have to copy.

## User-facing API

One public symbol, at the `django_strawberry_framework.testing` submodule path:

```python
def safe_wrap_connection_method(
    connection: BaseDatabaseWrapper,
    method_name: str,
    wrapper: Callable[..., object],
) -> bool: ...
```

Worked consumer shape, from the helper's own docstring:

```python
from django.db import connections
from django.test import TransactionTestCase
from django_strawberry_framework.testing import safe_wrap_connection_method


class _MyTest(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self._connection = connections["default"]
        self._original_cursor = self._connection.cursor

        def my_wrapped_cursor(*args, **kwargs):
            return self._original_cursor(*args, **kwargs)

        self._wrapped = safe_wrap_connection_method(
            self._connection, "cursor", my_wrapped_cursor,
        )

    def tearDown(self):
        if self._wrapped:
            self._connection.cursor = self._original_cursor
        super().tearDown()
```

### Error shapes

- `TypeError` — `safe_wrap_connection_method` received a non-callable `wrapper`. The message names the function and the condition and does **not** interpolate the object ([Decision 1](#decision-1--the-helper-declines-to-clobber-djangos-wrapper)).
- `AttributeError` — `method_name` names no attribute on `connection`.

## Architectural decisions

### Decision 1 — The helper declines to clobber Django's wrapper

`safe_wrap_connection_method(connection, method_name, wrapper)` returns `True` when it installed `wrapper`, and `False` when Django's `_DatabaseFailure` was already at the named attribute and the wrap was declined (the connection method is left untouched). The check is an `isinstance` against `django.test.testcases._DatabaseFailure`, the same private class `django-debug-toolbar` checks. Any callable is accepted, including an instance with `__call__`. It raises `TypeError` when `wrapper` is not callable — validated at the wrap site so a typo (passing `connection.cursor()`, the cursor object, instead of a callable) surfaces there rather than as a delayed failure deep in Django's ORM machinery. The `TypeError` message does **not** interpolate `wrapper`: the object is consumer-supplied and a hostile or broken `__repr__` would replace the intended `TypeError` with whatever the repr raises.

Restoration is the consumer's. The helper handles the wrap step only; the docstring carries the worked `setUp` / `tearDown` shape. A wrapper the helper installed and the consumer never restored crashes Django's teardown (Trac #37064); restoring also leaves a clean slot for the next `setUpClass` and for other libraries' wrap-time checks.

Pinned by `tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure`, `…::test_safe_wrap_connection_method_declines_when_database_failure_in_place`, `…::test_safe_wrap_connection_method_works_on_arbitrary_method_names`, `…::test_safe_wrap_connection_method_leaves_djangos_teardown_a_clean_unwrap`, `…::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`, `…::test_safe_wrap_connection_method_keeps_type_error_boundary_for_hostile_repr`, `…::test_safe_wrap_connection_method_accepts_callable_class_instance`, and `…::test_safe_wrap_connection_method_raises_attribute_error_on_missing_method`.

Rationale companion — the rejected restoration-on-behalf and interpolated-message alternatives: [Decision 1][rationale-d1].

### Decision 2 — The helper is a submodule export only

`safe_wrap_connection_method` is exported from `django_strawberry_framework/testing/__init__.py` and is reachable at `django_strawberry_framework.testing`. It is **not** re-exported from the package root, and **no symbol from this card is in `django_strawberry_framework/__init__.py #"__all__ = ("`**.

The public path is `django_strawberry_framework.testing`, never `django_strawberry_framework.test`: a `test` subpackage shadows the stdlib name and collides with test-collection tooling. The package's own coverage for the helper lives at `tests/testing/test_wrap.py`.

Rationale companion — why a public surface is correct for this card, and the rejected root re-export and `test` name: [Decision 2][rationale-d2].

### Decision 3 — Coverage lives in the package test tree

All coverage sits in `tests/testing/test_wrap.py`, and none in `examples/fakeshop/test_query/`.

That is the [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" fallback, taken deliberately: the helper acts on Django test-class setup/teardown state and is **not reachable through a live `/graphql/` query**.

No `FAKESHOP_SHARDED=1` gate: the helper works on any alias, so the tests run under the default single-database invocation.

Rationale companion — the rejected live-tier placement: [Decision 3][rationale-d3].

### Decision 4 — Joint `0.0.7` cut

The card ships in the joint `0.0.7` cut alongside its six siblings, under the policy [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut] establishes. No separate `0.0.8` cut for this card.

Rationale companion — the rejected `0.0.8` alternative: [Decision 4][rationale-d4].

## Implementation plan

1. `django_strawberry_framework/testing/_wrap.py` — `safe_wrap_connection_method`; re-exported from `django_strawberry_framework/testing/__init__.py`.
2. `tests/testing/test_wrap.py` — see [Test plan](#test-plan).

## Edge cases and constraints

- **`connections[…]` state is mutated by the tests and restored.** The suite assigns `connections["default"].cursor` and the other disallowed methods, restoring in `try/finally` or through `monkeypatch`. The sentinel technique is the load-bearing part: `_DatabaseFailure(mock.sentinel.…)` stands in for Django's own wrapper.
- **`docs/TREE.md` is a downstream consumer** of the module summary lines of `django_strawberry_framework/testing/_wrap.py` and `tests/testing/test_wrap.py`. A docstring edit to either is followed by a regenerate.

## Test plan

**This card owns 8 tests**, all of `tests/testing/test_wrap.py`, under the default single-database invocation: the four contract clauses of [Decision 1](#decision-1--the-helper-declines-to-clobber-djangos-wrapper) — install into a free slot, decline on a `_DatabaseFailure`, work on an arbitrary method name, and leave Django's own teardown a clean unwrap after declining — plus the two guarding the `TypeError` boundary (`…_raises_on_non_callable_wrapper`, `…_keeps_type_error_boundary_for_hostile_repr`), a callable class instance accepted as `wrapper` (`…_accepts_callable_class_instance`), and a missing `method_name` raising `AttributeError` (`…_raises_attribute_error_on_missing_method`).

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — the [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method] entry, plus the `Public exports` line for the `django_strawberry_framework.testing` subpackage.
- [`KANBAN.md`][kanban] — the `DONE-024-0.0.7` card, with this spec as its `SpecDoc` target.
- [`CHANGELOG.md`][changelog] — an entry under the `0.0.7` heading.
- [`docs/TREE.md`][tree] — regenerated whenever either surface module's summary line changes.

## Risks and open questions

- **The helper is advisory.** The package cannot force third-party wrappers to use it; a wrapper installed another way and left in place crashes Django's teardown, which is Django's documented `wontfix` position.
- **A private class.** `_DatabaseFailure` is Django-private; a Django that renames it fails the `django_strawberry_framework.testing` import loudly rather than silently installing over Django's wrapper.

## Out of scope (explicitly tracked elsewhere)

- A consumer-facing pytest plugin or multi-database test-case base class. The `django_strawberry_framework.testing` subpackage's test-client family and Relay helpers belong to other cards.
- Upstreaming a fix.

## Definition of done

1. `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` ships with the documented return contract and the non-interpolating `TypeError`; it is exported from `django_strawberry_framework.testing`.
2. `django_strawberry_framework/__init__.py`'s `__all__` is unchanged by this card; no symbol from this work is re-exported from the package root.
3. This card's 8 tests — all of `tests/testing/test_wrap.py` — are green under the default invocation, under `FAKESHOP_SHARDED=1`, and at the supported floor.
4. `uv run ruff format --check .` and `uv run ruff check .` both pass.
5. Docs updated per [Doc updates](#doc-updates); card `DONE-024-0.0.7` in `Done` at the joint `0.0.7` cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-safe-wrap-connection-method]: ../GLOSSARY.md#safe_wrap_connection_method
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-d1]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-1--the-helper-declines-to-clobber-djangos-wrapper
[rationale-d2]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-2--the-helper-is-a-submodule-export-only
[rationale-d3]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-3--coverage-lives-in-the-package-test-tree
[rationale-d4]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-4--joint-007-cut
[spec-020]: spec-020-list_field-0_0_7.md
[spec-020-decision-10--joint-007-cut]: spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-023]: spec-023-multi_db-0_0_7.md
[spec-024-rationale]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md
[spec-024-terms]: appx/spec-024-django_trac_37064_hardening-0_0_7-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
