"""The PostgreSQL integer bind rules a DRF uniqueness validator's guarded query applies.

System-under-test is ``rest_framework/query_bind.py``, only the residue a SQLite run of
the live tier cannot reach: the rules that read PostgreSQL's binding (real-server rows,
marked ``pg``, are in ``examples/fakeshop/test_query/test_serializer_validator_bind_api.py``).
An alias that reads as PostgreSQL (``tests/_postgresql_stand_in.py``) carries each
binding mode; its operations wrap each integer an integer field prepares in its width's
type and read Django's default (PostgreSQL's) integer ranges, as psycopg 3's do, and
its column types are PostgreSQL's for the positive integer fields.

- a typed server-bound scalar held to its wrapper's signed width, through the guard's
  own compilation of a validator-shaped query: refused under its source name, a fitting
  value, a raw ``int`` a custom lookup binds and a client-bound literal kept;
- an ``ArrayField`` (the ``FakeArrayField`` double) of integers: an explicit
  ``::type[]`` cast held to the signed type of the element's cast (a positive element's
  ``-1`` kept, a custom element type holding nothing), and a list parameter held to the
  array type psycopg's dumper selects (a ``numeric[]``, a dump ``DataError`` and psycopg 2
  holding nothing, and a scalar never offered to the dumper).
"""

from __future__ import annotations

from contextlib import contextmanager
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, ClassVar

import pytest
from apps.scalars.models import OverrideSpecimen, ScalarSpecimen
from django.db import connections, models
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.models.lookups import BuiltinLookup
from django.test.utils import register_lookup
from typing_extensions import override

from django_strawberry_framework.rest_framework.query_bind import _refused_params, guard_query
from django_strawberry_framework.utils._narrowing import call_method, is_list
from django_strawberry_framework.utils.typing import object_result
from tests._postgres_fields import FakeArrayField, patch_array_field
from tests._postgresql_stand_in import BINDING_MODES, StoringOperations, postgresql_stand_in

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.models.query import QuerySet


class _Int2(int):
    """psycopg 3's ``Int2``: an integer bound as ``smallint``."""


class _Int4(int):
    """psycopg 3's ``Int4``: an integer bound as ``integer``."""


class _Int8(int):
    """psycopg 3's ``Int8``: an integer bound as ``bigint``."""


class _IntegerWrappingOperations(StoringOperations):
    """psycopg 3's PostgreSQL operations' integer handling over the stand-in's own.

    Adapted from Django ``django/db/backends/postgresql/operations.py`` (BSD):
    ``integerfield_type_map`` and ``adapt_integerfield_value`` wrap each integer value in
    the type of its field's width; the ranges are Django's defaults, PostgreSQL's.
    """

    integerfield_type_map: ClassVar[dict[str, type[int]]] = {
        "SmallIntegerField": _Int2,
        "IntegerField": _Int4,
        "BigIntegerField": _Int8,
        "PositiveSmallIntegerField": _Int2,
        "PositiveIntegerField": _Int4,
        "PositiveBigIntegerField": _Int8,
    }

    @override
    def adapt_integerfield_value(self, value: object, internal_type: str) -> object:
        if not isinstance(value, int):
            return value
        return self.integerfield_type_map[internal_type](value)

    @override
    def integer_field_range(self, internal_type: str) -> tuple[int, int]:
        return BaseDatabaseOperations.integer_field_range(self, internal_type)


#: PostgreSQL's column types for the positive integer fields (SQLite spells them unsigned).
_POSITIVE_TYPES = {
    "PositiveSmallIntegerField": "smallint",
    "PositiveIntegerField": "integer",
    "PositiveBigIntegerField": "bigint",
}


@contextmanager
def _postgresql(
    mode: str,
    driver: ModuleType | None = None,
) -> Generator[BaseDatabaseWrapper, None, None]:
    """The stand-in PostgreSQL alias in binding ``mode``, on ``driver`` if one is given."""
    mode_driver, cursor_factory, _ = BINDING_MODES[mode]
    with postgresql_stand_in(driver or mode_driver, cursor_factory) as alias:
        connection = connections[alias]
        connection.ops = _IntegerWrappingOperations(connection)
        connection.data_types = {**connection.data_types, **_POSITIVE_TYPES}
        yield connection


class _RefusedError(Exception):
    """The refusal a guarded query raises, carrying the source name it was built for."""

    def __init__(self, name: str | None) -> None:
        super().__init__(name)
        self.name = name


class _RawEquals(BuiltinLookup[object]):
    """A consumer lookup binding its right-hand side as the plain value, unprepared."""

    lookup_name = "raw_equals"

    @override
    def get_rhs_op(self, connection: BaseDatabaseWrapper, rhs: str) -> str:
        return f"= {rhs}"


@pytest.fixture
def _raw_equals_on_integers() -> Generator[None, None, None]:
    """``_RawEquals`` registered on every ``IntegerField`` for the test only."""
    with register_lookup(models.IntegerField, _RawEquals):
        yield


