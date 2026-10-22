"""Tests for input permissions, relation-path gates, and Django/Channels request decoding.

Channels scope adapters and hostile ``info.context`` reads have no HTTP mount
(fakeshop has no ASGI/WS). Filter/order permission dispatch on the wire lives in
``examples/fakeshop/test_query/test_products_api.py`` and
``examples/fakeshop/test_query/test_library_api.py``.
"""

from collections.abc import Callable
from typing import NoReturn

import pytest
import pytest_django
import strawberry
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.http import HttpRequest
from django.test import modify_settings
from graphql import GraphQLError
from typing_extensions import override

import django_strawberry_framework.utils.permissions as perm
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.sets_mixins import ActiveInputPermissionMixin
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.permissions import (
    ChannelsRequestAdapter,
    _channels_request_adapter,
    _fire_flat_relation_path_gates,
    _related_declarations,
    _request_from_context,
    _safe_get_model,
    active_permission_targets,
    active_related_branches,
    auth_aliases_for_permission_classes,
    extract_branch_value,
    invoke_permission_method,
    iter_input_items,
    request_from_info,
    resolve_auth_aliases,
    run_active_input_permission_checks,
    walk_declared_relation_path,
)
from django_strawberry_framework.utils.querysets import SyncMisuseError
from django_strawberry_framework.utils.typing import object_result

# ---------------------------------------------------------------------------
# request_from_info -- family-labelled, shape-tolerant
# ---------------------------------------------------------------------------


class _Ctx:
    def __init__(self, request: object) -> None:
        self.request = request


@pytest.mark.parametrize("family_label", ["FilterSet", "OrderSet"])
def test_request_from_info_resolves_and_names_family(family_label: str) -> None:
    """Every ordinary Django request context resolves; bad shapes name the family."""
    request = HttpRequest()
    info_with_request = type("Info", (), {"context": _Ctx(request)})()
    assert request_from_info(info_with_request, family_label=family_label) is request

    info_bare = type("Info", (), {"context": request})()
    assert request_from_info(info_bare, family_label=family_label) is request

    info_mapping = type("Info", (), {"context": {"request": request}})()
    assert request_from_info(info_mapping, family_label=family_label) is request

    info_no_ctx = type("Info", (), {"context": None})()
    with pytest.raises(ConfigurationError, match=f"{family_label} requires"):
        request_from_info(info_no_ctx, family_label=family_label)

    info_bad = type("Info", (), {"context": object()})()
    with pytest.raises(ConfigurationError, match=f"{family_label} could not resolve"):
        request_from_info(info_bad, family_label=family_label)


# ---------------------------------------------------------------------------
# request_from_info -- the Strawberry-Channels mapping context (spec-041
# Decision 11). Duck-typed fakes only: this branch must work (and be testable)
# with no ``channels`` import anywhere in the helper.
# ---------------------------------------------------------------------------


class _FakeConsumer:
    def __init__(self, scope: object) -> None:
        self.scope = scope


class _FakeChannelsRequest:
    """The ``ChannelsRequest`` duck shape: ``consumer`` + ``body`` + request attrs."""

    def __init__(self, scope: object) -> None:
        self.consumer = _FakeConsumer(scope)
        self.body = b'{"query": "{ ping }"}'
        self.method = "POST"
        self.headers = {"content-type": "application/json"}


class _FakeInfo:
    """The ``info`` duck shape ``request_from_info`` reads: only ``context``."""

    def __init__(self, context: dict[str, object]) -> None:
        self.context = context


def _channels_info(scope: object) -> _FakeInfo:
    return _FakeInfo({"request": _FakeChannelsRequest(scope), "response": object()})


def test_channels_context_resolves_to_a_wrapping_adapter() -> None:
    """The mapping context resolves; ``.user`` / ``.session`` / ``.scope`` come from the scope."""
    user, session = object(), object()
    scope = {"user": user, "session": session, "type": "http"}
    adapter = request_from_info(_channels_info(scope), family_label="FilterSet")
    assert isinstance(adapter, ChannelsRequestAdapter)
    assert adapter.user is user
    assert adapter.session is session
    assert adapter.scope is scope


def test_channels_adapter_delegates_unknown_attributes_to_the_wrapped_request() -> None:
    """Non-scope attributes fall through to the original ``ChannelsRequest``."""
    scope = {"user": object()}
    info = _channels_info(scope)
    adapter = request_from_info(info, family_label="OrderSet")
    assert isinstance(adapter, ChannelsRequestAdapter)
    wrapped = info.context["request"]
    assert isinstance(wrapped, _FakeChannelsRequest)
    assert adapter.method == "POST"
    assert adapter.headers is wrapped.headers
    assert adapter.consumer is wrapped.consumer
    assert adapter.body == wrapped.body
    # A genuinely missing attribute is a normal AttributeError, not a swallow.
    with pytest.raises(AttributeError):
        _ = adapter.definitely_not_a_request_attribute


def test_channels_adapter_scope_fields_default_to_none_when_middleware_absent() -> None:
    """No ``AuthMiddlewareStack`` in the stack: ``.user`` / ``.session`` are ``None``, not errors."""
    adapter = request_from_info(_channels_info({"type": "http"}), family_label="FilterSet")
    assert isinstance(adapter, ChannelsRequestAdapter)
    assert adapter.user is None
    assert adapter.session is None


def test_channels_adapter_supports_permission_hooks_reading_both_kinds_of_attribute() -> None:
    """A consumer-style gate reading one scope-backed and one delegated attribute succeeds."""
    user = object()
    adapter = request_from_info(_channels_info({"user": user}), family_label="FilterSet")

    seen = {}

    class _Gate:
        def check_name_permission(self, request: ChannelsRequestAdapter) -> None:
            seen["user"] = request.user  # scope-backed
            seen["method"] = request.method  # delegated to the wrapped request

    invoke_permission_method(_Gate(), "name", adapter)
    assert seen == {"user": user, "method": "POST"}


@pytest.mark.parametrize(
    "context",
    [
        {"request": object()},  # no ``consumer.scope`` duck shape
        {"response": object()},  # no ``request`` key at all
        {"request": None},
        {},
    ],
)
def test_non_channels_mapping_shapes_still_raise_the_family_labelled_error(
    context: dict[str, object],
) -> None:
    """Mapping contexts that are not Channels-shaped keep the final ``ConfigurationError``."""
    info = type("Info", (), {"context": context})()
    with pytest.raises(ConfigurationError, match="FilterSet could not resolve"):
        request_from_info(info, family_label="FilterSet")


