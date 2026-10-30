"""Django model-field -> Strawberry type conversion, choice enums, and file / image output types.

Public surface:

- ``convert_field_output(field, type_name)`` - the read-output entry point
  ``types/base.py::_build_annotations`` calls for every non-relation column.
  Routes ``FileField`` / ``ImageField`` through ``FIELD_OUTPUT_TYPE_MAP`` to
  the structured ``DjangoFileType`` / ``DjangoImageType`` output objects
  (nullable by default as ``<object> | None`` to match the parent resolver's
  empty-file ``None``), and
  delegates every other column to ``convert_scalar``. File/image columns are
  read-output-only here: the lookup is kept OFF ``convert_scalar`` /
  ``scalar_for_field`` / ``SCALAR_MAP`` so no output object can ever reach the
  shared filter-input path (a ``FilterSet`` over a file column still yields a
  scalar ``str`` input).
- ``DjangoFileType`` / ``DjangoImageType`` - the structured read-output
  objects with the same public field names as ``strawberry-graphql-django``. ``DjangoFileType`` carries
  ``name`` / ``size`` / ``url``; ``DjangoImageType`` subclasses it and adds
  ``width`` / ``height``. Every nullable subfield delegates to the shared
  ``_safe_file_attr`` storage guard; ``name`` is read directly.
- ``DjangoFilePathType`` / ``DjangoImagePathType`` - the opt-in siblings that
  add the server's absolute filesystem ``path``. A generated type reaches them
  only by naming the column in ``Meta.filesystem_path_fields``; the path is
  deployment metadata and is off the default output on purpose (spec-048
  Decision 1).
- ``FIELD_OUTPUT_TYPE_MAP`` - module-level ``dict[type[models.Field], type]``
  mapping ``ImageField`` (listed before ``FileField`` by most-specific-first
  convention; the MRO walk, not dict order, decides the hit) and
  ``FileField`` to their output object. Consulted only through the shared
  ``_field_output_type_for`` MRO walk; never by ``scalar_for_field``.
- ``convert_scalar(field, type_name)`` - scalar columns
  (``CharField`` -> ``str`` etc.). Branches on ``scalar_route(field)``: the
  ``ArrayField`` / ``HStoreField`` arms, else the ``SCALAR_MAP`` match, then
  delegates to ``convert_choices_to_enum`` when ``field.choices`` is set, then
  widens to ``T | None`` on ``field.null``.
- ``scalar_route(field)`` - which ``convert_scalar`` arm converts a column:
  ``ArrayRoute`` (with the element field), ``HStoreRoute``, or ``MapRoute``
  (the matched ``SCALAR_MAP`` key class, its scalar, and whether the choice
  enum replaces it). ``inspect_django_type`` names its converter column from
  the same route.
- ``refuse_nested_array(field, element)`` - the one nested-``ArrayField``
  refusal, asked by ``convert_scalar``'s array arm and by the filter-input
  element read (``filters/inputs.py::_array_element_column``).
- ``convert_choices_to_enum(field, type_name)`` - generate (or fetch
  cached) Strawberry ``Enum`` from a Django choice field; called from
  ``convert_scalar`` when ``field.choices`` is set and also importable
  directly for tests / custom resolvers.
- ``resolved_relation_annotation(field, target_type, *, field_meta=None)``
  - render the final relation annotation for ``field`` pointing at a
  resolved ``DjangoType`` (``target_type``). Cardinality / null widening
  is sourced from ``FieldMeta``; reused by ``types/finalizer.py``'s
  deferred-resolution path.
- ``SCALAR_MAP`` - module-level ``dict[type[models.Field], TypeForm[object]]`` mapping
  Django field classes to their Python / Strawberry scalar. Mutable,
  last-write-wins, read on every ``convert_scalar`` call (no caching), so
  post-``finalize_django_types()`` mutations remain visible. The canonical
  extension path for a third-party / consumer field is to **subclass** a
  supported Django field - ``convert_scalar``'s MRO walk picks up the
  parent's scalar without registration. ``SCALAR_MAP[FieldCls] = py_type``
  is the non-subclass extension hook (e.g. unrelated third-party fields
  that store to a non-mapped column type). Notably absent from the
  default map: ``DurationField`` (no first-party Strawberry scalar - a
  consumer must register a custom scalar via ``SCALAR_MAP[DurationField]
  = MyDurationScalar``) and ``BinaryField`` (no first-party Strawberry
  scalar either; ``strawberry.scalars.Base64`` is the conventional plug:
  ``SCALAR_MAP[BinaryField] = strawberry.scalars.Base64``).

All field-shape introspection lives here so ``types/base.py`` stays
focused on ``Meta`` orchestration.
"""

import datetime
import decimal
import keyword
import re
import uuid
from dataclasses import dataclass
from enum import Enum, EnumMeta
from types import GenericAlias
from typing import TYPE_CHECKING, TypeAlias, TypeGuard, TypeVar, cast

import strawberry
from django.db import models
from django.db.models.fields.files import FieldFile, ImageFieldFile

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.registry import registry
from django_strawberry_framework.scalars import BigInt
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._array_field import array_element_field
from django_strawberry_framework.utils._narrowing import (
    is_iterable,
    is_list_or_tuple,
    is_text_atom,
    optional_annotation,
)
from django_strawberry_framework.utils.imports import import_attr_if_importable
from django_strawberry_framework.utils.lazy import unwrap_lazy_object
from django_strawberry_framework.utils.strings import pascal_case

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from django.contrib.postgres.fields import HStoreField
    from typing_extensions import TypeForm

    from django_strawberry_framework.utils.typing import (
        ConcreteField,
        ModelField,
    )

    from .base import DjangoType


_T = TypeVar("_T")


