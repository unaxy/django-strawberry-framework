"""manage.py inspect_rules - print the reduction audit of one rung of declared rules.

The static half of the rules inspector (the per-operation half is
``extensions/visibility.py``). ``--rung visibility`` (the default) imports the
project schema so every type is registered and finalized, then runs
``rules.audit`` over the registry and the schema's bypass rules.
``--rung constraints`` runs ``rules.audit_constraints`` over the installed
models' ``Meta.constraints``, ``unique``, ``max_length``, ``choices`` and
validators; no schema is needed. Either way the command prints the leaf
table, the findings and the metric vector (R, M, D, I, B, O) exactly as
``rules.render`` lays them out. Exit status is non-zero under ``--strict`` when
the verdict is NOT REDUCED, so the command doubles as a CI gate.
"""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError, CommandParser
from typing_extensions import override

from django_strawberry_framework.management.commands._imports import (
    import_module_symbol_or_command_error,
)
from django_strawberry_framework.registry import TypeRegistry, registry
from django_strawberry_framework.rules import audit, audit_constraints, render


class Command(BaseCommand):
    """Print the reduction audit for one rung of a project's declared rules."""

    help = "Audit declared visibility rules or model constraints for placement and multiplicity"

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        """Register the rung, the ``--schema`` selector and the ``--strict`` gate flag."""
        parser.add_argument(
            "--rung",
            choices=("visibility", "constraints"),
            default="visibility",
            help="Which rung to audit: visibility rules (needs --schema) or model constraints",
        )
        parser.add_argument(
            "--schema",
            type=str,
            default=None,
            help="Strawberry module[:symbol] selector of the schema to audit (visibility rung)",
        )
        parser.add_argument(
            "--app",
            action="append",
            default=None,
            help="Audit only models belonging to this app label (repeatable)",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit non-zero unless the verdict is REDUCED",
        )

    @override
    def handle(self, *args: object, **options: Any) -> None:  # pyright: ignore[reportExplicitAny]
        """Audit the chosen rung, print the report, gate under ``--strict``."""
        labels = set(options["app"]) if options["app"] else None
        if options["rung"] == "constraints":
            models = [
                model
                for model in apps.get_models()
                if labels is None or model._meta.app_label in labels
            ]
            report = audit_constraints(models)
            title = "inspect_rules --rung constraints"
        else:
            if not options["schema"]:
                raise CommandError("--schema is required for the visibility rung")
            schema = import_module_symbol_or_command_error(
                options["schema"],
                default_symbol_name="schema",
            )
            scoped = registry
            if labels is not None:
                scoped = TypeRegistry()
                for model, type_cls in registry.iter_types():
                    if model._meta.app_label in labels:
                        scoped.register(model, type_cls)
            report = audit(schema, registry=scoped)
            title = f"inspect_rules {options['schema']}"
        self.stdout.write(render(report, title))
        if options["strict"] and not report.reduced:
            raise CommandError(f"{options['rung']} rules are NOT REDUCED")
