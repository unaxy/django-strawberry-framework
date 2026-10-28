"""Neutral write-value primitives shared by the model, form, and serializer flavors.

The flavor-neutral owner of the per-value write checks every write flavor
runs at decode time (promoted from ``mutations/resolvers.py`` so the model
mutation resolver is not the utility module for the other write flavors):

- ``unstorable_text_error`` - the text storability preflight (lone surrogate, NUL);
- ``unstorable_temporal_error`` - the temporal storability preflight (a date, datetime,
  time or duration the write alias cannot store, or cannot read back);
- ``raw_choice_value`` - choice-enum member unwrapping;
- ``coerce_relation_pk_or_none`` - raw relation-pk coercion;
- ``relation_takes_global_id`` - whether a relation's id is a Relay GlobalID;
- ``type_check_relation_id`` - the structural relation-id check;
- ``decode_scalar_leaf`` - the shared text-preflight + choice-unwrap compose;
- ``decode_visible_relation`` - the visibility-on-every-branch single-relation
  decode spine (type-check -> visible object -> flavor projection);
- ``decode_visible_relation_ids`` - the batched id-set compose (type-check each
  id, batched NodeID mapping, then one visibility / existence ``pk__in`` query
  answering the stored keys);
- ``store_decoded`` / ``decoded_into`` / ``scalar_into`` / ``file_into`` /
  ``relation_into`` / ``decode_field_handlers`` - the SCALAR / RELATION / FILE
  store-into-dest vocabulary the write-flavor walks share;
- ``decode_provided_fields`` - the kind-routed walk over a bound write input;
- ``unstorable_columns`` - the save-time diagnosis of an attempted row: the
  declared columns holding a value the column cannot store (``None`` on a
  ``null=False`` column), read from the in-memory instance after a failed save.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from typing import TYPE_CHECKING

from django.db.models.fields import Field
from strawberry import relay

from django_strawberry_framework.registry import registry

from . import truth
from ._narrowing import (
    enum_value,
    is_list,
    is_text_atom,
    list_of,
    read_attr,
)
from .errors import (
    FIELD_ERROR_CODE_INVALID,
    UNBINDABLE_TEMPORAL_MESSAGE,
    field_error,
    join_error_path,
    relation_field_error,
    unstorable_temporal,
    unstorable_text,
)
from .inputs import FILE, RELATION_MULTI, RELATION_SINGLE, iter_provided_input_fields
from .lazy import unwrap_lazy_object
from .querysets import (
    coerce_field_value_or_none,
    identity_key,
    lookup_read_alias,
    pks_all_present,
    visible_related_object,
    visible_related_objects,
)
from .typing import strawberry_schema_from_info

if TYPE_CHECKING:
    from collections.abc import Callable, Container
    from typing import TypeAlias

    from django.db import models
    from strawberry import Info

    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.types.relay import _RelayDjangoType
    from django_strawberry_framework.utils.errors import FieldError

    from .inputs import InputFieldSpec
    from .typing import ModelField

    #: One kind handler: decode ``(spec, value)``, store it, and report a ``FieldError``.
    _FieldHandler: TypeAlias = Callable[[InputFieldSpec, object], FieldError | None]
    #: One flavor relation decoder, called with the shared keyword arguments.
    _RelationDecoder: TypeAlias = Callable[..., tuple[object, FieldError | None]]
    #: Any model field, its set and get types unread.
    _FieldAny: TypeAlias = Field[object, object]
else:
    # ``Field`` has no ``__class_getitem__`` at runtime: the hint stays the class.
    _FieldAny = Field


def unstorable_text_error(field_name: str, value: object) -> FieldError | None:
    """Reject an input value holding text the package refuses to store (lone surrogate, NUL).

    The write decode's envelope for the shared refusal rule
    (``utils/errors.py::unstorable_text``, which walks every text leaf of the value,
    JSON keys and values included): a lone surrogate answers the ``invalid`` "Text
    contains invalid Unicode" error, an embedded NUL Django's own
    ``ProhibitNullCharactersValidator`` error, keyed to the first refused leaf's
    dotted path under ``field_name`` (``tags.1``, ``attributes.color``,
    ``rows.0.name``), the same indexed grammar a nested serializer error uses.

    Either would otherwise reach a DB-bound operation - ``validate_unique()``'s lookup
    query (a unique column) or ``save()``'s INSERT (a text, array-of-text, ``jsonb`` or
    ``hstore`` column, or a consumer write of the decoded value) - and the backend's
    error (a lone surrogate's ``UnicodeEncodeError``, PostgreSQL's NUL ``DataError``) is
    neither the ``ValidationError`` ``full_clean`` raises nor the ``IntegrityError``
    ``save`` raises, so it escapes as a top-level GraphQL error with ``data: null``
    instead of the field-keyed envelope. Reject it HERE, at decode, before any DB-bound
    work, as a ``FieldError`` (the same in-band envelope every other input failure
    returns); a model-flavor write so answers what a ``ModelForm`` or serializer one
    already does. A ``JSON`` value is held to the same rule as a top-level string
    rather than trusted to its column: whether a JSON column stores an escaped lone
    surrogate or NUL depends on the backend and on the field's encoder, so the decode
    refuses both on every backend. A relation id's coerced pk meets this check too
    (``type_check_relation_id``), since a text-keyed target binds it into the existence
    query; a NUL-bearing text id never reaches it, because the id coercion
    (``querysets.py::coerce_field_value_or_none``) already answers it as naming no row.
    """
    refusal = unstorable_text(field_name, value)
    if refusal is None:
        return None
    return field_error(refusal.path, refusal.message, codes=refusal.code)


def unstorable_temporal_error(
    field_name: str,
    column: object,
    value: object,
    using: Callable[[], str],
) -> FieldError | None:
    """Reject a temporal or duration value the write alias ``using()`` cannot store in ``column``.

    The write decode's envelope for the shared rule
    (``utils/errors.py::unstorable_temporal``): a value Django's own save-time preparation
    on that connection refuses (an aware datetime whose projection onto the connection's
    time zone leaves years 1..9999, or whose date in the default time zone does in a
    ``DateField``, an aware time, any aware datetime under ``USE_TZ = False``) or binds
    as an integer the backend cannot hold (a duration past 64 bits of microseconds on
    SQLite or MySQL) would raise its
    ``OverflowError`` / ``ValueError`` at ``save()``, and an aware datetime PostgreSQL
    stores but cannot load back would raise at the post-write re-fetch; neither is an
    error the save mappers own, so it would escape as a masked top-level error. It is the
    ``invalid`` ``FieldError`` keyed to ``field_name`` instead, carrying the message a
    filter answers for the same value (``UNBINDABLE_TEMPORAL_MESSAGE``), before any
    database-bound work. ``value`` is what the write stores (the model flavor's value
    after the naive-datetime coercion), and a column that is neither temporal nor a
    duration answers ``None`` without resolving the alias.
    """
    if not unstorable_temporal(column, value, using):
        return None
    return field_error(field_name, UNBINDABLE_TEMPORAL_MESSAGE, codes=FIELD_ERROR_CODE_INVALID)


def raw_choice_value(value: object) -> object:
    """Unwrap a choice-enum member to its raw Django choice value (spec-036 Decision 6).

    A ``choices`` column resolves to the SAME generated Strawberry ``Enum`` on the
    read ``DjangoType`` and the write input (the symmetric wire contract), so the
    client's enum value arrives here as the ENUM MEMBER (e.g.
    ``BookCirculationStatusEnum.available``), not the raw string. The member's
    ``.value`` IS the Django choice value (``convert_choices_to_enum`` maps each
    member to its choice value), so setting the member directly onto the model
    would make ``full_clean()`` reject a perfectly valid choice (the member is not
    ``== "available"``). Unwrapping to ``.value`` feeds Django the raw choice value
    it stores and validates against. A non-enum scalar is passed through unchanged;
    an explicit ``None`` (a provided null) stays ``None``.

    A list value is unwrapped element-wise: every list-of-choices input (a
    ``MultipleChoiceField`` / ``ListField(child=ChoiceField)`` serializer field, an
    ``ArrayField`` whose ``base_field`` declares choices) publishes ``list[<enum>]``, so
    its elements arrive as members the same way. Unwrapping them here, rather than
    trusting each validator to accept a member, keeps the ``BLANK`` member honest:
    DRF's ``ChoiceField.to_internal_value`` tests ``data == ""`` for ``allow_blank``
    BEFORE it unwraps an ``Enum``, so a ``BLANK`` member reaching it is refused as an
    invalid choice while the unwrapped ``""`` is admitted. One level only: a scalar list
    input is a flat list of members, and the only deeper list (a ``JSON`` value, which is
    client-controlled nesting) never carries a member. The list is rebuilt, never mutated
    in place.
    """
    if is_list(value):
        return [_raw_choice_scalar(element) for element in value]
    return _raw_choice_scalar(value)


def _raw_choice_scalar(value: object) -> object:
    """Unwrap one non-list value: an enum member to its value, a ``str`` to the base ``str``."""
    raw_value = enum_value(value) if isinstance(value, Enum) else value
    return str.__str__(raw_value) if isinstance(raw_value, str) else raw_value


def coerce_relation_pk_or_none(related_model: type[models.Model], pk: object) -> object:
    """Coerce a raw M2M pk through the target's pk field; ``None`` if uncoercible / out of range.

    The raw-pk M2M counterpart to ``relay.py::_coerce_pk_or_none`` (which coerces a
    ``GlobalID`` ``node_id`` through the resolved Strawberry type's id field). A raw-pk
    relation has no Relay-Node type and so no ``resolve_id_attr`` seam: the existence
    query filters on ``pk__in`` directly, so coercion is against
    ``related_model._meta.pk`` via the shared
    ``querysets.py::coerce_field_value_or_none`` primitive - the same mechanics the
    GlobalID path uses: ``to_python``, then the bind on the database the existence query
    reads (``querysets.py::lookup_read_alias``) and the storage domain of the column
    storing it (a key-valued pk included), so an out-of-range pk (beyond the backend's
    signed-64-bit column range) is answered here rather than reaching ``pk__in`` and
    raising a raw backend ``OverflowError`` (``Python int too large to convert to SQLite
    INTEGER``). The pk field's own validators are not run, so a pk they would refuse
    still names a row that holds it. An uncoercible / out-of-range pk is treated as
    "identifies no row" - excluded from the existence query and so absent from the
    visible set, which makes it the same not-found ``relation_field_error`` as a
    genuinely missing pk, never a backend crash.
    """
    meta = truth.static_attr(related_model, "_meta")
    if meta is None:
        return None
    pk_field = getattr(meta, "pk", None)
    return coerce_field_value_or_none(pk_field, pk, alias=lookup_read_alias(related_model))


def relation_takes_global_id(related_primary_type: type[DjangoType] | None) -> bool:
    """Return whether a write-input relation to a target with this primary takes a GlobalID.

    The one Relay-vs-raw-pk rule for a relation id, read at both ends of a write: the
    schema side types the input from it (``mutations/inputs.py::relation_id_scalar``:
    ``ID`` when it holds, the target pk column's scalar otherwise), and the decode side
    picks the id's interpretation from it, never from the value
    (``type_check_relation_id`` and ``decode_visible_relation_ids``, passing
    ``registry.get`` of the target model - the lookup every flavor's bind types the input
    from). It holds when the target model's primary ``DjangoType`` is Relay-Node-shaped,
    the subclass test ``types/relay.py::implements_relay_node`` applies (read here off
    ``strawberry.relay.Node`` directly, so ``utils`` imports no ``types`` module); a
    target with no registered primary, or a non-Relay one, takes its raw pk.
    """
    return related_primary_type is not None and truth.is_subclass(
        related_primary_type,
        relay.Node,
    )


def type_check_relation_id(
    value: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    info: object = None,
    index: int | None = None,
) -> tuple[object, FieldError | None]:
    """Type-check + coerce ONE relation id to a pk.

    The "Relay target -> ``decode_model_global_id`` (non-``OK`` -> uniform relation
    error) | raw-pk target -> ``coerce_relation_pk_or_none`` (``None`` -> uniform
    relation error)" two-branch structural check the three write flavors share. Promoted here
    (from the serializer's cleanly-factored ``_type_check_relation_id``) so the
    single definition of "what counts as a well-formed relation id" is shared: the
    serializer single decoder and the form single decoder call it (the form keeping
    only its ``empty_values`` pass-through + ``to_field_name`` reduction on
    top), and the batched set decoder calls it per raw-pk element. The raw-pk
    branch touches no DB; the GlobalID branch resolves a non-pk NodeID value to
    its real pk with a query (batched per set by ``decode_visible_relation_ids``)
    - visibility is confirmed separately by the caller in both branches.

    The branch is the TARGET's, never the value's: ``relation_takes_global_id`` over the
    target model's registered primary (``registry.get``), the rule the input's id type was
    generated from.
    For a Relay target the value is the raw ``ID`` string the input carries, decoded
    against the target model under the schema executing ``info``
    (``strawberry_schema_from_info``), whose published type names a ``type``-strategy
    slot carries; every non-``OK`` status - a malformed string (bad base64, no
    ``type:id`` separator), an unresolvable or wrong-model type, an uncoercible node id
    - is the uniform ``relation_field_error``. For a raw-pk target the value is
    coerced through the target pk field (``None`` -> the uniform error) and ``info`` is
    never read.

    The coerced pk is then held to the text storability preflight
    (``unstorable_text_error``) before any caller binds it into an existence query: a
    lone surrogate in the id of a text-keyed target coerces cleanly through the
    target's text pk field, and the query would raise a raw backend
    ``UnicodeEncodeError``. It is the same field-keyed ``invalid`` error a scalar text
    leaf gets, keyed to ``graphql_name`` (``editionId``), or to the element's
    ``graphql_name.<index>`` path (``boundWith.1``) when ``index`` names its position
    in a relation-id list. A pk coerced to a non-text value (an int, a UUID) passes
    through it unchanged. An embedded NUL never reaches it: the coercion
    (``querysets.py::coerce_field_value_or_none``) answers a NUL-bearing text id as
    naming no row, so it is the uniform relation error, raw pk and GlobalID alike.

    The ``decode_model_global_id`` / ``GlobalIDDecode`` import is function-local:
    the package's ``relay`` module imports ``utils.querysets`` at module level, so
    a module-level import here would risk an import cycle through the utils
    package.
    """
    if relation_takes_global_id(registry.get(related_model)):
        from django_strawberry_framework.relay import GlobalIDDecode, decode_model_global_id  # noqa: PLC0415 - import cycle

        result = decode_model_global_id(
            value,
            related_model,
            schema=strawberry_schema_from_info(info),
        )
        if result.status is not GlobalIDDecode.OK:
            return None, relation_field_error(graphql_name)
        pk = result.pk
    else:
        pk = coerce_relation_pk_or_none(related_model, value)
        if pk is None:
            return None, relation_field_error(graphql_name)
    text_error = unstorable_text_error(_relation_id_error_path(graphql_name, index), pk)
    if text_error is not None:
        return None, text_error
    return pk, None


def _relation_id_error_path(graphql_name: str, index: int | None) -> str:
    """Key a relation id's error to ``graphql_name``, or to its ``graphql_name.<index>`` element."""
    return graphql_name if index is None else join_error_path(graphql_name, str(index))


def decode_scalar_leaf(graphql_name: str, value: object) -> tuple[object, FieldError | None]:
    """Run the shared scalar leaf decode: choice unwrap, then text preflight.

    The two-step compose every write flavor runs on a provided scalar value -
    ``raw_choice_value`` (a choice-enum member unwrapped to the raw Django choice
    value) then ``unstorable_text_error`` (a lone surrogate or an embedded NUL anywhere
    in the value - a list element, a ``JSON`` key or value - is a ``FieldError`` keyed
    to its path at decode, never a raw backend ``UnicodeEncodeError`` / ``DataError``
    at ``save()``). Unwrapping MUST happen first because an enum member is not itself
    a string while its storage value can be one; a preflight over the member would
    miss an unstorable choice value. This owns the compose so a fourth flavor cannot
    mis-order it. Returns ``(decoded, None)`` on success or ``(None, FieldError)``.
    Flavor-specific scalar steps (the model path's explicit-null rejection and
    naive-datetime coercion) stay at the call site, composed around this leaf, and so
    does the temporal storability check (``unstorable_temporal_error``): it reads the
    value each flavor stores, which on the form and serializer flavors exists only once
    their own validation has cleaned it.
    """
    decoded = raw_choice_value(value)
    error = unstorable_text_error(graphql_name, decoded)
    if error is not None:
        return None, error
    return decoded, None


def decode_visible_relation(
    value: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    info: Info[object, object],
    async_recourse: str,
    skip: Callable[[object], bool],
    project: Callable[[models.Model], object],
    key_attname: str | None,
    index: int | None = None,
) -> tuple[object, FieldError | None]:
    """Decode ONE relation id to its visible, flavor-projected value.

    The single-relation decode spine the form and serializer flavors share - and
    the owner of the **cross-flavor security invariant** that a writer must never
    attach a row it cannot see:

    (i) ``skip(value)`` short-circuits a clear / no-value (the form's
    ``empty_values``, the serializer's explicit ``None``) UNCHANGED, so the bound
    form / serializer's own validation decides required-ness; (ii) the structural
    type-check + pk coercion is ``type_check_relation_id`` (a non-``OK``
    ``GlobalID`` / an uncoercible raw pk is the uniform field-keyed
    ``FieldError``); (iii) the type-checked pk is resolved to the VISIBLE object
    via ``visible_related_object`` - a hidden / missing row is the SAME
    field-keyed ``FieldError`` (hidden and missing indistinguishable, no
    existence leak); (iv) ``project(obj)`` reduces the visible object to the
    flavor's bound-data value (the form's ``to_field_name`` key, the serializer's
    ``obj.pk``). ``index`` is the id's position when a caller maps this over a
    relation-id list; it keys the type-check's text error to that element.

    ``key_attname`` is the column the relation stores when it is not the related pk
    (``InputFieldSpec.key_attname``), required so no caller can leave it out: a visible
    row whose key is ``NULL`` names no row through it
    (``utils/querysets.py::linkable_rows``) and is the same relation error, whatever key
    the flavor binds.

    Returns ``(projected, None)`` on success or ``(None, FieldError)``. The
    form MULTI decoder maps this per element (it needs the object for
    ``to_field_name``). The model and serializer MULTI decoders share
    ``decode_visible_relation_ids`` (one ``pk__in`` visibility query) instead.
    """
    if skip(value):
        return value, None
    pk, error = type_check_relation_id(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
        info=info,
        index=index,
    )
    if error is not None:
        return None, error
    obj = visible_related_object(related_model, pk, info, async_recourse, key_attname)
    if obj is None:
        return None, relation_field_error(graphql_name)
    return project(obj), None


def materialize_relation_id_container(
    values: object,
    graphql_name: str,
) -> tuple[list[object], None] | tuple[None, FieldError]:
    """Materialize a relation-id container, or return the uniform field-keyed error.

    GraphQL normally supplies a list, but every write flavor's M2M seam can be
    reached with an arbitrary iterable, including a one-shot iterator. A
    non-iterable is an invalid relation VALUE, not a resolver exception, so it
    collapses to the same field-keyed ``relation_field_error`` envelope every
    other relation rejection uses; an iterable's own iteration is its
    behaviour, and whatever it raises propagates.

    Security-relevant, which is why it is one body rather than a copied one:
    the container is materialized BEFORE any member is decoded, so a
    partially-consumed iterator can never reach a visibility query, and a text,
    bytes-like or mapping atom is rejected outright rather than iterated into
    per-character or per-key "ids". A lazy translation ``Promise`` is a text atom
    too (``utils/_narrowing.py::is_text_atom``), whatever result class it wraps,
    so a ``lazy(..., list)`` value is refused with it. The atom check reads the
    real class of the object a ``SimpleLazyObject`` stands for, so a
    ``__class__`` claim neither hides an atom nor turns a container into one.

    Returns ``(provided_values, None)`` or ``(None, field_error)``.
    """
    unwrapped = unwrap_lazy_object(values)
    if is_text_atom(unwrapped) or issubclass(truth.class_of(unwrapped), Mapping):
        return None, relation_field_error(graphql_name)
    try:
        return list_of(values), None
    except TypeError:
        # ``list()``'s documented refusal of a non-iterable.
        return None, relation_field_error(graphql_name)


def decode_visible_relation_ids(
    values: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    info: Info[object, object],
    async_recourse: str,
    key_attname: str | None = None,
    project: Callable[[object, object], object] | None = None,
    single: bool = False,
) -> tuple[list[object], None] | tuple[None, FieldError]:
    """Type-check each relation id, then confirm the whole set in one visibility query.

    The batched compose the model FK / M2M set decoder and the serializer
    ``RELATION_MULTI`` decoder share:

    (i) every element is type-checked query-free first, by the target's id kind
    (``relation_takes_global_id``) - a raw pk through the target pk field, a Relay
    target's ``ID`` string through the shared decode/coerce half (a malformed string, a
    non-``OK`` decode or an uncoercible literal is the uniform field-keyed
    ``FieldError``, short-circuiting before any query) - then the decoded
    non-pk NodeID values are mapped to real pks in one ``__in`` query per
    distinct ``(type, id_attr)`` group (a value matching no row is the same
    uniform error, indistinguishable from missing); (ii) an empty set returns
    ``[]`` without touching the DB (a valid M2M clear); (iii)
    ``visible_related_objects`` confirms the whole set in ONE ``pk__in`` query
    through the related primary's ``get_queryset`` (or the default manager when
    no primary is registered); (iv) a hidden / missing member is the same
    ``relation_field_error`` (hidden and missing indistinguishable, no
    existence leak).

    The ids name rows by pk; the answer is the key a relation stores for each, read by
    the same query: the pk itself when ``key_attname`` is ``None``, or the
    ``key_attname`` column of a relation keyed by another column
    (``utils/relations.py::non_pk_relation_key_attname``), so a model write never
    stores a pk where the column holds a ``to_field`` value. A visible row whose key is
    ``NULL`` names no row through it (``utils/querysets.py::linkable_rows``) and is the
    same relation error. ``project(pk, key)`` replaces the answer for a flavor whose
    field resolves pks (the serializer's ``PrimaryKeyRelatedField``); the NULL-key
    refusal holds either way.

    Each element's type-check keys its text error to the element's index
    (``boundWith.1``); ``single`` marks ``values`` as one FK id the caller wrapped in a
    list, whose error keys to ``graphql_name`` alone.

    Flavor null policy stays at the caller: the model M2M path rejects a
    whole-list ``None``; the serializer passes it through so ``is_valid()``
    decides. Returns ``(keys, None)`` in input order on success or ``(None, FieldError)``.

    The ``relay`` imports are function-local for the same cycle dodge the
    ``type_check_relation_id`` docstring documents.
    """
    container = materialize_relation_id_container(values, graphql_name)
    if container[1] is not None:
        return None, container[1]

    from django_strawberry_framework.relay import (  # noqa: PLC0415 - import cycle
        GlobalIDDecode,
        _decode_and_coerce,
        _resolve_real_pks_batched,
    )

    members = container[0]
    takes_global_id = relation_takes_global_id(registry.get(related_model))
    slots: dict[type[_RelayDjangoType], tuple[str, ModelField | None]] = {}
    pks: list[object] = [None] * len(members)
    pending: list[tuple[int, type[_RelayDjangoType], object]] = []
    for position, value in enumerate(members):
        index = None if single else position
        if takes_global_id:
            # Only a Relay target reads ``info`` (for the executing schema); raw pks never do.
            intermediate = _decode_and_coerce(
                value,
                related_model,
                slots=slots,
                schema=strawberry_schema_from_info(info),
            )
            if intermediate.status is not GlobalIDDecode.OK:
                return None, relation_field_error(graphql_name)
            # The coerced id is bound into the batched NodeID query below, so it meets the
            # same text preflight ``type_check_relation_id`` holds a raw pk to.
            text_error = unstorable_text_error(
                _relation_id_error_path(graphql_name, index),
                intermediate.pk,
            )
            if text_error is not None:
                return None, text_error
            pending.append((position, intermediate.resolved_type, intermediate.pk))
        else:
            pk, error = type_check_relation_id(
                value,
                graphql_name=graphql_name,
                related_model=related_model,
                info=info,
                index=index,
            )
            if error is not None:
                return None, error
            pks[position] = pk
    if pending:
        resolved = _resolve_real_pks_batched(
            [(resolved_type, coerced) for _, resolved_type, coerced in pending],
            slots,
        )
        for (position, _resolved_type, _coerced), real_pk in zip(pending, resolved, strict=True):
            if real_pk is None:
                return None, relation_field_error(graphql_name)
            pks[position] = real_pk
    if not pks:
        return [], None
    visible = visible_related_objects(related_model, pks, info, async_recourse, key_attname)
    pk_field = related_model._meta.pk
    if not pks_all_present(pk_field, pks, visible.keys()):
        return None, relation_field_error(graphql_name)
    keys = [visible[identity_key(pk_field, pk)] for pk in pks]
    if project is None:
        return keys, None
    return [project(pk, key) for pk, key in zip(pks, keys, strict=True)], None


def _spec_field_name(spec: InputFieldSpec) -> str:
    """Default GraphQL error-path: the spec's own wire name."""
    return spec.graphql_name


def _no_relation_extra(_spec: InputFieldSpec) -> Mapping[str, object]:
    """Default relation-decoder extras: none."""
    return {}


def store_decoded(
    dest: dict[str, object],
    spec: InputFieldSpec,
    pair: tuple[object, FieldError | None],
) -> FieldError | None:
    """Store a successful ``(decoded, error)`` pair under ``spec.target_name``.

    The leftover glue every form / serializer kind handler copied after a decode:
    a ``FieldError`` short-circuits the walk without writing the dest; otherwise
    the value lands under the flavor's bound-data key (form field name /
    serializer field name). FILE uses this with ``(upload, None)``; nested
    serializer decode uses it around ``_decode_nested``.
    """
    decoded, error = pair
    if error is not None:
        return error
    dest[spec.target_name] = decoded
    return None


def decoded_into(
    dest: dict[str, object],
    decode: Callable[[InputFieldSpec, object], tuple[object, FieldError | None]],
) -> _FieldHandler:
    """Build a kind handler: ``decode(spec, value)`` then ``store_decoded``.

    The primitive SCALAR / FILE / RELATION / nested handlers all specialize.
    ``decode`` returns ``(decoded, None)`` or ``(None, FieldError)``.
    """

    def handler(spec: InputFieldSpec, value: object) -> FieldError | None:
        return store_decoded(dest, spec, decode(spec, value))

    return handler


def scalar_into(
    dest: dict[str, object],
    *,
    field_name: Callable[[InputFieldSpec], str] = _spec_field_name,
) -> _FieldHandler:
    """SCALAR handler: ``decode_scalar_leaf`` then store under ``target_name``.

    ``field_name(spec)`` is the GraphQL path the error keys to (default
    ``spec.graphql_name``; serializer nested decode passes the dotted prefix).
    """
    return decoded_into(
        dest,
        lambda spec, value: decode_scalar_leaf(field_name(spec), value),
    )


def file_into(
    dest: dict[str, object],
) -> _FieldHandler:
    """FILE handler: store the Upload under ``spec.target_name``.

    Destination is flavor policy: form ``provided_files`` (Django ``files=``),
    serializer ``provided_data`` (DRF reads files from ``data``).
    """
    return decoded_into(dest, lambda _spec, value: (value, None))


def relation_into(
    dest: dict[str, object],
    *,
    single: _RelationDecoder,
    multi: _RelationDecoder,
    info: Info[object, object],
    field_name: Callable[[InputFieldSpec], str] = _spec_field_name,
    extra: Callable[[InputFieldSpec], Mapping[str, object]] = _no_relation_extra,
) -> _FieldHandler:
    """RELATION_SINGLE / RELATION_MULTI handler over flavor decoders.

    Picks ``multi`` vs ``single`` from ``spec.kind``, calls with the shared
    kwargs (``graphql_name``, ``related_model``, ``key_attname``, ``info``) plus flavor extras
    (the form's ``form_field``), then ``store_decoded``. Flavor null / skip /
    projection policy stays on the decoder (form ``empty_values`` +
    ``to_field_name``; serializer ``None`` + ``obj.pk`` / batched ids).
    """

    def decode(spec: InputFieldSpec, value: object) -> tuple[object, FieldError | None]:
        decoder = multi if spec.kind == RELATION_MULTI else single
        return decoder(
            value,
            graphql_name=field_name(spec),
            related_model=spec.related_model,
            key_attname=spec.key_attname,
            info=info,
            **extra(spec),
        )

    return decoded_into(dest, decode)


def decode_field_handlers(
    dest: dict[str, object],
    *,
    info: Info[object, object],
    single: _RelationDecoder,
    multi: _RelationDecoder,
    file_dest: dict[str, object] | None = None,
    field_name: Callable[[InputFieldSpec], str] = _spec_field_name,
    extra: Callable[[InputFieldSpec], Mapping[str, object]] = _no_relation_extra,
    extra_handlers: dict[str, _FieldHandler] | None = None,
) -> tuple[dict[str, _FieldHandler], _FieldHandler]:
    """Build the SCALAR / RELATION_* / FILE handler map the form + serializer flavors share.

    Returns ``(handlers, scalar_handler)`` for ``decode_provided_fields``.
    ``file_dest`` is the form ``provided_files`` split (Django ``files=``);
    omitted, FILE lands in ``dest`` (DRF ``data``). ``extra_handlers`` is the
    serializer nested map (spreads last, so it can override a default kind).
    Flavor relation decoders stay arguments so form per-element
    ``to_field_name`` and serializer batched ids cannot drift into a mode flag.
    The model rider composes its handler map directly from the ``*_into``
    primitives instead (its FILE and M2M dest policies replace every default
    but ``RELATION_SINGLE``).
    """
    relation = relation_into(
        dest,
        single=single,
        multi=multi,
        info=info,
        field_name=field_name,
        extra=extra,
    )
    handlers = {
        RELATION_SINGLE: relation,
        RELATION_MULTI: relation,
        FILE: file_into(dest if file_dest is None else file_dest),
        **(extra_handlers or {}),
    }
    return handlers, scalar_into(dest, field_name=field_name)


def decode_provided_fields(
    specs: Iterable[InputFieldSpec],
    data: object,
    *,
    handlers: Mapping[str, _FieldHandler],
    scalar_handler: _FieldHandler,
) -> FieldError | None:
    """Route each provided input field by ``spec.kind`` through a handler map.

    The kind-dispatch decode loop the write flavors share: build
    the ``{spec.input_attr: spec}`` reverse map, walk the PROVIDED input fields
    (``UNSET`` stripped - single-sited in ``iter_provided_input_fields``), and
    hand each ``(spec, value)`` to the flavor's handler for ``spec.kind``
    (falling back to ``scalar_handler`` for the scalar leaf). Destination policy
    is the ``decode_field_handlers`` / ``*_into`` factories (the form splits
    ``provided_files`` for Django's ``files=``; the serializer routes everything
    into ``data``, including its ``NESTED_*`` recursion via ``extra_handlers``;
    the model flavor dest-splits M2M and captures ``EXCLUDED`` attrs the same
    way). Each handler returns a ``FieldError`` to short-circuit or ``None`` to
    continue. Returns the first handler ``FieldError`` or ``None``.
    """
    spec_by_attr = {spec.input_attr: spec for spec in specs}
    for python_name, value, _field in iter_provided_input_fields(data):
        spec = spec_by_attr.get(python_name)
        if spec is None:
            continue
        error = handlers.get(spec.kind, scalar_handler)(spec, value)
        if error is not None:
            return error
    return None


def unstorable_columns(
    instance: models.Model,
    names: Container[str],
    *,
    also: Callable[[_FieldAny, object], bool] | None = None,
) -> list[_FieldAny]:
    """Return the declared columns of ``instance`` holding a value the column cannot store.

    Walks the concrete, editable, non-primary-key columns whose field name is in
    ``names`` (the columns the write flavor's input declares) and names each one holding
    ``None`` on a ``null=False`` column, plus each one ``also(field, value)`` accepts, in
    the model's column order. A ``blank=True`` column skips ``Model.clean_fields`` on an
    empty value ("the developer is responsible for making sure they have a valid
    value"), so an omitted or ``null`` value with no default reaches the database's
    ``NOT NULL`` refusal as an ``IntegrityError`` naming no field. The caller runs this
    AFTER that failed save, never before it, so a consumer ``save()`` that fills the
    value in still writes (django-trac 13776 / 20205); the exception is the trigger and
    this reading the diagnosis.

    Reads only the in-memory ``instance`` the save was attempted on, never the
    database, so it is safe on a connection the ``IntegrityError`` left unusable. Each
    column's ``attname`` is read, so a foreign key with no related row reads ``None``
    instead of raising.
    """
    columns: list[models.Field[object, object]] = []
    for field in instance._meta.concrete_fields:
        if field.name not in names or not field.editable or field.primary_key:
            continue
        value = read_attr(instance, field.attname)
        if (value is None and not field.null) or (also is not None and also(field, value)):
            columns.append(field)
    return columns
