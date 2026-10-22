"""The L0 rung: declarative constraints, where each is authored, and whether the DB holds it.

Second rung of the whitepaper prototype (section 11 step 3). The same fragment
and the same audit, pointed at ``Meta.constraints``, ``unique=True``,
``max_length``, ``choices`` and field validators instead of visibility rules.
Each declaration is read into the fragment and placed:

* a ``CheckConstraint`` over field lookups, a ``UniqueConstraint`` over fields,
  ``unique=True`` and ``unique_together`` are authored at **L0**, the rung the
  application cannot bypass (a ``CharField`` ``max_length`` is the column's
  type, ``varchar(n)``, and so a declaration rather than a rule: not read);
* ``choices``, a ``TextField`` ``max_length`` and a validator are authored at
  **L1**, the field. Their owner is L0 whenever the DB can express the leaf
  (everything but a regex), so a validator with no DB form beside it is
  *stated too high*;
* a ``ChoicesConstraint`` is a **derived** copy: the ``CHECK`` the framework
  builds from ``choices``. It counts zero and it satisfies the owner, so
  ``choices`` plus ``ChoicesConstraint`` is one authored leaf held at L0.
  Django's ``validate_constraints`` is the derivation in the other direction
  (a Python check from a ``CheckConstraint``), which is why a lone
  ``CheckConstraint`` needs no validator beside it;
* a ``clean()`` body, a constraint over an expression and a validator the
  fragment does not know are **opaque**: counted in O, never placed.

M on this rung counts a leaf whose owner holds no copy of it, authored or
derived. D is structurally zero: the database refuses two constraints with one
name.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core import validators as dj_validators
from django.core.checks import CheckMessage
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models import F, Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.db.models.signals import class_prepared

from django_strawberry_framework.rules.audit import (
    Leaf,
    Report,
    Site,
    _report_duplicates,
    _report_misplaced,
)
from django_strawberry_framework.rules.fragment import (
    And,
    Compare,
    Field,
    Length,
    Not,
    Op,
    Or,
    Owner,
    Predicate,
    Rule,
    Rung,
    Unique,
    _declaring_class,
    canonical,
    footprint,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable

__all__ = [
    "Authored",
    "ChoicesConstraint",
    "OpaqueError",
    "audit_constraints",
    "constraint_sites",
    "predicate_from_q",
]


class ChoicesConstraint(CheckConstraint):
    """A ``CHECK (field IN choices)`` derived from the field's own ``choices``.

    ``Meta.constraints = [ChoicesConstraint("status", name="...")]`` states the
    membership rule once, on the field, and the DB form is generated from it:
    a derived copy in the whitepaper's sense, counted zero by the audit. A
    blank-admitting field admits ``""`` as well.
    """

    def __init__(
        self,
        field: str,
        *,
        name: str,
        condition: Q | None = None,
        violation_error_code: str | None = None,
        violation_error_message: str | None = None,
    ) -> None:
        self.field = field
        # ``condition`` is given only by a migration replaying the frozen
        # derivation; a live declaration resolves it when its class is prepared
        # (``_bind``), so ``deconstruct`` and ``==`` see the derived ``Q`` and a
        # change to the choices is a change to the constraint, which the
        # migration autodetector then emits. Without that the DB copy went
        # stale silently: the CHECK kept the old members and the audit still
        # said "held at L0".
        super().__init__(
            condition=Q() if condition is None else condition,
            name=name,
            violation_error_code=violation_error_code,
            violation_error_message=violation_error_message,
        )

    def condition_for(self, model: type[models.Model]) -> Q:
        """The membership ``Q`` read off ``model``'s field right now."""
        return Q(**{f"{self.field}__in": allowed_choices(model._meta.get_field(self.field))})

    @classmethod
    def _bind(cls, sender: type[models.Model], **_kwargs: object) -> None:
        """``class_prepared`` receiver: resolve every ``ChoicesConstraint`` on ``sender``."""
        for constraint in getattr(sender._meta, "constraints", ()):
            if isinstance(constraint, cls):
                constraint.condition = constraint.condition_for(sender)

    def check(self, model: type[models.Model], connection: object) -> list[CheckMessage]:
        """Django's system check, against the derived condition."""
        self.condition = self.condition_for(model)
        return super().check(model, connection)

    def _get_check_sql(self, model: type[models.Model], schema_editor: object) -> str:
        self.condition = self.condition_for(model)
        return super()._get_check_sql(model, schema_editor)

    def validate(
        self,
        model: type[models.Model],
        instance: models.Model,
        exclude: Collection[str] | None = None,
        using: str = DEFAULT_DB_ALIAS,
    ) -> None:
        """``full_clean`` support, against the derived condition."""
        self.condition = self.condition_for(model)
        super().validate(model, instance, exclude=exclude, using=using)

    def deconstruct(self) -> tuple[str, tuple[object, ...], dict[str, object]]:
        """``ChoicesConstraint(field, name=..., condition=<derived Q>)``, the derivation frozen.

        Equality is ``CheckConstraint``'s, over the condition, so a migration
        holding yesterday's members differs from today's declaration.
        """
        path, args, kwargs = super().deconstruct()
        return path, (self.field, *args), kwargs


