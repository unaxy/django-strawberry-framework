"""Live HTTP coverage for the values DRF uniqueness validators actually bind."""

from __future__ import annotations

import datetime
import inspect
from collections.abc import Generator, Iterator, Mapping
from contextlib import contextmanager
from decimal import Decimal
from functools import wraps
from importlib import import_module
from typing import TYPE_CHECKING

import pytest
import strawberry
from django.db import connection, models
from django.db.models import F, Q, Value
from django.db.models.expressions import Combinable
from django.db.models.lookups import BuiltinLookup
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext, isolate_apps
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_at
from rest_framework import serializers
from rest_framework.validators import (
    UniqueForDateValidator,
    UniqueForYearValidator,
    UniqueTogetherValidator,
    UniqueValidator,
    qs_exists_with_condition,
)
from typing_extensions import override

from django_strawberry_framework import (
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    NestedSerializerConfig,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils._narrowing import is_dict, read_attr, require
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import ModelSerializerBase, saved_pk

if TYPE_CHECKING:
    from django_strawberry_framework.rest_framework.serializer_converter import DRFSerializer
    from django_strawberry_framework.utils.typing import ConcreteField

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_HUGE = "999999999 00:00:00"
_FIT = "1 00:00:00"


class _Parent(models.Model):
    label: models.TextField[str | Combinable, str] = models.TextField()
    amount: models.IntegerField[float | int | str | Combinable | None, int | None] = (
        models.IntegerField(null=True)
    )
    rank: models.IntegerField[float | int | str | Combinable | None, int | None] = (
        models.IntegerField(null=True)
    )
    occurred_at: models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable | None,
        datetime.datetime | None,
    ] = models.DateTimeField(
        null=True,
    )

    class Meta:
        app_label = "scalars"
        managed = False

    @override
    def __str__(self) -> str:
        return self.label


class _Other(models.Model):
    label: models.TextField[str | Combinable, str] = models.TextField(default="")
    span: models.DurationField[object, datetime.timedelta | None] = models.DurationField(null=True)
    amount: models.IntegerField[float | int | str | Combinable | None, int | None] = (
        models.IntegerField(null=True)
    )
    positive_amount: models.PositiveIntegerField[
        float | int | str | Combinable | None,
        int | None,
    ] = models.PositiveIntegerField(null=True)
    rank: models.IntegerField[float | int | str | Combinable | None, int | None] = (
        models.IntegerField(null=True)
    )
    day: models.DateField[str | datetime.date | Combinable | None, datetime.date | None] = (
        models.DateField(null=True)
    )
    occurred_at: models.DateField[
        str | datetime.date | Combinable | None,
        datetime.date | None,
    ] = models.DateField(null=True)

    class Meta:
        app_label = "scalars"
        managed = False

    @override
    def __str__(self) -> str:
        return "Other"


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-serializer-validator-binds/", _view)]


@strawberry.type
class _Query:
    ping: int = 1


def _schema(
    serializer_class: type[DRFSerializer],
    *,
    operation: str = "create",
    nested_fields: Mapping[str, NestedSerializerConfig] | None = None,
    optional_fields: tuple[str, ...] | None = None,
) -> DjangoSchema:
    registry.clear()

    class ParentType(DjangoType):
        class Meta:
            model = _Parent
            fields = (
                "id",
                "label",
                "amount",
                "rank",
                "occurred_at",
            )

    selected_serializer = serializer_class
    selected_operation = operation
    selected_nested = nested_fields
    selected_optional = optional_fields

    class Write(SerializerMutation):
        class Meta:
            serializer_class = selected_serializer
            operation = selected_operation
            nested_fields = selected_nested
            optional_fields = selected_optional
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(Write)

    finalize_django_types()
    return DjangoSchema(query=_Query, mutation=Mutation, types=(ParentType,))


def _post(
    schema: DjangoSchema,
    data: str,
    *,
    row_id: int | None = None,
    include_path: bool = False,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        identifier = f'id: "{row_id}", ' if row_id is not None else ""
        error_fields = "field messages codes path" if include_path else "field messages codes"
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "mutation { write("
                f"{identifier}data: {{ {data} }}"
                f") {{ result {{ label amount rank }} errors {{ {error_fields} }} }} }}",
                url="/graphql-serializer-validator-binds/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.fixture
def _tables(transactional_db: None) -> Generator[None]:
    _ = transactional_db
    with connection.schema_editor() as editor:
        editor.create_model(_Parent)
        editor.create_model(_Other)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_Other)
            editor.delete_model(_Parent)


@pytest.fixture
def pg_array_other(transactional_db: None) -> Iterator[type[models.Model]]:
    _ = transactional_db

    def _array_field(base: ConcreteField) -> ConcreteField:
        array_type = read_attr(import_module("django.contrib.postgres.fields"), "ArrayField")
        if not isinstance(array_type, type) or not issubclass(array_type, models.Field):
            raise TypeError("Django's PostgreSQL ArrayField is unavailable")
        field = object_result(array_type, base)
        if not isinstance(field, models.Field):
            raise TypeError("Django's PostgreSQL ArrayField constructor returned no field")
        return field

    with isolate_apps():
        array_other: type[models.Model] = type(
            "ArrayOther",
            (models.Model,),
            {
                "__module__": __name__,
                "label": models.TextField(),
                "positives": _array_field(models.PositiveIntegerField()),
                "integers": _array_field(models.IntegerField()),
                "times": _array_field(models.TimeField()),
                "Meta": type("Meta", (), {"app_label": "scalars", "managed": False}),
            },
        )

        with connection.schema_editor() as editor:
            editor.create_model(array_other)
        try:
            yield array_other
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(array_other)


@contextmanager
def _database_zone(zone: str) -> Generator[None]:
    old = connection.settings_dict.copy()
    connection.settings_dict["TIME_ZONE"] = zone
    _ = connection.timezone, connection.timezone_name
    del connection.timezone, connection.timezone_name
    try:
        yield
    finally:
        connection.settings_dict.update(old)
        _ = connection.timezone, connection.timezone_name
        del connection.timezone, connection.timezone_name


