"""Package tests for inspect_django_type helpers and throwaway-type branches.

Happy-path tables, connection-only ``PeriodicalType.issues``, file/image converter
columns, dotted-path / ``--schema`` / unregistered-name / non-DjangoType failures,
and ``Meta.name`` bare lookup (including the Python class-name back-compat) live
in ``examples/fakeshop/tests/test_inspect_django_type.py``. What stays here has no
fakeshop shape: argparse ``--schema`` help; a custom ``NameConverter`` (prefixing
every SDL name would break the live GraphQL suite); empty-registry unfinalized /
no-Meta bases; function-local UNRESOLVED forward refs; direct ``relay.Node``
inheritance; a ``Meta.name`` / ``__name__`` collision; the ``ImageField`` path opt-in
(no shipped type opts an image column in); helper rendering
(``_sdl_type_name``, ``_render_annotation``, ``_scalar_name``); and the
``ArrayField`` / ``HStoreField`` converter rows, which only PostgreSQL columns
reach. A process-wide name converter in fakeshop would change the shipped SDL.
The relation-pk rows read real library models (the ``PatronProfile.patron``
one-to-one pk and the ``LendingDesk.venue_ptr`` parent link) through test-local
Relay-shaped types; the only Django models this module declares are the
unmanaged hosts of the ``tests/_postgres_fields.py`` container doubles.
"""

import sys
import types
from collections.abc import Iterator
from enum import Enum
from functools import partial
from io import StringIO
from typing import ClassVar, NewType

import pytest
import strawberry
from apps.library.models import Edition, LendingDesk, Patron, PatronProfile, Publisher, Venue
from apps.products.models import Category, Item
from apps.scalars.models import MediaSpecimen
from django.core.management import CommandError, call_command
from django.db import models
from django.utils.module_loading import import_string
from strawberry import relay
from strawberry.schema.name_converter import NameConverter
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types, strawberry_config
from django_strawberry_framework.management.commands.inspect_django_type import (
    _NOT_PUBLISHED,
    Command,
    _render_annotation,
    _scalar_converter,
    _scalar_name,
    _sdl_type_name,
    _strawberry_field_type,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.base import _is_suppressed_relay_pk
from tests._idioms import stub_module
from tests._postgres_fields import FakeArrayField, FakeHStoreField, patch_array_field
from tests.optimizer import _link_models


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# The namer a ``--schema``-less run uses: Strawberry's converter for a ``strawberry_config()`` schema.
_COLD_NAMER = partial(_scalar_name, converter=_scalar_converter(None))


def _make_test_module(monkeypatch: pytest.MonkeyPatch, **attrs: object) -> types.ModuleType:
    module = stub_module("test_module", **attrs)
    monkeypatch.setitem(sys.modules, "test_module", module)
    return module


def test_ambiguous_bare_name_lists_copyable_dotted_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every ambiguity candidate is a directly reusable dotted object path."""
    meta_a = type("Meta", (), {"model": Category, "fields": ("id", "name")})
    duplicate_a = type(
        "DupType",
        (DjangoType,),
        {"__module__": "management_duplicate_types_a", "Meta": meta_a},
    )
    module_a = stub_module("management_duplicate_types_a", DupType=duplicate_a)
    monkeypatch.setitem(sys.modules, module_a.__name__, module_a)
    meta_b = type("Meta", (), {"model": Item, "fields": ("id", "name")})
    duplicate_b = type(
        "DupType",
        (DjangoType,),
        {"__module__": "management_duplicate_types_b", "Meta": meta_b},
    )
    module_b = stub_module("management_duplicate_types_b", DupType=duplicate_b)
    monkeypatch.setitem(sys.modules, module_b.__name__, module_b)

    path_a = f"{module_a.__name__}.DupType"
    path_b = f"{module_b.__name__}.DupType"
    with pytest.raises(CommandError, match=r"DupType is ambiguous") as exc_info:
        call_command("inspect_django_type", "DupType")

    message = str(exc_info.value)
    assert f"  - {path_a} (model Category)" in message
    assert f"  - {path_b} (model Item)" in message
    assert import_string(path_a) is duplicate_a
    assert import_string(path_b) is duplicate_b


def test_schema_help_documents_naming_and_cold_process_requirements() -> None:
    parser = Command().create_parser("manage.py", "inspect_django_type")
    schema_action = next(
        action for action in parser._actions if "--schema" in action.option_strings
    )

    assert schema_action.help == (
        "Import the project schema first to register and finalize types and use its "
        "naming configuration; required for bare names in a cold process"
    )


def test_schema_option_uses_schema_naming_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--schema`` makes object and scalar names match that schema's actual SDL."""

    class PrefixedNames(NameConverter):
        @override
        def from_object(self, object_type: StrawberryObjectDefinition) -> str:
            return f"Api{super().from_object(object_type)}"

    TokenValue = NewType("TokenValue", str)
    token_definition = strawberry.scalar(name="OpaqueToken", serialize=str)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemRefType(DjangoType):
        description: TokenValue

        class Meta:
            model = Item
            fields = ("id", "description", "category")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> ItemRefType:
            raise NotImplementedError

    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(
            extra_scalar_map={TokenValue: token_definition},
            name_converter=PrefixedNames(),
        ),
    )
    _make_test_module(monkeypatch, schema=schema)
    out = StringIO()
    call_command(
        "inspect_django_type",
        "ItemRefType",
        "--schema",
        "test_module:schema",
        stdout=out,
    )
    rendered = out.getvalue()

    assert "ApiCategoryType!" in _connection_row(rendered, "category")
    assert "OpaqueToken!" in _connection_row(rendered, "description")
    sdl = str(schema)
    assert "category: ApiCategoryType!" in sdl
    assert "description: OpaqueToken!" in sdl


