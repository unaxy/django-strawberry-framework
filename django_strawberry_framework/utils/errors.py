"""The ``FieldError`` envelope type and the write-error constructors shared by every write flavor.

The flavor-neutral owner of the write-error envelope's type and leaf
construction (kept out of ``mutations/resolvers.py`` so the model mutation
resolver is not the utility module for the form, serializer, auth, and future
write flavors):

- ``FieldError`` / ``NON_FIELD_ERROR_KEY`` - the public envelope member type
  and its ``"__all__"`` non-field sentinel (re-exported by
  ``mutations/inputs.py``, the ``mutations`` package and the package root);
- ``field_error`` - the single ``FieldError`` leaf constructor;
- ``relation_field_error`` - the uniform relation-decode error;
- ``validation_error_to_field_errors`` - the Django ``ValidationError`` mapper;
- ``build_error_key_map`` / ``rekey_error_segment`` / ``ErrorKeyMap`` - the one
  key map every flavor uses to report a validator-origin error under the
  GraphQL input field the client sent (``categoryId``, not ``category``), and
  ``model_field_error_names`` - every name Django keys one model field's errors by,
  and ``save_time_error_key_map`` - the model-backed map a save-time Django
  ``ValidationError`` is keyed through on the ``ModelForm`` and serializer flavors;
- ``integrity_error_field_errors`` - the save-time ``IntegrityError`` envelope;
- ``join_error_path`` - dotted GraphQL error-path joining for nested
  flatteners;
- ``unstorable_text`` + ``UnstorableText`` - the one refusal rule for input text
  (a lone surrogate, an embedded NUL) and the record it answers, shared by the
  write decode (``utils/write_values.py::unstorable_text_error``) and the filter
  form validation (``filters/sets.py::FilterSet._validate_form_or_raise``);
- ``UNBINDABLE_TEMPORAL_MESSAGE`` - the message a temporal, duration or decimal value
  the database cannot bind answers, on a filter (``filters/sets.py::_unbindable_value_errors``,
  which asks Django to build and compile the filter's own predicate) and on a write;
- ``unbindable_temporal`` - whether a datetime or time bound into a column is one
  the database cannot bind, asked of that connection's own adapters; the base of
  ``unstorable_temporal`` and of the identity decode
  (``utils/querysets.py::coerce_field_value_or_none``);
- ``refuses_utc_offset`` - the one rule no Django call answers: an aware datetime
  or time whose UTC offset PostgreSQL refuses in the connection's binding mode (a
  list parameter's elements by the text rule, as psycopg binds them), read over a
  compiled predicate's parameters or a write's values;
- ``refuses_numeric_format`` - PostgreSQL ``numeric``'s format: a decimal whose spelling
  needs more digits before or after the point than ``numeric`` stores, read over a
  compiled predicate's parameters and by the identity decode
  (``utils/querysets.py::coerce_field_value_or_none``);
- ``refuses_integer_range`` - an integer the backend cannot bind as an element of an
  integer ``ArrayField``: each integer a whole-array lookup binds for its right-hand
  side, list parameters read at any nesting depth, held to ``binds_integer`` for the
  element column;
- ``unstorable_temporal`` - the write-side answer: a date, datetime, time or duration
  a temporal or duration column cannot store on the database a write runs on, asked
  of Django's own save-time preparation on that connection (``Field.get_db_prep_save``)
  and of the integer range it binds (``binds_integer``), or (PostgreSQL) a value whose
  UTC offset the server refuses or that it stores but cannot read back, or (psycopg 3)
  an ``ArrayField`` list the driver cannot dump as a whole, applied by every write
  flavor before the save (``utils/write_values.py::unstorable_temporal_error`` on the
  model flavor);
- ``binds_integer`` - whether a backend binds an integer as a value of a column, held
  to the range it stores for the column's internal type (none where the backend states
  no range for that type); shared with the filter bind ask
  (``filters/sets.py::_unbindable_predicate``) and the identity decode
  (``utils/querysets.py::coerce_field_value_or_none``);
- ``null_field_error`` / ``empty_validation_error`` - the two shared leaves
  for an explicit null on a non-nullable column (the column's own message) and a
  validation failure carrying no details (one message + code pair);
- ``FIELD_ERROR_CODE_*`` - the ``FieldError.codes`` vocabulary, a public wire
  contract named once here rather than left as the union of string literals at
  its raise sites;
- ``coded_error_extensions`` + ``*_ERROR_CODE`` - the ``extensions={"code": ...}``
  shape and code vocabulary every framework ``GraphQLError`` carries.

Layering: ``FieldError`` and ``NON_FIELD_ERROR_KEY`` live here, below every
write flavor, so the constructors import nothing from ``mutations/`` and every
flavor depends downward on this module.
"""

from __future__ import annotations

import datetime
import zoneinfo
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple

import strawberry
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import ProhibitNullCharactersValidator
from django.db import connections, models
from django.utils import timezone

from . import truth
from ._array_field import array_leaf_field
from ._narrowing import (
    call_method,
    dict_items,
    is_class,
    is_dict,
    is_iterable,
    is_list,
    is_list_or_tuple,
    is_text_atom,
    list_iter,
    list_of,
    read_attr,
    require,
    require_instance,
)
from .lazy import unwrap_lazy_object
from .relations import written_model_field
from .typing import object_result

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import TypeAlias

    from django.db.backends.base.base import BaseDatabaseWrapper

    from .inputs import InputFieldSpec
    from .typing import ConcreteField, ModelField

    #: The recursive error key map: validator-side name (a model field, form field,
    #: serializer field or serializer ``source``) -> (the GraphQL input field name,
    #: the nested level's own map or ``None``). Built by ``build_error_key_map``.
    ErrorKeyMap: TypeAlias = "dict[str, tuple[str, ErrorKeyMap | None]]"

__all__ = [
    "FIELD_ERROR_CODE_CONFLICT",
    "FIELD_ERROR_CODE_CONSTRAINT",
    "FIELD_ERROR_CODE_INVALID",
    "FIELD_ERROR_CODE_NOT_FOUND",
    "FIELD_ERROR_CODE_NULL",
    "FIELD_ERROR_CODE_PROTECTED",
    "FIELD_ERROR_CODE_TRUNCATED",
    "FILTER_INVALID_ERROR_CODE",
    "GLOBALID_INVALID_ERROR_CODE",
    "GLOBALID_UNVALIDATABLE_ERROR_CODE",
    "NON_FIELD_ERROR_KEY",
    "PAGINATION_INVALID_ERROR_CODE",
    "UNBINDABLE_TEMPORAL_MESSAGE",
    "FieldError",
    "UnstorableText",
    "binds_integer",
    "build_error_key_map",
    "coded_error_extensions",
    "datetime_django_binds",
    "empty_validation_error",
    "field_error",
    "integrity_error_field_errors",
    "join_error_path",
    "model_field_error_names",
    "null_field_error",
    "psycopg_refuses_list_parameter",
    "refuses_integer_range",
    "refuses_numeric_format",
    "refuses_utc_offset",
    "rekey_error_segment",
    "relation_field_error",
    "save_time_error_key_map",
    "unbindable_temporal",
    "unstorable_temporal",
    "unstorable_text",
    "validation_error_to_field_errors",
]

