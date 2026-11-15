"""The sync + async serializer-mutation resolver pipeline.

The DRF-serializer write runtime, the third sibling of ``mutations/resolvers.py``
(the ``036`` model pipeline) and ``forms/resolvers.py`` (the ``038`` form
pipeline). The pipeline is (spec-039 Decision 8):

    (update) locate -> authorize -> decode -> construct -> validate
            -> write -> re-fetch -> payload

**Authorize runs BEFORE the relation decode** (the ``036`` / ``038`` security
invariant): the decode issues visibility-scoped ``get_queryset`` queries, so
running it pre-auth would let an unauthorized caller probe related-object
visibility by id (a write-auth denial ``GraphQLError`` vs an in-band relation
``FieldError`` is an observable distinction). The ``transaction.atomic()``
boundary + the locate preamble + the authorize-before-decode ordering + the
optimizer re-fetch tail are NOT re-hand-rolled here: they are single-sited in the
shared ``mutations/resolvers.py::run_write_pipeline_sync`` skeleton, and this
flavor supplies only the serializer ``decode_step`` / ``write_step`` callbacks.

The serializer-specific invariants this module owns:

- **The decode produces a SERIALIZER-FIELD-keyed ``provided_data``** (spec-039 Decision
  8). DRF serializers are keyed by DECLARED field name and read uploads from
  ``data`` like any other value (the deliberate contrast with Django forms, which
  split ``files=``). The reverse map
  (``mutation_cls._input_field_specs``, a list of
  ``utils/inputs.py::InputFieldSpec``, read per request as the executing schema named
  it, ``utils/inputs.py::published_input_specs``) routes each provided input attr to its
  serializer field name (``spec.target_name``) + decode ``kind`` (``SCALAR`` /
  ``RELATION_SINGLE`` / ``RELATION_MULTI`` / ``FILE``).

- **The dedicated serializer relation decoder mirrors the ``038`` form decoder**
  (serializer-field-keyed, NOT the model-attr-keyed ``036`` decode; all three
  ride ``decode_provided_fields``). Each relation id - a GlobalID string *or* a raw
  pk, by target - is type-checked against the relation's **target model**, which is recorded on
  the bind-stashed reverse map (``InputFieldSpec.related_model``, resolved once at
  build from the backing FK via the serializer field's ``source``, or
  ``field.queryset.model`` for a serializer-only relation, so the
  query path never re-discovers the serializer field set), then **resolved to the
  visible object through
  the related primary ``DjangoType.get_queryset``** via the shared
  ``utils/querysets.py::visible_related_object`` (the SAME object-returning
  visibility query the form decoder re-keys over), reduced to the pk a
  ``PrimaryKeyRelatedField`` expects. A hidden / wrong-model / uncoercible id is a
  field-keyed ``FieldError`` keyed to ``spec.graphql_name`` (the GraphQL wire name
  the executing schema published and the client sent, e.g. ``categoryId``). The
  generated input field exposes exactly ONE strategy-dependent shape (spec-039
  Decision 7 - an ``ID`` carrying a GlobalID for a Relay target, else the raw-pk
  scalar); the shared decode helper reads which one from
  the target (``utils/write_values.py::relation_takes_global_id``), never from the
  value.

- **A relation ``GlobalID`` is decoded against the target type's RECORDED
  ``effective_globalid_strategy``** via ``decode_model_global_id`` (which takes the
  expected model and reads the recorded state), NOT a live settings read / a
  strategy re-validation on the query path (the spec-039 config-assessment
  grep-guard; the strategy is resolved once at finalization, never re-read per
  request).

- **The serializer is constructed via the CONSTRUCTOR-ONLY ``get_serializer_kwargs``
  hook + the framework merge** (spec-039 Decision 8). The framework
  builds the authoritative serializer ``data`` ITSELF - decoded client data plus the
  ``get_serializer_injected_data`` injection (whose keys must EXACTLY match
  ``Meta.injected_fields``) - then calls ``get_serializer_kwargs(info, data=<copy>,
  hook_context=<context>)`` for constructor kwargs only. ``data``, ``instance``,
  ``partial``, ``context["request"]``, and ``context["write_alias"]`` are
  FRAMEWORK-OWNED: a returned ``data`` other than the copy the hook received, or any
  ``instance`` or ``partial``, is a ``ConfigurationError``. ``partial=True`` is
  injected for update (never create); ``context["request"]`` is set to the framework
  request (the actor the inherited ``check_permission`` seam authorized against);
  ``context["write_alias"]`` is set to the pipeline's pinned write alias so custom
  serializer code stays inside the one transaction.

- **Validate via ``serializer.is_valid()``** - a failure maps the nested
  ``serializer.errors`` onto the ``FieldError`` envelope via the dedicated
  **recursive** ``serializer_errors_to_field_errors`` flattener (dotted path
  ``items.0.name``; DRF's ``non_field_errors`` / ``NON_FIELD_ERRORS_KEY`` bucket ->
  the ``"__all__"`` sentinel at every level - NOT the one-level ``036``
  ``validation_error_to_field_errors``), and returns a null-object payload. A
  validated date, datetime, time or duration the pinned alias cannot store (or, on
  PostgreSQL, read back), or a decimal past PostgreSQL ``numeric``'s format its column's
  own validators accept, is the field's ``invalid`` error through the same flattener
  before any write: at each writable root field's conversion
  (``_hold_unstorable_values``), and after ``is_valid()`` for a value a
  ``validate_<field>`` or ``validate()`` hook sets
  (``_unstorable_value_errors``). Each DRF uniqueness validator's original call at any
  level, a nested serializer's included, runs on a copied pinned queryset whose actual
  ORM lookup construction and one compilation are guarded. An unbindable value is the
  field's ``invalid`` error at its nested path, never a raw error or an aborted
  transaction (``utils/query_bind.py::guard_query``); a nested value no such
  validator binds is the consumer ``create()`` / ``update()``'s to write. DRF's own ``overflow``
  answer comes first, and a datetime DRF cannot place in a time zone, which it raises as
  a raw ``OverflowError``, fails its ``DateTimeField`` with that same ``overflow`` error
  (``_translate_datetime_overflow``).

- **Write via ``serializer.save()`` inside a nested-``atomic`` savepoint and the
  pinned-alias write phase, in a value-preserving closure** (the closure captures
  ``saved = serializer.save()`` via ``nonlocal`` - called EXACTLY ONCE). A save
  failure rolls the savepoint back BEFORE the exception converts into the
  envelope, so a custom ``save()`` that wrote rows then raised leaves NO partial
  write. Routing is by exception CLASS, all caught OUTSIDE the atomic
  block: a DRF ``serializers.ValidationError``'s ``.detail`` -> the recursive
  flattener; a Django ``ValidationError`` and an ``IntegrityError`` -> the shared
  ``036`` ``save_or_field_errors`` wrapper every flavor's save rides (the flat
  mapper over ``error_dict`` / ``messages``, NEVER ``.detail``, its model-side
  names - ``spec.source or spec.target_name`` - re-keyed to the GraphQL input
  names through ``save_time_error_key_map``, one level, since a Django error names
  no nested item; the integrity mapper, which answers a refused row's ``None`` on a
  ``blank=True, null=False`` input column as that column's field-keyed ``null`` error,
  read from the backing-model row (the model's own, a proxy's or a multi-table
  child's) whose save the write witness saw raise the caught exception
  (``_attempted_row_integrity_errors``)),
  never a top-level ``GraphQLError``. A
  nested item fails at save time through a DRF ``ValidationError`` in the nested
  shape, which the flattener keys to the item's path. DRF's ``update()`` saves
  through Django's update-else-insert, so on an update a ``created=True`` write of the
  located row's own table the witness (``_write_witness``) records under the
  authorized pk on the pinned alias is the re-INSERT of a located row a concurrent
  transaction deleted after the
  locate: the step returns the in-band ``conflict`` envelope on ``id``, rolled back
  with the re-inserted row, before the saved result is validated. A decode or
  ``is_valid()`` that fails over such a row first (``serializer.errors``, or a
  ``DoesNotExist`` DRF's ``UniqueTogetherValidator`` raises reading the vanished
  row's relation) is the same envelope: the shared skeleton probes the located row
  on a step failure (``mutations/resolvers.py::run_write_pipeline_sync``).

- **The re-fetch rides the ``036`` ``refetch_optimized`` path** (spec-039 Decision 9):
  the shared skeleton re-fetches the saved object by pk WITHOUT the visibility
  filter, routed through the optimizer so the plan keeps ``select_related`` /
  ``prefetch_related`` and, under the mutation operation, introduces no
  ``.only(...)`` on a queryset that carries none - no new optimizer code.

- **One ``transaction.atomic()`` boundary; the async path runs the sync body in
  one ``sync_to_async(thread_sensitive=True)`` call** - ``make_resolver_entries``'
  async entry, which runs the body through ``run_in_one_sync_boundary`` for the model
  and form flavors too, so the three flavors cannot drift on the boundary contract.

Single-sourced: the locate / authorize / id-decode / re-fetch / payload / atomic
boundary are the model flavor's shared skeleton; the shared save-time wrapper
(``save_or_field_errors``: the flat Django mapper + the integrity mapper), the
shared ``field_error`` leaf ctor, the ``NON_FIELD_ERROR_KEY`` sentinel, the
raw-pk coercion, and the
object-returning ``visible_related_object`` visibility query are all CALLED, not
re-implemented (the spec-039 import manifest). The serializer-specific code is the
serializer-field-keyed relation decoder and the recursive serializer-error
flattener.
"""

from __future__ import annotations

import copy
import dataclasses
import enum
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Final, TypeGuard, TypeVar, cast

from django.db import transaction
from django.db.models import Field, QuerySet
from django.db.models.signals import post_save, pre_save
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.settings import api_settings
from rest_framework.validators import (
    BaseUniqueForValidator,
    UniqueTogetherValidator,
    UniqueValidator,
)

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.resolvers import (
    StepFailure,
    make_resolver_entries,
    run_write_pipeline_sync,
    save_or_field_errors,
)
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    is_dict,
    is_list,
    is_list_or_tuple,
    is_mapping,
    is_str,
    list_of,
    pk_of,
    read_attr,
    require,
)
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_INVALID,
    FIELD_ERROR_CODE_TRUNCATED,
    NON_FIELD_ERROR_KEY,
    UNBINDABLE_TEMPORAL_MESSAGE,
    FieldError,
    build_error_key_map,
    empty_validation_error,
    field_error,
    integrity_error_field_errors,
    join_error_path,
    null_field_error,
    rekey_error_segment,
    save_time_error_key_map,
    unstorable_value,
)
from django_strawberry_framework.utils.inputs import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    optional_input_field,
    published_input_specs,
)
from django_strawberry_framework.utils.permissions import request_from_info
from django_strawberry_framework.utils.querysets import (
    is_manager,
    linkable_rows,
    related_visibility_queryset,
    sync_pipeline_recourse,
)
from django_strawberry_framework.utils.relations import (
    is_model_class,
    written_model_field,
)
from django_strawberry_framework.utils.typing import call_forwarded
from django_strawberry_framework.utils.write_transaction import (
    base_locked_queryset,
    conflict_error,
    make_cross_alias_save_guard,
    pin_write_queryset,
    pinned_write_alias,
    pipeline_write_phase,
    pks_match,
    require_write_pipeline,
)
from django_strawberry_framework.utils.write_values import (
    attempted_saves,
    decode_field_handlers,
    decode_provided_fields,
    decode_visible_relation,
    decode_visible_relation_ids,
    decoded_into,
    refused_save,
    saves_rows_of,
    unstorable_columns,
)
from django_strawberry_framework.write_mixins import backing_model_of

from .accessors import (
    bound_fields,
    child_relation_of,
    is_drf_field,
    serializer_errors,
    validated_data_of,
)
from .hook_context import SerializerHookContext
from .inputs import (
    _is_serializer_class,
    raise_writable_source_ownership_errors,
    runtime_validated_data_fields,
    serializer_canonical_input_name,
    serializer_model,
)
from .serializer_converter import (
    NESTED_MULTI,
    NESTED_SINGLE,
    nested_serializer_child,
    resolve_serializer_field,
    serializer_field_fits_kind,
)
from .validator_guard import guard_uniqueness_validator

