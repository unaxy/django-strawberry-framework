"""Guard the one ORM compilation a uniqueness check actually performs.

``guard_query`` follows one query through Django's own lookup construction and
compilation, refusing a value the database cannot bind under the source it was written
for. A DRF uniqueness validator's queryset carries it on the serializer flavor
(``rest_framework/validator_guard.py::guard_uniqueness_validator``); a model's
``unique_for_date`` / ``unique_for_year`` date checks carry it on the model and
``ModelForm`` flavors (``date_checks_guarded``).
"""

from __future__ import annotations

import ast
import functools
import hashlib
import inspect
import textwrap
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.core.exceptions import EmptyResultSet, FullResultSet, ValidationError
from django.db import connections, models
from django.db.models.sql.where import WhereNode

from django_strawberry_framework._completion import _syntax_shape
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._array_field import array_leaf_field
from django_strawberry_framework.utils._narrowing import (
    call_method,
    dict_items,
    is_dict,
    is_list,
    is_list_or_tuple,
    is_lookup,
    is_str,
    is_tuple,
    list_iter,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_INVALID,
    UNBOUNDED_YEAR_IN_ZONE_MESSAGE,
    _binds_client_side,
    binds_integer,
    refuses_integer_range,
    refuses_numeric_format,
    refuses_utc_offset,
)
from django_strawberry_framework.utils.relations import is_model_class
from django_strawberry_framework.utils.typing import object_result

if TYPE_CHECKING:
    from collections.abc import Callable, Container, Generator, Mapping

    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.models import QuerySet
    from django.db.models.sql.query import Query
    from typing_extensions import TypeIs

    from django_strawberry_framework.utils.typing import ConcreteField

_SQL_PAIR_LENGTH = 2


def guard_query(
    query: Query,
    *,
    alias: str,
    sources: Mapping[str, str],
    refusal: Callable[[str | None], Exception],
    provenance: list[tuple[object, object, str | None, str]],
) -> Query:
    """Install a per-query guard that follows Django ``Query.clone`` and compilation.

    ``Query.build_filter`` is the actual lookup-construction seam and receives the
    source spelling. ``Query.get_compiler`` is the actual evaluation seam. Its
    compiler's ``compile`` returns each lookup's prepared parameters during the
    original evaluation. A native ``EmptyResultSet`` or ``FullResultSet`` drops
    the compiled subtree's provenance with its parameters. Only parameter objects
    retained in the outer ``as_sql`` result are checked, never merely equal values.
    ``refusal`` builds the error raised for a refused source name. An
    ``OverflowError`` of a lookup no source names is the query's own and propagates.
    The guard never changes a global model field, lookup, compiler class, or connection.
    """
    query_type = type(query)

    def _source_name(expression: object) -> str | None:
        if not (is_tuple(expression) and expression and isinstance(expression[0], str)):
            return None
        key = expression[0]
        return next(
            (
                name
                for name, source in sorted(sources.items(), key=lambda item: -len(item[1]))
                if key == source or key.startswith(f"{source}__")
            ),
            None,
        )

    def _mark(node: object, name: str | None) -> None:
        if name is None:
            return
        if is_lookup(node):
            object.__setattr__(node, "_dsf_validator_field", name)
        elif isinstance(node, WhereNode):
            for child in node.children:
                _mark(child, name)

    def _build_filter(self: Query, expression: object, *args: object, **kwargs: object) -> object:
        name = _source_name(expression)
        try:
            result = object_result(query_type.build_filter, self, expression, *args, **kwargs)
        except OverflowError as exc:
            if name is None:
                raise
            raise refusal(name) from exc
        if is_tuple(result) and result:
            _mark(result[0], name)
        return result

    def _get_compiler(self: Query, *args: object, **kwargs: object) -> object:
        compiler = object_result(
            query_type.get_compiler,
            self,
            *args,
            **kwargs,
        )
        compiler_type = type(compiler)

        def _compile(self: object, node: object, *args: object, **kwargs: object) -> object:
            name = read_attr(node, "_dsf_validator_field", None)
            start = len(provenance)
            try:
                result = object_result(
                    require(read_attr(compiler_type, "compile"), callable),
                    self,
                    node,
                    *args,
                    **kwargs,
                )
            except (EmptyResultSet, FullResultSet):
                # Django discarded this compiled subtree, including every child
                # parameter it collected before deciding the result-set outcome.
                del provenance[start:]
                raise
            except OverflowError as exc:
                if not is_lookup(node) or not isinstance(name, str):
                    raise
                raise refusal(name) from exc
            if is_lookup(node) and is_tuple(result) and len(result) == _SQL_PAIR_LENGTH:
                params = result[1]
                if is_list_or_tuple(params):
                    lookup_sql = result[0] if isinstance(result[0], str) else ""
                    provenance.extend(
                        (
                            param,
                            read_attr(read_attr(node, "lhs"), "output_field"),
                            name if isinstance(name, str) else None,
                            lookup_sql,
                        )
                        for param in params
                    )
            return result

        def _as_sql(self: object, *args: object, **kwargs: object) -> object:
            # A nested Exists query contributes parameters to its outer Q.check query.
            # Its own result is not executed independently.
            query_node = read_attr(self, "query")
            subquery = bool(read_attr(query_node, "subquery", False))
            if not subquery:
                provenance.clear()
            result = object_result(
                require(read_attr(compiler_type, "as_sql"), callable),
                self,
                *args,
                **kwargs,
            )
            if subquery or not (is_tuple(result) and len(result) == _SQL_PAIR_LENGTH):
                return result
            # Every Django compiler's ``as_sql`` returns its parameters as a tuple or list.
            final_params = require(result[1], is_list_or_tuple)
            connection = connections[alias]
            for param, field, name, lookup_sql in provenance:
                if any(param is final for final in final_params) and _refused_params(
                    connection,
                    field,
                    (param,),
                    lookup_sql=lookup_sql,
                ):
                    raise refusal(name)
            return result

        guarded_compiler_type = type(
            f"_Guarded{truth.name(compiler_type)}",
            (compiler_type,),
            {"compile": _compile, "as_sql": _as_sql},
        )
        compiler.__class__ = guarded_compiler_type  # truth: ok per-instance compiler subtype
        return compiler

    guarded_query_type = type(
        f"_Guarded{truth.name(query_type)}",
        (query_type,),
        {"build_filter": _build_filter, "get_compiler": _get_compiler},
    )
    query.__class__ = guarded_query_type  # truth: ok instance-local query guard subtype
    return query


