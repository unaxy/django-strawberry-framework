"""Set-input traversal substrate shared by the FilterSet and OrderSet families.

FilterSet and OrderSet independently grew the SAME runtime walk over a generated
Strawberry input value: detect dict vs input-dataclass shape, decide which values
are active (``None`` / ``strawberry.UNSET``), resolve the per-field ``FieldSpec``
provenance, and classify each supplied top-level field as a leaf, a related
branch, or a logical operator. That classification was spelled inline at four
correctness-sensitive call sites -- the filter normalizer
(``filters/sets.py::FilterSet._normalize_input``), the order normalizer
(``orders/inputs.py::normalize_input_value``), and the permission walk
(``utils/permissions.py::active_permission_targets`` and its
``active_related_branches`` wrapper). A drift between any two copies in the active-input
decision is a real bug class -- a filter applied without its permission gate, a
related visibility hook skipped, work done on inactive input -- so the neutral
mechanics are single-sited here.

This module owns the *traversal mechanics* only; the family-specific *leaf
semantics* stay at the call sites:

* the filter normalizer keeps its per-field operator-bag iteration and the
  ``RangeFilter`` positional patch;
* the order normalizer keeps its ``Ordering`` direction handling and its
  recursion into child ordersets;
* the permission walkers keep the per-class ``check_*`` dedup and the
  parent-vs-child double dispatch.

Each consumer drives ``iter_active_fields`` with a ``SetInputTraversal`` config
and filters the yielded ``ActiveField`` records by ``kind``. It depends on no
family package (it operates on a duck-typed ``set_cls`` plus a config), so both
families import it without a cycle -- same contract as ``utils/permissions.py``
/ ``utils/connections.py`` / ``utils/inputs.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, NoReturn, cast

from strawberry.types.unset import UnsetType

from django_strawberry_framework.exceptions import ConfigurationError

from . import truth
from ._narrowing import dict_get, is_mapping, read_attr
from .canonical import base_container_values

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import TypeAlias

    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.orders.sets import OrderSet

    from .inputs import GeneratedInputFieldSpec

    #: A set family's field-spec map, keyed by ``(set class, python attr)``. Mapping
    #: keys are invariant, so each family's own map is its own member.
    FieldSpecMap: TypeAlias = (
        Mapping[tuple[type[FilterSet], str], GeneratedInputFieldSpec]
        | Mapping[tuple[type[OrderSet], str], GeneratedInputFieldSpec]
    )
    #: One active related branch: ``(field_name, related_obj, child_input)``. The
    #: declaration is read reflectively off the set class, so it is ``object`` here.
    RelatedBranch: TypeAlias = tuple[str, object, object]

# Default maximum traversal depth across set input graphs (logical operators and related branches).
# Sets with custom depth requirements (e.g. FilterSet._MAX_LOGIC_DEPTH) can override the class-level
# limit, while traversal algorithms (e.g. permission checks in utils/permissions.py) fall back to this
# neutral default.
DEFAULT_SET_INPUT_TRAVERSAL_DEPTH = 8

# ``ActiveField.kind`` markers. A supplied top-level field is exactly one of:
# a logical operator key (filter ``and_`` / ``or_`` / ``not_``), a related
# branch (a ``RelatedFilter`` / ``RelatedOrder`` declaration), or a leaf. The
# three are mutually exclusive -- the logical-operator attrs are never related
# names and related names are never logical -- so classification order between
# the logic and related checks is immaterial; ``iter_active_fields`` tests logic
# first to mirror ``FilterSet._normalize_input``'s original branch order.
LOGIC = "logic"
RELATED = "related"
LEAF = "leaf"


def _field_name(value: object, *, input_value: object) -> str:
    """Normalize one input key or reject it before lookup/permission dispatch.

    The key's real type decides (``truth.is_instance``): a ``__class__`` property can
    neither claim ``str`` for an object the base ``str`` slot refuses nor raise out of
    the check.
    """
    if not truth.is_instance(value, str):
        raise ConfigurationError(
            "Set input field names must be strings; received an invalid field name in an "
            f"input of type {truth.kind(input_value)}.",
        )
    return truth.text(value)


def _walk_error(input_value: object, detail: str) -> ConfigurationError:
    """Build a typed, safe traversal error for malformed consumer input."""
    return ConfigurationError(
        f"Could not traverse set input of type {truth.kind(input_value)}: {detail}.",
    )


def iter_input_items(input_value: object) -> list[tuple[str, object]] | None:
    """Walk a dict or Strawberry-input dataclass into ``(name, value)`` pairs.

    Returns ``None`` when ``input_value`` is neither a dict nor an object
    carrying ``__dataclass_fields__`` (the Strawberry-input sniff used
    package-wide -- faster than ``dataclasses.is_dataclass`` and matching the
    shape upstream uses to introspect input classes). Returns ``[]`` for a
    walkable-but-empty input.

    Single-sited here as the lowest-level traversal primitive; re-exported from
    ``utils/permissions.py`` so the existing
    ``from ..utils.permissions import iter_input_items`` consumers keep working.
    """
    if truth.is_instance(input_value, dict):
        pairs = base_container_values(input_value)
        return [(_field_name(name, input_value=input_value), value) for name, value in pairs]
    dataclass_fields: object = truth.static_attr(input_value, "__dataclass_fields__")
    if dataclass_fields is None:
        return None
    if not is_mapping(dataclass_fields):
        raise _walk_error(input_value, "its dataclass metadata is not a mapping")
    return [
        (field_name, read_attr(input_value, field_name))
        for field_name in (_field_name(name, input_value=input_value) for name in dataclass_fields)
    ]


def input_field_value(input_value: object, name: str) -> object:
    """Read ONE field off a dict-or-dataclass input; ``None`` when absent.

    The single-field sibling of ``iter_input_items``: the dict-vs-dataclass
    sniff (``.get`` vs ``getattr``) lives in exactly one module - this one,
    whose charter is the input-shape traversal primitives - so a caller that
    needs one branch value (``utils/permissions.py::extract_branch_value``)
    composes this with ``is_inactive_value`` instead of re-spelling the sniff.
    """
    field_name = _field_name(name, input_value=input_value)
    if truth.is_instance(input_value, dict):
        return dict_get(input_value, field_name)
    return getattr(input_value, field_name, None)


#: ``strawberry.UNSET``, typed as the instance it is. Strawberry annotates its sentinel ``Any``
#: so it can default a field of any type; ``UnsetType()`` hands back that one instance, so
#: ``value is UNSET`` holds for every ``strawberry.UNSET`` the engine supplies.
UNSET: Final[UnsetType] = UnsetType()


def is_inactive_value(value: object, *, unset_sentinel: object = None) -> bool:
    """Return ``True`` when ``value`` should be treated as "not supplied".

    The single active-input rule shared by every traversal surface: a value is
    inactive when it is ``None`` or the family's ``unset_sentinel``. Both shipped
    families pass ``unset_sentinel=strawberry.UNSET``: load-bearing on the filter
    side, whose operator-bag dataclasses default unsupplied lookups to ``UNSET``;
    defensive on the order side, whose generated inputs default unsupplied fields
    to ``None``, so the sentinel arm is inert there. Defined once so the
    ``UNSET`` / ``None`` decision cannot drift between the normalizers, the
    permission walkers, and ``extract_branch_value``.
    """
    return value is None or value is unset_sentinel


@dataclass(frozen=True)
class SetInputTraversal:
    """Family-specific configuration for ``iter_active_fields``.

    Carries everything the neutral walker needs to classify a supplied field
    without knowing filter / order leaf semantics:

    * ``field_specs`` -- the per-``(set_cls, python_attr)`` provenance map
      (``filters/inputs.py::_field_specs`` / ``orders/inputs.py::_field_specs``);
      consulted for every field so leaf and related consumers can read
      ``django_source_path`` off the yielded record.
    * ``related_attr`` -- the per-class related-collection attribute name
      (``"related_filters"`` / ``"related_orders"``); read off ``set_cls`` to
      recognize related branches.
    * ``logic_keys`` -- the python-attr tokens of the logical operators (filter
      ``and_`` / ``or_`` / ``not_``); empty for the order side, which has no
      logical operator bag.
    * ``unset_sentinel`` -- the family's "not supplied" sentinel
      (``strawberry.UNSET`` on both shipped families); threaded into
      ``is_inactive_value``.
    * ``handle_top_level_list`` -- the order side's top-level ``list[<T>]`` input
      shape; when set, a list ``input_value`` is flattened element-by-element.
    """

    field_specs: FieldSpecMap
    related_attr: str
    logic_keys: frozenset[str] = frozenset()
    unset_sentinel: object = None
    handle_top_level_list: bool = False


@dataclass(frozen=True)
class ActiveField:
    """One supplied, active top-level input field, classified.

    ``spec`` is the ``FieldSpec`` from ``config.field_specs`` (``None`` when the
    map has no entry -- a leaf consumer falls back to its own form-key rule, an
    order consumer skips defensively). ``related_obj`` is the declared
    ``RelatedFilter`` / ``RelatedOrder`` instance for a ``RELATED`` field and
    ``None`` otherwise.
    """

    python_attr: str
    raw_value: object
    spec: GeneratedInputFieldSpec | None
    kind: str
    related_obj: object = None


def set_traversal_depth_cap(set_cls: object) -> int:
    """Return the traversal-depth budget that governs ``set_cls``.

    ONE budget for both traversals over the same input tree: a ``FilterSet``
    declares ``_MAX_LOGIC_DEPTH`` (and consumers may raise it on a subclass),
    while an ``OrderSet`` has no such knob and takes
    ``DEFAULT_SET_INPUT_TRAVERSAL_DEPTH``. The resolution was written out at both
    the logical-branch walk and the permission walk, which is how one budget came
    to be enforced with two vocabularies.
    """
    declared = truth.static_attr(set_cls, "_MAX_LOGIC_DEPTH")
    return declared if truth.is_instance(declared, int) else DEFAULT_SET_INPUT_TRAVERSAL_DEPTH


def raise_set_traversal_depth_exceeded(
    set_cls: object,
    *,
    branch: str,
    input_noun: str,
    subject: str = "",
) -> NoReturn:
    """Raise the shared depth-cap ``ConfigurationError`` for ``set_cls``.

    The reason both walks cap at all is the same - a self-referential set
    (``CardFilter.dependencies`` -> ``CardFilter``) would otherwise recurse
    input-deep into a ``RecursionError`` instead of a typed error at the source -
    so the sentence is shared and only the three words that name WHICH walk hit
    the cap are per-caller.
    """
    cap = set_traversal_depth_cap(set_cls)
    label = truth.qualname(set_cls)
    if subject:
        label = f"{subject} {label}"
    cap_detail = (
        f"_MAX_LOGIC_DEPTH={cap}"
        if truth.static_attr(set_cls, "_MAX_LOGIC_DEPTH") is not None
        else f"the maximum traversal depth ({cap})"
    )
    raise ConfigurationError(
        f"{label}: {branch} nesting exceeded {cap_detail}. Flatten the "
        f"{input_noun} input or split into multiple queries.",
    )


def assert_set_traversal_depth(
    set_cls: object,
    depth: int,
    *,
    branch: str,
    input_noun: str,
    subject: str = "",
) -> None:
    """Fail closed when ``depth`` passes ``set_cls``'s traversal budget."""
    if depth > set_traversal_depth_cap(set_cls):
        raise_set_traversal_depth_exceeded(
            set_cls,
            branch=branch,
            input_noun=input_noun,
            subject=subject,
        )