# The non-field error key Django's ``full_clean`` uses for model-wide
# (multi-field-constraint) errors (Django's ``"__all__"`` sentinel). Pinned here
# as the single source of truth so the resolver keys a
# multi-field-constraint ``ValidationError`` to the same sentinel the read of
# ``error_dict`` produces.
NON_FIELD_ERROR_KEY: str = NON_FIELD_ERRORS


@strawberry.type
class FieldError:
    """A field-keyed validation error in the shared mutation error envelope.

    Every mutation flavor returns ``errors: list[FieldError]`` on its generated
    payload; a ``FieldError`` carries a ``field`` path and the list of human
    messages for that field.
    Every flavor keys ``field`` to the GraphQL input field the client sent
    (``categoryId``, ``isPrivate``, a ``Meta.input_class`` rename), whether the
    error came from the input decode, ``serializer.errors``, or a validator
    (``full_clean()``, ``form.errors``, a Django ``ValidationError`` raised by
    save-time code: a ``save()`` / ``delete()`` override, a signal receiver,
    ``perform_mutate`` or a serializer save). A non-field error keys to the
    ``"__all__"`` sentinel. An error on a field the input does not expose keeps
    its validator-side name (the model, form or serializer field name), since
    there is no input field to report; when an input renames a field onto such a
    name, two errors can share one key. Defined here (spec-036 Decision 7) as the ONE
    envelope member type: the form-based and DRF-serializer / auth
    flavors return this same class rather than a per-flavor mirror,
    so a client's error branch is written once. The type is ADDITIVE, not
    frozen - a member may be added (``codes`` / ``path`` below were), never
    removed or retyped. Mirrors graphene-django's ``ErrorType``.

    **Additive client-ergonomics fields.** Two optional,
    default-empty lists sit alongside the legacy ``field`` / ``messages`` (both kept
    intact for compatibility), so a client can branch WITHOUT parsing localized human
    text or the dotted ``field`` string:

    - ``codes`` - the structured error codes. For a serializer failure these are DRF
      ``ErrorDetail.code``s (``required`` / ``invalid`` / ``unique`` / ``blank`` / ...); for a
      Django ``ValidationError`` they are its ``.code``s; framework-generated errors carry a
      deliberate code (``invalid`` for a bad relation id, ``null`` for an explicit null,
      ``not_found`` for a locate miss, ``constraint`` for an integrity fallback).
    - ``path`` - the ``field`` dotted string split into SEGMENTS (``items.0.name`` ->
      ``["items", "0", "name"]``), so a client walks structured paths instead of parsing
      strings. A ROOT non-field error is ``field="__all__"`` with an EMPTY ``path`` (``[]``);
      a NESTED non-field error keeps its segments (``["items", "0", "__all__"]``).

    Both default to ``[]`` so every existing construction site (and a client selecting only
    ``field`` / ``messages``) is unaffected.
    """

    field: str
    messages: list[str]
    codes: list[str] = strawberry.field(default_factory=list)
    path: list[str] = strawberry.field(default_factory=list)


# ---------------------------------------------------------------------------
# ``FieldError.codes`` vocabulary
# ---------------------------------------------------------------------------
# The codes the framework itself emits on the write envelope, named once here:
# the vocabulary is what a client branches on, so it has one home rather than
# being the union of string literals across the subsystems that emit it.
#
# Framework ``"invalid"`` deliberately COLLIDES with Django's and DRF's own
# ``"invalid"`` on the wire - a client cannot tell a framework relation-decode
# rejection from a Django field-validation one by code alone, and that is the
# established shape, not an oversight to fix here.
#
# These are constants, not an ``Enum``, and ``codes=`` arguments are NOT
# validated against them: ``FieldError.codes`` is ``list[str]`` on the wire and
# Django / DRF codes flow through the same parameter, so the vocabulary must
# stay open at the constructor.
FIELD_ERROR_CODE_INVALID = "invalid"
FIELD_ERROR_CODE_NULL = "null"
FIELD_ERROR_CODE_CONSTRAINT = "constraint"
FIELD_ERROR_CODE_NOT_FOUND = "not_found"
FIELD_ERROR_CODE_PROTECTED = "protected"
FIELD_ERROR_CODE_CONFLICT = "conflict"
FIELD_ERROR_CODE_TRUNCATED = "truncated"

# ---------------------------------------------------------------------------
# Coded ``GraphQLError`` extensions
# ---------------------------------------------------------------------------
# The OTHER error vocabulary: the ``extensions={"code": ...}`` payload a
# framework ``GraphQLError`` carries so a client can act on a rejection without
# parsing prose. ``resource_policy.py::RESOURCE_LIMIT_ERROR_CODE`` is the
# established public spelling and stays exported from there (it is already in
# the package root's ``__all__``); the codes below had no owner at all and were
# re-typed as literals at each raise site, with the convention itself
# transmitted only through docstrings.
GLOBALID_INVALID_ERROR_CODE = "GLOBALID_INVALID"
GLOBALID_UNVALIDATABLE_ERROR_CODE = "GLOBALID_UNVALIDATABLE"
FILTER_INVALID_ERROR_CODE = "FILTER_INVALID"
PAGINATION_INVALID_ERROR_CODE = "PAGINATION_INVALID"


def coded_error_extensions(code: str, **detail: object) -> dict[str, object]:
    """Build the ``extensions`` mapping for a coded framework ``GraphQLError``.

    One shape for every coded error the framework raises: a ``"code"`` key
    naming the machine-readable rejection, plus whatever structured detail the
    raise site wants a client to be able to act on without parsing prose
    (``ResourceLimitExceeded``'s ``bound`` / ``limit`` / ``charged``, the
    filterset's ``errors`` payload). Keyword names become extension keys
    verbatim.

    Layering: this owns the SHAPE, never the vocabulary of any one subsystem -
    ``errors.py`` sits below ``filters/`` and ``relay.py`` and must never import
    from them. Codes flow downward: a subsystem's code constant either lives
    here (the four below) or stays at its own owner and is passed in.
    """
    return {"code": code, **detail}


