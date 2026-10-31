"""Live HTTP tests for model-mutation identities, relation decoding and write-error names."""

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from functools import wraps

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.products.services import seed_data
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Model, QuerySet
from django.db.models.signals import m2m_changed, pre_save
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_at, json_list
from strawberry import relay
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.name_converter import NameConverter
from typing_extensions import override

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    ResourcePolicy,
    finalize_django_types,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.views import DjangoGraphQLView
from tests._catalog_data import categories_from_seed

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-model-flows/", _graphql_view)]


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _schema(
    mutation: type[object],
    *,
    config: StrawberryConfig | None = None,
    resource_policy: ResourcePolicy | None = None,
) -> DjangoSchema:
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_Query,
        mutation=mutation,
        config=config,
        resource_policy=resource_policy,
        extensions=[lambda: optimizer],
    )


def _post(
    schema: DjangoSchema,
    document: str,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    """Decode the entire HTTP envelope and restore this mount even when the request raises."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(document, variables=variables, url="/graphql-model-flows/")
    finally:
        _CURRENT["schema"] = None


def _error(field: str) -> JSONObject:
    """The independently stated relation-refusal wire contract."""
    return {
        "field": field,
        "messages": [f"Invalid id for relation {field!r}."],
        "codes": ["invalid"],
        "path": field.split("."),
    }


def _category_node_schema() -> tuple[DjangoSchema, type[DjangoType]]:
    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")
            interfaces = (relay.Node,)

    class UpdateCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "update"
            permission_classes = []

    class DeleteCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "delete"
            permission_classes = []

    @strawberry.type
    class Mutation:
        update_category = DjangoMutationField(UpdateCategory)
        delete_category = DjangoMutationField(DeleteCategory)

    finalize_django_types()
    return _schema(Mutation), CategoryNode


def _node_id_decoy_pair() -> tuple[product_models.Category, product_models.Category]:
    decoy, target = categories_from_seed(("decoy", False), ("target", False))
    product_models.Category.objects.filter(pk=decoy.pk).update(description="decoy-untouched")
    product_models.Category.objects.filter(pk=target.pk).update(
        name=str(decoy.pk),
        description="before",
    )
    decoy.refresh_from_db()
    target.refresh_from_db()
    assert target.pk != decoy.pk
    assert target.name == str(decoy.pk)
    return decoy, target


@pytest.mark.django_db
def test_custom_node_id_update_uses_the_named_row_and_preserves_the_pk_decoy() -> None:
    """A custom Relay id updates the name-matched row and emits that same id again."""
    seed_data(0)
    decoy, target = _node_id_decoy_pair()
    schema, node_type = _category_node_schema()
    gid = global_id_for(node_type, target.name)
    payload = _post(
        schema,
        "mutation($id: ID!, $d: CategoryPartialInput!){ updateCategory(id:$id, data:$d){ "
        "node{ id description } errors{ field messages } } }",
        {"id": gid, "d": {"description": "after"}},
    )
    assert payload == {
        "data": {"updateCategory": {"node": {"id": gid, "description": "after"}, "errors": []}},
    }
    target.refresh_from_db()
    decoy.refresh_from_db()
    assert (target.description, decoy.description) == ("after", "decoy-untouched")


@pytest.mark.django_db
def test_custom_node_id_delete_removes_the_named_row_and_preserves_the_pk_decoy() -> None:
    """A custom Relay id deletes the name-matched row and keeps its id in the snapshot."""
    seed_data(0)
    decoy, target = _node_id_decoy_pair()
    schema, node_type = _category_node_schema()
    gid = global_id_for(node_type, target.name)
    payload = _post(
        schema,
        "mutation($id: ID!){ deleteCategory(id:$id){ node{ id } errors{ field messages } } }",
        {"id": gid},
    )
    assert payload == {"data": {"deleteCategory": {"node": {"id": gid}, "errors": []}}}
    assert not product_models.Category.objects.filter(pk=target.pk).exists()
    assert list(product_models.Category.objects.values_list("pk", "description")) == [
        (decoy.pk, "decoy-untouched"),
    ]


@strawberry.input
class _CategoryRelationOverride:
    category_id: strawberry.ID = strawberry.field(description="custom category ref")


@strawberry.input
class _RenamedItemName:
    name: str = strawberry.field(name="itemName")


def _item_schema(
    *,
    input_override: type[object] | None = None,
    hide_private: bool = False,
) -> tuple[DjangoSchema, type[DjangoType]]:
    class CategoryNode(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[product_models.Category],
            info: strawberry.Info,
        ) -> QuerySet[product_models.Category]:
            del cls, info
            return queryset.filter(is_private=False) if hide_private else queryset

    class ItemNode(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            interfaces = (relay.Node,)

    assert registry.get(product_models.Item) is ItemNode

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = []
            if input_override is not None:
                input_class = input_override

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    return _schema(Mutation), CategoryNode


@pytest.mark.django_db
@pytest.mark.parametrize("visibility", ["visible", "hidden", "missing"])
def test_relation_input_override_keeps_visibility_and_existence_validation(
    visibility: str,
) -> None:
    """A consumer input override still resolves the category through its declared target hook."""
    seed_data(0)
    (category,) = categories_from_seed(("Override category", visibility == "hidden"))
    schema, category_type = _item_schema(
        input_override=_CategoryRelationOverride,
        hide_private=True,
    )
    assert category.pk is not None
    pk = category.pk + 1000 if visibility == "missing" else category.pk
    payload = _post(
        schema,
        "mutation($d: ItemInput!){ createItem(data:$d){ "
        "node{ name category{ name } } errors{ field messages codes path } } }",
        {"d": {"name": "Override item", "categoryId": global_id_for(category_type, pk)}},
    )
    expected: JSONObject = (
        {"node": {"name": "Override item", "category": {"name": category.name}}, "errors": []}
        if visibility == "visible"
        else {"node": None, "errors": [_error("categoryId")]}
    )
    assert payload == {"data": {"createItem": expected}}
    assert list(product_models.Item.objects.values_list("name", "category_id")) == (
        [("Override item", category.pk)] if visibility == "visible" else []
    )


def _book_schema(
    *,
    operation: str = "create",
    raw_genres: bool = False,
    register_targets: bool = True,
    hide_secret: bool = False,
) -> tuple[DjangoSchema, type[DjangoType], type[DjangoType] | None, type[DjangoType] | None]:
    genre_type = shelf_type = None
    if register_targets:

        class GenreNode(DjangoType):
            class Meta:
                model = library_models.Genre
                fields = ("id", "name")
                interfaces = () if raw_genres else (relay.Node,)

            @classmethod
            @override
            def get_queryset(
                cls,
                queryset: QuerySet[library_models.Genre],
                info: strawberry.Info,
            ) -> QuerySet[library_models.Genre]:
                del cls, info
                return queryset.exclude(name="Secret") if hide_secret else queryset

        class ShelfNode(DjangoType):
            class Meta:
                model = library_models.Shelf
                fields = ("id", "code")
                interfaces = (relay.Node,)

        genre_type, shelf_type = GenreNode, ShelfNode

    class BookNode(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)

    selected_operation = operation

    class WriteBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = selected_operation
            permission_classes = []
            if register_targets and not raw_genres:
                fields = ("title", "shelf", "genres")

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(WriteBook)

    finalize_django_types()
    return _schema(Mutation), BookNode, genre_type, shelf_type


def _shelf() -> library_models.Shelf:
    branch = library_models.Branch.objects.create(name="Main")
    return library_models.Shelf.objects.create(code="S1", branch=branch)


@pytest.mark.django_db
@pytest.mark.parametrize("member", ["visible", "hidden", "mixed"])
def test_m2m_relay_members_are_checked_against_the_target_visibility(member: str) -> None:
    """One hidden id refuses the entire client set, while a visible set is attachable."""
    shelf = _shelf()
    visible = library_models.Genre.objects.create(name="Visible")
    hidden = library_models.Genre.objects.create(name="Secret")
    schema, _, genre_type, shelf_type = _book_schema(hide_secret=True)
    assert genre_type is not None
    assert shelf_type is not None
    members = {"visible": [visible], "hidden": [hidden], "mixed": [visible, hidden]}[member]
    payload = _post(
        schema,
        "mutation($d: BookGenresShelfTitleInput!){ write(data:$d){ "
        "node{ title } errors{ field messages codes path } } }",
        {
            "d": {
                "title": "Requested",
                "shelfId": global_id_for(shelf_type, shelf.pk),
                "genres": [global_id_for(genre_type, row.pk) for row in members],
            },
        },
    )
    assert payload == {
        "data": {
            "write": (
                {"node": {"title": "Requested"}, "errors": []}
                if member == "visible"
                else {"node": None, "errors": [_error("genres")]}
            ),
        },
    }
    assert list(library_models.Book.objects.values_list("title", flat=True)) == (
        ["Requested"] if member == "visible" else []
    )
    assert list(library_models.Book.genres.through.objects.values_list("genre_id", flat=True)) == (
        [visible.pk] if member == "visible" else []
    )


@contextmanager
def _refuse_genres() -> Generator[None, None, None]:
    def refuse(action: str, **kwargs: object) -> None:
        del kwargs
        if action == "post_add":
            raise ValidationError(
                {
                    "genres": ValidationError("Genres are frozen.", code="frozen"),
                    "shelf_id": "Shelf rejected with the genres.",
                },
            )

    through = library_models.Book.genres.through
    m2m_changed.connect(refuse, sender=through, weak=False)
    try:
        yield
    finally:
        m2m_changed.disconnect(refuse, sender=through)


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["create", "update"])
def test_m2m_signal_refusal_rekeys_errors_and_rolls_back_row_and_members(operation: str) -> None:
    """A post-add refusal rolls back the row write and restores an update's prior member set."""
    shelf = _shelf()
    stored = library_models.Genre.objects.create(name="Stored")
    frozen = library_models.Genre.objects.create(name="Frozen")
    schema, book_type, genre_type, shelf_type = _book_schema(operation=operation)
    assert genre_type is not None
    assert shelf_type is not None
    variables: dict[str, object]
    if operation == "create":
        book = None
        query = (
            "mutation($d: BookGenresShelfTitleInput!){ write(data:$d){ node{ id } errors{ "
            "field messages codes path } } }"
        )
        variables = {
            "d": {
                "title": "Refused",
                "shelfId": global_id_for(shelf_type, shelf.pk),
                "genres": [global_id_for(genre_type, frozen.pk)],
            },
        }
    else:
        book = library_models.Book.objects.create(title="Kept", shelf=shelf)
        book.genres.set([stored])
        query = (
            "mutation($id: ID!, $d: BookGenresShelfTitlePartialInput!){ write(id:$id, "
            "data:$d){ node{ id } errors{ field messages codes path } } }"
        )
        variables = {
            "id": global_id_for(book_type, book.pk),
            "d": {"title": "Refused", "genres": [global_id_for(genre_type, frozen.pk)]},
        }
    with _refuse_genres():
        payload = _post(schema, query, variables)
    assert payload == {
        "data": {
            "write": {
                "node": None,
                "errors": [
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
                ],
            },
        },
    }
    assert list(library_models.Book.objects.values_list("title", flat=True)) == (
        [] if book is None else ["Kept"]
    )
    pairs = set(library_models.Book.genres.through.objects.values_list("book_id", "genre_id"))
    assert pairs == (set() if book is None else {(book.pk, stored.pk)})


@contextmanager
def _refuse_save(model: type[Model], field: str) -> Generator[None, None, None]:
    def refuse(**kwargs: object) -> None:
        del kwargs
        raise ValidationError({field: ValidationError("Refused at save.", code="refused")})

    pre_save.connect(refuse, sender=model, weak=False)
    try:
        yield
    finally:
        pre_save.disconnect(refuse, sender=model)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("error_key", "field", "path"),
    [
        pytest.param("name", "itemName", ["itemName"], id="renamed-input"),
        pytest.param("category", "categoryId", ["categoryId"], id="relation-name"),
        pytest.param("category_id", "categoryId", ["categoryId"], id="relation-attname"),
        pytest.param("is_private", "isPrivate", ["isPrivate"], id="multi-word"),
        pytest.param("code", "code", ["code"], id="unknown-model-field"),
        pytest.param(
            "shelves.1.code",
            "shelves.1.code",
            ["shelves", "1", "code"],
            id="dotted-verbatim",
        ),
    ],
)
def test_model_save_errors_follow_the_model_to_input_wire_key_map(
    error_key: str,
    field: str,
    path: list[str],
) -> None:
    """Save-time names resolve through model fields, explicit input names and relation attnames."""
    seed_data(0)
    (category,) = categories_from_seed(("Save category", False))
    schema, category_type = _item_schema(input_override=_RenamedItemName)
    with _refuse_save(product_models.Item, error_key):
        payload = _post(
            schema,
            (
                "mutation($d: ItemInput!){ createItem(data:$d){ node{ id } errors{ field "
                "messages codes path } } }"
            ),
            {
                "d": {
                    "itemName": "Refused",
                    "categoryId": global_id_for(category_type, category.pk),
                },
            },
        )
    assert payload == {
        "data": {
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
        },
    }
    assert not product_models.Item.objects.exists()


