"""The reduction audit: where every visibility rule lives, and where it should.

Walks the registry (and optionally one schema's bypasses), splits every declared
rule into leaves, computes each leaf's owner, and reports the whitepaper's
metric vector:

* **R** - the largest authored multiplicity of any leaf: the authored sites
  carrying one canonical form, whatever their owners (identical copies, and
  isomorphic copies a template could absorb); derived copies, such as a mixin
  rule inherited by
  two models, count zero. Target 1.
* **M** - leaves whose declared site is not their computed owner. A branch in
  disguise is reported as a finding, not counted: splitting it always leaves
  at least one leaf away from its owner, and M counts that leaf. Target 0.
* **D** - rule names that carry more than one canonical body. Target 0.
* **I** - isomorphic groups whose copies outside every field template are more
  than one site: a footprint field declared differently (a hole), or models
  spread over apps (a dependency between apps). Reported, not gated; blessing
  is the answer. Such leftovers do not raise R.
* **B** - blessed items (declared leaves and opaque bodies carrying a stated
  reason), reported so the allow-list cannot grow silently.
* **O** - types whose visibility is an opaque ``get_queryset`` body nobody has
  blessed (unreducible by construction) and, inside those bodies, how many
  times the universal cascade rule had to be invoked by hand. Target 0.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django_strawberry_framework.registry import registry as _default_registry
from django_strawberry_framework.rules.apply import model_rule_sites, type_rules
from django_strawberry_framework.rules.fragment import (
    Owner,
    Predicate,
    Rule,
    Rung,
    canonical,
    leaves,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.db import models

    from django_strawberry_framework.registry import TypeRegistry

__all__ = [
    "Finding",
    "Leaf",
    "Report",
    "Site",
    "audit",
    "render",
]


@dataclass(frozen=True)
class Site:
    """Where a rule was authored."""

    label: str
    scope: Owner


@dataclass(frozen=True)
class Leaf:
    """One canonical leaf of a declared rule, with where it was authored and where it belongs."""

    rule: Rule
    predicate: Predicate
    site: Site
    owner: Owner
    split: bool
    rung_sensitive: bool = False
    held_at_owner: bool = False

    @property
    def misplaced(self) -> bool:
        """Whether the owner holds no copy of this leaf.

        The authored site differs from the owner's scope, or (on a rung where
        the enforcement home matters, ``rung_sensitive``) from its rung; a
        derived copy at the owner (``held_at_owner``) places the leaf.
        """
        return not (self.at_owner or self.held_at_owner)

    @property
    def at_owner(self) -> bool:
        """Whether this authored copy sits at the owner's scope (and rung, where that matters)."""
        if self.owner.key != self.site.scope.key:
            return False
        return not self.rung_sensitive or self.owner.rung is self.site.scope.rung

    @property
    def key(self) -> str:
        """The identity two leaves must share to be the same leaf."""
        return repr(self.predicate)


@dataclass(frozen=True)
class Finding:
    """One defect the audit names, with the sites involved and the remedy."""

    kind: str
    leaf: str
    sites: tuple[str, ...]
    remedy: str


@dataclass
class Report:
    """The metric vector plus everything that fed it."""

    leaves: list[Leaf] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    opaque: list[tuple[str, int]] = field(default_factory=list)
    blessed_opaque: list[tuple[str, str]] = field(default_factory=list)
    R: int = 1
    M: int = 0
    D: int = 0
    I: int = 0  # noqa: E741  # the paper's name for the component
    B: int = 0
    opaque_kind: str = "get_queryset bodies"
    invocation_kind: str | None = "cascade"

    @property
    def reduced(self) -> bool:
        """``True`` when every leaf is authored once at its owner, no name drifted, nothing is opaque."""
        return self.R <= 1 and self.M == 0 and self.D == 0 and not self.opaque


def _schema_site() -> Site:
    return Site("schema", Owner(scope="schema", rung=Rung.L6_ACTOR))