def field_error(path: str, messages: object, *, codes: object = None) -> FieldError:
    """Build ONE ``FieldError`` leaf for the shared envelope.

    The single leaf constructor BOTH the flat Django mapper
    (``validation_error_to_field_errors``) and the recursive DRF serializer
    flattener (``rest_framework/resolvers.py::serializer_errors_to_field_errors``)
    call, so the ``"__all__"`` sentinel + the message-container coercion + the
    structured ``path`` / ``codes`` derivation cannot drift between the two flatteners
    (nor across the three write flavors). An empty ``path`` (a model-wide / non-field
    error) is normalized to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to Django's
    ``"__all__"`` above - the single source). ``messages`` is
    coerced to a ``list[str]``: a bare string becomes a one-element list, any other
    iterable (a DRF ``ErrorDetail`` list, a tuple) is materialized as a list.

    **Structured ``path``:** the dotted ``path`` string is split into segments
    (``items.0.name`` -> ``["items", "0", "name"]``); an empty ``path`` (the root non-field
    error) yields ``[]`` while ``field`` is the ``"__all__"`` sentinel - the documented
    root rule. **Structured ``codes``:** the caller passes the DRF
    ``ErrorDetail.code``s / Django ``ValidationError.code``s (or a framework code); ``None``
    yields ``[]``.
    """
    normalized_path = truth.text(path)
    key = normalized_path or NON_FIELD_ERROR_KEY
    # Root rule: a model-wide / non-field error (an empty path, or the bare
    # ``"__all__"`` sentinel as the WHOLE path - the DRF flattener joins the top-level
    # non-field bucket to exactly that) carries an EMPTY ``path``, while ``field`` stays
    # ``"__all__"``; a NESTED non-field error (``items.0.__all__``) keeps its segments. So
    # the model + serializer flavors agree on the root-non-field shape.
    segments = (
        []
        if not normalized_path or normalized_path == NON_FIELD_ERROR_KEY
        else normalized_path.split(
            ".",
        )
    )
    return FieldError(
        field=key,
        messages=_str_list(messages),
        codes=_str_list(codes) if codes is not None else [],
        path=segments,
    )


def _str_list(value: object) -> list[str]:
    """Coerce a bare string or an iterable into a ``list[str]``.

    The one body behind ``field_error``'s ``messages`` AND ``codes`` coercion
    (the rule the DRF ``ErrorDetail`` flattener depends on): a text atom (text,
    bytes-like, or a lazy translation ``Promise``; ``utils/_narrowing.py::is_text_atom``)
    or any other non-iterable becomes a one-element list (never iterated
    char-by-char into per-character leaves); any other iterable (a DRF
    ``ErrorDetail`` list, a tuple) is materialized with each element rendered by
    ``truth.text``.
    """
    if is_text_atom(value) or not is_iterable(value):
        return [truth.text(value)]
    return [truth.text(item) for item in value]


def _leaf_codes(error: ValidationError) -> list[object]:
    """Return the truthy ``code`` of every leaf of a Django ``ValidationError``.

    ``error_list`` is the flattened leaf list ``messages`` reads; a dict-form
    error carries none (its leaves live under ``error_dict``), and a ``None``
    code is dropped.
    """
    # ``ValidationError.__init__`` stores every non-dict error's leaves as ``error_list``.
    leaves = [
        require_instance(leaf, ValidationError)
        for leaf in list_of(truth.static_attr(error, "error_list", ()))
    ]
    return [leaf.code for leaf in leaves if leaf.code]


def empty_validation_error(path: str = "") -> FieldError:
    """Build the fail-closed leaf for a validation failure carrying no details.

    Public because the DRF flattener needs it: a serializer whose ``is_valid()``
    fails with an empty (or unreadable) error payload still owes the envelope a
    leaf, and ``rest_framework/resolvers.py`` builds it here, as
    ``validation_error_to_field_errors`` does for an empty Django
    ``ValidationError``.
    """
    return field_error(
        path,
        "Validation failed without error details.",
        codes=FIELD_ERROR_CODE_INVALID,
    )


def null_field_error(path: str, column: ConcreteField) -> FieldError:
    """Build the uniform "required field was sent as null" ``FieldError`` for ``column``.

    Siblings :func:`relation_field_error`: the code ``null`` rejection the model flavor
    (``mutations/resolvers.py``) returns when a non-nullable column arrives explicitly
    null, and its create returns for a ``blank=True, null=False`` column with no default
    the input left out, after its INSERT fails
    (``mutations/resolvers.py::_created_row_integrity_errors``). The message is the
    column's own Django ``error_messages["null"]``, so a custom or translated message is
    sent as is: the message the ``ModelForm`` flavor answers a ``null=False`` column its
    form neither refuses nor resolves with (``forms/resolvers.py::_column_null_errors``),
    under the same field, code and path. The serializer flavor hands the ``null`` to the
    serializer, whose DRF ``allow_null`` check refuses it in ``is_valid()`` with DRF's own
    message, code ``null``, when the field is ``allow_null=False``; a ``blank=True,
    null=False`` column the serializer lets through as ``None`` (a generated
    ``required=False`` field left out, a declared ``allow_null=True`` field sent ``null``)
    answers this error after its failed save
    (``rest_framework/resolvers.py::_attempted_row_integrity_errors``). The register
    write step answers an omitted ``password`` with the user model's ``password``
    column (``auth/mutations.py::_register_write_step``).

    The M2M "send an empty list to clear it" rejection is a different
    condition with its own message and is deliberately NOT folded in here.
    """
    return field_error(path, column.error_messages["null"], codes=FIELD_ERROR_CODE_NULL)


def relation_field_error(graphql_name: str) -> FieldError:
    """Build the uniform invalid / hidden / wrong-model relation ``FieldError`` (spec-039 integration).

    The single leaf constructor for the relation-decode error all three write
    flavors raise - the ``036`` model path (``decode_visible_relation_ids``),
    the ``038`` form decoder, and the ``039`` serializer decoder all route
    through the shared ``utils/write_values.py`` decode spine to reach it
    (spec-039 folded away the former per-flavor ``_relation_error`` /
    ``_relation_field_error`` aliases). A wrong-model, hidden, missing, or
    uncoercible id all collapse to this one field-keyed shape (no existence
    leak), keyed to the GraphQL wire name the client sent (``categoryId``). Siblings
    the ``field_error`` leaf ctor above so the ``"Invalid id for relation ..."`` message
    + leaf construction are single
    sourced across every flavor.
    """
    name = truth.text(graphql_name)
    return field_error(
        name,
        f"Invalid id for relation {name!r}.",
        codes=FIELD_ERROR_CODE_INVALID,
    )


def build_error_key_map(
    specs: Iterable[InputFieldSpec],
    *,
    keys_of: Callable[[InputFieldSpec], tuple[str, ...]] | None = None,
) -> ErrorKeyMap:
    """Build the recursive error key map from a mutation's bind-stashed input specs.

    ``{validator-side name: (spec.graphql_name, child_map | None)}``: each
    validator-side name in ``keys_of(spec)`` maps to the spec's GraphQL name, or
    ``spec.target_name`` alone does when ``keys_of`` is ``None`` (the form field
    name on the form path, the declared serializer field name on the DRF path).
    The first name ``keys_of`` returns is the spec's primary name; the rest are
    aliases (a forward relation's ``attname``); no names means no entry.
    The model flavor passes ``model_field_error_names`` of the column behind
    ``spec.input_attr`` (``category`` and ``category_id`` for input
    ``categoryId``); ``save_time_error_key_map`` (the ``ModelForm`` and
    serializer save-time Django ``ValidationError``) passes the same names for
    the model field behind ``spec.source or spec.target_name``.
    Without ``keys_of``, a nested field's ``child_map`` is the same map built over
    its ``nested_specs``, so a nested serializer error re-keys at every depth.
    With ``keys_of``, the map is one level: ``keys_of`` reads one model's field
    names, and a nested level writes another model, so a nested field's
    ``child_map`` is ``None`` (the Django ``ValidationError`` such a map keys
    carries no nesting level to descend by). Every non-nested field's is ``None``.

    Primary names win: every spec's primary name is entered first, and an alias
    only fills a name no primary claimed. Two specs can share names only through
    a caller's ``keys_of`` (no shipped flavor produces it: the serializer
    ownership guards refuse two writable fields over one model field); then each
    primary name keeps its own spec's GraphQL name, while a name that is only an
    alias goes to the first spec listing it. Each flavor's build
    guards reject two inputs sharing one GraphQL name. A field the input does
    not expose has no entry, so an error on it keeps its validator-side name
    (``rekey_error_segment``).
    """
    entries: list[tuple[tuple[str, ...], tuple[str, ErrorKeyMap | None]]] = []
    for spec in specs:
        child = (
            build_error_key_map(spec.nested_specs)
            if spec.nested_specs is not None and keys_of is None
            else None
        )
        names = keys_of(spec) if keys_of is not None else (spec.target_name,)
        entries.append((names, (spec.graphql_name, child)))
    result: ErrorKeyMap = {names[0]: value for names, value in entries if names}
    for names, value in entries:
        for alias in names[1:]:
            _ = result.setdefault(alias, value)
    return result