class_prepared.connect(
    ChoicesConstraint._bind,
    weak=False,
    dispatch_uid="rules.choices_constraint",
)


def allowed_choices(field: models.Field) -> tuple[object, ...]:
    """The values ``field`` admits: its flat choices, plus ``""`` when it is blank-admitting."""
    values = [value for value, _label in field.flatchoices]
    if field.blank and "" not in values and not isinstance(field, models.BooleanField):
        values.append("")
    return tuple(values)


class OpaqueError(ValueError):
    """A declaration the fragment cannot read."""


_LOOKUPS: dict[str, Op] = {
    "exact": Op.EQ,
    "gt": Op.GT,
    "gte": Op.GTE,
    "lt": Op.LT,
    "lte": Op.LTE,
    "in": Op.IN,
    "regex": Op.REGEX,
}


def _compare_from_lookup(key: str, value: object) -> Predicate:
    segments = key.split("__")
    op = Op.EQ
    isnull: bool | None = None
    if segments[-1] in _LOOKUPS:
        op = _LOOKUPS[segments.pop()]
    elif segments[-1] == "isnull":
        segments.pop()
        isnull = bool(value)
    term: Field
    if len(segments) > 1 and segments[-1] == "length":
        term = Length("__".join(segments[:-1]))
    else:
        term = Field("__".join(segments))
    if isnull is not None:
        null = term.eq(None)
        return null if isnull else Not(null)
    if isinstance(value, F):
        value = Field(value.name)
    elif isinstance(value, models.Expression):
        raise OpaqueError(f"{key}={value!r} compares against an expression")
    return Compare(term, op, value)


def predicate_from_q(q: Q) -> Predicate:
    """Read a ``Q`` of field lookups into the fragment; ``OpaqueError`` when it holds an expression."""
    parts: list[Predicate] = []
    for child in q.children:
        if isinstance(child, Q):
            parts.append(predicate_from_q(child))
        elif isinstance(child, tuple) and len(child) == 2:
            parts.append(_compare_from_lookup(*child))
        else:
            raise OpaqueError(f"{child!r} is an expression, not a field lookup")
    if not parts:
        raise OpaqueError("an empty Q constrains nothing")
    if q.connector == Q.XOR:
        raise OpaqueError("XOR is parity over its operands, not a junction the fragment has")
    pred = parts[0] if len(parts) == 1 else (And if q.connector == Q.AND else Or)(tuple(parts))
    return Not(pred) if q.negated else pred


@dataclass(frozen=True)
class Authored:
    """One declaration: where it was written, at which rung, and what it says."""

    label: str
    name: str
    model: type[models.Model]
    rung: Rung
    leaf: Predicate | None = None
    derived: bool = False
    opaque: str | None = None


def _constraint_leaf(constraint: object, model: type[models.Model]) -> tuple[Predicate, bool]:
    """``(leaf, derived)`` for a ``Meta.constraints`` entry; ``OpaqueError`` when unreadable."""
    if isinstance(constraint, ChoicesConstraint):
        return Field(constraint.field).in_(
            allowed_choices(model._meta.get_field(constraint.field)),
        ), True
    if isinstance(constraint, CheckConstraint):
        if not isinstance(constraint.condition, Q):
            raise OpaqueError("condition is an expression")
        return predicate_from_q(constraint.condition), False
    if isinstance(constraint, UniqueConstraint):
        if constraint.expressions or not constraint.fields:
            raise OpaqueError("unique over expressions")
        condition = (
            None if constraint.condition is None else predicate_from_q(constraint.condition)
        )
        return Unique(
            tuple(constraint.fields),
            condition,
            getattr(constraint, "nulls_distinct", None),
            constraint.deferrable is not None,
        ), False
    raise OpaqueError(f"{type(constraint).__name__} is not a constraint the fragment reads")


def _validator_leaf(field: models.Field, validator: object) -> Predicate:
    term = Field(field.name)
    limit = getattr(validator, "limit_value", None)
    if isinstance(validator, dj_validators.MinLengthValidator):
        return term.length().gte(limit)
    if isinstance(validator, dj_validators.MaxLengthValidator):
        return term.length().lte(limit)
    if isinstance(validator, dj_validators.MinValueValidator):
        return term.gte(limit)
    if isinstance(validator, dj_validators.MaxValueValidator):
        return term.lte(limit)
    if isinstance(validator, dj_validators.RegexValidator):
        pattern = (
            validator.regex.pattern if hasattr(validator.regex, "pattern") else validator.regex
        )
        leaf = term.regex(str(pattern))
        return Not(leaf) if validator.inverse_match else leaf
    raise OpaqueError(f"validators[{type(validator).__name__}]")


