"""Declarative rules: a restricted language the framework can place, compare and enforce.

Prototype of whitepaper section 11 steps 1, 2, 3 and 4 on two rungs: read-side
visibility and declarative constraints. Public surface:

* :mod:`fragment` - ``Field`` / ``Actor`` terms, ``Rule``, canonical form,
  footprint, owner, and compilation to ``Q``.
* :mod:`apply` - the framework-owned ``get_queryset`` body that enforces
  declared rules (``Meta.visibility``, a model mixin's ``visibility``,
  ``DjangoSchema(visibility=...)``) with the cascade on by default.
* :mod:`audit` - the reduction report (R, M, D, I, B, opaque bodies) over
  visibility rules.
* :mod:`constraints` - the same report over ``Meta.constraints``, ``unique``,
  ``max_length``, ``choices`` and validators, plus ``ChoicesConstraint``, the
  derived ``CHECK`` for a field's choices.
"""

from .audit import Finding, Leaf, Report, Site, audit, render
from .constraints import ChoicesConstraint, audit_constraints, constraint_sites, predicate_from_q
from .fragment import (
    Actor,
    And,
    Compare,
    Field,
    Length,
    Not,
    Or,
    Owner,
    Predicate,
    Rule,
    Rung,
    Term,
    Unique,
    canonical,
    evaluate,
    footprint,
    leaves,
    owner,
)

__all__ = [
    "Actor",
    "And",
    "ChoicesConstraint",
    "Compare",
    "Field",
    "Finding",
    "Leaf",
    "Length",
    "Not",
    "Or",
    "Owner",
    "Predicate",
    "Report",
    "Rule",
    "Rung",
    "Site",
    "Term",
    "Unique",
    "audit",
    "audit_constraints",
    "canonical",
    "constraint_sites",
    "evaluate",
    "footprint",
    "leaves",
    "owner",
    "predicate_from_q",
    "render",
]
