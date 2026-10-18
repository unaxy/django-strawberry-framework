"""Optimizer tests for Relay GlobalID projection when the pk attname is not ``id``.

The default-pk half is live at
``examples/fakeshop/test_query/test_products_visibility_api.py::test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids``
and
``examples/fakeshop/test_query/test_products_visibility_api.py::test_relay_id_and_name_selection_is_clean_under_strictness_raise_over_http``.
The custom-attname half is carried by ``apps/library/models.py::PatronProfile``,
whose primary key is the one-to-one key to the patron it extends, so the column
an id projection must load is ``patron_id``.
"""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
import pytest_django
import strawberry
from apps.library.models import Patron, PatronProfile
from django.db.models import QuerySet
from strawberry import relay

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.optimizer._context import DST_OPTIMIZER_PLAN
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from tests._idioms import is_object_dict, is_object_list, saved_pk


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db(transaction=True)
def test_relay_id_with_custom_pk_attname_avoids_lazy_load(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """A Relay type whose pk attname is not ``id`` answers ``{ id postalCode }`` in one query.

    The walker resolves the configured ``id_attr``, projects the real pk column
    into ``only()``, and ``_resolve_id_default`` reads the loaded value from
    ``root.__dict__`` instead of falling back to ``getattr`` (spec-015 Decision
    7).
    """
    patron = Patron.objects.create(name="Ada")
    PatronProfile.objects.create(patron=patron, postal_code="EC1")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("name",)

    assert registry.get(Patron) is PatronType

    class PatronProfileNode(DjangoType):
        class Meta:
            model = PatronProfile
            fields = ("patron", "postal_code")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        def _all_profiles(self) -> QuerySet[PatronProfile]:
            return PatronProfile.objects.all()

        all_profiles: QuerySet[PatronProfile] = strawberry.field(
            resolver=_all_profiles,
            graphql_type=list[PatronProfileNode],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allProfiles { id postalCode } }", context_value=ctx)

    assert result.errors is None
    plan = require_instance(read_attr(ctx, DST_OPTIMIZER_PLAN), OptimizationPlan)
    assert "patron_id" in plan.only_fields
    assert "id" not in plan.only_fields
    assert result.data is not None
    assert result.data == {
        "allProfiles": [{"id": result.data["allProfiles"][0]["id"], "postalCode": "EC1"}],
    }
    data: dict[str, object] = result.data
    profiles = data["allProfiles"]
    assert is_object_list(profiles)
    profile = profiles[0]
    assert is_object_dict(profile)
    profile_id = profile["id"]
    assert isinstance(profile_id, str)
    node_id = relay.GlobalID.from_id(profile_id)
    assert node_id.type_name == PatronProfile._meta.label_lower
    assert node_id.node_id == str(saved_pk(patron))
