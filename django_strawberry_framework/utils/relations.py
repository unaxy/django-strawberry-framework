"""Relation-shape helpers shared by converters, resolvers, the optimizer, and input selectors."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Literal, Protocol, TypeAlias, TypeGuard, cast, overload

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Field
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.reverse_related import ForeignObjectRel

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    LookupValidationError,
    PathResolutionError,
)
from django_strawberry_framework.utils._narrowing import is_class, is_list_or_tuple, read_attr
from django_strawberry_framework.utils.typing import MISSING_ATTRIBUTE

from . import truth

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from django.db.models.expressions import Col
    from django.db.models.lookups import Lookup, Transform
    from django.db.models.options import Options
    from django.db.models.query_utils import PathInfo
    from typing_extensions import TypeIs

    from .typing import ConcreteField, ForeignKeyField, ModelField

__all__ = [
    "MANY_SIDE_RELATION_KINDS",
    "ClassifiedPath",
    "RelationKind",
    "RelationLink",
    "RelationPathHop",
    "carrier_backed_link",
    "classify_path",
    "has_composite_pk",
    "instance_accessor",
    "is_forward_concrete_relation",
    "is_forward_many_to_many",
    "is_forward_single_relation",
    "is_many_side_relation_kind",
    "is_model_class",
    "is_single_column_foreign_key",
    "m2m_through_link_fields",
    "m2m_through_model",
    "non_pk_forward_link",
    "non_pk_relation_key_attname",
    "order_column_paths",
    "path_traverses_to_many",
    "relation_bool",
    "relation_kind",
    "relation_link",
    "relation_name",
    "stored_value_column",
    "validate_lookup_expr",
]


def is_model_class(value: object) -> TypeIs[type[models.Model]]:
    """Return whether ``value`` is a Django model class, asked of its real type."""
    return is_class(value) and issubclass(value, models.Model)


RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
    "generic",
]

MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {"many", "reverse_many_to_one", "generic"},
)


def relation_bool(field: object, name: str, *, default: bool = False) -> bool:
    """Read one relation flag off a Django field (or ``FieldMeta``), requiring a ``bool``.

    An absent or ``None`` flag takes ``default``; any other non-``bool`` is
    malformed metadata and a configuration error, so a truthy non-bool never
    silently passes for ``True``.
    """
    value: object = getattr(field, name, default)
    if value is None:
        value = default
    if type(value) is not bool:
        raise ConfigurationError(
            f"Relation metadata {name!r} on {truth.kind(field)} must be a bool; "
            f"got {truth.kind(value)}.",
        )
    return value


def relation_name(field: object, name: str) -> str | None:
    """Read an optional GenericRelation field-name slot, requiring a ``str`` or ``None``."""
    value = read_attr(field, name, None)
    if value is not None and type(value) is not str:
        raise ConfigurationError(
            f"Relation metadata {name!r} on {truth.kind(field)} must be a string or "
            f"None; got {truth.kind(value)}.",
        )
    return value


class _RelationFieldLike(Protocol):
    """Shape contract for the five Django relation flags the relation classifiers read.

    Every caller in the package hands in a real Django relation field or rel
    descriptor whose ``many_to_many`` / ``one_to_many`` / ``one_to_one`` /
    ``auto_created`` / ``concrete`` attributes are always present. The narrower
    annotation documents the read contract; ``getattr(..., False)`` in the body
    still defends against shapes that omit a flag. The flags are read, never
    written, and a ``None`` reads as ``False`` (a plain Django ``Field`` carries
    ``None`` in the three cardinality slots), so a read-only snapshot such as
    ``FieldMeta`` satisfies the contract as well.
    """

    @property
    def many_to_many(self) -> bool | None: ...
    @property
    def one_to_many(self) -> bool | None: ...
    @property
    def one_to_one(self) -> bool | None: ...
    @property
    def auto_created(self) -> bool | None: ...
    @property
    def concrete(self) -> bool | None: ...


class _TraversableRelationLike(_RelationFieldLike, Protocol):
    """A relation whose ``path_infos`` a path walk can follow."""

    @property
    def path_infos(self) -> Sequence[PathInfo]: ...


def relation_kind(field: object) -> RelationKind:
    """Classify a Django relation field by GraphQL/runtime cardinality.

    Five shapes are distinguished:

    - ``"many"`` - a many-to-many relation from either side (``many_to_many=True``:
      a forward ``ManyToManyField`` or the reverse ``ManyToManyRel``), and no other shape.
    - ``"generic"`` - a ``contenttypes`` ``GenericRelation`` (the reverse
      side of a ``GenericForeignKey``), detected duck-typed by the presence
      of non-``None`` ``content_type_field_name`` and ``object_id_field_name``
      attributes. It is many-valued (``one_to_many=True``,
      ``auto_created=False``) and would otherwise land in ``"reverse_many_to_one"``
      below; the explicit kind lets the optimizer inject
      the constant content-type morph predicate and partition by the child
      ``object_id`` column instead of guessing a reverse join.
    - ``"reverse_many_to_one"`` - the reverse side of a ``ForeignKey``
      (Django's ``ManyToOneRel`` descriptor: ``one_to_many=True``; Django's
      one other ``one_to_many`` shape is the ``GenericRelation`` classified
      above). Cardinality-wise this collapses into
      the many-side for plan building today, but the descriptor itself
      is conceptually distinct from a forward M2M and is named so
      kind readers (``optimizer/field_meta.py::FieldMeta``) can
      disambiguate.
    - ``"reverse_one_to_one"`` - the reverse side of a
      ``OneToOneField`` (Django's ``OneToOneRel`` descriptor:
      ``one_to_one=True`` + ``auto_created=True`` + ``concrete=False``).
      ``concrete`` distinguishes it from Django's auto-created MTI parent
      link, which is a forward ``OneToOneField`` with the same other flags.
    - ``"forward_single"`` - every other forward single-row relation
      (``ForeignKey``, forward ``OneToOneField``, and the concrete
      auto-created MTI parent link).

    Examples:
        ``ManyToManyField``-like -> ``"many"``;
        ``GenericRelation``-like -> ``"generic"``;
        ``ManyToOneRel``-like -> ``"reverse_many_to_one"``;
        ``OneToOneRel``-like -> ``"reverse_one_to_one"``;
        ``ForeignKey``-like -> ``"forward_single"``;
        MTI ``<parent>_ptr``-like -> ``"forward_single"``.

    """
    many_to_many = relation_bool(field, "many_to_many")
    one_to_many = relation_bool(field, "one_to_many")
    one_to_one = relation_bool(field, "one_to_one")
    auto_created = relation_bool(field, "auto_created")
    concrete = relation_bool(field, "concrete")
    content_type_field_name = relation_name(field, "content_type_field_name")
    object_id_field_name = relation_name(field, "object_id_field_name")

    if many_to_many:
        return "many"
    # A ``GenericRelation`` (and a ``FieldMeta`` snapshot of one) is detected
    # duck-typed BEFORE the ``one_to_many`` arm below. The
    # ``getattr(..., None) is not None`` form (not ``hasattr``) is load-bearing:
    # ``FieldMeta`` is a slotted dataclass that ALWAYS carries the two slots, so
    # ``hasattr`` would misclassify every ``FieldMeta`` as ``"generic"`` - only a
    # genuine ``GenericRelation`` populates the slots with real field names.
    if content_type_field_name is not None and object_id_field_name is not None:
        return "generic"
    if one_to_many:
        return "reverse_many_to_one"
    if one_to_one and auto_created and not concrete:
        return "reverse_one_to_one"
    return "forward_single"


def is_many_side_relation_kind(kind: RelationKind | None) -> bool:
    """Return ``True`` for relation kinds represented as GraphQL lists."""
    return kind in MANY_SIDE_RELATION_KINDS


@dataclass(frozen=True)
class RelationPathHop:
    """One resolved relation segment of a classified model-field path.

    ``kind`` is ``relation_kind(field)`` - the semantic topology of the hop.
    ``many_side`` is the SQL-cardinality answer read from Django's
    ``PathInfo`` records (``any(pi.m2m for pi in field.path_infos)``): despite
    the name, ``PathInfo.m2m`` is ``True`` for an ordinary non-unique reverse
    FK too, so it, not ``kind``, decides whether the hop multiplies rows.
    ``target_model`` is ``field.path_infos[-1].to_opts.model`` - the model the
    walk continues from after one declared segment (which may expand to several
    ``PathInfo`` records, e.g. an M2M through table, collapsed at the segment
    boundary). No Django ``PathInfo`` object is retained on the frozen record.
    """

    segment: str
    kind: RelationKind
    target_model: type[models.Model]
    many_side: bool


@dataclass(frozen=True)
class ClassifiedPath:
    """The strict, immutable classification of one model-field path.

    ``hops`` are the ordered relation segments (empty for a local scalar).
    ``terminal`` is NEVER ``None``: for a path ending on a column it is that
    concrete Django field; for a relation-terminal path (e.g. ``genres`` used
    by an ``isnull`` relation filter) it is the terminal relation descriptor
    itself, which ALSO appears as the last hop. ``first_many_index`` is the
    index into ``hops`` of the first ``many_side`` hop, or ``None`` when the
    whole path is row-preserving. ``relation_chain`` is the tuple of relation
    (hop) segments - the path minus a scalar terminal - the safe subquery
    grouping key predicate generation consumes.
    """

    model: type[models.Model]
    path: str
    hops: tuple[RelationPathHop, ...]
    terminal: ModelField
    first_many_index: int | None
    relation_chain: tuple[str, ...]


def _resolve_segment_field(model: type[models.Model], segment: str) -> ModelField:
    """Return the field a path segment names, resolving ``pk`` to the pk field.

    ``pk`` is Django's ORM alias for the model's primary key; a ``pk`` segment
    anywhere in a path behaves like that pk field. Any other unresolvable
    segment surfaces as ``FieldDoesNotExist`` for the caller to convert into a
    typed ``PathResolutionError`` (this includes a hidden reverse relation
    declared ``related_name="+"``, whose reverse name ``get_field`` rejects). A
    ``model`` with no ``_meta`` (a ``Meta.model`` that is not a Django model)
    names no field either.
    """
    meta: Options[models.Model] | None = getattr(model, "_meta", None)
    if meta is None:
        raise FieldDoesNotExist(segment)
    if segment == "pk":
        return meta.pk
    return meta.get_field(segment)


def _is_traversable_relation(field: object) -> TypeGuard[_TraversableRelationLike]:
    """Return whether a resolved field is a relation the walk can follow.

    A traversable relation is one exposing usable ``path_infos``. A forward
    ``GenericForeignKey`` reports ``is_relation=True`` but defines NO
    ``path_infos`` - reading it before this guard would raise ``AttributeError``
    instead of the typed error, so ``path_infos`` is touched ONLY after this
    returns ``True``.
    """
    if not relation_bool(field, "is_relation"):
        return False
    return getattr(field, "path_infos", MISSING_ATTRIBUTE) is not MISSING_ATTRIBUTE


def classify_path(model: type[models.Model], field_path: str) -> ClassifiedPath:
    """Strictly classify an ORM ``field_path`` into an immutable relation plan.

    Splits on ``LOOKUP_SEP`` and walks each segment through
    ``Model._meta.get_field`` (with ``pk`` resolved to the pk field). A
    non-relation field is a valid terminal only as the LAST segment; anywhere
    earlier the path continues past an untraversable column and raises. A
    relation segment must expose non-empty ``path_infos``; its hop records
    ``relation_kind(field)`` as ``kind`` and ``any(pi.m2m ...)`` as
    ``many_side``, and the walk continues from ``path_infos[-1].to_opts.model``.
    A relation reached at the final segment is preserved as ``terminal`` AND as
    the last hop. Raises ``PathResolutionError`` (naming model, path, and
    segment) for a missing, non-traversable (forward ``GenericForeignKey``),
    empty-``path_infos``, or non-relation-mid-path segment.

    Kept uncached so callers may pass unhashable test doubles (a
    ``SimpleNamespace`` fake model pins the empty-``path_infos`` branch);
    ``_classify_path_cached`` layers a bounded ``lru_cache`` over it for the
    hot ``path_traverses_to_many`` path, keyed on the hashable,
    definition-time-stable ``(model, field_path)`` pair.

    Four other ``_meta`` path walkers share the split-and-``get_field``
    mechanism under different contracts and stay separate:
    ``optimizer/plans.py::_resolve_order_path_field`` answers the terminal
    concrete column or ``None`` for cursor anchoring;
    ``plans.py::_select_path_missing_connectors`` answers the connectors a
    ``select_related`` path still needs under a ``.only()`` projection, or
    ``None`` when the path does not resolve;
    ``utils/querysets.py::_prefetch_relation_target_or_none`` answers the
    terminal model or ``None`` (fail-open, with the default ``<model>_set``
    accessor spelling) for prefetch sealing;
    ``list_field.py::_resolve_order_field_path`` answers ``(field, related
    opts)`` or ``None`` for ordering-term certification. A caller needing
    another walker's answer, or this classifier gaining an accessor-name
    fallback or a non-raising mode, reopens the question.
    """
    if type(field_path) is not str:
        raise PathResolutionError(model, field_path, field_path) from None
    segments = field_path.split(LOOKUP_SEP)
    current = model
    hops: list[RelationPathHop] = []
    terminal: object = None
    last_index = len(segments) - 1
    for index, segment in enumerate(segments):
        try:
            field = _resolve_segment_field(current, segment)
        except FieldDoesNotExist:
            raise PathResolutionError(current, field_path, segment) from None
        try:
            is_relation = relation_bool(field, "is_relation")
        except ConfigurationError:
            raise PathResolutionError(current, field_path, segment) from None
        if is_relation:
            if not _is_traversable_relation(field):
                raise PathResolutionError(current, field_path, segment)
            path_infos = field.path_infos
            # The class is tested off a local so the check leaves ``path_infos`` typed as
            # the relation declares it rather than as a bare ``list`` / ``tuple``.
            infos_class = type(path_infos)
            if (infos_class is not list and infos_class is not tuple) or not path_infos:
                raise PathResolutionError(current, field_path, segment)
            target_model = path_infos[-1].to_opts.model
            many_side = any(relation_bool(path_info, "m2m") for path_info in path_infos)
            kind = relation_kind(field)
            hops.append(
                RelationPathHop(
                    segment=segment,
                    kind=kind,
                    target_model=target_model,
                    many_side=many_side,
                ),
            )
            current = target_model
            if index == last_index:
                terminal = field
        elif index == last_index:
            terminal = field
        else:
            raise PathResolutionError(current, field_path, segment)
    first_many_index = next(
        (i for i, hop in enumerate(hops) if hop.many_side),
        None,
    )
    return ClassifiedPath(
        model=model,
        path=field_path,
        hops=tuple(hops),
        # The final segment assigned its ``_resolve_segment_field`` result here or raised.
        terminal=cast("ModelField", terminal),
        first_many_index=first_many_index,
        relation_chain=tuple(hop.segment for hop in hops),
    )


def validate_lookup_expr(terminal: ModelField, lookup_expr: str) -> type[Lookup[object]]:
    """Validate a django-filter lookup expression against a classified terminal.

    A contract SEPARATE from path classification. ``terminal`` is a
    ``ClassifiedPath.terminal`` - a concrete Django field or a relation
    descriptor (forward relation field / ``ForeignObjectRel``). ``lookup_expr``
    is a ``LOOKUP_SEP``-joined chain of zero or more transforms followed by a
    final lookup (e.g. ``"icontains"``, ``"date__year__gte"``, ``"exact"``,
    ``"isnull"``).

    The walk advances an EXPRESSION cursor (the terminal's column, then
    successive transform instances). For each non-final part the cursor's
    ``get_transform`` must resolve a transform; the cursor advances to that
    transform bound to the previous cursor, so validation of the next part runs
    against the transform's own output field - NEVER re-validated against the
    original terminal. For the final part the cursor's ``get_lookup`` is tried
    first; if it returns ``None`` the part is treated as a TRAILING TRANSFORM
    with an implicit ``exact`` (Django's own ORM semantics: a lookup path
    ending on a transform compiles as ``transform + exact``), accepted only
    when the transform's output field supports ``exact``.

    A ``Field`` terminal (scalar or forward relation) starts the walk at its
    column, ``Field.cached_col``: the ``Col`` whose output field is the
    terminal itself, which is where Django's own ``Query.build_lookup`` starts.
    The column answers ``get_lookup`` / ``get_transform`` through that output
    field, and a transform that declares no ``output_field`` of its own
    (``Lower``, a ``JSONField`` key) resolves one from the column, so
    ``lower__icontains`` and ``a__b`` validate exactly as Django compiles them.
    A reverse ``ForeignObjectRel`` has no column; it starts the walk as itself,
    answering ``get_lookup`` / ``get_transform`` through its forward field
    (``RelatedIsNull`` / ``RelatedExact`` / ``RelatedIn``).

    Returns the resolved final lookup CLASS (the trailing-transform case
    returns the ``exact`` lookup class) - cheap and useful to callers.

    Raises ``LookupValidationError`` (naming the terminal, the full
    ``lookup_expr``, and the offending part) for an empty expression, an empty
    part, an unresolvable mid-chain transform, or a final part that is neither
    a lookup nor a trailing transform with a supported ``exact``.
    """
    if type(lookup_expr) is not str:
        raise LookupValidationError(terminal, lookup_expr, lookup_expr) from None
    if not lookup_expr:
        raise LookupValidationError(terminal, lookup_expr, lookup_expr)
    parts = lookup_expr.split(LOOKUP_SEP)
    for part in parts:
        if not part:
            raise LookupValidationError(terminal, lookup_expr, part)
    cursor: Col | Transform | models.ForeignObjectRel = (
        terminal.cached_col if truth.is_instance(terminal, Field) else terminal
    )
    # ``str.split`` always yields at least one part, so the final part always exists.
    *transform_parts, final_part = parts
    for part in transform_parts:
        transform = cursor.get_transform(part)
        if transform is None:
            raise LookupValidationError(terminal, lookup_expr, part)
        cursor = transform(cursor)
    lookup = cursor.get_lookup(final_part)
    if lookup is not None:
        return lookup
    transform = cursor.get_transform(final_part)
    if transform is not None:
        exact = transform(cursor).get_lookup("exact")
        if exact is not None:
            return exact
    raise LookupValidationError(terminal, lookup_expr, final_part)


def _lenient_traverses_to_many(model: type[models.Model], field_path: str) -> bool:
    """Legacy lenient to-many walk, retained verbatim as a fail-open fallback.

    Walks the ``__``-separated path swallowing any resolution failure into a
    ``False`` answer, returning ``True`` the instant a many-side relation is
    reached - even if garbage follows it. ``path_traverses_to_many`` runs this
    ONLY when strict ``classify_path`` raises ``PathResolutionError``, which
    preserves the pre-refactor answer on every path the classifier REJECTS: a
    many-then-garbage path (e.g. ``genres__nonexistent``) still answers
    ``True`` here, whereas plain ``False`` on the raise would have regressed it.
    On paths the classifier RESOLVES the answer comes from ``PathInfo.m2m``
    instead; see ``path_traverses_to_many`` for the one deliberate divergence
    from this lenient walk's cardinality rule.
    """
    if type(field_path) is not str:
        return False
    segments = field_path.split(LOOKUP_SEP)
    current = model
    for segment in segments:
        try:
            field = _resolve_segment_field(current, segment)
        except FieldDoesNotExist:
            return False
        if not relation_bool(field, "is_relation"):
            return False
        if is_many_side_relation_kind(relation_kind(field)):
            return True
        # ``Field.related_model`` checks the app registry is ready, so it is a resolved
        # model class or ``None`` (``GenericForeignKey`` declares ``None``).
        related: type[models.Model] | None = getattr(field, "related_model", None)
        if related is None:
            return False
        current = related
    return False


@lru_cache(maxsize=2048)
def _classify_path_cached(model: type[models.Model], field_path: str) -> ClassifiedPath:
    """Bounded ``lru_cache`` over ``classify_path`` for the hot to-many probe.

    ``path_traverses_to_many`` is called repeatedly with the same
    definition-time ``(model, field_path)`` pairs during filter/order
    generation; caching the frozen ``ClassifiedPath`` here avoids re-walking
    model metadata without forcing a cache onto the public, uncached
    ``classify_path`` (which must accept unhashable test doubles).
    """
    return classify_path(model, field_path)


def leading_relation_hops(
    model: type[models.Model],
    field_path: str,
) -> tuple[RelationPathHop, ...]:
    """Return ``classify_path``'s hops for the longest leading part of ``field_path`` it classifies.

    The relation segments a path crosses before whatever follows them: a column,
    a transform or key path past it (``created__year``, ``data__key``), or a
    segment that resolves to nothing. Each hop's ``target_model`` is the model
    Django's join reaches, and the hops cover ``field_path``'s first
    ``len(hops)`` segments. Empty when even the first segment does not classify
    as a relation.
    """
    segments = field_path.split(LOOKUP_SEP)
    for end in range(len(segments), 0, -1):
        hops = _classified_hops(model, LOOKUP_SEP.join(segments[:end]))
        if hops is not None:
            return hops
    return ()


def _classified_hops(
    model: type[models.Model],
    field_path: str,
) -> tuple[RelationPathHop, ...] | None:
    """Return the cached classification's hops for ``field_path``, ``None`` when it does not classify."""
    try:
        return _classify_path_cached(model, field_path).hops
    except PathResolutionError:
        return None


