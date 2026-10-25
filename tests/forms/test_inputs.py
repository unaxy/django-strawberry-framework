"""Form-derived input tests for the generated ``<FormClass>Input`` / ``PartialInput``.

Covers ``django_strawberry_framework/forms/inputs.py`` (the generation
substrate):

- ``get_form_fields`` discovery from ``base_fields`` with NO instantiation (incl.
  a kwarg-requiring form);
- the two generated inputs: ``<FormClass>Input`` (create; requiredness from
  ``field.required``) and ``<FormClass>PartialInput`` (model-backed optional, a
  non-model extra field still required);
- the ``ModelChoiceField`` / ``ModelMultipleChoiceField`` id mapping (Relay-``GlobalID``
  vs raw pk by the target's primary ``DjangoType``, single + multi), the
  ``FileField`` -> ``Upload`` mapping, and the reverse map (``category`` ->
  ``category_id`` / ``categoryId`` / ``relation_single``);
- the ``ChoiceField``-over-model-``choices`` symmetric-enum reuse (proves the
  overlap routes through the read converter, not a parallel table), and a choice
  field admitting fewer of the column's values publishing the generated enum of the
  admitted values (or refused at build when it admits no non-empty one, or writes a
  list over a single-value column);
- the ``to_field_name`` build guard: a key must be the primary key or a column of the
  target unique on its own (``require_readable_choice_keys``);
- ``Meta.fields`` / ``Meta.exclude`` narrowing + fail-loud, the empty-effective-set
  raise, and the create-required-narrowing guard + its waiver;
- shape-identity dedupe + the distinct-shape / same-``__name__`` collision raise
  via ``materialize_form_input_class``, and module-global materialization.

System-under-test is the generator run against the products ``Item`` / ``Category``
FK fixtures, library ``Genre`` / ``Branch`` as Relay / plain relation targets,
``Book.circulation_status`` for the choices enum, and package-local forms for the
``Upload`` and plain-``Form``-only shapes. Mirrors the
``tests/mutations/test_inputs.py`` fixture posture. Shipped form SDL and writes
live in ``examples/fakeshop/test_query/test_products_api.py`` /
``test_library_api.py`` / ``test_uploads_api.py``; this file keeps generator
fail-loud, shape identity, and throwaway-type id mapping.
"""

from __future__ import annotations

import decimal
import functools
import logging
import re
import sys
from collections.abc import Callable, Iterator
from enum import Enum
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import strawberry
from apps.library import models as library_models
from apps.library.forms import PatronProfileGenreForm, PatronProfileGenreNameForm
from apps.library.models import Book, Branch, Genre, TaggedItem
from apps.products import models as product_models
from apps.products.models import Category
from apps.scalars import models as scalar_models
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.expressions import Combinable
from strawberry import relay
from strawberry.types.base import StrawberryList, StrawberryOptional, get_object_definition
from strawberry.types.enum import StrawberryEnumDefinition
from strawberry.types.field import StrawberryField
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
)
from django_strawberry_framework.forms.inputs import (
    CREATE_SHAPED_KINDS,
    FORM,
    INPUTS_MODULE_PATH,
    _form_basis_content_identity,
    _model_column_for,
    build_form_input_class,
    clear_form_input_namespace,
    form_input_type_name,
    get_form_fields,
    guard_create_required_fields,
    guard_partial_required_column_less_fields,
    materialize_form_input_class,
    normalize_form_field_basis,
    require_readable_choice_keys,
    resolve_effective_form_fields,
)
from django_strawberry_framework.mutations.inputs import CREATE, PARTIAL
from django_strawberry_framework.registry import registry
from django_strawberry_framework.scalars import Upload, strawberry_config
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.converters import convert_choices_to_enum
from django_strawberry_framework.utils._narrowing import enum_value, list_of, require
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.inputs import InputFieldSpec
from django_strawberry_framework.utils.relations import is_model_class
from tests._idioms import ClassReadRaises, module_binding
from tests._postgres_fields import FakeArrayField, patch_array_field
from tests._relation_fixtures import RpCompositeParent

if TYPE_CHECKING:
    from django.db.models import Model
    from django.db.models.expressions import Combinable

    from django_strawberry_framework.forms.inputs import FormClass


def _as_form_class(stand_in: object) -> FormClass:
    """Hand a duck-typed form class to the column resolver that takes a form class."""
    # basedpyright: a plain stand-in class carrying only the hooks the code under test reads;
    # _model_column_for types the parameter as FormClass
    return stand_in  # pyright: ignore[reportReturnType]


@pytest.fixture(autouse=True)
def _isolate_registry_and_ledger() -> Iterator[None]:
    """Reset registry + the form-input ledger so each test starts clean.

    ``clear_form_input_namespace`` is not wired into ``registry.clear()``
    here, so the ledger is cleared explicitly. ``registry.clear()``
    is still needed because the products ``DjangoType``s and local fixtures
    register themselves on import / declaration.
    """
    registry.clear()
    clear_form_input_namespace()
    yield
    registry.clear()
    clear_form_input_namespace()


def _field_map(input_cls: type) -> dict[str, StrawberryField]:
    """Return ``python_name -> StrawberryField`` for a built input class."""
    return {f.python_name: f for f in get_object_definition(input_cls, strict=True).fields}


def _is_optional(field: StrawberryField) -> bool:
    """Return whether a Strawberry field's annotation is ``T | None``."""
    return isinstance(field.type, StrawberryOptional)


def _inner_type(field: StrawberryField) -> object:
    """Return the inner type of a ``StrawberryOptional`` field, else the type itself."""
    return field.type.of_type if isinstance(field.type, StrawberryOptional) else field.type


def _make_relay_target() -> tuple[type[library_models.Genre], type[DjangoType]]:
    """Register a Relay-Node ``DjangoType`` over ``library.Genre`` and return both."""

    class GenreNode(DjangoType, relay.Node):
        class Meta:
            model = Genre
            fields = ("id", "name")

    return Genre, GenreNode


def _make_non_relay_target() -> tuple[type[library_models.Branch], type[DjangoType]]:
    """Register a non-Relay ``DjangoType`` over ``library.Branch`` (raw int pk) and return both."""

    class BranchPlainType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")

    return Branch, BranchPlainType


# ---------------------------------------------------------------------------
# Module-path constant
# ---------------------------------------------------------------------------


def test_inputs_module_path_and_kind_constants() -> None:
    """The hoisted constants match the expected module path and create-shaped kinds."""
    assert INPUTS_MODULE_PATH == "django_strawberry_framework.forms.inputs"
    assert frozenset({CREATE, FORM}) == CREATE_SHAPED_KINDS


# ---------------------------------------------------------------------------
# get_form_fields / basis normalization - discovery from base_fields or hook
# ---------------------------------------------------------------------------


def test_get_form_fields_reads_base_fields() -> None:
    """Discovery returns the form's declared field dict in declaration order."""

    class SimpleForm(forms.Form):
        name = forms.CharField()
        age = forms.IntegerField()

    discovered = get_form_fields(SimpleForm)
    assert list(discovered) == ["name", "age"]
    assert isinstance(discovered["name"], forms.CharField)


def test_get_form_fields_does_not_instantiate_kwarg_requiring_form() -> None:
    """A form whose ``__init__`` requires a kwarg still yields a shape via ``base_fields``.

    Reading ``base_fields`` (the class-level declared-fields dict) needs no
    ``KwargForm()`` call, so a migrated form requiring ``user`` / ``request`` /
    a tenant still has a discoverable, request-independent stable shape.
    """

    class KwargForm(forms.Form):
        email = forms.EmailField()

        def __init__(self, *, user: object) -> None:
            # No-arg instantiation would raise TypeError (missing ``user``); the
            # discovery never instantiates, so the shape is still readable.
            super().__init__()
            self.user = user

    discovered = get_form_fields(KwargForm)
    assert list(discovered) == ["email"]
    with pytest.raises(TypeError):
        # basedpyright: deliberately omits ``user``; proves the form genuinely cannot be
        # instantiated no-arg
        KwargForm()  # pyright: ignore[reportCallIssue]


def test_corrupted_base_fields_raises_typed_on_default_path() -> None:
    """A clobbered ``base_fields`` raises a typed diagnostic naming the form.

    The default basis acquisition (``dict(form_class.base_fields)`` inside
    ``get_form_fields``) is guarded alongside the hook mapping: a consumer having
    clobbered ``base_fields`` to a non-mapping raises ``ConfigurationError``
    naming the form instead of a raw ``TypeError`` propagating out of
    ``build_form_input_class`` (the bind's build path).
    """

    class Corrupt(forms.Form):
        pass

    # basedpyright: the corrupt base_fields value is the hostile input under test; django-stubs
    # types the slot as a field mapping
    Corrupt.base_fields = 123  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(ConfigurationError, match="Corrupt"):
        build_form_input_class(Corrupt, operation_kind=FORM)


_HOSTILE_CLASS_ERRORS = [RuntimeError, TypeError, KeyboardInterrupt]


@pytest.mark.parametrize("raised", _HOSTILE_CLASS_ERRORS)
def test_hostile_class_base_fields_value_raises_typed_on_default_path(
    raised: type[BaseException],
) -> None:
    """A ``base_fields`` value whose ``__class__`` raises is typed on the default path.

    The default hook copies a clobbered ``base_fields`` mapping into the basis, so
    the per-value check guards it like a hook return: ``build_form_input_class`` raises
    ``ConfigurationError`` naming the form and the entry, never the raw exception.
    """

    class Corrupt(forms.Form):
        pass

    # basedpyright: the hostile base_fields value is the input under test; django-stubs
    # types the slot as a field mapping
    Corrupt.base_fields = {"x": ClassReadRaises(raised)}  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(ConfigurationError) as exc:
        build_form_input_class(Corrupt, operation_kind=FORM)
    assert str(exc.value) == (
        "DjangoFormMutation for Corrupt get_form_fields() must return a mapping of string "
        "names to forms.Field instances; invalid names [], invalid fields ['x']."
    )


def test_normalize_form_field_basis_rejects_none() -> None:
    """A mutation hook returning ``None`` raises a fail-loud ``ConfigurationError``."""

    class ProbeForm(forms.Form):
        pass

    with pytest.raises(ConfigurationError, match=r"must return a mapping.*not None"):
        normalize_form_field_basis(ProbeForm, None)


def test_form_field_basis_rejects_non_mapping_source() -> None:
    """A non-mapping basis object raises a fail-loud ``ConfigurationError``."""

    class ProbeForm(forms.Form):
        pass

    with pytest.raises(ConfigurationError, match="must return a mapping of field names"):
        normalize_form_field_basis(ProbeForm, 123)


def test_form_field_basis_rejects_malformed_names_and_field_values() -> None:
    """A hook-returned basis reports every bad key AND every bad value in one error."""

    class ProbeForm(forms.Form):
        pass

    with pytest.raises(ConfigurationError, match=r"invalid names.*invalid fields"):
        normalize_form_field_basis(
            ProbeForm,
            {1: forms.CharField(), "name": object()},
        )


def test_basis_rejects_non_identifier_field_names() -> None:
    """A basis with a non-identifier field name raises typed, naming it.

    A generated input attribute is rendered into the dataclass ``__init__``, so
    an empty / spaced / digit-leading / keyword name could never build an input:
    before the identifier guard such a name passed the string check and detonated
    as a raw ``SyntaxError`` out of the generated ``__init__`` source at
    input-class construction.
    """

    class ProbeForm(forms.Form):
        pass

    for name in (
        "",
        "with space",
        "9lead",
        "class",
        "None",
    ):
        with pytest.raises(ConfigurationError, match="invalid names"):
            normalize_form_field_basis(ProbeForm, {name: forms.CharField()})


def test_weird_field_names_fail_loud_through_build() -> None:
    """Weird names through the full build raise a typed diagnostic, not SyntaxError."""

    class ProbeForm(forms.Form):
        pass

    weird = {"": forms.CharField(), "with space": forms.CharField(), "good": forms.CharField()}
    with pytest.raises(ConfigurationError, match="invalid names"):
        build_form_input_class(ProbeForm, form_fields=weird, operation_kind=FORM)


def test_normalize_form_field_basis_valid_mapping() -> None:
    """A valid hook-returned mapping normalizes to a fresh dict of field instances."""

    class ProbeForm(forms.Form):
        pass

    custom = {"custom": forms.CharField()}
    normalized = normalize_form_field_basis(ProbeForm, custom)
    assert normalized == custom
    assert normalized is not custom


def test_build_form_input_class_with_custom_form_fields_basis() -> None:
    """``build_form_input_class`` honors an explicit ``form_fields`` basis mapping."""

    class DynamicForm(forms.Form):
        pass

    custom = {"title": forms.CharField(required=True), "notes": forms.CharField(required=False)}
    cre, specs = build_form_input_class(DynamicForm, operation_kind=FORM, form_fields=custom)
    par, _ = build_form_input_class(DynamicForm, operation_kind=PARTIAL, form_fields=custom)
    assert set(_field_map(cre)) == {"title", "notes"}
    assert set(_field_map(par)) == {"title", "notes"}
    assert len(specs) == 2