def test_non_mapping_scope_is_not_recognized_as_channels() -> None:
    """A ``consumer.scope`` that is not a mapping falls through to the final error."""
    request = _FakeChannelsRequest({})
    request.consumer.scope = ["not", "a", "mapping"]
    info = type("Info", (), {"context": {"request": request}})()
    with pytest.raises(ConfigurationError, match="OrderSet could not resolve"):
        request_from_info(info, family_label="OrderSet")


# ---------------------------------------------------------------------------
# request_from_info -- Strawberry's WebSocket context puts the consumer itself
# at context["request"], so its ASGI scope is direct at request.scope.
# ---------------------------------------------------------------------------


class _FakeWSConsumer:
    """The ``GraphQLWSConsumer`` duck shape: the consumer is the request."""

    def __init__(self, scope: object) -> None:
        self.scope = scope
        self.channel_name = "specific..inmemory!probe"


def _channels_ws_info(scope: object) -> _FakeInfo:
    consumer = _FakeWSConsumer(scope)
    return _FakeInfo({"request": consumer, "ws": consumer})


def test_channels_websocket_context_resolves_to_a_wrapping_adapter() -> None:
    """Direct scope fields resolve and other consumer attributes still delegate."""
    user, session = object(), object()
    scope = {"user": user, "session": session, "type": "websocket"}
    adapter = request_from_info(_channels_ws_info(scope), family_label="FilterSet")
    assert isinstance(adapter, ChannelsRequestAdapter)
    assert adapter.user is user
    assert adapter.session is session
    assert adapter.scope is scope
    assert adapter.channel_name == "specific..inmemory!probe"


def test_channels_websocket_scope_fields_default_to_none_when_middleware_absent() -> None:
    """A WS scope with no ``user`` key -> ``.user`` / ``.session`` are ``None``, not errors."""
    adapter = request_from_info(
        _channels_ws_info({"type": "websocket"}),
        family_label="OrderSet",
    )
    assert isinstance(adapter, ChannelsRequestAdapter)
    assert adapter.user is None
    assert adapter.session is None


def test_non_mapping_websocket_scope_is_not_recognized_as_channels() -> None:
    """A direct WebSocket scope must still be a mapping."""
    info = _channels_ws_info(["not", "a", "mapping"])
    with pytest.raises(ConfigurationError, match="OrderSet could not resolve"):
        request_from_info(info, family_label="OrderSet")


def test_mapping_request_must_be_a_django_request_or_channels_context() -> None:
    """A mapping's arbitrary ``request`` value must not bypass request validation."""

    class _Context(dict[str, object]):
        pass

    info = type("Info", (), {"context": _Context(request=object())})()
    with pytest.raises(ConfigurationError, match="OrderSet could not resolve"):
        request_from_info(info, family_label="OrderSet")


def test_request_like_attribute_context_remains_supported() -> None:
    """Non-mapping wrappers may carry the request-like object used by mutation hooks."""
    request = object()
    context = type("Context", (), {"request": request})()
    info = type("Info", (), {"context": context})()
    assert request_from_info(info, family_label="DjangoMutation") is request


def test_info_context_descriptor_error_propagates() -> None:
    """A consumer ``info.context`` descriptor's own exception propagates unchanged."""

    class _Info:
        @property
        def context(self) -> NoReturn:
            raise RuntimeError("context descriptor exploded")

    with pytest.raises(RuntimeError, match="context descriptor exploded"):
        request_from_info(_Info(), family_label="FilterSet")


def test_unresolvable_request_context_message_is_pinned() -> None:
    """The unresolvable-context rejection names the context's real class."""
    info = type("Info", (), {"context": object()})()
    with pytest.raises(ConfigurationError) as excinfo:
        request_from_info(info, family_label="FilterSet")
    assert str(excinfo.value) == (
        "FilterSet could not resolve a Django HttpRequest from `info.context` "
        "(got object). Expected `info.context.request`, a bare "
        "HttpRequest, a mapping whose `request` is an HttpRequest, or a Strawberry "
        "Channels mapping context whose `request` carries an ASGI scope "
        '(`context["request"].consumer.scope` for the HTTP consumer, '
        '`context["request"].scope` for the WebSocket consumer).'
    )


# ---------------------------------------------------------------------------
# iter_input_items / extract_branch_value
# ---------------------------------------------------------------------------


def test_iter_input_items_handles_dict_dataclass_and_non_walkable() -> None:
    assert iter_input_items({"a": 1}) == [("a", 1)]
    assert iter_input_items(42) is None

    @strawberry.input
    class _In:
        a: int | None = None

    assert iter_input_items(_In(a=3)) == [("a", 3)]


def test_extract_branch_value_collapses_only_the_configured_sentinel() -> None:
    """The order side (default ``unset_sentinel=None``) leaves UNSET intact; filter collapses it."""
    holder = {"branch": UNSET, "real": 5}
    # No sentinel configured (order semantics): UNSET passes through unchanged.
    assert extract_branch_value(holder, "branch") is UNSET
    # Filter semantics: UNSET collapses to None ("branch not supplied").
    assert extract_branch_value(holder, "branch", unset_sentinel=UNSET) is None
    assert extract_branch_value(holder, "real", unset_sentinel=UNSET) == 5
    assert extract_branch_value(None, "branch") is None


# ---------------------------------------------------------------------------
# invoke_permission_method -- fire + dedup
# ---------------------------------------------------------------------------


def test_invoke_permission_method_fires_once_and_dedupes() -> None:
    calls: list[str] = []

    class _Bare:
        def check_name_permission(self, _request: object) -> None:
            calls.append("name")

    fired: set[str] = set()
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert calls == ["name"]
    # A field with no matching method is a silent no-op.
    invoke_permission_method(_Bare(), "absent", HttpRequest(), fired=fired)
    assert calls == ["name"]


