"""Tests for the shared query-source / visibility substrate (``utils/querysets.py``).

Seal, Manager coercion, and hostile QuerySet internals have no wire shape: a
request sees the filtered rows, not the sealed class identity. Consumer
visibility and list/connection cost live in
``examples/fakeshop/test_query/test_products_visibility_api.py``,
``examples/fakeshop/test_query/test_library_api.py``, and
``examples/fakeshop/test_query/test_list_field_api.py``. ``coerce_field_value_or_none``
out-of-range ``__in`` drop is live in
``examples/fakeshop/test_query/test_scalars_filter_api.py``, and its match of a
stored value the column's validator refuses in
``examples/fakeshop/test_query/test_scalars_api.py``.

Visibility-boundary decision references below resolve to
``docs/SPECS/spec-045-visibility_boundary-0_0_14.md #"## Architectural decisions"``.
"""

import asyncio
import datetime
import functools
import threading
import warnings
import zoneinfo
from collections.abc import AsyncIterator, Awaitable, Callable, Generator, Iterable
from contextlib import AbstractContextManager, contextmanager
from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING, NoReturn, TypeVar

import django
import django.db.models.query as django_query
import pytest
import pytest_django
from apps.library.models import (
    Annotation,
    Book,
    Branch,
    BranchNote,
    CirculationDesk,
    DeskShift,
    LendingDesk,
    OpenVenue,
    Patron,
    PatronProfile,
    ProxyBranch,
    SelfServeDesk,
    Shelf,
    TaggedItem,
    Venue,
    VenueBadge,
    VenueSponsor,
)
from apps.products.models import Category, Entry, Item, Property
from apps.products.services import seed_data
from apps.scalars.models import NullableScalarSpecimen, ScalarSpecimen
from asgiref.sync import sync_to_async
from django.apps import apps
from django.apps.registry import Apps
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import (
    DEFAULT_DB_ALIAS,
    DataError,
    connection,
    connections,
    models,
    router,
    transaction,
)
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.models import (
    F,
    FilteredRelation,
    ForeignObjectRel,
    Prefetch,
    Q,
    Value,
)
from django.db.models.functions import (
    Trunc,
    Upper,
)
from django.db.models.lookups import In
from django.db.models.sql import Query as SqlQuery
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.datastructures import BaseTable, Join
from django.db.models.sql.where import ExtraWhere
from django.http import HttpRequest
from django.test import override_settings
from django.test.utils import CaptureQueriesContext, isolate_apps
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from typing_extensions import Self, override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import Ordering, OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils import querysets as querysets_module
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    call_method,
    is_exact_dict,
    is_iterable,
    is_str,
    list_of,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils._queryset_private import (
    queryset_db,
    queryset_hints,
    queryset_prefetch_lookups,
    set_queryset_hints,
)
from django_strawberry_framework.utils.querysets import (
    _CASCADE_SEAL_POLICY,
    _COMBINED_WHAT,
    _DEFAULT_SEAL_POLICY,
    _LIST_RELATION_CHILD_POLICY,
    _PREFETCH_CHILD_POLICY,
    SyncMisuseError,
    _concrete_or_none,
    _defect_message,
    _normalized_visibility_result,
    _prefetch_relation_target_or_none,
    _prepared_visibility_source,
    _routing_repr,
    _seal_or_defect,
    _SealPolicy,
    _snapshot_routing_intent,
    _type_is_genuinely_django,
    _validate_post_orderset_result,
    _visibility_result_error,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    base_queryset,
    coerce_field_value_or_none,
    expand_relation_order,
    identity_key,
    initial_queryset,
    is_async_only_iterable,
    joinless_relation_on,
    linkable_rows,
    lookup_target_fields,
    normalize_query_source,
    pks_all_present,
    reject_async_in_sync_context,
    reject_async_iterable_in_sync_context,
    reject_awaitable_sync_source,
    related_queryset,
    run_in_one_sync_boundary,
    split_lookup,
    truncates_to_integer,
    visible_related_object,
    visible_related_objects,
)
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.utils.write_transaction import write_pipeline
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._idioms import (
    FETCH_MODES,
    STR_ENUM,
    TEST_ASYNC_RECOURSE,
    ClaimsClassBase,
    ClassReadRaisesBase,
    requires_fetch_modes,
    saved_pk,
)
from tests._postgresql_stand_in import BINDING_MODES, postgresql_stand_in

if TYPE_CHECKING:
    from typing import TypeAlias

    from django.db.models.expressions import Combinable

    # The field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _AwareStamp: TypeAlias = models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ]

_M = TypeVar("_M", bound=models.Model)


def _rows_of(model: type[_M], rows: Iterable[object]) -> list[_M]:
    """Materialize ``rows``, proving each is a ``model`` instance."""
    proven: list[_M] = []
    for row in rows:
        assert isinstance(row, model)
        proven.append(row)
    return proven


def _compiled_sql(query: SqlQuery) -> tuple[str, tuple[str | int, ...]]:
    """``query`` compiled against the default connection: its SQL text and params."""
    compiler = require_instance(object_result(query.get_compiler, using="default"), SQLCompiler)
    return compiler.as_sql()


def _as_stand_in_hook_type(cls: type[object]) -> type[DjangoType]:
    """Hand a plain stand-in class carrying a ``get_queryset`` to the visibility substrate.

    The stand-in is either a class whose ``get_queryset`` is ``async def`` or one that
    carries no ``DjangoType`` default stamp at all.
    """
    # basedpyright: an async ``get_queryset`` is a supported consumer hook the sync base signature
    # does not admit, and a DjangoType subclass declaring one is reported as an incompatible
    # override; an unstamped class is by definition not a DjangoType; the visibility substrate
    # types the parameter as type[DjangoType]
    return cls  # pyright: ignore[reportReturnType]


# Every type declared here registers; the shared fixture clears it after each test.
pytestmark = pytest.mark.usefixtures("isolate_global_registry")


def _declared_type(
    model: type[models.Model],
    name: str,
    hook: Callable[[type, models.QuerySet[_M], object], object] | None = None,
) -> type[DjangoType]:
    """Declare a real ``DjangoType`` over ``model``, with ``hook`` as its visibility hook."""
    namespace: dict[str, object] = {
        "Meta": type("Meta", (), {"model": model, "fields": ("id",)}),
    }
    if hook is not None:
        namespace["get_queryset"] = classmethod(hook)
    return type(name, (DjangoType,), namespace)


def _stub_type(
    model: type[_M],
    hook: Callable[[type, models.QuerySet[_M], object], object],
) -> type[DjangoType]:
    """Declare a real ``DjangoType`` over ``model`` with ``hook`` as its visibility hook."""
    return _declared_type(model, "_StubType", hook)


def _sync_type() -> type[DjangoType]:
    """A real type whose sync ``get_queryset`` keeps every row but a never-present name."""
    return _declared_type(
        Category,
        "_SyncType",
        lambda _cls, queryset, _info: queryset.exclude(name="__never__"),
    )


