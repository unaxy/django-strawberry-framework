# DRY review: `django_strawberry_framework/mutations/operations.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is routed to the open family holding item
(`mutation-operation-descriptors`, owner HERE), or is a rejection carrying
its contract difference + trigger. Zero production edits; zero tracked files
changed.

## System trace

Target (157 lines, FRESH, CLEAN): the canonical write-side operation
vocabulary — four frozen
[operations][operations]`::MutationOperationDescriptor` instances
(`create` / `update` / `delete` / the plain-form `"form"` sentinel) plus the
predicates and derived maps/sets every write flavor composes by name. What
it owns:

- [operations][operations]`::MutationOperationDescriptor` — the one
  validated record type (frozen dataclass, 8 fields: `name`,
  `input_kind`, `input_override_attr`, `has_id_arg`, `has_data_arg`,
  `permission_action`, `supports_model_mutation`,
  `supports_form_mutation`).
- [operations][operations]`::OPERATION_CREATE` /
  `::OPERATION_UPDATE` / `::OPERATION_DELETE` / `::OPERATION_FORM` —
  the four declarations (the only
  `MutationOperationDescriptor(...)` constructions in the package;
  grep-verified).
- [operations][operations]`::_OPERATIONS_BY_NAME` — the registry the
  lookup + all derivations read.
- [operations][operations]`::get_operation_descriptor` /
  `::operation_takes_id` / `::operation_takes_data` — the lookup seam +
  the two GraphQL-argument predicates (`id: ID!` / `data:` presence).
- [operations][operations]`::NON_DELETE_OPERATION_INPUT_KIND` /
  `::_OPERATION_INPUT_OVERRIDE_ATTR` / `::NON_DELETE_WRITE_OPERATIONS` /
  `::_VALID_OPERATIONS` / `::_OPERATION_PERMISSION_ACTION` — five
  derivations, each a comprehension over `_OPERATIONS_BY_NAME` (no
  restated literal anywhere in the file).
- [operations][operations]`::non_delete_operation_error` — the shared
  create/update-only reject constructor (set AND message string
  single-sourced, naming the no-delete reason).

Direction correction for the plan index row: the row lists
`mutations/inputs.py` among files covered, but the dependency runs
REVERSE — [operations][operations] imports `CREATE` / `PARTIAL` from
[mutations-inputs][mutations-inputs] (the generator-kind namespace is
upstream-owned; the descriptor table BRIDGES operation to kind via
`input_kind`). [mutations-inputs][mutations-inputs] imports nothing
from [operations][operations] (grep-verified: zero matches). Likewise
`forms/sets.py` + `rest_framework/sets.py` compose the vocabulary
through the [mutations-sets][mutations-sets] re-export
(`from ..mutations.sets import (..., NON_DELETE_OPERATION_INPUT_KIND,
...)`), not a direct import — still composition by name, indirect
path. `mutations/resolvers.py` IS a direct consumer
(`::operation_takes_id` at the locate gate); `forms/resolvers.py` and
`rest_framework/resolvers.py` are NOT (they key off `meta.operation`
names for their own rules — see R6).

Target history: introduced in `7ff97021` (canonical descriptors
refactor); untouched since (`git log` shows that single commit).
Working blob == HEAD blob `16223c6b…`; item-scoped diff vs
`ITEM_BASELINE=ae4ad058…` is 0 bytes.

Connected code read for judgment, outside the item (full reads unless
noted): [mutations-fields][mutations-fields] (factory + signature +
`!= "form"` gate, full 360-line read),
[mutations-sets][mutations-sets]`::require_non_delete_operation` +
`::_safe_frozenset_membership` + metaclass `_validate_meta` region +
`::input_type_name` + `::_materialize_input_for` + import block (ranged
reads), [mutations-resolvers][mutations-resolvers] locate gate +
`_run_pipeline_sync` dispatch + update backstop (ranged reads),
[mutations-permissions][mutations-permissions]`::DjangoModelPermission.has_permission`
(ranged read), [mutations-inputs][mutations-inputs] `CREATE` / `PARTIAL`
definitions + namespace comment (ranged read),
[forms-sets][forms-sets] import block + `build_input` +
`input_type_name` + plain-form `_validate_meta` sentinel snapshot
(ranged reads), [forms-inputs][forms-inputs] `FORM` + namespace comment
(grep), [rf-sets][rf-sets] import block + `build_input` +
`input_type_name` + `operation == CREATE` site (ranged reads),
[rf-resolvers][rf-resolvers] `== "create"` / `== "update"` sites
(ranged reads), [mutations-init][mutations-init] (full),
oracles [test-operations][test-operations] (full 142-line read),
[test-permissions][test-permissions] perm-map row (grep),
[test-sets][test-sets] non-delete + delete-acceptance rows (grep), live
[products-api][products-api]`::test_create_update_delete_item_argument_signatures_over_http`
+ perm-denied rows (grep), contract sources [spec-036][spec-036] (vocabulary
+ Decision 14/15 rows, grep) + [spec-038][spec-038] Decisions 7/10/11
(via code-cited text) + [spec-039][spec-039] (existence only).
Excluded with reason: the concurrent hunks (`connection.py`,
`extensions/resource_policy.py`, `filters/sets.py`,
`forms/inputs.py::_form_field_basis`, `mutations/fields.py` guard
trio, `filters/inputs.py::_normalize_range_value`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) carry none of this family's mechanism
(verified by grep population, not by reading them); the
`utils/querysets` duplicate-trace collision was never opened. The
[mutations-fields][mutations-fields] hunk (+60/-17, working
`8c60a5c6…` vs HEAD `cf518361…`) was diffed first-hand and does NOT
touch the operations-consumer lines (`operation_takes_id/data` call
sites, `!= "form"` gate), so every composition claim below holds on
both bytes.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** SEARCHED (the file's reason to
exist). Sibling flavors each speak the operation vocabulary in local
terms, and every one composes the owner by name: model flavor via
[mutations-fields][mutations-fields]`::_synthesized_mutation_signature`
(`operation_takes_id/data`), [mutations-sets][mutations-sets]
(`_VALID_OPERATIONS`, `NON_DELETE_OPERATION_INPUT_KIND.get`,
`_OPERATION_INPUT_OVERRIDE_ATTR`, `require_non_delete_operation` +
`non_delete_operation_error`), and
[mutations-resolvers][mutations-resolvers] (`operation_takes_id`
locate gate); form flavor via [forms-sets][forms-sets]
(`NON_DELETE_OPERATION_INPUT_KIND[meta.operation]`, indirect path) +
the `"form"`-sentinel snapshot; serializer flavor via
[rf-sets][rf-sets] (same map, indirect path); auth via
[mutations-permissions][mutations-permissions]
(`_OPERATION_PERMISSION_ACTION[operation]`). No second descriptor
construction, no hand-spelled operation→kind/action map outside
oracles (55-match vocabulary grep over the whole package). Family
row F1.

