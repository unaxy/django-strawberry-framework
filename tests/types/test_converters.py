"""Converter tests for scalars, enums, relations, PostgreSQL containers, and file/image output objects.

Legal column shapes read real fakeshop fields: ``scalars.MediaSpecimen`` for
the file/image rows (``attachment``, ``image``, the ``blank``-only
``optional_attachment`` and the ``null``-only ``spare_image``), and
``ScalarSpecimen`` / ``NullableScalarSpecimen`` for the text and scalar
delegation rows. Primary-type relation resolution over HTTP lives in
``examples/fakeshop/test_query/test_library_api.py``
(``test_shelf_books_relation_resolves_to_primary_book_type_over_http``);
``BigAutoField -> Int`` lives in
``examples/fakeshop/test_query/test_scalars_api.py``
(``test_scalar_specimen_id_maps_big_auto_pk_to_int``).

The synthetic models that remain carry column shapes no fakeshop model can
declare, because *exposing* each column on a ``DjangoType`` is what cannot be
built. The unsupported-field, ``DurationField`` and ``BinaryField`` owners pin
the ``Unsupported Django field type`` raise in
``django_strawberry_framework/types/converters.py::scalar_for_field``; the
``FakeArrayField`` / ``FakeHStoreField`` owners pin, on SQLite, the
PostgreSQL container branches of
``django_strawberry_framework/types/converters.py::convert_scalar``; and
``ChoiceFixture``'s hyphenated, digit-led and keyword choice values pin
``django_strawberry_framework/types/converters.py::_sanitize_member_name``,
which ``Book.circulation_status`` never reaches. The ``CharField`` /
``ImageField`` subclass owners model a legal consumer shape no fakeshop model
carries; they pin the MRO walks in ``scalar_for_field`` and
``django_strawberry_framework/types/converters.py::_field_output_type_for``.
This module also keeps the diagnostic labels, ``force_nullable``, and
import-order primary-resolution traps that introspection of the shipped schema
cannot phrase, and the choice-enum rules: registry caching keyed on
``(model, field_name)``, grouped-choices rejection on the read enum beside the
same column's values listed flattened, the ``BLANK`` member a blank-admitting
column carries, and a ``None``-valued choice (``Choices.__empty__`` or
hand-declared) getting no member on the column enum, an ``ArrayField`` element
and a ``null=True`` column's read and write.
"""

import datetime
import enum
import itertools
import re
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, NoReturn, TypedDict, cast, get_args

import pytest
import strawberry
from apps.products.models import Category, Item
from apps.scalars.models import MediaSpecimen, NullableScalarSpecimen, ScalarSpecimen
from django.db import connection, models
from django.db.models.expressions import Combinable
from strawberry.types import get_object_definition
from typing_extensions import Never, override