def test_guard_create_required_fields_with_custom_form_fields() -> None:
    """``guard_create_required_fields`` honors an explicit ``form_fields`` basis."""

    class DynamicForm(forms.Form):
        pass

    custom = {"req": forms.CharField(required=True), "opt": forms.CharField(required=False)}
    with pytest.raises(ConfigurationError, match="req"):
        guard_create_required_fields(DynamicForm, ("opt",), form_fields=custom)


def test_guard_partial_required_column_less_fields_with_custom_form_fields() -> None:
    """``guard_partial_required_column_less_fields`` honors an explicit ``form_fields`` basis."""

    class DynamicForm(forms.Form):
        pass

    custom = {"req": forms.CharField(required=True), "opt": forms.CharField(required=False)}
    with pytest.raises(ConfigurationError, match="req"):
        guard_partial_required_column_less_fields(DynamicForm, ("opt",), form_fields=custom)


# ---------------------------------------------------------------------------
# The two generated inputs - create + partial requiredness
# ---------------------------------------------------------------------------


def _item_model_form() -> type[forms.ModelForm[product_models.Item]]:
    """A ``ModelForm`` over products ``Item`` with a non-model required ``confirm`` extra."""

    class ItemModelForm(forms.ModelForm[product_models.Item]):
        confirm = forms.BooleanField(required=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemModelForm


def test_create_input_required_and_optional_shapes() -> None:
    """``<FormClass>Input``: required fields non-optional, optional fields ``| None`` + UNSET."""
    cre, _ = build_form_input_class(_item_model_form(), operation_kind=CREATE)
    assert cre.__name__ == "ItemModelFormInput"
    fields = _field_map(cre)

    # ``name`` (required TextField) is non-optional.
    assert not _is_optional(fields["name"])
    assert _inner_type(fields["name"]) is str

    # The FK ``category`` -> ``category_id`` / ``categoryId``, required.
    assert not _is_optional(fields["category_id"])
    assert fields["category_id"].graphql_name == "categoryId"

    # The non-model required ``confirm`` is required in create.
    assert not _is_optional(fields["confirm"])

    # ``is_private`` (BooleanField, not required) is optional + UNSET.
    assert _is_optional(fields["is_private"])
    assert fields["is_private"].default_value is UNSET


@pytest.mark.parametrize(
    ("model", "key", "input_key"),
    [
        (library_models.PatronProfile, "patron", "patron_id"),
        (library_models.Edition, "isbn_13", "isbn_13"),
    ],
    ids=["one-to-one-key", "text-key"],
)
def test_partial_input_leaves_out_the_primary_key_the_create_input_carries(
    model: type[models.Model],
    key: str,
    input_key: str,
) -> None:
    """A form field over the model's primary key is a create input and never an update input.

    The create names its row by the client-assigned key; the partial input leaves it out
    (the mutation's ``id`` argument names the row) and keeps its canonical name, since
    the key is not part of any update shape.
    """
    other = "address_2" if model is library_models.PatronProfile else "imprint"
    form_cls = forms.modelform_factory(model, fields=(key, other))

    cre, _ = build_form_input_class(form_cls, operation_kind=CREATE)
    par, _ = build_form_input_class(form_cls, operation_kind=PARTIAL)

    assert set(_field_map(cre)) == {input_key, other}
    assert set(_field_map(par)) == {other}
    assert par.__name__ == f"{form_cls.__name__}PartialInput"


def test_partial_input_leaves_out_every_composite_key_member_the_create_input_carries() -> None:
    """Each member column of a ``CompositePrimaryKey`` is a create input and never an update input.

    A member's own ``primary_key`` flag is ``False``, yet ``construct_instance`` writing one
    re-keys the located row. Naming a member in an update ``fields`` is refused and in
    ``exclude`` accepted, stating what the update input already does.
    """
    form_cls = forms.modelform_factory(
        RpCompositeParent,
        fields=("tenant_id", "code", "label"),
    )

    cre, _ = build_form_input_class(form_cls, operation_kind=CREATE)
    par, _ = build_form_input_class(form_cls, operation_kind=PARTIAL)

    assert list(_field_map(cre)) == ["tenant_id", "code", "label"]
    assert list(_field_map(par)) == ["label"]
    assert list(
        resolve_effective_form_fields(form_cls, exclude=("code",), operation_kind=PARTIAL),
    ) == ["label"]
    with pytest.raises(
        ConfigurationError,
        match=re.escape("declares `fields` naming ['tenant_id'], which write(s) the row's"),
    ):
        resolve_effective_form_fields(
            form_cls,
            fields=("tenant_id", "label"),
            operation_kind=PARTIAL,
        )


class _FrozenKeyRow(models.Model):
    """An unmanaged owner of an ``editable=False`` text primary key ``code``."""

    code: models.TextField[str | Combinable, str] = models.TextField(
        primary_key=True,
        editable=False,
    )
    name: models.TextField[str | Combinable, str] = models.TextField()

    class Meta:
        managed = False
        app_label = "test_forms_frozen_key"


def test_partial_input_keeps_a_form_field_named_like_a_non_editable_key() -> None:
    """A declared form field named like an ``editable=False`` key stays an update input.

    ``construct_instance`` never writes a non-editable column, so the field cannot re-key
    the located row: it is an ordinary input (a value a custom ``save()`` may read), not
    the row identity an update leaves out.
    """

    class FrozenKeyForm(forms.ModelForm[_FrozenKeyRow]):
        code = forms.CharField()

        class Meta:
            model = _FrozenKeyRow
            fields = ("name",)

    par, _ = build_form_input_class(FrozenKeyForm, operation_kind=PARTIAL)

    assert set(_field_map(par)) == {"name", "code"}


def test_partial_input_model_backed_optional_extra_field_still_required() -> None:
    """``<FormClass>PartialInput``: model-backed fields optional, a required extra stays required."""
    par, _ = build_form_input_class(_item_model_form(), operation_kind=PARTIAL)
    assert par.__name__ == "ItemModelFormPartialInput"
    fields = _field_map(par)

    # Model-backed fields are forced optional + UNSET in the partial input.
    for name in ("name", "category_id", "is_private"):
        assert _is_optional(fields[name]), name
        assert fields[name].default_value is UNSET, name

    # The non-model required ``confirm`` keeps its declared ``field.required``
    # (the load-bearing partial assertion).
    assert not _is_optional(fields["confirm"])


def test_plain_form_only_field_included_in_input() -> None:
    """A plain ``Form`` field (no model column) appears in the input (derives from the form)."""

    class ContactForm(forms.Form):
        name = forms.CharField()
        captcha = forms.CharField(required=False)

    cre, _ = build_form_input_class(ContactForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert set(fields) == {"name", "captcha"}
    assert not _is_optional(fields["name"])
    assert _is_optional(fields["captcha"])


def test_null_boolean_field_is_optional_even_when_django_required() -> None:
    """Default ``NullBooleanField(required=True)`` is still optional + UNSET in the input.

    Converter forces ``required=False`` (Django validate is a no-op; GraphQL cannot
    express required-nullable). The build site must honor ``conversion.required``
    so omitting the field does not TypeError after GraphQL validation allows it.
    """

    class FlagForm(forms.Form):
        flag = forms.NullBooleanField()  # Django default required=True
        name = forms.CharField()

    cre, _ = build_form_input_class(FlagForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _is_optional(fields["flag"])
    assert fields["flag"].default_value is UNSET
    assert not _is_optional(fields["name"])


def test_non_null_column_backed_null_boolean_stays_required() -> None:
    """Model validation makes a required NullBooleanField over ``null=False`` non-null.

    ``library.Issue.embargoed`` is the non-null ``BooleanField`` carrier.
    """

    class IssueForm(forms.ModelForm[library_models.Issue]):
        embargoed = forms.NullBooleanField(required=True)

        class Meta:
            model = library_models.Issue
            fields = ("embargoed", "title")

    cre, _ = build_form_input_class(IssueForm, operation_kind=CREATE)
    fields = _field_map(cre)
    assert not _is_optional(fields["embargoed"])
    with pytest.raises(ConfigurationError, match=r"drops required form field.*embargoed"):
        guard_create_required_fields(IssueForm, ("title",))


def test_column_backed_null_boolean_is_optional() -> None:
    """A ``NullBooleanField`` backed by a nullable model column is optional too.

    The requiredness rule must apply on EVERY conversion path, not just the
    model-less one: a ``ModelForm`` field whose backing column resolves still
    routes through the shared ``form_field_required`` helper, so a Django
    ``required=True`` ``NullBooleanField`` over a column widens to ``| None`` +
    ``UNSET`` rather than compiling a required field from the raw
    ``field.required``.
    ``scalars.NullableScalarSpecimen.flag`` is the nullable carrier.
    """

    class NullableSpecimenForm(forms.ModelForm[scalar_models.NullableScalarSpecimen]):
        flag = forms.NullBooleanField()  # Django default required=True

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = ("flag",)

    cre, _ = build_form_input_class(NullableSpecimenForm, operation_kind=CREATE)
    fields = _field_map(cre)
    assert _is_optional(fields["flag"])
    assert fields["flag"].default_value is UNSET


def test_create_guard_ignores_django_required_null_boolean() -> None:
    """A Django-``required=True`` ``NullBooleanField`` is not create-required.

    Narrowing it out of the input must NOT trip the create-required guard - the
    field is optional in the schema and a bound form validates without it.
    """

    class FlagForm(forms.Form):
        flag = forms.NullBooleanField()  # Django default required=True
        name = forms.CharField()

    cre, _ = build_form_input_class(FlagForm, operation_kind=FORM, fields=("name",))
    assert set(_field_map(cre)) == {"name"}


def test_json_field_maps_to_json_scalar_in_input() -> None:
    """A plain ``Form`` ``JSONField`` maps to ``strawberry.scalars.JSON``, not ``str``."""

    class PayloadForm(forms.Form):
        payload = forms.JSONField()

    cre, specs = build_form_input_class(PayloadForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["payload"]) is strawberry.scalars.JSON
    assert next(s for s in specs if s.target_name == "payload").kind == SCALAR


# ---------------------------------------------------------------------------
# Relation id mapping - Relay vs raw pk, single + multi
# ---------------------------------------------------------------------------


def test_fk_to_non_relay_products_target_uses_raw_pk_id() -> None:
    """The products ``Item.category`` FK (non-Relay ``CategoryType``) becomes a raw pk id."""
    cre, specs = build_form_input_class(_item_model_form(), operation_kind=CREATE)
    fields = _field_map(cre)
    # CategoryType is non-Relay, so the id is the raw pk scalar (int), not GlobalID.
    assert _inner_type(fields["category_id"]) is int
    # Reverse map: input attr -> form field name + kind (unified InputFieldSpec).
    cat_spec = next(s for s in specs if s.target_name == "category")
    assert isinstance(cat_spec, InputFieldSpec)
    assert cat_spec.input_attr == "category_id"
    assert cat_spec.graphql_name == "categoryId"
    assert cat_spec.kind == RELATION_SINGLE
    assert cat_spec.source is None
    assert cat_spec.nested_specs is None


def test_model_choice_field_to_relay_target_uses_id() -> None:
    """A model-less ``ModelChoiceField`` to a Relay primary becomes ``<name>_id: ID``."""
    relay_target, _ = _make_relay_target()

    class PickForm(forms.Form):
        target = forms.ModelChoiceField(queryset=relay_target.objects.all())

    cre, specs = build_form_input_class(PickForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["target_id"]) is strawberry.ID
    spec = next(s for s in specs if s.target_name == "target")
    assert spec.input_attr == "target_id"
    assert spec.kind == RELATION_SINGLE
    assert spec.related_model is relay_target


def test_model_choice_field_to_non_relay_target_uses_raw_pk() -> None:
    """A model-less ``ModelChoiceField`` to a non-Relay primary becomes a raw pk id."""
    plain_target, _ = _make_non_relay_target()

    class PickForm(forms.Form):
        target = forms.ModelChoiceField(queryset=plain_target.objects.all())

    cre, _ = build_form_input_class(PickForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["target_id"]) is int


def test_model_multiple_choice_field_to_relay_target_is_list_of_id() -> None:
    """A ``ModelMultipleChoiceField`` to a Relay primary becomes ``list[ID]``, kind multi."""
    relay_target, _ = _make_relay_target()

    class PickManyForm(forms.Form):
        targets = forms.ModelMultipleChoiceField(queryset=relay_target.objects.all())

    cre, specs = build_form_input_class(PickManyForm, operation_kind=FORM)
    fields = _field_map(cre)
    inner = _inner_type(fields["targets"])
    assert inner == list[strawberry.ID]
    spec = next(s for s in specs if s.target_name == "targets")
    assert spec.input_attr == "targets"
    assert spec.kind == RELATION_MULTI


def test_model_multiple_choice_field_to_non_relay_target_is_list_of_raw_pk() -> None:
    """A ``ModelMultipleChoiceField`` to a non-Relay primary becomes ``list[<raw pk>]``."""
    plain_target, _ = _make_non_relay_target()

    class PickManyForm(forms.Form):
        targets = forms.ModelMultipleChoiceField(queryset=plain_target.objects.all())

    cre, _ = build_form_input_class(PickManyForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["targets"]) == list[int]


# ---------------------------------------------------------------------------
# FileField -> Upload, kind file
# ---------------------------------------------------------------------------


def test_file_field_maps_to_upload() -> None:
    """A plain ``Form`` ``FileField`` maps to ``Upload`` with kind ``file``."""

    class AvatarForm(forms.Form):
        avatar = forms.FileField()

    cre, specs = build_form_input_class(AvatarForm, operation_kind=FORM)
    fields = _field_map(cre)
    assert _inner_type(fields["avatar"]) is Upload
    spec = next(s for s in specs if s.target_name == "avatar")
    assert spec.kind == FILE


class _FileWidgetField(forms.Field):
    """A custom field with no ``FileField`` ancestor, rendered as an upload: it reads ``files``."""

    widget = forms.ClearableFileInput


def test_field_with_a_file_widget_maps_to_upload() -> None:
    """A column-less field whose widget reads ``files`` takes an ``Upload``, never a ``String``.

    The bound form reads the value from ``files``, so a ``String`` input could never fill it.
    """

    class ScanForm(forms.Form):
        scan = _FileWidgetField()

    cre, specs = build_form_input_class(ScanForm, operation_kind=FORM)
    assert _inner_type(_field_map(cre)["scan"]) is Upload
    assert [spec.kind for spec in specs] == [FILE]


class _MultipartTextarea(forms.Textarea):
    """A text widget that asks for a multipart form yet reads ``data``, as every ``Textarea``."""

    needs_multipart_form = True


def test_field_with_a_multipart_text_widget_stays_a_string() -> None:
    """A column-less field whose widget only asks for a multipart form still takes a ``String``."""

    class NoteForm(forms.Form):
        note = forms.CharField(widget=_MultipartTextarea)

    cre, specs = build_form_input_class(NoteForm, operation_kind=FORM)
    assert _inner_type(_field_map(cre)["note"]) is str
    assert [spec.kind for spec in specs] == [SCALAR]


@pytest.mark.parametrize("operation_kind", [CREATE, PARTIAL])
def test_field_with_a_multipart_text_widget_over_a_text_column_builds(
    operation_kind: str,
) -> None:
    """A text field rendered with a multipart text widget agrees with its text column."""
    form_class = _column_form(
        product_models.Item,
        "description",
        forms.CharField(widget=_MultipartTextarea, required=False),
    )
    built, specs = build_form_input_class(form_class, operation_kind=operation_kind)
    assert _inner_type(_field_map(built)["description"]) is str
    assert [spec.kind for spec in specs] == [SCALAR]


@pytest.mark.parametrize("operation_kind", [CREATE, PARTIAL])
def test_field_with_a_file_widget_over_a_file_column_builds(operation_kind: str) -> None:
    """A custom field with a file widget over a file column agrees with it on both inputs."""
    form_class = _column_form(product_models.Item, "attachment", _FileWidgetField())
    built, specs = build_form_input_class(form_class, operation_kind=operation_kind)
    assert _inner_type(_field_map(built)["attachment"]) is Upload
    assert [spec.kind for spec in specs] == [FILE]


# ---------------------------------------------------------------------------
# ChoiceField over a ModelForm model's choices -> the SAME read-side enum
# ---------------------------------------------------------------------------


def test_choices_modelform_field_resolves_to_read_side_enum() -> None:
    """A ``ModelForm`` field over a model ``choices`` column reuses the read converter's enum.

    Proves the model-backed overlap routes through ``convert_scalar`` /
    ``convert_choices_to_enum`` (the symmetric wire contract), not a parallel
    form-field table (spec-038 Decision 7 - the shared-table drift guard).
    """

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "circulation_status")

    assert registry.get(Book) is BookType

    class BookStatusForm(forms.ModelForm[Book]):
        class Meta:
            model = Book
            fields = ("circulation_status",)

    cre, _ = build_form_input_class(BookStatusForm, operation_kind=CREATE)
    fields = _field_map(cre)
    circulation_status = Book._meta.get_field("circulation_status")
    assert isinstance(circulation_status, models.Field)
    read_enum = convert_choices_to_enum(circulation_status, "BookType")
    # The generated input field uses the IDENTICAL enum object the read DjangoType
    # synthesizes (cached per column on the model field), not a parallel ``str``
    # mapping. Strawberry wraps the enum class in a ``StrawberryEnumDefinition`` on
    # the resolved field type, so compare its ``wrapped_cls`` against the raw enum
    # ``convert_choices_to_enum`` returns - same object proves the symmetric reuse.
    inner = _inner_type(fields["circulation_status"])
    assert isinstance(inner, StrawberryEnumDefinition)
    assert inner.wrapped_cls is read_enum


# ---------------------------------------------------------------------------
# A choice field admitting fewer of the column's values -> a generated enum
# ---------------------------------------------------------------------------

_DESK_CHOICES = [("available", "Available"), ("repair", "Repair")]
_ALL_STATUS_CHOICES = [*_DESK_CHOICES, ("checked_out", "Checked out")]


def _book_status_form(status_field: forms.Field) -> FormClass:
    """A ``Book`` ``ModelForm`` declaring ``circulation_status`` as ``status_field``."""

    class BookStatusForm(forms.ModelForm[library_models.Book]):
        circulation_status = status_field

        class Meta:
            model = library_models.Book
            fields = ("title", "circulation_status")

    return BookStatusForm


def _shelf_form(name: str, shelf_field: forms.Field) -> FormClass:
    """A ``Shelf`` ``ModelForm`` declaring the ``name`` column's field as ``shelf_field``."""
    meta = type("Meta", (), {"model": library_models.Shelf, "fields": (name,)})
    return type("ShelfChoiceForm", (forms.ModelForm,), {name: shelf_field, "Meta": meta})


def _enum_of(field: StrawberryField) -> type[Enum]:
    """Return the enum class a generated input field publishes."""
    inner = _inner_type(field)
    assert isinstance(inner, StrawberryEnumDefinition)
    enum_cls = inner.wrapped_cls
    assert issubclass(enum_cls, Enum)
    return enum_cls


def _members(enum_cls: type[Enum]) -> dict[str, object]:
    return {member.name: enum_value(member) for member in enum_cls}


@pytest.mark.parametrize(
    "status_field",
    [
        pytest.param(
            lambda: forms.TypedChoiceField(choices=_DESK_CHOICES, coerce=str),
            id="typed-choice",
        ),
        pytest.param(
            lambda: forms.ChoiceField(choices=_DESK_CHOICES, required=False),
            id="optional",
        ),
        pytest.param(
            lambda: forms.ChoiceField(choices=[("Desk", _DESK_CHOICES)]),
            id="grouped",
        ),
        pytest.param(
            lambda: forms.ChoiceField(choices=[("", "---"), *_DESK_CHOICES], required=False),
            id="declared-empty-option",
        ),
    ],
)
def test_choice_field_narrower_than_column_publishes_admitted_values(
    status_field: Callable[[], forms.Field],
) -> None:
    """A choice field admitting fewer of the column's values publishes only those values.

    ``Book.circulation_status`` lists ``available`` / ``checked_out`` / ``repair`` and lists
    no ``""`` (not ``blank``), so a field admitting ``available`` / ``repair`` publishes a
    generated ``<Input><Field>Enum`` of exactly those two, members and values the column's,
    on both the create and the partial input; the read enum is left untouched.
    """
    column = library_models.Book._meta.get_field("circulation_status")
    assert isinstance(column, models.Field)
    read_enum = convert_choices_to_enum(column, "BookType")
    form_class = _book_status_form(status_field())
    cre, _ = build_form_input_class(form_class, operation_kind=CREATE)
    par, _ = build_form_input_class(form_class, operation_kind=PARTIAL)
    for input_cls, enum_name in (
        (cre, "BookStatusFormInputCirculationStatusEnum"),
        (par, "BookStatusFormPartialInputCirculationStatusEnum"),
    ):
        enum_cls = _enum_of(_field_map(input_cls)["circulation_status"])
        assert enum_cls is not read_enum
        assert enum_cls.__name__ == enum_name
        assert _members(enum_cls) == {"available": "available", "repair": "repair"}
    assert len(read_enum) == 3


@pytest.mark.parametrize(
    "status_field",
    [
        pytest.param(lambda: forms.ChoiceField(choices=_ALL_STATUS_CHOICES), id="equal"),
        pytest.param(
            lambda: forms.ChoiceField(choices=[*_ALL_STATUS_CHOICES, ("archived", "Archived")]),
            id="superset",
        ),
        pytest.param(lambda: forms.ChoiceField(choices=lambda: _DESK_CHOICES), id="callable"),
        pytest.param(lambda: forms.ChoiceField(choices=[]), id="assigned-per-request"),
        pytest.param(forms.CharField, id="not-a-choice-field"),
    ],
)
def test_choice_field_admitting_every_column_value_keeps_read_enum(
    status_field: Callable[[], forms.Field],
) -> None:
    """A field admitting every column value, or with no static choices, keeps the read enum.

    An equal set and a superset (whose extra value the column never stores, and the enum
    cannot carry) admit every value the column lists. Callable choices and an empty
    class-level set (choices assigned per request in ``__init__``) are not known at build,
    so the column's read enum is published and the bound form refuses at request time.
    """
    column = library_models.Book._meta.get_field("circulation_status")
    assert isinstance(column, models.Field)
    read_enum = convert_choices_to_enum(column, "BookType")
    cre, _ = build_form_input_class(_book_status_form(status_field()), operation_kind=CREATE)
    assert _enum_of(_field_map(cre)["circulation_status"]) is read_enum


def _column_form(
    model: type[models.Model],
    name: str,
    field: forms.Field,
    fields: tuple[str, ...] = (),
) -> FormClass:
    """A ``model`` ``ModelForm`` declaring the ``name`` column's field as ``field``."""
    meta = type("Meta", (), {"model": model, "fields": (name, *fields)})
    return type("KindForm", (forms.ModelForm,), {name: field, "Meta": meta})


def _genres() -> models.QuerySet[Genre]:
    return Genre.objects.all()


def _categories() -> models.QuerySet[Category]:
    return Category.objects.all()


@pytest.mark.parametrize(
    (
        "model",
        "name",
        "make_field",
        "kinds",
    ),
    [
        pytest.param(
            Book,
            "circulation_status",
            lambda: forms.ModelChoiceField(queryset=_genres(), to_field_name="name"),
            "(ModelChoiceField) is a single-relation field over the scalar column",
            id="model-choice-over-choice-column",
        ),
        pytest.param(
            product_models.Item,
            "is_private",
            lambda: forms.ModelChoiceField(queryset=_categories()),
            "(ModelChoiceField) is a single-relation field over the scalar column",
            id="model-choice-over-boolean",
        ),
        pytest.param(
            scalar_models.NullableScalarSpecimen,
            "payload",
            lambda: forms.ModelChoiceField(queryset=_categories()),
            "(ModelChoiceField) is a single-relation field over the scalar column",
            id="model-choice-over-json",
        ),
        pytest.param(
            Book,
            "title",
            lambda: forms.ModelMultipleChoiceField(queryset=_genres()),
            "(ModelMultipleChoiceField) is a multi-relation field over the scalar column",
            id="model-multiple-choice-over-text",
        ),
        pytest.param(
            product_models.Item,
            "attachment",
            lambda: forms.ModelChoiceField(queryset=_categories()),
            "(ModelChoiceField) is a single-relation field over the file column",
            id="model-choice-over-file",
        ),
        pytest.param(
            Book,
            "genres",
            lambda: forms.ModelChoiceField(queryset=_genres()),
            "(ModelChoiceField) is a single-relation field over the multi-relation column",
            id="model-choice-over-m2m",
        ),
        pytest.param(
            product_models.Item,
            "category",
            lambda: forms.ModelMultipleChoiceField(queryset=_categories()),
            "(ModelMultipleChoiceField) is a multi-relation field over the single-relation column",
            id="model-multiple-choice-over-fk",
        ),
        pytest.param(
            product_models.Item,
            "attachment",
            lambda: forms.ModelMultipleChoiceField(queryset=_categories()),
            "(ModelMultipleChoiceField) is a multi-relation field over the file column",
            id="model-multiple-choice-over-file",
        ),
        pytest.param(
            Book,
            "genres",
            forms.FileField,
            "(FileField) is a file field over the multi-relation column",
            id="file-over-m2m",
        ),
        pytest.param(
            scalar_models.NullableScalarSpecimen,
            "payload",
            forms.ImageField,
            "(ImageField) is a file field over the scalar column",
            id="image-over-json",
        ),
        pytest.param(
            product_models.Item,
            "description",
            lambda: forms.FileField(required=False),
            "(FileField) is a file field over the scalar column",
            id="file-over-text",
        ),
        pytest.param(
            product_models.Item,
            "category",
            forms.FileField,
            "(FileField) is a file field over the single-relation column",
            id="file-over-fk",
        ),
        pytest.param(
            product_models.Item,
            "attachment",
            lambda: forms.CharField(required=False),
            "(CharField) is a scalar field over the file column",
            id="scalar-over-file",
        ),
    ],
)
@pytest.mark.parametrize("operation_kind", [CREATE, PARTIAL])
def test_field_of_another_kind_than_its_column_is_refused(
    model: type[models.Model],
    name: str,
    make_field: Callable[[], forms.Field],
    kinds: str,
    operation_kind: str,
) -> None:
    """A field whose kind differs from its column's is refused, whichever input carries it.

    The input types and decodes the field by its column's kind while the bound form reads
    it by its own, so the two disagree on every value; only a scalar field over a relation
    column agrees.
    """
    form_class = _column_form(model, name, make_field())
    with pytest.raises(ConfigurationError, match=re.escape(f"field {name!r} {kinds}")):
        _ = build_form_input_class(form_class, operation_kind=operation_kind)


def test_kind_refusal_names_the_form_the_column_and_the_remedy() -> None:
    """The refusal names the form, the field and its class, both kinds, the column and the fix."""
    form_class = _column_form(
        product_models.Item,
        "description",
        forms.ModelChoiceField(queryset=_categories()),
    )
    with pytest.raises(ConfigurationError) as excinfo:
        _ = build_form_input_class(form_class, operation_kind=CREATE)
    assert str(excinfo.value) == (
        "Form KindForm field 'description' (ModelChoiceField) is a single-relation field "
        "over the scalar column Item.description: the input carries the column's value and "
        "the form reads the field's. Declare a form field of the column's kind, or name the "
        "field after no model column; an update binds every declared field, including those "
        "Meta.fields / Meta.exclude leave out of its input."
    )


#: A field of another kind than its column, every one optional so a create may leave it out:
#: a relation field over text (the stored text is looked up as a ``Category`` key), a file
#: field over text (it reads ``files``, never the stored text) and a scalar field over a
#: file column (it reads ``data``, never the stored file).
_NARROWED_OUT_MISMATCHES = [
    pytest.param(
        "description",
        lambda: forms.ModelChoiceField(queryset=_categories(), required=False),
        "(ModelChoiceField) is a single-relation field over the scalar column",
        id="model-choice-over-text",
    ),
    pytest.param(
        "description",
        lambda: forms.FileField(required=False),
        "(FileField) is a file field over the scalar column",
        id="file-over-text",
    ),
    pytest.param(
        "attachment",
        lambda: forms.CharField(required=False),
        "(CharField) is a scalar field over the file column",
        id="scalar-over-file",
    ),
]


@pytest.mark.parametrize(("name", "make_field", "kinds"), _NARROWED_OUT_MISMATCHES)
def test_update_input_refuses_a_kind_mismatch_on_a_narrowed_out_field(
    name: str,
    make_field: Callable[[], forms.Field],
    kinds: str,
) -> None:
    """An update rebinds every declared field from the row, the narrowed-out one included."""
    form_class = _column_form(product_models.Item, name, make_field(), fields=("name",))
    with pytest.raises(ConfigurationError, match=re.escape(f"field {name!r} {kinds}")):
        _ = build_form_input_class(form_class, operation_kind=PARTIAL, fields=("name",))


@pytest.mark.parametrize(("name", "make_field", "kinds"), _NARROWED_OUT_MISMATCHES)
def test_create_input_admits_a_kind_mismatch_on_a_narrowed_out_field(
    name: str,
    make_field: Callable[[], forms.Field],
    kinds: str,
) -> None:
    """A create binds only its input's fields, so a narrowed-out field is never bound."""
    del kinds
    form_class = _column_form(product_models.Item, name, make_field(), fields=("name",))
    _cls, specs = build_form_input_class(form_class, operation_kind=CREATE, fields=("name",))

    assert [spec.target_name for spec in specs] == ["name"]


@pytest.mark.parametrize(
    (
        "model",
        "name",
        "make_field",
        "attr",
        "kind",
    ),
    [
        pytest.param(
            product_models.Item,
            "category",
            forms.IntegerField,
            "category_id",
            RELATION_SINGLE,
            id="integer-over-fk",
        ),
        pytest.param(
            product_models.Item,
            "category",
            forms.CharField,
            "category_id",
            RELATION_SINGLE,
            id="text-over-fk",
        ),
        pytest.param(
            Book,
            "genres",
            forms.MultipleChoiceField,
            "genres",
            RELATION_MULTI,
            id="multiple-choice-over-m2m",
        ),
    ],
)
@pytest.mark.parametrize("operation_kind", [CREATE, PARTIAL])
def test_scalar_field_over_relation_column_takes_the_relation_id(
    model: type[models.Model],
    name: str,
    make_field: Callable[[], forms.Field],
    attr: str,
    kind: str,
    operation_kind: str,
) -> None:
    """A scalar field over a relation column builds the relation's id input and kind.

    The decode hands the field the visible row's key, as an HTML form posts it, and the
    form resolves the key itself.
    """
    form_class = _column_form(model, name, make_field())
    built, specs = build_form_input_class(form_class, operation_kind=operation_kind)
    assert list(_field_map(built)) == [attr]
    assert [spec.kind for spec in specs] == [kind]


@pytest.mark.parametrize(
    ("required", "members"),
    [(False, ["BLANK", "good", "worn"]), (True, ["good", "worn"])],
)
def test_choice_field_narrowing_keeps_blank_only_when_the_form_admits_it(
    *,
    required: bool,
    members: list[str],
) -> None:
    """``BLANK`` stays only where the form admits ``""``: a field that is not required.

    ``Shelf.condition`` is ``blank=True``, so the column lists ``""``. A single-value
    ``ChoiceField`` passes ``""`` without reading its choices when it is not required and
    refuses it as required otherwise, so the narrowed enum keeps ``BLANK`` exactly then.
    """
    form_class = _shelf_form(
        "condition",
        forms.ChoiceField(choices=[("good", "G"), ("worn", "W")], required=required),
    )
    cre, _ = build_form_input_class(form_class, operation_kind=CREATE)
    assert list(_members(_enum_of(_field_map(cre)["condition"]))) == members


def test_typed_choice_field_narrowing_over_integer_column_keeps_column_values() -> None:
    """An integer column's narrowed members carry the column's ``int`` values.

    ``Shelf.tier`` is an ``IntegerChoices`` column; a ``TypedChoiceField(coerce=int)``
    declaring ``"1"`` / ``"2"`` admits the column's ``1`` / ``2`` (Django's ``valid_value``
    also compares as ``str``), so the generated enum holds the column's values.
    """
    form_class = _shelf_form(
        "tier",
        forms.TypedChoiceField(choices=[("1", "Low"), ("2", "Mid")], coerce=int),
    )
    cre, _ = build_form_input_class(form_class, operation_kind=CREATE)
    assert _members(_enum_of(_field_map(cre)["tier"])) == {"MEMBER_1": 1, "MEMBER_2": 2}


def test_choice_field_admitting_no_column_value_is_refused() -> None:
    """A field admitting no non-empty value the column lists is refused at build."""
    form_class = _book_status_form(forms.ChoiceField(choices=[("lost", "Lost")]))
    with pytest.raises(
        ConfigurationError,
        match="admits none of the non-empty values the choice column",
    ):
        build_form_input_class(form_class, operation_kind=CREATE)


def test_multiple_choice_field_over_single_value_choice_column_is_refused() -> None:
    """A ``MultipleChoiceField`` writes a list, which no single-value choice column lists."""
    form_class = _book_status_form(forms.MultipleChoiceField(choices=_DESK_CHOICES))
    with pytest.raises(ConfigurationError, match="over the single-value choice column"):
        build_form_input_class(form_class, operation_kind=CREATE)


_CITY_PICKS = [("north", "North"), ("south", "South")]


@pytest.mark.parametrize(("operation_kind", "optional"), [(CREATE, False), (PARTIAL, True)])
def test_typed_multiple_choice_field_over_text_column_without_choices_is_typed_as_a_list(
    operation_kind: str,
    *,
    optional: bool,
) -> None:
    """A ``TypedMultipleChoiceField`` over ``Branch.city`` publishes ``[String!]``, not ``String``.

    The column lists no choices and stores one text value; the field reads a list, so the
    input types it as the same field off-column (``convert_form_field``): required on
    create, widened optional on update like every column-backed field.
    """
    form_class = _column_form(Branch, "city", forms.TypedMultipleChoiceField(choices=_CITY_PICKS))
    built, specs = build_form_input_class(form_class, operation_kind=operation_kind)
    city = _field_map(built)["city"]
    assert _is_optional(city) is optional
    inner = _inner_type(city)
    assert isinstance(inner, StrawberryList)
    assert inner.of_type is str
    assert [spec.kind for spec in specs] == [SCALAR]


def test_multiple_choice_field_over_json_column_keeps_the_column_type() -> None:
    """A ``MultipleChoiceField`` over a ``JSONField`` keeps the column's ``JSON`` type.

    A ``JSONField`` stores the list itself, so the field is no list over a single value.
    """
    picks = forms.MultipleChoiceField(choices=_CITY_PICKS, required=False)
    model = scalar_models.NullableScalarSpecimen
    built, _ = build_form_input_class(_column_form(model, "payload", picks), operation_kind=CREATE)
    json_built, _ = build_form_input_class(
        _column_form(model, "payload", forms.JSONField(required=False)),
        operation_kind=CREATE,
    )
    assert _field_map(built)["payload"].type == _field_map(json_built)["payload"].type


@pytest.mark.parametrize(
    (
        "model",
        "name",
        "operation_kind",
        "fields",
        "warned",
    ),
    [
        pytest.param(Branch, "city", PARTIAL, None, True, id="update"),
        pytest.param(Branch, "city", PARTIAL, ("name",), True, id="update-excluding-it"),
        pytest.param(Branch, "city", CREATE, None, False, id="create"),
        pytest.param(
            scalar_models.NullableScalarSpecimen,
            "payload",
            PARTIAL,
            None,
            False,
            id="json-column",
        ),
    ],
)
def test_update_build_warns_of_a_list_field_over_a_single_value_column(
    caplog: pytest.LogCaptureFixture,
    model: type[models.Model],
    name: str,
    operation_kind: str,
    fields: tuple[str, ...] | None,
    *,
    warned: bool,
) -> None:
    """An update's build logs one warning per list-writing field over a single-value column.

    The update binds every declared field, one its input leaves out included, and binds an
    omitted one from the form's initial, which the field refuses unless the form presents
    the stored value as a list. A create binds only what its input carries, and a
    ``JSONField`` stores the list itself, so neither warns.
    """
    extra = ("name",) if model is Branch else ()
    picks = forms.MultipleChoiceField(choices=_CITY_PICKS, required=False)
    form_class = _column_form(model, name, picks, fields=extra)
    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        build_form_input_class(form_class, operation_kind=operation_kind, fields=fields)
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "django_strawberry_framework"
    ]
    expected = (
        "Form KindForm field 'city' is a MultipleChoiceField over the single-value column "
        "Branch.city, which lists no choices: its input is a list, which the form must turn "
        "into the column's value (e.g. joined in clean_city). An update omitting the field "
        "binds the field's initial value, so the form must present the stored value as a list "
        "(e.g. split into self.initial['city'] in __init__), or that update fails validation."
    )
    assert messages == ([expected] if warned else [])


@pytest.mark.parametrize(
    (
        "operation_kind",
        "name",
        "field",
        "warned",
    ),
    [
        pytest.param(
            PARTIAL,
            "tags",
            lambda: forms.ChoiceField(choices=[("x", "X")]),
            True,
            id="update-choice",
        ),
        pytest.param(PARTIAL, "tags", forms.CharField, True, id="update-char"),
        pytest.param(PARTIAL, "counts", forms.IntegerField, True, id="update-integer"),
        pytest.param(
            CREATE,
            "tags",
            lambda: forms.ChoiceField(choices=[("x", "X")]),
            False,
            id="create",
        ),
        pytest.param(PARTIAL, "tags", forms.MultipleChoiceField, False, id="list-field"),
    ],
)
def test_update_build_warns_of_a_single_value_field_over_an_array_column(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    operation_kind: str,
    name: str,
    field: Callable[[], forms.Field],
    *,
    warned: bool,
) -> None:
    """An update's build logs one warning per single-value field over an ``ArrayField``.

    An omitted one binds from the form's initial, which a ``ModelForm`` reads off the row as
    the stored list, which the field refuses unless the form presents one value. A create
    binds only what its input carries, and a list-reading field reads the stored list.
    """
    patch_array_field(monkeypatch)
    declared = field()
    form_class = _column_form(_PlainArrays, name, declared)
    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        build_form_input_class(form_class, operation_kind=operation_kind)
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "django_strawberry_framework"
    ]
    expected = (
        f"Form KindForm field '{name}' is a {type(declared).__name__} over the list column "
        f"_PlainArrays.{name}: its input is a single value, which the form must turn into the "
        f"column's value (e.g. wrapped into a list in clean_{name}). An update omitting the "
        "field binds the field's initial value, so the form must present the stored value as "
        f"a single value (e.g. picked from the stored list into self.initial['{name}'] in "
        "__init__), or that update fails validation or writes a value made from the stored "
        "list."
    )
    assert messages == ([expected] if warned else [])