def _safe_file_attr(read: "Callable[[], _T]") -> _T | None:
    """Run one storage-backed ``FieldFile`` read, degrading storage failures to ``None``.

    The single per-subfield guard shared by every nullable subfield resolver
    on ``DjangoFileType`` / ``DjangoImageType`` (``size`` / ``url``, plus
    ``width`` / ``height`` on images and the opt-in ``path`` on
    ``DjangoFilePathType`` / ``DjangoImagePathType``). ``read`` reads one property
    off the bound ``FieldFile`` the parent resolver returned (always truthy here --
    an empty file resolves the whole object to ``None`` before any subfield runs).

    The catch list is deliberately NARROW -- ``ValueError`` / ``OSError`` /
    ``NotImplementedError`` -- the storage-shaped errors a non-filesystem
    backend (S3 ``FieldFile.path`` -> ``NotImplementedError``) or a vanished
    file (``.size`` -> ``OSError``; ``.url`` on local storage is string-built
    from ``MEDIA_URL`` and does NOT raise) raises. Anything
    else propagates: in particular ``SuspiciousFileOperation`` (a
    ``SuspiciousOperation``, NOT a ``ValueError`` / ``OSError``) is a
    path-traversal security signal that must surface as a top-level error, not
    hide as a ``null`` subfield (spec-037 Decision 4). Catching a broad
    ``Exception`` would also swallow genuine resolver bugs.
    """
    try:
        return read()
    except (ValueError, OSError, NotImplementedError):
        return None


@strawberry.type
class DjangoFileType:
    """Structured read-output for a Django ``FileField`` (spec-037 Decision 3).

    The default output is limited to the subfields a remote client needs --
    ``name`` / ``size`` / ``url``. The server's absolute filesystem path is
    NOT among them (spec-048 Decision 1): it is deployment metadata that can
    reveal usernames, release directories, container mounts, tenant layout and
    storage conventions, none of which a client needs to render a file. A
    deployment that genuinely serves the path opts in per column through
    ``Meta.filesystem_path_fields``, which swaps this type for
    ``DjangoFilePathType``.

    The fields are resolver-backed (not bare annotations) because the storage
    properties (``url`` / ``size``) raise on a non-filesystem backend or a
    vanished file, and that access happens per-subfield AFTER the parent
    resolver returns -- outside any parent ``try/except`` -- so the guard must
    live on each subfield (spec-037 Decision 4). Each resolver's ``root`` is the
    bound ``FieldFile`` the generated parent resolver returned
    (``types/resolvers.py::_make_file_resolver``), not an instance of this class.

    Subfield nullability deliberately diverges from upstream's all-non-null
    shape: ``name`` is non-null (a stored string, present whenever the object
    is non-null), while ``size`` / ``url`` are nullable so a storage quirk on
    one property degrades that subfield to ``null`` rather than 500ing the
    whole query.
    """

    @strawberry.field
    @staticmethod
    def name(root: strawberry.Parent[FieldFile]) -> str:
        """Return the stored file name. Non-null and read directly (no storage guard)."""
        # ``FieldFile.__str__`` is ``self.name or ""``, and the parent resolver returns
        # only a truthy file (one with a non-empty name), so this is the stored name.
        return str(root)

    @strawberry.field
    @staticmethod
    def size(root: strawberry.Parent[FieldFile]) -> int | None:
        """Return the file size in bytes, or ``None`` if storage cannot read it."""
        return _safe_file_attr(lambda: root.size)

    @strawberry.field
    @staticmethod
    def url(root: strawberry.Parent[FieldFile]) -> str | None:
        """Return the file URL, or ``None`` if storage cannot produce one."""
        return _safe_file_attr(lambda: root.url)


@strawberry.type
class DjangoImageType(DjangoFileType):
    """Structured read-output for a Django ``ImageField`` (spec-037 Decision 3).

    Subclasses ``DjangoFileType`` -- inheriting ``name`` / ``size`` / ``url``
    so the three shared subfields are defined once -- and adds the image-only
    ``width`` / ``height`` dimensions through the same ``_safe_file_attr``
    guard. Two distinct types (rather than one flagged type with an
    ``is_image`` check) keep dimension fields off non-image files and match
    upstream.
    """

    @strawberry.field
    @staticmethod
    def width(root: strawberry.Parent[ImageFieldFile]) -> int | None:
        """Return the image width in pixels, or ``None`` if storage cannot read it."""
        return _safe_file_attr(lambda: root.width)

    @strawberry.field
    @staticmethod
    def height(root: strawberry.Parent[ImageFieldFile]) -> int | None:
        """Return the image height in pixels, or ``None`` if storage cannot read it."""
        return _safe_file_attr(lambda: root.height)


def _filesystem_path(root: strawberry.Parent[FieldFile]) -> str | None:
    """Return the absolute filesystem path, or ``None`` if storage cannot produce one."""
    return _safe_file_attr(lambda: root.path)


@strawberry.type
class _FileSystemPathFields:
    """The single definition of the opt-in ``path`` subfield (spec-048 Decision 1).

    A ``@strawberry.type``-decorated mixin rather than a plain one: Strawberry
    collects inherited fields only from bases that carry a type definition, so
    an undecorated mixin's ``path`` would silently vanish from both composed
    types. Private and never referenced by an annotation, so it contributes no
    GraphQL type of its own -- only the two public compositions below reach the
    schema.

    Defined once so ``DjangoFilePathType`` and ``DjangoImagePathType`` cannot
    drift in either the resolver's storage guard or the security wording of the
    description a consumer's SDL will carry.
    """

    path: str | None = strawberry.field(
        resolver=_filesystem_path,
        description=(
            "SECURITY: the file's absolute path on the server filesystem. Opted in "
            "per column via Meta.filesystem_path_fields; it is deployment metadata, "
            "not client data. Null when the storage backend cannot produce one."
        ),
    )


@strawberry.type
class DjangoFilePathType(DjangoFileType, _FileSystemPathFields):
    """``DjangoFileType`` plus the opt-in absolute filesystem ``path``.

    Reached only by naming the column in ``Meta.filesystem_path_fields``; it is
    never the default output for a ``FileField``. The opt-in is per column and
    lives in the type's own ``Meta``, so a reviewer reading one class sees every
    path the type publishes (spec-048 Decision 2).
    """


