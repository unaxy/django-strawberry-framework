# Attention: GraphQL names at the optimizer boundary

## Status

The correctness fix landed in the optimizer walker, and the follow-up question this marker kept
open (whether naming configuration should reach `finalize_django_types()` so custom-name collisions
can be refused there) is answered per schema: [`DjangoSchema`][glossary-djangoschema] refuses, at
construction, two fields its own `NameConverter` names alike. Nothing here is pending.

## Why this needs attention

The package advertises four behaviors that meet at the same boundary:

1. A [`DjangoType`][glossary-djangotype] exposes selected Django model fields through Strawberry.
2. Consumer-authored `strawberry.field(...)` overrides are preserved.
3. [`strawberry_config(...)`][glossary-strawberry-config] forwards Strawberry configuration such as
   `auto_camel_case` and a custom `NameConverter`.
4. [`DjangoOptimizerExtension`][glossary-optimizer] maps selected GraphQL fields back to Django ORM
   names to build `.only()`, `select_related()`, and `prefetch_related()` plans, including windowed
   planning for synthesized relation connections.

Those promises require one reliable GraphQL-name-to-Python-name boundary. The old walker reversed
each selected name with the package's own snake caser (since removed) and used that as the
boundary. That works for ordinary default-camel-cased names, but it is not a general inverse of
Strawberry's naming process.

## The underlying issue

GraphQL naming can be lossy or deliberately non-reversible:

| Python or Django name | GraphQL name | Reverse result | Actual ORM name |
| --- | --- | --- | --- |
| `address_2` | `address2` | `address2` | `address_2` |
| `address_line_2` | `addressLine2` | `address_line2` | `address_line_2` |
| `line_2_connection` | `line2Connection` | `line2_connection` | `line_2_connection` |
| `postal_code` with `name="secondaryAddress"` | `secondaryAddress` | `secondary_address` | `postal_code` |

An underscore before a digit disappears under Strawberry's default camelizer. No reverse function
can determine whether `address2` came from `address2` or `address_2`. An explicit GraphQL name or a
custom `NameConverter` can produce an arbitrary valid GraphQL name, so reversal is not even the
right abstraction for those cases.

The authoritative direction is forward:

```text
real Python/Django field
    -> finalized StrawberryField metadata
    -> active schema NameConverter
    -> selected GraphQL name
```

## The confirmed bugs

The old reverse-only lookup caused several related optimizer failures:

- A digit-boundary scalar could be omitted from `.only(...)`, leaving it deferred and causing a
  lazy query when Strawberry resolved the field.
- A digit-boundary foreign key or one-to-one field could be omitted from `select_related(...)`,
  causing a per-parent N+1.
- A synthesized digit-boundary `<field>Connection` could be missed entirely, so its advertised
  windowed `Prefetch` became one connection query per parent.
- A target primary key such as `code_2` could miss the FK-ID-elision path. This remained correct but
  performed an unnecessary join.
- An explicitly named `strawberry.field(...)` could be invisible to optimizer planning even though
  consumer overrides are a documented package feature.
- Selection merging used the reversed name as its identity. Two distinct GraphQL fields
  such as `secondaryAddress` and `secondary_address` therefore collapsed into one selection, and
  one ORM field could disappear from the plan.
- A custom schema `NameConverter`, accepted through `strawberry_config(...)`, could produce names
  the optimizer could not map back to the registered `DjangoType`.

GraphQL results usually remained correct because Django lazily loaded the missing data. The visible
failures were extra queries, broken optimizer guarantees, and possible false `strictness="raise"`
errors for supported fields. The nested-connection case directly contradicted the documented
one-batched-query-per-relation behavior.

## The fix

The optimizer never reverses a GraphQL name.
`django_strawberry_framework/optimizer/selections.py::ast_to_converted_selections` stamps each
converted field selection with the Python name the executing schema published the selected field
from (Strawberry files the `StrawberryField` on each GraphQL field under `DEFINITION_BACKREF`), read
back through `django_strawberry_framework/optimizer/selections.py::selection_python_name`, and
`django_strawberry_framework/optimizer/walker.py::_resolve_selection_target` matches that name
against the type's synthesized relation connections, then its model fields, returning the real
Django field name for ORM planning.

The same forward path covers:

