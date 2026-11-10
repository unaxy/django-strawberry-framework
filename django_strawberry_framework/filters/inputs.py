"""Filter input namespace, lookup-name scaffolding, and shape converters.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.filters.inputs")`` resolves
through ``module.__dict__`` (spec-027 Decision 9). The module pairs the
constants (``LOOKUP_PREFIXES`` / ``LOOKUP_NAME_MAP`` / ``FieldSpec`` /
``_field_specs`` / ``_materialized_names``) with the
filter-instance -> Strawberry-annotation converter pair
(``convert_filter_to_input_annotation`` /
``normalize_input_value``), the dataclass builder
(``build_input_class``), the per-filterset operator-bag helpers
(``filter_lookup_table`` / ``_build_input_fields`` / ``_build_logic_fields``
/ ``construct_search``), and the module-global materialization /
namespace-clear pair (``materialize_input_class`` /
``clear_filter_input_namespace``).
"""

from __future__ import annotations

import datetime
import decimal
import enum
import keyword
import uuid
import warnings
from collections import OrderedDict
from dataclasses import dataclass
from itertools import takewhile
from types import GenericAlias, MappingProxyType
from typing import TYPE_CHECKING, Annotated

import strawberry
from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.lookups import FieldGetDbPrepValueMixin
from django.utils.choices import flatten_choices
from django_filters import (
    ChoiceFilter,
    Filter,
    LookupChoiceFilter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumericRangeFilter,
    TypedChoiceFilter,
)
from django_filters import RangeFilter as _DjangoRangeFilter
from django_filters.fields import BaseCSVField
from django_filters.filters import BaseCSVFilter, QuerySetRequestMixin
from strawberry import relay

from django_strawberry_framework.conf import hide_flat_filters_setting
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.converter import FORM_FIELD_SCALARS, form_field_scalar
from django_strawberry_framework.registry import register_subsystem_clear
from django_strawberry_framework.relay import _node_id_slot
from django_strawberry_framework.scalars import BigInt
from django_strawberry_framework.sets_mixins import declaration_map
from django_strawberry_framework.types.converters import (
    _field_label,
    _generated_output_issue,
    _registered_scalar_entry,
    holds_values_as_given,
    refuse_nested_array,
    scalar_for_field,
)
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._array_field import array_element_field
from django_strawberry_framework.utils._narrowing import (
    dict_of,
    enum_value,
    is_concrete_field,
    is_list_or_tuple,
    is_mapping,
    is_queryset,
    list_of,
    optional_annotation,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.converters import convert_with_mro
from django_strawberry_framework.utils.input_values import (
    UNSET,
    is_inactive_value,
    iter_input_items,
)
from django_strawberry_framework.utils.inputs import (
    DECLARED_MEMBER,
    EXPANDED_MEMBER,
    LISTED_LOOKUP,
    LISTED_MEMBER,
    GeneratedFieldSources,
    GeneratedInputFieldSpec,
    MemberLever,
    build_strawberry_input_class,
    emit_set_input_field_triples,
    make_set_input_namespace,
    optional_field_kwargs,
)
from django_strawberry_framework.utils.relations import generated_column_source
from django_strawberry_framework.utils.strings import flatten_lookup_path, pascal_case_or_raise
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.utils.widgets import multi_widget_keys, widget_keys

from .base import (
    _RANGE_BOUNDS,
    EMPTY_VALUES,
    ArrayFilter,
    EnumMemberValue,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
    TextPatternFilter,
    TypedFilter,
    _ColumnCleanedFilter,
    _compared_columns,
    _declared_field_name,
    _EnumMemberFilterMixin,
    _filterset_lookup_lhs_path,
    _filterset_lookup_operand,
    _filterset_lookup_source_field,
    _filterset_model,
    _filterset_model_field,
    _filterset_value_field,
    _filterset_walked_lookup,
    _model_identity_column,
    _related_column_path,
    comparison_form_field,
    copied_filter,
    copied_form_field,
    defers_choices,
    model_choice_model,
    relation_identity_column,
)

# Domain-local aliases for the shared generated-input substrate (the mechanics
# are single-sited in ``utils/inputs.py``); the spec-027 Decision 9 names stay
# addressable from this module.
FieldSpec = GeneratedInputFieldSpec
build_input_class = build_strawberry_input_class

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from django_strawberry_framework.types.definition import DjangoTypeDefinition
    from django_strawberry_framework.utils.inputs import SetInputNamespace
    from django_strawberry_framework.utils.typing import ModelField

    from .sets import ChildProjection, FilterSet, _LeafDeclaration

# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so the factory, ``_build_logic_fields``, and
# ``filter_input_type`` (in ``__init__.py``) all stay in sync.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.filters.inputs"


# Search-prefix vocabulary for the planned `Meta.search_fields` surface
# (spec-027 Decision 2); consumed by `construct_search` below.
LOOKUP_PREFIXES: dict[str, str] = {
    "^": "istartswith",
    "=": "iexact",
    "@": "search",
    "$": "iregex",
}


# `django-filter` lookup -> python attr per spec-027 Decision 3 Layer 5. The
# map spells each lookup's attr with its word boundary (`i_contains`); the
# schema's `NameConverter` names the field from it (`iContains` by default,
# `i_contains` under `auto_camel_case=False`). `in` is a Python keyword, so its
# attr is `in_` and it publishes `in` through `name=`. Read through
# `lookup_leaf_names`, which names every bag lookup (a transform chain segment
# by segment), and by `FilterSet._operator_bag_items` (recognizing a hand-built
# operator bag).
LOOKUP_NAME_MAP: dict[str, str] = {
    "exact": "exact",
    "iexact": "i_exact",
    "contains": "contains",
    "icontains": "i_contains",
    "startswith": "starts_with",
    "istartswith": "i_starts_with",
    "endswith": "ends_with",
    "iendswith": "i_ends_with",
    "regex": "regex",
    "iregex": "i_regex",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
    "isnull": "is_null",
    "in": "in_",
    "range": "range",
    "date": "date",
    "year": "year",
    "month": "month",
    "day": "day",
    "week_day": "week_day",
    "quarter": "quarter",
    "hour": "hour",
    "minute": "minute",
    "second": "second",
}


def lookup_leaf_names(lookup: str) -> tuple[str, str | None]:
    """Return an operator-bag lookup's ``(python_attr, keyword wire name or None)``.

    A single token reads ``LOOKUP_NAME_MAP`` (``icontains`` -> ``i_contains``); one the
    map does not hold is its own attr (``iso_year``). A Python keyword token escapes its
    attr with a trailing ``_`` and carries the keyword as its wire name (``in`` ->
    ``in_`` / ``in``; a transform registered as ``from`` publishes ``from`` over the attr
    ``from_``). A transform chain (``year__gt``) joins each segment's attr with ``_``, a
    keyword segment unescaped (``year_gt``, ``year_i_contains``, ``year_in``). Only a
    single keyword token carries a wire name; the executing schema's ``NameConverter``
    names every other field (``yearIContains`` by default). The one site that names a bag
    lookup: ``filter_lookup_table`` keys each head's lookups by the attr and
    ``_build_input_fields`` publishes the pair.
    """
    segments = lookup.split(LOOKUP_SEP)
    if len(segments) == 1:
        if keyword.iskeyword(lookup):
            return f"{lookup}_", lookup
        return LOOKUP_NAME_MAP.get(lookup, lookup), None
    named = (lookup_leaf_names(segment) for segment in segments)
    return "_".join(attr if wire_name is None else wire_name for attr, wire_name in named), None


def _compose_and(branch_qs: list[models.Q]) -> models.Q:
    """Compose branch Q objects with logical AND."""
    q = models.Q()
    for branch_q in branch_qs:
        q &= branch_q
    return q


def _compose_or(branch_qs: list[models.Q]) -> models.Q:
    """Compose branch Q objects with logical OR."""
    if not branch_qs:
        return models.Q()
    q = models.Q()
    for branch_q in branch_qs:
        q |= branch_q
    return q


def _compose_not(branch_qs: list[models.Q]) -> models.Q:
    """Compose branch Q objects with logical NOT."""
    if not branch_qs:
        return models.Q()
    return ~branch_qs[0]


@dataclass(frozen=True, slots=True)
class LogicOperatorDescriptor:
    """Authoritative descriptor for a filter logical operator.

    Encapsulates the Python attribute name, wire name, cardinality (sequence vs
    single-element), and Django Q composition semantics in a single immutable record.
    """

    python_attr: str
    wire_name: str
    is_sequence: bool
    compose: Callable[[list[models.Q]], models.Q]

    def arm_key(self, index: int) -> str:
        """Return the key arm ``index`` of this operator carries in a filter error.

        django-graphene-filters' spelling (``AdvancedFilterSet.TreeFormMixin.errors``):
        the wire name and the arm's position for a sequence operator (``and_0``,
        ``or_1``), the wire name alone for ``not``, which takes one arm. A nested
        branch or leaf inside the arm follows under it (``filters/sets.py::_branch_key``).
        """
        return f"{self.wire_name}_{index}" if self.is_sequence else self.wire_name


LOGIC_OP_AND = LogicOperatorDescriptor(
    python_attr="and_",
    wire_name="and",
    is_sequence=True,
    compose=_compose_and,
)

LOGIC_OP_OR = LogicOperatorDescriptor(
    python_attr="or_",
    wire_name="or",
    is_sequence=True,
    compose=_compose_or,
)

LOGIC_OP_NOT = LogicOperatorDescriptor(
    python_attr="not_",
    wire_name="not",
    is_sequence=False,
    compose=_compose_not,
)

LOGIC_OPERATORS: tuple[LogicOperatorDescriptor, ...] = (LOGIC_OP_AND, LOGIC_OP_OR, LOGIC_OP_NOT)

LOGIC_OPERATORS_BY_WIRE: Mapping[str, LogicOperatorDescriptor] = MappingProxyType(
    {op.wire_name: op for op in LOGIC_OPERATORS},
)

LOGIC_OPERATORS_BY_PYTHON_ATTR: Mapping[str, LogicOperatorDescriptor] = MappingProxyType(
    {op.python_attr: op for op in LOGIC_OPERATORS},
)


# Provenance table populated by ``_build_input_fields`` and consulted at
# runtime by ``FilterSet._normalize_input`` and ``normalize_input_value``.
# Cleanup contract: keyed by ``(FilterSet subclass, python_attr)`` and
# emptied ONLY by ``clear_filter_input_namespace`` (driven by
# ``registry.clear()``). A consumer test suite that reloads model / filter
# modules WITHOUT routing through ``registry.clear()`` retains stale entries
# from the prior build; the filter test files' ``_isolate_registry`` autouse
# fixture clears this map explicitly for exactly that reason.
#
# spec-027 Decision 9 namespace lifecycle. Mechanics live in
# ``utils/inputs.py::make_set_input_namespace`` (heavy clear: ledger +
# field_specs + factory caches + ``_lifecycle`` binding). This module keeps
# the spec-named public wrappers and the disjoint per-subsystem ledgers.
# ``clear_filter_input_namespace`` leaves class objects parked in
# ``filters.inputs.__dict__``, per the parked-globals lifecycle stated on
# ``utils/inputs.py::make_input_namespace``.
_materialized_names: dict[str, type[object]]
_field_specs: dict[tuple[type[object], str], FieldSpec]
_namespace: SetInputNamespace = make_set_input_namespace(
    INPUTS_MODULE_PATH,
    "FilterSet",
    factory_module="django_strawberry_framework.filters.factories",
    factory_class_name="FilterArgumentsFactory",
    collision_registry_attr="_type_filterset_registry",
    set_module="django_strawberry_framework.filters.sets",
    set_class_name="FilterSet",
)
_materialized_names, _field_specs, _materialize_input, _clear_input_namespace = _namespace


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


# Pascal-case helper for input-class names. The conversion AND the
# no-word-character emptiness check both live in the shared
# ``utils/strings.py::pascal_case_or_raise`` (single-sited, shared with
# ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for``); this wrapper
# only supplies the ``RangeFilter``-specific error.
def _pascal_case(name: str) -> str:
    """Return ``name`` converted to ``PascalCase``, raising on a token-less input.

    Delegates to ``utils/strings.py::pascal_case_or_raise``; an input with no
    word-character tokens (e.g. ``"_"``, ``""``, ``"__"``) would silently
    collide on the downstream ``RangeInputType`` naming, so it raises
    ``ConfigurationError`` instead. Direct caller today:
    ``_build_range_input_class`` only. The indirect caller, ``_build_input_fields``'s
    operator-bag class naming, routes through
    ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for(field_path)`` and trips the
    same shared guard with its own error - so the error message below names
    the ``RangeFilter`` consumer specifically.
    """
    return pascal_case_or_raise(
        name,
        make_error=lambda bad: ConfigurationError(
            f"_pascal_case received {truth.render(bad)} which contains no word "
            "characters; rename the RangeFilter's `field_name=` so its "
            "name has at least one alphanumeric token.",
        ),
    )


def _scalar_from_form_field(form_field: object) -> object:
    """Return the scalar one value a filter's form field cleans is published as.

    The row ``forms/converter.py::form_field_scalar`` reads from ``FORM_FIELD_SCALARS``,
    the table ``convert_form_field`` reads too, so a ``forms.JSONField`` publishes
    ``JSON`` and a consumer ``field_class`` subclassing a registered class publishes
    that class's scalar. A form field no row covers (a bare ``forms.Field``, a consumer
    ``forms.Field`` subclass with its own ``to_python``) publishes ``String``: a
    django-filter form cleans the text of a querystring, so text reaches every filter
    form, where ``convert_form_field`` refuses such a field for a form mutation.
    """
    scalar = form_field_scalar(form_field)
    return str if scalar is None else scalar


def _scalar_from_model_field(
    model_field: ModelField | None,
    filter_instance: Filter,
    filterset_cls: type[FilterSet] | None,
) -> object:
    """Map the model field a leaf is typed from to its scalar via the shared ``SCALAR_MAP``.

    Delegates to ``types/converters.py::scalar_for_field``, so a filter input and the
    selected ``DjangoType`` field resolve a column to the SAME GraphQL scalar, including
    consumer-registered entries and the ``BigInt`` scalar for 64-bit columns. A field no
    entry covers (``types/converters.py::_registered_scalar_entry``, the walk
    ``scalar_for_field`` reads, answers ``None``) is refused naming the leaf as declared
    (``_unscalared_field_refusal``) rather than with the ``DjangoType`` advice, never
    degraded to ``str``. ``None`` (a method filter with no backing model field) keeps the
    ``str`` fallback.
    """
    if model_field is None:
        return str
    if _registered_scalar_entry(model_field) is None:
        raise _unscalared_field_refusal(filter_instance, model_field, filterset_cls)
    # A ``SCALAR_MAP`` value is a registered runtime annotation (a class or ``NewType``).
    return scalar_for_field(model_field)


def _unscalared_field_refusal(
    filter_instance: Filter,
    model_field: ModelField,
    filterset_cls: type[FilterSet] | None,
    *,
    generated_issue: str | None = None,
) -> ConfigurationError:
    """Build the refusal for a leaf typed from a model field no ``SCALAR_MAP`` entry covers.

    The remedy follows what the field is. A relation's value is a related row's key: one
    Django joins on a single column is filtered through generated ``Meta.fields`` only
    when the declaring set's generation seam selects the package identity primitive
    (a registered Relay target uses its public GlobalID; otherwise the target key),
    through a default model-choice filter on the target's primary key when scalar,
    by the related column named past it (``filters/base.py::_related_column_path``, on
    the path Django walks, ``_filterset_walked_lookup``), or by the related row's fields
    through a ``RelatedFilter``; one linked by several columns only by the last; a
    ``GenericForeignKey``, which Django builds no join for (``_compared_columns`` answers
    none), through the ``GenericRelation`` reversing it or the two columns it reads. A
    ``CompositePrimaryKey`` holds no one value, so its columns are named one by one. Any
    other column takes a ``SCALAR_MAP`` entry for its class.
    """
    declaration = _declaration_of(filter_instance, filterset_cls)
    subject = (
        f"{_declaration_subject(declaration, filterset_cls)} reads {_field_label(model_field)}, "
        f"a {truth.kind(model_field)}"
    )
    if generated_issue == "file":
        return ConfigurationError(
            f"{subject} computed by a GeneratedField as a file output; a database expression "
            "stores no file. Remove or change this filter declaration.",
        )
    if generated_issue == "array_choices":
        return ConfigurationError(
            f"{subject} computed by a GeneratedField whose ArrayField base_field declares "
            "choices Django never validates, so they publish no enum. Drop those choices "
            "or remove this filter declaration.",
        )
    if isinstance(model_field, models.CompositePrimaryKey):
        columns = ", ".join(repr(column.name) for column in model_field.fields)
        return ConfigurationError(
            f"{subject} over {columns}, which no one value names; filter each column it "
            "composes by name.",
        )
    unscalared = f"{subject} no SCALAR_MAP entry types, so nothing types its input"
    if not model_field.is_relation:
        return ConfigurationError(
            f"{unscalared}; register {truth.kind(model_field)} (or a class it subclasses) in "
            "SCALAR_MAP.",
        )
    compared = _compared_columns(filter_instance, model_field)
    if not compared:
        return ConfigurationError(
            f"{subject}: Django filters no queryset through it, so no input can carry its "
            "value; filter through the GenericRelation that reverses it on the related "
            "model, or on the content type and object id columns it reads.",
        )
    if len(compared) > 1:
        return ConfigurationError(
            f"{subject} {_linked_by_columns(len(compared))}",
        )
    walked = truth.text(_filterset_walked_lookup(declaration.filterset, declaration.declared)[0])
    path = LOOKUP_SEP.join((*walked.split(LOOKUP_SEP)[:-1], model_field.name))
    column = _related_column_path(model_field, path)
    key = relation_identity_column(model_field)
    if isinstance(key, models.CompositePrimaryKey):
        key = None
    from .sets import _relay_target_type_for_relation  # noqa: PLC0415 - import cycle

    target_type = _relay_target_type_for_relation(model_field)
    owner = declaration.filterset or filterset_cls
    generated_available = False
    if owner is not None:
        origin, shape_capable = owner._generation_policy_for_field(model_field, path, "exact")
        generated_available = origin == "framework_default" and shape_capable
    if target_type is not None:
        id_attr, id_field = _node_id_slot(target_type)
        generated_route = (
            f"filter by the related row's public {id_attr!r} GlobalID through {path!r} "
            "in Meta.fields"
            if generated_available
            and id_field is not None
            and not isinstance(id_field, models.CompositePrimaryKey)
            else ""
        )
        choice_route = (
            ""
            if key is None
            else (
                f"use a ModelChoiceFilter / ModelMultipleChoiceFilter{_scalar_prerequisite(key)}"
            )
        )
        key_route = ", ".join(route for route in (generated_route, choice_route) if route)
    elif key is None:
        key_route = ""
    elif generated_available:
        key_route = (
            f"filter by the related row's key through {path!r} in Meta.fields or a "
            f"ModelChoiceFilter / ModelMultipleChoiceFilter{_scalar_prerequisite(key)}"
        )
    else:
        key_route = (
            f"use a ModelChoiceFilter / ModelMultipleChoiceFilter{_scalar_prerequisite(key)}"
        )
    compared_prerequisite = _scalar_prerequisite(next(iter(compared), None))
    past = "" if column is None else f"name the related column past it (field_name {column!r})"
    if column is not None:
        past += compared_prerequisite
    routes = ", ".join(route for route in (key_route, past) if route)
    if routes:
        routes += ", or "
    return ConfigurationError(
        f"{unscalared}; {routes}filter the related row's own fields through a RelatedFilter.",
    )


def _scalar_prerequisite(column: ModelField | None) -> str:
    """State the missing scalar a suggested key or joined-column route must first register."""
    if column is None or _registered_scalar_entry(column) is not None:
        return ""
    return f" (first register {truth.kind(column)} for {_field_label(column)} in SCALAR_MAP)"


def _refuse_generated_filter_output(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet],
) -> None:
    """Apply generated-output policy before typed or active raw filter input dispatch."""
    declaration = _declaration_of(filter_instance, filterset_cls)
    source = _filterset_lookup_source_field(declaration.filterset, declaration.declared)
    for field in (source, model_field):
        if not is_concrete_field(field) or generated_column_source(field) is None:
            continue
        issue = _generated_output_issue(field)
        if issue is not None:
            raise _unscalared_field_refusal(
                filter_instance,
                field,
                filterset_cls,
                generated_issue=issue,
            )