def _together(option: object) -> tuple[object, ...]:
    """``unique_together`` as a tuple of field tuples (Django also accepts one flat tuple)."""
    members = tuple(option) if isinstance(option, (list, tuple)) else ()
    if members and isinstance(members[0], str):
        return (members,)
    return members


def _authored_members(base: type[models.Model], option: str) -> list[object]:
    """The members of the ``Meta`` option ``base`` wrote itself.

    ``class Child(Base): pass`` runs on ``Base``'s own ``Meta`` object,
    ``class Meta(Base.Meta)`` inherits what it does not name, and a child that
    adds a constraint must spread ``*Base.Meta.constraints`` because Django
    replaces the option rather than merging it. Django records all three in
    ``original_attrs`` as if the child had written them, holding the very
    objects the ancestor's ``Meta`` holds. Each is a derived copy here: a
    member is authored at ``base`` only when no ancestor's ``original_attrs``
    carries that same object.
    """
    members = base._meta.original_attrs.get(option, ())
    own = _together(members) if option == "unique_together" else tuple(members)
    inherited = {
        id(member)
        for ancestor in base.__mro__[1:]
        if issubclass(ancestor, models.Model) and ancestor is not models.Model
        for member in (
            _together(ancestor._meta.original_attrs.get(option, ()))
            if option == "unique_together"
            else tuple(ancestor._meta.original_attrs.get(option, ()))
        )
    }
    return [member for member in own if id(member) not in inherited]


def _meta_sites(base: type[models.Model], out: list[Authored]) -> None:
    # An abstract base keeps the raw ``%(app_label)s_%(class)s`` name that
    # Django interpolates per concrete class; here the base is the one site.
    names = {"app_label": (base._meta.app_label or "").lower(), "class": base.__name__.lower()}
    for constraint in _authored_members(base, "constraints"):
        assert isinstance(constraint, models.BaseConstraint)
        name = constraint.name % names if "%(" in constraint.name else constraint.name
        label = f"{base.__name__}.Meta.constraints[{name}]"
        try:
            leaf, derived = _constraint_leaf(constraint, base)
        except OpaqueError as exc:
            out.append(Authored(label, name, base, Rung.L0_DB, opaque=str(exc)))
        else:
            out.append(Authored(label, name, base, Rung.L0_DB, leaf, derived))
    for fields in _authored_members(base, "unique_together"):
        assert isinstance(fields, (list, tuple))
        name = "unique_together_" + "_".join(fields)
        out.append(
            Authored(
                f"{base.__name__}.Meta.unique_together",
                name,
                base,
                Rung.L0_DB,
                Unique(tuple(fields)),
            ),
        )


def _field_sites(field: models.Field, declaring: type[models.Model], out: list[Authored]) -> None:
    label = f"{declaring.__name__}.{field.name}"
    term = Field(field.name)
    # ``deconstruct`` keeps only what the author wrote: a ``OneToOneField``'s
    # implied ``unique``, a ``UUIDField``'s ``max_length=32`` and a
    # ``FileField``'s default 100 are the field type's, not a restatement.
    authored = field.deconstruct()[3]
    if authored.get("unique") and not field.primary_key:
        out.append(
            Authored(
                f"{label} unique=True",
                f"{field.name}_unique",
                declaring,
                Rung.L0_DB,
                Unique((field.name,)),
            ),
        )
    if "max_length" in authored and isinstance(field, models.TextField):
        # A ``CharField`` ``max_length`` is the column type (``varchar(n)``): a
        # declaration, not a rule, where SQL-92 files length, precision and
        # scale. On a ``TextField`` it reaches no column type and no model
        # validator either; only the form and serializer fields derive it: a
        # rule, authored at L1 with no copy below.
        out.append(
            Authored(
                f"{label} max_length",
                f"{field.name}_max_length",
                declaring,
                Rung.L1_FIELD,
                term.length().lte(authored["max_length"]),
            ),
        )
    if authored.get("choices"):
        out.append(
            Authored(
                f"{label} choices",
                f"{field.name}_choices",
                declaring,
                Rung.L1_FIELD,
                term.in_(allowed_choices(field)),
            ),
        )
    out.extend(
        _validator_site(field, validator, declaring, label)
        for validator in authored.get("validators", ())
    )


