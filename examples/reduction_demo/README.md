# Reduction demo

A runnable sketch of the whitepaper's thesis on one rung: read-side row
visibility. One policy, three ways of stating it, one audit.

```bash
python examples/reduction_demo/demo.py
```

The policy is GOAL.md's: staff see everything; everyone else sees rows whose
`is_private` is false and whose parents are visible. The three snapshot apps
return identical rows for an anonymous and a staff actor (the script asserts
it), and differ only in where the rule is written and how many times.

| snapshot | how the policy is stated | what the audit says |
|---|---|---|
| `astronomy_opaque` | GOAL.md verbatim: two hand-written `get_queryset` bodies, each calling `apply_cascade_permissions` | two opaque bodies, two cascade invocation sites; nothing can be footprinted or compared |
| `astronomy_declared` | one `Rule` in the fragment, `Meta.visibility = (visible,)` on both types; hooks gone, cascade now the framework default | R = 2, M = 2: branch in disguise on both types; the actor clause is identical duplication stated too low (owner: schema) and counted in M once per type; the row clause is isomorphic duplication (owner: a mixin that owns `is_private`), also multiplicity 2 |
| `astronomy_reduced` | `StaffBypass` on the schema, `Public` on the `Privatable` mixin that owns the column, no visibility code on either node | R = 1, M = 0, REDUCED |

The visibility half ends with the placement gate: `DjangoSchema(visibility=[Public])` is
refused, because `Public` reads a row field and the schema scope does not
contain that footprint.

## The inverse: a universal restriction

"Suspended users see nothing" (`active_only := actor.is_active eq True`) reads
no row, so no model owns it, and as a conjunct it cannot be a bypass. Two
snapshot apps share two models under a `Privatable` mixin and a staff bypass
on the schema; they differ only in where `active_only` is written.

| snapshot | how the restriction is stated | behaviour | what the audit says |
|---|---|---|---|
| `suspension_restated` | `Meta.visibility = (ActiveOnly,)` on both types | a suspended staff user sees everything: the bypass runs before the per-type rules | R = 2, M = 2: identical duplication, "author once at schema restrictions"; each copy stated too low |
| `suspension_reduced` | `DjangoSchema(restrictions=[ActiveOnly])` | a suspended staff user sees nothing: restrictions are evaluated above the bypass, on every type | R = 1, M = 0, REDUCED |

`DjangoSchema(restrictions=[Public])` is refused by the same placement gate.

## Rung 2: constraints

The same fragment and the same audit, pointed at `Meta.constraints`,
`unique=True`, `max_length`, `choices` and validators. One model with four
rules (unique sku, status in its choices, price at least zero, ends after
starts), stated two ways. Both snapshots refuse the same four bad rows from
`full_clean()` (the script asserts it); only one of them refuses the date
order at the database.

| snapshot | how the rules are stated | what the audit says |
|---|---|---|
| `pricing_restated` | `unique=True` plus a `UniqueConstraint`; `choices` plus a `CheckConstraint(status__in=...)`; `MinValueValidator(0)` plus a `CheckConstraint(price__gte=0)`; the date order in `clean()` only | R = 2 three times over (identical duplication: "keep the constraint; the others restate it"); the `clean()` body is opaque, and the `INSERT` table shows it is bypassable |
| `pricing_reduced` | `unique=True` alone; `choices` plus `ChoicesConstraint("status")`, the `CHECK` derived from the choices; one `CheckConstraint` each for the price floor and the date order; no validator, no `clean()` | R = 1, M = 0, O = 0, REDUCED: Django derives the Python check from each constraint (`validate_constraints`), and `ChoicesConstraint` derives the DB check from the choices, so every rule is authored once and held at L0 |

On this rung M counts a leaf whose owner (L0, when the database can express
the leaf) holds no copy of it, authored or derived: `choices` with nothing
below it is stated too high; `choices` with a `ChoicesConstraint` is placed.
A regex validator has no portable DB form, so its owner stays L1.

## What the prototype adds to the framework

- `django_strawberry_framework/rules/fragment.py`: `Field`, `Actor`, `Rule`,
  boolean structure; `canonical`, `footprint`, `owner`, `leaves`, `evaluate`
  (partial evaluation to a `Q`).
- `rules/apply.py`: the framework-owned `get_queryset` body. Schema
  restrictions first, on every type; then, for a type with rules, schema
  bypasses, then every rule declared on the type or on any class in its
  model's MRO (a `visibility = (...)` attribute on a mixin, abstract or
  concrete), then the forward-FK cascade (`Meta.cascade = False` opts out). A
  type with no declared rule keeps the identity hook it always had past the
  restrictions, cascade included, so the cascade is the default only for
  types that declare a rule.
- `rules/audit.py`: `audit()` and `render()`, the metric vector R / M / D / B
  / O plus cascade invocation counts inside opaque hooks. Isomorphic copies
  raise R like identical ones; a branch in disguise is a finding, not a count.
- `Meta.visibility`, `Meta.cascade`, `Meta.blessed = "<reason>"` (a
  hand-written `get_queryset` counted in B instead of O),
  `DjangoSchema(visibility=...)`, `DjangoSchema(restrictions=...)`.
- `manage.py inspect_rules --schema <selector> [--app <label>] [--strict]`:
  the static inspector, prints the audit; `--strict` exits non-zero unless the
  verdict is REDUCED (the CI gate without a baseline file).
- `extensions/visibility.py::DjangoVisibilityExplainExtension`: the
  per-operation inspector; every type the enforcement body scopes records
  which bypass fired or which rules filtered it, returned under
  `extensions["visibility"]`. No caps and no fail-closed gate yet; the shipped
  `DjangoDebugExtension` is the posture it must copy.

## What it deliberately does not do yet

Isomorphism beyond "same canonical form, different owner", anti-unification,
the SMT fallback, the baseline file and CI ratchet, the RLS twin. Those are
whitepaper sections 8 to 11; this is the smallest thing that shows the owner
computation picking the site, and the audit reading the difference.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
