"""Live GraphQL HTTP tests for generated mutation input shapes and payload slots.

Each row introspects a generated ``DjangoMutation`` input or payload over
``/graphql`` and reads one shape the input generator decides from the related
model's primary ``DjangoType``:

- a forward key to a Relay-Node primary is a ``GlobalID`` (``ItemInput.categoryId``),
  to a plain primary the target's raw pk scalar (``BookInput.shelfId``);
- a forward many-to-many to a Relay-Node primary is a list of ``GlobalID``
  (``BookInput.genres``), to a plain primary a list of raw pks
  (``createShelf``'s ``altBranches``), and is optional either way;
- a payload over a Relay-Node primary carries the row in a nullable ``node``
  slot (``CreateBookViaCustomInputPayload``), over a plain primary in a
  nullable ``result`` slot (``createShelf``'s payload), beside the
  ``errors: [FieldError!]!`` list either way.

Holder schemas mounted beside fakeshop publish the shapes no shipped mutation
writes: a forward one-to-one to a Relay-Node primary (``MembershipCard.patron``),
two columns differing only by an underscore before a digit (``field_2`` /
``field2``) and narrowings over them, and two merged narrowed inputs Strawberry
would re-case to one name.
"""

from functools import wraps
from typing import TYPE_CHECKING

import pytest
import strawberry
from apps.library import models as library_models
from django import forms
from django.db import models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import (
    JSONObject,
    assert_graphql_success,
    json_at,
    json_list,
    json_object,
    json_str,
    post_graphql,
    response_json,
)
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.utils._narrowing import dict_of
from django_strawberry_framework.views import DjangoGraphQLView

if TYPE_CHECKING:
    from typing import TypeAlias

    from django.db.models.expressions import Combinable

    _IntColumn: TypeAlias = models.IntegerField[float | int | str | Combinable, int]

_CURRENT_SCHEMA: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _form_input_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT_SCHEMA["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-input/", _form_input_view)]

_TYPE_REF = "kind name ofType { kind name ofType { kind name ofType { kind name } } }"


def _named_type(type_ref: JSONObject) -> str:
    """Return a type reference's own name, else (a wrapper's ``null`` name) its ``ofType`` name."""
    name = json_at(type_ref, "name") or json_at(type_ref, "ofType", "name")
    assert isinstance(name, str), type_ref
    return name


def _input_fields(type_name: str) -> dict[str, dict[str, object]]:
    """Return ``{field name: type tree}`` for the input object ``type_name`` over HTTP."""
    data = assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ inputFields {{ name type {{ {_TYPE_REF} }} }} }} }}',
    )
    return {
        json_str(field, "name"): json_object(field, "type")
        for field in json_list(data, "__type", "inputFields")
    }


def _mutation_data_input_name(field_name: str) -> str:
    """Return the named input type of mutation ``field_name``'s ``data`` argument."""
    data = assert_graphql_success(
        '{ __type(name: "Mutation") { fields { name args { name type { kind name '
        "ofType { kind name } } } } } }",
    )
    field = next(
        f for f in json_list(data, "__type", "fields") if json_at(f, "name") == field_name
    )
    arg = next(arg for arg in json_list(field, "args") if json_at(arg, "name") == "data")
    return _named_type(json_object(arg, "type"))


def _non_null(inner: dict[str, object]) -> dict[str, object]:
    return {"kind": "NON_NULL", "name": None, "ofType": inner}


def _scalar(name: str) -> dict[str, object]:
    return {"kind": "SCALAR", "name": name, "ofType": None}


def _list_of_non_null(name: str) -> dict[str, object]:
    return {
        "kind": "LIST",
        "name": None,
        "ofType": {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {"kind": "SCALAR", "name": name, "ofType": None},
        },
    }


def test_forward_key_to_a_relay_primary_is_a_required_global_id() -> None:
    """``ItemInput.categoryId`` is ``ID!``: ``CategoryType`` is a Relay node."""
    fields = _input_fields("ItemInput")

    assert fields["categoryId"] == _non_null(_scalar("ID")), fields


def test_forward_key_to_a_plain_primary_is_the_raw_pk_scalar() -> None:
    """``BookInput.shelfId`` is ``Int!``: ``ShelfType`` is not a Relay node.

    ``shelf`` is a required key, so the raw pk scalar is non-null; the
    ``<field>_id`` spelling is what a key maps to on a generated input.
    """
    fields = _input_fields("BookInput")

    assert fields["shelfId"] == _non_null(_scalar("Int")), fields
    assert "shelf" not in fields, fields


