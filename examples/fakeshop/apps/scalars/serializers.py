"""DRF serializers for the scalars app's live serializer-mutation surface.

A plain DRF ``ModelSerializer`` declared the standard DRF way (over the shared
``examples/fakeshop/drf_serializers.py::ModelSerializerBase``; no package imports);
``apps/scalars/schema.py`` wraps it in the shipped ``SerializerMutation`` base, the
serializer half of the temporal write surface over ``ScalarSpecimen``.
"""

from drf_serializers import ModelSerializerBase
from rest_framework import serializers

from .models import ScalarSpecimen


class ScalarSpecimenTemporalSerializer(ModelSerializerBase[ScalarSpecimen]):
    """``ModelSerializer`` over ``ScalarSpecimen``'s required columns, temporal ones included.

    DRF's ``DateTimeField`` refuses an aware value it cannot project onto the current time
    zone with its own ``overflow`` error; its ``TimeField`` passes an aware time through,
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
