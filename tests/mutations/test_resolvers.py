"""Write-pipeline resolver tests.

Private checks cover constrained-field exclusion, lookup coercion and pinned
aliases, metadata-based field indexing, row-lock and visibility re-read seams,
exception identity, and transaction lifetime. Direct mutation probes also cover
model inheritance, consumer save/delete hooks and update field sets.

Consumer model mutation identities, relation overrides, M2M visibility and
assignment refusals, raw-pk existence with or without registered targets, error-field
names, nullable foreign-key clears and scalar fields ending in ``_id`` are exercised over HTTP in
``examples/fakeshop/test_query/test_model_mutation_flows_api.py``. A generated column's
absence from every flavor's write input lives in
``examples/fakeshop/test_query/test_library_generated_api.py``; the composite-key update
input in ``examples/fakeshop/test_query/test_mti_composite_relations_api.py``; a
``DoesNotExist`` escaping the write, a soft-delete ``delete()`` and the nullable-column
explicit ``null`` in ``test_products_api.py`` / ``test_library_api.py``.
Other consumer writes live in
``examples/fakeshop/test_query/test_products_api.py``,
``examples/fakeshop/test_query/test_library_api.py`` and
``examples/fakeshop/test_query/test_uploads_api.py``; transaction rollback lives in
``examples/fakeshop/test_query/test_mutation_atomicity.py``. JSON defaults,
naive datetimes and JSON text preflight live in
``examples/fakeshop/test_query/test_scalars_mutation_api.py``. A decimal past PostgreSQL
``numeric``'s format in a column with no ``max_digits``, which fakeshop cannot declare on
the Django floor, is written here through an alias that reads as PostgreSQL. No fakeshop
model has a ``clean()`` rewriting a column or a ``DurationField`` mapped to text, so the
storability rule over the values ``clean_fields()`` and a model ``clean()`` leave is held
here too.
"""

from __future__ import annotations

import contextlib
import datetime
import itertools
import json
import logging
import threading
import time
import zoneinfo
from collections.abc import Callable, Generator, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeAlias, TypeVar
from unittest import mock
from unittest.mock import MagicMock, patch

import django
import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from django import forms
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, OperationalError, connection, models, transaction
from django.db.models import Model, QuerySet
from django.db.models.functions import Lower
from django.db.models.signals import post_save, pre_save
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
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
from django_strawberry_framework.mutations import resolvers
from django_strawberry_framework.mutations import resolvers as mutation_resolvers
from django_strawberry_framework.mutations.inputs import (
    NON_FIELD_ERROR_KEY,
    _relation_field_index,
    mutation_input_field_specs,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.types.converters import SCALAR_MAP
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    call_method,
    pk_of,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.errors import validation_error_to_field_errors
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.querysets import SyncMisuseError, visible_related_object
from django_strawberry_framework.utils.relations import is_model_class
from django_strawberry_framework.utils.typing import (
    call_forwarded,
    object_result,
)
from django_strawberry_framework.utils.write_transaction import (
    managed_write_transaction,
    open_write_pipeline,
    pipeline_write_phase,
    require_write_pipeline,
    write_pipeline,
)
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._idioms import (
    FETCH_MODES,
    TEST_ASYNC_RECOURSE,
    is_object_dict,
    is_object_list,
    requires_fetch_modes,
    saved_pk,
)
from tests._info import make_info, unread_info
from tests._postgresql_stand_in import numeric_refusing_postgresql
from tests.optimizer import _link_models

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from django_strawberry_framework.mutations.resolvers import (
        _ModelDecoded,
        _ModelDecodedWithExcluded,
    )

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _Bool: TypeAlias = models.BooleanField[bool | Combinable, bool]
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _Text: TypeAlias = models.TextField[str | Combinable, str]
    _DecimalSet: TypeAlias = str | float | Decimal | Combinable


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
    item_get_queryset: object | None = None,
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

    item_body: dict[str, object] = {
        "Meta": type(
            "Meta",
            (),
            {"model": product_models.Item, "fields": ("id", "name", "category"), "primary": True},
        ),
    }
    if item_get_queryset is not None:
        item_body["get_queryset"] = item_get_queryset
    ItemT = type("ItemT", (DjangoType, relay.Node), item_body)

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


# ---------------------------------------------------------------------------
# Custom NodeID lookup on the ambient write alias.
# The HTTP identity and decoy-row verdicts live in test_model_mutation_flows_api.py;
# this builder remains for the direct coercion probe's manager-alias witness.
# ---------------------------------------------------------------------------


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
def test_custom_node_id_real_pk_lookup_uses_pinned_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    """A custom NodeID lookup reads through the ambient write pipeline's alias.

    The NodeID payload identifies a non-pk column, so
    ``decode_model_global_id`` must resolve that value to a real pk before the
    mutation locates its row. The lookup is part of the write transaction's
    alias contract: a router may send reads to one alias and writes to another,
    and resolving the NodeID through the default manager would miss a row that
    exists only on the write alias. This package-level seam test pins the
    ambient pipeline recovery on the single-id path (``relay.py::_real_pk_source``)
    without requiring a second test database; the live sharded fakeshop suite
    exercises the same contract end to end.
    """
    seed_data(0)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    _schema, CategoryNode = _build_category_node_schema()
    target = catalog_categories[0]
    product_models.Category.objects.filter(pk=target.pk).update(
        description="before",
        is_private=False,
        name="alias-node-id",
    )
    target.refresh_from_db()
    gid = global_id_for(CategoryNode, target.name)
    manager = product_models.Category._default_manager
    using = mock.Mock(wraps=manager.using)
    monkeypatch.setattr(manager, "using", using)

    with write_pipeline("default", lock=False):
        node_id, error = resolvers.coerce_lookup_id(gid, CategoryNode)

    assert error is None
    assert node_id == saved_pk(target)
    using.assert_called_once_with("default")


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


class OmittedAmountRow(models.Model):
    """A ``blank=True, null=False`` integer, no default, that ``save()`` fills in from ``None``."""

    amount: _Int = models.IntegerField(blank=True)

    class Meta:
        app_label = "products"
        managed = False
        db_table = "tests_mutations_omitted_amount_row"

    @override
    def save(self, *args: object, **kwargs: object) -> None:
        if vars(self)["amount"] is None:
            self.amount = 5
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


class SlugVenue(_UnmanagedProductsModel):
    """The multi-table parent of ``SlugDesk``, keyed by Django, unique on ``slug``."""

    slug: _Text = models.TextField(unique=True)


class SlugDesk(SlugVenue):
    """A multi-table child whose ``seats`` is ``blank=True, null=False`` with no default."""

    seats: _Int = models.IntegerField(blank=True)


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


@pytest.mark.django_db(transaction=True)
def test_create_omitting_a_column_a_save_override_fills_in_writes() -> None:
    """An omitted ``blank=True, null=False`` column a model ``save()`` fills in writes.

    The create diagnoses an omitted column only after its INSERT fails
    (``_created_row_integrity_errors``), never before the save (django-trac 13776): the
    row reaches ``save()`` holding ``None``, the override stores ``5`` and the row is
    written with no error. No fakeshop model fills a column in from ``save()``.
    """
    with _tables(OmittedAmountRow):
        errors = _create_row(OmittedAmountRow, ("amount",), {})
        stored = list(OmittedAmountRow._base_manager.values_list("amount", flat=True))

    assert errors == []
    assert stored == [5]


_COMPETING_SLUG_DISPATCH_UID = "tests.mutations.competing_slug_venue"


@pytest.mark.django_db(transaction=True)
def test_child_create_refused_at_its_parent_table_names_the_childs_null_column() -> None:
    """A multi-table child's refused save answers the ``None`` column that save writes.

    A competing writer takes the parent's unique ``slug`` after validation, so the
    parent-table INSERT is refused, while the omitted ``seats`` the same save writes to
    the child table holds ``None``. One ``Model.save()`` writes both tables and Django
    records one save for it, the save that raised, so its ``seats`` is named, as for a
    single-table row. No fakeshop model inherits a parent with a unique column.
    """

    def _insert_competing_venue(**_kwargs: object) -> None:
        _ = SlugVenue._base_manager.bulk_create([SlugVenue(slug="taken")])

    with _tables(SlugVenue, SlugDesk):
        pre_save.connect(
            _insert_competing_venue,
            sender=SlugDesk,
            weak=False,
            dispatch_uid=_COMPETING_SLUG_DISPATCH_UID,
        )
        try:
            errors = _create_row(SlugDesk, ("slug", "seats"), {"slug": "taken"})
        finally:
            _ = pre_save.disconnect(sender=SlugDesk, dispatch_uid=_COMPETING_SLUG_DISPATCH_UID)
        stored = list(SlugDesk._base_manager.values_list("slug", flat=True))

    assert errors == [
        {
            "field": "seats",
            "messages": ["This field cannot be null."],
            "codes": ["null"],
            "path": ["seats"],
        },
    ]
    assert stored == []


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


# ---------------------------------------------------------------------------
# Partial-update uniqueness groups: inherited declarations and referenced columns
# ---------------------------------------------------------------------------


class _UqColumns(models.Model):
    """Abstract base: ``a`` and ``b`` carry the uniqueness, ``c`` the condition or nothing."""

    a: _Text = models.TextField()
    b: _Text = models.TextField()
    c: _Text = models.TextField(blank=True, default="")

    class Meta:
        abstract = True
        app_label = "products"
        managed = False


class UqPair(_UqColumns):
    """Unique on ``(a, b)`` through a ``UniqueConstraint``."""

    class Meta(_UqColumns.Meta):
        constraints = [models.UniqueConstraint(fields=["a", "b"], name="tests_uq_pair")]


class UqTogether(_UqColumns):
    """Unique on ``(a, b)`` through ``unique_together``."""

    class Meta(_UqColumns.Meta):
        unique_together = [("a", "b")]


class _UqAbstractPair(_UqColumns):
    """An abstract base declaring the ``(a, b)`` constraint its concrete child inherits."""

    class Meta(_UqColumns.Meta):
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=["a", "b"], name="tests_%(class)s_pair"),
        ]


