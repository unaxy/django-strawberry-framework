"""Form-derived ``@strawberry.input`` generation substrate.

Pure, finalizer-free machinery: given a Django ``Form`` / ``ModelForm`` class +
an operation kind + the effective field set (after ``Meta.fields`` /
``Meta.exclude``), it builds the ``<FormClass>Input`` (create) /
``<FormClass>PartialInput`` (update) ``@strawberry.input`` classes from the
form's declared ``base_fields``. No metaclass, no resolver, no finalizer wiring
lives here - the ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases and
the phase-2.5 bind live in ``sets.py``, the resolver pipeline in
``resolvers.py``. The generators here are callable and unit-testable in
isolation; the bind calls them.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.forms.inputs")`` resolves through
``module.__dict__`` (the same contract ``mutations/inputs.py`` /
``orders/inputs.py`` rely on). ``materialize_form_input_class`` /
``clear_form_input_namespace`` own that lifecycle.

The shape is the ``036`` discipline adapted to forms (spec-038 Decision 7):

- The input derives from the **form's declared fields** (``form_class.base_fields``,
  the stable class-level set - read with NO instantiation, so a kwarg-requiring
  form still has a discoverable shape), not the model's editable columns.
- Where a ``ModelForm`` field has a backing model column, the annotation routes
  through ``model_column_input_annotation`` so the wire contract is symmetric
  with the read ``DjangoType``; a choice field whose static choices admit fewer of
  a choice column's values than the column lists publishes a generated enum of the
  admitted values instead (``_form_choice_narrowing``). A plain ``Form`` field with
  no column uses ``converter.convert_form_field`` (the model-less table). The two key spaces
  (``forms.Field`` / ``models.Field``) stay strictly separate: the column is
  resolved first, then handed to the ``models.Field``-keyed converters.
- Shape identity is ``(form_class, operation_kind, frozenset(effective field
  names), basis content projection)`` keyed on the FORM CLASS OBJECT (not its
  ``__name__``; the projection is :func:`_form_basis_content_identity`); the canonical
  ``<FormClass>Input`` / ``<FormClass>PartialInput`` name for the full shape and
  a deterministic shape-derived name for a narrowing. Identical shapes dedupe;
  two distinct shapes on one name raise ``ConfigurationError`` at finalization -
  for free from the ``utils/inputs.py`` materialize ledger.

The materialize / build / camel-name / token-name mechanics are single-sited in
``utils/inputs.py`` / ``mutations/inputs.py``; this module is a thin domain
wrapper, in the spirit of ``mutations/inputs.py``.
"""

from __future__ import annotations

from types import GenericAlias
from typing import TYPE_CHECKING, Any, cast

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.choices import CallableChoiceIterator

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import (
    CREATE,
    PARTIAL,
    annotate_queryset_relation,
    model_column_input_annotation,
    model_column_write_kind,
)
from django_strawberry_framework.registry import register_subsystem_clear, registry
from django_strawberry_framework.scalars import Upload
from django_strawberry_framework.types.converters import (
    array_element_field,
    build_enum_from_choices,
    choice_column_pairs,
    choice_enum_name,
)
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import dict_of, is_str, read_attr
from django_strawberry_framework.utils.inputs import (
    InputFieldSpec,
    build_strawberry_input_class,
    guard_dropped_required,
    is_input_attribute_name,
    iter_input_field_collisions,
    make_input_namespace,
    name_set_input_type_name,
    optional_input_field,
    resolve_effective_fields,
)
from django_strawberry_framework.utils.relations import (
    is_forward_concrete_relation,
    is_forward_many_to_many,
    is_model_class,
    non_pk_relation_key_attname,
)
from django_strawberry_framework.utils.strings import graphql_camel_name

from .converter import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    convert_form_field,
    form_field_required,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from typing import TypeAlias

    from django_strawberry_framework.utils.typing import ConcreteField

    # A declarative form class - the only kind a form mutation's ``Meta.form_class``
    # validates to (``forms.Form`` / ``forms.ModelForm`` are siblings under
    # ``forms.BaseForm``, and only they carry the metaclass-built ``base_fields``).
    # ``ModelForm``'s model parameter is invariant in the stubs, so ``Any`` is the one
    # argument a consumer's ``ModelForm[Item]`` satisfies.
    # basedpyright: invariant model TypeVar; a consumer's ModelForm[Item] must be accepted
    FormClass: TypeAlias = type[forms.Form | forms.ModelForm[Any]]  # pyright: ignore[reportExplicitAny]
    #: Any ``ModelChoiceField``: its model parameter is read-only here.
    _ModelChoiceFieldAny: TypeAlias = forms.ModelChoiceField[models.Model]
    _ModelMultipleChoiceFieldAny: TypeAlias = forms.ModelMultipleChoiceField[models.Model]
else:
    # ``ModelChoiceField`` has no ``__class_getitem__`` at runtime: the hint stays the class.
    _ModelChoiceFieldAny = forms.ModelChoiceField
    _ModelMultipleChoiceFieldAny = forms.ModelMultipleChoiceField

# The multi-valued relation field class with its model parameter solved, so the
# real-class check against it answers over a known type.
_MODEL_MULTIPLE_CHOICE_FIELD: type[_ModelMultipleChoiceFieldAny] = forms.ModelMultipleChoiceField
_MODEL_CHOICE_FIELD: type[_ModelChoiceFieldAny] = forms.ModelChoiceField

# Module path the ``strawberry.lazy(...)`` marker references for the FORM input
# namespace; pinned as a single constant so any forward-ref and
# ``materialize_form_input_class`` stay in sync. A namespace distinct from
# ``mutations.inputs`` so the ``036`` ``<Model>Input`` and the form
# ``<FormClass>Input`` never share a module ``__dict__`` slot. Mirrors
# ``mutations/inputs.py::INPUTS_MODULE_PATH``.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.forms.inputs"

# The fixed operation-kind sentinel for a plain ``DjangoFormMutation`` (no model
# operation). The ``036`` ``CREATE`` / ``PARTIAL`` constants (reused from
# ``mutations.inputs``) drive the create-vs-partial GENERATOR split; ``FORM`` is
# the shape-identity component a plain ``DjangoFormMutation`` carries in place of
# a ``"create"`` / ``"update"`` model operation, so a plain form's input cache
# key ``(form_class, "form", effective set, basis content)`` is well-defined (spec-038
# Decision 7). The bind keys on it; the generators here do not branch on it.
FORM: str = "form"

