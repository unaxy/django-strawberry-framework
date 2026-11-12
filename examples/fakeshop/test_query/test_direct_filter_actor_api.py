"""A set built outside the GraphQL pipeline scopes its hops as the request's actor sees them.

DRF's ``DjangoFilterBackend`` builds the package's ``FilterSet`` with ``request=`` its
``Request``, and django-filter's ``FilterView`` and a consumer's own view build one with
``request=`` Django's; none runs a resolver, so no Strawberry ``Info`` exists. Every
``DjangoType.get_queryset`` such a set reaches (a walked key's hop, a relation key's target, an
intermediate model, a logical arm's branch) reads the actor off ``info.context.request`` as it
does under GraphQL, so each answer here equals the same filter's answer over ``/graphql/`` for
the same session: the anonymous viewer never matches through the secret shelf
``ShelfType.get_queryset`` hides, staff do.

A ``RelatedFilter`` head the form data names (``shelf=<pk>``, a flat copy such as
``shelves__books__shelf=<pk>``), which GraphQL cannot name, walks its path as the relation key
does and validates its key against the rows its target type lets the actor see: a hidden row's
key is refused with the body a key naming no row gets, and every hop runs its hook once, none
for a request naming no head.
"""

import json
from collections import Counter
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, ClassVar, NamedTuple

import pytest
from apps.library import models
from apps.library import schema as library_schema
from apps.library.filters import BookFilter, BranchFilter, CatalogueBookFilter, ShelfFilter
from apps.library.filters_genre import GenreFilter
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Model, QuerySet
from django.http import HttpRequest, JsonResponse, QueryDict
from django.test import Client, override_settings
from django.urls import path
from django_filters.filterset import BaseFilterSet
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterView
from graphql_client import (
    graphql_payload,
    json_list,
    json_loads,
    json_object,
    json_str,
    read_attr,
)
from rest_framework import generics
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.filters.sets import _DirectRequestContext
from django_strawberry_framework.utils._narrowing import require_instance
from tests._idioms import ModelSerializerBase

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse


class _BookTitleSerializer(ModelSerializerBase[models.Book]):
    class Meta:
        model = models.Book
        fields = ("title",)


class _BranchNameSerializer(ModelSerializerBase[models.Branch]):
    class Meta:
        model = models.Branch
        fields = ("name",)


class _BookListView(generics.ListAPIView[models.Book]):
    """A session-authenticated DRF list of books filtered through ``DjangoFilterBackend``."""

    queryset = models.Book.objects.order_by("pk")
    serializer_class = _BookTitleSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class: ClassVar[type[BaseFilterSet]] = BookFilter
    authentication_classes = (SessionAuthentication,)
    permission_classes = ()
    renderer_classes = (JSONRenderer,)
    pagination_class = None


class _CatalogueBookListView(_BookListView):
    filterset_class: ClassVar[type[BaseFilterSet]] = CatalogueBookFilter


class _BranchListView(generics.ListAPIView[models.Branch]):
    """The branch twin of ``_BookListView``."""

    queryset = models.Branch.objects.order_by("pk")
    serializer_class = _BranchNameSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class: ClassVar[type[BaseFilterSet]] = BranchFilter
    authentication_classes = (SessionAuthentication,)
    permission_classes = ()
    renderer_classes = (JSONRenderer,)
    pagination_class = None


class _ShelfCodeSerializer(ModelSerializerBase[models.Shelf]):
    class Meta:
        model = models.Shelf
        fields = ("code",)


class _GenreNameSerializer(ModelSerializerBase[models.Genre]):
    class Meta:
        model = models.Genre
        fields = ("name",)


class _ShelfListView(generics.ListAPIView[models.Shelf]):
    """The shelf twin of ``_BookListView``."""

    queryset = models.Shelf.objects.order_by("pk")
    serializer_class = _ShelfCodeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class: ClassVar[type[BaseFilterSet]] = ShelfFilter
    authentication_classes = (SessionAuthentication,)
    permission_classes = ()
    renderer_classes = (JSONRenderer,)
    pagination_class = None


class _GenreListView(generics.ListAPIView[models.Genre]):
    """The genre twin of ``_BookListView``."""

    queryset = models.Genre.objects.order_by("pk")
    serializer_class = _GenreNameSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class: ClassVar[type[BaseFilterSet]] = GenreFilter
    authentication_classes = (SessionAuthentication,)
    permission_classes = ()
    renderer_classes = (JSONRenderer,)
    pagination_class = None


class _ActorHeaderAuthentication(BaseAuthentication):
    """Authenticates the user the ``X-Actor`` header names; Django's middleware never sees it."""

    @override
    def authenticate(self, request: Request) -> tuple[AbstractBaseUser, None] | None:
        username = request.headers.get("X-Actor")
        if username is None:
            return None
        return get_user_model().objects.get(username=username), None


