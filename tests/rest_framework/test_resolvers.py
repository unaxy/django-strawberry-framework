"""Serializer-mutation resolver internals a live products `/graphql/` cannot drive.

System-under-test is `rest_framework/resolvers.py` - but ONLY the residue the live
products serializer surface (`examples/fakeshop/test_query/test_products_api.py`)
cannot reach. Per the README "Live-first, both verdicts", every consumer-reachable resolver
branch is earned LIVE; this file holds the genuinely-unreachable internals:

- the recursive `serializer_errors_to_field_errors` flattener over deeply-nested
  shapes no `ItemSerializer` error emits (list indexes, nested dicts, nested
  non-field buckets) - direct-called with synthetic `serializer.errors`-shaped
  dicts;
- raw-pk / NON-Relay relation decoding internals (explicit `None`, empty-list
  no-query, uncoercible short-circuit) that GraphQL validation never delivers as
  those Python values; live batched `pk__in` visibility and hidden-member
  envelopes live in `examples/fakeshop/test_query/test_library_api.py`
  (`test_serializer_m2m_alt_branches_visibility_is_one_batched_query_over_http`,
  `test_nested_shelf_alt_branches_visibility_is_one_batched_query_over_http`,
  `test_serializer_m2m_relation_visibility_over_http`);
- the value-preserving `save()`-called-once capture (a save spy);
- the `IntegrityError` diagnosis branch;
- the `IntegrityError` over a `blank=True, null=False` column on synthetic models: an
  integer and an integer-choice column (fakeshop's live `createItemHoldViaSerializer`
  pins the foreign key), a declared `allow_null` field's `null` on update, a model
  `save()` that fills the value in, a `create()` that raises before saving a row, a
  second thread's attempted row left out of the diagnosis, a `None` column outside the
  refused save's `update_fields` left out of it (a deferred one never loaded), and one
  named there by field name or `attname` kept;
- the `get_serializer_kwargs` / framework-merge / `partial` seams + the bare
  `HttpRequest` `request_from_info` fallback;
- the config-assessment grep-guard + the post-finalization
  `_resolve_globalid_strategy` monkeypatch (recorded strategy consumed, not the
  live setting);
- the `SyncMisuseError` async-`get_queryset`-from-sync path; async create colour
  is live (`test_create_item_via_serializer_over_graphql_async`);
- the re-fetch PLAN OBJECT (`select_related` kept, the selection's columns recorded,
  no `.only(...)` introduced under the mutation operation; spec-035 Decision 4) - the
  optimizer's stashed plan is introspection state no `/graphql` response carries, so
  only its behavioral half (the emitted SQL) is earned live.
- hostile `__name__` labels on producer-declared classes (mutation, serializer,
  field, validator): every `ConfigurationError` diagnostic renders them through
  the shared safe renderers, so a registered hostile-named class degrades its
  labels instead of escaping the metaclass exception raw; honest labels are pinned
  byte-identical (direct-called: no wire query can declare a hostile class).
- a ``validate_<field>`` hook that leaves a date for a ``DateTimeField`` column:
  refused when its default-zone midnight cannot be stored, else stored as that
  midnight. Django warns on every such store, so the example app declares no such
  serializer and the schema is built in-process.
- a ``DateTimeField`` DRF cannot place in a time zone below the top level (a ``ListField``
  child, a nested and a ``many=True`` nested serializer) and a ``DateTimeField`` subclass:
  DRF's ``overflow`` error keyed at its depth, and a ``to_internal_value`` override that
  answers the overflow itself left to it. The example serializer writes its datetime at
  the top level only (live in ``examples/fakeshop/test_query/test_scalars_mutation_api.py``).
- a ``DecimalField(max_digits=None, decimal_places=None)`` over a column with no
  ``max_digits`` (which fakeshop cannot declare on the Django floor) and over a bounded
  one: a decimal past PostgreSQL ``numeric``'s format its column's own validators
  accept refused as the field's ``invalid`` error, written through an alias that reads
  as PostgreSQL.
- a duration a DRF uniqueness validator binds past 64 bits of microseconds below the top
  level (a single, ``many=True`` and two-deep nested item under ``unique=True``,
  ``unique_together``, a conditional ``UniqueConstraint`` (a field in its ``condition``
  included) and ``unique_for_date``, a plain nested ``Serializer`` and a root
  serializer-only field declaring a ``UniqueValidator`` over another model): the item
  field's ``invalid`` error at its dotted path, nested values no validator binds left to
  the consumer's ``create()``, and a serializer-level validator's values held only where
  DRF reaches its query (a ``None`` partner, an omitted partner or ``date_field``).
  Dynamic duration and conditional cases are covered over HTTP in
  ``examples/fakeshop/test_query/test_serializer_validator_bind_api.py``.

**No create/update happy path, envelope, reverse-map, partial-update, visibility,
write-auth, authorize-before-decode, Upload, request-context, or re-fetch BEHAVIORAL test
is duplicated here** - those are owned by the live suite.

Consumer save-error mapping, post-save conflict, partial-write rollback and runtime-only
fields live in ``examples/fakeshop/test_query/test_serializer_runtime_api.py``. The direct
savepoint rollback timing, private exception classes and raw decoded mappings remain package
observations.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import decimal
import inspect
import logging
import re
import sys
import threading
import uuid
import zoneinfo
from collections.abc import Callable, Generator, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from typing import TYPE_CHECKING, NoReturn, Protocol, cast, runtime_checkable

import django
import pytest
import pytest_django
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.products.serializers import RenamedRelationItemSerializer
from apps.products.services import seed_data
from apps.scalars.models import NullableScalarSpecimen, ScalarSpecimen
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, connections, models, transaction
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import Model, QuerySet
from django.db.models.signals import post_save, pre_save
from django.db.utils import OperationalError
from django.http import HttpRequest
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework.settings import api_settings
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from strawberry import relay
from strawberry.types.base import StrawberryContainer, get_object_definition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    NestedSerializerConfig,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.resolvers import StepFailure
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework import resolvers as serializer_resolvers
from django_strawberry_framework.rest_framework.accessors import (
    base_fields,
    bound_fields,
    child_relation_of,
    declared_fields_of,
    list_child_of,
    serializer_errors,
    validated_data_of,
)
from django_strawberry_framework.rest_framework.hook_context import (
    SerializerHookContext,
)
from django_strawberry_framework.rest_framework.inputs import (
    build_serializer_input_class,
)
from django_strawberry_framework.rest_framework.serializer_converter import (
    NESTED_MULTI,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.types import relay as relay_module
from django_strawberry_framework.types.converters import SCALAR_MAP
from django_strawberry_framework.utils._narrowing import (
    call_method,
    is_list,
    is_mapping,
    is_tuple,
    pk_of,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils._queryset_private import (
    queryset_db,
)
from django_strawberry_framework.utils.errors import NON_FIELD_ERROR_KEY, build_error_key_map
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.inputs import (
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    InputFieldSpec,
)
from django_strawberry_framework.utils.querysets import SyncMisuseError
from django_strawberry_framework.utils.typing import call_forwarded, object_result
from django_strawberry_framework.utils.write_transaction import (
    authorization_phase,
    managed_write_transaction,
    pipeline_alias_guard,
    require_write_pipeline,
    write_pipeline,
)
from django_strawberry_framework.utils.write_values import refused_save
from django_strawberry_framework.write_mixins import _ValidatedMutationMeta
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._generated_inputs import keyword_constructor as _keyword_constructor
from tests._idioms import (
    AllowAll,
    ModelSerializerBase,
    PingQuery,
    is_object_dict,
    json_at,
    json_object,
    run_capturing,
    saved_pk,
)
from tests._info import make_info, unread_info
from tests._postgresql_stand_in import numeric_refusing_postgresql

if TYPE_CHECKING:
    from typing import TypeAlias, TypeVar

    from django.db.backends.utils import CursorWrapper
    from django.db.models.expressions import Combinable
    from typing_extensions import TypeIs

    from django_strawberry_framework.rest_framework.serializer_converter import (
        DRFField,
        DRFRelatedField,
        DRFSerializer,
    )
    from django_strawberry_framework.utils.errors import ErrorKeyMap, FieldError

    _ModelT = TypeVar("_ModelT", bound=Model)

    # An integer column's descriptor types as django-stubs declares them (set type, get type),
    # spelled out because the checker runs without the django-stubs mypy plugin.
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _Text: TypeAlias = models.TextField[str | Combinable, str]

    # A declared ``PrimaryKeyRelatedField``: drf-stubs type its constructor as returning the
    # single relation or, under ``many=True``, a ``ManyRelatedField``.
    _PkRelation: TypeAlias = (
        serializers.RelatedField[_ModelT, _ModelT, object] | serializers.ManyRelatedField
    )


def _first_column(cursor: CursorWrapper) -> object:
    """The first column of ``cursor``'s next row (the stubs type ``fetchone`` as ``Any``)."""
    row = require(call_method(cursor, "fetchone"), is_tuple)
    return row[0]


def _serializer_context(kwargs: dict[str, object]) -> dict[object, object]:
    """Return the ``context`` dict the merged serializer kwargs carry."""
    context = kwargs["context"]
    assert is_object_dict(context)
    return context


def _hook_ctx(
    operation: str = "create",
    alias: str = "default",
    instance_pk: object = None,
) -> SerializerHookContext:
    """A frozen hook context for direct-call tests (the shape the pipeline builds)."""
    return SerializerHookContext(
        operation=operation,
        write_alias=alias,
        instance_pk=instance_pk,
    )


def _as_serializer_mutation(stand_in: object) -> type[SerializerMutation]:
    """Hand a plain stand-in class to a resolver internal that takes a ``SerializerMutation``."""
    # basedpyright: a plain class carrying only the bound-mutation slots the internal reads (spec
    # lists, a ``_mutation_meta`` snapshot), so a slot can be malformed or absent; the serializer
    # resolver internals type the parameter as type[SerializerMutation]
    return stand_in  # pyright: ignore[reportReturnType]


class _CityRequest(HttpRequest):
    """A request carrying the visibility probe the ``get_queryset`` hook reads."""

    visibility_city: str


@runtime_checkable
class _ErrorEnvelope(Protocol):
    """The ``errors`` envelope every bind-materialized ``<Name>Payload`` carries."""

    errors: list[FieldError]


def _related_queryset(relation: object) -> QuerySet[Model, object]:
    """The ``QuerySet`` a ``RelatedField`` holds (the scope pass never leaves a manager)."""
    queryset = read_attr(relation, "queryset")
    assert isinstance(relation, serializers.RelatedField)
    assert isinstance(queryset, QuerySet)
    return queryset


def _child_relation(field: object) -> DRFRelatedField:
    """The per-member ``child_relation`` of a ``many=True`` relation field."""
    assert isinstance(field, serializers.ManyRelatedField)
    return child_relation_of(field)


def _is_queryset(value: object) -> TypeIs[QuerySet[Model, object]]:
    """Return whether ``value`` is a ``QuerySet`` (subclasses included)."""
    return isinstance(value, QuerySet)


def _validator_queryset_db(validator: UniqueValidator | UniqueTogetherValidator) -> str | None:
    """The alias a DRF uniqueness validator's queryset is pinned to (``None``: router decides)."""
    # drf-stubs types both validators' ``queryset`` as the bare generic ``QuerySet``.
    return queryset_db(require(read_attr(validator, "queryset"), _is_queryset))


pytestmark = pytest.mark.usefixtures("isolate_global_registry")


# ===========================================================================
# Recursive flattener shapes the products serializer never emits
# ===========================================================================
# `ItemSerializer` only ever emits flat field errors / a top-level `"__all__"`,
# so the recursive nesting (list indexes, nested dict child paths, nested
# non-field buckets) is unreachable live and direct-called here.


def test_flattener_list_index_child_error_becomes_dotted_path() -> None:
    """A `ListField` / `MultipleChoiceField` indexed child error -> dotted-path `tags.2`."""
    errors = {"tags": {2: ["bad tag"]}}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert [(fe.field, fe.messages) for fe in flat] == [("tags.2", ["bad tag"])]


