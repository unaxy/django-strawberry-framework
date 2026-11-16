"""``ErrorPolicy`` - what an unexpected exception says to a client in production.

Spec: ``docs/SPECS/spec-048-secure_output_defaults-0_0_14.md``.

graphql-core's default is to put an unhandled resolver or hook exception's
literal message into the response. That is the right default for a development
schema and the wrong one for a deployment: the message is written by whatever
raised it, which is frequently a library that had no idea it was addressing an
untrusted reader. A deployment does not become safe by remembering to install a
masking extension, so the package's required schema class installs a policy
instead.

The policy is deliberately narrow. It answers one question - *what does an
UNEXPECTED exception look like on the wire* - and nothing else:

- **The classification is structural, not a curated list.** A framework
  rejection is raised as a ``GraphQLError``; those are deliberate, audited,
  client-facing statements and travel unchanged. A parse or validation error has
  no originating exception at all and likewise travels unchanged. Everything
  else is an exception that reached the wire by accident, and only those are
  masked. A curated allowlist of error codes would have to be extended by every
  future rejection site and would fail OPEN the day someone forgot; this rule
  fails CLOSED for every new plain-Python exception.
- **The correlation identifier is the whole point.** Masking that only deletes
  information trades a disclosure for an unsupportable deployment. Each masked
  error carries a fresh ``uuid4().hex``, published to the client in the error's
  ``extensions`` and logged server-side alongside the original exception and its
  traceback, so an operator can resolve a user's complaint to one exception.
- **Development is untouched.** Under ``settings.DEBUG`` the policy is a
  pass-through; the local traceback is the reason the setting exists.

Resolved once at schema construction (``schema.py::DjangoSchema``) through
``resolve_error_policy``, exactly as the resource policy is: an invalid
deployment fails at startup rather than on a request, and no resolver re-reads
a setting.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .conf import error_policy_setting
from .exceptions import ConfigurationError
from .utils import introspection
from .utils._narrowing import read_attr
from .utils.policies import resolve_policy

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = (
    "DEFAULT_ERROR_POLICY",
    "ErrorPolicy",
    "new_correlation_id",
    "resolve_error_policy",
)


@dataclass(frozen=True)
class ErrorPolicy:
    """The immutable production error policy for one schema.

    ``enabled``
        Whether unexpected exceptions are masked at all. ``True`` by default -
        the whole point of the policy is that safety is not opt-in. A consumer
        who owns their own masking sets it ``False`` explicitly, which is a
        recorded decision rather than an omission.

    ``message``
        The single stable string every masked error carries. It interpolates
        nothing from the original exception by construction: a message that
        embeds any part of what it is masking is not a mask.

    ``correlation_extension_key``
        The key the correlation identifier is published under in the GraphQL
        error's ``extensions`` map. Configurable because a deployment with an
        existing error contract may already have a name for this field.

    ``schema.error_policy`` is read-only (``schema.py::DjangoSchema.error_policy``).
    """

    enabled: bool = True
    message: str = "An unexpected error occurred."
    correlation_extension_key: str = "correlationId"

    def __post_init__(self) -> None:
        """Reject a malformed policy at construction, naming the offending field.

        Every type test is EXACT, for the reason
        ``resource_policy.py::_require_positive_int`` states for a bound: a
        SUBCLASS is consumer code wearing a built-in's type, and every dunder the
        package then reaches for is that code. A ``str`` subclass stored as
        ``message`` is formatted into the masked error on the one path that
        exists to keep an untrusted reader from seeing anything the deployment
        did not choose, so a ``__str__`` / ``__format__`` hook there degrades the
        whole response instead of publishing the configured policy; one stored as
        ``correlation_extension_key`` is the key an operator's whole audit trail
        is looked up by. Admitting only the built-in types is what keeps the
        masking path on values the package owns.
        """
        if type(self.enabled) is not bool:
            raise ConfigurationError(
                f"ErrorPolicy.enabled must be a bool; got {introspection.describe(self.enabled)}.",
            )
        for name in ("message", "correlation_extension_key"):
            value = read_attr(self, name)
            if type(value) is not str or not value:
                raise ConfigurationError(
                    f"ErrorPolicy.{name} must be a non-empty string; got {introspection.describe(value)}.",
                )


#: The package default: masking on, a stable neutral message, the
#: ``correlationId`` extensions key. What a deployment gets by configuring
#: nothing, and the masking fallback of a schema that carries no policy.
DEFAULT_ERROR_POLICY = ErrorPolicy()


def resolve_error_policy(explicit: ErrorPolicy | Mapping[str, object] | None) -> ErrorPolicy:
    """Normalize the deployment's error policy once, at schema construction.

    Precedence, highest first: the ``DjangoSchema(error_policy=...)`` argument,
    the ``DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]`` mapping, and the package
    defaults. An ``ErrorPolicy`` instance from either override slot is used as
    it is, having validated itself at construction; a mapping from either source
    is applied over the package defaults so a deployment overrides only what it
    cares about.

    The structural twin of ``resource_policy.py::resolve_resource_policy`` -
    both delegate the shared resolution contract to
    ``utils/policies.py::resolve_policy``, because a consumer who has learned
    how one schema-construction policy is configured has learned both.
    """
    return resolve_policy(
        explicit,
        policy_cls=ErrorPolicy,
        default=DEFAULT_ERROR_POLICY,
        read_setting=error_policy_setting,
        display_name="error policy",
        unit="option",
    )


def new_correlation_id() -> str:
    """Return one fresh correlation identifier: 32 lowercase hexadecimal characters.

    ``uuid4().hex`` rather than a counter, a timestamp, or a request id: it is
    unique across processes and restarts without coordination, it carries no
    information about the deployment, and its format is fixed-width so a log
    grep for it cannot match anything else.

    One id is minted PER MASKED ERROR, not per operation. A response reporting
    two unrelated failures logs two exceptions, and a single shared id would
    make the log ambiguous exactly when an operator most needs it not to be.
    """
    return uuid.uuid4().hex
