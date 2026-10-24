"""Shared mutation-error constructors: leaf shapes, the Django mapper, the code vocabulary.

Scalar / byte / lazy-translation message coercion and the ``ValidationError``
mapping read Python values no wire request can shape. Consumer envelopes
(constraint ``codes``, ``__all__`` sentinel, relation ``not_found``) live in
``examples/fakeshop/test_query/test_products_api.py``. The error key map
primitives (``build_error_key_map``, ``rekey_error_segment``,
``model_field_error_names``) are pinned here directly; the per-flavor keying matrix
is ``tests/utils/test_error_keys.py``.

``unstorable_temporal`` is pinned live per flavor on SQLite and PostgreSQL in
``examples/fakeshop/test_query/test_scalars_mutation_api.py``; the rows here hold the
lines no live SQLite request reaches: a stand-in alias whose backend stores aware
datetimes itself (the PostgreSQL rule), an ``ArrayField`` column (a PostgreSQL-only
column, stood in for by ``tests/_postgres_fields.py::FakeArrayField``), MySQL's own
operations, and, on the Postgres tier, the real connection and ``ArrayField``.
"""

import ast
import datetime
import uuid
import warnings
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalar_models
from django.core.exceptions import ValidationError
from django.db import DEFAULT_DB_ALIAS, DataError, connections, models, transaction
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.mysql.operations import DatabaseOperations as MySQLOperations
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.models import Model
from django.test import override_settings
from django.utils.translation import gettext_lazy as _
from typing_extensions import override

from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
from django_strawberry_framework.utils import errors as errors_module
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_CONFLICT,
    FIELD_ERROR_CODE_CONSTRAINT,
    FIELD_ERROR_CODE_INVALID,
    FIELD_ERROR_CODE_NOT_FOUND,
    FIELD_ERROR_CODE_NULL,
    FIELD_ERROR_CODE_PROTECTED,
    FIELD_ERROR_CODE_TRUNCATED,
    FILTER_INVALID_ERROR_CODE,
    GLOBALID_INVALID_ERROR_CODE,
    GLOBALID_UNVALIDATABLE_ERROR_CODE,
    PAGINATION_INVALID_ERROR_CODE,
    build_error_key_map,
    coded_error_extensions,
    empty_validation_error,
    field_error,
    join_error_path,
    model_field_error_names,
    null_field_error,
    rekey_error_segment,
    relation_field_error,
    save_time_error_key_map,
    unbindable_temporal,
    unstorable_temporal,
    validation_error_to_field_errors,
)
from django_strawberry_framework.utils.inputs import RELATION_SINGLE, SCALAR, InputFieldSpec
from tests._postgres_fields import FakeArrayField

if TYPE_CHECKING:
    from django_strawberry_framework.utils.errors import ErrorKeyMap


class _RaisingMessage:
    @override
    def __str__(self) -> str:
        raise RuntimeError("message string")


def test_validation_error_message_object_render_propagates() -> None:
    """A consumer message object renders through its own ``__str__``; what it raises propagates."""
    with pytest.raises(RuntimeError, match="message string"):
        validation_error_to_field_errors(ValidationError({"name": [_RaisingMessage()]}))


@pytest.mark.parametrize(
    "payload",
    [
        ValidationError("value %(v)s", params={"w": 3}),
        ValidationError({"name": ValidationError("value %(v)s", params={"w": 3})}),
    ],
    ids=["non-field", "field"],
)
def test_validation_error_params_mismatch_propagates_like_django(payload: ValidationError) -> None:
    """A message whose params do not match its placeholders raises Django's own ``KeyError``.

    Django's ``ValidationError.messages`` interpolates ``message %= params``
    unguarded, so the admin and forms raise the same error for the same
    consumer ``clean()``; the mapper renders through that path and never
    substitutes the raw template.
    """
    with pytest.raises(KeyError, match="'v'"):
        list(ValidationError("value %(v)s", params={"w": 3}))
    with pytest.raises(KeyError, match="'v'"):
        validation_error_to_field_errors(payload)


def test_relation_field_error_message_is_pinned() -> None:
    leaf = relation_field_error("categoryId")
    assert leaf.field == "categoryId"
    assert leaf.messages == ["Invalid id for relation 'categoryId'."]
    assert leaf.codes == [FIELD_ERROR_CODE_INVALID]


def test_validation_error_mapper_keeps_normal_codes_and_non_field_shape() -> None:
    (error,) = validation_error_to_field_errors(
        ValidationError("whole-object", code="invalid"),
    )

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.path == []
    assert error.messages == ["whole-object"]
    assert error.codes == ["invalid"]


@pytest.mark.parametrize(
    ("payload", "field"),
    [({}, NON_FIELD_ERROR_KEY), ([], NON_FIELD_ERROR_KEY), ({"name": []}, "name")],
)
def test_validation_error_mapper_never_returns_an_empty_envelope(
    payload: dict[str, list[str]] | list[str],
    field: str,
) -> None:
    (error,) = validation_error_to_field_errors(ValidationError(payload))

    assert error.field == field
    assert error.messages == ["Validation failed without error details."]
    assert error.codes == ["invalid"]


def test_field_error_handles_scalar_integers_booleans_and_floats() -> None:
    error_int = field_error("count", 123, codes=456)
    assert error_int.field == "count"
    assert error_int.messages == ["123"]
    assert error_int.codes == ["456"]

    error_bool = field_error("active", False, codes=True)  # noqa: FBT003 - the bool is the value under test
    assert error_bool.field == "active"
    assert error_bool.messages == ["False"]
    assert error_bool.codes == ["True"]

    error_float = field_error("score", 98.6)
    assert error_float.field == "score"
    assert error_float.messages == ["98.6"]
    assert error_float.codes == []