@strawberry.type
class DjangoImagePathType(DjangoImageType, _FileSystemPathFields):
    """``DjangoImageType`` plus the opt-in absolute filesystem ``path``.

    The ``ImageField`` counterpart of ``DjangoFilePathType``, reached the same
    way and carrying the same ``width`` / ``height`` dimensions as the default
    image output.
    """


SCALAR_MAP: "dict[type[ConcreteField], TypeForm[object]]" = {
    models.AutoField: int,
    models.BigAutoField: int,
    models.SmallAutoField: int,
    models.CharField: str,
    models.TextField: str,
    models.SlugField: str,
    models.EmailField: str,
    models.URLField: str,
    models.GenericIPAddressField: str,
    models.FilePathField: str,
    models.IntegerField: int,
    models.BigIntegerField: BigInt,
    models.SmallIntegerField: int,
    models.PositiveIntegerField: int,
    models.PositiveSmallIntegerField: int,
    models.PositiveBigIntegerField: BigInt,
    models.BooleanField: bool,
    models.FloatField: float,
    models.DecimalField: decimal.Decimal,
    models.DateField: datetime.date,
    models.DateTimeField: datetime.datetime,
    models.TimeField: datetime.time,
    models.JSONField: strawberry.scalars.JSON,
    models.UUIDField: uuid.UUID,
    # FileField / ImageField stay ``str`` here on purpose: SCALAR_MAP is the
    # SHARED scalar/filter-input map (``scalar_for_field`` walks it for both the
    # selected-field side and ``filters/inputs.py::_scalar_from_model_field``). The
    # structured read-output objects live in FIELD_OUTPUT_TYPE_MAP below, so a
    # FilterSet over a file column still generates a scalar ``str`` input and no
    # output object ever leaks into a GraphQL input (spec-037 Decision 3).
    models.FileField: str,
    models.ImageField: str,
}

# Read-output-only file/image map, kept OFF the shared SCALAR_MAP /
# ``scalar_for_field`` filter-input path (spec-037 Decision 3). ImageField is
# listed before FileField (a superclass) by most-specific-first convention;
# the ``_field_output_type_for`` MRO walk -- not dict order -- resolves an
# ``ImageField`` (and consumer ImageField subclasses) to ``DjangoImageType``
# rather than falling through to ``DjangoFileType``, exactly as
# ``PositiveBigIntegerField`` resolves to ``BigInt`` before ``IntegerField``
# in SCALAR_MAP although listed after it.
FIELD_OUTPUT_TYPE_MAP: "dict[type[ConcreteField], type[DjangoFileType]]" = {
    models.ImageField: DjangoImageType,
    models.FileField: DjangoFileType,
}

# The opt-in sibling of each default file/image output object, keyed by the
# default (spec-048 Decision 2). A second dict rather than a second
# ``models.Field``-keyed map: the substitution is a property of the OUTPUT type
# already resolved by ``_field_output_type_for``, so keying it on the field
# class again would duplicate the MRO walk and let the two maps disagree about
# what an ``ImageField`` subclass resolves to.
FILESYSTEM_PATH_OUTPUT_TYPE_MAP: dict[type[DjangoFileType], type[DjangoFileType]] = {
    DjangoImageType: DjangoImagePathType,
    DjangoFileType: DjangoFilePathType,
}

# A choices entry is a ``(value, label-or-group)`` pair.
_CHOICE_ENTRY_LENGTH = 2

_NON_IDENT = re.compile(r"\W+", flags=re.ASCII)


_GRAPHQL_RESERVED_ENUM_VALUES = frozenset(
    {"false", "null", "true"},
)


# Soft-import ``HStoreField`` through the shared optional-import owner
# (``utils/imports.py::import_attr_if_importable``): ``None`` when
# ``django.contrib.postgres.fields`` is unavailable (package import still succeeds on a
# dev environment without the postgres driver), and a loud ``AttributeError`` if that
# module is importable but somehow missing the class -- a broken environment that
# should fail rather than silently degrade. The cast names the class the by-name lookup
# returns. ``ArrayField`` resolves the same way in its one owner,
# ``utils/_array_field.py``, which every subsystem's array test reads.
_HSTORE_FIELD_CLS = cast(
    "type[HStoreField] | None",
    import_attr_if_importable("django.contrib.postgres.fields", "HStoreField"),
)


def _field_label(field: object) -> str:
    """Return ``Model.field`` for diagnostics; an unbound field reads ``<unbound>``."""
    model = getattr(field, "model", None)
    model_name = truth.name(model) if truth.is_type(model) else "<unbound>"
    return f"{model_name}.{truth.text(getattr(field, 'name', '<unknown>'), '<unknown>')}"


def _scalar_map_entry(field: "ModelField") -> "tuple[type[ConcreteField], TypeForm[object]]":
    """Return the ``SCALAR_MAP`` ``(key, scalar)`` entry ``field``'s nearest MRO class keys.

    The one ``SCALAR_MAP`` walk: ``scalar_for_field`` and ``scalar_route``'s map arm both
    read it. Raises ``ConfigurationError`` for an unsupported field class.
    """
    entry = truth.mro_entry(SCALAR_MAP, truth.class_of(field))
    if entry is not None:
        return entry
    raise ConfigurationError(
        f"Unsupported Django field type {truth.render(truth.kind(field))} on "
        f"{_field_label(field)}. Add an entry to "
        "SCALAR_MAP or exclude this field via Meta.exclude.",
    )


def scalar_for_field(field: "ModelField") -> "TypeForm[object]":
    """Resolve a Django field to its ``SCALAR_MAP`` Python / Strawberry scalar.

    Walks ``type(field).__mro__`` so consumer-defined subclasses of a supported
    field resolve to the parent's scalar, and raises ``ConfigurationError`` for
    an unsupported field class. This is the single field-class -> scalar lookup
    shared by :func:`convert_scalar` (full DjangoType field conversion) and the
    filter-input converter (``filters/inputs.py::_scalar_from_model_field``), so a
    column resolves to the SAME scalar on the selected-field side and the
    filter-input side -- including consumer-registered ``SCALAR_MAP`` entries.
    It does NOT apply choice substitution or null widening; callers layer those
    on (``convert_scalar`` does; filter inputs handle choices separately).
    """
    return _scalar_map_entry(field)[1]


