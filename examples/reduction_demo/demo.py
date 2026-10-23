"""Reduction demo: one visibility policy, three ways of stating it, one audit.

Run from the repo root::

    python examples/reduction_demo/demo.py

Three snapshots of GOAL.md's ``astronomy`` app share one policy ("staff see
everything; everyone else sees public rows whose parents are public"):

1. ``astronomy_opaque``   - the policy as two hand-written ``get_queryset`` bodies
2. ``astronomy_declared`` - the policy in the rule fragment, still once per type
3. ``astronomy_reduced``  - each leaf stated once, at the scope its footprint picks

The script proves the three return identical rows for an anonymous and a staff
actor, then prints the reduction audit for each. Same behaviour, three very
different answers to "where does this rule live, and how many times?".
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# The checkout being demonstrated must win over any editable install elsewhere.
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.models import AnonymousUser  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import RequestFactory  # noqa: E402

import django_strawberry_framework  # noqa: E402
from django_strawberry_framework import DjangoSchema  # noqa: E402
from django_strawberry_framework.exceptions import ConfigurationError  # noqa: E402
from django_strawberry_framework.rules import audit, render  # noqa: E402

assert Path(django_strawberry_framework.__file__).is_relative_to(ROOT), (
    django_strawberry_framework.__file__
)

QUERY = "{ galaxies { name } bodies { name galaxy { name } } }"


def seed(models) -> None:
    andromeda = models.Galaxy.objects.create(name="Andromeda", is_private=False)
    hidden = models.Galaxy.objects.create(name="Hidden", is_private=True)
    models.CelestialBody.objects.create(name="public in Andromeda", galaxy=andromeda)
    models.CelestialBody.objects.create(
        name="private in Andromeda",
        galaxy=andromeda,
        is_private=True,
    )
    models.CelestialBody.objects.create(name="public in Hidden", galaxy=hidden)
    models.CelestialBody.objects.create(name="private in Hidden", galaxy=hidden, is_private=True)


def execute(schema: DjangoSchema, user):
    request = RequestFactory().get("/graphql/")
    request.user = user
    result = schema.execute_sync(QUERY, context_value=SimpleNamespace(request=request))
    assert result.errors is None, result.errors
    assert result.data is not None
    return result


def run(schema: DjangoSchema, user) -> dict:
    return execute(schema, user).data


def main() -> int:
    call_command("migrate", run_syncdb=True, verbosity=0)

    import astronomy_declared.models as declared_models
    import astronomy_opaque.models as opaque_models
    import astronomy_reduced.models as reduced_models
    import astronomy_reduced.schema as reduced
    import schemas as demo_schemas
    from astronomy_reduced.rules import Public

    schemas = {
        "1. opaque   (GOAL.md verbatim: two get_queryset bodies)": (
            demo_schemas.opaque,
            opaque_models,
        ),
        "2. declared (same rule in the fragment, once per type)": (
            demo_schemas.declared,
            declared_models,
        ),
        "3. reduced  (schema bypass + Privatable mixin, no hook bodies)": (
            demo_schemas.reduced,
            reduced_models,
        ),
    }
    for _schema, models in schemas.values():
        seed(models)

    staff = get_user_model().objects.create_user("staff", is_staff=True)
    actors = {"anonymous": AnonymousUser(), "staff": staff}

    print("BEHAVIOUR (must be identical across the three snapshots)")
    print("-" * 60)
    baseline: dict[str, dict] = {}
    for actor_name, user in actors.items():
        for title, (schema, _models) in schemas.items():
            data = run(schema, user)
            baseline.setdefault(actor_name, data)
            assert data == baseline[actor_name], (title, actor_name, data)
        galaxies = [g["name"] for g in baseline[actor_name]["galaxies"]]
        bodies = [b["name"] for b in baseline[actor_name]["bodies"]]
        print(f"{actor_name:>10}: galaxies={galaxies}")
        print(f"{'':>10}  bodies={bodies}")
    assert [g["name"] for g in baseline["anonymous"]["galaxies"]] == ["Andromeda"]
    assert [b["name"] for b in baseline["anonymous"]["bodies"]] == ["public in Andromeda"]
    assert len(baseline["staff"]["bodies"]) == 4
    print("all three snapshots agree for both actors\n")

    print("AUDIT (same behaviour, three answers to 'where is the rule, how many times')")
    print("-" * 60)
    for title, (schema, models) in schemas.items():
        print(render(audit(schema, registry=scoped_registry(models)), title))
        print()

    print("PLACEMENT GATE (a row rule cannot live at schema scope)")
    print("-" * 60)
    try:
        demo_schemas.build(reduced.Query, visibility=[Public])
    except ConfigurationError as exc:
        print(f"refused: {exc}")
    print()

    print("EXPLAIN (extensions['visibility'] on the reduced schema: which rule fired where)")
    print("-" * 60)
    for actor_name, user in actors.items():
        result = execute(demo_schemas.reduced, user)
        print(f"{actor_name}:")
        for event in result.extensions["visibility"]:
            print(f"  {json.dumps(event)}")
    print()

    print(
        "INSPECT_RULES (manage.py inspect_rules --schema schemas:reduced --app astronomy_reduced)",
    )
    print("-" * 60)
    call_command("inspect_rules", "--schema", "schemas:reduced", "--app", "astronomy_reduced")
    print()
    universal_restriction(staff)
    return rung_two()


def scoped_registry(models) -> object:
    """A registry holding only the types over ``models``' module, so each snapshot audits alone."""
    from django_strawberry_framework.registry import TypeRegistry
    from django_strawberry_framework.registry import registry as global_registry

    scoped = TypeRegistry()
    for model, type_cls in global_registry.iter_types():
        if model.__module__ == models.__name__:
            scoped.register(model, type_cls)
    return scoped


