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
operations, a date a ``DateTimeField`` column holds (no fakeshop write flavor hands one
over), and, on the Postgres tier, the real connection and ``ArrayField``.
"""

import ast
import datetime
import functools
import importlib
import uuid
import warnings
from collections.abc import Callable, Generator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalar_models
from django.core.exceptions import ValidationError
from django.db import DEFAULT_DB_ALIAS, DataError, connections, models, transaction
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.mysql.operations import DatabaseOperations as MySQLOperations
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.models import Model
from django.test import override_settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing_extensions import override

from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
from django_strawberry_framework.utils import errors as errors_module
from django_strawberry_framework.utils._narrowing import (
    call_method,
    is_list_or_tuple,
    is_tuple,
    require,
)
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
    binds_integer,
    build_error_key_map,
    coded_error_extensions,
    empty_validation_error,
    field_error,
    join_error_path,
    model_field_error_names,
    null_field_error,
    refuses_integer_range,
    refuses_numeric_format,
    refuses_utc_offset,
    rekey_error_segment,
    relation_field_error,
    save_time_error_key_map,
    unbindable_temporal,
    unstorable_temporal,
    validation_error_to_field_errors,
)
from django_strawberry_framework.utils.inputs import RELATION_SINGLE, SCALAR, InputFieldSpec
from tests._postgres_fields import FakeArrayField, patch_array_field, real_array_of
from tests._postgresql_stand_in import (
    BINDING_MODES,
    ClientCursor,
    DjangoClientCursor,
    StoringOperations,
    driver_module,
    postgresql_stand_in,
)

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


def test_validation_error_leaves_must_be_validation_errors() -> None:
    """Django stores every leaf as a ``ValidationError``; a planted leaf or map is a ``TypeError``."""
    planted_leaf = ValidationError("value")
    # Message-shaped, so ``messages`` renders it; it is still not a ``ValidationError``.
    vars(planted_leaf)["error_list"] = [SimpleNamespace(message="value", params=None, code="x")]
    with pytest.raises(TypeError, match="expected an instance of"):
        validation_error_to_field_errors(planted_leaf)
    planted_map = ValidationError({"name": ["required"]})
    vars(planted_map)["error_dict"] = [("name", [])]
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        validation_error_to_field_errors(planted_map)


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
# The error-code vocabulary: public wire contract
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
    default: models.TextField[str, str] = models.TextField()
    null_leaf = null_field_error("categoryId", default)
    assert null_leaf.field == "categoryId"
    assert null_leaf.messages == ["This field cannot be null."]
    assert null_leaf.codes == [FIELD_ERROR_CODE_NULL]
    assert null_leaf.path == ["categoryId"]
    custom: models.TextField[str, str] = models.TextField(
        error_messages={"null": "A hold needs an item."},
    )
    assert null_field_error("itemId", custom).messages == ["A hold needs an item."]

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
#: A naive year-1 midnight, the value Django makes aware in the default time zone.
_NAIVE_YEAR_ONE = datetime.datetime(1, 1, 1)  # noqa: DTZ001 - the naive value under test
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
    patch_array_field(monkeypatch)

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
            {"TIME_ZONE": "Asia/Tokyo"},
            _STAMP,
            datetime.date(1, 1, 1),
            True,
            id="date-session-wall-clock-before-year-one",
        ),
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
        pytest.param(
            {},
            _NESTED_STAMPS,
            [_BEFORE_YEAR_ONE, [_IN_RANGE]],
            False,
            id="array-non-list-item-dropped",
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
    there leaving years 1..9999 is refused. A naive datetime is first made aware in the
    default time zone (``UTC`` by default, so year 1 stores) and a date first becomes
    that midnight (in ``Asia/Tokyo`` year 1's falls in year 0); an aware time stores.
    Every element of an ``ArrayField`` is held to the rule, at any depth; an item that is
    no list where a nested array's level expects one holds no element and is dropped, so
    it is never held to the rule.
    """
    patch_array_field(monkeypatch)
    with (
        override_settings(**settings),
        _stand_in_alias(StoringOperations, supports_timezones=True) as alias,
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
            StoringOperations,
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
    patch_array_field(monkeypatch)
    with _stand_in_alias(MySQLOperations, supports_timezones=False) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is refused


@contextmanager
def _sqlite_alias(database_time_zone: str | None) -> Generator[str, None, None]:
    """Register a never-opened SQLite alias whose ``DATABASES`` ``TIME_ZONE`` is given."""
    alias = "sqlite_time_zone_stand_in"
    connections[alias] = SQLiteDatabaseWrapper(
        {"NAME": "stand-in", "TIME_ZONE": database_time_zone},
        alias,
    )
    try:
        yield alias
    finally:
        del connections[alias]


@pytest.mark.parametrize(
    (
        "settings",
        "database_time_zone",
        "column",
        "value",
        "refused",
    ),
    [
        pytest.param(
            {"TIME_ZONE": "Asia/Tokyo"},
            None,
            _STAMP,
            datetime.date(1, 1, 1),
            True,
            id="tokyo-year-one",
        ),
        pytest.param(
            {"TIME_ZONE": "Etc/GMT+12"},
            "Etc/GMT-14",
            _STAMP,
            datetime.date(9999, 12, 31),
            True,
            id="database-time-zone-year-9999",
        ),
        pytest.param(
            {"TIME_ZONE": "Etc/GMT+12"},
            "Etc/GMT-14",
            _STAMP,
            datetime.date(2021, 6, 15),
            False,
            id="database-time-zone-in-range",
        ),
        pytest.param({"TIME_ZONE": "UTC"}, None, _STAMP, datetime.date(1, 1, 1), False, id="utc"),
        pytest.param(
            {"TIME_ZONE": "America/Chicago"},
            None,
            _STAMP,
            datetime.date(1, 1, 1),
            False,
            id="chicago-year-one",
        ),
        pytest.param(
            {"USE_TZ": False, "TIME_ZONE": "Asia/Tokyo"},
            None,
            _STAMP,
            datetime.date(1, 1, 1),
            False,
            id="naive-midnight-without-use-tz",
        ),
        pytest.param(
            {"TIME_ZONE": "Asia/Tokyo"},
            None,
            _DATE,
            datetime.date(1, 1, 1),
            False,
            id="date-column",
        ),
        pytest.param(
            {"TIME_ZONE": "Asia/Tokyo"},
            None,
            _STAMP,
            _NAIVE_YEAR_ONE,
            True,
            id="naive-datetime-tokyo-year-one",
        ),
        pytest.param(
            {"TIME_ZONE": "UTC"},
            None,
            _STAMP,
            _NAIVE_YEAR_ONE,
            False,
            id="naive-datetime-utc",
        ),
        pytest.param(
            {"USE_TZ": False, "TIME_ZONE": "Asia/Tokyo"},
            None,
            _STAMP,
            _NAIVE_YEAR_ONE,
            False,
            id="naive-datetime-without-use-tz",
        ),
        pytest.param(
            {"TIME_ZONE": "Asia/Tokyo"},
            None,
            _NESTED_STAMPS,
            [[datetime.date(2021, 6, 15), None], [datetime.date(1, 1, 1)]],
            True,
            id="array-element-tokyo-year-one",
        ),
        pytest.param(
            {"TIME_ZONE": "UTC"},
            None,
            _NESTED_STAMPS,
            [[datetime.date(1, 1, 1), None], [datetime.date(9999, 12, 31)]],
            False,
            id="array-elements-utc",
        ),
    ],
)
def test_unstorable_temporal_holds_a_date_or_naive_datetime_to_the_datetime_django_binds(
    settings: dict[str, object],
    database_time_zone: str | None,
    column: models.Field[object, object],
    value: object,
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A date or naive datetime a ``DateTimeField`` column holds is checked as Django binds it.

    Django binds a date as its midnight and, under ``USE_TZ``, a naive datetime (that
    midnight included) made aware in the default time zone, which SQLite projects onto
    the connection's time zone (``UTC``, or the alias's ``DATABASES`` ``TIME_ZONE``).
    Year 1's midnight in ``Asia/Tokyo`` (local mean time, +09:18:59) falls in year 0;
    year 9999's last midnight at UTC-12 reaches year 10000 at UTC+14. Without ``USE_TZ``
    the naive value binds; a ``DateField`` column stores the date itself. Every
    ``ArrayField`` element is projected the same way, at any depth.
    """
    patch_array_field(monkeypatch)
    with override_settings(**settings), _sqlite_alias(database_time_zone) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is refused


#: An aware year-9999 instant whose wall clock stays in year 9999 in UTC and reaches
#: year 10000 in ``Asia/Tokyo`` (+09:18:59).
_YEAR_9999_EVENING_UTC = datetime.datetime(9999, 12, 31, 20, tzinfo=_UTC)


@pytest.mark.parametrize(
    ("settings", "value", "refused"),
    [
        pytest.param({"TIME_ZONE": "UTC"}, _BEFORE_YEAR_ONE, True, id="utc-year-one"),
        pytest.param({"TIME_ZONE": "UTC"}, _PAST_YEAR_9999, True, id="utc-year-9999"),
        pytest.param(
            {"TIME_ZONE": "UTC"},
            _YEAR_9999_EVENING_UTC,
            False,
            id="utc-year-9999-evening",
        ),
        pytest.param({"TIME_ZONE": "UTC"}, _IN_RANGE, False, id="utc-in-range"),
        pytest.param({"TIME_ZONE": "Asia/Tokyo"}, _BEFORE_YEAR_ONE, True, id="tokyo-year-one"),
        pytest.param({"TIME_ZONE": "Asia/Tokyo"}, _PAST_YEAR_9999, True, id="tokyo-year-9999"),
        pytest.param(
            {"TIME_ZONE": "Asia/Tokyo"},
            _YEAR_9999_EVENING_UTC,
            True,
            id="tokyo-year-9999-evening",
        ),
        pytest.param({"TIME_ZONE": "Asia/Tokyo"}, _IN_RANGE, False, id="tokyo-in-range"),
        pytest.param({"USE_TZ": False}, _BEFORE_YEAR_ONE, False, id="year-one-without-use-tz"),
    ],
)
def test_unstorable_temporal_holds_a_datetime_in_a_date_column_to_its_default_zone_date(
    settings: dict[str, object],
    value: datetime.datetime,
    refused: bool,  # noqa: FBT001
) -> None:
    """An aware datetime a ``DateField`` column holds is refused when Django cannot cast it.

    ``DateField.to_python`` makes an aware datetime naive in the default time zone
    (``TIME_ZONE``) under ``USE_TZ`` before taking its date, which raises
    ``OverflowError`` when that wall clock, or the UTC instant it is read through, leaves
    years 1..9999, on every backend. 9999-12-31 20:00 UTC stays in year 9999 in UTC and
    reaches year 10000 in ``Asia/Tokyo``; without ``USE_TZ`` the value's own date is
    stored.
    """
    with override_settings(**settings), _sqlite_alias(None) as alias:
        assert unstorable_temporal(_DATE, value, lambda: alias) is refused


#: A duration column, typed as the ``object``-valued field ``unstorable_temporal`` reads.
_DURATION: models.Field[object, object] = models.DurationField()
#: The longest whole-day duration whose microsecond count fits 64 bits.
_LONGEST_DAYS_IN_64_BITS = 106_751_991


@pytest.mark.parametrize(
    ("value", "refused_without_interval"),
    [
        pytest.param(datetime.timedelta(days=_LONGEST_DAYS_IN_64_BITS), False, id="fits"),
        pytest.param(
            datetime.timedelta(days=-_LONGEST_DAYS_IN_64_BITS),
            False,
            id="fits-negative",
        ),
        pytest.param(
            datetime.timedelta(days=_LONGEST_DAYS_IN_64_BITS + 1),
            True,
            id="past-64-bits",
        ),
        pytest.param(
            datetime.timedelta(days=-_LONGEST_DAYS_IN_64_BITS - 1),
            True,
            id="past-64-bits-negative",
        ),
        pytest.param(datetime.timedelta.max, True, id="timedelta-max"),
        pytest.param(datetime.timedelta.min, True, id="timedelta-min"),
    ],
)
def test_unstorable_temporal_holds_a_duration_to_the_integer_the_backend_binds(
    value: datetime.timedelta,
    refused_without_interval: bool,  # noqa: FBT001
) -> None:
    """A duration is refused where its microsecond count leaves the backend's 64 bits.

    Without a native interval (SQLite, MySQL) Django binds a duration as its microsecond
    count, which the driver refuses past ``BigIntegerField``'s range (2**63 microseconds
    is 106751991 days 04:00:54.775808); a backend with a native interval (PostgreSQL,
    stood in here) binds the ``timedelta`` itself, so every duration stores.
    """
    assert unstorable_temporal(_DURATION, value, lambda: DEFAULT_DB_ALIAS) is (
        refused_without_interval
    )
    driver, cursor_factory, _ = BINDING_MODES["psycopg3-client"]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert unstorable_temporal(_DURATION, value, lambda: alias) is False


@pytest.mark.parametrize(
    ("column", "value"),
    [
        pytest.param(_DATE, datetime.date(1, 1, 1), id="date-in-a-date-column"),
        pytest.param(_DURATION, None, id="null-duration"),
        pytest.param(_STAMPS, [None, None], id="array-of-nulls"),
    ],
)
def test_unstorable_temporal_asks_no_alias_for_a_value_its_column_does_not_convert(
    column: models.Field[object, object],
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A value holding nothing its column converts at the save answers ``False`` unasked.

    A plain date in a ``DateField`` is stored as it is and ``None`` stores, so the alias
    is never resolved.
    """
    patch_array_field(monkeypatch)

    assert unstorable_temporal(column, value, _unresolvable_alias) is False


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
            lambda: real_array_of(models.DateTimeField()),
            [_IN_RANGE, _PAST_YEAR_9999],
            True,
            id="array-element",
        ),
        pytest.param(
            {},
            lambda: real_array_of(models.DateTimeField()),
            [_IN_RANGE, None],
            False,
            id="array-in-range",
        ),
        pytest.param(
            {},
            lambda: real_array_of(models.TimeField()),
            [datetime.time(9, 30, tzinfo=_OFFSET_16), None],
            True,
            id="array-time-offset-16-00",
        ),
        pytest.param(
            {},
            lambda: real_array_of(models.DateTimeField()),
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

#: Each column the offset is bound into, and whether its value is a ``time`` or a ``datetime``.
_OFFSET_LEAVES = {"datetime": (_STAMP, False), "time": (_TIME, True)}


def _leaf_value(
    zone: datetime.tzinfo | None,
    *,
    is_time: bool,
) -> datetime.datetime | datetime.time:
    if is_time:
        return datetime.time(12, tzinfo=zone)
    return datetime.datetime(2021, 6, 15, 12, tzinfo=zone)


@pytest.mark.parametrize("mode", list(BINDING_MODES))
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
    from 16:00. Every member of a list is read. A stand-in alias carries each mode, so
    the rule holds on every test tier; the real server's answers are pinned by
    ``test_unbindable_temporal_answers_what_postgresql_refuses``.
    """
    driver, cursor_factory, client_side = BINDING_MODES[mode]
    column, is_time = _OFFSET_LEAVES[leaf]
    zone, refused_as_text, refused_time_on_server = _POSTGRESQL_OFFSETS[offset]
    value = _leaf_value(zone, is_time=is_time)
    bound = [datetime.time(9, 30), value] if is_time else value
    refused = refused_as_text if client_side else is_time and refused_time_on_server
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert unbindable_temporal(column, bound, lambda: alias) is refused


@pytest.mark.parametrize("mode", list(BINDING_MODES))
@pytest.mark.parametrize("is_time", [False, True], ids=["datetime", "time"])
@pytest.mark.parametrize("offset", list(_POSTGRESQL_OFFSETS))
def test_refuses_utc_offset_reads_each_aware_datetime_or_time_a_query_binds(
    mode: str,
    is_time: bool,  # noqa: FBT001
    offset: str,
) -> None:
    """The offset rule reads every datetime and time among the values a query binds.

    The values are a compiled predicate's parameters, beside which a text, a number, a
    date and a ``None`` bind as they are. A datetime or time is refused for the offset
    its connection's binding mode sends the server, as ``unbindable_temporal`` refuses
    one bound into a column.
    """
    driver, cursor_factory, client_side = BINDING_MODES[mode]
    zone, refused_as_text, refused_time_on_server = _POSTGRESQL_OFFSETS[offset]
    value = _leaf_value(zone, is_time=is_time)
    refused = refused_as_text if client_side else is_time and refused_time_on_server
    params = [
        "label",
        5,
        datetime.date(2021, 6, 15),
        None,
        value,
    ]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert refuses_utc_offset(connections[alias], params) is refused


@pytest.mark.parametrize(
    ("alias_kind", "bound_as_text", "refused"),
    [
        pytest.param("sqlite", False, False, id="not-postgresql"),
        pytest.param("server-side", False, False, id="datetime-bound-on-the-server"),
        pytest.param("server-side", True, True, id="datetime-bound-as-text"),
    ],
)
def test_refuses_utc_offset_reads_the_backend_and_the_text_binding(
    alias_kind: str,
    bound_as_text: bool,  # noqa: FBT001
    refused: bool,  # noqa: FBT001
) -> None:
    """Only PostgreSQL refuses an offset, and ``bound_as_text`` holds it to the text rule.

    A datetime carrying a fraction-of-a-second offset binds on SQLite and, on the server,
    on psycopg 3's server-side binding; bound as text (an ``ArrayField`` element) it is
    refused whatever the connection's binding mode.
    """
    value = _leaf_value(_offset(1, 0, 0, 500_000), is_time=False)
    if alias_kind == "sqlite":
        assert refuses_utc_offset(connections[DEFAULT_DB_ALIAS], [value]) is refused
        return
    driver, cursor_factory, _ = BINDING_MODES["psycopg3-server"]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        answer = refuses_utc_offset(connections[alias], [value], bound_as_text=bound_as_text)
    assert answer is refused


#: Each decimal spelling, and whether PostgreSQL ``numeric``'s format refuses it: up to
#: 131072 digits before the point and 16383 after, the written scale included.
_NUMERIC_SPELLINGS = [
    pytest.param("1e1000000", True, id="huge-exponent"),
    pytest.param("-1e1000000", True, id="negative-huge-exponent"),
    pytest.param("1e-1000000", True, id="tiny-exponent"),
    pytest.param("1E+131072", True, id="131073-integer-digits"),
    pytest.param("1E-16384", True, id="16384-fraction-digits"),
    pytest.param("-1E-16384", True, id="negative-16384-fraction-digits"),
    pytest.param("1." + "0" * 16384, True, id="16384-trailing-zeros"),
    pytest.param("1E+131071", False, id="131072-integer-digits"),
    pytest.param("1E-16383", False, id="16383-fraction-digits"),
    pytest.param("-1E-16383", False, id="negative-16383-fraction-digits"),
    pytest.param("1." + "0" * 16383, False, id="16383-trailing-zeros"),
    pytest.param("12.50", False, id="plain"),
    pytest.param("0E+1000000", False, id="zero-huge-exponent"),
    pytest.param("-0E+1073741822", False, id="zero-below-exponent-limit"),
    pytest.param("0E+1073741823", True, id="zero-at-exponent-limit"),
    pytest.param("0E-16383", False, id="zero-16383-fraction-digits"),
    pytest.param("0E-16384", True, id="zero-16384-fraction-digits"),
]


@pytest.mark.parametrize("mode", list(BINDING_MODES))
@pytest.mark.parametrize(("raw", "refused"), _NUMERIC_SPELLINGS)
def test_refuses_numeric_format_holds_each_decimal_a_query_binds_to_numeric(
    mode: str,
    raw: str,
    refused: bool,  # noqa: FBT001
) -> None:
    """PostgreSQL refuses a decimal whose spelling lies past ``numeric``'s format.

    The values are a compiled predicate's parameters, beside which a text, an integer, a
    float and a ``None`` bind as they are. ``numeric_in`` parses the spelling psycopg
    sends whatever the binding mode, so the answer is one rule in every mode.
    """
    driver, cursor_factory, _ = BINDING_MODES[mode]
    params = [
        "label",
        5,
        1.5,
        None,
        Decimal(raw),
    ]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert refuses_numeric_format(connections[alias], params) is refused


@pytest.mark.parametrize(("raw", "refused"), _NUMERIC_SPELLINGS)
@pytest.mark.parametrize("nested", [False, True], ids=["list", "nested-tuple"])
def test_refuses_numeric_format_reads_each_element_of_a_list_parameter(
    raw: str,
    refused: bool,  # noqa: FBT001
    nested: bool,  # noqa: FBT001
) -> None:
    """Each decimal element of a list parameter, at any nesting depth, is held to ``numeric``."""
    elements: list[object] = [None, Decimal(1), Decimal(raw)]
    parameter: object = (Decimal(1), tuple(elements)) if nested else elements
    driver, cursor_factory, _ = BINDING_MODES["psycopg3-client"]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert refuses_numeric_format(connections[alias], [parameter]) is refused


class _UnrangedIntegerField(models.IntegerField[int, int]):
    """An integer column type naming an internal type no backend states a range for."""

    @override
    def get_internal_type(self) -> str:
        return "UnrangedIntegerField"


def _read_default_ranges(monkeypatch: pytest.MonkeyPatch) -> BaseDatabaseWrapper:
    """The default connection, its operations reading Django's default integer ranges (PostgreSQL's)."""
    wrapper = connections[DEFAULT_DB_ALIAS]
    monkeypatch.setattr(
        wrapper.ops,
        "integer_field_range",
        functools.partial(BaseDatabaseOperations.integer_field_range, wrapper.ops),
    )
    return wrapper


@pytest.mark.parametrize(
    ("field", "number", "bound"),
    [
        pytest.param(models.IntegerField[int, int](), 2**31 - 1, True, id="integer-max"),
        pytest.param(models.IntegerField[int, int](), 2**31, False, id="integer-past-max"),
        pytest.param(
            models.PositiveIntegerField[int, int](),
            -1,
            False,
            id="positive-below-min",
        ),
        pytest.param(
            models.DurationField[object, object](),
            2**40,
            True,
            id="non-integer-as-bigint",
        ),
        pytest.param(_UnrangedIntegerField(), 2**70, True, id="unranged-past-int64"),
        pytest.param(_UnrangedIntegerField(), -(2**70), True, id="unranged-before-int64"),
    ],
)
def test_binds_integer_holds_a_number_to_the_range_the_backend_states(
    monkeypatch: pytest.MonkeyPatch,
    field: models.Field[int, int],
    number: int,
    bound: bool,  # noqa: FBT001
) -> None:
    """An integer is held to the range the backend states for the field's internal type.

    On a connection reading Django's default ranges (PostgreSQL's), an ``IntegerField``
    holds 32 bits and a ``PositiveIntegerField`` no negative, a column that is no
    ``IntegerField`` is held to ``BigIntegerField``'s range, and an internal type the
    backend states no range for (``integer_field_range`` raises ``KeyError``) holds no
    limit, as Django holds an ``in`` member or a ``range`` bound to none there.
    """
    assert binds_integer(_read_default_ranges(monkeypatch), field, number) is bound


#: Each compiled parameter list an integer-array predicate binds, and whether it refuses.
_INTEGER_ARRAY_PARAMS = [
    pytest.param([1, 2**63 - 1, -(2**63)], False, id="64-bit-ends"),
    pytest.param([1, 2**63], True, id="past-int64"),
    pytest.param([-(2**63) - 1], True, id="before-int64"),
    pytest.param([[1, 2**63]], True, id="list-parameter"),
    pytest.param([(1, (2**63,))], True, id="nested-tuple"),
    pytest.param(
        [
            "label",
            1.5,
            None,
            True,
            Decimal(2**70),
            str(2**70),
        ],
        False,
        id="non-integers-not-read",
    ),
]


@pytest.mark.parametrize(("params", "refused"), _INTEGER_ARRAY_PARAMS)
def test_refuses_integer_range_holds_each_integer_a_query_binds_to_the_element_range(
    params: list[object],
    refused: bool,  # noqa: FBT001
) -> None:
    """Each integer of a compiled predicate's parameters is held to the element's range.

    A list or tuple is one list parameter, read at any nesting depth; a ``bool``, a text,
    a float, a decimal and a ``None`` are not read. SQLite binds every integer type in 64
    bits.
    """
    assert (
        refuses_integer_range(
            connections[DEFAULT_DB_ALIAS],
            models.IntegerField[int, int](),
            params,
        )
        is refused
    )


@pytest.mark.parametrize(
    ("field", "params", "refused"),
    [
        pytest.param(
            models.IntegerField[int, int](),
            [2**31 - 1, [-(2**31)]],
            False,
            id="int32-ends",
        ),
        pytest.param(models.IntegerField[int, int](), [[1, 2**31]], True, id="past-int32"),
        pytest.param(
            models.SmallIntegerField[int, int](),
            [2**15],
            True,
            id="small-past-int16",
        ),
        pytest.param(_UnrangedIntegerField(), [[2**70]], False, id="unranged"),
    ],
)
def test_refuses_integer_range_reads_the_element_type_range(
    monkeypatch: pytest.MonkeyPatch,
    field: models.Field[int, int],
    params: list[object],
    refused: bool,  # noqa: FBT001
) -> None:
    """The range is the one the backend states for the element column's own internal type."""
    assert refuses_integer_range(_read_default_ranges(monkeypatch), field, params) is refused


