"""Consumer graph builders shared by connection wire tests and private window-state tests."""

import strawberry
from apps.library.models import Book, Branch, Genre, Loan, Shelf
from django.db import models as djmodels
from django.db.models.functions import Lower
from strategy_schemas import make_django_type
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.registry import registry
from tests._idioms import declare_django_type

_make_type = make_django_type


def _schema_with_root(
    declaring_type: type[DjangoType],
    *,
    field_name: str = "objs",
) -> strawberry.Schema:
    """Finalize and build a schema exposing ``field_name: [declaring_type!]!``.

    The root field lists every row of the declaring type's model in pk order
    so nested relation-connection queries have a deterministic parent set.
    """
    finalize_django_types()
    model = declaring_type.__django_strawberry_definition__.model

    def _resolver() -> list[djmodels.Model]:
        return list(model._default_manager.all().order_by("pk"))

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {field_name: list[declaring_type]},
                field_name: strawberry.field(resolver=_resolver),
            },
        ),
    )
    return DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
    )


def _seed_library_books(
    titles: list[str],
    *,
    genre_name: str = "fiction",
) -> tuple[Genre, list[Book]]:
    """Create one genre linked to one book per title (library inline-create rule)."""
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    genre = Genre.objects.create(name=genre_name)
    books: list[Book] = []
    for title in titles:
        book = Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)
        books.append(book)
    return genre, books


def _ordered_genres(
    _root: object,
    _info: strawberry.Info[object, object],
) -> djmodels.QuerySet[Genre]:
    """Order the consumer root explicitly so plan strategy cannot choose parent order."""
    return Genre.objects.order_by("pk")


def _genres_list_schema(
    *,
    optimizer: bool = False,
    book_total_count: bool = False,
    strictness: str = "off",
) -> strawberry.Schema:
    """Build a ``DjangoListField(GenreType)`` root over the M2M ``Genre.books``.

    With ``optimizer`` installed the parent ``Genre`` queryset is planned, so
    the nested ``booksConnection`` window lands on each genre's
    ``_dst_books_connection`` ``to_attr`` and the fast path fires.
    ``book_total_count`` opts ``BookType`` into ``Meta.connection`` so the
    nested connection carries ``totalCount``. ``strictness`` (``"off"`` /
    ``"warn"`` / ``"raise"``) wires the B3 contract for the strictness
    pins below; it is only meaningful with ``optimizer=True`` (no extension stashes
    no sentinel - the no-op baseline).
    """
    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}} if book_total_count else None,
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": DjangoListField(genre_type, resolver=_ordered_genres),
            },
        ),
    )
    extensions = []
    if optimizer:
        optimizer_ext = DjangoOptimizerExtension(strictness=strictness)
        extensions = [lambda: optimizer_ext]
    return DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
        extensions=extensions,
    )


def _genres_filterable_book_schema(*, strictness: str = "raise") -> strawberry.Schema:
    """Build the same M2M genres list root but with ``BookType`` carrying a sidecar.

    A ``filterset_class`` on ``BookType`` means a nested
    ``booksConnection(filter: ...)`` selection is a spec-033 Decision-6 sidecar
    fallback: the walker leaves it unplanned, so the resolver runs the
    per-parent pipeline and (with strictness active) fires the B3 contract with
    the filter/orderBy fallback reason.
    """

    class _BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"filterset_class": _BookFilter},
    )
    # ``"both"``: this fixture's tests select the raw ``books`` list sibling
    # ALONGSIDE ``booksConnection``, which the ``"connection"`` default does
    # not emit together.
    genre_type = _make_type(
        "GenreType",
        Genre,
        ("id", "name", "books"),
        meta_extra={"relation_shapes": {"books": "both"}},
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": DjangoListField(genre_type, resolver=_ordered_genres),
            },
        ),
    )
    optimizer = DjangoOptimizerExtension(strictness=strictness)
    return DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _genres_distinct_book_schema(
    *,
    optimizer: bool = True,
    strictness: str = "off",
) -> strawberry.Schema:
    """M2M genres list root whose ``BookType`` target ``get_queryset`` ``.distinct()``s.

    A ``.distinct()``-ing target is a spec-033 Decision-6 DISTINCT fallback: the
    window's ``Count(1) OVER`` would over-count the pre-DISTINCT fan-out rows,
    so the walker leaves the nested ``booksConnection`` unplanned and the
    per-parent pipeline runs - which counts ``totalCount`` correctly via
    ``.distinct().count()``. ``BookType`` opts into ``Meta.connection`` so
    ``totalCount`` exists; the ``genres__isnull=False`` join is what fans rows
    out so DISTINCT is load-bearing.
    """

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: djmodels.QuerySet[Book],
            info: object,
        ) -> djmodels.QuerySet[Book]:
            return queryset.filter(genres__isnull=False).distinct()

    assert registry.get(Book) is BookType

    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": DjangoListField(genre_type, resolver=_ordered_genres),
            },
        ),
    )
    extensions = []
    if optimizer:
        optimizer_ext = DjangoOptimizerExtension(strictness=strictness)
        extensions = [lambda: optimizer_ext]
    return DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
        extensions=extensions,
    )