def model_field_error_names(field: ModelField) -> tuple[str, ...]:
    """Return every name Django keys one model field's validation errors by.

    ``field.name`` always, and a forward relation's ``attname`` (``category_id``
    beside ``category``) too: ``validate_constraints()`` keys a single-field
    constraint error by the name the constraint lists, which may be the
    ``attname``, and a model ``clean()`` may raise under either spelling.
    Django's field-clash check forbids any other field from being named a
    relation's ``attname``, so both names identify this one field.
    """
    if isinstance(field, models.Field) and field.attname != field.name:
        return (field.name, field.attname)
    return (field.name,)


def save_time_error_key_map(
    specs: Iterable[InputFieldSpec],
    model: type[models.Model],
) -> ErrorKeyMap:
    """Build the key map for a Django ``ValidationError`` raised at save time.

    A Django error raised by consumer save-time code (a custom ``save()`` /
    ``create()`` / ``update()``, a model ``save()``, a signal receiver) keys by MODEL
    field name. On a model-backed flavor whose spec's ``target_name`` is not the model
    attr - the ``ModelForm`` (the form field, named after its model field) and the
    serializer (the declared field, or its ``source`` when it declares one:
    ``full_name = CharField(source="name")``) - the keys are
    ``model_field_error_names`` of the backing model field named ``spec.source or
    spec.target_name`` (``category`` and ``category_id`` for a forward relation),
    read through ``utils/relations.py::written_model_field``, so the ``pk`` alias
    names the primary key (``key = IntegerField(source="pk")`` keys ``pk`` and ``id``
    to ``key``; the parent link and its ``attname`` under multi-table inheritance); a
    name with no concrete model field behind it (a form-only or serializer-only
    field) keys by itself. No two serializer specs share a model field (the ownership
    check keys writable sources by the attribute they resolve to, so ``category``
    beside ``source="category_id"`` is rejected at class creation), and a form field
    names one model field, so every name a spec lists is its own: a ``category_ref =
    PrimaryKeyRelatedField(source="category")`` keys both ``category`` and
    ``category_id`` to ``categoryRefId``. A model field no input exposes keeps its
    name. Built only on the failure path.

    The map is one level, read against the backing model only. A Django
    ``ValidationError`` names fields, never the model or the nested item they
    belong to, so every name it carries is read as a field of the backing model:
    an error the save-time code raises about another row (a nested serializer
    item, a related object a signal receiver validates) lands on the input that
    backs a same-named field of this model, else keeps its name; no name is
    re-keyed onto a nested path (a name written as a dotted path matches no
    entry and is kept verbatim). A nested item fails at save time through a DRF
    ``serializers.ValidationError`` in the nested shape (``{"shelves": [{},
    {"code": [...]}]}``), which the serializer flattener keys to the item's path
    (``shelves.1.code``).
    """

    def model_names(spec: InputFieldSpec) -> tuple[str, ...]:
        name = spec.source or spec.target_name
        field = written_model_field(model, name)
        if field is None:
            return (name,)
        names = model_field_error_names(field)
        # The spec's own source leads (its primary name); the field's other names follow.
        return (name, *(other for other in names if other != name))

    return build_error_key_map(specs, keys_of=model_names)


def rekey_error_segment(key: str, key_map: ErrorKeyMap | None) -> tuple[str, ErrorKeyMap]:
    """Re-key ONE error-path segment to its GraphQL input name; return the child level's map.

    The ``"__all__"`` sentinel is checked before the map and never re-keyed (a
    Django field name cannot contain ``__``, so no field can claim it). A mapped
    name returns its GraphQL name and its nested child map (``{}`` when the field
    is not nested). An unmapped key (a numeric index, a field the input does not
    expose) and a ``None`` map both keep the key verbatim with no child map.
    """
    if key == NON_FIELD_ERRORS:
        return key, {}
    mapped = key_map.get(key) if key_map else None
    if mapped is None:
        return key, {}
    graphql_name, child_map = mapped
    return graphql_name, (child_map or {})


def validation_error_to_field_errors(
    exc: ValidationError,
    key_map: ErrorKeyMap | None = None,
) -> list[FieldError]:
    """Map a Django ``ValidationError`` to the ``FieldError`` envelope (spec-036 Decision 7).

    Uses ``exc.error_dict`` when present (per-field), keying the model's
    ``NON_FIELD_ERRORS`` bucket to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to
    ``"__all__"`` above - the single source) so a
    multi-field-constraint error surfaces under ``"__all__"``. Falls back to
    ``exc.messages`` under the sentinel for a non-dict ``ValidationError``. The
    single source for the ``full_clean()`` failure, the ``form.errors`` mapping,
    every flavor's save-time Django ``ValidationError`` (``save_or_field_errors``
    and its update / delete counterparts in ``mutations/resolvers.py``) and the
    ``IntegrityError``-race fallback mapping. Both leaves are built through the
    shared ``field_error`` leaf ctor so the sentinel + message coercion stay
    single-sited with the recursive DRF flattener.

    **Keying:** each ``error_dict`` name passes through ``rekey_error_segment``
    with ``key_map`` (``build_error_key_map``), so a write flavor reports a
    validator error under the GraphQL input field the client sent; a field the
    input does not expose keeps its validator-side name. ``None`` keys every
    name verbatim (a caller with no generated input, such as a service-layer
    error mapped into an envelope). Only the top-level names are keyed: Django
    flattens a nested ``error_dict`` value to its messages, so the error has no
    nested path to re-key.
    """
    # ``ValidationError.__init__`` stores a dict-form error's per-field leaf lists here.
    error_dict = truth.static_attr(exc, "error_dict")
    if error_dict is not None:
        errors: list[FieldError] = []
        for field_name, field_leaves in require(error_dict, is_dict).items():
            field_errors = [
                require_instance(error, ValidationError) for error in list_of(field_leaves)
            ]
            normalized_name = truth.text(field_name)
            # The sentinel check runs before the re-key (a ``NON_FIELD_ERRORS`` bucket
            # is never re-keyed), and an unmapped name keeps its validator-side name.
            path = (
                ""
                if normalized_name == NON_FIELD_ERRORS
                else rekey_error_segment(normalized_name, key_map)[0]
            )
            messages = [message for error in field_errors for message in error.messages]
            # Preserve each leaf Django ``ValidationError.code`` alongside the
            # message (a ``None`` code is dropped).
            codes = [code for error in field_errors for code in _leaf_codes(error)]
            errors.append(
                field_error(path, messages, codes=codes)
                if messages
                else empty_validation_error(path),
            )
        if errors:
            return errors
    messages = exc.messages
    codes = _leaf_codes(exc)
    return [field_error("", messages, codes=codes) if messages else empty_validation_error()]


