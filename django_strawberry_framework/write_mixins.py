"""Lifecycle machinery shared by the write-flavor ``Mutation`` families.

The write-side twin of ``sets_mixins.py``. This module lives at the package root
so the model (``mutations/sets.py``), form (``forms/sets.py``) and serializer
(``rest_framework/sets.py``) flavors and the auth holders (``auth/mutations.py``)
import their shared class-creation and bind substrate from one neutral home
rather than from one flavor's module. Each flavor keeps its own declaration
ledger, metaclass instance, allowed-key set and bind entry point in its own
``sets.py``; only the mechanics they share live here:

- the ``Meta`` vocabulary and validation primitives each ``_validate_meta``
  composes (``COMMON_WRITE_META_KEYS`` / ``MODEL_BACKED_WRITE_META_KEYS``,
  ``normalize_meta_field_selection``, the ``require_*`` gates, ``_validate_permission_classes``,
  ``validate_select_for_update``, ``model_backed_permission_and_lock``);
- the validated ``Meta`` snapshot every flavor stashes
  (``_ValidatedMutationMeta``) and its readers (``backing_model_of`` /
  ``own_backing_class`` / ``resolve_meta_model`` /
  ``resolve_backed_model_or_raise``);
- the declaration-ledger and ``Meta``-validating metaclass factories
  (``make_declaration_registry`` / ``make_meta_validating_metaclass``);
- the resolver-seam factory (``resolver_seams`` / ``dispatch_resolver_entry``);
- the input build / stash helpers and the phase-2.5 drain
  (``cached_build_input`` / ``build_and_stash_input`` / ``construction_kwargs`` /
  ``bind_write_declarations`` / ``bind_mutation_outputs``).

The ``Meta``-key typo guard each ``_validate_meta`` opens with
(``utils/inputs.py::reject_unknown_meta_keys``) is not here: the set
metaclasses run it too, so it lives in the module both families import.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from django.db import models
from typing_extensions import override

from .exceptions import ConfigurationError
from .mutations.inputs import build_payload_type, materialize_mutation_input_class
from .mutations.operations import NON_DELETE_WRITE_OPERATIONS, non_delete_operation_error
from .mutations.permissions import DjangoModelPermission, is_permission_class
from .registry import registry
from .utils import truth
from .utils._narrowing import is_text_atom, list_of, optional_instance, read_attr, require
from .utils.imports import import_attr
from .utils.inputs import get_or_store_shape_build, normalize_field_name_sequence
from .utils.lazy import unwrap_lazy_object
from .utils.relations import is_model_class

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Protocol, TypeAlias

    from strawberry.types import Info
    from strawberry.types.base import WithStrawberryObjectDefinition

    from .forms.inputs import FormClass
    from .forms.sets import DjangoFormMutation
    from .mutations.permissions import WritePermissionClass
    from .mutations.sets import DjangoMutation
    from .rest_framework.inputs import NestedSerializerConfig
    from .rest_framework.serializer_converter import DRFSerializer
    from .types.base import DjangoType
    from .utils.inputs import InputFieldSpec

    # A shape-build cache key, and the per-flavor stash value a build answers
    # beside its input class (the form's ``field_specs`` list, the serializer shape).
    _KeyT = TypeVar("_KeyT")
    _PayloadT = TypeVar("_PayloadT")
    # The class ``require_subclass`` gates against.
    _ExpectedT = TypeVar("_ExpectedT")
    #: One ``resolver_seams`` classmethod: a resolver seam of any signature.
    _SeamClassmethod: TypeAlias = classmethod[object, ..., object]
else:
    # ``classmethod`` has no ``__class_getitem__`` before Python 3.14: the hint stays the class.
    _SeamClassmethod = classmethod

#: Common Meta keys accepted by every write-flavor Mutation.Meta (fields, exclude, permission_classes).
COMMON_WRITE_META_KEYS: frozenset[str] = frozenset(
    {"fields", "exclude", "permission_classes"},
)

#: Common Meta keys accepted by every model-backed write-flavor Mutation.Meta
#: (DjangoMutation, ModelForm, Serializer).
MODEL_BACKED_WRITE_META_KEYS: frozenset[str] = COMMON_WRITE_META_KEYS | frozenset(
    {"operation", "select_for_update"},
)


def require_non_delete_operation(base_label: str, name: str, meta: type[object]) -> str:
    """Return ``Meta.operation`` if it is create/update, else raise the shared reject.

    The getattr + membership check both model-backed form and serializer
    ``_validate_meta`` share after their type-gates. The error body is
    ``non_delete_operation_error``; this owns the lookup so a new non-delete
    verb cannot leave one flavor still spelling the membership test. The
    model-less plain form does NOT call this (it rejects ANY ``operation`` key).
    """
    raw_operation = truth.static_attr(meta, "operation")
    if (
        not truth.is_instance(raw_operation, str)
        or (operation := truth.text(raw_operation)) not in NON_DELETE_WRITE_OPERATIONS
    ):
        raise non_delete_operation_error(base_label, name, raw_operation)
    return operation


def normalize_meta_field_selection(
    meta: type[object],
    *,
    flavor: str,
) -> tuple[tuple[str, ...] | None, tuple[str, ...] | None]:
    """Return ``(fields, exclude)`` after the shared sequence-shape normalize.

    Every write-flavor ``_validate_meta`` runs this pair so a new flavor cannot
    normalize one key and forget the other (the serializer flavor included -
    ``rest_framework/sets.py`` materializes its selectors at class creation and
    re-normalizes inside ``resolve_effective_serializer_fields`` at the bind).
    Existence / mutual-exclusion / empty-set checks stay at the
    caller: the model flavor's delete-inapplicable rule and the form flavor's
    ``resolve_effective_form_fields`` walk are different jobs.
    """
    fields = normalize_field_name_sequence(
        truth.static_attr(meta, "fields"),
        label="fields",
        flavor=flavor,
        ordered=True,
    )
    exclude = normalize_field_name_sequence(
        truth.static_attr(meta, "exclude"),
        label="exclude",
        flavor=flavor,
        ordered=False,
    )
    return fields, exclude


def cached_build_input(
    cache: dict[_KeyT, tuple[type[object], _PayloadT]],
    shape_key: _KeyT,
    *,
    guard: Callable[[], None],
    build_fn: Callable[[], tuple[type[object], _PayloadT]],
) -> tuple[type[object], _PayloadT]:
    """Run the per-declaration guard, THEN the per-shape cache lookup.

    The shared guard-before-cache-lookup core for flavors whose cache key is
    known BEFORE the build (today: the form ``build_input`` seam). The
    load-bearing ordering (spec-038 Decision 7 / spec-039 Decision 7): the
    create-required-narrowing ``guard`` runs PER declaration, BEFORE the
    per-shape cache lookup, so a waiving mutation (guard a no-op, having
    overridden the construction hook) that materializes a narrowed shape FIRST
    cannot suppress the guard for a later non-waiving mutation reusing the
    cached shape - the cache key (``shape_key``) excludes the waiver, so the
    guard is tied to the declaration, not the built shape.

    The get-or-store itself rides ``utils/inputs.py::get_or_store_shape_build``
    (the same spine serializer ``dedupe_serializer_input_shape`` uses after
    its walk). The serializer flavor deliberately does NOT call this helper:
    its cache key is the post-build ``SerializerInputShape`` descriptor, so
    ``rest_framework/sets.py`` preserves the same guard-before-dedupe
    discipline inline. The materialize-then-stash tail both flavors still
    share is ``build_and_stash_input``.

    On a cache miss ``build_fn()`` returns ``(input_cls, payload)`` where
    ``payload`` is the per-flavor stash value (the form's ``field_specs``
    list). ``cache`` is the FLAVOR's own per-pass ``make_shape_build_cache()``
    dict (passed in, not owned here) so the mutation / form caches stay
    disjoint - each is registered + cleared separately.
    """
    guard()
    return get_or_store_shape_build(cache, shape_key, build_fn)


def build_and_stash_input(
    cls: WriteMutationClass,
    *,
    build: Callable[[], tuple[type[object], _PayloadT]],
    materialize: Callable[[str, type[object], str], None],
    specs_of: Callable[[_PayloadT], list[InputFieldSpec]],
) -> type[object]:
    """Materialize a built input + stash its reverse map on the mutation.

    The materialize-then-stash tail the form + serializer ``build_input`` seams
    share: ``build()`` returns ``(input_cls, payload)`` (the per-flavor stash value),
    ``materialize(truth.name(input_cls), input_cls, owner)`` pins it as a module global
    of the flavor's input namespace (``owner`` names ``cls`` for the cross-family
    type-name claim's collision message), ``cls._input_field_specs = specs_of(payload)`` records
    the reverse map for the decode, and the class is returned.
    ``specs_of`` extracts the reverse-map specs from the per-flavor payload (the form
    payload IS the specs list - identity; the serializer payload is the shape, from
    which ``shape.field_specs`` is read), so the one tail serves both flavors.
    """
    input_cls, payload = build()
    materialize(truth.name(input_cls), input_cls, f"the input of {truth.label(cls)}")
    cls._input_field_specs = specs_of(payload)
    return input_cls


def construction_kwargs(
    *,
    instance: models.Model | None = None,
    **base: object,
) -> dict[str, object]:
    """Build a construction-hook kwargs dict, adding ``instance`` only when non-``None``.

    The default construction-kwargs hooks share the ``{...base...}`` +
    ``if instance is not None: kwargs["instance"] = instance`` shape: the form
    ``_default_get_form_kwargs`` passes ``base={"data": ..., "files": ...}``, the
    serializer ``get_serializer_kwargs`` passes ``base={"data": ...}``. Single-sites
    the "add ``instance`` only for update" clause (create / plain pass
    ``instance=None`` so no ``instance=`` key is emitted) so a new flavor's default
    hook reuses it rather than re-spelling the guard.
    """
    kwargs = dict(base)
    if instance is not None:
        kwargs["instance"] = instance
    return kwargs


def require_backing_class(
    name: str,
    meta: type[object],
    *,
    key: str,
    base_label: str,
    expected_label: str,
) -> object:
    """Return ``Meta.<key>`` or raise the shared "declares no backing class" error.

    The presence check both the form + serializer ``_validate_meta`` prologues share:
    an unset / ``None`` ``Meta.<key>`` (``form_class`` / ``serializer_class``) is a
    clean ``ConfigurationError`` naming the key + the expected base, never a
    downstream ``AttributeError`` on a missing class. ``base_label`` names the
    offending base (``DjangoModelFormMutation`` / ``DjangoFormMutation`` /
    ``SerializerMutation``); ``expected_label`` is the base type named in the message
    (``forms.ModelForm`` / ``forms.Form`` / ``serializers.ModelSerializer``). The
    per-flavor TYPE-gate is ``require_subclass`` (shared ``must be a <label>
    subclass; got <value>`` template + ``truth.render``); call it AFTER this
    presence check. The serializer's second, ModelSerializer-specific gate stays
    at that call site - its message names ``Meta.model``, not the shared
    subclass template. This helper owns only the shared presence clause.
    """
    backing: object = truth.static_attr(meta, key)
    if backing is None:
        raise ConfigurationError(
            f"{base_label} {name}.Meta declares no {key}; set Meta.{key} to a "
            f"{expected_label} subclass.",
        )
    return backing


def require_subclass(
    name: str,
    value: object,
    *,
    base_label: str,
    key: str,
    expected: type[_ExpectedT],
    expected_label: str,
    note: str = "",
) -> type[_ExpectedT]:
    """Return ``value`` if it is an ``expected`` subclass, else raise the shared type-gate.

    The ``must be a <expected_label> subclass; got <value>`` clause both form
    type-gates and the serializer ``Serializer`` gate share. Presence is
    ``require_backing_class`` (a missing key names the flavor's *contract* class,
    which can be narrower than this type-gate - serializer missing-key names
    ``ModelSerializer`` while this gate first names ``Serializer``). The subclass
    check reads the real MRO (``truth.is_subclass``). ``note`` is an optional second sentence
    (the ModelForm-vs-plain-Form redirect).
    """
    if truth.is_subclass(value, expected):
        return value
    message = (
        f"{base_label} {name}.Meta.{key} must be a {expected_label} subclass; "
        f"got {truth.render(value)}."
    )
    if note:
        message = f"{message} {note}"
    raise ConfigurationError(message)


def require_model_class(name: str, model: object, *, base_label: str) -> type[models.Model]:
    """Return ``model`` if it is a Django model class, else raise.

    The class-creation type-gate ``DjangoMutation._validate_meta`` runs after
    resolving ``Meta.model``. ModelForm / serializer ``_validate_meta``
    override the whole matrix and would otherwise skip this gate, so a
    non-model ``Meta.model`` would snapshot and crash at bind. One helper
    keeps the fail-loud on every model-backed flavor. ``base_label`` names
    the offending base so the model flavor's pinned
    ``DjangoMutation {name} resolved model must be a Django model class``
    message stays byte-identical.
    """
    if truth.is_subclass(model, models.Model):
        return model
    raise ConfigurationError(
        f"{base_label} {name} resolved model must be a Django model class; got {truth.render(model)}.",
    )


def backing_model_of(meta: _ValidatedMutationMeta) -> type[models.Model]:
    """Return a model-backed mutation snapshot's validated model.

    The snapshot's ``model`` slot is optional because the model-less form flavor
    (``DjangoFormMutation``) has none. Every model-backed flavor
    (``DjangoMutation``, ``DjangoModelFormMutation``, ``SerializerMutation``) gates
    it through ``require_model_class`` at class creation, so on their snapshots it
    is always a model class; a model-less snapshot here is a ``TypeError``.
    """
    return require(meta.model, is_model_class)


def own_backing_class(cls: type[object], key: str) -> object:
    """Return ``Meta.<key>`` from the class's OWN validated snapshot, else from its live ``Meta``.

    The no-argument discovery hooks (``get_form_fields`` / ``get_serializer_for_schema``)
    run inside ``_validate_meta``, before the metaclass stamps ``_mutation_meta``, where
    only the live declaration exists; every later call reads the frozen snapshot, so a
    post-declaration ``Meta`` edit cannot drift the shape. The snapshot is read from the
    class's own namespace, never up the MRO, where a subclass still validating would find
    its parent's. A class neither arm answers for raises ``ConfigurationError``.
    """
    meta = optional_instance(truth.class_dict(cls).get("_mutation_meta"), _ValidatedMutationMeta)
    backing = (
        truth.static_attr(truth.static_attr(cls, "Meta"), key)
        if meta is None
        else read_attr(meta, key)
    )
    if backing is None:
        raise ConfigurationError(f"{truth.name(cls)} cannot resolve Meta.{key}.")
    return backing


def resolve_meta_model(meta: type[object], *, key: str, meta_attr: str) -> object:
    """Resolve a backing class's ``Meta.model`` via the shared three-getattr chain.

    The ``meta.<key> -> backing.<meta_attr> -> backing_meta.model`` chain (each link a
    ``truth.static_attr`` read) both flavors' ``_resolve_model`` overrides walk, differing only
    in ``key`` (``form_class`` / ``serializer_class``) and ``meta_attr`` (a
    ``ModelForm``'s ``_meta`` vs a serializer's ``Meta``). Returns ``None`` for any
    missing link (no backing class, no meta, no model), so the caller's base
    validation raises the clean "resolves no model" error rather than an
    ``AttributeError``. Any other value is the consumer's declaration as written,
    which ``require_model_class`` type-gates.
    """
    backing = truth.static_attr(meta, key)
    backing_meta = truth.static_attr(backing, meta_attr)
    return truth.static_attr(backing_meta, "model")


def resolve_backed_model_or_raise(
    cls: type[DjangoMutation],
    meta: type[object],
    *,
    base_label: str,
    key: str,
    noun: str,
) -> type[models.Model]:
    """Return ``cls._resolve_model(meta)`` as a model class, or raise the shared errors.

    The no-model raise both flavors' ``_validate_meta`` share, run AFTER the backing
    class is type-validated (so ``Meta.<key>`` is a real class), then the
    ``require_model_class`` type-gate on a resolved value that is not a model class
    (a string / instance ``Meta.model``), so it cannot leak to bind.
    ``base_label`` / ``key`` / ``noun`` (``ModelForm`` / ``ModelSerializer``) are the
    only per-flavor axes; the messages are otherwise byte-identical across flavors.
    """
    model = cls._resolve_model(meta)
    if model is None:
        backing: object = truth.static_attr(meta, key)
        raise ConfigurationError(
            f"{base_label} {truth.name(cls)}.Meta.{key} {truth.name(backing)} resolves no model; "
            f"a {noun} must set Meta.model so the mutation has a model + a DjangoType to return.",
        )
    return require_model_class(truth.name(cls), model, base_label=base_label)


def resolver_seams(
    module_path: str,
    sync_name: str,
    async_name: str,
    *,
    with_id: bool = True,
) -> tuple[_SeamClassmethod, _SeamClassmethod]:
    """Build the ``(resolve_sync, resolve_async)`` classmethod pair a mutation base exposes.

    Every write-flavor base (``DjangoMutation`` / ``DjangoModelFormMutation`` /
    ``DjangoFormMutation`` / ``SerializerMutation``) exposes an identical
    ``resolve_sync`` / ``resolve_async`` seam: a function-local import of the flavor's
    resolver module (the cycle guard - the import runs at RESOLVE time, not class /
    module load) then a delegate to that module's entry with the GraphQL ``data`` /
    ``id`` kwargs. Single-sites the eight bodies as one factory: ``module_path`` is
    the flavor's resolver module, ``sync_name`` / ``async_name`` the entries it
    delegates to, and ``with_id`` is ``False`` for the model-LESS plain
    ``DjangoFormMutation`` (whose seam signature is ``(info, *, data)`` - no ``id``).

    Each call produces FRESH classmethod objects, so ``SubclassA.resolve_sync.__func__
    is BaseA.resolve_sync.__func__`` (inheritance) while ``BaseA.resolve_sync.__func__
    is not BaseB.resolve_sync.__func__`` (distinct factory calls) - the identities the
    field factory's routing tests assert. Assign the pair in the class body via
    ``resolve_sync, resolve_async = resolver_seams(...)`` so both land in the class
    ``__dict__``.
    """
    # Each shape is built in its own scope: the model-less pair has no ``id``, and
    # both pairs keep ``resolve_sync`` / ``resolve_async`` as their function names.
    if with_id:
        return _id_resolver_seams(module_path, sync_name, async_name)
    return _id_less_resolver_seams(module_path, sync_name, async_name)


def dispatch_resolver_entry(
    module_path: str,
    entry_name: str,
    cls: type[object],
    info: Info[object, object],
    /,
    **kwargs: object,
) -> object:
    """Call the flavor's resolver entry ``module_path.entry_name`` with the seam's arguments.

    The entry is imported by name at resolve time to break the import cycle between a
    flavor's ``sets`` and ``resolvers`` modules; its signature is the seam's
    (``(cls, info, *, data[, id])``).
    """
    entry = require(import_attr(module_path, entry_name), callable)
    return entry(cls, info, **kwargs)


def _id_resolver_seams(
    module_path: str,
    sync_name: str,
    async_name: str,
) -> tuple[_SeamClassmethod, _SeamClassmethod]:
    """Build ``resolver_seams``' ``(info, *, data, id)`` pair (every model-backed flavor)."""

    def resolve_sync(
        cls: type[object],
        info: Info[object, object],
        *,
        data: object,
        id: object,  # noqa: A002
    ) -> object:
        """Delegate to the flavor's sync resolver entry (function-local import cycle guard)."""
        return dispatch_resolver_entry(module_path, sync_name, cls, info, data=data, id=id)

    def resolve_async(
        cls: type[object],
        info: Info[object, object],
        *,
        data: object,
        id: object,  # noqa: A002
    ) -> object:
        """Delegate to the flavor's async resolver entry (function-local import cycle guard)."""
        return dispatch_resolver_entry(module_path, async_name, cls, info, data=data, id=id)

    return classmethod(resolve_sync), classmethod(resolve_async)


