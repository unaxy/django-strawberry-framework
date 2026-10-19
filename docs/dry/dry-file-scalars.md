# DRY review: `django_strawberry_framework/scalars.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a reused family row (trigger re-checked fresh, never
inherited), a file-local record with its proving challenge, or a recorded
rejection with contract difference + trigger + durable home. Zero production
edits; zero tracked files changed.

## System trace

Small target (207 lines, 18 top-level statements): the package's public
scalar definitions plus the schema-config factory. It DEFINES the `BigInt`
wire contract (`scalars.py::_parse_bigint` strict parser,
`scalars.py::_serialize_bigint` strict serializer, `scalars.py::BigInt`
`NewType`, `scalars.py::_BIGINT_SCALAR_DEFINITION` Strawberry binding),
the registration map (`scalars.py::_PACKAGE_SCALAR_MAP`, today one entry),
the single re-export point for Strawberry's `Upload`
(`scalars.py::Upload` / `scalars.py::UploadDefinition`, owned upstream),
and the config factory (`scalars.py::strawberry_config` fresh-map
isolation, collision `ValueError`, hostile-key containment,
`scalar_map=` refusal, `**config_kwargs` passthrough). It ENFORCES the
BigInt grammar at parse/serialize call time and the factory boundary at
schema-construction time. The module docstring's two load-bearing claims
were verified against the bodies: `Upload` resolves with NO map entry
because it rides Strawberry's `DEFAULT_SCALAR_REGISTRY` (probe P4:
`Upload` in registry, `BigInt` absent, registry size 17), and the
parse/serialize sides are wire-symmetric (decimal string in, decimal
string out) while the in-Python accept sets deliberately differ (probe
P2: every serialized sample fullmatches the parser grammar and
reparses to the identical int).

Connected code read for judgment, outside the item:
`django_strawberry_framework/exceptions.py` (full read;
`_safe_type_name` / `_safe_arg_repr` composed by name here,
`_safe_class_name` shared body for the J1 re-derivation);
`django_strawberry_framework/utils/querysets.py` (the stricter local
`_safe_class_name` twin + `STRICTER` docstring clause, cited region);
`django_strawberry_framework/types/converters.py` (full read;
`SCALAR_MAP` ownership incl. the `BigAutoField -> int` START.md
boundary and the `BigIntegerField` / `PositiveBigIntegerField -> BigInt`
rows consuming this file's `BigInt` by name);
`django_strawberry_framework/forms/converter.py` (full registry read;
`_SCALAR_FORM_FIELDS` model-less key space + kind prechecks);
`django_strawberry_framework/forms/inputs.py` (`Upload` file-triple
consumer, import + use lines);
`django_strawberry_framework/mutations/inputs.py`
(`model_column_write_annotation` file branch returning `Upload`,
import + use lines);
`django_strawberry_framework/rest_framework/serializer_converter.py`
(`_SERIALIZER_FIELD_CONVERTERS` registry + `Upload` annotation +
read-side `convert_scalar` / `scalar_for_field` delegation, import +
use lines);
`django_strawberry_framework/utils/converters.py`
(`convert_with_mro` shared walk mechanism);
`django_strawberry_framework/__init__.py` (root manifest re-exporting
`BigInt`, `Upload`, `strawberry_config` but not `UploadDefinition`);
`django_strawberry_framework/management/commands/inspect_django_type.py`
(`_GRAPHQL_SCALAR_NAMES` merging `_PACKAGE_SCALAR_MAP` by name with
an explicit no-second-literal comment);
`django_strawberry_framework/extensions/debug.py` (docstring consumer
example) and `django_strawberry_framework/extensions/resource_policy.py`
(`_UPLOAD_SCALAR_NAME = "Upload"` wire-name classifier, read);
`django_strawberry_framework/optimizer/lateral_fetch.py`
(`_ARRAY_BINDABLE_PARENT_FIELD_TYPES` field-name string set, read --
bindability contract, not a scalar map);
`django_strawberry_framework/orders/inputs.py` (doc prose stating the
order converter does NOT differentiate `BigIntegerField` columns);
`examples/fakeshop/apps/scalars/schema.py` + `models.py`
(consumer declarations + converter-row rationale comments);
`examples/fakeshop/config/schema.py` (consumer `config=` call);
`tests/test_scalars.py` (46 top-level statements, oracle inventory with an explicit
live-vs-package tier rationale in its header);
`examples/fakeshop/test_query/test_scalars_api.py`,
`test_scalars_filter_api.py` (live oracles); `docs/GLOSSARY.md`
(`BigInt` / `strawberry_config` / `Upload` entries) + `CHANGELOG.md`
(projections). Upstream `.venv` sources read: `strawberry`
`file_uploads/scalars.py` (`Upload` owner), `schema_converter.py`
(`DEFAULT_SCALAR_REGISTRY` owner), `schema/config.py`
(`StrawberryConfig` signature incl. `InitVar auto_camel_case`).

## Verification

### Matrix

Each axis searched against the target's REAL surface (probes P1--P6,
all read-only, all green; commands under `### Challenges`).

