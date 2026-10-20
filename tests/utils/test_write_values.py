"""Direct pins of write-value decode internals a GraphQL request cannot name.

Omitted-vs-null-vs-provided identity, hostile containers, generator materialization,
and GraphQL-unrepresentable member shapes (string-in-a-list, mixed GlobalID+pk) stay
here because the wire never delivers them. Consumer envelopes for hidden vs missing
relation ids, batched ``pk__in`` cost, duplicate members, and empty M2M clears live in
``examples/fakeshop/test_query/test_products_api.py`` and
``examples/fakeshop/test_query/test_library_api.py``.
"""

import sys
from collections.abc import Iterator
from enum import Enum
from typing import TYPE_CHECKING, NoReturn
from unittest import mock

import pytest
import strawberry
from apps.products.models import Category
from apps.scalars.models import NullableScalarSpecimen
from django.db import connection
from django.db.models import Model
from django.test.utils import CaptureQueriesContext
from django.utils.functional import SimpleLazyObject
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework.forms import resolvers as form_resolvers
from django_strawberry_framework.mutations import resolvers as mutation_resolvers
from django_strawberry_framework.mutations.inputs import FieldError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework import resolvers as serializer_resolvers
from django_strawberry_framework.types.base import DjangoType
from django_strawberry_framework.types.finalizer import finalize_django_types
from django_strawberry_framework.utils.errors import field_error
from django_strawberry_framework.utils.inputs import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    InputFieldSpec,
)
from django_strawberry_framework.utils.write_transaction import write_pipeline
from django_strawberry_framework.utils.write_values import (
    coerce_relation_pk_or_none,
    decode_field_handlers,
    decode_provided_fields,
    decode_scalar_leaf,
    decode_visible_relation,
    decode_visible_relation_ids,
    decoded_into,
    file_into,
    materialize_relation_id_container,
    raw_choice_value,
    relation_into,
    scalar_into,
    store_decoded,
    unencodable_text_error,
)
from tests._idioms import module_binding, saved_pk
from tests._info import make_info, unread_info

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeAlias

    _FieldHandler: TypeAlias = Callable[[InputFieldSpec, object], FieldError | None]


# basedpyright: Strawberry's idiom for an omittable input field defaults it to UNSET, which its
# stub types Any so it fits any annotation; this is that default under the field annotation
_OMITTED: None = strawberry.UNSET  # pyright: ignore[reportAny]


@strawberry.input
class _TriStateInput:
    scalar: str | None = _OMITTED
    relation: int | None = _OMITTED