class UqAbstractPair(_UqAbstractPair):
    """A concrete model unique on ``(a, b)`` through its abstract base."""


class UqParentPair(_UnmanagedProductsModel):
    """A multi-table parent unique on ``(a, b)`` through a ``UniqueConstraint``."""

    a: _Text = models.TextField()
    b: _Text = models.TextField()

    class Meta(_UnmanagedProductsModel.Meta):
        constraints = [models.UniqueConstraint(fields=["a", "b"], name="tests_uq_parent_pair")]


class UqChildOfPair(UqParentPair):
    """A multi-table child of ``UqParentPair`` adding the unconstrained ``c``."""

    c: _Text = models.TextField(blank=True, default="")


class UqParentTogether(_UnmanagedProductsModel):
    """A multi-table parent unique on ``(a, b)`` through ``unique_together``."""

    a: _Text = models.TextField()
    b: _Text = models.TextField()

    class Meta(_UnmanagedProductsModel.Meta):
        unique_together = [("a", "b")]


class UqChildOfTogether(UqParentTogether):
    """A multi-table child of ``UqParentTogether`` adding the unconstrained ``c``."""

    c: _Text = models.TextField(blank=True, default="")


class UqConditional(_UqColumns):
    """Unique on ``(a, b)`` among rows whose ``b`` is not empty and ``c`` is not ``draft``.

    The condition reads ``b`` again beside ``fields`` and reads ``c`` only inside a nested
    ``Q``.
    """

    class Meta(_UqColumns.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["a", "b"],
                condition=models.Q(b__gt="") & ~models.Q(c="draft"),
                name="tests_uq_conditional",
                violation_error_code="duplicate_live",
            ),
        ]


class UqExpression(_UqColumns):
    """Unique on ``(Lower(a), b)``: an expression constraint with no ``fields``."""

    class Meta(_UqColumns.Meta):
        constraints = [models.UniqueConstraint(Lower("a"), "b", name="tests_uq_expression")]


class UqGenerated(_UqColumns):
    """Unique on ``(folded, b)``, where ``folded`` is generated from ``a``."""

    # Unannotated: django-stubs declares ``GeneratedField`` without type parameters.
    folded = models.GeneratedField(
        expression=Lower("a"),
        output_field=models.TextField(),
        db_persist=True,
    )

    class Meta(_UqColumns.Meta):
        constraints = [models.UniqueConstraint(fields=["folded", "b"], name="tests_uq_generated")]


class UqSingle(_UqColumns):
    """``a`` alone is ``unique=True``."""

    a: _Text = models.TextField(unique=True)


class UqRootPerA(_UqColumns):
    """Unique on ``a`` among root rows, its condition reading ``parent`` and the row by ``pk``.

    ``pk`` resolves to ``id``, the name the ``validate_constraints`` exclude carries.
    """

    parent: models.ForeignKey[UqRootPerA | Combinable | None, UqRootPerA | None] = (
        models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)
    )

    class Meta(_UqColumns.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["a"],
                condition=models.Q(parent__isnull=True, pk__isnull=False),
                name="tests_uq_root_per_a",
            ),
        ]


class UqChecked(_UqColumns):
    """``a`` must differ from ``b``, through a ``CheckConstraint``."""

    class Meta(_UqColumns.Meta):
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(a=models.F("b")),
                name="tests_uq_checked",
                violation_error_code="a_is_b",
            ),
        ]


class UqCheckedParent(_UnmanagedProductsModel):
    """A multi-table parent whose ``a`` must differ from ``b``, through a ``CheckConstraint``."""

    a: _Text = models.TextField()
    b: _Text = models.TextField()

    class Meta(_UnmanagedProductsModel.Meta):
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(a=models.F("b")),
                name="tests_uq_checked_parent",
                violation_error_code="a_is_b",
            ),
        ]


class UqCheckedChild(UqCheckedParent):
    """A multi-table child of ``UqCheckedParent`` adding the unconstrained ``c``."""

    c: _Text = models.TextField(blank=True, default="")


class _PairedExpressionsConstraint(models.BaseConstraint):
    """A constraint shaped as postgres ``ExclusionConstraint`` keeps its columns.

    ``expressions`` holds ``(expression, operator)`` pairs, an expression possibly a
    bare field name, beside a ``condition``; its ``validate`` (never run here) would skip
    when ``exclude`` names any column either references, as ``ExclusionConstraint``'s does.
    """

    def __init__(
        self,
        *,
        name: str,
        expressions: list[tuple[str | Lower, str]],
        condition: models.Q,
    ) -> None:
        super().__init__(name=name)
        self.expressions = expressions
        self.condition = condition

    @override
    def deconstruct(self) -> tuple[str, Sequence[object], dict[str, object]]:
        """Carry the pairs and the condition through Django's ``clone``."""
        path, args, kwargs = super().deconstruct()
        return path, args, {**kwargs, "expressions": self.expressions, "condition": self.condition}


class UqExcluded(_UqColumns):
    """Declares a ``_PairedExpressionsConstraint`` over ``a``, ``Lower(b)``, conditioned on ``c``.

    Declared only for its groups; no table is created for it.
    """

    class Meta(_UqColumns.Meta):
        constraints = [
            _PairedExpressionsConstraint(
                name="tests_uq_excluded",
                expressions=[("a", "="), (Lower("b"), "=")],
                condition=models.Q(c="live"),
            ),
        ]


def _proxy_of(model: type[Model], name: str) -> type[Model]:
    """A proxy model over ``model``, sharing its table.

    Django keeps ``Meta.constraints`` / ``unique_together`` only on the declaring class,
    and ``models.E016`` refuses a proxy declaring any, so a proxy's own metadata is empty.
    """
    meta = type("Meta", (), {"app_label": "products", "proxy": True})
    return require(type(name, (model,), {"__module__": __name__, "Meta": meta}), is_model_class)


UqPairProxy = _proxy_of(UqPair, "UqPairProxy")
UqPairProxyProxy = _proxy_of(UqPairProxy, "UqPairProxyProxy")
UqTogetherProxy = _proxy_of(UqTogether, "UqTogetherProxy")
UqAbstractPairProxy = _proxy_of(UqAbstractPair, "UqAbstractPairProxy")
UqChildOfPairProxy = _proxy_of(UqChildOfPair, "UqChildOfPairProxy")
UqConditionalProxy = _proxy_of(UqConditional, "UqConditionalProxy")
UqExpressionProxy = _proxy_of(UqExpression, "UqExpressionProxy")
UqSingleProxy = _proxy_of(UqSingle, "UqSingleProxy")
UqCheckedProxy = _proxy_of(UqChecked, "UqCheckedProxy")


class UqSlugged(_UnmanagedProductsModel):
    """``slug`` is unique among published rows and filled from ``name`` by ``save()``."""

    name: _Text = models.TextField()
    slug: _Text = models.TextField()
    published: _Bool = models.BooleanField(default=False)

    class Meta(_UnmanagedProductsModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(published=True),
                name="tests_uq_slugged_live",
            ),
        ]

    @override
    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = self.name.lower()
        call_forwarded(super().save, args, kwargs)


class UqStatus(_UnmanagedProductsModel):
    """``n`` may be negative only while ``status`` is ``draft``; ``status`` has choices."""

    a: _Text = models.TextField(blank=True, default="")
    n: _Int = models.IntegerField(default=0)
    status: _Text = models.TextField(
        choices=[("draft", "Draft"), ("live", "Live")],
        default="draft",
    )

    class Meta(_UnmanagedProductsModel.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(n__gte=0) | models.Q(status="draft"),
                name="tests_uq_status_n",
            ),
        ]


class UqDated(_UnmanagedProductsModel):
    """``slug`` is unique per ``pub`` date (``unique_for_date``)."""

    a: _Text = models.TextField(blank=True, default="")
    slug: _Text = models.TextField(unique_for_date="pub")
    pub: models.DateField[str | datetime.date | Combinable, datetime.date] = models.DateField()


def _write_row(
    model: type[Model],
    data: dict[str, object],
    *,
    pk: object = None,
    fields: tuple[str, ...] = ("a", "b", "c"),
) -> object:
    """Run one model-flavor ``writeRow`` of ``fields``; answer its payload.

    An update (``pk`` set, partial input) or a create (``pk`` unset). ``data`` is written
    inline, so the query need not spell the generated input's name.
    """
    type(
        f"{model.__name__}T",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": ("id", *fields), "primary": True})},
    )
    meta: dict[str, object] = {
        "model": model,
        "fields": fields,
        "operation": "create" if pk is None else "update",
        "permission_classes": [_AllowAll],
    }
    if pk is not None:
        meta["select_for_update"] = False
    write = type("WriteRow", (DjangoMutation,), {"Meta": type("Meta", (), meta)})

    @strawberry.type
    class Mutation:
        write_row = DjangoMutationField(write)

    finalize_django_types()
    literal = ", ".join(f"{name}: {json.dumps(value)}" for name, value in data.items())
    selection = "{ result { id } errors{ field messages codes } }"
    if pk is None:
        query = f"mutation {{ writeRow(data: {{ {literal} }}) {selection} }}"
        variables = None
    else:
        query = f"mutation($id: ID!) {{ writeRow(id: $id, data: {{ {literal} }}) {selection} }}"
        variables = {"id": str(pk)}
    res = _schema(Mutation).execute_sync(query, variable_values=variables)
    assert res.errors is None, res.errors
    return _json_at(res.data, "writeRow")


