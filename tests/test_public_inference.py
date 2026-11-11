"""What a consumer's type checker infers for the public API, pinned with ``assert_type``.

Each pin wraps a public call as a consumer writes it, so a change to the inferred type is
a ``reportAssertTypeFailure`` and a visible diff in this module. Where the public type
carries ``Any`` (``DjangoType.get_queryset``'s base return), which no pin can spell
without an ignore, a typed assignment checks it instead. The client pins post to this
module's own ``urlpatterns``, a view answering one canned payload, so they need no
database and no schema.

``assert_type`` is a no-op at run time (it returns its argument), so basedpyright is the
check: the main pass and the 3.10 floor pass (``pyrightconfig.floor.json``) both read
this module. pytest only proves the module imports, that each query class it declares
builds as the consumer's would, and that each set applies.
"""

from collections.abc import Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import strawberry
from apps.library.models import Genre
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.test import SimpleTestCase, override_settings
from django.urls import re_path
from graphql import GraphQLFormattedError
from strawberry import relay
from strawberry.types import get_object_definition
from typing_extensions import assert_type, override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoNodeField,
    DjangoNodesField,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.auth import current_user
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import (
    AsyncTestClient,
    GraphQLTestMixin,
    Response,
    TestClient,
)
from tests._info import make_info

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedASGIResponse, _MonkeyPatchedWSGIResponse
else:
    # django-stubs' names for Django's test-client responses exist only in the stubs; at run
    # time ``assert_type`` ignores its type argument, which needs only to evaluate.
    _MonkeyPatchedWSGIResponse = _MonkeyPatchedASGIResponse = HttpResponse

pytestmark = pytest.mark.usefixtures("isolate_global_registry")

_QUERY = "{ ok }"


def _graphql_view(_request: HttpRequest) -> HttpResponse:
    """Answer every post with one successful GraphQL payload."""
    return JsonResponse({"data": {"ok": True}})


#: This module is its own ``ROOT_URLCONF`` for the client pins: every path reaches the view.
urlpatterns = [re_path(r"^.*$", _graphql_view)]


@pytest.fixture
def local_graphql_urlconf() -> Iterator[None]:
    """Route the Django test clients to ``_graphql_view`` with no middleware in the way."""
    with override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[]):
        yield


class GenreFilter(FilterSet):
    """A consumer filter set over ``Genre``, wired onto a type by ``_wire_genre_sets``."""

    class Meta:
        model = Genre
        fields = {"name": ["exact"]}


class GenreOrder(OrderSet):
    """A consumer order set over ``Genre``, wired onto a type by ``_wire_genre_sets``."""

    class Meta:
        model = Genre
        fields = ["name"]


def _wire_genre_sets() -> strawberry.Info[object, object]:
    """Wire both sets onto a Relay-Node ``Genre`` type, finalize, and return a resolver ``info``."""

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = GenreFilter
            orderset_class = GenreOrder

    finalize_django_types()
    assert registry.get(Genre) is GenreType
    return make_info(context=SimpleNamespace(request=HttpRequest()))


def _field_names(query_type: type) -> set[str]:
    """Return the Python names of the fields Strawberry built on ``query_type``."""
    return {field.python_name for field in get_object_definition(query_type, strict=True).fields}


def test_field_factories_infer_the_value_the_field_resolves_to() -> None:
    """Each field factory's call infers the value the field resolves to.

    The pins sit on unannotated locals: inside a class body the attribute's declared type
    is inference context, from which a generic factory can solve its own return and echo
    the annotation. The query class then declares the fields as a consumer does.
    """

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)

    list_field = assert_type(DjangoListField(GenreType), list[GenreType])
    connection_field = assert_type(DjangoConnectionField(GenreType), DjangoConnection[GenreType])
    node_field = assert_type(DjangoNodeField(GenreType), GenreType | None)
    nodes_field = assert_type(DjangoNodesField(GenreType), list[GenreType | None])
    any_node_field = assert_type(DjangoNodeField(), relay.Node | None)
    any_nodes_field = assert_type(DjangoNodesField(), list[relay.Node | None])

    @strawberry.type
    class Query:
        all_genres: list[GenreType] = list_field
        genre_connection: DjangoConnection[GenreType] = connection_field
        genre: GenreType | None = node_field
        genres: list[GenreType | None] = nodes_field
        node: relay.Node | None = any_node_field
        nodes: list[relay.Node | None] = any_nodes_field

    assert _field_names(Query) == {
        "all_genres",
        "genre_connection",
        "genre",
        "genres",
        "node",
        "nodes",
    }


