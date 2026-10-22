"""The ``FieldError`` envelope type and the write-error constructors shared by every write flavor.

The flavor-neutral owner of the write-error envelope's type and leaf
construction (promoted from ``mutations/resolvers.py`` so the model mutation
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
- ``null_field_error`` / ``empty_validation_error`` - the two leaves whose
  message + code pair was being re-typed by consumers of the module;
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

from typing import TYPE_CHECKING, NamedTuple, cast

import strawberry
from django.core.exceptions import NON_FIELD_ERRORS, FieldDoesNotExist, ValidationError
from django.core.validators import ProhibitNullCharactersValidator
from django.db import models
from django.utils.functional import Promise

from . import truth
from ._narrowing import dict_items, is_char_wise, is_dict, is_iterable, is_list, list_iter
from .lazy import unwrap_lazy_object

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import TypeAlias

    from .inputs import InputFieldSpec
    from .typing import ModelField

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
    "FieldError",
    "UnstorableText",
    "build_error_key_map",
    "coded_error_extensions",
    "empty_validation_error",
    "field_error",
    "integrity_error_field_errors",
    "join_error_path",
    "model_field_error_names",
    "null_field_error",
    "rekey_error_segment",
    "relation_field_error",
    "save_time_error_key_map",
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
    envelope member type: the form-based (0.0.12) and DRF-serializer / auth
    (0.0.13) flavors return this same class rather than a per-flavor mirror,
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
    bytes-like, or a lazy translation ``Promise``, each asked of its real class)
    or any other non-iterable becomes a one-element list (never iterated
    char-by-char into per-character leaves); any other iterable (a DRF
    ``ErrorDetail`` list, a tuple) is materialized with each element rendered by
    ``truth.text``.
    """
    if is_char_wise(value) or truth.is_instance(value, Promise) or not is_iterable(value):
        return [truth.text(value)]
    return [truth.text(item) for item in value]


def _leaf_codes(error: ValidationError) -> list[object]:
    """Return the truthy ``code`` of every leaf of a Django ``ValidationError``.

    ``error_list`` is the flattened leaf list ``messages`` reads; a dict-form
    error carries none (its leaves live under ``error_dict``), and a ``None``
    code is dropped.
    """
    # ``ValidationError.__init__`` stores every non-dict error's leaves as ``error_list``.
    leaves = cast("Iterable[ValidationError]", truth.static_attr(error, "error_list", ()))
    return [leaf.code for leaf in leaves if leaf.code]


def empty_validation_error(path: str = "") -> FieldError:
    """Build the fail-closed leaf for a validation failure carrying no details.

    Public because the DRF flattener needs it: a serializer whose ``is_valid()``
    fails with an empty (or unreadable) error payload still owes the envelope a
    leaf, and ``rest_framework/resolvers.py`` was hand-building this exact
    message + code pair at two sites purely because the name started with an
    underscore. The module docstring's claim that the DRF flattener calls the
    single leaf constructor is only true once this is reachable.
    """
    return field_error(
        path,
        "Validation failed without error details.",
        codes=FIELD_ERROR_CODE_INVALID,
    )


def null_field_error(path: str) -> FieldError:
    """Build the uniform "required field was sent as null" ``FieldError``.

    Siblings :func:`relation_field_error`: one message + code pair for the
    rejection every write flavor makes when a non-nullable field arrives
    explicitly null. The auth flavor reached this leaf through
    ``mutations/resolvers.py`` - importing a write-envelope leaf from the MODEL
    mutation resolver is exactly the layering the promotion of these
    constructors into ``utils/errors.py`` exists to undo.

    The M2M "send an empty list to clear it" rejection is a different
    condition with its own message and is deliberately NOT folded in here.
    """
    return field_error(path, "This field cannot be null.", codes=FIELD_ERROR_CODE_NULL)


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
    spec.target_name`` (``category`` and ``category_id`` for a forward relation); a
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
    model_meta = model._meta

    def model_names(spec: InputFieldSpec) -> tuple[str, ...]:
        name = spec.source or spec.target_name
        try:
            field = model_meta.get_field(name)
        except FieldDoesNotExist:
            return (name,)
        names = model_field_error_names(field) if isinstance(field, models.Field) else ()
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
    error_dict = cast(
        "dict[str, list[ValidationError]] | None",
        truth.static_attr(exc, "error_dict"),
    )
    if error_dict is not None:
        errors: list[FieldError] = []
        for field_name, field_errors in error_dict.items():
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
