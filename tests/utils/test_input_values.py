"""Tests for the neutral set-input traversal substrate (``utils/input_values.py``).

Dict-vs-dataclass walks, UNSET identity, and base-slot container reads are not
a document. Filter and order input on the wire live in
``examples/fakeshop/test_query/test_library_api.py``.
"""

from collections.abc import Iterator
from typing import NoReturn

import pytest
import strawberry
from django.utils.functional import SimpleLazyObject
from typing_extensions import override

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters.base import RelatedFilter
from django_strawberry_framework.filters.sets import FilterSet
from django_strawberry_framework.utils.input_values import (
    DEFAULT_SET_INPUT_TRAVERSAL_DEPTH,
    LEAF,
    LOGIC,
    RELATED,
    UNSET,
    RelatedDeclarationError,
    SetInputTraversal,
    assert_set_traversal_depth,
    input_field_value,
    is_inactive_value,
    iter_active_fields,
    iter_input_items,
    related_declaration_mapping,
    set_traversal_depth_cap,
)
from django_strawberry_framework.utils.inputs import GeneratedInputFieldSpec
from django_strawberry_framework.utils.typing import object_result
from tests._idioms import ClaimsClass, ClassReadRaises

# ---------------------------------------------------------------------------
# iter_input_items -- dict / dataclass / non-walkable
# ---------------------------------------------------------------------------


def test_iter_input_items_handles_dict_dataclass_and_non_walkable() -> None:
    assert iter_input_items({"a": 1}) == [("a", 1)]
    assert iter_input_items({}) == []
    assert iter_input_items(42) is None

    @strawberry.input
    class _In:
        a: int | None = None

    assert iter_input_items(_In(a=3)) == [("a", 3)]


# ---------------------------------------------------------------------------
# is_inactive_value -- the single active-input rule
# ---------------------------------------------------------------------------


def test_is_inactive_value_is_identity_based_not_truthiness() -> None:
    # ``None`` is always inactive; a configured sentinel collapses too.
    assert is_inactive_value(None) is True
    assert is_inactive_value(None, unset_sentinel=UNSET) is True
    assert is_inactive_value(UNSET, unset_sentinel=UNSET) is True
    # Falsy-but-supplied values stay ACTIVE (identity, not truthiness).
    assert is_inactive_value(0) is False
    assert is_inactive_value("") is False
    assert is_inactive_value(False) is False  # noqa: FBT003 - the bool is the value under test
    # Order semantics (no sentinel configured): UNSET is a normal active value,
    # so the order normalizer never needs to reference ``strawberry.UNSET``.
    assert is_inactive_value(UNSET) is False


# ---------------------------------------------------------------------------
# iter_active_fields -- classification + spec resolution + inactive skip
# ---------------------------------------------------------------------------


def test_iter_active_fields_classifies_and_skips_inactive() -> None:
    related_obj = RelatedFilter("ShelfFilter", field_name="shelf")

    class _Set(FilterSet):
        shelf = related_obj

    specs: dict[tuple[type[FilterSet], str], GeneratedInputFieldSpec] = {
        (_Set, "title"): GeneratedInputFieldSpec("title", "title", "title"),
        (_Set, "shelf"): GeneratedInputFieldSpec("shelf", "shelf", "shelf"),
    }
    config = SetInputTraversal(
        field_specs=specs,
        related_attr="related_filters",
        logic_keys=frozenset({"and_"}),
        unset_sentinel=UNSET,
    )
    fields = list(
        iter_active_fields(
            _Set,
            {
                "title": "x",
                "shelf": {"code": "y"},
                "and_": [{"title": "z"}],
                "skip_none": None,
                "skip_unset": UNSET,
            },
            config,
        ),
    )
    by_attr = {f.python_attr: f for f in fields}
    # ``None`` / ``UNSET`` fields are dropped entirely.
    assert set(by_attr) == {"title", "shelf", "and_"}
    # Leaf: spec resolved, no related_obj.
    assert by_attr["title"].kind == LEAF
    assert by_attr["title"].spec is not None
    assert by_attr["title"].spec.django_source_path == "title"
    assert by_attr["title"].related_obj is None
    # Related: spec resolved AND the declared related object carried through.
    assert by_attr["shelf"].kind == RELATED
    assert by_attr["shelf"].spec is not None
    assert by_attr["shelf"].spec.django_source_path == "shelf"
    assert by_attr["shelf"].related_obj is related_obj
    assert by_attr["shelf"].raw_value == {"code": "y"}
    # Logic: marked LOGIC; spec is None (no field-spec entry for an operator key).
    assert by_attr["and_"].kind == LOGIC
    assert by_attr["and_"].spec is None


