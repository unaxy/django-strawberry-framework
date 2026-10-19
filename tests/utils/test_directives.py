"""Tests for the shared field-directives validation (``utils/directives.py``).

``validated_field_directives`` raises at field construction. Per-factory call
sites stay in ``tests/test_list_field.py`` / ``tests/mutations/test_fields.py``;
consumer fields over HTTP live in ``examples/fakeshop/test_query/test_list_field_api.py``.
"""

from collections.abc import Iterator

import pytest
from django.utils.functional import SimpleLazyObject

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.directives import validated_field_directives
from tests._idioms import ClaimsClassBase, ClassReadRaises


@pytest.mark.parametrize(
    ("value", "type_name"),
    [
        ("@deprecated", "str"),
        (b"@deprecated", "bytes"),
        (bytearray(b"@deprecated"), "bytearray"),
        (memoryview(b"@deprecated"), "memoryview"),
    ],
)
def test_char_wise_sequences_are_rejected_typed(value: object, type_name: str) -> None:
    """The four Iterable-but-not-directives types reject at the construction line.

    A bare `str` iterates into characters and a `bytes` / `bytearray` /
    `memoryview` into ints; Strawberry consumes the iterable lazily, so an
    unvalidated value builds a field out of chars or ints and detonates at
    schema build or SDL render instead of here.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", value)
    assert str(exc.value) == (
        f"DjangoListField directives must be a sequence of directive instances; got {type_name}."
    )


def test_label_names_the_consuming_factory() -> None:
    """The label is interpolated so the message points at the assignment site."""
    with pytest.raises(ConfigurationError, match=r"^auth field directives must be"):
        validated_field_directives("auth field", "oops")


@pytest.mark.parametrize(
    "supplied",
    [
        (),
        [],
        ("a", "b"),
        ["a", "b"],
    ],
)
def test_ordinary_sequences_pass_through_as_tuples(supplied: tuple[str, ...] | list[str]) -> None:
    """Benign input is returned as a tuple with its contents and order intact."""
    assert validated_field_directives("DjangoListField", supplied) == tuple(supplied)


def test_generator_directives_are_materialized_once() -> None:
    """A single-pass iterable is consumed exactly once and handed back materialized.

    Returning the generator itself would let Strawberry's lazy read find it
    already exhausted, silently dropping every directive from the SDL.
    """
    seen: list[str] = []

    def _gen() -> Iterator[str]:
        for tag in ("a", "b"):
            seen.append(tag)
            yield tag

    result = validated_field_directives("DjangoListField", _gen())

    assert result == ("a", "b")
    assert seen == ["a", "b"]
    # Re-reading the RESULT does not re-drive the source generator.
    assert tuple(result) == ("a", "b")
    assert seen == ["a", "b"]


def test_non_iterable_raises_configuration_error_chaining_the_typeerror() -> None:
    """A non-iterable detonated as a raw TypeError inside ``strawberry.field`` pre-fix."""
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", 42)
    assert str(exc.value) == "DjangoListField directives could not be read (TypeError)."
    assert isinstance(exc.value.__cause__, TypeError)


def test_iterator_error_propagates() -> None:
    """An iterable's own iteration runs untouched; what it raises propagates."""

    class RaisingDirectives:
        def __iter__(self) -> Iterator[str]:
            yield "a"
            raise RuntimeError("iterator detonated")

    with pytest.raises(RuntimeError, match="iterator detonated"):
        validated_field_directives("DjangoMutationField", RaisingDirectives())


class _ClaimsStr(ClaimsClassBase):
    """A non-``str`` value whose ``__class__`` claims ``str``."""

    claimed = str


@pytest.mark.parametrize(
    "raised",
    [
        RuntimeError,
        ValueError,
        KeyboardInterrupt,
        SystemExit,
    ],
)
def test_value_whose_class_read_raises_is_judged_by_its_real_class(
    raised: type[BaseException],
) -> None:
    """The text-or-bytes check never reads ``__class__``, so a raising one never fires.

    The value's real class is neither text nor iterable: the typed unreadable reject,
    chaining ``list()``'s ``TypeError``. An ``isinstance`` check would let the value's own
    exception (an interrupt included) escape before any iteration starts.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", ClassReadRaises(raised))
    assert str(exc.value) == "DjangoListField directives could not be read (TypeError)."
    assert isinstance(exc.value.__cause__, TypeError)


def test_lazy_proxy_over_text_is_rejected_as_text() -> None:
    """A Django lazy proxy is checked as the object it wraps: a lazy ``str`` is text.

    Checking the proxy's own real class would let ``list()`` iterate the proxy's
    characters and the raw ``AttributeError`` at schema build would return.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", SimpleLazyObject(lambda: "@deprecated"))
    assert str(exc.value) == (
        "DjangoListField directives must be a sequence of directive instances; "
        "got SimpleLazyObject."
    )


def test_value_claiming_text_through_its_class_is_judged_by_its_real_class() -> None:
    """A ``__class__`` that claims ``str`` is not a ``str``: the value is still rejected.

    Its real class is not iterable, so it takes the typed unreadable reject.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", _ClaimsStr())
    assert str(exc.value) == "DjangoListField directives could not be read (TypeError)."
    assert isinstance(exc.value.__cause__, TypeError)