@pytest.mark.parametrize(("raw", "_refused"), _NUMERIC_SPELLINGS)
def test_refuses_numeric_format_reads_only_postgresql(raw: str, _refused: bool) -> None:  # noqa: FBT001
    """No other backend is read: SQLite binds every one of the PostgreSQL rows."""
    assert not refuses_numeric_format(
        connections[DEFAULT_DB_ALIAS],
        [Decimal(raw), [Decimal(raw)]],
    )


@pytest.mark.parametrize("mode", list(BINDING_MODES))
@pytest.mark.parametrize("is_time", [False, True], ids=["datetime", "time"])
@pytest.mark.parametrize("offset", list(_POSTGRESQL_OFFSETS))
@pytest.mark.parametrize("nested", [False, True], ids=["list", "nested-tuple"])
def test_refuses_utc_offset_holds_a_list_parameter_to_the_text_rule(
    mode: str,
    is_time: bool,  # noqa: FBT001
    offset: str,
    nested: bool,  # noqa: FBT001
) -> None:
    """Each element of a list parameter is held to the text rule in every binding mode.

    An ``ArrayField`` lookup's ``gt`` or ``in`` right-hand side binds the list as one
    parameter, whose elements psycopg binds as text whatever the cursor, at any nesting
    depth: a datetime or time is refused for an offset of 16:00 or more either way, or
    one with a fraction of a second, even where the same value bound alone on the server
    passes.
    """
    driver, cursor_factory, _ = BINDING_MODES[mode]
    zone, refused_as_text, _ = _POSTGRESQL_OFFSETS[offset]
    elements: list[object] = [None, _leaf_value(zone, is_time=is_time)]
    param: object = (tuple(elements),) if nested else elements
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert refuses_utc_offset(connections[alias], ["label", param]) is refused_as_text


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
    driver, cursor_factory, _ = BINDING_MODES["psycopg3-client"]
    with postgresql_stand_in(driver, cursor_factory) as alias:
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
@pytest.mark.parametrize("leaf", [*_OFFSET_LEAVES, "time-transform"])
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
    answer what the server does, and so does ``refuses_utc_offset`` over the time a
    datetime's ``time`` transform binds.
    """
    column, is_time = _OFFSET_LEAVES.get(leaf, (None, True))
    zone, _, _ = _POSTGRESQL_OFFSETS[offset]
    value = _leaf_value(zone, is_time=is_time)
    target = {"datetime": "occurred_at", "time": "occurred_time"}.get(leaf, "occurred_at__time")
    with _postgresql_alias(server_side_binding=server_side_binding) as alias:
        with warnings.catch_warnings():
            # A naive datetime under ``USE_TZ`` is made aware in the current time zone.
            warnings.filterwarnings("ignore", "DateTimeField .* received a naive", RuntimeWarning)
            refused = _postgresql_refuses(alias, target, value)
        if column is None:
            assert refuses_utc_offset(connections[alias], [value]) is refused
            return
        assert unbindable_temporal(column, [value], lambda: alias) is refused
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
    patch_array_field(monkeypatch)
    driver, cursor_factory, _ = BINDING_MODES["psycopg3-server"]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        assert unstorable_temporal(column, value, lambda: alias) is refused


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize("server_side_binding", [False, True], ids=["client-side", "server-side"])
@pytest.mark.parametrize("lookup", ["contains", "gt"])
@pytest.mark.parametrize("offset", ["15-59-59", "16-00", "half-second"])
def test_refuses_utc_offset_answers_postgresql_for_array_lookups(
    server_side_binding: bool,  # noqa: FBT001
    lookup: str,
    offset: str,
) -> None:
    """On the real server an array lookup's parameters are refused as the rule answers.

    A datetime array's ``contains`` (``@> ARRAY[%s]::timestamptz[]``, each element its own
    parameter) and ``gt`` (the list bound as one parameter) run over a temporary table on
    a second alias connecting with psycopg 3's ``server_side_binding`` off and on; the
    server's answer and ``refuses_utc_offset`` over the compiled parameters agree. Bound on
    the server only the list parameter's elements are refused, as text.
    """

    class ArrayOffsetProbe(models.Model):
        stamps = real_array_of(models.DateTimeField())

        class Meta:
            managed = False
            app_label = "test_array_offset_probe"
            db_table = "array_offset_probe"

    zone, refused_as_text, _ = _POSTGRESQL_OFFSETS[offset]
    expected = refused_as_text and (lookup == "gt" or not server_side_binding)
    value = [_leaf_value(zone, is_time=False)]
    with _postgresql_alias(server_side_binding=server_side_binding) as alias:
        connection = connections[alias]
        queryset = ArrayOffsetProbe.objects.using(alias).filter(**{f"stamps__{lookup}": value})
        compiler = call_method(queryset.query, "get_compiler", alias)
        compiled = require(call_method(compiler, "compile", queryset.query.where), is_tuple)
        params = require(compiled[1], is_list_or_tuple)
        with transaction.atomic(using=alias), connection.cursor() as cursor:
            cursor.execute(
                "CREATE TEMP TABLE array_offset_probe (id serial PRIMARY KEY, stamps timestamptz[])",
            )
            try:
                with transaction.atomic(using=alias):
                    _ = list(queryset)
            except DataError:
                refused = True
            else:
                refused = False
            transaction.set_rollback(True, using=alias)
        assert refused is expected
        assert refuses_utc_offset(connection, params) is expected


class _DriverDataError(Exception):
    """A database driver's ``DataError``."""