# The create-shaped operation kinds (everything that is NOT ``PARTIAL``): a
# ``DjangoModelFormMutation`` create (``CREATE``) and a plain
# ``DjangoFormMutation`` (``FORM``). The generator's only behavioral split is
# create-shaped vs ``PARTIAL`` (the latter widens model-backed fields to
# optional), so this names the create-shaped set in one place. ``CREATE`` /
# ``PARTIAL`` are re-exported from ``mutations.inputs`` so callers + tests
# address the form generator's full kind vocabulary on this module.
CREATE_SHAPED_KINDS: frozenset[str] = frozenset({CREATE, FORM})

# The form-input namespace lifecycle trio, single-sited via
# ``utils/inputs.py::make_input_namespace`` (spec-039 - the one-ledger shape
# the mutation, form, and serializer flavors share). ``_materialized_names`` is
# the ``name -> input_class`` ledger ``materialize_form_input_class`` writes;
# ``registry.clear()`` routes through
# ``clear_form_input_namespace`` to reset it - a namespace disjoint from
# ``mutations.inputs`` so the ``036`` ``<Model>Input`` and the form
# ``<FormClass>Input`` never share a module ``__dict__`` slot. The public
# ``materialize_*`` / ``clear_*`` names below stay thin wrappers so callers + tests
# address them unchanged.
_materialized_names, _materialize_input, _clear_input_namespace = make_input_namespace(
    INPUTS_MODULE_PATH,
    "DjangoFormMutation",
)


def materialize_form_input_class(name: str, input_cls: type[object]) -> None:
    """Set ``input_cls`` as a real module global of ``forms.inputs`` under ``name``.

    Thin family wrapper over the ``make_input_namespace`` materializer (which
    delegates to ``utils/inputs.py::materialize_generated_input_class`` pinning
    the form-side module path, family label, and ledger). See that helper for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, input_cls)``
    idempotency clause (re-materializing the same class under the same name is a
    no-op, so identical shapes dedupe), and the distinct-class collision raise (a
    second, DIFFERENT class under one name raises ``ConfigurationError`` - the
    spec-038 finalize-time collision raise, including two different form classes
    sharing a ``__name__``, which can never dedupe because they are distinct
    ``form_class`` identities).

    Defined here; called by the phase-2.5 bind.
    """
    _materialize_input(name, input_cls)


def clear_form_input_namespace() -> None:
    """Reset the form-input ledger for a fresh build.

    Clears ``_materialized_names`` (via the ``make_input_namespace`` clear) so
    ``materialize_form_input_class`` re-emits on the next finalize. Materialized
    class objects stay parked in ``forms.inputs.__dict__`` per the
    parked-globals lifecycle stated on
    ``utils/inputs.py::make_input_namespace``.

    Like ``clear_mutation_input_namespace`` (and unlike the set families' clear),
    this resets only the module-level ledger it owns - the form subsystem has no
    arguments-factory cache and no per-set ``_lifecycle`` binding state. Wired
    into ``registry.clear()`` (spec-038).
    """
    _clear_input_namespace()


# Register the form input-namespace clear as a canonical PRE-BIND clear (spec-039):
# the ``finalize_django_types`` pre-bind reset AND ``TypeRegistry.clear()``
# both iterate ``registry.iter_subsystem_clears()``. This owner registers the
# executable callback once; the stable owner key makes reload replace it without
# a central attribute lookup that can drift.
register_subsystem_clear(
    clear_form_input_namespace,
    owner="forms.input_namespace",
    before_bind=True,
)


def get_form_fields(form_class: FormClass) -> dict[str, forms.Field]:
    """Return the form's declared field dict from ``base_fields`` - NO instantiation.

    ``base_fields`` is the class-level declared-fields dict Django's
    ``DeclarativeFieldsMetaclass`` / ``ModelFormMetaclass`` populate at class
    creation (for a ``ModelForm`` it already includes the model-derived fields).
    Reading it needs no ``form_class()`` call, so a form whose ``__init__``
    requires constructor kwargs (``user``, ``request``, a tenant) still has a
    discoverable, request-independent stable field shape (spec-038 Decision 7). The overridable
    ``get_form_fields(cls)`` classmethod on the base delegates here for its
    default; this module ships the module-level discovery function only.

    A consumer having clobbered ``base_fields`` to a value ``dict()`` cannot
    read (its documented ``TypeError`` / ``ValueError``) raises a typed
    ``ConfigurationError`` naming the form (the bind's default hook delegates
    here, so a corrupted basis never escapes the schema-time build raw).
    """
    try:
        # The form metaclass stores ``base_fields`` as the name-keyed ``Field`` map; a
        # clobbered value fails ``dict()`` and is reported below.
        return dict(
            cast("Mapping[str, forms.Field]", truth.static_attr(form_class, "base_fields", None)),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"DjangoFormMutation for {truth.name(form_class)} get_form_fields() must return "
            "a mapping of field names to forms.Field instances.",
        ) from exc


def _form_field_basis(form_class: FormClass, form_fields: object = None) -> dict[str, forms.Field]:
    """Return the validated field basis used by every form-input operation.

    ``form_fields`` is the optional stable mapping supplied by a mutation's
    ``get_form_fields`` hook. Direct generator callers omit it and use the
    form's class-level ``base_fields`` through ``get_form_fields``. Copying the
    mapping keeps later narrowing/build passes from observing caller mutation,
    while the hook remains responsible for returning a request-independent
    field representation. A hook mapping ``dict()`` cannot read (its documented
    ``TypeError`` / ``ValueError``) raises the same typed diagnostic
    ``get_form_fields`` raises for a corrupted ``base_fields``.
    """
    source = get_form_fields(form_class) if form_fields is None else form_fields
    try:
        basis = dict_of(source)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"DjangoFormMutation for {truth.name(form_class)} get_form_fields() must return "
            "a mapping of field names to forms.Field instances.",
        ) from exc
    # A field name becomes a generated input attribute, so a name
    # ``is_input_attribute_name`` refuses is reported here instead of failing the build.
    # ``base_fields`` keys are always identifiers (declared form attributes / model
    # columns), so this rejects only hook names that could never have built an input.
    invalid_names: list[object] = []
    invalid_fields: list[object] = []
    valid: dict[str, forms.Field] = {}
    for name, field in basis.items():
        valid_name = is_input_attribute_name(name)
        if not valid_name:
            invalid_names.append(name)
        # The same hook can map a name to any value.
        if not truth.is_instance(field, forms.Field):
            invalid_fields.append(name)
        elif valid_name:
            valid[name] = field
    if invalid_names or invalid_fields:
        # The per-entry join keeps the benign ``['a', 'b']`` list-repr byte shape.
        raise ConfigurationError(
            f"DjangoFormMutation for {truth.name(form_class)} get_form_fields() must return "
            "a mapping of string names to forms.Field instances; invalid names "
            f"[{', '.join(truth.render(name) for name in invalid_names)}], invalid "
            f"fields [{', '.join(truth.render(name) for name in invalid_fields)}].",
        )
    return valid