def _refused_params(
    connection: BaseDatabaseWrapper,
    field: object,
    params: list[object] | tuple[object, ...],
    *,
    lookup_sql: str,
) -> bool:
    """Inspect only bindings that cannot recover through DRF's original query call.

    The field's storage bounds are not the range of a query parameter. SQLite's
    driver binds signed 64-bit Python integers irrespective of a positive column;
    MySQL and PostgreSQL client cursors send numeric literals. PostgreSQL's
    explicit array cast, and its typed server-side integer parameter, instead
    have the signed width of the SQL type Django reports for the field.
    """
    element, depth = array_leaf_field(field)
    sqlite_integer: ConcreteField = models.BigIntegerField()
    return (
        (
            connection.vendor == "sqlite"
            and any(
                isinstance(param, int)
                and not isinstance(param, bool)
                and not binds_integer(connection, sqlite_integer, param)
                for param in params
            )
        )
        or (
            connection.vendor == "postgresql"
            and depth > 0
            and isinstance(element, models.IntegerField)
            and isinstance(field, models.Field)
            and (
                (
                    f"::{field.cast_db_type(connection)}" in lookup_sql
                    and _signed_cast_refuses(connection, element, params)
                )
                or any(_driver_array_cast_refuses(connection, param) for param in params)
            )
        )
        or (
            connection.vendor == "postgresql"
            and depth == 0
            and not _binds_client_side(connection)
            and _typed_scalar_refuses(connection, params)
        )
        or refuses_utc_offset(connection, params)
        or refuses_numeric_format(connection, params)
    )


def _signed_integer_fields() -> tuple[ConcreteField, ...]:
    """Django's signed integer fields, narrowest first: ``smallint``, ``integer``, ``bigint``."""
    return (models.SmallIntegerField(), models.IntegerField(), models.BigIntegerField())


def _signed_cast_refuses(
    connection: BaseDatabaseWrapper,
    element: ConcreteField,
    params: list[object] | tuple[object, ...],
) -> bool:
    """Hold ``params`` to the signed SQL type an array of ``element`` is cast to, not its column checks.

    An element type whose cast no signed integer field shares (a custom ``db_type``)
    states no signed width and holds nothing.
    """
    cast_type = element.cast_db_type(connection)
    return any(
        signed.cast_db_type(connection) == cast_type
        and refuses_integer_range(connection, signed, params)
        for signed in _signed_integer_fields()
    )