def integrity_error_field_errors() -> list[FieldError]:
    """Map a save-time ``IntegrityError`` to the ``"__all__"`` envelope.

    The residual after ``full_clean()`` / serializer ``is_valid()``: a constraint
    violation that beat validation (a uniqueness race, a ``NOT NULL`` / FK /
    ``CHECK`` the flavor did not catch on the normal path). The catch is
    ``except IntegrityError`` (broad), so the message is the honest superset
    "A database constraint was violated." rather than over-claiming uniqueness.
    Keys to the ``"__all__"`` sentinel - ``save()``'s ``IntegrityError`` carries
    no reliable cross-backend field mapping. The model, form, and serializer
    write paths all return this same leaf via ``save_or_field_errors`` (the model
    flavor's update and delete through its ``forced_save_or_field_errors`` /
    ``_delete_or_field_errors`` counterparts).
    """
    return [
        field_error(
            "",
            "A database constraint was violated.",
            codes=FIELD_ERROR_CODE_CONSTRAINT,
        ),
    ]


def join_error_path(prefix: str, segment: str) -> str:
    """Join a dotted-path prefix with a child segment (``items`` + ``0`` -> ``items.0``).

    The dotted GraphQL error-path joining shared by nested write-error
    flatteners: an empty ``prefix`` (the root level) yields the bare segment,
    so a root non-field key stays ``__all__`` while a nested one becomes
    ``items.0.__all__`` (the root-vs-nested ``__all__`` distinction itself
    stays with each flattener's key handling).
    """
    normalized_prefix = truth.text(prefix)
    normalized_segment = truth.text(segment)
    return f"{normalized_prefix}.{normalized_segment}" if normalized_prefix else normalized_segment


#: Django's all-backend NUL rule, the validator every ``forms.CharField`` and DRF
#: ``CharField`` runs; its error is the one a refused NUL answers on every surface.
_PROHIBIT_NULL_CHARACTERS = ProhibitNullCharactersValidator()


class UnstorableText(NamedTuple):
    """One refused input text leaf: its dotted path and the message and code it answers."""

    path: str
    message: str
    code: str


def unstorable_text(path: str, value: object) -> UnstorableText | None:
    r"""Return the refusal for the first text leaf of ``value`` the package refuses, else ``None``.

    A GraphQL ``String`` (and every string inside a list, input object or ``JSON``
    value) can carry two kinds of text the package refuses before any database work:

    - a lone UTF-16 surrogate code point (U+D800 via a JSON ``\ud800`` escape in the
      request variables; a document literal cannot carry it, graphql-core refuses it as
      a syntax error), which is not a Unicode scalar value, so every driver fails to
      bind it (sqlite3 and psycopg both raise ``UnicodeEncodeError``). It answers the
      ``invalid`` "Text contains invalid Unicode" refusal; the base ``str``'s
      ``encode("utf-8")`` is the test.
    - an embedded NUL (U+0000, a JSON ``\u0000`` escape), which PostgreSQL refuses in
      every ``text`` / ``varchar`` / ``jsonb`` value (psycopg raises ``DataError``).
      SQLite would store it, so this refusal is policy, not storability: Django's and
      DRF's own all-backend rule, run through ``ProhibitNullCharactersValidator`` so
      its message and code are the ones a ``forms.CharField`` or DRF ``CharField``
      answers, and every surface answers the same on every backend.

    Every other valid scalar value passes. Every text leaf is checked, not only a
    top-level string: each element of a list and each key and value of a dict, at
    any depth (an explicit stack, so a deeply nested ``JSON`` value cannot exhaust the
    interpreter stack). The returned path joins ``path`` with each index or key
    (``tags.1``, ``attributes.color``, ``rows.0.name``) through ``join_error_path``;
    an unstorable dict KEY answers the dict's own path, since a segment holding the
    key would echo the refused text. A Django lazy proxy (``SimpleLazyObject``) is
    read as the object it stands for, and containers and strings through their base
    ``list`` / ``dict`` / ``str`` slots, so a subclass's overridden iteration or
    conversion cannot hide a leaf. Any other leaf (an int, ``None``, an enum member,
    an upload) is storable here.
    """
    pending: list[tuple[str, object]] = [(path, value)]
    while pending:
        current_path, popped = pending.pop()
        current = unwrap_lazy_object(popped)
        if truth.is_instance(current, str):
            refusal = _unstorable_leaf(current_path, truth.text(current))
            if refusal is not None:
                return refusal
        elif is_list(current):
            pending.extend(
                reversed(
                    [
                        (join_error_path(current_path, str(index)), element)
                        for index, element in enumerate(list_iter(current))
                    ],
                ),
            )
        elif is_dict(current):
            # Each key is a text leaf keyed to the dict, checked before its value.
            pending.extend(
                reversed(
                    [
                        entry
                        for key, item in dict_items(current)
                        for entry in (
                            (current_path, key),
                            (join_error_path(current_path, truth.text(key)), item),
                        )
                    ],
                ),
            )
    return None


def _unstorable_leaf(path: str, text: str) -> UnstorableText | None:
    """Answer one exact-``str`` text leaf's refusal keyed to ``path``, or ``None`` if storable."""
    try:
        _ = text.encode("utf-8")
    except UnicodeEncodeError:
        return UnstorableText(
            path,
            "Text contains invalid Unicode (unpaired surrogate code points).",
            FIELD_ERROR_CODE_INVALID,
        )
    try:
        _PROHIBIT_NULL_CHARACTERS(text)
    except ValidationError as exc:
        (message,) = exc.messages
        return UnstorableText(path, message, truth.text(exc.code))
    return None


#: The message a value the database cannot bind answers (``unbindable_temporal``,
#: ``refuses_numeric_format``).
UNBINDABLE_TEMPORAL_MESSAGE = "Enter a value the database can represent."