class _UnderscorePrefixConverter(NameConverter):
    @override
    def apply_naming_config(self, name: str) -> str:
        base = super().apply_naming_config(name)
        return f"n_{base}" if "_" in name else base


@strawberry.input
class _EditionUnnamedFields:
    isbn_13: str
    isbn_10: str | None = strawberry.field(default=UNSET)
    publisher_2_id: int | None = strawberry.field(default=UNSET)


@strawberry.input
class _PrintingUnnamedBoundWith:
    bound_with: list[str] | None = strawberry.field(default=UNSET)


def _config(name: str) -> tuple[StrawberryConfig, tuple[str, str, str], str]:
    if name == "default":
        return StrawberryConfig(), ("isbn13", "isbn10", "publisher2Id"), "boundWith"
    if name == "snake":
        return (
            StrawberryConfig(auto_camel_case=False),
            ("isbn_13", "isbn_10", "publisher_2_id"),
            "bound_with",
        )
    assert name == "custom"
    return (
        StrawberryConfig(name_converter=_UnderscorePrefixConverter()),
        ("n_isbn13", "n_isbn10", "n_publisher2Id"),
        "n_boundWith",
    )


def _edition_schema(config: StrawberryConfig) -> DjangoSchema:
    class PublisherNode(DjangoType):
        class Meta:
            model = library_models.Publisher
            fields = ("id", "name")

    class EditionNode(DjangoType):
        class Meta:
            model = library_models.Edition
            fields = ("isbn_13",)

    assert registry.get(library_models.Publisher) is PublisherNode
    assert registry.get(library_models.Edition) is EditionNode

    class CreateEdition(DjangoMutation):
        class Meta:
            model = library_models.Edition
            operation = "create"
            input_class = _EditionUnnamedFields
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(CreateEdition)

    finalize_django_types()
    return _schema(Mutation, config=config)


