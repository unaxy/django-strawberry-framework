"""Converter tests for the form-field -> Strawberry annotation registry.

Covers ``django_strawberry_framework/forms/converter.py``:

- ``convert_form_field`` scalar mappings + required-ness for every supported
  ``forms.Field`` class (text-like -> ``str``, the numeric / temporal / uuid /
  multi-choice cases, ``NullBooleanField`` -> ``bool | None``);
- the fail-loud dispatch: a bare ``forms.Field`` -> ``str``, a known subclass
  (``EmailField``) mapping via the MRO walk, and a custom ``forms.Field``
  subclass with no supported ancestor raising ``ConfigurationError`` (the
  load-bearing no-catch-all assertion);
- the relation / file kind flags (``ModelChoiceField`` / ``ModelMultipleChoiceField``
  / ``FileField`` / ``ImageField``) the input builder finalizes;
- ``form_field_reads_list``: the list-reading form fields (subclasses included), the
  PostgreSQL array form fields on the Postgres tier, and those arms off when
  ``django.contrib.postgres.forms`` cannot import; ``form_field_reads_one_value``: the
  registered scalar form fields, never a list field, a bare ``forms.Field`` or a consumer
  field no registered class covers.

The relation id-type (Relay-``GlobalID`` vs raw pk, single + multi) is pinned at
the input-build site (the converter returns only the ``kind`` for relations), so
that assertion lives in ``test_inputs.py`` where the id type is finalized.

The validating nullable-boolean subclass's input coercion is live in
``examples/fakeshop/test_query/test_input_shapes_api.py``.
Shipped ``FileField`` / ``ImageField`` -> ``Upload`` writes live in
``test_uploads_api.py`` / ``test_products_api.py``; this file keeps converter
dispatch, required-ness, and fail-loud unknown subclasses.
"""

from __future__ import annotations

import datetime
import decimal
import tempfile
import uuid

import pytest
import strawberry
from django import forms
from django.db import models
from typing_extensions import override

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    _postgres_form_field_class,
    convert_form_field,
    form_field_kind,
    form_field_reads_list,
    form_field_reads_one_value,
    form_field_required,
)
from django_strawberry_framework.utils._narrowing import list_of
from tests._soft_dependency import blocked_modules


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (forms.CharField(), str),
        (forms.EmailField(), str),
        (forms.SlugField(), str),
        # ``assume_scheme="https"`` is required across Django 5.2-6.0: 5.x emits a
        # RemovedInDjango60Warning without it (the http->https default flip), which the
        # suite's -W error turns into a collection error; 6.0 accepts the argument and
        # already defaults to https. Passing it explicitly is version-agnostic and the
        # converter maps URLField -> str regardless of scheme.
        (forms.URLField(assume_scheme="https"), str),
        (forms.RegexField(regex=r".*"), str),
        (forms.ChoiceField(), str),
        (forms.TypedChoiceField(), str),
        (forms.FilePathField(path=tempfile.gettempdir()), str),
        (forms.GenericIPAddressField(), str),
        (forms.Field(), str),
        (forms.IntegerField(), int),
        (forms.FloatField(), float),
        (forms.DecimalField(), decimal.Decimal),
        (forms.BooleanField(), bool),
        (forms.UUIDField(), uuid.UUID),
        (forms.DateField(), datetime.date),
        (forms.DateTimeField(), datetime.datetime),
        (forms.TimeField(), datetime.time),
        (forms.MultipleChoiceField(), list[str]),
        (forms.TypedMultipleChoiceField(), list[str]),
    ],
)
def test_scalar_field_annotations(field: forms.Field, expected: object) -> None:
    """Each supported scalar form field maps to its Strawberry annotation, kind ``scalar``."""
    conversion = convert_form_field(field)
    assert conversion.annotation == expected
    assert conversion.kind == SCALAR


def test_null_boolean_field_is_optional_bool() -> None:
    """``NullBooleanField`` -> ``bool | None``, always optional (graphene parity).

    Django's ``NullBooleanField.validate`` is a no-op, so ``field.required`` is
    meaningless for form validation. GraphQL also cannot express a required
    nullable input; baking ``bool | None`` with ``required=True`` (Django's
    default) produced SDL ``Boolean`` without a default, so clients could omit
    the field per the schema and then hit a Strawberry ``TypeError``. Force
    ``required=False`` regardless of ``field.required``.
    """
    conversion = convert_form_field(forms.NullBooleanField())
    assert conversion.annotation == (bool | None)
    assert conversion.kind == SCALAR
    assert conversion.required is False
    assert convert_form_field(forms.NullBooleanField(required=True)).required is False
    assert convert_form_field(forms.NullBooleanField(required=False)).required is False