def test_many_to_many_to_a_relay_primary_is_an_optional_global_id_list() -> None:
    """``BookInput.genres`` is ``[ID!]``: ``GenreType`` is a Relay node through ``Meta.interfaces``.

    The outer list is nullable: a many-to-many is optional on create whatever
    its column says.
    """
    fields = _input_fields("BookInput")

    assert fields["genres"] == _list_of_non_null("ID"), fields


def test_many_to_many_to_a_plain_primary_is_an_optional_raw_pk_list() -> None:
    """``createShelf``'s ``altBranches`` is ``[Int!]``: ``BranchType`` is not a Relay node."""
    fields = _input_fields(_mutation_data_input_name("createShelf"))

    assert fields["altBranches"] == _list_of_non_null("Int"), fields


def _payload_fields(type_name: str) -> dict[str, dict[str, object]]:
    """Return ``{field name: type tree}`` for the payload object ``type_name`` over HTTP."""
    data = assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ fields {{ name type {{ {_TYPE_REF} }} }} }} }}',
    )
    return {
        json_str(field, "name"): json_object(field, "type")
        for field in json_list(data, "__type", "fields")
    }


def _mutation_payload_name(field_name: str) -> str:
    """Return the named payload type mutation ``field_name`` returns."""
    data = assert_graphql_success(
        '{ __type(name: "Mutation") { fields { name type { kind name ofType { kind name } } } } }',
    )
    field = next(
        f for f in json_list(data, "__type", "fields") if json_at(f, "name") == field_name
    )
    return _named_type(json_object(field, "type"))


_FIELD_ERRORS = _non_null(
    {
        "kind": "LIST",
        "name": None,
        "ofType": {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {"kind": "OBJECT", "name": "FieldError"},
        },
    },
)


def test_payload_of_a_relay_primary_carries_a_nullable_node_slot() -> None:
    """``CreateBookViaCustomInputPayload`` exposes a nullable ``node`` and no ``result``.

    ``BookType`` is a Relay node, so ``payload_object_slot`` names the object
    slot ``node``; the slot is nullable because a refused write returns no row.
    """
    fields = _payload_fields("CreateBookViaCustomInputPayload")

    assert fields["node"] == {"kind": "OBJECT", "name": "BookType", "ofType": None}, fields
    assert fields["errors"] == _FIELD_ERRORS, fields
    assert "result" not in fields, fields


def test_payload_of_a_plain_primary_carries_a_nullable_result_slot() -> None:
    """``createShelf``'s payload exposes a nullable ``result`` and no ``node``.

    ``ShelfType`` is not a Relay node, so the object slot is the uniform
    ``result``, never ``node`` and never a model-derived name.
    """
    fields = _payload_fields(_mutation_payload_name("createShelf"))

    assert fields["result"] == {"kind": "OBJECT", "name": "ShelfType", "ofType": None}, fields
    assert fields["errors"] == _FIELD_ERRORS, fields
    assert "node" not in fields, fields
    assert "shelf" not in fields, fields


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize(
    ("input_literal", "written", "message"),
    [
        pytest.param("{flag: true}", [True], None, id="true"),
        pytest.param("{flag: false}", [False], None, id="false"),
        pytest.param(
            "{}",
            [],
            "Field 'RequiredFlagFormInput.flag' of required type 'Boolean!' was not provided.",
            id="omitted",
        ),
        pytest.param(
            "{flag: null}",
            [],
            "Expected value of type 'Boolean!', found null.",
            id="null",
        ),
    ],
)
def test_a_validating_nullable_boolean_form_field_requires_a_boolean_over_http(
    input_literal: str,
    written: list[bool],
    message: str | None,
) -> None:
    """A validating NullBooleanField subclass accepts either boolean and refuses absence or null."""
    called: list[object] = []

    class RequiredNullableBoolean(forms.NullBooleanField):
        validate = forms.Field.validate

    class RequiredFlagForm(forms.Form):
        flag = RequiredNullableBoolean(required=True)

    class SubmitRequired(DjangoFormMutation):
        class Meta:
            form_class = RequiredFlagForm
            permission_classes = []

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            del info
            called.append(dict_of(form.cleaned_data)["flag"])

    @strawberry.type
    class InputQuery:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class InputMutation:
        submit_required = DjangoMutationField(SubmitRequired)

    finalize_django_types()
    _CURRENT_SCHEMA["schema"] = DjangoSchema(query=InputQuery, mutation=InputMutation)
    try:
        with override_settings(ROOT_URLCONF=__name__):
            response = post_graphql(
                f"mutation {{ submitRequired(data: {input_literal}) {{ ok errors {{ field }} }} }}",
                url="/graphql-input/",
            )
        assert response.status_code == 200
        payload = response_json(response)
    finally:
        _CURRENT_SCHEMA["schema"] = None

    if message is None:
        assert payload == {"data": {"submitRequired": {"ok": True, "errors": []}}}
    else:
        assert payload["data"] is None, payload
        assert len(json_list(payload, "errors")) == 1, payload
        assert json_at(payload, "errors", 0, "message") == message, payload
    assert called == written


