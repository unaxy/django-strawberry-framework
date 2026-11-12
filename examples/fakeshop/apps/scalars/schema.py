"""GraphQL schema for scalar conversion, overrides, optimizer visibility, and file/image uploads.

Exposes ``ScalarSpecimen`` and its all-nullable counterpart
``NullableScalarSpecimen`` with every concrete scalar field selected so a
single live ``/graphql/`` query exercises both the non-null and nullable
branch of each non-trivial entry in the package's converter table. See
``apps/scalars/models.py`` for the rationale on which converter rows live
here vs. in ``tests/``.

The two models are linked via ``NullableScalarSpecimen.partner`` (cross-
model nullable FK with ``on_delete=SET_NULL``) so a single GraphQL query
can traverse both shapes - and ``ScalarSpecimen.nullable_partners`` exposes
the reverse side for composite queries.

``scalar_specimen_by_signed_big`` accepts a ``BigInt!`` argument so the
input-position parser (``BigInt.parse_value``) is exercised end-to-end -
both for the decimal-string literal form and the JSON-int literal form.

``ScalarSpecimenTagType`` declares a custom ``get_queryset(cls, queryset,
info)`` classmethod filtering to ``active=True``. The optimizer
downgrades any forward-FK select_related into that type to a
``Prefetch(queryset=cls.get_queryset(...))`` so the consumer's filter
survives plan execution. Visible in the live HTTP test by an inactive
tag resolving to ``null`` on the source specimen.

The ``ScalarSpecimen`` create / update mutations write the ``occurred_at`` /
``occurred_time`` columns through all three write flavors (``DjangoMutation``,
``DjangoModelFormMutation`` over ``forms.ScalarSpecimenTemporalForm``,
``SerializerMutation`` over ``serializers.ScalarSpecimenTemporalSerializer``), so a
datetime or time the database cannot store is refused live on each. The
``DayInstantForm`` pair writes ``occurred_on`` through
``forms.ScalarSpecimenDayInstantForm``'s ``clean_occurred_on``, which answers an aware
datetime for the ``DateField``: one whose date in the default time zone leaves years
1..9999 is the field's ``invalid`` error. ``UpdateScalarSpecimenViaLockedStampForm`` writes
through ``forms.ScalarSpecimenLockedStampForm``, whose disabled ``occurred_at``,
``occurred_time`` and ``external_id`` keep their stored values, microseconds included. The
``SplitForm`` pairs write ``occurred_at``
through ``forms.ScalarSpecimenSplitStampForm``'s ``SplitDateTimeField``, whose widget reads
a date key and a time key: unprefixed, under the form's own prefix (``PrefixedSplitForm``),
and from a copy a ``get_form`` keys under that prefix itself (``RekeyedSplitForm``); a
datetime whose wall clock in the current time zone leaves years 1..9999 is the field's
``invalid`` error there. The ``ViaPosted`` pairs bind a ``get_form_kwargs``
mapping holding each value as its text (``forms.as_posted_text``): over the temporal form's
one-key ``DateTimeField`` (``PostedForm``) the text is parsed and stored, while the split
widget's ``decompress`` cannot split the text of a datetime (``PostedSplitForm``), a
``ConfigurationError`` before ``is_valid()``. The ``NullableScalarSpecimen`` ``ViaForm``
pair writes the ``null=True`` ``flag`` column through
``forms.NullableScalarSpecimenFlagForm``'s checkbox and the ``null=True`` ``payload`` JSON
and ``score`` float columns through its ``CharField``, so an explicit ``null``, or a create
omitting the field, stores ``NULL``, while an update omitting ``label``, ``flag``,
``payload`` or ``score`` keeps the stored value, ``NULL`` included, where the form field's
own cleaning would rewrite it. The ``ViaJsonTextForm`` pair writes ``payload`` through
``forms.NullableScalarSpecimenJsonTextForm``'s ``JsonTextField``, typed ``String``, which parses
the JSON text sent and presents the stored value as its JSON text to an update omitting it.

The ``UniqueScalarSpecimen`` ``ViaForm`` and ``ViaSerializer`` pairs write columns each under
a uniqueness rule (``unique=True``, ``unique_together``, a conditional ``UniqueConstraint``)
through ``forms.UniqueScalarSpecimenForm`` and ``serializers.UniqueScalarSpecimenSerializer``,
whose ``validate_opened_at`` reads the wall clock sent as shop time;
``createUniqueScalarSpecimenViaUnboundedAmountSerializer`` writes ``amount`` through a
``DecimalField`` holding no digits. A value the database cannot store is the field's error
before a uniqueness check binds it in a query.
``createScalarSpecimenTagWithUniqueSpecimens`` writes a tag and a bundle of specimens, a
nested ``specimens`` list of those serializer items, through
``serializers.TagWithUniqueSpecimensSerializer``, whose own ``create()`` writes each item; a
value an item's uniqueness validator cannot bind in its query is that item field's error at
its nested path.

``all_scalar_specimens_by_parent_stamp`` lists specimens over a queryset holding a
``FilteredRelation("parent")`` alias named ``par`` and two annotations, ``parent_lag`` (the
duration from the parent's ``occurred_at``) and ``child_count``, filtered by
``filters.ScalarSpecimenParentStampFilter``, whose ``parentDayOf`` and ``parentDaysSpan``
paths cross that alias and whose ``parentLag*`` / ``childCount*`` paths name the
annotations.
"""

