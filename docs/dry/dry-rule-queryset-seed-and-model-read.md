# DRY review: `queryset-seed-and-model-read`

Status: verified
Run: 0.0.15 2026-10-01-9

Family `queryset-seed-and-model-read`. Owner candidate
`django_strawberry_framework/utils/querysets.py::model_for` — CONFIRMED
as one of three co-owners (strict type-to-model read, model-keyed seed,
type-keyed wrapper), not inherited. Indexed files (10):
`django_strawberry_framework/utils/querysets.py`, `relay.py`,
`types/relay.py`, `mutations/resolvers.py`, `permissions.py`,
`connection.py`, `optimizer/walker.py`, `list_field.py`,
`filters/base.py`, `filters/sets.py`. Trace at HEAD `5c3496e0` bytes;
`ITEM_BASELINE=2f54885689d9ee60d1da04a0b815ff686de8e652`. Prior
records (file-item F-findings, the run-7 types/relay adoption) used
only as population hints; every verdict below re-derived fresh. Never
read any `worker-memory/`.

Verdict in one line: F1 CONFIRMED (relay's inline manager-plus-using
seed is a second definition of the model-keyed seed, count 2) but
BLOCKED on concurrent non-ledger dirt — zero edits; F2 already
single-owned (count 1); ten rejections carry contract differences plus
triggers.

## System trace

The family covers two coupled mechanisms: (a) reading the Django
model a seed or a check runs against, and (b) seeding a fresh
unevaluated base queryset from that model. The package answers (a)
for the strict registered-type question in exactly one body,
`utils/querysets.py::model_for` (direct
`type_cls.__django_strawberry_definition__.model` read, raw
`AttributeError` when absent), and (b) in exactly one body,
`utils/querysets.py::base_queryset`
(`model._default_manager`, conditional `.using()`, `.all()`), with
`utils/querysets.py::initial_queryset` as its type-keyed wrapper
(`base_queryset(model_for(type_cls))`, one line, composing by name).

Whole-package sweep over all 119 `django_strawberry_framework/`
`.py` files for the mechanism vocabulary (`model_for`,
`initial_queryset`, `base_queryset`, `_default_manager`,
`_base_manager`, `__django_strawberry_definition__`, `.model`,
`.objects.`, `model_for_type`, `related_model_of_queryset`,
`require_queryset_related_model`, `annotate_queryset_relation`):
`model_for` has 17 executable call sites in 5 files, every one a
by-name consumer; `initial_queryset` has 9 in 4 files plus its own
docstring mentions; `base_queryset` has 8 in 8 files; the only
executable `_default_manager` reads outside the owner are relay's
two NodeID-lookup shapes (F1). Every other model derivation follows
a different authority's API (registry map, in-hand definition,
django-filter `Meta`, Django relation field, Django queryset) and is
adjudicated under Findings as its own rule or an exclusion.

Attribution: every dirty hunk in the 10 indexed files was diffed
against `git show HEAD:<path>`. None matches a `## Owned changes`
ledger row (the ledger holds no production row on any of the 10;
its one relay-adjacent row is an adopted trigger docstring whose
content is present but far from the seed lines). All other dirt is
concurrent work, left untouched. In particular the entire WT-only
`relay.py::_resolve_real_pks_batched` function and the WT-only
`relay.py::_decode_and_coerce` function are non-ledger concurrent
dirt; the F1 consolidation would have to edit the former, so it is
`blocked-on-hunt` per the dispatch procedure: hunk recorded, tree
untouched. No `## Implementation (Worker-1)` section follows: zero
tracked files changed.

## Verification

### Matrix

1. Cross-flavor policy mirroring — discharged by the caller
   census. Model, form, and serializer write flavors seed
   relation-visibility through the single shared spines
   (`visibility_scoped_related_queryset`,
   `related_visibility_queryset`, `related_visibility_queryset_or_default`
   in `utils/querysets.py`); form plus serializer column-less
   relation typing shares `mutations/inputs.py::annotate_queryset_relation`
   by name (`forms/inputs.py:481`,
   `rest_framework/serializer_converter.py:794`). No flavor
   re-spells a seed or a strict type-to-model read.
2. Sync/async twins — no twin exists. Negative sweep for
   `abase_queryset`, `ainitial_queryset`, `amodel_for`, and any
   async-qualified seed call: zero hits. Seeds are lazy querysets
   valid in both colors from one sync body: the connection async
   branch takes no default seed (resolver-required;
   `connection.py:2110`), the list field seeds once then
   dispatches per call (`list_field.py:1620`), and the Relay node
   sync/async twins each call `initial_queryset` by name
   (`types/relay.py:1047` vs `:1072`, `:1114` vs `:1139`, `:1116`
   vs `:1141`). The colored visibility runners are the
   sealed-execution family's twins, out of scope.
3. Derived rather than repeated knowledge — discharged by
   authority. The model reaches a seed from six sources
   (registration slot, registry map, in-hand definition,
   filterset `Meta`, relation field, queryset attribute); each
   follows its own authority's API with its own reasons to
   change, and the three package-owned derivations are each
   single-bodied with distinct contracts (F2, R1, R2). The only
   direct slot read for the model fact is the owner's body; the
   remaining slot spellings read different facts (R3) or the
   definition object for identity comparison (R3, R5).
4. Inverse / round-trip pairs — model-to-type (`registry.get`,
   `types_for`, `primary_for`) vs type-to-model (`model_for`,
   `model_for_type`): opposite directions over different stores
   (registration index vs class slot), each direction single.
   Queryset-to-model is Django-owned attribute storage; the
   package owns only the model-to-queryset seed (R6). No pair
   hides a second definition.