class _BaseSerializer(ModelSerializerBase[_Parent]):
    @override
    def create(self, validated_data: dict[str, object]) -> _Parent:
        validated_data.pop("value", None)
        validated_data.pop("span", None)
        validated_data.pop("day", None)
        validated_data.pop("values", None)
        validated_data.pop("times", None)
        return _Parent.objects.create(**validated_data)

    @override
    def update(self, instance: _Parent, validated_data: dict[str, object]) -> _Parent:
        validated_data.pop("span", None)
        for name, value in validated_data.items():
            setattr(instance, name, value)
        instance.save()
        return instance


class _ValidationOnlyDefault(_BaseSerializer):
    validation_stamp = serializers.DateTimeField(
        source="occurred_at",
        read_only=True,
        default=datetime.datetime.max.replace(tzinfo=datetime.timezone.utc),
    )

    class Meta:
        model = _Parent
        fields = ("label", "occurred_at", "validation_stamp")
        validators = []


class _ReadOnlyOperand(_BaseSerializer):
    validation_stamp = serializers.DateTimeField(
        source="occurred_at",
        read_only=True,
        default=datetime.datetime.max.replace(tzinfo=datetime.timezone.utc),
    )

    class Meta:
        model = _Parent
        fields = ("label", "validation_stamp")
        validators = [
            UniqueTogetherValidator(
                queryset=_Other.objects.all(),
                fields=("validation_stamp", "label"),
            ),
        ]


class _ReadOnlyOperandFit(_ReadOnlyOperand):
    validation_stamp = serializers.DateTimeField(
        source="occurred_at",
        read_only=True,
        default=datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc),
    )


class _Annotation(_BaseSerializer):
    value = serializers.DurationField(
        write_only=True,
        validators=[UniqueValidator(queryset=_Other.objects.annotate(value=F("span")))],
    )

    class Meta:
        model = _Parent
        fields = ("label", "value")


class _In(_BaseSerializer):
    span = serializers.ListField(
        child=serializers.DurationField(),
        write_only=True,
        validators=[UniqueValidator(queryset=_Other.objects.all(), lookup="in")],
    )

    class Meta:
        model = _Parent
        fields = ("label", "span")


class _Range(_In):
    span = serializers.ListField(
        child=serializers.DurationField(),
        write_only=True,
        validators=[UniqueValidator(queryset=_Other.objects.all(), lookup="range")],
    )


class _PositiveIn(_BaseSerializer):
    values = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        validators=[
            UniqueValidator(
                queryset=_Other.objects.annotate(values=F("positive_amount")),
                lookup="in",
            ),
        ],
    )

    class Meta:
        model = _Parent
        fields = ("label", "values")


class _WideIn(_BaseSerializer):
    values = serializers.ListField(
        child=serializers.DecimalField(max_digits=None, decimal_places=0),
        write_only=True,
        validators=[
            UniqueValidator(
                queryset=_Other.objects.annotate(values=F("amount")),
                lookup="in",
            ),
        ],
    )

    class Meta:
        model = _Parent
        fields = ("label", "values")


class _Empty(_BaseSerializer):
    span = serializers.DurationField(
        write_only=True,
        validators=[UniqueValidator(queryset=_Other.objects.none())],
    )

    class Meta:
        model = _Parent
        fields = ("label", "span")


class _EmptyAfterQuerySet(models.QuerySet[_Other]):
    """Append an empty predicate after the candidate value has been prepared."""

    @override
    def filter(self, *args: object, **kwargs: object) -> models.QuerySet[_Other]:
        candidate = super().filter(*args, **kwargs)
        return candidate.none()


class _EmptyAfter(_BaseSerializer):
    span = serializers.DurationField(
        write_only=True,
        validators=[UniqueValidator(queryset=_EmptyAfterQuerySet(model=_Other))],
    )

    class Meta:
        model = _Parent
        fields = ("label", "span")


def _normalize_amount(attrs: dict[str, object]) -> None:
    if attrs["amount"] is None:
        attrs["amount"] = 1


class _Normalized(_BaseSerializer):
    span = serializers.DurationField(write_only=True)
    amount = serializers.IntegerField(allow_null=True)

    class Meta:
        model = _Parent
        fields = ("label", "span", "amount")
        validators = [
            _normalize_amount,
            UniqueTogetherValidator(queryset=_Other.objects.all(), fields=("span", "amount")),
        ]


class _EagerDate(_BaseSerializer):
    day = serializers.DateField(write_only=True)
    amount = serializers.IntegerField(allow_null=True)

    class Meta:
        model = _Parent
        fields = ("label", "day", "amount")
        validators = [
            UniqueTogetherValidator(queryset=_Other.objects.all(), fields=("day", "amount")),
        ]

    def validate_day(self, value: datetime.date) -> datetime.datetime:
        return datetime.datetime.combine(
            value,
            datetime.time(0, 30),
            tzinfo=datetime.timezone.utc,
        )


class _DelayedDuration(_BaseSerializer):
    span = serializers.DurationField(write_only=True)
    amount = serializers.IntegerField(allow_null=True)

    class Meta:
        model = _Parent
        fields = ("label", "span", "amount")
        validators = [
            UniqueTogetherValidator(queryset=_Other.objects.all(), fields=("span", "amount")),
        ]


class _FilledFromInstance(_BaseSerializer):
    class Meta:
        model = _Parent
        fields = ("label", "occurred_at")
        validators = [
            UniqueTogetherValidator(
                queryset=_Other.objects.all(),
                fields=("occurred_at", "label"),
            ),
        ]


class _Condition(_BaseSerializer):
    span = serializers.DurationField(write_only=True)

    class Meta:
        model = _Parent
        fields = ("label", "amount", "span")
        validators = [
            UniqueTogetherValidator(
                queryset=_Other.objects.all(),
                fields=("amount",),
                condition_fields=("span",),
                condition=Q(span__gt=datetime.timedelta(0)),
            ),
        ]