def _traverses_to_many(
    classify: Callable[[type[models.Model], str], ClassifiedPath],
    model: type[models.Model],
    field_path: str,
) -> bool:
    """Answer the to-many question over ``classify``, with the shared fallback ladder.

    ONE body for both arms of :func:`path_traverses_to_many`: the hashable arm
    passes the cached classifier, the unhashable arm passes the uncached one.
    The ladder itself - strict answer, lenient walk on ``PathResolutionError`` -
    is the contract a 32-path matrix pins, and it must not be able to differ
    between the two arms.
    """
    try:
        return classify(model, field_path).first_many_index is not None
    except PathResolutionError:
        return _lenient_traverses_to_many(model, field_path)


@lru_cache(maxsize=2048)
def _path_traverses_to_many_cached(model: type[models.Model], field_path: str) -> bool:
    """Compute ``_traverses_to_many`` for hashable definition-time model/path pairs (cached)."""
    return _traverses_to_many(_classify_path_cached, model, field_path)


def path_traverses_to_many(model: type[models.Model], field_path: str) -> bool:
    """Return whether an ORM ``field_path`` traverses a to-many relation.

    Built on ``classify_path``: the strict classifier is the single
    site of the relation taxonomy, and this helper answers
    ``classify_path(...).first_many_index is not None``. When strict
    classification raises ``PathResolutionError`` (an unresolvable head, a
    garbage tail, a forward ``GenericForeignKey``) it falls back to the
    lenient walk (``_lenient_traverses_to_many``) rather than a bare ``False``.

    That fallback keeps the resolvable-vs-unresolvable boundary faithful: the
    lenient walk returns ``True`` the instant it reaches a many-side hop and never
    sees a garbage tail beyond it, while ``classify_path`` raises on that tail. A
    32-path matrix (``tests/utils/test_relations.py``) pins the
    fallback's answers on the raise paths, including
    ``genres__nonexistent`` -> ``True`` and ``genres__name__icontains`` ->
    ``True`` (many-then-garbage), where a plain ``False`` would diverge.

    One DELIBERATE divergence from ``relation_kind`` holds on the RESOLVED path:
    ``relation_kind`` reads every ``ManyToOneRel`` as ``reverse_many_to_one``
    (many-side), whereas the strict classifier reads ``PathInfo.m2m``
    (``not field.unique``). The reverse side of a ``ForeignKey(unique=True)`` is
    therefore reported single-valued here (-> ``False``) where a
    ``relation_kind``-based walk would answer ``True``. That is the correct
    answer: a unique reverse FK is genuinely single-valued, so it neither fans
    out nor needs the ``distinct`` stamp / order aggregate a ``True`` would trigger.

    Filter generation uses the result to set ``distinct=True`` on plain
    generated leaf filters; order resolution uses it to replace a fan-out
    ``order_by`` with a row-preserving aggregate. The answer depends only on
    model metadata, so the bounded process-lifetime cache safely serves both
    subsystems.
    """
    try:
        _ = hash((model, field_path))
    except TypeError:
        # An unhashable test double cannot key the cache; answer uncached.
        return _traverses_to_many(classify_path, model, field_path)
    return _path_traverses_to_many_cached(model, field_path)