@pytest.mark.django_db
@pytest.mark.parametrize("naming", ["default", "snake", "custom"])
@pytest.mark.parametrize(
    "refusal",
    [
        "unique",
        "null",
        "relation",
        "save",
        "valid",
    ],
)
def test_unnamed_consumer_fields_key_each_refusal_to_the_executing_schema(
    naming: str,
    refusal: str,
) -> None:
    """Each independent decode, validation and save refusal uses its schema's published input name."""
    publisher = library_models.Publisher.objects.create(name="P-Unnamed", house_code="PU")
    library_models.Edition.objects.create(isbn_13="978-dup", publisher=publisher)
    config, published, _ = _config(naming)
    schema = _edition_schema(config)
    isbn_13, isbn_10, publisher_2_id = published
    introspection = _post(schema, '{ __type(name: "EditionInput") { inputFields { name } } }')
    assert {
        json_at(field, "name")
        for field in json_list(introspection, "data", "__type", "inputFields")
    } == {*published, "imprint", "publisherId"}
    data, field, code = {
        "unique": ({isbn_13: "978-dup"}, isbn_13, "unique"),
        "null": ({isbn_13: "978-null", isbn_10: None}, isbn_10, "null"),
        "relation": ({isbn_13: "978-rel", publisher_2_id: 999999}, publisher_2_id, "invalid"),
        "save": ({isbn_13: "978-save", isbn_10: "0-00"}, isbn_10, "refused"),
        "valid": (
            {isbn_13: "978-valid", isbn_10: "0-00", publisher_2_id: publisher.pk},
            isbn_10,
            "",
        ),
    }[refusal]
    document = (
        "mutation($d: EditionInput!){ write(data:$d){ result{ __typename } errors{ field "
        "path codes } } }"
    )
    variables = {"d": {"publisherId": publisher.pk, **data}}
    if refusal == "save":
        with _refuse_save(library_models.Edition, "isbn_10"):
            payload = _post(schema, document, variables)
    else:
        payload = _post(schema, document, variables)
    if refusal == "valid":
        assert payload == {
            "data": {"write": {"result": {"__typename": "EditionNode"}, "errors": []}},
        }
        written = library_models.Edition.objects.get(pk="978-valid")
        assert (
            written.isbn_10,
            read_attr(written, "publisher_id"),
            read_attr(written, "publisher_2_id"),
        ) == ("0-00", publisher.pk, publisher.pk)
        expected_keys = ["978-dup", "978-valid"]
    else:
        assert payload == {
            "data": {
                "write": {
                    "result": None,
                    "errors": [{"field": field, "path": [field], "codes": [code]}],
                },
            },
        }
        expected_keys = ["978-dup"]
    assert (
        list(library_models.Edition.objects.order_by("pk").values_list("isbn_13", flat=True))
        == expected_keys
    )


