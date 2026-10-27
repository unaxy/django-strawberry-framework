"""Form-mutation resolver-pipeline tests.

Package-only: construction hooks, decode helpers, reconstruction internals,
throwaway-schema branches a shipped mutation cannot express, and fail-closed
``ConfigurationError`` / ``SyncMisuseError`` / deadline-before-write.

Live HTTP owns the consumer-visible form writes in
``examples/fakeshop/test_query/test_products_api.py`` (``createItemViaForm`` /
``updateItemViaForm`` / file create+omit / ``get_form_kwargs`` inject /
write-time IntegrityError / ``createItemHoldViaForm`` explicit-null FK /
``submitContact`` / ``submitPing`` /
``/graphql-async/``), ``test_library_api.py`` (raw-pk hidden FK+M2M,
``to_field_name`` write, omitted M2M preserve, explicit-null required M2M,
``perform_mutate`` write + IntegrityError rollback, explicit-null blank integer
choice column ``tier`` -> field-keyed ``null``), and
``test_uploads_api.py`` (ImageField form multipart).

Kept here because no shipped mutation carries them: Relay-GlobalID M2M
visibility (``GenreType`` has no hide hook), ``Meta.fields``-narrowed update,
``get_form``-only construction, request-scoped ``ModelChoiceField`` queryset vs
generated-input identity, NullBoolean UNSET omit (shipped
``setCardItemComplete.complete`` is ``required=False``, a weaker claim; the
Django-default-required omit needs a throwaway form, and a live holder cannot
declare ``DjangoFormMutation`` after the acceptance finalize), required extra
field on a partial input, a prefixed form whose ``add_prefix`` the consumer overrides
or whose ``get_form_kwargs`` binds its own prefixed copy of only ``data`` or only
``files`` (fakeshop's prefixed forms keep Django's ``add_prefix`` and bind both or
neither), ``to_field_name`` reconstruction (including an M2M member
whose ``to_field_name`` value is ``""``), a raw-pk M2M element ``""`` decoded through a
hiding text-keyed type (no fakeshop text-keyed type hides a row), ImageField
reconstruction key absence, decode-helper envelopes, optimizer
``dst_optimizer_plan`` re-fetch plan (spec-035 G2: no projection introduced under a
mutation), and the save-time rule for a ``blank=True, null=False``
column the form cleans to a value it cannot store (``None``, foreign key included, or
``""`` on a column that stores no empty string) over the shapes fakeshop has no column
for: ``""`` on a non-text choice column (omitted with no default, decimal / date, update
``null``, a filling-in model ``save()``, an unrelated consumer ``ValueError``), ``""`` on a
PostgreSQL ``ArrayField`` an optional single-value form field cleans (fakeshop carries no
``ArrayField``: it runs on SQLite), beside an unrelated ``DataError``, and ``None``
where fakeshop's live ``createItemHoldViaForm`` does not reach it (a plain integer
column sent ``null``, omitted or updated to ``null``, a filling-in model ``save()``,
and an ``ItemHold`` update sending ``itemId: null``, which no fakeshop form offers), and
the keying of a save-time Django ``ValidationError`` by a name fakeshop's own
``Item.save()`` rule never raises (a relation ``attname``, a name only the form
declares, a dotted name): the ``ModelForm`` reads it against the backing model, the
model-less plain form against its own form fields. A ``ModelForm.save()`` override
doing work only when committing, over a client-assigned key (no fakeshop form
carries one), pins that such a create saves through ``save(commit=False)``. A bound
form whose ``__init__`` or ``get_form`` rebuilds a relation field over another model or
key column is refused before validation; fakeshop's one rebuilt relation field
(``ShelfRelationsForm.branch``) keeps its model and key, so the refusals live here. So
does the schema-build refusal of a class-level relation field over another model on a
form bound as declared, which no finalizing fakeshop schema can carry, with the shapes it
leaves building and writing. So do the
fields whose widget reads several form-data keys (PostgreSQL's ``SplitArrayField``, a
consumer ``MultiValueField``), bound under each key: no fakeshop form declares one, and
fakeshop runs on SQLite, which has no ``ArrayField``; Django's ``SplitDateTimeField`` is
live in ``test_scalars_mutation_api.py``.
"""

from __future__ import annotations

import contextlib
import datetime
import decimal
import functools
import itertools
from collections.abc import Callable, Generator, Iterator
from enum import Enum
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeAlias
from urllib.parse import urlencode

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.products.services import seed_data
from apps.scalars import models as scalars_models
from asgiref.sync import async_to_sync
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DataError, connection, models
from django.db.models.signals import pre_save
from django.http import QueryDict
from django.test.utils import CaptureQueriesContext
from django.utils.datastructures import MultiValueDict
from graphql_client import post_lock_rereads
from strawberry import relay
from strawberry.types import ExecutionResult
from strawberry.types.base import get_object_definition
from strawberry.types.enum import StrawberryEnumDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    ResourcePolicy,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms import resolvers as form_resolvers
from django_strawberry_framework.forms.resolvers import (
    _decode_form_relation_multi,
    _is_empty_form_value,
    _reconstruct_partial_data,
    _to_form_key_value,
)
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils import widgets as widgets_module
from django_strawberry_framework.utils._narrowing import (
    dict_of,
    enum_value,
    list_of,
    pk_of,
    read_attr,
    require_instance,
)
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.querysets import SyncMisuseError, visible_related_object
from django_strawberry_framework.utils.typing import call_forwarded, object_result
from tests._generated_inputs import keyword_constructor as _keyword_constructor
from tests._idioms import is_object_dict, is_object_list, saved_pk
from tests._info import make_info, unread_info
from tests._postgres_fields import FakeArrayField, FakeSplitArrayWidget, patch_array_field

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from django.contrib.postgres.fields import ArrayField
    from django.db.models.expressions import Combinable
    from django.forms.utils import _FilesT

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _Text: TypeAlias = models.TextField[str | Combinable, str]


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


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry (co-clears the form + mutation ledgers) per test."""
    registry.clear()
    yield
    registry.clear()


_name_counter = itertools.count(1)


def _uniq(prefix: str) -> str:
    return f"{prefix}-{next(_name_counter)}"


class _AllowAll:
    """A permission class that authorizes every write (isolates the pipeline from auth)."""

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
    """A probe schema over ``mutation_type``, with response-boundary masking OFF.

    This file's subject is the FORM mutation pipeline. Two rows prove it fails
    closed by reading the message the pipeline itself raised - the write-phase
    ``ConfigurationError`` and the relation-hook ``SyncMisuseError`` - and the
    spec-048 error policy would replace both with its stable production message.
    These schemas therefore opt out (``error_policy={"enabled": False}``) instead of
    pretending an in-process probe is a debug deployment; the masking contract is
    pinned in ``tests/test_error_policy.py`` and the live tier.
    """
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_Query,
        mutation=mutation_type,
        extensions=[lambda: optimizer],
        error_policy={"enabled": False},
    )


# ---------------------------------------------------------------------------
# Products Item/Category ModelForm fixtures (FK + unique_item_per_category)
# ---------------------------------------------------------------------------


def _item_model_form() -> type[forms.ModelForm[product_models.Item]]:
    class ItemModelForm(forms.ModelForm[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemModelForm


def _build_item_form_schema(
    *,
    category_get_queryset: object = None,
    item_get_queryset: object = None,
    permission_classes: list[type] | None = None,
    form_class: type[forms.BaseForm] | None = None,
) -> tuple[
    strawberry.Schema,
    tuple[
        type[DjangoType],
        type[DjangoType],
        type[DjangoModelFormMutation],
        type[DjangoModelFormMutation],
    ],
]:
    """Declare Item/Category Relay primaries + a create/update ModelForm mutation."""
    perms = permission_classes if permission_classes is not None else [_AllowAll]

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

    form_cls = form_class or _item_model_form()
    # Build via ``type(...)`` so the ``Meta`` body can carry the parameterized
    # ``permission_classes`` (a nested ``class Meta:`` body cannot read the
    # enclosing function's parameter name).
    create_meta = {"form_class": form_cls, "operation": "create", "permission_classes": perms}
    update_meta = {"form_class": form_cls, "operation": "update", "permission_classes": perms}
    CreateItem = type(
        "CreateItem",
        (DjangoModelFormMutation,),
        {"Meta": type("Meta", (), create_meta)},
    )
    UpdateItem = type(
        "UpdateItem",
        (DjangoModelFormMutation,),
        {"Meta": type("Meta", (), update_meta)},
    )

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    return _schema(Mutation), (
        CategoryT,
        ItemT,
        CreateItem,
        UpdateItem,
    )


_CREATE = (
    "mutation($d: ItemModelFormInput!){ createItem(data:$d){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)

# ---------------------------------------------------------------------------
# decode split: form-key / choice-enum unwrap (unit tier)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_decode_split_relation_lands_under_form_key_not_id_attr() -> None:
    """``categoryId`` decodes to ``{"category": pk}`` in ``provided_data``.

    Wire write-through is
    ``test_products_api.py::test_create_item_via_form_category_id_writes_through_form_category_field``;
    this pins the internal form-key (not ``category_id``).
    """
    (
        _schema,
        (
            CategoryT,
            _ItemT,
            CreateItem,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    input_cls = CreateItem._input_class
    assert input_cls is not None
    data = _keyword_constructor(input_cls)(
        name="X",
        category_id=global_id_for(CategoryT, saved_pk(cat)),
    )
    info = make_info(context=SimpleNamespace())
    provided_data, provided_files, error = form_resolvers._decode_form_data(CreateItem, data, info)
    assert error is None
    # The form key is "category" (the form field name), NOT "category_id".
    assert provided_data["category"] == saved_pk(cat)
    assert "category_id" not in provided_data
    assert provided_files == {}


@pytest.mark.django_db
def test_decode_split_upload_lands_in_files_never_data() -> None:
    """An ``Upload`` field lands in ``provided_files``, never ``provided_data``."""

    class MediaForm(forms.ModelForm[scalars_models.MediaSpecimen]):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("label", "attachment", "image")

    class MediaT(DjangoType):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("id", "label")
            primary = True

    assert registry.get(scalars_models.MediaSpecimen) is MediaT

    class CreateMedia(DjangoModelFormMutation):
        class Meta:
            form_class = MediaForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_media = DjangoMutationField(CreateMedia)

    finalize_django_types()
    _schema(Mutation)
    upload = SimpleUploadedFile("a.txt", b"hello")
    image = SimpleUploadedFile("a.png", b"\x89PNG\r\n")
    input_cls = CreateMedia._input_class
    assert input_cls is not None
    data = _keyword_constructor(input_cls)(label="L", attachment=upload, image=image)
    info = make_info(context=SimpleNamespace())
    provided_data, provided_files, error = form_resolvers._decode_form_data(
        CreateMedia,
        data,
        info,
    )
    assert error is None
    assert set(provided_files) == {"attachment", "image"}
    assert "attachment" not in provided_data
    assert "image" not in provided_data
    assert provided_data == {"label": "L"}


@pytest.mark.django_db
def test_decode_unwraps_choice_enum_to_raw_value() -> None:
    """A scalar choice-enum member is unwrapped to its raw Django value in ``provided_data``."""

    class BookForm(forms.ModelForm[library_models.Book]):
        class Meta:
            model = library_models.Book
            fields = ("title", "circulation_status", "shelf")

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    assert registry.get(library_models.Shelf) is ShelfT

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    assert registry.get(library_models.Book) is BookT

    class CreateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    _schema(Mutation)
    input_cls = CreateBook._input_class
    assert input_cls is not None
    # The circulation_status field resolves to a generated enum; grab the member.
    status_attr = next(
        f.python_name
        for f in get_object_definition(input_cls, strict=True).fields
        if f.python_name.startswith("circulation")
    )
    enum_def = next(
        f.type
        for f in get_object_definition(input_cls, strict=True).fields
        if f.python_name == status_attr
    )
    # Strawberry wraps a choice enum in a ``StrawberryEnumDefinition``; the python
    # enum is ``.wrapped_cls``. Resolve the member whose value is "available".
    assert isinstance(enum_def, StrawberryEnumDefinition)
    enum_cls = enum_def.wrapped_cls
    assert issubclass(enum_cls, Enum)
    member = next(m for m in enum_cls if enum_value(m) == "available")
    data = input_cls(**{status_attr: member, "title": "T", "shelf_id": UNSET})
    info = make_info(context=SimpleNamespace())
    provided_data, _files, error = form_resolvers._decode_form_data(CreateBook, data, info)
    assert error is None
    assert provided_data["circulation_status"] == "available"


# ---------------------------------------------------------------------------
# relation visibility on EVERY branch (Relay x raw-pk, single x multi)
# ---------------------------------------------------------------------------


_M2MSchema: TypeAlias = tuple[
    strawberry.Schema,
    tuple[type[DjangoType], type[DjangoType], type[DjangoType]],
]


def _build_book_m2m_schema(*, genre_relay: bool, genre_get_queryset: object = None) -> _M2MSchema:
    """A ModelForm create over Book with a genres M2M; the Genre primary is Relay or plain."""

    class BookForm(forms.ModelForm[library_models.Book]):
        class Meta:
            model = library_models.Book
            fields = ("title", "shelf", "genres")

    genre_bases = (DjangoType, relay.Node) if genre_relay else (DjangoType,)
    genre_body: dict[str, object] = {
        "Meta": type(
            "Meta",
            (),
            {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
        ),
    }
    if genre_get_queryset is not None:
        genre_body["get_queryset"] = genre_get_queryset
    GenreT = object_result(type, "GenreT", genre_bases, genre_body)
    assert isinstance(GenreT, type)
    assert issubclass(GenreT, DjangoType)

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

    class CreateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


@pytest.mark.django_db
def test_relation_visibility_relay_multi_hidden_rejected() -> None:
    """A hidden Relay-``GlobalID`` M2M member -> field-keyed error (multi branch).

    ``GenreType`` has no hide hook, so no shipped form mutation can feed a hidden
    Relay M2M member. Raw-pk multi hide is live on ``createShelfViaForm``.
    """

    @classmethod
    def hide_all(
        _cls: type[DjangoType],
        qs: models.QuerySet[models.Model],
        _info: object,
    ) -> models.QuerySet[models.Model]:
        return qs.none()

    schema, (GenreT, ShelfT, _BookT) = _build_book_m2m_schema(
        genre_relay=True,
        genre_get_queryset=hide_all,
    )
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    res = schema.execute_sync(
        "mutation($d: BookFormInput!){ createBook(data:$d){ node{ title } errors{ field } } }",
        variable_values={
            "d": {
                "title": "B",
                "shelfId": global_id_for(ShelfT, saved_pk(shelf)),
                "genres": [global_id_for(GenreT, saved_pk(genre))],
            },
        },
    )
    assert res.errors is None, res.errors
    payload = res.data["createBook"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["genres"]


@pytest.mark.django_db
def test_null_boolean_field_omitted_in_mutation_uses_unset_default() -> None:
    """Omitting a ``NullBooleanField`` in the input succeeds at RUNTIME (the UNSET default).

    Baking ``bool | None`` while leaving the input field required would produce
    SDL that lets GraphQL validation accept the omit, then Strawberry would raise
    ``TypeError: missing 1 required keyword-only argument`` when constructing the
    input object. With the field
    widened to ``| None`` + ``UNSET`` the omit reaches the bound form as an
    absent value, and ``NullBooleanField`` resolves it to ``None``. A pure-SDL
    test cannot catch this - only executing the mutation with the field omitted.
    Shipped ``setCardItemComplete.complete`` is ``required=False`` (weaker);
    a live holder cannot declare ``DjangoFormMutation`` after finalize.
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
    res = schema.execute_sync(
        "mutation($d: NullFlagFormInput!){ submit(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"name": "hi"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["submit"]["ok"] is True
    assert captured["flag"] is None


# ---------------------------------------------------------------------------
# get_form_kwargs / get_form hooks
# ---------------------------------------------------------------------------


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
    res = schema.execute_sync(
        "mutation($d: TwoFieldFormKeepInput!){ submit(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"keep": "k"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["submit"]["ok"] is True


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
    ``cleaned_data`` and by identity against the captured instance.
    """

    class TwoFieldForm(forms.Form):
        keep = forms.CharField()
        injected = forms.CharField()  # required, but dropped by Meta.fields below

    built = {}
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
            # basedpyright: get_form's hook signature types files as dict[str, object];
            # django-stubs types the form's files as MultiValueDict[str, UploadedFile]
            built["form"] = TwoFieldForm(data=merged, files=files)  # pyright: ignore[reportArgumentType]
            return built["form"]

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            captured["form"] = form
            captured["injected"] = form.cleaned_data["injected"]

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    # Must NOT raise: the narrowing dropped the required ``injected`` and only
    # ``get_form`` is overridden, so the waiver has to reach through that operand.
    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: TwoFieldFormKeepInput!){ submit(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"keep": "k"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["submit"]["ok"] is True
    assert captured["injected"] == "from-get-form"
    assert captured["form"] is built["form"]


@pytest.mark.django_db
def test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged() -> None:
    """A ``get_form_kwargs`` override scoping a relation queryset changes runtime, not the input.

    Two mutations over ONE form, one plain and one overriding ``get_form_kwargs``
    to pass the request-scoped ``ModelChoiceField`` queryset the form applies in
    its ``__init__``. Both halves are asserted because either alone is
    non-distinguishing: the generated input's NAME and annotation set must be
    identical across the pair (the shape derives from ``get_form_fields()``, never
    from the construction hook), and a category outside the narrowed queryset must
    be rejected by the scoped mutation as a ``FieldError`` keyed to the ``categoryId``
    input the client sent (never the form field name ``category``) while the
    unscoped mutation accepts the same id (so the override demonstrably took
    effect at runtime).
    """

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
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

    def _shape(mutation_cls: type[DjangoFormMutation]) -> tuple[str, set[tuple[str, str]]]:
        assert mutation_cls._input_class is not None
        definition = get_object_definition(mutation_cls._input_class, strict=True)
        return definition.name, {(f.python_name, str(f.type)) for f in definition.fields}

    any_name, any_fields = _shape(PickAnyCategory)
    scoped_name, scoped_fields = _shape(PickScopedCategory)
    assert scoped_name == any_name
    assert scoped_fields == any_fields

    inside = product_models.Category.objects.create(name=_uniq("Inside"))
    outside = product_models.Category.objects.create(name=_uniq("Outside"))
    allowed["queryset"] = product_models.Category.objects.filter(pk=saved_pk(inside))

    outside_id = global_id_for(CategoryT, saved_pk(outside))
    scoped = schema.execute_sync(
        "mutation($d: CategoryPickFormInput!){ pickScoped(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"categoryId": outside_id}},
    )
    assert scoped.errors is None, scoped.errors
    assert scoped.data is not None
    assert scoped.data["pickScoped"]["ok"] is False
    errors = _json_list(scoped.data, "pickScoped", "errors")
    assert [_json_at(error, "field") for error in errors] == ["categoryId"]

    unscoped = schema.execute_sync(
        "mutation($d: CategoryPickFormInput!){ pickAny(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"categoryId": outside_id}},
    )
    assert unscoped.errors is None, unscoped.errors
    assert unscoped.data is not None
    assert unscoped.data["pickAny"]["ok"] is True
    assert unscoped.data["pickAny"]["errors"] == []


# ---------------------------------------------------------------------------
# partial-update reconstruction
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_partial_update_preserves_unprovided_m2m_with_to_field_name() -> None:
    """An omitted M2M whose form field sets ``to_field_name`` survives a partial update.

    The decode lands a PROVIDED M2M as ``to_field_name`` values
    (``_to_form_key_value``); ``model_to_dict`` would reconstruct an OMITTED one as
    related INSTANCES (effectively pks), which a ``ModelMultipleChoiceField`` keyed
    by ``to_field_name`` cannot resolve - so an omitted M2M would spuriously fail
    validation on a one-field update. Reconstruction converts each member by
    ``to_field_name`` too, so omitted and provided M2M bind in the same shape; a
    plain ``model_to_dict`` reconstruction fails this test.
    """

    class BookForm(forms.ModelForm[library_models.Book]):
        genres = forms.ModelMultipleChoiceField(
            queryset=library_models.Genre.objects.all(),
            to_field_name="name",
            required=False,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "shelf", "genres")

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    assert registry.get(library_models.Genre) is GenreT

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    assert registry.get(library_models.Shelf) is ShelfT

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class UpdateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    schema = _schema(Mutation)
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    book.genres.add(genre)
    res = schema.execute_sync(
        "mutation($id: ID!, $d: BookFormPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ title } errors{ field messages } } }",
        variable_values={"id": global_id_for(BookT, saved_pk(book)), "d": {"title": "Renamed"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    payload = _json_object(res.data, "updateBook")
    # The omitted to_field_name M2M did NOT spuriously fail validation.
    assert payload["errors"] == [], payload["errors"]
    assert _json_at(payload, "node", "title") == "Renamed"
    book.refresh_from_db()
    assert list(book.genres.values_list("pk", flat=True)) == [saved_pk(genre)]  # preserved


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("value", "genre_reads"),
    [("omitted", 4), ("supplied", 4)],
)
def test_m2m_member_whose_to_field_name_value_is_empty_stays_linked(
    value: str,
    genre_reads: int,
) -> None:
    """An M2M member whose ``to_field_name`` value is ``""`` is linked, never refused or dropped.

    A single ``ModelChoiceField`` cleans ``""`` to empty before its lookup, so a relation
    keyed ``""`` is refused there; a ``ModelMultipleChoiceField`` looks every member key
    up, ``""`` included, so the same genre named ``""`` binds as a member. An omitted
    ``genres`` is reconstructed to ``[""]`` and kept; a supplied one decodes the genre's
    ``GlobalID`` to ``""`` and links it. Both shapes read the genre table four times (the
    omitted members' reconstruction or the supplied member's decode, then the bound form's
    initial members, the field's lookup and the save's member set), so the empty key costs
    no extra lookup; where rows lock, the supplied member's decode adds its post-lock
    re-read. No fakeshop form keys an M2M by a text column a member can hold ``""`` in.
    """

    class BookForm(forms.ModelForm[library_models.Book]):
        genres = forms.ModelMultipleChoiceField(
            queryset=library_models.Genre.objects.all(),
            to_field_name="name",
            required=False,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class UpdateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    schema = _schema(Mutation)
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    empty = library_models.Genre.objects.create(name="")
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    data: dict[str, object] = {"title": "Renamed"}
    if value == "omitted":
        book.genres.add(empty)
    else:
        data["genres"] = [global_id_for(GenreT, saved_pk(empty))]
    with CaptureQueriesContext(connection) as captured:
        res = schema.execute_sync(
            "mutation($id: ID!, $d: BookFormPartialInput!){ updateBook(id:$id, data:$d){ "
            "node{ title } errors{ field messages } } }",
            variable_values={"id": global_id_for(BookT, saved_pk(book)), "d": data},
        )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["updateBook"] == {"node": {"title": "Renamed"}, "errors": []}
    assert list(book.genres.values_list("pk", flat=True)) == [saved_pk(empty)]
    reads = [
        query["sql"]
        for query in captured.captured_queries
        if query["sql"].startswith("SELECT") and 'FROM "library_genre"' in query["sql"]
    ]
    assert len(reads) == genre_reads + post_lock_rereads(int(value == "supplied")), reads


@pytest.mark.django_db
def test_partial_update_preserves_unprovided_fk_with_to_field_name() -> None:
    """An omitted FK whose form field sets ``to_field_name`` survives a partial update.

    The single-FK twin of the M2M ``to_field_name`` case. The bound
    ``ModelChoiceField(to_field_name="name")`` validates ``patron`` via
    ``queryset.get(name=value)``; ``model_to_dict`` reconstructs an OMITTED FK as the
    stored ``patron_id`` pk, so the bound form would run ``get(name=<pk>)`` ->
    ``DoesNotExist`` -> ``invalid_choice`` and spuriously fail a one-field update,
    even though a PROVIDED unchanged FK (decoded to its ``name``) passes.
    Reconstruction converts an omitted ``to_field_name`` FK by ``to_field_name``
    too (``Patron.name`` is unique, so the name names the one patron).
    """

    class LoanForm(forms.ModelForm[library_models.Loan]):
        patron = forms.ModelChoiceField(
            queryset=library_models.Patron.objects.all(),
            to_field_name="name",
        )

        class Meta:
            model = library_models.Loan
            fields = ("note", "patron")

    class PatronT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Patron
            fields = ("id", "name")
            primary = True

    assert registry.get(library_models.Patron) is PatronT

    class LoanT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Loan
            fields = ("id", "note")
            primary = True

    class UpdateLoan(DjangoModelFormMutation):
        class Meta:
            form_class = LoanForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_loan = DjangoMutationField(UpdateLoan)

    finalize_django_types()
    schema = _schema(Mutation)
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    patron = library_models.Patron.objects.create(name=_uniq("Pa"))
    loan = library_models.Loan.objects.create(book=book, patron=patron, note="Orig")
    res = schema.execute_sync(
        "mutation($id: ID!, $d: LoanFormPartialInput!){ updateLoan(id:$id, data:$d){ "
        "node{ note } errors{ field messages } } }",
        variable_values={"id": global_id_for(LoanT, saved_pk(loan)), "d": {"note": "Renamed"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    payload = _json_object(res.data, "updateLoan")
    # The omitted to_field_name FK did NOT spuriously fail validation.
    assert payload["errors"] == [], payload["errors"]
    assert _json_at(payload, "node", "note") == "Renamed"
    loan.refresh_from_db()
    assert loan.note == "Renamed"
    # the unchanged FK preserved
    assert saved_pk(loan.patron) == saved_pk(patron)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "file_field_name",
    ["attachment", "image"],
)
def test_partial_reconstruction_excludes_every_file_field_flavor(file_field_name: str) -> None:
    """Both a ``FileField`` and its ``ImageField`` subclass stay out of the reconstructed data.

    The exclusion is one ``isinstance(form_field, forms.FileField)``, and
    ``forms.ImageField`` subclasses ``forms.FileField``, so the two flavors are
    driven as separate rows over one form: an omitted column of either kind must
    contribute NO key to the bound ``data=``, while the omitted scalar beside them
    is reconstructed from the row. ``model_to_dict`` would otherwise hand a
    ``FieldFile`` to a field whose value can only arrive through ``files=``.
    """

    class MediaForm(forms.ModelForm[scalars_models.MediaSpecimen]):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("label", "attachment", "image")

    class MediaT(DjangoType):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("id", "label")
            primary = True

    assert registry.get(scalars_models.MediaSpecimen) is MediaT

    class UpdateMedia(DjangoModelFormMutation):
        class Meta:
            form_class = MediaForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_media = DjangoMutationField(UpdateMedia)

    finalize_django_types()
    _schema(Mutation)
    specimen = scalars_models.MediaSpecimen.objects.create(
        label=_uniq("Spec"),
        attachment="scalar_media/files/stored.txt",
        image="scalar_media/images/stored.png",
    )

    reconstructed, unresolved = form_resolvers._reconstruct_partial_data(UpdateMedia, specimen, {})
    assert unresolved == {}
    assert file_field_name not in reconstructed
    assert reconstructed["label"] == specimen.label


def _update_media_file_schema() -> tuple[strawberry.Schema, type[DjangoType]]:
    """Build an ``updateMedia`` ModelForm mutation over every ``MediaSpecimen`` file column."""

    class MediaForm(forms.ModelForm[scalars_models.MediaSpecimen]):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = (
                "label",
                "attachment",
                "image",
                "optional_attachment",
                "spare_image",
            )

    class MediaT(DjangoType, relay.Node):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("id", "label")
            primary = True

    assert registry.get(scalars_models.MediaSpecimen) is MediaT

    class UpdateMedia(DjangoModelFormMutation):
        class Meta:
            form_class = MediaForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_media = DjangoMutationField(UpdateMedia)

    finalize_django_types()
    return _schema(Mutation), MediaT


def _stored_media_specimen() -> scalars_models.MediaSpecimen:
    return scalars_models.MediaSpecimen.objects.create(
        label=_uniq("Spec"),
        attachment="scalar_media/files/stored.txt",
        image="scalar_media/images/stored.png",
        optional_attachment="scalar_media/files/optional.txt",
        spare_image="scalar_media/images/spare.png",
    )


_UPDATE_MEDIA = (
    "mutation($id: ID!, $d: MediaFormPartialInput!){ updateMedia(id:$id, data:$d){ "
    "node{ label } errors{ field codes } } }"
)


@pytest.mark.django_db
def test_update_explicit_null_on_an_optional_file_clears_it() -> None:
    """An explicit ``null`` on an optional file field is Django's clear, never "no change".

    The form flavor binds it through ``files=`` as ``False`` (``_file_clears``), which the
    optional ``FileField`` of the ``blank=True`` column cleans to ``False`` and the model
    field stores as the empty name. The other stored files are untouched.
    """
    schema, media_type = _update_media_file_schema()
    specimen = _stored_media_specimen()
    res = schema.execute_sync(
        _UPDATE_MEDIA,
        variable_values={
            "id": global_id_for(media_type, saved_pk(specimen)),
            "d": {"optionalAttachment": None},
        },
    )
    assert res.errors is None, res.errors
    assert _json_at(res.data, "updateMedia", "errors") == []
    specimen.refresh_from_db()
    assert specimen.optional_attachment.name == ""
    assert specimen.attachment.name == "scalar_media/files/stored.txt"
    assert specimen.spare_image.name == "scalar_media/images/spare.png"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("input_name", "column", "stored"),
    [
        ("attachment", "attachment", "scalar_media/files/stored.txt"),
        ("spareImage", "spare_image", "scalar_media/images/spare.png"),
    ],
    ids=["blank-false-file", "null-true-blank-false-image"],
)
def test_update_explicit_null_on_a_required_file_is_its_required_error(
    input_name: str,
    column: str,
    stored: str,
) -> None:
    """An explicit ``null`` on a required file field is its ``required`` error, not a kept file.

    ``FileField.clean(False, initial)`` validates a required field's ``False`` as ``None``
    and returns the stored file, so ``is_valid()`` passes;
    ``_required_file_clears`` answers it with the form field's ``required`` error, the
    create's answer to the same ``null``. A ``null=True`` column whose form field is
    required (``blank=False``) is no exception. Nothing is written.
    """
    schema, media_type = _update_media_file_schema()
    specimen = _stored_media_specimen()
    res = schema.execute_sync(
        _UPDATE_MEDIA,
        variable_values={
            "id": global_id_for(media_type, saved_pk(specimen)),
            "d": {"label": "renamed", input_name: None},
        },
    )
    assert res.errors is None, res.errors
    assert _json_at(res.data, "updateMedia", "node") is None
    assert _json_at(res.data, "updateMedia", "errors") == [
        {"field": input_name, "codes": ["required"]},
    ]
    label = specimen.label
    specimen.refresh_from_db()
    assert specimen.label == label
    assert read_attr(read_attr(specimen, column), "name") == stored


@pytest.mark.django_db
def test_required_extra_field_omitted_on_update_is_coercion_error() -> None:
    """A required non-model extra field stays required in the partial input.

    Omitting it is a GraphQL coercion error BEFORE the resolver.

    The partial input keeps a required non-model extra field required (it
    is not a model-backed field forced optional). Because a required generated
    field carries NO class default, an omitted required field is rejected at
    variable coercion rather than silently arriving as ``None`` at the resolver and
    surfacing as an in-band ``FieldError`` (which would mask the missing-input error).
    """

    class ConfirmForm(forms.ModelForm[product_models.Item]):
        confirm = forms.CharField()  # required non-model extra field

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Category) is CategoryT

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = ConfirmForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="X", category=cat)
    res = schema.execute_sync(
        "mutation($id: ID!, $d: ConfirmFormPartialInput!){ updateItem(id:$id, data:$d){ "
        "node{ name } errors{ field messages } } }",
        variable_values={"id": global_id_for(ItemT, saved_pk(item)), "d": {"name": "Y"}},
    )
    # The required ``confirm`` is non-null in SDL AND rejects omission at coercion:
    # a top-level error, no in-band envelope (the resolver is never reached).
    assert res.errors is not None
    assert "confirm" in str(res.errors[0]).lower()
    assert res.data is None


# ---------------------------------------------------------------------------
# save-time Django ValidationError keying: ModelForm (backing model) vs plain form (form)
# ---------------------------------------------------------------------------

_ITEM_SAVE_REFUSAL_DISPATCH_UID = "tests.forms.item_save_time_refusal"


@contextlib.contextmanager
def _item_save_refused(error_key: str) -> Generator[None, None, None]:
    """Refuse every ``Item`` save inside the block with a Django error keyed ``error_key``."""

    def _refuse(**_kwargs: object) -> None:
        raise ValidationError({error_key: ValidationError("Refused at save.", code="refused")})

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


class ItemSubmitForm(forms.Form):
    """A model-less form whose field names differ from the ``Item`` columns it writes."""

    item_name = forms.CharField()
    category = forms.ModelChoiceField(queryset=product_models.Category.objects.all())


def _save_refusal_schema(flavor: str) -> tuple[strawberry.Schema, str, str, str]:
    """Build the ``flavor`` mutation writing one ``Item``.

    Returns the schema, the create query, the input name of the ``Item`` name and a
    ``Category`` GlobalID.
    """
    if flavor == "modelform":
        (
            schema,
            (
                CategoryT,
                _ItemT,
                _C,
                _U,
            ),
        ) = _build_item_form_schema()
        query = (
            "mutation($d: ItemModelFormInput!){ createItem(data:$d){ "
            "node{ id } errors{ field messages codes path } } }"
        )
        name_input = "name"
    else:
        CategoryT = type(
            "CategoryT",
            (DjangoType, relay.Node),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
                ),
            },
        )

        class SubmitItem(DjangoFormMutation):
            class Meta:
                form_class = ItemSubmitForm
                permission_classes = [_AllowAll]

            @override
            def perform_mutate(
                self,
                form: forms.BaseForm,
                info: strawberry.Info[object, object],
            ) -> None:
                _ = product_models.Item.objects.create(
                    name=form.cleaned_data["item_name"],
                    category=form.cleaned_data["category"],
                )

        @strawberry.type
        class Mutation:
            create_item = DjangoMutationField(SubmitItem)

        finalize_django_types()
        schema = _schema(Mutation)
        query = (
            "mutation($d: ItemSubmitFormInput!){ createItem(data:$d){ "
            "ok errors{ field messages codes path } } }"
        )
        name_input = "itemName"
    category = product_models.Category.objects.create(name=_uniq("Cat"))
    return schema, query, name_input, global_id_for(CategoryT, saved_pk(category))


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "flavor",
        "error_key",
        "field",
        "path",
    ),
    [
        pytest.param("modelform", "name", "name", ["name"], id="modelform-model-field"),
        pytest.param(
            "modelform",
            "is_private",
            "isPrivate",
            ["isPrivate"],
            id="modelform-multi-word",
        ),
        pytest.param(
            "modelform",
            "category",
            "categoryId",
            ["categoryId"],
            id="modelform-relation",
        ),
        pytest.param(
            "modelform",
            "category_id",
            "categoryId",
            ["categoryId"],
            id="modelform-relation-attname",
        ),
        pytest.param("modelform", "code", "code", ["code"], id="modelform-no-such-model-field"),
        pytest.param(
            "modelform",
            "shelves.1.code",
            "shelves.1.code",
            ["shelves", "1", "code"],
            id="modelform-dotted-name-verbatim",
        ),
        pytest.param("plain", "item_name", "itemName", ["itemName"], id="plain-form-field"),
        pytest.param("plain", "category", "categoryId", ["categoryId"], id="plain-form-relation"),
        pytest.param("plain", "name", "name", ["name"], id="plain-model-field-is-no-form-field"),
        pytest.param(
            "plain",
            "category_id",
            "category_id",
            ["category_id"],
            id="plain-attname-is-no-form-field",
        ),
        pytest.param(
            "plain",
            "shelves.1.code",
            "shelves.1.code",
            ["shelves", "1", "code"],
            id="plain-dotted-name-verbatim",
        ),
    ],
)
def test_save_time_django_validation_error_keys_against_the_flavor_field_set(
    flavor: str,
    error_key: str,
    field: str,
    path: list[str],
) -> None:
    """A save-time Django error keys each name against the flavor's one field set.

    A ``pre_save`` receiver refuses the ``Item`` write with one name. The ``ModelForm``
    reads it as a field of the backing ``Item`` (``save_time_error_key_map``): the
    relation keys to ``categoryId`` under its name and its ``attname``, and a name
    ``Item`` lacks keeps it. The model-less ``DjangoFormMutation`` has no model and
    reads it as a field of its form: ``item_name`` lands on ``itemName``, while the
    ``Item`` columns ``name`` and ``category_id``, which name no form field, keep their
    names. On both, a dotted name is kept verbatim (its ``path`` split at the dots),
    never re-keyed. Nothing is written.
    """
    schema, query, name_input, category_gid = _save_refusal_schema(flavor)
    with _item_save_refused(error_key):
        res = schema.execute_sync(
            query,
            variable_values={"d": {name_input: "Refused", "categoryId": category_gid}},
        )
    assert res.errors is None, res.errors
    failed_slot: dict[str, object] = {"node": None} if flavor == "modelform" else {"ok": False}
    assert res.data == {
        "createItem": {
            **failed_slot,
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
# plain-form ok + errors payload + perform_mutate default / override
# ---------------------------------------------------------------------------


def test_plain_form_pipeline_rides_shared_write_skeleton(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plain form is a decode/write rider of ``run_write_pipeline_sync``, not a second orchestration."""
    seen: dict[str, object] = {}

    def fake_pipeline(
        _mutation_cls: object,
        _info: object,
        _data: object,
        id_: object,
        *,
        decode_step: object,
        write_step: object,
        tail_step: object = None,
    ) -> str:
        seen["id"] = id_
        seen["decode_step"] = decode_step
        seen["write_step"] = write_step
        seen["tail_step"] = tail_step
        return "ridden"

    class PlainForm(forms.Form):
        name = forms.CharField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = PlainForm
            permission_classes = []

    monkeypatch.setattr(form_resolvers, "run_write_pipeline_sync", fake_pipeline)
    result = form_resolvers._run_form_pipeline_sync(
        Submit,
        info=unread_info(),
        data="data",
        id_="unset-id",
    )
    assert result == "ridden"
    assert seen["id"] == "unset-id"
    assert callable(seen["decode_step"])
    assert callable(seen["write_step"])
    assert seen["tail_step"] is None


@pytest.mark.django_db
def test_perform_mutate_override_runs_only_on_success() -> None:
    """The ``perform_mutate`` override runs on a valid submit, NOT on a failing one.

    Live siblings: ``submitContact`` success/fail envelopes and
    ``createBranchWithShelf`` (the write). This throwaway pins the override
    call list, which no shipped form exposes.
    """
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
            calls.append(dict_of(form.cleaned_data)["message"])

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    q = "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field } } }"
    ok_res = schema.execute_sync(q, variable_values={"d": {"message": "go"}})
    assert ok_res.data is not None
    assert ok_res.data["submit"]["ok"] is True
    fail_res = schema.execute_sync(q, variable_values={"d": {"message": "fail"}})
    assert fail_res.data is not None
    assert fail_res.data["submit"]["ok"] is False
    assert calls == ["go"]  # the override ran only on the successful path


@pytest.mark.django_db
def test_plain_form_rejects_write_sql_outside_the_write_phase() -> None:
    """A plain-form ``clean_*`` write on the pinned alias fails closed (write-phase guard).

    The model-less body rides ``pipeline_alias_guard`` + ``pipeline_write_phase``
    like every other write flavor: validation is database-read-only, so an ORM
    create inside ``clean_message`` raises ``ConfigurationError`` rather than
    committing a side effect before ``perform_mutate``.
    """

    class SideEffectForm(forms.Form):
        message = forms.CharField()

        def clean_message(self) -> object:
            product_models.Category.objects.create(name=_uniq("PhaseLeak"))
            return dict_of(self.cleaned_data)["message"]

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = SideEffectForm
            permission_classes = []

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: SideEffectFormInput!){ submit(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"message": "hi"}},
    )
    # Strawberry surfaces the fail-closed ``ConfigurationError`` as a top-level
    # GraphQL error (data nulled) - the same shape a model-flavor phase violation
    # takes through ``DjangoSchema.execute_sync``.
    assert res.errors is not None
    assert "OUTSIDE the mutation's write phase" in str(res.errors[0].message)
    assert res.data is None or res.data.get("submit") is None
    assert not product_models.Category.objects.filter(name__startswith="PhaseLeak").exists()


