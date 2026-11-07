"""A declared filter whose ``lookup_expr`` crosses a relation answers as its joined spelling.

``ListFilter(field_name="shelf", lookup_expr="tier__in")`` is Django's ``shelf__tier__in``,
and it answers as ``field_name="shelf__tier", lookup_expr="in"`` answers on every read
the package makes: its input keeps the declared token (``tierIn``) typed by the column
the path reaches, a value that column cannot hold is refused, each crossed hop's
target type scopes the rows the leaf compares, the crossed hop's target set fires the
gate of the column compared, and a to-many crossing answers valid input. Book rows are
plain; separate target types hide a ``secret`` shelf and a ``restricted`` branch from
anonymous viewers and show both to staff.
"""

from collections.abc import Iterator
from functools import wraps

import pytest
import strawberry
from apps.library import models
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import Client, override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter
from graphql_client import JSONObject, graphql_payload, json_list, json_object, json_str
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}

#: The ``check_<name>_permission`` gates the crossed hop's target set fired, in order.
_GATES: list[str] = []


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-crossing-lookups/", _graphql_view)]


def _is_staff(info: strawberry.Info[object, object]) -> bool:
    # A raw ``FilterSet(data=...)`` scopes its hops with no ``info`` at all.
    context = getattr(info, "context", None)
    user = getattr(getattr(context, "request", None), "user", None)
    return bool(getattr(user, "is_staff", False))


class _GatedShelfFilter(FilterSet):
    """The crossed hop's target set; each gate records its column and admits."""

    class Meta:
        model = models.Shelf
        fields = {"tier": ["in"]}

    def check_tier_permission(self, request: object) -> None:
        del request
        _GATES.append("tier")

    def check_id_permission(self, request: object) -> None:
        del request
        _GATES.append("id")


class _CrossingBookFilter(FilterSet):
    """Book leaves crossing ``shelf``, each beside the spelling naming the path in full."""

    shelf = RelatedFilter(_GatedShelfFilter, field_name="shelf")
    shelf_tiers = ListFilter(field_name="shelf", lookup_expr="tier__in")
    control_tiers = ListFilter(field_name="shelf__tier", lookup_expr="in")
    branch_named = CharFilter(field_name="shelf", lookup_expr="branch__name")
    branch_missing = BooleanFilter(field_name="shelf", lookup_expr="branch__isnull")
    control_branch_missing = BooleanFilter(field_name="shelf__branch", lookup_expr="isnull")

    class Meta:
        model = models.Book
        fields = ()


class _CrossingBranchFilter(FilterSet):
    """A Branch leaf crossing the to-many ``shelves``."""

    shelf_tiers = ListFilter(field_name="shelves", lookup_expr="tier__in")

    class Meta:
        model = models.Branch
        fields = ()


class _LoggedCharFilter(CharFilter):
    """A ``CharFilter`` whose class-level ``filter`` override delegates to django-filter's."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return super().filter(qs, value)


class _LoggedListFilter(ListFilter):
    """A ``ListFilter`` whose class-level ``filter`` override delegates to the package's."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return super().filter(qs, value)


class _RawBookFilter(FilterSet):
    """A raw-form Book set crossing ``shelf`` through a delegating override."""

    branch_named = _LoggedCharFilter(field_name="shelf", lookup_expr="branch__name")

    class Meta:
        model = models.Book
        fields = ()


class _RawBranchFilter(FilterSet):
    """A raw-form Branch set crossing the to-many ``shelves`` through a delegating override."""

    shelf_tiers = _LoggedListFilter(field_name="shelves", lookup_expr="tier__in")

    class Meta:
        model = models.Branch
        fields = ()