@_as_stand_in_hook_type
class _AsyncType:
    """Plain class with an ``async def`` ``get_queryset``."""

    __django_strawberry_definition__ = SimpleNamespace(model=Category)

    @classmethod
    async def get_queryset(
        cls,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset


# ---------------------------------------------------------------------------
# normalize_query_source -- the single Manager-coercion / is-queryset decision
# ---------------------------------------------------------------------------


def test_normalize_query_source_coerces_manager_to_queryset() -> None:
    """A ``Manager`` becomes a ``QuerySet`` and reports ``is_queryset=True``."""
    source, is_queryset = normalize_query_source(Category.objects)
    assert isinstance(source, models.QuerySet)
    assert is_queryset is True


def test_normalize_query_source_passes_queryset_through() -> None:
    """A ``QuerySet`` passes through unchanged with ``is_queryset=True``."""
    qs = Category.objects.all()
    source, is_queryset = normalize_query_source(qs)
    assert source is qs
    assert is_queryset is True


def test_normalize_query_source_passes_non_queryset_through() -> None:
    """A non-queryset iterable passes through with ``is_queryset=False``."""
    payload = [1, 2, 3]
    source, is_queryset = normalize_query_source(payload)
    assert source is payload
    assert is_queryset is False


def test_initial_queryset_uses_default_manager() -> None:
    """``initial_queryset`` returns the declared model's ``_default_manager.all()``."""
    qs = initial_queryset(_sync_type())
    assert isinstance(qs, models.QuerySet)
    assert qs.model is Category


_MANAGER_SHAPES = ["from_queryset", "hand_written", "polymorphic"]
_ManagerShape = Callable[[type[models.Model], str, str], AbstractContextManager[type]]


def _shelves_one_hidden() -> None:
    """Shelves ``aa-ok`` and ``zz-hidden`` on one branch."""
    branch = Branch.objects.create(name="Shaped")
    Shelf.objects.create(branch=branch, code="aa-ok")
    Shelf.objects.create(branch=branch, code="zz-hidden")


@pytest.mark.django_db
@pytest.mark.parametrize("shape", _MANAGER_SHAPES)
def test_related_queryset_is_every_row_in_the_default_manager_class(
    shape: str,
    default_manager_shape: _ManagerShape,
) -> None:
    """A relation's seed is the default manager's ``QuerySet`` class over every row.

    The manager's own ``get_queryset`` hides ``zz-hidden``; the seed keeps its
    class (and a class's ``__init__`` state) and drops its filter, as Django's
    join across a relation reads no manager.
    """
    _shelves_one_hidden()
    with default_manager_shape(Shelf, shape, "code") as queryset_class:
        rows = related_queryset(Shelf)

        assert truth.class_of(rows) is queryset_class
        assert sorted(rows.values_list("code", flat=True)) == ["aa-ok", "zz-hidden"]
        assert list(base_queryset(Shelf).values_list("code", flat=True)) == ["aa-ok"]
        assert read_attr(rows, "shape_state", None) is (True if shape == "polymorphic" else None)


@pytest.mark.django_db
def test_related_queryset_reads_no_filtering_base_manager(
    default_manager_shape: _ManagerShape,
) -> None:
    """A ``Meta.base_manager_name`` that filters is not read: the seed is the join's rows."""
    _shelves_one_hidden()
    with default_manager_shape(Shelf, "base", "code"):
        rows = related_queryset(Shelf)

        assert truth.class_of(rows) is models.QuerySet
        assert sorted(rows.values_list("code", flat=True)) == ["aa-ok", "zz-hidden"]
        assert list(Shelf._base_manager.values_list("code", flat=True)) == ["aa-ok"]


def test_related_queryset_pins_the_requested_alias_else_the_managers() -> None:
    """``using`` pins the seed; unpinned it keeps the manager's own (unrouted) alias."""
    assert queryset_db(related_queryset(Shelf, using="other")) == "other"
    assert queryset_db(related_queryset(Shelf)) is None


def test_related_queryset_refuses_an_abstract_model() -> None:
    """An abstract model has no default manager: the seed names it, as ``base_queryset`` does."""

    class AbstractShelf(models.Model):
        class Meta:
            abstract = True
            app_label = "library"

    with pytest.raises(ConfigurationError, match=r"^AbstractShelf is an abstract model"):
        related_queryset(AbstractShelf)


class _PolymorphicRowIterable(django_query.ModelIterable[models.Model]):
    """django-polymorphic's ``PolymorphicModelIterable`` shape: a ``ModelIterable`` subclass."""


class _PolymorphicRowsQuerySet(models.QuerySet[models.Model]):
    """django-polymorphic's ``PolymorphicQuerySet`` shape: ``__init__`` stores its row iterable."""

    def __init__(
        self,
        model: type[models.Model] | None = None,
        query: SqlQuery | None = None,
        using: str | None = None,
        hints: dict[str, models.Model] | None = None,
    ) -> None:
        """Construct as ``QuerySet`` does, then store a ``ModelIterable`` subclass."""
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._iterable_class = _PolymorphicRowIterable


class _ValuesRowsQuerySet(models.QuerySet[models.Model]):
    """A class whose ``__init__`` stores a ``.values()`` row iterable: its rows are dicts."""

    def __init__(
        self,
        model: type[models.Model] | None = None,
        query: SqlQuery | None = None,
        using: str | None = None,
        hints: dict[str, models.Model] | None = None,
    ) -> None:
        """Construct as ``QuerySet`` does, then store ``ValuesIterable``."""
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._iterable_class = django_query.ValuesIterable


def _default_manager_of(
    monkeypatch: pytest.MonkeyPatch,
    queryset_class: type[models.QuerySet[models.Model]],
) -> None:
    """Make ``queryset_class.as_manager()`` ``Shelf``'s default manager for one test."""
    manager = queryset_class.as_manager()
    manager.model = Shelf
    monkeypatch.setitem(vars(Shelf._meta), "default_manager", manager)


def test_related_queryset_keeps_a_model_iterable_subclass(monkeypatch: pytest.MonkeyPatch) -> None:
    """A class whose ``__init__`` stores a ``ModelIterable`` subclass seeds model rows."""
    _default_manager_of(monkeypatch, _PolymorphicRowsQuerySet)

    rows = related_queryset(Shelf)

    assert truth.class_of(rows) is _PolymorphicRowsQuerySet
    assert truth.instance_state(rows)["_iterable_class"] is _PolymorphicRowIterable


def test_related_queryset_refuses_a_class_whose_init_stores_a_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A class whose ``__init__`` stores a ``Values*`` iterable yields no model rows: refused.

    The class is project code, so the refusal is a ``ConfigurationError`` naming the model,
    the class and the iterable it left.
    """
    _default_manager_of(monkeypatch, _ValuesRowsQuerySet)

    with pytest.raises(
        ConfigurationError,
        match=(
            r"^Shelf's default manager returns _ValuesRowsQuerySet, whose __init__ leaves the "
            r"row iterable ValuesIterable\. .*must keep a ModelIterable row iterable\.$"
        ),
    ):
        related_queryset(Shelf)


# ---------------------------------------------------------------------------
# coerce_field_value_or_none -- the shared "raw literal -> field value" coercion
# ---------------------------------------------------------------------------


def test_coerce_field_value_or_none_returns_coerced_value() -> None:
    """A well-formed literal coerces through ``to_python``."""
    assert coerce_field_value_or_none(Category._meta.pk, "3", alias=DEFAULT_DB_ALIAS) == 3


@pytest.mark.parametrize(
    ("text", "expected"),
    [pytest.param("title", "title", id="text"), pytest.param("a\x00b", None, id="embedded-nul")],
)
def test_coerce_field_value_or_none_reads_a_lazy_value_as_its_text(
    text: str,
    expected: object,
) -> None:
    """A ``SimpleLazyObject`` coerces as the text it stands for; an embedded NUL names no row."""
    lazy_text = SimpleLazyObject(lambda: text)
    field = Category._meta.get_field("name")

    assert coerce_field_value_or_none(field, lazy_text, alias=DEFAULT_DB_ALIAS) == expected


def test_coerce_field_value_or_none_drops_non_numeric_literal() -> None:
    """A non-numeric literal fails ``to_python`` (wrapped as ``ValidationError``) -> ``None``."""
    assert (
        coerce_field_value_or_none(Category._meta.pk, "not-a-number", alias=DEFAULT_DB_ALIAS)
        is None
    )


def test_coerce_field_value_or_none_drops_out_of_range_literal() -> None:
    """A syntactically-valid literal past the column's storage range is ``None``.

    ``to_python`` alone would cast ``2**63`` (one past the ``BigAutoField`` pk's
    signed-64-bit range) to a plain Python ``int`` with no error; the range the
    database stores for the column catches it, never a raw backend
    ``OverflowError`` at ``pk__in``.
    """
    assert coerce_field_value_or_none(Category._meta.pk, 2**63, alias=DEFAULT_DB_ALIAS) is None


@pytest.mark.parametrize("model", [PatronProfile, LendingDesk, SelfServeDesk])
def test_coerce_field_value_or_none_range_checks_a_relation_valued_pk(
    model: type[models.Model],
) -> None:
    """A one-to-one pk or parent-link chain is held to the range of the column storing it.

    The key's own ``to_python`` delegates down the chain, and the value is held to the
    integer range the database stores for the column the chain ends at
    (``DatabaseOperations.integer_field_range``): an out-of-range literal identifies no
    row instead of reaching ``pk__in`` as a backend ``OverflowError``.
    """
    assert coerce_field_value_or_none(model._meta.pk, "7", alias=DEFAULT_DB_ALIAS) == 7
    assert coerce_field_value_or_none(model._meta.pk, 2**63, alias=DEFAULT_DB_ALIAS) is None
    assert coerce_field_value_or_none(model._meta.pk, str(2**70), alias=DEFAULT_DB_ALIAS) is None


def _reject_thirteen(value: object) -> None:
    """A consumer validator declared on a key: refuse the id ``13``."""
    if value == 13:
        raise ValidationError("13 is reserved.")


def test_coerce_field_value_or_none_skips_validators_and_range_checks_the_stored_column() -> None:
    """A value a key's validator refuses still coerces; the column it stores still range-checks.

    A row holding an id the key's own ``validators=`` refuse (``13``) is stored by any
    write that skips ``full_clean``, so the id still identifies it. ``Patron.id``'s range,
    which the key reaches only through the column it stores, refuses ``2**63``.
    """
    key: models.OneToOneField[Patron | Combinable, Patron] = models.OneToOneField(
        Patron,
        on_delete=models.CASCADE,
        primary_key=True,
        validators=[_reject_thirteen],
    )
    assert coerce_field_value_or_none(key, "7", alias=DEFAULT_DB_ALIAS) == 7
    assert coerce_field_value_or_none(key, "13", alias=DEFAULT_DB_ALIAS) == 13
    assert coerce_field_value_or_none(key, 2**63, alias=DEFAULT_DB_ALIAS) is None


def test_coerce_field_value_or_none_codes_a_generated_column_as_the_column_it_computes() -> None:
    """A ``GeneratedField``'s own ``to_python`` is the identity; the output's casts.

    ``Shelf.code_length`` computes a ``BigIntegerField``: a decoded ``"2"`` is the integer
    its rows hold, and a literal past 64 bits identifies no row.
    """
    field = Shelf._meta.get_field("code_length")

    assert coerce_field_value_or_none(field, "2", alias=DEFAULT_DB_ALIAS) == 2
    assert coerce_field_value_or_none(field, str(2**70), alias=DEFAULT_DB_ALIAS) is None
    assert coerce_field_value_or_none(field, "two", alias=DEFAULT_DB_ALIAS) is None


def test_coerce_field_value_or_none_drops_an_infinite_float() -> None:
    """``int(inf)`` in ``IntegerField.to_python`` is ``OverflowError`` -> ``None``."""
    assert (
        coerce_field_value_or_none(Category._meta.pk, float("inf"), alias=DEFAULT_DB_ALIAS) is None
    )


_INTEGER_KEYS = [
    pytest.param(Category, "id", id="integer-pk"),
    pytest.param(Item, "category", id="fk-to-integer-pk"),
]


@pytest.mark.parametrize(("model", "name"), _INTEGER_KEYS)
@pytest.mark.parametrize(
    "value",
    [
        1.5,
        Decimal("1.5"),
        0.9,
        -1.5,
    ],
)
def test_coerce_field_value_or_none_drops_a_fractional_number(
    model: type[models.Model],
    name: str,
    value: object,
) -> None:
    """A fractional number names no integer row; ``int()`` truncating it never binds."""
    field = model._meta.get_field(name)
    assert coerce_field_value_or_none(field, value, alias=DEFAULT_DB_ALIAS) is None


@pytest.mark.parametrize(("model", "name"), _INTEGER_KEYS)
@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.0, 1), (Decimal("1E+2"), 100), (Decimal("3.000"), 3)],
)
def test_coerce_field_value_or_none_keeps_an_integral_number(
    model: type[models.Model],
    name: str,
    value: object,
    expected: int,
) -> None:
    """A number equal to its integer cast is that integer, however it is spelled."""
    field = model._meta.get_field(name)
    assert coerce_field_value_or_none(field, value, alias=DEFAULT_DB_ALIAS) == expected


def test_coerce_field_value_or_none_keeps_a_fractional_number_off_an_integer_column() -> None:
    """Only an integer column holds no fraction: a float, decimal or text column keeps it."""
    assert coerce_field_value_or_none(models.FloatField(), 1.5, alias=DEFAULT_DB_ALIAS) == 1.5
    assert coerce_field_value_or_none(
        _decimal_column(),
        Decimal("1.5"),
        alias=DEFAULT_DB_ALIAS,
    ) == Decimal("1.5")
    assert coerce_field_value_or_none(models.TextField(), 1.5, alias=DEFAULT_DB_ALIAS) == "1.5"


def _integer_column() -> "models.BigIntegerField[int | float | str | Combinable, int]":
    return models.BigIntegerField()


class _CastRefusingDecimal(Decimal):
    """A ``Decimal`` whose integer cast raises, so a test sees any check that casts it."""

    @override
    def __int__(self) -> int:
        raise AssertionError("the number was cast to an integer")


@pytest.mark.parametrize(
    ("spelling", "fractional"),
    [
        pytest.param("1.5", True, id="fraction"),
        pytest.param("-1E-1000000", True, id="tiny-fraction"),
        pytest.param("1E+2", False, id="integral-exponent"),
        pytest.param("-1E+1000000", False, id="million-digit-integer"),
        pytest.param("-0", False, id="negative-zero"),
        pytest.param("NaN", False, id="not-a-number"),
        pytest.param("sNaN", False, id="signaling-not-a-number"),
        pytest.param("Infinity", False, id="infinity"),
    ],
)
def test_truncates_to_integer_asks_the_number_and_never_casts_it(
    spelling: str,
    *,
    fractional: bool,
) -> None:
    """A decimal answers for its own integrality, however many digits its integer has.

    Django-filter caps a decimal only from above, so ``-1E+1000000`` reaches the check; a
    cast of it to an integer and the comparison back cost seconds each, so neither runs.
    """
    column = _integer_column()
    assert truncates_to_integer(column, _CastRefusingDecimal(spelling)) is fractional


def test_truncates_to_integer_reads_only_a_finite_non_integral_number() -> None:
    """A finite non-integral float is fractional; a bool, a string, inf and NaN are not."""
    column = _integer_column()
    assert truncates_to_integer(column, 0.9) is True
    assert truncates_to_integer(column, -1.5) is True
    assert truncates_to_integer(column, 1.0) is False
    assert truncates_to_integer(column, float("inf")) is False
    assert truncates_to_integer(column, float("nan")) is False
    assert truncates_to_integer(column, 7) is False
    assert truncates_to_integer(column, value=True) is False
    assert truncates_to_integer(column, "1.5") is False
    assert truncates_to_integer(models.FloatField(), 1.5) is False
    assert truncates_to_integer(None, 1.5) is False


def _narrow_big_auto_range(internal_type: str) -> tuple[int, int]:
    """A backend storing a ``BigAutoField`` column in ``0..10``."""
    assert internal_type == "BigAutoField"
    return (0, 10)


def test_coerce_field_value_or_none_reads_the_range_of_the_named_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The integer range is the one the ``alias`` database stores.

    A second alias whose backend stores the pk column in ``0..10`` refuses ``11`` there,
    while the default database, whose column is signed 64-bit, keeps it.
    """
    alias = "narrow_integer_alias"
    connections.databases[alias] = {**connections.databases["default"], "NAME": ":memory:"}
    try:
        monkeypatch.setattr(connections[alias].ops, "integer_field_range", _narrow_big_auto_range)
        assert coerce_field_value_or_none(Category._meta.pk, 11, alias=DEFAULT_DB_ALIAS) == 11
        assert coerce_field_value_or_none(Category._meta.pk, 11, alias=alias) is None
        assert coerce_field_value_or_none(Category._meta.pk, 10, alias=alias) == 10
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


class _UnrangedIntegerField(models.IntegerField[int, int]):
    """An integer column type naming an internal type no backend states a range for."""

    @override
    def get_internal_type(self) -> str:
        return "UnrangedIntegerField"


def test_coerce_field_value_or_none_holds_a_type_without_a_stated_range_to_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A column type the ``alias`` database states no range for holds its value to none.

    A second alias reads Django's default ranges (PostgreSQL's), whose
    ``integer_field_range`` raises ``KeyError`` for an internal type absent from them, so
    that column keeps ``2**70`` there, while an ``IntegerField`` is still held to its
    32 bits.
    """
    alias = "default_range_alias"
    connections.databases[alias] = {**connections.databases["default"], "NAME": ":memory:"}
    try:
        operations = connections[alias].ops
        monkeypatch.setattr(
            operations,
            "integer_field_range",
            functools.partial(BaseDatabaseOperations.integer_field_range, operations),
        )
        assert coerce_field_value_or_none(_UnrangedIntegerField(), 2**70, alias=alias) == 2**70
        assert coerce_field_value_or_none(models.IntegerField(), 2**31, alias=alias) is None
        assert (
            coerce_field_value_or_none(models.IntegerField(), 2**31 - 1, alias=alias) == 2**31 - 1
        )
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


def test_coerce_field_value_or_none_drops_overflowing_duration() -> None:
    """A duration string past ``timedelta``'s range is Django's ``OverflowError`` -> ``None``."""
    assert (
        coerce_field_value_or_none(
            models.DurationField(),
            "99999999999 00:00:00",
            alias=DEFAULT_DB_ALIAS,
        )
        is None
    )


def _decimal_column() -> "models.DecimalField[Decimal | Combinable, Decimal]":
    return models.DecimalField(max_digits=6, decimal_places=2)


def _unbounded_decimal_column() -> "models.DecimalField[Decimal | Combinable, Decimal]":
    return models.DecimalField(max_digits=None, decimal_places=None)


def _address_column() -> "models.GenericIPAddressField[str | Combinable, str]":
    return models.GenericIPAddressField()


def _duration_column() -> (
    "models.DurationField[datetime.timedelta | Combinable, datetime.timedelta]"
):
    return models.DurationField()


def _datetime_column() -> (
    "models.DateTimeField[datetime.datetime | Combinable, datetime.datetime]"
):
    return models.DateTimeField()


@pytest.mark.parametrize(
    ("raw", "held"),
    [
        pytest.param("1.500", "1.50", id="trailing-zero"),
        pytest.param("1.5" + "0" * 20000, "1.50", id="huge-scale"),
        pytest.param("1.505", None, id="finer-fraction"),
        pytest.param("12345678", None, id="too-many-digits"),
        pytest.param("1e1000000", None, id="huge-exponent"),
        pytest.param("1e-1000000", None, id="tiny-exponent"),
    ],
)
def test_coerce_field_value_or_none_holds_a_decimal_to_the_column_value(
    raw: str,
    held: str | None,
) -> None:
    """A decimal is the ``DecimalField(6, 2)`` value it equals, or ``None`` when none does.

    ``1.500`` and ``1.5`` with 20000 trailing zeros are the stored ``1.50``; a finer
    fraction, more integer digits than the column holds and an exponent past either end
    equal no stored value, on every backend.
    """
    coerced = coerce_field_value_or_none(_decimal_column(), raw, alias=DEFAULT_DB_ALIAS)
    assert (None if coerced is None else str(coerced)) == held


_PAST_UNCONSTRAINED_NUMERIC = (
    pytest.param("1e1000000", id="huge-exponent"),
    pytest.param("-1e1000000", id="negative-huge-exponent"),
    pytest.param("1e-1000000", id="tiny-exponent"),
    pytest.param("1E+131072", id="131073-integer-digits"),
    pytest.param("1E-16384", id="16384-fraction-digits"),
    pytest.param("9" * 131073, id="131073-nines"),
    pytest.param("1." + "0" * 16384 + "1", id="16385-fraction-digits"),
)

_WITHIN_UNCONSTRAINED_NUMERIC = tuple(
    pytest.param(sign + raw, sign + held, id=sign + name)
    for sign in ("", "-")
    for raw, held, name in (
        ("1E+131071", "1E+131071", "131072-integer-digits"),
        ("1E-16383", "1E-16383", "16383-fraction-digits"),
        ("9" * 131072, "9" * 131072, "131072-nines"),
        ("1.50", "1.50", "written-trailing-zero"),
        ("1." + "0" * 16383, "1." + "0" * 16383, "16383-trailing-zeros"),
        ("1.5" + "0" * 20000, "1.5", "trailing-zeros"),
        ("0E+1000000", "0E+1000000", "zero-huge-exponent"),
        ("0E+1073741824", "0", "zero-past-exponent-limit"),
        ("0E-16384", "0", "zero-tiny-exponent"),
        (
            "0.1234567890123456789012345678901234567891",
            "0.1234567890123456789012345678901234567891",
            "40-digit-fraction",
        ),
        (
            "0.1234567890123456789012345678901234567891" + "0" * 16344,
            "0.1234567890123456789012345678901234567891",
            "40-digit-fraction-trailing-zeros",
        ),
    )
)


@contextmanager
def _unopened_alias(wrapper: Callable[[str], BaseDatabaseWrapper]) -> Generator[str, None, None]:
    """Register the never-opened connection ``wrapper`` builds; it must stay unopened."""
    alias = "unconstrained_numeric_stand_in"
    connections[alias] = wrapper(alias)
    try:
        yield alias
        assert read_attr(connections[alias], "connection") is None
    finally:
        del connections[alias]


def _postgresql_wrapper(alias: str) -> BaseDatabaseWrapper:
    """A never-opened connection that reads as PostgreSQL; the decimal rule reads only the vendor."""
    wrapper = _sqlite_wrapper(alias)
    wrapper.vendor = "postgresql"
    return wrapper


def _sqlite_wrapper(alias: str) -> BaseDatabaseWrapper:
    """A SQLite connection that is never opened."""
    settings_dict = {**connections.databases[DEFAULT_DB_ALIAS], "NAME": ":memory:"}
    return SQLiteDatabaseWrapper(settings_dict, alias)


@pytest.mark.parametrize("raw", _PAST_UNCONSTRAINED_NUMERIC)
def test_coerce_field_value_or_none_refuses_a_decimal_past_postgresql_numeric(raw: str) -> None:
    """A decimal past PostgreSQL's unconstrained ``numeric`` names no row there.

    ``numeric`` with no precision stores up to 131072 digits before the point and 16383
    after; a value needing more refuses to bind (``numeric_in``: "value overflows numeric
    format"), so it is ``None`` with no connection opened.
    """
    with _unopened_alias(_postgresql_wrapper) as alias:
        assert coerce_field_value_or_none(_unbounded_decimal_column(), raw, alias=alias) is None


@pytest.mark.parametrize(("raw", "held"), _WITHIN_UNCONSTRAINED_NUMERIC)
def test_coerce_field_value_or_none_keeps_a_decimal_within_postgresql_numeric(
    raw: str,
    held: str,
) -> None:
    """A decimal within PostgreSQL's unconstrained ``numeric`` is the value it equals.

    A spelling that fits binds as written (``1.50`` stays ``1.50``, a 40-digit fraction
    stays exact); one past the limits loses its trailing fractional zeros without
    rounding, so ``1.5`` with 20000 zeros binds as ``1.5`` and such a zero as ``0``. The
    value is unchanged, so it names the same row.
    """
    with _unopened_alias(_postgresql_wrapper) as alias:
        coerced = coerce_field_value_or_none(_unbounded_decimal_column(), raw, alias=alias)
    assert coerced == Decimal(raw)
    assert str(coerced) == held


@pytest.mark.parametrize(
    "raw",
    [
        *_PAST_UNCONSTRAINED_NUMERIC,
        *(pytest.param(case.values[0], id=case.id) for case in _WITHIN_UNCONSTRAINED_NUMERIC),
    ],
)
def test_coerce_field_value_or_none_passes_an_unconstrained_decimal_through_off_postgresql(
    raw: str,
) -> None:
    """Off PostgreSQL a decimal on a ``DecimalField`` without ``max_digits`` binds as given.

    SQLite stores the value it is bound, so every one of the PostgreSQL rows, refused or
    trimmed there, passes with its spelling intact.
    """
    with _unopened_alias(_sqlite_wrapper) as alias:
        coerced = coerce_field_value_or_none(_unbounded_decimal_column(), raw, alias=alias)
    assert isinstance(coerced, Decimal)
    assert str(coerced) == str(Decimal(raw))


@pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite's adapters")
@pytest.mark.parametrize(
    ("column", "raw", "held"),
    [
        pytest.param(_address_column, "abc", "abc", id="address-bound-as-text"),
        pytest.param(_duration_column, "999999999 00:00:00", None, id="duration-past-int64-us"),
        pytest.param(
            _datetime_column,
            "0001-01-01T00:00:00+05:00",
            None,
            id="datetime-before-year-1",
        ),
    ],
)
def test_coerce_field_value_or_none_holds_the_bind_sqlite_makes(
    column: Callable[[], models.Field[object, object]],
    raw: str,
    held: str | None,
) -> None:
    """A value names a row on SQLite only as SQLite binds and stores it.

    SQLite's adapter binds any text for an address and refuses an aware datetime whose
    UTC projection precedes year 1. A duration binds as its microsecond count, an
    integer held to the 64-bit range (``BigIntegerField``'s), which a count past it
    leaves; PostgreSQL binds a native interval instead, hence the SQLite gate.
    """
    coerced = coerce_field_value_or_none(column(), raw, alias=DEFAULT_DB_ALIAS)
    assert (None if coerced is None else str(coerced)) == held


#: A non-UTC default time zone, so a naive value made aware in it differs from UTC.
_NAIVE_ZONE = "America/New_York"
_EIGHT_IN_ZONE = datetime.datetime(2024, 1, 1, 8, tzinfo=zoneinfo.ZoneInfo(_NAIVE_ZONE))
#: The naive spelling of ``_EIGHT_IN_ZONE``'s wall clock.
_NAIVE_EIGHT = _EIGHT_IN_ZONE.replace(tzinfo=None)


@override_settings(TIME_ZONE=_NAIVE_ZONE)
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("2024-01-01T08:00:00", _EIGHT_IN_ZONE, id="iso-t"),
        pytest.param("2024-01-01 08:00:00", _EIGHT_IN_ZONE, id="iso-space"),
        pytest.param("2024-01-01", _EIGHT_IN_ZONE.replace(hour=0), id="date-only-midnight"),
        pytest.param(_NAIVE_EIGHT, _EIGHT_IN_ZONE, id="naive-datetime"),
        pytest.param(datetime.date(2024, 1, 1), _EIGHT_IN_ZONE.replace(hour=0), id="date"),
    ],
)
def test_coerce_field_value_or_none_makes_a_naive_datetime_aware_in_the_default_zone(
    raw: object,
    expected: datetime.datetime,
) -> None:
    """A naive datetime key is the aware value Django binds for it, read without its warning.

    Under ``USE_TZ`` Django's lookup makes a naive ``DateTimeField`` value aware in the
    default time zone and warns as it does; the coercion makes the same projection
    silently and returns the aware value, so the reorder keys the request as the row.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with _unopened_alias(_sqlite_wrapper) as alias:
            coerced = coerce_field_value_or_none(_datetime_column(), raw, alias=alias)
    assert isinstance(coerced, datetime.datetime)
    assert coerced == expected
    assert coerced.utcoffset() == expected.utcoffset()


@override_settings(TIME_ZONE=_NAIVE_ZONE)
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(_NAIVE_EIGHT, _EIGHT_IN_ZONE, id="naive-datetime"),
        pytest.param(datetime.date(2024, 1, 1), _EIGHT_IN_ZONE.replace(hour=0), id="date"),
    ],
)
def test_coerce_field_value_or_none_makes_a_naive_datetime_aware_in_the_default_zone_not_the_current(
    raw: object,
    expected: datetime.datetime,
) -> None:
    """An activated current time zone does not move the zone a naive key is made aware in.

    Django binds a naive ``DateTimeField`` value in the default time zone (``TIME_ZONE``)
    whatever zone ``timezone.activate`` made current, so the coercion does too.
    """
    with timezone.override("Asia/Tokyo"), _unopened_alias(_sqlite_wrapper) as alias:
        coerced = coerce_field_value_or_none(_datetime_column(), raw, alias=alias)
    assert isinstance(coerced, datetime.datetime)
    assert coerced == expected
    assert coerced.utcoffset() == expected.utcoffset()


@override_settings(USE_TZ=False, TIME_ZONE=_NAIVE_ZONE)
def test_coerce_field_value_or_none_keeps_a_naive_datetime_naive_without_use_tz() -> None:
    """With ``USE_TZ`` off Django binds a naive datetime as it is, so the coercion does too."""
    with _unopened_alias(_sqlite_wrapper) as alias:
        coerced = coerce_field_value_or_none(
            _datetime_column(),
            "2024-01-01T08:00:00",
            alias=alias,
        )
    assert coerced == _NAIVE_EIGHT


@pytest.mark.parametrize(
    ("zone", "raw"),
    [
        pytest.param("Asia/Tokyo", "0001-01-01T00:00:00", id="year-1-east-of-utc"),
        pytest.param("America/New_York", "9999-12-31T23:00:00", id="year-9999-west-of-utc"),
    ],
)
def test_coerce_field_value_or_none_drops_a_naive_datetime_whose_utc_bind_overflows(
    zone: str,
    raw: str,
) -> None:
    """A naive datetime whose aware projection leaves years 1..9999 in UTC names no row.

    SQLite binds an aware datetime as its UTC wall clock; made aware in a zone east of
    UTC on year 1 (or west of it on the last hour of year 9999) the projection
    overflows, so the id is ``None``, never a crash and never a warning.
    """
    with override_settings(TIME_ZONE=zone), warnings.catch_warnings():
        warnings.simplefilter("error")
        with _unopened_alias(_sqlite_wrapper) as alias:
            assert coerce_field_value_or_none(_datetime_column(), raw, alias=alias) is None


@override_settings(TIME_ZONE=_NAIVE_ZONE)
@pytest.mark.parametrize(
    ("utc_row", "naive"),
    [
        pytest.param(
            datetime.datetime(2024, 1, 1, 13, tzinfo=datetime.timezone.utc),
            "2024-01-01T08:00:00",
            id="standard-time",
        ),
        pytest.param(
            datetime.datetime(2024, 11, 3, 5, 30, tzinfo=datetime.timezone.utc),
            "2024-11-03T01:30:00",
            id="dst-fold",
        ),
        pytest.param(
            datetime.datetime(2024, 3, 10, 7, 30, tzinfo=datetime.timezone.utc),
            "2024-03-10T02:30:00",
            id="dst-gap",
        ),
    ],
)
def test_identity_key_keys_a_naive_datetime_as_the_aware_row_it_binds(
    utc_row: datetime.datetime,
    naive: str,
) -> None:
    """A naive request and the aware row Django's lookup matched for it share one key.

    The row reads back aware (in UTC); the naive spelling is made aware in the default
    zone, so both key as the same instant without the naive-datetime warning, a wall
    clock the zone repeats (a DST fold) or skips (a gap) included: Django binds it at
    its first offset, and PEP 495 would hold that aware value unequal to the UTC row.
    """
    field = _DatetimeKeyed._meta.pk
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        keys = {
            identity_key(field, spelled)
            for spelled in (
                utc_row,
                naive,
                datetime.datetime.fromisoformat(naive),
                utc_row.astimezone(datetime.timezone(datetime.timedelta(hours=5))),
            )
        }
    assert len(keys) == 1