@pytest.mark.django_db(transaction=True)
def test_plain_form_expired_deadline_rejects_before_perform_mutate_write() -> None:
    """An expired policy stops the model-less write before ``perform_mutate`` or SQL."""
    created: list[str] = []

    class ContactForm(forms.Form):
        message = forms.CharField()

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
            del form, info
            name = _uniq("ExpiredPlainForm")
            product_models.Category.objects.create(name=name)
            created.append(name)

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = DjangoSchema(
        query=_Query,
        mutation=Mutation,
        resource_policy=ResourcePolicy(execution_deadline_seconds=0.000000000001),
        error_policy={"enabled": False},
    )
    with CaptureQueriesContext(connection) as captured:
        result = schema.execute_sync(
            "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field } } }",
            variable_values={"d": {"message": "hi"}},
            context_value={},
        )

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].extensions is not None
    assert result.errors[0].extensions["code"] == "RESOURCE_LIMIT_EXCEEDED"
    assert result.errors[0].extensions["bound"] == "execution_deadline_seconds"
    assert created == []
    assert not any(
        query["sql"]
        .lstrip()
        .upper()
        .startswith(
            (
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
            ),
        )
        for query in captured.captured_queries
    )


@pytest.mark.django_db
def test_sync_create_meeting_async_get_queryset_raises_sync_misuse() -> None:
    """A sync form create meeting an ``async def get_queryset`` on a relation raises ``SyncMisuseError``."""

    async def _async_get_queryset(
        _cls: type[DjangoType],
        qs: models.QuerySet[models.Model],
        _info: object,
    ) -> models.QuerySet[models.Model]:
        return qs

    CategoryT = type(
        "CategoryT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
            ),
            "get_queryset": classmethod(_async_get_queryset),
        },
    )

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Item) is ItemT

    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        "mutation($d: ItemModelFormInput!){ createItem(data:$d){ node{ name } errors{ field } } }",
        variable_values={
            "d": {"name": "X", "categoryId": global_id_for(CategoryT, saved_pk(cat))},
        },
    )
    assert res.errors is not None
    assert any(isinstance(e.original_error, SyncMisuseError) for e in res.errors)


# ---------------------------------------------------------------------------
# Re-fetch plan shape (the ModelForm re-fetch rides the 036 re-fetch path) - load-bearing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modelform_refetch_keeps_select_related_and_introduces_no_projection() -> None:
    """The ModelForm re-fetch plan KEEPS ``select_related`` and introduces no ``.only(...)``.

    ``dst_optimizer_plan`` is not a wire field. Nested ``category { name }`` on
    live ``createItemViaForm`` proves the relation came back; this pins the plan the
    mutation operation builds: the selection's columns recorded, the projection
    flag off.
    """
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    ctx = SimpleNamespace()
    res = schema.execute_sync(
        _CREATE,
        variable_values={
            "d": {"name": "G", "categoryId": global_id_for(CategoryT, saved_pk(cat))},
        },
        context_value=ctx,
    )
    assert res.errors is None, res.errors
    plan = require_instance(read_attr(ctx, "dst_optimizer_plan"), OptimizationPlan)
    # The relation selection (`category { name }`) is planned via select_related.
    assert plan.select_related == ("category",)
    # The columns are recorded; a MUTATION plan never introduces a projection.
    assert plan.introduce_projection is False
    assert plan.only_fields == (
        "id",
        "name",
        "category_id",
        "category__name",
    )