1. **Cross-flavor policy mirroring.** Searched, not assumed unique.
Table census (P6): `SCALAR_MAP` 26 keys, all `models.Field`
subclasses; `_PACKAGE_SCALAR_MAP` 1 key (`BigInt`, not a field);
`_SCALAR_FORM_FIELDS` 12 keys, all `forms.Field` subclasses, no
`BigInt`/file rows; `_SERIALIZER_FIELD_CONVERTERS` 16 keys, all
`serializers.Field` subclasses; the three field-keyed spaces pairwise
disjoint. `Upload` reaches the three write flavors by NAME from this
file (`is`-identical in forms + mutations inputs, P6), never by a
second mapping. Order inputs deliberately do NOT mirror the scalar
table (direction-only contract, doc-pinned). `lateral_fetch`'s
field-name string set is a psycopg-bindability contract, different
mechanism (name strings, not type maps). Verdict: one rule per
surface; the only sharing is correct (write flavors delegate
model-backed columns to the read side by name; see J2).
2. **Sync/async twins.** Discharged inapplicable by construction.
Instrument (P1): zero `AsyncFunctionDef`, zero `ClassDef` at module
level. Strawberry scalar `parse_value`/`serialize` hooks and the
`StrawberryConfig` factory are sync-only call sites; the target
touches no ORM, no await, no cancellation, no transaction. Async
suites build schemas with this factory's configs, but the factory
itself has no colored twin and no await point to preserve.
3. **Derived rather than repeated knowledge.** Searched. `BigInt` the
name appears twice (`NewType("BigInt", int)` Python identity,
`strawberry.scalar(name="BigInt")` GraphQL name) -- same file, same
owner, distinct contracts (C11 counts 1). `_PACKAGE_SCALAR_MAP`
derives from `_BIGINT_SCALAR_DEFINITION` by name (principle 6,
one line). The inspect-command namer derives `BigInt` from the map
by name with a no-second-literal comment (consumer, listed not
counted). Collision labels derive through `_safe_scalar_map_key_label`
(same owner). No cross-file duplicated fact is owned here.
4. **Inverse / round-trip pairs.** The pair (`_parse_bigint` /
`_serialize_bigint`) is co-owned in this file under one symmetry
contract. P2 proves the halves agree observationally: hostile-int
normalization both directions, canonical-string symmetry on seven
sample ints incl. 64-bit extrema and 101-digit values, strict
rejection matrices on both sides (bool/float/`None`/padded/plus/
leading-zero/`-0`/underscore/scientific/hex/Unicode-digit/non-decimal
inputs; bool/float/str/`Decimal`/`None`/object outputs). Test
expectations restating the grammar are oracles (listed, not
counted); the >4300-digit CPython cap was investigated and is not a
second definition (see axis 6).
5. **Contracts restated in another medium.** Counted 1 definition per
rule; everything else classified: module docstring (projection,
verified clause-by-clause against the bodies); GLOSSARY `BigInt` /
`strawberry_config` / `Upload` entries + CHANGELOG 0.0.7/0.0.8 rows
(projections); `tests/test_scalars.py` 46 members (oracles -- its
header states per-row WHY each row cannot be live: hostile
subclasses, non-int serializer inputs, direct-call parser inputs,
import surface, factory construction, default-registry resolution);
live `test_scalars_api.py` / `test_scalars_filter_api.py` /
`test_uploads_api.py` (wire oracles); scalars example-app
schema/models/filters/orders (consumers + rationale comments);
`config/schema.py` (consumer). No medium holds an independently
maintained copy of any rule.
6. **Enforcement by omission.** Family enumerated, each absence
checked against a contract source. Map omits `Upload`: intentional
(module docstring + spec-037 Decision 5 + GLOSSARY + oracle pinning
the absence + live proof it resolves under a plain
`StrawberryConfig`) -- not a gap. Serializer omits `str`:
intentional symmetry (oracle pins the rejection). Factory omits
value validation: Strawberry owns values at `Schema` build; no
contract source requires factory-side validation, and adding it
would duplicate upstream -- investigated, not a defect. Parser
omits `__index__`-only integers (numpy-style): no contract source;
`IntEnum` (a real `int`) works -- investigated, not a defect.
`BigAutoField -> BigInt`: owned by `types/converters.py`, START.md
pins `int` -- not this file's omission (C8 counts 0 here).
`>4300`-digit ints raise CPython `ValueError` from `int.__repr__`
on the serialize side: no spec/glossary/oracle pins huge-int
serialization, unreachable from any mapped 64-bit column, and
graphql-core converts a serialize raise to a field error either
way -- investigated boundary, not a defect (adding a guard would
change what is accepted, never behavior-preserving).

### Enumeration

Instrument: `ast` dump of `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-scalars/p1_ast_census.py`), count 18.
Every member lands below; R = file-local finding, F = reused family
row, J = recorded rejection.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | projection | R1/R2/R4/R5 prose verified |
| 2 | `import re` | machinery import | R1 consumer |
| 3 | `Mapping` import | annotation import | R5 consumer |
| 4 | `Any`, `NewType` imports | annotation imports | R1/R3/R5 consumers |
| 5 | `import strawberry` | engine import | R3 consumer |
| 6 | `Upload`, `UploadDefinition` import | upstream re-export source | R6 (upstream owns) |
| 7 | `StrawberryConfig` import | return-type import | R5 consumer |
| 8 | `ScalarDefinition` import | annotation import | R4/R5 consumers |
| 9 | `_safe_arg_repr`, `_safe_type_name` import | helper imports | R1/R2/R5 consumers (F non-member) |
| 10 | `__all__` | leaf manifest (4 names) | R7 |
| 11 | `_BIGINT_STRING_PATTERN` | grammar constant | R1 |
| 12 | `def _parse_bigint` | strict parser | R1 |
| 13 | `def _serialize_bigint` | strict serializer | R2 |
| 14 | `BigInt = NewType(...)` | scalar identity | R3 |
| 15 | `_BIGINT_SCALAR_DEFINITION` | Strawberry binding | R3 |
| 16 | `_PACKAGE_SCALAR_MAP` | registration map | R4 |
| 17 | `def strawberry_config` | config factory | R5 |
| 18 | `def _safe_scalar_map_key_label` | collision-key labeler | J1 (third site) |

No member unassigned. Prior-cycle trigger note: the exceptions-item
J1 table already records member 18 as the third hostile-class-name
site; it was re-derived fresh from this side (probe P5) and the
rejection is CONFIRMED below, not inherited.

### Challenges

