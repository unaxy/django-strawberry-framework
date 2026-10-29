"""Relation utility tests for kinds, many-side detection, instance accessors, and package re-exports.

``classify_path`` / ``validate_lookup_expr`` are construction-time taxonomy.
Traversal on the wire is ``examples/fakeshop/test_query/test_library_api.py``.
"""

import sys
import typing
from collections.abc import Callable
from dataclasses import FrozenInstanceError, dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from apps.kanban.models import Decision
from apps.library.models import (
    Book,
    Branch,
    Genre,
    LendingDesk,
    Loan,
    MembershipCard,
    Patron,
    PatronProfile,
    SelfServeDesk,
    TaggedItem,
    Venue,
)
from apps.library.models import Branch as _Branch
from apps.library.models import Shelf as _Shelf
from apps.scalars.models import ScalarSpecimen
from django.apps import AppConfig
from django.apps.registry import Apps
from django.contrib.admin.utils import lookup_spawns_duplicates
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Model, TextField
from django.db.models.fields.json import KeyTransformExact, KeyTransformIContains
from django.db.models.fields.related_lookups import RelatedExact, RelatedIsNull
from django.db.models.functions import Lower
from django.db.models.lookups import Exact, IContains, Lookup
from django.test.utils import register_lookup

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    LookupValidationError,
    PathResolutionError,
)
from django_strawberry_framework.utils import relations as relations_module
from django_strawberry_framework.utils._narrowing import call_method, read_attr
from django_strawberry_framework.utils.relations import (
    ClassifiedPath,
    RelationKind,
    RelationPathHop,
    _classify_path_cached,
    _is_traversable_relation,
    _lenient_traverses_to_many,
    carrier_backed_link,
    classify_path,
    has_composite_pk,
    instance_accessor,
    is_forward_concrete_relation,
    is_forward_many_to_many,
    is_many_side_relation_kind,
    is_row_key_column,
    is_single_column_foreign_key,
    m2m_through_link_fields,
    m2m_through_model,
    non_pk_forward_link,
    non_pk_relation_key_attname,
    order_column_paths,
    path_traverses_to_many,
    relation_bool,
    relation_kind,
    relation_link,
    respell_relation_path,
    reverse_relation_by_accessor,
    stored_value_column,
    validate_lookup_expr,
)
from tests._relation_fixtures import RpCompositeParent
from tests.optimizer._link_models import (
    LnkColumnChild,
    LnkPairChild,
    LnkParent,
    LnkSlugChild,
    LnkSlugObjectChild,
    LnkTag,
)
from tests.optimizer._spelling_models import SpBadge, SpCard, SpParent

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from django_strawberry_framework.utils.relations import RelationSpelling
    from django_strawberry_framework.utils.typing import ModelField


def _serving_field(
    monkeypatch: pytest.MonkeyPatch,
    answer: Callable[[str], object],
) -> type[Model]:
    """A real model (``Book``) whose ``_meta.get_field`` answers every segment through ``answer``.

    The answer is planted in the ``Options`` instance dict, so the undo deletes
    it and the class method shows through again.
    """
    monkeypatch.setitem(vars(Book._meta), "get_field", answer)
    return Book


@dataclass(frozen=True)
class _RelationDouble:
    """A relation field's metadata reads, pinned to one Django version's shape."""

    is_relation: bool
    many_to_many: bool
    one_to_many: bool
    one_to_one: bool
    auto_created: bool
    concrete: bool
    column: str | None
    related_model: type[Model]


def test_relation_kind_classifies_many_to_many_as_many() -> None:
    field = SimpleNamespace(
        many_to_many=True,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
    )

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_one_to_many_as_reverse_many_to_one() -> None:
    """A ``one_to_many`` shape that is no ``GenericRelation`` is a reverse FK, ``auto_created`` or not."""
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
    )

    assert relation_kind(field) == "reverse_many_to_one"


def test_relation_kind_classifies_generic_relation() -> None:
    """A ``GenericRelation``-shaped field classifies as ``"generic"`` before the ``one_to_many`` arm.

    Detected duck-typed by non-``None`` ``content_type_field_name`` /
    ``object_id_field_name`` slots, BEFORE the ``one_to_many`` arm below.
    """
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
        content_type_field_name="content_type",
        object_id_field_name="object_id",
    )

    assert relation_kind(field) == "generic"


def test_relation_kind_none_valued_generic_slots_are_not_generic() -> None:
    """``None`` content-type / object-id slots (a plain ``FieldMeta``) are NOT generic.

    ``FieldMeta`` is a slotted dataclass that always carries the two slots
    defaulted to ``None``, so the detector reads ``getattr(...) is not None``,
    not ``hasattr`` - otherwise every ``FieldMeta`` snapshot would misclassify
    as ``"generic"``.
    """
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
        content_type_field_name=None,
        object_id_field_name=None,
    )

    assert relation_kind(field) == "reverse_many_to_one"


def test_relation_kind_generic_is_in_literal() -> None:
    """The ``RelationKind`` alias enumerates ``"generic"``."""
    assert "generic" in typing.get_args(RelationKind)


def test_relation_kind_classifies_auto_created_one_to_many_as_reverse_many_to_one() -> None:
    """Reverse-FK descriptor (Django ``ManyToOneRel``): ``one_to_many`` + ``auto_created``."""
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=True,
    )

    assert relation_kind(field) == "reverse_many_to_one"


def test_relation_kind_reverse_many_to_one_is_in_literal() -> None:
    """The ``RelationKind`` alias enumerates ``"reverse_many_to_one"``.

    ``relation_kind`` returns this value for a reverse foreign key, so the
    alias that types its return must list it.
    """
    assert "reverse_many_to_one" in typing.get_args(RelationKind)


def test_is_many_side_relation_kind_matches_list_valued_shapes() -> None:
    assert is_many_side_relation_kind("many") is True
    assert is_many_side_relation_kind("reverse_many_to_one") is True
    assert is_many_side_relation_kind("generic") is True
    assert is_many_side_relation_kind("reverse_one_to_one") is False
    assert is_many_side_relation_kind("forward_single") is False
    assert is_many_side_relation_kind(None) is False


def test_relation_kind_classifies_auto_created_one_to_one_as_reverse() -> None:
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        concrete=False,
    )

    assert relation_kind(field) == "reverse_one_to_one"


def test_relation_kind_classifies_forward_single_relations() -> None:
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=False,
    )

    assert relation_kind(field) == "forward_single"


def test_relation_kind_classifies_concrete_auto_created_o2o_as_forward_single() -> None:
    """An auto-created MTI parent link is concrete and forward."""
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        concrete=True,
    )

    assert relation_kind(field) == "forward_single"


def test_is_forward_many_to_many_accepts_concrete_forward_m2m() -> None:
    """A forward ``ManyToManyField`` is concrete and not auto-created."""
    field = SimpleNamespace(many_to_many=True, concrete=True, auto_created=False)
    assert is_forward_many_to_many(field) is True


def test_is_forward_many_to_many_rejects_reverse_m2m_accessor() -> None:
    """A reverse M2M accessor is auto-created and not concrete."""
    field = SimpleNamespace(many_to_many=True, concrete=False, auto_created=True)
    assert is_forward_many_to_many(field) is False


def test_is_forward_many_to_many_rejects_non_m2m() -> None:
    field = SimpleNamespace(many_to_many=False, concrete=True, auto_created=False)
    assert is_forward_many_to_many(field) is False


def test_is_forward_many_to_many_stock_book_genres() -> None:
    """Library ``Book.genres`` is a forward writable M2M; reverse is not."""
    assert is_forward_many_to_many(Book._meta.get_field("genres")) is True
    assert is_forward_many_to_many(Genre._meta.get_field("books")) is False


def test_instance_accessor_uses_get_accessor_name_for_reverse_relations() -> None:
    """A reverse rel's instance attribute is ``get_accessor_name()``, not ``name``.

    For a reverse FK declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related QUERY name (``"book"``) while the
    instance attribute is ``"book_set"``.
    """
    rel = SimpleNamespace(name="book", get_accessor_name=lambda: "book_set")
    assert instance_accessor(rel) == "book_set"


def test_instance_accessor_falls_back_to_name_for_forward_fields() -> None:
    """Forward fields have no ``get_accessor_name``; ``name`` IS the attribute."""
    field = SimpleNamespace(name="genres")
    assert instance_accessor(field) == "genres"


