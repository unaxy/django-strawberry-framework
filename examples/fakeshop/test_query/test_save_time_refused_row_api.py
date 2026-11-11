"""Live HTTP: a save-time failure names a column only of the save that raised it.

Every flavor that writes a model answers a refused save's ``None`` on a ``blank=True,
null=False`` input column as that column's field-keyed ``null`` error, read from the
recorded save the caught exception propagated out of
(``django_strawberry_framework/utils/write_values.py::refused_save``): the model create's
own row, the ``ModelForm``'s ``form.instance``, any backing-model row of the
serializer. A refused save consumer code caught and swallowed (Django's
``get_or_create`` shape), a failure another write raises (another model's save, raw
SQL, ``QuerySet.update()``) and a fallback write refused inside the handler are not
that save's refusal: the answer is the ``"__all__"`` ``constraint`` envelope, and in the
``ModelForm`` flavor a ``ValueError`` propagates as raised, a fallback refused through a
helper the handler calls included. An exception consumer code raises over the row's own
refusal stays that row's ``null``: ``from`` it, or without ``from`` / ``from None`` in
the handler, or a database error a helper or a class context manager's ``__exit__``
raises (Django raises its own database errors ``from`` the driver's error, apart from
its delete refusals ``ProtectedError`` / ``RestrictedError``, which stay the envelope,
and the MySQL / Oracle cursor wrappers, which raise inside the driver error's handler).

The subject is the shipped ``ItemHold`` (``item`` is ``blank=True, null=False``, its
``null`` message "A hold needs an item.") behind a test-local schema; the escaping
write is a duplicate ``Category`` name. The consumer code each flavor runs is the shape
that flavor offers: a ``pre_save`` receiver on ``ItemHold`` for the model create (the
model mutation runs no consumer save hook and the shipped model has no ``save()``
override), a ``save()`` override on a ``ModelForm`` subclass, and ``create()`` /
``update()`` on a ``ModelSerializer`` subclass.

A row of the backing model's family is that model's row: the library ``Venue`` family
(the ``OpenVenue`` proxy, the ``LendingDesk`` / ``SelfServeDesk`` multi-table chain and
two test-local proxies, of ``OpenVenue`` and of ``LendingDesk``) behind serializers over
``Venue``, ``OpenVenue`` and ``LendingDesk`` whose ``create()`` / ``update()`` save a row
of another class, and ``ModelForm`` creates whose ``save()`` binds ``form.instance`` to
one. A refused save of a proxy's, a proxy of a proxy's, a multi-table child's or
grandchild's or a proxy of a child's row names its ``None`` column, a parent-table
(``name``) or a child-table (``windowCount``) one, also after the backing row's own save
and on a form first bound to a ``LendingDesk``; the concrete base under a proxy model,
a multi-table parent, a sibling and an unrelated ``Genre`` are the envelope, and so is a
failure a receiver raises after a family row's save completed.
"""

from __future__ import annotations

import datetime
from collections.abc import Generator, Mapping
from functools import wraps
from typing import TYPE_CHECKING, NoReturn, TypeVar

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.products.forms import ItemHoldModelForm
from apps.products.serializers import ItemHoldSerializer
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from django import forms
from django.db import IntegrityError, connection, transaction
from django.db.models.signals import post_save, pre_save
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_at, json_list, response_json
from typing_extensions import override

from django_strawberry_framework import (
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import ModelSerializerBase, saved_pk

if TYPE_CHECKING:
    from types import TracebackType

    from django.db.models import Model

pytestmark = pytest.mark.usefixtures("private_registry")

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}

#: The consumer code's scenario for the request: how it treats the row's own save
#: (``swallow``) and which write it runs afterwards (``escape``).
_SCENARIO: dict[str, str] = {}

#: Set while consumer code saves rows itself, so its receivers do not run again.
_BUSY: dict[str, bool] = {"busy": False}

_NULL_ITEM = [{"field": "itemId", "messages": ["A hold needs an item."], "codes": ["null"]}]
_ENVELOPE = [
    {
        "field": "__all__",
        "messages": ["A database constraint was violated."],
        "codes": ["constraint"],
    },
]


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-refused-row/", _graphql_view),
    path("graphql-refused-row-async/", _async_graphql_view),
]


def _escape() -> None:
    """Run the scenario's write after the row's own save: each raises, none is that save."""
    escape = _SCENARIO.get("escape", "none")
    first, second = product_models.Category.objects.order_by("pk")[:2]
    if escape == "other_save":
        product_models.Category(name=first.name).save()
    elif escape == "raw_sql":
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE products_category SET name = %s WHERE id = %s",
                [first.name, second.pk],
            )
    elif escape == "queryset_update":
        _ = product_models.Category.objects.filter(pk=second.pk).update(name=first.name)
    elif escape == "sibling_hold":
        product_models.ItemHold(reason="sibling").save()
    elif escape == "other_valueerror":
        # Another model's save dies before any statement: its key is not a number.
        product_models.Category(id="not-a-key", name="Unsaved").save()


def _translate_refusal() -> NoReturn:
    """A consumer helper the handler calls to translate the refusal, raising without ``from``."""
    msg = "The hold could not be written."
    raise IntegrityError(msg)


def _fall_back() -> None:
    """A consumer helper the handler calls to write a fallback the database refuses."""
    first = product_models.Category.objects.earliest("pk")
    product_models.Category(name=first.name).save()


class _TranslateRefusal:
    """A class context manager whose ``__exit__`` translates a refusal without ``from``."""

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if isinstance(exc, IntegrityError):
            msg = "The hold could not be written."
            raise IntegrityError(msg)