def _id_less_resolver_seams(
    module_path: str,
    sync_name: str,
    async_name: str,
) -> tuple[_SeamClassmethod, _SeamClassmethod]:
    """Build ``resolver_seams``' ``(info, *, data)`` pair (the model-less plain form)."""

    def resolve_sync(cls: type[object], info: Info[object, object], *, data: object) -> object:
        """Delegate to the flavor's sync resolver entry (no ``id`` - model-less flavor)."""
        return dispatch_resolver_entry(module_path, sync_name, cls, info, data=data)

    def resolve_async(cls: type[object], info: Info[object, object], *, data: object) -> object:
        """Delegate to the flavor's async resolver entry (no ``id`` - model-less flavor)."""
        return dispatch_resolver_entry(module_path, async_name, cls, info, data=data)

    return classmethod(resolve_sync), classmethod(resolve_async)


_DeclarationT = TypeVar("_DeclarationT")


@dataclass(frozen=True)
class DeclarationRegistry(Generic[_DeclarationT]):
    """The ``(register, clear, iter, store)`` quad ``make_declaration_registry`` returns.

    A flat named bundle (not a tuple of bare callables) so a caller assigns the
    three public functions to module-level names AND keeps a handle on the backing
    ``store`` list for the tests that introspect it directly (e.g. the
    ``_mutation_registry.count(...)`` idempotency assertion). ``register`` /
    ``clear`` / ``iter_`` carry the dedup / clear / snapshot mechanics; ``store``
    is the disjoint list they close over. Generic over the declaration class each
    ledger records (a frozen dataclass, not a ``NamedTuple``: a generic
    ``NamedTuple`` needs Python 3.11).
    """

    register: Callable[[_DeclarationT], None]
    clear: Callable[[], None]
    iter_: Callable[[], tuple[_DeclarationT, ...]]
    store: list[_DeclarationT]