@dataclass(frozen=True)
class ArrayRoute:
    """``convert_scalar``'s ``ArrayField`` arm: ``list[<element>]`` over ``element``."""

    element: "ConcreteField"


@dataclass(frozen=True)
class HStoreRoute:
    """``convert_scalar``'s ``HStoreField`` arm: ``strawberry.scalars.JSON``."""


@dataclass(frozen=True)
class MapRoute:
    """``convert_scalar``'s ``SCALAR_MAP`` arm: the matched ``key`` class and its ``scalar``.

    ``choices`` is true when the column declares choices, so the generated choice enum
    replaces ``scalar``.
    """

    key: "type[ConcreteField]"
    scalar: "TypeForm[object]"
    choices: bool


ScalarRoute: TypeAlias = ArrayRoute | HStoreRoute | MapRoute


def scalar_route(field: "ConcreteField") -> ScalarRoute:
    """Return which ``convert_scalar`` arm converts ``field``, with that arm's data.

    The sentinel-guarded postgres containers come first (``ArrayField``, then
    ``HStoreField``), so a test double subclassing ``models.Field`` never matches a
    ``SCALAR_MAP`` parent; every other column takes the ``SCALAR_MAP`` arm, which
    raises ``ConfigurationError`` for an unsupported field class. Classification only:
    the container arms' nested-array and ``choices`` rejections stay in
    ``convert_scalar``.
    """
    element = array_element_field(field)
    if element is not None:
        return ArrayRoute(element)
    if _HSTORE_FIELD_CLS is not None and truth.is_instance(field, _HSTORE_FIELD_CLS):
        return HStoreRoute()
    key, scalar = _scalar_map_entry(field)
    return MapRoute(key, scalar, choices=bool(field.choices))


def refuse_nested_array(field: object, element: object) -> None:
    """Refuse an ``ArrayField`` whose element column ``element`` is itself an ``ArrayField``.

    ``element`` is ``field``'s ``base_field`` (``utils/_array_field.py::array_element_field``).
    Multi-dimensional arrays have no GraphQL shape on either side: ``convert_scalar``'s array
    arm and the filter-input element read (``filters/inputs.py::_array_element_column``) both
    raise this one ``ConfigurationError``.
    """
    if array_element_field(element) is not None:
        raise ConfigurationError(
            f"Nested ArrayField on {_field_label(field)} is not supported.",
        )


def convert_scalar(
    field: "ConcreteField",
    type_name: str,
    *,
    force_nullable: bool | None = None,
) -> object:
    """Map a Django scalar field to a Python / Strawberry type.

    Algorithm:

    0. Compute ``effective_null`` from the ``force_nullable`` tri-state
       (``field.null`` when ``force_nullable is None``, else
       ``force_nullable`` itself); this single value drives every outer
       nullability decision below.
    0b. Branch on ``scalar_route(field)``. The array arm rejects nested
       arrays and outer ``choices``, then recurses on ``base_field`` and wraps
       in ``list[inner]``. The HStore arm rejects outer ``choices``, then
       returns ``strawberry.scalars.JSON``. Both widen to ``T | None`` on
       ``effective_null`` themselves.
    1. Otherwise the route is the ``SCALAR_MAP`` arm: the nearest class in
       ``type(field).__mro__`` that keys ``SCALAR_MAP`` (an unsupported field
       already raised ``ConfigurationError`` in ``scalar_route``).
    2. If the field declares ``choices``, replace the scalar type with a
       generated ``Enum`` via ``convert_choices_to_enum(field, type_name)``.
    3. If ``effective_null``, widen to ``T | None``.

    Order matters: choices replaces ``py_type`` *before* null widening so
    nullable choice fields end up as ``EnumType | None``, not
    ``(str | None)`` collapsed away. The widening test reads
    ``effective_null`` (not ``field.null``) at every site, so a
    ``force_nullable`` override flips the choice enum's nullability for free.

    Args:
        field: A bound Django model field.
        type_name: The choice-enum prefix: the published GraphQL name of the
            ``DjangoType`` reading the column (``Meta.name``, else the class
            name; ``types/definition.py::surface_type_name``), or what a filter
            leaf names (``filters/inputs.py::_enum_prefix``). Threaded through so
            the choice-enum path can build a stable
            ``<TypeName><FieldName>Enum`` GraphQL name. Also threaded into
            the recursive ``base_field`` call on ``ArrayField``, so an
            inner choice-bearing element resolves under the outer field's
            name.
        force_nullable: Keyword-only nullability override tri-state.
            ``None`` (default) honors ``field.null``. ``True`` emits ``T | None`` regardless of the
            column (force nullable). ``False`` emits ``T`` regardless (force
            required). Sourced per field from ``Meta.nullable_overrides`` /
            ``Meta.required_overrides`` by ``types/base.py::_build_annotations``.
            Only the OUTER field's nullability is affected; the recursive
            ``ArrayField.base_field`` call is left unset, so the inner
            element nullability follows ``base_field.null``.

    Raises:
        ConfigurationError: triggered by any of the following:

            - ``Unsupported Django field type`` - no class in
              ``type(field).__mro__`` is in ``SCALAR_MAP``.
            - ``Nested ArrayField on ...`` - ``ArrayField`` whose
              ``base_field`` is itself an ``ArrayField`` (multi-dim arrays
              are not supported).
            - ``ArrayField on ... declares choices on the outer field`` -
              outer-array ``choices`` are ambiguous at the GraphQL
              boundary; declare choices on ``base_field`` instead.
            - ``HStoreField on ... declares choices`` - ``HStoreField``
              stores a ``dict[str, str | None]`` with no enum-able shape
              at the GraphQL boundary.
            - ``<Model>.<field> uses Django's grouped-choices form`` -
              raised from ``convert_choices_to_enum`` for nested-tuple
              choice declarations.

    """
    # The tri-state collapses to a single boolean computed once: the
    # override (``force_nullable``) wins when set, otherwise the column's
    # ``field.null`` drives the decision. Every outer widening site below
    # reads ``effective_null`` so the override applies uniformly across the
    # ArrayField / HStoreField / choice / scalar branches without per-branch
    # override logic.
    effective_null = field.null if force_nullable is None else force_nullable
    route = scalar_route(field)
    # The recursive call into ``base_field`` re-enters ``convert_scalar`` and
    # naturally inherits choice substitution and inner-null widening; the outer
    # ``effective_null`` widens the resulting ``list[inner]`` here. The
    # recursion is left ``force_nullable``-unset so the inner element
    # nullability follows ``base_field.null`` and is NOT affected by the
    # outer override.
    if isinstance(route, ArrayRoute):
        refuse_nested_array(field, route.element)
        if field.choices:
            raise ConfigurationError(
                f"ArrayField on {_field_label(field)} declares choices on the outer "
                "field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices "
                "on base_field for an element-level enum, or leave the field out with Meta.fields "
                "/ Meta.exclude (a FilterSet's ArrayFilter can still filter it).",
            )
        inner = convert_scalar(route.element, type_name)
        result = GenericAlias(list, (inner,))
        return result | None if effective_null else result
    # HStore stores ``dict[str, str | None]`` with no enum-able GraphQL shape,
    # so outer ``choices`` are rejected before returning ``JSON``.
    if isinstance(route, HStoreRoute):
        if field.choices:
            raise ConfigurationError(
                f"HStoreField on {_field_label(field)} declares choices; "
                f"HStore stores a dict[str, str | None] with no enum-able shape at the "
                f"GraphQL boundary. Drop the choices declaration or model the constrained "
                f"shape with a separate field.",
            )
        json_type = strawberry.scalars.JSON
        return json_type | None if effective_null else json_type
    # The ``SCALAR_MAP`` arm resolved through the lookup the filter-input
    # converter shares, so a column resolves to the same scalar on both sides.
    py_type: object = route.scalar
    if route.choices:
        py_type = convert_choices_to_enum(field, type_name)
    if effective_null:
        py_type = optional_annotation(py_type)
    return py_type


