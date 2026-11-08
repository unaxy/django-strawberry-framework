"""DRF serializers for the scalars app's live serializer-mutation surface.

A plain DRF ``ModelSerializer`` declared the standard DRF way (over the shared
``examples/fakeshop/drf_serializers.py::ModelSerializerBase``; no package imports);
``apps/scalars/schema.py`` wraps it in the shipped ``SerializerMutation`` base, the
serializer half of the temporal write surface over ``ScalarSpecimen``.

``UniqueScalarSpecimenSerializer`` writes ``UniqueScalarSpecimen``, whose columns DRF's
``UniqueValidator`` / ``UniqueTogetherValidator`` bind in a query inside ``is_valid()``; its
``validate_opened_at`` reads the instant sent as shop time.
``UniqueScalarSpecimenUnboundedAmountSerializer`` declares ``amount`` as a ``DecimalField``
holding no digits, which passes a decimal PostgreSQL's ``numeric`` refuses.
"""

import datetime

from drf_serializers import ModelSerializerBase
from rest_framework import serializers

from .models import ScalarSpecimen, UniqueScalarSpecimen

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
    a zero whose exponent PostgreSQL's ``numeric`` refuses reaches the conditional
    ``UniqueConstraint`` on ``amount``; the mutation answers it as the field's ``invalid``
    error on PostgreSQL first.
    """

    amount = serializers.DecimalField(max_digits=None, decimal_places=None)