def _raw_rows(
    filterset_class: type[FilterSet],
    queryset: QuerySet[Model],
    query: str,
) -> list[str]:
    """Run ``query`` as raw form data on a first instance of ``filterset_class``; its rows.

    No request is handed over: a raw construction scopes every hop as an anonymous viewer.
    """
    filterset = filterset_class(data=QueryDict(query), queryset=queryset)
    assert filterset.is_valid(), filterset.errors
    matched: QuerySet[Model] = filterset.qs
    return sorted(str(row) for row in matched)


def _schema() -> DjangoSchema:
    class VisibleBranch(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = _CrossingBranchFilter

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Branch],
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Branch]:
            return queryset if _is_staff(info) else queryset.exclude(city="restricted")

    class VisibleShelf(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Shelf],
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Shelf]:
            return queryset if _is_staff(info) else queryset.exclude(topic="secret")

    class PlainBook(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            filterset_class = _CrossingBookFilter

    @strawberry.type
    class Query:
        books: DjangoConnection[PlainBook] = DjangoConnectionField(PlainBook)
        branches: DjangoConnection[VisibleBranch] = DjangoConnectionField(VisibleBranch)
        shelves: DjangoConnection[VisibleShelf] = DjangoConnectionField(VisibleShelf)

        @strawberry.field
        def raw_books(self, query: str) -> list[str]:
            del self
            return _raw_rows(_RawBookFilter, models.Book.objects.order_by("pk"), query)

        @strawberry.field
        def raw_branches(self, query: str) -> list[str]:
            del self
            return _raw_rows(_RawBranchFilter, models.Branch.objects.order_by("pk"), query)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _world() -> None:
    """One open branch with a visible upper and a secret lower shelf; one restricted middle shelf.

    No shelf's tier equals its key, so a tier compared as a key answers other rows.
    """
    open_branch = models.Branch.objects.create(name="open")
    restricted = models.Branch.objects.create(name="rest", city="restricted")
    visible = models.Shelf.objects.create(
        branch=open_branch,
        code="V",
        tier=models.Shelf.Tier.UPPER,
    )
    secret = models.Shelf.objects.create(
        branch=open_branch,
        code="S",
        topic="secret",
        tier=models.Shelf.Tier.LOWER,
    )
    held = models.Shelf.objects.create(
        branch=restricted,
        code="R",
        tier=models.Shelf.Tier.MIDDLE,
    )
    for shelf in (visible, secret, held):
        assert shelf.pk != shelf.tier
    for shelf, title in ((visible, "on-visible"), (secret, "on-secret"), (held, "on-restricted")):
        models.Book.objects.create(shelf=shelf, title=title)


@pytest.fixture
def staff() -> Iterator[Client]:
    """A client signed in as a staff user, who sees every shelf and branch."""
    create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))
    yield client
    client.logout()


def _post(
    schema: DjangoSchema,
    query: str,
    variables: JSONObject,
    client: Client,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                query,
                client=client,
                variables=variables,
                url="/graphql-crossing-lookups/",
            )
    finally:
        _CURRENT["schema"] = None


def _filter_type(schema: DjangoSchema, root: str) -> str:
    """Return the name of the ``filter`` argument's input type on the ``root`` connection."""
    result = schema.execute_sync(
        "{ __schema { queryType { fields { name args { name type { name } } } } } }",
    )
    assert result.errors is None, result.errors
    fields = json_list({"data": result.data}, "data", "__schema", "queryType", "fields")
    field = next(item for item in fields if json_str(item, "name") == root)
    argument = next(
        item for item in json_list(field, "args") if json_str(item, "name") == "filter"
    )
    return json_str(argument, "type", "name")


def _input_fields(schema: DjangoSchema, type_name: str) -> dict[str, JSONObject]:
    """Return each field of input type ``type_name`` by name, its type unwrapped two levels."""
    result = schema.execute_sync(
        "query($name: String!) { __type(name: $name) { inputFields { name type { kind name "
        "ofType { kind name ofType { kind name } } } } } }",
        variable_values={"name": type_name},
    )
    assert result.errors is None, result.errors
    fields = json_list({"data": result.data}, "data", "__type", "inputFields")
    return {json_str(item, "name"): json_object(item, "type") for item in fields}