from django_strawberry_framework import (
    BigInt,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters.inputs import _scalar_from_model_field
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.converters import (
    FIELD_OUTPUT_TYPE_MAP,
    FILESYSTEM_PATH_OUTPUT_TYPE_MAP,
    SCALAR_MAP,
    ArrayRoute,
    DjangoFilePathType,
    DjangoFileType,
    DjangoImagePathType,
    DjangoImageType,
    HStoreRoute,
    MapRoute,
    _column_admits_empty_string,
    _field_label,
    _field_output_type_for,
    _sanitize_member_name,
    build_enum_from_choices,
    choice_column_is_grouped,
    choice_column_values,
    choice_enum_name,
    convert_choices_to_enum,
    convert_field_output,
    convert_scalar,
    scalar_for_field,
    scalar_route,
)
from django_strawberry_framework.utils._narrowing import enum_value, require
from django_strawberry_framework.utils.typing import object_result
from tests._idioms import definition_raises, is_object_dict, is_object_list, resolver_function
from tests._postgres_fields import FakeArrayField, FakeHStoreField, patch_array_field

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.utils.choices import _ChoicesInput

    from django_strawberry_framework.utils.typing import ConcreteField


def _concrete_field(model: type[models.Model], name: str) -> "ConcreteField":
    """Read ``model``'s concrete column ``name`` (``get_field`` also returns reverse relations)."""
    field = model._meta.get_field(name)
    assert isinstance(field, models.Field)
    return field


class _UnreadableAttributeField(models.Field[object, object]):
    """A real Django field whose read of one attribute raises, armed once construction is done."""

    _unreadable: str | None = None

    def __init__(
        self,
        unreadable: str,
        *,
        name: str | None = None,
        choices: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(name=name, choices=choices)
        self._unreadable = unreadable

    @override
    def __getattribute__(self, name: str) -> object:
        if name == object.__getattribute__(self, "_unreadable"):
            raise RuntimeError(f"{name} exploded")
        return object_result(super().__getattribute__, name)


_app_label_counter = itertools.count(1)


def _unique_app_label(base: str) -> str:
    """Return a unique ``app_label`` per call to suppress Django's ``Model already registered`` warning.

    Multiple tests in this module declare same-named synthetic ``managed=False``
    models (canonically ``_Owner``) under a shared ``app_label`` such as
    ``test_choice_enums``. Django's app registry raises a ``RuntimeWarning``
    on the second and subsequent registrations because the
    ``(app_label, model_name)`` key collides. Routing the ``app_label``
    through this helper namespaces each test's synthetic model with a
    monotonically increasing suffix so the registry sees a fresh key per
    call. The choice fixture itself (``ChoiceFixture``) is function-scoped
    and does not use this helper: ``tests/conftest.py::_restore_app_registry``
    retires its ``test_choice_enums`` label after each test.
    """
    return f"{base}__{next(_app_label_counter)}"


# The clears cover the type + enum dicts and the connection-type cache but not
# Django's app registry: the ``ChoiceFixture`` model is declared per test under a
# synthetic ``app_label`` that ``tests/conftest.py::_restore_app_registry`` retires
# afterwards.
pytestmark = pytest.mark.usefixtures("isolate_global_registry")


@pytest.fixture
def choice_fixture_model() -> type[models.Model]:
    """Build a fresh Django model with two choice columns for each test.

    Function scope keeps the shared-enum assertions order-independent: every test
    gets its own ``ChoiceFixture`` class, so no enum cached against one test's class
    can satisfy (or poison) another's, and ``tests/conftest.py::_restore_app_registry``
    retires the ``test_choice_enums`` label after each test so the re-declaration
    never warns.

    The choice values are deliberately diverse to exercise sanitization:

    - ``active`` / ``archived``      \u2014 plain identifiers (the happy path).
    - ``first-name``                  \u2014 hyphen \u2192 underscore replacement.
    - ``123abc``                      \u2014 leading digit \u2192 ``MEMBER_`` prefix.
    - ``class``                       \u2014 Python keyword \u2192 underscore prefix.
    """
    STATUS_CHOICES = (
        ("active", "Active"),
        ("archived", "Archived"),
        ("first-name", "First-name"),
        ("123abc", "123abc"),
        ("class", "Class"),
    )

    class ChoiceFixture(models.Model):
        status: "models.TextField[str | Combinable, str]" = models.TextField(
            choices=STATUS_CHOICES,
        )
        nullable_status: "models.TextField[str | Combinable | None, str | None]" = (
            models.TextField(choices=STATUS_CHOICES, null=True)  # noqa: DJ001 - NULL is the fixture input
        )

        class Meta:
            app_label = "test_choice_enums"

    return ChoiceFixture


@pytest.fixture
def grouped_choice_field(choice_fixture_model: type[models.Model]) -> "Iterator[ConcreteField]":
    """Yield ``status`` with grouped-choices monkeypatched in.

    Django's grouped-choices form is a sequence of
    ``(group_label, [...inner_pairs])`` tuples. The patch is reversed in
    teardown so subsequent tests see the original flat choices.
    """
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = (("Active States", (("active", "Active"), ("archived", "Archived"))),)
    yield field
    field.choices = original


# ---------------------------------------------------------------------------
# Choice enum behavior
# ---------------------------------------------------------------------------


def test_choice_field_generates_strawberry_enum(choice_fixture_model: type[models.Model]) -> None:
    """A ``DjangoType`` over the fixture model produces an enum-typed choice annotation.

    The enum is named per ``f"{type_name}{PascalCase(field_name)}Enum"``.
    """

    class FixtureType(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    enum_cls = FixtureType.__annotations__["status"]
    assert isinstance(enum_cls, type)
    assert issubclass(enum_cls, enum.Enum)
    assert enum_cls.__name__ == "FixtureTypeStatusEnum"
    # DB values are preserved on the enum's ``.value`` attribute.
    assert {enum_value(member) for member in enum_cls} == {
        "active",
        "archived",
        "first-name",
        "123abc",
        "class",
    }


def test_choice_enum_cached_in_registry_keyed_by_model_field(
    choice_fixture_model: type[models.Model],
) -> None:
    """Once generated, the enum is cached on ``(model, field_name)``.

    ``registry.get_enum`` returns the identical object on subsequent reads.
    """

    class FixtureType(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    cached = registry.get_enum(choice_fixture_model, "status")
    assert cached is FixtureType.__annotations__["status"]
    assert registry.get_enum(choice_fixture_model, "status") is cached


def test_two_djangotypes_reading_same_choice_field_share_one_enum(
    choice_fixture_model: type[models.Model],
) -> None:
    """Two ``DjangoType``s pointing at the same column receive the cached enum.

    The first type wins the enum's GraphQL name; later types reuse the
    same object. The enum's ``__name__`` is set by whichever type
    registered first, even though runtime behaviour is identical.
    """

    class FixtureTypeA(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    # Drop FixtureTypeA from the registry's type/model maps but leave
    # the enum cache intact so we can verify cross-type enum reuse via
    # FixtureTypeB. ``unregister`` skips ``_enums``.
    registry.unregister(FixtureTypeA)

    class FixtureTypeB(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    assert FixtureTypeA.__annotations__["status"] is FixtureTypeB.__annotations__["status"]
    # First type wins the enum name regardless of who looks it up next.
    assert isinstance(FixtureTypeA.__annotations__["status"], type)
    assert FixtureTypeA.__annotations__["status"].__name__ == "FixtureTypeAStatusEnum"


def test_grouped_choices_form_rejected(grouped_choice_field: "ConcreteField") -> None:
    """Django's grouped-choices form raises ``ConfigurationError``, not a silent flatten."""
    with pytest.raises(ConfigurationError, match="grouped-choices"):
        convert_choices_to_enum(grouped_choice_field, "FixtureType")


@pytest.mark.parametrize(
    ("choice_pairs", "expected_message"),
    [
        pytest.param(
            ["a"],
            "declares a malformed choice 'a';",
            id="scalar-entry",
        ),
        pytest.param(
            [("a",)],
            "declares a malformed choice ('a',);",
            id="short-pair",
        ),
        pytest.param(
            [("a", "A", "extra")],
            "declares a malformed choice ('a', 'A', 'extra');",
            id="long-pair",
        ),
    ],
)
def test_build_enum_rejects_malformed_choice_pairs(
    choice_pairs: object,
    expected_message: str,
) -> None:
    """Each malformed choice shape produces its own typed configuration failure."""
    with pytest.raises(ConfigurationError, match=re.escape(expected_message)):
        # basedpyright: the malformed choice sequence is the hostile input under test;
        # build_enum_from_choices types the parameter as Iterable[object]
        build_enum_from_choices(choice_pairs, "FixtureTypeEnum", source_label="probe")  # pyright: ignore[reportArgumentType]


def test_build_enum_collision_message_runs_a_hostile_choice_repr() -> None:
    """A colliding choice value is rendered by its own ``__repr__``, whose error propagates."""

    class HostileChoice:
        @override
        def __str__(self) -> str:
            return "a"

        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr should not escape")

    with pytest.raises(RuntimeError, match="repr should not escape"):
        build_enum_from_choices(
            [("a", "A"), (HostileChoice(), "Hostile")],
            "FixtureTypeEnum",
            source_label="probe",
        )


def test_scalar_route_names_each_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """``scalar_route`` names the ``convert_scalar`` arm a column takes, with that arm's data.

    The containers win over ``SCALAR_MAP`` (each double subclasses ``models.Field``, which
    keys no map row); a map column carries the matched MRO ancestor, its scalar, and whether
    the choice enum replaces it.
    """
    patch_array_field(monkeypatch)
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class CustomTextField(models.TextField[str, str]):
        pass

    element: models.CharField[str, str] = models.CharField(max_length=5)
    assert scalar_route(FakeArrayField(element)) == ArrayRoute(element)
    assert scalar_route(FakeHStoreField()) == HStoreRoute()
    assert scalar_route(models.CharField()) == MapRoute(models.CharField, str, choices=False)
    assert scalar_route(models.CharField(choices=[("a", "A")])) == MapRoute(
        models.CharField,
        str,
        choices=True,
    )
    assert scalar_route(CustomTextField()) == MapRoute(models.TextField, str, choices=False)
    assert scalar_route(models.BigIntegerField()) == MapRoute(
        models.BigIntegerField,
        BigInt,
        choices=False,
    )


def test_scalar_route_rejects_an_unsupported_field() -> None:
    """An unsupported column raises the same ``ConfigurationError`` ``scalar_for_field`` raises."""
    field: models.DurationField[object, datetime.timedelta] = models.DurationField()
    with pytest.raises(ConfigurationError, match="Unsupported Django field type") as route_error:
        scalar_route(field)
    with pytest.raises(ConfigurationError) as lookup_error:
        scalar_for_field(field)
    assert str(route_error.value) == str(lookup_error.value)


def test_scalar_for_field_label_runs_a_hostile_field_name_str() -> None:
    """An unsupported field whose ``name`` cannot render propagates that render's error.

    A field of an unsupported class whose ``name`` raises from ``__str__`` and
    ``__repr__`` is malformed metadata no fakeshop model can declare; the label in
    ``django_strawberry_framework/types/converters.py::_field_label`` renders the name
    through its own ``__str__``, which is consumer behaviour.
    """

    class HostileMetadata:
        @override
        def __str__(self) -> str:
            raise RuntimeError("str should not escape")

        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr should not escape")

    class UnsupportedField(models.Field[object, object]):
        pass

    class Owner(models.Model):
        value = UnsupportedField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_hostile_converter")

    field = Owner._meta.get_field("value")
    # basedpyright: the planted non-string field name is the hostile input under test;
    # django-stubs types the slot as str
    field.name = HostileMetadata()  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(RuntimeError, match="str should not escape"):
        scalar_for_field(field)


def test_convert_choices_to_enum_propagates_hostile_choices_truthiness(
    choice_fixture_model: type[models.Model],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A choices container whose truthiness raises propagates that error."""

    class HostileChoices:
        def __bool__(self) -> bool:
            raise RuntimeError("bool should not escape")

    field = _concrete_field(choice_fixture_model, "status")
    monkeypatch.setattr(field, "choices", HostileChoices())
    with pytest.raises(RuntimeError, match="bool should not escape"):
        convert_choices_to_enum(field, "FixtureType")


def test_field_label_reads_the_model_name_truthfully() -> None:
    """A model metaclass's ``__name__`` hook never runs; unreadable field attributes propagate."""

    class _HostileModelMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__name__":
                raise RuntimeError("model name exploded")
            return object_result(super().__getattribute__, name)

    class _HostileModel(metaclass=_HostileModelMeta):
        pass

    class _UnreadableModel:
        @property
        def model(self) -> NoReturn:
            raise RuntimeError("model exploded")

        name = "field"

    class _UnreadableName:
        model = object

        @property
        def name(self) -> NoReturn:
            raise RuntimeError("name exploded")

    assert _field_label(type("Field", (), {"model": _HostileModel, "name": "field"})()) == (
        "_HostileModel.field"
    )
    with pytest.raises(RuntimeError, match="model exploded"):
        _ = _field_label(_UnreadableModel())
    with pytest.raises(RuntimeError, match="name exploded"):
        _ = _field_label(_UnreadableName())


def test_convert_scalar_propagates_unreadable_nullability_metadata() -> None:
    """A field whose ``null`` read raises propagates that error from ``convert_scalar``."""
    with pytest.raises(RuntimeError, match="null exploded"):
        _ = convert_scalar(_UnreadableAttributeField("null", name="field"), "OwnerType")


def test_choice_conversion_propagates_unrenderable_values_and_unreadable_field_metadata() -> None:
    """An unrenderable choice value and an unreadable ``field.model`` propagate their errors."""

    class _UnrenderableChoice:
        @override
        def __str__(self) -> str:
            raise RuntimeError("choice rendering exploded")

    with pytest.raises(RuntimeError, match="choice rendering exploded"):
        build_enum_from_choices(
            [(_UnrenderableChoice(), "label")],
            "FixtureEnum",
            source_label="probe",
        )

    unreadable_field = _UnreadableAttributeField("model", name="field", choices=[("a", "A")])

    with pytest.raises(RuntimeError, match="model exploded"):
        convert_choices_to_enum(unreadable_field, "FixtureType")


def test_choice_enum_name_derivation_propagates_a_hostile_type_name_format(
    choice_fixture_model: type[models.Model],
) -> None:
    """A type name whose ``__format__`` raises propagates that error."""

    class _HostileTypeName:
        @override
        def __format__(self, spec: str) -> str:
            raise RuntimeError("type name formatting exploded")

    field = _concrete_field(choice_fixture_model, "status")
    with pytest.raises(RuntimeError, match="type name formatting exploded"):
        # basedpyright: the unformattable type name is the hostile input under test;
        # convert_choices_to_enum types the parameter as str
        convert_choices_to_enum(field, _HostileTypeName())  # pyright: ignore[reportArgumentType]


def test_choice_enum_name_composes_type_and_pascal_cased_field_name() -> None:
    """The generated choice-enum name every flavor publishes is ``<TypeName><FieldName>Enum``."""
    assert choice_enum_name("ItemType", "status_code") == "ItemTypeStatusCodeEnum"


def _blank_choice_model(
    *,
    choices: object,
    blank: bool = False,
    null: bool = False,
) -> type[models.Model]:
    """Return a fresh model whose ``status`` column carries ``choices`` / ``blank`` / ``null``.

    The nullable column is its own declaration because its annotation carries ``None``.
    """
    # basedpyright: the malformed choices some callers pass are the hostile input under test;
    # django-stubs types choices as _ChoicesInput
    hostile_choices: _ChoicesInput = choices  # pyright: ignore[reportAssignmentType]
    if null:

        class NullableBlankChoiceFixture(models.Model):
            status: "models.TextField[str | Combinable | None, str | None]" = models.TextField(  # noqa: DJ001 - NULL is the fixture input
                choices=hostile_choices,
                blank=blank,
                null=True,
            )

            class Meta:
                app_label = _unique_app_label("test_blank_choice_enums")

        return NullableBlankChoiceFixture

    class BlankChoiceFixture(models.Model):
        status: "models.TextField[str | Combinable, str]" = models.TextField(
            choices=hostile_choices,
            blank=blank,
        )

        class Meta:
            app_label = _unique_app_label("test_blank_choice_enums")

    return BlankChoiceFixture


def _member_map(enum_cls: type[enum.Enum]) -> dict[str, object]:
    return {member.name: enum_value(member) for member in enum_cls}


def test_blank_admitting_text_choice_column_gets_blank_member() -> None:
    """A ``blank=True`` text choice column admits ``""``, so its enum carries ``BLANK``."""
    model = _blank_choice_model(choices=[("good", "Good"), ("worn", "Worn")], blank=True)
    enum_cls = convert_choices_to_enum(_concrete_field(model, "status"), "BlankFixtureType")
    assert _member_map(enum_cls) == {"BLANK": "", "good": "good", "worn": "worn"}
    # The member is prepended, as Django's ``Field.formfield`` prepends its blank choice.
    assert next(iter(enum_cls)).name == "BLANK"


def test_non_blank_text_choice_column_gets_no_blank_member() -> None:
    """A ``blank=False`` choice column does not admit ``""``, so no ``BLANK`` member."""
    model = _blank_choice_model(choices=[("good", "Good"), ("worn", "Worn")])
    enum_cls = convert_choices_to_enum(_concrete_field(model, "status"), "NonBlankFixtureType")
    assert _member_map(enum_cls) == {"good": "good", "worn": "worn"}


@pytest.mark.parametrize(
    "field_cls",
    [models.IntegerField, models.PositiveSmallIntegerField, models.BigIntegerField],
)
def test_integer_choice_column_with_blank_gets_no_blank_member(
    field_cls: type[models.Field[Never, object]],
) -> None:
    """An integer column with ``blank=True`` admits only ``None``, never ``""``."""

    class IntegerBlankChoiceFixture(models.Model):
        rank = field_cls(choices=[(1, "One"), (2, "Two")], blank=True, null=True)

        class Meta:
            app_label = _unique_app_label("test_blank_choice_enums")

    field = _concrete_field(IntegerBlankChoiceFixture, "rank")
    enum_cls = convert_choices_to_enum(field, "IntegerBlankFixtureType")
    assert _member_map(enum_cls) == {"MEMBER_1": 1, "MEMBER_2": 2}


@pytest.mark.parametrize(
    "choices",
    [[("", "Unassessed"), ("good", "Good")], [("good", "Good"), ("", "Unassessed")]],
    ids=["declared-first", "declared-last"],
)
def test_blank_column_with_declared_empty_choice_has_one_blank_member(
    choices: list[tuple[str, str]],
) -> None:
    """A ``blank=True`` column that already declares ``""`` keeps exactly one ``BLANK``."""
    model = _blank_choice_model(choices=choices, blank=True)
    enum_cls = convert_choices_to_enum(
        _concrete_field(model, "status"),
        "DeclaredEmptyFixtureType",
    )
    assert _member_map(enum_cls) == {"BLANK": "", "good": "good"}


def test_declared_empty_choice_is_not_duplicated_by_include_blank() -> None:
    """A declared ``("", label)`` already is the blank member; ``include_blank`` adds none."""
    enum_cls = build_enum_from_choices(
        [("", "Unassessed"), ("good", "Good")],
        "DeclaredBlankEnum",
        source_label="Fixture.status",
        include_blank=True,
    )
    assert _member_map(enum_cls) == {"BLANK": "", "good": "good"}


_CHOICE_COLUMN_CASES: "list[tuple[models.Field[Never, object], bool, list[object]]]" = [
    (models.TextField(choices=[("good", "Good")]), False, ["good"]),
    (models.TextField(choices=[("good", "Good")], blank=True), True, ["", "good"]),
    (models.TextField(choices=[("good", "Good"), ("", "Unassessed")]), False, ["good", ""]),
    (models.IntegerField(choices=[(1, "One")], blank=True, null=True), False, [1]),
]


@pytest.mark.parametrize(
    ("field", "admits", "values"),
    _CHOICE_COLUMN_CASES,
    ids=[
        "text-strict",
        "text-blank",
        "text-declared-empty",
        "integer-blank",
    ],
)
def test_choice_column_values(
    field: models.Field[Never, object],
    *,
    admits: bool,
    values: list[object],
) -> None:
    """A column's represented values are its choices plus ``""`` when it admits the empty string.

    A ``blank=False`` column that declares ``""`` represents it through the declared value; an
    integer column with ``blank=True`` admits only ``None``.
    """
    field.set_attributes_from_name("status")
    assert _column_admits_empty_string(field) is admits
    assert choice_column_values(field) == values


def test_choice_column_values_match_the_read_enum() -> None:
    """The represented values are exactly the read enum's member values, in member order."""
    model = _blank_choice_model(choices=[("good", "Good"), ("worn", "Worn")], blank=True)
    field = _concrete_field(model, "status")
    enum_cls = convert_choices_to_enum(field, "RepresentedFixtureType")
    assert choice_column_values(field) == [enum_value(member) for member in enum_cls]


@pytest.mark.parametrize("blank", [False, True], ids=["strict", "blank"])
@pytest.mark.parametrize(
    ("choices", "message"),
    [
        (["abc"], "declares a malformed choice 'abc'"),
        ([("a",)], r"declares a malformed choice \('a',\)"),
    ],
    ids=["bare-string", "one-tuple"],
)
def test_malformed_column_choices_keep_their_specific_message(
    choices: object,
    message: str,
    *,
    blank: bool,
) -> None:
    """A malformed choice is named on the column enum and the represented-value reader alike.

    The represented values are read through the enum's own choice checks, so neither path
    collapses the specific message into the generic "Could not inspect choices".
    """
    model = _blank_choice_model(choices=choices, blank=blank)
    field = _concrete_field(model, "status")
    with pytest.raises(ConfigurationError, match=message):
        convert_choices_to_enum(field, "MalformedFixtureType")
    with pytest.raises(ConfigurationError, match=message):
        choice_column_values(field)


_GROUPED_MESSAGE = re.escape(
    "BlankChoiceFixture.status uses Django's grouped-choices form (nested tuples for option groups). Only "
    "the flat (value, label) form is supported; flatten the choices source or split into "
    "separate fields.",
)


@pytest.mark.parametrize(
    ("choices", "blank", "values"),
    [
        ([("Fiction", [("a", "A"), ("b", "B")]), ("Other", [("c", "C")])], False, ["a", "b", "c"]),
        (
            [("Fiction", [("a", "A"), ("b", "B")]), ("Other", [("c", "C")])],
            True,
            [
                "",
                "a",
                "b",
                "c",
            ],
        ),
        ([(None, [("a", "A")]), ("z", "Z"), ("Other", [("c", "C")])], False, ["a", "z", "c"]),
        ([("Fiction", [("a", "A"), ("", "None yet")])], True, ["a", ""]),
    ],
    ids=[
        "groups-strict",
        "groups-blank",
        "none-label-group-beside-flat",
        "group-declares-empty",
    ],
)
def test_choice_column_values_flatten_groups_but_the_read_enum_refuses_them(
    choices: list[tuple[object, object]],
    *,
    blank: bool,
    values: list[object],
) -> None:
    """A grouped column lists its values flattened in group order; it still has no read enum.

    The write side asks whether the column lists a value (Django's ``flatchoices``), the read
    enum whether the form is flat; a ``(None, [...])`` group is a group, flattened the same way,
    and ``""`` follows the column's blank rule.
    """
    field = _concrete_field(_blank_choice_model(choices=choices, blank=blank), "status")
    assert choice_column_values(field) == values
    with pytest.raises(ConfigurationError, match=f"^{_GROUPED_MESSAGE}$"):
        convert_choices_to_enum(field, "GroupedFixtureType")


@pytest.mark.parametrize(
    ("choices", "message"),
    [
        ([("g", [("a", "A"), "bad"])], "declares a malformed choice 'bad'"),
        ([("g", [("a", "A"), ("b",)])], r"declares a malformed choice \('b',\)"),
    ],
    ids=["bare-string", "one-tuple"],
)
def test_malformed_choice_inside_a_group_keeps_its_specific_message(
    choices: object,
    message: str,
) -> None:
    """A group's inner entry passes the same malformed-entry check as a flat entry."""
    field = _concrete_field(_blank_choice_model(choices=choices), "status")
    with pytest.raises(ConfigurationError, match=message):
        choice_column_values(field)


@pytest.mark.parametrize(
    "read_column",
    [choice_column_values, choice_column_is_grouped],
    ids=["values", "is-grouped"],
)
def test_choice_column_readers_propagate_an_unreadable_choices_error(
    choice_fixture_model: type[models.Model],
    monkeypatch: pytest.MonkeyPatch,
    read_column: Callable[["ConcreteField"], object],
) -> None:
    """A choices container whose truthiness raises propagates its own exception unchanged."""

    class HostileChoices:
        def __bool__(self) -> bool:
            raise RuntimeError("choices truthiness exploded")

    field = _concrete_field(choice_fixture_model, "status")
    monkeypatch.setattr(field, "choices", HostileChoices())
    with pytest.raises(RuntimeError, match="choices truthiness exploded"):
        read_column(field)


def test_declared_blank_value_collides_with_blank_member() -> None:
    """A declared ``"BLANK"`` value and the blank member sanitize to one name: rejected."""
    with pytest.raises(ConfigurationError, match=r"sanitize to the same enum member: 'BLANK'"):
        build_enum_from_choices(
            [("BLANK", "Blank"), ("good", "Good")],
            "BlankCollisionEnum",
            source_label="Fixture.status",
            include_blank=True,
        )
    # Without the blank member the declared value is an ordinary member.
    enum_cls = build_enum_from_choices(
        [("BLANK", "Blank"), ("good", "Good")],
        "BlankValueEnum",
        source_label="Fixture.status",
    )
    assert _member_map(enum_cls) == {"BLANK": "BLANK", "good": "good"}


def test_nullable_blank_choice_column_keeps_null_and_blank_distinct() -> None:
    """``null=True, blank=True`` publishes a nullable enum whose ``BLANK`` member is ``""``."""
    model = _blank_choice_model(choices=[("good", "Good")], blank=True, null=True)
    annotation = convert_scalar(_concrete_field(model, "status"), "NullableBlankFixtureType")
    enum_cls = registry.get_enum(model, "status")
    assert enum_cls is not None
    assert annotation == enum_cls | None
    assert enum_value(enum_cls["BLANK"]) == ""


class _Condition(models.TextChoices):
    __empty__ = "Unassessed"
    GOOD = "good", "Good"
    WORN = "worn", "Worn"


class _Rank(models.IntegerChoices):
    __empty__ = "Unranked"
    NONE = 0, "None"
    ONE = 1, "One"


class _Grade(models.TextChoices):
    __empty__ = "Ungraded"
    UNSET = "", "Unset"
    GOOD = "good", "Good"


_EMPTY_LABEL_CASES: "list[tuple[models.Field[Never, object], dict[str, object]]]" = [
    (models.TextField(choices=_Condition.choices), {"good": "good", "worn": "worn"}),
    (
        models.TextField(choices=_Condition.choices, blank=True),
        {"BLANK": "", "good": "good", "worn": "worn"},
    ),
    (
        models.TextField(choices=_Condition.choices, null=True, blank=True),
        {"BLANK": "", "good": "good", "worn": "worn"},
    ),
    (
        models.IntegerField(choices=_Rank.choices, null=True, blank=True),
        {"MEMBER_0": 0, "MEMBER_1": 1},
    ),
    (models.TextField(choices=_Grade.choices), {"BLANK": "", "good": "good"}),
    (models.TextField(choices=[(None, "Unknown"), ("good", "Good")]), {"good": "good"}),
]


@pytest.mark.parametrize(
    ("field", "members"),
    _EMPTY_LABEL_CASES,
    ids=[
        "text-strict",
        "text-blank",
        "text-null-blank",
        "integer-zero",
        "declared-empty-string",
        "hand-declared-none",
    ],
)
def test_none_valued_choice_is_the_empty_option_label_and_gets_no_member(
    field: models.Field[Never, object],
    members: dict[str, object],
) -> None:
    """A ``(None, label)`` pair labels the empty option, never a value, so it gets no member.

    ``Choices.__empty__`` prepends the pair to ``.choices``; a hand-declared one is read the
    same way. The test is identity, so an ``IntegerChoices`` ``0`` keeps ``MEMBER_0`` and a
    declared ``""`` keeps ``BLANK``; the represented values the serializer check reads agree.
    """
    meta = type("Meta", (), {"app_label": _unique_app_label("test_empty_label_choices")})
    owner = type(
        "EmptyLabelFixture",
        (models.Model,),
        {"status": field, "Meta": meta, "__module__": __name__},
    )
    assert _concrete_field(owner, "status") is field
    enum_cls = convert_choices_to_enum(field, "EmptyLabelFixtureType")
    assert _member_map(enum_cls) == members
    assert choice_column_values(field) == list(members.values())


def test_nullable_empty_label_choice_column_reads_null_without_a_none_member() -> None:
    """A ``null=True`` column with ``__empty__`` publishes ``Enum | None`` and reads NULL as ``null``.

    The empty option travels as GraphQL ``null``, never as a member: the enum carries only the
    declared conditions (plus ``BLANK`` for the ``""`` the column admits).
    """
    owner_model = _blank_choice_model(choices=_Condition.choices, blank=True, null=True)

    class EmptyLabelOwnerType(DjangoType):
        class Meta:
            model = owner_model
            fields = ("status",)

    enum_cls = registry.get_enum(owner_model, "status")
    assert enum_cls is not None
    assert EmptyLabelOwnerType.__annotations__["status"] == (enum_cls | None)
    assert _member_map(enum_cls) == {"BLANK": "", "good": "good", "worn": "worn"}
    finalize_django_types()

    @strawberry.type
    class Query:
        def _owners(self) -> list[models.Model]:
            return [owner_model(status=None), owner_model(status="good")]

        owners: list[models.Model] = strawberry.field(
            resolver=_owners,
            graphql_type=list[EmptyLabelOwnerType],
        )

    result = strawberry.Schema(query=Query).execute_sync("{ owners { status } }")
    assert result.errors is None
    assert result.data == {"owners": [{"status": None}, {"status": "good"}]}


@pytest.mark.django_db(transaction=True)
def test_nullable_empty_label_choice_column_writes_null_as_null() -> None:
    """A ``null`` sent to a ``null=True`` ``__empty__`` column stores NULL; ``_None`` is no member.

    The unmanaged owner's table is created for this test only (SQLite's schema editor needs the
    transaction-less test), so the create mutation runs the real decode, ``full_clean`` and save.
    """

    class EmptyLabelWriteOwner(models.Model):
        status: "models.TextField[str | Combinable | None, str | None]" = models.TextField(  # noqa: DJ001 - NULL is the fixture input
            choices=_Condition.choices,
            null=True,
            blank=True,
        )

        class Meta:
            app_label = _unique_app_label("test_empty_label_choices")
            managed = False
            db_table = "converters_empty_label_write_owner"

    class EmptyLabelWriteOwnerType(DjangoType):
        class Meta:
            model = EmptyLabelWriteOwner
            fields = ("id", "status")
            primary = True

    assert registry.get(EmptyLabelWriteOwner) is EmptyLabelWriteOwnerType

    class CreateEmptyLabelWriteOwner(DjangoMutation):
        class Meta:
            model = EmptyLabelWriteOwner
            operation = "create"
            fields = ("status",)
            permission_classes = []

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        create_owner = DjangoMutationField(CreateEmptyLabelWriteOwner)

    finalize_django_types()
    schema = DjangoSchema(query=Query, mutation=Mutation)
    with connection.schema_editor() as editor:
        editor.create_model(EmptyLabelWriteOwner)
    try:
        document = (
            "mutation($status: EmptyLabelWriteOwnerTypeStatusEnum) { createOwner(data: "
            "{status: $status}) { result { status } errors { field messages } } }"
        )
        written = schema.execute_sync(document, variable_values={"status": None})
        assert written.errors is None
        assert written.data == {"createOwner": {"result": {"status": None}, "errors": []}}
        assert list(EmptyLabelWriteOwner.objects.values_list("status", flat=True)) == [None]
        refused = schema.execute_sync(document, variable_values={"status": "_None"})
        assert refused.errors is not None
        assert "Value '_None' does not exist in 'EmptyLabelWriteOwnerTypeStatusEnum' enum." in (
            refused.errors[0].message
        )
        assert EmptyLabelWriteOwner.objects.count() == 1
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(EmptyLabelWriteOwner)


@pytest.mark.parametrize(
    "choices",
    [[(None, "Unassessed")], [(None, "Unassessed"), (None, "Unknown")]],
    ids=["one", "two"],
)
def test_choices_holding_only_the_empty_option_are_empty(choices: list[tuple[None, str]]) -> None:
    """A sequence whose every pair is ``None``-valued declares no value: the empty-choices error."""
    labels = ", ".join(repr(label) for _value, label in choices)
    message = re.escape(
        f"Fixture.status declares choices but the sequence is empty, holding only the empty "
        f"option {labels} (a None value labels the empty option and is never a member); "
        "choices must be a non-empty flat sequence of (value, label) pairs.",
    )
    with pytest.raises(ConfigurationError, match=f"^{message}$"):
        build_enum_from_choices(choices, "OnlyEmptyEnum", source_label="Fixture.status")
    field: models.TextField[str | Combinable, str] = models.TextField(choices=choices, blank=True)
    field.set_attributes_from_name("status")
    with pytest.raises(ConfigurationError, match="holding only the empty option"):
        choice_column_values(field)


def test_empty_choices_message_names_no_empty_option() -> None:
    """A sequence with no pair at all keeps the plain empty-choices message."""
    with pytest.raises(
        ConfigurationError,
        match=r"^Fixture\.status declares choices but the sequence is empty; choices must be ",
    ):
        build_enum_from_choices([], "NoChoicesEnum", source_label="Fixture.status")


def test_choice_member_name_sanitization() -> None:
    """Hyphenated, leading-digit, and keyword choice values produce safe identifiers.

    Direct unit tests of ``_sanitize_member_name`` so the rules are pinned
    independently of Django field plumbing.
    """
    assert _sanitize_member_name("active") == "active"
    assert _sanitize_member_name("first-name") == "first_name"
    assert _sanitize_member_name("123abc") == "MEMBER_123abc"
    assert _sanitize_member_name("class") == "_class"  # Python keyword
    # Integer values from IntegerChoices.
    assert _sanitize_member_name(1) == "MEMBER_1"
    assert _sanitize_member_name(42) == "MEMBER_42"
    # The empty string (the value a blank-admitting field stores) is named ``BLANK``.
    assert _sanitize_member_name("") == "BLANK"


def test_sanitize_member_name_neutralizes_python_enum_reserved_shapes() -> None:
    """Values that sanitize to Python-``enum``-reserved member names get ``MEMBER_``-prefixed.

    ``Enum(cls_name, {name: value})`` refuses ``"mro"`` and treats any single-
    underscore ``_sunder_`` name as a reserved directive -- raising for most
    (``_x_`` / ``_name_``) and SILENTLY dropping the recognised ones
    (``_ignore_`` / ``_missing_``). Python 3.11+ also silently omits names in the
    generated class's private namespace. ``_sanitize_member_name`` must rewrite
    every such shape with the same ``MEMBER_`` prefix it already uses for
    GraphQL-reserved and introspection-prefixed names, so no hostile choice value
    escapes as a raw ``enum`` crash, a vanished member, or a version-dependent
    schema.
    """
    # Symbol-wrapped tokens collapse to a ``_word_`` sunder shape and must be
    # neutralised (unsanitized, ``Enum(...)`` raises a raw ``ValueError``).
    assert _sanitize_member_name("-x-") == "MEMBER__x_"
    assert _sanitize_member_name("[a]") == "MEMBER__a_"
    assert _sanitize_member_name("-1-") == "MEMBER__1_"
    # Recognised sunder directives (unsanitized, SILENTLY dropped as members).
    assert _sanitize_member_name("_ignore_") == "MEMBER__ignore_"
    assert _sanitize_member_name("_missing_") == "MEMBER__missing_"
    # The special-cased ``mro`` (case-sensitive: only the lowercase form is reserved).
    assert _sanitize_member_name("mro") == "MEMBER_mro"
    assert _sanitize_member_name("MRO") == "MRO"
    # A generated enum's class-private namespace is class-name-specific and
    # silently becomes an attribute instead of a member without the prefix.
    assert (
        _sanitize_member_name(
            "_FixtureTypeStatusEnum__hidden",
            enum_name="FixtureTypeStatusEnum",
        )
        == "MEMBER__FixtureTypeStatusEnum__hidden"
    )
    assert (
        _sanitize_member_name("_OtherEnum__hidden", enum_name="FixtureTypeStatusEnum")
        == "_OtherEnum__hidden"
    )
    # Non-sunder single-underscore names stay untouched (boundary guards).
    assert _sanitize_member_name("_x") == "_x"  # no trailing underscore
    assert _sanitize_member_name("x_") == "x_"  # no leading underscore
    assert _sanitize_member_name("caf\u00e9") == "caf_"  # trailing-only underscore


def test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema(
    choice_fixture_model: type[models.Model],
) -> None:
    """Reserved, non-ASCII, and introspection-prefixed values produce GraphQL-safe enum members."""
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = (
        ("true", "True"),
        ("FALSE", "False"),
        ("null", "Null"),
        ("caf\u00e9", "Cafe"),
        ("__private", "Private"),
    )
    registry.clear()
    try:
        enum_cls = convert_choices_to_enum(field, "FixtureType")

        assert [member.name for member in enum_cls] == [
            "MEMBER_true",
            "MEMBER_FALSE",
            "MEMBER_null",
            "caf_",
            "MEMBER___private",
        ]

        @strawberry.type
        class Query:
            def _statuses(self) -> list[enum.Enum]:
                return list(enum_cls)

            # The enum class is generated by the converter under test, so the field's GraphQL
            # type is passed as a value rather than written as a return annotation.
            statuses: list[enum.Enum] = strawberry.field(
                resolver=_statuses,
                graphql_type=list[enum_cls],
            )

        schema = strawberry.Schema(query=Query)
        result = schema.execute_sync("{ statuses }")

        assert result.errors is None
        assert result.data == {
            "statuses": [
                "MEMBER_true",
                "MEMBER_FALSE",
                "MEMBER_null",
                "caf_",
                "MEMBER___private",
            ],
        }
    finally:
        field.choices = original
        registry.clear()


def test_choice_field_with_null_widens_to_enum_or_none(
    choice_fixture_model: type[models.Model],
) -> None:
    """A nullable choice column produces *exactly* ``EnumType | None``.

    Strict equality matters \u2014 if a future ``convert_scalar`` reorder
    accidentally widens before the choices branch fires, the annotation
    would collapse via ``str | None`` and we want that to fail loudly
    rather than silently produce an ``EnumType | None | None`` shape.
    """

    class FixtureType(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("nullable_status",)

    enum_cls = registry.get_enum(choice_fixture_model, "nullable_status")
    assert enum_cls is not None
    assert FixtureType.__annotations__["nullable_status"] == (enum_cls | None)


# ---------------------------------------------------------------------------
# Direct unit coverage of the helpers (covers branches the integration
# tests above don't naturally exercise)
# ---------------------------------------------------------------------------


def test_convert_choices_to_enum_raises_on_empty_choices(
    choice_fixture_model: type[models.Model],
) -> None:
    """A field with ``choices=()`` raises rather than producing an empty enum."""
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = ()
    try:
        with pytest.raises(ConfigurationError, match="empty"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original


def test_convert_choices_to_enum_raises_on_sanitized_member_collision(
    choice_fixture_model: type[models.Model],
) -> None:
    """Two choice values that sanitize to the same Python identifier raise.

    Without the collision check, the dict comprehension silently keeps the last
    value, leaving the GraphQL enum missing one of the choices and
    producing a runtime coercion error long after schema build.
    """
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    # ``a-b`` and ``a_b`` both sanitize to ``a_b``.
    field.choices = (("a-b", "Hyphen"), ("a_b", "Underscore"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_raises_on_keyword_prefix_collision(
    choice_fixture_model: type[models.Model],
) -> None:
    """Keyword-prefix collisions also raise: ``"if"`` mangles to ``"_if"`` and collides with raw ``"_if"``.

    The second collision shape: the value ``"if"`` is a Python keyword
    and is sanitized to ``"_if"``;
    a sibling raw value ``"_if"`` would silently overwrite the first
    without the guard.
    """
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = (("if", "Conditional"), ("_if", "Underscored"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_raises_on_graphql_safe_name_collision(
    choice_fixture_model: type[models.Model],
) -> None:
    """Collision detection runs after GraphQL reserved-name rewriting."""
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = (("true", "Reserved"), ("MEMBER_true", "Already prefixed"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_with_python_enum_reserved_values_builds_schema(
    choice_fixture_model: type[models.Model],
) -> None:
    """Choice values that map to Python-``enum``-reserved member names build a working enum.

    Without the ``_is_enum_reserved_member`` neutralisation in
    ``_sanitize_member_name`` this raised a raw ``ValueError`` from ``Enum(...)``
    for the ``_sunder_``-shaped / ``mro`` values (``"-x-"``, ``"mro"``) and --
    worse -- SILENTLY dropped the recognised-directive value ``"_ignore_"`` from
    the enum. Python 3.11+ also dropped ``"_FixtureTypeStatusEnum__hidden"`` as a
    class-private attribute, making the generated schema interpreter-dependent.
    Every choice must survive as a member with its DB value preserved and the
    schema must build + execute.
    """
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = (
        ("-x-", "Dash X"),  # -> _x_ sunder shape: unsanitized, ValueError at Enum build.
        ("mro", "Method Resolution Order"),  # unsanitized, ValueError at Enum build.
        ("_ignore_", "Ignore Directive"),  # unsanitized, SILENTLY dropped as a member.
        # Unsanitized, SILENTLY installed as a class attribute, not a member.
        ("_FixtureTypeStatusEnum__hidden", "Private Namespace"),
        ("active", "Active"),  # plain control value.
    )
    registry.clear()
    try:
        enum_cls = convert_choices_to_enum(field, "FixtureType")

        # Every choice value survives as a distinct member (none dropped).
        assert {enum_value(member) for member in enum_cls} == {
            "-x-",
            "mro",
            "_ignore_",
            "_FixtureTypeStatusEnum__hidden",
            "active",
        }
        assert [member.name for member in enum_cls] == [
            "MEMBER__x_",
            "MEMBER_mro",
            "MEMBER__ignore_",
            "MEMBER__FixtureTypeStatusEnum__hidden",
            "active",
        ]

        @strawberry.type
        class Query:
            def _statuses(self) -> list[enum.Enum]:
                return list(enum_cls)

            # The enum class is generated by the converter under test, so the field's GraphQL
            # type is passed as a value rather than written as a return annotation.
            statuses: list[enum.Enum] = strawberry.field(
                resolver=_statuses,
                graphql_type=list[enum_cls],
            )

        schema = strawberry.Schema(query=Query)
        result = schema.execute_sync("{ statuses }")

        assert result.errors is None
        assert result.data == {
            "statuses": [
                "MEMBER__x_",
                "MEMBER_mro",
                "MEMBER__ignore_",
                "MEMBER__FixtureTypeStatusEnum__hidden",
                "active",
            ],
        }
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_raises_on_enum_reserved_sanitize_collision(
    choice_fixture_model: type[models.Model],
) -> None:
    """Collision detection still fires after the Python-``enum``-reserved rewrite.

    ``"-x-"`` and ``"_x_"`` both sanitize to ``MEMBER__x_``; the collision must
    surface as the localised ``ConfigurationError`` rather than a silently
    dropped member -- the same contract already held for the
    ``true`` / ``MEMBER_true`` GraphQL-reserved collision above.
    """
    field = choice_fixture_model._meta.get_field("status")
    assert isinstance(field, models.Field)
    original = field.choices
    field.choices = (("-x-", "Symbol wrapped"), ("_x_", "Sunder shaped"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


# ---------------------------------------------------------------------------
# SCALAR_MAP subclass resolution
# ---------------------------------------------------------------------------


class _TrimmedCharField(models.CharField[str, str]):
    """Consumer-style subclass of ``CharField``.

    Subclassing a Django field is the normal extension path; exact-type
    ``SCALAR_MAP`` lookup would reject this even though the column still
    stores ``str``.
    """


class _NullableTrimmedCharField(models.CharField[str | None, str | None]):
    """Same shape but with ``null=True`` to exercise widening on a subclass."""


def test_convert_scalar_resolves_subclass_of_supported_field_to_parent_scalar() -> None:
    """A consumer subclass of ``CharField`` resolves to ``str`` via MRO walk.

    Exact-type ``SCALAR_MAP`` lookup misses subclasses, breaking the standard Django
    extension path. The walker must find ``models.CharField`` on the
    subclass MRO and return its mapped scalar.
    """

    class _Owner(models.Model):
        slug = _TrimmedCharField(max_length=32)

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _concrete_field(_Owner, "slug")
    assert convert_scalar(field, "OwnerType") is str


def test_convert_scalar_subclass_with_null_widens_through_mro_resolution() -> None:
    """The MRO-resolved scalar still flows through the ``null=True`` widening branch."""

    class _Owner(models.Model):
        slug = _NullableTrimmedCharField(max_length=32, null=True)

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _concrete_field(_Owner, "slug")
    assert convert_scalar(field, "OwnerType") == (str | None)


def test_convert_scalar_unknown_field_type_still_raises() -> None:
    """A field whose MRO does not intersect ``SCALAR_MAP`` still raises.

    Guard against the MRO walk accidentally swallowing the unsupported
    case: ``object`` is on every MRO but is not in ``SCALAR_MAP``.

    Exposing this column is what the package refuses to build (the package raises), so
    no fakeshop model carries it; this owner alone reaches the ``Unsupported Django
    field type`` raise in
    ``django_strawberry_framework/types/converters.py::scalar_for_field``.
    """

    class _UnsupportedField(models.Field[object, object]):
        pass

    class _Owner(models.Model):
        weird = _UnsupportedField()

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _concrete_field(_Owner, "weird")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


def test_convert_scalar_duration_field_raises_unsupported() -> None:
    """``DurationField`` is intentionally absent from ``SCALAR_MAP``.

    Strawberry refuses ``datetime.timedelta`` at schema construction time
    (no first-party scalar), so leaving the entry in mapped it to a type
    that crashed downstream with a less-localized ``TypeError`` from the
    Strawberry frame. Surfacing the error at class-definition time via the
    standard ``Unsupported Django field type`` raise keeps the failure
    grep-stable for the consumer. A custom scalar is the supported
    extension path (``SCALAR_MAP[DurationField] = MyDurationScalar``).

    The ``DurationField`` column itself is legal Django; *exposing* it is what the
    package refuses to build, so no fakeshop type can carry it, and this owner alone
    pins its absence from ``SCALAR_MAP`` at the
    ``django_strawberry_framework/types/converters.py::scalar_for_field`` raise.
    """

    class _Owner(models.Model):
        elapsed: "models.DurationField[object, datetime.timedelta]" = models.DurationField()

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _concrete_field(_Owner, "elapsed")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


def test_convert_scalar_binary_field_raises_unsupported() -> None:
    """``BinaryField`` is intentionally absent from ``SCALAR_MAP``.

    Same reasoning as ``DurationField``: Strawberry has no first-party
    ``bytes`` scalar so the prior mapping crashed at schema build. The
    documented extension hook is
    ``SCALAR_MAP[BinaryField] = strawberry.scalars.Base64``.

    The ``BinaryField`` column itself is legal Django; *exposing* it is what the package
    refuses to build, so no fakeshop type can carry it, and this owner alone pins its
    absence from ``SCALAR_MAP`` at the
    ``django_strawberry_framework/types/converters.py::scalar_for_field`` raise.
    """

    class _Owner(models.Model):
        blob: "models.BinaryField[object, bytes | memoryview]" = models.BinaryField()

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _concrete_field(_Owner, "blob")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


# ---------------------------------------------------------------------------
# BigInt scalar - package-internal contract tests
#
# The field-mapping introspection tests and the basic outbound/inbound
# round-trip tests live on the scalars app
# (``examples/fakeshop/test_query/test_scalars_api.py``), including
# ``BigAutoField -> Int``
# (``test_scalar_specimen_id_maps_big_auto_pk_to_int``). What remains here
# is unreachable from a real HTTP path:
#
# - Two BigInt edge tests with no wire shape of their own: a nullable
#   ``BigInt`` argument given ``null`` (Strawberry strips it before the
#   parser runs, so the claim is about what the RESOLVER receives), and a
#   resolver returning ``bool`` for a ``BigInt`` annotation (no fakeshop
#   field can return the wrong Python type). Literal rejection over the
#   wire is pinned live on the scalars filter surface
#   (``test_query/test_scalars_api.py::test_filter_specimens_by_bigint_exact_rejects_non_integer_literal``).
#
# Synthetic models live under ``app_label = "test_bigint"`` so they do not
# collide with the choice-enum fixture's ``app_label = "test_choice_enums"``.
# ``managed = False`` per spec-017 Decision 7
# #"every test model hosting `FakeArrayField` or `FakeHStoreField` declares `class Meta: managed = False`":
# no migration implication; test rows are instantiated directly when needed.
# ---------------------------------------------------------------------------


class _IntrospectedTypeRef(TypedDict):
    """One level of the ``type { kind name ofType { ... } }`` introspection payload."""

    kind: str
    name: str | None
    ofType: "_IntrospectedTypeRef | None"


def _walk_introspected_type(type_field: _IntrospectedTypeRef) -> _IntrospectedTypeRef:
    """Walk a GraphQL introspection ``type`` payload to the terminal scalar.

    Wrapping types (``NON_NULL``, ``LIST``) have ``name: None`` per
    spec-017 Decision 7's introspection note
    (#"walk it explicitly rather than asserting on `field.type.name`").
    Walking the chain surfaces the inner ``SCALAR { name: "BigInt" }`` regardless of
    nullability / list wrapping.
    """
    current = type_field
    while (inner := current.get("ofType")) is not None:
        current = inner
    return current


def _introspect_field_type(
    schema: strawberry.Schema,
    type_name: str,
    field_name: str,
) -> _IntrospectedTypeRef:
    """Return the introspected ``type`` payload for ``Type.field`` on ``schema``."""
    query = (
        f'{{ __type(name: "{type_name}") {{ fields {{ name type {{ kind name '
        "ofType { kind name ofType { kind name ofType { kind name } } } } } } }"
    )
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    assert result.data is not None
    data: dict[str, object] = result.data
    fields = require(require(data["__type"], is_object_dict)["fields"], is_object_list)
    for field in fields:
        entry = require(field, is_object_dict)
        if entry["name"] == field_name:
            # The query selects ``kind name ofType`` at every level, so the payload has the
            # TypedDict's shape; the innermost level omits ``ofType``, read with ``get``
            return cast("_IntrospectedTypeRef", entry["type"])
    raise AssertionError(f"field {field_name!r} not found on type {type_name!r}; got {fields!r}")


def test_bigint_in_input_position_with_null_via_schema_execution() -> None:
    """A nullable ``BigInt`` argument accepts ``null``.

    Strawberry strips it before the parser runs, so the resolver receives ``None``.
    """

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt | None = None) -> str:
            return "null" if val is None else str(val)

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    result = schema.execute_sync("query { echo(val: null) }")
    assert result.errors is None
    assert result.data == {"echo": "null"}


def test_bigint_resolver_returning_bool_raises_via_schema_execution() -> None:
    """Outbound: a resolver returning ``True`` for a ``BigInt`` annotation raises ``TypeError``.

    The ``bool`` surfaces a ``TypeError`` at the schema boundary via ``_serialize_bigint``.
    """

    @strawberry.type
    class Query:
        @strawberry.field
        def bool_as_bigint(self) -> BigInt:
            # basedpyright: the resolver returns a bool for a BigInt field on purpose: the test
            # proves the strict serializer rejects it at the schema boundary
            return True  # pyright: ignore[reportReturnType]

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    result = schema.execute_sync("{ boolAsBigint }")
    assert result.errors is not None
    assert len(result.errors) > 0
    # The strict serializer's error message is the contract source; GraphQL wraps
    # the TypeError in a GraphQLError, so assert on the message substring rather
    # than the exception type.
    assert any("BigInt cannot serialize bool" in str(err) for err in result.errors)


# ---------------------------------------------------------------------------
# ArrayField -> list[T] sentinel-guarded recursion
#
# Synthetic models live under ``app_label = "test_arrayfield"`` so they do
# not collide with the prior synthetic apps (``test_bigint``,
# ``test_choice_enums``). Sentinel-branch tests point
# ``ARRAY_FIELD_CLS`` at ``FakeArrayField`` (``patch_array_field``) BEFORE declaring the
# ``DjangoType`` (spec-017 Decision 7 #"*before* declaring the `DjangoType`").
# The introspection helpers (``_introspect_field_type`` /
# ``_walk_introspected_type``) defined in the BigInt section above are
# reused verbatim by every owner-introspection test below.
#
# Why this section can never migrate to live HTTP: ``ArrayField`` is a
# PostgreSQL-only field type and the fakeshop runs on SQLite. The
# converter-table row is exercised here against synthetic models and the
# sentinel-monkeypatch pattern; consumer-facing coverage stays package-
# internal until the example project gains a postgres test matrix.
# ---------------------------------------------------------------------------


def test_array_field_of_int_maps_to_list_int_via_fake_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``ArrayField(IntegerField())`` maps to ``list[int]`` (non-null outer + inner).

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayIntOwner(models.Model):
        arr = FakeArrayField(models.IntegerField())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayIntOwnerType(DjangoType):
        class Meta:
            model = ArrayIntOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> ArrayIntOwner:
            return ArrayIntOwner(
                arr=[1, 2, 3],
            )

        owner: ArrayIntOwner = strawberry.field(resolver=_owner, graphql_type=ArrayIntOwnerType)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayIntOwnerType", "arr")
    # NON_NULL -> LIST -> NON_NULL -> SCALAR { name: "Int" }
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"] is not None
    assert type_payload["ofType"]["kind"] == "LIST"
    assert type_payload["ofType"]["ofType"] is not None
    assert type_payload["ofType"]["ofType"]["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "Int"


def test_array_field_of_char_maps_to_list_str_via_fake_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``ArrayField(CharField())`` maps to ``list[str]`` (terminal SCALAR name "String").

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayCharOwner(models.Model):
        arr = FakeArrayField(models.CharField(max_length=20))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayCharOwnerType(DjangoType):
        class Meta:
            model = ArrayCharOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> ArrayCharOwner:
            return ArrayCharOwner(arr=["a", "b"])

        owner: ArrayCharOwner = strawberry.field(resolver=_owner, graphql_type=ArrayCharOwnerType)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayCharOwnerType", "arr")
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"] is not None
    assert type_payload["ofType"]["kind"] == "LIST"
    assert type_payload["ofType"]["ofType"] is not None
    assert type_payload["ofType"]["ofType"]["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "String"


def test_array_field_nullable_inner_via_fake_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """``ArrayField(IntegerField(null=True))`` maps to ``list[int | None]``.

    Inner ``null=True`` drops the inner ``NON_NULL`` wrapper; outer stays
    non-null. Introspection chain: ``NON_NULL -> LIST -> SCALAR``.

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayNullableInnerOwner(models.Model):
        arr = FakeArrayField(models.IntegerField(null=True))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayNullableInnerOwnerType(DjangoType):
        class Meta:
            model = ArrayNullableInnerOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> ArrayNullableInnerOwner:
            return ArrayNullableInnerOwner(
                arr=[1, None, 2],
            )

        owner: ArrayNullableInnerOwner = strawberry.field(
            resolver=_owner,
            graphql_type=ArrayNullableInnerOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayNullableInnerOwnerType", "arr")
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"] is not None
    assert type_payload["ofType"]["kind"] == "LIST"
    # Inner-null drops the NON_NULL: directly SCALAR underneath LIST.
    assert type_payload["ofType"]["ofType"] is not None
    assert type_payload["ofType"]["ofType"]["kind"] == "SCALAR"
    assert type_payload["ofType"]["ofType"]["name"] == "Int"


def test_array_field_outer_nullable_via_fake_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """``ArrayField(IntegerField(), null=True)`` maps to ``list[int] | None``.

    Outer ``null=True`` drops the outer ``NON_NULL`` wrapper; inner stays
    non-null. Introspection chain: ``LIST -> NON_NULL -> SCALAR``.

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayOuterNullableOwner(models.Model):
        arr = FakeArrayField(models.IntegerField(), null=True)

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayOuterNullableOwnerType(DjangoType):
        class Meta:
            model = ArrayOuterNullableOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> ArrayOuterNullableOwner:
            return ArrayOuterNullableOwner(arr=None)

        owner: ArrayOuterNullableOwner = strawberry.field(
            resolver=_owner,
            graphql_type=ArrayOuterNullableOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayOuterNullableOwnerType", "arr")
    # Outer-null drops the NON_NULL: top-level kind is LIST.
    assert type_payload["kind"] == "LIST"
    assert type_payload["ofType"] is not None
    assert type_payload["ofType"]["kind"] == "NON_NULL"
    assert type_payload["ofType"]["ofType"] is not None
    assert type_payload["ofType"]["ofType"]["kind"] == "SCALAR"
    assert type_payload["ofType"]["ofType"]["name"] == "Int"


def test_array_field_multidim_rejected_via_fake_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nested ``ArrayField`` raises ``ConfigurationError`` at type creation.

    Exposing this column is what the package refuses to build (the package raises) and
    the column type is PostgreSQL-only besides, so no fakeshop model carries it; this
    owner alone reaches the ``Nested ArrayField`` raise in
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayMultidimOwner(models.Model):
        arr = FakeArrayField(FakeArrayField(models.IntegerField()))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="Nested ArrayField on"):

        @definition_raises
        class ArrayMultidimOwnerType(DjangoType):
            class Meta:
                model = ArrayMultidimOwner
                fields = ("arr",)


def test_annotation_override_of_arrayfield_with_nested_array_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Consumer ``arr: list[list[int]]`` annotation bypasses nested-ArrayField rejection.

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class NestedArrayOverrideOwner(models.Model):
        arr = FakeArrayField(FakeArrayField(models.IntegerField()))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class NestedArrayOverrideOwnerType(DjangoType):
        arr: list[list[int]]

        class Meta:
            model = NestedArrayOverrideOwner
            fields = ("arr",)

    finalize_django_types()
    assert NestedArrayOverrideOwnerType.__annotations__["arr"] == list[list[int]]


def test_array_field_choices_inner_via_fake_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """``ArrayField(CharField(choices=...))`` produces ``list[<TypeName><FieldName>Enum]``.

    The recursive ``convert_scalar(field.base_field, type_name)`` call hits
    the existing choice-enum branch on ``base_field``, so the inner type is
    an enum scalar.

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayChoicesInnerOwner(models.Model):
        arr = FakeArrayField(
            models.CharField(max_length=5, choices=[("A", "A"), ("B", "B")]),
        )

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayChoicesInnerOwnerType(DjangoType):
        class Meta:
            model = ArrayChoicesInnerOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> ArrayChoicesInnerOwner:
            return ArrayChoicesInnerOwner(arr=["A", "B"])

        owner: ArrayChoicesInnerOwner = strawberry.field(
            resolver=_owner,
            graphql_type=ArrayChoicesInnerOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayChoicesInnerOwnerType", "arr")
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"] is not None
    assert type_payload["ofType"]["kind"] == "LIST"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "ENUM"


def test_array_field_element_empty_label_gets_no_member_via_fake_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An ``ArrayField`` ``base_field`` with ``__empty__`` choices gets an element enum without ``_None``.

    The element enum is built by the same ``_normalize_choice_pairs`` the column enum reads, so the
    ``(None, "Unassessed")`` pair labels the empty option there too.
    """
    patch_array_field(monkeypatch)

    class ArrayEmptyLabelOwner(models.Model):
        arr = FakeArrayField(models.CharField(max_length=5, choices=_Condition.choices))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayEmptyLabelOwnerType(DjangoType):
        class Meta:
            model = ArrayEmptyLabelOwner
            fields = ("arr",)

    arr_args: tuple[object, ...] = get_args(ArrayEmptyLabelOwnerType.__annotations__["arr"])
    (element_enum,) = arr_args
    assert isinstance(element_enum, type)
    assert issubclass(element_enum, enum.Enum)
    assert _member_map(element_enum) == {"good": "good", "worn": "worn"}


def test_array_field_outer_choices_rejected_via_fake_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Outer ``choices`` on ``ArrayField`` raises ``ConfigurationError``.

    Spec-pinned error message mentions ``base_field`` and ``FilterSet`` as
    the consumer recourse.

    Exposing this column is what the package refuses to build (the package raises) and
    the column type is PostgreSQL-only besides, so no fakeshop model carries it; this
    owner alone reaches the outer-``choices`` raise in
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class ArrayOuterChoicesOwner(models.Model):
        arr = FakeArrayField(
            models.IntegerField(),
            choices=[(1, "one"), (2, "two")],
        )

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="declares choices on the outer"):

        @definition_raises
        class ArrayOuterChoicesOwnerType(DjangoType):
            class Meta:
                model = ArrayOuterChoicesOwner
                fields = ("arr",)


def test_array_field_base_field_unsupported_type_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unsupported ``base_field`` type surfaces the existing unsupported-type error.

    The ``Unsupported Django field type`` error comes via the recursive call.

    Exposing this column is what the package refuses to build (the package raises) and
    the column type is PostgreSQL-only besides, so no fakeshop model carries it; this
    owner alone reaches the recursive ``Unsupported Django field type`` raise in
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class _Weird(models.Field[object, object]):
        pass

    class ArrayUnsupportedBaseOwner(models.Model):
        arr = FakeArrayField(_Weird())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):

        @definition_raises
        class ArrayUnsupportedBaseOwnerType(DjangoType):
            class Meta:
                model = ArrayUnsupportedBaseOwner
                fields = ("arr",)


def test_array_field_sentinel_none_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """With ``ARRAY_FIELD_CLS = None`` the sentinel short-circuits.

    The field falls through to the MRO walk's unsupported-field error.

    Pins the short-circuit guard: with no ``ArrayField`` class, no column is an array,
    whatever its class.

    A ``FakeArrayField`` column exposed with ``ARRAY_FIELD_CLS`` unset is unbuildable
    by design (the package raises), so this unmanaged owner alone reaches the
    ``ARRAY_FIELD_CLS is not None`` guard in
    ``django_strawberry_framework/utils/_array_field.py::array_element_field``.
    """
    patch_array_field(monkeypatch, None)

    class ArraySentinelNoneOwner(models.Model):
        arr = FakeArrayField(models.IntegerField())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):

        @definition_raises
        class ArraySentinelNoneOwnerType(DjangoType):
            class Meta:
                model = ArraySentinelNoneOwner
                fields = ("arr",)


def test_real_array_field_compatible_with_strawberry() -> None:
    """Optional gated test: real ``ArrayField`` flows through the sentinel branch end-to-end.

    This runs ``django.contrib.postgres.fields.ArrayField`` on a postgres-equipped env.

    The real ``ArrayField`` owner is unmanaged and never migrated, because fakeshop runs
    on SQLite; it proves the sentinel dispatch in
    ``django_strawberry_framework/types/converters.py::convert_scalar`` matches Django's
    own class, and skips where ``django.contrib.postgres`` is unimportable.
    """
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415 - after the skip guard

    class RealArrayIntOwner(models.Model):
        arr: "ArrayField[Sequence[int] | Combinable, list[int]]" = ArrayField(
            models.IntegerField(),
        )

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class RealArrayIntOwnerType(DjangoType):
        class Meta:
            model = RealArrayIntOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> RealArrayIntOwner:
            return RealArrayIntOwner(
                arr=[1, 2, 3],
            )

        owner: RealArrayIntOwner = strawberry.field(
            resolver=_owner,
            graphql_type=RealArrayIntOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "RealArrayIntOwnerType", "arr")
    # NON_NULL -> LIST -> NON_NULL -> SCALAR { name: "Int" }
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"] is not None
    assert type_payload["ofType"]["kind"] == "LIST"
    assert type_payload["ofType"]["ofType"] is not None
    assert type_payload["ofType"]["ofType"]["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "Int"


# ---------------------------------------------------------------------------
# HStoreField -> strawberry.scalars.JSON sentinel-guarded branch
#
# Synthetic models live under ``app_label = "test_hstorefield"`` so they do
# not collide with the prior synthetic apps (``test_bigint``,
# ``test_arrayfield``, ``test_choice_enums``). Sentinel-branch tests
# monkey-patch ``converters._HSTORE_FIELD_CLS = FakeHStoreField`` BEFORE
# declaring the ``DjangoType`` (spec-017 Decision 7 #"*before* declaring the `DjangoType`").
# The sentinel's soft-import resolution is covered once in ``tests/utils/test_imports.py``,
# not here (spec-017 #"**Soft-import branch coverage** is NOT written here.").
#
# Same postgres-only constraint as the ArrayField section: ``HStoreField``
# can never run on the SQLite-backed fakeshop, so the converter-table row
# stays covered here against synthetic models. Migration to live HTTP is
# gated on the example project gaining a postgres test matrix.
# ---------------------------------------------------------------------------


def test_hstore_field_maps_to_json_scalar_via_fake_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``HStoreField`` (non-null) appears as ``JSON!`` in the schema.

    ``HStoreField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this
    unmanaged ``FakeHStoreField`` owner is the only route on SQLite into the ``HStoreField``
    branch of ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class HStoreOwner(models.Model):
        data = FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreOwnerType(DjangoType):
        class Meta:
            model = HStoreOwner
            fields = ("data",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> HStoreOwner:
            return HStoreOwner(data={"k": "v"})

        owner: HStoreOwner = strawberry.field(resolver=_owner, graphql_type=HStoreOwnerType)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "HStoreOwnerType", "data")
    # NON_NULL wrapper around JSON scalar.
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "JSON"


def test_hstore_field_nullable_via_fake_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """``HStoreField(null=True)`` appears as ``JSON`` (nullable).

    ``HStoreField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this
    unmanaged ``FakeHStoreField`` owner is the only route on SQLite into the ``HStoreField``
    branch of ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class HStoreNullableOwner(models.Model):
        data = FakeHStoreField(null=True)

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreNullableOwnerType(DjangoType):
        class Meta:
            model = HStoreNullableOwner
            fields = ("data",)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _owner(self) -> HStoreNullableOwner:
            return HStoreNullableOwner(data=None)

        owner: HStoreNullableOwner = strawberry.field(
            resolver=_owner,
            graphql_type=HStoreNullableOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "HStoreNullableOwnerType", "data")
    # Nullable: top-level kind is SCALAR (no NON_NULL wrapper).
    assert type_payload == {"kind": "SCALAR", "name": "JSON", "ofType": None}


def test_hstore_field_resolver_dict_serializes_via_schema_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Serializer-level test: a hand-built dict round-trips verbatim through the ``JSON`` scalar.

    The resolver returns the dict and ``schema.execute_sync`` serializes it.

    No DB persistence - SQLite cannot store HStore values; the test exercises
    only the scalar's wire-level serialization through Strawberry.

    ``HStoreField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this
    unmanaged ``FakeHStoreField`` owner is the only route on SQLite into the ``HStoreField``
    branch of ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class HStoreSerializeOwner(models.Model):
        data = FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreSerializeOwnerType(DjangoType):
        class Meta:
            model = HStoreSerializeOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v1"}

    @strawberry.type
    class Query:
        def _owner(self) -> HStoreSerializeOwner:
            return HStoreSerializeOwner(data=payload)

        owner: HStoreSerializeOwner = strawberry.field(
            resolver=_owner,
            graphql_type=HStoreSerializeOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}


def test_hstore_field_resolver_dict_with_none_value_via_schema_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A resolver returning ``{"k1": "v", "k2": None}`` round-trips with ``None`` preserved.

    The ``None`` value stays inside the dict, mirroring ``HStoreField``'s native
    ``dict[str, str | None]`` shape.

    ``HStoreField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this
    unmanaged ``FakeHStoreField`` owner is the only route on SQLite into the ``HStoreField``
    branch of ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class HStoreNoneValueOwner(models.Model):
        data = FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreNoneValueOwnerType(DjangoType):
        class Meta:
            model = HStoreNoneValueOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v", "k2": None}

    @strawberry.type
    class Query:
        def _owner(self) -> HStoreNoneValueOwner:
            return HStoreNoneValueOwner(data=payload)

        owner: HStoreNoneValueOwner = strawberry.field(
            resolver=_owner,
            graphql_type=HStoreNoneValueOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}


def test_hstore_field_outer_choices_rejected_via_fake_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Outer ``choices`` on ``HStoreField`` raises ``ConfigurationError``.

    HStore stores ``dict[str, str | None]`` with no enum-able shape at the
    GraphQL boundary; the rejection message names that rationale.

    Exposing this column is what the package refuses to build (the package raises) and
    the column type is PostgreSQL-only besides, so no fakeshop model carries it; this
    owner alone reaches the ``HStoreField ... declares choices`` raise in
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class HStoreOuterChoicesOwner(models.Model):
        data = FakeHStoreField(choices=[("a", "A")])

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    with pytest.raises(ConfigurationError, match="declares choices"):

        @definition_raises
        class HStoreOuterChoicesOwnerType(DjangoType):
            class Meta:
                model = HStoreOuterChoicesOwner
                fields = ("data",)


def test_hstore_field_sentinel_none_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """With ``_HSTORE_FIELD_CLS = None`` the sentinel short-circuits.

    The field falls through to the MRO walk's unsupported-field error.

    Pins the short-circuit guard: without ``_HSTORE_FIELD_CLS is not None``,
    the ``isinstance(field, _HSTORE_FIELD_CLS)`` call would ``TypeError``.

    A ``FakeHStoreField`` column exposed with ``_HSTORE_FIELD_CLS`` unset is
    unbuildable by design (the package raises), so this unmanaged owner alone reaches
    the ``_HSTORE_FIELD_CLS is not None`` guard in
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", None)

    class HStoreSentinelNoneOwner(models.Model):
        data = FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):

        @definition_raises
        class HStoreSentinelNoneOwnerType(DjangoType):
            class Meta:
                model = HStoreSentinelNoneOwner
                fields = ("data",)


def test_real_hstore_field_compatible_with_strawberry() -> None:
    """Optional gated test: real ``HStoreField`` flows through the sentinel branch end-to-end.

    This runs ``django.contrib.postgres.fields.HStoreField`` on a postgres-equipped env.

    Asserts both the introspection chain (``NON_NULL -> SCALAR { name: "JSON" }``)
    and resolver round-tripping (``{"k1": "v", "k2": None}`` preserved).

    The real ``HStoreField`` owner is unmanaged and never migrated, because fakeshop
    runs on SQLite; it proves the sentinel dispatch in
    ``django_strawberry_framework/types/converters.py::convert_scalar`` matches Django's
    own class, and skips where ``django.contrib.postgres`` is unimportable.
    """
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import HStoreField  # noqa: PLC0415 - after the skip guard

    class RealHStoreOwner(models.Model):
        data = HStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class RealHStoreOwnerType(DjangoType):
        class Meta:
            model = RealHStoreOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v", "k2": None}

    @strawberry.type
    class Query:
        def _owner(self) -> RealHStoreOwner:
            return RealHStoreOwner(data=payload)

        owner: RealHStoreOwner = strawberry.field(
            resolver=_owner,
            graphql_type=RealHStoreOwnerType,
        )

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "RealHStoreOwnerType", "data")
    # NON_NULL -> SCALAR { name: "JSON" }
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "JSON"

    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}


# ---------------------------------------------------------------------------
# Multi-type relation conversion regressions (always-defer)
# ---------------------------------------------------------------------------


def test_consumer_authored_relation_annotation_override_survives_always_defer() -> None:
    """Consumer-authored annotation override targeting a secondary survives always-defer.

    With ``Meta.primary = True`` on ``ItemType`` and ``AdminItemType`` as a
    secondary, an annotation-only override on ``CategoryType.items`` that
    points at ``AdminItemType`` must win over the primary-resolution path.
    Pins that the ``consumer_authored_fields`` short-circuit still skips
    relation synthesis for consumer-authored fields even though the
    auto-synthesized path is now always-defer.
    """

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        items: list[AdminItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})

    finalize_django_types()

    # Consumer annotation wins: list[AdminItemType], not list[ItemType].
    assert CategoryType.__annotations__["items"] == list[AdminItemType]


def test_consumer_assigned_strawberry_field_relation_survives_always_defer() -> None:
    """Consumer-assigned ``strawberry.field`` on a multi-type relation survives always-defer."""

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        @strawberry.field
        def items(self) -> list[AdminItemType]:
            return []

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset({"items"})

    # ``items`` is NOT in synthesized annotations - the consumer-authored
    # short-circuit skipped it, so no PendingRelationAnnotation was recorded.
    assert "items" not in CategoryType.__annotations__

    finalize_django_types()

    # Post-finalize: the consumer's resolver function is preserved and
    # exposed via Strawberry's field definition.
    items_field = next(
        field
        for field in get_object_definition(CategoryType, strict=True).fields
        if field.python_name == "items"
    )
    assert resolver_function(items_field).__qualname__.endswith("CategoryType.items")


def test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary() -> (
    None
):
    """Import-order trap closure: declare secondary -> source -> primary in order.

    Without always-defer, ``CategoryType.items`` would freeze against
    ``AdminItemType`` (the only registered type on ``Item`` at the
    moment ``CategoryType`` ran ``__init_subclass__``) and never pick
    up the primary that registered later.
    """

    # 1. Secondary registers first (no primary flag).
    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is AdminItemType

    # 2. Source references the reverse relation while only the secondary is known.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    # 3. Primary registers AFTER the source.
    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()

    # Post-finalize annotation must resolve to the primary, not the secondary.
    assert CategoryType.__annotations__["items"] == list[ItemType]

    # And the schema-built field type also picks the primary.
    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)
    items_field_type = _introspect_field_type(schema, "CategoryType", "items")
    terminal = _walk_introspected_type(items_field_type)
    assert terminal["name"] == "ItemType"


def test_relation_resolves_when_target_model_has_one_type_no_primary() -> None:
    """Backward-compat: a single registered type with no primary still resolves."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    finalize_django_types()
    assert CategoryType.__annotations__["items"] == list[ItemType]


def test_relation_target_with_multiple_no_primary_surfaces_audit_error_at_finalize() -> None:
    """The ambiguity audit fires before unresolved-target when target is multi-type-no-primary."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.model_for_type(AdminItemType) is Item

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    assert registry.get(Category) is CategoryType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    # The audit message is what fires - not the "no registered DjangoType"
    # message of the unresolved-target path.
    assert "Declare Meta.primary = True" in msg


# ---------------------------------------------------------------------------
# spec-029 - convert_scalar force_nullable tri-state
#
# These are direct ``convert_scalar`` unit tests (the tri-state seam fires at
# conversion time, unreachable from a live query without the override
# machinery). ``None`` must reproduce the column-native ``field.null`` result
# exactly (regression guard); ``True`` always widens; ``False`` always
# narrows. The choice / Array / HStore branches each read the same single
# ``effective_null`` value, so the override applies uniformly. Synthetic
# models reuse the existing ``_unique_app_label`` namespacing + the
# ``FakeArrayField`` / ``FakeHStoreField`` doubles and their monkeypatch
# pattern.
# ---------------------------------------------------------------------------


def _text_field(*, null: bool) -> models.Field[str | None, str | None]:
    """Return a scalars-app ``label`` ``TextField`` with the given ``null``."""
    model = NullableScalarSpecimen if null else ScalarSpecimen
    field = model._meta.get_field("label")
    assert isinstance(field, models.TextField)
    assert field.null is null
    return field


def test_convert_scalar_force_nullable_true_widens_non_null_column() -> None:
    """``force_nullable=True`` on a non-null ``TextField`` returns ``str | None``."""
    field = _text_field(null=False)
    assert convert_scalar(field, "OwnerType", force_nullable=True) == (str | None)


def test_convert_scalar_force_nullable_false_narrows_nullable_column() -> None:
    """``force_nullable=False`` on a nullable ``TextField`` returns bare ``str``."""
    field = _text_field(null=True)
    assert convert_scalar(field, "OwnerType", force_nullable=False) is str


def test_convert_scalar_force_nullable_none_honors_field_null() -> None:
    """``force_nullable=None`` (and the implicit default) reproduce ``field.null``.

    Regression guard for Decision 7's "the ``None`` default is identical to
    today's behavior" contract, checked in both column directions and against
    the no-kwarg call so the new keyword-only parameter cannot drift the
    existing default.
    """
    non_null = _text_field(null=False)
    nullable = _text_field(null=True)
    # Explicit None.
    assert convert_scalar(non_null, "OwnerType", force_nullable=None) is str
    assert convert_scalar(nullable, "OwnerType", force_nullable=None) == (str | None)
    # Implicit default (no kwarg) - the pre-override call shape.
    assert convert_scalar(non_null, "OwnerType") is str
    assert convert_scalar(nullable, "OwnerType") == (str | None)


def test_convert_scalar_force_nullable_on_choice_field(
    choice_fixture_model: type[models.Model],
) -> None:
    """The override flips a choice field's generated enum nullability (Decision 9).

    Widening sits AFTER choice substitution, so ``force_nullable=True`` on the
    non-null ``status`` column yields ``EnumType | None`` and ``False`` on the
    nullable ``nullable_status`` column yields a bare ``EnumType`` - the enum
    members are untouched in both directions.
    """
    registry.clear()
    status = _concrete_field(choice_fixture_model, "status")
    widened = convert_scalar(status, "FixtureType", force_nullable=True)
    enum_cls = registry.get_enum(choice_fixture_model, "status")
    assert enum_cls is not None
    assert widened == (enum_cls | None)

    nullable_status = _concrete_field(choice_fixture_model, "nullable_status")
    narrowed = convert_scalar(nullable_status, "FixtureType", force_nullable=False)
    nullable_enum = registry.get_enum(choice_fixture_model, "nullable_status")
    assert nullable_enum is not None
    assert narrowed is nullable_enum


def test_convert_scalar_force_nullable_on_array_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """The override flips the OUTER ``list[inner]`` nullability; inner is unchanged.

    A non-null ``ArrayField(IntegerField())`` with ``force_nullable=True``
    becomes ``list[int] | None`` (outer widened) while the inner element stays
    ``int`` (NOT ``int | None``) - the recursive ``base_field`` conversion is
    left ``force_nullable``-unset, so inner nullability follows
    ``base_field.null`` and is NOT affected by the outer override (Edge cases).
    A nullable-outer ``ArrayField(..., null=True)`` with ``force_nullable=False``
    narrows back to bare ``list[int]``.

    ``ArrayField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this unmanaged
    ``FakeArrayField`` owner is the only route on SQLite into the ``ArrayField`` branch of
    ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    patch_array_field(monkeypatch)

    class _ArrOwner(models.Model):
        arr = FakeArrayField(models.IntegerField())
        nullable_arr = FakeArrayField(models.IntegerField(), null=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_force_nullable_array")

    field = _concrete_field(_ArrOwner, "arr")
    widened = convert_scalar(field, "OwnerType", force_nullable=True)
    # Outer widened to | None; inner element stays bare int (override is outer-only).
    assert widened == (list[int] | None)
    # The unforced default on the same non-null-outer field is bare list[int].
    assert convert_scalar(field, "OwnerType") == list[int]

    nullable_field = _concrete_field(_ArrOwner, "nullable_arr")
    narrowed = convert_scalar(nullable_field, "OwnerType", force_nullable=False)
    assert narrowed == list[int]


def test_convert_scalar_force_nullable_on_hstore_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """The override flips ``HStoreField`` between ``JSON | None`` and ``JSON``.

    ``HStoreField`` is PostgreSQL-only and fakeshop migrates on SQLite, so this
    unmanaged ``FakeHStoreField`` owner is the only route on SQLite into the ``HStoreField``
    branch of ``django_strawberry_framework/types/converters.py::convert_scalar``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class _HStoreOwner(models.Model):
        data = FakeHStoreField()
        nullable_data = FakeHStoreField(null=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_force_nullable_hstore")

    field = _concrete_field(_HStoreOwner, "data")
    widened = convert_scalar(field, "OwnerType", force_nullable=True)
    assert widened == (strawberry.scalars.JSON | None)

    nullable_field = _concrete_field(_HStoreOwner, "nullable_data")
    narrowed = convert_scalar(nullable_field, "OwnerType", force_nullable=False)
    assert narrowed is strawberry.scalars.JSON


# ---------------------------------------------------------------------------
# File / image read-output mapping (spec-037, Decision 3 / Decision 4)
# ---------------------------------------------------------------------------


class _SubImageField(models.ImageField):
    """A consumer ``ImageField`` subclass, to pin the MRO precedence walk."""


def test_convert_field_output_filefield_to_djangofiletype() -> None:
    """A ``FileField`` resolves to ``DjangoFileType`` via ``FIELD_OUTPUT_TYPE_MAP``.

    The map identity is ``DjangoFileType``; ``convert_field_output`` widens it to
    the default-nullable ``DjangoFileType | None`` (spec-037 Decision 4).
    """
    field = _concrete_field(MediaSpecimen, "attachment")
    assert convert_field_output(field, "OwnerType") == (DjangoFileType | None)
    assert _field_output_type_for(field) is DjangoFileType


def test_convert_field_output_imagefield_to_djangoimagetype() -> None:
    """An ``ImageField`` resolves to ``DjangoImageType`` via ``FIELD_OUTPUT_TYPE_MAP``.

    Widened to the default-nullable ``DjangoImageType | None`` (spec-037 Decision 4).
    """
    field = _concrete_field(MediaSpecimen, "image")
    assert convert_field_output(field, "OwnerType") == (DjangoImageType | None)


def test_field_output_map_mro_precedence_image_subclass_wins() -> None:
    """An ``ImageField`` subclass resolves to ``DjangoImageType``, never ``DjangoFileType``.

    ``ImageField`` is a ``FileField`` subclass, so the MRO walk must hit the
    ``ImageField`` row before the ``FileField`` row (the same precedence as
    ``PositiveBigIntegerField`` -> ``BigInt`` before ``IntegerField``).
    """

    class _SubImageOwner(models.Model):
        preview = _SubImageField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_subimage_mro")

    field = _concrete_field(_SubImageOwner, "preview")
    assert _field_output_type_for(field) is DjangoImageType
    assert convert_field_output(field, "OwnerType") == (DjangoImageType | None)


def test_convert_field_output_file_image_nullable_by_default() -> None:
    """File/image output is ``<object> | None`` by DEFAULT, regardless of ``blank`` / ``null``.

    The generated parent resolver returns ``None`` for an empty / falsy
    ``FieldFile`` even on a ``null=False, blank=False`` column (legacy rows,
    direct ``Model.objects.create()``, fixtures store ``""``), so the SDL must be
    nullable to match what the resolver can return (spec-037 Decision 4). A
    stronger non-empty invariant is opt-in via ``required_overrides``
    (``force_nullable=False``), covered in the force_nullable test below.

    ``MediaSpecimen`` carries the three arms: ``attachment`` (neither),
    ``optional_attachment`` (``blank=True`` only) and ``spare_image``
    (``null=True`` only, an ``ImageField``).
    """
    required = MediaSpecimen._meta.get_field("attachment")
    blank_file = MediaSpecimen._meta.get_field("optional_attachment")
    null_image = MediaSpecimen._meta.get_field("spare_image")
    assert isinstance(required, models.Field)
    assert isinstance(blank_file, models.Field)
    assert isinstance(null_image, models.Field)
    assert (required.blank, required.null) == (False, False)
    assert (blank_file.blank, blank_file.null) == (True, False)
    assert (null_image.blank, null_image.null) == (False, True)

    assert convert_field_output(required, "OwnerType") == (DjangoFileType | None)
    assert convert_field_output(blank_file, "OwnerType") == (DjangoFileType | None)
    assert convert_field_output(null_image, "OwnerType") == (DjangoImageType | None)


def test_convert_field_output_force_nullable_overrides_default() -> None:
    """``force_nullable`` wins over the default-nullable file/image shape.

    ``required_overrides`` (``force_nullable=False``) forces the bare
    ``DjangoFileType`` even on a ``blank=True`` column -- the opt-in to a stronger
    non-empty invariant; ``nullable_overrides`` (``force_nullable=True``) keeps
    ``DjangoFileType | None`` (the default) on a plain required column.
    """
    required = _concrete_field(MediaSpecimen, "attachment")
    blank_file = _concrete_field(MediaSpecimen, "optional_attachment")

    assert convert_field_output(required, "OwnerType", force_nullable=True) == (
        DjangoFileType | None
    )
    assert convert_field_output(blank_file, "OwnerType", force_nullable=False) is DjangoFileType


def test_convert_field_output_delegates_scalar_columns() -> None:
    """A non-file column delegates to ``convert_scalar`` unchanged."""
    title = _concrete_field(ScalarSpecimen, "label")
    score = _concrete_field(NullableScalarSpecimen, "score")
    assert convert_field_output(title, "OwnerType") is str
    assert convert_field_output(score, "OwnerType") == (float | None)
    # The force_nullable tri-state still threads through to the scalar path.
    assert convert_field_output(title, "OwnerType", force_nullable=True) == (str | None)


def test_file_columns_stay_scalar_on_the_filter_input_path() -> None:
    """The SHARED scalar/filter-input path still sees ``str`` for a file column.

    ``FIELD_OUTPUT_TYPE_MAP`` is read-output-only; ``scalar_for_field`` (the
    lookup ``filters/inputs._scalar_from_model_field`` delegates to) walks
    ``SCALAR_MAP`` only, so a file column resolves to a scalar ``str`` filter
    input and no ``DjangoFileType`` / ``DjangoImageType`` output object ever
    reaches a GraphQL input. ``SCALAR_MAP``'s file/image rows stay ``str``.
    """
    attachment = MediaSpecimen._meta.get_field("attachment")
    image = MediaSpecimen._meta.get_field("image")

    # The package's filter-input scalar lookup keeps file/image columns scalar.
    assert scalar_for_field(attachment) is str
    assert scalar_for_field(image) is str
    assert _scalar_from_model_field(attachment) is str
    assert _scalar_from_model_field(image) is str
    # The shared SCALAR_MAP rows are untouched by the new output map.
    assert SCALAR_MAP[models.FileField] is str
    assert SCALAR_MAP[models.ImageField] is str
    assert FIELD_OUTPUT_TYPE_MAP[models.FileField] is DjangoFileType
    assert FIELD_OUTPUT_TYPE_MAP[models.ImageField] is DjangoImageType


# ---------------------------------------------------------------------------
# Filesystem-path opt-in (spec-048, Decision 1 / Decision 2)
# ---------------------------------------------------------------------------


def test_default_file_output_objects_publish_no_filesystem_path() -> None:
    """``path`` is absent from both default output objects; the opt-in siblings carry it.

    The field surface is read off Strawberry's own type definitions rather than
    off a rendered schema, so the assertion holds for every consumer type at
    once instead of for one generated SDL (spec-048 Decision 1).
    """
    default_file = {
        field.name for field in get_object_definition(DjangoFileType, strict=True).fields
    }
    default_image = {
        field.name for field in get_object_definition(DjangoImageType, strict=True).fields
    }
    assert default_file == {"name", "size", "url"}
    assert default_image == {
        "name",
        "size",
        "url",
        "width",
        "height",
    }
    opt_in_file = {
        field.name for field in get_object_definition(DjangoFilePathType, strict=True).fields
    }
    opt_in_image = {
        field.name for field in get_object_definition(DjangoImagePathType, strict=True).fields
    }
    assert opt_in_file == default_file | {"path"}
    assert opt_in_image == default_image | {"path"}


def test_opt_in_path_field_carries_the_security_description() -> None:
    """The single shared ``path`` definition warns, on BOTH opt-in types.

    The mixin exists so the wording cannot drift between the file and image
    compositions; identity of the description is what proves there is one
    definition rather than two that currently agree.
    """
    file_path = next(
        field
        for field in get_object_definition(DjangoFilePathType, strict=True).fields
        if field.name == "path"
    )
    image_path = next(
        field
        for field in get_object_definition(DjangoImagePathType, strict=True).fields
        if field.name == "path"
    )
    assert file_path.description == image_path.description
    assert file_path.description is not None
    assert "SECURITY" in file_path.description
    assert "filesystem_path_fields" in file_path.description


def test_convert_field_output_swaps_in_the_path_bearing_sibling() -> None:
    """``expose_filesystem_path`` routes a file/image column to its opt-in sibling.

    The nullability tri-state is unchanged by the swap: the opt-in type is
    nullable by default for the same empty-``FieldFile`` reason the default one
    is (spec-037 Decision 4), and ``force_nullable=False`` still narrows it.
    """
    attachment = _concrete_field(MediaSpecimen, "attachment")
    image = _concrete_field(MediaSpecimen, "image")
    assert convert_field_output(attachment, "OwnerType") == (DjangoFileType | None)
    assert convert_field_output(attachment, "OwnerType", expose_filesystem_path=True) == (
        DjangoFilePathType | None
    )
    assert convert_field_output(image, "OwnerType", expose_filesystem_path=True) == (
        DjangoImagePathType | None
    )
    assert (
        convert_field_output(
            attachment,
            "OwnerType",
            force_nullable=False,
            expose_filesystem_path=True,
        )
        is DjangoFilePathType
    )
    assert FILESYSTEM_PATH_OUTPUT_TYPE_MAP[DjangoFileType] is DjangoFilePathType
    assert FILESYSTEM_PATH_OUTPUT_TYPE_MAP[DjangoImageType] is DjangoImagePathType


def test_consumer_imagefield_subclass_opts_in_to_the_image_sibling() -> None:
    """The opt-in follows the MRO walk's answer, so a subclass keeps its dimensions.

    A consumer ``ImageField`` subclass resolves to ``DjangoImageType`` through
    ``_field_output_type_for``; the path swap is keyed on THAT answer rather
    than on the field class again, so the subclass reaches
    ``DjangoImagePathType`` and not the dimensionless file sibling.
    """

    class _SubImageOwner(models.Model):
        preview = _SubImageField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_filesystem_path_subclass")

    preview = _concrete_field(_SubImageOwner, "preview")
    assert convert_field_output(preview, "OwnerType", expose_filesystem_path=True) == (
        DjangoImagePathType | None
    )


def test_unsupported_field_message_names_the_field_class_and_label() -> None:
    """The unsupported-field rejection names the real field class and ``Model.field``."""

    class _UnsupportedField(models.Field[object, object]):
        pass

    class _LabelOwner(models.Model):
        weird = _UnsupportedField()

        class Meta:
            app_label = _unique_app_label("test_unsupported_label")

    with pytest.raises(ConfigurationError) as exc_info:
        scalar_for_field(_concrete_field(_LabelOwner, "weird"))
    assert str(exc_info.value) == (
        "Unsupported Django field type '_UnsupportedField' on _LabelOwner.weird. "
        "Add an entry to SCALAR_MAP or exclude this field via Meta.exclude."
    )
    assert _field_label(_UnsupportedField()) == "<unbound>.None"
