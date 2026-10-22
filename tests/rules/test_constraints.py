"""The L0 rung: reading Django constraints into the fragment and auditing their placement."""

import pytest
from apps.glossary import models as glossary_models
from apps.kanban import models as kanban_models
from apps.library import models as library_models
from apps.products import models as products_models
from django.db.models import F, Q

from django_strawberry_framework.rules import (
    ChoicesConstraint,
    Field,
    Length,
    Not,
    Or,
    Rung,
    Unique,
    audit_constraints,
    canonical,
    constraint_sites,
    evaluate,
    predicate_from_q,
    render,
)
from django_strawberry_framework.rules.constraints import OpaqueError, allowed_choices


def test_an_inherited_meta_is_a_derived_copy_and_a_templated_name_is_the_base_site() -> None:
    from django.apps.registry import Apps
    from django.db import models

    registry = Apps()  # keeps these fixtures out of the fakeshop corpus

    class StockBase(models.Model):
        partner = models.IntegerField()
        sku = models.TextField()

        class Meta:
            abstract = True
            app_label = "library"
            apps = registry
            unique_together = (("partner", "sku"),)
            constraints = [
                models.CheckConstraint(
                    condition=Q(partner__gte=0),
                    name="%(app_label)s_%(class)s_partner_floor",
                ),
            ]

    class StockRecord(StockBase):
        pass

    class StockRestated(StockBase):
        class Meta(StockBase.Meta):
            constraints = [
                models.CheckConstraint(condition=Q(partner__gte=0), name="partner_floor_again"),
            ]

    class StockSpread(StockBase):
        class Meta(StockBase.Meta):
            # Django replaces ``constraints`` rather than merging it, so a child
            # adding one must re-list the base's: the same objects, not a copy.
            constraints = [
                *StockBase.Meta.constraints,
                models.CheckConstraint(condition=Q(partner__lte=10), name="partner_cap"),
            ]
            unique_together = (*StockBase.Meta.unique_together, ("partner", "id"))

    meta_labels = sorted(s.label for s in constraint_sites(StockRecord) if ".Meta." in s.label)
    assert meta_labels == [
        "StockBase.Meta.constraints[library_stockbase_partner_floor]",
        "StockBase.Meta.unique_together",
    ]
    report = audit_constraints([StockRecord])
    assert (report.R, report.M, report.D) == (1, 0, 0)
    report = audit_constraints([StockRestated])
    assert report.R == 2  # the child's own Meta restates the floor
    labels = {s.label for s in constraint_sites(StockRestated)}
    assert "StockRestated.Meta.constraints[partner_floor_again]" in labels
    assert "StockRestated.Meta.unique_together" not in labels
    spread = [s for s in constraint_sites(StockSpread) if s.label.startswith("StockSpread.Meta")]
    assert sorted(s.name for s in spread) == ["partner_cap", "unique_together_partner_id"]
    assert audit_constraints([StockSpread]).R == 1  # the spread members are the base's objects


def test_xor_is_opaque_rather_than_read_as_or() -> None:
    with pytest.raises(OpaqueError, match="XOR"):
        predicate_from_q(Q(a=1) ^ Q(b=2))


def test_a_q_of_field_lookups_reads_into_the_fragment() -> None:
    assert predicate_from_q(Q(price__gte=0)) == Field("price").gte(0)
    assert predicate_from_q(~Q(title="")) == Not(Field("title").eq(""))
    assert predicate_from_q(Q(ends__gt=F("starts"))) == Field("ends").gt(Field("starts"))
    assert predicate_from_q(Q(rank__isnull=True)) == Field("rank").eq(None)
    assert predicate_from_q(Q(rank__isnull=False)) == Not(Field("rank").eq(None))
    assert predicate_from_q(Q(name__length__lte=20)) == Length("name").lte(20)
    nested = predicate_from_q(Q(a=1) | Q(b=2, c=3))
    assert isinstance(nested, Or)
    assert str(nested) == "(row.a eq 1 OR (row.b eq 2 AND row.c eq 3))"
    assert str(Field("ends").gt(Field("starts"))) == "row.ends gt row.starts"


