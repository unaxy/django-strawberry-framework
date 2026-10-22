"""The restricted visibility-rule language (whitepaper section 9, "the fragment").

A rule is data, not a callable, so the framework can answer three questions a
``get_queryset`` body cannot be asked:

* **footprint** - which row fields, relation paths and actor attributes the
  predicate reads (its free variables);
* **owner** - the tightest scope on the ladder that covers that footprint
  and whose composition law admits it (computed, never chosen);
* **equality** - whether two rules are the same leaf, after canonicalization.

The fragment is deliberately small: comparisons over a row field path or an
actor attribute, boolean structure, constants. No user-defined functions in
leaves. The same predicate also compiles to a Django ``Q`` for enforcement, so
the authored rule and the enforced rule are one object.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import F, Q

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

__all__ = [
    "Actor",
    "And",
    "Compare",
    "Field",
    "Length",
    "Not",
    "Op",
    "Or",
    "Owner",
    "Predicate",
    "Rule",
    "Rung",
    "Term",
    "Unique",
    "canonical",
    "evaluate",
    "footprint",
    "leaves",
    "owner",
]


class Op(str, Enum):
    """Comparison operators the fragment admits."""

    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"


_LOOKUP: dict[Op, str] = {
    Op.EQ: "exact",
    Op.LT: "lt",
    Op.LTE: "lte",
    Op.GT: "gt",
    Op.GTE: "gte",
    Op.IN: "in",
    Op.REGEX: "regex",
}


# --------------------------------------------------------------------------- terms


class _Comparable:
    """Comparison constructors shared by both term kinds."""

    def _compare(self, op: Op, value: object) -> Compare:
        return Compare(self, op, value)  # type: ignore[arg-type]

    def eq(self, value: object) -> Compare:
        """``term == value``."""
        return self._compare(Op.EQ, value)

    def ne(self, value: object) -> Compare:
        """``term != value``."""
        return self._compare(Op.NE, value)

    def lt(self, value: object) -> Compare:
        """``term < value``."""
        return self._compare(Op.LT, value)

    def lte(self, value: object) -> Compare:
        """``term <= value``."""
        return self._compare(Op.LTE, value)

    def gt(self, value: object) -> Compare:
        """``term > value``."""
        return self._compare(Op.GT, value)

    def gte(self, value: object) -> Compare:
        """``term >= value``."""
        return self._compare(Op.GTE, value)

    def in_(self, values: Iterable[object]) -> Compare:
        """``term in values``."""
        return self._compare(Op.IN, tuple(values))

    def is_true(self) -> Compare:
        """``term == True``."""
        return self.eq(True)

    def is_false(self) -> Compare:
        """``term == False``."""
        return self.eq(False)

    def regex(self, pattern: str) -> Compare:
        """``term matches pattern``. No portable DB form, so the owner rung is the validator."""
        return self._compare(Op.REGEX, pattern)


@dataclass(frozen=True)
class Field(_Comparable):
    """A row-side term: a model field, or a ``__``-joined relation path to one."""

    path: str

    def __post_init__(self) -> None:
        """Reject an empty or dangling lookup path."""
        if not self.path or self.path.startswith("__") or self.path.endswith("__"):
            raise ValueError(f"Field path must be a non-empty lookup path, got {self.path!r}")

    def __str__(self) -> str:
        """``row.<path>``."""
        return f"row.{self.path}"

    def length(self) -> Length:
        """The character length of this field, for ``max_length``-shaped rules."""
        return Length(self.path)

    @property
    def relation(self) -> str | None:
        """The first relation hop when the path crosses one, else ``None``."""
        head, sep, _rest = self.path.partition("__")
        return head if sep else None


@dataclass(frozen=True)
class Actor(_Comparable):
    """A context-side term: an attribute of the acting user."""

    attr: str

    def __post_init__(self) -> None:
        """Reject a non-identifier attribute name."""
        if not self.attr.isidentifier():
            raise ValueError(f"Actor attribute must be an identifier, got {self.attr!r}")

    def __str__(self) -> str:
        """``actor.<attr>``."""
        return f"actor.{self.attr}"


@dataclass(frozen=True)
class Length(Field):
    """The character length of a row field. Reads the same field as ``Field(path)``."""

    def __str__(self) -> str:
        """``len(row.<path>)``."""
        return f"len(row.{self.path})"


Term = Field | Actor


# ---------------------------------------------------------------------- predicates


class _Predicate:
    """Operator sugar shared by every predicate node."""

    def __and__(self, other: Predicate) -> And:
        """``self AND other``."""
        return And((self, other))  # type: ignore[arg-type]

    def __or__(self, other: Predicate) -> Or:
        """``self OR other``."""
        return Or((self, other))  # type: ignore[arg-type]

    def __invert__(self) -> Not:
        """``NOT self``."""
        return Not(self)  # type: ignore[arg-type]


@dataclass(frozen=True)
class Compare(_Predicate):
    """A leaf comparison: ``term <op> value``."""

    term: Term
    op: Op
    value: object

    def __post_init__(self) -> None:
        """Freeze a membership operand as a tuple so equal rules hash equal."""
        if self.op in (Op.IN, Op.NOT_IN) and not isinstance(self.value, tuple):
            object.__setattr__(self, "value", tuple(self.value))  # type: ignore[call-overload]

    def __str__(self) -> str:
        """``row.<path> <op> <value>`` or ``actor.<attr> <op> <value>``."""
        value = str(self.value) if isinstance(self.value, Field) else repr(self.value)
        return f"{self.term} {self.op.value} {value}"


@dataclass(frozen=True)
class And(_Predicate):
    """Conjunction."""

    operands: tuple[Predicate, ...]

    def __str__(self) -> str:
        """Parenthesized ``AND`` chain."""
        return "(" + " AND ".join(str(p) for p in self.operands) + ")"


@dataclass(frozen=True)
class Or(_Predicate):
    """Disjunction."""

    operands: tuple[Predicate, ...]

    def __str__(self) -> str:
        """Parenthesized ``OR`` chain."""
        return "(" + " OR ".join(str(p) for p in self.operands) + ")"


@dataclass(frozen=True)
class Not(_Predicate):
    """Negation."""

    operand: Predicate

    def __str__(self) -> str:
        """``NOT <operand>``."""
        return f"NOT {self.operand}"


@dataclass(frozen=True)
class Unique(_Predicate):
    """A set invariant: no two rows (satisfying ``condition``) share ``fields``.

    The one leaf kind that is not row-local: it reads other rows of the same
    table, so it has no ``Q`` and ``evaluate`` refuses it. Its DB form is
    ``UniqueConstraint`` (L0); ``unique=True`` on a field is the same leaf.
    ``canonical()`` drops ``deferred`` (SQL-92 files deferrability outside the
    constraint) and reads ``nulls_distinct=True`` as the default ``None``:
    what stays is what PostgreSQL's own duplicate-index test compares.
    """

    fields: tuple[str, ...]
    condition: Predicate | None = None
    nulls_distinct: bool | None = None
    deferred: bool = False

    def __str__(self) -> str:
        """``unique(a, b) WHERE <condition>``, with its NULL and timing qualifiers."""
        where = f" WHERE {self.condition}" if self.condition is not None else ""
        nulls = (
            ""
            if self.nulls_distinct is None
            else f" NULLS {'' if self.nulls_distinct else 'NOT '}DISTINCT"
        )
        deferred = " DEFERRED" if self.deferred else ""
        return f"unique({', '.join(self.fields)}){where}{nulls}{deferred}"


Predicate = Compare | And | Or | Not | Unique


@dataclass(frozen=True)
class Rule:
    """A named predicate. The name is the intent marker divergent copies drift from."""

    name: str
    predicate: Predicate
    blessed: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Reject a non-identifier rule name."""
        if not self.name.isidentifier():
            raise ValueError(f"Rule name must be an identifier, got {self.name!r}")

    def __str__(self) -> str:
        """``<name> := <predicate>``."""
        return f"{self.name} := {self.predicate}"