class _LazyActorBookListView(_BookListView):
    """Authenticates only when something reads ``request.user`` (DRF's lazy ``Request``)."""

    authentication_classes = (_ActorHeaderAuthentication,)

    @override
    def perform_authentication(self, request: Request) -> None:
        """Leave authentication to the first ``request.user`` read."""


class _ListedFilterView(FilterView):
    """django-filter's ``FilterView`` answering its filtered rows' ``column`` as JSON."""

    column = "title"

    @override
    def render_to_response(
        self,
        context: dict[str, object],
        **response_kwargs: object,
    ) -> JsonResponse:
        rows: QuerySet[Model] = self.object_list
        return JsonResponse(
            [{self.column: read_attr(row, self.column)} for row in rows],
            safe=False,
        )


class _CheckedFilterView(_ListedFilterView):
    """``_ListedFilterView`` answering a form that refuses the request with its errors, as 400."""

    @override
    def render_to_response(
        self,
        context: dict[str, object],
        **response_kwargs: object,
    ) -> JsonResponse:
        filterset = require_instance(context["filter"], BaseFilterSet)
        if not filterset.is_valid():
            return JsonResponse({"errors": filterset.form.errors.get_json_data()}, status=400)
        return super().render_to_response(context, **response_kwargs)


# Each set a head row filters: its class, the rows it filters, and the column a row answers.
_HEAD_SETS: dict[str, tuple[type[FilterSet], QuerySet[Model], str]] = {
    "books": (BookFilter, models.Book.objects.order_by("pk"), "title"),
    "shelves": (ShelfFilter, models.Shelf.objects.order_by("pk"), "code"),
    "branches": (BranchFilter, models.Branch.objects.order_by("pk"), "name"),
    "genres": (GenreFilter, models.Genre.objects.order_by("pk"), "name"),
}


def _consumer_rows(request: HttpRequest, route: str) -> JsonResponse:
    """A consumer view building a set over its query string with ``request=``."""
    filterset_class, queryset, column = _HEAD_SETS[route]
    filterset = filterset_class(request.GET, queryset=queryset, request=request)
    if not filterset.is_valid():
        return JsonResponse({"errors": filterset.form.errors.get_json_data()}, status=400)
    return JsonResponse(list(filterset.qs.values(column)), safe=False)


def _consumer_book_titles(request: HttpRequest) -> JsonResponse:
    """A consumer view building ``BookFilter`` over a JSON body, as its own code would."""
    return _consumer_answer(request, request)


def _consumer_book_titles_without_request(request: HttpRequest) -> JsonResponse:
    """The same view building its set with no ``request=``."""
    return _consumer_answer(request, None)


def _consumer_answer(request: HttpRequest, handed: HttpRequest | None) -> JsonResponse:
    filterset = BookFilter(
        data=json_object(json_loads(request.body)),
        queryset=models.Book.objects.order_by("pk"),
        request=handed,
    )
    if not filterset.is_valid():
        return JsonResponse({"errors": filterset.errors}, status=400)
    return JsonResponse({"titles": sorted(filterset.qs.values_list("title", flat=True))})


urlpatterns = [
    path("direct/books/", _BookListView.as_view()),
    path("direct/catalogue-books/", _CatalogueBookListView.as_view()),
    path("direct/branches/", _BranchListView.as_view()),
    path("direct/lazy-actor-books/", _LazyActorBookListView.as_view()),
    path(
        "direct/view-books/",
        _ListedFilterView.as_view(
            filterset_class=BookFilter,
            queryset=models.Book.objects.order_by("pk"),
        ),
    ),
    path(
        "direct/view-catalogue-books/",
        _ListedFilterView.as_view(
            filterset_class=CatalogueBookFilter,
            queryset=models.Book.objects.order_by("pk"),
        ),
    ),
    path(
        "direct/view-branches/",
        _ListedFilterView.as_view(
            filterset_class=BranchFilter,
            queryset=models.Branch.objects.order_by("pk"),
            column="name",
        ),
    ),
    path("direct/consumer-books/", _consumer_book_titles),
    path("direct/consumer-books-without-request/", _consumer_book_titles_without_request),
    path("direct/heads/backend/books/", _BookListView.as_view()),
    path("direct/heads/backend/shelves/", _ShelfListView.as_view()),
    path("direct/heads/backend/branches/", _BranchListView.as_view()),
    path("direct/heads/backend/genres/", _GenreListView.as_view()),
    *(
        path(
            f"direct/heads/filter-view/{route}/",
            _CheckedFilterView.as_view(
                filterset_class=filterset_class,
                queryset=queryset,
                column=column,
            ),
        )
        for route, (filterset_class, queryset, column) in _HEAD_SETS.items()
    ),
    path("direct/heads/consumer/<str:route>/", _consumer_rows),
]