def unbindable_temporal(
    column: object,
    value: object,
    using: Callable[[], str],
    *,
    bound_as_text: bool = False,
) -> bool:
    """Return whether the database ``using()`` names refuses to bind ``value`` into ``column``.

    ``column`` is the model field a write stores ``value`` in, or an identity decode binds it
    against; ``value`` is the value itself, or a list of them (an ``ArrayField``'s flattened
    elements). A value the scalar parse and the field's own clean accept can still be one
    the backend's adapter cannot bind; the driver's error would then escape as an
    unexpected one. The answer asks the connection's own operations, so it refuses exactly
    what that backend refuses (an ``OverflowError`` or ``ValueError`` from the adapter),
    and nothing else:

    - a ``datetime`` in a ``DateTimeField``: ``adapt_datetimefield_value``. SQLite, MySQL
      and Oracle project an aware value onto the connection's time zone, which fails when
      the projection leaves years 1..9999, and refuse any aware value when ``USE_TZ`` is
      false.
    - a ``time`` in a ``TimeField``: ``adapt_timefield_value``, which refuses an aware time
      on SQLite, MySQL and Oracle.
    - on PostgreSQL, whose adapters pass both through, an aware one whose UTC offset the
      server refuses (``refuses_utc_offset``). ``bound_as_text`` holds the value to the
      text rule whatever the connection's binding mode: psycopg binds the elements of a
      list parameter (an ``ArrayField`` write) as text even under server-side binding.

    A ``None`` member binds. Any other column answers ``False`` without calling ``using``
    or touching ``django.db.connections``. A filter's value is not read here: the filter
    form validation asks Django to build and compile the filter's own predicate
    (``filters/sets.py::_unbindable_value_errors``).
    """
    if isinstance(column, models.DateTimeField):
        bound_type: type[object] = datetime.datetime
    elif isinstance(column, models.TimeField):
        bound_type = datetime.time
    else:
        return False
    connection = connections[using()]
    operations = connection.ops
    members = list(value) if is_list_or_tuple(value) else [value]
    bound = [member for member in members if isinstance(member, bound_type)]
    try:
        for member in bound:
            if isinstance(member, datetime.datetime):
                _ = operations.adapt_datetimefield_value(member)
            else:
                _ = operations.adapt_timefield_value(member)
    except (OverflowError, ValueError):
        return True
    return refuses_utc_offset(connection, bound, bound_as_text=bound_as_text)


def refuses_utc_offset(
    connection: BaseDatabaseWrapper,
    values: Iterable[object],
    *,
    bound_as_text: bool = False,
) -> bool:
    """Whether PostgreSQL refuses any aware datetime or time in ``values`` for its UTC offset.

    ``values`` are what a query or a write binds on ``connection``: a compiled predicate's
    parameters, or a write's values. No Django call answers this: PostgreSQL's adapters pass
    an aware datetime or time through, and the server refuses it (``DataError``) only once
    the query runs. A list or tuple among ``values`` is one list parameter (an
    ``ArrayField`` lookup's ``gt`` or ``in`` right-hand side): psycopg binds its elements
    as text in either binding mode, so each, at any nesting depth, is held to the text
    rule. Every other value, and every value on any other backend, is not read.
    """
    for value in values:
        if is_list_or_tuple(value):
            if refuses_utc_offset(connection, value, bound_as_text=True):
                return True
        elif isinstance(value, datetime.datetime | datetime.time) and _postgresql_refuses_offset(
            connection,
            value,
            bound_as_text=bound_as_text,
        ):
            return True
    return False


#: The UTC offset magnitude from which PostgreSQL refuses a ``timestamptz`` / ``timetz``
#: (``time zone displacement out of range``); it accepts up to 15:59:59.
_POSTGRESQL_OFFSET_LIMIT = datetime.timedelta(hours=16)


def _postgresql_refuses_offset(
    connection: BaseDatabaseWrapper,
    scalar: datetime.datetime | datetime.time,
    *,
    bound_as_text: bool,
) -> bool:
    """Whether PostgreSQL refuses aware ``scalar`` for its UTC offset; ``False`` on any other backend.

    Under client-side binding (psycopg 2, and psycopg 3's default ``ClientCursor``) the
    value reaches the server as text carrying its offset, which PostgreSQL parses: an
    offset of 16:00 or more either way, or one with a fraction of a second, is refused.
    Under psycopg 3's server-side binding a ``datetime`` travels as a UTC instant, so
    no offset refuses it, while a ``time`` still carries its offset (whole seconds), so
    16:00 or more is refused. ``bound_as_text`` (an ``ArrayField`` element, which psycopg
    binds as text in either mode) applies the client-side rule without reading the mode.
    """
    offset = scalar.utcoffset()
    if offset is None or connection.vendor != "postgresql":
        return False
    out_of_range = abs(offset) >= _POSTGRESQL_OFFSET_LIMIT
    if not out_of_range and not offset.microseconds:
        return False
    if bound_as_text or _binds_client_side(connection):
        return True
    return out_of_range and isinstance(scalar, datetime.time)


_POSTGRESQL_NUMERIC_INTEGER_DIGITS = 131072
"""Digits PostgreSQL's unconstrained ``numeric`` stores before the decimal point."""

_POSTGRESQL_NUMERIC_FRACTION_DIGITS = 16383
"""Digits PostgreSQL's unconstrained ``numeric`` stores after the decimal point."""

_POSTGRESQL_NUMERIC_EXPONENT_LIMIT = 1073741823
"""The written exponent ``numeric_in`` refuses at or past (``INT_MAX / 2``), a zero's included."""


def refuses_numeric_format(connection: BaseDatabaseWrapper, values: Iterable[object]) -> bool:
    """Whether PostgreSQL refuses any decimal in ``values`` as past ``numeric``'s format.

    ``values`` are what a query binds on ``connection``: a compiled predicate's
    parameters, or a decimal an identity decode is about to bind. psycopg sends a
    ``Decimal`` as its own spelling (``str``), and ``numeric_in`` parses it into
    ``numeric``'s format whatever the column's typmod: up to 131072 digits before the
    decimal point and up to 16383 after (PostgreSQL's documentation, "Numeric Types"),
    past either of which the server refuses the bind as "value overflows numeric format"
    (``DataError``). The spelling is read as written, trailing fractional zeros
    included: ``numeric_in`` keeps the written scale. A zero has no digit before the
    point whatever its exponent (``numeric_in`` gives a zero weight 0), so only its
    scale and its written exponent's own bound hold it (``0E+1000000`` binds as ``0``,
    ``0E-16384`` is refused). A list or tuple among ``values``
    is one list parameter, whose elements are read at any nesting depth. Every other
    value, and every value on any other backend, is not read. SQLite is not asked since it
    refuses no spelling: Django binds the decimal as its text, which the ``NUMERIC`` column
    compares as a double, so a value past a double's range or precision compares as the
    nearest double (zero, an infinity, or the double a longer spelling rounds to) rather
    than failing the bind.
    """
    if connection.vendor != "postgresql":
        return False
    for value in values:
        if is_list_or_tuple(value):
            if refuses_numeric_format(connection, value):
                return True
        elif isinstance(value, Decimal) and not _fits_numeric(value):
            return True
    return False