# -------------------------------------------------------------------- canonical form


def _sort_key(pred: Predicate) -> str:
    return repr(pred)


def canonical(pred: Predicate) -> Predicate:
    """Normalize so that equal predicates compare equal.

    Flattens nested ``And``/``Or``, drops duplicate operands, sorts commutative
    operands, pushes ``Not`` to the leaves (De Morgan, double negation) and
    collapses a one-operand junction. ``Not`` is never folded into the
    comparison operator: ``NOT (score < 5)`` and ``score >= 5`` differ on a
    NULL row (and on an actor without the attribute), so folding would make the
    canonical form enforce differently from the authored one.
    """
    if isinstance(pred, Compare):
        if pred.op in (Op.IN, Op.NOT_IN):
            return Compare(pred.term, pred.op, tuple(sorted(pred.value, key=repr)))  # type: ignore[arg-type]
        return pred
    if isinstance(pred, Unique):
        condition = None if pred.condition is None else canonical(pred.condition)
        nulls_distinct = False if pred.nulls_distinct is False else None
        return Unique(tuple(sorted(pred.fields)), condition, nulls_distinct, False)
    if isinstance(pred, Not):
        inner = pred.operand
        if isinstance(inner, Not):
            return canonical(inner.operand)
        if isinstance(inner, Compare):
            return pred
        if isinstance(inner, And):
            return canonical(Or(tuple(Not(p) for p in inner.operands)))
        return canonical(And(tuple(Not(p) for p in inner.operands)))
    kind = type(pred)
    flat: list[Predicate] = []
    for operand in pred.operands:
        c = canonical(operand)
        if isinstance(c, kind):
            flat.extend(c.operands)
        else:
            flat.append(c)
    unique = sorted(set(flat), key=_sort_key)
    if len(unique) == 1:
        return unique[0]
    return kind(tuple(unique))


