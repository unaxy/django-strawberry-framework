"""The frozen serializer-hook context.

The consumer hooks (``get_serializer_kwargs`` / ``get_serializer_injected_data`` /
``get_serializer_save_kwargs``) never receive the LIVE located model instance:
a mutable target in consumer hands before the write is an attack surface (an
override could ``setattr`` unvalidated values that ``serializer.save()`` then
persists, or re-point ``pk`` at a row the caller was never authorized for). They
receive this frozen ``SerializerHookContext`` instead - the operation kind, the
pinned write alias, and the authorized target's pk snapshot - everything the
documented use cases (branching create-vs-update, routing an extra query into the
transaction, keying server data to the target row) actually need, with nothing
mutable. A hook that needs more of the row reads it itself through the pinned
alias (a visible, auditable query) rather than through a privileged live object.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerializerHookContext:
    """The immutable context every serializer consumer hook receives.

    - ``operation`` - ``"create"`` or ``"update"`` (the mutation's declared kind).
    - ``write_alias`` - the pipeline's pinned write alias; a hook that queries
      routes through it so the read joins the one transaction.
    - ``instance_pk`` - the authorized target's pk SNAPSHOT (captured immediately
      after the locate, before any consumer code ran); ``None`` on create.
    """

    operation: str
    write_alias: str
    instance_pk: object