def test_instance_accessor_prefers_precomputed_field_meta_slot() -> None:
    """A ``FieldMeta``-style ``accessor_name`` slot wins over any live lookup.

    ``FieldMeta`` cannot answer ``get_accessor_name()`` (it is a frozen
    snapshot), so the builders precompute the accessor into ``accessor_name``
    and this helper reads it first - the optimizer walker passes ``FieldMeta``
    values, not raw descriptors.
    """
    meta_like = SimpleNamespace(
        name="book",
        accessor_name="book_set",
        get_accessor_name=lambda: "WRONG-not-consulted",
    )
    assert instance_accessor(meta_like) == "book_set"


@pytest.mark.parametrize(
    (
        "model",
        "path",
        "source",
        "expected",
    ),
    [
        (
            SpParent,
            "cards",
            "query",
            "card",
        ),
        (
            SpParent,
            "card",
            "accessor",
            "cards",
        ),
        (
            SpParent,
            "cards__genres",
            "query",
            "card__genres",
        ),
        (
            SpParent,
            "card__genres__cards",
            "accessor",
            "cards__genres__cards",
        ),
        (
            SpCard,
            "parent__card",
            "accessor",
            "parent__cards",
        ),
        (
            SpParent,
            "badge",
            "query",
            "badge",
        ),
        (
            SpParent,
            "badge",
            "accessor",
            "badge",
        ),
        (
            Genre,
            "books",
            "query",
            "books",
        ),
        (
            Book,
            "genres",
            "accessor",
            "genres",
        ),
    ],
)
def test_respell_relation_path_translates_each_hop(
    model: type[Model],
    path: str,
    source: "RelationSpelling",
    expected: str,
) -> None:
    """Each hop is spelled in the other vocabulary through Django's relation metadata.

    ``SpParent.card`` is a reverse one-to-one declared ``related_name="card",
    related_query_name="cards"``: its query name answers ``select_related`` and
    ``only()``, its accessor ``prefetch_related``. A forward hop (``genres``,
    ``parent``, ``category``) and a reverse relation whose two names coincide
    (``badge``, ``books``) are spelled the same both ways.
    """
    assert respell_relation_path(model, path, source=source) == expected


@pytest.mark.parametrize(
    ("model", "path", "source"),
    [
        (SpParent, "card", "query"),
        (SpParent, "cards", "accessor"),
        (SpParent, "nope", "query"),
        (SpParent, "code", "query"),
        (SpCard, "parent_id", "query"),
        (SpCard, "genres__nope", "accessor"),
        (TaggedItem, "content_object", "query"),
        (SpBadge, "parent__card__name", "accessor"),
    ],
)
def test_respell_relation_path_answers_none_for_a_path_it_cannot_spell(
    model: type[Model],
    path: str,
    source: "RelationSpelling",
) -> None:
    """A path whose hops are not all relations in the given spelling has no translation.

    The accessor of ``SpParent.card`` is no query name and its query name no
    accessor; an unknown name, a column, a foreign key's ``attname``, a
    ``GenericForeignKey`` (no related model) and a trailing column all stop the
    walk, and the caller compares the path as written.
    """
    assert respell_relation_path(model, path, source=source) is None


_respell_apps = Apps([AppConfig("test_relations_respell", sys.modules[__name__])])


class _RsParent(models.Model):
    """A parent where ``cards`` is the query name of one relation and the accessor of another.

    Django's relation check ``fields.E305`` refuses the pair, so only a project
    that silences it can hold it; the models live in the private
    ``_respell_apps`` registry, so the system checks never see them and no test
    creates their tables (only model metadata is read).
    """

    name: "models.TextField[str | Combinable, str]" = models.TextField()
    friends: "models.ManyToManyField[_RsParent, models.Model]" = models.ManyToManyField("self")

    class Meta:
        app_label = "test_relations_respell"
        apps = _respell_apps


class _RsCard(models.Model):
    """Reached as ``parent.card``, queried as ``cards``."""

    parent: "models.OneToOneField[_RsParent | Combinable, _RsParent]" = models.OneToOneField(
        _RsParent,
        on_delete=models.CASCADE,
        related_name="card",
        related_query_name="cards",
    )

    class Meta:
        app_label = "test_relations_respell"
        apps = _respell_apps


class _RsSleeve(models.Model):
    """Reached as ``parent.cards``, queried as ``sleeves``."""

    parent: "models.ForeignKey[_RsParent | Combinable, _RsParent]" = models.ForeignKey(
        _RsParent,
        on_delete=models.CASCADE,
        related_name="cards",
        related_query_name="sleeves",
    )

    class Meta:
        app_label = "test_relations_respell"
        apps = _respell_apps


def test_respell_relation_path_reads_a_shared_name_in_the_spelling_it_is_given() -> None:
    """``cards`` names ``_RsCard`` as a query name and ``_RsSleeve`` as an accessor.

    The translation never guesses: the spelling a path arrives in picks the
    relation, and ``reverse_relation_by_accessor`` answers only by accessor.
    """
    card_rel = _RsParent._meta.get_field("cards")
    assert card_rel.related_model is _RsCard
    assert respell_relation_path(_RsParent, "cards", source="query") == "card"
    assert respell_relation_path(_RsParent, "cards", source="accessor") == "sleeves"
    assert respell_relation_path(_RsParent, "sleeves", source="query") == "cards"
    assert respell_relation_path(_RsParent, "card", source="accessor") == "cards"
    sleeve_rel = reverse_relation_by_accessor(_RsParent, "cards")
    assert sleeve_rel is not None
    assert sleeve_rel.related_model is _RsSleeve
    assert reverse_relation_by_accessor(_RsParent, "sleeves") is None


def test_respell_relation_path_answers_none_for_a_relation_without_an_accessor() -> None:
    """A symmetrical many-to-many on ``self`` has a reverse relation and no accessor.

    Django's ``ManyToManyRel.get_accessor_name()`` answers ``None`` for it, so
    the query-spelled path has no accessor spelling.
    """
    hidden = next(
        field
        for field in _RsParent._meta.get_fields(include_hidden=True)
        if isinstance(field, models.ManyToManyRel) and field.related_model is _RsParent
    )
    assert hidden.get_accessor_name() is None
    assert respell_relation_path(_RsParent, hidden.name, source="query") is None


# ---------------------------------------------------------------------------
# classify_path: strict, immutable model-path classification.
# ---------------------------------------------------------------------------


def test_classify_path_local_scalar_has_no_hops() -> None:
    """A local column classifies to zero hops with the concrete field as terminal."""
    plan = classify_path(Book, "title")

    assert isinstance(plan, ClassifiedPath)
    assert plan.model is Book
    assert plan.path == "title"
    assert plan.hops == ()
    assert plan.terminal is Book._meta.get_field("title")
    assert plan.first_many_index is None
    assert plan.relation_chain == ()


def test_classify_path_forward_fk_chain_is_row_preserving() -> None:
    """A forward FK chain yields forward_single hops and no many boundary."""
    plan = classify_path(Book, "shelf__branch__name")

    assert [hop.segment for hop in plan.hops] == ["shelf", "branch"]
    assert [hop.kind for hop in plan.hops] == ["forward_single", "forward_single"]
    assert [hop.many_side for hop in plan.hops] == [False, False]

    assert [hop.target_model for hop in plan.hops] == [_Shelf, _Branch]
    assert plan.terminal is _Branch._meta.get_field("name")
    assert plan.first_many_index is None
    assert plan.relation_chain == ("shelf", "branch")


def test_classify_path_accepts_pk_alias_mid_and_tail() -> None:
    """``pk`` resolves to the model's pk field as a scalar terminal after a FK hop."""
    plan = classify_path(Book, "shelf__pk")

    assert [hop.segment for hop in plan.hops] == ["shelf"]
    assert plan.terminal is _Shelf._meta.pk
    assert plan.first_many_index is None
    assert plan.relation_chain == ("shelf",)

    deep = classify_path(Book, "shelf__branch__pk")
    assert deep.relation_chain == ("shelf", "branch")
    assert deep.terminal is Branch._meta.pk


def test_classify_path_reverse_fk_is_first_many() -> None:
    """A leading reverse FK is the first many-side boundary."""
    plan = classify_path(Book, "loans__note")

    (hop,) = plan.hops
    assert hop.segment == "loans"
    assert hop.kind == "reverse_many_to_one"
    assert hop.target_model is Loan
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert plan.terminal is Loan._meta.get_field("note")
    assert plan.relation_chain == ("loans",)