def _rows(
    schema: DjangoSchema,
    root: str,
    label: str,
    where: JSONObject,
    client: Client,
) -> JSONObject:
    """Post ``where`` as the ``root`` connection's ``filter``; answer its labels or errors."""
    payload = _post(
        schema,
        f"query($where: {_filter_type(schema, root)}) "
        f"{{ {root}(filter: $where) {{ edges {{ node {{ {label} }} }} }} }}",
        {"where": where},
        client,
    )
    if "errors" in payload:
        return {"errors": [json_str(error, "message") for error in json_list(payload, "errors")]}
    edges = json_list(payload, "data", root, "edges")
    return {"rows": sorted(json_str(edge, "node", label) for edge in edges)}


@pytest.mark.django_db
def test_the_crossing_input_keeps_its_token_typed_as_the_crossed_column() -> None:
    """``tierIn`` is published as the declared token, its element the ``tier`` column's enum."""
    schema = _schema()
    fields = _input_fields(schema, _filter_type(schema, "books"))
    crossing = _input_fields(schema, json_str(fields["shelfTiers"], "name"))
    control = _input_fields(schema, json_str(fields["controlTiers"], "name"))

    assert list(crossing) == ["tierIn"]
    assert crossing["tierIn"] == control["in"]
    assert json_str(crossing["tierIn"], "ofType", "ofType", "name") == json_str(
        control["in"],
        "ofType",
        "ofType",
        "name",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["shelfTiers", "controlTiers"])
def test_a_value_the_crossed_column_cannot_hold_is_refused(key: str) -> None:
    """A member the ``tier`` column's enum does not name is a variable error, never a 500."""
    _world()
    lookup = "tierIn" if key == "shelfTiers" else "in"

    answer = _rows(_schema(), "books", "title", {key: {lookup: ["junk"]}}, Client())

    refusal = "Value 'junk' does not exist in 'VisibleBranchTierEnum' enum."
    assert answer == {
        "errors": [f"Variable '$where' has invalid value at .{key}.{lookup}[0]: {refusal}"],
    }


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["shelfTiers", "controlTiers"])
@pytest.mark.parametrize(
    ("member", "anonymous", "as_staff"),
    [
        pytest.param("MEMBER_3", ["on-visible"], ["on-visible"], id="visible-shelf"),
        pytest.param("MEMBER_1", [], ["on-secret"], id="hidden-shelf"),
    ],
)
def test_a_crossing_tier_matches_only_through_a_shelf_the_viewer_sees(
    key: str,
    member: str,
    anonymous: list[str],
    as_staff: list[str],
    staff: Client,
) -> None:
    """A hidden shelf's tier matches nothing for an anonymous viewer and its book for staff."""
    _world()
    schema = _schema()
    lookup = "tierIn" if key == "shelfTiers" else "in"
    where: JSONObject = {key: {lookup: [member]}}

    assert _rows(schema, "books", "title", where, Client()) == {"rows": anonymous}
    assert _rows(schema, "books", "title", where, staff) == {"rows": as_staff}