def normalize_form_field_basis(
    form_class: FormClass,
    form_fields: object,
) -> dict[str, forms.Field]:
    """Normalize a mutation hook's returned field basis with typed diagnostics."""
    if form_fields is None:
        raise ConfigurationError(
            f"DjangoFormMutation for {truth.name(form_class)} get_form_fields() must return "
            "a mapping of field names to forms.Field instances, not None.",
        )
    return _form_field_basis(form_class, form_fields)


def _related_model_of(field: forms.Field) -> object:
    """Return a column-less relation field's ``queryset.model``, or ``None``.

    The annotation input the build reads through
    ``_model_less_relation_annotation`` (``annotate_queryset_relation(
    field.queryset, ...)``). A field without a ``queryset`` attribute (every
    scalar) and a queryset-less field (the request-scoped-choices idiom, whose
    build-time annotation raises its own typed error when emitted) project
    ``None``.
    """
    return getattr(getattr(field, "queryset", None), "model", None)


def _form_basis_content_identity(
    form_class: FormClass,
    form_fields: Mapping[str, forms.Field] | None = None,
) -> tuple[tuple[str, type[forms.Field], bool, object, object], ...]:
    """Return a hashable projection of the hook basis that determines input content.

    The per-shape build cache (``forms/sets.py::_cached_build_form_input``) keys
    on the shape identity ``(form_class, operation_kind, effective field set,
    THIS projection)``. The projection captures every per-field quantity the
    build consumes - the converter-dispatch type (``type(field)``, the MRO walk
    in ``convert_form_field``), the ONE requiredness decision
    (``converter.form_field_required`` with the field's backing column, the
    same resolution the build site uses), a column-less relation field's
    related model (``_related_model_of``, which fixes the
    Relay-``GlobalID``-vs-raw-pk id annotation), and the column values a choice
    field narrows its published enum to (``_choice_narrowing_identity``) - so
    two calls with identical projections build identical input classes and
    MUST dedupe onto one class object (the per-shape dedupe contract: two mutations over one form +
    effective set reuse one input, however their bases were produced - the
    default hook, one hook shared on an intermediate base, or two different
    hook functions), while any content difference (a stateful
    ``get_form_fields`` hook returning a different requiredness per class, a
    swapped queryset model) lands on a distinct key, builds separately, and
    stays LOUD at the materialize ledger instead of silently sharing a wrong
    shape. Field-instance identity is deliberately NOT part of the projection
    (bases are rebuilt per call); the content tuple is the stable quantity.

    ``form_fields`` is the (already normalized or ``None``) hook basis; ``None``
    resolves through ``get_form_fields`` exactly as the build does, so a
    malformed basis raises the same typed ``ConfigurationError`` the build
    raises.
    """
    basis = _form_field_basis(form_class, form_fields)
    return tuple(_basis_field_identity(form_class, name, field) for name, field in basis.items())


def _basis_field_identity(
    form_class: FormClass,
    name: str,
    field: forms.Field,
) -> tuple[str, type[forms.Field], bool, object, object]:
    """Return one basis field's ``_form_basis_content_identity`` entry.

    The backing column is resolved once and shared by the requiredness decision and the
    choice-narrowing projection, the same resolution ``_field_triple_and_spec`` receives.
    """
    column = _model_column_for(form_class, name)
    return (
        name,
        type(field),
        form_field_required(field, column=column),
        _related_model_of(field),
        _choice_narrowing_identity(name, field, column, form_class),
    )


def resolve_effective_form_fields(
    form_class: FormClass,
    *,
    fields: object = None,
    exclude: object = None,
    form_fields: Mapping[str, forms.Field] | None = None,
    operation_kind: str | None = None,
) -> dict[str, forms.Field]:
    """Return the effective ``{name: forms.Field}`` dict after ``fields`` / ``exclude``.

    Normalizes + fail-loud validates the narrowing against the form's
    ``base_fields`` (spec-038 Decision 7):

    - ``fields`` and ``exclude`` are mutually exclusive;
    - each is normalized (bare-string / duplicate rejection);
    - a name in neither ``base_fields`` raises ``ConfigurationError`` naming the
      unknown field (a typo like ``fields = ("emial",)`` fails loud, never
      silently shrinks the input);
    - an empty effective set (``fields = ()``, an ``exclude`` dropping every
      field, or a form with no fields) raises ``ConfigurationError`` (the ``036``
      empty-input guard applied to ``base_fields``).

    Preserves ``base_fields`` declaration order for the non-narrowed and the
    ``exclude`` cases; honors the caller's order for ``fields``.

    For the ``PARTIAL`` (update) ``operation_kind`` the basis leaves out every field
    that writes the row's primary key (``_form_row_identity``): an omitted field is
    rebound from the located row by the partial reconstruction, so the bound form
    still validates it, at its stored value. ``None`` (and every create-shaped kind)
    keeps the full basis.

    The narrowing spine + the pinned error wording are single-sited in
    ``utils/inputs.py::resolve_effective_fields``, shared with the
    serializer flavor; this thin wrapper supplies the form basis (``base_fields``)
    and the form-flavor message knobs (the ``seq_flavor`` arg - spec-039).
    """
    return resolve_effective_fields(
        _form_field_basis(form_class, form_fields),
        fields=fields,
        exclude=exclude,
        subject=f"DjangoFormMutation for {truth.name(form_class)}",
        seq_flavor="DjangoFormMutation / DjangoModelFormMutation",
        unknown_noun="unknown form field(s)",
        empty_message=(
            f"DjangoFormMutation input for {truth.name(form_class)} has no fields; "
            "Meta.fields / Meta.exclude narrowed the form field set to empty (or the "
            "form declares no fields). A form input must define at least one field."
        ),
        row_identity=_form_row_identity(
            form_class,
            form_fields,
            operation_kind=operation_kind,
        ),
    )