5. Contracts restated in another medium — oracles state
   expectations independently: `test_model_for_returns_registered_model`
   asserts identity with `Category`, `test_initial_queryset_uses_default_manager`
   asserts default-manager seeding, and the three
   `test_model_for_type_*` rows pin the None-tolerant arms
   without reading either owner. The mutation resolver tests
   mock `model_for` / `initial_queryset` by module attribute
   name, pinning call-unity weakly. Live NodeID suites pin the
   F1 lookup behavior end to end. Projections: the three owner
   docstrings (including the relay-exclusion clause and the
   type-vs-model keying clause), the START.md verified
   FilterSet child-seed separation, and the file-item consumer
   records. No test re-spells a seed body.
6. Enforcement by omission — the seed population enumerated,
   every member checked: list default, connection default, node
   defaults (sync plus async), mutation locate, mutation
   refetch, cascade per-edge base, filter child base, filter
   `get_queryset` fallback, walker prefetch child, type
   relation recheck, related-visibility default — all seed
   through `base_queryset` / `initial_queryset` by name. The
   relation connection seeds from the parent's relation manager
   by documented design (R8). The optimizer root coerces a
   consumer source instead of seeding (no surface by
   construction). Auth carries no seed surface (zero
   `model_for` / seed calls in `auth/mutations.py` plus
   `auth/queries.py`). No member lacks a guard its contract
   requires; F1 is a second spelling, not an omission.

### Enumeration

Family item: the sweep population stands in for a file-member
enumeration. Instruments plus counts (WT bytes; docstring-only
mentions excluded from call counts):

- `model_for(` executable calls: 17, in 5 files —
  `types/relay.py` x4 (`:139`, `:211`, `:433`, `:998`),
  `mutations/resolvers.py` x5 (`:284`, `:724`, `:928`, `:1172`,
  `:1400`), `utils/querysets.py` x2 internal (`:337`,
  `:4258`), `relay.py` x4 (`:165`, `:323`, `:357`, `:407`),
  `permissions.py` x1 (`:623`). Definition: 1
  (`utils/querysets.py:266`).
- `initial_queryset(` executable calls: 9, in 4 files —
  `types/resolvers.py:464`, `types/relay.py` x6 (`:1047`,
  `:1072`, `:1114`, `:1116`, `:1139`, `:1141`),
  `mutations/resolvers.py` x2 (`:728`, `:877`),
  `utils/querysets.py:4550`. Definition: 1
  (`utils/querysets.py:325`), a one-line composer.
- `base_queryset(` executable calls: 8, in 8 files —
  `filters/sets.py:2859`, `filters/base.py:1466`,
  `optimizer/walker.py:592`, `utils/querysets.py:337`,
  `utils/querysets.py:4602`, `connection.py:2153`,
  `permissions.py:710`, `list_field.py:1620`. Definition: 1
  (`utils/querysets.py:280`).
- Executable `_default_manager` reads outside the owner: 2 —
  `relay.py:323`, `relay.py:407` (F1).
- Executable `_base_manager` reads: 4 — `optimizer/predicates.py:79`,
  `utils/write_transaction.py:1168`, `utils/write_transaction.py:1261`,
  `rest_framework/resolvers.py:2067` (R7).
- `__django_strawberry_definition__` executable spellings: 9
  line-sites — owner body (`utils/querysets.py:277`), writer
  (`types/base.py:891`), base self-read (`types/base.py:928`),
  validator (`list_field.py:190`), stamp probe
  (`relay.py:580`), name reads (`relay.py:233`, `:234`), CLI
  check (`management/commands/inspect_django_type.py:163`),
  test helper (`testing/relay.py:73`) (F2, R2, R3, R5).
- `registry.model_for_type` definition: 1 (`registry.py:411`);
  callers: 3 (`optimizer/extension.py:886`, `:1695`,
  `management/commands/inspect_django_type.py:204`) (R1).
- `related_model_of_queryset` spine: 1 definition
  (`mutations/inputs.py:397`) plus its raising half (`:409`)
  and flavor spine (`:426`); both flavors compose by name
  (R6).
- `definition.model` / `definition, model` executable reads:
  20+, all attribute reads off an already-resolved definition
  object, none performing a lookup (R4).

### Challenges

Each change posited against the rule's variation axes; only
authoritative definitions counted.

- C1 (seed manager choice): seeds must stop reading
  `_default_manager` (whatever replaces it). Moves:
  `base_queryset` plus relay's inline shape at `:323` and
  `:407` (one inline shape, two instances). Count: 2.
- C2 (seed alias pinning): the conditional-`.using()` pinning
  semantics change. Moves: `base_queryset` plus the same
  inline shape (it re-spells the conditional pin). Count: 2.
- C3 (seed detachment): every seed must detach via `.all()`.
  Moves: relay's inline shape only (the owner already
  detaches). Count: 1 — the delta that makes the inline
  shape a weaker instance of the same rule, not a distinct
  one: it answers the same question (rows of model M on
  alias A) with a behaviorally vacuous omission at these
  sites (verified against Django 6.1 `manager.py:157` plus
  `query.py:1640` / `:1971`: `Manager.filter` delegates to
  `get_queryset().filter`, `Manager.all()` is
  `get_queryset()`, `QuerySet.using` pins `_db` on a clone).
- C4 (strict read source): the registration slot moves or the
  read must survive it. Moves: `model_for` only (the
  registry map is populated from the `register()` call's
  model argument, not the slot). Count: 1.
- C5 (strict read error contract): unregistered input must
  yield `None` instead of raising. Moves: `model_for` only
  (its callers rely on fail-loud; the None-tolerant
  population already has its own owner, R1). Count: 1.
- C6 (probe None-arms): `model_for_type` must raise on
  scalars or stop accepting `None`. Moves: the registry
  probe only (the optimizer's scalar-origin call at
  `optimizer/extension.py:886` cannot route through the
  strict read). Count: 1.
- C7 (seed keying): the type-keyed seed must stop resolving
  through the registered type. Moves: `initial_queryset`
  only (one line; `base_queryset` untouched). Count: 1.