# ---------------------------------------------------------------------------
# ``spec-038-form_mutations-0_0_12`` edge contracts
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_narrowed_update_preserves_excluded_required_fk_and_validates_constraint() -> None:
    """A ``Meta.fields``-narrowed update reconstructs an EXCLUDED required FK from the row.

    The ModelForm declares ``('name', 'category')`` while the update mutation
    narrows the GraphQL input to ``('name',)``. A name-only update must preserve
    the located row's ``category`` (the bound ModelForm validates ``category`` even
    though it is off the wire), and the ``unique_item_per_category`` constraint
    must still validate against that preserved FK.
    """

    class NameCategoryForm(forms.ModelForm[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    assert registry.get(product_models.Category) is CategoryT

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = NameCategoryForm
            operation = "update"
            fields = ("name",)  # narrow the GraphQL input to name only
            permission_classes = [_AllowAll]

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
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="Before", category=cat)

    # 1) the excluded required FK is preserved from the located row.
    res = schema.execute_sync(
        query,
        variable_values={"id": global_id_for(ItemT, saved_pk(item)), "d": {"name": "After"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    payload = _json_object(res.data, "updateItem")
    assert payload["errors"] == []
    assert _json_at(payload, "node", "name") == "After"
    assert _json_at(payload, "node", "category", "name") == cat.name  # category preserved
    item.refresh_from_db()
    assert item.category_id == saved_pk(cat)

    # 2) the preserved FK still feeds composite-uniqueness validation: a name-only
    # update colliding within the preserved category trips unique_item_per_category.
    product_models.Item.objects.create(name="Taken", category=cat)
    res2 = schema.execute_sync(
        query,
        variable_values={"id": global_id_for(ItemT, saved_pk(item)), "d": {"name": "Taken"}},
    )
    assert res2.errors is None, res2.errors
    assert res2.data is not None
    payload2 = _json_object(res2.data, "updateItem")
    assert payload2["node"] is None
    assert NON_FIELD_ERROR_KEY in [
        _json_at(error, "field") for error in _json_list(payload2, "errors")
    ]


@pytest.mark.django_db
def test_decode_relation_single_empty_value_passes_through() -> None:
    """An explicit ``null`` single-relation value passes through unchanged.

    The decode does NOT decide required-ness or report a bogus 'Invalid id' for an
    empty value; it hands the empty value to the bound form, which clears (optional)
    or raises its own field-keyed required error (required).
    """
    field = forms.ModelChoiceField(queryset=product_models.Category.objects.all())
    assert field.queryset is not None
    decoded, error = form_resolvers._decode_form_relation_single(
        None,
        graphql_name="categoryId",
        related_model=field.queryset.model,
        key_attname=None,
        form_field=field,
        info=unread_info(),
    )
    assert error is None
    assert decoded is None


@pytest.mark.django_db
def test_decode_relation_multi_empty_values_return_empty_list() -> None:
    """An explicit ``null`` or empty list on an M2M returns ``[]`` and never iterates ``None``."""
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())
    empties: tuple[None, list[object]] = (None, [])
    for empty in empties:
        assert field.queryset is not None
        decoded, error = form_resolvers._decode_form_relation_multi(
            empty,
            graphql_name="genres",
            related_model=field.queryset.model,
            key_attname=None,
            form_field=field,
            info=unread_info(),
        )
        assert error is None
        assert decoded == []


# ---------------------------------------------------------------------------
# Relation-decode edge branches (no-primary fallback / uncoercible raw pk /
# multi short-circuit) + plain-form decode error + plain async seam
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_visible_related_object_no_primary_uses_default_manager() -> None:
    """With no registered primary type, ``visible_related_object`` scopes via the default manager.

    A relation whose related model has no primary ``DjangoType`` carries no
    visibility contract, so existence is checked against the default manager.
    Driven directly (the autouse fixture leaves the registry empty). The helper
    lives in ``utils/querysets.py`` so the form +
    serializer relation decoders share one object-returning visibility query.
    """
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    assert visible_related_object(library_models.Genre, saved_pk(genre), None) == genre
    assert visible_related_object(library_models.Genre, saved_pk(genre) + 9999, None) is None


@pytest.mark.django_db
def test_decode_form_relation_single_uncoercible_raw_pk_is_field_error() -> None:
    """A raw-pk relation value that does not coerce to the target pk is a field-keyed error.

    The raw-pk branch coerces through the target pk field; an uncoercible value
    (``"abc"`` for an integer pk) is the field-keyed ``FieldError`` BEFORE any
    visibility query.
    """
    field = forms.ModelChoiceField(queryset=library_models.Genre.objects.all())
    assert field.queryset is not None
    value, error = form_resolvers._decode_form_relation_single(
        "abc",
        graphql_name="genre",
        related_model=field.queryset.model,
        key_attname=None,
        form_field=field,
        info=unread_info(),
    )
    assert value is None
    assert error is not None
    assert error.field == "genre"


@pytest.mark.django_db
def test_decode_form_relation_multi_collects_valid_then_short_circuits_on_bad() -> None:
    """An M2M list collects each valid member's form key, and short-circuits on a bad element."""
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())
    # A valid element is decoded, to_field_name-converted (default ``obj.pk``), and collected.
    assert field.queryset is not None
    keys, error = form_resolvers._decode_form_relation_multi(
        [saved_pk(genre)],
        graphql_name="genres",
        related_model=field.queryset.model,
        key_attname=None,
        form_field=field,
        info=unread_info(),
    )
    assert error is None
    assert keys == [saved_pk(genre)]
    # A bad element short-circuits to the field-keyed error.
    keys, error = form_resolvers._decode_form_relation_multi(
        ["abc"],
        graphql_name="genres",
        related_model=field.queryset.model,
        key_attname=None,
        form_field=field,
        info=unread_info(),
    )
    assert keys is None
    assert error is not None
    assert error.field == "genres"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["single", "multi"])
@pytest.mark.parametrize("to_field_name", [None, "label"], ids=["pk-keyed", "key-keyed"])
def test_decode_form_relation_refuses_a_row_whose_stored_key_is_null(
    kind: str,
    to_field_name: str | None,
) -> None:
    """A visible row whose stored ``to_field`` key is ``NULL`` is the relation error.

    The relation stores ``label`` (``NullableScalarSpecimen.label`` stands in for that
    column), which is ``NULL`` on the row, so binding it would store an empty relation.
    That holds whatever the field is keyed by: a pk-keyed field would accept the row, and a
    field keyed by the stored column itself would answer its own ``invalid_choice``; both
    answer the relation error. A row with a label binds its form key.
    """
    keyed = scalars_models.NullableScalarSpecimen.objects.create(label=_uniq("K"))
    unkeyed = scalars_models.NullableScalarSpecimen.objects.create(label=None)
    queryset = scalars_models.NullableScalarSpecimen.objects.all()
    field = (
        forms.ModelChoiceField(queryset=queryset, required=False, to_field_name=to_field_name)
        if kind == "single"
        else forms.ModelMultipleChoiceField(
            queryset=queryset,
            required=False,
            to_field_name=to_field_name,
        )
    )
    decode = (
        form_resolvers._decode_form_relation_single
        if kind == "single"
        else form_resolvers._decode_form_relation_multi
    )

    def run(pk: object) -> tuple[object, object]:
        return decode(
            pk if kind == "single" else [pk],
            graphql_name="partner",
            related_model=scalars_models.NullableScalarSpecimen,
            key_attname="label",
            form_field=field,
            info=unread_info(),
        )

    form_key = saved_pk(keyed) if to_field_name is None else keyed.label
    expected = form_key if kind == "single" else [form_key]
    assert run(saved_pk(keyed)) == (expected, None)
    value, error = run(saved_pk(unkeyed))
    assert value is None
    assert isinstance(error, FieldError)
    assert (error.field, error.messages, error.codes) == (
        "partner",
        ["Invalid id for relation 'partner'."],
        ["invalid"],
    )


@pytest.mark.django_db
def test_plain_form_relation_decode_error_yields_not_ok_envelope() -> None:
    """A plain form's relation id that fails decode -> ``{ ok: false }`` with a field-keyed error.

    The plain-form pipeline short-circuits a relation decode failure to the pinned
    ``{ ok errors }`` envelope (never a top-level error), mirroring the ModelForm
    body's decode-error path.
    """

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class PickForm(forms.Form):
        genre = forms.ModelChoiceField(queryset=library_models.Genre.objects.all())

    class Pick(DjangoFormMutation):
        class Meta:
            form_class = PickForm
            permission_classes = []

    @strawberry.type
    class Mutation:
        pick = DjangoMutationField(Pick)

    finalize_django_types()
    schema = _schema(Mutation)
    library_models.Genre.objects.create(name=_uniq("G"))
    res = schema.execute_sync(
        "mutation($d: PickFormInput!){ pick(data:$d){ ok errors{ field messages } } }",
        # A well-formed GlobalID for a NONEXISTENT genre: decode resolves the type +
        # pk, then the visibility query finds no row -> field-keyed decode error.
        variable_values={"d": {"genreId": global_id_for(GenreT, 999999)}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    payload = _json_object(res.data, "pick")
    assert payload["ok"] is False
    assert [_json_at(error, "field") for error in _json_list(payload, "errors")] == ["genreId"]


@pytest.mark.django_db
def test_decode_form_relation_multi_keeps_a_member_whose_to_field_name_value_is_empty() -> None:
    """A raw-pk M2M member whose ``to_field_name`` value is ``""`` decodes to ``""``, unrefused.

    The member is read once by pk and projected to its name; a ``ModelMultipleChoiceField``
    looks ``""`` up like any member key, so the decode keeps it instead of reporting the
    ``invalid_choice`` a single ``ModelChoiceField`` gives that key.
    """
    empty = library_models.Genre.objects.create(name="")
    field = forms.ModelMultipleChoiceField(
        queryset=library_models.Genre.objects.all(),
        to_field_name="name",
    )
    with CaptureQueriesContext(connection) as captured:
        keys, error = _decode_form_relation_multi(
            [saved_pk(empty)],
            graphql_name="genres",
            related_model=library_models.Genre,
            key_attname=None,
            form_field=field,
            info=unread_info(),
        )
    assert (keys, error) == ([""], None)
    assert len(captured.captured_queries) == 1


def _build_printing_bound_with_schema() -> strawberry.Schema:
    """A ModelForm create over ``Printing`` whose ``bound_with`` names text-keyed editions.

    ``EditionT`` is a non-Relay primary, so ``boundWith`` takes raw ISBN text, and its
    ``get_queryset`` hides every edition whose ISBN is ``""`` or starts with ``hidden``.
    The generated ``bound_with`` field looks its members up by the ISBN pk.
    """

    class PrintingForm(forms.ModelForm[library_models.Printing]):
        class Meta:
            model = library_models.Printing
            fields = ("edition", "run_size", "bound_with")

    class EditionT(DjangoType):
        class Meta:
            model = library_models.Edition
            fields = ("isbn_13",)
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[library_models.Edition],
            info: object,
        ) -> models.QuerySet[library_models.Edition]:
            return queryset.exclude(isbn_13="").exclude(isbn_13__startswith="hidden")

    class PrintingT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Printing
            fields = ("id", "run_size")
            primary = True

    class CreatePrinting(DjangoModelFormMutation):
        class Meta:
            form_class = PrintingForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_printing = DjangoMutationField(CreatePrinting)

    finalize_django_types()
    assert registry.get(library_models.Edition) is EditionT
    assert registry.get(library_models.Printing) is PrintingT
    return _schema(Mutation)


_CREATE_PRINTING = (
    "mutation($d: PrintingFormInput!){ createPrinting(data:$d){ "
    "node{ runSize } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_m2m_raw_pk_element_empty_is_decoded_never_a_clear() -> None:
    """A raw-pk ``boundWith`` element ``""`` names the edition whose ISBN is ``""``, decoded.

    A list element is never a clear: ``""`` is the pk of an edition, so it is type-checked
    and resolved through ``EditionT.get_queryset`` like any member. That edition is hidden,
    so the element is the uniform relation error with nothing written. Bound undecoded, the
    generated (ISBN-keyed) field would link the hidden edition. The edition table is read
    twice: ``editionId`` and the element, each through ``EditionT.get_queryset``, plus the
    visible ``editionId``'s post-lock re-read where rows lock; the refusal precedes any
    form. ``EditionT`` is test-local: no fakeshop text-keyed type hides a row.
    """
    schema = _build_printing_bound_with_schema()
    publisher = library_models.Publisher.objects.create(name=_uniq("Pub"))
    library_models.Edition.objects.create(isbn_13="", isbn_10="0000000000", publisher=publisher)
    shown = library_models.Edition.objects.create(
        isbn_13="9780000000267",
        isbn_10="",
        publisher=publisher,
    )
    shown_pk = require_instance(pk_of(shown), str)
    with CaptureQueriesContext(connection) as captured:
        res = schema.execute_sync(
            _CREATE_PRINTING,
            variable_values={"d": {"editionId": shown_pk, "runSize": 1, "boundWith": [""]}},
        )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["createPrinting"] == {
        "node": None,
        "errors": [{"field": "boundWith", "messages": ["Invalid id for relation 'boundWith'."]}],
    }
    assert not library_models.Printing.objects.exists()
    reads = [q["sql"] for q in captured.captured_queries if 'FROM "library_edition"' in q["sql"]]
    assert len(reads) == 2 + post_lock_rereads(1), reads


@pytest.mark.django_db
def test_m2m_raw_pk_element_naming_a_visible_edition_links_it() -> None:
    """A visible edition named by its raw ISBN links (the control)."""
    schema = _build_printing_bound_with_schema()
    publisher = library_models.Publisher.objects.create(name=_uniq("Pub"))
    shown = library_models.Edition.objects.create(
        isbn_13="9780000000268",
        isbn_10="0000000000",
        publisher=publisher,
    )
    shown_pk = require_instance(pk_of(shown), str)
    res = schema.execute_sync(
        _CREATE_PRINTING,
        variable_values={"d": {"editionId": shown_pk, "runSize": 1, "boundWith": [shown_pk]}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["createPrinting"] == {"node": {"runSize": 1}, "errors": []}
    printing = library_models.Printing.objects.get()
    assert list(printing.bound_with.values_list("isbn_13", flat=True)) == [shown_pk]


def test_decode_form_relation_multi_non_iterable_returns_field_error() -> None:
    """Passing a non-iterable to _decode_form_relation_multi returns a field-keyed error."""
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())
    keys, error = form_resolvers._decode_form_relation_multi(
        12345,
        graphql_name="genres",
        related_model=library_models.Genre,
        key_attname=None,
        form_field=field,
        info=unread_info(),
    )
    assert keys is None
    assert error is not None
    assert error.field == "genres"
    assert error.codes == ["invalid"]


@pytest.mark.django_db
def test_partial_update_reconstruct_with_extra_model_choice_field() -> None:
    """A ModelForm with an extra ModelChoiceField does not crash reconstruction on non-model attrs."""
    cat = product_models.Category.objects.create(name=_uniq("cat"))
    item = product_models.Item.objects.create(name=_uniq("item"), category=cat)
    # basedpyright: the instance attribute the model does not declare is the non-model attr
    # under test
    item.extra_choice = "not a model object"  # pyright: ignore[reportAttributeAccessIssue]

    class CustomItemForm(forms.ModelForm[product_models.Item]):
        extra_choice = forms.ModelChoiceField(
            queryset=product_models.Category.objects.all(),
            to_field_name="name",
            required=False,
        )

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "extra_choice")

    class CustomItemMutation(DjangoModelFormMutation):
        class Meta:
            form_class = CustomItemForm
            operation = "update"

    data, unresolved = form_resolvers._reconstruct_partial_data(
        CustomItemMutation,
        item,
        {"name": "updated"},
    )
    assert unresolved == {}
    assert "extra_choice" not in data
    assert data["name"] == "updated"
    assert data["category"] == saved_pk(cat)


class _CityPicksForm(forms.ModelForm[library_models.Branch]):
    """A ``MultipleChoiceField`` over the single text column ``Branch.city``."""

    city = forms.MultipleChoiceField(choices=[("north", "North")])

    class Meta:
        model = library_models.Branch
        fields = ("name", "city")


def _update_city_picks() -> type[DjangoModelFormMutation]:
    """Declare an update mutation over ``_CityPicksForm``."""

    class UpdateCityPicks(DjangoModelFormMutation):
        class Meta:
            form_class = _CityPicksForm
            operation = "update"

    return UpdateCityPicks


@pytest.mark.django_db
def test_partial_reconstruction_leaves_an_omitted_list_field_over_a_single_value_column_out() -> (
    None
):
    """The stored single value of a list field is never rebound; the form's initial is.

    ``Branch.city`` stores the text the form joined, which the ``MultipleChoiceField``
    refuses, so the reconstruction leaves it out for ``_bind_omitted_shape_disagreeing_initials``.
    """
    branch = library_models.Branch.objects.create(name=_uniq("Br"), city="north")
    data, unresolved = form_resolvers._reconstruct_partial_data(_update_city_picks(), branch, {})
    assert unresolved == {}
    assert data == {"name": branch.name}


@pytest.mark.django_db
@pytest.mark.parametrize(("dropped", "bound"), [(False, {"city": "north"}), (True, {})])
def test_omitted_list_field_binds_the_initial_of_the_field_the_bound_form_declares(
    *,
    dropped: bool,
    bound: dict[str, object],
) -> None:
    """An omitted list field over a single-value column binds the bound form's own initial.

    The initial is read off the field the built form declares, so a field the form's
    ``__init__`` (or a ``get_form`` override) removed binds nothing and is left to the form.
    """
    branch = library_models.Branch.objects.create(name=_uniq("Br"), city="north")
    form = _CityPicksForm(data={"name": "Renamed"}, instance=branch)
    if dropped:
        del form.fields["city"]
    form_resolvers._bind_omitted_shape_disagreeing_initials(
        _update_city_picks(),
        form,
        {"name": "Renamed"},
    )
    assert dict(form.data) == {"name": "Renamed", **bound}


@pytest.mark.django_db
def test_omitted_list_field_initial_joins_an_immutable_query_dict_as_its_values() -> None:
    """A ``QueryDict`` bound form keeps every other field's values and gains the initial's.

    The ``QueryDict`` an HTML form post binds is immutable and holds a list per key, so the
    initial is set on a copy as its list of values; unpacking it into a ``dict`` would bind
    ``name`` as its raw value list.
    """
    branch = library_models.Branch.objects.create(name=_uniq("Br"), city="north")
    posted = QueryDict("name=Renamed")
    form = _CityPicksForm(data=posted, instance=branch)
    form_resolvers._bind_omitted_shape_disagreeing_initials(
        _update_city_picks(),
        form,
        {"name": "Renamed"},
    )
    bound = form.data
    assert isinstance(bound, QueryDict)
    assert bound.getlist("name") == ["Renamed"]
    assert bound.getlist("city") == ["north"]
    assert posted.getlist("city") == []


@pytest.mark.django_db
def test_omitted_list_field_initial_binds_under_the_form_prefix() -> None:
    """A prefixed form reads ``<prefix>-<name>``, so the initial is bound under that key."""
    branch = library_models.Branch.objects.create(name=_uniq("Br"), city="north")
    form = _CityPicksForm(data={"p-name": "Renamed"}, instance=branch, prefix="p")
    form_resolvers._bind_omitted_shape_disagreeing_initials(
        _update_city_picks(),
        form,
        {"name": "Renamed"},
    )
    assert dict(form.data) == {"p-name": "Renamed", "p-city": "north"}


class _PlainTagged(models.Model):
    """An unmanaged owner of a choiceless ``tags`` array column beside a ``title``."""

    title: models.TextField[str | Combinable, str] = models.TextField()
    tags = FakeArrayField(models.TextField())

    class Meta:
        managed = False
        app_label = "test_forms_one_tag"


class _OneTagForm(forms.ModelForm[_PlainTagged]):
    """A single-value ``ChoiceField`` over the ``tags`` array column."""

    tags = forms.ChoiceField(choices=[("x", "X"), ("y", "Y")])

    class Meta:
        model = _PlainTagged
        fields = ("title", "tags")


def _update_one_tag(monkeypatch: pytest.MonkeyPatch) -> type[DjangoModelFormMutation]:
    """Declare an update mutation over ``_OneTagForm``, its column read as an ``ArrayField``."""
    patch_array_field(monkeypatch)

    class UpdateOneTag(DjangoModelFormMutation):
        class Meta:
            form_class = _OneTagForm
            operation = "update"

    return UpdateOneTag


def test_partial_reconstruction_leaves_an_omitted_single_value_field_over_an_array_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stored list of a single-value field over an ``ArrayField`` is never rebound.

    ``tags`` stores the list the form wrapped, which the ``ChoiceField`` refuses, so the
    reconstruction leaves it out for ``_bind_omitted_shape_disagreeing_initials``.
    """
    row = _PlainTagged(pk=1, title="Kept", tags=["x"])
    data, unresolved = form_resolvers._reconstruct_partial_data(
        _update_one_tag(monkeypatch),
        row,
        {},
    )
    assert unresolved == {}
    assert data == {"title": "Kept"}


def test_omitted_single_value_field_over_an_array_binds_the_form_initial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An omitted single-value field over an ``ArrayField`` binds the one value the form presents."""
    row = _PlainTagged(pk=1, title="Kept", tags=["y", "x"])
    form = _OneTagForm(data={"title": "Renamed"}, instance=row, initial={"tags": "y"})
    form_resolvers._bind_omitted_shape_disagreeing_initials(
        _update_one_tag(monkeypatch),
        form,
        {"title": "Renamed"},
    )
    assert dict(form.data) == {"title": "Renamed", "tags": "y"}


@functools.cache
def _pg_tagged_note_model() -> type[models.Model]:
    """Declare the Postgres-tier owner of a real choiceless and a choice ``ArrayField``."""
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415 - needs the Postgres driver

    return type(
        "PgTaggedNote",
        (models.Model,),
        {
            "__module__": __name__,
            "title": models.TextField(),
            "tags": ArrayField(models.TextField()),
            "labels": ArrayField(models.TextField(choices=[("x", "X"), ("y", "Y")])),
            "Meta": type("Meta", (), {"managed": False, "app_label": "test_forms_pg_arrays"}),
        },
    )


def _pg_one_value_form() -> type[forms.ModelForm[models.Model]]:
    """A ``ModelForm`` reading one ``tags`` and one ``labels`` value, each wrapped into a list."""
    note_model = _pg_tagged_note_model()

    class OneValueForm(forms.ModelForm[models.Model]):
        tags = forms.ChoiceField(choices=[("x", "X"), ("y", "Y")])
        labels = forms.ChoiceField(choices=[("x", "X"), ("y", "Y")])

        class Meta:
            model = note_model
            fields = ("title", "tags", "labels")

        def clean_tags(self) -> list[object]:
            return [self.cleaned_data["tags"]]

        def clean_labels(self) -> list[object]:
            return [self.cleaned_data["labels"]]

    return OneValueForm


def _pg_one_value_schema(*, presents_initial: bool) -> strawberry.Schema:
    """Build ``createNote`` / ``updateNote`` over ``_pg_one_value_form``, rows by raw pk.

    With ``presents_initial`` the update hands the form an ``initial`` of each column's
    first stored element (``get_form_kwargs``), the one value the field presents.
    """
    note_form = _pg_one_value_form()
    note_model = _pg_tagged_note_model()

    class NoteT(DjangoType):
        class Meta:
            model = note_model
            fields = ("id", "title")
            primary = True

    assert registry.get(note_model) is NoteT

    class CreateNote(DjangoModelFormMutation):
        class Meta:
            form_class = note_form
            operation = "create"
            permission_classes = [_AllowAll]

    class UpdateNote(DjangoModelFormMutation):
        class Meta:
            form_class = note_form
            operation = "update"
            permission_classes = [_AllowAll]

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
            if presents_initial and instance is not None:
                kwargs["initial"] = {
                    name: list_of(read_attr(instance, name))[0] for name in ("tags", "labels")
                }
            return kwargs

    @strawberry.type
    class Mutation:
        create_note = DjangoMutationField(CreateNote)
        update_note = DjangoMutationField(UpdateNote)

    finalize_django_types()
    return _schema(Mutation)


@contextlib.contextmanager
def _pg_tagged_note_table() -> Generator[type[models.Model], None, None]:
    """Give the unmanaged ``PgTaggedNote`` a real table for the test, then drop it."""
    model = _pg_tagged_note_model()
    with connection.schema_editor() as editor:
        editor.create_model(model)
    try:
        yield model
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(model)


_CREATE_NOTE = (
    "mutation($d: OneValueFormInput!){ createNote(data:$d){ "
    "result{ title } errors{ field messages } } }"
)
_UPDATE_NOTE = (
    "mutation($id: ID!, $d: OneValueFormPartialInput!){ updateNote(id:$id, data:$d){ "
    "result{ title } errors{ field messages } } }"
)


@pytest.mark.pg
@pytest.mark.django_db
def test_single_value_fields_over_array_columns_create_the_wrapped_list() -> None:
    """A create sends one value per field, which ``clean_<field>`` wraps into the stored list."""
    schema = _pg_one_value_schema(presents_initial=True)
    with _pg_tagged_note_table() as model:
        res = schema.execute_sync(
            _CREATE_NOTE,
            variable_values={"d": {"title": "New", "tags": "x", "labels": "y"}},
        )
        assert res.errors is None, res.errors
        assert _json_at(res.data, "createNote") == {"result": {"title": "New"}, "errors": []}
        assert list(model._base_manager.values_list("tags", "labels")) == [(["x"], ["y"])]


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "presents_initial",
        "data",
        "stored",
        "errors",
    ),
    [
        pytest.param(
            True,
            {"tags": "y", "labels": "x"},
            (["y"], ["x"]),
            [],
            id="named",
        ),
        pytest.param(
            True,
            {"title": "Renamed"},
            (["x"], ["y"]),
            [],
            id="omitted",
        ),
        pytest.param(
            False,
            {"title": "Renamed"},
            (["x"], ["y"]),
            [
                {
                    "field": "tags",
                    "messages": [
                        "Select a valid choice. ['x'] is not one of the available choices.",
                    ],
                },
                {
                    "field": "labels",
                    "messages": [
                        "Select a valid choice. ['y'] is not one of the available choices.",
                    ],
                },
            ],
            id="omitted-without-initial",
        ),
    ],
)
def test_single_value_fields_over_array_columns_update(
    data: dict[str, object],
    stored: tuple[list[str], list[str]],
    errors: list[dict[str, object]],
    *,
    presents_initial: bool,
) -> None:
    """An update writes a named value wrapped, and an omitted one from the form's initial.

    An omitted field binds the one value the form's ``__init__`` presents, so the stored
    list is kept; a form presenting none binds the stored list, which the field refuses as
    a field error, and nothing is written.
    """
    schema = _pg_one_value_schema(presents_initial=presents_initial)
    with _pg_tagged_note_table() as model:
        note = model._base_manager.create(title="Old", tags=["x"], labels=["y"])
        res = schema.execute_sync(
            _UPDATE_NOTE,
            variable_values={"id": str(saved_pk(note)), "d": data},
        )
        assert res.errors is None, res.errors
        assert _json_at(res.data, "updateNote", "errors") == errors
        assert list(model._base_manager.values_list("tags", "labels")) == [stored]


@pytest.mark.django_db
def test_partial_update_reconstruct_with_reverse_relation_field() -> None:
    """A ModelForm with a field name matching a reverse relation does not crash reconstruction."""
    cat = product_models.Category.objects.create(name=_uniq("cat"))
    item = product_models.Item.objects.create(name=_uniq("item"), category=cat)

    class CustomItemForm(forms.ModelForm[product_models.Item]):
        entries = forms.ModelChoiceField(
            queryset=product_models.Entry.objects.all(),
            to_field_name="value",
            required=False,
        )

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "entries")

    class CustomItemMutation(DjangoModelFormMutation):
        class Meta:
            form_class = CustomItemForm
            operation = "update"

    data, unresolved = form_resolvers._reconstruct_partial_data(
        CustomItemMutation,
        item,
        {"name": "updated"},
    )
    assert unresolved == {}
    assert "entries" not in data
    assert data["name"] == "updated"
    assert data["category"] == saved_pk(cat)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("to_field_name", "reads"),
    [(None, 0), ("pk", 0), ("code", 1)],
    ids=["pk_keyed_by_default", "pk_keyed_by_name_pk", "keyed_by_another_column"],
)
def test_partial_update_reconstruct_reads_the_related_row_only_off_the_stored_key(
    to_field_name: str | None,
    reads: int,
) -> None:
    """An omitted FK is read back from its related row only when the form key is another column.

    ``Book.shelf`` stores the shelf pk. A declared ``ModelChoiceField`` resolving its
    choice by the pk (no ``to_field_name``, or ``"pk"``) is rebound from the stored value
    with no query; one keyed by ``code`` needs the shelf row, read once, to rebind by its
    code. A field keyed by the target's own name (every generated field) is pinned live by
    ``examples/fakeshop/test_query/test_products_api.py::test_update_item_via_form_non_colliding_partial_update``.
    """
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)

    class BookForm(forms.ModelForm[library_models.Book]):
        shelf = forms.ModelChoiceField(
            queryset=library_models.Shelf.objects.all(),
            to_field_name=to_field_name,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "shelf")

    class UpdateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "update"

    located = library_models.Book.objects.get(pk=saved_pk(book))
    with CaptureQueriesContext(connection) as captured:
        data, unresolved = form_resolvers._reconstruct_partial_data(UpdateBook, located, {})
    assert len(captured.captured_queries) == reads
    assert unresolved == {}
    assert data["shelf"] == (shelf.code if to_field_name == "code" else saved_pk(shelf))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("stored", "reads"),
    [
        ("null", 0),
        ("genre", 1),
        ("dangling", 1),
        ("dangling_select_related", 0),
    ],
)
def test_partial_update_reconstruct_reports_an_unresolvable_stored_key(
    stored: str,
    reads: int,
) -> None:
    """An omitted FK whose stored key names no row is reported, never bound by that key.

    ``PatronProfile.favorite_genre`` stores the genre name; the declared field resolves a
    genre by id, so the omitted field is projected from the related row. A NULL column is
    the form's empty value with no read and a stored genre binds by its id. A stored name
    no genre carries (read through the descriptor, or a ``select_related`` join that
    cached no row) has no id to bind: the field is reported with the form field's own
    ``invalid_choice`` error and left out of the data, so neither the stored name, read
    as an id, nor the empty value, which would clear the relation, is ever bound.
    """
    other = library_models.Genre.objects.create(name=_uniq("Other"))
    genre = library_models.Genre.objects.create(name=str(saved_pk(other)))
    patron = library_models.Patron.objects.create(name=_uniq("Patron"))
    library_models.PatronProfile.objects.create(
        patron=patron,
        favorite_genre=None if stored == "null" else genre,
    )

    class ProfileForm(forms.ModelForm[library_models.PatronProfile]):
        favorite_genre = forms.ModelChoiceField(
            queryset=library_models.Genre.objects.all(),
            required=False,
        )

        class Meta:
            model = library_models.PatronProfile
            fields = ("address_2", "favorite_genre")

    class UpdateProfile(DjangoModelFormMutation):
        class Meta:
            form_class = ProfileForm
            operation = "update"

    profiles = library_models.PatronProfile.objects.all()
    if stored == "dangling_select_related":
        profiles = profiles.select_related("favorite_genre")
    with connection.constraint_checks_disabled():
        if stored.startswith("dangling"):
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM library_genre WHERE id = %s",
                    [saved_pk(genre)],
                )
        try:
            located = profiles.get(pk=saved_pk(patron))
            with CaptureQueriesContext(connection) as captured:
                data, unresolved = form_resolvers._reconstruct_partial_data(
                    UpdateProfile,
                    located,
                    {"address_2": "Suite 9"},
                )
        finally:
            library_models.PatronProfile.objects.filter(pk=saved_pk(patron)).update(
                favorite_genre=None,
            )
    assert len(captured.captured_queries) == reads
    assert data["address_2"] == "Suite 9"
    if stored == "null":
        assert (data["favorite_genre"], unresolved) == (None, {})
    elif stored == "genre":
        assert (data["favorite_genre"], unresolved) == (saved_pk(genre), {})
    else:
        assert "favorite_genre" not in data
        assert list(unresolved) == ["favorite_genre"]
        [error] = unresolved["favorite_genre"]
        assert error.code == "invalid_choice"
        assert (
            error.message
            == ProfileForm.base_fields["favorite_genre"].error_messages["invalid_choice"]
        )
        assert error.params == {"value": genre.name}