def test_flattener_nested_dict_error_joins_its_path() -> None:
    """A nested dict-shaped error joins its dotted path (`items.0.name`)."""
    errors = {"items": [{"name": ["required"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert [(fe.field, fe.messages) for fe in flat] == [("items.0.name", ["required"])]


def test_flattener_nested_non_field_error_normalizes_to_path_all() -> None:
    """A nested `non_field_errors` bucket normalizes to `<path>.__all__`, no leaf dropped."""
    drf_key = api_settings.NON_FIELD_ERRORS_KEY
    errors = {"items": [{drf_key: ["cross-field at index 0"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    # `items.0` + the non-field bucket -> the parent path's `"__all__"` at that level.
    assert [(fe.field, fe.messages) for fe in flat] == [
        (f"items.0.{NON_FIELD_ERROR_KEY}", ["cross-field at index 0"]),
    ]


def test_flattener_top_level_non_field_bucket_is_all_sentinel() -> None:
    """A top-level `non_field_errors` bucket normalizes to the bare `"__all__"` sentinel."""
    drf_key = api_settings.NON_FIELD_ERRORS_KEY
    errors = {drf_key: ["model-wide error"]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert [(fe.field, fe.messages) for fe in flat] == [
        (NON_FIELD_ERROR_KEY, ["model-wide error"]),
    ]


def test_flattener_rekeys_root_segment_through_the_key_map() -> None:
    """A top-level field's leaf path is re-keyed through the recursive key map."""
    key_map: ErrorKeyMap = {"category": ("categoryId", None)}
    errors = {"category": ["bad relation"], "items": [{"category": ["nested"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, key_map)
    by_path = {fe.field: fe.messages for fe in flat}
    # `category` re-keyed to `categoryId`; the synthetic `items` has no key-map entry
    # (and no child map), so its children stay verbatim.
    assert by_path == {"categoryId": ["bad relation"], "items.0.category": ["nested"]}


def test_nested_specs_of_refuses_a_spec_recording_no_nested_map() -> None:
    """A nested kind's spec carries its nested map; one recording none raises ``TypeError``."""
    child = InputFieldSpec(input_attr="code", graphql_name="code", target_name="code", kind=SCALAR)
    nested = InputFieldSpec(
        input_attr="shelves",
        graphql_name="shelves",
        target_name="shelves",
        kind=NESTED_MULTI,
        nested_specs=(child,),
    )
    assert serializer_resolvers._nested_specs_of(nested) == (child,)
    with pytest.raises(TypeError, match=r"input field spec 'shelves' \(nested_multi\) records no"):
        serializer_resolvers._nested_specs_of(dataclasses.replace(nested, nested_specs=None))


def test_flattener_recursively_rekeys_nested_child_fields() -> None:
    """Nested child fields are re-keyed to their GraphQL names at EVERY depth.

    A nested child field whose GraphQL name differs from its serializer name
    (``alt_branches`` -> ``altBranches``) is re-keyed inside the nested path, not left as the
    serializer name - so nested DRF validation errors match the framework decode-error paths.
    """
    child_specs = (
        InputFieldSpec(input_attr="code", graphql_name="code", target_name="code", kind=SCALAR),
        InputFieldSpec(
            input_attr="alt_branches",
            graphql_name="altBranches",
            target_name="alt_branches",
            kind=RELATION_MULTI,
        ),
    )
    top_specs = [
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            kind=NESTED_MULTI,
            nested_specs=child_specs,
        ),
    ]
    key_map = build_error_key_map(top_specs)
    errors = {"shelves": [{"alt_branches": ["Bad pk"]}]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, key_map)
    assert fe.field == "shelves.0.altBranches"
    assert fe.path == ["shelves", "0", "altBranches"]


def test_flattener_rekeys_children_under_an_index_keyed_list_serializer_error() -> None:
    """An ``int`` error key is an item index carrying the level map, so its children re-key.

    DRF 3.18's ``ListSerializer`` reports only its failing items, as ``{index: errors}``;
    the dict is fed directly, so the row holds on every DRF version in the support range.
    """
    child_specs = (
        InputFieldSpec(input_attr="code", graphql_name="code", target_name="code", kind=SCALAR),
        InputFieldSpec(
            input_attr="alt_branches",
            graphql_name="altBranches",
            target_name="alt_branches",
            kind=RELATION_MULTI,
        ),
    )
    top_specs = [
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            kind=NESTED_MULTI,
            nested_specs=child_specs,
        ),
    ]
    key_map = build_error_key_map(top_specs)
    errors = {"shelves": {1: {"alt_branches": ["x"]}}}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, key_map)
    assert fe.field == "shelves.1.altBranches"
    assert fe.path == ["shelves", "1", "altBranches"]


def test_flattener_nested_non_field_bucket_keeps_all_sentinel_with_recursive_map() -> None:
    """A nested non-field bucket normalizes to ``<path>.__all__`` even with the recursive map."""
    child_specs = (
        InputFieldSpec(input_attr="code", graphql_name="code", target_name="code", kind=SCALAR),
    )
    top_specs = [
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            kind=NESTED_MULTI,
            nested_specs=child_specs,
        ),
    ]
    key_map = build_error_key_map(top_specs)
    drf_key = api_settings.NON_FIELD_ERRORS_KEY
    errors = {"shelves": [{drf_key: ["cross-field"]}]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, key_map)
    assert fe.field == f"shelves.0.{NON_FIELD_ERROR_KEY}"
    assert fe.path == ["shelves", "0", NON_FIELD_ERROR_KEY]


# ===========================================================================
# Raw-pk / non-Relay + many-relation decode (synthetic - unreachable live)
# ===========================================================================
# Products' `Category` is Relay-`GlobalID` + single, so the generated input only
# ever delivers one GlobalID shape; the raw-pk / non-Relay and many branches are
# driven by direct call against a synthetic non-Relay primary.


def _declare_nonrelay_genre_primary() -> type[DjangoType]:
    """A NON-Relay primary `DjangoType` over `Genre` (raw-pk target, no GlobalID)."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    return GenreT


@pytest.mark.django_db
def test_decode_relation_single_raw_pk_hidden_target_is_field_error() -> None:
    """A raw-pk single relation whose target is hidden by `get_queryset` -> field-keyed error."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Genre],
            info: strawberry.Info,
        ) -> QuerySet[library_models.Genre]:
            # Hide everything: the raw pk resolves to no VISIBLE row.
            return queryset.none()

    del GenreT
    genre = library_models.Genre.objects.create(name="HiddenGenre")
    pk, error = serializer_resolvers._decode_relation_single(
        saved_pk(genre),
        graphql_name="genreId",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert pk is None
    assert error is not None
    assert error.field == "genreId"


@pytest.mark.django_db
def test_decode_relation_single_raw_pk_visible_reduces_to_pk() -> None:
    """A raw-pk single relation whose target is visible reduces to its pk (the DRF write value)."""
    _declare_nonrelay_genre_primary()
    genre = library_models.Genre.objects.create(name="VisibleGenre")
    pk, error = serializer_resolvers._decode_relation_single(
        saved_pk(genre),
        graphql_name="genreId",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert error is None
    assert pk == saved_pk(genre)


@pytest.mark.django_db
def test_decode_relation_single_uncoercible_raw_pk_is_field_error() -> None:
    """A raw-pk relation value that does not coerce to the target pk is a field-keyed error."""
    _declare_nonrelay_genre_primary()
    pk, error = serializer_resolvers._decode_relation_single(
        "not-a-pk",
        graphql_name="genreId",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert pk is None
    assert error is not None
    assert error.field == "genreId"


@pytest.mark.django_db
def test_decode_relation_single_wrong_model_global_id_is_field_error() -> None:
    """A well-formed GlobalID for the WRONG model is a field-keyed error (no cross-model lookup)."""

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    assert registry.get(library_models.Genre) is GenreT

    finalize_django_types()
    genre = library_models.Genre.objects.create(name="WrongModelGenre")
    # A GlobalID whose type slot names a DIFFERENT model (`library.shelf`) than the
    # Genre-typed relation: `decode_model_global_id` rejects the model mismatch ->
    # field error, never a cross-model pk lookup.
    wrong_gid = str(relay.GlobalID(type_name="library.shelf", node_id=str(saved_pk(genre))))
    pk, error = serializer_resolvers._decode_relation_single(
        wrong_gid,
        graphql_name="genreId",
        related_model=library_models.Genre,
        key_attname=None,
        # A GlobalID decode reads the executing schema off ``info``.
        info=make_info(),
    )
    assert pk is None
    assert error is not None
    assert error.field == "genreId"


@pytest.mark.django_db
def test_decode_relation_multi_collects_visible_then_short_circuits() -> None:
    """A many-relation collects each visible member's pk and short-circuits on a bad element.

    Live HTTP never delivers an uncoercible Python value (GraphQL rejects it at
    validation). The batched visible-set SQL is
    ``test_library_api.py::test_serializer_m2m_alt_branches_visibility_is_one_batched_query_over_http``.
    """
    _declare_nonrelay_genre_primary()
    g1 = library_models.Genre.objects.create(name="MG1")
    g2 = library_models.Genre.objects.create(name="MG2")
    pks, error = serializer_resolvers._decode_relation_multi(
        [saved_pk(g1), saved_pk(g2)],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert error is None
    assert pks == [saved_pk(g1), saved_pk(g2)]

    # A bad (uncoercible) element short-circuits to the field-keyed error.
    pks, error = serializer_resolvers._decode_relation_multi(
        [saved_pk(g1), "bad"],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert pks is None
    assert error is not None
    assert error.field == "genreIds"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["single", "multi"])
def test_decode_relation_over_a_to_field_key_answers_pks_and_refuses_a_null_key(kind: str) -> None:
    """A relation storing another column answers pks for DRF and refuses a ``NULL`` key.

    ``PrimaryKeyRelatedField`` resolves pks, so a row with a key decodes to its pk, never
    the key; a visible row whose stored key is ``NULL`` would be stored as an empty relation
    and is the relation error. ``NullableScalarSpecimen.label`` stands in for that column.
    """
    keyed = NullableScalarSpecimen.objects.create(label="SerKeyed")
    unkeyed = NullableScalarSpecimen.objects.create(label=None)
    decode = (
        serializer_resolvers._decode_relation_single
        if kind == "single"
        else serializer_resolvers._decode_relation_multi
    )

    def run(pk: object) -> tuple[object, FieldError | None]:
        return decode(
            pk if kind == "single" else [pk],
            graphql_name="partnerId",
            related_model=NullableScalarSpecimen,
            key_attname="label",
            info=unread_info(),
        )

    expected = saved_pk(keyed) if kind == "single" else [saved_pk(keyed)]
    assert run(saved_pk(keyed)) == (expected, None)
    value, error = run(saved_pk(unkeyed))
    assert value is None
    assert error is not None
    assert (error.field, error.messages, error.codes) == (
        "partnerId",
        ["Invalid id for relation 'partnerId'."],
        ["invalid"],
    )


@pytest.mark.django_db
def test_decode_relation_single_explicit_none_passes_through() -> None:
    """An explicit `None` is a clear / no-value passed through (the serializer decides required-ness)."""
    _declare_nonrelay_genre_primary()
    pk, error = serializer_resolvers._decode_relation_single(
        None,
        graphql_name="genreId",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert error is None
    assert pk is None


@pytest.mark.django_db
def test_decode_relation_multi_explicit_none_passes_through() -> None:
    """An explicit `None` whole-list is passed through with no per-member walk.

    The serializer's required-ness decides whether `None` is acceptable.
    """
    _declare_nonrelay_genre_primary()
    pks, error = serializer_resolvers._decode_relation_multi(
        None,
        graphql_name="genreIds",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert error is None
    assert pks is None


@pytest.mark.django_db
def test_decode_relation_multi_empty_list_passes_through_without_query() -> None:
    """An empty many-relation input returns an empty list before any visibility query."""
    _declare_nonrelay_genre_primary()
    pks, error = serializer_resolvers._decode_relation_multi(
        [],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        key_attname=None,
        info=unread_info(),
    )
    assert error is None
    assert pks == []


# ===========================================================================
# Value-preserving save, save-time exception split, IntegrityError
# ===========================================================================


def _bind_item_serializer_mutation(
    serializer_cls: type[DRFSerializer],
    *,
    operation: str = "create",
    nested_fields: Mapping[str, NestedSerializerConfig] | None = None,
) -> type[SerializerMutation]:
    """Declare + finalize a minimal `SerializerMutation` over `serializer_cls`."""
    op_value = operation
    nested_value = nested_fields

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    class WriteItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = op_value
            nested_fields = nested_value
            permission_classes = [AllowAll]

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(WriteItem)

    finalize_django_types()
    DjangoSchema(query=PingQuery, mutation=Mutation)
    del CategoryT, ItemT
    return WriteItem


@pytest.mark.django_db
def test_serializer_save_is_called_exactly_once_and_refetch_uses_returned_object() -> None:
    """`serializer.save()` is called EXACTLY once; the value-preserving closure captures the return."""
    seed_data(0)
    calls: list[int] = []

    class SpyItemSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def save(self, **kwargs: object) -> product_models.Item:
            calls.append(1)
            return super().save(**kwargs)

    (category,) = categories_from_seed(("SpyCat", False))
    write_step = serializer_resolvers._serializer_write_step

    # Drive the write step directly with a constructed mutation + a faked info.
    mutation_cls = _bind_item_serializer_mutation(SpyItemSerializer)
    request = HttpRequest()
    request.user = User(username="spy")
    info = make_info(context=SimpleNamespace(request=request))

    provided: dict[str, object] = {"name": "SpyItem", "category": saved_pk(category)}
    # The write-pipeline context stands in for the shared skeleton the direct call bypasses.
    with write_pipeline("default", lock=False):
        saved = write_step(
            mutation_cls,
            info,
            None,
            provided,
            specs=mutation_cls._input_field_specs,
        )
    assert calls == [1]  # save() called exactly once
    assert isinstance(saved, product_models.Item)
    assert saved_pk(saved) is not None
    assert saved.name == "SpyItem"


def test_serializer_write_step_refuses_a_snapshot_with_no_serializer_class() -> None:
    """The write step reads only a serializer-flavor snapshot; one without a class is a typed error."""
    stand_in = _as_serializer_mutation(
        type(
            "NoSerializerMutation",
            (),
            {
                "_mutation_meta": _ValidatedMutationMeta(
                    model=None,
                    operation="create",
                    input_class=None,
                    partial_input_class=None,
                    fields=None,
                    exclude=None,
                    permission_classes=(),
                ),
            },
        ),
    )
    with pytest.raises(TypeError, match="expected the type the source guarantees, got NoneType"):
        serializer_resolvers._serializer_write_step(stand_in, unread_info(), None, {}, specs=())


@pytest.mark.django_db
def test_save_time_django_validation_error_keys_a_serializer_only_field_to_its_input_name() -> (
    None
):
    """A save-time Django error on a serializer-only input field keys to that field's input name.

    ``review_note`` is a write-only serializer field with no ``Item`` column behind it, so
    there is no model field to read names from; the field's own name still maps to its
    input ``reviewNote``.
    """
    seed_data(0)

    class NoteRaisingSerializer(ModelSerializerBase[product_models.Item]):
        review_note = serializers.CharField(write_only=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "review_note")

        @override
        def save(self, **kwargs: object) -> NoReturn:
            raise DjangoValidationError({"review_note": ["bad note"]})

    (category,) = categories_from_seed(("DjNoteCat", False))
    mutation_cls = _bind_item_serializer_mutation(NoteRaisingSerializer)
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "OK", "category": saved_pk(category), "review_note": "n"},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.path, fe.messages) for fe in result.errors] == [
        ("reviewNote", ["reviewNote"], ["bad note"]),
    ]


@pytest.mark.django_db
def test_save_time_django_validation_error_reads_its_names_as_backing_model_fields() -> None:
    """A Django error raised about a nested item keys as a field of the backing model.

    A Django ``ValidationError`` names no model or nested item, so the save-time key
    map reads each name against the backing ``Category`` only: ``name`` lands on the
    root input ``title`` that backs ``Category.name`` even when the nested ``Item``
    raised it, and ``category``, which ``Category`` lacks, keeps its name. Neither
    reaches an ``items.<i>`` path; that takes a DRF ``ValidationError`` in the nested
    shape.
    """
    seed_data(0)
    categories_from_seed()

    class ItemChild(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name",)

    class ItemRaisingCategorySerializer(ModelSerializerBase[product_models.Category]):
        title = serializers.CharField(source="name")
        items = ItemChild(many=True)

        class Meta:
            model = product_models.Category
            fields = ("title", "items")

        @override
        def create(self, validated_data: dict[str, object]) -> NoReturn:
            items = cast("list[dict[str, object]]", validated_data.pop("items"))
            category = product_models.Category.objects.create(**validated_data)
            for item in items:
                _ = product_models.Item.objects.create(category=category, **item)
            raise DjangoValidationError(
                {"name": ["item name"], "category": ["item category"]},
            )

    mutation_cls = _bind_item_serializer_mutation(
        ItemRaisingCategorySerializer,
        nested_fields={"items": NestedSerializerConfig()},
    )
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"title": "BackingReadCat", "items": [{"name": "BackingReadItem"}]},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.path, fe.messages) for fe in result.errors] == [
        ("title", ["title"], ["item name"]),
        ("category", ["category"], ["item category"]),
    ]


@pytest.mark.django_db
def test_save_time_django_validation_error_rekeys_model_name_to_wire_name() -> None:
    """A save-time Django `ValidationError` on a relation reports the wire name, not the column.

    The flat-mapper fallback re-keys through the specs like every other error path: a
    custom `save()` raising on the `category` FK surfaces as `categoryId` (the input name
    the client sent), matching the relation-decode contract.
    """
    seed_data(0)

    class DjangoRaisingOnRelationSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def save(self, **kwargs: object) -> NoReturn:
            raise DjangoValidationError({"category": ["django save-time on relation"]})

    (category,) = categories_from_seed(("DjRaiseRelCat", False))
    mutation_cls = _bind_item_serializer_mutation(DjangoRaisingOnRelationSerializer)
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "OK", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.messages) for fe in result.errors] == [
        ("categoryId", ["django save-time on relation"]),
    ]


@pytest.mark.django_db
def test_save_time_django_validation_error_uses_source_aware_wire_name() -> None:
    """A save-time Django `ValidationError` re-keys through a `source=` remap to the wire name.

    `RenamedRelationItemSerializer.category_pk` writes through `source="category"`; a custom
    `save()` raising Django-style on the MODEL name `category` surfaces as `categoryPk` (the
    wire name the client sent), not the model column.
    """
    seed_data(0)

    class RaisingRenamedSerializer(RenamedRelationItemSerializer):
        @override
        def save(self, **kwargs: object) -> NoReturn:
            raise DjangoValidationError({"category": ["django save-time renamed"]})

    (category,) = categories_from_seed(("DjRaiseRenCat", False))
    mutation_cls = _bind_item_serializer_mutation(RaisingRenamedSerializer)
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"display_name": "OK", "category_pk": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.messages) for fe in result.errors] == [
        ("categoryPk", ["django save-time renamed"]),
    ]


@pytest.mark.django_db
def test_save_time_django_validation_error_on_the_key_keys_to_a_field_declared_pk() -> None:
    """A save-time Django error on the primary key surfaces under a field declared ``pk``.

    ``pk = IntegerField()`` writes the key through Django's ``pk`` alias, which no
    ``Options.get_field`` name spells. Django's own unique check names the key by its model
    field, ``id``, so a ``create()`` raising ``{"id": [...]}`` surfaces as ``pk``, the field
    the client sent.
    """
    seed_data(0)

    class DeclaredPkSerializer(ModelSerializerBase[product_models.Item]):
        pk = serializers.IntegerField()

        class Meta:
            model = product_models.Item
            fields = ("pk", "name", "category")

        @override
        def create(self, validated_data: dict[str, object]) -> NoReturn:
            raise DjangoValidationError({"id": ["Item with this ID already exists."]})

    (category,) = categories_from_seed(("DjRaisePkCat", False))
    mutation_cls = _bind_item_serializer_mutation(DeclaredPkSerializer)
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"pk": 4242, "name": "OK", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.messages) for fe in result.errors] == [
        ("pk", ["Item with this ID already exists."]),
    ]


@pytest.mark.django_db
def test_save_time_integrity_error_maps_to_all_sentinel_envelope() -> None:
    """A save-time `IntegrityError` (a race) maps to the `"__all__"` envelope via `save_or_field_errors`."""
    seed_data(0)

    class IntegrityRaisingSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def save(self, **kwargs: object) -> NoReturn:
            raise IntegrityError("races to the unique constraint")

    (category,) = categories_from_seed(("IntRaiseCat", False))
    mutation_cls = _bind_item_serializer_mutation(IntegrityRaisingSerializer)
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "OK", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [fe.field for fe in result.errors] == [NON_FIELD_ERROR_KEY]


# ===========================================================================
# A save-time ``IntegrityError`` over a ``blank=True, null=False`` column
# ===========================================================================

_PICK_CHOICES = [(1, "One"), (2, "Two")]

_NULL_AMOUNT_ERROR = {
    "field": "amount",
    "messages": ["This field cannot be null."],
    "codes": ["null"],
}
_NULL_PICK_ERROR = {"field": "pick", "messages": ["This field cannot be null."], "codes": ["null"]}
_CONSTRAINT_ENVELOPE = [
    {
        "field": NON_FIELD_ERROR_KEY,
        "messages": ["A database constraint was violated."],
        "codes": ["constraint"],
    },
]


def _blank_columns_model(name: str) -> type[Model]:
    """A synthetic model: ``blank=True, null=False`` integer ``amount`` and integer-choice ``pick``.

    Neither column has a default, so a ``ModelSerializer`` generates both fields
    ``required=False`` and ``allow_null=False``; an omitted one leaves ``None`` on the row.
    """
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(blank=True),
            "pick": models.IntegerField(choices=_PICK_CHOICES, blank=True),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


@contextlib.contextmanager
def _synthetic_table(model_class: type[Model]) -> Generator[None, None, None]:
    """Give a ``managed = False`` synthetic model a real table for the test, then drop it."""
    with connections["default"].schema_editor() as schema_editor:
        schema_editor.create_model(model_class)
    try:
        yield
    finally:
        with connections["default"].schema_editor() as schema_editor:
            schema_editor.delete_model(model_class)


def _blank_columns_schema(
    serializer_cls: type[DRFSerializer],
    model_class: type[Model],
    *,
    nested_fields: Mapping[str, NestedSerializerConfig] | None = None,
) -> tuple[DjangoSchema, str, str]:
    """A non-Relay primary + create / update ``SerializerMutation`` over ``serializer_cls``.

    ``nested_fields`` is each mutation's ``Meta.nested_fields`` when given. Returns the schema
    and the create / update input type names.
    """
    nesting = {} if nested_fields is None else {"nested_fields": nested_fields}
    type(
        f"{model_class.__name__}T",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": model_class, "fields": ("id", "amount"), "primary": True},
            ),
        },
    )
    create = type(
        "CreateRow",
        (SerializerMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "serializer_class": serializer_cls,
                    "operation": "create",
                    "permission_classes": [],
                    **nesting,
                },
            ),
        },
    )
    update = type(
        "UpdateRow",
        (SerializerMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "serializer_class": serializer_cls,
                    "operation": "update",
                    "permission_classes": [],
                    **nesting,
                },
            ),
        },
    )

    @strawberry.type
    class Mutation:
        create_row = DjangoMutationField(create)
        update_row = DjangoMutationField(update)

    finalize_django_types()
    assert create._input_class is not None
    assert update._input_class is not None
    return (
        DjangoSchema(query=PingQuery, mutation=Mutation),
        create._input_class.__name__,
        update._input_class.__name__,
    )


def _serializer_over(
    model_class: type[Model],
    fields: tuple[str, ...],
    declared: Mapping[str, object] | None = None,
    methods: Mapping[str, object] | None = None,
    meta: Mapping[str, object] | None = None,
) -> type[DRFSerializer]:
    """A ``ModelSerializer`` over ``model_class`` writing ``fields``, plus ``declared`` fields.

    ``meta`` adds ``Meta`` options beside ``model`` and ``fields``.
    """
    return type(
        f"{model_class.__name__}Serializer",
        (serializers.ModelSerializer,),
        {
            **(declared or {}),
            **(methods or {}),
            "Meta": type("Meta", (), {"model": model_class, "fields": fields, **(meta or {})}),
        },
    )


def _run_row_write(
    schema: DjangoSchema,
    input_name: str,
    data: dict[str, object],
    row_id: object = None,
) -> object:
    """Run ``createRow`` (``row_id`` ``None``) or ``updateRow``; answer its payload."""
    request = HttpRequest()
    request.user = User(username="u")
    if row_id is None:
        document = (
            f"mutation($d: {input_name}!){{ createRow(data:$d){{ "
            "result{ id } errors{ field messages codes } } }"
        )
        variables: dict[str, object] = {"d": data}
        root = "createRow"
    else:
        document = (
            f"mutation($id: ID!, $d: {input_name}!){{ updateRow(id:$id, data:$d){{ "
            "result{ id } errors{ field messages codes } } }"
        )
        variables = {"id": str(row_id), "d": data}
        root = "updateRow"
    result = schema.execute_sync(
        document,
        variable_values=variables,
        context_value=SimpleNamespace(request=request),
    )
    assert result.errors is None, result.errors
    return json_at(result.data, root)


@pytest.mark.parametrize(
    (
        "amount_field",
        "operation",
        "data",
        "errors",
    ),
    [
        pytest.param(
            "generated",
            "create",
            {},
            [_NULL_AMOUNT_ERROR, _NULL_PICK_ERROR],
            id="omitted",
        ),
        pytest.param(
            "generated",
            "create",
            {"amount": 3},
            [_NULL_PICK_ERROR],
            id="omitted-choice",
        ),
        pytest.param(
            "declared",
            "create",
            {"amount": None},
            [_NULL_AMOUNT_ERROR],
            id="create-null",
        ),
        pytest.param(
            "declared",
            "update",
            {"amount": None},
            [_NULL_AMOUNT_ERROR],
            id="update-null",
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_save_time_null_on_not_null_column_is_field_keyed_null_error(
    amount_field: str,
    operation: str,
    data: dict[str, object],
    errors: list[dict[str, object]],
) -> None:
    """``None`` on a ``blank=True, null=False`` column is that column's ``null`` error.

    A generated field over such a column is ``required=False``, so an omitted value
    leaves ``None`` on the row (an integer and an integer-choice column); a declared
    ``allow_null=True`` field sends ``None`` through. ``Model.clean_fields`` skips a
    ``blank=True`` empty value, so the database's ``NOT NULL`` ``IntegrityError`` is the
    first refusal, and the write step diagnoses it from the row the witness saw attempted
    (``_attempted_row_integrity_errors``): the field, message and code the model and
    ``ModelForm`` flavors answer, never the ``"__all__"`` ``constraint`` envelope. Nothing
    is written (no row on create, the stored value unchanged on update).
    """
    model_class = _blank_columns_model("BlankColumnsRow")
    serializer_cls = (
        _serializer_over(
            model_class,
            ("amount",),
            {"amount": serializers.IntegerField(required=False, allow_null=True)},
        )
        if amount_field == "declared"
        else _serializer_over(model_class, ("amount", "pick"))
    )
    with _synthetic_table(model_class):
        schema, create_input, update_input = _blank_columns_schema(serializer_cls, model_class)
        if operation == "create":
            payload = _run_row_write(schema, create_input, data)
            stored: list[object] = []
        else:
            row = model_class._default_manager.create(amount=7, pick=1)
            payload = _run_row_write(schema, update_input, data, saved_pk(row))
            stored = [7]
        assert payload == {"result": None, "errors": errors}
        assert list(model_class._default_manager.values_list("amount", flat=True)) == stored


@pytest.mark.django_db(transaction=True)
def test_save_time_null_filled_in_by_model_save_writes() -> None:
    """A model ``save()`` that fills an omitted ``blank=True, null=False`` column in writes.

    The diagnosis reads the attempted row only after its save failed (django-trac 13776):
    the omitted ``amount`` reaches ``save()`` as ``None``, the override stores ``5`` and
    the row is written with no error.
    """

    class FilledAmountRow(Model):
        amount: _Int = models.IntegerField(blank=True)

        class Meta:
            app_label = "products"
            managed = False

        @override
        def save(self, *args: object, **kwargs: object) -> None:
            if vars(self)["amount"] is None:
                self.amount = 5
            call_forwarded(super().save, args, kwargs)

    with _synthetic_table(FilledAmountRow):
        schema, create_input, _ = _blank_columns_schema(
            _serializer_over(FilledAmountRow, ("amount",)),
            FilledAmountRow,
        )
        payload = _run_row_write(schema, create_input, {})
        assert json_at(payload, "errors") == []
        assert list(FilledAmountRow._default_manager.values_list("amount", flat=True)) == [5]


def _raise_integrity_error(_serializer: object, _validated_data: object) -> NoReturn:
    """A ``create()`` that saves nothing of the backing model and raises ``IntegrityError``."""
    raise IntegrityError("refused before any row was saved")


@pytest.mark.django_db(transaction=True)
def test_save_time_integrity_error_with_no_attempted_row_is_the_constraint_envelope() -> None:
    """A ``create()`` that raises without saving the backing model is the ``"__all__"`` envelope.

    The omitted ``amount`` would be ``None`` on any row built from the validated data, but
    no row of the backing model was attempted, so nothing names the column and the
    failure stays the ``constraint`` envelope.
    """
    model_class = _blank_columns_model("UnsavedColumnsRow")
    serializer_cls = _serializer_over(
        model_class,
        ("amount", "pick"),
        methods={"create": _raise_integrity_error},
    )
    with _synthetic_table(model_class):
        schema, create_input, _ = _blank_columns_schema(serializer_cls, model_class)
        payload = _run_row_write(schema, create_input, {})
        assert payload == {"result": None, "errors": _CONSTRAINT_ENVELOPE}


@pytest.mark.django_db(transaction=True)
def test_save_time_integrity_error_ignores_another_threads_attempted_row() -> None:
    """A row another thread attempts during the save is never this write's diagnosis.

    The ``create()`` starts a second thread that sends ``pre_save`` for a backing-model
    row holding ``None`` on ``amount``, joins it, then raises ``IntegrityError`` without
    saving a row of its own. The witness records attempts on the owning thread only, so
    the failure stays the ``"__all__"`` envelope instead of ``amount``'s ``null`` error.
    """
    model_class = _blank_columns_model("ConcurrentColumnsRow")

    def _create_racing(_serializer: object, _validated_data: object) -> NoReturn:
        errors: list[BaseException] = []

        def _other_request_save() -> None:
            pre_save.send(
                sender=model_class,
                instance=model_class(pick=1),
                raw=False,
                using="default",
                update_fields=None,
            )

        thread = threading.Thread(target=run_capturing, args=(errors, _other_request_save))
        thread.start()
        thread.join()
        assert errors == []
        raise IntegrityError("refused while another request saved")

    serializer_cls = _serializer_over(
        model_class,
        ("amount", "pick"),
        methods={"create": _create_racing},
    )
    with _synthetic_table(model_class):
        schema, create_input, _ = _blank_columns_schema(serializer_cls, model_class)
        payload = _run_row_write(schema, create_input, {})
        assert payload == {"result": None, "errors": _CONSTRAINT_ENVELOPE}


@pytest.mark.django_db(transaction=True)
def test_save_time_integrity_error_skips_a_column_outside_update_fields() -> None:
    """A ``None`` column the refused save leaves out of ``update_fields`` is never the diagnosis.

    The model ``save()`` narrows every update to ``update_fields=["label"]``, so the client's
    ``null`` on ``amount`` never reaches the ``UPDATE``; the declared ``label`` field carries
    no ``UniqueValidator``, so the database refuses the duplicate ``label`` instead. The
    witness records the save's ``update_fields`` with its row, and the diagnosis reads only
    the columns that save writes, so the failure is the ``"__all__"`` ``constraint``
    envelope, not ``amount``'s ``null`` error. Nothing is written.
    """

    class NarrowedSaveRow(Model):
        amount: _Int = models.IntegerField(blank=True)
        label: _Text = models.TextField(unique=True)

        class Meta:
            app_label = "products"
            managed = False

        @override
        def save(self, *args: object, **kwargs: object) -> None:
            if not self._state.adding:
                kwargs["update_fields"] = ["label"]
            call_forwarded(super().save, args, kwargs)

    serializer_cls = _serializer_over(
        NarrowedSaveRow,
        ("amount", "label"),
        {
            "amount": serializers.IntegerField(required=False, allow_null=True),
            "label": serializers.CharField(),
        },
    )
    with _synthetic_table(NarrowedSaveRow):
        schema, _, update_input = _blank_columns_schema(serializer_cls, NarrowedSaveRow)
        _ = NarrowedSaveRow._default_manager.create(amount=7, label="taken")
        row = NarrowedSaveRow._default_manager.create(amount=8, label="mine")
        payload = _run_row_write(
            schema,
            update_input,
            {"amount": None, "label": "taken"},
            saved_pk(row),
        )
        assert payload == {"result": None, "errors": _CONSTRAINT_ENVELOPE}
        stored = NarrowedSaveRow._default_manager.order_by("pk").values_list("amount", "label")
        assert list(stored) == [(7, "taken"), (8, "mine")]


@pytest.mark.parametrize("update_field", ["category", "category_id"])
@pytest.mark.django_db
def test_save_time_null_inside_update_fields_by_name_or_attname_is_field_keyed(
    update_field: str,
) -> None:
    """A ``None`` column the refused save names in ``update_fields`` keeps its ``null`` error.

    Django accepts an ``update_fields`` entry by field name or by ``attname``; a custom
    ``update()`` that saves the cleared foreign key under either spelling writes the column,
    so the database's ``NOT NULL`` refusal is that column's field-keyed ``null`` error, and
    the stored key is unchanged.
    """
    seed_data(1)
    item = product_models.Item.objects.select_related("category").first()
    assert item is not None
    category_pk = item.category_id

    class NarrowedUpdateSerializer(ModelSerializerBase[product_models.Item]):
        category: _PkRelation[product_models.Category] = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
            allow_null=True,
        )

        class Meta:
            model = product_models.Item
            fields = ("category",)

        @override
        def update(
            self,
            instance: product_models.Item,
            validated_data: dict[str, object],
        ) -> product_models.Item:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save(update_fields=[update_field])
            return instance

    mutation_cls = _bind_item_serializer_mutation(NarrowedUpdateSerializer, operation="update")
    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            item,
            {"category": None},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.messages, fe.codes) for fe in result.errors] == [
        ("categoryId", ["This field cannot be null."], ["null"]),
    ]
    stored = product_models.Item.objects.get(pk=item.pk)
    assert stored.category_id == category_pk