def _consumer_write(row: product_models.ItemHold) -> None:
    """The consumer code a flavor runs around the row's own save, holding ``item=None``."""
    swallow = _SCENARIO.get("swallow", "none")
    _BUSY["busy"] = True
    try:
        if swallow == "savepoint":
            try:
                with transaction.atomic():
                    row.save()
            except IntegrityError:
                pass
        elif swallow in {"reraise_from", "reraise_no_from", "reraise_from_none"}:
            msg = "The hold could not be written."
            try:
                with transaction.atomic():
                    row.save()
            except IntegrityError as exc:
                if swallow == "reraise_from":
                    raise IntegrityError(msg) from exc
                if swallow == "reraise_from_none":
                    raise IntegrityError(msg) from None
                raise IntegrityError(msg)  # noqa: B904
        elif swallow == "helper_translate":
            try:
                with transaction.atomic():
                    row.save()
            except IntegrityError:
                _translate_refusal()
        elif swallow == "cm_exit_translate":
            with _TranslateRefusal(), transaction.atomic():
                row.save()
        elif swallow in {"fallback_delete_protected", "fallback_delete_restricted"}:
            # The collector refuses the delete (``ProtectedError`` / ``RestrictedError``,
            # raised by Django with no cause) while the handler runs.
            guarded = product_models.Item.objects.get(pk=int(_SCENARIO["guarded"]))
            try:
                with transaction.atomic():
                    row.save()
            except IntegrityError:
                _ = guarded.delete()
        elif swallow == "fallback_through_helper":
            try:
                with transaction.atomic():
                    row.save()
            except IntegrityError:
                _fall_back()
        elif swallow == "fallback_in_handler":
            first = product_models.Category.objects.earliest("pk")
            try:
                with transaction.atomic():
                    row.save()
            except IntegrityError:
                product_models.Category(name=first.name).save()
        elif swallow == "stale_valueerror":
            # The row's own save dies before any statement and is swallowed.
            vars(row)["item_id"] = "not-a-key"
            try:
                with transaction.atomic():
                    row.save()
            except ValueError:
                pass
            vars(row)["item_id"] = None
        _escape()
    finally:
        _BUSY["busy"] = False


def _hold_pre_save(instance: Model, **_kwargs: object) -> None:
    """The model flavor's consumer code: a project ``pre_save`` receiver on ``ItemHold``."""
    if _BUSY["busy"] or not _SCENARIO:
        return
    assert isinstance(instance, product_models.ItemHold)
    _consumer_write(instance)


def _hold_post_save(instance: Model, **_kwargs: object) -> None:
    """A project ``post_save`` receiver saving a sibling hold the database refuses."""
    if _BUSY["busy"] or _SCENARIO.get("post_save") != "sibling":
        return
    del instance
    _BUSY["busy"] = True
    try:
        product_models.ItemHold(reason="sibling").save()
    finally:
        _BUSY["busy"] = False


@pytest.fixture(autouse=True)
def _consumer_receivers() -> Generator[None, None, None]:
    """Connect the project receivers for the test; clear the scenario afterwards."""
    pre_save.connect(
        _hold_pre_save,
        sender=product_models.ItemHold,
        weak=False,
        dispatch_uid="test_save_time_refused_row_api.pre_save",
    )
    post_save.connect(
        _hold_post_save,
        sender=product_models.ItemHold,
        weak=False,
        dispatch_uid="test_save_time_refused_row_api.post_save",
    )
    try:
        yield
    finally:
        _ = post_save.disconnect(
            sender=product_models.ItemHold,
            dispatch_uid="test_save_time_refused_row_api.post_save",
        )
        _ = pre_save.disconnect(
            sender=product_models.ItemHold,
            dispatch_uid="test_save_time_refused_row_api.pre_save",
        )
        _SCENARIO.clear()
        _BUSY["busy"] = False


class ConsumerHoldForm(ItemHoldModelForm):
    """``ItemHoldModelForm`` whose ``save()`` runs consumer code around the row's own save."""

    @override
    def save(self, commit: bool = True) -> product_models.ItemHold:
        row = super().save(commit=False)
        _consumer_write(row)
        if commit:
            row.save()
        return row


class ConsumerHoldSerializer(ItemHoldSerializer):
    """``ItemHoldSerializer`` whose ``create()`` / ``update()`` run consumer code."""

    @override
    def create(self, validated_data: dict[str, object]) -> product_models.ItemHold:
        row = product_models.ItemHold(**validated_data)
        _consumer_write(row)
        row.save()
        return row

    @override
    def update(
        self,
        instance: product_models.ItemHold,
        validated_data: dict[str, object],
    ) -> product_models.ItemHold:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        _consumer_write(instance)
        instance.save()
        return instance