def _declaration_of(
    filter_instance: Filter,
    filterset_cls: type[FilterSet] | None,
) -> _LeafDeclaration:
    """Return the declaration a leaf of ``filterset_cls`` stands for in an error message.

    ``filters/sets.py::_leaf_declaration`` owns the answer: a ``RelatedFilter``
    expansion's copy, projected or rebound, names the child set's declared filter,
    its attribute and the ``RelatedFilter`` path, never the runtime-built
    ``Projected<Class>`` or the parent's flat ``field_name``; a leaf declared on the
    set that holds it names itself, so its messages read as they do for any root
    filter.
    """
    from .sets import _leaf_declaration  # noqa: PLC0415 - import cycle

    return _leaf_declaration(filter_instance, filterset_cls)


def _linked_by_columns(count: int) -> str:
    """Return the refusal's reason and remedy for a relation linked by ``count`` columns."""
    return (
        f"linked by {count} columns, so no single key value can name a related row; filter the "
        "related row's own fields through a RelatedFilter."
    )


def _relation_identity_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None = None,
) -> object:
    """Type a raw-pk relation leaf from the column its predicate compares.

    The column is the one the filter's value is coerced through at request time
    (``filters/base.py::_compared_columns``): the target's primary key for a leaf marked
    for ``<relation>__pk`` and an ordinary link, the link's column for a declared
    unmarked ``ForeignObject`` off the pk or a many-to-many through a ``to_field``. The
    scalar comes from it through the shared ``SCALAR_MAP`` lookup, so the input agrees
    with how a ``DjangoType`` types that column (``Int``, ``UUID``, ``BigInt``,
    ``String``, ...). A relation linked by more than one column has no single column a
    value can name, so no scalar can type it and the build refuses it naming the column
    count. A raw-pk filter whose ``field_name`` resolves no relation on its ``FilterSet``
    model has no column to type from; both refusals name the filter as declared
    (``_declaration_of``).
    """
    columns = (
        _compared_columns(filter_instance, model_field)
        if model_field is not None and model_field.is_relation
        else ()
    )
    if len(columns) > 1:
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{_declaration_subject(declaration, filterset_cls)} names a relation "
            f"{_linked_by_columns(len(columns))}",
        )
    if not columns:
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{_declaration_subject(declaration, filterset_cls)}, which is not a "
            "relation to a model on its FilterSet; name a relation key in Meta.fields, or "
            "filter the related row's own fields through a RelatedFilter.",
        )
    return _scalar_from_model_field(columns[0], filter_instance, filterset_cls)


def _model_choice_takes_list(filter_instance: Filter) -> bool:
    """Whether a consumer model-choice filter's form field cleans a list of values.

    ``ModelMultipleChoiceFilter`` does, and so does django-filter's CSV wrapper around
    a ``ModelChoiceFilter`` (``filter_for_lookup`` builds
    ``ConcreteInFilter(BaseInFilter, <filter_class>)`` for an ``in`` lookup), whose
    ``BaseCSVField`` cleans each member through the model-choice field.
    """
    return isinstance(filter_instance, (ModelMultipleChoiceFilter, BaseCSVFilter))


def _declared_form_field(filter_instance: Filter) -> object:
    """Return the form field the filter's class builds, ``None`` when it builds none unbound.

    The filter is the class-level declaration every request deep-copies, so the field
    is read on a copy (``filters/base.py::copied_form_field``) and the declaration keeps
    nothing. A ``field`` that raises ``AttributeError`` without a bound ``FilterSet``
    (``AllValuesMultipleFilter`` reads the per-request ``model``) builds none here.
    """
    try:
        return copied_form_field(filter_instance)
    except AttributeError:
        return None


def _form_value_fields(filter_instance: Filter) -> tuple[object, ...]:
    """Return the form fields that clean one value the filter's input publishes.

    The filter's own form field (``_declared_form_field``), whose class also names the
    member a django-filter CSV field cleans (``BaseCSVFilter`` builds its field as a
    ``BaseCSVField`` subclass of the filter's own ``field_class``). A ``MultiValueField``
    (django-filter's ``RangeField`` and its ``DateRangeField`` / ``DateTimeRangeField`` /
    ``TimeRangeField`` kin) cleans each axis with one of its ``fields``, so those answer.
    Empty for a filter whose form field is not built unbound.
    """
    return _value_fields_of(_declared_form_field(filter_instance))


def _value_fields_of(form_field: object) -> tuple[object, ...]:
    """Return the fields of a built ``form_field`` cleaning one value (``_form_value_fields``)."""
    if form_field is None:
        return ()
    if isinstance(form_field, forms.MultiValueField):
        return tuple(form_field.fields)
    return (form_field,)


def _passes_value_through(form_field: object) -> bool:
    """Whether ``form_field`` cleans a value to itself, whatever its kind.

    Django's bare ``forms.Field`` (django-filter's ``Filter.field_class``, so a bare
    ``Filter`` or ``TypedFilter``) and a subclass that overrides neither ``to_python`` nor
    ``clean``: its ``to_python`` returns the value unchanged, so it cleans a value of any
    scalar the input publishes and the lookup receives it as sent.
    """
    return truth.is_instance(form_field, forms.Field) and not truth.overrides(
        truth.class_of(form_field),
        forms.Field,
        "to_python",
        "clean",
    )


#: Each form-field class -> the Python kind one value it cleans is: the scalars
#: ``FORM_FIELD_SCALARS`` publishes, and the classes whose kind no scalar publishes (a
#: ``DurationField``'s ``timedelta``), read by MRO (``_cleaned_kind``).
_CLEANED_KINDS: Mapping[type[forms.Field], object] = MappingProxyType(
    {**FORM_FIELD_SCALARS, forms.DurationField: datetime.timedelta},
)


#: The form fields cleaning each value through their ``coerce`` (``_cleaned_kind``,
#: ``_cleans_in_shipped_code``).
_COERCING_FORM_FIELDS: tuple[type[forms.Field], ...] = (
    forms.TypedChoiceField,
    forms.TypedMultipleChoiceField,
)

#: The methods whose own definition changes what a form field cleans (``_keeps_cleaning_of``,
#: ``_cleans_in_shipped_code``).
_CLEANING_METHODS: tuple[str, ...] = ("to_python", "clean", "_coerce")


def _keeps_cleaning_of(form_class: type[object], kind_class: type[object]) -> bool:
    """Whether no class from ``form_class`` up to ``kind_class`` defines its own cleaning.

    ``kind_class`` is on ``form_class``'s real MRO (``_cleaned_kind`` reads it from there);
    each class before it is read in its own namespace (``_CLEANING_METHODS``).
    django-filter's ``BaseCSVField`` is passed over: its ``clean`` cleans each member through
    the classes after it, so a member keeps the kind ``kind_class`` names, while a consumer
    member class cleaning its own way is seen past it.
    """
    below_kind = takewhile(lambda klass: klass is not kind_class, truth.mro(form_class))
    return not any(
        klass is not BaseCSVField
        and any(name in truth.class_dict(klass) for name in _CLEANING_METHODS)
        for klass in below_kind
    )


def _cleaned_kind(form_field: object) -> object | None:
    """Return the Python kind ``form_field`` cleans one value to, ``None`` when its class does not say.

    A ``TypedChoiceField`` / ``TypedMultipleChoiceField`` cleans each value through its
    ``coerce``: a class names the kind (``coerce=Decimal``), any other callable none. Every
    other field answers by its class's row in ``_CLEANED_KINDS``; a consumer field no row
    covers names none. So does a subclass defining its own cleaning below the class that names
    the kind (``_keeps_cleaning_of``): a ``DateField`` subclass whose ``clean`` returns the
    ISO text of the date it validates cleans text.
    """
    form_class: type[object] = truth.class_of(form_field)
    coercing: type[forms.Field] | None = next(
        (base for base in _COERCING_FORM_FIELDS if truth.is_subclass(form_class, base)),
        None,
    )
    entry: tuple[type[object], object] | None
    if coercing is not None:
        coerce = read_attr(form_field, "coerce", None)
        entry = (coercing, coerce if truth.is_type(coerce) else None)
    else:
        entry = truth.mro_entry(_CLEANED_KINDS, form_class)
    if entry is None or not _keeps_cleaning_of(form_class, entry[0]):
        return None
    return entry[1]


#: The packages whose form-field classes the no-value ask runs: Django's and django-filter's
#: (``_cleans_in_shipped_code``).
_SHIPPED_FORM_PACKAGES = frozenset(
    {truth.module(forms.Field).partition(".")[0], truth.module(BaseCSVField).partition(".")[0]},
)


def _is_shipped_code(obj: object) -> bool:
    """Whether the class or function ``obj`` is defined in a ``_SHIPPED_FORM_PACKAGES`` package."""
    return truth.module(obj).partition(".")[0] in _SHIPPED_FORM_PACKAGES


def _cleans_in_shipped_code(form_field: object) -> bool:
    """Whether every cleaning ``form_field`` runs is Django's or django-filter's own code.

    Each class of the form field's real MRO whose own namespace defines a cleaning method
    (``_CLEANING_METHODS``) is read for the module defining it, as
    ``filters/sets.py::_runs_shipped_filter`` reads ``filter``: every class is read, not only
    the one resolving ``clean``, since django-filter's ``BaseCSVField`` and ``BaseRangeField``
    clean each member through the classes after them. A ``TypedChoiceField`` /
    ``TypedMultipleChoiceField`` also runs its ``coerce``: a class (``coerce=int``) or a
    function shipped code defines (Django's identity default). A consumer class or
    ``coerce`` function defining its own cleaning is a parser with its own syntax; a
    ``coerce`` that is a class, a consumer's included (a ``TextChoices``), is asked, so the
    build calls it with each sample.
    """
    form_class: type[object] = truth.class_of(form_field)
    if any(truth.is_subclass(form_class, base) for base in _COERCING_FORM_FIELDS):
        coerce = read_attr(form_field, "coerce", None)
        if not truth.is_type(coerce) and not _is_shipped_code(coerce):
            return False
    return all(
        _is_shipped_code(klass)
        for klass in truth.mro(form_class)
        if any(name in truth.class_dict(klass) for name in _CLEANING_METHODS)
    )


#: The kinds ``json.JSONEncoder`` encodes without calling ``default`` (the stdlib ``json``
#: module's conversion table; ``bool`` is an ``int``, a ``tuple`` encodes as an array). Every
#: other class reaches ``default``, which raises ``TypeError`` with no encoder.
_JSON_NATIVE_KINDS: tuple[type[object], ...] = (
    str,
    int,
    float,
    list,
    tuple,
    dict,
    type(None),
)


def _refuse_kind_json_cannot_encode(
    filter_instance: Filter,
    column: ModelField,
    form_fields: tuple[object, ...],
    filterset_cls: type[FilterSet],
) -> None:
    """Refuse a filter whose form cleans a kind its ``JSONField`` cannot encode with no encoder.

    A lookup that prepares its value through the column (a subclass of Django's
    ``FieldGetDbPrepValueMixin``: ``exact``, ``gt``, ``in``, ``contains``, a key's ``exact`` /
    ``lt`` / ``in``) hands it to ``JSONField.get_db_prep_value``, which encodes it with the
    column's ``encoder``; with none that is ``json.dumps``, so a ``Decimal``, ``date``,
    ``datetime``, ``time``, ``timedelta`` or ``UUID`` raises ``TypeError`` for every request
    that sends a value, while a kind ``json.dumps`` encodes (``_JSON_NATIVE_KINDS``: a
    ``coerce=tuple`` choice's ``tuple`` is an array) is never refused. The kind is the one
    each form field cleans, read off its class (``_cleaned_kind``), not the scalar it
    publishes (a ``DurationField`` publishes ``String`` and cleans a ``timedelta``); a kind
    the class does not name (an arbitrary ``coerce``, a consumer field, a subclass
    overriding how its class cleans) is not refused. A text
    lookup (a key's ``icontains``, ``has_key``) renders the value as text and never reaches
    the encoder, and a declared encoder is trusted. A ``method=`` filter or a consumer
    ``filter`` override (``filters/sets.py::_runs_shipped_filter``) owns what its value
    means. The refusal names the filter as declared (``_declaration_of``).
    """
    from .sets import _runs_shipped_filter  # noqa: PLC0415 - import cycle

    lookup = _filterset_lookup_operand(filterset_cls, filter_instance).lookup
    if (
        not truth.is_instance(column, models.JSONField)
        or read_attr(column, "encoder", None) is not None
        or not truth.is_subclass(lookup, FieldGetDbPrepValueMixin)
        or not _runs_shipped_filter(filter_instance)
    ):
        return
    kinds = {_cleaned_kind(form_field) for form_field in form_fields}
    refused = sorted(
        truth.name(kind)
        for kind in kinds
        if kind is not None
        and kind is not strawberry.scalars.JSON
        and not any(truth.is_subclass(kind, native) for native in _JSON_NATIVE_KINDS)
    )
    if not refused:
        return
    declaration = _declaration_of(filter_instance, filterset_cls)
    raise ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} cleans "
        f"{', '.join(refused)}, which its JSONField cannot encode with no encoder; give the "
        "filter a form field cleaning text or a number (an IntegerField or FloatField "
        "field_class), a bare Filter or TypedFilter to compare the JSON value as sent, or an "
        "encoder on the column.",
    )


def _typed_by_cleaning_form(
    filter_instance: Filter,
    value_field: ModelField,
    form_fields: tuple[object, ...],
    filterset_cls: type[FilterSet],
) -> bool:
    """Whether the form fields cleaning a value of a column holding values as given type it.

    They do unless every one passes the value through (``_passes_value_through``: a bare
    ``Filter`` or ``TypedFilter`` hands the column the JSON value as sent); a kind the
    column cannot encode is refused first (``_refuse_kind_json_cannot_encode``).
    """
    if all(_passes_value_through(form_field) for form_field in form_fields):
        return False
    _refuse_kind_json_cannot_encode(filter_instance, value_field, form_fields, filterset_cls)
    return True


