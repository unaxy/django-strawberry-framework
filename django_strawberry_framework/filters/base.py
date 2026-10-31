"""Filter primitives + ``RelatedFilter``.

Layers 1 and 2 of the six-layer pipeline (spec-027 Decision 3) plus the
five parity-floor primitives (spec-027 Decision 4):

- `Filter` re-exported from `django_filters` for surface continuity.
- `TypedFilter` -> `ArrayFilter` / `RangeFilter` / `ListFilter`: same contract as
  the matching `graphene_django/filter/filters/*.py` primitive minus the
  Graphene `_input_type` constructor argument (the Strawberry-side
  annotation is derived later by `convert_filter_to_input_annotation`).
- `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`: same contract as the
  matching Graphene primitive with the decode step substituted to
  `strawberry.relay.GlobalID.from_id(value)` per spec-027 Decision 4.
- `RelationPkFilter` / `RelationPkMultipleFilter`: their raw-primary-key
  siblings for a relation key whose target is not a Relay node (or has no
  `DjangoType`), typed and coerced through the column their predicate compares
  (`_compared_columns`).
- `EnumChoiceFilter` / `EnumLookupFilter`: the generated filters of a choice
  column, `exact` and every other single-value lookup on a text choice column.
  Each applies every member of the column's choice enum as a value, sent as an
  `EnumMemberValue` (`BLANK` is `""` on each lookup, a `"null"`-valued member
  matches `"null"`), while raw form data keeps django-filter's handling.
- `TextPatternFilter`: the generated filter of a text-pattern lookup (`iexact`,
  `contains`, `startswith`, `regex`, ...) on a non-text column, a `CharFilter`
  whose leaf is typed `String`.
- `LazyRelatedClassMixin`: re-exported from the package-root
  `sets_mixins` module (shared with the future order / aggregate sets);
  imported here so `RelatedFilter` and the `filters` public surface keep
  exposing it unchanged.
- `RelatedFilter`: collapsed port of the cookbook's
  `BaseRelatedFilter` + `RelatedFilter(BaseRelatedFilter, ModelChoiceFilter)`
  pair into a single consumer-facing class so the public surface matches
  the spec's single-symbol promise (spec-027 Decision 2).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, NamedTuple, TypeVar, final

from django.core.exceptions import FieldError, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.options import Options
from django.db.models.sql import Query
from django.forms import (
    CharField,
    Field,
    MultipleChoiceField,
    MultiWidget,
    SelectMultiple,
    TextInput,
    Widget,
)
from django.utils.functional import Promise
from django_filters import (
    CharFilter,
    ChoiceFilter,
    Filter,
    ModelChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
)
from django_filters import constants as _filter_constants
from django_filters.exceptions import FieldLookupError
from django_filters.fields import BaseCSVField, ChoiceField
from django_filters.filters import BaseInFilter, BaseRangeFilter, FilterMethod
from django_filters.filterset import BaseFilterSet, FilterSetOptions
from django_filters.utils import get_model_field, resolve_field
from django_filters.widgets import BaseCSVWidget
from graphql import GraphQLError
from strawberry import relay
from typing_extensions import TypedDict, Unpack, override

from django_strawberry_framework.exceptions import ConfigurationError, PathResolutionError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.relay import _coerce_pk_or_none, _node_id_slot
from django_strawberry_framework.sets_mixins import (
    LazyRelatedClassMixin as LazyRelatedClassMixin,  # noqa: PLC0414 - kept re-export path
)  # re-exported via filters.__init__
from django_strawberry_framework.sets_mixins import RelatedSetTargetMixin
from django_strawberry_framework.types.definition import DjangoTypeDefinition, _resolves_id_off_pk

# ``filters -> types`` is the documented safe (acyclic) import direction:
# ``types/relay.py`` module-top imports are stdlib/django/strawberry/``..exceptions``
# only - it reaches into ``filters`` / ``registry`` solely via in-function imports -
# so a module-top ``filters/base.py -> types/relay.py`` import does not close a load
# cycle. These are the single source of truth for the
# strategy->payload-shape mapping shared with the encoder and the decoder.
from django_strawberry_framework.types.relay import (
    MODEL_LABEL_STRATEGIES,
    TYPE_NAME_STRATEGIES,
    implements_relay_node,
    model_for_label_slot,
    node_definition_for_published_name,
    published_node_type_name,
)
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._array_field import array_element_field
from django_strawberry_framework.utils._narrowing import (
    is_concrete_field,
    is_list_or_tuple,
    is_str,
    optional_instance,
    read_attr,
    require,
)
from django_strawberry_framework.utils.errors import (
    FILTER_INVALID_ERROR_CODE,
    GLOBALID_INVALID_ERROR_CODE,
    GLOBALID_UNVALIDATABLE_ERROR_CODE,
    coded_error_extensions,
)
from django_strawberry_framework.utils.permissions import set_bound_definition
from django_strawberry_framework.utils.querysets import (
    base_queryset,
    coerce_field_value_or_none,
    lookup_target_fields,
    truncates_to_integer,
)
from django_strawberry_framework.utils.relations import (
    _classify_path_cached,
    is_model_class,
    relation_bool,
    stored_value_column,
    stored_value_link,
)
from django_strawberry_framework.utils.typing import object_result, strawberry_schema_from_info

#: django-filter's ``EMPTY_VALUES``: the values a filter treats as "not supplied". The stub
#: types the constant ``Any``; it is a tuple of values.
EMPTY_VALUES = require(read_attr(_filter_constants, "EMPTY_VALUES"), is_list_or_tuple)

# The three framework strategies whose emitted GlobalID a filter input CAN
# decode + validate (``model`` / ``type`` / ``type+model``). Derived from the
# encoder's own payload-shape memberships so the "validatable on a filter" set
# cannot drift from the "emitted by the encoder" set. Intentionally NOT
# ``types/base.py::STRING_GLOBALID_STRATEGIES`` (same extension today): that set
# is the CONFIGURABLE vocabulary (what a consumer may declare), this union is
# the DECODABLE set (what a filter can validate) - an encode-only string
# strategy would join the former, never the latter. Re-open if the two
# contracts ever share one record (a single strategy table).
FRAMEWORK_GLOBALID_STRATEGIES = MODEL_LABEL_STRATEGIES | TYPE_NAME_STRATEGIES
# ``callable`` / ``custom`` are encode-only in the GlobalID system (there is
# deliberately no decode path - see ``types/relay.py`` #"no ``{"callable",
# "custom"}`` literal"). A typed filter input for such a target can never
# validly consume the IDs its target emits, so the build-time audit
# (``finalizer._audit_globalid_filter_strategies``) rejects those bindings and
# this runtime guard is the defense-in-depth backstop for hand-built filtersets
# constructed outside finalization. The names are needed for the reject message
# so the literal lives here rather than being derived by exclusion.
ENCODE_ONLY_GLOBALID_STRATEGIES = frozenset({"callable", "custom"})

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from typing import TypeAlias

    from django.forms.boundfield import BoundField
    from django.utils.datastructures import MultiValueDict
    from django_stubs_ext import StrPromise
    from strawberry.schema import Schema

    from django_strawberry_framework.types.relay import _RelayDjangoType
    from django_strawberry_framework.utils.typing import ConcreteField, ModelField

    from .sets import FilterSet

    # A form-field validator (``validate_range`` checks any value's shape).
    _Validator: TypeAlias = Callable[[object], None]

    class _FieldOptions(TypedDict, total=False):
        """The keyword options ``forms.Field.__init__`` takes, forwarded unchanged."""

        required: bool
        widget: Widget | type[Widget] | None
        label: str | StrPromise | None
        initial: object
        help_text: str | StrPromise
        error_messages: Mapping[str, str | StrPromise] | None
        show_hidden_initial: bool
        validators: Iterable[_Validator]
        localize: bool
        disabled: bool
        label_suffix: str | None
        template_name: str | None
        bound_field_class: type[BoundField] | None

    # Every target shape the constructor and setter store; resolution happens on read.
    _FilterSetTarget: TypeAlias = (
        str | type[FilterSet] | Callable[[], type[FilterSet] | None] | None
    )
    #: Any ``UploadedFile``, binary or text.
    _UploadedFileAny: TypeAlias = UploadedFile[bytes] | UploadedFile[str]
else:
    # ``UploadedFile`` has no ``__class_getitem__`` at runtime: the hint stays the class.
    _UploadedFileAny = UploadedFile

_M = TypeVar("_M", bound=models.Model)


class TypedFilter(Filter):
    """Base marker for `ArrayFilter` / `RangeFilter` / `ListFilter`.

    Same contract as `graphene_django/filter/filters/typed_filter.py::TypedFilter`
    with the Graphene-only `_input_type` constructor argument dropped.
    The Strawberry-side annotation derives from the resolved filter
    instance at materialization time via `convert_filter_to_input_annotation`;
    there is no Graphene-style `input_type` property.
    """


def _applied_filter_method(
    method: Callable[[models.QuerySet[_M], str | None, object], models.QuerySet[_M]],
    qs: models.QuerySet[_M],
    field_name: str | None,
    value: object,
) -> models.QuerySet[_M]:
    """Call a filter's ``method``: django-filter's ``(queryset, name, value) -> queryset`` contract.

    The stub types the bound method ``Callable[..., Any]``; this states the call shape
    django-filter documents and invokes it with.
    """
    return method(qs, field_name, value)


class _EmptyListAwareFilterMethod(FilterMethod):
    """``FilterMethod`` that treats an empty list as a real value.

    Shared base for `ArrayFilterMethod` / `ListFilterMethod` (single-sited):
    a consumer-supplied `method=` callable must run for
    `[]` -- the empty list is a valid filter value for array / list-shaped
    filters -- unlike the default `FilterMethod`, which short-circuits the whole
    `EMPTY_VALUES` set. Only `None` short-circuits to the unfiltered queryset
    here; the empty list reaches `self.method`.
    """

    @override
    def __call__(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply the custom method, treating empty list as a real value."""
        if value is None:
            return qs
        return _applied_filter_method(self.method, qs, self.f.field_name, value)


def _install_empty_list_aware_method(
    filter_instance: TypedFilter,
    value: object,
    method_cls: type[FilterMethod],
) -> None:
    """Install ``method_cls`` when a consumer ``method=`` is set.

    Single owner of the ArrayFilter / ListFilter ``method`` setter body: both
    filters must swap django-filter's default ``FilterMethod`` (which treats ``[]``
    as EMPTY) for an empty-list-aware wrapper. The named ``*FilterMethod``
    subclass remains a per-filter type identity (graphene-parity public names);
    only the install sequence is shared.
    """
    # basedpyright: typeshed declares ``Filter.method`` a plain attribute; django-filter defines it
    # as a property, whose ``fset`` this reuses. It reports ``fset`` unknown on each arm of the
    # declared ``Callable | str | None``
    TypedFilter.method.fset(filter_instance, value)  # pyright: ignore[reportFunctionMemberAccess, reportAttributeAccessIssue, reportOptionalMemberAccess, reportUnknownMemberType]
    if value is not None:
        # django-filter's own ``method`` setter shadows ``filter`` per instance the same way
        # (``self.filter = FilterMethod(self)``).
        filter_instance.filter = method_cls(filter_instance)


def _apply_lookups(
    filter_instance: Filter,
    qs: models.QuerySet[_M],
    lookups: dict[str, object],
) -> models.QuerySet[_M]:
    """Apply ``distinct`` (when flagged) then ``get_method(qs)(**lookups)``.

    Owns the "honor ``distinct`` then bind the lookup kwargs in ONE
    ``filter``/``exclude`` call" seam used by whole-value list predicates and
    the integer ``__range`` decomposition. Callers choose the lookup dict;
    this helper never splits a list-shaped value into per-element OR clauses.
    """
    if filter_instance.distinct:
        qs = qs.distinct()
    return filter_instance.get_method(qs)(**lookups)


def _apply_lookup_predicate(
    filter_instance: Filter,
    qs: models.QuerySet[_M],
    value: object,
    *,
    field_name: str | None = None,
) -> models.QuerySet[_M]:
    """Apply ``distinct`` + ONE ``<field>__<lookup>`` predicate carrying ``value``.

    The whole-value-in-one-predicate form (never upstream's per-element OR
    delegation): for a list-shaped ``value`` under ``lookup_expr="in"``,
    splitting per element would hand Django a scalar rhs it iterates
    (``pk__in="26"`` -> ``IN ('2','6')``). Shared so the call sites - and
    any future whole-value filter - cannot drift back to per-element form.

    ``field_name`` overrides ``filter_instance.field_name`` for the lookup key
    (the ``lookup_expr`` is always the instance's own). A GlobalID or raw-key
    filter passes the path its value compares (``_globalid_predicate_path``,
    computed from the LIVE ``field_name`` at filter time): the target column a
    consumer ``relay.NodeID[...]`` names, or the pk-qualified relation path
    ``f"{live_field_name}__pk"`` for a forward relation stored on a non-pk
    ``to_field``, so the predicate never compares the raw FK-stored column.
    """
    field = filter_instance.field_name if field_name is None else field_name
    lookup = f"{field}__{filter_instance.lookup_expr}"
    return _apply_lookups(filter_instance, qs, {lookup: value})


def _match_none_queryset(filter_instance: Filter, qs: models.QuerySet[_M]) -> models.QuerySet[_M]:
    """Match nothing, or every row when ``exclude=True``.

    The restrictive-empty membership result shared by the filters that match
    nothing on an empty or rejected input. Must never degrade to django-filter's
    empty-value skip (which would silently widen a restrictive predicate to no
    constraint). The excluded empty set is a constraint whose answer is every
    row, never the input BY IDENTITY, which the package reads as "applied no
    constraint" (``FilterSet._q_for_branch``, ``FilterSet._apply_relation_leaf``):
    ``not`` of it matches no rows.
    """
    return qs.all() if filter_instance.exclude else qs.none()


def _materialize_list_shaped_values(value: object, *, message: str, code: str) -> list[object]:
    """Fail-closed materialization of a filter's list-shaped input.

    A FilterSet hands each filter its form field's cleaned value, a plain
    list, but a caller can invoke a filter's ``filter`` directly with an
    arbitrary object. Only the list/tuple shapes accepted by
    the form contract are meaningful; every other shape fails closed with the
    caller's coded GraphQL error instead of leaking a raw ``TypeError`` from a
    ``len()`` / iteration the shape can never satisfy.

    Iterating an accepted ``list`` / ``tuple`` (subclass included) is the
    value's own behaviour, so whatever its ``__iter__`` raises propagates.
    """
    if not is_list_or_tuple(value):
        raise GraphQLError(message, extensions=coded_error_extensions(code))
    return list(value)


# Private instance-attribute slot a generated GlobalID RELATION filter carries a
# BOOLEAN flag under, set ``True`` when, and only when, its relation's link onto
# the target model reads NON-pk columns (a ``to_field`` FK/O2O, a ``ForeignObject``
# off the pk, a many-to-many whose through foreign key onto the target has a
# ``to_field``). The raw-pk siblings (``RelationPkFilter`` /
# ``RelationPkMultipleFilter``) carry the same flag, because their value is the
# target's primary key too. ``filters/sets.py::FilterSet.filter_for_field`` stamps the
# flag when ``utils/relations.py::non_pk_forward_link`` answers a link for the relation's
# link onto the target; marked filters read it through
# ``_marked_pk_field_name`` and DERIVE the pk-qualified path
# ``f"{self.field_name}__pk"`` at filter time from the LIVE ``field_name``. Storing
# a boolean flag (never a frozen absolute path) is what makes the marker immune to
# re-prefixing: ``_expand_related_filter`` deepcopies a child leaf and rebases its
# ``field_name`` to ``"<relation>__<child_field>"``, and a boolean survives that
# rebase while a saved absolute string (e.g. ``"target__pk"``) would go stale and
# compile against the wrong relation (a ``FieldError`` on the parent model). Absent
# / falsy (the common FK-to-pk / M2M-to-pk / reverse / own-PK case) the predicate stays
# byte-identical to upstream's ``{field_name__lookup_expr: node_id}`` - a raw key,
# and a Relay GlobalID of a target whose id is its primary key, carry the target
# PK, which Django already resolves to the local FK column for an FK-to-pk, so only
# the genuine non-pk-``to_field`` case needs the ``__pk`` qualification. A GlobalID
# whose target's id is another column (a consumer ``relay.NodeID[...]``) compiles
# on that column and never reads the flag (``_globalid_predicate_path``).
_GLOBALID_RELATION_PK_ATTR = "_dst_globalid_relation_pk"


