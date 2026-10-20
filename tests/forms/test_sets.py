"""``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases, ``Meta`` validation, and the bind.

Covers ``django_strawberry_framework/forms/sets.py``:

- the two-flavor ``Meta`` validation matrix at class creation (missing /
  wrong-type ``form_class``; a ``ModelForm`` on the plain base rejected naming
  ``DjangoModelFormMutation``; a non-``ModelForm`` on ``DjangoModelFormMutation``;
  a ``ModelForm`` with no resolvable model; ``operation = "delete"`` rejected on
  the ``ModelForm`` base; ANY ``operation`` rejected on the plain base;
  ``form_class`` accepted as a known key; ``fields`` + ``exclude`` both set;
  unknown key; the unknown-name narrowing routed through the input-generation machinery);
- plain-form input dedupe via the ``"form"`` sentinel;
- the shape-cache dedupe contract keyed on basis CONTENT identity
  (``forms/inputs.py::_form_basis_content_identity``): shared-hook siblings /
distinct hook functions / a default-vs-custom identical basis all dedupe onto
one input class, a stateful hook's requiredness or choice-narrowing drift stays
LOUD at the materialize ledger, and two distinct same-named form classes still collide;
- declaration registration (the ``ModelForm`` flavor in the ``DjangoMutation``
  registry, the plain flavor in the disjoint plain-form registry, abstract bases
  nowhere, post-finalize rejected);
- the phase-2.5 bind - both paths (the ``DjangoMutation``-ride for the
  ``ModelForm`` flavor through the ``build_input`` seam into ``forms.inputs``, and
  the ``bind_form_mutations()`` path for the plain flavor with the pinned
  ``{ ok errors }`` payload);
- the no-registered-primary-type finalize error for ``DjangoModelFormMutation``.

System-under-test is the bases / metaclasses / validation / bind, run against the
products ``Item`` / ``Category`` FK fixtures + package-local form fixtures (a
``ModelForm`` over ``Item``, a plain ``Form``, a ``ModelForm`` with no model).
Mirrors the ``tests/mutations/test_sets.py`` + ``tests/forms/test_inputs.py``
fixture posture. Request-time permission defaults live as ``submitPing``
(deny-by-default) and ``submitContact`` (empty ``permission_classes`` allow-any)
in ``test_products_api.py``; this file keeps class-creation validation,
registries, and bind/dedupe.
"""

from __future__ import annotations