- scalar projection;
- forward and reverse relation planning;
- synthesized relation-connection recognition;
- FK-ID elision;
- explicit `strawberry.field(name=...)` names; and
- custom schema name converters.

Selection merging keys on the exact GraphQL field name. Aliases of the same field still merge
because their `selection.name` is identical, while distinct GraphQL names remain distinct even when
a reverse caser would map them to one Python name.

The fix does **not** rename public GraphQL fields, change the default camel-casing convention, or
change the `DjangoType` declaration API. It makes optimizer planning follow the schema Strawberry
actually built.

## Collisions under a custom converter

`finalize_django_types()` runs before any schema exists, so it refuses only two fields with one
Python name. Two fields one schema's `NameConverter` names alike, including a pair only a custom
converter collides (one mapping both `primary_address` and `shipping_address` to `address`), are
refused when that `DjangoSchema` is built
(`django_strawberry_framework/schema.py::_refuse_field_name_collisions`), with a
`ConfigurationError` naming the type and both fields. Strawberry itself would keep one and
silently drop the other, which is what a plain `strawberry.Schema` does.

A direct call to the private `optimizer.walker.plan_optimizations(..., info=None)` has no converted
selections from an executing schema to read names from. The public `DjangoOptimizerExtension` path
always supplies execution `info`, and `plan_optimizations` is deliberately not re-exported as
consumer API, so this does not limit an advertised feature.

## Real-world example 1: how I thought it worked

Consider a delivery application with a conventional second address line and a numbered reverse
relation retained from a legacy database:

```python
class ShippingAddress(models.Model):
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)


class DeliveryAttempt(models.Model):
    address = models.ForeignKey(
        ShippingAddress,
        related_name="delivery_attempt_2",
        on_delete=models.CASCADE,
    )


class ShippingAddressType(DjangoType):
    class Meta:
        model = ShippingAddress
        fields = ("id", "address_line_1", "address_line_2", "delivery_attempt_2")
        interfaces = (relay.Node,)
```

A consumer reasonably expects this query:

```graphql
{
  shippingAddresses {
    addressLine2
    deliveryAttempt2Connection(
      first: 3
    ) {
      edges {
        node {
          id
        }
      }
    }
  }
}
```

to produce a projection containing `address_line_2` and one batched windowed prefetch for
`delivery_attempt_2`. The mental model was that camel-casing and snake-casing were inverse operations,
so every selected GraphQL name would return to its Django field automatically.

Before the fix, `addressLine2` reversed to `address_line2`, and `deliveryAttempt2Connection`
reversed to `delivery_attempt2_connection`. Neither matched the actual metadata keys. The scalar was
deferred and the connection was unplanned, even though the query and schema were valid.

## Real-world example 2: how it actually works now

The same schema and query keep their existing public names. Each selected field carries the Python
name the executing schema published it from, and planning matches that name:

```text
addressLine2
    -> published from StrawberryField(python_name="address_line_2")
    -> model field address_line_2
    -> .only("address_line_2")

deliveryAttempt2Connection
    -> published from the synthesized delivery_attempt_2_connection field
    -> relation connection over delivery_attempt_2
    -> Prefetch("delivery_attempt_2", to_attr="_dst_delivery_attempt_2_connection")
```

This also works if the application explicitly exposes `address_line_2` as `secondaryAddress`, or if
a custom `NameConverter` chooses that name globally. Planning follows the actual schema name forward
to the real ORM field instead of trying to reconstruct the ORM name from GraphQL text.

If two selected fields are explicitly named `secondaryAddress` and `secondary_address`, they now
remain two independent selections. Exact GraphQL identity controls merging, so both underlying ORM
columns appear in the plan.

## Questions answered

1. Custom-converter collisions are framework-attributed at `DjangoSchema` construction, per schema,
   rather than at finalization, so finalization takes no `StrawberryConfig` and gains no lifecycle
   dependency on one.
2. The public documentation states it ([`DjangoSchema`][glossary-djangoschema]).
3. Live rows pin the custom-converter path (`examples/fakeshop/test_query/test_globalid_naming_api.py`
   and the custom-converter rows of `examples/fakeshop/test_query/test_library_api.py`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangoschema]: docs/GLOSSARY.md#djangoschema
[glossary-djangotype]: docs/GLOSSARY.md#djangotype
[glossary-optimizer]: docs/GLOSSARY.md#djangooptimizerextension
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[walker]: django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