def test_bare_name_resolves_converter_applied_sdl_name_and_titles_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A custom ``NameConverter``'s SDL name resolves as a bare name AND titles the table.

    The operator pastes the name they see in the schema (``ApiItemRefType`` under a
    prefixing converter), not the Python class name, and the table title renders
    that same converter-applied name. Both require threading the schema's
    ``NameConverter`` (supplied by ``--schema``) into bare-name resolution and
    table rendering, since ``graphql_type_name`` alone ignores the converter.
    """

    class PrefixedNames(NameConverter):
        @override
        def from_object(self, object_type: StrawberryObjectDefinition) -> str:
            return f"Api{super().from_object(object_type)}"

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemRefType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> ItemRefType:
            raise NotImplementedError

    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(name_converter=PrefixedNames()),
    )
    _make_test_module(monkeypatch, schema=schema)
    out = StringIO()
    call_command(
        "inspect_django_type",
        "ApiItemRefType",  # the converter-applied SDL name, NOT the Python class name
        "--schema",
        "test_module:schema",
        stdout=out,
    )
    title = out.getvalue().splitlines()[0]
    assert title.startswith("ApiItemRefType  (model:")


def test_abstract_base_without_definition_raises_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A DjangoType subclass with no Meta never registers a definition.
    class AbstractBase(DjangoType):
        pass

    _make_test_module(monkeypatch, AbstractBase=AbstractBase)
    with pytest.raises(CommandError, match="not a registered DjangoType"):
        call_command("inspect_django_type", "test_module.AbstractBase")


def test_unfinalized_type_raises_command_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # A concrete registered DjangoType whose definition.finalized is False
    # (finalize_django_types() has not run) is a distinct branch from the
    # no-definition case above.
    class ConcreteType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert ConcreteType.__django_strawberry_definition__.finalized is False
    _make_test_module(monkeypatch, ConcreteType=ConcreteType)
    with pytest.raises(CommandError, match=r"finalize_django_types\(\) has not run"):
        call_command("inspect_django_type", "test_module.ConcreteType")


def test_strawberry_field_type_refuses_an_unfinalized_type() -> None:
    """Finalization attaches the Strawberry definition the field read needs; before it, a ``TypeError``.

    ``handle`` refuses an unfinalized type first, so the command never reaches this read.
    """

    class UnfinalizedType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    definition = UnfinalizedType.__django_strawberry_definition__
    assert definition.finalized is False
    with pytest.raises(TypeError, match="does not have a StrawberryObjectDefinition"):
        _strawberry_field_type(definition, "name")


def _inspect_text(type_name: str) -> str:
    """Return the ``inspect_django_type`` table printed for the registered ``type_name``."""
    out = StringIO()
    call_command("inspect_django_type", type_name, stdout=out)
    return out.getvalue()


def test_inspect_array_rows_name_the_array_arm_and_each_element_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An ``ArrayField`` row names the array arm and, inside it, its element's own label.

    A choices ``base_field`` reads ``choice enum`` inside the list, and a plain one names
    the ``SCALAR_MAP`` row the element converts through.
    """
    patch_array_field(monkeypatch)

    class TaggedShelf(models.Model):
        tags = FakeArrayField(models.CharField(max_length=5))
        grades = FakeArrayField(models.CharField(max_length=1, choices=[("a", "A"), ("b", "B")]))

        class Meta:
            managed = False
            app_label = "test_inspect_array"

    class TaggedShelfType(DjangoType):
        class Meta:
            model = TaggedShelf
            fields = ("tags", "grades")

    assert registry.get(TaggedShelf) is TaggedShelfType
    finalize_django_types()
    text = _inspect_text("TaggedShelfType")
    assert _connection_row(text, "tags").endswith("ArrayField -> list[SCALAR_MAP[CharField]]")
    assert _connection_row(text, "grades").endswith("ArrayField -> list[choice enum]")