def make_declaration_registry(label: str) -> DeclarationRegistry[_DeclarationT]:
    """Build a fresh declaration registry + its ``(register, clear, iter)`` callables.

    The Decision-13 shared-mechanics factory: given a human ``label``
    (``"DjangoMutation"`` / ``"DjangoFormMutation"``), create a private
    ``list[type]`` and return callables bound over it -

    - ``register`` records a class for the phase-2.5 bind, idempotent by identity
      (a class re-imported under a module reload is recorded once) and rejecting a
      declaration after ``registry.mark_finalized()`` / ``finalize_django_types()``
      (spec-036 Edge cases) - the bind has already run, so a late declaration would
      never be materialized; failing loud mirrors ``TypeRegistry._check_mutable``.
      ``label`` names the flavor in the reject message.
    - ``clear`` drops every recorded declaration (the ``registry.clear()`` co-clear
      hook) so a fresh finalize starts empty.
    - ``iter_`` returns every recorded declaration in registration order.

    The model flavor and the plain-form flavor (``forms/sets.py``) each instantiate
    this over their OWN list, so the dedup / reject / clear logic is single-sourced
    while the two ledgers stay disjoint (different ``bind_*`` bodies, different
    ``registry.clear()`` rows - the over-consolidation trap spec-038 Decision 13
    names is avoided by keeping the storage separate).
    """
    store: list[_DeclarationT] = []

    def register(declaration_cls: _DeclarationT) -> None:
        if registry.is_finalized():
            raise ConfigurationError(
                f"Cannot declare {label} {truth.name(declaration_cls)} after finalization; "
                "mutation declarations are import-time only (call registry.clear() first).",
            )
        # The ledger contract is idempotence by identity.
        if not truth.is_among(declaration_cls, store):
            store.append(declaration_cls)

    def clear() -> None:
        store.clear()

    def iter_() -> tuple[_DeclarationT, ...]:
        return tuple(store)

    return DeclarationRegistry(register=register, clear=clear, iter_=iter_, store=store)