def test_choice_field_whose_valid_value_raises_propagates_its_exception() -> None:
    """A consumer ``valid_value`` that raises propagates its own exception from the build."""

    class BrokenChoiceField(forms.ChoiceField):
        @override
        def valid_value(self, value: object) -> bool:
            raise RuntimeError("broken")

    form_class = _book_status_form(BrokenChoiceField(choices=_DESK_CHOICES))
    with pytest.raises(RuntimeError, match="broken"):
        build_form_input_class(form_class, operation_kind=CREATE)


class _TaggedBook(models.Model):
    """An unmanaged owner of a ``tags`` array column whose ``base_field`` lists ``a`` / ``b``."""

    tags = FakeArrayField(models.CharField(max_length=5, choices=[("a", "A"), ("b", "B")]))

    class Meta:
        managed = False
        app_label = "test_forms_array_choices"


class _GroupedBook(models.Model):
    """An unmanaged owner of a ``status`` column declaring Django's grouped-choices form."""

    status: models.CharField[str | int | Combinable, str] = models.CharField(
        max_length=4,
        choices=[("Shelf", [("a", "A"), ("b", "B")]), ("Desk", [("c", "C")])],
    )

    class Meta:
        managed = False
        app_label = "test_forms_grouped_choices"


class _PickedShelfNote(models.Model):
    """An unmanaged owner of a ``shelf`` foreign key that declares ``choices``."""

    shelf: models.ForeignKey[library_models.Shelf | Combinable, library_models.Shelf] = (
        models.ForeignKey(
            library_models.Shelf,
            on_delete=models.CASCADE,
            choices=[(1, "First"), (2, "Second")],
        )
    )

    class Meta:
        managed = False
        app_label = "test_forms_relation_choices"


