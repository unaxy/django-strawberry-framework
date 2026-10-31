"""Shared PostgreSQL periodical fixture rows for HTTP paging and internal EXPLAIN tests."""

from collections.abc import Sequence

from apps.library.models import Issue, Periodical
from django.db.models import Model


def _seed_periodicals() -> Sequence[Model]:
    populated = Periodical.objects.create(name="populated")
    sparse = Periodical.objects.create(name="sparse")
    Periodical.objects.create(name="empty")
    issues = [
        Issue.objects.create(periodical=populated, number=number, title=f"p{number}")
        for number in range(1, 6)
    ]
    for number in range(1, 4):
        Issue.objects.create(periodical=sparse, number=number, title=f"s{number}")
    return issues
