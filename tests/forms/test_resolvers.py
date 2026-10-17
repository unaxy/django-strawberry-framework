"""Form-mutation resolver-pipeline tests.

Package-only: construction hooks, decode helpers, reconstruction internals,
throwaway-schema branches a shipped mutation cannot express, and fail-closed
``ConfigurationError`` / ``SyncMisuseError`` / deadline-before-write.

Live HTTP owns the consumer-visible form writes in
``examples/fakeshop/test_query/test_products_api.py`` (``createItemViaForm`` /
``updateItemViaForm`` / file create+omit / ``get_form_kwargs`` inject /
write-time IntegrityError / ``submitContact`` / ``submitPing`` /
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
field on a partial input, ``to_field_name`` reconstruction (including an M2M member
whose ``to_field_name`` value is ``""``), a raw-pk M2M element ``""`` decoded through a
hiding text-keyed type (no fakeshop text-keyed type hides a row), ImageField
reconstruction key absence, decode-helper envelopes, optimizer
``dst_optimizer_plan`` G2, and the save-time blank non-text choice column shapes
fakeshop has no column for (omitted with no default, decimal / date, update
``null``, a filling-in model ``save()``, an unrelated consumer ``ValueError``), and
the keying of a save-time Django ``ValidationError`` by a name fakeshop's own
``Item.save()`` rule never raises (a relation ``attname``, a name only the form
declares, a dotted name): the ``ModelForm`` reads it against the backing model, the
model-less plain form against its own form fields.
"""

from __future__ import annotations

import contextlib
import datetime
import decimal
import itertools
from collections.abc import Generator, Iterator
from enum import Enum
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeAlias

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalars_models
from django import forms
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, models
from django.db.models.signals import pre_save
from django.test.utils import CaptureQueriesContext
from strawberry import relay
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
from django_strawberry_framework.forms import resolvers as form_resolvers
from django_strawberry_framework.forms.resolvers import (
    _decode_form_relation_multi,
    _is_empty_form_value,
    _reconstruct_partial_data,
    _to_form_key_value,
)
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import (
    dict_of,
    enum_value,
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

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

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


def _relay_global_id(type_cls: type, pk: object) -> relay.GlobalID:
    """Build a ``relay.GlobalID`` object (the coerced shape Strawberry hands the resolver).

    The unit-tier decode is called below ``Strawberry``'s argument coercion, so the
    relation value must be a ``relay.GlobalID`` instance (a plain base64 string
    takes the raw-pk branch). Reconstructs the exact GlobalID object from the wire
    string ``global_id_for`` mints (``from_id`` parses the type's actual encoding
    strategy), so the ``type_name`` / ``node_id`` slots match what live emission
    produces.
    """
    return relay.GlobalID.from_id(global_id_for(type_cls, pk))


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
        category_id=_relay_global_id(CategoryT, saved_pk(cat)),
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

    The motivating regression this commit fixes: baking ``bool | None`` while
    leaving the input field required produced SDL that let GraphQL validation
    accept the omit, then Strawberry raised ``TypeError: missing 1 required
    keyword-only argument`` when constructing the input object. With the field
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
    """An omitted M2M whose form field sets ``to_field_name`` survives a partial update (Finding 3).

    The decode lands a PROVIDED M2M as ``to_field_name`` values
    (``_to_form_key_value``); ``model_to_dict`` would reconstruct an OMITTED one as
    related INSTANCES (effectively pks), which a ``ModelMultipleChoiceField`` keyed
    by ``to_field_name`` cannot resolve - so an omitted M2M would spuriously fail
    validation on a one-field update (``spec-038-form_mutations-0_0_12`` Finding 3).
    Reconstruction now converts each member by ``to_field_name`` too, so omitted and
    provided M2M bind in the same shape. Fails on the pre-fix ``model_to_dict``
    reconstruction.
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
    no extra lookup. No fakeshop form keys an M2M by a text column a member can hold ``""``
    in.
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
    assert len(reads) == genre_reads, reads


@pytest.mark.django_db
def test_partial_update_preserves_unprovided_fk_with_to_field_name() -> None:
    """An omitted FK whose form field sets ``to_field_name`` survives a partial update.

    The single-FK twin of the M2M ``to_field_name`` case. The bound
    ``ModelChoiceField(to_field_name="code")`` validates ``shelf`` via
    ``queryset.get(code=value)``; ``model_to_dict`` reconstructs an OMITTED FK as the
    stored ``shelf_id`` pk, so the bound form would run ``get(code=<pk>)`` ->
    ``DoesNotExist`` -> ``invalid_choice`` and spuriously fail a one-field update,
    even though a PROVIDED unchanged FK (decoded to its ``code``) passes.
    Reconstruction now converts an omitted ``to_field_name`` FK by ``to_field_name``
    too. Fails on the pre-fix ``model_to_dict`` reconstruction.
    """

    class BookForm(forms.ModelForm[library_models.Book]):
        shelf = forms.ModelChoiceField(
            queryset=library_models.Shelf.objects.all(),
            to_field_name="code",
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "shelf")

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
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    res = schema.execute_sync(
        "mutation($id: ID!, $d: BookFormPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ title } errors{ field messages } } }",
        variable_values={"id": global_id_for(BookT, saved_pk(book)), "d": {"title": "Renamed"}},
    )
    assert res.errors is None, res.errors
    assert res.data is not None
    payload = _json_object(res.data, "updateBook")
    # The omitted to_field_name FK did NOT spuriously fail validation.
    assert payload["errors"] == [], payload["errors"]
    assert _json_at(payload, "node", "title") == "Renamed"
    book.refresh_from_db()
    assert book.title == "Renamed"
    # the unchanged FK preserved
    assert book.shelf_id == saved_pk(shelf)


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


@pytest.mark.django_db
def test_required_extra_field_omitted_on_update_is_coercion_error() -> None:
    """A required non-model extra field stays required in the partial input.

    Omitting it is a GraphQL coercion error BEFORE the resolver
    (``spec-038-form_mutations-0_0_12`` Finding 2).

    The partial input keeps a required non-model extra field required (it
    is not a model-backed field forced optional). Now that a required generated
    field carries NO class default, an omitted required field is rejected at
    variable coercion rather than silently arriving as ``None`` at the resolver and
    surfacing as an in-band ``FieldError`` (which masked the missing-input error).
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
    """A plain-form ``clean_*`` write on the pinned alias fails closed (0.0.14 phase hardening).

    The model-less body now rides ``pipeline_alias_guard`` + ``pipeline_write_phase``
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
# G2 plan-shape (the ModelForm re-fetch rides the 036 G2 path) - load-bearing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modelform_refetch_keeps_select_related_and_suppresses_only() -> None:
    """The ModelForm re-fetch plan KEEPS ``select_related`` and applies NO ``.only(...)`` (G2).

    ``dst_optimizer_plan`` is not a wire field. Nested ``category { name }`` on
    live ``createItemViaForm`` proves the relation came back; this pins the
    mutation G2 gate (``only_fields == ()``).
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
    # No `.only(...)` projection under a MUTATION (the G2 gate suppresses it).
    assert plan.only_fields == ()


# ---------------------------------------------------------------------------
# ``spec-038-form_mutations-0_0_12`` hardening
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_narrowed_update_preserves_excluded_required_fk_and_validates_constraint() -> None:
    """A ``Meta.fields``-narrowed update reconstructs an EXCLUDED required FK from the row.

    The ModelForm declares ``('name', 'category')`` while the update mutation
    narrows the GraphQL input to ``('name',)``. A name-only update must preserve
    the located row's ``category`` (the bound ModelForm validates ``category`` even
    though it is off the wire), and the ``unique_item_per_category`` constraint
    must still validate against that preserved FK
    (``spec-038-form_mutations-0_0_12`` Finding 3).
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
    """An explicit ``null`` single-relation value passes through unchanged (Finding 4).

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
        form_field=field,
        info=unread_info(),
    )
    assert error is None
    assert decoded is None