def make_meta_validating_metaclass(
    register: Callable[[_DeclarationT], None],
    *,
    name: str,
    module: str,
) -> type[object]:
    """Build a metaclass that validates ``Meta`` and registers the concrete subclass.

    The Decision-13 twin of ``make_declaration_registry``: given a ``register``
    callable bound over a disjoint declaration ledger, return a ``type`` subclass
    whose ``__new__`` -

    - builds the class via ``super().__new__``;
    - skips when ``attrs`` has no nested ``Meta`` (the abstract / intermediate
      base guard the set metaclasses rely on);
    - else runs ``new_class._validate_meta(meta)``, stashes ``_mutation_meta``,
      and calls ``register(new_class)``.

    The produced metaclass also SEALS the class head: once a concrete
    subclass's validated snapshot is stashed, a later ``cls._mutation_meta = ...``
    statement (or ``del``) through the metaclass's own ``__setattr__`` /
    ``__delattr__`` raises ``ConfigurationError``. A
    ``has_permission`` hook receives the mutation class, so a plain attribute
    statement inside the hook could otherwise replace the validated record
    wholesale (an attacker-chosen namespace holding the empty allow-any posture)
    and authorize every later request - the same persistent cross-request
    bypass class the snapshot's own seal closes. The creation-time write in
    ``__new__`` is the one honored write; ordinary reassignment or deletion
    afterwards is refused. Unrelated class attributes (the bind's ``_primary_type`` /
    ``_input_class`` / ``_payload_type_name`` outputs) are unaffected.

    ``DjangoMutationMetaclass`` and ``DjangoFormMutationMetaclass`` are the two
    consumers (model ledger vs plain-form ledger). ``SerializerMutation`` /
    ``DjangoModelFormMutation`` ride the model metaclass via inheritance - no
    third Meta-validating twin. FilterSet / OrderSet metaclasses collect related
    declarations and are a different contract.

    ``name`` / ``module`` pin the returned class's identity to its public
    binding site: without them every produced metaclass would share the
    function-local ``make_meta_validating_metaclass.<locals>.MetaValidatingMetaclass``
    ``__qualname__`` (and a ``MetaValidatingMetaclass`` ``__name__``), which
    breaks module addressability, ``repr``/introspection, and reference-based
    pickling of the public metaclasses. Each consumer passes its own public
    symbol name and ``module=__name__`` so ``module + __qualname__`` resolves
    back to the bound object (the contract ``pickle`` requires for a class).
    """

    class MetaValidatingMetaclass(type):
        if TYPE_CHECKING:
            # Every class this metaclass builds declares the ``_validate_meta`` seam and
            # the ``_mutation_meta`` slot ``__new__`` fills from it.
            _mutation_meta: object

            def _validate_meta(cls, _meta: object, /) -> object: ...

        def __new__(
            cls: type[MetaValidatingMetaclass],
            name: str,
            bases: tuple[type[object], ...],
            attrs: dict[str, object],
        ) -> MetaValidatingMetaclass:
            """Build the class; for a concrete subclass, validate ``Meta`` and register it."""
            new_class = super().__new__(cls, name, bases, attrs)
            meta = attrs.get("Meta")
            if meta is None:
                return new_class
            new_class._mutation_meta = new_class._validate_meta(meta)
            # The class just built is the ledger's declaration class; neither checker
            # can tie this metaclass instance to the element type its ledger records.
            register(cast("_DeclarationT", new_class))
            return new_class

        @override
        def __setattr__(cls, name: str, value: object) -> None:
            """Refuse reassigning the validated ``Meta`` snapshot on a mutation class.

            The metaclass stashes ``_mutation_meta`` exactly once at class
            creation; a post-creation rebind of that head would swap the
            mutation's per-request authorization source for a hook-chosen record
            (the persistent bypass class ``_ValidatedMutationMeta``'s seal closes
            at the slot level). The write at class creation is honored; a later
            assignment through this ``__setattr__`` raises typed ``ConfigurationError``.
            """
            if name == "_mutation_meta" and "_mutation_meta" in truth.class_dict(cls):
                raise ConfigurationError(
                    f"{truth.name(cls)}._mutation_meta is sealed and cannot be rebound; the "
                    "validated authorization snapshot is captured once at class creation.",
                )
            super().__setattr__(name, value)

        @override
        def __delattr__(cls, name: str) -> None:
            """Refuse deleting the validated ``Meta`` snapshot off a mutation class."""
            if name == "_mutation_meta" and "_mutation_meta" in truth.class_dict(cls):
                raise ConfigurationError(
                    f"{truth.name(cls)}._mutation_meta is sealed and cannot be deleted; the "
                    "validated authorization snapshot is captured once at class creation.",
                )
            super().__delattr__(name)

    # Stores naming the framework's own freshly built metaclass, not reads of a consumer object.
    built = MetaValidatingMetaclass
    built.__name__ = name  # truth: ok framework-built class renamed at creation
    built.__qualname__ = name  # truth: ok framework-built class renamed at creation
    built.__module__ = module  # truth: ok framework-built class renamed at creation
    return MetaValidatingMetaclass