@pytest.mark.django_db
def test_save_time_diagnosis_never_loads_a_deferred_column_the_save_left_out() -> None:
    """A deferred column a refused save leaves out of ``update_fields`` is skipped unread.

    Django saves a deferred-load row under ``update_fields`` naming only its loaded
    columns, so the diagnosis skips every other column before reading it: reading the
    deferred ``description`` would load it from the connection the ``IntegrityError`` left,
    for a column the save never wrote. The refusal (a duplicate unique name) is the
    ``"__all__"`` ``constraint`` envelope and no query runs.
    """
    seed_data(2)
    first, second = product_models.Category.objects.order_by("pk")[:2]
    loaded = product_models.Category.objects.defer("description").get(pk=first.pk)
    key_map: ErrorKeyMap = {"name": ("name", None), "description": ("description", None)}
    with serializer_resolvers._write_witness(
        _as_serializer_mutation(type("DeferredWitnessMut", (), {})),
        product_models.Category,
        "default",
    ) as witness:
        loaded.name = second.name
        with pytest.raises(IntegrityError) as excinfo, transaction.atomic():
            loaded.save()
        [(row, update_fields, _sender)] = witness.attempted
        assert row is loaded
        # The refused save pairs, so the diagnosis below reaches the column walk.
        assert refused_save(witness.attempted, excinfo.value) == (loaded, update_fields)
        assert update_fields is not None
        assert "name" in update_fields
        assert "description" not in update_fields
        with CaptureQueriesContext(connections["default"]) as queries:
            errors = serializer_resolvers._attempted_row_integrity_errors(
                witness.attempted,
                excinfo.value,
                key_map,
            )
    assert [(fe.field, fe.codes) for fe in errors] == [(NON_FIELD_ERROR_KEY, ["constraint"])]
    assert len(queries) == 0


# ===========================================================================
# A save-time validation error after a partial write rolls back
# ===========================================================================


# ===========================================================================
# get_serializer_kwargs precedence / framework merge (hermetic)
# ===========================================================================


def _basic_item_serializer() -> type[ModelSerializerBase[product_models.Item]]:
    class BasicItemSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    return BasicItemSerializer


@pytest.mark.django_db
def test_serializer_kwargs_injects_partial_true_on_update_never_create() -> None:
    """The framework injects `partial=True` for update (instance present), never for create."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    create_kwargs = serializer_resolvers._serializer_kwargs(
        mutation_cls,
        info,
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert "partial" not in create_kwargs

    instance = product_models.Category(pk=1)
    update_kwargs = serializer_resolvers._serializer_kwargs(
        mutation_cls,
        info,
        final_data={"name": "X"},
        instance=instance,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert update_kwargs["partial"] is True


@pytest.mark.django_db
def test_serializer_kwargs_sets_framework_request_unconditionally() -> None:
    """`context["request"]` is set to the framework request, defaulting `data` to `provided_data`."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    kwargs = serializer_resolvers._serializer_kwargs(
        mutation_cls,
        info,
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert kwargs["data"] == {"name": "X"}
    assert _serializer_context(kwargs)["request"] is request


@pytest.mark.django_db
def test_serializer_kwargs_merges_override_context_keys_keeping_framework_request() -> None:
    """An override's non-`request` context keys are kept; the framework `request` always wins."""

    class OverridingMutation(SerializerMutation):
        class Meta:
            serializer_class = _basic_item_serializer()
            operation = "create"

        @override
        def get_serializer_kwargs(
            self,
            info: strawberry.Info,
            *,
            data: Mapping[str, object],
            hook_context: SerializerHookContext,
        ) -> dict[str, object]:
            kwargs = super().get_serializer_kwargs(info, data=data, hook_context=hook_context)
            kwargs["context"] = {"extra": "value"}
            return kwargs

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(OverridingMutation)

    finalize_django_types()
    DjangoSchema(query=PingQuery, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))
    kwargs = serializer_resolvers._serializer_kwargs(
        OverridingMutation,
        info,
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert _serializer_context(kwargs)["extra"] == "value"  # the override key is kept
    assert _serializer_context(kwargs)["request"] is request  # the framework request wins


@pytest.mark.django_db
def test_serializer_kwargs_bare_httprequest_info_context_fallback() -> None:
    """`request_from_info` resolves a bare `HttpRequest` `info.context` (the no-`.request` fallback)."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    bare_request = HttpRequest()
    bare_request.user = User(username="u")
    # `info.context` IS the HttpRequest (no `.request` attribute layer).
    info = make_info(context=bare_request)
    kwargs = serializer_resolvers._serializer_kwargs(
        mutation_cls,
        info,
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert _serializer_context(kwargs)["request"] is bare_request


# ===========================================================================
# Config assessment: recorded GlobalID strategy consumed, not the live setting
# ===========================================================================


def test_resolvers_source_has_no_live_strategy_reads_grep_guard() -> None:
    """DoD grep-guard: `rest_framework/resolvers.py` reads no settings and no strategy resolver.

    The module references neither `conf.settings` nor `_resolve_globalid_strategy`.

    A relation `GlobalID` is decoded against the target type's RECORDED
    `effective_globalid_strategy` via `decode_model_global_id` (resolved once at
    finalization), never a per-request settings re-read / re-validation on the query
    path.
    """
    source = inspect.getsource(serializer_resolvers)
    assert "conf.settings" not in source
    assert "_resolve_globalid_strategy" not in source


@pytest.mark.django_db
def test_relation_decode_consumes_recorded_strategy_after_strategy_resolver_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After finalize, a serializer relation decode still resolves with `_resolve_globalid_strategy` broken.

    The behavioral backstop for the grep-guard: monkeypatch
    `types/relay.py::_resolve_globalid_strategy` to RAISE (as if a per-request
    re-read were attempted), then drive the relation decode - it must still resolve
    through the target type's recorded `effective_globalid_strategy`, proving the
    query path never re-reads the live setting.
    """
    seed_data(0)

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    (category,) = categories_from_seed(("StrategyCat", False))
    gid = global_id_for(CategoryT, saved_pk(category))

    def _boom(*_args: object, **_kwargs: object) -> NoReturn:
        raise AssertionError("_resolve_globalid_strategy must not run on the query path")

    monkeypatch.setattr(relay_module, "_resolve_globalid_strategy", _boom)

    pk, error = serializer_resolvers._decode_relation_single(
        gid,
        graphql_name="categoryId",
        related_model=product_models.Category,
        key_attname=None,
        # A GlobalID decode reads the executing schema off ``info``.
        info=make_info(),
    )
    assert error is None
    assert pk == saved_pk(category)


# ===========================================================================
# Sync + async boundary + SyncMisuseError
# ===========================================================================


@pytest.mark.django_db
def test_relation_decode_async_get_queryset_from_sync_raises_sync_misuse() -> None:
    """A relation target with an `async def` `get_queryset` raises `SyncMisuseError` in sync decode."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        # basedpyright: deliberately async on the sync path: the coroutine is the input the guard refuses
        async def get_queryset(  # pyright: ignore[reportIncompatibleMethodOverride]
            cls,
            queryset: QuerySet[library_models.Genre],
            info: strawberry.Info,
        ) -> QuerySet[library_models.Genre]:  # async hook on the sync path
            return queryset

    del GenreT
    genre = library_models.Genre.objects.create(name="AsyncGenre")
    with pytest.raises(SyncMisuseError):
        serializer_resolvers._decode_relation_single(
            saved_pk(genre),
            graphql_name="genreId",
            related_model=library_models.Genre,
            key_attname=None,
            info=unread_info(),
        )


# ===========================================================================
# Structured error codes + paths
# ===========================================================================


def test_flattener_preserves_error_detail_codes_and_path() -> None:
    """A DRF ``ErrorDetail.code`` -> ``codes``; the dotted key -> structured ``path`` segments."""
    errors = {
        "name": [ErrorDetail("This field is required.", code="required")],
        "items": [{"qty": [ErrorDetail("Not valid.", code="invalid")]}],
    }
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    by_field = {fe.field: (fe.codes, fe.path) for fe in flat}
    assert by_field["name"] == (["required"], ["name"])
    assert by_field["items.0.qty"] == (["invalid"], ["items", "0", "qty"])


def test_flattener_root_non_field_error_has_empty_path() -> None:
    """A ROOT non-field error is ``field="__all__"`` with an EMPTY ``path`` (the documented rule)."""
    drf_key = api_settings.NON_FIELD_ERRORS_KEY
    errors = {drf_key: [ErrorDetail("Model-wide problem.", code="invalid")]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert fe.field == NON_FIELD_ERROR_KEY
    assert fe.path == []
    assert fe.codes == ["invalid"]


def test_flattener_nested_non_field_error_keeps_all_sentinel_segment() -> None:
    """A NESTED non-field error keeps the ``"__all__"`` sentinel as its final path segment."""
    drf_key = api_settings.NON_FIELD_ERRORS_KEY
    errors = {"items": [{drf_key: [ErrorDetail("Cross-field.", code="invalid")]}]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert fe.path == ["items", "0", NON_FIELD_ERROR_KEY]


def test_flattener_plain_string_leaf_has_no_codes() -> None:
    """A plain (non-``ErrorDetail``) string leaf yields no codes (only real codes are surfaced)."""
    flat = serializer_resolvers.serializer_errors_to_field_errors({"name": ["plain string"]}, {})
    (fe,) = flat
    assert fe.codes == []
    assert fe.path == ["name"]


def test_flattener_bare_error_detail_preserves_code() -> None:
    """A bare DRF ``ErrorDetail`` leaf still preserves its single code."""
    flat = serializer_resolvers.serializer_errors_to_field_errors(
        {"name": ErrorDetail("Invalid.", code="invalid")},
        {},
    )
    (fe,) = flat
    assert fe.codes == ["invalid"]
    assert fe.path == ["name"]


# ===========================================================================
# Re-fetch plan shape - the plan-state half of a live-tier contract
# ===========================================================================
# The behavioral half (the emitted SQL names the undeferred columns) is earned
# live in `examples/fakeshop/test_query/test_products_api.py`. The plan OBJECT
# the optimizer stashed is not reachable from a real query, so it is pinned here.


def _build_serializer_refetch_schema() -> tuple[DjangoSchema, type[DjangoType]]:
    """Declare Item/Category Relay primaries + a create `SerializerMutation`, optimizer on."""

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    class WriteItem(SerializerMutation):
        class Meta:
            serializer_class = _basic_item_serializer()
            operation = "create"
            permission_classes = [AllowAll]

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(WriteItem)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(query=PingQuery, mutation=Mutation, extensions=[lambda: optimizer])
    del ItemT
    return schema, CategoryT


@pytest.mark.django_db
def test_serializer_refetch_introduces_no_projection() -> None:
    """The serializer re-fetch plan KEEPS `select_related` and introduces no `.only(...)`.

    A relation-selecting response plans the relation through `select_related`, and
    the plan introduces no projection because the operation is a MUTATION - the
    re-fetch rides the same path the form flavor does. `select_related` is
    load-bearing here, not decoration: `DST_OPTIMIZER_PLAN` is last-wins
    introspection data, so it is what proves the captured plan IS the re-fetch plan.
    """
    seed_data(0)
    schema, CategoryT = _build_serializer_refetch_schema()
    (category,) = categories_from_seed(("G2Cat", False))
    request = HttpRequest()
    request.user = User(username="u")
    ctx = SimpleNamespace(request=request)

    result = schema.execute_sync(
        "mutation($d: BasicItemSerializerInput!){ writeItem(data:$d){ "
        "node{ name category{ name } } errors{ field } } }",
        variable_values={
            "d": {"name": "G2Widget", "categoryId": global_id_for(CategoryT, saved_pk(category))},
        },
        context_value=ctx,
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    assert result.data["writeItem"]["errors"] == []

    plan = require_instance(read_attr(ctx, "dst_optimizer_plan"), OptimizationPlan)
    # The relation selection (`category { name }`) is planned via select_related.
    assert plan.select_related == ("category",)
    # The columns are recorded; a MUTATION plan never introduces a projection.
    assert plan.introduce_projection is False
    assert plan.only_fields == ("name", "category_id", "category__name")


# ===========================================================================
# Batched multi-relation visibility internals (SQL batching + hidden member
# envelopes are live in ``test_library_api.py``).
# ===========================================================================


def test_relation_queryset_scope_pins_unregistered_raw_pk_relation_without_visibility() -> None:
    """A relation target without a registered primary gets NO visibility filter but IS still pinned.

    A raw-pk relation has no visibility contract to AND on, but DRF's own ``is_valid()``
    lookup must still run inside the transaction on the write alias, so
    the author's queryset is alias-pinned rather than left untouched.
    """

    class BranchSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.all(),
        )

    serializer = BranchSer()
    field = bound_fields(serializer)["branch"]
    fake = type(
        "RawPkMut",
        (),
        {
            "_injected_field_specs": [],
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branch",
                    graphql_name="branch",
                    target_name="branch",
                    kind=RELATION_SINGLE,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(fake),
            serializer,
            info=unread_info(),
        )
    # Pinned to the write alias; no visibility constraint added (no primary type registered).
    pinned = _related_queryset(field)
    assert queryset_db(pinned) == "default"
    assert not pinned.query.where
    assert pinned.query.select_for_update is False


class _QuerysetlessBranchRelation(serializers.PrimaryKeyRelatedField[library_models.Branch]):
    """A relation DRF accepts with ``queryset=None`` because it overrides ``get_queryset()``."""

    @override
    def get_queryset(self) -> QuerySet[library_models.Branch]:
        return library_models.Branch.objects.all()


def test_relation_queryset_scope_refuses_a_relation_with_no_queryset_attribute() -> None:
    """A relation whose ``queryset`` is ``None`` (a ``get_queryset()`` override) is refused.

    The scope composes onto the field's own ``queryset``, so there is nothing to pin or
    narrow; the refusal names the field instead of failing on ``None``.
    """

    class BranchSer(serializers.Serializer[object]):
        branch = _QuerysetlessBranchRelation(queryset=None)

    fake = type(
        "QuerysetlessMut",
        (),
        {
            "_injected_field_specs": [],
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branch",
                    graphql_name="branch",
                    target_name="branch",
                    kind=RELATION_SINGLE,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    with (
        pytest.raises(
            ConfigurationError,
            match=r"relation field 'branch' has no queryset at runtime \(got NoneType\)",
        ),
        write_pipeline("default", lock=False),
    ):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(fake),
            BranchSer(),
            info=unread_info(),
        )


@pytest.mark.django_db
def test_runtime_relation_over_another_model_is_refused_before_any_write() -> None:
    """A runtime relation queryset over another model than the schema recorded is refused.

    The schema-time ``category`` relates to ``Category``; the request-time ``get_fields()``
    swaps its queryset to ``Entry``. Scoping that queryset by ``Category`` visibility would
    link an ``Entry`` row by a coinciding pk, so the write step refuses before validation.
    """
    seed_data(1)

    class SwappedRelationSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def get_fields(self) -> dict[str, DRFField]:
            fields: dict[str, DRFField] = base_fields(super())
            if self.context.get("request") is not None:
                fields["category"] = serializers.PrimaryKeyRelatedField(
                    queryset=product_models.Entry.objects.all(),
                )
            return fields

    mutation_cls = _bind_item_serializer_mutation(SwappedRelationSerializer)
    (category,) = categories_from_seed(("SwappedCat", False))
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))
    items_before = product_models.Item.objects.count()
    with (
        pytest.raises(ConfigurationError, match="targets Entry at runtime but Category"),
        write_pipeline("default", lock=False),
    ):
        serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "SwappedItem", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert product_models.Item.objects.count() == items_before


def test_relation_queryset_scope_locks_when_pipeline_locks() -> None:
    """When the pipeline locks, the scoped relation queryset is a base-manager FOR UPDATE query."""

    class BranchSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.all(),
        )

    serializer = BranchSer()
    fake = type(
        "LockMut",
        (),
        {
            "_injected_field_specs": [],
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branch",
                    graphql_name="branch",
                    target_name="branch",
                    kind=RELATION_SINGLE,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    with write_pipeline("default", lock=True):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(fake),
            serializer,
            info=unread_info(),
        )
    scoped = _related_queryset(bound_fields(serializer)["branch"])
    assert scoped.query.select_for_update is True
    assert queryset_db(scoped) == "default"


@pytest.mark.django_db
def test_relation_queryset_scope_covers_injected_relation_specs() -> None:
    """A ``Meta.injected_fields`` relation gets the SAME pin + visibility + lock as an input relation.

    Injected relation values reach DRF's identical second lookup, so skipping their specs
    would leave an unpinned, unlocked, visibility-free queryset - the specs walk must cover
    the disjoint union of ``_input_field_specs`` and ``_injected_field_specs``. The
    visibility half is asserted by MEMBERSHIP (a row the registered primary type hides must
    be absent from the scoped queryset), not just by queryset flags.
    """

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Branch],
            info: strawberry.Info,
        ) -> QuerySet[library_models.Branch]:
            return queryset.exclude(name="HiddenInjected")

    del BranchT
    visible = library_models.Branch.objects.create(name="VisibleInjected", city="c")
    hidden = library_models.Branch.objects.create(name="HiddenInjected", city="c")

    class BranchSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.all(),
        )

    def _fake() -> type[object]:
        return type(
            "InjectedRelMut",
            (),
            {
                "_input_field_specs": [],
                "_injected_field_specs": [
                    InputFieldSpec(
                        input_attr="branch",
                        graphql_name="branch",
                        target_name="branch",
                        kind=RELATION_SINGLE,
                        related_model=library_models.Branch,
                    ),
                ],
            },
        )

    locked = BranchSer()
    with write_pipeline("default", lock=True):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(_fake()),
            locked,
            info=unread_info(),
        )
    scoped = _related_queryset(bound_fields(locked)["branch"])
    assert queryset_db(scoped) == "default"
    assert scoped.query.select_for_update is True

    unlocked = BranchSer()
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(_fake()),
            unlocked,
            info=unread_info(),
        )
    visible_scoped = _related_queryset(bound_fields(unlocked)["branch"])
    assert visible in visible_scoped  # visibility-allowed row admitted
    assert hidden not in visible_scoped  # visibility-hidden row intersected OUT


@pytest.mark.django_db
@pytest.mark.parametrize("pipeline", ["unlocked", "locked"])
def test_relation_queryset_scope_admits_no_row_whose_to_field_key_is_null(pipeline: str) -> None:
    """DRF's lookup admits only rows a ``to_field`` relation can link, injected values included.

    The spec records the column the relation stores (``Branch.isil``); a branch without one
    would be stored as ``NULL``, so the scoped queryset leaves it out, locked or not, the
    same set the decode admits.
    """
    keyed = library_models.Branch.objects.create(name="KeyedInjected", isil="XX-KI")
    _ = library_models.Branch.objects.create(name="UnkeyedInjected")

    class BranchSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.all(),
        )

    fake = type(
        "InjectedKeyMut",
        (),
        {
            "_input_field_specs": [],
            "_injected_field_specs": [
                InputFieldSpec(
                    input_attr="branch",
                    graphql_name="branch",
                    target_name="branch",
                    kind=RELATION_SINGLE,
                    related_model=library_models.Branch,
                    key_attname="isil",
                ),
            ],
        },
    )
    serializer = BranchSer()
    with transaction.atomic(), write_pipeline("default", lock=pipeline == "locked"):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(fake),
            serializer,
            info=unread_info(),
        )
        scoped = _related_queryset(bound_fields(serializer)["branch"])
        assert list(scoped.values_list("pk", flat=True)) == [keyed.pk]


def test_relation_queryset_scope_cross_alias_author_queryset_fails_closed() -> None:
    """An author queryset EXPLICITLY routed to a different alias fails before validation."""

    class BranchSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.using("other").all(),
        )

    serializer = BranchSer()
    fake = type(
        "CrossAliasMut",
        (),
        {
            "_injected_field_specs": [],
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branch",
                    graphql_name="branch",
                    target_name="branch",
                    kind=RELATION_SINGLE,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    with (
        write_pipeline("default", lock=False),
        pytest.raises(ConfigurationError, match="routed to alias 'other'"),
    ):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(fake),
            serializer,
            info=unread_info(),
        )


def test_relation_queryset_scope_handles_many_related_field() -> None:
    """Many relation fields scope their child relation queryset through target visibility."""

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Branch],
            info: strawberry.Info,
        ) -> QuerySet[library_models.Branch]:
            return queryset.exclude(name="HiddenScope")

    class BranchesSer(serializers.Serializer[object]):
        branches: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Branch.objects.all(),
        )

    del BranchT
    serializer = BranchesSer()
    field = bound_fields(serializer)["branches"]
    fake = type(
        "ManyMut",
        (),
        {
            "_injected_field_specs": [],
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branches",
                    graphql_name="branches",
                    target_name="branches",
                    kind=RELATION_MULTI,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(fake),
            serializer,
            info=unread_info(),
        )
    assert _related_queryset(_child_relation(field)).query.where


@pytest.mark.django_db
def test_relation_queryset_scope_is_isolated_between_concurrent_serializer_instances() -> None:
    """Concurrent requests scope instance-local single/many fields without cross-bleed.

    DRF deep-copies a serializer class's declared fields into each runtime serializer instance.
    Synchronizing both requests inside ``get_queryset`` forces their visibility rewrites to
    interleave, pinning that ``_scope_relation_querysets_to_visibility`` mutates only those
    instance-local copies and never the shared declarations or a sibling request's fields.
    """
    scopes_met = threading.Barrier(2)

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Branch],
            info: strawberry.Info[object, object],
        ) -> QuerySet[library_models.Branch]:
            scopes_met.wait(timeout=5)
            request = read_attr(info.context, "request")
            return queryset.filter(city=read_attr(request, "visibility_city"))

    class BranchSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.all(),
        )
        branches: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Branch.objects.all(),
        )

    del BranchT
    library_models.Branch.objects.create(name="ConcurrentLeft", city="left")
    library_models.Branch.objects.create(name="ConcurrentRight", city="right")
    specs = [
        InputFieldSpec(
            input_attr="branch",
            graphql_name="branch",
            target_name="branch",
            kind=RELATION_SINGLE,
            related_model=library_models.Branch,
        ),
        InputFieldSpec(
            input_attr="branches",
            graphql_name="branches",
            target_name="branches",
            kind=RELATION_MULTI,
            related_model=library_models.Branch,
        ),
    ]
    mutation = type(
        "ConcurrentMut",
        (),
        {"_input_field_specs": specs, "_injected_field_specs": []},
    )
    declared_single_queryset = _related_queryset(declared_fields_of(BranchSer)["branch"])
    declared_many_queryset = _related_queryset(
        _child_relation(declared_fields_of(BranchSer)["branches"]),
    )

    def _scope_for(visibility_city: str) -> BranchSer:
        request = _CityRequest()
        request.visibility_city = visibility_city
        info = make_info(context=SimpleNamespace(request=request))
        serializer = BranchSer()
        # The pipeline context is a ContextVar - set it INSIDE this worker thread.
        with write_pipeline("default", lock=False):
            serializer_resolvers._scope_relation_querysets_to_visibility(
                _as_serializer_mutation(mutation),
                serializer,
                info,
            )
        return serializer

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(_scope_for, "left")
        right_future = executor.submit(_scope_for, "right")
        left_serializer = left_future.result(timeout=10)
        right_serializer = right_future.result(timeout=10)

    left_single = bound_fields(left_serializer)["branch"]
    right_single = bound_fields(right_serializer)["branch"]
    left_many = _child_relation(bound_fields(left_serializer)["branches"])
    right_many = _child_relation(bound_fields(right_serializer)["branches"])

    assert left_single is not right_single
    assert left_many is not right_many
    assert list(_related_queryset(left_single).values_list("name", flat=True)) == [
        "ConcurrentLeft",
    ]
    assert list(_related_queryset(left_many).values_list("name", flat=True)) == ["ConcurrentLeft"]
    assert list(_related_queryset(right_single).values_list("name", flat=True)) == [
        "ConcurrentRight",
    ]
    assert list(_related_queryset(right_many).values_list("name", flat=True)) == [
        "ConcurrentRight",
    ]
    assert _related_queryset(declared_fields_of(BranchSer)["branch"]) is declared_single_queryset
    assert (
        _related_queryset(_child_relation(declared_fields_of(BranchSer)["branches"]))
        is declared_many_queryset
    )


@pytest.mark.django_db
def test_save_kwargs_hook_validation_error_maps_to_field_error_envelope() -> None:
    """A DRF ``ValidationError`` raised BY the save-kwargs hook rides the documented mapping.

    The hook is invoked INSIDE the value-preserving, error-mapped closure - the same
    boundary as ``serializer.save()`` - so a hook-raised validation failure lands in the
    ``FieldError`` envelope, never as a top-level ``GraphQLError``.
    """
    seed_data(0)

    class PlainItemSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    def raising_save_kwargs(self: SerializerMutation, info: object, **_kwargs: object) -> NoReturn:
        del self, info  # the typed hook fixes these names; the body only raises
        raise serializers.ValidationError({"name": ["from the save-kwargs hook"]})

    mutation_cls = _bind_item_serializer_mutation(PlainItemSerializer)
    mutation_cls.get_serializer_save_kwargs = raising_save_kwargs
    (category,) = categories_from_seed(("HookErrCat", False))
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "OK", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.messages) for fe in result.errors] == [
        ("name", ["from the save-kwargs hook"]),
    ]


# ===========================================================================
# Framework-owned serializer kwargs + saved-result validation
# ===========================================================================


def _info_with_request() -> strawberry.Info[object, object]:
    request = HttpRequest()
    request.user = User(username="u")
    return make_info(context=SimpleNamespace(request=request))


@pytest.mark.django_db
def test_serializer_kwargs_sets_write_alias_in_context() -> None:
    """The framework sets ``context['write_alias']`` to the pipeline's pinned alias."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    kwargs = serializer_resolvers._serializer_kwargs(
        mutation_cls,
        _info_with_request(),
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert _serializer_context(kwargs)["write_alias"] == "default"


def _saved_result_fixture() -> type[object]:
    """A fake mutation for the saved-result validation tests."""
    return type(
        "SavedMut",
        (),
        {"_mutation_meta": SimpleNamespace(model=product_models.Item)},
    )


@pytest.mark.django_db
def test_saved_result_wrong_model_is_configuration_error() -> None:
    """A ``save()`` returning a non-model / wrong-model value fails loud before the re-fetch."""
    fake = _saved_result_fixture()
    with pytest.raises(ConfigurationError, match="must persist and return the written Item row"):
        serializer_resolvers._checked_saved_result(
            _as_serializer_mutation(fake),
            object(),
        )


@pytest.mark.django_db
def test_saved_result_unsaved_instance_is_configuration_error() -> None:
    """A ``save()`` returning an UNSAVED instance (pk None) fails loud."""
    fake = _saved_result_fixture()
    unsaved = product_models.Item(name="x")
    with pytest.raises(ConfigurationError, match="must persist and return the written Item row"):
        serializer_resolvers._checked_saved_result(
            _as_serializer_mutation(fake),
            unsaved,
        )


@pytest.mark.django_db
def test_saved_result_spoofed_pk_on_never_persisted_instance_is_configuration_error() -> None:
    """A never-persisted instance carrying a SPOOFED pk fails loud (would launder an existing row)."""
    seed_data(1)
    fake = _saved_result_fixture()
    (category,) = categories_from_seed(("SpoofCat", False))
    (real,) = items_from_seed(category, ("Real", False))
    product_models.Item.objects.exclude(pk__in=[saved_pk(real)]).delete()
    product_models.Entry.objects.filter(item_id__in=[saved_pk(real)]).delete()
    spoofed = product_models.Item(pk=saved_pk(real), name="Spoof")  # adding=True, _state.db=None
    with pytest.raises(ConfigurationError, match="must persist and return the written Item row"):
        serializer_resolvers._checked_saved_result(
            _as_serializer_mutation(fake),
            spoofed,
        )


def test_write_witness_blocks_cross_alias_pre_save() -> None:
    """The witness's ``pre_save`` guard rejects a cross-alias write BEFORE it executes.

    The post-hoc alias check on the returned row could only detect an escaped write after
    it was already committed outside the pinned transaction; the guard fires at the signal,
    so the query never runs. Same-alias writes pass; other threads are untouched (each
    request installs its own thread-scoped witness): another thread's save is neither
    recorded as written nor as attempted on this one, and a save that completes is no
    longer an attempt.
    """
    fake = type("WitnessMut", (), {})
    with serializer_resolvers._write_witness(
        _as_serializer_mutation(fake),
        product_models.Item,
        "default",
    ) as witness:
        with pytest.raises(ConfigurationError, match="attempted to save"):
            pre_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                using="other",
            )
        # Same-alias writes pass through the guard untouched, and are this thread's attempts.
        own_attempt = product_models.Item(name="x")
        pre_save.send(
            sender=product_models.Item,
            instance=own_attempt,
            using="default",
        )
        [(row, update_fields, sender)] = witness.attempted
        assert row is own_attempt
        assert update_fields is None
        # The record names the call that sent ``pre_save``: this test's own frame.
        assert sender is inspect.currentframe()

        # A DIFFERENT thread's cross-alias save is not this request's to police - and its
        # writes are not recorded on this request's witness either.

        errors: list[BaseException] = []

        def _other_thread_save() -> None:
            pre_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                using="other",
            )
            post_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                created=True,
                using="default",
            )

        thread = threading.Thread(target=run_capturing, args=(errors, _other_thread_save))
        thread.start()
        thread.join()
        assert errors == []
        # The other thread's save never lands on this witness, written or attempted.
        assert witness.written == []
        assert len(witness.attempted) == 1
        assert witness.attempted[0][0] is own_attempt

        # This thread's save completing takes its row back out of the attempts.
        post_save.send(
            sender=product_models.Item,
            instance=own_attempt,
            created=True,
            using="default",
        )
        assert [row for row, *_ in witness.written] == [own_attempt]
        assert witness.attempted == []


