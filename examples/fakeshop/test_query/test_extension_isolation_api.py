"""Live GraphQL HTTP tests for what one operation's extensions may be answered from.

Two claims a package-only schema cannot make, each reached from a real request:

- a schema whose factory entry returns an enforcement extension serves the
  request as an ordinary entry: the schema's own policies still bound and mask
  it, and the entry's own narrower policy configures nothing;
- the optimizer entry every deployment is documented to write - one module-level
  singleton behind a factory - keeps its published plan on the request it
  belongs to when a consumer extension runs an operation of its own.

The mechanics of the runner's bindings are pinned in ``tests/test_schema.py``
and ``tests/extensions/test_operation_state.py``. What this module owns is the
consumer-visible outcome, because a response reaching a client is something only
a request has.
"""

from collections.abc import Callable, Iterator
from functools import wraps

import pytest
import strawberry
from apps.products import schema as products_schema
from apps.products.services import seed_data
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.urls import include, path
from graphql_client import json_at, json_list, json_object, read_attr
from strawberry.extensions.base_extension import SchemaExtension
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    ResourcePolicy,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.error_policy import DEFAULT_ERROR_POLICY
from django_strawberry_framework.extensions import DjangoResourcePolicyExtension
from django_strawberry_framework.optimizer._context import (
    DST_OPTIMIZER_KEYS,
    get_context_value,
)
from django_strawberry_framework.resource_policy import DEFAULT_RESOURCE_POLICY
from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.urls(__name__)


def _narrow_resource_factory() -> DjangoResourcePolicyExtension:
    """A factory returning a resource-policy extension whose own policy is narrower."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=1))


@strawberry.type
class _ResourceQuery:
    """A scalar and a failing field for the authority-factory schema to serve."""

    @strawberry.field
    def hello(self) -> str:
        return "hi"

    @strawberry.field
    def fail(self) -> str:
        raise RuntimeError(_SENSITIVE)


#: What the failing field raises; a masked response never carries it.
_SENSITIVE = "internal tenant secret /srv/private/tenant-42.key"


class _Nester(SchemaExtension):
    """A consumer extension that runs one operation of its own at teardown.

    Its own operation begins after every optimizer hook of the request's
    operation has returned, and reports what the request's context object
    carried either side of it.
    """

    def __init__(self) -> None:
        super().__init__()
        self.ran = False
        self.published: list[dict[str, object]] = []

    @override
    def on_operation(self) -> Iterator[None]:
        """Run the inner operation once the outer operation's hooks are done."""
        yield
        if self.ran:
            return
        self.ran = True
        context = read_attr(self.execution_context, "context")
        self.published.append(_published(context))
        self.execution_context.schema.execute_sync(
            "{ allItems(first: 2) { edges { node { name category { id } } } } }",
            context_value=context,
        )
        self.published.append(_published(context))

    @override
    def get_results(self) -> dict[str, object]:
        """Report the comparison where a client can read it."""
        if len(self.published) != 2:
            return {}
        before, after = self.published
        return {
            "nesting": {
                "changed": sorted(key for key in before if before[key] is not after[key]),
                "planPublished": before["dst_optimizer_plan"] is not None,
            },
        }


def _published(context: object) -> dict[str, object]:
    """Every optimizer stash currently readable off a request context object."""
    return {key: get_context_value(context, key) for key in DST_OPTIMIZER_KEYS}


def _fresh_view(build: Callable[[], DjangoSchema]) -> Callable[..., HttpResponseBase]:
    """Mount the package's synchronous view over a schema built per request.

    The optimizer row needs the project's own generated types, which the
    acceptance fixtures rebuild per test; what it deliberately keeps across
    requests is the module-level optimizer, which is the shipped spelling.
    """

    @wraps(DjangoGraphQLView.as_view())
    def view(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponseBase:
        built = DjangoGraphQLView.as_view(schema=build())
        return built(request, *args, **kwargs)

    return view


def _nesting_schema() -> DjangoSchema:
    """The shipped optimizer spelling, with a consumer extension beside it."""
    finalize_django_types()
    return DjangoSchema(
        query=products_schema.Query,
        config=strawberry_config(),
        extensions=[lambda: _OPTIMIZER, lambda: _NESTER],
    )


#: The documented consumer wiring: one module-level optimizer behind a factory,
#: so its plan cache is shared across requests while its state is not.
_OPTIMIZER = DjangoOptimizerExtension()
_NESTER = _Nester()


def _authority_factory_schema() -> DjangoSchema:
    """A schema whose one entry is a factory returning an enforcement extension."""
    return DjangoSchema(query=_ResourceQuery, extensions=[_narrow_resource_factory])


urlpatterns = [
    path("", include("config.urls")),
    path("iso-nesting/", _fresh_view(_nesting_schema)),
    path("iso-chain/", _fresh_view(_authority_factory_schema)),
]


@pytest.mark.django_db
def test_an_operation_a_consumer_extension_starts_leaves_the_request_its_optimizer_plan() -> None:
    """The shipped singleton, through the project's own types, over a real request.

    The optimizer publishes its plan, elisions and lookup paths on the request's
    context object as introspection for whoever holds that request. A consumer
    extension's own operation runs inside the same request and shares that
    object, so what it must not do is clear it or publish its own values there.
    """
    seed_data(2)
    _NESTER.ran = False
    _NESTER.published.clear()
    client = TestClient(path="/iso-nesting/")

    response = client.query(
        "{ allItems(first: 2) { edges { node { name category { name } } } } }",
    )

    assert response.data is not None
    edges = json_list(response.data, "allItems", "edges")
    assert edges, response.data
    assert all(json_at(edge, "node", "category", "name") for edge in edges)
    assert response.extensions is not None
    nesting = json_object(response.extensions, "nesting")
    assert nesting["planPublished"] is True
    assert nesting["changed"] == []


def test_a_factory_returning_an_authority_is_an_ordinary_entry_on_the_request() -> None:
    """The factory's instance configures nothing; the schema's own policies govern.

    The factory's ``max_aliases=1`` would refuse two aliases, yet the request is
    served; the schema's default bound still refuses one alias past its ceiling,
    and its default error policy still masks a resolver failure.
    """
    client = TestClient(path="/iso-chain/")

    served = client.query("{ a: hello b: hello }")
    assert served.data == {"a": "hi", "b": "hi"}

    over = DEFAULT_RESOURCE_POLICY.max_aliases + 1
    refused = client.query(
        "{ " + " ".join(f"a{index}: hello" for index in range(over)) + " }",
        assert_no_errors=False,
    )
    assert refused.errors is not None
    assert len(refused.errors) == 1, refused.errors
    refusal = refused.errors[0]
    assert json_at(refusal, "extensions", "code") == "RESOURCE_LIMIT_EXCEEDED", refusal
    assert "alias" in str(refusal.get("message")), refusal

    masked = client.query("{ fail }", assert_no_errors=False)
    assert masked.errors is not None
    assert len(masked.errors) == 1, masked.errors
    assert masked.errors[0].get("message") == DEFAULT_ERROR_POLICY.message, masked.errors
    assert _SENSITIVE not in str(masked.errors), masked.errors