if TYPE_CHECKING:
    import datetime
    from collections.abc import Callable, Generator, Iterable, Iterator, Mapping, Sequence
    from typing import Protocol, TypeAlias

    from django.db import models
    from strawberry.types import Info

    from django_strawberry_framework.mutations.resolvers import (
        _AsyncResolverEntry,
        _SyncResolverEntry,
    )
    from django_strawberry_framework.utils.errors import ErrorKeyMap
    from django_strawberry_framework.utils.inputs import InputFieldSpec
    from django_strawberry_framework.utils.write_values import AttemptedSave

    from .serializer_converter import DRFField, DRFSerializer
    from .sets import SerializerMutation

    # One ``post_save`` witness record: (instance, pk at write, created, alias).
    _WrittenRow: TypeAlias = tuple[models.Model, object, bool, str | None]

    class _Saving(Protocol):
        """A bound serializer as far as ``save()`` goes: it returns what ``create()`` / ``update()`` did."""

        def save(self, **kwargs: object) -> object: ...

    class _DateTimeToInternal(Protocol):
        """A ``DateTimeField``'s ``to_internal_value``, as the overflow translation wraps it."""

        def __call__(self, value: datetime.datetime | str) -> datetime.datetime: ...

    class _ToInternal(Protocol):
        """A field's ``to_internal_value``, as the storability hold wraps it."""

        def __call__(self, data: object) -> object: ...

    class _Refuses(Protocol):
        """A storability rule: whether the alias ``using()`` names refuses a column's value."""

        def __call__(
            self,
            column: object,
            value: object,
            using: Callable[[], str],
            /,
        ) -> bool: ...

    class _RowSource(Protocol):
        """A validator's ``queryset``: a queryset or a manager, either of which ``all()`` re-reads."""

        def all(self) -> QuerySet[models.Model, object]: ...

    class _QuerysetValidator(Protocol):
        """A DRF validator that reads the database through a ``queryset`` (``UniqueValidator`` and kin)."""

        queryset: _RowSource

    #: Any model field, its set and get types unread.
    _FieldAny: TypeAlias = models.Field[object, object]
else:
    # ``Field`` has no ``__class_getitem__`` at runtime (only the ``django_stubs_ext``
    # patch adds one): the hint stays the class.
    _FieldAny = Field


#: One serializer's validators, kept in their own type through the queryset pinning.
_ValidatorT = TypeVar("_ValidatorT")


# The default ``truth.static_attr`` returns for an absent attribute, distinct from
# any value the attribute could hold.
class _Omitted(enum.Enum):
    """The absent-attribute default's type: one member, so an ``is _OMITTED`` test narrows it away."""

    OMITTED = enum.auto()


_OMITTED: Final = _Omitted.OMITTED

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) serializer pipeline. Mirrors the
# ``036`` / ``038`` recourse wording: the whole pipeline runs synchronously (under
# one ``sync_to_async`` worker on the async surface), so an ``async def
# get_queryset`` can never be awaited here. Single-sourced across the three write
# flavors via ``sync_pipeline_recourse``.
_SERIALIZER_ASYNC_RECOURSE = sync_pipeline_recourse("serializer mutation")


def _decode_relation_single(
    value: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    key_attname: str | None,
    info: Info[object, object],
) -> tuple[object, FieldError | None]:
    """Decode ONE relation id to its visible pk (mirrors the ``038`` form single decoder).

    The serializer coloring of the shared
    ``utils/write_values.py::decode_visible_relation`` spine:
    type-check + pk coercion -> visible object (a hidden / missing / wrong-model
    / uncoercible id is the uniform field-keyed ``FieldError``, no existence
    leak) -> the pk projection (what DRF's ``PrimaryKeyRelatedField`` expects). A
    visible row whose ``to_field`` key (``key_attname``) is ``NULL`` is the same relation
    error: the field would resolve it and the descriptor would store ``NULL``.

    An explicit ``None`` is NOT an id to decode: it is a clear / no-value skipped
    through unchanged so the serializer's own validation decides (a required
    relation raises its field-keyed required error via ``is_valid()``, an optional
    one clears). The generated GraphQL input field exposes only the one
    strategy-dependent shape (spec-039 Decision 7), and the decode reads which one from
    the target model, never from the value.
    """
    return decode_visible_relation(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
        info=info,
        async_recourse=_SERIALIZER_ASYNC_RECOURSE,
        skip=lambda candidate: candidate is None,
        project=pk_of,
        key_attname=key_attname,
    )


def _decode_relation_multi(
    values: object,
    *,
    graphql_name: str,
    related_model: type[models.Model],
    key_attname: str | None,
    info: Info[object, object],
) -> tuple[list[object] | None, FieldError | None]:
    """Decode an M2M ``list[<id>]`` to visible pks in ONE batched visibility query.

    Type-checks + coerces every element FIRST (no per-element DB fetch, short-circuiting on the
    first structurally-bad id), then confirms the whole set's visibility in ONE ``pk__in`` query
    via the shared ``decode_visible_relation_ids`` compose. A hidden / missing member collapses
    to the same field-keyed relation error (no existence leak), exactly as the per-element
    decode did. A visible member whose through-row key (``key_attname``) is ``NULL`` is the
    same error. An explicit ``None`` (the whole list) is passed through so the serializer's
    own required-ness decides; an empty list is a valid clear.
    """
    if values is None:
        return None, None
    return decode_visible_relation_ids(
        values,
        graphql_name=graphql_name,
        related_model=related_model,
        info=info,
        async_recourse=_SERIALIZER_ASYNC_RECOURSE,
        key_attname=key_attname,
        project=_visible_pk,
    )


def _visible_pk(pk: object, _key: object) -> object:
    """Answer the pk a ``PrimaryKeyRelatedField`` resolves, not the key the relation stores."""
    return pk


def _nested_specs_of(spec: InputFieldSpec) -> tuple[InputFieldSpec, ...]:
    """Return a nested kind's recorded nested reverse map.

    ``nested_specs`` is optional on the shared ``InputFieldSpec`` because only the
    serializer's ``nested_single`` / ``nested_multi`` kinds record one; a nested
    kind's spec always carries it, and a spec recording none raises ``TypeError``.
    """
    nested = spec.nested_specs
    if nested is None:
        raise TypeError(
            f"input field spec {spec.input_attr!r} ({spec.kind}) records no nested specs",
        )
    return nested


def _decode_input_object(
    specs: Iterable[InputFieldSpec],
    data: object,
    info: Info[object, object],
    *,
    path_prefix: str = "",
) -> tuple[dict[str, object], FieldError | None]:
    """Decode ONE strawberry input dataclass into a serializer-field-keyed dict.

    Walks the provided input fields (``UNSET`` stripped) and, using the per-field reverse map
    (``specs``, keyed by input attr), routes each value by ``kind`` to
    ``result[spec.target_name]`` (the DECLARED serializer field name DRF maps to ``source``
    internally):

    - ``SCALAR`` -> through the shared scalar leaf ``decode_scalar_leaf`` (the ``036`` /
      ``038`` text storability preflight + choice-enum unwrap).
    - ``RELATION_SINGLE`` / ``RELATION_MULTI`` -> the visibility-checked relation pk(s),
      type-checked against the relation's target model.
    - ``NESTED_SINGLE`` / ``NESTED_MULTI`` -> a RECURSIVELY-decoded nested dict / list of
      dicts, using the nested reverse map ``spec.nested_specs`` - so a nested relation is
      visibility-checked and a nested scalar text-preflighted exactly like a top-level one.
    - ``FILE`` -> the ``Upload`` value, routed into ``data`` like any other value (the
      deliberate DRF contrast with the form flavor's ``files=`` split).

    ``path_prefix`` is the dotted GraphQL path of the enclosing nested field (empty at the top),
    so a decode ``FieldError`` (a hidden relation id, invalid Unicode) is keyed to its FULL path
    (``shelves.0.altBranches``), not just the leaf name. Re-used recursively for nested items.
    A decode ``FieldError`` short-circuits (the shared skeleton maps it to a null payload).

    The reverse-map build + the ``UNSET``-strip walk + the kind dispatch are single-sited in
    ``utils/write_values.py::decode_provided_fields``; the SCALAR / RELATION / FILE
    store-into-dest handlers are the shared ``decode_field_handlers`` factories
    (FILE lands in ``data``, the deliberate DRF contrast with Django ``files=``).
    Nested recursion stays serializer-only via ``extra_handlers``.
    """
    if data is None:
        return {}, None
    if truth.static_attr(data, "__strawberry_definition__", _OMITTED) is _OMITTED:
        return {}, field_error(
            path_prefix or NON_FIELD_ERROR_KEY,
            "Invalid input object.",
            codes=FIELD_ERROR_CODE_INVALID,
        )
    provided_data: dict[str, object] = {}

    def _field_path(spec: InputFieldSpec) -> str:
        return join_error_path(path_prefix, spec.graphql_name)

    nested = decoded_into(
        provided_data,
        lambda spec, value: _decode_nested(spec, value, info, path_prefix=_field_path(spec)),
    )
    handlers, scalar_handler = decode_field_handlers(
        provided_data,
        info=info,
        single=_decode_relation_single,
        multi=_decode_relation_multi,
        field_name=_field_path,
        extra_handlers={NESTED_SINGLE: nested, NESTED_MULTI: nested},
    )
    error = decode_provided_fields(
        specs,
        data,
        handlers=handlers,
        scalar_handler=scalar_handler,
    )
    if error is not None:
        return {}, error
    return provided_data, None


def _decode_nested(
    spec: InputFieldSpec,
    value: object,
    info: Info[object, object],
    *,
    path_prefix: str,
) -> tuple[object, FieldError | None]:
    """Recursively decode a nested input value into nested serializer-keyed data.

    A single nested input dataclass -> one decoded dict (via ``_decode_input_object`` over
    ``spec.nested_specs``); a ``NESTED_MULTI`` list -> a list of decoded dicts, each keyed under
    its index in the path (``shelves.0`` / ``shelves.1``). An explicit ``None`` (a nested clear /
    omitted value that coerced to ``null``) passes through unchanged so the parent serializer's
    OWN validation decides (a required nested field raises its own field-keyed error via
    ``is_valid()``). A decode ``FieldError`` in any nested item short-circuits. The decoded nested
    data is handed to the parent serializer's ``create()`` / ``update()`` (which owns the write -
    the framework never auto-saves the nested relation).
    """
    if value is None:
        return None, None
    if spec.kind == NESTED_MULTI:
        try:
            items = list_of(value)
        except TypeError:
            return None, field_error(
                path_prefix,
                "Expected a list of items.",
                codes=FIELD_ERROR_CODE_INVALID,
            )
        decoded_items: list[dict[str, object] | None] = []
        for index, item in enumerate(items):
            item_path = join_error_path(path_prefix, str(index))
            if item is None:
                decoded_items.append(None)
                continue
            item_data, error = _decode_input_object(
                _nested_specs_of(spec),
                item,
                info,
                path_prefix=item_path,
            )
            if error is not None:
                return None, error
            decoded_items.append(item_data)
        return decoded_items, None
    item_data, error = _decode_input_object(
        _nested_specs_of(spec),
        value,
        info,
        path_prefix=path_prefix,
    )
    if error is not None:
        return None, error
    return item_data, None