def _field_output_type_for(field: "ModelField") -> type[DjangoFileType] | None:
    """Return the ``FIELD_OUTPUT_TYPE_MAP`` output object for ``field``, or ``None``.

    Walks ``type(field).__mro__`` against ``FIELD_OUTPUT_TYPE_MAP`` exactly as
    ``scalar_for_field`` walks ``SCALAR_MAP`` -- so an ``ImageField`` (and any
    consumer ``ImageField`` subclass) resolves to ``DjangoImageType`` before
    ``FileField`` is reached -- and returns ``None`` for a non-file column. Both
    walks compose ``utils/truth.py::mro_entry``, so the map walk is written once.
    """
    entry = truth.mro_entry(FIELD_OUTPUT_TYPE_MAP, truth.class_of(field))
    return None if entry is None else entry[1]


def convert_field_output(
    field: "ConcreteField",
    type_name: str,
    *,
    force_nullable: bool | None = None,
    expose_filesystem_path: bool = False,
) -> object:
    """Map a non-relation Django column to its read-output annotation.

    The read-output entry point ``types/base.py::_build_annotations`` calls for
    every non-relation column. Routing, not an expansion of
    ``convert_scalar``:

    - A ``FileField`` / ``ImageField`` resolves through ``FIELD_OUTPUT_TYPE_MAP``
      to ``DjangoFileType`` / ``DjangoImageType``, nullable by DEFAULT as
      ``<object> | None`` (spec-037 Decision 4): the generated parent resolver
      returns ``None`` for an empty / falsy ``FieldFile`` -- reachable even on a
      ``null=False, blank=False`` column (legacy rows, direct
      ``Model.objects.create()``, fixtures store ``""``) -- so the annotation
      must be nullable to match. ``force_nullable`` still wins when set, so
      ``Meta.required_overrides`` (``force_nullable=False``) is the explicit
      opt-in for a caller asserting a stronger non-empty invariant.
    - Every other column delegates unchanged to ``convert_scalar`` -- keeping
      ``convert_scalar`` / ``scalar_for_field`` / ``SCALAR_MAP`` scalar-only so
      the shared filter-input path never sees an output object.

    ``force_nullable`` carries the same ``Meta.nullable_overrides`` /
    ``Meta.required_overrides`` tri-state as ``convert_scalar``, threaded
    through unchanged so ``_build_annotations`` swaps one call for the other.

    ``expose_filesystem_path`` is the per-column ``Meta.filesystem_path_fields``
    opt-in (spec-048 Decision 2): true swaps the resolved output object for its
    path-bearing sibling through ``FILESYSTEM_PATH_OUTPUT_TYPE_MAP``. It is
    inert on a non-file column, which cannot happen -- the Meta validator
    rejects a non-file target -- so the flag is read only inside the file
    branch and never silently changes a scalar's annotation.
    """
    output_type = _field_output_type_for(field)
    if output_type is None:
        return convert_scalar(field, type_name, force_nullable=force_nullable)
    if expose_filesystem_path:
        output_type = FILESYSTEM_PATH_OUTPUT_TYPE_MAP[output_type]
    # A non-null SDL would turn the generated resolver's empty-file ``None`` into a top-level
    # "Cannot return null for non-nullable field" error (``resolvers._make_file_resolver``).
    file_effective_null = True if force_nullable is None else force_nullable
    return output_type | None if file_effective_null else output_type