def _schema() -> DjangoSchema:
    """Build the test-local schema: every flavor's ``ItemHold`` create, and the updates."""

    class ItemNode(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")

    class ItemHoldNode(DjangoType):
        class Meta:
            model = product_models.ItemHold
            fields = ("id", "reason")

    class CreateHold(DjangoMutation):
        class Meta:
            model = product_models.ItemHold
            fields = ("reason", "item")
            operation = "create"
            permission_classes = []

    class CreateHoldViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = ConsumerHoldForm
            operation = "create"
            permission_classes = []

    class UpdateHoldViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = ConsumerHoldForm
            operation = "update"
            permission_classes = []

    class CreateHoldViaSerializer(SerializerMutation):
        class Meta:
            serializer_class = ConsumerHoldSerializer
            operation = "create"
            permission_classes = []

    class UpdateHoldViaSerializer(SerializerMutation):
        class Meta:
            serializer_class = ConsumerHoldSerializer
            operation = "update"
            permission_classes = []

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        create_hold = DjangoMutationField(CreateHold)
        create_hold_via_form = DjangoMutationField(CreateHoldViaForm)
        update_hold_via_form = DjangoMutationField(UpdateHoldViaForm)
        create_hold_via_serializer = DjangoMutationField(CreateHoldViaSerializer)
        update_hold_via_serializer = DjangoMutationField(UpdateHoldViaSerializer)

    del ItemNode, ItemHoldNode
    finalize_django_types()
    return DjangoSchema(query=Query, mutation=Mutation, error_policy={"enabled": False})


_RESULT = "result { reason } errors { field messages codes }"

#: (root field, document) per flavor and operation; an update reads ``$id``.
_DOCUMENTS: dict[str, tuple[str, str]] = {
    "model-create": (
        "createHold",
        f"mutation($d: ItemHoldItemReasonInput!) {{ createHold(data: $d) {{ {_RESULT} }} }}",
    ),
    "modelform-create": (
        "createHoldViaForm",
        f"mutation($d: ConsumerHoldFormInput!) {{ createHoldViaForm(data: $d) {{ {_RESULT} }} }}",
    ),
    "modelform-update": (
        "updateHoldViaForm",
        (
            "mutation($id: ID!, $d: ConsumerHoldFormPartialInput!) "
            f"{{ updateHoldViaForm(id: $id, data: $d) {{ {_RESULT} }} }}"
        ),
    ),
    "serializer-create": (
        "createHoldViaSerializer",
        (
            "mutation($d: ConsumerHoldSerializerInput!) "
            f"{{ createHoldViaSerializer(data: $d) {{ {_RESULT} }} }}"
        ),
    ),
    "serializer-update": (
        "updateHoldViaSerializer",
        (
            "mutation($id: ID!, $d: ConsumerHoldSerializerPartialInput!) "
            f"{{ updateHoldViaSerializer(id: $id, data: $d) {{ {_RESULT} }} }}"
        ),
    ),
}

_FLAVORS = list(_DOCUMENTS)


def _variables(flavor: str, *, item: object = None) -> JSONObject:
    """The request's variables: the row holds ``item=None`` unless ``item`` names one."""
    data: JSONObject = {"reason": "reserved"}
    if item is not None or flavor != "model-create":
        data["itemId"] = item
    if flavor.endswith("-update"):
        held = product_models.ItemHold.objects.create(
            reason="held",
            item=product_models.Item.objects.earliest("pk"),
        )
        return {"id": str(held.pk), "d": data}
    return {"d": data}


def _post(flavor: str, variables: Mapping[str, object]) -> JSONObject:
    """POST the flavor's mutation over ``/graphql-refused-row/``; return the payload."""
    root, document = _DOCUMENTS[flavor]
    _CURRENT["schema"] = _schema()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(document, variables=variables, url="/graphql-refused-row/")
    finally:
        _CURRENT["schema"] = None
    assert "errors" not in payload, payload
    return {"answer": json_at(payload, "data", root)}


def _held_rows() -> list[str]:
    return sorted(product_models.ItemHold.objects.values_list("reason", flat=True))


@pytest.mark.django_db
@pytest.mark.parametrize("flavor", _FLAVORS)
def test_the_rows_own_refused_save_answers_its_null(flavor: str) -> None:
    """With no other write, the row's own refused save answers ``itemId``'s ``null`` error."""
    seed_data(1)
    variables = _variables(flavor)
    before = _held_rows()
    answer = _post(flavor, variables)
    assert answer == {"answer": {"result": None, "errors": _NULL_ITEM}}
    assert _held_rows() == before


@pytest.mark.django_db
@pytest.mark.parametrize("swallow", ["none", "savepoint"])
@pytest.mark.parametrize("escape", ["other_save", "raw_sql", "queryset_update"])
@pytest.mark.parametrize("flavor", _FLAVORS)
def test_a_failure_another_write_raises_is_the_envelope(
    flavor: str,
    escape: str,
    swallow: str,
) -> None:
    """A failure another write raises is the envelope, a swallowed refused save or not.

    The consumer code leaves the row's own save alone (``none``) or swallows its refused
    save in a savepoint (``savepoint``), then runs a write the database refuses for a
    duplicate ``Category`` name: another model's save, raw SQL or ``QuerySet.update()``.
    That write's ``IntegrityError`` is not the row's refusal, so the row's ``None``
    ``item`` is never named. Nothing is written.
    """
    seed_data(1)
    variables = _variables(flavor)
    before = _held_rows()
    names = sorted(product_models.Category.objects.values_list("name", flat=True))
    _SCENARIO.update(swallow=swallow, escape=escape)
    answer = _post(flavor, variables)
    assert answer == {"answer": {"result": None, "errors": _ENVELOPE}}
    assert _held_rows() == before
    assert sorted(product_models.Category.objects.values_list("name", flat=True)) == names


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("flavor", "expected"),
    [
        pytest.param("model-create", _ENVELOPE, id="model-create"),
        pytest.param("modelform-create", _ENVELOPE, id="modelform-create"),
        pytest.param("modelform-update", _ENVELOPE, id="modelform-update"),
        pytest.param("serializer-create", _NULL_ITEM, id="serializer-create"),
        pytest.param("serializer-update", _NULL_ITEM, id="serializer-update"),
    ],
)
def test_another_holds_refused_save_is_named_only_by_a_flavor_reading_any_row(
    flavor: str,
    expected: list[dict[str, object]],
) -> None:
    """Consumer code saves a second hold with no item, refused before the row's own save.

    The refused save is the second hold's. The serializer reads any backing-model row and
    names its ``itemId``; the model create reads only its own row and the ``ModelForm``
    only ``form.instance``, so for them it is the envelope, although their own row holds
    ``None`` on ``item`` too.
    """
    seed_data(1)
    variables = _variables(flavor)
    _SCENARIO.update(escape="sibling_hold")
    answer = _post(flavor, variables)
    assert answer == {"answer": {"result": None, "errors": expected}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "spelling",
    [
        pytest.param("reraise_from", id="from"),
        pytest.param("reraise_no_from", id="no-from"),
        pytest.param("reraise_from_none", id="from-none"),
        pytest.param("helper_translate", id="helper"),
        pytest.param("cm_exit_translate", id="cm-exit"),
    ],
)
@pytest.mark.parametrize("flavor", _FLAVORS)
def test_an_exception_raised_from_the_rows_refusal_answers_its_null(
    flavor: str,
    spelling: str,
) -> None:
    """An exception the consumer's handler raises over the row's own refusal is that refusal.

    ``raise IntegrityError(...) from exc`` keeps the save on the explicit cause's
    traceback; ``raise IntegrityError(...)`` without ``from``, or ``from None``, raised
    by the handler that caught the refusal, translates it, and so does a database error
    a helper the handler calls, or a class context manager's ``__exit__``, raises without
    ``from`` (Django raises its own database errors ``from`` the driver's, its causeless
    delete refusals and the MySQL / Oracle cursor wrappers' re-raises aside). Either way
    the row's ``None`` ``item`` is named.
    """
    seed_data(1)
    variables = _variables(flavor)
    _SCENARIO.update(swallow=spelling)
    answer = _post(flavor, variables)
    assert answer == {"answer": {"result": None, "errors": _NULL_ITEM}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "spelling",
    [
        pytest.param("fallback_in_handler", id="direct"),
        pytest.param("fallback_through_helper", id="helper"),
        pytest.param("fallback_delete_protected", id="delete-protected"),
        pytest.param("fallback_delete_restricted", id="delete-restricted"),
    ],
)
@pytest.mark.parametrize("flavor", _FLAVORS)
def test_a_fallback_write_refused_in_the_handler_is_the_envelope(
    flavor: str,
    spelling: str,
) -> None:
    """A fallback write refused while handling the row's refusal is not that refusal.

    The fallback's ``IntegrityError`` is raised by the fallback's own save, deep in
    Django, while the handler runs: the row's refusal is only its implicit
    ``__context__``, never its cause nor an exception the handler translated, so it is
    the envelope, whether the handler writes it or a helper it calls does: Django raises
    the fallback's ``IntegrityError`` ``from`` the driver's error. A delete the collector
    refuses (an ``Item`` a hold's ``PROTECT`` ``item`` or ``RESTRICT`` ``substitute``
    holds) raises Django's causeless ``ProtectedError`` / ``RestrictedError``, read as
    the fallback's own failure too.
    """
    seed_data(1)
    variables = _variables(flavor)
    _, held, substitute = product_models.Item.objects.order_by("pk")[:3]
    _ = product_models.ItemHold.objects.create(reason="guard", item=held, substitute=substitute)
    guarded = substitute if spelling == "fallback_delete_restricted" else held
    _SCENARIO.update(swallow=spelling, guarded=str(guarded.pk))
    answer = _post(flavor, variables)
    assert answer == {"answer": {"result": None, "errors": _ENVELOPE}}