def test_inspect_hstore_row_names_the_hstore_arm(monkeypatch: pytest.MonkeyPatch) -> None:
    """An ``HStoreField`` row names the HStore arm, which converts to ``JSON``."""
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

    class TaggedLedger(models.Model):
        attributes = FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_inspect_hstore"

    class TaggedLedgerType(DjangoType):
        class Meta:
            model = TaggedLedger
            fields = ("attributes",)

    assert registry.get(TaggedLedger) is TaggedLedgerType
    finalize_django_types()
    assert _connection_row(_inspect_text("TaggedLedgerType"), "attributes").endswith(
        "HStoreField -> JSON",
    )


def test_inspect_image_path_opt_in_row_names_the_swapped_output_object() -> None:
    """An ``ImageField`` path opt-in names ``DjangoImagePathType`` in both columns.

    ``Meta.filesystem_path_fields`` swaps the image column's output object through
    ``FILESYSTEM_PATH_OUTPUT_TYPE_MAP``; the converter column names the object the
    converter produced, the same one the type column renders. No shipped fakeshop
    type opts an image column in, so the row is built over ``scalars.MediaSpecimen``.
    """

    class ImagePathSpecimenType(DjangoType):
        class Meta:
            model = MediaSpecimen
            fields = ("id", "image")
            filesystem_path_fields = ("image",)

    assert registry.get(MediaSpecimen) is ImagePathSpecimenType
    finalize_django_types()
    image_cols = _connection_row(_inspect_text("ImagePathSpecimenType"), "image").split()
    assert image_cols[2:4] == ["DjangoImagePathType", "yes"]
    assert " ".join(image_cols[4:]) == "convert_field_output -> DjangoImagePathType"


