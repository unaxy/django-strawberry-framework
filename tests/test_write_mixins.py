"""Pins for the write-flavor substrate shared by every ``Mutation`` family.

Covers ``django_strawberry_framework/write_mixins.py``: the shared ``Meta``
vocabulary each flavor composes its allowed keys from; the ``Meta`` validation
primitives (``normalize_meta_field_selection``,
``require_subclass`` / ``require_model_class`` / ``require_non_delete_operation``,
``_validate_permission_classes``, ``validate_select_for_update``,
``model_backed_permission_and_lock``), including their hostile-input reads; the
declaration-ledger and ``Meta``-validating metaclass factories; the sealed
validated snapshot and the sealed ``_mutation_meta`` head; and the shared
phase-2.5 drain (``bind_write_declarations`` / ``bind_mutation_outputs``).

Class-creation and bind contracts a request cannot express: every row here
raises or stashes at declaration / finalize time. The flavors' wire behavior is
live in ``examples/fakeshop/test_query/``.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import NoReturn

import pytest
from apps.products import models as product_models
from django import forms
from django.utils.functional import SimpleLazyObject, lazy
from django.utils.translation import gettext_lazy
from typing_extensions import override

from django_strawberry_framework import (
    DjangoModelPermission,
    DjangoMutation,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.sets import (
    _ALLOWED_MODELFORM_META_KEYS,
    _ALLOWED_PLAIN_FORM_META_KEYS,
    DjangoFormMutation,
    bind_form_mutations,
)
from django_strawberry_framework.mutations.inputs import _materialized_names
from django_strawberry_framework.mutations.sets import _ALLOWED_MUTATION_META_KEYS, bind_mutations
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework.sets import _ALLOWED_SERIALIZER_META_KEYS
from django_strawberry_framework.write_mixins import (
    COMMON_WRITE_META_KEYS,
    MODEL_BACKED_WRITE_META_KEYS,
    DeclarationRegistry,
    _validate_permission_classes,
    _ValidatedMutationMeta,
    backing_model_of,
    bind_mutation_outputs,
    bind_write_declarations,
    make_declaration_registry,
    make_meta_validating_metaclass,
    model_backed_permission_and_lock,
    normalize_meta_field_selection,
    require_model_class,
    require_non_delete_operation,
    require_subclass,
    validate_select_for_update,
)


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry, co-clearing every mutation ledger and the shape build caches."""
    registry.clear()
    yield
    registry.clear()