def refuses_integer_range(
    connection: BaseDatabaseWrapper,
    element_field: ConcreteField,
    values: Iterable[object],
) -> bool:
    """Whether ``connection`` cannot bind an integer in ``values`` as an ``element_field`` value.

    ``values`` are what a lookup whose left-hand side is an ``ArrayField`` of
    ``element_field`` binds for its right-hand side (``Lookup.process_rhs``): each element
    a whole-array lookup binds is a parameter of its own (``ARRAY[%s, ...]``) or a member
    of one list parameter (``gt`` binds the list whole). Every integer is held to
    ``binds_integer`` for ``element_field``, so a member past the range
    the backend stores for the element's type is refused: Django holds an element to that
    range nowhere, and the driver (SQLite's, past 64 bits) or the server (PostgreSQL's
    ``::integer[]`` cast) would refuse it at the query. A list or tuple among ``values``
    is one list parameter, whose elements are read at any nesting depth. A ``bool`` and
    every other value are not read.
    """
    for value in values:
        if is_list_or_tuple(value):
            if refuses_integer_range(connection, element_field, value):
                return True
        elif (
            isinstance(value, int)
            and not isinstance(value, bool)
            and not binds_integer(connection, element_field, value)
        ):
            return True
    return False


def _fits_numeric(number: Decimal) -> bool:
    """Whether ``number``'s spelling stays within PostgreSQL ``numeric``'s format."""
    exponent = number.adjusted() - len(number.as_tuple().digits) + 1
    if number.is_zero():
        return (
            -_POSTGRESQL_NUMERIC_FRACTION_DIGITS <= exponent < _POSTGRESQL_NUMERIC_EXPONENT_LIMIT
        )
    return (
        max(number.adjusted() + 1, 0) <= _POSTGRESQL_NUMERIC_INTEGER_DIGITS
        and max(-exponent, 0) <= _POSTGRESQL_NUMERIC_FRACTION_DIGITS
    )


def _binds_client_side(connection: BaseDatabaseWrapper) -> bool:
    """Whether a PostgreSQL connection's cursors bind parameters into the query text.

    psycopg 2 always does. psycopg 3 does through a ``ClientCursor``, the cursor class
    Django connects with unless ``OPTIONS["server_side_binding"]`` is ``True`` or
    ``OPTIONS["cursor_factory"]`` names another (``None`` is psycopg's own ``Cursor``,
    which binds on the server); read from the parameters Django connects with
    (``get_connection_params``), so the connection is never opened.
    """
    client_cursor = read_attr(read_attr(connection, "Database"), "ClientCursor", None)
    params: dict[str, object] = connection.get_connection_params()
    factory = params.get("cursor_factory")
    return not is_class(client_cursor) or (
        is_class(factory) and issubclass(factory, client_cursor)
    )


def unstorable_temporal(column: object, value: object, using: Callable[[], str]) -> bool:
    """Return whether the database ``using()`` names cannot store ``value`` in ``column``.

    The write-side answer for a temporal or duration column: ``value`` is what a write
    flavor is about to store in ``column``, after its own parse and validation. Each value
    the column converts at the save is asked of Django itself, as the save prepares it
    (``Field.get_db_prep_save`` on that connection): a datetime in a ``DateField`` (made
    naive in the default time zone under ``USE_TZ``, then cast to its date), a date or
    datetime in a ``DateTimeField``, a time or datetime in a ``TimeField`` (a datetime
    stored as its naive ``time()``), a duration in a ``DurationField``. A plain ``date`` in
    a ``DateField`` always stores and is not asked. Four kinds of value are refused:

    - one Django's preparation refuses (an ``OverflowError`` or ``ValueError``): an aware
      datetime whose date in the default time zone leaves years 1..9999 in a
      ``DateField``; on SQLite, MySQL and Oracle an aware datetime whose projection onto
      the connection's time zone leaves years 1..9999, any aware datetime when
      ``USE_TZ`` is false, and an aware time.
    - one prepared as an integer the backend cannot bind (``binds_integer``): a duration
      on a backend without a native interval (SQLite, MySQL) is bound as its microsecond
      count, whose 64 bits hold durations up to 106751991 days 04:00:54.775807 either way.
    - on PostgreSQL, whose adapters pass datetimes and times through, an aware one whose
      UTC offset the server refuses in the connection's binding mode
      (``refuses_utc_offset``).
    - an aware datetime on a backend that stores the instant itself
      (``features.supports_timezones``: PostgreSQL), whose wall clock in the session
      time zone (``connection.timezone_name``: ``UTC`` under ``USE_TZ``, else
      ``TIME_ZONE``) leaves years 1..9999. PostgreSQL stores it, but the driver cannot
      load it back as a Python datetime, so the write pipeline's re-fetch of the saved
      row would raise. The zone's offset is read at the value's own wall clock, so no
      intermediate UTC value can overflow where the session's wall clock does not.

    A naive datetime or a date in a ``DateTimeField`` is first read as the datetime Django
    binds for it (``datetime_django_binds``), so the ask emits none of the warnings the
    save emits for it. An ``ArrayField`` holds every element (at any nesting depth) to the
    same rule against its ``base_field``, except that psycopg binds a list's elements as
    text in either binding mode, so on PostgreSQL each is held to the client-side offset
    rule; a ``None`` element, like a ``None`` value, stores. On PostgreSQL through psycopg
    3 the prepared list as a whole is then asked of the driver
    (``_psycopg_refuses_list``), which dumps every element with one dumper and can refuse
    a list whose elements each store alone (a naive time beside an aware one). Any other
    column, and a value holding nothing the column converts, answer ``False`` without
    calling ``using`` or touching ``django.db.connections``.
    """
    column, depth = array_leaf_field(column)
    values: list[object] = [value]
    for _ in range(depth):
        values = [element for item in values if is_list_or_tuple(item) for element in item]
    kinds = _converted_kinds(column)
    if kinds is None or not isinstance(column, models.Field):
        return False
    asked_types, stored_type = kinds
    if not any(isinstance(element, asked_types) for element in values):
        return False
    connection = connections[using()]
    # ``connection.timezone`` is ``None`` exactly when ``USE_TZ`` is off.
    use_tz = connection.timezone is not None
    prepared: list[object] = []
    asked: list[object] = []
    try:
        for element in values:
            if not isinstance(element, asked_types):
                prepared.append(element)
                continue
            bound = (
                datetime_django_binds(element, use_tz=use_tz)
                if isinstance(column, models.DateTimeField) and isinstance(element, datetime.date)
                else element
            )
            answer = object_result(column.get_db_prep_save, bound, connection)
            prepared.append(answer)
            asked.append(answer)
    except (OverflowError, ValueError):
        return True
    in_array = depth > 0
    if (
        any(
            isinstance(answer, int)
            and not isinstance(answer, bool)
            and not binds_integer(connection, column, answer)
            for answer in asked
        )
        or refuses_utc_offset(connection, asked, bound_as_text=in_array)
        or (in_array and _psycopg_refuses_list(connection, prepared, stored_type))
    ):
        return True
    if not isinstance(column, models.DateTimeField) or not connection.features.supports_timezones:
        return False
    zone = zoneinfo.ZoneInfo(connection.timezone_name)
    return any(
        isinstance(answer, datetime.datetime)
        and timezone.is_aware(answer)
        and _session_wall_clock_overflows(answer, zone)
        for answer in asked
    )


