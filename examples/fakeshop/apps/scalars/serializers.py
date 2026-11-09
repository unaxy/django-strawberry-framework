"""DRF serializers for the scalars app's live serializer-mutation surface.

A plain DRF ``ModelSerializer`` declared the standard DRF way (over the shared
``examples/fakeshop/drf_serializers.py::ModelSerializerBase``; no package imports);
``apps/scalars/schema.py`` wraps it in the shipped ``SerializerMutation`` base, the
serializer half of the temporal write surface over ``ScalarSpecimen``.

``UniqueScalarSpecimenSerializer`` writes ``UniqueScalarSpecimen``, whose columns DRF's
``UniqueValidator`` / ``UniqueTogetherValidator`` bind in a query inside ``is_valid()``; its
``validate_opened_at`` reads the instant sent as shop time.
``UniqueScalarSpecimenUnboundedAmountSerializer`` declares ``amount`` as a ``DecimalField``
holding no digits, with an explicit two-field DRF uniqueness validator after its field hook.
``TagWithUniqueSpecimensSerializer`` writes a ``ScalarSpecimenTag`` and a bundle of
specimens, a nested writable ``specimens`` list of ``UniqueScalarSpecimenSerializer`` items,
which its own ``create()`` writes; the specimens hold no key to the tag.
"""

import datetime
from decimal import Decimal
from typing import TypedDict

from drf_serializers import ModelSerializerBase
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from typing_extensions import NotRequired, override

from .models import ScalarSpecimen, ScalarSpecimenTag, UniqueScalarSpecimen

#: The shop's fixed wall-clock offset, one hour behind UTC.
SHOP_TIME = datetime.timezone(datetime.timedelta(hours=-1), "shop time")


class ScalarSpecimenTemporalSerializer(ModelSerializerBase[ScalarSpecimen]):
    """``ModelSerializer`` over ``ScalarSpecimen``'s required columns, temporal ones included.

    DRF's ``DateTimeField`` refuses an aware value it cannot project onto the current time
    zone with its own ``overflow`` error, and the mutation answers that error too for a
    naive value it cannot make aware there and, under ``USE_TZ = False``, an aware value it
    cannot project onto UTC; its ``TimeField`` passes an aware time through,
    which SQLite cannot store, and the mutation answers that as the field's ``invalid``
    error before the save. The time is written through ``clock_time``, renamed onto the
    ``occurred_time`` column by ``source=``, so the refusal is keyed to the input the client
    sent (``clockTime``), not the column.
    """

    clock_time = serializers.TimeField(source="occurred_time")

    class Meta:
        model = ScalarSpecimen
        fields = (
            "label",
            "occurred_on",
            "occurred_at",
            "clock_time",
            "external_id",
        )


class UniqueScalarSpecimenSerializer(ModelSerializerBase[UniqueScalarSpecimen]):
    """``ModelSerializer`` over ``UniqueScalarSpecimen``, each column under a uniqueness rule.

    DRF builds a ``UniqueValidator`` for ``label`` and ``opened_time`` and a
    ``UniqueTogetherValidator`` for ``opened_at`` with ``label``. ``validate_opened_at`` reads
    the wall clock sent as ``SHOP_TIME``, so ``9999-12-31T23:30:00`` becomes an instant past
    year 9999 in UTC, which the database cannot store. The mutation answers an aware time
    and that instant as the field's ``invalid`` error before a validator binds either.
    """

    class Meta:
        model = UniqueScalarSpecimen
        fields = (
            "label",
            "opened_time",
            "opened_at",
            "amount",
            "active",
        )

    def validate_opened_at(self, value: datetime.datetime) -> datetime.datetime:
        """Read the wall clock sent as ``SHOP_TIME``."""
        return value.replace(tzinfo=SHOP_TIME)