def _create_item_mutation() -> type[DjangoMutation]:
    """A ``create`` ``DjangoMutation`` over the products ``Item`` model."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    return CreateItem


def _meta_class(**attrs: object) -> type[object]:
    """A ``Meta`` class carrying exactly ``attrs``, the shape ``_validate_meta`` reads."""
    return type("Meta", (), attrs)


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


class _HostileRepr:
    @override
    def __repr__(self) -> str:
        raise RuntimeError("HostileRepr exploded")

    @override
    def __str__(self) -> str:
        raise RuntimeError("HostileRepr str exploded")


class _HostilePermMeta(type):
    @property
    def has_permission(cls) -> NoReturn:
        raise RuntimeError("HostilePermMeta.has_permission exploded")


class _HostileHashStr(str):
    """A str subclass whose __hash__ raises (hostile-Meta truthful-read parity test)."""

    @override
    def __hash__(self) -> int:
        raise RuntimeError("hostile hash")


def test_write_flavor_meta_vocabulary_composition() -> None:
    """All write flavors compose their allowed Meta keys from the mutation foundation vocabulary."""
    assert frozenset({"fields", "exclude", "permission_classes"}) == COMMON_WRITE_META_KEYS
    assert (
        COMMON_WRITE_META_KEYS | frozenset({"operation", "select_for_update"})
    ) == MODEL_BACKED_WRITE_META_KEYS
    assert (
        MODEL_BACKED_WRITE_META_KEYS
        | frozenset(
            {"model", "input_class", "partial_input_class"},
        )
    ) == _ALLOWED_MUTATION_META_KEYS
    assert (
        MODEL_BACKED_WRITE_META_KEYS
        | frozenset(
            {
                "form_class",
            },
        )
    ) == _ALLOWED_MODELFORM_META_KEYS
    assert (
        COMMON_WRITE_META_KEYS
        | frozenset(
            {
                "form_class",
            },
        )
    ) == _ALLOWED_PLAIN_FORM_META_KEYS
    assert (
        MODEL_BACKED_WRITE_META_KEYS
        | frozenset(
            {
                "serializer_class",
                "optional_fields",
                "injected_fields",
                "nested_fields",
            },
        )
    ) == _ALLOWED_SERIALIZER_META_KEYS


def test_make_declaration_registry_dedupes_and_rejects_post_finalize() -> None:
    """The factory-built declaration registry dedupes and rejects post-finalize.

    The ``make_declaration_registry`` factory single-sources the dedup / clear /
    post-finalize reject; a fresh registry over a disjoint list still dedupes by
    identity and rejects a declaration after finalization.
    """
    reg: DeclarationRegistry[type[object]] = make_declaration_registry("ProbeFlavor")

    class Probe:
        pass

    reg.register(Probe)
    reg.register(Probe)  # identity dedup
    assert reg.store.count(Probe) == 1
    assert reg.iter_() == (Probe,)

    reg.clear()
    assert reg.iter_() == ()

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Item) is ItemType

    finalize_django_types()
    with pytest.raises(ConfigurationError, match=r"ProbeFlavor .* after finalization"):
        reg.register(Probe)


def test_make_meta_validating_metaclass_validates_registers_and_skips_abstract() -> None:
    """The metaclass factory single-sources validate-then-register over a register callback.

    ``make_meta_validating_metaclass`` is the spec-038 Decision 13 twin of
    ``make_declaration_registry``: a fresh metaclass over a probe register still
    skips a no-``Meta`` base, validates + registers a concrete subclass, and keeps
    ledgers disjoint when two metaclasses close over different registers.
    """
    ledger_a: list[type] = []
    ledger_b: list[type] = []
    MetaA = make_meta_validating_metaclass(ledger_a.append, name="MetaA", module=__name__)
    MetaB = make_meta_validating_metaclass(ledger_b.append, name="MetaB", module=__name__)

    # The factory pins the produced class's identity to the caller-supplied
    # name/module rather than leaking the function-local ``MetaValidatingMetaclass``
    # ``__qualname__``.
    assert (MetaA.__name__, MetaA.__qualname__, MetaA.__module__) == ("MetaA", "MetaA", __name__)
    assert (MetaB.__name__, MetaB.__qualname__, MetaB.__module__) == ("MetaB", "MetaB", __name__)

    class BaseA(metaclass=MetaA):
        _mutation_meta = None

        @classmethod
        def _validate_meta(cls, _meta: type) -> str:
            return f"a:{cls.__name__}"

    class BaseB(metaclass=MetaB):
        _mutation_meta = None

        @classmethod
        def _validate_meta(cls, _meta: type) -> str:
            return f"b:{cls.__name__}"

    class AbstractA(BaseA):
        pass

    assert AbstractA._mutation_meta is None
    assert ledger_a == []

    class ConcreteA(BaseA):
        class Meta:
            pass

    class ConcreteB(BaseB):
        class Meta:
            pass

    assert ConcreteA._mutation_meta == "a:ConcreteA"
    assert ConcreteB._mutation_meta == "b:ConcreteB"
    assert ledger_a == [ConcreteA]
    assert ledger_b == [ConcreteB]


def test_require_subclass_accepts_expected_and_rejects_with_rendered_value() -> None:
    """The shared Meta type-gate returns the class or raises naming the rendered value."""

    class Expected:
        pass

    class Child(Expected):
        pass

    assert (
        require_subclass(
            "Probe",
            Child,
            base_label="ProbeBase",
            key="backing",
            expected=Expected,
            expected_label="Expected",
        )
        is Child
    )

    with pytest.raises(ConfigurationError) as exc:
        require_subclass(
            "Probe",
            "Expected",
            base_label="ProbeBase",
            key="backing",
            expected=Expected,
            expected_label="Expected",
        )
    assert str(exc.value) == (
        "ProbeBase Probe.Meta.backing must be a Expected subclass; got 'Expected'."
    )

    with pytest.raises(ConfigurationError, match=r"belongs on OtherBase"):
        require_subclass(
            "Probe",
            object,
            base_label="ProbeBase",
            key="backing",
            expected=Expected,
            expected_label="Expected",
            note="(A plain value belongs on OtherBase.)",
        )


def test_require_non_delete_operation_accepts_create_update_and_rejects_delete() -> None:
    """The shared create/update lookup is the membership test both model-backed flavors use."""
    assert (
        require_non_delete_operation("ProbeBase", "Probe", _meta_class(operation="create"))
        == "create"
    )
    assert (
        require_non_delete_operation("ProbeBase", "Probe", _meta_class(operation="update"))
        == "update"
    )
    with pytest.raises(ConfigurationError, match="operation must be one of"):
        require_non_delete_operation("ProbeBase", "Probe", _meta_class(operation="delete"))
    with pytest.raises(ConfigurationError, match="operation must be one of"):
        require_non_delete_operation("ProbeBase", "Probe", _meta_class())


def test_require_model_class_accepts_model_and_rejects_string_or_instance() -> None:
    """The shared model-class gate returns the model or raises at class-creation wording."""
    assert (
        require_model_class("Probe", product_models.Item, base_label="ProbeBase")
        is product_models.Item
    )
    with pytest.raises(ConfigurationError, match="must be a Django model class"):
        require_model_class("Probe", "Item", base_label="ProbeBase")
    with pytest.raises(ConfigurationError, match="must be a Django model class"):
        require_model_class("Probe", product_models.Item(), base_label="ProbeBase")


def test_normalize_meta_field_selection_returns_normalized_pair() -> None:
    """The shared fields/exclude pair normalizes both keys with one flavor label."""
    assert normalize_meta_field_selection(
        _meta_class(fields=["name"], exclude=None),
        flavor="DjangoMutation",
    ) == (("name",), None)
    with pytest.raises(ConfigurationError, match="not a bare string"):
        normalize_meta_field_selection(
            _meta_class(fields="name", exclude=None),
            flavor="DjangoMutation",
        )


def test_model_backed_permission_and_lock_defaults_and_explicit_opt_out() -> None:
    """Model-backed flavors share the DjangoModelPermission default + FOR UPDATE pair."""
    classes, lock = model_backed_permission_and_lock(
        "Probe",
        _meta_class(),
        flavor="DjangoMutation",
    )
    assert classes == (DjangoModelPermission,)
    assert lock is True

    classes, lock = model_backed_permission_and_lock(
        "Probe",
        _meta_class(select_for_update=False, permission_classes=[]),
        flavor="DjangoMutation",
    )
    assert classes == ()
    assert lock is False


def test_bind_mutation_outputs_stashes_model_less_payload_and_slots() -> None:
    """The shared payload stash writes the three bind-output slots both ledgers fill."""

    class ProbeForm(forms.Form):
        name = forms.CharField()

    class BindOutputsProbe(DjangoFormMutation):
        class Meta:
            form_class = ProbeForm
            permission_classes = []

    input_cls = BindOutputsProbe.build_input(BindOutputsProbe._mutation_meta)
    bind_mutation_outputs(BindOutputsProbe, input_cls=input_cls, object_type=None)
    assert BindOutputsProbe._primary_type is None
    assert BindOutputsProbe._input_class is input_cls
    assert BindOutputsProbe._payload_type_name == "BindOutputsProbePayload"
    assert "BindOutputsProbePayload" in _materialized_names


def test_backing_model_of_refuses_a_model_less_snapshot() -> None:
    """Only a model-backed snapshot names a model; the plain form flavor's is a ``TypeError``."""

    class ProbeForm(forms.Form):
        name = forms.CharField()

    class ModelLessProbe(DjangoFormMutation):
        class Meta:
            form_class = ProbeForm
            permission_classes = []

    assert ModelLessProbe._mutation_meta.model is None
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        _ = backing_model_of(ModelLessProbe._mutation_meta)


