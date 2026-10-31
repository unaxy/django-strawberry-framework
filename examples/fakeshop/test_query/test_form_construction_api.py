"""Live HTTP form construction, validation and narrowed-update contracts."""

from __future__ import annotations

from collections.abc import Mapping
from functools import wraps

import pytest
import strawberry
from apps.products import models as product_models
from apps.products.services import seed_data
from django import forms
from django.db import models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list, json_object
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import dict_of
from django_strawberry_framework.utils.typing import call_forwarded
from django_strawberry_framework.views import DjangoGraphQLView
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-form-construction/", _graphql_view)]


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _schema(mutation: type) -> DjangoSchema:
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_Query,
        mutation=mutation,
        extensions=[lambda: optimizer],
        error_policy={"enabled": False},
    )


def _post(schema: DjangoSchema, document: str, *, variables: Mapping[str, object]) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-form-construction/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("provided", "expected"),
    [(False, None), (True, True)],
    ids=["omitted", "provided-true"],
)
def test_null_boolean_field_omitted_in_mutation_uses_unset_default(
    *,
    provided: bool,
    expected: bool | None,
) -> None:
    """Omitting a ``NullBooleanField`` in the input succeeds at RUNTIME (the UNSET default).

    Baking ``bool | None`` while leaving the input field required would produce
    SDL that lets GraphQL validation accept the omit, then Strawberry would raise
    ``TypeError: missing 1 required keyword-only argument`` when constructing the
    input object. With the field
    widened to ``| None`` + ``UNSET`` the omit reaches the bound form as an
    absent value, and ``NullBooleanField`` resolves it to ``None``. A pure-SDL
    test cannot catch this - only executing the mutation with the field omitted.
    """
    captured = {}

    class NullFlagForm(forms.Form):
        flag = forms.NullBooleanField()  # Django default required=True
        name = forms.CharField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = NullFlagForm
            permission_classes = []

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            captured["flag"] = form.cleaned_data["flag"]

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    # ``flag`` is OMITTED entirely - only ``name`` is supplied.
    res = _post(
        schema,
        "mutation($d: NullFlagFormInput!){ submit(data:$d){ ok errors{ field messages } } }",
        variables={"d": {"name": "hi", **({"flag": True} if provided else {})}},
    )
    assert res == {"data": {"submit": {"ok": True, "errors": []}}}
    assert captured["flag"] is expected