def _path_traverses_to_many_cache_clear() -> None:
    """Invalidate every cache ``path_traverses_to_many`` reads.

    The probe layers a bounded classifier cache beneath its own answer cache;
    a clear that emptied only the outer layer would leave a metadata change
    under a warm ``(model, field_path)`` key answering from the stale frozen
    classification even after the clear was called.
    """
    _classify_path_cached.cache_clear()
    _path_traverses_to_many_cached.cache_clear()


@overload
def is_forward_many_to_many(field: ModelField) -> TypeGuard[ConcreteField]: ...
@overload
def is_forward_many_to_many(field: object) -> bool: ...
def is_forward_many_to_many(field: object) -> bool:
    """Return ``True`` for a forward, writable ``ManyToManyField``.

    ``relation_kind`` maps BOTH a forward ``ManyToManyField`` and an
    auto-created reverse M2M accessor (``ManyToManyRel``) to ``"many"`` -
    cardinality-wise they are identical, so the classifier cannot tell them
    apart. The mutation surfaces need the finer distinction: only a forward,
    writable M2M is an editable column a write can set / index. A forward
    ``ManyToManyField`` is ``concrete`` (equivalently, not ``auto_created``);
    the reverse accessor is ``auto_created`` and not ``concrete``.

    Single-sited here so the predicate cannot drift across the write
    surfaces that select editable / attestable M2M fields. Each flag is read
    through ``relation_bool``, ``relation_kind``'s read contract: an absent or
    ``None`` flag reads as ``False`` and a non-``bool`` one raises. Over a model field, ``True`` narrows it to
    the forward ``ManyToManyField`` (a concrete ``Field``, never a reverse rel).
    """
    many_to_many = relation_bool(field, "many_to_many")
    concrete = relation_bool(field, "concrete")
    auto_created = relation_bool(field, "auto_created")
    return many_to_many and (concrete or not auto_created)