def _execute_nothing(*_args: object) -> None:
    return None


def test_pipeline_alias_guard_rejects_every_statement_on_non_pinned_alias() -> None:
    """The pipeline's alias guard rejects ALL SQL on a non-pinned connection - no classification.

    A lexical read/write keyword test is bypassable (leading SQL comments, PostgreSQL
    ``EXPLAIN ANALYZE UPDATE`` which executes the write, write-capable functions invoked
    through ``SELECT``), so the guard installed around the pipeline's consumer-reachable
    phases raises on EVERY statement issued on a non-pinned alias - reads included - and
    is removed once the guarded phase exits.
    """
    extra = dict(connections.databases["default"])
    extra["NAME"] = ":memory:"
    connections.databases["mirror_alias"] = extra
    try:
        mirror = connections["mirror_alias"]
        baseline = len(mirror.execute_wrappers)
        with pipeline_alias_guard("NetMut", "default"):
            # Installed on the non-pinned alias for the phase...
            assert len(mirror.execute_wrappers) == baseline + 1
            guard = mirror.execute_wrappers[-1]
            for statement in (
                "UPDATE t SET x = 1",
                "/* hide */ INSERT INTO t VALUES (1)",
                "EXPLAIN ANALYZE UPDATE t SET x = 1",
                "SELECT write_capable_function()",
                "SELECT 1",
            ):
                with pytest.raises(ConfigurationError, match="SQL statement was issued"):
                    guard(_execute_nothing, statement, None, False, {})  # noqa: FBT003 - mirrors execute_wrapper(execute, sql, params, many, context)
        # ... and removed once the guarded phase exits.
        assert len(mirror.execute_wrappers) == baseline
    finally:
        connections["mirror_alias"].close()
        del connections["mirror_alias"]
        del connections.databases["mirror_alias"]


def test_pipeline_alias_guard_auth_alias_access_is_scoped_to_the_authorization_phase() -> None:
    """Auth-alias statements pass the guard ONLY while the authorization phase is open.

    A divergent read/write router keeps auth off the write alias, so the authorization
    phase permits queries on the identified auth aliases. The guard does NOT lexically
    classify them (a keyword test cannot safely authorize cross-alias execution - the
    rolled-back barrier transaction is the real boundary, exercised in the
    ``authorization_phase`` rollback test), so read AND write-shaped statements pass here;
    the scoping is what matters - before the phase opens and after it closes the same auth
    alias is back to reject-everything, so decode / hooks / validation cannot reach it.
    """
    extra = dict(connections.databases["default"])
    extra["NAME"] = ":memory:"
    connections.databases["auth_mirror"] = extra
    sentinel = object()

    def _execute(
        sql: object,
        params: object,
        many: object,
        context: object,
    ) -> object:
        del sql, params, many, context
        return sentinel

    try:
        mirror = connections["auth_mirror"]
        with write_pipeline("default", lock=False), pipeline_alias_guard("AuthMut", "default"):
            guard = mirror.execute_wrappers[-1]
            ctx = require_write_pipeline()
            # BEFORE the phase: every statement on the non-pinned alias is rejected.
            with pytest.raises(ConfigurationError, match="SQL statement was issued"):
                guard(_execute, "SELECT 1", None, False, {})  # noqa: FBT003 - mirrors execute_wrapper(execute, sql, params, many, context)
            # DURING the phase (flag toggled directly here; the rolled-back barrier
            # that makes this safe is proven separately): statements pass - read AND
            # write-shaped, since the barrier transaction, not lexical classification,
            # is the boundary.
            ctx.auth_phase = True
            ctx.auth_aliases = frozenset({"auth_mirror"})
            try:
                assert guard(_execute, "SELECT 1", None, False, {}) is sentinel  # noqa: FBT003 - mirrors execute_wrapper(execute, sql, params, many, context)
                assert (
                    guard(_execute, "UPDATE auth_permission SET x = 1", None, False, {})  # noqa: FBT003 - mirrors execute_wrapper(execute, sql, params, many, context)
                    is sentinel
                )
            finally:
                ctx.auth_phase = False
                ctx.auth_aliases = frozenset()
            # AFTER the phase closes: rejected again.
            with pytest.raises(ConfigurationError, match="SQL statement was issued"):
                guard(_execute, "SELECT 1", None, False, {})  # noqa: FBT003 - mirrors execute_wrapper(execute, sql, params, many, context)
    finally:
        connections["auth_mirror"].close()
        del connections["auth_mirror"]
        del connections.databases["auth_mirror"]


@pytest.mark.skipif(
    connections["default"].vendor != "sqlite",
    reason="builds a SQLite :memory: auth alias and reads SQLite's PRAGMA query_only refusal",
)
def test_authorization_phase_enforces_db_read_only_on_non_pinned_auth_aliases(
    django_db_blocker: pytest_django.DjangoDbBlocker,
) -> None:
    """The security boundary: a write on a non-pinned auth alias is REJECTED by the database.

    ``authorization_phase`` puts each non-pinned auth alias in a database-enforced read-only
    transaction (SQLite ``PRAGMA query_only``), so a permission backend's write is refused by
    the server itself - not merely rolled back. Forced rollback alone is not portable (non-
    transactional tables, implicitly-committed DDL, effects that outlive a rollback), so the
    barrier is backed by the DB's own read-only enforcement. Reads still pass; once the phase
    ends the connection is restored to writable.
    """
    extra = dict(connections.databases["default"])
    extra["NAME"] = ":memory:"
    connections.databases["auth_barrier"] = extra
    # A throwaway :memory: alias managed by hand (no fixture DB, no isolation
    # concern), so the pytest-django access block is explicitly lifted for it.
    with django_db_blocker.unblock():
        try:
            conn = connections["auth_barrier"]
            with conn.cursor() as cursor:
                cursor.execute("CREATE TABLE probe (id INTEGER PRIMARY KEY)")
                cursor.execute("INSERT INTO probe (id) VALUES (1)")
            # Pinned to ``default``; ``auth_barrier`` is a non-pinned auth alias.
            with (
                write_pipeline("default", lock=False),
                authorization_phase({"auth_barrier"}),
                conn.cursor() as cursor,
            ):
                # Reads are permitted inside the read-only barrier.
                cursor.execute("SELECT COUNT(*) FROM probe")
                assert _first_column(cursor) == 1
                # A write is refused by the database itself (read-only transaction).
                with pytest.raises(OperationalError, match="readonly"):
                    cursor.execute("INSERT INTO probe (id) VALUES (2)")
            # The write never happened, and the connection is writable again post-phase.
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM probe")
                assert _first_column(cursor) == 1
                cursor.execute("INSERT INTO probe (id) VALUES (3)")
                cursor.execute("SELECT COUNT(*) FROM probe")
                assert _first_column(cursor) == 2
        finally:
            # Django's SQLite ``close()`` keeps a ``:memory:`` database open, so the
            # throwaway handle is closed through the backend-neutral base ``close()``
            # before its alias is dropped.
            BaseDatabaseWrapper.close(connections["auth_barrier"])
            del connections["auth_barrier"]
            del connections.databases["auth_barrier"]


def test_pipeline_alias_guard_blocks_cross_alias_pre_save_and_ignores_other_threads() -> None:
    """The guard's ``pre_save`` receiver: cross-alias saves fail early, same-alias and other threads pass."""
    with pipeline_alias_guard("GuardMut", "default"):
        with pytest.raises(ConfigurationError, match="attempted to save"):
            pre_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                using="other",
            )
        # Same-alias saves pass through the guard untouched.
        pre_save.send(
            sender=product_models.Item,
            instance=product_models.Item(name="x"),
            using="default",
        )

        # A DIFFERENT thread's cross-alias save is not this request's to police.
        errors: list[BaseException] = []

        def _other_thread_save() -> None:
            pre_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                using="other",
            )

        thread = threading.Thread(target=run_capturing, args=(errors, _other_thread_save))
        thread.start()
        thread.join()
        assert errors == []