def _restrictions_site() -> Site:
    return Site("schema restrictions", Owner(scope="restrictions", rung=Rung.L6_ACTOR))


def _model_site(model: type[models.Model], label: str | None = None) -> Site:
    return Site(label or model.__name__, Owner(scope="model", rung=Rung.L1_FIELD, model=model))


def _stated_too_low(site: Site, owner: Owner) -> bool:
    """Whether the owner is a bigger scope than the authored site (so the remedy moves up).

    Bigger: either schema scope, an FK edge (which spans two models), or a
    base class of the site's model (shared by every model that inherits it).
    """
    if owner.scope in ("schema", "restrictions", "edge"):
        return True
    site_model, owner_model = site.scope.model, owner.model
    return (
        site_model is not None
        and owner_model is not None
        and site_model is not owner_model
        and issubclass(site_model, owner_model)
    )


def _opaque_hook(type_cls: type) -> tuple[str, int] | None:
    """``(label, cascade_invocations)`` when the type hides its visibility in Python."""
    if not type_cls.has_custom_get_queryset():  # type: ignore[attr-defined]
        return None
    try:
        source = inspect.getsource(type_cls.get_queryset)  # type: ignore[attr-defined]
    except (OSError, TypeError):
        source = ""
    return (type_cls.__name__, source.count("apply_cascade_permissions("))


# ``(site, rule, model, law)``: ``law`` is the connective the site combines its
# rules with, ``"or"`` for the schema's bypass list, ``"and"`` everywhere else.
_Declared = list[tuple[Site, Rule, "type[models.Model] | None", str]]
_Collected = tuple[_Declared, list[tuple[str, int]], list[tuple[str, str]]]


def _collect(
    bypasses: Iterable[Rule],
    restrictions: Iterable[Rule],
    registry: TypeRegistry,
) -> _Collected:
    declared: _Declared = [
        (
            _schema_site(),
            rule,
            None,
            "or",
        )
        for rule in bypasses
    ]
    declared += [
        (
            _restrictions_site(),
            rule,
            None,
            "and",
        )
        for rule in restrictions
    ]
    opaque: list[tuple[str, int]] = []
    blessed_opaque: list[tuple[str, str]] = []
    seen_model_sites: set[tuple[type, str]] = set()
    for model, type_cls in registry.iter_types():
        own = type_rules(type_cls)
        inherited = model_rule_sites(model)
        hook = None
        if not own and not inherited:
            hook = _opaque_hook(type_cls)
        elif getattr(type_cls, "__overrides_get_queryset__", False):
            # A hand-written body beside declared rules: the rules are audited,
            # but whatever the body does to them is not, so the type is opaque.
            hook = _opaque_hook(type_cls)
        if hook is not None:
            reason = getattr(type_cls, "__blessed__", None)
            if reason is None:
                opaque.append(hook)
            else:
                blessed_opaque.append((hook[0], reason))
        if not own and not inherited:
            continue
        declared.extend(
            (
                _model_site(model, type_cls.__name__),
                rule,
                model,
                "and",
            )
            for rule in own
        )
        for base, rule in inherited:
            if (base, rule.name) in seen_model_sites:
                continue  # a derived copy: the mixin's rule reaching a second concrete model
            seen_model_sites.add((base, rule.name))
            declared.append(
                (
                    _model_site(base),
                    rule,
                    base,
                    "and",
                ),
            )
    return declared, opaque, blessed_opaque