def test_choice_field_over_non_choice_column_keeps_column_type() -> None:
    """A choice field over a column without choices keeps the column's scalar.

    ``Book.title`` lists no choices, so there is no column value to narrow to: the field
    publishes the column's ``str`` and the form validates its own choices at request time.
    """
    form_class = type(
        "BookTitlePickForm",
        (forms.ModelForm,),
        {
            "title": forms.ChoiceField(choices=[("Dune", "Dune")]),
            "Meta": type("Meta", (), {"model": library_models.Book, "fields": ("title",)}),
        },
    )
    cre, _ = build_form_input_class(form_class, operation_kind=CREATE)
    assert _inner_type(_field_map(cre)["title"]) is str


def test_choice_field_over_relation_column_with_choices_keeps_relation_input() -> None:
    """A relation column declaring choices keeps its id input and relation kind.

    The decode routes a value by its spec ``kind``, so a choice field narrower than the
    foreign key's ``choices`` still publishes the ``shelfId`` relation input, never an enum
    of pk values under a scalar kind.
    """
    meta = type("Meta", (), {"model": _PickedShelfNote, "fields": ("shelf",)})
    shelf_field = forms.TypedChoiceField(choices=[(1, "First")], coerce=int)
    form_class = type("ShelfPickForm", (forms.ModelForm,), {"shelf": shelf_field, "Meta": meta})
    cre, specs = build_form_input_class(form_class, operation_kind=CREATE)
    assert list(_field_map(cre)) == ["shelf_id"]
    assert [spec.kind for spec in specs] == [RELATION_SINGLE]