def _unique_together_errors(label: str) -> list[dict[str, object]]:
    """The envelope Django's own ``(a, b)`` uniqueness check answers for ``label``."""
    return [
        {
            "field": NON_FIELD_ERROR_KEY,
            "messages": [f"{label} with this A and B already exists."],
            "codes": ["unique_together"],
        },
    ]


def _violated_errors(name: str, codes: list[str]) -> list[dict[str, object]]:
    """The envelope a conditional or expression ``UniqueConstraint`` named ``name`` answers.

    Django raises the constraint's default ``violation_error_message`` under its
    ``violation_error_code``; an unset code answers no code.
    """
    return [
        {
            "field": NON_FIELD_ERROR_KEY,
            "messages": [
                str(models.UniqueConstraint.default_violation_error_message) % {"name": name},
            ],
            "codes": codes,
        },
    ]


_UNIQUE_GROUP_CASES = [
    pytest.param(UqPair, (UqPair,), {"a": "x"}, _unique_together_errors("Uq pair"), id="concrete"),
    pytest.param(
        UqPairProxy,
        (UqPair,),
        {"a": "x"},
        _unique_together_errors("Uq pair"),
        id="proxy",
    ),
    pytest.param(
        UqPairProxyProxy,
        (UqPair,),
        {"a": "x"},
        _unique_together_errors("Uq pair"),
        id="proxy-of-proxy",
    ),
    pytest.param(
        UqTogether,
        (UqTogether,),
        {"a": "x"},
        _unique_together_errors("Uq together"),
        id="unique-together",
    ),
    pytest.param(
        UqTogetherProxy,
        (UqTogether,),
        {"a": "x"},
        _unique_together_errors("Uq together"),
        id="unique-together-proxy",
    ),
    pytest.param(
        UqAbstractPairProxy,
        (UqAbstractPair,),
        {"a": "x"},
        _unique_together_errors("Uq abstract pair"),
        id="abstract-base-proxy",
    ),
    pytest.param(
        UqChildOfPair,
        (UqParentPair, UqChildOfPair),
        {"a": "x"},
        _unique_together_errors("Uq parent pair"),
        id="multi-table-parent-constraint",
    ),
    pytest.param(
        UqChildOfTogether,
        (UqParentTogether, UqChildOfTogether),
        {"a": "x"},
        _unique_together_errors("Uq parent together"),
        id="multi-table-parent-unique-together",
    ),
    pytest.param(
        UqChildOfPairProxy,
        (UqParentPair, UqChildOfPair),
        {"a": "x"},
        _unique_together_errors("Uq parent pair"),
        id="multi-table-child-proxy",
    ),
    pytest.param(
        UqConditional,
        (UqConditional,),
        {"a": "x"},
        _violated_errors("tests_uq_conditional", ["duplicate_live"]),
        id="conditional",
    ),
    pytest.param(
        UqConditionalProxy,
        (UqConditional,),
        {"a": "x"},
        _violated_errors("tests_uq_conditional", ["duplicate_live"]),
        id="conditional-proxy",
    ),
    pytest.param(
        UqExpression,
        (UqExpression,),
        {"a": "X"},
        _violated_errors("tests_uq_expression", []),
        id="expression",
    ),
    pytest.param(
        UqExpressionProxy,
        (UqExpression,),
        {"a": "X"},
        _violated_errors("tests_uq_expression", []),
        id="expression-proxy",
    ),
    pytest.param(
        UqGenerated,
        (UqGenerated,),
        {"a": "X"},
        [
            {
                "field": NON_FIELD_ERROR_KEY,
                "messages": ["Uq generated with this Folded and B already exists."],
                "codes": ["unique_together"],
            },
        ],
        id="generated-member",
    ),
    pytest.param(
        UqRootPerA,
        (UqRootPerA,),
        {"a": "x"},
        _violated_errors("tests_uq_root_per_a", []),
        id="condition-by-relation-and-pk",
    ),
    pytest.param(
        UqSingleProxy,
        (UqSingle,),
        {"a": "x"},
        [
            {
                "field": "a",
                "messages": ["Uq single with this A already exists."],
                "codes": ["unique"],
            },
        ],
        id="single-field-unique-proxy",
    ),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "model",
        "tables",
        "data",
        "errors",
    ),
    _UNIQUE_GROUP_CASES,
)
def test_partial_update_validates_every_unique_check_django_runs_for_the_row(
    model: type[Model],
    tables: tuple[type[Model], ...],
    data: dict[str, object],
    errors: list[dict[str, object]],
) -> None:
    """A partial update colliding on a unique check through an unprovided column is refused.

    Each row collides with its sibling through the provided ``a`` and the unprovided
    ``b`` (and, for the conditional constraint, the unprovided ``c`` its condition reads;
    for the generated member, the ``folded`` column computed from ``a``). The unprovided
    co-members stay validated whether the check is declared on the model, on a proxy's
    concrete model, on an abstract base, or on a multi-table parent, and whether it names
    its columns in ``fields``, in its ``condition``, in an expression or through a
    generated column, so Django's own uniqueness error answers before the save and the
    stored row is unchanged. No fakeshop model has any of these shapes.
    """
    with _tables(*tables):
        _ = model.objects.create(a="x", b="1", c="live")
        row = model.objects.create(a="y", b="1", c="live")
        answered = _write_row(model, data, pk=pk_of(row))
        stored = sorted(model._base_manager.values_list("a", flat=True))

    assert answered == {"result": None, "errors": errors}
    assert stored == ["x", "y"]


