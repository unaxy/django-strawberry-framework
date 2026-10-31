"""Live GraphQL HTTP acceptance tests for the ``testing`` package's test-client family.

The request-driving half of ``testing/client.py``'s coverage: every case here
posts through Django's real fakeshop URLconf (the live ``/graphql/`` endpoint or
an intentional missing-endpoint probe) using the package's own ``TestClient`` /
``AsyncTestClient`` / ``GraphQLTestCase`` family. Responses assert transport status,
payloads, authentication changes and the errors raised for invalid requests.

Covered live here: the ``assert_no_errors=True`` raising direction on a real
invalid selection; a non-``dict`` ``variables`` mapping (``MappingProxyType``,
``UserDict``) sent as JSON; the source-level non-JSON ``ValueError`` from a real 404 on
both transport colors; the ``AsyncTestClient`` happy path (awaited transport,
async decode), its ``login()`` bracket including logout when the block raises,
and its nested two-file multipart upload (the async color of
``test_uploads_api.py``'s sync upload, so the DoD's "multipart ... on both
clients" is earned live on both); the sync ``login()`` exception-logout twin
(the clean-exit sync bracket and ``operation_name`` dispatch stay in
``test_products_api.py``); and the unittest family end to end
(``self.query(...)``, both assertion helpers' PASSING directions, the per-call
and ``GRAPHQL_URL`` endpoint rungs against a real view, and the
``TransactionTestCase`` combination).

The async tests that reach the GraphQL view carry ``django_db(transaction=True)``:
``django.test.AsyncClient`` runs the sync view on asgiref's executor thread,
whose separate SQLite connection cannot see rows seeded inside a
non-transactional test's uncommitted transaction; seeding happens in a sync
fixture (not the async body) so the ORM work never runs in the event loop and
raises ``SynchronousOnlyOperation``. The missing-endpoint probe stops at
Django's 404 handler and needs no database.
"""

import io
from collections import UserDict
from collections.abc import Callable, Mapping
from functools import wraps
from pathlib import Path
from types import MappingProxyType

import pytest
from apps.products import schema as products_schema
from apps.products.models import Category, Item
from apps.products.services import create_users, seed_data
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import override_settings
from django.urls import include, path, resolve
from graphql_client import json_at, json_list, json_object, read_attr
from PIL import Image
from typing_extensions import override

