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
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from types import GenericAlias, MappingProxyType
from typing import TYPE_CHECKING, Annotated, cast

import strawberry
from django import forms
from django.db import models
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
from django_filters.filters import BaseCSVFilter, QuerySetRequestMixin
from strawberry import relay

from django_strawberry_framework.conf import hide_flat_filters_setting
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import register_subsystem_clear
from django_strawberry_framework.sets_mixins import declaration_map
from django_strawberry_framework.types.converters import scalar_for_field
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    dict_of,
    enum_value,
    is_list_or_tuple,
    is_mapping,
    optional_annotation,
    read_attr,
    require,
)
from django_strawberry_framework.utils.converters import convert_with_mro
from django_strawberry_framework.utils.input_values import (
    UNSET,
    is_inactive_value,
    iter_input_items,
)
from django_strawberry_framework.utils.inputs import (
    GeneratedInputFieldSpec,
    build_strawberry_input_class,
    emit_set_input_field_triples,
    iter_set_subclasses,
    make_set_input_namespace,
    optional_field_kwargs,
    set_input_type_name,
)
from django_strawberry_framework.utils.strings import (
    flatten_lookup_path,
    graphql_camel_name,
    pascal_case_or_raise,
)
from django_strawberry_framework.utils.widgets import multi_widget_keys, widget_keys

from .base import (
    _RANGE_BOUNDS,
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
    _bound_field_name,
    _EnumMemberFilterMixin,
    _filterset_model_field,
    copied_form_field,
    model_choice_identity_column,
    relation_identity_column,
    unkept_form_field,
)

# Domain-local aliases for the shared generated-input substrate (the mechanics
# are single-sited in ``utils/inputs.py``); the spec-027 Decision 9 names stay
# addressable from this module.
FieldSpec = GeneratedInputFieldSpec
build_input_class = build_strawberry_input_class
_camel_case = graphql_camel_name
_iter_filterset_subclasses = iter_set_subclasses
_input_type_name_for = set_input_type_name

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from django_strawberry_framework.types.definition import DjangoTypeDefinition
    from django_strawberry_framework.utils.inputs import SetInputNamespace
    from django_strawberry_framework.utils.typing import ConcreteField, ModelField

    from .sets import FilterSet, _LeafDeclaration

# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so the factory, ``_build_logic_fields``, and
# ``filter_input_type`` (in ``__init__.py``) all stay in sync.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.filters.inputs"


# Search-prefix vocabulary for the future `Meta.search_fields` card per
# spec-027 Decision 2; consumed by `construct_search` below.
LOOKUP_PREFIXES: dict[str, str] = {
    "^": "istartswith",
    "=": "iexact",
    "@": "search",
    "$": "iregex",
}