def test_iter_active_fields_dict_and_dataclass_classify_identically() -> None:
    """The dataclass and raw-dict shapes yield the same records."""

    class _Set:
        related_filters = {"shelf": object()}

    @strawberry.input
    class _In:
        title: str | None = None
        shelf: strawberry.scalars.JSON | None = None

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_filters",
        unset_sentinel=UNSET,
    )
    dataclass_view = [
        (f.python_attr, f.kind)
        for f in iter_active_fields(
            _Set,
            _In(title="x", shelf=strawberry.scalars.JSON({"code": 1})),
            config,
        )
    ]
    dict_view = [
        (f.python_attr, f.kind)
        for f in iter_active_fields(_Set, {"title": "x", "shelf": {"code": 1}}, config)
    ]
    assert dataclass_view == dict_view == [("title", LEAF), ("shelf", RELATED)]


def test_iter_active_fields_flattens_top_level_list_only_when_configured() -> None:
    class _Set:
        related_orders = {}

    with_list = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    fields = list(iter_active_fields(_Set, [{"title": "a"}, {"subtitle": "b"}], with_list))
    assert [(f.python_attr, f.kind) for f in fields] == [("title", LEAF), ("subtitle", LEAF)]

    # Without the flag a bare list is non-walkable (no dict / dataclass shape)
    # so nothing is yielded -- the filter side, which never sends a top-level
    # list, relies on this.
    no_list = SetInputTraversal(field_specs={}, related_attr="related_orders")
    assert list(iter_active_fields(_Set, [{"title": "a"}], no_list)) == []


def test_iter_active_fields_inactive_or_non_walkable_top_level_yields_nothing() -> None:
    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        unset_sentinel=UNSET,
    )
    assert list(iter_active_fields(_Set, None, config)) == []
    assert list(iter_active_fields(_Set, UNSET, config)) == []
    assert list(iter_active_fields(_Set, 42, config)) == []


def test_dict_subclass_overrides_cannot_replace_the_shared_walk() -> None:
    """The traversal uses the real dict operations, not consumer overrides."""

    class _HostileDict(dict[str, object]):
        @override
        def items(self) -> NoReturn:
            raise RuntimeError("hostile items")

        @override
        def get(self, key: str, default: object = None) -> NoReturn:
            raise RuntimeError("hostile get")

    value = _HostileDict(name="x")
    assert iter_input_items(value) == [("name", "x")]
    assert input_field_value(value, "name") == "x"


def test_non_string_input_keys_fail_closed_before_permission_dispatch() -> None:
    """Input field names must be strings; a non-string key is refused at the walk."""
    with pytest.raises(ConfigurationError, match="field names must be strings"):
        iter_input_items({1: "unexpected"})


def test_hostile_list_iteration_cannot_escape_the_order_walk() -> None:
    """The top-level-list walk reads real list elements, not a subclass iterator."""

    class _HostileList(list[object]):
        @override
        def __iter__(self) -> Iterator[object]:
            raise RuntimeError("hostile list iterator")

    class _Set:
        related_orders = {}

    value = _HostileList([{"title": "x"}])
    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    fields = list(iter_active_fields(_Set, value, config))
    assert [(field.python_attr, field.raw_value) for field in fields] == [("title", "x")]


def test_nested_order_lists_fail_closed_instead_of_recursing_or_no_oping() -> None:
    """A list element must be a mapping or dataclass; a nested list is rejected."""

    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    with pytest.raises(ConfigurationError, match="list elements must be mapping or dataclass"):
        list(iter_active_fields(_Set, [[{"title": "x"}]], config))


def test_dataclass_metadata_must_be_a_mapping() -> None:
    """``__dataclass_fields__`` that is not a mapping is a typed traversal error."""

    class _NotAMapping:
        __dataclass_fields__ = ("name",)

    with pytest.raises(ConfigurationError) as excinfo:
        iter_input_items(_NotAMapping())
    assert str(excinfo.value) == (
        "Could not traverse set input of type _NotAMapping: its dataclass metadata is not a "
        "mapping."
    )


def test_dataclass_and_object_field_read_failures_propagate() -> None:
    """A field value read is consumer code; what it raises reaches the caller unchanged."""

    class _UnreadableDataclass:
        __dataclass_fields__ = {"name": object()}

        @property
        def name(self) -> NoReturn:
            raise RuntimeError("hostile dataclass field")

    class _UnreadableObject:
        @override
        def __getattribute__(self, name: str) -> object:
            if name == "name":
                raise RuntimeError("hostile object field")
            return object_result(super().__getattribute__, name)

    with pytest.raises(RuntimeError, match="hostile dataclass field"):
        iter_input_items(_UnreadableDataclass())
    with pytest.raises(RuntimeError, match="hostile object field"):
        input_field_value(_UnreadableObject(), "name")