def test_invoke_permission_method_rejects_an_async_gate_instead_of_silently_allowing() -> None:
    """An ``async def`` permission gate raises ``SyncMisuseError``, never a silent allow."""
    denied: list[str] = []

    class _Bare:
        async def check_name_permission(self, _request: object) -> NoReturn:
            # Would DENY, but as an ``async def`` it can never run under the sync
            # permission pass; the guard must reject the coroutine, not treat it as
            # a truthy success.
            denied.append("should-not-fire-but-must-not-be-silently-allowed")
            raise AssertionError("async gate body reached in a sync context")

    with pytest.raises(SyncMisuseError, match="check_name_permission returned a coroutine"):
        invoke_permission_method(_Bare(), "name", HttpRequest())

    # The coroutine was closed by the guard, never awaited, and its body never ran.
    assert denied == []


def test_invoke_permission_method_passes_a_normal_sync_return_through() -> None:
    """A plain sync gate returning ``None`` (the documented shape) is unaffected by the guard."""
    fired: set[str] = set()

    class _Bare:
        def check_name_permission(self, _request: object) -> None:
            return None

    # No raise, and the fire is recorded for the dedup set.
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert "check_name_permission" in fired


def test_invoke_permission_method_rejects_a_non_callable_gate_slot() -> None:
    """A DECLARED non-callable gate is a ConfigurationError, never a silent skip.

    A bare ``callable()`` probe treated ``check_name_permission = 42`` exactly
    like an absent gate: the intended gate never ran and nothing signaled -- the
    same authorization no-op the async-gate guard closes. Misconfiguration on a
    permission seam fails loud instead.
    """
    fired: set[str] = set()

    class _Bare:
        check_name_permission = 42  # a misconfigured, non-callable gate slot

    with pytest.raises(
        ConfigurationError,
        match=r"_Bare permission gate 'check_name_permission' must be callable",
    ):
        invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert fired == set()

    # The full walk reaches the same guard through the family dispatch.
    class _DuckRelated:
        pass

    class _Set(ActiveInputPermissionMixin):
        check_name_permission = "not-a-callable"

        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            return ["name"], [("duck", _DuckRelated(), {"x": 1})]

        @override
        @staticmethod
        def _invoke_permission_method(
            bare_instance: ActiveInputPermissionMixin,
            field_path: str,
            request: object,
            *,
            fired: set[str] | None = None,
        ) -> None:
            invoke_permission_method(bare_instance, field_path, request, fired=fired)

    # ``bare`` must be an instance of the set class (the mixin's
    # ``object.__new__(cls)`` contract) for the class-declared gate slot to be
    # visible through instance attribute access.
    with pytest.raises(ConfigurationError, match="must be callable"):
        run_active_input_permission_checks(
            _Set,
            {"name": "x"},
            HttpRequest(),
            fired={},
            bare=object.__new__(_Set),
            target_attr="filterset",
            related_attr="related_filters",
        )


def test_invoke_permission_method_propagates_a_gate_descriptor_error() -> None:
    """The gate slot is the consumer class's own attribute: its exception propagates."""

    class _GateSet:
        @property
        def check_name_permission(self) -> NoReturn:
            raise RuntimeError("gate descriptor exploded")

    with pytest.raises(RuntimeError, match="gate descriptor exploded"):
        invoke_permission_method(_GateSet(), "name", HttpRequest())


def test_invoke_permission_method_treats_a_none_slot_as_absent() -> None:
    """``check_name_permission = None`` stays a silent no-op (indistinguishable from absent)."""

    class _Bare:
        check_name_permission = None

    fired: set[str] = set()
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert fired == set()


def _returning_gate(result: object, calls: list[object]) -> Callable[[object, object], object]:
    def _check(_self: object, _request: object) -> object:
        calls.append(result)
        return result

    return _check


@pytest.mark.parametrize(
    "result",
    [
        False,
        0,
        0.0,
        "",
        [],
        "yes",
        1,
        object(),
    ],
    ids=[
        "false",
        "zero",
        "zero-float",
        "empty-str",
        "empty-list",
        "truthy-str",
        "one",
        "object",
    ],
)
def test_invoke_permission_method_denies_on_any_return_but_none_or_true(result: object) -> None:
    """A gate allows only by returning ``None`` or ``True``; every other return denies.

    A DRF-style ``return user.is_staff`` must never read as an allow, and a
    truthy non-bool is not an explicit allow either: the read fails closed with
    the plain ``GraphQLError`` a raising gate produces. The denied gate is not
    recorded in the dedup set, so a later fire in the same request runs it again.
    """
    calls: list[object] = []

    class _Bare:
        check_name_permission = _returning_gate(result, calls)

    fired: set[str] = set()
    for _ in range(2):
        with pytest.raises(GraphQLError, match=r"^Not authorized to use name on _Bare\.$") as exc:
            invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
        assert exc.value.extensions == {}
    assert fired == set()
    assert len(calls) == 2


@pytest.mark.parametrize("result", [None, True], ids=["none", "true"])
def test_invoke_permission_method_allows_on_none_or_true(result: object) -> None:
    """``None`` (the raise-to-deny form's fall-through) and ``True`` both allow and are recorded."""
    calls: list[object] = []

    class _Bare:
        check_name_permission = _returning_gate(result, calls)

    fired: set[str] = set()
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert fired == {"check_name_permission"}
    assert calls == [result]


@pytest.mark.parametrize("result", [None, True, False], ids=["none", "true", "false"])
def test_invoke_permission_method_rejects_an_async_gate_whatever_it_would_return(
    result: object,
) -> None:
    """An ``async def`` gate is refused before its result is read, allow or deny alike.

    The pass is synchronous, so the coroutine is never awaited: no awaited value
    can allow, and the gate is not recorded as fired.
    """
    ran: list[object] = []

    class _Bare:
        async def check_name_permission(self, _request: object) -> object:
            ran.append(result)
            return result

    fired: set[str] = set()
    with pytest.raises(SyncMisuseError, match="check_name_permission returned a coroutine"):
        invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert ran == []
    assert fired == set()


