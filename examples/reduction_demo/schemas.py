"""The demo schemas as importable module attributes.

``demo.py`` runs them; ``manage.py inspect_rules --schema schemas:reduced``
imports them. Django must be set up before this module is imported.
"""

from __future__ import annotations

import astronomy_declared.schema as declared_app
import astronomy_opaque.schema as opaque_app
import astronomy_reduced.schema as reduced_app
import suspension_reduced.schema as suspension_reduced_app
import suspension_restated.schema as suspension_restated_app
from astronomy_reduced.rules import StaffBypass
from suspension_reduced.rules import ActiveOnly

from django_strawberry_framework import DjangoOptimizerExtension, DjangoSchema
from django_strawberry_framework.extensions.visibility import DjangoVisibilityExplainExtension
from django_strawberry_framework.types.finalizer import finalize_django_types

finalize_django_types()


def build(query: type, **extra: object) -> DjangoSchema:
    """One schema per snapshot, each with its own optimizer and the explain extension."""
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=query,
        extensions=[lambda: optimizer, DjangoVisibilityExplainExtension],
        **extra,
    )


opaque = build(opaque_app.Query)
declared = build(declared_app.Query)
reduced = build(reduced_app.Query, visibility=[StaffBypass])
suspension_restated = build(suspension_restated_app.Query, visibility=[StaffBypass])
suspension_reduced = build(
    suspension_reduced_app.Query,
    visibility=[StaffBypass],
    restrictions=[ActiveOnly],
)
