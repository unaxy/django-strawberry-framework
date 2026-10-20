"""Write-pipeline resolver tests.

Internals a live fakeshop request cannot express: custom ``relay.NodeID`` write
locate (shipped ``CategoryType`` uses pk; changing it would retarget every
Category GlobalID), ``_unprovided_exclude`` / ``coerce_lookup_id`` helpers, a
create over a multi-table child of a client-keyed parent and through a ``save()``
override that saves twice, the ``update_fields`` an update names for a proxy, a three-table
row, a non-key parent link, a generated column and a deferred row,
``async def get_queryset`` ``SyncMisuseError``,
async-row leak isolation, Relay M2M hide on a second ``Genre`` primary
(shipped ``GenreType`` has no hide hook; a second primary cannot coexist in the
live process), raw-pk M2M *update* (no shipped ``updateShelf``), unregistered
primary existence-only decode, ``TaggedItem.object_id`` GFK indexing (no
shipped ``TaggedItemType``; rung 1 would add one to the library schema, rung 3
cannot declare ``DjangoMutation`` after the live autouse finalize),
relation-override visibility (no shipped override declares a relation field, so
the composite is package-only), pipeline pk-drift, model-flavor ``full_clean``
wire-name re-key (the only
multi-word validated model column, ``Book.circulation_status``, rides an
enum-guarded input, so no live request can fail its ``full_clean``), the keying
of a save-time Django ``ValidationError`` against the backing model through a
renamed ``Meta.input_class`` input, a relation ``attname`` and a dotted name
(fakeshop's ``Item.save()`` rule raises only ``name``), and
``ScalarSpecimen`` writes (no shipped mutation; rung 1
would add ``CreateScalarSpecimen`` to the scalars schema, rung 3 is the same
late-declaration reject). Consumer-visible create/update/delete, empty-name
``full_clean``, unresolvable relation ids, M2M replace/clear/omit, choice-enum
unwrap, raw-pk create visibility, model-flavor ``Item.attachment`` omit /
replace, the ``PROTECT`` / ``RESTRICT`` refused delete and the
``blank=True, null=False`` FK null guard live in
``examples/fakeshop/test_query/test_products_api.py`` and
``examples/fakeshop/test_query/test_library_api.py``; file-column update omit /
replace / explicit null live in ``examples/fakeshop/test_query/test_uploads_api.py``. Atomicity live in
``examples/fakeshop/test_query/test_mutation_atomicity.py``.
"""

from __future__ import annotations

import contextlib
import inspect
import itertools
from collections.abc import Callable, Generator, Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeAlias, TypeVar
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalars_models
from asgiref.sync import sync_to_async
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, connection, models, transaction
from django.db.models import Model, QuerySet
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from strawberry import relay
from strawberry.types import ExecutionResult
from strawberry.types.base import has_object_definition
from typing_extensions import Self, override

from django_strawberry_framework import (
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.resolvers import resolve_form_sync
from django_strawberry_framework.mutations import resolvers
from django_strawberry_framework.mutations import resolvers as mutation_resolvers
from django_strawberry_framework.mutations.inputs import (
    NON_FIELD_ERROR_KEY,
    _relation_field_index,
    mutation_input_field_specs,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework.resolvers import resolve_serializer_sync
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import pk_of, read_attr, require_instance
from django_strawberry_framework.utils.errors import validation_error_to_field_errors
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.querysets import SyncMisuseError
from django_strawberry_framework.utils.typing import call_forwarded, object_result
from django_strawberry_framework.utils.write_transaction import (
    managed_write_transaction,
    open_write_pipeline,
    pipeline_write_phase,
    require_write_pipeline,
)
from tests._idioms import is_object_dict, is_object_list, saved_pk
from tests._info import make_info, unread_info
from tests.optimizer import _link_models

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from django_strawberry_framework.mutations.resolvers import _ModelDecoded

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _Text: TypeAlias = models.TextField[str | Combinable, str]


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry (co-clears the mutation ledger + declaration registry) per test."""
    registry.clear()
    yield
    registry.clear()


_category_name_counter = itertools.count(1)


def _category_name() -> str:
    """A unique ``Category.name`` per call.

    ``Category.name`` is ``unique=True``; one test runs with ``transaction=True``
    (real commits, flushed at teardown rather than rolled back), so a fixed name
    can collide across tests depending on ordering. A per-call name keeps every
    test's category independent.
    """
    return f"Cat-{next(_category_name_counter)}"


class _AllowAll:
    """A permission class that authorizes every write (isolates the resolver from auth)."""

    def has_permission(
        self,
        _info: object,
        _mutation: type[object],
        _operation: str,
        _data: object,
        _instance: object = None,
    ) -> bool:
        return True


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _schema(mutation_type: type) -> strawberry.Schema:
    """Build a finalized schema with the optimizer extension installed."""
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_Query,
        mutation=mutation_type,
        extensions=[lambda: optimizer],
    )


# ---------------------------------------------------------------------------
# Products Item/Category fixtures (FK + unique_item_per_category)
# ---------------------------------------------------------------------------


def _build_item_schema(
    *,
    category_get_queryset: object | None = None,
    input_cls: object | None = None,
) -> tuple[strawberry.Schema, tuple[type[DjangoType], type[DjangoType]]]:
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types)."""
    category_body: dict[str, object] = {
        "Meta": type(
            "Meta",
            (),
            {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
        ),
    }
    if category_get_queryset is not None:
        category_body["get_queryset"] = category_get_queryset
    CategoryT = type("CategoryT", (DjangoType, relay.Node), category_body)

    ItemT = type(
        "ItemT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": product_models.Item,
                    "fields": ("id", "name", "category"),
                    "primary": True,
                },
            ),
        },
    )

    create_meta: dict[str, object] = {
        "model": product_models.Item,
        "operation": "create",
        "permission_classes": [_AllowAll],
    }
    if input_cls is not None:
        create_meta["input_class"] = input_cls
    update_meta = {
        "model": product_models.Item,
        "operation": "update",
        "permission_classes": [_AllowAll],
    }
    delete_meta = {
        "model": product_models.Item,
        "operation": "delete",
        "permission_classes": [_AllowAll],
    }

    CreateItem = type("CreateItem", (DjangoMutation,), {"Meta": type("Meta", (), create_meta)})
    UpdateItem = type("UpdateItem", (DjangoMutation,), {"Meta": type("Meta", (), update_meta)})
    DeleteItem = type("DeleteItem", (DjangoMutation,), {"Meta": type("Meta", (), delete_meta)})

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    return _schema(Mutation), (CategoryT, ItemT)


def _json_at(value: object, *path: str | int) -> object:
    """``value`` followed down ``path``: a ``str`` key into an object, an ``int`` index into a list."""
    found = value
    for key in path:
        if isinstance(key, str):
            assert is_object_dict(found), found
            found = found[key]
        else:
            assert is_object_list(found), found
            found = found[key]
    return found


def _json_object(value: object, *path: str | int) -> dict[object, object]:
    """The JSON object at ``path`` under ``value`` (see ``_json_at``)."""
    found = _json_at(value, *path)
    assert is_object_dict(found), found
    return found


def _json_list(value: object, *path: str | int) -> list[object]:
    """The JSON list at ``path`` under ``value`` (see ``_json_at``)."""
    found = _json_at(value, *path)
    assert is_object_list(found), found
    return found


def assert_mutation_field_error(
    result: ExecutionResult,
    payload_key: str,
    field: str,
) -> dict[object, object]:
    """Assert the common in-band mutation error envelope.

    Pins the shape every in-band failure test shares: no top-level GraphQL errors
    (the failure is in-band), a null object slot, and exactly one ``FieldError`` on
    ``field``. Returns the payload so a caller can add test-specific assertions
    (e.g. "no row was written"); those DB side-effect checks stay inline.
    """
    assert result.errors is None, result.errors
    assert result.data is not None
    payload = _json_object(result.data, payload_key)
    assert payload["node"] is None
    errors = _json_list(payload, "errors")
    assert [_json_at(error, "field") for error in errors] == [field], errors
    return payload