def is_forward_single_relation(field: object) -> bool:
    """Return whether ``field`` is a forward relation to one row, whatever its shape.

    A ``ForeignKey`` / ``OneToOneField`` (the MTI parent link included), a
    ``ForeignObject`` of any width and a ``GenericForeignKey``. ``relation_kind``
    reads ``"forward_single"`` for every field that is neither many-valued nor a
    reverse one-to-one, so the answer needs more than the kind: ``is_relation``
    (a plain column is ``"forward_single"`` too) and no ``ForeignObjectRel`` (the
    reverse ``GenericRel`` a ``GenericRelation(related_query_name=...)`` makes
    visible on the generic-key model reports ``many_to_one`` and no cardinality
    flag ``relation_kind`` reads, so it classifies ``"forward_single"``).
    """
    return (
        relation_bool(field, "is_relation")
        and not isinstance(field, ForeignObjectRel)
        and relation_kind(field) == "forward_single"
    )


@overload
def is_forward_concrete_relation(field: ModelField) -> TypeGuard[ConcreteField]: ...
@overload
def is_forward_concrete_relation(field: _RelationFieldLike) -> bool: ...
def is_forward_concrete_relation(field: object) -> bool:
    """Return whether ``field`` is a forward FK / OneToOne with a real DB column.

    The predicate is exactly "``is_forward_single_relation``, and backed by a
    real local column": cardinality is decided by ``relation_kind`` - this
    module's single site of the relation taxonomy - through that owner. Cardinality
    deliberately does NOT come from ``column`` / ``concrete``: Django moves BOTH
    flags for ``ManyToManyField`` inside the supported range. On the 5.2 support
    floor a forward M2M reports ``column="genres"`` and ``concrete=True``
    (``Field.set_attributes_from_name`` fills the attname in even though no such
    column exists on the source table - the pairing lives in the through table);
    6.0+ reports ``column=None`` and ``concrete=False``. A ``column``-only test
    therefore called a forward M2M a forward concrete relation on 5.2 and not on
    6.x - one predicate answering two ways across one supported matrix. The
    cardinality flags ``relation_kind`` reads (``many_to_many`` / ``one_to_many`` /
    ``one_to_one`` / ``auto_created``) are stable across that range, so routing
    the cardinality question through it makes the answer version-independent.

    The M2M exclusion belongs HERE rather than at the callers, so every caller
    inherits the whole contract: ``forms/inputs.py::_model_column_for`` and
    ``mutations/inputs.py::_relation_field_index`` answer a forward M2M through
    ``is_forward_many_to_many`` and every other relation through this predicate,
    with no cardinality-flag read of their own.

    The ``column`` / ``related_model`` reads stay load-bearing AFTER the kind
    gate, because a forward ``GenericForeignKey`` also classifies
    ``"forward_single"``: it carries ``ct_field`` / ``fk_field``, not the
    ``content_type_field_name`` / ``object_id_field_name`` slots that mark a
    ``GenericRelation``, so the ``"generic"`` arm never claims it. It is virtual
    all the same (``column=None``, ``related_model=None``), and excluding it
    keeps a scalar or extra form field that merely shares a name with a virtual
    or reverse relation from being misclassified by the FK index or by ModelForm
    backing-column resolution.

    Over a model field, ``True`` narrows it to the forward FK / OneToOne ``Field``.
    """
    if not is_forward_single_relation(field):
        return False
    return (
        getattr(field, "column", None) is not None
        and getattr(field, "related_model", None) is not None
    )


