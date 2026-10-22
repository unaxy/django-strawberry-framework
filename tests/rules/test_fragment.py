"""The rule fragment: canonical form, footprint, owner, leaves, and compilation to ``Q``."""

from types import SimpleNamespace

import pytest
from apps.library import models as library_models
from django.db.models import Q

from django_strawberry_framework.rules import (
    Actor,
    And,
    Field,
    Not,
    Or,
    Rule,
    Rung,
    canonical,
    evaluate,
    footprint,
    leaves,
    owner,
)

STAFF = Actor("is_staff").is_true()
PUBLIC = Field("is_private").is_false()


def test_canonical_sorts_flattens_and_dedupes_commutative_operands() -> None:
    left = (PUBLIC | STAFF) | STAFF
    right = STAFF | PUBLIC
    assert canonical(left) == canonical(right)
    assert isinstance(canonical(left), Or)
    assert len(canonical(left).operands) == 2


def test_canonical_pushes_negation_to_the_leaves_but_never_into_the_operator() -> None:
    assert canonical(~~STAFF) == STAFF
    assert canonical(~STAFF) == Not(STAFF)
    de_morgan = canonical(~(STAFF & PUBLIC))
    assert isinstance(de_morgan, Or)
    assert set(de_morgan.operands) == {Not(STAFF), Not(PUBLIC)}
    # ``NOT (rank < 3)`` keeps NULL rows; ``rank >= 3`` drops them. Not the same leaf.
    assert canonical(Not(Field("rank").lt(3))) == Not(Field("rank").lt(3))
    assert canonical(Not(Field("rank").lt(3))) != Field("rank").gte(3)


def test_canonical_collapses_a_single_operand_junction() -> None:
    assert canonical(And((STAFF, STAFF))) == STAFF


def test_footprint_is_the_set_of_terms_read() -> None:
    assert footprint(STAFF | PUBLIC) == {Actor("is_staff"), Field("is_private")}
    assert footprint(Field("galaxy__is_private").is_false()) == {Field("galaxy__is_private")}


def test_owner_of_an_actor_only_rule_is_the_schema() -> None:
    computed = owner(STAFF, library_models.Book)
    assert computed.scope == "schema"
    assert computed.rung is Rung.L6_ACTOR
    assert owner(STAFF, None) == computed


def test_owner_of_a_row_rule_needs_a_model() -> None:
    with pytest.raises(ValueError, match="without a model"):
        owner(PUBLIC, None)


def test_owner_of_a_single_field_rule_is_the_model_at_l1() -> None:
    computed = owner(Field("title").eq("x"), library_models.Book)
    assert (computed.scope, computed.model, computed.rung) == (
        "model",
        library_models.Book,
        Rung.L1_FIELD,
    )


def test_owner_of_a_two_field_rule_is_the_model_at_l2() -> None:
    computed = owner(Field("title").eq("x") & Field("pk").gt(1), library_models.Book)
    assert computed.rung is Rung.L2_ROW


def test_owner_of_a_relation_rule_is_the_edge_at_l4() -> None:
    computed = owner(Field("shelf__name").eq("x"), library_models.Book)
    assert (computed.scope, computed.relation, computed.rung) == (
        "edge",
        "shelf",
        Rung.L4_RELATION,
    )
    assert str(computed) == "Book.shelf"


def test_owner_of_an_actor_row_rule_is_the_model_at_l6() -> None:
    computed = owner(STAFF & Field("title").eq("x"), library_models.Book)
    assert (computed.scope, computed.rung) == ("model", Rung.L6_ACTOR)


def test_owner_crossing_two_relations_is_refused() -> None:
    with pytest.raises(ValueError, match="several relations"):
        owner(Field("shelf__name").eq("x") & Field("genres__name").eq("y"), library_models.Book)