class UniqueScalarSpecimenUnboundedAmountSerializer(UniqueScalarSpecimenSerializer):
    """``UniqueScalarSpecimenSerializer`` declaring ``amount`` as a digitless ``DecimalField``.

    DRF's ``DecimalField(max_digits=None, decimal_places=None)`` passes any finite decimal, so
    a zero whose exponent PostgreSQL's ``numeric`` refuses passes field conversion. A
    two-field ``UniqueTogetherValidator`` queries ``amount`` and ``active`` after the
    field hook; the mutation answers an unbindable query operand as the field's
    ``invalid`` error.
    """

    amount = serializers.DecimalField(max_digits=None, decimal_places=None)

    class Meta(UniqueScalarSpecimenSerializer.Meta):
        validators = [
            UniqueTogetherValidator(
                queryset=UniqueScalarSpecimen.objects.all(),
                fields=("amount", "active"),
            ),
        ]

    def validate_amount(self, value: Decimal) -> Decimal:
        """Let a fitting input become an unbindable operand for the uniqueness check."""
        return Decimal("0E+1073741824") if value == Decimal(7) else value


class UniqueScalarSpecimenReadOnlyLabelSerializer(ModelSerializerBase[UniqueScalarSpecimen]):
    """Use a read-only default to complete the opened-at uniqueness validator's pair."""

    default_label = serializers.CharField(source="label", read_only=True, default="defaulted")

    class Meta:
        model = UniqueScalarSpecimen
        fields = (
            "default_label",
            "opened_time",
            "opened_at",
            "amount",
            "active",
        )
        validators = [
            UniqueTogetherValidator(
                queryset=UniqueScalarSpecimen.objects.all(),
                fields=("opened_at", "default_label"),
            ),
        ]

    def validate_opened_at(self, value: datetime.datetime) -> datetime.datetime:
        """Read the wall clock sent as ``SHOP_TIME``."""
        return value.replace(tzinfo=SHOP_TIME)


class _UniqueSpecimenData(TypedDict):
    """One validated ``UniqueScalarSpecimenSerializer`` item."""

    label: str
    opened_time: datetime.time
    opened_at: datetime.datetime
    amount: object
    active: NotRequired[bool]


class _TagWithUniqueSpecimensData(TypedDict):
    """``TagWithUniqueSpecimensSerializer``'s validated data, nested specimens included."""

    label: str
    specimens: list[_UniqueSpecimenData]


class TagWithUniqueSpecimensSerializer(ModelSerializerBase[ScalarSpecimenTag]):
    """A ``ScalarSpecimenTag`` serializer writing a bundle of specimens beside the tag.

    Each item is a ``UniqueScalarSpecimenSerializer``, whose own ``UniqueValidator`` /
    ``UniqueTogetherValidator`` bind its values in a query inside ``is_valid()``. The mutation
    opts the list in with ``Meta.nested_fields``, and ``create()`` writes the tag and then
    each specimen itself, storing an aware ``opened_time`` as its wall clock with the offset
    dropped (SQLite stores no aware time).
    """

    specimens = UniqueScalarSpecimenSerializer(many=True)

    class Meta:
        model = ScalarSpecimenTag
        fields = ("label", "specimens")

    @override
    def create(self, validated_data: _TagWithUniqueSpecimensData) -> ScalarSpecimenTag:
        tag = ScalarSpecimenTag.objects.create(label=validated_data["label"])
        for specimen in validated_data["specimens"]:
            _ = UniqueScalarSpecimen.objects.create(
                **{**specimen, "opened_time": specimen["opened_time"].replace(tzinfo=None)},
            )
        return tag


class TagWithReadOnlyLabelSpecimensSerializer(ModelSerializerBase[ScalarSpecimenTag]):
    """Write nested specimens whose uniqueness partner is a read-only default."""

    specimens = UniqueScalarSpecimenReadOnlyLabelSerializer(many=True)

    class Meta:
        model = ScalarSpecimenTag
        fields = ("label", "specimens")

    @override
    def create(self, validated_data: _TagWithUniqueSpecimensData) -> ScalarSpecimenTag:
        tag = ScalarSpecimenTag.objects.create(label=validated_data["label"])
        for specimen in validated_data["specimens"]:
            _ = UniqueScalarSpecimen.objects.create(
                **{
                    **specimen,
                    "label": "defaulted",
                    "opened_time": specimen["opened_time"].replace(tzinfo=None),
                },
            )
        return tag