_CHECK_CONSTRAINT_CASES = [
    pytest.param(UqChecked, (UqChecked,), "tests_uq_checked", id="concrete"),
    pytest.param(UqCheckedProxy, (UqChecked,), "tests_uq_checked", id="proxy"),
    pytest.param(
        UqCheckedChild,
        (UqCheckedParent, UqCheckedChild),
        "tests_uq_checked_parent",
        id="multi-table-parent",
    ),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(("model", "tables", "name"), _CHECK_CONSTRAINT_CASES)
def test_partial_update_violating_a_check_constraint_through_an_unprovided_column_is_refused(
    model: type[Model],
    tables: tuple[type[Model], ...],
    name: str,
) -> None:
    """A provided ``a`` equal to the stored, unprovided ``b`` fails ``a != b`` before the save.

    The unprovided ``b`` the check reads stays validated, whether the ``CheckConstraint``
    is declared on the model, on a proxy's concrete model or on a multi-table parent, so
    Django's own violation answers instead of the database's ``constraint`` envelope and
    the stored row is unchanged. No fakeshop model a ``DjangoMutation`` writes declares a
    ``CheckConstraint``.
    """
    with _tables(*tables):
        _ = model.objects.create(a="x", b="1")
        row = model.objects.create(a="y", b="1")
        answered = _write_row(model, {"a": "1"}, pk=pk_of(row))
        stored = sorted(model._base_manager.values_list("a", flat=True))

    assert answered == {"result": None, "errors": _violated_errors(name, ["a_is_b"])}
    assert stored == ["x", "y"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(("model", "tables", "name"), _CHECK_CONSTRAINT_CASES)
def test_partial_update_satisfying_a_check_constraint_through_an_unprovided_column_saves(
    model: type[Model],
    tables: tuple[type[Model], ...],
    name: str,
) -> None:
    """A provided ``a`` that differs from the stored, unprovided ``b`` passes the check and saves."""
    del name
    with _tables(*tables):
        row = model.objects.create(a="y", b="1")
        answered = _write_row(model, {"a": "z"}, pk=pk_of(row))
        stored = list(model._base_manager.values_list("a", "b"))

    assert answered == {"result": {"id": pk_of(row)}, "errors": []}
    assert stored == [("z", "1")]


@pytest.mark.parametrize(
    ("model", "provided", "exclude"),
    [
        pytest.param(UqPairProxy, {"a"}, ["c", "id"], id="proxy"),
        pytest.param(UqPairProxy, {"c"}, ["a", "b", "id"], id="proxy-unrelated-provided"),
        pytest.param(UqTogetherProxy, {"b"}, ["c", "id"], id="unique-together-proxy"),
        pytest.param(
            UqChildOfPair,
            {"a"},
            ["c", "id", "uqparentpair_ptr"],
            id="multi-table-parent-constraint",
        ),
        pytest.param(UqConditional, {"a"}, ["id"], id="conditional"),
        pytest.param(UqConditional, {"c"}, ["id"], id="conditional-through-condition"),
        pytest.param(UqRootPerA, {"a"}, ["b", "c"], id="condition-by-relation-and-pk"),
        pytest.param(UqExpressionProxy, {"a"}, ["c", "id"], id="expression-proxy"),
        pytest.param(UqGenerated, {"a"}, ["c", "id"], id="generated-member"),
        pytest.param(UqSingleProxy, {"b"}, ["a", "c", "id"], id="single-field-unique-unprovided"),
        pytest.param(UqCheckedProxy, {"a"}, ["c", "id"], id="check-constraint-proxy"),
        pytest.param(
            UqCheckedChild,
            {"c"},
            [
                "a",
                "b",
                "id",
                "uqcheckedparent_ptr",
            ],
            id="check-constraint-unrelated-provided",
        ),
        pytest.param(UqExcluded, {"a"}, ["id"], id="exclusion-shaped-constraint"),
        pytest.param(UqDated, {"slug"}, ["a", "id"], id="unique-for-date-field"),
        pytest.param(UqDated, {"pub"}, ["a", "id"], id="unique-for-date-date"),
        pytest.param(UqDated, {"a"}, ["id", "pub", "slug"], id="unique-for-date-unrelated"),
    ],
)
def test_unprovided_exclude_keeps_every_member_of_a_group_a_provided_field_joins(
    model: type[Model],
    provided: set[str],
    exclude: list[str],
) -> None:
    """A group with a provided member keeps its other members; every other column stays out.

    The groups come from the model's and its parents' declarations and from every column a
    constraint's condition, expressions and generated members read; an unprovided column in
    no group with a provided one is excluded, as a ``partial=True`` update leaves it.
    """
    assert resolvers._unprovided_exclude(model, provided) == exclude


def test_clean_excludes_field_validates_only_provided_columns() -> None:
    """``clean_fields`` skips every unprovided column; the checks keep a joined co-member.

    ``n`` joins the ``CheckConstraint`` over ``n`` and ``status``, so ``status`` leaves
    the uniqueness / constraint exclude while staying in the ``clean_fields`` one.
    """
    assert resolvers._clean_excludes(UqStatus, {"n"}) == resolvers.CleanExcludes(
        fields=["a", "id", "status"],
        checks=["a", "id"],
    )


@pytest.mark.django_db(transaction=True)
def test_create_validates_a_constraint_over_a_column_save_fills_without_field_validating_it() -> (
    None
):
    """A create leaving out ``slug`` saves: the constraint runs, ``slug`` is not field-validated.

    ``published`` joins the conditional constraint over ``slug``, so the constraint runs
    against the row (no published row carries the empty slug), while the unprovided
    ``slug`` is left to ``save()``, which fills it, instead of failing ``blank``.
    """
    with _tables(UqSlugged):
        answered = _write_row(
            UqSlugged,
            {"name": "Hello", "published": True},
            fields=("name", "published"),
        )
        saved = UqSlugged._base_manager.get()

    assert answered == {"result": {"id": pk_of(saved)}, "errors": []}
    assert saved.slug == "hello"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("n", "errors", "stored"),
    [
        pytest.param(5, [], (5, "legacy"), id="satisfied"),
        pytest.param(
            -1,
            [
                {
                    "field": NON_FIELD_ERROR_KEY,
                    "messages": [
                        str(models.CheckConstraint.default_violation_error_message)
                        % {"name": "tests_uq_status_n"},
                    ],
                    "codes": [],
                },
            ],
            (1, "legacy"),
            id="violated",
        ),
    ],
)
def test_update_checks_a_stored_column_outside_its_choices_without_field_validating_it(
    n: int,
    errors: list[dict[str, object]],
    stored: tuple[int, str],
) -> None:
    """A stored ``status`` outside today's choices is checked against, never field-validated.

    ``n`` joins the ``CheckConstraint`` over ``n`` and ``status``: the check runs against
    the stored ``legacy`` status and refuses a negative ``n``, while ``status`` itself, left
    out of the input, never answers ``invalid_choice``.
    """
    with _tables(UqStatus):
        row = UqStatus.objects.create(n=1, status="live")
        _ = UqStatus.objects.filter(pk=pk_of(row)).update(status="legacy")
        answered = _write_row(UqStatus, {"n": n}, pk=pk_of(row), fields=("a", "n", "status"))
        saved = list(UqStatus._base_manager.values_list("n", "status"))

    result = None if errors else {"id": pk_of(row)}
    assert answered == {"result": result, "errors": errors}
    assert saved == [stored]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("rows", "data"),
    [
        pytest.param(
            [("s", "2026-01-01"), ("t", "2026-01-01")],
            {"slug": "s"},
            id="provided-field",
        ),
        pytest.param(
            [("s", "2026-01-01"), ("s", "2026-01-02")],
            {"pub": "2026-01-01"},
            id="provided-date",
        ),
    ],
)
def test_partial_update_validates_unique_for_date_through_an_unprovided_member(
    rows: list[tuple[str, str]],
    data: dict[str, object],
) -> None:
    """``unique_for_date`` runs when only one of the field and its date field is provided.

    Django's ``_get_unique_checks`` skips the date check when either is excluded, so the
    unprovided one stays in: its duplicate is Django's ``unique_for_date`` error.
    """
    with _tables(UqDated):
        created = [UqDated.objects.create(slug=slug, pub=pub) for slug, pub in rows]
        answered = _write_row(UqDated, data, pk=pk_of(created[1]), fields=("a", "slug", "pub"))
        stored = list(UqDated._base_manager.order_by("pk").values_list("slug", "pub"))

    assert answered == {
        "result": None,
        "errors": [
            {
                "field": "slug",
                "messages": ["Slug must be unique for Pub date."],
                "codes": ["unique_for_date"],
            },
        ],
    }
    assert stored == [(slug, datetime.date.fromisoformat(pub)) for slug, pub in rows]


@pytest.mark.django_db(transaction=True)
def test_a_field_failing_validation_is_left_out_of_its_uniqueness_checks() -> None:
    """A provided ``slug`` that fails ``clean_fields`` answers that error alone.

    ``Model.full_clean`` leaves a field that failed validation out of ``validate_unique``
    and ``validate_constraints``, so the blank ``slug`` is not also reported as a
    ``unique_for_date`` duplicate of the stored blank slug on the same date.
    """
    with _tables(UqDated):
        _ = UqDated.objects.create(slug="", pub="2026-01-01")
        row = UqDated.objects.create(slug="t", pub="2026-01-01")
        answered = _write_row(UqDated, {"slug": ""}, pk=pk_of(row), fields=("a", "slug", "pub"))

    assert answered == {
        "result": None,
        "errors": [
            {"field": "slug", "messages": ["This field cannot be blank."], "codes": ["blank"]},
        ],
    }


@pytest.mark.django_db
def test_sync_misuse_async_get_queryset_from_sync_path() -> None:
    """A sync update over a type with an ``async def get_queryset`` raises ``SyncMisuseError``."""
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()

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
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    cat.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="X",
        category=cat,
    )
    item.refresh_from_db()
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
        key_attname=None,
        info=unread_info(),
        relation_field=m2m_field,
    )
    assert error is not None
    assert error.field == "genres"


# ---------------------------------------------------------------------------
# Scalar field named ``<x>_id`` (spec-036)
#
# ``library.TaggedItem`` has a *scalar* ``object_id`` (a ``PositiveIntegerField``,
# emitted by the input generator) AND a ``GenericForeignKey`` ``content_object``.
# The decode index / provided-name mapping must NOT reverse ``object_id`` to a
# relation field by a blind ``_id`` suffix strip, and must NOT index the
# GFK as a decode-able FK. Both are reasoned from the relation field index,
# not a string heuristic.
# ---------------------------------------------------------------------------


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


def test_validation_error_to_field_errors_non_dict_uses_all_key() -> None:
    """A non-dict ``ValidationError`` (``.messages``, no ``.error_dict``) maps under the sentinel.

    ``full_clean()`` always raises with an ``error_dict`` (the keyed path), so this
    ``.messages`` fallback serves a bare ``ValidationError`` - the shape the form /
    serializer flavors and a model ``clean()`` raising a plain
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
    """A non-dict (model-wide) Django ``ValidationError`` keys ``"__all__"`` with an EMPTY path."""
    (fe,) = validation_error_to_field_errors(
        DjangoValidationError("Whole-object problem.", code="invalid"),
    )
    assert fe.field == NON_FIELD_ERROR_KEY
    assert fe.path == []
    assert fe.codes == ["invalid"]


# ---------------------------------------------------------------------------
# Row locking on the update/delete locate (spec-039)
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
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()
    _schema_and_types = _build_item_schema()
    ItemT = _schema_and_types[1][1]
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    cat.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="Lockable",
        category=cat,
    )
    item.refresh_from_db()

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


@requires_fetch_modes
@pytest.mark.django_db
@pytest.mark.parametrize("mode_name", ["FETCH_PEERS", "FETCH_RAISE"])
@pytest.mark.parametrize("select_for_update", [True, False], ids=["locked", "unlocked"])
def test_locate_instance_loads_the_row_under_the_hook_fetch_mode(
    mode_name: str,
    *,
    select_for_update: bool,
) -> None:
    """The located row carries the fetch mode the type's ``get_queryset`` set.

    The locked locate reads the row through the base manager filtered by the visible
    primary keys, a queryset the hook never touched; it carries the visible queryset's
    mode, so the row loads its relations as a read of it does. The unlocked locate reads
    through the sealed visible queryset itself.
    """
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()
    mode = FETCH_MODES[mode_name]

    def _hook(
        _cls: type[DjangoType],
        queryset: QuerySet[product_models.Item],
        _info: object,
    ) -> QuerySet[product_models.Item]:
        return queryset.fetch_mode(mode)

    ItemT = _build_item_schema(item_get_queryset=classmethod(_hook))[1][1]
    category = catalog_categories[0]
    product_models.Category.objects.filter(pk=category.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    category.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="Lockable",
        category=category,
    )
    item.refresh_from_db()

    with transaction.atomic():
        located = mutation_resolvers.locate_instance(
            ItemT,
            saved_pk(item),
            unread_info(),
            alias="default",
            select_for_update=select_for_update,
        )
    assert located is not None
    assert truth.instance_state(located._state).get("fetch_mode") is mode


@pytest.mark.django_db
def test_locate_instance_confirms_the_locked_row_with_a_fresh_visibility_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A locked row is located only when a second, unlocked statement still sees it.

    SQLite takes no row lock, so the re-read is forced on here; the Postgres race it
    closes is ``test_locate_instance_misses_a_row_hidden_while_its_lock_waited``.
    """
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()
    ItemT = _build_item_schema()[1][1]
    category = catalog_categories[0]
    product_models.Category.objects.filter(pk=category.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    category.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="Lockable",
        category=category,
    )
    item.refresh_from_db()
    monkeypatch.setattr(mutation_resolvers, "locks_rows", _returning(value=True))

    with transaction.atomic(), CaptureQueriesContext(connection) as captured:
        located = mutation_resolvers.locate_instance(
            ItemT,
            saved_pk(item),
            unread_info(),
            alias="default",
        )
    assert located is not None
    assert saved_pk(located) == saved_pk(item)
    assert len(captured) == 2

    no_rows: set[object] = set()
    monkeypatch.setattr(mutation_resolvers, "rows_visible_after_lock", _returning(no_rows))
    with transaction.atomic():
        assert (
            mutation_resolvers.locate_instance(
                ItemT,
                saved_pk(item),
                unread_info(),
                alias="default",
            )
            is None
        )