def universal_restriction(staff) -> None:
    """The inverse of the lead example: one restriction every type must apply."""
    import schemas as demo_schemas
    import suspension_reduced.models as reduced_models
    import suspension_reduced.schema as reduced
    import suspension_restated.models as restated_models
    from suspension_reduced.rules import Public

    query = "{ tickets { title } replies { body ticket { title } } }"
    for models in (restated_models, reduced_models):
        open_ticket = models.Ticket.objects.create(title="open")
        hidden = models.Ticket.objects.create(title="hidden", is_private=True)
        models.Reply.objects.create(ticket=open_ticket, body="public on open")
        models.Reply.objects.create(ticket=open_ticket, body="private on open", is_private=True)
        models.Reply.objects.create(ticket=hidden, body="public on hidden")
    snapshots = {
        "restated (active_only on each type)": (demo_schemas.suspension_restated, restated_models),
        "reduced  (active_only on the schema)": (demo_schemas.suspension_reduced, reduced_models),
    }
    user_model = get_user_model()
    actors = {
        "anonymous": AnonymousUser(),
        "member": user_model.objects.create_user("member"),
        "staff": staff,
        "suspended staff": user_model.objects.create_user(
            "suspended",
            is_staff=True,
            is_active=False,
        ),
    }

    print("UNIVERSAL RESTRICTION ('suspended users see nothing', two ways of stating it)")
    print("-" * 60)
    rows: dict[str, dict[str, list[str]]] = {}
    for actor_name, user in actors.items():
        for title, (schema, _models) in snapshots.items():
            request = RequestFactory().get("/graphql/")
            request.user = user
            result = schema.execute_sync(query, context_value=SimpleNamespace(request=request))
            assert result.errors is None, result.errors
            assert result.data is not None
            rows.setdefault(actor_name, {})[title] = [r["body"] for r in result.data["replies"]]
        seen = rows[actor_name]
        agree = len({tuple(v) for v in seen.values()}) == 1
        for title, replies in seen.items():
            print(f"{actor_name:>16} {title[:8]}: replies={replies}")
        print(f"{'':>16} {'agree' if agree else 'DIFFER'}")
    assert rows["anonymous"] == {t: [] for t in snapshots}
    assert all(v == ["public on open"] for v in rows["member"].values())
    assert all(len(v) == 3 for v in rows["staff"].values())
    assert rows["suspended staff"]["restated (active_only on each type)"] != []
    assert rows["suspended staff"]["reduced  (active_only on the schema)"] == []
    print(
        "restated: the schema bypass runs before the per-type restriction, so a suspended\n"
        "staff user sees everything; reduced: the restriction is evaluated above the bypass\n",
    )

    print("AUDIT (the actor leaf reads no row, so no model owns it)")
    print("-" * 60)
    for title, (schema, models) in snapshots.items():
        print(render(audit(schema, registry=scoped_registry(models)), title))
        print()

    print("PLACEMENT GATE (a row rule cannot be a schema restriction either)")
    print("-" * 60)
    try:
        demo_schemas.build(reduced.Query, restrictions=[Public])
    except ConfigurationError as exc:
        print(f"refused: {exc}")
    print()