@dataclass(frozen=True)
class RelationLink:
    """A relation link's column pairs, as Django's ``ForeignObject`` declares them.

    ``carriers`` are the columns on the model that STORES the key (the link's
    ``local_related_fields``); ``targets`` are the columns they reference on the
    other model (``foreign_related_fields``), index-for-index. Which model each
    side lives on depends on the hop:

    - a forward ``ForeignKey`` / ``OneToOneField`` / ``ForeignObject``: carriers
      on the source row (``(<name>_id,)``, one per ``from_fields`` entry),
      targets on the related model (its pk, a ``to_field``, the ``to_fields``);
    - a reverse FK / reverse one-to-one / reverse ``ForeignObject``: the forward
      link read from the other side, so carriers on the child and targets on the
      source row;
    - a ``GenericRelation``: the child's ``object_id`` carrying the source pk;
    - an M2M hop in either direction: the through table's foreign key onto the
      SOURCE model (``m2m_through_link_fields``), so carriers on the through row
      and targets on the source row (the source pk, or a through FK's
      ``to_field``).

    Both tuples are empty for every shape that is not such a link (a
    ``GenericForeignKey``, a non-relation, an M2M whose through table does not
    resolve).
    """

    carriers: tuple[ConcreteField, ...] = ()
    targets: tuple[ConcreteField, ...] = ()

    @property
    def carrier_attnames(self) -> tuple[str, ...]:
        """The carrier columns' attnames, in link order."""
        return tuple(field.attname for field in self.carriers)

    @property
    def target_attnames(self) -> tuple[str, ...]:
        """The target columns' attnames, in link order."""
        return tuple(field.attname for field in self.targets)