@pytest.mark.django_db
def test_decode_relation_multi_empty_values_return_empty_list() -> None:
    """An explicit ``null`` or empty list on an M2M returns ``[]`` and never iterates ``None`` (Finding 4)."""
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())
    empties: tuple[None, list[object]] = (None, [])
    for empty in empties:
        assert field.queryset is not None
        decoded, error = form_resolvers._decode_form_relation_multi(
            empty,
            graphql_name="genres",
            related_model=field.queryset.model,
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
    Driven directly (the autouse fixture leaves the registry empty). The helper was
    promoted to ``utils/querysets.py`` in spec-039 so the form +
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
        form_field=field,
        info=unread_info(),
    )
    assert keys is None
    assert error is not None
    assert error.field == "genres"


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
            form_field=field,
            info=unread_info(),
        )
    assert (keys, error) == ([""], None)
    assert len(captured.captured_queries) == 1


def _build_printing_bound_with_schema(
    *,
    to_field_name: str | None,
) -> strawberry.Schema:
    """A ModelForm create over ``Printing`` whose ``bound_with`` names text-keyed editions.

    ``EditionT`` is a non-Relay primary, so ``boundWith`` takes raw ISBN text, and its
    ``get_queryset`` hides every edition whose ISBN is ``""`` or starts with ``hidden``.
    ``to_field_name`` keys the ``bound_with`` member lookup (``None`` keeps the generated
    field, keyed by the ISBN pk).
    """

    class PrintingForm(forms.ModelForm[library_models.Printing]):
        class Meta:
            model = library_models.Printing
            fields = ("edition", "run_size", "bound_with")

    if to_field_name is not None:
        PrintingForm.base_fields["bound_with"] = forms.ModelMultipleChoiceField(
            queryset=library_models.Edition.objects.all(),
            to_field_name=to_field_name,
            required=False,
        )

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
@pytest.mark.parametrize(
    ("to_field_name", "isbn_10", "edition_reads"),
    [(None, "0000000000", 2), ("isbn_10", "", 2)],
    ids=["keyed_by_isbn", "keyed_by_isbn_10"],
)
def test_m2m_raw_pk_element_empty_is_decoded_never_a_clear(
    to_field_name: str | None,
    isbn_10: str,
    edition_reads: int,
) -> None:
    """A raw-pk ``boundWith`` element ``""`` names the edition whose ISBN is ``""``, decoded.

    A list element is never a clear: ``""`` is the pk of an edition, so it is type-checked
    and resolved through ``EditionT.get_queryset`` like any member. That edition is hidden,
    so the element is the uniform relation error with nothing written. Bound undecoded, the
    generated (ISBN-keyed) field would link the hidden edition, and a field keyed by
    ``isbn_10`` would read the pk ``""`` as an ``isbn_10`` value and link the visible edition
    whose ``isbn_10`` is ``""``. The edition table is read twice: ``editionId`` and the
    element, each through ``EditionT.get_queryset``; the refusal precedes any form. ``EditionT``
    is test-local: no fakeshop text-keyed type hides a row.
    """
    schema = _build_printing_bound_with_schema(to_field_name=to_field_name)
    publisher = library_models.Publisher.objects.create(name=_uniq("Pub"))
    library_models.Edition.objects.create(isbn_13="", isbn_10=isbn_10, publisher=publisher)
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
    assert len(reads) == edition_reads, reads


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("to_field_name", "isbn_10"),
    [(None, "0000000000"), ("isbn_10", "0000000267")],
    ids=["keyed_by_isbn", "keyed_by_isbn_10"],
)
def test_m2m_raw_pk_element_naming_a_visible_edition_links_it(
    to_field_name: str | None,
    isbn_10: str,
) -> None:
    """A visible edition named by its raw ISBN links through either key (the control)."""
    schema = _build_printing_bound_with_schema(to_field_name=to_field_name)
    publisher = library_models.Publisher.objects.create(name=_uniq("Pub"))
    shown = library_models.Edition.objects.create(
        isbn_13="9780000000268",
        isbn_10=isbn_10,
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


def test_to_form_key_value_handles_serializable_value_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    field = forms.ModelChoiceField(
        queryset=library_models.Genre.objects.all(),
        to_field_name="invalid_attr",
    )
    row = library_models.Genre(pk=42)

    # An attribute the row lacks: serializable_value raises AttributeError.
    assert _to_form_key_value(row, field) == 42

    def _missing(_self: library_models.Genre, _name: str) -> object:
        raise FieldDoesNotExist("missing")

    monkeypatch.setattr(library_models.Genre, "serializable_value", _missing)
    assert _to_form_key_value(row, field) == 42


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
        form_field=field,
        info=unread_info(),
    )
    assert error is None
    assert keys == [saved_pk(first), saved_pk(second)]


