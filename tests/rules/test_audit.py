"""The reduction audit over declared, inherited, schema-level and opaque visibility."""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from apps.library import models as library_models
from apps.products import models as products_models

from django_strawberry_framework import DjangoType, apply_cascade_permissions
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.rules import Actor, Field, Rule, audit, render
from django_strawberry_framework.schema import DjangoSchema

STAFF = Rule("staff_bypass", Actor("is_staff").is_true())
ACTIVE = Rule("active", Actor("is_active").is_true())
PUBLIC = Rule("public", Field("is_private").is_false())
VISIBLE = Rule("visible", Actor("is_staff").is_true() | Field("is_private").is_false())


@pytest.fixture(autouse=True)
def _isolated_registry(isolate_global_registry: None) -> Iterator[None]:
    yield


def _node(name: str, model: type, **meta: object) -> type[DjangoType]:
    attrs = {"model": model, "fields": ("id", "is_private"), **meta}
    return type(name, (DjangoType,), {"Meta": type("Meta", (), attrs)})


def test_the_declared_but_misplaced_shape_is_reported_leaf_by_leaf() -> None:
    _node("CategoryNode", products_models.Category, visibility=(VISIBLE,))
    _node("ItemNode", products_models.Item, visibility=(VISIBLE,))

    report = audit()

    assert (
        report.R,
        report.M,
        report.B,
        report.reduced,
    ) == (
        2,
        2,
        0,
        False,
    )
    kinds = sorted(f.kind for f in report.findings)
    assert kinds == [
        "branch in disguise",
        "branch in disguise",
        "identical duplication",
        "isomorphic duplication",
        "misplaced (stated too low)",
        "misplaced (stated too low)",
    ]
    identical = next(f for f in report.findings if f.kind == "identical duplication")
    assert identical.sites == ("CategoryNode", "ItemNode")
    assert identical.remedy == "author once at schema"
    isomorphic = next(f for f in report.findings if f.kind == "isomorphic duplication")
    assert "['is_private']" in isomorphic.remedy
    text = render(report, "declared")
    assert "verdict: NOT REDUCED" in text
    assert "MISPLACED" in text


def test_the_reduced_shape_counts_a_mixin_rule_once_and_a_schema_bypass_at_its_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ``TitledEntry`` is the abstract base both reading-list models inherit; a
    # rule declared there reaches both concrete models as derived copies.
    monkeypatch.setattr(
        library_models.TitledEntry,
        "visibility",
        (Rule("titled", Field("title").ne("")),),
        raising=False,
    )
    _node("ReadingListNode", library_models.ReadingList, fields=("id", "title"))
    _node("ReadingListEntryNode", library_models.ReadingListEntry, fields=("id", "title"))

    report = audit(SimpleNamespace(visibility=(STAFF,)))

    assert (
        report.R,
        report.M,
        report.B,
        report.reduced,
    ) == (
        1,
        0,
        0,
        True,
    )
    assert [(leaf.rule.name, leaf.site.label, str(leaf.owner)) for leaf in report.leaves] == [
        ("staff_bypass", "schema", "schema"),
        ("titled", "TitledEntry", "TitledEntry"),
    ]
    assert report.findings == []
    assert "verdict: REDUCED" in render(report)


def test_an_opaque_hook_is_named_with_its_cascade_invocations() -> None:
    class OpaqueNode(DjangoType):
        class Meta:
            model = products_models.Item
            fields = ("id", "is_private")

        @classmethod
        def get_queryset(cls, queryset, info):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)

    report = audit()

    assert report.opaque == [("OpaqueNode", 1)]
    assert report.leaves == []
    assert not report.reduced
    text = render(report)
    assert "cascade invocation sites      = 1" in text
    assert "opaque bodies are uncounted" in text


def test_a_blessed_rule_is_counted_in_b_and_excluded_from_r_and_m() -> None:
    blessed = Rule("staff_bypass", Actor("is_staff").is_true(), blessed="legacy tenant")
    _node("CategoryNode", products_models.Category, visibility=(blessed,))
    _node("ItemNode", products_models.Item, visibility=(blessed,))

    report = audit()

    assert (
        report.R,
        report.M,
        report.D,
        report.B,
    ) == (
        1,
        0,
        0,
        2,
    )