def test_to_form_key_value_reads_the_key_off_the_row_and_never_substitutes_the_pk() -> None:
    """The form key is the row's ``to_field_name`` value, or its pk when the field keys by pk.

    The input build admits only ``pk`` or a concrete field
    (``forms/inputs.py::require_readable_choice_keys``), so a name the row cannot answer
    is a programming error that propagates, never a silent fall back to the pk, which the
    form's ``queryset.get(<to_field_name>=pk)`` would resolve to another row.
    """
    row = library_models.Genre(pk=42, name="Poetry")

    def key(to_field_name: str | None) -> object:
        field = forms.ModelChoiceField(
            queryset=library_models.Genre.objects.all(),
            to_field_name=to_field_name,
        )
        return _to_form_key_value(row, field)

    assert key("name") == "Poetry"
    assert key("id") == 42
    assert key("pk") == 42
    assert key(None) == 42
    with pytest.raises(AttributeError):
        _ = key("missing__path")


def test_is_empty_form_value_handles_unhashable_and_typeerror() -> None:
    class FakeField:
        empty_values = {None, ""}

    class UnhashableValue:
        @override
        def __hash__(self) -> int:
            raise TypeError("unhashable")

        @override
        def __eq__(self, other: object) -> bool:
            raise TypeError("cannot compare")

    # basedpyright: a stand-in form field carrying only the slots the code under test reads;
    # _is_empty_form_value types the parameter as forms.Field | None
    assert not _is_empty_form_value(UnhashableValue(), FakeField())  # pyright: ignore[reportArgumentType]


def test_decode_form_relation_multi_rejects_non_collection_sequences() -> None:
    for bad in (
        "123",
        b"bytes",
        bytearray(b"bytes"),
        memoryview(b"view"),
        {"key": "val"},
    ):
        form_field: forms.ModelMultipleChoiceField[models.Model] = forms.ModelMultipleChoiceField(
            queryset=None,
        )
        val, err = _decode_form_relation_multi(
            bad,
            graphql_name="genres",
            related_model=library_models.Genre,
            key_attname=None,
            form_field=form_field,
            info=unread_info(),
        )
        assert val is None
        assert err is not None
        assert err.field == "genres"


@pytest.mark.django_db
def test_decode_form_relation_multi_one_shot_generator_fully_decoded() -> None:
    """A one-shot M2M container is materialized once, then decoded elementwise.

    The decoder consumes the container exactly once (no re-iteration of a
    one-shot iterator) and every member is type-checked + visibility-checked on
    its own branch.
    """
    first = library_models.Genre.objects.create(name=_uniq("G1"))
    second = library_models.Genre.objects.create(name=_uniq("G2"))
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())
    keys, error = form_resolvers._decode_form_relation_multi(
        iter([saved_pk(first), saved_pk(second)]),
        graphql_name="genres",
        related_model=library_models.Genre,
        key_attname=None,
        form_field=field,
        info=unread_info(),
    )
    assert error is None
    assert keys == [saved_pk(first), saved_pk(second)]


@pytest.mark.django_db
def test_decode_form_relation_multi_materializes_before_any_visibility_query() -> None:
    """A partially-consumed M2M container never reaches a visibility query.

    The container is materialized BEFORE any member is decoded, so an iterator
    that raises after its first id propagates its own exception with ZERO
    database queries - a half-consumed id set can never be partially confirmed
    against (or leaked into) the visibility check.
    """
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())

    def _container() -> Iterator[int]:
        yield saved_pk(genre)
        raise RuntimeError("second pull")

    with (
        CaptureQueriesContext(connection) as ctx,
        pytest.raises(RuntimeError, match="second pull"),
    ):
        form_resolvers._decode_form_relation_multi(
            _container(),
            graphql_name="genres",
            related_model=library_models.Genre,
            key_attname=None,
            form_field=field,
            info=unread_info(),
        )
    assert ctx.captured_queries == []


def test_reconstruct_partial_data_m2m_does_not_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    def _dangling(_self: library_models.Book) -> object:
        raise ObjectDoesNotExist("dangling")

    monkeypatch.setattr(library_models.Book, "genres", property(_dangling))

    class BookForm(forms.ModelForm[library_models.Book]):
        genres = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())

        class Meta:
            model = library_models.Book
            fields = ("genres",)

    class BookMutation(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "update"

    data, unresolved = _reconstruct_partial_data(BookMutation, library_models.Book(pk=1), {})
    assert unresolved == {}
    assert "genres" not in data


# ---------------------------------------------------------------------------
# Save-time unstorable ``blank=True, null=False`` column: ``""`` on a non-text choice column
# (``_modelform_save_or_field_errors``)
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _blank_choice_table(model_class: type[models.Model]) -> Generator[None, None, None]:
    """Give a ``managed = False`` synthetic model a real table for the test, then drop it."""
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(model_class)
    try:
        yield
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model_class)


def _blank_choice_schema(
    model_class: type[models.Model],
    fields: tuple[str, ...],
    *,
    type_fields: tuple[str, ...] | None = None,
) -> tuple[strawberry.Schema, str, str]:
    """A non-Relay primary + create / update ModelForm mutations over ``model_class``.

    The primary type selects ``type_fields`` (default ``fields``) beside ``id``, so a form
    may carry a relation whose target has no registered type. Returns the schema and the
    create / update input type names.
    """
    form_class = type(
        f"{model_class.__name__}Form",
        (forms.ModelForm,),
        {"Meta": type("Meta", (), {"model": model_class, "fields": fields})},
    )
    type(
        f"{model_class.__name__}T",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": model_class, "fields": ("id", *(type_fields or fields))},
            ),
        },
    )
    create = type(
        "CreateRow",
        (DjangoModelFormMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"form_class": form_class, "operation": "create", "permission_classes": []},
            ),
        },
    )
    update = type(
        "UpdateRow",
        (DjangoModelFormMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"form_class": form_class, "operation": "update", "permission_classes": []},
            ),
        },
    )

    @strawberry.type
    class Mutation:
        create_row = DjangoMutationField(create)
        update_row = DjangoMutationField(update)

    finalize_django_types()
    assert create._input_class is not None
    assert update._input_class is not None
    return _schema(Mutation), create._input_class.__name__, update._input_class.__name__


def _blank_choice_model(name: str, column: models.Field[object, object]) -> type[models.Model]:
    """A synthetic model: a ``blank=True, null=False`` choice column ``pick`` + a blank text ``note``.

    ``note`` holds ``""`` whenever it is omitted; a text column stores an empty string,
    so it is never the column the save failure is reported under.
    """
    return type(
        name,
        (models.Model,),
        {
            "__module__": __name__,
            "pick": column,
            "note": models.TextField(blank=True),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


_NULL_PICK_ERROR = {"field": "pick", "messages": ["This field cannot be null."], "codes": ["null"]}

# One unattached column per case below: ``_blank_choice_model`` binds each to its own model class.
_INTEGER_PICK_ON_CREATE: models.Field[object, object] = models.IntegerField(
    choices=[(1, "One"), (2, "Two")],
    blank=True,
)
_DECIMAL_PICK: models.Field[object, object] = models.DecimalField(
    max_digits=4,
    decimal_places=2,
    choices=[(decimal.Decimal("1.50"), "Low"), (decimal.Decimal("2.50"), "High")],
    blank=True,
)
_DATE_PICK: models.Field[object, object] = models.DateField(
    choices=[(datetime.date(2026, 1, 1), "New year")],
    blank=True,
)
_INTEGER_PICK_ON_UPDATE: models.Field[object, object] = models.IntegerField(
    choices=[(1, "One"), (2, "Two")],
    blank=True,
)


@pytest.mark.parametrize(
    (
        "column",
        "operation",
        "pick_input",
        "stored",
    ),
    [
        pytest.param(
            _INTEGER_PICK_ON_CREATE,
            "create",
            {},
            None,
            id="integer-create-omitted-no-default",
        ),
        pytest.param(
            _DECIMAL_PICK,
            "create",
            {"pick": None},
            None,
            id="decimal-create-null",
        ),
        pytest.param(
            _DATE_PICK,
            "create",
            {"pick": None},
            None,
            id="date-create-null",
        ),
        pytest.param(
            _INTEGER_PICK_ON_UPDATE,
            "update",
            {"pick": None},
            2,
            id="integer-update-null",
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_modelform_blank_choice_save_failure_is_field_keyed_null_error(
    column: models.Field[object, object],
    operation: str,
    pick_input: dict[str, object],
    stored: object,
) -> None:
    """A ``blank=True, null=False`` non-text choice column cleaned to ``""`` is the ``null`` error.

    Django's form field keeps ``empty_value=""`` on the column, ``Model.clean_fields``
    skips the blank value, and ``form.save()`` refuses it: an integer column's
    ``get_prep_value`` raises ``ValueError``, a decimal / date column's ``to_python``
    raises ``ValidationError``. Each reaches the envelope keyed by the column with
    Django's ``null`` message and code, and the write does not happen (no row on
    create, the stored value unchanged on update). The omitted ``note`` holds ``""``
    too, on a text column that stores it, so it is never reported.
    """
    model_class = _blank_choice_model("BlankPickRow", column)
    with _blank_choice_table(model_class):
        schema, create_input, update_input = _blank_choice_schema(model_class, ("pick", "note"))
        if operation == "create":
            res = schema.execute_sync(
                f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
                "result{ id } errors{ field messages codes } } }",
                variable_values={"d": pick_input},
            )
            payload = res.data and res.data["createRow"]
        else:
            row = model_class.objects.create(pick=stored)
            res = schema.execute_sync(
                f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
                "result{ id } errors{ field messages codes } } }",
                variable_values={"id": str(saved_pk(row)), "d": pick_input},
            )
            payload = res.data and res.data["updateRow"]
        assert res.errors is None, res.errors
        assert payload == {"result": None, "errors": [_NULL_PICK_ERROR]}
        assert list(model_class.objects.values_list("pick", flat=True)) == (
            [] if stored is None else [stored]
        )


@pytest.mark.django_db(transaction=True)
def test_modelform_blank_choice_filled_in_by_model_save_writes() -> None:
    """A model ``save()`` that fills the blank column in writes; nothing guards it beforehand.

    Django keeps ``blank=True, null=False`` so ``save()`` can supply the value
    (django-trac 13776), so the mapping runs only after a failed save: an omitted
    ``pick`` reaches ``save()`` as ``""``, the override stores ``2`` and the row is
    written.
    """

    class FilledPickRow(models.Model):
        pick: _Int = models.IntegerField(choices=[(1, "One"), (2, "Two")], blank=True)

        class Meta:
            app_label = "products"
            managed = False

        @override
        def save(self, *args: object, **kwargs: object) -> None:
            # Django keeps an assigned value unconverted in the instance dict the column's
            # descriptor reads, so the form's cleaned "" is still "" there.
            if vars(self)["pick"] == "":
                self.pick = 2
            call_forwarded(super().save, args, kwargs)

    with _blank_choice_table(FilledPickRow):
        schema, create_input, _ = _blank_choice_schema(FilledPickRow, ("pick",))
        res = schema.execute_sync(
            f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
            "result{ id } errors{ field messages codes } } }",
            variable_values={"d": {}},
        )
        assert res.errors is None, res.errors
        assert res.data is not None
        assert res.data["createRow"]["errors"] == []
        assert list(FilledPickRow.objects.values_list("pick", flat=True)) == [2]


#: The one exception instance the consumer ``save()`` raises, so the test can prove the
#: pipeline re-raised it rather than a replacement carrying the same message.
_CONSUMER_SAVE_ERROR = ValueError("consumer save refused the row")


@pytest.mark.django_db(transaction=True)
def test_modelform_unrelated_save_value_error_propagates() -> None:
    """A consumer ``save()`` ``ValueError`` with no unstorable blank column is not mapped.

    The exception class is the trigger, never the diagnosis: ``pick`` holds a member
    and ``note`` holds ``""`` on a text column (which stores an empty string), so no
    column explains the failure and the consumer's error propagates unchanged: the
    very instance ``save()`` raised reaches the response as the error's original.
    """

    class FailingPickRow(models.Model):
        pick: _Int = models.IntegerField(choices=[(1, "One"), (2, "Two")], blank=True)
        note: _Text = models.TextField(blank=True)

        class Meta:
            app_label = "products"
            managed = False

        @override
        def save(self, *args: object, **kwargs: object) -> None:
            raise _CONSUMER_SAVE_ERROR

    with _blank_choice_table(FailingPickRow):
        schema, create_input, _ = _blank_choice_schema(FailingPickRow, ("pick", "note"))
        res = schema.execute_sync(
            f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
            "result{ id } errors{ field messages codes } } }",
            variable_values={"d": {"pick": "MEMBER_1"}},
        )
        assert res.errors is not None
        assert [error.message for error in res.errors] == ["consumer save refused the row"]
        assert res.errors[0].original_error is _CONSUMER_SAVE_ERROR
        assert not FailingPickRow.objects.exists()


# ---------------------------------------------------------------------------
# Save-time ``""`` on a ``blank=True, null=False`` ``ArrayField`` (PostgreSQL ``DataError``)
# ---------------------------------------------------------------------------

_TAG_CHOICES = [("x", "X"), ("y", "Y")]

_NULL_TAGS_ERROR = {
    "field": "tags",
    "messages": ["This field cannot be null."],
    "codes": ["null"],
    "path": ["tags"],
}


def _blank_tags_model(*, client_key: bool) -> type[models.Model]:
    """A synthetic model: a ``title`` and a ``blank=True, null=False`` text ``ArrayField`` ``tags``.

    With ``client_key`` the row is keyed by a client-assigned text ``code``, so a create
    saves through ``save(commit=False)`` and ``save_new_row``'s INSERT.
    """
    from django.contrib.postgres import fields as postgres_fields  # noqa: PLC0415 - needs the Postgres driver

    tags: ArrayField[list[str], list[str]] = postgres_fields.ArrayField(
        models.TextField(),
        blank=True,
    )
    key: dict[str, models.Field[object, object]] = (
        {"code": models.TextField(primary_key=True)} if client_key else {}
    )
    return type(
        "BlankTagsRow",
        (models.Model,),
        {
            "__module__": __name__,
            "title": models.TextField(),
            "tags": tags,
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
            **key,
        },
    )


def _wrap_a_present_tag(form: forms.BaseForm) -> object:
    """Wrap a non-empty cleaned ``tags`` value into the stored list; leave an empty one as is."""
    value = dict_of(form.cleaned_data)["tags"]
    return [value] if value else value


def _blank_tags_form(
    model_class: type[models.Model],
    kind: str,
    *,
    client_key: bool,
) -> type[forms.BaseForm]:
    """A ``ModelForm`` declaring an optional single-value ``tags`` field of ``kind``.

    ``char-wrapping`` carries a ``clean_tags`` that wraps only a non-empty value, so an
    empty value reaches the instance unwrapped as the field's ``empty_value`` ``""``.
    """
    form_fields: dict[str, Callable[[], forms.Field]] = {
        "choice": lambda: forms.ChoiceField(choices=_TAG_CHOICES, required=False),
        "typed-choice": lambda: forms.TypedChoiceField(choices=_TAG_CHOICES, required=False),
        "char": lambda: forms.CharField(required=False),
        "char-wrapping": lambda: forms.CharField(required=False),
    }
    fields = ("code", "title", "tags") if client_key else ("title", "tags")
    attrs: dict[str, object] = {
        "tags": form_fields[kind](),
        "Meta": type("Meta", (), {"model": model_class, "fields": fields}),
    }
    if kind == "char-wrapping":
        attrs["clean_tags"] = _wrap_a_present_tag
    return type("BlankTagsForm", (forms.ModelForm,), attrs)


def _blank_tags_schema(
    form_class: type[forms.BaseForm],
    model_class: type[models.Model],
    *,
    key: str,
) -> tuple[strawberry.Schema, str, str]:
    """A non-Relay primary + create / update mutations over ``form_class``, with the input names.

    The primary type over ``model_class`` selects its primary key ``key`` and ``title``.
    """
    type(
        "BlankTagsT",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": model_class, "fields": (key, "title")},
            ),
        },
    )
    create = type(
        "CreateRow",
        (DjangoModelFormMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"form_class": form_class, "operation": "create", "permission_classes": []},
            ),
        },
    )
    update = type(
        "UpdateRow",
        (DjangoModelFormMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"form_class": form_class, "operation": "update", "permission_classes": []},
            ),
        },
    )

    @strawberry.type
    class Mutation:
        create_row = DjangoMutationField(create)
        update_row = DjangoMutationField(update)

    finalize_django_types()
    assert create._input_class is not None
    assert update._input_class is not None
    return _schema(Mutation), create._input_class.__name__, update._input_class.__name__


def _execute_in_mode(
    schema: strawberry.Schema,
    query: str,
    variables: dict[str, object],
    *,
    mode: str,
) -> ExecutionResult:
    """Run ``query`` through the sync pipeline, or the async one under ``async_to_sync``.

    ``async_to_sync`` sends the async pipeline's thread-sensitive body back to this thread,
    so both modes write on the test's own connection.
    """
    if mode == "sync":
        return schema.execute_sync(query, variable_values=variables)
    return async_to_sync(schema.execute)(query, variable_values=variables)