def _validator_site(
    field: models.Field,
    validator: object,
    declaring: type[models.Model],
    label: str,
) -> Authored:
    kind = type(validator).__name__
    try:
        leaf = _validator_leaf(field, validator)
    except OpaqueError as exc:
        return Authored(
            f"{label} {exc}",
            f"{field.name}_{kind}",
            declaring,
            Rung.L1_FIELD,
            opaque=str(exc),
        )
    return Authored(
        f"{label} validators[{kind}]",
        f"{field.name}_{kind}",
        declaring,
        Rung.L1_FIELD,
        leaf,
    )


_PURE_CALLS = frozenset(
    {
        "super",
        "len",
        "str",
        "int",
        "float",
        "bool",
        "set",
        "list",
        "tuple",
        "dict",
        "sorted",
        "min",
        "max",
        "getattr",
        "setattr",
        "isinstance",
        "repr",
    },
)


def _can_refuse(clean: Callable[..., object]) -> bool:
    """Whether a ``clean()`` body can reject a row, read from its syntax tree.

    A body that only normalises (``AbstractBaseUser.clean`` lower-cases the
    username) never raises, so it holds no rule and is not opaque. A body
    refuses when it raises, names ``ValidationError``, or calls a function by
    bare name other than a builtin: the helper's body is not read, so it is
    taken to be where the raise went. A docstring saying "raise" is prose.
    """
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(clean)))
    except (OSError, TypeError, SyntaxError):
        return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.Name) and node.id == "ValidationError":
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id not in _PURE_CALLS
        ):
            return True
    return False


def constraint_sites(
    model: type[models.Model],
    seen: set[tuple[type, str]] | None = None,
) -> list[Authored]:
    """Every declaration reaching ``model``, each attributed to the class that authored it.

    ``seen`` dedupes across models: an abstract base's constraint or field is
    one authored site however many concrete models inherit it.
    """
    seen = set() if seen is None else seen
    out: list[Authored] = []
    for base in model.__mro__:
        if not (isinstance(base, type) and issubclass(base, models.Model)) or base is models.Model:
            continue
        if (base, "meta") not in seen:
            seen.add((base, "meta"))
            _meta_sites(base, out)
        if "clean" in base.__dict__ and (base, "clean") not in seen:
            seen.add((base, "clean"))
            if not _can_refuse(base.__dict__["clean"]):
                continue  # a normaliser (``AbstractBaseUser.clean``), not a rule
            out.append(
                Authored(
                    f"{base.__name__}.clean",
                    "clean",
                    base,
                    Rung.L2_ROW,
                    opaque="hand-written body",
                ),
            )
    for field in model._meta.local_fields:
        declaring = _declaring_class(model, {field.name})
        if (declaring, field.name) in seen:
            continue
        seen.add((declaring, field.name))
        _field_sites(field, declaring, out)
    return out


def _db_can_express(leaf: Predicate) -> bool:
    if isinstance(leaf, Compare):
        return leaf.op is not Op.REGEX
    if isinstance(leaf, Not):
        return _db_can_express(leaf.operand)
    if isinstance(leaf, Unique):
        return leaf.condition is None or _db_can_express(leaf.condition)
    return all(_db_can_express(p) for p in leaf.operands)


def _owner(leaf: Predicate, model: type[models.Model]) -> Owner:
    names = {t.path for t in footprint(leaf) if isinstance(t, Field)}
    rung = Rung.L0_DB if _db_can_express(leaf) else Rung.L1_FIELD
    return Owner(scope="model", rung=rung, model=_declaring_class(model, names))


def audit_constraints(models_: Iterable[type[models.Model]]) -> Report:
    """Audit every declarative constraint on ``models_`` for placement and multiplicity."""
    report = Report(opaque_kind="constraint bodies", invocation_kind=None)
    seen: set[tuple[type, str]] = set()
    sites: list[Authored] = []
    for model in models_:
        sites.extend(constraint_sites(model, seen))

    held: set[tuple[str, tuple[object, ...], Rung]] = set()
    placed: list[tuple[Authored, Predicate, Owner]] = []
    for site in sites:
        if site.leaf is None:
            report.opaque.append((site.label, 0))
            continue
        leaf = canonical(site.leaf)
        owner = _owner(leaf, site.model)
        if site.derived or (site.rung is owner.rung and site.model is owner.model):
            held.add((repr(leaf), owner.key, owner.rung))
        if not site.derived:
            placed.append((site, leaf, owner))

    for site, leaf, owner in placed:
        authored_at = Site(site.label, Owner(scope="model", rung=site.rung, model=site.model))
        report.leaves.append(
            Leaf(
                Rule(site.name, leaf),
                leaf,
                authored_at,
                owner,
                split=False,
                rung_sensitive=True,
                held_at_owner=(repr(leaf), owner.key, owner.rung) in held,
            ),
        )
    _report_misplaced(report, report.leaves)
    _report_duplicates(report, report.leaves)
    return report