import strawberry
from django.db.models import (
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    FilteredRelation,
    Manager,
    Model,
    QuerySet,
)
from django.forms import ModelForm
from strawberry.types import Info
from typing_extensions import override

from apps.scalars import filters, forms, models, orders, serializers

# ``SerializerMutation`` is imported BY NAME (never via star import): the root ``__all__``
# omits it while DRF is a soft dependency, so the root ``__getattr__`` resolves it on demand.
from django_strawberry_framework import (
    BigInt,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    NestedSerializerConfig,
    SerializerMutation,
    auto,
)
from django_strawberry_framework.filters import FilterInput
from django_strawberry_framework.orders import OrderInput


class ScalarSpecimenTagType(DjangoType):
    """``DjangoType`` with a custom ``get_queryset`` filtering to ``active=True``.

    The classmethod is the consumer-facing API the optimizer detects via
    ``has_custom_get_queryset`` to trigger the ``Prefetch`` downgrade: any forward FK whose target
    type declares ``get_queryset`` is planned as ``Prefetch(queryset)``
    rather than ``select_related`` so the filter survives end-to-end.
    """

    @classmethod
    @override
    def get_queryset(
        cls,
        queryset: QuerySet[models.ScalarSpecimenTag],
        info: Info,
    ) -> QuerySet[models.ScalarSpecimenTag]:
        return queryset.filter(active=True)

    class Meta:
        model = models.ScalarSpecimenTag
        fields = (
            "id",
            "label",
            "active",
            "tagged_specimens",
        )
        filterset_class = filters.ScalarSpecimenTagFilter
        orderset_class = orders.ScalarSpecimenTagOrder


class ScalarSpecimenType(DjangoType):
    """``DjangoType`` exposing every converted scalar on ``ScalarSpecimen``."""

    class Meta:
        model = models.ScalarSpecimen
        fields = (
            "id",
            "label",
            "flag",
            "score",
            "price",
            "occurred_on",
            "occurred_at",
            "occurred_time",
            "payload",
            "external_id",
            "signed_big",
            "unsigned_big",
            "parent",
            "children",
            "nullable_partners",
            "tag",
        )
        filterset_class = filters.ScalarSpecimenFilter
        orderset_class = orders.ScalarSpecimenOrder
        # Explicit now that a second type wraps the same model: a relation to
        # ``ScalarSpecimen`` resolves here, not to the parent-stamp sibling.
        primary = True


class ScalarSpecimenParentStampType(DjangoType):
    """``ScalarSpecimen`` filtered through a ``FilteredRelation`` alias.

    ``primary = False``: ``ScalarSpecimenType`` stays the type a relation to
    ``ScalarSpecimen`` resolves to, and this one is reachable only through
    ``allScalarSpecimensByParentStamp``, whose queryset holds the ``par`` alias
    ``filters.ScalarSpecimenParentStampFilter`` crosses.
    """

    class Meta:
        model = models.ScalarSpecimen
        fields = ("id", "label")
        filterset_class = filters.ScalarSpecimenParentStampFilter
        primary = False


class NullableScalarSpecimenType(DjangoType):
    """``DjangoType`` exposing every converted scalar on ``NullableScalarSpecimen``.

    Every scalar field is nullable on the model so introspection reports the
    bare ``SCALAR`` shape (no ``NON_NULL`` wrapper). The ``partner`` FK is
    nullable too, exercising forward-FK selection where the related instance
    may be absent.
    """

    class Meta:
        model = models.NullableScalarSpecimen
        fields = (
            "id",
            "label",
            "flag",
            "score",
            "price",
            "occurred_on",
            "occurred_at",
            "occurred_time",
            "payload",
            "external_id",
            "signed_big",
            "unsigned_big",
            "partner",
        )
        filterset_class = filters.NullableScalarSpecimenFilter
        orderset_class = orders.NullableScalarSpecimenOrder


def _override_specimen_score(root: strawberry.Parent[models.OverrideSpecimen]) -> int:
    return root.score