@pytest.mark.django_db
def test_a_crossing_branch_name_matches_nothing_through_a_hidden_branch(staff: Client) -> None:
    """``shelf`` + ``branch__name`` walks the ``branch`` hop: a restricted branch stays unseen."""
    _world()
    schema = _schema()
    where: JSONObject = {"branchNamed": {"branchName": "rest"}}

    assert _rows(schema, "books", "title", where, Client()) == {"rows": []}
    assert _rows(schema, "books", "title", where, staff) == {"rows": ["on-restricted"]}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("member", "anonymous", "as_staff"),
    [
        pytest.param("MEMBER_3", ["open"], ["open"], id="visible-shelf"),
        pytest.param("MEMBER_1", [], ["open"], id="hidden-shelf"),
        pytest.param("MEMBER_2", [], ["rest"], id="restricted-branch"),
    ],
)
def test_a_to_many_crossing_answers_valid_input(
    member: str,
    anonymous: list[str],
    as_staff: list[str],
    staff: Client,
) -> None:
    """``shelves`` + ``tier__in`` compares ``tier`` over the shelves each viewer sees."""
    _world()
    schema = _schema()
    where: JSONObject = {"shelfTiers": {"tierIn": [member]}}

    assert _rows(schema, "branches", "name", where, Client()) == {"rows": anonymous}
    assert _rows(schema, "branches", "name", where, staff) == {"rows": as_staff}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("key", "lookup"),
    [("shelfTiers", "tierIn"), ("controlTiers", "in")],
)
def test_the_crossed_hop_fires_the_gate_of_the_column_it_compares(key: str, lookup: str) -> None:
    """The crossed ``shelf`` hop's target set fires ``check_tier_permission``, never the key's."""
    _world()
    _GATES.clear()

    answer = _rows(_schema(), "books", "title", {key: {lookup: ["MEMBER_3"]}}, Client())

    assert answer == {"rows": ["on-visible"]}
    assert _GATES == ["tier"]


@pytest.mark.django_db
@pytest.mark.parametrize("missing", [True, False])
def test_a_crossing_null_test_answers_as_its_joined_spelling(
    *,
    missing: bool,
    staff: Client,
) -> None:
    """``shelf`` + ``branch__isnull`` is the null test ``shelf__branch`` + ``isnull`` is.

    ``True`` also keeps a book reaching no visible branch (a hidden shelf, a restricted
    branch) for an anonymous viewer, as the flat null test over visible rows does.
    """
    _world()
    schema = _schema()
    fields = _input_fields(schema, _filter_type(schema, "books"))
    crossing_key = next(iter(_input_fields(schema, json_str(fields["branchMissing"], "name"))))
    control_key = next(
        iter(_input_fields(schema, json_str(fields["controlBranchMissing"], "name"))),
    )
    crossing: JSONObject = {"branchMissing": {crossing_key: missing}}
    control: JSONObject = {"controlBranchMissing": {control_key: missing}}

    for client in (Client(), staff):
        answer = _rows(schema, "books", "title", crossing, client)
        assert answer == _rows(schema, "books", "title", control, client)
        assert "errors" not in answer, answer
    assert _rows(schema, "books", "title", crossing, Client()) != _rows(
        schema,
        "books",
        "title",
        crossing,
        staff,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("root", "query", "rows"),
    [
        pytest.param("rawBooks", "branch_named=rest", [], id="restricted-branch-name"),
        pytest.param("rawBooks", "branch_named=open", ["on-visible"], id="open-name"),
        pytest.param("rawBranches", "shelf_tiers=3", ["open"], id="to-many-visible-shelf"),
        pytest.param("rawBranches", "shelf_tiers=1", [], id="to-many-hidden-shelf"),
        pytest.param("rawBranches", "shelf_tiers=2", ["rest"], id="to-many-visible-shelf-root"),
    ],
)
def test_a_delegating_override_crossing_a_relation_walks_it_on_raw_forms(
    root: str,
    query: str,
    rows: list[str],
) -> None:
    """A class-level ``filter`` override delegating to the shipped one walks the crossed hops.

    The first raw instance of a set holding it (``FilterSet(data=...)``, as
    ``DjangoFilterBackend`` builds one) compares ``branch__name`` only through shelves and
    branches an anonymous viewer sees, and a to-many crossing answers valid input on the
    visible shelves of the roots it is handed, as ``field_name="shelf__branch"`` /
    ``"shelves__tier"`` would.
    """
    _world()
    payload = _post(
        _schema(),
        f"query($q: String!) {{ {root}(query: $q) }}",
        {"q": query},
        Client(),
    )

    assert payload == {"data": {root: rows}}, payload