def serializer_errors_to_field_errors(errors: object, key_map: ErrorKeyMap) -> list[FieldError]:
    """Depth-first flatten DRF nested ``serializer.errors`` into the ``FieldError`` envelope.

    The recursive analog of the flat ``036``
    ``utils/errors.py::validation_error_to_field_errors`` - both terminate in
    the SAME ``field_error`` leaf ctor, so the ``"__all__"`` sentinel
    + the message coercion cannot drift. DRF's ``serializer.errors`` (and a DRF
    ``ValidationError.detail``) is a nested structure of dicts (per-field), lists
    (indexed children / a field's message list), and leaf strings / ``ErrorDetail``s.
    This walks it depth-first, emitting one ``FieldError`` per leaf:

    - a **dict** recurses each key, joining the dotted path (``items.0.name``); each key is
      RE-KEYED to its GraphQL name AS IT DESCENDS (not only the root),
      using the RECURSIVE ``key_map``, so a nested child field / alias / relation suffix
      reports its GraphQL name (``shelves.0.altBranches``, not ``shelves.0.alt_branches``).
      DRF's ``non_field_errors`` key (``NON_FIELD_ERRORS_KEY`` = ``api_settings.NON_FIELD_ERRORS_KEY``,
      default ``"non_field_errors"``) normalizes to the ``"__all__"`` sentinel segment at THAT
      level - so a top-level bucket becomes the bare ``"__all__"`` and a nested one
      ``<path>.__all__``;
    - a **list of dicts/lists** recurses each child under its NUMERIC index (``items.0``),
      carrying the SAME level key map (the list items are the same nested serializer);
    - a **list of leaf messages** (the common ``{field: ["msg", ...]}`` shape) is ONE
      ``FieldError`` for the (already-re-keyed) path with the whole message list.

    ``key_map`` is the RECURSIVE key map from ``utils/errors.py::build_error_key_map`` -
    ``{serializer field name: (GraphQL input name, child_map | None)}`` - so each nesting level
    re-keys with its OWN field map. A segment with no entry (a numeric index, the ``"__all__"``
    sentinel, or a non-mapped field) is kept verbatim.

    **Iterative, cycle- and budget-aware**: the error structure mirrors a
    client-controlled input (a deeply-nested ``JSONField`` payload reproduces its nesting in
    ``serializer.errors`` / a DRF ``ValidationError.detail``), so a recursive walk would let a
    deep payload crash the pipeline with a ``RecursionError`` at the ERROR path - the exact
    availability hole the iterative clone already closes on the data path. The walk is an
    explicit stack; a CYCLIC detail structure (constructible only by author code raising a
    hand-built ``ValidationError``) fails loud as a ``ConfigurationError``; and a node budget
    caps pathological fan-out - when exceeded, the flattened list ends with one ``"__all__"``
    ``truncated`` marker instead of unbounded work.
    """
    children = _error_node_children(errors, key_map, "")
    if children is None:
        return [_error_leaf(errors, "")]
    flattened: list[FieldError] = []
    budget = _ERROR_FLATTEN_NODE_BUDGET
    active: set[int] = {id(errors)}
    frames: list[tuple[object, Iterator[tuple[object, ErrorKeyMap, str]]]] = [
        (errors, iter(children)),
    ]
    while frames:
        node, entries = frames[-1]
        descended = False
        for child, child_map, child_prefix in entries:
            budget -= 1
            if budget < 0:
                flattened.append(
                    field_error(
                        NON_FIELD_ERROR_KEY,
                        "Too many validation error details to report; the list was truncated.",
                        codes=FIELD_ERROR_CODE_TRUNCATED,
                    ),
                )
                return flattened
            grand = _error_node_children(child, child_map, child_prefix)
            if grand is None:
                flattened.append(_error_leaf(child, child_prefix))
                continue
            if id(child) in active:
                raise ConfigurationError(
                    "SerializerMutation validation errors contain a CYCLIC detail structure "
                    "(a dict or list that transitively contains itself); cyclic error details "
                    "cannot be flattened. Break the cycle in the raised ValidationError.",
                )
            active.add(id(child))
            frames.append((child, iter(grand)))
            descended = True
            break
        if not descended:
            active.discard(id(node))
            _ = frames.pop()
    if not flattened:
        return [empty_validation_error()]
    return flattened


# The flattener's node budget: far above any legitimate ``serializer.errors``
# shape (hundreds of fields x nested items), far below pathological fan-out. On
# exhaustion the flattened list ends with one ``"__all__"`` ``truncated`` marker.
_ERROR_FLATTEN_NODE_BUDGET = 10_000


def _error_node_children(
    errors: object,
    key_map: ErrorKeyMap,
    prefix: str,
) -> list[tuple[object, ErrorKeyMap, str]] | None:
    """Expand one error node into ``(child, child_map, child_prefix)`` entries, or ``None`` for a leaf.

    The single expansion rule the iterative flattener walks: a **dict** re-keys each key to its
    GraphQL name AS IT DESCENDS (not only the root) via the shared
    ``utils/errors.py::rekey_error_segment`` with the level's own key map, after normalizing
    DRF's non-field bucket to the ``"__all__"`` sentinel segment with no child map (the bucket key
    is read from ``api_settings.NON_FIELD_ERRORS_KEY`` per node, the way DRF's own
    ``as_serializer_error`` reads it, so a key DRF reloads on ``setting_changed`` is honoured);
    an ``int`` key is an item index, not a field name: DRF 3.18's ``ListSerializer`` reports
    its failing items as ``{index: errors}`` where 3.17's lists every item
    (``ListSerializer.to_internal_value``), so the index segment carries the SAME level map,
    as a list item does;
    a **list containing dicts / lists** indexes each child under its numeric position,
    carrying the SAME level map (the items are the same nested
    serializer; a mixed list never occurs in DRF's shape, but the guard keeps a stray leaf from
    dropping). Anything else - a list of leaf messages, a bare string, an ``ErrorDetail`` - is a
    leaf (``None``).
    """
    if is_dict(errors):
        error_map = errors
        drf_non_field_key = api_settings.NON_FIELD_ERRORS_KEY
        children: list[tuple[object, ErrorKeyMap, str]] = []
        for key, value in error_map.items():
            name = str(key)
            if isinstance(key, int):
                segment, child_map = name, key_map
            elif name == drf_non_field_key:
                segment, child_map = NON_FIELD_ERROR_KEY, {}
            else:
                segment, child_map = rekey_error_segment(name, key_map)
            children.append((value, child_map, join_error_path(prefix, segment)))
        return children
    if is_list(errors) and any(isinstance(item, (dict, list)) for item in errors):
        return [
            (item, key_map, join_error_path(prefix, str(index)))
            for index, item in enumerate(errors)
        ]
    return None


def _error_leaf(errors: object, prefix: str) -> FieldError:
    """Build the shared leaf for one flattened error path.

    A leaf is a list of messages, a bare string, or an ``ErrorDetail``; ``prefix`` is already
    fully re-keyed during descent, so the shared ``field_error`` ctor gets the dotted GraphQL
    path directly - preserving each DRF ``ErrorDetail.code`` alongside the message
    and the structured path (derived inside ``field_error`` from the dotted key).
    """
    leaf_codes = _error_detail_codes(errors)
    if (
        errors
        in (
            None,
            "",
            [],
            {},
        )
        and not leaf_codes
    ):
        return empty_validation_error(prefix)
    return field_error(
        prefix,
        errors,
        codes=leaf_codes,
    )


def _error_detail_codes(errors: object) -> list[str]:
    """Extract DRF ``ErrorDetail.code``s from a ``serializer.errors`` leaf.

    A DRF leaf is a list of ``ErrorDetail`` (a ``str`` subclass carrying ``.code``), or a
    bare ``ErrorDetail`` / plain string; the codes are read off each element's ``.code`` (a
    plain ``str`` has none -> dropped). Passed to the shared ``field_error`` leaf so the
    serializer envelope carries structured codes a client can branch on (``required`` /
    ``invalid`` / ``unique`` / ``blank`` / ...) without parsing localized human text.
    """
    if is_list_or_tuple(errors):
        return [code for code in (getattr(item, "code", None) for item in errors) if code]
    code = getattr(errors, "code", None)
    return [code] if code else []


def _injected_serializer_data(
    mutation_cls: type[SerializerMutation],
    info: Info[object, object],
    *,
    data: dict[str, object],
    hook_context: SerializerHookContext,
) -> dict[str, object]:
    """Collect the ``Meta.injected_fields`` values through ``get_serializer_injected_data``.

    The declared-injection half of the final serializer data: the framework builds the
    authoritative data itself from the DECODED client data plus this hook's return - a
    ``get_serializer_kwargs`` override cannot replace or extend ``data``. The hook receives
    a shallow copy of the decoded client data plus the frozen ``SerializerHookContext`` -
    never the live located instance - and its returned keys must EXACTLY match
    ``Meta.injected_fields``: a missing declared field would silently fail validation, an
    undeclared extra key would smuggle a value past the auditable contract - both are a
    loud ``ConfigurationError``. Class validation already guarantees an injected field is
    never also a GraphQL input field, so the merge can never overwrite a client value.
    """
    declared = frozenset(mutation_cls._mutation_meta.injected_fields or ())
    injected = dict(
        mutation_cls().get_serializer_injected_data(info, data=data, hook_context=hook_context),
    )
    if frozenset(injected) != declared:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}.get_serializer_injected_data returned "
            f"key(s) {sorted(injected)!r}, but Meta.injected_fields declares "
            f"{sorted(declared)!r}. The hook must supply EXACTLY the declared injected fields - "
            "declare every supplied field in Meta.injected_fields and supply every declared one.",
        )
    return injected


def _serializer_kwargs(
    mutation_cls: type[SerializerMutation],
    info: Info[object, object],
    *,
    final_data: dict[str, object],
    instance: models.Model | None,
    alias: str,
    hook_context: SerializerHookContext,
) -> dict[str, object]:
    """Construct the serializer kwargs through ``get_serializer_kwargs`` + the framework merge.

    Calls the overridable CONSTRUCTOR-ONLY hook ``get_serializer_kwargs(info,
    data=<copy>, hook_context=<frozen context>)`` (the spec-039 Decision 8 construction
    hook) with a shallow copy of the framework-built final data, then owns the framework
    rules:

    - ``data`` is the framework-built final data (decoded client data + declared
      injection); the returned ``data`` must be omitted or the exact copy the hook
      received, anything else (an explicit ``None`` included) is a ``ConfigurationError``.
    - ``instance`` and ``partial`` are framework-owned: either key in the return is a
      ``ConfigurationError``; the framework injects the located, authorized row and
      ``partial=True`` for an UPDATE, never for create.
    - the override's ``context`` is merged, then ``context["request"]`` is set to the
      framework request and ``context["write_alias"]`` to the pipeline's pinned write
      alias.
    """
    data = dict(final_data)
    kwargs = dict(mutation_cls().get_serializer_kwargs(info, data=data, hook_context=hook_context))
    for reserved in ("instance", "partial"):
        if reserved in kwargs:
            raise ConfigurationError(
                f"SerializerMutation {truth.name(mutation_cls)}.get_serializer_kwargs returned "
                f"a `{reserved}` kwarg; `instance` and `partial` are framework-owned (the "
                "framework injects the located, authorized row and partial=True for update, "
                f"never for create). Remove `{reserved}` from the override.",
            )
    if kwargs.pop("data", data) is not data:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}.get_serializer_kwargs returned a "
            "`data` value that is not the exact object the hook received; `data` is "
            "framework-owned (decoded client input plus Meta.injected_fields injection), so "
            "the hook must pass it through unchanged or omit it. Supply extra fields via "
            "get_serializer_injected_data + Meta.injected_fields, not by rewriting `data`.",
        )
    kwargs["data"] = final_data
    if instance is not None:
        kwargs["instance"] = instance
        kwargs["partial"] = True
    request = request_from_info(info, family_label="SerializerMutation")
    context = require(kwargs.get("context") or {}, is_mapping)
    kwargs["context"] = {**context, "request": request, "write_alias": alias}
    return kwargs


def _model_name_repr(model: object) -> str:
    """``repr`` of a relation target's class name, or of the value itself when it is no class."""
    return truth.render(truth.name(model) if truth.is_type(model) else model)


def _relation_queryset_of(field: DRFField) -> object:
    """Return the ``queryset`` a runtime relation field decodes against, or ``None``.

    A single ``PrimaryKeyRelatedField`` carries it directly; a ``ManyRelatedField`` carries
    it on ``field.child_relation``. Read as an ``object``: the schema/runtime agreement guard
    is what proves its shape.
    """
    related = (
        child_relation_of(field) if isinstance(field, serializers.ManyRelatedField) else field
    )
    return read_attr(related, "queryset", None)