def _compiled(queryset: QuerySet[models.Model], alias: str) -> object:
    """The SQL and parameters ``queryset``'s compiler on ``alias`` produces."""
    return call_method(object_result(queryset.query.get_compiler, using=alias), "as_sql")


def _quantity_raw_equals(queryset: QuerySet[OverrideSpecimen]) -> QuerySet[OverrideSpecimen]:
    return queryset.filter(quantity__raw_equals=2**35)


def _quantity_in(value: int) -> Callable[[QuerySet[OverrideSpecimen]], QuerySet[OverrideSpecimen]]:
    return lambda queryset: queryset.filter(quantity__in=[value])


@pytest.mark.parametrize(
    ("mode", "narrowed", "refused"),
    [
        pytest.param("psycopg3-server", _quantity_in(2**35), True, id="typed-past-integer"),
        pytest.param("psycopg3-server", _quantity_in(2**31 - 1), False, id="typed-integer-end"),
        pytest.param(
            "psycopg3-server",
            _quantity_raw_equals,
            False,
            id="raw-int",
        ),
        pytest.param("psycopg3-client", _quantity_in(2**35), False, id="client-literal"),
    ],
)
@pytest.mark.usefixtures("_raw_equals_on_integers")
def test_server_bound_typed_integer_is_held_to_its_wrappers_width(
    mode: str,
    narrowed: Callable[[QuerySet[OverrideSpecimen]], QuerySet[OverrideSpecimen]],
    refused: bool,  # noqa: FBT001
) -> None:
    """A server-bound integer Django wrapped as ``integer`` is refused past 32 bits, under its source.

    The guard compiles the validator-shaped query on the alias: the ``in`` member an
    ``IntegerField`` prepares is wrapped as ``integer``, which the server refuses past its
    range; a plain ``int`` a custom lookup binds unprepared takes psycopg's own width, and a client
    cursor sends a literal the server compares at any width.
    """
    with _postgresql(mode) as connection:
        queryset = OverrideSpecimen.objects.all()
        _ = guard_query(
            queryset.query,
            alias=connection.alias,
            sources={"amount": "quantity"},
            refusal=_RefusedError,
            provenance=[],
        )
        if not refused:
            _ = _compiled(narrowed(queryset), connection.alias)
            return
        with pytest.raises(_RefusedError) as excinfo:
            _ = _compiled(narrowed(queryset), connection.alias)
    assert excinfo.value.name == "amount"


@pytest.mark.parametrize(
    ("value", "refused"),
    [pytest.param(2**35, False, id="fits-bigint"), pytest.param(2**63, True, id="past-bigint")],
)
def test_server_bound_bigint_is_held_to_its_own_width(value: int, refused: bool) -> None:  # noqa: FBT001
    """A ``BigIntegerField`` value is wrapped as ``bigint``, held to 64 bits, not 32."""
    with _postgresql("psycopg3-server") as connection:
        queryset = ScalarSpecimen.objects.all()
        _ = guard_query(
            queryset.query,
            alias=connection.alias,
            sources={"signed_big": "signed_big"},
            refusal=_RefusedError,
            provenance=[],
        )
        narrowed = queryset.filter(signed_big__in=[value])
        if not refused:
            _ = _compiled(narrowed, connection.alias)
            return
        with pytest.raises(_RefusedError) as excinfo:
            _ = _compiled(narrowed, connection.alias)
    assert excinfo.value.name == "signed_big"


class _CastArrayField(FakeArrayField):
    """The ``ArrayField`` double, cast as a real one: its element's cast type, then ``[]``.

    Adapted from ``django/contrib/postgres/fields/array.py::ArrayField.cast_db_type``
    (Django, BSD).
    """

    @override
    def cast_db_type(self, connection: BaseDatabaseWrapper) -> str | None:
        return f"{self.base_field.cast_db_type(connection)}[]"


class _OidField(models.IntegerField[int, int]):
    """An integer column of a type no signed integer field shares."""

    @override
    def db_type(self, connection: BaseDatabaseWrapper) -> str:
        return "oid"


class _DataError(Exception):
    """The stand-in driver's ``DataError``."""


class _Dumper:
    """A psycopg dumper: the OID it binds its value as."""

    def __init__(self, oid: int) -> None:
        self.oid = oid


#: The array OID psycopg binds a list of each integer wrapper as; plain integers past 64
#: bits, which no wrapper holds, bind as ``numeric[]``.
_ARRAY_OIDS: dict[type[object], int] = {
    _Int2: 1005,
    _Int4: 1007,
    _Int8: 1016,
    int: 1231,
}


class _Adapters:
    """psycopg's adapters map: its type registry by name, and each value a dumper was asked for."""

    def __init__(self) -> None:
        self.asked: list[object] = []
        registry = {
            "smallint": SimpleNamespace(array_oid=1005),
            "integer": SimpleNamespace(array_oid=1007),
            "bigint": SimpleNamespace(array_oid=1016),
        }
        self.types = SimpleNamespace(get=registry.get)


