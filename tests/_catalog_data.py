"""Select and reshape saved catalog rows produced by the product service seed.

Call ``apps.products.services.seed_data(N)`` at the start of the test before either
helper. ``N`` must cover the largest item group requested for one category. These
helpers never create models: they keep deterministic existing rows, remove surplus
seed rows, and update the retained rows to make each test's graph explicit.
"""

from apps.products.models import Category, Item

from tests._idioms import saved_pk


def categories_from_seed(*rows: tuple[str, bool]) -> list[Category]:
    """Keep one seeded category per ``(name, is_private)`` pair, in primary-key order."""
    categories = list(Category.objects.order_by("pk")[: len(rows)])
    assert len(categories) == len(rows), "seed_data must create every requested category"
    Category.objects.exclude(pk__in=[saved_pk(category) for category in categories]).delete()
    for category, (name, is_private) in zip(categories, rows, strict=True):
        Category.objects.filter(pk=saved_pk(category)).update(name=name, is_private=is_private)
        category.refresh_from_db()
    return categories


def items_from_seed(category: Category, *rows: tuple[str, bool]) -> list[Item]:
    """Keep seeded children of ``category`` as the requested ``(name, is_private)`` pairs."""
    items = list(category.items.order_by("pk")[: len(rows)])
    assert len(items) == len(rows), "seed_data(N) must cover the requested item group"
    category.items.exclude(pk__in=[saved_pk(item) for item in items]).delete()
    for item, (name, is_private) in zip(items, rows, strict=True):
        Item.objects.filter(pk=saved_pk(item)).update(name=name, is_private=is_private)
        item.refresh_from_db()
    return items