def test_null_boolean_subclass_with_real_validation_stays_required() -> None:
    """A custom subclass is not assumed to retain NullBooleanField's no-op validation."""

    class RequiredNullableBoolean(forms.NullBooleanField):
        validate = forms.Field.validate

    class ProbeForm(forms.Form):
        flag = RequiredNullableBoolean(required=True)

    field = ProbeForm.base_fields["flag"]
    assert convert_form_field(field).required is True
    assert ProbeForm(data={}).is_valid() is False
    assert ProbeForm(data={}).errors["flag"] == ["This field is required."]


def test_json_field_maps_to_json_scalar_not_charfield_str() -> None:
    """``JSONField`` subclasses ``CharField`` but must resolve to ``JSON``, not ``str``.

    Without an explicit registry row the MRO walk would hit ``CharField`` ->
    ``str`` and the generated input would reject object / array literals that
    Django's form field (and the serializer / model scalar tables) accept.
    """
    conversion = convert_form_field(forms.JSONField())
    assert conversion.annotation is strawberry.scalars.JSON
    assert conversion.kind == SCALAR


@pytest.mark.parametrize("required", [True, False], ids=["required", "optional"])
def test_required_ness_reflects_field_required(*, required: bool) -> None:
    """A non-NullBoolean conversion preserves its field's requiredness."""
    assert convert_form_field(forms.CharField(required=required)).required is required


# ---------------------------------------------------------------------------
# Relation / file kind flags (annotation finalized at the input-build site)
# ---------------------------------------------------------------------------


def test_model_choice_field_is_relation_single() -> None:
    """``ModelChoiceField`` -> kind ``relation_single`` (annotation finalized at build site).

    The converter only reads ``field.required`` and returns the relation ``kind``
    (the id annotation is finalized at the input-build site over a real model's
    primary ``DjangoType``), so a ``queryset=None`` field suffices here; the
    Relay-vs-raw-pk id-type assertions live in ``test_inputs.py``.
    """
    field: forms.ModelChoiceField[models.Model] = forms.ModelChoiceField(queryset=None)
    conversion = convert_form_field(field)
    assert conversion.kind == RELATION_SINGLE
    assert conversion.annotation is None


def test_model_multiple_choice_field_is_relation_multi() -> None:
    """``ModelMultipleChoiceField`` -> kind ``relation_multi`` (precedes the single check)."""
    field: forms.ModelMultipleChoiceField[models.Model] = forms.ModelMultipleChoiceField(
        queryset=None,
    )
    conversion = convert_form_field(field)
    assert conversion.kind == RELATION_MULTI
    assert conversion.annotation is None


@pytest.mark.parametrize("field_class", [forms.FileField, forms.ImageField], ids=["file", "image"])
def test_file_and_image_fields_are_file_kind(field_class: type[forms.FileField]) -> None:
    """Each upload form-field flavor has file kind before input-build annotation."""
    assert convert_form_field(field_class()).kind == FILE


class _UnsupportedField(forms.Field):
    """A custom field with no supported ancestor: ``convert_form_field`` refuses it."""


class _CustomModelChoiceField(forms.ModelChoiceField[models.Model]):
    pass


class _FileWidgetField(forms.Field):
    """A custom field with no ``FileField`` ancestor, rendered as an upload."""

    widget = forms.ClearableFileInput


class _MultipartTextarea(forms.Textarea):
    """A text widget that asks for a multipart form yet reads ``data``, as every ``Textarea``."""

    needs_multipart_form = True


_MODEL_CHOICE: forms.ModelChoiceField[models.Model] = forms.ModelChoiceField(queryset=None)
_MODEL_MULTIPLE_CHOICE: forms.ModelMultipleChoiceField[models.Model] = (
    forms.ModelMultipleChoiceField(queryset=None)
)