@pytest.mark.django_db
def test_saved_result_happy_path_returns_saved() -> None:
    """A persisted row of the backing model passes through unchanged on update."""
    seed_data(1)
    fake = _saved_result_fixture()
    (category,) = categories_from_seed(("OkCat", False))
    (item,) = items_from_seed(category, ("OkItem", False))
    product_models.Item.objects.exclude(pk__in=[saved_pk(item)]).delete()
    product_models.Entry.objects.filter(item_id__in=[saved_pk(item)]).delete()
    assert serializer_resolvers._checked_saved_result(_as_serializer_mutation(fake), item) is item


def test_validator_querysets_are_recursively_pinned_to_write_alias() -> None:
    """Field, serializer-level, and nested validator querysets share the write alias."""

    class ChildSerializer(serializers.Serializer[object]):
        name = serializers.CharField(
            validators=[
                UniqueValidator(queryset=product_models.Category.objects.all()),
            ],
        )

    class ParentSerializer(serializers.Serializer[object]):
        name = serializers.CharField(
            validators=[
                UniqueValidator(queryset=product_models.Item.objects.all()),
            ],
        )
        category: _PkRelation[product_models.Category] = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
        )
        child = ChildSerializer()

        class Meta:
            validators = [
                UniqueTogetherValidator(
                    queryset=product_models.Item.objects.all(),
                    fields=("name", "category"),
                ),
            ]

    serializer = ParentSerializer(data={})
    serializer_resolvers._pin_validator_querysets(serializer, "shard_b")

    name_validator = bound_fields(serializer)["name"].validators[0]
    together_validator = serializer.validators[0]
    assert isinstance(name_validator, UniqueValidator)
    assert isinstance(together_validator, UniqueTogetherValidator)
    assert _validator_queryset_db(name_validator) == "shard_b"
    assert _validator_queryset_db(together_validator) == "shard_b"
    child = bound_fields(serializer)["child"]
    assert isinstance(child, serializers.Serializer)
    child_validator = bound_fields(child)["name"].validators[0]
    assert isinstance(child_validator, UniqueValidator)
    assert _validator_queryset_db(child_validator) == "shard_b"


@pytest.mark.django_db
def test_validator_pinning_leaves_a_read_only_base_serializer_field_alone() -> None:
    """A nested plain ``BaseSerializer`` declares no ``.fields``, so the pinning walk stops at it.

    Class validation drops read-only fields from the write surface, so a mutation over a
    serializer that renders through a ``BaseSerializer`` subclass (``source="*"``) declares
    cleanly; its write must reach ``is_valid()`` instead of raising on the pinning walk.
    """
    seed_data(1)

    class SummarySerializer(serializers.BaseSerializer[product_models.Item]):
        @override
        def to_representation(self, instance: product_models.Item) -> dict[str, str]:
            return {"name": instance.name}

    class SummarizedItemSerializer(ModelSerializerBase[product_models.Item]):
        summary = SummarySerializer(source="*", read_only=True)

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "summary")

    category = product_models.Category.objects.first()
    mutation_cls = _bind_item_serializer_mutation(SummarizedItemSerializer)
    request = HttpRequest()
    request.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        assert category is not None
        saved = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "Summarized", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(saved, product_models.Item)
    assert saved.name == "Summarized"


def test_validator_queryset_pinning_replaces_shared_validator_per_serializer_instance() -> None:
    """Pinning one serializer cannot mutate the validator shared with another request."""
    shared = UniqueValidator(queryset=product_models.Item.objects.all())

    class SharedValidatorSerializer(serializers.Serializer[object]):
        name = serializers.CharField(validators=[shared])

    shard_serializer = SharedValidatorSerializer(data={})
    default_serializer = SharedValidatorSerializer(data={})
    assert bound_fields(shard_serializer)["name"].validators[0] is shared
    assert bound_fields(default_serializer)["name"].validators[0] is shared

    serializer_resolvers._pin_validator_querysets(shard_serializer, "shard_b")
    serializer_resolvers._pin_validator_querysets(default_serializer, "default")

    shard_validator = bound_fields(shard_serializer)["name"].validators[0]
    default_validator = bound_fields(default_serializer)["name"].validators[0]
    assert shard_validator is not shared
    assert default_validator is not shared
    assert shard_validator is not default_validator
    assert isinstance(shard_validator, UniqueValidator)
    assert isinstance(default_validator, UniqueValidator)
    assert _validator_queryset_db(shard_validator) == "shard_b"
    assert _validator_queryset_db(default_validator) == "default"
    assert _validator_queryset_db(shared) is None


def test_list_field_child_validator_querysets_are_pinned_and_isolated() -> None:
    """Composite field children execute validators and need per-request alias pinning too."""
    shared = UniqueValidator(queryset=product_models.Item.objects.all())

    class TagsSerializer(serializers.Serializer[object]):
        tags = serializers.ListField(child=serializers.CharField(validators=[shared]))

    shard_serializer = TagsSerializer(data={})
    default_serializer = TagsSerializer(data={})
    serializer_resolvers._pin_validator_querysets(shard_serializer, "shard_b")
    serializer_resolvers._pin_validator_querysets(default_serializer, "default")

    shard_tags = bound_fields(shard_serializer)["tags"]
    default_tags = bound_fields(default_serializer)["tags"]
    assert isinstance(shard_tags, serializers.ListField)
    assert isinstance(default_tags, serializers.ListField)
    shard_validator = list_child_of(shard_tags).validators[0]
    default_validator = list_child_of(default_tags).validators[0]
    assert shard_validator is not shared
    assert default_validator is not shared
    assert shard_validator is not default_validator
    assert isinstance(shard_validator, UniqueValidator)
    assert isinstance(default_validator, UniqueValidator)
    assert _validator_queryset_db(shard_validator) == "shard_b"
    assert _validator_queryset_db(default_validator) == "default"
    assert _validator_queryset_db(shared) is None


def test_validator_queryset_explicitly_routed_elsewhere_fails_closed() -> None:
    """An author-pinned validator queryset cannot escape the write transaction alias."""

    class RoutedValidatorSerializer(serializers.Serializer[object]):
        name = serializers.CharField(
            validators=[
                UniqueValidator(
                    queryset=product_models.Item.objects.using("other"),
                ),
            ],
        )

    serializer = RoutedValidatorSerializer(data={})
    with pytest.raises(ConfigurationError, match="routed to alias 'other'"):
        serializer_resolvers._pin_validator_querysets(serializer, "default")


@pytest.mark.django_db
def test_relation_queryset_scope_composes_with_author_queryset() -> None:
    """Visibility scoping AND-s the author's field queryset - never replaces it.

    A serializer author's own ``PrimaryKeyRelatedField(queryset=...)`` restriction is the base
    contract; visibility is an ADDITIONAL constraint. A visible-but-author-DISALLOWED row must
    still be rejected (replacing the author's queryset would admit it).
    """

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True  # default get_queryset: every branch is visible

    del BranchT
    allowed = library_models.Branch.objects.create(name="ScopeAllowed", city="allowed")
    other = library_models.Branch.objects.create(name="ScopeOther", city="other")

    class SingleSer(serializers.Serializer[object]):
        branch: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.filter(city="allowed"),
        )

    class ManySer(serializers.Serializer[object]):
        branches: _PkRelation[library_models.Branch] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Branch.objects.filter(city="allowed"),
        )

    single = SingleSer()
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(
                type(
                    "SingleMut",
                    (),
                    {
                        "_injected_field_specs": [],
                        "_input_field_specs": [
                            InputFieldSpec(
                                input_attr="branch",
                                graphql_name="branch",
                                target_name="branch",
                                kind=RELATION_SINGLE,
                                related_model=library_models.Branch,
                            ),
                        ],
                    },
                ),
            ),
            single,
            info=unread_info(),
        )
    single_qs = _related_queryset(bound_fields(single)["branch"])
    assert allowed in single_qs  # visible AND author-allowed
    assert other not in single_qs  # visible but author-DISALLOWED - the author's filter survives

    many = ManySer()
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            _as_serializer_mutation(
                type(
                    "ManyMut",
                    (),
                    {
                        "_injected_field_specs": [],
                        "_input_field_specs": [
                            InputFieldSpec(
                                input_attr="branches",
                                graphql_name="branches",
                                target_name="branches",
                                kind=RELATION_MULTI,
                                related_model=library_models.Branch,
                            ),
                        ],
                    },
                ),
            ),
            many,
            info=unread_info(),
        )
    many_qs = _related_queryset(_child_relation(bound_fields(many)["branches"]))
    assert allowed in many_qs
    assert other not in many_qs


# ===========================================================================
# Nested serializer inputs - decode internals
# ===========================================================================


def _nested_single_input_and_specs() -> tuple[type[object], list[InputFieldSpec]]:
    """Build a single-nested input (``detail`` -> ``{code}``) + its top reverse-map specs."""

    class Child(serializers.Serializer[object]):
        code = serializers.CharField()

    class Parent(serializers.Serializer[object]):
        detail = Child()

    cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    return cls, list(shape.field_specs)


def _nested_child_input_cls(top_cls: type[object]) -> Callable[..., object]:
    """Return the nested input class referenced by the top input's ``detail`` field."""
    definition = get_object_definition(top_cls, strict=True)
    field = next(f for f in definition.fields if f.python_name == "detail")
    field_type = field.type
    child_cls = field_type.of_type if isinstance(field_type, StrawberryContainer) else field_type
    assert isinstance(child_cls, type)
    return _keyword_constructor(child_cls)


def test_decode_nested_single_recurses_into_child() -> None:
    """A single nested input decodes recursively into a nested serializer-keyed dict."""
    top_cls, specs = _nested_single_input_and_specs()
    child_cls = _nested_child_input_cls(top_cls)
    data = _keyword_constructor(top_cls)(detail=child_cls(code="X"))
    provided, error = serializer_resolvers._decode_input_object(specs, data, info=unread_info())
    assert error is None
    assert provided == {"detail": {"code": "X"}}


def test_decode_nested_explicit_none_passes_through() -> None:
    """An explicit ``null`` nested value passes through unchanged (the serializer's validation decides)."""
    top_cls, specs = _nested_single_input_and_specs()
    data = _keyword_constructor(top_cls)(detail=None)
    provided, error = serializer_resolvers._decode_input_object(specs, data, info=unread_info())
    assert error is None
    assert provided == {"detail": None}


def test_decode_nested_single_error_short_circuits() -> None:
    """A decode error INSIDE a single nested input short-circuits with the nested error."""
    top_cls, specs = _nested_single_input_and_specs()
    child_cls = _nested_child_input_cls(top_cls)
    # A lone surrogate in the nested scalar trips the invalid-Unicode preflight inside the
    # nested decode, so the single-nested branch returns the error (keyed to the full path).
    data = _keyword_constructor(top_cls)(detail=child_cls(code="\ud800"))
    provided, error = serializer_resolvers._decode_input_object(specs, data, info=unread_info())
    assert provided == {}
    assert error is not None
    assert error.field == "detail.code"


# ===========================================================================
# Relation writes through the serializer write step
# ===========================================================================


def _bind_book_genres_mutation(
    serializer_cls: type[DRFSerializer],
    *,
    operation: str = "update",
) -> type[SerializerMutation]:
    """Declare + finalize a minimal Book/Genre `SerializerMutation` (M2M fixtures)."""
    op_value = operation

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    assert registry.get(library_models.Genre) is GenreT

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    assert registry.get(library_models.Book) is BookT

    class WriteBook(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = op_value
            permission_classes = [AllowAll]

    @strawberry.type
    class Mutation:
        write0 = DjangoMutationField(WriteBook)

    finalize_django_types()
    DjangoSchema(query=PingQuery, mutation=Mutation)
    return WriteBook


def _info() -> strawberry.Info[object, object]:
    request = HttpRequest()
    request.user = User(username="u")
    return make_info(context=SimpleNamespace(request=request))


def _genres_serializer(**extra: object) -> type[ModelSerializerBase[library_models.Book]]:
    """A Book serializer exposing title + genres (allow_empty so [] clears)."""

    class GenresSerializer(ModelSerializerBase[library_models.Book]):
        genres: _PkRelation[library_models.Genre] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

    for key, value in extra.items():
        setattr(GenresSerializer, key, value)
    return GenresSerializer


def _seed_book(genres: Iterable[library_models.Genre] = ()) -> library_models.Book:
    branch = library_models.Branch.objects.create(name="LedgerBranch", city="Boston")
    shelf = library_models.Shelf.objects.create(code="LedgerShelf", branch=branch)
    book = library_models.Book.objects.create(title="LedgerBook", shelf=shelf)
    if genres:
        book.genres.set(genres)
    return book


@pytest.mark.django_db
def test_supplied_m2m_duplicates_collapse_and_an_explicit_empty_list_clears() -> None:
    """DRF's M2M ``set()`` semantics hold through the write step: duplicates collapse, ``[]`` clears."""
    genre = library_models.Genre.objects.create(name="SetSemGenre")
    book = _seed_book(genres=[genre])
    mutation_cls = _bind_book_genres_mutation(_genres_serializer())

    with write_pipeline("default", lock=False):
        saved = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            book,
            {"genres": [saved_pk(genre), saved_pk(genre)]},
            specs=mutation_cls._input_field_specs,  # duplicates collapse to the one row
        )
    assert isinstance(saved, library_models.Book)
    assert list(book.genres.values_list("pk", flat=True)) == [saved_pk(genre)]

    with write_pipeline("default", lock=False):
        saved = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            book,
            {"genres": []},
            specs=mutation_cls._input_field_specs,  # an explicit empty list is a clear
        )
    assert isinstance(saved, library_models.Book)
    assert not book.genres.exists()


# ===========================================================================
# Phase separation, savepoint, canonical pks
# ===========================================================================


@pytest.mark.django_db
def test_save_failure_after_partial_writes_rolls_back_to_the_savepoint() -> None:
    """A custom ``create()`` that WROTE rows then raised leaves no partial write behind."""
    seed_data(0)

    class PartialWritingSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def create(self, validated_data: dict[str, object]) -> NoReturn:
            super().create(dict(validated_data))  # a real INSERT...
            raise serializers.ValidationError({"name": ["post-write failure"]})

    (category,) = categories_from_seed(("SavepointCat", False))
    mutation_cls = _bind_item_serializer_mutation(PartialWritingSerializer)
    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            None,
            {"name": "SavepointItem", "category": saved_pk(category)},
            specs=mutation_cls._input_field_specs,
        )
    assert isinstance(result, StepFailure)
    assert [(fe.field, fe.messages) for fe in result.errors] == [("name", ["post-write failure"])]
    # PROVEN in-transaction: the savepoint rollback removed the partial INSERT.
    assert not product_models.Item.objects.filter(name="SavepointItem").exists()


def test_flattener_survives_error_depth_beyond_the_recursion_limit() -> None:
    """The flattener is ITERATIVE: a deeper-than-recursion-limit error tree must not crash."""
    depth = sys.getrecursionlimit() + 200
    errors: dict[str, object] = {"leaf": ["boom"]}
    for _ in range(depth):
        errors = {"child": errors}

    flattened = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert len(flattened) == 1
    assert flattened[0].messages == ["boom"]


def test_flattener_truncates_past_the_node_budget() -> None:
    """Pathological fan-out ends in ONE ``__all__`` ``truncated`` marker, not unbounded work."""
    wide = {
        str(index): ["m"] for index in range(serializer_resolvers._ERROR_FLATTEN_NODE_BUDGET + 10)
    }
    flattened = serializer_resolvers.serializer_errors_to_field_errors(wide, {})
    assert flattened[-1].field == NON_FIELD_ERROR_KEY
    assert flattened[-1].codes == ["truncated"]
    assert len(flattened) <= serializer_resolvers._ERROR_FLATTEN_NODE_BUDGET + 1


def test_serializer_kwargs_preserves_custom_context_keys() -> None:
    """`get_serializer_kwargs` custom `context` keys are preserved alongside request and write_alias."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())

    class CustomContextMutation(mutation_cls):
        @override
        def get_serializer_kwargs(
            self,
            info: strawberry.Info,
            *,
            data: Mapping[str, object],
            hook_context: SerializerHookContext,
        ) -> dict[str, object]:
            return {
                "context": {"format": "json", "view": "custom_view", "custom_flag": True},
            }

    req = HttpRequest()
    req.user = User(username="u")
    info = make_info(context=SimpleNamespace(request=req))
    hook_ctx = _hook_ctx(operation="create", alias="default", instance_pk=None)

    kwargs = serializer_resolvers._serializer_kwargs(
        CustomContextMutation,
        info,
        final_data={"name": "test"},
        instance=None,
        alias="default",
        hook_context=hook_ctx,
    )
    assert _serializer_context(kwargs)["request"] is req
    assert _serializer_context(kwargs)["write_alias"] == "default"
    assert _serializer_context(kwargs)["format"] == "json"
    assert _serializer_context(kwargs)["view"] == "custom_view"
    assert _serializer_context(kwargs)["custom_flag"] is True


def test_serializer_errors_to_field_errors_never_returns_empty_envelope() -> None:
    """Empty serializer error dicts or lists of empty dicts fall back to a non-empty envelope."""
    empty_dict_errors = serializer_resolvers.serializer_errors_to_field_errors({}, {})
    assert len(empty_dict_errors) == 1
    assert empty_dict_errors[0].field == NON_FIELD_ERROR_KEY
    assert empty_dict_errors[0].messages == ["Validation failed without error details."]
    assert empty_dict_errors[0].codes == ["invalid"]

    empty_dicts: list[dict[str, object]] = [{}, {}]
    list_empty_dicts = serializer_resolvers.serializer_errors_to_field_errors(empty_dicts, {})
    assert len(list_empty_dicts) == 1
    assert list_empty_dicts[0].field == NON_FIELD_ERROR_KEY
    assert list_empty_dicts[0].messages == ["Validation failed without error details."]
    assert list_empty_dicts[0].codes == ["invalid"]

    field_empty_list = serializer_resolvers.serializer_errors_to_field_errors({"name": []}, {})
    assert len(field_empty_list) == 1
    assert field_empty_list[0].field == "name"
    assert field_empty_list[0].messages == ["Validation failed without error details."]
    assert field_empty_list[0].codes == ["invalid"]


def test_serializer_errors_to_field_errors_formats_scalar_integers_and_booleans() -> None:
    """Non-string scalar values in serializer errors are converted to strings."""
    errors = {"count": 100, "flag": False, "score": 9.5}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    by_field = {err.field: err.messages for err in flat}
    assert by_field["count"] == ["100"]
    assert by_field["flag"] == ["False"]
    assert by_field["score"] == ["9.5"]


def test_decode_input_object_handles_none() -> None:
    """_decode_input_object decodes a ``None`` input object to no values."""
    data_none, err_none = serializer_resolvers._decode_input_object([], None, info=unread_info())
    assert data_none == {}
    assert err_none is None


@pytest.mark.django_db
def test_decode_nested_multi_tolerates_none_item_in_list() -> None:
    """_decode_nested correctly passes None list items to DRF validation instead of raising AttributeError."""
    registry.clear()
    try:

        class ShelfItemChildSerializer(ModelSerializerBase[library_models.Shelf]):
            class Meta:
                model = library_models.Shelf
                fields = ("code", "topic")

        class LibraryBookSerializer(ModelSerializerBase[library_models.Book]):
            shelves = ShelfItemChildSerializer(many=True, required=False)

            class Meta:
                model = library_models.Book
                fields = ("title", "shelves")

            @override
            def create(self, validated_data: dict[str, object]) -> library_models.Book:
                return library_models.Book.objects.create(**validated_data)

        class ShelfT(DjangoType, relay.Node):
            class Meta:
                model = library_models.Shelf
                fields = ("id", "code", "topic")
                primary = True

        assert registry.get(library_models.Shelf) is ShelfT

        class BookT(DjangoType, relay.Node):
            class Meta:
                model = library_models.Book
                fields = ("id", "title")
                primary = True

        assert registry.get(library_models.Book) is BookT

        class CreateBook(SerializerMutation):
            class Meta:
                serializer_class = LibraryBookSerializer
                operation = "create"
                nested_fields = {"shelves": NestedSerializerConfig()}
                permission_classes = ()

        @strawberry.type
        class Query:
            ping: int = 1

        @strawberry.type
        class Mutation:
            create_book = DjangoMutationField(CreateBook)

        finalize_django_types()
        DjangoSchema(query=Query, mutation=Mutation)

        req = HttpRequest()
        req.user = User(username="u")
        info = make_info(context=SimpleNamespace(request=req))

        input_cls = CreateBook._input_class
        assert input_cls is not None
        input_data = _keyword_constructor(input_cls)(
            title="Book with None shelf",
            shelves=[None],
        )

        with managed_write_transaction("default"):
            result = serializer_resolvers.resolve_serializer_sync(
                CreateBook,
                info,
                data=input_data,
                id=UNSET,
            )

        assert isinstance(result, _ErrorEnvelope)
        assert result.errors is not None
        assert len(result.errors) > 0
        assert any("shelves" in err.field for err in result.errors)
    finally:
        registry.clear()


def test_hook_context_invariants() -> None:
    """``SerializerHookContext`` is frozen, slotted, and immutable."""
    ctx = SerializerHookContext(
        operation="update",
        write_alias="default",
        instance_pk=42,
    )
    assert ctx.operation == "update"
    assert ctx.write_alias == "default"
    assert ctx.instance_pk == 42
    assert not hasattr(ctx, "__dict__")

    with pytest.raises(FrozenInstanceError):
        # basedpyright: the write to the frozen dataclass field is the mutation under test; the
        # checker rejects assignment to a frozen field
        ctx.operation = "create"  # pyright: ignore[reportAttributeAccessIssue]

    ctx_same = SerializerHookContext(
        operation="update",
        write_alias="default",
        instance_pk=42,
    )
    assert ctx == ctx_same
    assert hash(ctx) == hash(ctx_same)


def test_decode_nested_multi_decodes_items_and_handles_item_error() -> None:
    """_decode_nested decodes items under NESTED_MULTI and short-circuits on child error."""

    @strawberry.input
    class ChildInput:
        name: str

    spec = InputFieldSpec(
        input_attr="items",
        graphql_name="items",
        target_name="items",
        kind=NESTED_MULTI,
        nested_specs=(
            InputFieldSpec(
                input_attr="name",
                graphql_name="name",
                target_name="name",
                kind="SCALAR",
            ),
        ),
    )

    val = [ChildInput(name="item1"), ChildInput(name="item2")]
    decoded, err = serializer_resolvers._decode_nested(
        spec,
        val,
        unread_info(),
        path_prefix="items",
    )
    assert err is None
    assert decoded == [{"name": "item1"}, {"name": "item2"}]

    val_bad = [ChildInput(name="item1"), ChildInput(name="bad\x00")]
    decoded_bad, err_bad = serializer_resolvers._decode_nested(
        spec,
        val_bad,
        unread_info(),
        path_prefix="items",
    )
    assert decoded_bad is None
    assert err_bad is not None
    assert err_bad.field == "items.1.name"


def test_serializer_errors_to_field_errors_direct_leaf() -> None:
    """serializer_errors_to_field_errors handles direct leaf errors without nested dicts."""
    err = ErrorDetail("Direct error", code="invalid")
    res = serializer_resolvers.serializer_errors_to_field_errors(err, {})
    assert len(res) == 1
    assert res[0].field == NON_FIELD_ERROR_KEY
    assert res[0].messages == ["Direct error"]
    assert res[0].codes == ["invalid"]


def test_serializer_decode_step_returns_field_errors_on_decode_failure() -> None:
    """_serializer_decode_step wraps a decode error into a ``StepFailure``."""

    @strawberry.input
    class NameInput:
        name: str

    specs = [
        InputFieldSpec(
            input_attr="name",
            graphql_name="name",
            target_name="name",
            kind="SCALAR",
        ),
    ]

    res = serializer_resolvers._serializer_decode_step(
        NameInput(name="bad\x00"),
        make_info(),
        specs=specs,
    )
    assert isinstance(res, StepFailure)
    assert len(res.errors) == 1
    assert res.errors[0].field == "name"


# ===========================================================================
# A date or naive datetime a serializer validates into a DateTimeField column
# ===========================================================================
# A ``validate_<field>`` hook returning ``value.date()`` or a naive datetime makes
# Django emit a naive-datetime ``RuntimeWarning`` on every store, so the shape stays
# out of the example app and is driven in-process here.


def _day_of(value: datetime.datetime) -> object:
    """Keep only the validated datetime's date."""
    return value.date()