def test_active_field_configuration_reads_propagate_and_related_reads_are_truthful() -> None:
    """A raising traversal config propagates; a metaclass hook never runs on the related read."""

    class _UnreadableConfig:
        @property
        def handle_top_level_list(self) -> NoReturn:
            raise RuntimeError("hostile traversal config")

        unset_sentinel = None

    class _UnreadableSentinelConfig:
        @property
        def unset_sentinel(self) -> NoReturn:
            raise RuntimeError("hostile unset_sentinel")

        handle_top_level_list = False

    class _HostileSetMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "related_orders":
                raise RuntimeError("hostile related declarations")
            return object_result(super().__getattribute__, name)

    class _UnreadableSet(metaclass=_HostileSetMeta):
        pass

    with pytest.raises(RuntimeError, match="hostile traversal config"):
        # basedpyright: each unreadable traversal config is the hostile input under test;
        # iter_active_fields types the parameter as SetInputTraversal
        list(iter_active_fields(object, {"name": "x"}, _UnreadableConfig()))  # pyright: ignore[reportArgumentType]
    with pytest.raises(RuntimeError, match="hostile unset_sentinel"):
        # basedpyright: each unreadable traversal config is the hostile input under test;
        # iter_active_fields types the parameter as SetInputTraversal
        list(iter_active_fields(object, {"name": "x"}, _UnreadableSentinelConfig()))  # pyright: ignore[reportArgumentType]

    config = SetInputTraversal(field_specs={}, related_attr="related_orders")
    fields = list(iter_active_fields(_UnreadableSet, {"name": "x"}, config))
    assert [(field.python_attr, field.kind) for field in fields] == [("name", LEAF)]


def test_active_field_related_declarations_must_be_a_mapping() -> None:
    """Non-mapping related declarations abort the walk with a typed error."""

    class _InvalidSet:
        related_orders = []

    config = SetInputTraversal(field_specs={}, related_attr="related_orders")
    with pytest.raises(ConfigurationError, match="declarations are not a mapping"):
        list(iter_active_fields(_InvalidSet, {"name": "x"}, config))


def test_active_field_list_skips_inactive_elements_and_accepts_none_related_mapping() -> None:
    """Inactive list elements are dropped; an absent related mapping leaves every field a leaf."""

    class _Set:
        related_orders = None

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )

    fields = list(iter_active_fields(_Set, [None, {"name": "x"}], config))

    assert [(field.python_attr, field.kind) for field in fields] == [("name", LEAF)]


def test_input_field_value_reads_dict_and_dataclass_fields() -> None:
    """``input_field_value`` reads single fields or returns None for missing fields/non-walkable inputs."""
    assert input_field_value({"a": 10}, "a") == 10
    assert input_field_value({"a": 10}, "missing") is None
    assert input_field_value(None, "a") is None
    assert input_field_value(42, "a") is None

    @strawberry.input
    class _In:
        title: str = "item"

    assert input_field_value(_In(), "title") == "item"
    assert input_field_value(_In(), "missing") is None


def test_field_name_bypasses_hostile_str_subclass_str_override() -> None:
    """``_field_name`` safely normalizes string subclass keys without calling overridden __str__."""

    class _HostileStr(str):
        @override
        def __str__(self) -> str:
            raise RuntimeError("hostile __str__ override")

    key = _HostileStr("field_name")
    assert iter_input_items({key: "value"}) == [("field_name", "value")]
    assert input_field_value({key: "value"}, key) == "value"


_FIELD_NAME_REFUSAL = (
    "Set input field names must be strings; received an invalid field name in an input of "
    "type dict."
)


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(ClassReadRaises(RuntimeError), id="raising-class"),
        pytest.param(ClassReadRaises(KeyboardInterrupt), id="raising-class-interrupt"),
        pytest.param(ClaimsClass(str), id="claims-str"),
        pytest.param(SimpleLazyObject(lambda: "field_name"), id="lazy-proxy-of-str"),
    ],
)
def test_field_name_asks_the_real_type_and_refuses_a_key_that_is_not_one(key: object) -> None:
    """A key that only claims ``str`` (or whose class read raises) is the typed refusal.

    ``str.__str__`` accepts only a real ``str``, so a ``__class__``-based answer lets the
    key through the check and into a raw ``TypeError`` / the key's own exception. Both
    entry points share the check.
    """
    with pytest.raises(ConfigurationError) as walk:
        iter_input_items({key: "value"})
    assert str(walk.value) == _FIELD_NAME_REFUSAL
    with pytest.raises(ConfigurationError) as single:
        # basedpyright: the key is the hostile non-``str`` input under test; the parameter is typed
        # ``str``
        input_field_value({"field_name": "value"}, key)  # pyright: ignore[reportArgumentType]
    assert str(single.value) == _FIELD_NAME_REFUSAL