def _list_enum_of(field: StrawberryField) -> type[Enum]:
    """Return the element enum class of a generated ``list[<enum>]`` input field."""
    outer = _inner_type(field)
    assert isinstance(outer, StrawberryList)
    element = outer.of_type
    assert isinstance(element, StrawberryEnumDefinition)
    enum_cls = element.wrapped_cls
    assert issubclass(enum_cls, Enum)
    return enum_cls


@pytest.mark.parametrize(
    ("tags_field", "members", "keeps_read_enum"),
    [
        pytest.param(
            lambda: forms.MultipleChoiceField(choices=[("a", "A")]),
            {"a": "a"},
            False,
            id="multiple-subset",
        ),
        pytest.param(
            lambda: forms.MultipleChoiceField(choices=[("a", "A"), ("b", "B"), ("c", "C")]),
            {"a": "a", "b": "b"},
            True,
            id="multiple-superset",
        ),
    ],
)
def test_array_choice_column_narrows_its_elements(
    monkeypatch: pytest.MonkeyPatch,
    tags_field: Callable[[], forms.Field],
    members: dict[str, object],
    *,
    keeps_read_enum: bool,
) -> None:
    """A ``MultipleChoiceField`` over an ``ArrayField`` narrows the ``base_field``'s values.

    Each element is checked against the values the ``base_field`` lists, so a subset publishes
    ``list[<Input><Field>Enum]`` of the admitted values; a superset keeps the column's ``list``
    of the element's read enum.
    """
    patch_array_field(monkeypatch)
    column = _TaggedBook._meta.get_field("tags")
    assert isinstance(column, FakeArrayField)
    meta = type("Meta", (), {"model": _TaggedBook, "fields": ("tags",)})
    form_class = type("TagsForm", (forms.ModelForm,), {"tags": tags_field(), "Meta": meta})
    cre, _ = build_form_input_class(form_class, operation_kind=CREATE)
    enum_cls = _list_enum_of(_field_map(cre)["tags"])
    assert _members(enum_cls) == members
    read_enum = converters.convert_choices_to_enum(column.base_field, "TaggedBookType")
    assert (enum_cls is read_enum) is keeps_read_enum
    if not keeps_read_enum:
        assert enum_cls.__name__ == "TagsFormInputTagsEnum"


@pytest.mark.parametrize(
    ("tags_choices", "members", "keeps_read_enum"),
    [
        pytest.param([("a", "A"), ("b", "B")], {"a": "a", "b": "b"}, True, id="every-value"),
        pytest.param([("a", "A")], {"a": "a"}, False, id="subset"),
    ],
)
@pytest.mark.parametrize(("operation_kind", "optional"), [(CREATE, False), (PARTIAL, True)])
def test_single_choice_field_over_array_choice_column_takes_one_element(
    monkeypatch: pytest.MonkeyPatch,
    tags_choices: list[tuple[str, str]],
    members: dict[str, object],
    operation_kind: str,
    *,
    keeps_read_enum: bool,
    optional: bool,
) -> None:
    """A single-value ``ChoiceField`` over an ``ArrayField`` publishes one element value.

    The field reads one value, which ``clean_<field>`` turns into the stored list, so its
    input is the element's read enum (the one the column's list carries), narrowed to the
    values the form's choices admit as the list case is; never a list.
    """
    patch_array_field(monkeypatch)
    column = _TaggedBook._meta.get_field("tags")
    assert isinstance(column, FakeArrayField)
    list_form = _column_form(_TaggedBook, "tags", forms.MultipleChoiceField(choices=tags_choices))
    list_enum = _list_enum_of(
        _field_map(build_form_input_class(list_form, operation_kind=CREATE)[0])["tags"],
    )
    form_class = _column_form(_TaggedBook, "tags", forms.ChoiceField(choices=tags_choices))
    built, specs = build_form_input_class(form_class, operation_kind=operation_kind)
    tags = _field_map(built)["tags"]
    assert _is_optional(tags) is optional
    element = _inner_type(tags)
    assert isinstance(element, StrawberryEnumDefinition)
    enum_cls = element.wrapped_cls
    assert issubclass(enum_cls, Enum)
    assert _members(enum_cls) == members
    assert (enum_cls is list_enum) is keeps_read_enum
    assert [spec.kind for spec in specs] == [SCALAR]


class _PlainArrays(models.Model):
    """An unmanaged owner of choiceless text and integer array columns."""

    tags = FakeArrayField(models.TextField())
    counts = FakeArrayField(models.IntegerField())

    class Meta:
        managed = False
        app_label = "test_forms_plain_arrays"


@pytest.mark.parametrize(
    ("name", "field", "scalar"),
    [
        pytest.param("tags", lambda: forms.ChoiceField(choices=[("x", "X")]), str, id="choice"),
        pytest.param(
            "counts",
            lambda: forms.TypedChoiceField(choices=[(1, "One")], coerce=int),
            str,
            id="typed-choice",
        ),
        pytest.param("tags", forms.CharField, str, id="char"),
        pytest.param("counts", forms.IntegerField, int, id="integer"),
        pytest.param("counts", forms.DecimalField, decimal.Decimal, id="decimal"),
    ],
)
@pytest.mark.parametrize(("operation_kind", "optional"), [(CREATE, False), (PARTIAL, True)])
def test_single_value_field_over_array_column_is_typed_as_the_form_reads_it(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    field: Callable[[], forms.Field],
    scalar: object,
    operation_kind: str,
    *,
    optional: bool,
) -> None:
    """A form field reading one value over an ``ArrayField`` publishes that value, not a list.

    The column lists no choices and stores a list, while the field reads a single value and
    ``clean_<field>`` wraps it, so the input types it as the same field off-column
    (``convert_form_field``): required on create, widened optional on update.
    """
    patch_array_field(monkeypatch)
    form_class = _column_form(_PlainArrays, name, field())
    built, specs = build_form_input_class(form_class, operation_kind=operation_kind)
    published = _field_map(built)[name]
    assert _is_optional(published) is optional
    assert _inner_type(published) is scalar
    assert [spec.kind for spec in specs] == [SCALAR]


class _ListReadingField(forms.Field):
    """A consumer field no registered scalar class covers, reading a list."""

    @override
    def to_python(self, value: object) -> object:
        return list_of(value)


@pytest.mark.parametrize(
    "field",
    [
        pytest.param(forms.Field, id="bare-field"),
        pytest.param(_ListReadingField, id="custom-field"),
    ],
)
@pytest.mark.parametrize(("operation_kind", "optional"), [(CREATE, False), (PARTIAL, True)])
def test_unregistered_field_over_array_column_keeps_the_column_list(
    monkeypatch: pytest.MonkeyPatch,
    field: Callable[[], forms.Field],
    operation_kind: str,
    *,
    optional: bool,
) -> None:
    """A bare or consumer ``forms.Field`` over an ``ArrayField`` keeps the column's ``list``.

    No registered scalar class states it reads one value (``form_field_reads_one_value``),
    so its ``to_python`` may read the column's list, and the column types its input.
    """
    patch_array_field(monkeypatch)
    built, _ = build_form_input_class(
        _column_form(_PlainArrays, "tags", field()),
        operation_kind=operation_kind,
    )
    tags = _field_map(built)["tags"]
    assert _is_optional(tags) is optional
    inner = _inner_type(tags)
    assert isinstance(inner, StrawberryList)
    assert inner.of_type is str


@functools.cache
def _pg_tags_model() -> type[models.Model]:
    """Declare the Postgres-tier owner of a real choiceless ``tags`` ``ArrayField``."""
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415 - needs the Postgres driver

    return type(
        "PgTags",
        (models.Model,),
        {
            "__module__": __name__,
            "tags": ArrayField(models.TextField()),
            "Meta": type("Meta", (), {"managed": False, "app_label": "test_forms_pg_tags"}),
        },
    )


def _pg_tag_list_field() -> forms.Field:
    """A consumer ``SimpleArrayField`` subclass over text elements."""
    from django.contrib.postgres.forms import SimpleArrayField  # noqa: PLC0415 - needs the Postgres driver

    class TagListField(SimpleArrayField):
        pass

    return TagListField(forms.CharField())


@pytest.mark.pg
@pytest.mark.parametrize(
    ("field", "scalar"),
    [
        pytest.param(None, None, id="default-simple-array"),
        pytest.param(_pg_tag_list_field, None, id="simple-array-subclass"),
        pytest.param(lambda: forms.MultipleChoiceField(choices=[("x", "X")]), None, id="multiple"),
        pytest.param(lambda: forms.ChoiceField(choices=[("x", "X")]), str, id="choice"),
    ],
)
def test_form_field_over_a_real_array_column_is_typed_by_the_shape_it_reads(
    field: Callable[[], forms.Field] | None,
    scalar: object,
) -> None:
    """Over a real ``ArrayField`` a list-reading field keeps the column's list; a scalar one not.

    The default ``ModelForm`` field is the ``SimpleArrayField`` ``ArrayField.formfield``
    builds, which ``convert_form_field`` types as the ``CharField`` it subclasses; it reads
    the column's list, so the input stays ``[String!]!``, as for a subclass of it and a
    ``MultipleChoiceField``. A ``ChoiceField`` reads one value.
    """
    model = _pg_tags_model()
    meta = type("Meta", (), {"model": model, "fields": ("tags",)})
    body: dict[str, object] = {"Meta": meta} if field is None else {"tags": field(), "Meta": meta}
    form_class = type("PgTagsForm", (forms.ModelForm,), body)
    built, _ = build_form_input_class(form_class, operation_kind=CREATE)
    tags = _field_map(built)["tags"]
    assert not _is_optional(tags)
    if scalar is None:
        assert isinstance(tags.type, StrawberryList)
        assert tags.type.of_type is str
    else:
        assert tags.type is scalar


@pytest.mark.parametrize(
    "field",
    [
        pytest.param(
            lambda: forms.MultipleChoiceField(choices=[("x", "X")]),
            id="multiple-choice",
        ),
        pytest.param(forms.JSONField, id="json"),
    ],
)
def test_list_reading_field_over_array_column_keeps_the_column_list(
    monkeypatch: pytest.MonkeyPatch,
    field: Callable[[], forms.Field],
) -> None:
    """A form field reading a list over an ``ArrayField`` keeps the column's ``list`` type."""
    patch_array_field(monkeypatch)
    built, _ = build_form_input_class(
        _column_form(_PlainArrays, "tags", field()),
        operation_kind=CREATE,
    )
    tags = _inner_type(_field_map(built)["tags"])
    assert isinstance(tags, StrawberryList)
    assert tags.of_type is str


