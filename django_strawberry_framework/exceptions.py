"""Exceptions raised by django-strawberry-framework.

Lives at the bottom of the import graph - no Django, no Strawberry, and from
the package only ``utils/truth.py`` (which imports nothing) - so the exception
hierarchy can be raised from anywhere without circulars. ``truth`` is imported
where a message is built, not at module scope: importing it runs the ``utils``
package, whose modules import this one.
"""

from __future__ import annotations

from typing_extensions import override

__all__ = (
    "ConfigurationError",
    "DjangoStrawberryFrameworkError",
    "LookupValidationError",
    "OptimizerError",
    "PathResolutionError",
)


class DjangoStrawberryFrameworkError(Exception):
    """Base exception for the package.

    Consumers can catch this to handle any framework-raised error in a
    single ``except``. Specific subclasses below distinguish causes when
    granular handling is needed.

    Rendering is the standard ``Exception`` behaviour. Every message the
    framework raises is built as an exact ``str`` at the raise site, from
    truthful renders (``utils/truth.py``), so ``str`` / ``repr`` of a
    framework-raised error never runs consumer code. A consumer that raises one
    of these with its own object as the message gets that object's own
    ``__str__`` / ``__repr__``, exactly as with any other exception.
    """


class ConfigurationError(DjangoStrawberryFrameworkError):
    """Raised when consumer configuration is invalid or inconsistent.

    Covers type-creation / finalization Meta validation, settings reads,
    registry collisions, filter/order/mutation set wiring, and other
    configuration-time failures. Examples:

        - Missing ``Meta.model``.
        - ``fields`` and ``exclude`` declared together.
        - A deferred-surface key (``aggregate_class``, ``fields_class``,
          ``search_fields``) declared before the feature that owns it has
          shipped.
        - A second ``DjangoType`` claiming ``Meta.primary`` for a model that
          already has one, or a ``primary`` flag flipped on re-register.
          Registering several types against one model is supported; only the
          ambiguity raises.
        - Several ``DjangoType`` subclasses for one model with none declared
          primary, which ``types/finalizer.py`` detects at finalization
          rather than at registration.
        - A non-mapping ``DJANGO_STRAWBERRY_FRAMEWORK`` settings value.

    ``SyncMisuseError`` (defined in ``utils/querysets.py``, re-exported at
    the package root) multiple-inherits this class and ``RuntimeError`` for
    async-hook-from-sync misuse.
    """


def _model_label(model: object) -> str:
    """Return ``app_label.ModelName`` for a Django model, or the value's kind for anything else.

    ``_meta`` is read from the real namespaces (``truth.static_attr``), so a
    consumer class cannot answer it through a metaclass hook; the ``label`` it
    holds is Django's own ``Options`` property.
    """
    from .utils import truth  # noqa: PLC0415 - import cycle

    meta = truth.static_attr(model, "_meta")
    label = None if meta is None else getattr(meta, "label", None)
    if truth.is_instance(label, str):
        return truth.text(label, fallback=truth.kind(model))
    return truth.kind(model)


def _terminal_label(terminal: object) -> str:
    """Return a Django field's ``name``, or the value's kind for anything else."""
    from .utils import truth  # noqa: PLC0415 - import cycle

    name = getattr(terminal, "name", None)
    if truth.is_instance(name, str):
        return truth.text(name, fallback=truth.kind(terminal))
    return truth.kind(terminal)


class PathResolutionError(ConfigurationError):
    """Raised when a model-field path cannot be strictly classified.

    Subclasses ``ConfigurationError`` (not ``OptimizerError``): a path that
    fails strict classification is a definition-time defect in a
    framework-generated or consumer-declared traversal, not a runtime planning
    failure - it belongs to the same configuration/definition family as a
    malformed ``Meta`` declaration, and remains catchable through the package
    base and through ``ConfigurationError``.

    The single named error for strict path classification. Distinct from the
    lenient boolean ``utils/relations.py::path_traverses_to_many`` walk (which
    answers a ``PathResolutionError`` from the lenient walk - ``True``
    once a many-side hop precedes the failure, ``False`` otherwise) so strict
    callers never turn a malformed declaration into a lenient answer by
    accident.

    Raise sites (all in ``utils/relations.py::classify_path``):

        - A segment that ``Model._meta.get_field`` rejects (``FieldDoesNotExist``),
          including a hidden reverse relation declared ``related_name="+"``.
        - A non-relation (scalar) segment that is NOT the final segment - the
          path continues past a column that cannot be traversed.
        - A forward ``GenericForeignKey`` segment (``is_relation=True`` but no
          ``path_infos``), whether terminal or mid-path - it is neither a
          scalar terminal nor a traversable relation.
        - A relation segment whose ``path_infos`` is empty.
        - Guard arms the segment list above does not name: a ``field_path``
          that is not a ``str`` (raised before segmentation, naming the whole
          value as the segment), and a segment whose ``is_relation`` flag
          ``utils/relations.py::relation_bool`` rejects as malformed metadata.

    The message always names the model label, the complete declared path, and
    the offending segment so the failure is actionable.
    """

    def __init__(
        self,
        model: object,
        field_path: str,
        segment: str,
    ) -> None:
        """Build the message from the unclassifiable ``segment`` of ``field_path`` on ``model``."""
        from .utils import truth  # noqa: PLC0415 - import cycle

        super().__init__(
            f"Cannot classify path {truth.render(field_path)} on model {_model_label(model)}: "
            f"segment {truth.render(segment)} is not a traversable model-field relation.",
        )
        self.model: object = model
        self.field_path: str = field_path
        self.segment: str = segment

    @override
    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (
            type(self),
            (self.model, self.field_path, self.segment),
            vars(self),  # truth: ok the exception's own pickle state, read by its own __reduce__
        )


