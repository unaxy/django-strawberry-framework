# DRY review: `mutation-discovery-own-snapshot-read`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

Rule: a mutation discovery default reads the backing class from the
class's OWN `_mutation_meta` snapshot when stamped, else from the live
`Meta` declaration - because class validation runs BEFORE the metaclass
stamps the snapshot (one window reads live, every later call reads
frozen-own). Derived owner (principle 7):
[mutations-sets][mutations-sets]`::snapshot_or_meta_backing` (new
helper; specified-not-landed, blocked-on-hunt).

What the rule owns: the stamp-timing fallback ORDER (own snapshot
first, live `Meta` second, own-namespace never MRO) shared by the two
backing-class discovery defaults. What it does NOT own: the snapshot
record or the stamp itself ([mutations-sets][mutations-sets] already
single-sites both), any post-bind plain read of a stamped slot (pure
consumers), or the per-flavor miss strictness (typed raise vs
pass-through - stays per-flavor, challenge C3).

The two definitions at WT bytes (`HEAD dd0b6691` + WT, pins below):

- D1, the form default:
  [forms-sets][forms-sets]`::_default_mutation_get_form_fields`
  (`forms/sets.py:191-214`): `truth.class_dict(cls).get("_mutation_meta")`
  -> `getattr(snapshot, "form_class", None)`, else
  `truth.static_attr(cls, "Meta", None)` ->
  `truth.static_attr(form_meta, "form_class", None)`, else typed
  `ConfigurationError("...cannot resolve Meta.form_class.")`.
- D2, the serializer default:
  [rest-sets][rest-sets]`::SerializerMutation.get_serializer_for_schema`
  (`rest_framework/sets.py:790-805`): `truth.class_dict(cls).get(...)`
  -> direct `meta.serializer_class`, else the strict double
  `truth.static_attr` chain off `cls.Meta`, then straight into the
  module-level discovery (a miss flows through as `None`).

Shared core (3 lines + the order): the own-namespace snapshot probe
over the same slot, the same two windows, the same stamp-timing fact
(both docstrings state it). Fair differences carried into the ownership
decision: the snapshot-arm spelling (tolerant `getattr` vs direct
access - observationally identical, `_ValidatedMutationMeta` always
carries both slots) and the miss strictness (typed raise vs
pass-through - genuinely different contracts, challenge C3).

Stamp side (single, already owned): the metaclass factory
[mutations-sets][mutations-sets]`::make_meta_validating_metaclass`
writes the slot exactly once at `mutations/sets.py:693`
(`_validate_meta` first, stash second - the order the fallback
exists for) and seals the class head (`__setattr__` / `__delattr__`
at `:699-725`); the record
[mutations-sets][mutations-sets]`::_ValidatedMutationMeta`
(`:833-870`, both backing slots always assigned) is the value both
arms read. Neither is a third definition of the fallback.

Sweep population: every `_mutation_meta` mention package-wide
(`grep -rn`, 40 hits across 11 files - closed, no second spelling of
the slot string exists) plus every `class_dict(...).get(...)` site
(29 hits) and every `get_serializer_for_schema()` /
`_default_mutation_get_form_fields` caller (census under `### Enumeration`).
Every hit is classified below; the fallback population is exactly 2.

## Verification

### Matrix

Discharged for the family as a whole (each axis searched, not sampled):

1. **Cross-flavor mirroring** - SEARCHED, this family. Form default
   (D1) vs serializer default (D2) vs model flavor (no discovery hook
   by construction: the model input comes from the snapshot's
   `input_class` / `partial_input_class` slots read post-bind, so no
   backing-class discovery window exists) vs plain-form flavor
   (shares D1's function object via `classmethod` at `forms/sets.py:593`
   and `:854` - one definition serving two classes, not two
   definitions). Consumer `get_form_fields` / `get_serializer_for_schema`
   overrides replace the default entirely (their own behavior, never
   members). No third flavor default after the full `_mutation_meta`
   census.
2. **Sync/async twins** - INAPPLICABLE with reason: discovery runs at
   class creation + finalize bind (synchronous windows, no awaits, no
   twin bodies); both defaults are plain classmethods with no async
   counterpart in either flavor.
