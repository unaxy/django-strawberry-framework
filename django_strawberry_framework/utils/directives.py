"""Construction-time validation for the consumer-supplied ``directives=`` forward.

Every field factory in the package hands a consumer ``directives`` value
straight to ``strawberry.field()``. Strawberry consumes
that iterable LAZILY -- at class decoration or SDL render -- so an unvalidated
value fails THERE with an unrelated error, or not at all, far from the
assignment line that supplied it:

- a bare ``str`` / ``bytes`` / ``bytearray`` / ``memoryview`` satisfies
  ``Iterable`` but iterates CHARACTER-wise (into ``str`` chars, or into ``int``
  bytes), so Strawberry builds a field whose "directives" are chars or ints
  without ``__strawberry_directive__``: a raw ``AttributeError`` at schema build
  for ``str``, and a silent build that crashes SDL render for the byte flavors;
- an iterator that raises midway escapes as whatever it raised;
- a non-iterable detonates as a raw ``TypeError`` inside ``strawberry.field``;
- a value whose ``__class__`` read raises escapes an ``isinstance`` text-or-bytes
  check itself, before any iteration starts.

This module owns the ONE validation behind all of them: a char-wise value is
refused by its real class (never a ``__class__`` read), and a non-iterable is
refused by the ``TypeError`` ``list()`` documents for it. An iterable's own ``__iter__`` / ``__next__`` is
the consumer's behaviour and runs untouched; whatever it raises propagates.

Exception policy, package-wide. ``SystemExit``, ``KeyboardInterrupt``,
``GeneratorExit`` and ``asyncio.CancelledError`` always propagate: no handler
in the package catches ``BaseException`` (or one of those) except to clean up
and re-raise. Identity is read from the interpreter (``utils/truth.py``), never
asked of a consumer object, so no handler exists to contain a raising or lying
dunder. Consumer behaviour - hooks, resolvers, iterators, a consumer object's
``__repr__`` / ``__str__`` - runs untouched, and its exceptions propagate to the
one boundary, the schema's production error policy. Untrusted wire bytes are
parsed with pre-validation or one arm no wider than the parse's own documented
error. ``scripts/check_truthful_reads.py`` enforces the identity and
``BaseException`` halves.
"""

from django_strawberry_framework.exceptions import ConfigurationError

from . import truth
from ._narrowing import list_of
from .lazy import unwrap_lazy_object

__all__ = ("validated_field_directives",)

_CHAR_WISE_TYPES: tuple[type[object], ...] = (
    str,
    bytes,
    bytearray,
    memoryview,
)


def validated_field_directives(label: str, directives: object) -> tuple[object, ...]:
    """Return ``directives`` as a tuple, or raise the typed construction-time reject.

    ``label`` names the consuming factory (``"DjangoListField"``,
    ``"DjangoMutationField"``, ``"auth field"``, ...) so the ``ConfigurationError``
    points at the assignment line the consumer actually wrote.

    The message wording is fixed across every caller on purpose: it is the one
    string a consumer greps for, and the callers' tests match on it.
    """
    # Text and bytes-like values are ``Iterable`` but their elements are never directives:
    # ``bytearray`` and ``memoryview`` iterate into ``int`` exactly as ``bytes`` does, so
    # they share the reject arm rather than silently building integer directives. The
    # check reads the value's real class, never its ``__class__``; a Django lazy proxy is
    # checked as the object it wraps (``utils/lazy.py::unwrap_lazy_object``), so a lazy
    # ``str`` is text too.
    wrapped = unwrap_lazy_object(directives)
    if any(truth.is_instance(wrapped, char_wise) for char_wise in _CHAR_WISE_TYPES):
        raise ConfigurationError(
            f"{label} directives must be a sequence of directive instances; "
            f"got {truth.kind(directives)}.",
        )
    try:
        return tuple(list_of(directives))
    except TypeError as exc:
        # ``list()``'s documented refusal of a non-iterable. The message names
        # the exception's type, never its text.
        raise ConfigurationError(
            f"{label} directives could not be read ({truth.kind(exc)}).",
        ) from exc