class _NullableCondition(_BaseSerializer):
    span = serializers.DurationField(write_only=True)

    class Meta:
        model = _Parent
        fields = (
            "label",
            "amount",
            "rank",
            "span",
        )
        validators = [
            UniqueTogetherValidator(
                queryset=_Other.objects.all(),
                fields=("amount", "rank"),
                condition_fields=("span",),
                condition=Q(span__gt=datetime.timedelta(0)),
            ),
        ]


#: ``_NullableDayCondition``'s condition, which a ``null`` day leaves to DRF's own check.
_DAY_CONDITION = Q(day__gt=datetime.date(2020, 1, 1))


class _NullableDayCondition(_BaseSerializer):
    day = serializers.DateField(allow_null=True, write_only=True)

    class Meta:
        model = _Parent
        fields = ("label", "amount", "day")
        validators = [
            UniqueTogetherValidator(
                queryset=_Other.objects.all(),
                fields=("amount",),
                condition_fields=("day",),
                condition=_DAY_CONDITION,
            ),
        ]


class _NestedTogetherChild(serializers.Serializer[object]):
    span = serializers.DurationField()
    amount = serializers.IntegerField()

    class Meta:
        validators = [
            UniqueTogetherValidator(queryset=_Other.objects.all(), fields=("span", "amount")),
        ]


class _NestedForChild(serializers.Serializer[object]):
    span = serializers.DurationField()
    day = serializers.DateField()

    class Meta:
        validators = [
            UniqueForDateValidator(queryset=_Other.objects.all(), field="span", date_field="day"),
        ]


class _NestedTogetherMid(serializers.Serializer[object]):
    child = _NestedTogetherChild()


class _NestedForMid(serializers.Serializer[object]):
    child = _NestedForChild()


class _NestedBase(_BaseSerializer):
    @override
    def create(self, validated_data: dict[str, object]) -> _Parent:
        child_data = validated_data.pop("child", None)
        mid_data = validated_data.pop("mid", None)
        if is_dict(mid_data):
            child_data = mid_data["child"]
        assert is_dict(child_data)
        parent = _Parent.objects.create(**validated_data)
        stored: dict[str, object] = {str(name): value for name, value in child_data.items()}
        span = stored["span"]
        if isinstance(span, datetime.timedelta):
            stored["span"] = min(span, datetime.timedelta(days=1))
        _ = _Other.objects.create(**stored)
        return parent


class _NestedTogetherSingle(_NestedBase):
    child = _NestedTogetherChild()

    class Meta:
        model = _Parent
        fields = ("label", "child")


class _NestedForSingle(_NestedBase):
    child = _NestedForChild()

    class Meta:
        model = _Parent
        fields = ("label", "child")


class _NestedTogetherDeep(_NestedBase):
    mid = _NestedTogetherMid()

    class Meta:
        model = _Parent
        fields = ("label", "mid")


class _NestedForDeep(_NestedBase):
    mid = _NestedForMid()

    class Meta:
        model = _Parent
        fields = ("label", "mid")


