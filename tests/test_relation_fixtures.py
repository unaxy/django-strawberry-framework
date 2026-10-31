"""The composite relation fixture drops its unmanaged tables after use.

Native composite-parent queries and crossed-carrier controls live in
``examples/fakeshop/test_query/test_mti_composite_relations_api.py``. This file
keeps the fixture's cleanup contract: a table query fails after context exit,
an observation the HTTP response cannot expose.
"""

import pytest
from django.db import connection
from django.db.utils import DatabaseError

from tests._relation_fixtures import (
    RpCompositeParent,
    relation_fixture_tables,
)


@pytest.mark.django_db(transaction=True)
def test_fixture_tables_are_dropped_on_exit() -> None:
    """Fixture smoke: after the context exits the tables are gone (no residue).

    No live request can express this: ``schema_editor.delete_model`` is
    test-DB hygiene, not a GraphQL wire shape. Rungs 1-3 have nothing to post.
    """
    with relation_fixture_tables(connection):
        RpCompositeParent.objects.create(tenant_id=1, code="ALPHA", label="A")

    # A missing relation raises a vendor-specific error -- ``OperationalError``
    # on SQLite, ``ProgrammingError`` (42P01) on PostgreSQL -- so assert their
    # common ``DatabaseError`` ancestor to stay green on both tiers.
    with pytest.raises(DatabaseError):
        RpCompositeParent.objects.count()