def _holder_input_fields(schema: DjangoSchema, type_name: str) -> dict[str, dict[str, object]]:
    """Return ``{field name: type tree}`` for ``type_name`` as the holder ``schema`` serves it."""
    _CURRENT_SCHEMA["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            response = post_graphql(
                f'{{ __type(name: "{type_name}") {{ inputFields {{ name type {{ {_TYPE_REF} }} }} }} }}',
                url="/graphql-input/",
            )
    finally:
        _CURRENT_SCHEMA["schema"] = None
    assert response.status_code == 200
    payload = response_json(response)
    assert "errors" not in payload, payload
    return {
        json_str(field, "name"): json_object(field, "type")
        for field in json_list(payload, "data", "__type", "inputFields")
    }


@strawberry.type
class _HolderQuery:
    @strawberry.field
    def ping(self) -> int:
        return 1


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
def test_one_to_one_to_a_relay_primary_is_a_global_id_over_http() -> None:
    """``MembershipCardInput.patronId`` is ``ID!``: a forward one-to-one keys like a forward key.

    ``PatronNode`` is a Relay node, so the generated input takes the patron's ``GlobalID``
    under the ``<field>_id`` spelling. No fakeshop mutation writes a membership card.
    """

    class PatronNode(DjangoType):
        class Meta:
            model = library_models.Patron
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class MembershipCardNode(DjangoType):
        class Meta:
            model = library_models.MembershipCard
            fields = ("id",)
            interfaces = (relay.Node,)

    class CreateMembershipCard(DjangoMutation):
        class Meta:
            model = library_models.MembershipCard
            operation = "create"
            permission_classes = []

    @strawberry.type
    class Mutation:
        create_membership_card = DjangoMutationField(CreateMembershipCard)

    del PatronNode, MembershipCardNode
    finalize_django_types()
    fields = _holder_input_fields(
        DjangoSchema(query=_HolderQuery, mutation=Mutation),
        "MembershipCardInput",
    )

    assert fields == {
        "patronId": _non_null(_scalar("ID")),
        "barcode": _non_null(_scalar("String")),
    }