_RowT = TypeVar("_RowT", bound=Model)


def _public_rows(
    _cls: type[DjangoType],
    queryset: QuerySet[_RowT],
    _info: strawberry.Info,
) -> QuerySet[_RowT]:
    """A ``get_queryset`` hook that hides every ``is_private`` row."""
    return queryset.filter(is_private=False)


def _await_a_lock_waiter() -> None:
    """Return once another backend of this database waits on a lock; fail after 10 seconds."""
    deadline = time.monotonic() + 10
    with connection.cursor() as cursor:
        while time.monotonic() < deadline:
            cursor.execute(
                "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' "
                "AND datname = current_database() AND pid <> pg_backend_pid()",
            )
            if call_method(cursor, "fetchall") != [(0,)]:
                return
            time.sleep(0.01)
    pytest.fail("no backend waited on the held row lock")


def _hide_while_a_reader_waits(model: type[Model], pk: object, held: threading.Event) -> None:
    """On this thread's connection, mark a row private and commit once another backend waits on it."""
    try:
        with transaction.atomic():
            model._base_manager.filter(pk=pk).update(is_private=True)
            held.set()
            _await_a_lock_waiter()
    finally:
        connection.close()


@contextlib.contextmanager
def _hidden_while_waited_on(model: type[Model], pk: object) -> Generator[None]:
    """Run the body while another connection holds ``pk``'s row and hides it once the body waits."""
    held = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as other:
        hiding = other.submit(_hide_while_a_reader_waits, model, pk, held)
        assert held.wait(10)
        yield
        hiding.result()


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
def test_locate_instance_misses_a_row_hidden_while_its_lock_waited() -> None:
    """Under READ COMMITTED a row the lock's wait saw hidden is not found.

    The locked statement re-reads the row after the wait but keeps its visibility
    subquery's snapshot, so it still returns the row; the fresh re-read does not.
    """
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()
    ItemT = _build_item_schema(item_get_queryset=classmethod(_public_rows))[1][1]
    category = catalog_categories[0]
    product_models.Category.objects.filter(pk=category.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    category.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="Hidden mid-lock",
        category=category,
    )
    item.refresh_from_db()

    with _hidden_while_waited_on(product_models.Item, saved_pk(item)), transaction.atomic():
        located = mutation_resolvers.locate_instance(
            ItemT,
            saved_pk(item),
            unread_info(),
            alias="default",
        )

    assert located is None


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
def test_locate_instance_lock_blocks_a_second_connections_writer() -> None:
    """The located row stays locked until the write transaction ends."""
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()
    ItemT = _build_item_schema()[1][1]
    category = catalog_categories[0]
    product_models.Category.objects.filter(pk=category.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    category.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="Lockable",
        category=category,
    )
    item.refresh_from_db()

    def _write_with_a_short_lock_timeout() -> None:
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL lock_timeout = '100ms'")
                product_models.Item.objects.filter(pk=saved_pk(item)).update(name="Overwritten")
        finally:
            connection.close()

    with transaction.atomic():
        assert mutation_resolvers.locate_instance(
            ItemT,
            saved_pk(item),
            unread_info(),
            alias="default",
        )
        with (
            ThreadPoolExecutor(max_workers=1) as other,
            pytest.raises(OperationalError, match="lock timeout"),
        ):
            other.submit(_write_with_a_short_lock_timeout).result()

    item.refresh_from_db()
    assert item.name == "Lockable"


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
def test_relation_target_hidden_while_its_lock_waited_is_a_relation_error() -> None:
    """A create's category, hidden by the commit its row lock waited on, answers the relation error."""
    seed_data(0)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))

    @strawberry.input
    class GidItemInput:
        category_id: strawberry.ID = strawberry.field(description="custom category ref")

    schema, (CategoryT, _ItemT) = _build_item_schema(
        category_get_queryset=classmethod(_public_rows),
        input_cls=GidItemInput,
    )
    category = catalog_categories[0]
    product_models.Category.objects.filter(pk=category.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    category.refresh_from_db()
    variables = {
        "d": {
            "name": "Linked mid-lock",
            "categoryId": global_id_for(CategoryT, saved_pk(category)),
        },
    }

    with _hidden_while_waited_on(product_models.Category, saved_pk(category)):
        res = schema.execute_sync(_CREATE, variable_values=variables)

    assert_mutation_field_error(res, "createItem", "categoryId")
    assert not product_models.Item.objects.filter(name="Linked mid-lock").exists()


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
def test_visible_related_object_misses_a_target_hidden_while_its_lock_waited() -> None:
    """The single-object relation decode re-reads visibility after its row lock too."""
    seed_data(0)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    _build_item_schema(category_get_queryset=classmethod(_public_rows))
    category = catalog_categories[0]
    product_models.Category.objects.filter(pk=category.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    category.refresh_from_db()

    with (
        _hidden_while_waited_on(product_models.Category, saved_pk(category)),
        transaction.atomic(),
        write_pipeline("default", lock=True),
    ):
        found = visible_related_object(
            product_models.Category,
            saved_pk(category),
            unread_info(),
            async_recourse=TEST_ASYNC_RECOURSE,
        )

    assert found is None


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
            write_step=lambda _instance, _decoded: product_models.Item(pk=7),
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
    located = product_models.Item(pk=7)
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


@pytest.mark.parametrize(
    ("flag", "captured"),
    [
        pytest.param({}, False, id="default"),
        pytest.param({"snapshot_target": False}, False, id="not_asked"),
        pytest.param({"snapshot_target": True}, True, id="snapshot_target"),
    ],
)
def test_pipeline_captures_target_state_only_when_asked(
    monkeypatch: pytest.MonkeyPatch,
    flag: dict[str, bool],
    *,
    captured: bool,
) -> None:
    """Only a pipeline run with ``snapshot_target`` captures the located row's field values.

    The serializer flavor is the one that checks the row for in-memory drift, so it
    alone asks for the capture; every other flavor runs no value type's copy code
    at the locate and publishes no ``target_state``.
    """
    located = product_models.Item(pk=7)
    snapshot = {"name": object()}
    calls: list[object] = []
    seen: dict[str, object] = {}

    def recording_snapshot(instance: object) -> dict[str, object]:
        calls.append(instance)
        return snapshot

    def probe_write(instance: Model | None, _decoded: object) -> Model | None:
        seen["target_state"] = require_write_pipeline().target_state
        return instance

    mutation_cls = _pipeline_harness(monkeypatch)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))
    monkeypatch.setattr(mutation_resolvers, "snapshot_target_state", recording_snapshot)

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
            write_step=probe_write,
            **flag,
        )
    assert result == "ok"
    assert calls == ([located] if captured else [])
    assert seen["target_state"] is (snapshot if captured else None)


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