def test_current_user_infers_object() -> None:
    """``current_user()`` declares ``object``; the unannotated ``me`` attribute reads as it."""

    @strawberry.type
    class Query:
        me = current_user()

    assert_type(Query.me, object)
    assert _field_names(Query) == {"me"}


def test_set_apply_sync_keeps_the_model_of_the_queryset_it_was_given() -> None:
    """``apply_sync`` on either set infers ``QuerySet[Genre]`` from a ``QuerySet[Genre]``."""
    info = _wire_genre_sets()
    queryset = Genre.objects.none()

    filtered = assert_type(GenreFilter.apply_sync({}, queryset, info), QuerySet[Genre])
    ordered = assert_type(GenreOrder.apply_sync({}, filtered, info), QuerySet[Genre])

    assert ordered.model is Genre


async def test_set_apply_async_keeps_the_model_of_the_queryset_it_was_given() -> None:
    """``apply_async`` on either set infers ``QuerySet[Genre]`` from a ``QuerySet[Genre]``."""
    info = _wire_genre_sets()
    queryset = Genre.objects.none()

    filtered = assert_type(await GenreFilter.apply_async({}, queryset, info), QuerySet[Genre])
    ordered = assert_type(await GenreOrder.apply_async({}, filtered, info), QuerySet[Genre])

    assert ordered.model is Genre


def test_get_queryset_base_hook_assigns_to_the_model_queryset() -> None:
    """The base hook's return assigns to the caller's ``QuerySet[Genre]``, inherited or through ``super()``.

    The base declares ``QuerySet[Any, Any]``, which ``assert_type``
    cannot spell without a ``reportExplicitAny`` ignore, so the package hook is checked by
    assignment: a base return that stopped being a queryset fails ``reportAssignmentType``
    at both sites. The README override spelling also passes ``@override`` against the base.
    """

    class PlainGenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class ScopedGenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            primary = False

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Genre], info: strawberry.Info) -> QuerySet[Genre]:
            rows: QuerySet[Genre] = super().get_queryset(queryset, info)
            return rows.filter(name__isnull=False)

    info = make_info(context=SimpleNamespace(request=HttpRequest()))
    inherited: QuerySet[Genre] = PlainGenreType.get_queryset(Genre.objects.none(), info)
    scoped = ScopedGenreType.get_queryset(Genre.objects.none(), info)

    assert inherited.model is Genre
    assert scoped.model is Genre


@pytest.mark.usefixtures("local_graphql_urlconf")
def test_test_client_query_infers_the_wsgi_response() -> None:
    """``TestClient().query(...)`` returns ``Response[_MonkeyPatchedWSGIResponse]``."""
    response = assert_type(TestClient().query(_QUERY), Response[_MonkeyPatchedWSGIResponse])

    errors = assert_type(response.errors, list[GraphQLFormattedError] | None)
    raw = assert_type(response.response, _MonkeyPatchedWSGIResponse)

    assert errors is None
    assert raw.status_code == 200


@pytest.mark.usefixtures("local_graphql_urlconf")
async def test_async_test_client_query_infers_the_asgi_response() -> None:
    """An awaited ``AsyncTestClient().query(...)`` returns ``Response[_MonkeyPatchedASGIResponse]``."""
    response = assert_type(
        await AsyncTestClient().query(_QUERY),
        Response[_MonkeyPatchedASGIResponse],
    )

    errors = assert_type(response.errors, list[GraphQLFormattedError] | None)
    raw = assert_type(response.response, _MonkeyPatchedASGIResponse)

    assert errors is None
    assert raw.status_code == 200


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
class GraphQLTestMixinInference(GraphQLTestMixin, SimpleTestCase):
    """A consumer unittest case over the mixin: ``self.query(...)`` returns the WSGI response."""

    def test_mixin_query_infers_the_wsgi_response(self) -> None:
        """``GraphQLTestMixin.query(...)`` returns ``Response[_MonkeyPatchedWSGIResponse]``."""
        response = assert_type(self.query(_QUERY), Response[_MonkeyPatchedWSGIResponse])

        self.assertResponseNoErrors(response)
        assert isinstance(response, Response)