class OverriddenScalarSpecimenType(DjangoType):
    """Demonstrates the consumer-authored field corners (spec-029) plus ``auto``.

    ``_build_annotations`` skips auto-synthesis for any consumer-authored field,
    so ``manage.py inspect_django_type OverriddenScalarSpecimenType`` names the row
    that actually produced each field in its converter column - a consumer
    override, never the auto ``SCALAR_MAP`` converter:

    * ``quantity`` - annotation-only override. The ``IntegerField`` would
      auto-convert to ``Int!``; the ``float | None`` annotation forces a nullable
      ``Float`` (``consumer annotation (scalar)``), decoupling the GraphQL type
      from the column without a migration.
    * ``token`` - annotation over the unsupported ``Base36Field``. The column has
      no ``SCALAR_MAP`` entry, so the ``token: str`` annotation is the escape
      hatch that lets it build at all (``consumer annotation (scalar)``).
    * ``score`` - the ``name: T = strawberry.field(resolver=...)`` overlap idiom:
      the annotation fixes the type, the assignment supplies the resolver
      (``consumer annotation + strawberry.field (scalar)``).
    * ``label`` - an assigned ``@strawberry.field`` resolver shadowing the column
      (``consumer strawberry.field (scalar)``).

    The fifth corner is the inverse of the four overrides:

    * ``note`` - declared as ``note: auto``. ``auto`` is "declare-but-infer": the
      field is listed as a class annotation (so every field is co-located here
      rather than split between annotations and the ``Meta.fields`` tuple), but its
      type is synthesized from the model exactly as bare selection would
      (``TextField`` -> ``String!``). It is *not* a consumer override, so its
      converter column still names the auto ``SCALAR_MAP`` row. Selection still
      belongs to ``Meta.fields``; ``auto`` never adds a field.
    """

    quantity: float | None
    token: str
    score: int = strawberry.field(resolver=_override_specimen_score)
    note: auto

    @strawberry.field
    @staticmethod
    def label(root: strawberry.Parent[models.OverrideSpecimen]) -> str:
        """Assigned-resolver override; upper-cases the column so the override is observable."""
        return root.label.upper()

    class Meta:
        model = models.OverrideSpecimen
        fields = (
            "id",
            "label",
            "quantity",
            "score",
            "token",
            "note",
        )


class MediaSpecimenType(DjangoType):
    """``DjangoType`` over a ``FileField`` + ``ImageField`` model (spec-037).

    On read, ``attachment`` converts to the structured ``DjangoFileType`` and
    ``image`` to ``DjangoImageType`` - and both are **nullable by default** in
    the live SDL even though the Django columns are required, because an empty /
    absent stored file resolves the whole object to ``null`` (spec-037
    Decision 4). Not Relay-Node-shaped (matching the other scalar specimens), so
    the generated mutation payloads carry the row in the ``result`` slot and
    ``updateMediaSpecimen`` locates its row by the raw pk ``id:``.
    """

    class Meta:
        model = models.MediaSpecimen
        fields = (
            "id",
            "label",
            "attachment",
            "image",
        )
        # Explicit now that a second type wraps the same model: a relation to
        # ``MediaSpecimen`` resolves here, not to the path-bearing sibling.
        primary = True


class UniqueScalarSpecimenType(DjangoType):
    """``DjangoType`` over ``UniqueScalarSpecimen``: its form and serializer writes' payload."""

    class Meta:
        model = models.UniqueScalarSpecimen
        fields = (
            "id",
            "label",
            "opened_time",
            "opened_at",
            "amount",
            "active",
        )


class MediaSpecimenWithPathType(DjangoType):
    """The ``Meta.filesystem_path_fields`` opt-in, demonstrated on ``attachment`` (spec-048).

    The default file/image output objects publish no filesystem path at all; a
    deployment that genuinely serves one names the column here, and that column
    alone resolves to the path-bearing ``DjangoFilePathType``. ``image`` is
    deliberately NOT named, so the live schema also demonstrates that the opt-in
    is per column rather than per type.

    ``primary = False``: ``MediaSpecimenType`` stays the type a relation to
    ``MediaSpecimen`` resolves to, and this one is reachable only through its own
    root field.

    The columns are selected by ``Meta.exclude`` where ``MediaSpecimenType``
    uses ``Meta.fields``: both publish the same four columns, so the live schema
    shows a file and an image column dropped by either selection form, with no
    output field and no generated file resolver for the excluded pair.
    """

    class Meta:
        model = models.MediaSpecimen
        exclude = ("optional_attachment", "spare_image")
        filesystem_path_fields = ("attachment",)
        primary = False