def _typed_scalar_refuses(
    connection: BaseDatabaseWrapper,
    params: list[object] | tuple[object, ...],
) -> bool:
    """Hold only params Django actually wrapped as a SQL integer type, to that type's width.

    PostgreSQL's operations wrap each value an integer field prepares in the psycopg type
    of the field's width (``integerfield_type_map``); bound on the server, the wrapper is
    that SQL type whatever the lookup's column. A custom lookup can return a plain ``int``
    against an integer LHS. Psycopg chooses that parameter's own integer/numeric width;
    the LHS does not cap it.
    """
    # Server binding is psycopg 3's, whose operations always carry the map.
    wrappers = require(read_attr(connection.ops, "integerfield_type_map"), is_dict)
    widths = {
        wrappers.get(signed.get_internal_type()): signed for signed in _signed_integer_fields()
    }
    return any(
        (signed := widths.get(type(param))) is not None
        and refuses_integer_range(connection, signed, (param,))
        for param in params
    )


def _driver_array_cast_refuses(connection: BaseDatabaseWrapper, param: object) -> bool:
    """Read psycopg's selected array OID without dumping the list parameter.

    Psycopg's client cursor appends the selected ``::type[]`` to its literal;
    server binding transmits that array OID. Only a list parameter carries one, and
    psycopg 2, which has no ``adapt.Transformer``, selects none. A dumper selection
    DataError is left to DRF's original ``qs_exists`` recovery path.
    """
    if not is_list(param):
        return False
    driver = read_attr(connection, "Database")
    adapt = read_attr(driver, "adapt", None)
    transformer_type = read_attr(adapt, "Transformer", None)
    if not isinstance(transformer_type, type):
        return False
    data_error = require(read_attr(driver, "DataError"), _is_exception_class)
    raw_connection = read_attr(connection, "connection")
    adapters = read_attr(driver if raw_connection is None else raw_connection, "adapters")
    try:
        transformer = object_result(transformer_type, adapters)
        dumper = call_method(
            transformer,
            "get_dumper",
            param,
            read_attr(read_attr(adapt, "PyFormat"), "TEXT"),
        )
    except data_error:
        return False
    oid = read_attr(dumper, "oid")
    types = read_attr(adapters, "types")
    for signed in _signed_integer_fields():
        info = call_method(types, "get", signed.cast_db_type(connection))
        if oid == read_attr(info, "array_oid"):
            return refuses_integer_range(connection, signed, (param,))
    return False


def _is_exception_class(value: object) -> TypeIs[type[Exception]]:
    """Whether ``value`` is an ``Exception`` class, as a DB-API driver's ``DataError`` is."""
    return isinstance(value, type) and issubclass(value, Exception)


#: The ``Model`` method ``validate_unique()`` runs the date checks through.
_DATE_CHECKS = "_perform_date_checks"

# ``date_checks_guarded`` depends on WHICH ``Model._perform_date_checks`` body runs: it hands
# each check a stand-in model whose only attribute is ``_default_manager.filter``, the one
# read every audited body makes of ``model_class``. The audited bodies, by the sha256 of their
# docstring-free syntax (``_completion.py::_syntax_shape``), and the releases carrying them:
#
# ======================================  ==================================================
# Django release                          ``_perform_date_checks`` body (comments may differ)
# ======================================  ==================================================
# 5.2.16, 5.2.19, 6.0.10, 6.1.2, 6.1.3    one body: ``ebf8e5b4...``, the row excluded on
#                                         ``self._is_pk_set()``
# ======================================  ==================================================
#
# Any other body (an unseen release, a model's own override, a body without source) is not
# shadowed: Django runs it unguarded.
_AUDITED_DATE_CHECKS = frozenset(
    {
        "ebf8e5b472064be054dd7b4dc8e59ddc6ee975945b3f4467176b9fe901190f00",
    },
)


class _YearUnboundedError(Exception):
    """A date check's year bound the current time zone cannot represent; never surfaced."""