class _ValidatedMutationMeta:
    """The validated ``Meta`` snapshot the metaclass stashes on a concrete mutation.

    A flat record (not a dataclass, to stay dependency-light) the bind and the
    resolver read instead of re-walking the raw ``Meta``. Mirrors
    ``types/base.py::_ValidatedMeta`` in role: validation happens once at class
    creation, then every downstream reader trusts this snapshot.

    The snapshot is SEALED once ``__init__`` finishes: the record is the write
    side's per-request authorization source
    (``mutations/permissions.py::run_permission_classes`` reads
    ``type(self)._mutation_meta.permission_classes``), and a ``has_permission``
    hook runs INSIDE the walk with the mutation class in hand - a mutable slot
    would let one request's hook rebind the validated set (e.g. to the empty
    allow-any posture) for every later request: a persistent cross-request
    authorization bypass. Any attribute write or delete through the record's own
    ``__setattr__`` / ``__delattr__`` on a sealed snapshot raises
    ``ConfigurationError`` (a consumer who needs different authorization declares
    a new mutation class).
    """

    __slots__: tuple[str, ...] = (
        "_sealed",
        "exclude",
        "fields",
        "form_class",
        "injected_fields",
        "input_class",
        "model",
        "nested_fields",
        "operation",
        "optional_fields",
        "partial_input_class",
        "permission_classes",
        "schema_fingerprint",
        "select_for_update",
        "serializer_class",
    )

    def __init__(
        self,
        *,
        model: type[models.Model] | None,
        operation: str,
        input_class: type[WithStrawberryObjectDefinition] | None,
        partial_input_class: type[WithStrawberryObjectDefinition] | None,
        fields: tuple[str, ...] | None,
        exclude: tuple[str, ...] | None,
        permission_classes: tuple[WritePermissionClass, ...],
        form_class: FormClass | None = None,
        serializer_class: type[DRFSerializer] | None = None,
        optional_fields: tuple[str, ...] | None = None,
        schema_fingerprint: tuple[tuple[object, ...], ...] | None = None,
        injected_fields: tuple[str, ...] | None = None,
        select_for_update: bool = False,
        nested_fields: Mapping[str, NestedSerializerConfig] | None = None,
    ) -> None:
        self._sealed: bool = False
        self.model: type[models.Model] | None = model
        self.operation: str = operation
        self.input_class: type[WithStrawberryObjectDefinition] | None = input_class
        self.partial_input_class: type[WithStrawberryObjectDefinition] | None = partial_input_class
        self.fields: tuple[str, ...] | None = fields
        self.exclude: tuple[str, ...] | None = exclude
        self.permission_classes: tuple[WritePermissionClass, ...] = permission_classes
        # The form-flavor snapshot: a ``DjangoModelFormMutation``
        # / ``DjangoFormMutation`` records its ``Meta.form_class`` here so the form
        # ``build_input`` / resolver read one snapshot shape. The model flavor
        # leaves it ``None`` (it has no ``form_class``); the model path never
        # reads this slot.
        self.form_class: FormClass | None = form_class
        # The serializer-flavor snapshot: a ``SerializerMutation``
        # records its ``Meta.serializer_class`` here so the serializer ``build_input``
        # / resolver read one snapshot shape (mirroring ``form_class``). The model +
        # form flavors leave it ``None``; neither path reads it.
        self.serializer_class: type[DRFSerializer] | None = serializer_class
        # The serializer-flavor ``Meta.optional_fields``: the
        # create-only force-optional override lives on the MUTATION's ``Meta`` (the
        # documented public key), NOT the serializer's own ``Meta``. Normalized at
        # class creation and stored here as the validated tuple (``None`` when unset);
        # the serializer ``build_input`` threads it into
        # ``build_serializer_input_class`` so it participates in the input shape +
        # descriptor identity. The model + form flavors leave it ``None``.
        self.optional_fields: tuple[str, ...] | None = optional_fields
        # The serializer-flavor schema-hook fingerprint: a stable digest of
        # the ``get_serializer_for_schema()`` field shape captured at class validation, so the
        # phase-2.5 bind can raise on a NONDETERMINISTIC hook that drifted. The model + form
        # flavors leave it ``None``; neither path reads it.
        self.schema_fingerprint: tuple[tuple[object, ...], ...] | None = schema_fingerprint
        # The serializer-flavor ``Meta.injected_fields``: the auditable,
        # per-field replacement for the blanket ``get_serializer_kwargs``-override waiver -
        # names the required fields a ``get_serializer_kwargs`` override supplies into ``data``,
        # subtracted from the create-required guard AND verified present at runtime. The model +
        # form flavors leave it ``None``.
        self.injected_fields: tuple[str, ...] | None = injected_fields
        # ``Meta.select_for_update``: the
        # base-manager ``SELECT ... FOR UPDATE`` row lock on the update / delete
        # locate AND every relation-target check, constrained by the visibility pk
        # subquery inside the write transaction. Every model-backed flavor (model /
        # ``ModelForm`` / serializer) validates it via ``validate_select_for_update``
        # (default ``True``; an explicit ``False`` opts into weaker concurrency).
        # Only the model-less plain form leaves the constructor default (``False`` -
        # it locates no row).
        self.select_for_update: bool = select_for_update
        # The serializer-flavor ``Meta.nested_fields``: the explicit opt-in
        # ``{field_name: NestedSerializerConfig}`` map naming the nested serializer fields the
        # generated input builds RECURSIVELY (an un-named nested field fails loud). ``None`` when
        # no nesting is opted in. The model + form flavors leave it ``None``.
        self.nested_fields: Mapping[str, NestedSerializerConfig] | None = nested_fields
        # Seal LAST: every validated slot is set; from here on the record's own
        # ``__setattr__`` / ``__delattr__`` refuse reassignment and deletion.
        self._sealed = True

    @override
    def __setattr__(self, name: str, value: object) -> None:
        """Reject any attribute write on a sealed validated snapshot."""
        if getattr(self, "_sealed", False):
            raise ConfigurationError(
                f"The validated mutation Meta snapshot is sealed and {name!r} cannot be "
                "reassigned; authorization configuration is captured once at class creation.",
            )
        object.__setattr__(self, name, value)

    @override
    def __delattr__(self, name: str) -> None:
        raise ConfigurationError(
            "The validated mutation Meta snapshot is sealed; attributes cannot be deleted. "
            "Authorization configuration is captured once at class creation.",
        )