def test_a_blessed_opaque_hook_is_counted_in_b_instead_of_o() -> None:
    class LicensedNode(DjangoType):
        class Meta:
            model = products_models.Item
            fields = ("id", "is_private")
            blessed = "filters through the licensing service"

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.none()

    report = audit()

    assert report.opaque == []
    assert report.blessed_opaque == [("LicensedNode", "filters through the licensing service")]
    assert (report.B, report.reduced) == (1, True)
    assert "blessed get_queryset body: LicensedNode" in render(report)

    with pytest.raises(ConfigurationError, match="does not override get_queryset"):
        _node("PlainNode", products_models.Category, blessed="no hook here")
    with pytest.raises(ConfigurationError, match="non-empty reason string"):
        type(
            "EmptyNode",
            (LicensedNode,),
            {"Meta": type("Meta", (), {"model": products_models.Category, "blessed": ""})},
        )


def test_isomorphic_copies_raise_r_like_identical_ones() -> None:
    _node("CategoryNode", products_models.Category, visibility=(PUBLIC,))
    _node("ItemNode", products_models.Item, visibility=(PUBLIC,))

    report = audit()

    assert (report.R, report.M, report.reduced) == (2, 0, False)
    assert [f.kind for f in report.findings] == ["isomorphic duplication"]


def test_divergent_copies_share_a_name_but_not_a_body() -> None:
    _node("CategoryNode", products_models.Category, visibility=(PUBLIC,))
    _node(
        "ItemNode",
        products_models.Item,
        visibility=(Rule("public", Field("is_private").ne(True)),),
    )

    report = audit()

    divergent = [f for f in report.findings if f.kind == "divergent duplication"]
    assert len(divergent) == 1
    assert divergent[0].sites == ("CategoryNode", "ItemNode")
    assert (report.D, report.reduced) == (1, False)


def test_divergence_is_judged_on_the_canonical_body() -> None:
    _node("CategoryNode", products_models.Category, visibility=(VISIBLE,))
    _node(
        "ItemNode",
        products_models.Item,
        visibility=(
            Rule("visible", Field("is_private").is_false() | Actor("is_staff").is_true()),
        ),
    )

    report = audit()

    assert report.D == 0
    assert "divergent duplication" not in {f.kind for f in report.findings}


def test_two_types_on_one_model_are_two_authored_sites() -> None:
    _node("CategoryNode", products_models.Category, visibility=(PUBLIC,))
    _node("CategoryAdminNode", products_models.Category, visibility=(PUBLIC,))

    report = audit()

    identical = [f for f in report.findings if f.kind == "identical duplication"]
    assert (report.R, report.reduced) == (2, False)
    assert identical[0].sites == ("CategoryAdminNode", "CategoryNode")


def test_a_hand_written_body_beside_declared_rules_makes_the_type_opaque() -> None:
    class LeakyNode(DjangoType):
        class Meta:
            model = products_models.Item
            fields = ("id", "is_private")
            visibility = (PUBLIC,)

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset

    report = audit()

    assert report.opaque == [("LeakyNode", 0)]
    assert [leaf.rule.name for leaf in report.leaves] == ["public"]
    assert not report.reduced


def test_an_actor_conjunct_is_owned_by_the_schema_restrictions_not_offered_as_a_bypass() -> None:
    active_public = Rule("active_public", Actor("is_active").is_true() & PUBLIC.predicate)
    _node("CategoryNode", products_models.Category, visibility=(active_public,))

    report = audit()

    assert (report.M, report.reduced) == (1, False)
    assert [(str(leaf.owner), leaf.split) for leaf in report.leaves] == [
        ("schema restrictions", True),
        ("Category", True),
    ]
    misplaced = next(f for f in report.findings if f.kind.startswith("misplaced"))
    assert misplaced.kind == "misplaced (stated too low)"
    assert misplaced.remedy == "move up to schema restrictions (L6 actor/policy)"