@pytest.mark.parametrize(
    ("message", "code"),
    [
        (b"invalid_token", b"invalid"),
        (bytearray(b"invalid_token"), bytearray(b"invalid")),
        (memoryview(b"invalid_token"), memoryview(b"invalid")),
    ],
    ids=["bytes", "bytearray", "memoryview"],
)
def test_field_error_handles_byte_strings_without_splitting(message: object, code: object) -> None:
    """A bytes-like message or code is one leaf rendered whole, never split per byte."""
    error = field_error("token", message, codes=code)

    assert error.field == "token"
    assert error.messages == [str(message)]
    assert error.codes == [str(code)]


def test_field_error_handles_lazy_translation_proxy_without_character_iteration() -> None:
    """Verify Django lazy translation proxies (Promise) are treated as atomic strings."""
    lazy_msg = _("This field is required.")
    lazy_code = _("required")
    error = field_error("title", lazy_msg, codes=lazy_code)

    assert error.field == "title"
    assert error.messages == ["This field is required."]
    assert error.codes == ["required"]


def test_validation_error_mapper_handles_lazy_translation_objects() -> None:
    """Verify ValidationError containing lazy translations formats cleanly into FieldError."""
    lazy_msg = _("Invalid choice selected.")
    ve_dict = ValidationError({"status": [lazy_msg]})
    errors = validation_error_to_field_errors(ve_dict)

    assert len(errors) == 1
    assert errors[0].field == "status"
    assert errors[0].messages == ["Invalid choice selected."]

    ve_scalar = ValidationError(_("Global model validation error."), code="invalid")
    (global_err,) = validation_error_to_field_errors(ve_scalar)
    assert global_err.field == NON_FIELD_ERROR_KEY
    assert global_err.messages == ["Global model validation error."]
    assert global_err.codes == ["invalid"]


@pytest.mark.parametrize(
    ("prefix", "segment", "expected"),
    [
        ("", "name", "name"),
        ("items", "0", "items.0"),
        ("items.0", "name", "items.0.name"),
        ("items.0", "__all__", "items.0.__all__"),
    ],
)
def test_join_error_path_variations(prefix: str, segment: str, expected: str) -> None:
    """Verify join_error_path joins prefixes and child segments correctly."""
    assert join_error_path(prefix, segment) == expected


# -------------------------------------------------------------------------
# The error-code vocabulary: public wire contract (bug-hunt batch 13 pins)
# -------------------------------------------------------------------------


def test_field_error_code_vocabulary_is_the_public_wire_contract() -> None:
    assert FIELD_ERROR_CODE_INVALID == "invalid"
    assert FIELD_ERROR_CODE_NULL == "null"
    assert FIELD_ERROR_CODE_CONSTRAINT == "constraint"
    assert FIELD_ERROR_CODE_NOT_FOUND == "not_found"
    assert FIELD_ERROR_CODE_PROTECTED == "protected"
    assert FIELD_ERROR_CODE_CONFLICT == "conflict"
    assert FIELD_ERROR_CODE_TRUNCATED == "truncated"
    assert GLOBALID_INVALID_ERROR_CODE == "GLOBALID_INVALID"
    assert GLOBALID_UNVALIDATABLE_ERROR_CODE == "GLOBALID_UNVALIDATABLE"
    assert FILTER_INVALID_ERROR_CODE == "FILTER_INVALID"
    assert PAGINATION_INVALID_ERROR_CODE == "PAGINATION_INVALID"
    for name in (
        "FIELD_ERROR_CODE_INVALID",
        "FIELD_ERROR_CODE_NULL",
        "FIELD_ERROR_CODE_CONSTRAINT",
        "FIELD_ERROR_CODE_NOT_FOUND",
        "FIELD_ERROR_CODE_PROTECTED",
        "FIELD_ERROR_CODE_CONFLICT",
        "FIELD_ERROR_CODE_TRUNCATED",
        "GLOBALID_INVALID_ERROR_CODE",
        "GLOBALID_UNVALIDATABLE_ERROR_CODE",
        "FILTER_INVALID_ERROR_CODE",
        "PAGINATION_INVALID_ERROR_CODE",
        "coded_error_extensions",
        "empty_validation_error",
        "null_field_error",
    ):
        assert name in errors_module.__all__


def test_coded_error_extensions_shape() -> None:
    assert coded_error_extensions("GLOBALID_INVALID") == {"code": "GLOBALID_INVALID"}
    assert coded_error_extensions("FILTER_INVALID", errors={"name": "bad"}) == {
        "code": "FILTER_INVALID",
        "errors": {"name": "bad"},
    }
    assert coded_error_extensions("X", bound=5, limit=3, charged=7) == {
        "code": "X",
        "bound": 5,
        "limit": 3,
        "charged": 7,
    }


def test_null_field_error_and_empty_validation_error_leaf_shapes() -> None:
    null_leaf = null_field_error("categoryId")
    assert null_leaf.field == "categoryId"
    assert null_leaf.messages == ["This field cannot be null."]
    assert null_leaf.codes == [FIELD_ERROR_CODE_NULL]
    assert null_leaf.path == ["categoryId"]

    root_empty = empty_validation_error()
    assert root_empty.field == NON_FIELD_ERROR_KEY
    assert root_empty.messages == ["Validation failed without error details."]
    assert root_empty.codes == [FIELD_ERROR_CODE_INVALID]
    assert root_empty.path == []

    named_empty = empty_validation_error("name")
    assert named_empty.field == "name"
    assert named_empty.path == ["name"]


def test_conflict_code_reaches_the_leaf_through_the_public_ctor() -> None:
    leaf = field_error(
        "id",
        "The row was changed or removed by a concurrent operation; retry.",
        codes=FIELD_ERROR_CODE_CONFLICT,
    )

    assert leaf.field == "id"
    assert leaf.codes == [FIELD_ERROR_CODE_CONFLICT]
    assert leaf.path == ["id"]