def _printing_schema(config: StrawberryConfig) -> DjangoSchema:
    class EditionNode(DjangoType):
        class Meta:
            model = library_models.Edition
            fields = ("isbn_13",)

    class PrintingNode(DjangoType):
        class Meta:
            model = library_models.Printing
            fields = ("id",)

    assert registry.get(library_models.Edition) is EditionNode
    assert registry.get(library_models.Printing) is PrintingNode

    class CreatePrinting(DjangoMutation):
        class Meta:
            model = library_models.Printing
            operation = "create"
            input_class = _PrintingUnnamedBoundWith
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(CreatePrinting)

    finalize_django_types()
    return _schema(
        Mutation,
        config=config,
        resource_policy=ResourcePolicy(max_relation_ids_per_mutation=1),
    )


@pytest.mark.django_db
@pytest.mark.parametrize("naming", ["default", "snake", "custom"])
@pytest.mark.parametrize("width", [1, 2], ids=["at-bound", "over-bound"])
def test_unnamed_raw_relation_list_is_charged_before_any_write(naming: str, width: int) -> None:
    """Raw ISBN relation lists keep their relation budget under every naming configuration."""
    publisher = library_models.Publisher.objects.create(name="P-Bound", house_code="PB")
    for isbn in ("978-a", "978-b"):
        library_models.Edition.objects.create(isbn_13=isbn, publisher=publisher)
    config, _, bound_with = _config(naming)
    schema = _printing_schema(config)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            "mutation($d: PrintingInput!){ write(data:$d){ result{ id } errors{ field } } }",
            {"d": {"editionId": "978-a", bound_with: ["978-a", "978-b"][:width]}},
        )
    table = connection.ops.quote_name(library_models.Printing._meta.db_table)
    writes = [
        row["sql"]
        for row in captured
        if row["sql"].lstrip().upper().startswith(("INSERT ", "UPDATE ")) and table in row["sql"]
    ]
    if width == 1:
        written = library_models.Printing.objects.get()
        assert payload == {"data": {"write": {"result": {"id": written.pk}, "errors": []}}}
        assert written.edition_id == "978-a"
        assert list(written.bound_with.values_list("pk", flat=True)) == ["978-a"]
        assert len(writes) == 1, writes
    else:
        assert payload == {
            "data": None,
            "errors": [
                {
                    "message": (
                        "Request exceeds the max_relation_ids_per_mutation resource bound: one mutation "
                        "field carries more relation ids than the policy allows (2 charged, 1 allowed)."
                    ),
                    "extensions": {
                        "code": "RESOURCE_LIMIT_EXCEEDED",
                        "bound": "max_relation_ids_per_mutation",
                        "limit": 1,
                        "charged": 2,
                    },
                },
            ],
        }
        assert writes == [], writes
        assert not library_models.Printing.objects.exists()