def test_decode_form_relation_multi_iteration_failures_stay_in_envelope() -> None:
    """A container that fails DURING iteration is the uniform field-keyed error.

    A generator raising midway and an ``__iter__`` raising ``BaseException``
    both collapse to the relation envelope instead of escaping the resolver as
    a raw ``RuntimeError`` / ``BaseException``.
    """

    class _ProbeBaseException(BaseException):
        pass

    class _MidwayRaise:
        def __iter__(self) -> Iterator[int]:
            yield 1
            raise RuntimeError("midway")

    class _BaseExceptionIter:
        def __iter__(self) -> Iterator[object]:
            raise _ProbeBaseException("hostile iteration")

    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.none())
    for values in (_MidwayRaise(), _BaseExceptionIter()):
        keys, error = form_resolvers._decode_form_relation_multi(
            values,
            graphql_name="genres",
            related_model=library_models.Genre,
            form_field=field,
            info=unread_info(),
        )
        assert keys is None
        assert error is not None
        assert error.field == "genres"


@pytest.mark.django_db
def test_decode_form_relation_multi_materializes_before_any_visibility_query() -> None:
    """A partially-consumed M2M container never reaches a visibility query.

    The container is materialized BEFORE any member is decoded, so an iterator
    that raises after its first id yields the field-keyed container error with
    ZERO database queries - a half-consumed id set can never be partially
    confirmed against (or leaked into) the visibility check.
    """
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    field = forms.ModelMultipleChoiceField(queryset=library_models.Genre.objects.all())

    def _container() -> Iterator[int]:
        yield saved_pk(genre)
        raise RuntimeError("hostile second pull")

    with CaptureQueriesContext(connection) as ctx:
        keys, error = form_resolvers._decode_form_relation_multi(
            _container(),
            graphql_name="genres",
            related_model=library_models.Genre,
            form_field=field,
            info=unread_info(),
        )
    assert keys is None
    assert error is not None
    assert error.field == "genres"
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
# Save-time blank non-text choice column (``_modelform_save_or_field_errors``)
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
) -> tuple[strawberry.Schema, str, str]:
    """A non-Relay primary + create / update ModelForm mutations over ``model_class``.

    Returns the schema and the create / update input type names.
    """
    form_class = type(
        f"{model_class.__name__}Form",
        (forms.ModelForm,),
        {"Meta": type("Meta", (), {"model": model_class, "fields": fields})},
    )
    type(
        f"{model_class.__name__}T",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model_class, "fields": ("id", *fields)})},
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