# `django-filter` lookup -> (python_attr, graphql_name) pair per spec-027
# Decision 3 Layer 5. Strawberry's auto-camel-case
# cannot transform `icontains` to `iContains` (no underscore to split on),
# and the Python keyword `in` cannot be a dataclass field - both are pinned
# here. Consumed by `filter_lookup_table` (keying each head's lookups by their
# Python attr, the names `FilterSet._normalize_input` reads), by
# `_build_input_fields` (for `strawberry.field(name=...)` emission), and by
# `FilterSet._operator_bag_items` (recognizing a hand-built operator bag).
LOOKUP_NAME_MAP: dict[str, tuple[str, str]] = {
    "exact": ("exact", "exact"),
    "iexact": ("i_exact", "iExact"),
    "contains": ("contains", "contains"),
    "icontains": ("i_contains", "iContains"),
    "startswith": ("starts_with", "startsWith"),
    "istartswith": ("i_starts_with", "iStartsWith"),
    "endswith": ("ends_with", "endsWith"),
    "iendswith": ("i_ends_with", "iEndsWith"),
    "regex": ("regex", "regex"),
    "iregex": ("i_regex", "iRegex"),
    "gt": ("gt", "gt"),
    "gte": ("gte", "gte"),
    "lt": ("lt", "lt"),
    "lte": ("lte", "lte"),
    "isnull": ("is_null", "isNull"),
    "in": ("in_", "in"),
    "range": ("range", "range"),
    "date": ("date", "date"),
    "year": ("year", "year"),
    "month": ("month", "month"),
    "day": ("day", "day"),
    "week_day": ("week_day", "weekDay"),
    "quarter": ("quarter", "quarter"),
    "hour": ("hour", "hour"),
    "minute": ("minute", "minute"),
    "second": ("second", "second"),
}


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
_field_specs: dict[tuple[type[FilterSet], str], FieldSpec]
_namespace: SetInputNamespace[FilterSet] = make_set_input_namespace(
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
    ``_build_range_input_class`` only. Indirect callers
    (``_input_type_name_for``, ``_build_input_fields``'s operator-bag class
    naming) route through
    ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`` and trip the
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
    """Pick a Strawberry-compatible scalar for a Django form field.

    Used by ``convert_filter_to_input_annotation`` for the
    ``CharFilter`` / ``NumberFilter`` / ``BooleanFilter`` catch-all
    branch. Form-field class -> Python scalar mapping derived by direct
    inspection of ``django.forms``; ``CharField`` is the catch-all (it's
    what every text-shaped filter falls through to).
    """
    if isinstance(form_field, forms.NullBooleanField):
        return bool
    if isinstance(form_field, forms.BooleanField):
        return bool
    # ``DecimalField`` and ``FloatField`` BOTH subclass ``IntegerField`` in
    # ``django.forms`` (the form-field hierarchy differs from the model-field
    # one, where they descend straight from ``Field``). They MUST be matched
    # before the ``IntegerField`` catch below; otherwise a decimal- or
    # float-backed filter mis-maps to ``int``. ``DecimalField`` and
    # ``FloatField`` are siblings (neither subclasses the other), so the
    # order between them is immaterial.
    if isinstance(form_field, forms.DecimalField):
        return decimal.Decimal
    if isinstance(form_field, forms.FloatField):
        return float
    if isinstance(form_field, forms.IntegerField):
        return int
    if isinstance(form_field, forms.DateTimeField):
        return datetime.datetime
    if isinstance(form_field, forms.DateField):
        return datetime.date
    if isinstance(form_field, forms.TimeField):
        return datetime.time
    if isinstance(form_field, forms.UUIDField):
        return uuid.UUID
    # Both ``CharField`` and the catch-all map to ``str``. The explicit
    # ``CharField`` branch is kept for documentation: the conversion
    # table in spec-027 Decision 4 lists ``CharFilter`` as a recognized
    # shape, and a future reader who inspects this function should see
    # that the mapping is intentional, not an accidental fallthrough.
    if isinstance(form_field, forms.CharField):
        return str
    return str


def _scalar_from_model_field(model_field: ModelField | None) -> object:
    """Map a Django model field to its scalar via the shared ``SCALAR_MAP`` lookup.

    Delegates to ``types/converters.py::scalar_for_field`` -- a LOCAL import, to
    avoid the top-level cycle through ``converters`` (same pattern as
    ``_choice_enum_from_filter``) -- so a filter input and the selected
    ``DjangoType`` field resolve a column to the SAME GraphQL scalar, including
    consumer-registered ``SCALAR_MAP`` entries and the ``BigInt`` scalar for
    64-bit columns. An unsupported field raises the same ``ConfigurationError``
    as field selection rather than silently degrading to ``str``. ``None`` (a
    method filter with no backing model field) keeps the ``str`` fallback.
    """
    if model_field is None:
        return str

    # A ``SCALAR_MAP`` value is a registered runtime annotation (a class or ``NewType``).
    return scalar_for_field(model_field)


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


def _relation_identity_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None = None,
) -> object:
    """Type a raw-pk relation leaf from the target's primary-key column.

    The scalar comes from ``filters/base.py::relation_identity_column`` through the
    shared ``SCALAR_MAP`` lookup, so the input agrees with how a ``DjangoType`` types
    that key (``Int``, ``UUID``, ``BigInt``, ...). A raw-pk filter whose ``field_name``
    resolves no relation on its ``FilterSet`` model has no column to type from; the
    refusal names the filter as declared (``_declaration_of``).
    """
    column = relation_identity_column(model_field)
    if column is None:
        declaration = _declaration_of(filter_instance, filterset_cls)
        declared = declaration.declared
        raise ConfigurationError(
            f"{declaration.kind} on {truth.render(declared)}{declaration.site} names "
            f"{truth.render(getattr(declared, 'field_name', None))}, which is not a "
            "relation to a model on its FilterSet; name a relation key in Meta.fields, or "
            "filter the related row's own fields through a RelatedFilter.",
        )
    return _scalar_from_model_field(column)


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