@pytest.mark.parametrize(
    ("status_choices", "members"),
    [
        pytest.param([("a", "A"), ("c", "C")], {"a": "a", "c": "c"}, id="flat-subset"),
        pytest.param([("Desk", [("c", "C")])], {"c": "c"}, id="grouped-subset"),
        pytest.param([("a", "A"), ("b", "B"), ("c", "C")], None, id="every-value"),
    ],
)
def test_choice_field_over_grouped_column_binds_only_when_narrowed(
    status_choices: list[tuple[str, object]],
    members: dict[str, object] | None,
) -> None:
    """A narrowed field over a grouped column binds; one admitting every value is refused.

    The grouped column has no read enum; the values it lists are its groups flattened, so a
    field admitting a subset of them publishes its own generated enum, while a field admitting
    every value takes the column's type and meets the grouped-choices refusal.
    """
    meta = type("Meta", (), {"model": _GroupedBook, "fields": ("status",)})
    status_field = forms.ChoiceField(choices=status_choices)
    form_class = type("GroupedForm", (forms.ModelForm,), {"status": status_field, "Meta": meta})
    if members is None:
        with pytest.raises(ConfigurationError, match="grouped-choices form"):
            build_form_input_class(form_class, operation_kind=CREATE)
        return
    cre, _ = build_form_input_class(form_class, operation_kind=CREATE)
    assert _members(_enum_of(_field_map(cre)["status"])) == members


# ---------------------------------------------------------------------------
# Meta.fields / Meta.exclude narrowing + fail-loud
# ---------------------------------------------------------------------------


def test_fields_narrowing_omits_dropped_field() -> None:
    """``Meta.fields`` narrows the input to the named fields."""
    cre, _ = build_form_input_class(
        _item_model_form(),
        operation_kind=CREATE,
        fields=(
            "name",
            "category",
            "is_private",
            "confirm",
        ),
    )
    fields = _field_map(cre)
    assert "is_private" in fields
    cre2, _ = build_form_input_class(
        _item_model_form(),
        operation_kind=CREATE,
        exclude=("is_private",),
    )
    assert "is_private" not in _field_map(cre2)


def test_build_form_input_class_consumes_a_one_shot_narrowing_iterable_once() -> None:
    """Each build reads a one-shot ``fields`` / ``exclude`` iterable once, in full.

    Every call gets its own generator, and the create and partial shapes each narrow
    to exactly what that generator yielded: a second read inside one build would see
    an exhausted iterator and silently narrow to nothing (``fields``) or widen to the
    whole form (``exclude``).
    """
    form_cls = _item_model_form()
    names = (
        "name",
        "category",
        "is_private",
        "confirm",
    )
    create, _ = build_form_input_class(
        form_cls,
        operation_kind=CREATE,
        fields=(name for name in names),
    )
    partial, _ = build_form_input_class(
        form_cls,
        operation_kind=PARTIAL,
        fields=(name for name in names),
    )
    assert set(_field_map(create)) == {
        "name",
        "category_id",
        "is_private",
        "confirm",
    }
    assert set(_field_map(partial)) == {
        "name",
        "category_id",
        "is_private",
        "confirm",
    }

    create, _ = build_form_input_class(
        form_cls,
        operation_kind=CREATE,
        exclude=(name for name in ("is_private",)),
    )
    partial, _ = build_form_input_class(
        form_cls,
        operation_kind=PARTIAL,
        exclude=(name for name in ("is_private",)),
    )
    expected = {"name", "category_id", "confirm"}
    assert set(_field_map(create)) == expected
    assert set(_field_map(partial)) == expected


def test_meta_fields_rejects_bare_string() -> None:
    """A bare-string ``Meta.fields`` raises (it would iterate as characters)."""
    with pytest.raises(ConfigurationError, match="bare string"):
        resolve_effective_form_fields(_item_model_form(), fields="name")


def test_meta_fields_rejects_duplicates() -> None:
    """A duplicate field name raises."""
    with pytest.raises(ConfigurationError, match="duplicate field"):
        resolve_effective_form_fields(_item_model_form(), fields=("name", "name"))


def test_meta_fields_rejects_unknown_name() -> None:
    """An unknown name (a typo) raises naming the unknown field."""
    with pytest.raises(ConfigurationError, match="unknown form field"):
        resolve_effective_form_fields(_item_model_form(), fields=("emial",))


def test_meta_fields_and_exclude_mutually_exclusive() -> None:
    """Declaring both ``fields`` and ``exclude`` raises."""
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):
        resolve_effective_form_fields(
            _item_model_form(),
            fields=("name",),
            exclude=("category",),
        )


def test_empty_effective_field_set_raises() -> None:
    """An ``exclude`` dropping every field (empty effective set) raises."""
    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_form_fields(
            _item_model_form(),
            exclude=(
                "name",
                "category",
                "is_private",
                "confirm",
            ),
        )


def test_empty_fields_tuple_raises() -> None:
    """A ``fields = ()`` (empty effective set) raises."""
    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_form_fields(_item_model_form(), fields=())


def test_fieldless_form_raises() -> None:
    """A form with no declared fields raises (empty effective set)."""

    class EmptyForm(forms.Form):
        pass

    with pytest.raises(ConfigurationError, match="has no fields"):
        resolve_effective_form_fields(EmptyForm)


# ---------------------------------------------------------------------------
# Create-required-narrowing guard + waiver
# ---------------------------------------------------------------------------


def test_create_guard_rejects_dropping_required_field_via_fields() -> None:
    """A create ``Meta.fields`` dropping a required form field raises naming it."""
    with pytest.raises(ConfigurationError, match="confirm"):
        # ``confirm`` is required; narrowing to only ``name`` drops it.
        guard_create_required_fields(_item_model_form(), ("name", "category"))


def test_create_guard_rejects_dropping_required_field_via_exclude() -> None:
    """A create ``Meta.exclude`` dropping a required form field raises naming it."""
    effective = resolve_effective_form_fields(_item_model_form(), exclude=("confirm",))
    with pytest.raises(ConfigurationError, match="confirm"):
        guard_create_required_fields(_item_model_form(), tuple(effective))


def test_create_input_builds_without_the_guard() -> None:
    """The builder never runs the create guard: a waiving bind builds the narrowed input."""
    cre, _ = build_form_input_class(
        _item_model_form(),
        operation_kind=CREATE,
        fields=("name", "category"),
    )
    assert "confirm" not in _field_map(cre)


def test_partial_guard_rejects_dropping_required_column_less_field() -> None:
    """A partial (update) narrowing dropping a required COLUMN-LESS field raises naming it.

    ``confirm`` is a non-model required extra; on update it cannot be reconstructed
    from the row (``model_to_dict`` only returns columns), so dropping it would
    finalize a form that fails required-validation on every request. The effective
    set here keeps only the model-backed fields, dropping ``confirm``.
    """
    effective = resolve_effective_form_fields(_item_model_form(), exclude=("confirm",))
    with pytest.raises(ConfigurationError, match="confirm"):
        guard_partial_required_column_less_fields(_item_model_form(), effective)


def test_partial_guard_allows_dropping_model_backed_required_field() -> None:
    """Dropping a MODEL-BACKED required field on update does NOT raise (the scoping rule).

    The load-bearing column-less scoping: ``name`` is a required model column, so the
    partial path widens it optional and reconstructs it from the located row - dropping
    it from the input is harmless and must NOT trip the guard (a blanket reuse of the
    create guard would wrongly reject it). Only ``confirm`` (column-less) would.
    """
    # Drop the model-backed required ``name`` but keep the column-less required ``confirm``.
    effective = resolve_effective_form_fields(_item_model_form(), exclude=("name",))
    guard_partial_required_column_less_fields(_item_model_form(), effective)  # no raise


def test_exclude_naming_unknown_field_raises() -> None:
    """``Meta.exclude`` naming a field not on the form raises the narrowing fail-loud."""
    with pytest.raises(ConfigurationError, match="unknown form field"):
        build_form_input_class(
            _item_model_form(),
            operation_kind=CREATE,
            exclude=("definitely_not_a_field",),
        )


def test_excluded_unsupported_field_is_never_converted() -> None:
    """An unsupported custom field excluded via ``Meta.fields`` is never converted.

    Required-field discovery walks the FULL declared set, so it must decide
    requiredness as a pure attribute read (``form_field_required``) and never
    call ``convert_form_field`` on a field the mutation excluded - otherwise the
    converter's raising fallthrough for an unsupported type would crash the build
    for a field the consumer deliberately kept out of the schema.
    """

    class Unsupported(forms.Field):
        """A custom field type the converter has no mapping for."""

    class WeirdForm(forms.Form):
        name = forms.CharField()
        weird = Unsupported(required=False)

    cre, _ = build_form_input_class(WeirdForm, operation_kind=FORM, fields=("name",))
    assert set(_field_map(cre)) == {"name"}


# ---------------------------------------------------------------------------
# Shape identity, naming, dedupe, collision
# ---------------------------------------------------------------------------


def test_narrowed_shapes_get_distinct_names() -> None:
    """Two different narrowings of one form produce distinct shape-derived names."""
    form_cls = _item_model_form()
    full = tuple(get_form_fields(form_cls))
    n1 = form_input_type_name(form_cls, CREATE, ("name", "category"), full_field_names=full)
    n2 = form_input_type_name(form_cls, CREATE, ("name", "is_private"), full_field_names=full)
    assert n1 != n2
    # Two narrowings to the SAME effective set produce the SAME name (dedupe basis).
    n3 = form_input_type_name(form_cls, CREATE, ("category", "name"), full_field_names=full)
    assert n1 == n3


def test_canonical_name_for_full_shape() -> None:
    """The full effective shape takes the stable ``<FormClass>Input`` / ``PartialInput`` name."""
    form_cls = _item_model_form()
    full = tuple(get_form_fields(form_cls))
    assert (
        form_input_type_name(form_cls, CREATE, full, full_field_names=full) == "ItemModelFormInput"
    )
    assert (
        form_input_type_name(form_cls, PARTIAL, full, full_field_names=full)
        == "ItemModelFormPartialInput"
    )


def test_build_form_input_class_rejects_out_of_vocabulary_operation_kind() -> None:
    """``build_form_input_class`` rejects anything but CREATE / FORM / PARTIAL."""

    class ProbeForm(forms.Form):
        x = forms.CharField(required=False)

    with pytest.raises(ConfigurationError, match="out-of-vocabulary operation_kind 42"):
        # basedpyright: the non-str operation kind is the hostile input under test;
        # build_form_input_class types the parameter as str
        build_form_input_class(ProbeForm, operation_kind=42)  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError, match="out-of-vocabulary operation_kind 'update'"):
        build_form_input_class(ProbeForm, operation_kind="update")


def test_identical_shape_dedupes_via_ledger() -> None:
    """Materializing the same class twice under one name is a no-op (identical shapes dedupe)."""
    cre, _ = build_form_input_class(_item_model_form(), operation_kind=CREATE)
    materialize_form_input_class("ItemModelFormInput", cre)
    materialize_form_input_class("ItemModelFormInput", cre)  # idempotent, no raise
    assert module_binding(sys.modules[INPUTS_MODULE_PATH], "ItemModelFormInput") is cre


def test_distinct_shapes_colliding_on_one_name_raise() -> None:
    """Two DISTINCT classes under one name raise ``ConfigurationError`` (the collision raise)."""
    cre_a, _ = build_form_input_class(_item_model_form(), operation_kind=CREATE)

    class OtherForm(forms.Form):
        x = forms.CharField()

    cre_b, _ = build_form_input_class(OtherForm, operation_kind=FORM)
    materialize_form_input_class("CollidingInput", cre_a)
    with pytest.raises(ConfigurationError, match="DjangoFormMutation"):
        materialize_form_input_class("CollidingInput", cre_b)


def test_two_forms_sharing_name_always_collide() -> None:
    """Two DIFFERENT form classes with the same ``__name__`` always collide (never dedupe).

    Distinct ``form_class`` identities never dedupe (dedupe is only within one
    ``form_class`` + effective set), so two ``<__name__>Input`` from different
    classes raise even if their field shapes happen to match.
    """

    def _make_named_form() -> type[forms.Form]:
        class SharedName(forms.Form):
            a = forms.CharField()

        return SharedName

    form_a = _make_named_form()
    form_b = _make_named_form()
    assert form_a.__name__ == form_b.__name__ == "SharedName"
    assert form_a is not form_b

    cre_a, _ = build_form_input_class(form_a, operation_kind=FORM)
    cre_b, _ = build_form_input_class(form_b, operation_kind=FORM)
    materialize_form_input_class("SharedNameInput", cre_a)
    with pytest.raises(ConfigurationError, match="DjangoFormMutation"):
        materialize_form_input_class("SharedNameInput", cre_b)


# ---------------------------------------------------------------------------
# Module-global materialization
# ---------------------------------------------------------------------------