from django_strawberry_framework.testing import (
    AsyncTestClient,
    GraphQLTestCase,
    GraphQLTransactionTestCase,
    TestClient,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import DjangoGraphQLView

# ---------------------------------------------------------------------------
# Probe URLconf: ``/alt/`` delegates to whatever the freshly reloaded
# ``/graphql/`` view is, so the GRAPHQL_URL / per-call rungs are proven by a
# POSITIVE hit on the real schema view, not an exception shape. Inert unless a
# test overrides ``ROOT_URLCONF`` to this module (``__name__``).
#
# The probe URLconf also mounts the project's own ``config.urls`` at the root,
# so ``/graphql/`` answers under it too: a row that only asserted a clean
# response would pass whether the request reached ``/alt/`` or fell back to
# ``/graphql/``. The marker header below is what makes the two distinguishable
# - only the delegated response carries it.
# ---------------------------------------------------------------------------

_PROBE_MARKER_HEADER = "X-Probe-Endpoint"
_PROBE_MARKER_VALUE = "alt"


@wraps(DjangoGraphQLView.as_view())
def _alt_graphql_view(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponseBase:
    """Delegate ``/alt/`` to the view ``/graphql/`` currently resolves to, marked.

    Resolving at request time (not import time) keeps the probe pointed at the
    schema view the reload fixture just rebuilt. The response is stamped with
    the probe marker header so a request that routed here is distinguishable
    from one that reached the same view at ``/graphql/``.
    """
    view: Callable[..., object] = resolve("/graphql/").func
    response = view(request, *args, **kwargs)
    assert isinstance(response, HttpResponseBase)
    response[_PROBE_MARKER_HEADER] = _PROBE_MARKER_VALUE
    return response


urlpatterns = [path("", include("config.urls")), path("alt/", _alt_graphql_view)]


# The write-auth-gated products mutation the async ``login()`` bracket drives
# (the live sync twin is ``test_products_api.py``'s TestClient bracket test).
_CREATE_ITEM = (
    "mutation($d: ItemInput!) { createItem(data: $d) { node { name } errors { field messages } } }"
)

_ITEMS_QUERY = (
    "query Items($first: Int) { allItems(first: $first, orderBy: [{name: "
    "ASC}]) { edges { node { name } } } }"
)

# The nested two-file upload mutation the async multipart test drives (the sync
# twin lives in ``test_uploads_api.py``); ``attachment`` / ``image`` are both
# required ``Upload!`` fields on the generated ``MediaSpecimenInput``.
_CREATE_MEDIA = """
mutation Create($data: MediaSpecimenInput!) {
  createMediaSpecimen(data: $data) {
    result {
      label
      attachment { name size url }
      image { name width height }
    }
    errors { field messages }
  }
}
"""

# A 5x9 PNG so the live width / height assertions read distinct, deterministic
# values (a square could pass by coincidence) - the same shape as the sync
# upload suite's fixture.
_IMAGE_WIDTH = 5
_IMAGE_HEIGHT = 9


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (_IMAGE_WIDTH, _IMAGE_HEIGHT)).save(buffer, format="PNG")
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# The sync client's GraphQL-error and non-JSON transport-error shapes.
# ---------------------------------------------------------------------------


def test_assert_no_errors_default_raises_with_the_errors_list() -> None:
    """The default gate raises on a real errors response; the message carries the errors.

    A real fakeshop request (an invalid selection is a validation error - no DB
    is touched): under the default ``assert_no_errors=True`` the errors response
    raises ``AssertionError`` (an explicit raise, so the gate holds under
    ``python -O``) instead of returning, and the errors list rides the message.
    The passing (non-raising) direction is the JSON happy path proven across the
    live suites.
    """
    client = TestClient()
    with pytest.raises(AssertionError) as excinfo:
        client.query("{ nope }")
    assert "nope" in str(excinfo.value)


def test_wrong_configured_endpoint_surfaces_django_non_json_decode_error() -> None:
    """A ``TESTING_ENDPOINT`` typo stays Django's source-level non-JSON ``ValueError``.

    The client deliberately does not replace the transport failure with a
    framework exception: Django's real 404 response is HTML, so
    ``HttpResponse.json()`` names its ``text/html`` content type. This pins the
    public troubleshooting contract against the live URLconf.
    """
    with (
        override_settings(
            DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/missing-graphql-endpoint/"},
        ),
        pytest.raises(ValueError, match=r"Content-Type.*text/html"),
    ):
        TestClient().query("{ __typename }")


@pytest.mark.django_db
@pytest.mark.parametrize("wrap", [MappingProxyType, UserDict], ids=["mappingproxy", "userdict"])
def test_query_sends_a_non_dict_variables_mapping(
    wrap: Callable[[dict[str, object]], Mapping[str, object]],
) -> None:
    """A ``MappingProxyType`` / ``UserDict`` for ``variables=`` reaches the server as JSON.

    ``query()`` accepts any ``Mapping[str, object]``; the builder copies it to a
    plain ``dict`` before encoding. With two seeded items, exactly one edge back
    proves the ``first`` variable arrived rather than being dropped.
    """
    seed_data(2)
    res = TestClient().query(_ITEMS_QUERY, variables=wrap({"first": 1}))
    assert res.errors is None
    assert res.data is not None
    edges = json_list(res.data, "allItems", "edges")
    expected = [
        item.name
        for item in Item.objects.filter(is_private=False, category__is_private=False).order_by(
            "name",
        )[:1]
    ]
    assert edges == [{"node": {"name": name}} for name in expected]
    assert expected


# ---------------------------------------------------------------------------
# The async client: real requests through Django's in-process
# ``AsyncClientHandler`` against the reloaded fakeshop schema.
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_catalog() -> str:
    """Seed catalog rows synchronously and return the first visible ordered item name."""
    seed_data(1)
    return (
        Item.objects.filter(is_private=False, category__is_private=False).order_by("name")[0].name
    )


@pytest.fixture
def permitted_writer() -> tuple[User, str]:
    """A ``create_users`` user granted ``add_item`` + a category GlobalID, for the async bracket.

    Seeds first (AGENTS.md seed-helper rule), then grants the explicit
    ``add_item`` codename: ``view_item_1`` is NOT a superuser, so the
    ``DjangoModelPermission`` codename check runs rather than the superuser
    short-circuit; the user is re-fetched after the grant to drop the stale
    per-request permission cache. The async consumer is transactional so the view's
    executor-thread connection sees the seeded rows.
    """
    create_users(1)
    seed_data(1)

    user = User.objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    user = User.objects.get(pk=read_attr(user, "pk"))  # drop the stale perm cache
    category = Category.objects.earliest("pk")
    category_gid = global_id_for(products_schema.CategoryType, category.pk)
    return user, category_gid


@pytest.mark.django_db(transaction=True)
async def test_async_query_happy_path(seeded_catalog: str) -> None:
    """The awaited request decodes the exact visible ordered page and retains its HTTP response."""
    res = await AsyncTestClient().query(_ITEMS_QUERY, variables={"first": 1})
    assert res.errors is None
    assert res.data == {"allItems": {"edges": [{"node": {"name": seeded_catalog}}]}}
    assert res.response.status_code == 200
    assert res.response["Content-Type"].startswith("application/json")


async def test_async_query_default_gate_raises_for_invalid_selection() -> None:
    """The async client's default assertion gate refuses a real validation error."""
    with pytest.raises(AssertionError, match="nope"):
        await AsyncTestClient().query("{ nope }")


async def test_async_wrong_endpoint_surfaces_the_same_non_json_decode_error() -> None:
    """The async color preserves the sync client's source-level transport failure shape."""
    with pytest.raises(ValueError, match=r"Content-Type.*text/html"):
        await AsyncTestClient("/missing-graphql-endpoint/").query("{ __typename }")


@pytest.mark.django_db(transaction=True)
async def test_async_login_brackets_the_write_authorized_mutation(
    permitted_writer: tuple[User, str],
) -> None:
    """The force-login/logout bracket through ``async with client.login(user)``.

    The sync bracket's async twin (the live sync bracket lives in
    ``test_products_api.py``): the write-auth-gated ``createItem`` is denied
    anonymous (top-level error), succeeds inside the bracket, and is denied
    again after it - the ``sync_to_async``-wrapped session round trip on one
    client instance.
    """
    user, category_gid = permitted_writer
    variables = {"d": {"name": "AsyncBracketWidget", "categoryId": category_gid}}
    client = AsyncTestClient()

    denied = await client.query(_CREATE_ITEM, variables=variables, assert_no_errors=False)
    assert denied.data is None
    assert denied.errors is not None
    assert len(denied.errors) == 1
    assert denied.errors[0].get("message") == "Not authorized to create ItemType."
    assert denied.errors[0].get("path") == ["createItem"]

    async with client.login(user):
        granted = await client.query(_CREATE_ITEM, variables=variables)
        assert granted.data is not None
        assert granted.data["createItem"]["errors"] == []
        assert granted.data["createItem"]["node"]["name"] == "AsyncBracketWidget"

    denied_again = await client.query(_CREATE_ITEM, variables=variables, assert_no_errors=False)
    assert denied_again.data is None
    assert denied_again.errors is not None
    assert len(denied_again.errors) == 1
    assert denied_again.errors[0].get("message") == "Not authorized to create ItemType."
    assert denied_again.errors[0].get("path") == ["createItem"]


@pytest.mark.django_db
def test_sync_login_bracket_logs_out_when_the_block_raises() -> None:
    """A raise inside ``with client.login(user)`` still clears the session on the wire.

    The clean-exit sync bracket lives in ``test_products_api.py``. This row is
    the exception arm: a permitted ``createItem`` succeeds inside the block, the
    block then raises, and the same client is unauthorized afterwards - logout
    ran in ``finally``, not only on the happy path.
    """
    create_users(1)
    seed_data(1)

    user = User.objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    user = User.objects.get(pk=read_attr(user, "pk"))
    category = Category.objects.earliest("pk")
    category_gid = global_id_for(products_schema.CategoryType, category.pk)
    variables = {"d": {"name": "SyncRaiseLogoutWidget", "categoryId": category_gid}}
    client = TestClient()

    def body_that_raises() -> None:
        with client.login(user):
            granted = client.query(_CREATE_ITEM, variables=variables)
            assert granted.data is not None
            assert granted.data["createItem"]["errors"] == []
            assert granted.data["createItem"]["node"]["name"] == "SyncRaiseLogoutWidget"
            raise RuntimeError("sync login error")

    with pytest.raises(RuntimeError, match="sync login error"):
        body_that_raises()

    denied = client.query(
        _CREATE_ITEM,
        variables={"d": {"name": "AfterSyncRaiseWidget", "categoryId": category_gid}},
        assert_no_errors=False,
    )
    assert denied.data is None
    assert denied.errors is not None
    assert len(denied.errors) == 1
    assert denied.errors[0].get("message") == "Not authorized to create ItemType."
    assert denied.errors[0].get("path") == ["createItem"]


@pytest.mark.django_db(transaction=True)
async def test_async_login_bracket_logs_out_when_the_block_raises(
    permitted_writer: tuple[User, str],
) -> None:
    """A raise inside ``async with client.login(user)`` still clears the session on the wire."""
    user, category_gid = permitted_writer
    variables = {"d": {"name": "AsyncRaiseLogoutWidget", "categoryId": category_gid}}
    client = AsyncTestClient()

    async def body_that_raises() -> None:
        async with client.login(user):
            granted = await client.query(_CREATE_ITEM, variables=variables)
            assert granted.data is not None
            assert granted.data["createItem"]["errors"] == []
            assert granted.data["createItem"]["node"]["name"] == "AsyncRaiseLogoutWidget"
            raise RuntimeError("async login error")

    with pytest.raises(RuntimeError, match="async login error"):
        await body_that_raises()

    denied = await client.query(
        _CREATE_ITEM,
        variables={"d": {"name": "AfterAsyncRaiseWidget", "categoryId": category_gid}},
        assert_no_errors=False,
    )
    assert denied.data is None
    assert denied.errors is not None
    assert len(denied.errors) == 1
    assert denied.errors[0].get("message") == "Not authorized to create ItemType."
    assert denied.errors[0].get("path") == ["createItem"]


@pytest.fixture
def upload_superuser() -> User:
    """Grant the seeded staff user the explicit media creation permission for the async upload."""
    create_users(1)
    user = User.objects.get(username="staff_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_mediaspecimen", content_type__app_label="scalars"),
    )
    return User.objects.get(pk=read_attr(user, "pk"))