def test_sdl_type_name_ignores_inherited_strawberry_definition() -> None:
    """A partially finalized child uses its own pending GraphQL name."""

    class FinalizedParent(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class PendingChild(FinalizedParent):
        class Meta(FinalizedParent.Meta):
            name = "PendingAlias"

    # Finalization processing the parent but not yet the child.
    strawberry.type(FinalizedParent)

    assert "__strawberry_definition__" in FinalizedParent.__dict__
    assert "__strawberry_definition__" not in PendingChild.__dict__
    definition = PendingChild.__django_strawberry_definition__
    assert _sdl_type_name(PendingChild, definition, NameConverter()) == "PendingAlias"


def test_render_annotation_renders_multi_member_union() -> None:
    # A consumer-authored union annotation (>1 non-None member) renders each
    # member name joined by " | " with no trailing "!" on the members.
    assert _render_annotation(int | str, _COLD_NAMER) == "Int | String"


def test_inspect_unresolved_forward_ref_relation_raises_command_error() -> None:
    """An annotation-only relation forward ref ``finalize`` can't resolve raises CommandError.

    ``CatType.items: list["ItemType"]`` is an annotation-only relation override.
    Both types are defined in this function's local scope, so the ``"ItemType"``
    forward reference is absent from the type's module globals; Strawberry leaves
    ``field.type`` as its ``UNRESOLVED`` sentinel after ``finalize_django_types()``
    alone (constructing a ``strawberry.Schema`` would force resolution). The
    command must refuse to print the sentinel as a real GraphQL type -- which is
    exactly the field Strawberry itself rejects at schema-build time -- and raise
    ``CommandError`` with a recovery hint instead.
    """

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CatType(DjangoType):
        items: list["ItemType"]

        class Meta:
            model = Category
            fields = ("id", "items")

    assert registry.get(Category) is CatType

    finalize_django_types()
    with pytest.raises(CommandError, match=r"unresolved Strawberry forward reference"):
        call_command("inspect_django_type", "CatType")


def _connection_row(text: str, field_name: str) -> str:
    """Return the table row whose first token is ``field_name`` (per-row isolation)."""
    for line in text.splitlines():
        if line.strip().split(" ", 1)[:1] == [field_name]:
            return line
    raise AssertionError(f"no row for field {field_name!r} in:\n{text}")


def test_inspect_direct_relay_node_inheritance_suppresses_pk_row() -> None:
    """Direct ``class Foo(DjangoType, relay.Node)`` reports the interface's ``ID!`` for the pk.

    The inspect command must flow through the shared suppression verdict in
    ``types/base.py`` (via ``_is_suppressed_relay_pk``) for both the
    ``Meta.interfaces`` arm covered by fakeshop ``BookType`` and this
    direct-inheritance arm, not a Meta-only membership check. A naive
    ``relay.Node in definition.interfaces`` would miss this spelling and fall
    through to a scalar / relation row for the pk.
    """

    class CategoryNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryNode

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "CategoryNode", stdout=out)
    text = out.getvalue()

    id_row = _connection_row(text, "id")
    assert " ID! " in id_row
    assert "relay.Node id" in id_row
    assert "SCALAR_MAP" not in id_row