@pytest.mark.django_db
@pytest.mark.parametrize("flavor", ["modelform-create", "modelform-update"])
@pytest.mark.parametrize(
    ("swallow", "escape", "expected"),
    [
        pytest.param(
            "stale_valueerror",
            "other_save",
            _ENVELOPE,
            id="stale-valueerror-other-save",
        ),
        pytest.param("savepoint", "other_valueerror", None, id="savepoint-other-valueerror"),
        pytest.param(
            "stale_valueerror",
            "other_valueerror",
            None,
            id="stale-valueerror-other-valueerror",
        ),
    ],
)
def test_a_modelform_failure_after_its_rows_swallowed_save_is_not_that_row(
    flavor: str,
    swallow: str,
    escape: str,
    expected: list[dict[str, object]] | None,
) -> None:
    """The ``ModelForm`` names a column only of ``form.instance``'s own failed save.

    The form's own save died and was swallowed, by an ``IntegrityError`` or by a
    ``ValueError`` before any statement (its ``item`` key is not a number), and another
    write then fails. Another model's ``IntegrityError`` is the envelope; another
    model's ``ValueError`` propagates as raised, never re-keyed as the row's ``null``.
    """
    seed_data(1)
    variables = _variables(flavor)
    _SCENARIO.update(swallow=swallow, escape=escape)
    root, document = _DOCUMENTS[flavor]
    _CURRENT["schema"] = _schema()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(
                document,
                variables=variables,
                url="/graphql-refused-row/",
            )
    finally:
        _CURRENT["schema"] = None
    if expected is None:
        assert json_at(payload, "data") is None
        [error] = json_list(payload, "errors")
        assert "expected a number but got 'not-a-key'" in str(json_at(error, "message"))
    else:
        assert "errors" not in payload, payload
        assert json_at(payload, "data", root) == {"result": None, "errors": expected}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("flavor", "expected"),
    [
        pytest.param("model-create", _ENVELOPE, id="model-create"),
        pytest.param("modelform-create", _ENVELOPE, id="modelform-create"),
        pytest.param("serializer-create", _NULL_ITEM, id="serializer-create"),
    ],
)
def test_a_sibling_hold_refused_inside_the_rows_save(
    flavor: str,
    expected: list[dict[str, object]],
) -> None:
    """A sibling hold a ``post_save`` receiver saves with no item is the innermost refusal.

    The row's own save succeeds and a project ``post_save`` receiver then saves a second
    hold holding ``None`` on ``item``, refused inside the row's save. The innermost
    recorded save the exception left is the sibling's: the serializer reads any
    backing-model row and names its ``itemId``; the model and ``ModelForm`` read only
    their own row, so the sibling is the envelope.
    """
    seed_data(1)
    _SCENARIO.update(post_save="sibling")
    item = product_models.Item.objects.earliest("pk")
    answer = _post(flavor, _variables(flavor, item=item.pk))
    assert answer == {"answer": {"result": None, "errors": expected}}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("flavor", ["model-create", "modelform-create", "serializer-create"])