def _naive_utc_wall_clock(value: datetime.datetime) -> object:
    """Keep the validated datetime's UTC wall clock, naive."""
    return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)


def _build_day_stamp_schema(keep: Callable[[datetime.datetime], object]) -> DjangoSchema:
    """A create ``SerializerMutation`` whose ``validate_occurred_at`` returns ``keep(value)``."""

    class SpecimenT(DjangoType):
        class Meta:
            model = ScalarSpecimen
            fields = ("id", "label")
            primary = True

    class DayStampSerializer(ModelSerializerBase[ScalarSpecimen]):
        def validate_occurred_at(self, value: datetime.datetime) -> object:
            return keep(value)

        class Meta:
            model = ScalarSpecimen
            fields = (
                "label",
                "occurred_on",
                "occurred_at",
                "occurred_time",
                "external_id",
            )

    class WriteDayStamp(SerializerMutation):
        class Meta:
            serializer_class = DayStampSerializer
            operation = "create"
            permission_classes = [AllowAll]

    @strawberry.type
    class Mutation:
        write_day_stamp = DjangoMutationField(WriteDayStamp)

    finalize_django_types()
    del SpecimenT
    return DjangoSchema(query=PingQuery, mutation=Mutation)


def _write_day_stamp(
    occurred_at: str,
    keep: Callable[[datetime.datetime], object] = _day_of,
) -> dict[object, object]:
    """Run the day-stamp create with ``occurred_at`` on the wire; return its payload."""
    request = HttpRequest()
    request.user = User(username="u")
    result = _build_day_stamp_schema(keep).execute_sync(
        "mutation($d: DayStampSerializerInput!){ writeDayStamp(data:$d){ "
        "result{ label } errors{ field messages codes } } }",
        variable_values={
            "d": {
                "label": "day",
                "occurredOn": "2021-06-15",
                "occurredAt": occurred_at,
                "occurredTime": "09:30:00",
                "externalId": str(uuid.uuid4()),
            },
        },
        context_value=SimpleNamespace(request=request),
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    return json_object(result.data, "writeDayStamp")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("zone", "keep"),
    [
        pytest.param("Asia/Tokyo", _day_of, id="tokyo-date"),
        pytest.param("Etc/GMT-14", _day_of, id="utc-plus-14-date"),
        pytest.param("Asia/Tokyo", _naive_utc_wall_clock, id="tokyo-naive-datetime"),
    ],
)
def test_serializer_date_over_a_datetime_column_whose_midnight_overflows_is_refused(
    zone: str,
    keep: Callable[[datetime.datetime], object],
) -> None:
    """A validated date or naive datetime Django would bind before year 1 is the field's ``invalid``.

    Django stores a date held by a ``DateTimeField`` as its midnight and a naive datetime
    as it is, each made aware in the default time zone; in a zone ahead of UTC a year-1
    midnight falls in year 0, which the adapter cannot bind. The refusal is keyed to the
    input field, nothing is written, and no masked error escapes.
    """
    with override_settings(TIME_ZONE=zone):
        payload = _write_day_stamp("0001-01-01T00:00:00Z", keep)

    assert payload["result"] is None
    assert payload["errors"] == [
        {
            "field": "occurredAt",
            "messages": ["Enter a value the database can represent."],
            "codes": ["invalid"],
        },
    ]
    assert not ScalarSpecimen.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "zone",
    [pytest.param("UTC", id="utc"), pytest.param("America/Chicago", id="chicago")],
)
def test_serializer_date_over_a_datetime_column_stores_its_default_zone_midnight(
    zone: str,
) -> None:
    """A validated date the database can hold stores as its midnight in the default zone.

    Django warns as it makes that midnight at the save; the package reads the same
    projection silently and lets the write through.
    """
    with (
        override_settings(TIME_ZONE=zone),
        pytest.warns(RuntimeWarning, match="received a naive datetime"),
    ):
        payload = _write_day_stamp("2021-06-15T09:30:00Z")

    assert payload["errors"] == []
    assert payload["result"] == {"label": "day"}
    stored = ScalarSpecimen.objects.get(label="day").occurred_at
    assert stored == datetime.datetime(2021, 6, 15, tzinfo=zoneinfo.ZoneInfo(zone))


_UNREPRESENTABLE = ["Enter a value the database can represent."]


def _converted_columns_model(name: str) -> type[Model]:
    """A synthetic model with a nullable ``amount``, a ``DateField`` and a ``DurationField``."""
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(null=True, blank=True),
            "day": models.DateField(null=True, blank=True),
            "span": models.DurationField(null=True, blank=True),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