def _column_cleaned_scalar(
    filter_instance: Filter,
    value_field: ModelField | None,
    filterset_cls: type[FilterSet],
) -> object | None:
    """Return the scalar a package column-cleaned filter's comparison form types a value as.

    A ``ListFilter`` / ``ArrayFilter`` / ``RangeFilter`` cleans each value with the form
    field of django-filter's own ``gte`` filter for the value's column
    (``filters/base.py::_ColumnCleanedFilter``), which agrees with every column that
    converts what it is handed. Over a column holding values as given
    (``types/converters.py::holds_values_as_given``) that form, a ``Meta.filter_overrides`` entry's
    (``filter_overrides={JSONField: {"filter_class": CharFilter}}`` cleans text), types the
    value. ``None`` where the column types it: a column that converts, one django-filter
    builds no filter for (each value passes through as sent), or a form passing values
    through; and for any other filter, whose own form cleans its values.
    """
    if (
        not truth.is_instance(filter_instance, _ColumnCleanedFilter)
        or value_field is None
        or not holds_values_as_given(value_field)
    ):
        return None
    form_field = comparison_form_field(
        filterset_cls,
        value_field,
        _filterset_walked_lookup(filterset_cls, filter_instance)[0],
    )
    if form_field is None or not _typed_by_cleaning_form(
        filter_instance,
        value_field,
        (form_field,),
        filterset_cls,
    ):
        return None
    return _scalar_from_form_field(form_field)


def _form_cleaned_value_field(
    filter_instance: Filter,
    value_field: ModelField | None,
    filterset_cls: type[FilterSet],
) -> ModelField | None:
    """Return ``value_field`` when the filter's own form cleans a value of it, else ``None``.

    A column whose own scalar is ``JSON`` and that converts nothing it is handed
    (``types/converters.py::holds_values_as_given``: a ``JSONField``, its key paths
    included) compares the kind the form cleans, so the form types the leaf
    whenever it has form fields, before any other rule: a ``CharFilter`` on ``payload__n``
    takes ``String`` and compares the text ``"5"``, an ``IntegerField`` form takes ``Int``,
    a ``BooleanFilter`` takes ``Boolean``; only a form passing every value through (a bare
    ``Filter`` or ``TypedFilter``) keeps the column's ``JSON``. A kind the column cannot
    encode is refused when the schema is built (``_refuse_kind_json_cannot_encode``).

    A transform between the column and the lookup (``filters/base.py::_filterset_value_field``)
    types the leaf by its output, because django-filter builds a generated leaf's filter
    from that output (``filters/sets.py::FilterSet.filter_for_field``), so its form cleans that
    kind. A declared filter's form comes from its own class instead: a
    ``DateFilter(field_name="occurred_on", lookup_expr="year")`` binds a ``DateField``
    whatever the ``year`` output is, and an ``Int`` wire value would reach a form that
    cannot clean it. The output types the leaf only when every form field that cleans one
    published value (``_form_value_fields``) cleans the scalar django-filter's own filter
    for that output cleans (``filters/base.py::comparison_form_field``) or a subclass of it,
    or passes any value through (``_passes_value_through``): a declared ``NumberFilter`` on
    ``occurred_at__year`` cleans the ``Decimal`` the generated ``NumberFilter`` does, so it
    stays ``Int``; a declared ``DateTimeFilter`` with ``lookup_expr="date"`` cleans a
    ``datetime``, which is a ``date``, so it stays ``Date`` (Django's ``DateTimeField``
    cleans a ``date``); a bare ``Filter`` or ``TypedFilter`` (``forms.Field``) on ``year``
    hands the lookup the ``Int`` it was sent, so it stays ``Int``, while a ``CharFilter``
    cleans text and takes ``String``. Otherwise ``None``, and the caller types the value by
    that form field. Every arm whose value a declared form cleans reads it: the scalar
    catch-all, a bare ``TypedFilter``, each member of a CSV filter (a consumer ``class
    DatesInFilter(BaseInFilter, DateFilter)`` on ``year__in`` takes ``Date`` members, a
    generated ``year__in`` keeps ``Int``) and each axis of django-filter's range filters (a
    ``DateFromToRangeFilter`` on ``occurred_on__year`` takes ``Date`` axes; the range arm
    refuses one whose axes clean different kinds, ``_range_axis_scalar``). A package
    ``RangeFilter`` / ``ListFilter`` / ``ArrayFilter`` cleans each value with the form field
    of the output's own ``gte`` filter (``filters/base.py::_ColumnCleanedFilter``), so it
    agrees by construction and keeps the output (over a column holding values as given its
    arm asks that form, ``_column_cleaned_scalar``). A leaf whose value is a converting
    column (no transform, a ``method=`` filter) is unchanged, as is one whose form field is
    not built unbound or whose converting output django-filter builds no filter for (an
    index of an array of arrays keeps its array refusal); a declared leaf on its column
    whose own form and lookup answer no value of it is refused by its arm once typed
    (``_refuse_form_serving_no_value``), never here, which a request reaches too.
    """
    if value_field is None or truth.is_instance(filter_instance, _ColumnCleanedFilter):
        return value_field
    form_fields = _form_value_fields(filter_instance)
    if form_fields and holds_values_as_given(value_field):
        typed = _typed_by_cleaning_form(filter_instance, value_field, form_fields, filterset_cls)
        return None if typed else value_field
    if value_field is _filterset_model_field(filterset_cls, filter_instance):
        return value_field
    upstream = comparison_form_field(
        filterset_cls,
        value_field,
        _filterset_walked_lookup(filterset_cls, filter_instance)[0],
    )
    if not form_fields or upstream is None:
        return value_field
    compared = _scalar_from_form_field(upstream)
    if all(
        _passes_value_through(form_field)
        or (
            truth.is_type(compared)
            and truth.is_subclass(_scalar_from_form_field(form_field), compared)
        )
        for form_field in form_fields
    ):
        return value_field
    return None


def _member_list(filter_instance: Filter, value: object) -> object:
    """Return the form value a CSV leaf hands its form for two members ``value``.

    Two: django-filter's CSV ``range`` field takes exactly two, its ``in`` any number.
    """
    return normalize_input_value(filter_instance, [value, value])


def _range_bounds(filter_instance: Filter, value: object) -> object:
    """Return the two axis values a range leaf's widget reads for the bounds ``value``, ``value``."""
    patch = require_instance(
        normalize_input_value(filter_instance, {"start": value, "end": value}),
        _RangeFormPatch,
    )
    keys = require(patch.axis_keys, is_list_or_tuple)
    return [patch.get(truth.text(key)) for key in keys]


#: One value of each scalar a column's leaf is published as, in the Python kind Strawberry
#: decodes it to (``_published_samples``): a value every column of that kind holds. A hand
#: table of inputs, never of verdicts: no Django, django-filter, Strawberry or graphql-core
#: API yields a value of a scalar or of a column, and whether a value answers is asked of
#: the filter's own form and lookup (``_answers_sample``). A text scalar has no row: the
#: form parses text by its own syntax, which no finite set of text samples covers, and a
#: text column compares every kind as its text.
_SCALAR_SAMPLES: Mapping[object, tuple[object, ...]] = MappingProxyType(
    {
        int: (1,),
        BigInt: (1,),
        float: (1.0,),
        decimal.Decimal: (decimal.Decimal(1),),
        bool: (True, False),
        datetime.date: (datetime.date(2000, 1, 1),),
        datetime.datetime: (datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),),
        datetime.time: (datetime.time(12, 0),),
        uuid.UUID: (uuid.UUID(int=1),),
    },
)


def _published_samples(element: object) -> tuple[object, ...]:
    """Return values of the published ``element`` a client can send, as Strawberry decodes them.

    A choice column's enum holds every value: each member outside ``EMPTY_VALUES``, which a
    filter skips as no constraint (``_refuse_choices_off_the_column`` asks the same set). A
    scalar answers its row in ``_SCALAR_SAMPLES``; any other (text, a consumer ``SCALAR_MAP``
    entry) none, so its leaf is asked only its choice form's keys (``_asked_samples``).
    """
    if truth.is_subclass(element, enum.Enum):
        return tuple(member for member in element if enum_value(member) not in EMPTY_VALUES)
    return next(
        (samples for kind, samples in _SCALAR_SAMPLES.items() if kind is element),
        (),
    )


def _asked_samples(
    filter_instance: Filter,
    element: object,
    form_field: object,
) -> tuple[object, ...] | None:
    """Return the values the no-value ask hands the filter's form, ``None`` when it is not asked.

    A choice column's enum is every value its input carries (``_published_samples``). On a
    column without ``choices``, a form whose values are its own choices
    (``_form_choice_samples``: eager choices, Django's own ``validate`` and ``valid_value``)
    is asked each of its keys, as a client sends it (text as text; a typed scalar the form
    reads as the text the key spells, so a key no value of the column spells is asked anyway
    and builds), and a form declaring none answers no value; that ``validate`` passes each
    key and nothing else, so the probe's ``validate`` being off decides nothing for it. Any
    other form (deferred choices, a consumer ``validate`` or ``valid_value``) is asked the
    published scalar's samples with ``validate`` off; a text scalar has none (the form
    parses text by its own syntax, which no finite sample covers), nor does a consumer
    ``SCALAR_MAP`` scalar, and the leaf is not asked.
    """
    if not truth.is_subclass(element, enum.Enum):
        keys = _form_choice_samples(filter_instance, form_field)
        if keys is not None:
            return keys
    return _published_samples(element) or None


def _validates_nothing(value: object) -> None:
    """Accept any cleaned ``value``: the probe's ``validate`` (``_answers_sample``)."""
    _ = value


def _django_resolves(owner: type[object], *names: str) -> bool:
    """Whether every method ``names`` the class ``owner`` resolves is defined by Django.

    Read as ``filters/sets.py::_runs_shipped_filter`` reads ``filter``: the function the
    class's real MRO resolves (``utils/truth.py::mro_attr``, unwrapped by
    ``stored_function``), for the module that defines it.
    """
    return all(
        truth.module(truth.stored_function(truth.mro_attr(owner, name))).partition(".")[0]
        == "django"
        for name in names
    )


def _django_converts(column: ModelField) -> bool:
    """Whether Django's own code converts each value ``column`` is handed, by its own class.

    The column's class must resolve ``to_python`` and ``get_prep_value`` to Django
    (``_django_resolves``). A relation (a ``ForeignObject``, ``ForeignKey`` and
    ``OneToOneField`` included, or a ``ManyToManyField``) prepares its value through the
    fields it points at, read off its last path step (``path_infos[-1].target_fields``,
    what Django's ``RelatedLookupMixin.get_prep_lookup`` reads), so each of those is
    asked the same way, down to the concrete key columns.
    """
    if not _django_resolves(truth.class_of(column), "to_python", "get_prep_value"):
        return False
    if truth.is_instance(column, models.ForeignObject) or truth.is_instance(
        column,
        models.ManyToManyField,
    ):
        return all(_django_converts(field) for field in column.path_infos[-1].target_fields)
    return True


def _answers_sample(
    filter_instance: Filter,
    model: type[models.Model],
    form_value: object,
) -> bool:
    """Whether the filter's own form and lookup turn ``form_value`` into a predicate on ``model``.

    Asked of upstream, as a request asks it: the form field the filter's class builds (on
    ``filters/base.py::copied_filter``'s copy of the filter, which evaluates no deferred
    ``choices``) cleans the value with its and its axes' validators and ``validate`` removed,
    and the filter's own ``filter`` applies the cleaned value to a fresh queryset of
    ``model``, holding no predicate, which builds the lookup and prepares the value through
    the column (``Lookup.get_prep_lookup``) without running SQL.
    A form refusing the value (``ValidationError``; the ``AttributeError`` a temporal form
    raises stripping a kind it reads only as text; the ``TypeError`` a ``JSONField`` form
    raises decoding one; the ``decimal.InvalidOperation`` a ``coerce=Decimal`` raises for a
    key it cannot parse, which Django's ``TypedChoiceField._coerce`` leaves uncaught), a
    column refusing what the form cleaned (``filters/sets.py::_PREPARATION_REFUSALS``, what
    ``_unbindable_predicate`` reads as a value the query cannot bind), and a cleaned value
    applied as no constraint (a ``BooleanFilter``'s ``None``) answer no. A validator or a
    ``validate`` bounds which values of the kind pass (``min_value``, a slug's or an email's
    syntax, a consumer's ``validate`` reading the database), never whether the form reads the
    kind (Django reads the kind in ``to_python``), and no sample speaks for every bound, so
    neither runs and no query does. A predicate Django resolves on no queryset never reaches
    here: the set refused it when it published
    (``filters/base.py::refuse_unresolvable_lookup``).
    """
    from .sets import _PREPARATION_REFUSALS  # noqa: PLC0415 - import cycle

    probe = copied_filter(filter_instance)
    form_field = probe.field
    axes = form_field.fields if isinstance(form_field, forms.MultiValueField) else ()
    for field in (form_field, *axes):
        field.validators = []
        field.validate = _validates_nothing
    try:
        cleaned = object_result(form_field.clean, form_value)
    # ``TypedChoiceField._coerce`` turns only ``ValueError``, ``TypeError`` and
    # ``ValidationError`` into its refusal, so a ``coerce=Decimal`` key no decimal spells
    # reaches here as ``decimal.InvalidOperation``.
    except (
        ValidationError,
        AttributeError,
        TypeError,
        decimal.InvalidOperation,
    ):
        return False
    with warnings.catch_warnings():
        # A lossy preparation's warning (a ``date`` on a ``DateTimeField``) belongs to no query.
        warnings.simplefilter("ignore")
        try:
            filtered = require(probe.filter(models.QuerySet(model=model), cleaned), is_queryset)
        except _PREPARATION_REFUSALS:
            return False
    return bool(filtered.query.where)


def _refuse_form_serving_no_value(
    filter_instance: Filter,
    element: object,
    filterset_cls: type[FilterSet],
    form_value: Callable[[Filter, object], object],
) -> None:
    """Refuse a leaf typed by its column whose own form and lookup answer no value of it.

    The leaf compares its column with no transform between them, so it is published as the
    column (``_form_cleaned_value_field``) while its own form field cleans each value: a
    ``TimeFilter`` on a ``DateTimeField`` is ``DateTime`` and its ``TimeField`` cannot read a
    ``datetime``; a ``UUIDFilter`` on an ``IntegerField`` reads no integer; a
    ``DurationFilter`` on an ``IntegerField`` cleans a ``timedelta`` the column cannot
    prepare; a ``BooleanFilter`` on a ``DateField`` cleans every date to no constraint; a
    ``DateRangeFilter`` inside a CSV ``in`` or ``range`` hands its own ``filter`` a list it
    cannot look up, and a ``MultipleChoiceField`` member reads no single value. Each sample
    (``_asked_samples``: the published ``element``'s, or the keys of a choice form's own
    choices on a column without ``choices``), turned by ``form_value`` into what the arm
    hands the form (``normalize_input_value``, ``_member_list``, ``_range_bounds``), is asked
    of the form and the lookup (``_answers_sample``); a leaf answering none is a declaration
    no value of its input can serve, refused naming the column, its form field, the lookup
    and the advice. One answered sample builds, so a leaf answering some values
    (``DateFilter`` on a ``DateTimeField``, ``CharFilter`` on an integer) is never refused.

    The leaf asked is the filter the consumer wrote, on the set declaring it
    (``_declaration_of``: a ``RelatedFilter`` expansion's copy is its child filter on the
    child set). Only a consumer's declaration is asked: a declared filter and a
    ``Meta.filter_overrides`` selection (``filters/sets.py::filter_generation_provenance``),
    never a generated leaf, whose class django-filter selects for the column. A ``method=``
    filter or a consumer ``filter`` override (``filters/sets.py::_runs_shipped_filter``) owns
    what its value means, a form field any consumer class or ``coerce`` cleans
    (``_cleans_in_shipped_code``) is a consumer's parser, a model-choice form field cleans
    by querying its queryset (the probe runs no query), and a column converting in its own
    ``to_python`` / ``get_prep_value`` (a relation's target key included,
    ``_django_converts``) or a lookup preparing in its own ``get_prep_lookup``
    (``_django_resolves``) is consumer code bounding which values pass, so none is asked. A
    transform, a column holding values as given, a package column-cleaned filter and a null
    test type their leaf on other arms.
    """
    from .sets import (  # noqa: PLC0415 - import cycle
        _FRAMEWORK_GENERATED_ORIGINS,
        _runs_shipped_filter,
        filter_generation_provenance,
    )

    provenance = filter_generation_provenance(filter_instance)
    if provenance is not None and provenance.origin in _FRAMEWORK_GENERATED_ORIGINS:
        return
    declaration = _declaration_of(filter_instance, filterset_cls)
    declared = declaration.declared
    owner = declaration.filterset
    column = _filterset_value_field(owner, declared)
    operand = _filterset_lookup_operand(owner, declared)
    if (
        column is None
        or truth.is_instance(declared, _ColumnCleanedFilter)
        or column is not _filterset_model_field(owner, declared)
        or holds_values_as_given(column)
        or operand.null_test
        or not _runs_shipped_filter(declared)
        or not _django_converts(column)
        or (operand.lookup is not None and not _django_resolves(operand.lookup, "get_prep_lookup"))
    ):
        return
    form_field = _declared_form_field(declared)
    form_fields = _value_fields_of(form_field)
    model = _filterset_model(owner)
    if (
        model is None
        or not form_fields
        or any(isinstance(field, forms.ModelChoiceField) for field in form_fields)
        or not all(_cleans_in_shipped_code(field) for field in form_fields)
    ):
        return
    samples = _asked_samples(declared, element, form_field)
    if samples is None or any(
        _answers_sample(declared, model, form_value(declared, sample)) for sample in samples
    ):
        return
    form_kind = ", ".join(sorted({truth.kind(form_field) for form_field in form_fields}))
    raise ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} is published as "
        f"{_field_label(column)} values, but its own form field ({form_kind}) and lookup "
        f"{truth.render(declared.lookup_expr)} answer no value of that column, so every value "
        "of its input would be refused or would constrain nothing (match every row); filter "
        "a transform of the column whose output its form cleans (a TimeFilter on "
        '`field_name="<column>__time"`), declare a filter class whose form cleans the '
        "column's kind, or read the value in `method=`.",
    )


