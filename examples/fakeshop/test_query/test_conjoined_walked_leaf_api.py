"""A walked ``conjoined`` multiple-choice leaf keeps a parent reaching a visible row for each value.

django-filter's ``MultipleChoiceFilter`` / ``ModelMultipleChoiceFilter`` with
``conjoined=True`` chains one ``filter()`` call per value, so Django gives each value a
join of its own across a to-many relation: a parent is kept when SOME related row
matches EACH value, two values possibly met by different related rows. A flat leaf the
package walks (a ``RelatedFilter`` on its first hop, or a target type whose
``get_queryset`` hides rows) answers the same rows over the visible related rows, on a
reverse foreign key, a many-to-many, a two-hop to-many path, a target column, a forward
key past a to-many hop and a path continuing past the walked hop; a hidden related row
meets no value. ``exclude=True`` answers as django-filter's, which excludes each value in
turn: the parents no visible related row of ANY value reaches. A consumer ``filter``
override on a to-many key whose raw key or GlobalID value names rows of the target keeps
a parent reaching a visible row each value names. A required filter whose
``always_filter`` is off asks ``is_noop`` once, of the whole value. A flat copy of a
child set's conjoined leaf answers Django's path over the parent's relation, so it keeps
a parent whose values two child rows meet, where the nested branch needs one child row
meeting them all; a nested branch whose child leaf walks a to-many hop answers per
child row as unwalked. Each request runs over ``/graphql`` against a connection whose
type serves the set, with the number of statements it runs.
"""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django import forms
from django.db import connection
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import Filter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, graphql_payload, json_at, json_list, json_object
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import (
    FilterSet,
    GlobalIDMultipleChoiceFilter,
    RelatedFilter,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-conjoined-walked/", _graphql_view)]

#: The label column each model's rows answer by.
_LABELS: dict[type[Model], str] = {
    models.Branch: "name",
    models.Shelf: "code",
    models.Genre: "name",
    models.Book: "title",
}

#: The rows a hooked target type hides.
_HIDDEN: dict[type[Model], Callable[[QuerySet[Model]], QuerySet[Model]]] = {
    models.Shelf: lambda rows: rows.exclude(topic="secret"),
    models.Genre: lambda rows: rows.exclude(name="gs"),
    models.Book: lambda rows: rows.exclude(title="xh"),
}


def _world() -> None:
    """Branches, their shelves, the shelves' books and the books' genres.

    ``alpha`` holds ``a1``, ``a2`` and the secret ``ah``; ``beta`` holds ``b1``; ``delta`` only
    the secret ``dh``; ``gamma`` none. Books ``x1`` / ``x4`` sit on ``a1``, ``x2`` on ``a2``,
    ``x3`` on ``b1``, ``xh`` on ``ah`` and ``x0`` on ``dh``; ``x3`` holds ``g1`` and ``g2``,
    ``xh`` holds ``g1`` and ``gs``.
    """
    branches = {name: models.Branch.objects.create(name=name) for name in ("alpha", "beta")}
    branches |= {name: models.Branch.objects.create(name=name) for name in ("delta", "gamma")}
    shelves = {
        code: models.Shelf.objects.create(branch=branches[branch], code=code, topic=topic)
        for code, branch, topic in (
            ("a1", "alpha", "open"),
            ("a2", "alpha", "open"),
            ("ah", "alpha", "secret"),
            ("b1", "beta", "open"),
            ("dh", "delta", "secret"),
        )
    }
    genres = {name: models.Genre.objects.create(name=name) for name in ("g1", "g2", "gs")}
    for title, shelf, held in (
        ("x1", "a1", ("g1",)),
        ("x2", "a2", ("g2",)),
        ("x3", "b1", ("g1", "g2")),
        ("x4", "a1", ("g2",)),
        ("xh", "ah", ("g1", "gs")),
        ("x0", "dh", ()),
    ):
        book = models.Book.objects.create(title=title, shelf=shelves[shelf])
        book.genres.add(*(genres[name] for name in held))


def _pk(model: type[Model], label: str) -> str:
    return str(read_attr(model._default_manager.get(**{_LABELS[model]: label}), "pk"))


@dataclass(frozen=True)
class _Answer:
    """The rows a value keeps, as django-filter answers it over every row and over visible ones."""

    labels: tuple[str, ...]
    every: tuple[str, ...]
    visible: tuple[str, ...] | None = None


@dataclass(frozen=True)
class _Shape:
    """A conjoined leaf's path, the models it reaches and the rows each value set keeps."""

    parent: type[Model]
    leaf: str
    target: type[Model]
    key: bool
    first: str
    first_target: type[Model]
    hidden: type[Model]
    answers: dict[str, _Answer]

    def value(self, labels: Sequence[str]) -> list[str]:
        """The choice naming ``labels``: target keys for a relation key, else the labels."""
        return [_pk(self.target, label) for label in labels] if self.key else list(labels)

    def wire(self, kind: str, labels: Sequence[str]) -> list[str] | list[int]:
        """The value sent for ``labels``: a model-choice key list types ``Int``."""
        values = self.value(labels)
        return [int(value) for value in values] if kind == "model" and self.key else values


def _branch_answers(*values: tuple[str, ...]) -> dict[str, _Answer]:
    one, same, split, hidden, out = values
    return {
        "one": _Answer(one, ("alpha",)),
        "two-rows-one-parent": _Answer(same, ("alpha",)),
        "two-parents": _Answer(split, ()),
        "hidden-member": _Answer(hidden, ("alpha",), ()),
        "excluded": _Answer(out, ("beta", "delta", "gamma")),
        "excluded-two-parents": _Answer(split, ("delta", "gamma")),
        "unconjoined-two-parents": _Answer(split, ("alpha", "beta")),
    }


_SHELF_VALUES = (
    ("a1",),
    ("a1", "a2"),
    ("a1", "b1"),
    ("a1", "ah"),
    ("a1", "a2"),
)
_BOOK_VALUES = (
    ("x1",),
    ("x1", "x2"),
    ("x1", "x3"),
    ("x1", "xh"),
    ("x1", "x2"),
)
_GENRE_ANSWERS = {
    "one": _Answer(("g1",), ("x1", "x3", "xh")),
    "two-rows-one-parent": _Answer(("g1", "g2"), ("x3",)),
    "two-parents": _Answer(("g2", "gs"), ()),
    "hidden-member": _Answer(("g1", "gs"), ("xh",), ()),
    "excluded": _Answer(("g1", "g2"), ("x0",)),
    "excluded-two-parents": _Answer(("g2", "gs"), ("x0", "x1"), ("x0", "x1", "xh")),
    "unconjoined-two-parents": _Answer(
        ("g2", "gs"),
        (
            "x2",
            "x3",
            "x4",
            "xh",
        ),
        ("x2", "x3", "x4"),
    ),
}
_SHELF_KEY_PAST_BOOKS = {
    "one": _Answer(("a1",), ("g1", "g2")),
    "two-rows-one-parent": _Answer(("a1", "b1"), ("g1", "g2")),
    "two-parents": _Answer(("a2", "ah"), ()),
    "hidden-member": _Answer(("a1", "ah"), ("g1",), ()),
    "excluded": _Answer(("a1", "b1"), ("gs",)),
    "excluded-two-parents": _Answer(("a2", "ah"), (), ("g1", "gs")),
    "unconjoined-two-parents": _Answer(("a2", "ah"), ("g1", "g2", "gs"), ("g2",)),
}

_SHAPES: dict[str, _Shape] = {
    "reverse-key": _Shape(
        parent=models.Branch,
        leaf="shelves",
        target=models.Shelf,
        key=True,
        first="shelves",
        first_target=models.Shelf,
        hidden=models.Shelf,
        answers=_branch_answers(*_SHELF_VALUES),
    ),
    "reverse-column": _Shape(
        parent=models.Branch,
        leaf="shelves__code",
        target=models.Shelf,
        key=False,
        first="shelves",
        first_target=models.Shelf,
        hidden=models.Shelf,
        answers=_branch_answers(*_SHELF_VALUES),
    ),
    "many-to-many-key": _Shape(
        parent=models.Book,
        leaf="genres",
        target=models.Genre,
        key=True,
        first="genres",
        first_target=models.Genre,
        hidden=models.Genre,
        answers=_GENRE_ANSWERS,
    ),
    "many-to-many-column": _Shape(
        parent=models.Book,
        leaf="genres__name",
        target=models.Genre,
        key=False,
        first="genres",
        first_target=models.Genre,
        hidden=models.Genre,
        answers=_GENRE_ANSWERS,
    ),
    "two-hop-key": _Shape(
        parent=models.Branch,
        leaf="shelves__books",
        target=models.Book,
        key=True,
        first="shelves",
        first_target=models.Shelf,
        hidden=models.Book,
        answers=_branch_answers(*_BOOK_VALUES),
    ),
    "two-hop-column": _Shape(
        parent=models.Branch,
        leaf="shelves__books__title",
        target=models.Book,
        key=False,
        first="shelves",
        first_target=models.Shelf,
        hidden=models.Book,
        answers=_branch_answers(*_BOOK_VALUES),
    ),
    "forward-key-past-to-many": _Shape(
        parent=models.Genre,
        leaf="books__shelf",
        target=models.Shelf,
        key=True,
        first="books",
        first_target=models.Book,
        hidden=models.Shelf,
        answers=_SHELF_KEY_PAST_BOOKS,
    ),
    "unwalked-tail": _Shape(
        parent=models.Branch,
        leaf="shelves__books__title",
        target=models.Book,
        key=False,
        first="shelves",
        first_target=models.Shelf,
        hidden=models.Shelf,
        answers=_branch_answers(*_BOOK_VALUES),
    ),
}


def _declare(
    shape: _Shape,
    kind: str,
    *,
    conjoined: bool = True,
    exclude: bool = False,
    required: bool = False,
) -> MultipleChoiceFilter:
    """A shipped filter of ``kind`` over ``shape``'s leaf, ``conjoined`` unless told otherwise."""
    target_rows = shape.target._default_manager.all()
    label = _LABELS[shape.target]
    if kind == "model":
        return ModelMultipleChoiceFilter(
            field_name=shape.leaf,
            queryset=target_rows,
            # A target column compares the chosen rows' own values of it.
            to_field_name=None if shape.key else label,
            conjoined=conjoined,
            exclude=exclude,
            required=required,
        )
    labels = [str(read_attr(row, label)) for row in target_rows]
    choices = [(value, value) for value in shape.value(labels)]
    return MultipleChoiceFilter(
        field_name=shape.leaf,
        choices=choices,
        conjoined=conjoined,
        exclude=exclude,
        required=required,
    )


def _node(model: type[Model], *, hiding: bool = False, **meta: object) -> type[DjangoType]:
    namespace: dict[str, object] = {}
    if hiding:
        scope = _HIDDEN[model]

        def get_queryset(
            _cls: type[DjangoType],
            queryset: QuerySet[Model],
            _info: object,
        ) -> QuerySet[Model]:
            return scope(queryset)

        namespace["get_queryset"] = classmethod(get_queryset)
    return make_django_type(
        f"Conjoined{model.__name__}",
        model,
        ("id", _LABELS[model]),
        meta_extra=meta,
        namespace_extra=namespace,
    )


def _schema(
    parent: type[Model],
    filters: dict[str, object],
    nodes: dict[type[Model], bool],
    *,
    typed: bool = True,
) -> tuple[DjangoSchema, dict[type[Model], type[DjangoType]]]:
    """A field over ``parent``'s rows filtered by a set declaring ``filters``.

    ``typed``, a connection whose type serves the set, its input generated; otherwise a
    resolver of the consumer's applying the set to a ``JSON`` value with ``apply_sync``,
    which reaches a filter no generated input types (a ``MultipleChoiceFilter`` on a
    relation key). ``nodes`` names each other model a type is registered for, ``True`` when
    its ``get_queryset`` hides rows.
    """
    filterset = type(
        "ConjoinedProbe",
        (FilterSet,),
        {**filters, "Meta": type("Meta", (), {"model": parent, "fields": []})},
    )
    root = _node(parent, filterset_class=filterset) if typed else _node(parent)
    types = {model: _node(model, hiding=hiding) for model, hiding in nodes.items()}

    def resolve_rows(_root: object, _info: strawberry.Info[object, object]) -> QuerySet[Model]:
        return parent._default_manager.order_by(_LABELS[parent])

    def resolve_applied(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[Model]:
        return filterset.apply_sync(where, resolve_rows(root, info), info)

    @strawberry.type
    class ServedQuery:
        rows = DjangoConnectionField(root, resolver=resolve_rows)

    @strawberry.type
    class AppliedQuery:
        rows: QuerySet[Model] = strawberry.field(
            resolver=resolve_applied,
            graphql_type=list[root],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=ServedQuery if typed else AppliedQuery,
        types=tuple(types.values()),
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    return schema, types


def _input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(schema: DjangoSchema, python_path: Sequence[str], value: object) -> JSONObject:
    """``value`` under the published names of ``python_path``, read from the executing schema."""
    current = _input(schema)
    names: list[str] = []
    for index, name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == name)
        wire = schema.config.name_converter.from_field(field)
        names.append(wire)
        if index < len(python_path) - 1:
            child = get_named_type(graphql_type_of(graphql_input_fields(current)[wire]))
            assert isinstance(child, GraphQLInputObjectType)
            current = child
    result: JSONObject = {names[-1]: value}
    for wire in reversed(names[:-1]):
        result = {wire: result}
    return result


def _post(
    schema: DjangoSchema,
    parent: type[Model],
    where: JSONObject,
    *,
    typed: bool = True,
) -> tuple[list[str], int]:
    """The sorted labels of the parents ``where`` keeps, and the statements the request ran."""
    selection = f"label: {_LABELS[parent]}"
    query = (
        f"query($where: {_input(schema).name}!) {{ rows(filter: $where) {{ "
        f"edges {{ node {{ {selection} }} }} }} }}"
        if typed
        else f"query($where: JSON!) {{ rows(where: $where) {{ {selection} }} }}"
    )
    _CURRENT["schema"] = schema
    try:
        with (
            override_settings(ROOT_URLCONF=__name__),
            CaptureQueriesContext(connection) as queries,
        ):
            payload = graphql_payload(
                query,
                variables={"where": where},
                url="/graphql-conjoined-walked/",
            )
    finally:
        _CURRENT["schema"] = None
    rows = (
        [
            json_at(json_object(edge), "node")
            for edge in json_list(json_at(payload, "data", "rows", "edges"))
        ]
        if typed
        else json_list(json_at(payload, "data", "rows"))
    )
    labels = sorted(str(json_at(json_object(row), "label")) for row in rows)
    return labels, len(queries.captured_queries)


def _walk_nodes(shape: _Shape, walk: str) -> dict[type[Model], bool]:
    """The types each walk registers beside the parent's: every model the path reaches."""
    nodes = dict.fromkeys(
        (model for model in (shape.first_target, shape.target, shape.hidden)),
        False,
    )
    nodes.pop(shape.parent, None)
    if walk == "hiding":
        nodes[shape.hidden] = True
    return nodes


def _walk_filters(shape: _Shape, walk: str) -> dict[str, object]:
    """The ``RelatedFilter`` the ``related-filter`` walk declares on the leaf's first hop."""
    if walk != "related-filter":
        return {}
    child = type(
        "ConjoinedHop",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": shape.first_target, "fields": []})},
    )
    return {"hop": RelatedFilter(child, field_name=shape.first)}


#: The statements one request runs: the parents' select, after a model-choice form's
#: read of the chosen rows.
_STATEMENTS = {"model": 2, "choice": 1}


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
@pytest.mark.parametrize("kind", ["model", "choice"])
@pytest.mark.parametrize("name", list(_SHAPES))
def test_a_walked_conjoined_leaf_keeps_a_parent_reaching_a_visible_row_for_each_value(
    name: str,
    kind: str,
    walk: str,
) -> None:
    """Each value is met by some visible related row; ``exclude`` drops a parent any value meets."""
    _world()
    shape = _SHAPES[name]
    filters = {
        "probe": _declare(shape, kind),
        "probe_out": _declare(shape, kind, exclude=True),
        "probe_any": _declare(shape, kind, conjoined=False),
        **_walk_filters(shape, walk),
    }
    # No generated input types a ``MultipleChoiceFilter`` on a relation key: a resolver
    # applies it to the value sent.
    typed = kind == "model" or not shape.key
    schema, _types = _schema(shape.parent, filters, _walk_nodes(shape, walk), typed=typed)
    answered: dict[str, tuple[list[str], int]] = {}
    expected: dict[str, tuple[list[str], int]] = {}
    for case, answer in shape.answers.items():
        leaf = {"excluded": "probe_out", "unconjoined": "probe_any"}.get(
            case.partition("-")[0],
            "probe",
        )
        value = shape.wire(kind, answer.labels)
        where: JSONObject = _where(schema, (leaf, "exact"), value) if typed else {leaf: value}
        answered[case] = _post(schema, shape.parent, where, typed=typed)
        rows = answer.visible if walk == "hiding" and answer.visible is not None else answer.every
        expected[case] = (list(rows), _STATEMENTS[kind])
    assert answered == expected


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
def test_a_walked_required_conjoined_leaf_asks_is_noop_once_of_the_whole_value(
    walk: str,
) -> None:
    """``always_filter`` off: every choice sent constrains nothing, two run no count per value."""
    _world()
    shape = _SHAPES["reverse-key"]
    probe = _declare(shape, "model", required=True)
    probe.always_filter = False
    schema, _types = _schema(
        shape.parent,
        {"probe": probe, **_walk_filters(shape, walk)},
        _walk_nodes(shape, walk),
    )
    every = shape.wire(
        "model",
        [
            "a1",
            "a2",
            "ah",
            "b1",
            "dh",
        ],
    )
    two = shape.wire("model", ["a1", "a2"])
    every_rows, every_statements = _post(
        schema,
        shape.parent,
        _where(schema, ("probe", "exact"), every),
    )
    # A value constraining something runs the statements one constraining nothing runs: the
    # default ``is_noop`` counts the choices for the whole value, never for each value.
    assert (every_rows, _post(schema, shape.parent, _where(schema, ("probe", "exact"), two))) == (
        [
            "alpha",
            "beta",
            "delta",
            "gamma",
        ],
        (["alpha"], every_statements),
    )


class _RawKeys(MultipleChoiceFilter):
    """A class-level ``filter`` override answering as django-filter does."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return super().filter(qs, value)


class _GlobalIDKeys(GlobalIDMultipleChoiceFilter):
    """A class-level ``filter`` override answering as the package's GlobalID filter does."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return super().filter(qs, value)


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
@pytest.mark.parametrize("kind", ["raw-key", "global-id"])
def test_a_conjoined_key_override_keeps_a_parent_reaching_a_visible_row_each_value_names(
    kind: str,
    walk: str,
) -> None:
    """The override runs as declared; its raw keys or GlobalIDs each name a visible shelf."""
    _world()
    shape = _SHAPES["reverse-key"]
    shelf_pks = shape.value(
        [
            "a1",
            "a2",
            "ah",
            "b1",
            "dh",
        ],
    )
    if kind == "raw-key":
        choices = [(pk, pk) for pk in shelf_pks]
        probe: Filter = _RawKeys(field_name="shelves", choices=choices, conjoined=True)
        probe_out: Filter = _RawKeys(
            field_name="shelves",
            choices=choices,
            conjoined=True,
            exclude=True,
        )
    else:
        probe = _GlobalIDKeys(field_name="shelves", conjoined=True)
        probe_out = _GlobalIDKeys(field_name="shelves", conjoined=True, exclude=True)
    typed = kind == "global-id"
    schema, types = _schema(
        shape.parent,
        {"probe": probe, "probe_out": probe_out, **_walk_filters(shape, walk)},
        _walk_nodes(shape, walk),
        typed=typed,
    )
    shelf_type = types[models.Shelf]

    def value(*codes: str) -> list[str]:
        keys = shape.value(codes)
        return keys if kind == "raw-key" else [global_id_for(shelf_type, key) for key in keys]

    hidden = [] if walk == "hiding" else ["alpha"]

    def where(leaf: str, codes: Sequence[str]) -> JSONObject:
        sent = value(*codes)
        return _where(schema, (leaf, "exact"), sent) if typed else {leaf: sent}

    assert {
        case: _post(schema, shape.parent, where(leaf, codes), typed=typed)[0]
        for case, leaf, codes in (
            ("two-rows-one-parent", "probe", ("a1", "a2")),
            ("two-parents", "probe", ("a1", "b1")),
            ("hidden-member", "probe", ("a1", "ah")),
            ("excluded", "probe_out", ("a1", "a2")),
            ("excluded-two-parents", "probe_out", ("a1", "b1")),
        )
    } == {
        "two-rows-one-parent": ["alpha"],
        "two-parents": [],
        "hidden-member": hidden,
        "excluded": ["beta", "delta", "gamma"],
        "excluded-two-parents": ["delta", "gamma"],
    }


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
def test_a_conjoined_child_leaf_answers_per_child_row_nested_and_over_the_parent_flat(
    walk: str,
) -> None:
    """Nested, one shelf holds every title; flat, the branch's shelves hold them between them."""
    _world()
    child = type(
        "ConjoinedShelfBooks",
        (FilterSet,),
        {
            "book_title": MultipleChoiceFilter(
                field_name="books__title",
                choices=[
                    (title, title)
                    for title in (
                        "x0",
                        "x1",
                        "x2",
                        "x3",
                        "x4",
                        "xh",
                    )
                ],
                conjoined=True,
            ),
            "Meta": type("Meta", (), {"model": models.Shelf, "fields": []}),
        },
    )
    schema, _types = _schema(
        models.Branch,
        {"shelves": RelatedFilter(child, field_name="shelves")},
        {models.Shelf: False, models.Book: walk == "hiding"},
    )
    flat_name = next(
        field.python_name
        for field in require_definition(schema, _input(schema).name).fields
        if field.python_name
        not in {
            "shelves",
            "and_",
            "or_",
            "not_",
        }
    )
    hidden = [] if walk == "hiding" else ["alpha"]
    answered = {
        (spelling, titles): _post(
            schema,
            models.Branch,
            _where(
                schema,
                ("shelves", "book_title", "exact")
                if spelling == "nested"
                else (flat_name, "exact"),
                list(titles),
            ),
        )[0]
        for spelling in ("nested", "flat")
        for titles in (("x1", "x4"), ("x1", "x2"), ("x1", "xh"))
    }
    assert answered == {
        ("nested", ("x1", "x4")): ["alpha"],
        ("flat", ("x1", "x4")): ["alpha"],
        ("nested", ("x1", "x2")): [],
        ("flat", ("x1", "x2")): ["alpha"],
        ("nested", ("x1", "xh")): [],
        ("flat", ("x1", "xh")): hidden,
    }


def require_definition(schema: DjangoSchema, name: str) -> StrawberryObjectDefinition:
    definition = schema.get_type_by_name(name)
    assert isinstance(definition, StrawberryObjectDefinition)
    return definition


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
def test_a_walked_conjoined_global_id_in_leaf_applies_its_list_in_one_predicate(walk: str) -> None:
    """The GlobalID filter applies an ``in`` list itself, one predicate: any value matches."""
    _world()
    shape = _SHAPES["reverse-key"]
    schema, types = _schema(
        shape.parent,
        {
            "probe": GlobalIDMultipleChoiceFilter(
                field_name="shelves",
                lookup_expr="in",
                conjoined=True,
            ),
            **_walk_filters(shape, walk),
        },
        _walk_nodes(shape, walk),
    )

    def ids(*codes: str) -> list[str]:
        return [global_id_for(types[models.Shelf], key) for key in shape.value(codes)]

    assert [
        _post(schema, shape.parent, _where(schema, ("probe", "in_"), ids(*codes)))[0]
        for codes in (("a1", "a2"), ("a1", "b1"))
    ] == [["alpha"], ["alpha", "beta"]]


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
def test_a_conjoined_method_filter_copied_from_a_child_set_receives_the_whole_value(
    walk: str,
) -> None:
    """A ``method=`` filter owns its value: run once with every value over the visible shelves."""
    _world()

    def titled_any(
        _filterset: FilterSet,
        queryset: QuerySet[Model],
        _name: str,
        value: Sequence[str],
    ) -> QuerySet[Model]:
        return queryset.filter(books__title__in=value)

    child = type(
        "ConjoinedShelfMethod",
        (FilterSet,),
        {
            "titled": MultipleChoiceFilter(
                choices=[
                    (title, title)
                    for title in (
                        "x0",
                        "x1",
                        "x2",
                        "x3",
                        "x4",
                        "xh",
                    )
                ],
                conjoined=True,
                method="titled_any",
            ),
            "titled_any": titled_any,
            "Meta": type("Meta", (), {"model": models.Shelf, "fields": []}),
        },
    )
    schema, _types = _schema(
        models.Branch,
        {"shelves": RelatedFilter(child, field_name="shelves")},
        {models.Shelf: walk == "hiding", models.Book: False},
    )
    flat_name = next(
        field.python_name
        for field in require_definition(schema, _input(schema).name).fields
        if field.python_name
        not in {
            "shelves",
            "and_",
            "or_",
            "not_",
        }
    )
    assert [
        _post(schema, models.Branch, _where(schema, (flat_name, "exact"), list(titles)))[0]
        for titles in (("x1", "x3"), ("x1", "xh"))
    ] == [["alpha", "beta"], ["alpha"]]


class _OneShotChoices(forms.MultipleChoiceField):
    """Cleans to a generator over the chosen values, as a consumer form field may."""

    @override
    def clean(self, value: object) -> Iterator[str]:
        # ``forms.Field.clean``'s three steps, its result handed on as a generator.
        cleaned = self.to_python(value)
        self.validate(cleaned)
        self.run_validators(cleaned)
        return (each for each in cleaned)


class _OneShotFilter(MultipleChoiceFilter):
    """A shipped conjoined filter whose form field cleans to a one-shot generator."""

    field_class = _OneShotChoices


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
def test_a_walked_conjoined_leaf_reads_every_value_a_one_shot_cleaned_value_holds(
    walk: str,
) -> None:
    """A generator the form cleans to answers each value as the unwalked leaf answers it."""
    _world()
    shape = _SHAPES["reverse-column"]
    choices = [
        (code, code)
        for code in (
            "a1",
            "a2",
            "ah",
            "b1",
            "dh",
        )
    ]
    schema, _types = _schema(
        shape.parent,
        {
            "probe": _OneShotFilter(field_name=shape.leaf, choices=choices, conjoined=True),
            **_walk_filters(shape, walk),
        },
        _walk_nodes(shape, walk),
        typed=False,
    )
    assert [
        _post(schema, shape.parent, {"probe": list(codes)}, typed=False)[0]
        for codes in (("a1", "a2"), ("a1", "b1"))
    ] == [["alpha"], []]
