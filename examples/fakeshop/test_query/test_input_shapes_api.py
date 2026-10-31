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
"""

from functools import wraps

import pytest
import strawberry
from django import forms
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
from typing_extensions import override

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoMutationField,
    DjangoSchema,
    finalize_django_types,
)
from django_strawberry_framework.utils._narrowing import dict_of
from django_strawberry_framework.views import DjangoGraphQLView

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