def _link_field_tuple(value: object) -> tuple[ConcreteField, ...] | None:
    """Return ``value`` as a tuple of column fields, or ``None`` when it is not one."""
    if not is_list_or_tuple(value):
        return None
    fields = tuple(value)
    for field in fields:
        if type(getattr(field, "attname", None)) is not str:
            return None
    return cast("tuple[ConcreteField, ...]", fields)


def relation_link(field: object) -> RelationLink:
    """Return the column pairs of the link ``field`` is, or is the reverse of.

    The one reader of "which columns join this relation". A forward
    ``ForeignObject`` (``ForeignKey``, ``OneToOneField``, ``GenericRelation``
    included) answers from its own ``local_related_fields`` /
    ``foreign_related_fields``; an M2M hop (forward ``ManyToManyField`` or
    reverse ``ManyToManyRel``) answers from its through table's foreign key onto
    the source model; a reverse descriptor (``ManyToOneRel``, ``OneToOneRel``,
    ``ForeignObjectRel``) answers from its forward ``.field``.
    A relation's ``attname`` names its carrier column only for a ``ForeignKey``
    (``<name>_id``): a plain ``ForeignObject`` has ``attname == name``,
    ``column`` ``None``, and its columns exist only as these pairs, so a
    consumer deriving a column from ``attname`` reads a name no table carries.

    Shapes that carry no pairs, and malformed ones (unequal or empty sides, a
    member without a string ``attname``), answer the empty ``RelationLink``.
    """
    link = field
    carriers: object = getattr(field, "local_related_fields", None)
    if carriers is None and relation_bool(field, "many_to_many"):
        link, _target_side = m2m_through_link_fields(field)
        if link is None:
            return RelationLink()
        carriers = getattr(link, "local_related_fields", None)
    elif carriers is None:
        link = read_attr(field, "field", None)
        if link is None:
            return RelationLink()
        carriers = getattr(link, "local_related_fields", None)
    carrier_fields = _link_field_tuple(carriers)
    target_fields = _link_field_tuple(getattr(link, "foreign_related_fields", None))
    if not carrier_fields or target_fields is None or len(carrier_fields) != len(target_fields):
        return RelationLink()
    return RelationLink(carriers=carrier_fields, targets=target_fields)


