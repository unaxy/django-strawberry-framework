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
from dataclasses import dataclass, replace
from functools import cache
from itertools import takewhile
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple, TypeVar, final

from django.core.exceptions import FieldError, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import connections, models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.json import HasKeys as JSONHasKeys
from django.db.models.lookups import Transform
from django.db.models.sql import Query
from django.forms import (
    CharField,
    Field,
    ModelChoiceField,
    MultipleChoiceField,
    MultiWidget,
    SelectMultiple,
    TextInput,
    Widget,
)
from django.utils.choices import BaseChoiceIterator, CallableChoiceIterator, normalize_choices
from django.utils.functional import LazyObject, Promise
from django_filters import (
    CharFilter,
    ChoiceFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
)
from django_filters import constants as _filter_constants
from django_filters.fields import BaseCSVField, BaseRangeField, ChoiceField
from django_filters.filters import (
    BaseInFilter,
    BaseRangeFilter,
    FilterMethod,
    QuerySetRequestMixin,
)
from django_filters.filters import RangeFilter as DjangoFilterRangeFilter
from django_filters.filterset import BaseFilterSet, FilterSetOptions
from django_filters.utils import get_field_parts, get_model_field
from django_filters.widgets import BaseCSVWidget
from graphql import GraphQLError
from strawberry import relay
from typing_extensions import TypedDict, Unpack, override

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    LookupValidationError,
    PathResolutionError,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.relay import _coerce_pk_or_none, _node_id_slot
from django_strawberry_framework.sets_mixins import (
    LazyRelatedClassMixin as LazyRelatedClassMixin,  # noqa: PLC0414 - kept re-export path
)  # re-exported via filters.__init__
from django_strawberry_framework.sets_mixins import RelatedSetTargetMixin
from django_strawberry_framework.types.converters import _field_label
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
from django_strawberry_framework.utils._array_field import (
    array_element_field,
    array_leaf_field,
    is_array_in_lookup,
)
from django_strawberry_framework.utils._narrowing import (
    dict_of,
    is_concrete_field,
    is_dict,
    is_list,
    is_list_or_tuple,
    is_str,
    optional_instance,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.errors import (
    FILTER_INVALID_ERROR_CODE,
    GLOBALID_INVALID_ERROR_CODE,
    GLOBALID_UNVALIDATABLE_ERROR_CODE,
    coded_error_extensions,
    held_past_integer_range,
)
from django_strawberry_framework.utils.imports import import_attr_if_importable
from django_strawberry_framework.utils.permissions import (
    alias_relation_path,
    set_bound_definition,
)
from django_strawberry_framework.utils.querysets import (
    _names_to_path,
    base_queryset,
    coerce_field_value_or_none,
    lookup_target_fields,
    split_lookup,
    truncates_to_integer,
)
from django_strawberry_framework.utils.relations import (
    _classify_path_cached,
    _walk_lookup_expr,
    choice_key_field,
    generated_column,
    generated_column_source,
    is_model_class,
    lookup_operand,
    lookup_registry,
    lookup_transform_parts,
    relation_bool,
    stored_value_column,
    stored_value_link,
)
from django_strawberry_framework.utils.typing import object_result, strawberry_schema_from_info

#: django-filter's ``EMPTY_VALUES``: the values a filter treats as "not supplied". The stub
#: types the constant ``Any``; it is a tuple of values.
EMPTY_VALUES = require(read_attr(_filter_constants, "EMPTY_VALUES"), is_list_or_tuple)

#: django-filter's ``Filter.method`` property, read off the class: the stub declares the slot a
#: plain attribute, so ``Filter.method`` types as its value, not the property.
_FILTER_METHOD_PROPERTY = require_instance(truth.static_attr(Filter, "method"), property)

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
# (``finalizer._audit_globalid_filter_strategies``) refuses every leaf a wired
# filterset serves (its reached sets' included) that decodes against one, and
# this runtime guard answers for what the audit does not ask: a filterset no
# wired type serves, applied from a project's own resolver. The names are needed
# for the reject message so the literal lives here rather than being derived by
# exclusion.
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
    _FILTER_METHOD_PROPERTY.__set__(filter_instance, value)
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

    The key is the path Django walks and the lookup applied where it ends
    (``_bound_field_name`` / ``_bound_lookup_expr``), the argument the filter's own
    ``field_name__lookup_expr`` spells. ``field_name`` overrides that path for the lookup
    key (the lookup is always the walk's). A GlobalID or raw-key
    filter passes the path its value compares (``_globalid_predicate_path``,
    computed from the walked path at filter time): the target column a
    consumer ``relay.NodeID[...]`` names, or the pk-qualified relation path
    ``f"{live_field_name}__pk"`` for a forward relation stored on a non-pk
    ``to_field``, so the predicate never compares the raw FK-stored column.
    """
    field = _bound_field_name(filter_instance) if field_name is None else field_name
    lookup = f"{field}__{_bound_lookup_expr(filter_instance)}"
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

# A copy of a relation-key filter whose ``field_name`` names a ``FilteredRelation`` alias
# the package joins its relation through (``filters/sets.py::FilterSet._relation_view``)
# carries a ``_RelationView``: its GlobalID target resolves from the relation path, and a
# target whose id is not its primary key compares that id through the alias.
_RELATION_VIEW_ATTR = "_dst_relation_view"


@dataclass(frozen=True)
class _RelationView:
    """The ``FilteredRelation`` alias a relation-key filter's copy is bound to, and its relation.

    ``alias`` is the copy's ``field_name``; ``path`` is the relation path the filter was
    declared with, which the alias joins through over the rows the request may see.
    """

    alias: str
    path: str


def _relation_view_of(filter_instance: Filter) -> _RelationView | None:
    """Return the ``_RelationView`` a relation-view copy carries, ``None`` for any other filter."""
    return optional_instance(getattr(filter_instance, _RELATION_VIEW_ATTR, None), _RelationView)


#: No ``FilteredRelation`` alias for a filter's path to start at (``_query_aliases``).
_NO_ALIASES: Mapping[str, str] = MappingProxyType({})


def _query_aliases(queryset: models.QuerySet[models.Model, object]) -> Mapping[str, str]:
    """Return each ``FilteredRelation`` alias ``queryset`` holds, to its ``relation_name``.

    The aliases a filter's path may start at: a flat leaf's walk reads them
    (``filters/sets.py::FilterSet._flat_leaf_walk``), and a GlobalID filter resolves its
    target through them (``_globalid_target``). Read from ``Query._filtered_relations``,
    the dict Django resolves a path's first name against (``Query.names_to_path``).
    """
    filtered = require(read_attr(queryset.query, "_filtered_relations", None), is_dict)
    return {
        str(alias): require_instance(relation, models.FilteredRelation).relation_name
        for alias, relation in filtered.items()
    }


# A copy of a relation-key filter re-bound to the target's key over the target rows
# (``filters/sets.py::FilterSet._routed_leaf_chain``: a to-many key, or a GlobalID key
# whose target's id an annotation holds, forward or to-many), and a copy of a leaf ending
# on the target's primary key past a declared hop into a set no type wires, carries the
# leaf as declared (``_KeyLeaf``): a GlobalID value names the type registered for the
# relation's target, so the copy resolves its target as that leaf does, whichever type the
# face or set it is bound to answers for.
_KEY_LEAF_ATTR = "_dst_key_leaf"


@dataclass(frozen=True, eq=False)
class _KeyLeaf:
    """The declared leaf a re-bound copy resolves its GlobalID target as, and its aliases.

    ``aliases`` are the ``FilteredRelation`` aliases of the rows the declaring set's leaves
    run over (``_query_aliases``): the copy filters other rows, so a declared path starting
    at one of them resolves through these.
    """

    leaf: Filter
    aliases: Mapping[str, str] = _NO_ALIASES


def _key_leaf_of(filter_instance: Filter) -> _KeyLeaf | None:
    """Return the ``_KeyLeaf`` a copy marked ``_KEY_LEAF_ATTR`` carries, else ``None``.

    The copy is a relation key's re-bound to the target's key, or a leaf's ending on the
    target's primary key past a declared hop into a set no type wires.
    """
    return optional_instance(getattr(filter_instance, _KEY_LEAF_ATTR, None), _KeyLeaf)


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


def _declared_field_name(filter_instance: Filter) -> str:
    """Return the ``field_name`` a filter bound to a ``FilterSet`` was declared with.

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


def _bound_field_name(filter_instance: Filter) -> str:
    """Return the ORM path a per-request filter walks: ``_filterset_walked_lookup``'s first part.

    Read against the filterset django-filter's ``BaseFilterSet.__init__`` stamps as
    ``filter_.parent``, so a ``lookup_expr`` continuing the path across a relation
    (``field_name="shelf", lookup_expr="tier__in"``) answers the path Django walks
    (``shelf__tier``); the filter's own ``field_name`` stays as declared.
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    return _filterset_walked_lookup(parent, filter_instance)[0]


def _bound_lookup_expr(filter_instance: Filter) -> str:
    """Return the lookup a per-request filter applies where its path ends: the walk's second part.

    ``_bound_field_name``'s companion: ``in`` for ``field_name="shelf",
    lookup_expr="tier__in"``, the filter's own ``lookup_expr`` wherever no relation is
    crossed past its ``field_name``.
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    return _filterset_walked_lookup(parent, filter_instance)[1]


def _bound_resolved_field(
    filter_instance: Filter,
    query: Query | None = None,
) -> _ResolvedField | None:
    """Return the field and column path a per-request filter's ORM path names.

    Reads the LIVE ``field_name`` against the filterset django-filter's
    ``BaseFilterSet.__init__`` stamps as ``filter_.parent``, so an expanded leaf whose
    ``field_name`` was rebased under a ``RelatedFilter`` prefix resolves the terminal
    field (``_filterset_resolved_field``). A path the model names no field for and the
    queryset that filterset was handed resolves (``_model_unresolved_query``: a queryset
    annotation or alias, a ``FilteredRelation`` alias and the columns past it) answers the
    field it names there (``_query_path_field``), on the filter's own path; ``query``, when
    given, is the query of the queryset the filter is applied to, read in its place.
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    resolved = _filterset_resolved_field(parent, filter_instance)
    query = _model_unresolved_query(
        filter_instance,
        _filterset_lookup_operand(parent, filter_instance),
        query,
    )
    if query is None or (resolved is not None and resolved.field is not None):
        return resolved
    field_name = _bound_field_name(filter_instance)
    field = _query_path_field(query, field_name)
    return resolved if field is None else _ResolvedField(field, field_name)


def _model_unresolved_query(
    filter_instance: Filter,
    operand: _LookupOperand,
    query: Query | None = None,
) -> Query | None:
    """Return ``_bound_query`` for a per-request filter its model's walk answers no field for.

    ``operand`` is the model's answer (``_filterset_lookup_operand``), which reads every
    path a fresh ``Query`` of the model resolves, cached per key; only a path it answers no
    field for (a queryset annotation or alias, a ``FilteredRelation`` alias and the columns
    past it) is read over the queryset the filter's ``FilterSet`` was handed, or over
    ``query`` when given: the query of the queryset a bound filter is applied to, which
    holds what a consumer ``filter_queryset`` added. ``None`` for every other filter, a
    ``method=`` filter included (its own method receives the value, so it keeps the
    model's answer), and for a filter bound to no ``FilterSet`` instance.
    """
    if read_attr(filter_instance, "method", None) is not None or operand.field is not None:
        return None
    bound = _bound_query(filter_instance)
    return bound if bound is None or query is None else query


def _bound_query(filter_instance: Filter) -> Query | None:
    """Return the query of the queryset a per-request filter's ``FilterSet`` was handed.

    django-filter's ``BaseFilterSet.__init__`` stores the queryset (the model's default
    one when handed none) before it stamps each per-request filter's ``parent``, so a
    path only that queryset resolves (a queryset annotation or alias, a
    ``FilteredRelation`` alias and the columns past it) is read where it is held. ``None``
    for a filter bound to no ``FilterSet`` instance (a class-level declaration, a
    standalone filter) and for one whose ``queryset`` is no ``QuerySet``.
    """
    parent = read_attr(filter_instance, "parent", None)
    if not isinstance(parent, BaseFilterSet):
        return None
    queryset = read_attr(parent, "queryset", None)
    return queryset.query if isinstance(queryset, models.QuerySet) else None


def _query_path_field(query: Query, field_path: str) -> ModelField | None:
    """Return the field ``field_path`` names over ``query``, ``None`` where it names none.

    Split as ``Query.build_filter`` splits a filter argument
    (``utils/querysets.py::split_lookup``): a path naming an annotation or alias
    ``query`` holds answers its ``output_field``, one crossing a ``FilteredRelation``
    alias the field it ends on, an alias of a reverse relation that relation (its
    ``ForeignObjectRel``, as the model's walk answers the relation's own name). ``None``
    where Django refuses the path (``FieldError``),
    where a part of it is left over as a transform (``_query_lookup_operand`` reads that
    output), and for an expression whose output Django cannot resolve.
    """
    try:
        _names, start, leftover = split_lookup(query, field_path)
        if leftover:
            return None
        if isinstance(start, models.ForeignObjectRel):
            return start
        output = start if is_concrete_field(start) else read_attr(start, "output_field", None)
    except FieldError:
        return None
    return output if is_concrete_field(output) else None


def _query_lookup_operand(
    query: Query,
    field_path: str,
    lookup_expr: str,
) -> _LookupOperand | None:
    """Return ``_LookupOperand`` for ``field_path`` and ``lookup_expr`` read over ``query``.

    Split as ``Query.build_filter`` splits the argument (``utils/querysets.py::split_lookup``)
    and the leftover walked from where the path ends as ``Query.build_lookup`` walks it
    (``utils/relations.py::_walk_lookup_expr``): the field is the output of the lookup's
    left-hand side, an annotation's own or a transform's of it. Uncached: the query is
    the request's. A path ending on a reverse relation (a ``FilteredRelation`` alias of
    one) answers it as ``_model_lookup_operand`` answers the relation's own name on the
    model: the relation and the lookup its forward field registers. ``None`` where Django
    refuses the path or no walk
    accepts the leftover (``FieldError``, ``LookupValidationError``).
    """
    try:
        _names, start, leftover = split_lookup(
            query,
            LOOKUP_SEP.join((field_path, lookup_expr)),
        )
        if isinstance(start, models.ForeignObjectRel):
            walk = _walk_lookup_expr(start, LOOKUP_SEP.join(leftover) or "exact")
            return _LookupOperand(
                start,
                issubclass(walk.lookup, models.lookups.IsNull),
                walk.lookup,
                walk.node_types,
            )
        walk = _walk_lookup_expr(start, LOOKUP_SEP.join(leftover) or "exact")
        output = read_attr(walk.lhs, "output_field", None)
    except (FieldError, LookupValidationError):
        return None
    return _LookupOperand(
        # Past a start that is no reverse relation, the left-hand side is a ``Col`` or an
        # expression, whose resolved ``output_field`` is a model ``Field``.
        require(output, is_concrete_field),
        issubclass(walk.lookup, models.lookups.IsNull),
        walk.lookup,
        walk.node_types,
    )


def _bound_lookup_operand(filter_instance: Filter, query: Query | None = None) -> _LookupOperand:
    """Return what one value a per-request filter applies is compared as.

    ``_filterset_lookup_operand`` over the filterset django-filter stamps as
    ``filter_.parent``, read on its model; a path the model names no field for (a queryset
    annotation or alias, a ``FilteredRelation`` alias) is read over the queryset that
    filterset was handed (``_bound_query``, ``_query_lookup_operand``), the queryset the
    filter's predicate is built on, or over ``query`` when one is given: the rows a
    consumer ``filter_queryset`` passes on (``filters/sets.py::FilterSet._clean_late_comparisons``).
    A ``method=`` filter keeps the model's answer: its own method receives the value.
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    operand = _filterset_lookup_operand(parent, filter_instance)
    query = _model_unresolved_query(filter_instance, operand, query)
    if query is None:
        return operand
    resolved = _query_lookup_operand(query, *_filterset_walked_lookup(parent, filter_instance))
    return operand if resolved is None else resolved


def _bound_model_field(filter_instance: Filter, query: Query | None = None) -> ModelField | None:
    """Return the model field a per-request filter's ORM path names on its FilterSet's model.

    The field of ``_bound_resolved_field`` (over ``query`` where the model names none);
    ``None`` when the path names none.
    """
    resolved = _bound_resolved_field(filter_instance, query)
    return None if resolved is None else resolved.field


def _bound_value_field(filter_instance: Filter, query: Query | None = None) -> ModelField | None:
    """Return the field each value a per-request filter applies is a value of.

    The field of ``_bound_lookup_operand``: ``_filterset_value_field`` over the filterset
    django-filter's ``BaseFilterSet.__init__`` stamps as ``filter_.parent``, and for a path
    only the queryset that filterset was handed (or ``query``) resolves, the output of the
    lookup's left-hand side read over it.
    """
    return _bound_lookup_operand(filter_instance, query).field


def _reads_integer_transform(filter_instance: Filter, query: Query) -> bool:
    """Whether a per-request filter compares an integer transform output.

    A generated ``<column>__year__in``, an ``ArrayField``'s ``len``, or a transform a
    project registers on a column (``Field.register_lookup``) with an ``IntegerField``
    output: its values are integers no column stores (``_bound_value_field``), held to
    their range where the filter form asks the database
    (``filters/sets.py::_unbindable_value_errors``), never coerced through the column.
    A named ``ExtractYear`` / ``ExtractMonth`` alias starts at the actual ``Transform``
    expression even though its path and value fields are the same output object;
    ``split_lookup`` distinguishes it from a ``Col`` alias and a non-transform
    annotation such as ``Count``, which keep their existing integer-member behavior.
    A transform registered on a stored integer column can keep the column's
    output-field identity too; the actual operand's ``node_types`` records that
    transform even when the Query starts at the stored field. ``query`` is the
    queryset the filter will actually apply to: a scoped terminal's synthetic
    parent holds no queryset, while its visible child rows already hold the
    annotation and must answer the same question as a handed queryset. Field
    identity alone cannot prove a transform: a stored ``GeneratedField`` is a
    wrapper around the ``output_field`` its native ``cached_col`` exposes, so
    only an actual transform node or starting expression establishes one.
    """
    field_name, lookup_expr = (
        _bound_field_name(filter_instance),
        _bound_lookup_expr(filter_instance),
    )
    operand = _query_lookup_operand(query, field_name, lookup_expr)
    if operand is None:
        return False
    value_field = operand.field
    if not isinstance(value_field, models.IntegerField):
        return False
    if any(issubclass(node_type, Transform) for node_type in operand.node_types):
        return True
    # The split ``_query_lookup_operand`` just accepted: the same path over the same query.
    _names, start, _leftover = split_lookup(query, LOOKUP_SEP.join((field_name, lookup_expr)))
    return isinstance(start, Transform)


class _LookupOperand(NamedTuple):
    """What one value a filter applies is compared as: a value of ``field``, or a null test's flag.

    ``null_test`` is whether the terminal lookup past the transforms is Django's ``IsNull``
    (a ``year__isnull`` leaf), whose operand is a boolean, never a value of ``field``. It is
    the resolved lookup's class, not its name: a consumer lookup registered as ``isnull``
    over a transform's output takes the operand its own class compares. ``lookup`` is that
    class, ``None`` where no walk resolved one (a ``method=`` filter, whose method applies
    no lookup of the filter's, a path the walk refuses, which a set publishes only past a
    name the related model lacks or under a consumer ``filter`` override,
    ``refuse_unresolvable_lookup``): ``filters/inputs.py`` asks it whether the value is
    prepared through the column (Django's ``FieldGetDbPrepValueMixin``), and
    ``refuse_listless_lookup`` whether it takes the list a ``ListFilter`` applies.
    ``node_types`` are the classes the predicate holds past the column, each transform's then
    the lookup's (``utils/relations.py::_LookupWalk.node_types``), a reverse relation key's
    too (the relation delegates its lookup registry to its forward field), empty where no walk
    resolved them.
    """

    field: ModelField | None
    null_test: bool
    lookup: type[models.lookups.Lookup] | None = None
    node_types: tuple[type[object], ...] = ()


@cache
def _lookup_operand(column: ConcreteField, lookup_expr: str) -> _LookupOperand | None:
    """Return the output field of the transforms ``lookup_expr`` applies to ``column``, and its lookup.

    The walk is ``utils/relations.py::lookup_operand``, from the column Django's query
    builds for ``column`` (``Field.cached_col``), so each transform and lookup is the one
    the filter's predicate resolves; the lookup is named by its class's ``lookup_name``, as
    ``django_filters.utils.resolve_field`` names it. The answer is kept per ``(column,
    lookup_expr)``, both fixed when the FilterSet is defined: every key is kept, a set
    bounded by the columns and lookups the defined FilterSets name. No entry is
    invalidated: Django registers lookups and transforms at startup, before any FilterSet
    resolves one. ``None`` when the walk refuses the expression (a name that is no
    transform or lookup of the column, as a relation hop is not) or the database
    expression cannot resolve an output (Django's ``FieldError``).

    A ``GeneratedField``'s computed column (``utils/relations.py::generated_column``) is
    walked from the generated field's own column (``generated_column_source``), whose
    lookups Django resolves on the ``output_field`` instance, where a project registers its
    own (``Field.register_lookup`` on the instance), none of which the clone carries. An
    output that is that instance (no transform, or one whose output is its source's)
    answers as the computed column.
    """
    try:
        output, lookup, node_types = lookup_operand(
            generated_column_source(column) or column,
            lookup_expr,
        )
    except (LookupValidationError, FieldError):
        return None
    return _LookupOperand(output, issubclass(lookup, models.lookups.IsNull), lookup, node_types)


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
    as an unknown field. A path django-filter's walk reads only by staying on a model past
    a part it cannot cross (``get_field_parts``: a column, a forward ``GenericForeignKey``)
    names no field, where django-filter would answer a sibling column sharing the next
    part's name (``payload__flag`` is a key of the ``payload`` JSON column, not the
    ``flag`` column); its value is read off the part's transforms
    (``_filterset_value_field``).
    """
    model = _filterset_model(filterset)
    if model is None:
        return None
    return _model_resolved_field(model, _filterset_walked_lookup(filterset, filter_instance)[0])


def _filterset_lookup_source_field(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> ModelField | None:
    """Return the field Django starts a leaf's lookup walk from, before any transform.

    The query's own split finds the field part when ``field_name`` or ``lookup_expr``
    contains transforms. A method owns its lookup token, so only its declared field name
    is read. This source keeps generated-output policy even when the final operand is a
    Boolean null test or a transform's different output field.
    """
    model = _filterset_model(filterset)
    if model is None:
        return None
    path, lookup_expr = _filterset_walked_lookup(filterset, filter_instance)
    if read_attr(filter_instance, "method", None) is not None:
        return _model_resolved_field(model, path).field
    try:
        head, _start, _leftover = split_lookup(Query(model), LOOKUP_SEP.join((path, lookup_expr)))
    except FieldError:
        return _model_resolved_field(model, path).field
    return _model_resolved_field(model, LOOKUP_SEP.join(head)).field


def _model_resolved_field(model: type[models.Model], field_path: str) -> _ResolvedField:
    """Resolve ``field_path`` on ``model``: ``_filterset_resolved_field`` once the model is read.

    A path naming a ``GeneratedField`` answers the column it computes
    (``utils/relations.py::generated_column``), so every read of a filter's column
    (its input type, the form field that cleans a value, the integer range guards of
    ``IntegerInFilter`` and ``IntegerRangeFilter``) sees the output's class; the path still
    names the generated field, so the predicate is the one Django builds for it. A path the
    classifier refuses keeps django-filter's answer only where its walk crossed a relation
    at every part before the last (``_filterset_resolved_field``).
    """
    try:
        field: ModelField = _classify_path_cached(model, field_path).terminal
    except PathResolutionError:
        # django-filter's walk stays on the model past a part it cannot cross
        # (``get_field_parts`` reads ``payload__flag`` as the ``flag`` column); Django reads
        # such a path as that part and its transforms (``Query.solve_lookup_type``).
        # ``get_field_parts`` answers ``None`` for a part naming no field (typeshed omits it).
        parts = get_field_parts(model, field_path)
        if not parts or any(part.related_model is None for part in parts[:-1]):
            return _ResolvedField(None, field_path)
        return _ResolvedField(get_model_field(model, field_path), field_path)
    if field_path.rpartition(LOOKUP_SEP)[2] != "pk":
        return _ResolvedField(generated_column(field) or field, field_path)
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
    ``counts__0_2``), or both. The output is the one Django's query resolves
    (``_lookup_operand``, the walk a generated leaf's filter class is selected by too,
    ``filters/sets.py::FilterSet.filter_for_field``): ``year`` / ``len`` an ``IntegerField``, ``date`` a
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
    none). The path is the one Django walks (``_filterset_walked_lookup``): a
    ``lookup_expr`` continuing it across a relation (``field_name="shelf",
    lookup_expr="topic__icontains"``) answers the column it reaches, as
    ``field_name="shelf__topic"`` does. A field the path names answers itself where the
    walk reads no transform: a relation, a crossing pair on a filter holding a ``filter``
    of its own included (it reads its pair as declared). A ``method=`` filter answers
    its model field: its own method, not a lookup, receives the value, so it is published
    and cleaned by the column.
    """
    return _filterset_lookup_operand(filterset, filter_instance).field