async def test_a_swallowed_refused_save_over_the_async_view_is_the_envelope(
    flavor: str,
) -> None:
    """Over the async view a swallowed refused save, then another write's failure, is the envelope.

    The write step runs in one ``sync_to_async`` call, so the recorded saves and the
    caught exception share its thread.
    """
    await sync_to_async(seed_data)(1)
    root, document = _DOCUMENTS[flavor]
    variables = await sync_to_async(_variables)(flavor)
    _SCENARIO.update(swallow="savepoint", escape="other_save")
    _CURRENT["schema"] = await sync_to_async(_schema)()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient().query(
                document,
                variables=variables,
                assert_no_errors=False,
                url="/graphql-refused-row-async/",
            )
    finally:
        _CURRENT["schema"] = None
    assert result.response.status_code == 200
    payload = response_json(result.response)
    assert "errors" not in payload, payload
    assert json_at(payload, "data", root) == {"result": None, "errors": _ENVELOPE}
    assert not await product_models.ItemHold.objects.aexists()


# ===========================================================================
# The backing model's family: a proxy's or a multi-table child's refused save
# ===========================================================================

_TODAY = datetime.date(2024, 1, 2)

_NULL_NAME = [{"field": "name", "messages": ["This field cannot be null."], "codes": ["null"]}]
_NULL_WINDOW_COUNT = [
    {"field": "windowCount", "messages": ["This field cannot be null."], "codes": ["null"]},
]

_FAMILY_RESULT = "result { name } errors { field messages codes }"

_VenueT = TypeVar("_VenueT", bound=library_models.Venue)

#: The request's consumer scenario: the class key of the row the write saves (``saved``),
#: the column that row leaves ``None`` (``refusal``) and what runs after its save
#: (``after_save``).
_FAMILY: dict[str, str] = {}

#: The classes the scenario keys name, rebuilt per request (the proxies are test-local).
_FAMILY_CLASSES: dict[str, type[library_models.Venue]] = {}


def _proxy_of(base: type[_VenueT], name: str) -> type[_VenueT]:
    """Declare a test-local proxy of ``base``; the registry restore drops it after the test."""
    meta = type("Meta", (), {"proxy": True, "app_label": "library"})
    made = type(name, (base,), {"Meta": meta, "__module__": __name__})
    assert issubclass(made, base)
    return made


def _install_family_classes() -> None:
    """Key the shipped ``Venue`` family and two test-local proxies for the scenario."""
    _FAMILY_CLASSES.update(
        venue=library_models.Venue,
        open_venue=library_models.OpenVenue,
        open_venue_proxy=_proxy_of(library_models.OpenVenue, "RefusedOpenVenueProxy"),
        desk=library_models.LendingDesk,
        desk_proxy=_proxy_of(library_models.LendingDesk, "RefusedLendingDeskProxy"),
        self_serve=library_models.SelfServeDesk,
    )


def _family_row(saved: str, instance: library_models.Venue | None) -> library_models.Venue:
    """Build the unsaved ``saved`` row: a new one, or ``instance``'s row loaded as that class.

    The column the scenario's ``refusal`` names holds ``None``; every other is storable.
    """
    cls = _FAMILY_CLASSES[saved]
    if instance is None:
        values: dict[str, object] = {"name": "Saved", "opened_on": _TODAY}
        if issubclass(cls, library_models.LendingDesk):
            values["window_count"] = 0
        if issubclass(cls, library_models.SelfServeDesk):
            values["kiosk_code"] = "K-1"
        row = cls(**values)
    else:
        row = cls._base_manager.get(pk=instance.pk)
        vars(row)["name"] = "Saved"
    refusal = _FAMILY.get("refusal")
    if refusal is not None:
        vars(row)[refusal] = None
    return row


def _null_and_raise(instance: Model, **_kwargs: object) -> NoReturn:
    """A receiver the consumer connects inside its write: it runs after the save completed."""
    vars(instance)["name"] = None
    msg = "The venue could not be audited."
    raise IntegrityError(msg)


def _family_write(instance: library_models.Venue | None) -> library_models.Venue:
    """The consumer's ``create()`` / ``update()``: save the scenario's row, return it."""
    saved = _FAMILY["saved"]
    if saved == "genre":
        library_models.Genre(name=None).save()
        pytest.fail("the genre's save was not refused")
    if saved == "backing_then_proxy":
        row = _family_row("venue", instance)
        row.save()
        library_models.OpenVenue(name=None, opened_on=_TODAY).save()
        return row
    row = _family_row(saved, instance)
    if _FAMILY.get("after_save") != "null_and_raise":
        row.save()
        return row
    post_save.connect(_null_and_raise, sender=type(row), weak=False)
    try:
        row.save()
    finally:
        _ = post_save.disconnect(_null_and_raise, sender=type(row))
    return row