@pytest.mark.django_db
def test_raw_pk_m2m_missing_member_preserves_the_stored_set() -> None:
    """A missing raw Genre key refuses the update and leaves the earlier relation set intact."""
    shelf = _shelf()
    book = library_models.Book.objects.create(title="Seeded", shelf=shelf)
    existing = library_models.Genre.objects.create(name="Stored")
    book.genres.set([existing])
    schema, book_type, _, _ = _book_schema(operation="update", raw_genres=True)
    assert existing.pk is not None
    payload = _post(
        schema,
        (
            "mutation($id: ID!, $d: BookPartialInput!){ write(id:$id, data:$d){ node{ id } "
            "errors{ field messages codes path } } }"
        ),
        {"id": global_id_for(book_type, book.pk), "d": {"genres": [existing.pk + 9999]}},
    )
    assert payload == {"data": {"write": {"node": None, "errors": [_error("genres")]}}}
    book.refresh_from_db()
    assert book.title == "Seeded"
    assert list(book.genres.values_list("pk", flat=True)) == [existing.pk]


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["valid", "missing-shelf", "missing-genre"])
def test_unregistered_raw_relations_validate_existence_without_a_type_hook(case: str) -> None:
    """Unregistered targets accept saved raw keys and refuse either missing FK or M2M key."""
    shelf = _shelf()
    genre = library_models.Genre.objects.create(name="Real")
    schema, _, _, _ = _book_schema(register_targets=False)
    assert registry.get(library_models.Shelf) is None
    assert registry.get(library_models.Genre) is None
    assert shelf.pk is not None
    assert genre.pk is not None
    payload = _post(
        schema,
        "mutation($d: BookInput!){ write(data:$d){ node{ title } errors{ field messages codes path } } }",
        {
            "d": {
                "title": "Requested",
                "shelfId": shelf.pk + (9999 if case == "missing-shelf" else 0),
                "genres": [genre.pk + (9999 if case == "missing-genre" else 0)],
            },
        },
    )
    field = "shelfId" if case == "missing-shelf" else "genres"
    expected: JSONObject = (
        {"node": {"title": "Requested"}, "errors": []}
        if case == "valid"
        else {"node": None, "errors": [_error(field)]}
    )
    assert payload == {"data": {"write": expected}}
    assert list(library_models.Book.objects.values_list("title", "shelf_id")) == (
        [("Requested", shelf.pk)] if case == "valid" else []
    )
    assert list(library_models.Book.genres.through.objects.values_list("genre_id", flat=True)) == (
        [genre.pk] if case == "valid" else []
    )