def _world() -> dict[str, int]:
    """An open branch's open and secret shelves (the secret one also a second branch's), a vault's."""
    home = models.Branch.objects.create(name="Home", city="Boston")
    annex = models.Branch.objects.create(name="Annex", city="Boston")
    vault = models.Branch.objects.create(name="Vault", city="restricted")
    open_shelf = models.Shelf.objects.create(code="S-open", topic="general", branch=home)
    secret = models.Shelf.objects.create(code="S-secret", topic="secret", branch=home)
    vault_shelf = models.Shelf.objects.create(code="S-vault", topic="general", branch=vault)
    secret.alt_branches.add(annex)
    _ = models.Book.objects.create(title="b-open", shelf=open_shelf)
    _ = models.Book.objects.create(title="b-secret", shelf=secret)
    _ = models.Book.objects.create(title="b-vault", shelf=vault_shelf)
    return {"secret": require_instance(secret.pk, int)}


def _client(viewer: str) -> Client:
    client = Client()
    if viewer == "staff":
        client.force_login(get_user_model().objects.get(username="staff_1"))
    return client


def _listed_names(
    client: Client,
    route: str,
    query: dict[str, str],
    column: str,
) -> list[str]:
    with override_settings(ROOT_URLCONF=__name__):
        response = client.get(f"/direct/{route}/?{_query_string(query)}")
    assert response.status_code == 200, response.content
    return sorted(json_str(row, column) for row in json_list(json_loads(response.content)))


def _query_string(query: dict[str, str]) -> str:
    data = QueryDict(mutable=True)
    data.update(query)
    return data.urlencode()


def _graphql_names(client: Client, document: str) -> list[str]:
    payload = graphql_payload(document, client=client)
    rows = json_list(json_object(payload, "data"), "rows")
    return sorted(json_str(row, "k") for row in rows)


class _BackendRow(NamedTuple):
    """A ``DjangoFilterBackend`` query and the same filter over fakeshop's ``/graphql/``."""

    route: str
    query: dict[str, str]
    column: str
    twin: str
    anonymous: list[str]
    staff: list[str]