@pytest.mark.django_db
def test_get_form_kwargs_override_waives_create_required_guard() -> None:
    """Overriding ``get_form_kwargs`` waives the create-required-narrowing guard.

    A ``Meta.fields`` narrowing dropping a still-required form field would normally
    raise at bind; the override is trusted to inject it, so the bind succeeds.
    """

    class TwoFieldForm(forms.Form):
        keep = forms.CharField()
        injected = forms.CharField()  # required, but dropped by Meta.fields

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = TwoFieldForm
            fields = ("keep",)
            permission_classes = []

        @override
        def get_form_kwargs(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> dict[str, object]:
            merged = dict(data)
            merged["injected"] = "supplied"
            return {"data": merged, "files": files}

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    # Must NOT raise at finalize (the guard is waived).
    finalize_django_types()
    schema = _schema(Mutation)
    res = _post(
        schema,
        "mutation($d: TwoFieldFormKeepInput!){ submit(data:$d){ ok errors{ field } } }",
        variables={"d": {"keep": "k"}},
    )
    assert res == {"data": {"submit": {"ok": True, "errors": []}}}


@pytest.mark.django_db
def test_get_form_only_override_builds_the_form_and_waives_the_required_guard() -> None:
    """A ``get_form``-ONLY override is honored at bind AND at construction.

    The coarser construction hook, exercised without ``get_form_kwargs`` in the
    picture: the mutation narrows a still-required form field away, which the
    create-required-narrowing guard rejects unless a construction hook is
    overridden - so ``finalize_django_types()`` succeeding is itself the assertion
    that the ``get_form`` override is what waived the guard. The pipeline must then
    validate the very form object the override returned (not a reconstructed
    default), pinned by the sentinel the override injects reaching
    ``cleaned_data`` and the successful HTTP response.
    """

    class TwoFieldForm(forms.Form):
        keep = forms.CharField()
        injected = forms.CharField()  # required, but dropped by Meta.fields below

    captured = {}

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = TwoFieldForm
            fields = ("keep",)
            permission_classes = []

        @override
        def get_form(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> forms.BaseForm:
            merged = dict(data)
            merged["injected"] = "from-get-form"
            assert not files
            return TwoFieldForm(data=merged)

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            captured["injected"] = form.cleaned_data["injected"]

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    # Must NOT raise: the narrowing dropped the required ``injected`` and only
    # ``get_form`` is overridden, so the waiver has to reach through that operand.
    finalize_django_types()
    schema = _schema(Mutation)
    res = _post(
        schema,
        "mutation($d: TwoFieldFormKeepInput!){ submit(data:$d){ ok errors{ field messages } } }",
        variables={"d": {"keep": "k"}},
    )
    assert res == {"data": {"submit": {"ok": True, "errors": []}}}
    assert captured["injected"] == "from-get-form"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("scoped", "inside", "accepted"),
    [(True, True, True), (True, False, False), (False, False, True)],
    ids=["scoped-inside", "scoped-outside", "unscoped-outside"],
)
def test_request_scoped_form_queryset_controls_relation_acceptance(
    *,
    scoped: bool,
    inside: bool,
    accepted: bool,
) -> None:
    """The bound form's queryset accepts its members and refuses excluded relation IDs."""
    seed_data(0)
    catalog_categories = categories_from_seed(
        ("__fixture_category_0__", False),
        ("__fixture_category_1__", False),
    )

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True

    class CategoryPickForm(forms.Form):
        category = forms.ModelChoiceField(queryset=product_models.Category.objects.all())

        # basedpyright: the verbatim forward to forms.Form.__init__ runs through call_forwarded,
        # which the checker does not read as a super() call
        def __init__(  # pyright: ignore[reportMissingSuperCall]
            self,
            *args: object,
            allowed_categories: models.QuerySet[product_models.Category] | None = None,
            **kwargs: object,
        ) -> None:
            call_forwarded(super().__init__, args, kwargs)
            if allowed_categories is not None:
                assert isinstance(self.fields["category"], forms.ModelChoiceField)
                self.fields["category"].queryset = allowed_categories

    allowed = {}

    class PickAnyCategory(DjangoFormMutation):
        class Meta:
            form_class = CategoryPickForm
            permission_classes = []

    class PickScopedCategory(DjangoFormMutation):
        class Meta:
            form_class = CategoryPickForm
            permission_classes = []

        @override
        def get_form_kwargs(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> dict[str, object]:
            kwargs = super().get_form_kwargs(info, data=data, files=files, instance=instance)
            kwargs["allowed_categories"] = allowed["queryset"]
            return kwargs

    @strawberry.type
    class Mutation:
        pick_any = DjangoMutationField(PickAnyCategory)
        pick_scoped = DjangoMutationField(PickScopedCategory)

    finalize_django_types()
    schema = _schema(Mutation)

    allowed_category = catalog_categories[0]
    product_models.Category.objects.filter(pk=allowed_category.pk).update(
        description="",
        is_private=False,
        name="Inside",
    )
    allowed_category.refresh_from_db()
    outside = catalog_categories[1]
    product_models.Category.objects.filter(pk=outside.pk).update(
        description="",
        is_private=False,
        name="Outside",
    )
    outside.refresh_from_db()
    allowed["queryset"] = product_models.Category.objects.filter(pk=saved_pk(allowed_category))

    selected = allowed_category if inside else outside
    field_name = "pickScoped" if scoped else "pickAny"
    result = _post(
        schema,
        f"mutation($d: CategoryPickFormInput!){{ {field_name}(data:$d){{ "
        "ok errors{ field messages codes } } }",
        variables={"d": {"categoryId": global_id_for(CategoryT, saved_pk(selected))}},
    )
    assert result == {
        "data": {
            field_name: {
                "ok": accepted,
                "errors": []
                if accepted
                else [
                    {
                        "field": "categoryId",
                        "messages": [
                            "Select a valid choice. That choice is not one of the available choices.",
                        ],
                        "codes": ["invalid_choice"],
                    },
                ],
            },
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize("provided", [False, True], ids=["omitted", "provided"])
def test_required_extra_field_omitted_on_update_is_coercion_error(*, provided: bool) -> None:
    """A required non-model extra field stays required in the partial input.

    Omitting it is a GraphQL coercion error BEFORE the resolver.

    The partial input keeps a required non-model extra field required (it
    is not a model-backed field forced optional). Because a required generated
    field carries NO class default, an omitted required field is rejected at
    variable coercion rather than silently arriving as ``None`` at the resolver and
    surfacing as an in-band ``FieldError`` (which would mask the missing-input error).
    """
    seed_data(1)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(catalog_categories[0], ("__fixture_item_0__", False))
    product_models.Entry.objects.filter(item__in=catalog_items).delete()

    class ConfirmForm(forms.ModelForm[product_models.Item]):
        confirm = forms.CharField()  # required non-model extra field

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True

    assert registry.get(product_models.Category) is CategoryT

    class ItemT(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = ConfirmForm
            operation = "update"
            permission_classes = []

    @strawberry.type
    class Mutation:
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name="Cat",
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
    res = _post(
        schema,
        "mutation($id: ID!, $d: ConfirmFormPartialInput!){ updateItem(id:$id, data:$d){ "
        "node{ name } errors{ field messages } } }",
        variables={
            "id": global_id_for(ItemT, saved_pk(item)),
            "d": {"name": "Y", **({"confirm": "yes"} if provided else {})},
        },
    )
    if provided:
        assert res == {"data": {"updateItem": {"node": {"name": "Y"}, "errors": []}}}
    else:
        assert res["data"] is None
        errors = json_list(res, "errors")
        assert len(errors) == 1
        error = json_object(errors[0])
        assert (
            error["message"] == "Variable '$d' got invalid value {'name': 'Y'}; "
            "Field 'confirm' of required type 'String!' was not provided."
        )
    item.refresh_from_db()
    assert item.name == ("Y" if provided else "X")
    assert item.category_id == saved_pk(cat)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("message", "ok"),
    [("go", True), ("fail", False)],
    ids=["valid", "invalid"],
)
def test_perform_mutate_override_runs_only_on_success(*, message: str, ok: bool) -> None:
    """A consumer's perform_mutate hook runs exactly once only after successful validation."""
    calls: list[object] = []

    class ContactForm(forms.Form):
        message = forms.CharField()

        def clean_message(self) -> object:
            value = dict_of(self.cleaned_data)["message"]
            if value == "fail":
                raise forms.ValidationError("nope")
            return value

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = []

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            calls.append(dict_of(form.cleaned_data).get("message"))

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    q = "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field messages codes } } }"
    result = _post(schema, q, variables={"d": {"message": message}})
    assert result == {
        "data": {
            "submit": {
                "ok": ok,
                "errors": [] if ok else [{"field": "message", "messages": ["nope"], "codes": []}],
            },
        },
    }
    assert calls == ([message] if ok else [])


@pytest.mark.django_db
@pytest.mark.parametrize("collision", [False, True], ids=["unique", "collision"])
def test_narrowed_update_preserves_excluded_required_fk_and_validates_constraint(
    *,
    collision: bool,
) -> None:
    """A ``Meta.fields``-narrowed update reconstructs an EXCLUDED required FK from the row.

    The ModelForm declares ``('name', 'category')`` while the update mutation
    narrows the GraphQL input to ``('name',)``. A name-only update must preserve
    the located row's ``category`` (the bound ModelForm validates ``category`` even
    though it is off the wire), and the ``unique_item_per_category`` constraint
    must still validate against that preserved FK.
    """
    seed_data(2)
    catalog_categories = categories_from_seed(("__fixture_category_0__", False))
    catalog_items = items_from_seed(
        catalog_categories[0],
        ("__fixture_item_0__", False),
        ("__fixture_item_1__", False),
    )
    product_models.Entry.objects.filter(item__in=catalog_items).delete()

    class NameCategoryForm(forms.ModelForm[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True

    assert registry.get(product_models.Category) is CategoryT

    class ItemT(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            interfaces = (relay.Node,)
            primary = True

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = NameCategoryForm
            operation = "update"
            fields = ("name",)  # narrow the GraphQL input to name only
            permission_classes = []

    @strawberry.type
    class Mutation:
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    # The narrowed shape gets a shape-derived input name; read it off the bound class.
    assert UpdateItem._input_class is not None
    input_name = UpdateItem._input_class.__name__
    query = (
        f"mutation($id: ID!, $d: {input_name}!){{ updateItem(id:$id, data:$d){{ "
        "node{ name category{ name } } errors{ field messages } } }"
    )
    cat = catalog_categories[0]
    product_models.Category.objects.filter(pk=cat.pk).update(
        description="",
        is_private=False,
        name="Cat",
    )
    cat.refresh_from_db()
    item = catalog_items[0]
    product_models.Item.objects.filter(pk=item.pk).update(
        description="",
        is_private=False,
        attachment="",
        name="Before",
        category=cat,
    )
    item.refresh_from_db()

    product_models.Item.objects.filter(pk=catalog_items[1].pk).update(name="Taken", category=cat)
    desired_name = "Taken" if collision else "After"
    result = _post(
        schema,
        query,
        variables={"id": global_id_for(ItemT, saved_pk(item)), "d": {"name": desired_name}},
    )
    assert result.get("errors") is None, result
    payload = json_object(result, "data", "updateItem")
    if collision:
        assert payload["node"] is None
        errors = json_list(payload, "errors")
        assert len(errors) == 1
        error = json_object(errors[0])
        assert error["field"] == NON_FIELD_ERROR_KEY
        assert error["messages"] == ["Item with this Category and Name already exists."]
    else:
        assert payload == {"node": {"name": "After", "category": {"name": cat.name}}, "errors": []}
    item.refresh_from_db()
    assert item.name == ("Before" if collision else "After")
    assert item.category_id == saved_pk(cat)