def test_schema_rows_name_each_scalar_as_the_schema_publishes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--schema`` names every scalar as that schema's own converter publishes it.

    ``relay_use_legacy_global_id`` publishes the Relay ``id`` as ``GlobalID!`` where
    the default config publishes ``ID!``, and a ``scalar_overrides`` entry renames a
    column's scalar. Neither lives in ``StrawberryConfig.scalar_map``, so the table
    reads the schema's own merged scalar registry, and each row matches the SDL.
    """
    plain_text = strawberry.scalar(name="PlainText", serialize=str, parse_value=str)

    class CategoryNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> CategoryNode:
            raise NotImplementedError

    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(relay_use_legacy_global_id=True),
        scalar_overrides={str: plain_text},
    )
    _make_test_module(monkeypatch, schema=schema)
    out = StringIO()
    call_command(
        "inspect_django_type",
        "CategoryNode",
        "--schema",
        "test_module:schema",
        stdout=out,
    )
    rendered = out.getvalue()

    assert " GlobalID! " in _connection_row(rendered, "id")
    assert " PlainText! " in _connection_row(rendered, "name")
    sdl = str(schema)
    assert "id: GlobalID!" in sdl
    assert "name: PlainText!" in sdl


def test_inspect_one_to_one_pk_on_relay_type_reports_relation_row() -> None:
    """A OneToOneField primary key on a Relay-Node-shaped type renders as a relation.

    ``_build_annotations`` suppresses the pk annotation for a Relay-shaped type
    only in its NON-relation branch, so a relation pk keeps its auto-synthesized
    annotation and finalize resolves it to the target type.
    ``apps/library/models.py::PatronProfile`` is keyed by its one-to-one
    ``patron``, so the schema surface
    exposes ``patron: <TargetType>!`` (the pk column's relation field)
    alongside the interface-supplied ``id: ID!`` - the pk field is NOT the
    id field. The table must mirror that: a relation row naming the resolved
    target type, never the interface's ``ID!`` row.
    """

    class InspRelPkTargetType(DjangoType):
        class Meta:
            model = Patron
            primary = True
            fields = ("id", "name")

    assert registry.get(Patron) is InspRelPkTargetType

    class InspRelPkProfileType(DjangoType):
        class Meta:
            model = PatronProfile
            fields = ("patron", "postal_code")
            interfaces = (relay.Node,)

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "InspRelPkProfileType", stdout=out)
    text = out.getvalue()

    target_row = _connection_row(text, "patron")
    assert "InspRelPkTargetType!" in target_row
    assert "relation: forward FK" in target_row
    assert " ID! " not in target_row
    assert "relay.Node id" not in target_row

    # The table agrees with the schema the type actually builds into.
    @strawberry.type
    class Query:
        @strawberry.field
        def profile(self) -> InspRelPkProfileType:
            raise NotImplementedError

    sdl = str(strawberry.Schema(query=Query))
    assert "patron: InspRelPkTargetType!" in sdl


def test_inspect_mti_parent_link_pk_on_relay_type_reports_relation_row() -> None:
    """An MTI parent-link pk (``<child>_ptr``) renders as a relation row.

    The parent link is a ``OneToOneField`` - it IS ``model._meta.pk`` for the
    child, so the same non-suppression contract applies: the field renders the
    resolved parent type, not the interface's ``ID!`` (the id derives FROM the
    ptr column, but the GraphQL field named for it is a relation type).
    ``apps/library/models.py::LendingDesk``'s ``venue_ptr`` is that pk.
    """

    class InspRelPkParentType(DjangoType):
        class Meta:
            model = Venue
            primary = True
            fields = ("id", "name")

    assert registry.get(Venue) is InspRelPkParentType

    class InspRelPkChildType(DjangoType):
        class Meta:
            model = LendingDesk
            fields = ("venue_ptr", "window_count")
            interfaces = (relay.Node,)

    assert registry.get(LendingDesk) is InspRelPkChildType

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "InspRelPkChildType", stdout=out)
    text = out.getvalue()

    ptr_row = _connection_row(text, "venue_ptr")
    assert "InspRelPkParentType" in ptr_row
    assert "relation: forward FK" in ptr_row
    assert " ID! " not in ptr_row
    assert "relay.Node id" not in ptr_row


def _mirror_check(type_cls: type[DjangoType], field_name: str, *, expected: bool) -> None:
    """Assert the predictor matches the build-time record for one field.

    The oracle compares the owner's verdict on the definition unpack against
    the merged ``origin.__annotations__`` record (present vs absent) - so a
    divergent edit at either call site fails while a behavior-preserving
    hand copy still passes. A consumer-authored pk reads False/present: the
    performer skips synthesis for it yet keeps the consumer annotation, so
    the predictor must agree the field is not suppressed.
    """
    definition = type_cls.__django_strawberry_definition__
    field = next(f for f in definition.selected_fields if f.name == field_name)
    predicted = _is_suppressed_relay_pk(
        definition.origin,
        definition.interfaces,
        definition.model,
        field,
        definition.consumer_authored_fields,
    )
    built_absent = field.name not in definition.origin.__annotations__
    assert predicted is expected, f"{type_cls.__name__}.{field_name}: predictor {predicted}"
    assert built_absent is expected, f"{type_cls.__name__}.{field_name}: built {built_absent}"


def test_inspect_suppressed_pk_mirror_matches_synthesis() -> None:
    """Predictor agrees with the build-time record on the covered population.

    Mirror-consistency gate: ``_is_suppressed_relay_pk`` must equal the
    build-time fact (pk name absent from ``origin.__annotations__``) for every
    selected field.
    Population: Relay scalar pk (True/absent, both the default-``id`` and
    the non-``id`` ``Edition.isbn_13`` spellings), non-Relay scalar pk
    (False/present control), direct ``relay.Node`` inheritance
    (True/absent), Relay + non-Relay relation pks
    (``PatronProfile.patron``, False/present), and a consumer-authored
    ``Edition.isbn_13`` override on a Relay-shaped type (False/present -
    the performer keeps the consumer annotation, so the predictor must not
    claim the interface row).
    """

    class MirrorRelayCategory(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class MirrorPlainCategory(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    _mirror_check(MirrorRelayCategory, "id", expected=True)
    _mirror_check(MirrorPlainCategory, "id", expected=False)
    registry.clear()

    class MirrorDirectCategory(DjangoType, relay.Node):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")

    class MirrorRelayCode(DjangoType):
        class Meta:
            model = Edition
            primary = True
            fields = ("isbn_13", "isbn_10")
            interfaces = (relay.Node,)

    finalize_django_types()
    _mirror_check(MirrorDirectCategory, "id", expected=True)
    _mirror_check(MirrorRelayCode, "isbn_13", expected=True)
    registry.clear()

    class MirrorConsumerRelayCode(DjangoType):
        isbn_13: str

        class Meta:
            model = Edition
            primary = True
            fields = ("isbn_13", "isbn_10")
            interfaces = (relay.Node,)

    finalize_django_types()
    _mirror_check(MirrorConsumerRelayCode, "isbn_13", expected=False)
    registry.clear()

    class MirrorRelTargetType(DjangoType):
        class Meta:
            model = Patron
            primary = True
            fields = ("id", "name")

    assert registry.get(Patron) is MirrorRelTargetType

    class MirrorRelayProfile(DjangoType):
        class Meta:
            model = PatronProfile
            primary = True
            fields = ("patron", "postal_code")
            interfaces = (relay.Node,)

    class MirrorPlainProfile(DjangoType):
        class Meta:
            model = PatronProfile
            fields = ("patron", "postal_code")

    finalize_django_types()
    _mirror_check(MirrorRelayProfile, "patron", expected=False)
    _mirror_check(MirrorPlainProfile, "patron", expected=False)


def test_inspect_consumer_authored_pk_on_relay_type_reports_consumer_row() -> None:
    """A consumer pk override on a Relay-shaped type renders its consumer row.

    The performer skips auto-synthesis for any name in
    ``consumer_authored_fields`` before the Relay-pk suppression check, so a
    consumer ``isbn_13: str`` override keeps its annotation and the schema
    exposes the consumer's type. The table must mirror that: the consumer
    converter row, never the interface's ``ID!`` row.
    """

    class InspConsumerPkType(DjangoType):
        isbn_13: str

        class Meta:
            model = Edition
            fields = ("isbn_13", "isbn_10")
            interfaces = (relay.Node,)

    assert registry.get(Edition) is InspConsumerPkType

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "InspConsumerPkType", stdout=out)
    text = out.getvalue()

    pk_row = _connection_row(text, "isbn_13")
    assert " ID! " not in pk_row
    assert "relay.Node id" not in pk_row
    assert "consumer annotation (scalar)" in pk_row


def _table(text: str) -> list[str]:
    """Return the title and field rows of a printed table, each with its whitespace collapsed.

    The two header lines (column names and rule) are fixed text and are skipped.
    """
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return [lines[0], *lines[3:]]


def test_inspect_node_id_over_relay_pk_reports_the_interface_id_row() -> None:
    """``id: relay.NodeID[int]`` publishes no field of its own; the schema's ``id`` is ``ID!``.

    Strawberry treats a ``relay.NodeID`` annotation as private, so the consumer
    pk override leaves ``__strawberry_definition__`` without an ``id`` field and
    the ``relay.Node`` interface supplies ``id: ID!``.
    """

    class InspNodeIdPkType(DjangoType):
        id: relay.NodeID[int]

        class Meta:
            model = Publisher
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert registry.get(Publisher) is InspNodeIdPkType

    finalize_django_types()
    assert _table(_inspect_text("InspNodeIdPkType")) == [
        "InspNodeIdPkType (model: apps.library.models.Publisher)",
        "id BigAutoField ID! no relay.Node id",
        "name TextField String! no SCALAR_MAP[TextField]",
    ]


def test_inspect_node_id_over_text_relay_pk_reports_the_interface_id_row() -> None:
    """A ``relay.NodeID[str]`` over a text pk not named ``id`` reports the interface's ``ID!``."""

    class InspNodeIdTextPkType(DjangoType):
        isbn_13: relay.NodeID[str]

        class Meta:
            model = Edition
            fields = ("isbn_13", "isbn_10")
            interfaces = (relay.Node,)

    assert registry.get(Edition) is InspNodeIdTextPkType

    finalize_django_types()
    assert _table(_inspect_text("InspNodeIdTextPkType")) == [
        "InspNodeIdTextPkType (model: apps.library.models.Edition)",
        "isbn_13 TextField ID! no relay.Node id",
        "isbn_10 TextField String! no SCALAR_MAP[TextField]",
    ]