def _is_hidden_flat_copy(filterset_cls: type[FilterSet], filter_instance: Filter) -> bool:
    """Whether ``HIDE_FLAT_FILTERS`` keeps ``filter_instance`` out of ``filterset_cls``'s input.

    A ``RelatedFilter`` expansion's copy of one of the set's own declarations
    (``filters/sets.py::_is_flat_copy``) is hidden when the key is set (its truthiness is
    this consumer's own semantics); every other filter of the set's table is published.
    The input builder (``_build_input_fields``) and the served-leaf audit
    (``_refuse_unsealable_served_leaves``) read the one answer, so the set the build checks
    is the set the schema publishes.
    """
    from .sets import _is_flat_copy  # noqa: PLC0415 - import cycle

    return bool(hide_flat_filters_setting()) and _is_flat_copy(filterset_cls, filter_instance)


def _served_reach(
    served: Iterable[type[FilterSet]],
) -> Iterator[tuple[type[FilterSet], type[FilterSet], tuple[str, ...]]]:
    """Yield ``(root, set, through)`` for each set ``served`` reaches through a ``RelatedFilter``.

    Every set a served set reaches is served too, as its nested branch, through a branch
    the set's published filter table still holds (the declared ``RelatedFilter`` itself or
    one held under its declared name, never an expansion copy) or a flat copy the schema
    publishes (each copy's child set, ``ChildProjection.filterset``, unless
    ``HIDE_FLAT_FILTERS`` hides the copy: ``_is_hidden_flat_copy``, the input builder's own
    rule); a ``get_filters`` override that drops both serves no request through the branch.
    Breadth first, each set once, the served sets first, each yielded before its branches
    are read, so a caller refusing a set's leaf stops before a later set builds: ``root``
    is the served set it was first reached from and ``through`` the ``RelatedFilter``
    attributes crossed, ``<Set>.<attribute>`` outermost first (empty for a served set).
    """
    from .sets import _expansion_record  # noqa: PLC0415 - import cycle

    # The list grows while it is walked.
    pending: list[tuple[type[FilterSet], type[FilterSet], tuple[str, ...]]] = [
        (filterset_cls, filterset_cls, ()) for filterset_cls in served
    ]
    seen = {filterset_cls for _root, filterset_cls, _through in pending}
    for root, filterset_cls, through in pending:
        yield root, filterset_cls, through
        table = filterset_cls._filter_table()
        heads = {
            name: leaf
            for name, leaf in table.items()
            if truth.is_instance(leaf, RelatedFilter) and _expansion_record(leaf) is None
        }
        branches: list[tuple[type[FilterSet] | None, str]] = [
            (record.filterset, record.branch)
            for leaf in table.values()
            if (record := _expansion_record(leaf)) is not None
            and not _is_hidden_flat_copy(filterset_cls, leaf)
        ]
        related_filters = declaration_map(
            truth.static_attr(filterset_cls, "related_filters", OrderedDict[str, object]()),
            RelatedFilter,
        )
        branches.extend(
            (related_filter.filterset, name)
            for name, related_filter in related_filters.items()
            if name in heads or any(head is related_filter for head in heads.values())
        )
        for child, branch in branches:
            if child is not None and child not in seen:
                seen.add(child)
                pending.append(
                    (root, child, (*through, f"{truth.name(filterset_cls)}.{branch}")),
                )


def _refuse_unsealable_served_leaves(served: Iterable[type[FilterSet]]) -> None:
    """Refuse a leaf of a connection-served set whose predicate holds a class the seal refuses.

    A ``DjangoConnectionField`` (root, or the ``<relation>Connection`` a Relay type grows)
    applies its ``filter:`` argument inside the visibility boundary
    (``utils/querysets.py::apply_filterset_sync``), whose seal admits only Django's own node
    classes (``utils/querysets.py::_type_is_genuinely_django``, spec-045 Decision 2). A leaf
    whose path resolves to any other transform or lookup class (a project ``Transform`` or
    ``Lookup``, a ``Func``-based transform, a subclass of a Django class, a third-party
    app's lookup; registered on a field class, on an instance, or on a transform) is
    published on that argument yet refused on every request, so the build refuses it. The
    classes asked are the ones Django's query resolves for the leaf's ``field_name`` and
    ``lookup_expr`` (``filters/base.py::_filterset_lookup_operand``, the ``get_transform`` /
    ``get_lookup`` walk), each asked of the seal's own predicate, so the build and the
    request cannot disagree.

    Every set a served set reaches through a ``RelatedFilter`` is served too, as its nested
    branch (``_served_reach``, the reach the GlobalID audit reads too). Each reached set's
    own filter table is asked, its expansion copies skipped
    (``filters/sets.py::_expansion_record``), so every leaf is judged once, on the set that
    declares it, and named there with the ``RelatedFilter`` path it was reached through. A
    leaf whose ``filter`` is consumer code on its own set (a ``method=`` filter, a
    ``filter`` override, a ``filter`` held on the instance:
    ``filters/sets.py::_runs_shipped_filter``) owns its query, and a path the model alone
    cannot resolve (a queryset annotation) has no walk; the seal judges both per request. A
    predicate Django resolves on no queryset never reaches here: its set refused it when it
    published (``filters/base.py::refuse_unresolvable_lookup``). A set no connection serves,
    applied from the project's own resolver, is never sealed and is not asked.
    """
    from django_strawberry_framework.utils.querysets import (  # noqa: PLC0415 - import cycle
        _type_is_genuinely_django,
    )

    from .sets import _expansion_record, _runs_shipped_filter  # noqa: PLC0415 - import cycle

    for _root, filterset_cls, through in _served_reach(served):
        table = filterset_cls._filter_table()
        for name, leaf in table.items():
            if (
                truth.is_instance(leaf, RelatedFilter)
                or _expansion_record(leaf) is not None
                or not _runs_shipped_filter(leaf)
            ):
                continue
            node_types = _filterset_lookup_operand(filterset_cls, leaf).node_types
            refused = next((t for t in node_types if not _type_is_genuinely_django(t)), None)
            if refused is not None:
                raise _unsealable_leaf_refusal(leaf, name, filterset_cls, through, refused)


def _unsealable_leaf_refusal(
    leaf: Filter,
    name: str,
    filterset_cls: type[FilterSet],
    through: tuple[str, ...],
    refused: type[object],
) -> ConfigurationError:
    """Build the refusal of a served leaf whose predicate holds ``refused``, a class not Django's own.

    ``leaf`` is ``name`` on ``filterset_cls``, the set declaring it, reached from the served
    set across the ``RelatedFilter`` attributes ``through`` (empty for the served set's own).
    """
    from .sets import _LeafDeclaration  # noqa: PLC0415 - import cycle

    attribute = f"{truth.name(filterset_cls)}.{name}" if through else None
    declaration = _LeafDeclaration(leaf, attribute, through, filterset_cls)
    return ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} with lookup "
        f"{truth.render(leaf.lookup_expr)} resolves to "
        f"{truth.module(refused)}.{truth.qualname(refused)}, which is not one of Django's own "
        "lookup or transform classes. A connection serves this filter (a "
        "DjangoConnectionField, or the <relation>Connection a Relay type grows for a to-many "
        "relation) and runs its filter: argument inside the visibility boundary, which admits "
        "only Django's own lookup and transform classes, so every request naming the filter "
        "would be refused. Filter through a Django class (registered under any lookup name), "
        "apply a FilterSet no connection serves from a resolver of your own (FilterInput[...] "
        'and apply_sync), or set Meta.relation_shapes = {"<relation>": "list"} on the type '
        "whose to-many relation grows the connection.",
    )


def _range_axis_scalar(filter_instance: Filter, filterset_cls: type[FilterSet]) -> object:
    """Return the scalar both axes of a range filter's own form clean, the build refusing two.

    The range input carries one scalar for both bounds (``_build_range_input_class``:
    ``start`` and ``end`` of one type, under one generated name per value path), so a
    ``MultiValueField`` whose axes clean different kinds (``fields=(forms.DateField(),
    forms.IntegerField())``) has no type that each bound's form can clean, and is a
    ``ConfigurationError`` naming the filter as declared (``_declaration_of``).
    """
    scalars = {_scalar_from_form_field(axis) for axis in _form_value_fields(filter_instance)}
    if len(scalars) == 1:
        return scalars.pop()
    declaration = _declaration_of(filter_instance, filterset_cls)
    kinds = ", ".join(sorted(truth.name(scalar) for scalar in scalars))
    raise ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} cleans its two "
        f"range axes as different kinds ({kinds}), and a range input carries one type for "
        "both bounds; give both axes form fields that clean one kind.",
    )


def _model_choice_identity_annotation(
    filter_instance: Filter,
    filterset_cls: type[FilterSet] | None,
) -> object:
    """Type one value of a consumer model-choice filter from the column its form cleans.

    The column is the ``to_field_name`` field (the primary key when unset) of the model
    its form field looks values up in (``filters/base.py::model_choice_model``: the
    ``queryset`` model, or for a callable ``queryset`` the model the ``field_name`` path
    ends on), read through the shared ``SCALAR_MAP`` lookup. The filter keeps its own
    form field, so its ``queryset`` still validates every value. Both refusals name the
    filter as declared (``_declaration_of``), whose own ``queryset``, ``field_name`` and
    ``to_field_name`` are the ones read.
    """
    declaration = _declaration_of(filter_instance, filterset_cls)
    subject = _declaration_subject(declaration, filterset_cls)
    model = model_choice_model(declaration.filterset, declaration.declared)
    if model is None:
        if callable(read_attr(declaration.declared, "queryset", None)):
            raise ConfigurationError(
                f"{subject} has a callable queryset, which names its model only once a request "
                "arrives, and its field_name is no path of fields on the FilterSet model to "
                "read that model from, so there is no column to type its input from. Pass a "
                "model queryset, or point field_name at the field the filter compares (the "
                "relation, or the to_field_name column past it).",
            )
        raise ConfigurationError(
            f"{subject} has no queryset and its field_name names no relation on the FilterSet "
            "model, so there is no column to type its input from. Pass a model queryset.",
        )
    to_field_name = declaration.declared.extra.get("to_field_name")
    column = _model_identity_column(model, to_field_name)
    if column is None:
        if callable(read_attr(declaration.declared, "queryset", None)):
            source = (
                "the model its field_name path ends on (a callable queryset names none at build)"
            )
            remedy = "Pass a model queryset, name a column of that model,"
        else:
            source = "the model its form field looks each value up in"
            remedy = "Name a column of that model,"
        raise ConfigurationError(
            f"{subject} has to_field_name {to_field_name!r}, which names no column of "
            f"{truth.qualname(model)}, {source}, so there is no column to type its input "
            f"from. {remedy} or drop to_field_name to look values up by primary key.",
        )
    return _scalar_from_model_field(column, filter_instance, filterset_cls)


def _choice_enum_from_filter(
    filter_instance: Filter,
    type_name: str,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None = None,
) -> type[enum.Enum]:
    """Derive a Strawberry enum from the ``choices`` of the model field a choice filter reads.

    The enum comes only from the backing model field's ``choices``, through
    ``types/converters.py::convert_choices_to_enum``, so it is shared with any sibling
    ``DjangoType`` reading the same column; the filter's own ``choices`` never feed the enum.
    Per spec-027 Decision 4, a choice filter with no backing field declaring ``choices``
    raises ``ConfigurationError`` naming the declared filter (``_declaration_of``): a
    ``ChoiceFilter`` on a plain column, a transform's output (``lookup_expr="year"``) or a
    ``method=`` path, and django-filter's ``ChoiceFilter`` subclasses ``AllValuesFilter``
    and ``DateRangeFilter``, whose choices are the column's distinct values or fixed
    date-range keys. Over a column declaring ``choices``, a filter whose own form field
    accepts none of the enum's members is refused too (``_refuse_choices_off_the_column``).

    ``model_field`` is threaded as a parameter rather than stashed on
    the filter instance - keeps the filter stateless and avoids the
    "side-effect on a filter during input-class construction" trap.
    """
    # Local import to avoid a top-level cycle through ``types.converters``.
    from django_strawberry_framework.types.converters import convert_choices_to_enum  # noqa: PLC0415 - import cycle

    # A reverse ``ForeignObjectRel`` declares no ``choices``, so it fails the same guard.
    if not is_concrete_field(model_field) or not getattr(model_field, "choices", None):
        raise _no_choices_refusal(filter_instance, model_field, filterset_cls)
    choice_enum = convert_choices_to_enum(model_field, type_name)
    _refuse_choices_off_the_column(filter_instance, model_field, choice_enum, filterset_cls)
    return choice_enum


def _declaration_subject(
    declaration: _LeafDeclaration,
    filterset_cls: type[FilterSet] | None,
) -> str:
    """Return ``<owner>: <Class> on '<field_name>'<route>``, a refusal's subject for a leaf."""
    return (
        f"{declaration.owner(filterset_cls)}: {declaration.kind} on "
        f"{truth.render(declaration.declared.field_name)}{declaration.route}"
    )


def _no_choices_refusal(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None,
) -> ConfigurationError:
    """Build the refusal for a choice filter reading its value off no field declaring ``choices``.

    The reason names what the leaf is typed from: no model field (a ``method=`` path, a path
    no column of the model answers), a transform's output, which is bound to no model
    (``lookup_expr="year"`` compares an integer, which declares no ``choices`` whatever its
    column declares), or a column; only the column can take ``choices``, so only its reason
    carries the advice to declare them.
    """
    declaration = _declaration_of(filter_instance, filterset_cls)
    if model_field is None:
        reason, declare = "reads no model field", ""
    elif truth.is_type(read_attr(model_field, "model", None)):
        reason = f"reads {_field_label(model_field)}, which declares no `choices`"
        declare = (
            "declare `choices` on the column it filters (a `choices=` list of pairs, or a "
            "`TextChoices` / `IntegerChoices` class's `.choices`), or "
        )
    else:
        reason = (
            f"reads a transform's output ({truth.kind(model_field)}), which declares no "
            "`choices` whatever its column declares"
        )
        declare = ""
    return ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} {reason}, so no choice enum types "
        f"its input (the filter's own `choices` never feed the enum); {declare}filter the "
        "column through a non-choice filter (`CharFilter`, `NumberFilter`, "
        "`DateFromToRangeFilter`, its lookups in Meta.fields, or `CharFilter(method=...)` for "
        "a method filter).",
    )


def _refuse_choices_off_the_column(
    filter_instance: Filter,
    model_field: ModelField,
    choice_enum: type[enum.Enum],
    filterset_cls: type[FilterSet] | None,
) -> None:
    """Refuse a filter publishing ``choice_enum`` whose own form field accepts none of its members.

    The input carries a member's value (``normalize_input_value``) to the filter's own form
    field, which validates it against the filter's own ``choices`` (django-filter never reads
    the column's for a declared filter). The form field is asked through Django's own
    comparison (``ChoiceField.valid_value``) for each member value outside django-filter's
    ``EMPTY_VALUES``, which a filter skips as no constraint, so an empty member is never
    accepted as a choice. Accepting one member builds, as a subset of the column's ``choices``
    does (each member off it answers ``invalid_choice``, as the multiple-choice family's
    does); accepting none (``DateRangeFilter``'s fixed date-range keys, a
    ``choices=`` list sharing no value with the column) is a declaration no value of its
    input can serve, so it is refused naming the column. A filter whose form field is no
    ``ChoiceField`` (a ``CharFilter`` over a choices column), a model-choice field, a field
    built only per request (``AllValuesFilter``, ``_declared_form_field``) and ``choices``
    evaluated per form build are not asked: this check never evaluates a callable, lazy
    (``lazy()`` promise, ``SimpleLazyObject``), choice-iterator or ``QuerySet`` ``choices``,
    which may read the database (``filters/base.py::defers_choices``); a ``Choices`` class is
    asked.
    """
    form_field = _eager_choice_form_field(filter_instance, _declared_form_field(filter_instance))
    if form_field is None:
        return
    checked = [value for value in map(enum_value, choice_enum) if value not in EMPTY_VALUES]
    if not checked or any(form_field.valid_value(value) for value in checked):
        return
    declaration = _declaration_of(filter_instance, filterset_cls)
    raise ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} publishes the choice enum of "
        f"{_field_label(model_field)}, but its own form field accepts none of that column's "
        "`choices`, so every value of its input would be refused (a `DateRangeFilter`'s "
        "fixed date-range keys are no column's choices); give the filter `choices` drawn "
        "from the column's (`choices=<Model>.<Choices>.choices`, or a subset of them), or "
        "filter that column through a non-choice filter (`CharFilter`, `NumberFilter`, "
        "`DateFromToRangeFilter`, its lookups in Meta.fields, or `CharFilter(method=...)` for "
        "a method filter).",
    )