def _relation_model_of(field: DRFField) -> object:
    """Return the target model a runtime relation field decodes against, or ``None``.

    A single ``PrimaryKeyRelatedField`` carries ``field.queryset.model``; a
    ``ManyRelatedField`` carries it on ``field.child_relation.queryset``. Used by the
    schema/runtime agreement guard to confirm the runtime relation still points at the same
    model the schema-time ``InputFieldSpec.related_model`` recorded.
    """
    return getattr(_relation_queryset_of(field), "model", None)


def _assert_schema_runtime_agreement(
    mutation_cls: type[SerializerMutation],
    serializer: DRFSerializer,
) -> None:
    """Raise ``ConfigurationError`` if runtime disagrees with the schema write surface.

    The schema-time field map (the ``get_serializer_for_schema()`` hook) drives the generated
    GraphQL input + the bind-stashed reverse map (``mutation_cls._input_field_specs``); the
    runtime write uses the REAL ``serializer_class``. If they diverge, DRF would silently
    ignore an incoming key the GraphQL schema implied is writable. This turns the hook
    into a VERIFIED contract: for every write-surface field spec (GraphQL input +
    ``Meta.injected_fields`` - one walk via ``_write_surface_specs``), the runtime
    ``serializer.fields`` must

    - contain ``spec.target_name`` and have it WRITABLE (not ``read_only``);
    - bind the SAME ``source`` the schema-time discovery recorded;
    - for a relation, still be a ``PrimaryKeyRelatedField`` (single) / ``ManyRelatedField`` of
      a ``PrimaryKeyRelatedField`` (multi) over the SAME ``related_model``;
    - for a file / scalar, keep a compatible kind (a scalar that moved to a relation or file,
      or vice versa, is a mismatch).

    Injected fields ride the SAME per-field check: presence of an injected value is
    guaranteed by construction, but the runtime serializer must still declare each injected
    field writable with the recorded source / kind / relation-model, or DRF drops it.

    Runs BEFORE ``is_valid()`` so a schema/runtime mismatch is a framework configuration
    failure (a clear ``ConfigurationError`` at the boundary), never a serializer-validation
    ambiguity. A runtime serializer with EXTRA fields the schema map omits is fine (they are
    simply never provided); only the write-surface fields are held to the contract.
    """
    for spec in _write_surface_specs(mutation_cls):
        _assert_field_agreement(mutation_cls, serializer, spec)


def _assert_runtime_write_source_ownership(
    mutation_cls: type[SerializerMutation],
    serializer: DRFSerializer,
    data: Mapping[str, object],
    specs: Iterable[InputFieldSpec],
    *,
    path: str = "",
) -> None:
    """Reject runtime fields that can overwrite one another in ``validated_data``.

    Schema discovery cannot see context-dependent fields returned by ``get_fields()``. Walk the
    instantiated serializer immediately before validation, including every explicitly opted-in
    nested serializer, so hidden/defaulted runtime fields cannot silently replace client or
    injected values through DRF's last-write-wins source assignment. Sources are keyed by the
    model field they resolve to on the serializer's own ``Meta.model``, so a runtime
    ``source="category_id"`` collides with a client ``category``.
    """
    supplied_fields = set(data)
    runtime_fields = runtime_validated_data_fields(
        bound_fields(serializer),
        supplied_fields=supplied_fields,
        apply_defaults=mutation_cls._mutation_meta.operation == "create",
    )
    runtime_sources = {field_name: field.source for field_name, field in runtime_fields.items()}
    raise_writable_source_ownership_errors(
        truth.name(mutation_cls),
        runtime_sources,
        location=f"runtime serializer path {(path or '<root>')!r}",
        model=serializer_model(type(serializer)),
    )

    for spec in specs:
        if spec.kind not in (NESTED_SINGLE, NESTED_MULTI):
            continue
        runtime: DRFField = bound_fields(serializer)[spec.target_name]
        child_serializer, many = nested_serializer_child(runtime)
        raw_child = data.get(spec.target_name)
        child_values = raw_child if many and is_list_or_tuple(raw_child) else [raw_child]
        # A nested input's keys are its serializer field names; a key that is not a
        # string names no field, so it can neither supply one nor collide with one.
        child_data: dict[str, object] = {
            key: item
            for value in child_values
            if is_mapping(value)
            for key, item in value.items()
            if isinstance(key, str)
        }
        child_path = f"{path}.{spec.target_name}" if path else spec.target_name
        _assert_runtime_write_source_ownership(
            mutation_cls,
            child_serializer,
            child_data,
            list(_nested_specs_of(spec)),
            path=child_path,
        )


def _assert_field_agreement(
    mutation_cls: type[SerializerMutation],
    serializer: DRFSerializer,
    spec: InputFieldSpec,
    *,
    nested_path: tuple[str, ...] = (),
) -> None:
    """Assert ONE schema-time field spec agrees with the runtime serializer.

    The per-field body of ``_assert_schema_runtime_agreement`` (which walks the one
    ``_write_surface_specs`` list covering GraphQL input + ``Meta.injected_fields``): the
    runtime ``serializer.fields`` must contain ``spec.target_name``, have it WRITABLE, bind
    the SAME ``source``, keep a relation as a ``PrimaryKeyRelatedField`` /
    ``ManyRelatedField(PrimaryKeyRelatedField)`` over the SAME ``related_model``, and keep a
    file / scalar kind compatible (``serializer_field_fits_kind``, the reading the schema
    build refuses a kind mismatch by). Any divergence is a framework ``ConfigurationError`` at
    the boundary. ``nested_path`` locates this serializer level's normalized
    configuration, so nested model resolution and optionality do not inherit the
    root mutation's settings.
    """
    runtime_fields = bound_fields(serializer)
    name = truth.name(type(serializer))
    target = spec.target_name
    runtime: DRFField | None = runtime_fields.get(target)
    if runtime is None:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: the schema exposes field "
            f"{target!r}, but the runtime serializer {name} does not declare it. DRF would "
            "silently ignore the incoming value. Make get_serializer_for_schema() and the "
            "runtime serializer_class agree (declare the field on the serializer, or drop it "
            "from the schema field map).",
        )
    if runtime.read_only:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: the schema exposes writable field "
            f"{target!r}, but the runtime serializer {name} declares it read_only; the "
            "incoming value would be ignored. Make the runtime field writable or drop it "
            "from the schema field map.",
        )
    schema_source = spec.source or target
    runtime_source = runtime.source or target
    if runtime_source != schema_source:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: field {target!r} binds source "
            f"{runtime_source!r} at runtime but {schema_source!r} in the schema field map; "
            "the write would target a different attribute than the schema implies. Align "
            "the runtime serializer's source with get_serializer_for_schema().",
        )
    if spec.kind in (RELATION_SINGLE, RELATION_MULTI):
        _assert_relation_agreement(mutation_cls, spec, runtime)
    elif spec.kind in (NESTED_SINGLE, NESTED_MULTI):
        _assert_nested_agreement(
            mutation_cls,
            spec,
            runtime,
            nested_path=(*nested_path, spec.target_name),
        )
    elif spec.kind == FILE:
        if not serializer_field_fits_kind(runtime, FILE):
            raise ConfigurationError(
                f"SerializerMutation {truth.name(mutation_cls)}: field {target!r} is a file input "
                f"in the schema but {truth.name(type(runtime))} at runtime; the kind moved. Align "
                "the runtime serializer field with get_serializer_for_schema().",
            )
    elif not serializer_field_fits_kind(runtime, SCALAR):
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: field {target!r} is a scalar in the "
            f"schema but a relation / file / nested serializer ({truth.name(type(runtime))}) at "
            "runtime; the kind moved. Align the runtime serializer field with "
            "get_serializer_for_schema().",
        )
    if spec.required is None and spec.annotation_repr is None:
        return
    # Both incoherent spellings - the attribute missing and the attribute ``None`` (an
    # abstract base) - normalize to one rejection: with no validated snapshot the
    # requiredness / annotation answer is undeterminable, so it leaves the permit path
    # instead of being coerced onto it. Every bound mutation carries the snapshot; the guard
    # reads only the three attributes it compares, so any object carrying them answers.
    meta = truth.static_attr(mutation_cls, "_mutation_meta")
    if meta is None:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: field {target!r} carries a schema "
            "requiredness or annotation contract, but the mutation has no validated Meta "
            "snapshot, so agreement with the runtime field cannot be determined. A bound "
            "mutation always carries one; reaching this guard without it is a framework "
            "invariant violation, not a supported configuration.",
        )
    operation = read_attr(meta, "operation")
    level_meta = meta
    for name in nested_path:
        level_meta = require(read_attr(level_meta, "nested_fields"), is_mapping)[name]
    declared_optional = read_attr(level_meta, "optional_fields")
    optional_fields = frozenset(list_of(declared_optional) if declared_optional else ())
    runtime_required = (
        False
        if operation == "update"
        else bool(
            runtime.required and target not in optional_fields,
        )
    )
    if spec.required is not None and runtime_required != spec.required:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: field {target!r} is "
            f"{'required' if runtime_required else 'optional'} at runtime but "
            f"{'required' if spec.required else 'optional'} in the schema input. Align "
            "the runtime serializer's required/default declaration with "
            "get_serializer_for_schema().",
        )
    if spec.annotation_repr is None:
        return
    if spec.kind in (NESTED_SINGLE, NESTED_MULTI):
        # An opted-in nested field's annotation is the RECURSIVELY generated nested
        # input type, which ``resolve_serializer_field`` cannot re-derive: it rejects
        # every nested serializer by contract (nesting is opt-in only, and the input
        # build routes an opted-in field to the recursive nested build instead of the
        # flat converter). ``_assert_nested_agreement`` already held this field to the
        # schema's nested shape and recursed into every child spec - each child's own
        # annotation is checked there - so the container's annotation is covered by
        # that walk plus the requiredness check above.
        return
    snapshot_model = (
        serializer_model(type(serializer)) if nested_path else read_attr(meta, "model")
    )
    try:
        _python_attr, runtime_annotation, _runtime_spec = resolve_serializer_field(
            runtime,
            None if snapshot_model is None else require(snapshot_model, is_model_class),
            serializer_canonical_input_name(type(serializer), is_partial=operation == "update"),
        )
        runtime_annotation, _field_kwargs = optional_input_field(
            runtime_annotation,
            widen=(
                bool(runtime.allow_null or not runtime_required)
                if spec.required is not None
                else False
            ),
        )
    except ConfigurationError as exc:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: runtime field {target!r} "
            "could not be resolved to the schema's generated input annotation; align "
            "the runtime serializer with get_serializer_for_schema().",
        ) from exc
    if repr(runtime_annotation) != spec.annotation_repr:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: runtime field {target!r} "
            f"resolves to annotation {runtime_annotation!r}, but the schema input "
            f"resolves to {spec.annotation_repr}; align the runtime serializer field "
            "with get_serializer_for_schema().",
        )