Authoritative definitions counted only; consumers, oracles, and
projections that move alongside are listed, not counted. Executed
probes are read-only files under
`docs/dry/temp-tests/dry-file-scalars/` run with `uv run python`
from the repo root; NO shared-tree pytest, NO source mutation (so no
workspace copy was owed), NO database opened by any probe.

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| C1 | register a second package scalar | **1** (`scalars.py`: NewType + definition + map row + `__all__` + docstring, one file/owner) | inspect namer follows by construction; GLOSSARY/CHANGELOG/tests move as projection/oracle |
| C2 | widen the wire grammar (e.g. accept `+1`) | **1** (pattern + parser + messages, same body) | package + live BigInt oracles |
| C3 | serializer accepts `str` | **1** (refused: symmetry contract; oracle `test_bigint_serialize_rejects_non_int_types` pins) | same oracles |
| C4 | allow redeclaring a package scalar | **1** (factory collision branch; oracle pins `ValueError`) | collision-message oracles |
| C5 | drop hostile-key containment | **1** (factory `try/except` + labeler; oracles pin `ValueError` + chained cause) | hostile-key oracles |
| C6 | register `Upload` in the package map | **1** (refused: upstream owns it; oracle pins the absence, live test pins default-registry resolution) | SDL oracle |
| C7 | rename the GraphQL scalar | **1** (definition `name=`; inspect namer follows by construction) | SDL/namer oracles |
| C8 | `BigAutoField -> BigInt` | **0 here** (owned by `types/converters.py::SCALAR_MAP`; START.md pins `int`) | converter oracles |
| C9 | unify all converter tables into one map | **refused** (J2: four key spaces, four contracts) | -- |
| C10 | one shared class-label helper | **refused** (J1: 3 definitions, diverging oracles P5) | -- |
| C11 | spell the `BigInt` name once | **1** (same file; Python-identity vs GraphQL-name are distinct contracts -- renaming the GraphQL type touches only `name=`, renaming the symbol touches imports) | -- |
| C12 | root-export `UploadDefinition` | **0 here** (routed observation for `package-root-public-surface`; no contract source requires it) | -- |