def test_materialized_input_is_module_global() -> None:
    """A materialized input class is a real global of ``forms.inputs`` (the lazy-ref contract)."""
    cre, _ = build_form_input_class(_item_model_form(), operation_kind=CREATE)
    materialize_form_input_class("ItemModelFormInput", cre)
    assert module_binding(sys.modules[INPUTS_MODULE_PATH], "ItemModelFormInput") is cre


# ---------------------------------------------------------------------------
# Reverse map - scalar identity + kind constants
# ---------------------------------------------------------------------------


def test_scalar_reverse_map_is_identity() -> None:
    """A plain scalar field's reverse map is identity (``name`` -> ``name``, kind scalar)."""
    _, specs = build_form_input_class(_item_model_form(), operation_kind=CREATE)
    name_spec = next(s for s in specs if s.target_name == "name")
    assert name_spec.input_attr == "name"
    assert name_spec.graphql_name == "name"
    assert name_spec.kind == SCALAR


# ---------------------------------------------------------------------------
# Fail-loud guards - input-attr collision + None-queryset relation
# ---------------------------------------------------------------------------


def test_relation_id_attr_collision_is_fail_loud() -> None:
    """A relation ``target`` colliding with a field named ``target_id`` raises.

    The relation (-> ``target_id``) and a field literally named ``target_id`` raise
    ``ConfigurationError`` rather than silently dropping one input.

    Both generate ``input_attr == "target_id"``; ``build_strawberry_input_class`` would
    write the second over the first in its annotations dict, losing a field. The package
    is fail-loud, so the assembled-attr collision is caught and named instead.
    """
    plain_target, _ = _make_non_relay_target()

    class CollidingForm(forms.Form):
        target = forms.ModelChoiceField(queryset=plain_target.objects.all())
        target_id = forms.CharField()

    with pytest.raises(ConfigurationError) as exc:
        build_form_input_class(CollidingForm, operation_kind=FORM)
    message = str(exc.value)
    assert "target_id" in message
    assert "'target'" in message
    assert "collide" in message


def test_camel_case_graphql_name_collision_is_fail_loud() -> None:
    """Two fields whose names default-camel-case to ONE GraphQL name raise.

    They raise rather than silently dropping one input.

    ``foo_bar`` and ``fooBar`` produce DISTINCT input attrs (so the input-attr guard
    passes) but the SAME ``graphql_name`` ``fooBar``; Strawberry would collapse the two
    onto one schema field. The graphql-name guard catches and names them, mirroring the
    read-type guard ``types/finalizer.py::_audit_field_surface``.
    """

    class CamelCollideForm(forms.Form):
        foo_bar = forms.IntegerField()
        fooBar = forms.IntegerField()  # noqa: N815 - intentional collision fixture

    with pytest.raises(ConfigurationError) as exc:
        build_form_input_class(CamelCollideForm, operation_kind=FORM)
    message = str(exc.value)
    assert "fooBar" in message
    assert "collide" in message


def test_extra_field_shadowing_reverse_relation_stays_scalar() -> None:
    """An extra ModelForm field reusing a reverse-accessor name stays on the scalar path.

    ``model._meta.get_field("items")`` resolves ``Category.items`` (a reverse
    ``ManyToOneRel``). Treating that as a backing column would emit ``itemsId`` /
    ``relation_single`` for a declared ``CharField`` extra. ``_model_column_for``
    must ignore ``ForeignObjectRel`` so the extra routes through ``convert_form_field``.
    """
    rev = Category._meta.get_field("items")
    assert rev.is_relation
    assert not rev.concrete

    class CategoryForm(forms.ModelForm[Category]):
        items = forms.CharField()

        class Meta:
            model = Category
            fields = ("name", "items")

    cre, specs = build_form_input_class(CategoryForm, operation_kind=CREATE)
    items_spec = next(s for s in specs if s.target_name == "items")
    assert items_spec.input_attr == "items"
    assert items_spec.graphql_name == "items"
    assert items_spec.kind == SCALAR
    assert items_spec.related_model is None
    fields = _field_map(cre)
    assert "items" in fields
    assert "items_id" not in fields
    assert not _is_optional(fields["items"])


def test_extra_field_shadowing_generic_foreign_key_stays_scalar() -> None:
    """An extra ModelForm field reusing a GenericForeignKey name stays on the scalar path.

    ``TaggedItem.content_object`` is a ``GenericForeignKey`` with no concrete DB column.
    ``_model_column_for`` must return ``None`` so an extra form field with the same name
    routes through ``convert_form_field`` rather than crashing on missing ``related_model``.
    """

    class TaggedItemForm(forms.ModelForm[TaggedItem]):
        content_object = forms.CharField()

        class Meta:
            model = TaggedItem
            fields = ("tag",)

    assert _model_column_for(TaggedItemForm, "content_object") is None

    cre, specs = build_form_input_class(TaggedItemForm, operation_kind=CREATE)
    co_spec = next(s for s in specs if s.target_name == "content_object")
    assert co_spec.input_attr == "content_object"
    assert co_spec.graphql_name == "contentObject"
    assert co_spec.kind == SCALAR
    assert co_spec.related_model is None
    fields = _field_map(cre)
    assert "content_object" in fields
    assert not _is_optional(fields["content_object"])


def test_extra_field_shadowing_generic_relation_stays_scalar() -> None:
    """An extra ModelForm field reusing a GenericRelation name stays on the scalar path.

    ``Branch.tags`` is a ``GenericRelation`` with no concrete DB column.
    ``_model_column_for`` must return ``None`` so an extra form field with the same name
    routes through ``convert_form_field`` as a scalar rather than misclassifying as a single relation.
    """

    class BranchForm(forms.ModelForm[Branch]):
        tags = forms.CharField()

        class Meta:
            model = Branch
            fields = ("name",)

    assert _model_column_for(BranchForm, "tags") is None

    cre, specs = build_form_input_class(BranchForm, operation_kind=CREATE)
    tags_spec = next(s for s in specs if s.target_name == "tags")
    assert tags_spec.input_attr == "tags"
    assert tags_spec.graphql_name == "tags"
    assert tags_spec.kind == SCALAR
    assert tags_spec.related_model is None
    fields = _field_map(cre)
    assert "tags" in fields
    assert "tags_id" not in fields


def test_guard_partial_required_column_less_fields_catches_dropped_gfk_extra() -> None:
    """guard_partial_required_column_less_fields catches dropped required GFK-shadowing extra fields."""

    class TaggedItemForm(forms.ModelForm[TaggedItem]):
        content_object = forms.CharField(required=True)

        class Meta:
            model = TaggedItem
            fields = ("tag",)

    effective = resolve_effective_form_fields(TaggedItemForm, exclude=("content_object",))
    with pytest.raises(ConfigurationError, match="content_object"):
        guard_partial_required_column_less_fields(TaggedItemForm, effective)


def test_digit_boundary_form_fields_survive_distinct_in_sdl() -> None:
    """``field_2`` / ``field2`` both appear on the generated form input (shared pin path).

    Package ``graphql_camel_name`` keeps them distinct; ``build_strawberry_input_class``
    pins every wire name so Strawberry's converter cannot collapse ``field_2`` onto
    ``field2``. Forms route through that shared builder - this locks the form flavor.
    """

    class DigitForm(forms.Form):
        field_2 = forms.IntegerField()
        field2 = forms.IntegerField()

    cre, specs = build_form_input_class(DigitForm, operation_kind=FORM)
    assert {(s.input_attr, s.graphql_name) for s in specs} == {
        ("field_2", "field_2"),
        ("field2", "field2"),
    }

    def _probe(inp: object) -> int:
        del inp  # Strawberry derives the argument whose SDL name the test reads; never runs
        return 1

    _probe.__annotations__ = {"inp": cre, "return": int}

    @strawberry.type
    class Query:
        probe: int = strawberry.field(resolver=_probe)

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    sdl = schema.as_str()
    block = sdl[sdl.index("input DigitFormInput") :]
    block = block[: block.index("}")]
    assert "field_2:" in block
    assert "field2:" in block


@pytest.mark.parametrize("to_field_name", [None, "name"])
def test_model_choice_field_with_none_queryset_is_fail_loud(to_field_name: str | None) -> None:
    """A model-less ``ModelChoiceField(queryset=None)`` raises a diagnosable error at schema build.

    The queryset-in-``__init__`` idiom raises ``ConfigurationError``, not a bare
    ``AttributeError``.

    Schema-time discovery reads ``base_fields`` without instantiating the form, so a
    ``queryset`` assigned in ``__init__`` is ``None`` here and the related model cannot be
    resolved; the guard names the form / field rather than failing on ``None.model``. A
    ``to_field_name`` names no target the key check could read, so it is this refusal too.
    """

    class LateQuerysetForm(forms.Form):
        target: forms.ModelChoiceField[Model] = forms.ModelChoiceField(
            queryset=None,
            to_field_name=to_field_name,
        )

    with pytest.raises(ConfigurationError) as exc:
        build_form_input_class(LateQuerysetForm, operation_kind=FORM)
    message = str(exc.value)
    assert "LateQuerysetForm" in message
    assert "'target'" in message
    assert "queryset is None" in message


def _make_empty_form() -> type[forms.Form]:
    """A plain field-less ``forms.Form`` for hostile-basis probes."""

    class EmptyForm(forms.Form):
        pass

    return EmptyForm


def test_honest_str_subclass_basis_name_still_builds() -> None:
    """An honest ``str`` subclass basis key passes the name guard and builds.

    The identifier/keyword guard interrogates each basis name; a well-behaved
    subclass inherits ``str.isidentifier`` and must keep building (the guard
    rejects only names that could never build an input).
    """

    class PlainSub(str):
        pass

    form_cls = _make_empty_form()
    normalized = normalize_form_field_basis(form_cls, {PlainSub("good"): forms.CharField()})
    assert list(normalized) == ["good"]
    cre, _ = build_form_input_class(form_cls, form_fields=normalized, operation_kind=FORM)
    field_names = {f.python_name for f in get_object_definition(cre, strict=True).fields}
    assert field_names == {"good"}


@pytest.mark.parametrize("raised", _HOSTILE_CLASS_ERRORS)
def test_basis_diagnostic_typed_for_hostile_class_value(raised: type[BaseException]) -> None:
    """A value whose ``__class__`` raises under ``isinstance`` is invalid, never raw.

    The per-value check classifies the value by its real class
    (``utils/truth.py::is_instance``), so a value whose ``__class__`` read raises is
    listed under invalid fields without that read ever running, instead of escaping
    ``_form_field_basis`` as the raw exception.
    """
    with pytest.raises(ConfigurationError) as exc:
        normalize_form_field_basis(_make_empty_form(), {"x": ClassReadRaises(raised)})
    assert str(exc.value) == (
        "DjangoFormMutation for EmptyForm get_form_fields() must return a mapping of string "
        "names to forms.Field instances; invalid names [], invalid fields ['x']."
    )


def test_basis_diagnostic_keeps_list_repr_for_benign_names() -> None:
    """Benign invalid names keep the classic ``['a', 'b']`` list-repr byte shape."""

    class ProbeForm(forms.Form):
        pass

    with pytest.raises(ConfigurationError) as exc:
        normalize_form_field_basis(
            ProbeForm,
            {"with space": forms.CharField(), "9lead": forms.CharField()},
        )
    assert "['with space', '9lead']" in str(exc.value)


def test_resolve_target_column_reverse_m2m_and_non_concrete_fallback() -> None:
    class FakeReverseM2M:
        is_relation = True
        many_to_many = True
        auto_created = True

    class FakeNonConcreteField:
        is_relation = False
        column = None

    def _get_field(name: str) -> object:
        if name == "reverse_m2m":
            return FakeReverseM2M()
        if name == "non_concrete":
            return FakeNonConcreteField()
        raise FieldDoesNotExist

    fake_model = SimpleNamespace(_meta=SimpleNamespace(get_field=_get_field))
    fake_form = type("FakeForm", (), {"_meta": SimpleNamespace(model=fake_model)})

    assert _model_column_for(_as_form_class(fake_form), "reverse_m2m") is None
    assert _model_column_for(_as_form_class(fake_form), "non_concrete") is None


def test_form_basis_content_identity_reraises_the_basis_typed_reject_verbatim() -> None:
    """A hostile basis reaching the cache-key projection keeps the build's OWN reject.

    ``_form_basis_content_identity`` resolves its basis through the same guarded
    ``_form_field_basis`` read the build uses, so a basis the build already rejects
    typed must surface as THAT typed ``ConfigurationError`` verbatim - never
    re-wrapped in the projection's own raw-read wording, never a raw escape from
    cache-key assembly.
    """

    class _ClobberedBasesForm(forms.Form):
        name = forms.CharField()

    # dict(42) raises TypeError inside the guard
    # basedpyright: the corrupt base_fields value is the hostile input under test; django-stubs
    # types the slot as a field mapping
    _ClobberedBasesForm.base_fields = 42  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(ConfigurationError) as excinfo:
        _form_basis_content_identity(_ClobberedBasesForm, None)

    assert (
        "get_form_fields() must return a mapping of field names to forms.Field instances."
        in str(excinfo.value)
    )
    # The passthrough arm re-raises the basis reject VERBATIM: the projection's own
    # raw-read wording must not appear.
    assert "reading the field basis" not in str(excinfo.value)