def test_model_and_plain_form_binds_ride_bind_mutation_outputs() -> None:
    """Both declaration-ledger drains stash payload + slots through one shared drain."""
    # Both public drains delegate to the one shared body ...
    assert "bind_write_declarations" in bind_mutations.__code__.co_names
    assert "bind_write_declarations" in bind_form_mutations.__code__.co_names
    assert bind_form_mutations.__globals__["bind_write_declarations"] is bind_write_declarations
    # ... which is the single site stashing payload + slots.
    assert "bind_mutation_outputs" in bind_write_declarations.__code__.co_names


@pytest.mark.parametrize("invalid_op", _UNHASHABLE_AND_NON_STRING_OPERATIONS)
def test_require_non_delete_operation_rejects_unhashable_and_non_string_operation(
    invalid_op: object,
) -> None:
    """require_non_delete_operation raises ConfigurationError for unhashable or non-string operations."""
    with pytest.raises(
        ConfigurationError,
        match=r"Meta\.operation must be one of \['create', 'update'\]; got ",
    ):
        require_non_delete_operation(
            "DjangoModelFormMutation",
            "BadOpMutation",
            _meta_class(operation=invalid_op),
        )


def test_require_model_class_hostile_repr_propagates() -> None:
    """The rejection renders the value through its own ``__repr__``; what that raises propagates."""
    hostile = _HostileRepr()
    with pytest.raises(RuntimeError, match="HostileRepr exploded"):
        require_model_class("Probe", hostile, base_label="DjangoMutation")