def rung_two() -> int:
    """Rung 2: four declarative constraints on one model, restated twice versus authored once."""
    from datetime import date
    from decimal import Decimal

    import pricing_reduced.models as reduced_pricing
    import pricing_restated.models as restated_pricing
    from django.core.exceptions import ValidationError
    from django.db import IntegrityError, transaction

    from django_strawberry_framework.rules import audit_constraints

    snapshots = {"restated": restated_pricing.Offer, "reduced": reduced_pricing.Offer}
    jan, feb = date(2026, 1, 1), date(2026, 2, 1)
    good = {
        "sku": "dup",
        "status": "live",
        "price": Decimal("1"),
        "starts": jan,
        "ends": feb,
    }
    bad_rows = {
        "negative price": {**good, "sku": "a", "price": Decimal("-1")},
        "unknown status": {**good, "sku": "b", "status": "bogus"},
        "ends before starts": {
            **good,
            "sku": "c",
            "starts": feb,
            "ends": jan,
        },
        "duplicate sku": dict(good),
    }
    for offer in snapshots.values():
        offer.objects.create(**good)

    print("RUNG 2: CONSTRAINTS (one model, two ways of stating four rules)")
    print("-" * 60)
    print(f"{'bad row':<20} {'snapshot':<10} {'full_clean()':<28} INSERT")
    inserted: dict[tuple[str, str], bool] = {}
    for label, values in bad_rows.items():
        for name, offer in snapshots.items():
            try:
                offer(**values).full_clean()
                cleaned = "accepted"
            except ValidationError as exc:
                cleaned = "refused on " + ", ".join(sorted(exc.message_dict))
            try:
                with transaction.atomic():
                    offer.objects.create(**values)
                inserted[label, name] = True
            except IntegrityError:
                inserted[label, name] = False
            verdict = "ACCEPTED" if inserted[label, name] else "refused"
            print(f"{label:<20} {name:<10} {cleaned:<28} {verdict}")
    # Both snapshots refuse every bad row in Python; only the reduced one has the
    # date order in the database, so the restated snapshot's clean() is bypassable.
    assert inserted["ends before starts", "restated"] is True
    assert all(not ok for (label, _), ok in inserted.items() if label != "ends before starts")
    assert inserted["ends before starts", "reduced"] is False
    print("same four refusals from full_clean(); the restated date rule is DB-bypassable\n")

    print("AUDIT (rung 2)")
    print("-" * 60)
    for name, offer in snapshots.items():
        print(render(audit_constraints([offer]), f"pricing_{name}"))
        print()

    print(
        "INSPECT_RULES (manage.py inspect_rules --rung constraints --app pricing_reduced --strict)",
    )
    print("-" * 60)
    call_command("inspect_rules", "--rung", "constraints", "--app", "pricing_reduced", "--strict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