def _refused_raw_decimal(raw: str) -> None:
    """Bind ``raw`` unheld against the decimal-keyed table: PostgreSQL refuses it."""
    with pytest.raises(DataError), transaction.atomic():
        list(_DecimalKeyed.objects.filter(pk__in=[_DecimalKeyed._meta.pk.to_python(raw)]))


_decimal_keyed_apps = Apps([])


class _DecimalKeyed(models.Model):
    """A table keyed by a ``DecimalField(6, 2)``."""

    code: "models.DecimalField[str | float | Decimal | Combinable, Decimal]" = models.DecimalField(
        primary_key=True,
        max_digits=6,
        decimal_places=2,
    )

    class Meta:
        app_label = "products"
        managed = False
        apps = _decimal_keyed_apps


class _DatetimeKeyed(models.Model):
    """A table keyed by an aware ``DateTimeField``."""

    stamp: "_AwareStamp" = models.DateTimeField(primary_key=True)

    class Meta:
        app_label = "products"
        managed = False
        apps = _decimal_keyed_apps


class _UnconstrainedDecimalKeyed(models.Model):
    """A table keyed by a ``DecimalField`` without ``max_digits``."""

    code: "models.DecimalField[str | float | Decimal | Combinable, Decimal]" = models.DecimalField(
        primary_key=True,
        max_digits=None,
        decimal_places=None,
    )

    class Meta:
        app_label = "products"
        managed = False
        apps = _decimal_keyed_apps


@pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite stores the value it is bound")
@pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="Django below 6.1 cannot read back a DecimalField without decimal_places",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("raw", "rows"),
    [
        pytest.param("1.5" + "0" * 20000, [Decimal("1.5")], id="trailing-zeros"),
        pytest.param("1e1000000", [], id="huge-exponent"),
    ],
)
def test_coerce_field_value_or_none_finds_an_unconstrained_decimal_key_on_sqlite(
    raw: str,
    rows: list[Decimal],
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """On SQLite an unconstrained decimal key binds as given and the ``pk__in`` query runs.

    The value PostgreSQL would trim or refuse keeps its spelling here, and the one query
    finds the stored ``1.5`` or no row.
    """
    with connection.schema_editor() as editor:
        editor.create_model(_UnconstrainedDecimalKeyed)
    try:
        _UnconstrainedDecimalKeyed.objects.create(code=Decimal("1.5"))
        coerced = coerce_field_value_or_none(
            _UnconstrainedDecimalKeyed._meta.pk,
            raw,
            alias=DEFAULT_DB_ALIAS,
        )
        assert str(coerced) == str(Decimal(raw))
        with django_assert_num_queries(1):
            found = [
                row.code for row in _UnconstrainedDecimalKeyed.objects.filter(pk__in=[coerced])
            ]
        assert found == rows
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_UnconstrainedDecimalKeyed)


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
def test_coerce_field_value_or_none_refuses_an_offset_postgresql_refuses() -> None:
    """A datetime key whose UTC offset PostgreSQL's server refuses names no row there.

    The adapter passes the aware value through and the server refuses ``+16:00``
    (``utils/errors.py::unbindable_temporal``): the raw ``to_python`` value raises
    ``DataError`` in the ``pk__in`` query, the coerced one is ``None``.
    """
    raw = "2020-01-01T00:00:00+16:00"
    with connection.schema_editor() as editor:
        editor.create_model(_DatetimeKeyed)
    try:
        with pytest.raises(DataError), transaction.atomic():
            list(_DatetimeKeyed.objects.filter(pk__in=[_DatetimeKeyed._meta.pk.to_python(raw)]))
        assert (
            coerce_field_value_or_none(_DatetimeKeyed._meta.pk, raw, alias=DEFAULT_DB_ALIAS)
            is None
        )
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_DatetimeKeyed)


@pytest.mark.parametrize(
    ("column", "value", "refused"),
    [
        pytest.param(
            lambda: _DatetimeKeyed._meta.pk,
            "2020-01-01T00:00:00+16:00",
            True,
            id="datetime-16-00",
        ),
        pytest.param(
            lambda: _DatetimeKeyed._meta.pk,
            "2020-01-01T00:00:00+15:59",
            False,
            id="datetime-15-59",
        ),
        pytest.param(
            lambda: ScalarSpecimen._meta.get_field("occurred_time"),
            datetime.time(12, tzinfo=datetime.timezone(datetime.timedelta(hours=-16))),
            True,
            id="time-minus-16-00",
        ),
        pytest.param(
            lambda: ScalarSpecimen._meta.get_field("occurred_time"),
            datetime.time(12, tzinfo=datetime.timezone(datetime.timedelta(hours=-15))),
            False,
            id="time-minus-15-00",
        ),
    ],
)
def test_coerce_field_value_or_none_holds_a_utc_offset_to_what_postgresql_binds(
    column: Callable[[], models.Field[object, object] | None],
    value: object,
    *,
    refused: bool,
) -> None:
    """On an alias reading as PostgreSQL a value whose UTC offset its server refuses is ``None``.

    The alias binds as text (psycopg 3's ``ClientCursor``) and its adapters pass the aware
    value through, so the offset rule (``utils/errors.py::unbindable_temporal``) answers:
    an offset of 16:00 or more names no row, one inside it is the coerced value.
    """
    driver, cursor_factory, _ = BINDING_MODES["psycopg3-client"]
    field = column()
    assert isinstance(field, models.Field)
    expected = object_result(field.to_python, value)
    assert isinstance(expected, (datetime.datetime, datetime.time))
    assert expected.tzinfo is not None
    with postgresql_stand_in(driver, cursor_factory) as alias:
        coerced = coerce_field_value_or_none(field, value, alias=alias)
    assert coerced == (None if refused else expected)


@pytest.mark.pg
def test_coerce_field_value_or_none_refuses_a_malformed_address_on_postgresql() -> None:
    """PostgreSQL's ``inet`` adapter refuses ``abc``, so it names no row there."""
    coerced = coerce_field_value_or_none(_address_column(), "abc", alias=DEFAULT_DB_ALIAS)
    assert coerced is None


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("raw", "rows"),
    [
        pytest.param("1e1000000", [], id="huge-exponent"),
        pytest.param("1.5" + "0" * 20000, [Decimal("1.50")], id="huge-scale"),
    ],
)
def test_coerce_field_value_or_none_binds_a_decimal_key_on_postgresql(
    raw: str,
    rows: list[Decimal],
) -> None:
    """A decimal key PostgreSQL cannot bind as spelled filters by the value the column holds.

    The raw ``to_python`` value raises ``DataError`` in the ``pk__in`` query; the coerced
    one either names no row or is the stored ``1.50``, and the query runs.
    """
    with connection.schema_editor() as editor:
        editor.create_model(_DecimalKeyed)
    try:
        _DecimalKeyed.objects.create(code=Decimal("1.50"))
        _refused_raw_decimal(raw)
        coerced = coerce_field_value_or_none(_DecimalKeyed._meta.pk, raw, alias=DEFAULT_DB_ALIAS)
        found = (
            []
            if coerced is None
            else [row.code for row in _DecimalKeyed.objects.filter(pk__in=[coerced])]
        )
        assert found == rows
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_DecimalKeyed)


@pytest.mark.django_db
def test_expand_relation_order_spells_a_related_pk_as_its_key_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``"pk"`` inside a related ``Meta.ordering`` is spelled as that model's key column.

    ``SQLCompiler.find_ordering_name`` expands ``profile`` to ``PatronProfile``'s
    ordering and never expands the ``"pk"`` there. Spelled from ``Annotation`` as
    ``profile__pk`` it would end on the ``patron`` one-to-one key and expand again,
    to ``Patron.Meta.ordering``; the emails here run against the keys, so only the
    key column orders the rows as Django does.
    """
    for name, email in (
        ("Ada", "c@example.com"),
        ("Bo", "b@example.com"),
        ("Cy", "a@example.com"),
    ):
        patron = Patron.objects.create(name=name, email=email)
        Annotation.objects.create(profile=PatronProfile.objects.create(patron=patron), body=name)
    monkeypatch.setattr(PatronProfile._meta, "ordering", ["pk"])
    monkeypatch.setattr(Patron._meta, "ordering", ["email"])
    queryset = Annotation._base_manager.order_by("profile")

    expanded = expand_relation_order(["profile"], queryset.query)

    assert expanded == ["profile__patron_id"]
    django_order = [annotation.body for annotation in queryset]
    assert django_order == ["Ada", "Bo", "Cy"]
    assert [annotation.body for annotation in queryset.order_by(*expanded)] == django_order


@pytest.mark.django_db
def test_relation_write_visibility_boundary_is_controlled_by_type_registration() -> None:
    """Unregistered targets use their default manager; registered targets apply visibility."""
    seed_data(0)
    registry.clear()
    (category,) = categories_from_seed(("VisibilityBoundary", False))
    try:
        assert visible_related_objects(
            Category,
            [saved_pk(category)],
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        ) == {
            saved_pk(category): saved_pk(category),
        }

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                primary = True

            @classmethod
            @override
            def get_queryset(
                cls,
                queryset: models.QuerySet[Category],
                info: object,
            ) -> models.QuerySet[Category]:
                return queryset.exclude(pk=saved_pk(category))

        del CategoryType
        assert (
            visible_related_objects(
                Category,
                [saved_pk(category)],
                info=None,
                async_recourse=TEST_ASYNC_RECOURSE,
            )
            == {}
        )
    finally:
        registry.clear()


@pytest.mark.django_db
def test_visible_related_objects_reads_a_non_pk_key_beside_the_pk_in_one_query() -> None:
    """A relation keyed by another column reads it in the membership query; NULL links nothing.

    Each visible pk maps to the ``key_attname`` value a relation keyed by that column
    stores, read beside the pk in the one ``pk__in`` query. A row whose key is ``NULL``
    cannot be linked by it and is left out, the absence a hidden or missing row has.
    """
    registry.clear()
    keyed = NullableScalarSpecimen.objects.create(label="Keyed")
    unkeyed = NullableScalarSpecimen.objects.create(label=None)
    pks = [keyed.pk, unkeyed.pk]
    try:
        with CaptureQueriesContext(connection) as ctx:
            present = visible_related_objects(
                NullableScalarSpecimen,
                pks,
                info=None,
                key_attname="label",
                async_recourse=TEST_ASYNC_RECOURSE,
            )
        assert present == {keyed.pk: "Keyed"}
        assert len(ctx.captured_queries) == 1
        assert visible_related_objects(
            NullableScalarSpecimen,
            pks,
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        ) == {keyed.pk: keyed.pk, unkeyed.pk: unkeyed.pk}
    finally:
        registry.clear()


@pytest.mark.django_db
def test_linkable_rows_drops_null_keys_and_keeps_every_row_for_a_pk_key() -> None:
    """A relation keyed by a column links only rows whose key is set; a pk key links every row.

    ``key_attname`` ``None`` answers the queryset itself, so a pk-keyed read gains no
    predicate.
    """
    keyed = NullableScalarSpecimen.objects.create(label="Keyed")
    unkeyed = NullableScalarSpecimen.objects.create(label=None)
    queryset = NullableScalarSpecimen.objects.filter(pk__in=[keyed.pk, unkeyed.pk])

    assert linkable_rows(queryset, None) is queryset
    assert list(linkable_rows(queryset, "label").values_list("pk", flat=True)) == [keyed.pk]


@pytest.mark.django_db
def test_visible_related_object_answers_none_for_a_null_key_in_one_query() -> None:
    """A visible row whose stored key is ``NULL`` is ``None``, like a hidden or missing row.

    The predicate rides the one visibility query; with no ``key_attname`` the same row
    resolves.
    """
    registry.clear()
    keyed = NullableScalarSpecimen.objects.create(label="Keyed")
    unkeyed = NullableScalarSpecimen.objects.create(label=None)
    try:
        with CaptureQueriesContext(connection) as ctx:
            refused = visible_related_object(
                NullableScalarSpecimen,
                unkeyed.pk,
                None,
                key_attname="label",
                async_recourse=TEST_ASYNC_RECOURSE,
            )
        assert refused is None
        assert len(ctx.captured_queries) == 1
        assert (
            visible_related_object(
                NullableScalarSpecimen,
                keyed.pk,
                None,
                key_attname="label",
                async_recourse=TEST_ASYNC_RECOURSE,
            )
            == keyed
        )
        assert (
            visible_related_object(
                NullableScalarSpecimen,
                unkeyed.pk,
                None,
                async_recourse=TEST_ASYNC_RECOURSE,
            )
            == unkeyed
        )
    finally:
        registry.clear()


# ---------------------------------------------------------------------------
# apply_type_visibility_sync / _async -- the colored visibility routing
# ---------------------------------------------------------------------------


def test_apply_type_visibility_sync_runs_sync_get_queryset() -> None:
    """The sync path invokes ``get_queryset`` and returns its queryset."""
    base = Category.objects.all()
    result = apply_type_visibility_sync(
        _sync_type(),
        base,
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(result) is models.QuerySet
    assert _compiled_sql(result.query) == _compiled_sql(base.exclude(name="__never__").query)


def test_apply_type_visibility_sync_rejects_async_hook_loudly() -> None:
    """An ``async def`` ``get_queryset`` under the sync path raises ``SyncMisuseError``.

    The coroutine is closed before the raise (the ``filterwarnings = error``
    pytest config would fail the test on an unawaited-coroutine warning), and the
    typed marker is both a ``ConfigurationError`` and a ``RuntimeError``.
    """
    base = Category.objects.all()
    with pytest.raises(SyncMisuseError, match="returned a coroutine in a sync"):
        apply_type_visibility_sync(
            _AsyncType,
            base,
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )
    assert issubclass(SyncMisuseError, ConfigurationError)
    assert issubclass(SyncMisuseError, RuntimeError)


async def test_apply_type_visibility_async_awaits_async_hook() -> None:
    """The async runner awaits the hook and preserves the predicate it returns."""
    seen: list[models.QuerySet[Category]] = []

    async def hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        seen.append(queryset)
        return queryset.filter(name="awaited")

    base = Category.objects.all()
    result = await apply_type_visibility_async(_stub_type(Category, hook), base, info=None)
    assert len(seen) == 1
    assert seen[0] is not base
    assert type(result) is models.QuerySet
    assert _compiled_sql(result.query) == _compiled_sql(base.filter(name="awaited").query)


async def test_apply_type_visibility_async_runs_a_custom_sync_hook_off_the_event_loop() -> None:
    """A custom sync ``get_queryset`` runs in a worker thread and its queryset is used as is.

    The hook may read the database, which Django refuses on the event-loop thread.
    """
    threads: dict[str, int] = {"loop": threading.get_ident()}

    def _hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        threads["hook"] = threading.get_ident()
        return queryset.exclude(name="__never__")

    base = Category.objects.all()
    result = await apply_type_visibility_async(
        _declared_type(Category, "_WorkerHookType", _hook),
        base,
        info=None,
    )
    assert isinstance(result, models.QuerySet)
    assert threads["hook"] != threads["loop"]


def _unstamped_sync_type() -> type[DjangoType]:
    """A plain stand-in class with a sync ``get_queryset`` and no ``DjangoType`` default stamp."""

    def _hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset

    return _as_stand_in_hook_type(
        type(
            "_UnstampedSyncType",
            (),
            {
                "__django_strawberry_definition__": SimpleNamespace(model=Category),
                "get_queryset": classmethod(_hook),
            },
        ),
    )


@pytest.mark.parametrize(
    ("hook_kind", "expected_hops"),
    [
        pytest.param("identity-default", 0, id="identity-default-inline"),
        pytest.param("async-def", 0, id="async-def-awaited-on-loop"),
        pytest.param("custom-sync", 1, id="custom-sync-one-worker"),
        pytest.param("unstamped-sync", 1, id="unstamped-sync-one-worker"),
    ],
)
async def test_apply_type_visibility_async_hops_only_for_a_hook_that_may_do_io(
    monkeypatch: pytest.MonkeyPatch,
    hook_kind: str,
    expected_hops: int,
) -> None:
    """Only a synchronous hook the package cannot prove I/O-free pays the sync boundary.

    The identity default is stamped at class creation and runs inline; an
    ``async def`` hook is awaited on the loop; a custom sync hook, or one on a
    class carrying no stamp, runs in exactly one worker.
    """
    real_boundary = querysets_module.run_in_one_sync_boundary
    hops: list[Callable[..., object]] = []

    async def _counting_boundary(
        fn: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        hops.append(fn)
        return await real_boundary(fn, *args, **kwargs)

    monkeypatch.setattr(querysets_module, "run_in_one_sync_boundary", _counting_boundary)
    type_cls: type[DjangoType] = {
        "identity-default": lambda: _declared_type(Category, "_IdentityHookType"),
        "async-def": lambda: _AsyncType,
        "custom-sync": _sync_type,
        "unstamped-sync": _unstamped_sync_type,
    }[hook_kind]()

    result = await apply_type_visibility_async(type_cls, Category.objects.all(), info=None)

    assert isinstance(result, models.QuerySet)
    assert len(hops) == expected_hops


# ---------------------------------------------------------------------------
# run_in_one_sync_boundary -- the shared off-event-loop worker primitive
# ---------------------------------------------------------------------------


async def test_run_in_one_sync_boundary_runs_callable_off_event_loop() -> None:
    """The primitive executes ``fn`` on a worker thread, not the event-loop thread."""
    captured: dict[str, int] = {}

    def _body() -> str:
        captured["worker"] = threading.get_ident()
        return "ok"

    async def _run() -> str:
        captured["loop"] = threading.get_ident()
        return await run_in_one_sync_boundary(_body)

    assert await _run() == "ok"
    assert captured["worker"] != captured["loop"]


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- source preparation
# (the get_queryset-visibility-boundary decision)
# ---------------------------------------------------------------------------


def test_visibility_source_must_be_a_queryset() -> None:
    """A non-queryset source fails closed BEFORE the hook runs (fires no consumer code)."""

    def _boom(
        _cls: type,
        _queryset: models.QuerySet[Category],
        _info: object,
    ) -> NoReturn:  # must never run
        raise AssertionError("hook ran on an invalid source")

    with pytest.raises(ConfigurationError, match="requires a QuerySet of Category rows"):
        # basedpyright: the plain list is the hostile input under test; apply_type_visibility_sync
        # types the parameter as QuerySet[Model, object]
        apply_type_visibility_sync(
            _stub_type(Category, _boom),
            [1, 2],  # pyright: ignore[reportArgumentType]
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_visibility_source_must_use_registered_concrete_table() -> None:
    """A source over the wrong model fails closed - the hook would narrow the wrong table."""
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            _sync_type(),
            Item.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


@pytest.mark.django_db
def test_evaluated_source_is_refreshed_before_hook(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """An evaluated source is ``.all()``-refreshed before consumer code sees it - zero SQL.

    Cached rows must never reach (or bypass) the hook: the hook receives a
    fresh unevaluated clone, and the refresh itself composes lazily (the
    security carve-out from the optimizer's guarantee that a
    consumer-evaluated root queryset passes through unchanged, spec-035
    Decision 3).
    """
    seen: dict[str, object] = {}

    def _capture(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        seen["qs"] = queryset
        return queryset

    evaluated = Category.objects.all()
    list(evaluated)  # materialize the cache
    with django_assert_num_queries(0):
        result = apply_type_visibility_sync(
            _stub_type(Category, _capture),
            evaluated,
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )
    assert seen["qs"] is not evaluated
    assert isinstance(seen["qs"], models.QuerySet)
    assert seen["qs"]._result_cache is None
    assert result._result_cache is None


def test_active_write_pipeline_pins_source_and_repins_result() -> None:
    """An active nondefault write alias pins the hook input and its unpinned result."""
    received: list[str | None] = []

    def hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        received.append(queryset_db(queryset))
        return Category.objects.filter(name="x")

    with write_pipeline("archive", lock=False):
        result = apply_type_visibility_sync(
            _stub_type(Category, hook),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )
    assert received == ["archive"]
    assert queryset_db(result) == "archive"


def test_active_write_pipeline_rejects_divergent_source_alias() -> None:
    """An explicitly divergent SOURCE alias under a write pipeline fails closed (pre-pin)."""
    with (
        write_pipeline("default", lock=False),
        pytest.raises(ConfigurationError, match="routed to alias 'other'"),
    ):
        apply_type_visibility_sync(
            _sync_type(),
            Category.objects.using("other"),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


class _ProjectCategoryQuerySet(models.QuerySet[Category]):
    """A project queryset class with one method of its own, as a manager would declare."""

    def named(self, name: str) -> Self:
        """Narrow to the categories called ``name``."""
        return self.filter(name=name)


def _project_method_hook(
    seen: dict[str, object],
) -> Callable[[type, models.QuerySet[Category], object], models.QuerySet[Category]]:
    """A visibility hook that records its input and narrows through the project method."""

    def _hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        seen["qs"] = queryset
        return require_instance(queryset, _ProjectCategoryQuerySet).named("visible")

    return _hook


def test_hook_receives_the_sources_own_queryset_class() -> None:
    """The hook gets a clone of the source's own class, so a project method is callable.

    The input is a fresh instance (never the source object) carrying the source's
    predicate; the hook's result keeps its class too.
    """
    seen: dict[str, object] = {}
    source = _ProjectCategoryQuerySet(model=Category).filter(name__startswith="v")
    result = apply_type_visibility_sync(
        _stub_type(Category, _project_method_hook(seen)),
        source,
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(seen["qs"]) is _ProjectCategoryQuerySet
    assert seen["qs"] is not source
    assert type(result) is _ProjectCategoryQuerySet
    sql = str(result.query)
    assert "LIKE v%" in sql
    assert "= visible" in sql


async def test_async_hook_receives_the_sources_own_queryset_class() -> None:
    """The async runner hands the hook the source's own class too."""
    seen: dict[str, object] = {}
    source = _ProjectCategoryQuerySet(model=Category).filter(name__startswith="v")
    result = await apply_type_visibility_async(
        _stub_type(Category, _project_method_hook(seen)),
        source,
        info=None,
    )
    assert type(seen["qs"]) is _ProjectCategoryQuerySet
    assert seen["qs"] is not source
    assert type(result) is _ProjectCategoryQuerySet
    assert "= visible" in str(result.query)


