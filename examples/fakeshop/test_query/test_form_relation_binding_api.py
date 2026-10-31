"""Live HTTP form tests for relation-key reconstruction, replacement and decode refusals."""

from collections.abc import Mapping
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django import forms
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload, post_lock_rereads
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
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import dict_of, read_attr
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-form-relations/", _graphql_view)]


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _schema(mutation: type[object]) -> DjangoSchema:
    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(query=_Query, mutation=mutation, extensions=[lambda: optimizer])


def _post(schema: DjangoSchema, document: str, variables: Mapping[str, object]) -> JSONObject:
    """Read the native HTTP response and restore this test's schema mount on every exit."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(document, variables=variables, url="/graphql-form-relations/")
    finally:
        _CURRENT["schema"] = None


def _relation_error(field: str) -> JSONObject:
    """The independent public relation decode error selected by these operations."""
    return {
        "field": field,
        "messages": [f"Invalid id for relation {field!r}."],
        "codes": ["invalid"],
        "path": [field],
    }


def _book() -> models.Book:
    branch = models.Branch.objects.create(name="Form relation branch")
    shelf = models.Shelf.objects.create(code="Form relation shelf", branch=branch)
    return models.Book.objects.create(title="Original", shelf=shelf)


def _book_schema() -> tuple[DjangoSchema, type[DjangoType], type[DjangoType]]:
    class GenreNode(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class ShelfNode(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)

    class BookNode(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)

    class BookForm(forms.ModelForm[models.Book]):
        genres = forms.ModelMultipleChoiceField(
            queryset=models.Genre.objects.all(),
            to_field_name="name",
            required=False,
        )

        class Meta:
            model = models.Book
            fields = ("title", "shelf", "genres")

    class UpdateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "update"
            permission_classes = []

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    assert registry.get(models.Shelf) is ShelfNode
    return _schema(Mutation), BookNode, GenreNode


_BOOK_UPDATE = (
    "mutation($id: ID!, $d: BookFormPartialInput!){ updateBook(id:$id, data:$d){ "
    "node{ title } errors{ field messages codes path } } }"
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value",
    [
        "omitted",
        "supplied",
        "empty-list",
        "explicit-null",
    ],
)
def test_form_m2m_name_keys_preserve_omission_and_obey_explicit_replacement(value: str) -> None:
    """An omitted name-keyed set survives, a supplied set replaces, and either empty shape clears."""
    book = _book()
    selected = models.Genre.objects.create(name="Selected genre")
    previous = models.Genre.objects.create(name="Previous genre")
    book.genres.add(previous if value == "supplied" else selected)
    schema, book_type, genre_type = _book_schema()
    data: dict[str, object] = {"title": "Renamed"}
    if value == "supplied":
        data["genres"] = [global_id_for(genre_type, selected.pk)]
    elif value == "empty-list":
        data["genres"] = []
    elif value == "explicit-null":
        data["genres"] = None

    payload = _post(
        schema,
        _BOOK_UPDATE,
        {"id": global_id_for(book_type, book.pk), "d": data},
    )
    assert payload == {"data": {"updateBook": {"node": {"title": "Renamed"}, "errors": []}}}
    book.refresh_from_db()
    assert book.title == "Renamed"
    assert list(book.genres.order_by("pk").values_list("pk", flat=True)) == (
        [] if value in {"empty-list", "explicit-null"} else [selected.pk]
    )
    assert book.shelf_id == models.Shelf.objects.get().pk
    assert list(models.Genre.objects.order_by("pk").values_list("name", flat=True)) == [
        "Selected genre",
        "Previous genre",
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["omitted", "supplied"])
def test_form_m2m_member_with_an_empty_name_is_preserved_or_attached(value: str) -> None:
    """An empty form key names a real M2M member and costs the same four genre reads."""
    book = _book()
    empty = models.Genre.objects.create(name="")
    schema, book_type, genre_type = _book_schema()
    data: dict[str, object] = {"title": "Renamed"}
    if value == "omitted":
        book.genres.add(empty)
    else:
        data["genres"] = [global_id_for(genre_type, empty.pk)]
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            _BOOK_UPDATE,
            {"id": global_id_for(book_type, book.pk), "d": data},
        )
    assert payload == {"data": {"updateBook": {"node": {"title": "Renamed"}, "errors": []}}}
    book.refresh_from_db()
    assert book.title == "Renamed"
    assert list(book.genres.values_list("pk", flat=True)) == [empty.pk]
    genre_reads = [
        query["sql"]
        for query in captured.captured_queries
        if query["sql"].lstrip().upper().startswith("SELECT")
        and 'FROM "library_genre"' in query["sql"]
    ]
    assert len(genre_reads) == 4 + post_lock_rereads(int(value == "supplied")), genre_reads


def _loan_schema() -> tuple[DjangoSchema, type[DjangoType], type[DjangoType]]:
    class PatronNode(DjangoType):
        class Meta:
            model = models.Patron
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class LoanNode(DjangoType):
        class Meta:
            model = models.Loan
            fields = ("id", "note")
            interfaces = (relay.Node,)

    class LoanForm(forms.ModelForm[models.Loan]):
        patron = forms.ModelChoiceField(queryset=models.Patron.objects.all(), to_field_name="name")

        class Meta:
            model = models.Loan
            fields = ("note", "patron")

    class UpdateLoan(DjangoModelFormMutation):
        class Meta:
            form_class = LoanForm
            operation = "update"
            permission_classes = []

    @strawberry.type
    class Mutation:
        update_loan = DjangoMutationField(UpdateLoan)

    return _schema(Mutation), LoanNode, PatronNode


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["omitted", "supplied", "missing"])
def test_form_fk_name_key_preserves_omission_and_checks_a_supplied_target(value: str) -> None:
    """An omitted name-keyed FK survives, a supplied FK changes, and a missing target writes nothing."""
    book = _book()
    previous = models.Patron.objects.create(name="Previous patron")
    selected = models.Patron.objects.create(name="Selected patron")
    loan = models.Loan.objects.create(book=book, patron=previous, note="Original")
    schema, loan_type, patron_type = _loan_schema()
    data: dict[str, object] = {"note": "Renamed"}
    if value != "omitted":
        assert selected.pk is not None
        target_pk = selected.pk + 1000 if value == "missing" else selected.pk
        data["patronId"] = global_id_for(patron_type, target_pk)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            "mutation($id: ID!, $d: LoanFormPartialInput!){ updateLoan(id:$id, data:$d){ "
            "node{ note } errors{ field messages codes path } } }",
            {"id": global_id_for(loan_type, loan.pk), "d": data},
        )
    expected: JSONObject = (
        {"node": None, "errors": [_relation_error("patronId")]}
        if value == "missing"
        else {"node": {"note": "Renamed"}, "errors": []}
    )
    assert payload == {"data": {"updateLoan": expected}}
    loan.refresh_from_db()
    assert loan.note == ("Original" if value == "missing" else "Renamed")
    assert read_attr(loan, "patron_id") == (selected.pk if value == "supplied" else previous.pk)
    assert read_attr(loan, "book_id") == book.pk
    if value == "missing":
        assert not [
            query["sql"]
            for query in captured.captured_queries
            if query["sql"].lstrip().upper().startswith("UPDATE")
            and '"library_loan"' in query["sql"]
        ]


def _pick_schema() -> tuple[DjangoSchema, type[DjangoType]]:
    class GenreNode(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class PickForm(forms.Form):
        genre = forms.ModelChoiceField(queryset=models.Genre.objects.all())

    class Pick(DjangoFormMutation):
        class Meta:
            form_class = PickForm
            permission_classes = []

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            del info
            genre = dict_of(form.cleaned_data)["genre"]
            assert isinstance(genre, models.Genre)
            models.Branch.objects.create(name=genre.name)

    @strawberry.type
    class Mutation:
        pick = DjangoMutationField(Pick)

    return _schema(Mutation), GenreNode


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["saved", "missing"])
def test_plain_form_relation_decode_refusal_skips_the_write_and_returns_not_ok(value: str) -> None:
    """A valid relation reaches the consumer write; a missing one returns its field error first."""
    genre = models.Genre.objects.create(name="Picked genre")
    schema, genre_type = _pick_schema()
    assert genre.pk is not None
    pk = genre.pk + 1000 if value == "missing" else genre.pk
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            "mutation($d: PickFormInput!){ pick(data:$d){ ok errors{ field messages codes path } } }",
            {"d": {"genreId": global_id_for(genre_type, pk)}},
        )
    expected: JSONObject = (
        {"ok": False, "errors": [_relation_error("genreId")]}
        if value == "missing"
        else {"ok": True, "errors": []}
    )
    assert payload == {"data": {"pick": expected}}
    assert list(models.Branch.objects.values_list("name", flat=True)) == (
        [] if value == "missing" else [genre.name]
    )
    inserts = [
        query["sql"]
        for query in captured.captured_queries
        if query["sql"].lstrip().upper().startswith("INSERT")
        and '"library_branch"' in query["sql"]
    ]
    assert len(inserts) == int(value == "saved"), inserts


def _printing_schema(*, hides_empty: bool) -> DjangoSchema:
    class EditionNode(DjangoType):
        class Meta:
            model = models.Edition
            fields = ("isbn_13",)

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Edition],
            info: strawberry.Info,
        ) -> QuerySet[models.Edition]:
            del cls, info
            if hides_empty:
                return queryset.exclude(isbn_13="").exclude(isbn_13__startswith="hidden")
            return queryset

    class PrintingNode(DjangoType):
        class Meta:
            model = models.Printing
            fields = ("id", "run_size")
            interfaces = (relay.Node,)

    class PrintingForm(forms.ModelForm[models.Printing]):
        class Meta:
            model = models.Printing
            fields = ("edition", "run_size", "bound_with")

    class CreatePrinting(DjangoModelFormMutation):
        class Meta:
            form_class = PrintingForm
            operation = "create"
            permission_classes = []

    @strawberry.type
    class Mutation:
        create_printing = DjangoMutationField(CreatePrinting)

    assert registry.get(models.Edition) is EditionNode
    assert registry.get(models.Printing) is PrintingNode
    return _schema(Mutation)


@pytest.mark.django_db
@pytest.mark.parametrize("member", ["hidden-empty", "visible-empty", "visible-text"])
def test_form_raw_text_m2m_members_are_decoded_even_when_the_key_is_empty(member: str) -> None:
    """An empty ISBN element is decoded like text: hidden refuses, visible attaches, never clears."""
    publisher = models.Publisher.objects.create(name="Form publisher", house_code="FORM")
    empty = models.Edition.objects.create(isbn_13="", isbn_10="0000000000", publisher=publisher)
    shown = models.Edition.objects.create(isbn_13="9780000000268", publisher=publisher)
    schema = _printing_schema(hides_empty=member == "hidden-empty")
    selected = shown.pk if member == "visible-text" else empty.pk
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            "mutation($d: PrintingFormInput!){ createPrinting(data:$d){ "
            "node{ runSize } errors{ field messages codes path } } }",
            {"d": {"editionId": shown.pk, "runSize": 1, "boundWith": [selected]}},
        )
    expected: JSONObject = (
        {"node": None, "errors": [_relation_error("boundWith")]}
        if member == "hidden-empty"
        else {"node": {"runSize": 1}, "errors": []}
    )
    assert payload == {"data": {"createPrinting": expected}}
    assert list(models.Printing.objects.values_list("run_size", "edition_id")) == (
        [] if member == "hidden-empty" else [(1, shown.pk)]
    )
    assert list(
        models.Printing.bound_with.through.objects.values_list("edition_id", flat=True),
    ) == ([] if member == "hidden-empty" else [selected])
    if member == "hidden-empty":
        reads = [
            query["sql"]
            for query in captured.captured_queries
            if query["sql"].lstrip().upper().startswith("SELECT")
            and 'FROM "library_edition"' in query["sql"]
        ]
        assert len(reads) == 2 + post_lock_rereads(1), reads
        assert not [
            query["sql"]
            for query in captured.captured_queries
            if query["sql"].lstrip().upper().startswith("INSERT")
            and '"library_printing"' in query["sql"]
        ]