def test_classify_path_forward_m2m_is_first_many() -> None:
    """A forward M2M is a many-side hop even where its PathInfo expansion is mixed."""
    plan = classify_path(Book, "genres__name")

    (hop,) = plan.hops
    assert hop.segment == "genres"
    assert hop.kind == "many"
    assert hop.target_model is Genre
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert plan.terminal is Genre._meta.get_field("name")


def test_classify_path_reverse_m2m_is_first_many() -> None:
    """The reverse side of an M2M is also many-side."""
    plan = classify_path(Genre, "books__title")

    (hop,) = plan.hops
    assert hop.segment == "books"
    assert hop.kind == "many"
    assert hop.target_model is Book
    assert hop.many_side is True
    assert plan.first_many_index == 0


def test_classify_path_generic_relation_is_many_side() -> None:
    """A ``GenericRelation`` is a traversable many-side hop classified ``generic``."""
    plan = classify_path(Branch, "tags__tag")

    (hop,) = plan.hops
    assert hop.segment == "tags"
    assert hop.kind == "generic"
    assert hop.target_model is TaggedItem
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert plan.terminal is TaggedItem._meta.get_field("tag")


def test_classify_path_reverse_o2o_is_row_preserving() -> None:
    """A reverse O2O is single-valued: reverse_one_to_one, no many boundary."""
    plan = classify_path(Patron, "card__barcode")

    (hop,) = plan.hops
    assert hop.segment == "card"
    assert hop.kind == "reverse_one_to_one"
    assert hop.target_model is MembershipCard
    assert hop.many_side is False
    assert plan.first_many_index is None
    assert plan.terminal is MembershipCard._meta.get_field("barcode")


def test_classify_path_named_reverse_fk_behind_to_one_prefix() -> None:
    """The named Medtrics category: a reverse FK behind a to-one prefix.

    ``Loan.book -> Book.loans -> Loan.patron -> Patron.email`` contains NO
    ``ManyToManyField``; the row-multiplying hop is the mid-path reverse FK, so
    ``first_many_index`` MUST be 1, not 0.
    """
    plan = classify_path(Loan, "book__loans__patron__email")

    assert [hop.segment for hop in plan.hops] == ["book", "loans", "patron"]
    assert [hop.kind for hop in plan.hops] == [
        "forward_single",
        "reverse_many_to_one",
        "forward_single",
    ]
    assert [hop.many_side for hop in plan.hops] == [False, True, False]
    assert [hop.target_model for hop in plan.hops] == [Book, Loan, Patron]
    assert plan.terminal is Patron._meta.get_field("email")
    assert plan.first_many_index == 1
    assert plan.relation_chain == ("book", "loans", "patron")


_unique_reverse_apps = Apps([AppConfig("test_relations_unique_reverse", sys.modules[__name__])])


class _UrParent(models.Model):
    """A parent reached in reverse by one unique and one ordinary ``ForeignKey``.

    Fakeshop declares no ``ForeignKey(unique=True)``, so these models stand in for
    the unique-reverse hop. They live in the private ``_unique_reverse_apps``
    registry, whose one app config (this module) lets Django wire the reverse
    relations: no installed model gains a reverse relation, ``migrate`` and the
    system checks never see them, and no test creates their tables (only model
    metadata is read).
    """

    name: "models.TextField[str | Combinable, str]" = models.TextField()

    class Meta:
        app_label = "test_relations_unique_reverse"
        apps = _unique_reverse_apps


class _UrUniqueChild(models.Model):
    """A child whose ``ForeignKey(unique=True)`` gives ``_UrParent`` a single-valued reverse."""

    note: "models.TextField[str | Combinable, str]" = models.TextField()
    parent: "models.ForeignKey[_UrParent | Combinable, _UrParent]" = models.ForeignKey(
        _UrParent,
        on_delete=models.CASCADE,
        unique=True,
        related_name="unique_children",
    )

    class Meta:
        app_label = "test_relations_unique_reverse"
        apps = _unique_reverse_apps


class _UrPlainChild(models.Model):
    """A child whose ordinary ``ForeignKey`` gives ``_UrParent`` a many-side reverse."""

    note: "models.TextField[str | Combinable, str]" = models.TextField()
    parent: "models.ForeignKey[_UrParent | Combinable, _UrParent]" = models.ForeignKey(
        _UrParent,
        on_delete=models.CASCADE,
        related_name="plain_children",
    )

    class Meta:
        app_label = "test_relations_unique_reverse"
        apps = _unique_reverse_apps


def test_classify_path_unique_reverse_fk_is_row_preserving() -> None:
    """The reverse hop of a ``ForeignKey(unique=True)`` is single-valued.

    ``classify_path`` reads many-ness from ``PathInfo.m2m`` (``not
    field.unique``), so ``_UrParent.unique_children`` keeps its
    ``reverse_many_to_one`` kind yet reports ``many_side`` ``False`` and no many
    boundary, and ``path_traverses_to_many`` answers ``False``: the
    deliberate divergence from a ``relation_kind`` walk documented on
    ``django_strawberry_framework/utils/relations.py::path_traverses_to_many``.
    """
    plan = classify_path(_UrParent, "unique_children__note")

    (hop,) = plan.hops
    assert hop.segment == "unique_children"
    assert hop.kind == "reverse_many_to_one"
    assert hop.target_model is _UrUniqueChild
    assert hop.many_side is False
    assert plan.first_many_index is None
    assert plan.terminal is _UrUniqueChild._meta.get_field("note")
    assert path_traverses_to_many(_UrParent, "unique_children__note") is False
    assert path_traverses_to_many(_UrParent, "unique_children") is False
    assert _segment_walk_traverses_to_many(_UrParent, "unique_children__note") is True


def test_classify_path_plain_reverse_fk_beside_unique_is_first_many() -> None:
    """An ordinary reverse FK on the same parent stays the first many-side boundary.

    The contrast row for the unique reverse hop: ``_UrParent.plain_children``
    has ``PathInfo.m2m`` ``True``, so ``classify_path`` reports ``many_side``
    ``True`` at index 0 and
    ``django_strawberry_framework/utils/relations.py::path_traverses_to_many``
    answers ``True``; uniqueness of the link alone flips the answer.
    """
    plan = classify_path(_UrParent, "plain_children__note")

    (hop,) = plan.hops
    assert hop.segment == "plain_children"
    assert hop.kind == "reverse_many_to_one"
    assert hop.target_model is _UrPlainChild
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert path_traverses_to_many(_UrParent, "plain_children__note") is True
    assert path_traverses_to_many(_UrParent, "plain_children") is True


def test_classify_path_relation_terminal_is_hop_and_terminal() -> None:
    """A relation reached at the final segment is both the last hop and the terminal."""
    plan = classify_path(Book, "genres")

    (hop,) = plan.hops
    genres_field = Book._meta.get_field("genres")
    assert hop.segment == "genres"
    assert hop.kind == "many"
    assert plan.terminal is genres_field
    assert plan.first_many_index == 0
    assert plan.relation_chain == ("genres",)


def test_classify_path_self_referential_forward_chain_is_row_preserving() -> None:
    """A self-FK forward chain of differing depth stays row-preserving."""
    one = classify_path(Decision, "supersedes__question")
    assert [hop.segment for hop in one.hops] == ["supersedes"]
    assert one.hops[0].kind == "forward_single"
    assert one.hops[0].target_model is Decision
    assert one.first_many_index is None

    two = classify_path(Decision, "supersedes__supersedes__question")
    assert [hop.segment for hop in two.hops] == ["supersedes", "supersedes"]
    assert [hop.target_model for hop in two.hops] == [Decision, Decision]
    assert two.first_many_index is None
    assert two.terminal is Decision._meta.get_field("question")


def test_classify_path_self_referential_reverse_fk_is_many() -> None:
    """The reverse side of a self-FK is a many-side hop."""
    plan = classify_path(Decision, "superseded_by_set__question")

    (hop,) = plan.hops
    assert hop.segment == "superseded_by_set"
    assert hop.kind == "reverse_many_to_one"
    assert hop.target_model is Decision
    assert hop.many_side is True
    assert plan.first_many_index == 0


def test_classify_path_unresolvable_segment_raises() -> None:
    """A missing leading segment raises with model, path, and segment named."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(Book, "nonexistent__name")

    err = excinfo.value
    assert err.segment == "nonexistent"
    assert err.field_path == "nonexistent__name"
    assert err.model is Book
    message = str(err)
    assert "library.Book" in message
    assert "nonexistent__name" in message
    assert "nonexistent" in message


def test_classify_path_garbage_tail_after_scalar_raises() -> None:
    """A scalar segment followed by more path components raises."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(Book, "title__nonsense")

    assert excinfo.value.segment == "title"
    assert "title__nonsense" in str(excinfo.value)


