"""Live relation leaves answer over each relation kind's visible target rows.

Ordinary JSON arguments feed the public FilterSet applicator without binding the
unbound filter sets to an output type. Django's own query after hidden
rows are deleted inside a rolled-back savepoint supplies each expected result.
The unfiltered sibling retains every root, including hidden-only and
empty relations; visible positive and excluding controls keep the predicate live.
"""

from collections.abc import Mapping
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.glossary import models as glossary_models
from apps.library import models
from django.contrib.contenttypes.models import ContentType
from django.db import models as django_models
from django.db import transaction
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload
from strawberry.scalars import JSON

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-relation-worlds/", _graphql_view)]


class _World(NamedTuple):
    """One relation's model, public filter set, visibility and lookup names."""

    parent: type[FilterSet]
    model: type[django_models.Model]
    target: type[DjangoType]
    hidden: tuple[django_models.QuerySet[django_models.Model], ...]
    relation: str
    terminal: str
    hidden_value: str
    visible_value: str
    label: str
    roots: django_models.QuerySet[django_models.Model] | None = None
    extra_targets: tuple[type[DjangoType], ...] = ()
    secondary_output: bool = False


def _hidden_type(model: type[django_models.Model], **lookups: object) -> type[DjangoType]:
    def visible(
        _cls: type[DjangoType],
        queryset: django_models.QuerySet[django_models.Model],
        _info: object,
        **_kwargs: object,
    ) -> django_models.QuerySet[django_models.Model]:
        return queryset.exclude(**lookups)

    return type(
        model.__name__ + "VisibleTarget",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": model, "fields": ("id",), "primary": True}),
            "get_queryset": classmethod(visible),
        },
    )


def _book(title: str, *, hidden: bool = False, shelf: models.Shelf | None = None) -> models.Book:
    if shelf is None:
        branch = models.Branch.objects.create(
            name="branch-" + title + ("-hidden" if hidden else ""),
        )
        shelf = models.Shelf.objects.create(branch=branch, code="shelf-" + title)
    return models.Book.objects.create(
        title=title,
        shelf=shelf,
        circulation_status="repair" if hidden else "available",
    )