_BACKEND_ROWS = {
    "forward-key-to-a-hidden-shelf": _BackendRow(
        "catalogue-books",
        {"shelf": "{secret}"},
        "title",
        "{{ rows: allLibraryCatalogueBooks(filter: {{shelf: {{exact: {secret}}}}}) {{ k: title }} }}",
        [],
        ["b-secret"],
    ),
    "walked-column-on-a-hidden-shelf": _BackendRow(
        "books",
        {"shelf__topic": "secret"},
        "title",
        '{{ rows: allLibraryBooks(filter: {{shelf: {{topic: {{exact: "secret"}}}}}}) {{ k: title }} }}',
        [],
        ["b-secret"],
    ),
    "walked-through-a-hidden-branch": _BackendRow(
        "books",
        {"shelf__branch__name": "Vault"},
        "title",
        (
            '{{ rows: allLibraryBooks(filter: {{shelf: {{branch: {{name: {{exact: "Vault"}}}}}}}}) '
            "{{ k: title }} }}"
        ),
        [],
        ["b-vault"],
    ),
    "to-many-key-naming-a-hidden-shelf": _BackendRow(
        "branches",
        {"alt_shelves": "{secret}"},
        "name",
        "{{ rows: allLibraryBranches(filter: {{altShelves: {{exact: [{secret}]}}}}) {{ k: name }} }}",
        [],
        ["Annex"],
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("shape", sorted(_BACKEND_ROWS))
def test_django_filter_backend_scopes_each_hop_as_the_sessions_actor(
    shape: str,
    viewer: str,
) -> None:
    """``DjangoFilterBackend``'s set answers as the same filter over GraphQL for the viewer."""
    create_users(1)
    row = _BACKEND_ROWS[shape]
    pks = _world()
    client = _client(viewer)
    expected = row.staff if viewer == "staff" else row.anonymous
    query = {key: value.format(**pks) for key, value in row.query.items()}

    assert _listed_names(client, row.route, query, row.column) == expected
    assert _graphql_names(client, row.twin.format(**pks)) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("shape", sorted(_BACKEND_ROWS))
def test_filter_view_scopes_each_hop_as_the_sessions_actor(shape: str, viewer: str) -> None:
    """django-filter's ``FilterView`` set answers as the same filter over GraphQL for the viewer."""
    create_users(1)
    row = _BACKEND_ROWS[shape]
    pks = _world()
    client = _client(viewer)
    expected = row.staff if viewer == "staff" else row.anonymous
    query = {key: value.format(**pks) for key, value in row.query.items()}

    assert _listed_names(client, f"view-{row.route}", query, row.column) == expected
    assert _graphql_names(client, row.twin.format(**pks)) == expected


# (consumer JSON data, the same filter over /graphql/)
_ARM_ROWS = {
    "flat-key-in-an-or-arm": (
        {"or": [{"shelf__code": "S-secret"}]},
        (
            '{ rows: allLibraryBooks(filter: {or: [{shelf: {code: {exact: "S-secret"}}}]}) '
            "{ k: title } }"
        ),
    ),
    "nested-branch-in-an-or-arm": (
        {"or": [{"shelf": {"code": {"exact": "S-secret"}}}]},
        (
            '{ rows: allLibraryBooks(filter: {or: [{shelf: {code: {exact: "S-secret"}}}]}) '
            "{ k: title } }"
        ),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("shape", sorted(_ARM_ROWS))
def test_a_consumer_built_set_scopes_its_logical_arms_as_the_requests_actor(
    shape: str,
    viewer: str,
) -> None:
    """A set a consumer view builds with ``request=`` scopes every arm as GraphQL does."""
    create_users(1)
    data, document = _ARM_ROWS[shape]
    _ = _world()
    client = _client(viewer)
    expected = ["b-secret"] if viewer == "staff" else []

    assert _post_consumer(client, "consumer-books", data) == expected
    assert _graphql_names(client, document) == expected


def _post_consumer(client: Client, route: str, data: Mapping[str, object]) -> list[object]:
    with override_settings(ROOT_URLCONF=__name__):
        # raw-envelope exemption: a consumer's own non-GraphQL view (a DRF / django-filter
        # route), which no GraphQL client helper reaches.
        response = client.post(
            f"/direct/{route}/",
            data=json.dumps(data),
            content_type="application/json",
        )
    assert response.status_code == 200, response.content
    return json_list(json_loads(response.content), "titles")


# The consumer data each row sends: a walked key's hop and a logical arm's branch.
_HOOK_SHAPES: dict[str, dict[str, object]] = {
    "walked-key": {"shelf__topic": "secret"},
    "nested-branch-in-an-or-arm": {"or": [{"shelf": {"topic": {"exact": "secret"}}}]},
}

# How a hook reads the request off ``info.context``: Strawberry's context answers all three.
_CONTEXT_READS: dict[str, Callable[[_DirectRequestContext], object]] = {
    "attribute": lambda context: context.request,
    "item": lambda context: context["request"],
    "get": lambda context: context.get("request"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("read", sorted(_CONTEXT_READS))
@pytest.mark.parametrize("shape", sorted(_HOOK_SHAPES))
def test_a_consumer_built_sets_hooks_read_the_request_off_the_context(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    read: str,
) -> None:
    """Each hook reads the view's request off ``info.context`` as Strawberry's context spells it.

    The context holds no response (``None``): nothing would merge one into the view's reply.
    """
    create_users(1)
    _ = _world()
    seen: list[tuple[object, object]] = []

    def hook(
        _cls: type[library_schema.ShelfType],
        queryset: QuerySet[models.Shelf],
        info: object,
    ) -> QuerySet[models.Shelf]:
        context = require_instance(read_attr(info, "context"), _DirectRequestContext)
        request = require_instance(_CONTEXT_READS[read](context), HttpRequest)
        seen.append((request.user.get_username(), context.response))
        return queryset

    monkeypatch.setattr(library_schema.ShelfType, "get_queryset", classmethod(hook))
    client = _client("staff")

    assert _post_consumer(client, "consumer-books", _HOOK_SHAPES[shape]) == ["b-secret"]
    assert set(seen) == {("staff_1", None)}


# The same filters over /graphql/, for the memo rows.
_HOOK_TWINS = {
    "walked-key": '{ rows: allLibraryBooks(filter: {shelf: {topic: {exact: "secret"}}}) { k: title } }',
    "nested-branch-in-an-or-arm": (
        '{ rows: allLibraryBooks(filter: {or: [{shelf: {topic: {exact: "secret"}}}]}) '
        "{ k: title } }"
    ),
}

# The attribute a memoizing hook stores on ``info.context``.
_MEMO = "visible_shelf_memo"


@pytest.mark.django_db
@pytest.mark.parametrize("surface", ["direct", "graphql"])
@pytest.mark.parametrize("shape", sorted(_HOOK_SHAPES))
def test_a_hook_memoizes_on_the_context_on_either_path(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    surface: str,
) -> None:
    """A hook may store a value on ``info.context`` and read it back, as Strawberry's allows."""
    create_users(1)
    _ = _world()
    seen: list[object] = []

    def hook(
        _cls: type[library_schema.ShelfType],
        queryset: QuerySet[models.Shelf],
        info: object,
    ) -> QuerySet[models.Shelf]:
        context = read_attr(info, "context")
        setattr(context, _MEMO, len(seen))
        seen.append(read_attr(context, _MEMO))
        return queryset

    monkeypatch.setattr(library_schema.ShelfType, "get_queryset", classmethod(hook))
    client = _client("staff")

    if surface == "direct":
        assert _post_consumer(client, "consumer-books", _HOOK_SHAPES[shape]) == ["b-secret"]
    else:
        assert _graphql_names(client, _HOOK_TWINS[shape]) == ["b-secret"]
    assert seen
    assert seen == list(range(len(seen)))


@pytest.mark.django_db
@pytest.mark.parametrize("shape", sorted(_HOOK_SHAPES))
def test_a_set_built_without_a_request_hands_its_hooks_no_info(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
) -> None:
    """With no ``request=`` there is no actor to read: each hook receives ``None``.

    A logical arm's nested branch then has no request to apply its child set with, which the
    shared request read refuses.
    """
    create_users(1)
    _ = _world()
    seen: list[object] = []

    def hook(
        _cls: type[library_schema.ShelfType],
        queryset: QuerySet[models.Shelf],
        info: object,
    ) -> QuerySet[models.Shelf]:
        seen.append(info)
        return queryset.exclude(topic="secret")

    monkeypatch.setattr(library_schema.ShelfType, "get_queryset", classmethod(hook))
    client = _client("staff")
    route = "consumer-books-without-request"

    if shape == "walked-key":
        assert _post_consumer(client, route, _HOOK_SHAPES[shape]) == []
    else:
        with pytest.raises(ConfigurationError, match=r"requires `info\.context`"):
            _ = _post_consumer(client, route, _HOOK_SHAPES[shape])
    assert seen == [None]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "staff"),
    [
        pytest.param({"shelf__topic": "secret"}, ["b-secret"], id="walked-key"),
        pytest.param({"shelf__branch__name": "Vault"}, ["b-vault"], id="walked-through-a-branch"),
    ],
)
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
def test_a_backend_set_reads_the_user_drf_authenticates_not_djangos(
    query: dict[str, str],
    staff: list[str],
    viewer: str,
) -> None:
    """The context holds DRF's ``Request``, so a hook's ``request.user`` runs DRF authentication.

    The view authenticates from a header and only on the first ``request.user`` read, so the
    Django request under DRF's never learns the user: only DRF's ``Request`` names staff.
    """
    create_users(1)
    _ = _world()
    headers = {"X-Actor": "staff_1"} if viewer == "staff" else {}

    with override_settings(ROOT_URLCONF=__name__):
        response = Client().get(
            f"/direct/lazy-actor-books/?{_query_string(query)}",
            headers=headers,
        )

    assert response.status_code == 200, response.content
    titles = sorted(json_str(row, "title") for row in json_list(json_loads(response.content)))
    assert titles == (staff if viewer == "staff" else [])


# A key naming no row: a raw head refuses it, its nested twin matches nothing.
_MISSING = 999999

# The answer of an entry point whose form refused the request (status 400).
_REFUSED = "refused"


def _head_world() -> dict[str, int]:
    """Branches, shelves, books and genres each with a row the anonymous viewer cannot see.

    ``ShelfType`` hides ``S-secret`` (topic ``secret``), ``BookType`` hides ``b-repair`` (in
    repair) and ``BranchType`` hides ``Vault`` (city ``restricted``) from anonymous viewers;
    staff see every row. ``BranchFilter.shelves`` declares ``queryset=`` the
    ``permanent collection`` shelves, so ``S-gen`` and ``S-secret`` are outside it for every
    viewer. No row a viewer's root type hides answers a row here, so each raw answer is
    comparable with its ``/graphql/`` twin, whose root runs that hook. Keys are explicit:
    ``Vault``'s equals the visible ``S-gen``'s and ``Home``'s no shelf's, so a copied head's
    key read against its first hop's rows instead of its last hop's answers otherwise.
    """
    home = models.Branch.objects.create(pk=1, name="Home", city="Boston")
    annex = models.Branch.objects.create(pk=2, name="Annex", city="Boston")
    vault = models.Branch.objects.create(pk=21, name="Vault", city="restricted")
    perm = models.Shelf.objects.create(
        pk=20,
        code="S-perm",
        topic="permanent collection",
        branch=home,
    )
    general = models.Shelf.objects.create(pk=21, code="S-gen", topic="general", branch=home)
    secret = models.Shelf.objects.create(pk=22, code="S-secret", topic="secret", branch=home)
    repairs = models.Shelf.objects.create(pk=23, code="S-repairs", topic="general", branch=annex)
    b_perm = models.Book.objects.create(pk=40, title="b-perm", shelf=perm)
    b_gen = models.Book.objects.create(pk=41, title="b-gen", shelf=general)
    _ = models.Book.objects.create(pk=42, title="b-secret", shelf=secret)
    b_repair = models.Book.objects.create(
        pk=43,
        title="b-repair",
        shelf=repairs,
        circulation_status=models.Book.CirculationStatus.REPAIR,
    )
    g_open = models.Genre.objects.create(pk=60, name="G-open")
    g_repair = models.Genre.objects.create(pk=61, name="G-repair")
    g_open.books.add(b_perm, b_gen)
    g_repair.books.add(b_repair)
    return {
        "home": require_instance(home.pk, int),
        "vault": require_instance(vault.pk, int),
        "perm": require_instance(perm.pk, int),
        "general": require_instance(general.pk, int),
        "secret": require_instance(secret.pk, int),
        "b_perm": require_instance(b_perm.pk, int),
        "b_gen": require_instance(b_gen.pk, int),
        "b_repair": require_instance(b_repair.pk, int),
        "g_open": require_instance(g_open.pk, int),
        "missing": _MISSING,
    }


class _HeadRow(NamedTuple):
    """A raw query naming a ``RelatedFilter`` head, its ``/graphql/`` nested twin, the answers.

    An answer is the matched rows' column, or ``_REFUSED`` where the form refuses the key
    (the twin, which cannot name a head, matches nothing there).
    """

    route: str
    query: dict[str, list[str]]
    twin: str
    anonymous: list[str] | str
    staff: list[str] | str


_HEAD_ROWS = {
    "own-forward-head-visible": _HeadRow(
        "books",
        {"shelf": ["{perm}"]},
        '{{ rows: allLibraryBooks(filter: {{shelf: {{code: {{exact: "S-perm"}}}}}}) {{ k: title }} }}',
        ["b-perm"],
        ["b-perm"],
    ),
    "own-forward-head-hidden": _HeadRow(
        "books",
        {"shelf": ["{secret}"]},
        '{{ rows: allLibraryBooks(filter: {{shelf: {{code: {{exact: "S-secret"}}}}}}) {{ k: title }} }}',
        _REFUSED,
        ["b-secret"],
    ),
    "own-forward-head-missing": _HeadRow(
        "books",
        {"shelf": ["{missing}"]},
        '{{ rows: allLibraryBooks(filter: {{shelf: {{code: {{exact: "none"}}}}}}) {{ k: title }} }}',
        _REFUSED,
        _REFUSED,
    ),
    "own-reverse-foreign-key-head-hidden": _HeadRow(
        "shelves",
        {"books": ["{b_repair}"]},
        '{{ rows: allLibraryShelves(filter: {{books: {{title: {{exact: "b-repair"}}}}}}) {{ k: code }} }}',
        _REFUSED,
        ["S-repairs"],
    ),
    "own-scoped-to-many-head-hidden": _HeadRow(
        "branches",
        {"shelves": ["{secret}"]},
        '{{ rows: allLibraryBranches(filter: {{shelves: {{code: {{exact: "S-secret"}}}}}}) {{ k: name }} }}',
        _REFUSED,
        _REFUSED,
    ),
    "own-scoped-to-many-head-out-of-scope": _HeadRow(
        "branches",
        {"shelves": ["{general}"]},
        '{{ rows: allLibraryBranches(filter: {{shelves: {{code: {{exact: "S-gen"}}}}}}) {{ k: name }} }}',
        _REFUSED,
        _REFUSED,
    ),
    "own-reverse-many-to-many-head-hidden": _HeadRow(
        "genres",
        {"books": ["{b_repair}"]},
        '{{ rows: allLibraryGenres(filter: {{books: {{title: {{exact: "b-repair"}}}}}}) {{ k: name }} }}',
        _REFUSED,
        ["G-repair"],
    ),
    "own-many-to-many-head-visible": _HeadRow(
        "books",
        {"genres": ["{g_open}"]},
        '{{ rows: allLibraryBooks(filter: {{genres: {{name: {{exact: "G-open"}}}}}}) {{ k: title }} }}',
        ["b-gen", "b-perm"],
        ["b-gen", "b-perm"],
    ),
    "own-many-to-many-head-missing": _HeadRow(
        "books",
        {"genres": ["{missing}"]},
        '{{ rows: allLibraryBooks(filter: {{genres: {{name: {{exact: "none"}}}}}}) {{ k: title }} }}',
        _REFUSED,
        _REFUSED,
    ),
    "copied-head-visible-through-a-hidden-shelf": _HeadRow(
        "books",
        {"shelf__branch": ["{home}"]},
        (
            '{{ rows: allLibraryBooks(filter: {{shelf: {{branch: {{name: {{exact: "Home"}}}}}}}}) '
            "{{ k: title }} }}"
        ),
        ["b-gen", "b-perm"],
        ["b-gen", "b-perm", "b-secret"],
    ),
    "copied-head-hidden": _HeadRow(
        "books",
        {"shelf__branch": ["{vault}"]},
        (
            '{{ rows: allLibraryBooks(filter: {{shelf: {{branch: {{name: {{exact: "Vault"}}}}}}}}) '
            "{{ k: title }} }}"
        ),
        _REFUSED,
        [],
    ),
    "copied-head-two-hops-down-hidden": _HeadRow(
        "branches",
        {"shelves__books__shelf": ["{secret}"]},
        (
            "{{ rows: allLibraryBranches(filter: {{shelves: {{books: {{shelf: "
            '{{code: {{exact: "S-secret"}}}}}}}}}}) {{ k: name }} }}'
        ),
        _REFUSED,
        [],
    ),
    "copied-head-two-hops-down-out-of-scope": _HeadRow(
        "branches",
        {"shelves__books__shelf": ["{general}"]},
        (
            "{{ rows: allLibraryBranches(filter: {{shelves: {{books: {{shelf: "
            '{{code: {{exact: "S-gen"}}}}}}}}}}) {{ k: name }} }}'
        ),
        [],
        [],
    ),
    "copied-head-two-hops-down-in-scope": _HeadRow(
        "branches",
        {"shelves__books__shelf": ["{perm}"]},
        (
            "{{ rows: allLibraryBranches(filter: {{shelves: {{books: {{shelf: "
            '{{code: {{exact: "S-perm"}}}}}}}}}}) {{ k: name }} }}'
        ),
        ["Home"],
        ["Home"],
    ),
    "to-many-head-reads-its-last-value": _HeadRow(
        "shelves",
        {"books": ["{b_gen}", "{b_perm}"]},
        '{{ rows: allLibraryShelves(filter: {{books: {{title: {{exact: "b-perm"}}}}}}) {{ k: code }} }}',
        ["S-perm"],
        ["S-perm"],
    ),
}

# Every entry point building the package's set outside the GraphQL pipeline.
_ENTRY_POINTS = ("backend", "filter-view", "consumer")


def _head_response(
    client: Client,
    entry: str,
    route: str,
    query: dict[str, list[str]],
) -> "_MonkeyPatchedWSGIResponse":
    data = QueryDict(mutable=True)
    for key, values in query.items():
        data.setlist(key, values)
    with override_settings(ROOT_URLCONF=__name__):
        return client.get(f"/direct/heads/{entry}/{route}/?{data.urlencode()}")


def _head_answer(response: "_MonkeyPatchedWSGIResponse", column: str) -> list[str] | str:
    if response.status_code == 400:
        return _REFUSED
    assert response.status_code == 200, response.content
    return sorted(json_str(row, column) for row in json_list(json_loads(response.content)))


def _formatted(query: dict[str, list[str]], pks: dict[str, int]) -> dict[str, list[str]]:
    return {key: [value.format(**pks) for value in values] for key, values in query.items()}


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("entry", _ENTRY_POINTS)
@pytest.mark.parametrize("shape", sorted(_HEAD_ROWS))
def test_a_raw_head_reads_its_relation_as_the_walked_key_does(
    shape: str,
    entry: str,
    viewer: str,
) -> None:
    """A ``RelatedFilter`` head the raw form names matches through the rows its nested twin sees.

    The head walks its path as a relation key: each hop's target ``get_queryset`` for the
    request's actor and each declaration's ``queryset=`` scope it, a copied head's
    intermediate hops included, and its key is validated against the visible rows of its
    relation's target, so a hidden row is refused as a missing one is while its nested twin
    matches nothing. A to-many head's ``Select`` reads the last value it is sent.
    """
    create_users(1)
    row = _HEAD_ROWS[shape]
    pks = _head_world()
    client = _client(viewer)
    expected = row.staff if viewer == "staff" else row.anonymous
    column = _HEAD_SETS[row.route][2]

    response = _head_response(client, entry, row.route, _formatted(row.query, pks))

    assert _head_answer(response, column) == expected
    assert _graphql_names(client, row.twin.format(**pks)) == (
        [] if expected == _REFUSED else expected
    )


# (route, head, the hidden row's key, a key naming no row)
_ORACLE_ROWS = {
    "own-forward-head": ("books", "shelf", "secret"),
    "own-reverse-foreign-key-head": ("shelves", "books", "b_repair"),
    "own-reverse-many-to-many-head": ("genres", "books", "b_repair"),
    "copied-head": ("books", "shelf__branch", "vault"),
    "copied-head-two-hops-down": ("branches", "shelves__books__shelf", "secret"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("entry", _ENTRY_POINTS)
@pytest.mark.parametrize("shape", sorted(_ORACLE_ROWS))
def test_a_raw_head_refuses_a_hidden_key_as_a_missing_one(shape: str, entry: str) -> None:
    """The anonymous viewer cannot tell a hidden row's key from one naming no row.

    Both are refused with the same body, the form's ``invalid_choice`` for the head.
    """
    create_users(1)
    route, head, hidden = _ORACLE_ROWS[shape]
    pks = _head_world()
    client = _client("anonymous")

    hidden_response = _head_response(client, entry, route, {head: [str(pks[hidden])]})
    missing_response = _head_response(client, entry, route, {head: [str(_MISSING)]})

    assert hidden_response.status_code == 400, hidden_response.content
    assert hidden_response.content == missing_response.content
    assert missing_response.status_code == 400
    assert b"Select a valid choice" in hidden_response.content


def _count_visibility_hooks(monkeypatch: pytest.MonkeyPatch) -> Counter[str]:
    """Count each ``get_queryset`` run of the library types that hide rows, by type."""
    calls: Counter[str] = Counter()

    def count(scope: type[DjangoType]) -> None:
        hook: Callable[..., object] = scope.get_queryset
        name = scope.__name__

        def counting(_cls: type[DjangoType], queryset: QuerySet[Model], info: object) -> object:
            calls[name] += 1
            return hook(queryset, info)

        monkeypatch.setattr(scope, "get_queryset", classmethod(counting))

    for scope in (library_schema.BookType, library_schema.ShelfType, library_schema.BranchType):
        count(scope)
    return calls


# (route, raw query, the hook runs it costs by type)
_RAW_COST_ROWS: dict[str, tuple[str, dict[str, list[str]], dict[str, int]]] = {
    "books-naming-no-head": ("books", {"title": ["b-perm"]}, {}),
    "branches-naming-no-head": ("branches", {"name": ["Home"]}, {}),
    "own-head": ("books", {"shelf": ["{perm}"]}, {"ShelfType": 1}),
    "own-head-and-its-walked-key": (
        "books",
        {"shelf": ["{perm}"], "shelf__code": ["S-perm"]},
        {"ShelfType": 1},
    ),
    "copied-head-two-hops-down": (
        "branches",
        {"shelves__books__shelf": ["{perm}"]},
        {"BookType": 1, "ShelfType": 2},
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("entry", _ENTRY_POINTS)
@pytest.mark.parametrize("shape", sorted(_RAW_COST_ROWS))
def test_a_raw_head_runs_each_hops_hook_once_and_an_absent_one_none(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    entry: str,
) -> None:
    """A named head runs each hop's ``get_queryset`` once, for its walk and its choices alike.

    A request naming no head runs none: an absent head is neither walked nor scoped.
    """
    create_users(1)
    route, query, cost = _RAW_COST_ROWS[shape]
    pks = _head_world()
    calls = _count_visibility_hooks(monkeypatch)

    response = _head_response(_client("anonymous"), entry, route, _formatted(query, pks))

    assert response.status_code == 200, response.content
    assert dict(calls) == cost


# (a /graphql/ document, the hook runs it costs by type, the sets it builds by class)
_GRAPHQL_COST_ROWS: dict[str, tuple[str, dict[str, int], dict[str, int]]] = {
    "column": (
        '{ rows: allLibraryBooks(filter: {title: {exact: "b-perm"}}) { k: title } }',
        {"BookType": 1},
        {"BookFilter": 1},
    ),
    "nested-branch": (
        '{ rows: allLibraryBooks(filter: {shelf: {code: {exact: "S-perm"}}}) { k: title } }',
        {"BookType": 1, "ShelfType": 1},
        {"BookFilter": 1, "BranchFilter": 1, "ShelfFilter": 1},
    ),
    # ``BranchFilter.shelf_codes`` walks ``shelves``: its absent-leaf probe builds ``ShelfFilter``.
    "branches-column": (
        '{ rows: allLibraryBranches(filter: {name: {exact: "Home"}}) { k: name } }',
        {"BranchType": 1},
        {"BranchFilter": 1, "ShelfFilter": 1},
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("shape", sorted(_GRAPHQL_COST_ROWS))
def test_graphql_sets_walk_and_scope_no_head(monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
    """A set the GraphQL pipeline builds names no head: no head adds a hook run or a set.

    An absent walked leaf's probe builds its hop's target set once and runs no hook.
    """
    create_users(1)
    document, cost, built = _GRAPHQL_COST_ROWS[shape]
    _ = _head_world()
    calls = _count_visibility_hooks(monkeypatch)
    sets: Counter[str] = Counter()
    original_init = FilterSet.__init__

    def counting_init(
        self: FilterSet,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        sets[type(self).__name__] += 1
        original_init(self, data, queryset, request=request, prefix=prefix)

    monkeypatch.setattr(FilterSet, "__init__", counting_init)

    assert _graphql_names(Client(), document)
    assert dict(calls) == cost
    assert dict(sets) == built