def test_leaves_split_a_branch_in_disguise_but_keep_a_true_leaf() -> None:
    split = leaves(STAFF | PUBLIC, library_models.Book)
    assert [(str(p), o.scope) for p, o in split] == [
        ("actor.is_staff eq True", "schema"),
        ("row.is_private eq False", "model"),
    ]
    # An actor conjunct restricts; the schema's bypass list holds grants only, so
    # it goes to the schema's restriction scope, never offered as a bypass.
    conjunct = leaves(STAFF & PUBLIC, library_models.Book)
    assert [(str(p), str(o), o.rung) for p, o in conjunct] == [
        ("actor.is_staff eq True", "schema restrictions", Rung.L6_ACTOR),
        ("row.is_private eq False", "Book", Rung.L1_FIELD),
    ]
    restricting = owner(STAFF, library_models.Book, restriction=True)
    assert (restricting.scope, restricting.model) == ("restrictions", None)
    # A rule that is one leaf takes its polarity from the site that holds it.
    assert leaves(STAFF, library_models.Book, site_law="and")[0][1].scope == "restrictions"
    assert leaves(STAFF, library_models.Book, site_law="or")[0][1].scope == "schema"
    whole = leaves(Field("title").eq("x") | Field("pk").gt(1), library_models.Book)
    assert len(whole) == 1
    assert whole[0][1].rung is Rung.L2_ROW


def test_evaluate_folds_actor_terms_and_keeps_row_terms_symbolic() -> None:
    staff = SimpleNamespace(is_staff=True)
    anonymous = SimpleNamespace(is_staff=False)
    assert evaluate(STAFF | PUBLIC, staff) is True
    assert evaluate(STAFF | PUBLIC, anonymous) == Q(is_private__exact=False)
    assert evaluate(STAFF & PUBLIC, anonymous) is False
    assert evaluate(STAFF & PUBLIC, staff) == Q(is_private__exact=False)
    assert evaluate(~PUBLIC, None) == ~Q(is_private__exact=False)
    assert evaluate(Actor("missing").is_true(), object()) is False
    assert evaluate(Actor("rank").gt(1), object()) is False
    assert evaluate(Field("rank").in_([1, 2]), None) == Q(rank__in=(1, 2))
    assert evaluate(Field("rank").ne(1) & Field("rank").lte(5), None) == (
        ~Q(rank__exact=1) & Q(rank__lte=5)
    )


def test_rule_and_term_validation() -> None:
    with pytest.raises(ValueError, match="identifier"):
        Rule("not valid", STAFF)
    with pytest.raises(ValueError, match="identifier"):
        Actor("not valid")
    with pytest.raises(ValueError, match="lookup path"):
        Field("__is_private")
    assert str(Rule("visible", STAFF | PUBLIC)) == (
        "visible := (actor.is_staff eq True OR row.is_private eq False)"
    )
    assert Rule("a", STAFF, blessed="why") == Rule("a", STAFF)


def test_owner_of_an_inherited_field_rule_is_the_abstract_mixin_that_owns_the_field() -> None:
    computed = owner(Field("title").eq("x"), library_models.ReadingList)
    assert computed.model is library_models.TitledEntry
    assert str(computed) == "TitledEntry"
    # A field the child adds itself pulls the owner back down to the child.
    assert owner(Field("pk").gt(1), library_models.ReadingList).model is library_models.ReadingList


def test_owner_of_a_multi_table_parent_field_rule_is_the_parent() -> None:
    # ``name`` lives in ``Venue``'s table; ``LendingDesk`` and ``SelfServeDesk`` reach it
    # through the parent link, so the parent is the one place the rule is authored.
    assert owner(Field("name").ne(""), library_models.SelfServeDesk).model is library_models.Venue
    assert owner(Field("window_count").gt(0), library_models.SelfServeDesk).model is (
        library_models.LendingDesk
    )
    assert owner(Field("kiosk_code").ne(""), library_models.SelfServeDesk).model is (
        library_models.SelfServeDesk
    )