def _validate_permission_classes(
    site: str,
    value: object,
    *,
    unset_default: tuple[WritePermissionClass, ...] = (DjangoModelPermission,),
    model_less: bool = False,
) -> tuple[WritePermissionClass, ...]:
    """Validate + normalize a write surface's ``permission_classes`` at class creation.

    ``site`` opens every message and names where the value was declared: a
    ``Meta`` key on a declared class (``"DjangoFormMutation Submit.Meta.permission_classes"``)
    or an auth factory's keyword (``"login_mutation() permission_classes"``).

    An invalid ``permission_classes`` entry is rejected at
    class-creation, not deferred to a request-time ``TypeError`` /
    ``AttributeError`` inside ``DjangoMutation.check_permission`` (which does
    ``permission_class().has_permission(...)``). So:

    - ``None`` (unset) -> ``tuple(unset_default)``: the model-backed flavors keep
      the ``[DjangoModelPermission]`` default, while the model-less plain
      ``DjangoFormMutation`` passes ``unset_default=(DenyAll,)`` so an unset
      ``permission_classes`` denies rather than crashing in the model-permission
      default (spec-038 Decision 11 - there is no safe model-permission default
      without a model).
    - a bare text atom (``utils/_narrowing.py::is_text_atom``: a ``str``, a
      bytes-like value, or a lazy translation ``Promise`` - a single name; every
      ``Promise`` counts, so a ``lazy(..., list)`` value too; a ``SimpleLazyObject``
      is judged as the object it stands for) or a bare class (forgot the
      enclosing sequence) -> ``ConfigurationError``: the contract is a
      *sequence* of permission classes.
    - any other non-iterable -> ``ConfigurationError``.
    - each entry must be a **class exposing a callable ``has_permission``** (the
      shape ``check_permission`` instantiates + calls); an instance, a non-class
      value, or a class without ``has_permission`` -> ``ConfigurationError``
      naming the offending entry.
    - ``model_less=True`` (the plain ``DjangoFormMutation`` and the model-less
      auth fields ``login`` / ``logout`` / ``current_user``): an entry that is a
      ``DjangoModelPermission`` not overriding ``has_permission`` (the class
      itself or a subclass that inherits its hook) -> ``ConfigurationError``.
      That hook reads the model the mutation validated at declaration and maps
      the operation to an ``add`` / ``change`` / ``delete`` codename; a
      model-less surface has neither, so the class would raise per request
      instead of denying. A subclass overriding ``has_permission`` decides
      without the model and is admitted. What stays unguardable is code the
      class creation cannot read: an override that calls ``super()``, or any
      gate reading the mutation's model, still raises per request on a
      model-less surface.

    Returns the normalized IMMUTABLE tuple the snapshot stores, so the live
    authorization walk (``mutations/permissions.py::run_permission_classes``)
    can never be lengthened or emptied mid-request by a ``has_permission`` hook
    that mutates the class's list (a cleared live list short-circuits the walk
    to "all allowed" - an authorization bypass - and the emptied list would
    persist on the class, authorizing every later request). An explicit ``[]``
    is preserved as the documented allow-any opt-out for BOTH flavors (stored
    as the empty tuple).
    """
    if value is None:
        return tuple(unset_default)
    # A bare text atom, a bare class, or a value whose real class defines no
    # ``__iter__`` is not a sequence; iterating an accepted one is the value's own
    # behaviour.
    if (
        is_text_atom(unwrap_lazy_object(value))
        or truth.is_type(value)
        or truth.mro_attr(truth.class_of(value), "__iter__") is None
    ):
        raise ConfigurationError(
            f"{site} must be a sequence of permission classes; got {truth.render(value)}.",
        )
    classes = list_of(value)
    validated: list[WritePermissionClass] = []
    for entry in classes:
        if not is_permission_class(entry):
            raise ConfigurationError(
                f"{site} entry {truth.render(entry)} is not a permission class exposing "
                "has_permission; each entry must be a class with a "
                "has_permission(info, mutation, operation, data, instance) method.",
            )
        if (
            model_less
            and truth.is_subclass(entry, DjangoModelPermission)
            and not truth.overrides(entry, DjangoModelPermission, "has_permission")
        ):
            raise ConfigurationError(
                f"{site} includes {truth.name(entry)}, a DjangoModelPermission that does not "
                "override has_permission; it requires a model and this surface has none. "
                "Override has_permission without calling the base hook, omit permission_classes "
                "for this surface's "
                "default, or set [] to allow any.",
            )
        validated.append(entry)
    # The validated snapshot is stored IMMUTABLE: a mutable list reachable from
    # the mutation class could be emptied or reordered by a ``has_permission``
    # hook (which receives the mutation class), turning deny-closed into the
    # allow-any posture for every later request. The walk reads this snapshot.
    return tuple(validated)


