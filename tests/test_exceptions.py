"""Exception hierarchy: inheritance, GraphQL translation, typed-message renders.

This file keeps exception-class internals that a live ``/graphql/`` request
cannot uniquely show: the inheritance lattice, ``.args`` identity, standard
``str`` / ``repr`` rendering, pickle/copy fidelity, GraphQL-core
``located_error`` preserving the original exception type (the HTTP envelope
carries only ``message``), and the exact messages ``PathResolutionError`` /
``LookupValidationError`` build. Under the production error policy a resolver
exception is masked anyway, so a client JSON body cannot see
``original_error``.

Wire messages belong to the live suites that own the raise sites:
``examples/fakeshop/test_query/test_error_policy_api.py`` (masked resolver
exceptions, parse/validation pass-through, DEBUG unmasking),
``examples/fakeshop/test_query/test_connection_pagination_api.py``
(pagination ``GraphQLError`` containment),
``examples/fakeshop/test_query/test_products_api.py`` (mutation
``GraphQLError`` denials and in-band ``FieldError`` envelopes), and
``examples/fakeshop/test_query/test_transport_api.py`` (a misconfigured body
cap raising ``ConfigurationError`` out of ``Client.get``, not as JSON).
"""

from __future__ import annotations

import copy
from collections.abc import Callable

import pytest
import strawberry
from apps.library.models import Book
from strawberry.types import ExecutionResult
from typing_extensions import override

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    LookupValidationError,
    OptimizerError,
    PathResolutionError,
)
from django_strawberry_framework.utils.querysets import SyncMisuseError
from tests._idioms import pickle_roundtrip


class _Unprintable:
    """A consumer message arg whose ``str`` / ``repr`` both raise."""

    @override
    def __str__(self) -> str:
        raise RuntimeError("str failed")

    @override
    def __repr__(self) -> str:
        raise RuntimeError("repr failed")


class _PicklableDummyModelMeta:
    label = "auth.User"


class _PicklableDummyModel:
    _meta = _PicklableDummyModelMeta()


class _PicklableDummyTerminal:
    name = "created_at"


class _TaggedPathResolutionError(PathResolutionError):
    """A ``PathResolutionError`` carrying the extra instance state a roundtrip must keep."""

    custom_tag: str


class _TaggedLookupValidationError(LookupValidationError):
    """A ``LookupValidationError`` carrying the extra instance state a roundtrip must keep."""

    custom_tag: str


def _execute_raising(exc_factory: Callable[[], BaseException]) -> ExecutionResult:
    @strawberry.type
    class Query:
        @strawberry.field
        def boom(self) -> str:
            raise exc_factory()

    return strawberry.Schema(query=Query).execute_sync("{ boom }")


def test_inheritance_lattice() -> None:
    assert issubclass(ConfigurationError, DjangoStrawberryFrameworkError)
    assert issubclass(OptimizerError, DjangoStrawberryFrameworkError)
    assert issubclass(PathResolutionError, ConfigurationError)
    assert issubclass(LookupValidationError, ConfigurationError)
    assert issubclass(SyncMisuseError, ConfigurationError)
    assert issubclass(SyncMisuseError, DjangoStrawberryFrameworkError)
    assert issubclass(SyncMisuseError, RuntimeError)
    assert not issubclass(OptimizerError, ConfigurationError)
    assert not issubclass(PathResolutionError, OptimizerError)


def test_normal_string_message_unchanged() -> None:
    err = OptimizerError("Unplanned N+1: books")
    assert str(err) == "Unplanned N+1: books"
    assert err.args == ("Unplanned N+1: books",)


def test_empty_args_render_empty_string() -> None:
    """No message args: ``str`` is empty, exactly as with any other exception."""
    assert str(DjangoStrawberryFrameworkError()) == ""


def test_args_reassignment_and_pickle_never_leave_stale_render_caches() -> None:
    """Standard mutable-``args`` semantics survive rendering and serialization."""
    err = ConfigurationError("first")
    assert str(err) == "first"
    assert repr(err) == "ConfigurationError('first')"

    err.args = ("second",)
    restored = pickle_roundtrip(err)

    assert str(err) == "second"
    assert repr(err) == "ConfigurationError('second')"
    assert str(restored) == "second"
    assert repr(restored) == "ConfigurationError('second')"