_BLANK_TAGS_INPUTS = [
    pytest.param("create", {"title": "New", "tags": ""}, id="create-empty"),
    pytest.param("create", {"title": "New", "tags": None}, id="create-null"),
    pytest.param("create", {"title": "New"}, id="create-omitted"),
    pytest.param(
        "keyed-create",
        {"code": "K1", "title": "New", "tags": ""},
        id="keyed-create-empty",
    ),
    pytest.param(
        "keyed-create",
        {"code": "K1", "title": "New", "tags": None},
        id="keyed-create-null",
    ),
    pytest.param("keyed-create", {"code": "K1", "title": "New"}, id="keyed-create-omitted"),
    pytest.param("update", {"tags": ""}, id="update-empty"),
    pytest.param("update", {"tags": None}, id="update-null"),
]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    "kind",
    [
        "choice",
        "typed-choice",
        "char",
        "char-wrapping",
    ],
)
@pytest.mark.parametrize(("operation", "data"), _BLANK_TAGS_INPUTS)
def test_modelform_blank_array_cleaned_to_empty_string_is_field_keyed_null_error(
    operation: str,
    data: dict[str, object],
    kind: str,
    mode: str,
) -> None:
    """An optional single-value field cleaning ``""`` onto a ``blank=True, null=False`` array is ``null``.

    The form field cleans ``""``, an explicit ``null`` or an omitted create value to its
    ``empty_value`` ``""``; ``ModelForm._post_clean`` writes it onto the instance and
    ``Model.clean_fields`` skips the blank column, so PostgreSQL refuses the save with a
    ``DataError`` (malformed array literal). The ``ModelForm`` save diagnoses the column
    from the instance it attempted: the envelope is keyed by ``tags`` with Django's
    ``null`` message and code, on a create, a client-assigned-key create and an update,
    sync and async. Nothing is written, and the connection still answers the query that
    reads the table afterwards.
    """
    client_key = operation == "keyed-create"
    model_class = _blank_tags_model(client_key=client_key)
    with _blank_choice_table(model_class):
        schema, create_input, update_input = _blank_tags_schema(
            _blank_tags_form(model_class, kind, client_key=client_key),
            model_class,
            key="code" if client_key else "id",
        )
        stored: list[tuple[object, object]] = []
        if operation == "update":
            row = model_class._base_manager.create(title="Old", tags=["x"])
            stored = [("Old", ["x"])]
            query = (
                f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
                "result{ title } errors{ field messages codes path } } }"
            )
            res = _execute_in_mode(schema, query, {"id": str(saved_pk(row)), "d": data}, mode=mode)
            payload = res.data and res.data["updateRow"]
        else:
            query = (
                f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
                "result{ title } errors{ field messages codes path } } }"
            )
            res = _execute_in_mode(schema, query, {"d": data}, mode=mode)
            payload = res.data and res.data["createRow"]
        assert res.errors is None, res.errors
        assert payload == {"result": None, "errors": [_NULL_TAGS_ERROR]}
        assert list(model_class._base_manager.values_list("title", "tags")) == stored


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_modelform_unrelated_save_data_error_propagates(operation: str, mode: str) -> None:
    """A ``DataError`` no column explains propagates unchanged; nothing is written.

    The consumer's ``save()`` runs a cast PostgreSQL refuses (a ``DataError`` the
    database raised) while ``tags`` holds a wrapped list the column stores and
    ``title`` a text value, so no column explains the failure: the exception is the
    trigger, never the diagnosis, and the response carries the ``DataError`` itself.
    """
    from django.contrib.postgres import fields as postgres_fields  # noqa: PLC0415 - needs the Postgres driver

    class CastingTagsRow(models.Model):
        title: _Text = models.TextField(blank=True)
        tags: ArrayField[list[str], list[str]] = postgres_fields.ArrayField(
            models.TextField(),
            blank=True,
        )

        class Meta:
            app_label = "products"
            managed = False

        @override
        def save(self, *args: object, **kwargs: object) -> None:
            with connection.cursor() as cursor:
                cursor.execute("SELECT %s::integer", ["not a number"])
            call_forwarded(super().save, args, kwargs)

    class WrappingTagsForm(forms.ModelForm[CastingTagsRow]):
        tags = forms.CharField(required=False)

        class Meta:
            model = CastingTagsRow
            fields = ("title", "tags")

        def clean_tags(self) -> object:
            return _wrap_a_present_tag(self)

    with _blank_choice_table(CastingTagsRow):
        schema, create_input, update_input = _blank_tags_schema(
            WrappingTagsForm,
            CastingTagsRow,
            key="id",
        )
        if operation == "update":
            [row] = CastingTagsRow._base_manager.bulk_create(
                [CastingTagsRow(title="", tags=["y"])],
            )
            stored: list[tuple[object, object]] = [("", ["y"])]
            query = (
                f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
                "result{ title } errors{ field messages codes } } }"
            )
            variables: dict[str, object] = {"id": str(saved_pk(row)), "d": {"tags": "x"}}
        else:
            stored = []
            query = (
                f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
                "result{ title } errors{ field messages codes } } }"
            )
            variables = {"d": {"title": "", "tags": "x"}}
        res = _execute_in_mode(schema, query, variables, mode=mode)
        assert res.errors is not None
        assert [type(error.original_error) for error in res.errors] == [DataError]
        assert list(CastingTagsRow._base_manager.values_list("title", "tags")) == stored


# ---------------------------------------------------------------------------
# Save-time ``None`` on a ``null=False`` column (``_unstorable_cleaned_fields``)
# ---------------------------------------------------------------------------


def _blank_amount_model(name: str) -> type[models.Model]:
    """A synthetic model: a ``blank=True, null=False`` plain integer column ``amount``.

    The optional ``forms.IntegerField`` Django builds for it cleans an omitted or
    explicit ``null`` to ``None``, which ``Model.clean_fields`` skips.
    """
    return type(
        name,
        (models.Model,),
        {
            "__module__": __name__,
            "amount": models.IntegerField(blank=True),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
        },
    )


_NULL_AMOUNT_ERROR = {
    "field": "amount",
    "messages": ["This field cannot be null."],
    "codes": ["null"],
}