def test_flat_relation_path_gate_denies_on_a_false_return() -> None:
    """A flat path stops at the first returned denial; the denied gate is not recorded.

    ``category__name`` fires ``Item.check_category_permission`` (allows with
    ``True``) and then ``Category.check_name_permission``, which returns
    ``False`` and denies.
    """
    calls: list[object] = []

    class Category:
        check_name_permission = _returning_gate(result=False, calls=calls)

    class Item(ActiveInputPermissionMixin):
        related_filters = {"category": _Rel("category", Category, target_attr="filterset")}
        check_category_permission = _returning_gate(result=True, calls=calls)

    fired: dict[type[object], set[str]] = {}
    with pytest.raises(GraphQLError, match="Not authorized to use name on Category"):
        _fire_flat_relation_path_gates(
            Item,
            "category__name",
            HttpRequest(),
            fired=fired,
            related_attr="related_filters",
            target_attr="filterset",
        )
    assert calls == [True, False]
    assert fired[Item] == {"check_category_permission"}
    assert fired[Category] == set()


def test_nested_branch_gate_denies_on_a_false_return() -> None:
    """A parent per-branch gate returning ``False`` denies the nested branch and is not recorded."""
    calls: list[str] = []

    class _Child:
        @classmethod
        def _run_permission_checks(
            cls,
            _input_value: object,
            _request: object,
            *,
            _fired: dict[type[object], set[str]] | None = None,
            _depth: int = 0,
        ) -> None:
            calls.append("child._run")

    related_obj = type("Rel", (), {"orderset": _Child})()

    class _Parent(ActiveInputPermissionMixin):
        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            return ["name"], [("child", related_obj, {"x": 1})]

        @override
        @staticmethod
        def _invoke_permission_method(
            bare_instance: ActiveInputPermissionMixin,
            field_path: str,
            request: object,
            *,
            fired: set[str] | None = None,
        ) -> None:
            invoke_permission_method(bare_instance, field_path, request, fired=fired)

        def check_name_permission(self, _request: object) -> bool:
            calls.append("parent.name")
            return True

        def check_child_permission(self, _request: object) -> bool:
            calls.append("parent.child")
            return False

    fired: dict[type[object], set[str]] = {}
    with pytest.raises(GraphQLError, match="Not authorized to use child on _Parent"):
        run_active_input_permission_checks(
            _Parent,
            {"name": "v", "child": {"x": 1}},
            HttpRequest(),
            fired=fired,
            bare=object.__new__(_Parent),
            target_attr="orderset",
            related_attr="related_orders",
        )
    assert calls == ["parent.name", "child._run", "parent.child"]
    assert fired[_Parent] == {"check_name_permission"}


# ---------------------------------------------------------------------------
# _fire_flat_relation_path_gates -- flat traversal leaves are gated like their
# nested twins (the shared representational-bypass fix, both families).
# ---------------------------------------------------------------------------


class _Rel:
    """Duck-typed RelatedFilter/RelatedOrder: an ORM ``field_name`` + a target set."""

    def __init__(
        self,
        field_name: object,
        target: object,
        *,
        target_attr: str,
    ) -> None:
        self.field_name = field_name
        setattr(self, target_attr, target)


def _record_gate(store: list[str], label: str) -> Callable[[object, object], None]:
    def _check(_self: object, _request: object) -> None:
        store.append(label)

    return _check


def test_fire_flat_relation_path_gates_fires_the_deep_target_chain() -> None:
    """A deep flat path fires each parent relation gate plus the terminal field gate.

    ``entries__property__category__name`` fires the SAME gates the nested twin
    (``entries: {property: {category: {name}}}``) would: the branch gate on each
    intermediate set and ``check_name_permission`` on the terminal target set.
    """
    calls: list[str] = []

    class Category:
        check_name_permission = _record_gate(calls, "Category.name")

    class Property:
        related_filters = {"category": _Rel("category", Category, target_attr="filterset")}
        check_category_permission = _record_gate(calls, "Property.category")

    class Entry:
        related_filters = {"property": _Rel("property", Property, target_attr="filterset")}
        check_property_permission = _record_gate(calls, "Entry.property")

    class Item(ActiveInputPermissionMixin):
        related_filters = {"entries": _Rel("entries", Entry, target_attr="filterset")}
        check_entries_permission = _record_gate(calls, "Item.entries")

    _fire_flat_relation_path_gates(
        Item,
        "entries__property__category__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == [
        "Item.entries",
        "Entry.property",
        "Property.category",
        "Category.name",
    ]


def test_undeclared_walk_reads_no_relation_of_a_set_with_no_model() -> None:
    """The visibility reading walks undeclared relations off the set's model; a model-less set has none."""

    class Modelless:
        related_filters: dict[str, object] = {}

    assert walk_declared_relation_path(
        Modelless,
        "shelves__code",
        related_attr="related_filters",
        target_attr="filterset",
        undeclared=True,
    ) == ((), ("shelves", "code"))


def test_walk_declared_relation_path_returns_the_hops_and_the_path_left_on_the_last_target() -> (
    None
):
    """The walk reads the declared chain a flat path spells and hands back the rest.

    The longest ``field_name`` match is one hop; the walk stops at a segment no
    declaration claims and after a hop whose target is not a class; a
    relation-key path consumes its last relation as a hop and leaves nothing.
    """

    class Category:
        related_filters: dict[str, object] = {}

    class Version:
        related_filters: dict[str, object] = {}

    class Item(ActiveInputPermissionMixin):
        related_filters = {
            "category": _Rel("category", Category, target_attr="filterset"),
            "version": _Rel("target_version", Version, target_attr="filterset"),
            "milestone": _Rel("target_version__milestone", Category, target_attr="filterset"),
            "dangling": _Rel("dangling", None, target_attr="filterset"),
        }

    def _walk(
        path: str,
    ) -> tuple[list[tuple[type[object] | None, str, type[object] | None]], tuple[str, ...]]:
        hops, remainder = walk_declared_relation_path(
            Item,
            path,
            related_attr="related_filters",
            target_attr="filterset",
        )
        return [(hop.owner, hop.declared_attr, hop.target) for hop in hops], remainder

    assert _walk("name") == ([], ("name",))
    assert _walk("category") == ([(Item, "category", Category)], ())
    assert _walk("category__name") == ([(Item, "category", Category)], ("name",))
    assert _walk("category__parent__name") == ([(Item, "category", Category)], ("parent", "name"))
    assert _walk("target_version__milestone__name") == ([(Item, "milestone", Category)], ("name",))
    assert _walk("target_version__milestone") == ([(Item, "milestone", Category)], ())
    assert _walk("target_version__code") == ([(Item, "version", Version)], ("code",))
    assert _walk("dangling__name") == ([(Item, "dangling", None)], ("name",))
    assert _walk("undeclared__name") == ([], ("undeclared", "name"))