class LookupValidationError(ConfigurationError):
    """Raised when a django-filter lookup expression is invalid for a terminal.

    Distinct from ``PathResolutionError``: path classification and lookup
    validation are separate contracts, so a caller can tell "the relation path
    does not resolve" apart from "the path resolves but this transform/lookup
    is not available on its output field". Both are configuration-family
    (subclass ``ConfigurationError``), catchable through the package base.

    Raised by ``utils/relations.py::validate_lookup_expr`` when:

        - ``lookup_expr`` is empty, or splitting it on ``LOOKUP_SEP`` yields an
          empty part (e.g. ``"date__"`` or a leading ``"__"``).
        - A non-final part does not resolve as a transform on the current
          output field (``get_transform`` returns ``None``).
        - The final part resolves as neither a lookup (``get_lookup``) nor a
          trailing transform whose output supports the implicit ``exact``.
        - Guard arms the list above does not name: a ``lookup_expr`` that is
          not a ``str`` (raised before splitting), and a chain Django refuses
          with ``FieldError`` (e.g. a transform applied to a bare field with no
          output field yet), converted to this error.

    The message names the terminal field, the full ``lookup_expr``, and the
    offending part so the failure is actionable.
    """

    def __init__(
        self,
        terminal: object,
        lookup_expr: str,
        part: str,
    ) -> None:
        """Build the message from the invalid ``part`` of ``lookup_expr`` for ``terminal``."""
        from .utils import truth  # noqa: PLC0415 - import cycle

        super().__init__(
            f"Invalid lookup expression {truth.render(lookup_expr)} for terminal "
            f"{_terminal_label(terminal)}: part {truth.render(part)} is not a valid transform "
            "or lookup.",
        )
        self.terminal: object = terminal
        self.lookup_expr: str = lookup_expr
        self.part: str = part

    @override
    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (
            type(self),
            (self.terminal, self.lookup_expr, self.part),
            vars(self),  # truth: ok the exception's own pickle state, read by its own __reduce__
        )


class OptimizerError(DjangoStrawberryFrameworkError):
    """Raised when ``DjangoOptimizerExtension`` cannot plan a relation traversal.

    Raise sites:

        - Typed input-guard at stamp time: ``FieldMeta.from_django_field``
          rejects an input that is not a Django field descriptor (missing
          ``name`` / ``is_relation``), converting a malformed descriptor
          into a typed failure at ``DjangoType`` construction or the
          walker's unregistered fallback map-build rather than a late
          ``AttributeError`` mid-walk.
        - Strictness-``"raise"`` N+1 guard: fires when optimizer
          ``strictness`` is ``"raise"`` and a request reaches an unplanned
          relation that would lazy-load. Covers both the list-relation
          resolver and the nested-connection window-partition path (a
          single-valued forward relation or any kind without a windowable
          parent partition).
        - Window fetch-mode contract: ``utils/connections.py::
          assert_window_fetch_mode`` rejects a window that engages the
          count-free ``hasNextPage`` probe while also annotating the partition
          count (a planner/strategy bug that would otherwise pass the n+1
          sentinel through as a real edge).
        - Window bounds: ``utils/connections.py::window_range_plan`` rejects
          a negative offset or limit on a direct window request.
        - Reversed keyset window: ``optimizer/plans.py::apply_window_pagination``
          rejects a keyset-seek window that is also reversed, since backward
          keyset pagination resolves through the per-parent/root slicer, never a
          reversed window plan.
        - Backward-window order reversal: ``optimizer/plans.py::_reverse_order_by``
          rejects an order entry with neither a ``descending`` flag nor a
          callable ``desc()``, since a backward (``last``-only) window cannot be
          expressed for it.
        - Row-preserving predicate attachment
          (``optimizer/predicates.py::attach_exists``): the three runtime
          caller-contract guards - inner-queryset model does not match the outer
          model, inner and outer resolve to different database aliases, or the
          outer queryset carries a combinator (union / intersection /
          difference) that a reserved existence alias cannot attach to.
        - Hooked relation without resolve info
          (``optimizer/walker.py::_hook_info``): a direct walk planned with no
          operation's resolve info reaches a relation whose target declares
          ``get_queryset``, which receives ``strawberry.Info`` and never ``None``.
    """