def _digit_boundary_schema() -> DjangoSchema:
    """Serve a full create and one narrowed create per column over ``field_2`` beside ``field2``.

    ``field_2`` beside ``field2`` is legal Django but a naming no fakeshop domain model carries.
    """

    class DigitBoundary(models.Model):
        field_2: "_IntColumn" = models.IntegerField()
        field2: "_IntColumn" = models.IntegerField()

        class Meta:
            app_label = "library"
            managed = False

        @override
        def __str__(self) -> str:
            return f"{self.field_2}/{self.field2}"

    class DigitBoundaryNode(DjangoType):
        class Meta:
            model = DigitBoundary
            fields = ("id",)
            interfaces = (relay.Node,)

    class CreateDigitBoundary(DjangoMutation):
        class Meta:
            model = DigitBoundary
            operation = "create"
            permission_classes = []

    class CreateDigitBoundaryUnderscored(DjangoMutation):
        class Meta:
            model = DigitBoundary
            operation = "create"
            fields = ("field_2",)
            permission_classes = []

    class CreateDigitBoundaryJoined(DjangoMutation):
        class Meta:
            model = DigitBoundary
            operation = "create"
            fields = ("field2",)
            permission_classes = []

    @strawberry.type
    class Mutation:
        create_digit_boundary = DjangoMutationField(CreateDigitBoundary)
        create_digit_boundary_underscored = DjangoMutationField(CreateDigitBoundaryUnderscored)
        create_digit_boundary_joined = DjangoMutationField(CreateDigitBoundaryJoined)

    del DigitBoundaryNode
    finalize_django_types()
    return DjangoSchema(query=_HolderQuery, mutation=Mutation)


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
def test_digit_boundary_columns_keep_distinct_wire_names_over_http() -> None:
    """``field_2`` and ``field2`` publish two input fields, never one silently overwritten.

    Their camel names differ, so the collision guard passes the pair; Strawberry would
    re-derive an unpinned ``field_2`` to ``field2`` and drop one column from the SDL. Every
    generated input field pins its wire name
    (``django_strawberry_framework/utils/inputs.py::build_strawberry_input_class``).
    """
    fields = _holder_input_fields(_digit_boundary_schema(), "DigitBoundaryInput")

    assert fields == {"field_2": _non_null(_scalar("Int")), "field2": _non_null(_scalar("Int"))}


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize(
    ("type_name", "field"),
    [("DigitBoundaryField_u2Input", "field_2"), ("DigitBoundaryField2Input", "field2")],
    ids=["field_2", "field2"],
)
def test_digit_boundary_narrowings_publish_distinct_input_types_over_http(
    type_name: str,
    field: str,
) -> None:
    """A ``Meta.fields`` narrowing to ``field_2`` and one to ``field2`` mint two input types.

    The narrowed name's token keeps an underscore before a digit
    (``django_strawberry_framework/utils/inputs.py::pascalize_token``), so the two shapes
    never claim one GraphQL type name; each type carries its one column.
    """
    fields = _holder_input_fields(_digit_boundary_schema(), type_name)

    assert fields == {field: _non_null(_scalar("Int"))}


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize(
    ("type_name", "fields"),
    [
        ("CollA_ubCInput", {"aB": _non_null(_scalar("Int")), "c": _non_null(_scalar("Int"))}),
        ("CollA_ubcInput", {"aBc": _non_null(_scalar("Int"))}),
    ],
    ids=["a_b-and-c", "a_bc"],
)
def test_merged_narrowed_inputs_recased_alike_publish_both_names_over_http(
    type_name: str,
    fields: dict[str, dict[str, object]],
) -> None:
    """Two merged narrowed inputs Strawberry would re-case alike publish both canonical names.

    Columns ``a_b`` + ``c`` and ``a_bc`` name the distinct shapes ``CollA_ubCInput`` and
    ``CollA_ubcInput``; ``to_camel_case`` maps both class names to ``CollAUbcinput``, so the
    merge with a consumer ``input_class`` pins the shape's name
    (``django_strawberry_framework/mutations/sets.py::_materialize_merged_input``) and both
    types build.
    """

    class Coll(models.Model):
        a_b: "_IntColumn" = models.IntegerField()
        c: "_IntColumn" = models.IntegerField()
        a_bc: "_IntColumn" = models.IntegerField()

        class Meta:
            app_label = "library"
            managed = False

        @override
        def __str__(self) -> str:
            return f"{self.a_b}/{self.c}/{self.a_bc}"

    class CollNode(DjangoType):
        class Meta:
            model = Coll
            fields = ("id",)
            interfaces = (relay.Node,)

    @strawberry.input
    class CustomCInput:
        c: int = strawberry.field(description="custom")

    @strawberry.input
    class CustomABCInput:
        a_bc: int = strawberry.field(description="custom")

    class CreateCollPair(DjangoMutation):
        class Meta:
            model = Coll
            operation = "create"
            fields = ("a_b", "c")
            input_class = CustomCInput
            permission_classes = []

    class CreateCollJoined(DjangoMutation):
        class Meta:
            model = Coll
            operation = "create"
            fields = ("a_bc",)
            input_class = CustomABCInput
            permission_classes = []

    @strawberry.type
    class Mutation:
        create_coll_pair = DjangoMutationField(CreateCollPair)
        create_coll_joined = DjangoMutationField(CreateCollJoined)

    del CollNode
    finalize_django_types()

    assert _holder_input_fields(
        DjangoSchema(query=_HolderQuery, mutation=Mutation),
        type_name,
    ) == (fields)
