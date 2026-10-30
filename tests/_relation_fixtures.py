"""Shared TEST-ONLY relation fixture models.

These ``Rp*`` models carry two relation shapes the fakeshop example apps do not
carry as first-class models: a ``CompositePrimaryKey`` parent with a reverse
to-many, and a ``GenericRelation`` declared with a ``related_query_name``, which
makes its reverse ``GenericRel`` a visible field of the generic-key model. They
are defined here ONCE so every consumer imports the same classes (a model class
declared twice under one name is a registry warning, which the suite treats as
an error).

Each model is a plain ``django.db.models.Model`` with
``class Meta: app_label = "products"`` and ``managed = False``. The
``app_label`` MUST name an installed app so Django wires the reverse
relations into ``_meta.get_fields()``; ``managed = False`` keeps ``migrate``
and the test runner from ever creating or dropping their tables on their own.
Because nothing manages the tables, callers create and drop them on demand
with ``connection.schema_editor()`` via ``relation_fixture_tables``.

None of these classes enters a GraphQL schema: a test that declares a
``DjangoType`` over one runs under a cleared registry (and a declaration over
``RpGenericTag`` that selects ``holder`` is refused before it registers). The
``Rp`` prefix keeps the class and table names distinct from the inline test
models declared elsewhere in the suite.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, TypeAlias

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from django.db.models.expressions import Combinable
    from django.db.models.fields.related_descriptors import RelatedManager

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _Char: TypeAlias = models.CharField[str | int | Combinable, str]
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _PositiveInt: TypeAlias = models.PositiveIntegerField[float | int | str | Combinable, int]
    _Text: TypeAlias = models.TextField[str | Combinable, str]


class RpCompositeParent(models.Model):
    """A composite-primary-key parent (``tenant_id`` + ``code``).

    Django's ``CompositePrimaryKey`` (supported on the >= 5.2.16 floor this repo
    targets) names the concrete member fields; instance ``pk`` reads back as a
    tuple in declaration order (e.g. ``(1, "X")``).

    This family models a composite-primary-key parent whose reverse to-many
    needs a ``ForeignObject`` child (Django refuses a plain ``ForeignKey`` to a
    ``CompositePrimaryKey`` target, ``fields.E347``), a shape fakeshop excludes
    because Relay finalization rejects composite pks, and it alone executes
    ``django_strawberry_framework/optimizer/predicates.py::correlated_inner_root``
    against a real composite-pk table.
    """

    tenant_id: _Int = models.IntegerField()
    code: _Char = models.CharField(max_length=32)
    pk = models.CompositePrimaryKey("tenant_id", "code")
    label: _Char = models.CharField(max_length=64)
    # Reverse accessor Django adds at class creation, declared for the type checker.
    children: RelatedManager[RpCompositeChild]

    class Meta:
        app_label = "products"
        managed = False


class RpCompositeChild(models.Model):
    """A child of the composite-pk parent, giving a reverse ``children`` hop.

    Django (every version on this repo's >= 5.2.16 floor) refuses a plain
    ``ForeignKey`` whose target has a ``CompositePrimaryKey`` -- system check
    ``fields.E347``, and ``schema_editor`` never emits the join column, so the
    relation is dead at runtime. The supported way to bind on a multi-column
    key is ``ForeignObject`` with ``from_fields`` / ``to_fields``: it is a
    virtual relation over the two concrete carrier columns
    (``parent_tenant_id`` / ``parent_code``) here, and it still yields the
    forward ``parent`` accessor and the reverse ``RpCompositeParent.children``
    to-many the later composite-pk correlation-execution tests rely on.
    Assigning ``parent=<instance>`` populates both carrier columns.
    """

    parent_tenant_id: _Int = models.IntegerField()
    parent_code: _Char = models.CharField(max_length=32)
    name: _Char = models.CharField(max_length=64)
    parent: models.ForeignObject[RpCompositeParent, RpCompositeParent] = models.ForeignObject(
        RpCompositeParent,
        on_delete=models.CASCADE,
        from_fields=["parent_tenant_id", "parent_code"],
        to_fields=["tenant_id", "code"],
        related_name="children",
    )

    class Meta:
        app_label = "products"
        managed = False


class RpGenericTag(models.Model):
    """A generic-key model: a ``GenericForeignKey`` over ``content_type`` / ``object_id``.

    ``RpGenericHolder.tags`` declares ``related_query_name="holder"``, so this
    model's ``_meta.get_fields()`` carries the reverse ``GenericRel`` as
    ``holder``: a single-valued relation onto the holder whose ``object_id``
    carrier is a column of this model.
    """

    name: _Text = models.TextField()
    content_type: models.ForeignKey[ContentType | Combinable, ContentType] = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+",
    )
    object_id: _PositiveInt = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        app_label = "products"
        managed = False


class _RpUnmanagedProductsModel(models.Model):
    """The abstract base whose ``Meta`` a proxy below subclasses.

    Django keeps the ``Meta`` of an abstract model only, so a proxy of a concrete
    model spells its own ``Meta`` as a subclass of this one (Django's documented
    abstract-``Meta`` inheritance), and the checker reads that ``Meta`` as a
    compatible override.
    """

    class Meta:
        abstract = True
        app_label = "products"
        managed = False


class RpGenericHolder(_RpUnmanagedProductsModel):
    """The ``GenericRelation`` side, whose ``related_query_name`` names the reverse ``holder``."""

    # Typed here: django-stubs types ``Model.pk`` as ``Any``. ``None`` until the row is saved.
    pk: int | None

    title: _Text = models.TextField()
    tags = GenericRelation(RpGenericTag, related_query_name="holder")


class RpGenericProxyHolder(RpGenericHolder):
    """A proxy of the holder declaring its own generic relations onto the tag.

    ``proxy_tags`` keeps the default ``for_concrete_model=True``, so it reads the
    tags stored under the CONCRETE holder's content type; ``proxy_only_tags`` sets
    ``for_concrete_model=False`` and reads only tags stored under this proxy's own
    content type. Their ``related_query_name`` makes each reverse ``GenericRel``
    visible on the tag (``proxy_holder``, ``proxy_only_holder``).
    """

    proxy_tags = GenericRelation(RpGenericTag, related_query_name="proxy_holder")
    proxy_only_tags = GenericRelation(
        RpGenericTag,
        related_query_name="proxy_only_holder",
        for_concrete_model=False,
    )

    class Meta(_RpUnmanagedProductsModel.Meta):
        proxy = True


@contextlib.contextmanager
def relation_fixture_tables(
    connection: BaseDatabaseWrapper,
    models_in_order: Sequence[type[models.Model]] = (RpCompositeParent, RpCompositeChild),
) -> Generator[None, None, None]:
    """Create the given ``Rp*`` fixture tables via ``schema_editor``; drop on exit.

    The models are ``managed = False``, so their tables never exist until a
    caller materializes them. This context manager creates them in the given
    (FK dependency) order, the composite-pk pair by default, and deletes them
    in reverse on exit (including on error), leaving no residue in the test
    database.

    Callers must run under ``@pytest.mark.django_db(transaction=True)`` (the
    SQLite schema editor refuses to run inside the plain ``django_db`` atomic
    wrapper) and pass the test ``connection``
    (``from django.db import connection``).
    """
    created: list[type[models.Model]] = []
    try:
        with connection.schema_editor() as editor:
            for m in models_in_order:
                editor.create_model(m)
                created.append(m)
        yield
    finally:
        # Drop whatever was successfully created, in reverse. Tracking
        # ``created`` (rather than ``models_in_order``) means a mid-list
        # ``create_model`` failure still tears down the earlier tables, so
        # the "no residue" guarantee holds even on partial construction.
        with connection.schema_editor() as editor:
            for m in reversed(created):
                editor.delete_model(m)


@contextlib.contextmanager
def generic_fixture_rows(
    connection: BaseDatabaseWrapper,
) -> Generator[tuple[RpGenericHolder, RpGenericHolder], None, None]:
    """Materialize the generic pair's tables and yield two holders, one tag each.

    Holder ``"b"`` carries tag ``"t1"`` and holder ``"a"`` tag ``"t2"``, so an
    ascending order on the holder's ``title`` reverses the tags' insertion order.
    A third tag, ``"stray"``, stores holder ``"a"``'s pk as its ``object_id`` under
    another model's content type, so it belongs to no holder: a reading of the
    reverse ``holder`` that compares ``object_id`` without the content type
    claims it. A fourth, ``"p1"``, stores holder ``"b"`` under the proxy
    ``RpGenericProxyHolder``'s own content type, the one tag ``proxy_only_tags``
    reads (``t1`` / ``t2`` are stored under the concrete holder's). The same
    ``relation_fixture_tables`` contract applies (``transaction=True``).
    """
    with relation_fixture_tables(connection, (RpGenericHolder, RpGenericTag)):
        first = RpGenericHolder.objects.create(title="b")
        second = RpGenericHolder.objects.create(title="a")
        for name, holder in (("t1", first), ("t2", second)):
            RpGenericTag.objects.create(name=name, content_object=holder)
        assert second.pk is not None
        RpGenericTag.objects.create(
            name="stray",
            content_type=ContentType.objects.get_for_model(RpGenericTag),
            object_id=second.pk,
        )
        assert first.pk is not None
        RpGenericTag.objects.create(
            name="p1",
            content_type=ContentType.objects.get_for_model(
                RpGenericProxyHolder,
                for_concrete_model=False,
            ),
            object_id=first.pk,
        )
        yield first, second