**2. Sync/async twins.** INAPPLICABLE in one line: pure frozen data +
pure sync predicates, zero `await`/`async` in the file — no color
exists to twin.

**3. Derived rather than repeated knowledge.** SEARCHED. All five
derived objects are comprehensions over `_OPERATIONS_BY_NAME`
(read each); `CREATE`/`PARTIAL` are imported, never re-spelled;
`sorted(...)` renders in messages derive from the owner at use time
([mutations-sets][mutations-sets]`::DjangoMutationMetaclass._validate_meta`
renders `sorted(_VALID_OPERATIONS)`); no consumer rebuilds a map
from `_meta` or settings. `NON_DELETE_WRITE_OPERATIONS` has exactly
one in-file spelling (`supports_form_mutation and name != "form"`;
equivalent to `input_kind is not None` today, but the alternative is
not implemented anywhere — no second definition).

**4. Inverse / round-trip pairs.** INAPPLICABLE in one line:
`get_operation_descriptor` is a one-way registry lookup keyed by the
`.name` identity (reverse is the attribute itself); `takes_id/data`
are field projections, not inverse halves; no encode/decode or
pack/unpack split exists on this surface.

**5. Contracts restated in another medium.** SEARCHED. Oracles (move
on intent, never counted): [test-operations][test-operations] spells
every descriptor field + every derived map (fails when the owner
changes, as desired); [test-permissions][test-permissions] pins the
action map; [test-sets][test-sets] pins the non-delete reject + the
model flavor's broader `_VALID_OPERATIONS` delete-acceptance; live
[products-api][products-api] pins shipped argument presence +
perm-denied verdicts per operation. Projections (describe, never
own): the module docstring, [mutations-init][mutations-init] bullet,
[mutations-fields][mutations-fields] `::_synthesized_mutation_signature`
docstring arg-shape restatement (verified byte-matching the
descriptors: id for update/delete, data for all-but-delete),
[rf-sets][rf-sets] line-128 comment naming the map. Contract
sources: [spec-036][spec-036] cites
[operations][operations] as the derivation home for the vocabulary
("`operation` not in the three model-flavor values
[`mutations/operations.py`][operations] derives"), plus Decision 14
(arg shape) + Decision 15 (add/change/delete codenames);
[spec-038][spec-038] Decisions 7/10/11 (sentinel, plain-form rejects
any `Meta.operation`, DenyAll default).

**6. Enforcement by omission.** SEARCHED: enumerated the 4-member
family against every predicate/map. `delete` absent from the input
maps (id-only, Decision 14 — enforced at
[mutations-sets][mutations-sets] validation + `input_type_name` +
`_materialize_input_for`); `"form"` absent from `_VALID_OPERATIONS`
(model flavor cannot be model-less) and `_OPERATION_PERMISSION_ACTION`
(model-less form authorizes via DenyAll/`[]`, Decision 11);
`NON_DELETE_WRITE_OPERATIONS` = exactly `{create, update}`
(modelform/serializer have no delete pipeline).
`operation_takes_id/data` answer `False` for unknown names —
fail-closed pre-validation (unreachable post-validation; `_validate`
rejects unknown first). No member lacks a guard a contract source
requires → no axis-6 defect. Seam-mirror note (pass-2 record
confirmed from this side):
[mutations-fields][mutations-fields]`::DjangoMutationField` line 330
`takes_id = ... operation != "form"` is True for create while
`operation_takes_id("create")` is False — BY DESIGN, not drift: the
inline form is the resolver-CALL gate (every model op passes `id=`,
create as `UNSET`), the predicate is the SIGNATURE gate (create
exposes no `id:` arg); replacing the gate with the predicate would
`TypeError` every create (see R3).

### Enumeration

Instrument: every name in `ast.Module.body` (`python3 -c` AST dump):
21 top-level nodes. Count: 21. Assignment: ALL 21 → family row F1
(`mutation-operation-descriptors`, owned HERE); zero file-local rows;
neighbor look-alikes → rejections R1–R8. No consolidation inside a
file item.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (spec-036/038/39 vocabulary charter) | F1 (projection at owner) |
| 1–5 | `__future__` / `dataclass` / `Any` / `exceptions` / `inputs(CREATE, PARTIAL)` imports | F1 (upstream bridge: exceptions renderers, generator kinds) |
| 6 | `::MutationOperationDescriptor` | F1 (the one record type) |
| 7–10 | `::OPERATION_CREATE` / `::OPERATION_UPDATE` / `::OPERATION_DELETE` / `::OPERATION_FORM` | F1 (the four declarations) |
| 11 | `::_OPERATIONS_BY_NAME` | F1 (registry every derivation reads) |
| 12 | `::get_operation_descriptor` | F1 (lookup seam; consumed by 13/14 + oracle) |
| 13 | `::operation_takes_id` | F1 (consumers: fields signature, resolvers locate) |
| 14 | `::operation_takes_data` | F1 (consumer: fields signature) |
| 15 | `::NON_DELETE_OPERATION_INPUT_KIND` | F1 (consumers: sets ×3 sites, forms-sets ×2, rf-sets ×2) |
| 16 | `::_OPERATION_INPUT_OVERRIDE_ATTR` | F1 (consumers: sets validation loop + materialize index) |
| 17 | `::NON_DELETE_WRITE_OPERATIONS` | F1 (consumer: `require_non_delete_operation`; message set) |
| 18 | `::_VALID_OPERATIONS` | F1 (consumer: model `_validate_meta` membership) |
| 19 | `::_OPERATION_PERMISSION_ACTION` | F1 (consumer: `DjangoModelPermission`) |
| 20 | `::non_delete_operation_error` | F1 (shared reject; consumer: `require_non_delete_operation`) |

### Challenges

Authoritative definitions only; consumers/oracles/projections listed,
not counted. Each challenge exercises one variation axis of F1.

- **C1 — new model operation (id-only `archive`).** Forced:
  [operations][operations] table (+1 descriptor; all five derived
  objects follow by comprehension). Count = 1. Consumers that would
  also move (listed): `sets.py` literal-`delete` branches (R4),
  resolvers dispatch (R5), perm map gains an action — family-item
  questions, not second definitions.
- **C2 — change update's permission action.** Forced:
  `::OPERATION_UPDATE` row only (`_OPERATION_PERMISSION_ACTION`
  derives). Count = 1.
- **C3 — change the `data:` shape (delete gains `data`).** Forced:
  `::OPERATION_DELETE.has_data_arg` only (`operation_takes_data` +
  field signature follow). Count = 1.
- **C4 — new variation axis (per-operation flag, e.g. bulk
  support).** Forced: dataclass field + four rows, all in
  [operations][operations]. Count = 1.
- **C5 — rename an override attr (`partial_input_class`).**
  Forced: `::OPERATION_UPDATE` row only (override-attr map derives;
  sets validation loop + materialize index compose). Count = 1.
- **C6 — retire the `"form"` sentinel.** Forced:
  `::OPERATION_FORM` row + registry membership, both in
  [operations][operations]. Count = 1. Consumers listed:
  forms-sets snapshot, fields signature/call gates.

No experiment beyond inspection: the target is pure data + pure
functions with no ordering, transactional, async, or
actor/time/state-observing behavior (principle 8) — executing the
predicates would assert `True == True` without distinguishing any
rival hypothesis. Composition is proven textually (import + call at
each site, first-hand reads above).

## Findings

### F1 — `mutation-operation-descriptors` (consolidated, owner HERE)

- **Contract + variation.** The write-side operation vocabulary:
  which names exist; per name the input-generator kind, the consumer
  override attr, `id:`/`data:` presence, the model-permission
  codename action, and flavor support. Varies on: member set (new
  operation), per-member flags (arg shape, action, kind, support).
- **Sites + roles.** Definition (sole): [operations][operations]
  table + derivations + predicates + reject constructor (members
  6–20). Consumers (compose by name, verified first-hand):
  [mutations-fields][mutations-fields]`::_synthesized_mutation_signature`,
  [mutations-resolvers][mutations-resolvers]`::run_write_pipeline_sync`
  (locate gate), [mutations-sets][mutations-sets] (4 sites),
  [mutations-permissions][mutations-permissions]`::DjangoModelPermission.has_permission`,
  [forms-sets][forms-sets] (2 sites, via sets re-export),
  [rf-sets][rf-sets] (2 sites, via sets re-export). Upstream owners
  (reverse edge): [mutations-inputs][mutations-inputs] (`CREATE` /
  `PARTIAL`), [forms-inputs][forms-inputs] (`FORM`). Oracles:
  [test-operations][test-operations], [test-permissions][test-permissions]
  map row, [test-sets][test-sets] reject/acceptance rows, live
  [products-api][products-api] signature + perm rows. Projections:
  module + `__init__` docstrings, fields-signature docstring,
  rf-sets comment, spec prose. Contract sources: [spec-036][spec-036]
  (names operations.py as derivation home), [spec-038][spec-038],
  [spec-039][spec-039].
- **Challenges.** C1–C6, each count = 1 (owner only).
- **Owner + lifetime.** Owner stays [operations][operations]:
  narrowest cohesive vocabulary module every flavor can import
  without a dependency reversal (it imports only exceptions +
  generator kinds; nothing imports it that it imports). Lifetime
  (principle 4): the derived maps/sets are pure import-time
  derivations, NOT cached state — validity key = module import;
  owner = this module; mutators = none (descriptors frozen,
  containers module-private except the three public maps);
  invalidation = N/A (recompute is the definition).
- **Migration.** None owed — already single-sourced since `7ff97021`;
  every consumer composes by name (Matrix 1). Open follow-ups live
  at the FAMILY item, not here: whether R4/R5 literal-`delete`
  enforcement sites should consult the predicates (family decides;
  file items do not consolidate).
- **Distinct behavior.** R1–R8 stay separate (see Rejections).
- **Behavioral proof.** `static-reviewed`: composition verified by
  first-hand read of each import + call site; no observable-behavior
  delta exists to execute (pure vocabulary). Structural gate OWED
  at the family item (the fields-item record already notes an F1
  gate + negative control owed there — this item adds no second
  gate proposal).
- **Coupling.** None (zero edits).
- **Freshness.** Working-tree blobs (`git hash-object`):
  [operations][operations] `16223c6b…` (= HEAD; CLEAN),
  [mutations-sets][mutations-sets] `cffa29e5…`,
  [mutations-inputs][mutations-inputs] `fc442047…`,
  [mutations-permissions][mutations-permissions] `54f770ae…`,
  [mutations-resolvers][mutations-resolvers] `3fd1e571…`,
  [mutations-init][mutations-init] `9a5683e9…`,
  [forms-sets][forms-sets] `36ce80b4…`,
  [forms-inputs][forms-inputs] `436fcf42…`, [rf-sets][rf-sets]
  `2c7117d6…`, [rf-resolvers][rf-resolvers] `8024703e…`,
  [test-operations][test-operations] `52c7d712…`,
  [test-permissions][test-permissions] `9cef2100…`,
  [test-sets][test-sets] `2dc45288…`,
  [products-api][products-api] `eff4cd80…`,
  [mutations-fields][mutations-fields] working `8c60a5c6…` vs HEAD
  `cf518361…` (concurrent guard-trio hunk; diffed first-hand, does
  not touch the three operations-consumer lines — claims hold on
  both bytes). Searched population: full-package vocabulary grep
  (55 matches), operation-identity grep (54 matches), tests grep,
  live-tier grep, SPECS grep. Excluded: §System trace list; none
  carries this family's mechanism.

### Rejected candidates

- **R1 — generator kinds (`CREATE`/`PARTIAL`) vs operation
  names.** Difference: `CREATE == "create"` textually, but
  [mutations-inputs][mutations-inputs] documents the namespaces as
  split ("the mutation `operation` `Meta` value is `sets.py`'s
  namespace; the generator only distinguishes create-input from
  partial-input"); `PARTIAL != "update"` proves the vocabularies
  are not one rule. Bridge = `input_kind` column (this family).
  Trigger: generator gains a third shape → inputs.py owns it, this
  table gains a row. Home: inputs.py namespace comment + F1 bridge.
- **R2 — `FORM` kind vs `OPERATION_FORM`.** Same split, form side
  ([forms-inputs][forms-inputs] owns `FORM == "form"` with its own
  namespace comment). Trigger/reconsider as R1. Home:
  [forms-inputs][forms-inputs].
- **R3 — `fields.py:330` `!= "form"` call gate vs
  `operation_takes_id`.** Difference: call-gating (all model ops
  pass `id=`, create as `UNSET`) vs signature-gating (create
  exposes no `id:`); create is inline-True/predicate-False BY
  DESIGN, mirroring the `resolver_seams` `with_id` shape (True
  default; False only for the plain form) — pass-2 seam-mirror
  record, confirmed from this side. Trigger: a flavor whose
  `with_id` seam shape diverges from `operation != "form"` → the
  gate must consult the seam, never the predicate. Home:
  [mutations-fields][mutations-fields] FL5 + family item.
- **R4 — `sets.py` literal-`delete` branches vs
  `has_data_arg`.** Difference: the branches carry delete-specific
  validation sequencing + messages (fields/exclude inapplicable
  reject; editable-walk skip), not the bare boolean. Routed (not
  rejected-outright): the family item decides literal vs
  predicate composition. Trigger: a second id-only model operation
  → literals must move. Home: family item F1 follow-up.
- **R5 — resolvers `== "delete"` dispatch + `== "update"`
  backstop vs descriptor flags.** Difference: pipeline dispatch
  (`_run_delete` vs shared skeleton) and the update-only
  pk-substitution security backstop are control-flow/authorization
  decisions owned with `shared-write-skeleton`, not vocabulary
  restatements. Trigger: new operation → dispatch table moves;
  family item judges the key. Home: family item (coupled read of
  `shared-write-skeleton`).
- **R6 — `rf/resolvers.py` `== "create"`/`== "update"` runtime
  rules vs descriptors.** Difference: each encodes its own
  contract (`apply_defaults`, runtime-requiredness widening,
  `Input`/`PartialInput` suffix) that varies on the operation for
  serializer-local reasons. Trigger: new operation with
  create-like defaults → those sites move independently. Home: the
  rest_framework flavor (its future file/family item).
- **R7 — `operation_kind == CREATE/PARTIAL` (rf-sets, forms-sets)
  vs operation vocabulary.** Difference: comparisons in the
  generator-KIND namespace (R1), not the operation namespace.
  Home: input-kind rule.
- **R8 — `shared-write-skeleton` vs this file.** Difference: the
  pipeline (transaction, locate, auth phase, decode/write steps,
  async wrap) shares no lifecycle with a frozen vocabulary table;
  check-don't-inherit confirmed ([operations][operations] imports
  only exceptions + kinds; no resolver/transaction/async
  machinery). Home: `shared-write-skeleton` family.

## Defects

None found while tracing. Every omission is contract-justified
(Matrix 6); every docstring restatement matches its body
(fields-signature docstring vs descriptors verified
member-by-member); the spec-cited owner is the actual owner
([spec-036][spec-036] names [operations][operations], confirmed).

## Pending execution

Absent — no `execution-deferred` proof exists. The target is pure
data + pure predicates with no ordering/transactional/async surface
(§Challenges), so execution cannot distinguish any rival
hypothesis; composition is established by first-hand reads of each
import + call site.

## Judgment

Zero-edit result, legitimate: matrix discharged against the real
surface (descriptor instances, both predicates,
`NON_DELETE_OPERATION_INPUT_KIND`, and the four remaining derived
objects each traced to every consumer); all six challenges count
exactly one authoritative definition; all 21 enumerated members
assigned to the owned-here family; strongest rejections carry
contract differences + triggers + homes. The vocabulary has exactly
one owner and every flavor composes it by name. No consolidation is
owed in a file item; literal-composition follow-ups (R4/R5) and the
structural gate belong to the open `mutation-operation-descriptors`
family item.

## Implementation (Worker 1)

Zero tracked changes; zero new tracked files. Item-scoped diff:
`git diff ae4ad058… -- django_strawberry_framework/mutations/operations.py`
= 0 bytes (target CLEAN, working == HEAD `16223c6b…`); the only new
path is this artifact itself
(`docs/dry/dry-file-mutations__operations.md`, untracked, expected).
Per tasking ("No production edits", "NO shared-tree pytest"): no
source touched, no `ruff` run owed (no `.py` edits; markdown
scaffold kept to the 10-group convention), no pytest executed (and
none needed — §Challenges). Concurrent dirt listed in §System trace
was never read for verdicts beyond the first-hand hunk attribution
that proves it untouched; `docs/dry/dry-0_0_15.md`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, the staged
`tests/utils/test_querysets.py` hunk, and the utils/querysets
duplicate-trace collision were not modified. Do not commit.

## Independent verification (Worker 2)

Own trace first (recorded BEFORE weighing `## Findings`; first-hand reads +
greps at `HEAD 9031cb3d`, worktree as found):

- **Rule re-derived.** The target owns one vocabulary table: 4 frozen
  [operations][operations]`::MutationOperationDescriptor` rows
  (`create` / `update` / `delete` / `"form"` sentinel), 1 registry
  (`::_OPERATIONS_BY_NAME`), 3 predicates
  (`::get_operation_descriptor`, `::operation_takes_id`,
  `::operation_takes_data`), 5 derived comprehensions
  (`::NON_DELETE_OPERATION_INPUT_KIND`,
  `::_OPERATION_INPUT_OVERRIDE_ATTR`, `::NON_DELETE_WRITE_OPERATIONS`,
  `::_VALID_OPERATIONS`, `::_OPERATION_PERMISSION_ACTION`), 1 shared
  reject (`::non_delete_operation_error`). I read every derivation
  body: each is a comprehension over `_OPERATIONS_BY_NAME`; no restated
  literal in the file. Count of authoritative definitions per posited
  change (C1 new id-only operation, C2 action change, C3 arg-shape
  change, C4 new flag axis, C5 override-attr rename, C6 sentinel
  retire): 1 in every case — the table.
- **Consumers found independently (6 production modules).**
  [mutations-fields][mutations-fields] (`operation_takes_id/data` at
  the signature gates, lines 291/293), [mutations-sets][mutations-sets]
  (4 derived objects + reject: import block lines 75-81,
  `require_non_delete_operation` line 126, `_validate_meta` line 1125,
  override loop line 1176, kind lookups lines 1279/1406/1410),
  [mutations-resolvers][mutations-resolvers] (`operation_takes_id`
  locate gate line 207), [mutations-permissions][mutations-permissions]
  (`_OPERATION_PERMISSION_ACTION` line 34),
  [forms-sets][forms-sets] (`NON_DELETE_OPERATION_INPUT_KIND` lines
  683/702 + `require_non_delete_operation` line 612, via the
  `..mutations.sets` re-export lines 52-76 — indirect composition by
  name), [rf-sets][rf-sets] (same map lines 825/892 + line 601, via
  the same re-export lines 68-85 — indirect). Upstream providers (not
  consumers): [mutations-inputs][mutations-inputs] (`CREATE` /
  `PARTIAL`), [forms-inputs][forms-inputs] (`FORM`). Oracles spell
  literals: [test-operations][test-operations] asserts every field
  (`== "create"`, `is None`, `== "add"`, …) and every derived map
  against literal keys + upstream tokens — fails when the owner moves,
  never reads expectations from it. Second-construction sweep:
  `MutationOperationDescriptor(` occurs exactly 4× package-wide, all
  HERE. No hand-spelled operation→kind/action map in production
  (`partial_input_class` hits in sets.py are the kind-namespace
  `operation_kind == CREATE` branch line 1496 and Meta-key sets —
  R7's namespace, not this rule).
- **Owner I would choose.** [operations][operations], same as W1: the
  narrowest cohesive vocabulary module every flavor can import without
  reversing a dependency (it imports only exceptions + generator
  kinds; nothing it imports imports it back). No rival owner exists.
- **Reconciliation vs W1.** Agree on every row: F1 consolidated HERE;
  C1–C6 counts (all 1); R1–R8 differences + triggers + homes (each
  re-verified below); upstream direction; gate + R4/R5 follow-ups owed
  at the family item; Pending absent; no coupling; no defects.

**Enumeration (member-by-member vs my own AST count).** Instrument
re-run by me (`ast.Module.body`): 21 nodes — matches W1's 21. Every
member checked: 0 module docstring → F1 projection-at-owner; 1–5 the
five imports → F1 upstream bridges; 6 the record type → F1; 7–10 the
four declarations → F1; 11 the registry → F1; 12–14 the three
predicates → F1; 15–19 the five derivations → F1; 20 the shared
reject → F1. **Ruling on zero-file-local: CORRECT, and the alternative
would be fabrication.** The named candidate
(`NON_DELETE_OPERATION_INPUT_KIND`) is a comprehension over the family
registry — family mechanism, not a local rule. The file contains no
private helper, no local-only token, no second contract: docstring =
family charter (projection at owner), imports = bridges. A file-local
row here would invent a rule to fill a quota.

**Counts + roles.** C1–C6 each force exactly the owner table (verified
by reading the derivation bodies, not by trusting the artifact).
Consumers/oracles/projections listed, never counted — W1's tables do
this correctly. No oracle rewritten (zero production/test edits; and
[test-operations][test-operations] asserts literals, confirmed by
first-hand read lines 50-124).

**Equivalence (principle 8).** Pure frozen data + pure predicates: no
ordering, transaction, async, cancellation, or actor/time/state
observation exists to differ on. Inspection (import + call at each of
the 6 consumer modules, verified above) IS the behavioral proof here;
executing the predicates would assert `True == True` against no rival
hypothesis. No `execution-deferred` proof is owed.

**Zero-edit confirmed by me.** `git diff
ae4ad058674af0a079f81cb474e46c43244ea3eb --
django_strawberry_framework/mutations/operations.py` = 0 bytes
(re-run); `git status --short` shows no operations.py dirt; working
blob `16223c6b…` == HEAD blob. W1's "zero production changes,
artifact created, NO probe — inspection-only" report is accurate.

**Rejections (difference + trigger each, first-hand).** R1 generator
kinds: `PARTIAL != "update"` + inputs.py namespace split (line 24)
proves two vocabularies; bridge = `input_kind` column — agree. R2
`FORM` vs `OPERATION_FORM`: same split, form side — agree. R3 the
seam-mirror: fields.py line 330 `!= "form"` (resolver-CALL gate: every
model op passes `id=`, create as `UNSET`) vs
`operation_takes_id("create") == False` (SIGNATURE gate: create
exposes no `id:`) — create is inline-True/predicate-False BY DESIGN;
gating the call on the predicate would `TypeError` every create —
agree, and the mirror of the `resolver_seams` `with_id` shape is
correctly homed at fields FL5 + family. R4 sets.py line 1142
literal-`delete` (delete-specific sequencing + messages, not the bare
boolean) — routed, not rejected-outright — agree. R5 resolvers lines
316/809 dispatch + update backstop (control-flow/authorization owned
with `shared-write-skeleton`) — agree. R6 rf-resolvers lines 1069/1184
(`apply_defaults`, runtime-requiredness — serializer-local contracts,
no operations import) — agree. R7 kind-namespace comparisons —
agree. R8 pipeline vs vocabulary (operations.py imports only
exceptions + kinds) — agree.

**Fingerprints re-hashed by me (`git hash-object`, all match W1):**
operations `16223c6b…`, sets `cffa29e5…`, inputs `fc442047…`,
permissions `54f770ae…`, resolvers `3fd1e571…`, `__init__`
`9a5683e9…`, forms-sets `36ce80b4…`, forms-inputs `436fcf42…`,
rf-sets `2c7117d6…`, rf-resolvers `8024703e…`, test-operations
`52c7d712…`, test-permissions `9cef2100…`, test-sets `2dc45288…`,
products-api `eff4cd80…`. Fields.py working `8c60a5c6…` vs HEAD
`cf518361…` confirmed; its hunk (+60/-17) contains zero
operations-consumer lines (grep for `operations|takes_id|takes_data`
in the diff = no hits), so W1's both-bytes claim holds.

**Gates + negative controls — ruling.** No gate is owed IN this file
item, and none is proposed: correct. A structural gate must guard the
owner against bypass across ALL consumers — that population only
exists at the family item holding every site; demanding one here
would scope it to a file backstop. W1's routing (gate + R4/R5
literal-composition follow-ups owed at `mutation-operation-descriptors`
family) is the DRY-correct placement. No missing negative control.

**Pending absent — adequate.** The inapplicability reason is stated
and I judge it sound (pure-data file; §Equivalence above). No probe
was needed and none is owed.

**Coupling.** None — zero edits. Agree.

**AGENTS.md prose check.** No `.py` touched → no ruff run owed; no
pytest run (none authorized, none needed). Artifact citations use
`path::Symbol` form throughout; the link block carries all 10
canonical groups; no process provenance; no test-tier action. No
violation — not `revision-needed` material.

**Index-direction correction — VERIFIED first-hand, with an
extension.** operations.py line 18 `from .inputs import CREATE,
PARTIAL`; inputs.py's import block (lines 37-68) contains zero
operations imports (grep-verified). So [mutations-inputs] is UPSTREAM
provider, not consumer — W1's correction stands. Further, W1's own
trace proves TWO direct consumers missing from the plan row
(resolvers.py locate gate, permissions.py perm-action map). Worker 0
must rewrite the row as:

| `mutation-operation-descriptors` | `django_strawberry_framework/mutations/operations.py` | `django_strawberry_framework/mutations/operations.py`, `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Family `mutation-operation-descriptors` | open |

i.e. DROP `mutations/inputs.py` (upstream token owner — its kinds are
R1's separate rule, homed at inputs.py), ADD `mutations/resolvers.py`
+ `mutations/permissions.py` (direct composers). forms/rf resolvers
stay OUT per R6; auth stays OUT (zero usage, grep-verified).

## Defects (Worker 2)

None. (The plan-row coverage error above is a Worker-0 index fix,
given as exact rows — not a package defect.)

## Judgment (Worker 2)

`Status: verified`. Zero-edit file item, legitimate: 21/21 members
assigned to the owned-here family with no invented file-local rows,
six challenges all count 1, R1–R8 carry differences + triggers, all 14
freshness fingerprints re-hash clean, Pending-absent judged adequate
for a pure-data file, gate correctly deferred to the family item.
Concurrent dirt (fields.py guard-trio hunk et al.) verified untouched
by this item's claims; all other worktree dirt preserved, nothing
committed.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[plan]: dry-0_0_15.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[operations]: ../../django_strawberry_framework/mutations/operations.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py

<!-- tests/ -->
[test-operations]: ../../tests/mutations/test_operations.py
[test-permissions]: ../../tests/mutations/test_permissions.py
[test-sets]: ../../tests/mutations/test_sets.py

<!-- examples/ -->
[products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
## Bounded re-review at bfaee91d (Worker 2, Q7)

Phase-1 trace only. Prior findings were not read; no status is set
and no verdict on prior findings is proposed here.

### 1. Operation-phase model (derived from current source)

Vocabulary owner: `django_strawberry_framework/mutations/operations.py`
(HEAD bytes, clean — fingerprint below). Four frozen descriptors,
each owning seven facets (name, input_kind, input_override_attr,
has_id_arg, has_data_arg, permission_action, flavor support):

- `create`: input_kind CREATE, override `input_class`, id F, data T,
  perm `add`, model T, form T.
- `update`: input_kind PARTIAL, override `partial_input_class`, id T,
  data T, perm `change`, model T, form T.
- `delete`: input_kind None, override None, id T, data F,
  perm `delete`, model T, form F.
- `form` sentinel: input_kind None, override None, id F, data T,
  perm None, model F, form T.

Derived maps (all dict/frozenset comprehensions over
`_OPERATIONS_BY_NAME`, recomputed by construction, zero extra edits):
`NON_DELETE_OPERATION_INPUT_KIND` (`create`->CREATE, `update`->PARTIAL),
`_OPERATION_INPUT_OVERRIDE_ATTR` (`create`->`input_class`,
`update`->`partial_input_class`), `NON_DELETE_WRITE_OPERATIONS`
(`{create, update}`), `_VALID_OPERATIONS` (`{create, update, delete}`),
`_OPERATION_PERMISSION_ACTION` (`create`->`add`, `update`->`change`,
`delete`->`delete`). Predicates `operation_takes_id` /
`operation_takes_data` plus `get_operation_descriptor` read the
descriptors; `non_delete_operation_error` single-sites the shared
create/update-only reject (set AND message string).

Pipeline phases (owner: `mutations/resolvers.py::run_write_pipeline_sync`,
the skeleton all flavors ride): locate (update/delete only, through the
target type visibility `get_queryset`, select-for-update lock) ->
authorize (exactly once, AFTER locate, BEFORE decode) -> decode_step
(flavor callback) -> write_step (flavor callback) -> tail
(delete snapshot tail, else `refetch_optimized` + object-slot payload,
else model-less `{ ok: true }`). Error paths roll back via the shared
envelope builder. The read-only-vs-write phase flag is owned by
`utils/write_transaction.py` (`WriteAliasContext.write_phase` +
`pipeline_write_phase()` + `pipeline_alias_guard` spanning every
consumer-reachable phase); the atomic boundary by `open_write_pipeline`
nested inside the completion-spanning managed transaction. Per-flavor
mapping: model create/update construct-or-setattr + `full_clean` + save
(+ M2M `.set`); delete snapshot-before-delete; ModelForm decode +
partial reconstruction + `get_form`/`is_valid`/`form.save`; serializer
serializer-keyed decode + `is_valid` + `serializer.save`; plain form
`perform_mutate`, no locate, no re-fetch. GOAL rows applied: declarative
writes (GOAL success criterion 6), deny-by-default write permissions
(`DenyAll` default on the model-less flavor; `DjangoModelPermission`
default on model-backed), one transaction spanning the response.

### 2. Serializer/form interaction points (role + contract each)

Value-level and import-level audit; `forms/resolvers.py` imports nothing
from `mutations/operations.py` (only `make_resolver_entries`,
`run_write_pipeline_sync`, `save_or_field_errors` from
`mutations/resolvers.py`, plus `pipeline_write_phase` and decode
helpers). `rest_framework/resolvers.py` likewise imports nothing from
`mutations/operations.py` (skeleton + inputs + error/permission/
queryset/transaction/write-value helpers only).

- (a) `NON_DELETE_OPERATION_INPUT_KIND[meta.operation]` in
  `forms/sets.py::build_input` / `input_type_name` and
  `rest_framework/sets.py::build_input` / `input_type_name`. Role:
  consumers of the derived map. Contract: `create`->CREATE (required
  narrowing guards apply), `update`->PARTIAL (all-optional, no
  create-required guard); delete never reaches it (model
  `_materialize_input_for` returns None via `.get()`; form/serializer
  `_validate_meta` rejects delete first via (b)).
- (b) `mutations/sets.py::require_non_delete_operation`, consumed by the
  ModelForm and serializer `_validate_meta` paths. Role: shared lookup
  over `NON_DELETE_WRITE_OPERATIONS`; body via
  `non_delete_operation_error`. Contract: exactly `{create, update}`
  passes; anything else (incl. `delete`) is the shared typed reject
  redirecting to a 036 delete mutation.
- (c) `_OPERATION_INPUT_OVERRIDE_ATTR`, consumed by model
  `_validate_meta` (cross-override guard: an override for a non-declared
  operation is a loud reject) and `_materialize_input_for` (override
  selection). No form/serializer counterpart (those flavors have no
  `input_class` overrides).
- (d) `_VALID_OPERATIONS`, consumed ONLY by model `_validate_meta`
  membership. Asymmetry recorded: model accepts delete; form/serializer
  go through (b) and reject it. Plain form rejects ANY `Meta.operation`
  key by presence (model-less, Decision 10).
- (e) `_OPERATION_PERMISSION_ACTION`, consumed by
  `mutations/permissions.py::DjangoModelPermission.has_permission`
  (`add`/`change`/`delete` codename build). ModelForm/serializer writes
  authorize through the same `run_permission_classes` seam; the plain
  `form` sentinel is deliberately absent from the map and defaults to
  `DenyAll` instead of a codename lookup.
- (f) `operation_takes_id` drives `needs_locate` in the skeleton for all
  model-backed flavors; `operation_takes_id` / `operation_takes_data`
  drive `mutations/fields.py::_synthesized_mutation_signature` for every
  flavor (the form/serializer `data:` lazy-ref resolves to their own
  input namespaces; payload ref stays in `mutations.inputs`).
- (g) Value-convention reads of `meta.operation` inside
  `rest_framework/resolvers.py` (string literals, no operations-module
  dependency): `_assert_field_agreement` (`update` forces optional
  requiredness; `PartialInput` vs `Input` suffix in the annotation
  re-derivation), `_assert_runtime_write_source_ownership`
  (`apply_defaults` exactly when `operation == "create"`),
  `SerializerHookContext.operation` (frozen string `"create"`/`"update"`
  handed to hooks instead of the live instance). Role: convention
  consumers; a renamed operation value would need these literals moved
  but no definition lives here.
- (h) Explicit non-interactions (verified by import audit): `_hook_mapping`
  (mapping coercion for the three serializer hooks), `_frozen_hook_view`
  (immutable hook data view), `_assert_save_kwargs_no_shadow` /
  `_assert_save_kwargs_not_model_fields` (save-kwarg guards), the
  relation-intent ledger + post-save attestation, and the write witness
  never branch on operation vocabulary (save for (g)); they walk
  `_write_surface_specs` (input specs + injected specs), whose
  composition the delta does not touch.
- (i) Sentinel spelling: `OPERATION_FORM.name == "form"` mirrors
  `forms/inputs.py::FORM == "form"` (create-shaped via
  `CREATE_SHAPED_KINDS`). Two literals holding one sentinel value;
  recorded as observed, no verdict.

### 3. Definition counts (change challenges, current source)

- New operation (posit a create-like model operation, e.g. `publish`,
  with its own input kind + permission action + arg shape):
  definitions to move = 1 (one `MutationOperationDescriptor` literal +
  its row in the `_OPERATIONS_BY_NAME` tuple — a single edit site in
  `mutations/operations.py`). All five derived maps, both predicates,
  and the shared reject follow by construction (0 edits). Value-keyed
  consumer sites needing a per-operation DECISION (not definitions):
  `_run_pipeline_sync` explicit `== "delete"` dispatch, delete-only
  guards, the agreement `== "update"` requiredness branch, the
  source-ownership `== "create"` defaults branch.
- New pipeline phase (posit splitting write into pre/post commit steps,
  or a new phase-flag state): definitions in `mutations/operations.py`
  = 0 (it owns vocabulary, no phase flag). The phase flag definition is
  1 (`WriteAliasContext.write_phase` + `pipeline_write_phase` +
  `pipeline_alias_guard` in `utils/write_transaction.py`); the skeleton
  order in `run_write_pipeline_sync` is 1 consumer site.
- New input generator kind: 1 definition pair (`CREATE`/`PARTIAL` in
  `mutations/inputs.py`), not in the operations module.

### 4. Owners I would choose (DRY principle 7; principle 5 lifecycle)

- Operation vocabulary (names, input kinds, override attrs, arg shape,
  permission actions, flavor support): keep
  `mutations/operations.py`. Every legitimate consumer (model/form/
  serializer sets, fields, permissions, resolvers) already depends
  inward on it; it is the narrowest cohesive owner with no reversed
  dependency.
- Shared lifecycle (locate->authorize->decode->write->tail, one atomic
  boundary, authorize-before-decode ordering): keep
  `mutations/resolvers.py::run_write_pipeline_sync`; flavor adapters
  (`decode_step`/`write_step`/`tail_step`) stay at the flavors
  (principle 5: one body, named adapters, no mode flags).
- Phase flag + alias guard: keep `utils/write_transaction.py`.
- Serializer hook hardening, agreement checks, save-kwarg guards,
  intent ledger, attestation: keep `rest_framework/resolvers.py`.
  Moving any of it beside the vocabulary would couple the operation
  table to DRF machinery its other consumers cannot import
  (dependency direction wins over narrowness).
- Form decode + partial reconstruction: keep `forms/resolvers.py`
  (stable counterpart, confirmed clean below).

### 5. Delta assessment (does anything derived break?)

(a) `rest_framework/resolvers.py` worktree delta (+129/-77 vs HEAD
`8024703e`): hunk groups are (1) guarded `isinstance` interrogations in
`_hook_mapping`, `_frozen_hook_view` (leaf + container walk),
`_merged_serializer_kwargs` context-mapping check; (2) `_safe_*`
rendering (`_safe_class_name` / `_safe_type_name` / `_safe_arg_repr`)
replacing bare `mutation_cls.__name__`, `type(x).__name__`,
`repr(key)`, `{alias!r}` spellings across hook/injected/kwargs/
agreement/ownership/scope/validator/ledger/intent/attestation/witness/
saved-result messages; (3) guarded `write_alias` `__eq__` comparison;
(4) agreement-function rewordings with identical checks. Attribution:
NO hunk touches an operation-phase concept — seam signatures
(`decode_step`/`write_step`), `hook_context.operation` values,
`== "create"` / `== "update"` branches, `_write_surface_specs`
composition, save-kwarg shadow/model-field SETS, `pipeline_write_phase`
windows, and the fail-closed OPAQUE-leaf reject are all byte-identical
in behavior. Benign-input rendering is unchanged (offender sort uses the
same renderer family, preserving benign order). Hostile inputs that
previously escaped as raw `TypeError`/`AttributeError`/`RecursionError`
now take the same typed `ConfigurationError` with the same trigger
conditions — strictly narrower observable behavior, same contract. No
defect: no GOAL row (declarative writes, deny-by-default, response-
spanning transaction) is broken, and no reaching wire/configuration
input changes its accept/reject outcome — write-path rejects that were
`ConfigurationError` remain `ConfigurationError` on the same inputs.
What still holds: the skeleton order, the frozen-view immutability
promise, the agreement walk coverage, the exact-match injection
contract, and the save-kwarg shadow + model-field prohibitions.

(b) `forms/resolvers.py`: worktree == HEAD `4edb984b` (no diff output;
hashes match) — the form counterpart is stable; everything in (2)(a)-(f)
derived against it still holds byte-for-byte.

(c) Concurrent dirt elsewhere is out of scope and unattributed here:
`mutations/sets.py`, `mutations/fields.py`, `mutations/resolvers.py`,
`mutations/inputs.py`, `forms/sets.py`, `forms/inputs.py`,
`rest_framework/sets.py`, `tests/mutations/test_sets.py`,
`tests/rest_framework/test_sets.py` are dirty vs HEAD (fingerprints
below); `mutations/permissions.py`, `mutations/inputs.py` CREATE/PARTIAL
lines read, `rest_framework/hook_context.py`,
`utils/write_transaction.py`, oracles `tests/mutations/test_permissions.py`
pins `_OPERATION_PERMISSION_ACTION == {create:add, update:change,
delete:delete}` and per-operation allow/deny rows) were read as cited.
Preserved untouched; no revert, no commit.

### 6. Freshness fingerprints (HEAD `bfaee91d`, worktree hashes)

- `django_strawberry_framework/mutations/operations.py`: HEAD
  `16223c6b8a477bec61da690d08f1c1a01125d8ec`, worktree `16223c6b…` —
  CLEAN (match).
- `django_strawberry_framework/forms/resolvers.py`: HEAD
  `4edb984b299b4e2a71492e73382558b01865f48a`, worktree `4edb984b…` —
  CLEAN (match, no delta).
- `django_strawberry_framework/rest_framework/resolvers.py`: HEAD
  `8024703ec0fb09758daeec0585e0065de1c61fc3`, worktree
  `c0b5403979692f695d89d998121027e3b6afaf62` — DIRTY (+129/-77;
  `git diff HEAD --stat` confirms; hunks attributed in section 5).
- Supporting inputs read (HEAD blob / worktree hash): `mutations/sets.py`
  `cffa29e5` / `936f5ae7` (dirty, concurrent);
  `mutations/fields.py` `cf518361` / `64410c86` (dirty, concurrent);
  `mutations/permissions.py` `54f770ae` / `54f770ae` (clean);
  `mutations/resolvers.py` `3fd1e571` / `a322d17a` (dirty, concurrent);
  `mutations/inputs.py` `fc442047` / `fcbb964d` (dirty, concurrent);
  `forms/sets.py` `36ce80b4` / `98ef150d` (dirty, concurrent);
  `forms/inputs.py` `55614839` / `436fcf42` (dirty, concurrent);
  `rest_framework/sets.py` `2c7117d6` / `def19a9e1` (dirty, concurrent);
  `rest_framework/hook_context.py` `f4910159` / `f4910159` (clean);
  `utils/write_transaction.py` `eca9ad4d` / `eca9ad4d` (clean);
  `GOAL.md` `7dfbef5c` / `7dfbef5c` (clean);
  `docs/dry/DRY.md` `e8151123` / `e8151123` (clean);
  `docs/dry/worker-2.md` `4f089ea4` / `4f089ea4` (clean).
- Oracles read (worktree hash): `tests/mutations/test_permissions.py`
  `9cef2100` (clean vs HEAD `9cef2100`);
  `tests/mutations/test_sets.py` `8574a349` (dirty vs HEAD `2dc45288`);
  `tests/rest_framework/test_sets.py` `f3fffbdd` (dirty vs HEAD
  `7e7d1819`). No test was executed (re-review reads oracles only).

PHASE-1-TRACE-RECORDED — artifact: docs/dry/dry-file-mutations__operations.md

## Bounded re-review at bfaee91d (Worker 2, Q7) -- Phase 2 reconciliation

Scope: findings (a)/R6/R8 only (vocabulary ownership + flavor
interaction); settled rows stay settled. Zero source edits; re-review
only; oracles read, never executed.

### Phase-1 integrity (pre-exposure statement)

My phase-1 section `## Bounded re-review at bfaee91d (Worker 2, Q7)`
(lines 645-887, ending `PHASE-1-TRACE-RECORDED`) is intact and was
recorded pre-exposure: in phase 1 I never opened this artifact file
(appended via shell heredoc without any read; the first read of any
prior section happened in this phase 2). Its key results stand
unchallenged by anything below: 4 frozen descriptors + derived
maps/predicates; neither rest nor forms resolvers import operations.py;
+129 assessed as message-rendering + guarded-interrogation with no
operation-phase concept touched; forms counterpart byte-identical.

### Reconciliation vs (a) -- vocabulary table + consumer directions: HOLDS

- Descriptors still 4, derived maps identical: target file is
  byte-identical (`16223c6b`, 157 lines; `git status` clean), so every
  count and every derivation body the prior passes verified holds
  without re-proof.
- Consumer directions re-checked on CURRENT worktree bytes (concurrent
  dirt present, attributed per hunk, not reverted):
  `mutations/resolvers.py` still `from .operations import
  operation_takes_id` (line 129) with the locate gate
  `needs_locate = ... operation_takes_id(meta.operation)` (line 207)
  -- direct consumer, holds.
  `mutations/permissions.py` still imports + indexes
  `_OPERATION_PERMISSION_ACTION` (lines 34/174) -- holds.
  `mutations/fields.py` + `mutations/sets.py` import lines intact
  (lines 64 / 75) -- holds. `mutations/inputs.py` still has zero
  operations imports (package grep re-run: its only hits are prose in
  `__init__.py`) -- upstream direction holds despite its concurrent
  dirt. `forms/resolvers.py` has zero operations/meta.operation matches
  -- NOT a direct consumer, holds. `rest_framework/resolvers.py` has no
  operations import; its only operation reads are the four
  pre-existing `meta.operation` value sites (lines 1118, 1229/1233,
  1262, 2240) -- NOT a direct consumer, holds.
- The +129 delta ADDS no direct import of operations.py and NO new
  `meta.operation` consumer: `git diff HEAD -- rest_framework/
  resolvers.py | grep ^[+-].*operation` yields exactly one changed
  line-pair, the line-1262 rendering swap
  (`type(serializer).__name__` -> `_safe_type_name(serializer)`)
  around a byte-identical `'PartialInput' if operation == 'update'
  else 'Input'` ternary. 208 changed lines total, 1 touching an
  operation token, 0 changing operation logic.

### Reconciliation vs R6 -- serializer-local == rules: SURVIVES

Opened all three sites on current worktree bytes: (1)
`_assert_runtime_write_source_ownership` line 1118
(`apply_defaults=...operation == "create"`) -- zero diff hunks touch
it; the create-defaults contract and its DRF reason are unchanged.
(2) `_assert_field_agreement` lines 1229-1237 (`operation =
meta.operation`; `False if operation == "update" else bool(...)`) --
zero diff hunks touch the branch; the update-widened-optional
contract stands. (3) Line 1262 suffix ternary -- logic identical
(rendering-only change proven above). (4) `hook_context.operation`
passthrough line 2240 -- untouched. Each site still varies on the
operation for serializer-local reasons (DRF partial semantics,
runtime required/default declarations, generated input naming), none
reads the descriptor table, none is reachable from a descriptor edit.
Trigger stands as written (new operation with create-like defaults ->
those sites move independently); home stays the rest_framework
flavor/file item.

### Reconciliation vs R8 -- skeleton vs vocabulary: SURVIVES

`mutations/operations.py` import block (lines 12-19, current bytes):
`__future__`, `dataclass`, `typing.Any`, `..exceptions`
(`ConfigurationError`, `_safe_arg_repr`), `.inputs` (`CREATE`,
`PARTIAL`). Only exceptions + generator kinds; no resolver,
transaction, or async machinery. The pipeline lifecycle still shares
nothing with the frozen table. Holds.

### Freshness re-hashed (HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`)

- Target `mutations/operations.py`: worktree `16223c6b…` == HEAD
  `16223c6b…` -- UNCHANGED (matches phase-1 and both prior passes).
- `rest_framework/resolvers.py`: HEAD `8024703e…`, worktree
  `c0b54039…` -- dirty, SAME worktree hash as phase 1 (no new dirt
  landed mid-re-review); +129/-77 diffstat confirmed.
- `forms/resolvers.py`: `4edb984b…` both sides -- clean, no delta.
- Status check: only `rest_framework/resolvers.py` dirty among the
  three; artifact itself untracked; all other concurrent dirt
  preserved untouched; nothing committed.

### Defects (Worker 2)

None. No contract row breaks (GOAL declarative-writes /
deny-by-default / response-spanning transaction untouched by the
delta); no reaching input changes accept/reject outcome.

### Verdict

`verified` -- the item stands at `bfaee91d`. Findings (a)/R6/R8 all
hold against the delta; target unchanged; zero edits; no pending
execution.

### Exact plan rows for Worker 0 (not applied -- plan is Worker 0's)

1. Item tick (plan line 170) -- replace the trailing parenthetical:
`- [x] File `mutations/operations.py` --
[dry-file-mutations__operations.md](dry-file-mutations__operations.md)
-- verified (Run 0.0.15 2026-09-18-1; bounded re-review Q7 at `bfaee91d`
via two-phase W2: (a)/R6/R8 stand, +129 hook/agreement hardening
touches no operation-phase concept, forms counterpart byte-identical;
zero edits, no pending execution)`
2. Q7 queue close (plan lines 982-983) -- append the CLOSED clause in
the Q2-Q6 pattern:
`- Q7: File `mutations__operations` (rest/resolvers hook/agreement
cites vs +129 -- scope at dispatch) -- CLOSED: stands at `bfaee91d`
(two-phase W2; vocabulary + (a)/R6/R8 hold, hardening touches no
operation-phase concept, forms counterpart byte-identical).`

PHASE-2-RECONCILIATION-RECORDED -- verdict: verified
