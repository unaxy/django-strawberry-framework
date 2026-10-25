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
from strawberry.types.base import StrawberryOptional, get_object_definition
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
from django_strawberry_framework.forms.inputs import build_form_input_class
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


def test_null_boolean_validating_subclass_generates_required_input() -> None:
    """A validating subclass must not generate nullable-required SDL.

    The converter preserves the subclass's real requiredness and emits a
    non-null ``bool`` annotation. The generated input therefore rejects omission
    during GraphQL coercion instead of exposing ``Boolean`` while its dataclass
    constructor still requires ``flag``.
    """

    class RequiredNullableBoolean(forms.NullBooleanField):
        validate = forms.Field.validate

    class ProbeForm(forms.Form):
        flag = RequiredNullableBoolean(required=True)

    assert convert_form_field(ProbeForm.base_fields["flag"]).annotation is bool

    input_cls, _ = build_form_input_class(ProbeForm, operation_kind="form")
    field = get_object_definition(input_cls, strict=True).fields[0]
    assert not isinstance(field.type, StrawberryOptional)

    def resolve_probe(inp: object) -> int:
        del inp
        return 1

    resolve_probe.__annotations__ = {"inp": input_cls, "return": int}

    @strawberry.type
    class Query:
        # basedpyright: Strawberry types the field from the resolver's run-time __annotations__
        # set above; a class annotation would be a second, static declaration of that type
        probe = strawberry.field(resolver=resolve_probe)  # pyright: ignore[reportGeneralTypeIssues]

    schema = strawberry.Schema(query=Query)
    assert "flag: Boolean!" in schema.as_str()

    omitted = schema.execute_sync("{ probe(inp: {}) }")
    assert omitted.errors is not None
    assert "flag" in omitted.errors[0].message
    assert schema.execute_sync("{ probe(inp: {flag: true}) }").errors is None


def test_json_field_maps_to_json_scalar_not_charfield_str() -> None:
    """``JSONField`` subclasses ``CharField`` but must resolve to ``JSON``, not ``str``.

    Without an explicit registry row the MRO walk would hit ``CharField`` ->
    ``str`` and the generated input would reject object / array literals that
    Django's form field (and the serializer / model scalar tables) accept.
    """
    conversion = convert_form_field(forms.JSONField())
    assert conversion.annotation is strawberry.scalars.JSON
    assert conversion.kind == SCALAR


def test_required_ness_reflects_field_required() -> None:
    """``required`` mirrors ``field.required`` for both states (non-NullBoolean)."""
    assert convert_form_field(forms.CharField(required=True)).required is True
    assert convert_form_field(forms.CharField(required=False)).required is False


def test_email_field_maps_via_mro_under_charfield() -> None:
    """A known subclass (``EmailField``) resolves to its ``CharField`` parent's scalar."""
    # EmailField is not its own entry in the scalar table; the MRO walk reaches
    # CharField -> str. This is the parity behavior the spec mandates.
    assert convert_form_field(forms.EmailField()).annotation is str


def test_float_and_decimal_do_not_collapse_to_integer_parent() -> None:
    """``FloatField`` / ``DecimalField`` subclass ``IntegerField`` but keep their own scalar.

    A naive "first ``isinstance`` wins" walk over an ``IntegerField``-first
    registry would mis-map both to ``int``; the ``type(field).__mro__`` walk
    visits the field's own class first so each resolves correctly.
    """
    assert convert_form_field(forms.FloatField()).annotation is float
    assert convert_form_field(forms.DecimalField()).annotation is decimal.Decimal
    # UUIDField subclasses CharField - same hazard, same guard.
    assert convert_form_field(forms.UUIDField()).annotation is uuid.UUID


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


def test_file_and_image_fields_are_file_kind() -> None:
    """``FileField`` / ``ImageField`` -> kind ``file`` (the ``Upload`` annotation is build-site)."""
    assert convert_form_field(forms.FileField()).kind == FILE
    assert convert_form_field(forms.ImageField()).kind == FILE


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


def test_bare_field_maps_to_str_as_exact_type_special_case() -> None:
    """A bare ``forms.Field`` is an exact-type special case -> ``str`` (not a catch-all)."""
    conversion = convert_form_field(forms.Field())
    assert conversion.annotation is str
    assert conversion.kind == SCALAR


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


def test_form_field_required_column_backed_variations() -> None:
    """``form_field_required`` accounts for backing column nullability on exact NullBooleanField."""

    class MockColumn:
        def __init__(self, *, null: bool) -> None:
            self.null = null

    class MockColumnNoNull:
        pass

    nb_req = forms.NullBooleanField(required=True)
    nb_opt = forms.NullBooleanField(required=False)

    # Exact NullBooleanField is forced optional when column is None or column.null is True
    assert form_field_required(nb_req, column=None) is False
    assert form_field_required(nb_opt, column=None) is False
    assert form_field_required(nb_req, column=MockColumn(null=True)) is False
    assert form_field_required(nb_req, column=MockColumnNoNull()) is False

    # Backed by non-null column, exact NullBooleanField preserves field.required
    assert form_field_required(nb_req, column=MockColumn(null=False)) is True
    assert form_field_required(nb_opt, column=MockColumn(null=False)) is False

    # Non-NullBooleanField always returns field.required regardless of column
    char_req = forms.CharField(required=True)
    char_opt = forms.CharField(required=False)
    assert form_field_required(char_req, column=None) is True
    assert form_field_required(char_req, column=MockColumn(null=True)) is True
    assert form_field_required(char_opt, column=None) is False
    assert form_field_required(char_opt, column=MockColumn(null=False)) is False


def test_custom_subclasses_of_precheck_kinds() -> None:
    """Custom subclasses of relation, file, and multi-choice fields resolve to expected kinds."""

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

    assert convert_form_field(CustomModelChoiceField(queryset=None)).kind == RELATION_SINGLE
    assert convert_form_field(CustomModelMultipleChoiceField(queryset=None)).kind == RELATION_MULTI
    assert convert_form_field(CustomFileField()).kind == FILE
    assert convert_form_field(CustomImageField()).kind == FILE
    conv_multi = convert_form_field(CustomMultipleChoiceField())
    assert conv_multi.kind == SCALAR
    assert conv_multi.annotation == list[str]


def test_unsupported_django_form_fields_raise() -> None:
    """Form fields without scalar mapping or supported ancestor raise ConfigurationError."""
    unsupported_fields = [
        forms.DurationField(),
        forms.MultiValueField(fields=[forms.CharField()]),
        forms.SplitDateTimeField(),
        forms.ComboField(fields=[forms.CharField()]),
    ]
    for field in unsupported_fields:
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