def _model_choice_identity_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None,
) -> object:
    """Type one value of a consumer model-choice filter from the column its form cleans.

    The column is ``filters/base.py::model_choice_identity_column``'s (the ``queryset``
    model's primary key or ``to_field_name`` field, or the ``field_name`` relation's
    target for a callable ``queryset``) through the shared ``SCALAR_MAP`` lookup. The
    filter keeps its own form field, so its ``queryset`` still validates every value.
    The refusal names the filter as declared (``_declaration_of``).
    """
    column = model_choice_identity_column(filter_instance, model_field)
    if column is None:
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{declaration.owner(filterset_cls)}: {declaration.kind} on "
            f"{truth.render(getattr(declaration.declared, 'field_name', None))}"
            f"{declaration.route} has no model queryset (its queryset is callable or unset) "
            "and its field_name names no relation on the FilterSet model, so there is no "
            "column to type its input from. Pass a model queryset, or point field_name at a "
            "relation.",
        )
    return _scalar_from_model_field(column)


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
    ``ChoiceFilter`` on a plain column or a ``method=`` path, and django-filter's ``ChoiceFilter``
    subclasses ``AllValuesFilter`` and ``DateRangeFilter``, whose choices are the
    column's distinct values or fixed date-range keys.

    ``model_field`` is threaded as a parameter rather than stashed on
    the filter instance - keeps the filter stateless and avoids the
    "side-effect on a filter during input-class construction" trap.
    """
    # Local import to avoid a top-level cycle through ``types.converters``.
    from django_strawberry_framework.types.converters import convert_choices_to_enum  # noqa: PLC0415 - import cycle

    if model_field is None or not getattr(model_field, "choices", None):
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{declaration.kind} on {truth.render(declaration.declared)}{declaration.site} "
            "is backed by no model field declaring `choices`; declare `choices` on the column "
            "it filters (a `TextChoices` / `IntegerChoices` class), or filter that column "
            "through a non-choice filter (`CharFilter`, `NumberFilter`, "
            "`DateFromToRangeFilter`, its lookups in Meta.fields, or `CharFilter(method=...)` "
            "for a method filter).",
        )
    # Past the guard the field declares truthy ``choices``, which only a concrete
    # ``Field`` carries (a reverse ``ForeignObjectRel`` has no ``choices``).
    return convert_choices_to_enum(cast("ConcreteField", model_field), type_name)


def _element_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    owner_definition: DjangoTypeDefinition | None,
    filterset_cls: type[FilterSet] | None = None,
) -> object:
    """Single-element Strawberry type with the MODEL FIELD as source of truth.

    A backing model field's choices become the shared GraphQL enum and its
    column type becomes the scalar (including the ``BigInt`` scalar for 64-bit
    columns). The ``django-filter`` form field is consulted ONLY as the
    fallback for a custom ``method=`` filter with no backing model field --
    otherwise ``django-filter``'s ``NumberFilter`` form (a ``DecimalField``)
    mis-types integer columns and a CSV ``in`` over a choice column collapses
    to ``str``. Callers that need a different shape for a specific lookup (e.g.
    ``isnull`` is always boolean) handle that before calling this.

    One lookup-driven arm comes first: a generated text-pattern leaf on a
    non-text column (``FilterSet.filter_for_lookup`` gives it ``TextPatternFilter``)
    is ``str``, never the column's scalar or choice enum, because the pattern is
    matched against the column's text rendering. A declared filter or a
    ``Meta.filter_overrides`` selection keeps the column-driven type.

    Known contract limit: a custom ``method=`` filter has no backing
    ``model_field``, so its element type is inferred from the
    ``django-filter`` form field and a CSV/list ``method=`` filter therefore
    yields ``list[str]`` even when the column it ultimately queries is an
    ``int``. To get a typed element on a method filter, back it with a model
    field (``field_name=``) or declare the input annotation explicitly.
    """
    if truth.is_instance(filter_instance, TextPatternFilter):
        return str
    if model_field is not None and getattr(model_field, "choices", None):
        type_name = _owner_type_name(owner_definition) or "Filter"
        return _choice_enum_from_filter(filter_instance, type_name, model_field, filterset_cls)
    if model_field is not None:
        return _scalar_from_model_field(model_field)
    form_field = _declared_form_field(filter_instance)
    return (
        _scalar_from_form_field(form_field)
        if form_field is not None
        else _scalar_from_model_field(model_field)
    )


# ---------------------------------------------------------------------------
# Public converter pair
# ---------------------------------------------------------------------------


# Most-specific-first filter-class order. Convert and normalize both walk this
# via ``convert_with_mro`` so a new primitive cannot be typed on one ladder and
# coerced on the other (spec-053 C3). The consumer model-choice pair sits after
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

    Last precheck is ``object`` (the original ``else``), so a real dispatch
    never reaches here, and no handler returns ``MRO_CONTINUE``. The factory
    keeps ``convert_with_mro``'s raising contract all the same.
    """
    return ConfigurationError(
        f"internal: filter input dispatch reached fallthrough for {truth.render(obj)}",
    )