def _assert_invalid(payload: JSONObject, name: str) -> None:
    assert payload == {
        "data": {
            "write": {
                "result": None,
                "errors": [
                    {
                        "field": name,
                        "messages": ["Enter a value the database can represent."],
                        "codes": ["invalid"],
                    },
                ],
            },
        },
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_read_only_validation_default_is_not_an_omitted_root_write() -> None:
    if connection.vendor != "sqlite":
        pytest.skip("the validation-only timezone overflow is SQLite-specific")
    schema = _schema(_ValidationOnlyDefault)
    with _database_zone("Asia/Tokyo"):
        omitted = _post(schema, 'label: "omitted"')
        explicit_null = _post(schema, 'label: "null", occurredAt: null')
        supplied = _post(schema, 'label: "supplied", occurredAt: "2021-01-01T00:00:00Z"')
        refused = _post(
            schema,
            'label: "unrepresentable", occurredAt: "9999-12-31T23:30:00Z"',
        )
    _assert_invalid(refused, "occurredAt")
    assert [row.label for row in _Parent.objects.order_by("pk")] == ["omitted", "null", "supplied"]
    assert list(_Parent.objects.values_list("occurred_at", flat=True))[:2] == [None, None]
    for payload, label in ((omitted, "omitted"), (explicit_null, "null"), (supplied, "supplied")):
        assert json_at(payload, "data", "write", "result", "label") == label, payload
        assert json_at(payload, "data", "write", "errors") == [], payload
    update_schema = _schema(_ValidationOnlyDefault, operation="update")
    saved = _Parent.objects.get(label="supplied")
    original_stamp = saved.occurred_at
    with _database_zone("Asia/Tokyo"):
        updated = _post(update_schema, 'label: "renamed"', row_id=saved_pk(saved))
    assert json_at(updated, "data", "write", "errors") == [], updated
    saved.refresh_from_db()
    assert (saved.label, saved.occurred_at) == ("renamed", original_stamp)


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_read_only_default_as_a_bound_operand_keeps_its_validator_side_name() -> None:
    with override_settings(TIME_ZONE="Asia/Tokyo"):
        refused = _post(_schema(_ReadOnlyOperand), 'label: "readonly"')
        admitted = _post(_schema(_ReadOnlyOperandFit), 'label: "fit-readonly"')
    _assert_invalid(refused, "validation_stamp")
    assert json_at(admitted, "data", "write", "errors") == [], admitted
    assert list(_Parent.objects.values_list("label", "occurred_at")) == [
        ("fit-readonly", None),
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize(
    (
        "serializer",
        "value",
        "fit_value",
        "field",
    ),
    [
        (
            _Annotation,
            f'value: "{_HUGE}"',
            f'value: "{_FIT}"',
            "value",
        ),
        (
            _In,
            f'span: ["{_FIT}", "{_HUGE}"]',
            f'span: ["{_FIT}"]',
            "span",
        ),
        (
            _Range,
            f'span: ["{_FIT}", "{_HUGE}"]',
            f'span: ["{_FIT}", "2 00:00:00"]',
            "span",
        ),
    ],
)
def test_actual_annotation_and_iterable_lookups_hold_the_bound_member(
    serializer: type[DRFSerializer],
    value: str,
    fit_value: str,
    field: str,
) -> None:
    schema = _schema(serializer)
    payload = _post(schema, f'label: "probe", {value}')
    if connection.vendor == "sqlite":
        _assert_invalid(payload, field)
        assert not _Parent.objects.exists()
    else:
        assert json_at(payload, "data", "write", "errors") == [], payload
        assert _Parent.objects.filter(label="probe").exists()
    fit = _post(schema, f'label: "fit", {fit_value}')
    assert json_at(fit, "data", "write", "errors") == [], fit
    assert _Parent.objects.filter(label="fit").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize(
    ("serializer", "value", "field"),
    [
        (_Annotation, f'value: "{_FIT}"', "value"),
        (_In, f'span: ["{_FIT}", "2 00:00:00"]', "span"),
        (_Range, f'span: ["{_FIT}", "2 00:00:00"]', "span"),
    ],
)
def test_actual_lookup_keeps_drfs_ordinary_duplicate_answer(
    serializer: type[DRFSerializer],
    value: str,
    field: str,
) -> None:
    _ = _Other.objects.create(label="existing", span=datetime.timedelta(days=1))
    payload = _post(_schema(serializer), f'label: "duplicate", {value}')
    assert json_at(payload, "data", "write", "result") is None, payload
    assert json_at(payload, "data", "write", "errors", 0, "field") == field, payload
    assert json_at(payload, "data", "write", "errors", 0, "codes") == ["unique"], payload
    assert not _Parent.objects.exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_positive_column_in_lookup_binds_a_negative_sqlite_integer() -> None:
    if connection.vendor != "sqlite":
        pytest.skip("the positive column versus signed driver range control uses SQLite")
    schema = _schema(_PositiveIn)
    negative = _post(schema, 'label: "negative-no-match", values: [-1]')
    assert json_at(negative, "data", "write", "errors") == [], negative
    _ = _Other.objects.create(label="positive-row", positive_amount=1)
    fitting = _post(schema, 'label: "positive-no-match", values: [2]')
    duplicate = _post(schema, 'label: "positive-duplicate", values: [1]')
    assert json_at(fitting, "data", "write", "errors") == [], fitting
    assert json_at(duplicate, "data", "write", "result") is None, duplicate
    assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"]
    assert list(_Parent.objects.order_by("pk").values_list("label", flat=True)) == [
        "negative-no-match",
        "positive-no-match",
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_postgresql_client_integer_literal_past_column_width_remains_a_no_match() -> None:
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL client cursor integer literal control")
    configuration = require(read_attr(connection, "settings_dict"), is_dict)
    options = require(configuration["OPTIONS"], is_dict)
    if options.get("server_side_binding", False):
        pytest.skip("requires PostgreSQL client-side cursor binding")
    schema = _schema(_WideIn)
    wide = _post(schema, 'label: "wide-no-match", values: ["34359738368"]')
    assert json_at(wide, "data", "write", "errors") == [], wide
    _ = _Other.objects.create(label="one", amount=1)
    duplicate = _post(schema, 'label: "one-duplicate", values: ["1"]')
    assert json_at(duplicate, "data", "write", "result") is None, duplicate
    assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"]
    assert list(_Parent.objects.values_list("label", flat=True)) == ["wide-no-match"]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_postgresql_server_binding_distinguishes_typed_and_raw_integer_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RawEquals(BuiltinLookup):
        lookup_name = "raw_equals"

        @override
        def get_rhs_op(self, connection: object, rhs: str) -> str:
            return f"= {rhs}"

    amount_field = _Other._meta.get_field("amount")
    assert isinstance(amount_field, models.IntegerField)
    amount_field.register_lookup(RawEquals)

    class RawWide(_BaseSerializer):
        value = serializers.DecimalField(
            max_digits=None,
            decimal_places=0,
            write_only=True,
            validators=[
                UniqueValidator(
                    queryset=_Other.objects.annotate(value=F("amount")),
                    lookup="raw_equals",
                ),
            ],
        )

        class Meta:
            model = _Parent
            fields = ("label", "value")

    settings = require(read_attr(connection, "settings_dict"), is_dict)
    options = require(settings.get("OPTIONS"), is_dict)
    connection.close()
    try:
        with monkeypatch.context() as configured:
            configured.setitem(options, "server_side_binding", value=True)
            raw = _post(_schema(RawWide), 'label: "raw-wide", value: "34359738368"')
            typed = _post(_schema(_WideIn), 'label: "typed-wide", values: ["34359738368"]')
            assert json_at(raw, "data", "write", "errors") == [], raw
            _assert_invalid(typed, "values")
    finally:
        connection.close()
        lookups = require(read_attr(amount_field, "instance_lookups"), is_dict)
        lookups.pop("raw_equals", None)
    assert list(_Parent.objects.values_list("label", flat=True)) == ["raw-wide"]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_postgresql_positive_array_uses_its_signed_cast_width(
    pg_array_other: type[models.Model],
) -> None:
    array_other = pg_array_other

    class PositiveArray(_BaseSerializer):
        values = serializers.ListField(
            child=serializers.DecimalField(max_digits=None, decimal_places=0),
            write_only=True,
            validators=[
                UniqueValidator(
                    queryset=array_other._default_manager.annotate(values=F("positives")),
                ),
            ],
        )

        class Meta:
            model = _Parent
            fields = ("label", "values")

    _ = array_other._default_manager.create(
        label="existing",
        positives=[1],
        integers=[4],
        times=[datetime.time(9), datetime.time(10)],
    )
    schema = _schema(PositiveArray)
    negative = _post(schema, 'label: "negative-no-match", values: ["-1"]')
    fitting = _post(schema, 'label: "fitting-no-match", values: ["2"]')
    duplicate = _post(schema, 'label: "duplicate", values: ["1"]')
    overflow = _post(schema, 'label: "cast-overflow", values: ["34359738368"]')
    for payload in (negative, fitting):
        assert json_at(payload, "data", "write", "errors") == [], payload
    assert json_at(duplicate, "data", "write", "result") is None, duplicate
    assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"]
    _assert_invalid(overflow, "values")
    assert list(_Parent.objects.order_by("pk").values_list("label", flat=True)) == [
        "negative-no-match",
        "fitting-no-match",
    ]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_postgresql_integer_array_gt_uses_the_selected_driver_oid(
    pg_array_other: type[models.Model],
) -> None:
    if read_attr(read_attr(read_attr(connection, "Database"), "adapt"), "Transformer") is None:
        pytest.skip("the selected array OID path requires psycopg 3")
    array_other = pg_array_other

    class IntegerArrayGT(_BaseSerializer):
        values = serializers.ListField(
            child=serializers.DecimalField(max_digits=None, decimal_places=0),
            write_only=True,
            validators=[
                UniqueValidator(
                    queryset=array_other._default_manager.annotate(values=F("integers")),
                    lookup="gt",
                ),
            ],
        )

        class Meta:
            model = _Parent
            fields = ("label", "values")

    _ = array_other._default_manager.create(
        label="higher-array",
        positives=[1],
        integers=[4],
        times=[datetime.time(9), datetime.time(10)],
    )
    schema = _schema(IntegerArrayGT)
    overflow = _post(schema, 'label: "oid-overflow", values: ["34359738368"]')
    _assert_invalid(overflow, "values")
    assert not _Parent.objects.exists()
    fitting = _post(schema, 'label: "oid-no-match", values: ["5"]')
    assert json_at(fitting, "data", "write", "errors") == [], fitting
    matched = _post(schema, 'label: "oid-match", values: ["2"]')
    assert json_at(matched, "data", "write", "result") is None, matched
    assert json_at(matched, "data", "write", "errors", 0, "codes") == ["unique"]
    assert list(_Parent.objects.values_list("label", flat=True)) == ["oid-no-match"]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_postgresql_recoverable_list_dump_stays_with_drfs_no_match(
    pg_array_other: type[models.Model],
) -> None:
    array_other = pg_array_other

    class TimeArray(_BaseSerializer):
        times = serializers.ListField(
            child=serializers.TimeField(),
            write_only=True,
            validators=[UniqueValidator(queryset=array_other._default_manager.all(), lookup="gt")],
        )

        class Meta:
            model = _Parent
            fields = ("label", "times")

    _ = array_other._default_manager.create(
        label="later",
        positives=[1],
        integers=[4],
        times=[datetime.time(11), datetime.time(12)],
    )
    schema = _schema(TimeArray)
    mixed = _post(schema, 'label: "mixed", times: ["09:00:00", "10:00:00+02:00"]')
    assert json_at(mixed, "data", "write", "errors") == [], mixed
    duplicate = _post(schema, 'label: "duplicate", times: ["09:00:00", "10:00:00"]')
    assert json_at(duplicate, "data", "write", "result") is None, duplicate
    assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"]
    assert list(_Parent.objects.values_list("label", flat=True)) == ["mixed"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_empty_queryset_does_not_bind_the_serializer_only_duration() -> None:
    schema = _schema(_Empty)
    payload = _post(schema, f'label: "empty", span: "{_HUGE}"')
    assert json_at(payload, "data", "write", "errors") == [], payload
    assert _Parent.objects.filter(label="empty").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_later_empty_predicate_drops_prepared_params_before_execution() -> None:
    payload = _post(_schema(_EmptyAfter), f'label: "later-empty", span: "{_HUGE}"')
    assert json_at(payload, "data", "write", "errors") == [], payload
    assert _Parent.objects.filter(label="later-empty").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_prior_validator_normalization_is_seen_by_the_actual_together_query() -> None:
    schema = _schema(_Normalized)
    payload = _post(schema, f'label: "normalized", span: "{_HUGE}", amount: null')
    if connection.vendor == "sqlite":
        _assert_invalid(payload, "span")
        assert not _Parent.objects.exists()
    else:
        assert json_at(payload, "data", "write", "errors") == [], payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_eager_date_prep_fails_even_when_null_skips_later_exists() -> None:
    schema = _schema(_EagerDate)
    with override_settings(TIME_ZONE="America/New_York"):
        refused = _post(schema, 'label: "early", day: "0001-01-01", amount: null')
        admitted = _post(schema, 'label: "fit", day: "2021-01-01", amount: null')
    _assert_invalid(refused, "day")
    assert json_at(admitted, "data", "write", "errors") == [], admitted
    delayed = _post(_schema(_DelayedDuration), f'label: "delayed", span: "{_HUGE}", amount: null')
    assert json_at(delayed, "data", "write", "errors") == [], delayed
    assert list(_Parent.objects.order_by("pk").values_list("label", flat=True)) == [
        "fit",
        "delayed",
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize(
    ("serializer", "level", "kind"),
    [
        (_NestedTogetherSingle, "single", "together"),
        (_NestedForSingle, "single", "for-date"),
        (_NestedTogetherDeep, "deep", "together"),
        (_NestedForDeep, "deep", "for-date"),
    ],
)
def test_nested_serializer_owns_its_bind_error_at_each_depth(
    serializer: type[DRFSerializer],
    level: str,
    kind: str,
) -> None:
    if connection.vendor != "sqlite":
        pytest.skip("SQLite duration binding provides the signed-64 refusal")
    nested = (
        {"child": NestedSerializerConfig()}
        if level == "single"
        else {"mid": NestedSerializerConfig(nested_fields={"child": NestedSerializerConfig()})}
    )
    schema = _schema(serializer, nested_fields=nested)
    partner = "amount: 8" if kind == "together" else 'day: "2022-01-01"'
    duplicate_partner = "amount: 7" if kind == "together" else 'day: "2021-01-01"'
    _ = _Other.objects.create(
        label="duplicate-source",
        span=datetime.timedelta(days=2),
        amount=7,
        day=datetime.date(2021, 1, 1),
    )

    def _nested(span: str, other: str) -> str:
        child = f'child: {{ span: "{span}", {other} }}'
        return child if level == "single" else f"mid: {{ {child} }}"

    refused = _post(schema, f'label: "refused", {_nested(_HUGE, partner)}', include_path=True)
    path = ["child", "span"] if level == "single" else ["mid", "child", "span"]
    assert json_at(refused, "data", "write", "result") is None, refused
    assert json_at(refused, "data", "write", "errors") == [
        {
            "field": ".".join(path),
            "path": path,
            "messages": ["Enter a value the database can represent."],
            "codes": ["invalid"],
        },
    ], refused
    assert not _Parent.objects.exists()
    assert _Other.objects.count() == 1

    fitting = _post(schema, f'label: "fitting", {_nested("3 00:00:00", partner)}')
    assert json_at(fitting, "data", "write", "errors") == [], fitting
    duplicate = _post(
        schema,
        f'label: "duplicate", {_nested("2 00:00:00", duplicate_partner)}',
        include_path=True,
    )
    assert json_at(duplicate, "data", "write", "result") is None, duplicate
    assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"], duplicate
    assert list(_Parent.objects.values_list("label", flat=True)) == ["fitting"]
    assert _Other.objects.count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_update_instance_value_is_prepared_by_the_other_models_date_field() -> None:
    row = _Parent.objects.create(
        label="before",
        occurred_at=datetime.datetime(1, 1, 1, 0, 30, tzinfo=datetime.timezone.utc),
    )
    schema = _schema(_FilledFromInstance, operation="update")
    with override_settings(TIME_ZONE="America/New_York"):
        payload = _post(schema, 'label: "after"', row_id=saved_pk(row))
    _assert_invalid(payload, "occurredAt")
    row.refresh_from_db()
    assert row.label == "before"
    fit = _Parent.objects.create(
        label="fit-before",
        occurred_at=datetime.datetime(2021, 1, 1, 0, 30, tzinfo=datetime.timezone.utc),
    )
    with override_settings(TIME_ZONE="America/New_York"):
        admitted = _post(schema, 'label: "fit-after"', row_id=saved_pk(fit))
    assert json_at(admitted, "data", "write", "errors") == [], admitted
    fit.refresh_from_db()
    assert fit.label == "fit-after"


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize(
    ("zone", "edge"),
    [
        pytest.param("America/New_York", "9999-12-31T12:00:00Z", id="last-year-behind-utc"),
        pytest.param("Asia/Tokyo", "0001-01-01T00:30:00Z", id="first-year-ahead-of-utc"),
    ],
)
def test_unique_for_year_datetime_bound_is_the_date_fields_error(zone: str, edge: str) -> None:
    """A ``date_field`` datetime whose year bound the backend cannot bind is that field's error.

    DRF's ``UniqueForYearValidator`` filters ``occurred_at__year``; over a datetime column
    Django binds the year's first and last instants in the current time zone, and on
    SQLite projects them onto UTC, which leaves years 1..9999 at either end of the range.
    The stored value itself binds, so the year bound alone is refused, as ``occurredAt``'s
    ``invalid`` error with nothing written. PostgreSQL binds the aware bounds; the write
    goes through there. A fitting year is written, and a repeat of its label is DRF's own
    ``unique`` error.
    """

    class UniqueLabelPerYear(_BaseSerializer):
        class Meta:
            model = _Parent
            fields = ("label", "occurred_at")
            validators = [
                UniqueForYearValidator(
                    queryset=_Parent.objects.all(),
                    field="label",
                    date_field="occurred_at",
                ),
            ]

    schema = _schema(UniqueLabelPerYear)
    with override_settings(TIME_ZONE=zone):
        edge_payload = _post(schema, f'label: "edge", occurredAt: "{edge}"')
        fitting = _post(schema, 'label: "fit", occurredAt: "2021-06-01T12:00:00Z"')
        repeated = _post(schema, 'label: "fit", occurredAt: "2021-09-01T12:00:00Z"')
    if connection.vendor == "sqlite":
        _assert_invalid(edge_payload, "occurredAt")
    else:
        assert json_at(edge_payload, "data", "write", "errors") == [], edge_payload
    assert json_at(fitting, "data", "write", "errors") == [], fitting
    assert json_at(repeated, "data", "write", "result") is None, repeated
    assert json_at(repeated, "data", "write", "errors", 0, "field") == "label", repeated
    assert json_at(repeated, "data", "write", "errors", 0, "codes") == ["unique"], repeated
    written = ["fit"] if connection.vendor == "sqlite" else ["edge", "fit"]
    assert list(_Parent.objects.order_by("pk").values_list("label", flat=True)) == written


#: An aware instant whose date in New York is in year 0: ``DateField`` cannot prepare it.
_BEFORE_YEAR_ONE = datetime.datetime(1, 1, 1, 0, 30, tzinfo=datetime.timezone.utc)


class _OtherBeforeYearOneQuerySet(models.QuerySet[_Other]):
    """A consumer queryset whose ``filter`` adds its own ``day`` constant to every filter."""

    @override
    def filter(self, *args: object, **kwargs: object) -> models.QuerySet[_Other]:
        return super().filter(*args, day__gt=_BEFORE_YEAR_ONE, **kwargs)


class _ParentLastYearQuerySet(models.QuerySet[_Parent]):
    """A consumer queryset whose ``filter`` adds its own ``occurred_at`` year to every filter."""

    @override
    def filter(self, *args: object, **kwargs: object) -> models.QuerySet[_Parent]:
        return super().filter(*args, occurred_at__year=9999, **kwargs)


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize(
    "queryset",
    [
        pytest.param(_OtherBeforeYearOneQuerySet(model=_Other), id="prepared-constant"),
        pytest.param(_ParentLastYearQuerySet(model=_Parent), id="compiled-constant"),
    ],
)
def test_a_validator_querysets_own_overflowing_constant_is_no_field_error(
    queryset: models.QuerySet[models.Model],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An ``OverflowError`` a validator queryset's own constant raises is not the client's.

    The consumer's ``filter`` adds a constant no serializer field supplies: an aware date
    ``DateField`` preparation cannot make naive in New York, or a year whose last instant
    SQLite cannot project onto UTC. The guard names no field for it, so the error is the
    query's own: the mutation fails as an unexpected error (the ``OverflowError`` logged),
    nothing written, never as ``label``'s ``invalid`` error. PostgreSQL binds the compiled
    year bound, so that row is SQLite's.
    """
    if queryset.model is _Parent and connection.vendor != "sqlite":
        pytest.skip("only SQLite projects a datetime year bound onto UTC")

    class UniqueLabel(_BaseSerializer):
        class Meta:
            model = _Parent
            fields = ("label",)
            extra_kwargs = {"label": {"validators": [UniqueValidator(queryset=queryset)]}}

    with override_settings(TIME_ZONE="America/New_York"):
        payload = _post(_schema(UniqueLabel), 'label: "constant"')
    assert json_at(payload, "data") is None, payload
    assert json_at(payload, "errors", 0, "message") == "An unexpected error occurred.", payload
    assert {record.exc_info[0] for record in caplog.records if record.exc_info} == {OverflowError}
    assert not _Parent.objects.exists()


def _drf_queries_other(schema: DjangoSchema, data: str, *, row_id: int) -> bool:
    """Whether the update ``data`` on ``row_id`` runs a statement reading ``_Other``'s table.

    Sent with a duration every backend binds, the write leaves the guard nothing to hold,
    so whether a uniqueness statement runs is the installed DRF validator's own decision.
    """
    table = connection.ops.quote_name(_Other._meta.db_table)
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, data, row_id=row_id)
    assert json_at(payload, "data", "write", "errors") == [], payload
    return any(table in query["sql"] for query in queries.captured_queries)


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize(
    (
        "serializer_class",
        "stored",
        "data",
        "written",
    ),
    [
        pytest.param(_Condition, {"amount": 1}, 'span: "{}"', {}, id="condition-only-change"),
        pytest.param(
            _NullableCondition,
            {"amount": None, "rank": 1},
            'rank: 2, span: "{}"',
            {"rank": 2},
            id="omitted-null-partner",
        ),
    ],
)
def test_drf_owns_condition_only_change_and_omitted_null_decisions(
    serializer_class: type[DRFSerializer],
    stored: dict[str, int | None],
    data: str,
    written: dict[str, int],
) -> None:
    """Whether an update changing only a condition value, or omitting a null partner, queries is DRF's.

    The installed DRF decides whether a changed ``condition_fields`` value counts as a change
    and whether a null constraint value skips the check; the update sent with a fitting
    duration on a twin row asks it. The same update with a duration past 64 bits of
    microseconds is held exactly where DRF queries, as ``span``'s ``invalid`` error on SQLite,
    with nothing written, and is written everywhere else.
    """
    schema = _schema(serializer_class, operation="update")
    twin = _Parent.objects.create(label="twin", **stored)
    row = _Parent.objects.create(label="row", **stored)
    queried = _drf_queries_other(schema, data.format(_FIT), row_id=saved_pk(twin))
    payload = _post(schema, data.format(_HUGE), row_id=saved_pk(row))
    if queried and connection.vendor == "sqlite":
        _assert_invalid(payload, "span")
        assert _Parent.objects.filter(pk=saved_pk(row), **stored).exists()
    else:
        assert json_at(payload, "data", "write", "errors") == [], payload
        assert _Parent.objects.filter(pk=saved_pk(row), **(stored | written)).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_nulls_distinct_false_binds_the_nullable_constraint_only_when_supported() -> None:
    if "nulls_distinct" not in inspect.signature(UniqueTogetherValidator).parameters:
        pytest.skip("this DRF release has no nulls_distinct constructor argument")
    if connection.vendor != "sqlite":
        pytest.skip("the signed-64 duration bind refusal uses SQLite")

    class NullBound(_BaseSerializer):
        span = serializers.DurationField(write_only=True)
        amount = serializers.IntegerField(allow_null=True)

        class Meta:
            model = _Parent
            fields = ("label", "span", "amount")
            validators = [
                UniqueTogetherValidator(
                    queryset=_Other.objects.all(),
                    fields=("span", "amount"),
                    nulls_distinct=False,
                ),
            ]

    schema = _schema(NullBound)
    refused = _post(schema, f'label: "refused-null", span: "{_HUGE}", amount: null')
    fitting = _post(schema, f'label: "fitting-null", span: "{_FIT}", amount: null')
    _assert_invalid(refused, "span")
    assert json_at(fitting, "data", "write", "errors") == [], fitting
    assert list(_Parent.objects.values_list("label", flat=True)) == ["fitting-null"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
def test_nullable_condition_uses_the_installed_django_q_check_body() -> None:
    _ = _Other.objects.create(
        label="matched-other",
        amount=1,
        day=datetime.date(2021, 1, 1),
    )
    payload = _post(
        _schema(_NullableDayCondition),
        'label: "nullable-condition", amount: 1, day: null',
    )
    # DRF's own condition check, over the installed Django's ``Q.check``, decides the null
    # day; the guarded check answers as it does.
    duplicate = qs_exists_with_condition(
        _Other.objects.filter(amount=1),
        _DAY_CONDITION,
        {"day": None},
    )
    if duplicate:
        assert json_at(payload, "data", "write", "result") is None, payload
        assert json_at(payload, "data", "write", "errors") != [], payload
        assert not _Parent.objects.exists()
    else:
        assert json_at(payload, "data", "write", "errors") == [], payload
        assert _Parent.objects.filter(label="nullable-condition").exists()


@pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite duration integer binding")
@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize("short_circuit", ["full", "empty"])
@pytest.mark.parametrize("duplicate", [False, True], ids=["available", "duplicate"])
def test_discarded_predicate_with_an_equal_surviving_decimal_keeps_drfs_decision(
    short_circuit: str,
    *,
    duplicate: bool,
) -> None:
    """Native result-set shortcuts drop the duration, despite an equal decimal surviving."""
    if duplicate:
        _ = _Other.objects.create(label="kept")
    duration = datetime.timedelta(days=999999999)
    decimal_value = Decimal(86399999913600000000)
    predicate = (
        Q(span=duration) | ~Q(pk__in=[])
        if short_circuit == "full"
        else (Q(span=duration) & Q(pk__in=[])) | Q(label="kept")
    )
    decimal_field: ConcreteField = models.DecimalField(max_digits=24, decimal_places=0)
    candidates = _Other.objects.filter(predicate).annotate(
        value=Value(decimal_value, output_field=decimal_field),
    )

    class DecimalOperand(_BaseSerializer):
        value = serializers.DecimalField(
            max_digits=24,
            decimal_places=0,
            write_only=True,
            validators=[UniqueValidator(queryset=candidates)],
        )

        class Meta:
            model = _Parent
            fields = ("label", "value")

    native = DecimalOperand(data={"label": "native", "value": str(decimal_value)})
    assert native.is_valid() is not duplicate
    native_errors = require(read_attr(native, "errors"), is_dict)
    if duplicate:
        assert read_attr(json_at(native_errors, "value", 0), "code") == "unique"
    else:
        assert native_errors == {}
    payload = _post(_schema(DecimalOperand), f'label: "written", value: "{decimal_value}"')
    if duplicate:
        assert json_at(payload, "data", "write", "result") is None, payload
        assert json_at(payload, "data", "write", "errors", 0, "field") == "value", payload
        assert json_at(payload, "data", "write", "errors", 0, "codes") == ["unique"], payload
        assert not _Parent.objects.exists()
    else:
        assert json_at(payload, "data", "write", "errors") == [], payload
        assert _Parent.objects.filter(label="written").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize("family", ["field", "for_date"])
def test_plain_nested_dotted_scalar_uses_the_validators_native_source_leaf(
    family: str,
) -> None:
    """A supported serializer-only dotted scalar keeps its declared nested error path."""
    field_validators = (
        [UniqueValidator(queryset=_Other.objects.all())] if family == "field" else []
    )

    def _normalize_stamp(attrs: dict[str, object]) -> None:
        attrs["stamp"] = require(attrs["payload"], is_dict)["day"]

    class Payload(serializers.Serializer[object]):
        stamp = serializers.DateTimeField(
            source="payload.day",
            default_timezone=datetime.timezone.utc,
            validators=field_validators,
        )
        day = serializers.DateField()

        class Meta:
            validators = (
                [
                    _normalize_stamp,
                    UniqueForDateValidator(
                        queryset=_Other.objects.all(),
                        field="stamp",
                        date_field="day",
                    ),
                ]
                if family == "for_date"
                else []
            )

    class NestedPayload(_BaseSerializer):
        child = Payload()

        class Meta:
            model = _Parent
            fields = ("label", "child")

        @override
        def create(self, validated_data: dict[str, object]) -> _Parent:
            _ = validated_data.pop("child")
            return _Parent.objects.create(**validated_data)

    schema = _schema(NestedPayload, nested_fields={"child": NestedSerializerConfig()})
    with override_settings(TIME_ZONE="America/New_York"):
        native = Payload(data={"stamp": "2021-01-01T12:00:00Z", "day": "2021-01-01"})
        assert native.is_valid()
        refused = _post(
            schema,
            'label: "refused", child: { stamp: "0001-01-01T00:30:00Z", day: "2021-01-01" }',
            include_path=True,
        )
        assert json_at(refused, "data", "write", "result") is None, refused
        assert json_at(refused, "data", "write", "errors") == [
            {
                "field": "child.stamp",
                "path": ["child", "stamp"],
                "messages": ["Enter a value the database can represent."],
                "codes": ["invalid"],
            },
        ], refused
        assert not _Parent.objects.exists()
        fitting = _post(
            schema,
            'label: "fitting", child: { stamp: "2021-01-01T12:00:00Z", day: "2021-01-01" }',
        )
        assert json_at(fitting, "data", "write", "errors") == [], fitting
        _ = _Other.objects.create(label="duplicate", day=datetime.date(2021, 1, 1))
        duplicate = _post(
            schema,
            'label: "duplicate", child: { stamp: "2021-01-01T12:00:00Z", day: "2021-01-01" }',
        )
        assert json_at(duplicate, "data", "write", "result") is None, duplicate
        assert json_at(duplicate, "data", "write", "errors", 0, "field") == "child.stamp", (
            duplicate
        )
        assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"], duplicate
    assert list(_Parent.objects.values_list("label", flat=True)) == ["fitting"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("_tables")
@pytest.mark.parametrize("optional_owner", ["root", "child"])
def test_nested_agreement_uses_its_own_model_and_optional_field_context(
    optional_owner: str,
) -> None:
    """Equal field names at different levels keep each level's model and optionality."""

    class Child(serializers.Serializer[object]):
        amount = serializers.CharField()

    class NestedLabel(_BaseSerializer):
        child = Child()

        class Meta:
            model = _Parent
            fields = ("label", "amount", "child")

        @override
        def create(self, validated_data: dict[str, object]) -> _Parent:
            child = require(validated_data.pop("child"), is_dict)
            validated_data["amount"] = child["amount"]
            return _Parent.objects.create(**validated_data)

    schema = _schema(
        NestedLabel,
        optional_fields=("amount",) if optional_owner == "root" else None,
        nested_fields={
            "child": NestedSerializerConfig(
                optional_fields=("amount",) if optional_owner == "child" else None,
            ),
        },
    )
    payload = _post(schema, 'label: "written", child: { amount: "7" }')
    assert json_at(payload, "data", "write", "errors") == [], payload
    assert json_at(payload, "data", "write", "result", "amount") == 7, payload
    assert list(_Parent.objects.values_list("label", "amount")) == [("written", 7)]