@pytest.mark.parametrize(
    ("field", "kind"),
    [
        pytest.param(_MODEL_MULTIPLE_CHOICE, RELATION_MULTI, id="mmcf"),
        pytest.param(_MODEL_CHOICE, RELATION_SINGLE, id="mcf"),
        pytest.param(_CustomModelChoiceField(queryset=None), RELATION_SINGLE, id="mcf-subclass"),
        pytest.param(forms.FileField(), FILE, id="file"),
        pytest.param(forms.ImageField(), FILE, id="image"),
        pytest.param(forms.MultipleChoiceField(), SCALAR, id="multiple-choice"),
        pytest.param(forms.ChoiceField(), SCALAR, id="choice"),
        pytest.param(forms.Field(), SCALAR, id="bare-field"),
        pytest.param(_UnsupportedField(), SCALAR, id="unsupported-custom"),
        pytest.param(forms.SplitDateTimeField(), SCALAR, id="unsupported-builtin"),
        pytest.param(_FileWidgetField(), FILE, id="custom-field-file-widget"),
        pytest.param(forms.CharField(widget=forms.FileInput), FILE, id="char-file-widget"),
        pytest.param(forms.FileField(widget=forms.TextInput), FILE, id="file-text-widget"),
        pytest.param(
            forms.CharField(widget=_MultipartTextarea),
            SCALAR,
            id="multipart-textarea",
        ),
    ],
)
def test_form_field_kind_reads_the_class_and_widget(field: forms.Field, kind: str) -> None:
    """``form_field_kind`` reads the class and the widget's real type, a refused field included.

    A widget asking for a multipart form is no file widget unless it is a ``FileInput``.
    """
    assert form_field_kind(field) == kind


# ---------------------------------------------------------------------------
# Fail-loud dispatch - no base-Field catch-all
# ---------------------------------------------------------------------------


def test_unknown_custom_field_subclass_raises() -> None:
    """A custom ``forms.Field`` subclass with no supported ancestor raises ``ConfigurationError``.

    This is the catch-all-shadowing regression: if a base-``forms.Field`` -> ``str``
    entry were registered, this custom field would silently become ``String``
    instead of failing loud. The raise proves no such catch-all exists.
    """

    class CustomField(forms.Field):
        pass

    field = CustomField()
    with pytest.raises(ConfigurationError) as excinfo:
        convert_form_field(field)
    assert str(excinfo.value) == (
        f"Unsupported form field type 'CustomField' on form field {field!r}. "
        "convert_form_field has no mapping for it and no supported ancestor; subclass a "
        "supported form field, or drop it via Meta.fields / Meta.exclude."
    )


@pytest.mark.parametrize(
    (
        "kind",
        "required",
        "column_kind",
        "expected",
    ),
    [
        pytest.param("nullable-boolean", True, "absent", False, id="nullboolean-no-column"),
        pytest.param("nullable-boolean", False, "absent", False, id="optional-no-column"),
        pytest.param("nullable-boolean", True, "nullable", False, id="nullable-column"),
        pytest.param("nullable-boolean", True, "malformed", False, id="column-without-null"),
        pytest.param("nullable-boolean", True, "required", True, id="required-column"),
        pytest.param("nullable-boolean", False, "required", False, id="optional-required-column"),
        pytest.param("text", True, "absent", True, id="text-required-no-column"),
        pytest.param("text", True, "nullable", True, id="text-required-nullable-column"),
        pytest.param("text", False, "absent", False, id="text-optional-no-column"),
        pytest.param("text", False, "required", False, id="text-optional-required-column"),
    ],
)
def test_form_field_required_column_backed_variations(
    kind: str,
    column_kind: str,
    *,
    required: bool,
    expected: bool,
) -> None:
    """Exact NullBooleanField honors real column nullability; other fields retain requiredness."""
    field = (
        forms.NullBooleanField(required=required)
        if kind == "nullable-boolean"
        else forms.CharField(required=required)
    )
    columns: dict[str, object] = {
        "absent": None,
        "nullable": models.BooleanField(null=True),
        "required": models.BooleanField(null=False),
        # The helper also accepts a column-like object lacking null; no model can carry it.
        "malformed": object(),
    }
    assert form_field_required(field, column=columns[column_kind]) is expected


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        pytest.param("single", RELATION_SINGLE, id="model-choice"),
        pytest.param("multi", RELATION_MULTI, id="model-multiple-choice"),
        pytest.param("file", FILE, id="file"),
        pytest.param("image", FILE, id="image"),
        pytest.param("scalar-list", SCALAR, id="multiple-choice"),
    ],
)
def test_custom_subclasses_of_precheck_kinds(kind: str, expected: str) -> None:
    """A supported field subclass keeps the converter's precheck kind."""

    class CustomModelChoiceField(forms.ModelChoiceField[models.Model]):
        pass

    class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField[models.Model]):
        pass

    class CustomFileField(forms.FileField):
        pass

    class CustomImageField(forms.ImageField):
        pass

    class CustomMultipleChoiceField(forms.MultipleChoiceField):
        pass

    fields = {
        "single": CustomModelChoiceField(queryset=None),
        "multi": CustomModelMultipleChoiceField(queryset=None),
        "file": CustomFileField(),
        "image": CustomImageField(),
        "scalar-list": CustomMultipleChoiceField(),
    }
    conversion = convert_form_field(fields[kind])
    assert conversion.kind == expected
    if kind == "scalar-list":
        assert conversion.annotation == list[str]