def _form_row_identity(
    form_class: FormClass,
    form_fields: Mapping[str, forms.Field] | None = None,
    *,
    operation_kind: str | None,
) -> frozenset[str]:
    """Return the form fields an ``operation_kind`` input leaves out as the row's identity.

    Only the ``PARTIAL`` (update) input has any: the declared fields whose backing
    model column (``_model_column_for``) is an editable primary key - a
    ``OneToOneField(primary_key=True)``, a client-assigned text key, or an inherited parent
    key. ``construct_instance`` would assign a provided value to the located instance and
    ``save()`` would then update or insert a different row, so the update input never
    carries it (the model flavor's ``mutations/inputs.py::editable_input_fields`` rule). An
    ``editable=False`` key is no such field: ``construct_instance`` never writes a
    non-editable column, so a declared form field named like one is an ordinary input. A
    create input keeps every field: a client-assigned key is how a create names its row.
    """
    if operation_kind != PARTIAL:
        return frozenset()
    return frozenset(
        name
        for name in _form_field_basis(form_class, form_fields)
        if (column := _model_column_for(form_class, name)) is not None
        and column.primary_key
        and column.editable
    )


def form_input_type_name(
    form_class: FormClass,
    operation_kind: str,
    effective_field_names: tuple[str, ...],
    *,
    full_field_names: tuple[str, ...],
) -> str:
    """Return the generated input-class name for a form shape (spec-038 Decision 7).

    The canonical full shape takes the stable ``<FormClass>Input`` /
    ``<FormClass>PartialInput`` name; a narrowed shape (``Meta.fields`` /
    ``Meta.exclude``) takes a deterministic shape-derived name so two NARROWINGS
    to the same effective set produce the same name (dedupe via the materialize
    ledger) while a different shape produces a different name.

    The shape identity is the 4-tuple ``(form_class, operation_kind,
    frozenset(effective_field_names), _form_basis_content_identity(...))`` the
    build cache keys on (``forms/sets.py::_cached_build_form_input``). The name
    reads only the form class's ``__name__``, the operation kind and the field
    sets, so two shapes that differ in basis content alone share a name and
    collide loudly at the materialize ledger. Token concatenation,
    full-vs-narrowed comparison, and the ``PartialInput`` / ``Input`` suffix ride
    ``utils/inputs.py::name_set_input_type_name`` (the name-set owner shared
    with model ``mutation_input_type_name``). This wrapper supplies the
    form-class base name and the create-vs-partial decision
    (``operation_kind == PARTIAL``; a ``FORM`` sentinel is create-shaped).
    """
    return name_set_input_type_name(
        truth.name(form_class),
        is_partial=operation_kind == PARTIAL,
        effective_field_names=effective_field_names,
        full_field_names=full_field_names,
    )


def _model_column_for(form_class: FormClass, name: str) -> ConcreteField | None:
    """Return the backing model column for a ``ModelForm`` field ``name``, or ``None``.

    A ``ModelForm`` exposes its model via ``_meta.model``; a field with a backing
    forward column / M2M resolves through ``model._meta.get_field(name)``. A plain
    ``Form`` (no ``_meta.model``), or a ``ModelForm`` extra field that declares no
    model column (a ``confirm``, a captcha, or a field reusing the name of a
    reverse relation, GenericForeignKey, or GenericRelation), yields ``None`` - the
    caller routes it through the model-less ``convert_form_field`` table instead.
    The two key spaces stay separate: only a resolved concrete ``models.Field``
    ever reaches the read-side converters (spec-038 Decision 7).

    ``get_field`` also resolves reverse relations (``ForeignObjectRel`` - e.g.
    ``Category.items``), ``GenericForeignKey``, and ``GenericRelation``. Those
    are NOT ModelForm column-backed fields: an extra form field that reuses those
    names (e.g. ``items = forms.CharField()``) must stay on the model-less path.
    Treating them as columns would mis-emit a relation id input (``itemsId``) or
    crash on missing related models.
    """
    # A ``ModelForm``'s ``_meta`` is its ``ModelFormOptions``, whose ``model`` is the
    # ``Meta.model`` class ``ModelFormMetaclass`` already read ``_meta`` from
    # (``fields_for_model``); a plain ``Form`` has no ``_meta``.
    model: type[models.Model] | None = getattr(
        truth.static_attr(form_class, "_meta", None),
        "model",
        None,
    )
    if model is None:
        return None
    try:
        column = model._meta.get_field(name)
    except FieldDoesNotExist:
        return None
    if getattr(column, "is_relation", False):
        if getattr(column, "many_to_many", False):
            if not is_forward_many_to_many(column):
                return None
        elif not is_forward_concrete_relation(column):
            return None
    elif getattr(column, "column", None) is None:
        return None
    # The arms above let through only a forward concrete / forward M2M column,
    # read off the dynamically-resolved ``_meta.model``.
    return cast("ConcreteField", column)


def relation_target_model(
    form_class: FormClass,
    name: str,
    field: forms.Field,
) -> type[models.Model] | None:
    """Return the model a relation form field's ids are decoded against, or ``None``.

    The backing column's related model for a ``ModelForm`` column, else the field's
    class-level ``queryset.model``: the basis the input build records on the field's
    ``InputFieldSpec.related_model``. ``None`` when neither names a model (a scalar
    column, or a column-less field whose queryset is assigned per request).
    """
    column = _model_column_for(form_class, name)
    model = _related_model_of(field) if column is None else column.related_model
    return model if is_model_class(model) else None


def choice_key_field(
    model: type[models.Model],
    key: str | None,
) -> models.Field[object, object] | None:
    """Return the field of ``model`` a model-choice ``to_field_name`` resolves its choice by.

    Unset, ``""`` and ``"pk"`` key by the primary key (``ModelChoiceField.to_python``
    looks up ``to_field_name or "pk"``); any other name resolves by name or attname.
    ``None`` when ``model`` has no column of that name.
    """
    if not key or key == "pk":
        return model._meta.pk
    try:
        field = model._meta.get_field(key)
    except FieldDoesNotExist:
        return None
    # ``get_field`` answers a ``models.Field`` for every forward name; a reverse relation
    # or a generic relation is no column of the row and reads as ``None`` below.
    return field if truth.is_instance(field, models.Field) else None


def _names_one_row(model: type[models.Model], field: models.Field[object, object]) -> bool:
    """Return whether ``field`` alone is unique on ``model``, as Django's fields.E311 asks.

    ``unique=True`` (a primary key included), a one-field ``unique_together`` entry, or a
    ``UniqueConstraint`` over that field alone with no condition and no expression
    (``Options.total_unique_constraints``).
    """
    if field.unique:
        return True
    alone = ({field.name}, {field.attname})
    return any(set(group) in alone for group in model._meta.unique_together) or any(
        set(constraint.fields) in alone for constraint in model._meta.total_unique_constraints
    )


