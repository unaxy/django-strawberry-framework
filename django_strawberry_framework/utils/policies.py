"""Shared schema-construction policy normalization.

``resource_policy.py::resolve_resource_policy`` and ``error_policy.py::
resolve_error_policy`` are deliberately the same shape - a consumer who has
learned how one schema-construction policy is configured has learned both -
so that shape lives here once: an explicit policy instance is used, an absent
one falls back to the configured setting and then to the fail-closed package
default, a non-mapping override is rejected, unknown keys are rejected naming the valid vocabulary, and
a mapping is applied over the dataclass defaults. A mapping override is read
once, through its own ``items()``, into a plain ``dict`` that validation and
construction both read, so they see the same keys even when the mapping is
stateful or one-shot; whatever the mapping's own iteration raises propagates as
the deployment's error. A value or key is classified by its real class, never a
``__class__`` read, so one whose ``__class__`` raises or lies still reaches the
typed rejection; a ``str`` subclass key is kept as the mapping holds it and
compared, sorted and passed to the constructor as itself. Domain validation stays with the policy
classes themselves (``__post_init__``), so an instance from any path was
validated on the same terms.
"""

from __future__ import annotations

from dataclasses import fields
from typing import TYPE_CHECKING, TypeVar

from django_strawberry_framework.exceptions import ConfigurationError

from . import introspection
from ._narrowing import is_real_instance, is_real_mapping, is_str

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from _typeshed import DataclassInstance

__all__ = ("resolve_policy",)

PolicyT = TypeVar("PolicyT", bound="DataclassInstance")


def _article(name: str) -> str:
    """Return the indefinite article for a class name: "an ErrorPolicy", "a ResourcePolicy"."""
    return "an" if name[0] in "AEIOU" else "a"


def resolve_policy(
    explicit: PolicyT | Mapping[str, object] | None,
    *,
    policy_cls: type[PolicyT],
    default: PolicyT,
    read_setting: Callable[[], object],
    display_name: str,
    unit: str,
) -> PolicyT:
    """Normalize one deployment policy the way every schema-construction policy resolves.

    Precedence, highest first: the ``explicit`` argument, the deployment value
    read through ``read_setting``, and ``default``. An instance from either
    override slot is returned as it is: its ``__post_init__`` validated it.

    ``display_name`` is the human name used in messages ("resource policy") and
    ``unit`` is what one override key is called there ("bound" / "option"); the
    wire-visible wording of both rejections is produced from these, so the two
    resolvers cannot drift apart in text any more than in behavior.

    Either override is recognised by its real class, never a ``__class__`` read,
    so a Django lazy proxy (``SimpleLazyObject``) of a policy or a mapping is the
    typed rejection below, like any other value of the wrong class.
    """
    if is_real_instance(explicit, policy_cls):
        return explicit
    overrides = explicit if explicit is not None else read_setting()
    if overrides is None:
        return default
    if is_real_instance(overrides, policy_cls):
        # An instance behind the SETTING slot is the same declaration the
        # explicit argument accepts: one ladder with two spellings.
        return overrides
    # The mapping protocol is asked of the real class, so a value whose
    # ``__class__`` raises or lies is the typed rejection below, never its own error.
    if not is_real_mapping(overrides):
        raise ConfigurationError(
            f"The {display_name} must be {_article(introspection.name(policy_cls))} "
            f"{introspection.name(policy_cls)} or a mapping of {unit} names to values; "
            f"got {introspection.describe(overrides)}.",
        )
    named: dict[str, object] = {}
    for name, value in overrides.items():
        # A key is a name only if its real class is ``str``, so a lazy proxy
        # key is the typed rejection, not a bare ``TypeError`` from ``sorted()``.
        if not is_str(name):
            raise ConfigurationError(
                f"The {display_name} {unit} names must be strings; got {introspection.describe(name)}.",
            )
        named[name] = value
    known = {field.name for field in fields(policy_cls)}
    unknown = sorted(name for name in named if name not in known)
    if unknown:
        raise ConfigurationError(
            f"Unknown {display_name.replace(' ', '-')} {unit}(s): {', '.join(unknown)}. "
            f"Valid {unit}s: {', '.join(sorted(known))}.",
        )
    return policy_cls(**named)