def _world(kind: str, *, declared: bool) -> _World:
    """Seed distinct matching, hidden-only and empty roots for the relation's real tables."""
    if kind in {"forward-m2m", "hidden-reverse-m2m"}:
        relation = "genres" if kind == "forward-m2m" else "archive_genres"
        target_model = models.Genre
        hidden = models.Genre.objects.filter(name__startswith="secret")
        target = _hidden_type(target_model, name__startswith="secret")
        open_genre = models.Genre.objects.create(name="open")
        secret = models.Genre.objects.create(name="secret")
        for title, members in (("both", [open_genre, secret]), ("secret", [secret]), ("none", [])):
            book = _book(title)
            manager = book.genres if kind == "forward-m2m" else book.archive_genres
            manager.set(members)
        parent_model, terminal, hidden_value, visible_value = models.Book, "name", "secret", "open"
        label = "title"
    elif kind == "reverse-fk":
        relation = "books"
        target_model = models.Book
        hidden = models.Book.objects.filter(circulation_status="repair")
        target = _hidden_type(target_model, circulation_status="repair")
        for code, members in (("mixed", [False, True]), ("hidden", [True]), ("empty", [])):
            branch = models.Branch.objects.create(name=code)
            shelf = models.Shelf.objects.create(branch=branch, code=code)
            for index, is_hidden in enumerate(members):
                _book(f"{code}-x{index}", shelf=shelf, hidden=is_hidden)
        # Distinct titles make the exact visible control independent of the hidden title.
        parent_model, terminal = models.Shelf, "title"
        hidden_value, visible_value, label = "mixed-x1", "mixed-x0", "code"
    elif kind == "reverse-o2o":
        relation = "card"
        target_model = models.MembershipCard
        hidden = models.MembershipCard.objects.filter(barcode__startswith="secret")
        target = _hidden_type(target_model, barcode__startswith="secret")
        for name in ("open", "secret", "none"):
            patron = models.Patron.objects.create(name=name, email=f"{name}@example.test")
            if name != "none":
                models.MembershipCard.objects.create(patron=patron, barcode=name)
        parent_model, terminal, hidden_value, visible_value = (
            models.Patron,
            "barcode",
            "secret",
            "open",
        )
        label = "name"
    elif kind in {"generic-relation", "proxy-generic-relation"}:
        relation = "tags" if kind == "generic-relation" else "proxy_tags"
        parent_model = models.Branch if kind == "generic-relation" else models.ProxyBranch
        target_model = models.TaggedItem
        hidden = models.TaggedItem.objects.filter(tag__startswith="secret")
        target = _hidden_type(target_model, tag__startswith="secret")
        content_type = ContentType.objects.get_for_model(parent_model, for_concrete_model=False)
        other_type = ContentType.objects.get_for_model(models.Shelf)
        opposite_type = ContentType.objects.get_for_model(
            models.ProxyBranch if kind == "generic-relation" else models.Branch,
            for_concrete_model=False,
        )
        for name, tags in (("both", ["open", "secret"]), ("secret", ["secret"]), ("none", [])):
            branch = models.Branch.objects.create(name=name)
            for tag in tags:
                models.TaggedItem.objects.create(
                    tag=tag,
                    content_type=content_type,
                    object_id=saved_pk(branch),
                )
            # Same key on another table and the concrete/proxy sibling must not satisfy this hop.
            for decoy_type in (other_type, opposite_type):
                models.TaggedItem.objects.create(
                    tag="open",
                    content_type=decoy_type,
                    object_id=saved_pk(branch),
                )
        terminal, hidden_value, visible_value, label = "tag", "secret", "open", "name"
    else:
        assert kind == "nullable-fk-hidden-reverse-mti-outer"
        relation = "lead_ticket"
        target_model = models.RepairTicket
        hidden = models.RepairTicket.objects.filter(code__startswith="secret")
        target = _hidden_type(target_model, code__startswith="secret")
        for name in ("open", "secret", "none"):
            desk = models.LendingDesk.objects.create(name=name)
            if name != "none":
                desk.lead_ticket = models.RepairTicket.objects.create(code=name, venue=desk)
                desk.save()
        parent_model, terminal, hidden_value, visible_value = (
            models.LendingDesk,
            "code",
            "secret",
            "open",
        )
        label = "name"
    child = type(
        "Child",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": target_model, "fields": {terminal: ["exact"]}})},
    )
    target_path = f"{relation}__{terminal}"
    branch = {"visible": RelatedFilter(child, field_name=relation)} if declared else {}
    parent = type(
        "Parent",
        (FilterSet,),
        {
            **branch,
            "excluding": CharFilter(field_name=target_path, exclude=True),
            "key_isnull": BooleanFilter(field_name=relation, lookup_expr="isnull"),
            "Meta": type("Meta", (), {"model": parent_model, "fields": {target_path: ["exact"]}}),
        },
    )
    return _World(
        parent,
        parent_model,
        target,
        (hidden,),
        relation,
        terminal,
        hidden_value,
        visible_value,
        label,
    )


def _labels(rows: django_models.QuerySet[django_models.Model], label: str) -> list[JSONObject]:
    return [{"label": read_attr(row, label)} for row in rows.order_by("pk")]


def _base(world: _World) -> django_models.QuerySet[django_models.Model]:
    return world.roots if world.roots is not None else world.model.objects.all()


def _absent_answer(world: _World, lookups: JSONObject, *, exclude: bool) -> list[JSONObject]:
    """Ask Django after deleting hidden targets, then restore the entire real world."""
    with transaction.atomic():
        for hidden in world.hidden:
            hidden.delete()
        method = _base(world).exclude if exclude else _base(world).filter
        # The result contract compares root identity sets; Django joins can repeat a root.
        answer = _labels(method(**lookups).distinct(), world.label)
        transaction.set_rollback(True)
    return answer