def require_readable_choice_keys(
    form_class: FormClass,
    form_fields: Mapping[str, forms.Field] | None = None,
) -> None:
    """Refuse a model-choice field whose ``to_field_name`` is not a unique column of its target.

    A relation id names its row by primary key. The decode reads that row through the
    target's visibility query and binds the value ``to_field_name`` reads off it
    (``forms/resolvers.py::_to_form_key_value``); an omitted relation is rebound the same
    way from the stored row. The bound form then resolves that value with
    ``queryset.get(<to_field_name>=key)`` (a ``ModelMultipleChoiceField`` with
    ``filter(<to_field_name>__in=keys)``), so the key must name the one row the decode
    admitted. ``to_field_name`` must be unset, ``""``, ``"pk"``, or a concrete field of the
    target, by name or attname, that is unique on its own: ``unique=True``, a one-field
    ``unique_together`` entry, or a ``UniqueConstraint`` over that field alone with no
    condition (Django's fields.E311 test for a ``ForeignKey.to_field``). A lookup path, an
    annotation, a property, a relation that is not a column, an unknown name, or a column
    two rows may share is a ``ConfigurationError``: the single field's lookup would raise
    ``MultipleObjectsReturned`` or resolve another row, and the multiple field would link
    every row sharing the key, a row the target's visibility query hides included.
    ``form_fields`` is the set the operation binds: the full declared basis for an update,
    whose reconstruction rebinds every declared field, including those the input leaves
    out, and the input's own fields for a create. A field whose target model is unknown at
    build (no model column and no class-level queryset) is refused by its relation
    annotation instead.
    """
    for name, field in _form_field_basis(form_class, form_fields).items():
        if not truth.is_instance(field, _MODEL_CHOICE_FIELD):
            continue
        key = read_attr(field, "to_field_name", None)
        if not is_str(key) or not key or key == "pk":
            continue
        model = relation_target_model(form_class, name, field)
        if model is None:
            continue
        target = choice_key_field(model, key)
        # Django 5.2 counts a many-to-many field concrete (it carries a column name);
        # 6.0 does not. Either way it is no column of the target's row.
        if (
            target is None
            or not target.concrete
            or target.many_to_many
            or not _names_one_row(model, target)
        ):
            raise ConfigurationError(
                f"DjangoFormMutation for {truth.name(form_class)}: field {name!r} sets "
                f"to_field_name={key!r}, which is not a unique concrete field of "
                f"{truth.name(model)}. A relation id names its row by primary key and the "
                "form looks up the key read off that row, so to_field_name must be "
                f"'pk' or a concrete field of {truth.name(model)} that is unique on its own "
                "(unique=True, a one-field unique_together, or a UniqueConstraint over it "
                "alone with no condition).",
            )


def _model_less_relation_annotation(
    name: str,
    field: _ModelChoiceFieldAny,
    form_class: FormClass,
) -> tuple[str, object, type[models.Model]]:
    """Map a column-LESS relation form field to its ``(python_attr, annotation, related_model)``.

    A plain ``Form`` ``ModelChoiceField`` / ``ModelMultipleChoiceField`` has no
    backing model column, so it cannot reach ``relation_input_annotation`` (which
    is ``models.Field``-keyed). Its related model is its ``queryset.model``; the
    id type rides ``annotate_queryset_relation`` (the same Relay-``GlobalID``-vs-raw-pk
    rule as the model-backed path). The ``<name>_id`` (single) / ``list[<id>]``
    (multi) ``036`` scheme is reused so the wire contract is uniform across the
    model-backed and model-less relation paths. A missing primary still falls
    back to the raw pk scalar (unlike the serializer flavor, which raises when
    the relation target has no registered primary ``DjangoType`` - spec-039).

    A ``ModelChoiceField`` whose ``queryset`` is assigned in ``__init__`` (a valid
    Django idiom) has ``queryset is None`` in the uninstantiated ``base_fields``
    that schema-time discovery reads, so its related model cannot be resolved. That
    is a fail-loud ``ConfigurationError`` naming the form / field rather than a bare
    ``AttributeError`` on ``None.model``, keeping the package's fail-loud contract.
    """
    many = truth.is_instance(field, _MODEL_MULTIPLE_CHOICE_FIELD)
    return annotate_queryset_relation(
        field.queryset,
        many=many,
        python_attr=name if many else f"{name}_id",
        primary_of=registry.get,
        missing=lambda: ConfigurationError(
            f"Form {truth.name(form_class)!r} field {name!r} is a "
            f"{truth.kind(field)} whose queryset is None at class definition. "
            "Schema-time input generation reads base_fields WITHOUT instantiating the "
            "form, so a queryset assigned in __init__ is not visible and the relation "
            "id type cannot be resolved. Declare the field with a concrete queryset "
            "(e.g. ModelChoiceField(queryset=Model.objects.all())), or drop it from "
            "the generated input via Meta.fields / Meta.exclude.",
        ),
    )


def _form_admits_choice_value(
    field: forms.ChoiceField,
    value: object,
    *,
    writes_list: bool,
) -> bool:
    """Return whether a form choice field admits ``value``, the way its own ``validate`` decides.

    A single-value ``ChoiceField`` passes an empty value (``""``) without consulting its choices
    when the field is not required (``ChoiceField.validate`` checks ``valid_value`` only for a
    non-empty value), and refuses it as required otherwise; every other value, and every element
    of a ``MultipleChoiceField`` list, is admitted exactly when ``valid_value`` admits it (the
    field's own choices, option groups descended, compared as given and as ``str``). Whatever a
    consumer ``valid_value`` override raises propagates to the schema build.
    """
    if not writes_list and truth.is_instance(value, str) and value == "":
        return not field.required
    return bool(field.valid_value(value))