@pytest.mark.django_db(transaction=True)
async def test_async_multipart_upload_creates_media_specimen(
    upload_superuser: User,
    tmp_path: Path,
) -> None:
    """Nested file placeholders and operation selection create and return both saved uploads."""
    variables = {"data": {"label": "async-uploaded", "attachment": None, "image": None}}
    files: dict[str, object] = {
        "data.attachment": SimpleUploadedFile(
            "async.txt",
            b"async multipart bytes",
            content_type="text/plain",
        ),
        "data.image": SimpleUploadedFile("async.png", _png_bytes(), content_type="image/png"),
    }
    client = AsyncTestClient()
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        async with client.login(upload_superuser):
            res = await client.query(
                _CREATE_MEDIA,
                variables=variables,
                files=files,
                operation_name="Create",
            )
    assert res.response.status_code == 200
    assert res.data is not None
    payload = json_object(res.data, "createMediaSpecimen")
    assert payload["errors"] == []
    result = json_object(payload, "result")
    assert result["label"] == "async-uploaded"
    attachment_name = json_at(result, "attachment", "name")
    assert isinstance(attachment_name, str)
    assert attachment_name.endswith("async.txt")
    assert json_at(result, "attachment", "size") == len(b"async multipart bytes")
    image_name = json_at(result, "image", "name")
    assert isinstance(image_name, str)
    assert image_name.endswith("async.png")
    assert json_at(result, "image", "width") == _IMAGE_WIDTH
    assert json_at(result, "image", "height") == _IMAGE_HEIGHT


