"""Shared mutation-error constructors: leaf shapes, the Django mapper, the code vocabulary.

Scalar / byte / lazy-translation message coercion and the ``ValidationError``
mapping read Python values no wire request can shape. Consumer envelopes
(constraint ``codes``, ``__all__`` sentinel, relation ``not_found``) live in
``examples/fakeshop/test_query/test_products_api.py``. The error key map
primitives (``build_error_key_map``, ``rekey_error_segment``,
``model_field_error_names``) are pinned here directly; the per-flavor keying matrix
is ``tests/utils/test_error_keys.py``.
"""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from apps.library import models as library_models
from apps.products import models as product_models
from django.core.exceptions import ValidationError
from django.db.models import Model
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
    validation_error_to_field_errors,
)
from django_strawberry_framework.utils.inputs import RELATION_SINGLE, SCALAR, InputFieldSpec

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