def _form_choice_narrowing(
    name: str,
    field: forms.Field,
    column: ConcreteField,
    form_class: FormClass,
) -> tuple[list[tuple[object, object]], bool] | None:
    """Return the column choices a form choice field narrows its input to, or ``None``.

    The form validates the value (spec-038 Decision 7: the form is the input source of truth),
    so the published input carries the values the column lists AND the form field admits. When
    the field admits every value the column lists (the ``TypedChoiceField`` Django generates
    from the column, an equal declared set, a declared superset whose extra values the column
    never stores), the column's own type is published (``None``: the read enum, the symmetric
    wire contract). Otherwise the result is ``(pairs, writes_list)``: the column's
    ``(value, label)`` pairs the field admits (``types/converters.py::choice_column_pairs``, a
    grouped column flattened, ``""`` where the column admits it), in column order, and whether
    the field writes a list. Members and values are the column's, so a narrowed enum is a subset
    of the read enum's member names and decodes to the raw value the column stores.

    Only static choices narrow: the published type is built once, at schema build, from the
    field basis (``base_fields``, or the ``get_form_fields`` hook's fields), never from a bound
    form, so callable choices (re-evaluated on every read) and an empty set (choices assigned
    per request in ``__init__``) leave the column's type published, and the bound form still
    refuses a value outside its request-time choices.

    A ``MultipleChoiceField`` writes a list, so it narrows the element choices of an
    ``ArrayField`` (its ``base_field``) and is refused over a single-value choice column, where
    no list is a value the column lists. A field admitting no non-empty value the column lists
    is refused: its input could carry at most the empty value (where the column lists ``""``
    and the form admits it), and every other value fails validation. A column without choices, a
    relation or file column (even one declaring choices), a non-choice form field, a
    ``ModelChoiceField`` (its choices are its queryset's rows, read per request, even over a
    scalar choice column) and a single-value ``ChoiceField`` over an ``ArrayField`` keep the
    column's type.
    """
    if not truth.is_instance(field, forms.ChoiceField) or truth.is_instance(
        field,
        _MODEL_CHOICE_FIELD,
    ):
        return None
    element = array_element_field(column)
    choice_column = element or column
    if not choice_column.choices:
        return None
    if model_column_write_kind(column) != SCALAR:
        # A relation or file column declaring choices keeps its own kind and id / ``Upload``
        # type: the published type must match the kind the decode routes the value by.
        return None
    writes_list = truth.is_instance(field, forms.MultipleChoiceField)
    if writes_list and element is None:
        raise ConfigurationError(
            f"Form {truth.name(form_class)} field {truth.render(name)} is a "
            f"{truth.kind(field)} over the single-value choice column "
            f"{truth.name(column.model)}.{column.name}: it writes a list, which is not one of the "
            "column's choices. Declare a ChoiceField to write one value, or store many values in "
            "an ArrayField column whose base_field declares the choices.",
        )
    if element is not None and not writes_list:
        return None
    choices: object = field.choices
    if truth.is_instance(choices, CallableChoiceIterator) or not list(
        cast("Iterable[object]", choices),
    ):
        return None
    listed = choice_column_pairs(choice_column)
    admitted = [
        (value, label)
        for value, label in listed
        if _form_admits_choice_value(field, value, writes_list=writes_list)
    ]
    if len(admitted) == len(listed):
        return None
    if all(truth.is_instance(value, str) and value == "" for value, _label in admitted):
        raise ConfigurationError(
            f"Form {truth.name(form_class)} field {truth.render(name)} admits none of the "
            "non-empty values the choice column "
            f"{truth.name(choice_column.model)}.{choice_column.name} lists, so no non-empty value "
            "its input could carry passes the form. Declare choices the column lists, or drop "
            "the field via Meta.fields / Meta.exclude.",
        )
    return admitted, writes_list


def _form_choice_annotation(
    name: str,
    pairs: list[tuple[object, object]],
    *,
    writes_list: bool,
    type_name: str,
    form_class: FormClass,
) -> object:
    """Return the generated enum annotation for a form choice field's narrowed column choices.

    The enum is ``<InputTypeName><FieldName>Enum`` (``types/converters.py::choice_enum_name``, the
    naming every flavor's generated choice enum shares), built by the shared
    ``build_enum_from_choices`` core from the ``_form_choice_narrowing`` pairs, so member
    sanitization and ``BLANK`` follow the read enum's rules; a list-writing field publishes
    ``list[<enum>]`` with a non-null element. One input class references it, and the per-shape
    build cache builds each input once.
    """
    enum_cls = build_enum_from_choices(
        pairs,
        choice_enum_name(type_name, name),
        source_label=f"Form {truth.name(form_class)} field {truth.render(name)}",
    )
    return GenericAlias(list, (enum_cls,)) if writes_list else enum_cls


def _choice_narrowing_identity(
    name: str,
    field: forms.Field,
    column: ConcreteField | None,
    form_class: FormClass,
) -> object:
    """Project the column values a choice field narrows its input to, for the shape identity.

    ``None`` when the field publishes its column's type; otherwise ``(writes_list, values)``.
    A refusal projects ``None`` instead of escaping the identity walk: the projection walks the
    whole basis, an excluded field must not fail the build, and the build re-runs the narrowing
    for every emitted field, where the refusal is raised.
    """
    if column is None:
        return None
    try:
        narrowing = _form_choice_narrowing(name, field, column, form_class)
    except ConfigurationError:
        return None
    if narrowing is None:
        return None
    pairs, writes_list = narrowing
    return writes_list, tuple(value for value, _label in pairs)


def _simple_triple(name: str, annotation: object, kind: str) -> tuple[str, str, object, str]:
    """Return ``(input_attr, graphql_name, annotation, kind)`` for a NON-relation form field.

    The scalar / file arms of ``_field_triple_and_spec`` all share one shape: the
    input attr IS the form field's own name, and the wire name is its camelCase
    (only a relation remaps to ``<name>_id``). Single-sources that
    ``python_attr = name; graphql_name = graphql_camel_name(name)`` pair so it is
    spelled once rather than in every non-relation arm.
    """
    return name, graphql_camel_name(name), annotation, kind