def test_classify_path_forward_gfk_traversal_raises() -> None:
    """A forward ``GenericForeignKey`` mid-path raises (no ``path_infos``)."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(TaggedItem, "content_object__x")

    assert excinfo.value.segment == "content_object"
    assert "library.TaggedItem" in str(excinfo.value)


def test_classify_path_bare_forward_gfk_raises() -> None:
    """A bare forward ``GenericForeignKey`` is neither scalar nor traversable."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(TaggedItem, "content_object")

    assert excinfo.value.segment == "content_object"


def test_classify_path_hidden_reverse_relation_raises() -> None:
    """A ``related_name='+'`` hidden reverse name is rejected by ``get_field``.

    No fakeshop model declares ``related_name='+'``; the resolution path is the
    same ``FieldDoesNotExist`` branch a missing name takes, proven above.
    """
    with pytest.raises(PathResolutionError):
        classify_path(Patron, "definitely_hidden_reverse")


def test_classify_path_empty_path_infos_relation_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A relation exposing empty ``path_infos`` raises (defensive - no real field does).

    Stock Django relation descriptors always populate ``path_infos``; this pins
    the fail-closed branch with a real model whose ``get_field`` returns
    a traversable-looking relation with an empty ``path_infos``.
    """
    fake_field = SimpleNamespace(is_relation=True, path_infos=[])
    model = _serving_field(monkeypatch, lambda _name: fake_field)

    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(model, "rel")

    assert excinfo.value.segment == "rel"


def test_classify_path_non_string_path_raises_typed_path_error() -> None:
    """A non-string path is rejected through the path error contract before any split."""
    with pytest.raises(PathResolutionError):
        # basedpyright: the non-str path is the hostile input under test; classify_path types the
        # parameter as str
        classify_path(Book, object())  # pyright: ignore[reportArgumentType]


def test_path_resolution_error_is_configuration_family() -> None:
    """``PathResolutionError`` is catchable as ConfigurationError and the base."""
    err = PathResolutionError(Book, "loans__x", "x")
    assert isinstance(err, ConfigurationError)
    assert isinstance(err, DjangoStrawberryFrameworkError)


def test_relation_path_hop_and_classified_path_are_frozen() -> None:
    """The plan records are immutable frozen dataclasses."""
    hop = RelationPathHop(segment="s", kind="many", target_model=Book, many_side=True)
    with pytest.raises(FrozenInstanceError):
        # basedpyright: a write to the frozen dataclass is the rejected operation under test
        hop.segment = "other"  # pyright: ignore[reportAttributeAccessIssue]

    plan = classify_path(Book, "title")
    with pytest.raises(FrozenInstanceError):
        # basedpyright: a write to the frozen dataclass is the rejected operation under test
        plan.path = "other"  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize(
    ("model", "path"),
    [
        (Book, "title"),
        (Book, "shelf__branch__name"),
        (Book, "shelf__pk"),
        (Book, "loans__note"),
        (Book, "genres__name"),
        (Genre, "books__title"),
        (Branch, "tags__tag"),
        (Patron, "card__barcode"),
        (Loan, "book__loans__patron__email"),
        (Decision, "supersedes__supersedes__question"),
        (Decision, "superseded_by_set__question"),
        (_UrParent, "unique_children__note"),
        (_UrParent, "plain_children__note"),
    ],
)
def test_classify_path_first_many_matches_django_oracle(model: type[Model], path: str) -> None:
    """``first_many_index is not None`` matches Django's own duplicate oracle.

    ``lookup_spawns_duplicates`` is imported in the TEST ONLY - it must never
    appear in production code.
    """
    spawns = classify_path(model, path).first_many_index is not None
    assert spawns == lookup_spawns_duplicates(model._meta, path)


# ---------------------------------------------------------------------------
# validate_lookup_expr: transform + lookup validation, separate from paths.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("lookup_expr", "lookup_name"),
    [
        ("icontains", "IContains"),
        ("exact", "Exact"),
        ("in", "In"),
        ("isnull", "IsNull"),
        ("gte", "GreaterThanOrEqual"),
    ],
)
def test_validate_lookup_expr_plain_lookups_on_scalar(lookup_expr: str, lookup_name: str) -> None:
    """A plain final lookup on a scalar terminal resolves to its lookup class."""
    terminal = Book._meta.get_field("title")
    resolved = validate_lookup_expr(terminal, lookup_expr)
    assert resolved.__name__ == lookup_name


def test_validate_lookup_expr_transform_chain_advances_output_field() -> None:
    """A ``date__year__gte`` chain validates through each transform's output field.

    ``Decision.created_date`` is a ``DateTimeField``: ``date`` -> ``DateField``,
    ``year`` -> ``IntegerField``, then ``gte`` resolves as the integer lookup.
    """
    terminal = Decision._meta.get_field("created_date")
    resolved = validate_lookup_expr(terminal, "date__year__gte")
    # The lookup is resolved against the year transform's IntegerField output.
    assert resolved.__name__ == "YearGte"


def test_validate_lookup_expr_trailing_transform_implies_exact() -> None:
    """A trailing transform (no final lookup) is accepted as ``transform + exact``.

    ``date`` on a ``DateTimeField`` is a transform, not a lookup; Django treats
    a lookup path ending on a transform as an implicit ``exact`` on the
    transform output, so validation returns the ``Exact`` lookup class.
    """
    terminal = Decision._meta.get_field("created_date")
    resolved = validate_lookup_expr(terminal, "date")
    assert resolved.__name__ == "Exact"


def test_validate_lookup_expr_invalid_final_lookup_raises() -> None:
    """An unknown final lookup on a valid terminal raises with message content."""
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "not_a_lookup")

    err = excinfo.value
    assert err.part == "not_a_lookup"
    assert err.lookup_expr == "not_a_lookup"
    assert err.terminal is terminal
    message = str(err)
    assert "not_a_lookup" in message
    assert "title" in message


def test_validate_lookup_expr_invalid_mid_chain_transform_raises() -> None:
    """An unresolvable non-final transform raises naming the offending part."""
    terminal = Decision._meta.get_field("created_date")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "bogus__gte")

    assert excinfo.value.part == "bogus"
    assert "bogus__gte" in str(excinfo.value)


def test_validate_lookup_expr_trailing_transform_without_exact_support_raises() -> None:
    """A final part that is neither a lookup nor a trailing transform raises.

    ``year`` is a valid transform on a ``DateField``, but here ``day`` follows a
    scalar ``TextField`` where it resolves as neither a lookup nor a transform.
    """
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "day")

    assert excinfo.value.part == "day"


@pytest.mark.parametrize("lookup_expr", ["isnull", "exact", "in"])
def test_validate_lookup_expr_relation_descriptor_terminal(lookup_expr: str) -> None:
    """A relation-descriptor terminal resolves relation lookups (isnull/exact/in).

    A reverse-FK descriptor (``Book.loans`` -> ``ManyToOneRel``) answers
    ``get_lookup`` with the ``Related*`` lookup family.
    """
    terminal = Book._meta.get_field("loans")
    resolved = validate_lookup_expr(terminal, lookup_expr)
    assert resolved.__name__.startswith("Related")


def test_validate_lookup_expr_forward_m2m_terminal_isnull() -> None:
    """A forward M2M descriptor terminal resolves ``isnull`` to a lookup class."""
    terminal = Book._meta.get_field("genres")
    resolved = validate_lookup_expr(terminal, "isnull")
    assert resolved.__name__ == "IsNull"


def test_validate_lookup_expr_empty_expr_raises() -> None:
    """An empty lookup expression raises."""
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "")

    assert excinfo.value.lookup_expr == ""


def test_validate_lookup_expr_empty_part_raises() -> None:
    """A trailing ``__`` (empty part) raises."""
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "date__")

    assert excinfo.value.part == ""


def test_lookup_validation_error_is_configuration_family() -> None:
    """``LookupValidationError`` is catchable as ConfigurationError and the base."""
    err = LookupValidationError(Book._meta.get_field("title"), "x", "x")
    assert isinstance(err, ConfigurationError)
    assert isinstance(err, DjangoStrawberryFrameworkError)


def test_lookup_validation_error_labels_unnamed_terminal_by_type() -> None:
    """A terminal without a ``name`` falls back to its type name in the message."""
    err = LookupValidationError(object(), "x", "x")
    assert "object" in str(err)


# ---------------------------------------------------------------------------
# path_traverses_to_many: identical answers to the segment-walk oracle.
# ---------------------------------------------------------------------------


def _segment_walk_traverses_to_many(model: type[Model], field_path: str) -> bool:
    """The segment-by-segment walk, kept here as the compatibility oracle.

    Used ONLY to prove the ``classify_path``-based ``path_traverses_to_many``
    returns identical booleans across the hostile-path matrix below.
    """
    current: object = model
    for segment in field_path.split("__"):
        try:
            field = call_method(read_attr(current, "_meta"), "get_field", segment)
        except FieldDoesNotExist:
            return False
        if not getattr(field, "is_relation", False):
            return False
        if is_many_side_relation_kind(relation_kind(field)):
            return True
        related = read_attr(field, "related_model", None)
        if related is None:
            return False
        current = related
    return False


# Frozen expected answers: what the segment walk returns for each path.
_TRAVERSES_MATRIX = [
    # valid to-one / scalar -> False
    (Book, "title", False),
    (Book, "shelf__branch__name", False),
    (Book, "shelf__pk", False),
    (Patron, "card__barcode", False),
    (Decision, "supersedes__supersedes__question", False),
    (Book, "shelf__code", False),
    (Genre, "name", False),
    (Branch, "city", False),
    (Book, "shelf__branch", False),
    (Book, "shelf", False),
    (Patron, "card", False),
    # valid to-many -> True
    (Book, "loans__note", True),
    (Book, "genres__name", True),
    (Genre, "books__title", True),
    (Branch, "tags__tag", True),
    (Loan, "book__loans__patron__email", True),
    (Decision, "superseded_by_set__question", True),
    (Branch, "shelves__code", True),
    (Book, "genres", True),
    (Book, "loans", True),
    (Book, "shelf__branch__shelves__code", True),
    # unresolvable head -> False
    (Branch, "does_not_exist", False),
    (Book, "nonexistent__name", False),
    # garbage tail after scalar -> False
    (Book, "shelf__nope", False),
    (Book, "title__nonsense", False),
    # forward GenericForeignKey -> False (related_model is None)
    (TaggedItem, "content_object", False),
    (TaggedItem, "content_object__x", False),
    # many-then-garbage -> True (the segment walk short-circuits at the many hop)
    (Book, "genres__nonexistent", True),
    (Book, "loans__nonexistent__x", True),
    (Book, "genres__name__icontains", True),
    (Loan, "book__genres__nonsense", True),
]


@pytest.mark.parametrize(("model", "path", "expected"), _TRAVERSES_MATRIX)
def test_path_traverses_to_many_matches_the_segment_walk(
    model: type[Model],
    path: str,
    *,
    expected: bool,
) -> None:
    """``path_traverses_to_many`` returns the frozen segment-walk answer for every path."""
    assert path_traverses_to_many(model, path) is expected
    # And it agrees with the segment walk executed live in-process.
    assert path_traverses_to_many(model, path) is _segment_walk_traverses_to_many(model, path)


def test_path_traverses_to_many_many_then_garbage_uses_lenient_fallback() -> None:
    """A many-then-garbage path exercises the ``PathResolutionError`` fallback.

    ``classify_path`` raises on the garbage tail; the lenient fallback recovers
    the segment walk's ``True`` (the first hop is a forward M2M) instead of ``False``.
    """
    with pytest.raises(PathResolutionError):
        classify_path(Book, "genres__nonexistent")
    assert path_traverses_to_many(Book, "genres__nonexistent") is True


def test_lenient_fallback_all_to_one_relation_terminal_returns_false() -> None:
    """The lenient fallback's fully-walked-to-one exit returns ``False`` directly.

    ``path_traverses_to_many`` reaches the lenient loop's final ``return False``
    only in isolation: an all-to-one path ending on a relation
    (``shelf__branch``) is classified successfully by ``classify_path`` (so the
    public function never falls back), leaving this exit exercised by a direct
    call on the private helper.
    """
    assert _lenient_traverses_to_many(Book, "shelf__branch") is False


def test_path_traverses_to_many_is_cached() -> None:
    """Repeated checks reuse the bounded metadata cache."""
    relations_module._path_traverses_to_many_cache_clear()
    try:
        assert path_traverses_to_many(Branch, "shelves__code") is True
        assert path_traverses_to_many(Branch, "shelves__code") is True
        info = relations_module._path_traverses_to_many_cached.cache_info()
        assert info.misses == 1
        assert info.hits == 1
    finally:
        relations_module._path_traverses_to_many_cache_clear()


def test_classify_path_cached_wrapper_shares_bounded_cache() -> None:
    """``_classify_path_cached`` caches the frozen plan keyed on model + path."""
    _classify_path_cached.cache_clear()
    try:
        first = _classify_path_cached(Book, "genres__name")
        second = _classify_path_cached(Book, "genres__name")
        assert first is second
        info = _classify_path_cached.cache_info()
        assert info.misses == 1
        assert info.hits == 1
    finally:
        _classify_path_cached.cache_clear()


def test_classify_path_public_is_uncached_accepts_unhashable_model() -> None:
    """Public ``classify_path`` stays uncached so unhashable test doubles work.

    A ``SimpleNamespace`` model is unhashable (it defines ``__eq__``); the
    public entry point must not route through the ``lru_cache`` wrapper.
    """
    first = classify_path(Book, "title")
    second = classify_path(Book, "title")
    # Uncached: a fresh frozen plan each call (equal but distinct objects).
    assert first == second
    assert first is not second


def test_path_traverses_to_many_answers_an_unhashable_model_uncached() -> None:
    """The public probe bypasses its cache when the model key is unhashable."""
    scalar = SimpleNamespace(is_relation=False, name="title")

    def get_field(_segment: str) -> SimpleNamespace:
        return scalar

    unhashable_model = SimpleNamespace(_meta=SimpleNamespace(get_field=get_field))
    # basedpyright: the unhashable namespace standing in for a model is the input under test;
    # path_traverses_to_many types the parameter as type[Model]
    assert path_traverses_to_many(unhashable_model, "title") is False  # pyright: ignore[reportArgumentType]


def test_has_composite_pk_cardinality() -> None:
    """Composite-PK returns True only for a model whose pk is a ``CompositePrimaryKey``."""
    assert has_composite_pk(Book) is False

    assert has_composite_pk(RpCompositeParent) is True


def test_has_composite_pk_follows_a_rebound_pk(monkeypatch: pytest.MonkeyPatch) -> None:
    """A rebound ``_meta.pk`` is reported in its current shape, not the cached ``pk_fields``."""
    single_pk = Book._meta.pk
    assert len(Book._meta.pk_fields) == 1
    assert len(RpCompositeParent._meta.pk_fields) == 2

    monkeypatch.setattr(Book._meta, "pk", models.CompositePrimaryKey("title", "subtitle"))
    monkeypatch.setattr(RpCompositeParent._meta, "pk", single_pk)

    assert has_composite_pk(Book) is True
    assert has_composite_pk(RpCompositeParent) is False


@pytest.mark.parametrize(
    ("model", "name", "expected"),
    [
        pytest.param(Book, "id", True, id="auto-key"),
        pytest.param(Book, "title", False, id="plain-column"),
        pytest.param(PatronProfile, "patron", True, id="one-to-one-key"),
        pytest.param(PatronProfile, "address_2", False, id="one-to-one-owner-column"),
        pytest.param(LendingDesk, "id", True, id="inherited-parent-key"),
        pytest.param(LendingDesk, "venue_ptr", True, id="parent-link"),
        pytest.param(LendingDesk, "window_count", False, id="child-column"),
        pytest.param(SelfServeDesk, "venue_ptr", True, id="grandparent-link"),
        pytest.param(SelfServeDesk, "lendingdesk_ptr", True, id="grandchild-link"),
        pytest.param(SelfServeDesk, "kiosk_code", False, id="grandchild-column"),
        pytest.param(RpCompositeParent, "tenant_id", True, id="composite-member"),
        pytest.param(RpCompositeParent, "code", True, id="composite-second-member"),
        pytest.param(RpCompositeParent, "pk", True, id="composite-key-field"),
        pytest.param(RpCompositeParent, "label", False, id="composite-owner-column"),
    ],
)
def test_is_row_key_column_names_every_column_of_a_primary_key(
    model: type[Model],
    name: str,
    expected: bool,  # noqa: FBT001 - a parametrized expectation
) -> None:
    """A column is a row key when it is the key itself or a member of a ``CompositePrimaryKey``.

    A composite member carries ``primary_key=False``, so the flag alone cannot name it; the
    key a multi-table child inherits and its parent links are keys of their own tables.
    """
    column = model._meta.get_field(name)
    assert isinstance(column, models.Field)
    assert is_row_key_column(column) is expected


def test_relation_bool_none_value_falls_back_to_default() -> None:
    """A None-valued attribute in relation_bool adopts the provided default."""
    field_with_none = SimpleNamespace(flag=None)
    assert relation_bool(field_with_none, "flag", default=True) is True
    assert relation_bool(field_with_none, "flag", default=False) is False


def test_relation_metadata_rejects_non_boolean_and_non_string_slots() -> None:
    """Relation flags must be real bools and name slots real strings, not truthy stand-ins."""
    malformed_bool = SimpleNamespace(
        many_to_many=1,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        concrete=True,
    )
    malformed_name = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        concrete=True,
        content_type_field_name=123,
    )

    with pytest.raises(ConfigurationError, match="must be a bool"):
        relation_kind(malformed_bool)
    with pytest.raises(ConfigurationError, match="must be a string or None"):
        relation_kind(malformed_name)


def test_traversable_relation_probe_handles_a_false_flag() -> None:
    """A field whose relation flag is false is untraversable."""
    assert _is_traversable_relation(SimpleNamespace(is_relation=False)) is False


def test_classify_path_wraps_malformed_relation_flags_and_taxonomy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A malformed segment flag is a path error; a malformed kind flag is a metadata error."""
    malformed_flag = SimpleNamespace(is_relation=1)
    with pytest.raises(PathResolutionError):
        classify_path(_serving_field(monkeypatch, lambda _name: malformed_flag), "relation")

    path_info = SimpleNamespace(m2m=False, to_opts=SimpleNamespace(model=Book))
    malformed_kind = SimpleNamespace(
        is_relation=True,
        path_infos=[path_info],
        many_to_many=1,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        concrete=True,
    )
    with pytest.raises(ConfigurationError, match="must be a bool"):
        classify_path(_serving_field(monkeypatch, lambda _name: malformed_kind), "relation")