def test_validation_error_mapper_keys_django_non_field_bucket_to_sentinel() -> None:
    exception = ValidationError(
        {"__all__": [ValidationError("model wide", code="mw")], "name": [ValidationError("bad")]},
    )

    by_field = {error.field: error for error in validation_error_to_field_errors(exception)}

    assert by_field[NON_FIELD_ERROR_KEY].path == []
    assert by_field[NON_FIELD_ERROR_KEY].messages == ["model wide"]
    assert by_field[NON_FIELD_ERROR_KEY].codes == ["mw"]
    assert by_field["name"].messages == ["bad"]


def test_errors_module_performs_no_settings_reads() -> None:
    """The error leaf module is configuration-free (layering pin)."""
    source = Path(errors_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename="errors.py")

    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("DEBUG", "settings"):
            hits.append(f"attr {node.attr} @ line {node.lineno}")
        if isinstance(node, ast.Name) and node.id in ("settings", "conf"):
            hits.append(f"name {node.id} @ line {node.lineno}")

    assert hits == [], hits


# ---------------------------------------------------------------------------
# Error keying: validator-side name -> GraphQL input name
# ---------------------------------------------------------------------------


def _keys(errors: list[FieldError]) -> list[tuple[str, list[str], list[str]]]:
    """``(field, path, messages)`` per leaf, in envelope order."""
    return [(fe.field, fe.path, fe.messages) for fe in errors]


def test_rekey_error_segment_never_rekeys_the_non_field_sentinel() -> None:
    """``"__all__"`` is checked before the map, so even a map entry for it is ignored."""
    key_map: ErrorKeyMap = {NON_FIELD_ERROR_KEY: ("hijacked", {"x": ("y", None)})}

    assert rekey_error_segment(NON_FIELD_ERROR_KEY, key_map) == (NON_FIELD_ERROR_KEY, {})
    (error,) = validation_error_to_field_errors(
        ValidationError({NON_FIELD_ERROR_KEY: ["model-wide"]}),
        key_map,
    )
    assert (error.field, error.path) == (NON_FIELD_ERROR_KEY, [])


def test_rekey_error_segment_keeps_an_unmapped_name_verbatim() -> None:
    """A name with no map entry (a field the input does not expose) keeps its own name."""
    key_map: ErrorKeyMap = {"category": ("categoryId", None)}

    assert rekey_error_segment("is_private", key_map) == ("is_private", {})
    assert rekey_error_segment("category", key_map) == ("categoryId", {})
    errors = validation_error_to_field_errors(
        ValidationError({"category": ["bad"], "is_private": ["hidden"]}),
        key_map,
    )
    assert _keys(errors) == [
        ("categoryId", ["categoryId"], ["bad"]),
        ("is_private", ["is_private"], ["hidden"]),
    ]


def test_validation_error_mapper_without_a_map_keys_every_name_verbatim() -> None:
    """``key_map=None`` (and an omitted map) keeps each ``error_dict`` name as raised."""
    exc = ValidationError({"category": ["bad"], NON_FIELD_ERROR_KEY: ["whole"]})

    assert _keys(validation_error_to_field_errors(exc, None)) == [
        ("category", ["category"], ["bad"]),
        (NON_FIELD_ERROR_KEY, [], ["whole"]),
    ]
    assert _keys(validation_error_to_field_errors(exc)) == _keys(
        validation_error_to_field_errors(exc, None),
    )


def test_validation_error_mapper_resolves_swapped_names_in_one_lookup() -> None:
    """Two inputs renamed onto each other's names each re-key exactly once."""
    key_map: ErrorKeyMap = {"name": ("description", None), "description": ("name", None)}
    errors = validation_error_to_field_errors(
        ValidationError({"name": ["on name"], "description": ["on description"]}),
        key_map,
    )
    assert _keys(errors) == [
        ("description", ["description"], ["on name"]),
        ("name", ["name"], ["on description"]),
    ]


def test_validation_error_mapper_lets_a_rename_share_an_unexposed_name() -> None:
    """A rename onto an unexposed field's name yields two errors on one key, never merged."""
    key_map: ErrorKeyMap = {"name": ("category", None)}
    errors = validation_error_to_field_errors(
        ValidationError({"name": ["on name"], "category": ["on the unexposed FK"]}),
        key_map,
    )
    assert _keys(errors) == [
        ("category", ["category"], ["on name"]),
        ("category", ["category"], ["on the unexposed FK"]),
    ]


def test_build_error_key_map_recurses_into_nested_specs() -> None:
    """A nested field carries its own level's map; a flat field carries ``None``."""
    child = (
        InputFieldSpec(
            input_attr="alt_branches",
            graphql_name="altBranches",
            target_name="alt_branches",
            kind=SCALAR,
        ),
    )
    specs = [
        InputFieldSpec(
            input_attr="category_id",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            # The map reads only ``nested_specs``; the serializer's nested kinds live
            # behind the DRF soft dependency, so a plain kind stands in.
            kind=SCALAR,
            nested_specs=child,
        ),
    ]
    key_map = build_error_key_map(specs)

    assert key_map == {
        "category": ("categoryId", None),
        "shelves": ("shelves", {"alt_branches": ("altBranches", None)}),
    }
    segment, child_map = rekey_error_segment("shelves", key_map)
    assert segment == "shelves"
    assert rekey_error_segment("alt_branches", child_map) == ("altBranches", {})