def validate_select_for_update(flavor: str, mutation_name: str, meta: type[object]) -> bool:
    """Validate ``Meta.select_for_update`` for a model-backed flavor.

    Every model-backed write flavor (model / ``ModelForm`` / serializer) shares
    this ONE validator so the key's contract cannot drift: the update / delete
    locate and every relation-target check acquire a base-manager ``SELECT ...
    FOR UPDATE`` (constrained by the visibility pk subquery) inside the write
    transaction. The default is ``True`` - locked writes are the safe posture;
    an explicit ``False`` opts into weaker concurrency: a row located this
    transaction may be concurrently modified or deleted instead of waiting on the
    lock, and a deleted one surfaces as the in-band ``conflict`` envelope on every
    flavor, never re-INSERTed by the update on any table a multi-table row spans
    (``mutations/resolvers.py::save_located_row``; the serializer flavor through
    its write witness), and never answered by a field error its decode or
    validation reached first (``mutations/resolvers.py::run_write_pipeline_sync``
    probes the located row on a step failure). On a backend without
    ``FOR UPDATE`` (sqlite) Django skips the clause silently, so ``True`` is
    safe to leave in place regardless of backend. A non-bool is a clear
    class-creation error.
    """
    select_for_update = truth.static_attr(meta, "select_for_update", default=True)
    if not truth.is_instance(select_for_update, bool):
        raise ConfigurationError(
            f"{flavor} {mutation_name}.Meta.select_for_update must be a bool; got "
            f"{truth.render(select_for_update)}.",
        )
    return select_for_update


def model_backed_permission_and_lock(
    name: str,
    meta: type[object],
    *,
    flavor: str,
) -> tuple[tuple[WritePermissionClass, ...], bool]:
    """Return ``(permission_classes, select_for_update)`` for a model-backed write flavor.

    Every model-backed ``_validate_meta`` (model / ModelForm) pairs the
    ``DjangoModelPermission`` default with the ``FOR UPDATE`` lock validator.
    The model-less plain form does NOT call this (DenyAll default, no row to
    lock, plus the ``model_less`` model-permission reject). The serializer flavor
    interleaves other Meta keys between the lock and the permission walk, so
    it keeps calling the two primitives in that order rather than this pair.
    """
    permission_classes = _validate_permission_classes(
        f"{flavor} {name}.Meta.permission_classes",
        truth.static_attr(meta, "permission_classes"),
    )
    return permission_classes, validate_select_for_update(flavor, name, meta)