def _eager_choice_form_field(
    filter_instance: Filter,
    form_field: object,
) -> forms.ChoiceField | None:
    """Return the built ``form_field`` as a ``ChoiceField`` whose choices the build may read.

    ``None`` when it is no ``ChoiceField`` (the multiple-choice and typed kin are), when it
    is a model-choice field (its choices are a queryset), and when the filter's ``choices``
    are deferred (``defers_choices``): the form field is built lazily, so only reading its
    ``choices`` would evaluate them.
    """
    if (
        defers_choices(filter_instance)
        or not isinstance(form_field, forms.ChoiceField)
        or isinstance(form_field, forms.ModelChoiceField)
    ):
        return None
    return form_field


#: The ``ChoiceField`` methods deciding which values its form accepts (``_validates_its_keys``).
_CHOICE_VALIDATION_METHODS: tuple[str, ...] = ("validate", "valid_value")


def _validates_its_keys(form_field: forms.ChoiceField) -> bool:
    """Whether ``form_field`` accepts its own choices' keys and nothing else, as Django's does.

    Its class's ``validate`` and ``valid_value`` (``_CHOICE_VALIDATION_METHODS``), each the
    function its real MRO resolves, are read for the module defining them, as
    ``_django_resolves`` reads a method: a consumer override accepting values off its keys
    widens which values pass, so the keys do not stand in for it.
    """
    form_class = truth.class_of(form_field)
    return all(
        _is_shipped_code(truth.stored_function(truth.mro_attr(form_class, name)))
        for name in _CHOICE_VALIDATION_METHODS
    )


def _form_choice_samples(filter_instance: Filter, form_field: object) -> tuple[object, ...] | None:
    """Return the values the filter's built choice ``form_field`` accepts, ``None`` for any other.

    Django's and django-filter's ``ChoiceField`` ``validate`` accepts its own choices' keys and
    nothing else, so its values are those keys (``flatten_choices`` opens Django's option
    groups); django-filter's empty and null choices included, since whether a key constrains
    anything is asked of the filter's own ``filter`` (``_answers_sample``: a scalar ``""`` is
    skipped, a CSV member ``""`` compares). ``flatten_choices`` is handed an iterator over the
    choices, as ``valid_value`` iterates them: django-filter's ``ChoiceIterator`` answers the
    truthiness ``flatten_choices`` asks with the size of the choices it wraps, which an
    iterator declared as ``choices`` has none of. ``None`` where the form is no
    ``ChoiceField`` whose choices the build may read (``_eager_choice_form_field``) or one
    whose ``validate`` / ``valid_value`` is a consumer's (``_validates_its_keys``).
    """
    choice_field = _eager_choice_form_field(filter_instance, form_field)
    if choice_field is None or not _validates_its_keys(choice_field):
        return None
    pairs = list_of(object_result(flatten_choices, object_result(iter, choice_field.choices)))
    return tuple(list_of(pair)[0] for pair in pairs)


def _unnameable_lookup_refusal(
    filter_instance: Filter,
    lookup: str,
    filterset_cls: type[FilterSet],
) -> ConfigurationError:
    """Build the refusal for a leaf whose lookup is no GraphQL field name.

    Each lookup of an operator bag is published as an input field named by it, so a
    ``lookup_expr`` opening on an ``ArrayField`` index (``0``) or slice (``0_2``) names
    none. The same transform spelled in the ``field_name`` (``<column>__0``) is published
    under the filter's own name.
    """
    declaration = _declaration_of(filter_instance, filterset_cls)
    return ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} "
        f"publishes lookup {truth.render(lookup)}, which is no GraphQL field name. Spell an "
        "index or slice in field_name (`<column>__0`, `<column>__0_2`) and name the lookup "
        "in lookup_expr.",
    )


#: The ``ArrayField`` lookups whose operand is an array of the column's elements, so a list
#: input of the element type carries it (``_array_element_column``).
_ARRAY_ELEMENT_LIST_LOOKUPS = frozenset(
    {
        "exact",
        "contains",
        "contained_by",
        "overlap",
    },
)


def _array_column_refusal(
    filter_instance: Filter,
    model_field: object,
    filterset_cls: type[FilterSet] | None,
    lookup: str | None = None,
) -> ConfigurationError:
    """Build the refusal for a filter whose input cannot carry its ``ArrayField`` lookup's operand.

    A scalar, typed, choice-list or catch-all filter hands the ORM one element where the
    column compares a whole array, and an ``in`` compares the column with each of several
    arrays, so an element-typed input would build and then fail every value at the
    database. A transform spelled in the ``field_name`` (``<column>__len``, an index
    ``<column>__0``, a slice ``<column>__0_2``) or a ``len`` in the ``lookup_expr`` never
    reaches it: its leaf is typed from the transform's output
    (``filters/base.py::_filterset_value_field``); an index or slice opening the
    ``lookup_expr`` names no input field (``_unnameable_lookup_refusal``). ``lookup``
    names what the filter applies when its ``lookup_expr`` does not (a ``RangeFilter``'s
    ``range``).

    A null test (``isnull``, read as the catch-all reads it:
    ``filters/base.py::_filterset_lookup_operand``) on a list, CSV, choice or typed filter
    is refused too, since each publishes the column's elements where the test takes one
    ``Boolean``; its advice names the ``BooleanFilter`` the catch-all types ``Boolean``
    (django-filter's own filter for a generated ``isnull``). Every other refused lookup's
    advice names the ``ArrayFilter`` lookups that take one array of the column's elements.
    """
    declaration = _declaration_of(filter_instance, filterset_cls)
    applied = lookup if lookup is not None else getattr(filter_instance, "lookup_expr", None)
    if lookup is None and _filterset_lookup_operand(filterset_cls, filter_instance).null_test:
        remedy = (
            "a null test takes one Boolean, which this filter does not publish. Declare a "
            "BooleanFilter with lookup_expr 'isnull'."
        )
    else:
        remedy = (
            "only exact, contains, contained_by and overlap take one array of the column's "
            "elements. Declare an ArrayFilter with one of those lookup_expr values."
        )
    return ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} "
        f"has no input type for lookup {truth.render(applied)} on the ArrayField column "
        f"{_field_label(model_field)}: {remedy}",
    )


def _array_element_column(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None,
) -> ModelField | None:
    """Return the column a list arm types each member from: an ``ArrayField``'s element.

    A list input carries an ``ArrayField`` lookup only when the lookup's operand is an
    array of the column's elements (``_ARRAY_ELEMENT_LIST_LOOKUPS``); then each member is a
    value of ``base_field`` (``utils/_array_field.py::array_element_field``), the column it is
    cleaned by (``filters/base.py::_column_form_field``) and the read side converts
    (``types/converters.py::convert_scalar``), so element ``choices`` give the enum the column's
    ``DjangoType`` shares and the array's own ``choices`` are never read. A nested array is
    refused by ``types/converters.py::refuse_nested_array``; any other lookup by
    ``_array_column_refusal``. Every other column is returned as given.
    """
    element = array_element_field(model_field)
    if element is None:
        return model_field
    if getattr(filter_instance, "lookup_expr", None) not in _ARRAY_ELEMENT_LIST_LOOKUPS:
        raise _array_column_refusal(filter_instance, model_field, filterset_cls)
    refuse_nested_array(model_field, element)
    return element


def _element_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    owner_definition: DjangoTypeDefinition | None,
    filterset_cls: type[FilterSet],
) -> object:
    """Single-element Strawberry type with the MODEL FIELD as source of truth.

    A backing model field's choices become the shared GraphQL enum and its
    column type becomes the scalar (including the ``BigInt`` scalar for 64-bit
    columns). Where a transform stands between the column and the lookup, in the
    ``lookup_expr`` (a generated ``year`` / ``year__in`` / ``date`` leaf) or the
    ``field_name`` (``occurred_at__year``, an ``ArrayField`` index ``counts__0``), the
    field is the last transform's output the leaf builder passes
    (``filters/base.py::_filterset_value_field``). The ``django-filter`` form
    field types the value only where the caller passes no field: a custom
    ``method=`` filter with no backing model field, a path that resolves to no
    column of the FilterSet model (a ``FilteredRelation`` alias only the filter's
    queryset holds), a declared filter whose own form cleans another kind than
    the field (``_form_cleaned_value_field``: a ``DateFilter`` with
    ``lookup_expr="year"`` is ``Date``), a filter over a ``JSON``-scalar column that converts
    nothing it is handed whose form does not pass values through (a ``CharFilter`` on a ``JSONField`` key
    is ``String``), and a ``method=`` filter named ``isnull`` whose form cleans its own
    kind (no column is its operand). Each of those reads the form through
    ``FORM_FIELD_SCALARS`` (``_scalar_from_form_field``). Everywhere else the field wins, since
    ``django-filter``'s ``NumberFilter`` form (a ``DecimalField``) would mis-type
    integer columns and a CSV ``in`` over a choice column would collapse to ``str``.
    Callers that need a different shape for a specific lookup (Django's ``isnull``
    is always boolean) handle that before calling this.

    An ``ArrayField`` column reaches this only as its element column, which the list arms
    pass after ``_array_element_column`` admits the lookup; any other arm or lookup over an
    ``ArrayField`` column is refused here (``_array_column_refusal``), as the choice and range
    arms refuse it before their own reads, since no input of the element type, or a list of
    it, carries that lookup's operand. A catch-all null test never reaches it (``bool``).

    One lookup-driven arm comes first: a generated text-pattern leaf on a
    non-text column (``FilterSet.filter_for_lookup`` gives it ``TextPatternFilter``)
    is ``str``, never the column's scalar or choice enum, because the pattern is
    matched against the column's text rendering. A declared filter or a
    ``Meta.filter_overrides`` selection keeps the column-driven type; its arm
    refuses one whose own form and lookup answer no value of that type
    (``_refuse_form_serving_no_value``).

    Known contract limit: a custom ``method=`` filter has no backing
    ``model_field``, so its element type is inferred from the
    ``django-filter`` form field and a CSV/list ``method=`` filter therefore
    yields ``list[str]`` even when the column it ultimately queries is an
    ``int``. To get a typed element on a method filter, back it with a model
    field (``field_name=``) or declare the input annotation explicitly.
    """
    scalar = _element_scalar(filter_instance, model_field, filterset_cls)
    if scalar is not None:
        return scalar
    type_name = _enum_prefix(owner_definition, filterset_cls)
    return _choice_enum_from_filter(filter_instance, type_name, model_field, filterset_cls)


def _element_scalar(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet],
) -> object | None:
    """Return the scalar ``_element_annotation`` publishes, ``None`` for a choice column's enum.

    Builds nothing, so ``publishes_json_value`` asks it at request time.
    """
    if truth.is_instance(filter_instance, TextPatternFilter):
        return str
    if array_element_field(model_field) is not None:
        raise _array_column_refusal(filter_instance, model_field, filterset_cls)
    if model_field is not None and getattr(model_field, "choices", None):
        return None
    if model_field is not None:
        return _scalar_from_model_field(model_field, filter_instance, filterset_cls)
    form_field = _declared_form_field(filter_instance)
    return (
        _scalar_from_form_field(form_field)
        if form_field is not None
        else _scalar_from_model_field(model_field, filter_instance, filterset_cls)
    )


def _catchall_element(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet],
    element: Callable[[ModelField | None], object],
) -> object:
    """Type one value of a catch-all leaf: ``bool`` for a null test, else ``element`` of its field.

    A ``method=`` filter is typed from its model column, else from the form field its class
    builds; one with no column whose ``field`` builds none on the unbound declaration raises
    (``_refuse_method_without_form_field``, spec-027 Decision 4). ``isnull`` is a boolean
    predicate regardless of the column type, past a transform too (``year__isnull``): the
    value field is irrelevant there. A ``method=`` filter's method applies no lookup of the
    filter's, so a form that cleans its own kind types it, whatever the column
    (``NumberFilter(field_name="name", lookup_expr="isnull", method=...)`` takes a number);
    one passing any value through, or building none unbound, keeps ``Boolean``. Any other
    leaf's element is the field its form cleans a value of (``_form_cleaned_value_field``).
    ``element`` is ``_element_annotation`` for the published input and ``_element_scalar``
    for ``publishes_json_value``.
    """
    _refuse_method_without_form_field(filter_instance, model_field, filterset_cls)
    if _filterset_lookup_operand(filterset_cls, filter_instance).null_test:
        if read_attr(filter_instance, "method", None) is None or all(
            _passes_value_through(field) for field in _form_value_fields(filter_instance)
        ):
            return bool
        return element(None)
    return element(_form_cleaned_value_field(filter_instance, model_field, filterset_cls))


def publishes_json_value(filter_instance: Filter, filterset_cls: type[FilterSet]) -> bool:
    """Whether one value of ``filter_instance`` is published as ``JSON``, so an object is a value.

    Asks the arms of ``convert_filter_to_input_annotation`` that type one value through
    ``_element_annotation`` (a bare ``TypedFilter`` and the catch-all), dispatched on the same
    kind table, for the scalar alone (``_element_scalar``: no choice enum is built); every
    other arm publishes no ``JSON`` value. ``filters/sets.py::FilterSet._leaf_form_data``
    reads it: an object sent to such a leaf (a pass-through ``TypedFilter`` on a ``JSONField``
    key, a ``method=`` filter whose form is a ``forms.JSONField``) is one JSON value, bound
    under its one form-data key.
    """
    model_field = _filterset_value_field(filterset_cls, filter_instance)

    def _no_json(_filter: Filter) -> object:
        return None

    def _typed(matched: Filter) -> object:
        value_field = _form_cleaned_value_field(matched, model_field, filterset_cls)
        return _element_scalar(matched, value_field, filterset_cls)

    def _catchall(matched: Filter) -> object:
        return _catchall_element(
            matched,
            model_field,
            filterset_cls,
            lambda field: _element_scalar(matched, field, filterset_cls),
        )

    published = convert_with_mro(
        filter_instance,
        isinstance_prechecks=_filter_input_prechecks(
            _no_json,
            _no_json,
            _no_json,
            _no_json,
            _no_json,
            _no_json,
            _no_json,
            _no_json,
            _typed,
            _no_json,
            _no_json,
            _catchall,
        ),
        scalar_registry={},
        fallthrough_error_factory=_unexpected_filter_dispatch,
    )
    return truth.is_among(published, (strawberry.scalars.JSON,))


# ---------------------------------------------------------------------------
# Public converter pair
# ---------------------------------------------------------------------------


# Most-specific-first filter-class order. Convert and normalize both walk this
# via ``convert_with_mro`` so a new primitive cannot be typed on one ladder and
# coerced on the other (spec-055 C3). The consumer model-choice pair sits after
# the package relation primitives and before ``BaseCSVFilter`` (its ``in``
# wrapper is both) and ``ChoiceFilter`` (which ``ModelChoiceFilter``
# subclasses). ``MultipleChoiceFilter`` (with django-filter's
# ``TypedMultipleChoiceFilter`` / ``AllValuesMultipleFilter``) is last before the
# catch-all, so every class that is also another kind keeps that kind's arm: a
# generated ``in`` wrapper around it the CSV arm, the package's GlobalID and
# consumer model-choice subclasses theirs, and a consumer class pairing it with a
# range, list, array or choice filter that filter's.
# A bare ``TypedFilter`` (List / Array / Range already matched) is typed as one
# element, so normalize hands it the scalar the ChoiceFilter and catch-all arms
# hand theirs, never the multiple-choice list a class pairing it with
# ``MultipleChoiceFilter`` would otherwise reach. Last entry is ``object`` (the
# original ``else``): convert's method-filter / ``isnull`` / scalar arm,
# normalize's unwrap. A duck-typed non-``Filter`` still reaches that arm, so a
# malformed filter object is rejected with a typed ``ConfigurationError``.
_FILTER_INPUT_KIND_TYPES: tuple[type[object] | tuple[type[object], ...], ...] = (
    GlobalIDMultipleChoiceFilter,
    GlobalIDFilter,
    RelationPkMultipleFilter,
    RelationPkFilter,
    (ModelMultipleChoiceFilter, ModelChoiceFilter),
    BaseCSVFilter,
    (RangeFilter, _DjangoRangeFilter),
    (ListFilter, ArrayFilter),
    TypedFilter,
    (ChoiceFilter, TypedChoiceFilter),
    MultipleChoiceFilter,
    object,
)


def _filter_input_prechecks(
    *handlers: Callable[[Filter], object],
) -> list[tuple[type[object] | tuple[type[object], ...], Callable[[Filter], object]]]:
    """Zip the shared kind order with per-pass handlers.

    ``zip(..., strict=True)`` fails loud if convert or normalize forgets a
    handler when the kind table grows.
    """
    return list(zip(_FILTER_INPUT_KIND_TYPES, handlers, strict=True))


def _unexpected_filter_dispatch(obj: object) -> ConfigurationError:
    """Fallthrough factory for the filter-input ``convert_with_mro`` riders.

    Last precheck is ``object`` (the catch-all), so a real dispatch
    never reaches here, and no handler returns ``MRO_CONTINUE``. The factory
    keeps ``convert_with_mro``'s raising contract all the same.
    """
    return ConfigurationError(
        f"internal: filter input dispatch reached fallthrough for {truth.render(obj)}",
    )