def _schema(world: _World) -> DjangoSchema:
    output = type(
        "RootOutput",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": world.model,
                    "fields": (world.label,),
                    "primary": not world.secondary_output,
                },
            ),
        },
    )

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> django_models.QuerySet[django_models.Model]:
            return world.parent.apply_sync(where, _base(world).order_by("pk"), info)

        def _all_rows(self) -> django_models.QuerySet[django_models.Model]:
            return _base(world).order_by("pk")

        rows: django_models.QuerySet[django_models.Model] = strawberry.field(
            resolver=_rows,
            graphql_type=list[output],
        )
        all_rows: django_models.QuerySet[django_models.Model] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[output],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[world.target, *world.extra_targets],
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _post(schema: DjangoSchema, where: JSONObject, label: str) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                f"query($where: JSON!) {{ rows(where: $where) {{ label: {label} }} "
                f"allRows {{ label: {label} }} }}",
                variables={"where": where},
                url="/graphql-relation-worlds/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize(
    "kind",
    [
        "forward-m2m",
        "hidden-reverse-m2m",
        "reverse-fk",
        "reverse-o2o",
        "generic-relation",
        "proxy-generic-relation",
        "nullable-fk-hidden-reverse-mti-outer",
    ],
)
@pytest.mark.parametrize(
    "verdict",
    [
        "hidden-positive",
        "hidden-exclude",
        "key-isnull-true",
        "key-isnull-false",
        "visible-positive",
        "visible-exclude",
    ],
)
def test_relation_kind_filters_match_django_with_hidden_targets_absent(
    kind: str,
    verdict: str,
    *,
    declared: bool,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Each leaf uses visible target identity without hiding its parent roots."""
    world = _world(kind, declared=declared)
    path = f"{world.relation}__{world.terminal}"
    value = world.visible_value if verdict.startswith("visible-") else world.hidden_value
    exclude = verdict.endswith("exclude")
    if verdict.startswith("key-isnull-"):
        null = verdict == "key-isnull-true"
        where: JSONObject = {"key_isnull": null}
        lookups: JSONObject = {f"{world.relation}__isnull": null}
    else:
        where = {"excluding" if exclude else path: value}
        lookups = {path: value}
    universe = _labels(_base(world), world.label)
    expected = _absent_answer(world, lookups, exclude=exclude)
    schema = _schema(world)
    sql = record_compiled_sql()
    payload = _post(schema, where, world.label)
    assert payload == {"data": {"rows": expected, "allRows": universe}}, payload
    roots = [
        statement
        for statement in sql
        if statement.lstrip().upper().startswith("SELECT ")
        and " FROM " in statement
        and statement.split(" FROM ", 1)[1].startswith(f'"{world.model._meta.db_table}"')
    ]
    assert len(roots) == 2, sql
    filtered = [statement for statement in roots if "EXISTS" in statement.upper()]
    assert len(filtered) == 1, roots
    assert all("DISTINCT" not in statement.upper() for statement in roots), roots


def _self_through_world() -> _World:
    target_type = _hidden_type(glossary_models.GlossaryTerm, title__startswith="secret")
    status = glossary_models.GlossaryStatus.objects.create(key="relation-world", label="World")
    kind = glossary_models.GlossaryTermLinkKind.objects.create(key="relation-world", label="World")

    def term(title: str) -> glossary_models.GlossaryTerm:
        return glossary_models.GlossaryTerm.objects.create(
            title=title,
            title_sort=title,
            anchor="relation-world-" + title,
            status=status,
            status_text="World",
        )

    source, lonely, target, secret = term("source"), term("lonely"), term("target"), term("secret")
    for order, linked in enumerate((target, secret)):
        glossary_models.GlossaryTermLink.objects.create(
            source_term=source,
            target_term=linked,
            kind=kind,
            order=order,
        )
    glossary_models.GlossaryTermLink.objects.create(
        source_term=lonely,
        target_term=secret,
        kind=kind,
        order=0,
    )

    class TermChild(FilterSet):
        class Meta:
            model = glossary_models.GlossaryTerm
            fields = {"title": ["exact"]}

    class TermParent(FilterSet):
        linked = RelatedFilter(TermChild, field_name="related_terms")
        unlinked = BooleanFilter(field_name="related_terms", lookup_expr="isnull")

        class Meta:
            model = glossary_models.GlossaryTerm
            fields = {"related_terms__title": ["exact"]}

    return _World(
        TermParent,
        glossary_models.GlossaryTerm,
        target_type,
        (glossary_models.GlossaryTerm.objects.filter(title__startswith="secret"),),
        "related_terms",
        "title",
        "secret",
        "target",
        "title",
        roots=glossary_models.GlossaryTerm.objects.filter(pk__in=[source.pk, lonely.pk]),
        secondary_output=True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("verdict", ["hidden-target", "visible-target", "no-visible-link"])
def test_self_referential_explicit_through_filter_reads_only_its_visible_targets(
    verdict: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A source with only a hidden link is unlinked; a visible target retains its source once."""
    world = _self_through_world()
    if verdict == "no-visible-link":
        where: JSONObject = {"unlinked": True}
        lookups: JSONObject = {"related_terms__isnull": True}
    else:
        value = "secret" if verdict == "hidden-target" else "target"
        where = {"related_terms__title": value}
        lookups = dict(where)
    universe = _labels(_base(world), world.label)
    expected = _absent_answer(world, lookups, exclude=False)
    sql = record_compiled_sql()
    payload = _post(_schema(world), where, world.label)
    assert payload == {"data": {"rows": expected, "allRows": universe}}, payload
    roots = [statement for statement in sql if 'FROM "glossary_glossaryterm"' in statement]
    assert len(roots) == 2, sql
    filtered = [statement for statement in roots if "EXISTS" in statement.upper()]
    assert len(filtered) == 1, roots
    assert '"glossary_glossarytermlink"' in filtered[0], filtered


def _projected_world(*, customize_child: bool) -> _World:
    visible_book_type = _hidden_type(models.Book, circulation_status="repair")
    visible_genre_type = _hidden_type(models.Genre, name__startswith="secret")

    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    attrs: dict[str, object] = {
        "books": RelatedFilter(BookChild, field_name="books"),
        "without_book_titled": CharFilter(field_name="books__title", exclude=True),
        "subtitle_missing": BooleanFilter(field_name="books__subtitle", lookup_expr="isnull"),
        "Meta": type("Meta", (), {"model": models.Genre, "fields": {"name": ["exact"]}}),
    }
    if customize_child:

        def forwarding_init(
            self: FilterSet,
            data: Mapping[str, object] | None = None,
            queryset: django_models.QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            FilterSet.__init__(self, data=data, queryset=queryset, request=request, prefix=prefix)

        attrs["__init__"] = forwarding_init
    genre_child = type("GenreChild", (FilterSet,), attrs)

    class BookParent(FilterSet):
        genres = RelatedFilter(genre_child, field_name="genres")

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    x_open = _book("x")
    x_hidden = _book("x", hidden=True)
    no_subtitle = _book("plain")
    with_x = models.Genre.objects.create(name="with_x")
    with_x.books.set([x_open])
    only_hidden_x = models.Genre.objects.create(name="only_hidden_x")
    only_hidden_x.books.set([x_hidden, no_subtitle])
    secret = models.Genre.objects.create(name="secret")
    secret.books.set([x_open])
    for title, genres in (
        ("in_with_x", [with_x]),
        ("in_only_hidden_x", [only_hidden_x]),
        ("in_both", [with_x, only_hidden_x]),
        ("in_secret", [secret]),
        ("in_none", []),
    ):
        book = _book(title)
        book.subtitle = "s"
        book.save()
        book.genres.set(genres)
    return _World(
        BookParent,
        models.Book,
        visible_genre_type,
        (
            models.Book.objects.filter(circulation_status="repair"),
            models.Genre.objects.filter(name__startswith="secret"),
        ),
        "genres",
        "books__title",
        "x",
        "x",
        "title",
        roots=models.Book.objects.exclude(circulation_status="repair"),
        extra_targets=(visible_book_type,),
        secondary_output=True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("customize_child", [True, False], ids=["projected", "expanded"])
@pytest.mark.parametrize("verdict", ["exclude", "isnull-true", "isnull-false"])
def test_projected_child_negation_and_null_extension_answer_at_the_outer_parent(
    verdict: str,
    *,
    customize_child: bool,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A copied child exclusion negates at the Book root instead of selecting a different Genre."""
    world = _projected_world(customize_child=customize_child)
    exclude = verdict == "exclude"
    if exclude:
        where: JSONObject = {"genres__without_book_titled": "x"}
        lookups: JSONObject = {"genres__books__title": "x"}
    else:
        null = verdict == "isnull-true"
        where = {"genres__subtitle_missing": null}
        lookups = {"genres__books__subtitle__isnull": null}
    universe = _labels(_base(world), world.label)
    assert len(universe) == 7, universe
    expected = _absent_answer(world, lookups, exclude=exclude)
    sql = record_compiled_sql()
    payload = _post(_schema(world), where, world.label)
    assert payload == {"data": {"rows": expected, "allRows": universe}}, payload
    roots = [
        statement
        for statement in sql
        if statement.lstrip().startswith("SELECT ")
        and " FROM " in statement
        and statement.split(" FROM ", 1)[1].startswith('"library_book"')
    ]
    assert len(roots) == 2, sql
    filtered = [statement for statement in roots if "EXISTS" in statement.upper()]
    assert len(filtered) == 1, roots
    assert '"library_genre"' in filtered[0], filtered