def _genres_expression_ordered_schema(
    *,
    optimizer: bool = True,
    auto_camel_case: bool = True,
) -> strawberry.Schema:
    """``_genres_list_schema`` whose ``BookType`` orders by a bare EXPRESSION.

    ``get_queryset`` returns ``queryset.order_by(Lower("title"))``, so the
    connection's effective ordering carries a term with no direction of its own -
    the shape a ``last: N`` window must still be able to reverse
    (``plans.py::_reverse_order_by``). ``auto_camel_case`` doubles this fixture as
    the non-default-``NameConverter`` schema for the count-observer pins.
    """

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: djmodels.QuerySet[Book],
            info: object,
        ) -> djmodels.QuerySet[Book]:
            return queryset.order_by(Lower("title"))

    assert registry.get(Book) is BookType

    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": DjangoListField(genre_type, resolver=_ordered_genres),
            },
        ),
    )
    extensions = []
    if optimizer:
        optimizer_ext = DjangoOptimizerExtension()
        extensions = [lambda: optimizer_ext]
    return DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(auto_camel_case=auto_camel_case),
        extensions=extensions,
    )


def _shelves_with_consumer_books_schema(
    *,
    strictness: str = "raise",
    books_hint: OptimizerHint | None = None,
) -> strawberry.Schema:
    """Root ``objs: [ShelfType]`` where the consumer owns ``ShelfType.books``.

    The consumer resolver sorts ``root.books.all()`` in memory, keeping its
    delegation to the native relation cache identical with and without a hint.
    Without a hint those rows are fresh and nested generated resolvers see the
    unplanned loan relation; with the hint they retain the prefetched loans.
    The nested probe is the many-side ``loans`` (a reverse
    FK): Django's related manager seeds each child's FORWARD FK cache with the
    parent
    (known-related-objects), so a ``books { shelf }`` access never lazy-loads
    - the many side has no such seeding and is the real N+1.
    ``books_hint`` opts back in via ``Meta.optimizer_hints``.
    """

    class LoanType(DjangoType):
        class Meta:
            model = Loan
            fields = ("id", "note")

    assert registry.get(Loan) is LoanType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "loans")

    def _curated_books(root: Shelf) -> list[Book]:
        return sorted(root.books.all(), key=lambda book: book.title)[:2]

    meta_ns: dict[str, object] = {"model": Shelf, "fields": ("id", "code", "books")}
    if books_hint is not None:
        meta_ns["optimizer_hints"] = {"books": books_hint}
    shelf_type = declare_django_type(
        "ShelfType",
        {
            "__annotations__": {},
            "books": strawberry.field(resolver=_curated_books, graphql_type=list[BookType]),
            "Meta": type("Meta", (), meta_ns),
        },
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[shelf_type]}, "objs": DjangoListField(shelf_type)},
        ),
    )
    optimizer = DjangoOptimizerExtension(strictness=strictness)
    return DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