def _converted_kinds(column: object) -> tuple[tuple[type[object], ...], type[object]] | None:
    """Return the value kinds ``column`` converts at the save, and the kind it binds; else ``None``.

    The first member is what ``unstorable_temporal`` asks Django to prepare for the
    column, the second the type of a prepared value PostgreSQL's adapters pass through
    (``_psycopg_refuses_list``). ``DateTimeField`` is read before ``DateField``, its base.
    """
    if isinstance(column, models.DateTimeField):
        return (datetime.date,), datetime.datetime
    if isinstance(column, models.DateField):
        return (datetime.datetime,), datetime.date
    if isinstance(column, models.TimeField):
        return (datetime.time, datetime.datetime), datetime.time
    if isinstance(column, models.DurationField):
        return (datetime.timedelta,), datetime.timedelta
    return None


def datetime_django_binds(value: datetime.date, *, use_tz: bool) -> datetime.datetime:
    """Return the datetime a ``DateTimeField`` binds for ``value``, without Django's warning.

    A ``date`` that is not a ``datetime`` becomes its midnight, and under ``USE_TZ``
    (``use_tz``) a naive datetime (that midnight included) is made aware in the default
    time zone (``TIME_ZONE``); an aware datetime is returned as it is. Django makes the
    same projection at the save and at a lookup's bind, and warns (``RuntimeWarning``) as
    it makes a naive value aware; this read is silent, since it only reads what Django
    will bind, and it runs on the write pipeline's threads and in an identity decode
    (``utils/querysets.py::coerce_field_value_or_none``), where no warnings filter can be
    scoped to one call.
    """
    # Adapted from Django's DateTimeField.to_python and DateTimeField.get_prep_value
    # (django/db/models/fields/__init__.py, BSD-3-Clause), their warning left out and
    # ``settings.USE_TZ`` read as ``use_tz``.
    # The complete upstream license ships in LICENSE.django.
    if isinstance(value, datetime.datetime):
        stamp = value
    else:
        stamp = datetime.datetime(value.year, value.month, value.day)  # noqa: DTZ001 - naive, as Django builds it
    if use_tz and timezone.is_naive(stamp):
        default_timezone = timezone.get_default_timezone()
        stamp = timezone.make_aware(stamp, default_timezone)
    return stamp


def binds_integer(connection: BaseDatabaseWrapper, field: object, number: int) -> bool:
    """Whether ``connection`` binds the integer ``number`` as a value of ``field``.

    ``number`` is held to the range the backend stores for ``field``'s internal type
    (``DatabaseOperations.integer_field_range``, the range Django's integer comparison
    lookups test a bound against before binding it): ``IntegerField``'s 32 bits on
    PostgreSQL, 64 bits for every integer type on SQLite. A field that is no
    ``IntegerField`` yet binds an integer, as a ``DurationField`` binds its microsecond
    count on a backend without a native interval, is held to ``BigIntegerField``'s range.
    An internal type the backend states no range for (an ``IntegerField`` subclass naming
    its own, absent from ``DatabaseOperations.integer_field_ranges``) holds no limit: the
    lookup raises ``KeyError`` there, and Django holds an ``in`` member or a ``range``
    bound to no range for it either.
    """
    internal_type = (
        field.get_internal_type() if isinstance(field, models.IntegerField) else "BigIntegerField"
    )
    try:
        bounds = connection.ops.integer_field_range(internal_type)
    except KeyError:
        return True
    return _within_integer_range(number, bounds)


def _within_integer_range(number: int, bounds: tuple[int | None, int | None]) -> bool:
    """Whether ``number`` lies inside ``bounds``, either end of which a backend may leave open.

    ``None`` at an end is no limit there, as Django's range-aware integer lookups read it
    (``django.db.models.lookups.IntegerFieldOverflow``).
    """
    low, high = bounds
    return (low is None or number >= low) and (high is None or number <= high)


def psycopg_refuses_list_parameter(
    connection: BaseDatabaseWrapper,
    params: Iterable[object],
) -> bool:
    """Whether psycopg 3 refuses to dump any list parameter among ``params``.

    ``params`` are a compiled predicate's parameters; a list or tuple among them is one
    list parameter (an ``ArrayField`` lookup's ``gt`` or ``in`` right-hand side), which
    psycopg dumps with one element dumper, so a naive time beside an aware one raises
    the driver's ``DataError`` when the query binds it. Each is asked of the driver as
    it stands, nested lists included (``_psycopg_refuses_list``): Django has already
    prepared its elements for the lookup, so every one is dumped as the query dumps it.
    """
    return any(
        is_list_or_tuple(param) and _psycopg_refuses_list(connection, list(param), object)
        for param in params
    )


def _psycopg_refuses_list(
    connection: BaseDatabaseWrapper,
    values: list[object],
    stored_type: type[object],
) -> bool:
    """Whether psycopg 3 refuses to dump ``values``, one list parameter's elements.

    psycopg dumps a list parameter with one element dumper, chosen from a single element
    of the list, so a list whose elements each bind alone can still be refused: a naive
    time dumped by the aware-time dumper raises the driver's ``DataError`` ("cannot
    calculate the offset of tzinfo 'None' without a date") when the query or save binds
    it. The list is asked of the driver itself, as it will be bound: dumped as text by
    the driver's ``adapt.Transformer`` over the open connection's adapters
    (``connection.connection``, only when already connected; the connection is never
    opened), else the driver module's own ``adapters``. Only the driver's ``DataError``
    refuses; any other exception propagates. ``values`` are the elements of an
    ``ArrayField`` write, each one its ``base_field`` converts as Django prepares it for
    the save (``unstorable_temporal``) and every other one as it stands, ``None``
    included, or a filter's list parameter as Django prepared it
    (``psycopg_refuses_list_parameter``, ``stored_type`` ``object``). They are asked only
    when every one is ``None`` or an instance of ``stored_type``, the type the column
    stores (any other element of a write is converted by the column's ``to_python`` at
    the save, not dumped as it stands). A connection that is not PostgreSQL, and psycopg
    2 (no ``adapters`` / ``adapt.Transformer``), are not asked.
    """
    if connection.vendor != "postgresql" or not all(
        element is None or isinstance(element, stored_type) for element in values
    ):
        return False
    driver = read_attr(connection, "Database")
    adapt = read_attr(driver, "adapt", None)
    transformer_cls = read_attr(adapt, "Transformer", None)
    text_format = read_attr(read_attr(adapt, "PyFormat", None), "TEXT", None)
    refusal = read_attr(driver, "DataError", None)
    raw_connection = read_attr(connection, "connection", None)
    adapters = read_attr(driver if raw_connection is None else raw_connection, "adapters", None)
    if (
        adapters is None
        or not callable(transformer_cls)
        or not (is_class(refusal) and issubclass(refusal, Exception))
    ):
        return False
    try:
        _ = call_method(transformer_cls(adapters), "dump_sequence", [values], [text_format])
    except refusal:
        return True
    return False


def _session_wall_clock_overflows(value: datetime.datetime, zone: datetime.tzinfo) -> bool:
    """Whether aware ``value``'s wall clock in ``zone`` leaves years 1..9999.

    The shift is the difference between two aware datetimes sharing ``value``'s wall
    clock (``zone``'s offset minus ``value``'s), computed as a ``timedelta``, so only the
    final wall clock can overflow.
    """
    wall = value.replace(tzinfo=None)
    try:
        _ = wall + (value - wall.replace(tzinfo=zone))
    except OverflowError:
        return True
    return False