class FamilySerializer(ModelSerializerBase[library_models.Venue]):
    """A ``Venue``-family serializer whose ``create()`` / ``update()`` save the scenario's row."""

    @override
    def create(self, validated_data: dict[str, object]) -> library_models.Venue:
        return _family_write(None)

    @override
    def update(
        self,
        instance: library_models.Venue,
        validated_data: dict[str, object],
    ) -> library_models.Venue:
        return _family_write(instance)


class FamilyVenueSerializer(FamilySerializer):
    """The ``Venue`` serializer."""

    class Meta:
        model = library_models.Venue
        fields = ("name",)
        extra_kwargs = {"name": {"allow_null": True}}


class FamilyOpenVenueSerializer(FamilySerializer):
    """The ``OpenVenue`` proxy's serializer."""

    class Meta:
        model = library_models.OpenVenue
        fields = ("name",)
        extra_kwargs = {"name": {"allow_null": True}}


class FamilyLendingDeskSerializer(FamilySerializer):
    """The ``LendingDesk`` child's serializer, over a parent and a child column."""

    class Meta:
        model = library_models.LendingDesk
        fields = ("name", "window_count")
        extra_kwargs = {"name": {"allow_null": True}, "window_count": {"allow_null": True}}


class FamilyForm(forms.ModelForm[library_models.Venue]):
    """A ``Venue``-family form whose ``save()`` may save a row of another class instead.

    ``name`` cleans an explicit ``null`` to ``None``. A ``rebind_*`` scenario binds
    ``form.instance`` to the new row of that class it saves, holding ``None`` on ``name``;
    ``save_other_proxy`` saves such an ``OpenVenue`` and returns the form's own row unsaved.
    """

    name = forms.CharField(required=False, empty_value=None)

    @override
    def save(self, commit: bool = True) -> library_models.Venue:
        scenario = _FAMILY["saved"]
        if scenario == "default":
            return super().save(commit=commit)
        row = super().save(commit=False)
        if scenario == "save_other_proxy":
            library_models.OpenVenue(name=None, opened_on=_TODAY).save()
            return row
        rebound = {
            "rebind_proxy": library_models.OpenVenue,
            "rebind_child": library_models.LendingDesk,
            "rebind_concrete": library_models.Venue,
        }[scenario]
        new = rebound(name=None, opened_on=_TODAY)
        self.instance = new
        new.save()
        return new


class FamilyVenueForm(FamilyForm):
    """The ``Venue`` form."""

    class Meta:
        model = library_models.Venue
        fields = ("name",)


class FamilyOpenVenueForm(FamilyForm):
    """The ``OpenVenue`` proxy's form."""

    class Meta:
        model = library_models.OpenVenue
        fields = ("name",)


class FamilyLendingDeskForm(FamilyForm):
    """The ``LendingDesk`` child's form."""

    class Meta:
        model = library_models.LendingDesk
        fields = ("name",)


def _family_schema() -> DjangoSchema:
    """Every family write: a serializer create / update per backing model, a form create."""

    class VenueNode(DjangoType):
        class Meta:
            model = library_models.Venue
            fields = ("id", "name")

    class OpenVenueNode(DjangoType):
        class Meta:
            model = library_models.OpenVenue
            fields = ("id", "name")

    class LendingDeskNode(DjangoType):
        class Meta:
            model = library_models.LendingDesk
            fields = ("id", "name", "window_count")

    class CreateVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyVenueSerializer
            operation = "create"
            permission_classes = []

    class UpdateVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyVenueSerializer
            operation = "update"
            permission_classes = []

    class CreateOpenVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyOpenVenueSerializer
            operation = "create"
            permission_classes = []

    class UpdateOpenVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyOpenVenueSerializer
            operation = "update"
            permission_classes = []

    class CreateLendingDeskFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyLendingDeskSerializer
            operation = "create"
            permission_classes = []

    class UpdateLendingDeskFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyLendingDeskSerializer
            operation = "update"
            permission_classes = []

    class CreateVenueViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = FamilyVenueForm
            operation = "create"
            permission_classes = []

    class CreateVenueViaFormFromDesk(DjangoModelFormMutation):
        """Binds the create's form to a new ``LendingDesk``, a row of the form's model."""

        class Meta:
            form_class = FamilyVenueForm
            operation = "create"
            permission_classes = []

        @override
        def get_form(
            self,
            info: strawberry.Info[object, object],
            *,
            data: dict[str, object],
            files: dict[str, object],
            instance: Model | None = None,
        ) -> forms.ModelForm[library_models.Venue]:
            return super().get_form(
                info,
                data=data,
                files=files,
                instance=library_models.LendingDesk(window_count=0),
            )

    class CreateOpenVenueViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = FamilyOpenVenueForm
            operation = "create"
            permission_classes = []

    class CreateLendingDeskViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = FamilyLendingDeskForm
            operation = "create"
            permission_classes = []

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        create_venue_family = DjangoMutationField(CreateVenueFamily)
        update_venue_family = DjangoMutationField(UpdateVenueFamily)
        create_open_venue_family = DjangoMutationField(CreateOpenVenueFamily)
        update_open_venue_family = DjangoMutationField(UpdateOpenVenueFamily)
        create_lending_desk_family = DjangoMutationField(CreateLendingDeskFamily)
        update_lending_desk_family = DjangoMutationField(UpdateLendingDeskFamily)
        create_venue_via_form = DjangoMutationField(CreateVenueViaForm)
        create_venue_via_form_from_desk = DjangoMutationField(CreateVenueViaFormFromDesk)
        create_open_venue_via_form = DjangoMutationField(CreateOpenVenueViaForm)
        create_lending_desk_via_form = DjangoMutationField(CreateLendingDeskViaForm)

    del VenueNode, OpenVenueNode, LendingDeskNode
    finalize_django_types()
    return DjangoSchema(query=Query, mutation=Mutation, error_policy={"enabled": False})