@pytest.mark.parametrize(
    ("operation", "amount_input", "stored"),
    [
        pytest.param("create", {"amount": None}, None, id="create-null"),
        pytest.param("create", {}, None, id="create-omitted"),
        pytest.param("update", {"amount": None}, 7, id="update-null"),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_modelform_none_on_not_null_scalar_is_field_keyed_null_error(
    operation: str,
    amount_input: dict[str, object],
    stored: object,
) -> None:
    """``None`` on a ``blank=True, null=False`` scalar is the column's ``null`` error.

    The save reaches the database's ``NOT NULL`` ``IntegrityError``, which the
    ``ModelForm`` save diagnoses from the instance it attempted: the envelope is keyed
    by the column with Django's ``null`` message and code, never the ``"__all__"``
    ``constraint`` error, and the write does not happen (no row on create, the stored
    value unchanged on update).
    """
    model_class = _blank_amount_model("BlankAmountRow")
    with _blank_choice_table(model_class):
        schema, create_input, update_input = _blank_choice_schema(model_class, ("amount",))
        if operation == "create":
            res = schema.execute_sync(
                f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
                "result{ id } errors{ field messages codes } } }",
                variable_values={"d": amount_input},
            )
            payload = res.data and res.data["createRow"]
        else:
            row = model_class.objects.create(amount=stored)
            res = schema.execute_sync(
                f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
                "result{ id } errors{ field messages codes } } }",
                variable_values={"id": str(saved_pk(row)), "d": amount_input},
            )
            payload = res.data and res.data["updateRow"]
        assert res.errors is None, res.errors
        assert payload == {"result": None, "errors": [_NULL_AMOUNT_ERROR]}
        assert list(model_class.objects.values_list("amount", flat=True)) == (
            [] if stored is None else [stored]
        )


@pytest.mark.django_db(transaction=True)
def test_modelform_none_filled_in_by_model_save_writes() -> None:
    """A model ``save()`` that fills a ``None`` ``null=False`` column in writes.

    The diagnosis runs only after a failed save (django-trac 13776): an explicit
    ``null`` reaches ``save()`` as ``None``, the override stores ``5`` and the row is
    written with no error.
    """

    class FilledAmountRow(models.Model):
        amount: _Int = models.IntegerField(blank=True)

        class Meta:
            app_label = "products"
            managed = False

        @override
        def save(self, *args: object, **kwargs: object) -> None:
            if vars(self)["amount"] is None:
                self.amount = 5
            call_forwarded(super().save, args, kwargs)

    with _blank_choice_table(FilledAmountRow):
        schema, create_input, _ = _blank_choice_schema(FilledAmountRow, ("amount",))
        res = schema.execute_sync(
            f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
            "result{ id } errors{ field messages codes } } }",
            variable_values={"d": {"amount": None}},
        )
        assert res.errors is None, res.errors
        assert res.data is not None
        assert res.data["createRow"]["errors"] == []
        assert list(FilledAmountRow.objects.values_list("amount", flat=True)) == [5]


@pytest.mark.django_db(transaction=True)
def test_modelform_update_null_on_not_null_foreign_key_is_field_keyed_null_error() -> None:
    """An update sending ``itemId: null`` on ``ItemHold.item`` is the ``itemId`` ``null`` error.

    ``item`` is ``blank=True, null=False``: the form's optional ``ModelChoiceField``
    cleans the ``null`` to ``None`` and the forced UPDATE hits ``NOT NULL`` inside
    ``forced_save_or_field_errors``'s savepoint. The error is keyed through the
    backing model's ``item`` to the input's ``itemId``, as the model flavor keys the
    same input, and the stored reference is unchanged. (Fakeshop's live
    ``createItemHoldViaForm`` pins the create; it has no ``ItemHold`` update form.)
    """
    seed_data(1)
    item = product_models.Item.objects.earliest("pk")
    hold = product_models.ItemHold.objects.create(reason="reserved", item=item)
    schema, _, update_input = _blank_choice_schema(
        product_models.ItemHold,
        ("reason", "item"),
        type_fields=("reason",),
    )
    res = schema.execute_sync(
        f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
        "result{ id } errors{ field messages codes } } }",
        variable_values={"id": str(saved_pk(hold)), "d": {"itemId": None}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["updateRow"] == {
        "result": None,
        "errors": [
            {"field": "itemId", "messages": ["This field cannot be null."], "codes": ["null"]},
        ],
    }
    assert list(product_models.ItemHold.objects.values_list("item", flat=True)) == [item.pk]


# ---------------------------------------------------------------------------
# Explicit ``null`` the form coerces to a storable value (``_coerced_null_fields``)
# ---------------------------------------------------------------------------

_NULL_IS_PRIVATE_ERROR = {
    "field": "isPrivate",
    "messages": ["This field cannot be null."],
    "codes": ["null"],
}


@pytest.mark.django_db(transaction=True)
def test_modelform_create_null_boolean_is_field_keyed_null_error() -> None:
    """``isPrivate: null`` on create is the ``isPrivate`` ``null`` error, not a stored ``False``.

    ``CheckboxInput`` reads the bound ``None`` as ``False``, a value the ``null=False``
    column stores, so the save would succeed with a value the client never sent. The
    valid form's instance is checked before the write; no row is written.
    """
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        "mutation($d: ItemModelFormInput!){ createItem(data:$d){ "
        "node{ id } errors{ field messages codes } } }",
        variable_values={
            "d": {
                "name": "NullPrivate",
                "categoryId": global_id_for(CategoryT, saved_pk(cat)),
                "isPrivate": None,
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data == {"createItem": {"node": None, "errors": [_NULL_IS_PRIVATE_ERROR]}}
    assert not product_models.Item.objects.filter(name="NullPrivate").exists()


@pytest.mark.django_db(transaction=True)
def test_modelform_update_null_boolean_leaves_the_stored_value() -> None:
    """``isPrivate: null`` on update over a ``True`` row is the ``null`` error; the row stays ``True``."""
    (
        schema,
        (
            _CategoryT,
            ItemT,
            _C,
            UpdateItem,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="Private", category=cat, is_private=True)
    assert UpdateItem._input_class is not None
    res = schema.execute_sync(
        f"mutation($id: ID!, $d: {UpdateItem._input_class.__name__}!){{ "
        "updateItem(id:$id, data:$d){ node{ id } errors{ field messages codes } } }",
        variable_values={"id": global_id_for(ItemT, saved_pk(item)), "d": {"isPrivate": None}},
    )
    assert res.errors is None, res.errors
    assert res.data == {"updateItem": {"node": None, "errors": [_NULL_IS_PRIVATE_ERROR]}}
    item.refresh_from_db()
    assert item.is_private is True


@pytest.mark.django_db(transaction=True)
def test_modelform_update_null_on_form_required_field_keeps_the_required_error() -> None:
    """``name: null`` on a form-required field fails ``is_valid()`` with ``required`` first.

    The coerced-``null`` check runs only on a valid form, so the form's own error keeps
    its message and code and the stored name is unchanged.
    """
    (
        schema,
        (
            _CategoryT,
            ItemT,
            _C,
            UpdateItem,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="Named", category=cat)
    assert UpdateItem._input_class is not None
    res = schema.execute_sync(
        f"mutation($id: ID!, $d: {UpdateItem._input_class.__name__}!){{ "
        "updateItem(id:$id, data:$d){ node{ id } errors{ field messages codes } } }",
        variable_values={"id": global_id_for(ItemT, saved_pk(item)), "d": {"name": None}},
    )
    assert res.errors is None, res.errors
    assert res.data == {
        "updateItem": {
            "node": None,
            "errors": [
                {"field": "name", "messages": ["This field is required."], "codes": ["required"]},
            ],
        },
    }
    item.refresh_from_db()
    assert item.name == "Named"


def _dotted_prefix_item_form() -> type[forms.ModelForm[product_models.Item]]:
    """An item form under the prefix ``item`` whose ``add_prefix`` joins with a dot."""

    class DottedPrefixItemForm(_item_model_form()):
        prefix = "item"

        @override
        def add_prefix(self, field_name: str) -> str:
            return f"{self.prefix}.{field_name}" if self.prefix else field_name

    return DottedPrefixItemForm


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("is_private", "errors", "stored"),
    [(None, [_NULL_IS_PRIVATE_ERROR], []), (True, [], [True])],
    ids=["explicit-null", "value"],
)
def test_modelform_create_binds_and_reads_through_the_form_add_prefix(
    is_private: object,
    errors: list[dict[str, object]],
    stored: list[bool],
) -> None:
    """A consumer ``add_prefix`` override names the key the package binds and reads.

    The data is re-keyed through the form's own ``add_prefix`` (``item.<name>``, never a
    hand-built ``item-<name>``), so the form reads every value, and the explicit-``null``
    check reads the bound ``None`` under the same key: ``isPrivate: null`` is the ``null``
    error, nothing written; a value is stored.
    """
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema(form_class=_dotted_prefix_item_form())
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        "mutation($d: DottedPrefixItemFormInput!){ createItem(data:$d){ "
        "node{ id } errors{ field messages codes } } }",
        variable_values={
            "d": {
                "name": "DottedPrefix",
                "categoryId": global_id_for(CategoryT, saved_pk(cat)),
                "isPrivate": is_private,
            },
        },
    )
    assert res.errors is None, res.errors
    assert _json_at(res.data, "createItem", "errors") == errors
    written = product_models.Item.objects.filter(name="DottedPrefix")
    assert list(written.values_list("is_private", flat=True)) == stored


def _update_prefixed_media_schema(
    *,
    own: str,
    seen: list[dict[str, object]] | None = None,
) -> tuple[strawberry.Schema, type[DjangoType]]:
    """Build ``updateMedia`` over a ``MediaSpecimen`` form under the prefix ``m``.

    The mutation's ``get_form_kwargs`` binds its own ``m-<name>`` keyed copy of the
    mapping ``own`` names (``"data"`` or ``"files"``) and passes the package's other
    mapping through, so the package re-keys only that one. ``"multivalue"`` binds the
    bare data as the immutable ``QueryDict`` a form post arrives as and the bare files as
    a ``MultiValueDict``, both of which the package re-keys into copies. ``"partial"``
    binds the data keyed ``m-<name>`` beside a bare ``label`` the form never reads, a
    mapping its builder keyed, which the package leaves as bound. ``"source"`` adds a
    bare ``source`` key the form's ``clean()`` reads, which is no form field and so stays
    as bound. ``"kept-files"`` binds its own bare copy of the files and appends it to
    ``seen``, so a test can read it after the write.
    """

    class MediaForm(forms.ModelForm[scalars_models.MediaSpecimen]):
        prefix = "m"

        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("label", "attachment")

        @override
        def clean(self) -> dict[str, object] | None:
            cleaned = super().clean()
            if own == "source" and self.data.get("source") != "api":
                raise ValidationError("The source key was not bound as sent.")
            return cleaned

    class MediaT(DjangoType, relay.Node):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("id", "label")
            primary = True

    class UpdateMedia(DjangoModelFormMutation):
        class Meta:
            form_class = MediaForm
            operation = "update"
            permission_classes = [_AllowAll]

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
            if own == "multivalue":
                kwargs["data"] = QueryDict(urlencode(data))
                kwargs["files"] = MultiValueDict({name: [value] for name, value in files.items()})
                return kwargs
            if own == "source":
                kwargs["data"] = {**data, "source": "api"}
                return kwargs
            if own == "kept-files":
                kept = dict(files)
                if seen is not None:
                    seen.append(kept)
                kwargs["files"] = kept
                return kwargs
            if own == "partial":
                prefixed = {f"m-{name}": value for name, value in data.items()}
                kwargs["data"] = {"label": "unprefixed", **prefixed}
                return kwargs
            bound = data if own == "data" else files
            kwargs[own] = {f"m-{name}": value for name, value in bound.items()}
            return kwargs

    @strawberry.type
    class Mutation:
        update_media = DjangoMutationField(UpdateMedia)

    finalize_django_types()
    return _schema(Mutation), MediaT


_STORED_ATTACHMENT = "scalar_media/files/stored.txt"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "own",
    [
        "data",
        "files",
        "multivalue",
        "partial",
        "source",
    ],
    ids=[
        "consumer-data",
        "consumer-files",
        "multivalue",
        "partial",
        "non-field-key",
    ],
)
@pytest.mark.parametrize(
    ("change", "errors", "new_label"),
    [
        (
            {"label": "renamed", "attachment": None},
            [{"field": "attachment", "codes": ["required"]}],
            None,
        ),
        ({"label": "renamed"}, [], "renamed"),
    ],
    ids=["explicit-null", "file-omitted"],
)
def test_update_under_a_half_rekeyed_prefix_binds_both_mappings(
    own: str,
    change: dict[str, object],
    errors: list[dict[str, object]],
    new_label: str | None,
) -> None:
    """Each of ``data`` / ``files`` is re-keyed on its own, only while it holds no prefixed key.

    A ``get_form_kwargs`` that binds its own prefixed copy of one mapping keeps it as
    bound, and the package re-keys the other; a bare-keyed immutable ``QueryDict`` and
    ``MultiValueDict`` are re-keyed into copies, data holding a prefixed key beside a
    bare one is left as bound, and a key no form field names stays bare beside the
    re-keyed fields. The form reads both: the explicit
    ``attachment: null`` on the required file is its ``required`` error, nothing written,
    and an update omitting the file writes the label and keeps the file.
    """
    schema, media_type = _update_prefixed_media_schema(own=own)
    specimen = _stored_media_specimen()
    label = specimen.label
    res = schema.execute_sync(
        _UPDATE_MEDIA,
        variable_values={"id": global_id_for(media_type, saved_pk(specimen)), "d": change},
    )
    assert res.errors is None, res.errors
    assert _json_at(res.data, "updateMedia", "errors") == errors
    specimen.refresh_from_db()
    assert specimen.label == (new_label or label)
    assert specimen.attachment.name == _STORED_ATTACHMENT


@pytest.mark.django_db
def test_update_under_a_prefix_never_mutates_the_bound_files_mapping() -> None:
    """A files ``dict`` the hook binds and keeps a reference to reads unchanged after the write.

    The package re-keys it into a new mapping it binds in its place, so the hook's dict
    keeps its bare key while the form reads the explicit ``attachment: null`` under the
    prefix and answers the required file's ``required`` error.
    """
    seen: list[dict[str, object]] = []
    schema, media_type = _update_prefixed_media_schema(own="kept-files", seen=seen)
    specimen = _stored_media_specimen()
    res = schema.execute_sync(
        _UPDATE_MEDIA,
        variable_values={
            "id": global_id_for(media_type, saved_pk(specimen)),
            "d": {"attachment": None},
        },
    )
    assert res.errors is None, res.errors
    assert _json_at(res.data, "updateMedia", "errors") == [
        {"field": "attachment", "codes": ["required"]},
    ]
    assert seen == [{"attachment": False}]


# One unattached column per case below: ``_blank_choice_model`` binds each to its own model class.
_TEXT_PICK_ON_CREATE: models.Field[object, object] = models.TextField(
    choices=[("a", "A"), ("b", "B")],
    blank=True,
)
_TEXT_PICK_ON_UPDATE: models.Field[object, object] = models.TextField(
    choices=[("a", "A"), ("b", "B")],
    blank=True,
)


@pytest.mark.parametrize(
    ("column", "operation", "stored"),
    [
        pytest.param(_TEXT_PICK_ON_CREATE, "create", None, id="create"),
        pytest.param(_TEXT_PICK_ON_UPDATE, "update", "a", id="update"),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_modelform_null_on_blank_text_choice_is_field_keyed_null_error(
    column: models.Field[object, object],
    operation: str,
    stored: object,
) -> None:
    """``pick: null`` on a ``blank=True, null=False`` text choice column is the ``null`` error.

    The column's ``TypedChoiceField`` cleans the ``null`` to its ``empty_value`` ``""``,
    which a text column stores, so the save would clear the column the client sent
    ``null`` for. The error is keyed by the column with Django's ``null`` message and
    code and nothing is written. The omitted (create) or reconstructed (update) ``note``
    is not an explicit ``null``, so it is never named.
    """
    model_class = _blank_choice_model("TextPickRow", column)
    with _blank_choice_table(model_class):
        schema, create_input, update_input = _blank_choice_schema(model_class, ("pick", "note"))
        if operation == "create":
            res = schema.execute_sync(
                f"mutation($d: {create_input}!){{ createRow(data:$d){{ "
                "result{ id } errors{ field messages codes } } }",
                variable_values={"d": {"pick": None}},
            )
            payload = res.data and res.data["createRow"]
        else:
            row = model_class.objects.create(pick=stored)
            res = schema.execute_sync(
                f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
                "result{ id } errors{ field messages codes } } }",
                variable_values={"id": str(saved_pk(row)), "d": {"pick": None}},
            )
            payload = res.data and res.data["updateRow"]
        assert res.errors is None, res.errors
        assert payload == {"result": None, "errors": [_NULL_PICK_ERROR]}
        assert list(model_class.objects.values_list("pick", flat=True)) == (
            [] if stored is None else [stored]
        )


@pytest.mark.django_db(transaction=True)
def test_modelform_update_null_on_nullable_column_clears_it() -> None:
    """``pick: null`` on a ``null=True`` integer column stores ``NULL`` with no error.

    The column stores the clear the client sent, so the coerced-``null`` check never
    names it.
    """
    model_class = _blank_choice_model(
        "NullablePickRow",
        models.IntegerField(blank=True, null=True),
    )
    with _blank_choice_table(model_class):
        schema, _, update_input = _blank_choice_schema(model_class, ("pick",))
        row = model_class.objects.create(pick=3)
        res = schema.execute_sync(
            f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){{ "
            "result{ id } errors{ field messages codes } } }",
            variable_values={"id": str(saved_pk(row)), "d": {"pick": None}},
        )
        assert res.errors is None, res.errors
        assert res.data is not None
        assert res.data["updateRow"]["errors"] == []
        assert list(model_class.objects.values_list("pick", flat=True)) == [None]


class _CleanedPrivateForm(forms.ModelForm[product_models.Item]):
    """``clean_is_private`` supplies ``True`` whatever the client sent."""

    class Meta:
        model = product_models.Item
        fields = ("name", "category", "is_private")

    def clean_is_private(self) -> bool:
        return True


class _DisabledPrivateForm(forms.ModelForm[product_models.Item]):
    """A ``disabled`` ``is_private``: the bound value is ignored for the field's initial."""

    is_private = forms.BooleanField(required=False, disabled=True)

    class Meta:
        model = product_models.Item
        fields = ("name", "category", "is_private")


class _UnwrittenPrivateForm(forms.ModelForm[product_models.Item]):
    """A declared ``is_private`` that ``Meta.fields`` leaves out of ``construct_instance``."""

    is_private = forms.BooleanField(required=False)

    class Meta:
        model = product_models.Item
        fields = ("name", "category")


class _ExcludedPrivateForm(forms.ModelForm[product_models.Item]):
    """A declared ``is_private`` that ``Meta.exclude`` leaves out of ``construct_instance``."""

    is_private = forms.BooleanField(required=False)

    class Meta:
        model = product_models.Item
        # ``Meta.exclude`` is the shape under test.
        exclude = ("is_private", "attachment")  # noqa: DJ006


@pytest.mark.parametrize(
    ("shape", "stored", "written"),
    [
        pytest.param("clean_field", False, True, id="clean-field"),
        pytest.param("get_form_kwargs", False, True, id="get-form-kwargs"),
        pytest.param("disabled", False, False, id="disabled"),
        pytest.param("unwritten", True, True, id="unwritten"),
        pytest.param("excluded", True, True, id="excluded"),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_modelform_null_the_consumer_form_resolves_is_written(
    shape: str,
    stored: object,
    written: object,
) -> None:
    """An explicit ``isPrivate: null`` the consumer's form resolves is no ``null`` error.

    Only the form field's own cleaning of the bound ``None`` is refused. A ``clean_is_private``
    supplying ``True``, a ``get_form_kwargs`` override binding ``True`` in place of the
    ``null``, a ``disabled`` field (the bound value ignored for the stored ``False``, the
    value its own cleaning of the ``null`` would give) and a declared field ``Meta.fields``
    or ``Meta.exclude`` leaves out of ``construct_instance`` each succeed, the row holding
    the value the form resolved.
    """
    chosen_form = {
        "clean_field": _CleanedPrivateForm,
        "get_form_kwargs": _item_model_form(),
        "disabled": _DisabledPrivateForm,
        "unwritten": _UnwrittenPrivateForm,
        "excluded": _ExcludedPrivateForm,
    }[shape]

    # The ``category`` relation input needs the target's registered primary type.
    type(
        "CategoryT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
            ),
        },
    )

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = chosen_form
            operation = "update"
            permission_classes = [_AllowAll]

        @override
        def get_form_kwargs(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> dict[str, object]:
            bound = {**data, "is_private": True} if shape == "get_form_kwargs" else data
            return super().get_form_kwargs(info, data=bound, files=files, instance=instance)

    @strawberry.type
    class Mutation:
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    assert UpdateItem._input_class is not None
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="Private", category=cat, is_private=stored)
    res = _schema(Mutation).execute_sync(
        f"mutation($id: ID!, $d: {UpdateItem._input_class.__name__}!){{ "
        "updateItem(id:$id, data:$d){ node{ id } errors{ field codes } } }",
        variable_values={"id": global_id_for(ItemT, saved_pk(item)), "d": {"isPrivate": None}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["updateItem"]["errors"] == []
    item.refresh_from_db()
    assert item.is_private is written


class CommitNoteRow(models.Model):
    """A row Django keys, written through ``CommitOnlyNoteForm``."""

    note: _Text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "products"
        managed = False
        db_table = "tests_forms_commit_note_row"


class KeyedCommitNoteRow(models.Model):
    """``CommitNoteRow`` keyed by the client's ``code`` instead."""

    code: _Text = models.TextField(primary_key=True)
    note: _Text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "products"
        managed = False
        db_table = "tests_forms_keyed_commit_note_row"


#: The notes every ``commit=True`` save of a commit-only form recorded.
_COMMITTED_NOTES: list[str] = []


class CommitOnlyNoteForm(forms.ModelForm[CommitNoteRow]):
    """A ``ModelForm`` whose ``save()`` records the note only when it commits."""

    class Meta:
        model = CommitNoteRow
        fields = ("note",)

    @override
    def save(self, commit: bool = True) -> CommitNoteRow:
        row = super().save(commit=commit)
        if commit:
            _COMMITTED_NOTES.append(row.note)
        return row


class KeyedCommitOnlyNoteForm(forms.ModelForm[KeyedCommitNoteRow]):
    """``CommitOnlyNoteForm`` over the client-keyed ``KeyedCommitNoteRow``."""

    class Meta:
        model = KeyedCommitNoteRow
        fields = ("code", "note")

    @override
    def save(self, commit: bool = True) -> KeyedCommitNoteRow:
        row = super().save(commit=commit)
        if commit:
            _COMMITTED_NOTES.append(row.note)
        return row


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "form_class",
        "model_class",
        "data",
        "committed",
    ),
    [
        (
            CommitOnlyNoteForm,
            CommitNoteRow,
            {"note": "assigned"},
            ["assigned"],
        ),
        (
            KeyedCommitOnlyNoteForm,
            KeyedCommitNoteRow,
            {"code": "K1", "note": "keyed"},
            [],
        ),
    ],
    ids=["assigned_key", "client_key"],
)
def test_modelform_create_over_a_client_key_saves_through_commit_false(
    form_class: type[forms.ModelForm[models.Model]],
    model_class: type[models.Model],
    data: dict[str, object],
    committed: list[str],
) -> None:
    """A client-key create calls the form's ``save(commit=False)`` and saves the row itself.

    On a key Django assigns the create is one ``form.save()``, so an override's
    commit-only work runs. On a client-assigned key the package calls the form's
    ``save()`` with ``commit=False``, INSERTs the returned row and calls
    ``save_m2m()``, as Django's admin does, so that work does not run while the row
    is still written.
    """
    _COMMITTED_NOTES.clear()
    type(
        f"{model_class.__name__}T",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model_class, "fields": "__all__", "primary": True})},
    )
    create = type(
        "CreateRow",
        (DjangoModelFormMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {"form_class": form_class, "operation": "create", "permission_classes": []},
            ),
        },
    )

    @strawberry.type
    class Mutation:
        create_row = DjangoMutationField(create)

    finalize_django_types()
    assert create._input_class is not None
    with _blank_choice_table(model_class):
        res = _schema(Mutation).execute_sync(
            f"mutation($d: {create._input_class.__name__}!){{ createRow(data: $d){{ "
            "errors{ field messages codes } } }",
            variable_values={"d": data},
        )
        notes = list(model_class._base_manager.values_list("note", flat=True))

    assert res.errors is None, res.errors
    assert res.data == {"createRow": {"errors": []}}
    assert notes == [data["note"]]
    assert committed == _COMMITTED_NOTES


# ---------------------------------------------------------------------------
# The bound form's model-choice fields agree with the decode basis
# ---------------------------------------------------------------------------

#: The email that hides a patron from ``_register_hiding_patron_type``'s ``get_queryset``.
_HIDDEN_EMAIL = "hidden@example.test"

#: ``ModelChoiceField`` with its model parameter solved, for a typed ``require_instance``.
_MODEL_CHOICE_FIELD: type[forms.ModelChoiceField[models.Model]] = forms.ModelChoiceField

#: Applied to the bound form at the end of its ``__init__`` (or by a ``get_form`` override).
_Retune: TypeAlias = "Callable[[forms.BaseForm], None]"


def _register_hiding_patron_type() -> None:
    """Register a raw-pk ``Patron`` primary whose ``get_queryset`` hides ``_HIDDEN_EMAIL``."""

    class PatronT(DjangoType):
        class Meta:
            model = library_models.Patron
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[library_models.Patron],
            info: object,
        ) -> models.QuerySet[library_models.Patron]:
            return queryset.exclude(email=_HIDDEN_EMAIL)

    assert registry.get(library_models.Patron) is PatronT


def _model_choice(form: forms.BaseForm, name: str) -> forms.ModelChoiceField[models.Model]:
    """The bound form's model-choice field ``name``."""
    return require_instance(form.fields[name], _MODEL_CHOICE_FIELD)


def _set_key(name: str, key: str | None) -> _Retune:
    """A retune that sets the bound field ``name``'s ``to_field_name`` to ``key``."""

    def retune(form: forms.BaseForm) -> None:
        _model_choice(form, name).to_field_name = key

    return retune


def _set_queryset(name: str, queryset: models.QuerySet[models.Model]) -> _Retune:
    """A retune that assigns the bound field ``name`` the queryset ``queryset``."""

    def retune(form: forms.BaseForm) -> None:
        _model_choice(form, name).queryset = queryset

    return retune


def _loan_patron_form(
    *,
    class_key: str | None,
    retune: _Retune | None,
) -> type[forms.ModelForm[library_models.Loan]]:
    """A ``Loan`` ``ModelForm`` whose ``patron`` keys by ``class_key``, retuned in ``__init__``."""

    class LoanPatronForm(forms.ModelForm[library_models.Loan]):
        patron = forms.ModelChoiceField(
            queryset=library_models.Patron.objects.all(),
            to_field_name=class_key,
        )

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            files: _FilesT | None = None,
            instance: library_models.Loan | None = None,
        ) -> None:
            super().__init__(data=data, files=files, instance=instance)
            if retune is not None:
                retune(self)

        class Meta:
            model = library_models.Loan
            fields = ("patron", "note")

    return LoanPatronForm


def _update_loan_schema(
    loan_form: type[forms.ModelForm[library_models.Loan]],
    *,
    get_form_retune: _Retune | None = None,
) -> tuple[strawberry.Schema, type[DjangoType]]:
    """An ``updateLoan`` schema over ``loan_form``; ``get_form_retune`` runs in ``get_form``."""
    _register_hiding_patron_type()

    class LoanT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Loan
            fields = ("id", "note")
            primary = True

    class UpdateLoan(DjangoModelFormMutation):
        class Meta:
            form_class = loan_form
            operation = "update"
            permission_classes = [_AllowAll]

        @override
        def get_form(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> forms.ModelForm[library_models.Loan]:
            form = super().get_form(info, data=data, files=files, instance=instance)
            if get_form_retune is not None:
                get_form_retune(form)
            return form

    @strawberry.type
    class Mutation:
        update_loan = DjangoMutationField(UpdateLoan)

    finalize_django_types()
    return _schema(Mutation), LoanT


def _loan_rows() -> tuple[library_models.Loan, library_models.Patron, library_models.Patron]:
    """A loan of a visible patron, and a patron ``_register_hiding_patron_type`` hides."""
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    visible = library_models.Patron.objects.create(name=_uniq("Pa"))
    hidden = library_models.Patron.objects.create(name=_uniq("Pa"), email=_HIDDEN_EMAIL)
    loan = library_models.Loan.objects.create(book=book, patron=visible, note="Orig")
    return loan, visible, hidden


#: A refusal probe: the schema, its document and variables, the expected message, and a
#: check that nothing was written.
_Probe: TypeAlias = "tuple[strawberry.Schema, str, dict[str, object], str, Callable[[], None]]"

_UPDATE_LOAN = (
    "mutation($id: ID!, $d: LoanPatronFormPartialInput!){ updateLoan(id:$id, data:$d){ "
    "node{ note } errors{ field } } }"
)
_KEY_ADVICE = (
    "The to_field_name get_form or the form's __init__ sets must name the column "
    "get_form_fields() declares."
)


def _loan_probe(
    *,
    class_key: str | None,
    init_retune: _Retune | None = None,
    get_form_retune: _Retune | None = None,
    send_patron: bool,
    bound_label: str,
    class_label: str,
) -> _Probe:
    """A ``Loan`` update whose bound ``patron`` would resolve the hidden patron.

    ``class_key`` names the key the decode binds (the class-level field's); the hidden
    patron carries the visible one's key under the column the bound field reads instead.
    """
    schema, loan_type = _update_loan_schema(
        _loan_patron_form(class_key=class_key, retune=init_retune),
        get_form_retune=get_form_retune,
    )
    loan, visible, hidden = _loan_rows()
    if class_key is None:
        hidden.name = str(saved_pk(visible))
        hidden.save(update_fields=["name"])
    else:
        visible.name = str(saved_pk(hidden))
        visible.save(update_fields=["name"])
    data: dict[str, object] = {"note": "Changed"}
    if send_patron:
        data["patronId"] = saved_pk(visible)

    def unchanged() -> None:
        loan.refresh_from_db()
        assert (saved_pk(loan.patron), loan.note) == (saved_pk(visible), "Orig")

    message = (
        f"UpdateLoan: the bound form's field 'patron' resolves its choice by {bound_label}, "
        f"but the input binds Patron rows by {class_label}. {_KEY_ADVICE}"
    )
    variables: dict[str, object] = {"id": global_id_for(loan_type, saved_pk(loan)), "d": data}
    return schema, _UPDATE_LOAN, variables, message, unchanged


def _init_sets_key() -> _Probe:
    return _loan_probe(
        class_key=None,
        init_retune=_set_key("patron", "name"),
        send_patron=True,
        bound_label="'name'",
        class_label="its primary key",
    )


def _init_clears_key() -> _Probe:
    return _loan_probe(
        class_key="name",
        init_retune=_set_key("patron", None),
        send_patron=True,
        bound_label="its primary key",
        class_label="'name'",
    )


def _get_form_sets_key() -> _Probe:
    return _loan_probe(
        class_key=None,
        get_form_retune=_set_key("patron", "name"),
        send_patron=True,
        bound_label="'name'",
        class_label="its primary key",
    )


def _omitted_relation_init_sets_key() -> _Probe:
    return _loan_probe(
        class_key=None,
        init_retune=_set_key("patron", "name"),
        send_patron=False,
        bound_label="'name'",
        class_label="its primary key",
    )


def _init_sets_unknown_key() -> _Probe:
    return _loan_probe(
        class_key=None,
        init_retune=_set_key("patron", "nickname"),
        send_patron=True,
        bound_label="a name that is no field of its model",
        class_label="its primary key",
    )


_UPDATE_BOOK_GENRES = (
    "mutation($id: ID!, $d: BookGenresFormPartialInput!){ updateBook(id:$id, data:$d){ "
    "node{ title } errors{ field } } }"
)


def _m2m_init_sets_key() -> _Probe:
    """A ``Book`` update whose bound ``genres`` would link a genre the type hides."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[library_models.Genre],
            info: object,
        ) -> models.QuerySet[library_models.Genre]:
            return queryset.exclude(name__regex=r"^\d+$")

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    retune = _set_key("genres", "name")

    class BookGenresForm(forms.ModelForm[library_models.Book]):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            files: _FilesT | None = None,
            instance: library_models.Book | None = None,
        ) -> None:
            super().__init__(data=data, files=files, instance=instance)
            retune(self)

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

    class UpdateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookGenresForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    assert registry.get(library_models.Genre) is GenreT
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    visible = library_models.Genre.objects.create(name=_uniq("G"))
    library_models.Genre.objects.create(name=str(saved_pk(visible)))

    def unchanged() -> None:
        book.refresh_from_db()
        assert (book.title, list(book.genres.all())) == ("Orig", [])

    message = (
        "UpdateBook: the bound form's field 'genres' resolves its choice by 'name', but the "
        f"input binds Genre rows by its primary key. {_KEY_ADVICE}"
    )
    return (
        _schema(Mutation),
        _UPDATE_BOOK_GENRES,
        {
            "id": global_id_for(BookT, saved_pk(book)),
            "d": {"title": "Changed", "genres": [saved_pk(visible)]},
        },
        message,
        unchanged,
    )


def _plain_init_swaps_model() -> _Probe:
    """A plain form whose bound ``patron`` would hand ``perform_mutate`` a ``Branch``."""
    _register_hiding_patron_type()
    picked: list[object] = []
    retune = _set_queryset("patron", library_models.Branch.objects.all())

    class PickPatronForm(forms.Form):
        patron = forms.ModelChoiceField(queryset=library_models.Patron.objects.all())

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            files: _FilesT | None = None,
        ) -> None:
            super().__init__(data=data, files=files)
            retune(self)

    class PickPatron(DjangoFormMutation):
        class Meta:
            form_class = PickPatronForm
            permission_classes = []

        @override
        def perform_mutate(
            self,
            form: forms.BaseForm,
            info: strawberry.Info[object, object],
        ) -> None:
            del info
            picked.append(dict_of(form.cleaned_data)["patron"])

    @strawberry.type
    class Mutation:
        pick_patron = DjangoMutationField(PickPatron)

    finalize_django_types()
    visible = library_models.Patron.objects.create(name=_uniq("Pa"))
    library_models.Branch.objects.create(pk=saved_pk(visible), name=_uniq("Br"))

    def unchanged() -> None:
        assert picked == []

    message = (
        "PickPatron: the bound form's field 'patron' looks its choice up among Branch rows, "
        "but the input decodes 'patron' ids against Patron. The queryset get_form or the "
        "form's __init__ assigns must be over the model get_form_fields() declares."
    )
    return (
        _schema(Mutation),
        "mutation($d: PickPatronFormInput!){ pickPatron(data:$d){ ok } }",
        {"d": {"patronId": saved_pk(visible)}},
        message,
        unchanged,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "probe",
    [
        _init_sets_key,
        _init_clears_key,
        _get_form_sets_key,
        _omitted_relation_init_sets_key,
        _init_sets_unknown_key,
        _m2m_init_sets_key,
        _plain_init_swaps_model,
    ],
    ids=[
        "init-sets-key",
        "init-clears-key",
        "get-form-sets-key",
        "omitted-relation",
        "unknown-key",
        "many-to-many",
        "plain-form-other-model",
    ],
)
def test_bound_choice_disagreeing_with_the_decode_is_refused_before_validation(
    probe: Callable[[], _Probe],
) -> None:
    """A bound model-choice field over another model or key column refuses the request.

    The decode resolves the visible row and binds the key the class-level field reads off
    it; a bound field rebuilt by ``__init__`` or ``get_form`` would look that key up under
    another column (the hidden patron or genre carries it there) or in another model's
    rows. The request is the fail-closed ``ConfigurationError`` and nothing is written,
    whether the relation is provided, omitted from an update (rebound from the stored
    key), single or many-to-many.
    """
    schema, document, variables, message, unchanged = probe()
    res = schema.execute_sync(document, variable_values=variables)
    assert res.errors is not None
    assert [error.message for error in res.errors] == [message]
    unchanged()


def _plain_pick_schema(
    field: forms.ModelChoiceField[models.Model],
    retune: _Retune,
) -> tuple[strawberry.Schema, list[object]]:
    """A plain form declaring ``field`` as ``pick``, retuned in ``__init__``, and its picks."""
    picked: list[object] = []

    class PickForm(forms.Form):
        pick = field

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            files: _FilesT | None = None,
        ) -> None:
            super().__init__(data=data, files=files)
            retune(self)

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
            picked.append(dict_of(form.cleaned_data)["pick"])

    @strawberry.type
    class Mutation:
        pick = DjangoMutationField(Pick)

    finalize_django_types()
    return _schema(Mutation), picked


#: An admitted pick: the schema, the rows its ``perform_mutate`` picked, the id to send,
#: and the row that id names.
_PickBuild: TypeAlias = "tuple[strawberry.Schema, list[object], object, models.Model]"


def _pick_patron_requeried() -> _PickBuild:
    """``__init__`` reassigns the queryset over the same model: the request-scoped idiom."""
    _register_hiding_patron_type()
    schema, picked = _plain_pick_schema(
        forms.ModelChoiceField(queryset=library_models.Patron.objects.all()),
        _set_queryset("pick", library_models.Patron.objects.exclude(email=_HIDDEN_EMAIL)),
    )
    patron = library_models.Patron.objects.create(name=_uniq("Pa"))
    return schema, picked, saved_pk(patron), patron


def _pick_patron_by_pk_spelling(
    key: str,
) -> Callable[[], _PickBuild]:
    """``__init__`` respells the pk key of a pk-keyed field as ``key``."""

    def build() -> _PickBuild:
        _register_hiding_patron_type()
        schema, picked = _plain_pick_schema(
            forms.ModelChoiceField(queryset=library_models.Patron.objects.all()),
            _set_key("pick", key),
        )
        patron = library_models.Patron.objects.create(name=_uniq("Pa"))
        return schema, picked, saved_pk(patron), patron

    return build


def _pick_card_by_attname() -> _PickBuild:
    """``__init__`` respells a ``patron`` key as its attname ``patron_id``: one column."""

    class CardT(DjangoType):
        class Meta:
            model = library_models.MembershipCard
            fields = ("id", "barcode")
            primary = True

    schema, picked = _plain_pick_schema(
        forms.ModelChoiceField(
            queryset=library_models.MembershipCard.objects.all(),
            to_field_name="patron",
        ),
        _set_key("pick", "patron_id"),
    )
    assert registry.get(library_models.MembershipCard) is CardT
    patron = library_models.Patron.objects.create(name=_uniq("Pa"))
    card = library_models.MembershipCard.objects.create(patron=patron, barcode=_uniq("Bc"))
    return schema, picked, saved_pk(card), card


def _pick_branch_from_a_proxy() -> _PickBuild:
    """``__init__`` looks the name-keyed branch up among ``ProxyBranch`` rows, a subclass."""

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

    schema, picked = _plain_pick_schema(
        forms.ModelChoiceField(queryset=library_models.Branch.objects.all(), to_field_name="name"),
        _set_queryset("pick", library_models.ProxyBranch.objects.all()),
    )
    assert registry.get(library_models.Branch) is BranchT
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    return schema, picked, saved_pk(branch), branch


def _pick_venue_from_a_child_table() -> _PickBuild:
    """``__init__`` looks a pk-keyed venue up among ``LendingDesk`` rows, a multi-table child.

    The child's primary key is its parent link, a different field from the venue's ``id``
    holding the same value, so both read as the one primary key.
    """

    class VenueT(DjangoType):
        class Meta:
            model = library_models.Venue
            fields = ("id", "name")
            primary = True

    schema, picked = _plain_pick_schema(
        forms.ModelChoiceField(queryset=library_models.Venue.objects.all()),
        _set_queryset("pick", library_models.LendingDesk.objects.all()),
    )
    assert registry.get(library_models.Venue) is VenueT
    desk = library_models.LendingDesk.objects.create(name=_uniq("Desk"))
    return schema, picked, saved_pk(desk), desk


@pytest.mark.django_db
@pytest.mark.parametrize(
    "build",
    [
        _pick_patron_requeried,
        _pick_patron_by_pk_spelling("pk"),
        _pick_patron_by_pk_spelling("id"),
        _pick_card_by_attname,
        _pick_branch_from_a_proxy,
        _pick_venue_from_a_child_table,
    ],
    ids=[
        "same-model-queryset",
        "pk-as-pk",
        "pk-as-id",
        "attname",
        "proxy-queryset",
        "multi-table-child-queryset",
    ],
)
def test_bound_choice_agreeing_with_the_decode_links_the_decoded_row(
    build: Callable[[], _PickBuild],
) -> None:
    """A bound field over the target (or a subclass) and the same key column binds as decoded.

    A reassigned queryset over the same model, any spelling of the primary key, a column's
    name or attname, and a subclass of the target (a proxy, or a multi-table child whose
    primary key is its parent link) all resolve the row the decode admitted.
    """
    schema, picked, pk, row = build()
    res = schema.execute_sync(
        "mutation($d: PickFormInput!){ pick(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"pickId": pk}},
    )
    assert res.errors is None, res.errors
    assert res.data == {"pick": {"ok": True, "errors": []}}
    assert [pk_of(require_instance(choice, models.Model)) for choice in picked] == [pk_of(row)]


@pytest.mark.django_db
def test_queryset_less_bound_choice_is_left_to_the_form() -> None:
    """A bound model-choice field with no queryset looks nothing up, so the form decides.

    ``get_form`` clears the bound ``patron`` field's queryset: the agreement check has no
    model to compare, and the form's own validation refuses the cleared relation as
    required, with nothing written.
    """

    def clear_queryset(form: forms.BaseForm) -> None:
        patron = form.fields["patron"]
        assert isinstance(patron, forms.ModelChoiceField)
        patron.queryset = None

    schema, loan_type = _update_loan_schema(
        _loan_patron_form(class_key=None, retune=None),
        get_form_retune=clear_queryset,
    )
    loan, visible, _hidden = _loan_rows()
    res = schema.execute_sync(
        _UPDATE_LOAN,
        variable_values={"id": global_id_for(loan_type, saved_pk(loan)), "d": {"patronId": None}},
    )
    assert res.errors is None, res.errors
    assert res.data == {"updateLoan": {"node": None, "errors": [{"field": "patronId"}]}}
    loan.refresh_from_db()
    assert saved_pk(loan.patron) == saved_pk(visible)


# ---------------------------------------------------------------------------
# A class-level model-choice field over a model its relation column never names
# ---------------------------------------------------------------------------


def _register_primaries(*targets: type[models.Model]) -> None:
    """Register a raw-pk primary ``DjangoType`` exposing ``id`` for each of ``targets``."""
    for target in targets:
        meta = type("Meta", (), {"model": target, "fields": ("id",), "primary": True})
        _ = type(f"{target.__name__}T", (DjangoType,), {"Meta": meta})
        assert registry.get(target) is not None


def _relation_form(
    model: type[models.Model],
    name: str,
    field: forms.Field,
    *others: str,
) -> type[forms.ModelForm[models.Model]]:
    """A ``<Model>Form`` declaring the ``name`` column's field as ``field``, plus ``others``."""
    meta = type("Meta", (), {"model": model, "fields": (*others, name)})
    return type(f"{model.__name__}Form", (forms.ModelForm,), {name: field, "Meta": meta})


def _declare_write(
    form_class: type[forms.ModelForm[models.Model]],
    *,
    operation: str = "create",
    fields: tuple[str, ...] | None = None,
) -> type[DjangoModelFormMutation]:
    """Declare a default-``get_form`` ``ModelForm`` mutation ``Write`` over ``form_class``."""
    meta: dict[str, object] = {
        "form_class": form_class,
        "operation": operation,
        "permission_classes": [_AllowAll],
    }
    if fields is not None:
        meta["fields"] = fields

    class Write(DjangoModelFormMutation):
        Meta = type("Meta", (), meta)

    return Write


def _venue_choice() -> forms.ModelChoiceField[models.Model]:
    """A ``venue`` choice field whose class-level queryset is over ``Patron``, not ``Venue``."""
    return forms.ModelChoiceField(queryset=library_models.Patron.objects.all())


def _class_choice_message(
    form: str,
    name: str,
    queryset_model: str,
    target: str,
) -> str:
    return (
        f"Form {form} field {name!r} looks its choice up among {queryset_model} rows, but the "
        f"input decodes {name!r} ids against {target}, the model its column relates to, so "
        f"every write that binds {name!r} would be refused. Declare the field's queryset over "
        f"{target} or a subclass of it, or assign it in the form's __init__ or the mutation's "
        "get_form."
    )


def _refuse_unrelated_model() -> str:
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    _ = _declare_write(
        _relation_form(library_models.RepairTicket, "venue", _venue_choice(), "code"),
    )
    return _class_choice_message("RepairTicketForm", "venue", "Patron", "Venue")


def _refuse_kiosk_from(queryset: models.QuerySet[models.Model], label: str) -> Callable[[], str]:
    def declare() -> str:
        _register_primaries(library_models.KioskFault, library_models.SelfServeDesk)
        field = forms.ModelChoiceField(queryset=queryset)
        _ = _declare_write(_relation_form(library_models.KioskFault, "kiosk", field, "note"))
        return _class_choice_message("KioskFaultForm", "kiosk", label, "SelfServeDesk")

    return declare


def _refuse_branch_note_from(
    queryset: models.QuerySet[models.Model],
    label: str,
) -> Callable[[], str]:
    def declare() -> str:
        _register_primaries(library_models.BranchNote, library_models.ProxyBranch)
        field = forms.ModelChoiceField(queryset=queryset)
        _ = _declare_write(_relation_form(library_models.BranchNote, "branch", field, "body"))
        return _class_choice_message("BranchNoteForm", "branch", label, "ProxyBranch")

    return declare


def _refuse_many_to_many() -> str:
    _register_primaries(library_models.VenueSponsor, library_models.Venue)
    field = forms.ModelMultipleChoiceField(queryset=library_models.Patron.objects.all())
    _ = _declare_write(_relation_form(library_models.VenueSponsor, "venues", field, "name"))
    return _class_choice_message("VenueSponsorForm", "venues", "Patron", "Venue")


def _refuse_one_to_one() -> str:
    _register_primaries(library_models.VenueBadge, library_models.Venue)
    _ = _declare_write(_relation_form(library_models.VenueBadge, "venue", _venue_choice(), "code"))
    return _class_choice_message("VenueBadgeForm", "venue", "Patron", "Venue")


def _lead_ticket_form() -> type[forms.ModelForm[models.Model]]:
    """A ``Venue`` form whose optional ``lead_ticket`` looks its choice up among patrons."""
    field = forms.ModelChoiceField(queryset=library_models.Patron.objects.all(), required=False)
    return _relation_form(library_models.Venue, "lead_ticket", field, "name")


def _refuse_update_narrowed_out() -> str:
    _register_primaries(library_models.Venue, library_models.RepairTicket)
    _ = _declare_write(_lead_ticket_form(), operation="update", fields=("name",))
    return _class_choice_message("VenueForm", "lead_ticket", "Patron", "RepairTicket")


def _refuse_get_form_kwargs_override() -> str:
    """A ``get_form_kwargs`` override keeps Django's construction, so the field is still copied."""
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    ticket_form = _relation_form(library_models.RepairTicket, "venue", _venue_choice(), "code")

    class Write(DjangoModelFormMutation):
        class Meta:
            form_class = ticket_form
            operation = "create"
            permission_classes = [_AllowAll]

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
            return {**kwargs, "label_suffix": ""}

    _ = Write
    return _class_choice_message("RepairTicketForm", "venue", "Patron", "Venue")


def _declare_rebuilding_write(
    ticket_form: type[forms.ModelForm[models.Model]],
) -> type[DjangoModelFormMutation]:
    """Declare ``RebuildingWrite``, whose ``get_form`` assigns ``venue`` a ``Venue`` queryset."""

    class RebuildingWrite(DjangoModelFormMutation):
        class Meta:
            form_class = ticket_form
            operation = "create"
            permission_classes = [_AllowAll]

        @override
        def get_form(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: models.Model | None = None,
        ) -> forms.ModelForm[models.Model]:
            form = super().get_form(info, data=data, files=files, instance=instance)
            _set_queryset("venue", library_models.Venue.objects.all())(form)
            return form

    return RebuildingWrite


def _refuse_after_a_rebuilding_declaration() -> str:
    """A ``get_form`` override builds the shared input shape first; the default one refuses."""
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    ticket_form = _relation_form(library_models.RepairTicket, "venue", _venue_choice(), "code")
    _ = _declare_rebuilding_write(ticket_form)
    _ = _declare_write(ticket_form)
    return _class_choice_message("RepairTicketForm", "venue", "Patron", "Venue")


def _refuse_model_choice_over_a_scalar_column() -> str:
    """A model-choice field over a column that is no relation is the kind refusal's."""
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    field = forms.ModelChoiceField(queryset=library_models.Venue.objects.all())
    _ = _declare_write(_relation_form(library_models.RepairTicket, "code", field, "venue"))
    return (
        "Form RepairTicketForm field 'code' (ModelChoiceField) is a single-relation field over "
        "the scalar column RepairTicket.code: the input carries the column's value and the form "
        "reads the field's. Declare a form field of the column's kind, or name the field after "
        "no model column; an update binds every declared field, including those Meta.fields / "
        "Meta.exclude leave out of its input."
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "declare",
    [
        _refuse_unrelated_model,
        _refuse_kiosk_from(library_models.LendingDesk.objects.all(), "LendingDesk"),
        _refuse_kiosk_from(library_models.Venue.objects.all(), "Venue"),
        _refuse_branch_note_from(library_models.Branch.objects.all(), "Branch"),
        _refuse_branch_note_from(library_models.VisibleBranch.objects.all(), "VisibleBranch"),
        _refuse_many_to_many,
        _refuse_one_to_one,
        _refuse_update_narrowed_out,
        _refuse_get_form_kwargs_override,
        _refuse_after_a_rebuilding_declaration,
        _refuse_model_choice_over_a_scalar_column,
    ],
    ids=[
        "unrelated-model",
        "multi-table-parent",
        "multi-table-grandparent",
        "proxy-targets-concrete-model",
        "sibling-proxy",
        "many-to-many",
        "one-to-one",
        "update-binds-a-narrowed-out-field",
        "get-form-kwargs-override",
        "default-declaration-after-a-rebuilding-one",
        "scalar-column-kind-refusal",
    ],
)
def test_class_choice_over_a_model_the_column_never_names_is_refused_at_build(
    declare: Callable[[], str],
) -> None:
    """A class-level choice field the request would always refuse fails ``finalize_django_types()``.

    The form binds its class-level fields as declared (no ``__init__`` or ``order_fields``
    override) and the mutation keeps the default ``get_form``, so every write binding the
    field would hit the request-time refusal: the queryset's model is neither the column's
    related model nor a subclass of it (a multi-table parent or grandparent, a proxy
    target's concrete model, a sibling proxy, an unrelated model, single, one-to-one or
    many-to-many). A create refuses a field its input makes required, which every create
    sends; an update refuses every declared field, since its reconstruction binds them all,
    so a field its ``Meta.fields`` leaves out of the input is refused too.
    A ``get_form_kwargs`` override keeps Django's construction; a ``get_form`` override on
    another declaration that built the same input shape first does not exempt this one.
    A model-choice field over a scalar column is left to the kind refusal.
    """
    message = declare()
    with pytest.raises(ConfigurationError) as raised:
        finalize_django_types()
    assert str(raised.value) == message


#: An admitted write: the schema, the ``write`` mutation's inline ``data`` literal, and a
#: check that the row it wrote links the decoded target.
_AdmittedWrite: TypeAlias = "tuple[strawberry.Schema, str, Callable[[], None]]"


def _write_schema(mutation: type[DjangoModelFormMutation]) -> strawberry.Schema:
    """A probe schema exposing ``mutation`` as ``write``, after ``finalize_django_types()``."""

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(mutation)

    finalize_django_types()
    return _schema(Mutation)


def _ticket_write(write: type[DjangoModelFormMutation], target: models.Model) -> _AdmittedWrite:
    """A ``RepairTicket`` create linking ``target``, the venue the decode admits."""
    code = _uniq("Rt")

    def linked() -> None:
        ticket = library_models.RepairTicket.objects.get(code=code)
        assert pk_of(ticket.venue) == pk_of(target)

    return _write_schema(write), f'{{code: "{code}", venueId: {pk_of(target)}}}', linked


def _admit_same_model() -> _AdmittedWrite:
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    field = forms.ModelChoiceField(queryset=library_models.Venue.objects.all())
    write = _declare_write(_relation_form(library_models.RepairTicket, "venue", field, "code"))
    return _ticket_write(write, library_models.Venue.objects.create(name=_uniq("Ve")))


def _admit_multi_table_child() -> _AdmittedWrite:
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    field = forms.ModelChoiceField(queryset=library_models.LendingDesk.objects.all())
    write = _declare_write(_relation_form(library_models.RepairTicket, "venue", field, "code"))
    return _ticket_write(write, library_models.LendingDesk.objects.create(name=_uniq("Desk")))


def _admit_proxy() -> _AdmittedWrite:
    _register_primaries(library_models.Shelf, library_models.Branch)
    field = forms.ModelChoiceField(queryset=library_models.ProxyBranch.objects.all())
    write = _declare_write(_relation_form(library_models.Shelf, "branch", field, "code"))
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    code = _uniq("Sh")

    def linked() -> None:
        assert pk_of(library_models.Shelf.objects.get(code=code).branch) == pk_of(branch)

    return _write_schema(write), f'{{code: "{code}", branchId: {pk_of(branch)}}}', linked


def _admit_init_assigned_queryset() -> _AdmittedWrite:
    """The class-level queryset is over ``Patron``; ``__init__`` assigns one over ``Venue``."""
    _register_primaries(library_models.RepairTicket, library_models.Venue)

    class RepairTicketForm(forms.ModelForm[models.Model]):
        venue = _venue_choice()

        class Meta:
            model = library_models.RepairTicket
            fields = ("code", "venue")

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            files: _FilesT | None = None,
            instance: models.Model | None = None,
        ) -> None:
            super().__init__(data=data, files=files, instance=instance)
            _set_queryset("venue", library_models.Venue.objects.all())(self)

    write = _declare_write(RepairTicketForm)
    return _ticket_write(write, library_models.Venue.objects.create(name=_uniq("Ve")))


def _admit_order_fields_assigned_queryset() -> _AdmittedWrite:
    """``order_fields``, which Django's ``__init__`` calls, assigns the ``Venue`` queryset."""
    _register_primaries(library_models.RepairTicket, library_models.Venue)

    class RepairTicketForm(forms.ModelForm[models.Model]):
        venue = _venue_choice()

        class Meta:
            model = library_models.RepairTicket
            fields = ("code", "venue")

        @override
        def order_fields(self, field_order: Iterable[str] | None) -> None:
            super().order_fields(field_order)
            _set_queryset("venue", library_models.Venue.objects.all())(self)

    write = _declare_write(RepairTicketForm)
    return _ticket_write(write, library_models.Venue.objects.create(name=_uniq("Ve")))


def _admit_get_form_assigned_queryset() -> _AdmittedWrite:
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    ticket_form = _relation_form(library_models.RepairTicket, "venue", _venue_choice(), "code")
    write = _declare_rebuilding_write(ticket_form)
    return _ticket_write(write, library_models.Venue.objects.create(name=_uniq("Ve")))


def _admit_hook_basis_over_another_model() -> _AdmittedWrite:
    """``get_form_fields`` returns a ``Patron`` field; the form binds its own ``Venue`` field."""
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    venue_field = forms.ModelChoiceField(queryset=library_models.Venue.objects.all())
    ticket_form = _relation_form(library_models.RepairTicket, "venue", venue_field, "code")

    class Write(DjangoModelFormMutation):
        class Meta:
            form_class = ticket_form
            operation = "create"
            permission_classes = [_AllowAll]

        @classmethod
        @override
        def get_form_fields(cls) -> dict[str, forms.Field]:
            return {"code": forms.CharField(), "venue": _venue_choice()}

    return _ticket_write(Write, library_models.Venue.objects.create(name=_uniq("Ve")))


def _admit_create_narrowing_out_the_field() -> _AdmittedWrite:
    """A create whose ``Meta.fields`` leaves the optional field out never binds it."""
    _register_primaries(library_models.Venue, library_models.RepairTicket)
    write = _declare_write(_lead_ticket_form(), fields=("name",))
    name = _uniq("Ve")

    def linked() -> None:
        assert library_models.Venue.objects.get(name=name).lead_ticket is None

    return _write_schema(write), f'{{name: "{name}"}}', linked


def _admit_create_omitting_an_optional_field() -> _AdmittedWrite:
    """A create may omit an optional field, and then never binds it."""
    _register_primaries(library_models.Venue, library_models.RepairTicket)
    write = _declare_write(_lead_ticket_form())
    name = _uniq("Ve")

    def linked() -> None:
        assert library_models.Venue.objects.get(name=name).lead_ticket is None

    return _write_schema(write), f'{{name: "{name}"}}', linked


def _admit_create_omitting_an_optional_many_to_many() -> _AdmittedWrite:
    """An optional many-to-many field a create omits is never bound either."""
    _register_primaries(library_models.VenueSponsor, library_models.Venue)
    field = forms.ModelMultipleChoiceField(
        queryset=library_models.Patron.objects.all(),
        required=False,
    )
    write = _declare_write(_relation_form(library_models.VenueSponsor, "venues", field, "name"))
    name = _uniq("Sp")

    def linked() -> None:
        assert not library_models.VenueSponsor.objects.get(name=name).venues.exists()

    return _write_schema(write), f'{{name: "{name}"}}', linked


@pytest.mark.django_db
@pytest.mark.parametrize(
    "build",
    [
        _admit_same_model,
        _admit_multi_table_child,
        _admit_proxy,
        _admit_init_assigned_queryset,
        _admit_order_fields_assigned_queryset,
        _admit_get_form_assigned_queryset,
        _admit_hook_basis_over_another_model,
        _admit_create_narrowing_out_the_field,
        _admit_create_omitting_an_optional_field,
        _admit_create_omitting_an_optional_many_to_many,
    ],
    ids=[
        "same-model",
        "multi-table-child",
        "proxy",
        "init-assigns-the-target-queryset",
        "order-fields-assigns-the-target-queryset",
        "get-form-assigns-the-target-queryset",
        "get-form-fields-basis-over-another-model",
        "create-narrows-the-field-out",
        "create-omits-an-optional-field",
        "create-omits-an-optional-many-to-many",
    ],
)
def test_class_choice_the_bound_form_agrees_with_builds_and_writes(
    build: Callable[[], _AdmittedWrite],
) -> None:
    """A field the bound form looks up among the target's rows builds, and the write links it.

    The class-level queryset over the target, a multi-table child or a proxy of it; one over
    another model that the form's ``__init__``, its ``order_fields`` or the mutation's
    ``get_form`` replaces before the request reads it; a ``get_form_fields`` basis over
    another model while the form binds its own class-level field; and a create that never
    binds the field, because its ``Meta.fields`` leaves it out or because the field is
    optional and the create omits it.
    """
    schema, data, linked = build()
    res = schema.execute_sync(f"mutation {{ write(data: {data}) {{ errors {{ field }} }} }}")
    assert res.errors is None, res.errors
    assert res.data == {"write": {"errors": []}}
    linked()


@pytest.mark.django_db
def test_queryset_less_class_choice_builds() -> None:
    """A class-level choice field with no queryset names no model, so the build leaves it alone.

    The form decides what a queryset assigned per request admits; the build has no model to
    compare against the column's.
    """
    _register_primaries(library_models.RepairTicket, library_models.Venue)
    field: forms.ModelChoiceField[models.Model] = forms.ModelChoiceField(queryset=None)
    write = _declare_write(_relation_form(library_models.RepairTicket, "venue", field, "code"))
    _ = _write_schema(write)
    assert write._input_class is not None


@pytest.mark.django_db
def test_optional_class_choice_sent_by_a_create_is_refused_at_request() -> None:
    """An optional create field over another model builds, and a create sending it is refused.

    The build cannot know a create will send the optional field, so the request-time check
    refuses the create that does, before ``is_valid()`` and with nothing written.
    """
    _register_primaries(library_models.Venue, library_models.RepairTicket)
    schema = _write_schema(_declare_write(_lead_ticket_form()))
    venue = library_models.Venue.objects.create(name=_uniq("Ve"))
    ticket = library_models.RepairTicket.objects.create(code=_uniq("Rt"), venue=venue)
    name = _uniq("Ve")
    res = schema.execute_sync(
        f'mutation {{ write(data: {{name: "{name}", leadTicketId: {pk_of(ticket)}}}) '
        "{ errors { field } } }",
    )
    assert res.errors is not None
    message = (
        "Write: the bound form's field 'lead_ticket' looks its choice up among Patron rows, "
        "but the input decodes 'lead_ticket' ids against RepairTicket. The queryset get_form "
        "or the form's __init__ assigns must be over the model get_form_fields() declares."
    )
    assert [error.message for error in res.errors] == [message]
    assert not library_models.Venue.objects.filter(name=name).exists()


# ---------------------------------------------------------------------------
# A form field whose widget reads other keys than its name (``_bind_under_form_keys``)
# ---------------------------------------------------------------------------


def _keyed_row_model(name: str, **columns: models.Field[object, object]) -> type[models.Model]:
    """A synthetic unmanaged model: a ``title`` beside ``columns``."""
    return type(
        name,
        (models.Model,),
        {
            "__module__": __name__,
            "title": models.TextField(),
            "Meta": type("Meta", (), {"app_label": "products", "managed": False}),
            **columns,
        },
    )


def _keyed_row_form(
    model_class: type[models.Model],
    name: str,
    form_field: forms.Field,
    *,
    prefix: str | None = None,
    attrs: Mapping[str, object] | None = None,
) -> type[forms.BaseForm]:
    """A ``ModelForm`` over ``title`` and the column ``name``, declaring ``form_field`` for it."""
    return type(
        "KeyedRowForm",
        (forms.ModelForm,),
        {
            name: form_field,
            "prefix": prefix,
            "Meta": type("Meta", (), {"model": model_class, "fields": ("title", name)}),
            **(attrs or {}),
        },
    )


def _prefixed_copy(data: dict[str, object]) -> dict[str, object]:
    """Key ``data`` as the form prefix ``pfx`` reads a one-key field: ``pfx-<name>``."""
    return {f"pfx-{name}": value for name, value in data.items()}


#: The data a ``get_form_kwargs`` hook binds, by the name ``_keyed_row_schema`` takes:
#: ``multivalue`` a ``MultiValueDict`` holding each value as its one entry; ``doseq`` the
#: ``QueryDict`` a query string spelling each list as repeated keys parses to (a list per
#: key, as text); ``prefixed-copy`` the hook's own ``pfx-<name>`` copy (a form prefixed
#: ``pfx`` keeps it as bound), as a ``dict`` or a ``MultiValueDict``.
_BOUND_DATA: dict[str, Callable[[dict[str, object]], Mapping[str, object]]] = {
    "multivalue": lambda data: MultiValueDict({name: [value] for name, value in data.items()}),
    "doseq": lambda data: QueryDict(urlencode(data, doseq=True)),
    "prefixed-copy": _prefixed_copy,
    "prefixed-copy-multivalue": lambda data: MultiValueDict(
        {name: [value] for name, value in _prefixed_copy(data).items()},
    ),
}


def _keyed_row_schema(
    form_class: type[forms.BaseForm],
    model_class: type[models.Model],
    *,
    bind: str = "dict",
) -> tuple[strawberry.Schema, str, str]:
    """A non-Relay primary + create / update mutations over ``form_class``, with the input names.

    ``bind`` names the data each mutation's ``get_form_kwargs`` binds (``_BOUND_DATA``):
    ``"dict"`` the package's own mapping, any other a shape a consumer hook binds.
    """
    type(
        "KeyedRowT",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model_class, "fields": ("id", "title")})},
    )

    def get_form_kwargs(
        self: DjangoModelFormMutation,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: models.Model | None = None,
    ) -> dict[str, object]:
        kwargs = DjangoModelFormMutation.get_form_kwargs(
            self,
            info,
            data=data,
            files=files,
            instance=instance,
        )
        kwargs["data"] = _BOUND_DATA[bind](data)
        return kwargs

    hooks: dict[str, object] = {"get_form_kwargs": get_form_kwargs} if bind != "dict" else {}

    def meta(operation: str) -> type:
        attrs: dict[str, object] = {
            "form_class": form_class,
            "operation": operation,
            "permission_classes": [],
        }
        return type("Meta", (), attrs)

    create = type("CreateRow", (DjangoModelFormMutation,), {"Meta": meta("create"), **hooks})
    update = type("UpdateRow", (DjangoModelFormMutation,), {"Meta": meta("update"), **hooks})

    @strawberry.type
    class Mutation:
        create_row = DjangoMutationField(create)
        update_row = DjangoMutationField(update)

    finalize_django_types()
    names = [
        require_instance(mutation._input_class, type).__name__ for mutation in (create, update)
    ]
    return _schema(Mutation), names[0], names[1]