def audit(schema: object | None = None, *, registry: TypeRegistry = _default_registry) -> Report:
    """Audit every registered type (and ``schema``'s bypasses and restrictions) for reduction."""
    bypasses = tuple(getattr(schema, "visibility", ()) or ()) if schema is not None else ()
    restrictions = tuple(getattr(schema, "restrictions", ()) or ()) if schema is not None else ()
    declared, opaque, blessed_opaque = _collect(bypasses, restrictions, registry)
    report = Report(opaque=opaque, blessed_opaque=blessed_opaque)

    for site, rule, model, law in declared:
        parts = leaves(rule.predicate, model, site_law=law)
        split = len(parts) > 1
        for predicate, own in parts:
            report.leaves.append(Leaf(rule, predicate, site, own, split))
        if split:
            report.findings.append(
                Finding(
                    "branch in disguise",
                    str(rule),
                    (site.label,),
                    "split into "
                    + "; ".join(f"[{p}] owned by {o} ({o.rung.value})" for p, o in parts),
                ),
            )

    live = [leaf for leaf in report.leaves if leaf.rule.blessed is None]
    report.B = len(report.leaves) - len(live) + len(blessed_opaque)

    _report_misplaced(report, live)
    _report_duplicates(report, live)

    by_name: dict[str, set[str]] = {}
    for _site, rule, _model, _law in declared:
        if rule.blessed is None:
            by_name.setdefault(rule.name, set()).add(repr(canonical(rule.predicate)))
    for name, bodies in by_name.items():
        if len(bodies) > 1:
            report.D += 1
            report.findings.append(
                Finding(
                    "divergent duplication",
                    name,
                    tuple(sorted(s.label for s, r, _, _ in declared if r.name == name)),
                    "one definition per name; the others are drift",
                ),
            )
    return report


def _report_misplaced(report: Report, live: list[Leaf]) -> None:
    """Count every misplaced leaf in M and name its remedy."""
    for leaf in live:
        if leaf.misplaced:
            report.M += 1
            direction = "up" if _stated_too_low(leaf.site, leaf.owner) else "down"
            report.findings.append(
                Finding(
                    f"misplaced ({'stated too low' if direction == 'up' else 'stated too high'})",
                    str(leaf.predicate),
                    (leaf.site.label,),
                    f"move {direction} to {leaf.owner} ({leaf.owner.rung.value})",
                ),
            )


def _report_duplicates(report: Report, live: list[Leaf]) -> None:
    """Raise R to the largest authored multiplicity and name each duplicated leaf.

    Copies with one owner are identical duplication. Copies with several
    owners are isomorphic: every set of them one field template could absorb
    (the same declarations, one home) counts toward R; what those sets leave
    over, when it is more than one site, is a pattern counted once in I.
    """
    groups: dict[str, list[Leaf]] = {}
    for leaf in live:
        groups.setdefault(leaf.key, []).append(leaf)
    for members in groups.values():
        sites = _site_labels(members)
        if len(sites) < 2:
            continue
        predicate = str(members[0].predicate)
        if len({m.owner.key for m in members}) == 1:
            report.R = max(report.R, len(sites))
            report.findings.append(
                Finding("identical duplication", predicate, sites, _identical_remedy(members)),
            )
            continue
        fields = sorted({t.path for m in members for t in _row_terms(m.predicate)})
        buckets, holes, homes = _template_cost(members)
        absorbed: set[int] = set()
        for home, bucket in buckets:
            bucket_sites = _site_labels(bucket)
            if len(bucket_sites) < 2:
                continue
            absorbed.update(id(m) for m in bucket)
            report.R = max(report.R, len(bucket_sites))
            remedy = (
                f"one abstract mixin in {home} owning {fields} and this rule, "
                "inherited by each model"
                if fields
                else "a grant at one site and a restriction at another: two rules, not one"
            )
            report.findings.append(
                Finding("isomorphic duplication", predicate, bucket_sites, remedy),
            )
        left = [m for m in members if id(m) not in absorbed]
        left_sites = _site_labels(left)
        if len(left_sites) < 2:
            continue
        report.I += 1
        why = (
            f"the fields differ in {holes}, so no abstract base can hold them without "
            "each model re-declaring its own"
            if holes
            else f"the models span {homes}; a shared base is a dependency between apps"
        )
        report.findings.append(
            Finding(
                "isomorphic pattern",
                predicate,
                left_sites,
                f"{why}; bless it as a pattern or leave it",
            ),
        )