def test_fire_flat_relation_path_gates_resolves_a_renamed_branch_by_field_name() -> None:
    """A hop is matched on ``field_name`` (ORM accessor), not the public attr name.

    ``visible_shelves = RelatedFilter(ShelfFilter, field_name="shelves")`` has a
    public attr (``visible_shelves``) that differs from its ORM ``field_name``
    (``shelves``). The flat source path uses the ORM name (``shelves__code``); the
    hop still resolves, and the branch gate fired is keyed on the PUBLIC attr so it
    matches the gate the nested form fires.
    """
    calls: list[str] = []

    class Shelf:
        check_code_permission = _record_gate(calls, "Shelf.code")

    class Book(ActiveInputPermissionMixin):
        related_filters = {
            "visible_shelves": _Rel("shelves", Shelf, target_attr="filterset"),
        }
        check_visible_shelves_permission = _record_gate(calls, "Book.visible_shelves")

    _fire_flat_relation_path_gates(
        Book,
        "shelves__code",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Book.visible_shelves", "Shelf.code"]


def test_fire_flat_relation_path_gates_fires_the_branch_gate_of_a_relation_key_leaf() -> None:
    """A relation-key leaf (``shelves__isnull``) walks its declared branch, so its gate fires.

    The leaf reads the branch's target rows like its nested twin does, so the
    branch gate keyed on the PUBLIC attr fires; nothing remains on the target,
    so no target field gate fires.
    """
    calls: list[str] = []

    class Shelf:
        check_shelves_permission = _record_gate(calls, "Shelf.shelves")

    class Book(ActiveInputPermissionMixin):
        related_filters = {
            "visible_shelves": _Rel("shelves", Shelf, target_attr="filterset"),
        }
        check_visible_shelves_permission = _record_gate(calls, "Book.visible_shelves")

    _fire_flat_relation_path_gates(
        Book,
        "shelves",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Book.visible_shelves"]


def test_fire_flat_relation_path_gates_prefers_composite_branch_prefix() -> None:
    """A multi-hop RelatedFilter branch wins over a shorter overlapping branch.

    ``milestone`` can be declared over ``target_version__milestone`` while a
    separate ``target_version`` branch also exists. A flat
    ``target_version__milestone__key`` leaf must gate the declared composite
    branch and its target, not descend through the shorter branch and stop
    before the target permission hook.
    """
    calls: list[str] = []

    class Milestone:
        check_key_permission = _record_gate(calls, "Milestone.key")

    class TargetVersion:
        related_filters: dict[str, object] = {}

    class Card(ActiveInputPermissionMixin):
        related_filters = {
            "milestone": _Rel(
                "target_version__milestone",
                Milestone,
                target_attr="filterset",
            ),
            "target_version": _Rel(
                "target_version",
                TargetVersion,
                target_attr="filterset",
            ),
        }
        check_milestone_permission = _record_gate(calls, "Card.milestone")

    _fire_flat_relation_path_gates(
        Card,
        "target_version__milestone__key",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Card.milestone", "Milestone.key"]


def test_fire_flat_relation_path_gates_stops_at_an_unresolved_hop() -> None:
    """A relation hop with no declared RelatedFilter stops the walk (no guessing)."""
    calls: list[str] = []

    class Item(ActiveInputPermissionMixin):
        related_filters: dict[str, object] = {}  # no ``author`` RelatedFilter declared
        check_author_permission = _record_gate(calls, "Item.author")

    _fire_flat_relation_path_gates(
        Item,
        "author__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    # No declared related object for ``author`` -> no target gate is fired and no
    # FilterSet is guessed. The owner's flat-path gate (fired by the caller,
    # not here) remains the authorization point.
    assert calls == []


def test_fire_flat_relation_path_gates_dedupes_against_the_nested_twin() -> None:
    """Flat and nested twins share the per-class ``fired`` map: each gate fires once."""
    calls: list[str] = []

    class Category:
        check_name_permission = _record_gate(calls, "Category.name")

    class Item(ActiveInputPermissionMixin):
        related_filters = {"category": _Rel("category", Category, target_attr="filterset")}
        check_category_permission = _record_gate(calls, "Item.category")

    fired: dict[type, set[str]] = {}
    # First the flat leaf...
    _fire_flat_relation_path_gates(
        Item,
        "category__name",
        HttpRequest(),
        fired=fired,
        related_attr="related_filters",
        target_attr="filterset",
    )
    # ...then the same path again (as the nested twin would, sharing ``fired``).
    _fire_flat_relation_path_gates(
        Item,
        "category__name",
        HttpRequest(),
        fired=fired,
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Item.category", "Category.name"]


def test_fire_flat_relation_path_gates_works_for_the_order_family() -> None:
    """The shared fix covers the order family (``related_orders`` / ``orderset``).

    The order side exposes flat relation-traversal order fields via the
    ``Meta.fields = ["category__name"]`` shorthand; the same representational
    bypass is closed by the same shared walk with the order-family config.
    """
    calls: list[str] = []

    class CategoryOrder:
        check_name_permission = _record_gate(calls, "CategoryOrder.name")

    class ItemOrder(ActiveInputPermissionMixin):
        related_orders = {"category": _Rel("category", CategoryOrder, target_attr="orderset")}
        check_category_permission = _record_gate(calls, "ItemOrder.category")

    _fire_flat_relation_path_gates(
        ItemOrder,
        "category__name",
        HttpRequest(),
        fired={},
        related_attr="related_orders",
        target_attr="orderset",
    )
    assert calls == ["ItemOrder.category", "CategoryOrder.name"]


def test_fire_flat_relation_path_gates_falls_back_to_declared_attribute_when_field_name_is_none() -> (
    None
):
    """When field_name is None or omitted, the declared attribute name is used.

    In RelatedOrder(AuthorOrder) or RelatedFilter(AuthorFilter), field_name is None
    on the class declaration. A flat relation traversal (``author__name``) must fall
    back to the declared attribute key (``author``) rather than skipping the branch.
    """
    calls: list[str] = []

    class AuthorOrder:
        check_name_permission = _record_gate(calls, "AuthorOrder.name")

    class BookOrder(ActiveInputPermissionMixin):
        # field_name is None (the default for RelatedOrder(Target))
        related_orders = {"author": _Rel(None, AuthorOrder, target_attr="orderset")}
        check_author_permission = _record_gate(calls, "BookOrder.author")

    _fire_flat_relation_path_gates(
        BookOrder,
        "author__name",
        HttpRequest(),
        fired={},
        related_attr="related_orders",
        target_attr="orderset",
    )
    assert calls == ["BookOrder.author", "AuthorOrder.name"]


def test_fire_flat_relation_path_gates_stops_when_a_mid_chain_target_is_unresolved() -> None:
    """A hop whose related object's target set resolves to ``None`` stops the walk.

    A ``RelatedFilter``/``RelatedOrder`` whose lazy target has not resolved (or is
    unresolvable) exposes ``None`` at ``target_attr``; the branch gate on the
    current set still fires, but the walk stops rather than descending into
    ``None`` (so no terminal gate is fired on a phantom target).
    """
    calls: list[str] = []

    class Item(ActiveInputPermissionMixin):
        # ``category`` matches the hop but its target filterset is unresolved.
        related_filters = {"category": _Rel("category", None, target_attr="filterset")}
        check_category_permission = _record_gate(calls, "Item.category")

    _fire_flat_relation_path_gates(
        Item,
        "category__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    # The parent branch gate fired; the walk then stopped at the unresolved target.
    assert calls == ["Item.category"]


def test_fire_flat_relation_path_gates_is_a_noop_for_a_non_traversal_leaf() -> None:
    """A single-segment source path (no relation hop) fires nothing here."""
    calls: list[str] = []

    class Item(ActiveInputPermissionMixin):
        related_filters: dict[str, object] = {}
        check_name_permission = _record_gate(calls, "Item.name")

    _fire_flat_relation_path_gates(
        Item,
        "name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    # The owner's own field gate is fired by the caller's normal leaf loop, not
    # by the relation-chain walk.
    assert calls == []


def test_flat_relation_gate_skips_non_string_branch_names() -> None:
    """A non-string branch name matches no hop and fires no gate."""
    calls: list[str] = []

    class _NonStringSet(ActiveInputPermissionMixin):
        related_filters = {"category": _Rel(123, object(), target_attr="filterset")}
        check_category_permission = _record_gate(calls, "_NonStringSet.category")

    _fire_flat_relation_path_gates(
        _NonStringSet,
        "category__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )

    assert calls == []


def test_related_permission_declarations_fail_closed_for_malformed_metadata() -> None:
    """Only a mapping declares related branches; absent means none, malformed raises.

    The declaration is read statically, so a metaclass ``__getattribute__`` that
    would raise on it is never run: the class declares nothing and reads as none.
    """

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "related_filters":
                raise RuntimeError("related descriptor exploded")
            return object_result(super().__getattribute__, name)

    class _UnreadableSet(ActiveInputPermissionMixin, metaclass=_HostileMeta):
        pass

    class _NoneSet:
        related_filters = None

    class _InvalidSet:
        related_filters = []

    assert _related_declarations(_UnreadableSet, "related_filters") == ()
    assert _related_declarations(_NoneSet, "related_filters") == ()
    with pytest.raises(ConfigurationError) as excinfo:
        _related_declarations(_InvalidSet, "related_filters")
    assert str(excinfo.value) == (
        "_InvalidSet related permission declarations under 'related_filters' must be a "
        "mapping; got list."
    )


# ---------------------------------------------------------------------------
# run_active_input_permission_checks -- core dispatch + per-class dedup
# ---------------------------------------------------------------------------


def test_run_active_input_permission_checks_double_dispatch_and_dedup() -> None:
    """Parent per-branch gate + child gate both fire once; child recurses via its own class."""
    calls: list[str] = []

    class _Child:
        @classmethod
        def _run_permission_checks(
            cls,
            _input_value: object,
            _request: object,
            *,
            _fired: dict[type[object], set[str]] | None = None,
            _depth: int = 0,
        ) -> None:
            (_fired if _fired is not None else {}).setdefault(cls, set())
            calls.append(f"child._run@{_depth}")

    related_obj = type("Rel", (), {"orderset": _Child})()

    class _Parent(ActiveInputPermissionMixin):
        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            # The fused single-pass contract ``run_active_input_permission_checks``
            # consumes: one call yields BOTH the per-field gate
            # paths (repeated ``name`` -> must dedup) and the related branches.
            return ["name", "name"], [("child", related_obj, {"x": 1})]

        @override
        @staticmethod
        def _invoke_permission_method(
            bare_instance: ActiveInputPermissionMixin,
            field_path: str,
            request: object,
            *,
            fired: set[str] | None = None,
        ) -> None:
            invoke_permission_method(bare_instance, field_path, request, fired=fired)

        def check_name_permission(self, _request: object) -> None:
            calls.append("parent.name")

        def check_child_permission(self, _request: object) -> None:
            calls.append("parent.child")

    fired: dict[type, set[str]] = {}
    bare = object.__new__(_Parent)
    run_active_input_permission_checks(
        _Parent,
        {"name": "v", "child": {"x": 1}},
        HttpRequest(),
        fired=fired,
        bare=bare,
        target_attr="orderset",
        related_attr="related_orders",
    )
    # ``name`` gate fires ONCE despite the repeated path; the parent's per-branch
    # ``child`` gate fires once AND the child class recurses once. The shared core
    # threads the depth budget, so the child re-enters at ``_depth=1``.
    assert calls.count("parent.name") == 1
    assert calls.count("parent.child") == 1
    assert calls.count("child._run@1") == 1


def test_active_related_branches_empty_when_no_related_collection() -> None:
    class _NoRel(ActiveInputPermissionMixin):
        pass

    assert (
        active_related_branches(
            _NoRel,
            {"a": 1},
            related_attr="related_orders",
        )
        == []
    )


def test_run_active_input_permission_checks_caps_related_recursion() -> None:
    """A self-referential related branch is capped with a typed error (report Defect 5).

    The shared core threads a depth budget and refuses to recurse past the set's
    cap (``_MAX_LOGIC_DEPTH`` when defined, ``DEFAULT_SET_INPUT_TRAVERSAL_DEPTH``
    otherwise), converting an otherwise input-deep ``RecursionError`` into a
    catchable ``ConfigurationError`` at the source.
    """

    class _SelfRef(ActiveInputPermissionMixin):
        _MAX_LOGIC_DEPTH = 2

        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            # Always yields a related branch pointing back at THIS class -- the
            # runtime shape of ``CardFilter.dependencies`` -> ``CardFilter``.
            return [], [("child", _rel, {"x": 1})]

        @override
        @staticmethod
        def _invoke_permission_method(
            bare_instance: ActiveInputPermissionMixin,
            field_path: str,
            request: object,
            *,
            fired: set[str] | None = None,
        ) -> None:
            pass

        @override
        @classmethod
        def _run_permission_checks(
            cls,
            input_value: object,
            request: object,
            *,
            _fired: dict[type[object], set[str]] | None = None,
            _bare: ActiveInputPermissionMixin | None = None,
            _depth: int = 0,
        ) -> None:
            run_active_input_permission_checks(
                cls,
                input_value,
                request,
                fired=_fired if _fired is not None else {},
                bare=object.__new__(cls),
                target_attr="child_set",
                related_attr="related",
                depth=_depth,
            )

    _rel = type("Rel", (), {"child_set": _SelfRef})()

    with pytest.raises(ConfigurationError, match="nesting exceeded"):
        _SelfRef._run_permission_checks({"child": {"x": 1}}, HttpRequest())


def test_active_permission_targets_excludes_logic_and_related_keys_from_the_leaf_half() -> None:
    """The LEAF half of the single classification pass drops logic and related keys.

    The gate dispatch consumes exactly this half. It used to reach it through a
    ``active_permission_field_paths`` wrapper in this module that nothing in the
    package called - ``sets_mixins`` has its own one-line delegate, which is the
    natural home because it already holds the seven configuration values the
    wrapper made every caller re-pass.
    """

    class _Set(ActiveInputPermissionMixin):
        related_orders = {"shelf": object()}

    paths, branches = active_permission_targets(
        _Set,
        {"title": "asc", "shelf": {"code": "x"}, "and_": [{"title": "x"}]},
        field_specs={},
        related_attr="related_orders",
        logic_keys=frozenset({"and_"}),
        fallback_path=lambda attr: attr,
    )
    # ``shelf`` (related, recognized off ``_Set.related_orders``) and ``and_``
    # (logic) excluded; ``title`` falls back to the python-attr token since
    # ``field_specs`` has no entry.
    assert paths == ["title"]
    assert [name for name, _target, _value in branches] == ["shelf"]


# ---------------------------------------------------------------------------
# resolve_auth_aliases (the authorization-phase auth-alias identification)
# ---------------------------------------------------------------------------


def test_auth_aliases_for_permission_classes_gates_alias_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The explicit no-permissions opt-out grants no auth-alias access."""
    calls: list[None] = []

    def _resolve() -> frozenset[str]:
        calls.append(None)
        return frozenset({"auth"})

    monkeypatch.setattr(
        "django_strawberry_framework.utils.permissions.resolve_auth_aliases",
        _resolve,
    )

    assert auth_aliases_for_permission_classes([]) == frozenset()
    assert calls == []
    assert auth_aliases_for_permission_classes([object()]) == frozenset({"auth"})
    assert calls == [None]


def test_related_depth_error_survives_hostile_child_qualname() -> None:
    """The depth-limit error names the child set from its real qualname.

    A metaclass ``__getattribute__`` that raises on ``__qualname__`` never runs:
    the label is read from the interpreter, so the typed depth error surfaces.
    """

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__qualname__":
                raise RuntimeError("qualname exploded")
            return object_result(super().__getattribute__, name)

    class _Child(metaclass=_HostileMeta):
        _MAX_LOGIC_DEPTH = 0

        @classmethod
        def _run_permission_checks(
            cls,
            _input_value: object,
            _request: object,
            *,
            _fired: dict[type[object], set[str]] | None,
            _depth: int,
        ) -> NoReturn:
            raise AssertionError("depth gate should fire before recursion")

    related = type("Related", (), {"child_set": _Child})()

    class _Parent(ActiveInputPermissionMixin):
        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            return [], [("child", related, input_value)]

    with pytest.raises(ConfigurationError, match="nesting exceeded") as excinfo:
        run_active_input_permission_checks(
            _Parent,
            {"child": {}},
            HttpRequest(),
            fired={},
            bare=object.__new__(_Parent),
            target_attr="child_set",
            related_attr="related",
        )
    assert "._Child" in str(excinfo.value)


def test_run_active_input_permission_checks_falls_back_to_default_traversal_depth() -> None:
    """When child set defines no _MAX_LOGIC_DEPTH, traversal uses DEFAULT_SET_INPUT_TRAVERSAL_DEPTH."""

    class _ChildWithoutDepthCap:
        @classmethod
        def _run_permission_checks(
            cls,
            _input_value: object,
            _request: object,
            *,
            _fired: dict[type[object], set[str]] | None,
            _depth: int,
        ) -> NoReturn:
            raise AssertionError("depth gate should fire before recursion")

    related = type("Related", (), {"child_set": _ChildWithoutDepthCap})()

    class _Parent(ActiveInputPermissionMixin):
        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            return [], [("child", related, input_value)]

    # At depth=8, next_depth=9 > DEFAULT_SET_INPUT_TRAVERSAL_DEPTH (8), raising error
    with pytest.raises(
        ConfigurationError,
        match="nesting exceeded the maximum traversal depth \\(8\\)",
    ):
        run_active_input_permission_checks(
            _Parent,
            {"child": {}},
            HttpRequest(),
            fired={},
            bare=object.__new__(_Parent),
            target_attr="child_set",
            related_attr="related",
            depth=8,
        )


@pytest.mark.django_db
def test_resolve_auth_aliases_returns_the_default_alias_by_default() -> None:
    """With no divergent router, every auth model reads ``default``."""
    assert resolve_auth_aliases() == frozenset({"default"})


@pytest.mark.django_db
def test_resolve_auth_aliases_tracks_a_divergent_router_read_answer(
    settings: pytest_django.Settings,
) -> None:
    """The auth alias follows the router's read answer for the auth models."""
    auth_app_label = get_user_model()._meta.app_label

    class _AuthToShardRouter:
        def db_for_read(self, model: type[Model], **_hints: object) -> str | None:
            # Route the auth app (and its perm/contenttype/session companions)
            # to a non-default alias; everything else keeps the default.
            if model._meta.app_label in {
                auth_app_label,
                "auth",
                "contenttypes",
                "sessions",
            }:
                return "shard_b"
            return None

        def db_for_write(self, _model: type[Model], **_hints: object) -> None:
            return None

    settings.DATABASE_ROUTERS = [_AuthToShardRouter()]
    assert resolve_auth_aliases() == frozenset({"shard_b"})


@pytest.mark.django_db
def test_resolve_auth_aliases_includes_the_session_store_alias_while_sessions_is_installed(
    settings: pytest_django.Settings,
) -> None:
    """A router keeping ``sessions.Session`` on its own alias adds it to the auth set.

    Resolving the lazy request user loads a database-backed session, so the
    session store's read alias joins the auth aliases. With
    ``django.contrib.sessions`` uninstalled the model is skipped and only the
    other auth models' alias remains.
    """

    class _SessionStoreRouter:
        def db_for_read(self, model: type[Model], **_hints: object) -> str | None:
            return "session_store" if model._meta.label == "sessions.Session" else None

        def db_for_write(self, _model: type[Model], **_hints: object) -> None:
            return None

    settings.DATABASE_ROUTERS = [_SessionStoreRouter()]
    assert resolve_auth_aliases() == frozenset({"default", "session_store"})
    with modify_settings(INSTALLED_APPS={"remove": ["django.contrib.sessions"]}):
        assert resolve_auth_aliases() == frozenset({"default"})


def test_resolve_auth_aliases_skips_uninstalled_models() -> None:
    """A model the deployment does not install is skipped, never an error."""
    assert _safe_get_model("nonexistent_app", "Nope") is None
    assert _safe_get_model("auth", "Nope") is None


def test_channels_request_in_object_context_is_adapted_to_channels_request_adapter() -> None:
    """Channels request stored at context.request resolves to a ChannelsRequestAdapter."""

    class _FakeConsumer:
        def __init__(self, scope: object) -> None:
            self.scope = scope

    class _FakeChannelsRequest:
        def __init__(self, scope: object) -> None:
            self.consumer = _FakeConsumer(scope)
            self.method = "POST"

    scope = {"user": "ada", "session": {"key": "456"}}
    raw_req = _FakeChannelsRequest(scope)
    ctx = type("Context", (), {"request": raw_req})()
    info = type("Info", (), {"context": ctx})()

    resolved = request_from_info(info, family_label="FilterSet")
    assert isinstance(resolved, ChannelsRequestAdapter)
    assert resolved.user == "ada"
    assert resolved.session == {"key": "456"}
    assert resolved.scope is scope
    assert resolved.method == "POST"


def test_bare_channels_consumer_in_object_context_is_adapted() -> None:
    """A bare Channels WebSocket consumer context resolves to a ChannelsRequestAdapter."""

    class _FakeWSConsumer:
        def __init__(self, scope: object) -> None:
            self.scope = scope
            self.channel_name = "specific..inmemory!ws"

    scope = {"user": "grace", "session": None}
    consumer = _FakeWSConsumer(scope)
    info = type("Info", (), {"context": consumer})()

    resolved = request_from_info(info, family_label="OrderSet")
    assert isinstance(resolved, ChannelsRequestAdapter)
    assert resolved.user == "grace"
    assert resolved.session is None
    assert resolved.scope is scope
    assert resolved.channel_name == "specific..inmemory!ws"


def test_run_active_input_permission_checks_safely_handles_missing_target_attr() -> None:
    """If a related object lacks target_attr, child recursion is safely skipped without AttributeError."""

    class _DuckRelatedObj:
        # Does not define 'filterset' or 'target_attr'
        pass

    class _SampleFilter(ActiveInputPermissionMixin):
        @override
        @classmethod
        def _permission_walk_gates(
            cls,
            input_value: object,
        ) -> tuple[tuple[type[object], str], ...]:
            return ()

        @override
        @classmethod
        def _active_permission_targets(
            cls,
            input_value: object,
        ) -> tuple[list[str], list[tuple[str, object, object]]]:
            return [], [("duck", _DuckRelatedObj(), {"sub": 1})]

        @override
        @staticmethod
        def _invoke_permission_method(
            bare_instance: ActiveInputPermissionMixin,
            field_path: str,
            request: object,
            *,
            fired: set[str] | None = None,
        ) -> None:
            if fired is not None:
                fired.add(f"check_{field_path}_permission")

    fired: dict[type[object], set[str]] = {}
    run_active_input_permission_checks(
        _SampleFilter,
        {"duck": {"sub": 1}},
        object(),
        fired=fired,
        bare=object.__new__(_SampleFilter),
        target_attr="filterset",
        related_attr="related_filters",
    )
    assert fired.get(_SampleFilter) == {"check_duck_permission"}


def test_channels_request_adapter_idempotent_wrapping() -> None:
    """Wrapping an existing ChannelsRequestAdapter returns the adapter directly."""
    scope = {"user": "ada", "type": "websocket"}
    adapter = ChannelsRequestAdapter(HttpRequest(), scope)

    assert _channels_request_adapter(adapter) is adapter
    assert _channels_request_adapter({"request": adapter}) is adapter
    assert _channels_request_adapter(type("Ctx", (), {"request": adapter})()) is adapter
    assert _request_from_context(adapter) is adapter
    assert _request_from_context({"request": adapter}) is adapter
    assert _request_from_context(type("Ctx", (), {"request": adapter})()) is adapter


def test_permissions_all_exports_are_complete() -> None:
    """Every symbol in permissions.__all__ exists and resolve_auth_aliases is exported."""
    assert "resolve_auth_aliases" in perm.__all__
    for symbol in perm.__all__:
        assert hasattr(perm, symbol), f"Symbol {symbol!r} in __all__ but not in permissions module"