def test_lookup_validation_rejects_a_non_string_expression() -> None:
    """A non-string ``lookup_expr`` is a typed lookup error, rendered truthfully."""
    with pytest.raises(LookupValidationError) as excinfo:
        # basedpyright: the non-str lookup expression is the input under test;
        # validate_lookup_expr types the parameter as str
        validate_lookup_expr(Book._meta.get_field("title"), 123)  # pyright: ignore[reportArgumentType]
    assert str(excinfo.value) == (
        "Invalid lookup expression 123 for terminal title: part 123 is not a valid "
        "transform or lookup."
    )


def test_many_path_probe_rejects_a_non_string_path() -> None:
    """A non-string path is not many-side rather than an error out of the probe."""
    # basedpyright: the non-str path is the hostile input under test; path_traverses_to_many types
    # the parameter as str
    assert path_traverses_to_many(Book, 123) is False  # pyright: ignore[reportArgumentType]


def test_instance_accessor_rejects_malformed_accessor_metadata() -> None:
    """Each accessor tier requires the declared shape: string slot, callable hook, string result."""
    with pytest.raises(ConfigurationError, match="must be a string"):
        instance_accessor(SimpleNamespace(accessor_name=123))
    with pytest.raises(ConfigurationError, match="must be callable"):
        instance_accessor(SimpleNamespace(get_accessor_name=123, name="relation"))
    with pytest.raises(ConfigurationError, match="must be a string"):
        instance_accessor(SimpleNamespace(get_accessor_name=lambda: 123, name="relation"))


