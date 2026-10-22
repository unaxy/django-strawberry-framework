"""``DjangoMutation`` base + metaclass + ``Meta`` validation + phase-2.5 bind.

The write-side declarative surface, in the spirit of ``filters/sets.py`` /
``orders/sets.py`` (a base class with a nested ``class Meta``, never a decorator -
spec-036 Decision 3 / START.md). This module owns four concerns:

- ``DjangoMutation`` - the consumer-facing base. A concrete subclass declares a
  nested ``Meta`` (``model`` + ``operation`` + optional ``input_class`` /
  ``partial_input_class`` / ``fields`` / ``exclude`` / ``permission_classes``);
  the metaclass validates it at class creation and registers the declaration.
- ``DjangoMutationMetaclass`` - collects + validates ``Meta`` at class creation
  and registers the concrete subclass (the abstract base carries no ``Meta`` and
  is skipped, the same in-flight-base-class guard the set metaclasses rely on).
  Built by ``write_mixins.py::make_meta_validating_metaclass`` (the shared
  write-flavor substrate) so the plain-form flavor shares the lifecycle.
- the declaration registry (``register_mutation`` / ``clear_mutation_registry`` /
  ``iter_mutations``) the finalizer bind drains. ``register_mutation`` rejects a
  late declaration after ``registry.mark_finalized()`` (spec-036 Edge cases).
- ``bind_mutations()`` - the phase-2.5 entry point the finalizer calls. For each
  registered mutation it resolves the model's primary ``DjangoType`` (spec-036
  Decision 11), builds + materializes the generated ``Input`` / ``PartialInput``
  classes (``create`` / ``update``) and the ``<Name>Payload`` (every operation)
  as module globals of ``mutations.inputs`` before ``strawberry.Schema(...)`` runs
  (spec-036 Decision 12), raising ``ConfigurationError`` on a no-primary target or
  a duplicate generated GraphQL name.

Deliberate divergence from ``_bind_sidecar_sets`` (spec-036 Decision 5): a
``DjangoMutation`` is NOT a ``DjangoType`` sidecar (it has its own ``Meta.model``,
not a ``DjangoType``-definition attr like ``orderset_class``), so the bind iterates
the **mutation-declaration registry**, not ``registry.iter_definitions()``. It is a
sibling of ``_bind_filtersets`` / ``_bind_ordersets`` at the *placement* level
(same phase-2.5 window), not a ``_bind_sidecar_sets`` consumer.

The mutation ``Meta`` is its OWN validation namespace, disjoint from the
``DjangoType`` ``Meta`` (spec-036 Decision 12): this module defines its own
allowed-key set and does NOT import / extend ``types/base.py``'s
``ALLOWED_META_KEYS`` / ``DEFERRED_META_KEYS`` (which stay byte-unchanged).

**No resolver, no ``DjangoMutationField``, no permission *enforcement* lands
here.** Those live in ``resolvers.py`` + ``fields.py``. A ``DjangoMutation``
declared here is inert until a field exposes it: registered + bound at finalize,
never resolved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeGuard, cast, get_origin

import strawberry
from strawberry import relay
from strawberry.types.base import StrawberryList, StrawberryObjectDefinition

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import register_subsystem_clear, registry
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from django_strawberry_framework.utils.inputs import (
    InputFieldSpec,
    get_or_store_shape_build,
    make_shape_build_cache,
)
from django_strawberry_framework.utils.typing import unwrap_return_type
from django_strawberry_framework.write_mixins import (
    MODEL_BACKED_WRITE_META_KEYS,
    _ValidatedMutationMeta,
    backing_model_of,
    bind_write_declarations,
    dispatch_resolver_entry,
    make_declaration_registry,
    make_meta_validating_metaclass,
    model_backed_permission_and_lock,
    normalize_meta_field_selection,
    reject_unknown_meta_keys,
    require_model_class,
    resolver_seams,
)

from .inputs import (
    CREATE,
    INPUTS_MODULE_PATH,
    PARTIAL,
    build_mutation_input,
    editable_input_fields,
    materialize_mutation_input_class,
    mutation_input_field_specs,
    mutation_input_shape,
    relation_input_annotation,
)
from .operations import (
    _OPERATION_INPUT_OVERRIDE_ATTR,
    _VALID_OPERATIONS,
    NON_DELETE_OPERATION_INPUT_KIND,
)
from .permissions import run_permission_classes

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Protocol

    from django.db import models
    from strawberry.types import Info
    from strawberry.types.base import WithStrawberryObjectDefinition
    from strawberry.types.field import StrawberryField

    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.write_mixins import DeclarationRegistry, _BoundDeclaration

    from .inputs import ModelFieldIndex, MutationInputShape


# The mutation ``Meta``'s own allowed-key set (spec-036 Decision 12). Disjoint
# from ``types/base.py::ALLOWED_META_KEYS``: a mutation
# ``Meta`` is the mutation class's own namespace, composed from the shared
# ``MODEL_BACKED_WRITE_META_KEYS`` plus model-flavor specific keys.
_ALLOWED_MUTATION_META_KEYS: frozenset[str] = MODEL_BACKED_WRITE_META_KEYS | frozenset(
    {"model", "input_class", "partial_input_class"},
)


#: The model flavor's resolver module and its two entries, shared by ``DjangoMutation``'s
#: runtime seams and the checker's reading of them (``_ModelResolverSeams``).
_MUTATION_RESOLVERS_MODULE = "django_strawberry_framework.mutations.resolvers"
_MUTATION_SYNC_ENTRY = "resolve_mutation_sync"
_MUTATION_ASYNC_ENTRY = "resolve_mutation_async"


# Per-finalize-pass build cache keyed by generated-input shape identity
# (``(model, operation_kind, frozenset(effective field names))``, spec-036
# Decision 6 #"Type identity and naming"). The key is the EFFECTIVE field set, NOT the raw
# ``(fields, exclude)`` declaration: two declarations that resolve to the same
# effective shape via different ``fields`` / ``exclude`` spellings (e.g.
# ``fields=("name",)`` vs the complementary ``exclude=(<the rest>)``, or a
# ``fields`` list naming the full editable set vs an un-narrowed create) must
# dedupe to one type (spec-036 Edge cases #"Two mutations over one model").
# Keying on the effective set mirrors
# ``mutations/inputs.py::mutation_input_shape``'s identity tuple (cache_key /
# type_name), so the cache key, the generated name, the field name seam, and the
# spec identity are single-sourced and cannot drift - two mutations with the same
# effective shape reuse one class object so the materialize ledger dedupes
# idempotently instead of seeing two distinct same-named classes.
#
# The ``(cache, clear)`` pair rides ``utils/inputs.py::make_shape_build_cache``,
# the same factory forms + serializer use, so the three write
# flavors share one dict-plus-clear shape while staying disjoint. Cleared at the
# start of ``bind_mutations()`` AND co-cleared from ``registry.clear()`` so a
# stale class from a prior (failed or re-run) finalize never leaks across a
# clear that does not itself re-bind.
_shape_build_cache: dict[
    tuple[type[models.Model], str, frozenset[str]],
    type[WithStrawberryObjectDefinition],
]
clear_mutation_shape_build_cache: Callable[[], None]
_shape_build_cache, clear_mutation_shape_build_cache = make_shape_build_cache()
register_subsystem_clear(clear_mutation_shape_build_cache, owner="mutations.shape_cache")


# The model-flavor declaration registry: every concrete ``DjangoMutation`` records
# itself here at class creation; ``bind_mutations`` drains it at phase 2.5 and
# ``registry.clear()`` resets it via ``clear_mutation_registry``. The list +
# callables come from ``make_declaration_registry`` (spec-038 Decision 13) so the
# plain-form flavor (``forms/sets.py``) instantiates the SAME mechanics over a
# SECOND, disjoint list - the dedup / reject / clear logic is single-sourced while
# the two ledgers stay separate. ``register_mutation`` / ``clear_mutation_registry``
# / ``iter_mutations`` stay the importable public names ``registry.py`` (the
# co-clear), the metaclass, ``mutations/fields.py``, and the tests reference;
# ``_mutation_registry`` stays the backing list the idempotency tests introspect.
_mutation_declaration_registry: DeclarationRegistry[type[DjangoMutation]] = (
    make_declaration_registry("DjangoMutation")
)
register_mutation: Callable[[type[DjangoMutation]], None] = _mutation_declaration_registry.register
clear_mutation_registry: Callable[[], None] = _mutation_declaration_registry.clear
iter_mutations: Callable[[], tuple[type[DjangoMutation], ...]] = (
    _mutation_declaration_registry.iter_
)
_mutation_registry = _mutation_declaration_registry.store
register_subsystem_clear(clear_mutation_registry, owner="mutations.declarations")


def _is_input_type(value: object) -> TypeGuard[type[WithStrawberryObjectDefinition]]:
    """Whether ``value`` is a ``@strawberry.input``-decorated class.

    ``TypeGuard``: a decorated OUTPUT type is a ``WithStrawberryObjectDefinition`` too,
    and answers ``False``.
    """
    if not truth.is_type(value):
        return False
    definition = truth.static_attr(value, "__strawberry_definition__")
    return truth.is_instance(definition, StrawberryObjectDefinition) and definition.is_input


def _validate_input_class(
    mutation_name: str,
    input_class: object,
    *,
    attr_name: str,
    model: type[models.Model],
    fields: tuple[str, ...] | None,
    exclude: tuple[str, ...] | None,
) -> type[WithStrawberryObjectDefinition]:
    """Validate a consumer ``input_class`` / ``partial_input_class``.

    Two checks (spec-036 Decision 5 error-shapes + Decision 6
    #"Custom inputs follow the generated field-naming scheme"):

    1. It is a ``@strawberry.input``-decorated type - a class carrying
       ``__strawberry_definition__`` with ``is_input`` True. A plain class or a
       non-class value raises ``ConfigurationError``.
    2. Its field names do not diverge from the generated naming scheme. The scheme
       is single-sourced with the generator: the expected python-attr set is
       ``editable_input_fields(model, ...)`` mapped through the SAME
       ``relation_input_annotation`` the generator uses (``<field>_id`` for
       forward FK / OneToOne, the plain field name for a scalar / M2M), so the
       validator's notion of "the scheme" cannot drift from
       ``build_mutation_input``. A field whose python-name is not in that set
       raises ``ConfigurationError`` naming the divergence + the expected scheme.
    """
    if not _is_input_type(input_class):
        raise ConfigurationError(
            f"DjangoMutation {mutation_name}.Meta.{attr_name} must be a "
            f"@strawberry.input-decorated type; got {truth.render(input_class)}.",
        )

    expected = _expected_input_attr_names(
        model,
        fields=fields,
        exclude=exclude,
        # ``input_class`` customizes the create input, ``partial_input_class`` the update.
        operation_kind=CREATE if attr_name == "input_class" else PARTIAL,
    )
    supplied = {field.python_name for field in input_class.__strawberry_definition__.fields}
    diverging = sorted(supplied - expected)
    if diverging:
        raise ConfigurationError(
            f"DjangoMutation {mutation_name}.Meta.{attr_name} declares field(s) "
            f"{diverging!r} that diverge from the generated naming scheme "
            f"(scalars use the model field name, forward FK/OneToOne use "
            f"`<field>_id`, M2M uses the field name). Expected names: "
            f"{sorted(expected)!r}.",
        )
    return input_class


def _expected_input_attr_names(
    model: type[models.Model],
    *,
    fields: tuple[str, ...] | None,
    exclude: tuple[str, ...] | None,
    operation_kind: str,
) -> set[str]:
    """Return the python-attr set the generator would emit for ``model``.

    Single-sourced with ``build_mutation_input`` via ``editable_input_fields`` +
    ``relation_input_annotation`` so a custom ``input_class``'s accepted names
    cannot drift from what the generator actually produces. The id-type lookup
    inside ``relation_input_annotation`` is irrelevant to the python-attr (which
    is ``<field>_id`` / the field name regardless of GlobalID-vs-pk), so the
    related-primary argument is passed ``None``.
    """
    names: set[str] = set()
    for field in editable_input_fields(
        model,
        fields=fields,
        exclude=exclude,
        operation_kind=operation_kind,
    ):
        if getattr(field, "is_relation", False):
            python_attr, _graphql_name, _annotation = relation_input_annotation(
                field,
                related_primary_type=None,
            )
            names.add(python_attr)
        else:
            names.add(field.name)
    return names


# Model-flavor metaclass: validate ``Meta`` + register onto the model declaration
# ledger. Built by ``make_meta_validating_metaclass`` (the Decision-13 twin of
# ``make_declaration_registry``) so the plain-form flavor instantiates the SAME
# validate-then-register lifecycle over ``register_form_mutation``. A type checker
# cannot follow a factory-built metaclass into a ``metaclass=`` keyword, so it sees
# the class statement below instead; the runtime binding is the factory product.
if TYPE_CHECKING:

    class DjangoMutationMetaclass(type):
        """The factory-built model-flavor metaclass, as a type checker sees it."""

else:
    DjangoMutationMetaclass = make_meta_validating_metaclass(
        register_mutation,
        name="DjangoMutationMetaclass",
        module=__name__,
    )


# The model-backed ``resolve_sync`` / ``resolve_async`` seams as a type checker reads them.
# The class installs the ``resolver_seams`` pair at run time, which a checker cannot type as
# overridable methods, so it reads them from this typing-only base instead: a consumer's
# override is checked against these signatures, and each body states what the default does.
# At run time the base is ``object``, so ``DjangoMutation``'s bases and MRO are unchanged.
if TYPE_CHECKING:

    class _ModelResolverSeams(Protocol):
        """The overridable model-flavor resolver-dispatch seams (``mutations/fields.py::_resolve``).

        Bare ``Info`` takes Strawberry's ``Any`` TypeVar defaults, so an override may type
        ``info`` with its own context and root.
        """

        @classmethod
        def resolve_sync(
            cls,
            info: Info,
            *,
            data: object,
            id: object,  # noqa: A002
        ) -> object:
            """Dispatch the mutation synchronously."""
            return dispatch_resolver_entry(
                _MUTATION_RESOLVERS_MODULE,
                _MUTATION_SYNC_ENTRY,
                cls,
                info,
                data=data,
                id=id,
            )

        @classmethod
        def resolve_async(
            cls,
            info: Info,
            *,
            data: object,
            id: object,  # noqa: A002
        ) -> object:
            """Dispatch the mutation asynchronously."""
            return dispatch_resolver_entry(
                _MUTATION_RESOLVERS_MODULE,
                _MUTATION_ASYNC_ENTRY,
                cls,
                info,
                data=data,
                id=id,
            )

    _ModelResolverSeamsBase = _ModelResolverSeams
else:
    _ModelResolverSeamsBase = object


class DjangoMutation(_ModelResolverSeamsBase, metaclass=DjangoMutationMetaclass):
    """Consumer-facing write-side base class (spec-036 Decision 3 / Decision 5).

    A concrete mutation declares a nested ``class Meta`` with ``model`` +
    ``operation`` (and optional ``input_class`` / ``partial_input_class`` /
    ``fields`` / ``exclude`` / ``permission_classes``); the metaclass validates it
    at class creation and registers it for the phase-2.5 bind. Uniform with
    ``DjangoType`` / ``FilterSet`` / ``OrderSet`` - a base class with a nested
    ``Meta``, never a decorator.

    A declared mutation is inert until a field exposes it: it is registered +
    bound at finalize (its generated ``Input`` / ``PartialInput`` /
    ``<Name>Payload`` classes are materialized), but never resolved. The
    resolver pipeline, the ``DjangoMutationField`` factory, and permission
    *enforcement* live in ``resolvers.py`` + ``fields.py``.
    """

    # The validated ``Meta`` snapshot the metaclass stashes on a concrete
    # subclass; the bind and the resolver read it. ``None`` on the abstract
    # base (which carries no ``Meta``). A type checker sees the snapshot's own
    # type, since the pipeline reads only a validated subclass's snapshot, never
    # the abstract base's ``None``.
    if TYPE_CHECKING:
        _mutation_meta: ClassVar[_ValidatedMutationMeta]
        #: The consumer's nested ``class Meta`` a concrete mutation declares (the
        #: abstract base declares none, so there is no run-time default).
        Meta: ClassVar[type]
    else:
        _mutation_meta = None

    # Bind outputs. The phase-2.5 bind
    # stashes the resolved primary type, the materialized input class (create /
    # update; ``None`` for delete), and the materialized payload class name here;
    # ``DjangoMutationField`` reads them to synthesize the resolver signature +
    # the ``strawberry.lazy`` payload return-ref. Left ``None`` until the bind runs;
    # a type checker sees the bound types, since only a bound mutation is resolved.
    if TYPE_CHECKING:
        _primary_type: ClassVar[type[DjangoType]]
    else:
        _primary_type = None
    _input_class: ClassVar[type[object] | None] = None
    if TYPE_CHECKING:
        _payload_type_name: ClassVar[str]
    else:
        _payload_type_name = None
    # Bind-stashed reverse map the model decode rides
    # (``utils/write_values.py::decode_provided_fields``). Empty until bind (and
    # stays empty for ``delete``, which has no input). Form / serializer
    # subclasses overwrite ``_input_field_specs`` with their own flavor map.
    _input_field_specs: ClassVar[Sequence[InputFieldSpec]] = ()
    _model_fields_by_attr: ClassVar[ModelFieldIndex | None] = None

    @classmethod
    def _resolve_model(cls, meta: type[object]) -> type[models.Model] | None:
        """Resolve the mutation's Django model from ``Meta`` (the model-resolution seam).

        In 0.0.11 the only source is ``Meta.model``. This is the overridable hook
        the 0.0.12 form flavor (``Meta.form_class._meta.model``) and the 0.0.13
        serializer flavor (``Meta.serializer_class.Meta.model``) replace so they
        supply the model WITHOUT a literal ``Meta.model``, without re-opening the
        base validation (spec-036 Decision 5). A subclass overrides this
        classmethod to change the resolved model.
        """
        return cast("type[models.Model] | None", truth.static_attr(meta, "model"))

    @classmethod
    def _validate_meta(cls, meta: object) -> _ValidatedMutationMeta:
        """Validate a concrete mutation's nested ``Meta`` at class creation (spec-036 Decision 5).

        The overridable validation seam the metaclass invokes
        (``DjangoMutationMetaclass.__new__``). This default is the **model flavor**
        (the 0.0.11 body relocated verbatim from the former module-level
        ``_validate_mutation_meta``); the spec-038 form flavors override it with
        their own matrix (``forms/sets.py``). The validation matrix (raising
        ``ConfigurationError`` naming the offending key, all at class-creation):

        - **unknown ``Meta`` key** - the typo guard over
          ``_ALLOWED_MUTATION_META_KEYS`` (own keys only, no MRO walk), mirroring
          ``types/base.py::_validate_meta``.
        - **no resolvable model** - ``cls._resolve_model(meta)`` returns ``None``
          (in 0.0.11 a missing ``Meta.model``; the seam lets the 0.0.12 / 0.0.13
          flavors supply it differently).
        - **resolved model is not a Django model class** - a string name, a model
          instance, or any non-``models.Model`` type (mirrors
          ``types/base.py::_validate_meta``; without this the bind crashes with a
          raw ``AttributeError`` / ``TypeError``).
        - **bad ``operation``** - missing or not in
          ``{"create", "update", "delete"}``.
        - **``fields`` + ``exclude`` both supplied** - mutual exclusion.
        - **unknown / empty ``fields`` / ``exclude`` on create/update** - the
          ``editable_input_fields`` walk the bind uses, so a typo'd name or an
          empty narrowing fails at class creation (not deferred to finalize).
        - **inapplicable consumer input override** - ``input_class`` on anything
          other than create, or ``partial_input_class`` on anything other than
          update; delete accepts neither because it has no input.
        - **bad ``input_class`` / ``partial_input_class``** - not a
          ``@strawberry.input`` type, or field names diverging from the generated
          scheme.

        ``permission_classes`` + ``select_for_update`` are validated by
        ``model_backed_permission_and_lock`` (the ``DjangoModelPermission``
        default when unset, plus the ``FOR UPDATE`` lock). A bad permission
        entry is rejected here at class creation rather than as a request-time
        ``TypeError`` / ``AttributeError`` inside ``check_permission``
        (spec-036 Decision 15 - the write-auth seam; the enforcement runs in
        the resolver).
        """
        name = truth.name(cls)
        meta = reject_unknown_meta_keys(
            f"DjangoMutation {name}",
            meta,
            _ALLOWED_MUTATION_META_KEYS,
        )

        model = cls._resolve_model(meta)
        if model is None:
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta declares no resolvable model; set Meta.model.",
            )
        # Mirror ``types/base.py::_validate_meta``: a non-model value (a string name,
        # a model *instance*, an unrelated class) must fail at class creation as
        # ``ConfigurationError``. Without this gate the bad value is snapshotted and
        # the phase-2.5 bind crashes with a raw ``AttributeError`` / ``TypeError``
        # (a missing ``_meta`` / unhashable instance) instead of a typed config error.
        # Shared with ModelForm / serializer ``_validate_meta`` via
        # ``require_model_class`` so those overrides cannot skip the gate.
        model = require_model_class(name, model, base_label="DjangoMutation")

        raw_operation = truth.static_attr(meta, "operation")
        if (
            not truth.is_instance(raw_operation, str)
            or (operation := truth.text(raw_operation)) not in _VALID_OPERATIONS
        ):
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta.operation must be one of "
                f"{sorted(_VALID_OPERATIONS)}; got {truth.render(raw_operation)}.",
            )

        # The model-flavor field-sequence pair routes through the shared
        # ``normalize_meta_field_selection`` (spec-039 - no per-flavor
        # re-binding wrapper); the ``DjangoMutation`` flavor label keeps the
        # messages byte-identical.
        fields, exclude = normalize_meta_field_selection(meta, flavor="DjangoMutation")
        if fields is not None and exclude is not None:
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta declares both `fields` and `exclude`; "
                "supply at most one.",
            )
        if operation == "delete" and (fields is not None or exclude is not None):
            # A ``delete`` is ``id:``-only and materializes NO input (spec-036
            # Decision 14), so ``fields`` / ``exclude`` have no effect. Because
            # delete skips input generation, an unknown / malformed name in them is
            # never validated by ``editable_input_fields`` either, so a typo'd field
            # silently finalizes. Reject the inapplicable keys outright: declaring
            # them on a delete is a configuration mistake regardless of whether the
            # names are valid.
            raise ConfigurationError(
                f"DjangoMutation {name}.Meta.operation is 'delete', which is id-only and "
                "takes no input; remove the inapplicable Meta.fields / Meta.exclude.",
            )

        # Create / update materialize an input from the editable column set. Run the
        # SAME ``editable_input_fields`` walk the bind / generator use NOW so an
        # unknown / non-editable name and an empty narrowing fail at class creation
        # (the form flavor's posture via ``resolve_effective_form_fields``), not as a
        # deferred finalize-time ``ConfigurationError`` after the class already
        # registered. Delete is excluded above (it takes no input).
        if operation != "delete":
            selected = editable_input_fields(
                model,
                fields=fields,
                exclude=exclude,
                operation_kind=NON_DELETE_OPERATION_INPUT_KIND[operation],
            )
            if not selected:
                raise ConfigurationError(
                    f"DjangoMutation {name}.Meta.fields / Meta.exclude narrowed the "
                    f"editable column set to empty (or {truth.name(model)} declares no "
                    f"editable columns). A {operation} mutation input must define at "
                    "least one field.",
                )

        # Reject consumer input overrides that the declared operation cannot use.
        # Delete has no input; create and update each read only their matching
        # override. Without this guard, a valid customization is accepted and then
        # silently discarded at bind time. The same mapping selects the override in
        # ``_materialize_input_for``, so validation cannot drift from materialization.
        for applies_to, override_key in _OPERATION_INPUT_OVERRIDE_ATTR.items():
            if operation != applies_to and truth.static_attr(meta, override_key) is not None:
                raise ConfigurationError(
                    f"DjangoMutation {name}.Meta.{override_key} applies only to "
                    f"operation='{applies_to}' (it customizes the {applies_to} input); this "
                    f"mutation declares operation={operation!r}, so Meta.{override_key} would be "
                    "silently ignored at the bind. Remove it.",
                )

        input_class = truth.static_attr(meta, "input_class")
        if input_class is not None:
            input_class = _validate_input_class(
                name,
                input_class,
                attr_name="input_class",
                model=model,
                fields=fields,
                exclude=exclude,
            )
        partial_input_class = truth.static_attr(meta, "partial_input_class")
        if partial_input_class is not None:
            partial_input_class = _validate_input_class(
                name,
                partial_input_class,
                attr_name="partial_input_class",
                model=model,
                fields=fields,
                exclude=exclude,
            )

        permission_classes, select_for_update = model_backed_permission_and_lock(
            name,
            meta,
            flavor="DjangoMutation",
        )

        return _ValidatedMutationMeta(
            model=model,
            operation=operation,
            input_class=input_class,
            partial_input_class=partial_input_class,
            fields=fields,
            exclude=exclude,
            permission_classes=permission_classes,
            select_for_update=select_for_update,
        )

    # Module path the generated input class is materialized into - the
    # ``strawberry.lazy`` target ``DjangoMutationField`` references for
    # the ``data:`` argument. The model default is ``mutations.inputs``; the form
    # flavors override it to ``forms.inputs`` (a disjoint namespace). A class
    # attribute (not a classmethod) because it has no per-``Meta`` dependence.
    input_module_path: ClassVar[str] = INPUTS_MODULE_PATH

    @classmethod
    def build_input(
        cls,
        meta: _ValidatedMutationMeta,
        primary_type: type[DjangoType],
    ) -> type[object] | None:
        """Build + materialize the operation's generated input class (the bind hook seam).

        The overridable input-materialization seam ``bind_write_declarations`` calls at
        phase 2.5. The **model default** delegates to ``_materialize_input_for``
        (today's exact model behavior: the model-column ``<Model>Input`` /
        ``<Model>PartialInput`` built from the editable columns, or ``None`` for a
        ``delete``), then stashes ``_input_field_specs`` + ``_model_fields_by_attr`` for
        the decode; the form flavors override it to build the form-derived input from
        ``forms/inputs.py`` instead (spec-038 Decision 13). Returning ``None`` means "no
        input for this operation" (the model ``delete`` case).
        """
        input_cls = _materialize_input_for(truth.name(cls), meta, primary_type)
        if input_cls is not None:
            # The decode's bind-time hand-off: total-coverage specs (merged
            # dataclass, consumer overrides included) + the Django-field index
            # (``relation_field.null`` and the ``_provided_attr_names``
            # FK-to-field-name reversal).
            cls._input_field_specs, cls._model_fields_by_attr = mutation_input_field_specs(
                backing_model_of(meta),
                input_cls,
            )
        return input_cls

    @classmethod
    def input_type_name(cls, meta: _ValidatedMutationMeta) -> str:
        """Return the generated input class name for a create / update mutation (the name seam).

        The overridable input-name seam ``mutations/fields.py`` consults
        to synthesize the lazy ``data:`` forward-ref. The **model default** reads
        ``mutation_input_shape(...).type_name`` - the SAME descriptor the bind /
        ``build_mutation_input`` path uses for the materialize name and the shape
        cache key, so the field's lazy ``data:`` ref can never disagree
        with the class the bind pins. The form flavors override it with
        ``forms/inputs.py::form_input_type_name``.

        ``mutations/fields.py::_synthesized_mutation_signature`` consults this
        seam (spec-038), so this is the single source for the model ``data:``
        lazy-ref name.

        A validated ``delete`` raises the typed ``ConfigurationError`` (never the
        raw ``KeyError`` a direct index leaked): a delete is id-only and
        materializes no input, and the framework never consults this seam for one
        (``operation_takes_data`` gates the ``data:`` ref at the field factory), so
        only a direct consumer call can reach the reject - where it must still fail
        loud as the package's typed error, mirroring ``_materialize_input_for``'s
        ``.get()`` delete short-circuit.
        """
        operation_kind = NON_DELETE_OPERATION_INPUT_KIND.get(meta.operation)
        if operation_kind is None:
            raise ConfigurationError(
                f"DjangoMutation {truth.name(cls)} declares operation='delete', which is "
                "id-only and materializes no input; input_type_name applies only to "
                "create / update mutations.",
            )
        return mutation_input_shape(
            backing_model_of(meta),
            operation_kind,
            fields=meta.fields,
            exclude=meta.exclude,
        ).type_name

    # The overridable sync / async resolver-dispatch seams
    # (``mutations/fields.py::_resolve`` calls them). The **model default** delegates
    # to ``mutations/resolvers.py::resolve_mutation_sync`` / ``resolve_mutation_async``
    # (the function-local import inside the generated seam keeps the module-load order
    # independent of ``resolvers.py``); the form + serializer flavors override this
    # pair with their own ``resolver_seams(...)`` call (the eight
    # near-identical seam bodies single-sited as one factory). A type checker sees
    # the pair as the classmethods the factory builds, so a subclass may override
    # either with a method (``_ModelResolverSeams`` carries the checker's reading).
    if not TYPE_CHECKING:
        resolve_sync, resolve_async = resolver_seams(
            _MUTATION_RESOLVERS_MODULE,
            _MUTATION_SYNC_ENTRY,
            _MUTATION_ASYNC_ENTRY,
        )

    def check_permission(
        self,
        info: Info,
        operation: str,
        # basedpyright: consumer hook: a narrower base fails an override typing its own data
        data: Any,  # pyright: ignore[reportExplicitAny, reportAny]  # noqa: ANN401 - consumer hook; an override narrows it
        # basedpyright: consumer hook: an override typing ``Item | None`` fails a narrower base
        instance: Any = None,  # pyright: ignore[reportExplicitAny, reportAny]  # noqa: ANN401 - consumer hook; an override narrows it
    ) -> bool:
        """Return whether the request is authorized for ``operation`` (spec-036 Decision 15).

        The imperative override point: a subclass redefines this to replace /
        extend the class-based check. The default delegates to every
        ``Meta.permission_classes`` entry, returning ``False`` as soon as one
        denies and ``True`` only when all allow. The resolver maps a ``False``
        return to a raised ``GraphQLError`` (the top-level authorization failure,
        distinct from the field-keyed validation envelope).

        **Defined here; invoked only by the resolver**, at
        the pipeline placement spec-036 Decision 8 step 3 / Decision 15 pins
        (before the write for ``create``; after the visibility lookup for
        ``update`` / ``delete``). This module ships only the default method body
        + the ``permission_classes`` default assignment; the raise-on-denial lives
        in ``resolvers.py``.

        An ``async def has_permission`` entry returns a coroutine, which is truthy:
        a naive ``if not has_permission(...)`` would never deny it, so an async
        deny-check would be silently treated as ALLOW - an authorization bypass. The pipeline
        is synchronous (spec-036 Decision 15), so the coroutine can never be awaited here;
        it is closed and raised as a ``SyncMisuseError``, the same discipline
        ``apply_type_visibility_sync`` applies to an async ``get_queryset``. (An async
        ``check_permission`` override is caught by the resolver's ``authorize_or_raise`` one
        level up.)

        The walk body is single-sited in
        ``mutations/permissions.py::run_permission_classes``,
        shared with the plain ``DjangoFormMutation`` (which is not a
        ``DjangoMutation`` subclass), so the authorization seam cannot fork.
        """
        # basedpyright: the consumer-hook Any parameters above, handed on to the shared walk
        return run_permission_classes(self, info, operation, data, instance)  # pyright: ignore[reportAny]


def _resolve_primary_type(
    mutation_cls: _BoundDeclaration[type[DjangoType]],
    model: type[models.Model],
) -> type[DjangoType]:
    """Resolve ``model``'s primary ``DjangoType`` for a mutation, or raise (spec-036 Decision 11).

    Distinguishes the two finalize-time error cases (spec-036 Error shapes):

    - **no registered type at all** (``types_for(model)`` empty) -> "no type to
      return" - the return payload + relation-id strategy cannot be resolved.
    - **multiple types, no declared primary** (``get`` returns ``None`` but
      ``types_for`` is non-empty) -> the ``Meta.primary`` ambiguity error.

    ``registry.get`` returning ``None`` does not distinguish them, so ``types_for``
    is consulted to phrase the right message. (A model with multiple types and no
    primary already fails the Phase-1 ``_audit_primary_ambiguity`` upstream, but
    the bind raises its own clear message for the zero-type case and stays robust
    if the model reaches the bind unaudited.)
    """
    primary = registry.get(model)
    if primary is not None:
        return primary
    if registry.types_for(model):
        raise ConfigurationError(
            f"DjangoMutation {truth.name(mutation_cls)} targets {truth.name(model)}, which has "
            "multiple registered DjangoTypes and no declared primary; set Meta.primary on "
            "one of them so the mutation return type is unambiguous.",
        )
    raise ConfigurationError(
        f"DjangoMutation {truth.name(mutation_cls)} targets {truth.name(model)}, which has no "
        "registered DjangoType; the mutation has no type to return. Declare a "
        f"DjangoType for {truth.name(model)}.",
    )


def _materialize_input_for(
    mutation_name: str,
    meta: _ValidatedMutationMeta,
    primary_type: type[DjangoType],
) -> type[WithStrawberryObjectDefinition] | None:
    """Build + materialize the operation's input class, or return ``None`` for ``delete``.

    ``create`` builds the ``<Model>Input`` (``CREATE`` kind); ``update`` builds the
    ``<Model>PartialInput`` (``PARTIAL`` kind); ``delete`` is ``id:``-only and
    needs no input (spec-036 Decision 14). A consumer ``input_class`` /
    ``partial_input_class`` is **merged** with the generated input, NOT a wholesale
    replacement (the spec-010 relation-override contract, spec-036 DoD): the
    consumer declares the field(s) it wants to customize
    (using the generated naming scheme - validated at class creation), the
    generator fills the rest of the editable shape, and the consumer's fields are
    honored, never clobbered. See ``_materialize_merged_input``.

    Identical generated shapes dedupe to one class object: the shape identity is
    ``(model, operation kind, frozenset(effective field names))`` (spec-036
    Decision 6). The first mutation with a given shape builds + caches the class in
    ``_shape_build_cache``; a later mutation with the identical shape reuses that
    cached object, so ``materialize_mutation_input_class`` sees the SAME class
    twice and dedupes idempotently (rather than a fresh, name-colliding object). A
    consumer-merged input is materialized under the SAME canonical shape name (it
    customizes representations of existing columns, it does not change the field
    set), so two mutations resolving the same shape to two DIFFERENT representations
    still raise the collision.
    """
    operation_kind = NON_DELETE_OPERATION_INPUT_KIND.get(meta.operation)
    if operation_kind is None:
        return None  # delete: id-only, no input.

    consumer_input = read_attr(meta, _OPERATION_INPUT_OVERRIDE_ATTR[meta.operation])
    if consumer_input is not None:
        # The snapshot holds a validated input class or ``None``.
        return _materialize_merged_input(
            mutation_name,
            meta,
            primary_type,
            operation_kind,
            cast("type[WithStrawberryObjectDefinition]", consumer_input),
        )

    # Derive the shape ONCE: ``mutation_input_shape`` single-sources the
    # cache key (the EFFECTIVE field set, NOT the raw ``(fields, exclude)``
    # spelling - two narrowings to one effective shape must dedupe, spec-036
    # Edge cases #"Two mutations over one model") AND the generated name, so the
    # bind cache key and the generated type name cannot drift. The same
    # descriptor is handed to
    # ``build_mutation_input`` so it does not re-walk the editable fields.
    shape = mutation_input_shape(
        backing_model_of(meta),
        operation_kind,
        fields=meta.fields,
        exclude=meta.exclude,
    )
    input_cls = get_or_store_shape_build(
        _shape_build_cache,
        shape.cache_key,
        lambda: build_mutation_input(
            backing_model_of(meta),
            operation_kind=operation_kind,
            primary_type=primary_type,
            fields=meta.fields,
            exclude=meta.exclude,
            shape=shape,
        ),
    )
    materialize_mutation_input_class(
        truth.name(input_cls),
        input_cls,
        f"the input of DjangoMutation {mutation_name!r}",
    )
    return input_cls


def _materialize_merged_input(
    mutation_name: str,
    meta: _ValidatedMutationMeta,
    primary_type: type[DjangoType],
    operation_kind: str,
    consumer_input: type[WithStrawberryObjectDefinition],
) -> type[WithStrawberryObjectDefinition]:
    """Merge a consumer ``input_class`` with the generated remainder (spec-010).

    The consumer-authored ``@strawberry.input`` declares only the field(s) it
    customizes (a custom scalar, validator, alias, description), using the
    generated naming scheme (``_validate_input_class`` already pinned ``supplied
    expected``). Those python-attr names are passed to ``build_mutation_input`` as
    ``overrides`` so the generator emits every OTHER editable column and SKIPS the
    consumer-authored ones - the generated remainder. The two are combined by
    **class inheritance** (``strawberry.input(type(name, (consumer, remainder),
    {}))``): Strawberry collects the union of both bases' fields, the consumer base
    takes MRO precedence, and the consumer's field definitions are preserved
    EXACTLY (annotation, default / required-ness, ``name=`` alias, description,
    directives) rather than reconstructed from triples. Because ``overrides``
    guarantees the two field sets are disjoint, there is no duplicate-field clash.

    The merged class is named + materialized under the **canonical shape name**
    (``shape.type_name`` from the shared ``mutation_input_shape`` descriptor,
    derived from the full selected field set, which still includes the overridden
    columns, so it is the same ``<Model>Input`` / shape-derived name the
    all-generated path uses): the consumer customizes representations of existing
    columns, it does NOT change the shape identity ``(model, operation kind,
    frozenset(effective names))``. A merged input is therefore NOT cached in
    ``_shape_build_cache`` (it is mutation-specific), and if two mutations resolve
    the same shape to two different representations they collide on that name and
    raise the ``ConfigurationError`` at ``materialize_mutation_input_class`` -
    the same fail-loud the all-generated collision uses.
    """
    consumer_attrs = frozenset(
        field.python_name for field in consumer_input.__strawberry_definition__.fields
    )
    shape = mutation_input_shape(
        backing_model_of(meta),
        operation_kind,
        fields=meta.fields,
        exclude=meta.exclude,
    )
    _validate_relation_override_types(
        mutation_name,
        consumer_input,
        shape,
        attr_name="input_class" if operation_kind == CREATE else "partial_input_class",
    )
    remainder = build_mutation_input(
        backing_model_of(meta),
        operation_kind=operation_kind,
        primary_type=primary_type,
        fields=meta.fields,
        exclude=meta.exclude,
        overrides=consumer_attrs,
        shape=shape,
    )
    merged = strawberry.input(type(shape.type_name, (consumer_input, remainder), {}))
    materialize_mutation_input_class(shape.type_name, merged)
    return merged


def _validate_relation_override_types(
    mutation_name: str,
    consumer_input: type[WithStrawberryObjectDefinition],
    shape: MutationInputShape,
    *,
    attr_name: str,
) -> None:
    """Type- and shape-lock a relation override to the generated id (spec-036 Decision 10).

    A relation column whose related model HAS a primary Relay-Node type generates a
    ``relay.GlobalID`` (forward FK / OneToOne) or ``list[relay.GlobalID]`` (M2M) input
    whose decode is **type-checked against the relation target** AND
    **visibility-checked through the related type's ``get_queryset``** (spec-036
    Decision 10) - so a permitted writer cannot attach a row they could
    not *see*. The visibility check holds for any input shape:
    ``utils/write_values.py::decode_visible_relation_ids`` confirms every decoded
    pk, raw or from a ``GlobalID``, through the related primary type's
    ``get_queryset``. The type-check rides the EXACT generated shape: the same
    decoder decodes a ``relay.GlobalID`` against the relation target (the FK path
    unwraps a one-element list, the M2M path iterates a flat list) and coerces
    anything else as a raw pk through the target's pk field.

    The naming half (``_validate_input_class``) lets a consumer override a
    relation field's *representation* under its generated ``<field>_id`` / ``list``
    name, but it name-checks only - so a consumer could declare a divergent TYPE or
    CONTAINER SHAPE and the merge would honor it, defeating the decode:

    - ``category_id: int`` (raw pk core) - the value is coerced as a raw pk and
      still confirmed through the related primary type's ``get_queryset``, but the
      ``GlobalID`` decode never runs (target-model match, node-id coercion through
      the type's id field, mapping to the real pk), so the input takes raw pks
      where the generated schema takes ``GlobalID``s;
    - ``genres: relay.GlobalID`` (M2M overridden as a SCALAR) - the M2M decoder
      materializes the value as a container, a ``GlobalID`` is not iterable, so every
      request is the field-keyed invalid-relation ``FieldError``;
    - ``genres: list[list[relay.GlobalID]]`` (NESTED list) - each inner list is not a
      ``relay.GlobalID``, so it is coerced as a raw pk through the target's pk field,
      fails, and every request is the field-keyed invalid-relation ``FieldError``;
    - ``category_id: list[relay.GlobalID]`` (FK overridden as a LIST) - the FK decoder
      wraps the value in a one-element list, the inner list fails the same raw-pk
      coercion, and every request is the field-keyed invalid-relation ``FieldError``.

    So a relation override MUST keep BOTH the generated ``relay.GlobalID`` core AND its
    container shape (scalar for FK / OneToOne, one-level ``list`` for M2M); any
    divergence in core type or list depth is a fail-loud ``ConfigurationError``,
    caught at the bind rather than as a relation error on every request.

    Enforced at the phase-2.5 bind, NOT at class creation: whether the related model
    has a primary Relay-Node type is a ``registry.get`` lookup only reliably populated
    at finalization (this is exactly why ``_validate_input_class`` passes
    ``related_primary_type=None`` - the python-attr name is registry-independent, the
    id *type* is not). The expected shape is single-sourced with the generator by
    reading ``relation_input_annotation``'s emitted annotation (core via
    ``_annotation_core_is_global_id``, list depth via ``get_origin(...) is list``), so
    "GlobalID iff Relay-Node primary" and "list iff M2M" cannot drift from what
    ``build_mutation_input`` produces. A raw-pk relation (a non-Relay target)
    generates a raw pk input already, so there is no ``GlobalID`` decode to defeat
    and an override there is left alone.
    """
    # A validated ``@strawberry.input`` class: its definition slot holds an input definition.
    consumer_definition = require_instance(
        truth.static_attr(consumer_input, "__strawberry_definition__"),
        StrawberryObjectDefinition,
    )
    consumer_fields = {field.python_name: field for field in consumer_definition.fields}
    for field in shape.selected:
        if not getattr(field, "is_relation", False):
            continue
        python_attr, _graphql_name, annotation = relation_input_annotation(
            field,
            # A relation field's ``related_model`` is its resolved target model class.
            related_primary_type=registry.get(cast("type[models.Model]", field.related_model)),
        )
        if not _annotation_core_is_global_id(annotation):
            continue  # raw-pk relation (non-Relay target): no GlobalID decode to bypass.
        consumer_field = consumer_fields.get(python_attr)
        if consumer_field is None:
            continue  # not overridden; the generated GlobalID remainder is used.
        expected_depth = 1 if get_origin(annotation) is list else 0
        consumer_depth, consumer_core = _strawberry_field_shape(consumer_field)
        if consumer_core is not relay.GlobalID or consumer_depth != expected_depth:
            expected = "list[relay.GlobalID]" if expected_depth else "relay.GlobalID"
            kind = "M2M" if expected_depth else "forward FK/OneToOne"
            raise ConfigurationError(
                f"DjangoMutation {mutation_name}.Meta.{attr_name} overrides relation field "
                f"{python_attr!r} with an id type/shape that diverges from the generated input. "
                f"{truth.name(field.related_model)} has a primary Relay-Node type, so the {kind} "
                f"relation input is {expected} - type- and visibility-checked at decode (spec-036 "
                "Decision 10). A divergent core type would skip the GlobalID decode (the "
                "input would take raw pks where the schema takes GlobalIDs; visibility is "
                "still confirmed through the related primary type's get_queryset), and a "
                "divergent container shape would reject every id as an invalid relation. "
                f"Declare {python_attr!r} as {expected}.",
            )


def _annotation_core_is_global_id(annotation: object) -> bool:
    """Return whether a generated relation annotation's core id type is ``relay.GlobalID``.

    ``relation_input_annotation`` emits ``relay.GlobalID`` (forward FK / OneToOne) or
    ``list[relay.GlobalID]`` (M2M) for a Relay-Node-primary target, and the related
    model's raw pk scalar (or ``list[<scalar>]``) otherwise. This peels the M2M ``list``
    wrapper via ``utils/typing.py::unwrap_return_type`` (the shared one-layer list /
    Strawberry-list peeler) and compares the core against ``relay.GlobalID`` so both id
    shapes are recognized from the one generator-emitted annotation (no separate
    Relay-vs-pk re-derivation).
    """
    return unwrap_return_type(annotation) is relay.GlobalID


def _strawberry_field_shape(field: StrawberryField) -> tuple[int, object]:
    """Return a consumer field's ``(list_depth, core_type)``, peeling Strawberry wrappers.

    A consumer relation override resolves to nested ``StrawberryOptional`` /
    ``StrawberryList`` wrappers around a core type: ``relay.GlobalID | None`` is a
    ``StrawberryOptional(GlobalID)`` (depth 0), ``list[relay.GlobalID]`` is a
    ``StrawberryList(GlobalID)`` (depth 1), ``list[list[relay.GlobalID]]`` is depth 2.
    Optional wrappers are nullability (ignored for the shape); each ``StrawberryList``
    counts one level of list depth. Returning ``(depth, core)`` lets the shape-lock
    compare BOTH the core identity (``is relay.GlobalID``) and the list depth against
    the generated relation annotation, so a wrong core (``int`` / ``strawberry.ID``), a
    scalar-for-M2M, a list-for-FK, or a nested list are all caught.
    """
    type_ = field.type
    depth = 0
    seen: set[int] = set()
    while hasattr(type_, "of_type") and id(type_) not in seen:
        seen.add(id(type_))
        if isinstance(type_, StrawberryList):
            depth += 1
        # Read by name: the probe above admits any wrapper that carries ``of_type``.
        type_ = read_attr(type_, "of_type")
    return depth, type_


def bind_mutations() -> None:
    """Bind every registered ``DjangoMutation`` (the finalizer phase-2.5 entry point).

    The model-backed rider of ``bind_write_declarations``: each declaration's
    payload object type is its resolved primary ``DjangoType``
    (``_resolve_primary_type`` raises for no-primary / ambiguous), so the bind
    materializes the operation's input class (``create`` / ``update``) and the
    per-mutation ``<Name>Payload`` as module globals of ``mutations.inputs``
    before ``strawberry.Schema(...)`` runs.
    """
    bind_write_declarations(
        cache=_shape_build_cache,
        iterate=iter_mutations,
        resolve_object_type=lambda mutation_cls, meta: _resolve_primary_type(
            mutation_cls,
            backing_model_of(meta),
        ),
    )