def test_exact_queryset_source_reaches_the_hook_as_an_exact_queryset() -> None:
    """A plain ``QuerySet`` source stays a plain ``QuerySet`` at the hook."""
    seen: dict[str, object] = {}

    def _capture(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        seen["qs"] = queryset
        return queryset

    apply_type_visibility_sync(
        _stub_type(Category, _capture),
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(seen["qs"]) is models.QuerySet


def test_hook_returning_its_project_class_input_keeps_the_class() -> None:
    """A hook that returns its own project-class input gets a fresh clone of that class back."""
    source = _ProjectCategoryQuerySet(model=Category).filter(name="visible")
    result = apply_type_visibility_sync(
        _stub_type(Category, lambda _cls, queryset, _info: queryset),
        source,
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(result) is _ProjectCategoryQuerySet
    assert result is not source
    assert "= visible" in str(result.query)


def test_project_class_clone_keeps_the_sources_query_state() -> None:
    """The class-keeping clone carries filters, annotations, ordering, routing and prefetch."""
    seen: dict[str, object] = {}

    def _capture(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        seen["qs"] = queryset
        return queryset

    source = (
        _ProjectCategoryQuerySet(model=Category)
        .using("other")
        .filter(name__startswith="a")
        .annotate(flag=models.Value(1))
        .order_by("-name")
        .prefetch_related("items")
    )
    apply_type_visibility_sync(
        _stub_type(Category, _capture),
        source,
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    received = require_instance(seen["qs"], _ProjectCategoryQuerySet)
    assert "flag" in received.query.annotations
    assert received.query.order_by == ("-name",)
    assert "LIKE a%" in str(received.query)
    assert queryset_db(received) == "other"
    assert queryset_prefetch_lookups(received) == ("items",)


def test_project_class_projection_source_still_fails_closed() -> None:
    """Keeping the class admits nothing new: a ``.values()`` project source is refused."""
    with pytest.raises(ConfigurationError, match="projection"):
        apply_type_visibility_sync(
            _sync_type(),
            _ProjectCategoryQuerySet(model=Category).values("id"),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_active_write_pipeline_pins_a_project_class_source() -> None:
    """Under a write pipeline the project-class input is pinned and keeps its class."""
    seen: dict[str, object] = {}

    def _capture(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        seen["qs"] = queryset
        return queryset

    with write_pipeline("archive", lock=False):
        result = apply_type_visibility_sync(
            _stub_type(Category, _capture),
            _ProjectCategoryQuerySet(model=Category),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )
    received = require_instance(seen["qs"], _ProjectCategoryQuerySet)
    assert queryset_db(received) == "archive"
    assert queryset_db(result) == "archive"


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- hook-result normalization
# ---------------------------------------------------------------------------


def _sync_hook_type(result: object) -> type[DjangoType]:
    """A Category stub type whose hook returns ``result`` verbatim."""
    return _stub_type(Category, lambda _cls, _qs, _info: result)


def test_hook_manager_result_is_coerced_sync() -> None:
    """A Manager hook result is read once and its exact queryset predicate is preserved."""
    calls: list[str] = []

    class ScopedManager(models.Manager[Category]):
        @override
        def all(self) -> models.QuerySet[Category]:
            calls.append("all")
            return Category.objects.filter(name="managed")

    manager = ScopedManager()
    manager.model = Category
    result = apply_type_visibility_sync(
        _sync_hook_type(manager),
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert calls == ["all"]
    assert type(result) is models.QuerySet
    assert result.model is Category
    assert _compiled_sql(result.query) == _compiled_sql(
        Category.objects.filter(name="managed").query,
    )


async def test_hook_manager_result_is_coerced_async() -> None:
    """An async-path ``Manager`` return is coerced too, never passed through verbatim."""

    @_as_stand_in_hook_type
    class _ManagerAsyncType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(
            cls,
            _queryset: models.QuerySet[Category],
            _info: object,
        ) -> models.Manager[Category]:
            return Category.objects

    result = await apply_type_visibility_async(
        _ManagerAsyncType,
        Category.objects.all(),
        info=None,
    )
    assert isinstance(result, models.QuerySet)


def _async_generator_result() -> AsyncIterator[int]:
    async def _agen() -> AsyncIterator[int]:
        yield 1  # never iterated

    return _agen()


@pytest.mark.parametrize(
    ("bad", "detail"),
    [
        (None, "NoneType"),
        ([], "list"),
        ((n for n in ()), "generator"),
        (_async_generator_result(), "async_generator"),
        (object(), "object"),
    ],
)
def test_invalid_hook_results_fail_closed(bad: object, detail: str) -> None:
    """``None`` / list / generator / async-generator / custom-iterable returns fail closed."""
    with pytest.raises(
        ConfigurationError,
        match=f"must return a QuerySet or Manager.*got {detail}",
    ):
        apply_type_visibility_sync(
            _sync_hook_type(bad),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_wrong_model_hook_result_fails_closed() -> None:
    """A queryset over an unrelated model fails closed (wrong concrete table)."""
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            _sync_hook_type(Item.objects.all()),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_mti_child_hook_result_fails_closed() -> None:
    """An MTI-child queryset lives on ITS OWN concrete table - incompatible.

    ``apps/library/models.py::LendingDesk`` extends ``Venue`` with a table of
    its own, so a ``Venue`` hook answering with desk rows reads the wrong table.
    """
    hook = _stub_type(Venue, lambda _cls, _qs, _info: LendingDesk.objects.all())
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            hook,
            Venue.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_proxy_hook_result_is_accepted() -> None:
    """A proxy-sibling queryset shares the concrete table and passes the boundary.

    ``apps/library/models.py::OpenVenue`` is a proxy of ``Venue``, the same base
    whose concrete ``LendingDesk`` child the test above refuses.
    """
    hook = _stub_type(Venue, lambda _cls, _qs, _info: OpenVenue.objects.all())
    result = apply_type_visibility_sync(
        hook,
        Venue.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert result.model is OpenVenue


def test_unpinned_result_is_repinned_to_explicit_source_alias() -> None:
    """A routed source's alias is required: an unpinned hook result is normalized onto it.

    Alias-state only - the alias never resolves a connection, so no secondary
    database is needed.
    """
    hook = _stub_type(Category, lambda _cls, _qs, _info: Category.objects.filter(name="x"))
    result = apply_type_visibility_sync(
        hook,
        Category.objects.using("other"),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert queryset_db(result) == "other"


def test_matching_explicit_result_alias_is_accepted() -> None:
    """A hook result explicitly routed to the required alias passes through."""
    result = apply_type_visibility_sync(
        _sync_type(),
        Category.objects.using("other").all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert queryset_db(result) == "other"


def test_divergent_explicit_result_alias_fails_closed() -> None:
    """A hook result explicitly routed OFF the required alias fails closed."""
    hook = _stub_type(Category, lambda _cls, _qs, _info: Category.objects.using("elsewhere"))
    with pytest.raises(
        ConfigurationError,
        match=r"routed to alias 'elsewhere'.*pinned to alias 'other'",
    ):
        apply_type_visibility_sync(
            hook,
            Category.objects.using("other"),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_unpinned_read_hook_keeps_documented_alias_routing() -> None:
    """With no required alias, an unpinned read hook may still choose ``.using(alias)`` itself."""
    hook = _stub_type(Category, lambda _cls, qs, _info: qs.using("other"))
    result = apply_type_visibility_sync(
        hook,
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert queryset_db(result) == "other"


@pytest.mark.django_db
def test_evaluated_hook_result_is_refreshed(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """An evaluated hook result is re-cloned so cached rows never survive the boundary."""
    evaluated = Category.objects.all()
    list(evaluated)
    with django_assert_num_queries(0):
        result = apply_type_visibility_sync(
            _sync_hook_type(evaluated),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )
    assert result is not evaluated
    assert result._result_cache is None


def test_normalization_preserves_lazy_query_state() -> None:
    """Sealing preserves lazy query state: filters / annotations / ordering survive.

    The sealed queryset is a fresh clone of the hook's result, of its own class,
    carrying every piece of SQL state that decides which rows are selected - the
    filter, the annotation, the ordering.
    """

    class _CustomQuerySet(models.QuerySet[Category]):
        pass

    shaped = (
        _CustomQuerySet(model=Category)
        .filter(name__startswith="a")
        .annotate(flag=models.Value(1))
        .order_by("-name")
    )
    result = apply_type_visibility_sync(
        _sync_hook_type(shaped),
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(result) is _CustomQuerySet
    assert result is not shaped
    assert "flag" in result.query.annotations
    assert result.query.order_by == ("-name",)
    assert "a" in str(result.query)  # the startswith filter survived


def test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked() -> None:
    """A SUBCLASS result carrying a pending ``_deferred_filter`` seals with it baked.

    Django's related-manager machinery leaves the pending ``(negate, args,
    kwargs)`` tuple on whatever class the model's manager builds its querysets
    from. The seal's clone reads ``QuerySet.query``, which bakes it, so the
    predicate lands in the compiled SQL of the subclass's own clone.
    """

    class _DeferredSub(models.QuerySet[Category]):
        pass

    result = _DeferredSub(model=Category)
    truth.instance_state(result)["_deferred_filter"] = (False, (), {"name": "later"})
    hook = _sync_hook_type(result)
    sealed = apply_type_visibility_sync(
        hook,
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(sealed) is _DeferredSub
    sql_str, params = _compiled_sql(sealed.query)
    assert "name" in sql_str
    assert "later" in params


def test_exact_queryset_pending_deferred_filter_is_resolved() -> None:
    """An EXACT plain ``QuerySet`` carrying a pending ``_deferred_filter`` seals cleanly.

    Django's ``RelatedManager._apply_rel_filters`` leaves the relation predicate as
    a pending ``_deferred_filter`` that is only baked into ``_query`` on first
    ``.query`` access, so ``instance.rel.all()`` reaches the seal with the flag set.
    The seal's clone reads Django's ``query`` getter, which bakes the predicate, so
    it lands in the sealed SQL.
    """
    result = Category.objects.all()
    truth.instance_state(result)["_deferred_filter"] = (False, (), {"name": "later"})
    sealed, defect = _seal_or_defect(result, Category, None)
    assert defect is None
    assert sealed is not None
    assert sealed is not result
    sql_str, params = _compiled_sql(sealed.query)
    assert "name" in sql_str
    assert "later" in params


def test_a_value_whose_class_property_raises_is_a_typed_seal_defect() -> None:
    """The admission test itself must not dispatch the candidate's own code.

    ``isinstance(candidate, QuerySet)`` falls back to the candidate's
    ``__class__`` when the real type does not match, and that is a consumer
    property on an arbitrary object: it can claim to be a queryset, or raise
    straight out of the shape proof the boundary exists to fail closed. The real
    type answers instead, so a value that cannot be one is the typed ``type``
    defect every other unusable shape is.
    """

    class _RaisingClass(ClassReadRaisesBase):
        pass

    sealed, defect = _seal_or_defect(_RaisingClass(message="class bomb"), Category, None)
    assert sealed is None
    assert defect == ("type", "_RaisingClass")


def test_a_value_that_only_claims_to_be_a_queryset_is_a_typed_seal_defect() -> None:
    """A ``__class__`` that names ``QuerySet`` does not make a value one."""

    class _ClaimsToBeAQuerySet(ClaimsClassBase):
        claimed = models.QuerySet

    candidate = _ClaimsToBeAQuerySet()
    assert isinstance(candidate, models.QuerySet)
    sealed, defect = _seal_or_defect(candidate, Category, None)
    assert sealed is None
    assert defect == ("type", "_ClaimsToBeAQuerySet")


class _TermChoices(models.TextChoices):
    """Names and SQL a hook spells through ``TextChoices`` members."""

    TITLE = "title"
    DESCENDING_TITLE = "-title"
    LATER_TITLES = "library_book.title >= 'B'"
    TITLE_PARAMETER = "B"
    BRANCH_TABLE = "library_branch"
    HEADLINE = "headline"
    SHELVED = "shelved"
    DEFAULT = "default"
    GENRES = "genres"
    TITLE_COLUMN = "library_book.title"
    UPPER = "UPPER"
    TEMPLATE = "%(function)s(%(expressions)s)"
    JOINER = ", "
    PLUS = "+"
    PRECISION = "precision"
    CATEGORY_TABLE = "products_category"
    OTHER_TABLE = "products_item"
    DISJUNCTION = "OR"


#: The same terms as ``enum.StrEnum`` members.
_TermEnum = STR_ENUM(
    "_TermEnum",
    {name: str(member) for name, member in _TermChoices.__members__.items()},
)


def _term(kind: str, name: str) -> str:
    """``name``'s term as a ``TextChoices`` or a ``StrEnum`` member, or as exact ``text``."""
    member = read_attr(_TermChoices if kind == "text-choices" else _TermEnum, name)
    assert is_str(member)
    return str.__str__(member) if kind == "text" else member


@pytest.mark.django_db
def test_related_manager_queryset_seals_and_scopes_to_its_parent() -> None:
    """A related-manager queryset seals and its baked relation predicate is preserved.

    ``instance.rel.all()`` reaches the seal as an EXACT plain ``QuerySet`` whose
    relation predicate is still a pending ``_deferred_filter``; the seal's clone
    bakes it, so the queryset selects ONLY the parent's children. Two
    parents each get a child; sealing parent A's ``items.all()`` and evaluating it
    must return A's child alone (a lost predicate would leak B's child too).
    """
    seed_data(1)
    parent_a, parent_b = categories_from_seed(("RelParentA", False), ("RelParentB", False))
    (item_a,) = items_from_seed(parent_a, ("ChildA", False))
    items_from_seed(parent_b, ("ChildB", False))
    sealed, defect = _seal_or_defect(parent_a.items.all(), Item, None)
    assert defect is None
    assert type(sealed) is models.QuerySet
    assert list(sealed) == [item_a]


def test_values_projection_result_fails_closed_on_read_surface() -> None:
    """A hook returning a ``.values()`` projection fails closed on a read surface.

    A read surface composes over model rows; a ``.values()`` return yields dicts,
    not ``Category`` instances. ``require_model_rows`` (the default) rejects it.
    """
    hook = _sync_hook_type(Category.objects.values("name"))
    with pytest.raises(ConfigurationError, match="the visibility contract composes over"):
        apply_type_visibility_sync(
            hook,
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_values_projection_source_fails_closed_on_read_surface() -> None:
    """A ``.values()`` SOURCE is rejected on a read surface before the hook runs."""
    with pytest.raises(ConfigurationError, match="the visibility contract composes over"):
        apply_type_visibility_sync(
            _sync_type(),
            Category.objects.values("name"),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_baked_alias_map_matching_table_is_accepted() -> None:
    """A queryset whose alias map is already baked against the CORRECT table passes.

    The base-table check reads the frozen alias map; when it agrees with the
    registered model's concrete table there is no defect. Baking composes lazy
    query state only; no SQL runs.
    """
    baked = Category.objects.all()
    baked.query.get_initial_alias()  # freeze the alias map against Category's table
    result = apply_type_visibility_sync(
        _sync_hook_type(baked),
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert result.model is Category


def test_cross_model_union_source_fails_closed() -> None:
    """A cross-model ``union()`` SOURCE (not just a hook return) fails closed.

    The recursive branch check inspects the source too: a union whose branch
    reads ``Item``'s table cannot seed a ``Category`` visibility resolution.
    """
    hostile = Category.objects.all().union(Item.objects.all())
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            _sync_type(),
            hostile,
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_manager_result_degrading_to_list_fails_closed() -> None:
    """A hook returning a Manager whose ``.all()`` yields a list fails closed (never a bypass)."""

    class _ListManager(models.Manager[Category]):
        @override
        # basedpyright: deliberately degrades ``all()`` into a list, the bypass shape the guard refuses
        def all(self) -> list[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return ["secret"]

    manager = _ListManager()
    manager.model = Category
    manager._db = None
    with pytest.raises(ConfigurationError, match="must produce a QuerySet"):
        apply_type_visibility_sync(
            _sync_hook_type(manager),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_manager_all_exception_propagates_through_coercion() -> None:
    """The Manager's own ``all()`` is consumer code: what it raises propagates unchanged.

    The routing read beside it comes from the manager's instance namespace, so the
    hostile ``_db`` hook runs only inside ``all()``.
    """

    class _HostileManager(models.Manager[Category]):
        @override
        def __getattribute__(self, name: str) -> object:
            if name == "_db":
                raise RuntimeError("hostile manager routing read")
            return object_result(super().__getattribute__, name)

    manager = _HostileManager()
    manager.model = Category
    with pytest.raises(RuntimeError, match="hostile manager routing read"):
        normalize_query_source(manager)


@pytest.mark.django_db
def test_clean_queryset_transforms_after_seal() -> None:
    """A clean (unshadowed) queryset seals fine and keeps composing post-seal.

    The complement of the fail-closed shadow tests: once sealed, an ordinary
    queryset still transforms normally -- ``values_list`` keeps the visibility
    predicate and serves only the visible rows.
    """
    seed_data(0)
    categories_from_seed(("visible_row", False), ("hidden_row", True))
    result = apply_type_visibility_sync(
        _sync_hook_type(Category.objects.filter(is_private=False)),
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert "is_private" in str(result.values_list("name").query)
    assert sorted(result.values_list("name", flat=True)) == ["visible_row"]


def test_a_subclass_result_comes_back_as_a_clone_of_its_class() -> None:
    """A hook result of a project subclass comes back as a fresh clone of that class.

    The clone is never the hook's object, so its project methods stay callable on
    what the surface composes onto, and the SQL predicate is preserved.
    """

    class _AddOnly(models.QuerySet[Category]):
        def published(self) -> Self:  # additive only
            return self.filter(name="published")

    shaped = _AddOnly(model=Category).filter(name="ok")
    result = apply_type_visibility_sync(
        _sync_hook_type(shaped),
        Category.objects.all(),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert type(result) is _AddOnly
    assert result is not shaped
    assert "published" in str(result.published().query)
    assert "ok" in str(result.query)


def test_hook_exception_propagates_unchanged() -> None:
    """An exception raised INSIDE the hook propagates as-is - the boundary never masks it."""

    class _BoomError(RuntimeError):
        pass

    def _raise(_cls: type, _queryset: models.QuerySet[Category], _info: object) -> NoReturn:
        raise _BoomError("consumer bug")

    with pytest.raises(_BoomError, match="consumer bug"):
        apply_type_visibility_sync(
            _stub_type(Category, _raise),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- objects embedded in the query graph
# consumer objects can ride through the seal one edge down: a ``Prefetch``
# queryset and a combinator-branch ``Query`` subclass
# ---------------------------------------------------------------------------


def _identity_hook_type() -> type[DjangoType]:
    """A Category stub whose hook returns its argument (the sealed source) verbatim."""
    return _stub_type(Category, lambda _cls, queryset, _info: queryset)


def test_string_and_default_prefetch_lookups_pass_through() -> None:
    """Plain string lookups and a ``Prefetch`` with no queryset seal through unchanged.

    Only a ``Prefetch`` carrying a consumer queryset is a dispatch vector; a bare
    string lookup (Django builds the related queryset itself) and a
    ``Prefetch(queryset=None)`` carry no consumer code, so they pass through.
    """
    source = Category.objects.all().prefetch_related("items", Prefetch("items"))
    sealed = apply_type_visibility_sync(
        _identity_hook_type(),
        source,
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    string_lookup, default_prefetch = queryset_prefetch_lookups(sealed)
    assert string_lookup == "items"
    assert isinstance(default_prefetch, Prefetch)
    assert default_prefetch.queryset is None


def test_sliced_source_fails_closed_with_typed_error() -> None:
    """A pre-sliced SOURCE fails closed with a typed ConfigurationError, not a raw TypeError.

    The hook and surface compose further filters / ordering onto the source, and
    Django forbids refiltering or reordering a sliced query. Without this check
    the next transform would raise a raw ``TypeError`` outside the typed defect
    contract (the cascade already rejects a sliced target subquery).
    """
    with pytest.raises(ConfigurationError, match="sliced"):
        apply_type_visibility_sync(
            _sync_type(),
            Category.objects.all()[:5],
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


def test_sliced_hook_result_fails_closed_with_typed_error() -> None:
    """A hook returning a pre-sliced queryset fails closed with a typed error."""
    hook = _sync_hook_type(Category.objects.filter(name="visible")[:3])
    with pytest.raises(ConfigurationError, match="sliced"):
        apply_type_visibility_sync(
            hook,
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


@pytest.mark.django_db
def test_identity_hook_result_is_resealed_dropping_injected_cache_sync() -> None:
    """A hook that mutates the received source's ``_result_cache`` and returns it is re-sealed.

    Object identity is not immutability (spec-045 Decision 3): a hook can inject
    a synthetic unsaved row into the sealed source's ``_result_cache`` and return
    the SAME object, which an identity fast path would serve with zero SQL. The
    result is ALWAYS re-sealed, so the returned queryset has
    ``_result_cache is None`` and only the real visible rows survive on evaluation.
    """
    seed_data(0)
    categories_from_seed(("visible_row", False))

    def _hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        queryset._result_cache = [Category(name="synthetic-hidden", is_private=True)]
        return queryset

    result = apply_type_visibility_sync(
        _stub_type(Category, _hook),
        Category.objects.filter(is_private=False),
        info=None,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert result._result_cache is None
    assert sorted(row.name for row in _rows_of(Category, result)) == ["visible_row"]


def test_clean_annotation_and_select_related_seal_fine() -> None:
    """A plain Django annotation + ``select_related`` dict tree seals with no defect.

    The complement of the fail-closed AST tests: trusted Django nodes (a ``Count``
    annotation, a ``{str: {}}`` select_related tree) pass the graph validation.
    """
    source = Item.objects.select_related("category").annotate(n=models.Count("id"))
    sealed, defect = _seal_or_defect(source, Item, None)
    assert defect is None
    assert type(sealed) is models.QuerySet


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- awaitable discipline
# ---------------------------------------------------------------------------


class _AwaitableOf:
    """A custom (non-coroutine) awaitable resolving to a fixed value."""

    def __init__(self, value: object) -> None:
        self.value = value

    def __await__(self) -> Generator[None, None, object]:
        yield from ()  # resolves without suspending
        return self.value


def test_sync_boundary_rejects_custom_awaitable_hook() -> None:
    """A custom awaitable at the sync boundary raises ``SyncMisuseError`` (not a coroutine)."""
    hook = _stub_type(Category, lambda _cls, qs, _info: _AwaitableOf(qs))
    with pytest.raises(SyncMisuseError, match="returned an awaitable in a sync"):
        apply_type_visibility_sync(
            hook,
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


async def test_async_custom_awaitable_hook_is_awaited_once() -> None:
    """The async runner awaits a custom awaitable hook return to its queryset."""
    hook = _stub_type(Category, lambda _cls, qs, _info: _AwaitableOf(qs))
    result = await apply_type_visibility_async(hook, Category.objects.all(), info=None)
    assert isinstance(result, models.QuerySet)


async def test_async_nested_awaitable_fails_closed() -> None:
    """An async hook resolving to ANOTHER awaitable fails closed after exactly one await."""

    @_as_stand_in_hook_type
    class _NestedType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(
            cls,
            queryset: models.QuerySet[Category],
            _info: object,
        ) -> Awaitable[models.QuerySet[Category]]:
            async def _inner() -> models.QuerySet[Category]:
                return queryset  # disposed, never awaited

            return _inner()

    with pytest.raises(ConfigurationError, match="nested awaitable"):
        await apply_type_visibility_async(_NestedType, Category.objects.all(), info=None)


async def test_async_generator_hook_result_fails_closed() -> None:
    """An async hook resolving to an async generator is not awaitable - a type rejection."""

    @_as_stand_in_hook_type
    class _AgenType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(
            cls,
            _queryset: models.QuerySet[Category],
            _info: object,
        ) -> AsyncIterator[int]:
            return _async_generator_result()

    with pytest.raises(ConfigurationError, match="got async_generator"):
        await apply_type_visibility_async(_AgenType, Category.objects.all(), info=None)


@pytest.mark.django_db(transaction=True)
async def test_identity_hook_result_is_resealed_dropping_injected_cache_async() -> None:
    """Sync/async parity: the async runner also re-seals an identity return.

    An async hook injects a synthetic unsaved row into the received sealed
    source's ``_result_cache`` and returns the SAME object; the async runner
    re-seals it, dropping the cache, so only the real visible row survives.
    """
    await sync_to_async(seed_data)(0)
    await sync_to_async(categories_from_seed)(("visible_row", False))

    @_as_stand_in_hook_type
    class _CaptureAsyncType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(
            cls,
            queryset: models.QuerySet[Category],
            _info: object,
        ) -> models.QuerySet[Category]:
            queryset._result_cache = [Category(name="synthetic-hidden", is_private=True)]
            return queryset

    result = await apply_type_visibility_async(
        _CaptureAsyncType,
        Category.objects.filter(is_private=False),
        info=None,
    )
    assert result._result_cache is None
    names = [row.name for row in _rows_of(Category, [row async for row in result])]
    assert names == ["visible_row"]


def test_module_spoofed_type_is_not_genuine_django() -> None:
    """``__module__`` is spoofable, so provenance is proven by object identity.

    A consumer class declaring ``__module__ = "django.db.models.functions"`` is NOT
    the object Django exposes at ``sys.modules[module].<qualname>``, so identity
    provenance rejects it where a ``__module__.startswith("django.")`` check would
    accept it.
    """

    class _SpoofFunc(models.Func):
        pass

    _SpoofFunc.__module__ = "django.db.models.functions"
    assert _type_is_genuinely_django(_SpoofFunc) is False
    # And a genuine Django expression type is still accepted.
    assert _type_is_genuinely_django(models.Value) is True


def test_deferred_plain_model_instance_still_seals() -> None:
    """A plain model instance (no expression protocol) remains a valid reverse-rel value.

    This is exactly the ``RelatedManager._apply_rel_filters`` shape: ``category.items``
    ``.all()`` leaves a deferred ``{"category": <Category instance>}`` filter on an
    ``Item`` queryset. The instance carries no ``resolve_expression``, so Django
    extracts its pk to a bound parameter; the bake resolves against ``Item``'s real
    ``category`` FK and seals cleanly.
    """
    result = Item.objects.all()
    truth.instance_state(result)["_deferred_filter"] = (
        False,
        (),
        {"category": Category(name="p", pk=7)},
    )
    sealed, defect = _seal_or_defect(result, Item, None)
    assert defect is None
    assert sealed is not None


def test_extra_order_by_none_and_string_sequence_seal() -> None:
    """A ``None`` or all-string ``extra_order_by`` seals -- the raw-SQL slot is accepted."""
    none_source = Category.objects.all()
    str(none_source.query)
    # basedpyright: a None extra_order_by is the slot shape under test; django-stubs types the slot
    # as a sequence of order-by names
    none_source.query.extra_order_by = None  # pyright: ignore[reportAttributeAccessIssue]
    sealed, defect = _seal_or_defect(none_source, Category, None)
    assert defect is None
    assert sealed is not None

    str_source = Category.objects.all()
    str(str_source.query)
    str_source.query.extra_order_by = ("name",)
    sealed, defect = _seal_or_defect(str_source, Category, None)
    assert defect is None
    assert sealed is not None


def _filtered_relation_join() -> tuple[models.QuerySet[Category], str, BaseTable | Join]:
    """Return a genuine ``Join`` carrying a resolved ``filtered_relation`` (compiled)."""
    frq = Category.objects.annotate(
        vi=FilteredRelation("items", condition=Q(items__name="keep")),
    ).filter(vi__name="keep")
    _compiled_sql(frq.query)  # populate alias_map + resolved_condition
    for alias, join in frq.query.alias_map.items():
        if getattr(join, "filtered_relation", None) is not None:
            return frq, alias, join
    raise AssertionError("no filtered_relation join was produced")


def test_legit_filtered_relation_seals_byte_identical() -> None:
    """A legitimate ``FilteredRelation`` query seals and compiles to identical SQL."""
    frq, _alias, _join = _filtered_relation_join()
    expected_sql, expected_params = _compiled_sql(frq.query)
    sealed, defect = _seal_or_defect(frq, Category, None)
    assert defect is None
    assert sealed is not None
    got_sql, got_params = _compiled_sql(sealed.query)
    assert got_sql == expected_sql
    assert list(got_params) == list(expected_params)


def test_module_spoofing_metaclass_is_not_invoked_and_fails_closed() -> None:
    """Provenance reads ``__module__`` / ``__qualname__`` via ``type.__getattribute__``.

    A consumer metaclass overriding ``__getattribute__`` would otherwise run during the
    provenance read that is meant to reject the type; ``type.__getattribute__`` resolves
    both names without dispatching the metaclass hook.
    """
    fired: list[str] = []

    class _NoisyMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:  # must never run for provenance
            fired.append(name)
            return object_result(super().__getattribute__, name)

    class _NoisyType(metaclass=_NoisyMeta):
        __module__ = "django.db.models.functions"

    assert _type_is_genuinely_django(_NoisyType) is False
    assert fired == []
    assert _type_is_genuinely_django(models.Value) is True


def test_provenance_of_type_with_raising_module_descriptor_fails_closed() -> None:
    """A metaclass whose ``__module__`` descriptor raises fails closed, not errors.

    ``type.__getattribute__`` still consults a metaclass DATA descriptor, so a hostile
    ``__module__`` property that raises would propagate past the typed contract; the
    provenance read catches it and fails closed.
    """

    class _RaisingMeta(type):
        @property
        @override
        # basedpyright: the hostile shape under test, a ``__module__`` property whose read raises;
        # the checker rejects any property overriding a base class attribute
        def __module__(cls) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
            raise AttributeError("no module")

    class _Raiser(metaclass=_RaisingMeta):
        pass

    assert _type_is_genuinely_django(_Raiser) is False


def test_none_hints_seals_to_fresh_dict() -> None:
    """A ``None`` ``_hints`` seals to a fresh empty dict rather than erroring."""
    source = Category.objects.all()
    str(source.query)
    # basedpyright: plants a ``None`` ``_hints``, which Django never stores (it writes ``{}``)
    set_queryset_hints(source, None)  # pyright: ignore[reportArgumentType]
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    assert queryset_hints(sealed) == {}


def test_concrete_or_none_rejects_the_abstract_model_base() -> None:
    """``models.Model`` itself carries no ``_meta``, so it resolves to no concrete model."""
    assert _concrete_or_none(models.Model) is None


def test_shared_combined_query_branch_is_validated_once() -> None:
    """The same branch object listed twice is a shared reference, not a cycle."""
    source = Category.objects.filter(is_private=False)
    branch = Category.objects.filter(is_private=False).query
    str(source.query)
    str(branch)
    source.query.combined_queries = (branch, branch)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None


def test_sealed_queryset_keeps_its_predicate_through_filter_composition() -> None:
    """Post-seal filtering compiles the same predicates and values as ordinary Django."""
    source = Category.objects.filter(is_private=False)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    composed = sealed.filter(name="visible")
    oracle = Category.objects.filter(is_private=False, name="visible")
    assert composed.query.sql_with_params() == oracle.query.sql_with_params()
    assert composed.query.where.children


@pytest.mark.django_db
def test_trunc_tzinfo_is_retained_and_rows_survive() -> None:
    """Exact stdlib timezone objects are retained by reference and cost no rows.

    ``Trunc(..., tzinfo=zoneinfo.ZoneInfo(...))`` and ``tzinfo=datetime.timezone.utc``
    are ordinary consumer annotations; the seal must keep the timezone (an immutable
    interpreter-owned value) and the annotated queryset must still return its rows.
    """
    seed_data(0)
    categories_from_seed(("tz_row", False))
    tz = zoneinfo.ZoneInfo("UTC")
    source = Category.objects.filter(is_private=False).annotate(
        day=Trunc("created_date", "day", tzinfo=tz),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    assert isinstance(sealed.query.annotations["day"], Trunc)
    assert read_attr(sealed.query.annotations["day"], "tzinfo") is tz
    assert [row.name for row in _rows_of(Category, sealed)] == ["tz_row"]

    source = Category.objects.filter(is_private=False).annotate(
        day=Trunc("created_date", "day", tzinfo=datetime.timezone.utc),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    assert isinstance(sealed.query.annotations["day"], Trunc)
    assert read_attr(sealed.query.annotations["day"], "tzinfo") is datetime.timezone.utc
    assert [row.name for row in _rows_of(Category, sealed)] == ["tz_row"]


@pytest.mark.django_db
def test_value_payload_literals_seal_and_rows_survive() -> None:
    """Ordinary ``Value`` literals seal and the annotated queryset still returns rows."""
    seed_data(0)
    categories_from_seed(("lit_row", False))
    source = Category.objects.filter(is_private=False).annotate(
        flag=models.Value(1),
        label=models.Value("x"),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    rows = _rows_of(Category, sealed)
    assert [row.name for row in rows] == ["lit_row"]
    # basedpyright: annotate() sets the annotation on each row at run time; the model class does
    # not declare it
    annotated: dict[str, object] = vars(rows[0])
    assert annotated["flag"] == 1
    assert annotated["label"] == "x"


def test_type_is_genuinely_django_absent_module_fails_closed() -> None:
    """A ``__module__`` naming a ``django.`` module absent from ``sys.modules`` fails closed."""

    class _Spoof:
        pass

    _Spoof.__module__ = "django.this_module_does_not_exist_zzz"
    _Spoof.__qualname__ = "Spoof"
    assert _type_is_genuinely_django(_Spoof) is False


def test_concrete_model_probe_never_runs_a_metaclass_meta_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A metaclass ``_meta`` hook never runs: the probe reads the real class namespace.

    A model class whose metaclass raises on ``_meta`` is malformed by
    construction, so no fakeshop model can carry it; ``_HostileModel`` alone
    shows ``django_strawberry_framework/utils/querysets.py::_concrete_or_none``
    answering the real concrete model past the hook.
    """
    model_base = type(models.Model)

    class _HostileModelBase(model_base):
        @override
        def __getattribute__(self, name: str) -> object:
            if name == "_meta" and type.__getattribute__(self, "_hostile_meta"):
                raise RuntimeError("model metadata exploded")
            return object_result(super().__getattribute__, name)

    class _HostileModel(models.Model, metaclass=_HostileModelBase):
        _hostile_meta = False

        class Meta:
            app_label = "test_querysets_hostile_meta"
            managed = False

    monkeypatch.setattr(_HostileModel, "_hostile_meta", True)

    assert _concrete_or_none(_HostileModel) is _HostileModel


class _AsyncOnlyIterable:
    """An async-only iterable: ``__aiter__`` with no ``__iter__`` (no cleanup debt)."""

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> object:
        raise StopAsyncIteration


def test_is_async_only_iterable_arms() -> None:
    """The async-only predicate: AsyncIterable without Iterable; a QuerySet is BOTH."""
    assert is_async_only_iterable(_AsyncOnlyIterable()) is True
    assert is_async_only_iterable(Category.objects.all()) is False
    assert is_async_only_iterable([1, 2]) is False
    assert is_async_only_iterable(None) is False


def test_reject_async_iterable_in_sync_context_names_the_flavor() -> None:
    """An async-only source under sync execution raises SyncMisuseError naming the flavor."""
    with pytest.raises(SyncMisuseError, match="A DjangoListField resolver returned"):
        reject_async_iterable_in_sync_context(
            _AsyncOnlyIterable(),
            flavor_noun="DjangoListField",
            async_executor=False,
        )
    with pytest.raises(SyncMisuseError, match="A connection resolver returned"):
        reject_async_iterable_in_sync_context(
            _AsyncOnlyIterable(),
            flavor_noun="connection",
            async_executor=False,
        )


def test_reject_async_iterable_in_sync_context_passes_sync_sources() -> None:
    """Sync-iterable sources (lists, QuerySets) pass through untouched."""
    reject_async_iterable_in_sync_context(
        [1, 2],
        flavor_noun="connection",
        async_executor=False,
    )
    reject_async_iterable_in_sync_context(
        Category.objects.none(),
        flavor_noun="connection",
        async_executor=False,
    )


async def test_reject_async_iterable_in_sync_context_noop_under_async_execution() -> None:
    """Under the async executor the guard is a no-op: that executor consumes the source.

    The verdict is the CALLER's, so the row states it as one. A guard that read
    the ambient loop would call a synchronous operation nested inside an
    asynchronous one async and pass a source its executor cannot consume.
    """
    source = _AsyncOnlyIterable()
    reject_async_iterable_in_sync_context(
        source,
        flavor_noun="connection",
        async_executor=True,
    )


def test_reject_async_in_sync_context_cancels_future() -> None:
    """An unawaited future passed to reject_async_in_sync_context is cancelled before raising."""
    loop = asyncio.new_event_loop()
    future = loop.create_future()
    try:
        with pytest.raises(SyncMisuseError, match="returned an awaitable"):
            reject_async_in_sync_context(
                future,
                owner="TestOwner",
                method="test_method",
                context="test_context",
                recourse="test_recourse",
            )
        assert future.cancelled() is True
    finally:
        loop.close()


def test_coerce_field_value_or_none_returns_none_for_non_field() -> None:
    """Passing a non-Field object returns None rather than raising an error."""
    assert coerce_field_value_or_none(None, 42, alias=DEFAULT_DB_ALIAS) is None
    # basedpyright: the string standing in for a field is the hostile input under test;
    # coerce_field_value_or_none types the parameter as ModelField | None
    assert coerce_field_value_or_none("not_a_field", 42, alias=DEFAULT_DB_ALIAS) is None  # pyright: ignore[reportArgumentType]


def test_prepared_visibility_source_with_custom_render_error() -> None:
    """_prepared_visibility_source formats defect with custom render_error callable."""
    DummyType = _declared_type(Category, "DummyType")

    def custom_render(code: str, detail: str) -> str:
        return f"custom source error: {code} -> {detail}"

    with pytest.raises(ConfigurationError, match="custom source error: type -> list"):
        _prepared_visibility_source(DummyType, [1, 2, 3], render_error=custom_render)


def test_normalized_visibility_result_with_custom_render_error() -> None:
    """_normalized_visibility_result formats defect with custom render_error callable."""
    DummyType = _declared_type(Category, "DummyType")

    def custom_render(code: str, detail: str) -> str:
        return f"custom result error: {code} -> {detail}"

    with pytest.raises(ConfigurationError, match="custom result error: type -> list"):
        _normalized_visibility_result(
            DummyType,
            [1, 2, 3],
            required_alias=None,
            render_error=custom_render,
        )


def test_pks_all_present_subset_check() -> None:
    """pks_all_present keys each declared pk through the pk field and tests subset membership.

    The key is the column's value, so ``"1"`` and ``1`` are one integer pk.
    """
    pk_field = Category._meta.pk
    assert pks_all_present(pk_field, [1, 2], {1, 2, 3}) is True
    assert pks_all_present(pk_field, ["1", "02"], {1, 2}) is True
    assert pks_all_present(pk_field, [1, 4], {1, 2, 3}) is False


@pytest.mark.django_db
def test_visible_related_object_resolution() -> None:
    """visible_related_object resolves the visible object or returns None."""
    seed_data(0)
    (cat,) = categories_from_seed(("Electronics", False))
    info = SimpleNamespace(context=SimpleNamespace(request=None))

    resolved = visible_related_object(
        Category,
        saved_pk(cat),
        info,
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert resolved == cat

    missing = visible_related_object(Category, 999999, info, async_recourse=TEST_ASYNC_RECOURSE)
    assert missing is None


def test_reject_awaitable_sync_source_noop_for_non_awaitable() -> None:
    """reject_awaitable_sync_source passes non-awaitables without raising."""
    reject_awaitable_sync_source([1, 2, 3], _declared_type(Category, "CategoryType"))
    reject_awaitable_sync_source(Category.objects.none(), _declared_type(Category, "CategoryType"))


def test_reject_awaitable_sync_source_raises_for_awaitable() -> None:
    """reject_awaitable_sync_source raises SyncMisuseError for an awaitable source."""

    async def sample() -> models.QuerySet[Category]:
        return Category.objects.all()

    coro = sample()
    with pytest.raises(SyncMisuseError, match="consumer resolver returned an awaitable"):
        reject_awaitable_sync_source(coro, _declared_type(Category, "CategoryType"))


def test_prefetch_relation_target_unresolvable_paths_fail_open() -> None:
    """Unresolvable relation paths fail OPEN to Django, never raw-raise.

    The proof only ever NARROWS shapes Django itself mishandles; a path it
    cannot resolve here (unknown segment, plain column, unresolved lazy FK
    string) returns ``None`` and the entry is left to Django's own fetch-time
    traversal, exactly as if no guard ran.
    """

    class _BrokenFkHolder(models.Model):
        """A model whose only relation is an unresolvable lazy FK string.

        A key to an app that is not installed is malformed by construction and
        fails Django's system checks, so no fakeshop model can carry it; it
        alone covers the non-model ``related_model`` return of
        ``django_strawberry_framework/utils/querysets.py::_prefetch_relation_target_or_none``.
        """

        name: "models.TextField[str | Combinable, str]" = models.TextField(default="")
        rel: "models.ForeignKey[models.Model | Combinable, models.Model]" = models.ForeignKey(
            "missing_app.Missing",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "products"
            db_table = "probe_broken_fk_holder"

    assert _prefetch_relation_target_or_none(Category, object()) is None
    assert _prefetch_relation_target_or_none(Category, "bogus_rel") is None
    assert _prefetch_relation_target_or_none(Category, "name") is None
    # A resolved segment followed by an unknown one: the accessor scan runs on
    # Item (which carries FORWARD relations) and still finds nothing.
    assert _prefetch_relation_target_or_none(Category, "items__nope") is None
    # A dangling string FK keeps ``related_model`` a STRING (no raise): the
    # exact-type check fails, the helper returns None, Django keeps ownership.
    assert _prefetch_relation_target_or_none(_BrokenFkHolder, "rel") is None
    # A miss on a model carrying a non-concrete relation that is NOT a reverse
    # relation (a forward M2M, a GenericForeignKey, a GenericRelation): the
    # accessor scan must skip it, since none of them has an accessor name.
    assert _prefetch_relation_target_or_none(Book, "nope") is None
    assert _prefetch_relation_target_or_none(TaggedItem, "nope") is None
    assert _prefetch_relation_target_or_none(Branch, "nope") is None


@pytest.mark.django_db
def test_prefetch_relation_target_default_accessors_resolve() -> None:
    """The reverse-accessor map resolves every spelling Django's prefetch accepts.

    Covers the installed apps' default ``<model>_set`` relations (FK and M2M
    reverse), a multi-segment path THROUGH an accessor, and the reverse
    ``OneToOne`` accessor (the bare child model name, no ``_set``).
    """
    # Relations declared WITHOUT a related_name, reached by the default
    # ``<model>_set`` accessor (the spelling ``get_field`` alone cannot see).
    assert _prefetch_relation_target_or_none(ContentType, "permission_set") is Permission
    assert _prefetch_relation_target_or_none(ContentType, "logentry_set") is LogEntry
    assert _prefetch_relation_target_or_none(User, "logentry_set") is LogEntry
    assert _prefetch_relation_target_or_none(Group, "user_set") is User
    assert _prefetch_relation_target_or_none(Permission, "user_set") is User
    assert _prefetch_relation_target_or_none(Permission, "group_set") is Group
    # An accessor can be an INTERMEDIATE segment like any relation name.
    assert (
        _prefetch_relation_target_or_none(ContentType, "permission_set__content_type")
        is ContentType
    )

    # ``apps/library/models.py::Venue`` is the target of a one-to-one and a
    # many-to-many that declare no ``related_name``. Reverse OneToOne accessors
    # are the BARE child model name (no ``_set``).
    assert _prefetch_relation_target_or_none(Venue, "venuebadge") is VenueBadge
    # A reverse M2M without a related_name uses the same ``<model>_set`` spelling.
    assert _prefetch_relation_target_or_none(Venue, "venuesponsor_set") is VenueSponsor


@isolate_apps("apps.library")
def test_prefetch_relation_target_reads_a_colliding_part_as_the_accessor() -> None:
    """A part that is one relation's accessor and another's query name resolves to the accessor.

    Django's prefetch traversal resolves a lookup by attribute access, so ``"beta"`` fetches
    ``_BetaRow`` (accessor ``beta``) even though ``_meta.get_field("beta")`` answers with
    ``_AlphaRow``'s reverse relation (query name ``beta``).
    """

    class _Hub(models.Model):
        class Meta:
            app_label = "library"

    class _AlphaRow(models.Model):
        hub: "models.ForeignKey[_Hub | Combinable, _Hub]" = models.ForeignKey(
            _Hub,
            on_delete=models.CASCADE,
            related_name="alpha",
            related_query_name="beta",
        )

        class Meta:
            app_label = "library"

    class _BetaRow(models.Model):
        hub: "models.ForeignKey[_Hub | Combinable, _Hub]" = models.ForeignKey(
            _Hub,
            on_delete=models.CASCADE,
            related_name="beta",
            related_query_name="gamma",
        )

        class Meta:
            app_label = "library"

    assert _Hub._meta.get_field("beta").related_model is _AlphaRow
    assert _prefetch_relation_target_or_none(_Hub, "beta") is _BetaRow
    assert _prefetch_relation_target_or_none(_Hub, "alpha") is _AlphaRow


@pytest.mark.django_db
def test_prefetch_relation_target_resolves_every_installed_default_accessor() -> None:
    """EVERY installed default-accessor relation resolves to its own target.

    The proof must hold project-wide: any reverse relation reachable through a
    ``<model>_set`` spelling (FK, M2M, or reverse OneToOne) whose target the
    guard cannot resolve would fail OPEN exactly where the #37267 leak is
    reachable, so the accessor map must cover them all.
    """
    unresolved: list[tuple[str, str, str]] = []
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if not (field.is_relation and field.auto_created and not field.concrete):
                continue
            assert isinstance(field, ForeignObjectRel)
            accessor = field.get_accessor_name()
            if not accessor or not accessor.endswith("_set"):
                continue
            if _prefetch_relation_target_or_none(model, accessor) is not field.related_model:
                assert field.related_model is not None
                unresolved.append((model.__name__, accessor, field.related_model.__name__))
    assert unresolved == []


@pytest.mark.django_db
def test_seal_serves_a_combinator_as_a_single_table_primary_key_membership_query() -> None:
    """The sealed query is ``<model>.filter(pk__in=<combined>.values("pk"))`` on the caller's alias.

    One table, one predicate, the combinator kept verbatim inside the subquery and
    reduced to the primary-key column, so every surface can narrow it; the
    explicit alias the result carried stays the sealed queryset's alias.
    """
    seed_data(1)
    first, second = Category.objects.order_by("pk")[:2]
    combined = (
        Category.objects.using("default")
        .filter(pk=saved_pk(first))
        .union(Category.objects.filter(pk=saved_pk(second)))
        .order_by("-name")
    )

    sealed, defect = _seal_or_defect(combined, Category, None)

    assert defect is None
    assert sealed is not None
    assert sealed.db == "default"
    assert sealed.query.combinator is None
    assert not sealed.query.values_select
    (membership,) = sealed.query.where.children
    assert isinstance(membership, In)
    assert read_attr(read_attr(membership, "lhs"), "target") is Category._meta.pk
    membership_rhs = require_instance(read_attr(membership, "rhs"), SqlQuery)
    assert membership_rhs.combinator == "union"
    assert len(membership_rhs.combined_queries) == 2
    assert membership_rhs.values_select == ("pk",)
    # Vendor-neutral text only: a backend may parenthesize each compound branch.
    sql = str(sealed.query)
    table = Category._meta.db_table
    assert sql.startswith(f'SELECT "{table}"."id"')
    assert sql.endswith(f'ORDER BY "{table}"."name" DESC')
    assert [saved_pk(row) for row in _rows_of(Category, sealed)] == [
        saved_pk(row) for row in sorted((first, second), key=lambda c: c.name, reverse=True)
    ]


@pytest.mark.django_db
def test_seal_carries_a_primary_key_ordering_of_a_combinator() -> None:
    """``order_by("-pk")`` after a combinator is a column ordering the rewrite re-applies."""
    seed_data(1)
    first, second = Category.objects.order_by("pk")[:2]
    combined = (
        Category.objects.filter(pk=saved_pk(first))
        .union(Category.objects.filter(pk=saved_pk(second)))
        .order_by("-pk")
    )
    sealed, defect = _seal_or_defect(combined, Category, None)
    assert defect is None
    assert sealed is not None
    assert sealed.query.combinator is None
    assert [saved_pk(row) for row in _rows_of(Category, sealed)] == [
        saved_pk(second),
        saved_pk(first),
    ]


def _union_of_an_annotated_intersection(
    qs: models.QuerySet[Category],
) -> models.QuerySet[Category]:
    return qs.union(qs.intersection(qs.annotate(n=F("id"))))


def _union_of_a_difference_of_a_union_all(
    qs: models.QuerySet[Category],
) -> models.QuerySet[Category]:
    return qs.union(qs.difference(qs.union(qs, all=True)))


def _union_of_a_values_projected_intersection(
    qs: models.QuerySet[Category],
) -> models.QuerySet[Category]:
    return qs.union(qs.intersection(qs).values("id", "name"))


def _union_of_a_values_list_projected_intersection(
    qs: models.QuerySet[Category],
) -> models.QuerySet[Category]:
    return qs.union(qs.intersection(qs).values_list("id", "name"))


@pytest.mark.parametrize(
    ("build", "detail"),
    [
        pytest.param(
            _union_of_an_annotated_intersection,
            "union: a branch selects annotations ('n') that would be dropped from the rows",
            id="nested-branch-annotations",
        ),
        pytest.param(
            _union_of_a_difference_of_a_union_all,
            "union: union(all=True) keeps duplicate rows, which a primary-key set cannot",
            id="nested-union-all",
        ),
        pytest.param(
            _union_of_a_values_projected_intersection,
            "union: a nested combinator projects .values('id', 'name'), which the "
            "primary-key subquery cannot re-project",
            id="nested-combinator-values",
        ),
        pytest.param(
            _union_of_a_values_list_projected_intersection,
            "union: a nested combinator projects .values('id', 'name'), which the "
            "primary-key subquery cannot re-project",
            id="nested-combinator-values-list",
        ),
    ],
)
def test_seal_refuses_a_nested_combinator_whose_branch_the_primary_key_set_cannot_carry(
    build: Callable[[models.QuerySet[Category]], models.QuerySet[Category]],
    detail: str,
) -> None:
    """The lost-property walk recurses into a combined branch at any depth."""
    sealed, defect = _seal_or_defect(build(Category.objects.all()), Category, None)
    assert sealed is None
    assert defect == ("combined", detail)


@pytest.mark.django_db
def test_seal_serves_a_nested_combinator_as_its_primary_key_set() -> None:
    """A combinator nested in a branch keeps its own set operation inside the subquery."""
    seed_data(1)
    first, second, third = Category.objects.order_by("pk")[:3]
    qs = Category.objects.all()
    combined = qs.filter(pk=saved_pk(first)).union(
        qs.filter(pk__in=[saved_pk(second), saved_pk(third)]).difference(
            qs.filter(pk=saved_pk(third)),
        ),
    )
    sealed, defect = _seal_or_defect(combined, Category, None)
    assert defect is None
    assert sealed is not None
    assert sealed.query.combinator is None
    assert sorted(saved_pk(row) for row in _rows_of(Category, sealed)) == [
        saved_pk(first),
        saved_pk(second),
    ]


def test_unrendered_defect_code_says_so_instead_of_mislabelling() -> None:
    """A code with no arm at a site names itself; it never borrows another code's prose.

    Every message-building site renders only the subset of codes IT can reach,
    so a ladder ending in an unconditional branch for its own last code cannot
    fail loudly: a code added to the seal without an arm here would be reported
    to the schema author as an alias mismatch or a wrong-table error - a false
    description of a real rejection. Dispatch is exhaustive
    instead, and the fallback is legible on both halves: it names the code and
    carries the detail, so the rejection still fails closed.
    """
    message = _defect_message({"type": "arm for type"}, ("type", "list"), "Subject")
    assert message == "arm for type"

    unrendered = _defect_message({"type": "arm for type"}, ("brand_new", "detail"), "Subject")
    assert "'brand_new'" in unrendered
    assert "detail" in unrendered
    assert "no wording" in unrendered
    # The point of the fallback: no other code's prose is borrowed.
    assert "arm for type" not in unrendered


def test_seal_require_unevaluated() -> None:
    """Populated _result_cache produces an 'unevaluated' defect when require_unevaluated=True."""
    qs = Category.objects.all()
    policy_uneval: _SealPolicy[models.Model] = _SealPolicy(
        require_model_rows=True,
        reject_sliced=True,
        require_shared_alias=False,
        require_unevaluated=True,
    )
    # When cache is None: no defect
    assert qs._result_cache is None
    sealed, defect = _seal_or_defect(qs, Category, None, policy_uneval)
    assert defect is None
    assert sealed is not None

    # When cache is populated: ("evaluated", "the result cache is populated")
    qs_eval = Category.objects.all()
    qs_eval._result_cache = []
    sealed, defect = _seal_or_defect(qs_eval, Category, None, policy_uneval)
    assert sealed is None
    assert defect == ("evaluated", "the result cache is populated")


def test_visibility_defect_messages() -> None:
    """Visibility helpers word the defects their policies reach and name the ones they cannot.

    No ``get_queryset`` seal policy sets ``require_unevaluated`` and no visibility
    seal states a routing expectation, so ``evaluated`` and ``routing`` have no arm
    at either visibility site: were the seal ever to hand one over, the exhaustive
    dispatch must say so rather than mislabel it.
    """
    BookType = _declared_type(Book, "BookType")

    for code in ("evaluated", "routing"):
        unrendered = str(
            _visibility_result_error(
                BookType,
                Category,
                None,
                (code, "unreachable here"),
                None,
            ),
        )
        assert f"with the {code!r} defect (unreachable here)" in unrendered
        assert "declares no wording for" in unrendered

    err_msg_comb = str(
        _visibility_result_error(
            BookType,
            Category,
            None,
            ("combined", "union: a lost property"),
            None,
        ),
    )
    assert err_msg_comb == "BookType.get_queryset returned a combined queryset; " + (
        _COMBINED_WHAT.format(model="Category", detail="union: a lost property")
    )

    DummyType = _declared_type(Category, "DummyType")

    evaluated_qs = Category.objects.all()
    evaluated_qs._result_cache = []
    policy_uneval: _SealPolicy[models.Model] = _SealPolicy(require_unevaluated=True)
    with pytest.raises(
        ConfigurationError,
        match=r"with the 'evaluated' defect .* declares no wording for",
    ):
        _prepared_visibility_source(DummyType, evaluated_qs, policy=policy_uneval)

    duplicated_qs = Category.objects.all().union(Category.objects.all(), all=True)
    with pytest.raises(ConfigurationError) as excinfo:
        _prepared_visibility_source(DummyType, duplicated_qs)
    detail = "union: union(all=True) keeps duplicate rows, which a primary-key set cannot"
    assert str(excinfo.value) == (
        "apply_type_visibility for DummyType got a combined source queryset; "
        + _COMBINED_WHAT.format(model="Category", detail=detail)
    )


@pytest.mark.django_db
def test_apply_type_visibility_sync_serves_a_combined_result_as_its_pk_set() -> None:
    """A combined hook result is served as the rows its primary keys select, narrowable after.

    The sealed value is a single-table ``pk__in`` membership query of model rows,
    so a surface can still ``.filter(...)`` and ``.only(...)`` it, where Django
    refuses both on the combinator itself; the rows are the combinator's row set.
    """
    seed_data(1)
    names = sorted(
        require_instance(name, str)
        for name in list_of(Category.objects.values_list("name", flat=True))
    )
    first, second = names[0], names[1]

    def _union_hook(
        _cls: type,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset.filter(name=first).union(queryset.filter(name=second))

    CombinedType = _declared_type(Category, "CombinedType", _union_hook)

    sealed = apply_type_visibility_sync(
        CombinedType,
        Category.objects.all(),
        SimpleNamespace(),
        async_recourse=TEST_ASYNC_RECOURSE,
    )
    assert sealed.query.combinator is None
    assert sorted(row.name for row in _rows_of(Category, sealed)) == [first, second]
    second_only = sealed.filter(name=second).only("name")
    assert [row.name for row in _rows_of(Category, second_only)] == [second]


@pytest.mark.parametrize("combinator", ["union", "intersection", "difference"])
def test_list_relation_child_policy_serves_every_combinator_shape(combinator: str) -> None:
    """The plain-list child seal serves union, intersection, and difference alike.

    The child plan projects the sealed value (``.only()`` / ``.select_related()``)
    and Django refilters it at fetch time, both of which Django refuses on a
    combinator, so each shape reaches them as the single-table primary-key set it
    selects.
    """
    base = Category.objects.all()
    combined = call_method(base.filter(pk__gte=0), combinator, base.filter(pk__gte=1))
    sealed, defect = _seal_or_defect(combined, Category, None, _LIST_RELATION_CHILD_POLICY)
    assert defect is None
    assert sealed is not None
    assert sealed.query.combinator is None


def test_validate_post_orderset_result_valid() -> None:
    """_validate_post_orderset_result accepts valid, ordered candidate querysets."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    valid_candidate = Category.objects.all().order_by("name")
    sealed = _validate_post_orderset_result(
        DummyType,
        _snapshot_routing_intent(source_qs),
        valid_candidate,
        "MyOrderSet.apply_sync",
    )
    assert type(sealed) is models.QuerySet
    assert sealed.query.order_by == ("name",)
    assert _compiled_sql(sealed.query) == _compiled_sql(valid_candidate.query)


def test_validate_post_orderset_result_rejects_non_queryset() -> None:
    """_validate_post_orderset_result rejects non-queryset collections."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    with pytest.raises(
        ConfigurationError,
        match=(
            r"MyOrderSet\.apply_sync must return an unevaluated, unsliced QuerySet of Category rows; "
            r"got type defect"
        ),
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            [1, 2, 3],
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_none() -> None:
    """_validate_post_orderset_result rejects None return values."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    with pytest.raises(
        ConfigurationError,
        match=(
            r"MyOrderSet\.apply_sync must return an unevaluated, unsliced QuerySet of Category rows; "
            r"got type defect"
        ),
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            None,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_wrong_model() -> None:
    """_validate_post_orderset_result rejects querysets of an unrelated model."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    wrong_model_qs = Item.objects.all()
    with pytest.raises(
        ConfigurationError,
        match=(
            r"MyOrderSet\.apply_sync must return an unevaluated, unsliced QuerySet of Category rows; "
            r"got table defect"
        ),
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            wrong_model_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_evaluated() -> None:
    """_validate_post_orderset_result rejects querysets with evaluated result cache."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    eval_qs = Category.objects.all()
    eval_qs._result_cache = []
    with pytest.raises(
        ConfigurationError,
        match=(
            r"MyOrderSet\.apply_sync must return an unevaluated, unsliced QuerySet of Category rows; "
            r"got evaluated defect"
        ),
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            eval_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_sliced() -> None:
    """_validate_post_orderset_result rejects sliced querysets."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    sliced_qs = Category.objects.all()[:5]
    with pytest.raises(
        ConfigurationError,
        match=(
            r"MyOrderSet\.apply_sync must return an unevaluated, unsliced QuerySet of Category rows; "
            r"got sliced defect"
        ),
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            sliced_qs,
            "MyOrderSet.apply_sync",
        )


@pytest.mark.django_db
def test_validate_post_orderset_result_serves_a_combined_result_and_refuses_a_lost_property() -> (
    None
):
    """A combined sidecar result is served as its primary-key set, re-sorted by its ordering.

    A combinator that set cannot express (an outer ordering by an annotation the
    rewritten query has no column for) fails closed with the shared
    combined-queryset text rather than the one-sentence shape wording.
    """
    seed_data(1)
    names = sorted(
        require_instance(name, str)
        for name in list_of(Category.objects.values_list("name", flat=True))
    )

    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    comb_qs = (
        Category.objects.filter(name=names[0])
        .union(Category.objects.filter(name=names[1]))
        .order_by("-name")
    )
    sealed = _validate_post_orderset_result(
        DummyType,
        _snapshot_routing_intent(source_qs),
        comb_qs,
        "MyOrderSet.apply_sync",
    )
    assert sealed.query.combinator is None
    assert [row.name for row in _rows_of(Category, sealed)] == [names[1], names[0]]

    upper = Category.objects.annotate(upper_name=Upper("name"))
    lost_qs = upper.union(upper).order_by("upper_name")
    with pytest.raises(ConfigurationError) as excinfo:
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            lost_qs,
            "MyOrderSet.apply_sync",
        )
    detail = (
        "union: its ordering by 'upper_name' is not a Category column, so the rewritten "
        "query cannot carry it (it carries a column name or an F() over a column, with "
        ".asc() / .desc(); never a lookup, transform or other expression)"
    )
    assert str(excinfo.value) == (
        "MyOrderSet.apply_sync returned a combined queryset; "
        + _COMBINED_WHAT.format(model="Category", detail=detail)
    )


@pytest.mark.django_db
def test_validate_post_orderset_result_refuses_a_combined_result_ordered_through_a_hiding_type() -> (
    None
):
    """A related order term on a combinator is a lost property, refused like any other.

    The rewrite re-sorts the primary-key set only by a column name or an ``F()``
    over a column; this ``OrderSet`` term is an ``OrderBy`` over the
    visibility-scoped ``CASE`` on a shelf the shelf type can hide, so the combined
    result fails closed instead of being served in an order the rewrite cannot
    reproduce.
    """

    def _hide_secret(
        _cls: type[DjangoType],
        queryset: models.QuerySet[Shelf],
        _info: object,
        **_kwargs: object,
    ) -> models.QuerySet[Shelf]:
        return queryset.exclude(topic="secret")

    type(
        "UnionShelfType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": Shelf, "fields": "__all__"}),
            "get_queryset": classmethod(_hide_secret),
        },
    )

    DummyType = _declared_type(Book, "DummyType")

    class UnionBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "shelf__topic"]

    request = HttpRequest()
    request.user = AnonymousUser()
    source_qs = Book.objects.all()
    combined = Book.objects.filter(title="a").union(Book.objects.filter(title="b"))
    ordered = UnionBookOrder.apply_sync(
        [{"shelf_topic": Ordering.ASC}],
        combined,
        SimpleNamespace(context=SimpleNamespace(request=request)),
    )
    with pytest.raises(ConfigurationError, match="is not a Book column"):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            ordered,
            "UnionBookOrder.apply_sync",
        )


def test_validate_post_orderset_result_rejects_projection() -> None:
    """_validate_post_orderset_result rejects values/projection querysets."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    values_qs = Category.objects.values("id")
    with pytest.raises(
        ConfigurationError,
        match=(
            r"MyOrderSet\.apply_sync must return an unevaluated, unsliced QuerySet of Category rows; "
            r"got projection defect"
        ),
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            values_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_db_routing_mismatch() -> None:
    """_validate_post_orderset_result rejects querysets routed to a different database."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    diff_db_qs = Category.objects.using("other")
    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            diff_db_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_hints_routing_mismatch() -> None:
    """_validate_post_orderset_result rejects querysets with divergent database routing hints."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    diff_hints_qs = Category.objects.all()
    set_queryset_hints(diff_hints_qs, {"instance": 123})
    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            diff_hints_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_routing_hints_hostile_repr() -> None:
    """_validate_post_orderset_result never calls a consumer __repr__ on routing hints."""
    DummyType = _declared_type(Category, "DummyType")

    class HostileValue:
        @override
        def __repr__(self) -> str:
            raise AssertionError("Hostile consumer __repr__ invoked")

    val_a = HostileValue()
    val_b = HostileValue()

    source_qs = Category.objects.all()
    set_queryset_hints(source_qs, {"tag": val_a})

    cand_same = Category.objects.all()
    # Same instance (identity).
    set_queryset_hints(cand_same, {"tag": val_a})

    # The same hint object is the same routing intent.
    sealed = _validate_post_orderset_result(
        DummyType,
        _snapshot_routing_intent(source_qs),
        cand_same,
        "MyOrderSet.apply_sync",
    )
    assert sealed is not None

    cand_diff = Category.objects.all()
    # Different instance.
    set_queryset_hints(cand_diff, {"tag": val_b})

    # Rejection formatting must not invoke HostileValue.__repr__
    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ) as exc_info:
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            cand_diff,
            "MyOrderSet.apply_sync",
        )
    assert "HostileValue at 0x" in str(exc_info.value)


def test_validate_post_orderset_result_routing_hints_none_vs_empty() -> None:
    """_validate_post_orderset_result preserves distinction between absent (None) and empty ({}) hints."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    # basedpyright: plants a ``None`` ``_hints``, which Django never stores (it writes ``{}``)
    set_queryset_hints(source_qs, None)  # pyright: ignore[reportArgumentType]

    cand_qs = Category.objects.all()
    set_queryset_hints(cand_qs, {})

    with pytest.raises(
        ConfigurationError,
        match=r"expected db=None, hints=None, got db=None, hints=\{\}",
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            cand_qs,
            "MyOrderSet.apply_sync",
        )


def test_routing_repr_renders_a_non_dict_hints_mapping_by_its_repr() -> None:
    """A ``dict`` SUBCLASS renders by its own repr rather than being walked as hints."""

    class HintsSubclass(dict[str, object]):
        pass

    assert _routing_repr(HintsSubclass({"tag": "a"})) == "{'tag': 'a'}"


def test_routing_repr_names_instance_hints_by_class_and_identity() -> None:
    """An exact hints dict renders scalars by repr and instance hints as ``<Class at 0x...>``."""
    instance = Category(name="c")
    assert _routing_repr(None) == "None"
    assert _routing_repr("default") == "'default'"
    assert _routing_repr({"tag": "a", "instance": instance}) == (
        f"{{'instance': <Category at {hex(id(instance))}>, 'tag': 'a'}}"
    )


def test_routing_rejects_a_renamed_hint_key_at_equal_length() -> None:
    """Same-size hint dicts with different KEYS are a routing change."""
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    set_queryset_hints(source_qs, {"tenant": "a"})

    cand_qs = Category.objects.all()
    set_queryset_hints(cand_qs, {"other": "a"})

    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ):
        _validate_post_orderset_result(
            DummyType,
            _snapshot_routing_intent(source_qs),
            cand_qs,
            "MyOrderSet.apply_sync",
        )


def test_snapshot_routing_intent_is_frozen_before_consumer_code_can_mutate_the_source() -> None:
    """The baseline is a COPY taken before the override runs, not a post-call read.

    ``OrderSet.apply_*`` receives the very queryset object the seal later
    compares against, so an override can rewrite ``_db`` or edit ``_hints`` in
    place and return the same object. The snapshot copies the hints dictionary
    and holds the alias by value, so both in-place edits are rejected against
    what the source carried when the override was handed it.
    """
    DummyType = _declared_type(Category, "DummyType")

    source_qs = Category.objects.all()
    set_queryset_hints(source_qs, {"tenant": 1})
    expected = _snapshot_routing_intent(source_qs)
    assert (expected.db, expected.hints) == (None, {"tenant": 1})
    assert expected.effective_alias == "default"
    assert expected.hints is not queryset_hints(source_qs)

    # An in-place hints edit on the source leaves the snapshot untouched and is rejected.
    queryset_hints(source_qs)["tenant"] = 2
    assert expected.hints == {"tenant": 1}
    with pytest.raises(ConfigurationError, match=r"expected db=None, hints=\{'tenant': 1\}"):
        _validate_post_orderset_result(DummyType, expected, source_qs, "MyOrderSet.apply_sync")

    # An in-place alias rewrite on the same object is rejected the same way.
    set_queryset_hints(source_qs, {"tenant": 1})
    assert expected.hints is not None
    tenant = expected.hints["tenant"]
    assert isinstance(tenant, int)
    queryset_hints(source_qs)["tenant"] = tenant
    truth.instance_state(source_qs)["_db"] = "other"
    with pytest.raises(ConfigurationError, match=r"expected db=None, .* got db='other'"):
        _validate_post_orderset_result(DummyType, expected, source_qs, "MyOrderSet.apply_sync")


class _NestedAliasRouter:
    """A legal router whose answer depends on state INSIDE a hint value.

    ``ConnectionRouter`` hands hint values to a router untouched, so reading
    into one is ordinary router code - a standard ``instance`` hint is itself a
    mutable object. It is also why preserving a hint's identity proves nothing
    about the connection a later read would pick.
    """

    calls: list[str] = []

    def db_for_read(self, _model: type[models.Model], **hints: object) -> str | None:
        _NestedAliasRouter.calls.append("read")
        token = hints.get("tenant")
        if not is_exact_dict(token):
            return None
        alias = token["alias"]
        return alias if isinstance(alias, str) else None

    def db_for_write(self, model: type[models.Model], **hints: object) -> str | None:
        _NestedAliasRouter.calls.append("write")
        return self.db_for_read(model, **hints)


@override_settings(DATABASE_ROUTERS=[_NestedAliasRouter()])
def test_routing_intent_pins_the_alias_resolved_before_a_hint_could_be_mutated() -> None:
    """A hint mutated behind a preserved identity cannot re-route the sealed result.

    The seal's hint comparison proves the candidate carries the hints the
    source did; it cannot prove those objects still mean the same thing,
    because a router is free to read mutable state inside one. The effective
    alias is therefore resolved at snapshot time - before the public
    ``apply_*`` call can touch anything - and the accepted result is pinned to
    it, so the attestation is about the connection rather than about hint
    contents.
    """
    DummyType = _declared_type(Category, "DummyType")

    token = {"alias": "default"}
    source_qs = Category.objects.all()
    set_queryset_hints(source_qs, {"tenant": token})

    _NestedAliasRouter.calls.clear()
    intent = _snapshot_routing_intent(source_qs)
    assert intent.effective_alias == "default"
    # Exactly one router answer, taken at the snapshot. Timing is the contract:
    # a refactor that resolved the alias after the override ran would read the
    # mutated token instead.
    assert _NestedAliasRouter.calls == ["read"]

    # The override mutates INSIDE the hint value it was handed and returns a
    # queryset carrying that very object, so the hint comparison still holds.
    token["alias"] = "other"
    candidate = Category.objects.all()
    set_queryset_hints(candidate, {"tenant": token})
    assert queryset_hints(candidate)["tenant"] is queryset_hints(source_qs)["tenant"]

    sealed = _validate_post_orderset_result(DummyType, intent, candidate, "MyOrderSet.apply_sync")
    # Validation asks the router nothing; the pin is the frozen answer.
    assert _NestedAliasRouter.calls == ["read"]
    assert queryset_db(sealed) == "default"
    assert sealed.db == "default"
    # Without the pin, the mutated token routes the read somewhere else.
    assert router.db_for_read(Category, **queryset_hints(candidate)) == "other"


@override_settings(DATABASE_ROUTERS=[_NestedAliasRouter()])
def test_routing_intent_resolves_a_write_marked_source_through_the_write_router() -> None:
    """The resolution mirrors ``QuerySet.db``: a write-marked source asks ``db_for_write``.

    ``_for_write`` is carried forward by the seal, so resolving the read alias
    for a source Django would route as a write would pin the wrong connection.
    """
    source_qs = Category.objects.select_for_update()
    set_queryset_hints(source_qs, {"tenant": {"alias": "default"}})

    _NestedAliasRouter.calls.clear()
    intent = _snapshot_routing_intent(source_qs)
    assert _NestedAliasRouter.calls == ["write", "read"]
    assert intent.effective_alias == "default"


def test_routing_intent_on_an_explicitly_routed_source_needs_no_router() -> None:
    """An explicit ``.using(...)`` alias IS the effective alias; no router is consulted."""
    source_qs = Category.objects.using("default")
    with override_settings(DATABASE_ROUTERS=[_RaisingRouter()]):
        intent = _snapshot_routing_intent(source_qs)
    assert (intent.db, intent.effective_alias) == ("default", "default")


class _RaisingRouter:
    def db_for_read(self, _model: type[models.Model], **_hints: object) -> NoReturn:
        raise RuntimeError("router exploded")


@override_settings(DATABASE_ROUTERS=[_RaisingRouter()])
def test_routing_intent_propagates_the_router_error() -> None:
    """The database router is deployment code: its exception propagates unchanged."""
    with pytest.raises(RuntimeError, match="router exploded"):
        _snapshot_routing_intent(Category.objects.all())


class _MemberAliasRouter:
    """Answers every read with ``alias``, a ``TextChoices`` / ``StrEnum`` member."""

    def __init__(self, alias: str) -> None:
        self.alias = alias

    def db_for_read(self, _model: type[models.Model], **_hints: object) -> str:
        """The member alias, for every model."""
        return self.alias


@pytest.mark.parametrize("kind", ["text-choices", "str-enum"])
def test_routing_intent_freezes_a_member_router_answer_as_its_exact_text(kind: str) -> None:
    """A member alias a router answers is frozen as its text."""
    with override_settings(DATABASE_ROUTERS=[_MemberAliasRouter(_term(kind, "DEFAULT"))]):
        intent = _snapshot_routing_intent(Category.objects.all())
    assert intent.db is None
    assert type(intent.effective_alias) is str
    assert intent.effective_alias == "default"


def _pending(
    queryset: models.QuerySet[models.Model, object],
    kwargs: dict[str, object],
    args: tuple[object, ...] = (),
) -> models.QuerySet[models.Model, object]:
    """``queryset`` carrying ``args`` / ``kwargs`` as the pending filter a manager leaves."""
    truth.instance_state(queryset)["_deferred_filter"] = (False, args, kwargs)
    return queryset


@pytest.mark.django_db
def test_deferred_filter_shallow_nesting_seals() -> None:
    """A pending filter nested well inside the budget seals to Django's own SQL and rows."""
    seed_data(2)
    candidate = _pending(Item.objects.all(), {}, (Q(Q(Q(pk__gte=0)), name__gte=""),))
    twin = Item.objects.filter(Q(Q(Q(pk__gte=0)), name__gte=""))

    sealed, defect = _seal_or_defect(candidate, Item, None)

    assert defect is None
    assert sealed is not None
    assert str(sealed.query) == str(twin.query)
    assert list(sealed) == list(twin)


def _item_pks(mode_name: str) -> models.QuerySet[Item, dict[str, object]]:
    """``Item`` primary keys under ``mode_name``'s fetch mode, or the queryset's default."""
    pks = Item.objects.values("pk")
    return pks if mode_name == "default" else pks.fetch_mode(FETCH_MODES[mode_name])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mode_name",
    [
        "default",
        *[
            pytest.param(name, marks=requires_fetch_modes)
            for name in ("FETCH_ONE", "FETCH_PEERS", "FETCH_RAISE")
        ],
    ],
)
def test_deferred_filter_queryset_value_seals_with_its_fetch_mode(mode_name: str) -> None:
    """A ``QuerySet`` value in a pending filter seals on every supported Django release.

    Django supports ``pk__in=<queryset>``; the value's fetch mode (where the release has
    one) is one of Django's own stateless singletons, retained by reference, so the
    sealed SQL and rows are Django's.
    """
    seed_data(2)
    candidate = _pending(Item.objects.all(), {"pk__in": _item_pks(mode_name)})
    twin = Item.objects.filter(pk__in=_item_pks(mode_name))

    sealed, defect = _seal_or_defect(candidate, Item, None)

    assert defect is None
    assert sealed is not None
    assert str(sealed.query) == str(twin.query)
    rows = list(sealed)
    assert rows
    assert rows == list(twin)


def test_extra_where_without_params_seals_with_none_params() -> None:
    """``extra(where=...)`` with no ``params=`` stores ``None``, which ``ExtraWhere`` reads as ``()``."""
    sealed, defect = _seal_or_defect(Book.objects.extra(where=["1 = 1"]), Book, None)
    assert defect is None
    assert sealed is not None
    extra_where = sealed.query.where.children[0]
    assert type(extra_where) is ExtraWhere
    assert extra_where.params is None


def _doubled() -> Value:
    return Value(2, output_field=models.IntegerField())


@pytest.mark.parametrize(
    "lookup",
    [
        "shelf__twice",
        "shelf__twice__gt",
        "shelf__branch__twice",
        "vshelf__twice",
    ],
)
def test_a_name_past_a_relation_splits_as_over_the_rows_annotating_none(lookup: str) -> None:
    """A name past a relation is the related model's, never the rows' own annotation.

    Django's ``Query.names_to_path`` falls back to a selected annotation of the query for a
    name the related model lacks; the package splits the path, and reads its target
    fields, as it does over the same rows annotating nothing, ``FilteredRelation`` alias
    included, and leaves the annotated query selecting its annotation.
    """
    plain = Book.objects.alias(vshelf=FilteredRelation("shelf"))
    annotated = plain.annotate(twice=_doubled())
    assert split_lookup(annotated.query, lookup) == split_lookup(plain.query, lookup)
    assert lookup_target_fields(annotated.query, lookup) == lookup_target_fields(
        plain.query,
        lookup,
    )
    assert list(annotated.query.annotation_select) == ["twice"]


@pytest.mark.parametrize(
    ("model", "lookup"),
    [
        pytest.param(TaggedItem, "tag__exact", id="a-column"),
        pytest.param(DeskShift, "desk__branch", id="a-relation-django-joins"),
        pytest.param(Book, "shelf__branch", id="two-relations-django-joins"),
        pytest.param(TaggedItem, "bogus__exact", id="a-name-the-model-lacks"),
    ],
)
def test_the_joinless_walk_answers_none_short_of_a_generic_foreign_key(
    model: type[models.Model],
    lookup: str,
) -> None:
    """A walk ending on a column, a joined relation or a name the model lacks: no such key.

    Django's walk of the path reaches no relation it builds no join for, so the answer is
    ``None``: past a column the names are its transforms and lookup, never fields.
    """
    assert joinless_relation_on(model, lookup) is None


def test_the_joinless_walk_answers_the_generic_foreign_key_and_the_names_past_it() -> None:
    """Past a key onto a ``GenericForeignKey``: the key, read on the model the walk reached."""
    assert joinless_relation_on(DeskShift, "desk__content_object__id__exact") == (
        CirculationDesk._meta.get_field("content_object"),
        ("id", "exact"),
    )


def test_combined_query_branch_over_another_model_fails_closed() -> None:
    """A union whose branch reads another model's table fails closed as ``table``.

    ``QuerySet.model`` reports the outer (registered) model, but a
    ``combined_queries`` branch reads ``Item``'s table; the primary-key rewrite
    would select the ``Category`` rows whose primary key equals an ``Item``'s.
    Constructing the union composes lazy query state only - no SQL runs.
    """
    hostile = Category.objects.all().union(Item.objects.all())
    assert _seal_or_defect(hostile, Category, None)[1] == ("table", "Item")
    nested = Category.objects.all().union(Category.objects.all().union(Item.objects.all()))
    assert _seal_or_defect(nested, Category, None)[1] == ("table", "Item")
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            _sync_hook_type(hostile),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )


@requires_fetch_modes
@pytest.mark.parametrize("mode_name", ["FETCH_ONE", "FETCH_PEERS", "FETCH_RAISE"])
def test_the_seal_carries_each_django_fetch_mode(mode_name: str) -> None:
    """The sealed clone loads its rows under the candidate's own Django fetch mode."""
    mode = FETCH_MODES[mode_name]
    sealed, defect = _seal_or_defect(
        Category.objects.filter(name="visible").fetch_mode(mode),
        Category,
        None,
    )
    assert defect is None
    assert sealed is not None
    assert truth.instance_state(sealed)["_fetch_mode"] is mode


@pytest.mark.django_db
def test_seal_policy_presets_answer_slice_and_combinator_independently() -> None:
    """Each preset rejects exactly the shapes its surface cannot recompose onto.

    ``reject_sliced`` and ``require_model_rows`` are deliberately independent
    fields. A read surface rejects a slice, the one-edge-down child whose own
    gate classifies a slice admits one, the plain-list-relation child does not
    (Django refilters it at fetch time), and the cascade rejects a slice because
    it narrows by ``.filter(...)``. Every one of them serves a combinator as its
    primary-key set, which each can narrow and re-project.
    """
    base = Category.objects.all()
    sliced = base[:5]
    combined = base.union(base)

    assert _seal_or_defect(sliced, Category, None, _DEFAULT_SEAL_POLICY)[1] == (
        "sliced",
        "rows 0:5",
    )
    assert _seal_or_defect(sliced, Category, None, _PREFETCH_CHILD_POLICY)[1] is None
    assert _seal_or_defect(sliced, Category, None, _LIST_RELATION_CHILD_POLICY)[1] == (
        "sliced",
        "rows 0:5",
    )
    assert _seal_or_defect(sliced, Category, None, _CASCADE_SEAL_POLICY)[1] == (
        "sliced",
        "rows 0:5",
    )
    for policy in (
        _DEFAULT_SEAL_POLICY,
        _CASCADE_SEAL_POLICY,
        _PREFETCH_CHILD_POLICY,
        _LIST_RELATION_CHILD_POLICY,
    ):
        sealed, defect = _seal_or_defect(combined, Category, None, policy)
        assert defect is None
        assert sealed is not None
        assert sealed.query.combinator is None
    # ``require_model_rows`` still answers only the projection question.
    assert _seal_or_defect(base.values("id"), Category, None, _DEFAULT_SEAL_POLICY)[1] == (
        "projection",
        "ValuesIterable",
    )
    assert _seal_or_defect(base.values("id"), Category, None, _CASCADE_SEAL_POLICY)[1] is None


def test_a_combined_prefetch_child_is_served_as_its_primary_key_set() -> None:
    """A ``Prefetch`` child built by a combinator is rewritten; a path and a bare ``Prefetch`` stay.

    Django's prefetch filters the child by its relation, which it refuses after a
    combinator, so the child becomes ``pk__in`` of the set it selects.
    """
    child = Item.objects.filter(name="a").union(Item.objects.filter(name="b"))
    candidate = Category.objects.prefetch_related(
        "items__entries",
        Prefetch("items"),
        Prefetch("items", queryset=child, to_attr="combined_items"),
    )
    sealed, defect = _seal_or_defect(candidate, Category, None)
    assert defect is None
    assert sealed is not None
    lookups = queryset_prefetch_lookups(sealed)
    assert lookups[0] == "items__entries"
    first = lookups[1]
    assert not is_str(first)
    assert first.queryset is None
    rewritten = lookups[2]
    assert not is_str(rewritten)
    assert rewritten.to_attr == "combined_items"
    assert rewritten.queryset is not None
    assert rewritten.queryset.query.combinator is None
    assert child.query.combinator == "union"


@pytest.mark.parametrize(
    ("child", "defect"),
    [
        pytest.param(
            lambda: Item.objects.all().union(Category.objects.all()),
            ("table", "Category"),
            id="branch-over-another-model",
        ),
        pytest.param(
            lambda: Item.objects.all().union(Item.objects.all(), all=True),
            (
                "combined",
                "union: union(all=True) keeps duplicate rows, which a primary-key set cannot",
            ),
            id="duplicates",
        ),
    ],
)
def test_a_combined_prefetch_child_the_rewrite_cannot_serve_fails_closed(
    child: Callable[[], models.QuerySet[models.Model]],
    defect: tuple[str, str],
) -> None:
    """A combined child over another model, or one its primary-key set would change, is refused."""
    candidate = Category.objects.prefetch_related(Prefetch("items", queryset=child()))
    assert _seal_or_defect(candidate, Category, None) == (None, defect)


def _two_level_prefetch(entries: models.QuerySet[models.Model]) -> models.QuerySet[Category]:
    """A ``Category`` source prefetching ``items`` and, under them, ``entries`` over ``entries``."""
    items = Item.objects.prefetch_related(Prefetch("entries", queryset=entries))
    return Category.objects.prefetch_related(Prefetch("items", queryset=items))


@pytest.mark.django_db
def test_a_combined_prefetch_child_two_levels_down_is_served_as_its_primary_key_set() -> None:
    """A combined child under a plain child is rewritten too, so each item reads its own entries.

    Django hoists the inner lookup into the outer prefetch and filters it by each item,
    a predicate a combinator's compiler ignores; served as its primary-key set, each
    item's ``entries`` are its own.
    """
    seed_data(2)
    every = Entry.objects.all()
    entries = every.filter(pk__gte=0).union(every.filter(pk__lt=0))
    sealed, defect = _seal_or_defect(_two_level_prefetch(entries), Category, None)
    assert defect is None
    assert sealed is not None
    outer = queryset_prefetch_lookups(sealed)[0]
    assert not is_str(outer)
    assert outer.queryset is not None
    inner = queryset_prefetch_lookups(outer.queryset)[0]
    assert not is_str(inner)
    assert inner.queryset is not None
    assert inner.queryset.query.combinator is None
    assert entries.query.combinator == "union"
    served = [
        (saved_pk(item), entry.item_id)
        for category in _rows_of(Category, sealed)
        for item in category.items.all()
        for entry in _rows_of(
            Entry,
            require(call_method(read_attr(item, "entries"), "all"), is_iterable),
        )
    ]
    assert served
    assert all(item_pk == entry_item for item_pk, entry_item in served)


def test_a_combined_prefetch_child_two_levels_down_over_another_model_fails_closed() -> None:
    """A combined child two levels down with a branch over another table is the ``table`` defect."""
    entries = Entry.objects.all().union(Item.objects.all())
    assert _seal_or_defect(_two_level_prefetch(entries), Category, None) == (
        None,
        ("table", "Item"),
    )


_UNRELATED_ROWS = (
    "a prefetch child over an unrelated table would populate the relation with rows the "
    "related type's visibility hook never saw"
)


@pytest.mark.parametrize(
    ("candidate", "alias", "detail"),
    [
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Property.objects.all()),
            ),
            None,
            "Category prefetch 'items' queryset is over Property rows, but the 'items' "
            f"relation targets Item rows; {_UNRELATED_ROWS}",
            id="unrelated-model",
        ),
        pytest.param(
            lambda: _two_level_prefetch(Property.objects.all()),
            None,
            "Item prefetch 'entries' queryset is over Property rows, but the 'entries' "
            f"relation targets Entry rows; {_UNRELATED_ROWS}",
            id="unrelated-model-one-level-down",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items__entries", queryset=Property.objects.all()),
            ),
            None,
            "Category prefetch 'items__entries' queryset is over Property rows, but the "
            f"'items__entries' relation targets Entry rows; {_UNRELATED_ROWS}",
            id="unrelated-model-nested-path",
        ),
        pytest.param(
            lambda: Item.objects.prefetch_related(
                Prefetch("category", queryset=Property.objects.all()),
            ),
            None,
            "Item prefetch 'category' queryset is over Property rows, but the 'category' "
            f"relation targets Category rows; {_UNRELATED_ROWS}",
            id="forward-fk",
        ),
        pytest.param(
            lambda: ContentType.objects.prefetch_related(
                Prefetch("permission_set", queryset=LogEntry.objects.all()),
            ),
            None,
            "ContentType prefetch 'permission_set' queryset is over LogEntry rows, but the "
            f"'permission_set' relation targets Permission rows; {_UNRELATED_ROWS}",
            id="default-accessor",
        ),
        pytest.param(
            lambda: BranchNote.objects.prefetch_related(
                Prefetch("branch", queryset=Property.objects.all()),
            ),
            None,
            "BranchNote prefetch 'branch' queryset is over Property rows, but the 'branch' "
            f"relation targets ProxyBranch rows; {_UNRELATED_ROWS}",
            id="proxy-target",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Item.objects.using("other")),
            ),
            None,
            "Category prefetch 'items' queryset is routed to alias 'other', but this "
            "resolution reads alias None; one resolution never spans two database connections",
            id="routed-child-under-unrouted-parent",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Item.objects.using("other")),
            ),
            "default",
            "Category prefetch 'items' queryset is routed to alias 'other', but this "
            "resolution reads alias 'default'; one resolution never spans two database "
            "connections",
            id="cross-routed-child",
        ),
        pytest.param(
            lambda: _two_level_prefetch(Entry.objects.using("other")),
            None,
            "Item prefetch 'entries' queryset is routed to alias 'other', but this "
            "resolution reads alias None; one resolution never spans two database connections",
            id="routed-child-one-level-down",
        ),
    ],
)
def test_a_prefetch_child_off_its_relation_or_its_alias_fails_closed(
    candidate: Callable[[], models.QuerySet[models.Model]],
    alias: str | None,
    detail: str,
) -> None:
    """A child at any depth over a model its relation does not target, or routed off, is refused.

    Django hands a child's rows to the relation without checking their model (Django
    ticket #37267), so they would reach the relation unseen by its type's hook; a
    routed child would split one resolution across two connections.
    """
    source = candidate()
    model = source.model
    assert _seal_or_defect(source, model, alias) == (None, ("prefetch", detail))


def test_a_candidate_routed_off_the_alias_is_refused_before_its_children() -> None:
    """A routed-off candidate with a bad ``Prefetch`` child reports the ``alias`` defect.

    The candidate's own routing is checked before its children are walked, so the
    refusal names the outer queryset rather than one of its children.
    """
    source = Category.objects.prefetch_related(
        Prefetch("items", queryset=Property.objects.all()),
    ).using("other")
    assert _seal_or_defect(source, Category, "default") == (None, ("alias", "other"))


def test_a_prefetch_child_refusal_names_the_child_in_the_hook_error() -> None:
    """A hook returning such a child fails closed with the child named in the error."""
    hook_result = Category.objects.prefetch_related(
        Prefetch("items", queryset=Property.objects.all()),
    )
    with pytest.raises(ConfigurationError) as raised:
        apply_type_visibility_sync(
            _sync_hook_type(hook_result),
            Category.objects.all(),
            info=None,
            async_recourse=TEST_ASYNC_RECOURSE,
        )
    assert str(raised.value).startswith(
        "_StubType.get_queryset was refused: its Category prefetch 'items' queryset is over "
        "Property rows",
    )


@pytest.mark.parametrize(
    ("candidate", "alias"),
    [
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Item.objects.all()),
            ),
            None,
            id="relation-target",
        ),
        pytest.param(
            lambda: Shelf.objects.prefetch_related(
                Prefetch("branch", queryset=ProxyBranch.objects.all()),
            ),
            None,
            id="target-subclass",
        ),
        pytest.param(
            lambda: BranchNote.objects.prefetch_related(
                Prefetch("branch", queryset=Branch.objects.all()),
            ),
            None,
            id="concrete-model-of-a-proxy-target",
        ),
        pytest.param(
            lambda: ContentType.objects.prefetch_related(
                Prefetch("permission_set", queryset=Permission.objects.all()),
            ),
            None,
            id="default-accessor",
        ),
        pytest.param(
            lambda: _two_level_prefetch(Entry.objects.all()),
            None,
            id="nested-child",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items__entries", queryset=Entry.objects.all()),
            ),
            None,
            id="nested-path",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Item.objects.all()[:5], to_attr="top_items"),
            ),
            None,
            id="sliced-child-with-to-attr",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Item.objects.using("other")),
            ).using("other"),
            None,
            id="child-routed-with-its-parent",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                Prefetch("items", queryset=Item.objects.using("default")),
            ),
            "default",
            id="child-routed-to-the-required-alias",
        ),
        pytest.param(
            lambda: Category.objects.prefetch_related(
                "items",
                Prefetch("items"),
                Prefetch("items", queryset=None, to_attr="every_item"),
            ),
            None,
            id="no-child-queryset",
        ),
    ],
)
def test_a_prefetch_child_on_its_relation_and_alias_seals(
    candidate: Callable[[], models.QuerySet[models.Model]],
    alias: str | None,
) -> None:
    """A child over its relation's target (or a subclass of it), on the parent's alias, seals."""
    source = candidate()
    sealed, defect = _seal_or_defect(source, source.model, alias)
    assert defect is None
    assert sealed is not None
    assert queryset_prefetch_lookups(sealed) == queryset_prefetch_lookups(source)


@pytest.mark.django_db
def test_an_unrouted_prefetch_child_follows_its_parent_alias_at_fetch() -> None:
    """The seal leaves an unrouted child unrouted; Django routes it with the parent's rows."""
    seed_data(2)
    candidate = Category.objects.prefetch_related(Prefetch("items", queryset=Item.objects.all()))
    sealed, defect = _seal_or_defect(candidate, Category, "default")
    assert defect is None
    assert sealed is not None
    assert queryset_db(sealed) == "default"
    child = queryset_prefetch_lookups(sealed)[0]
    assert not is_str(child)
    assert child.queryset is not None
    assert queryset_db(child.queryset) is None
    rows = _rows_of(Category, sealed)
    assert rows
    assert all(type(item) is Item for row in rows for item in row.items.all())
