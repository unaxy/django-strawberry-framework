"""Form-field -> Strawberry annotation conversion + the decode kinds the form resolver reads.

This module is the machinery for the **model-less case**
(spec-038 Decision 7): a plain ``forms.Form`` field (a ``captcha``, a
``confirm_email``) has no Django model column and so no read-side equivalent in
``types/converters.py``. ``convert_form_field`` is the ``forms.Field``-keyed
registry that maps such a field to its Strawberry annotation + required-ness, in
the graphene-django ``convert_form_field`` parity shape, raised through the
package's own ``ConfigurationError``.

It is NOT a parallel copy of the read-side scalar table. A ``ModelForm`` field
that HAS a backing model column routes through the read-side
``convert_scalar`` / ``convert_choices_to_enum`` / ``relation_input_annotation``
at the ``forms/inputs.py`` build site (keyed on the resolved ``models.Field``),
so a ``choices`` form field resolves to the SAME generated enum the read
``DjangoType`` synthesizes (the symmetric wire contract), unless its static choices
admit fewer of the column's values, when it publishes the generated enum of the
admitted values (``forms/inputs.py::_form_choice_narrowing``). The bound form still
reads such a field by its class and widget, so its kind (``form_field_kind``) must agree with
the column's (``forms/inputs.py::require_column_kind_agreement``). The two key spaces -
``forms.Field`` here, ``models.Field`` on the read side - stay strictly separate.

**Fail-loud dispatch.** The registry registers each supported class
*individually* (so subclasses map via the MRO walk - ``EmailField`` /
``SlugField`` / ``URLField`` / ``RegexField`` under ``CharField``), handles a
bare ``forms.Field`` as an explicit exact-type special case -> ``str``, and the
fallthrough (unregistered) default **raises** ``ConfigurationError`` naming the
field and class. Crucially there is **no base-``forms.Field`` catch-all
registration**: registering ``forms.Field`` -> ``str`` would shadow the raise so
every custom ``forms.Field`` subclass silently became ``String`` (the
graphene-django ``ImproperlyConfigured`` parity, lost). A custom
``class CustomField(forms.Field)`` with no supported ancestor therefore hits the
raising default.

**The reverse map.** The generated input GraphQL names follow the
cross-flavor ``036`` convention (a ``ModelChoiceField`` named ``category`` emits
``categoryId`` / python attr ``category_id``), but a bound Django form is keyed
by FORM-field name (``ItemModelForm(data={"category": pk})``, never
``{"category_id": pk}``). So ``forms/inputs.py`` retains, per generated input
field, a ``utils/inputs.py::InputFieldSpec`` (``target_name`` = form field name)
that ``forms/resolvers.py`` consults at decode to produce a
form-field-keyed payload, where ``kind`` is one of the four module constants
below. This module owns only the kind constants + ``convert_form_field``; the
reverse-map record type is single-sited on ``InputFieldSpec``.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from collections.abc import Callable

import strawberry
from django import forms

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils.converters import (
    MRO_CONTINUE,
    MroContinue,
    convert_with_mro,
    finish_field_conversion,
    make_kind_converter,
    make_scalar_converter,
)
from django_strawberry_framework.utils.imports import import_attr_if_importable

# The four decode kinds the reverse-map record carries. Single-sourced in
# ``utils/inputs.py`` (one conceptual enum, not a per-flavor
# copy); re-exported here (the ``as`` form marks the explicit re-export) so the
# form resolver, the input builder, and the tests keep addressing them on
# this module (spec-038 Decision 7).
from django_strawberry_framework.utils.inputs import FILE as FILE  # noqa: PLC0414 - explicit re-export
from django_strawberry_framework.utils.inputs import RELATION_MULTI as RELATION_MULTI  # noqa: PLC0414 - explicit re-export
from django_strawberry_framework.utils.inputs import RELATION_SINGLE as RELATION_SINGLE  # noqa: PLC0414 - explicit re-export
from django_strawberry_framework.utils.inputs import SCALAR as SCALAR  # noqa: PLC0414 - explicit re-export
from django_strawberry_framework.utils.inputs import FieldConversionBase


class FormFieldConversion(FieldConversionBase):
    """The model-less annotation + decode kind ``convert_form_field`` returns.

    ``required`` is the form field's own ``field.required``, except the exact
    built-in ``NullBooleanField`` which is always optional (Django's
    ``validate`` is a no-op and GraphQL cannot express required-nullable inputs -
    graphene-django parity). A validating ``NullBooleanField`` subclass keeps
    its declared requiredness and therefore resolves to a non-null ``bool``
    annotation, so GraphQL cannot permit omission while the generated dataclass
    still requires the value. ``annotation`` is the resolved Strawberry
    annotation for a SCALAR field; for a relation / file field the annotation is
    finalized at the ``forms/inputs.py`` build site (where the backing model
    column - if any - and the related primary ``DjangoType`` are known, so the
    Relay-``GlobalID``-vs-raw-pk id type can be resolved), so those kinds carry
    ``annotation=None`` here and
    only the ``kind`` is authoritative. The ``(annotation, kind, required)``
    value-object shape is the shared ``utils/inputs.py::FieldConversionBase``.
    """

    __slots__: tuple[str, ...] = ()


# The value shape of every form converter table entry: a ``forms.Field`` in, its
# ``FormFieldConversion`` out.
FormFieldConverter = Callable[[forms.Field], FormFieldConversion]


def form_field_kind(field: forms.Field) -> str:
    """Return the decode kind a form field reads its value as, by its class and widget.

    A ``ModelMultipleChoiceField`` reads a list of rows (``relation_multi``, checked before
    the ``ModelChoiceField`` it subclasses), a ``ModelChoiceField`` one row
    (``relation_single``), a ``FileField`` / ``ImageField``, or any field whose widget is a
    ``forms.FileInput`` (``ClearableFileInput`` included: Django's widget whose
    ``value_from_datadict`` reads ``files``; a custom field rendered with it, a ``CharField``
    with ``FileInput``), an upload (``file``), and every other field a ``data`` value
    (``scalar``). The widget is read statically and checked by its real type, so no
    consumer code runs; ``needs_multipart_form`` is not read, since it only asks for a
    multipart form and a widget setting it may still read ``data``. A custom widget that
    reads ``files`` without subclassing ``forms.FileInput`` reads as ``scalar``: subclass
    ``forms.FileInput`` for it. A pure static read that never converts, so a field
    ``convert_form_field`` refuses still has a kind. It is the kind ``convert_form_field``
    gives a column-less field and the kind
    ``forms/inputs.py::require_column_kind_agreement`` compares with a backing column's.
    """
    if truth.is_instance(field, forms.ModelMultipleChoiceField):
        return RELATION_MULTI
    if truth.is_instance(field, forms.ModelChoiceField):
        return RELATION_SINGLE
    if truth.is_instance(field, forms.FileField) or truth.is_instance(
        truth.static_attr(field, "widget", None),
        forms.FileInput,
    ):
        return FILE
    return SCALAR


def form_field_required(field: forms.Field, *, column: object = None) -> bool:
    """Return the effective GraphQL-input requiredness of any form field (the one rule).

    An exact ``NullBooleanField`` has a no-op ``validate``, so its
    ``field.required`` is normally meaningless (omit / ``None`` both pass).
    Two shapes must retain declared requiredness, however:

    - a custom subclass may override validation and genuinely reject omission;
    - a ModelForm field backed by a non-null model column reaches model
      validation after the form field's no-op and rejects ``None``.

    GraphQL cannot express "required but nullable", but the non-null column
    shape has a non-null ``bool`` annotation already, so keeping
    ``required=True`` accurately rejects omission and null before execution.

    This is the SINGLE requiredness decision, shared by ``convert_form_field``
    (the annotation path) and ``forms/inputs.py``'s build site + create/partial
    required-field discovery, so the column-backed and column-less paths cannot
    drift. It is a pure attribute + ``isinstance`` read - it never converts - so
    required-field discovery over the full declared field set never raises on an
    excluded unsupported field.
    """
    if type(field) is not forms.NullBooleanField:
        return field.required
    if column is not None and not getattr(column, "null", True):
        return field.required
    return False


def _null_boolean_converter(field: forms.Field) -> FormFieldConversion:
    """Convert ``NullBooleanField`` with an annotation matching requiredness.

    The exact built-in field keeps ``bool | None`` + an optional input default
    because its ``validate`` is a no-op. A subclass that restores real required
    validation must instead produce ``bool`` + no default; otherwise the
    generated GraphQL field is nullable while Strawberry's input dataclass still
    requires the keyword, allowing omission to reach a constructor ``TypeError``.
    """
    required = form_field_required(field)
    annotation = bool if required else bool | None
    return FormFieldConversion(annotation=annotation, kind=SCALAR, required=required)


def _scalar_converter(annotation: object) -> FormFieldConverter:
    """Return a form scalar-table converter (``form_field_required`` for requiredness)."""
    return make_scalar_converter(
        FormFieldConversion,
        annotation,
        required_of=form_field_required,
    )


def _kind_converter(kind: str, annotation: object = None) -> FormFieldConverter:
    """Return a form kind-precheck converter (``form_field_required`` for requiredness)."""
    return make_kind_converter(
        FormFieldConversion,
        kind,
        annotation=annotation,
        required_of=form_field_required,
    )


# Each supported ``forms.Field`` class -> a ``make_scalar_converter`` callable.
# Registered individually (not via a base-``Field`` catch-all) so subclasses map
# through the MRO walk in ``convert_form_field`` - ``EmailField`` / ``SlugField``
# / ``URLField`` / ``RegexField`` resolve under ``CharField``, the parity
# behavior. ``ChoiceField`` -> ``str`` is the model-less default; a ``ChoiceField``
# over a ModelForm model's ``choices`` is routed through the read-side enum (or the
# enum of the column values it admits) at the build site instead.
# ``ModelChoiceField`` / ``ModelMultipleChoiceField`` /
# ``MultipleChoiceField`` / ``FileField`` / ``ImageField`` are deliberately NOT in
# this scalar table - they resolve by ``kind`` in ``convert_form_field`` before the
# walk reaches it.
#
# Resolution is a ``type(field).__mro__`` walk against this dict (the same idiom
# ``types/converters.py::scalar_for_field`` uses on the read side), so the
# MOST-specific registered class wins regardless of dict insertion order:
# ``FloatField`` / ``DecimalField`` both subclass ``IntegerField`` and
# ``UUIDField`` / ``JSONField`` subclass ``CharField``, so a linear "first
# ``isinstance`` wins" walk would mis-map them to the parent's scalar. The MRO
# walk visits the field's own class first, so each resolves to its own entry.
# ``JSONField`` must stay an explicit row (``strawberry.scalars.JSON``) - without
# it the CharField parent would silently type JSON payloads as ``String``,
# rejecting object / array literals that Django's form field (and the serializer
# / model scalar tables) accept as structured JSON.
_SCALAR_FORM_FIELDS: dict[type[forms.Field], FormFieldConverter] = {
    forms.CharField: _scalar_converter(str),
    forms.ChoiceField: _scalar_converter(str),
    forms.IntegerField: _scalar_converter(int),
    forms.FloatField: _scalar_converter(float),
    forms.DecimalField: _scalar_converter(decimal.Decimal),
    forms.NullBooleanField: _null_boolean_converter,
    forms.BooleanField: _scalar_converter(bool),
    forms.UUIDField: _scalar_converter(uuid.UUID),
    forms.JSONField: _scalar_converter(strawberry.scalars.JSON),
    forms.DateTimeField: _scalar_converter(datetime.datetime),
    forms.DateField: _scalar_converter(datetime.date),
    forms.TimeField: _scalar_converter(datetime.time),
}


def _bare_form_field(field: forms.Field) -> FormFieldConversion | MroContinue:
    """Exact-type ``forms.Field`` -> ``str``; any subclass continues the MRO walk.

    NOT a catch-all: an ``isinstance`` match that always returned a conversion
    would shadow the raising fallthrough. Returning ``MRO_CONTINUE`` lets
    ``convert_with_mro`` continue (``None`` is a successful conversion
    elsewhere). Ordered LAST in the precheck list so a supported subclass has
    already been offered to the scalar registry.
    """
    if type(field) is forms.Field:
        return FormFieldConversion(
            annotation=str,
            kind=SCALAR,
            required=form_field_required(field),
        )
    return MRO_CONTINUE


# The relation / file kinds ``form_field_kind`` answers, each converted before the scalar
# walk could reach a parent class (``ModelChoiceField`` subclasses ``ChoiceField`` -> ``str``).
# Relation / file annotations are finalized at the build site (``annotation=None``).
_CONVERT_RELATION_MULTI = _kind_converter(RELATION_MULTI)
_CONVERT_RELATION_SINGLE = _kind_converter(RELATION_SINGLE)
_CONVERT_FILE = _kind_converter(FILE)
_CONVERT_KIND: dict[str, FormFieldConverter] = {
    RELATION_MULTI: _CONVERT_RELATION_MULTI,
    RELATION_SINGLE: _CONVERT_RELATION_SINGLE,
    FILE: _CONVERT_FILE,
}
# ``MultipleChoiceField`` subclasses ``ChoiceField``, so its ``list[str]`` must win before
# the scalar walk reaches ``ChoiceField`` -> ``str``.
_CONVERT_MULTIPLE_CHOICE = _kind_converter(SCALAR, list[str])


def convert_form_field(field: forms.Field) -> FormFieldConversion:
    """Map a model-less ``forms.Field`` to its Strawberry annotation + decode kind.

    Returns a ``FormFieldConversion`` carrying the resolved scalar
    ``annotation`` (``None`` for the relation / file kinds, finalized at the
    build site), the decode ``kind``, and ``required`` from
    ``form_field_required`` (forced ``False`` for ``NullBooleanField`` - see
    ``FormFieldConversion``).

    Dispatch rides the shared ``utils/converters.py::convert_with_mro``
    skeleton (ordered prechecks, then the scalar registry MRO walk, then a
    raising fallthrough) with ``finish_field_conversion`` invoking a
    ``make_scalar_converter`` registry hit. It is NOT a
    ``functools.singledispatch`` with a ``forms.Field`` -> ``str`` catch-all
    (which would shadow the raise so every custom field silently became
    ``String`` - spec-038 Decision 7):

    - a relation / file field (``form_field_kind``) returns its kind first, its
      annotation finalized at the build site (``ModelChoiceField`` subclasses
      ``ChoiceField``, so it MUST win before the scalar walk reaches ``ChoiceField``
      -> ``str``; ``FileField`` / ``ImageField`` likewise, and a field rendered with a
      ``forms.FileInput`` is an ``Upload``: its form reads it from ``files``, which a
      ``String`` input never reaches);
    - then ``MultipleChoiceField`` -> ``list[str]`` (it subclasses ``ChoiceField``
      and so must be checked before the scalar ``ChoiceField`` entry);
    - then the scalar registry MRO walk (``EmailField`` resolves under
      ``CharField``; ``FloatField`` / ``DecimalField`` resolve to their own
      entries, NOT the ``IntegerField`` they subclass, because the walk visits
      the field's own class first - the same reason ``UUIDField`` does not
      collapse to its ``CharField`` parent);
    - then the explicit exact-type special case ``type(field) is forms.Field``
      -> ``str`` (the listed "base ``Field`` -> ``str``", NOT a catch-all);
    - else the fallthrough **raises** ``ConfigurationError`` naming the field /
      class.

    The relation / multi checks run before the scalar walk because
    ``ModelChoiceField`` / ``ModelMultipleChoiceField`` / ``MultipleChoiceField``
    all subclass ``ChoiceField`` (which the scalar table maps to ``str``), so the
    more-specific kind must win.
    """
    kind = form_field_kind(field)
    if kind != SCALAR:
        return _CONVERT_KIND[kind](field)
    result = convert_with_mro(
        field,
        isinstance_prechecks=[
            (forms.MultipleChoiceField, _CONVERT_MULTIPLE_CHOICE),
            (forms.Field, _bare_form_field),
        ],
        scalar_registry=_SCALAR_FORM_FIELDS,
        fallthrough_error_factory=_unsupported_form_field,
    )
    return finish_field_conversion(result, field)


def _postgres_form_field_class(name: str) -> type[forms.Field] | None:
    """Return the ``django.contrib.postgres.forms`` field class ``name``, or ``None``.

    Soft-imported through the shared optional-import owner
    (``utils/imports.py::import_attr_if_importable``): the module imports a PostgreSQL
    driver, so it is unavailable (``None``) on an environment without one, where no
    consumer form can declare the class either.
    """
    cls = import_attr_if_importable("django.contrib.postgres.forms", name)
    return cls if truth.is_subclass(cls, forms.Field) else None


# The form field classes that read a list (``form_field_reads_list``), each matched with its
# subclasses; a PostgreSQL array form field is listed only where its module imports.
_LIST_READING_FORM_FIELDS: tuple[type[forms.Field], ...] = tuple(
    cls
    for cls in (
        forms.MultipleChoiceField,
        forms.JSONField,
        _postgres_form_field_class("SimpleArrayField"),
        _postgres_form_field_class("SplitArrayField"),
    )
    if cls is not None
)


def form_field_reads_list(field: forms.Field) -> bool:
    """Return whether ``field`` reads a list as its value, the single owner of that fact.

    ``form_field_reads_one_value`` reads it, which ``forms/inputs.py`` asks to tell a form
    field whose input shape disagrees with an ``ArrayField`` column (one reading a single
    value) from one that reads the column's list. A ``MultipleChoiceField``
    (``TypedMultipleChoiceField`` included) reads only a list; a ``JSONField`` reads any
    JSON value, a list among them; PostgreSQL's ``SimpleArrayField`` (the field
    ``ArrayField.formfield`` builds) and ``SplitArrayField`` read a list. Each is matched
    with its subclasses. It is a class list because Django states no class-agnostic "reads a
    list" fact: ``to_python`` is free to read anything, and ``convert_form_field``'s
    published annotation is not that fact either (it types a ``SimpleArrayField`` as the
    ``CharField`` it subclasses, and has no row for a ``SplitArrayField``).
    """
    return truth.is_one_of(field, _LIST_READING_FORM_FIELDS)


# The registered scalar form-field classes (``_SCALAR_FORM_FIELDS``), as one tuple for
# ``form_field_reads_one_value``'s subclass match.
_SCALAR_FORM_FIELD_CLASSES: tuple[type[forms.Field], ...] = tuple(_SCALAR_FORM_FIELDS)


def form_field_reads_one_value(field: forms.Field) -> bool:
    """Return whether ``field`` is a built-in form field reading a single value.

    One of the scalar form-field classes ``convert_form_field`` registers
    (``_SCALAR_FORM_FIELDS``: a ``CharField``, ``ChoiceField``, ``IntegerField``, ...),
    subclasses included, that does not read a list (``form_field_reads_list``: a
    ``SimpleArrayField`` subclasses ``CharField``, a ``JSONField`` reads any JSON value). A
    bare ``forms.Field`` and a consumer ``forms.Field`` subclass no registered class covers
    answer ``False``: their ``to_python`` may read anything, a list included, so nothing
    states they read one value.
    """
    return not form_field_reads_list(field) and truth.is_one_of(
        field,
        _SCALAR_FORM_FIELD_CLASSES,
    )


def _unsupported_form_field(field: forms.Field) -> ConfigurationError:
    """Build the fail-loud ``ConfigurationError`` for an unmapped ``forms.Field``.

    The fallthrough factory ``convert_with_mro`` raises when a field is matched by
    neither a precheck nor the scalar registry: an unregistered ``forms.Field``
    subclass with no supported ancestor (the graphene-django
    ``ImproperlyConfigured`` parity, raised as the package's own
    ``ConfigurationError``). Spelt as a factory so the no-catch-all contract -
    raise, never silently coerce to ``str`` - stays in this module's wording.
    The field's kind and repr are read through ``truth.kind`` / ``truth.render``.
    """
    return ConfigurationError(
        f"Unsupported form field type {truth.kind(field)!r} on form "
        f"field {truth.render(field)}. convert_form_field has no mapping "
        "for it and no supported ancestor; subclass a supported form field, or "
        "drop it via Meta.fields / Meta.exclude.",
    )
