"""Shared fixtures for the fakeshop acceptance (live ``/graphql/``) suites.

The complete-reload discipline these suites depend on lives in the shared
``schema_reload`` module (``examples/fakeshop/schema_reload.py``, importable via
``pytest.ini``'s ``pythonpath = examples/fakeshop``) so it is single-sited across
every fakeshop suite that rebuilds the aggregate ``config.schema`` - both these
acceptance suites and the project-level ``examples/fakeshop/tests/`` modules. See that
module's docstring for why a partial reload leaves the combined build raising a
``LazyType`` ``KeyError`` or a ``DuplicatedTypeName``.

``reload_all_project_schemas`` rebuilds the full project schema by reloading every
contributing app in a dependency-safe order, so the rebuild is complete and
order-independent. A module-scoped fixture applies that discipline once per worker
receiving tests from a module. A function-scoped guard then empties the served
schema's optimizer plan cache for every test and fingerprints the complete
registration state. If a test changes any app registration or contributing module,
teardown marks the registry stale, including after an assertion failure, and the next
test that reads the project schema runs the full rebuild under ambient settings first;
the module fixture runs it on the way out if the module's last test left it stale. A
test that requests ``private_registry`` starts on an empty registry it fills with its
own types, so a stale registry is cleared for it rather than rebuilt.

``delete_after_authorization`` stands in for a concurrent transaction that deletes an
update's located row between the locate and the write: it wraps the fakeshop mutation's
``check_permission`` so the row is deleted once authorization has run, outside any
savepoint the write opens.

``record_compiled_sql`` records the read statements a request compiles where the compiler
builds them. ``CaptureQueriesContext`` watches one connection object, and the async
pipeline hands its ORM work to a ``sync_to_async`` executor thread holding a different one,
so an async suite counts statements here instead.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator

import pytest
from django.core.exceptions import EmptyResultSet
from django.db.models.sql.compiler import SQLCompiler
from graphql_client import DeleteAfterAuthorization, RecordCompiledSql, read_attr
from schema_reload import _PROJECT_APP_SCHEMA_MODULES, reload_all_project_schemas
from strawberry.types import Info

from django_strawberry_framework import DjangoMutation
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils.write_transaction import pipeline_write_phase

#: Whether a test changed this worker's registrations since the last full rebuild.
_PROJECT_SCHEMA: dict[str, bool] = {"stale": False}


def _registry_registration_identity() -> tuple[object, ...]:
    """Fingerprint every registration map plus contributing module identities."""
    return (
        registry._finalized,
        tuple(
            sorted(
                (id(model), tuple(id(type_cls) for type_cls in type_classes))
                for model, type_classes in registry._types.items()
            ),
        ),
        tuple(
            sorted((id(model), id(type_cls)) for model, type_cls in registry._primaries.items()),
        ),
        tuple(sorted((id(type_cls), id(model)) for type_cls, model in registry._models.items())),
        tuple(
            sorted(
                (id(model), field_name, id(enum_cls))
                for model, enums_by_field in registry._enums.items()
                for field_name, enum_cls in enums_by_field.items()
            ),
        ),
        tuple(
            sorted(
                (id(type_cls), id(definition))
                for type_cls, definition in registry._definitions.items()
            ),
        ),
        tuple(id(pending) for pending in registry._pending),
        tuple(id(sys.modules.get(module_name)) for module_name in _PROJECT_APP_SCHEMA_MODULES),
    )


@pytest.fixture(scope="module")
def reload_all_project_app_schemas() -> Callable[[], None]:
    """Return the :func:`schema_reload.reload_all_project_schemas` callable for an autouse fixture."""
    return reload_all_project_schemas


@pytest.fixture(scope="module", autouse=True)
def _reload_project_schema_for_acceptance_tests(
    reload_all_project_app_schemas: Callable[[], None],
) -> Iterator[None]:
    """Rebuild the full project schema once per module on every assigned worker.

    A registry the module's last test left stale is rebuilt on the way out, so the
    suites that run after this module start from the full project schema.
    """
    reload_all_project_app_schemas()
    _PROJECT_SCHEMA["stale"] = False
    yield
    if _PROJECT_SCHEMA["stale"]:
        reload_all_project_app_schemas()
        _PROJECT_SCHEMA["stale"] = False


@pytest.fixture(autouse=True)
def _isolate_project_schema_for_acceptance_test(
    request: pytest.FixtureRequest,
    _reload_project_schema_for_acceptance_tests: None,
    reload_all_project_app_schemas: Callable[[], None],
) -> Iterator[None]:
    """Start each test on the full project schema with an empty plan cache.

    A registry an earlier test left stale is rebuilt first unless this test requests
    ``private_registry``. ``config/schema.py`` serves one module-level optimizer, so
    emptying its plan cache makes every test's hit and miss counts absolute. A test
    that changes any registration leaves the registry stale for the next test.
    """
    if _PROJECT_SCHEMA["stale"] and "private_registry" not in request.fixturenames:
        reload_all_project_app_schemas()
        _PROJECT_SCHEMA["stale"] = False
    optimizer = read_attr(sys.modules["config.schema"], "_optimizer")
    assert isinstance(optimizer, DjangoOptimizerExtension), optimizer
    optimizer.cache_clear()
    registration_identity = _registry_registration_identity()
    try:
        yield
    finally:
        if _registry_registration_identity() != registration_identity:
            _PROJECT_SCHEMA["stale"] = True


@pytest.fixture
def private_registry(_isolate_project_schema_for_acceptance_test: None) -> None:
    """Start the test on an empty registry it fills with its own types.

    The test never reads the project schema, so the autouse guard clears a registry an
    earlier test left stale instead of rebuilding it, and leaves it stale afterward.
    """
    registry.clear()


@pytest.fixture
def project_schema_override(
    reload_all_project_app_schemas: Callable[[], None],
) -> Callable[[], None]:
    """Rebuild under temporary settings; the autouse state guard restores afterward."""
    return reload_all_project_app_schemas


@pytest.fixture
def delete_after_authorization(monkeypatch: pytest.MonkeyPatch) -> DeleteAfterAuthorization:
    """Return an arming callable; each armed ``check_permission`` deletes after authorizing.

    The concurrent delete is SIMULATED on the request's own connection: the wrapped
    ``check_permission`` runs the mutation's real authorization, then ``delete()`` inside
    ``pipeline_write_phase`` (the pipeline is database-read-only before its write, and the
    stand-in writer borrows the write seam), so it lands after the locate and before the
    write, outside any savepoint the write opens, and rolls back with the transaction.
    ``mutation_cls`` is read off its schema module at test time, the class the rebuilt
    schema serves. The armed classes are restored at teardown.
    """

    def arm(mutation_cls: type[DjangoMutation], delete: Callable[[], object], /) -> None:
        original = mutation_cls.check_permission

        def deleting(
            mutation: DjangoMutation,
            info: Info,
            operation: str,
            data: object,
            instance: object = None,
        ) -> bool:
            allowed = original(mutation, info, operation, data, instance)
            with pipeline_write_phase():
                _ = delete()
            return allowed

        monkeypatch.setattr(mutation_cls, "check_permission", deleting)

    return arm


def _pass_through(method: Callable[..., object]) -> Callable[..., object]:
    """``method`` as a blind forwarding target that binds none of its own overloads.

    A recorder hands its arguments on untouched, so no single overload of the
    wrapped method describes the call; seen through this signature, the call
    answers ``object`` instead of an overload the arguments cannot select.
    """
    return method


@pytest.fixture
def record_compiled_sql(monkeypatch: pytest.MonkeyPatch) -> RecordCompiledSql:
    """Return a recording callable; each call returns the list it appends statements to.

    A query Django compiles to "no rows possible" never reaches the database, so it
    is skipped rather than recorded. Only the plain SELECT compiler is read:
    compiling a write compiler a second time re-runs its pre-SQL setup, which for a
    multi-table update executes a SELECT and rewrites the query's own filter, so an
    instrument must not ask one for its SQL. The compiler is restored at teardown.
    """

    def record(table: str = "", /) -> list[str]:
        recorded: list[str] = []
        original_execute_sql = _pass_through(SQLCompiler.execute_sql)

        def _recording_execute_sql(self: SQLCompiler, *args: object, **kwargs: object) -> object:
            if type(self) is SQLCompiler:
                try:
                    sql = self.as_sql()[0]
                except EmptyResultSet:
                    sql = ""
                if sql and table in sql:
                    recorded.append(sql)
            return original_execute_sql(self, *args, **kwargs)

        monkeypatch.setattr(SQLCompiler, "execute_sql", _recording_execute_sql)
        return recorded

    return record