- C8 (relation-child seed model): a prefetch child must seed
  from the registered type instead of `field.related_model`.
  Moves: the walker call site only (a caller decision, and
  the wrong one: the relation's model may be a strict
  subclass of any registered type's model). Count: 1, and
  the caller's choice, not a definition.
- C9 (registry cleared mid-request): `TypeRegistry.clear()`
  runs between type resolution and model read. Moves:
  nothing — but the two probes diverge observably (map
  empties, class attribute survives; `registry.py:646`
  clears maps only, nothing deletes the slot), which is the
  behavioral proof that F2 and R1 are distinct contracts.
- C10 (consumer metaclass lies about the slot): a hostile
  `__getattribute__` on a consumer type. `model_for`
  (direct access, metaclass dispatch) vs the stamp probe
  (truthful read, no dispatch) diverge — the behavioral
  proof that F2 and R2 are distinct contracts.

## Findings

### F1 — model-keyed seed (CONFIRMED duplication, blocked-on-hunt)

- **Contract + variation.** A fresh unevaluated base queryset
  for a model, optionally pinned to a database alias: the
  model's `_default_manager`, conditional `.using()`,
  detached via `.all()`. Varies on the alias only; the
  manager choice (`_default_manager`) is the rule's fixed
  answer.
- **Sites + roles.** Definitions (2): `utils/querysets.py::base_queryset`
  (owner) plus relay's inline manager-plus-conditional-`using`
  shape, one shape in two instances —
  `relay.py::_resolve_real_pk` (WT `:321`-`:326`, HEAD
  `:302`-`:307`, byte-identical) and
  `relay.py::_resolve_real_pks_batched` (WT `:404`-`:415`,
  no HEAD lines: the whole function is WT-only concurrent
  dirt). Consumers of the owner (8 call sites, all by
  name): `filters/sets.py:2859`, `filters/base.py:1466`,
  `optimizer/walker.py:592`, `utils/querysets.py:337`,
  `utils/querysets.py:4602`, `connection.py:2153`,
  `permissions.py:710`, `list_field.py:1620`. Oracles: the
  live NodeID suites (`test_multi_db.py`, incl. the sharded
  alias-pinning rows; `test_library_shapes_api.py`) plus the
  transitive `test_initial_queryset_uses_default_manager`.
  Projection: the `base_queryset` docstring's relay-exclusion
  clause (HEAD `:310`, WT `:293`-`:294`, committed
  context) — a description, not a reason: it states that
  relay takes the raw manager but no load-bearing why, and
  the fresh trace finds none.
- **Challenges.** C1 count 2, C2 count 2, C3 count 1 (weaker
  instance, vacuous at these sites — Django-source proof in
  C3). A grep for the seed population (`base_queryset`)
  misses both relay instances: the drift vector this
  consolidation closes.
- **Owner + lifetime (principles 7, 4).**
  `utils/querysets.py::base_queryset` stands: every
  legitimate consumer already imports from that module
  (`relay.py` imports `model_for` from it today, so no new
  dependency and no reversed edge), it is the narrowest
  module holding seed responsibility, and its module
  docstring records the cycle-safe import position. Pure
  derivation per call: no stored state, no lifetime owed.
- **Migration (deferred by the block).** Each relay instance
  becomes `base_queryset(model_for(resolved_type),
  using=using)` (plus the import name), dropping the
  `Manager | QuerySet` union annotation and the duplicated
  comment; the `base_queryset` docstring's relay-exclusion
  clause is deleted in the same edit. Net about minus 8
  lines. Both instances must move together: consolidating
  the HEAD-clean single shape while the batched twin stays
  inline would trade twin-consistency for a new divergence.
- **Distinct behavior.** None stays behind: the chained
  `.filter().values_list().first()` / `__in` lookup, the
  pipeline-alias recovery above each site (an adjacent rule
  reported below, out of this family's scope), and the
  `id_attr == "pk"` early-outs are untouched.
- **Behavioral proof.** `static-reviewed`: site-by-site
  equivalence against Django 6.1 `Manager.all` /
  `QuerySet.all` / `QuerySet.using` bodies (shared venv
  source read, not executed) plus the no-`isinstance`
  no-Manager-only-method check on both chains. One
  unsupported-state delta stated and dismissed: a custom
  manager overriding `.all()` to return a non-queryset
  would break the owner call while the raw-manager chain
  survives — that violates Django's documented
  `Manager.all()` contract, the package already routes
  every other seed through `.all()`, and no test or
  docstring pins relay's accidental survival.
  `execution-deferred`: the post-block focused run plus
  the sharded alias rows (see `## Pending execution`).
- **Structural gate.** None behaviorally possible: the
  inline shape and the owner call are observationally
  identical, so a hand-copy negative control passes every
  oracle (same standard as the verified target-guard
  item). Unity will rest on this census plus the
  docstring-clause deletion plus the trigger below.
- **Coupling.** Blocked on concurrent non-ledger dirt: the
  WT-only `relay.py::_resolve_real_pks_batched` function
  (the consolidation must edit its WT `:404`-`:415`
  manager lines, which exist nowhere at HEAD) and the
  surrounding WT-only `_decode_and_coerce` plus the
  `_resolve_real_pk` slot-parametrization. The dirt is not
  hunt-ledgered and matches the run-9 maintainer-merge
  character; treated as `blocked-on-hunt` per the dispatch
  procedure either way. Nothing touched.
- **Freshness.** `relay.py` WT `63bbba0b` / HEAD `037723cd`;
  `utils/querysets.py` WT `3e392d48` / HEAD `69ac3ea3`;
  Django `6.1` venv source; oracles as fingerprinted below.
  Any fingerprint change reopens.
- **Reconsideration trigger.** The concurrent batched-decode
  code landing (committed) re-arms this consolidation:
  both relay instances route through `base_queryset` in one
  change, or the family re-litigates with the landed shape.
  Durable home until then: this finding.

### F2 — strict type-to-model read (single-owned, count 1)

- **Contract + variation.** The Django model registered to
  a `DjangoType`, read off the registration slot, failing
  loud (`AttributeError`) for anything unregistered. No
  legitimate variation: the slot and the failure are the
  rule.
- **Sites + roles.** Definition (1):
  `utils/querysets.py::model_for`. Consumers (17,
  Section `### Enumeration`): the Relay slot/coerce/decode
  reads, the node resolve defaults' `DoesNotExist` raisers,
  the write pipeline's locate/decode/delete reads, the
  cascade root read, and the two internal composers
  (`initial_queryset`, `_captured_model`). Oracles:
  `test_model_for_returns_registered_model` (independent:
  asserts identity with `Category`, never via the owner).
  Projection: the owner docstring's consumer list.
- **Challenges.** C4 count 1, C5 count 1. The slot NAME is
  spelled at 9 line-sites, but a shared string is not a
  shared rule: no variation axis moves a dunder slot name,
  so a name constant would relieve no change obligation
  (principle 11); each spelling's contract is adjudicated
  in R2/R3/R5 instead.
- **Owner + lifetime.** `utils/querysets.py::model_for`
  stands (principle 7: narrowest module every consumer
  already imports; cycle-safe). Pure per-call read, no
  lifetime.
- **Migration.** None — already single.
- **Behavioral proof.** `static-reviewed` (owner body plus
  all 17 call sites read; unity is observable in the
  census). No execution owed: nothing moves.
- **Structural gate.** None owed: single ownership plus the
  fail-loud contract (a bypass re-spelling the slot read
  identically is behavior-preserving; a divergent one
  fails the oracles).
- **Freshness.** Same input fingerprints as F1 plus
  `types/relay.py` WT `9903f6ea` / HEAD `2d1efd00`,
  `mutations/resolvers.py` WT `2ff49673` / HEAD `d77a6c68`,
  `permissions.py` WT `87271361` / HEAD `9edd4cf5`.

### R1 — registry model probe (rejected: None-tolerant contract)

`registry.py::model_for_type` answers a different question:
model for ANY probe object (scalar origins, `None`
itself), `None` when unregistered, sourced from the
registry map rather than the class slot. C6 count 1; C9
proves the contracts diverge observably (`clear()`
empties the map, the slot survives). Its three callers
need exactly the tolerant arms. Trigger: a caller
needing fail-loud from the map, or the slot ceasing to
be the store — then one probe absorbs the other.

### R2 — stamp best-effort probe (rejected: trust contract)

`relay.py:580`-`:581` reads the slot truthfully (no
metaclass dispatch) and tolerates absence, feeding the
copy-before-stamp gate. `model_for` reads with metaclass
dispatch and raises. C10 proves the divergence; routing
the stamp through the strict read would weaken a trust
posture, which is never behavior-preserving (principle
8). Trigger: the strict read ever going truthful, or the
threat model explicitly excluding consumer metaclasses.

### R3 — definition-identity validation reads (rejected: different rule)

`list_field.py:190`, `testing/relay.py:73`, and
`management/commands/inspect_django_type.py:163` read the
DEFINITION object for presence/identity comparison, not
the model; the model (where needed) comes later off the
validated object. The list-field check belongs to the
verified target-guard family; the test-helper check is
homed in the open `registered-djangotype-definition-validation`
family row. Trigger: any of these sites needing the
model without the identity check — then it composes
`model_for`.

### R4 — reads off an in-hand definition (rejected: no lookup)

The 20+ `definition.model` reads (connection pipelines,
keyset state, list `_model_from_definition`, strategy
helpers, finalizer, inspect table) perform no lookup:
the definition object is already resolved and threaded
down. Consolidating attribute access into a lookup
helper would be machinery hiding the threading
discipline the call sites document. Trigger: a site
re-resolving the definition to reach `.model` — then it
joins F2's population.

### R5 — declaration and writer side (rejected: declare vs read)

`types/base.py:891` (slot assignment),
`types/base.py:698` (`Meta.model` validation), and
`types/base.py:928` (self-read) own declaring and
validating the slot. Reading what they wrote is F2's
direction, not a second copy of it. Trigger: the
declaration ceasing to be the slot's single writer.

### R6 — queryset-to-model direction (rejected: opposite direction)

`queryset.model`, `related_model_of_queryset` plus its
raising/flavor halves (`mutations/inputs.py:397`, `:409`,
`:426`, both flavors composing by name), `field.model`,
and the optimizer's `queryset.model` guards read the
model a query object already carries — Django-owned
storage in the attribute case, an already-single spine
in the helper case. The family owns the reverse
direction (model to seed). Trigger: a queryset-model
read re-deriving through a type lookup — then it joins
F2.

### R7 — base-manager probes (rejected: deliberate bypass)

The four `_base_manager` sites (`optimizer/predicates.py:79`,
`utils/write_transaction.py:1168`, `:1261`,
`rest_framework/resolvers.py:2067`) deliberately bypass
default-manager filtering for locks, existence, and
attestation — each documents why replaying the default
filter would corrupt its answer. A seed-manager change
(C1) must NOT move them. Trigger: locks or attestation
ever required to respect default filtering.

### R8 — relation-manager seeds (rejected: parent-scoped rows)

`connection.py::_build_relation_connection_resolver`
(`getattr(root, accessor).all()`), the serializer M2M
attestation read, and the prefetch cooperation seam seed
from a PARENT'S relation manager, preserving prefetch
caches and relation scoping the table seed cannot
provide. Table-seed changes must not move them.
Trigger: a relation seed ever needing unscoped table
rows — then it composes `base_queryset`.

### R9 — manager coercion (rejected: validation, not seeding)

`utils/querysets.py::_coerced_manager_queryset` coerces
a consumer-supplied `Manager` with fail-closed alias
preservation — a trust boundary over hostile input, not
a seed over a trusted model manager. Trigger: seeds
ever accepting untrusted managers — then they route
through the coercion first.

### R10 — type-keyed wrapper (confirmed composition, not duplication)

`initial_queryset` is defined as
`base_queryset(model_for(type_cls))`: one body, one
line, composing both owners by name. The keying split
(type vs model) is load-bearing — relation children
must seed from the relation's own (possibly
subclass) model, never the registered type's — and is
recorded at the owner plus the START.md verified list.
Trigger: a caller seeding a relation child through the
registered type — that is a defect, not a variation.

### Sub-rule reported for Worker-0 indexing (not consolidated here)

`write-pipeline-alias-recovery`: the NodeID `using`
recovery twins (`relay.py:319`-`:320` single vs
`:401`-`:403` batched — recover the write pipeline's
alias when the caller threads none). Same question,
same shape, two instances; adjacent to F1 but a
different rule (alias sourcing, not seeding). Files:
`django_strawberry_framework/relay.py`. Suggested
trigger: a third recovery site or a recovery-semantics
change. No row exists; Worker-0 owns the index.

## Defects

None. Two examined-and-cleared notes, neither a defect:
the `testing/relay.py` registration check resembles the
verified target-guard rule but is already homed in the
open `registered-djangotype-definition-validation`
family row (no ticked row is factually wrong); the
`base_queryset` locals shadowing the seed-helper import
inside `optimizer/walker.py:1191`,
`optimizer/walker.py:1216`, and
`optimizer/nested_planner.py:1294` never call the import
in the shadowed scope, so the shadowing is benign
naming, not behavior.

## Pending execution

- `proof: uv run python scripts/workspace.py run
  dry/modelfetch-e8/consolidate -- pytest
  tests/utils/test_querysets.py
  tests/types/test_relay_interfaces.py
  tests/mutations/test_resolvers.py -n0 --no-cov -q`
  (discharges F1's behavioral proof once the block
  clears; runnable only after the unblocked
  consolidation lands).
- Sharded cell: `unverified` (cell unauthorized). Not
  inapplicable by construction: the F1 lookup's `using`
  arm reaches the database-alias decision, and the
  alias-pinning rows live in `test_multi_db.py` behind
  `FAKESHOP_SHARDED=1`. The unblocked consolidation owes
  that run. PG cell: `unverified` (cell unauthorized;
  same reachability reasoning).
- No `gate:` witness owed: a green unmutated suite would
  discharge nothing for a blocked finding.

## Judgment

The family is one real duplication plus settled
single-ownership. F1 CONFIRMED: relay's two inline
NodeID-lookup seeds re-spell `base_queryset` on two of
three variation axes with no load-bearing difference,
and the owner docstring's exclusion clause states no
reason that survives a fresh read — but the batched
twin is WT-only concurrent dirt, so the consolidation
is `blocked-on-hunt`, recorded above, with zero files
changed. F2 is already single-owned (17 consumers, one
body). Ten rejections (R1-R10) each carry a concrete
contract difference and a trigger; the strict read,
the tolerant probe, and the truthful stamp read are
three rules, not one. One adjacent sub-rule named for
indexing. No defect, no ticked row disturbed.

Type gates (shared venv, tree-state — zero edits, so
these record the concurrently-dirty tree, not a
change): `uv run mypy` clean (119 files),
`uv run basedpyright` 0/0/0, `uv run python
scripts/check_any.py` 130 uses at 90 sites (matches
the run-9 baseline). No workspace copy created (no
source-mutating proof ran); census probes were
read-only greps plus source reads in the shared tree.
The entry's one authorized focused test was not spent.

Freshness (full input pins; `git hash-object` WT vs
`git rev-parse HEAD:path`; HEAD `5c3496e0`):

- Indexed 10: `utils/querysets.py` WT `3e392d48` HEAD
  `69ac3ea3`; `relay.py` WT `63bbba0b` HEAD `037723cd`;
  `types/relay.py` WT `9903f6ea` HEAD `2d1efd00`;
  `mutations/resolvers.py` WT `2ff49673` HEAD `d77a6c68`;
  `permissions.py` WT `87271361` HEAD `9edd4cf5`;
  `connection.py` WT `48de0243` HEAD `99969652`;
  `optimizer/walker.py` WT `4fd8077f` HEAD `13e1be20`;
  `list_field.py` WT `6c0992f2` HEAD `37d2e6dc`;
  `filters/base.py` WT `9502e12c` HEAD `6b952d4d`;
  `filters/sets.py` WT `697ffd40` HEAD `85699ac2`.
- Excluded on body strength: `registry.py` WT `df3fa3d0`
  HEAD `bc498506`; `types/resolvers.py` WT `a8c6a46e`
  HEAD `09d40f34`; `types/base.py` WT `763a5acc` HEAD
  `e8416cc0`; `types/definition.py` WT `ef9e871a` HEAD
  `fd339a7c`; `types/finalizer.py` WT `0807fea7` HEAD
  `662826eb`; `mutations/inputs.py` WT `e73c7878` HEAD
  `d11b8745`; `mutations/sets.py` WT `a1035397` HEAD
  `50f9d6a1`; `forms/inputs.py` WT `65ac558f` HEAD
  `0ba0d9a5`; `forms/resolvers.py` WT `9f7ff436` HEAD
  `61678b9e`; `forms/sets.py` WT `fde417f2` HEAD
  `44df4fe5`; `rest_framework/resolvers.py` WT `074d6e4b`
  HEAD `fc9d8ee5`; `rest_framework/inputs.py` WT
  `015916f6` HEAD `dfedd0e5`;
  `rest_framework/serializer_converter.py` WT `6eb7da3a`
  HEAD `40cb765a`; `rest_framework/sets.py` WT `f2e353b6`
  HEAD `b0894760`; `optimizer/extension.py` WT `8e3fe7c1`
  HEAD `b7b6c434`; `optimizer/predicates.py` WT `d9e2f789`
  HEAD `965d1282`; `optimizer/plans.py` WT `2e962ae2`
  HEAD `97a524e2`; `optimizer/nested_planner.py` WT
  `b6ff0a0e` HEAD `8c3a45f5`; `optimizer/selections.py`
  WT `1f6d3e04` HEAD `f49ea7fa`; `optimizer/lateral_fetch.py`
  WT `a48cb0a4` HEAD `a48cb0a4` (clean);
  `optimizer/single_parent_fetch.py` WT `3a4bb89b` HEAD
  `3a4bb89b` (clean); `keyset.py` WT `7d43c6b1` HEAD
  `6af980b8`; `utils/relations.py` WT `23df6180` HEAD
  `3b35dfcd`; `utils/inputs.py` WT `0575e9b2` HEAD
  `0caa3416`; `utils/write_transaction.py` WT `6eb22df4`
  HEAD `d45c9433`; `utils/write_values.py` WT `5b3ae98e`
  HEAD `7f414700`; `testing/relay.py` WT `572f8d64` HEAD
  `2290f12b`; `management/commands/inspect_django_type.py`
  WT `2e1223dc` HEAD `034dd692`; `types/converters.py` WT
  `22919a32` HEAD `d26ea98f`; `auth/mutations.py` WT
  `d368c5a8` HEAD `e62a385b`; `auth/queries.py` WT
  `4f3ab00f` HEAD `4f3ab00f` (clean); `orders/sets.py` WT
  `8ce11495` HEAD `a8cd33c7`.
- Contract sources: `tests/utils/test_querysets.py` WT
  `40d4149c` HEAD `160c3da0`;
  `tests/types/test_relay_interfaces.py` WT `3ffb75b8`
  HEAD `515ebce5`; `tests/test_registry.py` WT `8bd9a869`
  HEAD `48af782f`; `tests/optimizer/test_extension.py` WT
  `173c14b6` HEAD `9d57709f`;
  `tests/mutations/test_resolvers.py` WT `eeab4fbe` HEAD
  `4f94c05a`;
  `examples/fakeshop/test_query/test_multi_db.py` WT
  `893956aa` HEAD `893956aa` (clean);
  `examples/fakeshop/test_query/test_library_shapes_api.py`
  WT `fbd38b2a` HEAD `fbd38b2a` (clean).
- Searched population: 119 package `.py` files, whole
  `django_strawberry_framework/` tree. Django equivalence
  source: shared-venv Django `6.1`
  (`db/models/manager.py:157`, `db/models/query.py:1640`,
  `:1971`).

## Independent verification (Worker-2)

Recorded BEFORE reading `## Findings` (only the artifact header and
the `## Judgment` tail anchor were seen). All bytes below are HEAD
`5c3496e0` unless marked WT. Fingerprints re-taken by Worker-2:
WT `utils/querysets.py` `3e392d48`, `relay.py` `63bbba0b`,
`types/relay.py` `9903f6ea`, `mutations/resolvers.py`
`2ff49673`, `permissions.py` `87271361`, `connection.py`
`48de0243`, `optimizer/walker.py` `4fd8077f`, `list_field.py`
`6c0992f2`, `filters/base.py` `9502e12c`, `filters/sets.py`
`697ffd40`; HEAD `69ac3ea3` / `037723cd` / `2d1efd00` /
`d77a6c68` / `9edd4cf5` / `99969652` / `13e1be20` / `37d2e6dc`
/ `6b952d4d` / `85699ac2` — 10/10 match the run-9 dispatch
pins. `git diff ITEM_BASELINE --name-only` is the plan edit
alone; no `## Implementation` section exists (one prose mention
only). Zero-edit shape confirmed before tracing.

### Worker-2 trace: F1 model-keyed seed with optional alias pin

Sites (roles mine):

- Definition D1: `utils/querysets.py::base_queryset` (HEAD
  :297-314) — `manager = model._default_manager; return
  manager.using(using).all() if using is not None else
  manager.all()`.
- Definition D2-instance-a: `relay.py::_resolve_real_pk`
  (HEAD :302-306) — comment + annotation +
  `manager = model_for(resolved_type)._default_manager` +
  conditional `manager = manager.using(using)`, then
  `.filter(...).values_list("pk", flat=True).first()`.
- D2-instance-b (WT ONLY): `relay.py::_resolve_real_pks_batched`
  (WT :404-409) — the same 5 lines byte-for-byte (verified by
  direct comparison of all three sites).
- Consumers composing D1 by name (HEAD): `connection.py:2135`,
  `filters/base.py:1500`, `filters/sets.py:2765`
  (`using=parent_db`), `list_field.py:1676`,
  `optimizer/walker.py:593`, `permissions.py:708`
  (`using=state.alias`), `utils/querysets.py:354`
  (`initial_queryset` body), `utils/querysets.py:4678`
  (`related_visibility_queryset_or_default` fallback).
- Projection (stated separation): D1's docstring clause
  "`relay.py` deliberately does not use this - it takes the raw
  manager and composes from there."

Change challenges (mine): (C1) change the alias-pin shape
(e.g. always return `.all()`, or route the pin through a hook) —
must touch D1 + both D2 instances (a change to the rule cannot
move D1 while the relay copies keep the old spelling, and the
two relay instances must move together or the single/batched
decoders diverge). (C2) change the seed manager
(`_default_manager` vs a filtered base) — same three touch
points. Count: 2 definitions (D1 + the D2 shape in two
instances), 3 sites. CONFIRMED duplication on the merits.

Owner I would choose: `base_queryset` (principle 7 — the
existing owner with exactly this responsibility; every
legitimate consumer already imports from `utils/querysets.py`
without reversing a dependency; `relay.py` already imports
`model_for` from there). Migration shape: both relay instances
become `base_queryset(model_for(resolved_type),
using=using).filter(...)...` (Manager-vs-QuerySet union
annotation collapses; `.filter` chains identically).

Block (mine): instance-b is absent at HEAD (`_resolve_real_pks_batched`
and `_decode_and_coerce` grep empty at HEAD; `relay.py` WT diff
is +198/-65) and is called only from WT-only dirt
(`utils/write_values.py:326,335,351`, a lazy import plus two
calls inside the concurrent batching feature). Attribution by
content: the `## Owned changes` ledger names `relay.py` once
(adopted orphan `typed-globalid-decode` trigger docstring — I
verified that exact text IS present in WT at :451 and absent at
HEAD, so ledger dirt and twin dirt coexist and are
content-distinct); the cycle baseline names no package file. The
twin + slot-threading + `_decode_and_coerce` machinery matches
neither → external concurrent (hunt-feature) dirt. Consolidating
only HEAD-clean instance-a while instance-b stays inline would
leave the second definition in place: the change obligation
survives, so the migration must land whole or not at all
(twin-consistency refusal correct). The host function of
instance-a is itself hunt-reshaped in WT (`slot` param, hoisted
`current_write_pipeline` import), so even the single-shape edit
touches a concurrently-moving function. Verdict on F1:
CONFIRMED but correctly unmigrated; zero edits correct.

Open item carried into reconciliation: D1's docstring exclusion
clause states a deliberateness my trace finds no surviving
reason for (`.filter` chains identically off the seeded
queryset). Whether W1 filed, cleared, or missed this decides a
`(Worker-2)` defect entry, not the verdict — the clause is the
blocked migration's to delete.

### Worker-2 trace: F2 strict type-to-model read

Definition: `model_for` body (HEAD `utils/querysets.py:294`,
`return type_cls.__django_strawberry_definition__.model`) — the
ONLY code read of `__django_strawberry_definition__.model`
package-wide (the other two HEAD mentions are docstrings:
`types/relay.py:321`, `utils/querysets.py:286`). No second body
exists. Count 1 → single-owned. Owner: `model_for` itself.

Consumer census (mine, HEAD code calls, 15 direct):
`mutations/resolvers.py` x5 (:284, :725, :929, :1161, :1365),
`permissions.py` :622, `relay.py` x3 (:156, :304-seed, :339),
`types/relay.py` x4 (:125, :193, :376, :940),
`utils/querysets.py` x2 (:354 in `initial_queryset`, :4334 in
`_captured_model`); plus 3 transitive via `_captured_model`
(:3237, :4388, :4494); plus WT +1 (batched :407). Raw
`model_for(` text lines: 17 at HEAD (15 code + 1 docstring + the
def), 18 in WT. FLAGGED: reconcile the exact "17 consumers"
figure against W1's list — my code-call count is 15/16, so the
record must show which 17 lines W1 means. The count-1 verdict
does not hinge on it.

### Worker-2 trace: type-keyed wrapper + rejection candidates

- `initial_queryset` (HEAD :342-354) composes both rules by name
  (`base_queryset(model_for(type_cls))`); consumers:
  `mutations/resolvers.py` :729 + :878 (`.using(alias)` chain),
  `types/relay.py` x6 (:989, :1014, :1056, :1058, :1081, :1083),
  `types/resolvers.py` :450, `utils/querysets.py` :4626. Single
  body; `optimizer/walker.py:585` explicitly routes AWAY from it
  (relation-model authority, not registered-type authority) with
  a real reason — that separation I would KEEP.
- Rejection candidates (mine, each with a contract difference):
  (a) `registry.py::model_for_type` (:382) — lenient
  None-returning registry-map read vs strict definition-attr
  read (different contract AND mechanism); (b) `registry.get`
  model→type reads (inverse direction, ~10 code sites); (c)
  `_base_manager` seeds (`optimizer/predicates.py:78`,
  `rest_framework/resolvers.py:2055`,
  `utils/write_transaction.py:1172,1265`) — unfiltered base vs
  default manager (different visibility posture); (d) re-pin
  `.using()` on live querysets
  (`optimizer/single_parent_fetch.py:286`,
  `types/resolvers.py:453`, `mutations/resolvers.py:878`) —
  routing moves on existing sources, not seeds (878 composes
  `initial_queryset`, a consumer); (e) `_captured_model` (:4320)
  — model-or-captured seam composing `model_for`; (f)
  `default_order`/`applied_order` `model._meta` reads —
  ordering derivation, different rule; (g)
  `_coerced_manager_queryset` / `normalize_query_source` —
  Manager→QuerySet coercion, different rule. Expect W1's R1–R10
  to approximate this set; reconciling each below.
- Sub-rule shape: the `if using is None: pipeline =
  current_write_pipeline(); using = ...` alias-recovery block
  appears in `_resolve_real_pk` (HEAD :296-301) and the WT-only
  batched twin (:401-403) — two instances, one unlanded.
  Naming it for future indexing (rather than consolidating or
  dropping) looks right; endorsement wording judged below.
- Matrix (mine): axis 1 searched via the `.using(`/`_base_manager`/
  flavor-resolver census; axis 2: relay single/batched are same-color
  batching variants, not async twins, and both colors of the
  visibility twins compose `initial_queryset` as consumers; axis
  3: direct definition-model read single-sited, `_meta` reads a
  different rule; axis 4: `registry.get` inverse noted, no shared
  grammar; axis 5 (other media) and full oracle census: NOT
  independently censused — judged from W1's record; axis 6: the
  relay inline is a second definition (F1), not an omission gap.

### Reconciliation with W1's findings (read after the trace above)

### Reconciliation (Worker-2, after reading W1 whole)

F1: FULL AGREEMENT. Count 2 (owner + one inline shape in two
instances) matches my C1/C2 on the same touch points; owner
`base_queryset` with the same principle-7 reasoning (relay
already imports `model_for` from the module — no new edge);
migration shape identical to mine (union annotation
collapses, `.filter` chains). Block: my content attribution
agrees instance-b is unlanded concurrent dirt (absent at HEAD,
called only from WT-only `write_values.py` batching dirt,
matching no ledger row and no cycle-baseline path). Label
note: W1 writes "not hunt-ledgered... treated as
`blocked-on-hunt` per the dispatch procedure either way"; I
attribute it as external concurrent feature dirt by content.
The labels differ, the operative facts do not (unlanded,
untouchable, twin-consistency bars a single-shape migration),
so no disagreement stands. Twin-consistency refusal ENDORSED:
consolidating the HEAD-clean instance while the twin stays
inline leaves the change obligation alive. Structural gate
"none behaviorally possible" ACCEPTED for a blocked finding (a
gate test landed now would be born red, which DRY.md forbids;
the trigger re-arms the question). The docstring exclusion
clause: W1 treats it as reasonless projection deleted by the
deferred migration — I ACCEPTED clearing over a defect entry
(the clause's factual statement is true; only its implied
deliberateness is rebutted, and the deletion is already
specified in the blocked Migration field with a re-arm
trigger, so no obligation is lost).

F2: AGREEMENT on count 1, owner, C4/C5, and triggers — with
record correction C1: the "17 consumers" headline (System
trace, Enumeration, F2 sites, Judgment) is wrong; the
executable WT census is 16 (4+5+2+4+1 as W1 itself itemizes —
every site re-verified present by Worker-2; the 17th line is
the `initial_queryset` docstring mention at WT
`utils/querysets.py:330`, excluded by W1's own stated method).
Repro: `grep -rn "model_for("
django_strawberry_framework/ --include='*.py'` = 18 lines =
def + docstring + 16 calls. The itemized evidence is correct;
only the headline numeral errs, and no verdict hinges on it.

C2: `initial_queryset` "9" headline is wrong; executable WT
census is 10 (1+6+2+1 as itemized — `utils/querysets.py:4550`
confirmed executable code inside
`visibility_scoped_related_queryset`'s return). C3:
`base_queryset` "8 in 8 files" is wrong on files; it is 8
calls in 7 files (`utils/querysets.py` twice). Both itemized
lists verified complete. Worker-0 transcribes 16 / 10 / 8-in-7.

R1–R10: ALL ENDORSED, each with contract difference + trigger
verified. Spot evidence: R1 callers match my HEAD census
(shifted lines); R2 stamp probe confirmed at WT `:580`-`:581`
and HEAD (O2 below); R3 identity-comparison shape confirmed at
`list_field.py:190`; R4 executable count re-derived as 21
("20+" holds); R5 writer + self-read confirmed; R6 spine
confirmed at `:397`/`:409`/`:426` with both flavors composing
`annotate_queryset_relation` by name (also discharges matrix
axis 1); R7 four sites match my census exactly; R8
`getattr(root, accessor).all()` confirmed; R9 coercion-vs-seed
difference holds; R10 composition + load-bearing keying split
matches my trace (walker routes away with reason). O1: R9
names `_coerced_manager_queryset` but not its caller
`normalize_query_source` (WT `:340`, "the single
Manager-to-QuerySet coercion"); the same coercion-not-seeding
reasoning covers it, so this is a naming-completeness
observation, not a gap — no verdict impact. O2: C10's
"no dispatch" half describes WT bytes (`truth.static_attr`);
at HEAD the probe uses tolerant `getattr` (dispatching, but
None-defaulted). The rejection stands on tolerance-vs-fail-loud
at BOTH states; C10's metaclass-divergence proof is WT-shaped.
Observation only.

Matrix: all six axes judged discharged against the real
surface. Axis 2 twin pairing verified against the WT call
lines; axis 5 oracle names verified present
(`test_model_for_returns_registered_model`,
`test_initial_queryset_uses_default_manager`, three
`test_model_for_type_*` rows); axis 6 auth-zero confirmed by
my own census (no `auth/` hits for any of the three helpers).

Sub-rule `write-pipeline-alias-recovery`: ENDORSED for
indexing. Both instances verified (HEAD `:296`-`:301` single,
WT-only `:401`-`:403` batched); same question, same shape,
unlandable now. Exact index-row wording endorsed (Worker-0
applies verbatim): Family `write-pipeline-alias-recovery` |
Owner `TBD by family item (sole file relay.py; the shared
helper both NodeID decoders compose)` | Files
`django_strawberry_framework/relay.py` | Holding `Family
write-pipeline-alias-recovery` | Status `open (named by
Family queryset-seed-and-model-read e8, endorsed by its W2;
instances _resolve_real_pk + WT-only _resolve_real_pks_batched;
trigger: a third recovery site or a recovery-semantics
change)`.

`proof:` typing CORRECT: the workspace run discharges F1's
behavioral proof only after the unblocked consolidation
lands; running it now would witness the unmutated tree, not
the migration — so `proof:` (not `gate:`) is right, and the
plan item must read `verified, pending execution`. Cells
CORRECT: sharded/PG `unverified` (cells unauthorized), and
`inapplicable by construction` correctly NOT claimed (the
`using` arm reaches the alias decision; pinning rows live
behind `FAKESHOP_SHARDED=1`). No `gate:` witness owed:
correct, nothing would discharge.

Freshness: present and comparable. All 10 indexed pins
re-taken by Worker-2 and matching; 5 "clean" claims
re-verified (`lateral_fetch`, `single_parent_fetch`,
`auth/queries`, both live-query suites — WT==HEAD at the
pinned hashes); 2 excluded pins (`registry.py`, `keyset.py`)
re-verified exact. No fingerprint moved during verification
(WT pins still equal dispatch pins).

Gates (shared worktree venv `.venv`, Django 6.1 — no
workspace copy; read-only probes + gate runs only, same as
W1): `uv run mypy` → clean, 119 files; `uv run
basedpyright` → 0/0/0; `uv run python scripts/check_any.py`
→ 130 uses at 90 sites. All three match the run-9 baseline
exactly. Ruff: VACUOUS — zero tracked paths touched
(zero-edit item; this artifact is untracked `.md`, which
ruff does not process); repo-wide ruff correctly NOT run
(it would surface concurrent dirt).

Defects: none new. The two cleared notes re-verified
(shadowing scopes contain no bare `base_queryset(` calls;
`nested_planner.py:1301/1318` pass the local as an argument).
No `(Worker-2)` entry owed.

VERDICT: `verified` (plan item: `verified, pending
execution` — the `proof:` entry correctly remains). C1–C3
are headline-numeral slips with correct itemized evidence
and explicit corrections on this page; O1–O2 are
observations. No standing disagreement exists: every
W1/W2 difference above is reconciled with fresh evidence.

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
