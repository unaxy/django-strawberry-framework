"""Raw relation identities use the target's stored key column through native HTTP filters.

Real temporary models expose decimal, datetime and relation-valued primary keys,
plus non-primary to_field links in each many-to-many direction. Ordinary JSON
arguments reach unbound consumer FilterSets. A plain target, a
visibility hook and an explicit RelatedFilter admission remain separate modes.
"""

from __future__ import annotations

import datetime
from collections.abc import Generator, Sequence
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING

import pytest
import strawberry
from django.core.validators import MinValueValidator
from django.db import connection as db_connection
from django.db import models as db_models
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list
from strawberry import relay
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import (
    call_method,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.relations import is_model_class
from django_strawberry_framework.views import DjangoGraphQLView

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-identity-columns/", _graphql_view)]


class _IdentityRow(db_models.Model):
    """A temporary row whose display names its stored identity."""

    class Meta:
        abstract = True

    @override
    def __str__(self) -> str:
        return str(read_attr(self, "pk"))


class _HttpValidatedKey(_IdentityRow):
    """An integer key whose model validator refuses stored values below ten."""

    code: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(10)],
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_validated_key"


class _HttpValidatedHolder(_IdentityRow):
    """A named row holding the real key's integer column."""

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    key: db_models.ForeignKey[_HttpValidatedKey | Combinable, _HttpValidatedKey] = (
        db_models.ForeignKey(
            _HttpValidatedKey,
            on_delete=db_models.CASCADE,
            related_name="+",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_validated_holder"


class _HttpHopKeyOwner(_IdentityRow):
    """A row reaching each ``_HOP_KEY_PREFIXES`` target by forward many-to-many."""

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    decimal_links: db_models.ManyToManyField[_HttpDecimalHopKey, db_models.Model] = (
        db_models.ManyToManyField("_HttpDecimalHopKey", related_name="+")
    )
    stamp_links: db_models.ManyToManyField[_HttpStampHopKey, db_models.Model] = (
        db_models.ManyToManyField("_HttpStampHopKey", related_name="+")
    )
    parent_decimal_links: db_models.ManyToManyField[_HttpParentDecimalHopKey, db_models.Model] = (
        db_models.ManyToManyField("_HttpParentDecimalHopKey", related_name="+")
    )
    parent_text_links: db_models.ManyToManyField[_HttpParentTextHopKey, db_models.Model] = (
        db_models.ManyToManyField("_HttpParentTextHopKey", related_name="+")
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_hop_key_owner"


class _HttpDecimalHopKey(_IdentityRow):
    """A decimal-keyed target ``_HttpHopKeyOwner`` reaches by forward M2M, reverse FK and reverse M2M."""

    code: db_models.DecimalField[str | float | Decimal | Combinable, Decimal] = (
        db_models.DecimalField(primary_key=True, max_digits=6, decimal_places=2)
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()
    owner: db_models.ForeignKey[_HttpHopKeyOwner | Combinable, _HttpHopKeyOwner] = (
        db_models.ForeignKey(
            _HttpHopKeyOwner,
            on_delete=db_models.CASCADE,
            related_name="decimal_rows",
        )
    )
    backers: db_models.ManyToManyField[_HttpHopKeyOwner, db_models.Model] = (
        db_models.ManyToManyField(
            _HttpHopKeyOwner,
            related_name="decimal_backs",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_decimal_hop_key"


class _HttpStampHopKey(_IdentityRow):
    """A datetime-keyed target ``_HttpHopKeyOwner`` reaches by forward M2M, reverse FK and reverse M2M."""

    code: db_models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ] = db_models.DateTimeField(primary_key=True)
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()
    owner: db_models.ForeignKey[_HttpHopKeyOwner | Combinable, _HttpHopKeyOwner] = (
        db_models.ForeignKey(
            _HttpHopKeyOwner,
            on_delete=db_models.CASCADE,
            related_name="stamp_rows",
        )
    )
    backers: db_models.ManyToManyField[_HttpHopKeyOwner, db_models.Model] = (
        db_models.ManyToManyField(
            _HttpHopKeyOwner,
            related_name="stamp_backs",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_stamp_hop_key"


class _HttpDecimalKeyParent(_IdentityRow):
    """A row whose unique decimal ``code`` a ``_HttpParentDecimalHopKey`` primary key references."""

    code: db_models.DecimalField[str | float | Decimal | Combinable, Decimal] = (
        db_models.DecimalField(unique=True, max_digits=6, decimal_places=2)
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_decimal_key_parent"


class _HttpParentDecimalHopKey(_IdentityRow):
    """A target keyed by a one-to-one primary key onto ``_HttpDecimalKeyParent.code``, not its pk."""

    parent: db_models.OneToOneField[_HttpDecimalKeyParent | Combinable, _HttpDecimalKeyParent] = (
        db_models.OneToOneField(
            _HttpDecimalKeyParent,
            on_delete=db_models.CASCADE,
            to_field="code",
            primary_key=True,
            related_name="+",
        )
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()
    owner: db_models.ForeignKey[_HttpHopKeyOwner | Combinable, _HttpHopKeyOwner] = (
        db_models.ForeignKey(
            _HttpHopKeyOwner,
            on_delete=db_models.CASCADE,
            related_name="parent_decimal_rows",
        )
    )
    backers: db_models.ManyToManyField[_HttpHopKeyOwner, db_models.Model] = (
        db_models.ManyToManyField(
            _HttpHopKeyOwner,
            related_name="parent_decimal_backs",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_parent_decimal_hop_key"


class _HttpTextKeyParent(_IdentityRow):
    """A row whose unique text ``slug`` a ``_HttpParentTextHopKey`` primary key references."""

    slug: db_models.TextField[str | Combinable, str] = db_models.TextField(unique=True)

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_text_key_parent"


class _HttpParentTextHopKey(_IdentityRow):
    """A target keyed by a one-to-one primary key onto ``_HttpTextKeyParent.slug``, not its pk."""

    parent: db_models.OneToOneField[_HttpTextKeyParent | Combinable, _HttpTextKeyParent] = (
        db_models.OneToOneField(
            _HttpTextKeyParent,
            on_delete=db_models.CASCADE,
            to_field="slug",
            primary_key=True,
            related_name="+",
        )
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()
    owner: db_models.ForeignKey[_HttpHopKeyOwner | Combinable, _HttpHopKeyOwner] = (
        db_models.ForeignKey(
            _HttpHopKeyOwner,
            on_delete=db_models.CASCADE,
            related_name="parent_text_rows",
        )
    )
    backers: db_models.ManyToManyField[_HttpHopKeyOwner, db_models.Model] = (
        db_models.ManyToManyField(
            _HttpHopKeyOwner,
            related_name="parent_text_backs",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_parent_text_hop_key"


_HOP_KEY_PREFIXES: dict[type[Model], str] = {
    _HttpDecimalHopKey: "decimal",
    _HttpStampHopKey: "stamp",
    _HttpParentDecimalHopKey: "parent_decimal",
    _HttpParentTextHopKey: "parent_text",
}


_STAMP_VISIBLE = datetime.datetime(2024, 1, 1, 12, tzinfo=datetime.timezone.utc)


_STAMP_HIDDEN = datetime.datetime(2024, 1, 2, 12, tzinfo=datetime.timezone.utc)


@pytest.fixture
def hop_key_owners() -> Generator[None, None, None]:
    """Real tables: ``alpha`` reaches each target's visible row, ``beta`` its hidden one, ``gamma`` none.

    Every to-many kind links the same pairs: ``alpha`` lists the visible row in its forward
    M2M, owns it by its reverse FK and backs it by its reverse M2M; ``beta`` does all three
    for the hidden row.
    """
    parents: tuple[type[Model], ...] = (_HttpDecimalKeyParent, _HttpTextKeyParent)
    targets = tuple(_HOP_KEY_PREFIXES)
    with db_connection.schema_editor() as editor:
        for model in (_HttpHopKeyOwner, *parents, *targets):
            editor.create_model(model)
    try:
        alpha, beta, _gamma = (
            _HttpHopKeyOwner.objects.create(name=name) for name in ("alpha", "beta", "gamma")
        )
        keyed: list[tuple[str, Model, Model]] = [
            (
                "decimal",
                _HttpDecimalHopKey.objects.create(code=Decimal("1.50"), visible=True, owner=alpha),
                _HttpDecimalHopKey.objects.create(code=Decimal("2.50"), visible=False, owner=beta),
            ),
            (
                "stamp",
                _HttpStampHopKey.objects.create(code=_STAMP_VISIBLE, visible=True, owner=alpha),
                _HttpStampHopKey.objects.create(code=_STAMP_HIDDEN, visible=False, owner=beta),
            ),
            (
                "parent_decimal",
                _HttpParentDecimalHopKey.objects.create(
                    parent=_HttpDecimalKeyParent.objects.create(code=Decimal("1.50")),
                    visible=True,
                    owner=alpha,
                ),
                _HttpParentDecimalHopKey.objects.create(
                    parent=_HttpDecimalKeyParent.objects.create(code=Decimal("2.50")),
                    visible=False,
                    owner=beta,
                ),
            ),
            (
                "parent_text",
                _HttpParentTextHopKey.objects.create(
                    parent=_HttpTextKeyParent.objects.create(slug="visible-slug"),
                    visible=True,
                    owner=alpha,
                ),
                _HttpParentTextHopKey.objects.create(
                    parent=_HttpTextKeyParent.objects.create(slug="hidden-slug"),
                    visible=False,
                    owner=beta,
                ),
            ),
        ]
        for prefix, visible, hidden in keyed:
            _ = call_method(read_attr(alpha, f"{prefix}_links"), "add", visible)
            _ = call_method(read_attr(beta, f"{prefix}_links"), "add", hidden)
            _ = call_method(read_attr(visible, "backers"), "add", alpha)
            _ = call_method(read_attr(hidden, "backers"), "add", beta)
        yield
    finally:
        with db_connection.schema_editor() as editor:
            for model in (*reversed(targets), *parents, _HttpHopKeyOwner):
                editor.delete_model(model)


class _HttpDecimalKeyChild(_IdentityRow):
    """A row keyed to a ``_HttpDecimalKeyParent`` by its unique ``code``, not its primary key."""

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    parent: db_models.ForeignKey[_HttpDecimalKeyParent | Combinable, _HttpDecimalKeyParent] = (
        db_models.ForeignKey(
            _HttpDecimalKeyParent,
            on_delete=db_models.CASCADE,
            to_field="code",
            related_name="+",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_decimal_key_child"


class _HttpCodedOwner(_IdentityRow):
    """A row carrying a unique ``code`` beside its primary key, linked to ``_HttpCodedTarget`` rows.

    ``targets`` runs through ``_HttpTargetCodedLink`` (keyed to the target by its ``code``),
    ``source_coded_targets`` through ``_HttpSourceCodedLink`` (keyed to this owner by its ``code``).
    """

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    code: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField(
        unique=True,
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()
    targets: db_models.ManyToManyField[_HttpCodedTarget, _HttpTargetCodedLink] = (
        db_models.ManyToManyField(
            "_HttpCodedTarget",
            through="_HttpTargetCodedLink",
            related_name="owners",
        )
    )
    source_coded_targets: db_models.ManyToManyField[_HttpCodedTarget, _HttpSourceCodedLink] = (
        db_models.ManyToManyField(
            "_HttpCodedTarget",
            through="_HttpSourceCodedLink",
            related_name="source_coded_owners",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_coded_owner"


class _HttpCodedTarget(_IdentityRow):
    """A row carrying a unique ``code`` beside its primary key, reached by ``_HttpCodedOwner`` rows."""

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    code: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField(
        unique=True,
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_coded_target"


class _HttpTargetCodedLink(_IdentityRow):
    """The ``_HttpCodedOwner.targets`` join row, keyed to the target by its ``code``."""

    owner: db_models.ForeignKey[_HttpCodedOwner | Combinable, _HttpCodedOwner] = (
        db_models.ForeignKey(
            _HttpCodedOwner,
            on_delete=db_models.CASCADE,
            related_name="+",
        )
    )
    target: db_models.ForeignKey[_HttpCodedTarget | Combinable, _HttpCodedTarget] = (
        db_models.ForeignKey(
            _HttpCodedTarget,
            on_delete=db_models.CASCADE,
            to_field="code",
            related_name="+",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_target_coded_link"


class _HttpSourceCodedLink(_IdentityRow):
    """The ``_HttpCodedOwner.source_coded_targets`` join row, keyed to the owner by its ``code``."""

    owner: db_models.ForeignKey[_HttpCodedOwner | Combinable, _HttpCodedOwner] = (
        db_models.ForeignKey(
            _HttpCodedOwner,
            on_delete=db_models.CASCADE,
            to_field="code",
            related_name="+",
        )
    )
    target: db_models.ForeignKey[_HttpCodedTarget | Combinable, _HttpCodedTarget] = (
        db_models.ForeignKey(
            _HttpCodedTarget,
            on_delete=db_models.CASCADE,
            related_name="+",
        )
    )

    class Meta(_IdentityRow.Meta):
        managed = False
        app_label = "library"
        db_table = "live_identity_source_coded_link"


_CODED_MODELS: tuple[type[Model], ...] = (
    _HttpCodedOwner,
    _HttpCodedTarget,
    _HttpTargetCodedLink,
    _HttpSourceCodedLink,
)


@pytest.fixture
def coded_links() -> Generator[None, None, None]:
    """Real tables: each row's ``code`` is another row's primary key.

    Owners ``alpha`` (pk 1, code 2), ``beta`` (pk 2, code 1) and the hidden ``gamma`` (pk 3,
    code 3); targets ``one`` (pk 1, code 2), ``two`` (pk 2, code 1) and the hidden ``three``
    (pk 3, code 3). Both many-to-manys link ``alpha``-``one``, ``beta``-``two`` and
    ``gamma``-``three``, so a leaf comparing a code where it takes a primary key answers
    the swapped partner.
    """
    with db_connection.schema_editor() as editor:
        for model in _CODED_MODELS:
            editor.create_model(model)
    try:
        for pk, code, name, visible in (
            (
                1,
                2,
                "one",
                True,
            ),
            (
                2,
                1,
                "two",
                True,
            ),
            (
                3,
                3,
                "three",
                False,
            ),
        ):
            owner_name = {"one": "alpha", "two": "beta", "three": "gamma"}[name]
            owner = _HttpCodedOwner.objects.create(
                pk=pk,
                code=code,
                name=owner_name,
                visible=visible,
            )
            target = _HttpCodedTarget.objects.create(pk=pk, code=code, name=name, visible=visible)
            _ = _HttpTargetCodedLink.objects.create(owner=owner, target=target)
            _ = _HttpSourceCodedLink.objects.create(owner=owner, target=target)
        # Root and target visibility deliberately disagree on this extra link.
        opposing_owner = _HttpCodedOwner.objects.create(
            pk=11,
            code=12,
            name="outside",
            visible=False,
        )
        opposing_target = _HttpCodedTarget.objects.create(
            pk=11,
            code=12,
            name="open-target",
            visible=True,
        )
        _HttpTargetCodedLink.objects.create(owner=opposing_owner, target=opposing_target)
        _HttpSourceCodedLink.objects.create(owner=opposing_owner, target=opposing_target)
        yield
    finally:
        with db_connection.schema_editor() as editor:
            for model in reversed(_CODED_MODELS):
                editor.delete_model(model)


def _filterset(
    source: type[Model],
    relation: str,
    mode: str,
) -> tuple[type[FilterSet], tuple[type[DjangoType], ...]]:
    target = require(source._meta.get_field(relation).related_model, is_model_class)
    namespace: dict[str, object] = {
        "Meta": type("Meta", (), {"model": source, "fields": {relation: ["exact", "in"]}}),
    }
    targets: tuple[type[DjangoType], ...] = ()
    if mode != "plain":

        def visible(
            _cls: type[DjangoType],
            queryset: QuerySet[Model],
            _info: object,
        ) -> QuerySet[Model]:
            return queryset.filter(visible=True) if mode == "scoped" else queryset

        target_type = type(
            "TargetScope",
            (DjangoType,),
            {
                "Meta": type("Meta", (), {"model": target, "fields": ("visible",)}),
                "get_queryset": classmethod(visible),
            },
        )
        targets = (target_type,)
        if mode == "declared":
            target_set = type(
                "Child",
                (FilterSet,),
                {"Meta": type("Meta", (), {"model": target, "fields": ()})},
            )
            namespace["hop"] = RelatedFilter(
                target_set,
                field_name=relation,
                queryset=target._default_manager.filter(visible=True),
            )
    return type("RootFilter", (FilterSet,), namespace), targets


def _schema(
    source: type[Model],
    filterset: type[FilterSet],
    targets: Sequence[type[DjangoType]] = (),
) -> DjangoSchema:
    output = type(
        "IdentityRoot",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": source, "fields": ("name",)})},
    )

    @strawberry.type
    class Query:
        def _rows(self, info: strawberry.Info[object, object], where: JSON) -> QuerySet[Model]:
            return filterset.apply_sync(where, source._default_manager.order_by("name"), info)

        def _all_rows(self) -> QuerySet[Model]:
            return source._default_manager.order_by("name")

        rows: QuerySet[Model] = strawberry.field(resolver=_rows, graphql_type=list[output])
        all_rows: QuerySet[Model] = strawberry.field(resolver=_all_rows, graphql_type=list[output])

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=targets,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _post(schema: DjangoSchema, where: JSONObject) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
                variables={"where": where},
                url="/graphql-identity-columns/",
            )
    finally:
        _CURRENT["schema"] = None


def _names(source: type[Model]) -> list[str]:
    return [
        require_instance(read_attr(row, "name"), str)
        for row in source._default_manager.order_by("name")
    ]


def _expected(
    names: Sequence[str],
    *,
    universe: Sequence[str] = ("alpha", "beta", "gamma"),
) -> JSONObject:
    return {
        "data": {
            "rows": [{"name": name} for name in names],
            "allRows": [{"name": name} for name in universe],
        },
    }


def _wire_members(members: Sequence[object]) -> list[object]:
    """JSON strings carry the column spellings a consumer's raw search accepts."""
    return [
        value.isoformat()
        if isinstance(value, datetime.datetime)
        else str(value)
        if isinstance(value, Decimal)
        else value
        for value in members
    ]


_HIDDEN = object()


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("hop_key_owners")
@pytest.mark.parametrize("mode", ["plain", "scoped", "declared"])
@pytest.mark.parametrize(
    (
        "target",
        "members",
        "negated",
        "expected",
    ),
    [
        pytest.param(_HttpDecimalHopKey, [Decimal("NaN")], False, [], id="decimal-nan"),
        pytest.param(_HttpDecimalHopKey, [Decimal("Infinity")], False, [], id="decimal-infinity"),
        pytest.param(
            _HttpDecimalHopKey,
            [Decimal("-Infinity")],
            False,
            [],
            id="decimal-neg-infinity",
        ),
        pytest.param(
            _HttpDecimalHopKey,
            [Decimal("NaN")],
            True,
            ["alpha", "beta", "gamma"],
            id="decimal-not-nan",
        ),
        pytest.param(
            _HttpDecimalHopKey,
            [Decimal("Infinity"), Decimal("1.50")],
            False,
            ["alpha"],
            id="decimal-infinity-beside-visible",
        ),
        pytest.param(
            _HttpDecimalHopKey,
            [Decimal("1.50")],
            False,
            ["alpha"],
            id="decimal-visible",
        ),
        pytest.param(_HttpDecimalHopKey, [Decimal("2.50")], False, _HIDDEN, id="decimal-hidden"),
        pytest.param(_HttpDecimalHopKey, [Decimal("9.99")], False, [], id="decimal-missing"),
        pytest.param(
            _HttpStampHopKey,
            [datetime.datetime(1, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=14)))],
            False,
            [],
            id="stamp-below-range",
        ),
        pytest.param(
            _HttpStampHopKey,
            [
                datetime.datetime(
                    9999,
                    12,
                    31,
                    23,
                    59,
                    59,
                    tzinfo=datetime.timezone(datetime.timedelta(hours=-14)),
                ),
            ],
            False,
            [],
            id="stamp-above-range",
        ),
        pytest.param(
            _HttpStampHopKey,
            [datetime.datetime(1, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=14)))],
            True,
            ["alpha", "beta", "gamma"],
            id="stamp-not-below-range",
        ),
        pytest.param(_HttpStampHopKey, [_STAMP_VISIBLE], False, ["alpha"], id="stamp-visible"),
        pytest.param(_HttpStampHopKey, [_STAMP_HIDDEN], False, _HIDDEN, id="stamp-hidden"),
        pytest.param(
            _HttpStampHopKey,
            [datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)],
            False,
            [],
            id="stamp-missing",
        ),
        pytest.param(
            _HttpParentDecimalHopKey,
            [Decimal("1.50")],
            False,
            ["alpha"],
            id="parent-decimal-visible",
        ),
        pytest.param(
            _HttpParentDecimalHopKey,
            [Decimal("2.50")],
            False,
            _HIDDEN,
            id="parent-decimal-hidden",
        ),
        pytest.param(
            _HttpParentDecimalHopKey,
            [Decimal("9.99")],
            False,
            [],
            id="parent-decimal-missing",
        ),
        pytest.param(
            _HttpParentTextHopKey,
            ["visible-slug"],
            False,
            ["alpha"],
            id="parent-text-visible",
        ),
        pytest.param(
            _HttpParentTextHopKey,
            ["hidden-slug"],
            False,
            _HIDDEN,
            id="parent-text-hidden",
        ),
        pytest.param(_HttpParentTextHopKey, ["missing-slug"], False, [], id="parent-text-missing"),
    ],
)
def test_rich_relation_key_values_keep_membership_and_visibility_semantics(
    *,
    target: type[Model],
    members: list[object],
    negated: bool,
    expected: object,
    mode: str,
) -> None:
    """Unrepresentable keys drop beside matching members; hidden and missing keys stay distinct."""
    relation = _HOP_KEY_PREFIXES[target] + "_links"
    filterset, targets = _filterset(_HttpHopKeyOwner, relation, mode)
    leaf: JSONObject = {relation: {"exact": _wire_members(members)}}
    where: JSONObject = {"not_": leaf} if negated else leaf
    names = (
        (["beta"] if mode == "plain" else [])
        if expected is _HIDDEN
        else [require_instance(name, str) for name in json_list(expected)]
    )
    payload = _post(_schema(_HttpHopKeyOwner, filterset, targets), where)
    assert payload == _expected(names), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("hop_key_owners")
@pytest.mark.parametrize("mode", ["plain", "scoped", "declared"])
@pytest.mark.parametrize("kind", ["rows", "backs"], ids=["reverse-fk", "reverse-m2m"])
@pytest.mark.parametrize(
    ("target", "member"),
    [
        pytest.param(_HttpDecimalHopKey, "1.50", id="decimal"),
        pytest.param(_HttpStampHopKey, _STAMP_VISIBLE.isoformat(), id="datetime"),
        pytest.param(_HttpParentDecimalHopKey, "1.50", id="one-to-one-decimal-to-field"),
        pytest.param(_HttpParentTextHopKey, "visible-slug", id="one-to-one-text-to-field"),
    ],
)
def test_each_reverse_relation_kind_reads_the_rich_target_key_column(
    target: type[Model],
    member: str,
    kind: str,
    mode: str,
) -> None:
    """Reverse FK and M2M links compare the same stored key as their forward-M2M control."""
    relation = _HOP_KEY_PREFIXES[target] + "_" + kind
    filterset, targets = _filterset(_HttpHopKeyOwner, relation, mode)
    payload = _post(_schema(_HttpHopKeyOwner, filterset, targets), {relation: {"exact": [member]}})
    assert payload == _expected(["alpha"]), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("hop_key_owners")
@pytest.mark.parametrize("mode", ["plain", "scoped", "declared"])
@pytest.mark.parametrize(
    "kind",
    ["links", "rows", "backs"],
    ids=["forward-m2m", "reverse-fk", "reverse-m2m"],
)
def test_many_side_in_lookup_keeps_the_same_identity_list_policy(kind: str, mode: str) -> None:
    """The separate `in` generation arm drops an invalid decimal beside the matching member."""
    relation = "decimal_" + kind
    filterset, targets = _filterset(_HttpHopKeyOwner, relation, mode)
    payload = _post(
        _schema(_HttpHopKeyOwner, filterset, targets),
        {relation: {"in_": ["Infinity", "1.50"]}},
    )
    assert payload == _expected(["alpha"]), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("lookup", ["exact", "in_"], ids=["single-key", "membership"])
def test_forward_decimal_to_field_relation_still_accepts_the_targets_large_integer_pk(
    lookup: str,
) -> None:
    """A target PK outside the Decimal(6,2) link column's range still selects only its child."""
    with db_connection.schema_editor() as editor:
        editor.create_model(_HttpDecimalKeyParent)
        editor.create_model(_HttpDecimalKeyChild)
    try:
        parent = _HttpDecimalKeyParent.objects.create(pk=1234567, code=Decimal("1.50"))
        other = _HttpDecimalKeyParent.objects.create(code=Decimal("2.50"))
        _HttpDecimalKeyChild.objects.create(name="kept", parent=parent)
        _HttpDecimalKeyChild.objects.create(name="other", parent=other)
        filterset = type(
            "DecimalChildFilter",
            (FilterSet,),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {"model": _HttpDecimalKeyChild, "fields": {"parent": ["exact", "in"]}},
                ),
            },
        )
        value: object = 1234567 if lookup == "exact" else [1234567]
        payload = _post(_schema(_HttpDecimalKeyChild, filterset), {"parent": {lookup: value}})
        assert payload == _expected(["kept"], universe=["kept", "other"]), payload
    finally:
        with db_connection.schema_editor() as editor:
            editor.delete_model(_HttpDecimalKeyChild)
            editor.delete_model(_HttpDecimalKeyParent)


_CODED_PATHS = [
    pytest.param(_HttpCodedOwner, "targets", "alpha", id="forward-target-to-field"),
    pytest.param(_HttpCodedTarget, "source_coded_owners", "one", id="reverse-target-to-field"),
    pytest.param(_HttpCodedOwner, "source_coded_targets", "alpha", id="forward-source-to-field"),
    pytest.param(_HttpCodedTarget, "owners", "one", id="reverse-source-to-field"),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("coded_links")
@pytest.mark.parametrize("mode", ["plain", "scoped", "declared"])
@pytest.mark.parametrize("lookup", ["exact", "in_"])
@pytest.mark.parametrize(("source", "relation", "name"), _CODED_PATHS)
def test_through_link_direction_and_lookup_compare_the_requested_target_pk(
    source: type[Model],
    relation: str,
    name: str,
    lookup: str,
    mode: str,
) -> None:
    """A target code equal to another target's PK cannot swap either side of a through link."""
    filterset, targets = _filterset(source, relation, mode)
    universe = _names(source)
    payload = _post(_schema(source, filterset, targets), {relation: {lookup: [1]}})
    assert payload == _expected([name], universe=universe), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("coded_links")
@pytest.mark.parametrize("mode", ["plain", "scoped", "declared"])
@pytest.mark.parametrize(
    "case",
    [
        "second-pk",
        "both",
        "hidden-pk",
        "missing-pk",
    ],
)
def test_through_target_to_field_membership_keeps_its_visible_and_missing_key_contract(
    case: str,
    mode: str,
) -> None:
    """Both requested keys contribute, and only the plain target admits the real hidden third row."""
    if case == "second-pk":
        members, names = [2], ["beta"]
    elif case == "both":
        members, names = [1, 2], ["alpha", "beta"]
    elif case == "hidden-pk":
        members, names = [3], (["gamma"] if mode == "plain" else [])
    else:
        members, names = [4], []
    filterset, targets = _filterset(_HttpCodedOwner, "targets", mode)
    payload = _post(_schema(_HttpCodedOwner, filterset, targets), {"targets": {"exact": members}})
    assert payload == _expected(names, universe=_names(_HttpCodedOwner)), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("coded_links")
@pytest.mark.parametrize("lookup", ["exact", "in"], ids=["equality", "membership"])
@pytest.mark.parametrize(
    (
        "source",
        "relation",
        "wire",
        "name",
    ),
    [
        pytest.param(_HttpCodedOwner, "targets", "targets", "alpha", id="forward"),
        pytest.param(
            _HttpCodedTarget,
            "source_coded_owners",
            "sourceCodedOwners",
            "one",
            id="reverse",
        ),
    ],
)
def test_relay_through_target_to_field_uses_the_decoded_primary_key(
    source: type[Model],
    relation: str,
    wire: str,
    name: str,
    lookup: str,
) -> None:
    """The real target GlobalID selects its linked source, never the source with a swapped target code."""
    target = require(source._meta.get_field(relation).related_model, is_model_class)
    source_set = type(
        "RelayCodedSourceFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": source, "fields": {relation: ["exact", "in"]}})},
    )
    target_type = type(
        "RelayCodedTarget",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": target, "fields": ("id", "name"), "interfaces": (relay.Node,)},
            ),
        },
    )
    source_type = type(
        "RelayCodedRoot",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": source,
                    "fields": ("id", "name"),
                    "filterset_class": source_set,
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(source_type)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        types=[target_type],
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(
                f"query($ids: [String!]!) {{ rows(filter: {{ {wire}: {{ {lookup}: $ids }} }}) "
                "{ edges { node { name } } } }",
                variables={"ids": [global_id_for(target_type, 1)]},
                url="/graphql-identity-columns/",
            )
    finally:
        _CURRENT["schema"] = None
    assert payload == {"data": {"rows": {"edges": [{"node": {"name": name}}]}}}, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("coded_links")
@pytest.mark.parametrize("mode", ["plain", "scoped", "declared"])
@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_through_link_visibility_belongs_to_the_target_independently_of_the_root(
    direction: str,
    mode: str,
) -> None:
    """A hidden root matches a visible target; the reverse hop refuses the hidden owner."""
    if direction == "forward":
        source, relation = _HttpCodedOwner, "targets"
        names = ["outside"]
    else:
        source, relation = _HttpCodedTarget, "source_coded_owners"
        names = ["open-target"] if mode == "plain" else []
    filterset, targets = _filterset(source, relation, mode)
    payload = _post(_schema(source, filterset, targets), {relation: {"exact": [11]}})
    assert payload == _expected(names, universe=_names(source)), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("lookup", "value", "names"),
    [
        pytest.param("exact", 5, ["five"], id="single"),
        pytest.param("in_", [5], ["five"], id="membership"),
        pytest.param("in_", [5, 12], ["five", "twelve"], id="both-members"),
    ],
)
def test_relation_identity_reads_a_stored_key_that_its_model_validator_refuses(
    lookup: str,
    value: object,
    names: list[str],
) -> None:
    """Looking up a stored identity does not rerun its target model's write-time validator."""
    with db_connection.schema_editor() as editor:
        editor.create_model(_HttpValidatedKey)
        editor.create_model(_HttpValidatedHolder)
    try:
        for code, name in ((5, "five"), (12, "twelve")):
            _HttpValidatedHolder.objects.create(
                name=name,
                key=_HttpValidatedKey.objects.create(code=code),
            )
        filterset = type(
            "ValidatedKeyFilter",
            (FilterSet,),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {"model": _HttpValidatedHolder, "fields": {"key": ["exact", "in"]}},
                ),
            },
        )
        payload = _post(_schema(_HttpValidatedHolder, filterset), {"key": {lookup: value}})
        assert payload == _expected(names, universe=["five", "twelve"]), payload
    finally:
        with db_connection.schema_editor() as editor:
            editor.delete_model(_HttpValidatedHolder)
            editor.delete_model(_HttpValidatedKey)
