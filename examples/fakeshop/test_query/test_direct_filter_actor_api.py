"""A set built outside the GraphQL pipeline scopes its hops as the request's actor sees them.

DRF's ``DjangoFilterBackend`` builds the package's ``FilterSet`` with ``request=`` its
``Request``, and django-filter's ``FilterView`` and a consumer's own view build one with
``request=`` Django's; none runs a resolver, so no Strawberry ``Info`` exists. Every
``DjangoType.get_queryset`` such a set reaches (a walked key's hop, a relation key's target, an
intermediate model, a logical arm's branch) reads the actor off ``info.context.request`` as it
does under GraphQL, so each answer here equals the same filter's answer over ``/graphql/`` for
the same session: the anonymous viewer never matches through the secret shelf
``ShelfType.get_queryset`` hides, staff do.
"""

import json
from collections.abc import Callable, Mapping
from typing import ClassVar, NamedTuple

import pytest
from apps.library import models
from apps.library import schema as library_schema
from apps.library.filters import BookFilter, BranchFilter, CatalogueBookFilter
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

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters.sets import _DirectRequestContext
from django_strawberry_framework.utils._narrowing import require_instance
from tests._idioms import ModelSerializerBase


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