def _refuse_method_without_form_field(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None,
) -> None:
    """Refuse a ``method=`` filter with no model field whose class builds no form field unbound.

    ``model_field`` is the field the caller types the leaf from
    (``filters/base.py::_filterset_value_field``); over one, the arm types the leaf from that
    column (a ``method=`` filter keeps its column), whether or not the form field is built
    unbound: an ``AllValuesMultipleFilter`` reads the per-request ``model`` to build its
    field, so unbound it builds none, and over a column its element is the column's while the
    form field built per request validates each value before the method runs. With no model
    field and no form field, nothing types the value. The refusal names the filter as
    declared (``_declaration_of``).
    """
    method = read_attr(filter_instance, "method", None)
    if (
        method is None
        or model_field is not None
        or _declared_form_field(filter_instance) is not None
    ):
        return
    declaration = _declaration_of(filter_instance, filterset_cls)
    raise ConfigurationError(
        f"{declaration.owner(filterset_cls)}: {declaration.kind}(method={truth.render(method)}) "
        f"on {truth.render(declaration.declared.field_name)}{declaration.route} is backed by "
        "no model field and exposes no form field, so nothing types its value; point "
        "field_name at a model field, or put the method on a typed filter primitive "
        "(`CharFilter(method=...)`, `NumberFilter(method=...)`, `ListFilter(method=...)` for a "
        "list value, ...) or on a `Filter` subclass declaring `field_class` at class level.",
    )


#: The filter's form-data key as a refusal spells it, and every key its widget derives from it.
_FORM_KEY = "<name>"


def _refuse_widget_reading_other_keys(
    filter_instance: Filter,
    filterset_cls: type[FilterSet] | None,
) -> None:
    """Refuse a one-value filter whose form field's widget reads keys other than its own name.

    Every arm but the range arm publishes one value and writes it under the filter's one
    form-data key (``filters/sets.py::FilterSet._normalize_input``); a widget reading other
    keys (``utils/widgets.py::widget_keys``: a ``MultiWidget`` such as django-filter's
    ``RangeWidget`` on a ``NumericRangeFilter``'s ``RangeField``, a consumer
    ``MultiValueField``'s, a ``SplitArrayWidget``) never reads that value, so the filter
    would answer every request with every row. The refusal names the filter as declared
    (``_declaration_of``). A filter whose form field builds nothing unbound
    (``_declared_form_field``) is not read here, nor a model-choice filter (django-filter's
    ``QuerySetRequestMixin``) whose ``queryset`` is callable or unset, as
    ``filters/base.py::model_choice_model`` reads it: a callable one is called
    with the request, which the schema build has none of, and an unset one builds no field
    (its set refuses it when it publishes, ``filters/base.py::refuse_querysetless_choice``,
    unless consumer code supplies one per request, and the model-choice arm refuses one
    whose ``field_name`` names no relation).
    """
    if truth.is_instance(filter_instance, QuerySetRequestMixin):
        queryset = read_attr(filter_instance, "queryset", None)
        if queryset is None or callable(queryset):
            return
    form_field = _declared_form_field(filter_instance)
    if form_field is None:
        return
    keys = widget_keys(read_attr(form_field, "widget"), _FORM_KEY)
    if keys == [_FORM_KEY]:
        return
    declaration = _declaration_of(filter_instance, filterset_cls)
    numeric_range = (
        " A NumericRangeFilter filters a PostgreSQL range column, which the schema does not "
        "publish."
        if truth.is_instance(declaration.declared, NumericRangeFilter)
        else ""
    )
    raise ConfigurationError(
        f"{_declaration_subject(declaration, filterset_cls)} publishes one "
        f"value under its form-data key {_FORM_KEY}, but its form field's widget reads "
        f"{', '.join(keys)}, so the value would never be read. Declare a RangeFilter (the "
        "package's or django-filter's) for a two-bound range, or give the filter a form field "
        f"whose widget reads one key.{numeric_range}",
    )


def convert_filter_to_input_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    owner_definition: DjangoTypeDefinition | None,
    filterset_cls: type[FilterSet],
) -> object:
    """Return the Strawberry annotation for a resolved ``django-filter`` filter.

    Implements the spec-027 Decision 4 conversion table. Kind order is
    ``_FILTER_INPUT_KIND_TYPES`` (most-specific first): Relay-aware primitives,
    then the raw-pk relation pair (typed from the target key column), then a
    consumer ``ModelChoiceFilter`` / ``ModelMultipleChoiceFilter`` (typed from the
    column its form field cleans), then CSV, then
    Range / List / Array, then bare ``TypedFilter``, then
    ``ChoiceFilter``, then a ``MultipleChoiceFilter`` (a list whose element is typed
    like a ``ListFilter``'s, from the model column, never from
    ``TypedMultipleChoiceFilter.coerce``), then the ``object`` catch-all. A ``method=``
    filter with no model column whose form field is not built unbound raises
    ``ConfigurationError`` (``_refuse_method_without_form_field``), as does a leaf typed by a
    choice enum that reads no field declaring ``choices``, or whose own form field accepts
    none of its column's choices (``_choice_enum_from_filter``), and a declared or
    ``Meta.filter_overrides`` leaf on its column whose own form and lookup answer no value
    of it (``_refuse_form_serving_no_value``, on the catch-all, bare ``TypedFilter``, CSV
    and range arms), and a leaf typed from a field no ``SCALAR_MAP`` entry covers (a
    relation, a ``GenericForeignKey``, a ``CompositePrimaryKey``, an unregistered column:
    ``_unscalared_field_refusal``, through ``_scalar_from_model_field`` on every arm that
    reads a column's scalar).

    Dispatch rides ``utils/converters.py::convert_with_mro`` with the same
    kind table ``normalize_input_value`` uses.

    ``filterset_cls`` (the ``FilterSet`` whose leaf this is) qualifies the nested
    ``RangeFilter`` sub-input class name so two filtersets sharing a ``field_name``
    mint two distinct GraphQL type names (spec-027 forward path; see
    ``_build_range_input_class``, which also covers the set/field splits that still
    meet), and names a choice enum when no type owns the set (``_enum_prefix``).

    A ``LookupChoiceFilter`` raises ``ConfigurationError`` before anything reads it:
    it filters by a value and a lookup read from two form-data keys (``<name>`` and
    ``<name>_lookup``), and no generated input carries that pair. The form field of a
    filter that reaches a ``field`` read is built on a copy of it (``_declared_form_field``),
    so building the schema writes nothing to a class-level declaration.

    Every arm but the range arm publishes one value under the filter's one form-data key,
    so a filter on any of them whose form field's widget reads other keys (a
    ``NumericRangeFilter``, a ``MultiWidget`` / ``MultiValueField`` filter) raises
    ``ConfigurationError`` (``_refuse_widget_reading_other_keys``); the range arm asks the
    widget for its two keys (``range_form_keys``).
    """
    _refuse_generated_filter_output(filter_instance, model_field, filterset_cls)
    if truth.is_instance(filter_instance, LookupChoiceFilter):
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{_declaration_subject(declaration, filterset_cls)} filters by "
            "a value and a lookup read from two form-data keys, and no GraphQL input carries "
            "that pair. List the lookups in Meta.fields dict form (one input field per "
            "lookup), or keep the filter on a FilterSet the schema does not serve.",
        )
    required = bool(dict_of(filter_instance.extra).get("required", False))

    def _gid_multi(_filter: Filter) -> object:
        return list[str]

    def _gid(_filter: Filter) -> object:
        return str

    def _pk_multi(matched: Filter) -> object:
        element = _relation_identity_annotation(matched, model_field, filterset_cls)
        return GenericAlias(list, (element,))

    def _pk(matched: Filter) -> object:
        return _relation_identity_annotation(matched, model_field, filterset_cls)

    def _model_choice(matched: Filter) -> object:
        element = _model_choice_identity_annotation(matched, filterset_cls)
        return GenericAlias(list, (element,)) if _model_choice_takes_list(matched) else element

    def _csv(matched: Filter) -> object:
        # django-filter expands ``Meta.fields`` ``in`` / ``range`` lookups
        # into ``BaseInFilter`` / ``BaseRangeFilter`` (both ``BaseCSVFilter``
        # subclasses) whose form field consumes a LIST of values, not a
        # scalar. The element type is model-field-driven so a CSV ``in`` over
        # a choice column keeps its enum and a 64-bit column keeps ``BigInt``; past a
        # transform, a member the filter's own form cannot clean as the output is typed by
        # that form (``_form_cleaned_value_field``).
        value_field = _form_cleaned_value_field(matched, model_field, filterset_cls)
        column = _array_element_column(matched, value_field, filterset_cls)
        element = _element_annotation(matched, column, owner_definition, filterset_cls)
        _refuse_form_serving_no_value(matched, element, filterset_cls, _member_list)
        return GenericAlias(list, (element,))

    def _multiple_choice(matched: Filter) -> object:
        # The form field (``MultipleChoiceField``) cleans a list; each element is typed
        # from the model column like a ``ListFilter``'s (spec-027 Decision 4), unless the
        # column holds values as given and compares what the form cleans
        # (``_form_cleaned_value_field``). A ``method=`` one is typed so too, its form field
        # built per request or not (``_refuse_method_without_form_field``).
        _refuse_method_without_form_field(matched, model_field, filterset_cls)
        value_field = (
            _form_cleaned_value_field(matched, model_field, filterset_cls)
            if model_field is not None and holds_values_as_given(model_field)
            else model_field
        )
        element = _element_annotation(matched, value_field, owner_definition, filterset_cls)
        return GenericAlias(list, (element,))

    def _range(matched: Filter) -> object:
        # Refuse a widget the patch cannot address when the schema is built, not per request.
        _ = range_form_keys(matched, matched.field_name or "range", filterset_cls)
        if array_element_field(model_field) is not None:
            raise _array_column_refusal(matched, model_field, filterset_cls, "range")
        # Each axis is typed like a scalar leaf's value (``_form_cleaned_value_field``), a
        # package range's by its comparison form over a column holding values as given.
        value_field = _form_cleaned_value_field(matched, model_field, filterset_cls)
        compared = _column_cleaned_scalar(matched, value_field, filterset_cls)
        if compared is not None:
            inner = compared
        elif value_field is not None or model_field is None:
            inner = _scalar_from_model_field(value_field, matched, filterset_cls)
            _refuse_form_serving_no_value(matched, inner, filterset_cls, _range_bounds)
        else:
            inner = _range_axis_scalar(matched, filterset_cls)
        return _build_range_input_class(matched, inner, filterset_cls)

    def _list(matched: Filter) -> object:
        column = _array_element_column(matched, model_field, filterset_cls)
        compared = _column_cleaned_scalar(matched, column, filterset_cls)
        element = (
            _element_annotation(matched, column, owner_definition, filterset_cls)
            if compared is None
            else compared
        )
        return GenericAlias(list, (element,))

    def _typed(matched: Filter) -> object:
        # Past a transform, a value the filter's own form cannot clean as the output is typed
        # by that form (``_form_cleaned_value_field``), as the catch-all's is.
        value_field = _form_cleaned_value_field(matched, model_field, filterset_cls)
        element = _element_annotation(matched, value_field, owner_definition, filterset_cls)
        _refuse_form_serving_no_value(matched, element, filterset_cls, normalize_input_value)
        return element

    def _choice(matched: Filter) -> object:
        # The array's own ``choices`` are ambiguous (the read side refuses them too).
        if array_element_field(model_field) is not None:
            raise _array_column_refusal(matched, model_field, filterset_cls)
        type_name = _enum_prefix(owner_definition, filterset_cls)
        return _choice_enum_from_filter(matched, type_name, model_field, filterset_cls)

    def _catchall(matched: Filter) -> object:
        # Catch-all scalar branch (``_catchall_element``).
        element = _catchall_element(
            matched,
            model_field,
            filterset_cls,
            lambda field: _element_annotation(matched, field, owner_definition, filterset_cls),
        )
        _refuse_form_serving_no_value(matched, element, filterset_cls, normalize_input_value)
        return element

    def _one_key(handler: Callable[[Filter], object]) -> Callable[[Filter], object]:
        def _checked(matched: Filter) -> object:
            _refuse_widget_reading_other_keys(matched, filterset_cls)
            return handler(matched)

        return _checked

    annotation = convert_with_mro(
        filter_instance,
        isinstance_prechecks=_filter_input_prechecks(
            _one_key(_gid_multi),
            _one_key(_gid),
            _one_key(_pk_multi),
            _one_key(_pk),
            _one_key(_model_choice),
            _one_key(_csv),
            _range,
            _one_key(_list),
            _one_key(_typed),
            _one_key(_choice),
            _one_key(_multiple_choice),
            _one_key(_catchall),
        ),
        scalar_registry={},
        fallthrough_error_factory=_unexpected_filter_dispatch,
    )
    if not required:
        annotation = optional_annotation(annotation)
    return annotation


def normalize_input_value(
    filter_instance: Filter,
    raw_value: object,
    field_name: str | None = None,
) -> object:
    """Translate a Strawberry-shaped input value into ``django-filter`` form-data.

    Returns one of three shapes (spec-027 Decision 4):

    - a scalar value (``str`` / ``int`` / wire-form GlobalID string /
      enum ``.value``) when the filter consumes a single form-data key;
      a member of a generated choice-column filter's enum
      (``EnumChoiceFilter`` / ``EnumLookupFilter``) becomes
      ``EnumMemberValue(member.value)`` instead, so every member is a value
      on every lookup that publishes it (``BLANK`` filters ``""``, a
      ``"null"``-valued member filters ``"null"``) while a raw string keeps
      django-filter's form-data handling (``""`` skips, ``"null"`` on a
      ``ChoiceFilter`` is ``IS NULL``). A GlobalID is kept in its base64
      wire form (not pre-decoded to a bare ``node_id``) so the bound filter
      can validate its ``type_name`` before decoding;
    - a ``dict`` when the filter publishes a ``JSON`` value (``publishes_json_value``):
      one JSON object, bound under the filter's one form-data key;
    - a ``list`` when ``django-filter`` consumes a list;
    - a ``_RangeFormPatch`` when the filter consumes the two form-data keys
      its range widget reads (``RangeFilter`` -> ``{<field>_0, <field>_1}``,
      django-filter's ``RangeFilter`` -> ``{<field>_min, <field>_max}``).

    Kind order is ``_FILTER_INPUT_KIND_TYPES``, the same table convert
    walks. A bare ``TypedFilter`` is typed as one element, so normalize gives
    it the scalar shape the ``ChoiceFilter`` and catch-all arms give, as
    convert does. ``None`` from unwrap (an enum member whose ``.value`` is
    ``None``) is a successful result, not a continue signal.
    """
    # Defensive short-circuit against ``strawberry.UNSET`` reaching the
    # branches below: every branch indexes / iterates / coerces
    # ``raw_value`` and would either raise ``TypeError`` (UNSET is not
    # iterable) or silently pass the UNSET sentinel into ``data``. Every
    # caller MUST treat UNSET as "not supplied" - same as ``None`` - so
    # this entry point is the single defensive line every future caller
    # benefits from.
    if is_inactive_value(raw_value, unset_sentinel=UNSET):
        return None

    def _gid_multi(_filter: Filter) -> object:
        items = _require_list_container(_filter, raw_value, "GlobalID list")
        return [_encode_global_id_input(item) for item in items]

    def _gid(_filter: Filter) -> object:
        return _encode_global_id_input(raw_value)

    def _pk_multi(_filter: Filter) -> object:
        items = _require_list_container(_filter, raw_value, "primary-key list")
        return [_unwrap_enum_member(item) for item in items]

    def _pk(_filter: Filter) -> object:
        return _unwrap_enum_member(raw_value)

    def _model_choice(matched: Filter) -> object:
        # The consumer's model-choice form field cleans the raw value(s) itself.
        if not _model_choice_takes_list(matched):
            return _unwrap_enum_member(raw_value)
        items = _require_list_container(matched, raw_value, "model-choice list")
        return [_unwrap_enum_member(item) for item in items]

    def _csv(_filter: Filter) -> object:
        # ``in`` / ``range`` generated CSV filters consume a list; unwrap
        # any enum members per element (parity with ``ListFilter`` below).
        items = _require_list_container(_filter, raw_value, "CSV membership list")
        return [_unwrap_enum_member(item) for item in items]

    def _multiple_choice(_filter: Filter) -> object:
        # ``MultipleChoiceField`` cleans a list of choice values.
        items = _require_list_container(_filter, raw_value, "multiple-choice list")
        return [_unwrap_enum_member(item) for item in items]

    def _range(matched: Filter) -> object:
        return _normalize_range_value(matched, raw_value, field_name=field_name)

    def _list(_filter: Filter) -> object:
        items = _require_list_container(_filter, raw_value, "list input")
        return [_unwrap_enum_member(item) for item in items]

    def _typed(matched: Filter) -> object:
        return _scalar(matched)

    def _scalar(matched: Filter) -> object:
        # Shared by the ``ChoiceFilter`` and catch-all arms. A generated choice-column
        # filter takes each enum member as a typed value no form-data sentinel can
        # reinterpret; a raw value (not a member) keeps django-filter's handling.
        if isinstance(matched, _EnumMemberFilterMixin) and isinstance(raw_value, enum.Enum):
            return EnumMemberValue(enum_value(raw_value))
        return _unwrap_enum_member(raw_value)

    return convert_with_mro(
        filter_instance,
        isinstance_prechecks=_filter_input_prechecks(
            _gid_multi,
            _gid,
            _pk_multi,
            _pk,
            _model_choice,
            _csv,
            _range,
            _list,
            _typed,
            _scalar,
            _multiple_choice,
            _scalar,
        ),
        scalar_registry={},
        fallthrough_error_factory=_unexpected_filter_dispatch,
    )