def _assert_relation_agreement(
    mutation_cls: type[SerializerMutation],
    spec: InputFieldSpec,
    runtime: DRFField,
) -> None:
    """Confirm a runtime relation field matches the schema-time relation spec (helper).

    A ``RELATION_SINGLE`` spec requires a runtime ``PrimaryKeyRelatedField``; a
    ``RELATION_MULTI`` spec requires a ``ManyRelatedField`` wrapping a ``PrimaryKeyRelatedField``
    (the only pk-decoding shapes). Either way the runtime relation must point at
    the SAME ``related_model`` the schema-time ``InputFieldSpec`` recorded, so the id decoded
    against the schema target is the id the runtime field validates against.
    """
    if spec.kind == RELATION_SINGLE:
        ok_shape = isinstance(runtime, serializers.PrimaryKeyRelatedField)
    else:
        ok_shape = isinstance(runtime, serializers.ManyRelatedField) and isinstance(
            child_relation_of(runtime),
            serializers.PrimaryKeyRelatedField,
        )
    if not ok_shape:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: relation field {spec.target_name!r} is "
            f"{truth.name(type(runtime))} at runtime, but the schema types it as a primary-key "
            "relation; only PrimaryKeyRelatedField (single) / PrimaryKeyRelatedField(many=True) "
            "decode a pk. Align the runtime serializer field with get_serializer_for_schema().",
        )
    runtime_model = _relation_model_of(runtime)
    if runtime_model is not spec.related_model:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: relation field {spec.target_name!r} "
            f"targets {_model_name_repr(runtime_model)} at runtime but "
            f"{_model_name_repr(spec.related_model)} in the schema field "
            "map; the decoded id would be validated against a different model. Align the runtime "
            "relation's queryset with get_serializer_for_schema().",
        )
    runtime_queryset = _relation_queryset_of(runtime)
    if not (is_manager(runtime_queryset) or isinstance(runtime_queryset, QuerySet)):
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: relation field {spec.target_name!r} "
            f"holds a {truth.name(type(runtime_queryset))!r} queryset at runtime, but the schema "
            "types it as a primary-key relation, which looks its id up in a QuerySet or a "
            "Manager. Align the runtime relation's queryset with get_serializer_for_schema().",
        )


def _assert_nested_agreement(
    mutation_cls: type[SerializerMutation],
    spec: InputFieldSpec,
    runtime: DRFField,
    *,
    nested_path: tuple[str, ...],
) -> None:
    """Confirm a runtime nested serializer field matches the schema-time nested spec.

    A ``NESTED_MULTI`` spec requires a runtime ``ListSerializer`` (a ``many=True`` nested
    serializer); a ``NESTED_SINGLE`` spec requires a plain nested ``Serializer`` (a
    ``BaseSerializer`` that is NOT a ``ListSerializer``). Then the agreement RECURSES: each
    schema-time nested field spec (``spec.nested_specs``) is held to the SAME present / writable /
    source / kind / relation-model / deeper-nested contract against the runtime nested
    serializer's own fields - so a nested shape that drifted between the schema-time hook and the
    runtime serializer is a clear ``ConfigurationError`` at the boundary, at every depth.
    """
    if spec.kind == NESTED_MULTI:
        ok_shape = isinstance(runtime, serializers.ListSerializer)
    else:
        ok_shape = isinstance(runtime, serializers.BaseSerializer) and not isinstance(
            runtime,
            serializers.ListSerializer,
        )
    if not ok_shape:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: nested field {spec.target_name!r} is "
            f"{truth.name(type(runtime))} at runtime, but the schema types it as a nested "
            f"{'list of serializers' if spec.kind == NESTED_MULTI else 'serializer'}. Align the "
            "runtime serializer field with get_serializer_for_schema().",
        )
    child_serializer, _many = nested_serializer_child(runtime)
    for child_spec in _nested_specs_of(spec):
        _assert_field_agreement(
            mutation_cls,
            child_serializer,
            child_spec,
            nested_path=nested_path,
        )


def _scope_relation_querysets_to_visibility(
    mutation_cls: type[SerializerMutation],
    serializer: DRFSerializer,
    info: Info[object, object],
) -> None:
    """Intersect each runtime relation field's queryset WITH the visibility queryset.

    For every relation the schema recorded (``_input_field_specs`` AND the
    ``Meta.injected_fields`` specs, ``_injected_field_specs``), narrow the runtime
    serializer field's ``queryset`` (``PrimaryKeyRelatedField``) / ``child_relation.queryset``
    (``ManyRelatedField``) to ``original.filter(pk__in=<visibility queryset>)`` - the author's
    OWN queryset restriction AND-ed with the related primary ``DjangoType``'s visibility-scoped
    ``get_queryset``. Visibility is an ADDITIONAL constraint, never a replacement:
    reassigning the field queryset would erase a serializer author's intentional
    ``PrimaryKeyRelatedField(queryset=Branch.objects.filter(city="allowed"))`` and could
    admit a visible-but-serializer-disallowed row. Composing preserves the author's
    contract while still ensuring DRF's own ``is_valid()`` lookup can never re-fetch a row the
    visibility check hid (a single ``pk__in`` subquery - no extra round trip). A relation whose
    target has no registered primary (a raw-pk relation with no visibility contract) keeps the
    author's own restriction but is STILL pinned to the write alias (and locked when the
    operation locks). The agreement guard already ran, so every relation spec has a matching
    writable runtime field over the recorded model (with a non-``None`` queryset).
    The rewrite is deliberately applied to ``serializer.fields``, whose declared fields DRF
    deep-copies for each serializer instance, never to the serializer class's shared
    ``_declared_fields``. Concurrent requests therefore receive independently scoped relation
    fields. The synchronized regression
    ``tests/rest_framework/test_resolvers.py::test_relation_queryset_scope_is_isolated_between_concurrent_serializer_instances``
    pins that DRF instance-isolation contract with requests carrying different visibility scopes.

    **Nested recursion.** A nested serializer field's OWN relation fields are scoped
    too, by recursing into the runtime nested serializer's ``.fields`` with the nested reverse
    map (``spec.nested_specs``) - so DRF's nested ``is_valid()`` lookup is the visibility lookup
    at every depth, the same defense-in-depth the top level gets.
    """
    # Injected fields (``Meta.injected_fields``) are relation-capable too: their values reach
    # DRF's SAME second lookup, so their querysets need the SAME pin + visibility + lock
    # discipline as the GraphQL-input relations (the specs are disjoint by class validation).
    _scope_specs_over_serializer(_write_surface_specs(mutation_cls), serializer, info)


def _reads_a_queryset(validator: object) -> TypeGuard[_QuerysetValidator]:
    """Whether ``validator`` holds a ``queryset`` it reads during ``is_valid()``.

    ``TypeGuard``: a held ``queryset`` is read as a row source without checking its
    shape, and a validator holding none says nothing about its type.
    """
    return read_attr(validator, "queryset", None) is not None


def _validation_tree(serializer: DRFField, *, path: str = "") -> Iterator[tuple[DRFField, str]]:
    """Yield every serializer and field instance ``serializer.is_valid()`` validates through.

    Each node comes with the owner label naming it (the innermost serializer class and the
    dotted path from the root). A serializer is yielded before its bound fields, a field
    before what it validates through: a ``ListSerializer`` field's ``child`` serializer, a
    nested serializer's own fields, a field's ``child`` (``ListField`` / ``DictField``) and
    ``child_relation`` (a many relation). A nested serializer field is yielded both as its
    parent's field and as the root of its own level. These are the per-request instances DRF
    deep-copies from the declared fields, never shared class state.
    """
    serializer_name = truth.name(type(serializer))
    yield serializer, f"{serializer_name}{f'.{path}' if path else ''}"
    if not isinstance(serializer, serializers.Serializer):
        # A plain ``BaseSerializer`` (a read-only ``source="*"`` renderer, a list
        # child) declares no ``fields``.
        return

    def _field_nodes(field: DRFField, field_path: str) -> Iterator[tuple[DRFField, str]]:
        yield field, f"{serializer_name}.{field_path}"
        if isinstance(field, serializers.ListSerializer):
            # ``ListSerializer.__init__`` asserts a ``child``; drf-stubs keep the class-level None.
            yield from _validation_tree(
                require(read_attr(field, "child"), is_drf_field),
                path=field_path,
            )
            return
        if isinstance(field, serializers.BaseSerializer):
            yield from _validation_tree(field, path=field_path)
            return
        child: object = getattr(field, "child", None)
        if is_drf_field(child):
            yield from _field_nodes(child, f"{field_path}.child")
        child_relation: object = getattr(field, "child_relation", None)
        if is_drf_field(child_relation):
            yield from _field_nodes(child_relation, f"{field_path}.child_relation")

    for field_name, field in bound_fields(serializer).items():
        yield from _field_nodes(field, f"{path}.{field_name}" if path else field_name)


def _pin_validator_querysets(serializer: DRFField, alias: str) -> None:
    """Pin every queryset-backed DRF validator in ``serializer``'s validation tree to the write alias.

    DRF uniqueness validators perform database reads during ``is_valid()``. Field
    ``UniqueValidator`` instances, serializer-level unique-together/date validators,
    and their nested-serializer counterparts must therefore share the transaction's
    alias. DRF intentionally shares validator objects while copying serializer fields,
    so every queryset-backed validator is shallow-copied and replaced on its serializer
    or field instance (``_validation_tree``) before its queryset is pinned. Filters and
    validator semantics remain intact, while concurrent requests cannot rewrite one
    another's validator routing.
    """

    def _pinned(validators: Iterable[_ValidatorT], owner: str) -> list[_ValidatorT]:
        pinned: list[_ValidatorT] = []
        for validator in validators:
            if not _reads_a_queryset(validator):
                pinned.append(validator)
                continue
            queryset = validator.queryset
            local_validator = copy.copy(validator)
            local_validator.queryset = pin_write_queryset(
                queryset.all(),
                alias,
                owner=f"{owner} {truth.kind(validator)} queryset",
            )
            pinned.append(local_validator)
        return pinned

    for node, owner in _validation_tree(serializer):
        node.validators = _pinned(node.validators, owner)


def _translate_datetime_overflow(serializer: DRFSerializer) -> None:
    """Answer DRF's own ``overflow`` error where a ``DateTimeField`` raises a raw ``OverflowError``.

    ``DateTimeField.enforce_timezone`` turns an ``OverflowError`` into its ``overflow``
    error only when it projects an aware value onto the field's time zone; the same
    overflow raised placing a naive value in a non-UTC current time zone (DRF's
    ``valid_datetime`` check) or projecting an aware one onto UTC under ``USE_TZ = False``
    (``timezone.make_naive``) escapes ``is_valid()`` raw. Every ``DateTimeField``
    instance (subclasses included) in the validation tree (``_validation_tree``) gets its
    current ``to_internal_value`` wrapped on the instance, so the field fails with the
    error DRF gives the sibling value, keyed to it at any depth; a ``to_internal_value``
    override that handles the ``OverflowError`` itself never lets one reach the wrapper.
    """
    for node, _owner in _validation_tree(serializer):
        if isinstance(node, serializers.DateTimeField):
            node.to_internal_value = _overflow_failing(node, node.to_internal_value)


def _written_columns(
    serializer: DRFSerializer,
    model: type[models.Model],
) -> dict[str, tuple[DRFField, _FieldAny]]:
    """Map each writable bound field whose ``source`` names a concrete column to the column.

    The source is a top-level ``validated_data`` key DRF assigns onto the instance
    (``utils/relations.py::written_model_field``); a ``read_only`` field and one naming no
    concrete column of ``model`` write nothing the storability rule reads.
    """
    columns: dict[str, tuple[DRFField, _FieldAny]] = {}
    for name, field in bound_fields(serializer).items():
        if field.read_only:
            continue
        column = written_model_field(model, field.source or name)
        if column is not None:
            columns[name] = (field, column)
    return columns


def _hold_unstorable_values(serializer: DRFSerializer, model: type[models.Model]) -> None:
    """Guard each actual uniqueness query and each root writable field's conversion.

    A field or serializer validator at any nested level retains DRF's own call order,
    default handling and query reachability. Its per-instance Query guard intercepts
    Django's eager lookup preparation and the one compiler execution the validator
    chooses. Root save storability is separate: only writable concrete columns are
    held here and in ``_unstorable_value_errors`` after validation; DRF's read-only
    defaults enter validator attrs but never become root writes by sharing a source.
    """
    written = _written_columns(serializer, model)
    held: set[int] = set()
    for node, _owner in _validation_tree(serializer):
        # A nested serializer is yielded as its parent's field and as its own level's root.
        if not isinstance(node, serializers.Serializer) or id(node) in held:
            continue
        held.add(id(node))
        _hold_serializer_values(node, written if node is serializer else {})


