"""The sync + async form-mutation resolver pipeline.

The form-flavor write runtime, the sibling of ``mutations/resolvers.py`` (the
``036`` model pipeline). The pipeline is (spec-038 Decision 8):

    (update) locate -> authorize -> decode -> construct + validate-once
            -> write -> (ModelForm) re-fetch -> payload

**Authorize runs BEFORE the relation decode** (matching the ``036`` model path):
the decode issues visibility-scoped ``get_queryset`` queries, so running it
pre-auth would let an unauthorized caller probe related-object visibility by id
(a write-auth denial ``GraphQLError`` vs an in-band relation ``FieldError`` is an
observable distinction). For ``update`` the locate must precede authorize (object
-level perms need the instance), exactly as the model path locates first.

and the form-specific invariants this module owns:

- **The decode produces a FORM-field-keyed ``provided_data`` + a separate
  ``provided_files``** (Decision 8 step 1). A bound Django form is keyed by FORM
  field name (``ItemModelForm(data={"category": pk})``, never ``{"category_id":
  pk}``) and reads uploads from ``files=``, never ``data=``. The reverse
  map (``mutation_cls._input_field_specs``, a list of
  ``utils/inputs.py::InputFieldSpec``) routes each provided input attr to its form
  field name + decode ``kind`` (``SCALAR`` / ``RELATION_SINGLE`` /
  ``RELATION_MULTI`` / ``FILE``). An update binds an explicit ``null`` file as
  Django's clear sentinel ``False`` (``_file_clears``); a required file field cannot
  clear, so that ``null`` is its ``required`` error (``_required_file_clears``).

- **The dedicated form relation decoder visibility-checks EVERY branch**
  (Decision 7 / Decision 8 step 1). Every model-choice field the input carries is a
  relation id (the build refuses one over a column that is no relation,
  ``forms/inputs.py::require_column_kind_agreement``). Each relation id - a GlobalID string
  *or* a raw pk, by target - is type-checked (``decode_model_global_id`` for the Relay
  branch, ``coerce_relation_pk_or_none`` for the raw-pk branch), then **resolved
  to the visible object through the related primary ``DjangoType.get_queryset``**
  (``apply_type_visibility_sync(initial_queryset(...))``). The model flavor's
  batched set decoder now shares ``decode_visible_relation_ids`` (visibility on
  every branch, including raw pk); the form still maps per element because it
  needs the related object for ``to_field_name``. A hidden / wrong-model /
  uncoercible id is a field-keyed ``FieldError`` (hidden and missing
  indistinguishable, no existence leak), and so is a visible row whose stored key
  (the column a ``to_field`` relation stores) is ``NULL``, whatever column the form
  field is keyed by. The visible object is converted to the form-key value by
  ``to_field_name`` (``obj.serializable_value(field.to_field_name)``, or ``obj.pk``
  when the field sets none; the input build admits only ``pk`` or a concrete field of
  the target unique on its own, ``forms/inputs.py::require_readable_choice_keys``) so
  the bound form validates by the same key it was built on. The bound form's own field,
  which an ``__init__`` or ``get_form`` override may rebuild, must query the target model
  (or a subclass) by the same key column, or the request is a ``ConfigurationError``
  before ``is_valid()`` (``_assert_bound_choice_agreement``); a class-level field over
  another model, on a form that binds its class-level fields under the default
  ``get_form``, is refused at schema build instead when every write binds it (any update,
  a create whose input makes it required: ``forms/inputs.py::require_class_choice_models``).
  A single relation whose
  form-key value the field cleans to empty is refused as that field's ``invalid_choice``
  error rather than bound as a clear. Only a whole single or list value in the field's
  ``empty_values`` is a clear; an M2M list element never is, so every element, ``""``
  included, is decoded.

- **``update`` reconstructs the full bound payload** (Decision 8 step 4): for
  every non-file declared form field the input did not provide, supply the located
  row's value under the form field name, then overlay ``provided_data``; ``files =
  provided_files``. Scalars, and a FK whose ``ModelChoiceField`` resolves its choice by
  the column the FK stores (``to_field_name or "pk"`` names ``ForeignKey.target_field``,
  as every generated field does), come from ``model_to_dict``: the stored value already
  is the form key. M2M and every other ``ModelChoiceField`` FK, including a
  ``to_field_name``-less field over a ``ForeignKey(to_field=...)``, are reconstructed
  from the related object(s) through the form field's own ``prepare_value`` so an omitted
  relation binds in the SAME shape a provided one decodes to (Decision 8). A single FK's
  form key, stored or provided, must be a value the ``ModelChoiceField`` looks up: one in the field's
  ``empty_values`` (a ``to_field`` or text key holding ``""``) cleans to empty, never to
  the row, so it is the form field's own ``invalid_choice`` error, keyed like every form
  error, before the form is bound. A non-null stored key of a FK reconstructed from its
  related object that resolves to no row is the same error: the stored key is never read
  under the form's lookup field and never replaced by an empty value. An
  omitted file is preserved via the bound ``form_class(instance=...)``'s ``initial``
  (never re-supplied, never cleared). An omitted field whose input shape disagrees with
  its column (a ``MultipleChoiceField`` over a single-value column without choices, a
  built-in single-value field over an ``ArrayField``) binds the bound form's own initial for the
  field (``_bind_omitted_shape_disagreeing_initials``), never the stored value. A required
  non-model extra field stays
  required in the partial input, so it is always present in
  ``provided_data``. This is a partial-input transport, not partial validation:
  the reconstructed bound ``ModelForm`` revalidates every declared field. An
  omitted value that is already stored but no longer satisfies the current form
  (for example after a validator was tightened) therefore blocks the mutation.
  The caller must supply a valid replacement in the same request, or repair the
  row out of band when the field is excluded from the generated input; the
  framework never silently excludes an invalid untouched field from validation.

- **The form is constructed once via the overridable ``get_form`` /
  ``get_form_kwargs`` hooks** (Decision 8 step 4 / Decision 6); ``form.is_valid()``
  runs once. Each value is bound under the keys the bound form reads it from: a prefixed
  form (a class-level ``prefix``, a ``get_form_kwargs`` ``prefix=``, a ``get_form``
  passing the package's mapping or a copy with a prefix) reads ``form.add_prefix(name)``,
  and a field whose widget reads several keys (a ``MultiWidget``, such as
  ``SplitDateTimeField``'s; PostgreSQL's ``SplitArrayWidget``, ``SplitArrayField``'s)
  reads its parts under that name's ``<key>_0`` .. keys. A bound ``data`` mapping holding
  bare field names and none of those keys is re-keyed: each value whole under
  ``form.add_prefix(name)``, its parts under the widget's keys (a ``MultiWidget`` splits a
  value with its own ``decompress``; a ``SplitArrayWidget`` gets one element per index,
  padded to its ``size`` with ``None``); a bound ``files`` mapping is re-keyed under the
  prefix; one already holding a key the form reads is left as bound
  (``_bind_under_form_keys``), a multi-key widget field's whole value it holds under
  ``form.add_prefix(name)`` with none of the widget's part keys still getting its parts
  beside it (``_bind_kept_parts``). A ``disabled`` field reads no data and is bound
  whole. A list longer than a ``SplitArrayWidget``'s ``size``, which the widget would
  truncate, is that field's ``max_length`` error before ``is_valid()``.
  Every later read or write of the bound values goes through the same keys
  (``_bound_form_value`` / ``_bind_form_values``). A
  failure maps ``form.errors`` onto the ``FieldError`` envelope via
  the reused ``validation_error_to_field_errors(ValidationError(
  form.errors.as_data()), key_map)``: each form field name is re-keyed to the
  GraphQL input field the client sent (``category`` -> ``categoryId``) through
  the shared ``build_error_key_map`` over the bind-stashed specs, a form field
  the input does not expose keeps its form field name, and the form's
  ``NON_FIELD_ERRORS`` bucket lands on the ``"__all__"`` sentinel - the same
  keying a model ``full_clean()`` failure gets. A valid ``ModelForm`` whose instance
  holds a datetime or time the pinned alias cannot store (or, on PostgreSQL, read back)
  answers that column's ``invalid`` error before the save
  (``_unstorable_temporal_errors``).

- **Write via the ``ModelForm``'s save / ``perform_mutate`` (plain), wrapped by
  the reused save-time mappers** (``save_or_field_errors``; a ``ModelForm`` update
  ``forced_save_or_field_errors``) (Decision 8 step 5), never a top-level
  ``GraphQLError`` at the write: an ``IntegrityError``
  is the ``"__all__"`` envelope, and a Django ``ValidationError`` raised by
  consumer save-time code (a ``save()`` / ``perform_mutate`` override, a model
  ``save()``, a signal receiver) is mapped through the flavor's key map - the
  form field name for the plain form, every name Django keys the backing model
  field by for the ``ModelForm`` (``save_time_error_key_map``). Before the save, an
  explicit ``null`` on a ``null=False`` column that the column's own form field cleaned
  to a storable value instead of ``None`` (a ``BooleanField``'s ``False``, a ``blank=True``
  text or text-choice column's ``""``) is that column's field-keyed ``null`` error, as on
  the model flavor, and nothing is written (``_coerced_null_fields``). The ``ModelForm``
  save adds the one failure a valid ``ModelForm`` reaches on its own: a
  ``blank=True, null=False`` column cleaned to an empty value it cannot store
  (``None``, refused by the database's ``NOT NULL`` ``IntegrityError``, or ``""`` on
  a column that stores no empty string: a non-text choice column, refused by
  ``save()`` with a ``ValueError`` / ``ValidationError``, or an ``ArrayField``,
  refused by PostgreSQL with a ``DataError``) maps to that column's field-keyed
  ``null`` error (``_modelform_save_or_field_errors``); any other ``ValueError`` or
  ``DataError`` propagates. On a
  ``ModelForm`` update, and a create over a
  client-assigned key, the form's ``save()`` is called with ``commit=False``, the
  package saves the row it returned and calls ``form.save_m2m()``, as Django's
  admin does, so work a ``ModelForm.save()`` override does only when committing
  does not run there. A create INSERTs it (``mutations/resolvers.py::save_new_row``,
  whose ``force_insert`` the model's ``save()`` receives): a row committed under
  that key between ``is_valid()`` and the save is the ``"__all__"`` ``constraint``
  envelope, never overwritten. An update UPDATEs it
  (``mutations/resolvers.py::save_located_row``, whose ``force_update`` the model's
  ``save()`` receives, inside ``forced_save_or_field_errors``): a located row a
  concurrent transaction deleted after the locate is the ``conflict`` envelope on
  ``id``, never re-INSERTed. A bound form that fails over such a row (the omitted
  M2M rebuilt from the now-empty database, an omitted relation's stored key whose
  target cascaded away with it) is the same envelope, not ``form.errors``: the
  shared skeleton probes the located row on a step failure
  (``mutations/resolvers.py::run_write_pipeline_sync``). Every other create is one
  ``form.save()``.

- **The ``ModelForm`` re-fetch rides the ``036`` ``refetch_optimized`` path**
  (Decision 9): by pk WITHOUT the visibility filter, routed through
  ``apply_connection_optimization`` so the plan keeps ``select_related`` /
  ``prefetch_related`` and, under the mutation operation, introduces no
  ``.only(...)`` on a queryset that carries none - no new optimizer code.

- **One ``transaction.atomic()`` boundary; the async path runs the sync body in
  one ``sync_to_async(thread_sensitive=True)`` call** (Decision 8) - both form
  flavors ride ``run_write_pipeline_sync`` for that boundary, the same skeleton
  the model / serializer / delete paths use.

- **``SyncMisuseError`` discipline** is inherited from
  ``apply_type_visibility_sync``: a sync form mutation meeting an ``async def
  get_queryset`` (a relation decode or the update locate) closes the coroutine and
  raises.

Single-sourced: the locate / authorize / id-decode / re-fetch / payload /
validation-mapper / save-mapper are the promoted ``036`` public helpers, CALLED
not re-implemented. The genuinely net-new code is the visibility-on-every-branch
relation decoder, the ``kind``-split decode, and the partial-update
reconstruction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import DataError, IntegrityError, models
from django.forms.models import model_to_dict
from django.utils.datastructures import MultiValueDict

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.resolvers import (
    StepFailure,
    adds_by_update_first,
    forced_save_or_field_errors,
    make_resolver_entries,
    run_write_pipeline_sync,
    save_located_row,
    save_new_row,
    save_or_field_errors,
)
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    call_method,
    list_of,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_INVALID,
    UNBINDABLE_TEMPORAL_MESSAGE,
    build_error_key_map,
    save_time_error_key_map,
    unstorable_temporal,
    validation_error_to_field_errors,
)
from django_strawberry_framework.utils.querysets import sync_pipeline_recourse
from django_strawberry_framework.utils.relations import (
    is_model_class,
    is_single_column_foreign_key,
)
from django_strawberry_framework.utils.widgets import widget_entries, widget_keys
from django_strawberry_framework.utils.write_transaction import (
    pinned_write_alias,
    pipeline_write_phase,
)
from django_strawberry_framework.utils.write_values import (
    decode_field_handlers,
    decode_provided_fields,
    decode_visible_relation,
    materialize_relation_id_container,
    unstorable_columns,
)
from django_strawberry_framework.write_mixins import backing_model_of

from .inputs import choice_key_field, relation_target_model, shape_disagreeing_column
from .sets import _is_form_class

if TYPE_CHECKING:
    from collections.abc import Callable, Container, Iterable, Mapping
    from typing import Protocol, TypeAlias, TypeVar

    from strawberry.types import Info
    from typing_extensions import TypeIs

    from django_strawberry_framework.mutations.resolvers import (
        _AsyncResolverEntry,
        _SyncResolverEntry,
    )
    from django_strawberry_framework.utils.errors import ErrorKeyMap, FieldError
    from django_strawberry_framework.utils.typing import ForeignKeyField

    from .sets import DjangoFormMutation, DjangoModelFormMutation

    # A form-flavor mutation class: the ``ModelForm`` or the model-less plain base.
    _FormMutationClass: TypeAlias = type[DjangoModelFormMutation | DjangoFormMutation]
    # The form ``decode_step`` product: the form-keyed bound ``(data, files)`` pair.
    _DecodedForm: TypeAlias = tuple[dict[str, object], dict[str, object]]

    _FormT = TypeVar("_FormT", bound=forms.BaseForm)
    _FormT_co = TypeVar("_FormT_co", bound=forms.BaseForm, covariant=True)
    _ValueT = TypeVar("_ValueT")

    class _FormBuilder(Protocol[_FormT_co]):
        """A form mutation instance, as its ``get_form`` construction hook builds a form."""

        def get_form(
            self,
            info: Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> _FormT_co: ...


# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) form pipeline. Mirrors the
# ``036`` ``_MUTATION_ASYNC_RECOURSE`` wording: the whole pipeline runs
# synchronously (under one ``sync_to_async`` worker on the async surface), so an
# ``async def get_queryset`` can never be awaited here.
_FORM_ASYNC_RECOURSE = sync_pipeline_recourse("form mutation")


if TYPE_CHECKING:
    # Each model parameter is read-only here, so the ``Model`` bound covers every form
    # and field.
    _ModelFormAny: TypeAlias = forms.ModelForm[models.Model]
    _ModelChoiceFieldAny: TypeAlias = forms.ModelChoiceField[models.Model]
    _ModelMultipleChoiceFieldAny: TypeAlias = forms.ModelMultipleChoiceField[models.Model]
    #: Any model field, its set and get types unread.
    _FieldAny: TypeAlias = models.Field[object, object]
else:
    # None of the four has a ``__class_getitem__`` at runtime (only the
    # ``django_stubs_ext`` patch adds one): each hint stays the bare class.
    _ModelFormAny = forms.ModelForm
    _ModelChoiceFieldAny = forms.ModelChoiceField
    _ModelMultipleChoiceFieldAny = forms.ModelMultipleChoiceField
    _FieldAny = models.Field


def _is_model_choice_field(field: forms.Field) -> TypeIs[_ModelChoiceFieldAny]:
    """``isinstance(field, forms.ModelChoiceField)``, its choices read as rows of ``Model``."""
    return isinstance(field, forms.ModelChoiceField)


def _is_model_multiple_choice_field(
    field: forms.Field,
) -> TypeIs[_ModelMultipleChoiceFieldAny]:
    """``isinstance(field, forms.ModelMultipleChoiceField)``, its choices read as rows of ``Model``."""
    return isinstance(field, forms.ModelMultipleChoiceField)


def _stored_key_is_form_key(link: ForeignKeyField, form_field: _ModelChoiceFieldAny) -> bool:
    """Return whether a FK column already stores the key ``form_field`` resolves its choice by.

    The column holds the value of ``ForeignKey.target_field``: the related pk, or the
    ``to_field``. The bound ``ModelChoiceField`` looks its choice up by
    ``to_field_name or "pk"`` (``ModelChoiceField.to_python``). The stored value is the
    form key exactly when both name the same related column. A generated field always
    does (``ForeignKey.formfield`` passes the target's name as ``to_field_name``); a
    declared field keyed by another column does not, a ``to_field_name``-less field over
    a ``to_field`` FK included.
    """
    key = form_field.to_field_name or "pk"
    target = link.target_field
    return key == target.name or (key == "pk" and target.primary_key)


def _is_empty_form_value(candidate: object, form_field: forms.Field) -> bool:
    """Return whether ``candidate`` matches the form field's empty values safely."""
    empty_values: Container[object] = form_field.empty_values
    try:
        return candidate in empty_values
    except TypeError:
        return False


def _unrepresentable_choice(
    form_field: forms.Field,
    form_key: object,
    *,
    value: object,
) -> ValidationError | None:
    """Return the field's ``invalid_choice`` error when ``form_key`` names no row through it.

    The one representability check every single-relation form key passes before a form is
    bound with it. ``ModelChoiceField.to_python`` answers ``None`` for any value in the
    field's ``empty_values`` before it looks a choice up, so a related row whose form-key
    value is one of them (a ``to_field_name`` column holding ``""``, a text key ``""``, a
    nullable column other than the one the relation stores holding ``NULL``) cannot be named
    through the field: binding the key clears an optional relation or reports a required
    one as missing. ``form_key`` is
    ``None`` when no related row resolves (a dangling stored key), which is refused the same
    way. Either is the field's own ``invalid_choice`` error with ``value`` as its parameter,
    never a clear and never a reinterpreted key. Only single relations reach it: a
    ``ModelMultipleChoiceField`` looks every member key up, an empty-valued key included,
    so ``_decode_form_relation_multi`` binds a member keyed ``""`` as is.
    """
    if not _is_model_choice_field(form_field) or not _is_empty_form_value(form_key, form_field):
        return None
    return ValidationError(
        form_field.error_messages["invalid_choice"],
        code="invalid_choice",
        params={"value": value},
    )


def _decode_form_relation_single(
    value: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    key_attname: str | None,
    form_field: forms.Field,
    info: Info[object, object],
    index: int | None = None,
) -> tuple[object, FieldError | None]:
    """Decode ONE relation id to its form-key value, visibility-checked.

    The form coloring of the shared
    ``utils/write_values.py::decode_visible_relation`` spine:
    type-check + pk coercion -> visible object (a hidden / missing / wrong-model
    / uncoercible id is the uniform field-keyed ``FieldError``, closing the
    raw-pk visibility gap) -> the form-key projection via ``to_field_name``
    (``ModelChoiceField.prepare_value``). The ``related_model`` is the target the
    build recorded on the reverse-map spec (``InputFieldSpec.related_model``),
    from the SAME basis the generated id type used (the backing column's
    ``related_model`` for a ``ModelForm`` column, else the form field's
    ``queryset.model``). It is NOT re-derived from ``form_field.queryset.model``
    here: the decode reads the CLASS-level ``base_fields`` field, whose
    ``queryset`` is ``None`` under the request-scoped-choices idiom (a FK declared
    ``ModelChoiceField(queryset=None)`` that assigns the queryset in ``__init__``),
    which would crash with a bare ``AttributeError`` on ``None.model``. The
    ``form_field`` is still consulted for ``empty_values`` (the skip) and
    ``to_field_name`` (the projection), both class-level and queryset-independent.

    An explicit ``null`` (or any of the form field's ``empty_values``) as the WHOLE
    single-relation value is NOT an id to decode: it is a clear / no-value, skipped
    through UNCHANGED so the
    bound form's OWN validation decides - a required ``ModelChoiceField`` raises
    its field-keyed required error via ``form.is_valid()``, an optional one clears
    to the empty value (spec-038 Decision 8 step 1). Treating it as a raw pk
    instead would mis-report a decode-level "Invalid id for relation" error and
    block a legitimate nullable-FK clear.

    A visible row whose stored key (``key_attname``, the column a ``to_field`` relation
    stores) is ``NULL`` names no row, whatever column the form field is keyed by: the
    descriptor would store ``NULL`` and clear the relation. It is the uniform relation
    error the spine answers for a hidden or missing row.

    A visible row whose form-key value the field cleans to empty (a ``to_field_name``
    column holding ``""``) cannot be linked through a single ``ModelChoiceField``: binding
    that key would clear the relation the client named. It is the field's own
    ``invalid_choice`` error keyed to ``graphql_name`` (``_unrepresentable_choice``, the
    check an omitted relation's stored key passes in ``_reconstruct_partial_data``), and no
    form is bound.
    """

    def skip(candidate: object) -> bool:
        return _is_empty_form_value(candidate, form_field)

    form_key, error = decode_visible_relation(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
        info=info,
        async_recourse=_FORM_ASYNC_RECOURSE,
        skip=skip,
        project=form_field.prepare_value,
        key_attname=key_attname,
        index=index,
    )
    if error is not None or skip(value):
        return form_key, error
    choice_error = _unrepresentable_choice(form_field, form_key, value=value)
    if choice_error is not None:
        return None, validation_error_to_field_errors(
            ValidationError({graphql_name: [choice_error]}),
        )[0]
    return form_key, None


def _never_a_clear(_candidate: object) -> bool:
    """Skip nothing: a relation-id list element is always an id to decode."""
    return False


def _decode_form_relation_multi(
    values: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    key_attname: str | None,
    form_field: forms.Field,
    info: Info[object, object],
) -> tuple[list[object] | None, FieldError | None]:
    """Decode an M2M ``list[<id>]`` to a list of form-key values, visibility-checked (NET-NEW).

    Runs the shared ``decode_visible_relation`` spine over each element (so every member
    is type-checked, visibility-checked on its own branch, and ``to_field_name``
    converted) and returns the list under the form field name. Each member is passed
    its index, so a text error keys to the element (``boundWith.1``). The first member
    error short-circuits. An empty list is a valid clear.

    **A list element is never a clear.** The ``empty_values`` skip applies to the whole
    value only (below); an element in ``empty_values`` (a raw text pk ``""``) is an id like
    any other and gets the full decode, so a hidden or missing row is the uniform
    relation error. Skipped undecoded, it would be bound as is and the
    ``ModelMultipleChoiceField`` would look it up as a real key: linking a row its
    related type's ``get_queryset`` hides, or reading a pk as the ``to_field_name``
    value of another row. A visible member keyed ``""`` decodes to ``""`` and is
    linked, since the field looks every member key up.

    An explicit ``null`` (or any of the form field's ``empty_values``, including
    the empty list) clears the M2M: return ``[]`` so the bound form decides
    required-ness (required -> a field-keyed error via ``form.is_valid()``;
    optional -> clear) and ``None`` is NEVER iterated - iterating it would raise a
    top-level ``TypeError`` instead of the field-keyed envelope
    (spec-038 Decision 8 step 1).

    This DIVERGES, deliberately, from the model ``DjangoMutation`` path, which
    rejects an explicit ``null`` M2M with a field-keyed error
    (``mutations/resolvers.py::_relation_null_error`` - "use ``[]`` to clear, not
    ``null``"). A bound ``ModelForm`` follows Django form semantics, where an empty
    value clears an optional M2M (and a required one errors), so the form flavor
    honors the form's own required-ness rather than imposing the model path's
    stricter "null is never a valid replace-set" stance (spec-038 Decision 8 step 1).
    """
    if _is_empty_form_value(values, form_field):
        return [], None
    container = materialize_relation_id_container(values, graphql_name)
    if container[1] is not None:
        return None, container[1]
    keys: list[object] = []
    for index, value in enumerate(container[0]):
        key, error = decode_visible_relation(
            value,
            graphql_name=graphql_name,
            related_model=related_model,
            info=info,
            async_recourse=_FORM_ASYNC_RECOURSE,
            skip=_never_a_clear,
            project=form_field.prepare_value,
            key_attname=key_attname,
            index=index,
        )
        if error is not None:
            return None, error
        keys.append(key)
    return keys, None


def _decode_form_data(
    mutation_cls: _FormMutationClass,
    data: object,
    info: Info[object, object],
) -> tuple[dict[str, object], dict[str, object], FieldError | None]:
    """Decode the bound input dataclass into ``(provided_data, provided_files, error)`` (NET-NEW).

    Walks the provided input fields (``UNSET`` stripped) and, using the
    bind-stashed per-field reverse map (``mutation_cls._input_field_specs``,
    keyed by input attr), routes each value by ``kind`` to the right FORM-keyed
    place:

    - ``SCALAR`` -> ``provided_data[target_name]``, through the shared
      scalar leaf ``decode_scalar_leaf`` (text storability preflight +
      choice-enum unwrap).
    - ``RELATION_SINGLE`` / ``RELATION_MULTI`` -> the visibility-checked,
      ``to_field_name``-converted relation value(s) under ``target_name``.
    - ``FILE`` -> ``provided_files[target_name]`` (NEVER ``data=`` - a bound
      Django form reads uploads from ``files=``).

    A relation decode ``FieldError`` short-circuits. The reverse-map build + the
    ``UNSET``-strip walk + the kind dispatch are single-sited in
    ``utils/write_values.py::decode_provided_fields``; the SCALAR / RELATION /
    FILE store-into-dest handlers are the shared ``decode_field_handlers``
    factories. Flavor coloring stays in the relation decoders (``empty_values``
    skip + ``to_field_name``) and in ``file_dest=provided_files`` (Django
    ``files=``, never ``data=``).
    """
    form_fields = dict(mutation_cls.get_form_fields())

    provided_data: dict[str, object] = {}
    provided_files: dict[str, object] = {}
    handlers, scalar_handler = decode_field_handlers(
        provided_data,
        info=info,
        single=_decode_form_relation_single,
        multi=_decode_form_relation_multi,
        file_dest=provided_files,
        extra=lambda spec: {"form_field": form_fields[spec.target_name]},
    )
    error = decode_provided_fields(
        mutation_cls._input_field_specs,
        data,
        handlers=handlers,
        scalar_handler=scalar_handler,
    )
    if error is not None:
        return {}, {}, error
    return provided_data, provided_files, None


def _reconstruct_partial_data(
    mutation_cls: _FormMutationClass,
    instance: models.Model,
    provided_data: dict[str, object],
) -> tuple[dict[str, object], dict[str, list[ValidationError]]]:
    """Reconstruct the full bound ``data=`` for a partial ``ModelForm`` update (NET-NEW).

    For every non-file declared form field NOT overridden by ``provided_data``,
    supply the located row's value under the form field name, then overlay
    ``provided_data``; ``files`` is supplied separately and an omitted file is
    preserved via the bound ``form_class(instance=...)``'s ``initial``. The result
    lets the bound form validate a one-field change against the row's other
    (unchanged) values - e.g. a ``unique_together`` co-member comes from the row,
    not the input. That full-form validation is deliberate: if an unchanged stored
    value no longer passes the form's current validators, the mutation fails without
    writing any field. The client must include a valid replacement in the same
    partial input (or the consumer must repair the row out of band if narrowing
    excluded that field); untouched fields are not silently exempted.

    Three reconstruction shapes, each matching what the DECODE produces for a PROVIDED
    field so an omitted field binds byte-compatibly with a provided one:

    - **Scalars + a FK / OneToOne stored by its form key** come from ``model_to_dict``.
      A FK's value there is its ``attname``: the value of ``ForeignKey.target_field``
      (the related pk, or the ``ForeignKey(to_field=...)`` column). When the bound
      ``ModelChoiceField`` resolves its choice by that same column
      (``_stored_key_is_form_key``; every generated field does, since
      ``ForeignKey.formfield`` passes the target's name as ``to_field_name``), the
      stored value is exactly what ``ModelChoiceField.prepare_value`` produces for a provided FK,
      with no related-object fetch. A non-empty stored key that resolves to no row needs
      no fetch either: the bound form's own lookup refuses it as ``invalid_choice``.
    - **Every other single ``ModelChoiceField`` FK / OneToOne** is reconstructed from
      the related object via ``ModelChoiceField.prepare_value``, NOT ``model_to_dict``. The bound
      form validates it with ``queryset.get(<to_field_name or "pk">=value)``, so the
      stored value of another column fails ``to_python`` for an OMITTED unchanged FK
      ("Select a valid choice"), or matches a different row whose key equals it, while
      a PROVIDED unchanged FK passes: a ``to_field_name`` naming another column, or a
      ``to_field_name``-less field (keyed by pk) over a ``ForeignKey(to_field=...)``.
      The fetch reads the related row through the FK descriptor, unscoped by
      visibility like ``model_to_dict``. A FK whose column is NULL falls through to
      ``model_to_dict`` (the form's empty value). A non-null stored key that resolves to
      no row (a dangling key, which a ``db_constraint=False`` FK admits) cannot be
      projected: the stored key and the form key are different namespaces, so binding
      the stored key would let the form resolve an unrelated row whose form key equals
      it, and binding the empty value would clear the relation.

    - **M2M** is reconstructed as a list of ``form_field.prepare_value(obj)``
      (the ``to_field_name`` value, default ``obj.pk``) - NOT ``model_to_dict``'s
      list of related INSTANCES. For a ``ModelMultipleChoiceField`` with
      ``to_field_name`` set, the bound form looks members up by THAT key, so a
      ``model_to_dict`` (instance) shape would fail validation for an omitted M2M
      while a PROVIDED list (decoded to ``to_field_name`` values) passes - an
      omitted-vs-provided inconsistency (spec-038 Decision 8 step 4). Only a
      form field that is a real forward M2M on the model is reconstructed this way;
      a non-model extra is left to ``model_to_dict`` (which ignores non-columns).

    Every non-null stored single FK then passes one representability check
    (``_unrepresentable_choice``) before anything is bound: its form key (the stored value
    of a FK stored by its form key, else the projection of the related row) must be a value
    the field looks up. ``ModelChoiceField.to_python`` answers ``None`` for anything in the
    field's ``empty_values`` before its lookup, so a form key of ``""`` (a ``to_field`` or
    text key holding ``""``) would bind as empty and clear the relation, whether a row
    carries that key or not. Such a form key, and a projected FK's dangling stored key, are
    reported as the form field's own ``invalid_choice`` error (the error the form gives a
    choice it cannot resolve), and nothing is bound. A FK stored by its form key is decided
    by the stored value alone, with no query. A provided relation passes the same check in
    ``_decode_form_relation_single``.

    - **A field whose input shape disagrees with its column**
      (``forms/inputs.py::shape_disagreeing_column``: a ``MultipleChoiceField`` over a
      column that is neither an ``ArrayField`` nor a ``JSONField`` and lists no choices, or
      a built-in single-value field over an ``ArrayField``) is left out here: its stored
      value is in the column's shape, the single value the form made of a list or the list
      the form made of a single value, which the field refuses (or, for a field accepting
      the stored list itself, reads as a value made of it: a ``CharField`` its text, a
      ``BooleanField`` its truthiness).
      ``_bind_omitted_shape_disagreeing_initials`` binds it from the constructed form's own
      initial instead, so a form presenting the stored value in the field's shape (an
      ``__init__`` setting ``self.initial``) validates an omitted field unchanged, and one
      that does not fails it under the full-form validation above or, through such a field,
      writes the value made of the stored list.

    Reconstruction reads the form's FULL declared field set (``get_form_fields``),
    NOT the (possibly narrowed) generated input: a ``Meta.fields`` / ``Meta.exclude``
    narrowing drops excluded model-backed fields from the GraphQL input, but the
    bound ``ModelForm`` still validates EVERY field it declares, so an excluded
    required field (e.g. a narrowed-away ``category``) must still be reconstructed
    from the located row. A file field's ``model_to_dict`` value
    is the stored relative path, not a re-bindable ``data=`` value, so file fields
    are excluded (``forms.ImageField`` subclasses ``forms.FileField``, so the one
    ``isinstance`` catches both). Net-new vs. ``036``: the model update does
    ``setattr`` on the located instance, not a bound-data reconstruction.

    Returns ``(data, unresolved)``: ``unresolved`` maps each form field whose stored key
    the field cannot bind to its errors, in the ``form.errors.as_data()`` shape
    ``_form_errors_to_field_errors`` maps; the caller binds ``data`` only when ``unresolved``
    is empty.
    """
    # Only a ``ModelForm`` update locates a row to reconstruct from.
    model = backing_model_of(mutation_cls._mutation_meta)
    form_class = require(mutation_cls._mutation_meta.form_class, _is_form_class)
    form_fields = dict(mutation_cls.get_form_fields())
    m2m_field_names = {field.name for field in model._meta.many_to_many}
    links = {
        field.name: field
        for field in model._meta.concrete_fields
        if is_single_column_foreign_key(field)
    }

    m2m_data: dict[str, object] = {}
    relation_data: dict[str, object] = {}
    unresolved: dict[str, list[ValidationError]] = {}
    scalar_names: list[str] = []
    for name, form_field in form_fields.items():
        if name in provided_data or isinstance(form_field, forms.FileField):
            continue
        if shape_disagreeing_column(form_class, name, form_field) is not None:
            # Bound from the form's initial (``_bind_omitted_shape_disagreeing_initials``).
            continue
        if _is_model_multiple_choice_field(form_field) and name in m2m_field_names:
            try:
                related_objs = call_method(read_attr(instance, name), "all")
                m2m_data[name] = [form_field.prepare_value(obj) for obj in list_of(related_objs)]
            except (AttributeError, ObjectDoesNotExist):
                pass
        elif (
            name in links
            and _is_model_choice_field(form_field)
            and not _is_model_multiple_choice_field(form_field)
        ):
            stored_key = read_attr(instance, links[name].attname, None)
            if stored_key is None:
                scalar_names.append(name)
                continue
            same_key = _stored_key_is_form_key(links[name], form_field)
            if same_key:
                form_key = stored_key
            else:
                try:
                    related = read_attr(instance, name, None)
                except ObjectDoesNotExist:
                    related = None
                form_key = None if related is None else form_field.prepare_value(related)
            choice_error = _unrepresentable_choice(form_field, form_key, value=stored_key)
            if choice_error is not None:
                unresolved[name] = [choice_error]
            elif same_key:
                scalar_names.append(name)
            else:
                relation_data[name] = form_key
        else:
            scalar_names.append(name)

    base = model_to_dict(instance, fields=scalar_names)
    data = {
        **base,
        **m2m_data,
        **relation_data,
        **provided_data,
    }
    return data, unresolved


def _form_errors_to_field_errors(
    errors: dict[str, list[ValidationError]],
    mutation_cls: _FormMutationClass,
) -> list[FieldError]:
    """Map form-field-keyed errors onto the ``FieldError`` envelope.

    ``errors`` is a failed form's ``form.errors.as_data()``, or the omitted relations
    ``_reconstruct_partial_data`` could not resolve, in the same shape. Reuses the
    ``036`` ``validation_error_to_field_errors`` over a ``ValidationError(errors)``: the
    ``{field: [ValidationError, ...]}`` shape is what the mapper's ``error_dict`` branch
    consumes, so the form's ``NON_FIELD_ERRORS`` bucket keys to the ``"__all__"``
    sentinel exactly as a model ``full_clean()`` failure does (Decision 8 step 4).
    Each form field name is re-keyed to the GraphQL input field the client sent
    through ``build_error_key_map`` over ``mutation_cls._input_field_specs`` (a
    form spec's ``target_name`` IS the form field name); a form field the input
    does not expose keeps its form field name. No parallel mapper.
    """
    return validation_error_to_field_errors(
        ValidationError(errors),
        build_error_key_map(mutation_cls._input_field_specs),
    )


def _modelform_decode_step(
    mutation_cls: _FormMutationClass,
    data: object,
    info: Info[object, object],
    *,
    instance: models.Model | None,
) -> _DecodedForm | StepFailure:
    """Run the form ``decode_step``: form-decode + (ModelForm update) partial reconstruction.

    Decodes the bound input into a FORM-field-keyed ``(provided_data,
    provided_files)`` (the ``038`` ``_decode_form_data`` contract: visibility on
    every relation branch), then - for update - reconstructs the full bound
    ``data=`` so a one-field change validates against the row's unchanged values.
    A plain form has no located instance, so reconstruction is skipped. Returns
    ``(form_data, provided_files)`` for the write step, or a ``StepFailure``
    on a decode failure or an omitted relation whose stored key resolves to no row
    (the shared skeleton maps it to the error envelope; no form is bound).
    """
    provided_data, provided_files, decode_error = _decode_form_data(mutation_cls, data, info)
    if decode_error is not None:
        return StepFailure([decode_error])
    if instance is None:
        return provided_data, provided_files
    form_data, unresolved = _reconstruct_partial_data(mutation_cls, instance, provided_data)
    if unresolved:
        return StepFailure(_form_errors_to_field_errors(unresolved, mutation_cls))
    return form_data, provided_files


def _choice_key_identity(model: type[models.Model], key: str | None) -> object:
    """Return the column a model-choice key resolves its choice by, as a comparable token.

    Every spelling of the primary key (unset, ``""``, ``"pk"``, or the name of a
    ``primary_key`` field, a multi-table child's parent link included) is the one ``"pk"``
    token; any other key is the resolved field, so a name and its attname agree and two
    columns never do. ``None`` when ``model`` has no field of that name.
    """
    field = choice_key_field(model, key)
    if field is not None and field.primary_key:
        return "pk"
    return field


def _choice_key_label(key: object) -> str:
    """Render a ``_choice_key_identity`` token for a diagnostic."""
    if key is None:
        return "a name that is no field of its model"
    if key == "pk":
        return "its primary key"
    return repr(read_attr(key, "name", None))


def _assert_bound_choice_agreement(
    mutation_cls: _FormMutationClass,
    form: forms.BaseForm,
    form_data: dict[str, object],
) -> None:
    """Refuse a bound model-choice field that resolves its key other than the decode did.

    The decode resolves each relation id against the input's target model (the backing
    column's related model, else the class-level field's ``queryset.model``:
    ``forms/inputs.py::relation_target_model``) and binds the value the class-level
    field's ``to_field_name`` reads off that row (``ModelChoiceField.prepare_value``); an update binds
    an omitted relation's stored key the same way (``_reconstruct_partial_data``). The bound
    form looks that value up through ITS field, which an ``__init__`` or ``get_form``
    override may have rebuilt. For every bound name whose class-level and bound fields are
    both model-choice fields and whose bound field has a queryset, the bound queryset's model
    must be the target or a subclass of it, and the bound key must resolve to the same
    column (``_choice_key_identity``). Otherwise the form would read the key under another
    column or model and link a row the decode never admitted, a row the target's visibility
    query hides included, so the request is a ``ConfigurationError`` before ``is_valid()``
    and nothing is written. On a form that binds its class-level fields under the default
    ``get_form``, the build already refused such a column-backed field wherever every write
    binds it (``forms/inputs.py::require_class_choice_models``), so the model refusal
    reaches only an optional field a create sends.
    Reassigning the queryset over the same model and key (the
    request-scoped choices idiom) agrees. A bound field that is no longer a model-choice
    field, one whose queryset is ``None``, and a name the bound form does not declare are
    left to the form's own validation. The build names a target for every model-choice field
    an operation binds (``forms/inputs.py::require_column_kind_agreement`` refuses one over a
    column that is no relation, and a column-less one needs a class-level queryset), so the
    target is always a model here.
    """
    form_class = require(mutation_cls._mutation_meta.form_class, _is_form_class)
    basis = dict(mutation_cls.get_form_fields())
    for name in form_data:
        basis_field = basis.get(name)
        bound_field = form.fields.get(name)
        if (
            basis_field is None
            or bound_field is None
            or not _is_model_choice_field(basis_field)
            or not _is_model_choice_field(bound_field)
        ):
            continue
        target = require(relation_target_model(form_class, name, basis_field), is_model_class)
        queryset = bound_field.queryset
        # A queryset-less bound field looks nothing up.
        if queryset is None:
            continue
        bound_model = queryset.model
        if not issubclass(bound_model, target):
            raise ConfigurationError(
                f"{truth.name(mutation_cls)}: the bound form's field {name!r} looks its "
                f"choice up among {truth.name(bound_model)} rows, but the input decodes "
                f"{name!r} ids against {truth.name(target)}. The queryset get_form or the "
                "form's __init__ assigns must be over the model get_form_fields() declares.",
            )
        basis_key = _choice_key_identity(target, basis_field.to_field_name)
        bound_key = _choice_key_identity(bound_model, bound_field.to_field_name)
        if bound_key != basis_key:
            raise ConfigurationError(
                f"{truth.name(mutation_cls)}: the bound form's field {name!r} resolves its "
                f"choice by {_choice_key_label(bound_key)}, but the input binds "
                f"{truth.name(target)} rows by {_choice_key_label(basis_key)}. The "
                "to_field_name get_form or the form's __init__ sets must name the column "
                "get_form_fields() declares.",
            )


def _bind_omitted_shape_disagreeing_initials(
    mutation_cls: _FormMutationClass,
    form: forms.BaseForm,
    form_data: Mapping[str, object],
) -> dict[str, list[ValidationError]]:
    """Bind an update's omitted fields that read another shape than their column from the initial.

    ``_reconstruct_partial_data`` leaves such a field (``shape_disagreeing_column``)
    out of ``form_data`` when the input omits it. The form ``get_form`` built reads the
    field's initial (``form.get_initial_for_field``: the ``initial`` a ``ModelForm`` builds
    from the row and the ``initial=`` kwarg, after any ``__init__`` adjustment), which is
    bound under the keys the field's widget reads (``_bind_form_values``) before
    ``is_valid()``: the value the form itself presents for the unchanged field. A name the
    bound form no longer declares is left out. Returns the initials that cannot be bound,
    as ``_bind_form_values`` does.
    """
    form_class = require(mutation_cls._mutation_meta.form_class, _is_form_class)
    initials: dict[str, object] = {}
    for name, basis_field in mutation_cls.get_form_fields().items():
        if name in form_data or shape_disagreeing_column(form_class, name, basis_field) is None:
            continue
        bound_field = form.fields.get(name)
        if bound_field is not None:
            initials[name] = form.get_initial_for_field(bound_field, name)
    if not initials:
        return {}
    return _bind_form_values(form, initials)


#: What ``_bound_form_value`` answers for a field the bound form holds no value for.
_UNBOUND = object()


def _bound_form_value(form: forms.BaseForm, name: str, *, files: bool = False) -> object:
    """Return the value the bound form holds for its field ``name``, else ``_UNBOUND``.

    Read from ``form.files`` when ``files`` is set, else ``form.data``, under
    ``form.add_prefix(name)``: the key the package binds the field's whole value under, so
    a form prefix and a consumer ``add_prefix`` override are both honoured. A widget
    reading that one key reads the value there; one reading other keys (a ``MultiWidget``,
    a ``SplitArrayWidget``) reads its parts from them, bound beside the whole value
    (``_bind_under_form_keys``), so an explicit ``null`` reads as ``None`` here for every
    widget.
    A ``MultiValueDict`` (a ``QueryDict`` a ``get_form`` override binds) answers its last
    value, any other mapping its value.
    """
    bound: Mapping[str, object] = form.files if files else form.data
    key = form.add_prefix(name)
    return bound.get(key, _UNBOUND)


def _widget_parts(
    form: forms.BaseForm,
    name: str,
    value: object,
) -> tuple[str, dict[str, object]] | ValidationError:
    """Return ``(form.add_prefix(name), parts)``: how the bound form's field ``name`` reads ``value``.

    ``parts`` are the form-data entries the field's widget reads ``value`` from under
    ``form.add_prefix(name)`` (``utils/widgets.py::widget_entries``): that one key for a
    widget reading one, each part under its own key for a ``MultiWidget`` /
    ``SplitArrayWidget``. A value the widget cannot read (a list longer than a
    ``SplitArrayWidget``'s ``size``) answers Django's ``ArrayMaxLengthValidator``
    ``ValidationError`` instead. A ``disabled`` field reads no data (Django cleans its
    initial), so its value is bound whole under that one key, never split nor refused.
    """
    key = form.add_prefix(name)
    field = form.fields[name]
    if field.disabled:
        return key, {key: value}
    try:
        return key, widget_entries(read_attr(field, "widget"), key, value)
    except ValidationError as error:
        return error


def _set_field_entries(
    bound: MultiValueDict[str, object],
    key: str,
    parts: Mapping[str, object],
    values: list[object],
) -> None:
    """Set one field's entries on ``bound``: ``values`` under ``key``, each part as its one entry.

    A widget reading ``key`` alone reads ``values`` there (``get`` its last, ``getlist``
    all of them); a multi-key widget's part overrides ``key`` when the widget reads it.
    """
    bound.setlist(key, values)
    if list(parts) != [key]:
        for part_key, part in parts.items():
            bound.setlist(part_key, [part])


def _bind_form_values(
    form: forms.BaseForm,
    values: Mapping[str, object],
) -> dict[str, list[ValidationError]]:
    """Bind ``values`` (keyed by field name) into the form's data under the keys each widget reads.

    Each value is bound whole under ``form.add_prefix(name)`` (what ``_bound_form_value``
    reads) and in parts under each key a multi-key widget reads (``_widget_parts``). The
    bound data is replaced, never mutated: a ``MultiValueDict`` (a ``QueryDict`` a
    ``get_form`` override binds, immutable or not) is copied and each value set as its list
    of values (``setlist``), each part as its one entry, since unpacking it into a ``dict``
    would bind every other field's raw value list; any other mapping is merged into a
    ``dict``. Returns the error of each value its widget cannot read, keyed by field name;
    such a value is left unbound.
    """
    errors: dict[str, list[ValidationError]] = {}
    bindings: dict[str, tuple[str, dict[str, object]]] = {}
    for name, value in values.items():
        parts = _widget_parts(form, name, value)
        if isinstance(parts, ValidationError):
            errors[name] = [parts]
        else:
            bindings[name] = parts
    bound = form.data
    if isinstance(bound, MultiValueDict):
        merged = bound.copy()
        for name, (key, parts) in bindings.items():
            value = values[name]
            listed = truth.is_instance(value, list) or truth.is_instance(value, tuple)
            _set_field_entries(merged, key, parts, list_of(value) if listed else [value])
        form.data = merged
    else:
        merged_data: dict[str, object] = dict(bound)
        for name, (key, parts) in bindings.items():
            merged_data.update({key: values[name], **parts})
        form.data = merged_data
    return errors


def _bind_under_form_keys(form: forms.BaseForm) -> dict[str, list[ValidationError]]:
    """Re-key bare field-keyed ``form.data`` / ``form.files`` under the keys the form reads.

    The package binds by bare field name, and a form reads a field from the keys its
    widget reads under ``form.add_prefix(name)``: ``<prefix>-<name>`` for a prefixed form,
    and for a widget reading several keys (a ``MultiWidget``: ``SplitDateTimeWidget``'s
    ``<name>_0`` / ``<name>_1``; PostgreSQL's ``SplitArrayWidget``: ``<name>_0`` ..
    ``<name>_<size - 1>``) each of those keys. A form whose prefix comes from the form
    class, a ``get_form_kwargs`` ``prefix=``, or a ``get_form`` that passes the package's
    mapping (or a copy of it) with a prefix, and a field over such a widget, would read
    none of the client's values: a required field answers ``required``, an optional one
    its empty value. The re-key runs on the built form, before the package or
    ``is_valid()`` reads it, through the bound form's own fields; the form's own
    ``__init__`` sees the field-keyed mapping. The rule is by content, each mapping on
    its own: a mapping holding a form field's bare name that the form reads under other
    keys, and none of those keys, is re-keyed; a mapping already holding one was keyed by
    its builder, wholly or partly, and is left as bound. Only those field names move,
    each bound whole under ``form.add_prefix`` (what ``_bound_form_value`` reads) and in
    parts under the keys its widget reads (``_widget_parts``): any other key (a CSRF
    token, an extra value a consumer ``clean()`` reads) stays as bound, as a prefixed
    Django form leaves it. The bound mapping is never mutated: a re-keyed copy replaces
    it, a ``MultiValueDict`` (a ``QueryDict``, immutable or not) as a copy of its own type
    keeping each moved name's value list under its prefixed name and giving each part its
    one entry (a moved field's value is its one value, or the list of its several:
    ``_bound_value``), other data
    as a ``dict``, and a files ``dict`` as a ``MultiValueDict`` holding each value as its
    one entry, so ``get`` answers it unchanged; ``form.files`` is re-keyed under the prefix
    alone. A ``data`` mapping kept as bound still gets the parts of a multi-key widget
    field whose whole value it holds under ``form.add_prefix(name)`` with none of its part
    keys (``_bind_kept_parts``). A ``disabled`` field reads no data, so it is bound whole
    and never split. Nothing Django's form ``__init__`` derives from the bound data changes:
    ``is_bound`` reads only whether either mapping was passed.

    Returns the errors of each field whose value its widget cannot read (a list longer
    than a ``SplitArrayWidget``'s ``size``), keyed by field name.
    """
    moved = {name: keys for name in form.fields if (keys := _form_keys(form, name))}
    errors: dict[str, list[ValidationError]] = {}
    data: Mapping[str, object] = form.data
    if moved and _holds_bare_field_names(data, moved):
        if isinstance(data, MultiValueDict):
            form.data = _rekeyed_multi_value_dict(data, moved, form, errors)
        else:
            form.data = _rekeyed_data(data, moved, form, errors)
    else:
        _bind_kept_parts(form, errors)
    renamed = {name: key for name in form.fields if (key := form.add_prefix(name)) != name}
    # ``form.files`` is typed as a ``MultiValueDict``; the package and a ``get_form_kwargs``
    # pass a plain ``dict``, so the bound object is read untyped and narrowed.
    files = read_attr(form, "files")
    if (
        not renamed
        or not isinstance(files, dict)
        or not _holds_bare_field_names(
            form.files,
            {name: [key] for name, key in renamed.items()},
        )
    ):
        return errors
    if isinstance(files, MultiValueDict):
        form.files = _renamed_multi_value_dict(form.files, renamed)
        return errors
    # A plain ``dict``'s ``copy()`` is a ``dict``: its entries read each value as bound,
    # never a value list, and the bound mapping is left untouched.
    form.files = _multi_value_dict_of(form.files.copy(), renamed)
    return errors


def _form_keys(form: forms.BaseForm, name: str) -> list[str]:
    """Return the keys other than ``name`` the bound form reads its field ``name`` from.

    ``form.add_prefix(name)`` and every key the field's widget reads under it
    (``_widget_keys``); empty for an unprefixed field whose widget reads its bare name
    alone.
    """
    key = form.add_prefix(name)
    reads = dict.fromkeys([key, *_widget_keys(form, name)])
    return [read for read in reads if read != name]


def _widget_keys(form: forms.BaseForm, name: str) -> list[str]:
    """Return the keys the bound form's field ``name`` reads under ``form.add_prefix(name)``.

    Every key its widget reads (``utils/widgets.py::widget_keys``). A ``disabled`` field's
    keys are listed too; ``_widget_parts`` binds its value whole under the first of them.
    """
    return widget_keys(read_attr(form.fields[name], "widget"), form.add_prefix(name))


def _bound_value(bound: Mapping[str, object], name: str) -> object:
    """Return the value ``bound`` holds under ``name``: a ``MultiValueDict``'s values read whole.

    A ``MultiValueDict`` (a ``QueryDict``) holding one value answers it; one holding several
    (``setlist(name, [...])``, a ``doseq`` query string) answers the list of them, the
    inverse of ``_bind_form_values``'s ``setlist``. Any other mapping answers its value.
    """
    if not isinstance(bound, MultiValueDict):
        return bound[name]
    values = list_of(bound.getlist(name))
    return values[0] if len(values) == 1 else values


def _bind_kept_parts(form: forms.BaseForm, errors: dict[str, list[ValidationError]]) -> None:
    """Bind the parts of each whole value a hook keyed itself under a multi-key widget's keys.

    A mapping kept as bound (``_bind_under_form_keys``) may hold a multi-key widget field's
    whole value under ``form.add_prefix(name)`` and none of the keys the widget reads its
    parts from (a ``get_form_kwargs`` binding its own prefixed copy of the package's data):
    those parts are bound beside it through ``_widget_parts``, so the widget reads the value
    sent. A field whose widget reads one key, a ``disabled`` field, and one already holding
    any of its part keys are left as bound. A value the widget cannot read records its
    error in ``errors`` and binds nothing.
    """
    bound: Mapping[str, object] = form.data
    spread: dict[str, tuple[str, dict[str, object]]] = {}
    for name in form.fields:
        key = form.add_prefix(name)
        part_keys = [read for read in _widget_keys(form, name) if read != key]
        if not part_keys or key not in bound or any(read in bound for read in part_keys):
            continue
        parts = _widget_parts(form, name, _bound_value(bound, key))
        if isinstance(parts, ValidationError):
            errors[name] = [parts]
        else:
            spread[name] = parts
    if not spread:
        return
    if isinstance(bound, MultiValueDict):
        merged = bound.copy()
        for key, parts in spread.values():
            _set_field_entries(merged, key, parts, list_of(bound.getlist(key)))
        form.data = merged
        return
    merged_data: dict[str, object] = dict(bound)
    for _key, parts in spread.values():
        merged_data.update(parts)
    form.data = merged_data


def _holds_bare_field_names(bound: Container[object], moved: Mapping[str, Iterable[str]]) -> bool:
    """Whether ``bound`` holds a moved field's bare name and none of any field's moved keys."""
    return any(name in bound for name in moved) and not any(
        key in bound for keys in moved.values() for key in keys
    )


def _rekeyed_data(
    data: Mapping[str, object],
    moved: Mapping[str, object],
    form: forms.BaseForm,
    errors: dict[str, list[ValidationError]],
) -> dict[str, object]:
    """Return ``data`` as a ``dict`` with each moved field bound whole and in parts.

    A moved field's value is bound under ``form.add_prefix(name)`` and its parts under the
    keys its widget reads (``_widget_parts``); one whose widget cannot read it records its
    error in ``errors`` and binds nothing.
    """
    rekeyed: dict[str, object] = {}
    for name, value in data.items():
        if name not in moved:
            rekeyed[name] = value
            continue
        parts = _widget_parts(form, name, value)
        if isinstance(parts, ValidationError):
            errors[name] = [parts]
            continue
        rekeyed.update({parts[0]: value, **parts[1]})
    return rekeyed


def _multi_value_dict_of(
    entries: dict[str, _ValueT],
    renamed: Mapping[str, str],
) -> MultiValueDict[str, _ValueT]:
    """Return a ``MultiValueDict`` holding each value of ``entries`` as its one entry, renamed keys moved.

    ``get`` on it answers each value exactly as ``entries`` holds it.
    """
    rekeyed: MultiValueDict[str, _ValueT] = MultiValueDict()
    for name, value in entries.items():
        rekeyed.setlist(renamed.get(name, name), [value])
    return rekeyed


def _renamed_multi_value_dict(
    bound: MultiValueDict[str, _ValueT],
    renamed: Mapping[str, str],
) -> MultiValueDict[str, _ValueT]:
    """Return a copy of ``bound`` (its own type, mutable) with each renamed field's key moved."""
    rekeyed = bound.copy()
    rekeyed.clear()
    for name in bound:
        rekeyed.setlist(renamed.get(name, name), bound.getlist(name))
    return rekeyed


def _rekeyed_multi_value_dict(
    bound: MultiValueDict[str, object],
    moved: Mapping[str, object],
    form: forms.BaseForm,
    errors: dict[str, list[ValidationError]],
) -> MultiValueDict[str, object]:
    """Return a copy of ``bound`` (its own type, mutable) with each moved field re-keyed.

    A moved field keeps its value list under ``form.add_prefix(name)`` and gives each part
    its widget reads from the field's value (``_bound_value``: its one value, or the list
    of its several) its one entry (``_widget_parts``); one whose widget cannot read it
    records its error in ``errors`` and binds nothing.
    """
    rekeyed = bound.copy()
    rekeyed.clear()
    for name in bound:
        if name not in moved:
            rekeyed.setlist(name, bound.getlist(name))
            continue
        parts = _widget_parts(form, name, _bound_value(bound, name))
        if isinstance(parts, ValidationError):
            errors[name] = [parts]
            continue
        _set_field_entries(rekeyed, parts[0], parts[1], bound.getlist(name))
    return rekeyed


def _bound_form_or_field_errors(
    mutation_cls: _FormMutationClass,
    holder: _FormBuilder[_FormT],
    info: Info[object, object],
    decoded: _DecodedForm,
    *,
    instance: models.Model | None,
) -> tuple[_FormT, None] | tuple[None, list[FieldError]]:
    """Construct the bound form and run ``is_valid()`` once (both form flavors).

    Returns ``(form, None)`` on success or ``(None, errors)`` on a validation
    failure, the errors keyed through ``mutation_cls``'s input specs. A value the bound
    form's widget cannot read (a list longer than a ``SplitArrayWidget``'s ``size``, sent,
    reconstructed from the located row, or an omitted field's initial) is that field's
    ``max_length`` error before ``is_valid()`` runs (``_bind_under_form_keys``). ``holder``
    is the ``mutation_cls`` instance whose ``get_form`` hook builds the form. The
    persist hook (``form.save`` vs ``perform_mutate``) stays at the caller so
    ModelForm can return ``form.instance`` while a plain ``Form`` has no instance
    slot.
    """
    form_data, provided_files = decoded
    form = holder.get_form(info, data=form_data, files=provided_files, instance=instance)
    unbindable = _bind_under_form_keys(form)
    if instance is not None:
        unbindable |= _bind_omitted_shape_disagreeing_initials(mutation_cls, form, form_data)
    _assert_bound_choice_agreement(mutation_cls, form, form_data)
    if unbindable:
        return None, _form_errors_to_field_errors(unbindable, mutation_cls)
    if not form.is_valid():
        return None, _form_errors_to_field_errors(form.errors.as_data(), mutation_cls)
    return form, None


def _unstorable_cleaned_fields(
    form: _ModelFormAny,
) -> list[_FieldAny]:
    """Return the form's columns holding a value the column cannot store.

    Reads the instance the save was attempted on, never the database, so it is safe
    after a failed write left the transaction unusable. Two values qualify, both on a
    concrete, editable, non-primary-key column the form declares:

    - ``None`` on a ``null=False`` column. A ``blank=True`` column's optional form field
      cleans an omitted or explicit ``null`` to ``None`` (``ModelChoiceField``,
      ``IntegerField``, ``DateField``, ...), ``ModelForm._post_clean`` writes it onto
      ``form.instance``, and ``Model.clean_fields`` skips every ``blank=True`` column
      whose value is an empty value ("the developer is responsible for making sure they
      have a valid value"), so the database refuses it with a ``NOT NULL``
      ``IntegrityError``. The column's ``attname`` is read, so a foreign key with no
      related row reads ``None`` instead of raising.
    - ``""`` on a ``blank=True`` column that stores no empty string. Django's
      ``Field.formfield`` keeps ``TypedChoiceField(empty_value="")`` on a ``null=False``
      choice column whatever the column type, so a non-text choice column carries a
      value only ``save()`` refuses, for example the ``ValueError`` of an integer /
      float column's ``get_prep_value`` ("expected a number but got ''") or the
      ``ValidationError`` of a decimal / date / UUID / boolean column's ``to_python``.
      An optional single-value form field over an ``ArrayField`` (a ``ChoiceField``,
      ``TypedChoiceField`` or ``CharField`` whose ``clean_<field>``, if any, wraps only a
      non-empty value) cleans to its ``empty_value`` ``""`` too, which PostgreSQL refuses
      at the save with a ``DataError`` (malformed array literal).

    A text column storing ``""`` is a legitimate clear and is never named. The walk and
    the ``None`` rule are the model flavor's too (``utils/write_values.py::unstorable_columns``);
    the ``""`` rule is this flavor's, since only a form field cleans to it.
    """
    return unstorable_columns(form.instance, form.fields, also=_is_unstorable_blank)


def _is_unstorable_blank(field: _FieldAny, value: object) -> bool:
    """Whether ``value`` is the ``""`` a ``blank=True`` column storing no empty string refuses."""
    return field.blank and value == "" and not field.empty_strings_allowed


def _coerced_null_fields(form: _ModelFormAny) -> list[_FieldAny]:
    """Return the ``null=False`` columns whose explicit ``null`` their form field stored as a value.

    ``form.data`` is what ``get_form`` bound (after any override of the hook), read under
    the field's prefixed name (``_bound_form_value``). It holds ``None`` under a
    ``null=False`` column's form field only for an explicit ``null``: an update
    reconstructs an omitted field from the located row, which never stores ``NULL`` there,
    and an upload is bound through ``files=``, never ``data=``. The column's form field may
    clean that ``None`` to a value instead of ``None``: ``CheckboxInput`` reads it as
    ``False``, and the ``CharField`` / ``TypedChoiceField`` of a ``blank=True`` text column
    clean it to its ``empty_value`` ``""``. ``ModelForm._post_clean`` writes that value onto
    ``form.instance`` and the save would succeed, storing a value the client never sent.
    Such a column is named here, from the instance the save would write, so the write never
    runs.

    Only the form field's own cleaning of the bound ``None`` is named. A different cleaned
    value is the consumer form's (a ``clean_<field>`` / ``clean()`` default) and is
    written; a ``disabled`` field ignores the bound value; a form field that
    ``Meta.fields`` / ``Meta.exclude`` leaves out of ``construct_instance`` never writes
    the column. A ``None`` on the instance is left to the save-time diagnosis
    (``_unstorable_cleaned_fields``), as is a ``""`` the column cannot store: a consumer
    ``save()`` may still fill either in (django-trac 13776 / 20205). A ``null=True``
    column stores the clear, and an M2M is not a concrete column (an empty value
    clears it), so neither is named. A form field required by the form never gets here:
    its own ``required`` error fails ``is_valid()`` first.
    """
    instance = form.instance
    options = form._meta
    cleaned_data: Mapping[str, object] = form.cleaned_data
    coerced_fields: list[models.Field[object, object]] = []
    for field in instance._meta.concrete_fields:
        name = field.name
        form_field = form.fields.get(name)
        if field.null or form_field is None or form_field.disabled or not field.editable:
            continue
        if field.primary_key or (options.fields is not None and name not in options.fields):
            continue
        if options.exclude is not None and name in options.exclude:
            continue
        if _bound_form_value(form, name) is not None:
            continue
        value = read_attr(instance, field.attname)
        if value is None or _is_unstorable_blank(field, value):
            continue
        own_cleaning = call_method(form_field, "clean", read_attr(form[name], "data"))
        if cleaned_data.get(name) == own_cleaning:
            coerced_fields.append(field)
    return coerced_fields


def _unstorable_temporal_errors(form: _ModelFormAny) -> dict[str, list[ValidationError]]:
    """Map each column the form writes a datetime or time the write alias cannot store to its error.

    Django's ``forms.DateTimeField`` / ``forms.TimeField`` range-check nothing past what
    Python parses, so a valid form can carry an aware value the database refuses at
    ``save()`` (the adapter's ``OverflowError`` / ``ValueError``) or, on PostgreSQL,
    stores but cannot load back at the re-fetch. Every concrete column the cleaned data
    names is read from ``form.instance``, the value the save writes (what
    ``construct_instance`` set, else the column's stored or default value), and held to
    ``utils/errors.py::unstorable_temporal`` on the write pipeline's pinned alias (a date
    an ``ArrayField`` of datetimes still holds after ``Model.clean_fields`` is read as the
    midnight Django stores for it). A
    refused column answers the ``invalid`` ``UNBINDABLE_TEMPORAL_MESSAGE`` error under its
    form field name, the form-error shape the envelope maps
    (``_form_errors_to_field_errors``).
    """
    instance = form.instance
    cleaned_data: Mapping[str, object] = form.cleaned_data
    return {
        field.name: [ValidationError(UNBINDABLE_TEMPORAL_MESSAGE, code=FIELD_ERROR_CODE_INVALID)]
        for field in instance._meta.concrete_fields
        if field.name in cleaned_data
        and unstorable_temporal(
            field,
            read_attr(instance, field.attname),
            pinned_write_alias,
        )
    }


def _file_clears(provided_files: dict[str, object]) -> dict[str, object]:
    """Bind an update's explicit ``null`` file as Django's clear sentinel ``False``.

    A Django ``FileField`` reads ``None`` as "no change" (``clean(None, initial)`` returns
    the stored file) and ``False`` as "clear", the value ``ClearableFileInput`` returns for
    its clear checkbox. The input has no checkbox, and an omitted file is never in
    ``provided_files``, so a ``None`` there is the client's explicit ``null``: bound as
    ``False``, an optional form field cleans it to ``False`` and the model field's
    ``save_form_data`` stores the empty name. A create has no stored file to clear and
    keeps the ``None``.
    """
    return {name: False if value is None else value for name, value in provided_files.items()}


def _required_file_clears(form: forms.BaseForm) -> dict[str, list[ValidationError]]:
    """Map each required file field the bound form was asked to clear to its ``required`` error.

    A required ``FileField`` cannot clear: ``clean(False, initial)`` validates the
    ``False`` as ``None``, which returns the stored file, so ``is_valid()`` passes and the
    save would report success with the file the client asked to remove. ``form.files`` is
    what ``get_form`` bound (after any override of the hook), read under the field's
    prefixed name (``_bound_form_value``); a ``disabled`` field ignores it. The error is
    the form field's own ``error_messages["required"]``, code ``required``, the answer the
    same ``null`` gets on a create.
    """
    errors: dict[str, list[ValidationError]] = {}
    for name, form_field in form.fields.items():
        if _bound_form_value(form, name, files=True) is not False:
            continue
        if form_field.required and not form_field.disabled:
            message = form_field.error_messages["required"]
            errors[name] = [ValidationError(message, code="required")]
    return errors


def _column_null_errors(
    fields: list[_FieldAny],
) -> dict[str, list[ValidationError]]:
    """Map each column to its Django ``error_messages["null"]`` error, code ``null``.

    The column's own message is the source of truth, so a custom or translated message
    is sent as is; the error carries the field, code and path the model flavor gives the
    same input (``mutations/resolvers.py::_explicit_null_error``).
    """
    return {
        field.name: [ValidationError(field.error_messages["null"], code="null")]
        for field in fields
    }


def _modelform_save_or_field_errors(
    form: _ModelFormAny,
    mutation_cls: type[DjangoModelFormMutation],
    *,
    creating: bool,
) -> list[FieldError] | None:
    """Run the form's save; map a save-time failure to the envelope else ``None``.

    An update, and a create whose row ``Model.save()`` would write UPDATE-then-INSERT
    (``mutations/resolvers.py::adds_by_update_first``: a client-assigned key), split the
    save the way Django's admin does (``ModelAdmin.save_form`` / ``save_model`` /
    ``save_related``): the form's ``save()`` is called with ``commit=False``, the
    package saves the row it returned, then calls ``form.save_m2m()``. A create saves
    it through ``mutations/resolvers.py::save_new_row`` (an INSERT, whose
    ``force_insert`` the model's ``save()`` receives, so a row a concurrent transaction
    committed under that key is the ``constraint`` envelope, never overwritten); an
    update through ``mutations/resolvers.py::save_located_row`` inside
    ``forced_save_or_field_errors`` (an UPDATE of every table the row spans, whose
    ``force_update`` the model's ``save()`` receives, so a located row a concurrent
    transaction deleted is the ``conflict`` envelope, never re-INSERTed). Work a
    consumer ``ModelForm.save()`` override does only when committing does not run
    there; an override that saves the instance itself under ``commit=False`` is
    trusted code and that save is Django's plain ``save()``. Any other create is one
    ``form.save()``.

    The ``IntegrityError`` -> ``"__all__"`` and consumer ``ValidationError`` mappings
    are the shared ``save_or_field_errors`` (``forced_save_or_field_errors`` on an
    update), keyed through
    ``utils/errors.py::save_time_error_key_map`` over the backing model: a
    ``ModelForm`` field is named after its model field, and a model ``save()`` or
    signal receiver keys its error by the model field name or a forward relation's
    ``attname``, so both reach the GraphQL input name. On top, the one failure a
    VALID ``ModelForm`` can reach at ``save()`` on its own: a ``blank=True,
    null=False`` column the form cleaned to an empty value the column cannot store
    (an omitted or explicitly ``null`` optional field with no default to fall back
    on), which Django's ``clean_fields`` skipped. ``None`` reaches the database's
    ``NOT NULL`` ``IntegrityError``; ``""`` on a non-text choice column is refused by
    the column's ``get_prep_value`` / ``to_python`` with a ``ValueError`` or
    ``ValidationError``, and on an ``ArrayField`` (an optional single-value form
    field's ``empty_value``) by PostgreSQL with a ``DataError``. The exception is the
    trigger, never the diagnosis: the failure is re-raised as that column's
    field-keyed ``ValidationError`` only when
    ``_unstorable_cleaned_fields`` finds such a column on the instance the save was
    attempted on, so the error carries the field, code ``null`` and path the model
    flavor gives the same input (``mutations/resolvers.py::_explicit_null_error`` for
    an explicit ``null`` scalar, ``mutations/resolvers.py::_decode_single_relation_id``
    for an explicit ``null`` foreign key, ``mutations/resolvers.py::_created_row_integrity_errors``
    for a column a create omitted), with the column's Django ``error_messages["null"]``
    as the message (the form is the message source of truth, so a custom or translated
    message is sent as is).
    The diagnosis reads only the in-memory instance, so no query runs on a connection
    the ``IntegrityError`` / ``DataError`` left unusable; the shared mapper's envelope
    then rolls the pipeline transaction back (an update's failed save is already
    contained in ``forced_save_or_field_errors``'s savepoint). An ``IntegrityError`` no
    such column explains reaches the shared mapper unchanged (the ``"__all__"``
    envelope), such a ``ValueError`` or ``DataError`` propagates unchanged, and any
    other ``ValidationError`` is the consumer's own and maps as raised. Checking the
    instance AFTER the save attempt, not before, keeps Django's own ``blank=True,
    null=False`` contract (django-trac 13776 / 20205): a consumer ``save()`` that fills
    the value in never sees the guard.
    """

    def save() -> None:
        try:
            if not creating:
                save_located_row(form.save(commit=False))
                form.save_m2m()
            elif adds_by_update_first(form.instance):
                save_new_row(form.save(commit=False))
                form.save_m2m()
            else:
                _ = form.save()
        except (
            IntegrityError,
            DataError,
            ValueError,
            ValidationError,
        ):
            unstorable_fields = _unstorable_cleaned_fields(form)
            if not unstorable_fields:
                raise
            raise ValidationError(_column_null_errors(unstorable_fields)) from None

    def error_key_map() -> ErrorKeyMap:
        return save_time_error_key_map(
            mutation_cls._input_field_specs,
            backing_model_of(mutation_cls._mutation_meta),
        )

    if creating:
        return save_or_field_errors(save, error_key_map=error_key_map)
    # An update's form is bound to the located row, the target the zero-row
    # disambiguation probes.
    return forced_save_or_field_errors(
        form.instance,
        error_key_map=error_key_map,
        save_callable=save,
    )


def _modelform_write_step(
    mutation_cls: type[DjangoModelFormMutation],
    info: Info[object, object],
    instance: models.Model | None,
    decoded: _DecodedForm,
) -> models.Model | StepFailure:
    """Run the ``ModelForm`` ``write_step``: ``get_form`` -> ``is_valid`` -> ``form.save``.

    Constructs the form via the overridable ``get_form`` hook over the decoded bound
    data, runs ``is_valid()`` once (a failure maps ``form.errors`` onto the envelope
    via the reused ``validation_error_to_field_errors``), answers an update's explicit
    ``null`` on a required file field with its ``required`` error
    (``_required_file_clears``), refuses an explicit ``null`` a
    ``null=False`` column's own form field cleaned to a storable value as that column's
    field-keyed ``null`` error (``_coerced_null_fields``), refuses a datetime or time the
    write alias cannot store as that column's ``invalid`` error
    (``_unstorable_temporal_errors``), then writes through
    ``_modelform_save_or_field_errors`` (the form's save, split around
    ``commit=False`` on an update and a client-assigned-key create; the reused
    ``IntegrityError`` / ``ValidationError`` mappers, the update's ``conflict``, plus
    the unstorable ``blank=True, null=False`` column ``null`` mapping). Returns the saved instance
    (the skeleton's ``refetch_optimized`` re-fetches it by pk under the optimizer plan) or a
    ``StepFailure`` on a validation / write failure.
    """
    if instance is not None:
        decoded = (decoded[0], _file_clears(decoded[1]))
    bound = _bound_form_or_field_errors(
        mutation_cls,
        mutation_cls(),
        info,
        decoded,
        instance=instance,
    )
    if bound[1] is not None:
        return StepFailure(bound[1])
    form = bound[0]
    kept_files = _required_file_clears(form)
    if kept_files:
        return StepFailure(_form_errors_to_field_errors(kept_files, mutation_cls))
    coerced_fields = _coerced_null_fields(form)
    if coerced_fields:
        return StepFailure(
            _form_errors_to_field_errors(_column_null_errors(coerced_fields), mutation_cls),
        )
    temporal_errors = _unstorable_temporal_errors(form)
    if temporal_errors:
        return StepFailure(_form_errors_to_field_errors(temporal_errors, mutation_cls))

    # The pinned-alias WRITE phase opens for exactly the form's save: the form
    # construction + ``is_valid()`` above are database-read-only under the
    # pipeline's phased alias guard.
    with pipeline_write_phase():
        write_error = _modelform_save_or_field_errors(
            form,
            mutation_cls,
            creating=instance is None,
        )
    if write_error is not None:
        return StepFailure(write_error)
    # ``get_form`` returns a ``ModelForm[Any]`` (its model parameter is invariant),
    # whose ``instance`` is the saved row.
    return require_instance(read_attr(form, "instance"), models.Model)


def _plain_form_write_step(
    mutation_cls: type[DjangoFormMutation],
    info: Info[object, object],
    decoded: _DecodedForm,
) -> Literal[True] | StepFailure:
    """Run the plain-form ``write_step``: ``get_form`` -> ``is_valid`` -> ``perform_mutate``.

    Same construct/validate helper as ModelForm; the persist hook is
    ``perform_mutate`` (default ``form.save()`` if present, else no-op), whose
    ``IntegrityError`` / ``ValidationError`` maps to the envelope through
    ``save_or_field_errors``; a ``ValidationError`` keys by form field name, the
    same map ``_form_errors_to_field_errors`` uses. Returns ``True`` on success so
    the skeleton's model-less tail builds ``{ ok: true }``.
    """
    holder = mutation_cls()
    bound = _bound_form_or_field_errors(
        mutation_cls,
        holder,
        info,
        decoded,
        instance=None,
    )
    if bound[1] is not None:
        return StepFailure(bound[1])
    form = bound[0]

    # ``perform_mutate`` is the only write window (mirrors ``form.save`` /
    # ``serializer.save`` / ``instance.delete`` on the other flavors).
    with pipeline_write_phase():
        write_error = save_or_field_errors(
            lambda: holder.perform_mutate(form, info),
            error_key_map=lambda: build_error_key_map(mutation_cls._input_field_specs),
        )
    if write_error is not None:
        return StepFailure(write_error)
    return True


def _run_form_pipeline_sync(
    mutation_cls: _FormMutationClass,
    info: Info[object, object],
    data: object,
    id_: object,
) -> object:
    """Run the form-flavor rider of ``run_write_pipeline_sync`` (both form bases).

    ONE skeleton call serves both bases - the ``transaction.atomic()`` boundary
    + the locate preamble + the authorize-before-decode security ordering + the
    payload tail are single-sited in the skeleton, and the two form flavors
    share the form ``decode_step`` (form decode + partial reconstruction)
    verbatim. The ONLY divergence is the ``write_step``, picked on
    ``mutation_cls._primary_type``:

    - the ``ModelForm`` flavor (a real primary type) runs ``get_form`` ->
      ``is_valid`` -> ``form.save`` and the skeleton's optimizer re-fetch tail;
    - the plain ``DjangoFormMutation`` (``_primary_type is None``) has no row to
      locate, no object slot, and no re-fetch - the skeleton skips the locate
      and builds the ``{ ok, errors }`` payload while this flavor's write step
      runs ``perform_mutate``.

    This is the single sync body the async path wraps in one
    ``sync_to_async(thread_sensitive=True)`` call.
    """
    # ``_primary_type is None`` IS the plain-vs-``ModelForm`` flavor split; each arm
    # names its own differently-shaped step and binds it to the one declared name.
    write_step: Callable[[models.Model | None, _DecodedForm], object]
    if mutation_cls._primary_type is None:

        def plain_write_step(
            _instance: models.Model | None,
            decoded: _DecodedForm,
        ) -> Literal[True] | StepFailure:
            return _plain_form_write_step(mutation_cls, info, decoded)

        write_step = plain_write_step
    else:

        def modelform_write_step(
            instance: models.Model | None,
            decoded: _DecodedForm,
        ) -> models.Model | StepFailure:
            return _modelform_write_step(mutation_cls, info, instance, decoded)

        write_step = modelform_write_step

    return run_write_pipeline_sync(
        mutation_cls,
        info,
        data,
        id_,
        decode_step=lambda instance: _modelform_decode_step(
            mutation_cls,
            data,
            info,
            instance=instance,
        ),
        write_step=write_step,
    )


# The form-flavor module entry points (spec-038 Decision 8), via the shared factory
# (spec-039 - single-sourced with the model flavor). ``resolve_form_sync``
# normalizes the ``UNSET``-default kwargs to ``_run_form_pipeline_sync`` (the plain
# flavor never passes ``id``, so it defaults to ``UNSET`` and the plain body ignores
# it); ``resolve_form_async`` runs the same body through the shared
# ``run_pipeline_async`` boundary (one ``sync_to_async(thread_sensitive=True)`` call,
# so the ``transaction.atomic()`` + every ORM call run on one worker thread). Both
# form bases' ``resolve_sync`` / ``resolve_async`` seams delegate here by name.
resolve_form_sync: _SyncResolverEntry[_FormMutationClass]
resolve_form_async: _AsyncResolverEntry[_FormMutationClass]
resolve_form_sync, resolve_form_async = make_resolver_entries(_run_form_pipeline_sync)
