"""Consumer Django forms for the scalars app's live form-mutation surface.

Wraps ``MediaSpecimen`` (the spec-037 ``FileField`` / ``ImageField`` model) in a
``DjangoModelFormMutation`` so the spec-038 FORM path's ``ImageField -> Upload`` mapping
is earned over a LIVE multipart ``/graphql/`` request - the form-mutation twin of the
spec-037 model-path ``createMediaSpecimen`` upload. ``MediaSpecimen`` already carries an
``ImageField`` (so no model change / migration is needed) and a ``MediaSpecimenType`` for
the payload's ``node`` slot.

``ScalarSpecimenTemporalForm`` is the ``ModelForm`` half of the temporal write surface:
the ``occurred_at`` / ``occurred_time`` columns written through Django's own
``DateTimeField`` / ``TimeField`` form fields, so a value those fields clean but the
database cannot store is refused over a live request.
"""

from __future__ import annotations

from django import forms

from apps.scalars import models


class MediaSpecimenImageForm(forms.ModelForm[models.MediaSpecimen]):
    """A ``MediaSpecimen`` ``ModelForm`` carrying the ``image`` ``ImageField``.

    For the spec's named ``ImageField -> Upload`` case over the FORM path: the converter
    maps ``image`` to the ``Upload`` scalar, the resolver routes the upload into the bound
    form's ``files=``, and the bound ``ImageField`` validates it as a real image (Pillow),
    so the live test asserts the stored image AND its dimensions (the products
    ``FileField`` form test skips dimensions). ``attachment`` is intentionally NOT a form
    field, so it is excluded from ``full_clean`` and a single-image create is reachable.
    """

    class Meta:
        model = models.MediaSpecimen
        fields = ("label", "image")


class ScalarSpecimenTemporalForm(forms.ModelForm[models.ScalarSpecimen]):
    """A ``ScalarSpecimen`` ``ModelForm`` over the required columns, temporal ones included.

    Django's form fields parse a datetime or time and range-check nothing past what Python
    holds, so an aware ``occurred_at`` whose UTC projection leaves years 1..9999, or an
    aware ``occurred_time`` on SQLite, is a valid form the database cannot store; the
    mutation answers it as the field's ``invalid`` error before the save.
    """

    class Meta:
        model = models.ScalarSpecimen
        fields = (
            "label",
            "occurred_on",
            "occurred_at",
            "occurred_time",
            "external_id",
        )