class RelatedDeclarationError(Exception):
    """A set's related-declaration attribute is not a mapping.

    An internal signal, never surfaced: :func:`related_declaration_mapping`
    raises it and every caller translates it into that caller's own
    ``ConfigurationError`` prose (the permission walker names the declaring
    class and attribute; the input traversal names the input type). ``kind``
    is ``"not_mapping"`` and ``value`` carries the rejected declaration.
    """

    def __init__(self, kind: str, value: object = None) -> None:
        """Carry the failure ``kind`` and the offending ``value``."""
        super().__init__(kind)
        self.kind: str = kind
        self.value: object = value


def related_declaration_mapping(owner: object, related_attr: str) -> Mapping[object, object]:
    """Read a set's related-declaration attribute and prove it is a mapping.

    The shared front half of every related-branch traversal: read the attribute
    from the class's real namespaces (``truth.static_attr``), treat an absent or ``None``
    declaration as "no related fields", and reject anything that is not a
    ``Mapping`` before a caller starts indexing it. The permission walker and
    the neutral input traversal both need exactly this and had it written out
    twice, so a new rule about what a related declaration may BE would have had
    to be added in both places.

    What stays per-caller is what each does with the mapping - the permission
    walker materializes it through the UNBOUND ``dict.items`` (an ``items``
    override must not run inside an authorization walk), while the traversal
    reads membership lazily. Those are different contracts, not a missed merge.

    Raises :class:`RelatedDeclarationError` for the caller to translate.
    """
    related: object = truth.static_attr(owner, related_attr)
    if related is None:
        return {}
    if not is_mapping(related):
        raise RelatedDeclarationError("not_mapping", related)
    return related


