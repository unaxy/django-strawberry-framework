"""Keep DRF's validator call in control while guarding its actual ORM operations."""

from __future__ import annotations

import logging
from contextlib import nullcontext
from typing import TYPE_CHECKING, TypeVar

import django
from django.db import DatabaseError, connections, transaction
from django.db.models import BooleanField, Q, Value
from django.db.models.functions import Coalesce
from django.db.models.sql.constants import SINGLE
from django.db.models.sql.query import Query
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.validators import (
    BaseUniqueForValidator,
    UniqueTogetherValidator,
    UniqueValidator,
)

from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    call_method,
    is_queryset,
    read_attr,
    require,
)
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_INVALID,
    UNBINDABLE_TEMPORAL_MESSAGE,
)
from django_strawberry_framework.utils.typing import object_result

from .query_bind import guard_query

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_ValidatorT = TypeVar("_ValidatorT")


def guard_uniqueness_validator(
    validator: _ValidatorT,
    *,
    alias: str,
    field_name: str | None,
    sources: Mapping[str, str],
) -> _ValidatorT:
    """Guard one copied, alias-pinned validator without replacing its ``__call__``.

    The validator's original method owns defaults, required, changed and null
    decisions. The copied queryset's query keeps a local compiler guard through
    ``Query.clone``. DRF's original validator-list position and context are intact.
    """
    if not isinstance(
        validator,
        UniqueValidator | UniqueTogetherValidator | BaseUniqueForValidator,
    ):
        return validator

    def _refusal(name: str | None) -> None:
        if field_name is None:
            raise DRFValidationError(
                UNBINDABLE_TEMPORAL_MESSAGE,
                code=FIELD_ERROR_CODE_INVALID,
            )
        raise DRFValidationError(
            {name or field_name: [UNBINDABLE_TEMPORAL_MESSAGE]},
            code=FIELD_ERROR_CODE_INVALID,
        )

    provenance: list[tuple[object, object, str | None, str]] = []
    queryset = require(read_attr(validator, "queryset"), is_queryset).all()
    _ = guard_query(
        queryset.query,
        alias=alias,
        sources=sources,
        refuse=_refusal,
        provenance=provenance,
    )
    validator.queryset = queryset

    if isinstance(validator, UniqueTogetherValidator):
        condition = read_attr(validator, "condition", None)
        if isinstance(condition, Q):
            validator_object: object = validator
            object.__setattr__(
                validator_object,
                "condition",
                _guarded_condition(condition, alias, sources, _refusal, provenance),
            )
    return validator


def _guarded_condition(
    condition: Q,
    alias: str,
    sources: Mapping[str, str],
    refuse: Callable[[str | None], None],
    provenance: list[tuple[object, object, str | None, str]],
) -> Q:
    """Make DRF's combined conditional ``Q.check`` use its pinned write alias.

    ``Q._combine`` creates the result through ``self.create``. Thus DRF's
    ``(condition & Exists(queryset.filter(condition))).check(against)`` retains this
    per-validator subtype, including the local compiler guard.
    """
    condition_type = type(condition)

    def _check(self: Q, against: Mapping[str, object], using: str = "default") -> bool:
        del using
        return _checked_q_check(self, against, alias, sources, refuse, provenance)

    guarded_type = type(
        f"_Guarded{truth.name(condition_type)}",
        (condition_type,),
        {"check": _check},
    )
    guarded = condition.copy()
    guarded.__class__ = guarded_type  # truth: ok instance-local conditional query guard subtype
    return guarded


def _checked_q_check(
    condition: Q,
    against: Mapping[str, object],
    alias: str,
    sources: Mapping[str, str],
    refuse: Callable[[str | None], None],
    provenance: list[tuple[object, object, str | None, str]],
) -> bool:
    """Run Django's ``Q.check`` once on the pinned alias with guarded compilation.

    Adapted from Django ``django/db/models/query_utils.py::Q.check`` (BSD-3-Clause;
    ``LICENSE.django``). Django exposes ``using`` but no injection seam between
    constructing its new ``Query(None)`` and executing it. This narrow adaptation
    installs the per-query compiler guard there; the rest is Django's own body.
    """
    query = guard_query(
        Query(None),
        alias=alias,
        sources=sources,
        refuse=refuse,
        provenance=provenance,
    )
    for name, value in against.items():
        expression = value if hasattr(value, "resolve_expression") else Value(value)
        query.add_annotation(expression, name, select=False)
    query.add_annotation(Value(1), "_check")
    connection = connections[alias]
    # Django 5.2/6.0 Q.check wraps a nullable boolean expression before adding
    # it; 6.1 removes that wrapper. Keep each supported upstream body here.
    if django.VERSION < (6, 1) and connection.features.supports_comparing_boolean_expr:
        query.add_q(Q(Coalesce(condition, Value(value=True), output_field=BooleanField())))
    else:
        query.add_q(condition)
    compiler = object_result(query.get_compiler, using=alias)
    context_manager = (
        transaction.atomic(using=alias) if connection.in_atomic_block else nullcontext()
    )
    try:
        with context_manager:
            return call_method(compiler, "execute_sql", SINGLE) is not None
    except DatabaseError as exc:
        logging.getLogger("django.db.models").warning(
            "Got a database error calling check() on %r: %s",
            condition,
            exc,
        )
        return True