#: (root field suffix, serializer class name) per backing model.
_FAMILY_BACKINGS = {
    "venue": ("VenueFamily", "FamilyVenueSerializer"),
    "open_venue": ("OpenVenueFamily", "FamilyOpenVenueSerializer"),
    "desk": ("LendingDeskFamily", "FamilyLendingDeskSerializer"),
}


def _family_rows() -> tuple[list[tuple[int | None, str]], list[int], list[str]]:
    """Every stored venue's key and name, every desk's window count, every genre's name."""
    return (
        list(library_models.Venue._base_manager.order_by("pk").values_list("pk", "name")),
        list(
            library_models.LendingDesk._base_manager.order_by("pk").values_list(
                "window_count",
                flat=True,
            ),
        ),
        sorted(library_models.Genre.objects.values_list("name", flat=True)),
    )


def _post_family(root: str, document: str, variables: Mapping[str, object]) -> object:
    """POST a family write over ``/graphql-refused-row/``; return its root field's answer."""
    _install_family_classes()
    _CURRENT["schema"] = _family_schema()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(document, variables=variables, url="/graphql-refused-row/")
    finally:
        _CURRENT["schema"] = None
        _FAMILY_CLASSES.clear()
    assert "errors" not in payload, payload
    return json_at(payload, "data", root)


def _located_kiosk() -> int:
    """Store the ``SelfServeDesk`` an update locates: a row of every ``Venue``-family class."""
    return saved_pk(
        library_models.SelfServeDesk.objects.create(
            name="Located",
            opened_on=_TODAY,
            window_count=1,
            kiosk_code="K-0",
        ),
    )


def _post_family_serializer(backing: str, located: int | None) -> object:
    """POST the ``backing`` serializer's create, or its update of the ``located`` row."""
    suffix, serializer = _FAMILY_BACKINGS[backing]
    data: JSONObject = {"name": None}
    if backing == "desk":
        data["windowCount"] = None if _FAMILY.get("refusal") == "window_count" else 1
    if located is None:
        root = f"create{suffix}"
        document = (
            f"mutation($d: {serializer}Input!) {{ {root}(data: $d) {{ {_FAMILY_RESULT} }} }}"
        )
        return _post_family(root, document, {"d": data})
    root = f"update{suffix}"
    document = (
        f"mutation($id: ID!, $d: {serializer}PartialInput!) "
        f"{{ {root}(id: $id, data: $d) {{ {_FAMILY_RESULT} }} }}"
    )
    return _post_family(root, document, {"id": str(located), "d": data})


@pytest.fixture(autouse=True)
def _clear_family_scenario() -> Generator[None, None, None]:
    """Clear the family scenario after the test."""
    try:
        yield
    finally:
        _FAMILY.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("op", ["create", "update"])
@pytest.mark.parametrize(
    (
        "backing",
        "saved",
        "refusal",
        "expected",
    ),
    [
        pytest.param("venue", "venue", "name", _NULL_NAME, id="venue-venue"),
        pytest.param("venue", "open_venue", "name", _NULL_NAME, id="venue-proxy"),
        pytest.param("venue", "open_venue_proxy", "name", _NULL_NAME, id="venue-proxy-of-proxy"),
        pytest.param("venue", "desk", "name", _NULL_NAME, id="venue-child"),
        pytest.param("venue", "desk_proxy", "name", _NULL_NAME, id="venue-proxy-of-child"),
        pytest.param("venue", "self_serve", "name", _NULL_NAME, id="venue-grandchild"),
        pytest.param("venue", "genre", "name", _ENVELOPE, id="venue-unrelated"),
        pytest.param("open_venue", "open_venue", "name", _NULL_NAME, id="proxy-proxy"),
        pytest.param(
            "open_venue",
            "open_venue_proxy",
            "name",
            _NULL_NAME,
            id="proxy-proxy-of-proxy",
        ),
        pytest.param("open_venue", "venue", "name", _ENVELOPE, id="proxy-concrete-base"),
        pytest.param("open_venue", "desk", "name", _ENVELOPE, id="proxy-sibling-child"),
        pytest.param("open_venue", "genre", "name", _ENVELOPE, id="proxy-unrelated"),
        pytest.param("desk", "desk", "name", _NULL_NAME, id="child-child"),
        pytest.param("desk", "desk_proxy", "name", _NULL_NAME, id="child-proxy-of-child"),
        pytest.param("desk", "self_serve", "name", _NULL_NAME, id="child-grandchild"),
        pytest.param("desk", "venue", "name", _ENVELOPE, id="child-parent"),
        pytest.param("desk", "genre", "name", _ENVELOPE, id="child-unrelated"),
        pytest.param(
            "desk",
            "desk",
            "window_count",
            _NULL_WINDOW_COUNT,
            id="child-child-own-table",
        ),
        pytest.param(
            "desk",
            "desk_proxy",
            "window_count",
            _NULL_WINDOW_COUNT,
            id="child-proxy-of-child-own-table",
        ),
        pytest.param(
            "desk",
            "self_serve",
            "window_count",
            _NULL_WINDOW_COUNT,
            id="child-grandchild-own-table",
        ),
    ],
)
def test_a_serializer_names_the_null_of_a_refused_row_of_its_models_family(
    backing: str,
    saved: str,
    refusal: str,
    expected: list[dict[str, object]],
    op: str,
) -> None:
    """A refused save of a row of the serializer's model, a proxy or a child, names its column.

    The consumer's ``create()`` / ``update()`` saves a row of another class holding ``None``
    on a ``null=False`` column: ``Venue.name`` (the parent table's) or
    ``LendingDesk.window_count`` (a child table's own). Django sends the save's signals with
    the row's own class, and every subclass of the serializer's model (a proxy, a proxy of
    a proxy, a multi-table child or grandchild, a proxy of a child) saves the model's rows,
    so its refusal is the field-keyed ``null`` the model's own row answers. A row of the
    concrete base under a proxy model, of a sibling, of a multi-table parent or of an
    unrelated model (``Genre``) is not, and is the ``"__all__"`` envelope. Nothing is
    written.
    """
    located = _located_kiosk() if op == "update" else None
    before = _family_rows()
    _FAMILY.update(saved=saved, refusal=refusal)
    answer = _post_family_serializer(backing, located)
    assert answer == {"result": None, "errors": expected}
    assert _family_rows() == before