def _filterset_lookup_operand(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> _LookupOperand:
    """Return ``_filterset_value_field``'s field with whether its terminal lookup is a null test.

    The lookup is the walk's answer past the transforms (``_lookup_operand``), and the
    filter's own ``lookup_expr`` (``isnull`` by name) wherever the field is not read off
    that walk (a ``method=`` filter's too, whose method applies no lookup of the filter's:
    ``filters/inputs.py`` lets its own form type a value it cleans).
    """
    from .sets import FilterSet, ProjectedChildFilter, _leaf_declaration  # noqa: PLC0415 - import cycle

    if isinstance(filter_instance, ProjectedChildFilter):
        owner = filterset if isinstance(filterset, type) else type(filterset)
        if issubclass(owner, FilterSet):
            declaration = _leaf_declaration(filter_instance, owner)
            if declaration.declared is not filter_instance:
                return _filterset_lookup_operand(declaration.filterset, declaration.declared)
    lookup_expr = filter_instance.lookup_expr
    if read_attr(filter_instance, "method", None) is not None:
        return _LookupOperand(
            _filterset_model_field(filterset, filter_instance),
            _names_null_test(lookup_expr),
        )
    model = _filterset_model(filterset)
    if model is None:
        return _LookupOperand(None, _names_null_test(lookup_expr))
    return _model_lookup_operand(model, *_filterset_walked_lookup(filterset, filter_instance))


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
            return _LookupOperand(None, _names_null_test(lookup_expr))
        # The field part is the one Django's split just walked, so it names a column.
        path_column = require(
            lookup_target_fields(query, LOOKUP_SEP.join(field_parts))[0],
            is_concrete_field,
        )
        operand = _lookup_operand(path_column, LOOKUP_SEP.join((*transforms, lookup_expr)))
        return _LookupOperand(None, _names_null_test(lookup_expr)) if operand is None else operand
    if not is_concrete_field(column):
        try:
            walk = _walk_lookup_expr(column, lookup_expr)
        except LookupValidationError:
            return _LookupOperand(column, _names_null_test(lookup_expr))
        return _LookupOperand(
            column,
            issubclass(walk.lookup, models.lookups.IsNull),
            walk.lookup,
            walk.node_types,
        )
    operand = _lookup_operand(column, lookup_expr)
    return _LookupOperand(column, _names_null_test(lookup_expr)) if operand is None else operand


def _filterset_lookup_lhs_path(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    field_name: str,
    lookup_expr: str,
) -> str | None:
    """Return the path ``field_name`` and ``lookup_expr`` compare on ``filterset``'s model.

    ``_lookup_lhs_path`` over a fresh ``Query`` of the model, which holds no annotation:
    the names Django walks as a path, then each transform its query applies ahead of the
    lookup, a bare trailing transform (``lookup_expr="date"``, an implicit ``exact``)
    included. ``None`` for a filterset with no model, a path only the queryset a filter
    runs on resolves (an annotation, a ``FilteredRelation`` alias: Django's
    ``FieldError``), or a ``lookup_expr`` no walk from where the path ends accepts
    (``LookupValidationError``: ``bogus``, which a set publishes only on a filter whose
    ``filter`` is consumer code, ``refuse_unresolvable_lookup``, or a ``range`` past a
    ``pk`` that is a relation, which Django registers no ``range`` lookup on;
    ``RangeFilter.filter`` walks the column the key stores instead).
    """
    model = _filterset_model(filterset)
    if model is None:
        return None
    return _query_lookup_lhs_path(Query(model), field_name, lookup_expr)


def _query_lookup_lhs_path(query: Query, field_name: str, lookup_expr: str) -> str | None:
    """Return ``_lookup_lhs_path`` for ``field_name`` and ``lookup_expr`` over ``query``.

    ``None`` where Django refuses the path (``FieldError``) or no walk from where it ends
    accepts the ``lookup_expr`` (``LookupValidationError``).
    """
    try:
        return _lookup_lhs_path(query, LOOKUP_SEP.join((field_name, lookup_expr)))
    except (FieldError, LookupValidationError):
        return None


def _bound_lookup_lhs_path(filter_instance: Filter, field_name: str) -> str | None:
    """Return ``_filterset_lookup_lhs_path`` for a per-request filter, read over its queryset too.

    The model's answer; for a path only the queryset its ``FilterSet`` was handed resolves
    (``_model_unresolved_query``), the answer over that queryset's query. ``None`` where
    neither resolves it.
    """
    parent: BaseFilterSet | None = getattr(filter_instance, "parent", None)
    lookup_expr = _bound_lookup_expr(filter_instance)
    path = _filterset_lookup_lhs_path(parent, field_name, lookup_expr)
    query = _model_unresolved_query(
        filter_instance,
        _filterset_lookup_operand(parent, filter_instance),
    )
    if path is not None or query is None:
        return path
    return _query_lookup_lhs_path(query, field_name, lookup_expr)


def _names_null_test(lookup_expr: str) -> bool:
    """Whether a ``lookup_expr`` no walk resolved names Django's null test: ``isnull``."""
    return lookup_expr == "isnull"


def _column_form_field(
    filter_instance: Filter,
    *,
    element: bool = False,
    query: Query | None = None,
) -> Field | None:
    """Return the form field that cleans one value of a bound filter's column for a comparison.

    The column is the field each value the filter applies is a value of
    (``_bound_value_field``): the column itself, or the output of the transforms between
    it and the lookup (``year``'s ``IntegerField``, ``date``'s ``DateField``, an
    ``ArrayField`` index's ``base_field``), so a value is cleaned as the type it is
    published as. For a path only the queryset the parent was handed resolves (a queryset
    annotation or alias, a ``FilteredRelation`` alias and the columns past it) it is the
    field that queryset compares, though the leaf is published ``String``: no queryset
    exists when the schema is built. The field is the one django-filter's own ``gte``
    filter for the column builds (``FilterSet._upstream_filter_for_lookup``: a
    ``NumberFilter``'s ``DecimalField`` for a decimal or integer column, a
    ``DateTimeFilter``'s ``DateTimeField`` for a datetime one, a ``CharFilter``'s
    ``CharField`` for text, ...), the owner of what one scalar value of that column may
    be, so a value a declared filter hands the ORM is held to the rule
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
    path resolving to no column, or a column django-filter builds no filter for. A
    relation is cleaned as the column a value compared on it meets
    (``_compared_value_column``: the target column the relation compares on, its
    ``to_field``, else the primary key), as ``<relation>__<that column>`` cleans it, never
    by django-filter's own form field for a relation, ``ModelChoiceField``, which looks
    every value up in the target's default manager: a key no row holds would answer
    "Select a valid choice" where one the target's ``get_queryset`` hides answers rows, an
    existence oracle the package's own relation keys refuse (``_RelationIdentityListField``).
    A ``lookup_expr`` continuing the path across a relation is cleaned as the column the
    walk reaches (``_bound_value_field``, over ``_filterset_walked_lookup``), as
    ``field_name="<relation>__<column>"`` cleans it.
    ``None`` for a relation no one column holds a value of: one compared on more than one
    column or on none, one whose ``lookup_expr`` Django does not apply to the relation
    itself (``range``, which Django registers on no relation, or a crossing pair on a
    filter holding a ``filter`` of its own, which reads its pair as declared), or one a
    ``method=`` filter names, whose method applies no lookup of the filter's to the
    relation.
    ``element`` reads one element of a list value: an ``ArrayField`` column's element is a
    value of its innermost ``base_field``, the column a nested array's leaves are stored
    through (``utils/_array_field.py::array_leaf_field``), any other column's a value of
    the column itself.
    ``query`` is the query of the rows the filter applies to when it is not the one the
    parent was handed (``filters/sets.py::FilterSet._clean_late_comparisons``: the
    queryset a consumer ``filter_queryset`` builds before it calls ``super()``), read as
    ``_query_lookup_operand`` reads it.
    """
    parent = read_attr(filter_instance, "parent", None)
    if not isinstance(parent, BaseFilterSet):
        return None
    model_field = _bound_value_field(filter_instance, query)
    if model_field is None:
        return None
    if element:
        leaf, depth = array_leaf_field(model_field)
        if depth:
            model_field = require(leaf, is_concrete_field)
    column = _compared_value_column(filter_instance, model_field)
    if column is None:
        return None
    return comparison_form_field(type(parent), column, _bound_field_name(filter_instance))


def comparison_form_field(
    filterset_cls: type[BaseFilterSet],
    model_field: ModelField,
    field_name: str | None,
) -> Field | None:
    """Return the form field django-filter's own ``gte`` filter for ``model_field`` builds.

    The filter is the one ``filterset_cls`` selects without the package ``FilterSet``'s own
    ``filter_for_lookup`` override (``FilterSet._upstream_filter_for_lookup``); any other
    django-filter ``FilterSet`` is asked through its own ``filter_for_lookup``. Built on
    ``field_name`` with the params django-filter pairs with the class. ``None`` for a field
    django-filter builds no filter for.
    """
    if issubclass(filterset_cls, _filter_set_class()):
        filter_class, params = filterset_cls._upstream_filter_for_lookup(model_field, "gte")
    else:
        filter_class, params = filterset_cls.filter_for_lookup(
            require(model_field, is_concrete_field),
            "gte",
        )
    if filter_class is None:
        return None
    return _built_filter(filter_class, field_name, params).field


def copied_form_field(filter_instance: Filter) -> Field:
    """Return the form field the filter's own class builds, read on a copy of the filter.

    ``Filter.field`` caches the field in the filter's ``_field`` (and a subclass may write
    more: a ``queryset`` into ``extra``, a field half built before it raises); a class-level
    declaration is shared by every request and deep-copied into each one, so a read of it
    must not write to it. The read runs on ``copied_filter``'s copy, so the filter class's
    own ``field``, a consumer subclass's override included, builds it, the declaration keeps
    nothing and no deferred ``choices`` are evaluated.
    """
    return copied_filter(filter_instance).field


def defers_choices(filter_instance: Filter) -> bool:
    """Whether the filter's ``choices`` are evaluated only by the form each request builds.

    Django's ``normalize_choices`` leaves a value it reads as lazy to whoever iterates it: a
    ``BaseChoiceIterator`` (the ``CallableChoiceIterator`` it makes of callable choices,
    django-filter's ``ChoiceIterator``), a ``lazy()`` promise, and a callable, which it wraps
    in a ``CallableChoiceIterator``. A ``SimpleLazyObject`` and a ``QuerySet`` are left
    unread by django-filter's own choice fields and by the build's copy
    (``copied_filter``). Any of them may read the database, so the build never evaluates
    them; a ``Choices`` class is no such callable (Django reads its ``.choices``). Each
    class is read off the value's real class (``utils/truth.py::is_one_of``), which forces
    no ``SimpleLazyObject``.
    """
    choices = dict_of(filter_instance.extra).get("choices")
    return truth.is_one_of(
        choices,
        (
            BaseChoiceIterator,
            Promise,
            LazyObject,
            models.QuerySet,
        ),
    ) or (callable(choices) and isinstance(normalize_choices(choices), CallableChoiceIterator))


class _UnreadChoices(CallableChoiceIterator):
    """Django's ``CallableChoiceIterator`` that also answers ``len()``, for the build's copy.

    ``copied_filter`` hands a ``SimpleLazyObject`` or ``QuerySet`` ``choices`` over in it, so
    building a Django choice form field evaluates nothing. Django's own wrapper has no
    ``__len__``, but the value it stands in for has one, and consumer code reading
    ``len(self.choices)`` in a ``field_class.__init__`` (or ``len(self.extra["choices"])`` in
    a ``field`` override) built against the declared value: ``__len__`` counts what iterating
    answers, evaluating the choices as the declared value would (a ``SimpleLazyObject`` and a
    ``QuerySet`` cache what they evaluate, so the count of evaluations is the declared
    value's). It counts by iterating, never ``len(list(self))``, which asks ``__len__`` for a
    length hint and recurses. ``__bool__`` keeps the wrapper's own truthiness (an object
    without ``__len__`` is true), so a truth test still evaluates nothing.
    """

    def __len__(self) -> int:
        return sum(1 for _ in iter(self))

    def __bool__(self) -> bool:
        return True


def copied_filter(filter_instance: Filter) -> Filter:
    """Return the schema build's copy of the filter: a deep copy, as django-filter makes per request.

    Django's own choice form fields (``ChoiceField``, ``TypedChoiceField``,
    ``MultipleChoiceField``, ``TypedMultipleChoiceField``, a consumer ``field_class`` on
    them) normalize ``choices`` when they are built, which forces a ``SimpleLazyObject`` and
    runs a ``QuerySet``; django-filter's own choice fields leave them to whoever iterates
    them. The build reads the filter's form field, never its deferred choices
    (``defers_choices``), so on the copy such ``choices`` are handed over in the lazy wrapper
    ``normalize_choices`` makes of callable choices and leaves unread (``_UnreadChoices``, a
    ``CallableChoiceIterator`` answering ``len()``): building the field evaluates nothing,
    and iterating its choices still answers the declared ones. A consumer ``field_class``
    whose ``__init__`` reads its own ``choices`` (``len()`` included), or a ``field``
    override reading ``extra["choices"]``, evaluates them where it is built, as often as it
    would on the declared value. Each request's copy is django-filter's and keeps the
    ``choices`` as declared.
    """
    probe = copy.deepcopy(filter_instance)
    choices = dict_of(probe.extra).get("choices")
    if truth.is_one_of(choices, (LazyObject, models.QuerySet)):
        probe.extra["choices"] = object_result(_UnreadChoices, lambda: choices)
    return probe


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
    ``via`` names the ``RelatedFilter`` attributes the filter was reached through,
    outermost first and joined by ``, then``, when it was. Two callers copy: the
    finalizer's audit of every published table a wired set serves
    (``types/finalizer.py::_audit_filter_copies``) and a ``RelatedFilter`` expansion,
    naming the one declaration it copies through (``filters/sets.py::_expand_related_filter``).
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

    def _hand_column_field(self, _field: Field, _query: Query | None = None, /) -> None:
        """Give the form field this bound filter just built its column's comparison field.

        The column is read over the queryset the parent was handed, or over the query
        given (``_column_form_field``).
        """
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

    ``element_field`` is the form field of the ``gte`` filter for the value each element
    compares, the column's or a transform output's (an ``ArrayField``'s innermost
    ``base_field``'s for an array column, a relation's key column, ``_compared_value_column``),
    so an element that value cannot hold is a form error rather than a value handed to the
    ORM, a text element is stripped and a naive datetime element made aware, under any
    django-filter ``FilterSet`` parent. Over an ``ArrayField`` of arrays (``depth``, the
    column's levels, ``utils/_array_field.py::array_leaf_field``) a list or tuple element of a
    whole-array lookup's value (``exact``, ``contains``, ``contained_by``, ``overlap``) is
    descended at any depth and each member that is no list is cleaned the same way: Django's
    ``ArrayRHSMixin`` prepares only the outermost members of such a value, through an inner
    ``ArrayField`` that prepares nothing, and PostgreSQL's containment and overlap read a
    multidimensional array's elements whatever its dimensions, so a flat list of leaves
    compares as the nested one does, and ``exact`` finds a value of other dimensions equal to
    no row of the column's. Under an ``in`` whose members are whole array values
    (``members_are_arrays``: the column's own ``in`` is Django's ``ArrayInLookup``, flat or
    nested) each member is one value of the column, held to its ``depth``, the levels Django's
    ``ArrayField.get_db_prep_value`` walks before it hands an element to the innermost column:
    a member, and each element of it above the innermost level, is descended when it is a list
    or tuple, and any other one, a member that is ``None`` included, is the field's error with
    ``MultipleChoiceField``'s ``invalid_list`` message (a member is never a leaf, since
    ``ArrayInLookup`` turns each member into a tuple); each element at the innermost level, a
    list included, is ``element_field``'s to clean, as Django's own form field cleans any
    value, since Django hands it to that column's ``get_prep_value``: a numeric leaf refuses a
    list with its ``invalid`` error and a text leaf reads it as text (``CharField.to_python``).
    The value is read on the parent's model, or, for a path its model names no field for,
    over the queryset the parent was handed (``_bound_value_field``: a queryset annotation
    or alias, a ``FilteredRelation`` alias and the columns past it, each typed ``String``
    on the wire, since no queryset exists when the schema is built); a path only the queryset
    the package ``FilterSet``'s own ``filter_queryset`` passes on resolves gets its
    ``element_field`` there and is cleaned again
    (``filters/sets.py::FilterSet._clean_late_comparisons``).
    Any other ``None`` element, one inside such a member included, stays ``None``, and a
    value that is not a list or tuple, or a field with no ``element_field`` (a filter bound
    to no ``FilterSet``, a path neither its model nor that queryset resolves, an expression
    with no output field, a relation compared on more than one column or on none, a
    crossing pair on a filter holding a ``filter`` of its own, a ``method=`` filter on a
    relation, a column django-filter builds no filter for), passes through as sent for the
    filter to judge. Under a lookup that is Django's ``Range`` (``bounds``) a non-empty list
    of other than two members is the field's error, django-filter's ``BaseRangeField`` rule,
    message and code (``invalid_values``); an empty list keeps the filter's meaning.

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
        depth: int = 0,
        members_are_arrays: bool = False,
        **kwargs: Unpack[_FieldOptions],
    ) -> None:
        super().__init__(**kwargs)
        self.element_field: Field | None = element_field
        self.depth: int = depth
        self.members_are_arrays: bool = members_are_arrays
        self.bounds: bool = False

    @override
    def to_python(self, value: object) -> object:
        """Clean each element with ``element_field``; anything else passes through."""
        element_field = self.element_field
        if element_field is None or not is_list_or_tuple(value):
            return value
        if self.members_are_arrays:
            return [
                self._cleaned(element_field, _array_value(member), self.depth - 1)
                for member in value
            ]
        return self._cleaned(element_field, value, None if self.depth > 1 else 0)

    @override
    def validate(self, value: object) -> None:
        """Refuse a non-empty list of other than two bounds when the lookup is a ``range``.

        django-filter's ``BaseRangeField.clean`` rule, message and code: Django's ``Range``
        reads exactly two members, so one would raise an ``IndexError`` and three a
        ``TypeError`` past the form. An empty list keeps the filter's own meaning.
        """
        super().validate(value)
        if self.bounds and is_list_or_tuple(value) and value and len(value) != _RANGE_BOUNDS:
            raise ValidationError(
                BaseRangeField.default_error_messages["invalid_values"],
                code="invalid_values",
            )

    def _cleaned(
        self,
        element_field: Field,
        elements: list[object] | tuple[object, ...],
        below: int | None,
    ) -> list[object]:
        """Return ``elements`` cleaned, each holding ``below`` list levels (``None``: any number).

        An element at a level that holds lists is one array (``_array_value``); one at the
        leaf level is ``element_field``'s to clean, a list included.
        """
        return [
            None
            if element is None
            else self._cleaned(element_field, element, None)
            if below is None and is_list_or_tuple(element)
            else self._cleaned(element_field, _array_value(element), below - 1)
            if below
            else element_field.clean(element)
            for element in elements
        ]