def test_is_forward_concrete_relation() -> None:
    """is_forward_concrete_relation correctly identifies forward concrete relations."""
    # Forward ForeignKey
    assert is_forward_concrete_relation(Book._meta.get_field("shelf")) is True
    # Forward OneToOne
    assert is_forward_concrete_relation(MembershipCard._meta.get_field("patron")) is True
    # Reverse OneToOneRel -> False
    assert is_forward_concrete_relation(Patron._meta.get_field("card")) is False
    # Forward ManyToManyField -> False (kind is "many", not "forward_single")
    assert is_forward_concrete_relation(Book._meta.get_field("genres")) is False
    # Reverse ForeignObjectRel (reverse FK) -> False
    assert is_forward_concrete_relation(Branch._meta.get_field("shelves")) is False
    # GenericForeignKey -> False
    assert is_forward_concrete_relation(TaggedItem._meta.get_field("content_object")) is False
    # GenericRelation -> False
    assert is_forward_concrete_relation(Branch._meta.get_field("tags")) is False
    # Scalar field -> False
    assert is_forward_concrete_relation(Book._meta.get_field("title")) is False
    # Non-field -> False
    # basedpyright: deliberately not a field; the test proves the predicate answers False
    assert is_forward_concrete_relation(None) is False  # pyright: ignore[reportCallIssue, reportArgumentType]
    assert is_forward_concrete_relation(object()) is False  # pyright: ignore[reportCallIssue, reportArgumentType]


def test_is_forward_concrete_relation_reads_cardinality_not_the_column_flag() -> None:
    """A forward M2M is rejected on its KIND, never on a Django-version-specific ``column``.

    Django moves both ``column`` and ``concrete`` for ``ManyToManyField`` inside
    the supported range: the 5.2 support floor reports ``column="genres"`` /
    ``concrete=True``, while 6.0+ reports ``column=None`` / ``concrete=False``.
    A real ``Book.genres`` therefore only exercises whichever shape the matrix
    cell installed, so the assertion above passes on 6.x for the wrong reason
    and the 5.2 cell is the only thing that catches a ``column``-based test.
    These doubles pin BOTH shapes on EVERY cell, so the predicate cannot regress
    to a version-dependent signal without failing everywhere at once.
    """
    m2m_on_django_52 = _RelationDouble(
        is_relation=True,
        many_to_many=True,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        concrete=True,
        column="genres",
        related_model=Genre,
    )
    m2m_on_django_60 = _RelationDouble(
        is_relation=True,
        many_to_many=True,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        concrete=False,
        column=None,
        related_model=Genre,
    )
    forward_fk = _RelationDouble(
        is_relation=True,
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
        concrete=True,
        column="shelf_id",
        related_model=Branch,
    )

    assert is_forward_concrete_relation(m2m_on_django_52) is False
    assert is_forward_concrete_relation(m2m_on_django_60) is False
    assert is_forward_concrete_relation(forward_fk) is True