def _require_list_container(
    filter_instance: Filter,
    raw_value: object,
    shape: str,
) -> list[object] | tuple[object, ...]:
    """Fail loud when a list-consuming normalize arm receives another container.

    The list-consuming normalize arms iterate ``raw_value``.
    Generated filter inputs declare a GraphQL list. A consumer's ordinary JSON
    argument or a programmatic ``apply_sync`` caller can still supply another
    shape to the public apply pipeline. Iterating one would splat it: a
    ``{'start': 1, 'end': 5}`` patch would normalize to its KEYS
    (``['start', 'end']``) and a string to its CHARACTERS, silently dropping
    the intended predicate and filling the form-data dict with junk members.
    The shape is invalid, not merely iterable, so it raises the typed
    ``ConfigurationError`` (fail loud, never a silent keys-for-values swap).
    Returns ``raw_value``, narrowed to the list or tuple it proved, for the
    arm to iterate.
    """
    if not is_list_or_tuple(raw_value):
        raise ConfigurationError(
            f"{_declaration_of(filter_instance, None).kind} consumes a list of values for its "
            f"{filter_instance.field_name!r} input, but received a non-list container "
            f"({truth.kind(raw_value)} {truth.render(raw_value)}) for the {shape}; "
            "send a list (generated filter inputs deliver a list after GraphQL coercion).",
        )
    return raw_value


# ---------------------------------------------------------------------------
# Range / GlobalID / Enum value helpers
# ---------------------------------------------------------------------------


def _encode_global_id_input(value: object) -> object:
    """Return the wire-form GlobalID string for a ``relay.GlobalID``-or-string.

    ``normalize_input_value`` feeds GlobalID-aware filters their form-data
    value. A ``relay.GlobalID`` OBJECT (the shape a direct-Python
    ``apply_sync`` / ``apply_async`` caller passes) MUST keep its
    ``type_name`` so ``GlobalIDFilter.filter`` /
    ``GlobalIDMultipleChoiceFilter.filter`` can validate it against the
    target GraphQL type (spec-027 Decision 4) before any queryset clause runs.
    Decoding the object down to its bare ``node_id`` here would strip the
    ``type_name`` *before* validation, so a wrong-type GlobalID object would
    silently pass the gate. Re-encoding to the base64 wire string preserves the type, survives
    the ``django-filter`` form ``clean`` step, and lets the bound filter
    run the canonical decode-and-validate path. A ``str`` value is
    already wire-form and passes through unchanged, so the GraphQL string
    path is untouched.
    """
    if isinstance(value, relay.GlobalID):
        return relay.to_base64(value.type_name, value.node_id)
    return value


def _unwrap_enum_member(value: object) -> object:
    """Return ``value.value`` for an ``enum.Enum`` member; passthrough otherwise.

    Structural ``isinstance(value, enum.Enum)`` rather than duck-typing on
    ``.value`` / ``.name``: a ``@strawberry.enum`` decorates a Python
    ``enum.Enum``, so its members ARE ``enum.Enum`` instances. The structural
    check also unwraps a member whose ``.value`` is legitimately ``None``
    (a value-truthiness guard would return such a member un-unwrapped), and
    it never misfires on plain objects that merely expose a
    ``.value`` attribute (e.g. ``decimal.Decimal``).

    Single-level unwrap - nested-list / nested-dict inputs are not
    recursively unwrapped. No current consumer produces such shapes (the
    Django converter pipeline yields flat scalars / lists from the
    `django-filter` form-field hierarchy); a future nested-shape
    ``ListFilter`` would need its own per-level walk.
    """
    if isinstance(value, enum.Enum):
        return enum_value(value)
    return value


def _build_range_input_class(
    filter_instance: Filter,
    inner: object,
    filterset_cls: type[FilterSet],
) -> type[object]:
    """Return a Strawberry input dataclass with ``start: T | None`` and ``end: T | None``.

    Each call builds a fresh class and nothing caches it: the name and axes depend
    only on the owning filterset, the Django field path and the inner scalar, and
    the arguments factory builds each filterset's input once per generation.

    The class name is qualified by the owning ``FilterSet`` and stemmed on the value path,
    the ``field_name`` followed by every transform Django's query applies ahead of the
    lookup (``filters/base.py::_filterset_lookup_lhs_path``) --
    ``f"{filterset_cls.__name__}{Pascal(value_path)}RangeInputType"``, so
    ``RangeFilter(field_name="occurred_at", lookup_expr="year__range")``, a bare
    ``lookup_expr="year"`` and ``RangeFilter(field_name="occurred_at__year",
    lookup_expr="range")`` all spell ``OccurredAtYear`` and a ``range`` over the column
    itself ``OccurredAt``, two types whose axes differ (``Int`` and ``DateTime``); a
    ``method=`` filter's bounds are its column's, so its stem is the ``field_name``; a set
    with no model, a path no query of the model resolves (an annotation, a
    ``FilteredRelation`` alias) and a ``lookup_expr`` no walk accepts are stemmed on the
    ``field_name`` and the ``lookup_expr`` parts ahead of the last -- mirroring the
    per-field operator-bag naming (``ClassBasedTypeNameMixin.type_name_for``). Without
    this qualifier the name
    derived from ``field_name`` alone, so two filtersets that share a
    ``field_name`` for a ``RangeFilter`` (e.g. both filter a ``price`` column)
    each mint a DISTINCT sub-input class under the SAME GraphQL type name, and
    two filtersets serving one schema with ranges of different scalars (a
    ``date`` range vs an ``int`` range) could not share it. The qualifier keeps
    the common case distinct; it is not injective (``A`` over ``b_c`` and ``AB``
    over ``c`` both spell ``ABCRangeInputType``, and ``shelf__code`` /
    ``shelf_code`` in one set share a stem). These nested classes are embedded
    directly in the annotation, NOT materialized through Decision 9's
    ``_materialized_names`` ledger, so the arguments factory claims each one
    through ``utils/inputs.py::claim_generated_type_name`` when it claims its
    set's root: two ranges of different axes under one name reached from one set
    raise ``ConfigurationError`` at finalize, and a pair from two sets fails only
    a schema serving both.
    """
    field_name = getattr(filter_instance, "field_name", "field") or "field"
    lookup_expr = filter_instance.lookup_expr
    if read_attr(filter_instance, "method", None) is not None:
        # A ``method=`` filter's bounds are its column's (``_filterset_value_field``).
        value_path = field_name
    else:
        # Where no query of the model walks the path (no model, an alias or annotation only
        # the queryset holds, an unwalkable ``lookup_expr``), the stem keeps the parts the
        # ``lookup_expr`` spells ahead of the last.
        value_path = _filterset_lookup_lhs_path(
            filterset_cls,
            field_name,
            lookup_expr,
        ) or LOOKUP_SEP.join((field_name, *lookup_expr.split(LOOKUP_SEP)[:-1]))
    cls_name = f"{truth.name(filterset_cls)}{_pascal_case(value_path)}RangeInputType"
    return build_input_class(
        cls_name,
        [
            ("start", optional_annotation(inner), {"default": None}),
            ("end", optional_annotation(inner), {"default": None}),
        ],
    )


#: The axes a range input carries: ``_build_range_input_class`` declares exactly these.
_RANGE_AXES = frozenset({"start", "end"})


class _RangeFormPatch(dict[str, object]):
    """A range filter's form-data patch: the start and end keys its range widget reads.

    The one multi-key shape ``normalize_input_value`` returns, under its own type so
    the normalizer's caller (``filters/sets.py::FilterSet._normalize_input``) merges it
    by type and never mistakes a dict a non-range filter passed through verbatim for
    a patch.
    """

    axis_keys: tuple[str, str] | None = None


def _normalize_range_value(
    filter_instance: Filter,
    raw_value: object,
    field_name: str | None = None,
) -> _RangeFormPatch:
    """Return the form-data patch of a range filter: its start and end under its widget's keys.

    Per spec-027 Decision 4 the two keys are the ones the filter's own range widget
    reads (``utils/widgets.py::multi_widget_keys``): ``<name>_0`` / ``<name>_1`` for the
    package's ``RangeFilter`` (Django's ``MultiWidget``), ``<name>_min`` / ``<name>_max``
    for django-filter's ``RangeFilter`` (``RangeWidget``), ``<name>_after`` /
    ``<name>_before`` for its date and time families (``DateRangeWidget``), and a
    consumer widget's own ``suffixes`` (``range_form_keys``, which the schema build already
    ran, so a widget that does not read exactly two keys never reaches a request). The
    patch's key prefix is the form-data field name
    (``filter_instance.field_name`` for direct filters; the caller may override via
    ``field_name`` for the dataclass-attribute case where the Strawberry attr differs
    from the django-filter form-key).

    Partial-range inputs surface only the supplied key (the start key for
    start-only, the end key for end-only, ``{}`` for neither). Omitting
    ``None``-valued axes preserves the form-data "axis not supplied" convention
    ``django-filter`` consumes and keeps the patch keys load-bearing for any caller
    walking ``data.keys()``.

    The value is read through ``utils/input_values.py::iter_input_items``, the
    package's one dict-or-input-dataclass walk. Generated range inputs declare
    the ``{start, end}`` object; ordinary consumer JSON arguments and programmatic
    mappings can also reach this pipeline. A value the walk cannot read (a list,
    a scalar, an arbitrary object), or a key other than ``start`` / ``end``,
    would lose its values, so it raises the typed
    ``ConfigurationError`` instead of answering with an unconstrained patch, as
    ``_require_list_container`` does for the list arms. A misspelled lookup
    under a range head (``{"span": {"rnage": {...}}}``) arrives here as the
    head's bare value, so this check is also what makes it raise like any other
    unknown lookup.
    """
    base = field_name or filter_instance.field_name or "range"
    items = iter_input_items(raw_value)
    if items is None or any(name not in _RANGE_AXES for name, _ in items):
        raise ConfigurationError(
            f"{_declaration_of(filter_instance, None).kind} consumes a range input with only "
            f"'start' / 'end' axes for its {base!r} input, but received "
            f"{truth.kind(raw_value)} {truth.render(raw_value)}; send a mapping or "
            "input object with 'start' / 'end' (generated filter inputs reject this shape"
            " during GraphQL validation).",
        )
    axes = dict(items)
    start = axes.get("start")
    end = axes.get("end")
    start_key, end_key = range_form_keys(filter_instance, base)
    # Drop ``None``- and ``UNSET``-valued axes so partial-range inputs surface only
    # the supplied key. A range widget treats a missing key the same as a
    # ``None``-valued one, but emitting ``{<start key>: None}`` or
    # ``{<start key>: UNSET}`` to the form-data dict surfaces "axis supplied, value
    # is inactive" to any caller walking ``data.keys()`` and leaks ``UNSET`` into
    # form-field cleaning -- the same ``is_inactive_value`` test as
    # ``normalize_input_value``'s entry guard.
    patch = _RangeFormPatch()
    patch.axis_keys = (start_key, end_key)
    if not is_inactive_value(start, unset_sentinel=UNSET):
        patch[start_key] = _unwrap_enum_member(start)
    if not is_inactive_value(end, unset_sentinel=UNSET):
        patch[end_key] = _unwrap_enum_member(end)
    return patch


def range_form_keys(
    filter_instance: Filter,
    base: str,
    filterset_cls: type[FilterSet] | None = None,
) -> tuple[str, str]:
    """Return the start and end form-data keys a range filter's widget reads for ``base``.

    The widget is the one the form field the filter's own class builds carries, a consumer
    ``field`` override included, read on a copy so the class-level declaration every request
    shares keeps nothing (``_declared_form_field``), and asked for its keys through
    ``utils/widgets.py::multi_widget_keys``. A widget that does not read exactly two keys has
    no slot for a start and an end, and neither has a field the filter builds only inside a
    bound ``FilterSet``, so each is a ``ConfigurationError`` naming the filter as declared on
    ``filterset_cls`` (``_declaration_of``); ``convert_filter_to_input_annotation`` runs this
    when the schema is built.
    """
    form_field = _declared_form_field(filter_instance)
    if form_field is None:
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{declaration.kind} consumes a range input for its {base!r} "
            f"input{declaration.site}, but its form field is built only inside a bound "
            "FilterSet, so the form-data keys its widget reads cannot be known when the "
            "schema is built; build the field from the filter's own arguments.",
        )
    return _range_widget_keys(
        filter_instance,
        read_attr(form_field, "widget"),
        base,
        filterset_cls,
    )


def _range_widget_keys(
    filter_instance: Filter,
    widget: object,
    base: str,
    filterset_cls: type[FilterSet] | None = None,
) -> tuple[str, str]:
    """Ask an actual range widget for its axes under the declaration's typed refusal."""
    keys = multi_widget_keys(widget, base)
    if keys is None or len(keys) != _RANGE_BOUNDS:
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{declaration.kind} consumes a range input for its {base!r} "
            f"input{declaration.site}, but its form field's widget does not read exactly two "
            f"form-data keys ({truth.render(keys)}); give it a two-widget MultiWidget.",
        )
    return keys[0], keys[1]


def _enum_prefix(
    owner_definition: DjangoTypeDefinition | None,
    filterset_cls: type[FilterSet],
) -> str:
    """Return the prefix a choice enum built for a leaf of ``filterset_cls`` carries.

    The owning type's published name when the set is bound to one
    (``DjangoTypeDefinition.graphql_type_name``, the rule the read side names the
    same column's enum by), else the set's own class name: two unbound sets over
    same-named choice columns of different models (``RelatedFilter`` targets no
    type serves) mint two names, never one literal.
    """
    if owner_definition is not None:
        return owner_definition.graphql_type_name
    return truth.name(filterset_cls)


# ---------------------------------------------------------------------------
# Logical-operator + input-field builders
# ---------------------------------------------------------------------------


def _build_logic_fields(type_name: str) -> list[tuple[str, object, dict[str, object]]]:
    """Return ``(python_attr, annotation, field_kwargs)`` triples for logical operators.

    Operators come from ``LOGIC_OPERATORS`` so adding an operator automatically
    emits the field on the generated input without parallel edits. The annotations
    follow the INSIDE-list shape: the ``Annotated[...]`` wraps the
    forward-reference string directly, and the ``list[...]`` (for sequence operators)
    wraps the ``Annotated[...]`` -- NOT the other way around. Non-sequence operators
    use a single self-ref. GraphQL surface names ride through
    ``optional_field_kwargs`` -> ``strawberry.field(name=...)`` because the
    wire tokens are Python keywords and cannot be dataclass field names.
    """
    self_ref: object = Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]
    list_ref = GenericAlias(list, (self_ref,))
    return [
        (
            op.python_attr,
            optional_annotation(list_ref if op.is_sequence else self_ref),
            optional_field_kwargs(op.wire_name),
        )
        for op in LOGIC_OPERATORS
    ]


# One bag lookup's django-filter form key (its name in the published filter table) and filter.
FormKeyedFilter = tuple[str, Filter]


@dataclass(frozen=True)
class FilterLookupTable:
    """Every operator-bag lookup's django-filter form key, decided once per filter set.

    ``heads`` maps ``head -> lookup token -> (form key, filter)`` in the
    published filter table's order (``FilterSet._filter_table``);
    ``_build_input_fields`` emits one input field per head from it.
    ``by_input_attr`` maps ``input attr -> lookup attr -> (form key, filter)``,
    keyed by each head's own spelling and by its flattened
    generated-input attr; ``FilterSet._normalize_input`` reads it. Both views
    hold the same entries, so the generated input and the form data it
    normalizes to cannot disagree. ``gate_paths`` maps the same keys to the
    head's ``check_<path>_permission`` path: a declared head, and an expansion
    of a child's declared filter, gates on its own name (``shelf__home_branch``
    fires ``check_shelf_home_branch_permission`` and, through the relation walk,
    the child's ``check_home_branch_permission``, as the nested spelling does);
    any other head gates on its filter's ``field_name`` (the ORM path), so
    ``name`` and ``name__icontains`` share the ``name`` gate
    (``leaf_gate_path``). ``source`` is the published filter table
    (``FilterSet._filter_table``) the lookup table was built from: the cache is
    valid only while that object is.
    """

    source: Mapping[str, Filter]
    heads: Mapping[str, Mapping[str, FormKeyedFilter]]
    by_input_attr: Mapping[str, Mapping[str, FormKeyedFilter]]
    gate_paths: Mapping[str, str]


