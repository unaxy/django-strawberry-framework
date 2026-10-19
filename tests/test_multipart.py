"""Pin for the GraphQL multipart wire vocabulary pair.

The ``operations`` / ``map`` control-field names live in
``django_strawberry_framework/_multipart.py``; the pair the view guard and
the test client read is the two named fields, never a second spelling of
the names. The values themselves stay pinned by the suites that spell the
literals - the client unit rows, the view rows, the live hand-built
multipart rows, and upstream's own read - never by this file.
"""

from django_strawberry_framework._multipart import (
    _MULTIPART_CONTROL_FIELDS,
    _MULTIPART_MAP_FIELD,
    _MULTIPART_OPERATIONS_FIELD,
)


def test_control_fields_pair_derives_from_the_named_fields() -> None:
    """The pair is the two named fields, never a second spelling of the names."""
    assert _MULTIPART_CONTROL_FIELDS == (_MULTIPART_OPERATIONS_FIELD, _MULTIPART_MAP_FIELD)
