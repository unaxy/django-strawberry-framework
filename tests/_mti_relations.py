"""Real MTI-parent forward-M2M fixtures shared by live and private resolver tests.

The shipped Venue chain has a reverse M2M; Django's ancestor prefetch reuse
requires the forward M2M declared here. Tables are real and explicitly created
under transaction-enabled tests. Model declarations stay function-local for
suite-wide Django app-registry cleanup. No fixture row is catalog/auth data.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import strawberry
from asgiref.sync import sync_to_async
from django.db import connection as db_connection
from django.db import models
from django.db.models import Model, QuerySet
from typing_extensions import override

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.registry import registry

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable
    from django.db.models.fields.related_descriptors import ManyRelatedManager


def declare_mti_tag_models() -> tuple[type[Model], type[Model], type[Model]]:
    """Declare a forward many-to-many on an MTI parent, plus the parent's child.

    Test-local because fakeshop carries no forward many-to-many on a model with
    a multi-table child (its one inherited many-to-many, ``venuesponsor`` on the
    ``Venue`` chain, is a reverse relation, which Django never serves from an
    ancestor). ``managed = False`` keeps ``migrate`` away from the tables, which
    ``create_mti_tag_tables`` creates and ``drop_mti_tag_tables`` drops; the suite's ``_restore_app_registry``
    unregisters the classes after each test.
    """

    class MtiTag(models.Model):
        name: "models.TextField[str | Combinable, str]" = models.TextField()

        class Meta:
            app_label = "library"
            managed = False
            db_table = "resolvers_mti_tag"
            ordering = ("name",)

    class MtiPlace(models.Model):
        name: "models.TextField[str | Combinable, str]" = models.TextField()
        tags: "models.ManyToManyField[MtiTag, models.Model]" = models.ManyToManyField(
            MtiTag,
            db_table="resolvers_mti_place_tags",
        )

        class Meta:
            app_label = "library"
            managed = False
            db_table = "resolvers_mti_place"

    class MtiShop(MtiPlace):
        # basedpyright: Django's ModelBase pops a concrete model's Meta (only an abstract model
        # keeps one), so MtiPlace has no Meta at run time for this one to subclass
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            app_label = "library"
            managed = False
            db_table = "resolvers_mti_shop"

    return MtiTag, MtiPlace, MtiShop


@runtime_checkable
class _TaggedRow(Protocol):
    """An MTI fixture row carrying the ``tags`` many-to-many manager."""

    tags: "ManyRelatedManager[Model, Model]"


@runtime_checkable
class _PlaceWithShop(Protocol):
    """An MTI fixture parent row reaching its child through the ``mtishop`` accessor."""

    mtishop: Model


def create_mti_tag_tables(*models_in_order: type[Model]) -> None:
    with db_connection.schema_editor() as editor:
        for model in models_in_order:
            editor.create_model(model)


def drop_mti_tag_tables(*models_in_order: type[Model]) -> None:
    with db_connection.schema_editor() as editor:
        for model in reversed(models_in_order):
            editor.delete_model(model)


def seed_mti_tags(tag_model: type[Model], shop_model: type[Model]) -> None:
    """Two shops: ``One`` tagged Alpha / Beta / Hidden, ``Two`` tagged Beta."""
    # Reverse name order makes the declared ordering observable on every path.
    hidden = tag_model.objects.create(name="Hidden")
    beta = tag_model.objects.create(name="Beta")
    alpha = tag_model.objects.create(name="Alpha")
    one = shop_model.objects.create(name="One")
    two = shop_model.objects.create(name="Two")
    assert isinstance(one, _TaggedRow)
    assert isinstance(two, _TaggedRow)
    one.tags.add(alpha, beta, hidden)
    two.tags.add(beta)


def _shops_reached_through_prefetched_places(place_model: type[Model]) -> list[Model]:
    """Prefetch ``tags`` on the PARENT rows, then walk down to each child.

    ``place.mtishop`` caches the parent on the child's ``mtiplace_ptr``. From
    Django 6.1 the child's ``tags`` manager answers from that ancestor's
    prefetch, so its ``all()`` is an EVALUATED queryset while the child's own
    ``_prefetched_objects_cache`` holds nothing.
    """
    places = place_model.objects.prefetch_related("tags").order_by("name")
    shops: list[Model] = []
    for place in places:
        assert isinstance(place, _PlaceWithShop)
        shops.append(place.mtishop)
    return shops


def mti_tag_schema(
    tag_model: type[Model],
    place_model: type[Model],
    shop_model: type[Model],
    *,
    hide_prefix: str | None = None,
    run_async: bool,
) -> DjangoSchema:
    """Build a ``DjangoSchema`` whose ``shops`` root returns the walked-down children."""

    class MtiTagType(DjangoType):
        class Meta:
            model = tag_model
            fields = ("id", "name")

        if hide_prefix is not None:

            @classmethod
            @override
            def get_queryset(cls, queryset: QuerySet[Model], info: object) -> QuerySet[Model]:
                return queryset.exclude(name__startswith=hide_prefix)

    assert registry.get(tag_model) is MtiTagType

    class MtiShopType(DjangoType):
        class Meta:
            model = shop_model
            fields = ("id", "name", "tags")

    finalize_django_types()

    @strawberry.type(name="Query")
    class AsyncQuery:
        async def _shops(self) -> list[Model]:
            return await sync_to_async(_shops_reached_through_prefetched_places)(
                place_model,
            )

        shops: list[Model] = strawberry.field(resolver=_shops, graphql_type=list[MtiShopType])

    @strawberry.type(name="Query")
    class SyncQuery:
        def _shops(self) -> list[Model]:
            return _shops_reached_through_prefetched_places(place_model)

        shops: list[Model] = strawberry.field(resolver=_shops, graphql_type=list[MtiShopType])

    return DjangoSchema(query=AsyncQuery if run_async else SyncQuery, config=strawberry_config())