def m2m_through_model(field: object) -> type[models.Model] | None:
    """Return the M2M join table: ``field.through`` (rel side) or ``remote_field.through``."""
    through: object = getattr(field, "through", None)
    if through is None:
        through = getattr(getattr(field, "remote_field", None), "through", None)
    # A relation's ``through`` slot holds the join-table model class.
    return cast("type[models.Model] | None", through)


def m2m_through_link_fields(
    field: object,
) -> tuple[ForeignKeyField | None, ForeignKeyField | None]:
    """Return the M2M through table's (source-side FK, target-side FK) for one M2M hop.

    Resolved from the forward ``ManyToManyField``'s own naming
    (``m2m_field_name`` / ``m2m_reverse_field_name``, which honor
    ``through_fields``), which stays correct for self-referential M2Ms where
    scanning through-model FKs by target would be ambiguous. ``field`` is either
    the forward field (the source owns it) or the ``ManyToManyRel`` (the source
    is the target; the sides swap). ``(None, None)`` when the through model or
    the naming API is missing.
    """
    # Either the relation's own forward field or ``field`` itself.
    forward_field: object = getattr(field, "field", None)
    if not forward_field:
        forward_field = field
    through = m2m_through_model(field)
    source_name: object = getattr(forward_field, "m2m_field_name", None)
    target_name: object = getattr(forward_field, "m2m_reverse_field_name", None)
    if through is None or not callable(source_name) or not callable(target_name):
        return None, None
    through_meta = through._meta
    # ``m2m_field_name`` / ``m2m_reverse_field_name`` name the through table's
    # two ``ForeignKey`` columns.
    source_fk = cast("ForeignKeyField", through_meta.get_field(cast("str", source_name())))
    target_fk = cast("ForeignKeyField", through_meta.get_field(cast("str", target_name())))
    if forward_field is field:
        return source_fk, target_fk
    return target_fk, source_fk


def is_single_column_foreign_key(field: object) -> TypeGuard[ForeignKeyField]:
    """Return whether ``field`` is a forward FK / OneToOne whose value is one column.

    ``isinstance(field, models.ForeignKey)`` is the forward-concrete test:
    ``OneToOneField`` subclasses ``ForeignKey`` (MTI ``<parent>_ptr`` parent
    links included), while reverse relations (``ForeignObjectRel``), M2M
    (join-table-backed), ``GenericForeignKey`` (virtual, polymorphic),
    ``GenericRelation`` (a ``ForeignObject`` but not a ``ForeignKey``), and plain
    ``ForeignObject`` relations of any width are all excluded by construction.
    The ``column`` check guards the single-column contract against a
    ``ForeignKey`` shape whose value is not one concrete column. Every consumer
    that joins, casts, or filters on ``.column`` / ``.attname`` /
    ``.target_field`` as ONE column (the visibility cascade's ``__in`` edge, the
    lateral and single-parent fetch link) gates on this predicate.
    """
    return isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None


@overload
def stored_value_column(field: ConcreteField) -> ConcreteField: ...
@overload
def stored_value_column(field: ModelField) -> ModelField: ...
def stored_value_column(field: ModelField) -> ModelField:
    """Return the column whose values ``field`` stores: itself, or the column a key references.

    A ``ForeignKey`` / ``OneToOneField`` holds the value of the column it references
    (``ForeignKey.target_field``: the related pk, or its ``to_field``), and that column
    may itself be a key: a one-to-one primary key, a multi-table-inheritance parent
    link (one link per inheritance level), a ``to_field`` naming another key. The walk
    follows each link to the first column that is not a key, the walk
    ``ForeignKey.get_col`` makes to pick a key's output field, so a value typed or
    range-checked against the result is held to the column that stores it. Every
    other field (a plain column, a composite primary key, a reverse relation) is
    returned as is.
    """
    while isinstance(field, models.ForeignKey):
        field = field.target_field
    return field


def carrier_backed_link(field: object) -> RelationLink | None:
    """Return the link of a forward relation whose value lives only in separate carrier columns.

    A forward ``ForeignObject`` that is not a ``ForeignKey`` stores nothing in a
    column of its own (``column`` is ``None``): its link is the pairs of
    carrier columns on this model and target columns on the related model that
    :func:`relation_link` reads. ``None`` for every other field, a
    ``ForeignKey`` / ``OneToOneField`` (one column of its own), a
    ``GenericRelation`` (many-valued), a ``GenericForeignKey`` (no link
    pairs) and every reverse descriptor (a ``ForeignObjectRel``, the reverse
    side of a ``GenericRelation`` included, whose link belongs to the field
    on the other model) included.
    """
    if not is_forward_single_relation(field) or is_single_column_foreign_key(field):
        return None
    link = relation_link(field)
    return link if link.carriers else None


def non_pk_forward_link(field: object) -> RelationLink | None:
    """Return the link of a forward relation keyed by columns other than the related pk.

    A ``ForeignKey`` with a ``to_field`` and a ``ForeignObject`` whose
    ``to_fields`` are not the related model's primary key: ``<relation>__pk``
    names a column the source row does not hold, so Django reaches it through
    a join, and a link whose carriers match no related row (no database
    constraint holds a ``ForeignObject``, nor a ``db_constraint=False`` key)
    drops the source row from an inner join. ``None`` for a relation keyed by
    the related pk (Django trims ``<relation>__pk`` to the carrier column, no
    join) and for every field that is not a forward single-valued relation.
    """
    if not is_forward_single_relation(field):
        return None
    link = relation_link(field)
    if not link.carriers:
        return None
    # A forward single-valued relation with link pairs names a resolved model.
    related = cast("type[models.Model]", getattr(field, "related_model", None))
    return None if link.targets == (related._meta.pk,) else link