_TRI_STATE_SPECS = [
    InputFieldSpec(
        input_attr="scalar",
        graphql_name="scalar",
        target_name="scalar",
        kind="scalar",
    ),
    InputFieldSpec(
        input_attr="relation",
        graphql_name="relation",
        target_name="relation",
        kind="relation",
        related_model=Category,
    ),
]


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db
def test_decode_layers_preserve_omitted_null_and_provided_values() -> None:
    """The shared gate never collapses omitted, explicit-null, and provided input states."""
    decoded: dict[str, object] = {}

    def relation_handler(spec: InputFieldSpec, value: object) -> FieldError | None:
        related_model = spec.related_model
        assert related_model is not None
        result, error = decode_visible_relation(
            value,
            graphql_name=spec.graphql_name,
            related_model=related_model,
            info=unread_info(),
            async_recourse="Use a synchronous visibility hook.",
            skip=lambda candidate: candidate is None,
            project=saved_pk,
            key_attname=None,
        )
        if error is None:
            decoded[spec.input_attr] = result
        return error

    def scalar_handler(spec: InputFieldSpec, value: object) -> FieldError | None:
        result, error = decode_scalar_leaf(spec.graphql_name, value)
        if error is None:
            decoded[spec.input_attr] = result
        return error

    error = decode_provided_fields(
        _TRI_STATE_SPECS,
        _TriStateInput(),
        handlers={"relation": relation_handler},
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert decoded == {}

    error = decode_provided_fields(
        _TRI_STATE_SPECS,
        _TriStateInput(scalar=None, relation=None),
        handlers={"relation": relation_handler},
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert decoded == {"scalar": None, "relation": None}

    category = Category.objects.create(name="TriState")
    error = decode_provided_fields(
        _TRI_STATE_SPECS,
        _TriStateInput(scalar="provided", relation=saved_pk(category)),
        handlers={"relation": relation_handler},
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert decoded == {"scalar": "provided", "relation": saved_pk(category)}


@pytest.mark.django_db
def test_decode_visible_relation_ids_rejects_uncoercible_member_without_a_visibility_query() -> (
    None
):
    """A string member fails the type check before any ``pk__in``; GraphQL ``[Int!]`` never delivers it."""
    first = Category.objects.create(name="BatchA")
    recourse = "Use a synchronous visibility hook."

    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            [saved_pk(first), "bad"],
            graphql_name="categoryIds",
            related_model=Category,
            info=unread_info(),
            async_recourse=recourse,
        )
    assert pks is None
    assert error is not None
    assert error.field == "categoryIds"
    assert ctx.captured_queries == []


def test_decode_visible_relation_ids_maps_a_non_iterable_to_relation_error() -> None:
    """A non-iterable container stays inside the field error envelope."""
    pks, error = decode_visible_relation_ids(
        object(),
        graphql_name="categoryIds",
        related_model=Category,
        info=unread_info(),
        async_recourse="Use a synchronous visibility hook.",
    )
    assert pks is None
    assert error is not None
    assert error.field == "categoryIds"


def test_materialize_relation_id_container_iteration_error_propagates() -> None:
    """An iterable's own iteration runs untouched; what it raises propagates."""

    class RaisingIterator:
        def __iter__(self) -> Iterator[int]:
            yield 1
            raise RuntimeError("relation iterator detonated")

    with pytest.raises(RuntimeError, match="relation iterator detonated"):
        materialize_relation_id_container(RaisingIterator(), "categoryIds")


class _TextSub(str):
    pass


class _MappingSub(dict[str, object]):
    pass


@pytest.mark.parametrize(
    "values",
    [
        pytest.param("12", id="str"),
        pytest.param(_TextSub("ab"), id="str-subclass"),
        pytest.param(b"12", id="bytes"),
        pytest.param(bytearray(b"1"), id="bytearray"),
        pytest.param(memoryview(b"1"), id="memoryview"),
        pytest.param({"a": 1}, id="dict"),
        pytest.param(_MappingSub({"a": 1}), id="dict-subclass"),
        pytest.param(SimpleLazyObject(lambda: "12"), id="lazy-str"),
        pytest.param(SimpleLazyObject(lambda: {"a": 1}), id="lazy-dict"),
        pytest.param(7, id="int"),
        pytest.param(object(), id="object"),
    ],
)
def test_materialize_relation_id_container_rejects_text_mapping_and_non_iterable_atoms(
    values: object,
) -> None:
    """Text / bytes-like / mapping atoms (subclasses included) and non-iterables are the uniform error.

    A text atom iterated would decompose into per-character "ids" and a mapping
    into per-key "ids"; a non-iterable would raise ``TypeError`` out of ``list()``.
    A Django lazy proxy is judged by the object it stands for.
    """
    provided_values, error = materialize_relation_id_container(values, "categoryIds")
    assert provided_values is None
    assert error is not None
    assert error.field == "categoryIds"


@pytest.mark.parametrize(
    "values",
    [
        pytest.param([1, 2], id="list"),
        pytest.param(SimpleLazyObject(lambda: [1, 2]), id="lazy-list"),
    ],
)
def test_materialize_relation_id_container_materializes_a_list(values: object) -> None:
    """A list, or a lazy proxy standing for one, is materialized member by member."""
    provided_values, error = materialize_relation_id_container(values, "categoryIds")
    assert error is None
    assert provided_values == [1, 2]


def test_materialize_relation_id_container_materializes_once() -> None:
    """A one-shot generator is fully consumed by exactly one materialization pass.

    The decoded set is what the container yielded, never a re-iteration.
    """
    consumed: list[int] = []

    def _one_shot() -> Iterator[int]:
        for item in (1, 2):
            consumed.append(item)
            yield item

    provided_values, error = materialize_relation_id_container(_one_shot(), "categoryIds")
    assert error is None
    assert provided_values == [1, 2]
    assert consumed == [1, 2]


def _spec(
    *,
    attr: str,
    kind: str,
    target: str | None = None,
    graphql: str | None = None,
    key_attname: str | None = None,
) -> InputFieldSpec:
    return InputFieldSpec(
        input_attr=attr,
        graphql_name=graphql or attr,
        target_name=target or attr,
        kind=kind,
        related_model=Category if kind in {RELATION_SINGLE, RELATION_MULTI} else None,
        key_attname=key_attname,
    )


def test_store_decoded_writes_target_or_returns_error() -> None:
    """The store glue writes ``target_name`` on success and leaves dest untouched on error."""
    dest: dict[str, object] = {}
    spec = _spec(attr="name", kind=SCALAR, target="title", graphql="displayName")
    assert store_decoded(dest, spec, ("ok", None)) is None
    assert dest == {"title": "ok"}

    error = field_error("displayName", "nope", codes="invalid")
    dest.clear()
    assert store_decoded(dest, spec, (None, error)) is error
    assert dest == {}


def test_decode_scalar_leaf_rejects_hostile_string_subclass_encoding() -> None:
    """Unicode preflight must not dispatch a consumer string subclass's ``encode``."""

    class HostileText(str):
        @override
        def encode(self, *args: object, **kwargs: object) -> bytes:
            return b""

    decoded, error = decode_scalar_leaf("name", HostileText("\ud800"))
    assert decoded is None
    assert error is not None
    assert error.field == "name"


def test_decode_scalar_leaf_normalizes_string_subclass_after_preflight() -> None:
    """A valid string subclass is stored as an exact ``str``, not consumer code."""

    class HostileText(str):
        @override
        def __str__(self) -> str:
            raise AssertionError("storage must not dispatch the override")

    decoded, error = decode_scalar_leaf("name", HostileText("valid"))
    assert error is None
    assert type(decoded) is str
    assert decoded == "valid"


class _Flag(Enum):
    BLANK = ""
    on = "on"


def test_raw_choice_value_unwraps_list_elements() -> None:
    """A list-of-choices value arrives as members; each is unwrapped, ``BLANK`` to ``""``."""
    members = [
        _Flag.BLANK,
        _Flag.on,
        "raw",
        None,
    ]
    decoded = raw_choice_value(members)
    assert decoded == [
        "",
        "on",
        "raw",
        None,
    ]
    assert decoded is not members
    assert members == [
        _Flag.BLANK,
        _Flag.on,
        "raw",
        None,
    ]


def test_raw_choice_value_unwraps_one_level_only() -> None:
    """A nested list is a JSON value, which never carries a member: it passes through untouched."""
    nested = [[_Flag.on]]
    decoded = raw_choice_value(nested)
    assert isinstance(decoded, list)
    assert decoded == [[_Flag.on]]
    assert decoded[0] is nested[0]


def test_decode_scalar_leaf_checks_choice_value_after_unwrapping() -> None:
    """An enum's raw storage string receives the Unicode preflight."""

    class InvalidTextChoice(Enum):
        broken = "\ud800"

    decoded, error = decode_scalar_leaf("status", InvalidTextChoice.broken)
    assert decoded is None
    assert error is not None
    assert error.field == "status"
    assert error.codes == ["invalid"]

    decoded, error = decode_scalar_leaf("statuses", [InvalidTextChoice.broken])
    assert decoded is None
    assert error is not None
    assert error.field == "statuses.0"


class _HidingList(list[object]):
    """A list whose own iteration hides every element behind one valid string."""

    @override
    def __iter__(self) -> Iterator[object]:
        return iter(["fine"])


class _HidingDict(dict[object, object]):
    """A dict whose own ``items`` refuses to be read."""

    @override
    def items(self) -> NoReturn:
        raise AssertionError("the walk must not dispatch the override")


@pytest.mark.parametrize(
    ("value", "error_field"),
    [
        (_HidingList(["ok", "\ud800"]), "tags.1"),
        ({"rows": _HidingList(["\ud800"])}, "tags.rows.0"),
        (_HidingDict({"color": "\ud800"}), "tags.color"),
        ([_HidingDict({"\ud800": "red"})], "tags.0"),
    ],
)
def test_unencodable_text_error_reads_containers_through_the_base_slots(
    value: object,
    error_field: str,
) -> None:
    """A list / dict subclass's overridden iteration cannot hide an unstorable leaf."""
    error = unencodable_text_error("tags", value)
    assert error is not None
    assert error.field == error_field


def test_unencodable_text_error_walks_nesting_deeper_than_the_recursion_limit() -> None:
    """The walk keeps an explicit stack, so a deeply nested ``JSON`` value cannot overflow it."""
    depth = sys.getrecursionlimit() * 2
    root: list[object] = []
    level = root
    for _ in range(depth):
        child: list[object] = []
        level.append(child)
        level = child
    level.append("\ud800")

    error = unencodable_text_error("payload", root)
    assert error is not None
    assert error.path == ["payload", *(["0"] * (depth + 1))]


def test_scalar_into_stores_decoded_leaf_and_keys_errors_to_field_name() -> None:
    """SCALAR handlers share ``decode_scalar_leaf`` + ``store_decoded``; nested paths rekey."""
    dest: dict[str, object] = {}
    spec = _spec(attr="name", kind=SCALAR, target="title", graphql="displayName")
    handler = scalar_into(dest)
    assert handler(spec, "ok") is None
    assert dest == {"title": "ok"}

    dest.clear()
    error = handler(spec, "\ud800")
    assert error is not None
    assert error.field == "displayName"
    assert dest == {}

    nested = scalar_into(dest, field_name=lambda item: f"parent.{item.graphql_name}")
    error = nested(spec, "\ud800")
    assert error is not None
    assert error.field == "parent.displayName"


def test_file_into_stores_upload_on_the_supplied_dest() -> None:
    """FILE destination is the flavor policy: form ``files=`` vs serializer ``data``."""
    files: dict[str, object] = {}
    data: dict[str, object] = {}
    spec = _spec(attr="attachment", kind=FILE, target="attachment")
    upload = object()
    assert file_into(files)(spec, upload) is None
    assert files == {"attachment": upload}
    assert data == {}
    assert file_into(data)(spec, upload) is None
    assert data == {"attachment": upload}


def test_relation_into_dispatches_single_and_multi_then_stores() -> None:
    """One relation handler picks multi vs single, forwards the spec's key and extras, and stores.

    ``key_attname`` reaches every decoder from the spec, so no flavor resolves the stored
    column itself.
    """
    dest: dict[str, object] = {}
    calls: list[tuple[object, ...]] = []

    def single(
        value: object,
        *,
        graphql_name: str,
        related_model: type[Model],
        key_attname: str | None,
        info: object,
        **extra: object,
    ) -> tuple[str, None]:
        del related_model  # relation_into passes it by keyword; this stand-in does not read it
        calls.append(
            (
                "single",
                value,
                graphql_name,
                key_attname,
                info,
                extra,
            ),
        )
        return f"s-{value}", None

    def multi(
        value: object,
        *,
        graphql_name: str,
        related_model: type[Model],
        key_attname: str | None,
        info: object,
        **extra: object,
    ) -> tuple[list[str | object], None]:
        del related_model  # relation_into passes it by keyword; this stand-in does not read it
        calls.append(
            (
                "multi",
                value,
                graphql_name,
                key_attname,
                info,
                extra,
            ),
        )
        return ["m", value], None

    spec_single = _spec(
        attr="category_id",
        kind=RELATION_SINGLE,
        target="category",
        graphql="categoryId",
        key_attname="code",
    )
    spec_multi = _spec(attr="tag_ids", kind=RELATION_MULTI, target="tags", graphql="tagIds")
    info = make_info()
    handler = relation_into(
        dest,
        single=single,
        multi=multi,
        info=info,
        extra=lambda spec: {"form_field": spec.target_name},
    )
    assert handler(spec_single, 7) is None
    assert dest["category"] == "s-7"
    assert calls[0] == (
        "single",
        7,
        "categoryId",
        "code",
        info,
        {"form_field": "category"},
    )
    assert handler(spec_multi, [1, 2]) is None
    assert dest["tags"] == ["m", [1, 2]]
    assert calls[1] == (
        "multi",
        [1, 2],
        "tagIds",
        None,
        info,
        {"form_field": "tags"},
    )

    dest.clear()

    def failing(
        _value: object,
        *,
        graphql_name: str,
        related_model: type[Model],
        key_attname: str | None,
        info: object,
    ) -> tuple[None, FieldError]:
        del (
            related_model,
            key_attname,
            info,
        )  # relation_into passes it by keyword; this stand-in does not read it
        return None, field_error(graphql_name, "hidden", codes="invalid")

    error_handler = relation_into(dest, single=failing, multi=failing, info=unread_info())
    error = error_handler(spec_single, 7)
    assert error is not None
    assert error.field == "categoryId"
    assert dest == {}


def test_decoded_into_is_the_store_glue_nested_handlers_use() -> None:
    """Nested serializer decode is the same store primitive as SCALAR / FILE / RELATION."""
    dest: dict[str, object] = {}
    spec = _spec(attr="shelves", kind="nested_single", target="shelves")
    handler = decoded_into(
        dest,
        lambda item, value: ({"n": value, "k": item.target_name}, None),
    )
    assert handler(spec, {"title": "A"}) is None
    assert dest == {"shelves": {"n": {"title": "A"}, "k": "shelves"}}


def test_decode_field_handlers_split_files_from_data() -> None:
    """The compose both walks call: FILE dest is optional; SCALAR/RELATION share dest."""
    data: dict[str, object] = {}
    files: dict[str, object] = {}
    scalar_spec = _spec(attr="name", kind=SCALAR, target="name")
    file_spec = _spec(attr="attachment", kind=FILE, target="attachment")
    relation_spec = _spec(attr="category_id", kind=RELATION_SINGLE, target="category")

    def single(
        value: object,
        *,
        graphql_name: str,
        related_model: type[Model],
        key_attname: str | None,
        info: object,
    ) -> tuple[str, None]:
        del (
            graphql_name,
            related_model,
            key_attname,
            info,
        )  # relation_into passes it by keyword; this stand-in does not read it
        return f"pk-{value}", None

    def multi(
        _value: object,
        *,
        graphql_name: str,
        related_model: type[Model],
        key_attname: str | None,
        info: object,
    ) -> NoReturn:
        del (
            graphql_name,
            related_model,
            key_attname,
            info,
        )  # relation_into passes it by keyword; this stand-in does not read it
        raise AssertionError("multi should not run")

    handlers, scalar_handler = decode_field_handlers(
        data,
        info=unread_info(),
        single=single,
        multi=multi,
        file_dest=files,
    )
    assert scalar_handler(scalar_spec, "Widget") is None
    assert handlers[FILE](file_spec, "upload") is None
    assert handlers[RELATION_SINGLE](relation_spec, 3) is None
    assert data == {"name": "Widget", "category": "pk-3"}
    assert files == {"attachment": "upload"}


def test_form_and_serializer_decode_walks_share_field_handlers() -> None:
    """Form, serializer, and model decode walks import the same store-into-dest compose."""
    assert module_binding(form_resolvers, "decode_field_handlers") is decode_field_handlers
    assert module_binding(serializer_resolvers, "decode_field_handlers") is decode_field_handlers
    assert module_binding(serializer_resolvers, "decoded_into") is decoded_into
    assert module_binding(form_resolvers, "decode_provided_fields") is decode_provided_fields
    assert module_binding(serializer_resolvers, "decode_provided_fields") is decode_provided_fields
    # The model rider composes its handler map from the ``*_into`` primitives
    # directly (it replaces every ``decode_field_handlers`` default but
    # ``RELATION_SINGLE``), so it shares the spine + primitives, not the factory.
    assert module_binding(mutation_resolvers, "decode_provided_fields") is decode_provided_fields
    assert module_binding(mutation_resolvers, "decoded_into") is decoded_into
    assert module_binding(mutation_resolvers, "relation_into") is relation_into


@pytest.mark.django_db
def test_decode_visible_relation_ids_rejects_non_collection_types() -> None:
    """Strings, bytes, bytearrays, memoryviews, and mappings are rejected as invalid relation values."""
    category = Category.objects.create(name="NonCollTarget")
    recourse = "Use a synchronous visibility hook."

    for bad_container in [
        "123",
        "abc",
        b"123",
        bytearray(b"123"),
        memoryview(b"123"),
        {"category": saved_pk(category)},
    ]:
        pks, error = decode_visible_relation_ids(
            bad_container,
            graphql_name="categoryIds",
            related_model=Category,
            info=unread_info(),
            async_recourse=recourse,
        )
        assert pks is None
        assert error is not None
        assert error.field == "categoryIds"


def test_coerce_relation_pk_or_none_handles_non_models_and_uncoercible_values() -> None:
    """coerce_relation_pk_or_none returns None for non-models and uncoercible pks."""
    # basedpyright: the non-model class is the hostile input under test; coerce_relation_pk_or_none
    # types the parameter as type[Model]
    assert coerce_relation_pk_or_none(object, 1) is None  # pyright: ignore[reportArgumentType]
    # basedpyright: the None model is the hostile input under test; coerce_relation_pk_or_none
    # types the parameter as type[Model]
    assert coerce_relation_pk_or_none(None, 1) is None  # pyright: ignore[reportArgumentType]
    assert coerce_relation_pk_or_none(Category, object()) is None


def test_decode_provided_fields_tolerates_unmapped_input_fields() -> None:
    """Input fields present on the data object but not declared in specs are safely skipped."""

    @strawberry.input
    class ExtraFieldInput:
        name: str = "Test"
        extra: str = "Ignored"

    dest: dict[str, object] = {}
    specs = [_spec(attr="name", kind=SCALAR, target="name")]
    handlers: dict[str, _FieldHandler] = {}
    scalar_handler = scalar_into(dest)

    error = decode_provided_fields(
        specs,
        ExtraFieldInput(),
        handlers=handlers,
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert dest == {"name": "Test"}


def test_decode_provided_fields_handles_none_and_non_strawberry_data() -> None:
    """decode_provided_fields safely treats None and non-strawberry data as empty without crashing."""
    dest: dict[str, object] = {}
    specs = [_spec(attr="name", kind=SCALAR, target="name")]
    handlers: dict[str, _FieldHandler] = {}
    scalar_handler = scalar_into(dest)

    assert (
        decode_provided_fields(
            specs,
            None,
            handlers=handlers,
            scalar_handler=scalar_handler,
        )
        is None
    )
    assert dest == {}

    assert (
        decode_provided_fields(
            specs,
            {"name": "dict_input"},
            handlers=handlers,
            scalar_handler=scalar_handler,
        )
        is None
    )
    assert dest == {}


def test_unencodable_text_error_handles_non_strings_and_valid_strings() -> None:
    """unencodable_text_error returns None for non-strings and valid UTF-8 strings."""
    assert unencodable_text_error("field", None) is None
    assert unencodable_text_error("field", 123) is None
    assert unencodable_text_error("field", object()) is None
    assert unencodable_text_error("field", "valid unicode string") is None

    err = unencodable_text_error("field", "\ud800")
    assert err is not None
    assert err.field == "field"
    assert err.codes == ["invalid"]


@pytest.mark.django_db
def test_decode_visible_relation_handles_invalid_id_and_missing_object() -> None:
    """decode_visible_relation returns field errors for type-check failure or missing/hidden object."""
    recourse = "Use a synchronous visibility hook."

    # Type check failure branch
    val, error = decode_visible_relation(
        "not_an_int",
        graphql_name="categoryId",
        related_model=Category,
        info=unread_info(),
        async_recourse=recourse,
        skip=lambda x: x is None,
        project=saved_pk,
        key_attname=None,
    )
    assert val is None
    assert error is not None
    assert error.field == "categoryId"

    # Missing / hidden object branch (type check passes for 999999, but obj is None)
    val, error = decode_visible_relation(
        999999,
        graphql_name="categoryId",
        related_model=Category,
        info=unread_info(),
        async_recourse=recourse,
        skip=lambda x: x is None,
        project=saved_pk,
        key_attname=None,
    )
    assert val is None
    assert error is not None
    assert error.field == "categoryId"


def test_decode_provided_fields_short_circuits_on_handler_error() -> None:
    """decode_provided_fields immediately halts and returns the error from a failing handler."""

    @strawberry.input
    class InputData:
        first: str = "first_val"
        second: str = "second_val"

    specs = [
        _spec(attr="first", kind="fail_kind", target="first"),
        _spec(attr="second", kind=SCALAR, target="second"),
    ]
    failing_handler_called: list[tuple[str, object]] = []
    scalar_handler_called: list[tuple[str, object]] = []

    def failing_handler(spec: InputFieldSpec, val: object) -> FieldError:
        failing_handler_called.append((spec.input_attr, val))
        return field_error(spec.graphql_name, "handler failed", codes="custom_error")

    def dummy_scalar(spec: InputFieldSpec, val: object) -> None:
        scalar_handler_called.append((spec.input_attr, val))

    error = decode_provided_fields(
        specs,
        InputData(),
        handlers={"fail_kind": failing_handler},
        scalar_handler=dummy_scalar,
    )
    assert error is not None
    assert error.field == "first"
    assert error.codes == ["custom_error"]
    assert len(failing_handler_called) == 1
    assert len(scalar_handler_called) == 0


@pytest.mark.django_db
def test_decode_visible_relation_ids_accepts_global_id_members_with_one_query() -> None:
    """GlobalID members decode end-to-end at the batch seam and still batch to ONE query.

    A valid ``GlobalID`` beside a raw pk decodes both to real pks and confirms
    visibility in the single ``pk__in`` query (the GlobalID decode itself is
    non-raising and query-free for a pk ``id_attr``; it reads the executing schema
    off ``info``); a wrong-model GlobalID and a malformed pk token are the uniform
    field-keyed error.
    """

    class GidBatchPinType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert registry.get(Category) is GidBatchPinType

    finalize_django_types()
    recourse = "Use a synchronous visibility hook."
    row = Category.objects.create(name="GidBatch")

    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            [relay.GlobalID("products.category", str(saved_pk(row))), saved_pk(row)],
            graphql_name="categoryIds",
            related_model=Category,
            info=make_info(),
            async_recourse=recourse,
        )
    assert error is None
    assert pks == [saved_pk(row), saved_pk(row)]
    assert len(ctx.captured_queries) == 1

    for bad_gid in (
        relay.GlobalID("unknown.model", str(saved_pk(row))),
        relay.GlobalID("products.category", "not-a-pk"),
    ):
        pks, error = decode_visible_relation_ids(
            [bad_gid],
            graphql_name="categoryIds",
            related_model=Category,
            info=make_info(),
            async_recourse=recourse,
        )
        assert pks is None
        assert error is not None
        assert error.field == "categoryIds"


@pytest.mark.django_db
def test_custom_node_id_relation_set_batches_real_pk_lookup() -> None:
    """A same-type non-pk-NodeID set maps to real pks in ONE query, not one per id.

    The batched set decode resolves each distinct non-pk ``(type, id_attr)``
    group with a single ``__in`` mapping query: total queries stay constant at
    one mapping plus one visibility query across K=1/2/4 (the GlobalID decode
    reads the executing schema off ``info``). A value matching no row is the
    uniform field-keyed error after the mapping query alone (no visibility
    query).
    """

    class NameBatchNodeType(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert registry.get(Category) is NameBatchNodeType

    finalize_django_types()
    recourse = "Use a synchronous visibility hook."
    rows = [Category.objects.create(name=f"BatchNode{i}") for i in range(4)]
    for size in (1, 2, 4):
        members = [relay.GlobalID("products.category", rows[i].name) for i in range(size)]
        with CaptureQueriesContext(connection) as ctx:
            pks, error = decode_visible_relation_ids(
                members,
                graphql_name="categoryIds",
                related_model=Category,
                info=make_info(),
                async_recourse=recourse,
            )
        assert error is None
        assert pks == [rows[i].pk for i in range(size)]
        assert len(ctx.captured_queries) == 2

    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            [relay.GlobalID("products.category", "no-such-batch-name")],
            graphql_name="categoryIds",
            related_model=Category,
            info=make_info(),
            async_recourse=recourse,
        )
    assert pks is None
    assert error is not None
    assert error.field == "categoryIds"
    assert len(ctx.captured_queries) == 1


@pytest.mark.django_db
def test_custom_node_id_relation_set_refuses_unencodable_text_before_the_mapping_query() -> None:
    """A text node id carrying a lone surrogate is the element's field error, with no query run.

    A non-pk ``NodeID[str]`` decodes to the text value the batched ``__in`` mapping query
    would bind, so it meets the same text preflight a raw text pk meets: the answer is the
    preflight's ``invalid`` error keyed to the member's index, before any query.
    """

    class SurrogateBatchNodeType(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert registry.get(Category) is SurrogateBatchNodeType

    finalize_django_types()
    row = Category.objects.create(name="SurrogateBatchNode")
    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            [
                relay.GlobalID("products.category", row.name),
                relay.GlobalID("products.category", "Batch\ud800"),
            ],
            graphql_name="categoryIds",
            related_model=Category,
            info=make_info(),
            async_recourse="Use a synchronous visibility hook.",
        )
    assert pks is None
    assert error is not None
    assert error.field == "categoryIds.1"
    assert error.codes == ["invalid"]
    assert ctx.captured_queries == []


@pytest.mark.django_db
def test_custom_node_id_relation_set_mapping_uses_pipeline_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The batched NodeID mapping recovers the active write pipeline's alias.

    The set decoder cannot thread an alias through its flavor handlers, so the
    batched mapping recovers the pinned alias exactly like the single-id
    primitive: with a pipeline active, the ``__in`` mapping query runs on the
    pipeline alias.
    """

    class AliasBatchNodeType(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert registry.get(Category) is AliasBatchNodeType

    finalize_django_types()
    row = Category.objects.create(name="AliasBatchNode")
    manager = Category._default_manager
    using = mock.Mock(wraps=manager.using)
    monkeypatch.setattr(manager, "using", using)
    with write_pipeline("default", lock=False):
        pks, error = decode_visible_relation_ids(
            [relay.GlobalID("products.category", row.name)],
            graphql_name="categoryIds",
            related_model=Category,
            info=make_info(),
            async_recourse="Use a synchronous visibility hook.",
        )
    assert error is None
    assert pks == [row.pk]
    using.assert_any_call("default")


@pytest.mark.django_db
def test_decode_visible_relation_ids_accepts_duplicate_pks_with_one_query() -> None:
    """Duplicate pks are a subset check, not a count match: the decode keeps the duplicates.

    Live ``test_serializer_m2m_duplicate_alt_branch_pks_still_one_visibility_query``
    unique-attaches on the wire. GraphQL cannot observe that the decoder returns
    ``[a, b, a]`` rather than a set; a len-compare in ``pks_all_present`` would
    still unique-attach.
    """
    first = Category.objects.create(name="DupA")
    second = Category.objects.create(name="DupB")
    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            [saved_pk(first), saved_pk(second), saved_pk(first)],
            graphql_name="categoryIds",
            related_model=Category,
            info=unread_info(),
            async_recourse="Use a synchronous visibility hook.",
        )
    assert error is None
    assert pks == [saved_pk(first), saved_pk(second), saved_pk(first)]
    assert len(ctx.captured_queries) == 1


@pytest.mark.django_db
def test_decode_visible_relation_ids_answers_the_key_a_non_pk_relation_stores() -> None:
    """The ids name rows by pk; the answer is each row's ``key_attname`` value, in input order.

    A relation keyed by a column other than the pk stores that column's value, read
    in the same one visibility query; a visible row whose key is ``NULL`` cannot be
    linked by it and is the uniform field-keyed relation error.
    """
    keyed = NullableScalarSpecimen.objects.create(label="Keyed")
    other = NullableScalarSpecimen.objects.create(label="Other")
    unkeyed = NullableScalarSpecimen.objects.create(label=None)

    def decode(pks: list[object]) -> tuple[list[object] | None, FieldError | None]:
        return decode_visible_relation_ids(
            pks,
            graphql_name="partnerIds",
            related_model=NullableScalarSpecimen,
            info=unread_info(),
            async_recourse="Use a synchronous visibility hook.",
            key_attname="label",
        )

    with CaptureQueriesContext(connection) as ctx:
        keys, error = decode([other.pk, keyed.pk, other.pk])
    assert (keys, error) == (["Other", "Keyed", "Other"], None)
    assert len(ctx.captured_queries) == 1

    keys, error = decode([keyed.pk, unkeyed.pk])
    assert keys is None
    assert error is not None
    assert error.field == "partnerIds"


@pytest.mark.django_db
def test_decode_visible_relation_ids_projects_pks_and_still_refuses_a_null_key() -> None:
    """``project(pk, key)`` answers what the flavor binds; a ``NULL`` key is refused first.

    The serializer's ``PrimaryKeyRelatedField`` resolves pks, so its decoder projects each
    visible row back to its pk; the row set is the one the stored key admits.
    """
    keyed = NullableScalarSpecimen.objects.create(label="Keyed")
    unkeyed = NullableScalarSpecimen.objects.create(label=None)

    def decode(pks: list[object]) -> tuple[list[object] | None, FieldError | None]:
        return decode_visible_relation_ids(
            pks,
            graphql_name="partnerIds",
            related_model=NullableScalarSpecimen,
            info=unread_info(),
            async_recourse="Use a synchronous visibility hook.",
            key_attname="label",
            project=lambda pk, key: (pk, key),
        )

    assert decode([keyed.pk]) == ([(keyed.pk, "Keyed")], None)
    keys, error = decode([keyed.pk, unkeyed.pk])
    assert keys is None
    assert error is not None
    assert error.field == "partnerIds"


@pytest.mark.django_db
@pytest.mark.parametrize("key_attname", [None, "label"])
def test_decode_visible_relation_refuses_a_visible_row_whose_stored_key_is_null(
    key_attname: str | None,
) -> None:
    """The single spine refuses a ``NULL`` stored key whatever the flavor projects.

    With the stored column named, the visible ``label=None`` row is the uniform relation
    error and ``project`` never runs; with no stored column (a pk-keyed relation) the same
    row resolves.
    """
    unkeyed = NullableScalarSpecimen.objects.create(label=None)
    projected: list[object] = []

    def project(obj: Model) -> object:
        projected.append(obj)
        return saved_pk(obj)

    value, error = decode_visible_relation(
        unkeyed.pk,
        graphql_name="partnerId",
        related_model=NullableScalarSpecimen,
        info=unread_info(),
        async_recourse="Use a synchronous visibility hook.",
        skip=lambda candidate: candidate is None,
        project=project,
        key_attname=key_attname,
    )

    if key_attname is None:
        assert (value, error) == (unkeyed.pk, None)
        assert projected == [unkeyed]
    else:
        assert value is None
        assert error is not None
        assert (error.field, error.messages, error.codes) == (
            "partnerId",
            ["Invalid id for relation 'partnerId'."],
            ["invalid"],
        )
        assert projected == []


@pytest.mark.django_db
def test_decode_visible_relation_ids_materializes_generators_once_and_clears_empty() -> None:
    """A one-shot generator container is materialized ONCE; an empty one clears query-free.

    End-to-end over the batch seam: the container is consumed exactly once by
    the materialization (never re-iterated at the decode layer), and a
    generator yielding nothing is a valid M2M clear that returns ``[]``
    WITHOUT touching the DB.
    """
    created = [Category.objects.create(name=f"Gen{i}") for i in range(2)]
    consumed: list[int] = []

    def _one_shot() -> Iterator[int]:
        for item in created:
            consumed.append(saved_pk(item))
            yield saved_pk(item)

    pks, error = decode_visible_relation_ids(
        _one_shot(),
        graphql_name="categoryIds",
        related_model=Category,
        info=unread_info(),
        async_recourse="Use a synchronous visibility hook.",
    )
    assert error is None
    assert pks == [saved_pk(item) for item in created]
    assert consumed == [saved_pk(item) for item in created]

    def _empty() -> Iterator[object]:
        yield from ()

    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            _empty(),
            graphql_name="categoryIds",
            related_model=Category,
            info=unread_info(),
            async_recourse="Use a synchronous visibility hook.",
        )
    assert error is None
    assert pks == []
    assert ctx.captured_queries == []


@pytest.mark.django_db
def test_decode_visible_relation_ids_coercion_and_null_boundaries_stay_contained() -> None:
    """Hostile member shapes collapse to the uniform error or coerce visibly - never raw.

    ``None`` as a MEMBER or as the whole container, an out-of-range int (the
    ``OverflowError`` guard), lexical strings the pk field's ``to_python``
    governs, and bools all either fail the type check into the field-keyed
    ``relation_field_error`` or coerce through the pk field and pass the same
    visibility gate as any other pk - no raw ``TypeError`` / ``ValueError`` /
    ``OverflowError`` escapes the resolver.
    """
    category = Category.objects.create(name="BoundaryTarget")
    recourse = "Use a synchronous visibility hook."

    for bad_container in (None, [None]):
        pks, error = decode_visible_relation_ids(
            bad_container,
            graphql_name="categoryIds",
            related_model=Category,
            info=unread_info(),
            async_recourse=recourse,
        )
        assert pks is None
        assert error is not None
        assert error.field == "categoryIds"

    for member in (
        10**30,
        "",
        "0x10",
        "12.0",
        True,
        False,
    ):
        pks, error = decode_visible_relation_ids(
            [member],
            graphql_name="categoryIds",
            related_model=Category,
            info=unread_info(),
            async_recourse=recourse,
        )
        assert (pks is None) == (error is not None), f"ambiguous decode for {member!r}"
        if error is not None:
            assert error.field == "categoryIds"

    # A string the pk field coerces to a REAL pk passes the same visibility
    # gate as the int literal (to_python mechanics are the documented contract).
    pks, error = decode_visible_relation_ids(
        [str(saved_pk(category))],
        graphql_name="categoryIds",
        related_model=Category,
        info=unread_info(),
        async_recourse=recourse,
    )
    assert error is None
    assert pks == [saved_pk(category)]


def _relation_decoder_never_called(*_args: object, **_kwargs: object) -> NoReturn:
    """A relation decoder the path under test never reaches: any call fails the test."""
    raise AssertionError("the relation decoders must not run")


def test_decode_field_handlers_extra_handlers_override_the_scalar_kind() -> None:
    """``extra_handlers`` entries are FULL handlers and replace the scalar fallback.

    The spread-last map keys by ``spec.kind``, so an override under the scalar
    kind wins over the returned ``scalar_handler`` fallback in
    ``decode_provided_fields`` - the documented serializer nested-override
    shape (its values are ``decoded_into``-composed handlers, not decode pairs).
    """

    @strawberry.input
    class NameInput:
        name: str = "x"

    dest: dict[str, object] = {}

    def custom(spec: InputFieldSpec, value: object) -> None:
        dest[spec.target_name] = f"custom-{value}"

    handlers, _ = decode_field_handlers(
        dest,
        info=unread_info(),
        single=_relation_decoder_never_called,
        multi=_relation_decoder_never_called,
        extra_handlers={SCALAR: custom},
    )
    spec = _spec(attr="name", kind=SCALAR, target="name")
    error = decode_provided_fields(
        [spec],
        NameInput(),
        handlers=handlers,
        scalar_handler=lambda _item, _value: (_ for _ in ()).throw(AssertionError("default ran")),
    )
    assert error is None
    assert dest == {"name": "custom-x"}