def test_an_expression_condition_is_opaque() -> None:
    from django.db.models import Value
    from django.db.models.lookups import Exact

    with pytest.raises(OpaqueError, match="expression"):
        predicate_from_q(Q(Exact(Value(1), Value(1))))
    with pytest.raises(OpaqueError, match="constrains nothing"):
        predicate_from_q(Q())
    with pytest.raises(TypeError, match="set invariant"):
        evaluate(Unique(("sku",)), None)


def test_canonical_sorts_membership_sets_and_unique_fields() -> None:
    assert canonical(Field("kind").in_(["human", "agent"])) == Field("kind").in_(
        ("agent", "human"),
    )
    assert canonical(Unique(("b", "a"), ~Field("x").eq(1))) == Unique(
        ("a", "b"),
        Not(Field("x").eq(1)),
    )
    assert str(Unique(("a", "b"), Field("x").eq(1))) == "unique(a, b) WHERE row.x eq 1"
    assert evaluate(Length("name").lte(3), None) == Q(name__length__lte=3)
    assert evaluate(Field("ends").gt(Field("starts")), None) == Q(ends__gt=F("starts"))


def test_choices_restated_as_a_check_is_identical_duplication_held_at_l0() -> None:
    report = audit_constraints([kanban_models.Actor])

    sites = {
        leaf.site.label: (str(leaf.predicate), leaf.owner.rung, leaf.misplaced)
        for leaf in report.leaves
    }
    assert sites["Actor.kind choices"] == ("row.kind in ('agent', 'human')", Rung.L0_DB, False)
    assert sites["Actor.Meta.constraints[actor_kind_valid]"] == (
        "row.kind in ('agent', 'human')",
        Rung.L0_DB,
        False,
    )
    assert (
        "Actor.kind max_length" not in sites
    )  # SlugField's default 50 is the type's, not authored
    identical = [f for f in report.findings if f.kind == "identical duplication"]
    assert len(identical) == 1
    assert identical[0].sites == ("Actor.Meta.constraints[actor_kind_valid]", "Actor.kind choices")
    assert identical[0].remedy == (
        "replace Actor.Meta.constraints[actor_kind_valid] with a ChoicesConstraint derived from "
        "Actor.kind choices"
    )
    assert (
        report.R,
        report.M,
        report.D,
        report.reduced,
    ) == (
        2,
        0,
        0,
        False,
    )


def test_choices_with_no_db_form_is_stated_too_high() -> None:
    report = audit_constraints([library_models.Shelf])

    misplaced = [f for f in report.findings if f.kind.startswith("misplaced")]
    assert [(f.kind, f.sites, f.remedy) for f in misplaced] == [
        (
            "misplaced (stated too high)",
            ("Shelf.condition choices",),
            "move down to Shelf (L0 db constraint)",
        ),
        (
            "misplaced (stated too high)",
            ("Shelf.tier choices",),
            "move down to Shelf (L0 db constraint)",
        ),
    ]
    by_label = {leaf.site.label: leaf for leaf in report.leaves}
    assert "Shelf.condition max_length" not in by_label  # a CharField width is the column type
    assert str(by_label["Shelf.condition choices"].predicate) == (
        "row.condition in ('', 'damaged', 'good', 'worn', None)"
    )
    # ``__empty__`` on the choices class declares ``None`` first; ``blank=True`` admits ``""``.
    assert allowed_choices(library_models.Shelf._meta.get_field("condition")) == (
        None,
        "good",
        "worn",
        "damaged",
        "",
    )
    assert report.M == 2


def test_field_type_defaults_are_not_authored_sites() -> None:
    labels = {site.label for site in constraint_sites(products_models.Item)}
    assert "Item.attachment max_length" not in labels  # FileField's default 100
    uuid_labels = {site.label for site in constraint_sites(kanban_models.UUIDModel)}
    assert "UUIDModel.id max_length" not in uuid_labels  # UUIDField's 32
    assert not any(label.endswith("card unique=True") for label in uuid_labels)  # OneToOneField
    opaque = [site for site in constraint_sites(kanban_models.UUIDModel) if site.opaque]
    assert [s.label for s in opaque] == [
        "UUIDModel.Meta.constraints[kanban_uuidmodel_exactly_one_link]",
    ]


def test_an_abstract_base_constraint_is_one_site_across_its_children() -> None:
    seen: set[tuple[type, str]] = set()
    first = constraint_sites(kanban_models.Actor, seen)
    second = constraint_sites(kanban_models.TrackedPath, seen)
    key_sites = [s.label for s in first + second if s.label.startswith("LookupBase.key")]
    assert key_sites == ["LookupBase.key unique=True"]