def test_inspect_node_id_over_pk_without_node_interface_is_not_a_field() -> None:
    """Without the ``relay.Node`` interface nothing publishes an ``id``, so the pk is no field."""

    class InspNodeIdPlainPkType(DjangoType):
        id: relay.NodeID[int]

        class Meta:
            model = Publisher
            fields = ("id", "name")

    assert registry.get(Publisher) is InspNodeIdPlainPkType

    finalize_django_types()
    assert _table(_inspect_text("InspNodeIdPlainPkType")) == [
        "InspNodeIdPlainPkType (model: apps.library.models.Publisher)",
        "id BigAutoField - - (not a GraphQL field)",
        "name TextField String! no SCALAR_MAP[TextField]",
    ]


def test_inspect_private_column_on_a_plain_type_is_not_a_field() -> None:
    """A ``strawberry.Private`` column override publishes no field."""

    class InspPrivatePlainType(DjangoType):
        house_code: strawberry.Private[str]

        class Meta:
            model = Publisher
            fields = ("id", "name", "house_code")

    assert registry.get(Publisher) is InspPrivatePlainType

    finalize_django_types()
    assert _table(_inspect_text("InspPrivatePlainType")) == [
        "InspPrivatePlainType (model: apps.library.models.Publisher)",
        "id BigAutoField Int! no SCALAR_MAP[BigAutoField]",
        "name TextField String! no SCALAR_MAP[TextField]",
        "house_code TextField - - (not a GraphQL field)",
    ]


