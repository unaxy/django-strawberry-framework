"""OptimizationPlan tests for lifecycle, ORM reconciliation, paths, ordering, and window pagination.

The plan dataclass, ``apply``, path helpers, and window-pagination functions are
not GraphQL fields. Consumer-visible SQL is
``examples/fakeshop/test_query/test_library_api.py`` and
``examples/fakeshop/test_query/test_single_parent_fastpath_api.py``.
"""

import sys
from collections.abc import Callable
from types import SimpleNamespace

import pytest
from apps.kanban.models import Card, Status
from apps.library.models import Book, Issue, ReadingList, ReadingListEntry
from apps.products.models import Category, Entry, Item, Property
from apps.scalars.models import NullableScalarSpecimen
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, FilteredRelation, Model, OrderBy, Prefetch, Q, QuerySet
from django.db.models.expressions import Combinable
from django.db.models.functions import Lower
from django.test.utils import isolate_apps
from typing_extensions import override

from django_strawberry_framework.connection import _ends_in_unique_column
from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.keyset import (
    CursorState,
    declared_cursor_state_for_definition,
    order_fingerprint,
)
from django_strawberry_framework.optimizer.plans import (
    _MAX_PATH_DEPTH,
    WINDOW_ROW_NUMBER,
    WINDOW_ROW_NUMBER_REVERSED,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
    PlannedWindow,
    PrefetchSeal,
    _consumer_prefetch_lookups,
    _consumer_projection,
    _flatten_select_related,
    _IndexedList,
    _loads,
    _reverse_order_by,
    _select_mask,
    _select_path_missing_connectors,
    append_prefetch_unique,
    append_unique,
    append_unique_many,
    apply_projection,
    apply_window_pagination,
    deterministic_order,
    diff_plan_for_queryset,
    effective_connection_order,
    effective_cursor_state,
    ends_in_unique_column,
    local_cursor_attnames,
    lookup_paths,
    merged_projection,
    normalize_order_direction,
    order_entry_has_explicit_nulls,
    resolver_key,
    runtime_path_from_path,
    seals_consumer_prefetch,
)
from django_strawberry_framework.utils._queryset_private import (
    queryset_prefetch_lookups,
)
from django_strawberry_framework.utils.connections import ConnectionWindowBounds
from tests._definition import make_definition
from tests.optimizer._spelling_models import SpBadge, SpCard, SpParent


