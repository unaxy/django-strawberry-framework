"""Unbound raw relation forms compare target primary keys and drop uncoercible members over HTTP.

The consumer's ordinary JSON argument constructs its public FilterSet
and reads its qs property. No target DjangoType is registered, so generated
relation leaves keep their raw-key form behavior rather than Relay conversion.
"""

from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_object
from strawberry.scalars import JSON

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-raw-relation-form/", _graphql_view)]


def _schema(filterset: type[FilterSet], model: type[Model], label: str) -> DjangoSchema:
    output = type(
        "RawRelationRoot",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": (label,)})},
    )

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[Model]:
        del root
        request = require_instance(read_attr(info.context, "request"), HttpRequest)
        return filterset(
            data=json_object(where),
            queryset=model._default_manager.order_by(label),
            request=request,
        ).qs

    def resolve_all(root: object) -> QuerySet[Model]:
        del root
        return model._default_manager.order_by(label)

    @strawberry.type
    class Query:
        rows: QuerySet[Model] = strawberry.field(resolver=resolve_rows, graphql_type=list[output])
        all_rows: QuerySet[Model] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[output],
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: extension],
    )


def _post(schema: DjangoSchema, where: JSONObject, label: str) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                f"query($where: JSON!) {{ rows(where: $where) {{ {label} }} allRows {{ {label} }} }}",
                variables={"where": where},
                url="/graphql-raw-relation-form/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize("many", [False, True], ids=["exact", "membership"])
def test_generated_raw_to_field_relation_form_uses_the_targets_primary_key(*, many: bool) -> None:
    """A stored name equal to another genre's key never aliases that genre's identity."""
    alpha = models.Genre.objects.create(name="ALPHA")
    beta = models.Genre.objects.create(name="BETA")
    gamma = models.Genre.objects.create(name="GAMMA")
    decoy = models.Genre.objects.create(name=str(saved_pk(alpha)))
    for name, genre in (
        ("ALPHA", alpha),
        ("BETA", beta),
        ("GAMMA", gamma),
        ("DECOY", decoy),
    ):
        patron = models.Patron.objects.create(name=name, email=f"{name}@example.test")
        models.PatronProfile.objects.create(patron=patron, postal_code=name, favorite_genre=genre)

    class ProfileFilter(FilterSet):
        class Meta:
            model = models.PatronProfile
            fields = {"favorite_genre": ["exact", "in"]}

    where: JSONObject = (
        {"favorite_genre__in": [saved_pk(alpha), saved_pk(beta)]}
        if many
        else {"favorite_genre": saved_pk(alpha)}
    )
    payload = _post(
        _schema(ProfileFilter, models.PatronProfile, "postal_code"),
        where,
        "postalCode",
    )
    assert payload == {
        "data": {
            "rows": [{"postalCode": name} for name in (["ALPHA", "BETA"] if many else ["ALPHA"])],
            "allRows": [
                {"postalCode": name}
                for name in (
                    "ALPHA",
                    "BETA",
                    "DECOY",
                    "GAMMA",
                )
            ],
        },
    }, payload


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["exact", "bad-membership", "mixed-membership"])
def test_generated_raw_relation_form_drops_only_members_the_target_column_cannot_hold(
    kind: str,
) -> None:
    """Bad keys identify no target while a valid member beside one still selects its own root."""
    branch = models.Branch.objects.create(name="raw form")
    shelf = models.Shelf.objects.create(branch=branch, code="selected")
    other = models.Shelf.objects.create(branch=branch, code="other")
    models.Book.objects.create(shelf=shelf, title="Kept")
    models.Book.objects.create(shelf=other, title="Other")

    class BookShelfFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"shelf": ["exact", "in"]}

    where: JSONObject = {"shelf": "not-a-pk"}
    if kind != "exact":
        where = {
            "shelf__in": ["not-a-pk", saved_pk(shelf)]
            if kind == "mixed-membership"
            else ["not-a-pk"],
        }
    payload = _post(_schema(BookShelfFilter, models.Book, "title"), where, "title")
    assert payload == {
        "data": {
            "rows": [{"title": "Kept"}] if kind == "mixed-membership" else [],
            "allRows": [{"title": "Kept"}, {"title": "Other"}],
        },
    }, payload