3. **Derived rather than repeated** - SEARCHED: the live-`Meta` arm
   derives from the same declaration the snapshot froze, but that IS
   the fallback (the family's subject), not a second derivation of
   it. `types/base.py:686` (`truth.class_dict(cls).get("Meta")`)
   reads a DjangoType's own `Meta` for concreteness - different
   subject (type `Meta`, not mutation snapshot), excluded with
   contract difference under R5.
4. **Inverse / round-trip pairs** - SEARCHED: the write half (metaclass
   stash + head seal) is single-owned at
   [mutations-sets][mutations-sets]; this family is the read half.
   No second write site, no second seal, no encode/decode split beyond
   the one pair.
5. **Contracts in another medium** - SEARCHED: oracles pin VALUES
   (child serializer wins, post-declaration `Meta` mutation ignored,
   typed miss message) and never read the fallback spelling -
   independent oracles, listed under F1, never rewritten to compose
   the owner. Both bodies' docstrings state the stamp-timing rule -
   projections. No restatement to consolidate.
6. **Enforcement by omission** - SEARCHED: discovery-hook census is
   {form default, serializer default} + the model flavor's deliberate
   absence (no discovery hook exists there - inapplicable, not
   missing) + consumer overrides (out of contract by design). No
   member lacks a guard the rule requires; no defect.

### Enumeration

Instrument: `grep -rn '_mutation_meta' django_strawberry_framework/`
(40 hits, 11 files) + `grep -rn 'class_dict(.*).get'`
(29 hits) + caller censuses of both defaults. Every hit lands in F1
(definition), a consumer row, or an R-exclusion:

- F1 definitions (2): `forms/sets.py:202`,
  `rest_framework/sets.py:793`.
- Consumers - post-bind plain reads (stamped slot, no fallback, MRO
  read is correct because the executing class IS the bound class):
  `forms/resolvers.py:411`, `forms/sets.py:501`,
  `mutations/fields.py:273,316`, `mutations/resolvers.py:280,922`,
  `mutations/permissions.py:141`, `mutations/sets.py:1905`,
  `utils/write_transaction.py:288`,
  `rest_framework/resolvers.py:944,1155,1629,1972,2034,2234,2322,2339,2350`,
  plus `rest_framework/resolvers.py:1263` (None-guarded MRO read -
  consumer with a guard, still no live-`Meta` arm) and
  `schema.py:192` (R3, MRO-visible request-path read).
- Consumers - declarations / lifecycle: `forms/sets.py:864,866`
  (slot declaration), `mutations/sets.py:646-725` (stash + seal),
  `:1126,1128`, `:1493-1518` (protocol declarations).
- Exclusions with contract differences: R1 (`mutations/fields.py:124`
  presence-only boolean), R2 (`rest_framework/sets.py:937`
  `_input_type_name` bind-stash read), R3 (`schema.py:192`), R4
  (`auth/mutations.py` duck-typed snapshot), R5 (`types/base.py:686`
  own-`Meta` type read), R6 (patch-module `__dict__` descriptor
  reads). Each under `## Findings` with trigger.
- Caller census (both defaults are discovery-only, never on the query
  path): `cls.get_serializer_for_schema()` production callers are
  exactly `_validate_meta` (`rest_framework/sets.py:632`, window A)
  and `_checked_schema_field_map` (`:242`, window B, via
  `build_input` / `input_type_name`); `_default_mutation_get_form_fields`
  rides as the `classmethod` default on both form bases
  (`forms/sets.py:595,856`), reached via `_mutation_form_fields`
  from both flavors' `_validate_meta` + `build_input` /
  `input_type_name`. No resolver, permission, or request-path caller
  on either side.

### Challenges

Variation axes of the fallback (own-snapshot-or-live-`Meta` ORDER),
each with the definitions forced to move:

- C1 - stamp timing flips (metaclass stamps BEFORE `_validate_meta`
  runs): both `else` arms (live-`Meta` read) are deleted and both
  `if` arms simplify to direct own reads. Forced: D1 + D2 = **2**.
- C2 - own-read posture changes (nearest-stamped-snapshot MRO walk
  for intermediate bases, or a `truth.class_dict` contract change
  requiring a new own-read spelling): the probe line + the window
  logic move on both sides. Forced: D1 + D2 = **2**.
- C3 - miss strictness changes: reword/retarget the form's typed
  raise -> D1 only; change the serializer's `None` pass-through (at
  WT bytes `None` reaches `get_serializer_for_schema(None)` ->
  `None()` -> `TypeError`, `rest_framework/inputs.py:377-379`, the
  documented propagate-unchanged arm) -> D2 only. Forced: **1 + 1**,
  separate axes. Miss strictness is per-flavor and stays at the
  callers (principle 3 - same shape today, separate reasons to
  change: the form's raise is an oracle-pinned direct-call contract,
  the serializer's pass-through is validation-order fallout).
- C4 - slot/key axes: rename the snapshot slot (`form_class` /
  `serializer_class`) or the live-`Meta` key -> 1 site each (different
  slots, different keys). Per-flavor parameters of the helper, not
  shared definitions. Forced: **1** per axis.
- C5 (considered, NOT a family axis) - the `_mutation_meta` slot
  NAME is renamed: moves D1 + D2 + the R1 presence check + ~15
  post-bind consumers + the metaclass write/seal. A mechanical
  identifier rename across many rules, not this rule's variation;
  rowed as sub-rule S1 (rejected) for Worker-0.

Count verdict: the fallback ORDER has 2 authoritative definitions
(C1, C2); everything else about the two sites is per-flavor (C3, C4)
or a different rule (C5/S1). Consolidate the order; leave miss
handling and slot/key selection at the callers.

## Findings

### F1 - own-snapshot-or-live-Meta backing read (CONFIRMED, blocked-on-hunt)

- **Contract + variation.** When a discovery default runs during
  class validation (before the metaclass stamps the snapshot) it
  reads the backing class from live `Meta`; on every later call it
  reads the class's OWN stamped snapshot (never an inherited one).
  Varies on stamp timing (C1) and own-read posture (C2); slot/key
  selection (C4) and miss strictness (C3) are per-flavor inputs.
- **Sites + roles.** Definitions (2): D1
  [forms-sets][forms-sets]`::_default_mutation_get_form_fields`
  (WT `b8643610`, HEAD `76520347`) and D2
  [rest-sets][rest-sets]`::SerializerMutation.get_serializer_for_schema`
  (WT `0062e647`, HEAD `25f6c55c`). Stamp/write owner (not a
  definition of the read):
  [mutations-sets][mutations-sets]`::make_meta_validating_metaclass`
  + `::_ValidatedMutationMeta`. Consumers: the `### Enumeration`
  post-bind readers (compose the stamped slot by name; untouched by
  this family). Oracles (independent, pin values never the fallback
  spelling):
  [test-rest-sets][test-rest-sets]`::test_subclass_redefining_serializer_validates_against_child_serializer`
  (D2 window A: child serializer wins over the parent snapshot -
  fails if the fallback reads MRO-visible state);
  [test-forms-sets][test-forms-sets]`::test_default_get_form_fields_uses_frozen_form_class_snapshot`
  (D1 window B: post-declaration `Meta` mutation ignored);
  [test-forms-sets][test-forms-sets]`::test_default_form_field_hook_rejects_a_class_without_form_metadata`
  (D1 miss: typed raise). Projections: both bodies' stamp-timing
  docstrings.
- **Challenges.** C1 count 2; C2 count 2; C3 1+1 (stays separate);
  C4 1 per axis (helper parameters); C5 out of family (S1).
- **Owner + lifetime.** [mutations-sets][mutations-sets] via a new
  `snapshot_or_meta_backing(cls, slot, key)` helper (principle 7:
  it owns the metaclass factory - the source of the stamp-timing
  fact - and the snapshot record; both flavors already import it
  at runtime (`forms/sets.py:55-78`, `rest_framework/sets.py:71-90`)
  so no dependency reverses and the helper adds no new edge - it
  needs only `truth`, and the sole forms reference in
  [mutations-sets][mutations-sets] is a `TYPE_CHECKING` import at
  `:96`. The forms-default alternative would force a new
  sibling-flavor runtime edge (`rest_framework` -> `forms` for
  machinery), which principle 7 forbids. Reads: the class's own
  namespace + live `Meta` (both reads, no effects). Lifetime:
  per-call derivation, "not cached" (principle 4). Enforcement
  authority: none beyond the read - miss strictness stays with the
  callers). No stored derivation.
- **Migration (specified-not-landed; the landing pass applies it
  verbatim once the hunt's lines land).** At
  [mutations-sets][mutations-sets], beside `require_backing_class`
  (`mutations/sets.py:299`, the presence-clause precedent):
  `snapshot_or_meta_backing(cls: type[object], slot: str, key: str)
  -> object` returning the backing class or `None`: own snapshot
  via `truth.class_dict(cls).get("_mutation_meta")`; snapshot arm
  via PLAIN `getattr(snapshot, slot, None)` - required, not style:
  the snapshot is slotted (`__slots__` at `:854-870`), so
  `truth.static_attr` would return the member descriptor uninvoked
  (`_is_data_descriptor` true at `truth.py:370`, `instance_dict`
  `None` for slotted instances at `truth.py:399`); live arm via
  `truth.static_attr(cls, "Meta", None)` then
  `truth.static_attr(meta, key, None)` (tolerant chain -
  `static_attr` defaults to `None`, never raises, `truth.py:437`).
  D1 becomes `form_class = snapshot_or_meta_backing(cls,
  "form_class", "form_class")` + its unchanged typed raise +
  `get_form_fields(form_class)` (identical all paths: same
  snapshot `getattr`-default, same tolerant chain, same raise).
  D2 becomes `serializer_class = snapshot_or_meta_backing(cls,
  "serializer_class", "serializer_class")` + unchanged
  pass-through (identical all paths at WT bytes: direct slot
  access is equivalent to the `getattr`-default since both slots
  always exist and are always assigned; the live arm spells the
  identical tolerant chain; the `None` miss reaches the identical
  downstream `TypeError`). Full docstring on the helper (new public
  symbol); no new `Any` token (`object` in/out, callers keep their
  casts - no `ALLOWED_ANY` change); the moved `getattr` line keeps
  the truthful-reads verdict (same pattern, both files in scope -
  the landing pass re-runs all three gates).
- **Distinct behavior.** Miss strictness stays per-flavor (D1's
  typed raise, D2's pass-through); slot/key selection stays at the
  call sites as helper arguments. Recorded here and in the helper
  docstring at landing.
- **Behavioral proof.** D2 window A `execution-verified`: the
  subclass oracle passes at WT bytes (this pass's one shared-tree
  probe, `1 passed`, command under `## Pending execution` -
  rejects "the fallback reads the parent snapshot"). D1 windows +
  miss `static-reviewed` (both bodies + the closed 40-hit census +
  oracle bodies read at pinned WT blobs - rejects "a third window
  or caller exists"). Post-migration equivalence `execution-deferred`
  (no migration landed - blocked): the 3-node oracle re-run is the
  `proof:` entry. Principle-8 coverage: return values in both
  windows + the exact miss outcomes (`ConfigurationError` /
  `TypeError`) are preserved per the arm-by-arm analysis above;
  no query, transaction, or async effects exist on these paths.
- **Structural gate (specified-not-landed).** A spy gate at the
  owner: `test_mutation_discovery_routes_through_snapshot_or_meta_backing`
  monkeypatches
  [mutations-sets][mutations-sets]`::snapshot_or_meta_backing`
  (call-counting wrapper), exercises D1 + D2 in window A (fresh
  subclass declaration per flavor) and window B (post-stamp call),
  and asserts each default routed through the helper in both
  windows. Negative control: a hand copy of the helper body inlined
  into one default - every behavioral oracle still passes (the copy
  is correct) while the spy gate fails (no helper call). The
  landing pass authors the gate + proves it via
  `scripts/workspace.py prove` on a failability manifest, then runs
  the `proof:` entries. Unrunnable until the helper lands (no
  bespoke existence test - the spy asserts routing, not a name).
- **Coupling.** The hunt's truth-migration WIP on both bodies (the
  blocking hunks below) + the hunt-owned `utils/truth.py`
  (untracked, WT `711352b1`, no HEAD/baseline blob): the migration
  is specified at WT bytes and its freshness fingerprints decide
  staleness - any hunt rewrite of these lines reopens F1 before
  landing. No other finding couples.
- **Freshness.** WT (`git hash-object`) / HEAD (`git rev-parse`)
  / ITEM_BASELINE (`abee4c21...`, equals WT on all tracked paths -
  no drift since dispatch; dispatch pins re-verified same-kind):
  `forms/sets.py` `b8643610` / `76520347` / `b8643610`;
  `rest_framework/sets.py` `0062e647` / `25f6c55c` / `0062e647`;
  `mutations/sets.py` `a1035397` / `50f9d6a1` / `a1035397`;
  `mutations/fields.py` `3368f696` / `0fada991` / `3368f696`;
  `schema.py` `c3f267aa` / `f3b6df8f` / `c3f267aa`;
  `types/base.py` `e7a62d32` / `e0ad32aa` / `e7a62d32`;
  `rest_framework/resolvers.py` `08310034` / `5e80bbf7` / `08310034`;
  `rest_framework/inputs.py` `af8cea5c` / `6ad29171` / `af8cea5c`;
  `auth/mutations.py` `8d9e8561` / `101dbf82` / `8d9e8561`;
  `tests/forms/test_sets.py` `dca57bfc` / `7d4c0da6` / `dca57bfc`;
  `tests/rest_framework/test_sets.py` `078e8486` / `ff621ce8` /
  `078e8486`; `utils/truth.py` WT-only `711352b1` (untracked -
  verified absent at HEAD and baseline via `rev-parse --verify`).
  Searched population: 40 `_mutation_meta` hits / 11 files, 29
  `class_dict.get` hits, both caller censuses (above). Contract
  sources: the metaclass order (`mutations/sets.py:686-697`), the
  slot record (`:854-870`), the three oracle bodies. Excluded
  modules (body-read): R1-R6 + every `### Enumeration` consumer.
- **BLOCKED-ON-HUNT (zero edits made).** Both definition bodies
  are inside hunt-dirtied hunks (truth migration; no
  `## Owned changes` row covers either file; attributed by diff
  content vs `git show HEAD:<path>`); any consolidation edit would
  touch them, so per the binding concurrency rule nothing was
  touched. Exact hunks:
  (1) `forms/sets.py @@ -194,55 +199,78 @@`: the
  `_default_mutation_get_form_fields` rewrite (`cls.__dict__.get`
  -> `truth.class_dict(cls).get`, `getattr` -> `truth.static_attr`
  x2, `cls.__name__` -> `truth.name`, + the neighboring
  `_require_zero_arg_form_fields_declaration` insertion).
  (2) `rest_framework/sets.py @@ -796,17 +777,31 @@`: the
  `get_serializer_for_schema` discovery rewrite (`cls.__dict__.get`
  -> `truth.class_dict` + cast, `cls.Meta.serializer_class` ->
  strict double `truth.static_attr` + cast, docstring reword).
  (`mutations/sets.py` is likewise hunt-dirty, 238 changed lines,
  so the helper insertion point is also unavailable - but the two
  call-site hunks block regardless.) WT-vs-HEAD behavioral delta
  owned by the hunt (observed, NOT filed - concurrent WIP): the D2
  miss path changed from raw `AttributeError`
  (`cls.Meta.serializer_class` at HEAD) to `None` pass-through
  (`static_attr` default-`None` at WT). The migration above is
  specified at WT bytes.

### R1 - `mutations/fields.py:124` presence-only guard (excluded)

`truth.class_dict(mutation_cls).get("_mutation_meta") is None` ->
raise. No value read, no live-`Meta` arm, no fallback: it answers
"concrete with own `Meta`?" for field-target validation, a
different contract (concreteness + ledger currency,
`mutations/fields.py:106-135`). A C1/C2 change to the fallback
order does not move it (it would still probe concreteness the same
way). Trigger: the guard starts READING the backing (or any slot
value) off the probed snapshot instead of testing presence.

### R2 - `rest_framework/sets.py:937` `_input_type_name` stash read (excluded)

`truth.class_dict(cls).get("_input_type_name")` - an own-namespace
bind-stash read over a DIFFERENT slot with no `Meta` fallback and
no stamp-timing hazard (bind outputs, not discovery). Same
mechanism family (own-namespace read), different rule. Trigger: the
stash read gains a live-declaration fallback arm.

### R3 - `schema.py:192` MRO-visible request-path read (excluded)

`truth.static_attr(mutation_cls, "_mutation_meta", None)` + getattr
model default at execution time. MRO-visible BY DESIGN (the
executing class is the bound class; no validation window exists at
request time) with no fallback arm - the opposite visibility
contract from F1's own-only rule. Trigger: execution-time discovery
of an unstamped class gains meaning (it cannot today - execution
implies stamped).

### R4 - `auth/mutations.py::_AuthMutationMetaSnapshot` (excluded)

A deliberately-NOT-`_ValidatedMutationMeta` duck-typed shape
(`permission_classes` + pinned `operation`, no backing-class slots,
no discovery hook, no live-`Meta` arm -
`auth/mutations.py:219-229`). Different subject (fixed-surface
permission holder), different contract. Trigger: an auth surface
grows backing-class discovery.

### R5 - `types/base.py:686` own-`Meta` type read (excluded)

`truth.class_dict(cls).get("Meta")` for DjangoType concreteness -
reads the `Meta` object itself on a different class family (types,
not mutations), not a snapshot, with no fallback. Trigger: type
registration grows a snapshot-then-`Meta` fallback.

### R6 - patch-module `__dict__` descriptor reads (excluded)

`_cross_web_patches.py`, `_django_patches.py`,
`_graphql_core_patches.py`, `_strawberry_patches.py`
`truth.class_dict(...).get(...)` sites read install/capture
descriptors for upstream patching - different domain (patch
lifecycle), different slots, no `Meta` fallback. Trigger: none
plausible within this rule (a patch module growing mutation
discovery).

### S1 - the `_mutation_meta` slot-name spelling (sub-rule, rejected)

Every `_mutation_meta` spelling (F1 x2, R1, ~15 post-bind
consumers, the metaclass write/seal) names one slot. Consolidating
the NAME into a shared constant is rejected: attribute names are
spelled at use by language design; a constant breaks greppability
(the 40-hit census above IS the ownership instrument), litters
every plain consumer read, and relieves no change obligation (a
rename is a mechanical identifier sweep, identical cost with or
without the constant - C5). Durable home: none owed (no owner prose
claims otherwise). Trigger: the slot name must vary per flavor or
be computed at runtime (today it is one literal by construction).

## Defects

None filed. One candidate examined and cleared on-record (not a
defect): the WT-vs-HEAD D2 miss-path delta (raw `AttributeError` ->
`None` pass-through) is uncommitted hunt WIP inside the blocking
hunk (2) above - concurrent work, out of scope, explicitly not
homed. No guard is missing on any family member (matrix axis 6);
no docstring contradicts its body (both stamp-timing docstrings
match their WT bodies line for line).

## Pending execution

- `proof: uv run pytest -n0 tests/rest_framework/test_sets.py::test_subclass_redefining_serializer_validates_against_child_serializer tests/forms/test_sets.py::test_default_get_form_fields_uses_frozen_form_class_snapshot tests/forms/test_sets.py::test_default_form_field_hook_rejects_a_class_without_form_metadata --no-cov`
  - Discharges F1 post-migration equivalence (both windows + the
    form miss). Before-side: node 1/3 `execution-verified` green
    at WT `0062e647` by this pass's probe (run id evidence: `1
    passed in 0.12s`, HEAD `dd0b6691`); nodes 2-3/3 cited
    `static-reviewed` (bodies read at WT `dca57bfc`, single-probe
    budget spent). Meaningful as an equivalence proof when re-run
    post-landing; the final gate runs it as listed.
- `proof (landing-owed, unrunnable until the F1 gate lands):
  uv run python scripts/workspace.py prove dry/mutdisc-f38/consolidate <manifest>`
  - The landing pass authors the failability manifest (hand copy of
    `snapshot_or_meta_backing` inlined into one default -> spy gate
    red, all three oracle nodes green), runs it, and records the run
    id in F1. Listed so the obligation survives; the final gate must
    NOT run this line before the landing pass replaces `<manifest>`
    with the authored path.

No `gate:` entries. Sharded/PG cells: inapplicable by construction
(discovery runs at class creation + finalize bind with no database,
alias, or dialect decision - no queryset, no `using`, no backend
probe; verified by body read of both defaults + the helper spec) -
for Worker-2 to judge.

## Judgment

CONFIRM-blocked: the own-snapshot-or-live-`Meta` fallback is one
rule with exactly 2 authoritative definitions (C1 + C2 count 2,
population closed at 40 hits); the owner is derived as
[mutations-sets][mutations-sets] via a specified
`snapshot_or_meta_backing` helper; miss strictness (C3) and
slot/key selection (C4) stay per-flavor; six exclusions + one
sub-rule carry contract differences with triggers. Zero edits: both
definition bodies sit inside hunt-dirtied hunks (quoted above), so
the migration + spy gate are specified-not-landed with freshness
fingerprints, one executed probe (D2 window A green), and two
deferred proofs. No defects.

## Index rows for Worker-0

Worker-0 transcribes verbatim; Worker-0 authors nothing. 2 rows
(1 family status + 1 sub-rule rejection):

| `mutation-discovery-own-snapshot-read` | `django_strawberry_framework/mutations/sets.py::snapshot_or_meta_backing` (derived by family item run 0.0.15 2026-10-01-11; helper specified-not-landed) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/mutations/sets.py` | Family `mutation-discovery-own-snapshot-read` | open (F1 CONFIRMED count-2 but blocked-on-hunt: `forms/sets.py @@ -194,55 +199,78 @@` + `rest_framework/sets.py @@ -796,17 +777,31 @@`; migration + spy gate specified, zero edits; verified, pending execution) |
| `mutation-snapshot-slot-name` | `django_strawberry_framework/mutations/sets.py` (slot writer; rejection recorded here) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` (+ ~15 post-bind consumers) | Family `mutation-discovery-own-snapshot-read` | rejected (S1: attribute names spelled at use by language design; a constant breaks the grep census and relieves no rename obligation; trigger: the slot name must vary per flavor or be computed at runtime) |

## Independent verification (Worker-2)

Recorded before reading `## Findings` (only the section
map + `## Judgment` tail + `## Index rows` were open for
placement). All counts re-derived at WT bytes, HEAD
`dd0b6691`.

### Own trace: sites + roles

Rule: a mutation discovery default reads the backing
class from the class's OWN validated `_mutation_meta`
snapshot when the metaclass has stamped it (bind window),
else from the live `Meta` declaration (class-creation
window, before the stamp exists).

- D1 (definition):
  [forms-sets][forms-sets]`::_default_mutation_get_form_fields`
  (WT :191-214; HEAD :~186-209) - own-snapshot
  `form_class` read, live-`Meta` fallback, `None` ->
  `ConfigurationError("...cannot resolve Meta.form_class.")`,
  then `get_form_fields` discovery.
- D2 (definition):
  [rest-sets][rest-sets]`::SerializerMutation.get_serializer_for_schema`
  default body (WT :790-805; HEAD :~808-810) -
  own-snapshot `serializer_class` read, live-`Meta`
  fallback, then module-level discovery delegate.
- Owner I choose:
  [mutations-sets][mutations-sets]`::snapshot_or_meta_backing`
  (new helper, specified-not-landed) - owns the slot
  lifecycle (stamps + seals `_mutation_meta`) and the
  `_ValidatedMutationMeta` record; both flavors already
  import from it, so no dependency reverses. Forms-as-owner
  would force a sibling import (`rest_framework` -> `forms`);
  rejected.
- Consumers: the 2 form `classmethod(...)` bindings
  (:595, :856); `cls.get_serializer_for_schema()` call
  sites (`_validate_meta` :632, `_checked_schema_field_map`
  :242); `_mutation_form_fields` hook invocation.
- Oracles (independent, spell expectations): the form
  miss test, the serializer subclass-own-snapshot test, the
  override-drives-bind test, the determinism fingerprint
  tests, the library live-query tests.
- Projections: both defaults' docstrings, spec-039 prose,
  example comments.

### Own trace: definition counts

- C1 (stamp-timing fallback ORDER: own snapshot first,
  live `Meta` second): D1 + D2 move together. Count 2.
- C2 (own-namespace read mechanism for the snapshot):
  D1 + D2 move together (`cls.__dict__.get` at HEAD,
  `truth.class_dict(cls).get` at WT - the migration moved
  both spellings in lockstep, which is itself evidence of
  one rule). Count 2.
- C3 (miss strictness): 1+1 per-flavor, stays separate.
  Form arm: `None` -> `ConfigurationError`. Serializer
  arm: `None` flows into discovery -> `TypeError` at WT
  (`None()`); `AttributeError` at HEAD
  (`cls.Meta.serializer_class` direct). Verified by
  execution below.
- C4 (backing slot/key selection): 1-per-axis,
  parameterized (`form_class` vs `serializer_class`).

### Own trace: censuses (WT source bytes, `__pycache__` excluded)

- `_mutation_meta`: 59 source lines (39 code + 20
  prose), across 11 files. Both F1 definitions are the
  only `class_dict(...).get("_mutation_meta")` fallback
  bodies; the rest are the slot lifecycle (stash + seal),
  post-bind MRO-visible reads, presence guards, the
  auth duck-type, declarations, and prose.
- `truth.class_dict(...).get(`: 29 lines, every one
  enumerated (2 F1 bodies + `mutations/fields.py:124`
  presence guard + `rest_framework/sets.py:937`
  `_input_type_name` stash read + 25 unrelated-slot
  reads). Closed.
- Callers: `_default_mutation_get_form_fields` has 3
  production references (def + 2 bindings) + 2 test
  references (import + direct miss-call); the serializer
  classmethod hook has 2 production call sites + the
  override/drives-bind oracle family. The module-level
  `rest_framework/inputs.py::get_serializer_for_schema`
  is a same-named distinct rule (discovery from a
  serializer class, no snapshot read) - excluded.

### Own trace: matrix discharge

1. Cross-flavor mirroring: searched. The model flavor
   has no discovery default (no hook, nothing missing -
   no contract source requires one). Form + serializer
   are the full population. Discharged by search.
2. Sync/async twins: both defaults are pure sync
   classmethods at class-creation/bind; no await
   boundary, no twin. Inapplicable with reason.
3. Derived knowledge: the backing class is READ (snapshot
   or `Meta`), never re-derived from `_meta`/model on
   either path. No second derivation. Discharged.
4. Inverse/round-trip pairs: no encode/decode pair for
   this read. Inapplicable with reason.
5. Contracts in another medium: docstrings (projections),
   spelled test expectations (oracles), spec-039 prose
   (projection). Classified, none counted as definitions.
6. Enforcement by omission: discovery-hook defaults
   enumerated - form (ONE body shared by both bases,
   already single) + serializer (one body). Model flavor
   has no hook by contract (nothing to enforce).
   Discharged, no gap.

### Own trace: observable equivalence (principle 8)

Executed at WT (`docs/dry/temp-tests/mutdisc-f38/`,
4/4 green) + 3 focused oracles (green):

- Both windows resolve the same backing class per arm
  (snapshot arm wins over live `Meta` when stamped -
  probed on both arms with a stale-`Meta` probe class).
- Exact miss outcomes differ per arm and must stay
  per-arm: form `ConfigurationError`
  ("cannot resolve Meta.form_class"); serializer
  `TypeError` at WT (HEAD: `AttributeError` - the
  truth migration changed this arm's miss outcome by
  replacing a direct `cls.Meta.serializer_class` read
  with a `None`-defaulting `static_attr` chain;
  concurrent behavior delta, owned by the hunt).
- Exception point, short-circuit order (snapshot check
  before any `Meta` touch), and zero query/transaction
  effects are identical across arms; only the miss
  type + message stay per-flavor (C3).

### Own trace: block call

Both definition bodies sit inside concurrent
truth-migration hunks (re-derived from `git diff HEAD`:
`forms/sets.py @@ -194,55 +199,78 @@`,
`rest_framework/sets.py @@ -796,17 +777,31 @@`);
`## Owned changes` names neither file (nor
`mutations/sets.py`, the specified helper home, which is
itself hunt-dirtied); `utils/truth.py` (which any
landing-time helper body must read through) is untracked
concurrent work. Zero legal partial landings: the helper
cannot land in a hunt-dirtied file, the call-site
migration touches both hunt hunks, and landing the helper
against a different read spelling would mint a third
spelling of the rule. BLOCKED-ON-HUNT, zero edits. Agree.

### Reconciliation with `## Findings` (read after the above)

- F1 CONFIRM count-2 + owner
  `mutations/sets.py::snapshot_or_meta_backing`
  (specified-not-landed): AGREE - same sites, same
  roles, same counts (C1/C2 count 2, C3 1+1 per-flavor,
  C4 1-per-axis), same owner with the same dependency
  reasoning.
- C3 miss outcomes: AGREE -
  `ConfigurationError`/`TypeError` per arm at WT,
  verified by my own execution (not inherited).
- R1-R6 + S1: AGREE on all seven dispositions - each
  carries a contract difference + trigger. Pre-reading
  my trace had deeply analyzed R1-R4 + S1 equivalents
  and had R5/R6 sites inside the closed 29-census
  (not yet dispositioned); post-reading I confirm all
  six exclusions on their stated contract differences
  (presence-only vs value read; different slot;
  MRO-visible-by-design vs own-only; duck-typed
  non-record; type-`Meta` vs snapshot; patch-domain
  descriptors) and triggers.
- Census size: DIFFERENCE RECORDED + CLOSED HERE - my
  WT source census is 59 `_mutation_meta` lines (39 code
  + 20 prose) across the same 11 files, not 40; the 29
  `class_dict.get` count reproduces exactly. The 40-hit
  figure is reproducible at NO state (WT 59, HEAD 65,
  ITEM_BASELINE 59 - and W1's own no-drift claim makes
  baseline == WT, so 40 contradicts the artifact
  internally). Against my 59: W1's `### Enumeration`
  homes 48 by line/range/file, 4 more implicitly (F1
  "both bodies' stamp-timing docstrings" ->
  `forms/sets.py:196`, `rest_framework/sets.py:782,783`;
  "the record (`:833-870`)" ->
  `mutations/sets.py:844`), leaving 7 genuinely
  homeless, homed here: (i) `mutations/fields.py:158`
  (CODE) - the `_has_mutation_protocol` MRO-visible
  EXISTENCE probe ("present even as `None`"), an
  R1-sibling exclusion: no value read, no live-`Meta`
  arm, opposite visibility posture from R1's own-only
  concreteness check; trigger: the protocol check reads
  a snapshot VALUE or gains a fallback arm - provably
  not a third definition (read the body); (ii) 6 prose
  projections: `mutations/fields.py:86,88` (R1-function
  docstring), `:150` (protocol-function docstring),
  `:298` (consumer-field docstring),
  `mutations/sets.py:1172` (a SUBSTRING hit inside
  `_validate_mutation_meta`, not the slot at all),
  `rest_framework/sets.py:630` (window-A comment,
  F1-adjacent). Verdict-neutral (closure re-derived at
  59 with exactly 2 fallback bodies), so recorded here
  per the "do not spend the verdict asking Worker-1 to
  write it" rule - not a revision driver. Worker-0
  closeout wording should read 59/39, not 40.
- Freshness instrument note: all 11 tracked pins
  re-hashed same-kind and match W1 exactly
  (WT/HEAD/BASE, BASE==WT - no drift since dispatch);
  `utils/truth.py` WT `711352b1` matches and its HEAD +
  baseline absence is confirmed - but via
  `git cat-file -e` (exit 128, "not in"), NOT W1's
  cited `rev-parse --verify`, which errors on a
  `REV:path` argument regardless and so proves nothing.
  Fact stands, instrument corrected here.
- Freshness fingerprints: AGREE - WT/HEAD pins
  re-hashed same-kind and match
  (`b8643610`/`76520347`, `0062e647`/`25f6c55c`).
- Structural gate (specified spy gate): AGREE - the
  negative control (helper body inlined into one
  default) is sound: behavior oracles stay green on a
  correct copy while the routing assertion fails; only
  the routing assertion can catch the bypass.
- `## Pending execution` typing: AGREE - `proof:` for
  the deferred oracle re-run, `proof:` (flagged
  not-to-run-early) for the landing-owed failability
  manifest; no `gate:` owed on a zero-edit item.
- Block call: AGREE (see above).

### Gates + checks (Worker-2)

- Ruff: VACUOUS - the item diff vs ITEM_BASELINE is the
  plan edit alone (verified: `git diff abee4c21...` over
  both targets is empty; only new file is this untracked
  artifact). No tracked `.py` touched, nothing to
  check. My scratch probes
  (`docs/dry/temp-tests/mutdisc-f38/`, temp, Worker-0
  removes) are `ruff check` + `ruff format --check`
  clean.
- Type gates (all three re-run by me at WT, vs run-11
  baseline): `uv run basedpyright` -> `0 errors, 0
  warnings, 0 notes` (baseline 0/0/0); `uv run python
  scripts/check_any.py` -> `128 allowed use(s) of Any
  at 89 site(s)` (baseline 128/89); `uv run python
  scripts/check_truthful_reads.py --check` -> `tier-1 0
  ... errors 0` (baseline tier-1 0). All green, all
  match. mypy never run, never cited (gone).
- Point (a) judgment: W1's nothing-to-judge claim is
  REJECTED as reasoning - the gates judge tree state,
  and the artifact makes gate-relevant assertions (the
  migration's no-new-`Any` shape, the kept
  truthful-reads verdict) that only a gate run can
  ground. Outcome moot-green (above); the landing pass
  re-runs all three regardless (freshness).
- Proof entry 1 (3-node oracle re-run): ran EXACTLY as
  listed at WT -> `3 passed in 0.12s`. All three nodes
  exist and are green. Point (b) judgment: the bare
  `uv run pytest` form is ACCEPTABLE and is the only
  gate-runnable form - item `workspace.py` addresses
  are released after verification, so by gate time no
  `dry/mutdisc-f38/...` address exists; the gate runs
  pending commands as listed in its own copy. The
  `workspace.py run` form is for source-mutating
  proofs; this oracle re-run mutates nothing.
- Proof entry 2 (failability manifest): correctly typed
  `proof`, correctly flagged not-to-run-early
  (`<manifest>` placeholder, helper unlanded). The
  landing pass replaces it with the authored manifest +
  run id. No `gate:` owed on a zero-edit item.
- Junk-own-value precision (my 5th probe): D2 at WT
  with a non-snapshot own `_mutation_meta` raises
  `AttributeError` (direct slot read), while the
  specified `getattr`-default helper would yield
  `None` -> `TypeError` there. Uncontracted path (the
  metaclass seal makes it unreachable on real mutation
  classes; no oracle pins it) - recorded for
  exactness, not a defect, not a migration blocker.
- Sharded/PG: AGREE inapplicable-by-construction - both
  defaults + the helper spec touch no database, alias,
  or dialect decision (class-namespace reads +
  form/serializer object construction only).
- Banned test words: scratch probes clean (grep
  negative); no new test/production files committed.
- Observed-not-homed (concurrent prose drift, same
  handling as W1's cleared delta):
  `tests/rest_framework/test_sets.py:1020` still says
  "via ``cls.__dict__``" while the WT body reads via
  `truth.class_dict` - hunt-migration fallout, owned by
  the hunt, no contract row broken (test prose, not an
  oracle predicate). Not a defect.

### Verdict input

Zero-edit CONFIRM-blocked stands: F1 count-2 + owner +
migration/gate specs correct, block call agreed, gates
green at baseline, proofs typed and entry 1 validated.
Record-accuracy corrections (census 40 -> 59/39 with
the 7 homeless homed; freshness instrument) carried
above. No defect. Status set `verified`; plan item
reads `verified, pending execution` (two `proof:`
entries remain).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[rest-sets]: ../../django_strawberry_framework/rest_framework/sets.py

<!-- tests/ -->
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-rest-sets]: ../../tests/rest_framework/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