def test_form_basis_content_identity_propagates_a_raw_requiredness_read_failure() -> None:
    """A field's raising ``required`` read is consumer behaviour; it propagates unchanged.

    ``_form_field_basis`` validation only checks the field's real class, so a subclass
    whose ``required`` read raises passes validation and raises later inside the
    projection's per-field walk (``form_field_required`` reads ``field.required``); the
    consumer's own exception reaches the caller, never a wrapped one.
    """

    class _HostileRequiredField(forms.Field):
        armed = False

        @property
        @override
        def required(self) -> bool:
            # Django's ``Field.__init__`` both assigns and reads this slot; the read
            # turns hostile only AFTER construction (the projection reads it later).
            if type(self).armed:
                raise RuntimeError("hostile requiredness read")
            return self._required_slot

        @required.setter
        # basedpyright: the hostile shape under test, a ``required`` property whose read raises
        # once armed; the checker rejects any property overriding a base class attribute
        def required(self, value: bool) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
            self._required_slot = value

    class _PlainHostForm(forms.Form):
        name = forms.CharField()

    field = _HostileRequiredField()
    _HostileRequiredField.armed = True

    with pytest.raises(RuntimeError, match="hostile requiredness read"):
        _form_basis_content_identity(_PlainHostForm, {"confirm": field})


def test_basis_diagnostic_message_is_pinned() -> None:
    """The invalid-basis diagnostic names the form and each invalid entry."""
    form_cls = _make_empty_form()
    with pytest.raises(ConfigurationError) as exc_info:
        normalize_form_field_basis(form_cls, {"9lead": forms.CharField(), "ok": 3})
    assert str(exc_info.value) == (
        f"DjangoFormMutation for {form_cls.__name__} get_form_fields() must return "
        "a mapping of string names to forms.Field instances; invalid names "
        "['9lead'], invalid fields ['ok']."
    )


# ---------------------------------------------------------------------------
# require_readable_choice_keys: ``to_field_name`` must name one row of the target
# ---------------------------------------------------------------------------


class _KeyedRow(models.Model):
    """An unmanaged target whose text columns are unique alone, together, or conditionally.

    ``together_code`` is unique through a one-field ``unique_together`` entry and
    ``constraint_code`` through a ``UniqueConstraint`` over it alone: each names one row,
    as Django's fields.E311 reads them. ``pair_left`` is unique only with ``pair_right``
    and ``partial_code`` only where ``live`` is set, so neither names one row.
    """

    together_code: models.TextField[str | Combinable, str] = models.TextField()
    constraint_code: models.TextField[str | Combinable, str] = models.TextField()
    pair_left: models.TextField[str | Combinable, str] = models.TextField()
    pair_right: models.TextField[str | Combinable, str] = models.TextField()
    partial_code: models.TextField[str | Combinable, str] = models.TextField()
    live: models.BooleanField[bool | Combinable, bool] = models.BooleanField()

    class Meta:
        managed = False
        app_label = "test_forms_choice_keys"
        unique_together = (("together_code",), ("pair_left", "pair_right"))
        constraints = (
            models.UniqueConstraint(fields=("constraint_code",), name="keyed_row_constraint"),
            models.UniqueConstraint(
                fields=("partial_code",),
                condition=models.Q(live=True),
                name="keyed_row_partial",
            ),
        )


def _keyed_row_subclass(name: str, **meta: object) -> type[models.Model]:
    """A subclass of ``_KeyedRow`` declaring only ``meta``.

    The parent's uniqueness declarations stay on ``_KeyedRow._meta``.
    """
    meta_class = type("Meta", (), {"app_label": "test_forms_choice_keys", **meta})
    return require(
        type(name, (_KeyedRow,), {"__module__": __name__, "Meta": meta_class}),
        is_model_class,
    )


_KeyedRowProxy = _keyed_row_subclass("_KeyedRowProxy", proxy=True)
_KeyedRowChild = _keyed_row_subclass("_KeyedRowChild", managed=False)


def _loan_form(
    to_field_name: str | None,
    queryset: models.QuerySet[Book] | None = None,
) -> type[forms.ModelForm[library_models.Loan]]:
    """A ``Loan`` ``ModelForm`` whose declared ``book`` keys its choices by ``to_field_name``."""
    book_queryset = Book.objects.all() if queryset is None else queryset

    class LoanBookForm(forms.ModelForm[library_models.Loan]):
        book: forms.ModelChoiceField[Book] = forms.ModelChoiceField(
            queryset=book_queryset,
            to_field_name=to_field_name,
        )

        class Meta:
            model = library_models.Loan
            fields = ("book", "note")

    return LoanBookForm


def _plain_choice_form(
    queryset: models.QuerySet[models.Model],
    to_field_name: str,
) -> type[forms.Form]:
    """A plain ``Form`` (no model column) whose ``pick`` keys its choices by ``to_field_name``."""

    class PlainPickForm(forms.Form):
        pick: forms.ModelChoiceField[models.Model] = forms.ModelChoiceField(
            queryset=queryset,
            to_field_name=to_field_name,
        )

    return PlainPickForm


@pytest.mark.parametrize(
    "to_field_name",
    [
        None,
        "",
        "pk",
        "id",
    ],
)
def test_require_readable_choice_keys_admits_every_spelling_of_the_primary_key(
    to_field_name: str | None,
) -> None:
    """Unset, ``""``, ``pk`` and the primary key's own name key the choice by its pk."""
    require_readable_choice_keys(_loan_form(to_field_name))


@pytest.mark.parametrize(
    ("queryset", "to_field_name"),
    [
        pytest.param(Branch.objects.all(), "name", id="unique"),
        pytest.param(library_models.MembershipCard.objects.all(), "patron", id="unique-fk"),
        pytest.param(
            library_models.MembershipCard.objects.all(),
            "patron_id",
            id="unique-fk-attname",
        ),
        pytest.param(_KeyedRow.objects.all(), "together_code", id="unique-together-alone"),
        pytest.param(_KeyedRow.objects.all(), "constraint_code", id="unique-constraint-alone"),
        pytest.param(
            _KeyedRowProxy.objects.all(),
            "together_code",
            id="proxy-parent-unique-together-alone",
        ),
        pytest.param(
            _KeyedRowProxy.objects.all(),
            "constraint_code",
            id="proxy-parent-unique-constraint-alone",
        ),
        pytest.param(
            _KeyedRowChild.objects.all(),
            "constraint_code",
            id="multi-table-parent-unique-constraint-alone",
        ),
    ],
)
def test_require_readable_choice_keys_admits_a_column_unique_on_its_own(
    queryset: models.QuerySet[models.Model],
    to_field_name: str,
) -> None:
    """A concrete column of the target, by name or attname, that is unique alone is readable.

    A proxy or multi-table child target is unique through its parent's declarations, which
    Django keeps on the parent's ``_meta``.
    """
    require_readable_choice_keys(_plain_choice_form(queryset, to_field_name))


@pytest.mark.parametrize(
    ("to_field_name", "queryset"),
    [
        pytest.param("shelf__code", None, id="path"),
        pytest.param(
            "loan_count",
            Book.objects.annotate(loan_count=models.Count("loans")),
            id="annotation",
        ),
        pytest.param("nope", None, id="unknown"),
        pytest.param("loans", None, id="reverse-relation"),
        pytest.param("genres", None, id="many-to-many"),
        pytest.param("title", None, id="non-unique"),
        pytest.param("shelf", None, id="non-unique-fk"),
        pytest.param("shelf_id", None, id="non-unique-fk-attname"),
    ],
)
def test_require_readable_choice_keys_refuses_a_key_naming_no_one_row(
    to_field_name: str,
    queryset: models.QuerySet[Book] | None,
) -> None:
    """A path, an annotation, an unknown name, a relation or a shared column is refused.

    ``Book.title`` and ``Book.shelf`` are unique only together (a ``UniqueConstraint``
    over both), so two books may share either one.
    """
    form_class = _loan_form(to_field_name, queryset)

    with pytest.raises(ConfigurationError) as exc_info:
        require_readable_choice_keys(form_class)

    assert str(exc_info.value) == (
        f"DjangoFormMutation for LoanBookForm: field 'book' sets to_field_name="
        f"{to_field_name!r}, which is not a unique concrete field of Book. A relation id names "
        "its row by primary key and the form looks up the key read off that row, so "
        "to_field_name must be 'pk' or a concrete field of Book that is unique on its own "
        "(unique=True, a one-field unique_together, or a UniqueConstraint over it alone with "
        "no condition)."
    )


def test_require_readable_choice_keys_refuses_a_non_unique_key_on_a_text_keyed_m2m() -> None:
    """``Printing.bound_with`` keyed by ``isbn_10``, which two editions may share, is refused.

    A ``ModelMultipleChoiceField`` would link every edition carrying the key, so the build
    refuses the field the operation binds.
    """

    class PrintingForm(forms.ModelForm[library_models.Printing]):
        bound_with: forms.ModelMultipleChoiceField[library_models.Edition] = (
            forms.ModelMultipleChoiceField(
                queryset=library_models.Edition.objects.all(),
                to_field_name="isbn_10",
                required=False,
            )
        )

        class Meta:
            model = library_models.Printing
            fields = ("edition", "run_size", "bound_with")

    with pytest.raises(
        ConfigurationError,
        match="field 'bound_with' sets to_field_name='isbn_10', which is not a unique concrete "
        "field of Edition",
    ):
        require_readable_choice_keys(PrintingForm)


@pytest.mark.parametrize("target", [_KeyedRow, _KeyedRowProxy], ids=["concrete", "proxy"])
@pytest.mark.parametrize("to_field_name", ["pair_left", "partial_code"])
def test_require_readable_choice_keys_refuses_a_column_unique_only_with_others(
    target: type[models.Model],
    to_field_name: str,
) -> None:
    """A column unique only beside another, or only where a condition holds, is refused.

    Through a proxy too: the parent's declarations are read, and they do not make either
    column unique alone.
    """
    with pytest.raises(ConfigurationError, match="which is not a unique concrete field"):
        require_readable_choice_keys(_plain_choice_form(target.objects.all(), to_field_name))


def test_require_readable_choice_keys_reads_a_column_less_field_target_from_its_queryset() -> None:
    """A plain-form field has no model column; its queryset's model is the target."""
    require_readable_choice_keys(_plain_choice_form(Branch.objects.all(), "name"))
    with pytest.raises(ConfigurationError, match="field 'pick' sets to_field_name='shelves'"):
        require_readable_choice_keys(_plain_choice_form(Branch.objects.all(), "shelves"))


def test_update_input_refuses_an_unreadable_key_on_a_narrowed_out_field() -> None:
    """An update reads the full declared basis, so a field the input leaves out still fails.

    The update reconstruction rebinds every declared field, the narrowed-out ``book``
    included, through the same ``to_field_name`` read.
    """
    with pytest.raises(ConfigurationError, match="field 'book' sets to_field_name='shelf__code'"):
        _ = build_form_input_class(
            _loan_form("shelf__code"),
            operation_kind=PARTIAL,
            fields=("note",),
        )


def test_create_input_admits_an_unreadable_key_on_a_narrowed_out_field() -> None:
    """A create binds only its input's fields, so a narrowed-out field's key is never read."""
    _cls, specs = build_form_input_class(
        _loan_form("shelf__code"),
        operation_kind=FORM,
        fields=("note",),
    )

    assert [spec.target_name for spec in specs] == ["note"]


def test_create_input_refuses_an_unreadable_key_on_an_included_field() -> None:
    """A create that binds the field reads its key, so an unreadable one is refused at build."""
    with pytest.raises(ConfigurationError, match="field 'book' sets to_field_name='shelf__code'"):
        _ = build_form_input_class(_loan_form("shelf__code"), operation_kind=FORM)


@pytest.mark.parametrize(
    ("form_class", "expected"),
    [
        pytest.param(
            PatronProfileGenreForm,
            {"patron": None, "favorite_genre": "name"},
            id="declared-id-keyed",
        ),
        pytest.param(
            PatronProfileGenreNameForm,
            {"favorite_genre": "name"},
            id="generated-name-keyed",
        ),
    ],
)
def test_relation_spec_records_the_column_a_to_field_relation_stores(
    form_class: type[forms.ModelForm[library_models.PatronProfile]],
    expected: dict[str, str | None],
) -> None:
    """A relation into a ``to_field`` key records the stored column, whatever the field is keyed by.

    ``PatronProfile.favorite_genre`` stores ``Genre.name``, so its spec carries
    ``key_attname="name"`` under the declared id-keyed field and the generated name-keyed
    one alike; the pk-keyed ``patron`` records ``None``.
    """
    _cls, specs = build_form_input_class(form_class, operation_kind=CREATE)

    assert {spec.target_name: spec.key_attname for spec in specs if spec.related_model} == expected


def test_relation_spec_of_a_column_less_field_records_no_stored_column() -> None:
    """A plain-form relation stores nothing itself, so it records no ``key_attname``."""
    _cls, specs = build_form_input_class(
        _plain_choice_form(Branch.objects.all(), "name"),
        operation_kind=FORM,
    )

    [spec] = specs
    assert (spec.related_model, spec.key_attname) == (Branch, None)