def _marked_pk_field_name(filter_instance: Filter) -> str | None:
    """Derive the pk-qualified relation path for a marked GlobalID filter, else ``None``.

    The single home for the ``_GLOBALID_RELATION_PK_ATTR`` read: a marked
    filter (a relation whose link onto its target reads non-pk columns) compiles against
    ``f"{self.field_name}__pk"`` DERIVED from the LIVE ``field_name`` at filter time
    (immune to ``_expand_related_filter`` rebasing, per ``_GLOBALID_RELATION_PK_ATTR``);
    every other target keeps the raw ``{field_name__lookup_expr: node_id}`` predicate
    (``None``). Sharing the derivation keeps marked filters from drifting apart: a
    per-method copy would let the empty-``node_id`` guard reach only one of them.
    A GlobalID filter reads it through ``_globalid_predicate_path``, which puts a
    target whose id is not its primary key first.
    """
    if getattr(filter_instance, _GLOBALID_RELATION_PK_ATTR, False):
        field_name = getattr(filter_instance, "field_name", None)
        if field_name:
            return f"{field_name}__pk"
    return None


def _bound_field_name(filter_instance: Filter) -> str:
    """Return the ORM path of a filter bound to a ``FilterSet``.

    django-filter's metaclass defaults every declared filter's ``field_name`` to its
    attribute name and ``filter_for_field`` names every generated one, so a bound
    filter's ``field_name`` is a string; only an unbound ``Filter()`` still carries
    the ``None`` its constructor defaults to. A ``None`` here is a filter the
    consumer rebound after class creation, refused rather than handed to a path walk.
    """
    field_name = filter_instance.field_name
    if field_name is None:
        raise ConfigurationError(
            f"{truth.kind(filter_instance)} has no field_name; a filter bound to a "
            "FilterSet must name the model field path it filters.",
        )
    return field_name


def _bound_resolved_field(filter_instance: Filter) -> _ResolvedField | None:
    """Return the field and column path a per-request filter's ORM path names.

    Reads the LIVE ``field_name`` against the filterset django-filter's
    ``BaseFilterSet.__init__`` stamps as ``filter_.parent``, so an expanded leaf whose
    ``field_name`` was rebased under a ``RelatedFilter`` prefix resolves the terminal
    field (``_filterset_resolved_field``).
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    return _filterset_resolved_field(parent, filter_instance)


def _bound_model_field(filter_instance: Filter) -> ModelField | None:
    """Return the model field a per-request filter's ORM path names on its FilterSet's model.

    The field of ``_bound_resolved_field``; ``None`` when the path names none.
    """
    resolved = _bound_resolved_field(filter_instance)
    return None if resolved is None else resolved.field


def _bound_value_field(filter_instance: Filter) -> ModelField | None:
    """Return the field each value a per-request filter applies is a value of.

    ``_filterset_value_field`` over the filterset django-filter's
    ``BaseFilterSet.__init__`` stamps as ``filter_.parent``.
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    return _filterset_value_field(parent, filter_instance)


def _reads_integer_transform(filter_instance: Filter) -> bool:
    """Whether a per-request filter compares an integer transform's output, not its column.

    A generated ``<column>__year__in``, an ``ArrayField``'s ``len``, or a transform a
    project registers on a column (``Field.register_lookup``) with an ``IntegerField``
    output: its values are integers no column stores (``_bound_value_field``), held to
    their range where the filter form asks the database
    (``filters/sets.py::_unbindable_value_errors``), never coerced through the column.
    """
    value_field = _bound_value_field(filter_instance)
    return isinstance(value_field, models.IntegerField) and value_field is not (
        _bound_model_field(filter_instance)
    )


class _LookupOperand(NamedTuple):
    """What one value a filter applies is compared as: a value of ``field``, the operand of ``lookup``.

    ``lookup`` is the terminal lookup past the transforms (``isnull`` for a ``year__isnull``
    leaf), whose operand is not a value of ``field`` when it is ``isnull``.
    """

    field: ModelField | None
    lookup: str


@cache
def _lookup_operand(column: ConcreteField, lookup_expr: str) -> _LookupOperand | None:
    """Return the output field of the transforms ``lookup_expr`` applies to ``column``, and its lookup.

    ``django_filters.utils.resolve_field``, the walk ``BaseFilterSet.filter_for_field``
    selects a generated leaf's filter class by (``filter_for_lookup`` keys its class on the
    terminal lookup this walk answers); it builds a query per call, so the answer is kept
    per ``(column, lookup_expr)``, both fixed when the FilterSet is defined: every key is
    kept, a set bounded by the columns and lookups the defined FilterSets name. No entry is
    invalidated: Django registers lookups and transforms at startup, before any FilterSet
    resolves one. ``None`` when that walk refuses the expression (upstream's
    ``FieldLookupError``): a name that is no transform or lookup of the column, as a
    relation hop is not.
    """
    try:
        output_field, lookup_name = resolve_field(column, lookup_expr)
    except FieldLookupError:
        return None
    return _LookupOperand(require(output_field, is_concrete_field), require(lookup_name, is_str))


class _ResolvedField(NamedTuple):
    """The model field a filter's ORM path names, and the ORM path that names its column.

    ``path`` is the filter's own ``field_name`` except for a path ending on a
    relation-valued primary key, where it continues through each key's target field to
    the column the key stores (``pk__id``, ``kiosk__pk__venue_ptr__id``). Django reads
    that path on the key's own column, with no join, and applies the column's lookups:
    an integer column's ``gte`` / ``lte`` read a bound past its range as widening or
    matching nothing, where the relation's lookups bind it raw. ``field`` is ``None`` for a
    path naming no field.
    """

    field: ModelField | None
    path: str