# ------------------------------------------------------------------------ footprint


def footprint(pred: Predicate) -> frozenset[Term]:
    """The free variables of ``pred``: every row field path and actor attribute read."""
    if isinstance(pred, Compare):
        if isinstance(pred.value, Field):
            return frozenset({pred.term, pred.value})
        return frozenset({pred.term})
    if isinstance(pred, Unique):
        own: frozenset[Term] = frozenset(Field(name) for name in pred.fields)
        return own if pred.condition is None else own | footprint(pred.condition)
    if isinstance(pred, Not):
        return footprint(pred.operand)
    out: set[Term] = set()
    for operand in pred.operands:
        out |= footprint(operand)
    return frozenset(out)


# ---------------------------------------------------------------------------- owner


class Rung(str, Enum):
    """The ladder (whitepaper section 3), restricted to what the fragment can express."""

    L0_DB = "L0 db constraint"
    L1_FIELD = "L1 field"
    L2_ROW = "L2 row"
    L4_RELATION = "L4 relation"
    L6_ACTOR = "L6 actor/policy"


@dataclass(frozen=True)
class Owner:
    """The computed home of a predicate.

    ``scope`` is ``"schema"`` for an actor-only grant (no row field in the
    footprint, so no model is its owner; the schema ORs its grants),
    ``"restrictions"`` for an actor-only restriction (the schema's second
    scope, which ANDs what it holds above every grant), ``"model"`` for a
    rule over one model's rows (``model`` is the *declaring* class: the base,
    abstract or a multi-table parent, that owns every field the rule reads,
    when there is one), or ``"edge"`` for a rule that crosses a relation
    (``relation`` names the hop).
    """

    scope: str
    rung: Rung
    model: type[models.Model] | None = None
    relation: str | None = None

    def __str__(self) -> str:
        """``schema``, ``schema restrictions``, ``<Model>`` or ``<Model>.<relation>``."""
        if self.scope == "schema":
            return "schema"
        if self.scope == "restrictions":
            return "schema restrictions"
        assert self.model is not None
        if self.scope == "edge":
            return f"{self.model.__name__}.{self.relation}"
        return self.model.__name__

    @property
    def key(self) -> tuple[object, ...]:
        """The identity two owners must share to be the same scope."""
        return (self.scope, self.model, self.relation)