def _write_keyed_row(
    model_class: type[models.Model],
    form_class: type[forms.BaseForm],
    *,
    operation: str,
    data: dict[str, object],
    stored: Mapping[str, object] | None,
    mode: str,
    bind: str = "dict",
) -> object:
    """Run ``operation`` (``create`` or ``update`` over a row holding ``stored``); its payload."""
    schema, create_input, update_input = _keyed_row_schema(form_class, model_class, bind=bind)
    selection = "{ result{ title } errors{ field messages codes path } }"
    if operation == "create":
        query = f"mutation($d: {create_input}!){{ createRow(data:$d){selection} }}"
        res = _execute_in_mode(schema, query, {"d": data}, mode=mode)
        root = "createRow"
    else:
        row = model_class._base_manager.create(title="Old", **dict(stored or {}))
        query = (
            f"mutation($id: ID!, $d: {update_input}!){{ updateRow(id:$id, data:$d){selection} }}"
        )
        res = _execute_in_mode(schema, query, {"id": str(saved_pk(row)), "d": data}, mode=mode)
        root = "updateRow"
    assert res.errors is None, res.errors
    return _json_at(res.data, root)


def _array_column_and_field(shape: str) -> tuple[models.Field[object, object], forms.Field]:
    """The ``ArrayField`` column and the ``SplitArrayField`` (``size`` 3) of ``shape``."""
    from django.contrib.postgres import fields as postgres_fields  # noqa: PLC0415 - needs the Postgres driver
    from django.contrib.postgres import forms as postgres_forms  # noqa: PLC0415 - needs the Postgres driver

    shapes: dict[str, Callable[[], tuple[models.Field[object, object], forms.Field]]] = {
        "text-required-keep-nulls": lambda: (
            postgres_fields.ArrayField(models.TextField()),
            postgres_forms.SplitArrayField(forms.CharField(), size=3),
        ),
        "text-optional-drop-nulls": lambda: (
            postgres_fields.ArrayField(models.TextField(), blank=True),
            postgres_forms.SplitArrayField(
                forms.CharField(),
                size=3,
                required=False,
                remove_trailing_nulls=True,
            ),
        ),
        "integer-required-drop-nulls": lambda: (
            postgres_fields.ArrayField(models.IntegerField()),
            postgres_forms.SplitArrayField(
                forms.IntegerField(),
                size=3,
                remove_trailing_nulls=True,
            ),
        ),
        "integer-nullable-elements": lambda: (
            postgres_fields.ArrayField(models.IntegerField(null=True, blank=True)),
            postgres_forms.SplitArrayField(forms.IntegerField(required=False), size=3),
        ),
        "text-column-default": lambda: (
            postgres_fields.ArrayField(models.TextField(), blank=True, default=_default_tags),
            postgres_forms.SplitArrayField(
                forms.CharField(),
                size=3,
                required=False,
                remove_trailing_nulls=True,
            ),
        ),
    }
    return shapes[shape]()


