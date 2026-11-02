"""GraphQL/Django naming helpers for case conversion and lookup-path flattening.

Every name transform the package applies at the GraphQL/Django boundary:

- ``pascal_case`` builds ``PascalCase`` type-name stems from field names and
  lookup paths (``<TypeName><FieldName>Enum`` choice enums, per-field filter
  and order input types); ``pascal_case_or_raise`` adds the guard against an
  empty stem.
- ``flatten_lookup_path`` collapses a ``LOOKUP_SEP`` path into one identifier
  token.
"""

from typing import TYPE_CHECKING

from django_strawberry_framework.exceptions import ConfigurationError

from . import truth

if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ("flatten_lookup_path", "pascal_case", "pascal_case_or_raise")


def _plain_text(value: object) -> str:
    """Return ``value`` as an exact ``str``; raise ``ConfigurationError`` for a non-string.

    A string is a value whose real type is one: a lazy proxy, or an object whose
    ``__class__`` raises or claims ``str``, is a non-string. A ``str`` subclass is
    copied through the base slot (``truth.text``) so its overridden ``split`` /
    ``replace`` / ``strip`` never run inside these helpers. The exact-``str`` test,
    the common case, runs first.
    """
    if type(value) is str:
        return value
    if not truth.is_instance(value, str):
        raise ConfigurationError(
            f"String helper input must be a string; got {truth.kind(value)}.",
        )
    return truth.text(value)


def pascal_case(name: str) -> str:
    """Convert a ``snake_case`` field name or ``LOOKUP_SEP`` path to ``PascalCase``.

    Leading and trailing underscore runs are preserved verbatim
    (``"_leading"`` -> ``"_Leading"``, ``"status_"`` -> ``"Status_"``):
    members of one set whose names differ only at the underscore edges
    (``price`` / ``price_`` / ``_price``) are distinct Python attrs, so their
    generated type-name stems must stay distinct too -- otherwise
    two members' operator-bag / range / enum classes would claim one GraphQL
    type name and the set could not be served (a set whose two members mint
    one input type name of different fields is refused at finalize; two enums
    under one name fail Strawberry's duplicate-name check at schema build).

    Interior underscore runs collapse (``"double__underscore"`` ->
    ``"DoubleUnderscore"``), so a ``LOOKUP_SEP`` path PascalCases segment by
    segment (``"category__name"`` -> ``"CategoryName"``, the stem
    ``ClassBasedTypeNameMixin.type_name_for`` builds); the digit rule below
    pins the one interior boundary capitalization cannot encode.

    A separator before a digit-leading segment is retained (``"field_2"``
    -> ``"Field_2"``, not ``"Field2"``) because capitalization cannot encode
    that boundary: without it, ``field_2`` and ``field2`` both become
    ``Field2``, so per-field operator-bag / range / enum type names would
    collide and the set could not be served.

    Per-segment ``str.capitalize()`` lower-cases every character after the
    first, so acronyms are not preserved (``"my_HTTP_response"`` ->
    ``"MyHttpResponse"``) and names differing only in letter case share a stem
    (``my_HTTP`` / ``my_http`` -> ``MyHttp``); Django and DRF accept
    upper-case field names, so the stem is injective only over lowercase
    input. A generated input name two declarations still share is handled by
    ``utils/inputs.py::claim_generated_type_name``: classes of identical fields
    merge into one type, two shapes reached from one set raise
    ``ConfigurationError`` at finalize, and any other pair of shapes fails
    only the schema that serves both (``schema.py::DjangoSchema`` names the
    two declarations).

    An input with no word-character tokens (``""``, ``"_"``, ``"__"``)
    returns ``""``; ``pascal_case_or_raise`` turns that into the consumer's
    typed error rather than letting an empty stem collide with the root
    type name.

    Examples:
        ``"is_active"`` -> ``"IsActive"``;
        ``"status"`` -> ``"Status"``;
        ``"payment_method"`` -> ``"PaymentMethod"``;
        ``"field_2"`` -> ``"Field_2"``;
        ``"field2"`` -> ``"Field2"``;
        ``"_leading"`` -> ``"_Leading"``;
        ``"trailing_"`` -> ``"Trailing_"``;
        ``"___x_foo"`` -> ``"___XFoo"``;
        ``"double__underscore"`` -> ``"DoubleUnderscore"``.

    """
    name = _plain_text(name)
    parts = [part for part in name.split("_") if part]
    if not parts:
        return ""
    head, *rest = parts
    stem = head.capitalize() + "".join(
        f"_{part}" if part[0].isdigit() else part.capitalize() for part in rest
    )
    leading = name[: len(name) - len(name.lstrip("_"))]
    trailing = name[len(name.rstrip("_")) :]
    return f"{leading}{stem}{trailing}"


def pascal_case_or_raise(name: str, *, make_error: "Callable[[str], Exception]") -> str:
    """Return ``pascal_case(name)``, raising ``make_error(name)`` when it is empty.

    Single-sites the no-token check both consumers wrap:
    ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`` and
    ``filters/inputs.py::_pascal_case``. ``pascal_case`` returns ``""`` for an
    input with no word-character tokens (``""``, ``"_"``, ``"__"``), which
    would silently collide on downstream generated type names; ``make_error``
    keeps each consumer's error type and message consumer-specific while the
    emptiness check itself stays here.
    """
    pascal = pascal_case(name)
    if not pascal:
        raise make_error(name)
    return pascal


def flatten_lookup_path(name: str) -> str:
    """Flatten a Django ``LOOKUP_SEP`` path into a single identifier token.

    ``category__name`` -> ``category_name``: every run of two or more
    underscores becomes one. The one owner of this mangle behind (a)
    python-attr derivation for the generated filter / order input fields, (b)
    the ``check_<field>_permission`` method-name mangle, and (c) the order
    side's aggregate-alias mangle. ``LOOKUP_SEP`` must never survive into a
    generated attribute or alias: Django's ``prefetch_related`` / ``order_by``
    machinery splits on it, the reason generated ``Prefetch`` ``to_attr`` names
    escape it too.
    """
    flattened = _plain_text(name)
    while "__" in flattened:
        flattened = flattened.replace("__", "_")
    return flattened