if TYPE_CHECKING:
    # A write-mutation declaration class of either ledger: the model-backed
    # ``DjangoMutation`` family (model / ``ModelForm`` / serializer) or the
    # model-less ``DjangoFormMutation``.
    WriteMutationClass: TypeAlias = type[DjangoMutation | DjangoFormMutation]

    # The payload object type one ledger's drain resolves: the primary
    # ``DjangoType`` for the model-backed ledger, ``None`` for the model-less one.
    _ObjectTypeT = TypeVar("_ObjectTypeT", bound="type[DjangoType] | None")
    _ObjectTypeT_co = TypeVar(
        "_ObjectTypeT_co",
        bound="type[DjangoType] | None",
        covariant=True,
    )

    class _BindTarget(Protocol[_ObjectTypeT_co]):
        """A declaration class as ``bind_mutation_outputs`` stashes the bind outputs on it.

        ``_primary_type`` holds the payload's object type: the primary
        ``DjangoType`` on the model-backed ledger, ``None`` on the model-less one.
        """

        __name__: str
        _primary_type: _ObjectTypeT_co
        _input_class: type[object] | None
        _payload_type_name: str

    class _BoundDeclaration(_BindTarget[_ObjectTypeT], Protocol[_ObjectTypeT]):
        """A registered declaration as the phase-2.5 drain reads and stashes it.

        Registration follows the metaclass's validated-snapshot stash, so
        ``_mutation_meta`` is always set; ``build_input`` accepts exactly the
        object type its own ledger's ``resolve_object_type`` answers.
        """

        _mutation_meta: _ValidatedMutationMeta

        def build_input(
            self,
            meta: _ValidatedMutationMeta,
            primary_type: _ObjectTypeT,
        ) -> type[object] | None:
            """Build + materialize the operation's input class; ``None`` when it takes none."""


def bind_mutation_outputs(
    mutation_cls: _BindTarget[_ObjectTypeT],
    *,
    input_cls: type[object] | None,
    object_type: _ObjectTypeT,
) -> None:
    """Build the payload, materialize it, and stash bind outputs on ``mutation_cls``.

    The payload half of the phase-2.5 bind (the input half is the flavor's
    ``build_input`` seam; the input twin is ``build_and_stash_input``). Both
    declaration ledgers write the same three slots ``DjangoMutationField``
    reads after finalize (``_primary_type`` / ``_input_class`` /
    ``_payload_type_name``):

    - model-backed (``bind_mutations``): ``object_type`` is the resolved
      primary ``DjangoType``; the payload carries ``payload_object_slot``;
    - model-less (``bind_form_mutations``): ``object_type`` is ``None`` and
      the payload is the pinned ``{ ok errors }`` shape.

    Auth's login/logout holders use a fixed payload *name* (``"Login"`` /
    ``"Logout"``) rather than the mutation class's name and do not stash
    ``_input_class``, so they stay local. Payload classes ride the SAME
    ``materialize_mutation_input_class`` ledger as the input classes (one
    ledger, one collision check, one ``registry.clear()`` co-clear).
    """
    payload_cls = build_payload_type(
        truth.name(mutation_cls),
        object_type=object_type,
    )
    materialize_mutation_input_class(truth.name(payload_cls), payload_cls)
    mutation_cls._primary_type = object_type
    mutation_cls._input_class = input_cls
    mutation_cls._payload_type_name = truth.name(payload_cls)


def bind_write_declarations(
    *,
    cache: dict[_KeyT, _PayloadT],
    iterate: Callable[[], tuple[_BoundDeclaration[_ObjectTypeT], ...]],
    resolve_object_type: Callable[
        [_BoundDeclaration[_ObjectTypeT], _ValidatedMutationMeta],
        _ObjectTypeT,
    ],
) -> None:
    """Drain one write-declaration registry through the phase-2.5 bind.

    The ONE drain both write-declaration ledgers ride - the model-backed
    ``bind_mutations()`` (which the ``ModelForm`` and serializer flavors ride
    too, being ``DjangoMutation`` subclasses) and the model-less
    ``bind_form_mutations()``. ``finalize_django_types`` calls each in the
    phase-2.5 window, after primary-type state is settled and before
    ``strawberry.type(...)`` freezes the schema classes (spec-036 Decision 12).

    Per registered class: resolve the payload's object type, route the input
    materialization through the ``build_input`` seam (spec-038 Decision 13 - the
    model flavor rebuilds the model-column input, the form / serializer flavors
    build their own), and stash both through ``bind_mutation_outputs``.

    ``resolve_object_type`` is the ONLY per-ledger divergence: the model-backed
    drain resolves the primary ``DjangoType`` (raising for no-primary /
    ambiguous), the model-less drain answers ``None`` (which selects the pinned
    ``{ ok errors }`` payload and keeps ``_primary_type`` ``None``). Every
    flavor's ``build_input`` carries the same ``(meta, primary_type)`` signature
    so this one call reaches all of them.

    ``cache`` is the caller's own PER-PASS build cache, cleared at the top so
    each input is rebuilt fresh. The cross-pass materialization ledgers
    (``mutations.inputs`` / ``forms.inputs`` - the ``ModelForm`` flavor rides
    the model pass but writes the FORM ledger) are reset ONCE by
    ``finalize_django_types`` before the bind sequence so a recover-in-place
    re-finalize is retry-idempotent; they are NOT reset here, where a per-pass
    clear would wipe the sibling pass's already-materialized entries.
    """
    cache.clear()
    for mutation_cls in iterate():
        meta = mutation_cls._mutation_meta
        object_type = resolve_object_type(mutation_cls, meta)
        bind_mutation_outputs(
            mutation_cls,
            input_cls=mutation_cls.build_input(meta, object_type),
            object_type=object_type,
        )