@pytest.mark.django_db
@pytest.mark.parametrize("op", ["create", "update"])
def test_a_serializer_names_a_proxy_row_refused_after_its_own_row_saved(op: str) -> None:
    """The ``Venue`` serializer saves its row, then an ``OpenVenue`` holding ``None`` on ``name``.

    The ``OpenVenue`` row's refused save is the one the failure propagated out of, a row of
    the serializer's model's family, so its ``name`` is named. Nothing is written.
    """
    located = _located_kiosk() if op == "update" else None
    before = _family_rows()
    _FAMILY.update(saved="backing_then_proxy")
    answer = _post_family_serializer("venue", located)
    assert answer == {"result": None, "errors": _NULL_NAME}
    assert _family_rows() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "saved",
    [
        pytest.param("venue", id="model"),
        pytest.param("open_venue", id="proxy"),
        pytest.param("desk", id="child"),
    ],
)
def test_a_failure_after_a_family_rows_save_completed_is_the_envelope(saved: str) -> None:
    """A receiver raising after the row's save completed leaves no refused save of the row.

    The consumer's ``create()`` connects a ``post_save`` receiver for the row's class that
    clears ``name`` and raises an ``IntegrityError``. The row's ``post_save`` has already
    taken its record back, whatever its class, so the row's ``None`` is never named: the
    answer is the ``"__all__"`` envelope, the same for the model's own row, a proxy's and a
    child's. Nothing is written.
    """
    before = _family_rows()
    _FAMILY.update(saved=saved, after_save="null_and_raise")
    answer = _post_family_serializer("venue", None)
    assert answer == {"result": None, "errors": _ENVELOPE}
    assert _family_rows() == before


#: (root field, form class name) per form create.
_FAMILY_FORMS = {
    "venue": ("createVenueViaForm", "FamilyVenueForm"),
    "venue_from_desk": ("createVenueViaFormFromDesk", "FamilyVenueForm"),
    "open_venue": ("createOpenVenueViaForm", "FamilyOpenVenueForm"),
    "desk": ("createLendingDeskViaForm", "FamilyLendingDeskForm"),
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("form", "scenario", "expected"),
    [
        pytest.param("venue", "default", _NULL_NAME, id="venue-default"),
        pytest.param("open_venue", "default", _NULL_NAME, id="proxy-default"),
        pytest.param("desk", "default", _NULL_NAME, id="child-default"),
        pytest.param("venue", "rebind_proxy", _NULL_NAME, id="venue-rebind-proxy"),
        pytest.param("venue", "rebind_child", _NULL_NAME, id="venue-rebind-child"),
        pytest.param(
            "venue_from_desk",
            "rebind_proxy",
            _NULL_NAME,
            id="venue-from-child-rebind-proxy",
        ),
        pytest.param(
            "venue_from_desk",
            "rebind_concrete",
            _NULL_NAME,
            id="venue-from-child-rebind-venue",
        ),
        pytest.param("venue", "save_other_proxy", _ENVELOPE, id="venue-save-other-proxy"),
        pytest.param("open_venue", "rebind_concrete", _ENVELOPE, id="proxy-rebind-concrete-base"),
        pytest.param("desk", "rebind_concrete", _ENVELOPE, id="child-rebind-parent"),
    ],
)
def test_a_modelform_names_the_null_of_its_instance_refused_as_any_row_of_its_model(
    form: str,
    scenario: str,
    expected: list[dict[str, object]],
) -> None:
    """A form ``save()`` that rebinds ``form.instance`` to a proxy or child row names its column.

    The consumer's ``save()`` binds ``form.instance`` to a new row of another class holding
    ``None`` on ``name`` and saves it. A row of the form's model (a proxy, a multi-table
    child) is the form's row, so its refusal is the field-keyed ``null``, also when the
    create's form was bound to a ``LendingDesk`` first (``get_form``) and the rebound row is
    an ``OpenVenue`` or a plain ``Venue``, neither of them a ``LendingDesk``. The concrete
    base under a proxy form, the parent under a child form, and another row saved while
    ``form.instance`` stays the form's own are the ``"__all__"`` envelope. Nothing is
    written.
    """
    before = _family_rows()
    _FAMILY.update(saved=scenario)
    root, form_class = _FAMILY_FORMS[form]
    document = f"mutation($d: {form_class}Input!) {{ {root}(data: $d) {{ {_FAMILY_RESULT} }} }}"
    answer = _post_family(root, document, {"d": {"name": None}})
    assert answer == {"result": None, "errors": expected}
    assert _family_rows() == before