def test_path_traverses_to_many_cache_clear_reaches_the_classification_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The probe's cache clear invalidates the classifier cache beneath the answer cache.

    The probe's answer is computed from ``_classify_path_cached``; a clear that
    emptied only the outer answer cache would serve the stale frozen
    classification after a metadata change under the same ``(model, path)``
    key, even though the clear had been called.
    """
    _classify_path_cached.cache_clear()
    relations_module._path_traverses_to_many_cache_clear()
    try:

        class _MutableOpts:
            fields = {"flag": SimpleNamespace(name="flag", is_relation=False)}

            def get_field(self, name: str) -> SimpleNamespace:
                try:
                    return self.fields[name]
                except KeyError:
                    raise FieldDoesNotExist(name) from None

        model = _serving_field(monkeypatch, _MutableOpts().get_field)
        assert path_traverses_to_many(model, "flag") is False

        _MutableOpts.fields = {
            "flag": SimpleNamespace(
                name="flag",
                is_relation=True,
                many_to_many=True,
                one_to_many=False,
                one_to_one=False,
                auto_created=False,
                concrete=True,
                content_type_field_name=None,
                object_id_field_name=None,
                path_infos=(SimpleNamespace(m2m=True, to_opts=SimpleNamespace(model=Genre)),),
            ),
        }
        relations_module._path_traverses_to_many_cache_clear()

        # The clear reaches beneath the answer cache: a classifier cache left
        # warm would answer the stale frozen classification here.
        assert path_traverses_to_many(model, "flag") is True
    finally:
        _classify_path_cached.cache_clear()
        relations_module._path_traverses_to_many_cache_clear()


@pytest.mark.parametrize(
    (
        "owner",
        "field_name",
        "carriers",
        "targets",
    ),
    [
        (
            "LnkPairChild",
            "parent",
            ("p_tenant", "p_code"),
            ("tenant", "code"),
        ),
        (
            "LnkParent",
            "pair_children",
            ("p_tenant", "p_code"),
            ("tenant", "code"),
        ),
        (
            "LnkParent",
            "column_children",
            ("p_id",),
            ("id",),
        ),
        (
            "LnkParent",
            "slug_children",
            ("parent_id",),
            ("slug",),
        ),
        (
            "Book",
            "shelf",
            ("shelf_id",),
            ("id",),
        ),
        (
            "Patron",
            "card",
            ("patron_id",),
            ("id",),
        ),
        (
            "Branch",
            "tags",
            ("object_id",),
            ("id",),
        ),
        (
            "Book",
            "genres",
            ("book_id",),
            ("id",),
        ),
        (
            "Genre",
            "books",
            ("genre_id",),
            ("id",),
        ),
        (
            "LnkParent",
            "tags",
            ("parent_id",),
            ("slug",),
        ),
        (
            "LnkTag",
            "parents",
            ("tag_id",),
            ("code",),
        ),
        (
            "TaggedItem",
            "content_object",
            (),
            (),
        ),
        (
            "Book",
            "title",
            (),
            (),
        ),
    ],
    ids=[
        "forward_two_column_fo",
        "reverse_two_column_fo",
        "reverse_one_column_fo",
        "reverse_to_field_fk",
        "forward_fk",
        "reverse_o2o",
        "generic_relation",
        "forward_m2m",
        "reverse_m2m",
        "forward_to_field_through_m2m",
        "reverse_to_field_through_m2m",
        "generic_foreign_key",
        "non_relation",
    ],
)
def test_relation_link_reads_the_link_column_pairs(
    owner: str,
    field_name: str,
    carriers: tuple[str, ...],
    targets: tuple[str, ...],
) -> None:
    """``relation_link`` answers a link's carrier / target columns from either side.

    A forward link answers from itself, a reverse descriptor from its forward
    ``.field``, and an M2M hop in either direction from its through table's FK
    onto the source model; a ``GenericForeignKey`` and a non-relation carry no
    pairs.
    """
    model = {
        "LnkPairChild": LnkPairChild,
        "LnkParent": LnkParent,
        "LnkTag": LnkTag,
        "Book": Book,
        "Patron": Patron,
        "Branch": Branch,
        "Genre": Genre,
        "TaggedItem": TaggedItem,
    }[owner]
    link = relation_link(model._meta.get_field(field_name))
    assert link.carrier_attnames == carriers
    assert link.target_attnames == targets


@pytest.mark.parametrize(
    "double",
    [
        SimpleNamespace(local_related_fields="p_id", foreign_related_fields=()),
        SimpleNamespace(
            local_related_fields=(SimpleNamespace(attname=1),),
            foreign_related_fields=(SimpleNamespace(attname="id"),),
        ),
        SimpleNamespace(
            local_related_fields=(SimpleNamespace(attname="a"), SimpleNamespace(attname="b")),
            foreign_related_fields=(SimpleNamespace(attname="id"),),
        ),
        SimpleNamespace(local_related_fields=(), foreign_related_fields=()),
        SimpleNamespace(field=SimpleNamespace(local_related_fields=None)),
        SimpleNamespace(field=None),
    ],
    ids=[
        "carriers_not_a_sequence",
        "carrier_attname_not_a_string",
        "unequal_sides",
        "empty_sides",
        "reverse_link_without_pairs",
        "no_link",
    ],
)
def test_relation_link_answers_empty_for_malformed_links(double: SimpleNamespace) -> None:
    """A link shape the reader cannot pair column-for-column answers no pairs."""
    link = relation_link(double)
    assert link.carriers == ()
    assert link.targets == ()


@pytest.mark.parametrize(
    ("owner", "field_name", "expected"),
    [
        ("Book", "shelf", True),
        ("MembershipCard", "patron", True),
        ("LnkSlugChild", "parent", True),
        ("LnkColumnChild", "parent", False),
        ("LnkPairChild", "parent", False),
        ("Patron", "card", False),
        ("Book", "genres", False),
        ("Branch", "tags", False),
        ("TaggedItem", "content_object", False),
    ],
    ids=[
        "fk",
        "o2o",
        "to_field_fk",
        "one_column_fo",
        "two_column_fo",
        "reverse_o2o",
        "m2m",
        "generic_relation",
        "generic_foreign_key",
    ],
)
def test_is_single_column_foreign_key(owner: str, field_name: str, *, expected: bool) -> None:
    """Only a forward ``ForeignKey`` / ``OneToOneField`` is a one-column link."""
    model = {
        "Book": Book,
        "MembershipCard": MembershipCard,
        "LnkSlugChild": LnkSlugChild,
        "LnkColumnChild": LnkColumnChild,
        "LnkPairChild": LnkPairChild,
        "Patron": Patron,
        "Branch": Branch,
        "TaggedItem": TaggedItem,
    }[owner]
    assert is_single_column_foreign_key(model._meta.get_field(field_name)) is expected


def _reverse_generic_relation() -> object:
    """Return the reverse ``GenericRel`` a ``GenericRelation`` adds to its generic-key model.

    A ``related_query_name`` makes the reverse descriptor visible in the
    generic-key model's ``_meta.get_fields()``; its link pairs read the
    ``object_id`` column against the holder's primary key.
    """
    meta = type("Meta", (), {"app_label": "products", "managed": False})
    tag = type(
        "CarrierProbeTag",
        (models.Model,),
        {
            "__module__": __name__,
            "content_type": models.ForeignKey(
                ContentType,
                on_delete=models.CASCADE,
                related_name="+",
            ),
            "object_id": models.PositiveIntegerField(),
            "content_object": GenericForeignKey("content_type", "object_id"),
            "Meta": meta,
        },
    )
    type(
        "CarrierProbeHolder",
        (models.Model,),
        {
            "__module__": __name__,
            "tags": GenericRelation(tag, related_query_name="holder"),
            "Meta": meta,
        },
    )
    return tag._meta.get_field("holder")


@pytest.mark.parametrize(
    ("field", "carriers"),
    [
        (lambda: LnkPairChild._meta.get_field("parent"), ("p_tenant", "p_code")),
        (lambda: LnkColumnChild._meta.get_field("parent"), ("p_id",)),
        (lambda: LnkSlugChild._meta.get_field("parent"), None),
        (lambda: LnkParent._meta.get_field("pair_children"), None),
        (lambda: Branch._meta.get_field("tags"), None),
        (_reverse_generic_relation, None),
        (lambda: TaggedItem._meta.get_field("content_object"), None),
        (lambda: Book._meta.get_field("genres"), None),
        (lambda: Book._meta.get_field("title"), None),
    ],
    ids=[
        "two_column_fo",
        "one_column_fo",
        "to_field_fk",
        "reverse_fo",
        "generic_relation",
        "reverse_generic_relation",
        "generic_foreign_key",
        "m2m",
        "non_relation",
    ],
)
def test_carrier_backed_link_answers_only_a_forward_foreign_object(
    field: Callable[[], object],
    carriers: tuple[str, ...] | None,
) -> None:
    """Only a forward ``ForeignObject`` that is not a ``ForeignKey`` is carrier-backed.

    Its link is its carrier / target pairs. A ``ForeignKey`` has a column of its
    own, and a reverse descriptor (the reverse ``GenericRel`` included, although
    ``relation_link`` reads ``object_id`` pairs off it) belongs to the field on
    the other model.
    """
    link = carrier_backed_link(field())
    assert (None if link is None else link.carrier_attnames) == carriers


@pytest.mark.parametrize(
    ("field", "carriers"),
    [
        (lambda: LnkPairChild._meta.get_field("parent"), ("p_tenant", "p_code")),
        (lambda: LnkSlugObjectChild._meta.get_field("parent"), ("p_slug",)),
        (lambda: LnkSlugChild._meta.get_field("parent"), ("parent_id",)),
        (lambda: LnkColumnChild._meta.get_field("parent"), None),
        (lambda: Book._meta.get_field("shelf"), None),
        (lambda: MembershipCard._meta.get_field("patron"), None),
        (lambda: LnkParent._meta.get_field("pair_children"), None),
        (lambda: TaggedItem._meta.get_field("content_object"), None),
        (lambda: Book._meta.get_field("genres"), None),
        (lambda: Book._meta.get_field("title"), None),
    ],
    ids=[
        "two_column_fo",
        "one_column_fo_non_pk",
        "to_field_fk",
        "one_column_fo_pk",
        "fk",
        "o2o",
        "reverse_fo",
        "generic_foreign_key",
        "m2m",
        "non_relation",
    ],
)
def test_non_pk_forward_link_answers_only_links_keyed_by_other_columns(
    field: Callable[[], object],
    carriers: tuple[str, ...] | None,
) -> None:
    """Only a forward single-valued link whose targets are not the related pk answers its pairs.

    Django trims ``<relation>__pk`` to the carrier column of a link onto the
    related pk, so only the others need a correlation of their own.
    """
    link = non_pk_forward_link(field())
    assert (None if link is None else link.carrier_attnames) == carriers


def test_non_pk_forward_link_refuses_an_unresolved_related_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A forward link names a resolved model; an unresolved ``"app.Model"`` string is a ``TypeError``."""
    field = LnkSlugChild._meta.get_field("parent")
    monkeypatch.setitem(vars(field), "related_model", "optimizer.LnkSlugParent")
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        non_pk_forward_link(field)