@pytest.mark.django_db
@pytest.mark.parametrize("value_shape", ["invalid", "valid"])
def test_partial_update_validates_a_scalar_column_whose_name_ends_in_id(value_shape: str) -> None:
    """A scalar object_id refuses a negative value and accepts a changed positive value."""
    branch = library_models.Branch.objects.create(name="Scalar connector")
    other = library_models.Branch.objects.create(name="Alternate connector")
    assert other.pk != branch.pk
    tagged = library_models.TaggedItem.objects.create(content_object=branch, tag="alpha")

    class TaggedItemNode(DjangoType):
        class Meta:
            model = library_models.TaggedItem
            fields = ("id", "tag", "object_id")
            interfaces = (relay.Node,)

    class UpdateTaggedItem(DjangoMutation):
        class Meta:
            model = library_models.TaggedItem
            operation = "update"
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(UpdateTaggedItem)

    finalize_django_types()
    schema = _schema(Mutation)
    payload = _post(
        schema,
        (
            "mutation($id: ID!, $d: TaggedItemPartialInput!){ write(id:$id, data:$d){ node{ "
            "tag } errors{ field messages codes path } } }"
        ),
        {
            "id": global_id_for(TaggedItemNode, tagged.pk),
            "d": {"objectId": -5 if value_shape == "invalid" else other.pk},
        },
    )
    if value_shape == "valid":
        assert payload == {"data": {"write": {"node": {"tag": "alpha"}, "errors": []}}}
    else:
        assert payload == {
            "data": {
                "write": {
                    "node": None,
                    "errors": [
                        {
                            "field": "objectId",
                            "messages": ["Ensure this value is greater than or equal to 0."],
                            "codes": ["min_value"],
                            "path": ["objectId"],
                        },
                    ],
                },
            },
        }
    tagged.refresh_from_db()
    assert (tagged.tag, tagged.object_id) == (
        "alpha",
        branch.pk if value_shape == "invalid" else other.pk,
    )
    assert library_models.Branch.objects.get(pk=branch.pk).name == "Scalar connector"
    assert library_models.Branch.objects.get(pk=other.pk).name == "Alternate connector"


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["explicit-null", "omitted"])
def test_explicit_null_on_a_nullable_foreign_key_clears_the_stored_relation(change: str) -> None:
    """A real nullable FK clears on explicit null and stays linked when a scalar update omits it."""
    publisher = library_models.Publisher.objects.create(name="Primary", house_code="PRIMARY")
    other = library_models.Publisher.objects.create(name="Second", house_code="SECOND")
    edition = library_models.Edition.objects.create(
        isbn_13="978-nullable",
        publisher=publisher,
        publisher_2=other,
    )

    class PublisherNode(DjangoType):
        class Meta:
            model = library_models.Publisher
            fields = ("id", "name")

    class EditionNode(DjangoType):
        class Meta:
            model = library_models.Edition
            fields = ("isbn_13", "imprint")

    assert registry.get(library_models.Publisher) is PublisherNode
    assert registry.get(library_models.Edition) is EditionNode

    class UpdateEdition(DjangoMutation):
        class Meta:
            model = library_models.Edition
            operation = "update"
            fields = ("imprint", "publisher_2")
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(UpdateEdition)

    finalize_django_types()
    schema = _schema(Mutation)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            (
                "mutation($id: ID!, $d: EditionImprintPublisher_u2PartialInput!){ write(id:$id, "
                "data:$d){ result{ imprint } errors{ field messages codes path } } }"
            ),
            {
                "id": edition.pk,
                "d": {
                    "imprint": "updated",
                    **({"publisher_2Id": None} if change == "explicit-null" else {}),
                },
            },
        )
    assert payload == {"data": {"write": {"result": {"imprint": "updated"}, "errors": []}}}
    publisher_table = connection.ops.quote_name(library_models.Publisher._meta.db_table)
    assert not [
        row["sql"]
        for row in captured
        if row["sql"].lstrip().upper().startswith("SELECT")
        and f"FROM {publisher_table}" in row["sql"]
    ]
    edition.refresh_from_db()
    assert edition.imprint == "updated"
    assert read_attr(edition, "publisher_id") == publisher.pk
    assert read_attr(edition, "publisher_2_id") == (
        None if change == "explicit-null" else other.pk
    )