# ---------------------------------------------------------------------------
# The unittest family: TestCase-shaped, in-file subclasses driving real
# ``/graphql/`` requests (the assertion helpers' PASSING directions ride here).
# ---------------------------------------------------------------------------


class GraphQLTestCaseEndToEndTests(GraphQLTestCase):
    """``self.query(...)`` + both helpers + the per-call rung, end to end."""

    @override
    def setUp(self) -> None:
        super().setUp()
        seed_data(1)

    def test_seeded_query_via_self_client_passes_no_errors(self) -> None:
        res = self.query(
            "query Items { allItems(first: 1) { edges { node { name } } } }",
            operation_name="Items",
        )
        self.assertResponseNoErrors(res)
        assert res.data is not None
        assert len(json_list(res.data, "allItems", "edges")) == 1

    def test_invalid_query_returns_instead_of_raising_then_has_errors(self) -> None:
        # The mixin's flipped ``assert_no_errors=False`` default (graphene
        # parity): the errors response RETURNS for the helper to assert on.
        res = self.query("{ nope }")
        self.assertResponseHasErrors(res)
        assert res.data is None

    @override_settings(ROOT_URLCONF=__name__)
    def test_per_call_url_routes_to_the_probe_endpoint(self) -> None:
        # Rung 1 end-to-end: a positive hit on the real schema view mounted at
        # the probe URLconf's ``/alt/``, not an exception shape. The marker
        # header is what makes the routing observable - ``/graphql/`` answers
        # under this URLconf too, so a clean response alone would not say which
        # endpoint served it.
        res = self.query(
            "query Items { allItems(first: 1) { edges { node { name } } } }",
            url="/alt/",
        )
        self.assertResponseNoErrors(res)
        assert res.data is not None
        assert res.data["allItems"]["edges"]
        assert res.response[_PROBE_MARKER_HEADER] == _PROBE_MARKER_VALUE