@pytest.mark.parametrize(
    "field",
    [
        forms.DurationField(),
        forms.MultiValueField(fields=[forms.CharField()]),
        forms.SplitDateTimeField(),
        forms.ComboField(fields=[forms.CharField()]),
    ],
    ids=[
        "duration",
        "multi-value",
        "split-datetime",
        "combo",
    ],
)
def test_unsupported_django_form_fields_raise(field: forms.Field) -> None:
    """Form fields without scalar mapping or supported ancestor raise ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Unsupported form field type"):
        convert_form_field(field)


class _PickedTags(forms.MultipleChoiceField):
    """A consumer ``MultipleChoiceField`` subclass."""


@pytest.mark.parametrize(
    ("field", "reads_list"),
    [
        pytest.param(forms.MultipleChoiceField(), True, id="multiple-choice"),
        pytest.param(forms.TypedMultipleChoiceField(), True, id="typed-multiple-choice"),
        pytest.param(_PickedTags(), True, id="multiple-choice-subclass"),
        pytest.param(forms.JSONField(), True, id="json"),
        pytest.param(forms.ChoiceField(), False, id="choice"),
        pytest.param(forms.TypedChoiceField(coerce=int), False, id="typed-choice"),
        pytest.param(forms.CharField(), False, id="char"),
        pytest.param(forms.IntegerField(), False, id="integer"),
    ],
)
def test_form_field_reads_list(field: forms.Field, *, reads_list: bool) -> None:
    """A multiple-choice or JSON form field reads a list; a single-value field does not."""
    assert form_field_reads_list(field) is reads_list


class _ListReadingField(forms.Field):
    """A consumer field no registered scalar class covers, reading a list."""

    @override
    def to_python(self, value: object) -> object:
        return list_of(value)


@pytest.mark.parametrize(
    ("field", "reads_one_value"),
    [
        pytest.param(forms.ChoiceField(), True, id="choice"),
        pytest.param(forms.TypedChoiceField(coerce=int), True, id="typed-choice"),
        pytest.param(forms.CharField(), True, id="char"),
        pytest.param(forms.EmailField(), True, id="char-subclass"),
        pytest.param(forms.IntegerField(), True, id="integer"),
        pytest.param(forms.DecimalField(), True, id="decimal"),
        pytest.param(forms.MultipleChoiceField(), False, id="multiple-choice"),
        pytest.param(forms.JSONField(), False, id="json"),
        pytest.param(forms.Field(), False, id="bare-field"),
        pytest.param(_ListReadingField(), False, id="custom-field"),
    ],
)
def test_form_field_reads_one_value(field: forms.Field, *, reads_one_value: bool) -> None:
    """A registered scalar form field reads one value; a list field, a bare or custom one not."""
    assert form_field_reads_one_value(field) is reads_one_value


def test_postgres_form_field_class_is_none_without_its_module() -> None:
    """An unimportable ``django.contrib.postgres.forms`` leaves its array form fields off."""
    with blocked_modules("django.contrib.postgres.forms"):
        assert _postgres_form_field_class("SimpleArrayField") is None


@pytest.mark.pg
def test_postgres_array_form_fields_read_a_list() -> None:
    """``SimpleArrayField``, ``SplitArrayField`` and a subclass read a list.

    ``convert_form_field`` still types the ``SimpleArrayField`` as the ``CharField`` it
    subclasses: the list-reading fact is ``form_field_reads_list``'s, not its annotation.
    """
    from django.contrib.postgres.forms import (  # noqa: PLC0415 - needs the Postgres driver
        SimpleArrayField,
        SplitArrayField,
    )

    class TagList(SimpleArrayField):
        pass

    simple = SimpleArrayField(forms.CharField())
    assert form_field_reads_list(simple)
    assert form_field_reads_list(SplitArrayField(forms.CharField(), size=2))
    assert form_field_reads_list(TagList(forms.CharField()))
    assert convert_form_field(simple).annotation is str