def iter_active_fields(
    set_cls: type[object],
    input_value: object,
    config: SetInputTraversal,
) -> Iterator[ActiveField]:
    """Yield one ``ActiveField`` per supplied, active top-level field of ``input_value``.

    Owns the mechanics every consumer would otherwise re-spell:

    * the ``None`` / ``unset_sentinel`` inactive-value skip (via
      ``is_inactive_value``), applied to the whole input and to each field;
    * the dict-vs-dataclass walk (via ``iter_input_items`` -- a non-walkable
      input yields nothing);
    * the order side's top-level ``list[<T>]`` flattening
      (``handle_top_level_list``), recursing per element so each element's
      fields stream out in order;
    * the per-field ``FieldSpec`` lookup;
    * the leaf / related / logic classification.

    It does NOT recurse into child set inputs -- a ``RELATED`` field carries its
    raw child value on the record and the consumer recurses with the
    family-appropriate entry point (the order normalizer re-enters
    ``normalize_input_value``; the filter normalizer strips the branch and lets
    ``_apply_related_constraints`` own it). Leaf shape (operator bags, ranges,
    directions) is the consumer's business too; this walker only marks the kind.
    """
    unset_sentinel = config.unset_sentinel
    handle_top_level_list = config.handle_top_level_list
    if is_inactive_value(input_value, unset_sentinel=unset_sentinel):
        return
    if handle_top_level_list and truth.is_instance(input_value, list):
        elements = base_container_values(input_value)
        for element in elements:
            if is_inactive_value(element, unset_sentinel=unset_sentinel):
                continue
            if truth.is_instance(element, list) or iter_input_items(element) is None:
                raise ConfigurationError(
                    "Order input list elements must be mapping or dataclass values; "
                    f"received {truth.kind(element)}.",
                )
            yield from iter_active_fields(set_cls, element, config)
        return
    items = iter_input_items(input_value)
    if items is None:
        return
    try:
        related = related_declaration_mapping(set_cls, config.related_attr)
    except RelatedDeclarationError:
        raise _walk_error(input_value, "related-field declarations are not a mapping") from None
    for python_attr, raw_value in items:
        if is_inactive_value(raw_value, unset_sentinel=unset_sentinel):
            continue
        # Every class is a valid probe: an identity lookup by a wider key is sound, so
        # the family's map is read through its class-keyed view.
        spec = cast(
            "Mapping[tuple[type[object], str], GeneratedInputFieldSpec]",
            config.field_specs,
        ).get((set_cls, python_attr))
        if python_attr in config.logic_keys:
            yield ActiveField(python_attr, raw_value, spec, LOGIC)
        elif python_attr in related:
            yield ActiveField(python_attr, raw_value, spec, RELATED, related[python_attr])
        else:
            yield ActiveField(python_attr, raw_value, spec, LEAF)