def test_build_error_key_map_keyed_by_keys_of_is_one_level() -> None:
    """``keys_of`` replaces ``target_name`` as the validator-side names, top level only.

    ``keys_of`` reads one model's field names, so a nested field gets no child map: a
    nested level writes another model, whose names it cannot read.
    """
    child = (
        InputFieldSpec(
            input_attr="code",
            graphql_name="shelfCode",
            target_name="shelf_code",
            kind=SCALAR,
            source="code",
        ),
    )
    specs = [
        InputFieldSpec(
            input_attr="full_name",
            graphql_name="fullName",
            target_name="full_name",
            kind=SCALAR,
            source="name",
        ),
        InputFieldSpec(
            input_attr="is_private",
            graphql_name="isPrivate",
            target_name="is_private",
            kind=SCALAR,
        ),
        InputFieldSpec(
            input_attr="category_id",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            # The map reads only ``nested_specs``; the serializer's nested kinds live
            # behind the DRF soft dependency, so a plain kind stands in.
            kind=SCALAR,
            nested_specs=child,
        ),
    ]

    def model_names(spec: InputFieldSpec) -> tuple[str, ...]:
        name = spec.source or spec.target_name
        return (name, f"{name}_id") if spec.kind == RELATION_SINGLE else (name,)

    by_source = build_error_key_map(specs, keys_of=model_names)

    assert by_source == {
        "name": ("fullName", None),
        "is_private": ("isPrivate", None),
        "category": ("categoryId", None),
        "category_id": ("categoryId", None),
        "shelves": ("shelves", None),
    }
    assert "full_name" not in by_source