def test_validate_select_for_update_hostile_repr_propagates() -> None:
    """The non-bool rejection renders the value through its own ``__repr__``; it propagates."""
    hostile = _HostileRepr()

    class BadMeta:
        select_for_update = hostile

    with pytest.raises(RuntimeError, match="HostileRepr exploded"):
        validate_select_for_update("DjangoMutation", "Probe", BadMeta)


def test_validate_permission_classes_hostile_metaclass_never_runs() -> None:
    """A metaclass ``has_permission`` property is read as stored, never run, and refused.

    The declaration is read from the real namespaces (``truth.static_attr``): the
    property object is not callable, so the entry is no permission class.
    """

    class HostilePerm(metaclass=_HostilePermMeta):
        pass

    with pytest.raises(
        ConfigurationError,
        match=r"permission_classes entry .* is not a permission class exposing has_permission",
    ):
        _validate_permission_classes("Probe", [HostilePerm])


def test_validate_permission_classes_custom_base_label_and_flavor_forwarding() -> None:
    """_validate_permission_classes and model_backed_permission_and_lock format with base_label."""
    with pytest.raises(
        ConfigurationError,
        match=(
            r"CustomFlavor BadPermsMutation\.Meta\.permission_classes must be a sequence "
            r"of permission classes"
        ),
    ):
        _validate_permission_classes("BadPermsMutation", "bad_sequence", base_label="CustomFlavor")

    with pytest.raises(
        ConfigurationError,
        match=(
            r"CustomFlavor BadPermsMutation\.Meta\.permission_classes entry 123 is not a "
            r"permission class exposing has_permission"
        ),
    ):
        _validate_permission_classes("BadPermsMutation", [123], base_label="CustomFlavor")

    with pytest.raises(
        ConfigurationError,
        match=(
            r"DjangoModelFormMutation BadPermsMutation\.Meta\.permission_classes entry "
            r"123 is not a permission class exposing has_permission"
        ),
    ):
        model_backed_permission_and_lock(
            "BadPermsMutation",
            _meta_class(permission_classes=[123]),
            flavor="DjangoModelFormMutation",
        )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("DjangoModelPermission", id="str"),
        pytest.param(b"DjangoModelPermission", id="bytes"),
        pytest.param(bytearray(b"DjangoModelPermission"), id="bytearray"),
        pytest.param(memoryview(b"DjangoModelPermission"), id="memoryview"),
        pytest.param(gettext_lazy("DjangoModelPermission"), id="lazy-translation"),
        pytest.param(
            SimpleLazyObject(lambda: gettext_lazy("DjangoModelPermission")),
            id="simple-lazy-over-lazy",
        ),
        pytest.param(SimpleLazyObject(lambda: "DjangoModelPermission"), id="simple-lazy-str"),
        pytest.param(lazy(lambda: [DjangoModelPermission], list)(), id="lazy-translation-list"),
    ],
)
def test_validate_permission_classes_refuses_a_text_atom_as_a_sequence(value: object) -> None:
    """A text atom is one name, never a sequence of permission classes.

    Iterated, it would surface a misleading per-character "entry 'D' is not a permission
    class". A lazy translation string walks its text the same way, a ``SimpleLazyObject`` is
    read as the object it stands for, and every lazy ``Promise`` is text whatever result
    class it wraps, so a lazy list is refused with it.
    """
    with pytest.raises(
        ConfigurationError,
        match=r"Probe\.Meta\.permission_classes must be a sequence of permission classes",
    ):
        _validate_permission_classes("Probe", value)


def test_validate_permission_classes_reads_a_simple_lazy_list_as_the_list() -> None:
    """A ``SimpleLazyObject`` over a list of classes is that list."""
    assert _validate_permission_classes(
        "Probe",
        SimpleLazyObject(lambda: [DjangoModelPermission]),
    ) == (DjangoModelPermission,)


def test_require_non_delete_operation_reads_a_hostile_hash_operation_as_its_text() -> None:
    """The shared non-delete check also reads the operation as plain text, never hashing it."""
    operation = require_non_delete_operation(
        "SerializerMutation",
        "HashOpMutation",
        _meta_class(operation=_HostileHashStr("create")),
    )
    assert operation == "create"
    assert type(operation) is str