def test_order_list_elements_reject_primitive_values() -> None:
    """When handle_top_level_list is True, non-mapping list elements raise ConfigurationError."""

    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    with pytest.raises(
        ConfigurationError,
        match="Order input list elements must be mapping or dataclass values",
    ):
        list(iter_active_fields(_Set, ["string_element"], config))

    with pytest.raises(
        ConfigurationError,
        match="Order input list elements must be mapping or dataclass values",
    ):
        list(iter_active_fields(_Set, [123], config))


def test_default_set_input_traversal_depth() -> None:
    """DEFAULT_SET_INPUT_TRAVERSAL_DEPTH provides a neutral recursion ceiling across set families."""
    assert DEFAULT_SET_INPUT_TRAVERSAL_DEPTH == 8
    assert FilterSet._MAX_LOGIC_DEPTH == DEFAULT_SET_INPUT_TRAVERSAL_DEPTH


# ---------------------------------------------------------------------------
# related_declaration_mapping -- the shared related-declaration front half
# ---------------------------------------------------------------------------


def test_related_declaration_mapping_treats_absent_and_none_as_no_declarations() -> None:
    """An absent or explicitly-``None`` declaration is "no related fields", not an error."""

    class _Absent:
        pass

    class _None:
        related_orders = None

    marker = {"shelf": object()}

    class _Mapping:
        related_orders = marker

    assert related_declaration_mapping(_Absent, "related_orders") == {}
    assert related_declaration_mapping(_None, "related_orders") == {}
    assert related_declaration_mapping(_Mapping, "related_orders") is marker


@pytest.mark.parametrize(
    "bad",
    [
        list[object](),
        42,
        "nope",
        {"a": 1}.keys(),
        set[object](),
    ],
)
def test_related_declaration_mapping_rejects_non_mappings(bad: object) -> None:
    """A present declaration that is not a Mapping is rejected before any indexing."""

    class _Set:
        related_orders = bad

    with pytest.raises(RelatedDeclarationError) as excinfo:
        related_declaration_mapping(_Set, "related_orders")
    assert excinfo.value.kind == "not_mapping"


def test_related_declaration_mapping_never_runs_a_metaclass_getattribute() -> None:
    """The declaration is read from the class's real namespaces, so a hostile hook never runs.

    A metaclass ``__getattribute__`` that raises for the attribute is not consulted: the
    class declares nothing under that name, so it has no related fields.
    """

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "related_orders":
                raise RuntimeError("hostile class read")
            return object_result(super().__getattribute__, name)

    class _Set(metaclass=_HostileMeta):
        pass

    assert related_declaration_mapping(_Set, "related_orders") == {}


def test_iter_active_fields_propagates_a_hostile_config_related_attr_read() -> None:
    """The traversal config's attribute NAME read is consumer code; what it raises propagates.

    The config is a public dataclass a test double may replace; its ``related_attr``
    property's exception reaches the caller unchanged, like any other consumer hook's.
    """

    class _HostileConfig:
        unset_sentinel = UNSET
        handle_top_level_list = False

        @property
        def related_attr(self) -> NoReturn:
            raise RuntimeError("hostile config related_attr")

    with pytest.raises(RuntimeError, match="hostile config related_attr"):
        # basedpyright: the config whose related_attr raises is the hostile input under test;
        # iter_active_fields types the parameter as SetInputTraversal
        list(iter_active_fields(object, {"name": "x"}, _HostileConfig()))  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# Depth-cap helpers -- one budget, shared sentence, defensive label read
# ---------------------------------------------------------------------------


def test_set_traversal_depth_cap_resolves_the_family_budget() -> None:
    """A declared int knob is honored; absent/None/non-int knobs take the neutral default."""

    class _OrderLike:
        pass

    class _NoneKnob:
        _MAX_LOGIC_DEPTH = None

    class _Raised:
        _MAX_LOGIC_DEPTH = 12

    class _Garbage:
        _MAX_LOGIC_DEPTH = "10"

    assert set_traversal_depth_cap(_OrderLike) == DEFAULT_SET_INPUT_TRAVERSAL_DEPTH
    assert set_traversal_depth_cap(_NoneKnob) == DEFAULT_SET_INPUT_TRAVERSAL_DEPTH
    assert set_traversal_depth_cap(_Raised) == 12
    assert set_traversal_depth_cap(_Garbage) == DEFAULT_SET_INPUT_TRAVERSAL_DEPTH