def _is_declared_head(filterset_cls: type[FilterSet], name: str, filter_instance: Filter) -> bool:
    """Whether ``filter_instance``, held as ``name`` on ``filterset_cls``, is a declared head there.

    A filter ``filterset_cls`` declares is one, and so is a ``RelatedFilter``
    expansion's copy of a child filter that is one on its own set, followed
    through the record the copy carries (``filters/sets.py::_expansion_record``)
    to the set declaring it. The child set's declarations answer, never the
    copy's provenance stamp: ``origin="declared"`` says a consumer owns the
    object, not which set declares it, and a child set's own filter that a
    ``get_filters()`` override returns into another set carries it there too.
    """
    from .sets import _expansion_record, _projection_child_filter  # noqa: PLC0415 - import cycle

    # django-filter's metaclass stores ``declared_filters`` as the name-keyed declared map.
    declared_filters = require(
        truth.static_attr(filterset_cls, "declared_filters", {}),
        is_mapping,
    )
    if name in declared_filters:
        return True
    record = _expansion_record(filter_instance)
    return record is not None and _is_declared_head(
        record.filterset,
        record.name,
        _projection_child_filter(record),
    )


def leaf_gate_path(filterset_cls: type[FilterSet], name: str, filter_instance: Filter) -> str:
    """Return the gate path leaf ``name`` of ``filterset_cls`` fires ``check_<path>_permission`` on.

    The path ``FilterLookupTable.gate_paths`` holds for the leaf's head: a
    declared head's own name (``_is_declared_head``), else the ``field_name``
    every lookup of a generated head shares, which its head spells.
    """
    if _is_declared_head(filterset_cls, name, filter_instance):
        return name
    return _declared_field_name(filter_instance)


def _group_filters_by_head(
    filterset_cls: type[FilterSet],
    all_filters: Mapping[str, Filter],
) -> tuple[OrderedDict[str, OrderedDict[str, FormKeyedFilter]], set[str]]:
    """Group a published filter table by input head, keeping each lookup's own form key.

    A declared filter, and a ``RelatedFilter`` expansion of a child's declared
    filter, is its own head: its name is its form key even when it ends in its
    own lookup token (``name__exact``). A generated entry joins the head its
    name spells ahead of the tail django-filter's ``get_filter_name`` appends for
    its ``lookup_expr``, under that tail's lookup: ``occurred_at__year__gt`` joins
    ``occurred_at`` under ``year__gt``, and ``occurred_at__year`` (a ``year`` or
    ``year__exact`` lookup, which django-filter names alike) under ``year``, so a
    ``RelatedFilter`` expansion keeps the alias it is published under
    (``branch__name``). A name not ending in that tail (a ``get_filters()``
    override re-keyed it) is its own head. Two filters claiming one
    ``(head, lookup)`` slot would leave one unreachable from the generated
    input, so that raises. Returns the grouping and the set of declared heads.
    """
    grouped: OrderedDict[str, OrderedDict[str, FormKeyedFilter]] = OrderedDict()
    declared_heads: set[str] = set()
    for filter_name, filter_instance in all_filters.items():
        # Skip expanded RelatedFilter entries (e.g., `self_link__self_link`
        # under a self-referential filterset). The top-level
        # `RelatedFilter` forward-ref already exposes the same target;
        # the expanded duplicate would otherwise reach the leaf branch
        # and trip the `ChoiceFilter` guard.
        if "__" in filter_name and truth.is_instance(filter_instance, RelatedFilter):
            continue
        lookup_expr = filter_instance.lookup_expr
        if _is_declared_head(filterset_cls, filter_name, filter_instance):
            head, lookup_token = filter_name, lookup_expr
            declared_heads.add(head)
        else:
            # django-filter names a generated filter ``<path>`` plus this tail (empty
            # for ``exact``, which keeps the bare ``<path>`` as its own head).
            tail = filterset_cls.get_filter_name("", lookup_expr)
            if tail and filter_name.endswith(tail) and len(filter_name) > len(tail):
                head, lookup_token = filter_name[: -len(tail)], tail.removeprefix(LOOKUP_SEP)
            else:
                head, lookup_token = filter_name, lookup_expr
        bag = grouped.setdefault(head, OrderedDict())
        prior = bag.get(lookup_token)
        if prior is not None:
            raise ConfigurationError(
                f"{truth.qualname(filterset_cls)}: filters {prior[0]!r} and {filter_name!r} "
                f"both bind the {lookup_token!r} lookup of input field {head!r}, so one "
                "would be unreachable from the generated input. Rename one filter or "
                "drop one via Meta.fields / Meta.exclude.",
            )
        bag[lookup_token] = (filter_name, filter_instance)
    return grouped, declared_heads


def filter_lookup_table(filterset_cls: type[FilterSet]) -> FilterLookupTable:
    """Return ``filterset_cls``'s ``FilterLookupTable``, built once per published filter table.

    The flattened generated-input attr of a ``<path>__<field>`` head is an alias
    only when no head is literally spelled that way (a head's own spelling wins);
    two heads sharing one alias raise, since one would be unreachable, and so do
    two lookups of one head named by one attr (``lookup_leaf_names``).
    """
    all_filters = filterset_cls._filter_table()
    cached = filterset_cls._lookup_table
    if cached is not None and cached.source is all_filters:
        return cached
    heads, declared_heads = _group_filters_by_head(filterset_cls, all_filters)
    by_input_attr: dict[str, Mapping[str, FormKeyedFilter]] = {}
    gate_paths: dict[str, str] = {}
    for head, bag in heads.items():
        lookups: dict[str, FormKeyedFilter] = {}
        for token, entry in bag.items():
            lookup_attr = lookup_leaf_names(token)[0]
            prior = lookups.setdefault(lookup_attr, entry)
            if prior is not entry:
                raise ConfigurationError(
                    f"{truth.qualname(filterset_cls)}: filters {prior[0]!r} and {entry[0]!r} "
                    f"both generate the lookup attribute {lookup_attr!r} of input field "
                    f"{head!r}, so one would be unreachable. Rename one filter or drop one "
                    "via Meta.fields / Meta.exclude.",
                )
        by_input_attr[head] = lookups
        _form_key, sample_filter = next(iter(bag.values()))
        # A declared head gates on its own name; so does an expansion of a child's
        # declared filter, whose flat spelling must fire the gates its nested twin
        # fires (``utils/permissions.py::_fire_flat_relation_path_gates`` walks the
        # relation hops and fires the child's ``check_<name>_permission``).
        gate_paths[head] = head if head in declared_heads else _declared_field_name(sample_filter)
    alias_heads: dict[str, str] = {}
    for head in heads:
        input_attr = flatten_lookup_path(head)
        if input_attr in heads:
            continue
        prior_head = alias_heads.setdefault(input_attr, head)
        if prior_head != head:
            raise ConfigurationError(
                f"{truth.qualname(filterset_cls)}: filters {prior_head!r} and {head!r} both "
                f"generate the input attribute {input_attr!r} (Django path separators "
                "flatten to '_'), so one would be unreachable. Rename one filter or "
                "drop one via Meta.fields / Meta.exclude.",
            )
        by_input_attr[input_attr] = by_input_attr[head]
        gate_paths[input_attr] = gate_paths[head]
    table = FilterLookupTable(
        source=all_filters,
        heads=heads,
        by_input_attr=by_input_attr,
        gate_paths=gate_paths,
    )
    filterset_cls._lookup_table = table
    return table


def filter_member_lever(filterset_cls: type[FilterSet], head: str) -> MemberLever:
    """Return the kind of member input head ``head`` of ``filterset_cls`` is.

    A filter or ``RelatedFilter`` the set declares or inherits is a declaration;
    a head a ``RelatedFilter`` expansion copies in is that branch's flat copy
    (``_flat_copy_record``); any other head is a ``Meta.fields`` entry.
    """
    if head in filterset_cls.declared_filters:
        return MemberLever(DECLARED_MEMBER)
    record = _flat_copy_record(filterset_cls, head)
    if record is not None:
        return MemberLever(EXPANDED_MEMBER, via=record.branch)
    return MemberLever(LISTED_MEMBER)


def _flat_copy_record(filterset_cls: type[FilterSet], head: str) -> ChildProjection | None:
    """Return the expansion record of input head ``head``'s flat copies, else ``None``.

    A head a ``RelatedFilter`` expansion copies in holds the copies of one child
    head's lookups (``filters/sets.py::_is_flat_copy``); any other head holds none.
    """
    from .sets import _expansion_record  # noqa: PLC0415 - import cycle

    for _form_key, head_filter in filter_lookup_table(filterset_cls).heads.get(head, {}).values():
        record = _expansion_record(head_filter)
        if record is not None and record.holds_in(filterset_cls):
            return record
    return None


def _lookup_lever(filterset_cls: type[FilterSet], head: str) -> MemberLever:
    """Return the lever of an operator-bag lookup of input head ``head``.

    The lookups come from a ``Meta.fields`` lookup list: the head's own on
    ``filterset_cls``, or, for a ``RelatedFilter`` expansion's flat copy, the child
    head's on the child set (``shelves__code`` copies ``code`` of the shelf set).
    A declared filter is a head of its own, with its one lookup.
    """
    record = _flat_copy_record(filterset_cls, head)
    if record is None:
        return MemberLever(LISTED_LOOKUP, via=repr(head))
    child_head = head.removeprefix(f"{record.branch}{LOOKUP_SEP}")
    return MemberLever(LISTED_LOOKUP, via=f"{child_head!r} on {truth.qualname(record.filterset)}")


def _build_input_fields(
    filterset_cls: type[FilterSet],
    owner_definition: DjangoTypeDefinition | None = None,
) -> list[tuple[str, object, dict[str, object]]]:
    """Return per-field input triples for a filterset's top-level GraphQL input.

    Emits one entry per head of ``filter_lookup_table`` (the grouped published
    filter table, ``FilterSet._filter_table``): a forward-reference ``Annotated[...]`` for
    ``RelatedFilter`` boundaries OR a per-field operator-bag dataclass for leaf
    paths, one bag attr per lookup the table holds. Populates ``_field_specs``
    for the active-field walk and the permission gates.
    """
    # The metaclass stores ``related_filters`` from
    # ``sets_mixins.py::collect_related_declarations`` (``RelatedFilter`` only).
    related_filters = declaration_map(
        truth.static_attr(filterset_cls, "related_filters", OrderedDict[str, object]()),
        RelatedFilter,
    )
    lookup_table = filter_lookup_table(filterset_cls)

    # ``HIDE_FLAT_FILTERS`` (default ``False``, the default of
    # ``django-graphene-filters``'s key of the same name) controls whether a
    # ``RelatedFilter`` expansion's flat copies (``categoryName``, deep
    # ``entriesPropertyCategoryName``, ...) are emitted. When hidden, those
    # filters are reached only through their nested ``RelatedFilter`` branch
    # (``category: { name: { ... } }``) -- the strawberry-django shape. When
    # shown, BOTH the flat and nested shapes appear, a surface this package
    # adds: upstream never publishes the expanded copies (its ``filter`` input
    # renders a ``RelatedFilter`` as a reference to the target's input, and its
    # flat connection arguments, the ones its key hides, drop every key under a
    # ``RelatedFilter``'s name through the ``is_expanded_child`` test in
    # ``django_graphene_filters/connection_field.py::_get_trimmed_filterset_class``).
    # A copy is named by the record its expansion stamped, never by its key
    # (``_visible_entries``), so a copy a ``get_filters()`` override re-keys is
    # hidden and the set's own filter spelled under a branch's name is not; the
    # hidden operator-bag lookups are never built in the first place. The key is
    # read through its ``conf.py`` named reader; truthiness coercion is this
    # consumer's own semantics (the reader stays thin).
    hide_flat_filters = bool(hide_flat_filters_setting())

    def _visible_entries() -> Iterator[tuple[str, Mapping[str, FormKeyedFilter]]]:
        """Yield the grouped entries minus the ``HIDE_FLAT_FILTERS`` expanded copies.

        An expanded copy is a lookup ``filters/sets.py::_is_flat_copy`` names:
        it carries the ``ChildProjection`` of a ``RelatedFilter`` this set
        declares, under whatever key the set's filter table holds it, so its
        nested twin answers it through that branch. When ``HIDE_FLAT_FILTERS``
        is set, each copy leaves its head's operator bag, and a head left with
        no lookup is not emitted; every other lookup (the set's own filter,
        a ``Meta.fields`` traversal under a ``RelatedFilter``'s name included)
        stays, so nothing the set filters on becomes unreachable. This
        pre-filter stays filter-family semantics, BEFORE the shared emission
        scaffold.
        """
        if not hide_flat_filters:
            yield from lookup_table.heads.items()
            return
        for top_name, lookup_bag in lookup_table.heads.items():
            own_lookups = {
                token: entry
                for token, entry in lookup_bag.items()
                if not _is_hidden_flat_copy(filterset_cls, entry[1])
            }
            if own_lookups:
                yield top_name, own_lookups

    def _related_of(
        top_name: str,
        _lookup_bag: Mapping[str, FormKeyedFilter],
    ) -> tuple[type[FilterSet] | None, str] | None:
        rel_filter = related_filters.get(top_name)
        if rel_filter is None:
            return None
        return rel_filter.filterset, top_name

    def _leaf_of(
        top_name: str,
        python_attr: str,
        lookup_bag: Mapping[str, FormKeyedFilter],
    ) -> tuple[object, str]:
        # Leaf path: build a per-field operator-bag input class. Every
        # operator-bag leaf is optional (``optional_field_kwargs``); an
        # omitted ``default`` would build a REQUIRED field.
        bag_name = filterset_cls.type_name_for(python_attr)
        bag_specs: list[tuple[str, object, dict[str, object]]] = []
        for lookup, (_form_key, leaf_filter) in lookup_bag.items():
            lookup_python_attr, lookup_wire_name = lookup_leaf_names(lookup)
            if not lookup_python_attr.isidentifier():
                raise _unnameable_lookup_refusal(leaf_filter, lookup, filterset_cls)
            # A leaf is typed by the field each value is cleaned as: the output of any
            # transform between column and lookup (``year``'s int, an index's element).
            model_field = _filterset_value_field(filterset_cls, leaf_filter)
            annotation = convert_filter_to_input_annotation(
                leaf_filter,
                model_field,
                owner_definition,
                filterset_cls,
            )
            bag_specs.append(
                (lookup_python_attr, annotation, optional_field_kwargs(lookup_wire_name)),
            )
        lookup_lever = _lookup_lever(filterset_cls, top_name)
        bag_class = build_input_class(
            bag_name,
            bag_specs,
            sources=GeneratedFieldSources(
                subject=f"FilterSet {truth.qualname(filterset_cls)!r}",
                field_noun="lookups",
                rename_clause="Rename one lookup",
                members={lookup_leaf_names(lookup)[0]: lookup for lookup in lookup_bag},
                levers={lookup_leaf_names(lookup)[0]: lookup_lever for lookup in lookup_bag},
            ),
        )
        # The ``FieldSpec`` source path is the head's permission gate path;
        # the form keys the normalizer emits come from the lookup table.
        return bag_class | None, lookup_table.gate_paths[top_name]

    # The per-field emission scaffold (python-attr flatten ->
    # optional kwargs -> related lazy-ref vs leaf -> triple + ``FieldSpec``) is
    # single-sited in ``utils/inputs.py::emit_set_input_field_triples``; the
    # closures above carry the filter-family semantics.
    return emit_set_input_field_triples(
        filterset_cls,
        _visible_entries(),
        related_of=_related_of,
        leaf_of=_leaf_of,
        module_path=INPUTS_MODULE_PATH,
        field_specs=_field_specs,
    )


def construct_search(all_filters: Mapping[str, object]) -> dict[str, str]:
    """Translate ``LOOKUP_PREFIXES``-vocabulary keys into a ``{name: lookup}`` map.

    No package code calls it yet: the ``Meta.search_fields`` consumer surface is
    spec-062's, and its wiring point is the ``TODO(spec-062 Slice 1)`` anchor in
    ``filters/sets.py``. It is the one consumer of ``LOOKUP_PREFIXES``. The
    prefix-translation tests in ``tests/filters/test_inputs.py`` exercise the
    helper directly.
    """
    result: dict[str, str] = {}
    for filter_name in all_filters:
        prefix = filter_name[:1]
        if prefix in LOOKUP_PREFIXES:
            result[filter_name[1:]] = LOOKUP_PREFIXES[prefix]
    return result


# ---------------------------------------------------------------------------
# Module-global materialization (spec-027 Decision 9)
# ---------------------------------------------------------------------------


def materialize_input_class(name: str, cls: type[object]) -> None:
    """Set ``cls`` as a real module global of ``filters.inputs`` under ``name``.

    Thin family wrapper over the ``make_set_input_namespace`` materializer.
    See ``utils/inputs.py::materialize_generated_input_class`` for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, cls)``
    idempotency clause, and the distinct-class collision raise (spec-027
    Decision 9).
    """
    _materialize_input(name, cls)


def clear_filter_input_namespace() -> None:
    """Reset the filter-input ledger and per-filterset binding state for a fresh build.

    Thin family wrapper over the ``make_set_input_namespace`` heavy clear
    (ledger, ``_field_specs``, ``FilterArgumentsFactory`` caches, every
    ``FilterSet`` subclass's ``_lifecycle`` binding attrs). Materialized class
    objects stay parked in ``filters.inputs.__dict__`` per the parked-globals
    lifecycle stated on ``utils/inputs.py::make_input_namespace`` - which is what
    keeps held ``strawberry.lazy(...)`` LazyTypes resolving across an autouse
    reload that does not also reload the holder (``test_scalars_api.py`` reloads
    only its own app's schema).
    """
    _clear_input_namespace()


register_subsystem_clear(
    clear_filter_input_namespace,
    owner="filters.input_namespace",
    before_bind=True,
)