def _declaring_class(model: type[models.Model], names: set[str]) -> type[models.Model]:
    """The outermost class in ``model``'s MRO whose own fields cover ``names``.

    Django hoists abstract-base fields onto each concrete child, so the
    concrete model always covers them; the question is whether a smaller
    scope already does. An abstract mixin does when it declares every field
    read, and so does a multi-table parent, whose fields stay in its own
    table and never reach the child's ``local_fields``. That base is the
    owner: it is the one place the field is authored, and therefore the one
    place a rule over that field is authored once and inherited N times.
    """
    for base in reversed(model.__mro__):
        meta = getattr(base, "_meta", None)
        if meta is None or base is model:
            continue
        local = {f.name for f in meta.local_fields}
        if names <= local:
            return base
    return model


def owner(
    pred: Predicate,
    model: type[models.Model] | None,
    *,
    restriction: bool = False,
) -> Owner:
    """Compute the owner of ``pred`` when it is declared for ``model``'s rows.

    ``restriction`` says the predicate is a conjunct (it must hold for a row
    to be visible) rather than a disjunct (its truth grants everything). The
    schema has one scope for each polarity, both binding only the actor: a
    grant that reads no row is a bypass, ``DjangoSchema(visibility=...)``; a
    restriction that reads no row is universal and belongs above every
    grant, ``DjangoSchema(restrictions=...)``.
    """
    terms = footprint(pred)
    actor_terms = {t for t in terms if isinstance(t, Actor)}
    row_terms = {t for t in terms if isinstance(t, Field)}
    if not row_terms:
        return Owner(scope="restrictions" if restriction else "schema", rung=Rung.L6_ACTOR)
    if model is None:
        raise ValueError(f"{pred} reads row fields but is declared without a model")
    relations = {t.relation for t in row_terms if t.relation is not None}
    if relations:
        if len(relations) > 1:
            raise ValueError(f"{pred} crosses several relations {sorted(relations)}; split it")
        rung = Rung.L6_ACTOR if actor_terms else Rung.L4_RELATION
        return Owner(scope="edge", rung=rung, model=model, relation=next(iter(relations)))
    names = {t.path for t in row_terms}
    declaring = _declaring_class(model, names)
    if actor_terms:
        rung = Rung.L6_ACTOR
    elif len(names) == 1:
        rung = Rung.L1_FIELD
    else:
        rung = Rung.L2_ROW
    return Owner(scope="model", rung=rung, model=declaring)


def leaves(
    pred: Predicate,
    model: type[models.Model] | None,
    *,
    restriction: bool = False,
    site_law: str = "or",
) -> Sequence[tuple[Predicate, Owner]]:
    """Split a canonical predicate into leaves, each with its owner.

    A junction whose operands all share one owner is itself a leaf. A junction
    whose operands fall to different owners is a *branch in disguise*: each
    operand is a leaf of its own and the junction survives only as composition.
    The connective is carried down: every operand of an ``And`` (and everything
    beneath it) is a restriction, so an actor-only conjunct is owned by the
    schema's restriction scope, never proposed as a bypass.

    ``site_law`` is the connective the declaring site combines its rules with
    (``"and"`` for a model or a type, whose rules must all hold; ``"or"`` for
    the schema's bypass list). It decides the polarity of a rule that is
    itself one leaf: a lone actor rule on a type is a conjunct of that type's
    rule set, so it restricts. A junction's operands take their polarity from
    the junction.
    """
    c = canonical(pred)
    if isinstance(c, (And, Or)):
        inner = restriction or isinstance(c, And)
        parts = [(p, owner(p, model, restriction=inner)) for p in c.operands]
        if len({o.key for _, o in parts}) > 1:
            out: list[tuple[Predicate, Owner]] = []
            for p, _ in parts:
                out.extend(leaves(p, model, restriction=inner))
            return out
        return [(c, owner(c, model, restriction=inner))]
    return [(c, owner(c, model, restriction=restriction or site_law == "and"))]


