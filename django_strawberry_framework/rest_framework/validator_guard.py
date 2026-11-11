"""Keep DRF's validator call in control while guarding its actual ORM operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from django.db.models import Q, Value
from django.db.models.sql.query import Query
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.validators import (
    BaseUniqueForValidator,
    UniqueTogetherValidator,
    UniqueValidator,
)

from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    is_queryset,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_INVALID,
    UNBINDABLE_TEMPORAL_MESSAGE,
)

from .query_bind import guard_query

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_ValidatorT = TypeVar(
    "_ValidatorT",
    bound=UniqueValidator | UniqueTogetherValidator | BaseUniqueForValidator,
)

#: The ``against`` key under which ``_GuardInstaller`` reaches Django's check query.
_GUARD_ANNOTATION = "_dsf_validator_guard"


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

    def _refusal(name: str | None) -> DRFValidationError:
        if field_name is None:
            return DRFValidationError(
                UNBINDABLE_TEMPORAL_MESSAGE,
                code=FIELD_ERROR_CODE_INVALID,
            )
        return DRFValidationError(
            {name or field_name: [UNBINDABLE_TEMPORAL_MESSAGE]},
            code=FIELD_ERROR_CODE_INVALID,
        )

    provenance: list[tuple[object, object, str | None, str]] = []
    queryset = require(read_attr(validator, "queryset"), is_queryset).all()
    _ = guard_query(
        queryset.query,
        alias=alias,
        sources=sources,
        refusal=_refusal,
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
    refusal: Callable[[str | None], Exception],
    provenance: list[tuple[object, object, str | None, str]],
) -> Q:
    """Make DRF's combined conditional ``Q.check`` run Django's own body, guarded, on its alias.

    ``Q._combine`` creates the result through ``self.create``. Thus DRF's
    ``(condition & Exists(queryset.filter(condition))).check(against)`` retains this
    per-validator subtype. Its ``check`` calls the installed Django's ``Q.check`` on the
    pinned write alias, so that release's own body (its nullable-boolean handling, its
    ``DatabaseError`` reading) decides; a ``_GuardInstaller`` among ``against`` installs
    the per-query compiler guard on the query that body builds, before it adds the
    condition or compiles.
    """
    condition_type = type(condition)

    def _check(self: Q, against: Mapping[str, object], using: str = "default") -> bool:
        del using

        def _install(query: Query) -> Query:
            return guard_query(
                query,
                alias=alias,
                sources=sources,
                refusal=refusal,
                provenance=provenance,
            )

        installer = _GuardInstaller(_install)
        checked = condition_type.check(
            self,
            {_GUARD_ANNOTATION: installer, **against},
            using=alias,
        )
        # A body that never resolved the installer ran unguarded: fail loudly.
        _ = require_instance(installer.query, Query)
        return checked

    guarded_type = type(
        f"_Guarded{truth.name(condition_type)}",
        (condition_type,),
        {"check": _check},
    )
    guarded = condition.copy()
    guarded.__class__ = guarded_type  # truth: ok instance-local conditional query guard subtype
    return guarded


class _GuardInstaller:
    """An ``against`` value whose resolution guards the query Django's ``Q.check`` builds.

    Every supported Django ``Q.check`` resolves each ``against`` value on its fresh
    ``Query(None)`` (``add_annotation(..., select=False)``) before it adds the condition
    and compiles, so the guard sees both. The annotation it leaves is never selected and
    no condition names it.
    """

    def __init__(self, install: Callable[[Query], Query]) -> None:
        self.install: Callable[[Query], Query] = install
        self.query: Query | None = None

    def resolve_expression(self, query: Query, *args: object, **kwargs: object) -> Value:
        """Guard ``query`` and stand in as an inert, unselected annotation."""
        del args, kwargs
        self.query = self.install(query)
        return Value(None)