def _hold_serializer_values(
    serializer: DRFSerializer,
    written: Mapping[str, tuple[DRFField, _FieldAny]],
) -> None:
    """Hold real root writes and guard each uniqueness validator in DRF's own order.

    The writable field's conversion is checked against its save column. Read-only
    defaults are absent from that write path: DRF adds them only to its separate
    validator mapping. Each validator's copied, pinned queryset is guarded at its
    actual filter/exists calls, after defaults and earlier validators have run.
    """
    for name, field in bound_fields(serializer).items():
        entry = written.get(name)
        if entry is not None:
            field.to_internal_value = _storability_failing(
                entry[1],
                field.to_internal_value,
                unstorable_value,
            )
        # A nested Serializer owns its serializer-level validators. It appears here
        # as a parent field and is visited again as its own validation-tree node.
        if not field.read_only and not isinstance(field, serializers.Serializer):
            field.validators = [
                guard_uniqueness_validator(
                    validator,
                    alias=pinned_write_alias(),
                    field_name=None,
                    # DRF UniqueValidator queries the bound source's final
                    # attribute, even when the field writes a nested attrs path.
                    sources={name: field.source_attrs[-1]} if field.source_attrs else {},
                )
                if isinstance(validator, UniqueValidator)
                else validator
                for validator in field.validators
            ]
    fields = bound_fields(serializer)

    def _guard_serializer_validator(validator: _ValidatorT) -> _ValidatorT:
        if isinstance(validator, UniqueTogetherValidator):
            checked_names = list(validator.fields)
            names = [
                *checked_names,
                *(
                    name
                    for name in list_of(read_attr(validator, "condition_fields", ()))
                    if is_str(name)
                ),
            ]
            field_name = checked_names[0] if checked_names else ""
            sources = {name: fields[name].source or name for name in names if name in fields}
        elif isinstance(validator, BaseUniqueForValidator):
            # The date field's year bound is client data the query compiles too.
            names = [validator.field, validator.date_field]
            field_name = validator.field
            # BaseUniqueForValidator.__call__ uses source_attrs[-1], whereas
            # UniqueTogetherValidator.filter_queryset uses the complete source.
            sources = {
                name: fields[name].source_attrs[-1]
                for name in names
                if name in fields and fields[name].source_attrs
            }
        else:
            return validator
        return guard_uniqueness_validator(
            validator,
            alias=pinned_write_alias(),
            field_name=field_name,
            sources=sources,
        )

    serializer.validators = [
        _guard_serializer_validator(validator) for validator in serializer.validators
    ]


def _storability_failing(
    column: _FieldAny,
    original: _ToInternal,
    refuses: _Refuses,
) -> _ToInternal:
    """Fail a converted root writable value the pinned alias cannot save to ``column``."""

    def _to_internal_value(data: object) -> object:
        value = original(data)
        if refuses(column, value, pinned_write_alias):
            raise DRFValidationError(UNBINDABLE_TEMPORAL_MESSAGE, code=FIELD_ERROR_CODE_INVALID)
        return value

    return _to_internal_value


def _unstorable_written_values(
    columns: Mapping[str, tuple[DRFField, _FieldAny]],
    values: object,
    refuses: _Refuses,
) -> dict[str, list[ErrorDetail]]:
    """Map each field of ``columns`` whose value in ``values`` ``refuses`` refuses for its column.

    ``values`` is the serializer's final ``validated_data``, keyed by each writable
    field's ``source`` and asked on the pinned alias after ``is_valid()``. A refused field answers the
    ``invalid`` ``UNBINDABLE_TEMPORAL_MESSAGE`` ``ErrorDetail`` under its field name, the
    shape ``serializer.errors`` carries. A value that is no mapping (what a
    ``to_internal_value`` or ``validate()`` override returns in its place, which DRF passes
    on and its own ``save()`` refuses) holds no column value to read.
    """
    if not is_mapping(values):
        return {}
    return {
        name: [ErrorDetail(UNBINDABLE_TEMPORAL_MESSAGE, code=FIELD_ERROR_CODE_INVALID)]
        for name, (field, column) in columns.items()
        if (source := field.source or name) in values
        and refuses(column, values[source], pinned_write_alias)
    }


def _overflow_failing(
    field: serializers.DateTimeField,
    original: _DateTimeToInternal,
) -> _DateTimeToInternal:
    """Return ``original`` wrapped to fail ``field`` with ``overflow`` on a raw ``OverflowError``."""

    def _to_internal_value(value: datetime.datetime | str) -> datetime.datetime:
        try:
            return original(value)
        except OverflowError:
            field.fail("overflow")

    return _to_internal_value


def _scope_specs_over_serializer(
    specs: Iterable[InputFieldSpec],
    serializer: DRFSerializer,
    info: Info[object, object],
) -> None:
    """Scope one serializer's relation-field querysets to visibility, recursing into nested.

    The per-serializer body of ``_scope_relation_querysets_to_visibility``, factored out so it
    serves both the top-level input specs and each nested serializer's specs. A relation field's
    final queryset is **author queryset AND target visibility, pinned to the write alias, and
    locked when ``Meta.select_for_update`` locks**:

    - the author's queryset (an intentional ``PrimaryKeyRelatedField(queryset=...)``
      restriction) stays the base contract, PINNED to the pipeline's write alias - an author
      queryset EXPLICITLY routed to a different alias (``.using("other")``) fails closed
      BEFORE validation (``pin_write_queryset``), never a lookup outside the transaction;
    - the related primary type's visibility queryset is AND-ed on as a ``pk__in`` subquery
      (never a replacement); a raw-pk relation with no registered primary has no visibility
      contract but is STILL pinned (and locked) - DRF's own ``is_valid()`` lookup must run
      inside the same transaction on the same alias regardless;
    - when the operation locks, the composed queryset is reduced to a pk subquery under a
      base-manager ``SELECT ... FOR UPDATE`` (``base_locked_queryset`` - never
      ``select_for_update()`` on the author's arbitrary queryset shape), so the row DRF's
      second relation lookup confirms cannot be deleted out from under the write.

    A relation keyed by a ``to_field`` (``spec.key_attname``) admits only the rows whose
    key is not ``NULL`` (``utils/querysets.py::linkable_rows``), the set the decode admits.

    A nested field recurses into the runtime nested serializer's own fields with the nested
    reverse map, so every depth gets the same pin + visibility + lock discipline.
    """
    pipeline = require_write_pipeline()
    for spec in specs:
        if spec.kind in (NESTED_SINGLE, NESTED_MULTI):
            nested_field: DRFField | None = bound_fields(serializer).get(spec.target_name)
            if nested_field is None:  # pragma: no cover - the agreement guard already required it.
                continue
            child_serializer, _many = nested_serializer_child(nested_field)
            _scope_specs_over_serializer(
                _nested_specs_of(spec),
                child_serializer,
                info,
            )
            continue
        if spec.kind not in (RELATION_SINGLE, RELATION_MULTI):
            continue
        field: DRFField | None = bound_fields(serializer).get(spec.target_name)
        if field is None:  # pragma: no cover - the agreement guard already required it.
            continue
        # The agreement guard proved a relation spec's runtime field is a
        # PrimaryKeyRelatedField, or a ManyRelatedField over one.
        relation = cast(
            "serializers.PrimaryKeyRelatedField[models.Model]",
            child_relation_of(field) if isinstance(field, serializers.ManyRelatedField) else field,
        )
        # ``.all()`` normalizes a Manager to a QuerySet (preserving an explicit ``.using``);
        # the pin fails closed on a cross-alias author queryset BEFORE any validation runs.
        # The schema/runtime agreement guard already rejected a relation whose queryset
        # is neither a QuerySet nor a Manager over the recorded model; the assert only
        # narrows what the guard proved.
        author_queryset = read_attr(relation, "queryset")
        assert is_manager(author_queryset) or isinstance(author_queryset, QuerySet)  # noqa: S101 - _assert_relation_agreement already rejected any other queryset
        scoped = pin_write_queryset(
            author_queryset.all(),
            pipeline.alias,
            owner=(f"{truth.name(type(serializer))}.{spec.target_name} relation queryset"),
        )
        # ``related_visibility_queryset`` single-sites the ``registry.get`` resolve +
        # the visibility-scoping call; ``None`` = raw-pk relation with
        # no primary type (no visibility contract to AND on - the pin + lock still apply).
        visible = related_visibility_queryset(
            # A relation spec always records its target model.
            require(spec.related_model, is_model_class),
            info,
            _SERIALIZER_ASYNC_RECOURSE,
        )
        if visible is not None:
            # Compose (AND), not replace: keep the author's queryset as the base contract and
            # add visibility as a pk__in constraint (a subquery, so still one lookup per field).
            scoped = scoped.filter(
                pk__in=pin_write_queryset(visible, pipeline.alias).values("pk"),
            )
        if pipeline.lock:
            scoped = base_locked_queryset(
                require(spec.related_model, is_model_class),
                pipeline.alias,
                scoped,
            )
        # DRF's lookup admits only the rows the decode does: a ``NULL`` ``to_field`` key
        # names no row, for a decoded and an injected value alike.
        scoped = linkable_rows(scoped, spec.key_attname)
        # basedpyright: drf-stubs types the slot's rows as the model; isinstance proves a QuerySet,
        # not its row type (a ``.values()`` queryset passes it)
        relation.queryset = scoped  # pyright: ignore[reportAttributeAccessIssue]


def _write_surface_specs(mutation_cls: type[SerializerMutation]) -> list[InputFieldSpec]:
    """Return the top-level write-surface specs: GraphQL input fields + ``Meta.injected_fields``.

    The one list every top-level per-field discipline walks (schema/runtime agreement,
    write-source ownership, queryset scoping): the two spec sets are disjoint by class
    validation, so concatenation is exact.
    """
    return [*mutation_cls._input_field_specs, *(mutation_cls._injected_field_specs or [])]


@dataclasses.dataclass(frozen=True)
class _Witness:
    """What ``_write_witness`` observed of the backing model's row saves on the owning thread.

    ``written`` holds one ``(instance, pk_at_write, created, using)`` record per
    completed save (its ``post_save``); ``attempted`` is the
    ``utils/write_values.py::attempted_saves`` record of the saves that started and have
    not completed, so after a failed ``serializer.save()`` it holds the row whose save
    raised the caught exception, if a backing-model save raised it, and the columns that
    save wrote (``_attempted_row_integrity_errors``). A backing-model save is one of a row
    of the model, a proxy of it or a multi-table child
    (``utils/write_values.py::saves_rows_of``).
    """

    written: list[_WrittenRow]
    attempted: list[AttemptedSave]