def _is_enum_reserved_member(name: str, *, enum_name: str | None = None) -> bool:
    """Return whether ``name`` is a member name Python's ``enum`` reserves.

    ``Enum(cls_name, {name: value})`` refuses ``"mro"`` outright and reserves every
    single-underscore ``_sunder_`` name for directives. Python 3.11+ also treats
    ``_<cls_name>__private`` as a class attribute instead of a member. Some of
    these names raise, while recognised directives and class-private names are
    silently omitted from the enum. All must receive the same ``MEMBER_`` prefix
    used for GraphQL-reserved and introspection-prefixed names. Applying the
    private-name rule on Python 3.10 too keeps the generated schema stable across
    every supported interpreter.

    The shape checks mirror ``enum``'s private predicates rather than importing
    them. ``__dunder__`` names are already handled by the ``startswith("__")``
    branch in :func:`_sanitize_member_name`.
    """
    # ``len(name) > 1`` is enough to keep ``name[1]`` in range: a two-character name fails
    # ``name[1] != "_"`` anyway, so the outcome equals ``enum``'s own ``len(name) > 2``.
    if name == "mro" or (
        len(name) > 1 and name[0] == "_" and name[-1] == "_" and name[1] != "_" and name[-2] != "_"
    ):
        return True
    if enum_name is None:
        return False
    private_prefix = f"_{enum_name}__"
    return (
        len(name) > len(private_prefix)
        and name.startswith(private_prefix)
        and (name[-1] != "_" or name[-2] != "_")
    )


def _sanitize_member_name(value: object, *, enum_name: str | None = None) -> str:
    """Produce a Strawberry / GraphQL-safe enum member from a Django choice value.

    The choice value (DB-side, not the human label) is the input. We coerce
    to ``str`` so ``IntegerChoices`` work, replace any non-ASCII
    identifier characters with ``_``, name the empty string ``BLANK``,
    prefix with ``MEMBER_`` if the result starts with a digit, and prefix
    with an underscore if it collides with a Python keyword. GraphQL-reserved enum
    values (``true``, ``false``, ``null``), introspection-prefixed
    names, and names Python's ``enum`` reserves are also prefixed so Strawberry
    can build the schema without a raw ``enum`` crash or a silently dropped
    member. ``enum_name`` enables detection of the class-specific
    ``_<enum_name>__private`` namespace used by Python's name mangling.
    Sanitization is a function of the raw value, not the label, so schema
    member names stay stable when consumers edit human-readable labels.

    Rules apply in this order: (1) ASCII non-identifier characters
    rewritten to ``_``; (2) the empty string becomes ``BLANK`` and a
    leading-digit result is prefixed with ``MEMBER_``; (3) Python-keyword
    result prefixed with ``_``;
    (4) GraphQL-reserved (``true`` / ``false`` / ``null``),
    ``__``-prefixed, or Python-``enum``-reserved (``mro``, ``_sunder_``, or the
    generated class's private namespace; see :func:`_is_enum_reserved_member`)
    result prefixed with ``MEMBER_``.
    The order is load-bearing because the keyword-and-reserved rewrites in
    steps 3 and 4 cannot collapse into a single condition without changing
    how downstream collision detection (see ``convert_choices_to_enum``)
    categorises ambiguous values.
    """
    sanitized = _NON_IDENT.sub("_", str(value))
    if not sanitized:
        # ``""`` is the value a blank-admitting field stores, declared or admitted
        # (``build_enum_from_choices``'s ``include_blank``), so both spell one member.
        sanitized = "BLANK"
    elif sanitized[0].isdigit():
        sanitized = f"MEMBER_{sanitized}"
    if keyword.iskeyword(sanitized):
        sanitized = f"_{sanitized}"
    if (
        sanitized.casefold() in _GRAPHQL_RESERVED_ENUM_VALUES
        or sanitized.startswith("__")
        or _is_enum_reserved_member(sanitized, enum_name=enum_name)
    ):
        sanitized = f"MEMBER_{sanitized}"
    return sanitized


def build_enum_from_choices(
    choice_pairs: "Iterable[object]",
    enum_name: str,
    *,
    source_label: str,
    include_blank: bool = False,
) -> type[Enum]:
    """Build a Strawberry ``Enum`` from a flat ``(value, label)`` choice sequence.

    The shared choices -> enum CORE reused by the read-side model-choice path
    (``convert_choices_to_enum``, keyed + cached per ``(model, field_name)``), the
    serializer-only ``ChoiceField`` / ``MultipleChoiceField`` path
    (``rest_framework/serializer_converter.py``, keyed by the descriptor-derived name),
    and a ``ModelForm`` choice field admitting fewer of its column's values
    (``forms/inputs.py::_form_choice_annotation``, one enum per input class). All build a
    GraphQL-safe enum from the SAME rules, so the grouped-form rejection, the
    value-not-label sanitization, and the sanitize-collision guard cannot drift between
    the flavors:

    1. leave out every ``None``-valued pair (the ``(None, label)`` pair ``Choices.__empty__``
       adds, or one declared by hand): it labels the empty option, which travels as ``null``
       where the field is nullable and as ``BLANK`` where it admits ``""``, so it gets no
       member; reject a sequence left empty;
    2. reject Django's grouped-choices form (a ``(group_label, [(value, label), ...])``
       nested tuple - detected on ``label`` being a list / tuple, the load-bearing
       distinction: in the grouped form the *value* slot is the group name, so testing
       it would false-negative);
    3. when ``include_blank`` is set and no declared value is ``""``, prepend the
       ``("", "")`` pair (Django's ``Field.formfield`` prepends its blank choice the same
       way): the field admits the empty string, so the enum must carry it;
    4. sanitize member names from choice VALUES (not labels) so a label edit does not
       churn the GraphQL schema; reject two values that sanitize to one member (``""``
       sanitizes to ``BLANK``, so a declared ``"BLANK"`` value beside it is rejected);
    5. build the ``Enum`` and decorate with ``strawberry.enum``.

    ``include_blank`` is the caller's answer to "does this field admit the empty string?": a model
    column per ``_column_admits_empty_string`` (``convert_choices_to_enum``), or a serializer
    field with ``allow_blank=True``
    (``rest_framework/serializer_converter.py::_serializer_choice_enum``).

    ``source_label`` names the offending field in every raised message
    (``"Model.field"`` for the read side, the serializer field name for the serializer
    side), so the two callers share one message shape. The caller owns caching /
    registry keying (the two key spaces - ``(model, field_name)`` vs the descriptor-
    derived enum name - stay separate).

    Raises:
        ConfigurationError: empty sequence (or one holding only ``None``-valued pairs),
            grouped-choices form, or two values that sanitize to the same enum member.

    """
    normalized_pairs = _normalize_choice_pairs(choice_pairs, source_label=source_label)
    _insert_blank_pair(normalized_pairs, include_blank=include_blank)

    members: dict[str, object] = {}
    collisions: dict[str, list[object]] = {}
    for value, _label in normalized_pairs:
        member = _sanitize_member_name(value, enum_name=enum_name)
        if member in members:
            collisions.setdefault(member, [members[member]]).append(value)
        else:
            members[member] = value
    if collisions:
        details = ", ".join(
            f"{truth.render(member)} from values "
            f"[{', '.join(sorted(truth.render(value) for value in vals))}]"
            for member, vals in sorted(collisions.items())
        )
        raise ConfigurationError(
            f"{source_label} choices sanitize to the same enum member: "
            f"{details}.  Rename one side or split into separate fields.",
        )
    # The metaclass call ``Enum(enum_name, members)`` makes, spelled out: its type is the
    # ``type[Enum]`` the functional API returns, where a checker reading ``Enum(...)``
    # with a non-literal name either rejects it or types an ``Enum`` member.
    enum_cls = EnumMeta.__call__(Enum, enum_name, members)
    return strawberry.enum(enum_cls)