def _site_labels(members: list[Leaf]) -> tuple[str, ...]:
    """The distinct authored sites, labelled; a label two models share gets its app prefixed."""
    scopes_by_label: dict[str, set[tuple[object, ...]]] = {}
    for member in members:
        scopes_by_label.setdefault(member.site.label, set()).add(member.site.scope.key)
    labels: set[str] = set()
    for member in members:
        label = member.site.label
        model = member.site.scope.model
        if len(scopes_by_label[label]) > 1 and model is not None:
            label = f"{model._meta.app_label}.{label}"
        labels.add(label)
    return tuple(sorted(labels))


def _identical_remedy(members: list[Leaf]) -> str:
    """What to do with copies that share one owner.

    A ``choices`` copy beside a ``CHECK`` is derived, not deleted: the
    ``choices`` drive the enum, the ``CHECK`` holds the rows, so one is
    written and the other read off it. Otherwise one copy may already sit at
    the owner (a CHECK beside the validator restating it): keep that one.
    """
    choices = sorted(m.site.label for m in members if m.site.label.endswith(" choices"))
    checks = sorted(
        m.site.label for m in members if m.at_owner and not m.site.label.endswith(" choices")
    )
    if choices and checks:
        return f"replace {checks[0]} with a ChoicesConstraint derived from {choices[0]}"
    kept = sorted(m.site.label for m in members if m.at_owner)
    if kept:
        return f"keep {kept[0]}; the others restate it"
    return f"author once at {members[0].owner}"


def _row_terms(predicate: Predicate) -> list:
    from django_strawberry_framework.rules.fragment import Field, footprint

    return [t for t in footprint(predicate) if isinstance(t, Field)]


# Presentation attributes: a base carrying one value would flatten each
# child's label, but the column, the rule and every derived copy are the same,
# so a difference in them is not a hole in the rule's template.
_COSMETIC = frozenset({"verbose_name", "help_text", "db_comment"})


def _resolve_field(model: type[models.Model], path: str) -> models.Field | None:
    """The field ``path`` names on ``model``, following ``__`` relation hops, or ``None``."""
    from django.core.exceptions import FieldDoesNotExist

    current: type[models.Model] | None = model
    found: models.Field | None = None
    for part in path.split("__"):
        if current is None:
            return None
        try:
            found = current._meta.get_field(part)  # type: ignore[assignment]
        except FieldDoesNotExist:
            return None
        current = getattr(found, "related_model", None)
    return found