def _array_value(member: object) -> list[object] | tuple[object, ...]:
    """Return ``member``, an array value or one of its rows; anything else is ``invalid_list``.

    The message is Django's own for a value that is no list (``MultipleChoiceField``).
    """
    if is_list_or_tuple(member):
        return member
    raise ValidationError(
        MultipleChoiceField.default_error_messages["invalid_list"],
        code="invalid_list",
    )


class _ElementCleanedFilter(_ColumnCleanedFilter):
    """``ListFilter`` / ``ArrayFilter`` half: each element is cleaned as ``gte`` cleans one."""

    field_class: type[Field] = _ElementField

    @override
    def _hand_column_field(self, field: Field, query: Query | None = None, /) -> None:
        """Fill only a missing comparison cleaner on an owned ``_ElementField``."""
        if isinstance(field, _ElementField) and field.element_field is None:
            operand = _bound_lookup_operand(self, query)
            lookup = operand.lookup
            field.element_field = _column_form_field(self, element=True, query=query)
            field.depth = array_leaf_field(operand.field)[1]
            field.members_are_arrays = is_array_in_lookup(lookup)
            field.bounds = truth.is_subclass(lookup, models.lookups.Range)


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

    Each element is cleaned by the form field of the ``gte`` filter for the value it
    compares, the column's or a transform output's, an ``ArrayField`` column's innermost
    ``base_field``'s, a relation's key column's (``_ElementField``), so an element that value
    cannot hold is a form error rather than a value handed to the ORM, a text element is
    stripped and a naive datetime element made aware; over a path only the queryset its
    ``FilterSet`` was handed resolves (a queryset annotation, a ``FilteredRelation`` alias)
    the value is the one that queryset compares, and over one only the queryset the package
    ``FilterSet``'s own ``filter_queryset`` passes on resolves, the one that queryset
    compares (``filters/sets.py::FilterSet._clean_late_comparisons``). An ``in`` over an
    integer column, or a
    relation compared on one, drops each element that names no row as ``ListFilter``'s does
    (``_integer_in_column``). An element of an integer column, a transform's integer output
    or an integer ``ArrayField``'s elements cleaned to a decimal past that column's range on
    the queryset's database is applied as the integer one past the same end
    (``_held_column_value``), whose verdict is the decimal's and whose conversion is
    immediate. An element over a duration column the queryset's database cannot bind (on
    SQLite and MySQL, one whose microsecond count lies past 64 bits) is refused by the bind
    ask as ``ListFilter``'s is, raw drivers included. Raw form data (``DjangoFilterBackend``,
    a ``QueryDict``) reads ``?name=a,b`` as ``["a", "b"]`` and an empty ``?name=`` as no
    constraint (``_MembershipCSVWidget``); only a list or tuple is an explicit ``[]``.
    Its lookup takes the list as ``ListFilter``'s does (``refuse_listless_lookup``): over an
    ``ArrayField`` column the input build admits ``exact``, ``contains``, ``contained_by``
    and ``overlap``; a transform's output that is no array (``len``, an index) is refused
    with any lookup comparing one value.
    """

    # basedpyright: the stub declares ``Filter.method`` a plain attribute, not the property it is
    @_FILTER_METHOD_PROPERTY.setter
    @override
    def method(self, value: object) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Swap in `ArrayFilterMethod` when a consumer `method=` is set."""
        _install_empty_list_aware_method(self, value, ArrayFilterMethod)

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply the lookup; `[]` is a real value (not `EMPTY_VALUES`-ish).

        An ``in`` over an integer column, or a relation compared on one
        (``_integer_in_column``), keeps only the elements that can name a row, those inside
        the column's integer range on the queryset's database and not fractional
        (``_identifying_members``); a list with none left matches nothing, or every row
        under ``exclude``. Every other value goes to django-filter's own ``Filter.filter``.
        The ``value == []`` comparison runs the value's own ``__eq__``; whatever it
        raises propagates.
        """
        if value == []:
            return _apply_lookup_predicate(self, qs, value)
        value = _held_column_value(self, qs, value)
        column = _integer_in_column(self, qs.query)
        if column is not None and is_list_or_tuple(value):
            kept = _identifying_members(column, list(value), qs.db)
            if not kept:
                return _match_none_queryset(self, qs)
            return super().filter(qs, kept)
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
    form field of the ``gte`` filter for the value its range compares, the column's or a
    transform output's), so a bound that value cannot hold is a form error rather than a
    value handed to the ORM. Without one the bounds pass through as sent; over a path only
    the queryset the package ``FilterSet``'s own ``filter_queryset`` passes on resolves, the
    set gives the field its ``bound_field`` there and cleans the bounds again
    (``filters/sets.py::FilterSet._clean_late_comparisons``).
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
                one the ``gte`` filter for the value its range compares builds), or ``None``.
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

    The declared ``lookup_expr`` names the published input key (``exact`` for the default,
    ``range``, a bare ``date``) and the transforms the bounds compare through; its final
    lookup is never applied. Two bounds compare as a range whatever that lookup is
    (``<field>__range``, ``BETWEEN``), as django-filter's ``RangeFilter.filter`` replaces
    its ``lookup_expr`` with ``range``; over an integer column they apply as
    ``<field>__gte`` and ``<field>__lte`` in one predicate, as the generated ``range`` does
    (``IntegerRangeFilter``): Django's range-aware integer lookups read a bound past the
    column's range as widening or matching nothing, where ``BETWEEN`` would bind it raw and
    overflow the backend. A range with one bound left out or ``null`` applies that lone
    bound: a start alone as ``<field>__gte``, an end alone as ``<field>__lte``. Both shapes
    compare through every transform Django's query applies ahead of the lookup
    (``year__exact``, ``year__range`` and a bare ``year`` all compare ``<field>__year``,
    two bounds as ``<field>__year__range``), the value each bound is cleaned as; django-filter
    applies ``range`` / ``gte`` / ``lte`` on its ``field_name`` alone, dropping a
    ``lookup_expr`` transform and comparing the bare column. A range with neither bound
    constrains nothing.

    Each bound is cleaned by the form field of the ``gte`` filter for the value the range
    compares (``_column_form_field``): the column's, or the output's of the transforms between
    it and the lookup (``year``'s ``IntegerField``, ``date``'s ``DateField``), so a bound that
    value cannot hold (a non-finite decimal, a number past django-filter's ``1e50`` cap) is a
    form error as it is on ``gte``, a naive datetime bound is made aware and a text bound
    stripped; a bound off a choice column's choices is compared like any other value. Over a
    path only the queryset its ``FilterSet`` was handed resolves (a queryset annotation, a
    ``FilteredRelation`` alias and the columns past it) the value is the one that queryset
    compares, and an integer annotation's ``range`` applies as ``gte`` + ``lte`` as an integer
    column's does; over one only the queryset the package ``FilterSet``'s own
    ``filter_queryset`` passes on resolves (a consumer override annotating before it calls
    ``super()``), each bound is cleaned as that queryset compares it, there
    (``filters/sets.py::FilterSet._clean_late_comparisons``). A relation's lone bound under
    a lookup Django applies to the relation itself (``gte``, ``exact``) is cleaned as the
    target column the relation compares on (its
    ``to_field``, else the primary key), as ``<relation>__<that column>``'s is
    (``_compared_value_column``); a ``range`` over a relation, or a ``method=`` filter on one,
    cleans no bound, since Django registers no ``range`` lookup on a relation and a method
    applies no lookup of the filter's. A bound of an integer column (or a transform's integer
    output, or a relation's integer key column) cleaned to a decimal past that column's range
    on the queryset's database applies as the integer one past the same end
    (``_held_column_value``): Django's range-aware lookups read it as the decimal, never
    converting a decimal whose ``int()`` takes seconds (``-1e1000000``).
    """

    field_class: type[RangeField] = RangeField

    @override
    def _hand_column_field(self, field: Field, query: Query | None = None, /) -> None:
        """Fill only a missing bound cleaner on an owned ``RangeField``."""
        if isinstance(field, RangeField) and field.bound_field is None:
            field.bound_field = _column_form_field(self, query=query)

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Apply a lone bound as ``gte`` / ``lte``, two bounds as ``range`` (integer: ``gte`` + ``lte``).

        The declared lookup's final part is replaced as django-filter's ``RangeFilter.filter``
        replaces it; every transform Django's query applies ahead of it stays on the path
        (``_lookup_lhs_path``: ``year__exact``, ``year__range`` and a bare ``year`` all compare
        ``year``). A range input with one bound left out (or ``null``) reaches here as
        ``[start, None]`` / ``[None, end]`` and applies that bound alone as ``gte`` / ``lte``,
        since ``BETWEEN x AND NULL`` matches no row. ``[None, None]`` returns ``qs`` unchanged.
        Two bounds apply as ``range``; over an integer column (no transform between it and the
        lookup) as ``gte`` + ``lte`` in one predicate (``IntegerRangeFilter.filter``), so a
        bound past the column's range never reaches the backend. A relation itself (raw form
        data; GraphQL publishes no range over one) is compared on the column its values are
        compared on (``_compared_value_column``: its ``to_field``, else the target's primary
        key), so both shapes apply the compared column's ``gte`` / ``lte`` (two integer bounds
        as its ``gte`` + ``lte``) and a held bound past it widens or matches nothing, where
        the relation's own lookups would bind it raw and Django registers no ``range`` on
        a relation. Every shape goes through
        `_apply_lookups` (``distinct`` and ``exclude`` honoured). A lone bound, the ``range``
        and the ``gte`` + ``lte`` pair name the column the path resolves to
        (``_ResolvedField.path``), so over a relation-valued primary key they apply the stored
        column's lookups, never the relation's, which bind a bound past the column raw or,
        for ``range``, which Django refuses on the relation itself.
        A scoped terminal's synthetic parent has no queryset, so a path it cannot resolve
        is read from ``qs.query`` before deciding whether the two-bound integer rewrite
        applies. The same actual query owns the integer holding before that decision.
        """
        if not (is_list_or_tuple(value) and len(value) == _RANGE_BOUNDS):
            return super().filter(qs, value)
        value = require(_held_column_value(self, qs, value), is_list_or_tuple)
        start, end = value
        if start is None and end is None:
            return qs
        resolved = _bound_resolved_field(self)
        field_name, lookup_expr = _bound_field_name(self), _bound_lookup_expr(self)
        if (resolved is None or resolved.field is None) and (
            actual_field := _query_path_field(qs.query, field_name)
        ) is not None:
            resolved = _ResolvedField(actual_field, field_name)
        path = field_name if resolved is None else resolved.path
        field = None if resolved is None else resolved.field
        # A relation compares the column its values are compared on, holding past it.
        if (
            field is not None
            and field.is_relation
            and (column := _compared_value_column(self, field)) is not None
        ):
            path, field = LOOKUP_SEP.join((path, column.name)), column
        # Every transform ahead of the declared lookup stays (the value each bound is
        # cleaned as); the lookup itself gives way to ``gte`` / ``lte`` / ``range``.
        bound_path = _lookup_lhs_path(qs.query, LOOKUP_SEP.join((path, lookup_expr)))
        if end is None:
            return _apply_lookups(self, qs, {f"{bound_path}__gte": start})
        if start is None:
            return _apply_lookups(self, qs, {f"{bound_path}__lte": end})
        if bound_path == path and isinstance(field, models.IntegerField):
            return _apply_lookups(self, qs, {f"{path}__gte": start, f"{path}__lte": end})
        return _apply_lookups(self, qs, {f"{bound_path}__range": (start, end)})


def _integer_in_column(filter_instance: Filter, query: Query) -> ModelField | None:
    """Return the integer column a per-request filter's ``in`` compares its members on, else ``None``.

    The column the path names, a relation's the target column it compares on, its
    ``to_field``, else the primary key (``_compared_value_column``), so
    ``field_name="tag"`` keeps the members ``<relation>__<that column>`` keeps
    (``_identifying_members``). A queryset-only ``F`` or ``Count`` alias names
    an ordinary integer output and keeps this rule. A true integer ``Transform``
    in the actual query does not name a stored integer column: its complete
    member list must reach the form's bind ask. ``None`` for any other lookup,
    a non-integer column, or a path naming no field.
    """
    if _bound_lookup_expr(filter_instance) != "in":
        return None
    if _reads_integer_transform(filter_instance, query):
        return None
    model_field = _bound_model_field(filter_instance)
    if model_field is None:
        model_field = _query_path_field(query, _bound_field_name(filter_instance))
    column = None if model_field is None else _compared_value_column(filter_instance, model_field)
    return column if isinstance(column, models.IntegerField) else None


def _django_prepares(lookup: type[models.lookups.Lookup] | None) -> bool:
    """Whether ``lookup`` is one of Django's own and prepares its value through its field.

    Django's ``Lookup.prepare_rhs`` (``IExact``, the text patterns, ``Regex`` and
    ``IsNull`` leave it false and never convert the value), on a class Django itself
    defines (``utils/truth.py::module``): only Django's own comparisons read no more of a
    number than which side of the column's range it lies on, so a project lookup (one a
    ``register_lookup`` adds, ``prepare_rhs`` true by default) receives the value its form
    cleaned, as a ``method=`` filter does.
    """
    return (
        lookup is not None
        and lookup.prepare_rhs
        and truth.module(lookup).partition(".")[0] == "django"
    )


def _integer_compared_column(
    filter_instance: Filter,
    query: Query | None = None,
) -> ModelField | None:
    """Return the integer column whose ``int()`` each number a bound filter compares runs, else ``None``.

    The column a value is cleaned as (``_column_form_field``): the field each value is a
    value of (``_bound_value_field``: the column, or an integer transform's output such as
    ``year``'s or ``len``'s), a relation's the target column it compares on
    (``_compared_value_column``), an ``ArrayField``'s its innermost element column
    (``utils/_array_field.py::array_leaf_field``), where the lookup the filter applies is
    Django's own and prepares its value through that field (``_django_prepares``): the one it
    resolves, or for a ``RangeFilter``, which replaces its declared lookup with ``gte`` /
    ``lte`` / ``range`` (``RangeFilter.filter``), those. ``None`` where it does not
    (``iexact``, a text pattern, ``regex``, ``isnull``: Django hands the value on as it is;
    a project lookup, which owns what its value means), where no walk resolved one, and
    where that is no ``IntegerField`` or no one column (a filter bound to no
    ``FilterSet``, a path naming no field). The actual ``query`` is read for a
    scoped terminal whose synthetic parent has no queryset of its own.
    """
    operand = (
        _query_lookup_operand(
            query,
            _bound_field_name(filter_instance),
            _bound_lookup_expr(filter_instance),
        )
        if query is not None
        else _bound_lookup_operand(filter_instance)
    )
    if (
        operand is None
        or operand.field is None
        or not (isinstance(filter_instance, RangeFilter) or _django_prepares(operand.lookup))
    ):
        return None
    column = _compared_value_column(filter_instance, operand.field)
    if column is None:
        return None
    leaf, _depth = array_leaf_field(column)
    return leaf if isinstance(leaf, models.IntegerField) else None


def _held_column_value(filter_instance: Filter, qs: models.QuerySet[_M], value: object) -> object:
    """Return ``value`` held to its integer column's range on the database ``qs`` runs on.

    Each ``Decimal`` past the range of the integer column whose ``int()`` the filter's
    lookup runs (``_integer_compared_column``) becomes the integer one past the same end
    (``utils/errors.py::held_past_integer_range``), so the package's own filter classes
    never hand Django a decimal whose ``int()`` takes seconds, under any django-filter
    ``FilterSet`` parent; ``value`` as it is for any other column.
    """
    column = _integer_compared_column(filter_instance, qs.query)
    if column is None:
        return value
    return held_past_integer_range(connections[qs.db], column, value)


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

    Its lookup takes the list: ``in``, ``range`` (exactly two bounds, else the form's
    ``invalid_values`` error), a transform ending in either (``year__in``), ``has_keys`` /
    ``has_any_keys``, a ``JSONField``'s, ``RangeField``'s or ``CompositePrimaryKey``'s own
    comparisons, or anything over an ``ArrayField`` the input build admits; a column whose
    field class is project or third-party code is not judged. A set publishing one whose
    Django lookup compares one value (django-filter's default ``exact``, ``gte``,
    ``icontains``, ``isnull``, ``year``) refuses it (``refuse_listless_lookup``); a
    ``method=`` filter receives the list whatever its ``lookup_expr``.

    Same contract as `graphene_django/filter/filters/list_filter.py::ListFilter`:
    an empty list short-circuits to `qs.none()` (or a new queryset over every
    row when `exclude=True`) instead of being normalized into a "no value
    supplied" pass-through. Each element is cleaned by the form field of the ``gte``
    filter for the value it compares, the column's or the output's of the transforms
    between it and the lookup (``year__in``'s ``IntegerField``; ``_ElementField``), a
    relation's the target column Django compares it on, its ``to_field``, else the primary
    key (``field_name="tag"`` cleans as ``<relation>__<that column>``), as the generated
    ``in`` cleans its members, never by a row lookup, so an element that value cannot hold
    is a form error rather than a value handed to the ORM, a text element is stripped and a
    naive datetime element made aware; an element off a choice column's choices is a value
    like any other. Over a path only the queryset its ``FilterSet`` was handed resolves (a
    queryset annotation, a ``FilteredRelation`` alias and the columns past it) the value is
    the one that queryset compares: its annotation's output field, the column past the
    alias, the alias's target key, an integer one dropping as a column's does; over one
    only the queryset the package ``FilterSet``'s own ``filter_queryset`` passes on resolves
    (a consumer override annotating before it calls ``super()``), the one that queryset
    compares, cleaned there (``filters/sets.py::FilterSet._clean_late_comparisons``).
    Over an integer column, or a relation compared on one, an ``in`` drops each element
    outside the column's integer range on the queryset's database: it can identify no row,
    and bound raw it would overflow the backend. A fractional element names no row and is
    dropped too, never truncated to an integer. A decimal element past that range, or past
    the range of an integer transform's output the filter compares, is held to the integer
    one past the same end before it is read (``_held_column_value``), so it is dropped or
    compared without its ``int()`` running. A list whose every element drops matches
    nothing (every row when excluding). An element over a duration column the queryset's
    database cannot bind (on SQLite and MySQL, one whose microsecond count lies past 64
    bits) is refused instead, as the generated ``in`` refuses it: under the package's
    ``FilterSet`` the bind ask is part of the form's clean
    (``filters/form_binding.py::BindAskingFilterForm``), so raw drivers see the refusal as
    a form error too. The column's own validators are not applied, so an element they
    would refuse still matches a row that holds it. Raw form data
    (``DjangoFilterBackend``, a ``QueryDict``) reads as the generated ``in`` reads it
    (``_MembershipCSVWidget``): ``?name=a,b`` is ``["a", "b"]`` and an empty ``?name=``
    applies no constraint.
    """

    # basedpyright: the stub declares ``Filter.method`` a plain attribute, not the property it is
    @_FILTER_METHOD_PROPERTY.setter
    @override
    def method(self, value: object) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
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
        a coded reject. An ``in`` over an integer column, or a relation compared on one
        (``_integer_in_column``), then keeps only the elements naming a row, those inside
        the column's integer range on the queryset's database and not fractional
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
        value = require(_held_column_value(self, qs, value), is_list)
        column = _integer_in_column(self, qs.query)
        if column is not None:
            kept = _identifying_members(column, value, qs.db)
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
      `Decimal`) names no row and is dropped, never truncated to an integer. A decimal
      member past the range reaches here already held by the filter set to the integer
      one past the same end (`filters/sets.py::_held_integer_value`), so it drops without
      its `int()` ever running. The column's own validators are not run, so a member they
      would refuse still matches a row that holds it, as `exact` matches it.
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
        if _reads_integer_transform(self, qs.query):
            # A transform's output names no stored column: each member binds as the
            # lookup prepares it, so one past the integer range the database stores for
            # the output is refused by the filter form's bind ask, never dropped. A
            # fractional member equals no integer output and is dropped.
            operand = _query_lookup_operand(
                qs.query,
                _bound_field_name(self),
                _bound_lookup_expr(self),
            )
            output = None if operand is None else operand.field
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
    ``BETWEEN`` would express if the backend could bind the value. A decimal bound past the
    range reaches here already held by the filter set to the integer one past the same end
    (``filters/sets.py::_held_integer_value``), which the lookups read as the decimal
    without converting it.

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
    when it carries the primary key. ``foreign_rows`` is whether the rows the filter
    runs over answer for a type other than ``definition`` (an undeclared hop's face
    re-entering the table of the type the walking set is bound to, or a copy carrying its
    leaf as declared, ``_key_leaf_of``, over a face or set whose rows another type scopes,
    ``_rows_definition``), so, as across a relation, an id slot only ``definition``'s own
    ``get_queryset`` annotates is not on them.
    """

    definition: DjangoTypeDefinition
    row_path: str
    slot: _OffPkIdSlot | None
    foreign_rows: bool = False


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


def _globalid_target(
    filter_instance: Filter,
    *,
    stable: bool = False,
    aliases: Mapping[str, str] = _NO_ALIASES,
) -> _GlobalIDTarget | None:
    """Resolve where a GlobalID-aware filter validates and compiles its node id.

    Reads the owner of the filter's runtime ``parent``: a filter set instance's class's
    own binding (``utils/permissions.py::set_bound_definition``, which the finalizer's
    phase 2.5 wires, spec-027 #"Bind the owner."), or, for an undeclared hop's face,
    the type registered for the face's model (``registry.get``), as the unwalked
    relation's leaf resolves it (``related_target_for``), whichever type the face's
    rows answer for (a leaf ending on a re-entry's primary key names the relation's
    target type, never the type the walking set is bound to; ``foreign_rows`` records
    that the two differ), and resolves the LIVE ``field_name`` (a leaf
    ``_expand_related_filter`` rebased resolves its rebased path). A path starting at a
    ``FilteredRelation`` alias of ``aliases`` (those of the queryset the filter is
    applied to, ``_query_aliases``; a re-bound copy reads its ``_KeyLeaf``'s) resolves
    as the relations the alias joins (``_resolve_globalid_target``), so it validates as
    the same filter over that relation does; with none at hand (the build's ask) it
    resolves nothing. Rows no definition answers for resolve from their model once the
    registry is stable (``registry.is_finalized()``, or ``stable``: the finalizer's
    build-time audit asks once every type is collected and its strategy stamped,
    ``types/finalizer.py::_audit_globalid_filter_strategies``, so the build resolves
    the definition a request resolves): an unbound set instance (a ``RelatedFilter``
    target no ``DjangoType`` wires, a subclass of a wired set included) from its
    model's registry primary (``registry.get``), the type its relation leaves are
    generated from, for the relation branch only (its own key, nested or as a hop's
    flat copy of it, keeps the upstream scalar shape, so it is never validated as that
    primary's GlobalID); an unbound set over a model no type exposes, and an undeclared
    hop's face into one, walk from that model (``_resolve_globalid_target``'s
    ``start_model``). A relation key's copy re-bound to the target's key over the
    target rows, and a copy of a leaf another set declares ending on the target's
    primary key past a declared hop into a set no type wires (``_key_leaf_of``, both),
    resolves the definition and id slot its leaf as declared resolves, with an empty
    row path (the copy compares those rows' own columns), whichever type the face or
    set it is bound to answers for, so every decode of one relation names one type; its
    rows are foreign when a type other than that definition answers for them
    (``_rows_definition``). Two routing branches:

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
    before the registry is stable), for an unbound set's own key (never a leaf
    another set declares that a declared hop carries onto it), or when
    the lookup cannot resolve a target; the filter then decodes the GlobalID
    without type-name validation
    (the node-id-only fallback, spec-031 Decision 13; a relation's node id is still
    coerced through the column its path names, ``_unresolved_target_node_id``) and compiles on
    its own ``field_name``. The resolution of WHICH definition (own-PK vs relation)
    stays single-sited in ``_resolve_globalid_target`` so the strategy-aware
    acceptance check in ``_decode_and_validate_global_id`` consumes a single
    definition (spec-031 Decision 13).
    """
    key_leaf = _key_leaf_of(filter_instance)
    if key_leaf is not None:
        declared = _globalid_target(key_leaf.leaf, stable=stable, aliases=key_leaf.aliases)
        if declared is None:
            return None
        # The copy compares the rows its face answers for: another type's rows carry no
        # annotation only ``declared.definition``'s ``get_queryset`` adds.
        rows_definition = _rows_definition(getattr(filter_instance, "parent", None))
        return replace(
            declared,
            row_path="",
            foreign_rows=rows_definition is not declared.definition,
        )
    parent: object = getattr(filter_instance, "parent", None)
    # An undeclared hop's face (``filters/sets.py::_UndeclaredHopSet``) carries the
    # definition its rows answer for on itself; a filter set instance answers for its
    # class's own binding.
    face = truth.instance_dict(parent) or {}
    relation_only = False
    foreign_rows = False
    if "_owner_definition" in face:
        # A face's ids name the type registered for its model, as the unwalked relation's
        # leaf names them (``related_target_for``), whichever type answers for its rows.
        face_meta = require_instance(face["_meta"], FilterSetOptions)
        owner = registry.get_definition(registry.get(require(face_meta.model, is_model_class)))
        foreign_rows = owner is not _rows_definition(parent)
    else:
        owner = set_bound_definition(truth.class_of(parent))
        relation_only = owner is None
    if owner is not None:
        start_model = owner.model
    else:
        # Rows no definition answers for (an unbound set, an undeclared hop into a model no
        # type exposes) still carry relation leaves generated from the registry primary of
        # their relation's model, so they validate from that primary once the registry is
        # stable; an unbound set's own key stays the upstream scalar shape, never a
        # GlobalID of its model's primary.
        meta = optional_instance(truth.static_attr(parent, "_meta", None), FilterSetOptions)
        model = getattr(meta, "model", None)
        if not (stable or registry.is_finalized()) or not is_model_class(model):
            return None
        start_model = model
        if relation_only:
            owner = registry.get_definition(registry.get(model))
    view = _relation_view_of(filter_instance)
    field_name = (
        None
        if getattr(filter_instance, "field_name", None) is None
        else _bound_field_name(filter_instance)
        if view is None
        else view.path
    )
    resolved = _resolve_globalid_target(
        owner,
        start_model,
        field_name,
        stable=stable,
        aliases=aliases,
    )
    if resolved is None:
        return None
    definition, row_path = resolved
    if relation_only and not row_path:
        return None
    return _GlobalIDTarget(definition, row_path, _off_pk_id_slot(definition), foreign_rows)


def _rows_definition(parent: object) -> DjangoTypeDefinition | None:
    """Return the definition of the type whose ``get_queryset`` scoped the rows ``parent`` filters.

    An undeclared hop's face carries it (``_owner_definition``); a filter set instance's
    rows answer for its class's binding, else for its model's registry primary, the type
    ``FilterSet._target_type_for_related_filter`` scopes an unbound branch by.
    """
    face = truth.instance_dict(parent) or {}
    if "_owner_definition" in face:
        return optional_instance(face["_owner_definition"], DjangoTypeDefinition)
    bound = set_bound_definition(truth.class_of(parent))
    if bound is not None:
        return bound
    meta = require_instance(truth.static_attr(parent, "_meta", None), FilterSetOptions)
    return registry.get_definition(registry.get(require(meta.model, is_model_class)))


def _compares_target_annotation(
    filter_instance: Filter,
    aliases: Mapping[str, str] = _NO_ALIASES,
) -> bool:
    """Whether a GlobalID ``filter_instance``'s target carries its id in an annotation.

    A ``relay.NodeID`` over an attribute no model column holds (``_OffPkIdSlot.field``
    is ``None``) exists only on the rows the target type's ``get_queryset`` returns.
    ``aliases`` are those of the rows the leaf runs over (``_globalid_target``).
    """
    target = _globalid_target(filter_instance, stable=True, aliases=aliases)
    return target is not None and target.slot is not None and target.slot.field is None


def _resolve_globalid_target(
    owner: DjangoTypeDefinition | None,
    start_model: type[models.Model],
    field_name: str | None,
    *,
    stable: bool = False,
    aliases: Mapping[str, str] = _NO_ALIASES,
) -> tuple[DjangoTypeDefinition, str] | None:
    """Resolve ``field_name`` from ``owner`` to ``(target definition, row path)``.

    The walk behind ``_globalid_target``: the row path is the prefix of ``field_name``
    that reaches the target's rows, every segment before a terminal scalar primary key
    (``""`` for the owner's own id), or the whole path when it ends on a relation. It
    comes from the walk, never from trimming ``field_name``: a relation may be named
    like the target's primary key. A ``"pk"`` segment names the current model's primary
    key: a scalar primary key is the current definition's own Relay id and ends the
    path, and one that is itself a relation (``OneToOneField(primary_key=True)``, an MTI
    ``<parent>_ptr``) is walked like any other relation, as
    ``filters/sets.py::FilterSet._is_own_pk_under_relay_owner`` keeps a relation primary
    key out of the own-PK branch. A hop into a model no ``DjangoType`` exposes continues
    on that model, so the target is the terminal relation's ``registry.get`` exactly as
    generation types the leaf (a ``shelf__branch`` key with no ``Shelf`` type validates
    against ``Branch``'s); a primary key ending on such a model resolves nothing. The
    walk starts on ``start_model``: the owner's own model, or the model of rows no
    definition answers for when there is no ``owner``. Continuing past a hop no
    definition resolves waits for a stable registry: ``stable`` (the finalizer's
    build-time audit, which runs once every type is collected and its strategy stamped,
    before ``registry.is_finalized()`` flips) or a finalized registry; before either the
    walk ends at that hop, so a filter set applied before finalization reads such a leaf
    node-id-only. A first segment naming a ``FilteredRelation`` alias of ``aliases`` walks
    as the model relations the alias joins (``utils/permissions.py::alias_relation_path``,
    an alias over another alias read as that alias's relations), as Django reads it at the
    start of a path (``Query.names_to_path``); the row path keeps the alias, the spelling
    the queryset holding it resolves (``vshelf`` for ``vshelf``, ``vshelf`` for
    ``vshelf__id``).
    """
    if not isinstance(field_name, str) or not field_name:
        return None

    current_def: DjangoTypeDefinition | None = owner
    current_model = start_model
    segments = field_name.split("__")
    # A path starting at a ``FilteredRelation`` alias walks as the relations the alias
    # joins, as Django reads it there (``Query.names_to_path``); its row path keeps the
    # alias, the spelling the queryset holding it resolves.
    alias = segments[0] if segments[0] in aliases else None
    joined = 0
    if alias is not None:
        relations = alias_relation_path(alias, aliases).split(LOOKUP_SEP)
        joined = len(relations)
        segments = [*relations, *segments[1:]]

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
                row_path = segments[:i] if alias is None else [alias, *segments[joined:i]]
                return current_def, "__".join(row_path)
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
    child instance (``FilterSet._projection_child``), or from an undeclared hop's
    face (``filters/sets.py::_UndeclaredHopSet``) to the set walking it, to the
    instance that owns it, so the GlobalID type-name check validates against the
    names THIS schema published. ``None`` for a filterset built outside the apply
    pipeline (a direct public construction), where no schema exists to consult: its
    ``_apply_info`` is ``None`` or a ``_DirectRequestInfo``, which names none.
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
    query: Query | None = None,
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
    `effective_globalid_strategy` is `None` (an unfinalized or non-Relay
    target), is a fail-closed reject with a coded
    `GraphQLError(..., extensions={"code": "GLOBALID_UNVALIDATABLE"})`.
    `finalizer._audit_globalid_filter_strategies` refuses, during finalization,
    every leaf a wired filterset serves that decodes against an encode-only target;
    that runtime arm answers for a filterset no wired type serves and for a leaf whose
    path starts at a `FilteredRelation` alias, which the audit cannot see. A finalized
    non-Relay target has no recorded strategy and can reach the separate
    missing-strategy refusal through an ordinary request.
    A malformed wire string (unparseable base64 / not a
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
    relation linked by more than one column, answers ``GLOBALID_INVALID``. The path is
    the one Django walks (``_bound_field_name``), so a ``lookup_expr`` continuing it to a
    column coerces through that column; a path the model names no field for is read over
    ``query``, the queryset the filter is applied to, which holds a ``FilteredRelation``
    alias wherever it was added (a ``filter_queryset`` override included). A filter whose
    path names no model field (no FilterSet model, no field on it), or whose lookup applies
    a transform, passes the decoded node id through. ``target``
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
            # Fail closed: the target emits GlobalIDs a filter input cannot
            # decode + validate. ``callable`` / ``custom`` are encode-only; a
            # ``None`` strategy on a known definition means the type was never
            # finalized as a Relay node. The encode-only audit refuses callable
            # and custom targets of every leaf a wired set serves during
            # finalization; their runtime arm answers for a set no wired type
            # serves and for a leaf whose path starts at a ``FilteredRelation``
            # alias. A finalized non-Relay target can reach this refusal through
            # an ordinary request because the audit admits it.
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
        and (target.row_path or target.foreign_rows)
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
        field = _bound_model_field(filter_instance, query)
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
    ``GLOBALID_INVALID`` too. ``field`` and the lookup are the walk's
    (``_bound_lookup_expr``), so ``lookup_expr="code"`` past a relation is ``exact`` on
    ``code``; a lookup ``field`` does not register (a transform applied ahead of it)
    compares another column and passes the node id through unchanged. A relation linked by no
    column (a ``GenericForeignKey``) never reaches here: its set refused the filter when
    it published (``refuse_identityless_relation``). A ``GeneratedField``'s computed column answers its
    lookups from the registry Django's query resolves them on, its ``output_field``
    instance (``utils/relations.py::lookup_registry``, the generated field read back by
    ``generated_column_source``), so a lookup a project registers there is one it registers.
    """
    source = generated_column_source(field) if is_concrete_field(field) else None
    if lookup_registry(source or field).get_lookup(_bound_lookup_expr(filter_instance)) is None:
        return node_id
    columns = _compared_columns(filter_instance, field)
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
        view = _relation_view_of(filter_instance)
        # A relation-view copy's target is its relation's, whose rows it reads through the alias.
        row_path = target.row_path if view is None else view.alias
        return f"{row_path}__{id_attr}" if row_path else id_attr
    return _marked_pk_field_name(filter_instance)


class GlobalIDFilter(Filter):
    """Filter that decodes a Relay GlobalID before delegating to `Filter`.

    Same contract as `graphene_django/filter/filters/global_id_filter.py::GlobalIDFilter`
    with the decode substituted to `strawberry.relay.GlobalID.from_id(value)`
    per spec-027 Decision 4. The Graphene-only
    `GlobalIDFormField` / `GlobalIDMultipleChoiceField` dependencies drop
    away; the default `forms.Field` inherited through `django_filters.Filter.field_class`
    is used. Its cleaning passes the input through without CharField's text coercion.

    Accepts both raw `str` and `strawberry.relay.GlobalID` objects per
    spec-027 #"Accepts both raw". Validates the decoded `type_name` against the
    strategy-aware accepted set (resolved through the parent filterset's bound owner's
    `related_target_for(field_name)`, or the owner itself when the filter targets the
    own PK; a `field_name` starting at a `FilteredRelation` alias of the queryset it
    filters resolves as the relation the alias joins) per spec-031 Decision 13; a
    mismatch raises `GraphQLError("GlobalID type mismatch...")` before any queryset
    clause runs. The decoded node id is the value of the target type's id slot, its
    primary key or the column a consumer `relay.NodeID[...]` names, and is coerced and
    compared as that column, as `node(id:)` reads it.
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
        target = _globalid_target(self, aliases=_query_aliases(qs))
        node_id = _decode_and_validate_global_id(
            value,
            self,
            target=target,
            alias=qs.db,
            query=qs.query,
        )
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
        target = _globalid_target(self, aliases=_query_aliases(qs))
        node_ids = [
            _decode_and_validate_global_id(
                item,
                self,
                index=idx,
                target=target,
                alias=qs.db,
                query=qs.query,
            )
            for idx, item in enumerate(value)
        ]
        path = _globalid_predicate_path(self, target)
        lookup_expr = _bound_lookup_expr(self)
        if lookup_expr != "in":
            if path is None:
                return super().filter(qs, node_ids)
            # Upstream's per-element predicates read ``field_name`` and ``lookup_expr``; a copy
            # carries the path and the lookup applied where it ends.
            rebound = copy.copy(self)
            rebound.field_name = path
            rebound.lookup_expr = lookup_expr
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
    model = getattr(relation, "related_model", None)
    return _model_identity_column(model, None) if is_model_class(model) else None


def _model_identity_column(
    model: type[models.Model],
    to_field_name: str | None,
) -> ConcreteField | None:
    """Return the concrete column holding ``model``'s primary key, or its ``to_field_name``.

    The field is the one Django's ``ModelChoiceField`` looks a value up by,
    ``to_field_name or "pk"`` (``utils/relations.py::choice_key_field``). A
    relation-valued column (a multi-table-inheritance parent link, a one-to-one used as
    the key, a foreign key named as ``to_field_name``) is followed to the column that
    actually stores the value. ``None`` when ``to_field_name`` names no column of
    ``model``.
    """
    field = choice_key_field(model, to_field_name)
    return None if field is None else stored_value_column(field)


def model_choice_model(
    filterset: type[BaseFilterSet] | None,
    filter_instance: Filter,
) -> type[models.Model] | None:
    """Return the model a consumer ``ModelChoiceFilter`` family filter's form field looks values up in.

    A ``ModelChoiceFilter`` / ``ModelMultipleChoiceFilter`` the consumer declares on
    ``filterset`` (or selects through ``Meta.filter_overrides``) keeps django-filter's
    model-choice form field, which looks each value up in the filter's ``queryset`` by
    ``to_field_name`` (``_model_identity_column``): a model queryset's model. A callable
    ``queryset`` (``queryset=lambda request: ...``) names its model only once a request
    arrives, so the model is the one the filter's ``field_name`` path ends on over
    ``filterset``'s model (the path Django walks, ``_filterset_walked_lookup``, classified
    by ``utils/relations.py::_classify_path_cached``): the model its last relation
    reaches, ``filterset``'s model for a path crossing none. A path ending on Django's
    ``pk`` alias ends on the model the part before it reaches (``kiosk__pk`` on
    ``kiosk``'s target, a bare ``pk`` on ``filterset``'s model), as ``kiosk__id`` does. An
    unset ``queryset`` names a model only through a path ending on a relation, and a
    ``pk`` path ends on the column the key stores, never on a relation. ``None`` for a
    path the classifier refuses (a name naming no field, a queryset annotation, a
    ``GenericForeignKey``).
    """
    queryset = read_attr(filter_instance, "queryset", None)
    if queryset is not None and not callable(queryset):
        model = read_attr(queryset, "model", None)
        return model if is_model_class(model) else None
    model = _filterset_model(filterset)
    if model is None:
        return None
    walked = _filterset_walked_lookup(filterset, filter_instance)[0]
    prefix, _sep, last = walked.rpartition(LOOKUP_SEP)
    if last == "pk":
        # Django's ``pk`` alias is the primary key of the model the path before it
        # reaches, read as the column it stores (``_model_resolved_field``), never as the
        # parent link a multi-table-inheritance child's key is.
        if queryset is None:
            return None
        if not prefix:
            return model
        walked = prefix
    try:
        path = _classify_path_cached(model, walked)
    except PathResolutionError:
        return None
    if queryset is None and not relation_bool(path.terminal, "is_relation"):
        return None
    return path.hops[-1].target_model if path.hops else model


def _compared_columns(filter_instance: Filter, field: ModelField) -> tuple[ConcreteField, ...]:
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
    No column for a relation Django builds no join for (a ``GenericForeignKey``, whose
    target is no one model): no value compares on it, so a set holding a GlobalID or
    model-choice filter on one refuses it when it publishes
    (``refuse_identityless_relation``), and any other leaf running shipped code there
    (``filters/inputs.py::refuse_joinless_relation``).
    """
    marked = bool(getattr(filter_instance, _GLOBALID_RELATION_PK_ATTR, False))
    if isinstance(field, models.ForeignKey) or not field.is_relation:
        if field.is_relation and marked:
            column = relation_identity_column(field)
            return () if column is None else (column,)
        column = stored_value_column(field)
        return (column,) if isinstance(column, models.Field) else ()
    related = getattr(field, "related_model", None)
    if not is_model_class(related) or not isinstance(
        field,
        (models.ForeignObject, models.ManyToManyField, models.ForeignObjectRel),
    ):
        return ()
    targets = related._meta.pk_fields if marked else field.path_infos[-1].target_fields
    return tuple(stored_value_column(target) for target in targets)


def _compared_value_column(filter_instance: Filter, field: ModelField) -> ModelField | None:
    """Return the column one value ``filter_instance`` compares on ``field`` is a value of.

    A column answers itself. A relation whose lookup Django applies to the relation
    itself (``_filterset_lookup_lhs_path`` reads back the filter's own ``field_name``)
    answers the one column a value compared on it meets (``_compared_columns``), the
    target field Django's related lookups prepare the value through (``RelatedIn`` /
    ``RelatedLookupMixin``: the relation's ``path_infos[-1].target_fields[-1]``, its
    ``to_field``, else the target's primary key), so ``field_name="tag"`` reads its values
    as ``<relation>__<that column>`` does. The path and lookup are the ones Django walks
    (``_bound_field_name`` / ``_bound_lookup_expr``), so ``field_name="shelf",
    lookup_expr="branch__in"`` reads its values as ``shelf__branch`` + ``in`` does.
    ``None`` for a relation compared on more than one column or on none (a
    ``GenericForeignKey``), whose value no one column holds, for a lookup Django does not
    apply to the relation itself (``range``; a crossing pair on a filter holding a
    ``filter`` of its own, which reads its pair as declared, compares the crossed column,
    not the relation), and for a ``method=`` filter, whose method receives the value and
    applies no lookup of the filter's to the relation.
    """
    if not field.is_relation:
        return field
    if read_attr(filter_instance, "method", None) is not None:
        return None
    field_name = _bound_field_name(filter_instance)
    if _bound_lookup_lhs_path(filter_instance, field_name) != field_name:
        return None
    columns = _compared_columns(filter_instance, field)
    return columns[0] if len(columns) == 1 else None


def _coerce_relation_identity(filter_instance: Filter, value: object, alias: str) -> object:
    """Coerce one raw identity value through the target key column; ``None`` if it names no row.

    The column is the one ``_compared_columns`` reads off the filter's ORM path, so a
    key leaf compared through its relation and one compared on the target's key column
    across a visibility hop coerce alike. A value the column cannot hold (one the
    queryset's database ``alias`` cannot bind, out of the column's range there, wrong
    shape) identifies no row, the same verdict ``_identifying_members`` gives an integer
    ``in`` member; the column's own validators are not run, so a key they would refuse
    still matches a row that holds it. A relation linked by more than one column, or by
    none (``_compared_columns``), has no single column one value can name, so every value
    identifies no row. The relation is the field each value is compared as
    (``_bound_value_field``), the one ``filters/inputs.py::_relation_identity_annotation``
    types the input from: the path's own relation, or the relation a transform between
    the column and the lookup outputs, whose key the value names rather than the
    column's. A filter whose path names no such field (no model to walk, or nothing on
    it) has no column and passes the value through unchanged.
    """
    field = _bound_value_field(filter_instance)
    if field is None:
        return value
    columns = _compared_columns(filter_instance, field)
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
        qualifies the path with ``__pk`` exactly as on ``RelationPkFilter``. Everything the
        filter's path applies ahead of its lookup stays (``_membership_path``): a relation
        the ``lookup_expr`` continues across, and every transform
        (``<column>__<transform>__in`` for a transform whose output is a relation, a bare
        trailing ``<transform>`` too), so the members are compared with the value the
        transform computes, as they were coerced.
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
        path = _membership_path(self, qs.query)
        return _apply_lookups(self, qs, {f"{path}{LOOKUP_SEP}in": kept})


def _membership_path(filter_instance: Filter, query: Query) -> str:
    """Return the path a filter's predicate applies its lookup to, over the queryset's ``query``.

    The filter's path (its ``field_name``, or the non-pk ``to_field`` marker's ``__pk`` path,
    then its ``lookup_expr``) less its final lookup, split as ``Query.build_filter`` splits
    it (``utils/querysets.py::split_lookup``): every name Django walks as a path stays, a
    relation the ``lookup_expr`` continues across included, then each transform
    ``Query.build_lookup`` applies to where that walk ends
    (``utils/relations.py::lookup_transform_parts``), a final part that is no lookup there
    being a trailing transform with an implicit ``exact``. A path Django refuses raises its
    ``FieldError``.
    """
    path = LOOKUP_SEP.join(
        (
            _marked_pk_field_name(filter_instance) or _bound_field_name(filter_instance),
            _bound_lookup_expr(filter_instance),
        ),
    )
    return _lookup_lhs_path(query, path)


def _lookup_lhs_path(query: Query, lookup: str) -> str:
    """Return the path a filter argument ``lookup`` applies its final lookup to over ``query``.

    ``lookup`` less its final lookup, split as ``Query.build_filter`` splits it
    (``utils/querysets.py::split_lookup``): every name Django walks as a path stays, then
    each transform ``Query.build_lookup`` applies to where that walk ends
    (``utils/relations.py::lookup_transform_parts``), a final part that is no lookup there
    being a trailing transform with an implicit ``exact``. A path Django refuses raises its
    ``FieldError``.
    """
    head, start, lookups = split_lookup(query, lookup)
    # ``Query.build_lookup`` reads an empty leftover (a path ending on a field) as ``exact``.
    return LOOKUP_SEP.join(
        (*head, *lookup_transform_parts(start, LOOKUP_SEP.join(lookups) or "exact")),
    )


def refuse_identityless_relation(
    filterset_cls: type[BaseFilterSet],
    filter_name: str,
    filter_instance: Filter,
    *,
    shipped: bool,
) -> None:
    """Refuse a GlobalID or model-choice filter on a relation no row identity is compared on.

    A ``GlobalIDFilter`` / ``GlobalIDMultipleChoiceFilter`` with no resolvable target
    compares its node id on the columns ``_compared_columns`` reads off the relation its
    ``field_name`` names (``_unresolved_target_node_id``), and a ``ModelChoiceFilter`` /
    ``ModelMultipleChoiceFilter`` (a ``Meta.filter_overrides`` selection and
    django-filter's CSV wrapper around one included) compares there the row its
    ``queryset`` looks each value up in, whatever that ``queryset`` is. A relation Django
    builds no join for, a ``GenericForeignKey`` (a content type and an object id, no one
    target model), has none, and Django refuses a queryset filter through it with
    ``FieldError``, so the declaration could answer no request.
    ``filters/sets.py::FilterSet._publish_filters`` asks this of every leaf a set
    publishes: a set a type serves refuses it when the schema builds, an unserved set at
    its first use (its first construction, ``FilterSet.__init__``, or the package's first
    read of its table), and again at every construction until it is fixed. A path naming
    no field is not read here, and neither is a filter with a ``method``: django-filter
    dispatches it to that method, which filters as it chooses (the content type and
    object id columns, say), never through the relation its ``field_name`` names. A
    model-choice filter is asked only when its ``filter`` is ``shipped`` code
    (``filters/sets.py::_runs_shipped_filter``): a ``filter`` override of its own filters
    as it chooses too, while a GlobalID filter's override still holds the node-id
    comparison it would reach through ``super()``.
    """
    if not isinstance(filter_instance, (GlobalIDFilter, GlobalIDMultipleChoiceFilter)) and not (
        shipped and isinstance(filter_instance, (ModelChoiceFilter, ModelMultipleChoiceFilter))
    ):
        return
    if read_attr(filter_instance, "method", None) is not None:
        return
    field = _filterset_model_field(filterset_cls, filter_instance)
    if field is None or not field.is_relation or _compared_columns(filter_instance, field):
        return
    raise ConfigurationError(
        f"FilterSet {truth.qualname(filterset_cls)}: {truth.kind(filter_instance)} "
        f"{filter_name!r} has field_name {_declared_field_name(filter_instance)!r}, which names "
        f"{_field_label(field)}, a {truth.kind(field)}: Django filters no queryset through "
        "it, so no related row's identity can be compared on it. Filter through the "
        "GenericRelation that reverses it on the related model, or on the content type and "
        "object id columns it reads.",
    )


#: The packages whose form-field code the queryset ask trusts: Django's, django-filter's and
#: this one's.
_SHIPPED_FORM_PACKAGES = frozenset({"django", "django_filters", __name__.partition(".")[0]})


def _field_needs_a_queryset(field_class: object) -> bool:
    """Whether building ``field_class`` runs Django's ``ModelChoiceField.__init__`` with no queryset.

    Django's ``ModelChoiceField`` (and ``ModelMultipleChoiceField``, its subclass) takes its
    ``queryset`` as a required argument. Every ``__init__`` its real MRO defines before
    Django's one (``utils/truth.py::mro``, read through each class's own namespace) is
    shipped code that forwards the keyword arguments it is given (django-filter's
    ``ChoiceIteratorMixin`` and ``BaseCSVField``), so a filter supplying no queryset builds
    the field without one. A consumer ``__init__`` before it can supply one, and is trusted.
    """
    if not truth.is_subclass(field_class, ModelChoiceField):
        return False
    before = takewhile(lambda klass: klass is not ModelChoiceField, truth.mro(field_class))
    return all(
        truth.module(truth.stored_function(init)).partition(".")[0] in _SHIPPED_FORM_PACKAGES
        for klass in before
        if (init := truth.class_dict(klass).get("__init__")) is not None
    )


def refuse_querysetless_choice(
    filterset_cls: type[BaseFilterSet],
    filter_name: str,
    filter_instance: Filter,
) -> None:
    """Refuse a model-choice filter that can never build its form field: it has no queryset.

    django-filter's ``QuerySetRequestMixin.field`` passes the queryset ``get_queryset``
    answers to the form field, and its ``get_queryset`` answers the ``queryset=`` value (a
    callable called with the request). With no ``queryset=`` passed and no ``queryset`` key
    in ``extra`` (a ``Meta.filter_overrides`` entry's ``extra``), the form field is built
    without the queryset Django's ``ModelChoiceField`` requires: it raises ``TypeError`` on
    every request that builds the set's form. A ``queryset`` key in ``extra`` is a passed
    value, whatever it holds, and is not judged. Consumer code that can supply the queryset
    per request is trusted and not judged: a filter class overriding ``get_queryset`` or
    ``field`` (``utils/truth.py::overrides``; the package's ``RelatedFilter`` derives its
    target's), a form field class whose own ``__init__`` runs first
    (``_field_needs_a_queryset``), and a set overriding ``__init__``, ``get_form_class`` or
    ``form`` (the caller's ask, ``filters/sets.py::FilterSet._publish_filters``). A set a
    type serves refuses it when the schema builds, an unserved set at its first use, as
    ``refuse_identityless_relation``.
    """
    if not truth.is_instance(filter_instance, QuerySetRequestMixin):
        return
    if (
        read_attr(filter_instance, "queryset", None) is not None
        or "queryset" in dict_of(filter_instance.extra)
        or truth.overrides(
            truth.class_of(filter_instance),
            QuerySetRequestMixin,
            "get_queryset",
            "field",
        )
        or not _field_needs_a_queryset(read_attr(filter_instance, "field_class", None))
    ):
        return
    raise ConfigurationError(
        f"FilterSet {truth.qualname(filterset_cls)}: {truth.kind(filter_instance)} "
        f"{filter_name!r} has field_name {truth.text(_declared_field_name(filter_instance))!r} "
        "and no queryset, so the model-choice form field it builds has no rows to look a "
        "value up in, and every request building the set's form would fail. "
        "Pass queryset= (a model queryset, or a callable taking the request), override the "
        "filter's get_queryset(request), or give a Meta.filter_overrides entry an `extra` "
        'returning {"queryset": ...}.',
    )


#: The shipped filter classes whose ``filter`` applies a relation's ``range`` as the bounds
#: ``gte`` / ``lte`` on the path itself: both bounds (``IntegerRangeFilter.filter``), or a lone
#: one (django-filter's ``RangeFilter.filter`` sets ``self.lookup_expr`` to ``"gte"`` for a
#: lone ``start``, ``"lte"`` for a lone ``stop`` and ``"range"`` for both). The package's
#: ``RangeFilter`` is no subclass of django-filter's (its bases are ``TypedFilter`` and
#: ``Filter``) and reads a lone bound through the walk of its ``lookup_expr``, so it is
#: asked ``range`` as declared.
_BOUNDED_RANGE_FILTERS: tuple[type[Filter], ...] = (IntegerRangeFilter, DjangoFilterRangeFilter)


def refuse_unresolvable_lookup(
    filterset_cls: type[BaseFilterSet],
    filter_name: str,
    filter_instance: Filter,
) -> None:
    """Refuse a filter whose ``field_name`` and ``lookup_expr`` Django resolves on no queryset.

    The filter's predicate is the argument ``field_name__lookup_expr`` (a ``RangeFilter``'s
    ``field_name`` read as the column path it applies, ``_ResolvedField.path``), split as
    ``Query.build_filter`` splits it (``utils/querysets.py::split_lookup``, over a fresh
    ``Query`` of the model) into the names walked as a path and the transforms and lookup
    left over, each asked of where the path ends (``Field.get_transform`` /
    ``Field.get_lookup``, ``utils/relations.py::lookup_transform_parts``)
    (``_unresolvable_lookup``). Where the path ends on a column, the leftover is the
    column's transforms and lookups on every queryset: one the column's walk refuses
    (``signed_big__gt``, a ``lookup_expr`` no field registers) is refused. Where it ends
    on a relation, the leftover is asked of the field Django's query asks it of, the last
    join's field (``Query.names_to_path``'s final field: the relation itself, a reverse
    relation's ``ForeignObjectRel``, a many-to-many's through key onto its target), whose
    lookups every request applies whether or not a hop is walked
    (``filters/sets.py::FilterSet._leaf_chain``: a to-one key folds into them, a to-many
    key's predicate is built as declared before the target's key answers it), so one those
    refuse is refused (``parent`` or ``children`` with ``icontains``; the target's key is
    spelled ``children__id``); a filter applying the relation's ``range`` as its bounds
    (``_BOUNDED_RANGE_FILTERS``) is asked for a bound's ``gte``.
    ``filters/sets.py::FilterSet._publish_filters`` asks this of every
    leaf a set publishes whose ``filter`` is shipped code
    (``filters/sets.py::_runs_shipped_filter``), as ``refuse_identityless_relation`` is
    asked: a set a type serves refuses it when the schema builds, an unserved set at its
    first use (its first construction, or the package's first read of its table) and at
    every construction after until it is fixed. Nothing is kept between asks: a lookup a
    project registers after a set publishes (Django registers lookups at startup,
    ``AppConfig.ready``) is not seen by it.

    Not judged: a first name the model does not carry (a queryset annotation, a
    ``FilteredRelation`` alias, which only the queryset a filter runs on holds: Django's
    ``FieldError`` at the split), and a name past a relation the related model does not
    carry (a walked hop reads it on rows a type's ``get_queryset`` shapes,
    ``filters/sets.py::FilterSet._leaf_chain``). A name past a ``GenericForeignKey`` is
    no such name: no hop walks one and no queryset can annotate a name it holds, and
    ``filters/inputs.py::refuse_joinless_relation`` refuses it first. A set declaring no
    ``Meta.model`` has no model to resolve a path on and is not asked: a type refuses it
    when it binds (``types/finalizer.py::_bind_filterset_owner``), and applied unbound it
    refuses a leaf naming the missing ``Meta.model``
    (``filters/sets.py::FilterSet._leaf_form_entries``).
    """
    model = _filterset_model(filterset_cls)
    if model is None:
        return
    # django-filter formats the predicate's argument (``Filter.filter``), so a lazy
    # ``field_name`` or ``lookup_expr`` is read as the text it renders.
    field_name = truth.text(_declared_field_name(filter_instance))
    lookup_expr = truth.text(filter_instance.lookup_expr)
    path = (
        _model_resolved_field(model, field_name).path
        if truth.is_instance(filter_instance, RangeFilter)
        else field_name
    )
    refused = _unresolvable_lookup(
        model,
        path,
        lookup_expr,
        bounds=truth.is_one_of(filter_instance, _BOUNDED_RANGE_FILTERS),
    )
    if refused is None:
        return
    field, refusal = refused
    related_key = _related_column_hint(field, path)
    raise ConfigurationError(
        f"FilterSet {truth.qualname(filterset_cls)}: {truth.kind(filter_instance)} "
        f"{filter_name!r} has field_name {field_name!r} and lookup_expr {lookup_expr!r}, "
        "but Django resolves no transform or "
        f"lookup {truth.render(refusal.part)} on {_field_label(field)} ({truth.kind(field)}), "
        "so every request naming the filter would be refused. Spell the transforms and lookup "
        "the field registers (a column's lookups belong in lookup_expr, not field_name"
        f"{related_key}), register a project lookup at startup (Field.register_lookup in "
        "AppConfig.ready), or read the value in `method=`.",
    ) from refusal


#: ``django.contrib.postgres.lookups.HasKeys`` (``HStoreField``'s ``has_keys``, and through
#: ``HasAnyKeys`` its ``has_any_keys``), or ``None`` without a PostgreSQL driver.
_PG_HAS_KEYS_CLS = import_attr_if_importable("django.contrib.postgres.lookups", "HasKeys")

#: ``django.contrib.postgres.fields.RangeField``, whose ``get_prep_value`` reads a two-member
#: list as one range, or ``None`` without a PostgreSQL driver.
_PG_RANGE_FIELD_CLS = import_attr_if_importable("django.contrib.postgres.fields", "RangeField")


def _takes_list(lookup: type[models.lookups.Lookup], field: ModelField) -> bool:
    """Whether Django's own ``lookup`` applies a list over ``field`` as the list it is.

    Asked of Django first: a lookup whose ``get_db_prep_lookup_value_is_iterable`` is true
    (``FieldGetDbPrepValueIterableMixin``: ``in``, ``range``, a transform's or a relation's,
    read off the class's real MRO, ``utils/truth.py::mro_attr``) prepares each member as a
    value of the field. No Django seam marks the rest, so they are named: ``has_keys`` /
    ``has_any_keys`` (``JSONField``'s ``HasKeys``, ``HStoreField``'s) read each member as a
    key, and a lookup Django prepares through the field (``_django_prepares``: ``exact``,
    ``contains``, a comparison) takes the list as one value where a list is one, a
    ``JSONField``'s (a JSON array), a ``RangeField``'s (two bounds) or a
    ``CompositePrimaryKey``'s (one member per column: ``TupleExact``, ``TupleGreaterThan``).
    Everywhere else a list is no value of the field.
    """
    if truth.mro_attr(lookup, "get_db_prep_lookup_value_is_iterable") is True:
        return True
    if truth.is_subclass(lookup, JSONHasKeys) or (
        truth.is_type(_PG_HAS_KEYS_CLS) and truth.is_subclass(lookup, _PG_HAS_KEYS_CLS)
    ):
        return True
    return _django_prepares(lookup) and (
        truth.is_instance(field, models.JSONField)
        or truth.is_instance(field, models.CompositePrimaryKey)
        or (truth.is_type(_PG_RANGE_FIELD_CLS) and truth.is_instance(field, _PG_RANGE_FIELD_CLS))
    )


def refuse_listless_lookup(
    filterset_cls: type[BaseFilterSet],
    filter_name: str,
    filter_instance: Filter,
) -> None:
    """Refuse a ``ListFilter`` / ``ArrayFilter`` whose lookup applies one value, never a list.

    Both publish a list and hand the whole list to their lookup, so the lookup must take
    one (``_takes_list``), as ``in`` and ``range`` do; one comparing a single value
    (django-filter's default ``exact``, ``gte``, ``icontains``, ``isnull``, a transform
    ending in one: ``year``, an ``ArrayField``'s ``len`` or index) would stringify the list,
    fail to prepare it, or match nothing. The lookup is the one Django's query resolves
    past the transforms (``_filterset_lookup_operand``).
    ``filters/sets.py::FilterSet._publish_filters`` asks this of every leaf a set publishes
    whose ``filter`` is shipped code, right after ``refuse_unresolvable_lookup``: a set a
    type serves refuses the filter when the schema builds, an unserved set at its first
    use (its first construction, or the package's first read of its table) and at every
    construction after until it is fixed. A ``Meta.filter_overrides`` selection building a
    ``ListFilter`` for a column's ``exact`` or ``gte`` is refused alike. Over a relation
    the refusal spells the related column past it (``_related_column_hint``), the column a
    list of keys is typed by.

    Not judged: a lookup no walk resolves (a ``method=`` filter, whose method receives the
    list; a path only the queryset holds), a lookup a project registers (its class is not
    Django's: a served set refuses it when it seals its leaves), a column whose field class
    is project or third-party code (it owns how it prepares a value, a list stored as text
    included), a value of an ``ArrayField`` column, whose lookups the input build admits by
    name (``filters/inputs.py::_array_element_column``), and a stock django-filter
    ``FilterSet``, which publishes through no package table.
    """
    if not truth.is_instance(filter_instance, _ElementCleanedFilter):
        return
    operand = _filterset_lookup_operand(filterset_cls, filter_instance)
    lookup, field = operand.lookup, operand.field
    if (
        lookup is None
        or field is None
        or truth.module(lookup).partition(".")[0] != "django"
        or truth.module(truth.class_of(field)).partition(".")[0] != "django"
        or array_element_field(field) is not None
        or _takes_list(lookup, field)
    ):
        return
    field_name = truth.text(_declared_field_name(filter_instance))
    lookup_expr = truth.text(filter_instance.lookup_expr)
    related_key = _related_column_hint(field, field_name)
    raise ConfigurationError(
        f"FilterSet {truth.qualname(filterset_cls)}: {truth.kind(filter_instance)} "
        f"{filter_name!r} has field_name {field_name!r} and lookup_expr {lookup_expr!r}, "
        f"but the lookup it applies, Django's {truth.qualname(lookup)} "
        f"({truth.render(truth.mro_attr(lookup, 'lookup_name'))}), compares one value, and "
        "the filter publishes and applies a list. Declare lookup_expr 'in' (any member "
        "matches) or 'range' (two bounds), or a transform ending in either ('year__in')"
        f"{related_key}; read the list in `method=`; or, for a Meta.filter_overrides "
        "selection, list only those lookups for the column in Meta.fields.",
    )


def _filterset_walked_lookup(
    filterset: type[BaseFilterSet] | BaseFilterSet | None,
    filter_instance: Filter,
) -> tuple[str, str]:
    """Return ``filter_instance``'s ``field_name`` and ``lookup_expr`` as Django walks them.

    ``_model_walked_lookup`` on ``filterset``'s model: a ``lookup_expr`` continuing the
    path across a relation (``field_name="shelf", lookup_expr="tier__in"``) answers the
    path Django walks and the lookup left where it ends (``("shelf__tier", "in")``), so
    every package read meaning that path (the column a value is cleaned and typed as,
    the hops a walk crosses, scopes and gates, the terminal it runs over the last hop's
    rows) reads what ``field_name="shelf__tier", lookup_expr="in"`` reads. The argument
    the filter's own ``filter`` hands Django is the same either way, and the filter is
    never rewritten: its ``field_name``, ``lookup_expr`` and ``label`` read as declared
    (``filters/sets.py::FilterSet._bound_terminal`` writes the walked pair onto its
    per-request copy alone). The filter's own pair answers for a filterset with no
    model, a ``ProjectedChildFilter`` (its child filter walks in the child set), and a
    filter holding a ``filter`` of its own (``filters/sets.py::_own_filter``: the
    ``FilterMethod`` a ``method=`` installs, or a callable stored on the instance, which
    receives the pair as declared). A class-level ``filter`` override walks, as
    ``filters/sets.py::FilterSet._flat_leaf_walk`` walks it: it reads its pair off the
    per-request copy the walk binds; so does a ``RelatedFilter`` head.
    """
    field_name = truth.text(_declared_field_name(filter_instance))
    lookup_expr = truth.text(filter_instance.lookup_expr)
    model = _filterset_model(filterset)
    if model is None:
        return field_name, lookup_expr
    walked = _model_walked_lookup(model, field_name, lookup_expr)
    if walked == (field_name, lookup_expr):
        operand = _model_lookup_operand(model, field_name, lookup_expr)
        query = _model_unresolved_query(filter_instance, operand)
        if query is not None:
            walked = _query_walked_lookup(query, field_name, lookup_expr)
    if walked[1] == lookup_expr or not _walks_declared_lookup(filter_instance):
        return field_name, lookup_expr
    return walked


def _walks_declared_lookup(filter_instance: Filter) -> bool:
    """Whether the path ``filter_instance``'s package reads walk is the one Django walks.

    A leaf holding no ``filter`` of its own (``filters/sets.py::_own_filter``), the rule
    ``filters/sets.py::FilterSet._flat_leaf_walk`` walks by, a ``RelatedFilter`` head
    included; never a ``ProjectedChildFilter`` (``_filterset_walked_lookup``).
    """
    from .sets import ProjectedChildFilter, _own_filter  # noqa: PLC0415 - import cycle

    return (
        not isinstance(filter_instance, ProjectedChildFilter)
        and _own_filter(filter_instance) is None
    )


@cache
def _model_walked_lookup(
    model: type[models.Model],
    field_name: str,
    lookup_expr: str,
) -> tuple[str, str]:
    """Return ``field_name`` and ``lookup_expr``, every name Django walks as a path in the first.

    The argument ``field_name__lookup_expr`` is split as ``Query.build_filter`` splits it
    (``utils/querysets.py::split_lookup``, over a fresh ``Query`` of the model) into the
    names walked as a path and the transforms and lookup left over. Where the path runs
    past the ``field_name`` (``field_name="shelf", lookup_expr="branch__in"``,
    ``lookup_expr="pk__in"``), the answer is that path and the leftover
    (``("shelf__branch", "in")``; an empty leftover is Django's ``exact``); any other pair
    is answered as given, a path Django refuses on a fresh query (a queryset annotation or
    ``FilteredRelation`` alias) included. Kept per key, each fixed when the FilterSet is
    defined.
    """
    return _query_walked_lookup(Query(model), field_name, lookup_expr)


def _query_walked_lookup(query: Query, field_name: str, lookup_expr: str) -> tuple[str, str]:
    """Walk a bound lookup on its actual query, retaining Django's implicit ``exact``."""
    try:
        head, _start, leftover = split_lookup(query, LOOKUP_SEP.join((field_name, lookup_expr)))
    except FieldError:
        return field_name, lookup_expr
    if len(head) <= len(field_name.split(LOOKUP_SEP)):
        return field_name, lookup_expr
    return LOOKUP_SEP.join(head), LOOKUP_SEP.join(leftover) or "exact"


def _related_column_path(field: ModelField, path: str) -> str | None:
    """Return ``path`` continued to the related column a relation ``field`` compares; ``None``.

    A relation applies only its own lookups (``RelatedExact``, ``RelatedIn``, ...) to the
    column its last join compares (``path_infos[-1].target_fields``); that column's own
    lookups are reached by naming it past the relation (``children__id``), which Django
    answers alike whether or not a hop is walked. ``None`` for a column, and for a relation
    compared on more than one column or on a column that is itself a relation.
    """
    if not isinstance(
        field,
        (models.ForeignObject, models.ManyToManyField, models.ForeignObjectRel),
    ):
        return None
    targets = field.path_infos[-1].target_fields
    if len(targets) != 1 or targets[0].is_relation:
        return None
    return LOOKUP_SEP.join((path, targets[0].name))


def _related_column_hint(field: ModelField, path: str) -> str:
    """Return the refusal's pointer to ``_related_column_path``'s column; ``""`` without one."""
    column = _related_column_path(field, path)
    if column is None:
        return ""
    return f" (a relation's related column is named past it: field_name {column!r})"


def _unresolvable_lookup(
    model: type[models.Model],
    field_name: str,
    lookup_expr: str,
    *,
    bounds: bool,
) -> tuple[ModelField, LookupValidationError] | None:
    """Return the field ``refuse_unresolvable_lookup``'s walk refuses on, and its refusal; ``None``.

    ``bounds`` is whether the filter applies a final ``range`` as its bounds. Asked once per
    published leaf (a set publishes its table once), so nothing is kept.
    """
    query = Query(model)
    try:
        head, start, leftover = split_lookup(query, LOOKUP_SEP.join((field_name, lookup_expr)))
    except FieldError:
        return None
    # A fresh ``Query`` holds no annotation, so the start is a field Django's walk ended on.
    field: ModelField = (
        start
        if truth.is_instance(start, models.ForeignObjectRel)
        else require(start, is_concrete_field)
    )
    # ``Query.build_lookup`` reads an empty leftover (a path ending on a field) as ``exact``.
    rest = LOOKUP_SEP.join(leftover) or "exact"
    if not field.is_relation:
        refusal = _refusal(field, rest)
        return None if refusal is None else (field, refusal)
    if len(head) < len(field_name.split(LOOKUP_SEP)):
        return None
    # A range filter applies a relation's ``range`` as its bounds.
    *transforms, final = rest.split(LOOKUP_SEP)
    if bounds and final == "range":
        rest = LOOKUP_SEP.join((*transforms, "gte"))
    # The walk from the relation reads its own lookups (the ``Col`` Django's query builds:
    # a reverse relation, a many-to-many's through key onto its target).
    refusal = _refusal(field, rest)
    if refusal is None:
        return None
    steps = _names_to_path(query, head[:-1], model._meta)[0] if head[:-1] else []
    owner = steps[-1].to_opts.model if steps else model
    # Named as the path spells it: a many-to-many, not its through table's key.
    return owner._meta.get_field(head[-1]), refusal


def _refusal(start: ModelField, lookup_expr: str) -> LookupValidationError | None:
    """Return the refusal of ``lookup_expr`` by Django's walk from ``start``; ``None`` for none."""
    try:
        _ = lookup_transform_parts(start, lookup_expr)
    except LookupValidationError as refusal:
        return refusal
    return None


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

    The ``ModelChoiceFilter`` itself is the raw-form head (``FilterSet(data=...)``,
    ``DjangoFilterBackend``, ``FilterView``; GraphQL names no head): a key the form data
    names (``shelf=<pk>``) is validated against ``get_queryset``'s rows within those the
    target type lets the request see and matches through the rows each hop shows, as the
    relation key does (``filters/sets.py::FilterSet._flat_leaf_walk``).

    ``flat=False`` (keyword-only, an exact ``bool``, read-only through ``flat``)
    withdraws the declaration's flat copies: the parent's expansion
    (``filters/sets.py::FilterSet._expand_along``) still validates the
    declaration and copies nothing through it. A flat key and its nested branch
    differ in meaning (a flat key matches a parent through any one related row,
    a branch through one row meeting every condition), so it removes a
    capability, and clients regenerate their schema. What stays: the nested
    branch, the raw-form head, the target's own build and cap, and the parent's
    own filters, explicit ``Meta.fields`` traversals across the relation
    included. A form-data key only the copy registered is ignored, as
    django-filter ignores any unregistered key. An own key an enabled copy
    would replace is the own filter again, with its full behavior: its value
    when omitted (a checkbox's ``False``), ``required``, ``lookup_expr``,
    ``exclude``, its widget, and a shown field under ``HIDE_FLAT_FILTERS``; an
    own ``method=`` runs on the parent queryset with no relation gate and no
    target visibility, as any own ``method=`` does. A ``get_filters()`` override
    reading a copied key finds it absent once the declaration it came from is
    disabled.
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
        flat: bool = True,
        **kwargs: object,
    ) -> None:
        """Bind the target `filterset` and record explicit-queryset intent.

        ``flat`` is keyword-only, so a positional extra stays django-filter's;
        anything but an exact ``bool`` raises ``ConfigurationError``, the
        placeholder ``RelatedFilter(None)`` included. It is stored before the
        upstream constructor runs, so it never reaches ``Filter.extra``.

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
        if not truth.is_exact(flat, bool):
            raise ConfigurationError(
                f"RelatedFilter flat must be a bool; got {truth.describe(flat)}.",
            )
        self._flat: bool = flat
        self._has_explicit_queryset: bool = kwargs.get("queryset") is not None
        # basedpyright: the kwargs are forwarded verbatim and ``ModelChoiceFilter.__init__`` owns
        # their validation; it rejects ``object`` kwargs for the ``str | None`` params
        super().__init__(*args, **kwargs)  # pyright: ignore[reportArgumentType]
        self._filterset: _FilterSetTarget = filterset

    @property
    def flat(self) -> bool:
        """Whether the parent's expansion copies this declaration's target filters flat."""
        return self._flat

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