def _is_choice_group(label: object) -> TypeGuard[list[object] | tuple[object, ...]]:
    """Return whether a choice entry's second slot holds a group's inner pairs.

    Django's grouped-choices form is ``(group_label, [(value, label), ...])``. In the flat form
    the second element is always a label; in the grouped form it is a sequence of
    ``(value, label)`` pairs. Detecting on the second slot rather than the first is the
    load-bearing distinction: in the grouped form the first slot is the human-readable group
    name (a string), so testing it produces a false negative.
    """
    return truth.is_one_of(label, (list, tuple))


def _unpack_choice_entry(entry: object, *, source_label: str) -> tuple[object, object]:
    """Return one choice entry as its ``(value, label)`` pair, refusing a malformed entry.

    A text atom (``utils/_narrowing.py::is_text_atom``: text, a bytes-like value,
    or a lazy translation ``Promise``) is malformed even at length two, where
    unpacking would read its two characters (or byte integers) as a pair; every
    ``Promise`` counts whatever result class it wraps, so a ``lazy(..., tuple)``
    entry is refused too. A ``SimpleLazyObject`` entry is judged as the object it
    stands for (``utils/lazy.py::unwrap_lazy_object``).
    """
    malformed = is_text_atom(unwrap_lazy_object(entry))
    value: object = None
    label: object = None
    if not malformed:
        if is_iterable(entry):
            # Two-name unpacking documents exactly these two failures: an
            # iterable whose ``__iter__`` yields no iterator (``TypeError``) and
            # a wrong-length entry (``ValueError``).
            try:
                value, label = entry
            except (TypeError, ValueError):
                malformed = True
        else:
            malformed = True
    if malformed:
        raise ConfigurationError(
            f"{source_label} declares a malformed choice {truth.render(entry)}; "
            "choices must be a flat sequence of (value, label) pairs.",
        )
    return value, label


def _normalize_choice_pairs(
    choice_pairs: "Iterable[object]",
    *,
    source_label: str,
    flatten_groups: bool = False,
) -> list[tuple[object, object]]:
    """Return a choice sequence as flat ``(value, label)`` pairs, rejecting every malformed form.

    Steps 1 and 2 of ``build_enum_from_choices`` (an empty sequence, a malformed entry, Django's
    grouped-choices form), shared with ``choice_column_values`` so a column's listed
    values are read through the same checks, with the same messages, as its enum.

    ``flatten_groups`` answers "which values does the column list?" rather than "can the read
    enum be built?": each group of Django's grouped-choices form (a ``(None, [...])`` group
    included) is expanded one level, in order, every inner entry passing the same
    malformed-entry check (Django's ``Field.flatchoices`` rule, which ``Field.validate`` reads).
    Without it the grouped form is refused, since the read enum supports only the flat form.

    A ``None``-valued pair (the ``(None, label)`` pair ``Choices.__empty__`` adds to
    ``.choices``, or one declared by hand) is the label of the empty option, never a value, so it
    is left out: the empty option travels as ``null`` where the field is nullable and as the
    ``BLANK`` member where it admits ``""``. The test is identity, so a declared ``""`` and an
    ``IntegerChoices`` ``0`` stay. A sequence holding nothing but such pairs is empty.
    """
    pairs = tuple(choice_pairs)
    normalized_pairs: list[tuple[object, object]] = []
    for entry in pairs:
        value, label = _unpack_choice_entry(entry, source_label=source_label)
        if flatten_groups and _is_choice_group(label):
            normalized_pairs.extend(
                _unpack_choice_entry(inner, source_label=source_label) for inner in label
            )
            continue
        normalized_pairs.append((value, label))

    for _value, label in normalized_pairs:
        if _is_choice_group(label):
            raise ConfigurationError(
                f"{source_label} uses Django's grouped-choices "
                "form (nested tuples for option groups). Only the flat "
                "(value, label) form is supported; flatten the choices source or split into "
                "separate fields.",
            )

    empty_labels = [label for value, label in normalized_pairs if value is None]
    value_pairs = [(value, label) for value, label in normalized_pairs if value is not None]
    if not value_pairs:
        only_empty = (
            ", holding only the empty option "
            f"{', '.join(truth.render(label) for label in empty_labels)} (a None value labels "
            "the empty option and is never a member)"
            if empty_labels
            else ""
        )
        raise ConfigurationError(
            f"{source_label} declares choices but the sequence is empty{only_empty}; choices must "
            "be a non-empty flat sequence of (value, label) pairs.",
        )
    return value_pairs