def test_a_lone_actor_rule_on_a_type_is_a_restriction_not_a_bypass() -> None:
    # Enforcement ANDs a type's rules, so ``staff`` alone on a type means "only
    # staff see these rows": its owner is the restriction scope, not the bypass list.
    _node("CategoryNode", products_models.Category, visibility=(STAFF,))

    report = audit(SimpleNamespace(visibility=(STAFF,)))

    assert [(leaf.site.label, str(leaf.owner)) for leaf in report.leaves] == [
        ("schema", "schema"),
        ("CategoryNode", "schema restrictions"),
    ]
    assert report.M == 1
    isomorphic = [f for f in report.findings if f.kind == "isomorphic duplication"]
    assert (
        isomorphic[0].remedy
        == "a grant at one site and a restriction at another: two rules, not one"
    )


def test_a_universal_restriction_restated_per_model_is_owned_once_by_the_schema() -> None:
    # The inverse of the lead example: ``active AND titled`` on two types. The actor
    # conjunct reads no row, so both copies have one owner, the schema's restriction
    # scope, and the finding is identical duplication with a real remedy.
    rule = Rule("active_titled", Actor("is_active").is_true() & Field("title").ne(""))
    _node(
        "ReadingListNode",
        library_models.ReadingList,
        fields=("id", "title"),
        visibility=(rule,),
    )
    _node(
        "ReadingListEntryNode",
        library_models.ReadingListEntry,
        fields=("id", "title"),
        visibility=(rule,),
    )

    report = audit()

    actor = next(
        f
        for f in report.findings
        if f.leaf == "actor.is_active eq True" and f.kind == "identical duplication"
    )
    assert actor.remedy == "author once at schema restrictions"
    # M: the actor conjunct twice (owner: schema restrictions) and the title conjunct
    # twice (owner: the abstract ``TitledEntry`` that declares ``title``).
    assert (report.R, report.M, report.I) == (2, 4, 0)

    reduced = audit(SimpleNamespace(restrictions=(Rule("active", Actor("is_active").is_true()),)))
    assert [(leaf.site.label, str(leaf.owner)) for leaf in reduced.leaves][:1] == [
        ("schema restrictions", "schema restrictions"),
    ]


def test_a_rule_naming_no_field_is_refused_at_definition() -> None:
    with pytest.raises(ConfigurationError, match="names no field 'no_such_field'"):
        _node(
            "BadNode",
            products_models.Item,
            visibility=(Rule("ghost", Field("no_such_field").is_true()),),
        )
    with pytest.raises(ConfigurationError, match="names no field 'nope'"):
        _node(
            "BadNode",
            products_models.Item,
            visibility=(Rule("ghost", Field("category__nope").is_true()),),
        )


def test_cascade_alone_declares_nothing_and_a_visibility_field_is_not_a_rule_tuple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from django_strawberry_framework.rules.apply import model_rule_sites

    node = _node("CategoryNode", products_models.Category, cascade=False)
    assert node.has_custom_get_queryset() is False
    assert audit().reduced

    monkeypatch.setattr(products_models.Item, "visibility", object(), raising=False)
    assert model_rule_sites(products_models.Item) == ()
    _node("ItemNode", products_models.Item)


def test_declaring_visibility_marks_the_hook_custom_and_validates_shape() -> None:
    node = _node("CategoryNode", products_models.Category, visibility=(PUBLIC,), cascade=False)
    assert node.has_custom_get_queryset()
    assert node.__visibility_rules__ == (PUBLIC,)
    assert node.__cascade__ is False
    assert _node("PlainNode", products_models.Item).has_custom_get_queryset() is False

    with pytest.raises(ConfigurationError, match="must be a list or tuple of Rule"):
        _node("BadNode", products_models.Item, visibility=PUBLIC)
    with pytest.raises(ConfigurationError, match="every entry must be a Rule"):
        _node("BadNode", products_models.Item, visibility=("public",))
    with pytest.raises(ConfigurationError, match="cascade must be a bool"):
        _node("BadNode", products_models.Item, cascade="no")