def validate_footprint(pred: Predicate, model: type[models.Model]) -> None:
    """Raise ``ValueError`` when a row term of ``pred`` names no field of ``model``."""
    from django.core.exceptions import FieldDoesNotExist

    for term in footprint(pred):
        if not isinstance(term, Field):
            continue
        current: type[models.Model] | None = model
        for hop in term.path.split("__"):
            if current is None:
                raise ValueError(f"{term.path!r} walks past a non-relation on {model.__name__}")
            try:
                dj_field = current._meta.get_field(hop)
            except FieldDoesNotExist:
                raise ValueError(
                    f"{term.path!r} names no field {hop!r} on {current.__name__}",
                ) from None
            current = getattr(dj_field, "related_model", None)


# ------------------------------------------------------------------------- evaluate


def _compare_const(left: object, op: Op, right: object) -> bool:
    if op is Op.EQ:
        return left == right
    if op is Op.NE:
        return left != right
    if op is Op.IN:
        return left in right  # type: ignore[operator]
    if op is Op.NOT_IN:
        return left not in right  # type: ignore[operator]
    if left is None:
        return False
    if op is Op.REGEX:
        return re.search(str(right), str(left)) is not None
    if op is Op.LT:
        return left < right  # type: ignore[operator]
    if op is Op.LTE:
        return left <= right  # type: ignore[operator]
    if op is Op.GT:
        return left > right  # type: ignore[operator]
    return left >= right  # type: ignore[operator]


def _compare_q(term: Field, op: Op, value: object) -> Q:
    path = f"{term.path}__length" if isinstance(term, Length) else term.path
    if isinstance(value, Field):
        value = F(value.path)
    if op is Op.NE:
        return ~Q(**{f"{path}__exact": value})
    if op is Op.NOT_IN:
        return ~Q(**{f"{path}__in": value})
    return Q(**{f"{path}__{_LOOKUP[op]}": value})


def _join(qs: list[Q], *, conjunction: bool) -> Q:
    out = qs[0]
    for q in qs[1:]:
        out = (out & q) if conjunction else (out | q)
    return out


def evaluate(pred: Predicate, actor: object) -> Q | bool:
    """Partially evaluate ``pred`` for ``actor``.

    Actor terms are read off ``actor`` now (a missing attribute reads as
    ``None``); row terms stay symbolic as a ``Q``. The result is ``True`` (no
    filter), ``False`` (nothing visible) or a ``Q`` to ``.filter(...)`` with.
    """
    if isinstance(pred, Compare):
        if isinstance(pred.term, Actor):
            return _compare_const(getattr(actor, pred.term.attr, None), pred.op, pred.value)
        return _compare_q(pred.term, pred.op, pred.value)
    if isinstance(pred, Unique):
        raise TypeError(f"{pred} is a set invariant; it has no row-local form to evaluate")
    if isinstance(pred, Not):
        inner = evaluate(pred.operand, actor)
        return (not inner) if isinstance(inner, bool) else ~inner
    results = [evaluate(p, actor) for p in pred.operands]
    conjunction = isinstance(pred, And)
    absorbing, neutral = (False, True) if conjunction else (True, False)
    if any(r is absorbing for r in results):
        return absorbing
    qs = [r for r in results if not isinstance(r, bool)]
    if not qs:
        return neutral
    return _join(qs, conjunction=conjunction)