def test_assert_set_traversal_depth_enforces_the_declared_budget() -> None:
    """Depths within budget pass silently; past budget raises the shared typed sentence."""

    class _Set:
        _MAX_LOGIC_DEPTH = 4

    assert_set_traversal_depth(_Set, 4, branch="related-branch", input_noun="related")
    with pytest.raises(ConfigurationError) as excinfo:
        assert_set_traversal_depth(_Set, 5, branch="related-branch", input_noun="related")
    assert str(excinfo.value) == (
        "test_assert_set_traversal_depth_enforces_the_declared_budget.<locals>._Set: "
        "related-branch nesting exceeded _MAX_LOGIC_DEPTH=4. Flatten the related input or "
        "split into multiple queries."
    )


def test_assert_set_traversal_depth_words_knobless_sets_with_the_default_sentence() -> None:
    """A set with no ``_MAX_LOGIC_DEPTH`` knob is capped at the neutral default."""

    class _OrderLike:
        pass

    with pytest.raises(
        ConfigurationError,
        match="nesting exceeded the maximum traversal depth \\(8\\)",
    ):
        assert_set_traversal_depth(
            _OrderLike,
            DEFAULT_SET_INPUT_TRAVERSAL_DEPTH + 1,
            branch="related-branch",
            input_noun="related",
        )


@pytest.mark.parametrize("subject", ["", "FilterSet"])
def test_depth_cap_error_label_survives_a_str_subclass_qualname(subject: str) -> None:
    """A walk that decided to fail names the class through the base ``str`` slot.

    The ``str`` subclass overrides ``__str__`` and ``__format__`` to raise, so a label
    interpolated as-is replaces the typed depth error with the consumer's exception.
    """

    class _HostileQualname(str):
        @override
        def __str__(self) -> str:
            raise RuntimeError("hostile qualname __str__")

        @override
        def __format__(self, format_spec: str) -> str:
            raise RuntimeError("hostile qualname __format__")

    class _Set:
        _MAX_LOGIC_DEPTH = 1

    _Set.__qualname__ = _HostileQualname("Hostile.Set")
    with pytest.raises(ConfigurationError) as excinfo:
        assert_set_traversal_depth(
            _Set,
            2,
            branch="logical-branch",
            input_noun="filter",
            subject=subject,
        )
    label = f"{subject} Hostile.Set" if subject else "Hostile.Set"
    assert str(excinfo.value) == (
        f"{label}: logical-branch nesting exceeded _MAX_LOGIC_DEPTH=1. Flatten the "
        "filter input or split into multiple queries."
    )


@pytest.mark.parametrize("raised", [RuntimeError, KeyboardInterrupt])
def test_depth_cap_error_label_survives_a_qualname_whose_class_read_raises(
    raised: type[BaseException],
) -> None:
    """The label is the interpreter's qualname: the metaclass's ``__qualname__`` answer never runs."""

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__qualname__":
                return ClassReadRaises(raised)
            return object_result(super().__getattribute__, name)

    class _Set(metaclass=_HostileMeta):
        _MAX_LOGIC_DEPTH = 1

    with pytest.raises(ConfigurationError) as excinfo:
        assert_set_traversal_depth(_Set, 2, branch="logical-branch", input_noun="filter")
    assert str(excinfo.value) == (
        "test_depth_cap_error_label_survives_a_qualname_whose_class_read_raises.<locals>._Set: "
        "logical-branch nesting exceeded _MAX_LOGIC_DEPTH=1. Flatten the "
        "filter input or split into multiple queries."
    )


def test_depth_cap_error_label_reads_qualname_defensively() -> None:
    """A hostile ``__qualname__`` hook never runs: the label is read from the interpreter."""

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__qualname__":
                raise RuntimeError("hostile qualname")
            return object_result(super().__getattribute__, name)

    class _Set(metaclass=_HostileMeta):
        _MAX_LOGIC_DEPTH = 1

    with pytest.raises(ConfigurationError) as excinfo:
        assert_set_traversal_depth(_Set, 2, branch="related-branch", input_noun="related")
    assert "hostile qualname" not in str(excinfo.value)
    assert "nesting exceeded" in str(excinfo.value)