_CREATE = (
    "mutation($d: ItemInput!){ createItem(data:$d){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)
_DELETE = (
    "mutation($id: ID!){ deleteItem(id:$id){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)


def _item_gid(item_type: type, pk: object) -> str:
    return global_id_for(item_type, pk)


# ---------------------------------------------------------------------------
# Custom ``relay.NodeID`` write-side
#
# When a primary type encodes a NON-pk column as its Relay id
# (``name: relay.NodeID[str]``), the GlobalID a client holds carries that column's
# value, not the pk. ``decode_model_global_id`` -> ``_resolve_real_pk`` must map it
# to the row's real pk BEFORE the write locate runs ``get(pk=...)``. The unit test
# in ``tests/test_relay_node_field.py`` pins the decode in isolation; these pin a
# real update / delete CONSUMER of that decoded pk end-to-end, with the decoy row
# seeded so its pk's string form IS the target row's ``name`` - the exact pk/name
# confusion the fix guards (the pre-fix value flowed straight into ``get(pk=...)``
# and hit the wrong row).
# ---------------------------------------------------------------------------

# ``name`` is consumed as the Relay id (``relay.NodeID[str]``), so it surfaces as the
# ``id`` field, not a ``name`` field - select ``id`` (the encoded GlobalID) + a plain
# writable column (``description``).
_CATEGORY_UPDATE = (
    "mutation($id: ID!, $d: CategoryPartialInput!){ updateCategory(id:$id, data:$d){ "
    "node{ id description } errors{ field messages } } }"
)
_CATEGORY_DELETE = (
    "mutation($id: ID!){ deleteCategory(id:$id){ node{ id } errors{ field messages } } }"
)


def _build_category_node_schema() -> tuple[strawberry.Schema, type[DjangoType]]:
    """Category primary type with ``name: relay.NodeID[str]`` + update/delete mutations.

    The Relay id encodes the non-pk ``name`` column, so the write-side locate must
    resolve the GlobalID payload (a ``name`` string) to the row's real pk via
    ``_resolve_real_pk`` before ``get(pk=...)`` runs. Returns ``(schema, CategoryNode)``
    so the caller can mint the client-held GlobalID with ``global_id_for``.
    """

    class CategoryNode(DjangoType, relay.Node):
        name: relay.NodeID[str]

        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")
            primary = True

    class UpdateCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "update"
            permission_classes = [_AllowAll]

    class DeleteCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "delete"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_category = DjangoMutationField(UpdateCategory)
        delete_category = DjangoMutationField(DeleteCategory)

    finalize_django_types()
    return _schema(Mutation), CategoryNode


@pytest.mark.django_db
def test_update_custom_node_id_resolves_payload_to_real_pk_not_wrong_row() -> None:
    """A write through a custom ``relay.NodeID[str]`` updates the NAME-matched row, not the pk-coincident one.

    Shipped ``CategoryType`` uses the pk as Relay id; retargeting it would change
    every Category GlobalID. Decode isolation is
    ``tests/test_relay_node_field.py``; this is the write consumer. Live
    ``updateItem`` locates by pk GlobalID
    (``test_products_api.py::test_update_item_non_colliding_partial_update``).
    """
    schema, CategoryNode = _build_category_node_schema()
    decoy = product_models.Category.objects.create(name="decoy", description="decoy-untouched")
    target = product_models.Category.objects.create(
        name=str(saved_pk(decoy)),
        description="before",
    )
    assert saved_pk(target) != saved_pk(decoy)
    assert target.name == str(saved_pk(decoy))

    gid = global_id_for(CategoryNode, target.name)
    res = schema.execute_sync(
        _CATEGORY_UPDATE,
        variable_values={"id": gid, "d": {"description": "after"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    node = _json_object(res.data, "updateCategory", "node")
    assert node["description"] == "after"
    # The returned id is rebuilt from the (unchanged) ``name``, so it round-trips to
    # the same GlobalID - the node returned is the target, not the pk-coincident decoy.
    assert node["id"] == gid

    target.refresh_from_db()
    decoy.refresh_from_db()
    assert target.description == "after"  # the row whose NAME matched the payload
    assert decoy.description == "decoy-untouched"  # the pk-coincident row is untouched


@pytest.mark.django_db
def test_custom_node_id_real_pk_lookup_uses_pinned_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    """A custom NodeID lookup forwards the mutation's pinned database alias.

    The NodeID payload identifies a non-pk column, so
    ``decode_model_global_id`` must resolve that value to a real pk before the
    mutation locates its row. The lookup is part of the write transaction's
    alias contract: a router may send reads to one alias and writes to another,
    and resolving the NodeID through the default manager would miss a row that
    exists only on the write alias. This package-level seam test pins the
    forwarding without requiring a second test database; the live sharded
    fakeshop suite exercises the same contract end to end.
    """
    _schema, CategoryNode = _build_category_node_schema()
    target = product_models.Category.objects.create(name="alias-node-id", description="before")
    gid = global_id_for(CategoryNode, target.name)
    manager = product_models.Category._default_manager
    using = mock.Mock(wraps=manager.using)
    monkeypatch.setattr(manager, "using", using)

    node_id, error = resolvers.coerce_lookup_id(gid, CategoryNode, using="default")

    assert error is None
    assert node_id == saved_pk(target)
    using.assert_called_once_with("default")


@pytest.mark.django_db
def test_delete_custom_node_id_resolves_payload_to_real_pk_not_wrong_row() -> None:
    """A delete through a custom ``relay.NodeID[str]`` removes the NAME-matched row.

    The delete twin of the update case: the located instance comes from the resolved
    real pk, so deleting via a GlobalID whose payload is the target's ``name`` removes
    the target - while the row whose pk's string form equals that ``name`` survives.
    """
    schema, CategoryNode = _build_category_node_schema()
    decoy = product_models.Category.objects.create(name="decoy-del", description="x")
    target = product_models.Category.objects.create(
        name=str(saved_pk(decoy)),
        description="doomed",
    )
    assert saved_pk(target) != saved_pk(decoy)
    assert target.name == str(saved_pk(decoy))

    gid = global_id_for(CategoryNode, target.name)
    res = schema.execute_sync(_CATEGORY_DELETE, variable_values={"id": gid})
    assert res.errors is None, res.errors
    # The snapshot id (preserved for cache eviction) decodes to the target's name.
    assert res.data is not None
    assert res.data["deleteCategory"]["node"]["id"] == gid
    # The NAME-matched target is gone; the row whose pk string equals that name survives.
    assert not product_models.Category.objects.filter(pk=saved_pk(target)).exists()
    assert product_models.Category.objects.filter(pk=saved_pk(decoy)).exists()


def test_unprovided_exclude_keeps_constrained_co_member_drops_unrelated() -> None:
    """``_unprovided_exclude`` pins the constrained-co-member carve-out on ``Item``.

    A ``name``-only provided set keeps ``category`` OUT of the exclude set (the two
    co-participate in ``unique_item_per_category``) while ``description`` /
    ``is_private`` (unconstrained, unprovided) stay excluded.
    """
    exclude = resolvers._unprovided_exclude(product_models.Item, {"name"})
    assert "category" not in exclude  # co-constrained with provided ``name``
    assert "description" in exclude  # unrelated, unprovided
    assert "is_private" in exclude


def test_unprovided_exclude_single_field_unique_group_kept() -> None:
    """A provided single-``unique`` field is its own group; an unprovided unrelated field is excluded."""
    # ``Category.name`` is ``unique=True`` (a 1-element group). Providing ``name``
    # keeps it validating; the unprovided ``description`` is excluded.
    exclude = resolvers._unprovided_exclude(product_models.Category, {"name"})
    assert "name" not in exclude
    assert "description" in exclude


@pytest.mark.parametrize(
    "raw_id",
    ["5", "not-a-global-id", 5],
    ids=["raw-pk-string", "garbage", "non-string"],
)
def test_coerce_lookup_id_rejects_non_globalid(raw_id: str | int) -> None:
    """A non-GlobalID ``id:`` is a ``FieldError`` on ``id`` before any pk lookup.

    Live ``updateItem`` covers the string arms over HTTP
    (``test_products_api.py::test_update_item_malformed_id_is_field_error_no_coercion_crash``).
    GraphQL ``ID`` never delivers a Python ``int``, so the non-string arm has no
    wire shape; this helper pin is the remaining coverage.
    """

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    node_id, error = resolvers.coerce_lookup_id(raw_id, ItemT)
    assert node_id is None
    assert error is not None
    assert error.field == "id"


class KeyedVenue(models.Model):
    """A row keyed by the client's ``code``, the multi-table parent of ``KeyedDesk``."""

    code: _Text = models.TextField(primary_key=True)
    name: _Text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "products"
        managed = False
        db_table = "tests_mutations_keyed_venue"


class KeyedDesk(KeyedVenue):
    """A multi-table child of the client-keyed ``KeyedVenue``; its key is the parent link."""

    seats: _Int = models.IntegerField(default=0)

    # basedpyright: Django's ModelBase pops a concrete model's Meta (only an abstract model keeps
    # one), so KeyedVenue has no Meta at run time for this one to subclass
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        app_label = "products"
        managed = False
        db_table = "tests_mutations_keyed_desk"


class TwiceSavedRow(models.Model):
    """A row Django keys, whose ``save()`` override saves a second time to fill ``slug``."""

    slug: _Text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "products"
        managed = False
        db_table = "tests_mutations_twice_saved_row"

    @override
    def save(self, *args: object, **kwargs: object) -> None:
        call_forwarded(super().save, args, kwargs)
        self.slug = f"saved-{pk_of(self)}"
        call_forwarded(super().save, args, kwargs)


class TwiceSavedKeyedRow(models.Model):
    """``TwiceSavedRow`` keyed by the client's ``code`` instead."""

    code: _Text = models.TextField(primary_key=True)
    slug: _Text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "products"
        managed = False
        db_table = "tests_mutations_twice_saved_keyed_row"

    @override
    def save(self, *args: object, **kwargs: object) -> None:
        call_forwarded(super().save, args, kwargs)
        self.slug = f"saved-{pk_of(self)}"
        call_forwarded(super().save, args, kwargs)


class _UnmanagedProductsModel(models.Model):
    """Abstract base whose ``Meta`` the two models below inherit instead of declaring one."""

    class Meta:
        abstract = True
        app_label = "products"
        managed = False


class LinkedVenue(_UnmanagedProductsModel):
    """The multi-table parent of ``LinkedDesk``."""

    name: _Text = models.TextField(blank=True, default="")


class LinkedDesk(LinkedVenue):
    """A multi-table child keyed by its own column, joined through an ordinary parent link.

    ``venue`` is a ``parent_link`` one-to-one that is not the child's primary key, and
    ``double_seats`` a generated column. No fakeshop model has either shape.
    """

    desk_id: models.AutoField[int | str | Combinable, int] = models.AutoField(primary_key=True)
    venue: models.OneToOneField[LinkedVenue | Combinable, LinkedVenue] = models.OneToOneField(
        LinkedVenue,
        on_delete=models.CASCADE,
        parent_link=True,
    )
    seats: _Int = models.IntegerField(default=0)
    # Unannotated: django-stubs declares ``GeneratedField`` without type parameters, so it
    # has no field generic to spell.
    double_seats = models.GeneratedField(
        expression=models.F("seats") * 2,
        output_field=models.IntegerField(),
        db_persist=True,
    )


class BareVenue(_UnmanagedProductsModel):
    """The multi-table parent of ``BareDesk``."""

    # Typed here: django-stubs types ``Model.pk`` as ``Any``. ``None`` until the row is saved.
    pk: int | None

    name: _Text = models.TextField(blank=True, default="")


class BareDesk(BareVenue):
    """A multi-table child declaring no field of its own: its table holds only its key.

    An ``update_fields`` save names no column of its table, so Django counts the table
    as updated without a statement. No fakeshop model has this shape.
    """


class BareDeskForm(forms.ModelForm[BareDesk]):
    """A ``ModelForm`` over ``BareDesk``'s inherited ``name``."""

    class Meta:
        model = BareDesk
        fields = ("name",)


class _DeleteDeskTableAfterLocate:
    """Authorize, then delete the located desk's own table row, keeping its venue row.

    The stand-in for a concurrent ``delete(keep_parents=True)`` committed between the
    locate and the write, on the pipeline's connection.
    """

    def has_permission(
        self,
        _info: object,
        _mutation: type[object],
        _operation: str,
        _data: object,
        instance: object = None,
    ) -> bool:
        if instance is not None:
            with pipeline_write_phase():
                desk = BareDesk._base_manager.get(pk=read_attr(instance, "pk"))
                _ = desk.delete(keep_parents=True)
        return True


@contextlib.contextmanager
def _tables(*model_classes: type[Model]) -> Generator[None, None, None]:
    """Give ``managed = False`` synthetic models real tables for the test, then drop them."""
    with connection.schema_editor() as schema_editor:
        for model_class in model_classes:
            schema_editor.create_model(model_class)
    try:
        yield
    finally:
        with connection.schema_editor() as schema_editor:
            for model_class in reversed(model_classes):
                schema_editor.delete_model(model_class)


def _create_row(model: type[Model], fields: tuple[str, ...], data: dict[str, object]) -> object:
    """Run one model-flavor ``createRow`` of ``fields`` over ``model``; answer its ``errors``."""
    type(
        f"{model.__name__}T",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": fields, "primary": True})},
    )
    create = type(
        "CreateRow",
        (DjangoMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": model,
                    "fields": fields,
                    "operation": "create",
                    "permission_classes": [_AllowAll],
                },
            ),
        },
    )

    @strawberry.type
    class Mutation:
        create_row = DjangoMutationField(create)

    finalize_django_types()
    res = _schema(Mutation).execute_sync(
        f"mutation($d: {model.__name__}Input!){{ createRow(data: $d){{ "
        "errors{ field messages codes path } } }",
        variable_values={"d": data},
    )
    assert res.errors is None, res.errors
    return _json_at(res.data, "createRow", "errors")


#: The envelope a create answers when its row's key is taken at the INSERT.
_CONSTRAINT_ERRORS = [
    {
        "field": NON_FIELD_ERROR_KEY,
        "messages": ["A database constraint was violated."],
        "codes": ["constraint"],
        "path": [],
    },
]

_COMPETING_VENUE_DISPATCH_UID = "tests.mutations.competing_keyed_venue"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("key", ["free", "raced"])
def test_child_create_inserts_its_client_keyed_parent_row(key: str) -> None:
    """A multi-table child create INSERTs its client-keyed parent row, never UPDATEs one.

    ``KeyedDesk`` inherits ``KeyedVenue``, keyed by the client's ``code``. A free code
    INSERTs both rows without trying an UPDATE on either table. A venue a competing
    writer saves under that code after the uniqueness check is the ``constraint``
    envelope, rolled back with the competing venue, never overwritten and adopted as the
    desk's parent. No fakeshop model inherits a client-keyed parent.
    """
    seen: list[object] = []

    def _insert_competing_venue(instance: Model, **_kwargs: object) -> None:
        seen.append(read_attr(instance, "code"))
        _ = KeyedVenue._base_manager.bulk_create([KeyedVenue(code="K1", name="Competing")])

    with _tables(KeyedVenue, KeyedDesk), CaptureQueriesContext(connection) as queries:
        if key == "raced":
            pre_save.connect(
                _insert_competing_venue,
                sender=KeyedDesk,
                weak=False,
                dispatch_uid=_COMPETING_VENUE_DISPATCH_UID,
            )
        try:
            errors = _create_row(
                KeyedDesk,
                ("code", "name", "seats"),
                {"code": "K1", "name": "Desk", "seats": 3},
            )
        finally:
            _ = pre_save.disconnect(sender=KeyedDesk, dispatch_uid=_COMPETING_VENUE_DISPATCH_UID)
        venues = list(KeyedVenue._base_manager.values_list("code", "name"))
        desks = list(KeyedDesk._base_manager.values_list("code", "seats"))
    updates = [
        query["sql"] for query in queries.captured_queries if query["sql"].startswith("UPDATE")
    ]

    assert updates == []
    if key == "raced":
        assert errors == _CONSTRAINT_ERRORS
        assert seen == ["K1"]
        assert (venues, desks) == ([], [])
    else:
        assert errors == []
        assert (venues, desks) == ([("K1", "Desk")], [("K1", 3)])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "model",
        "fields",
        "data",
        "errors",
        "rows",
    ),
    [
        (
            TwiceSavedRow,
            ("slug",),
            {"slug": ""},
            [],
            [(1, "saved-1")],
        ),
        (
            TwiceSavedKeyedRow,
            ("code", "slug"),
            {"code": "K1"},
            _CONSTRAINT_ERRORS,
            [],
        ),
    ],
    ids=["assigned_key", "client_key"],
)
def test_create_through_a_save_override_that_saves_twice(
    model: type[Model],
    fields: tuple[str, ...],
    data: dict[str, object],
    errors: list[dict[str, object]],
    rows: list[tuple[object, str]],
) -> None:
    """An override saving twice creates on a key Django assigns, not on a client's key.

    On a key Django assigns the create takes a plain ``save()``, so the override's second
    save updates the row its first inserted. On a client-assigned key the create INSERTs
    and the override forwards ``force_insert`` to both saves, so the second is the
    ``constraint`` envelope with nothing written, as under ``QuerySet.create``.
    """
    with _tables(model):
        answered = _create_row(model, fields, data)
        stored = list(model._base_manager.values_list("pk", "slug"))

    assert answered == errors
    assert stored == rows


@pytest.mark.parametrize(
    ("row", "update_fields"),
    [
        pytest.param(product_models.Item, (), id="single-table"),
        pytest.param(library_models.OpenVenue, (), id="proxy"),
        pytest.param(
            library_models.SelfServeDesk,
            (
                "name",
                "opened_on",
                "lead_ticket",
                "window_count",
                "kiosk_code",
            ),
            id="two-parent-links",
        ),
        pytest.param(LinkedDesk, ("name", "venue", "seats"), id="non-key-parent-link"),
    ],
)
def test_located_row_update_fields_names_a_multi_table_rows_loaded_non_key_columns(
    row: type[Model],
    update_fields: tuple[str, ...],
) -> None:
    """Only a row a parent link joins to a second table names columns, minus its keys.

    A single-table row and a proxy of one name nothing (``force_update`` alone covers their
    one table, and their save keeps ``update_fields=None``). A multi-table row names every
    concrete column of every table it spans except each table's primary key (both
    ``<parent>_ptr`` links of the kiosk chain) and a generated column; a parent link that is
    not the child's primary key is an ordinary column and is named, as a plain save writes
    it. Fakeshop updates no proxy, no three-table row and no row of the last shape.
    """
    assert resolvers.located_row_update_fields(row()) == update_fields


@pytest.mark.django_db
def test_located_row_update_fields_leaves_out_deferred_columns() -> None:
    """A deferred multi-table row names only its loaded columns, as Django's own save does.

    The pipeline locates a whole row, so no live update reaches a deferred one.
    """
    desk = library_models.LendingDesk.objects.create(name="Deferred", window_count=2)

    deferred = library_models.LendingDesk.objects.only("name").get(pk=desk.pk)

    assert resolvers.located_row_update_fields(deferred) == ("name",)


@pytest.mark.django_db(transaction=True)
def test_save_located_row_updates_both_tables_through_a_non_key_parent_link() -> None:
    """A multi-table row joined by an ordinary parent link saves as two ``UPDATE`` s.

    Django accepts the named parent link and leaves the generated column to the database:
    the parent table and the child's own each take one ``UPDATE``, no ``INSERT``.
    """
    with _tables(LinkedVenue, LinkedDesk):
        desk = LinkedDesk.objects.create(name="Linked", seats=2)
        desk.name = "Renamed"
        desk.seats = 5

        with CaptureQueriesContext(connection) as queries:
            resolvers.save_located_row(desk)

        stored = list(LinkedDesk._base_manager.values_list("name", "seats", "double_seats"))
    writes = [
        query["sql"].split()[:2]
        for query in queries.captured_queries
        if query["sql"].startswith(("UPDATE", "INSERT"))
    ]

    assert writes == [["UPDATE", '"products_linkedvenue"'], ["UPDATE", '"products_linkeddesk"']]
    assert stored == [("Renamed", 5, 10)]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("flavor", ["model", "form"])
def test_update_of_a_columnless_child_table_deleted_after_the_locate_is_conflict(
    flavor: str,
) -> None:
    """A child table naming no ``update_fields`` column is checked before the save.

    Django counts a table that contributes no column to ``update_fields`` as updated
    without a statement, so a ``BareDesk`` whose own table row was deleted after the
    locate would save its venue and fire ``post_save`` on a desk that no longer exists.
    The pre-save existence check answers ``conflict`` instead: no ``UPDATE`` runs, no
    ``post_save`` fires, and the rollback restores the desk row. The model and
    ``ModelForm`` flavors alike.
    """
    saved: list[object] = []

    def _record(sender: object, **_kwargs: object) -> None:
        saved.append(sender)

    type(
        "BareDeskT",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": BareDesk, "fields": ("id", "name"), "primary": True})},
    )
    meta: dict[str, object] = {
        "operation": "update",
        "permission_classes": [_DeleteDeskTableAfterLocate],
        "select_for_update": False,
    }
    if flavor == "form":
        update = type(
            "UpdateDesk",
            (DjangoModelFormMutation,),
            {"Meta": type("Meta", (), {**meta, "form_class": BareDeskForm})},
        )
    else:
        update = type(
            "UpdateDesk",
            (DjangoMutation,),
            {"Meta": type("Meta", (), {**meta, "model": BareDesk, "fields": ("name",)})},
        )

    @strawberry.type
    class Mutation:
        update_desk = DjangoMutationField(update)

    finalize_django_types()
    with _tables(BareVenue, BareDesk):
        desk = BareDesk.objects.create(name="Bare")
        input_type = "BareDeskFormPartialInput" if flavor == "form" else "BareDeskPartialInput"
        post_save.connect(_record, sender=BareDesk, weak=False)
        try:
            with CaptureQueriesContext(connection) as queries:
                res = _schema(Mutation).execute_sync(
                    f"mutation($id: ID!, $d: {input_type}!){{ updateDesk(id: $id, data: $d){{ "
                    "result { id } errors { field codes } } }",
                    variable_values={"id": str(desk.pk), "d": {"name": "Renamed"}},
                )
        finally:
            _ = post_save.disconnect(_record, sender=BareDesk)
        stored = list(BareDesk._base_manager.values_list("pk", "name"))

    assert res.errors is None, res.errors
    assert _json_at(res.data, "updateDesk") == {
        "result": None,
        "errors": [{"field": "id", "codes": ["conflict"]}],
    }
    assert saved == []
    assert not [
        query["sql"]
        for query in queries.captured_queries
        if query["sql"].startswith(("UPDATE", "INSERT"))
    ]
    assert stored == [(desk.pk, "Bare")]


@pytest.mark.django_db
def test_globalid_relation_override_flows_through_visibility_contract() -> None:
    """A ``GlobalID`` relation override is still relation-visibility-checked (Decision 10).

    The bind-time type-lock (``sets.py::_validate_relation_override_types``) forces a
    relation override to keep the generated ``relay.GlobalID`` id type, so the override
    decodes through the same ``GlobalID`` type-check and Decision-10 visibility check
    as the generated input. This pins the end-to-end guarantee: a
    ``createItem`` whose ``categoryId`` names a ``Category`` hidden by
    ``Category.get_queryset`` is a ``FieldError`` on ``categoryId`` (hidden
    indistinguishable from missing, no existence leak) - even though ``categoryId``
    came from a consumer ``input_class`` override, not the generated input.

    No shipped override declares a relation field, so the composite is package-only.
    """

    @classmethod
    def _hide_private(
        _cls: type[DjangoType],
        queryset: QuerySet[product_models.Category],
        _info: strawberry.Info,
    ) -> QuerySet[product_models.Category]:
        return queryset.filter(is_private=False)

    @strawberry.input
    class GidItemInput:
        category_id: relay.GlobalID = strawberry.field(description="custom category ref")

    schema, (CategoryT, _ItemT) = _build_item_schema(
        category_get_queryset=_hide_private,
        input_cls=GidItemInput,
    )
    hidden = product_models.Category.objects.create(name=_category_name(), is_private=True)
    res = schema.execute_sync(
        _CREATE,
        variable_values={
            "d": {"name": "New", "categoryId": global_id_for(CategoryT, saved_pk(hidden))},
        },
    )
    assert_mutation_field_error(res, "createItem", "categoryId")
    assert product_models.Item.objects.filter(name="New").count() == 0


@pytest.mark.django_db
def test_sync_misuse_async_get_queryset_from_sync_path() -> None:
    """A sync update over a type with an ``async def get_queryset`` raises ``SyncMisuseError``."""

    async def _async_get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[product_models.Item],
        _info: strawberry.Info,
        **_kwargs: object,
    ) -> QuerySet[product_models.Item]:
        return queryset

    ItemT = type(
        "ItemT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Item, "fields": ("id", "name"), "primary": True},
            ),
            "get_queryset": classmethod(_async_get_queryset),
        },
    )

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Category) is CategoryT

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

    finalize_django_types()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="X", category=cat)
    # Drive the sync pipeline directly (the locate path runs get_queryset); the
    # managed-transaction context stands in for the DjangoSchema execution the
    # direct call bypasses.
    with (
        managed_write_transaction("default"),
        transaction.atomic(),
        pytest.raises(SyncMisuseError),
    ):
        resolvers.resolve_mutation_sync(
            UpdateItem,
            info=make_info(),
            data=UNSET,
            id=str(global_id_for(ItemT, saved_pk(item))),
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_mutation_does_not_leak_into_later_read_optimizer_execution() -> None:
    """An async mutation must not corrupt a later read-side optimizer execution.

    The regression pin for the async-ORM cross-test row leak. The cause is leaked
    rows, not ContextVar lifecycle: the async pipeline runs its whole ORM body -
    the ``transaction.atomic()`` write included - inside one
    ``sync_to_async(thread_sensitive=True)`` call, so the ``save()``
    commits on asgiref's executor-thread connection, NOT the main-thread
    connection that the plain ``django_db`` marker wraps in a rollback
    transaction. Under plain ``django_db`` that committed row escapes per-test
    rollback and persists into the NEXT test's database. The read-side optimizer
    suite (``test_extension.py``) then plans a relation whose visibility-narrowed
    child queryset does not match the leaked row's category, and the forward-FK
    resolver re-raises ``RelatedObjectDoesNotExist``. The
    optimizer's per-execution ContextVars are NOT leaked (``on_execute`` resets
    cleanly across the ``sync_to_async`` hop - verified); the corruption is leaked
    ROWS, a test-isolation defect cured by the suite-wide ``transaction=True``
    convention for async-ORM tests.

    This pin reproduces the async-mutation-THEN-read sequence in ONE process and
    is order-independent in BOTH directions:

    * **Canary (catches a prior leaker):** under ``transaction=True`` this test
      reads with a connection that sees committed rows, so an entry guard asserts
      the products tables are empty - if an EARLIER async test reverted to plain
      ``django_db`` and leaked, that committed row is visible here and trips the
      guard, regardless of which leaker ran first.
    * **Self-contained (catches its own regression):** it runs an async create
      then a read-side optimizer execution over a node type whose category target
      carries a user-narrowing ``get_queryset`` (the exact read shape that
      surfaced the leak), asserting the read plans + resolves the relation, sees
      exactly the row it wrote, and round-trips the relation. Flip this test's own
      decorator to plain ``django_db`` and the cross-test leak it documents
      returns.
    """
    # Canary entry guard: under ``transaction=True`` this connection sees any
    # committed-but-unrolled-back rows. A non-empty table here means an earlier
    # async-ORM test escaped its rollback (the row leak) - fail loudly with the
    # offending rows rather than letting the corruption surface downstream.
    leaked_cats = await sync_to_async(
        lambda: list(product_models.Category.objects.values_list("name", flat=True)),
        thread_sensitive=True,
    )()
    leaked_items = await sync_to_async(
        lambda: list(product_models.Item.objects.values_list("name", flat=True)),
        thread_sensitive=True,
    )()
    assert (leaked_cats, leaked_items) == ([], []), (
        f"Row leak: an earlier async-ORM test committed rows that escaped "
        f"per-test rollback (categories={leaked_cats}, items={leaked_items}). "
        f"Async-ORM tests must use @pytest.mark.django_db(transaction=True)."
    )

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[product_models.Category],
            info: strawberry.Info[object, object],
            **kwargs: object,
        ) -> QuerySet[product_models.Category]:
            # Narrow the category by a request-user-derived predicate so a leaked
            # row's category (created under a DIFFERENT name) would NOT match,
            # reproducing the read-side ``RelatedObjectDoesNotExist`` the leak caused.
            user_name = read_attr(read_attr(info.context, "user", None), "name", None)
            if user_name is not None:
                queryset = queryset.filter(name=user_name)
            return queryset

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    def _all_items() -> QuerySet[product_models.Item]:
        return product_models.Item.objects.all()

    # ``from __future__ import annotations`` makes a ``-> list[ItemT]`` string
    # annotation unresolvable from module scope (``ItemT`` is function-local), so
    # set the return annotation to the real ``list[ItemT]`` type object before
    # handing the resolver to ``strawberry.field`` - the read field still types to
    # the list of the local node type without depending on global name lookup.
    _all_items.__annotations__["return"] = list[ItemT]

    @strawberry.type
    class Query:
        # basedpyright: Strawberry types the field from the resolver's run-time return annotation
        # set above; a class annotation would be a string unresolvable from module scope
        all_items = strawberry.field(resolver=_all_items)  # pyright: ignore[reportGeneralTypeIssues]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        mutation=Mutation,
        extensions=[lambda: optimizer],
    )

    user_name = _category_name()
    cat = await product_models.Category.objects.acreate(name=user_name)
    create = (
        "mutation($d: ItemInput!){ createItem(data:$d){ "
        "node{ name category{ name } } errors{ field messages } } }"
    )
    res = await schema.execute(
        create,
        variable_values={
            "d": {"name": "LeakProbe", "categoryId": global_id_for(CategoryT, saved_pk(cat))},
        },
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["createItem"]["node"]["name"] == "LeakProbe"

    # The read-side optimizer execution: the category target's user-narrowing
    # get_queryset means a leaked item (whose category was created under a name
    # that does not match this request's user) would re-raise
    # RelatedObjectDoesNotExist when the optimizer plans the relation. This is the
    # exact read shape the leak corrupted, run as a SYNC execution (the failing
    # ``test_extension.py`` read used ``schema.execute_sync``); it is driven
    # through ``sync_to_async`` so the sync ORM runs off the event loop, the
    # suite's standard async-test idiom for a synchronous ORM read.
    ctx = SimpleNamespace(user=SimpleNamespace(name=user_name))
    read = await sync_to_async(schema.execute_sync, thread_sensitive=True)(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert read.errors is None, read.errors
    # Exactly the one row this test wrote - no phantom leaked rows.
    assert read.data is not None
    names = sorted(
        require_instance(_json_at(row, "name"), str) for row in _json_list(read.data, "allItems")
    )
    assert names == ["LeakProbe"], names
    # The relation round-trips through the optimizer plan (the leak's failure mode
    # is a None relation -> RelatedObjectDoesNotExist; here it resolves).
    assert read.data["allItems"][0]["category"]["name"] == user_name


# ---------------------------------------------------------------------------
# Library Book/Genre M2M: hidden Relay member (GenreType has no hide hook)
# ---------------------------------------------------------------------------


def _build_book_schema(
    *,
    genre_get_queryset: object | None = None,
) -> tuple[strawberry.Schema, tuple[type[DjangoType], type[DjangoType], type[DjangoType]]]:
    """Declare Book/Genre/Shelf primaries + a create mutation over the Book M2M."""
    genre_body: dict[str, object] = {
        "Meta": type(
            "Meta",
            (),
            {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
        ),
    }
    if genre_get_queryset is not None:
        genre_body["get_queryset"] = genre_get_queryset
    GenreT = type("GenreT", (DjangoType, relay.Node), genre_body)

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


def _make_branch_shelf() -> library_models.Shelf:
    branch = library_models.Branch.objects.create(name="Main")
    return library_models.Shelf.objects.create(code="S1", branch=branch)


_CREATE_BOOK = (
    "mutation($d: BookGenresShelfTitleInput!){ createBook(data:$d){ "
    "node{ id title } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_m2m_hidden_related_id_is_field_error() -> None:
    """An M2M id for a row the related type hides -> ``FieldError`` on the M2M field.

    Live ``createBookViaCustomInput`` covers visible Genre GlobalIDs. Shipped
    ``GenreType`` has no ``get_queryset``; adding one (even flag-gated) would
    change every genre read. A second primary ``Genre`` type cannot coexist with
    the shipped type in the live process, so the hide arm stays on a throwaway
    schema. Hidden indistinguishable from missing; no book is written.
    """

    @classmethod
    def _hide_secret(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Genre],
        _info: strawberry.Info,
    ) -> QuerySet[library_models.Genre]:
        return queryset.exclude(name="Secret")

    schema, (GenreT, ShelfT, _BookT) = _build_book_schema(genre_get_queryset=_hide_secret)
    shelf = _make_branch_shelf()
    visible = library_models.Genre.objects.create(name="Sci-Fi")
    hidden = library_models.Genre.objects.create(name="Secret")
    res = schema.execute_sync(
        _CREATE_BOOK,
        variable_values={
            "d": {
                "title": "Dune",
                "shelfId": global_id_for(ShelfT, saved_pk(shelf)),
                "genres": [
                    global_id_for(GenreT, saved_pk(visible)),
                    global_id_for(GenreT, saved_pk(hidden)),
                ],
            },
        },
    )
    assert_mutation_field_error(res, "createBook", "genres")
    assert not library_models.Book.objects.filter(title="Dune").exists()


_M2M_REFUSAL_DISPATCH_UID = "tests.mutations.m2m_save_time_refusal"


def _refuse_genre_assignment(action: str, **_kwargs: object) -> None:
    """An ``m2m_changed`` receiver refusing every genre assignment once it is made."""
    if action == "post_add":
        raise DjangoValidationError(
            {
                "genres": DjangoValidationError("Genres are frozen.", code="frozen"),
                "shelf_id": "Shelf rejected with the genres.",
            },
        )


@contextlib.contextmanager
def _genre_assignment_refused() -> Generator[None, None, None]:
    """Connect ``_refuse_genre_assignment`` to ``Book.genres``' through model inside the block."""
    through = library_models.Book.genres.through
    m2m_changed.connect(
        _refuse_genre_assignment,
        sender=through,
        weak=False,
        dispatch_uid=_M2M_REFUSAL_DISPATCH_UID,
    )
    try:
        yield
    finally:
        _ = m2m_changed.disconnect(sender=through, dispatch_uid=_M2M_REFUSAL_DISPATCH_UID)


def _build_update_book_schema() -> tuple[
    strawberry.Schema,
    tuple[type[DjangoType], type[DjangoType], type[DjangoType]],
]:
    """Declare Book/Genre/Shelf primaries + an update mutation over the Book M2M."""

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class UpdateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "update"
            fields = ("title", "shelf", "genres")
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


#: The envelope the refusing receiver produces, keyed through the model key map:
#: ``genres`` stays ``genres`` and the forward key's column ``shelf_id`` reports as
#: ``shelfId``.
_M2M_REFUSAL_ERRORS = [
    {
        "field": "genres",
        "messages": ["Genres are frozen."],
        "codes": ["frozen"],
        "path": ["genres"],
    },
    {
        "field": "shelfId",
        "messages": ["Shelf rejected with the genres."],
        "codes": [],
        "path": ["shelfId"],
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_m2m_assignment_validation_error_is_the_model_keyed_envelope(operation: str) -> None:
    """A ``ValidationError`` from an ``m2m_changed`` receiver is the envelope, nothing written.

    The M2M ``.set(...)`` runs after the row's ``save()`` inside the write window, so a
    receiver refusing the assignment raises after the ``Book`` row and its new through
    rows were written. The model flavor maps it through the same key map as
    ``full_clean()``, returns a null object, and rolls everything back: a create leaves
    no book and no through row, an update leaves the stored title and genres as they
    were.
    """
    shelf = _make_branch_shelf()
    stored = library_models.Genre.objects.create(name="Stored")
    frozen = library_models.Genre.objects.create(name="Frozen")
    if operation == "create":
        schema, (GenreT, ShelfT, _BookT) = _build_book_schema()
        query = (
            "mutation($d: BookGenresShelfTitleInput!){ createBook(data:$d){ "
            "node{ id } errors{ field messages codes path } } }"
        )
        variables: dict[str, object] = {
            "d": {
                "title": "Refused",
                "shelfId": global_id_for(ShelfT, saved_pk(shelf)),
                "genres": [global_id_for(GenreT, saved_pk(frozen))],
            },
        }
        book = None
    else:
        schema, (GenreT, _ShelfT, BookT) = _build_update_book_schema()
        book = library_models.Book.objects.create(title="Kept", shelf=shelf)
        book.genres.set([stored])
        query = (
            "mutation($id: ID!, $d: BookGenresShelfTitlePartialInput!){ "
            "updateBook(id:$id, data:$d){ node{ id } errors{ field messages codes path } } }"
        )
        variables = {
            "id": global_id_for(BookT, saved_pk(book)),
            "d": {"title": "Refused", "genres": [global_id_for(GenreT, saved_pk(frozen))]},
        }
    with _genre_assignment_refused():
        res = schema.execute_sync(query, variable_values=variables)
    assert res.errors is None, res.errors
    assert res.data == {
        f"{operation}Book": {"node": None, "errors": _M2M_REFUSAL_ERRORS},
    }
    assert not library_models.Book.objects.filter(title="Refused").exists()
    through_pairs = set(
        library_models.Book.genres.through.objects.values_list("book_id", "genre_id"),
    )
    if book is None:
        assert through_pairs == set()
    else:
        book.refresh_from_db()
        assert book.title == "Kept"
        assert through_pairs == {(saved_pk(book), saved_pk(stored))}


_ITEM_SAVE_REFUSAL_DISPATCH_UID = "tests.mutations.item_save_time_refusal"


@contextlib.contextmanager
def _item_save_refused(error_key: str) -> Generator[None, None, None]:
    """Refuse every ``Item`` save inside the block with a Django error keyed ``error_key``."""

    def _refuse(**_kwargs: object) -> None:
        raise DjangoValidationError(
            {error_key: DjangoValidationError("Refused at save.", code="refused")},
        )

    pre_save.connect(
        _refuse,
        sender=product_models.Item,
        weak=False,
        dispatch_uid=_ITEM_SAVE_REFUSAL_DISPATCH_UID,
    )
    try:
        yield
    finally:
        _ = pre_save.disconnect(
            sender=product_models.Item,
            dispatch_uid=_ITEM_SAVE_REFUSAL_DISPATCH_UID,
        )


@strawberry.input
class _RenamedItemName:
    """A ``Meta.input_class`` override exposing ``Item.name`` as ``itemName``."""

    name: str = strawberry.field(name="itemName")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("error_key", "field", "path"),
    [
        pytest.param("name", "itemName", ["itemName"], id="renamed-input"),
        pytest.param("category", "categoryId", ["categoryId"], id="relation-name"),
        pytest.param("category_id", "categoryId", ["categoryId"], id="relation-attname"),
        pytest.param("is_private", "isPrivate", ["isPrivate"], id="multi-word"),
        pytest.param("code", "code", ["code"], id="no-such-model-field"),
        pytest.param(
            "shelves.1.code",
            "shelves.1.code",
            ["shelves", "1", "code"],
            id="dotted-name-verbatim",
        ),
    ],
)
def test_save_time_django_validation_error_reads_its_names_as_model_fields(
    error_key: str,
    field: str,
    path: list[str],
) -> None:
    """A save-time Django error keys each name as a field of the mutation's own model.

    A ``pre_save`` receiver refuses the ``Item`` write with one name. The model
    flavor reads it through ``_model_error_key_map``: the model field ``name`` lands
    on the renamed root input ``itemName``, the relation under both its name and its
    ``attname`` on ``categoryId``, ``is_private`` on ``isPrivate``. ``code``, which
    ``Item`` lacks, keeps its name, and a dotted name is kept verbatim (its ``path``
    split at the dots), never re-keyed. Nothing is written.
    """
    schema, (CategoryT, _ItemT) = _build_item_schema(input_cls=_RenamedItemName)
    category = product_models.Category.objects.create(name=_category_name())
    with _item_save_refused(error_key):
        res = schema.execute_sync(
            "mutation($d: ItemInput!){ createItem(data:$d){ "
            "node{ id } errors{ field messages codes path } } }",
            variable_values={
                "d": {
                    "itemName": "Refused",
                    "categoryId": global_id_for(CategoryT, saved_pk(category)),
                },
            },
        )
    assert res.errors is None, res.errors
    assert res.data == {
        "createItem": {
            "node": None,
            "errors": [
                {
                    "field": field,
                    "messages": ["Refused at save."],
                    "codes": ["refused"],
                    "path": path,
                },
            ],
        },
    }
    assert not product_models.Item.objects.filter(name="Refused").exists()


# ---------------------------------------------------------------------------
# Raw-pk M2M update existence check (no shipped updateShelf)
# ---------------------------------------------------------------------------


def _build_book_raw_m2m_schema() -> tuple[
    strawberry.Schema,
    tuple[type[DjangoType], type[DjangoType], type[DjangoType]],
]:
    """Declare a NON-Relay ``Genre`` primary so ``Book.genres`` is a raw-pk ``list[Int]`` M2M."""
    GenreT = type(
        "GenreT",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
            ),
        },
    )

    class BranchT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

    assert registry.get(library_models.Branch) is BranchT

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code", "branch")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            primary = True

    class UpdateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


@pytest.mark.django_db
def test_update_raw_pk_m2m_nonexistent_id_is_field_error_no_dangling_row() -> None:
    """A nonexistent raw-pk M2M id on update -> ``FieldError`` on the M2M field, set unchanged.

    Live ``createShelf`` covers the create arm
    (``test_library_api.py::test_create_shelf_model_mutation_nonexistent_alt_branch_is_field_error``).
    Fakeshop ships no ``updateShelf`` / ``updateBook`` with a raw-pk M2M, so the
    update arm stays on a throwaway non-Relay ``Genre`` primary.
    """
    schema, (_GenreT, _ShelfT, BookT) = _build_book_raw_m2m_schema()
    shelf = _make_branch_shelf()
    book = library_models.Book.objects.create(title="Seeded", shelf=shelf)
    existing = library_models.Genre.objects.create(name="Sci-Fi")
    book.genres.set([existing])
    res = schema.execute_sync(
        "mutation($id: ID!, $d: BookPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ id } errors{ field messages } } }",
        variable_values={"id": global_id_for(BookT, saved_pk(book)), "d": {"genres": [88888]}},
    )
    assert_mutation_field_error(res, "updateBook", "genres")
    # The pre-existing M2M set is untouched (the failed write rolled back).
    assert set(book.genres.values_list("pk", flat=True)) == {saved_pk(existing)}


@pytest.mark.django_db
def test_raw_pk_m2m_existence_check_coerces_out_of_range_pk_no_overflow() -> None:
    """An out-of-range raw-pk M2M id is treated as not-found, never a raw ``OverflowError``.

    ``decode_visible_relation_ids`` type-checks each id through the target pk
    field before any ``pk__in`` query. The default ``AutoField`` / ``BigAutoField``
    pk maps to a 32-bit ``Int`` input (so graphql-core caps it), but a target with
    an explicit ``BigIntegerField`` / ``PositiveBigIntegerField`` primary key maps
    to the arbitrary-precision ``BigInt`` input - a pk past SQLite's signed 64-bit
    range would overflow the parameter binding. Coercing first makes an
    out-of-range pk the same field-keyed ``FieldError`` a nonexistent pk yields.
    """
    m2m_field = library_models.Book._meta.get_field("genres")
    related_model = m2m_field.related_model
    assert related_model is not None
    _pks, error = resolvers._decode_relation_id_list(
        [9223372036854775808],
        graphql_name="genres",
        related_model=related_model,
        info=unread_info(),
        relation_field=m2m_field,
    )
    assert error is not None
    assert error.field == "genres"


# ---------------------------------------------------------------------------
# FK explicit-null decode (required-null is live on updateItem.categoryId)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_single_fk_explicit_null_on_nullable_clears_not_relation_error() -> None:
    """An explicit ``null`` on a nullable FK clears (``None``), never a relation error.

    Required-FK ``null`` is live
    (``test_products_api.py::test_update_item_explicit_null_category_id_is_field_error``).
    Fakeshop write surfaces have no ``null=True`` FK, so the clear-signal branch
    is a helper pin with ``category.null`` patched True.
    """
    _build_item_schema()
    # Item.attachment is a nullable FileField, not an FK. Use Category.is_private's
    # sibling: monkeypatch a nullable FK field object that mirrors a real relation.
    fk_field = product_models.Item._meta.get_field("category")
    related_model = fk_field.related_model
    assert related_model is not None
    # Temporarily treat the relation as nullable for the clear-signal branch.
    with mock.patch.object(fk_field, "null", new=True):
        pk, error = resolvers._decode_single_relation_id(
            None,
            graphql_name="categoryId",
            related_model=related_model,
            info=unread_info(),
            relation_field=fk_field,
        )
    assert error is None
    assert pk is None


@pytest.mark.django_db
def test_raw_pk_relations_with_no_registered_primary_use_default_manager_existence() -> None:
    """An unregistered raw-pk relation has existence validation but no visibility contract.

    Only ``Book`` is registered: the generated ``shelfId`` FK and ``genres`` M2M
    inputs therefore carry raw primary keys with no target ``get_queryset`` policy.
    Existing target rows remain attachable through the default manager, while a
    missing member of either relation fails in-band before validation / write.
    """

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    assert registry.get(library_models.Book) is BookT

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    schema = _schema(Mutation)
    shelf = _make_branch_shelf()
    genre = library_models.Genre.objects.create(name="Real")
    query = (
        "mutation($d: BookInput!){ createBook(data:$d){ "
        "node{ id title } errors{ field messages } } }"
    )

    valid = schema.execute_sync(
        query,
        variable_values={
            "d": {"title": "Valid", "shelfId": saved_pk(shelf), "genres": [saved_pk(genre)]},
        },
    )
    assert valid.errors is None, valid.errors
    assert valid.data is not None
    assert valid.data["createBook"]["errors"] == []
    book = library_models.Book.objects.get(title="Valid")
    assert book.shelf_id == saved_pk(shelf)
    assert set(book.genres.values_list("pk", flat=True)) == {saved_pk(genre)}

    invalid_cases = (
        (
            "Missing shelf",
            {"shelfId": saved_pk(shelf) + 9999, "genres": [saved_pk(genre)]},
            "shelfId",
        ),
        (
            "Missing genre",
            {"shelfId": saved_pk(shelf), "genres": [saved_pk(genre) + 9999]},
            "genres",
        ),
    )
    for title, relations, error_field in invalid_cases:
        result = schema.execute_sync(
            query,
            variable_values={"d": {"title": title, **relations}},
        )
        assert_mutation_field_error(result, "createBook", error_field)
        assert not library_models.Book.objects.filter(title=title).exists()


# ---------------------------------------------------------------------------
# Create-validation parity with Model.objects.create over empty-value defaults,
# plus naive-datetime tz-coercion.
#
# ``ScalarSpecimen`` (scalars app) has ``payload = JSONField(default=dict)``
# (``blank=False``) and ``occurred_at = DateTimeField()``. Neither is reachable
# via a live mutation (the scalars app exposes no write surface), so these are
# package tests over the real model. The mutation is narrowed to the non-BigInt
# scalar columns so the schema builds without the scalar_map config.
# ---------------------------------------------------------------------------

_SPEC_UUID = "12345678-1234-5678-1234-567812345678"


def _build_scalar_specimen_schema() -> tuple[strawberry.Schema, type[DjangoMutation]]:
    """Declare a ScalarSpecimen primary + a create mutation; return (schema, CreateSpec)."""

    class SpecT(DjangoType, relay.Node):
        class Meta:
            model = scalars_models.ScalarSpecimen
            fields = ("id", "label")
            primary = True

    assert registry.get(scalars_models.ScalarSpecimen) is SpecT

    class CreateSpec(DjangoMutation):
        class Meta:
            model = scalars_models.ScalarSpecimen
            operation = "create"
            fields = (
                "label",
                "occurred_on",
                "occurred_at",
                "occurred_time",
                "external_id",
                "payload",
            )
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_spec = DjangoMutationField(CreateSpec)

    finalize_django_types()
    return _schema(Mutation), CreateSpec


@pytest.mark.django_db
def test_create_omitting_empty_value_default_field_succeeds() -> None:
    """Omitting a ``JSONField(default=dict)`` (blank=False) on create succeeds.

    The field is optional in the input (it has a default), so a client may omit it.
    Before the fix, ``full_clean`` validated the model's own empty default (``{}`` is
    in Django's ``empty_values``) and rejected it ("This field cannot be blank") -
    stricter than ``Model.objects.create()``, which applies the default unvalidated.
    Create now excludes unprovided fields from ``full_clean``, so the omission writes
    the default cleanly. No shipped ScalarSpecimen mutation: rung 1 would add one to
    the scalars schema; a live holder cannot declare ``DjangoMutation`` after
    finalize.
    """
    schema, CreateSpec = _build_scalar_specimen_schema()
    assert CreateSpec._input_class is not None
    input_name = CreateSpec._input_class.__name__
    res = schema.execute_sync(
        f"mutation($d: {input_name}!){{ createSpec(data:$d){{ node{{ id }} errors{{ field messages }} }} }}",
        variable_values={
            "d": {
                "label": "spec-omit-payload",
                "occurredOn": "2024-01-01",
                "occurredAt": "2024-01-01T12:00:00+00:00",
                "occurredTime": "12:00:00",
                "externalId": _SPEC_UUID,
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["createSpec"]["errors"] == []
    assert res.data["createSpec"]["node"] is not None
    assert scalars_models.ScalarSpecimen.objects.get(label="spec-omit-payload").payload == {}


@pytest.mark.django_db
def test_create_naive_datetime_input_is_made_timezone_aware() -> None:
    """A naive datetime input is coerced to an aware datetime on create.

    Under ``USE_TZ=True`` a naive datetime would trigger Django's naive-datetime
    ``RuntimeWarning`` at save - which this suite's ``-W error`` config escalates to a
    top-level error. The decode step makes a naive datetime aware (like DRF), so the
    create succeeds warning-free and stores an aware value. (A regression would
    surface as the escalated warning failing this test.) No shipped ScalarSpecimen
    mutation: rung 1 would add one to the scalars schema; a live holder cannot
    declare ``DjangoMutation`` after finalize.
    """
    schema, CreateSpec = _build_scalar_specimen_schema()
    assert CreateSpec._input_class is not None
    input_name = CreateSpec._input_class.__name__
    res = schema.execute_sync(
        f"mutation($d: {input_name}!){{ createSpec(data:$d){{ node{{ id }} errors{{ field messages }} }} }}",
        variable_values={
            "d": {
                "label": "spec-naive-dt",
                "occurredOn": "2024-01-01",
                "occurredAt": "2024-01-01T12:00:00",  # naive: no offset
                "occurredTime": "12:00:00",
                "externalId": _SPEC_UUID,
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["createSpec"]["errors"] == []
    row = scalars_models.ScalarSpecimen.objects.get(label="spec-naive-dt")
    assert timezone.is_aware(row.occurred_at)


@pytest.mark.django_db
def test_create_unencodable_text_nested_in_a_json_value_is_field_error_before_save() -> None:
    """A lone surrogate nested in a ``JSONField`` value is a path-keyed decode error; no row.

    The model flavor runs the same storability walk as a top-level string, so a list
    element inside the ``payload`` object is refused at decode (keyed ``payload.tags.1``)
    instead of being handed to the column's encoder.
    """
    schema, CreateSpec = _build_scalar_specimen_schema()
    assert CreateSpec._input_class is not None
    input_name = CreateSpec._input_class.__name__
    res = schema.execute_sync(
        f"mutation($d: {input_name}!){{ createSpec(data:$d){{ node{{ id }} errors{{ field codes }} }} }}",
        variable_values={
            "d": {
                "label": "spec-surrogate-json",
                "occurredOn": "2024-01-01",
                "occurredAt": "2024-01-01T12:00:00+00:00",
                "occurredTime": "12:00:00",
                "externalId": _SPEC_UUID,
                "payload": {"tags": ["ok", "\ud800"]},
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["createSpec"] == {
        "node": None,
        "errors": [{"field": "payload.tags.1", "codes": ["invalid"]}],
    }
    assert not scalars_models.ScalarSpecimen.objects.filter(label="spec-surrogate-json").exists()


# ---------------------------------------------------------------------------
# Scalar field named ``<x>_id`` regression (spec-036)
#
# ``library.TaggedItem`` has a *scalar* ``object_id`` (a ``PositiveIntegerField``,
# emitted by the input generator) AND a ``GenericForeignKey`` ``content_object``.
# The decode index / provided-name mapping must NOT reverse ``object_id`` to a
# relation field by a blind ``_id`` suffix strip, and must NOT index the
# GFK as a decode-able FK. Both are reasoned from the relation field index,
# not a string heuristic.
# ---------------------------------------------------------------------------


def _build_tagged_item_schema() -> tuple[strawberry.Schema, type[DjangoType]]:
    """Declare a TaggedItem primary + an update mutation; return (schema, TaggedItemT)."""

    class TaggedItemT(DjangoType, relay.Node):
        class Meta:
            model = library_models.TaggedItem
            fields = ("id", "tag", "object_id")
            primary = True

    class UpdateTaggedItem(DjangoMutation):
        class Meta:
            model = library_models.TaggedItem
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_tagged_item = DjangoMutationField(UpdateTaggedItem)

    finalize_django_types()
    return _schema(Mutation), TaggedItemT


@pytest.mark.django_db
def test_partial_update_validates_scalar_field_named_id_suffix() -> None:
    """A scalar field literally named ``<x>_id`` IS validated on partial update (spec-036).

    ``TaggedItem.object_id`` is a scalar ``PositiveIntegerField``. A partial update
    providing an invalid value (``-5``) must surface as a ``FieldError`` from
    ``full_clean`` keyed to the ``objectId`` input the client sent - NOT skipped from validation (which the
    old ``_id`` suffix-strip caused: ``object_id`` was mangled to ``object``, read
    as unprovided, excluded from ``full_clean``, and the invalid value slipped to
    the DB as a mis-labeled ``IntegrityError`` / ``"__all__"`` envelope). No
    shipped ``TaggedItemType``: rung 1 would add one to the library schema; a live
    holder cannot declare ``DjangoMutation`` after finalize.
    """
    schema, TaggedItemT = _build_tagged_item_schema()
    ct = ContentType.objects.get_for_model(library_models.Branch)
    branch = library_models.Branch.objects.create(name="RegressionBranch")
    tagged = library_models.TaggedItem.objects.create(
        tag="alpha",
        content_type=ct,
        object_id=saved_pk(branch),
    )
    update_q = (
        "mutation($id: ID!, $d: TaggedItemPartialInput!){ "
        "updateTaggedItem(id:$id, data:$d){ "
        "node{ tag } errors{ field messages } } }"
    )
    res = schema.execute_sync(
        update_q,
        variable_values={
            "id": global_id_for(TaggedItemT, saved_pk(tagged)),
            "d": {"objectId": -5},
        },
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    payload = _json_object(res.data, "updateTaggedItem")
    # The invalid scalar surfaces as a FieldError keyed to the ``objectId`` input -
    # NOT a swallowed write, NOT a mis-labeled ``"__all__"`` uniqueness envelope.
    assert payload["node"] is None
    fields = [_json_at(error, "field") for error in _json_list(payload, "errors")]
    assert "objectId" in fields, payload["errors"]
    assert NON_FIELD_ERROR_KEY not in fields, payload["errors"]
    # The invalid value never reached the DB.
    tagged.refresh_from_db()
    assert tagged.object_id == saved_pk(branch)


def test_provided_attr_names_keeps_scalar_id_suffix_field() -> None:
    """``_provided_attr_names`` keeps a scalar ``<x>_id`` field under its real name (spec-036).

    The FK reversal is index-driven: ``content_type_id`` (a real FK attr) maps to
    ``content_type``, while ``object_id`` (a scalar) stays ``object_id`` - never
    mangled to ``object``.
    """

    @strawberry.input
    class Probe:
        object_id: int
        tag: str
        content_type_id: int

    assert has_object_definition(Probe)
    _specs, model_fields = mutation_input_field_specs(library_models.TaggedItem, Probe)
    provided = resolvers._provided_attr_names(
        model_fields,
        {"object_id": 5, "tag": "x", "content_type_id": 1},
        [],
    )
    assert provided == {"object_id", "tag", "content_type"}


def test_relation_field_index_excludes_generic_foreign_key() -> None:
    """``_relation_field_index`` does not index a ``GenericForeignKey`` as a FK (spec-036).

    A GFK reports ``is_relation=True`` but ``column=None`` / ``related_model=None``,
    so it must never enter ``fk_by_attr`` (where ``decode_visible_relation_ids``
    would later compare a decoded model against ``related_model=None``). The real
    ``content_type`` FK is still indexed.
    """
    fk_by_attr, _m2m_by_name = _relation_field_index(library_models.TaggedItem)
    assert "content_object_id" not in fk_by_attr
    assert "content_type_id" in fk_by_attr


def test_explicit_null_error_allows_null_on_nullable_column() -> None:
    """``_explicit_null_error`` yields no error for ``null`` on a ``null=True`` column.

    The complement of the live
    ``test_uploads_api.py::test_update_explicit_null_on_the_required_file_is_a_field_error_over_http``
    row: an explicit ``None`` on a nullable scalar column is a valid clear, so the guard
    returns ``None`` (no ``FieldError``). ``NullableScalarSpecimen.score`` is
    ``null=True``. No live products mutation exposes a nullable scalar column, so this
    branch is earned against a real nullable example model rather than a live query.
    """
    assert (
        resolvers._explicit_null_error(
            scalars_models.NullableScalarSpecimen._meta.get_field("score"),
            "score",
            None,
        )
        is None
    )


def test_validation_error_to_field_errors_non_dict_uses_all_key() -> None:
    """A non-dict ``ValidationError`` (``.messages``, no ``.error_dict``) maps under the sentinel.

    ``full_clean()`` always raises with an ``error_dict`` (the keyed path), so this
    ``.messages`` fallback serves a bare ``ValidationError`` - the shape the ``0.0.12``
    form / ``0.0.13`` serializer flavors and a model ``clean()`` raising a plain
    message produce. It is the documented single-source mapper, exercised directly as
    it is unreachable through the current ``full_clean`` path.
    """
    errors = validation_error_to_field_errors(ValidationError("a plain message"))
    assert [(error.field, error.messages) for error in errors] == [
        (NON_FIELD_ERROR_KEY, ["a plain message"]),
    ]


# ---------------------------------------------------------------------------
# Structured error codes + paths on the Django flat mapper (spec-039)
# ---------------------------------------------------------------------------


def test_validation_error_to_field_errors_preserves_django_codes_and_path() -> None:
    """A Django ``ValidationError``'s ``.code``s -> ``codes``; field name -> ``path``."""
    exc = DjangoValidationError(
        {"name": [DjangoValidationError("This field is required.", code="required")]},
    )
    (fe,) = validation_error_to_field_errors(exc)
    assert fe.field == "name"
    assert fe.codes == ["required"]
    assert fe.path == ["name"]


def test_validation_error_to_field_errors_non_dict_root_has_empty_path() -> None:
    """A non-dict (model-wide) Django ``ValidationError`` keys ``"__all__"`` with an EMPTY path (#13)."""
    (fe,) = validation_error_to_field_errors(
        DjangoValidationError("Whole-object problem.", code="invalid"),
    )
    assert fe.field == NON_FIELD_ERROR_KEY
    assert fe.path == []
    assert fe.codes == ["invalid"]


# ---------------------------------------------------------------------------
# Row locking on the update/delete locate (spec-039, expanded in 0.0.14)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_locate_instance_locks_through_base_manager_subquery_by_default() -> None:
    """The default locate acquires a visibility-constrained base-manager row lock.

    The lock query must NOT be the consumer's visibility queryset with
    ``.select_for_update()`` attached (joins / unions / annotations cannot legally
    carry ``FOR UPDATE``); it is the model's base manager filtered by
    ``pk__in=<visible pks>``. The located row still respects visibility (a row
    outside the subquery is not found).
    """
    _schema_and_types = _build_item_schema()
    ItemT = _schema_and_types[1][1]
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Lockable", category=cat)

    with transaction.atomic():
        located = mutation_resolvers.locate_instance(
            ItemT,
            saved_pk(item),
            unread_info(),
            alias="default",
        )
    assert located is not None
    assert saved_pk(located) == saved_pk(item)
    # The locked read comes from the BASE manager (a plain Item row), and the
    # visibility subquery still gates it: a missing pk is None, not an error.
    with transaction.atomic():
        assert (
            mutation_resolvers.locate_instance(
                ItemT,
                saved_pk(item) + 999,
                unread_info(),
                alias="default",
            )
            is None
        )


_T = TypeVar("_T")


def _noop(*_args: object, **_kwargs: object) -> None:
    """A patched seam that accepts any call and does nothing."""


def _returning(value: _T) -> Callable[..., _T]:
    """A patched seam that accepts any call and answers ``value`` (the same object each call)."""

    def stub(*_args: object, **_kwargs: object) -> _T:
        return value

    return stub


def _fresh_mock(*_args: object, **_kwargs: object) -> mock.MagicMock:
    """A patched seam that accepts any call and answers a NEW ``MagicMock`` each call."""
    return mock.MagicMock()


def _identity(value: object) -> object:
    return value


def _decode_marker(_instance: Model | None) -> tuple[str]:
    return ("decoded",)


def _write_located(instance: Model | None, _decoded: object) -> Model | None:
    return instance


def test_locate_instance_opt_out_skips_the_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """``select_for_update=False`` locates through the (pinned) visibility queryset, unlocked."""
    sentinel = object()
    get = MagicMock(return_value=sentinel)
    select_for_update = MagicMock()
    pinned_qs = MagicMock(name="pinned_qs", get=get, select_for_update=select_for_update)
    using = MagicMock(return_value=pinned_qs)
    visible_qs = MagicMock(name="visible_qs", using=using)
    visible_qs._db = None

    monkeypatch.setattr(mutation_resolvers, "model_for", _fresh_mock)
    monkeypatch.setattr(mutation_resolvers, "initial_queryset", _noop)
    monkeypatch.setattr(mutation_resolvers, "apply_type_visibility_sync", _returning(visible_qs))

    result = mutation_resolvers.locate_instance(
        DjangoType,
        7,
        unread_info(),
        alias="default",
        select_for_update=False,
    )
    assert result is sentinel
    using.assert_called_once_with("default")
    select_for_update.assert_not_called()
    get.assert_called_once_with(pk=7)


# ---------------------------------------------------------------------------
# Multi-db atomic boundary (the managed write alias)
# ---------------------------------------------------------------------------


def test_write_pipeline_opens_atomic_on_managed_write_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``run_write_pipeline_sync`` opens ``transaction.atomic(using=<managed alias>)``.

    The alias is resolved ONCE (by the ``DjangoSchema`` execution context, from
    ``router.db_for_write``) and published through the managed-transaction
    context; the pipeline's own atomic block - and its rollback - must ride the
    SAME alias, or a multi-db router write commits on the routed alias while
    the rollback stays on ``default``.
    """

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    del ItemType

    # No permission classes: this test is about the managed-alias atomic, not auth,
    # so the authorization phase (and its rolled-back auth-alias barrier) is a no-op.
    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = []

    finalize_django_types()

    captured: dict[str, object] = {}

    class _Atomic:
        def __init__(self, using: str | None = None) -> None:
            captured["using"] = using

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

    def _refetched(*_args: object, **_kwargs: object) -> MagicMock:
        return MagicMock(pk=1)

    monkeypatch.setattr(mutation_resolvers, "model_for", _fresh_mock)
    monkeypatch.setattr(mutation_resolvers, "payload_object_slot", _returning("node"))
    monkeypatch.setattr(mutation_resolvers, "payload_cls_for", _fresh_mock)
    monkeypatch.setattr(mutation_resolvers, "authorize_or_raise", _noop)
    monkeypatch.setattr(mutation_resolvers, "refetch_optimized", _refetched)
    monkeypatch.setattr(mutation_resolvers, "build_payload", _returning("ok"))

    with (
        patch.object(transaction, "atomic", side_effect=_Atomic),
        managed_write_transaction("shard_b"),
    ):
        result = mutation_resolvers.run_write_pipeline_sync(
            CreateItem,
            info=make_info(),
            data=None,
            id_=None,
            decode_step=lambda _instance: ("decoded",),
            write_step=lambda _instance, _decoded: MagicMock(pk=7),
        )

    assert result == "ok"
    assert captured["using"] == "shard_b"


def _pipeline_harness(
    monkeypatch: pytest.MonkeyPatch,
    *,
    operation: str = "update",
    authorize: Callable[..., object] | None = None,
) -> mock.MagicMock:
    """Scaffold ``run_write_pipeline_sync`` with mocked locate/authorize/refetch (snapshot tests)."""
    mutation_cls = MagicMock(
        **{"_mutation_meta.operation": operation, "_mutation_meta.select_for_update": False},
    )
    mutation_cls.__name__ = "SnapshotMutation"
    mutation_cls._primary_type = object()

    # A REAL identity ``to_python``: the canonical pk comparison must not be fed a
    # MagicMock whose repeated calls return one shared (always-equal) child mock.
    fake_model = MagicMock(__name__="Row", **{"_meta.pk.to_python": _identity})
    monkeypatch.setattr(mutation_resolvers, "model_for", _returning(fake_model))
    monkeypatch.setattr(mutation_resolvers, "payload_object_slot", _returning("node"))
    monkeypatch.setattr(mutation_resolvers, "payload_cls_for", _fresh_mock)
    # ``**_kwargs`` absorbs the pinned ``using=`` alias the pipeline threads to the
    # real decode; this harness asserts drift handling, not alias propagation
    # (``test_custom_node_id_real_pk_lookup_uses_pinned_alias`` owns that).
    monkeypatch.setattr(mutation_resolvers, "coerce_lookup_id", _returning((7, None)))
    monkeypatch.setattr(mutation_resolvers, "check_instance_write_alias", _noop)
    monkeypatch.setattr(
        mutation_resolvers,
        "authorize_or_raise",
        authorize if authorize is not None else _noop,
    )
    monkeypatch.setattr(mutation_resolvers, "refetch_optimized", _fresh_mock)
    monkeypatch.setattr(mutation_resolvers, "build_payload", _returning("ok"))
    return mutation_cls


def test_pipeline_snapshots_authorized_pk_before_permission_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The authorized pk is captured BEFORE the permission hook can touch the mutable instance.

    A malicious ``check_permission`` re-pointing ``instance.pk`` at a hidden row must not
    poison the snapshot the saved-result validation compares against: the write step
    returning the (mutated) instance fails the flavor-independent backstop.
    """
    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args: object, **_kwargs: object) -> None:
        located.pk = 999  # re-point at a hidden row AFTER authorization

    mutation_cls = _pipeline_harness(monkeypatch, authorize=evil_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError, match="must write the row that was authorized"),
    ):
        object_result(
            mutation_resolvers.run_write_pipeline_sync,
            mutation_cls,
            info=None,
            data=None,
            id_="ignored",
            decode_step=_decode_marker,
            write_step=_write_located,
        )


def test_pipeline_rejects_pk_drift_during_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An update permission hook re-pointing ``instance.pk`` fails closed with the drift error."""
    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def drifting_authorize(*_args: object, **_kwargs: object) -> None:
        located.pk = 8

    mutation_cls = _pipeline_harness(monkeypatch, authorize=drifting_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError) as exc,
    ):
        object_result(
            mutation_resolvers.run_write_pipeline_sync,
            mutation_cls,
            info=None,
            data=None,
            id_="ignored",
            decode_step=_decode_marker,
            write_step=_write_located,
        )
    assert str(exc.value) == (
        f"{truth.name(mutation_cls)}: the located instance's pk changed from 7 to 8 during "
        "authorization; an update must write the row that was authorized, never a "
        "substituted one."
    )


def test_pipeline_pk_drift_hostile_repr_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pk forged by a hook renders through its own ``__repr__``; what that raises propagates.

    The drift is still refused before the write; the diagnostic names the forged pk
    through ``truth.render``, so the forged object's own exception surfaces in place of
    the ``ConfigurationError``.
    """

    class _HostilePk:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("hostile pk repr")

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args: object, **_kwargs: object) -> None:
        located.pk = _HostilePk()

    mutation_cls = _pipeline_harness(monkeypatch, authorize=evil_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(RuntimeError, match="hostile pk repr"),
    ):
        object_result(
            mutation_resolvers.run_write_pipeline_sync,
            mutation_cls,
            info=None,
            data=None,
            id_="ignored",
            decode_step=_decode_marker,
            write_step=_write_located,
        )


def test_pipeline_publishes_authorized_pk_on_write_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The post-locate snapshot is published on the write-pipeline context for the flavors."""
    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )
    seen: dict[str, object] = {}

    def probe_authorize(*_args: object, **_kwargs: object) -> None:
        seen["authorized_pk"] = require_write_pipeline().authorized_pk

    mutation_cls = _pipeline_harness(monkeypatch, authorize=probe_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
    ):
        result = object_result(
            mutation_resolvers.run_write_pipeline_sync,
            mutation_cls,
            info=None,
            data=None,
            id_="ignored",
            decode_step=_decode_marker,
            write_step=_write_located,
        )
    assert result == "ok"
    assert seen["authorized_pk"] == 7


def test_delete_pipeline_rejects_pk_drift_during_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A delete permission hook re-pointing ``instance.pk`` fails closed before any delete."""
    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args: object, **_kwargs: object) -> None:
        located.pk = 999  # re-point at a hidden row AFTER authorization

    mutation_cls = _pipeline_harness(
        monkeypatch,
        operation="delete",
        authorize=evil_authorize,
    )
    mutation_cls.configure_mock(**{"_mutation_meta.permission_classes": []})
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError, match="pk changed"),
    ):
        object_result(mutation_resolvers._run_delete, mutation_cls, info=None, id_="ignored")


def test_delete_pipeline_pk_drift_hostile_repr_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A delete-path pk forged by a hook renders through its own ``__repr__``; it propagates.

    The drift is still refused before any delete; the diagnostic names the forged pk
    through ``truth.render``, so the forged object's own exception surfaces in place of
    the ``ConfigurationError``.
    """

    class _HostilePk:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("hostile pk repr")

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args: object, **_kwargs: object) -> None:
        located.pk = _HostilePk()

    mutation_cls = _pipeline_harness(
        monkeypatch,
        operation="delete",
        authorize=evil_authorize,
    )
    mutation_cls.configure_mock(**{"_mutation_meta.permission_classes": []})
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(RuntimeError, match="hostile pk repr"),
    ):
        object_result(mutation_resolvers._run_delete, mutation_cls, info=None, id_="ignored")


def test_delete_pipeline_rides_shared_write_skeleton(monkeypatch: pytest.MonkeyPatch) -> None:
    """Delete supplies a snapshot ``tail_step``; locate/auth/atomic live in the skeleton."""
    seen: dict[str, object] = {}

    def fake_pipeline(
        _mutation_cls: object,
        _info: object,
        data: object,
        id_: object,
        *,
        decode_step: object,
        write_step: object,
        tail_step: object = None,
    ) -> str:
        del decode_step, write_step  # the delete resolver passes the pipeline steps by keyword
        seen["data"] = data
        seen["id"] = id_
        seen["tail_step"] = tail_step
        return "ridden"

    monkeypatch.setattr(mutation_resolvers, "run_write_pipeline_sync", fake_pipeline)
    monkeypatch.setattr(mutation_resolvers, "payload_cls_for", _returning(object))
    monkeypatch.setattr(mutation_resolvers, "payload_object_slot", _returning("node"))

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    finalize_django_types()
    assert DeleteItem._primary_type is ItemType
    result = mutation_resolvers._run_delete(DeleteItem, info=unread_info(), id_="gid")
    assert result == "ridden"
    assert seen["data"] is None
    assert seen["id"] == "gid"
    assert callable(seen["tail_step"])


def test_write_flavors_share_resolver_entry_factory() -> None:
    """Model, form, and serializer sync entries all come from ``make_resolver_entries``."""
    assert inspect.isfunction(resolvers.resolve_mutation_sync)
    assert inspect.isfunction(resolve_form_sync)
    assert inspect.isfunction(resolve_serializer_sync)
    assert resolvers.resolve_mutation_sync.__name__ == "resolve_sync"
    assert resolve_form_sync.__name__ == "resolve_sync"
    assert resolve_serializer_sync.__name__ == "resolve_sync"


@pytest.mark.django_db
def test_assign_m2m_integrity_error_contained_in_envelope() -> None:
    """IntegrityError during M2M assignment is returned as the constraint FieldError envelope."""

    class CategoryType(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")

    assert registry.get(product_models.Category) is CategoryType

    class CreateCategoryMutation(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "create"
            permission_classes = [_AllowAll]

    finalize_django_types()
    cat = product_models.Category(name=_category_name())

    with patch(
        "django_strawberry_framework.mutations.resolvers._assign_m2m",
        side_effect=IntegrityError("constraint failed"),
    ):
        decoded: _ModelDecoded = (cat, [("fake_m2m", [1, 2])], [])
        with managed_write_transaction("default"), open_write_pipeline(CreateCategoryMutation):
            failure = resolvers._model_write_step(CreateCategoryMutation, None, decoded)
        assert isinstance(failure, resolvers.StepFailure)
        errors = failure.errors
        assert len(errors) == 1
        assert errors[0].field == NON_FIELD_ERROR_KEY
        assert errors[0].codes == ["constraint"]


@pytest.mark.django_db
def test_model_write_step_full_clean_error_keys_to_wire_name() -> None:
    """A ``full_clean`` failure on a multi-word column reports the GraphQL wire name.

    The write step re-keys the Django field buckets through the bind-stashed
    specs: ``Book.circulation_status`` (whose input is the enum-guarded
    ``circulationStatus``, so no live request can fail its ``full_clean``) surfaces
    as ``circulationStatus`` - the wire-name contract the relation-decode errors,
    the serializer flattener, and the committed ``categoryId`` rows already keep.
    The key map itself is pinned too: the FK ``shelf`` and its ``shelf_id`` column
    both ride the ``shelfId`` input.
    """

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("id", "title", "circulation_status")

    del BookType

    class CreateBookMutation(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            permission_classes = [_AllowAll]

    finalize_django_types()
    key_map = resolvers._model_error_key_map(CreateBookMutation)
    assert key_map["shelf"][0] == "shelfId"
    assert key_map["shelf_id"][0] == "shelfId"
    assert key_map["circulation_status"][0] == "circulationStatus"

    branch = library_models.Branch.objects.create(name="WireNameMapBranch")
    shelf = library_models.Shelf.objects.create(code="WM-1", branch=branch)
    book = library_models.Book(
        title="Wire",
        circulation_status="bogus-not-a-choice-value!!",
        shelf=shelf,
    )
    decoded: _ModelDecoded = (book, [], [])
    with managed_write_transaction("default"), open_write_pipeline(CreateBookMutation):
        failure = resolvers._model_write_step(CreateBookMutation, None, decoded)
    assert isinstance(failure, resolvers.StepFailure)
    assert [field_error.field for field_error in failure.errors] == ["circulationStatus"]


@pytest.mark.django_db
def test_delete_integrity_error_contained_in_envelope() -> None:
    """IntegrityError during instance.delete() is returned as the constraint FieldError envelope."""
    cat = product_models.Category.objects.create(name=_category_name())

    with patch.object(
        product_models.Category,
        "delete",
        side_effect=IntegrityError("FK constraint on delete"),
    ):
        errors = resolvers._delete_or_field_errors(cat)
        assert isinstance(errors, list)
        assert len(errors) == 1
        assert errors[0].field == NON_FIELD_ERROR_KEY
        assert errors[0].codes == ["constraint"]


# ---------------------------------------------------------------------------
# A forward ``ForeignObject`` written through its carriers (no fakeshop model has one)
# ---------------------------------------------------------------------------


def _link_model(name: str) -> type[Model]:
    """Return the link fixture model ``tests.optimizer._link_models`` declares as ``name``."""
    model = read_attr(_link_models, name)
    assert isinstance(model, type)
    assert issubclass(model, Model)
    return model


def _build_link_child_schema(
    child_model: type[Model],
) -> tuple[strawberry.Schema, type[DjangoType]]:
    """Primaries over ``LnkParent`` and ``child_model`` + all-fields create / update mutations.

    The child type exposes every field, its generated ``parent`` relation
    included; the mutations name no ``Meta.fields``, so their inputs carry the
    link's carrier columns as scalars and no relation input.
    """
    type(
        "LnkParentT",
        (DjangoType, relay.Node),
        {"Meta": type("Meta", (), {"model": _link_models.LnkParent, "fields": ("id", "label")})},
    )
    child_type = type(
        "LnkChildT",
        (DjangoType, relay.Node),
        {"Meta": type("Meta", (), {"model": child_model, "fields": "__all__"})},
    )
    create = type(
        "CreateChild",
        (DjangoMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": child_model, "operation": "create", "permission_classes": [_AllowAll]},
            ),
        },
    )
    update = type(
        "UpdateChild",
        (DjangoMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": child_model, "operation": "update", "permission_classes": [_AllowAll]},
            ),
        },
    )

    @strawberry.type
    class Mutation:
        create_child = DjangoMutationField(create)
        update_child = DjangoMutationField(update)

    finalize_django_types()
    return _schema(Mutation), child_type


_LINK_CHILD_CARRIER_ROWS: list[
    tuple[str, Callable[[_link_models.LnkParent], dict[str, object]]]
] = [
    ("LnkPairChild", lambda parent: {"pTenant": parent.tenant, "pCode": parent.code}),
    ("LnkColumnChild", lambda parent: {"pId": saved_pk(parent)}),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("child_name", "carriers"),
    _LINK_CHILD_CARRIER_ROWS,
    ids=["two_column_fo", "one_column_fo"],
)
def test_all_fields_mutation_writes_a_foreign_object_through_its_carriers(
    child_name: str,
    carriers: Callable[[_link_models.LnkParent], dict[str, object]],
) -> None:
    """Create and update set the link by writing its carrier columns; ``parent`` reads it back.

    ``pa`` and ``pb`` share ``code="A"``, so the two-column create lands on
    ``pb`` only when both carriers are written; the update moves the row to
    ``pc`` and the payload's generated ``parent`` follows it.
    """
    child_model = _link_model(child_name)
    schema, child_type = _build_link_child_schema(child_model)
    payload = "node { id name parent { label } } errors { field messages }"
    create = f"mutation($d: {child_name}Input!) {{ createChild(data: $d) {{ {payload} }} }}"
    update = (
        f"mutation($id: ID!, $d: {child_name}PartialInput!) "
        f"{{ updateChild(id: $id, data: $d) {{ {payload} }} }}"
    )

    with _link_models.link_fixture_tables(connection):
        parents = {p.label: p for p in _link_models.LnkParent.objects.all()}
        created = schema.execute_sync(
            create,
            variable_values={"d": {"name": "new", **carriers(parents["pb"])}},
        )
        assert created.errors is None, created.errors
        assert created.data is not None
        node = _json_object(created.data, "createChild", "node")
        assert created.data["createChild"]["errors"] == []
        assert (node["name"], node["parent"]) == ("new", {"label": "pb"})
        row = child_model.objects.get(name="new")
        assert node["id"] == global_id_for(child_type, saved_pk(row))

        updated = schema.execute_sync(
            update,
            variable_values={"id": node["id"], "d": carriers(parents["pc"])},
        )
        assert updated.errors is None, updated.errors
        assert updated.data is not None
        assert updated.data["updateChild"]["errors"] == []
        assert updated.data["updateChild"]["node"]["parent"] == {"label": "pc"}
        assert read_attr(child_model.objects.get(pk=saved_pk(row)), "parent") == parents["pc"]


def _build_link_key_schema(
    hidden_label: str,
) -> tuple[strawberry.Schema, type[DjangoType], type[DjangoType], type[DjangoType]]:
    """Relation-input mutations over the ``Lnk*`` links keyed by ``to_field`` columns.

    ``CreateSlugChild`` / ``UpdateSlugChild`` write ``LnkSlugChild.parent`` (a
    ``ForeignKey(to_field="slug")``) through ``parentId``; ``UpdateParentTags`` writes
    ``LnkParent.tags``, whose through row stores the tag's ``code``. The parent
    primary hides the parent labelled ``hidden_label``. Returns the schema and the
    parent, tag and child primaries the ids are minted against.
    """

    class LnkParentT(DjangoType, relay.Node):
        class Meta:
            model = _link_models.LnkParent
            fields = ("id", "label")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[_link_models.LnkParent],
            info: strawberry.Info,
            **kwargs: object,
        ) -> QuerySet[_link_models.LnkParent]:
            return queryset.exclude(label=hidden_label)

    class LnkTagT(DjangoType, relay.Node):
        class Meta:
            model = _link_models.LnkTag
            fields = ("id", "name")

    class LnkSlugChildT(DjangoType, relay.Node):
        class Meta:
            model = _link_models.LnkSlugChild
            fields = ("id", "name", "parent")

    class CreateSlugChild(DjangoMutation):
        class Meta:
            model = _link_models.LnkSlugChild
            operation = "create"
            fields = ("name", "parent")
            permission_classes = [_AllowAll]

    class UpdateSlugChild(DjangoMutation):
        class Meta:
            model = _link_models.LnkSlugChild
            operation = "update"
            fields = ("name", "parent")
            permission_classes = [_AllowAll]

    class UpdateParentTags(DjangoMutation):
        class Meta:
            model = _link_models.LnkParent
            operation = "update"
            fields = ("tags",)
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_slug_child = DjangoMutationField(CreateSlugChild)
        update_slug_child = DjangoMutationField(UpdateSlugChild)
        update_parent_tags = DjangoMutationField(UpdateParentTags)

    finalize_django_types()
    return _schema(Mutation), LnkParentT, LnkTagT, LnkSlugChildT


_SLUG_CHILD_PAYLOAD = "node { name parent { label } } errors { field messages }"
_SLUG_CHILD_RELATION_ERROR = [
    {"field": "parentId", "messages": ["Invalid id for relation 'parentId'."]},
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "operation",
        "target",
        "expected_errors",
        "expected_keys",
    ),
    [
        (
            "create",
            "pa",
            [],
            ["s-a"],
        ),
        (
            "create",
            "pc",
            _SLUG_CHILD_RELATION_ERROR,
            [],
        ),
        (
            "update",
            "pa",
            [],
            ["s-a"],
        ),
        (
            "update",
            "pc",
            _SLUG_CHILD_RELATION_ERROR,
            ["s-b"],
        ),
    ],
    ids=[
        "create_visible",
        "create_hidden",
        "update_visible",
        "update_hidden",
    ],
)
def test_to_field_relation_input_stores_the_key_of_the_visible_row_it_names(
    operation: str,
    target: str,
    expected_errors: list[dict[str, object]],
    expected_keys: list[str],
) -> None:
    """A ``to_field`` FK input names its target by id and stores the target's key column.

    The hidden ``pc``'s ``slug`` is ``pa``'s id, so storing the id ``pa`` is named by
    would link ``pc``: a create and an update (of ``b1``, linked to ``pb``) naming
    ``pa`` store ``pa``'s slug and answer ``pa``, and naming the hidden ``pc`` is the
    uniform relation error that writes nothing (no row created, ``b1`` keeps ``pb``'s
    slug).
    """
    with _link_models.link_fixture_tables(connection):
        parents = {p.label: p for p in _link_models.LnkParent.objects.all()}
        _link_models.LnkParent.objects.filter(pk=saved_pk(parents["pc"])).update(
            slug=str(saved_pk(parents["pa"])),
        )
        schema, parent_type, _tag_type, child_type = _build_link_key_schema(hidden_label="pc")
        parent_id = global_id_for(parent_type, saved_pk(parents[target]))
        if operation == "create":
            name = "new"
            result = schema.execute_sync(
                "mutation($d: LnkSlugChildInput!) "
                f"{{ createSlugChild(data: $d) {{ {_SLUG_CHILD_PAYLOAD} }} }}",
                variable_values={"d": {"name": name, "parentId": parent_id}},
            )
        else:
            name = "b1"
            child = _link_models.LnkSlugChild.objects.get(name=name)
            result = schema.execute_sync(
                "mutation($id: ID!, $d: LnkSlugChildPartialInput!) "
                f"{{ updateSlugChild(id: $id, data: $d) {{ {_SLUG_CHILD_PAYLOAD} }} }}",
                variable_values={
                    "id": global_id_for(child_type, saved_pk(child)),
                    "d": {"parentId": parent_id},
                },
            )
        assert result.errors is None, result.errors
        assert result.data is not None
        answer = _json_object(result.data, f"{operation}SlugChild")
        assert answer["errors"] == expected_errors
        expected_node = (
            {"name": name, "parent": {"label": target}} if not expected_errors else None
        )
        assert answer["node"] == expected_node
        stored = _link_models.LnkSlugChild.objects.filter(name=name).values_list(
            "parent_id",
            flat=True,
        )
        assert list(stored) == expected_keys


@pytest.mark.django_db(transaction=True)
def test_to_field_through_m2m_input_sets_the_key_its_through_rows_store() -> None:
    """An M2M whose through row keys the target by ``to_field`` stores each tag's ``code``.

    ``LnkTagging.tag`` is ``ForeignKey(LnkTag, to_field="code")``; the ``tags`` input
    names tags by id, and the replace-set written is their codes, which ``.set()``
    reads a non-instance member as.
    """
    update = (
        "mutation($id: ID!, $d: LnkParentTagsPartialInput!) "
        "{ updateParentTags(id: $id, data: $d) { node { id } errors { field messages } } }"
    )

    with _link_models.link_fixture_tables(connection):
        schema, parent_type, tag_type, _child_type = _build_link_key_schema(hidden_label="")
        parent = _link_models.LnkParent.objects.get(label="pb")
        tags = {t.name: t for t in _link_models.LnkTag.objects.all()}
        result = schema.execute_sync(
            update,
            variable_values={
                "id": global_id_for(parent_type, saved_pk(parent)),
                "d": {
                    "tags": [
                        global_id_for(tag_type, saved_pk(tags[name])) for name in ("t3", "t2")
                    ],
                },
            },
        )
        assert result.errors is None, result.errors
        assert result.data is not None
        assert result.data["updateParentTags"]["errors"] == []
        stored = _link_models.LnkTagging.objects.filter(parent=parent).values_list(
            "tag_id",
            flat=True,
        )
        assert sorted(stored) == ["c-t2", "c-t3"]