Probe commands + what each proved (`static-reviewed` marks oracle
bodies read but not executed; every probe below is
`execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-scalars/p1_ast_census.py`
  -- 18 members, 0 async, 0 class defs (matrix axis 2 +
  enumeration instrument). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-scalars/p2_bigint_matrix.py`
  -- 14 accept + 21 `ValueError` + 2 structural parser cases;
  serializer canonicalization of hostile/`Hex`/`IntEnum` ints;
  6 `TypeError` outputs; 7-value wire symmetry; huge-int digit-cap
  boundary recorded. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-scalars/p3_config_factory.py`
  -- 20 factory assertions: instance shape, BigInt-in/Upload-out,
  per-call map isolation, `None`-vs-`{}` equivalence, `scalar_map=`
  refusal, merge + caller-dict immutability, collision message,
  three hostile mappings contained as `ValueError` (unmaterializable,
  keys-raising, `__eq__`-raising with chained cause), kwarg
  passthrough (`name_converter.auto_camel_case`, per the
  `InitVar` oracle), extra+kwargs composition, upstream `TypeError`
  transparency, labeler plain-`str` normalization incl. `sorted()`
  safety. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-scalars/p4_upload_identity.py`
  -- `is`-identity of `Upload`/`UploadDefinition`/root symbols,
  `__all__` manifest, one-entry map, default-registry
  membership (17 entries, strawberry-graphql 0.324.0). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-scalars/p5_j1_divergence.py`
  -- fresh three-body divergence table (see J1). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-scalars/p6_table_census.py`
  -- key-space populations (26/1/12/16), `BigAutoField -> int` vs
  `BigIntegerField`/`PositiveBigIntegerField -> BigInt`, form-table
  file-row absence, three-space disjointness, `Upload` `is`-sharing,
  inspect-namer derivation. `execution-verified`.

## Findings

### R1 -- BigInt input grammar (file-local)

- **Contract + variation.** Wire input is a JSON-safe decimal: Python
  `int` (excluding `bool`) or a canonical ASCII decimal string
  `^(0|-?[1-9][0-9]*)$`. Varies on nothing legitimate; every listed
  rejection (`bool`, `float`, padded/plus/leading-zero/`-0`/
  underscore/scientific/hex/Unicode-digit/empty strings, `None`,
  `Decimal`, foreign objects) is part of the contract.
- **Sites + roles.** Definition: `scalars.py::_BIGINT_STRING_PATTERN`
  + `scalars.py::_parse_bigint` (one body split across a constant and
  its sole reader -- within-file factoring, not two definitions).
  Consumers: Strawberry `parse_value` hook (engine), converter-table
  `BigInt` rows (they name the TYPE, never the grammar),
  `scalar_specimen_by_signed_big` example query. Oracles:
  `tests/test_scalars.py` parser rows + live
  `test_scalars_api.py` literal-acceptance rows. Projections:
  parser docstring, module docstring, GLOSSARY `BigInt` entry.
- **Challenges.** C2 counts 1; C11 counts 1 for the name half.
- **Owner + lifetime.** Owner is this file (the scalar's home; no
  narrower candidate exists -- the grammar is meaningless outside the
  scalar). No stored derivation (pure function + module constant).
- **Migration.** None (no consolidation in a file item).
- **Distinct behavior.** Hostile `int`/`str` subclasses normalized
  through base slots (`int.__int__`, `str.__str__`) so consumer
  dunders cannot forge or break the wire value (P2 + hostile oracles).
- **Behavioral proof.** P2 `execution-verified` (37 parser cases);
  oracles `static-reviewed` (suite not run per item rules).
- **Structural gate.** Existing oracles fail on any grammar drift
  (e.g. accepting `+1` breaks the malformed-literal live rows AND
  the package rejection rows); negative control is their documented
  tier rationale (direct-call rows unexpressible live).
- **Freshness.** Target `5e354042d405040f6137cebd39abe9c042ffece8`;
  `tests/test_scalars.py`
  `b9819c140ec921fc606a95335f3a801bf50b1f9d`;
  `test_scalars_api.py`
  `8c09e9b558901be0178a2658ec22e16a1d316c7f`.

### R2 -- BigInt output serializer (file-local)

- **Contract + variation.** Serializes Python `int` (excluding
  `bool`) to canonical decimal `str` via `int.__repr__` (bypasses
  subclass `__repr__`/`__str__`); rejects everything else with
  `TypeError`, INCLUDING canonical strings -- the input/output
  symmetry contract (a schema cannot emit what the parser rejects).
- **Sites + roles.** Definition: `scalars.py::_serialize_bigint`.
  Round-trip half of R1 under the same owner (one grammar, two
  halves, one file -- the DRY-approved shape for an inseparable
  pair). Oracles: hostile-subclass + non-int rejection rows.
- **Challenges.** C3 counts 1 (refused by contract).
- **Owner + lifetime.** This file; pure function, nothing stored.
- **Behavioral proof.** P2 `execution-verified` (canonicalization +
  6 `TypeError` rows + 7-value symmetry loop).
- **Structural gate.** Rejection oracles pin both the accept shape
  and the strictness (a permissive `serialize=str` breaks the
  non-int rows).
- **Freshness.** Target as in R1.

### R3 -- BigInt identity + Strawberry binding (file-local)

- **Contract + variation.** `scalars.py::BigInt` (`NewType("BigInt",
  int)`) is the annotation identity; `scalars.py::_BIGINT_SCALAR_DEFINITION`
  (`strawberry.scalar(name="BigInt", serialize=..., parse_value=...)`)
  is the GraphQL binding. The two `BigInt` spellings are distinct
  contracts (Python identity vs GraphQL type name), C11.
- **Sites + roles.** Definitions (one owner):
  `scalars.py::BigInt`, `scalars.py::_BIGINT_SCALAR_DEFINITION`.
  Consumer: `types/converters.py::SCALAR_MAP` rows (name the type by
  import, P6). Oracles: introspection rows naming the `BigInt` SDL
  scalar on both 64-bit columns.
- **Challenges.** C7 counts 1; C11 counts 1.
- **Behavioral proof.** P4 `execution-verified` (binding name,
  map linkage).
- **Freshness.** Target as in R1; `types/converters.py`
  `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75`.

### R4 -- Package scalar registration map (file-local)

- **Contract + variation.** `scalars.py::_PACKAGE_SCALAR_MAP` maps
  package-CUSTOM scalar types to their definitions (today exactly
  `{BigInt: definition}`). `Upload` is deliberately absent --
  upstream's `DEFAULT_SCALAR_REGISTRY` owns it (P4). Varies by
  adding future custom scalars (C1 counts 1).
- **Sites + roles.** Definition here. Consumers (compose by name):
  `strawberry_config` (merge source),
  `inspect_django_type._GRAPHQL_SCALAR_NAMES` (derives the `BigInt`
  SDL name from the map with a no-second-literal comment).
  NOT a second converter table (see J2).
- **Challenges.** C1 counts 1; C6 counts 1 (absence refused);
  C8 counts 0 here.
- **Behavioral proof.** P4 `execution-verified` (exact one-entry
  contents, registry contrast).
- **Structural gate.** Absence oracle
  (`test_strawberry_config_scalar_map_excludes_upload`) + live
  default-registry proof
  (`test_upload_field_resolves_under_plain_strawberry_config`).
- **Freshness.** Target as in R1; `inspect_django_type.py`
  `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d`.

### R5 -- `strawberry_config()` factory (file-local)

- **Contract + variation.** Returns a fresh `StrawberryConfig` per
  call carrying an isolated merge of `_PACKAGE_SCALAR_MAP` with
  `extra_scalar_map`; collisions raise `ValueError` naming labels;
  unmaterializable/unhashable/uncomparable mappings raise
  `ValueError` (never the consumer's exception); `scalar_map=`
  refused; all other kwargs forwarded verbatim (incl. `InitVar`
  `auto_camel_case` via `name_converter`, `relay_max_results`).
  Varies on consumer scalars + upstream config fields -- both open
  by design.
- **Sites + roles.** Definition: `scalars.py::strawberry_config`
  (+ label helper J1). Consumers: `config/schema.py`,
  live-test schema builders, `extensions/debug.py` docstring shape.
  Oracles: the 18 factory/collision/hostile/passthrough rows in
  `tests/test_scalars.py`.
- **Challenges.** C4 counts 1; C5 counts 1.
- **Owner + lifetime.** This file (the map's home; the factory is
  the map's publish point). Per-call fresh dict; no cross-call
  state (P3 isolation proof) -- principle 4 satisfied by
  construction ("not cached" across calls, isolated within).
- **Behavioral proof.** P3 `execution-verified` (20 assertions).
- **Structural gate.** Collision/hostile/passthrough oracles each
  fail a distinct factory weakening (plain merge breaks absence;
  unguarded `dict()` leaks raw exceptions; dropped kwargs break
  the `InitVar` row).
- **Freshness.** Target as in R1.

### R6 -- `Upload` single re-export point (file-local)

- **Contract + variation.** `scalars.py::Upload` /
  `scalars.py::UploadDefinition` ARE Strawberry's builtin objects,
  re-exported, not wrapped (P4 `is`-proofs). The scalar itself is
  owned upstream (`strawberry.file_uploads.scalars`); this file
  owns only the package's single import point. No variation.
- **Sites + roles.** Upstream definition (external, authoritative
  for the scalar). Single package re-export here. Consumers (all
  `is`-identical, P6): root manifest (`Upload` only),
  `mutations/inputs.py` FILE branch, `forms/inputs.py` file
  triple, `rest_framework/serializer_converter.py` file
  annotation, scalars example-app schema. No second package
  definition exists (full-package grep: only `scalars.py` binds
  the names; all other hits are imports/uses/prose).
- **Challenges.** Any "second Upload source" change counts 0 --
  there is no second source; adding one would be the duplication,
  not the fix.
- **Behavioral proof.** P4 `execution-verified`.
- **Freshness.** Target as in R1; upstream strawberry-graphql
  0.324.0, graphql-core 3.2.8; `mutations/inputs.py`
  `fc4420475f404297822d7d94bee7bdd275700803`;
  `forms/inputs.py`
  `55614839ff479b3610b6026be65f2107ee560fcd`;
  `serializer_converter.py`
  `32904418a169941c2afa1c9cd6866c55debc64f3`.

### R7 -- Leaf manifest + root-surface note (file-local)

- **Contract + variation.** `scalars.py::__all__` publishes the
  four public names. Root re-exports three (`BigInt`, `Upload`,
  `strawberry_config`); `UploadDefinition` stays module-level.
- **Sites + roles.** Definition here (leaf manifest).
  `package-root-public-surface` (existing indexed family) owns the
  ROOT manifest decision. C12: no spec/glossary/oracle requires a
  root `UploadDefinition` (GLOSSARY upload entry names root import
  of `Upload` only; no test imports `UploadDefinition` from root;
  the factory annotates values with upstream `ScalarDefinition`,
  not `UploadDefinition`) -- routed observation, not a defect,
  no new row proposed.
- **Behavioral proof.** P4 manifest assertion
  `execution-verified`; root absence check `execution-verified`
  (`root.UploadDefinition` raises `AttributeError`).
- **Freshness.** Target as in R1; `__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`.

### F-reuse -- `typed-rejection-value-tail` (checked non-membership)

This file does NOT join the family: scalar `parse_value` /
`serialize` MUST raise Strawberry-contract `ValueError` /
`TypeError` (graphql-core maps such raises to field errors by type),
not framework typed rejections -- different contract, different
reasons to change. Its `_safe_type_name` / `_safe_arg_repr` uses
are CONSUMER uses of `exceptions.py` helpers (imported by name,
never redefined), which is composition, not membership. No index
change proposed.

### J1 -- hostile-metaclass-safe class-name rendering (rejection CONFIRMED, third site re-derived fresh)

Three bodies spell nearby rules; each encodes a distinct contract
with its own reasons to change (table re-derived from live imports
via probe P5, using the package oracles' own metaclass
`__getattribute__`-override hostile-double idiom):

| Site | Empty `__name__` | Non-string (42) | Unreadable | str-subclass (hostile dunders) |
|---|---|---|---|---|
| `exceptions.py::_safe_class_name` (shared) | repr `"''"` | repr of NAME (`"42"`) | `_safe_type_name` | plain `str` |
| `utils/querysets.py::_safe_class_name` (strict twin) | accepted `""` | metaclass label (never reprs the name object) | `_safe_type_name` | plain `str` |
| `scalars.py::_safe_scalar_map_key_label` (factory twin) | accepted `""` | repr of KEY | repr of KEY | plain `str` |

- **Contract differences.** Shared labels classes inside
  `ConfigurationError` prose across 8 modules: the repr rung keeps
  SOME rendering for malformed metadata, and `qualified` serves
  finalizer diagnostics. Strict labels the consumer queryset the
  sealed boundary is REJECTING: repr-dispatch on that very object
  could run hostile consumer code mid-rejection, so the fallback
  never touches the name object. Factory labels a dict KEY inside a
  factory `ValueError` (not a framework error at all) AND its
  `sorted()` call-site needs `__lt__`-safety the message sites never
  face. All three cells that CAN diverge DO diverge (P5); the
  easy cases agree, which is why textual search keeps false-flagging
  this trio.
- **Trigger (re-checked fresh, extended).** A change removing the
  sealed boundary's never-dispatch constraint, a `strict=` parameter
  the 8 shared consumers provably never set, a factory that stops
  sorting labels, or a fourth spelling with identical fallback +
  qualification -- any reopens the count. Measured today:
  constraints intact, oracles diverge, factory twin carries its own
  `sorted()` + `ValueError`-boundary reasons (plus the aliasing-key
  reachability: an `__eq__`-aliasing consumer key CAN surface in
  the intersection, so the labeler's hostile path is live, not
  hypothetical -- pinned by
  `test_strawberry_config_collision_message_survives_hostile_key`).
- **Durable home.** Existing split clause in
  `exceptions.py::_safe_class_name`'s docstring + `STRICTER` clause
  in `utils/querysets.py::_safe_class_name`'s docstring + the parity
  note on `scalars.py::_safe_scalar_map_key_label` (verified
  against its body). Plan index row already covers all three files
  -- no index change proposed.
- **Freshness.** Target as in R1; `exceptions.py`
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`;
  `utils/querysets.py`
  `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`;
  hostile oracles in `tests/test_scalars.py` + `tests/test_exceptions.py`
  `static-reviewed`.

### J2 -- converter-table ownership per surface (rejection, NEW row proposed)

Candidate considered: one shared field->scalar table for
`types/converters.py::SCALAR_MAP`,
`scalars.py::_PACKAGE_SCALAR_MAP`,
`forms/converter.py::_SCALAR_FORM_FIELDS`,
`rest_framework/serializer_converter.py::_SERIALIZER_FIELD_CONVERTERS`
(plus the scalars example app's `filters.py`/`orders.py`/`schema.py`
declarations as a possible fifth table).

- **Contract differences.** `SCALAR_MAP`: `models.Field` subclass
  -> Python/Strawberry scalar, shared read-output + filter-input
  contract with choice substitution layered by callers, mutable
  last-write-wins extension hook. `_PACKAGE_SCALAR_MAP`: scalar
  TYPE -> Strawberry `ScalarDefinition`, schema-registration
  contract, consumed once per `strawberry_config()` call. Form
  table: model-LESS `forms.Field` -> annotation + decode kind
  (relation/file kinds finalize at the build site; no `BigInt` or
  file rows by design). Serializer table: serializer-ONLY
  `serializers.Field` -> conversion (model-backed columns delegate
  to the read side's `convert_scalar`/`scalar_for_field` BY NAME,
  verified import line). Example-app declarations: consumer
  FilterSet/OrderSet wiring + rationale comments, no table at all.
  Key spaces pairwise disjoint (P6); value spaces disjoint
  (scalars vs annotations vs conversions vs definitions). What
  SHOULD be shared already is: model-backed write columns delegate
  to the read side rather than copying rows (principle 6, verified
  in all three flavors), and the write-side walks share the
  `utils/converters.py::convert_with_mro` mechanism with separate
  key spaces (principle 5/7 shape, owned elsewhere).
- **Trigger.** A new surface whose field population is a SUBSET of
  an existing table's key space with identical value contract and
  lifecycle (e.g. a second `models.Field`-keyed scalar map) would
  reopen the count. A new KIND of field population keeps its own
  table.
- **Durable home.** Each table's module docstring already states
  its key space and non-membership (`types/converters.py` file-row
  comment, `forms/converter.py` kind comment + module docstring,
  `serializer_converter.py` mirror comment, `scalars.py` module
  docstring contrast clause) -- verified by reading, plus this
  finding.
- **Index note for Worker 0.** Propose one `rejected` row:
  `converter-table-per-surface-ownership`, owner
  `types/converters.py::SCALAR_MAP` (first among equals only as
  index anchor; each table keeps its own owner), files covered
  `types/converters.py`, `scalars.py`, `forms/converter.py`,
  `rest_framework/serializer_converter.py`, holding item Family
  `converter-table-per-surface-ownership`.
- **Freshness.** Target as in R1; `forms/converter.py`
  `b717fd0f68bba4c50ee9883ed4a9ccd59b700a51`;
  `utils/converters.py`
  `5332f0542c0bd180aee30de95ec091933b54ee34`.

### Handoff (not a finding -- belongs to another item's target)

`types/converters.py::scalar_for_field` walks `type(field).__mro__`
with hash-based `in` against `SCALAR_MAP`, while
`utils/converters.py::convert_with_mro` (used by the form,
serializer, and filter flavors) reads the MRO through `type`'s raw
descriptor and scans identity-based, with comments explicitly
naming hostile-metaclass `__mro__` interception and hostile
`__hash__`/`__eq__` as the reasons. Whether the read side should
ride the shared skeleton (and whether its current plain walk is a
gap or a deliberate contract difference) is a verdict for the
`types/converters.py` file item, which owns both the walk and its
oracles -- recorded here only so the question is not mistaken for
examined-and-closed. No defect filed (no contract source read
states the read-side walk must be metaclass-hostile-safe).

## Defects

None. Every claim checked while tracing held: the 18-member census;
the `Upload`/default-registry contrast; the wire-symmetry loop; the
per-call factory isolation; the three hostile-containment shapes
with chained causes; the four key-space populations and their
disjointness; the `is`-identity of every `Upload` consumer; the
no-second-literal merge; the J1 three-way divergence; the tier
rationale in the package test header matching each oracle's tier.
The investigated boundaries (digit cap, `__index__`-only ints,
factory value validation, `UploadDefinition` root absence) each
lack a contract source and change what is accepted, so none is
filed. Nothing routed to any owner.

## Pending execution

None. All six probes already ran green against the shared tree;
each is read-only (imports + pure calls + `StrawberryConfig`
construction; no source mutation, no database, no Django settings
beyond import). No pytest was run in the shared tree, per item
rules; oracle bodies are `static-reviewed`. No
`execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres cells
are `inapplicable by construction`: the target's code path reaches
no database, alias, or dialect decision (pure total functions +
in-memory dict assembly + upstream config construction).

## Judgment

Backstop discharged: 18/18 `ast.Module.body` members enumerated,
12 challenges run (C1--C12, every variation axis of every rule),
six matrix axes discharged against the real surface, seven
file-local records with proving challenges (R1--R7), one reused
family checked as non-membership with its consumer relationship
named, two rejections with difference + trigger + home (J1
CONFIRMED fresh with a third-site divergence table, J2 proposed as
a new index row), zero defects, zero pending. The target owns its
rules singly: one grammar, one serializer, one binding, one map,
one factory, one re-export point. Zero-edit result is legitimate.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
e65545d8b61b5d11919bbbc0a206375e86d02fee --
django_strawberry_framework/scalars.py docs/dry/dry-file-scalars.md`
is empty for the target (working blob
`5e354042d405040f6137cebd39abe9c042ffece8` equals the item
baseline member and `HEAD:` -- target CLEAN, so no hunk
attribution was owed); the artifact itself is this new file. The
`## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never
touched. Concurrent dirt (`django_strawberry_framework/connection.py`
hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never edited, reverted, or
tidied, verified by content-diff scoping (`git status --short`
shows the same five dirty paths before and after, plus only the
ignored scratch below). Scratch (ignored, kept for Worker 2
re-run): `docs/dry/temp-tests/dry-file-scalars/p1_ast_census.py`,
`p2_bigint_matrix.py`, `p3_config_factory.py`,
`p4_upload_identity.py`, `p5_j1_divergence.py`,
`p6_table_census.py`. No `ruff` run owed (no tracked edits). Do
not commit.

## Independent verification (Worker 2)

Worker 2 re-derived from the target + connected bodies + probe
re-runs (`django_strawberry_framework/scalars.py::._parse_bigint`,
`django_strawberry_framework/scalars.py::._serialize_bigint`,
`django_strawberry_framework/scalars.py::BigInt`,
`django_strawberry_framework/scalars.py::_PACKAGE_SCALAR_MAP`,
`django_strawberry_framework/scalars.py::strawberry_config`,
`django_strawberry_framework/scalars.py::Upload`,
`django_strawberry_framework/scalars.py::__all__`,
`django_strawberry_framework/scalars.py::_safe_scalar_map_key_label`;
read `django_strawberry_framework/types/converters.py`,
`django_strawberry_framework/utils/converters.py::convert_with_mro`,
`django_strawberry_framework/exceptions.py`,
`django_strawberry_framework/utils/querysets.py::_safe_class_name`,
`django_strawberry_framework/__init__.py`,
`django_strawberry_framework/management/commands/inspect_django_type.py`
`"_GRAPHQL_SCALAR_NAMES"`, `tests/test_scalars.py` header). Own
trace before reconciling (counts = authoritative definitions
only):

- BigInt input grammar: 1 (`scalars.py` pattern + parser, one
  body). Owner: this file. Agree R1.
- BigInt output serializer: 1 (same file, round-trip half of the
  same symmetry contract). Owner: this file. Agree R2.
- BigInt identity + binding (`NewType` Python identity vs
  `strawberry.scalar(name=)` GraphQL name): 1 owner holding two
  distinct-contract spellings (C11). Owner: this file. Agree R3.
- Scalar map + `Upload` absence: map 1 (this file);
  `Upload` scalar itself owned upstream
  (`strawberry.file_uploads.scalars`), single package re-export
  here, absence deliberate (default-registry resolution, P4
  re-run: 17 entries, `Upload` in / `BigInt` out). Owner split
  as W1 states. Agree R4/R6.
- Config factory (`strawberry_config` isolation + collision +
  hostile containment + `scalar_map=` refusal + kwarg
  passthrough): 1. Owner: this file (map publish point). P3
  re-run green (20 checks). Agree R5.
- Leaf manifest (`__all__` 4 names; root re-exports 3,
  `UploadDefinition` stays module-level): leaf owned here, root
  decision owned by `package-root-public-surface`. C12 routed
  observation, not a defect, no new row. Agree R7.
- Converter tables: `types/converters.py::SCALAR_MAP` (26
  `models.Field` keys) vs `scalars.py::_PACKAGE_SCALAR_MAP` (1
  scalar-type key) vs `forms/converter.py::_SCALAR_FORM_FIELDS`
  (12 `forms.Field` keys) vs
  `rest_framework/serializer_converter.py::_SERIALIZER_FIELD_CONVERTERS`
  (16 `serializers.Field` keys); P6 re-run confirms populations
  + three-space disjointness + `Upload` `is`-sharing +
  `BigAutoField -> int` vs 64-bit -> `BigInt`. Four contracts,
  four owners; sharing already correct (model-backed write
  columns delegate to the read side by name; write walks share
  `utils/converters.py::convert_with_mro` skeleton with separate
  key spaces). Unification refused. **J2 ENDORSED as rejected**
  (exact index row below).
- Hostile-label third site
  (`exceptions.py::_safe_class_name` shared vs
  `utils/querysets.py::_safe_class_name` strict twin vs
  `scalars.py::_safe_scalar_map_key_label` factory twin): P5
  re-run confirms all three diverging cells (non-string 42:
  repr-of-name vs metaclass label vs repr-of-key; empty:
  `repr("")` vs `""` vs `""`; unreadable: shared/strict
  metaclass label vs factory repr-of-key; str-subclass all
  plain-`str` with factory additionally `sorted()`-safe). Three
  contracts, three owners. **J1 CONFIRMED, no index change**
  (existing row already covers all three files; durable home
  verified: `exceptions.py::_safe_class_name` docstring split
  clause + `utils/querysets.py::_safe_class_name` `STRICTER`
  clause + factory parity note).
- Tail checked-non-membership
  (`typed-rejection-value-tail`): agree non-member. Scalar
  hooks MUST raise Strawberry-contract `ValueError`/`TypeError`
  (graphql-core maps by type); framework typed rejections are a
  different contract. `_safe_type_name`/`_safe_arg_repr` uses
  are by-name consumers, not definitions. No index change.
  Agree.

### Enumeration (member-by-member vs own count)

P1 re-run: 18 members, 0 `AsyncFunctionDef`, 0 `ClassDef`.
Independent `ast.Module.body` walk matches W1's 18 rows
1:1 (docstring projection; 8 imports incl. upstream re-export
source + helper imports as consumers; `__all__` leaf R7;
pattern + parser R1; serializer R2; `BigInt` + binding R3; map
R4; factory R5; labeler J1). No member unassigned, no hidden
19th. Tail F non-member correctly excluded (consumer, not
definition). Agree.

### Matrix vs real surface

1. Cross-flavor: searched, agree (P6 census re-run green;
  order-inputs non-mirroring + `lateral_fetch` name-string set
  correctly distinguished as different contracts).
2. Sync/async: inapplicable by construction, agree (0/0
  instrument + no ORM/await/transaction in target; factory
  configs consumed by async suites does not color the factory).
3. Derived knowledge: searched, agree (C11 two-spellings-one-owner
  with distinct contracts; map + namer + labels derive by name).
4. Round-trip pair: co-owned halves, agree (P2 re-run: 14
  accept + 21 `ValueError` + 2 structural parser cases, hostile
  normalization both directions, 6 `TypeError` outputs, 7-value
  symmetry loop, digit-cap boundary investigated not filed).
5. Other media: 1 definition per rule, roles correct (module
  docstring/GLOSSARY/CHANGELOG projections; `tests/test_scalars.py`
  46 members re-counted as oracles with live-vs-package tier
  rationale verified in header; live `test_scalars_api.py` /
  filter / uploads wire oracles; example-app + `config/schema.py`
  consumers). No oracle rewritten to read from its owner (oracles
  spell literals/identities; namer derives FROM the map, the
  direction composition requires). Agree.
6. Omission: family enumerated with contract source per absence,
  agree (Upload absence + serializer-`str` refusal pinned by
  oracles; factory value validation / `__index__`-only /
  `BigAutoField` / digit-cap investigated with no contract source
  and accept-changing, so not defects).

### Counts + roles; equivalence

C1--C12 counts agree (C1 1; C2 1; C3 refused-1; C4 1; C5 1; C6
refused-1; C7 1; C8 0 here; C9 refused J2; C10 refused J1; C11 1
same-file distinct contracts; C12 0 here routed). Roles agree
throughout. Observable equivalence (principle 8): zero-edit, so
no migration to prove; P2/P3/P4/P6 re-runs are
`execution-verified` for the CURRENT behavior (wrong results
rejected: forged subclass serialization, hostile-key escape,
map-aliasing, `Upload` second source, grammar drift); oracle
bodies `static-reviewed` (no shared-tree pytest per item rules).
`FAKESHOP_SHARDED=1`/Postgres `inapplicable by construction`
accepted: pure functions + in-memory dict assembly + upstream
config construction reach no DB/alias/dialect.

### Zero-edit, J2 ruling, handoff

`git diff e65545d8b61b5d11919bbbc0a206375e86d02fee --
django_strawberry_framework/scalars.py` empty (re-run);
working blob `5e354042d405040f6137cebd39abe9c042ffece8` equals
`HEAD:` (target clean, no hunk attribution owed). Coverage +
assignment validated (18/18 + F/J routing above); file item owes
no production edit and none was made. **J2 ruling: ENDORSED.**
Worker 0 should add one `rejected` index row + one family item
(exact text under `## Judgment`). **Handoff: CONFIRMED
RECORDED.** `types/converters.py::scalar_for_field` plain walk
(`type(field).__mro__` + hash `in`) vs
`utils/converters.py::convert_with_mro` hostile-safe walk (raw
descriptor + identity scan + documented metaclass/`__hash__` /
`__eq__` reasons) is explicitly marked not-examined-not-closed
for the `types/converters.py` item, with no defect filed (no
contract source requires the hardened walk there). The later
item must pick it up; nothing here pre-judges it.

### Rejections / fingerprints / gates / pending / coupling

Both rejections carry contract difference + trigger + durable
home (J1 trigger extended with aliasing-key liveness +
`sorted()` reason; J2 trigger = subset-population same-contract
surface). Freshness re-hashed: target `5e354042…` (working =
`HEAD:`), `tests/test_scalars.py` `b9819c14…`,
`test_scalars_api.py` `8c09e9b5…`, `types/converters.py`
`9ceb34af…`, `forms/converter.py` `b717fd0f…`,
`utils/converters.py` `5332f054…`, `exceptions.py`
`e06b0b7f…`, `utils/querysets.py` `1539b66c…`, `__init__.py`
`0ef72601…`, `inspect_django_type.py` `46dffb3d…`,
`mutations/inputs.py` `fc442047…`, `forms/inputs.py`
`55614839…`, `serializer_converter.py` `32904418…` -- all match
artifact. Gates: the four named oracles exist in
`tests/test_scalars.py` (`test_bigint_serialize_rejects_non_int_types`,
`test_strawberry_config_scalar_map_excludes_upload`,
`test_upload_field_resolves_under_plain_strawberry_config`,
`test_strawberry_config_collision_message_survives_hostile_key`);
negative-control reasoning inspected and sound (each weakening
breaks its named oracle); full `prove_failability.py` mutation
not run (not authorized in a file item; recorded as
`static-reviewed` gate justification, not an execution claim).
`## Pending execution`: absent, correctly (all probes read-only,
already green; no pytest owed). Coupling: none introduced;
handoff explicitly decoupled. Agree.

### AGENTS.md prose check

Item-scoped diff empty for tracked paths (artifact itself is the
only new file, untracked); no process provenance, citations use
`path::Symbol` (with `"quoted substring"` where line-local),
tests stay at mandated tiers (hostile/direct-call/factory rows
in `tests/`, wire rows live in `test_query/`), no version/
changelog/commit/branch action. No violation. Concurrent dirt
(`connection.py`, `test_connection.py`, staged
`tests/utils/test_querysets.py`, `bug_hunt-0_0_15.md`,
`dry-0_0_15.md`, plus the untracked verified dry-file artifacts)
left untouched; `git status --short` shows only expected
evolution since W1 (new sibling artifacts from concurrent
items), no edits by this verification.

### Defects (Worker 2)

None (no new entries). All W1 non-filings re-checked
(digit cap, `__index__`-only, factory value validation, root
`UploadDefinition` absence -- each lacks a contract source and
changes what is accepted). No security/routing/auth impact.

## Defects (Worker 2)

None.

## Judgment (Worker 2)

`Status: verified`. Zero-edit backstop legitimately discharged:
18/18 enumerated, 12 challenges with agreed counts, 6 matrix axes
discharged against the real surface, R1--R7 file-local, F
non-membership + J1 confirmation + J2 new rejection all agreed,
handoff recorded for `types/converters.py`, fingerprints all
match, gates sound, no pending, no coupling, no AGENTS.md
violation, no defects. Worker 0 actions: tick File `scalars.py`;
append the J2 `rejected` responsibility-index row + family item
exactly as below (release `0.0.15`, run `0.0.15 2026-09-18-1`).

Exact index row:

`| converter-table-per-surface-ownership |
types/converters.py::SCALAR_MAP (index anchor only; each table
keeps its own owner) | types/converters.py, scalars.py,
forms/converter.py, rest_framework/serializer_converter.py |
Family converter-table-per-surface-ownership | rejected |`

Exact family item:

`- [ ] Family converter-table-per-surface-ownership —
[dry-rule-converter-table-per-surface-ownership.md](dry-rule-converter-table-per-surface-ownership.md)`

Confirm (Worker 2, hash-fix re-pass): R6 line 409 now carries the correct 40-char blob id matching `git hash-object`; corrupt literal survives only as the historical quote in the `## Iterations` note; my line-785 truncated-prefix "all match" claim needs no amendment (it compared 8-hex prefixes, and the full-literal fault was in W1's R6 line, not that list); `Status: verified` stands.

## Iterations (hash fix)

Micro-fix pass: replaced the corrupt 32-char R6 Freshness fingerprint for `serializer_converter.py` (`32904418a169941c2afa1c99debc64f3`) with the Worker-0-verified 40-char blob id `32904418a169941c2afa1c9cd6866c55debc64f3` (reproduced via `git hash-object` on the clean worktree path); no other artifact, production, or ledger change.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