@pytest.mark.django_db
def test_choices_constraint_derives_its_check_from_the_field() -> None:
    constraint = ChoicesConstraint("kind", name="derived_kind")
    members = Q(kind__in=("human", "agent"))
    assert constraint.condition_for(kanban_models.Actor) == members
    # Binding (what ``class_prepared`` does for a declared one) freezes the derivation into
    # what migrations see, so a later change to the choices is a change to the constraint.
    original = kanban_models.Actor._meta.constraints
    kanban_models.Actor._meta.constraints = [*original, constraint]
    try:
        ChoicesConstraint._bind(kanban_models.Actor)
    finally:
        kanban_models.Actor._meta.constraints = original
    path, args, kwargs = constraint.deconstruct()
    assert (path, args, kwargs) == (
        "django_strawberry_framework.rules.constraints.ChoicesConstraint",
        ("kind",),
        {"name": "derived_kind", "condition": members},
    )
    frozen = ChoicesConstraint("kind", name="derived_kind", condition=members)
    assert constraint == frozen
    stale = ChoicesConstraint("kind", name="derived_kind", condition=Q(kind__in=("human",)))
    assert constraint != stale  # yesterday's members: the autodetector emits a new CHECK
    from django.core.exceptions import ValidationError

    constraint.validate(kanban_models.Actor, kanban_models.Actor(key="x", kind="human"))
    with pytest.raises(ValidationError):
        constraint.validate(kanban_models.Actor, kanban_models.Actor(key="x", kind="bogus"))


def test_an_isomorphic_group_counts_in_r_only_when_a_template_can_hold_it() -> None:
    # Same declaration (``TextField(unique=True)``), one app: the mixin is the remedy.
    report = audit_constraints([library_models.RepairTicket, library_models.VenueBadge])
    finding = next(f for f in report.findings if f.kind == "isomorphic duplication")
    assert (report.R, report.I) == (2, 0)
    assert finding.remedy == (
        "one abstract mixin in library owning ['code'] and this rule, inherited by each model"
    )

    # A ``TextField`` beside a ``PositiveIntegerField``: a hole, so no abstract base can hold it.
    report = audit_constraints([kanban_models.TargetVersion, kanban_models.Card])
    patterns = [f for f in report.findings if f.kind == "isomorphic pattern"]
    assert (report.R, report.I) == (1, 1)
    assert [(f.leaf, f.sites) for f in patterns] == [
        ("unique(number)", ("Card.number unique=True", "TargetVersion.number unique=True")),
    ]
    assert patterns[0].remedy.startswith("the fields differ in ['number:type'], so no abstract")

    # Identical declarations in two apps: the base would be a dependency neither app has.
    report = audit_constraints([kanban_models.Card, glossary_models.GlossaryTerm])
    patterns = [f for f in report.findings if f.kind == "isomorphic pattern"]
    assert (report.R, report.I, report.reduced) == (1, 1, True)
    assert patterns[0].leaf == "unique(title)"
    assert patterns[0].remedy == (
        "the models span ['glossary', 'kanban']; a shared base is a dependency between apps; "
        "bless it as a pattern or leave it"
    )
    assert "I (isomorphic patterns)       = 1   reported, not gated" in render(report)


def test_the_template_absorbs_the_largest_identical_sub_group_and_r_is_monotone() -> None:
    library = [
        library_models.Branch,
        library_models.CirculationDesk,
        library_models.Genre,
        library_models.Patron,
        library_models.Periodical,
        library_models.Publisher,
        library_models.VenueSponsor,
    ]
    assert (audit_constraints(library).R, audit_constraints(library).I) == (7, 0)
    # One more copy in another app: a single leftover is just a leaf at its owner.
    report = audit_constraints([*library, products_models.Category])
    assert (report.R, report.I) == (7, 0)
    # Two leftovers in two apps are a pattern between themselves; the bucket still counts.
    report = audit_constraints([*library, products_models.Category, kanban_models.SpecDoc])
    pattern = next(f for f in report.findings if f.kind == "isomorphic pattern")
    assert (report.R, report.I) == (7, 1)
    assert pattern.sites == ("Category.name unique=True", "SpecDoc.name unique=True")
    # A hole in one member leaves the identical three to the template.
    from apps.scalars import models as scalars_models

    report = audit_constraints(
        [
            scalars_models.MediaSpecimen,
            scalars_models.ScalarSpecimen,
            scalars_models.ScalarSpecimenTag,
            scalars_models.NullableScalarSpecimen,
        ],
    )
    dup = next(f for f in report.findings if f.kind == "isomorphic duplication")
    assert (report.R, report.I, len(dup.sites)) == (3, 0, 3)
    # A reverse accessor that is public API is a hole the template cannot parameterize.
    report = audit_constraints([products_models.Item, products_models.Property])
    pattern = next(f for f in report.findings if f.kind == "isomorphic pattern")
    assert pattern.leaf == "unique(category, name)"
    assert "['category:related_name']" in pattern.remedy


