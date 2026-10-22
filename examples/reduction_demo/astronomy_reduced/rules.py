"""Snapshot 3 (reduced): each leaf named once, at its owner.

``StaffBypass`` reads only the actor, so its owner is the schema (it goes in
``DjangoSchema(visibility=...)``). ``Public`` reads one row field, so its owner
is whatever class owns that field: the ``Privatable`` mixin in ``models.py``.
"""

from django_strawberry_framework.rules import Actor, Field, Rule

StaffBypass = Rule("staff_bypass", Actor("is_staff").is_true())
Public = Rule("public", Field("is_private").is_false())