@contextmanager
def _write_witness(
    mutation_cls: type[SerializerMutation],
    model: type[models.Model],
    alias: str,
) -> Generator[_Witness, None, None]:
    """Observe + police the ORM writes of the consumer-controlled write phase.

    Three receivers scoped to the write phase (hooks, validation, and ``serializer.save()``),
    on THIS thread only (concurrent requests in other threads are untouched - each request
    installs its own witness):

    - a ``pre_save`` guard over EVERY model: a cross-alias ``Model.save()`` gets a clear,
      early, serializer-specific error naming ``context['write_alias']`` (before Django
      even opens the cross-alias connection). The COMPLETE cross-alias enforcement is the
      pipeline skeleton's ``pipeline_alias_guard`` (``utils/write_transaction.py``): it
      spans every consumer-reachable phase - not just the write step - and rejects EVERY
      statement on a non-pinned connection without attempting to classify reads vs writes
      (lexical classification is bypassable via comments, ``EXPLAIN ANALYZE``, and
      write-capable functions), so signal-less paths (``QuerySet.update()``,
      ``bulk_create``, raw cursor SQL) are covered there;
    - a ``pre_save`` recorder for the mutation's backing model
      (``utils/write_values.py::attempted_saves``): the yielded witness's ``attempted``
      list holds every instance whose save started and has not completed, with that
      save's ``update_fields`` and the call that sent its ``pre_save`` (``post_save``
      takes it back out), so the save-time ``IntegrityError`` diagnosis reads the row
      whose save raised the caught exception and the columns it wrote
      (``utils/write_values.py::refused_save``);
    - a ``post_save`` recorder for the mutation's backing model: the yielded witness's
      ``written`` list collects
      ``(instance, pk_at_write, created, using)`` for every row the ORM actually wrote.
      On CREATE the saved-result check (``_checked_saved_result``) requires the returned
      row to be one of these INSERTs, so a ``create()`` returning an EXISTING row is
      refused. On UPDATE, a ``created=True`` record of the located row's
      own table under the authorized pk is the update-else-insert re-INSERT of a row
      that vanished after the locate, which ``_guarded_serializer_write`` returns as
      the ``conflict`` envelope (``_inserted_authorized_row``).

    Both recorders hear a save of any row of the backing model: Django sends
    ``pre_save`` / ``post_save`` with the saved instance's own class, so they connect
    without a sender and keep a save whose sender is the model, a proxy of it or a
    multi-table child (``utils/write_values.py::saves_rows_of``), the classes the
    saved-result check accepts a returned row of. A save of the concrete base under a
    proxy model, of a sibling proxy, of a multi-table parent or of an unrelated model
    is not recorded.

    Signal-less SAME-alias bulk writes are invisible to the recorder; for the create
    witness that fails CLOSED (an unwitnessed create result is rejected - persist the
    returned row via ``instance.save()``). Cross-alias writes cannot hide the same way:
    the pipeline's statement guard sees them regardless of signals.
    """
    owner = threading.get_ident()
    written: list[_WrittenRow] = []

    # The cross-alias ``pre_save`` blocker is the shared
    # ``write_transaction.py::make_cross_alias_save_guard`` body; only the
    # actor / recourse message halves are serializer-specific.
    _block_cross_alias = make_cross_alias_save_guard(
        alias,
        actor=(f"SerializerMutation {truth.name(mutation_cls)}: the serializer write phase"),
        recourse="context['write_alias']",
    )

    def _record(
        sender: object,
        instance: models.Model,
        *,
        created: bool,
        using: str | None,
        **kwargs: object,
    ) -> None:
        del kwargs
        if threading.get_ident() != owner or not saves_rows_of(model, sender):
            return
        written.append(
            (
                instance,
                pk_of(instance),
                created,
                using,
            ),
        )

    # The cross-alias blocker connects first, so a save it refuses is never recorded
    # as attempted.
    pre_save.connect(_block_cross_alias, weak=False)
    post_save.connect(_record, weak=False)
    try:
        with attempted_saves(model) as attempted:
            yield _Witness(written=written, attempted=attempted)
    finally:
        _ = post_save.disconnect(_record)
        _ = pre_save.disconnect(_block_cross_alias)


def _saved(serializer: _Saving, save_kwargs: Mapping[str, object]) -> object:
    """Return ``serializer.save(**save_kwargs)``; drf-stubs types the result ``Any``."""
    return serializer.save(**save_kwargs)


def _inserted_authorized_row(
    model: type[models.Model],
    authorized_pk: object,
    alias: str,
    written: list[_WrittenRow],
) -> bool:
    """Return whether the witness saw the located row's table INSERTed under the authorized pk.

    ``written`` is the ``_write_witness`` ``post_save`` record of the backing model; a
    ``created=True`` row whose pk snapshot is ``authorized_pk`` on the pinned alias was
    INSERTed under the located row's key, which a present row would have refused. Only a
    row of the located row's own table counts (``_meta.concrete_model``: the backing
    model or a proxy of it): a multi-table child's ``created`` names its own table's
    INSERT, which a child row saved over a present parent row (an existing row turned
    into a child) reports too.
    """
    table = model._meta.concrete_model
    return any(
        created
        and using == alias
        and row._meta.concrete_model is table
        and pks_match(model, row_pk, authorized_pk)
        for row, row_pk, created, using in written
    )


def _checked_saved_result(
    mutation_cls: type[SerializerMutation],
    saved: object,
    *,
    creating: bool,
    written: list[_WrittenRow],
) -> models.Model:
    """Validate the ``serializer.save()`` result before the pipeline re-fetches it.

    The result must be a persisted row of the mutation's backing model (a wrong-model or
    unsaved return has no row to re-fetch). On CREATE it must also be a row the
    ``_write_witness`` ``post_save`` record saw INSERTED: the skeleton re-fetches the saved
    row without the visibility filter, so a ``create()`` returning an existing row (a
    ``get_or_create`` keyed by a client value) would otherwise answer with a row the caller
    cannot see. A ``create()`` that persists through a signal-less bulk path fails closed;
    persist the returned row through ``instance.save()``.
    """
    model = backing_model_of(mutation_cls._mutation_meta)
    if not truth.is_instance(saved, model) or pk_of(saved) is None or saved._state.adding:
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: save() returned "
            f"{truth.render(saved)}; the serializer's create()/update() must persist and "
            f"return the written {truth.name(model)} row.",
        )
    if creating and not any(row is saved and created for row, _pk, created, _using in written):
        raise ConfigurationError(
            f"SerializerMutation {truth.name(mutation_cls)}: save() returned a "
            f"{truth.name(model)} that was never observed being INSERTED during the save; a "
            "create must persist and return the row it inserted, never an existing row.",
        )
    return saved


def _serializer_write_step(
    mutation_cls: type[SerializerMutation],
    info: Info[object, object],
    instance: models.Model | None,
    provided_data: dict[str, object],
    *,
    specs: Sequence[InputFieldSpec],
) -> models.Model | StepFailure:
    """Run the serializer ``write_step`` callback: construct -> validate -> save.

    Constructs the serializer through the ``get_serializer_kwargs`` hook + the
    framework merge (``_serializer_kwargs``), runs ``is_valid()`` (a failure
    routes ``serializer.errors`` through the flattener), then writes via a
    value-preserving ``serializer.save()`` closure inside a nested-``atomic``
    savepoint and the pinned-alias write phase (``save()`` called EXACTLY ONCE,
    captured via ``nonlocal``). Returns the saved object (the skeleton re-fetches
    it by pk under the optimizer plan) or a ``StepFailure`` on a validation / write
    failure - with the savepoint rolled back first, so a failed save leaves no
    partial write.

    A save-time failure routes by exception CLASS, all caught OUTSIDE the atomic
    block: a DRF ``serializers.ValidationError``'s ``.detail`` -> the recursive
    flattener; a Django ``ValidationError`` / an ``IntegrityError`` -> the shared
    ``save_or_field_errors`` wrapper every flavor's save rides (the flat ``036``
    mapper over ``error_dict`` / ``messages``, never ``.detail``, keyed through
    ``utils/errors.py::save_time_error_key_map``, top-level names only; the
    integrity mapper, diagnosing the refused row through
    ``_attempted_row_integrity_errors``) - never a top-level ``GraphQLError`` at the write. Every
    validation branch builds its key map on that failure path only; a successful
    write never builds one. Every key map reads ``specs``, the mutation's input specs
    as the executing schema published them, which ``_run_serializer_pipeline_sync``
    reads once per request and hands to the decode step too.
    """
    # Class validation gated ``Meta.serializer_class`` to a ``ModelSerializer`` subclass.
    serializer_class = require(mutation_cls._mutation_meta.serializer_class, _is_serializer_class)
    pipeline = require_write_pipeline()
    alias = pipeline.alias
    # The authorized pk is an IMMUTABLE snapshot captured by the pipeline skeleton
    # immediately after the locate - BEFORE the permission hook, the first
    # consumer-controlled code, could touch the mutable located instance (a live
    # ``instance.pk`` read here would already be too late: a malicious permission
    # method runs before this step). A direct (skeleton-less) invocation falls back
    # to snapshotting at step entry - still before any of THIS step's hooks run.
    authorized_pk = pipeline.authorized_pk
    if authorized_pk is None and instance is not None:
        authorized_pk = pk_of(instance)
    # The frozen hook context every consumer hook receives INSTEAD of the live,
    # mutable located instance: the operation kind, the
    # pinned alias, and the authorized pk snapshot.
    hook_context = SerializerHookContext(
        operation=mutation_cls._mutation_meta.operation,
        write_alias=alias,
        instance_pk=authorized_pk,
    )
    # The witness wraps the ENTIRE consumer-controlled phase (the data/kwargs hooks,
    # ``is_valid()`` with its author validators, the save-kwargs hook, and ``save()``):
    # a cross-alias ``Model.save()`` is blocked at ``pre_save`` with a serializer-specific
    # error, and every actual write of the backing model is recorded so a create result
    # can be PROVEN inserted. The statement-level cross-alias net
    # (signal-less paths included) is the pipeline skeleton's ``pipeline_alias_guard``,
    # which spans this step and every other consumer-reachable phase.
    model = backing_model_of(mutation_cls._mutation_meta)
    with _write_witness(mutation_cls, model, alias) as witness:
        return _guarded_serializer_write(
            mutation_cls,
            info,
            instance,
            provided_data,
            serializer_class=serializer_class,
            alias=alias,
            authorized_pk=authorized_pk,
            hook_context=hook_context,
            witness=witness,
            specs=specs,
        )


def _unstorable_value_errors(
    serializer: DRFSerializer,
    model: type[models.Model],
) -> dict[str, list[ErrorDetail]]:
    """Map each field whose validated value the pinned alias cannot store to its error.

    DRF's ``DateTimeField`` answers its own ``overflow`` error for a datetime it cannot place
    in a time zone (``_translate_datetime_overflow`` extends DRF's answer to the values it
    raises raw), and that answer stands (it runs first, inside ``is_valid()``); what it
    lets through can still be a value the database refuses: an
    aware time (SQLite, MySQL and Oracle refuse it at ``save()``), an aware datetime whose
    projection onto the connection's time zone leaves years 1..9999 though the current
    zone's does not, one PostgreSQL stores but cannot load back at the re-fetch, a date
    or naive datetime a ``validate_<field>`` hook leaves for a ``DateTimeField`` column,
    which Django makes aware in the default time zone (a date as its midnight), an aware
    datetime a hook leaves for a ``DateField`` column whose date in the default time zone
    leaves years 1..9999, or a duration past 64 bits of microseconds on a backend that
    binds it as that integer (SQLite, MySQL). A ``DecimalField(max_digits=None,
    decimal_places=None)`` (the field a column with no ``max_digits`` needs, since DRF's
    ``ModelSerializer`` cannot build one) holds no digits, so it can let through a decimal
    PostgreSQL's ``numeric`` refuses at ``save()``, and any field one a bounded column's
    validators accept but SQLite stores as a value the re-fetch cannot read back (an
    infinity, or a double rounded past the column's digits). Each writable bound field whose
    ``source`` is a top-level ``validated_data`` key naming a concrete column of ``model``
    (``utils/relations.py::written_model_field``) is held to
    ``utils/errors.py::unstorable_value`` on the pinned alias
    (``_unstorable_written_values``); a refused one answers
    the ``invalid`` ``UNBINDABLE_TEMPORAL_MESSAGE`` ``ErrorDetail`` under its field name,
    the shape ``serializer.errors`` carries, so the flattener keys it to the input the
    client sent. A converted root input is also checked inside ``is_valid()`` by
    ``_hold_unstorable_values``; this final check catches changes from
    ``validate_<field>`` and ``validate()``. Its uniqueness queries are separately
    guarded at Django's lookup/compiler seams. A nested serializer's values are written
    by the consumer's own ``create()`` / ``update()`` and are not read here.
    """
    return _unstorable_written_values(
        _written_columns(serializer, model),
        validated_data_of(serializer),
        unstorable_value,
    )


