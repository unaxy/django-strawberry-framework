"""``DjangoMutation`` base, ``Meta`` validation, registration, and the phase-2.5 bind.

Covers the spec-036 surface (``django_strawberry_framework/mutations/sets.py``):

- the ``Meta`` validation matrix at class creation (unknown key; no-resolvable-model
  via ``_resolve_model``; bad / missing ``operation``; ``fields`` + ``exclude``
  both supplied; ``input_class`` not a ``@strawberry.input`` type; the
  diverging-field-name rejection);
- ``permission_classes`` defaulting to ``[DjangoModelPermission]`` (and an explicit
  override honored);
- the ``_resolve_model`` overridable seam;
- declaration registration (concrete registered, abstract base not, post-finalize
  rejected);
- the phase-2.5 bind - the finalize-time materialize trigger:
  generated ``<Model>Input`` / ``<Model>PartialInput`` / ``<Name>Payload`` become
  module globals of ``mutations.inputs``, identical shapes dedupe, distinct shapes
  colliding on one generated name raise ``ConfigurationError``, and the
  ``registry.clear()`` co-clear resets both the input/payload ledger and the
  declaration registry;
- the no-registered-primary-type finalize error (zero-type vs ambiguous phrasings);
- the namespace-isolation contract (a mutation ``Meta`` key is not a ``DjangoType``
  ``Meta`` key, Decision 12).

Metaclass / validation / bind. The composed schema's bound mutations are live
in ``examples/fakeshop/test_query/test_products_api.py`` and
``examples/fakeshop/test_query/test_library_api.py``; a request cannot observe
``ConfigurationError`` at class creation, ledger dedupe, or post-finalize
registration refusal.
"""

from __future__ import annotations