import itertools
import re
import sys
from collections.abc import Callable, Iterator
from typing import NoReturn

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from django import forms
from django.db import models
from strawberry.types.base import get_object_definition
from typing_extensions import override

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoModelPermission,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms import (
    DjangoFormMutation as DjangoFormMutationFromForms,
)
from django_strawberry_framework.forms import (
    DjangoModelFormMutation as DjangoModelFormMutationFromForms,
)
from django_strawberry_framework.forms.inputs import (
    INPUTS_MODULE_PATH as FORMS_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.forms.inputs import (
    _materialized_names as form_materialized_names,
)
from django_strawberry_framework.forms.sets import (
    _cached_build_form_input,
    _default_mutation_get_form_fields,
    _form_kwargs_overridden,
    _form_mutation_registry,
    _form_shape_build_cache,
    clear_form_shape_build_cache,
    iter_form_mutations,
    register_form_mutation,
)
from django_strawberry_framework.mutations.inputs import CREATE
from django_strawberry_framework.mutations.inputs import (
    _materialized_names as mutation_materialized_names,
)
from django_strawberry_framework.mutations.permissions import DenyAll
from django_strawberry_framework.mutations.sets import iter_mutations
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils.typing import call_forwarded
from tests._idioms import ClassReadRaises, definition_raises, module_binding
from tests._info import unread_info


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry (now co-clearing the form-input ledger + the plain-form registry).

    ``registry.clear()`` is wired this slice to co-clear
    ``clear_form_input_namespace`` (the form-input + form-payload globals ledger)
    and ``clear_form_mutation_registry`` (the plain-form declaration registry), so
    a single ``registry.clear()`` resets every form-side ledger (and the mutation
    ledgers the ``ModelForm`` flavor rides). The products ``DjangoType``s register
    on import, so the clear is needed before/after.
    """
    registry.clear()
    yield
    registry.clear()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_form_sets__{next(_app_label_counter)}"


def _item_model_form() -> type[forms.ModelForm[product_models.Item]]:
    """A ``ModelForm`` over products ``Item`` (the ``ModelForm`` flavor fixture)."""

    class ItemModelForm(forms.ModelForm[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemModelForm


def _contact_form() -> type[forms.Form]:
    """A plain ``forms.Form`` (no model column) - the plain-flavor fixture."""

    class ContactForm(forms.Form):
        message = forms.CharField()

    return ContactForm


def _declare_products_primaries() -> tuple[type[DjangoType], type[DjangoType]]:
    """Register primary ``DjangoType``s for ``Item`` + ``Category`` (Relay-shaped)."""

    class CategoryT(DjangoType, strawberry.relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, strawberry.relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    return CategoryT, ItemT


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_bases_exported_from_package_root() -> None:
    """Both bases are re-exported from the package root + are in ``__all__``."""
    assert django_strawberry_framework.DjangoFormMutation is DjangoFormMutationFromForms
    assert django_strawberry_framework.DjangoModelFormMutation is DjangoModelFormMutationFromForms
    assert "DjangoFormMutation" in django_strawberry_framework.__all__
    assert "DjangoModelFormMutation" in django_strawberry_framework.__all__


# ---------------------------------------------------------------------------
# Meta validation matrix - missing / wrong-type form_class
# ---------------------------------------------------------------------------


def test_modelform_missing_form_class_raises() -> None:
    """A ``DjangoModelFormMutation`` with no ``Meta.form_class`` raises naming the key."""
    with pytest.raises(ConfigurationError, match="declares no form_class"):

        @definition_raises
        class CreateItem(DjangoModelFormMutation):
            class Meta:
                operation = "create"


def test_plain_form_missing_form_class_raises() -> None:
    """A ``DjangoFormMutation`` with no ``Meta.form_class`` raises naming the key."""
    with pytest.raises(ConfigurationError, match="declares no form_class"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                pass


def test_modelform_with_plain_form_raises() -> None:
    """A plain ``forms.Form`` on ``DjangoModelFormMutation`` raises (must be a ModelForm)."""
    form_cls = _contact_form()
    with pytest.raises(ConfigurationError, match=r"must be a forms\.ModelForm subclass"):

        @definition_raises
        class CreateThing(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"


def test_plain_base_with_modelform_raises_naming_modelform_base() -> None:
    """A ``ModelForm`` on the plain ``DjangoFormMutation`` base raises naming the ModelForm base.

    The ``issubclass(form_class, forms.ModelForm)``-first check: the
    targeted message names ``DjangoModelFormMutation`` as the correct base, not a
    generic "not a Form" message.
    """
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="use DjangoModelFormMutation"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = form_cls


def test_plain_base_form_class_not_a_form_raises() -> None:
    """A non-``Form`` value on the plain base raises the general type gate."""

    class NotAForm:
        pass

    with pytest.raises(ConfigurationError, match=r"must be a forms\.Form subclass"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = NotAForm


def test_modelform_with_no_resolvable_model_raises() -> None:
    """A ``ModelForm`` whose ``_meta.model`` is unset raises a clean config error, not AttributeError.

    A ``ModelForm`` declaring only ``fields`` with no ``Meta.model`` resolves no
    model; the form ``_validate_meta`` raises a ``ConfigurationError`` rather than
    letting ``form_class._meta.model`` surface a raw ``AttributeError``.
    """

    class NoModelForm(forms.ModelForm[models.Model]):
        name = forms.CharField()

    with pytest.raises(ConfigurationError, match="resolves no model"):

        @definition_raises
        class CreateThing(DjangoModelFormMutation):
            class Meta:
                form_class = NoModelForm
                operation = "create"


def test_modelform_non_model_meta_model_raises_at_class_creation() -> None:
    """A ``ModelForm`` whose ``_meta.model`` is not a Django model class fails at class creation.

    Django's ``ModelForm`` metaclass normally rejects this earlier; a post-creation
    swap still must not snapshot and crash at bind. Rides ``require_model_class``.
    """
    form_cls = _item_model_form()
    # basedpyright: the string model swapped onto the form's options is the hostile input under
    # test; django-stubs types the slot as the model class and the options as generic in it
    form_cls._meta.model = "Item"  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
    with pytest.raises(ConfigurationError, match="must be a Django model class"):

        @definition_raises
        class CreateThing(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"


def test_default_form_field_hook_rejects_a_class_without_form_metadata() -> None:
    """The default field-basis hook fails loudly when neither snapshot nor Meta names a form."""

    class MissingFormMetadata:
        pass

    with pytest.raises(ConfigurationError, match=r"cannot resolve Meta\.form_class"):
        # basedpyright: the class without form metadata is the hostile input under test;
        # _default_mutation_get_form_fields types the parameter as a form-mutation class
        _default_mutation_get_form_fields(MissingFormMetadata)  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# Meta validation matrix - operation rules
# ---------------------------------------------------------------------------


def test_modelform_delete_operation_rejected() -> None:
    """``operation = "delete"`` on ``DjangoModelFormMutation`` is rejected (no form delete)."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        @definition_raises
        class DeleteItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "delete"


def test_modelform_missing_operation_rejected() -> None:
    """A missing ``operation`` on the ``ModelForm`` base is rejected (``None`` invalid)."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        @definition_raises
        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls


@pytest.mark.parametrize(
    "operation",
    [
        "create",
        "update",
        "delete",
        "upsert",
        # An explicit ``operation = None`` is rejected by KEY PRESENCE, not value:
        # the fixed ``"form"`` sentinel accepts no copied ``Meta.operation`` key,
        # even one set to ``None``.
        None,
    ],
)
def test_plain_base_rejects_any_operation(operation: str | None) -> None:
    """The plain ``DjangoFormMutation`` base rejects ANY ``Meta.operation`` (Decision 10)."""
    form_cls = _contact_form()
    declared_operation = operation  # bind to a local: a class body cannot read the param name.
    with pytest.raises(ConfigurationError, match="operation is not supported"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = form_cls
                operation = declared_operation


@pytest.mark.parametrize(
    "operation",
    [
        "create",
        "update",
        "delete",
        None,
    ],
)
def test_plain_base_rejects_inherited_meta_operation(operation: str | None) -> None:
    """Decision 10 rejects ``Meta.operation`` inherited via a shared Meta parent too.

    ``form_class`` / ``permission_classes`` resolve through ``getattr`` (MRO-visible),
    so a shared ``Meta`` parent is a real consumer pattern. Presence of ``operation``
    must use the same visibility (``hasattr``), not ``vars(meta)`` own-keys-only -
    otherwise ``class Meta(Shared): pass`` with ``Shared.operation = ...`` silently
    accepts while ``Submit.Meta.operation`` still resolves to the inherited value.
    """
    form_cls = _contact_form()
    declared_operation = operation

    class SharedMeta:
        form_class = form_cls
        operation = declared_operation

    with pytest.raises(ConfigurationError, match="operation is not supported"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta(SharedMeta):
                pass


# ---------------------------------------------------------------------------
# Meta validation matrix - allowed keys + narrowing
# ---------------------------------------------------------------------------


def test_modelform_form_class_accepted_as_known_key() -> None:
    """A valid ``DjangoModelFormMutation`` declaration does not raise; the snapshot is stamped."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem._mutation_meta.form_class is form_cls
    assert CreateItem._mutation_meta.model is product_models.Item
    assert CreateItem._mutation_meta.operation == "create"


def test_plain_form_class_accepted_as_known_key() -> None:
    """A valid ``DjangoFormMutation`` declaration does not raise; the snapshot uses the sentinel."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    assert Submit._mutation_meta.form_class is form_cls
    assert Submit._mutation_meta.model is None
    assert Submit._mutation_meta.operation == "form"
    # An unset ``permission_classes`` defaults to deny-by-default for the plain
    # flavor - it cannot inherit the model-permission default.
    assert Submit._mutation_meta.permission_classes == (DenyAll,)


def test_plain_form_unset_permission_classes_defaults_to_deny_all() -> None:
    """A plain form with no ``permission_classes`` defaults to ``[DenyAll]``.

    A model-less form cannot inherit ``DjangoModelPermission`` (it reads a model
    the plain flavor never resolves), so the safe default is deny-by-default rather
    than a request-time crash.
    """
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    assert Submit._mutation_meta.permission_classes == (DenyAll,)


def test_plain_form_empty_permission_classes_is_allow_any_opt_out() -> None:
    """An explicit ``permission_classes = []`` on a plain form is preserved (allow-any opt-out)."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls
            permission_classes = []

    # The allow-any opt-out is stored as the immutable empty tuple:
    assert Submit._mutation_meta.permission_classes == ()


def test_modelform_unset_permission_classes_keeps_model_permission_default() -> None:
    """The ModelForm flavor still defaults to ``[DjangoModelPermission]``."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == (DjangoModelPermission,)


def test_modelform_unknown_meta_key_raises() -> None:
    """A stray ``Meta`` key on the ``ModelForm`` base raises the typo guard."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="unknown keys"):

        @definition_raises
        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"
                widget = "nope"


def test_plain_form_model_key_is_unknown() -> None:
    """``model`` is NOT an allowed plain-form key (it dropped from the form allowed set)."""
    form_cls = _contact_form()
    with pytest.raises(ConfigurationError, match="unknown keys"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = form_cls
                model = product_models.Item


def test_modelform_fields_and_exclude_both_raises() -> None:
    """Declaring both ``fields`` and ``exclude`` on the ``ModelForm`` base raises."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        @definition_raises
        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"
                fields = ("name",)
                exclude = ("category",)


def test_plain_form_fields_and_exclude_both_raises() -> None:
    """Declaring both ``fields`` and ``exclude`` on the plain base raises."""

    class MultiForm(forms.Form):
        a = forms.CharField()
        b = forms.CharField()

    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = MultiForm
                fields = ("a",)
                exclude = ("b",)


@pytest.mark.parametrize("narrowing", ["fields", "exclude"])
def test_plain_form_one_shot_narrowing_is_snapshotted_before_finalize(narrowing: str) -> None:
    """One-shot ``Meta.fields`` / ``Meta.exclude`` iterables survive class validation.

    Validation must normalize the declaration before the effective-field check consumes
    it. Otherwise a generator or iterator validates successfully at class creation but
    is exhausted by the phase-2.5 bind, which reports a false empty form input.
    """

    class TwoFieldForm(forms.Form):
        message = forms.CharField()
        subject = forms.CharField(required=False)

    declaration = iter(("message",) if narrowing == "fields" else ("subject",))

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = TwoFieldForm
            if narrowing == "fields":
                fields = declaration
            else:
                exclude = declaration
            permission_classes = []

    assert Submit._mutation_meta.fields == (("message",) if narrowing == "fields" else None)
    assert Submit._mutation_meta.exclude == (("subject",) if narrowing == "exclude" else None)
    finalize_django_types()
    assert Submit._input_class is not None


def test_plain_form_permission_iterable_error_propagates() -> None:
    """A permission iterable's own ``__iter__`` is consumer code: what it raises propagates."""

    class BrokenPermissions:
        def __iter__(self) -> Iterator[object]:
            raise RuntimeError("permission iterator exploded")

    with pytest.raises(RuntimeError, match="permission iterator exploded"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = _contact_form()
                permission_classes = BrokenPermissions()


def test_modelform_unknown_field_name_routes_through_slice1_narrowing() -> None:
    """An unknown ``Meta.fields`` name routes through the narrowing fail-loud."""
    form_cls = _item_model_form()
    with pytest.raises(ConfigurationError, match="unknown form field"):

        @definition_raises
        class CreateItem(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "create"
                fields = ("definitely_not_a_field",)


def _profile_model_form(
    *names: str,
) -> type[forms.ModelForm[library_models.PatronProfile]]:
    """A ``ModelForm`` over ``PatronProfile`` (keyed by its one-to-one ``patron``)."""

    class ProfileModelForm(forms.ModelForm[library_models.PatronProfile]):
        class Meta:
            model = library_models.PatronProfile
            fields = names

    return ProfileModelForm


def test_modelform_update_meta_fields_naming_the_primary_key_raises_at_class_creation() -> None:
    """An update ``Meta.fields`` naming the form's primary-key field is refused at class creation.

    The form publishes ``patron`` on create; the update input never carries it, since the
    mutation's ``id`` argument names the row. The same ``Meta.fields`` builds a create and
    an update ``Meta.exclude`` naming the key builds, stating what the update already does.
    """
    form_cls = _profile_model_form("patron", "address_2")

    class ProfileT(DjangoType):
        class Meta:
            model = library_models.PatronProfile
            fields = ("address_2",)
            primary = True

    class CreateProfile(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"
            fields = ("patron", "address_2")

    class UpdateProfileExcludingKey(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "update"
            exclude = ("patron",)

    assert CreateProfile._mutation_meta.fields == ("patron", "address_2")
    with pytest.raises(
        ConfigurationError,
        match=re.escape(
            "DjangoFormMutation for ProfileModelForm declares `fields` naming ['patron'], "
            "which write(s) the row's primary key.",
        ),
    ):

        @definition_raises
        class UpdateProfile(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "update"
                fields = ("patron", "address_2")

    assert registry.get(library_models.PatronProfile) is ProfileT
    finalize_django_types()
    # The excluded key is no update input, so the update keeps the canonical name.
    partial_name = "ProfileModelFormPartialInput"
    assert UpdateProfileExcludingKey.input_type_name(UpdateProfileExcludingKey._mutation_meta) == (
        partial_name
    )
    assert UpdateProfileExcludingKey._input_class is not None
    assert UpdateProfileExcludingKey._input_class.__name__ == partial_name


def test_modelform_update_over_only_the_primary_key_raises_at_class_creation() -> None:
    """A form whose only field is its primary key has no update input and is refused.

    The create over the same form builds and binds, its input carrying only the key: the
    bind builds the create input alone, never the update input the form has none of.
    """
    form_cls = _profile_model_form("patron")

    class ProfileT(DjangoType):
        class Meta:
            model = library_models.PatronProfile
            fields = ("address_2",)
            primary = True

    class CreateProfile(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"
            permission_classes = []

    with pytest.raises(
        ConfigurationError,
        match="DjangoFormMutation input for ProfileModelForm has no fields",
    ):

        @definition_raises
        class UpdateProfile(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = "update"

    assert registry.get(library_models.PatronProfile) is ProfileT
    finalize_django_types()
    assert CreateProfile._input_class is not None
    assert [
        field.python_name
        for field in get_object_definition(CreateProfile._input_class, strict=True).fields
    ] == ["patron_id"]


def test_cached_build_form_input_runs_required_guard_per_declaration() -> None:
    """A cached narrowed shape does NOT let a later declaration bypass the create-required guard.

    The per-shape build cache is keyed by ``(form_class, operation_kind, effective
    set)`` - NOT by ``guard_required``. So a WAIVING mutation
    (``guard_required=False``, having overridden ``get_form_kwargs`` / ``get_form``)
    that materializes a narrowed shape FIRST must not poison the cache for a later
    NON-waiving mutation over the same form + effective set: the guard is tied to
    each declaration, not to whichever class built the shape first. Pre-fix, the
    second call returned the cached value and silently skipped the guard.
    """

    class _RequiredExtraForm(forms.ModelForm[product_models.Item]):
        confirm = forms.CharField()  # required, no model column - dropped by the narrowing below

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    clear_form_shape_build_cache()
    # The waiving declaration narrows `confirm` away and builds without the guard.
    waived_cls, _specs = _cached_build_form_input(
        _RequiredExtraForm,
        operation_kind=CREATE,
        fields=("name", "category"),
        exclude=None,
        guard_required=False,
    )
    assert waived_cls is not None  # the waiver built + cached the narrowed shape

    # A later NON-waiving declaration over the SAME form + effective set must STILL
    # raise (the guard runs per-declaration, before the cache lookup), not silently
    # reuse the waived shape.
    with pytest.raises(ConfigurationError, match="confirm"):
        _cached_build_form_input(
            _RequiredExtraForm,
            operation_kind=CREATE,
            fields=("name", "category"),
            exclude=None,
            guard_required=True,
        )


@pytest.mark.parametrize(
    ("mutation_base", "form_factory"),
    [(DjangoModelFormMutation, _item_model_form), (DjangoFormMutation, _contact_form)],
    ids=["modelform", "plain_form"],
)
def test_get_form_only_override_trips_the_construction_hook_waiver(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
    form_factory: Callable[[], type[forms.BaseForm]],
) -> None:
    """Overriding ONLY ``get_form`` counts as a construction-hook override on both flavors.

    ``_form_kwargs_overridden`` tests BOTH construction hooks, and every other
    consumer in the trees overrides the finer ``get_form_kwargs`` - which
    short-circuits the check - so the coarser ``get_form`` is the operand that
    only ever decides for a mutation overriding it ALONE. Both flavors are driven
    because each detects against its own framework base
    (``DjangoModelFormMutation`` / ``DjangoFormMutation``), and the
    overrides-neither control in the same row pins that the detection is not
    simply always ``True``.
    """
    form_cls = form_factory()
    meta_body: dict[str, object] = {"form_class": form_cls}
    if mutation_base is DjangoModelFormMutation:
        meta_body["operation"] = "create"

    def get_form(
        self: DjangoFormMutation | DjangoModelFormMutation,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: models.Model | None = None,
    ) -> forms.BaseForm:
        return call_forwarded(
            form_cls,
            (),
            self.get_form_kwargs(info, data=data, files=files, instance=instance),
        )

    Overriding = type(
        "Overriding",
        (mutation_base,),
        {"Meta": type("Meta", (), dict(meta_body)), "get_form": get_form},
    )
    Inheriting = type(
        "Inheriting",
        (mutation_base,),
        {"Meta": type("Meta", (), dict(meta_body))},
    )
    assert issubclass(Overriding, mutation_base)
    assert issubclass(Inheriting, mutation_base)

    assert _form_kwargs_overridden(Overriding, mutation_base) is True
    assert _form_kwargs_overridden(Inheriting, mutation_base) is False


# ---------------------------------------------------------------------------
# permission_classes default
# ---------------------------------------------------------------------------


def test_modelform_permission_classes_default() -> None:
    """An unset ``permission_classes`` resolves to ``[DjangoModelPermission]`` (the ModelForm base)."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == (DjangoModelPermission,)


def test_plain_form_permission_classes_explicit_opt_out() -> None:
    """A plain form may opt out with an explicit ``[]`` (the AllowAny posture)."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls
            permission_classes = []

    assert Submit._mutation_meta.permission_classes == ()


def test_plain_form_rejects_model_permission_at_class_creation() -> None:
    """``DjangoModelPermission`` on a model-less plain form is rejected at class creation.

    ``DjangoModelPermission.has_permission`` reads the mutation's model via
    ``mutation._resolve_model(mutation.Meta)`` and maps the operation to an
    ``add`` / ``change`` / ``delete`` codename. A plain ``DjangoFormMutation`` is
    NOT a ``DjangoMutation`` subclass (it has no ``_resolve_model``) and carries the
    ``"form"`` operation sentinel, so the class would only surface the mismatch as a
    raw ``AttributeError`` at REQUEST time - the exact incompatibility ``DenyAll``
    documents and the default avoids. The plain-form ``_validate_meta`` rejects it at
    class creation instead (the package's fail-loud contract), naming the model-backed
    base and the two valid plain-form postures. A subclass of ``DjangoModelPermission``
    is rejected too (the ``issubclass`` guard).
    """
    form_cls = _contact_form()

    class CustomModelPermission(DjangoModelPermission):
        pass

    for offending in (DjangoModelPermission, CustomModelPermission):
        with pytest.raises(ConfigurationError, match="requires a model"):

            @definition_raises
            class Submit(DjangoFormMutation):
                class Meta:
                    form_class = form_cls
                    permission_classes = [offending]


# ---------------------------------------------------------------------------
# Declaration registration (disjoint ledgers)
# ---------------------------------------------------------------------------


def test_modelform_registers_in_mutation_registry() -> None:
    """A concrete ``DjangoModelFormMutation`` rides the ``DjangoMutation`` declaration registry."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem in iter_mutations()
    assert CreateItem not in iter_form_mutations()


def test_plain_form_registers_in_disjoint_form_registry() -> None:
    """A concrete ``DjangoFormMutation`` records in the disjoint plain-form registry only."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    assert Submit in iter_form_mutations()
    assert Submit not in iter_mutations()


def test_abstract_bases_register_nowhere() -> None:
    """The abstract ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases register nowhere."""
    assert DjangoModelFormMutation not in iter_mutations()
    assert DjangoFormMutation not in iter_form_mutations()


def test_plain_form_registration_is_idempotent() -> None:
    """Re-recording the same plain class (identity) does not double-register."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    register_form_mutation(Submit)
    assert _form_mutation_registry.count(Submit) == 1


def test_plain_form_late_declaration_after_finalize_raises() -> None:
    """Declaring a plain form after ``finalize_django_types()`` raises naming the flavor."""

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Item) is ItemType

    finalize_django_types()
    with pytest.raises(ConfigurationError, match=r"DjangoFormMutation .* after finalization"):

        @definition_raises
        class Submit(DjangoFormMutation):
            class Meta:
                form_class = _contact_form()


# ---------------------------------------------------------------------------
# Phase-2.5 bind - both paths
# ---------------------------------------------------------------------------


def test_modelform_bind_materializes_form_input_into_forms_namespace() -> None:
    """The ``ModelForm`` flavor binds via the ``DjangoMutation`` path through the ``build_input`` seam.

    The form-derived input materializes into ``forms.inputs`` (NOT
    ``mutations.inputs``), and the model-backed ``<Name>Payload`` materializes into
    ``mutations.inputs`` (the ``DjangoMutation`` payload path, with a ``node`` /
    ``result`` slot).
    """
    _declare_products_primaries()
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert form_materialized_names == {}
    finalize_django_types()

    forms_module = sys.modules[FORMS_INPUTS_MODULE_PATH]
    # The form-derived input lives in forms.inputs, NOT mutations.inputs.
    assert "ItemModelFormInput" in form_materialized_names
    assert "ItemModelFormInput" not in mutation_materialized_names
    assert CreateItem._input_class is form_materialized_names["ItemModelFormInput"]
    assert (
        module_binding(forms_module, "ItemModelFormInput")
        is form_materialized_names["ItemModelFormInput"]
    )

    # The payload is model-backed (rides the DjangoMutation payload path).
    assert "CreateItemPayload" in mutation_materialized_names
    assert CreateItem._payload_type_name == "CreateItemPayload"
    assert CreateItem._primary_type is not None
    payload = mutation_materialized_names["CreateItemPayload"]
    slots = {f.python_name for f in get_object_definition(payload, strict=True).fields}
    assert "errors" in slots
    assert "node" in slots  # Item is Relay-shaped -> node slot


def test_plain_form_bind_materializes_input_and_ok_errors_payload() -> None:
    """The plain flavor binds via ``bind_form_mutations()`` with a pinned ``{ ok errors }`` payload."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    finalize_django_types()

    # The form-derived input materialized.
    assert "ContactFormInput" in form_materialized_names
    assert Submit._input_class is form_materialized_names["ContactFormInput"]
    # The pinned model-less payload has EXACTLY ok + errors, no object slot.
    assert Submit._payload_type_name == "SubmitPayload"
    assert Submit._primary_type is None
    payload = mutation_materialized_names["SubmitPayload"]
    slots = {f.python_name for f in get_object_definition(payload, strict=True).fields}
    assert slots == {"ok", "errors"}


def test_plain_form_get_form_fields_hook_controls_input_basis() -> None:
    """The plain mutation hook may add a stable schema-time form field."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            fields = super().get_form_fields()
            fields["injected"] = forms.CharField(required=False)
            return fields

        class Meta:
            form_class = form_cls
            permission_classes = []

    finalize_django_types()

    assert Submit._input_class is not None
    slots = {
        field.python_name
        for field in get_object_definition(Submit._input_class, strict=True).fields
    }
    assert slots == {"message", "injected"}


def test_default_get_form_fields_uses_frozen_form_class_snapshot() -> None:
    """Changing ``Meta.form_class`` after declaration cannot drift the generated input."""

    class FormA(forms.Form):
        alpha = forms.CharField()

    class FormB(forms.Form):
        beta = forms.IntegerField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class: type[forms.Form] = FormA
            permission_classes = []

    Submit.Meta.form_class = FormB
    finalize_django_types()

    assert Submit._mutation_meta.form_class is FormA
    assert Submit._input_class is form_materialized_names["FormAInput"]
    assert {
        field.python_name
        for field in get_object_definition(Submit._input_class, strict=True).fields
    } == {"alpha"}
    bound = Submit().get_form(unread_info(), data={"alpha": "ok"}, files={})
    assert isinstance(bound, FormA)


def test_modelform_get_form_fields_hook_controls_input_basis() -> None:
    """The ModelForm mutation hook follows the same schema-time discovery contract."""
    _declare_products_primaries()
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            fields = super().get_form_fields()
            fields["injected"] = forms.CharField(required=False)
            return fields

        class Meta:
            form_class = form_cls
            operation = "create"

    finalize_django_types()

    assert CreateItem._input_class is not None
    slots = {
        field.python_name
        for field in get_object_definition(CreateItem._input_class, strict=True).fields
    }
    assert "injected" in slots


def test_get_form_fields_hook_basis_drives_required_guard() -> None:
    """Required fields from the hook cannot be narrowed away silently."""
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            fields = super().get_form_fields()
            fields["injected"] = forms.CharField(required=True)
            return fields

        class Meta:
            form_class = form_cls
            fields = ("message",)
            permission_classes = []

    assert Submit in iter_form_mutations()

    with pytest.raises(ConfigurationError, match="injected"):
        finalize_django_types()


@pytest.mark.parametrize("mutation_base", [DjangoFormMutation, DjangoModelFormMutation])
@pytest.mark.parametrize("bad_hook", [None, "not-callable"])
def test_non_callable_get_form_fields_is_configuration_error(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
    bad_hook: str | None,
) -> None:
    """A malformed hook declaration fails as typed configuration, not raw ``TypeError``."""
    form_cls = _contact_form() if mutation_base is DjangoFormMutation else _item_model_form()
    meta_attrs: dict[str, object] = (
        {"form_class": form_cls, "permission_classes": []}
        if mutation_base is DjangoFormMutation
        else {"form_class": form_cls, "operation": "create"}
    )
    with pytest.raises(ConfigurationError, match=r"get_form_fields.*callable classmethod"):
        type(
            "NonCallableHookMutation",
            (mutation_base,),
            {"get_form_fields": bad_hook, "Meta": type("Meta", (), meta_attrs)},
        )


@pytest.mark.parametrize("mutation_base", [DjangoFormMutation, DjangoModelFormMutation])
def test_raising_get_form_fields_body_propagates(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
) -> None:
    """A hook body raising mid-call propagates its own exception unchanged.

    The hook is consumer behaviour: both flavors' ``_validate_meta`` invoke it at
    class creation and whatever it raises reaches the caller as itself.
    """
    form_cls = _contact_form() if mutation_base is DjangoFormMutation else _item_model_form()
    meta_attrs: dict[str, object] = (
        {"form_class": form_cls, "permission_classes": []}
        if mutation_base is DjangoFormMutation
        else {"form_class": form_cls, "operation": "create"}
    )

    def get_exploding_form_fields(_cls: type) -> NoReturn:
        raise RuntimeError("hook exploded")

    with pytest.raises(RuntimeError, match="hook exploded"):
        type(
            "RaisingHookMutation",
            (mutation_base,),
            {
                "get_form_fields": classmethod(get_exploding_form_fields),
                "Meta": type("Meta", (), meta_attrs),
            },
        )


def _uncalled_hook_cls(cls: type) -> NoReturn:
    del cls
    raise AssertionError("the hook body must not run")


def _uncalled_hook_self_info(self: object, info: object) -> NoReturn:
    del self, info
    raise AssertionError("the hook body must not run")


def _uncalled_hook_self_default_info(self: object, info: object = None) -> NoReturn:
    del self, info
    raise AssertionError("the hook body must not run")


@pytest.mark.parametrize("mutation_base", [DjangoFormMutation, DjangoModelFormMutation])
@pytest.mark.parametrize(
    ("hook", "declared_as", "required"),
    [
        (_uncalled_hook_cls, "a plain function", "parameter 'cls'"),
        (staticmethod(_uncalled_hook_cls), "a staticmethod", "parameter 'cls'"),
        (_uncalled_hook_self_info, "a plain function", "parameters 'self', 'info'"),
        (_uncalled_hook_self_default_info, "a plain function", "parameter 'self'"),
    ],
)
def test_argument_requiring_get_form_fields_function_is_rejected_at_declaration(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
    hook: object,
    declared_as: str,
    required: str,
) -> None:
    """A function hook that needs a positional argument is rejected before it is ever called.

    The hook is read from the class, so only a classmethod receives an argument.
    The declaration check runs at class creation and names the fix; the hook body
    (which would raise ``AssertionError``) never runs.
    """
    form_cls = _contact_form() if mutation_base is DjangoFormMutation else _item_model_form()
    meta_attrs: dict[str, object] = (
        {"form_class": form_cls, "permission_classes": []}
        if mutation_base is DjangoFormMutation
        else {"form_class": form_cls, "operation": "create"}
    )

    with pytest.raises(ConfigurationError) as excinfo:
        type(
            "ArgumentRequiringHookMutation",
            (mutation_base,),
            {"get_form_fields": hook, "Meta": type("Meta", (), meta_attrs)},
        )
    assert str(excinfo.value) == (
        "ArgumentRequiringHookMutation.get_form_fields must be a callable classmethod "
        "returning a mapping of form field names to forms.Field instances; it is declared "
        f"as {declared_as} requiring the positional {required}, but the hook is called "
        "with no arguments. Decorate it with @classmethod."
    )
    assert excinfo.value.__cause__ is None


def test_get_form_fields_hook_raising_configuration_error_reraises_unchanged() -> None:
    """A hook raising ``ConfigurationError`` propagates its own typed error, not a wrap."""
    form_cls = _contact_form()

    def get_config_error_form_fields(_cls: type) -> NoReturn:
        raise ConfigurationError("the hook's own typed reject")

    with pytest.raises(ConfigurationError, match="hook's own typed reject") as excinfo:
        type(
            "ConfigRaisingHookMutation",
            (DjangoFormMutation,),
            {
                "get_form_fields": classmethod(get_config_error_form_fields),
                "Meta": type(
                    "Meta",
                    (),
                    {"form_class": form_cls, "permission_classes": []},
                ),
            },
        )
    assert "calling it raised" not in str(excinfo.value)


@pytest.mark.parametrize("mutation_base", [DjangoFormMutation, DjangoModelFormMutation])
@pytest.mark.parametrize(
    "hook_style",
    ["zero_arg_plain_function", "staticmethod_lambda"],
)
def test_zero_arg_and_staticmethod_get_form_fields_hooks_are_accepted(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
    hook_style: str,
) -> None:
    """A zero-arg plain function / ``@staticmethod`` hook still binds (permissive posture).

    Both are callable zero-arg, so the declaration check accepts them and the
    returned mapping drives the input; only a function requiring a positional
    argument is rejected.
    """
    _declare_products_primaries()
    form_cls = _contact_form() if mutation_base is DjangoFormMutation else _item_model_form()
    meta_attrs: dict[str, object] = (
        {"form_class": form_cls, "permission_classes": []}
        if mutation_base is DjangoFormMutation
        else {"form_class": form_cls, "operation": "create"}
    )
    hook = (
        (lambda: {"message": forms.CharField()})
        if hook_style == "zero_arg_plain_function"
        else staticmethod(lambda: {"message": forms.CharField()})
    )
    mutation_cls = type(
        "ZeroArgStyleHookMutation",
        (mutation_base,),
        {"get_form_fields": hook, "Meta": type("Meta", (), meta_attrs)},
    )
    finalize_django_types()
    assert issubclass(mutation_cls, (DjangoFormMutation, DjangoModelFormMutation))
    assert mutation_cls._input_class is not None
    assert {
        field.python_name
        for field in get_object_definition(mutation_cls._input_class, strict=True).fields
    } == {"message"}


@pytest.mark.parametrize("mutation_base", [DjangoFormMutation, DjangoModelFormMutation])
@pytest.mark.parametrize("bad_return", [None, ["message"], [("message",)]])
def test_malformed_get_form_fields_return_is_configuration_error(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
    bad_return: list[str] | list[tuple[str, ...]] | None,
) -> None:
    """Malformed hook returns fail through the typed configuration boundary for both bases."""
    form_cls = _contact_form() if mutation_base is DjangoFormMutation else _item_model_form()
    meta_attrs: dict[str, object] = (
        {"form_class": form_cls, "permission_classes": []}
        if mutation_base is DjangoFormMutation
        else {"form_class": form_cls, "operation": "create"}
    )

    def get_bad_form_fields(cls: type) -> object:
        del cls
        return bad_return

    with pytest.raises(ConfigurationError, match=r"get_form_fields\(.*mapping"):
        type(
            "MalformedHookMutation",
            (mutation_base,),
            {
                "get_form_fields": classmethod(get_bad_form_fields),
                "Meta": type("Meta", (), meta_attrs),
            },
        )


@pytest.mark.parametrize("mutation_base", [DjangoFormMutation, DjangoModelFormMutation])
@pytest.mark.parametrize("raised", [RuntimeError, TypeError, KeyboardInterrupt])
def test_hostile_class_hook_value_is_configuration_error(
    mutation_base: type[DjangoFormMutation | DjangoModelFormMutation],
    raised: type[BaseException],
) -> None:
    """A hook value whose ``__class__`` raises fails declaration typed for both bases.

    The hook's basis is validated at class creation; a value that cannot even be
    asked ``isinstance(value, forms.Field)`` is listed under invalid fields in the
    typed ``ConfigurationError`` instead of escaping the declaration raw.
    """
    form_cls = _contact_form() if mutation_base is DjangoFormMutation else _item_model_form()
    meta_attrs: dict[str, object] = (
        {"form_class": form_cls, "permission_classes": []}
        if mutation_base is DjangoFormMutation
        else {"form_class": form_cls, "operation": "create"}
    )

    def get_hostile_form_fields(cls: type) -> dict[str, object]:
        del cls
        return {"message": ClassReadRaises(raised)}

    with pytest.raises(ConfigurationError) as exc:
        type(
            "HostileClassHookMutation",
            (mutation_base,),
            {
                "get_form_fields": classmethod(get_hostile_form_fields),
                "Meta": type("Meta", (), meta_attrs),
            },
        )
    assert str(exc.value) == (
        f"DjangoFormMutation for {form_cls.__name__} get_form_fields() must return a mapping "
        "of string names to forms.Field instances; invalid names [], invalid fields "
        "['message']."
    )


def test_form_bind_is_retry_idempotent_after_fixable_later_phase_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plain-form re-finalize after a fixable post-bind failure succeeds, not a masked collision.

    The plain-form sibling of the mutation retry-idempotency guard. ``bind_form_mutations``
    materializes ``ContactFormInput`` (form ledger) and ``SubmitPayload`` (the
    mutation ledger, since the plain payload rides ``materialize_mutation_input_class``)
    before the later phases. Resetting both ledgers in ``finalize_django_types``
    before the bind sequence makes a recover-in-place re-finalize clean instead of
    raising a spurious distinct-class collision that masks the original error.
    """
    form_cls = _contact_form()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    def _boom() -> None:
        raise RuntimeError("injected post-bind finalization failure")

    monkeypatch.setattr("django_strawberry_framework.types.finalizer._bind_ordersets", _boom)
    with pytest.raises(RuntimeError, match="injected post-bind"):
        finalize_django_types()
    assert "ContactFormInput" in form_materialized_names
    assert "SubmitPayload" in mutation_materialized_names
    assert registry.is_finalized() is False

    monkeypatch.undo()
    finalize_django_types()

    assert registry.is_finalized() is True
    assert "ContactFormInput" in form_materialized_names
    assert Submit._input_class is form_materialized_names["ContactFormInput"]


def test_plain_form_input_dedupes_via_form_sentinel() -> None:
    """Two plain mutations over the SAME form + effective set dedupe to one input class.

    The ``"form"`` sentinel shape identity (Decision 7): both build the same
    ``<FormClass>Input`` shape, so the materialize ledger dedupes to one class
    object (idempotent re-materialize, no collision raise).
    """
    form_cls = _contact_form()

    class SubmitA(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    class SubmitB(DjangoFormMutation):
        class Meta:
            form_class = form_cls

    finalize_django_types()

    assert "ContactFormInput" in form_materialized_names
    # Both resolve to the SAME deduped input class object.
    assert SubmitA._input_class is SubmitB._input_class
    assert SubmitA._input_class is form_materialized_names["ContactFormInput"]


def test_modelform_no_registered_primary_type_raises_at_finalize() -> None:
    """A ``DjangoModelFormMutation`` whose model has no registered ``DjangoType`` raises at finalize.

    No primary type for the model means the mutation has no type to return - the
    reused ``_resolve_primary_type`` path raises the "no registered DjangoType" /
    "no type to return" error.
    """
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    assert CreateItem in iter_mutations()

    # No DjangoType declared for Item this build.
    with pytest.raises(ConfigurationError, match=r"no registered DjangoType|no type to return"):
        finalize_django_types()


def test_plain_form_default_perform_mutate_calls_form_save() -> None:
    """The default ``perform_mutate`` calls ``form.save()`` when the plain form defines one.

    A plain ``forms.Form`` has no ``save`` by default (the no-op path); a form that
    DOES define one has it invoked by the default ``perform_mutate`` hook.
    """
    called = {}

    class SavingForm(forms.Form):
        message = forms.CharField()

        def save(self) -> None:
            called["saved"] = True

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = SavingForm
            permission_classes = []

    Submit().perform_mutate(SavingForm(data={"message": "x"}), info=unread_info())
    assert called["saved"] is True


@pytest.mark.parametrize(
    "invalid_meta",
    [
        123,
        "string",
        [1, 2, 3],
        (1, 2),
        lambda: None,
    ],
)
def test_plain_form_mutation_rejects_non_class_meta(invalid_meta: object) -> None:
    """A non-class Meta on DjangoFormMutation raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match=r"BadMeta\.Meta must be a class; got "):

        @definition_raises
        class BadMeta(DjangoFormMutation):
            Meta = invalid_meta


@pytest.mark.parametrize(
    "invalid_meta",
    [
        123,
        "string",
        [1, 2, 3],
        (1, 2),
        lambda: None,
    ],
)
def test_modelform_mutation_rejects_non_class_meta(invalid_meta: object) -> None:
    """A non-class Meta on DjangoModelFormMutation raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match=r"BadModelMeta\.Meta must be a class; got "):

        @definition_raises
        class BadModelMeta(DjangoModelFormMutation):
            # basedpyright: the non-class Meta is the hostile input under test; DjangoMutation
            # declares Meta as a class
            Meta = invalid_meta  # pyright: ignore[reportAssignmentType]


@pytest.mark.parametrize(
    "invalid_op",
    [
        [],
        {},
        {"a": 1},
        set[object](),
        123,
        True,
        None,
    ],
)
def test_modelform_mutation_rejects_unhashable_and_non_string_operation(
    invalid_op: object,
) -> None:
    """An unhashable or non-string operation on DjangoModelFormMutation raises ConfigurationError."""
    form_cls = _item_model_form()

    with pytest.raises(
        ConfigurationError,
        match=r"Meta\.operation must be one of \['create', 'update'\]; got ",
    ):

        @definition_raises
        class BadOp(DjangoModelFormMutation):
            class Meta:
                form_class = form_cls
                operation = invalid_op


def test_input_type_name_seams() -> None:
    """Both form bases expose input_type_name deriving the canonical input class name."""
    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "update"

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = _contact_form()
            permission_classes = []

    assert CreateItem.input_type_name(CreateItem._mutation_meta) == "ItemModelFormInput"
    assert UpdateItem.input_type_name(UpdateItem._mutation_meta) == "ItemModelFormPartialInput"
    assert Submit.input_type_name(Submit._mutation_meta) == "ContactFormInput"


def test_plain_form_check_permission_seam() -> None:
    """DjangoFormMutation.check_permission runs the write-auth permission walk."""

    class AllowMutation(DjangoFormMutation):
        class Meta:
            form_class = _contact_form()
            permission_classes = []

    assert AllowMutation().check_permission(unread_info(), operation="form", data={}) is True

    class DenyMutation(DjangoFormMutation):
        class Meta:
            form_class = _contact_form()
            permission_classes = [DenyAll]

    assert DenyMutation().check_permission(unread_info(), operation="form", data={}) is False


def test_cached_build_form_input_partial_column_less_guard() -> None:
    """PARTIAL build path executes guard_partial_required_column_less_fields and builds partial."""

    class ExtraRequiredForm(forms.ModelForm[product_models.Item]):
        confirm = forms.CharField(required=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    with pytest.raises(ConfigurationError, match="confirm"):
        _cached_build_form_input(
            ExtraRequiredForm,
            operation_kind="partial",
            fields=("name", "category"),
            exclude=None,
            guard_required=True,
        )

    input_cls, field_specs = _cached_build_form_input(
        _item_model_form(),
        operation_kind="partial",
        fields=("name", "category"),
        exclude=None,
        guard_required=True,
    )
    assert input_cls is not None
    assert len(field_specs) == 2


def test_form_shape_build_cache_clears_via_registry_and_direct_clear() -> None:
    """The form shape cache co-clears on ``registry.clear()`` and the direct clear.

    The form twin of the model flavor's
    ``test_mutation_shape_build_cache_clears_via_registry_and_direct_clear``:
    ``_form_shape_build_cache`` is a per-pass build cache, so a stale entry from a
    prior (failed or re-run) finalize must never leak across a reset - direct
    ``clear_form_shape_build_cache`` and ``registry.clear()`` both empty the same
    dict (the ``forms.shape_cache`` subsystem clear).
    """
    probe_key = (
        forms.Form,
        "form",
        frozenset({"message"}),
        (),
    )
    _form_shape_build_cache[probe_key] = (object, [])
    assert probe_key in _form_shape_build_cache

    clear_form_shape_build_cache()
    assert _form_shape_build_cache == {}

    _form_shape_build_cache[probe_key] = (object, [])
    registry.clear()
    assert _form_shape_build_cache == {}


# ---------------------------------------------------------------------------
# Shape-cache dedupe keys on basis CONTENT identity
# (``forms/inputs.py::_form_basis_content_identity`` - the 4th cache-key
# component ``_cached_build_form_input`` consults)
# ---------------------------------------------------------------------------


def test_shared_hook_intermediate_base_siblings_dedupe() -> None:
    """Two siblings inheriting ONE custom hook over one form dedupe to one input class.

    The shape-cache key carries the basis CONTENT, never the concrete mutation
    class: the hook lives on the intermediate base, both siblings produce
    identical bases, so both land on one cache entry and the materialize ledger
    sees one class (no spurious distinct-class collision).
    """
    form_cls = _contact_form()

    class BaseSubmit(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            fields = dict(form_cls.base_fields)
            fields["injected"] = forms.CharField(required=False)
            return fields

    class SiblingA(BaseSubmit):
        class Meta:
            form_class = form_cls
            permission_classes = []

    class SiblingB(BaseSubmit):
        class Meta:
            form_class = form_cls
            permission_classes = []

    finalize_django_types()

    assert SiblingA._input_class is SiblingB._input_class
    assert SiblingA._input_class is not None
    slots = {
        field.python_name
        for field in get_object_definition(SiblingA._input_class, strict=True).fields
    }
    assert slots == {"message", "injected"}


def test_modelform_shared_hook_siblings_dedupe() -> None:
    """The shared-hook dedupe contract holds on the ModelForm flavor too."""
    _declare_products_primaries()
    form_cls = _item_model_form()

    class BaseCreateItem(DjangoModelFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            return dict(form_cls.base_fields)

    class CreateA(BaseCreateItem):
        class Meta:
            form_class = form_cls
            operation = "create"

    class CreateB(BaseCreateItem):
        class Meta:
            form_class = form_cls
            operation = "create"

    finalize_django_types()

    assert CreateA._input_class is CreateB._input_class
    assert CreateA._input_class is form_materialized_names["ItemModelFormInput"]


def test_distinct_hook_functions_identical_bases_dedupe() -> None:
    """Two mutations with their OWN hook functions returning identical bases dedupe.

    Hook-function identity is not the quantity - the returned basis content is:
    two different hook functions over one form producing the same
    ``(name, type, requiredness, related model)`` tuples share one cache entry.
    """
    form_cls = _contact_form()

    class TwinA(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            return dict(form_cls.base_fields)

        class Meta:
            form_class = form_cls
            permission_classes = []

    class TwinB(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            return dict(form_cls.base_fields)

        class Meta:
            form_class = form_cls
            permission_classes = []

    finalize_django_types()

    assert TwinA._input_class is TwinB._input_class
    assert TwinA._input_class is form_materialized_names["ContactFormInput"]


def test_default_hook_and_custom_hook_same_basis_dedupe() -> None:
    """A default-hook mutation and a custom hook returning exactly ``base_fields`` dedupe.

    The default hook reads ``base_fields``; a custom hook handing back exactly
    that mapping contributes the same content, so the two mutations reuse one
    built class instead of colliding on the ledger.
    """
    form_cls = _contact_form()

    class DefaultHook(DjangoFormMutation):
        class Meta:
            form_class = form_cls
            permission_classes = []

    class CustomSameBasis(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            return dict(form_cls.base_fields)

        class Meta:
            form_class = form_cls
            permission_classes = []

    finalize_django_types()

    assert DefaultHook._input_class is CustomSameBasis._input_class
    assert DefaultHook._input_class is form_materialized_names["ContactFormInput"]


def test_stateful_shared_hook_requiredness_drift_is_loud() -> None:
    """A shared hook returning per-class requiredness lands on the LOUD collision.

    Same effective name-set, different content: the basis content identity
    differs, each sibling builds its own class, and the materialize ledger
    rejects the second distinct class under one name - never a silent share of
    a wrong shape.
    """

    class TwoFieldForm(forms.Form):
        message = forms.CharField()
        topic = forms.CharField()

    class StatefulBase(DjangoFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            fields = dict(TwoFieldForm.base_fields)
            fields["injected"] = forms.CharField(required=cls.__name__ == "DriftA")
            return fields

    class DriftA(StatefulBase):
        class Meta:
            form_class = TwoFieldForm
            permission_classes = []

    assert DriftA in iter_form_mutations()

    class DriftB(StatefulBase):
        class Meta:
            form_class = TwoFieldForm
            permission_classes = []

    assert DriftB in iter_form_mutations()

    with pytest.raises(ConfigurationError, match="materialized by two distinct"):
        finalize_django_types()


def test_stateful_shared_hook_choice_narrowing_drift_is_loud() -> None:
    """A shared hook narrowing a choice field differently per class lands on the LOUD collision.

    Field type and requiredness agree, so only the column values each sibling's
    ``circulation_status`` admits tell the two bases apart: each builds its own
    generated enum, and the materialize ledger rejects the second distinct class under
    one name - never one sibling silently publishing the other's members.
    """

    class BookT(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("id", "circulation_status")
            primary = True

    class RepairDeskForm(forms.ModelForm[library_models.Book]):
        class Meta:
            model = library_models.Book
            fields = ("circulation_status",)

    class StatefulBase(DjangoModelFormMutation):
        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            choices = [("available", "Available"), ("repair", "Repair")]
            if cls.__name__ == "DriftB":
                choices = choices[:1]
            fields: dict[str, forms.Field] = {
                "circulation_status": forms.ChoiceField(choices=choices),
            }
            return fields

    class DriftA(StatefulBase):
        class Meta:
            form_class = RepairDeskForm
            operation = "create"

    class DriftB(StatefulBase):
        class Meta:
            form_class = RepairDeskForm
            operation = "create"

    assert registry.get(library_models.Book) is BookT
    assert {DriftA, DriftB} <= set(iter_mutations())
    with pytest.raises(ConfigurationError, match="materialized by two distinct"):
        finalize_django_types()


def test_excluded_choice_field_admitting_no_column_value_still_binds() -> None:
    """An excluded field never refuses the build, though the shape identity reads it.

    ``circulation_status`` admits none of the non-empty values its column lists, which refuses
    an emitted field; the shape identity walks the whole hook basis, excluded fields included, so the
    refusal must stay out of it, and the mutation binds without the field.
    """

    class BookT(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class LostShelfForm(forms.ModelForm[library_models.Book]):
        circulation_status = forms.ChoiceField(choices=[("lost", "Lost")], required=False)

        class Meta:
            model = library_models.Book
            fields = ("title", "circulation_status")

    class RetitleBook(DjangoModelFormMutation):
        class Meta:
            form_class = LostShelfForm
            operation = "update"
            exclude = ("circulation_status",)

    finalize_django_types()

    assert registry.get(library_models.Book) is BookT
    assert RetitleBook._input_class is not None
    slots = {
        field.python_name
        for field in get_object_definition(RetitleBook._input_class, strict=True).fields
    }
    assert slots == {"title"}


def test_two_distinct_form_classes_sharing_name_still_collide() -> None:
    """Two DIFFERENT form classes with one ``__name__`` can never dedupe (documented).

    ``form_class`` identity stays the first cache-key component, so distinct
    same-named forms build separately and the ledger keeps rejecting the second
    class under the shared name.
    """

    def make_form() -> type[forms.Form]:
        class ContactForm(forms.Form):
            message = forms.CharField()

        return ContactForm

    class FormA(DjangoFormMutation):
        class Meta:
            form_class = make_form()
            permission_classes = []

    assert FormA in iter_form_mutations()

    class FormB(DjangoFormMutation):
        class Meta:
            form_class = make_form()
            permission_classes = []

    assert FormB in iter_form_mutations()

    with pytest.raises(ConfigurationError, match="materialized by two distinct"):
        finalize_django_types()


def test_non_callable_get_form_fields_hook_message_is_pinned() -> None:
    """A non-callable hook is rejected typed, naming the mutation class."""
    with pytest.raises(ConfigurationError) as exc_info:
        type(
            "NonCallableHookMutation",
            (DjangoFormMutation,),
            {
                "get_form_fields": 42,
                "Meta": type(
                    "Meta",
                    (),
                    {"form_class": _contact_form(), "permission_classes": []},
                ),
            },
        )
    assert str(exc_info.value) == (
        "NonCallableHookMutation.get_form_fields must be a callable classmethod "
        "returning a mapping of form field names to forms.Field instances."
    )