def _field_triple_and_spec(
    name: str,
    field: forms.Field,
    column: ConcreteField | None,
    type_name: str,
    form_class: FormClass,
) -> tuple[str, object, InputFieldSpec, bool]:
    """Resolve one form field to its ``(python_attr, base_annotation, InputFieldSpec, required)``.

    A ``ModelForm`` field with a backing column routes through
    ``model_column_input_annotation`` (keyed on the resolved ``models.Field``):
    a relation column -> ``<name>_id`` / ``categoryId`` + the Relay-vs-raw-pk
    id type, ``relation_single`` / ``relation_multi``; a file/image column ->
    ``Upload`` (``file``); else the read-side scalar / choice-enum (``scalar``),
    except a choice field admitting fewer of a choice column's values than it
    lists, which publishes the generated enum of the admitted values
    (``_form_choice_narrowing``).
    A column-less field (a plain ``Form`` field or a ``ModelForm`` extra field)
    uses ``converter.convert_form_field`` (the model-less table) for the kind,
    and the relation / file annotations are finalized here (where ``Upload`` and
    the model-less relation id-type are known).

    Returns the BASE (non-optional) annotation; the create/partial requiredness
    widening is applied by the caller. The returned ``required`` is the shared
    ``converter.form_field_required`` decision for BOTH the column-backed and
    column-less paths (so ``NullBooleanField`` is forced optional on either
    basis, and the two paths cannot drift). The returned ``InputFieldSpec``
    records the reverse map the resolver consults - ``target_name`` is
    always the form's declared name, never the ``<name>_id`` relation attr,
    because a bound Django form is keyed by form-field name. A relation field
    also records ``related_model`` from the SAME basis the generated id type uses
    (the backing column's ``related_model``, else the model
    ``annotate_queryset_relation`` resolved from ``queryset.model``) so the
    decode never re-derives it from the class-level ``base_fields`` field
    (whose ``queryset`` is ``None`` under the request-scoped-choices idiom).
    """
    related_model: type[models.Model] | None = None
    # ONE requiredness decision for both the column-backed and column-less paths
    # (so a NullBooleanField backed by a nullable model column is forced optional
    # too, not just the model-less one) - see ``converter.form_field_required``.
    field_required = form_field_required(field, column=column)
    narrowing = None if column is None else _form_choice_narrowing(name, field, column, form_class)
    if narrowing is not None:
        pairs, writes_list = narrowing
        python_attr, graphql_name, annotation, kind = _simple_triple(
            name,
            _form_choice_annotation(
                name,
                pairs,
                writes_list=writes_list,
                type_name=type_name,
                form_class=form_class,
            ),
            SCALAR,
        )
    elif column is not None:
        # ModelForm field with a backing model column: the shared column mapper
        # types the GraphQL id / Upload / scalar; kind comes from
        # ``model_column_write_kind``; related_model stays here for the reverse map.
        python_attr, graphql_name, annotation = model_column_input_annotation(
            column,
            type_name,
            primary_of=registry.get,
        )
        kind = model_column_write_kind(column)
        if kind in (RELATION_SINGLE, RELATION_MULTI):
            # The decode resolves ids against the SAME model the id type derived
            # from (the backing column's related model), not the form field's
            # (possibly ``None``) ``queryset.model``.
            related_model = column.related_model
    else:
        # Column-less form field: the model-less ``convert_form_field`` table owns
        # the kind; relation / file annotations are finalized here. Requiredness
        # was already decided above via ``form_field_required``.
        conversion = convert_form_field(field)
        if conversion.kind == FILE:
            python_attr, graphql_name, annotation, kind = _simple_triple(name, Upload, FILE)
        elif conversion.kind in (RELATION_SINGLE, RELATION_MULTI):
            # ``convert_form_field`` answers a relation kind only for a
            # ``ModelChoiceField`` (the multi variant subclasses it).
            python_attr, annotation, related_model = _model_less_relation_annotation(
                name,
                cast("forms.ModelChoiceField[models.Model]", field),
                form_class,
            )
            graphql_name = graphql_camel_name(python_attr)
            kind = conversion.kind
        else:
            python_attr, graphql_name, annotation, kind = _simple_triple(
                name,
                conversion.annotation,
                conversion.kind,
            )

    spec = InputFieldSpec(
        input_attr=python_attr,
        graphql_name=graphql_name,
        target_name=name,
        kind=kind,
        related_model=related_model,
        key_attname=None if related_model is None else non_pk_relation_key_attname(column),
    )
    return python_attr, annotation, spec, field_required


def _guard_input_attr_collisions(form_class: FormClass, field_specs: list[InputFieldSpec]) -> None:
    """Raise if two form fields collide on the generated input attr OR GraphQL name.

    Two distinct ways two form fields collapse to one generated input field, both
    of which ``build_strawberry_input_class`` would resolve by SILENTLY dropping
    one - so both fail loud here (the package's fail-loud contract):

    * ``input_attr`` clash - a relation field ``foo`` remaps to input attr
      ``foo_id`` (the ``036`` scheme), so a form declaring BOTH a relation ``foo``
      AND a field literally named ``foo_id`` produces two specs with
      ``input_attr == "foo_id"``; the second overwrites the first in the
      annotations dict.
    * ``graphql_name`` clash - two distinct field names that default-camel-case to
      ONE GraphQL name (``foo_bar`` + ``fooBar`` -> ``fooBar``). The python attrs
      differ (so the input-attr check above passes), but Strawberry collapses the
      two onto one schema field. Mirrors the read-type guard in
      ``types/finalizer.py::_audit_field_surface``.

    The seen-dict walk + the two collision arms are single-sited in
    ``utils/inputs.py::iter_input_field_collisions``; the form
    flavor raises on the FIRST collision (the serializer aggregates instead),
    with byte-stable wording via the threaded form nouns.
    """
    for message in iter_input_field_collisions(
        field_specs,
        subject=f"Form {truth.name(form_class)!r}",
        field_noun="form fields",
        rename_clause="Rename one of the form fields,",
        name_of=lambda spec: spec.target_name,
    ):
        raise ConfigurationError(message)