def test_inspect_private_column_on_a_relay_type_is_not_a_field() -> None:
    """On a Relay-shaped type a private non-pk column is no field; the pk keeps its ``ID!`` row."""

    class InspPrivateRelayType(DjangoType):
        house_code: strawberry.Private[str]

        class Meta:
            model = Publisher
            fields = ("id", "name", "house_code")
            interfaces = (relay.Node,)

    assert registry.get(Publisher) is InspPrivateRelayType

    finalize_django_types()
    assert _table(_inspect_text("InspPrivateRelayType")) == [
        "InspPrivateRelayType (model: apps.library.models.Publisher)",
        "id BigAutoField ID! no relay.Node id",
        "name TextField String! no SCALAR_MAP[TextField]",
        "house_code TextField - - (not a GraphQL field)",
    ]


def test_inspect_class_var_column_is_not_a_field() -> None:
    """A ``ClassVar`` column annotation publishes no field."""

    class InspClassVarType(DjangoType):
        house_code: ClassVar[str]

        class Meta:
            model = Publisher
            fields = ("id", "name", "house_code")

    assert registry.get(Publisher) is InspClassVarType

    finalize_django_types()
    assert _table(_inspect_text("InspClassVarType")) == [
        "InspClassVarType (model: apps.library.models.Publisher)",
        "id BigAutoField Int! no SCALAR_MAP[BigAutoField]",
        "name TextField String! no SCALAR_MAP[TextField]",
        "house_code TextField - - (not a GraphQL field)",
    ]


def test_strawberry_field_type_answers_not_published_for_a_dropped_name() -> None:
    """A name Strawberry published no field for reads ``_NOT_PUBLISHED``, a published one its type."""

    class InspDroppedType(DjangoType):
        house_code: strawberry.Private[str]

        class Meta:
            model = Publisher
            fields = ("id", "name", "house_code")

    finalize_django_types()
    definition = InspDroppedType.__django_strawberry_definition__
    assert _strawberry_field_type(definition, "house_code") is _NOT_PUBLISHED
    assert _strawberry_field_type(definition, "name") is str


