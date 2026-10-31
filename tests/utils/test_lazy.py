"""Tests for Django lazy-proxy unwrapping (``utils/lazy.py::unwrap_lazy_object``).

The helper's own contract: a ``LazyObject`` is read as the object it wraps,
its factory running once and propagating what it raises, and every other value,
including one that merely forwards ``__class__``, comes back unchanged. The
consumers' verdicts are pinned where they classify: ``tests/auth/test_sessions.py``
(request transport), ``tests/utils/test_policies.py`` (policy overrides) and
``tests/types/test_relay_interfaces.py`` (``is_type_of``).
"""

from typing import NoReturn

import pytest
from django.utils.functional import SimpleLazyObject

from django_strawberry_framework.utils.lazy import _LAZY_OBJECT, unwrap_lazy_object
from tests._idioms import ClaimsClass


def test_a_lazy_proxy_is_read_as_the_object_it_wraps_running_its_factory_once() -> None:
    """The wrapped object comes back itself; a second read does not rerun the factory."""
    wrapped = object()
    calls: list[int] = []

    def factory() -> object:
        calls.append(1)
        return wrapped

    lazy = SimpleLazyObject(factory)
    assert unwrap_lazy_object(lazy) is wrapped
    assert unwrap_lazy_object(lazy) is wrapped
    assert calls == [1]


def test_a_raising_factory_propagates_its_own_exception() -> None:
    def factory() -> NoReturn:
        raise LookupError("factory")

    with pytest.raises(LookupError, match="factory"):
        unwrap_lazy_object(SimpleLazyObject(factory))


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(object(), id="ordinary-object"),
        pytest.param(ClaimsClass(_LAZY_OBJECT), id="claims-lazy-object"),
    ],
)
def test_a_value_that_is_not_a_django_lazy_proxy_comes_back_unchanged(value: object) -> None:
    """Only Django's own proxy is unwrapped; a ``__class__``-forwarding stand-in is not."""
    if type(value) is ClaimsClass:
        assert isinstance(value, _LAZY_OBJECT)
    assert unwrap_lazy_object(value) is value
