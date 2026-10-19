"""GraphQL multipart request wire vocabulary, owned once for both transports.

The multipart request specification names exactly two control fields:
``operations``, carrying the operations document, and ``map``, carrying the
file map. Both package transports agree on those names by reading this module
- the test client emits them (see
``testing/client.py::_GraphQLTestClientBase._build_body``) and the view guards
them (see
``views.py::_RequestBodyBoundaryMixin._reject_lossy_multipart_control_fields``)
- so a specification rename lands in one place instead of two.

Upstream Strawberry's ``parse_multipart`` reads the same two literals on both
transports. That spelling lives in the installed dependency and cannot be owned
here; it stands as the independent backstop, alongside the test suites, which
spell the literals rather than importing them. A mistyped name here fails
against upstream's read and against the oracles instead of updating them.
"""

#: The multipart ``operations`` control field: the operations document.
_MULTIPART_OPERATIONS_FIELD = "operations"

#: The multipart ``map`` control field: the file map.
_MULTIPART_MAP_FIELD = "map"

#: The control fields that carry a JSON control document, as named by the multipart
#: request specification and read by upstream's ``parse_multipart`` on both
#: transports. Everything else in the form is a file payload Django's upload
#: handlers own.
_MULTIPART_CONTROL_FIELDS = (_MULTIPART_OPERATIONS_FIELD, _MULTIPART_MAP_FIELD)