def _filterset_model_field(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> ModelField | None:
    """Return the model field ``filter_instance``'s ORM path names on ``filterset``'s model.

    The field of ``_filterset_resolved_field``; ``None`` when the path names none.
    """
    resolved = _filterset_resolved_field(filterset, filter_instance)
    return None if resolved is None else resolved.field


def _filterset_resolved_field(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> _ResolvedField | None:
    """Resolve ``filter_instance``'s ORM path on ``filterset``'s model to a field and column path.

    django-filter needs no model: no filterset, or one without a model, has nothing to
    walk and returns ``None``. A bound filter must name its path
    (``_bound_field_name``), walked by the package's path classifier
    (``utils/relations.py::_classify_path_cached``, the path being fixed when the
    FilterSet is defined), which reads Django's ``pk`` alias at any segment as that
    model's primary key, as the ORM does. A path ending on ``pk`` answers the column the
    key stores, the walk ``utils/relations.py::stored_value_link`` makes: a
    relation-valued key (a multi-table-inheritance parent link, a one-to-one primary key)
    is followed through each link's target field to the column, so ``pk`` /
    ``<relation>__pk`` is typed, cleaned and range-checked exactly as that column's own
    name is, its path naming the column (``_ResolvedField.path``). A path naming a
    relation explicitly answers the relation. A path the classifier refuses is answered by
    ``django_filters.utils.get_model_field``: ``None`` for a path naming no field (a
    typo, a missing hop), the field itself for a forward ``GenericForeignKey``, and
    ``RuntimeError`` for a relation hop that is still an unresolved lazy string (a
    FilterSet used before Django's app registry is populated), surfaced rather than read
    as an unknown field.
    """
    model = _filterset_model(filterset)
    if model is None:
        return None
    return _model_resolved_field(model, _bound_field_name(filter_instance))


def _model_resolved_field(model: type[models.Model], field_path: str) -> _ResolvedField:
    """Resolve ``field_path`` on ``model``: ``_filterset_resolved_field`` once the model is read."""
    try:
        field: ModelField = _classify_path_cached(model, field_path).terminal
    except PathResolutionError:
        return _ResolvedField(get_model_field(model, field_path), field_path)
    if field_path.rpartition(LOOKUP_SEP)[2] != "pk":
        return _ResolvedField(field, field_path)
    column, links = stored_value_link(field)
    return _ResolvedField(column, LOOKUP_SEP.join((field_path, *links)))


def _filterset_model(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
) -> type[models.Model] | None:
    """Return ``filterset``'s ``Meta.model``; ``None`` for no filterset or one without a model."""
    # django-filter's metaclass stores ``_meta = FilterSetOptions(...)`` on every filterset.
    meta = optional_instance(truth.static_attr(filterset, "_meta", None), FilterSetOptions)
    return getattr(meta, "model", None)


def _filterset_value_field(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> ModelField | None:
    """Return the field each value ``filter_instance`` compares on ``filterset``'s model is a value of.

    The value a lookup compares on its right-hand side belongs to the output of the
    transforms between the column and the lookup, wherever they are spelled: in the
    ``lookup_expr`` (a generated ``<column>__year`` / ``year__gt`` / ``year__in`` or
    ``date`` leaf, a declared ``lookup_expr="date"``), in the ``field_name``
    (``occurred_at__year``, an ``ArrayField``'s index ``counts__0`` or slice
    ``counts__0_2``), or both. The output is django-filter's own answer
    (``_lookup_operand``, the walk ``BaseFilterSet.filter_for_field`` selects a
    generated leaf's filter class by): ``year`` / ``len`` an ``IntegerField``, ``date`` a
    ``DateField``, an index the array's ``base_field``, a slice the array. A lookup
    applied to the column itself (``exact``, ``in``, ``isnull``, a text pattern such as
    ``icontains``, an ``ArrayField``'s ``contains``) answers the column. A null test's
    operand is a value of neither: its readers ask ``_filterset_lookup_operand`` for the
    terminal lookup, ``isnull`` past a transform too (``year__isnull``).

    A ``field_name`` naming a model field is resolved by ``_filterset_resolved_field``
    (``pk`` read as the column its key stores). One naming none is split as
    ``Query.build_filter`` splits a filter argument (``Query.solve_lookup_type``), its
    column the one the field part names (``utils/querysets.py::lookup_target_fields``)
    and its transforms walked ahead of the ``lookup_expr``. ``None`` for a filterset with
    no model, a path Django refuses (a name naming nothing, a ``FilteredRelation`` alias
    only the queryset a filter runs on holds), or one whose remainder is no transform of
    the column its field part reaches (a field part ending on a relation reaches its key,
    so ``tag__year`` and a queryset annotation past a relation, ``series__handle``, read
    none). A field the path names answers itself where the walk reads no transform: a
    relation, or a ``lookup_expr`` that continues the path across a relation
    (``field_name="shelf", lookup_expr="topic__icontains"``, which the filter's own
    ``filter`` hands Django whole). A ``method=`` filter answers its model field: its own
    method, not a lookup, receives the value, so it is published and cleaned by the column.
    """
    return _filterset_lookup_operand(filterset, filter_instance).field


def _filterset_lookup_operand(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> _LookupOperand:
    """Return ``_filterset_value_field``'s field with the terminal lookup it is compared by.

    The lookup is django-filter's answer past the transforms (``_lookup_operand``), and the
    filter's own ``lookup_expr`` wherever the field is not read off that walk.
    """
    lookup_expr = filter_instance.lookup_expr
    if read_attr(filter_instance, "method", None) is not None:
        return _LookupOperand(_filterset_model_field(filterset, filter_instance), lookup_expr)
    model = _filterset_model(filterset)
    if model is None:
        return _LookupOperand(None, lookup_expr)
    return _model_lookup_operand(model, _bound_field_name(filter_instance), lookup_expr)


@cache
def _model_lookup_operand(
    model: type[models.Model],
    field_path: str,
    lookup_expr: str,
) -> _LookupOperand:
    """Return ``_filterset_lookup_operand``'s answer for ``field_path`` and ``lookup_expr`` on ``model``.

    The answer depends on the three keys alone (a fresh ``Query`` holds no annotation),
    each fixed when the FilterSet is defined, so it is kept for every key, a set bounded
    by the declared and generated filters: the per-request filter reads it on every form
    build. A path naming no field is split as ``Query.build_filter`` splits it.
    """
    column = _model_resolved_field(model, field_path).field
    if column is None:
        query = Query(model)
        try:
            transforms, field_parts, _expression = query.solve_lookup_type(field_path)
        except FieldError:
            return _LookupOperand(None, lookup_expr)
        # The field part is the one Django's split just walked, so it names a column.
        path_column = require(
            lookup_target_fields(query, LOOKUP_SEP.join(field_parts))[0],
            is_concrete_field,
        )
        operand = _lookup_operand(path_column, LOOKUP_SEP.join((*transforms, lookup_expr)))
        return _LookupOperand(None, lookup_expr) if operand is None else operand
    if not is_concrete_field(column):
        return _LookupOperand(column, lookup_expr)
    operand = _lookup_operand(column, lookup_expr)
    return _LookupOperand(column, lookup_expr) if operand is None else operand


def _column_form_field(filter_instance: Filter, *, element: bool = False) -> Field | None:
    """Return the form field that cleans one value of a bound filter's column for a comparison.

    The column is the field each value the filter applies is a value of
    (``_bound_value_field``): the column itself, or the output of the transforms between
    it and the lookup (``year``'s ``IntegerField``, ``date``'s ``DateField``, an
    ``ArrayField`` index's ``base_field``), so a value is cleaned as the type it is
    published as. The field is the one django-filter's own ``gte`` filter for the column builds
    (``FilterSet._upstream_filter_for_lookup``: a ``NumberFilter``'s ``DecimalField`` for a
    decimal or integer column, a ``DateTimeFilter``'s ``DateTimeField`` for a datetime one,
    a ``CharFilter``'s ``CharField`` for text, ...), the owner of what one scalar value of
    that column may be, so a value a declared filter hands the ORM is held to the rule
    ``FilterSet._validate_form_or_raise`` already applies to ``gte`` / ``lte``. A
    comparison and not ``exact``: django-filter builds ``exact`` on a choice column as a
    ``ChoiceFilter``, whose ``ChoiceField`` refuses any value off the column's choices,
    while a range bound or a list member compares against the stored values whatever they
    are. Any django-filter ``FilterSet`` parent cleans, the package's or django-filter's
    own (a ``DjangoFilterBackend`` view's), so a value its column cannot hold is that
    form's error. The filter is the one the parent's class selects without the package
    ``FilterSet``'s own ``filter_for_lookup`` override: on a package subclass the method
    that override replaces (a django-filter base or mixin behind it included), on any
    other django-filter ``FilterSet`` its own ``filter_for_lookup``, a consumer override
    honoured as its ``FILTER_DEFAULTS`` and ``Meta.filter_overrides`` are. ``None`` for a
    filter bound to no ``FilterSet`` (a class-level declaration, a standalone filter), a
    path resolving to no column, a relation, or a column django-filter builds no filter
    for. A relation's form field is django-filter's
    ``ModelChoiceField``, which looks every value up in the target's default manager: a
    key no row holds would answer "Select a valid choice" where one the target's
    ``get_queryset`` hides answers rows, an existence oracle the package's own relation
    keys refuse (``_RelationIdentityListField``), so a relation's values reach the ORM as
    sent. ``element`` reads one element of a list value: an ``ArrayField`` column's element
    is a value of its ``base_field`` (``utils/_array_field.py::array_element_field``), any
    other column's a value of the column itself.
    """
    parent = read_attr(filter_instance, "parent", None)
    if not isinstance(parent, BaseFilterSet):
        return None
    model_field = _bound_value_field(filter_instance)
    if model_field is None:
        return None
    if element:
        model_field = array_element_field(model_field) or model_field
    if model_field.is_relation:
        return None
    if isinstance(parent, _filter_set_class()):
        filter_class, params = type(parent)._upstream_filter_for_lookup(model_field, "gte")
    else:
        filter_class, params = type(parent).filter_for_lookup(
            require(model_field, is_concrete_field),
            "gte",
        )
    if filter_class is None:
        return None
    return _built_filter(filter_class, filter_instance.field_name, params).field


def copied_form_field(filter_instance: Filter) -> Field:
    """Return the form field the filter's own class builds, read on a copy of the filter.

    ``Filter.field`` caches the field in the filter's ``_field`` (and a subclass may
    write more: a ``queryset`` into ``extra``, a field half built before it raises); a
    class-level declaration is shared by every request and deep-copied into each one, so
    a read of it must not write to it. The read runs on a deep copy, the copy
    django-filter itself makes per request, so the filter class's own ``field``,
    a consumer subclass's override included, builds it and the declaration keeps
    nothing.
    """
    return copy.deepcopy(filter_instance).field


def _refuses_deep_copy(value: object) -> bool:
    """Whether a deep copy of ``value`` raises; ``None`` copies."""
    try:
        _ = copy.deepcopy(value)
    except Exception:  # noqa: BLE001 - any refusal is the answer, never propagated
        return True
    return False


def copied_declared_filter(
    filter_instance: Filter,
    filterset_cls: type[BaseFilterSet],
    name: str,
    *,
    via: str = "",
) -> Filter:
    """Return a deep copy of ``filterset_cls``'s filter ``name``, or refuse the filter by name.

    django-filter deep-copies every filter of a ``FilterSet`` class into each instance,
    so a filter a deep copy refuses (a bound ``method=`` over an object holding a lock
    or a cache handler, a ``functools.partial`` over one, such a value in ``extra``)
    can serve no request. The refusal names the set, the attribute and the filter's
    class and carries the copy's own error as ``__cause__``. A filter whose ``method``
    itself refuses the copy is told the spellings a copy keeps (a FilterSet method's
    name, a plain function); any other is told to keep the object off the filter.
    ``via`` names the ``RelatedFilter`` the filter was reached through, when it was.
    """
    try:
        return copy.deepcopy(filter_instance)
    except Exception as exc:
        reached = f" (reached through RelatedFilter {via})" if via else ""
        advice = (
            'Pass method= as the name of a FilterSet method (method="<name>") or as a '
            "plain function."
            if _refuses_deep_copy(filter_instance.method)
            else "Keep the object off the filter: build it inside the filter's method or "
            "the FilterSet's filter_queryset, or hold it on a class."
        )
        raise ConfigurationError(
            f"FilterSet {truth.qualname(filterset_cls)}.{name}{reached}: "
            f"{truth.kind(filter_instance)} cannot be deep-copied "
            f"({truth.kind(exc)}: {truth.text(exc)}); django-filter deep-copies every "
            "filter for each request, so a filter must hold nothing a deep copy refuses "
            f"(a lock, a cache handler). {advice}",
        ) from exc


def _built_filter(
    filter_class: Callable[..., Filter],
    field_name: str | None,
    params: Mapping[str, object],
) -> Filter:
    """Build ``filter_class`` on ``field_name`` with django-filter's own ``params`` for it.

    ``params`` are the constructor options ``filter_for_lookup`` pairs with the class
    (``choices`` for a choice column, ``queryset`` for a relation), forwarded as
    ``filter_for_field`` forwards them; their values are typed by the class they belong
    to, which only the call can check.
    """
    return filter_class(field_name=field_name, **params)


class _ColumnCleanedFilter(TypedFilter):
    """A typed filter whose form field cleans its values as the column's ``gte`` cleans one.

    The form field reads its column's comparison form field (``_column_form_field``) only
    once the filter is bound to a ``FilterSet``, the package's or django-filter's own: the
    per-request copy django-filter binds builds its field once and hands it that field
    (``_hand_column_field``). A class-level declaration has no column to read, so its field
    is the one the rest of its class's MRO builds (a mixin's or a consumer subclass's
    ``field`` override between this class and ``Filter`` included), read on a deep copy so
    nothing is written to the filter: the declaration is shared by every request, and a
    field kept on it would ride every per-request deep copy and clean no value.
    """

    def _hand_column_field(self, _field: Field, /) -> None:
        """Give the form field this bound filter just built its column's comparison field."""
        raise NotImplementedError

    @property
    @override
    def field(self) -> Field:
        """The form field, holding the column's comparison form field once the filter is bound."""
        if read_attr(self, "parent", None) is None:
            return super(_ColumnCleanedFilter, copy.deepcopy(self)).field
        state = truth.instance_state(self)
        if "_field" in state:
            return super().field
        built = super().field
        self._hand_column_field(built)
        return built


class _MembershipCSVWidget(BaseCSVWidget):
    """Read raw form text as comma-separated members, an empty one as omission.

    The raw-form rule of the generated ``in`` (``_MembershipCSVField``) and of
    ``ListFilter`` / ``ArrayFilter`` (``_ElementField``). Form text (a querystring through
    ``DjangoFilterBackend``, a ``QueryDict``, a lazy translation string) splits on commas,
    ``?name=a,b`` reading ``["a", "b"]``. django-filter's ``BaseCSVWidget`` turns
    the empty string a querystring carries into ``[]``, which these filters read as the
    empty set; raw form data keeps django-filter's own rule (an empty ``?name=`` applies
    no constraint) by reading it as ``None``. Any other value (a list or tuple, the shape
    the GraphQL input layer sends) reaches the field as sent, so only a list or tuple
    reaches the filter as an explicit ``[]``.
    """

    # basedpyright: the stub types the CSV widget's return as ``list[str]``; the base already
    # returns ``None`` for an absent key, this override returns it for an empty one too, and
    # a value that is not form text as sent
    @override
    def value_from_datadict(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        data: Mapping[str, object],
        files: Mapping[str, object],
        name: str,
    ) -> object:
        """Return ``None`` for a raw empty string, any non-text value as sent, else split it."""
        value = data.get(name)
        if value == "":
            return None
        if value is None or isinstance(value, (str, Promise)):
            return super().value_from_datadict(data, files, name)
        return value


class _MembershipCSVTextInput(_MembershipCSVWidget, TextInput):
    """``_MembershipCSVWidget`` rendered as a text input, as django-filter's ``CSVWidget`` is."""


class _ElementField(Field):
    """Form field of ``ListFilter`` / ``ArrayFilter``: each element is cleaned by ``element_field``.

    ``element_field`` is the form field of the column's ``gte`` filter (an
    ``ArrayField``'s ``base_field``'s for an array column), so an element the column cannot
    hold is a form error rather than a value handed to the ORM, a text element is stripped
    and a naive datetime element made aware, under any django-filter ``FilterSet`` parent.
    A ``None`` element stays ``None``, and a value that is not a list or tuple, or a field
    with no ``element_field`` (a filter bound to no ``FilterSet``, a relation, a column
    django-filter builds no filter for), passes through as sent for the filter to judge.

    Raw form data reads as the generated ``in`` reads it (``_MembershipCSVWidget``, rendered
    as a text input): ``?name=a,b`` is ``["a", "b"]``, an empty ``?name=`` applies no
    constraint, and a list or tuple passes through, so an explicit ``[]`` keeps its meaning.
    A consumer ``widget=`` replaces it.
    """

    widget: type[Widget] | Widget = _MembershipCSVTextInput

    def __init__(
        self,
        *,
        element_field: Field | None = None,
        **kwargs: Unpack[_FieldOptions],
    ) -> None:
        super().__init__(**kwargs)
        self.element_field: Field | None = element_field

    @override
    def to_python(self, value: object) -> object:
        """Clean each element with ``element_field``; anything else passes through."""
        element_field = self.element_field
        if element_field is None or not is_list_or_tuple(value):
            return value
        return [None if element is None else element_field.clean(element) for element in value]


class _ElementCleanedFilter(_ColumnCleanedFilter):
    """``ListFilter`` / ``ArrayFilter`` half: each element is cleaned as ``gte`` cleans one."""

    field_class: type[Field] = _ElementField

    @override
    def _hand_column_field(self, field: Field, /) -> None:
        """Hand an ``_ElementField`` the comparison form field of one element of the column."""
        if isinstance(field, _ElementField):
            field.element_field = _column_form_field(self, element=True)


class ArrayFilterMethod(_EmptyListAwareFilterMethod):
    """Empty-list-aware `FilterMethod` for `ArrayFilter` (see the shared base)."""


class ArrayFilter(_ElementCleanedFilter):
    """Filter shaped for PostgreSQL `ArrayField` columns.

    Same contract as `graphene_django/filter/filters/array_filter.py::ArrayFilter`.
    The custom `method` setter swaps in `ArrayFilterMethod` so a
    consumer-supplied `method=` callable does not short-circuit on
    empty-list input - the empty list is a valid filter value here, unlike
    the default `FilterMethod` contract.

    Empty-list contract:
        `[]` is intentionally treated as a real value (not an
        `EMPTY_VALUES` short-circuit). The downstream meaning depends
        entirely on the bound `lookup_expr`:

        - `__contains=[]` matches every row on Postgres `ArrayField`
          (every list contains the empty list as a subset).
        - `__overlap=[]` matches no rows (empty overlap is vacuously
          false).
        - `__contained_by=[]` matches only rows whose array is empty.

        Consumers who want "any-of these values" semantics should bind
        `lookup_expr="overlap"` and pass `[value, ...]`; passing `[]`
        to `overlap` is a deliberate "match nothing" request. Consumers
        who want "no constraint" semantics should not send the filter
        at all (or send `None`, which short-circuits to the unfiltered
        queryset).

    Each element is cleaned by the form field of the column's own ``gte`` filter, an
    ``ArrayField`` column's ``base_field``'s (``_ElementField``), so an element the column
    cannot hold is a form error rather than a value handed to the ORM, a text element is
    stripped and a naive datetime element made aware. Raw form data (``DjangoFilterBackend``,
    a ``QueryDict``) reads ``?name=a,b`` as ``["a", "b"]`` and an empty ``?name=`` as no
    constraint (``_MembershipCSVWidget``); only a list or tuple is an explicit ``[]``.
    """

    # basedpyright: typeshed declares ``Filter.method`` a plain attribute, not the property it is,
    # so it reports ``setter`` unknown on each arm of the declared ``Callable | str | None``, and
    # the decorator it cannot type as untyped
    @override
    @TypedFilter.method.setter  # pyright: ignore[reportFunctionMemberAccess, reportAttributeAccessIssue, reportOptionalMemberAccess, reportUntypedFunctionDecorator, reportUnknownMemberType]
    def method(self, value: object) -> None:
        """Swap in `ArrayFilterMethod` when a consumer `method=` is set."""
        _install_empty_list_aware_method(self, value, ArrayFilterMethod)

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply the lookup; `[]` is a real value (not `EMPTY_VALUES`-ish).

        Every other value goes to django-filter's own ``Filter.filter``. The
        ``value == []`` comparison runs the value's own ``__eq__``; whatever it
        raises propagates.
        """
        if value == []:
            return _apply_lookup_predicate(self, qs, value)
        return super().filter(qs, value)


@dataclass(frozen=True)
class EnumMemberValue:
    """The form value of a generated choice enum member: its stored value, carried typed.

    ``filters/inputs.py::normalize_input_value`` wraps every member of a column's choice
    enum in this marker when the matched filter is a generated enum-member filter
    (``EnumChoiceFilter`` / ``EnumLookupFilter``). Form data never holds an instance (no
    querystring or raw ``data`` can spell one), so none of django-filter's form-data
    sentinels can reinterpret a member: ``BLANK`` (``""``) never meets the
    ``EMPTY_VALUES`` skip, a member whose value is ``"null"`` never meets
    ``ChoiceFilter``'s ``null_value`` ``IS NULL`` branch, and ``CharField`` never strips
    a member's whitespace. Matched by ``isinstance`` and compared by value, so it survives
    ``copy.deepcopy`` and pickling.
    """

    value: object


class _EnumMemberFieldMixin(Field):
    """Form-field half of the enum-member filters: cleans an ``EnumMemberValue`` to itself.

    The marker's ``value`` is validated exactly as the raw value would be (a ``ChoiceField``
    still rejects a value outside its choices), and the marker itself is returned so the
    filter applies the member's value untouched. Every other value cleans as the concrete
    form field cleans it, so raw form data (a DRF querystring through
    ``DjangoFilterBackend``) validates unchanged.
    """

    @override
    def clean(self, value: object) -> object:
        """Return an ``EnumMemberValue`` once its value validates, else the cleaned value."""
        if isinstance(value, EnumMemberValue):
            super().clean(value.value)
            return value
        return object_result(super().clean, value)


class _EnumMemberFilterMixin(Filter):
    """Filter half of the enum-member filters: an ``EnumMemberValue`` is always a predicate.

    The marker's value is applied as ``<field>__<lookup>`` whatever it is, so no empty-value
    skip or ``null_value`` branch can reinterpret an enum member; every other value goes to
    the concrete filter's own ``filter`` unchanged.
    """

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply the member's value as the lookup, else the concrete filter's ``filter``."""
        if isinstance(value, EnumMemberValue):
            return _apply_lookup_predicate(self, qs, value.value)
        return super().filter(qs, value)


# basedpyright: both bases define ``__init__``; the mixin's base is ``Field`` itself, so
# construction runs django-filter's ``ChoiceField.__init__``, which chains to ``Field``'s
class _EnumChoiceField(_EnumMemberFieldMixin, ChoiceField):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """``ChoiceField`` that cleans an ``EnumMemberValue`` to itself."""


# basedpyright: both bases define ``__init__``; the mixin's base is ``Field`` itself, so
# construction runs ``CharField.__init__``, which chains to ``Field``'s
class _EnumCharField(_EnumMemberFieldMixin, CharField):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """``CharField`` that cleans an ``EnumMemberValue`` to itself, its value never stripped."""


# basedpyright: both bases define ``__init__``; the mixin's base is ``Filter`` itself, so
# construction runs ``ChoiceFilter.__init__``, which chains to ``Filter``'s
class EnumChoiceFilter(_EnumMemberFilterMixin, ChoiceFilter):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """The generated ``exact`` filter of a choice column: every enum member is a value.

    ``FilterSet.filter_for_lookup`` returns this class wherever django-filter would generate
    a ``ChoiceFilter`` (an ``exact`` lookup on a column with ``choices``). Its GraphQL input
    is the column's generated enum, whose ``BLANK`` member carries ``""`` when the column
    admits the empty string (``types/converters.py::convert_choices_to_enum``). The input
    normalizer (``filters/inputs.py::normalize_input_value``) sends every member as an
    ``EnumMemberValue``, which compiles to ``<field> = <value>``: ``BLANK`` is ``= ''``
    rather than django-filter's empty-value skip, and a member whose value is ``"null"`` is
    ``= 'null'`` rather than ``ChoiceFilter``'s ``IS NULL`` branch. Every other value keeps
    ``ChoiceFilter``'s behavior, so a raw ``""`` (a querystring ``?field=`` under
    ``DjangoFilterBackend``) and an omitted field still apply no constraint, a raw
    ``"null"`` still applies ``IS NULL``, and a plain ``String`` filter's ``exact: ""``
    still applies none.
    """

    field_class: type[_EnumChoiceField] = _EnumChoiceField


class EnumLookupFilter(_EnumMemberFilterMixin, CharFilter):
    """The generated filter of every other single-value lookup on a text choice column.

    ``FilterSet.filter_for_lookup`` returns this class where django-filter would generate a
    ``CharFilter`` for a column with ``choices`` (``iexact``, ``contains``, ``startswith``,
    ``regex``, ``gt`` and their siblings), because the input publishes the column's choice
    enum on those lookups too. Each enum member reaches it as an ``EnumMemberValue`` and is
    applied as ``<field>__<lookup>`` with that value, so ``iExact: BLANK`` matches only the
    blank rows rather than the empty-value skip that would match every row, and
    ``contains: BLANK`` matches every non-null value. A raw form-data string
    (``?field__icontains=wo``) validates and filters exactly as ``CharFilter`` does.
    """

    field_class: type[CharField] = _EnumCharField


class TextPatternFilter(CharFilter):
    """The generated filter of a text-pattern lookup on a non-text column.

    ``FilterSet.filter_for_lookup`` returns it for ``iexact``, the ``contains`` /
    ``startswith`` / ``endswith`` families and ``regex`` / ``iregex`` listed on a column
    whose package default filter is not a ``CharFilter`` (a date, time, number, Boolean or
    UUID column): Django matches the pattern against the column's text rendering, so the
    value is cleaned as text, exactly as ``CharFilter`` cleans it. The class is the marker
    ``filters/inputs.py::_element_annotation`` reads to type the leaf ``String`` rather
    than the column's scalar or choice enum.
    """


# A range filter takes exactly a lower and an upper bound (django-filter's ``RangeField`` too).
_RANGE_BOUNDS = 2


def validate_range(value: object) -> None:
    """Reject range values whose length is not exactly two.

    Validator is only invoked by Django when the value is non-empty (the
    standard form-field contract); a one-element, three-element list, or
    non-sequence raises `ValidationError(code="invalid")`.
    """
    if not is_list_or_tuple(value) or len(value) != _RANGE_BOUNDS:
        raise ValidationError(
            "Invalid range specified: it needs to contain 2 values.",
            code="invalid",
        )


class _RangeWidget(MultiWidget):
    """Two-box widget that reads ``<name>_0`` / ``<name>_1``.

    Django's ``MultiWidget`` names its two boxes ``_0`` / ``_1``
    (``utils/widgets.py::multi_widget_keys``), the keys the range normalizer emits for
    ``RangeFilter``.
    """

    def __init__(self, attrs: dict[str, object] | None = None) -> None:
        super().__init__((TextInput, TextInput), attrs)

    @override
    def decompress(self, value: object) -> list[object]:
        """Split a two-element value, or two empty boxes when nothing is bound."""
        if is_list_or_tuple(value) and len(value) == _RANGE_BOUNDS:
            return list(value)
        return [None, None]


class RangeField(Field):
    """`forms.Field` whose default validator is `validate_range`.

    The widget reads the ``<name>_0`` / ``<name>_1`` keys the range normalizer
    emits for it (``utils/widgets.py::multi_widget_keys``). A missing pair arrives as
    ``[None, None]`` and ``to_python`` collapses it to ``None`` so django-filter skips
    the constraint instead of compiling ``col BETWEEN NULL AND NULL``.

    ``bound_field`` cleans each bound that is not ``None`` (``RangeFilter`` passes the
    form field of its column's ``gte`` filter), so a bound the column cannot hold is a
    form error rather than a value handed to the ORM. Without one the bounds pass
    through as sent.
    """

    # Class-level defaults ``forms.Field`` reads through the instance and never
    # mutates (``__init__`` copies ``default_validators`` into a fresh per-instance
    # ``validators`` list), so every ``RangeField`` shares them; annotated with the
    # types django-stubs declares on ``forms.Field``. ``empty_values`` keeps the
    # base's ``Sequence`` type: it is only read.
    default_validators: list[_Validator] = [validate_range]  # noqa: RUF012 - copied, never mutated
    empty_values: Sequence[object] = [
        None,
        [None, None],
        (None, None),
        ["", ""],
        ("", ""),
    ]
    # A widget class here; ``Field.__init__`` replaces it with an instance of that class.
    widget: type[Widget] | Widget = _RangeWidget

    def __init__(
        self,
        *,
        bound_field: Field | None = None,
        **kwargs: Unpack[_FieldOptions],
    ) -> None:
        """Build the field; ``bound_field`` cleans each bound, ``None`` passes them through.

        Args:
            bound_field: The form field that cleans one bound (``RangeFilter`` passes the
                one its column's ``gte`` filter builds), or ``None``.
            **kwargs: The options ``forms.Field`` takes.

        """
        super().__init__(**kwargs)
        self.bound_field: Field | None = bound_field

    @override
    def to_python(self, value: object) -> object:
        """Collapse a missing widget pair to ``None``, else clean each bound with ``bound_field``.

        A ``None`` bound stays ``None`` (a range left open on that side), and a value
        that is not a pair is returned as it is for ``validate_range`` to refuse.
        """
        if value in self.empty_values:
            return None
        bound_field = self.bound_field
        if bound_field is None or not (is_list_or_tuple(value) and len(value) == _RANGE_BOUNDS):
            return value
        return [None if bound is None else bound_field.clean(bound) for bound in value]


class RangeFilter(_ColumnCleanedFilter):
    """Filter that consumes a two-element list via `RangeField`.

    Both bounds apply the declared lookup (``lookup_expr="range"`` compiles to ``BETWEEN``),
    except over an integer column, where a ``range`` applies them as ``<field>__gte`` and
    ``<field>__lte`` in one predicate, as the generated ``range`` does
    (``IntegerRangeFilter``): Django's range-aware integer lookups read a bound past the
    column's range as widening or matching nothing, where ``BETWEEN`` would bind it raw and
    overflow the backend. A range with one bound left out or ``null`` applies that lone
    bound: a start alone as ``<field>__gte``, an end alone as ``<field>__lte``
    (django-filter's ``RangeFilter`` reads a one-sided range the same way). A range with
    neither bound constrains nothing.

    Each bound is cleaned by the form field of the column's own ``gte`` filter
    (``_column_form_field``), so a bound the column cannot hold (a non-finite decimal, a
    number past django-filter's ``1e50`` cap) is a form error as it is on ``gte``, a
    naive datetime bound is made aware and a text bound stripped; a bound off a choice
    column's choices is compared like any other value.
    """

    field_class: type[RangeField] = RangeField

    @override
    def _hand_column_field(self, field: Field, /) -> None:
        """Hand a ``RangeField`` the column's comparison form field as its ``bound_field``."""
        if isinstance(field, RangeField):
            field.bound_field = _column_form_field(self)

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply a one-sided range as its lone bound, an integer range as ``gte`` + ``lte``.

        A range input with one bound left out (or ``null``) reaches here as ``[start, None]`` /
        ``[None, end]``. The declared ``range`` lookup would compile it to ``BETWEEN x AND NULL``,
        which matches no row, so the lone bound applies on its own through `_apply_lookups`
        (``distinct`` and ``exclude`` honoured), through the transforms the ``lookup_expr``
        carries ahead of ``range`` (a ``year__range`` bound is a ``year__gte`` / ``year__lte``).
        ``[None, None]`` returns ``qs`` unchanged. Two
        bounds of a ``range`` over an integer column apply as ``gte`` + ``lte`` in one
        predicate (``IntegerRangeFilter.filter``), so a bound past the column's range never
        reaches the backend; any other two-bound range keeps the declared lookup. A lone bound
        and the ``gte`` + ``lte`` pair name the column the path resolves to
        (``_ResolvedField.path``), so over a relation-valued primary key they apply the stored
        column's lookups, never the relation's, which bind a bound past the column raw; a
        two-bound range over a relation-valued key storing a non-integer column applies
        ``range`` to the stored column too, which Django refuses on the relation itself.
        """
        if not (is_list_or_tuple(value) and len(value) == _RANGE_BOUNDS):
            return super().filter(qs, value)
        start, end = value
        if start is None and end is None:
            return qs
        resolved = _bound_resolved_field(self)
        path = _bound_field_name(self) if resolved is None else resolved.path
        # A lone bound compares what the range compares: the transforms ahead of its lookup
        # (``year__range``'s ``year``) stay on the path.
        bound_path = LOOKUP_SEP.join((path, *self.lookup_expr.split(LOOKUP_SEP)[:-1]))
        if end is None:
            return _apply_lookups(self, qs, {f"{bound_path}__gte": start})
        if start is None:
            return _apply_lookups(self, qs, {f"{bound_path}__lte": end})
        if self.lookup_expr == "range" and resolved is not None:
            if isinstance(resolved.field, models.IntegerField):
                return _apply_lookups(self, qs, {f"{path}__gte": start, f"{path}__lte": end})
            if path != self.field_name:
                return _apply_lookups(self, qs, {f"{path}__range": (start, end)})
        return super().filter(qs, value)


def _identifying_members(
    model_field: ModelField,
    members: list[object],
    alias: str,
) -> list[object]:
    """Return each member coerced through ``model_field``, dropping one that names no row.

    The coercion is the shared ``utils/querysets.py::coerce_field_value_or_none``
    primitive against the queryset's database ``alias``: a member ``to_python`` refuses,
    that database cannot bind, or outside the column's integer range there identifies no
    row. The column's own
    validators are not run, so a member they would refuse still matches a row that holds
    it.
    """
    kept: list[object] = []
    for member in members:
        coerced = coerce_field_value_or_none(model_field, member, alias=alias)
        if coerced is not None:
            kept.append(coerced)
    return kept


class ListFilterMethod(_EmptyListAwareFilterMethod):
    """Empty-list-aware `FilterMethod` for `ListFilter` (see the shared base)."""


class ListFilter(_ElementCleanedFilter):
    """Filter that accepts a list-shaped input (e.g. `__in` lookups).

    Same contract as `graphene_django/filter/filters/list_filter.py::ListFilter`:
    an empty list short-circuits to `qs.none()` (or a new queryset over every
    row when `exclude=True`) instead of being normalized into a "no value
    supplied" pass-through. Each element is cleaned by the form field of the
    column's own ``gte`` filter (``_ElementField``), as the generated ``in`` cleans
    its members, so an element the column cannot hold is a form error rather than a
    value handed to the ORM, a text element is stripped and a naive datetime element
    made aware; an element off a choice column's choices is a value like any other.
    Over an integer column, an ``in`` drops each element outside the column's integer
    range on the queryset's database: it can identify no row, and bound raw it would
    overflow the backend. A fractional element names no row and is dropped too, never
    truncated to an integer. A list whose every element drops matches nothing (every row
    when excluding). The column's own validators are not applied, so an element they
    would refuse still matches a row that holds it. Raw form data (``DjangoFilterBackend``,
    a ``QueryDict``) reads as the generated ``in`` reads it (``_MembershipCSVWidget``):
    ``?name=a,b`` is ``["a", "b"]`` and an empty ``?name=`` applies no constraint.
    """

    # basedpyright: typeshed declares ``Filter.method`` a plain attribute, not the property it is,
    # so it reports ``setter`` unknown on each arm of the declared ``Callable | str | None``, and
    # the decorator it cannot type as untyped
    @override
    @TypedFilter.method.setter  # pyright: ignore[reportFunctionMemberAccess, reportAttributeAccessIssue, reportOptionalMemberAccess, reportUntypedFunctionDecorator, reportUnknownMemberType]
    def method(self, value: object) -> None:
        """Swap in `ListFilterMethod` when a consumer `method=` is set."""
        _install_empty_list_aware_method(self, value, ListFilterMethod)

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Short-circuit empty-list inputs to `qs.none()` (every row when excluding).

        The raw input is shape-gated through
        ``_materialize_list_shaped_values`` before the emptiness probe, so a
        scalar, a one-shot iterator, or a generator never reaches ``len()``,
        and a string value under an ``in`` lookup is never iterated
        char-by-char (``in: "26"`` compiling to ``IN ('2','6')``). Only the list/tuple
        shapes the form contract delivers are meaningful; everything else is
        a coded reject. An ``in`` over an integer column then keeps only the elements inside
        the column's integer range on the queryset's database
        (``_identifying_members``); a list with none left matches nothing, or every
        row under ``exclude`` (``_match_none_queryset``).
        """
        if value is None:
            return super().filter(qs, value)
        value = _materialize_list_shaped_values(
            value,
            message="Invalid filter value: expected a list.",
            code=FILTER_INVALID_ERROR_CODE,
        )
        if len(value) == 0:
            return _match_none_queryset(self, qs)
        model_field = _bound_model_field(self) if self.lookup_expr == "in" else None
        if isinstance(model_field, models.IntegerField):
            kept = _identifying_members(model_field, value, qs.db)
            if not kept:
                return _match_none_queryset(self, qs)
            return super().filter(qs, kept)
        return super().filter(qs, value)


class _MembershipCSVField(BaseCSVField):
    """``BaseCSVField`` bound to ``_MembershipCSVWidget``."""

    base_widget_class: type[_MembershipCSVWidget] = _MembershipCSVWidget


class MembershipInFilter(BaseInFilter):
    """The generated ``in`` filter of every non-relation column: ``[]`` is the empty set.

    ``FilterSet.filter_for_lookup`` puts this base in front of the ``in`` class
    django-filter builds (``membership_in_filter_class``); ``IntegerInFilter`` is the
    integer column's. Omission and ``None`` apply no constraint, an explicit ``[]``
    matches no rows (every row under ``exclude``), as Django's own
    ``filter(<field>__in=[])`` does, and a non-empty list binds as one ``__in``
    predicate. A raw ``?field__in=`` through ``DjangoFilterBackend`` keeps
    django-filter's rule (``_MembershipCSVWidget``).
    """

    base_field_class: type[BaseCSVField] = _MembershipCSVField

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Match nothing for an explicit ``[]``; otherwise django-filter's ``__in``.

        The raw input is shape-gated through ``_materialize_list_shaped_values``
        (``ListFilter`` / ``IntegerInFilter`` containment): only the list/tuple
        shapes the form contract delivers are meaningful; everything else is a
        coded reject.
        """
        if value is None:
            return qs
        members = _materialize_list_shaped_values(
            value,
            message="Invalid filter value: expected a list.",
            code=FILTER_INVALID_ERROR_CODE,
        )
        if not members:
            return _match_none_queryset(self, qs)
        return super().filter(qs, members)


def membership_in_filter_class(in_filter_class: type[BaseInFilter]) -> type[MembershipInFilter]:
    """Put ``MembershipInFilter`` in front of the ``in`` class django-filter built.

    ``class ConcreteInFilter(MembershipInFilter, in_filter_class): pass`` over whatever
    ``BaseInFilter`` subclass ``BaseFilterSet.filter_for_lookup`` returned, keeping its
    name: a ``class`` statement, so the body carries exactly the interpreter's
    structural dunders the sequence-profile validator
    (``filters/sets.py::_dynamic_csv_profile_for``) unwraps, and a NEW class per call,
    as upstream builds, so a class one filter set's instantiation has deep-copied (which
    stamps ``copyreg``'s ``__slotnames__`` on it) is never another filter set's.
    """

    class ConcreteInFilter(MembershipInFilter, in_filter_class):
        pass

    ConcreteInFilter.__name__ = truth.name(in_filter_class)  # truth: ok built class renamed
    return ConcreteInFilter


class IntegerInFilter(MembershipInFilter, NumberFilter):
    """Integer ``__in`` filter that drops out-of-range members and is empty-aware.

    `filter_for_lookup` routes a non-relation integer column's `in` lookup here
    instead of django-filter's plain `BaseInFilter`. Two behaviours layer onto the
    default element-binding `__in`:

    - **Range coercion**: each member is coerced through the column against the
      queryset's database (`_identifying_members`) and one that database cannot bind or
      outside the column's integer range there is dropped, so it never reaches the backend
      as a raw `OverflowError`. A fractional member (raw form data cleans `"1.5"` to a
      `Decimal`) names no row and is dropped, never truncated to an integer. The column's
      own validators are not run, so a member they would refuse still matches a row that
      holds it, as `exact` matches it.
    - **Empty-aware match-nothing**: a NON-empty input whose members ALL
      drop - every value is out of range and can identify no row - matches NOTHING,
      so it short-circuits to `qs.none()` rather than degrading to django-filter's
      empty-value SKIP, which would silently widen a restrictive `in` to no
      constraint (return every visible row). An explicitly empty input (`in: []`) is
      the empty set too (`MembershipInFilter`). A mixed input keeps its valid
      members. For an `exclude` filter the complement of "no row" is "every row", so
      it returns a new queryset over every row.

    A lookup through an integer transform (a generated `<column>__year__in`, `iso_year`,
    `month`, an `ArrayField`'s `len`, a transform a project registers with an
    `IntegerField` output) compares the transform's output, a value no column stores
    (`_reads_integer_transform`), so its members are not coerced through the column: each
    binds as Django's lookup prepares it for that output, and the filter form's bind ask
    (`filters/sets.py::_unbindable_value_errors`) refuses an integer transform's member
    past the integer range the queryset's database stores for it, as it does for a
    declared `in` over the same transform. A member inside that range that no row holds
    matches nothing, and a fractional member equals no integer output and is dropped.
    """

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Coerce members, matching nothing when the input is empty or fully drops.

        The raw input is shape-gated through ``_materialize_list_shaped_values``
        first, so a scalar never reaches the coercion loop and a string value is
        never iterated char-by-char (``in: "26"`` coercing to ``[2, 6]`` would be
        a wrong-result membership). Only the list/tuple shapes the form contract
        delivers are meaningful; everything else is a coded reject.
        """
        if value is None:
            return super().filter(qs, value)
        value = _materialize_list_shaped_values(
            value,
            message="Invalid filter value: expected a list of integers.",
            code=FILTER_INVALID_ERROR_CODE,
        )
        if _reads_integer_transform(self):
            # A transform's output names no stored column: each member binds as the
            # lookup prepares it, so one past the integer range the database stores for
            # the output is refused by the filter form's bind ask, never dropped. A
            # fractional member equals no integer output and is dropped.
            output = _bound_value_field(self)
            kept = [member for member in value if not truncates_to_integer(output, member)]
            if not kept:
                return _match_none_queryset(self, qs)
            return super().filter(qs, kept)
        model_field = _bound_model_field(self)
        if model_field is not None:
            kept = _identifying_members(model_field, value, qs.db)
            if not kept:
                # An empty membership list, or one whose every value is out of range,
                # matches no row; never the empty-value skip that would return all rows.
                return _match_none_queryset(self, qs)
            return super().filter(qs, kept)
        return super().filter(qs, value)


class IntegerRangeFilter(BaseRangeFilter, NumberFilter):
    """Integer ``__range`` filter that never overflows the backend on an out-of-range bound.

    `filter_for_lookup` routes a non-relation integer column's `range` lookup here
    instead of django-filter's plain `BaseRangeFilter` (the sibling of the `in` ->
    `IntegerInFilter` reroute). A `__range` lookup binds BOTH bounds directly as query
    parameters (`WHERE col BETWEEN a AND b`), so a bound past the column's signed-64-bit
    range reaches the backend as a raw `OverflowError` (`Python int too large to convert
    to SQLite INTEGER`) escaping as a top-level error - the same defect `IntegerInFilter`
    fixes for the element-binding `__in`. A single-bound `gte` / `lte`, by contrast, is
    resolved by Django's range-aware integer lookups to "matches everything / nothing"
    BEFORE binding and never overflows.

    The two-bound range is therefore decomposed into a `gte` (lower) + `lte` (upper) pair
    applied in ONE predicate, so each bound flows through Django's range-aware integer
    lookup instead of a raw ``BETWEEN`` bind. This preserves inclusive-range semantics
    (`col >= start AND col <= end`) and its exact complement under `exclude`
    (`NOT (col >= start AND col <= end)`), while an out-of-range bound simply widens
    (a below-min lower / above-max upper imposes no constraint) or empties the match
    (an above-max lower / below-min upper can identify no row) - the same outcome a raw
    ``BETWEEN`` would express if the backend could bind the value.

    A lookup carrying a transform (a generated ``<column>__year__range``, ``iso_year``,
    ``month``, an ``ArrayField``'s ``len``) applies the pair to the transform's output
    (``<column>__year__gte`` + ``<column>__year__lte``), never to the column itself.
    """

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply the range as a decomposed ``gte`` + ``lte`` pair (never a raw ``BETWEEN``).

        The ``isinstance`` shape check is the only emptiness probe: the shapes
        an ``EMPTY_VALUES`` membership would skip (``None`` / ``""`` / ``()``)
        all take the shape check's skip arm, and no comparison runs against the
        value. Iterating an accepted ``list`` / ``tuple`` is the value's own
        behaviour, and whatever it raises propagates.
        """
        if not is_list_or_tuple(value):
            # Explicit empty / None / a non-sequence: keep django-filter's skip
            # (no bounds supplied).
            return qs
        bounds: list[object] = list(value)
        if len(bounds) != _RANGE_BOUNDS:
            return qs
        # ``BaseRangeField`` validates length == 2 before we run, and the generated
        # ``list[BigInt!]`` input carries non-null elements, so both bounds are present.
        start, end = bounds
        path = LOOKUP_SEP.join(
            part for part in (self.field_name, self.lookup_expr.rpartition(LOOKUP_SEP)[0]) if part
        )
        return _apply_lookups(self, qs, {f"{path}__gte": start, f"{path}__lte": end})


@dataclass(frozen=True)
class _GlobalIDTarget:
    """Where a GlobalID filter's node id is validated and compiled.

    ``definition`` is the type the id must name. ``row_path`` is the ORM path
    from the filter's model to that type's rows: the filter's ``field_name``
    minus a trailing scalar primary-key segment (``""`` for the owner's own id).
    ``slot`` is the type's id slot when its GlobalID carries an attribute other
    than the primary key (a consumer ``relay.NodeID[...]`` annotation), ``None``
    when it carries the primary key.
    """

    definition: DjangoTypeDefinition
    row_path: str
    slot: _OffPkIdSlot | None


class _OffPkIdSlot(NamedTuple):
    """A Relay type's id slot that is not its primary key (``relay.py::_node_id_slot``).

    ``field`` is the model field behind ``id_attr``, ``None`` when no model field
    holds it (an attribute the type's ``get_queryset`` annotates).
    """

    node_type: type[_RelayDjangoType]
    id_attr: str
    field: ModelField | None


def _off_pk_id_slot(definition: DjangoTypeDefinition) -> _OffPkIdSlot | None:
    """Return the id slot of a Relay ``definition`` whose GlobalID is not its primary key.

    ``None`` for a type whose id is its primary key (a type that is not a Relay
    node, one with no ``NodeID`` annotation, one whose ``NodeID`` names the key),
    the one predicate FK-id elision reads (``types/definition.py::_resolves_id_off_pk``),
    so every such filter keeps comparing the key.
    """
    origin = definition.origin
    if not implements_relay_node(origin):
        return None
    if not _resolves_id_off_pk(origin, definition.model._meta.pk.name):
        return None
    return _OffPkIdSlot(origin, *_node_id_slot(origin))


def _globalid_target(filter_instance: Filter) -> _GlobalIDTarget | None:
    """Resolve where a GlobalID-aware filter validates and compiles its node id.

    Reads the owner of the filter's runtime ``parent``: a filter set instance's
    class's own binding (``utils/permissions.py::set_bound_definition``, which
    the finalizer's phase 2.5 wires, spec-027 #"Bind the owner."), or the
    definition an undeclared hop's face carries, and resolves the LIVE
    ``field_name`` (a leaf ``_expand_related_filter`` rebased resolves its
    rebased path). Rows no definition answers for resolve from their model once
    the registry is stable (``registry.is_finalized()``): an unbound set instance (a
    ``RelatedFilter`` target no ``DjangoType`` wires, a subclass of a wired set
    included) from its model's registry primary (``registry.get``), the type its
    relation leaves are generated from, for the relation branch only (its own key
    keeps the upstream scalar shape, so it is never validated as that primary's
    GlobalID); an unbound set over a model no type exposes, and an undeclared hop's
    face into one, walk from that model (``_resolve_globalid_target``'s
    ``start_model``). Two routing branches:

    1. **Own-PK branch.** When ``filter_instance.field_name`` matches the
       owning model's PK name (``_meta.pk.name`` or ``"pk"``) and that PK is
       not itself a relation, the relevant definition is the owning
       ``DjangoType`` (the OWNER itself is the Relay node - its PK gets a
       GlobalID).
    2. **Relation branch.** Otherwise - including a PK that is a relation
       (``OneToOneField(primary_key=True)``, an MTI ``<parent>_ptr``) - the
       field name resolves through
       ``owner_definition.related_target_for(<base_field>)`` - where
       ``<base_field>`` is the parent-relation prefix in expanded child
       filter names like ``"genres__id"`` (Django ``__`` source paths per
       spec-027 #"rebuild ORM paths"); the relevant definition is the
       target ``DjangoType`` (spec-027
       #"the relation target (`owner_definition.related_target_for(field_name)`)").

    Returns the ``_GlobalIDTarget`` (definition, row path from the walk, and the
    off-pk id slot ``_off_pk_id_slot`` reads), resolved once per ``filter()``
    call and threaded through every element of a list. Returns ``None`` when
    nothing resolves a definition (no ``parent`` or no model, an unbound set
    before the registry is finalized), for an unbound set's own key, or when
    the lookup cannot resolve a target; the filter then decodes the GlobalID
    without type-name validation
    (the node-id-only fallback, spec-031 Decision 13; a relation's node id is still
    coerced through the column its path names, ``_unresolved_target_node_id``) and compiles on
    its own ``field_name``. The resolution of WHICH definition (own-PK vs relation)
    stays single-sited in ``_resolve_globalid_target`` so the strategy-aware
    acceptance check in ``_decode_and_validate_global_id`` consumes a single
    definition (spec-031 Decision 13).
    """
    parent: object = getattr(filter_instance, "parent", None)
    # An undeclared hop's face (``filters/sets.py::_UndeclaredHopSet``) carries the
    # definition its rows answer for on itself; a filter set instance answers for its
    # class's own binding.
    face = truth.instance_dict(parent) or {}
    relation_only = False
    if "_owner_definition" in face:
        owner = optional_instance(face["_owner_definition"], DjangoTypeDefinition)
    else:
        owner = set_bound_definition(truth.class_of(parent))
        relation_only = owner is None
    start_model: type[models.Model] | None = None
    if owner is None:
        # Rows no definition answers for (an unbound set, an undeclared hop into a model no
        # type exposes) still carry relation leaves generated from the registry primary of
        # their relation's model, so they validate from that primary once the registry is
        # stable; an unbound set's own key stays the upstream scalar shape, never a
        # GlobalID of its model's primary.
        meta = optional_instance(truth.static_attr(parent, "_meta", None), FilterSetOptions)
        model = getattr(meta, "model", None)
        if not registry.is_finalized() or not is_model_class(model):
            return None
        start_model = model
        if relation_only:
            owner = registry.get_definition(registry.get(model))
    field_name: str | None = getattr(filter_instance, "field_name", None)
    resolved = _resolve_globalid_target(owner, field_name, start_model=start_model)
    if resolved is None:
        return None
    definition, row_path = resolved
    if relation_only and not row_path:
        return None
    return _GlobalIDTarget(definition, row_path, _off_pk_id_slot(definition))


def resolve_globalid_target_definition(
    owner: DjangoTypeDefinition,
    field_name: str | None,
) -> DjangoTypeDefinition | None:
    """Resolve the target definition a GlobalID filter validates against, given its owner.

    The target definition ``_globalid_target`` resolves, read from an owner
    instead of a live filter's ``parent`` so the finalizer's build-time
    audit (``finalizer._audit_globalid_filter_strategies``) resolves the SAME
    target definition from a bound filterset's own binding
    (``utils/permissions.py::set_bound_definition``) + ``filter.field_name``
    that the runtime path resolves from a live filter instance - the
    own-PK-vs-relation decision stays single-sited here.

    A ``"pk"`` segment names the current model's primary key. A scalar primary
    key is the current definition's own Relay id, so it ends the path (owner
    itself when it is the whole path). A primary key that is itself a relation
    (``OneToOneField(primary_key=True)``, an MTI ``<parent>_ptr``) is walked like
    any other relation, so ``"pk"`` on such a model resolves to the definition
    the key points at, matching how ``FilterSet._is_own_pk_under_relay_owner``
    keeps a relation primary key out of the own-PK filter branch.

    Returns the owner itself for the own-PK branch, the terminal related target's
    definition for relation paths (including multi-hop relations like
    ``"shelf__branch__id"`` and paths through a relation primary key like
    ``"pk__card"``), or ``None`` when the path does not end on a registered
    target (a scalar segment before the end, an unknown field, a terminal model no
    ``DjangoType`` exposes). A hop whose model no type exposes does not end the
    walk: a relation leaf is generated from its own relation's model, whatever the
    hops before it expose. The audit calls this once every type is collected and
    its strategy stamped, before ``registry.is_finalized()`` flips, so the walk reads
    the registry as stable (``stable=True``) and resolves the target the request-time
    walk resolves once the registry is finalized.
    """
    resolved = _resolve_globalid_target(owner, field_name, stable=True)
    return None if resolved is None else resolved[0]


def _resolve_globalid_target(
    owner: DjangoTypeDefinition | None,
    field_name: str | None,
    *,
    start_model: type[models.Model] | None = None,
    stable: bool = False,
) -> tuple[DjangoTypeDefinition, str] | None:
    """Resolve ``field_name`` from ``owner`` to ``(target definition, row path)``.

    The walk behind ``resolve_globalid_target_definition`` and
    ``_globalid_target``: the row path is the prefix of ``field_name`` that
    reaches the target's rows, every segment before a terminal scalar primary
    key (``""`` for the owner's own id), or the whole path when it ends on a
    relation. It comes from the walk, never from trimming ``field_name``: a
    relation may be named like the target's primary key. A hop into a model no
    ``DjangoType`` exposes continues on that model, so the target is the terminal
    relation's ``registry.get`` exactly as generation types the leaf (a
    ``shelf__branch`` key with no ``Shelf`` type validates against ``Branch``'s);
    a primary key ending on such a model resolves nothing. With no ``owner`` the
    walk starts on ``start_model`` (rows no definition answers for). Continuing past a
    hop no definition resolves waits for a stable registry: ``stable`` (the
    finalizer's build-time audit, which runs once every type is collected and its
    strategy stamped, before ``registry.is_finalized()`` flips) or a finalized
    registry; before either the walk ends at that hop, so a filter set applied before
    finalization reads such a leaf node-id-only.
    """
    if not isinstance(field_name, str) or not field_name:
        return None

    current_def: DjangoTypeDefinition | None = owner
    current_model = owner.model if owner is not None else start_model
    if current_model is None:
        return None
    segments = field_name.split("__")

    for i, raw_segment in enumerate(segments):
        pk_field = read_attr(truth.static_attr(current_model, "_meta", None), "pk", None)
        pk_name = read_attr(pk_field, "name", None)
        segment = raw_segment
        if is_str(pk_name) and raw_segment == "pk":
            segment = pk_name

        # Only a scalar primary key is the definition's own Relay id; a relation
        # primary key (``OneToOneField(primary_key=True)``, an MTI ``<parent>_ptr``)
        # is a relation like any other and resolves to the definition it points at.
        if segment == pk_name and not getattr(pk_field, "is_relation", False):
            if i == len(segments) - 1 and current_def is not None:
                return current_def, "__".join(segments[:i])
            return None

        target = None if current_def is None else current_def.related_target_for(segment)
        if target is not None:
            current_def, _model_field = target
            current_model = current_def.model
            continue
        # A hop whose model no ``DjangoType`` exposes still leads on: generation types a
        # relation leaf from its own relation's model (``registry.get``), whatever the
        # hops before it expose, so the walk continues on the relation's model once the
        # registry is stable: ``stable`` from the finalizer's audit, which runs after every
        # type is collected, else ``registry.is_finalized()``, the signal
        # ``DjangoTypeDefinition.related_target_for`` caches on.
        if not (stable or registry.is_finalized()):
            return None
        field = get_model_field(current_model, segment)
        related_model = read_attr(field, "related_model", None)
        if not relation_bool(field, "is_relation") or not is_model_class(related_model):
            return None
        current_model = related_model
        current_def = registry.get_definition(registry.get(related_model))

    if current_def is None:
        return None
    return current_def, field_name


def _accepted_globalid_type_names(
    definition: DjangoTypeDefinition | None,
    schema: Schema | None = None,
) -> set[str] | None:
    """Return the accepted ``type_name`` payload(s) for a resolved definition's strategy.

    Strategy-aware target validation keyed on the resolved owner/target
    definition's recorded ``effective_globalid_strategy`` (spec-031 Decision 13) -
    the same field decode reads, so encode, decode, and filter validation all
    agree on one contract. The set is what a matching id of the target carries
    (the ``expected`` side of the mismatch error, and ``None`` when no guard
    applies); whether a received slot names the target is ``_slot_names_target``,
    which resolves a type-name slot the way decode does:

    - ``model`` -> the model label only (``definition.model._meta.label_lower``).
    - ``type`` -> the type name only: the name the executing ``schema`` published
      for the target (what a ``type``-strategy id of this schema carries, under
      whatever ``NameConverter`` it runs); the ``graphql_type_name`` - the default
      converter's spelling - when no schema is at hand (a filterset applied
      outside the request pipeline) or the schema publishes no object type for
      the target (no id of this schema can name it, so only its own spelling
      remains).
    - ``type+model`` -> either the model label or that type name.
    - ``definition is None`` (no owner, an unbound set's own key, or no target
      type) -> ``None``
      (node-id-only fallback; the ``type_name`` guard is skipped).

    ``_decode_and_validate_global_id`` calls this only after it has fail-closed
    on the encode-only (``callable`` / ``custom``) and lifecycle-defect
    (``effective_globalid_strategy is None`` on a known definition) cases, so a
    non-``None`` definition passed here always carries a framework strategy and
    always yields a non-empty accepted set. The ``accepted or None`` collapse is
    kept as a defensive belt only.
    """
    if definition is None:
        return None
    strategy = definition.effective_globalid_strategy
    accepted: set[str] = set()
    if strategy in MODEL_LABEL_STRATEGIES:
        accepted.add(definition.model._meta.label_lower)
    if strategy in TYPE_NAME_STRATEGIES:
        published = None if schema is None else published_node_type_name(schema, definition.origin)
        accepted.add(definition.graphql_type_name if published is None else published)
    return accepted or None


def _slot_names_target(
    definition: DjangoTypeDefinition,
    type_name: str,
    schema: Schema | None,
) -> bool:
    """Return whether a decoded ``type_name`` slot names the filter target ``definition``.

    One authority with decode: a model-label slot (a dot) names the target when
    its strategy emits model labels and the slot resolves to the target model through
    ``types/relay.py::model_for_label_slot`` - the reading decode runs, so the app
    label is exact and the model name case-insensitive; a
    type-name slot names it when the strategy decodes type names and the slot
    resolves to the target through ``types/relay.py::node_definition_for_published_name``
    - the same resolution ``node(id:)`` runs under the executing ``schema`` - so a
    slot this schema publishes for another type is refused even when it equals the
    target's own default spelling. With no schema at hand (a filterset applied
    outside the request pipeline) the target's ``graphql_type_name`` is the one
    accepted spelling.
    """
    strategy = definition.effective_globalid_strategy
    if "." in type_name:
        return (
            strategy in MODEL_LABEL_STRATEGIES
            and model_for_label_slot(type_name) is definition.model
        )
    if strategy not in TYPE_NAME_STRATEGIES:
        return False
    if schema is None:
        return type_name == definition.graphql_type_name
    try:
        return node_definition_for_published_name(schema, type_name) is definition
    except ConfigurationError:
        return False


def _filter_schema(filter_instance: Filter) -> Schema | None:
    """Return the Strawberry schema executing the request ``filter_instance`` filters for.

    Read off the owning ``FilterSet``'s ``_apply_info`` - the resolver ``info``
    ``apply_sync`` / ``apply_async`` stash on the top-level instance and
    ``_q_for_branch`` on every nested sibling - climbing from a relation leaf's
    child instance (``FilterSet._projection_child``) to the instance that owns
    it, so the GlobalID type-name check validates against the names THIS schema
    published. ``None`` for a filterset built outside the apply pipeline (a
    direct unit-test construction), where no schema exists to consult.
    """
    owner = read_attr(filter_instance, "parent", None)
    while owner is not None:
        info = read_attr(owner, "_apply_info", None)
        if info is not None:
            return strawberry_schema_from_info(info)
        owner = read_attr(owner, "_projection_owner", None)
    return None


def _global_id_from_filter_text(value: object) -> relay.GlobalID:
    """Decode a GlobalID filter string, raising ``ValueError`` for any malformed value."""
    # Strawberry's own decode reads the value as ``str`` and raises ``ValueError`` for
    # anything else, so a non-string takes the same malformed-payload route.
    if not isinstance(value, str):
        raise ValueError("a GlobalID filter value is a base64 string")  # noqa: TRY004
    return relay.GlobalID.from_id(value)


def _decode_and_validate_global_id(
    value: object,
    filter_instance: Filter,
    *,
    index: int | None = None,
    target: _GlobalIDTarget | None = None,
    alias: str,
) -> object:
    """Decode `value` to a node id and validate its type and target id per strategy.

    Accepts both raw `str` and `strawberry.relay.GlobalID` objects per
    spec-027 #"Accepts both raw". The accepted `type_name` payload(s) are
    strategy-aware (spec-031 Decision 13): under the resolved owner/target
    definition's recorded `effective_globalid_strategy`, an emitted model-label
    ID round-trips while the bare GraphQL type name is rejected (and vice
    versa for the `type` strategy). Raises `GraphQLError("GlobalID type
    mismatch: filter expects <expected> but received <actual>")` when the
    decoded `type_name` does not name the target for the three framework
    strategies (spec-027 #"filter expects <expected> but received <actual>",
    strategy-aware, spec-031 Decision 13): `_slot_names_target` resolves a
    type-name slot through the executing schema's published names exactly as
    decode does, and `<expected>` is `_accepted_globalid_type_names`. A received
    slot equal to an expected spelling that this schema publishes for another type
    reads `... but received <actual>, which this schema publishes for another type`. No resolvable
    target (`definition is None`, ``_globalid_target``) skips the `type_name` guard (the
    node-id-only fallback, coerced below when the filter names a model field). A
    target on a `callable` / `custom` (encode-only) strategy, or a known target whose
    `effective_globalid_strategy` is `None` (an unfinalized / non-Relay
    lifecycle defect), is a fail-closed reject with a coded
    `GraphQLError(..., extensions={"code": "GLOBALID_UNVALIDATABLE"})` - the
    runtime backstop behind the build-time audit
    (`finalizer._audit_globalid_filter_strategies`) for hand-built filtersets
    constructed outside finalization. A malformed wire string (unparseable
    base64 / not a
    `type_name:node_id` payload) raises `GraphQLError(..., extensions={"code":
    "GLOBALID_INVALID"})` - the uniform coded error the node-refetch path emits
    (`relay.py::_decode_or_graphql_error`) - instead of leaking Strawberry's raw
    `GlobalIDValueError`. A well-formed GlobalID whose id part is empty (e.g.
    `to_base64("BookNode", "")`) decodes to an empty `node_id` and passes decode +
    strategy + `type_name` validation, but an empty identifier is not a valid
    resource id: it too raises `GraphQLError(..., extensions={"code":
    "GLOBALID_INVALID"})` (with the list index when present). Treating an empty
    decoded id as a filter value would silently widen a restrictive predicate (a
    scalar no-op, or a dropped list element turning `{in: ["type:"]}` into an
    unfiltered query), so an empty decoded id is a rejected input of the same
    class as a malformed payload / wrong type. Only a `None` value (omission,
    handled by the callers) and an explicit `[]` (match-none, handled by
    `GlobalIDMultipleChoiceFilter`) remain non-error paths.
    `GlobalIDMultipleChoiceFilter` passes `index` so the rejected list element is
    named in the mismatch, malformed, and empty-id messages per spec-027
    #"validates every element of the list independently". The resolved target's
    id slot owns the final coercion, the field the node field coerces against
    (``relay.py::_coerce_pk_or_none``): its ``models.Field`` primary key, or the
    column a consumer ``relay.NodeID[...]`` annotation names. An ID with a
    correctly typed wire payload but an invalid integer / UUID / range / text
    value is rejected as ``GLOBALID_INVALID`` before Django can raise while
    compiling the queryset; a valid value no row carries matches nothing. The bind
    and the column's storage domain are the filtered queryset's database ``alias``'s,
    and the column's own validators are not run, so an id they would refuse still matches
    a row that holds it.
    A filter with no resolvable target (no owner, an unbound set's own key, or a path
    into a model no ``DjangoType`` resolves) skips the ``type_name`` guard; when its path names a model
    field and its ``lookup_expr`` is a lookup that field registers, the node id is still
    coerced through the column the predicate compares (``_unresolved_target_node_id``,
    over ``_compared_columns``: a scalar column itself, the target's primary key or the
    link's column for a relation), so an id that column cannot hold, and every id for a
    relation linked by more than one column, answers ``GLOBALID_INVALID``. A filter
    whose path names no model field (no FilterSet model, no field on it), or whose
    ``lookup_expr`` continues the path or applies a transform, passes the decoded node
    id through. ``target``
    threads the filter's ``_globalid_target`` through a list so it resolves once per
    call; when omitted it is resolved here.
    """
    if isinstance(value, relay.GlobalID):
        decoded = value
    else:
        try:
            decoded = _global_id_from_filter_text(value)
        except ValueError as exc:
            # Malformed payload: ``ValueError`` is the superset
            # ``types/relay.py::decode_global_id`` catches too.
            suffix = "" if index is None else f" at index {index}"
            raise GraphQLError(
                f"Invalid GlobalID: {truth.render(value)} is not a valid GlobalID (malformed "
                f"base64 or not a 'type_name:node_id' shape){suffix}.",
                extensions=coded_error_extensions(GLOBALID_INVALID_ERROR_CODE),
            ) from exc
    if target is None:
        target = _globalid_target(filter_instance)
    definition = None if target is None else target.definition
    if definition is not None:
        strategy = definition.effective_globalid_strategy
        if strategy not in FRAMEWORK_GLOBALID_STRATEGIES:
            # Fail closed: an encode-only or unfinalized target.
            suffix = "" if index is None else f" at index {index}"
            if strategy in ENCODE_ONLY_GLOBALID_STRATEGIES:
                message = (
                    f"GlobalID for a {strategy}-strategy type "
                    f"({definition.graphql_type_name}) cannot be validated on a filter "
                    f"input; these strategies are encode-only{suffix}."
                )
            else:
                message = (
                    f"GlobalID filter target {definition.graphql_type_name} has no "
                    f"recorded globalid strategy; the type was not finalized as a Relay "
                    f"node, so its filter input cannot validate a GlobalID{suffix}."
                )
            raise GraphQLError(
                message,
                extensions=coded_error_extensions(GLOBALID_UNVALIDATABLE_ERROR_CODE),
            )
    if (
        target is not None
        and target.slot is not None
        and target.slot.field is None
        and target.row_path
    ):
        # A ``relay.NodeID`` over an attribute no model column holds (an annotation the
        # type's ``get_queryset`` adds) is comparable only on that type's own rows.
        suffix = "" if index is None else f" at index {index}"
        raise GraphQLError(
            f"GlobalID filter target {target.definition.graphql_type_name} carries its id in "
            f"{target.slot.id_attr!r}, which no model column holds, so a filter across a "
            f"relation cannot compare it{suffix}.",
            extensions=coded_error_extensions(GLOBALID_UNVALIDATABLE_ERROR_CODE),
        )
    schema = _filter_schema(filter_instance)
    accepted = _accepted_globalid_type_names(definition, schema)
    if (
        accepted is not None
        and definition is not None
        and not _slot_names_target(definition, decoded.type_name, schema)
    ):
        suffix = "" if index is None else f" at index {index}"
        expected = " or ".join(sorted(accepted))
        # An accepted spelling refused anyway names a different type in this schema.
        shadowed = (
            ", which this schema publishes for another type"
            if decoded.type_name in accepted
            else ""
        )
        raise GraphQLError(
            "GlobalID type mismatch: filter expects "
            f"{expected} but received {decoded.type_name}{shadowed}{suffix}",
        )
    if decoded.node_id in EMPTY_VALUES:
        # Empty node id: accepting it would widen a restrictive filter.
        suffix = "" if index is None else f" at index {index}"
        raise GraphQLError(
            f"Invalid GlobalID: {truth.render(value)} decodes to an empty node id, which is not a "
            f"valid resource identifier{suffix}.",
            extensions=coded_error_extensions(GLOBALID_INVALID_ERROR_CODE),
        )
    target_model = getattr(definition, "model", None) if definition is not None else None
    if target is not None and target.slot is not None:
        # A consumer ``relay.NodeID[...]`` slot: the node id is that column's value.
        slot = target.slot
        coerced_slot_value = _coerce_pk_or_none(
            slot.node_type,
            decoded.node_id,
            slot=(slot.id_attr, slot.field),
            alias=alias,
        )
        if coerced_slot_value is None:
            suffix = "" if index is None else f" at index {index}"
            raise GraphQLError(
                f"Invalid GlobalID: {truth.render(value)} carries a node id that is not a valid "
                f"{truth.kind(target_model)} id value{suffix}.",
                extensions=coded_error_extensions(GLOBALID_INVALID_ERROR_CODE),
            )
        return coerced_slot_value
    target_pk = getattr(truth.static_attr(target_model, "_meta", None), "pk", None)
    if isinstance(target_pk, models.Field):
        coerced_node_id = coerce_field_value_or_none(target_pk, decoded.node_id, alias=alias)
        if coerced_node_id is None:
            suffix = "" if index is None else f" at index {index}"
            raise GraphQLError(
                f"Invalid GlobalID: {truth.render(value)} carries a node id that is not a valid "
                f"{truth.kind(target_model)} primary-key value{suffix}.",
                extensions=coded_error_extensions(GLOBALID_INVALID_ERROR_CODE),
            )
        return coerced_node_id
    if target is None:
        field = _bound_model_field(filter_instance)
        if field is not None:
            return _unresolved_target_node_id(
                value,
                decoded.node_id,
                filter_instance,
                field,
                index=index,
                alias=alias,
            )
    return decoded.node_id


def _unresolved_target_node_id(
    value: object,
    node_id: str,
    filter_instance: Filter,
    field: ModelField,
    *,
    index: int | None,
    alias: str,
) -> object:
    """Coerce a node id a filter with no resolvable target type compares on ``field``.

    A GlobalID filter whose path no ``DjangoType`` resolves (no owner, an unbound set's
    own key, or a consumer-declared ``GlobalIDFilter(field_name="<relation>")`` /
    ``GlobalIDFilter(field_name="<relation>__id")`` into an unregistered model) has no
    type to validate the ``type_name`` against, but its predicate still compares the
    node id on the columns ``_compared_columns`` reads off that field: the field itself
    for a scalar column, the target's primary key for an ordinary relation, the link's
    column for a ``ForeignObject`` off the pk or a many-to-many through a ``to_field``.
    One column: the node id is coerced through it with ``coerce_field_value_or_none``,
    the coercion the resolved path runs on its target's primary key, so an id that
    column cannot hold answers ``GLOBALID_INVALID`` instead of the raw ``ValueError``
    Django raises compiling the queryset. More than one (a multi-column link, a
    composite primary key): no single node id can name a row, so every id answers
    ``GLOBALID_INVALID`` too. A ``lookup_expr`` that is no lookup ``field`` registers
    (one continuing the path, ``lookup_expr="code"``, or applying a transform) compares
    another column, and a relation into a model that is not resolved has none; both pass
    the node id through unchanged.
    """
    if field.get_lookup(filter_instance.lookup_expr) is None:
        return node_id
    columns = _compared_columns(filter_instance, field)
    if columns is None:
        return node_id
    suffix = "" if index is None else f" at index {index}"
    if len(columns) != 1:
        raise GraphQLError(
            f"Invalid GlobalID: {truth.render(value)} carries a node id, but "
            f"{truth.kind(columns[0].model)} is linked by {len(columns)} columns no single "
            f"node id can name{suffix}.",
            extensions=coded_error_extensions(GLOBALID_INVALID_ERROR_CODE),
        )
    column = columns[0]
    coerced = coerce_field_value_or_none(column, node_id, alias=alias)
    if coerced is None:
        raise GraphQLError(
            f"Invalid GlobalID: {truth.render(value)} carries a node id that is not a valid "
            f"{truth.kind(column.model)} key value{suffix}.",
            extensions=coded_error_extensions(GLOBALID_INVALID_ERROR_CODE),
        )
    return coerced


def _globalid_predicate_path(
    filter_instance: Filter,
    target: _GlobalIDTarget | None,
) -> str | None:
    """Return the ORM path a decoded node id compiles on, ``None`` for the filter's own.

    A target whose id slot is not its primary key compares that slot on the
    target rows, ``<row path>__<id_attr>`` (the bare ``id_attr`` for the owner's
    own id), the predicate the node field filters ``{id_attr: node_id}`` by; the
    slot names the target column itself, so a forward relation's stored link
    (a non-pk ``to_field`` included) is joined through, never compared. Every
    other target keeps ``_marked_pk_field_name``: ``<relation>__pk`` for a
    forward relation linked off the target's primary key, else ``None``.
    """
    if target is not None and target.slot is not None:
        id_attr = target.slot.id_attr
        return f"{target.row_path}__{id_attr}" if target.row_path else id_attr
    return _marked_pk_field_name(filter_instance)


class GlobalIDFilter(Filter):
    """Filter that decodes a Relay GlobalID before delegating to `Filter`.

    Same contract as `graphene_django/filter/filters/global_id_filter.py::GlobalIDFilter`
    with the decode substituted to `strawberry.relay.GlobalID.from_id(value)`
    per spec-027 Decision 4. The Graphene-only
    `GlobalIDFormField` / `GlobalIDMultipleChoiceField` dependencies drop
    away; the default `forms.CharField` (inherited via `Filter.field_class`)
    is used.

    Accepts both raw `str` and `strawberry.relay.GlobalID` objects per
    spec-027 #"Accepts both raw". Validates the decoded `type_name` against
    the strategy-aware accepted set (resolved through the parent filterset's
    bound owner's `related_target_for(field_name)`, or the owner
    itself when the filter targets the own PK) per spec-031 Decision 13; a
    mismatch raises `GraphQLError("GlobalID type mismatch...")` before
    any queryset clause runs. The decoded node id is the value of the target
    type's id slot, its primary key or the column a consumer `relay.NodeID[...]`
    names, and is coerced and compared as that column, as `node(id:)` reads it.
    """

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Decode + validate the GlobalID; delegate to `Filter.filter` with `node_id`.

        A ``None`` value is omission and short-circuits to the unfiltered queryset.
        Every other value is decoded and validated by
        ``_decode_and_validate_global_id``, which rejects a malformed payload, a
        wrong ``type_name``, AND a well-typed empty-id GlobalID (an empty decoded
        ``node_id`` is ``GLOBALID_INVALID``, not a silent no-op), so ``node_id`` is
        guaranteed present and valid below.

        The target resolves once (``_globalid_target``) and the predicate path comes
        from ``_globalid_predicate_path``, DERIVED from the LIVE ``field_name`` at
        filter time so it stays correct after ``_expand_related_filter`` rebases the
        leaf. A target whose id is a consumer ``relay.NodeID[...]`` column compiles
        on that column of the target rows (``<row path>__<id_attr>``). A forward
        relation bound on a non-pk ``to_field`` (flagged at generation via the
        boolean ``_GLOBALID_RELATION_PK_ATTR``) into a target whose id is its
        primary key compiles on ``f"{self.field_name}__pk"``, so the decoded key
        never compares the raw FK-stored ``to_field`` column. Every other case
        delegates to ``Filter.filter`` with the unchanged
        ``{field_name__lookup_expr: node_id}`` predicate.
        """
        if value is None:
            return super().filter(qs, None)
        target = _globalid_target(self)
        node_id = _decode_and_validate_global_id(value, self, target=target, alias=qs.db)
        path = _globalid_predicate_path(self, target)
        if path is not None:
            return _apply_lookup_predicate(self, qs, node_id, field_name=path)
        return super().filter(qs, node_id)


class _AbsentGlobalIDMultipleChoiceWidget(SelectMultiple):
    """Preserve an absent membership key as ``None`` rather than ``[]``.

    ``SelectMultiple`` reads a ``QueryDict`` through ``getlist()``, which returns
    ``[]`` for both an absent key and a present empty key. Those values have different
    filter semantics here: omission skips the filter, while ``{in: []}`` matches no
    rows. Key presence retains that distinction across plain dictionaries and
    ``QueryDict`` instances.
    """

    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: MultiValueDict[str, _UploadedFileAny],
        name: str,
    ) -> object:
        """Return ``None`` for an absent key; defer to ``SelectMultiple`` otherwise."""
        if name not in data:
            return None
        return object_result(super().value_from_datadict, data, files, name)


@final
class _GlobalIDMultipleChoiceField(MultipleChoiceField):
    """`MultipleChoiceField` that skips fixed-`choices` validation.

    `MultipleChoiceField.valid_value` rejects any submitted value that
    is not in `self.choices` -- and a `GlobalIDMultipleChoiceFilter`
    has no static choice set (its `choices` default to `[]`), so the
    stock field rejected EVERY GlobalID at form-clean time before the
    filter's own decode/validate could run. GlobalID list elements are
    decoded and type-checked in `GlobalIDMultipleChoiceFilter.filter`
    (per spec-027 #"validates every element of the list independently"), not against a
    fixed set, so this field accepts any submitted value and defers
    validation to the filter. Same contract as
    ``graphene_django/forms/forms.py::GlobalIDMultipleChoiceField`` minus its
    per-value GlobalID check.

    The custom widget and field overrides preserve ``None`` for an omitted key:
    ``SelectMultiple`` otherwise maps an absent ``QueryDict`` key to ``[]``, and
    ``MultipleChoiceField.to_python`` maps a widget-provided ``None`` to ``[]``.
    An explicit empty list remains ``[]`` and therefore keeps its match-nothing
    membership semantics.
    """

    widget = _AbsentGlobalIDMultipleChoiceWidget

    @override
    def valid_value(self, value: object) -> bool:
        """Accept any value; GlobalID validation happens in the filter."""
        return True

    # basedpyright: upstream's list-only return cannot express the preserved omission; it rejects
    # the ``None`` arm against the ``list[str]`` return
    @override
    def to_python(self, value: object) -> list[str] | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Preserve omission without bypassing ``Field.clean`` validation."""
        if value is None:
            return None
        return super().to_python(value)

    @override
    def validate(self, value: object) -> None:
        """Validate omitted values through ``Field`` and lists through the parent."""
        if value is None:
            Field.validate(self, value)
            return
        super().validate(value)


class GlobalIDMultipleChoiceFilter(MultipleChoiceFilter):
    """Multi-value sibling of `GlobalIDFilter`.

    Validates every list element independently per spec-027
    #"validates every element of the list independently"; a single wrong-type element
    rejects the whole input with the offending index named in the error
    message.

    Uses `_GlobalIDMultipleChoiceField` so the form-clean step does not
    reject submitted GlobalIDs against an empty `choices` set (the stock
    `MultipleChoiceField` would); decode + type validation run in
    `filter` instead.

    An explicit empty list is a real membership predicate for every list-shaped
    lookup (``in``, many-side ``exact``, etc.): it matches no rows (or every row
    when ``exclude=True``), matching ``ListFilter``'s empty-set semantics rather
    than upstream ``MultipleChoiceFilter``'s ``if not value: return qs`` skip.
    Omission (``None``, preserved by ``_GlobalIDMultipleChoiceField``) remains
    the no-constraint path.
    """

    field_class: type[_GlobalIDMultipleChoiceField] = _GlobalIDMultipleChoiceField

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Decode + validate every GlobalID; apply the lookup-shaped predicate.

        A ``None`` value is omission and short-circuits to the unfiltered
        queryset; an explicit ``[]`` is the match-none membership predicate
        (``ListFilter`` empty-set semantics for every list-shaped lookup, not
        upstream ``MultipleChoiceFilter``'s ``if not value: return qs`` skip).
        A container that is not a ``list`` / ``tuple`` is refused before the
        emptiness probe, under the ``GLOBALID_INVALID`` code a malformed member
        gets. All three run BEFORE decode. Every remaining element is decoded
        and validated by ``_decode_and_validate_global_id``, which rejects a
        malformed payload, a wrong ``type_name``, AND a well-typed empty-id
        GlobalID (an empty decoded id is ``GLOBALID_INVALID`` with its list
        index named), so no vacuous element can silently reduce the membership
        list.

        The ``in`` lookup consumes the WHOLE decoded list in one predicate.
        Upstream ``MultipleChoiceFilter.filter`` instead ORs one predicate
        PER element, which for ``lookup_expr="in"`` produced
        ``pk__in="26"`` - Django iterates the STRING and the clause
        explodes to ``IN ('2','6')``. That was correct by accident for
        single-digit pks, which is all a fresh-per-test SQLite database
        ever produces; the first Postgres run surfaced it the moment a
        sequence (which never rewinds across rolled-back tests) passed 9.
        Non-``in`` lookups (per-element semantics, e.g. a multi-valued
        relation's ``exact``) keep the upstream OR delegation for non-empty
        lists only, on a copy carrying the predicate path when the target's id
        is not its primary key.
        """
        if value is None:
            return super().filter(qs, None)
        value = _materialize_list_shaped_values(
            value,
            message="Invalid GlobalID list: expected a list of GlobalIDs.",
            code=GLOBALID_INVALID_ERROR_CODE,
        )
        if len(value) == 0:
            return _match_none_queryset(self, qs)
        target = _globalid_target(self)
        node_ids = [
            _decode_and_validate_global_id(item, self, index=idx, target=target, alias=qs.db)
            for idx, item in enumerate(value)
        ]
        path = _globalid_predicate_path(self, target)
        if self.lookup_expr != "in":
            if path is None:
                return super().filter(qs, node_ids)
            # Upstream's per-element predicates read ``field_name``; a copy carries the path.
            rebound = copy.copy(self)
            rebound.field_name = path
            return super(GlobalIDMultipleChoiceFilter, rebound).filter(qs, node_ids)
        # ``_globalid_predicate_path`` DERIVES the path from the LIVE ``field_name``
        # (immune to ``_expand_related_filter`` rebasing): the target's id column for a
        # consumer ``relay.NodeID[...]`` target, the pk-qualified relation path
        # ``f"{self.field_name}__pk"`` for a non-pk-``to_field`` relation into a
        # pk-id target; every other target passes ``None``, leaving the predicate
        # byte-identical to the raw ``{field_name__in: node_ids}`` form. Framework
        # generation stamps the marker on this filter for a many-to-many whose through
        # foreign key onto the target has a non-pk ``to_field``, and for a forward,
        # single-valued FK bound on a non-pk ``to_field`` whose ``in`` lookup is
        # list-shaped: ``filter_for_field`` selects ``GlobalIDMultipleChoiceFilter`` for
        # such an ``in`` and applies the marker, so the path is honored identically to
        # ``GlobalIDFilter``'s single-value ``in`` (shared derivation, one home).
        return _apply_lookup_predicate(self, qs, node_ids, field_name=path)


def relation_identity_column(relation: object) -> ConcreteField | None:
    """Return the concrete column that types and coerces a relation leaf's raw identity.

    A relation key in ``Meta.fields`` whose target is not a Relay node filters by the
    related row's primary key. The GraphQL input scalar and the value coercion both read
    that key's column: ``relation.related_model._meta.pk``, followed through any
    relation-valued primary key (a multi-table-inheritance child's parent link, a
    one-to-one used as the key) down to the column that actually stores the value.
    ``None`` for a non-relation, or a relation whose target is not a resolved model.
    """
    if not getattr(relation, "is_relation", False):
        return None
    return _model_identity_column(getattr(relation, "related_model", None), None)


def _model_identity_column(model: object, to_field_name: str | None) -> ConcreteField | None:
    """Return the concrete column holding ``model``'s primary key, or its ``to_field_name``.

    A relation-valued column (a multi-table-inheritance parent link, a one-to-one used
    as the key, a foreign key named as ``to_field_name``) is followed to the column that
    actually stores the value. ``None`` when ``model`` is not a resolved model.
    """
    meta: object = getattr(model, "_meta", None)
    if not isinstance(meta, Options):
        return None
    column = stored_value_column(meta.get_field(to_field_name) if to_field_name else meta.pk)
    return column if isinstance(column, models.Field) else None


def model_choice_identity_column(
    filter_instance: Filter,
    relation: object,
) -> ConcreteField | None:
    """Return the column a consumer ``ModelChoiceFilter`` family filter's form field cleans.

    A ``ModelChoiceFilter`` / ``ModelMultipleChoiceFilter`` the consumer declares (or
    selects through ``Meta.filter_overrides``) keeps django-filter's model-choice form
    field, which looks each value up in the filter's ``queryset`` by ``to_field_name``
    (the primary key when unset). The value's column is that field of the queryset's
    model. A callable ``queryset`` (``queryset=lambda request: ...``) has no model until
    a request arrives, so the model is the target of ``relation``, the field the
    filter's ``field_name`` names on its FilterSet model. ``None`` when neither source
    names a model.
    """
    queryset = getattr(filter_instance, "queryset", None)
    model = None if callable(queryset) else getattr(queryset, "model", None)
    if model is None and getattr(relation, "is_relation", False):
        model = getattr(relation, "related_model", None)
    return _model_identity_column(model, filter_instance.extra.get("to_field_name"))


def _compared_columns(
    filter_instance: Filter,
    field: ModelField | None,
) -> tuple[ConcreteField, ...] | None:
    """Return the columns a raw identity compared on ``field`` meets, each the column it stores.

    ``field`` is what ``filter_instance``'s ORM path names (``_bound_model_field``). A
    key column compares the value it stores, so its identity is the column that value
    lives in (``stored_value_column``): a plain column, or a forward ``ForeignKey`` /
    ``OneToOneField`` followed through each link to the column it references (its
    ``to_field`` included). That covers a single-valued key leaf compared through its
    own key and the target key column a to-many key leaf walking a visibility hop names
    on the hop's target rows (``filters/sets.py::FilterSet._leaf_chain``), a
    relation-valued primary key such as a one-to-one onto a non-pk ``to_field``
    included; an unmarked forward key into an unresolved target raises the
    ``ValueError`` Django's own query raises for it.

    A forward relation carrying the ``_GLOBALID_RELATION_PK_ATTR`` marker compiles
    against ``<relation>__pk`` and meets the target's primary-key fields. Every other
    relation compared as a relation (a ``ForeignObject``, a reverse relation, a
    many-to-many) meets the target fields of the last join Django builds for it
    (``path_infos[-1].target_fields``, Django's own answer): the target's primary
    key for a reverse relation and an ordinary link, the link's column for a
    ``ForeignObject`` off the pk and for a many-to-many whose through foreign key onto
    the target has a ``to_field``, and every carrier's target for a multi-column link.
    ``None`` for a path naming no field and for a relation whose target is not a
    resolved model.
    """
    if field is None:
        return None
    marked = bool(getattr(filter_instance, _GLOBALID_RELATION_PK_ATTR, False))
    if isinstance(field, models.ForeignKey) or not field.is_relation:
        if field.is_relation and marked:
            column = relation_identity_column(field)
            return None if column is None else (column,)
        column = stored_value_column(field)
        return (column,) if isinstance(column, models.Field) else None
    related = getattr(field, "related_model", None)
    if not is_model_class(related) or not isinstance(
        field,
        (models.ForeignObject, models.ManyToManyField, models.ForeignObjectRel),
    ):
        return None
    targets = related._meta.pk_fields if marked else field.path_infos[-1].target_fields
    return tuple(stored_value_column(target) for target in targets)


def _coerce_relation_identity(filter_instance: Filter, value: object, alias: str) -> object:
    """Coerce one raw identity value through the target key column; ``None`` if it names no row.

    The column is the one ``_compared_columns`` reads off the filter's ORM path, so a
    key leaf compared through its relation and one compared on the target's key column
    across a visibility hop coerce alike. A value the column cannot hold (one the
    queryset's database ``alias`` cannot bind, out of the column's range there, wrong
    shape) identifies no row, the same verdict ``_identifying_members`` gives an integer
    ``in`` member; the column's own validators are not run, so a key they would refuse
    still matches a row that holds it. A relation linked by more than one column
    (``_compared_columns``) has no single column one value can name, so every value
    identifies no row. A filter whose path names no field (``_bound_model_field``: no
    model to walk, or nothing on it) has no column and passes the value through
    unchanged.
    """
    columns = _compared_columns(filter_instance, _bound_model_field(filter_instance))
    if columns is None:
        return value
    if len(columns) != 1:
        return None
    return coerce_field_value_or_none(columns[0], value, alias=alias)


@final
class _RelationIdentityListField(Field):
    """Form field for a list of raw relation identities: no choice set, no existence check.

    django-filter's ``ModelMultipleChoiceField`` validates every member against the target
    model's default manager, which answers "Select a valid choice" for a key that exists
    nowhere and an empty match for one the target's ``get_queryset`` hides: an existence
    oracle for hidden rows. This field only preserves the list; coercion happens in
    ``RelationPkMultipleFilter.filter``, where a key that names no row simply matches
    nothing, exactly as a GlobalID relation leaf treats it. Omission stays ``None`` (the
    widget keeps an absent key distinct from ``[]``).
    """

    widget = _AbsentGlobalIDMultipleChoiceWidget

    @override
    def to_python(self, value: object) -> list[object] | None:
        """Return ``None`` for omission and a list for a list or tuple; reject anything else.

        The rejection reuses ``MultipleChoiceField``'s ``invalid_list`` code, so a form
        error reads the same as it does for django-filter's list-valued fields.
        """
        if value is None:
            return None
        if not is_list_or_tuple(value):
            raise ValidationError("Enter a list of values.", code="invalid_list")
        return list(value)


class RelationPkFilter(Filter):
    """Single raw-primary-key filter for a relation leaf whose target is not a Relay node.

    The non-Relay sibling of ``GlobalIDFilter``: ``FilterSet.filter_for_lookup`` selects
    it for ``exact`` on a single-valued relation (forward FK, one-to-one) when the target
    type is not a Relay node or no ``DjangoType`` exposes the target model. The input is
    typed from the column its predicate compares (``_compared_columns``): the target's
    primary key for a generated leaf, the link's column for a declared unmarked one. The
    form field is django-filter's plain ``Field``, never a ``ModelChoiceField``, so a key
    for a missing row and one ``get_queryset`` hides are indistinguishable: both reach the
    predicate and match by value.
    """

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Coerce the key through the target column and apply one relation predicate.

        ``None`` is omission. A key the column cannot hold identifies no row and matches
        nothing (every row under ``exclude``), never django-filter's empty-value skip. A
        forward relation bound on a non-pk ``to_field`` carries the
        ``_GLOBALID_RELATION_PK_ATTR`` marker and compiles against ``<relation>__pk``,
        so the value is always the target's primary key.
        """
        if value is None:
            return qs
        coerced = _coerce_relation_identity(self, value, qs.db)
        if coerced is None:
            return _match_none_queryset(self, qs)
        return _apply_lookup_predicate(self, qs, coerced, field_name=_marked_pk_field_name(self))


class RelationPkMultipleFilter(Filter):
    """List-valued raw-primary-key sibling of ``RelationPkFilter``.

    Selected for ``in`` on any relation and for ``exact`` on a multi-valued one (reverse
    FK, forward or reverse M2M) when the target is not a Relay node. The README membership
    rules hold: every member is coerced through the target key column and a member that
    names no row is dropped, an all-dropped list matches no rows, and an explicit ``[]``
    matches nothing. Omission (``None``) is the no-constraint path.
    """

    field_class: type[_RelationIdentityListField] = _RelationIdentityListField

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Coerce every member and apply ONE ``<relation>__in`` predicate over the survivors.

        ``exact`` on a multi-valued relation and ``in`` on any relation both mean "related
        to at least one of these rows", which a single ``__in`` over one join expresses
        for both (and for its ``exclude`` complement). The non-pk ``to_field`` marker
        qualifies the path with ``__pk`` exactly as on ``RelationPkFilter``.
        """
        if value is None:
            return qs
        members = _materialize_list_shaped_values(
            value,
            message="Invalid filter value: expected a list of primary keys.",
            code=FILTER_INVALID_ERROR_CODE,
        )
        kept = [
            coerced
            for coerced in (_coerce_relation_identity(self, member, qs.db) for member in members)
            if coerced is not None
        ]
        if not kept:
            return _match_none_queryset(self, qs)
        field_name = _marked_pk_field_name(self) or self.field_name
        return _apply_lookups(self, qs, {f"{field_name}__in": kept})


def _filter_set_class() -> type[FilterSet]:
    """Return the ``FilterSet`` family base for the target-type gate.

    Deferred so the ``filters.sets -> filters.base`` module-load edge stays
    one-directional: ``filters.sets`` imports this module at module scope
    (the ``FilterSet`` base needs ``RelatedFilter``), so a module-level import
    back would re-enter a partially-initialized ``filters.sets`` at import
    time -- the same cycle-keeping contract as
    ``orders/base.py::_order_set_class``.
    """
    from .sets import FilterSet  # noqa: PLC0415 - import cycle

    return FilterSet


class RelatedFilter(RelatedSetTargetMixin["FilterSet"], ModelChoiceFilter):
    """`ModelChoiceFilter` that traverses into another `FilterSet`.

    Collapsed port of `django_graphene_filters/filters.py::BaseRelatedFilter`
    + `django_graphene_filters/filters.py::RelatedFilter` into a single
    consumer-facing class per spec-027 Decision 2 (single-symbol public
    surface). The lazy-resolution logic (`bind_filterset`, `.filterset`
    property, target-model-derived queryset) carries over from the
    cookbook unchanged.

    Target acceptance shapes:

    - A `FilterSet` class.
    - An absolute import path (e.g. ``"apps.library.filters.ShelfFilter"``).
    - An unqualified class name resolved against the owning filterset's
      module (e.g. ``"ShelfFilter"`` when both filtersets live in the
      same file).
    - ``None`` -- the placeholder form (the branch is skipped at input
      emission and BFS enqueue).

    A target that RESOLVES to anything else -- an ``OrderSet`` (the
    cross-family twin), a plain class, or a factory returning a non-class
    -- raises ``ConfigurationError`` at the ``.filterset`` read. Without the
    gate the mis-wiring survives declaration, binding, and expansion and
    first detonates inside a consumer (``_expand_related_filter`` calling
    ``target._filters_along(path, scope)``, or the BFS builder's ``target.type_name_for()``)
    as a raw ``AttributeError``, or -- for an OrderSet-shaped target --
    silently walks the ORDER family's fields through the filter input
    builder.
    """

    # ``RelatedSetTargetMixin`` parameterization: the slots the shared
    # owner-bind / lazy-target machinery reads. The order
    # twin uses ``("_orderset", "bound_orderset")``.
    _target_attr: str = "_filterset"
    _owner_attr: str = "bound_filterset"
    # The owning set the bind records under ``_owner_attr``. Annotation only: the slot stays
    # absent until the bind, which is how ``_bind_owner`` tells a first bind from a re-bind.
    bound_filterset: type[FilterSet]

    def __init__(
        self,
        filterset: _FilterSetTarget,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Bind the target `filterset` and record explicit-queryset intent.

        Rejects `lookups=` with `TypeError` before delegating to
        `ModelChoiceFilter.__init__`: the lookups a related branch exposes
        are the target filter set's own (its `Meta.fields` and declared
        filters), so nothing reads the kwarg. The explicit guard runs ahead
        of `super().__init__` because `django_filters.Filter.__init__`
        silently absorbs unknown kwargs into `self.extra`, which would
        otherwise accept the kwarg and ignore it.
        """
        if "lookups" in kwargs:
            raise TypeError(
                "`RelatedFilter` does not accept `lookups=`; declare the lookups on the "
                "target FilterSet's `Meta.fields`.",
            )
        self._has_explicit_queryset: bool = kwargs.get("queryset") is not None
        # basedpyright: the kwargs are forwarded verbatim and ``ModelChoiceFilter.__init__`` owns
        # their validation; it rejects ``object`` kwargs for the ``str | None`` params
        super().__init__(*args, **kwargs)  # pyright: ignore[reportArgumentType]
        self._filterset: _FilterSetTarget = filterset

    def bind_filterset(self, filterset: type[FilterSet]) -> None:
        """Bind the owning `FilterSet` once; subsequent calls are no-ops.

        The public spelling of the bind the metaclass performs at class
        creation (``sets_mixins.py::collect_related_declarations`` calls
        ``_bind_owner`` directly), so a call once the declaring class exists
        is a no-op and cannot clobber that owner.

        Silent-no-op contract:
            A second call with a DIFFERENT ``filterset`` (the rare case
            of a module-level ``RelatedFilter`` instance shared across
            two ``FilterSet`` subclasses) is also silenced here. The
            strict cross-owner mismatch detection runs later at
            finalize time in
            ``types/finalizer.py::_bind_filterset_owner`` (subpass 1 of
            finalizer phase 2.5's ``_bind_filtersets`` umbrella's multi-owner
            axis checks), so a real divergent-owner reuse still surfaces a
            ``ConfigurationError`` with both owners named - just not at
            class-creation time.

        Unqualified-string caveat:
            ``bound_filterset`` is the resolution scope for an UNQUALIFIED
            string target (``RelatedFilter("ShelfFilter")``) - the
            ``.filterset`` property resolves the name against
            ``bound_filterset.__module__``. Because re-bind is a no-op, a
            single ``RelatedFilter`` INSTANCE shared across two subclasses
            (defined on a base ``FilterSet`` and inherited) keeps the FIRST
            subclass's module as that scope, so a second subclass in a
            different module that meant a same-named-but-different
            ``ShelfFilter`` would resolve to the first's. Use a class object
            or an absolute import path for a shared/inherited
            ``RelatedFilter``, or declare it per subclass.

        Thin wrapper over the shared ``RelatedSetTargetMixin._bind_owner``.
        """
        self._bind_owner(filterset)

    @override
    def _validate_target(self, resolved: object) -> type[FilterSet]:
        """Enforce the ``RelatedSetTargetMixin`` family gate: target must be a ``FilterSet``.

        Fired by ``sets_mixins.py::RelatedSetTargetMixin._resolved_target`` on
        every non-``None`` resolved read -- the one seam every consumer routes
        through (the Layer-5 BFS enqueue in
        ``utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built``,
        ``filters/sets.py::_expand_related_filter``, the finalizer's
        unregistered-target audit, ``get_queryset``'s fallback, and the
        permission traversal). Without the gate the mis-wiring survives
        declaration, binding, and expansion and first detonates inside a
        consumer (``target._filters_along(path, scope)`` or ``target._filter_table()``, or
        the BFS builder's ``target.type_name_for()``) as a raw ``AttributeError``, or -- for an
        OrderSet-shaped target -- silently walks the ORDER family's fields
        through the filter input builder. Mirrors the order twin's
        ``orders/base.py::RelatedOrder._validate_target``.

        Target and owner identity are read by ``utils/truth.py``, so a value
        is never asked whether it is a class.
        """
        if not truth.is_subclass(resolved, _filter_set_class()):
            # ``_bind_owner`` is the one writer of the owner slot, and it stores a set class.
            owner: type[object] | None = getattr(self, self._owner_attr, None)
            owner_label = truth.qualname(owner) if truth.is_type(owner) else "<unbound>"
            raise ConfigurationError(
                f"{owner_label} declares RelatedFilter {truth.render(self.field_name)} targeting "
                f"{truth.kind(resolved)}, which is not a FilterSet subclass. "
                "RelatedFilter targets must resolve to a FilterSet subclass (a class, "
                "an import-path string, or a zero-arg factory returning one); "
                "an OrderSet or unrelated class cannot filter a relation branch. "
                "Declare the branch with a FilterSet or remove it.",
            )
        return resolved

    @property
    def filterset(self) -> type[FilterSet] | None:
        """Resolve `self._filterset` lazily on first access.

        Re-stores the resolved class so the next access is a plain
        attribute read; setter remains usable when a caller wants to
        substitute the target. String / callable resolution is delegated
        to ``LazyRelatedClassMixin.resolve_lazy_class`` via the shared
        ``RelatedSetTargetMixin._resolved_target``, which also fires the
        family's target-TYPE gate (``_validate_target``): a resolved value
        must be ``None`` (the skip-silently placeholder) or a ``FilterSet``
        subclass.
        """
        return self._resolved_target()

    # basedpyright: the setter takes a lazy target (a class, an import path, or a factory)
    # that the getter resolves to the class on read
    @filterset.setter
    def filterset(self, value: _FilterSetTarget) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        self._set_target(value)

    # basedpyright: typeshed types ``QuerySetRequestMixin.get_queryset`` as never ``None``, but it
    # returns the ``queryset=`` value verbatim, which defaults to ``None``; the checker rejects the
    # ``None`` arm against the ``QuerySet`` return
    @override
    def get_queryset(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        request: object,
    ) -> models.QuerySet[models.Model] | None:
        """Derive the queryset from the target filterset's `Meta.model`.

        When no explicit `queryset=` was supplied at construction time,
        falls back to `target_filterset._meta.model._default_manager.all()`
        - the cookbook's documented auto-derivation contract. An explicit
        queryset is preserved verbatim.
        """
        if self.queryset is None:
            target = self.filterset
            model = read_attr(truth.static_attr(target, "_meta", None), "model", None)
            if model is not None:
                return base_queryset(require(model, is_model_class))
        return super().get_queryset(request)