@strawberry.type
class Query:
    """Scalars coverage root fields."""

    def _all_media_specimens_with_path(self) -> list[models.MediaSpecimen]:
        """Root field for the filesystem-path opt-in demonstration type (spec-048)."""
        return list(models.MediaSpecimen.objects.order_by("id"))

    all_media_specimens_with_path: list[models.MediaSpecimen] = strawberry.field(
        resolver=_all_media_specimens_with_path,
        graphql_type=list[MediaSpecimenWithPathType],
    )

    def _all_override_specimens(self) -> list[models.OverrideSpecimen]:
        """Root field for the consumer-authored field-override demonstration type."""
        return list(models.OverrideSpecimen.objects.order_by("id"))

    all_override_specimens: list[models.OverrideSpecimen] = strawberry.field(
        resolver=_all_override_specimens,
        graphql_type=list[OverriddenScalarSpecimenType],
    )

    def _all_media_specimens(self) -> list[models.MediaSpecimen]:
        """Root field for the file/image read-output demonstration type (spec-037)."""
        return list(models.MediaSpecimen.objects.order_by("id"))

    all_media_specimens: list[models.MediaSpecimen] = strawberry.field(
        resolver=_all_media_specimens,
        graphql_type=list[MediaSpecimenType],
    )

    def _all_scalar_specimens(
        self,
        info: Info,
        filter: FilterInput[filters.ScalarSpecimenFilter] | None = None,  # noqa: A002 - the GraphQL argument name
        order_by: list[OrderInput[orders.ScalarSpecimenOrder]] | None = None,
    ) -> QuerySet[models.ScalarSpecimen]:
        """Root field listing scalar specimens, filtered and ordered by the optional arguments."""
        queryset = models.ScalarSpecimen.objects.order_by("id")
        if filter is not None:
            queryset = filters.ScalarSpecimenFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ScalarSpecimenOrder.apply_sync(order_by, queryset, info)
        return queryset

    all_scalar_specimens: QuerySet[models.ScalarSpecimen] = strawberry.field(
        resolver=_all_scalar_specimens,
        graphql_type=list[ScalarSpecimenType],
    )

    def _all_scalar_specimens_by_parent_stamp(
        self,
        info: Info,
        filter: FilterInput[filters.ScalarSpecimenParentStampFilter] | None = None,  # noqa: A002 - the GraphQL argument name
    ) -> QuerySet[models.ScalarSpecimen]:
        """Root field listing scalar specimens over a queryset aliasing ``parent`` as ``par``.

        The ``FilteredRelation`` alias and the ``parent_lag`` / ``child_count`` annotations
        exist only on this queryset, so the filter's ``par__occurred_at``, ``parent_lag`` and
        ``child_count`` paths resolve only against the queryset it runs on.
        """
        queryset = models.ScalarSpecimen.objects.alias(par=FilteredRelation("parent"))
        queryset = queryset.annotate(
            parent_lag=ExpressionWrapper(
                F("occurred_at") - F("par__occurred_at"),
                output_field=DurationField(),
            ),
            child_count=Count("children"),
        )
        queryset = queryset.order_by("id")
        if filter is not None:
            queryset = filters.ScalarSpecimenParentStampFilter.apply_sync(filter, queryset, info)
        return queryset

    all_scalar_specimens_by_parent_stamp: QuerySet[models.ScalarSpecimen] = strawberry.field(
        resolver=_all_scalar_specimens_by_parent_stamp,
        graphql_type=list[ScalarSpecimenParentStampType],
    )

    def _all_scalar_specimens_via_manager(self) -> Manager[models.ScalarSpecimen]:
        """Resolver returning a bare ``Manager`` instead of ``Manager.all()``.

        Consumers frequently write ``return Model.objects`` rather than
        ``return Model.objects.all()``. Both shapes are equivalent for
        Strawberry's default resolver path, but the optimizer's
        ``isinstance(QuerySet)`` gate must coerce the Manager via
        ``.all()`` before the plan can be applied - otherwise the
        Manager passes through unoptimized and the consumer pays N+1 on
        any forward-FK selection. This field exposes that coercion path
        end-to-end (no ``DjangoListField`` wrapping involved).
        """
        return models.ScalarSpecimen.objects

    all_scalar_specimens_via_manager: Manager[models.ScalarSpecimen] = strawberry.field(
        resolver=_all_scalar_specimens_via_manager,
        graphql_type=list[ScalarSpecimenType],
    )

    def _all_nullable_scalar_specimens(
        self,
        info: Info,
        filter: FilterInput[filters.NullableScalarSpecimenFilter] | None = None,  # noqa: A002 - the GraphQL argument name
        order_by: list[OrderInput[orders.NullableScalarSpecimenOrder]] | None = None,
    ) -> QuerySet[models.NullableScalarSpecimen]:
        """Root field listing nullable scalar specimens, filtered and ordered by the optional arguments."""
        queryset = models.NullableScalarSpecimen.objects.order_by("id")
        if filter is not None:
            queryset = filters.NullableScalarSpecimenFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.NullableScalarSpecimenOrder.apply_sync(order_by, queryset, info)
        return queryset

    all_nullable_scalar_specimens: QuerySet[models.NullableScalarSpecimen] = strawberry.field(
        resolver=_all_nullable_scalar_specimens,
        graphql_type=list[NullableScalarSpecimenType],
    )

    def _all_scalar_specimen_tags(
        self,
        info: Info,
        filter: FilterInput[filters.ScalarSpecimenTagFilter] | None = None,  # noqa: A002 - the GraphQL argument name
        order_by: list[OrderInput[orders.ScalarSpecimenTagOrder]] | None = None,
    ) -> QuerySet[models.ScalarSpecimenTag]:
        """Root field listing scalar specimen tags, filtered and ordered by the optional arguments."""
        queryset = models.ScalarSpecimenTag.objects.order_by("id")
        if filter is not None:
            queryset = filters.ScalarSpecimenTagFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ScalarSpecimenTagOrder.apply_sync(order_by, queryset, info)
        return queryset

    all_scalar_specimen_tags: QuerySet[models.ScalarSpecimenTag] = strawberry.field(
        resolver=_all_scalar_specimen_tags,
        graphql_type=list[ScalarSpecimenTagType],
    )

    def _scalar_specimen_by_signed_big(self, signed_big: BigInt) -> models.ScalarSpecimen | None:
        """Lookup-by-``BigInt`` query field exercising input-position parsing.

        Returns the ``ScalarSpecimen`` whose ``signed_big`` column matches
        the requested value, or ``None`` if no row matches. The
        ``BigInt!`` argument exercises ``BigInt.parse_value`` end-to-end
        for both wire forms: decimal-string literals
        (``signedBig: "9223372036854775000"``) and JSON-int literals
        (``signedBig: 42``).
        """
        return models.ScalarSpecimen.objects.filter(signed_big=signed_big).first()

    scalar_specimen_by_signed_big: models.ScalarSpecimen | None = strawberry.field(
        resolver=_scalar_specimen_by_signed_big,
        graphql_type=ScalarSpecimenType | None,
    )