def build_form_input_class(
    form_class: FormClass,
    *,
    operation_kind: str,
    fields: object = None,
    exclude: object = None,
    form_fields: Mapping[str, forms.Field] | None = None,
) -> tuple[type[object], list[InputFieldSpec]]:
    """Build ONE ``@strawberry.input`` class from a form's declared fields.

    ``operation_kind`` is ``CREATE`` / ``FORM`` (the create-shaped input - each
    field's requiredness from ``field.required``, graphene-django parity) or
    ``PARTIAL`` (the update-shaped input). In the partial input, model-backed
    fields are forced optional (the reconstruction supplies them from the
    located row), but a **non-model extra field keeps its declared
    ``field.required``** (spec-038 Decision 7 - so a required ``confirm`` stays
    required on update). Optional fields widen ``annotation | None`` + a
    ``strawberry.UNSET`` default, the ``036`` shape.

    ``operation_kind`` is part of the generator's pinned vocabulary (the three
    kinds re-exported / declared on this module): anything else is a
    misconfiguration the generator would otherwise silently resolve to a
    create-shaped input, so it fails loud naming the form and the received
    value.
    """
    if operation_kind not in CREATE_SHAPED_KINDS | {PARTIAL}:
        raise ConfigurationError(
            f"DjangoFormMutation input build for {truth.name(form_class)} received "
            f"out-of-vocabulary operation_kind {operation_kind!r}; expected CREATE, "
            "FORM, or PARTIAL.",
        )
    effective = resolve_effective_form_fields(
        form_class,
        fields=fields,
        exclude=exclude,
        form_fields=form_fields,
        operation_kind=operation_kind,
    )
    # The update reconstruction rebinds every declared field; a create binds only its own.
    bound_fields = form_fields if operation_kind == PARTIAL else effective
    require_readable_choice_keys(form_class, bound_fields)
    # The un-narrowed shape of the same operation: the canonical-name comparison basis,
    # so an update input that drops only the row identity keeps the canonical name.
    full_field_names = tuple(
        resolve_effective_form_fields(
            form_class,
            form_fields=form_fields,
            operation_kind=operation_kind,
        ),
    )
    type_name = form_input_type_name(
        form_class,
        operation_kind,
        tuple(effective),
        full_field_names=full_field_names,
    )
    is_partial = operation_kind == PARTIAL

    triples: list[tuple[str, object, dict[str, object]]] = []
    field_specs: list[InputFieldSpec] = []
    for name, field in effective.items():
        column = _model_column_for(form_class, name)
        python_attr, annotation, spec, field_required = _field_triple_and_spec(
            name,
            field,
            column,
            type_name,
            form_class,
        )
        field_specs.append(spec)

        # Requiredness: the create input honors the converter/form required flag;
        # the partial input forces a model-backed field optional but a column-less
        # extra field keeps its converted ``required``. The widening tail
        # (``T | None`` + ``UNSET`` default + ``name=`` alias) is single-sited
        # in ``utils/inputs.py::optional_input_field``.
        required = False if (is_partial and column is not None) else field_required
        annotation, field_kwargs = optional_input_field(
            annotation,
            python_attr=python_attr,
            graphql_name=spec.graphql_name,
            widen=not required,
        )
        triples.append((python_attr, annotation, field_kwargs))

    _guard_input_attr_collisions(form_class, field_specs)
    input_cls = build_strawberry_input_class(type_name, triples)
    return input_cls, field_specs


def _required_form_field_names(
    form_class: FormClass,
    form_fields: Mapping[str, forms.Field] | None = None,
) -> set[str]:
    """Return the names of every declared form field that must appear in a create input.

    Uses the shared ``converter.form_field_required`` with each field's backing
    column, matching the build site: an exact ``NullBooleanField`` is optional
    unless a non-null model column makes omission invalid. This never calls
    ``convert_form_field``, so discovery over the FULL declared set cannot raise
    on an unsupported field later excluded via ``Meta.fields`` / ``Meta.exclude``.
    """
    return {
        name
        for name, field in _form_field_basis(form_class, form_fields).items()
        if form_field_required(field, column=_model_column_for(form_class, name))
    }


def guard_create_required_fields(
    form_class: FormClass,
    effective_field_names: Iterable[str],
    form_fields: Mapping[str, forms.Field] | None = None,
) -> None:
    """Raise if a create-shaped narrowing drops a still-declared required form field.

    A bound form fails required-validation for any ``field.required`` field absent
    from its bound ``data=``, so a create whose effective field set (after
    ``Meta.fields`` / ``Meta.exclude``) omits a still-declared required form field
    would compile to a schema that looks valid but can never succeed. This raises
    ``ConfigurationError`` naming the dropped required field(s), covering both
    ``Meta.fields`` and ``Meta.exclude``.

    It is separate from the input builder (``build_form_input_class``) so the bind's
    per-shape build cache (``forms/sets.py::_cached_build_form_input``) can run it PER
    mutation DECLARATION rather than only on the first build of a given shape: the cache key
    excludes ``guard_required``, so a waiving mutation (``guard_required=False``,
    having overridden ``get_form_kwargs`` / ``get_form``) that materializes a
    narrowed shape FIRST must not suppress the guard for a later non-waiving
    mutation reusing the same cached shape. The guard is tied to the declaration,
    not the built input shape (spec-038 Decision 7, the create-required guard).

    The drop-detection (``required - effective - waived``) is single-sited in
    ``utils/inputs.py::guard_dropped_required`` (spec-039), shared with the
    serializer create guard; the form flavor passes no ``waived`` set (it has no
    injected-field mechanism) and keeps its own pinned error wording.
    """
    guard_dropped_required(
        _required_form_field_names(form_class, form_fields),
        effective_field_names,
        make_error=lambda dropped: ConfigurationError(
            f"DjangoFormMutation create input for {truth.name(form_class)} drops required form "
            f"field(s) {dropped!r} via Meta.fields / Meta.exclude; a bound form can "
            "never validate without them. Keep them in the input, or override get_form_kwargs "
            "/ get_form to supply them (which waives this guard).",
        ),
    )


def guard_partial_required_column_less_fields(
    form_class: FormClass,
    effective_field_names: Iterable[str],
    form_fields: Mapping[str, forms.Field] | None = None,
) -> None:
    """Raise if a partial (update) narrowing drops a required COLUMN-LESS form field.

    The partial counterpart to ``guard_create_required_fields``, but scoped to
    column-less fields ONLY. On update the input maps to ``PARTIAL``: a model-backed
    required field is widened optional and reconstructed from the located row by
    ``_reconstruct_partial_data``, so dropping it from the input via ``Meta.fields`` /
    ``Meta.exclude`` is harmless. But a required field with NO backing model column -
    a declarative extra like ``confirm = forms.CharField(required=True)`` - cannot be
    reconstructed from model state (``model_to_dict`` only returns columns), so if it
    is dropped the bound form fails its required validation on EVERY request while the
    schema still finalizes cleanly. Reject that at bind, naming the field(s).

    Scoping the required set to ``_model_column_for(...) is None`` is load-bearing:
    a blanket reuse of ``guard_create_required_fields`` here would wrongly reject
    reconstructable model-backed required fields that the partial path
    legitimately drops. Drop detection itself is
    ``utils/inputs.py::guard_dropped_required`` (same spine as the create guard);
    only the required-set filter is form-partial-specific. The ``get_form_kwargs`` /
    ``get_form`` waiver (``guard_required=False``) suppresses this the same way it
    suppresses the create guard.
    """
    column_less_required = {
        name
        for name in _required_form_field_names(form_class, form_fields)
        if _model_column_for(form_class, name) is None
    }
    guard_dropped_required(
        column_less_required,
        effective_field_names,
        make_error=lambda dropped: ConfigurationError(
            f"DjangoModelFormMutation update input for {truth.name(form_class)} drops required "
            f"column-less form field(s) {dropped!r} via Meta.fields / Meta.exclude; they cannot "
            "be reconstructed from the row, so a bound form can never validate without them. Keep "
            "them in the input, or override get_form_kwargs / get_form to supply them (which "
            "waives this guard).",
        ),
    )
