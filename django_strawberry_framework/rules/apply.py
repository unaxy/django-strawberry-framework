"""Enforcement of declared visibility rules (the framework-owned ``get_queryset`` body).

``DjangoType.get_queryset``'s default now calls :func:`apply_declared_visibility`.
Every type, rules or not, is subject first to the schema's restrictions
(``DjangoSchema(restrictions=[...])``): actor-only rules that must all hold, or
nothing is visible. They sit above the bypasses, so a bypass cannot grant what
a restriction denies. Past them, a type with no declared rules anywhere (none
on the type, none on its model's bases, no ``Meta.cascade``) keeps the identity
behaviour it always had, so no existing consumer changes. A type with rules
gets, in order:

1. the schema's bypasses (``DjangoSchema(visibility=[...])``): actor-only rules;
   the first one that holds returns the queryset untouched;
2. every rule declared on the type (``Meta.visibility``) and on the model's
   bases (a ``visibility = (...)`` attribute on an abstract mixin), ANDed;
3. the forward-FK cascade, on by default once rules are declared, off with
   ``Meta.cascade = False``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import models

from django_strawberry_framework.rules.fragment import Rule, canonical, evaluate

if TYPE_CHECKING:
    from django_strawberry_framework.types.base import DjangoType

__all__ = [
    "actor_from_info",
    "apply_declared_visibility",
    "model_rule_sites",
    "schema_bypasses",
    "schema_restrictions",
    "type_rules",
]


def type_rules(type_cls: type[DjangoType]) -> tuple[Rule, ...]:
    """Rules declared on the type itself via ``Meta.visibility``."""
    return tuple(getattr(type_cls, "__visibility_rules__", ()))


def model_rule_sites(model: type[models.Model]) -> tuple[tuple[type[models.Model], Rule], ...]:
    """``(declaring_class, rule)`` for every ``visibility`` attribute on the model's MRO.

    The declaring class is the authored site. Two concrete models inheriting
    one abstract mixin share one site; the framework applies its rules to both
    as derived copies.
    """
    out: list[tuple[type[models.Model], Rule]] = []
    for base in model.__mro__:
        declared = base.__dict__.get("visibility")
        if declared is None or not (isinstance(base, type) and issubclass(base, models.Model)):
            continue
        if not isinstance(declared, (list, tuple)):
            # A model *field* named ``visibility`` (a descriptor here), not a rule tuple.
            continue
        for rule in declared:
            if not isinstance(rule, Rule):
                raise TypeError(f"{base.__name__}.visibility must hold Rule objects, got {rule!r}")
            out.append((base, rule))
    return tuple(out)


def _schema_rules(info: object, attr: str) -> tuple[Rule, ...]:
    try:
        schema = getattr(info, "schema", None)
    except Exception:  # a fake ``info`` without a raw schema
        return ()
    # A Strawberry ``Info`` answers with the Strawberry schema; a raw graphql-core
    # ``GraphQLResolveInfo`` (what the optimizer's nested walk carries) answers
    # with the ``GraphQLSchema``, which points back at it.
    schema = getattr(schema, "_strawberry_schema", schema)
    return tuple(getattr(schema, attr, ()) or ())


def schema_bypasses(info: object) -> tuple[Rule, ...]:
    """The schema-wide bypass rules reachable from ``info.schema``, or none."""
    return _schema_rules(info, "visibility")


def schema_restrictions(info: object) -> tuple[Rule, ...]:
    """The schema-wide restriction rules reachable from ``info.schema``, or none."""
    return _schema_rules(info, "restrictions")


def actor_from_info(info: object) -> object:
    """The acting user, or ``None`` when the context carries no request/user."""
    from django_strawberry_framework.utils.permissions import _request_from_context

    context: object = getattr(info, "context", None)
    if context is None:
        return None
    request = _request_from_context(context)
    return getattr(request, "user", None)


def apply_declared_visibility(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[Any, Any],  # pyright: ignore[reportExplicitAny]
    info: object,
) -> models.QuerySet[Any, Any]:  # pyright: ignore[reportExplicitAny]
    """Filter ``queryset`` by every rule declared for ``type_cls``; see the module docstring."""
    from django_strawberry_framework.extensions.visibility import record
    from django_strawberry_framework.permissions import apply_cascade_permissions
    from django_strawberry_framework.utils.querysets import model_for

    # The canonical form is what the audit compares, so it is also what runs:
    # the authored and the enforced predicate must be one object.
    actor = actor_from_info(info)
    for rule in schema_restrictions(info):
        if evaluate(canonical(rule.predicate), actor) is not True:
            record({"type": type_cls.__name__, "restriction": rule.name, "site": "schema"})
            return queryset.none()
    if not type_cls.__declares_visibility__:
        return queryset

    own = type_rules(type_cls)
    inherited = model_rule_sites(model_for(type_cls))
    cascade = getattr(type_cls, "__cascade__", None)
    for rule in schema_bypasses(info):
        if evaluate(canonical(rule.predicate), actor) is True:
            record({"type": type_cls.__name__, "bypass": rule.name, "site": "schema"})
            return queryset

    applied: list[dict[str, object]] = []
    sites = [(type_cls.__name__, rule) for rule in own] + [
        (base.__name__, rule) for base, rule in inherited
    ]
    for site, rule in sites:
        verdict = evaluate(canonical(rule.predicate), actor)
        if verdict is True:
            applied.append({"rule": rule.name, "site": site, "effect": "no filter"})
            continue
        if verdict is False:
            applied.append({"rule": rule.name, "site": site, "effect": "nothing visible"})
            queryset = queryset.none()
            break
        applied.append({"rule": rule.name, "site": site, "effect": str(verdict)})
        queryset = queryset.filter(verdict)

    if cascade is not False:
        queryset = apply_cascade_permissions(type_cls, queryset, info)
    record(
        {
            "type": type_cls.__name__,
            "rules": applied,
            "cascade": "framework default" if cascade is None else cascade,
        },
    )
    return queryset