@contextmanager
def date_checks_guarded(
    instance: models.Model,
    *,
    provided: Container[str],
    alias: str,
    answer: Callable[[str, ValidationError], Mapping[str, list[ValidationError]]],
) -> Generator[None]:
    """Run each ``unique_for_date`` / ``unique_for_year`` date check of ``instance`` guarded.

    For the length of the block ``Model._perform_date_checks`` (the method
    ``validate_unique()`` runs a model's date checks through) is shadowed on ``instance``
    when the body ``instance``'s class resolves is one ``_AUDITED_DATE_CHECKS`` holds;
    any other body is left to run unguarded. Django calls the shadow once with every
    check (``validate_unique()`` with none still calls it with an empty list); the shadow
    calls the original once per check, with that one check, its model's default manager
    handing Django's own body a queryset whose query carries ``guard_query`` with the
    check's date field as its one source. Django bounds a ``__year`` lookup's year in the
    current time zone (``timezone.activate`` decides, not ``TIME_ZONE``) and projects each
    bound onto the connection's time zone, where year 9999 west of UTC, or year 1 east of
    it, overflows: that refusal, and only one compiling a lookup on the date field, is the
    check's ``invalid``
    ``UNBOUNDED_YEAR_IN_ZONE_MESSAGE`` error, keyed to the date field when ``provided``
    names it, else to the field the check validates. ``answer`` takes that key and error
    and returns the errors the check reports (the model flavor reports it, the
    ``ModelForm`` flavor adds it to the form itself); a key refused once is answered once.
    Any other error, a ``unique_for_month`` check's included, is Django's own, and the
    other checks still run; a parameter the guard refuses on another lookup (the validated
    value, the row's own ``pk`` exclude, a manager's filter) is an ``OverflowError``, the
    query's own error. The shadow is removed after the block.
    """
    if _date_checks_digest(read_attr(type(instance), _DATE_CHECKS)) not in _AUDITED_DATE_CHECKS:
        yield
        return
    namespace = truth.instance_state(instance)
    perform = require(read_attr(instance, _DATE_CHECKS), callable)

    def checked(date_checks: object) -> dict[str, list[ValidationError]]:
        errors: dict[str, list[ValidationError]] = {}
        refused: set[str] = set()
        for check in list_iter(require(date_checks, is_list)):
            model_class, lookup_type, field, unique_for = require(check, is_tuple)
            date_field = require(unique_for, is_str)
            key = date_field if date_field in provided else require(field, is_str)
            guarded = _GuardedDateCheck(
                require(model_class, is_model_class),
                alias=alias,
                sources={key: date_field},
            )
            try:
                found = require(
                    object_result(
                        perform,
                        [
                            (
                                guarded,
                                lookup_type,
                                field,
                                unique_for,
                            ),
                        ],
                    ),
                    is_dict,
                )
            except _YearUnboundedError:
                if key not in refused:
                    refused.add(key)
                    error = ValidationError(
                        UNBOUNDED_YEAR_IN_ZONE_MESSAGE,
                        code=FIELD_ERROR_CODE_INVALID,
                    )
                    for name, messages in answer(key, error).items():
                        errors.setdefault(name, []).extend(messages)
                continue
            for name, messages in dict_items(found):
                errors.setdefault(require(name, is_str), []).extend(
                    require_instance(message, ValidationError)
                    for message in list_iter(require(messages, is_list))
                )
        return errors

    namespace[_DATE_CHECKS] = checked
    try:
        yield
    finally:
        del namespace[_DATE_CHECKS]


class _GuardedDateCheck:
    """One date check's model as ``Model._perform_date_checks`` reads it: its default manager.

    Django's body reads only ``model_class._default_manager.filter(**lookup_kwargs)``;
    the queryset returned is the manager's own (its ``get_queryset`` rows), its query
    carrying ``guard_query`` before Django adds the check's lookups, so the guard sees
    each lookup's construction and compilation.
    """

    def __init__(
        self,
        model_class: type[models.Model],
        *,
        alias: str,
        sources: Mapping[str, str],
    ) -> None:
        self.model_class: type[models.Model] = model_class
        self.alias: str = alias
        self.sources: Mapping[str, str] = sources
        # The stand-in is its own default manager: its ``filter`` is the manager's.
        self._default_manager: _GuardedDateCheck = self

    def filter(self, *args: object, **kwargs: object) -> QuerySet[models.Model]:
        """Return the default manager's ``filter(*args, **kwargs)``, its query guarded."""
        queryset = self.model_class._default_manager.all()
        _ = guard_query(
            queryset.query,
            alias=self.alias,
            sources=self.sources,
            refusal=_date_check_refusal,
            provenance=[],
        )
        return queryset.filter(*args, **kwargs)


def _date_check_refusal(name: str | None) -> Exception:
    """Refuse a date check's parameter: a year bound on its date field, else the query's own."""
    if name is None:
        return OverflowError("the database cannot bind a parameter of a date check's query")
    return _YearUnboundedError()


@functools.cache
def _date_checks_digest(method: object) -> str | None:
    """Hash ``method``'s docstring-free syntax (sha256); ``None`` when it has no source.

    Cached per function object, so each body is read and hashed once per process.
    """
    try:
        source = textwrap.dedent(inspect.getsource(require(method, inspect.isfunction)))
    except (OSError, TypeError):
        return None
    return _date_checks_source_digest(source)


def _date_checks_source_digest(source: str) -> str:
    """Hash the docstring-free syntax (sha256) of the one function ``source`` defines."""
    function = ast.parse(source).body[0]
    for node in ast.walk(function):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and ast.get_docstring(node) is not None
        ):
            del node.body[0]
    return hashlib.sha256(repr(_syntax_shape(function)).encode()).hexdigest()