@override_settings(ROOT_URLCONF=__name__)
class GraphQLTestCaseClassAttrEndpointTests(GraphQLTestCase):
    """The ``GRAPHQL_URL`` rung: the subclass pins its endpoint by assignment."""

    GRAPHQL_URL: str | None = "/alt/"

    @override
    def setUp(self) -> None:
        super().setUp()
        seed_data(1)

    def test_class_attr_endpoint_hits_the_real_view(self) -> None:
        # Rung 3: the positive hit plus the marker header, which is what
        # distinguishes the class attribute having routed the request to
        # ``/alt/`` from a fall-back to ``/graphql/`` under the same URLconf.
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }")
        self.assertResponseNoErrors(res)
        assert res.data is not None
        assert res.data["allItems"]["edges"]
        assert res.response[_PROBE_MARKER_HEADER] == _PROBE_MARKER_VALUE


class GraphQLTransactionTestCaseSmokeTests(GraphQLTransactionTestCase):
    """The ``(Mixin, TransactionTestCase)`` combination is wired end to end."""

    @override
    def setUp(self) -> None:
        super().setUp()
        seed_data(1)

    def test_one_clean_seeded_query_round_trips(self) -> None:
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }")
        self.assertResponseNoErrors(res)
        assert res.data is not None
        assert res.data["allItems"]["edges"]