def test_inspect_uses_sdl_names_for_renamed_relation_and_consumer_enum() -> None:
    """Renamed auto-relation and finalized consumer-enum metadata report SDL names."""

    @strawberry.enum(name="PublishedState")
    class State(Enum):
        DRAFT = "draft"

    class RenamedCategoryType(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")
            name = "Category"

    assert registry.get(Category) is RenamedCategoryType

    class ItemRefType(DjangoType):
        name: State

        class Meta:
            model = Item
            fields = ("id", "name", "category")

    assert registry.get(Item) is ItemRefType

    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "ItemRefType", stdout=out)
    text = out.getvalue()

    category_row = _connection_row(text, "category")
    assert "Category!" in category_row
    assert "relation: forward FK" in category_row
    assert "RenamedCategoryType" not in text
    assert "PublishedState!" in _connection_row(text, "name")


@pytest.mark.parametrize(
    ("child_name", "label"),
    [
        ("LnkPairChild", "relation: forward ForeignObject"),
        ("LnkColumnChild", "relation: forward ForeignObject"),
        ("LnkSlugChild", "relation: forward FK"),
    ],
    ids=["two_column_fo", "one_column_fo", "to_field_fk"],
)
def test_inspect_labels_a_forward_foreign_object_by_its_link(child_name: str, label: str) -> None:
    """A forward ``ForeignObject`` row reads ``forward ForeignObject``; a ``ForeignKey`` ``forward FK``.

    Only a ``ForeignKey`` (any ``to_field``) stores the link in a column of its
    own; a ``ForeignObject`` joins on its carrier columns, one or several.
    """
    type(
        "LnkParentInspectType",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": _link_models.LnkParent, "fields": ("id", "label")})},
    )
    type(
        "LnkChildInspectType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": getattr(_link_models, child_name), "fields": ("id", "parent")},
            ),
        },
    )
    finalize_django_types()
    out = StringIO()
    call_command("inspect_django_type", "LnkChildInspectType", stdout=out)
    parent_row = _connection_row(out.getvalue(), "parent")
    assert "LnkParentInspectType!" in parent_row
    assert parent_row.rstrip().endswith(label)


def test_bare_name_meta_name_collision_with_python_name_is_ambiguous() -> None:
    """``Meta.name`` of one type colliding with another's ``__name__`` is ambiguous."""

    class CategoryView(DjangoType):
        class Meta:
            model = Category
            primary = True
            fields = ("id", "name")
            name = "ItemType"

    assert registry.get(Category) is CategoryView

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    finalize_django_types()
    with pytest.raises(CommandError, match=r"ItemType is ambiguous") as exc_info:
        call_command("inspect_django_type", "ItemType")
    message = str(exc_info.value)
    assert "CategoryView" in message
    assert "ItemType" in message
    assert "fully-dotted object paths" in message


def test_scalar_name_uses_custom_scalar_definition_name() -> None:
    """A custom scalar wrapper reports its explicit SDL name, never its object repr."""

    class TokenValue:
        pass

    with pytest.warns(DeprecationWarning, match=r"Passing a class to strawberry\.scalar\(\)"):
        token = strawberry.scalar(TokenValue, name="OpaqueToken", serialize=str)

    assert _COLD_NAMER(token) == "OpaqueToken"


def test_scalar_name_uses_named_union_metadata() -> None:
    """A finalized named union leaf reports its SDL name, never its object repr."""
    assert _COLD_NAMER(strawberry.union("SearchResult")) == "SearchResult"


def test_scalar_name_falls_back_to_dunder_name_for_definitionless_type() -> None:
    """A mapless leaf with no Strawberry definition falls back to ``__name__``."""

    class UnmappedCustomScalar:
        pass

    assert _COLD_NAMER(UnmappedCustomScalar) == "UnmappedCustomScalar"


def test_scalar_name_reads_a_non_class_leafs_declared_name_or_its_text() -> None:
    """A non-class leaf reports its stored ``__name__``, else its own text."""

    class _Nameless:
        @override
        def __str__(self) -> str:
            return "nameless-leaf"

    assert _COLD_NAMER(NewType("OpaqueId", str)) == "OpaqueId"
    assert _COLD_NAMER(_Nameless()) == "nameless-leaf"