def _refuse_method_without_form_field(
    filter_instance: Filter,
    filterset_cls: type[FilterSet] | None,
) -> None:
    """Refuse a ``method=`` filter whose class builds no form field on the unbound declaration.

    Nothing can type such a filter's input: ``AllValuesMultipleFilter`` reads the
    per-request ``model`` to build its field, so unbound it builds none. The refusal
    names the filter as declared (``_declaration_of``).
    """
    form_field = _declared_form_field(filter_instance)
    method = read_attr(filter_instance, "method", None)
    if method is None or form_field is not None:
        return
    declaration = _declaration_of(filter_instance, filterset_cls)
    raise ConfigurationError(
        f"{declaration.kind}(method={truth.render(method)}) on "
        f"{truth.render(declaration.declared)}{declaration.site} exposes no form "
        "field; put the method on a typed filter primitive (`CharFilter(method=...)`, "
        "`NumberFilter(method=...)`, `ListFilter(method=...)` for a list value, ...) "
        "or on a `Filter` subclass declaring `field_class` at class level.",
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
    ``filters/base.py::model_choice_identity_column`` reads it: a callable one is called
    with the request, which the schema build has none of, and an unset one builds no field
    (the model-choice arm names that refusal).
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
        f"{declaration.owner(filterset_cls)}: {declaration.kind} on "
        f"{truth.render(declaration.declared.field_name)}{declaration.route} publishes one "
        f"value under its form-data key {_FORM_KEY}, but its form field's widget reads "
        f"{', '.join(keys)}, so the value would never be read. Declare a RangeFilter (the "
        "package's or django-filter's) for a two-bound range, or give the filter a form field "
        f"whose widget reads one key.{numeric_range}",
    )