class CreateMediaSpecimen(DjangoMutation):
    """Create mutation over ``MediaSpecimen`` - the write side of the spec-037 surface.

    The generated ``MediaSpecimenInput`` maps the ``attachment`` / ``image``
    file columns to Strawberry's ``Upload`` scalar (the input-side half of
    spec-037), so a live multipart ``/graphql/`` request can create a row with
    real uploaded files. Uses the default ``[DjangoModelPermission]`` write
    authorization, so the caller needs the ``scalars.add_mediaspecimen`` perm.
    """

    class Meta:
        model = models.MediaSpecimen
        operation = "create"


class UpdateMediaSpecimen(DjangoMutation):
    """Update mutation over ``MediaSpecimen`` - the partial-update side of the ``Upload`` surface.

    The generated ``MediaSpecimenPartialInput`` makes every column omittable, so an
    update that leaves ``attachment`` out keeps the stored file, one that sends a
    new upload replaces it through the generic update loop, and an explicit
    ``null`` on the required ``attachment`` column is a field error rather than a
    silent clear. ``MediaSpecimenType`` is not a Relay node, so ``id:`` is the raw
    pk string and an uncoercible one is the not-found ``FieldError`` on ``id``.
    Same default ``[DjangoModelPermission]`` write authorization as the create
    twin (``scalars.change_mediaspecimen``).
    """

    class Meta:
        model = models.MediaSpecimen
        operation = "update"


class CreateMediaSpecimenImageViaForm(DjangoModelFormMutation):
    """Create a ``MediaSpecimen`` via ``MediaSpecimenImageForm`` - the FORM ``ImageField`` path.

    The spec-038 form-mutation twin of ``createMediaSpecimen`` (the spec-037 model path),
    for the named ``ImageField -> Upload`` gap: the form's ``image`` ``ImageField`` maps to
    the ``Upload`` scalar, the resolver routes the upload into the bound form's ``files=``,
    and the bound ``ImageField`` validates it as a real image (Pillow). The live test
    asserts the stored image's dimensions, which the products ``FileField`` form test
    skips. ``permission_classes = []`` keeps write-auth out of the path under test.
    """

    class Meta:
        form_class = forms.MediaSpecimenImageForm
        operation = "create"
        permission_classes = []


class CreateScalarSpecimen(DjangoMutation):
    """Create a ``ScalarSpecimen`` through the model flavor: the temporal write surface.

    ``occurredAt`` (``DateTime``) and ``occurredTime`` (``Time``) are written as parsed,
    a naive datetime made aware under ``USE_TZ``; a value the database cannot store (an
    aware datetime whose projection onto the connection's time zone leaves years
    1..9999, an aware time on SQLite) is the field's ``invalid`` error with nothing
    written. ``permission_classes = []`` keeps write-auth out of the path under test.
    """

    class Meta:
        model = models.ScalarSpecimen
        operation = "create"
        permission_classes = []


class UpdateScalarSpecimen(DjangoMutation):
    """Update a ``ScalarSpecimen`` through the model flavor, located by its raw pk ``id:``."""

    class Meta:
        model = models.ScalarSpecimen
        operation = "update"
        permission_classes = []


class CreateScalarSpecimenViaForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through ``ScalarSpecimenTemporalForm`` (the form flavor)."""

    class Meta:
        form_class = forms.ScalarSpecimenTemporalForm
        operation = "create"
        permission_classes = []


class UpdateScalarSpecimenViaForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through ``ScalarSpecimenTemporalForm`` (the form flavor)."""

    class Meta:
        form_class = forms.ScalarSpecimenTemporalForm
        operation = "update"
        permission_classes = []


class UpdateScalarSpecimenViaLockedStampForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through ``ScalarSpecimenLockedStampForm`` (stamp disabled)."""

    class Meta:
        form_class = forms.ScalarSpecimenLockedStampForm
        operation = "update"
        permission_classes = []


class CreateScalarSpecimenViaDayInstantForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through ``ScalarSpecimenDayInstantForm``."""

    class Meta:
        form_class = forms.ScalarSpecimenDayInstantForm
        operation = "create"
        permission_classes = []


class UpdateScalarSpecimenViaDayInstantForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through ``ScalarSpecimenDayInstantForm``."""

    class Meta:
        form_class = forms.ScalarSpecimenDayInstantForm
        operation = "update"
        permission_classes = []


class CreateScalarSpecimenViaSplitForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through ``ScalarSpecimenSplitStampForm`` (a split ``occurredAt``)."""

    class Meta:
        form_class = forms.ScalarSpecimenSplitStampForm
        operation = "create"
        permission_classes = []


class UpdateScalarSpecimenViaSplitForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through ``ScalarSpecimenSplitStampForm`` (a split ``occurredAt``)."""

    class Meta:
        form_class = forms.ScalarSpecimenSplitStampForm
        operation = "update"
        permission_classes = []


class CreateScalarSpecimenViaPrefixedSplitForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through ``PrefixedScalarSpecimenSplitStampForm`` (prefix ``specimen``)."""

    class Meta:
        form_class = forms.PrefixedScalarSpecimenSplitStampForm
        operation = "create"
        permission_classes = []


class UpdateScalarSpecimenViaPrefixedSplitForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through ``PrefixedScalarSpecimenSplitStampForm`` (prefix ``specimen``)."""

    class Meta:
        form_class = forms.PrefixedScalarSpecimenSplitStampForm
        operation = "update"
        permission_classes = []


def _keyed_under_specimen_prefix(values: dict[str, object]) -> dict[str, object]:
    """Key ``values`` as the form prefix ``specimen`` reads a one-key field: ``specimen-<name>``."""
    return {f"specimen-{name}": value for name, value in values.items()}


class CreateScalarSpecimenViaRekeyedSplitForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through the prefixed split form, bound by a re-keying ``get_form``.

    The hook keys every value ``specimen-<name>``, the whole ``occurredAt`` datetime
    included; the package keeps that mapping as bound and adds the date and time keys the
    split widget reads beside it.
    """

    class Meta:
        form_class = forms.PrefixedScalarSpecimenSplitStampForm
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
    ) -> ModelForm[models.ScalarSpecimen]:
        """Bind the data keyed ``specimen-<name>``."""
        return super().get_form(
            info,
            data=_keyed_under_specimen_prefix(data),
            files=files,
            instance=instance,
        )


class UpdateScalarSpecimenViaRekeyedSplitForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through the prefixed split form, bound by a re-keying ``get_form``."""

    class Meta:
        form_class = forms.PrefixedScalarSpecimenSplitStampForm
        operation = "update"
        permission_classes = []

    @override
    def get_form(
        self,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: Model | None = None,
    ) -> ModelForm[models.ScalarSpecimen]:
        """Bind the data keyed ``specimen-<name>``."""
        return super().get_form(
            info,
            data=_keyed_under_specimen_prefix(data),
            files=files,
            instance=instance,
        )


class CreateScalarSpecimenViaPostedForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through ``ScalarSpecimenTemporalForm`` bound to posted text."""

    class Meta:
        form_class = forms.ScalarSpecimenTemporalForm
        operation = "create"
        permission_classes = []

    @override
    def get_form_kwargs(
        self,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: Model | None = None,
    ) -> dict[str, object]:
        """Bind the data as the text an HTML form post carries (``forms.as_posted_text``)."""
        kwargs = super().get_form_kwargs(info, data=data, files=files, instance=instance)
        kwargs["data"] = forms.as_posted_text(data)
        return kwargs


class UpdateScalarSpecimenViaPostedForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through ``ScalarSpecimenTemporalForm`` bound to posted text."""

    class Meta:
        form_class = forms.ScalarSpecimenTemporalForm
        operation = "update"
        permission_classes = []

    @override
    def get_form_kwargs(
        self,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: Model | None = None,
    ) -> dict[str, object]:
        """Bind the data as the text an HTML form post carries (``forms.as_posted_text``)."""
        kwargs = super().get_form_kwargs(info, data=data, files=files, instance=instance)
        kwargs["data"] = forms.as_posted_text(data)
        return kwargs


class CreateScalarSpecimenViaPostedSplitForm(DjangoModelFormMutation):
    """Create a ``ScalarSpecimen`` through the split-stamp form bound to posted text."""

    class Meta:
        form_class = forms.ScalarSpecimenSplitStampForm
        operation = "create"
        permission_classes = []

    @override
    def get_form_kwargs(
        self,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: Model | None = None,
    ) -> dict[str, object]:
        """Bind the data as the text an HTML form post carries (``forms.as_posted_text``)."""
        kwargs = super().get_form_kwargs(info, data=data, files=files, instance=instance)
        kwargs["data"] = forms.as_posted_text(data)
        return kwargs


class UpdateScalarSpecimenViaPostedSplitForm(DjangoModelFormMutation):
    """Update a ``ScalarSpecimen`` through the split-stamp form bound to posted text."""

    class Meta:
        form_class = forms.ScalarSpecimenSplitStampForm
        operation = "update"
        permission_classes = []

    @override
    def get_form_kwargs(
        self,
        info: strawberry.Info[object, object],
        *,
        data: dict[str, object],
        files: dict[str, object],
        instance: Model | None = None,
    ) -> dict[str, object]:
        """Bind the data as the text an HTML form post carries (``forms.as_posted_text``)."""
        kwargs = super().get_form_kwargs(info, data=data, files=files, instance=instance)
        kwargs["data"] = forms.as_posted_text(data)
        return kwargs


class CreateNullableScalarSpecimenViaForm(DjangoModelFormMutation):
    """Create a ``NullableScalarSpecimen`` through ``forms.NullableScalarSpecimenFlagForm``."""

    class Meta:
        form_class = forms.NullableScalarSpecimenFlagForm
        operation = "create"
        permission_classes = []


class UpdateNullableScalarSpecimenViaForm(DjangoModelFormMutation):
    """Update a ``NullableScalarSpecimen`` through ``forms.NullableScalarSpecimenFlagForm``."""

    class Meta:
        form_class = forms.NullableScalarSpecimenFlagForm
        operation = "update"
        permission_classes = []


class CreateNullableScalarSpecimenViaJsonTextForm(DjangoModelFormMutation):
    """Create a ``NullableScalarSpecimen`` through ``forms.NullableScalarSpecimenJsonTextForm``."""

    class Meta:
        form_class = forms.NullableScalarSpecimenJsonTextForm
        operation = "create"
        permission_classes = []


class UpdateNullableScalarSpecimenViaJsonTextForm(DjangoModelFormMutation):
    """Update a ``NullableScalarSpecimen`` through ``forms.NullableScalarSpecimenJsonTextForm``."""

    class Meta:
        form_class = forms.NullableScalarSpecimenJsonTextForm
        operation = "update"
        permission_classes = []


class CreateScalarSpecimenViaSerializer(SerializerMutation):
    """Create a ``ScalarSpecimen`` through ``ScalarSpecimenTemporalSerializer``."""

    class Meta:
        serializer_class = serializers.ScalarSpecimenTemporalSerializer
        operation = "create"
        permission_classes = []


class UpdateScalarSpecimenViaSerializer(SerializerMutation):
    """Update a ``ScalarSpecimen`` through ``ScalarSpecimenTemporalSerializer``."""

    class Meta:
        serializer_class = serializers.ScalarSpecimenTemporalSerializer
        operation = "update"
        permission_classes = []


class CreateUniqueScalarSpecimenViaForm(DjangoModelFormMutation):
    """Create a ``UniqueScalarSpecimen`` through ``UniqueScalarSpecimenForm``."""

    class Meta:
        form_class = forms.UniqueScalarSpecimenForm
        operation = "create"
        permission_classes = []


class UpdateUniqueScalarSpecimenViaForm(DjangoModelFormMutation):
    """Update a ``UniqueScalarSpecimen`` through ``UniqueScalarSpecimenForm``."""

    class Meta:
        form_class = forms.UniqueScalarSpecimenForm
        operation = "update"
        permission_classes = []


class CreateUniqueScalarSpecimenViaSerializer(SerializerMutation):
    """Create a ``UniqueScalarSpecimen`` through ``UniqueScalarSpecimenSerializer``."""

    class Meta:
        serializer_class = serializers.UniqueScalarSpecimenSerializer
        operation = "create"
        permission_classes = []


class UpdateUniqueScalarSpecimenViaSerializer(SerializerMutation):
    """Update a ``UniqueScalarSpecimen`` through ``UniqueScalarSpecimenSerializer``."""

    class Meta:
        serializer_class = serializers.UniqueScalarSpecimenSerializer
        operation = "update"
        permission_classes = []


class CreateScalarSpecimenTagWithUniqueSpecimens(SerializerMutation):
    """Create a ``ScalarSpecimenTag`` and a bundle of ``UniqueScalarSpecimen`` rows.

    ``serializers.TagWithUniqueSpecimensSerializer`` declares the nested writable
    ``specimens`` list and writes it in its own ``create()``.
    """

    class Meta:
        serializer_class = serializers.TagWithUniqueSpecimensSerializer
        operation = "create"
        nested_fields = {"specimens": NestedSerializerConfig()}
        permission_classes = []


class CreateScalarSpecimenTagWithReadOnlyLabelSpecimens(SerializerMutation):
    """Write nested specimens whose uniqueness partner is a read-only default."""

    class Meta:
        serializer_class = serializers.TagWithReadOnlyLabelSpecimensSerializer
        operation = "create"
        nested_fields = {"specimens": NestedSerializerConfig()}
        permission_classes = []


class CreateUniqueScalarSpecimenViaUnboundedAmountSerializer(SerializerMutation):
    """Create a ``UniqueScalarSpecimen`` through the digitless-``amount`` serializer."""

    class Meta:
        serializer_class = serializers.UniqueScalarSpecimenUnboundedAmountSerializer
        operation = "create"
        permission_classes = []


@strawberry.type
class Mutation:
    """Scalars coverage write surface: the live ``Upload`` path (spec-037) and temporal writes.

    The ``ScalarSpecimen`` create / update pairs write the temporal columns through each
    flavor (model, ``ModelForm``, serializer), and ``LockedStampForm`` updates through a form
    disabling them; the ``SplitForm`` pairs write
    ``occurredAt`` through a ``SplitDateTimeField``; the ``ViaPosted`` pairs bind posted
    text over the temporal and the split form; the ``NullableScalarSpecimen``
    ``ViaForm`` pair writes the ``null=True`` ``flag`` through a checkbox and ``payload``
    and ``score`` through a ``CharField``, and the ``ViaJsonTextForm`` pair writes ``payload``
    as JSON text; the ``UniqueScalarSpecimen`` pairs write columns under uniqueness rules
    through a ``ModelForm`` and a serializer.
    """

    create_media_specimen = DjangoMutationField(CreateMediaSpecimen)
    update_media_specimen = DjangoMutationField(UpdateMediaSpecimen)
    create_media_specimen_image_via_form = DjangoMutationField(CreateMediaSpecimenImageViaForm)
    create_scalar_specimen = DjangoMutationField(CreateScalarSpecimen)
    update_scalar_specimen = DjangoMutationField(UpdateScalarSpecimen)
    create_scalar_specimen_via_form = DjangoMutationField(CreateScalarSpecimenViaForm)
    update_scalar_specimen_via_form = DjangoMutationField(UpdateScalarSpecimenViaForm)
    update_scalar_specimen_via_locked_stamp_form = DjangoMutationField(
        UpdateScalarSpecimenViaLockedStampForm,
    )
    create_scalar_specimen_via_day_instant_form = DjangoMutationField(
        CreateScalarSpecimenViaDayInstantForm,
    )
    update_scalar_specimen_via_day_instant_form = DjangoMutationField(
        UpdateScalarSpecimenViaDayInstantForm,
    )
    create_scalar_specimen_via_split_form = DjangoMutationField(CreateScalarSpecimenViaSplitForm)
    update_scalar_specimen_via_split_form = DjangoMutationField(UpdateScalarSpecimenViaSplitForm)
    create_scalar_specimen_via_prefixed_split_form = DjangoMutationField(
        CreateScalarSpecimenViaPrefixedSplitForm,
    )
    update_scalar_specimen_via_prefixed_split_form = DjangoMutationField(
        UpdateScalarSpecimenViaPrefixedSplitForm,
    )
    create_scalar_specimen_via_rekeyed_split_form = DjangoMutationField(
        CreateScalarSpecimenViaRekeyedSplitForm,
    )
    update_scalar_specimen_via_rekeyed_split_form = DjangoMutationField(
        UpdateScalarSpecimenViaRekeyedSplitForm,
    )
    create_scalar_specimen_via_posted_form = DjangoMutationField(
        CreateScalarSpecimenViaPostedForm,
    )
    update_scalar_specimen_via_posted_form = DjangoMutationField(
        UpdateScalarSpecimenViaPostedForm,
    )
    create_scalar_specimen_via_posted_split_form = DjangoMutationField(
        CreateScalarSpecimenViaPostedSplitForm,
    )
    update_scalar_specimen_via_posted_split_form = DjangoMutationField(
        UpdateScalarSpecimenViaPostedSplitForm,
    )
    create_nullable_scalar_specimen_via_form = DjangoMutationField(
        CreateNullableScalarSpecimenViaForm,
    )
    update_nullable_scalar_specimen_via_form = DjangoMutationField(
        UpdateNullableScalarSpecimenViaForm,
    )
    create_nullable_scalar_specimen_via_json_text_form = DjangoMutationField(
        CreateNullableScalarSpecimenViaJsonTextForm,
    )
    update_nullable_scalar_specimen_via_json_text_form = DjangoMutationField(
        UpdateNullableScalarSpecimenViaJsonTextForm,
    )
    create_scalar_specimen_via_serializer = DjangoMutationField(CreateScalarSpecimenViaSerializer)
    update_scalar_specimen_via_serializer = DjangoMutationField(UpdateScalarSpecimenViaSerializer)
    create_unique_scalar_specimen_via_form = DjangoMutationField(
        CreateUniqueScalarSpecimenViaForm,
    )
    update_unique_scalar_specimen_via_form = DjangoMutationField(
        UpdateUniqueScalarSpecimenViaForm,
    )
    create_unique_scalar_specimen_via_serializer = DjangoMutationField(
        CreateUniqueScalarSpecimenViaSerializer,
    )
    update_unique_scalar_specimen_via_serializer = DjangoMutationField(
        UpdateUniqueScalarSpecimenViaSerializer,
    )
    create_scalar_specimen_tag_with_unique_specimens = DjangoMutationField(
        CreateScalarSpecimenTagWithUniqueSpecimens,
    )
    create_scalar_specimen_tag_with_read_only_label_specimens = DjangoMutationField(
        CreateScalarSpecimenTagWithReadOnlyLabelSpecimens,
    )
    create_unique_scalar_specimen_via_unbounded_amount_serializer = DjangoMutationField(
        CreateUniqueScalarSpecimenViaUnboundedAmountSerializer,
    )


__all__ = ("Mutation", "Query")