def test_delete_pipeline_refuses_a_located_row_that_is_not_a_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The delete write step takes only a model row; any other located value raises ``TypeError``.

    ``locate_instance`` answers a model row or ``None``; the write step's guard holds that
    contract after authorization, before any snapshot or delete runs.
    """
    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=set,
        _meta=SimpleNamespace(concrete_fields=[]),
    )
    mutation_cls = _pipeline_harness(monkeypatch, operation="delete")
    mutation_cls.configure_mock(**{"_mutation_meta.permission_classes": []})
    monkeypatch.setattr(mutation_resolvers, "locate_instance", _returning(located))

    with (
        patch.object(transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(TypeError, match="expected an instance of"),
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


def test_bound_model_fields_refuses_a_delete_mutation() -> None:
    """A delete has no input, so the bind stashes no model-field index for a decode to read."""

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
    with pytest.raises(TypeError, match="DeleteItem holds no bound model-field index"):
        mutation_resolvers._bound_model_fields(DeleteItem)


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
        decoded: _ModelDecoded = (cat, [("fake_m2m", [1, 2])], resolvers.CleanExcludes([], []))
        with managed_write_transaction("default"), open_write_pipeline(CreateCategoryMutation):
            failure = resolvers._model_write_step(
                CreateCategoryMutation,
                None,
                decoded,
                specs=CreateCategoryMutation._input_field_specs,
            )
        assert isinstance(failure, resolvers.StepFailure)
        errors = failure.errors
        assert len(errors) == 1
        assert errors[0].field == NON_FIELD_ERROR_KEY
        assert errors[0].codes == ["constraint"]


def test_model_write_step_refuses_a_decode_carrying_excluded_values() -> None:
    """A four-tuple decode (one carrying ``EXCLUDED`` values) raises ``ValueError``.

    The shared model write tail cannot write an excluded value, so a bind that stashes an
    ``EXCLUDED`` spec without a flavor write step consuming it fails loud.
    """
    decoded: _ModelDecodedWithExcluded = (
        product_models.Item(),
        [],
        resolvers.CleanExcludes([], []),
        {"password": "secret"},
    )
    with pytest.raises(ValueError, match=r"three-tuple; a decode carrying EXCLUDED values"):
        resolvers._model_write_step(DjangoMutation, None, decoded, specs=())


@pytest.mark.django_db
def test_delete_integrity_error_contained_in_envelope() -> None:
    """IntegrityError during instance.delete() is returned as the constraint FieldError envelope."""
    seed_data(0)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    cat.refresh_from_db()

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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "returned",
    [
        None,
        1,
        (1,),
        (1, None),
    ],
    ids=[
        "none",
        "int",
        "one-tuple",
        "pair-without-dict",
    ],
)
def test_delete_without_a_count_is_success(returned: object) -> None:
    """A ``delete()`` returning anything but Django's ``(total, per_model)`` pair succeeds.

    Only Django's own pair reports the target model's count, so another return (a
    soft-delete override's ``None``) reports no count and answers no envelope, never a
    top-level ``TypeError`` / ``ValueError`` from unpacking it.
    """
    seed_data(0)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    cat.refresh_from_db()

    with patch.object(product_models.Category, "delete", return_value=returned):
        assert resolvers._delete_or_field_errors(cat) is None


@pytest.mark.django_db
def test_delete_of_zero_target_rows_is_conflict() -> None:
    """Django's pair with the target model's count zero is the ``conflict`` envelope on ``id``."""
    seed_data(0)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name=_category_name(),
    )
    cat.refresh_from_db()

    with patch.object(product_models.Category, "delete", return_value=(0, {})):
        errors = resolvers._delete_or_field_errors(cat)
    assert isinstance(errors, list)
    assert [(error.field, error.codes) for error in errors] == [("id", ["conflict"])]


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


class SpelledDecimalTarget(models.Model):
    """A relation target keyed by a ``DecimalField`` without ``max_digits``."""

    code: models.DecimalField[str | float | Decimal | Combinable, Decimal] = models.DecimalField(
        primary_key=True,
        max_digits=None,
        decimal_places=None,
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "mutations_spelled_decimal_target"


class SpelledStampTarget(models.Model):
    """A relation target keyed by an aware ``DateTimeField``."""

    stamp: models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ] = models.DateTimeField(primary_key=True)

    class Meta:
        app_label = "products"
        managed = False
        db_table = "mutations_spelled_stamp_target"


class SpelledDecimalOwner(models.Model):
    """A row relating to the decimal-keyed target by a nullable FK and an M2M."""

    name: _Text = models.TextField()
    decimal_target: models.ForeignKey[
        SpelledDecimalTarget | Combinable | None,
        SpelledDecimalTarget | None,
    ] = models.ForeignKey(
        SpelledDecimalTarget,
        on_delete=models.CASCADE,
        null=True,
        related_name="+",
    )
    decimal_targets: models.ManyToManyField[SpelledDecimalTarget, models.Model] = (
        models.ManyToManyField(SpelledDecimalTarget, related_name="+")
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "mutations_spelled_decimal_owner"


class SpelledStampOwner(models.Model):
    """A row relating to the datetime-keyed target by a nullable FK and an M2M.

    An owner of its own: a row also carrying the decimal key reads that column back
    whenever it is fetched, and Django reads a ``DecimalField`` without
    ``decimal_places`` only from 6.1, so the datetime rows run on every supported Django.
    """

    name: _Text = models.TextField()
    stamp_target: models.ForeignKey[
        SpelledStampTarget | Combinable | None,
        SpelledStampTarget | None,
    ] = models.ForeignKey(
        SpelledStampTarget,
        on_delete=models.CASCADE,
        null=True,
        related_name="+",
    )
    stamp_targets: models.ManyToManyField[SpelledStampTarget, models.Model] = (
        models.ManyToManyField(SpelledStampTarget, related_name="+")
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "mutations_spelled_stamp_owner"


def _spelled_key_models(stored: object) -> tuple[type[models.Model], type[models.Model]]:
    """The target keyed by ``stored``'s kind and the owner relating to it."""
    if isinstance(stored, Decimal):
        return SpelledDecimalTarget, SpelledDecimalOwner
    return SpelledStampTarget, SpelledStampOwner


@contextlib.contextmanager
def _spelled_key_tables(stored: object) -> Generator[None, None, None]:
    """Create the tables of ``stored``'s kind; its target holds one row keyed by it."""
    target, owner = _spelled_key_models(stored)
    created: list[type[models.Model]] = []
    try:
        with connection.schema_editor() as editor:
            for model in (target, owner):
                editor.create_model(model)
                created.append(model)
        _ = target._default_manager.create(pk=stored)
        yield
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(created):
                editor.delete_model(model)


def _spelled_key_schema(stored: object) -> strawberry.Schema:
    """A create mutation writing both relations of ``stored``'s owner by raw pk."""
    _, owner = _spelled_key_models(stored)
    prefix = "decimal" if isinstance(stored, Decimal) else "stamp"

    class SpelledKeyOwnerT(DjangoType):
        class Meta:
            model = owner
            fields = ("name",)

    class CreateSpelledKeyOwner(DjangoMutation):
        class Meta:
            model = owner
            operation = "create"
            fields = ("name", f"{prefix}_target", f"{prefix}_targets")
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_spelled_key_owner = DjangoMutationField(CreateSpelledKeyOwner)

    finalize_django_types()
    del SpelledKeyOwnerT
    return _schema(Mutation)


_SPELLED_DECIMAL_PAIRS = [
    pytest.param(Decimal("2.5"), "2.50", id="trailing-zero"),
    pytest.param(Decimal(7), "7.0", id="one-fractional-zero"),
    pytest.param(Decimal(7), "7.00", id="two-fractional-zeros"),
    pytest.param(Decimal(70), "7E+1", id="exponent"),
    pytest.param(Decimal(0), "0.00", id="zero"),
]
_SPELLED_STAMP_PAIR = pytest.param(
    datetime.datetime(2024, 1, 1, 8, tzinfo=datetime.timezone.utc),
    "2024-01-01T10:00:00+02:00",
    id="aware-datetime-in-another-offset",
)


def _decimal_reads_back() -> bool:
    """Whether this Django reads back a ``DecimalField`` without ``decimal_places``."""
    return django.VERSION >= (6, 1)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("stored", "spelled"),
    [
        *(
            pytest.param(
                *case.values,
                id=case.id,
                marks=pytest.mark.skipif(
                    connection.vendor != "sqlite" or not _decimal_reads_back(),
                    reason="SQLite stores the value it is bound, read back from Django 6.1",
                ),
            )
            for case in _SPELLED_DECIMAL_PAIRS
        ),
        _SPELLED_STAMP_PAIR,
    ],
)
def test_relation_ids_spelling_a_stored_key_differently_link_its_row(
    stored: object,
    spelled: str,
) -> None:
    """A raw-pk FK and M2M id names its row by the key's value, as the ``pk__in`` lookup does.

    The membership check keys the requested ids and the rows it found by the pk column's
    value, so ``2.50`` is the stored ``2.5`` and an aware datetime in a ``+02:00`` offset
    is the row stored in UTC: the write links the row through both relations, never the
    uniform "Invalid id" error.
    """
    _assert_relation_ids_link(stored, spelled)


#: A non-UTC default time zone, so a naive id read in UTC would name another instant.
_NAIVE_ZONE = "America/New_York"


@pytest.mark.django_db(transaction=True)
def test_relation_ids_spelling_a_datetime_key_naively_link_the_row_at_that_wall_clock() -> None:
    """A naive datetime FK and M2M id names the row at its wall clock in ``TIME_ZONE``.

    The id is made aware in the default zone, as Django's lookup binds it, without the
    naive-datetime warning, so the membership check keys it as the aware row it found
    and the write links that row through both relations.
    """
    stored = datetime.datetime(2024, 1, 1, 8, tzinfo=zoneinfo.ZoneInfo(_NAIVE_ZONE))
    with override_settings(TIME_ZONE=_NAIVE_ZONE):
        _assert_relation_ids_link(stored, "2024-01-01T08:00:00")