def _insert_blank_pair(
    normalized_pairs: list[tuple[object, object]],
    *,
    include_blank: bool,
) -> None:
    """Prepend ``("", "")`` when ``include_blank`` is set and no declared value is ``""``."""
    if include_blank and not any(
        truth.is_instance(value, str) and value == "" for value, _label in normalized_pairs
    ):
        normalized_pairs.insert(0, ("", ""))


def _column_admits_empty_string(field: "ConcreteField") -> bool:
    """Return whether a column admits ``""``: Django's own text-column blank predicate.

    ``blank=True`` on a type that stores empty strings; an ``IntegerChoices`` column with
    ``blank=True`` admits only ``None``, never ``""``. It is the ``include_blank`` a choice
    column's read enum (``convert_choices_to_enum``) is built with.
    """
    return bool(field.blank and field.empty_strings_allowed)


def choice_column_pairs(field: "ConcreteField") -> list[tuple[object, object]]:
    """Return the ``(value, label)`` pairs a choice column lists, in order.

    The column's choice pairs with every group of Django's grouped-choices form flattened in
    order (Django's ``Field.flatchoices``, which ``Field.validate`` checks a stored value
    against), never a ``None``-valued pair (it labels the empty option), plus ``("", "")`` when
    ``_column_admits_empty_string`` holds and no listed value is ``""``. Every entry, a group's
    inner entries included, passes the same ``_normalize_choice_pairs`` checks as the read enum,
    so a malformed column raises the same specific ``ConfigurationError``. For a flat column the
    pairs are exactly the ones ``convert_choices_to_enum`` builds its members from; a grouped
    column has pairs but no read enum. No enum is built or registered, so a write-side caller
    cannot claim the column enum's GraphQL name; a caller publishing a subset of the pairs builds
    its own enum through ``build_enum_from_choices``
    (``forms/inputs.py::_form_choice_annotation``).
    """
    include_blank = _column_admits_empty_string(field)
    choice_source = field.choices or []
    pairs = _normalize_choice_pairs(
        choice_source,
        source_label=_field_label(field),
        flatten_groups=True,
    )
    _insert_blank_pair(pairs, include_blank=include_blank)
    return pairs


def choice_column_values(field: "ConcreteField") -> list[object]:
    """Return the values a choice column lists, in order: the write side's admissible set.

    The values of ``choice_column_pairs``: for a flat column exactly the member values
    ``convert_choices_to_enum`` builds; a grouped column has values but no read enum.
    """
    return [value for value, _label in choice_column_pairs(field)]


def choice_column_is_grouped(field: "ConcreteField") -> bool:
    """Return whether a column declares Django's grouped-choices form, which has no read enum.

    An entry is a group when its second slot holds the group's inner pairs (``_is_choice_group``);
    a malformed entry is no group here and is refused by whichever check reads it next.
    """
    entries: tuple[object, ...] = tuple(field.choices or [])
    return any(
        is_list_or_tuple(entry)
        and len(entry) == _CHOICE_ENTRY_LENGTH
        and _is_choice_group(entry[1])
        for entry in entries
    )


def choice_enum_name(type_name: str, field_name: str) -> str:
    """Return the generated choice-enum name ``<TypeName><FieldName>Enum``.

    ``<TypeName>`` is the prefix the caller names: a model column's is the published
    name of the type that reads it (``Meta.name``, else the class name), or, for a
    filter leaf no type owns, its set's class name.

    Every flavor (read-side model column, serializer choice field, form choice field) publishes
    its generated choice enum into the one schema namespace under this name, so enums for the
    same type and field name collide or dedupe by the same rule.
    """
    return f"{type_name}{pascal_case(field_name)}Enum"


def convert_choices_to_enum(field: "ConcreteField", type_name: str) -> type[Enum]:
    """Generate (or fetch from registry) a Strawberry ``Enum`` for ``field.choices``.

    1. Cache check on ``(field.model, field.name)``; return cached on hit.
    2. Compute the enum name via ``choice_enum_name(type_name, field.name)``.
    3. Delegate to the shared ``build_enum_from_choices`` core (empty / grouped-form
       rejection, the ``BLANK`` member when ``_column_admits_empty_string``, value-based
       sanitization, sanitize-collision guard, ``Enum`` build).
    4. Cache via ``registry.register_enum`` and return the enum class.

    The first caller to read a given ``(model, field_name)`` (a ``DjangoType``
    under its published name, or a ``FilterSet`` leaf under its owner's published
    name, else its set's class name) wins the enum's GraphQL name; sibling types
    and filters pointing at the same column receive the cached enum unchanged.
    The build rules are single-sited in ``build_enum_from_choices`` so the
    serializer-only ``ChoiceField`` path applies the identical grouped-form /
    sanitization / collision contract.

    Raises:
        ConfigurationError: empty ``field.choices``, Django's grouped-choices form, or
            two choice values that sanitize to the same enum member (all raised by
            ``build_enum_from_choices``).

    """
    model = field.model
    field_name = field.name
    cached = registry.get_enum(model, field_name)
    if cached is not None:
        return cached

    enum_name = choice_enum_name(type_name, field_name)
    choice_source = field.choices or []
    include_blank = _column_admits_empty_string(field)
    enum_cls = build_enum_from_choices(
        choice_source,
        enum_name,
        source_label=_field_label(field),
        include_blank=include_blank,
    )
    registry.register_enum(model, field_name, enum_cls)
    return enum_cls


def resolved_relation_annotation(
    field: "ModelField",
    target_type: "type[DjangoType]",
    *,
    field_meta: FieldMeta | None = None,
) -> object:
    """Return the concrete annotation for ``field`` pointing at ``target_type``."""
    meta = field_meta or FieldMeta.from_django_field(field)
    if meta.is_many_side:
        return GenericAlias(list, (target_type,))
    if meta.nullable:
        return target_type | None
    return target_type
