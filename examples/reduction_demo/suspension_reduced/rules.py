"""Snapshot ``suspension_reduced``: the two rules this snapshot states, named once each."""

from django_strawberry_framework.rules import Actor, Field, Rule

Public = Rule("public", Field("is_private").is_false())
ActiveOnly = Rule("active_only", Actor("is_active").is_true())