def _default_tags() -> list[str]:
    """The ``text-column-default`` column's default list."""
    return ["d"]


_SPLIT_ARRAY_WRITES = [
    pytest.param(
        "text-required-keep-nulls",
        "create",
        ["a", "b", "c"],
        None,
        id="text-req-create",
    ),
    pytest.param(
        "text-required-keep-nulls",
        "update",
        ["d", "e", "f"],
        ["x", "y", "z"],
        id="text-req-update",
    ),
    pytest.param("text-optional-drop-nulls", "create", ["a", "b"], None, id="text-opt-create"),
    pytest.param("text-optional-drop-nulls", "create", [], None, id="text-opt-create-empty"),
    pytest.param("text-optional-drop-nulls", "update", ["a"], ["x", "y"], id="text-opt-update"),
    pytest.param(
        "text-optional-drop-nulls",
        "update",
        [],
        ["x", "y"],
        id="text-opt-update-empty",
    ),
    pytest.param("integer-required-drop-nulls", "create", [1, 2], None, id="int-req-create"),
    pytest.param("integer-required-drop-nulls", "update", [3], [1, 2], id="int-req-update"),
    pytest.param("integer-nullable-elements", "create", [1, None, 3], None, id="int-null-create"),
    pytest.param(
        "integer-nullable-elements",
        "update",
        [1, 2, 3],
        [4, 5, 6],
        id="int-null-update",
    ),
    pytest.param("text-column-default", "create", ["a"], None, id="default-create"),
    pytest.param("text-column-default", "create", [], None, id="default-create-empty"),
    pytest.param("text-column-default", "update", ["a"], ["x"], id="default-update"),
]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("prefix", [None, "pfx"], ids=["unprefixed", "prefixed"])
@pytest.mark.parametrize(
    (
        "shape",
        "operation",
        "sent",
        "stored",
    ),
    _SPLIT_ARRAY_WRITES,
)
def test_modelform_split_array_field_writes_the_list_sent(
    shape: str,
    operation: str,
    sent: list[object],
    stored: list[object] | None,
    prefix: str | None,
    mode: str,
) -> None:
    """A ``SplitArrayField`` reads the list from ``<name>_0`` .. ``<name>_2``, the keys it is bound under.

    Each element is bound under its own key, padded to ``size`` with ``None``, so the
    field cleans exactly the list sent (Django's ``remove_trailing_nulls`` drops the
    padding; a required field still answers Django's own ``required`` for a list with no
    truthy element, which no row here sends) and an empty list is a value, never an
    omission the column default would fill: the row stores the list sent, created or
    updated, required or optional, text or integer elements, nullable elements kept, under
    a form prefix too.
    """
    column, form_field = _array_column_and_field(shape)
    model_class = _keyed_row_model("SplitTagsRow", tags=column)
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _keyed_row_form(model_class, "tags", form_field, prefix=prefix),
            operation=operation,
            data={"title": "New", "tags": sent},
            stored=None if stored is None else {"tags": stored},
            mode=mode,
        )
        assert payload == {"result": {"title": "New"}, "errors": []}
        assert list(model_class._base_manager.values_list("title", "tags")) == [("New", sent)]


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("prefix", [None, "pfx"], ids=["unprefixed", "prefixed"])
@pytest.mark.parametrize(
    ("shape", "stored", "created"),
    [
        pytest.param("text-required-keep-nulls", ["x", "y", "z"], None, id="text-req"),
        pytest.param("text-optional-drop-nulls", ["x"], None, id="text-opt"),
        pytest.param("integer-required-drop-nulls", [1, 2, 3], None, id="int-req"),
        pytest.param("integer-nullable-elements", [1, None, 3], None, id="int-null"),
        pytest.param("text-column-default", ["x", "y"], ["d"], id="default"),
    ],
)
def test_modelform_split_array_field_omitted_keeps_the_stored_list(
    shape: str,
    stored: list[object],
    created: list[object] | None,
    prefix: str | None,
    mode: str,
) -> None:
    """An update omitting a ``SplitArrayField`` keeps the stored list; a create omitting it, the default.

    The update binds the located row's list under the widget's keys, so the unchanged
    field validates and is written back as stored. A create omitting the field binds no
    key, so the widget reports it omitted and the column default fills it.
    """
    column, form_field = _array_column_and_field(shape)
    model_class = _keyed_row_model("SplitTagsRow", tags=column)
    with _blank_choice_table(model_class):
        form_class = _keyed_row_form(model_class, "tags", form_field, prefix=prefix)
        payload = _write_keyed_row(
            model_class,
            form_class,
            operation="update",
            data={"title": "New"},
            stored={"tags": stored},
            mode=mode,
        )
        assert payload == {"result": {"title": "New"}, "errors": []}
        assert list(model_class._base_manager.values_list("title", "tags")) == [("New", stored)]
        if created is not None:
            model_class._base_manager.all().delete()
            registry.clear()
            payload = _write_keyed_row(
                model_class,
                form_class,
                operation="create",
                data={"title": "Made"},
                stored=None,
                mode=mode,
            )
            assert payload == {"result": {"title": "Made"}, "errors": []}
            rows = list(model_class._base_manager.values_list("title", "tags"))
            assert rows == [("Made", created)]


_TAGS_TOO_LONG_ERROR = {
    "field": "tags",
    "messages": ["List contains 4 items, it should contain no more than 3."],
    "codes": ["max_length"],
    "path": ["tags"],
}


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("operation", "data", "stored"),
    [
        pytest.param(
            "create",
            {
                "title": "New",
                "tags": [
                    "a",
                    "b",
                    "c",
                    "d",
                ],
            },
            None,
            id="create",
        ),
        pytest.param(
            "update",
            {
                "title": "New",
                "tags": [
                    "a",
                    "b",
                    "c",
                    "d",
                ],
            },
            ["x"],
            id="update-sent",
        ),
        pytest.param(
            "update",
            {"title": "New"},
            [
                "w",
                "x",
                "y",
                "z",
            ],
            id="update-reconstructed",
        ),
    ],
)
def test_modelform_split_array_field_longer_than_size_is_refused(
    operation: str,
    data: dict[str, object],
    stored: list[str] | None,
    mode: str,
) -> None:
    """A list longer than ``size`` is the field's ``max_length`` error; nothing is written.

    The widget reads no key past ``size``, so binding the list would drop its tail and
    write a shorter one. It is refused before validation with Django's own
    ``ArrayMaxLengthValidator`` message and code, keyed like every field error, whether
    the client sent it or an update reconstructed it from the located row.
    """
    column, form_field = _array_column_and_field("text-optional-drop-nulls")
    model_class = _keyed_row_model("SplitTagsRow", tags=column)
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _keyed_row_form(model_class, "tags", form_field),
            operation=operation,
            data=data,
            stored=None if stored is None else {"tags": stored},
            mode=mode,
        )
        assert payload == {"result": None, "errors": [_TAGS_TOO_LONG_ERROR]}
        kept = [] if stored is None else [("Old", stored)]
        assert list(model_class._base_manager.values_list("title", "tags")) == kept


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_modelform_split_array_field_explicit_null_is_the_column_null_error(
    operation: str,
    mode: str,
) -> None:
    """An explicit ``null`` on a ``null=False`` array column is its ``null`` error, nothing written.

    The optional field cleans the padded ``None`` elements to ``[]``, a value the column
    stores, so the whole ``None`` bound under the field's prefixed name names the
    explicit ``null`` (``_coerced_null_fields``).
    """
    column, form_field = _array_column_and_field("text-optional-drop-nulls")
    model_class = _keyed_row_model("SplitTagsRow", tags=column)
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _keyed_row_form(model_class, "tags", form_field),
            operation=operation,
            data={"title": "New", "tags": None},
            stored={"tags": ["x"]},
            mode=mode,
        )
        assert payload == {"result": None, "errors": [_NULL_TAGS_ERROR]}
        kept = [] if operation == "create" else [("Old", ["x"])]
        assert list(model_class._base_manager.values_list("title", "tags")) == kept


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    "bind",
    ["doseq", "prefixed-copy", "prefixed-copy-multivalue"],
)
@pytest.mark.parametrize(
    (
        "operation",
        "data",
        "stored",
        "result",
        "rows",
    ),
    [
        pytest.param(
            "create",
            {"title": "New", "tags": ["a", "b", "c"]},
            None,
            {"title": "New"},
            [("New", ["a", "b", "c"])],
            id="create",
        ),
        pytest.param(
            "update",
            {"title": "New"},
            ["x", "y"],
            {"title": "New"},
            [("New", ["x", "y"])],
            id="update-omitted",
        ),
        pytest.param(
            "create",
            {
                "title": "New",
                "tags": [
                    "a",
                    "b",
                    "c",
                    "d",
                ],
            },
            None,
            None,
            [],
            id="create-past-size",
        ),
    ],
)
def test_modelform_split_array_field_reads_a_hook_bound_mapping(
    operation: str,
    data: dict[str, object],
    stored: list[str] | None,
    result: dict[str, object] | None,
    rows: list[tuple[str, list[str]]],
    bind: str,
    mode: str,
) -> None:
    """A ``SplitArrayField`` reads the whole list a ``get_form_kwargs`` hook binds.

    A ``QueryDict`` spelling the list as repeated keys holds it as its value list, read
    whole, never as its last element; a hook's own ``pfx-<name>`` copy under a form
    prefixed ``pfx`` is kept as bound, and the list it holds under ``pfx-tags`` gets its
    elements beside it under the widget's keys. Each writes the list sent, keeps the
    stored list on an omitted update, and refuses a list longer than ``size``.
    """
    column, form_field = _array_column_and_field("text-optional-drop-nulls")
    model_class = _keyed_row_model("SplitTagsRow", tags=column)
    with _blank_choice_table(model_class):
        prefix = "pfx" if bind.startswith("prefixed") else None
        payload = _write_keyed_row(
            model_class,
            _keyed_row_form(model_class, "tags", form_field, prefix=prefix),
            operation=operation,
            data=data,
            stored=None if stored is None else {"tags": stored},
            mode=mode,
            bind=bind,
        )
        errors = [] if result is not None else [_TAGS_TOO_LONG_ERROR]
        assert payload == {"result": result, "errors": errors}
        assert list(model_class._base_manager.values_list("title", "tags")) == rows


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("prefix", [None, "pfx"], ids=["unprefixed", "prefixed"])
def test_modelform_disabled_split_array_field_keeps_a_stored_list_past_size(
    prefix: str | None,
    mode: str,
) -> None:
    """A ``disabled`` ``SplitArrayField`` reads its initial: an omitted update keeps a longer stored list.

    Django cleans a disabled field's initial and never its data, so the stored list is
    bound whole, neither split nor refused, and the update writes it back unchanged.
    """
    from django.contrib.postgres import forms as postgres_forms  # noqa: PLC0415 - needs the Postgres driver

    column, _ = _array_column_and_field("text-optional-drop-nulls")
    form_field = postgres_forms.SplitArrayField(
        forms.CharField(),
        size=3,
        required=False,
        remove_trailing_nulls=True,
        disabled=True,
    )
    model_class = _keyed_row_model("SplitTagsRow", tags=column)
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _keyed_row_form(model_class, "tags", form_field, prefix=prefix),
            operation="update",
            data={"title": "New"},
            stored={
                "tags": [
                    "w",
                    "x",
                    "y",
                    "z",
                ],
            },
            mode=mode,
        )
        assert payload == {"result": {"title": "New"}, "errors": []}
        rows = list(model_class._base_manager.values_list("title", "tags"))
        assert rows == [
            (
                "New",
                [
                    "w",
                    "x",
                    "y",
                    "z",
                ],
            ),
        ]


class _PairWidget(forms.MultiWidget):
    """Two text boxes holding a ``"<left>:<right>"`` value."""

    def __init__(self) -> None:
        super().__init__((forms.TextInput, forms.TextInput))

    @override
    def decompress(self, value: object) -> list[object]:
        """Split ``"<left>:<right>"``; an empty value is two empty boxes."""
        if isinstance(value, str) and value:
            return list(value.split(":", 1))
        return [None, None]


class _PairField(forms.MultiValueField):
    """A ``MultiValueField`` over two required text parts, compressed to ``"<left>:<right>"``."""

    widget = _PairWidget

    def __init__(self) -> None:
        super().__init__((forms.CharField(), forms.CharField()))

    @override
    def compress(self, data_list: list[object]) -> str:
        return ":".join(str(part) for part in data_list)


def _text_column() -> models.Field[object, object]:
    """A fresh ``TextField`` column."""
    return models.TextField()


_MULTI_WIDGET_KINDS: dict[
    str,
    tuple[
        Callable[[], models.Field[object, object]],
        Callable[[], forms.Field],
        str,
        object,
        object,
    ],
] = {
    "pair": (
        _text_column,
        _PairField,
        "left:right",
        "left:right",
        "old:pair",
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    "bind",
    [
        "dict",
        "prefixed",
        "multivalue",
        "prefixed-copy",
    ],
)
@pytest.mark.parametrize("operation", ["create", "update", "update-omitted"])
@pytest.mark.parametrize("kind", list(_MULTI_WIDGET_KINDS))
def test_modelform_multi_widget_field_writes_the_compressed_value(
    kind: str,
    operation: str,
    bind: str,
    mode: str,
) -> None:
    """A consumer ``MultiValueField`` over a column reads its parts from the ``MultiWidget``'s keys.

    The value is split by the widget's own ``decompress`` (the pair's two halves) and bound
    under ``<name>_0`` / ``<name>_1``, so the field compresses exactly the value sent; an
    update omitting it binds the stored value the same way and keeps it. Under a form
    prefix, from a ``MultiValueDict`` a ``get_form_kwargs`` override binds, and beside the
    whole value a hook's own prefixed copy holds, the parts land on the keys the form reads.
    Django's ``SplitDateTimeField`` runs the same rule live
    (``test_scalars_mutation_api.py::test_split_datetime_form_field_writes_the_datetime_sent``).
    """
    column_class, field_class, sent, written, stored = _MULTI_WIDGET_KINDS[kind]
    model_class = _keyed_row_model("MultiKeyRow", value=column_class())
    with _blank_choice_table(model_class):
        form_class = _keyed_row_form(
            model_class,
            "value",
            field_class(),
            prefix="pfx" if bind.startswith("prefixed") else None,
        )
        data: dict[str, object] = {"title": "New"}
        if operation != "update-omitted":
            data["value"] = sent
        payload = _write_keyed_row(
            model_class,
            form_class,
            operation=operation.removesuffix("-omitted"),
            data=data,
            stored={"value": stored},
            mode=mode,
            bind="dict" if bind == "prefixed" else bind,
        )
        assert payload == {"result": {"title": "New"}, "errors": []}
        expected = stored if operation == "update-omitted" else written
        assert list(model_class._base_manager.values_list("title", "value")) == [("New", expected)]


_JSON_TOO_LONG_ERROR = {
    "field": "tags",
    "messages": ["List contains 3 items, it should contain no more than 2."],
    "codes": ["max_length"],
    "path": ["tags"],
}


def _split_json_form(
    model_class: type[models.Model],
    *,
    bind: str = "dict",
    disabled: bool = False,
) -> type[forms.BaseForm]:
    """A ``JSONField`` over the ``tags`` JSON column, read through a ``size`` 2 split widget.

    Prefixed ``pfx`` when ``bind`` is a hook's prefixed copy.
    """
    field = forms.JSONField(
        widget=FakeSplitArrayWidget(forms.TextInput(), size=2),
        disabled=disabled,
    )
    prefix = "pfx" if bind.startswith("prefixed") else None
    return _keyed_row_form(model_class, "tags", field, prefix=prefix)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "bind",
    ["dict", "prefixed-copy", "prefixed-copy-multivalue"],
)
@pytest.mark.parametrize(("sent", "written"), [([1, 2], [1, 2]), ([1], [1, None])])
def test_modelform_split_array_widget_binds_each_element_padded_to_size(
    sent: list[int],
    written: list[int | None],
    bind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each element is bound under ``<name>_<index>``, padded with ``None`` to the widget's ``size``.

    The field reads the padded list the widget's keys hold (a ``JSONField`` keeps the
    padding, where a ``SplitArrayField`` would drop it under ``remove_trailing_nulls``):
    from the package's mapping, and from a hook's own prefixed copy, a ``dict`` or a
    ``MultiValueDict``, whose whole value gets its parts beside it.
    """
    monkeypatch.setattr(widgets_module, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    model_class = _keyed_row_model("SplitJsonRow", tags=models.JSONField())
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _split_json_form(model_class, bind=bind),
            operation="create",
            data={"title": "New", "tags": sent},
            stored=None,
            mode="sync",
            bind=bind,
        )
        assert payload == {"result": {"title": "New"}, "errors": []}
        assert list(model_class._base_manager.values_list("title", "tags")) == [("New", written)]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "bind",
    [
        "dict",
        "multivalue",
        "doseq",
        "prefixed-copy",
        "prefixed-copy-multivalue",
    ],
)
@pytest.mark.parametrize(
    ("operation", "data", "stored"),
    [
        pytest.param("create", {"title": "New", "tags": [1, 2, 3]}, None, id="create"),
        pytest.param("update", {"title": "New", "tags": [1, 2, 3]}, [9], id="update-sent"),
        pytest.param("update", {"title": "New"}, [7, 8, 9], id="update-reconstructed"),
    ],
)
def test_modelform_split_array_widget_value_past_size_is_refused(
    operation: str,
    data: dict[str, object],
    stored: list[int] | None,
    bind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A list longer than the widget's ``size`` is the field's ``max_length`` error before validation.

    Sent or reconstructed, from the package's mapping, a ``MultiValueDict`` or a
    ``doseq`` ``QueryDict`` a ``get_form_kwargs`` override binds (the whole list read, never
    its last element), or a hook's own prefixed copy; nothing is written.
    """
    monkeypatch.setattr(widgets_module, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    model_class = _keyed_row_model("SplitJsonRow", tags=models.JSONField())
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _split_json_form(model_class, bind=bind),
            operation=operation,
            data=data,
            stored=None if stored is None else {"tags": stored},
            mode="sync",
            bind=bind,
        )
        assert payload == {"result": None, "errors": [_JSON_TOO_LONG_ERROR]}
        kept = [] if stored is None else [("Old", stored)]
        assert list(model_class._base_manager.values_list("title", "tags")) == kept


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bind", ["dict", "prefixed", "prefixed-copy"])
def test_disabled_split_widget_field_keeps_its_stored_value_past_size(
    bind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``disabled`` field reads its initial, never the data: bound whole, never split or refused.

    The stored list is longer than the widget's ``size``; Django cleans the disabled
    field's initial, so the update omitting it keeps the stored list, unprefixed, re-keyed
    under the form's prefix, and in a hook's own prefixed copy.
    """
    monkeypatch.setattr(widgets_module, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    model_class = _keyed_row_model("SplitJsonRow", tags=models.JSONField())
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _split_json_form(model_class, bind=bind, disabled=True),
            operation="update",
            data={"title": "New"},
            stored={"tags": [7, 8, 9]},
            mode="sync",
            bind="dict" if bind == "prefixed" else bind,
        )
        assert payload == {"result": {"title": "New"}, "errors": []}
        rows = list(model_class._base_manager.values_list("title", "tags"))
        assert rows == [("New", [7, 8, 9])]


def _split_initial_form(model_class: type[models.Model]) -> type[forms.BaseForm]:
    """A ``MultipleChoiceField`` over a text column, its initial the stored text split on commas."""

    class SplitInitialForm(forms.ModelForm[models.Model]):
        tags = forms.MultipleChoiceField(
            choices=[("a", "A"), ("b", "B")],
            required=False,
            widget=FakeSplitArrayWidget(forms.TextInput(), size=1),
        )

        class Meta:
            model = model_class
            fields = ("title", "tags")

        @override
        def get_initial_for_field(self, field: forms.Field, field_name: str) -> object:
            initial = object_result(super().get_initial_for_field, field, field_name)
            return str(initial).split(",") if field_name == "tags" else initial

        def clean_tags(self) -> str:
            return ",".join(str(tag) for tag in list_of(dict_of(self.cleaned_data)["tags"]))

    return SplitInitialForm


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("stored", "errors", "kept"),
    [
        pytest.param("a", [], ("New", "a"), id="fits"),
        pytest.param(
            "a,b",
            [
                {
                    "field": "tags",
                    "messages": ["List contains 2 items, it should contain no more than 1."],
                    "codes": ["max_length"],
                    "path": ["tags"],
                },
            ],
            ("Old", "a,b"),
            id="past-size",
        ),
    ],
)
def test_omitted_initial_binds_under_the_split_widget_keys(
    stored: str,
    errors: list[dict[str, object]],
    kept: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An omitted field's initial is bound under its widget's keys; one past ``size`` is refused.

    A list field over a text column binds the form's own initial when omitted
    (``_bind_omitted_shape_disagreeing_initials``): here ``get_initial_for_field`` splits the
    stored text, and the split list is bound under ``tags_0``, so the unchanged field validates and
    is written back; an initial longer than the widget's ``size`` is the field's
    ``max_length`` error, nothing written.
    """
    monkeypatch.setattr(widgets_module, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    model_class = _keyed_row_model("SplitInitialRow", tags=models.TextField())
    with _blank_choice_table(model_class):
        payload = _write_keyed_row(
            model_class,
            _split_initial_form(model_class),
            operation="update",
            data={"title": "New"},
            stored={"tags": stored},
            mode="sync",
        )
        result = None if errors else {"title": "New"}
        assert payload == {"result": result, "errors": errors}
        assert list(model_class._base_manager.values_list("title", "tags")) == [kept]