def test_build_error_key_map_never_lets_an_alias_displace_a_primary_name() -> None:
    """Every primary name is entered before any alias; an alias fills only an unclaimed name.

    A synthetic ``keys_of`` hands two specs overlapping name tuples, so the two-pass
    rule is pinned on its own rather than through a serializer the ownership guards
    would refuse.
    """
    specs = [
        InputFieldSpec(
            input_attr="category",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
        InputFieldSpec(
            input_attr="category_ref",
            graphql_name="categoryRefId",
            target_name="category_ref",
            kind=RELATION_SINGLE,
        ),
    ]
    names = {"category": ("category", "category_id"), "category_ref": ("category_id", "category")}

    key_map = build_error_key_map(specs, keys_of=lambda spec: names[spec.target_name])

    assert key_map == {"category": ("categoryId", None), "category_id": ("categoryRefId", None)}


@pytest.mark.parametrize(
    ("model", "name", "expected"),
    [
        pytest.param(
            product_models.Item,
            "category",
            ("category", "category_id"),
            id="forward-fk",
        ),
        pytest.param(product_models.Item, "is_private", ("is_private",), id="scalar"),
        pytest.param(library_models.Shelf, "alt_branches", ("alt_branches",), id="m2m"),
        pytest.param(product_models.Category, "items", ("items",), id="reverse-relation"),
    ],
)
def test_model_field_error_names_add_a_forward_relation_attname(
    model: type[Model],
    name: str,
    expected: tuple[str, ...],
) -> None:
    """A forward relation answers to its ``attname`` too; every other field to its name alone."""
    assert model_field_error_names(model._meta.get_field(name)) == expected


def test_save_time_error_key_map_reads_the_backing_model_one_level() -> None:
    """The save-time map keys the backing model's names and gives a nested field no child map.

    A Django ``ValidationError`` names no nested item, so the map is read against
    ``Category`` alone: ``title`` (``source="name"``) owns ``name``, and the nested
    ``items`` level, which writes ``Item``, is not descended into.
    """
    child = (
        InputFieldSpec(
            input_attr="category_id",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
    )
    specs = [
        InputFieldSpec(
            input_attr="title",
            graphql_name="title",
            target_name="title",
            kind=SCALAR,
            source="name",
        ),
        InputFieldSpec(
            input_attr="items",
            graphql_name="items",
            target_name="items",
            # The map reads only ``nested_specs``; the serializer's nested kinds live
            # behind the DRF soft dependency, so a plain kind stands in.
            kind=SCALAR,
            nested_specs=child,
        ),
    ]

    assert save_time_error_key_map(specs, product_models.Category) == {
        "name": ("title", None),
        "items": ("items", None),
    }


@pytest.mark.parametrize(
    (
        "model",
        "target_name",
        "source",
        "expected",
    ),
    [
        pytest.param(
            product_models.Item,
            "key",
            "pk",
            {"pk": ("key", None), "id": ("key", None)},
            id="source-pk-integer-key",
        ),
        pytest.param(
            product_models.Item,
            "pk",
            None,
            {"pk": ("pk", None), "id": ("pk", None)},
            id="declared-pk",
        ),
        pytest.param(
            library_models.Edition,
            "key",
            "pk",
            {"pk": ("key", None), "isbn_13": ("key", None)},
            id="source-pk-text-key",
        ),
        pytest.param(
            library_models.LendingDesk,
            "ptr",
            "pk",
            {"pk": ("ptr", None), "venue_ptr": ("ptr", None), "venue_ptr_id": ("ptr", None)},
            id="source-pk-parent-link",
        ),
    ],
)
def test_save_time_error_key_map_reads_the_pk_alias_as_the_primary_key(
    model: type[Model],
    target_name: str,
    source: str | None,
    expected: dict[str, tuple[str, None]],
) -> None:
    """A spec writing Django's ``pk`` alias owns every name the primary key answers to.

    ``pk`` is no ``Options.get_field`` name, yet it writes ``_meta.pk``: the integer
    ``id``, ``Edition``'s ISBN text ``isbn_13``, or under multi-table inheritance
    ``LendingDesk``'s parent link ``venue_ptr`` and its ``attname``. A Django save-time
    error names the key by that model field, so it re-keys to the spec's input, whether
    the field is renamed onto ``pk`` (``source="pk"``) or declared as ``pk``.
    """
    spec = InputFieldSpec(
        input_attr=target_name,
        graphql_name=target_name,
        target_name=target_name,
        kind=SCALAR,
        source=source,
    )

    assert save_time_error_key_map([spec], model) == expected


_UTC = datetime.timezone.utc
_IN_RANGE = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=_UTC)
_BEFORE_YEAR_ONE = datetime.datetime(
    1,
    1,
    1,
    tzinfo=datetime.timezone(datetime.timedelta(hours=1)),
)
_PAST_YEAR_9999 = datetime.datetime(
    9999,
    12,
    31,
    23,
    tzinfo=datetime.timezone(datetime.timedelta(hours=-1)),
)
_AWARE_TIME = datetime.time(9, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
#: UTC offsets PostgreSQL refuses under client-side binding: 16:00, and a fraction of a second.
_OFFSET_16 = datetime.timezone(datetime.timedelta(hours=16))
_OFFSET_HALF_SECOND = datetime.timezone(datetime.timedelta(hours=1, microseconds=500_000))


#: Unbound columns, typed as the ``object``-valued fields ``unstorable_temporal`` reads.
_TEXT: models.Field[object, object] = models.TextField()
_DATE: models.Field[object, object] = models.DateField()
_STAMP: models.Field[object, object] = models.DateTimeField()
_TIME: models.Field[object, object] = models.TimeField()
_INTEGERS: models.Field[object, object] = FakeArrayField(models.IntegerField())
_NESTED_STAMPS: models.Field[object, object] = FakeArrayField(
    FakeArrayField(models.DateTimeField()),
)
_STAMPS: models.Field[object, object] = FakeArrayField(models.DateTimeField())
_TIMES: models.Field[object, object] = FakeArrayField(models.TimeField())


class _StoringOperations(BaseDatabaseOperations):
    """Operations whose adapters pass aware datetimes and times through, as PostgreSQL's do."""

    @override
    def adapt_datetimefield_value(self, value: datetime.datetime | None) -> str | None:
        return None if value is None else value.isoformat()

    @override
    def adapt_timefield_value(self, value: datetime.datetime | datetime.time | None) -> str | None:
        return None if value is None else value.isoformat()


@contextmanager
def _stand_in_alias(
    operations: type[BaseDatabaseOperations],
    *,
    supports_timezones: bool,
) -> Generator[str, None, None]:
    """Register a ``default``-shaped alias with ``operations`` and the time-zone feature given."""
    alias = "temporal_write_stand_in"
    wrapper = connections.create_connection(DEFAULT_DB_ALIAS)
    wrapper.ops = operations(wrapper)
    wrapper.features.supports_timezones = supports_timezones
    connections[alias] = wrapper
    try:
        yield alias
    finally:
        del connections[alias]


def _unresolvable_alias() -> str:
    raise AssertionError("a non-temporal column must not resolve the alias")


@pytest.mark.parametrize(
    ("column", "value"),
    [
        pytest.param(_TEXT, "text", id="text"),
        pytest.param(_DATE, datetime.date(1, 1, 1), id="date"),
        pytest.param(_INTEGERS, [1, 2], id="array-of-integers"),
    ],
)
def test_unstorable_temporal_leaves_a_non_temporal_column_without_resolving_the_alias(
    column: models.Field[object, object],
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A column that stores no datetime or time answers ``False`` before ``using`` is called."""
    monkeypatch.setattr(errors_module, "_ARRAY_FIELD_CLS", FakeArrayField)

    assert unstorable_temporal(column, value, _unresolvable_alias) is False


@pytest.mark.parametrize(
    (
        "settings",
        "column",
        "value",
        "refused",
    ),
    [
        pytest.param({}, _STAMP, _BEFORE_YEAR_ONE, True, id="before-year-one"),
        pytest.param({}, _STAMP, _PAST_YEAR_9999, True, id="past-year-9999"),
        pytest.param({}, _STAMP, _IN_RANGE, False, id="in-range"),
        pytest.param(
            {},
            _STAMP,
            datetime.datetime(1, 1, 1),  # noqa: DTZ001 - the naive value under test
            False,
            id="naive",
        ),
        pytest.param({}, _TIME, _AWARE_TIME, False, id="aware-time"),
        pytest.param(
            {"USE_TZ": False, "TIME_ZONE": "Asia/Tokyo"},
            _STAMP,
            _BEFORE_YEAR_ONE,
            False,
            id="session-wall-clock-in-range",
        ),
        pytest.param(
            {"USE_TZ": False, "TIME_ZONE": "Asia/Tokyo"},
            _STAMP,
            datetime.datetime(1, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9.5))),
            True,
            id="session-wall-clock-before-year-one",
        ),
        pytest.param(
            {},
            _NESTED_STAMPS,
            [[_IN_RANGE, None], [_BEFORE_YEAR_ONE]],
            True,
            id="array-element",
        ),
    ],
)
def test_unstorable_temporal_holds_a_stored_instant_to_its_session_wall_clock(
    settings: dict[str, object],
    column: models.Field[object, object],
    value: object,
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On a backend storing aware datetimes, the session wall clock must stay in years 1..9999.

    The stand-in's adapters pass every datetime and time through, as PostgreSQL's do, and
    it stores the instant itself (``supports_timezones``): the driver then loads it back
    on the session time zone (``UTC`` under ``USE_TZ``, else ``TIME_ZONE``, whose year-1
    offset in ``Asia/Tokyo`` is its local mean time, +09:18:59), so only a wall clock
    there leaving years 1..9999 is refused. A naive datetime and an aware time store.
    Every element of an ``ArrayField`` is held to the rule, at any depth.
    """
    monkeypatch.setattr(errors_module, "_ARRAY_FIELD_CLS", FakeArrayField)
    with (
        override_settings(**settings),
        _stand_in_alias(_StoringOperations, supports_timezones=True) as alias,
    ):
        assert unstorable_temporal(column, value, lambda: alias) is refused


@pytest.mark.parametrize(
    (
        "operations",
        "column",
        "value",
        "refused",
    ),
    [
        pytest.param(
            MySQLOperations,
            _TIME,
            _AWARE_TIME,
            True,
            id="mysql-aware-time",
        ),
        pytest.param(
            MySQLOperations,
            _STAMP,
            _PAST_YEAR_9999,
            True,
            id="mysql-past-year-9999",
        ),
        pytest.param(
            MySQLOperations,
            _STAMP,
            _IN_RANGE,
            False,
            id="mysql-in-range",
        ),
        pytest.param(
            _StoringOperations,
            _STAMP,
            _BEFORE_YEAR_ONE,
            False,
            id="adapter-binding-without-time-zone-support",
        ),
    ],
)
def test_unstorable_temporal_asks_the_write_alias_own_operations(
    operations: type[BaseDatabaseOperations],
    column: models.Field[object, object],
    value: object,
    refused: bool,  # noqa: FBT001
) -> None:
    """A backend that does not store aware instants is held to its own adapter alone.

    MySQL's operations refuse an aware time and a datetime whose projection onto the
    connection's time zone leaves years 1..9999; a backend whose adapter binds the value
    and stores no aware instant (no session projection on load) stores it.
    """
    with _stand_in_alias(operations, supports_timezones=False) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is refused


@pytest.mark.parametrize(
    ("column", "value", "refused"),
    [
        pytest.param(_NESTED_STAMPS, None, False, id="null"),
        pytest.param(_NESTED_STAMPS, [[_IN_RANGE, None]], False, id="in-range"),
        pytest.param(
            _NESTED_STAMPS,
            [[_IN_RANGE], [_PAST_YEAR_9999]],
            True,
            id="nested-element-past-year-9999",
        ),
        pytest.param(_STAMPS, [_BEFORE_YEAR_ONE], True, id="element-before-year-one"),
        pytest.param(_TIMES, [datetime.time(9, 30), _AWARE_TIME], True, id="aware-time-element"),
        pytest.param(_TIMES, [datetime.time(9, 30)], False, id="naive-time-elements"),
    ],
)
def test_unstorable_temporal_holds_each_array_element_on_the_adapter(
    column: models.Field[object, object],
    value: object,
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every element of an ``ArrayField`` of datetimes or times, at any depth, meets the adapter.

    Held to MySQL's operations, which refuse an aware time and a datetime whose projection
    leaves years 1..9999, so the rows answer the same on every test tier.
    """
    monkeypatch.setattr(errors_module, "_ARRAY_FIELD_CLS", FakeArrayField)
    with _stand_in_alias(MySQLOperations, supports_timezones=False) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is refused


def _real_array_of(base_field: models.Field[object, object]) -> models.Field[object, object]:
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415 - after the skip guard

    return ArrayField(base_field)


@pytest.mark.pg
@pytest.mark.parametrize(
    (
        "settings",
        "column",
        "value",
        "refused",
    ),
    [
        pytest.param(
            {},
            models.DateTimeField,
            _BEFORE_YEAR_ONE,
            True,
            id="utc-before-year-one",
        ),
        pytest.param({}, models.TimeField, _AWARE_TIME, False, id="aware-time"),
        pytest.param(
            {"USE_TZ": False, "TIME_ZONE": "Asia/Tokyo"},
            models.DateTimeField,
            _BEFORE_YEAR_ONE,
            False,
            id="tokyo-wall-clock-in-range",
        ),
        pytest.param(
            {},
            lambda: _real_array_of(models.DateTimeField()),
            [_IN_RANGE, _PAST_YEAR_9999],
            True,
            id="array-element",
        ),
        pytest.param(
            {},
            lambda: _real_array_of(models.DateTimeField()),
            [_IN_RANGE, None],
            False,
            id="array-in-range",
        ),
        pytest.param(
            {},
            lambda: _real_array_of(models.TimeField()),
            [datetime.time(9, 30, tzinfo=_OFFSET_16), None],
            True,
            id="array-time-offset-16-00",
        ),
        pytest.param(
            {},
            lambda: _real_array_of(models.DateTimeField()),
            [datetime.datetime(2021, 6, 15, tzinfo=_OFFSET_HALF_SECOND)],
            True,
            id="array-datetime-offset-half-second",
        ),
    ],
)
def test_unstorable_temporal_on_postgresql(
    settings: dict[str, object],
    column: Callable[[], models.Field[object, object]],
    value: object,
    refused: bool,  # noqa: FBT001
) -> None:
    """The real PostgreSQL connection stores the instant and is held to its session wall clock.

    An ``ArrayField`` element is held to the UTC offset rule of the suite's client-side
    binding too: 16:00 or more, or a fraction of a second, is refused.
    """
    with override_settings(**settings):
        assert unstorable_temporal(column(), value, lambda: DEFAULT_DB_ALIAS) is refused


def _offset(
    hours: int,
    minutes: int = 0,
    seconds: int = 0,
    microseconds: int = 0,
) -> datetime.timezone:
    """A fixed UTC offset; a negative ``hours`` flips the whole offset."""
    sign = -1 if hours < 0 else 1
    return datetime.timezone(
        sign
        * datetime.timedelta(
            hours=abs(hours),
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        ),
    )


#: Each offset PostgreSQL is asked about, and whether it refuses it under client-side
#: binding (as text) and under psycopg 3's server-side binding for a ``time`` (a
#: ``datetime`` bound server-side travels as a UTC instant, which no offset refuses).
_POSTGRESQL_OFFSETS = {
    "15-59-59": (_offset(15, 59, 59), False, False),
    "minus-15-59": (_offset(-15, 59), False, False),
    "16-00": (_offset(16), True, True),
    "minus-16-00": (_offset(-16), True, True),
    "23-59": (_offset(23, 59), True, True),
    "whole-seconds": (_offset(1, 0, 30), False, False),
    "half-second": (_offset(1, 0, 0, 500_000), True, False),
    "minus-15-59-59-999999": (_offset(-15, 59, 59, 999_999), True, False),
    "naive": (None, False, False),
}

#: Each temporal leaf the offset reaches: its column, lookup parts and whether its value is a
#: ``time`` (a ``TimeField``, or a ``DateTimeField``'s ``time`` transform) or a ``datetime``.
_OFFSET_LEAVES = {
    "datetime": (_STAMP, ("gt",), False),
    "time": (_TIME, ("in",), True),
    "time-transform": (_STAMP, ("time", "exact"), True),
}


def _leaf_value(
    zone: datetime.tzinfo | None,
    *,
    is_time: bool,
) -> datetime.datetime | datetime.time:
    if is_time:
        return datetime.time(12, tzinfo=zone)
    return datetime.datetime(2021, 6, 15, 12, tzinfo=zone)


class _ClientCursor:
    """psycopg 3's ``ClientCursor``: it binds every parameter into the query text."""


class _DjangoClientCursor(_ClientCursor):
    """Django's default psycopg 3 cursor class, a ``ClientCursor``."""


class _ServerBindingCursor:
    """psycopg 3's ``Cursor``, which binds parameters on the server."""


def _driver(**exports: type[object]) -> ModuleType:
    """A database driver module exporting ``exports``."""
    module = ModuleType("driver_stand_in")
    vars(module).update(exports)
    return module


#: Each binding mode a PostgreSQL connection can run in: its driver module and the
#: ``cursor_factory`` Django connects with (psycopg 2 exports no ``ClientCursor``; a
#: psycopg 3 ``cursor_factory`` of ``None`` is psycopg's own server-binding ``Cursor``).
_BINDING_MODES = {
    "psycopg2": (_driver(), _DjangoClientCursor, True),
    "psycopg3-client": (_driver(ClientCursor=_ClientCursor), _DjangoClientCursor, True),
    "psycopg3-server": (_driver(ClientCursor=_ClientCursor), _ServerBindingCursor, False),
    "psycopg3-default-cursor": (_driver(ClientCursor=_ClientCursor), None, False),
}


@contextmanager
def _postgresql_stand_in(
    driver: ModuleType,
    cursor_factory: type[object] | None,
) -> Generator[str, None, None]:
    """Register an alias that reads as PostgreSQL, on ``driver`` and ``cursor_factory``.

    Its adapters pass every datetime and time through, as Django's PostgreSQL adapters do,
    and it is never opened: the binding mode is read from its connection parameters.
    """
    alias = "postgresql_stand_in"
    wrapper = SQLiteDatabaseWrapper(
        {"NAME": "stand-in", "OPTIONS": {"cursor_factory": cursor_factory}},
        alias,
    )
    wrapper.vendor = "postgresql"
    wrapper.Database = driver
    connections[alias] = wrapper
    stand_in = connections[alias]
    stand_in.ops = _StoringOperations(stand_in)
    try:
        yield alias
    finally:
        del connections[alias]


@pytest.mark.parametrize("mode", list(_BINDING_MODES))
@pytest.mark.parametrize("leaf", list(_OFFSET_LEAVES))
@pytest.mark.parametrize("offset", list(_POSTGRESQL_OFFSETS))
def test_unbindable_temporal_holds_a_utc_offset_to_postgresql_binding_mode(
    mode: str,
    leaf: str,
    offset: str,
) -> None:
    """A PostgreSQL connection refuses exactly the UTC offsets its binding mode sends it.

    Bound as text (psycopg 2, psycopg 3's ``ClientCursor``) an aware datetime or time is
    refused for an offset of 16:00 or more either way, or one with a fraction of a
    second; bound on the server (any other psycopg 3 cursor) a datetime travels as a UTC
    instant, so no offset refuses it, while a time keeps its whole-second offset, refused
    from 16:00. Every member of an ``in`` list is read. A stand-in alias carries each
    mode, so the rule holds on every test tier; the real server's answers are pinned by
    ``test_unbindable_temporal_answers_what_postgresql_refuses``.
    """
    driver, cursor_factory, client_side = _BINDING_MODES[mode]
    column, lookup_parts, is_time = _OFFSET_LEAVES[leaf]
    zone, refused_as_text, refused_time_on_server = _POSTGRESQL_OFFSETS[offset]
    value = _leaf_value(zone, is_time=is_time)
    bound = [datetime.time(9, 30), value] if lookup_parts == ("in",) else value
    refused = refused_as_text if client_side else is_time and refused_time_on_server
    with _postgresql_stand_in(driver, cursor_factory) as alias:
        assert unbindable_temporal(column, lookup_parts, bound, lambda: alias) is refused


@pytest.mark.parametrize(
    ("column", "value"),
    [
        pytest.param(_STAMP, _leaf_value(_offset(16), is_time=False), id="datetime-16-00"),
        pytest.param(
            _TIME,
            _leaf_value(_offset(1, 0, 0, 500_000), is_time=True),
            id="time-half-second",
        ),
    ],
)
def test_unstorable_temporal_refuses_a_utc_offset_postgresql_refuses(
    column: models.Field[object, object],
    value: object,
) -> None:
    """A write value whose UTC offset PostgreSQL refuses is unstorable, through the same rule."""
    driver, cursor_factory, _ = _BINDING_MODES["psycopg3-client"]
    with _postgresql_stand_in(driver, cursor_factory) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is True


@contextmanager
def _postgresql_alias(*, server_side_binding: bool) -> Generator[str, None, None]:
    """A second alias on the test database, connecting with ``server_side_binding``."""
    alias = "binding_mode"
    wrapper = connections.create_connection(DEFAULT_DB_ALIAS)
    settings_dict = connections[DEFAULT_DB_ALIAS].settings_dict
    wrapper.settings_dict = {
        **settings_dict,
        "OPTIONS": {**settings_dict["OPTIONS"], "server_side_binding": server_side_binding},
    }
    connections[alias] = wrapper
    try:
        yield alias
    finally:
        wrapper.close()
        del connections[alias]


def _postgresql_refuses(alias: str, column: str, value: object) -> bool:
    """Whether the server refuses ``value`` filtering on ``column`` and written into it."""
    bound = {f"{column}__in": [value]} if column == "occurred_time" else {column: value}
    try:
        _ = list(scalar_models.ScalarSpecimen.objects.using(alias).filter(**bound))
    except DataError:
        filter_refused = True
    else:
        filter_refused = False
    write_refused = False
    if column != "occurred_at__time":
        row = {
            "label": "offset",
            "occurred_on": datetime.date(2021, 6, 15),
            "occurred_at": _IN_RANGE,
            "occurred_time": datetime.time(9, 30),
            "external_id": uuid.uuid4(),
            column: value,
        }
        try:
            with transaction.atomic(using=alias):
                _ = scalar_models.ScalarSpecimen.objects.using(alias).create(**row)
                transaction.set_rollback(True, using=alias)
        except DataError:
            write_refused = True
        assert write_refused is filter_refused
    return filter_refused


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize("server_side_binding", [False, True], ids=["client-side", "server-side"])
@pytest.mark.parametrize("leaf", list(_OFFSET_LEAVES))
@pytest.mark.parametrize("offset", list(_POSTGRESQL_OFFSETS))
def test_unbindable_temporal_answers_what_postgresql_refuses(
    server_side_binding: bool,  # noqa: FBT001
    leaf: str,
    offset: str,
) -> None:
    """The rule refuses exactly the offsets the real server refuses, in each binding mode.

    Each value is filtered on (``exact``, ``in``, a datetime's ``time`` transform) and
    written over a second alias on the test database, connecting with psycopg 3's
    ``server_side_binding`` off and on; ``unbindable_temporal`` and ``unstorable_temporal``
    answer what the server does.
    """
    column, lookup_parts, is_time = _OFFSET_LEAVES[leaf]
    zone, _, _ = _POSTGRESQL_OFFSETS[offset]
    value = _leaf_value(zone, is_time=is_time)
    target = {"datetime": "occurred_at", "time": "occurred_time"}.get(leaf, "occurred_at__time")
    with _postgresql_alias(server_side_binding=server_side_binding) as alias:
        with warnings.catch_warnings():
            # A naive datetime under ``USE_TZ`` is made aware in the current time zone.
            warnings.filterwarnings("ignore", "DateTimeField .* received a naive", RuntimeWarning)
            refused = _postgresql_refuses(alias, target, value)
        assert unbindable_temporal(column, lookup_parts, [value], lambda: alias) is refused
        if leaf != "time-transform":
            assert unstorable_temporal(column, value, lambda: alias) is refused


@pytest.mark.parametrize(
    ("column", "value", "refused"),
    [
        pytest.param(
            _STAMPS,
            [_leaf_value(_offset(16), is_time=False)],
            True,
            id="datetime-element",
        ),
        pytest.param(
            _TIMES,
            [_leaf_value(_offset(1, 0, 0, 500_000), is_time=True)],
            True,
            id="time-element-half-second",
        ),
        pytest.param(_STAMP, _leaf_value(_offset(16), is_time=False), False, id="scalar-datetime"),
    ],
)
def test_unstorable_temporal_holds_array_elements_to_the_text_rule_on_server_side_binding(
    column: models.Field[object, object],
    value: object,
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Under server-side binding an ``ArrayField`` element is still held to the text rule.

    psycopg binds a list parameter's elements as text whatever the cursor, so a datetime
    element at +16:00 and a time element whose offset carries a fraction of a second are
    refused, while the same datetime written to a plain column travels as a UTC instant
    and stores.
    """
    monkeypatch.setattr(errors_module, "_ARRAY_FIELD_CLS", FakeArrayField)
    driver, cursor_factory, _ = _BINDING_MODES["psycopg3-server"]
    with _postgresql_stand_in(driver, cursor_factory) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is refused


def _postgresql_refuses_array(
    alias: str,
    column: models.Field[object, object],
    value: object,
) -> bool:
    """Whether the server refuses ``value`` written into a temporary column of ``column``'s type."""
    connection = connections[alias]
    with transaction.atomic(using=alias), connection.cursor() as cursor:
        cursor.execute(f"CREATE TEMP TABLE offset_probe (cell {column.db_type(connection)})")
        try:
            with transaction.atomic(using=alias):
                cursor.execute(
                    "INSERT INTO offset_probe (cell) VALUES (%s)",
                    [column.get_db_prep_save(value, connection)],
                )
        except DataError:
            refused = True
        else:
            refused = False
        transaction.set_rollback(True, using=alias)
    return refused


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("column", "value", "refused"),
    [
        pytest.param(
            lambda: _real_array_of(models.DateTimeField()),
            [_leaf_value(_offset(16), is_time=False)],
            True,
            id="datetime-element",
        ),
        pytest.param(
            lambda: _real_array_of(models.TimeField()),
            [_leaf_value(_offset(1, 0, 0, 500_000), is_time=True)],
            True,
            id="time-element-half-second",
        ),
        pytest.param(
            models.DateTimeField,
            _leaf_value(_offset(16), is_time=False),
            False,
            id="scalar-datetime",
        ),
    ],
)
def test_unstorable_temporal_answers_postgresql_for_array_elements_on_server_side_binding(
    column: Callable[[], models.Field[object, object]],
    value: object,
    refused: bool,  # noqa: FBT001
) -> None:
    """On the real server with ``server_side_binding`` the array elements are refused as text.

    The value is written into a temporary column of the field's type over a second alias
    connecting with psycopg 3's ``server_side_binding``, the way the ORM binds it
    (``get_db_prep_save``); the server's answer and ``unstorable_temporal``'s agree.
    """
    field = column()
    with _postgresql_alias(server_side_binding=True) as alias:
        assert _postgresql_refuses_array(alias, field, value) is refused
        assert unstorable_temporal(field, value, lambda: alias) is refused