def test_the_schema_scope_refuses_a_rule_that_reads_a_row() -> None:
    import strawberry

    @strawberry.type
    class Query:
        ok: bool = strawberry.field(resolver=lambda: True)

    with pytest.raises(ConfigurationError, match=r"reads row fields \['is_private'\]"):
        DjangoSchema(query=Query, visibility=[PUBLIC])
    with pytest.raises(ConfigurationError, match="cannot be a schema-wide restrictions rule"):
        DjangoSchema(query=Query, restrictions=[PUBLIC])
    with pytest.raises(ConfigurationError, match="every entry must be a Rule"):
        DjangoSchema(query=Query, visibility=["staff"])
    with pytest.raises(ConfigurationError, match=r"restrictions=\.\.\.\) holds 'active'"):
        DjangoSchema(query=Query, restrictions=["active"])
    assert DjangoSchema(query=Query, visibility=[STAFF]).visibility == (STAFF,)
    assert DjangoSchema(query=Query).visibility == ()
    assert DjangoSchema(query=Query, restrictions=[ACTIVE]).restrictions == (ACTIVE,)
    assert DjangoSchema(query=Query).restrictions == ()


def _list_schema(node: type[DjangoType], **extra: object) -> DjangoSchema:
    import strawberry

    from django_strawberry_framework import DjangoListField
    from django_strawberry_framework.types.finalizer import finalize_django_types

    query = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"categories": list[node]}, "categories": DjangoListField(node)},
        ),
    )
    finalize_django_types()
    return DjangoSchema(query=query, **extra)


def _names(schema: DjangoSchema, user: object) -> list[str]:
    from django.test import RequestFactory

    request = RequestFactory().get("/graphql/")
    request.user = user  # type: ignore[assignment]
    result = schema.execute_sync(
        "{ categories { name } }",
        context_value=SimpleNamespace(request=request),
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    return sorted(row["name"] for row in result.data["categories"])


@pytest.mark.django_db
def test_a_schema_restriction_reaches_every_type_and_sits_above_the_bypass() -> None:
    from apps.products import services

    services.seed_data(1)
    products_models.Category.objects.filter(pk=products_models.Category.objects.first().pk).update(
        is_private=True,
    )
    public = sorted(
        products_models.Category.objects.filter(is_private=False).values_list("name", flat=True),
    )
    everything = sorted(products_models.Category.objects.values_list("name", flat=True))
    plain = _node("PlainNode", products_models.Category, fields=("id", "name"), primary=True)
    ruled = _node(
        "RuledNode",
        products_models.Category,
        fields=("id", "name"),
        visibility=(PUBLIC,),
    )
    restated = _node(
        "RestatedNode",
        products_models.Category,
        fields=("id", "name"),
        visibility=(ACTIVE, PUBLIC),
    )
    active_staff = SimpleNamespace(is_active=True, is_staff=True, is_authenticated=True)
    suspended_staff = SimpleNamespace(is_active=False, is_staff=True, is_authenticated=True)
    member = SimpleNamespace(is_active=True, is_staff=False, is_authenticated=True)

    # A type with no rule of its own is still subject to the schema's restriction.
    restricted_plain = _list_schema(plain, restrictions=[ACTIVE])
    assert _names(restricted_plain, member) == everything
    assert _names(restricted_plain, suspended_staff) == []

    # The restriction is evaluated above the bypass: a passing bypass cannot beat it.
    restricted_ruled = _list_schema(ruled, visibility=[STAFF], restrictions=[ACTIVE])
    assert _names(restricted_ruled, active_staff) == everything
    assert _names(restricted_ruled, member) == public
    assert _names(restricted_ruled, suspended_staff) == []

    # Stated per type instead, the same restriction loses to the bypass.
    leaky = _list_schema(restated, visibility=[STAFF])
    assert _names(leaky, suspended_staff) == everything
    assert _names(leaky, member) == public