def _assert_relation_ids_link(stored: object, spelled: str) -> None:
    """Create an owner naming the ``stored`` key's row as ``spelled`` through its FK and M2M."""
    is_decimal = isinstance(stored, Decimal)
    prefix = "decimal" if is_decimal else "stamp"
    _, owner_model = _spelled_key_models(stored)
    with _spelled_key_tables(stored):
        result = _spelled_key_schema(stored).execute_sync(
            f"mutation($d: {owner_model.__name__}Input!) "
            "{ createSpelledKeyOwner(data: $d) { errors { field messages } } }",
            variable_values={
                "d": {
                    "name": "owner",
                    f"{prefix}TargetId": spelled,
                    f"{prefix}Targets": [spelled],
                },
            },
        )
        assert result.errors is None, result.errors
        assert result.data == {"createSpelledKeyOwner": {"errors": []}}
        owner = owner_model._default_manager.get(name="owner")
        assert read_attr(owner, f"{prefix}_target_id") == stored
        if isinstance(owner, SpelledDecimalOwner):
            linked = [pk_of(row) for row in owner.decimal_targets.all()]
        else:
            assert isinstance(owner, SpelledStampOwner)
            linked = [pk_of(row) for row in owner.stamp_targets.all()]
        assert linked == [stored]


class NonNegativeDecimalField(models.DecimalField[object, object]):
    """A project ``DecimalField`` whose ``default_validators`` refuse a negative value."""

    default_validators = [MinValueValidator(0)]


class CentsDecimalField(models.DecimalField[object, object]):
    """A project ``DecimalField`` whose ``to_python`` rounds to cents: the value its save binds."""

    @override
    def to_python(self, value: object) -> object:
        number = object_result(super().to_python, value)
        return number.quantize(Decimal("0.01")) if isinstance(number, Decimal) else number


class UnboundedAmount(models.Model):
    """Decimal columns a write can carry past PostgreSQL ``numeric``'s format.

    ``amount`` and the nullable ``spare`` have no ``max_digits`` (Django's unconstrained
    ``numeric``, from 6.1), so their ``DecimalValidator`` refuses only a value that is not
    finite; ``priced`` is bounded, and its validator counts no digit for a zero's
    positive exponent. ``capped`` (a ``validators=`` entry) and ``floored`` (a field
    subclass's ``default_validators``) carry a project validator besides, and ``rounded``
    a field subclass whose ``to_python`` rounds to cents.
    """

    amount: models.DecimalField[str | float | Decimal | Combinable, Decimal] = models.DecimalField(
        max_digits=None,
        decimal_places=None,
    )
    spare: models.DecimalField[str | float | Decimal | Combinable | None, Decimal | None] = (
        models.DecimalField(max_digits=None, decimal_places=None, null=True, blank=True)
    )
    priced: models.DecimalField[str | float | Decimal | Combinable | None, Decimal | None] = (
        models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    )
    capped: models.DecimalField[_DecimalSet | None, Decimal | None] = models.DecimalField(
        max_digits=None,
        decimal_places=None,
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)],
    )
    floored: NonNegativeDecimalField = NonNegativeDecimalField(
        max_digits=None,
        decimal_places=None,
        null=True,
        blank=True,
    )
    rounded: CentsDecimalField = CentsDecimalField(
        max_digits=None,
        decimal_places=None,
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "mutations_unbounded_amount"


#: A column of ``UnboundedAmount`` and a spelling its validator passes that ``numeric``
#: refuses: past the integer digits, the fraction digits, or a zero's written exponent.
_PAST_NUMERIC = [
    pytest.param("amount", "1e1000000", id="huge-exponent"),
    pytest.param("amount", "-1e1000000", id="negative-huge-exponent"),
    pytest.param("amount", "1e-1000000", id="tiny-exponent"),
    pytest.param("amount", "1E+131072", id="131073-integer-digits"),
    pytest.param("amount", "0E-16384", id="zero-16384-fraction-digits"),
    pytest.param("spare", "1e1000000", id="nullable-huge-exponent"),
    pytest.param("priced", "0E+1073741824", id="bounded-zero-past-exponent-limit"),
]

_REQUIRES_UNBOUNDED_DECIMAL = pytest.mark.skipif(
    not _decimal_reads_back(),
    reason="a DecimalField without max_digits is read back from Django 6.1",
)


def _write_amount(operation: str, data: dict[str, object], pk: object = None) -> object:
    """Run the model flavor's ``operation`` on ``UnboundedAmount`` with ``data``; its payload."""

    class UnboundedAmountT(DjangoType):
        class Meta:
            model = UnboundedAmount
            fields = (
                "id",
                "amount",
                "spare",
                "priced",
                "capped",
                "floored",
                "rounded",
            )
            primary = True

    class CreateUnboundedAmount(DjangoMutation):
        class Meta:
            model = UnboundedAmount
            operation = "create"
            fields = (
                "amount",
                "spare",
                "priced",
                "capped",
                "floored",
                "rounded",
            )
            permission_classes = [_AllowAll]

    class UpdateUnboundedAmount(DjangoMutation):
        class Meta:
            model = UnboundedAmount
            operation = "update"
            fields = (
                "amount",
                "spare",
                "priced",
                "capped",
                "floored",
                "rounded",
            )
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_unbounded_amount = DjangoMutationField(CreateUnboundedAmount)
        update_unbounded_amount = DjangoMutationField(UpdateUnboundedAmount)

    finalize_django_types()
    del UnboundedAmountT
    selection = "{ result { amount spare priced } errors { field messages codes } }"
    if operation == "create":
        document = (
            "mutation($d: UnboundedAmountInput!) "
            f"{{ createUnboundedAmount(data: $d) {selection} }}"
        )
        variables: dict[str, object] = {"d": data}
    else:
        document = (
            "mutation($id: ID!, $d: UnboundedAmountPartialInput!) "
            f"{{ updateUnboundedAmount(id: $id, data: $d) {selection} }}"
        )
        variables = {"id": str(pk), "d": data}
    result = _schema(Mutation).execute_sync(document, variable_values=variables)
    assert result.errors is None, result.errors
    assert is_object_dict(result.data), result.data
    return result.data[f"{operation}UnboundedAmount"]


def _stored_amounts() -> list[tuple[Decimal, Decimal | None, Decimal | None]]:
    """Every ``UnboundedAmount`` row's three decimals."""
    return [(row.amount, row.spare, row.priced) for row in UnboundedAmount.objects.order_by("pk")]


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(("column", "wire"), _PAST_NUMERIC)
def test_model_write_refuses_a_decimal_past_postgresql_numeric(
    operation: str,
    column: str,
    wire: str,
) -> None:
    """A decimal its column's validator passes but PostgreSQL cannot bind is the field's error.

    ``full_clean`` passes it and PostgreSQL's ``numeric_in`` refuses it at the save, a
    ``DataError`` no save mapper owns. The write decode answers the field's ``invalid``
    error instead, with nothing written.
    """
    with numeric_refusing_postgresql(UnboundedAmount):
        pk = (
            saved_pk(UnboundedAmount.objects.create(amount=Decimal(7)))
            if operation == "update"
            else None
        )
        before = _stored_amounts()
        payload = _write_amount(operation, {"amount": "7", column: wire}, pk)

        assert payload == {
            "result": None,
            "errors": [
                {
                    "field": column,
                    "messages": ["Enter a value the database can represent."],
                    "codes": ["invalid"],
                },
            ],
        }
        assert _stored_amounts() == before


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("column", ["amount", "spare", "priced"])
def test_model_write_stores_a_decimal_within_postgresql_numeric(
    operation: str,
    column: str,
) -> None:
    """A decimal PostgreSQL's ``numeric`` holds is written through the same stand-in."""
    with numeric_refusing_postgresql(UnboundedAmount):
        pk = (
            saved_pk(UnboundedAmount.objects.create(amount=Decimal(7)))
            if operation == "update"
            else None
        )
        payload = _write_amount(operation, {"amount": "7", column: "12.5"}, pk)

        assert is_object_dict(payload), payload
        assert payload["errors"] == []
        assert read_attr(UnboundedAmount.objects.get(), column) == Decimal("12.5")


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_model_write_leaves_a_decimal_its_validator_refuses_to_full_clean(operation: str) -> None:
    """A decimal past ``numeric``'s format the column's ``DecimalValidator`` refuses keeps its error.

    ``priced`` holds 10 digits, so ``1e1000000`` is ``full_clean()``'s ``max_digits``
    error, never the storability refusal, though PostgreSQL could not bind it either.
    """
    with numeric_refusing_postgresql(UnboundedAmount):
        pk = (
            saved_pk(UnboundedAmount.objects.create(amount=Decimal(7)))
            if operation == "update"
            else None
        )
        before = _stored_amounts()
        payload = _write_amount(operation, {"amount": "7", "priced": "1e1000000"}, pk)

        assert payload == {
            "result": None,
            "errors": [
                {
                    "field": "priced",
                    "messages": ["Ensure that there are no more than 10 digits in total."],
                    "codes": ["max_digits"],
                },
            ],
        }
        assert _stored_amounts() == before


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    (
        "column",
        "wire",
        "message",
        "code",
    ),
    [
        pytest.param(
            "capped",
            "1e1000000",
            "Ensure this value is less than or equal to 100.",
            "max_value",
            id="validators-entry",
        ),
        pytest.param(
            "floored",
            "-1e1000000",
            "Ensure this value is greater than or equal to 0.",
            "min_value",
            id="subclass-default-validators",
        ),
    ],
)
def test_model_write_leaves_a_decimal_a_project_validator_refuses_to_it(
    operation: str,
    column: str,
    wire: str,
    message: str,
    code: str,
) -> None:
    """A decimal past ``numeric``'s format the column's own validators refuse keeps their error.

    The storability rule reads a decimal only once every validator ``full_clean()`` runs
    for the column accepts it, a ``validators=`` entry and a field subclass's
    ``default_validators`` included, so the project validator's own error answers.
    """
    with numeric_refusing_postgresql(UnboundedAmount):
        pk = (
            saved_pk(UnboundedAmount.objects.create(amount=Decimal(7)))
            if operation == "update"
            else None
        )
        before = _stored_amounts()
        payload = _write_amount(operation, {"amount": "7", column: wire}, pk)

        assert payload == {
            "result": None,
            "errors": [{"field": column, "messages": [message], "codes": [code]}],
        }
        assert _stored_amounts() == before