import importlib
import re
import sys
from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalar_models
from django.db import models
from django.db.models import Model
from django.utils.translation import gettext_lazy
from strawberry import relay
from strawberry.types.base import StrawberryObjectDefinition, get_object_definition
from typing_extensions import override

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoModelPermission,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.sets import (
    DjangoFormMutationMetaclass,
)
from django_strawberry_framework.mutations import (
    DjangoModelPermission as DjangoModelPermissionFromPackage,
)
from django_strawberry_framework.mutations import (
    DjangoMutation as DjangoMutationFromPackage,
)
from django_strawberry_framework.mutations import resolvers as mutation_resolvers
from django_strawberry_framework.mutations import sets as mutation_sets
from django_strawberry_framework.mutations.inputs import (
    CREATE,
    INPUTS_MODULE_PATH,
    PARTIAL,
    _materialized_names,
    editable_input_fields,
    mutation_input_shape,
)
from django_strawberry_framework.mutations.sets import (
    DjangoMutationMetaclass,
    _mutation_registry,
    _resolve_primary_type,
    _shape_build_cache,
    _validate_input_class,
    clear_mutation_shape_build_cache,
    iter_mutations,
    register_mutation,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.base import (
    ALLOWED_META_KEYS,
    DEFERRED_META_KEYS,
)
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.inputs import RELATION_SINGLE, SCALAR
from tests._idioms import (
    canonical_order,
    definition_raises,
    module_binding,
    pickle_roundtrip,
    scrambled,
)
from tests.optimizer import _link_models

if TYPE_CHECKING:
    from typing import TypeAlias

    from django.db.models.expressions import Combinable

    # The field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry (co-clearing mutation ledgers + the shape build cache).

    ``registry.clear()`` co-clears ``clear_mutation_input_namespace`` (input +
    payload globals ledger), ``clear_mutation_registry`` (declaration registry),
    and ``clear_mutation_shape_build_cache`` (per-pass input build cache), so a
    single ``registry.clear()`` resets every mutation-side ledger. The products
    ``DjangoType``s register on import, so the clear is needed before/after.
    """
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Meta validation matrix - class creation, ConfigurationError
# ---------------------------------------------------------------------------


def test_meta_without_model_raises() -> None:
    """A ``Meta`` with no resolvable model raises naming ``Meta.model``."""
    with pytest.raises(ConfigurationError, match="no resolvable model"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                operation = "create"


def test_meta_model_string_raises_at_class_creation() -> None:
    """A string ``Meta.model`` raises ``ConfigurationError`` at class creation.

    Before the gate, ``Meta.model = "Item"`` snapshotted successfully and the
    phase-2.5 bind crashed with ``AttributeError: 'str' object has no attribute
    '__name__'``. Mirror ``DjangoType``'s ``Meta.model must be a Django model
    class`` posture so a typo'd / lazy string never reaches finalize.
    """
    with pytest.raises(ConfigurationError, match="must be a Django model class"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = "Item"
                operation = "create"


def test_meta_model_instance_raises_at_class_creation() -> None:
    """A model *instance* ``Meta.model`` raises at class creation (not finalize)."""
    with pytest.raises(ConfigurationError, match="must be a Django model class"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item()
                operation = "create"


def test_meta_bad_operation_raises() -> None:
    """An ``operation`` outside the valid set raises naming the bad value + valid set."""
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "upsert"


def test_meta_missing_operation_raises() -> None:
    """A missing ``operation`` raises the same operation error (``None`` is not valid)."""
    with pytest.raises(ConfigurationError, match="operation must be one of"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item


def test_meta_unknown_key_raises() -> None:
    """A stray ``Meta`` key raises the typo guard (mutation-local allowed set)."""
    with pytest.raises(ConfigurationError, match="unknown keys"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                widget = "nope"


def test_meta_fields_and_exclude_both_raises() -> None:
    """Declaring both ``fields`` and ``exclude`` raises (mutual exclusion at creation)."""
    with pytest.raises(ConfigurationError, match="both `fields` and `exclude`"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ("name",)
                exclude = ("description",)


def test_meta_duplicate_fields_raises() -> None:
    """A repeated name in ``Meta.fields`` raises at class creation.

    ``("name", "name", "category")`` would otherwise collapse silently when the
    effective field set is taken as a ``frozenset``, masking the malformed
    declaration. The shared ``normalize_field_name_sequence`` rejects it fail-loud
    naming the repeated field.
    """
    with pytest.raises(ConfigurationError, match="duplicate field name"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ("name", "name", "category")


def test_meta_duplicate_exclude_raises() -> None:
    """A repeated name in ``Meta.exclude`` is rejected the same way, naming ``exclude``."""
    with pytest.raises(ConfigurationError, match=r"Meta\.exclude declares duplicate"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                exclude = ("description", "description")


@pytest.mark.parametrize("kind", [set, frozenset])
def test_meta_exclude_accepts_an_unordered_set_stored_in_canonical_order(
    kind: type[set[str] | frozenset[str]],
) -> None:
    """A set-valued ``Meta.exclude`` builds, and its stored tuple ignores the hash order.

    ``exclude`` only names columns to drop (the input keeps the model's column order), so
    a set is a natural spelling; it is stored sorted by ``canonical_sort_key``, so the
    snapshot is the same under every ``PYTHONHASHSEED``. ``scrambled`` iterates out of that
    order in this process, so storing the declared iteration order fails the row.
    """
    declared = scrambled(
        kind,
        (
            "flag",
            "score",
            "price",
            "occurred_on",
            "payload",
        ),
    )

    class UpdateSpecimen(DjangoMutation):
        class Meta:
            model = scalar_models.ScalarSpecimen
            operation = "update"
            exclude = declared

    assert UpdateSpecimen._mutation_meta.exclude == tuple(canonical_order(declared))


def test_meta_unknown_fields_raises_at_class_creation() -> None:
    """An unknown ``Meta.fields`` name raises at class creation (not finalize).

    ``editable_input_fields`` rejects unknown names, but only when the bind /
    generator walks the set - so on its own a typo'd create/update ``Meta.fields``
    would register cleanly and fail later. The model ``_validate_meta`` runs
    that walk at class creation (form-flavor parity).
    """
    with pytest.raises(ConfigurationError, match="non-editable or unknown field"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ("not_a_real_field",)


def test_update_meta_fields_naming_the_primary_key_raises_at_class_creation() -> None:
    """An update ``Meta.fields`` naming the row's primary key is refused at class creation.

    ``PatronProfile`` is keyed by its one-to-one ``patron``, which the create input
    carries; the update input never does, since its ``id`` argument names the row. The
    same ``Meta.fields`` builds a create, and an update ``Meta.exclude`` naming the key
    builds too, because it states what the update input already does.
    """

    class CreateProfile(DjangoMutation):
        class Meta:
            model = library_models.PatronProfile
            operation = "create"
            fields = ("patron", "address_2")

    class UpdateProfileExcludingKey(DjangoMutation):
        class Meta:
            model = library_models.PatronProfile
            operation = "update"
            exclude = ("patron",)

    assert CreateProfile._mutation_meta.fields == ("patron", "address_2")
    assert UpdateProfileExcludingKey._mutation_meta.exclude == ("patron",)
    with pytest.raises(
        ConfigurationError,
        match=re.escape(
            "DjangoMutation for PatronProfile declares `fields` naming ['patron'], which "
            "write(s) the row's primary key.",
        ),
    ):

        @definition_raises
        class UpdateProfile(DjangoMutation):
            class Meta:
                model = library_models.PatronProfile
                operation = "update"
                fields = ("patron", "address_2")


def test_meta_fields_naming_a_foreign_object_raises_at_class_creation() -> None:
    """``Meta.fields`` naming a forward ``ForeignObject`` raises naming its link columns.

    The relation has no column of its own to write; the class-creation walk
    rejects it and points at the carriers, which the full-shape input already
    writes as scalars.
    """
    with pytest.raises(
        ConfigurationError,
        match=re.escape(
            "DjangoMutation for LnkPairChild declares `fields` naming LnkPairChild.parent, a "
            "ForeignObject that targets LnkParent (tenant, code) through the carrier column(s) "
            "(p_tenant, p_code). It has no column of its own and cannot be generated as a "
            "mutation input. Name its carrier field(s) (p_tenant, p_code) in `fields` instead.",
        ),
    ):

        @definition_raises
        class CreatePairChild(DjangoMutation):
            class Meta:
                model = _link_models.LnkPairChild
                operation = "create"
                fields = ("name", "parent")


def test_meta_empty_fields_raises_at_class_creation() -> None:
    """``Meta.fields = ()`` on create/update raises at class creation (empty input)."""
    with pytest.raises(ConfigurationError) as exc:

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = ()

    assert str(exc.value) == (
        "DjangoMutation create input for Item has no fields; Meta.fields / Meta.exclude "
        "narrowed the editable column set to empty (or the model declares no editable "
        "columns). A mutation input must define at least one field."
    )


def test_meta_fields_non_string_entry_raises() -> None:
    """A non-string entry in ``Meta.fields`` raises at class creation."""
    with pytest.raises(ConfigurationError, match="non-string entry"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = (1, 2)


def test_meta_delete_with_fields_raises() -> None:
    """``operation="delete"`` with ``Meta.fields`` raises at class creation.

    A delete is id-only and materializes NO input, so it never runs the
    ``editable_input_fields`` walk that would otherwise catch an unknown field
    name - a typo'd ``fields`` would finalize silently. Because ``fields`` /
    ``exclude`` have no effect on a delete at all, declaring them is rejected
    outright regardless of whether the names are valid.
    """
    with pytest.raises(ConfigurationError, match="id-only and takes no input"):

        @definition_raises
        class DeleteItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "delete"
                fields = ("definitely_not_a_field",)


def test_meta_delete_with_exclude_raises() -> None:
    """The same rejection applies to ``Meta.exclude`` on a delete operation."""
    with pytest.raises(ConfigurationError, match="id-only and takes no input"):

        @definition_raises
        class DeleteItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "delete"
                exclude = ("name",)


def test_meta_input_class_not_strawberry_input_raises() -> None:
    """A plain (non-``@strawberry.input``) ``input_class`` raises (Error-shapes)."""

    class NotAnInput:
        pass

    with pytest.raises(ConfigurationError, match=r"@strawberry\.input"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                input_class = NotAnInput


def test_meta_input_class_diverging_field_names_raises() -> None:
    """An ``input_class`` with names off the generated scheme raises.

    The generated scheme: scalars use the model field name, forward FK uses
    ``<field>_id``. A custom input naming a relation field ``category`` (instead of
    ``category_id``) diverges and is rejected at class creation.
    """

    @strawberry.input
    class BadItemInput:
        name: str
        category: int  # should be ``category_id`` per the generated scheme

    with pytest.raises(ConfigurationError, match="diverge from the generated naming scheme"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                input_class = BadItemInput


def test_custom_inputs_follow_the_primary_key_rule_of_their_operation() -> None:
    """A custom create input may carry a client-assigned key; a custom update input may not.

    ``Edition`` is keyed by its ISBN text: the generated create input carries
    ``isbn_13``, so an ``input_class`` naming it follows the scheme, while the update
    input never does, so a ``partial_input_class`` naming it diverges.
    """

    @strawberry.input
    class EditionKeyInput:
        isbn_13: str
        imprint: str

    class CreateEdition(DjangoMutation):
        class Meta:
            model = library_models.Edition
            operation = "create"
            input_class = EditionKeyInput

    assert CreateEdition._mutation_meta.input_class is EditionKeyInput
    with pytest.raises(ConfigurationError, match="diverge from the generated naming scheme"):

        @definition_raises
        class UpdateEdition(DjangoMutation):
            class Meta:
                model = library_models.Edition
                operation = "update"
                partial_input_class = EditionKeyInput


def test_meta_input_class_following_scheme_validates_clean() -> None:
    """A custom ``input_class`` whose names follow the scheme is accepted."""

    @strawberry.input
    class GoodItemInput:
        name: str
        category_id: int

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = GoodItemInput

    assert CreateItem._mutation_meta.input_class is GoodItemInput


@pytest.mark.parametrize(
    ("operation", "override_name", "applies_to"),
    [
        ("delete", "input_class", "create"),
        ("delete", "partial_input_class", "update"),
        ("create", "partial_input_class", "update"),
        ("update", "input_class", "create"),
    ],
)
def test_meta_inapplicable_input_override_raises(
    operation: str,
    override_name: str,
    applies_to: str,
) -> None:
    """Every input override fails loud when its operation cannot consume it."""

    @strawberry.input
    class GoodItemInput:
        name: str
        category_id: int

    mutation_meta = type(
        "Meta",
        (),
        {"model": product_models.Item, "operation": operation, override_name: GoodItemInput},
    )
    with pytest.raises(
        ConfigurationError,
        match=rf"Meta\.{override_name} applies only to operation='{applies_to}'",
    ):

        @definition_raises
        class MisconfiguredItemMutation(DjangoMutation):
            Meta = mutation_meta


@pytest.mark.parametrize(
    ("operation", "override_name", "other_override_name"),
    [
        ("create", "input_class", "partial_input_class"),
        ("update", "partial_input_class", "input_class"),
    ],
)
def test_meta_applicable_input_override_is_accepted(
    operation: str,
    override_name: str,
    other_override_name: str,
) -> None:
    """Create and update retain the one consumer override each binds."""

    @strawberry.input
    class GoodItemInput:
        name: str
        category_id: int

    mutation_meta = type(
        "Meta",
        (),
        {"model": product_models.Item, "operation": operation, override_name: GoodItemInput},
    )

    class ItemMutation(DjangoMutation):
        Meta = mutation_meta

    assert getattr(ItemMutation._mutation_meta, override_name) is GoodItemInput
    assert getattr(ItemMutation._mutation_meta, other_override_name) is None


# ---------------------------------------------------------------------------
# permission_classes default + override
# ---------------------------------------------------------------------------


def test_permission_classes_defaults_to_django_model_permission() -> None:
    """A ``Meta`` with no ``permission_classes`` resolves to ``[DjangoModelPermission]``."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    assert CreateItem._mutation_meta.permission_classes == (DjangoModelPermission,)


def test_permission_classes_explicit_override_honored() -> None:
    """An explicit ``permission_classes`` list is stored verbatim (as the immutable tuple)."""

    class AllowAll:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            return True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [AllowAll]

    assert CreateItem._mutation_meta.permission_classes == (AllowAll,)


def test_permission_classes_sequence_is_normalized_to_an_immutable_tuple() -> None:
    """A tuple ``permission_classes`` is normalized to the stored tuple (immutable snapshot)."""

    class AllowAll:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            return True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = (AllowAll,)

    assert CreateItem._mutation_meta.permission_classes == (AllowAll,)


def test_permission_classes_bare_class_raises() -> None:
    """A bare class (not wrapped in a sequence) raises at class creation.

    The contract is a *sequence* of permission classes; a single class would
    iterate as a ``TypeError`` inside ``check_permission`` at request time, so it is
    rejected up front naming the sequence requirement.
    """

    class AllowAll:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            return True

    with pytest.raises(ConfigurationError, match="must be a sequence of"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = AllowAll


def test_permission_classes_bare_string_raises() -> None:
    """A bare string ``permission_classes`` raises (would iterate as characters)."""
    with pytest.raises(ConfigurationError, match="must be a sequence of"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = "AllowAll"


def test_permission_classes_instance_entry_raises() -> None:
    """An entry that is an INSTANCE (not a class) raises.

    ``check_permission`` does ``permission_class().has_permission(...)`` - it
    INSTANTIATES each entry - so an already-instantiated object is invalid and is
    rejected at class creation rather than as a request-time ``TypeError``.
    """

    class AllowAll:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            return True

    with pytest.raises(ConfigurationError, match="not a permission class exposing has_permission"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = [AllowAll()]  # instance, not the class


def test_permission_classes_entry_without_has_permission_raises() -> None:
    """A class entry lacking ``has_permission`` raises at class creation."""

    class NotAPermission:
        pass

    with pytest.raises(ConfigurationError, match="not a permission class exposing has_permission"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = [NotAPermission]


# ---------------------------------------------------------------------------
# _resolve_model seam
# ---------------------------------------------------------------------------


def test_resolve_model_seam_lets_subclass_supply_model_without_meta_model() -> None:
    """Overriding ``_resolve_model`` supplies the model without a literal ``Meta.model``."""

    class FlavorMutation(DjangoMutation):
        @classmethod
        @override
        def _resolve_model(cls, meta: type[object]) -> type[Model] | None:
            # The form and serializer flavors derive the model from form_class /
            # serializer_class; emulate that here with a stand-in source.
            return getattr(meta, "_model_source", None)

    class CreateItem(FlavorMutation):
        class Meta:
            _model_source = product_models.Item
            operation = "create"

    assert CreateItem._mutation_meta.model is product_models.Item


# ---------------------------------------------------------------------------
# Declaration registration
# ---------------------------------------------------------------------------


def test_concrete_mutation_registers_abstract_base_does_not() -> None:
    """A concrete mutation is recorded; the abstract ``DjangoMutation`` base is not."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    assert CreateItem in iter_mutations()
    assert DjangoMutation not in iter_mutations()


def test_registration_is_idempotent() -> None:
    """Re-recording the same class (identity) does not double-register."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    register_mutation(CreateItem)
    assert _mutation_registry.count(CreateItem) == 1


def test_late_declaration_after_finalize_raises() -> None:
    """Declaring a mutation after ``finalize_django_types()`` raises (Edge cases)."""

    class ItemType2(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Item) is ItemType2

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="after finalization"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"


# ---------------------------------------------------------------------------
# Phase-2.5 bind - the finalize-time materialize trigger
# ---------------------------------------------------------------------------


def _declare_products_primaries() -> tuple[type[DjangoType], type[DjangoType]]:
    """Register primary ``DjangoType``s for ``Item`` and ``Category`` (Relay-shaped)."""

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


def test_bind_materializes_input_and_payload_globals() -> None:
    """After finalize, the create/update/delete classes are materialized into inputs.

    The bind is the FIRST caller of ``build_mutation_input`` / ``build_payload_type``
    / ``materialize_mutation_input_class``: pin they fire at finalize. The true
    "materialized at finalize" signal is the ledger ``_materialized_names`` (reset
    by ``registry.clear()``), not ``hasattr`` of the module global - materialized
    classes are deliberately left PARKED in ``__dict__`` across a clear (the
    shared parked-globals lifecycle), so a prior test's parked ``ItemInput`` would
    make a bare ``hasattr`` pass spuriously.
    """
    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    # Ledger empty before finalize: nothing has been materialized this build.
    assert _materialized_names == {}

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    # create -> ItemInput; update -> ItemPartialInput; delete -> no input.
    assert "ItemInput" in _materialized_names
    assert "ItemPartialInput" in _materialized_names
    # Every operation gets a payload.
    assert "CreateItemPayload" in _materialized_names
    assert "UpdateItemPayload" in _materialized_names
    assert "DeleteItemPayload" in _materialized_names
    # The materialized class is also a real module global (the lazy-ref contract).
    assert module_binding(inputs_module, "ItemInput") is _materialized_names["ItemInput"]

    # The bind stashes forward-compat refs for the resolver pipeline.
    assert CreateItem._input_class is _materialized_names["ItemInput"]
    assert CreateItem._payload_type_name == "CreateItemPayload"
    assert DeleteItem._input_class is None  # delete is id-only
    assert DeleteItem._input_field_specs == ()
    assert UpdateItem._primary_type is not None
    create_attrs = {spec.input_attr for spec in CreateItem._input_field_specs or ()}
    assert create_attrs == {
        field.python_name
        for field in get_object_definition(CreateItem._input_class, strict=True).fields
    }
    assert "category_id" in create_attrs
    assert CreateItem._model_fields_by_attr is not None
    assert CreateItem._model_fields_by_attr["category_id"] is (
        product_models.Item._meta.get_field("category")
    )


def test_bind_is_retry_idempotent_after_fixable_later_phase_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A re-call after a fixable post-bind finalization failure succeeds, not a masked collision.

    ``finalize_django_types()`` documents recover-in-place: fix the offending
    cause and call again, no ``registry.clear()`` required. But phase 2.5 binds
    mutations (materializing ``ItemInput`` into the ledger) BEFORE the later phases
    that can fail. A bind that cleared only ``_shape_build_cache`` would leave the
    ledger populated with run-1's class object, so run-2 would rebuild a fresh
    ``ItemInput`` and hit a spurious distinct-class collision in
    ``materialize_generated_input_class`` - masking the original, fixed error.
    Resetting the materialization ledgers in ``finalize_django_types`` before the
    bind sequence makes the rerun clean.
    """
    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    # A fixable failure in a phase that runs AFTER the mutation bind (orderset bind
    # sits just past ``bind_mutations`` / ``bind_form_mutations`` in phase 2.5).
    def _boom() -> None:
        raise RuntimeError("injected post-bind finalization failure")

    monkeypatch.setattr("django_strawberry_framework.types.finalizer._bind_ordersets", _boom)
    with pytest.raises(RuntimeError, match="injected post-bind"):
        finalize_django_types()
    # The bind already materialized the input before the later phase failed.
    assert "ItemInput" in _materialized_names
    assert registry.is_finalized() is False

    # Fix the cause and re-finalize WITHOUT registry.clear(): the rerun must NOT
    # raise the masking distinct-class collision.
    monkeypatch.undo()
    finalize_django_types()

    assert registry.is_finalized() is True
    assert "ItemInput" in _materialized_names
    assert CreateItem._input_class is _materialized_names["ItemInput"]


def test_bind_merges_consumer_input_class_with_generated_remainder() -> None:
    """A consumer ``input_class`` overriding ONE field is MERGED, not a wholesale replace.

    The spec-010 relation-override contract: the
    consumer declares only the field it customizes; the generator fills the rest of
    the editable shape, and the consumer's field is honored, not clobbered. A
    partial consumer input must therefore yield the FULL shape - both the
    consumer's ``name`` (with its custom description preserved) AND the generated
    ``category_id`` - under the canonical ``ItemInput`` name, never just ``name``.
    """
    _declare_products_primaries()

    @strawberry.input
    class CustomItemInput:
        # Override ONLY ``name`` (custom description); everything else is generated.
        name: str = strawberry.field(description="A custom-described name")

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = CustomItemInput

    finalize_django_types()

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    fields = {f.python_name: f for f in get_object_definition(merged, strict=True).fields}
    # Generated remainder filled in (the partial-replacement bug would drop these).
    assert "category_id" in fields
    assert "is_private" in fields
    # Consumer field honored, not clobbered (its description survives the merge).
    assert fields["name"].description == "A custom-described name"
    spec_by_attr = {spec.input_attr: spec for spec in CreateItem._input_field_specs or ()}
    assert set(spec_by_attr) == set(fields)

    assert spec_by_attr["name"].kind == SCALAR
    assert spec_by_attr["category_id"].kind == RELATION_SINGLE
    assert spec_by_attr["category_id"].related_model is product_models.Category


def test_bind_merges_an_input_class_that_overrides_every_selected_column() -> None:
    """An ``input_class`` naming every selected column leaves an empty remainder; it still binds.

    The generated half of the merge carries no field, and the merged input is the
    consumer's alone, so an empty generated remainder is a valid build, never the
    empty-input refusal (that belongs to an empty selection).
    """
    _declare_products_primaries()

    @strawberry.input
    class CustomCategoryName:
        name: str = strawberry.field(description="custom name")

    class CreateCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "create"
            fields = ("name",)
            input_class = CustomCategoryName

    finalize_django_types()

    merged = _materialized_names["CategoryNameInput"]
    assert CreateCategory._input_class is merged
    assert {
        f.python_name: f.description for f in get_object_definition(merged, strict=True).fields
    } == {"name": "custom name"}


def test_bind_merges_consumer_partial_input_class_for_update() -> None:
    """A consumer ``partial_input_class`` is likewise merged on the update side."""
    _declare_products_primaries()

    @strawberry.input
    class CustomItemPartial:
        name: str | None = strawberry.field(default=UNSET, description="custom partial")

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            partial_input_class = CustomItemPartial

    finalize_django_types()

    merged = _materialized_names["ItemPartialInput"]
    assert UpdateItem._input_class is merged
    fields = {f.python_name: f for f in get_object_definition(merged, strict=True).fields}
    assert "category_id" in fields  # generator filled the rest
    assert fields["name"].description == "custom partial"  # consumer field honored


def test_bind_rejects_raw_pk_relation_override_for_relay_target() -> None:
    """A raw-pk relation override for a Relay-Node target raises at bind (Decision 10).

    ``Category`` has a primary Relay-Node type, so the generated ``category_id`` input
    is a ``strawberry.ID`` decoded as a GlobalID, type-checked AND visibility-checked
    through ``Category``'s ``get_queryset`` (Decision 10) at decode. A consumer
    ``input_class`` declaring ``category_id: int`` (a raw pk) publishes an ``Int`` the
    GlobalID decode can never read, so every request would be the invalid-relation
    ``FieldError``. The bind rejects it fail-loud.

    Enforced at finalization, not class creation: whether ``Category`` has a primary
    Relay-Node type is a ``registry.get`` lookup only reliably populated at the
    phase-2.5 bind (``_validate_input_class`` name-checks at class creation but cannot
    know the id type then - it passes ``related_primary_type=None``).
    """
    _declare_products_primaries()

    @strawberry.input
    class RawPkItemInput:
        name: str
        category_id: int  # raw pk: the GlobalID decode can never read it

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = RawPkItemInput

    assert CreateItem in iter_mutations()

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_raw_pk_relation_override_on_partial_input() -> None:
    """The type-lock applies to ``partial_input_class`` (update) too (Decision 10)."""
    _declare_products_primaries()

    @strawberry.input
    class RawPkItemPartial:
        category_id: int | None = strawberry.field(default=UNSET)

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            partial_input_class = RawPkItemPartial

    assert UpdateItem in iter_mutations()

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_strawberry_parsed_globalid_relation_override() -> None:
    """A ``relay.GlobalID`` relation override for a Relay-Node target raises at bind.

    ``relay.GlobalID`` makes Strawberry parse the id during argument conversion, before the
    resolver runs, so a malformed id would fail there as a masked top-level error instead
    of reaching the package decode as the ``categoryId`` relation ``FieldError`` the
    generated ``strawberry.ID`` input answers. The bind rejects the divergent core.
    """
    _declare_products_primaries()

    @strawberry.input
    class ParsedGidItemInput:
        name: str
        category_id: relay.GlobalID

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = ParsedGidItemInput

    assert CreateItem in iter_mutations()

    with pytest.raises(ConfigurationError, match=r"Declare 'category_id' as strawberry\.ID"):
        finalize_django_types()


def test_bind_accepts_id_relation_override_for_relay_target() -> None:
    """A relation override that keeps the generated ``strawberry.ID`` id type binds clean.

    The contract-compliant form: the consumer customizes the relation field's
    representation (here a description) while keeping the ``strawberry.ID`` id type, so
    the GlobalID decode and the Decision-10 visibility contract still ride the merged
    field. The merge honors the consumer's field, and the generator fills the remainder.
    """
    _declare_products_primaries()

    @strawberry.input
    class GidItemInput:
        category_id: strawberry.ID = strawberry.field(
            description="custom category ref",
        )

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = GidItemInput

    finalize_django_types()

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    fields = {f.python_name: f for f in get_object_definition(merged, strict=True).fields}
    assert fields["category_id"].description == "custom category ref"  # consumer field honored
    assert "name" in fields  # generator filled the rest


def _declare_book_m2m_primaries() -> tuple[type[DjangoType], type[DjangoType], type[DjangoType]]:
    """Register Relay-Node primaries for ``Genre`` / ``Shelf`` / ``Book`` (Book has a real M2M).

    The M2M analogue of ``_declare_products_primaries``: ``Book.genres`` is a forward
    M2M to ``Genre`` (a Relay-Node primary), so the generated relation input is
    ``list[strawberry.ID]`` - the shape an override must keep.
    """

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title", "genres")
            primary = True

    return GenreT, ShelfT, BookT


def test_bind_rejects_m2m_relation_override_as_scalar_id() -> None:
    """An M2M override declared as a SCALAR ``strawberry.ID`` raises at bind.

    ``Book.genres`` generates ``list[strawberry.ID]``; a consumer ``genres:
    strawberry.ID`` keeps the ``ID`` core but loses the list container, so the M2M decode
    would refuse the string atom on every request. A core-only type-lock would miss
    this - the shape-aware lock catches the list-depth mismatch.
    """
    _declare_book_m2m_primaries()

    @strawberry.input
    class BadBookInput:
        genres: strawberry.ID

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = BadBookInput

    assert CreateBook in iter_mutations()

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_m2m_relation_override_as_nested_id_list() -> None:
    """An M2M override declared as a NESTED ``list[list[strawberry.ID]]`` raises at bind.

    The nested-list shape has the ``ID`` core but list depth 2 vs the generated depth 1;
    the inner lists are not id strings, so the GlobalID decode would fail every member.
    The shape-lock rejects the depth mismatch at the bind.
    """
    _declare_book_m2m_primaries()

    @strawberry.input
    class BadBookInput:
        genres: list[list[strawberry.ID]]

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = BadBookInput

    assert CreateBook in iter_mutations()

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_rejects_fk_relation_override_as_id_list() -> None:
    """A forward-FK override declared as a ``list[strawberry.ID]`` raises at bind.

    ``Item.category`` generates a SCALAR ``strawberry.ID``; a ``category_id:
    list[strawberry.ID]`` has the ``ID`` core but list depth 1 vs the generated 0. The FK
    decode wraps the value in a one-element list, the inner list fails the GlobalID
    decode, and every request would be the invalid-relation ``FieldError``. The
    shape-lock rejects it at the bind.
    """
    _declare_products_primaries()

    @strawberry.input
    class BadItemInput:
        category_id: list[strawberry.ID]

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = BadItemInput

    assert CreateItem in iter_mutations()

    with pytest.raises(ConfigurationError, match="diverges from the generated input"):
        finalize_django_types()


def test_bind_accepts_optional_fk_relation_override() -> None:
    """A forward-FK override declared as ``strawberry.ID | None`` binds clean (positive control).

    The shape-lock compares the ``strawberry.ID`` core and the list depth only; an
    Optional wrapper is nullability, so the nullable scalar keeps depth 0 and the
    merged input honors the consumer's field.
    """
    _declare_products_primaries()

    @strawberry.input
    class NullableItemInput:
        category_id: strawberry.ID | None = strawberry.field(description="nullable category ref")

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = NullableItemInput

    finalize_django_types()

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    fields = {f.python_name: f for f in get_object_definition(merged, strict=True).fields}
    assert fields["category_id"].description == "nullable category ref"


def test_bind_accepts_optional_m2m_relation_override() -> None:
    """An M2M override declared as ``list[strawberry.ID] | None`` binds clean (positive control).

    The Optional wrapper around the one-level list is nullability, not list depth, so
    the shape-lock reads depth 1 with the ``strawberry.ID`` core and the merged input
    honors the consumer's field.
    """
    _declare_book_m2m_primaries()

    @strawberry.input
    class NullableBookInput:
        genres: list[strawberry.ID] | None = strawberry.field(description="nullable genres ref")

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = NullableBookInput

    finalize_django_types()

    assert CreateBook._input_class is not None
    merged = _materialized_names[CreateBook._input_class.__name__]
    fields = {f.python_name: f for f in get_object_definition(merged, strict=True).fields}
    assert fields["genres"].description == "nullable genres ref"


def test_bind_accepts_m2m_relation_override_as_id_list() -> None:
    """The contract-compliant M2M override - ``list[strawberry.ID]`` - binds clean (positive control).

    Proves the shape-lock does not over-reject: an override that keeps BOTH the
    ``strawberry.ID`` core AND the one-level ``list`` container (here adding a
    description) is honored, and the generator fills the remainder.
    """
    _declare_book_m2m_primaries()

    @strawberry.input
    class GidBookInput:
        genres: list[strawberry.ID] = strawberry.field(description="custom genres ref")

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            input_class = GidBookInput

    finalize_django_types()

    assert CreateBook._input_class is not None
    merged = _materialized_names[CreateBook._input_class.__name__]
    fields = {f.python_name: f for f in get_object_definition(merged, strict=True).fields}
    assert fields["genres"].description == "custom genres ref"  # consumer field honored
    assert "shelf_id" in fields  # generator filled the FK remainder


def test_bind_dedupes_identical_full_shapes() -> None:
    """Two create mutations over the same model with the full shape share one ``ItemInput``."""
    _declare_products_primaries()

    class CreateItemA(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class CreateItemB(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    finalize_django_types()
    # Both bind to the same materialized ``ItemInput`` (identical shapes dedupe).
    assert CreateItemA._input_class is CreateItemB._input_class
    assert CreateItemA._input_class is module_binding(sys.modules[INPUTS_MODULE_PATH], "ItemInput")


def test_bind_dedupes_full_set_fields_with_bare_create() -> None:
    """A ``fields`` list naming the full editable set dedupes with a bare create.

    The type identity is the EFFECTIVE field set (spec-036 Decision 6), not the raw
    ``(fields, exclude)`` declaration. ``Item``'s full editable set is
    ``("name", "description", "category", "attachment", "is_private")``; a
    ``fields`` list naming exactly that set IS the canonical shape, so it must
    resolve to the same materialized ``ItemInput`` as an un-narrowed create
    (spec-036 Edge cases and constraints) rather than spuriously raising a
    distinct-shape collision on the shared name.
    """
    _declare_products_primaries()

    class CreateBare(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class CreateFull(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            fields = (
                "name",
                "description",
                "category",
                "attachment",
                "is_private",
            )

    # Reaches finalize without raising; both share the one canonical ``ItemInput``.
    finalize_django_types()
    assert CreateBare._input_class is CreateFull._input_class
    assert CreateBare._input_class is module_binding(sys.modules[INPUTS_MODULE_PATH], "ItemInput")


def test_bind_dedupes_fields_with_complementary_exclude() -> None:
    """``fields=("name",)`` and the complementary ``exclude`` dedupe to one shape.

    Two narrowings that select the same effective set ``{name}`` via different
    spellings - ``fields=("name",)`` vs ``exclude`` naming every OTHER editable
    column - resolve to the same shape-derived ``<Model>...Input`` name and must
    dedupe to one materialized type (spec-036 Decision 6 / Edge cases and
    constraints), not raise a spurious distinct-shape collision on the shared name.
    """
    _declare_products_primaries()

    class CreateViaFields(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            fields = ("name",)

    class CreateViaExclude(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            exclude = (
                "description",
                "category",
                "attachment",
                "is_private",
            )

    # Reaches finalize without raising; both share one shape-derived input type.
    finalize_django_types()
    assert CreateViaFields._input_class is CreateViaExclude._input_class
    # The shared type is a narrowed, shape-derived name (not the canonical
    # ``ItemInput``, since the effective set is only ``{name}``).
    assert CreateViaFields._input_class is not None
    assert CreateViaFields._input_class.__name__ != "ItemInput"


def test_bind_merged_and_generated_same_shape_distinct_representations_raise() -> None:
    """Two representations of one input shape claiming the canonical name raise.

    Under the merge contract a consumer ``input_class`` is materialized under the
    canonical SHAPE name (``ItemInput``) - the consumer's Python class name is
    irrelevant, it customizes representations of existing columns, not the shape.
    So two ``Item`` create mutations that resolve the same ``ItemInput`` shape to
    two DIFFERENT representations - one consumer-customized, one plain generated -
    claim one name with two distinct class objects, and the input ledger's
    collision check fires at finalize (a consumer class name can neither dodge nor
    forge a collision).
    """
    _declare_products_primaries()

    @strawberry.input
    class CustomItemInput:
        name: str = strawberry.field(description="custom")

    class CreateItemCustom(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = CustomItemInput

    assert CreateItemCustom in iter_mutations()

    class CreateItemPlain(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    assert CreateItemPlain in iter_mutations()

    with pytest.raises(ConfigurationError, match="ItemInput"):
        finalize_django_types()


@strawberry.type
class _PingQuery:
    @strawberry.field
    def ping(self) -> int:
        return 1


def test_bind_merged_narrowed_input_publishes_the_canonical_shape_name() -> None:
    """A merged narrowed input publishes ``shape.type_name`` verbatim, escapes and all.

    ``pascalize_token`` escapes the ``is_private`` underscore as ``_u``, so the shape
    name is ``ItemIs_uprivateNameInput``; Strawberry names a type given no ``name=``
    ``to_camel_case(__name__)``, which would publish ``ItemIsUprivatenameinput`` while
    the ledger holds the canonical name. The merge pins ``name=shape.type_name``.
    """
    _declare_products_primaries()

    @strawberry.input
    class CustomItemInput:
        name: str = strawberry.field(description="custom")

    class CreateNarrowItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            fields = ("name", "is_private")
            input_class = CustomItemInput

    @strawberry.type
    class Mutation:
        create_narrow_item = DjangoMutationField(CreateNarrowItem)

    finalize_django_types()
    shape = mutation_input_shape(product_models.Item, CREATE, fields=("name", "is_private"))
    assert shape.type_name == "ItemIs_uprivateNameInput"
    merged = CreateNarrowItem._input_class
    assert merged is not None
    assert get_object_definition(merged, strict=True).name == shape.type_name
    assert shape.type_name in _materialized_names

    sdl = DjangoSchema(query=_PingQuery, mutation=Mutation).as_str()
    assert "input ItemIs_uprivateNameInput " in sdl


def test_bind_merged_narrowed_shapes_recased_alike_stay_distinct() -> None:
    """Two narrowed merged shapes Strawberry would re-case alike publish both names.

    Columns ``a_b`` + ``c`` and ``a_bc`` name the distinct shapes ``CollA_ubCInput`` and
    ``CollA_ubcInput``; ``to_camel_case`` maps both to ``CollAUbcinput``, so an unpinned
    merge fails the schema build with Strawberry's ``DuplicatedTypeName``, past the
    package's own name-collision guard. ``Coll`` stays synthetic: no fakeshop model
    carries the column pair.
    """

    class Coll(models.Model):
        a_b: _Int = models.IntegerField()
        c: _Int = models.IntegerField()
        a_bc: _Int = models.IntegerField()

        class Meta:
            app_label = "test_mutation_sets_naming"

    class CollNode(DjangoType, relay.Node):
        class Meta:
            model = Coll
            fields = ("id",)
            primary = True

    @strawberry.input
    class CustomCInput:
        c: int = strawberry.field(description="custom")

    @strawberry.input
    class CustomABCInput:
        a_bc: int = strawberry.field(description="custom")

    class CreateCollPair(DjangoMutation):
        class Meta:
            model = Coll
            operation = "create"
            fields = ("a_b", "c")
            input_class = CustomCInput

    class CreateCollJoined(DjangoMutation):
        class Meta:
            model = Coll
            operation = "create"
            fields = ("a_bc",)
            input_class = CustomABCInput

    @strawberry.type
    class Mutation:
        create_coll_pair = DjangoMutationField(CreateCollPair)
        create_coll_joined = DjangoMutationField(CreateCollJoined)

    finalize_django_types()
    assert registry.get(Coll) is CollNode
    sdl = DjangoSchema(query=_PingQuery, mutation=Mutation).as_str()
    assert "input CollA_ubCInput " in sdl
    assert "input CollA_ubcInput " in sdl


def test_bind_duplicate_payload_name_distinct_shapes_raises() -> None:
    """Two mutations generating the same ``<Name>Payload`` for distinct shapes raise.

    Same class name in different "modules" -> same ``<Name>Payload`` name but a
    distinct object slot/type, so the payload ledger collision fires at finalize.
    """
    _declare_products_primaries()

    # Two distinct mutation classes that resolve to the same payload name
    # ``CreateThingPayload`` over distinct primary object types (Item vs Category).
    CreateThing1 = type(
        "CreateThing",
        (DjangoMutation,),
        {"Meta": type("Meta", (), {"model": product_models.Item, "operation": "create"})},
    )
    CreateThing2 = type(
        "CreateThing",
        (DjangoMutation,),
        {"Meta": type("Meta", (), {"model": product_models.Category, "operation": "create"})},
    )
    assert CreateThing1 in iter_mutations()
    assert CreateThing2 in iter_mutations()

    with pytest.raises(ConfigurationError, match="CreateThingPayload"):
        finalize_django_types()


def test_registry_clear_co_clears_mutation_namespace_and_declarations() -> None:
    """``registry.clear()`` resets the materialized ledger AND the declaration registry."""
    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    finalize_django_types()
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "ItemInput")  # materialized
    assert CreateItem in iter_mutations()  # non-empty before clear

    registry.clear()

    # Declaration registry emptied via ``clear_mutation_registry``; ledger emptied
    # via ``clear_mutation_input_namespace`` so a fresh finalize re-emits cleanly.
    assert iter_mutations() == ()

    assert _materialized_names == {}


# ---------------------------------------------------------------------------
# No-registered-primary-type finalize error (Decision 11 / Error-shapes)
# ---------------------------------------------------------------------------


def test_bind_no_registered_type_raises_no_type_to_return() -> None:
    """A mutation over a model with no registered ``DjangoType`` raises at finalize."""

    class CreatePeriodical(DjangoMutation):
        class Meta:
            model = library_models.Periodical
            operation = "create"

    assert CreatePeriodical in iter_mutations()

    with pytest.raises(ConfigurationError, match="no type to return"):
        finalize_django_types()


def test_bind_resolve_primary_distinguishes_ambiguous_from_zero_type() -> None:
    """``_resolve_primary_type`` phrases the ambiguity case distinctly from no-type.

    The full ``finalize_django_types()`` path catches a multiple-types-no-primary
    model at the Phase-1 ``_audit_primary_ambiguity`` BEFORE the bind runs (the
    plan's documented note), so the bind's ambiguity branch is exercised here at
    the unit level. The bind consults ``types_for`` (not just ``registry.get``,
    which returns ``None`` for both cases) to phrase the right message.
    """

    class IssueTypeA(DjangoType):
        class Meta:
            model = library_models.Issue
            fields = ("id", "title")

    assert registry.get(library_models.Issue) is IssueTypeA

    class IssueTypeB(DjangoType):
        class Meta:
            model = library_models.Issue
            fields = ("id", "title")

    assert registry.model_for_type(IssueTypeB) is library_models.Issue

    class CreateIssue(DjangoMutation):
        class Meta:
            model = library_models.Issue
            operation = "create"

    with pytest.raises(ConfigurationError, match="multiple registered DjangoTypes"):
        _resolve_primary_type(CreateIssue, library_models.Issue)

    # The full finalize path catches this earlier at the Phase-1 ambiguity audit.
    with pytest.raises(ConfigurationError, match="multiple registered DjangoType subclasses"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Namespace isolation - mutation Meta key is not a DjangoType Meta key (Decision 12)
# ---------------------------------------------------------------------------


def test_mutation_meta_key_rejected_on_django_type_meta() -> None:
    """A mutation-only key (``operation``) on a ``DjangoType.Meta`` is an unknown key.

    Proves the two ``Meta`` namespaces are disjoint: ``operation`` is a mutation
    key, not a ``DjangoType`` key, so the ``DjangoType`` typo guard rejects it -
    confirming ``ALLOWED_META_KEYS`` carries no mutation key (Decision 12).
    """
    with pytest.raises(ConfigurationError, match="Unknown Meta keys"):

        @definition_raises
        class ItemTypeBad(DjangoType):
            class Meta:
                model = product_models.Item
                fields = ("id", "name")
                operation = "create"


@pytest.mark.parametrize(
    "mutation_key",
    [
        "operation",
        "input_class",
        "partial_input_class",
        "permission_classes",
    ],
    ids=str,
)
def test_djangotype_meta_key_sets_carry_no_mutation_key(mutation_key: str) -> None:
    """The ``DjangoType`` Meta-key sets carry no mutation key."""
    assert mutation_key not in ALLOWED_META_KEYS
    assert mutation_key not in DEFERRED_META_KEYS


# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------


def test_django_mutation_and_permission_are_public_exports() -> None:
    """``DjangoMutation`` + ``DjangoModelPermission`` are root exports in ``__all__``."""
    assert django_strawberry_framework.DjangoMutation is DjangoMutation
    assert DjangoMutationFromPackage is DjangoMutation
    assert django_strawberry_framework.DjangoModelPermission is DjangoModelPermission
    assert DjangoModelPermissionFromPackage is DjangoModelPermission
    assert "DjangoMutation" in django_strawberry_framework.__all__
    assert "DjangoModelPermission" in django_strawberry_framework.__all__


def test_meta_fields_bare_string_raises() -> None:
    """A bare-string ``Meta.fields`` (would iterate as characters) raises at class creation."""
    with pytest.raises(ConfigurationError, match="not a bare string"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                fields = "name"


def test_meta_exclude_lazy_translation_string_raises() -> None:
    """A lazy translation ``Meta.exclude`` is the bare-string refusal naming ``exclude``.

    The ``gettext_lazy`` proxy walks its text character by character, so read as a
    sequence it would exclude one name per character instead of the one it spells.
    """
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoMutation Meta\.exclude must be a sequence of field names, not a bare string",
    ):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                exclude = gettext_lazy("name")


def test_meta_permission_classes_non_iterable_raises() -> None:
    """A non-iterable ``Meta.permission_classes`` (an int) raises via the ``list()`` guard.

    A bare text atom or class is caught by the explicit text-atom and class guards;
    any *other* non-iterable (here an ``int``) trips the ``list(value)`` ``TypeError``
    branch instead, surfacing the same fail-loud ``ConfigurationError`` at class creation.
    """
    with pytest.raises(ConfigurationError, match="must be a sequence of"):

        @definition_raises
        class CreateItem(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = 5


def test_bind_skips_relation_lock_for_non_relay_target() -> None:
    """The relation-type-lock skips a relation whose target type is NOT Relay-Node.

    The relation-type-lock only guards a Relay-Node relation's ``strawberry.ID`` core
    and container shape against a consumer ``input_class`` override. When the FK
    target's ``DjangoType`` is a plain (non-Node) type, the generated ``<field>_id`` is
    a raw pk with no GlobalID decode to feed, so the lock skips it and
    the consumer ``input_class`` merges with the raw-pk remainder. Products' relation
    targets are all Relay-Node, so this skip branch is earned with a non-Node pair here.
    """

    class NonNodeCategoryType(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")

    assert registry.get(product_models.Category) is NonNodeCategoryType

    class NonNodeItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")

    assert registry.get(product_models.Item) is NonNodeItemType

    @strawberry.input
    class CustomItemInput:
        name: str = strawberry.field(description="custom")

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = CustomItemInput

    finalize_django_types()

    merged = _materialized_names["ItemInput"]
    assert CreateItem._input_class is merged
    field_names = {
        field.python_name for field in get_object_definition(merged, strict=True).fields
    }
    assert {"name", "category_id"} <= field_names


# ---------------------------------------------------------------------------
# Model-flavor seam defaults: the seams default to the model behavior
# (spec-038). Validation lives in ``_validate_meta`` beside the
# ``build_input`` / ``input_type_name`` / ``input_module_path`` / ``resolve_*``
# seams; these pin the MODEL flavor's behavior through each seam.
# ---------------------------------------------------------------------------


def test_validate_meta_is_the_classmethod_validation_seam() -> None:
    """The metaclass validates via the ``_validate_meta`` classmethod seam.

    The validation is ``DjangoMutation._validate_meta``, with no module-level
    ``_validate_mutation_meta`` beside it. A model mutation validates through it (a
    representative case pinned), and the seam is a classmethod a subclass can
    override (the form flavor does).
    """
    assert not hasattr(mutation_sets, "_validate_mutation_meta")
    assert "_validate_meta" in vars(DjangoMutation)

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    # The seam produces the validated snapshot.
    assert CreateItem._mutation_meta.model is product_models.Item
    assert CreateItem._mutation_meta.operation == "create"
    # The form_class slot is None on the model flavor.
    assert CreateItem._mutation_meta.form_class is None


def test_model_flavor_input_seams_produce_model_defaults() -> None:
    """``build_input`` / ``input_type_name`` / ``input_module_path`` default to model behavior.

    The seams exist and, on a plain ``DjangoMutation``, produce the model-column
    input materialized in ``mutations.inputs`` under the canonical ``<Model>Input``
    name, reached through the overridable seam.
    """
    _declare_products_primaries()

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    class UpdateItemName(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            fields = ("name",)

    # input_module_path defaults to the mutations.inputs namespace.
    assert CreateItem.input_module_path == INPUTS_MODULE_PATH
    # input_type_name returns the canonical model-input name (full shape).
    assert CreateItem.input_type_name(CreateItem._mutation_meta) == "ItemInput"
    # The seam reads mutation_input_shape(...).type_name - full AND narrowed
    # must match the descriptor the bind / build_mutation_input path uses, so the
    # field's lazy data: ref can never disagree with the materialized class name.
    create_meta = CreateItem._mutation_meta
    assert create_meta.model is not None
    assert (
        CreateItem.input_type_name(create_meta)
        == mutation_input_shape(
            create_meta.model,
            CREATE,
            fields=create_meta.fields,
            exclude=create_meta.exclude,
        ).type_name
    )
    update_meta = UpdateItemName._mutation_meta
    assert update_meta.model is not None
    assert (
        UpdateItemName.input_type_name(update_meta)
        == mutation_input_shape(
            update_meta.model,
            PARTIAL,
            fields=update_meta.fields,
            exclude=update_meta.exclude,
        ).type_name
    )
    assert UpdateItemName.input_type_name(update_meta) != "ItemPartialInput"

    finalize_django_types()

    # build_input (via the bind) materialized the model-column input into
    # mutations.inputs under the canonical name (the 036 default).
    assert "ItemInput" in _materialized_names
    materialized = _materialized_names["ItemInput"]
    assert CreateItem._input_class is materialized
    # The input carries the model's editable columns (name + category_id), proving
    # it is the model-column input, not a form-derived one.
    field_names = {f.python_name for f in get_object_definition(materialized, strict=True).fields}
    editable = {f.name for f in editable_input_fields(product_models.Item, operation_kind=PARTIAL)}
    assert "name" in field_names
    assert "category_id" in field_names  # FK -> <field>_id scheme
    assert "name" in editable


def test_model_flavor_resolve_seams_delegate_to_resolver_entry_points() -> None:
    """``resolve_sync`` / ``resolve_async`` default to the model resolver entry points.

    The seams delegate to ``mutations/resolvers.py::resolve_mutation_sync`` /
    ``resolve_mutation_async`` (the model dispatch); ``fields.py::_resolve`` calls
    them, so the model resolver path runs through the seams.
    """
    assert "resolve_sync" in vars(DjangoMutation)
    assert "resolve_async" in vars(DjangoMutation)

    assert callable(mutation_resolvers.resolve_mutation_sync)
    assert callable(mutation_resolvers.resolve_mutation_async)


def test_mutation_shape_build_cache_clears_via_registry_and_direct_clear() -> None:
    """The model shape cache uses ``make_shape_build_cache`` and co-clears on ``registry.clear()``.

    Forms and serializer already rode the factory + ``register_subsystem_clear``;
    the model flavor kept a hand-rolled dict cleared only inside ``bind_mutations``.
    A ``registry.clear()`` without a following bind then left stale shape entries.
    Direct ``clear_mutation_shape_build_cache`` and ``registry.clear()`` both empty
    the same dict.
    """

    @strawberry.input
    class ProbeInput:
        __strawberry_definition__: ClassVar[StrawberryObjectDefinition]
        name: str

    probe_key = (product_models.Category, "create", frozenset({"name"}))
    _shape_build_cache[probe_key] = ProbeInput
    assert probe_key in _shape_build_cache

    clear_mutation_shape_build_cache()
    assert _shape_build_cache == {}

    _shape_build_cache[probe_key] = ProbeInput
    registry.clear()
    assert _shape_build_cache == {}


@pytest.mark.parametrize(
    ("metaclass", "name", "module"),
    [
        pytest.param(
            DjangoMutationMetaclass,
            "DjangoMutationMetaclass",
            "django_strawberry_framework.mutations.sets",
            id="model-mutation",
        ),
        pytest.param(
            DjangoFormMutationMetaclass,
            "DjangoFormMutationMetaclass",
            "django_strawberry_framework.forms.sets",
            id="form-mutation",
        ),
    ],
)
def test_public_metaclasses_pin_public_identity_and_pickle(
    metaclass: type,
    name: str,
    module: str,
) -> None:
    """Each public metaclass remains module-addressable and pickleable by its own name."""
    assert metaclass.__name__ == name
    assert metaclass.__qualname__ == name
    assert metaclass.__module__ == module
    assert getattr(importlib.import_module(module), name) is metaclass
    assert pickle_roundtrip(metaclass) is metaclass


# Each value an operation key can never be: unhashable containers and non-string scalars.
_UNHASHABLE_AND_NON_STRING_OPERATIONS: tuple[object, ...] = (
    list[object](),
    dict[object, object](),
    {"a": 1},
    set[object](),
    123,
    True,
    None,
)


@pytest.mark.parametrize("invalid_op", _UNHASHABLE_AND_NON_STRING_OPERATIONS)
def test_django_mutation_validate_meta_rejects_unhashable_and_non_string_operation(
    invalid_op: object,
) -> None:
    """DjangoMutation._validate_meta raises ConfigurationError for unhashable or non-string operations."""
    _declare_products_primaries()

    with pytest.raises(
        ConfigurationError,
        match=(
            r"DjangoMutation BadOpMutation\.Meta\.operation must be one of \['create', "
            r"'delete', 'update'\]; got "
        ),
    ):

        @definition_raises
        class BadOpMutation(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = invalid_op


class _HostileRepr:
    @override
    def __repr__(self) -> str:
        raise RuntimeError("HostileRepr exploded")

    @override
    def __str__(self) -> str:
        raise RuntimeError("HostileRepr str exploded")


def test_validate_input_class_hostile_repr_propagates() -> None:
    """The non-input rejection renders the value through its own ``__repr__``; it propagates."""
    hostile = _HostileRepr()
    with pytest.raises(RuntimeError, match="HostileRepr exploded"):
        _validate_input_class(
            "Probe",
            hostile,
            attr_name="input_class",
            model=product_models.Item,
            fields=None,
            exclude=None,
        )


class _HostileHashStr(str):
    """A str subclass whose __hash__ raises (hostile-Meta truthful-read parity test)."""

    @override
    def __hash__(self) -> int:
        raise RuntimeError("hostile hash")


def test_django_mutation_validate_meta_reads_a_hostile_hash_operation_as_its_text() -> None:
    """DjangoMutation._validate_meta reads ``Meta.operation`` as the plain text it spells.

    A str subclass's ``__hash__`` may raise; the membership test runs over the exact
    ``str`` copy ``truth.text`` makes, so the override never runs and the operation is
    the ``create`` it spells.
    """
    _declare_products_primaries()

    class HashOpMutation(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = _HostileHashStr("create")

    operation = HashOpMutation._mutation_meta.operation
    assert operation == "create"
    assert type(operation) is str


def test_django_mutation_input_type_name_delete_operation_raises_typed_reject() -> None:
    """DjangoMutation.input_type_name on a validated delete raises ConfigurationError.

    A direct consumer call to input_type_name on a delete mutation (unusual,
    as the framework gates the data: ref at the field factory) must fail loud
    as a typed ConfigurationError, not a raw KeyError from indexing
    NON_DELETE_OPERATION_INPUT_KIND. The reject mirrors _materialize_input_for's
    .get() delete short-circuit.
    """
    _declare_products_primaries()

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    with pytest.raises(
        ConfigurationError,
        match=(
            r"DjangoMutation DeleteItem declares operation='delete', which is id-only "
            r"and materializes no input"
        ),
    ):
        DeleteItem.input_type_name(DeleteItem._mutation_meta)