def _attempted_row_integrity_errors(
    attempted: list[AttemptedSave],
    error: BaseException,
    error_key_map: ErrorKeyMap,
) -> list[FieldError]:
    """Map a failed ``serializer.save()``'s ``IntegrityError``, naming each input column left null.

    ``attempted`` is the write witness's record of the saves of backing-model rows (the
    model's own, a proxy's or a multi-table child's) that started and never completed,
    and ``error`` the caught exception: the row read is the one whose
    save raised it (``utils/write_values.py::refused_save``), never a save the consumer's
    ``create()`` / ``update()`` caught and swallowed before another write raised. A
    ``blank=True, null=False`` column with no default skips ``Model.clean_fields`` on an
    empty value, so a ``ModelSerializer`` field DRF generates ``required=False`` over it,
    left out, and a declared ``allow_null=True`` field sent ``null`` both reach the
    database's ``NOT NULL`` refusal as an ``IntegrityError`` naming no field. Each such
    input column the row holds ``None`` on (``utils/write_values.py::unstorable_columns``,
    read from the in-memory row, so no query runs on the failed connection) answers
    ``null_field_error`` under its published input name, the model flavor's answer
    (``mutations/resolvers.py::_created_row_integrity_errors``). Only a column the refused
    save writes counts: a save with ``update_fields`` (a consumer ``save()`` narrowing its
    write, or a deferred-load row's loaded fields) leaves every column outside it
    untouched, so its ``None`` cannot be what the database refused; Django accepts a
    column there by its name or its ``attname``. The columns and their names are the
    save-time key map (``utils/errors.py::save_time_error_key_map``), keyed by model field
    name. No backing-model save that raised ``error`` (a custom ``create()`` /
    ``update()`` whose failing write is another model's, the concrete base's under a
    proxy model or a multi-table parent's included, an M2M row, raw SQL, or no write at
    all), or one no such column explains, is the ``"__all__"`` ``constraint`` envelope.
    Read after the failed save, never before, so a consumer ``save()`` that fills the
    value in still writes.
    """
    refused = refused_save(attempted, error)
    if refused is None:
        return integrity_error_field_errors()
    row, update_fields = refused
    columns = unstorable_columns(row, error_key_map, update_fields=update_fields)
    if not columns:
        return integrity_error_field_errors()
    return [null_field_error(error_key_map[column.name][0], column) for column in columns]


def _guarded_serializer_write(
    mutation_cls: type[SerializerMutation],
    info: Info[object, object],
    instance: models.Model | None,
    provided_data: dict[str, object],
    *,
    serializer_class: type[DRFSerializer],
    alias: str,
    authorized_pk: object,
    hook_context: SerializerHookContext,
    witness: _Witness,
    specs: Sequence[InputFieldSpec],
) -> models.Model | StepFailure:
    """Run the write-step body inside the ``_write_witness`` guards.

    Every validation and save-time error is keyed through ``specs``, the mutation's
    input specs named as the executing schema published them
    (``utils/inputs.py::published_input_specs``).

    A save-time ``IntegrityError`` is diagnosed from the row the database refused, the
    backing-model row (the model's own, a proxy's or a multi-table child's) in
    ``witness.attempted`` whose save raised it (``_attempted_row_integrity_errors``): each
    input column that save writes and the row holds ``None`` on with ``null=False`` (a
    ``ModelSerializer`` field DRF generates ``required=False`` over a ``blank=True``
    column with no default, left out; a declared ``allow_null=True`` field sent ``null``)
    answers the field-keyed ``null`` error the model and ``ModelForm`` flavors answer for
    the same column; any other is the ``"__all__"`` ``constraint`` envelope. Create and
    update alike.
    """
    written = witness.written
    # The framework builds the authoritative serializer data ITSELF:
    # decoded client data + the exact-match ``Meta.injected_fields`` injection - a
    # ``get_serializer_kwargs`` override cannot replace or extend it.
    injected = _injected_serializer_data(
        mutation_cls,
        info,
        data=dict(provided_data),
        hook_context=hook_context,
    )
    final_data = {**provided_data, **injected}
    kwargs = _serializer_kwargs(
        mutation_cls,
        info,
        final_data=final_data,
        instance=instance,
        alias=alias,
        hook_context=hook_context,
    )
    # The merged mapping comes from the consumer-overridable ``get_serializer_kwargs``,
    # whose keyword set no static signature can check.
    serializer = call_forwarded(serializer_class, (), kwargs)

    # PROVE the schema-time write surface (GraphQL input + Meta.injected_fields)
    # and the runtime serializer AGREE before ``is_valid()`` runs, so a schema hook that
    # exposed a field the runtime serializer does not actually declare (or declares with a
    # different source / relation target / kind) - or a declared-but-unaccepted injected
    # field - is a framework CONFIGURATION failure, not a silent DRF-ignores-the-unknown-key
    # ambiguity. One walk over ``_write_surface_specs``.
    _assert_schema_runtime_agreement(mutation_cls, serializer)
    _assert_runtime_write_source_ownership(
        mutation_cls,
        serializer,
        final_data,
        _write_surface_specs(mutation_cls),
    )
    # adapt each relation field's queryset to the SAME visibility-scoped queryset the
    # decode used - pinned to the write alias and locked when the operation locks - so DRF's
    # own ``is_valid()`` lookup is the VISIBILITY lookup inside the transaction rather than an
    # unscoped second fetch (defense in depth - DRF can never re-fetch a row the decode's
    # visibility check hid, even if the decode is bypassed).
    _scope_relation_querysets_to_visibility(mutation_cls, serializer, info)
    # DRF's queryset-backed validators issue their own database reads during
    # ``is_valid()``. Pin every field-, serializer-, and nested-level validator
    # queryset to the same alias before validation so uniqueness cannot consult
    # another shard or escape the transaction.
    _pin_validator_querysets(serializer, alias)
    # A datetime DRF cannot place in a time zone fails with its own ``overflow`` error
    # instead of escaping ``is_valid()`` as a raw ``OverflowError``.
    _translate_datetime_overflow(serializer)
    # A value the pinned alias cannot store, or a DRF uniqueness validator at any level
    # cannot bind in its query, fails its field before the validator binds it.
    _hold_unstorable_values(serializer, backing_model_of(mutation_cls._mutation_meta))

    if not serializer.is_valid():
        return StepFailure(
            serializer_errors_to_field_errors(
                serializer_errors(serializer),
                build_error_key_map(specs),
            ),
        )

    # A date, datetime, time, duration or decimal DRF validated (or a ``validate_<field>``
    # hook set) but the pinned alias cannot store (or, on PostgreSQL, read back) is the
    # field's ``invalid`` error before any write.
    storability_errors = _unstorable_value_errors(
        serializer,
        backing_model_of(mutation_cls._mutation_meta),
    )
    if storability_errors:
        return StepFailure(
            serializer_errors_to_field_errors(
                storability_errors,
                build_error_key_map(specs),
            ),
        )

    saved: object = None

    def _do_save() -> None:
        # the DRF-native ``serializer.save(**kwargs)`` customization point
        # (request-derived save-time data, e.g. ``owner=request.user``), distinct from the
        # constructor ``get_serializer_kwargs``; DRF merges the kwargs over
        # ``validated_data``. Invoked INSIDE this value-preserving closure so a hook-raised
        # DRF / Django ``ValidationError`` (or ``IntegrityError`` from a hook query) rides the
        # SAME error mapping as ``save()`` itself - the ``FieldError`` envelope, never a
        # top-level ``GraphQLError``.
        nonlocal saved
        save_kwargs = dict(
            mutation_cls().get_serializer_save_kwargs(
                info,
                data=dict(provided_data),
                hook_context=hook_context,
            ),
        )
        # The write phase opens for exactly ``serializer.save()``; everything
        # before this point was database-read-only under the phased alias guard.
        with pipeline_write_phase():
            saved = _saved(serializer, save_kwargs)

    # The save runs inside its OWN savepoint (a nested ``atomic`` - the same
    # containment ``forced_save_or_field_errors`` uses), rolled back BEFORE a
    # caught validation / integrity failure is converted into the ``FieldError``
    # envelope: a custom ``save()`` that wrote rows and THEN raised must leave
    # the transaction with NO partial writes at conversion time. The exceptions
    # are caught OUTSIDE the atomic block deliberately - an ``IntegrityError``
    # escaping ``save_base``'s savepoint-less inner atomic flags the connection
    # ``needs_rollback``, and only the enclosing atomic's own savepoint rollback
    # clears that flag; a manual savepoint (or a catch INSIDE the block) would
    # leave the transaction refusing every subsequent statement.
    def _savepointed_save() -> None:
        with transaction.atomic(using=alias):
            _do_save()

    def _error_key_map() -> ErrorKeyMap:
        return save_time_error_key_map(
            specs,
            backing_model_of(mutation_cls._mutation_meta),
        )

    try:
        write_error = save_or_field_errors(
            _savepointed_save,
            error_key_map=_error_key_map,
            integrity_errors=lambda exc: _attempted_row_integrity_errors(
                witness.attempted,
                exc,
                _error_key_map(),
            ),
        )
    except DRFValidationError as exc:
        return StepFailure(
            serializer_errors_to_field_errors(
                exc.detail,
                build_error_key_map(specs),
            ),
        )
    if write_error is not None:
        return StepFailure(write_error)
    # An INSERT into the located row's own table under the authorized pk during an UPDATE
    # proves the located row was gone when the save ran (an INSERT over a present row is
    # an ``IntegrityError``): DRF's
    # ``ModelSerializer.update()`` saves through ``save()``'s update-else-insert fallback,
    # so a row a concurrent transaction deleted after the locate was re-inserted. That is
    # the in-band ``conflict`` envelope, rolled back with the re-inserted row.
    if authorized_pk is not None and _inserted_authorized_row(
        backing_model_of(mutation_cls._mutation_meta),
        authorized_pk,
        alias,
        written,
    ):
        return StepFailure([conflict_error()])
    # The saved result is validated BEFORE the pipeline re-fetches it: a persisted row of the
    # backing model, and on create a row the witness saw INSERTED.
    return _checked_saved_result(
        mutation_cls,
        saved,
        creating=authorized_pk is None,
        written=written,
    )


def _serializer_decode_step(
    data: object,
    info: Info[object, object],
    *,
    specs: Sequence[InputFieldSpec],
) -> dict[str, object] | StepFailure:
    """Run the serializer ``decode_step`` callback: serializer-field-keyed decode.

    Decodes the bound input against ``specs``, the top-level reverse map with its nested
    maps, through the recursive ``_decode_input_object`` into a serializer-field-keyed
    ``provided_data`` (type-check + visibility on every relation branch, ``Upload`` into
    ``data``), so a decode ``FieldError`` carries a name the client sent. Returns
    ``provided_data`` for the write step, or a ``StepFailure`` on a decode failure (the
    shared skeleton maps it to a null-object payload). The ``instance`` the skeleton
    locates is not needed at decode (DRF's ``partial=True`` + the framework merge own the
    partial update at construction), so it is not threaded in.
    """
    provided_data, decode_error = _decode_input_object(specs, data, info)
    if decode_error is not None:
        return StepFailure([decode_error])
    return provided_data


def _run_serializer_pipeline_sync(
    mutation_cls: type[SerializerMutation],
    info: Info[object, object],
    data: object,
    id_: object,
) -> object:
    """Run the serializer decode/write callbacks through the shared write skeleton.

    The serializer-flavor dispatcher matching ``_run_pipeline_sync`` /
    ``_run_form_pipeline_sync``: ``make_resolver_entries`` owns the ``UNSET``-default
    kwargs and the async boundary; this body supplies only the serializer
    ``decode_step`` / ``write_step``, both keyed through the mutation's input specs as
    the executing schema published them (``utils/inputs.py::published_input_specs``),
    read once per request.
    """
    # Every error of the request is keyed through the names the executing schema published.
    specs = published_input_specs(info, mutation_cls._input_field_specs)
    return run_write_pipeline_sync(
        mutation_cls,
        info,
        data,
        id_,
        decode_step=lambda _instance: _serializer_decode_step(data, info, specs=specs),
        write_step=lambda instance, decoded: _serializer_write_step(
            mutation_cls,
            info,
            instance,
            decoded,
            specs=specs,
        ),
    )


# The serializer module entries, via the shared factory. The
# full pair is taken so the three write flavors cannot drift on the UNSET-kwargs
# or async-boundary contract.
resolve_serializer_sync: _SyncResolverEntry[type[SerializerMutation]]
resolve_serializer_async: _AsyncResolverEntry[type[SerializerMutation]]
resolve_serializer_sync, resolve_serializer_async = make_resolver_entries(
    _run_serializer_pipeline_sync,
)