def test_two_abstract_bases_with_one_name_are_two_sites() -> None:
    report = audit_constraints([glossary_models.GlossaryStatus, kanban_models.Milestone])
    pattern = next(f for f in report.findings if f.kind == "isomorphic pattern")
    assert (report.R, report.I) == (1, 1)
    assert pattern.sites == (
        "glossary.LookupBase.key unique=True",
        "kanban.LookupBase.key unique=True",
    )


def test_relation_paths_resolve_and_unique_carries_its_qualifiers() -> None:
    from django.db.models import Deferrable, UniqueConstraint

    from django_strawberry_framework.rules.audit import _resolve_field
    from django_strawberry_framework.rules.constraints import _constraint_leaf

    found = _resolve_field(library_models.Book, "shelf__code")
    assert found is not None
    assert (found.model, found.name) == (library_models.Shelf, "code")
    assert _resolve_field(library_models.Book, "shelf__nothing") is None
    strict = UniqueConstraint(
        fields=["sku"],
        name="sku_strict",
        nulls_distinct=False,
        deferrable=Deferrable.DEFERRED,
    )
    leaf, derived = _constraint_leaf(strict, library_models.Book)
    assert (str(leaf), derived) == ("unique(sku) NULLS NOT DISTINCT DEFERRED", False)
    # NULLS NOT DISTINCT changes which tables are valid; deferral is timing and
    # NULLS DISTINCT is the default, so neither is identity.
    assert canonical(leaf) != canonical(Unique(("sku",)))
    assert canonical(leaf) == Unique(("sku",), None, False, False)
    relaxed = Unique(("sku",), nulls_distinct=True, deferred=True)
    assert canonical(relaxed) == Unique(("sku",))


def test_a_clean_that_only_normalises_is_not_an_opaque_rule() -> None:
    from django.contrib.auth.models import AbstractBaseUser

    from django_strawberry_framework.rules.constraints import _can_refuse

    assert not _can_refuse(AbstractBaseUser.__dict__["clean"])
    assert not any(s.label == "AbstractBaseUser.clean" for s in constraint_sites(AbstractBaseUser))

    def refusing(self: object) -> None:
        raise ValueError("ends before starts")

    def delegating(self: object) -> None:
        refuse_if_bad(self)

    def prose(self: object) -> None:
        """Never raise; a ValidationError is the helper's business."""
        self.title = str(getattr(self, "title", "")).strip()

    def refuse_if_bad(instance: object) -> None:
        raise ValueError(instance)

    assert _can_refuse(refusing)
    assert _can_refuse(delegating)  # the helper's body is where the raise went
    assert not _can_refuse(prose)  # a docstring's "raise" is not a statement
    assert _can_refuse(object())  # no source: opaque, not silently a normaliser


def test_a_charfield_width_is_the_column_type_and_a_textfield_width_is_a_rule() -> None:
    from apps.glossary import models as glossary_models

    labels = {s.label: s for s in constraint_sites(library_models.Shelf)}
    assert "Shelf.condition max_length" not in labels
    text_widths = [
        s
        for model in (library_models.Shelf, glossary_models.GlossaryTerm)
        for s in constraint_sites(model)
        if s.label.endswith(" max_length")
    ]
    assert all(s.rung is Rung.L1_FIELD for s in text_widths)


def test_render_names_opaque_constraint_bodies_without_cascade_lines() -> None:
    text = render(audit_constraints([kanban_models.UUIDModel]), "uuid")
    assert "opaque constraint bodies" in text
    assert "cascade" not in text
    assert "verdict: NOT REDUCED" in text