_ROUNDED_TO_ZERO = [
    pytest.param("1e-1000000", id="tiny-exponent"),
    pytest.param("0." + "0" * 16383 + "5", id="16384-fraction-digits"),
]


@_REQUIRES_UNBOUNDED_DECIMAL
@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("wire", _ROUNDED_TO_ZERO)
def test_model_write_holds_the_decimal_its_column_to_python_gives(
    operation: str,
    wire: str,
) -> None:
    """A spelling ``numeric`` refuses that the column's ``to_python`` rounds to a cent is stored.

    The save binds the value ``to_python`` gives (``0.00``), which ``numeric`` holds, so the
    write stores it rather than refusing the spelling as sent.
    """
    with numeric_refusing_postgresql(UnboundedAmount):
        pk = (
            saved_pk(UnboundedAmount.objects.create(amount=Decimal(7)))
            if operation == "update"
            else None
        )
        payload = _write_amount(operation, {"amount": "7", "rounded": wire}, pk)

        assert is_object_dict(payload), payload
        assert payload["errors"] == []
        assert UnboundedAmount.objects.get().rounded == Decimal(0)


class CleanedStamp(models.Model):
    """A model ``clean()`` rewriting a column the write stores, chosen by the ``label`` sent.

    ``day-instant`` replaces the unique ``day`` with the aware midnight UTC of its date, which
    Django stores as its date in the default time zone; ``noted-instant`` sets ``noted``, a
    column the mutations below never provide; ``day-refused`` does what ``day-instant`` does
    and refuses ``day`` itself. ``span`` is a ``DurationField``, which a project maps to a text
    scalar Django's own ``clean_fields()`` parses.
    """

    label: models.TextField[str | Combinable, str] = models.TextField()
    day: models.DateField[str | datetime.date | Combinable | None, datetime.date | None] = (
        models.DateField(null=True, blank=True, unique=True)
    )
    noted: models.DateField[str | datetime.date | Combinable | None, datetime.date | None] = (
        models.DateField(null=True, blank=True)
    )
    span: models.DurationField[object, datetime.timedelta | None] = models.DurationField(
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "products"
        managed = False
        db_table = "mutations_cleaned_stamp"

    @override
    def clean(self) -> None:
        """Rewrite ``day`` or ``noted`` as ``label`` names (the class docstring)."""
        if self.label == "noted-instant":
            self.noted = datetime.datetime(1, 1, 1, 0, 30, tzinfo=datetime.timezone.utc)
        elif self.label in {"day-instant", "day-refused"} and self.day is not None:
            midnight = datetime.datetime.combine(self.day, datetime.time.min)
            self.day = midnight.replace(tzinfo=datetime.timezone.utc)
            if self.label == "day-refused":
                raise ValidationError(
                    {"day": ValidationError("Refused by clean().", code="refused")},
                )


def _create_cleaned_stamp(data: dict[str, object], written: str) -> ExecutionResult:
    """Run a model-flavor create of ``CleanedStamp``'s ``label`` and ``written`` columns."""

    class CleanedStampT(DjangoType):
        class Meta:
            model = CleanedStamp
            fields = ("label", written)
            primary = True

    class CreateCleanedStamp(DjangoMutation):
        class Meta:
            model = CleanedStamp
            operation = "create"
            fields = ("label", written)
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_cleaned_stamp = DjangoMutationField(CreateCleanedStamp)

    finalize_django_types()
    del CleanedStampT
    input_type = f"CleanedStamp{''.join(sorted(('Label', written.title())))}Input"
    return _schema(Mutation).execute_sync(
        f"mutation($d: {input_type}!) {{ createCleanedStamp(data: $d) "
        "{ result { label } errors { field messages codes path } } }",
        variable_values={"d": data},
    )


def _stored_cleaned_stamps() -> list[tuple[object, ...]]:
    """Every ``CleanedStamp`` row's label, day and span."""
    return list(CleanedStamp._base_manager.order_by("pk").values_list("label", "day", "span"))


def _unstorable_errors(field: str) -> list[dict[str, object]]:
    """The ``invalid`` envelope a value the database cannot store answers under ``field``."""
    return [
        {
            "field": field,
            "messages": ["Enter a value the database can represent."],
            "codes": ["invalid"],
            "path": [field],
        },
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "label",
        "day",
        "errors",
        "stored_day",
    ),
    [
        pytest.param(
            "day-instant",
            "0001-01-01",
            _unstorable_errors("day"),
            None,
            id="year-one-instant",
        ),
        pytest.param(
            "day-instant",
            "2021-06-15",
            [],
            datetime.date(2021, 6, 14),
            id="in-range-instant",
        ),
        pytest.param(
            "day-refused",
            "0001-01-01",
            [
                {
                    "field": "day",
                    "messages": ["Refused by clean()."],
                    "codes": ["refused"],
                    "path": ["day"],
                },
            ],
            None,
            id="refused-by-clean",
        ),
    ],
)
@override_settings(TIME_ZONE="America/New_York")
def test_model_clean_datetime_the_unique_date_column_cannot_store_is_the_field_error(
    label: str,
    day: str,
    errors: list[dict[str, object]],
    stored_day: datetime.date | None,
) -> None:
    """A model ``clean()``'s aware datetime whose date leaves years 1..9999 is refused.

    ``clean()`` runs after the decode held the date sent to the storability rule, and
    leaves ``day`` the aware midnight UTC of ``0001-01-01``, whose date under
    ``America/New_York`` falls in year 0: Django's own conversion of it would raise
    ``OverflowError`` binding the unique column's uniqueness query, then the save. The model
    flavor holds each provided column the instance then carries to the same rule before
    that query: the ``day`` ``invalid`` error with nothing written. A column ``clean()``
    already refused keeps its own error alone, and an in-range day is stored as its date in
    the default time zone.
    """
    with _tables(CleanedStamp):
        result = _create_cleaned_stamp({"label": label, "day": day}, "day")
        stored = _stored_cleaned_stamps()

    assert result.errors is None, result.errors
    assert _json_at(result.data, "createCleanedStamp", "errors") == errors
    assert stored == ([] if stored_day is None else [(label, stored_day, None)])


@pytest.mark.django_db(transaction=True)
@override_settings(TIME_ZONE="America/New_York")
def test_model_clean_value_on_a_column_the_input_does_not_provide_stays_the_application_s(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A model ``clean()`` setting a value on a column the input does not provide fails the save.

    ``noted`` is no input field, so ``clean()``'s aware datetime there is the application's
    own value: the storability rule holds only the provided columns, and Django's conversion
    at the save raises the ``OverflowError`` as the request's error, nothing written.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    with _tables(CleanedStamp):
        result = _create_cleaned_stamp({"label": "noted-instant"}, "day")
        stored = _stored_cleaned_stamps()

    assert result.errors is not None
    assert [error.message for error in result.errors] == ["An unexpected error occurred."]
    logged = [
        record.exc_info[1]
        for record in caplog.records
        if record.name == "django_strawberry_framework" and record.exc_info is not None
    ]
    assert [type(error) for error in logged] == [OverflowError], logged
    assert stored == []


@pytest.mark.skipif(
    connection.vendor != "sqlite",
    reason="SQLite binds a duration as its microsecond count, an integer of 64 bits",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("span", "errors", "stored"),
    [
        pytest.param(
            "106751992 00:00:00",
            _unstorable_errors("span"),
            [],
            id="past-64-bits",
        ),
        pytest.param(
            "1 00:00:00",
            [],
            [("spanned", None, datetime.timedelta(days=1))],
            id="in-range",
        ),
    ],
)
def test_text_scalar_duration_parsed_past_the_backend_integer_is_the_field_error(
    monkeypatch: pytest.MonkeyPatch,
    span: str,
    errors: list[dict[str, object]],
    stored: list[tuple[object, ...]],
) -> None:
    """A ``DurationField`` a project maps to text holds the duration ``clean_fields()`` parses.

    The decode holds the text sent, which the storability rule cannot read as a duration;
    ``clean_fields()`` writes back the ``timedelta`` it parses, which SQLite cannot bind past
    64 bits of microseconds. The model flavor holds the parsed value to the rule: the
    ``span`` ``invalid`` error with nothing written, while a one-day duration is stored.
    """
    monkeypatch.setitem(SCALAR_MAP, models.DurationField, str)
    with _tables(CleanedStamp):
        result = _create_cleaned_stamp({"label": "spanned", "span": span}, "span")
        written = _stored_cleaned_stamps()

    assert result.errors is None, result.errors
    assert _json_at(result.data, "createCleanedStamp", "errors") == errors
    assert written == stored