#: The adapters a stand-in psycopg 3 module exports, and those of an open connection.
_MODULE_ADAPTERS = object()
_OPEN_ADAPTERS = object()

#: One recorded list dump: the adapters, the parameters and the formats dumped.
_Dump = tuple[object, list[object], list[object]]


def _psycopg3_driver(outcome: Exception | None, dumps: list[_Dump]) -> ModuleType:
    """A psycopg 3 module whose ``adapt.Transformer`` records each dump into ``dumps``.

    A dump raises ``outcome`` when one is given, else dumps silently.
    """

    class Transformer:
        def __init__(self, adapters: object) -> None:
            self.adapters = adapters

        def dump_sequence(self, params: list[object], formats: list[object]) -> list[object]:
            dumps.append((self.adapters, params, formats))
            if outcome is not None:
                raise outcome
            return []

    adapt = ModuleType("adapt_stand_in")
    vars(adapt).update(Transformer=Transformer, PyFormat=SimpleNamespace(TEXT="text"))
    driver = driver_module(ClientCursor=ClientCursor, DataError=_DriverDataError)
    vars(driver).update(adapt=adapt, adapters=_MODULE_ADAPTERS)
    return driver


@pytest.mark.parametrize(
    ("outcome", "refused"),
    [
        pytest.param(_DriverDataError("cannot dump"), True, id="driver-refuses"),
        pytest.param(None, False, id="driver-dumps"),
    ],
)
def test_unstorable_temporal_asks_psycopg_for_an_array_as_a_whole(
    outcome: Exception | None,
    refused: bool,  # noqa: FBT001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On psycopg 3 an ``ArrayField`` list is dumped as text by the driver, and refused on its ``DataError``.

    psycopg dumps a list with one element dumper, so a list whose elements each pass the
    per-element rule can still be refused; the driver's own answer decides. The list
    reaches the driver flattened and projected as the save binds it (a date in a
    ``DateTimeField`` column as its midnight, made aware), ``None`` kept, through the
    driver module's adapters while the connection is not open.
    """
    patch_array_field(monkeypatch)
    dumps: list[_Dump] = []
    stamp = datetime.datetime(2021, 6, 15, 12, tzinfo=_UTC)
    with postgresql_stand_in(_psycopg3_driver(outcome, dumps), DjangoClientCursor) as alias:
        value = [[datetime.date(2021, 6, 15)], [None, stamp]]
        assert unstorable_temporal(_NESTED_STAMPS, value, lambda: alias) is refused
    midnight = datetime.datetime(2021, 6, 15, tzinfo=timezone.get_default_timezone())
    assert dumps == [(_MODULE_ADAPTERS, [[midnight, None, stamp]], ["text"])]


def test_unstorable_temporal_dumps_an_array_through_the_open_connection_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An already open psycopg 3 connection's adapters dump the list, not the module's."""
    patch_array_field(monkeypatch)
    dumps: list[_Dump] = []
    with postgresql_stand_in(_psycopg3_driver(None, dumps), DjangoClientCursor) as alias:
        connection = connections[alias]
        connection.connection = SimpleNamespace(adapters=_OPEN_ADAPTERS)
        try:
            assert unstorable_temporal(_TIMES, [_AWARE_TIME], lambda: alias) is False
        finally:
            connection.connection = None
    assert dumps == [(_OPEN_ADAPTERS, [[_AWARE_TIME]], ["text"])]


def test_unstorable_temporal_propagates_any_other_driver_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the driver's ``DataError`` refuses a list; anything else it raises propagates."""
    patch_array_field(monkeypatch)
    driver = _psycopg3_driver(LookupError("unexpected"), [])
    with (
        postgresql_stand_in(driver, DjangoClientCursor) as alias,
        pytest.raises(LookupError, match="unexpected"),
    ):
        _ = unstorable_temporal(_TIMES, [_AWARE_TIME], lambda: alias)


@pytest.mark.parametrize(
    (
        "driver",
        "vendor",
        "column",
        "value",
    ),
    [
        pytest.param(
            driver_module(DataError=_DriverDataError),
            "postgresql",
            _TIMES,
            [datetime.time(9, 30), _AWARE_TIME],
            id="psycopg2",
        ),
        pytest.param(
            _psycopg3_driver(_DriverDataError("cannot dump"), []),
            "postgresql",
            _TIMES,
            ["09:30", _AWARE_TIME],
            id="element-the-column-converts",
        ),
        pytest.param(
            _psycopg3_driver(_DriverDataError("cannot dump"), []),
            "sqlite",
            _TIMES,
            [datetime.time(9, 30)],
            id="not-postgresql",
        ),
        pytest.param(
            _psycopg3_driver(_DriverDataError("cannot dump"), []),
            "postgresql",
            _STAMPS,
            [_IN_RANGE, _AWARE_TIME],
            id="element-another-column-stores",
        ),
    ],
)
def test_unstorable_temporal_leaves_an_array_the_driver_is_not_asked_about(
    driver: ModuleType,
    vendor: str,
    column: models.Field[object, object],
    value: list[object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Psycopg 2, a list holding an element the column converts, and another backend are not dumped.

    psycopg 2 has no ``adapt.Transformer`` to ask. An element that is neither ``None`` nor
    the type the column stores (a string, or a time in a ``DateTimeField`` array) is
    converted by the column's ``to_python`` at the save, or refused there, before the
    driver sees it, so the list as it stands is not what the save binds. A connection
    that is not PostgreSQL is not asked, whatever its driver module exports.
    """
    patch_array_field(monkeypatch)
    with postgresql_stand_in(driver, DjangoClientCursor) as alias:
        connections[alias].vendor = vendor
        assert unstorable_temporal(column, value, lambda: alias) is False


_NAIVE_TIME = datetime.time(9, 30)
_LATER_NAIVE_TIME = datetime.time(10)
_OTHER_AWARE_TIME = datetime.time(11, tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))


@pytest.mark.parametrize(
    ("value", "nested", "refused"),
    [
        pytest.param([_NAIVE_TIME, _AWARE_TIME], False, True, id="naive-aware"),
        pytest.param(
            [_AWARE_TIME, _NAIVE_TIME, _OTHER_AWARE_TIME],
            False,
            True,
            id="aware-naive-aware",
        ),
        pytest.param([None, _NAIVE_TIME, _AWARE_TIME], False, True, id="none-naive-aware"),
        pytest.param([[_NAIVE_TIME], [_AWARE_TIME]], True, True, id="nested-naive-aware"),
        pytest.param([_AWARE_TIME, _NAIVE_TIME], False, False, id="aware-naive"),
        pytest.param(
            [_NAIVE_TIME, _AWARE_TIME, _LATER_NAIVE_TIME],
            False,
            False,
            id="naive-aware-naive",
        ),
        pytest.param([_AWARE_TIME, _OTHER_AWARE_TIME], False, False, id="all-aware"),
        pytest.param([_NAIVE_TIME, _LATER_NAIVE_TIME], False, False, id="all-naive"),
        pytest.param(
            [_NAIVE_TIME, datetime.datetime(2021, 6, 15, 9, 30)],  # noqa: DTZ001 - naive under test
            False,
            False,
            id="time-datetime",
        ),
        pytest.param(
            [datetime.datetime(2021, 6, 15, 9, 30, tzinfo=_UTC), _AWARE_TIME],
            False,
            True,
            id="aware-datetime-aware-time",
        ),
        pytest.param([None], False, False, id="none"),
        pytest.param([], False, False, id="empty"),
    ],
)
def test_unstorable_temporal_refuses_a_time_array_psycopg_cannot_dump(
    value: list[object],
    nested: bool,  # noqa: FBT001
    refused: bool,  # noqa: FBT001
) -> None:
    """A time list is refused exactly when psycopg 3 itself cannot dump it.

    psycopg dumps a list with the dumper of one element, so a naive time dumped by the
    aware-time dumper raises its ``DataError``; each list here stores element by element.
    A datetime element is read as the naive ``time()`` the column stores for it, so an
    aware datetime beside an aware time is a naive time beside an aware one.
    The alias stands in for PostgreSQL on the real driver module, never connected; the
    list's elements are dumped as text in either binding mode.
    """
    pytest.importorskip("psycopg")
    psycopg = importlib.import_module("psycopg")
    column = real_array_of(models.TimeField())
    if nested:
        column = real_array_of(column)
    with postgresql_stand_in(psycopg, None) as alias:
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
            lambda: real_array_of(models.DateTimeField()),
            [_leaf_value(_offset(16), is_time=False)],
            True,
            id="datetime-element",
        ),
        pytest.param(
            lambda: real_array_of(models.TimeField()),
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