class TestOptimizationPlanIsEmpty:
    """``is_empty`` returns ``True`` only when all plan directives are empty."""

    def test_empty_plan(self) -> None:
        plan = OptimizationPlan()
        assert plan.is_empty is True

    def test_non_empty_select_related(self) -> None:
        plan = OptimizationPlan(select_related=["category"])
        assert plan.is_empty is False

    def test_non_empty_prefetch_related(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"])
        assert plan.is_empty is False

    def test_non_empty_only_fields(self) -> None:
        plan = OptimizationPlan(only_fields=["name"])
        assert plan.is_empty is False

    def test_non_empty_fk_id_elisions(self) -> None:
        plan = OptimizationPlan(fk_id_elisions=["ItemType.category@allItems.category"])
        assert plan.is_empty is False

    def test_non_empty_planned_resolver_keys(self) -> None:
        plan = OptimizationPlan(planned_resolver_keys=["ItemType.category@allItems.category"])
        assert plan.is_empty is False

    def test_cacheable_flag_does_not_affect_empty_state(self) -> None:
        plan = OptimizationPlan(cacheable=False)
        assert plan.is_empty is True


class TestLookupPaths:
    """``lookup_paths`` flattens Django lookup paths for debugging/B8."""

    def test_flatten_select_related_paths(self) -> None:
        plan = OptimizationPlan(select_related=["item", "item__category"])
        assert lookup_paths(plan) == {"item", "item__category"}

    def test_flatten_plain_prefetch_string(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"])
        assert lookup_paths(plan) == {"items"}

    def test_flatten_nested_prefetch_objects_recursively(self) -> None:
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        assert lookup_paths(plan) == {"items", "items__entries"}

    def test_does_not_include_resolver_keys(self) -> None:
        plan = OptimizationPlan(
            select_related=["category"],
            planned_resolver_keys=["ItemType.category@allItems.category"],
            fk_id_elisions=["ItemType.owner@allItems.owner"],
        )
        assert lookup_paths(plan) == {"category"}

    def test_ignores_unknown_prefetch_like_entries(self) -> None:
        # Deliberately impossible for generated plans; covers defensive flattening.
        # basedpyright: the non-lookup prefetch entry is the hostile input under test;
        # OptimizationPlan types prefetch_related as Sequence[PrefetchLookup]
        plan = OptimizationPlan(prefetch_related=[object()])  # pyright: ignore[reportArgumentType]
        assert lookup_paths(plan) == set()

    def test_uses_finalized_lookup_paths_after_finalize(self) -> None:
        """After ``finalize()``, ``lookup_paths`` reuses the frozen path set."""
        plan = OptimizationPlan(
            select_related=["category"],
            prefetch_related=["items"],
        ).finalize()
        # The frozen set is populated and is what ``lookup_paths`` returns.
        assert plan.finalized_lookup_paths == frozenset({"category", "items"})
        result = lookup_paths(plan)
        assert result == {"category", "items"}
        # A fresh ``set`` copy, not the frozenset itself.
        assert isinstance(result, set)
        assert not isinstance(result, frozenset)


def test_resolver_key_includes_parent_type_and_runtime_path() -> None:
    class ItemType:
        pass

    assert (
        resolver_key(ItemType, "category", ("allItems", "category"))
        == "ItemType.category@allItems.category"
    )


class TestOptimizationPlanApply:
    """``apply`` mutates a queryset with the collected directives."""

    def test_apply_empty_plan_returns_queryset_unchanged(self) -> None:
        plan = OptimizationPlan()
        qs = Category.objects.all()
        result = plan.apply(qs)
        # An empty plan should not add select_related or prefetch_related.
        assert result.query.select_related is False
        assert queryset_prefetch_lookups(result) == ()

    def test_apply_select_related(self) -> None:
        plan = OptimizationPlan(select_related=["category"])
        # Use a model that has a FK - Item.category.

        qs = Item.objects.all()
        result = plan.apply(qs)
        assert isinstance(result.query.select_related, dict)
        assert "category" in result.query.select_related

    def test_apply_prefetch_related(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.all()
        result = plan.apply(qs)
        assert "items" in queryset_prefetch_lookups(result)

    def test_apply_only_fields(self) -> None:
        plan = OptimizationPlan(only_fields=["name"])
        qs = Category.objects.all()
        result = plan.apply(qs)
        fields, is_deferred = result.query.deferred_loading
        assert fields == {"name"}
        assert is_deferred is False

    def test_apply_releases_the_query_name_join_of_a_relation_it_prefetches(self) -> None:
        """A consumer ``select_related("cards")`` yields to the planned ``Prefetch("card")``.

        ``SpParent.card`` is queried as ``cards``: the JOIN would cache the
        relation and Django would skip the prefetch, so it is released; the
        consumer's ``badge`` JOIN is on another relation and stays.
        """
        plan = OptimizationPlan(prefetch_related=[Prefetch("card", queryset=SpCard.objects.all())])
        qs = SpParent.objects.select_related("cards", "badge")

        result = plan.apply(qs)

        assert result.query.select_related == {"badge": {}}
        (lookup,) = queryset_prefetch_lookups(result)
        assert isinstance(lookup, Prefetch)
        assert lookup.prefetch_to == "card"


class TestOptimizationPlanMerge:
    """Construction-time merge operations commit complete accepted plans."""

    def test_full_merge_covers_every_directive_and_metadata_field_once(self) -> None:
        existing_seal = PrefetchSeal(own_keys=("existing-key",), model=Item, seal=_seal_as_is)
        new_seal = PrefetchSeal(own_keys=("new-key",), model=Item, seal=_seal_as_is)
        target = OptimizationPlan(
            select_related=["category"],
            prefetch_related=["items"],
            only_fields=["name"],
            fk_id_elisions=["existing-elision"],
            planned_resolver_keys=["existing-key"],
            select_path_resolver_keys={"category": ("existing-key",)},
            prefetch_path_resolver_keys={"items": ("existing-key",)},
            prefetch_path_seals={"items": existing_seal},
        )
        source = OptimizationPlan(
            select_related=["category", "owner", "owner"],
            prefetch_related=["items", "properties", "properties"],
            only_fields=["name", "description", "description"],
            fk_id_elisions=["existing-elision", "new-elision", "new-elision"],
            planned_resolver_keys=["existing-key", "new-key", "new-key"],
            select_path_resolver_keys={"category": ("existing-key", "new-key", "new-key")},
            prefetch_path_resolver_keys={"items": ("existing-key", "new-key", "new-key")},
            prefetch_path_seals={"items": new_seal, "properties": new_seal},
            cacheable=False,
        )

        target.merge_from(source)

        assert target.select_related == ["category", "owner"]
        assert target.prefetch_related == ["items", "properties"]
        assert target.only_fields == ["name", "description"]
        assert target.fk_id_elisions == ["existing-elision", "new-elision"]
        assert target.planned_resolver_keys == ["existing-key", "new-key"]
        assert target.select_path_resolver_keys == {"category": ("existing-key", "new-key")}
        assert target.prefetch_path_resolver_keys == {
            "items": ("existing-key", "new-key"),
        }
        # The first seal recorded for a path is the one the plan keeps.
        assert target.prefetch_path_seals == {"items": existing_seal, "properties": new_seal}
        assert target.cacheable is False

    def test_metadata_merge_excludes_child_queryset_directives(self) -> None:
        target = OptimizationPlan()
        child = OptimizationPlan(
            select_related=["category"],
            prefetch_related=["entries"],
            only_fields=["name"],
            fk_id_elisions=["child-elision"],
            planned_resolver_keys=["child-key"],
            cacheable=False,
        )

        target.merge_metadata_from(child)

        assert target.select_related == []
        assert target.prefetch_related == []
        assert target.only_fields == []
        assert target.fk_id_elisions == ["child-elision"]
        assert target.planned_resolver_keys == ["child-key"]
        assert target.cacheable is False

    def test_merge_rejects_finalized_source_and_target(self) -> None:
        with pytest.raises(RuntimeError, match="construction-time"):
            OptimizationPlan().merge_from(OptimizationPlan().finalize())
        with pytest.raises(RuntimeError, match="construction-time"):
            OptimizationPlan().finalize().merge_from(OptimizationPlan())

    def test_merge_inventory_guard_reports_stale_classification(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            OptimizationPlan,
            "_FULL_MERGE_FIELDS",
            OptimizationPlan._FULL_MERGE_FIELDS | {"removed_field"},
        )

        with pytest.raises(RuntimeError, match=r"stale=\['removed_field'\]"):
            OptimizationPlan._assert_merge_field_inventory()

    def test_introduce_projection_is_a_construction_field_no_merge_carries(self) -> None:
        """The operation flag is set when a plan is built and never merged from another plan.

        Every plan of one walk is built with its parent's flag, so a merge has
        nothing to reconcile; the inventory guard classifies it on its own.
        """
        assert frozenset({"introduce_projection"}) == OptimizationPlan._CONSTRUCTION_FIELDS
        OptimizationPlan._assert_merge_field_inventory()
        target = OptimizationPlan(introduce_projection=False)
        target.merge_from(OptimizationPlan(only_fields=["name"]))
        target.merge_metadata_from(OptimizationPlan())
        assert target.introduce_projection is False

    def test_merge_inventory_guard_reports_an_unclassified_construction_field(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(OptimizationPlan, "_CONSTRUCTION_FIELDS", frozenset[str]())

        with pytest.raises(RuntimeError, match=r"unclassified=\['introduce_projection'\]"):
            OptimizationPlan._assert_merge_field_inventory()


class TestOptimizationPlanFinalize:
    """``finalize`` swaps mutable list fields for tuples so post-handoff mutation raises."""

    def test_finalize_returns_tuples_for_list_fields(self) -> None:
        plan = OptimizationPlan(
            select_related=["category"],
            prefetch_related=["items"],
            only_fields=["name"],
            fk_id_elisions=["ItemType.category@x"],
            planned_resolver_keys=["ItemType.entries@x"],
        )
        finalized = plan.finalize()
        assert isinstance(finalized.select_related, tuple)
        assert isinstance(finalized.prefetch_related, tuple)
        assert isinstance(finalized.only_fields, tuple)
        assert isinstance(finalized.fk_id_elisions, tuple)
        assert isinstance(finalized.planned_resolver_keys, tuple)

    def test_finalize_precomputes_context_metadata_frozensets(self) -> None:
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(
            select_related=["category"],
            prefetch_related=[outer],
            fk_id_elisions=["ItemType.category@allItems.category"],
            planned_resolver_keys=["ItemType.items@allItems.items"],
        )

        finalized = plan.finalize()

        assert finalized.finalized_fk_id_elisions == frozenset(
            {"ItemType.category@allItems.category"},
        )
        assert finalized.finalized_planned_resolver_keys == frozenset(
            {"ItemType.items@allItems.items"},
        )
        assert finalized.finalized_lookup_paths == frozenset(
            {"category", "items", "items__entries"},
        )

    def test_finalize_preserves_values_and_cacheable_flag(self) -> None:
        plan = OptimizationPlan(select_related=["a", "b"], cacheable=False)
        finalized = plan.finalize()
        assert finalized.select_related == ("a", "b")
        assert finalized.cacheable is False

    def test_finalize_blocks_post_handoff_append_on_cache_isolation(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"]).finalize()
        # Tuple has no ``append``; mutation attempts raise AttributeError
        # rather than silently poisoning the plan-cache entry for the
        # next request.
        assert isinstance(plan.prefetch_related, tuple)
        assert not hasattr(plan.prefetch_related, "append")

    def test_finalize_is_idempotent(self) -> None:
        plan = OptimizationPlan(select_related=["a"]).finalize()
        again = plan.finalize()
        assert again.select_related == ("a",)
        assert isinstance(again.select_related, tuple)

    def test_apply_works_on_finalized_plan(self) -> None:
        plan = OptimizationPlan(select_related=["category"]).finalize()
        qs = Item.objects.all()
        result = plan.apply(qs)
        assert isinstance(result.query.select_related, dict)
        assert "category" in result.query.select_related


class TestPlanHelperRelocations:
    """``append_unique`` / ``append_unique_many`` / ``append_prefetch_unique`` live with the plan shape."""

    def test_append_unique_skips_existing_value(self) -> None:
        values: list[str] = ["a"]
        append_unique(values, "a")
        append_unique(values, "b")
        assert values == ["a", "b"]

    def test_append_unique_many_iterates_tuple(self) -> None:
        values: list[str] = []
        append_unique_many(
            values,
            ("a", "b", "a"),
        )
        assert values == ["a", "b"]

    def test_append_unique_on_finalized_tuple_raises_for_a_missing_value(self) -> None:
        plan = OptimizationPlan(only_fields=["a"]).finalize()
        assert isinstance(plan.only_fields, tuple)
        append_unique(plan.only_fields, "a")
        assert plan.only_fields == ("a",)
        with pytest.raises(AttributeError, match="'tuple' object has no attribute 'append'"):
            append_unique(plan.only_fields, "b")
        assert plan.only_fields == ("a",)

    def test_append_prefetch_unique_on_finalized_tuple_raises_for_a_missing_path(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"]).finalize()
        assert isinstance(plan.prefetch_related, tuple)
        append_prefetch_unique(plan.prefetch_related, Prefetch("items"))
        assert plan.prefetch_related == ("items",)
        with pytest.raises(AttributeError, match="'tuple' object has no attribute 'append'"):
            append_prefetch_unique(plan.prefetch_related, Prefetch("other"))
        assert plan.prefetch_related == ("items",)

    def test_append_prefetch_unique_dedupes_by_lookup_path(self) -> None:
        first = Prefetch("items", queryset=Item.objects.all())
        second = Prefetch("items", queryset=Item.objects.filter(pk__gt=0))
        values: list[str | Prefetch[str]] = []
        append_prefetch_unique(values, first)
        append_prefetch_unique(values, second)
        assert values == [first]

    def test_append_prefetch_unique_keeps_distinct_to_attrs_on_one_lookup(self) -> None:
        """Two windows on ONE relation coexist when their ``to_attr``s differ.

        The divergent-alias per-key scheme attaches one ``Prefetch``
        per response key to the SAME lookup; Django's ``prefetch_to`` replaces
        the last path segment with ``to_attr``, so the ``_lookup_path`` dedupe
        keys them apart - both survive (and a true duplicate still dedupes).
        """
        first = Prefetch("items", queryset=Item.objects.all(), to_attr="_dst_items$a_connection")
        second = Prefetch("items", queryset=Item.objects.all(), to_attr="_dst_items$b_connection")
        duplicate = Prefetch(
            "items",
            queryset=Item.objects.filter(pk__gt=0),
            to_attr="_dst_items$a_connection",
        )
        values: list[str | Prefetch[str]] = []
        append_prefetch_unique(values, first)
        append_prefetch_unique(values, second)
        append_prefetch_unique(values, duplicate)
        assert values == [first, second]

    def test_plan_default_lists_use_indexed_append_unique(self) -> None:
        plan = OptimizationPlan()
        assert isinstance(plan.only_fields, _IndexedList)

        append_unique(plan.only_fields, "name")
        append_unique(plan.only_fields, "name")
        append_unique(plan.only_fields, "id")

        assert plan.only_fields == ["name", "id"]

    def test_plan_default_prefetch_list_indexes_by_lookup_path(self) -> None:
        first = Prefetch("items", queryset=Item.objects.all())
        second = Prefetch("items", queryset=Item.objects.filter(pk__gt=0))
        plan = OptimizationPlan()
        assert isinstance(plan.prefetch_related, _IndexedList)

        append_prefetch_unique(plan.prefetch_related, first)
        append_prefetch_unique(plan.prefetch_related, second)

        assert plan.prefetch_related == [first]


class TestIndexedList:
    """Direct coverage of ``_IndexedList`` mutators and the unhashable fallback."""

    def test_constructor_dedupes_initial_values(self) -> None:
        indexed = _IndexedList(["a", "b", "a"])
        assert indexed == ["a", "b"]

    def test_append_and_extend_keep_index_for_later_append_unique(self) -> None:
        indexed: _IndexedList[str] = _IndexedList()
        indexed.append("a")
        indexed.extend(["b", "c"])
        assert indexed == ["a", "b", "c"]
        # The sidecar index was maintained, so a later ``append_unique`` of an
        # already-present value is a no-op.
        indexed.append_unique("b")
        assert indexed == ["a", "b", "c"]

    def test_append_unique_falls_back_to_membership_for_unhashable_values(self) -> None:
        indexed: _IndexedList[list[str]] = _IndexedList()
        unhashable = ["nested"]
        # Unhashable key: the ``_seen`` probe raises ``TypeError`` and the
        # helper falls back to an ``in self`` membership scan. First insert
        # appends; the second is recognised as a duplicate and skipped.
        indexed.append_unique(unhashable)
        indexed.append_unique(unhashable)
        assert indexed == [["nested"]]


class TestFlattenSelectRelated:
    """``_flatten_select_related`` normalizes Django's three select_related shapes."""

    def test_false_returns_empty_set(self) -> None:
        assert _flatten_select_related(False) == set()  # noqa: FBT003 - the bool is the value under test

    def test_true_returns_empty_set_for_wildcard(self) -> None:
        # A wildcard ``select_related()`` cannot safely justify
        # dropping explicit optimizer entries because the wildcard only
        # follows non-null FKs.  Treat as no overlap.
        assert _flatten_select_related(True) == set()  # noqa: FBT003 - the bool is the value under test

    def test_dict_flattens_to_top_level_paths(self) -> None:
        assert _flatten_select_related({"category": {}}) == {"category"}

    def test_dict_flattens_nested_chains(self) -> None:
        assert _flatten_select_related({"category": {"parent": {}}}) == {
            "category",
            "category__parent",
        }

    def test_none_or_non_dict_returns_empty_set(self) -> None:
        assert _flatten_select_related(None) == set()
        assert _flatten_select_related("invalid") == set()
        assert _flatten_select_related(123) == set()
        assert _flatten_select_related([1, 2]) == set()


class TestConsumerPrefetchLookups:
    """``_consumer_prefetch_lookups`` reads attached lookups leniently.

    A real queryset contributes its ``prefetch_related`` lookups as a list;
    anything else contributes nothing, so a consumer-controlled
    ``Prefetch.queryset`` that is not a queryset reconciles to no lookups
    instead of raising. The queryset arm reads through the shared
    ``queryset_prefetch_lookups`` owner, which holds the one spelling of
    the Django-private attribute.
    """

    def test_attached_lookups_come_back_as_a_list(self) -> None:
        qs = Item.objects.prefetch_related("entries")
        assert _consumer_prefetch_lookups(qs) == ["entries"]

    def test_queryset_without_prefetches_gives_an_empty_list(self) -> None:
        assert _consumer_prefetch_lookups(Item.objects.all()) == []

    @pytest.mark.parametrize(
        "candidate",
        [
            object(),
            SimpleNamespace(),
            SimpleNamespace(_prefetch_related_lookups=None),
            SimpleNamespace(_prefetch_related_lookups=("entries",)),
        ],
        ids=[
            "plain-object",
            "bare-namespace",
            "none-valued-attribute",
            "populated-attribute-unread",
        ],
    )
    def test_non_queryset_inputs_give_an_empty_list(self, candidate: object) -> None:
        """Only a real queryset's lookups are returned.

        An unrelated object carrying an attribute of the same name is not
        a queryset, so its attribute stays unread and the input reconciles
        to no lookups instead of raising.
        """
        assert _consumer_prefetch_lookups(candidate) == []


class TestDiffPlanForQueryset:
    """``diff_plan_for_queryset`` reconciles plan vs. queryset without mutating the plan."""

    def test_returns_same_instances_when_nothing_to_drop(self) -> None:
        plan = OptimizationPlan(select_related=["category"], prefetch_related=["items"])
        qs = Category.objects.all()
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_qs is qs

    def test_drops_select_related_already_on_queryset(self) -> None:
        plan = OptimizationPlan(select_related=["category"])
        qs = Item.objects.select_related("category")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is not plan
        assert delta_plan.select_related == ()
        assert delta_qs is qs
        # Original plan is untouched - the plan cache reuses it across requests.
        assert plan.select_related == ["category"]

    def test_drops_chained_select_related(self) -> None:
        plan = OptimizationPlan(select_related=["item__category"])
        qs = Entry.objects.select_related("item__category")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.select_related == ()

    def test_wildcard_select_related_does_not_drop_explicit_entries(self) -> None:
        # A wildcard ``select_related()`` follows only non-null FKs; the
        # optimizer may name nullable FKs explicitly.  Treat the
        # wildcard as no overlap and pass entries through unchanged.  The
        # wildcard query state is set directly because that state, not the
        # call spelling that produces it, is the contract under test.
        plan = OptimizationPlan(select_related=["item", "property"])
        qs = Entry.objects.all()
        qs.query.select_related = True
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_plan.select_related == ["item", "property"]

    def test_drops_string_prefetch_already_on_queryset(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.prefetch_related("items")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
        assert plan.prefetch_related == ["items"]

    def test_consumer_prefetch_by_accessor_owns_the_query_name_join(self) -> None:
        """``Prefetch("card", queryset=...)`` owns the JOIN ``cards`` of the same relation.

        ``SpParent.card`` is queried as ``cards``. The JOIN, its key and the
        ``only()`` entries beneath it leave the plan; the JOIN planned through it
        becomes a prefetch lookup spelled in accessors (``card__parent``), and the
        JOIN of the unrelated ``badge`` stays.
        """
        plan = OptimizationPlan(
            select_related=["cards", "cards__parent", "badge"],
            only_fields=[
                "code",
                "cards__name",
                "cards__parent__code",
                "badge__name",
            ],
            planned_resolver_keys=["cards-key", "parent-key", "badge-key"],
            select_path_resolver_keys={
                "cards": ("cards-key",),
                "cards__parent": ("parent-key",),
                "badge": ("badge-key",),
            },
        )
        qs = SpParent.objects.prefetch_related(Prefetch("card", queryset=SpCard.objects.all()))

        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)

        assert delta_qs is qs
        assert delta_plan.select_related == ("badge",)
        assert delta_plan.prefetch_related == ("card__parent",)
        assert delta_plan.only_fields == ("code", "badge__name")
        assert delta_plan.planned_resolver_keys == ("parent-key", "badge-key")

    def test_consumer_prefetch_by_accessor_leaves_the_join_it_does_not_name(self) -> None:
        """The control: ``Prefetch("badge", queryset=...)`` owns ``badge`` and leaves ``cards``."""
        plan = OptimizationPlan(
            select_related=["cards", "badge"],
            only_fields=["cards__name", "badge__name"],
            planned_resolver_keys=["cards-key", "badge-key"],
            select_path_resolver_keys={"cards": ("cards-key",), "badge": ("badge-key",)},
        )
        qs = SpParent.objects.prefetch_related(Prefetch("badge", queryset=SpBadge.objects.all()))

        delta_plan, _ = diff_plan_for_queryset(plan, qs)

        assert delta_plan.select_related == ("cards",)
        assert delta_plan.only_fields == ("cards__name",)
        assert delta_plan.planned_resolver_keys == ("cards-key",)

    def test_consumer_join_by_query_name_keeps_its_prefetch_by_accessor(self) -> None:
        """The consumer's own JOIN ``cards`` caches ``card``, so its ``Prefetch("card")`` owns nothing."""
        plan = OptimizationPlan(
            select_related=["cards"],
            planned_resolver_keys=["cards-key"],
            select_path_resolver_keys={"cards": ("cards-key",)},
        )
        qs = SpParent.objects.select_related("cards").prefetch_related(
            Prefetch("card", queryset=SpCard.objects.all()),
        )

        delta_plan, _ = diff_plan_for_queryset(plan, qs)

        assert delta_plan.select_related == ()
        assert delta_plan.planned_resolver_keys == ("cards-key",)

    def test_consumer_prefetch_object_suppresses_plan_string(self) -> None:
        plan = OptimizationPlan(prefetch_related=["items"])
        qs = Category.objects.prefetch_related(Prefetch("items", queryset=Item.objects.all()))
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()

    def test_partial_overlap_keeps_remaining_entries(self) -> None:
        plan = OptimizationPlan(select_related=["item", "property"])
        qs = Entry.objects.select_related("item")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.select_related == ("property",)
        assert plan.select_related == ["item", "property"]

    def test_carries_over_metadata_fields(self) -> None:
        plan = OptimizationPlan(
            select_related=["category"],
            only_fields=["name"],
            fk_id_elisions=["ItemType.category@allItems.category"],
            planned_resolver_keys=["ItemType.category@allItems.category"],
            cacheable=False,
        ).finalize()
        qs = Item.objects.select_related("category")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan.only_fields == ("name",)
        assert delta_plan.fk_id_elisions == ("ItemType.category@allItems.category",)
        assert delta_plan.planned_resolver_keys == ("ItemType.category@allItems.category",)
        assert delta_plan.finalized_lookup_paths == frozenset()
        assert delta_plan.cacheable is False

    def test_consumer_descendant_string_absorbed_by_optimizer_prefetch(self) -> None:
        # The consumer's ``"items__entries"`` carries no info the
        # optimizer's nested ``Prefetch`` lacks.  The plain string is
        # stripped from the queryset and the optimizer entry is kept;
        # this avoids the ``'items' lookup was already seen with a
        # different queryset`` ValueError without sacrificing
        # projection.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == (outer,)
        assert delta_qs is not qs
        assert queryset_prefetch_lookups(delta_qs) == ()

    def test_consumer_exact_plus_descendant_strings_both_absorbed(self) -> None:
        # The exact-plus-descendant case: ``prefetch_related("items", "items__entries")``
        # combined.  Both plain strings are absorbed by the optimizer's
        # ``Prefetch("items", queryset=...)`` so Django does not see
        # the implicit ``items`` from ``items__entries`` colliding with
        # the explicit ``Prefetch("items", ...)``.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items", "items__entries")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == (outer,)
        assert delta_qs is not qs
        assert queryset_prefetch_lookups(delta_qs) == ()

    def test_optimizer_does_not_strip_consumer_descendants_it_does_not_cover(self) -> None:
        # When the optimizer's own subtree does not cover
        # every consumer descendant on the same subtree, absorbing
        # would silently drop data. Drop the optimizer entry instead;
        # the consumer's deeper prefetch is preserved.
        outer = Prefetch("items", queryset=Item.objects.only("name"))  # no nested chain
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs
        assert {getattr(e, "prefetch_to", e) for e in queryset_prefetch_lookups(delta_qs)} == {
            "items__entries",
        }

    def test_optimizer_can_absorb_consumer_path_only_when_covered(self) -> None:
        # Variant: consumer has both a covered descendant and an
        # uncovered descendant. The uncovered one tips the decision -
        # we drop the optimizer to keep the consumer's full subtree.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items__entries", "items__properties")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs

    def test_consumer_descendant_with_custom_prefetch_drops_optimizer(self) -> None:
        # When any consumer entry on the subtree is a custom
        # ``Prefetch`` (not just a bare string), we cannot losslessly
        # absorb it; drop the optimizer entry to preserve the
        # consumer's explicit subtree.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        consumer_descendant = Prefetch("items__entries", queryset=Entry.objects.all())
        qs = Category.objects.prefetch_related(consumer_descendant)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs
        assert queryset_prefetch_lookups(delta_qs) == (consumer_descendant,)

    def test_consumer_plain_string_replaced_by_optimizer_nested_prefetch(self) -> None:
        # The consumer's ``prefetch_related("items")`` plain
        # string vs. optimizer ``Prefetch("items", queryset=...)``
        # carrying nested chains.  The plain string carries no info
        # the optimizer's Prefetch lacks, so the optimizer wins and
        # the consumer's bare entry is stripped from the queryset.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        qs = Category.objects.prefetch_related("items")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == (outer,)
        assert delta_qs is not qs
        assert queryset_prefetch_lookups(delta_qs) == ()

    def test_upgrade_preserves_other_consumer_prefetches(self) -> None:
        # When upgrading a single consumer plain string to the
        # optimizer's ``Prefetch``, any unrelated consumer prefetches
        # must survive the queryset rewrite.
        inner = Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))
        outer = Prefetch("items", queryset=Item.objects.prefetch_related(inner))
        plan = OptimizationPlan(prefetch_related=[outer])
        unrelated = Prefetch("properties", queryset=Property.objects.all())
        qs = Category.objects.prefetch_related("items", unrelated)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == (outer,)
        assert delta_qs is not qs
        assert queryset_prefetch_lookups(delta_qs) == (unrelated,)

    def test_keeps_only_fields_when_consumer_applied_only_and_apply_unions(self) -> None:
        # Django's ``QuerySet.only(...).only(...)`` replaces (not merges) the
        # deferred-field set, so the diff leaves ``only_fields`` alone and the
        # projection writer spells out the union: the consumer's columns and
        # the selection's both load, neither side lazy-loads per row.
        plan = OptimizationPlan(select_related=["category"], only_fields=["id", "category_id"])
        qs = Item.objects.only("name")
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_qs is qs
        fields, is_deferred = delta_plan.apply(delta_qs).query.deferred_loading
        assert fields == {"id", "category_id", "name"}
        assert is_deferred is False

    def test_keeps_only_fields_when_consumer_did_not_apply_only(self) -> None:
        # Counterpart to the drop case: without a consumer ``.only()``,
        # the optimizer's ``only_fields`` passes through unchanged and
        # ``apply()`` applies it.
        plan = OptimizationPlan(only_fields=["id"])
        qs = Item.objects.all()
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        assert delta_plan.only_fields == ["id"]
        applied = delta_plan.apply(delta_qs)
        fields, is_deferred = applied.query.deferred_loading
        assert fields == {"id"}
        assert is_deferred is False

    def test_keeps_only_fields_when_consumer_used_defer(self) -> None:
        # Django's ``defer(a).only(a, b)`` silently keeps ``a`` deferred, so the
        # projection writer un-defers what the plan reads and keeps the rest of
        # the consumer's ``defer()``: the loaded set is the union of both sides.
        plan = OptimizationPlan(only_fields=["id", "name"])
        qs = Item.objects.defer("name", "description")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        assert delta_plan is plan
        fields, is_deferred = delta_plan.apply(qs).query.deferred_loading
        assert fields == {"description"}
        assert is_deferred is True

    def test_unions_with_the_consumer_effective_only_when_chained(self) -> None:
        # Django's chained ``.only().only()`` collapses to the most recent
        # argument; the union reads that effective set.
        plan = OptimizationPlan(only_fields=["id"])
        qs = Item.objects.only("name").only("category_id")
        delta_plan, _ = diff_plan_for_queryset(plan, qs)
        fields, _ = delta_plan.apply(qs).query.deferred_loading
        assert fields == {"id", "category_id"}

    def test_consumer_prefetch_with_queryset_keeps_consumer_drops_optimizer(self) -> None:
        # When the consumer passes their own ``Prefetch`` with a custom
        # queryset, we cannot losslessly replace it.  Consumer wins,
        # optimizer is dropped (any nested optimizer work is sacrificed
        # - the consumer chose to manage this branch explicitly).
        consumer_pf = Prefetch("items", queryset=Item.objects.all())
        opt_pf = Prefetch("items", queryset=Item.objects.prefetch_related("entries"))
        plan = OptimizationPlan(prefetch_related=[opt_pf])
        qs = Category.objects.prefetch_related(consumer_pf)
        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)
        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs
        assert queryset_prefetch_lookups(delta_qs) == (consumer_pf,)

    def test_consumer_custom_prefetch_survives_redundant_trailing_string(self) -> None:
        """A duplicate bare lookup never hides the consumer's custom queryset.

        Django accepts ``Prefetch("items", queryset=...)`` followed by the
        redundant ``"items"`` string and keeps the first custom queryset. The
        optimizer must inspect both same-path entries rather than collapsing
        them to the trailing string and replacing a permission filter.
        """
        consumer_pf = Prefetch(
            "items",
            queryset=Item.objects.filter(is_private=False),
        )
        opt_pf = Prefetch(
            "items",
            queryset=Item.objects.only("id", "category_id"),
        )
        plan = OptimizationPlan(prefetch_related=[opt_pf])
        qs = Category.objects.prefetch_related(consumer_pf, "items")

        delta_plan, delta_qs = diff_plan_for_queryset(plan, qs)

        assert delta_plan.prefetch_related == ()
        assert delta_qs is qs
        assert queryset_prefetch_lookups(delta_qs) == (consumer_pf, "items")


def _seal_as_is(seed: QuerySet[Model] | None, _info: object) -> QuerySet[Model]:
    """A target hook that admits every row of the seed (the default manager without one)."""
    return seed if seed is not None else Item.objects.all()


def _sealed_items_plan(seal: PrefetchSeal) -> OptimizationPlan:
    """A category plan prefetching ``items`` through a hooked target, its child planning ``nested``."""
    return OptimizationPlan(
        prefetch_related=[Prefetch("items", queryset=Item.objects.all())],
        planned_resolver_keys=["items-key", "nested-key"],
        prefetch_path_resolver_keys={"items": ("items-key", "nested-key")},
        prefetch_path_seals={"items": seal},
    ).finalize()


class TestConsumerPrefetchSeal:
    """A consumer ``Prefetch`` onto a sealed path that the hook cannot narrow wins unsealed."""

    def test_sliced_seed_is_not_sealed(self) -> None:
        seeds: list[QuerySet[Model] | None] = []

        def _recording_seal(seed: QuerySet[Model] | None, info: object) -> QuerySet[Model]:
            seeds.append(seed)
            return _seal_as_is(seed, info)

        plan = _sealed_items_plan(
            PrefetchSeal(own_keys=("items-key",), model=Item, seal=_recording_seal),
        )
        consumer = Prefetch("items", queryset=Item.objects.order_by("pk")[:2])
        queryset = Category.objects.prefetch_related(consumer)

        delta_plan, delta_qs = diff_plan_for_queryset(plan, queryset)

        assert seeds == []
        assert delta_plan.prefetch_related == ()
        assert delta_plan.planned_resolver_keys == ()
        assert queryset_prefetch_lookups(delta_qs) == (consumer,)

    @pytest.mark.parametrize(
        ("seals", "lookups", "expected"),
        [
            pytest.param(False, ("items__entries",), False, id="no-seals"),
            pytest.param(True, ("items__entries",), True, id="beneath-sealed-path"),
            pytest.param(True, ("items",), True, id="on-sealed-path"),
            pytest.param(True, ("properties",), False, id="elsewhere"),
        ],
    )
    def test_seals_consumer_prefetch_reads_the_consumer_lookups(
        self,
        lookups: tuple[str, ...],
        *,
        seals: bool,
        expected: bool,
    ) -> None:
        plan = (
            _sealed_items_plan(PrefetchSeal(own_keys=("items-key",), model=Item, seal=_seal_as_is))
            if seals
            else OptimizationPlan(prefetch_related=["items"]).finalize()
        )

        assert (
            seals_consumer_prefetch(plan, Category.objects.prefetch_related(*lookups)) is expected
        )


def _linked_path(*keys: str | int) -> SimpleNamespace | None:
    """Build a graphql-core-style ``key``/``prev`` linked response path."""
    node = None
    for key in keys:
        node = SimpleNamespace(key=key, prev=node)
    return node


class TestRuntimePathFromPath:
    """``runtime_path_from_path`` walks ``prev`` under a fixed, fail-loud bound."""

    def test_walks_a_deep_but_finite_path(self) -> None:
        """A path of (ceiling - 1) nodes resolves fully - the boundary that just fits."""
        # _linked_path builds root-first; the output is that same root-first order.
        keys = tuple(f"f{i}" for i in range(_MAX_PATH_DEPTH - 1))
        path = _linked_path(*keys)
        assert runtime_path_from_path(path) == keys

    def test_strips_list_indexes(self) -> None:
        """Integer (list-index) keys are skipped; string keys/aliases kept."""
        path = _linked_path("allItems", 0, "cat")
        assert runtime_path_from_path(path) == ("allItems", "cat")

    def test_raises_on_cyclic_path(self) -> None:
        """A self-referential ``prev`` chain hits the bound and fails loud."""
        node = SimpleNamespace(key="loop", prev=None)
        node.prev = node  # never bottoms out
        with pytest.raises(RuntimeError, match="cyclic or corrupt"):
            runtime_path_from_path(node)


class TestApplyWindowPagination:
    """``apply_window_pagination`` annotation + range-filter mechanism (spec-033 Decision 4)."""

    def _windowed(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        reverse: bool = False,
        with_total_count: bool = True,
        next_page_probe: bool = False,
    ) -> QuerySet[Item]:
        return apply_window_pagination(
            Item.objects.all(),
            partition_by="category_id",
            order_by=["name", "pk"],
            offset=offset,
            limit=limit,
            reverse=reverse,
            with_total_count=with_total_count,
            next_page_probe=next_page_probe,
        )

    def test_annotates_row_number_and_total_count(self) -> None:
        """Both window annotations land under the ``_dst_*`` reserved names."""
        qs = self._windowed(offset=0, limit=3)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT in annotations
        sql = str(qs.query).upper()
        assert "ROW_NUMBER()" in sql
        assert "COUNT(" in sql

    def test_ambiguous_shapes_keep_partition_marker_row(self) -> None:
        """``offset > 0`` / ``limit == 0`` windows keep each partition's row 1.

        The marker-row disambiguation (spec-033 Decision 5):
        the otherwise-ambiguous empty shapes OR the range filter with
        ``row_number == 1`` so an empty prefetch list proves zero children and
        a marker-only list carries the real count. The SQL shape pin: the
        row-number predicate appears with BOTH the range bound and the
        ``= 1`` alternative.
        """
        overshot = self._windowed(offset=5, limit=2)
        sql = str(overshot.query).upper()
        assert "> 5" in sql
        assert "<= 7" in sql
        assert "= 1" in sql  # the marker alternative
        assert " OR " in sql

        first_zero = self._windowed(offset=0, limit=0)
        sql = str(first_zero.query).upper()
        assert "= 1" in sql

        # Unbounded overshoot (offset without a finite limit) still markers.
        unbounded = self._windowed(offset=3, limit=None)
        sql = str(unbounded.query).upper()
        assert "> 3" in sql
        assert "= 1" in sql

    def test_unambiguous_shapes_plan_no_marker(self) -> None:
        """Plain ``first: N`` (offset 0, positive bound) and reverse windows add no marker."""
        plain = self._windowed(offset=0, limit=3)
        sql = str(plain.query).upper()
        assert "<= 3" in sql
        assert " OR " not in sql

        # The reversed (last-only) window never markers, even at ``limit == 0``.
        reverse_zero = self._windowed(offset=0, limit=0, reverse=True)
        sql = str(reverse_zero.query).upper()
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert " OR " not in sql

    def test_with_total_count_false_omits_count_annotation(self) -> None:
        """``with_total_count=False`` drops the count window, keeping the row filters.

        The conditional-count contract (spec-033 Decision 4):
        the walker passes ``False`` when nothing in the selection observes the
        count; the row-number annotation and its range filters are untouched.
        """
        qs = self._windowed(offset=2, limit=3, with_total_count=False)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        sql = str(qs.query).upper()
        assert "ROW_NUMBER()" in sql
        assert WINDOW_TOTAL_COUNT.upper() not in sql
        # The range filters still apply without the count annotation.
        assert ">" in sql
        assert "<=" in sql

    def test_next_page_probe_overfetches_one_row_without_the_count(self) -> None:
        """``next_page_probe=True`` bounds to ``limit + 1`` and drops the count.

        The count-free ``hasNextPage`` render: the plain first page fetches ONE
        sentinel row past the page (``<= 4`` for ``first: 3``, not ``<= 3``) and
        omits ``_dst_total_count`` entirely - the resolver derives ``hasNextPage``
        from the sentinel's presence. The renderer reads ``fetch_upper_bound``
        and never mentions the probe itself.
        """
        qs = self._windowed(offset=0, limit=3, with_total_count=False, next_page_probe=True)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        sql = str(qs.query).upper()
        assert "<= 4" in sql  # the n+1 sentinel bound
        assert "<= 3" not in sql  # NOT the plain page bound
        assert " OR " not in sql  # a probe is not a marker shape

    def test_next_page_probe_composes_with_marker_on_the_offset_page(self) -> None:
        """The bounded forward offset page overfetches the sentinel AND markers.

        ``next_page_probe`` engages on the offset page too, composing with the
        marker: the range bound becomes ``<= offset + limit + 1`` (the n+1 sentinel
        via ``fetch_upper_bound``) OR'd with the ``= 1`` marker alternative, and no
        count is annotated. This is load-bearing - the offset page
        stops paying ``Count(1) OVER`` for a ``hasNextPage``-only selection.
        """
        qs = self._windowed(offset=2, limit=3, with_total_count=False, next_page_probe=True)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        sql = str(qs.query).upper()
        assert "> 2" in sql
        assert "<= 6" in sql  # offset 2 + limit 3 + 1 sentinel
        assert "<= 5" not in sql  # NOT the plain page bound
        assert "= 1" in sql  # the marker alternative
        assert " OR " in sql  # marker composes with the probe bound

    def test_next_page_probe_inert_on_the_unbounded_offset_shape(self) -> None:
        """The probe flag stays inert on the unbounded offset page (no finite bound).

        An ``after``-offset window with no ``first`` has no upper bound for the
        sentinel to sit past, so ``window_range_plan`` drops the probe and the
        window keeps its marker-only shape (``> offset`` OR ``= 1``).
        """
        qs = self._windowed(offset=3, limit=None, next_page_probe=True)
        sql = str(qs.query).upper()
        assert "> 3" in sql
        assert "= 1" in sql  # marker only
        assert "<= " not in sql  # no finite fetch ceiling

    @pytest.mark.parametrize("offset", [0, 2], ids=["first-page", "offset-page"])
    def test_engaged_probe_with_count_is_rejected(self, offset: int) -> None:
        """An engaged-probe window that also annotates the count fails loudly.

        The probe/count mutual-exclusion contract at the ORM window entry point
        (``utils/connections.py::assert_window_fetch_mode``): a probe-eligible
        window (the plain first page OR the bounded forward offset page) with
        ``next_page_probe=True`` engages the overfetch, so ``with_total_count=True``
        is a planner bug - the sentinel would leak as a real edge. The unbounded
        offset case is inert and stays allowed
        (``test_next_page_probe_inert_on_the_unbounded_offset_shape`` above).
        """
        with pytest.raises(OptimizerError, match="mutually exclusive"):
            self._windowed(offset=offset, limit=3, with_total_count=True, next_page_probe=True)

    def test_with_total_count_false_reverse_branch_still_bounds(self) -> None:
        """The reverse (last-only) branch honors ``with_total_count=False`` too."""
        qs = self._windowed(offset=0, limit=2, reverse=True, with_total_count=False)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER_REVERSED in annotations
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT not in annotations
        assert "<= 2" in str(qs.query).upper()

    def test_applies_order_by_to_queryset_not_just_the_window(self) -> None:
        """The deterministic order is applied to the queryset's own ``ORDER BY``.

        The SQL window orders the ROW-NUMBER values, but Django hands prefetched
        instances to ``to_attr`` in the queryset's own return order; the fast path
        consumes ``rows`` as forward-ordered. So the same ``order_by`` tuple must
        drive ``queryset.order_by`` too, or the fast path can diverge from the
        fallback pipeline when DB return order != connection order
        (spec-033 Decision 4, cursor-parity). Forward order applies in BOTH
        branches.
        """
        forward = self._windowed(offset=0, limit=3)
        assert tuple(forward.query.order_by) == ("name", "pk")
        reverse = self._windowed(offset=0, limit=2, reverse=True)
        assert tuple(reverse.query.order_by) == ("name", "pk")

    def test_forward_window_filters_offset_and_upper_bound(self) -> None:
        """A forward window with offset+limit filters ``__gt`` offset and ``__lte`` offset+limit."""
        qs = self._windowed(offset=2, limit=3)
        where = str(qs.query).upper()
        # Window-function filters wrap the queryset in a subquery with the
        # row-number predicates; both bounds must appear.
        assert WINDOW_ROW_NUMBER.upper() in where
        # offset filter (> 2) and upper-bound filter (<= 5) both present.
        assert "> 2" in where
        assert "<= 5" in where

    def test_no_offset_skips_lower_filter(self) -> None:
        """``offset == 0`` applies only the upper-bound filter."""
        qs = self._windowed(offset=0, limit=3)
        # The annotations are present; only the upper-bound filter applies.
        assert WINDOW_ROW_NUMBER in qs.query.annotations
        sql = str(qs.query).upper()
        assert "<= 3" in sql
        assert " > " not in sql

    def test_reverse_branch_uses_reversed_row_number(self) -> None:
        """The reverse (last-only) branch annotates ``_dst_row_number_reversed`` and bounds it."""
        qs = self._windowed(offset=0, limit=2, reverse=True)
        annotations = qs.query.annotations
        assert WINDOW_ROW_NUMBER_REVERSED in annotations
        # The reversed window still annotates the forward row number + total count.
        assert WINDOW_ROW_NUMBER in annotations
        assert WINDOW_TOTAL_COUNT in annotations
        # The reversed window MUST be bounded to ``limit`` rows (annotation alone
        # over-fetches every child row).
        sql = str(qs.query).upper()
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert "<= 2" in sql

    def test_reverse_branch_applies_offset_filter_when_present(self) -> None:
        """``reverse=True`` with a non-zero ``offset`` still applies the forward gt-filter.

        The walker never plans this combination (``after`` + ``last`` raises
        ``UnwindowableConnection`` at bounds derivation), but the helper's
        contract is the full ``(offset, limit, reverse)`` surface for direct
        callers: the forward offset filter composes with the reversed bound
        rather than being silently dropped.
        """
        qs = self._windowed(offset=2, limit=3, reverse=True)
        sql = str(qs.query).upper()
        assert "> 2" in sql
        assert WINDOW_ROW_NUMBER_REVERSED.upper() in sql
        assert "<= 3" in sql

    def test_reverse_branch_with_none_limit_adds_no_upper_filter(self) -> None:
        """``reverse=True, limit=None`` annotates the reversed window but adds no bound.

        Guards that the limit-vs-``None`` decision lives in the caller
        (``_connection_window_slice_from_arguments`` passes the literal
        ``last`` for the reverse branch); ``apply_window_pagination`` itself
        still no-ops on ``None``.
        """
        qs = self._windowed(offset=0, limit=None, reverse=True)
        assert WINDOW_ROW_NUMBER_REVERSED in qs.query.annotations
        assert "<=" not in str(qs.query).upper()

    def test_unbounded_limit_skips_upper_filter(self) -> None:
        """``limit is None`` (no upper bound) annotates but adds no ``__lte`` row filter."""
        qs = self._windowed(offset=1, limit=None)
        # Annotation present; offset filter applies, but no finite upper bound.
        assert WINDOW_ROW_NUMBER in qs.query.annotations
        sql = str(qs.query).upper()
        assert "> 1" in sql
        assert "<=" not in sql

    def test_maxsize_limit_skips_upper_filter(self) -> None:
        """``sys.maxsize`` (relay's no-limit sentinel) adds no upper-bound filter."""
        qs = self._windowed(offset=0, limit=sys.maxsize)
        assert WINDOW_ROW_NUMBER in qs.query.annotations
        sql = str(qs.query).upper()
        assert "<=" not in sql
        assert " > " not in sql

    def test_annotations_compose_with_only(self) -> None:
        """Window annotations survive a ``.only()`` projection (annotations, not columns)."""
        qs = apply_window_pagination(
            Item.objects.only("name", "category_id"),
            partition_by="category_id",
            order_by=["name", "pk"],
            offset=0,
            limit=3,
        )
        assert WINDOW_ROW_NUMBER in qs.query.annotations
        assert WINDOW_TOTAL_COUNT in qs.query.annotations


class TestOrderEntryHasExplicitNulls:
    """``order_entry_has_explicit_nulls`` is the shared OrderBy NULLS vocabulary gate."""

    def test_string_refs_never_carry_nulls(self) -> None:
        assert order_entry_has_explicit_nulls("title") is False
        assert order_entry_has_explicit_nulls("-title") is False

    def test_plain_orderby_is_not_explicit(self) -> None:
        assert order_entry_has_explicit_nulls(F("title").asc()) is False
        assert order_entry_has_explicit_nulls(F("title").desc()) is False

    def test_nulls_first_or_last_is_explicit(self) -> None:
        assert order_entry_has_explicit_nulls(F("title").asc(nulls_first=True)) is True
        assert order_entry_has_explicit_nulls(F("title").desc(nulls_last=True)) is True


class TestDeterministicOrder:
    """The deterministic order rule has one source, which ``connection.py`` re-exports."""

    def test_ends_in_unique_column_string_refs(self) -> None:
        """String order refs: pk / attname / unique field are unique; non-unique are not."""
        assert ends_in_unique_column(("id",), Category) is True
        assert ends_in_unique_column(("pk",), Category) is True
        assert ends_in_unique_column(("name",), Category) is True  # Category.name unique=True
        assert ends_in_unique_column(("-name",), Category) is True  # leading '-' stripped
        assert ends_in_unique_column(("name",), Item) is False  # Item.name unique=False
        assert ends_in_unique_column(("category__name",), Item) is False  # relation path
        assert ends_in_unique_column(("_dst_order_alias",), Category) is False  # annotation alias
        assert ends_in_unique_column((), Category) is False  # unordered

    def test_ends_in_unique_column_expression_refs(self) -> None:
        """``F`` expression terminals read the wrapped column name."""
        assert ends_in_unique_column((F("name").asc(),), Category) is True  # unique
        assert ends_in_unique_column((F("name").asc(),), Item) is False  # non-unique

    def test_ends_in_unique_column_bare_f_expression(self) -> None:
        """Bare ``F`` expression terminals read the wrapped column name directly."""
        assert ends_in_unique_column((F("name"),), Category) is True  # unique
        assert ends_in_unique_column((F("name"),), Item) is False  # non-unique
        assert ends_in_unique_column((F("id"),), Item) is True  # unique pk
        assert deterministic_order((F("id"),), Item) == (F("id"),)

    def test_ends_in_unique_column_unnameable_terminal(self) -> None:
        """A transform terminal (no readable column name) is treated as non-unique."""
        assert ends_in_unique_column((Lower("name"),), Category) is False

    def test_ends_in_unique_column_nullable_unique_is_not_total_order(self) -> None:
        """A NULLABLE unique terminal is NOT a total order.

        SQL ``UNIQUE`` permits multiple NULLs, so terminal ties among NULL rows
        are nondeterministic - the pk must still be appended. ``NullableScalarSpecimen.label``
        is ``unique=True, null=True``: unique but not a total order.
        """
        assert ends_in_unique_column(("label",), NullableScalarSpecimen) is False
        # So the pk is appended as the terminal tiebreaker.
        assert deterministic_order(("label",), NullableScalarSpecimen) == ("label", "id")
        # Contrast: a NON-nullable unique terminal remains a total order.
        assert ends_in_unique_column(("name",), Category) is True
        assert deterministic_order(("name",), Category) == ("name",)

    def test_deterministic_order_appends_pk_when_not_unique(self) -> None:
        """A non-unique terminal gets the pk appended; a unique one is returned unchanged."""
        assert deterministic_order(("name",), Item) == ("name", "id")
        # Already ends in a unique column -> unchanged.
        assert deterministic_order(("name",), Category) == ("name",)
        assert deterministic_order(("id",), Item) == ("id",)

    def test_deterministic_order_matches_connection_reexport(self) -> None:
        """``connection.py`` re-exports the same ``ends_in_unique_column`` (one source)."""
        assert _ends_in_unique_column is ends_in_unique_column

    def test_ends_in_unique_column_defensive_for_non_model(self) -> None:
        """Non-model objects without ``_meta`` safely return False."""
        # basedpyright: each non-model is the hostile input under test; ends_in_unique_column
        # types the parameter as type[Model]
        assert ends_in_unique_column(("id",), object()) is False  # pyright: ignore[reportArgumentType]
        assert ends_in_unique_column(("id",), SimpleNamespace()) is False  # pyright: ignore[reportArgumentType]


class TestEffectiveConnectionOrder:
    """The shared default-order precedence for BOTH connection order sites.

    ``effective_connection_order`` is the one spelling of "which ORDER BY does a
    connection paginate under by default" consumed by the plan-time window
    (``nested_planner.py::plan_connection_relation``) and the resolve-time
    pipeline (``connection.py::_finalize_queryset``) - the cursor-parity
    invariant's order leg (spec-033 Decision 4).
    """

    def test_keyset_cursor_field_is_the_default_order_when_no_explicit_won(self) -> None:
        """A declared ``cursor_field`` IS the connection order with no explicit orderBy."""
        query = Item.objects.all().query
        assert effective_connection_order(("-number", "id"), query, Item) == ("-number", "id")

    def test_explicit_orderby_beats_the_declared_cursor_field(self) -> None:
        """An explicit ``orderBy:`` keeps the shipped derivation even for a keyset target."""
        query = Item.objects.order_by("name").query
        assert effective_connection_order(("-number", "id"), query, Item) == ("name", "id")

    def test_falls_back_to_meta_ordering_through_deterministic_order(self) -> None:
        """No explicit order: model ``Meta.ordering`` is honored, made total if needed.

        ``Status`` orders by the non-unique ``order`` column implicitly, so the pk
        is appended; ``Card.number`` is unique-terminal, so it is returned
        unchanged.
        """
        assert effective_connection_order(None, Status.objects.all().query, Status) == (
            "order",
            "id",
        )
        assert effective_connection_order(None, Card.objects.all().query, Card) == ("number",)

    def test_no_order_source_anywhere_appends_the_pk(self) -> None:
        """An unordered model with no explicit order paginates by the pk alone."""
        assert effective_connection_order(None, Item.objects.all().query, Item) == ("id",)

    def test_ordering_none_is_no_default_order(self) -> None:
        """``Meta.ordering = None`` clears an abstract parent's order; the pk alone totals it.

        Django accepts ``None`` and reads the option by truthiness, so it is no
        default order rather than an iterable to unpack.
        """
        assert ReadingListEntry._meta.ordering is None
        query = ReadingListEntry.objects.all().query
        assert effective_connection_order(None, query, ReadingListEntry) == ("id",)
        assert effective_connection_order(None, ReadingList.objects.all().query, ReadingList) == (
            "title",
            "id",
        )

    def test_cleared_default_ordering_is_not_reapplied(self) -> None:
        """A bare ``.order_by()`` turns ``Meta.ordering`` off, so the pk alone totals the page.

        Django compiles no ``Meta.ordering`` once ``query.default_ordering`` is
        cleared, so a connection over that source pages under the pk tiebreaker,
        not the model order the consumer removed.
        """
        query = Status.objects.order_by().query
        assert query.default_ordering is False
        assert effective_connection_order(None, query, Status) == ("id",)


class TestNormalizeOrderDirection:
    """A reversed queryset becomes the reverse of its forward total order, flag reset.

    The connection order ladder's two entry points run it first; the live
    reversed-hook rows in ``examples/fakeshop/test_query/test_keyset_api.py``
    page through it. These rows pin each source of the forward order and that
    the materialized order compiles the SQL Django compiles for the reversed
    queryset once the connection's tiebreaker joins it.
    """

    def test_forward_queryset_is_returned_as_is(self) -> None:
        """A queryset under the forward flag is the same object back."""
        queryset = Item.objects.order_by("name")
        assert normalize_order_direction(queryset, None, Item) is queryset

    def test_explicit_order_is_reversed_whole_with_the_flag_reset(self) -> None:
        """``order_by("name").reverse()`` materializes ``-name, -id`` under the forward flag."""
        reversed_queryset = Item.objects.order_by("name").reverse()
        normalized = normalize_order_direction(reversed_queryset, None, Item)
        assert reversed_queryset.query.standard_ordering is False
        assert (normalized.query.standard_ordering, normalized.query.order_by) == (
            True,
            ("-name", "-id"),
        )
        compiled = Item.objects.order_by("name", "id").reverse()
        assert str(normalized.query) == str(compiled.query)
        assert effective_connection_order(None, normalized.query, Item) == ("-name", "-id")

    def test_meta_ordering_is_materialized_then_reversed(self) -> None:
        """A bare ``.reverse()`` reverses the model's ``Meta.ordering`` made total."""
        assert normalize_order_direction(
            Status.objects.reverse(),
            None,
            Status,
        ).query.order_by == ("-order", "-id")
        normalized = normalize_order_direction(ReadingList.objects.reverse(), None, ReadingList)
        assert normalized.query.order_by == ("-title", "-id")
        assert str(normalized.query) == str(
            ReadingList.objects.order_by("title", "id").reverse().query,
        )

    def test_orderby_expression_swaps_its_nulls_placement(self) -> None:
        """An ``OrderBy`` reverses through Django's own ``reverse_ordering``, NULLS included."""
        reversed_queryset = Item.objects.order_by(F("name").asc(nulls_first=True)).reverse()
        normalized = normalize_order_direction(reversed_queryset, None, Item)
        entry, tiebreaker = normalized.query.order_by
        assert isinstance(entry, OrderBy)
        assert (entry.descending, *_nulls_slots(entry), tiebreaker) == (
            True,
            None,
            True,
            "-id",
        )
        compiled = Item.objects.order_by(F("name").asc(nulls_first=True), "id").reverse()
        assert str(normalized.query) == str(compiled.query)

    def test_extra_ordering_expression_moves_into_order_by_as_is(self) -> None:
        """An expression in ``extra(order_by=...)`` becomes the explicit order unchanged.

        The compiler runs it through the same per-term loop from either
        collection, so the moved order compiles the SQL the ``extra`` ordering
        compiled. Only a queryset no visibility seal ran on carries one: the seal
        admits ``extra`` order terms that are strings.
        """
        term = Lower("name").desc()
        queryset = Item.objects.all().extra(order_by=[term])
        normalized = normalize_order_direction(queryset, None, Item)
        assert (normalized.query.extra_order_by, normalized.query.order_by) == ((), (term,))
        assert str(normalized.query) == str(queryset.query)

    def test_raw_extra_term_moves_as_the_sql_the_compiler_emits(self) -> None:
        """A dotted term naming no own column moves as the ``RawSQL`` Django compiles for it."""
        queryset = Item.objects.all().extra(order_by=['-"products_item".name'])
        normalized = normalize_order_direction(queryset, None, Item)
        (moved,) = normalized.query.order_by
        assert isinstance(moved, OrderBy)
        assert moved.descending is True
        assert normalized.query.extra_order_by == ()
        assert str(normalized.query) == str(queryset.query)

    def test_no_order_anywhere_reverses_the_cursor_field_else_the_pk(self) -> None:
        """With no order on the queryset or model, the declared cursor order (or pk) flips."""
        assert normalize_order_direction(
            Item.objects.reverse(),
            ("-name", "id"),
            Item,
        ).query.order_by == ("name", "-id")
        normalized = normalize_order_direction(Item.objects.reverse(), None, Item)
        assert (normalized.query.standard_ordering, normalized.query.order_by) == (True, ("-id",))


def _issue_cursor_state() -> CursorState:
    """The declared ``("-number", "id")`` vocabulary over the library ``Issue`` model."""
    state = declared_cursor_state_for_definition(
        make_definition(Issue, cursor_field=("-number", "id")),
    )
    assert state is not None
    return state


class TestEffectiveCursorState:
    """The one derivation of a keyset page's cursor vocabulary from its effective order."""

    @pytest.mark.parametrize("effective", [(), ("-number", "id")], ids=["unordered", "declared"])
    def test_the_declared_order_is_the_declared_state_itself(
        self,
        effective: tuple[str, ...],
    ) -> None:
        """The planner reads ``is`` as "decode under the declared vocabulary already done"."""
        state = _issue_cursor_state()
        assert effective_cursor_state(state, effective) == (state, {})
        assert effective_cursor_state(state, effective)[0] is state

    def test_another_order_derives_its_own_columns_fingerprint_and_annotations(self) -> None:
        state = _issue_cursor_state()
        derived, annotations = effective_cursor_state(state, ("periodical__name", "-id"))
        assert derived.definition is state.definition
        assert derived.cursor_field == ("periodical__name", "-id")
        assert derived.fingerprint == order_fingerprint(("periodical__name", "-id"))
        assert [(c.name, c.descending, c.value_source) for c in derived.columns] == [
            ("periodical__name", False, "_dst_cursor_value_0"),
            ("id", True, "id"),
        ]
        assert annotations == {"_dst_cursor_value_0": F("periodical__name")}
        # Only the local column is read off the row; the related one rides its annotation.
        assert local_cursor_attnames(derived) == ("id",)
        assert local_cursor_attnames(state) == ("number", "id")


def test_metadata_merge_merges_the_window_vocabularies_by_resolver_key() -> None:
    """Each window keeps its own bounds and vocabulary under its own resolver key."""
    state = _issue_cursor_state()
    derived, _annotations = effective_cursor_state(state, ("-id",))
    bounds = ConnectionWindowBounds(offset=0, limit=2, reverse=False)
    root = PlannedWindow(bounds, state)
    nested = PlannedWindow(bounds, derived)
    target = OptimizationPlan(planned_windows={"Root.kids@roots.kids": root})
    target.merge_metadata_from(
        OptimizationPlan(planned_windows={"Kid.kids@roots.kids.edges.node.kids": nested}),
    )
    assert target.planned_windows == {
        "Root.kids@roots.kids": root,
        "Kid.kids@roots.kids.edges.node.kids": nested,
    }


def _nulls_slots(entry: OrderBy) -> tuple[bool | None, bool | None]:
    """``(nulls_first, nulls_last)`` as ``OrderBy`` stores them: ``None`` is the backend default."""
    return entry.nulls_first, entry.nulls_last


class TestReverseOrderBy:
    """``_reverse_order_by`` mirrors Django's ``queryset.reverse()`` (spec-033 Decision 4)."""

    def test_flips_string_direction(self) -> None:
        """String refs toggle the leading ``-``; the pk terminal stays total."""
        assert _reverse_order_by(["name", "id"]) == ["-name", "-id"]
        assert _reverse_order_by(["-name", "id"]) == ["name", "-id"]

    def test_flips_orderby_descending(self) -> None:
        """``OrderBy`` expressions flip ``.descending`` without re-running the compiler."""
        reversed_order = _reverse_order_by([F("name").asc()])
        assert isinstance(reversed_order[0], OrderBy)
        assert reversed_order[0].descending is True

    def test_swaps_explicit_nulls_positioning(self) -> None:
        """Explicit ``nulls_first`` / ``nulls_last`` swap on reversal, like ``.reverse()``.

        Django inverts NULLS placement when reversing an ordering; mirror that so
        a consumer ``OrderSet`` with explicit NULLS positioning produces a reversed
        window matching the resolve-time ``.reverse()`` pipeline.
        """
        nulls_first = _reverse_order_by([F("name").asc(nulls_first=True)])[0]
        assert isinstance(nulls_first, OrderBy)
        assert nulls_first.descending is True
        first_slot, last_slot = _nulls_slots(nulls_first)
        assert first_slot is None
        assert last_slot is True

        nulls_last = _reverse_order_by([F("name").desc(nulls_last=True)])[0]
        assert isinstance(nulls_last, OrderBy)
        assert nulls_last.descending is False
        first_slot, last_slot = _nulls_slots(nulls_last)
        assert first_slot is True
        assert last_slot is None

    def test_random_order_passes_through(self) -> None:
        """``"?"`` carries no direction: it stays ``"?"`` (``order_by("-?")`` is a FieldError)."""
        assert _reverse_order_by(["?", "id"]) == ["?", "-id"]

    def test_bare_expression_reverses_through_desc(self) -> None:
        """A term with no ``.descending`` is IMPLICITLY ascending; its reverse is ``desc()``.

        ``deterministic_order`` carries whatever the child queryset or
        ``Meta.ordering`` ordered by, and Django's ``order_by`` accepts bare
        expressions (``Lower("title")``, ``Coalesce(...)``, a plain ``F``) with no
        direction of their own. SQL reads those as ascending, and
        ``queryset.reverse()`` inverts them - so the window's reversed row number
        must sort them DESCENDING.

        A term passed through UNCHANGED would leave ``_dst_row_number_reversed``
        ordered forward on that column, so a ``last: N`` page filtering
        ``rn_reversed <= N`` over a forward numbering would return the partition's
        FIRST rows.
        """
        reversed_f = _reverse_order_by([F("name")])[0]
        assert isinstance(reversed_f, OrderBy)
        assert reversed_f.descending is True
        assert reversed_f.expression == F("name")

        reversed_expression = _reverse_order_by([Lower("title")])[0]
        assert isinstance(reversed_expression, OrderBy)
        assert reversed_expression.descending is True
        assert reversed_expression.expression == Lower("title")

    def test_unreversible_term_raises_instead_of_serving_the_wrong_end(self) -> None:
        """A term that is neither an ``OrderBy`` nor ``desc()``-able fails loudly.

        There is no correct reversal for such a term, and silently keeping it
        forward is what produced a wrong ``last: N`` page. ``OptimizerError`` (not
        ``ValueError`` / ``TypeError``) so the walker's leave-unplanned pagination
        handler cannot swallow it.
        """
        unreversible = SimpleNamespace(name="not-an-expression")
        with pytest.raises(
            OptimizerError,
            match=r"Cannot reverse connection order entry .*neither an 'OrderBy' nor carries",
        ):
            # basedpyright: the unreversible term is the hostile input under test;
            # _reverse_order_by types the parameter as Sequence[OrderEntry]
            _reverse_order_by([unreversible])  # pyright: ignore[reportArgumentType]


class TestApplyOverAConsumerProjection:
    """``OptimizationPlan.apply`` over a queryset that already carries ``.only()`` / ``.defer()``.

    Django refuses ``select_related`` through a deferred relation field
    ("cannot be both deferred and traversed"); the plan's projection is written as
    the union with the consumer's, every join connector loaded, so the JOIN
    compiles. Each case compiles the applied queryset (``str(qs.query)``): the
    runtime behavior Django enforces, not just the plan shape.
    """

    @staticmethod
    def _apply(plan: OptimizationPlan, queryset: QuerySet[Model]) -> QuerySet[Model]:
        """The extension's reconcile-then-apply pipeline."""
        delta, queryset = diff_plan_for_queryset(plan, queryset)
        return delta.apply(queryset)

    @pytest.mark.parametrize("introduce", [True, False], ids=["introduces", "widens-only"])
    def test_projected_plan_keeps_the_path_and_loads_its_connector(
        self,
        *,
        introduce: bool,
    ) -> None:
        plan = OptimizationPlan(
            select_related=["category"],
            only_fields=["name", "category_id", "category__name"],
            introduce_projection=introduce,
        ).finalize()
        applied = self._apply(plan, Item.objects.only("description"))
        assert applied.query.deferred_loading == (
            frozenset(
                {
                    "name",
                    "category_id",
                    "category__name",
                    "description",
                },
            ),
            False,
        )
        assert 'JOIN "products_category"' in str(applied.query)

    @pytest.mark.parametrize("introduce", [True, False], ids=["introduces", "widens-only"])
    def test_projected_plan_undefers_the_connector_the_consumer_deferred(
        self,
        *,
        introduce: bool,
    ) -> None:
        plan = OptimizationPlan(
            select_related=["shelf", "shelf__branch"],
            only_fields=["title", "shelf_id", "shelf__code"],
            introduce_projection=introduce,
        ).finalize()
        applied = self._apply(plan, Book.objects.defer("shelf"))
        assert applied.query.deferred_loading == (frozenset(), True)
        compiled = str(applied.query)
        assert 'JOIN "library_shelf"' in compiled
        assert 'JOIN "library_branch"' in compiled


@pytest.mark.parametrize(
    ("queryset_factory", "introduce", "expected"),
    [
        pytest.param(
            Item.objects.all,
            True,
            (frozenset({"name", "category_id"}), False),
            id="unprojected-introduces",
        ),
        pytest.param(
            Item.objects.all,
            False,
            (frozenset[str](), True),
            id="unprojected-left-whole",
        ),
        pytest.param(
            lambda: Item.objects.only("description"),
            False,
            (frozenset({"name", "category_id", "description"}), False),
            id="only-widened",
        ),
        pytest.param(
            lambda: Item.objects.defer("name", "description"),
            False,
            (frozenset({"description"}), True),
            id="defer-narrowed",
        ),
    ],
)
def test_apply_projection_introduces_only_when_asked(
    queryset_factory: Callable[[], QuerySet[Item]],
    *,
    introduce: bool,
    expected: tuple[frozenset[str], bool],
) -> None:
    """``introduce=False`` leaves an unprojected queryset whole and widens a projected one.

    A consumer ``.only()`` gains every name read; a consumer ``.defer()`` stops
    deferring them. With nothing to widen and ``introduce=False`` the queryset
    loads every column, Django's default ``(frozenset(), True)``.
    """
    applied = apply_projection(queryset_factory(), ["name", "category_id"], introduce=introduce)

    assert applied.query.deferred_loading == expected


def test_consumer_projection_defensive_shapes() -> None:
    """``_consumer_projection`` reports no projection for shapes no queryset produces.

    A non-queryset input and a malformed ``deferred_loading`` shape both read as
    "no projection", so ``apply_projection(..., introduce=False)`` leaves them alone.
    """
    assert _consumer_projection(SimpleNamespace()) is None
    malformed = SimpleNamespace(query=SimpleNamespace(deferred_loading=("only-one",)))
    assert _consumer_projection(malformed) is None


@pytest.mark.parametrize(
    ("path", "names", "expected"),
    [
        pytest.param("item", {"value", "item_id"}, (), id="connector-loaded"),
        pytest.param("item", {"value"}, ("item_id",), id="connector-missing"),
        pytest.param("bogus", {"value"}, None, id="unknown-segment"),
        pytest.param("item__name__upper", {"value"}, None, id="through-a-column"),
    ],
)
def test_select_path_missing_connectors(
    path: str,
    names: set[str],
    expected: tuple[str, ...] | None,
) -> None:
    """The ``.only()`` entries a joined path still needs, or ``None`` when it does not resolve."""
    select_mask = _select_mask(Entry, names)
    assert _select_path_missing_connectors(path, select_mask, model=Entry) == expected


def test_apply_projection_leaves_a_filtered_relation_join_alone() -> None:
    """A ``FilteredRelation`` alias is no deferred field: the ``.only()`` applies as given."""
    queryset = Entry.objects.annotate(
        public_item=FilteredRelation("item", condition=Q(item__is_private=False)),
    ).select_related("public_item")

    applied = apply_projection(queryset, ["value"])

    assert applied.query.deferred_loading == (frozenset({"value"}), False)
    assert "public_item" in str(applied.query)


class _RenamedKeyFK(models.ForeignKey[ContentType | Combinable, ContentType]):
    """A content-type key whose column attribute is ``<name>_ref``, not ``<name>_id``."""

    @override
    def get_attname(self) -> str:
        return f"{self.name}_ref"


@isolate_apps("apps.library")
def test_apply_projection_keeps_a_generic_foreign_key_carrier_by_its_key_attname() -> None:
    """A consumer prefetch of a ``GenericForeignKey`` keeps its key field's own attname.

    Django's generic prefetch reads the content type off each row by the key
    field's ``attname``; a ``ForeignKey`` subclass may spell that attribute
    other than ``<name>_id``, so the projection names the attname the field
    reports, beside the object-id column ``fk_field`` names.
    """

    class _RenamedTag(models.Model):
        ct: _RenamedKeyFK = _RenamedKeyFK(ContentType, on_delete=models.CASCADE, related_name="+")
        obj_id: models.IntegerField[float | int | str | Combinable, int] = models.IntegerField()
        target: GenericForeignKey = GenericForeignKey("ct", "obj_id")

        class Meta:
            app_label = "library"

    applied = apply_projection(_RenamedTag.objects.prefetch_related("target"), ["id"])

    assert applied.query.deferred_loading == (frozenset({"id", "ct_ref", "obj_id"}), False)


@pytest.mark.parametrize(
    ("deferred", "names", "remaining"),
    [
        pytest.param(("shelf", "subtitle"), ["shelf_id"], ["subtitle"], id="attname"),
        pytest.param(("shelf", "subtitle"), ["shelf__code"], ["subtitle"], id="dotted-read"),
        pytest.param(
            ("shelf__code", "shelf__topic"),
            ["shelf__code"],
            ["shelf__topic"],
            id="dotted-defer",
        ),
    ],
)
def test_merged_projection_defer_mode_matches_every_spelling_of_a_read_column(
    deferred: tuple[str, ...],
    names: list[str],
    remaining: list[str],
) -> None:
    """A consumer ``.defer()`` stops deferring a column the names read under any spelling.

    The live rows defer and read one column by its field name; these are the
    spellings no fakeshop row carries: the attname, a dotted read under the
    deferred relation, and a dotted ``.defer()`` entry.
    """
    assert merged_projection(Book.objects.defer(*deferred), names) == (remaining, True)


@pytest.mark.parametrize(
    ("entry", "loaded"),
    [
        pytest.param("category", True, id="name"),
        pytest.param("category_id", True, id="attname"),
        pytest.param("category__description", False, id="dotted-unread"),
        pytest.param("missing", False, id="unknown-field"),
        pytest.param("name__a", False, id="through-a-column"),
    ],
)
def test_loads_reads_an_entry_through_djangos_select_mask(entry: str, *, loaded: bool) -> None:
    """An entry is loaded under any spelling Django resolves; one it cannot resolve loads nothing.

    The read mask is ``.only("name", "category__name")``: the dotted read loads the
    ``category`` key column, not the related ``description``.
    """
    assert _loads(_select_mask(Item, ["name", "category__name"]), entry, Item) is loaded