class _Transformer:
    """psycopg 3's ``adapt.Transformer``: a list of one wrapper type binds as that type's array.

    A list it cannot select one dumper for raises ``DataError``; a scalar binds as no array.
    """

    def __init__(self, adapters: _Adapters) -> None:
        self.adapters = adapters

    def get_dumper(self, obj: object, _format: object) -> _Dumper:
        self.adapters.asked.append(obj)
        if not is_list(obj):
            return _Dumper(0)
        kinds = {type(item) for item in obj}
        if len(kinds) != 1:
            message = "cannot dump a list of mixed types"
            raise _DataError(message)
        return _Dumper(_ARRAY_OIDS.get(kinds.pop(), 0))


def _psycopg3(adapters: _Adapters) -> ModuleType:
    """A psycopg 3 driver module whose adapters are ``adapters``."""
    driver, _, _ = BINDING_MODES["psycopg3-server"]
    module = ModuleType("psycopg_stand_in")
    vars(module).update(
        vars(driver),
        adapt=SimpleNamespace(Transformer=_Transformer, PyFormat=SimpleNamespace(TEXT="text")),
        DataError=_DataError,
        adapters=adapters,
    )
    return module


_CAST = '"c" @> ARRAY[%s]::integer[]'
_PLAIN = '"c" > %s'


@pytest.mark.parametrize(
    (
        "element",
        "params",
        "lookup_sql",
        "refused",
    ),
    [
        pytest.param(
            models.IntegerField[int, int](),
            [_Int4(2**35)],
            _CAST,
            True,
            id="cast-past-integer",
        ),
        pytest.param(models.IntegerField[int, int](), [_Int4(5)], _CAST, False, id="cast-fits"),
        pytest.param(
            models.PositiveIntegerField[int, int](),
            [_Int4(-1)],
            _CAST,
            False,
            id="cast-positive-negative",
        ),
        pytest.param(
            models.PositiveIntegerField[int, int](),
            [_Int4(2**35)],
            _CAST,
            True,
            id="cast-positive-past-integer",
        ),
        pytest.param(_OidField(), [2**70], '"c" @> ARRAY[%s]::oid[]', False, id="cast-own-type"),
        pytest.param(models.IntegerField[int, int](), [2**35], _PLAIN, False, id="scalar-uncast"),
    ],
)
def test_array_cast_holds_each_element_to_the_signed_type_of_its_cast(
    element: models.Field[int, int],
    params: list[object],
    lookup_sql: str,
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An element an explicit ``::type[]`` cast binds is held to that signed SQL type's range.

    A positive element's array is cast to ``integer[]``, so ``-1`` binds and 2**35 does
    not; a custom element type's cast states no signed width. A scalar parameter is never
    offered to the driver's dumper, which selects an array type for a list only.
    """
    patch_array_field(monkeypatch)
    adapters = _Adapters()
    with _postgresql("psycopg3-server", _psycopg3(adapters)) as connection:
        verdict = _refused_params(
            connection,
            _CastArrayField(element),
            params,
            lookup_sql=lookup_sql,
        )
    assert (verdict, adapters.asked) == (refused, [])


@pytest.mark.parametrize(
    ("member", "refused"),
    [
        pytest.param([_Int4(2**35)], True, id="integer-array-past-integer"),
        pytest.param([_Int4(5)], False, id="integer-array-fits"),
        pytest.param([_Int8(2**35)], False, id="bigint-array"),
        pytest.param([2**70], False, id="numeric-array"),
        pytest.param([_Int4(1), "1"], False, id="dump-data-error"),
    ],
)
def test_list_parameter_is_held_to_the_array_type_psycopg_selects(
    member: list[object],
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A list parameter is held to the array type psycopg's dumper selects for it.

    A list of ``integer`` wrappers binds as ``integer[]`` (refused past 32 bits), one of
    ``bigint`` wrappers as ``bigint[]``, plain integers past 64 bits as ``numeric[]``,
    which no integer width holds; a list no dumper is selected for raises
    ``DataError``, which DRF's own query call answers.
    """
    patch_array_field(monkeypatch)
    adapters = _Adapters()
    with _postgresql("psycopg3-server", _psycopg3(adapters)) as connection:
        verdict = _refused_params(
            connection,
            _CastArrayField(models.IntegerField[int, int]()),
            [member],
            lookup_sql=_PLAIN,
        )
    assert (verdict, adapters.asked) == (refused, [member])


def test_psycopg2_list_parameter_selects_no_array_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Psycopg 2 binds a list as an untyped ``ARRAY[...]``: no array width holds it."""
    patch_array_field(monkeypatch)
    with _postgresql("psycopg2") as connection:
        assert not _refused_params(
            connection,
            _CastArrayField(models.IntegerField[int, int]()),
            [[_Int4(2**35)]],
            lookup_sql=_PLAIN,
        )