@pytest.mark.parametrize(
    "roundtrip",
    [pickle_roundtrip, copy.copy, copy.deepcopy],
    ids=["pickle", "copy", "deepcopy"],
)
def test_path_resolution_error_roundtrip_preserves_attributes(
    roundtrip: Callable[[object], object],
) -> None:
    """PathResolutionError keeps constructor args and extra state across a roundtrip."""
    err = _TaggedPathResolutionError(_PicklableDummyModel, "groups.permissions", "permissions")
    err.custom_tag = "custom_value"

    restored = roundtrip(err)

    assert isinstance(restored, PathResolutionError)
    assert restored.model is _PicklableDummyModel
    assert restored.field_path == "groups.permissions"
    assert restored.segment == "permissions"
    assert getattr(restored, "custom_tag", None) == "custom_value"
    assert str(restored) == str(err)
    assert repr(restored) == repr(err)


@pytest.mark.parametrize(
    "roundtrip",
    [pickle_roundtrip, copy.copy, copy.deepcopy],
    ids=["pickle", "copy", "deepcopy"],
)
def test_lookup_validation_error_roundtrip_preserves_attributes(
    roundtrip: Callable[[object], object],
) -> None:
    """LookupValidationError keeps constructor args and extra state across a roundtrip."""
    term = _PicklableDummyTerminal()
    err = _TaggedLookupValidationError(term, "created_at__year__invalid", "invalid")
    err.custom_tag = "custom_value"

    restored = roundtrip(err)

    assert isinstance(restored, LookupValidationError)
    assert isinstance(restored.terminal, _PicklableDummyTerminal)
    assert restored.terminal.name == "created_at"
    assert restored.lookup_expr == "created_at__year__invalid"
    assert restored.part == "invalid"
    assert getattr(restored, "custom_tag", None) == "custom_value"
    assert str(restored) == str(err)
    assert repr(restored) == repr(err)
    if roundtrip is copy.copy:
        assert restored.terminal is term
    else:
        assert restored.terminal is not term


def test_framework_error_keeps_its_type_through_graphql() -> None:
    """GraphQL-core ``located_error`` calls ``str(exc)``; the original type survives."""
    result = _execute_raising(lambda: ConfigurationError("bad config"))
    assert result.errors is not None
    oe = result.errors[0].original_error
    assert isinstance(oe, ConfigurationError)
    assert isinstance(oe, DjangoStrawberryFrameworkError)
    assert result.errors[0].message == "bad config"

    result = _execute_raising(lambda: SyncMisuseError("sync misuse"))
    assert result.errors is not None
    oe = result.errors[0].original_error
    assert isinstance(oe, SyncMisuseError)
    assert isinstance(oe, RuntimeError)


def test_consumer_message_arg_renders_through_its_own_dunders() -> None:
    """A consumer object as the message renders like any exception's args.

    The framework never raises one (its messages are exact ``str``), so a
    consumer that does gets its object's own ``__str__`` / ``__repr__``, and
    whatever those raise propagates.
    """
    bad = _Unprintable()
    err = ConfigurationError(bad)
    assert err.args == (bad,)
    with pytest.raises(RuntimeError, match="str failed"):
        str(err)
    with pytest.raises(RuntimeError, match="repr failed"):
        repr(err)


def test_path_resolution_error_message_is_pinned() -> None:
    err = PathResolutionError(Book, "loans__x", "x")
    assert str(err) == (
        "Cannot classify path 'loans__x' on model library.Book: "
        "segment 'x' is not a traversable model-field relation."
    )
    assert err.model is Book
    assert (err.field_path, err.segment) == ("loans__x", "x")
    # A value without ``_meta`` is named by its kind.
    assert "on model object:" in str(PathResolutionError(object(), "a", "a"))


def test_lookup_validation_error_message_is_pinned() -> None:
    terminal = Book._meta.get_field("title")
    err = LookupValidationError(terminal, "title__nope", "nope")
    assert str(err) == (
        "Invalid lookup expression 'title__nope' for terminal title: "
        "part 'nope' is not a valid transform or lookup."
    )
    assert "for terminal object:" in str(LookupValidationError(object(), "x", "x"))