def _evening_utc(_serializer: object, value: datetime.date) -> datetime.datetime:
    """A ``validate_day`` hook answering the validated date's 20:00 UTC instant."""
    return datetime.datetime.combine(value, datetime.time(20), tzinfo=datetime.timezone.utc)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("sent", "stored"),
    [
        pytest.param("9999-12-31", None, id="past-year-9999-in-tokyo"),
        pytest.param("2021-06-15", datetime.date(2021, 6, 16), id="in-range"),
    ],
)
def test_serializer_datetime_from_a_date_hook_is_held_to_its_default_zone_date(
    sent: str,
    stored: datetime.date | None,
) -> None:
    """An aware datetime a hook leaves for a ``DateField`` is refused where Django cannot cast it.

    A ``validate_day`` hook answers the sent date's 20:00 UTC instant, which Django casts
    to a date in the default time zone (``Asia/Tokyo``) at the save; 9999-12-31 20:00 UTC
    is in year 10000 there: the field's ``invalid`` error, nothing written, no masked
    ``OverflowError``. A value inside the range stores as its Tokyo date.
    """
    model_class = _converted_columns_model(f"DayStampRow{'Refused' if stored is None else ''}")
    serializer_cls = _serializer_over(
        model_class,
        ("day",),
        methods={"validate_day": _evening_utc},
    )
    with _synthetic_table(model_class), override_settings(TIME_ZONE="Asia/Tokyo"):
        schema, create_input, _ = _blank_columns_schema(serializer_cls, model_class)
        payload = _run_row_write(schema, create_input, {"day": sent})
        stored_days = list(model_class._default_manager.values_list("day", flat=True))

    if stored is None:
        assert payload == {
            "result": None,
            "errors": [{"field": "day", "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
        }
        assert stored_days == []
    else:
        assert json_at(payload, "errors") == []
        assert stored_days == [stored]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("sent", "days", "fits_64_bits"),
    [
        pytest.param("106751992 00:00:00", 106_751_992, False, id="past-64-bits"),
        pytest.param("-106751992 00:00:00", -106_751_992, False, id="past-64-bits-negative"),
        pytest.param("106751991 00:00:00", 106_751_991, True, id="fits-64-bits"),
    ],
)
def test_serializer_duration_past_the_backend_integer_is_refused(
    sent: str,
    days: int,
    *,
    fits_64_bits: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A duration whose microsecond count SQLite cannot bind is the field's ``invalid`` error.

    SQLite stores a duration as its microsecond count in a 64-bit integer, which a
    ``DurationField`` carries no validator for; past it the driver would raise
    ``OverflowError`` at the save. The refusal is keyed to the input field and nothing
    is written; a duration that fits stores. PostgreSQL binds an ``interval``, so every
    duration stores there. The column's scalar is the consumer's ``SCALAR_MAP`` entry,
    here DRF's own duration text.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = re.sub(r"\W", "", sent.replace("-", "Minus"))
    model_class = _converted_columns_model(f"SpanRow{suffix}")
    serializer_cls = _serializer_over(
        model_class,
        ("span",),
        declared={"span": serializers.DurationField()},
    )
    with _synthetic_table(model_class):
        schema, create_input, _ = _blank_columns_schema(serializer_cls, model_class)
        payload = _run_row_write(schema, create_input, {"span": sent})
        stored_spans = list(model_class._default_manager.values_list("span", flat=True))

    if not fits_64_bits and not connections["default"].features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [{"field": "span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
        }
        assert stored_spans == []
    else:
        assert json_at(payload, "errors") == []
        assert stored_spans == [datetime.timedelta(days=days)]


def _unique_span_model(name: str, shape: str) -> type[Model]:
    """A synthetic model whose ``span`` is unique under ``shape``, beside an ``amount``.

    ``unique`` is ``unique=True``, ``together`` is ``unique_together`` with ``amount``, and
    ``conditional`` a ``UniqueConstraint`` over the rows whose ``amount`` is positive.
    """
    meta: dict[str, object] = {"app_label": "products", "managed": False}
    if shape == "together":
        meta["unique_together"] = (("span", "amount"),)
    if shape == "conditional":
        meta["constraints"] = (
            models.UniqueConstraint(
                fields=("span",),
                condition=models.Q(amount__gt=0),
                name=f"{name.lower()}_span_key",
            ),
        )
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(default=1),
            "span": models.DurationField(unique=shape == "unique"),
            "Meta": type("Meta", (), meta),
        },
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("shape", ["unique", "together", "conditional"])
@pytest.mark.parametrize(
    ("sent", "days"),
    [
        pytest.param("999999999 00:00:00", None, id="past-64-bits"),
        pytest.param("5 00:00:00", 5, id="fits-64-bits"),
    ],
)
def test_serializer_duration_past_the_backend_integer_is_refused_before_its_uniqueness_query(
    operation: str,
    shape: str,
    sent: str,
    days: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A duration SQLite cannot bind fails its field before a uniqueness validator binds it.

    DRF's ``UniqueValidator`` (``unique=True``, a conditional ``UniqueConstraint``) and
    ``UniqueTogetherValidator`` bind ``span`` in a query inside ``is_valid()``, where SQLite
    raises ``OverflowError`` binding a microsecond count past 64 bits, which DRF's
    ``qs_exists`` does not catch. The serializer answers ``span``'s ``invalid`` error before
    any of them runs, nothing written; a duration that fits is written. PostgreSQL binds an
    ``interval``, so every duration stores there. The column's scalar is the consumer's
    ``SCALAR_MAP`` entry, here DRF's own duration text.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    model_class = _unique_span_model(
        f"UniqueSpanRow{shape.title()}{operation.title()}{days or 'Past'}",
        shape,
    )
    serializer_cls = _serializer_over(model_class, ("span", "amount"))
    stored = datetime.timedelta(days=2)
    with _synthetic_table(model_class):
        row_id = (
            saved_pk(model_class._default_manager.create(span=stored, amount=1))
            if operation == "update"
            else None
        )
        schema, create_input, update_input = _blank_columns_schema(serializer_cls, model_class)
        payload = _run_row_write(
            schema,
            create_input if row_id is None else update_input,
            {"span": sent, "amount": 1},
            row_id,
        )
        stored_spans = list(model_class._default_manager.values_list("span", flat=True))

    kept = [] if row_id is None else [stored]
    if days is None and not connections["default"].features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [{"field": "span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
        }
        assert stored_spans == kept
    else:
        assert json_at(payload, "errors") == []
        assert stored_spans == [datetime.timedelta(days=days or 999_999_999)]


def _unique_stamp_model() -> type[Model]:
    """A synthetic model with a unique ``stamp`` time beside an ``amount``."""
    return type(
        "UniqueStampRow",
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(default=1),
            "stamp": models.TimeField(unique=True),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


def _aware_stamp(_serializer: object, attrs: dict[str, object]) -> dict[str, object]:
    """A ``validate()`` hook setting ``stamp`` to an aware time."""
    return {**attrs, "stamp": datetime.time(9, 30, tzinfo=datetime.timezone.utc)}


@pytest.mark.django_db(transaction=True)
def test_serializer_validate_setting_an_aware_unique_time_is_refused_after_is_valid() -> None:
    """A value ``validate()`` sets, after every uniqueness validator ran, is still refused.

    DRF runs ``validate()`` after its validators, so the ``UniqueValidator`` on ``stamp``
    bound the naive time sent; the aware time the hook sets is ``stamp``'s ``invalid`` error
    on SQLite, which cannot store it, nothing written. PostgreSQL stores it.
    """
    model_class = _unique_stamp_model()
    serializer_cls = _serializer_over(model_class, ("stamp",), methods={"validate": _aware_stamp})
    with _synthetic_table(model_class):
        schema, create_input, _ = _blank_columns_schema(serializer_cls, model_class)
        payload = _run_row_write(schema, create_input, {"stamp": "09:30:00"})
        stored = list(model_class._default_manager.values_list("stamp", flat=True))

    if connections["default"].vendor == "postgresql":
        assert json_at(payload, "errors") == []
        return
    assert payload == {
        "result": None,
        "errors": [{"field": "stamp", "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
    }
    assert stored == []


def _keys_only(_serializer: object, data: object) -> object:
    """A ``to_internal_value`` override answering the list of the keys sent, no mapping."""
    return list(data) if is_mapping(data) else data


@pytest.mark.django_db(transaction=True)
def test_serializer_hold_passes_a_non_mapping_value_on_to_drf(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A non-mapping value a ``to_internal_value`` override returns is passed on untouched.

    ``_keys_only`` answers the list of the keys sent in place of the validated mapping. The
    storability hold reads no column value from it, so DRF's own validators and
    ``save()`` meet it as the override returned it: the request fails with DRF's own
    refusal of a non-mapping ``validated_data``, masked, never an error the hold raises
    indexing the list by a field name, and nothing is written.
    """
    model_class = _unique_stamp_model()
    serializer_cls = _serializer_over(
        model_class,
        ("stamp",),
        methods={"to_internal_value": _keys_only},
    )
    with _synthetic_table(model_class), caplog.at_level(logging.ERROR):
        schema, create_input, _ = _blank_columns_schema(serializer_cls, model_class)
        request = HttpRequest()
        request.user = User(username="u")
        result = schema.execute_sync(
            f"mutation($d: {create_input}!){{ createRow(data:$d){{ result{{ id }} }} }}",
            variable_values={"d": {"stamp": "09:30:00"}},
            context_value=SimpleNamespace(request=request),
        )
        rows = model_class._default_manager.count()

    assert result.errors is not None
    assert [error.message for error in result.errors] == ["An unexpected error occurred."]
    logged = [record.getMessage().partition("\n")[0] for record in caplog.records]
    assert "'list' object is not a mapping" in logged, logged
    assert rows == 0


#: A duration whose microsecond count leaves 64 bits, and one that fits, as DRF's text.
_PAST_64_BITS = "999999999 00:00:00"
_FITS_64_BITS = "5 00:00:00"
#: Where a consumer ``create()`` / ``update()`` clamps a duration before writing it.
_CLAMPED = datetime.timedelta(days=10**6)


def _nested_parent_model(name: str) -> type[Model]:
    """A synthetic parent row whose serializer writes nested child rows."""
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(default=1),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


def _validated_item(value: object) -> dict[str, object]:
    """A nested serializer's validated mapping, keyed by its field sources."""
    assert is_mapping(value), value
    return {str(key): item for key, item in value.items()}


def _nested_items(level: str, validated_data: dict[str, object]) -> list[dict[str, object]]:
    """Pop the nested child items ``level`` declares out of ``validated_data``."""
    if level == "single":
        return [_validated_item(validated_data.pop("child"))]
    if level == "many":
        items = validated_data.pop("children")
        assert is_list(items), items
        return [_validated_item(item) for item in items]
    return [_validated_item(_validated_item(validated_data.pop("mid"))["child"])]


def _nested_parent_serializer(
    parent_model: type[Model],
    child_model: type[Model],
    child_serializer: serializers.Serializer[object],
    level: str,
    *,
    clamp: bool = False,
) -> tuple[type[DRFSerializer], dict[str, NestedSerializerConfig]]:
    """A ``ModelSerializer`` over ``parent_model`` declaring ``child_serializer`` at ``level``.

    ``single`` declares it as ``child``, ``many`` as the list ``children`` and ``deep`` as
    ``mid.child`` under a plain ``Serializer``. Its own ``create()`` / ``update()`` writes
    the parent, then each child row (its ``span`` clamped to ``_CLAMPED`` when ``clamp``).
    Answers the class and the ``Meta.nested_fields`` opting the nesting in.
    """
    if level == "single":
        declared: dict[str, object] = {"child": child_serializer}
        nested = {"child": NestedSerializerConfig()}
    elif level == "many":
        declared = {"children": type(child_serializer)(many=True)}
        nested = {"children": NestedSerializerConfig()}
    else:
        mid = type("NestedMidSerializer", (serializers.Serializer,), {"child": child_serializer})
        declared = {"mid": mid()}
        nested = {"mid": NestedSerializerConfig(nested_fields={"child": NestedSerializerConfig()})}

    def _write_children(items: list[dict[str, object]]) -> None:
        for item in items:
            if clamp:
                item["span"] = min(require_instance(item["span"], datetime.timedelta), _CLAMPED)
            _ = child_model._default_manager.create(**item)

    def create(_serializer: object, validated_data: dict[str, object]) -> Model:
        items = _nested_items(level, validated_data)
        parent = parent_model._default_manager.create(**validated_data)
        _write_children(items)
        return parent

    def update(_serializer: object, instance: Model, validated_data: dict[str, object]) -> Model:
        items = _nested_items(level, validated_data)
        for name, value in validated_data.items():
            setattr(instance, name, value)
        instance.save()
        _write_children(items)
        return instance

    serializer_cls = _serializer_over(
        parent_model,
        ("amount", *declared),
        declared,
        {"create": create, "update": update},
    )
    return serializer_cls, nested


#: The dotted path of the item under test's ``span`` at each nesting level.
_NESTED_PATHS = {"single": "child.span", "many": "children.1.span", "deep": "mid.child.span"}


def _nested_payload(level: str, item: dict[str, object]) -> dict[str, object]:
    """The nested input sending ``item`` at ``level``, a fitting first item before it in a list."""
    if level == "single":
        return {"child": item}
    if level == "many":
        return {"children": [{**item, "span": "1 00:00:00"}, item]}
    return {"mid": {"child": item}}


def _nested_spans(level: str, sent: str) -> list[datetime.timedelta]:
    """The child spans a nested write of ``sent`` at ``level`` stores, in write order."""
    days = 999_999_999 if sent == _PAST_64_BITS else 5
    stored = [datetime.timedelta(days=days)]
    return [datetime.timedelta(days=1), *stored] if level == "many" else stored


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("shape", ["unique", "together", "conditional"])
@pytest.mark.parametrize("level", list(_NESTED_PATHS))
@pytest.mark.parametrize("sent", [_PAST_64_BITS, _FITS_64_BITS], ids=["past-64-bits", "fits"])
def test_serializer_nested_duration_a_uniqueness_validator_cannot_bind_is_the_item_error(
    operation: str,
    shape: str,
    level: str,
    sent: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested item's duration its uniqueness validator cannot bind fails the item's field.

    The child ``ModelSerializer``'s ``UniqueValidator`` (``unique=True``, a conditional
    ``UniqueConstraint``) or ``UniqueTogetherValidator`` binds ``span`` in a query inside
    ``is_valid()`` at the item's own level: a single nested item, the second item of a
    ``many=True`` list, an item under a plain nested ``Serializer``. On SQLite a duration
    past 64 bits of microseconds raises ``OverflowError`` there, which DRF's ``qs_exists``
    does not catch; the item's ``span`` answers its ``invalid`` error at its dotted path
    instead, nothing written, on a create and on the pipeline's partial update. A duration
    that fits reaches the consumer's own ``create()`` / ``update()``, which writes it;
    PostgreSQL binds an ``interval``, so every duration reaches it there.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = f"{shape.title()}{level.title()}{operation.title()}{'Past' if sent == _PAST_64_BITS else 'Fits'}"
    parent_model = _nested_parent_model(f"NestedSpanParent{suffix}")
    child_model = _unique_span_model(f"NestedSpanChild{suffix}", shape)
    child_cls = _serializer_over(child_model, ("id", "span", "amount"))
    serializer_cls, nested = _nested_parent_serializer(
        parent_model,
        child_model,
        child_cls(),
        level,
    )
    path = _NESTED_PATHS[level]
    with _synthetic_table(parent_model), _synthetic_table(child_model):
        row_id = (
            saved_pk(parent_model._default_manager.create(amount=1))
            if operation == "update"
            else None
        )
        schema, create_input, update_input = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        payload = _run_row_write(
            schema,
            create_input if row_id is None else update_input,
            {"amount": 1, **_nested_payload(level, {"span": sent, "amount": 1})},
            row_id,
        )
        spans = list(child_model._default_manager.order_by("pk").values_list("span", flat=True))
        parents = parent_model._default_manager.count()

    native = connections["default"].features.has_native_duration_field
    if sent == _PAST_64_BITS and not native:
        assert payload == {
            "result": None,
            "errors": [{"field": path, "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
        }
        assert (spans, parents) == ([], 0 if row_id is None else 1)
    else:
        assert json_at(payload, "errors") == []
        assert spans == _nested_spans(level, sent)


def _condition_span_model(name: str) -> type[Model]:
    """A synthetic model unique on ``amount`` and ``rank`` among the rows of positive ``span``."""
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(default=1),
            "rank": models.IntegerField(default=1),
            "span": models.DurationField(),
            "Meta": type(
                "Meta",
                (),
                {
                    "app_label": "products",
                    "managed": False,
                    "constraints": (
                        models.UniqueConstraint(
                            fields=("amount", "rank"),
                            condition=models.Q(span__gt=datetime.timedelta(0)),
                            name=f"{name.lower()}_amount_rank_key",
                        ),
                    ),
                },
            ),
        },
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sent", [_PAST_64_BITS, _FITS_64_BITS], ids=["past-64-bits", "fits"])
def test_serializer_nested_duration_a_constraint_condition_binds_is_the_item_error(
    sent: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested duration a conditional constraint's condition binds fails the item's field.

    ``span`` is no field of the ``UniqueConstraint`` on ``amount`` and ``rank``; it sits in
    its ``condition``, so DRF's ``UniqueTogetherValidator`` carries it in
    ``condition_fields`` and binds its value checking the condition inside ``is_valid()``,
    where SQLite raises ``OverflowError`` for a duration past 64 bits of microseconds, which
    DRF does not catch. ``child.span`` answers its ``invalid`` error instead, nothing written;
    a duration that fits is written by the consumer's ``create()``.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = "Past" if sent == _PAST_64_BITS else "Fits"
    parent_model = _nested_parent_model(f"ConditionSpanParent{suffix}")
    child_model = _condition_span_model(f"ConditionSpanChild{suffix}")
    child_cls = _serializer_over(child_model, ("span", "amount", "rank"))
    serializer_cls, nested = _nested_parent_serializer(
        parent_model,
        child_model,
        child_cls(),
        "single",
    )
    with _synthetic_table(parent_model), _synthetic_table(child_model):
        schema, create_input, _ = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        payload = _run_row_write(
            schema,
            create_input,
            {"amount": 1, "child": {"span": sent, "amount": 1, "rank": 1}},
        )
        spans = list(child_model._default_manager.values_list("span", flat=True))

    if sent == _PAST_64_BITS and not connections["default"].features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [
                {"field": "child.span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]},
            ],
        }
        assert spans == []
    else:
        assert json_at(payload, "errors") == []
        assert spans == [datetime.timedelta(days=999_999_999 if sent == _PAST_64_BITS else 5)]


def _accept_every_item(_attrs: object) -> None:
    """A serializer-level validator accepting every item."""


def _dated_span_model(name: str, *, unique_for_date: bool) -> type[Model]:
    """A synthetic model with a ``span`` beside a ``day``, unique for that date when asked."""
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "day": models.DateField(),
            "span": models.DurationField(unique_for_date="day" if unique_for_date else None),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("shape", ["unique-for-date", "plain"])
@pytest.mark.parametrize("sent", [_PAST_64_BITS, _FITS_64_BITS], ids=["past-64-bits", "fits"])
def test_serializer_nested_duration_only_a_validator_bind_holds(
    shape: str,
    sent: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested duration is held only where a uniqueness validator binds it in a query.

    ``unique_for_date="day"`` makes DRF's ``UniqueForDateValidator`` bind the item's ``span``
    beside the integer parts of its ``day``, so on SQLite a duration past 64 bits of
    microseconds is ``child.span``'s ``invalid`` error, nothing written. A ``span`` no
    validator binds is the consumer ``create()``'s to write: the one here clamps it, so the
    same duration is written clamped, with no error.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = f"{shape.title().replace('-', '')}{'Past' if sent == _PAST_64_BITS else 'Fits'}"
    parent_model = _nested_parent_model(f"HeldSpanParent{suffix}")
    child_model = _dated_span_model(f"HeldSpanChild{suffix}", unique_for_date=shape != "plain")
    # A serializer-level validator of the consumer's own binds nothing the hold reads.
    child_cls = _serializer_over(
        child_model,
        ("span", "day"),
        meta=None if shape != "plain" else {"validators": [_accept_every_item]},
    )
    serializer_cls, nested = _nested_parent_serializer(
        parent_model,
        child_model,
        child_cls(),
        "single",
        clamp=shape == "plain",
    )
    with _synthetic_table(parent_model), _synthetic_table(child_model):
        schema, create_input, _ = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        payload = _run_row_write(
            schema,
            create_input,
            {"amount": 1, "child": {"span": sent, "day": "2021-06-15"}},
        )
        spans = list(child_model._default_manager.values_list("span", flat=True))

    days = 999_999_999 if sent == _PAST_64_BITS else 5
    if shape == "plain":
        assert json_at(payload, "errors") == []
        assert spans == [min(datetime.timedelta(days=days), _CLAMPED)]
    elif sent == _PAST_64_BITS and not connections["default"].features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [
                {"field": "child.span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]},
            ],
        }
        assert spans == []
    else:
        assert json_at(payload, "errors") == []
        assert spans == [datetime.timedelta(days=days)]


def _unchanged_instance(_serializer: object, instance: Model, _validated_data: object) -> Model:
    """An ``update()`` writing nothing, which a serializer declaring nesting must override."""
    return instance


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("placement", ["root", "nested"])
@pytest.mark.parametrize("sent", [_PAST_64_BITS, _FITS_64_BITS], ids=["past-64-bits", "fits"])
def test_serializer_declared_unique_validator_over_another_model_holds_its_bind(
    placement: str,
    sent: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A declared ``UniqueValidator`` over another model's rows holds the value it binds.

    The ``span`` field writes no column of the mutation's model: at the root it is a
    serializer-only field, nested it sits on a plain ``Serializer``. Its declared
    ``UniqueValidator`` binds the value against the other model's ``span`` column, read from
    the validator's own queryset, so on SQLite a duration past 64 bits of microseconds is
    ``span``'s ``invalid`` error at its path, nothing written; a duration that fits reaches
    ``create()``, which writes the other model's row.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = f"{placement.title()}{'Past' if sent == _PAST_64_BITS else 'Fits'}"
    parent_model = _nested_parent_model(f"DeclaredSpanParent{suffix}")
    other_model = _unique_span_model(f"DeclaredSpanOther{suffix}", "unique")
    span = serializers.DurationField(
        write_only=True,
        validators=[UniqueValidator(queryset=other_model._default_manager.all())],
    )

    def create(_serializer: object, validated_data: dict[str, object]) -> Model:
        held = validated_data.pop("span") if placement == "root" else validated_data.pop("child")
        span_value = held if placement == "root" else _validated_item(held)["span"]
        _ = other_model._default_manager.create(span=span_value, amount=1)
        return parent_model._default_manager.create(**validated_data)

    if placement == "root":
        declared: dict[str, object] = {"span": span}
        nested: dict[str, NestedSerializerConfig] | None = None
        data: dict[str, object] = {"amount": 1, "span": sent}
        path = "span"
    else:
        plain = type("DeclaredSpanSerializer", (serializers.Serializer,), {"span": span})
        declared = {"child": plain()}
        nested = {"child": NestedSerializerConfig()}
        data = {"amount": 1, "child": {"span": sent}}
        path = "child.span"
    serializer_cls = _serializer_over(
        parent_model,
        ("amount", *declared),
        declared,
        {"create": create, "update": _unchanged_instance},
    )
    with _synthetic_table(parent_model), _synthetic_table(other_model):
        schema, create_input, _ = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        payload = _run_row_write(schema, create_input, data)
        spans = list(other_model._default_manager.values_list("span", flat=True))

    if sent == _PAST_64_BITS and not connections["default"].features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [{"field": path, "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
        }
        assert spans == []
    else:
        assert json_at(payload, "errors") == []
        assert spans == [datetime.timedelta(days=999_999_999 if sent == _PAST_64_BITS else 5)]


#: Whether DRF's ``UniqueTogetherValidator`` takes ``nulls_distinct`` (3.18; 3.17 skips any ``None``).
_DRF_NULLS_DISTINCT = "nulls_distinct" in inspect.signature(UniqueTogetherValidator).parameters


def _nullable_partner_model(name: str) -> type[Model]:
    """A synthetic model with a ``span`` beside a nullable ``amount``."""
    return type(
        name,
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(null=True, default=1),
            "span": models.DurationField(),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sent", [_PAST_64_BITS, "5 00:00:00"])
def test_nested_together_read_only_callable_default_is_evaluated_once(
    sent: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A validator sees DRF's one read-only default and holds the value it will bind."""
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    parent_model = _nested_parent_model("ReadOnlyDefaultParent")
    child_model = _nullable_partner_model("ReadOnlyDefaultChild")
    calls: list[int] = []

    def rank_default() -> int:
        calls.append(1)
        return 1

    child_cls = _serializer_over(
        child_model,
        ("span", "amount"),
        {"amount": serializers.IntegerField(read_only=True, default=rank_default)},
        meta={
            "validators": [
                UniqueTogetherValidator(
                    queryset=child_model._default_manager.all(),
                    fields=("span", "amount"),
                ),
            ],
        },
    )
    serializer_cls, nested = _nested_parent_serializer(
        parent_model,
        child_model,
        child_cls(),
        "single",
        clamp=True,
    )
    with _synthetic_table(parent_model), _synthetic_table(child_model):
        schema, create_input, _ = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        calls.clear()
        payload = _run_row_write(schema, create_input, {"amount": 1, "child": {"span": sent}})
        stored = list(child_model._default_manager.values_list("span", flat=True))

    assert calls == [1]
    if sent == _PAST_64_BITS and not connections["default"].features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [
                {"field": "child.span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]},
            ],
        }
        assert stored == []
    else:
        assert json_at(payload, "errors") == []
        assert stored == [_CLAMPED if sent == _PAST_64_BITS else datetime.timedelta(days=5)]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("case", ["null-partner", "null-partner-bound", "omitted-partner"])
def test_serializer_together_value_drf_binds_in_no_query_is_not_held(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``UniqueTogetherValidator``'s value is held only where DRF reaches its query.

    The nested item declares ``UniqueTogetherValidator(fields=("span", "amount"))`` and its
    consumer ``create()`` clamps ``span``. DRF skips the query when a checked value is
    ``None``, so a duration past 64 bits beside a ``null`` ``amount`` is written clamped,
    unheld; with ``nulls_distinct=False`` (DRF 3.18) DRF binds it, so on SQLite it is
    ``child.span``'s ``invalid`` error. An omitted non-required ``amount`` keeps DRF's own
    ``required`` error, raised before any query.
    """
    if case == "null-partner-bound" and not _DRF_NULLS_DISTINCT:
        pytest.skip("this DRF release has no nulls_distinct")
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = case.title().replace("-", "")
    parent_model = _nested_parent_model(f"PartnerParent{suffix}")
    child_model = _nullable_partner_model(f"PartnerChild{suffix}")
    validator = UniqueTogetherValidator(
        queryset=child_model._default_manager.all(),
        fields=("span", "amount"),
    )
    if case == "null-partner-bound":
        # The ``nulls_distinct=False`` argument, which drf-stubs do not declare.
        vars(validator)["nulls_distinct"] = False
    amount = (
        serializers.IntegerField(required=False)
        if case == "omitted-partner"
        else serializers.IntegerField(allow_null=True)
    )
    child_cls = _serializer_over(
        child_model,
        ("span", "amount"),
        {"amount": amount},
        meta={"validators": [validator]},
    )
    serializer_cls, nested = _nested_parent_serializer(
        parent_model,
        child_model,
        child_cls(),
        "single",
        clamp=True,
    )
    item: dict[str, object] = {"span": _PAST_64_BITS}
    if case != "omitted-partner":
        item["amount"] = None
    with _synthetic_table(parent_model), _synthetic_table(child_model):
        schema, create_input, _ = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        payload = _run_row_write(schema, create_input, {"amount": 1, "child": item})
        spans = list(child_model._default_manager.values_list("span", flat=True))

    native = connections["default"].features.has_native_duration_field
    if case == "omitted-partner":
        assert payload == {
            "result": None,
            "errors": [
                {
                    "field": "child.amount",
                    "messages": ["This field is required."],
                    "codes": ["required"],
                },
            ],
        }
        assert spans == []
    elif case == "null-partner-bound" and not native:
        assert payload == {
            "result": None,
            "errors": [
                {"field": "child.span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]},
            ],
        }
        assert spans == []
    else:
        assert json_at(payload, "errors") == []
        assert spans == [_CLAMPED]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("operation", "amount"),
    [
        pytest.param("update", None, id="update-unchanged"),
        pytest.param("update", 1, id="update-same"),
        pytest.param("update", 2, id="update-changed"),
        pytest.param("create", 1, id="create"),
    ],
)
def test_serializer_together_condition_value_is_held_only_where_drf_queries(
    operation: str,
    amount: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A root ``condition_fields`` value is held only where DRF's validator queries.

    The root serializer declares a ``UniqueTogetherValidator`` over another model's rows on
    ``amount``, whose ``condition`` reads the serializer-only ``span``. Which updates DRF
    checks (an omitted ``amount``, one sent as stored, a changed one, a changed condition
    value) is the installed DRF's decision; the same write sent with a duration that fits
    64 bits of microseconds, on a twin row, asks it. Where DRF queries, the condition's
    ``span`` is bound, which on SQLite is ``span``'s ``invalid`` error past 64 bits of
    microseconds; elsewhere the consumer ``create()`` / ``update()`` writes, the duration
    unheld. A create always queries.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    suffix = f"{operation.title()}{amount or 0}"
    parent_model = _nested_parent_model(f"ConditionRootParent{suffix}")
    other_model = _unique_span_model(f"ConditionRootOther{suffix}", "plain")
    validator = UniqueTogetherValidator(
        queryset=other_model._default_manager.all(),
        fields=("amount",),
        condition_fields=("span",),
        condition=models.Q(span__gt=datetime.timedelta(0)),
    )

    def write(
        _serializer: object,
        instance: Model | None,
        validated_data: dict[str, object],
    ) -> Model:
        _ = validated_data.pop("span")
        if instance is None:
            return parent_model._default_manager.create(**validated_data)
        for name, value in validated_data.items():
            setattr(instance, name, value)
        instance.save()
        return instance

    def create(serializer: object, validated_data: dict[str, object]) -> Model:
        return write(serializer, None, validated_data)

    serializer_cls = _serializer_over(
        parent_model,
        ("amount", "span"),
        {"span": serializers.DurationField(write_only=True)},
        {"create": create, "update": write},
        meta={"validators": [validator]},
    )
    data: dict[str, object] = {} if amount is None else {"amount": amount}
    connection = connections["default"]
    other_table = connection.ops.quote_name(other_model._meta.db_table)
    with _synthetic_table(parent_model), _synthetic_table(other_model):
        schema, create_input, update_input = _blank_columns_schema(serializer_cls, parent_model)
        input_name = create_input if operation == "create" else update_input

        def row() -> object:
            return (
                saved_pk(parent_model._default_manager.create(amount=1))
                if operation == "update"
                else None
            )

        twin = row()
        with CaptureQueriesContext(connection) as probe:
            fitting = _run_row_write(schema, input_name, {**data, "span": _FITS_64_BITS}, twin)
        assert json_at(fitting, "errors") == []
        queried = any(other_table in query["sql"] for query in probe.captured_queries)
        payload = _run_row_write(schema, input_name, {**data, "span": _PAST_64_BITS}, row())

    assert queried or operation == "update"
    if queried and not connection.features.has_native_duration_field:
        assert payload == {
            "result": None,
            "errors": [{"field": "span", "messages": _UNREPRESENTABLE, "codes": ["invalid"]}],
        }
    else:
        assert json_at(payload, "errors") == []


@pytest.mark.django_db(transaction=True)
def test_serializer_unique_for_date_value_is_held_only_with_its_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``UniqueForDateValidator``'s ``field`` is held only where its ``date_field`` is sent too.

    DRF answers a missing ``date_field`` with its own ``required`` error before any query,
    so a duration past 64 bits of microseconds sent without ``day`` binds nothing and the
    item keeps DRF's ``child.day`` error.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    parent_model = _nested_parent_model("UndatedSpanParent")
    child_model = _dated_span_model("UndatedSpanChild", unique_for_date=True)
    child_cls = _serializer_over(
        child_model,
        ("span", "day"),
        {"day": serializers.DateField(required=False)},
    )
    serializer_cls, nested = _nested_parent_serializer(
        parent_model,
        child_model,
        child_cls(),
        "single",
    )
    with _synthetic_table(parent_model), _synthetic_table(child_model):
        schema, create_input, _ = _blank_columns_schema(
            serializer_cls,
            parent_model,
            nested_fields=nested,
        )
        payload = _run_row_write(
            schema,
            create_input,
            {"amount": 1, "child": {"span": _PAST_64_BITS}},
        )

    assert payload == {
        "result": None,
        "errors": [
            {"field": "child.day", "messages": ["This field is required."], "codes": ["required"]},
        ],
    }


# A naive year-1 datetime made aware in Tokyo, and an aware one projected onto UTC under
# ``USE_TZ = False``: DRF's ``DateTimeField`` raises a raw ``OverflowError`` placing either.
_NAIVE_YEAR_ONE = "0001-01-01T05:00:00"
_AWARE_YEAR_ONE = "0001-01-01T00:00:00+01:00"
_IN_RANGE = "2021-06-15T09:30:00"
_OUT_OF_RANGE = ["Datetime value out of range."]
_DRF_TO_INTERNAL_VALUE = serializers.DateTimeField.to_internal_value
#: What ``_OverflowTolerantDateTimeField`` answers for a datetime it cannot place.
_TOLERATED = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


class _StampSerializer(serializers.Serializer[object]):
    at = serializers.DateTimeField()


class _SubclassedDateTimeField(serializers.DateTimeField):
    """A ``DateTimeField`` subclass that leaves ``to_internal_value`` to DRF."""


class _OverflowTolerantDateTimeField(serializers.DateTimeField):
    """A consumer ``DateTimeField`` whose ``to_internal_value`` answers an overflow itself."""

    @override
    def to_internal_value(self, value: datetime.datetime | str) -> datetime.datetime:
        try:
            return super().to_internal_value(value)
        except OverflowError:
            return _TOLERATED


def _stamp_shape(shape: str) -> tuple[serializers.Serializer[object], str]:
    """A serializer placing ``_NAIVE_YEAR_ONE`` in a ``DateTimeField`` at ``shape``'s depth.

    Returns the bound serializer and the dotted path the field's error flattens to.
    """
    fields: dict[str, object]
    if shape == "list-child":
        fields = {"stamps": serializers.ListField(child=serializers.DateTimeField())}
        data: dict[str, object] = {"stamps": [_IN_RANGE, _NAIVE_YEAR_ONE]}
        path = "stamps.1"
    elif shape == "nested":
        fields = {"stamp": _StampSerializer()}
        data = {"stamp": {"at": _NAIVE_YEAR_ONE}}
        path = "stamp.at"
    elif shape == "many-nested":
        fields = {"stamps": _StampSerializer(many=True)}
        data = {"stamps": [{"at": _IN_RANGE}, {"at": _NAIVE_YEAR_ONE}]}
        path = "stamps.1.at"
    else:
        fields = {"at": _SubclassedDateTimeField()}
        data = {"at": _NAIVE_YEAR_ONE}
        path = "at"
    serializer_class = type("ShapeSerializer", (serializers.Serializer,), fields)
    return serializer_class(data=data), path


@pytest.mark.parametrize(
    "shape",
    [
        "list-child",
        "nested",
        "many-nested",
        "subclass",
    ],
)
def test_datetime_overflow_is_drf_overflow_error_at_every_depth(shape: str) -> None:
    """A ``DateTimeField`` DRF cannot place answers its ``overflow`` error, keyed at its depth.

    A naive year-1 datetime made aware in Tokyo raises a raw ``OverflowError`` inside
    ``is_valid()`` from a ``ListField`` child, a nested serializer, a ``many=True`` nested
    serializer and a ``DateTimeField`` subclass alike; after the translation each fails
    ``is_valid()`` with DRF's ``overflow`` error, which the flattener keys to the field's
    dotted path. Only the per-request field instances are wrapped: the declared field and
    the class keep DRF's ``to_internal_value``.
    """
    serializer, path = _stamp_shape(shape)
    serializer_resolvers._translate_datetime_overflow(serializer)
    with override_settings(TIME_ZONE="Asia/Tokyo"):
        assert not serializer.is_valid()

    flat = serializer_resolvers.serializer_errors_to_field_errors(
        serializer_errors(serializer),
        {},
    )
    assert [(fe.field, fe.messages, fe.codes) for fe in flat] == [
        (path, _OUT_OF_RANGE, ["overflow"]),
    ]
    wrapped = [
        node
        for node, _owner in serializer_resolvers._validation_tree(serializer)
        if "to_internal_value" in vars(node)
    ]
    assert wrapped
    assert all(isinstance(node, serializers.DateTimeField) for node in wrapped)
    declared: list[object] = [
        *declared_fields_of(type(serializer)).values(),
        *declared_fields_of(_StampSerializer).values(),
    ]
    stamps = declared_fields_of(type(serializer)).get("stamps")
    if isinstance(stamps, serializers.ListField):
        declared.append(list_child_of(stamps))
    assert not any("to_internal_value" in vars(field) for field in declared)
    assert serializers.DateTimeField.to_internal_value is _DRF_TO_INTERNAL_VALUE


@pytest.mark.parametrize(
    ("value", "settings"),
    [
        pytest.param(_NAIVE_YEAR_ONE, {"TIME_ZONE": "Asia/Tokyo"}, id="naive-under-tokyo"),
        pytest.param(_AWARE_YEAR_ONE, {"USE_TZ": False}, id="aware-without-time-zone-support"),
    ],
)
def test_datetime_overflow_a_field_override_handles_itself_is_left_to_it(
    value: str,
    settings: dict[str, object],
) -> None:
    """A ``to_internal_value`` override that answers the ``OverflowError`` itself keeps its answer.

    The translation wraps the instance's own method, so the consumer override runs first
    and the wrapper never sees an overflow it caught: the value it returns validates.
    """
    serializer_class = type(
        "TolerantSerializer",
        (serializers.Serializer,),
        {"at": _OverflowTolerantDateTimeField()},
    )
    serializer = serializer_class(data={"at": value})
    serializer_resolvers._translate_datetime_overflow(serializer)
    with override_settings(**settings):
        assert serializer.is_valid(), serializer_errors(serializer)

    assert validated_data_of(serializer) == {"at": _TOLERATED}


class SerializerSpelledDecimalTarget(Model):
    """An M2M target keyed by a ``DecimalField`` without ``max_digits``."""

    code: models.DecimalField[str | float | decimal.Decimal | Combinable, decimal.Decimal] = (
        models.DecimalField(primary_key=True, max_digits=None, decimal_places=None)
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "serializer_spelled_decimal_target"


class SerializerSpelledStampTarget(Model):
    """An M2M target keyed by an aware ``DateTimeField``."""

    stamp: models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ] = models.DateTimeField(primary_key=True)

    class Meta:
        app_label = "products"
        managed = False
        db_table = "serializer_spelled_stamp_target"


class SerializerSpelledDecimalOwner(Model):
    """A row relating to the decimal-keyed target by an M2M."""

    name: models.TextField[str | Combinable, str] = models.TextField()
    decimal_targets: models.ManyToManyField[SerializerSpelledDecimalTarget, Model] = (
        models.ManyToManyField(SerializerSpelledDecimalTarget, related_name="+", blank=True)
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "serializer_spelled_decimal_owner"


class SerializerSpelledStampOwner(Model):
    """A row relating to the datetime-keyed target by an M2M.

    An owner of its own: Django reads a ``DecimalField`` without ``decimal_places`` only
    from 6.1, so the datetime row, kept off the decimal owner, runs on every supported
    Django.
    """

    name: models.TextField[str | Combinable, str] = models.TextField()
    stamp_targets: models.ManyToManyField[SerializerSpelledStampTarget, Model] = (
        models.ManyToManyField(SerializerSpelledStampTarget, related_name="+", blank=True)
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "serializer_spelled_stamp_owner"


def _spelled_key_models(stored: object) -> tuple[type[Model], type[Model]]:
    """The M2M target keyed by ``stored``'s kind and the owner relating to it."""
    if isinstance(stored, decimal.Decimal):
        return SerializerSpelledDecimalTarget, SerializerSpelledDecimalOwner
    return SerializerSpelledStampTarget, SerializerSpelledStampOwner


def _spelled_key_owner_schema(stored: object) -> DjangoSchema:
    """A create ``SerializerMutation`` writing the M2M of ``stored``'s owner by raw pk."""
    target, owner = _spelled_key_models(stored)
    prefix = "decimal" if isinstance(stored, decimal.Decimal) else "stamp"
    _ = type(
        f"{target.__name__}T",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": target, "fields": "__all__", "primary": True})},
    )

    class SpelledKeyOwnerT(DjangoType):
        class Meta:
            model = owner
            fields = ("name",)
            primary = True

    class SpelledKeyOwnerSerializer(ModelSerializerBase[Model]):
        class Meta:
            model = owner
            fields = ("name", f"{prefix}_targets")

    class CreateSpelledKeyOwner(SerializerMutation):
        class Meta:
            serializer_class = SpelledKeyOwnerSerializer
            operation = "create"
            permission_classes = []

    @strawberry.type
    class Mutation:
        create_spelled_key_owner = DjangoMutationField(CreateSpelledKeyOwner)

    finalize_django_types()
    del SpelledKeyOwnerT
    return DjangoSchema(query=PingQuery, mutation=Mutation)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("stored", "spelled"),
    [
        *(
            pytest.param(
                decimal.Decimal(stored),
                spelled,
                id=case_id,
                marks=pytest.mark.skipif(
                    connections["default"].vendor != "sqlite" or django.VERSION < (6, 1),
                    reason="SQLite stores the value it is bound, read back from Django 6.1",
                ),
            )
            for stored, spelled, case_id in (
                ("2.5", "2.50", "trailing-zero"),
                ("7", "7.0", "one-fractional-zero"),
                ("7", "7.00", "two-fractional-zeros"),
                ("70", "7E+1", "exponent"),
                ("0", "0.00", "zero"),
            )
        ),
        pytest.param(
            datetime.datetime(2024, 1, 1, 8, tzinfo=datetime.timezone.utc),
            "2024-01-01T10:00:00+02:00",
            id="aware-datetime-in-another-offset",
        ),
    ],
)
def test_serializer_m2m_ids_spelling_a_stored_key_differently_link_its_row(
    stored: object,
    spelled: str,
) -> None:
    """A serializer M2M id names its row by the key's value, as the ``pk__in`` lookup does.

    The batched membership check keys the requested ids and the rows it found by the pk
    column's value, so ``2.50`` is the stored ``2.5`` and an aware datetime in a ``+02:00``
    offset is the row stored in UTC: the write links the row, never the uniform
    "Invalid id" error.
    """
    is_decimal = isinstance(stored, decimal.Decimal)
    target, owner_model = _spelled_key_models(stored)
    prefix = "decimal" if is_decimal else "stamp"
    with contextlib.ExitStack() as tables:
        for model in (target, owner_model):
            tables.enter_context(_synthetic_table(model))
        _ = target._default_manager.create(pk=stored)
        request = HttpRequest()
        request.user = User(username="u")
        result = _spelled_key_owner_schema(stored).execute_sync(
            "mutation($d: SpelledKeyOwnerSerializerInput!){ createSpelledKeyOwner(data:$d){ "
            "errors{ field messages } } }",
            variable_values={"d": {"name": "owner", f"{prefix}Targets": [spelled]}},
            context_value=SimpleNamespace(request=request),
        )
        assert result.errors is None, result.errors
        assert result.data == {"createSpelledKeyOwner": {"errors": []}}
        owner = owner_model._default_manager.get(name="owner")
        if isinstance(owner, SerializerSpelledDecimalOwner):
            linked = [pk_of(row) for row in owner.decimal_targets.all()]
        else:
            assert isinstance(owner, SerializerSpelledStampOwner)
            linked = [pk_of(row) for row in owner.stamp_targets.all()]
        assert linked == [stored]


class SerializerCentsDecimalField(models.DecimalField[object, object]):
    """A project ``DecimalField`` whose ``to_python`` rounds to cents: the value its save binds."""

    @override
    def to_python(self, value: object) -> object:
        number = object_result(super().to_python, value)
        return (
            number.quantize(decimal.Decimal("0.01"))
            if isinstance(number, decimal.Decimal)
            else number
        )


class SerializerUnboundedAmount(Model):
    """Decimal columns a serializer can carry past PostgreSQL ``numeric``'s format.

    ``amount`` and the nullable ``spare`` have no ``max_digits`` (Django's unconstrained
    ``numeric``, from 6.1), which DRF's ``ModelSerializer`` cannot build a field for, so
    the serializer declares ``DecimalField(max_digits=None, decimal_places=None)``, which
    holds no digits; ``priced`` is bounded, and its validator counts no digit for a
    zero's positive exponent; ``rounded`` is a field subclass whose ``to_python`` rounds
    to cents.
    """

    amount: models.DecimalField[str | float | decimal.Decimal | Combinable, decimal.Decimal] = (
        models.DecimalField(max_digits=None, decimal_places=None)
    )
    spare: models.DecimalField[
        str | float | decimal.Decimal | Combinable | None,
        decimal.Decimal | None,
    ] = models.DecimalField(max_digits=None, decimal_places=None, null=True, blank=True)
    priced: models.DecimalField[
        str | float | decimal.Decimal | Combinable | None,
        decimal.Decimal | None,
    ] = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rounded: SerializerCentsDecimalField = SerializerCentsDecimalField(
        max_digits=None,
        decimal_places=None,
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "serializer_unbounded_amount"


class UnboundedAmountSerializer(ModelSerializerBase[SerializerUnboundedAmount]):
    """A serializer declaring a ``DecimalField`` without ``max_digits`` for each column."""

    amount = serializers.DecimalField(max_digits=None, decimal_places=None)
    spare = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        required=False,
        allow_null=True,
    )
    priced = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        required=False,
        allow_null=True,
    )
    rounded = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SerializerUnboundedAmount
        fields = (
            "amount",
            "spare",
            "priced",
            "rounded",
        )


#: A column of ``SerializerUnboundedAmount`` and a spelling its serializer field and
#: validator pass that ``numeric`` refuses: past the integer digits, the fraction digits,
#: or a zero's written exponent.
_PAST_NUMERIC = [
    pytest.param("amount", "1e1000000", id="huge-exponent"),
    pytest.param("amount", "-1e1000000", id="negative-huge-exponent"),
    pytest.param("amount", "1e-1000000", id="tiny-exponent"),
    pytest.param("amount", "1E+131072", id="131073-integer-digits"),
    pytest.param("amount", "0E-16384", id="zero-16384-fraction-digits"),
    pytest.param("spare", "1e1000000", id="nullable-huge-exponent"),
    pytest.param("priced", "0E+1073741824", id="bounded-zero-past-exponent-limit"),
]

_REQUIRES_UNBOUNDED_DECIMAL = pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="a DecimalField without max_digits is read back from Django 6.1",
)


def _write_amount_via_serializer(
    operation: str,
    data: dict[str, object],
    pk: object = None,
) -> object:
    """Run the serializer flavor's ``operation`` with ``data``; its payload."""

    class SerializerUnboundedAmountT(DjangoType):
        class Meta:
            model = SerializerUnboundedAmount
            fields = (
                "id",
                "amount",
                "spare",
                "priced",
            )
            primary = True

    class CreateAmount(SerializerMutation):
        class Meta:
            serializer_class = UnboundedAmountSerializer
            operation = "create"
            permission_classes = [AllowAll]

    class UpdateAmount(SerializerMutation):
        class Meta:
            serializer_class = UnboundedAmountSerializer
            operation = "update"
            permission_classes = [AllowAll]

    @strawberry.type
    class Mutation:
        create_amount = DjangoMutationField(CreateAmount)
        update_amount = DjangoMutationField(UpdateAmount)

    finalize_django_types()
    del SerializerUnboundedAmountT
    selection = "{ result { amount } errors { field messages codes } }"
    if operation == "create":
        document = (
            "mutation($d: UnboundedAmountSerializerInput!) "
            f"{{ createAmount(data: $d) {selection} }}"
        )
        variables: dict[str, object] = {"d": data}
    else:
        document = (
            "mutation($id: ID!, $d: UnboundedAmountSerializerPartialInput!) "
            f"{{ updateAmount(id: $id, data: $d) {selection} }}"
        )
        variables = {"id": str(pk), "d": data}
    request = HttpRequest()
    request.user = User(username="u")
    result = DjangoSchema(query=PingQuery, mutation=Mutation).execute_sync(
        document,
        variable_values=variables,
        context_value=SimpleNamespace(request=request),
    )
    assert result.errors is None, result.errors
    assert is_object_dict(result.data), result.data
    return result.data[f"{operation}Amount"]


def _stored_serializer_amounts() -> list[tuple[object, ...]]:
    """Every ``SerializerUnboundedAmount`` row's three decimals."""
    return list(
        SerializerUnboundedAmount.objects.order_by("pk").values_list("amount", "spare", "priced"),
    )


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(("column", "wire"), _PAST_NUMERIC)
def test_serializer_write_refuses_a_decimal_past_postgresql_numeric(
    operation: str,
    column: str,
    wire: str,
) -> None:
    """A decimal the serializer validates but PostgreSQL cannot bind is the field's error.

    ``is_valid()`` passes it (a declared ``DecimalField`` without ``max_digits`` holds no
    digits and runs no model validator) and PostgreSQL's ``numeric_in`` refuses it at the
    save, a ``DataError`` no save mapper owns. The serializer flavor answers the field's
    ``invalid`` error before any write instead, with nothing written.
    """
    with numeric_refusing_postgresql(SerializerUnboundedAmount):
        pk = (
            saved_pk(SerializerUnboundedAmount.objects.create(amount=decimal.Decimal(7)))
            if operation == "update"
            else None
        )
        before = _stored_serializer_amounts()
        payload = _write_amount_via_serializer(operation, {"amount": "7", column: wire}, pk)

        assert payload == {
            "result": None,
            "errors": [
                {
                    "field": column,
                    "messages": ["Enter a value the database can represent."],
                    "codes": ["invalid"],
                },
            ],
        }
        assert _stored_serializer_amounts() == before


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("column", ["amount", "spare", "priced"])
def test_serializer_write_stores_a_decimal_within_postgresql_numeric(
    operation: str,
    column: str,
) -> None:
    """A decimal PostgreSQL's ``numeric`` holds is written through the same stand-in."""
    with numeric_refusing_postgresql(SerializerUnboundedAmount):
        pk = (
            saved_pk(SerializerUnboundedAmount.objects.create(amount=decimal.Decimal(7)))
            if operation == "update"
            else None
        )
        payload = _write_amount_via_serializer(operation, {"amount": "7", column: "12.5"}, pk)

        assert is_object_dict(payload), payload
        assert payload["errors"] == []
        stored = read_attr(SerializerUnboundedAmount.objects.get(), column)
        assert stored == decimal.Decimal("12.5")


_ROUNDED_TO_ZERO = [
    pytest.param("1e-1000000", id="tiny-exponent"),
    pytest.param("0." + "0" * 16383 + "5", id="16384-fraction-digits"),
]


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("wire", _ROUNDED_TO_ZERO)
def test_serializer_write_holds_the_decimal_its_column_to_python_gives(
    operation: str,
    wire: str,
) -> None:
    """A validated decimal the column's ``to_python`` rounds to a cent ``numeric`` holds is stored.

    DRF hands the spelling as sent to the save, which binds the value ``to_python`` gives
    (``0.00``), so the write stores it rather than refusing the spelling.
    """
    with numeric_refusing_postgresql(SerializerUnboundedAmount):
        pk = (
            saved_pk(SerializerUnboundedAmount.objects.create(amount=decimal.Decimal(7)))
            if operation == "update"
            else None
        )
        payload = _write_amount_via_serializer(operation, {"amount": "7", "rounded": wire}, pk)

        assert is_object_dict(payload), payload
        assert payload["errors"] == []
        assert SerializerUnboundedAmount.objects.get().rounded == decimal.Decimal(0)


def _unique_amount_model() -> type[Model]:
    """A synthetic integer column whose generated DRF field has a UniqueValidator."""
    return type(
        "UnpatchedUniqueAmount",
        (Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(unique=True),
            "Meta": type("Meta", (), {"app_label": "scalars", "managed": False}),
        },
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connections["default"].vendor != "sqlite", reason="SQLite integer binding")
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("duplicate", [False, True], ids=["available", "duplicate"])
def test_serializer_unique_validator_without_django_stubs_runtime_patch(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    *,
    duplicate: bool,
) -> None:
    """An ordinary consumer's unpatched Field class supports native uniqueness outcomes.

    Fakeshop enables django-stubs' runtime patch globally; deleting that hook is a
    configuration test no request under those settings can express.
    """
    model = _unique_amount_model()
    serializer = _serializer_over(model, ("amount",))
    with _synthetic_table(model):
        row = model._default_manager.create(amount=1)
        _ = model._default_manager.create(amount=2)
        schema, create_input, update_input = _blank_columns_schema(serializer, model)
        monkeypatch.delattr(models.Field, "__class_getitem__")
        payload = _run_row_write(
            schema,
            update_input if operation == "update" else create_input,
            {"amount": 2 if duplicate else 1 if operation == "update" else 3},
            saved_pk(row) if operation == "update" else None,
        )
    if duplicate:
        assert json_at(payload, "result") is None
        assert json_at(payload, "errors", 0, "field") == "amount"
        assert json_at(payload, "errors", 0, "codes") == ["unique"]
    else:
        assert json_at(payload, "errors") == []
        assert json_at(payload, "result", "id") is not None


@pytest.mark.parametrize("unique", [False, True], ids=["ordinary-present", "unique-omitted"])
def test_guard_installation_does_not_run_a_star_fields_native_source_lookup(
    *,
    unique: bool,
) -> None:
    """Guard installation preserves native validators and inactive source lookup order.

    Public Meta source ownership refuses writable star fields through
    django_strawberry_framework/rest_framework/inputs.py::raise_writable_source_ownership_errors,
    so a live request cannot reach this raw DRF configuration. The direct installer
    must still avoid forcing a native validator's lookup before it runs.
    """
    validators = [UniqueValidator(queryset=ScalarSpecimen.objects.all())] if unique else []

    class MergeText(serializers.CharField):
        @override
        def run_validation(self, data: object = serializers.empty) -> dict[str, str]:
            cleaned = require_instance(object_result(super().run_validation, data), str)
            return {"text": cleaned}

    class StarSerializer(serializers.Serializer[object]):
        merged = MergeText(source="*", required=False, validators=validators)

    data: dict[str, object] = {} if unique else {"merged": "clean"}
    native = StarSerializer(data=data)
    assert native.is_valid(), serializer_errors(native)
    held = StarSerializer(data=data)
    serializer_resolvers._pin_validator_querysets(held, "default")
    before = tuple(bound_fields(held)["merged"].validators)
    assert bound_fields(held)["merged"].source_attrs == []
    with write_pipeline("default", lock=False):
        serializer_resolvers._hold_serializer_values(held, {})
    assert all(
        original is current
        for original, current in zip(before, bound_fields(held)["merged"].validators, strict=True)
    )
    assert held.is_valid(), serializer_errors(held)
    assert (
        validated_data_of(held)
        == validated_data_of(native)
        == ({} if unique else {"text": "clean"})
    )