def test_make_declaration_registry_identity_dedup_hostile_eq_safe_containment() -> None:
    """make_declaration_registry dedupes by identity, not __eq__, avoiding hostile metaclass escapes.

    The register ledger's ``list.__contains__`` dispatches each entry's __eq__
    (a consumer-supplied metaclass may override with a raising body), so an
    ``is`` identity scan replaces the ``not in`` check. This keeps hostile
    __eq__ from escaping as a raw RuntimeError at class registration.
    """
    reg: DeclarationRegistry[type[object]] = make_declaration_registry("ProbeRegistry")

    class HostileEqMeta(type):
        @override
        def __eq__(cls, other: object) -> bool:
            raise RuntimeError("hostile eq")

        # basedpyright: None is the runtime marker for unhashable; typeshed types the slot as a method
        __hash__ = None  # pyright: ignore[reportAssignmentType]

    class FirstClass:
        pass

    class SecondClass(metaclass=HostileEqMeta):
        pass

    reg.register(FirstClass)
    # No RuntimeError: identity scan, not equality check.
    reg.register(SecondClass)
    assert len(reg.store) == 2

    # Re-register the same object (identity) is deduplicated silently.
    reg.register(FirstClass)
    assert len(reg.store) == 2


def test_whole_record_swap_and_deletion_on_a_real_mutation_class_are_sealed() -> None:
    """A mutation class's validated ``_mutation_meta`` head refuses reassignment and deletion.

    The metaclass guard (``make_meta_validating_metaclass.__setattr__`` /
    ``__delattr__``) refuses a post-creation rebind or deletion of
    ``_mutation_meta`` through those methods: a ``has_permission`` hook receives
    the mutation class, so an unguarded head would let one request replace the validated record
    wholesale with a hook-chosen namespace (the empty allow-any posture) - the
    persistent cross-request bypass the snapshot's own seal closes at the slot
    level. Creation time is the one honored write, so the guards are unreachable
    from a live request and are earned here at the unit tier. Related bind
    outputs (``_primary_type`` etc.) are unaffected.
    """
    sealed = _create_item_mutation()
    original = sealed._mutation_meta
    hook_chosen = SimpleNamespace(permission_classes=())
    with pytest.raises(ConfigurationError, match="sealed and cannot be rebound"):
        # basedpyright: the hook-chosen namespace is the hostile rebind under test; the slot is
        # typed as the validated record
        sealed._mutation_meta = hook_chosen  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(ConfigurationError, match="sealed and cannot be deleted"):
        del sealed._mutation_meta
    # The validated record survived both attempts, record identity included.
    assert isinstance(sealed._mutation_meta, _ValidatedMutationMeta)
    assert sealed._mutation_meta is original
    assert sealed._mutation_meta.permission_classes == (DjangoModelPermission,)
    # Unrelated class attributes (the bind's outputs) stay writable and deletable:
    # the head seal narrows ONLY the ``_mutation_meta`` head.
    sealed._primary_type = DjangoType
    assert sealed._primary_type is DjangoType
    del sealed._primary_type
    assert "_primary_type" not in sealed.__dict__


def test_validated_mutation_meta_record_refuses_slot_writes_and_deletes() -> None:
    """The validated snapshot's own slots are sealed once ``__init__`` finishes.

    Mirrors the head seal at the record level: the record is the per-request
    authorization source (``run_permission_classes`` reads
    ``type(self)._mutation_meta.permission_classes``), so a sealed record's own
    ``__setattr__`` / ``__delattr__`` refuse attribute reassignment and deletion. A
    consumer who needs different authorization declares a new mutation class.
    """
    snapshot = _create_item_mutation()._mutation_meta
    with pytest.raises(ConfigurationError, match="sealed"):
        snapshot.permission_classes = ()
    with pytest.raises(ConfigurationError) as excinfo:
        del snapshot.permission_classes
    assert str(excinfo.value) == (
        "The validated mutation Meta snapshot is sealed; attributes cannot be deleted. "
        "Authorization configuration is captured once at class creation."
    )
    with pytest.raises(ConfigurationError, match="sealed and 'model' cannot be reassigned"):
        snapshot.model = None
    # The validated configuration is untouched by all three attempts.
    assert snapshot.permission_classes == (DjangoModelPermission,)
    assert snapshot.operation == "create"