def _normalize(value: object) -> object:
    """``value`` in a form that compares by content: deconstructibles by their deconstruction."""
    deconstruct = getattr(value, "deconstruct", None)
    if callable(deconstruct) and not isinstance(value, type):
        path, args, kwargs = deconstruct()[-3:]
        return (path, _normalize(args), _normalize(kwargs))
    if isinstance(value, dict):
        return tuple(sorted((k, _normalize(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_normalize(v) for v in value)
    return value


_Signature = tuple[str, object, dict[str, object]]


def _signature(found: models.Field) -> _Signature:
    """A field's declaration as the author wrote it: class path, positional args, attributes."""
    _name, dotted, args, kwargs = found.deconstruct()
    return (
        dotted,
        _normalize(args),
        {k: _normalize(v) for k, v in kwargs.items() if k not in _COSMETIC},
    )


def _hashable(value: object) -> object:
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


_Buckets = list[tuple[str, list[Leaf]]]


def _template_cost(members: list[Leaf]) -> tuple[_Buckets, list[str], list[str]]:
    """What a field template absorbing ``members`` would cost.

    Anti-unifies the declarations (``deconstruct()``) of every footprint
    field across the members. A hole is a field class, positional argument
    or attribute that differs between members: a shared field in an abstract
    base carries no parameters, and a child that re-declares the field owns
    it again, so one hole means no field template holds the whole group. The
    homes are the apps the members live in. Returns the buckets a template
    could absorb (one per home and identical declaration), the holes over
    the whole group, and the homes.
    """
    paths = sorted({t.path for m in members for t in _row_terms(m.predicate)})
    declarations: list[tuple[str, dict[str, _Signature]]] = []
    for member in members:
        site_model = member.site.scope.model
        home = site_model._meta.app_label if site_model is not None else ""
        found = {
            path: _resolve_field(site_model, path) for path in paths if site_model is not None
        }
        declarations.append(
            (home, {path: _signature(f) for path, f in found.items() if f is not None}),
        )
    buckets: dict[object, list[Leaf]] = {}
    for member, (home, signatures) in zip(members, declarations, strict=True):
        key = (home if paths else "", _hashable(_normalize(sorted(signatures.items()))))
        buckets.setdefault(key, []).append(member)
    holes: set[str] = set()
    for path in paths:
        present = [sigs[path] for _, sigs in declarations if path in sigs]
        if not present:
            continue
        first_class, first_args, first_kwargs = present[0]
        if any(cls != first_class for cls, _, _ in present):
            holes.add(f"{path}:type")
        if any(args != first_args for _, args, _ in present):
            holes.add(f"{path}:args")
        for attr in {k for _, _, kw in present for k in kw}:
            if any(kw.get(attr) != first_kwargs.get(attr) for _, _, kw in present):
                holes.add(f"{path}:{attr}")
    homes = sorted({home for home, _ in declarations if home})
    return ([(str(key[0]), bucket) for key, bucket in buckets.items()], sorted(holes), homes)


def render(report: Report, title: str = "") -> str:
    """A plain-text rendering of ``report`` for a terminal."""
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("=" * len(title))
    unknown = "  (over declared rules only; opaque bodies are uncounted)" if report.opaque else ""
    lines.append(f"R (max authored multiplicity) = {report.R}   target 1{unknown}")
    lines.append(f"M (misplaced leaves)          = {report.M}   target 0{unknown}")
    lines.append(f"D (divergent names)           = {report.D}   target 0{unknown}")
    lines.append(f"I (isomorphic patterns)       = {report.I}   reported, not gated")
    lines.append(f"B (blessed)                   = {report.B}")
    for name, reason in report.blessed_opaque:
        lines.append(f"  blessed get_queryset body: {name} ({reason})")
    if report.opaque:
        if report.invocation_kind is None:
            hooks = ", ".join(name for name, _ in report.opaque)
        else:
            hooks = ", ".join(
                f"{name} ({n} {report.invocation_kind} call{'s'[: n != 1]})"
                for name, n in report.opaque
            )
        lines.append(f"opaque {report.opaque_kind:<22} = {len(report.opaque)}: {hooks}")
        if report.invocation_kind is not None:
            calls = sum(n for _, n in report.opaque)
            lines.append(
                f"{report.invocation_kind} invocation sites      = {calls}   target 0 (framework default)",
            )
        lines.append("  -> rules inside Python bodies cannot be footprinted, compared or counted")
    lines.append("")
    if report.leaves:
        lines.append("leaves")
        for leaf in report.leaves:
            flag = " MISPLACED" if leaf.misplaced else ""
            lines.append(
                f"  {leaf.rule.name:<14} [{leaf.predicate}]  at {leaf.site.label:<14}"
                f" owner {leaf.owner!s:<14} {leaf.owner.rung.value}{flag}",
            )
        lines.append("")
    if report.findings:
        lines.append("findings")
        for f in report.findings:
            lines.append(f"  {f.kind}: {f.leaf}")
            lines.append(f"      at {', '.join(f.sites)}")
            lines.append(f"      remedy: {f.remedy}")
    else:
        lines.append("findings: none" if report.leaves else "findings: none (nothing declared)")
    lines.append("")
    lines.append("verdict: " + ("REDUCED" if report.reduced else "NOT REDUCED"))
    return "\n".join(lines)