def non_pk_relation_key_attname(field: object) -> str | None:
    """Return the related column a write through ``field`` stores, when it is not the related pk.

    A forward ``ForeignKey`` / ``OneToOneField`` stores the value of the column it
    references (``ForeignKey.target_field``: a ``to_field``), and a forward M2M's through
    row stores the value of the column its target-side foreign key references
    (:func:`m2m_through_link_fields`), which is also what ``.set()`` reads a non-instance
    member as. Both read through :func:`non_pk_forward_link`. ``None`` when that column
    is the related pk (the pk is then the stored key itself) and for every field that is
    neither shape.
    """
    if is_forward_many_to_many(field):
        _source_fk, field = m2m_through_link_fields(field)
    link = non_pk_forward_link(field)
    return None if link is None else link.target_attnames[0]


def order_column_paths(field_path: str, terminal: object) -> tuple[str, ...]:
    """Return the column paths an ordering term over ``field_path`` orders by, in order.

    A path ending on a carrier-backed forward relation (:func:`carrier_backed_link`)
    orders by each carrier column in link order, under the relations the path
    crosses: ``"fo"`` over ``from_fields=["tenant", "code"]`` is
    ``("tenant", "code")`` and ``"shelf__fo"`` is ``("shelf__tenant",
    "shelf__code")``. That is what Django's string ``order_by("fo")`` compiles
    to (``SQLCompiler.find_ordering_name``: one ``OrderBy`` per local column,
    no join, the related model's ``Meta.ordering`` never applied), and the
    only spelling an expression accepts: ``F("fo")`` reads one column, so
    ``Query.resolve_ref`` raises ``FieldError`` for a link of several. Every
    other path is returned unchanged: a ``ForeignKey`` / ``OneToOneField``
    leaf already names its own column. ``terminal`` is the field
    ``field_path`` ends on, the ``terminal`` of its :func:`classify_path`, which
    the caller has already classified.
    """
    link = carrier_backed_link(terminal)
    if link is None:
        return (field_path,)
    head, _sep, _tail = field_path.rpartition(LOOKUP_SEP)
    prefix = f"{head}{LOOKUP_SEP}" if head else ""
    return tuple(f"{prefix}{carrier.name}" for carrier in link.carriers)


def instance_accessor(field: object) -> str:
    """Return the attribute name relation rows are reached through on an instance.

    For a REVERSE relation declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related *query* name (``"book"`` - the
    filter/annotation vocabulary) while the instance attribute is
    ``get_accessor_name()`` (``"book_set"``); ``getattr(root, field.name)``
    raises ``AttributeError`` there, and Django's
    ``prefetch_related`` rejects the query name as a lookup for the same
    reason. They coincide whenever ``related_name`` is set, so only a
    relation declared without one exposes the split (fakeshop's
    ``RepairTicket.venue``, ``VenueBadge.venue``, ``VenueSponsor.venues``). Forward fields
    (``ForeignKey``, ``ManyToManyField``, ``OneToOneField``) have no
    ``get_accessor_name`` and their ``name`` IS the instance attribute.

    Three-tier read, matching the two field shapes the package passes
    around: an ``optimizer/field_meta.py::FieldMeta`` carries the accessor
    precomputed on its ``accessor_name`` slot (the builders derive it from
    the raw descriptor via this same helper); a raw Django reverse-relation
    descriptor answers ``get_accessor_name()``; everything else (forward
    fields, test doubles) falls back to ``name``.

    ``field.name`` stays the GraphQL-surface / optimizer-key vocabulary;
    this helper is ONLY for the seams Django resolves against the instance:
    the Phase-2 relation resolvers' ``getattr``, the spec-032 synthesized
    relation connections, and the optimizer's prefetch lookup paths.
    """
    precomputed = read_attr(field, "accessor_name", None)
    if precomputed is not None:
        if type(precomputed) is not str:
            raise ConfigurationError(
                f"Relation accessor metadata on {truth.kind(field)} must be a string; "
                f"got {truth.kind(precomputed)}.",
            )
        return precomputed
    get_accessor_name = read_attr(field, "get_accessor_name", None)
    if get_accessor_name is not None:
        if not callable(get_accessor_name):
            raise ConfigurationError(
                f"Relation accessor metadata on {truth.kind(field)} must be callable.",
            )
        accessor_name = get_accessor_name()
    else:
        accessor_name = read_attr(field, "name", MISSING_ATTRIBUTE)
    if type(accessor_name) is not str:
        raise ConfigurationError(
            f"Resolved relation accessor on {truth.kind(field)} must be a string; "
            f"got {truth.kind(accessor_name)}.",
        )
    return accessor_name


def has_composite_pk(model: type[models.Model]) -> bool:
    """Return whether ``model`` declares a Django 5.2+ composite primary key.

    Reads Django's own ``Options.is_composite_pk`` property, which checks the
    live ``_meta.pk`` on every call (``Options.pk_fields`` is a cached
    property and would keep reporting a pk shape that has since been
    rebound). Two consumers share this one detection:

    - The FK-id-elision eligibility test (a forward single relation
      satisfying an id-only child selection from the source row's local FK
      column) must fail closed for a composite primary key: the source-row
      ``attname`` carries a single-column id, but the target's ``pk`` is a
      tuple, so eliding would compare the wrong shapes and surface wrong
      data. ``FieldMeta.from_django_field`` stamps ``fk_id_elision_eligible``
      through it the same way for registered types and the walker's
      unregistered fallback map.
    - ``django_strawberry_framework/types/relay.py::_check_composite_pk_for_relay_node``
      rejects a Relay-declared type over a composite-pk model.
    """
    return model._meta.is_composite_pk