def convert_filter_to_input_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    owner_definition: DjangoTypeDefinition | None = None,
    filterset_cls: type[FilterSet] | None = None,
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
    ``TypedMultipleChoiceFilter.coerce``), then the ``object`` catch-all (the original
    ``else``).
    ``method=...`` filters
    that expose no form field raise ``ConfigurationError``.

    Dispatch rides ``utils/converters.py::convert_with_mro`` with the same
    kind table ``normalize_input_value`` uses.

    ``filterset_cls`` (the owning ``FilterSet`` for a leaf built through
    ``_build_input_fields``) qualifies the nested ``RangeFilter`` sub-input
    class name so two filtersets sharing a ``field_name`` mint two distinct
    GraphQL type names (spec-027 forward path; see ``_build_range_input_class``,
    which also covers the set/field splits that still meet). ``None`` (direct
    converter callers) keeps the unqualified ``<Field>RangeInputType`` name.

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
    if truth.is_instance(filter_instance, LookupChoiceFilter):
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{declaration.owner(filterset_cls)}: {declaration.kind} on "
            f"{truth.render(declaration.declared.field_name)}{declaration.route} filters by "
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
        element = _model_choice_identity_annotation(matched, model_field, filterset_cls)
        return GenericAlias(list, (element,)) if _model_choice_takes_list(matched) else element

    def _csv(matched: Filter) -> object:
        # django-filter expands ``Meta.fields`` ``in`` / ``range`` lookups
        # into ``BaseInFilter`` / ``BaseRangeFilter`` (both ``BaseCSVFilter``
        # subclasses) whose form field consumes a LIST of values, not a
        # scalar. The element type is model-field-driven so a CSV ``in`` over
        # a choice column keeps its enum and a 64-bit column keeps ``BigInt``.
        element = _element_annotation(matched, model_field, owner_definition, filterset_cls)
        return GenericAlias(list, (element,))

    def _multiple_choice(matched: Filter) -> object:
        # The form field (``MultipleChoiceField``) cleans a list; each element is typed
        # from the model column like a ``ListFilter``'s (spec-027 Decision 4).
        _refuse_method_without_form_field(matched, filterset_cls)
        element = _element_annotation(matched, model_field, owner_definition, filterset_cls)
        return GenericAlias(list, (element,))

    def _range(matched: Filter) -> object:
        # Refuse a widget the patch cannot address when the schema is built, not per request.
        _ = range_form_keys(matched, matched.field_name or "range", filterset_cls)
        inner = _scalar_from_model_field(model_field)
        return _build_range_input_class(matched, inner, filterset_cls)

    def _list(matched: Filter) -> object:
        element = _element_annotation(matched, model_field, owner_definition, filterset_cls)
        return GenericAlias(list, (element,))

    def _typed(matched: Filter) -> object:
        return _element_annotation(matched, model_field, owner_definition, filterset_cls)

    def _choice(matched: Filter) -> object:
        type_name = _owner_type_name(owner_definition) or "Filter"
        return _choice_enum_from_filter(matched, type_name, model_field, filterset_cls)

    def _catchall(matched: Filter) -> object:
        # Catch-all scalar branch: a ``method=`` filter is typed from its model column, else
        # from the form field its class builds; one whose ``field`` builds none on the
        # unbound declaration raises (spec-027 Decision 4).
        _refuse_method_without_form_field(matched, filterset_cls)
        if getattr(matched, "lookup_expr", None) == "isnull":
            # ``isnull`` is a boolean predicate regardless of the column type;
            # the model field (the column's value type) is irrelevant here.
            return bool
        return _element_annotation(matched, model_field, owner_definition, filterset_cls)

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
    The schema declares every such input as a GraphQL list, so the wire can
    only deliver a list; the reachable non-list shapes are direct-Python
    ``apply_sync`` caller mistakes. Iterating one would splat it: a
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
            "send a list (the GraphQL schema already rejects this shape over the wire).",
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
    filterset_cls: type[FilterSet] | None = None,
) -> type[object]:
    """Return a Strawberry input dataclass with ``start: T | None`` and ``end: T | None``.

    Each call builds a fresh class and nothing caches it: the name and axes depend
    only on the owning filterset, the Django field path and the inner scalar, and
    the arguments factory builds each filterset's input once per generation.

    The class name is qualified by the owning ``FilterSet`` when one is
    supplied -- ``f"{filterset_cls.__name__}{Pascal(field_name)}RangeInputType"``
    -- mirroring the per-field operator-bag naming
    (``ClassBasedTypeNameMixin.type_name_for``). Without this qualifier the name
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
    a schema serving both. ``None`` (direct converter callers that build no
    schema) keeps the unqualified ``<Field>RangeInputType`` name.
    """
    field_name = getattr(filter_instance, "field_name", "field") or "field"
    prefix = truth.name(filterset_cls) if filterset_cls is not None else ""
    cls_name = f"{prefix}{_pascal_case(field_name)}RangeInputType"
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
    package's one dict-or-input-dataclass walk. The schema types every range
    input as the ``{start, end}`` object, so the wire delivers nothing else; a
    value that walk cannot read (a list, a scalar, an arbitrary object) or that
    carries a key other than ``start`` / ``end`` is a hand-built mapping's
    mistake. Its values would never be read, so it raises the typed
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
            "input object with 'start' / 'end' (the GraphQL schema already rejects this "
            "shape over the wire).",
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

    The widget is the one the filter's form field builds (``filters/base.py::unkept_form_field``,
    which writes nothing to a class-level declaration every request shares), asked for its
    keys through ``utils/widgets.py::multi_widget_keys``. A widget that does not read exactly
    two keys has no slot for a start and an end, so it is a ``ConfigurationError`` naming
    the filter as declared on ``filterset_cls`` (``_declaration_of``);
    ``convert_filter_to_input_annotation`` runs this when the schema is built.
    """
    keys = multi_widget_keys(read_attr(unkept_form_field(filter_instance), "widget"), base)
    if keys is None or len(keys) != _RANGE_BOUNDS:
        declaration = _declaration_of(filter_instance, filterset_cls)
        raise ConfigurationError(
            f"{declaration.kind} consumes a range input for its {base!r} "
            f"input{declaration.site}, but its form field's widget does not read exactly two "
            f"form-data keys ({truth.render(keys)}); give it a two-widget MultiWidget.",
        )
    return keys[0], keys[1]


def _owner_type_name(owner_definition: DjangoTypeDefinition | None) -> str | None:
    """Return the GraphQL type name for ``owner_definition`` (or ``None``).

    Delegates to ``DjangoTypeDefinition.graphql_type_name`` so the three
    callers (this helper, ``filters/base.py::_accepted_globalid_type_names``
    for its schema-less spelling, ``types/finalizer.py::_bind_filterset_owner``)
    share one derivation rule and cannot drift across renames.
    """
    return owner_definition.graphql_type_name if owner_definition is not None else None


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
            optional_field_kwargs(op.python_attr, op.wire_name),
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
    to the set declaring it. The child set's declarations answer, never a stamp
    on the copy, which a set borrowing the same object restamps.
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
    return _bound_field_name(filter_instance)


def _group_filters_by_head(
    filterset_cls: type[FilterSet],
    all_filters: Mapping[str, Filter],
) -> tuple[OrderedDict[str, OrderedDict[str, FormKeyedFilter]], set[str]]:
    """Group a published filter table by input head, keeping each lookup's own form key.

    A declared filter, and a ``RelatedFilter`` expansion of a child's declared
    filter, is its own head: its name is its form key even when it ends in its
    own lookup token (``name__exact``). A generated ``<path>__<lookup>`` entry
    joins the ``<path>`` head under ``<lookup>``. Two filters claiming one
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
            # django-filter names a generated filter ``<path>__<lookup>``, or the
            # bare ``<path>`` for ``exact``; a trailing token that is not the
            # filter's own lookup belongs to the path.
            head, _, lookup_token = filter_name.rpartition("__")
            if not head or lookup_token != lookup_expr:
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
    two heads sharing one alias raise, since one would be unreachable.
    """
    all_filters = filterset_cls._filter_table()
    cached = filterset_cls._lookup_table
    if cached is not None and cached.source is all_filters:
        return cached
    heads, declared_heads = _group_filters_by_head(filterset_cls, all_filters)
    by_input_attr: dict[str, Mapping[str, FormKeyedFilter]] = {}
    gate_paths: dict[str, str] = {}
    for head, bag in heads.items():
        by_input_attr[head] = {
            LOOKUP_NAME_MAP.get(token, (token, token))[0]: entry for token, entry in bag.items()
        }
        _form_key, sample_filter = next(iter(bag.values()))
        # A declared head gates on its own name; so does an expansion of a child's
        # declared filter, whose flat spelling must fire the gates its nested twin
        # fires (``utils/permissions.py::_fire_flat_relation_path_gates`` walks the
        # relation hops and fires the child's ``check_<name>_permission``).
        gate_paths[head] = head if head in declared_heads else _bound_field_name(sample_filter)
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
    # ``django-graphene-filters``'s key of the same name) controls whether the
    # flat relational traversal fields (``categoryName``, deep
    # ``entriesPropertyCategoryName``, ...) are emitted. When hidden, the
    # relation is filtered only through its nested ``RelatedFilter`` branch
    # (``category: { name: { ... } }``) -- the strawberry-django shape. When
    # shown, BOTH the flat and nested shapes appear, a surface this package
    # adds: upstream never publishes the expanded copies (its ``filter`` input
    # renders a ``RelatedFilter`` as a reference to the target's input, and its
    # flat connection arguments, the ones its key hides, drop every expanded
    # child through the ``is_expanded_child`` test in
    # ``django_graphene_filters/connection_field.py::_get_trimmed_filterset_class``).
    # Because this package emits a single Strawberry input type here, the same
    # ``is_expanded_child`` rule is just a skip in this loop, so the hidden
    # operator-bag classes are never built in the first place. The key is read
    # through its ``conf.py`` named reader; truthiness coercion is this
    # consumer's own semantics (the reader stays thin).
    hide_flat_filters = bool(hide_flat_filters_setting())

    def _visible_entries() -> Iterator[tuple[str, Mapping[str, FormKeyedFilter]]]:
        """Yield the grouped entries minus the ``HIDE_FLAT_FILTERS`` expanded children.

        A flat relational traversal path (``category__name``,
        ``entries__property__category__name``) is an "expanded child" of a
        declared ``RelatedFilter`` - its first path segment names the relation.
        Such paths are reachable through the nested branch already; hide them
        when ``HIDE_FLAT_FILTERS`` is set -- the ``is_expanded_child`` skip
        upstream applies to its flat connection arguments unconditionally inside
        ``django_graphene_filters/connection_field.py::_get_trimmed_filterset_class``.
        This pre-filter stays filter-family semantics, BEFORE the shared
        emission scaffold.
        """
        for top_name, lookup_bag in lookup_table.heads.items():
            if (
                hide_flat_filters
                and "__" in top_name
                and top_name.split("__", 1)[0] in related_filters
            ):
                continue
            yield top_name, lookup_bag

    def _related_target_of(
        top_name: str,
        _lookup_bag: Mapping[str, FormKeyedFilter],
    ) -> tuple[bool, type[FilterSet] | None]:
        rel_filter = related_filters.get(top_name)
        if rel_filter is None:
            return False, None
        return True, rel_filter.filterset

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
            lookup_python_attr, lookup_graphql_name = LOOKUP_NAME_MAP.get(lookup, (lookup, lookup))
            model_field = _filterset_model_field(filterset_cls, leaf_filter)
            annotation = convert_filter_to_input_annotation(
                leaf_filter,
                model_field,
                owner_definition,
                filterset_cls,
            )
            bag_specs.append(
                (
                    lookup_python_attr,
                    annotation,
                    optional_field_kwargs(lookup_python_attr, lookup_graphql_name),
                ),
            )
        bag_class = build_input_class(bag_name, bag_specs)
        # The ``FieldSpec`` source path is the head's permission gate path;
        # the form keys the normalizer emits come from the lookup table.
        return bag_class | None, lookup_table.gate_paths[top_name]

    # The per-field emission scaffold (python-attr flatten -> camel-case ->
    # optional kwargs -> related lazy-ref vs leaf -> triple + ``FieldSpec``) is
    # single-sited in ``utils/inputs.py::emit_set_input_field_triples``; the
    # closures above carry the filter-family semantics.
    return emit_set_input_field_triples(
        filterset_cls,
        _visible_entries(),
        related_target_of=_related_target_of,
        related_source_path_of=lambda top_name, _lookup_bag: top_name,
        leaf_of=_leaf_of,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
        field_specs=_field_specs,
    )


def construct_search(all_filters: Mapping[str, object]) -> dict[str, str]:
    """Translate ``LOOKUP_PREFIXES``-vocabulary keys into a ``{name: lookup}`` map.

    No package code calls it yet: the ``Meta.search_fields`` consumer surface is
    spec-060's, and its wiring point is the ``TODO(spec-060 Slice 1)`` anchor in
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