def test_m2m_through_model_refuses_an_unresolved_through() -> None:
    """A join table is a model class once resolved; an ``"app.Model"`` string is a ``TypeError``."""
    assert m2m_through_model(SimpleNamespace(through=None, remote_field=None)) is None
    assert m2m_through_model(Book._meta.get_field("genres")) is not None
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        m2m_through_model(SimpleNamespace(through="library.BookGenres"))


@pytest.mark.parametrize(
    ("field", "key"),
    [
        (lambda: LnkSlugChild._meta.get_field("parent"), "slug"),
        (lambda: LnkParent._meta.get_field("tags"), "code"),
        (lambda: Book._meta.get_field("shelf"), None),
        (lambda: MembershipCard._meta.get_field("patron"), None),
        (lambda: Book._meta.get_field("genres"), None),
        (lambda: LnkParent._meta.get_field("slug_children"), None),
        (lambda: Book._meta.get_field("title"), None),
    ],
    ids=[
        "to_field_fk",
        "to_field_through_m2m",
        "fk",
        "o2o",
        "m2m",
        "reverse_fk",
        "non_relation",
    ],
)
def test_non_pk_relation_key_attname_names_the_stored_column_only_when_not_the_pk(
    field: Callable[[], object],
    key: str | None,
) -> None:
    """A write through a relation stores the column its link references; only a non-pk one is named.

    The ``to_field`` FK stores the parent's ``slug``; the ``LnkParent.tags`` through row
    stores the tag's ``code`` (its target-side key's ``to_field``); a pk-keyed FK,
    OneToOne and auto-through M2M store the pk, and a reverse relation or a column
    writes no key.
    """
    assert non_pk_relation_key_attname(field()) == key


@pytest.mark.parametrize(
    ("model", "field_path", "expected"),
    [
        (LnkPairChild, "parent", ("p_tenant", "p_code")),
        (LnkColumnChild, "parent", ("p_id",)),
        (LnkParent, "pair_children__parent", ("pair_children__p_tenant", "pair_children__p_code")),
        (LnkSlugChild, "parent", ("parent",)),
        (LnkPairChild, "parent__label", ("parent__label",)),
        (LnkPairChild, "pk", ("pk",)),
        (Book, "shelf__branch", ("shelf__branch",)),
    ],
    ids=[
        "two_column_fo",
        "one_column_fo",
        "fo_behind_a_relation",
        "to_field_fk",
        "column_past_a_fo",
        "pk",
        "fk_chain",
    ],
)
def test_order_column_paths_expands_only_a_terminal_foreign_object(
    model: type[Model],
    field_path: str,
    expected: tuple[str, ...],
) -> None:
    """A path ending on a carrier-backed link orders by its carriers; any other path is itself.

    The carriers keep the relations the path crosses before the link, in link
    order.
    """
    terminal = classify_path(model, field_path).terminal
    assert order_column_paths(field_path, terminal) == expected


@pytest.mark.parametrize(
    "double",
    [
        SimpleNamespace(many_to_many=True, through=None, remote_field=None),
        SimpleNamespace(many_to_many=True, is_relation=True, through=Book),
    ],
    ids=["no_through_model", "no_path_infos"],
)
def test_m2m_through_link_answers_empty_without_a_through_link(double: SimpleNamespace) -> None:
    """An M2M hop whose through FKs do not resolve has no link pairs."""
    assert relation_link(double).carriers == ()
    assert m2m_through_link_fields(double) == (None, None)


@pytest.mark.parametrize(
    ("lookup_expr", "lookup_class"),
    [
        ("lower", Exact),
        ("lower__exact", Exact),
        ("lower__icontains", IContains),
        ("lower__lower__exact", Exact),
    ],
    ids=[
        "trailing-transform-implies-exact",
        "exact",
        "icontains",
        "chained-transforms",
    ],
)
def test_validate_lookup_expr_output_less_transform_resolves_through_the_column(
    lookup_expr: str,
    lookup_class: type[Lookup[object]],
) -> None:
    """A transform declaring no output field resolves its lookup as Django's ORM does.

    ``Lower`` takes its output field from the expression it wraps; the walk
    wraps the terminal's column, so ``Lower`` outputs a ``TextField`` and the
    next part resolves against it, exactly as ``title__<lookup_expr>`` compiles.
    """
    terminal = Book._meta.get_field("title")
    with register_lookup(TextField, Lower):
        resolved = validate_lookup_expr(terminal, lookup_expr)
    assert resolved is lookup_class


@pytest.mark.parametrize(
    ("lookup_expr", "part"),
    [("lower__bogus", "bogus"), ("lower__bogus__exact", "bogus")],
    ids=["final-part", "mid-chain-part"],
)
def test_validate_lookup_expr_unknown_part_after_output_less_transform_raises(
    lookup_expr: str,
    part: str,
) -> None:
    """A name the transform's resolved output field does not know is a typed rejection."""
    terminal = Book._meta.get_field("title")
    with register_lookup(TextField, Lower), pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, lookup_expr)
    assert excinfo.value.part == part
    assert excinfo.value.lookup_expr == lookup_expr


@pytest.mark.parametrize(
    ("lookup_expr", "lookup_class"),
    [("a__b", KeyTransformExact), ("a__b__icontains", KeyTransformIContains)],
    ids=["trailing-key-implies-exact", "icontains"],
)
def test_validate_lookup_expr_nested_json_keys_resolve_key_transform_lookups(
    lookup_expr: str,
    lookup_class: type[Lookup[object]],
) -> None:
    """Nested ``JSONField`` keys validate to the key-transform lookup Django compiles.

    Each key is a ``KeyTransform`` whose output field is the ``JSONField`` its
    column carries, so the next key and the final lookup resolve against it.
    """
    terminal = ScalarSpecimen._meta.get_field("payload")
    assert validate_lookup_expr(terminal, lookup_expr) is lookup_class


@pytest.mark.parametrize(
    ("lookup_expr", "lookup_class"),
    [("exact", RelatedExact), ("isnull", RelatedIsNull)],
    ids=["exact", "isnull"],
)
def test_validate_lookup_expr_forward_fk_column_answers_related_lookups(
    lookup_expr: str,
    lookup_class: type[Lookup[object]],
) -> None:
    """A forward FK's column keeps the FK as its output field, so lookups stay relational.

    The column's output field is the terminal itself, never the target primary
    key, matching the column Django's ORM filters a relation through.
    """
    terminal = Book._meta.get_field("shelf")
    assert validate_lookup_expr(terminal, lookup_expr) is lookup_class


@pytest.mark.parametrize(
    ("field", "column"),
    [
        (lambda: Book._meta.pk, lambda: Book._meta.pk),
        (lambda: PatronProfile._meta.pk, lambda: Patron._meta.pk),
        (lambda: LendingDesk._meta.pk, lambda: Venue._meta.pk),
        (lambda: SelfServeDesk._meta.pk, lambda: Venue._meta.pk),
        (
            lambda: PatronProfile._meta.get_field("favorite_genre"),
            lambda: Genre._meta.get_field("name"),
        ),
        (lambda: Patron._meta.get_field("profile"), lambda: Patron._meta.get_field("profile")),
        (lambda: RpCompositeParent._meta.pk, lambda: RpCompositeParent._meta.pk),
    ],
    ids=[
        "plain_pk",
        "one_to_one_pk",
        "parent_link",
        "grandchild_parent_link_chain",
        "to_field_column",
        "reverse_relation",
        "composite_pk",
    ],
)
def test_stored_value_column_follows_each_key_to_the_column_storing_its_value(
    field: "Callable[[], ModelField]",
    column: Callable[[], object],
) -> None:
    """A key resolves to the first non-key column down its chain; anything else is itself."""
    assert stored_value_column(field()) is column()
