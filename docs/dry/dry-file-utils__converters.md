# DRY review: `utils/converters.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target
`django_strawberry_framework/utils/converters.py` is the
single owner of the fail-loud converter-dispatch
skeleton: ordered `isinstance` prechecks, then a scalar
registry MRO walk, then a raising fallthrough. Four
riding call sites compose it by name (two write-field
converters plus the filter convert / normalize pair);
the value-shape factories and the post-walk invoke split
are shared the same way. No production edits; no plan
edits; nothing tracked touched.

Trace basis is HEAD bytes throughout
(`5332f0542c0bd180aee30de95ec091933b54ee34`).
The worktree state
(`3f5e6e1803e96afb61084d541d76e9e5956881f7`,
185 lines) carries 3 hunks (7+/13-) of
concurrent-external dirt, attributed by content below;
the item-scoped diff vs `ITEM_BASELINE`
(`7249b48ac43899b937910821083097b9bbe539ab`)
is empty on this path (the baseline was taken on the
dirty tree, so the dirt predates the item). The plan's
`## Owned changes` ledger carries no row naming this
file (verified: rows cover `optimizer/walker.py`, three
test files, and the fourteen 09-19 adopted orphans).
HEAD is `0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`
at dispatch and at writing (unmoved).

### Hunk attribution (HEAD -> worktree)

All three hunks are the hunt's truth-migration,
mechanical and content-identical in kind to the same
migration visible across the worktree
(`types/converters.py` worktree `_class_map_lookup`,
the inspect-CLI leg, the `from ..utils import truth`
imports both write converters now carry):

- Hunk 1 (imports): `+from . import truth`.
  `utils/truth.py` is untracked (`??` in `git status`)
  and absent at HEAD (`git show HEAD:...truth.py`
  fails). A new import of a hunt-owned untracked
  module cannot be ledgered DRY work.
- Hunk 2 (docstring): the phase-2 read-mechanism
  sentence retargeted from the raw getset descriptor
  to `truth.mro`. Prose half of the same migration.
- Hunk 3 (body): `type.__dict__["__mro__"].__get__`
  plus the 8-line hostile-metaclass comment becomes
  `truth.mro(type(field))` plus a 2-line comment;
  the identity-scan comment trims from 4 lines to 2.
  Code half of the same migration.
  Behavioral equivalence is `static-reviewed`:
  worktree `truth.mro` resolves through the same
  `type.__dict__["__mro__"]` slot
  (`_get_mro = _TYPE_SLOTS["__mro__"].__get__`;
  `is_type` is true for `type(field)`), and the
  identity scan plus registry snapshot are
  byte-identical. Execution proof would re-run the
  hostile-MRO oracles; that run is not sought (no
  test run is authorized in the shared tree, and a
  file item owes no production edit the proof would
  discharge).

Connected sources read whole or at the riding seam:
the three riders (`forms/converter.py`,
`rest_framework/serializer_converter.py`,
`filters/inputs.py` convert + normalize),
`utils/inputs.py` (`SCALAR`, `FieldConversionBase`),
the FAM-MRO legs (`types/converters.py` at HEAD
`058f1081…`, `inspect_django_type.py` at HEAD
`2807d0fc…`), the non-riding converters
(`mutations/inputs.py` kind classifier,
`orders/inputs.py` leaf annotation), the five other
package MRO scans (finalizer, relay, definition,
sets-mixins, querysets bodies), the oracles
(`tests/utils/test_converters.py` CLEAN at
`447fa2c5…`,
`tests/rest_framework/test_dry_import_ratchet.py`
CLEAN at `595e0f39…`), and the contract sources
(spec-039
Decision 4 + Decision 7, spec-053 C3, the GOAL
no-silent-`String` contract).

## Verification

### Matrix

1. **Cross-flavor policy mirroring** -- searched.
   Read-side dispatch (`types/converters.py` scalar +
   output walks) vs this skeleton: different key
   spaces over different field populations (R1,
   CONVERGE with the verified table direction on a
   fresh census). Mutations model-input triple: a
   total classifier with a `SCALAR` default, no
   registry walk (R2, fresh). Orders leaf
   annotation: single-kind mapping (R3, fresh).
   Filter form-field ladder: fallback typing where
   no model field backs the filter (CONVERGE with
   verified R11 -- re-read, trigger unfired).
   Instrument: package census for `__mro__` /
   `truth.mro` / `singledispatch` / `registry`
   (reported in R6) plus full reads of every
   converter pair.
2. **Sync/async twins** -- inapplicable by
   construction. Instrument: `grep` for
   `async|await|except|try:` over both target
   states returns only the `scalar_registry`
   substring; zero `AsyncFunctionDef`, zero ORM
   access. Pure class-creation dispatch; the async
   resolver pipelines consume the converter's
   output kinds, never the mapping.
3. **Derived rather than repeated knowledge** --
   searched. The only second derivations of "which
   MRO ancestor fires" are the three FAM-MRO legs
   (family convergence, below) and the CLI naming
   predictor (a family member). No other site
   derives a firing row: the census in R6 names
   every remaining MRO scan and its distinct
   question.
4. **Inverse / round-trip pairs** -- searched. The
   filter convert / normalize pair is the round
   trip whose KIND ORDER is single-sited here:
   both ride the skeleton over the one
   `_filter_input_prechecks` table (spec-053 C3),
   so a new primitive cannot be typed on one
   ladder and coerced on the other. `make_*` are
   constructors and `finish_field_conversion` is
   the post-walk invoke; neither owns an inverse,
   and the raising fallthrough has no decode half
   by construction.
5. **Contracts restated in another medium** --
   searched. Contract sources: spec-039 Decision 4
   (skeleton home) + Decision 7 (serializer
   mapping), spec-053 C3 (filter kind order), GOAL
   ("unmapped field RAISES, never silently becomes
   `String`"). Projections: the three riders'
   module docstrings (each states the skeleton +
   the no-catch-all posture; verified against the
   bodies). Oracles: the 18-test skeleton suite
   (12 skeleton + 3 `make_*` + 1 finish + 2
   `__code__` pins, counted at the CLEAN file)
   (independent literals, never read from the
   owner), the import-identity ratchet, the flavor
   MRO/subclass rows. No medium restates the walk
   mechanics a second time.
6. **Enforcement by omission** -- searched, no
   defect. Riders: form convert, serializer
   convert, filter convert, filter normalize.
   Non-riders: read-side dispatch (R1), mutations
   triple (R2), orders leaf (R3), the form-field
   ladder (R11). No contract source (spec, glossary
   anchor, owner prose, oracle) requires any
   non-rider to ride the skeleton; each omission
   carries a contract difference below. Nothing
   routes to the maintainer.

### Enumeration

Instrument: `ast.Module.body` census of both target
states. HEAD: 12 members. Worktree: 13 members
(+1: the dirt import, member 5, homed in the hunk
attribution above, not as a rule). Nested defs
(`_MroContinue.__repr__`,
`make_kind_converter._convert`) home with their
parents. Every member lands below; line numbers
are HEAD bytes at `5332f054…`.

| # | Member (HEAD) | Home |
|---|---|---|
| 1 | Module docstring (:1-28) | F-MECH (projection; 7 claims verified) |
| 2 | `__future__` import (:30) | F-MECH |
| 3 | `Callable` import (:32) | F-MECH |
| 4 | `Any` import (:33) | F-MECH |
| 5 | `from . import truth` (worktree :35 ONLY) | Dirt; see hunk attribution |
| 6 | `.inputs` import (:36 HEAD) | F-VALUE + F-FINISH consumer |
| 7 | `__all__` (:38; 5 names) | F-MECH |
| 8 | `_MroContinue` + `__repr__` (:47) | F-SENTINEL |
| 9 | `MRO_CONTINUE` (:62) | F-SENTINEL |
| 10 | `convert_with_mro` (:65) | F-DISPATCH + FAM-MRO converge |
| 11 | `make_kind_converter` + `_convert` (:133) | F-VALUE |
| 12 | `make_scalar_converter` (:155) | F-VALUE |
| 13 | `finish_field_conversion` (:175) | F-FINISH |

### Challenges

Each change posited with the definition count at
HEAD bytes. Consumers / oracles / projections that
also move are listed, never counted.

| ID | Change posited | Count | Home |
|---|---|---|---|
| C1 | A fourth riding flavor (new field population) | 0 here (caller supplies its 3 args; skeleton untouched) | F-DISPATCH |
| C2 | Walk-mechanics change (e.g. exact-type-only firing) | 1 (`convert_with_mro` walk leg) | F-DISPATCH |
| C3 | Fallthrough-posture change (raise -> default) | 0 here (factories are per-caller definitions) | F-DISPATCH split proof |
| C4 | `(annotation, kind, required)` construction change | 1 (`make_kind_converter._convert`) | F-VALUE |
| C5 | A third requiredness flavor | 0 here (`required_of` seam absorbs it) | F-VALUE split proof |
| C6 | Continue-signal change (sentinel identity / `None` verdict) | 1 (sentinel + the `is not` arm, one rule) | F-SENTINEL |
| C7 | Pure key-lookup firing-rule change | 3, all outside (`scalar_for_field`, `_field_output_type_for`, `_matched_scalar_key`); here listed-not-counted | FAM-MRO converge |
| C8 | Unify all converter tables into one map | Refused (disjoint key spaces + disjoint value contracts) | R1 |

C7 is the open-family probe the dispatch brief
ordered: on fresh evidence the walk leg inside
`convert_with_mro` stays listed-not-counted (see
FAM-MRO below), so the family count does not move.

## Findings

### FL1 -- F-DISPATCH: the dispatch skeleton (file-local)

- **Contract + variation.** `convert_with_mro`
  dispatches a field instance through ordered
  `isinstance` prechecks (first match wins;
  `MRO_CONTINUE` continues; `None` is a value),
  then a most-specific-first MRO walk over a
  caller-supplied registry (interpreter-read MRO,
  snapshot copy, identity scan), then a raising
  fallthrough via a caller-supplied factory. No
  base-class catch-all exists at any layer.
  Varies as the control flow only; populations,
  registries, and wordings are caller arguments.
- **Sites + roles.** *Definition*: this function
  (one body). *Consumers*: the four riding call
  sites (form convert, serializer convert, filter
  convert, filter normalize -- each supplies its
  own prechecks + registry + factory). *Oracles*:
  the 12 skeleton tests (order, continue, `None`,
  most-specific, unregistered-subclass, raise,
  four hostile-MRO rows -- attribute-access,
  hashing, mro-property, fake-MRO -- snapshot
  row) plus the flavor MRO/subclass rows and the
  import-identity ratchet
  (`tests/rest_framework/test_dry_import_ratchet.py`).
  *Projections*: the three riders'
  docstrings + spec-039 D4/D7 + spec-053 C3.
- **Challenges.** C1 counts 0 here (filter riders
  arrived as pure callers); C2 counts 1; C3
  counts 0 here (the per-caller factories move).
- **Owner + lifetime.** This module (the
  flavor-agnostic mechanics live nowhere else;
  every rider imports them by name). Pure
  dispatch; nothing stored (the per-call
  registry snapshot is garbage after return).
- **Migration.** None (no consolidation in a
  file item).
- **Distinct behavior.** The per-caller
  fallthrough wordings stay per subject (the
  standing per-subject direction, re-checked:
  three factories, three messages, one shared
  raising posture).
- **Behavioral proof.** `static-reviewed` (body
  + all four riders + oracles read at HEAD
  bytes; the CLEAN oracle suite pins every arm
  with independent literals).
- **Freshness.** Target `5332f054…` (work
  `3f5e6e18…`); riders `37f3ff39…`,
  `6652d092…`, `82b52d97…`; oracles
  `447fa2c5…` (CLEAN), `595e0f39…` (CLEAN).

### FL2 -- F-SENTINEL: the continue protocol (file-local)

- **Contract + variation.** `MRO_CONTINUE` is
  the identity-compared continue signal: a
  precheck returning it keeps walking; `None` is
  a successful conversion. `_MroContinue.__repr__`
  renders the stable `MRO_CONTINUE` token.
  Varies as the signal only.
- **Sites + roles.** *Definition*: the class +
  the singleton (one rule). *Consumers*: the
  skeleton's `is not` arm, the bare-`forms.Field`
  precheck, filter normalize's convert-only skip.
  *Oracles*: the continue test (incl. the `repr`
  pin) + the `None`-is-a-value test.
- **Challenges.** C6 counts 1.
- **Owner + lifetime.** This module (the signal
  exists only for this skeleton's arm). Immutable
  singleton; no lifetime.
- **Behavioral proof.** `static-reviewed`.
- **Freshness.** Target `5332f054…`; oracles
  `447fa2c5…` (CLEAN).

### FL3 -- F-VALUE: the shared value-shape factory (file-local)

- **Contract + variation.** `make_kind_converter`
  builds the `field -> conversion` closures both
  write registries store (fixed kind + optional
  annotation + requiredness); `make_scalar_converter`
  pins kind to `SCALAR` with a required
  annotation. `required_of` is the genuine
  requiredness variation (omitted: `field.required`
  for serializers; `form_field_required` for the
  form NullBoolean arm). Key spaces stay separate;
  only the VALUE shape is shared.
- **Sites + roles.** *Definition*: the two
  factories (one body -- scalar delegates to
  kind). *Consumers*: both flavor table builders
  + both flavor kind prechecks. *Oracles*: the
  five value-shape tests (3 `make_*` + the two
  `__code__`-identity pins across flavors).
- **Challenges.** C4 counts 1; C5 counts 0
  here (a third flavor passes a third
  `required_of`).
- **Owner + lifetime.** This module (the
  closure shape; the `(annotation, kind,
  required)` record itself stays owned by
  `utils/inputs.py::FieldConversionBase`,
  composed -- not restated -- here).
- **Behavioral proof.** `static-reviewed`.
- **Freshness.** Target `5332f054…`; shape
  owner `ee31d360…`; oracles `447fa2c5…`
  (CLEAN).

### FL4 -- F-FINISH: the post-walk invoke split (file-local)

- **Contract + variation.** `finish_field_conversion`
  returns a `FieldConversionBase` instance as-is
  and invokes anything else with `field`
  (precheck hits are finished; registry hits are
  callables that still need `field`). Lets the
  skeleton stay value-agnostic. Varies as the
  split only.
- **Sites + roles.** *Definition*: this
  function. *Consumers*: both write converters
  (the serializer wraps it in
  `_finish_serializer_conversion`, which adds
  the consumer-converter return-gate -- verified
  in the serializer artifact). *Oracle*: the
  instance/callable split test (incl. the
  non-callable-registry-value posture).
- **Challenges.** Changing the split counts 1.
- **Owner + lifetime.** This module. Pure
  function; nothing stored.
- **Behavioral proof.** `static-reviewed`.
- **Freshness.** Target `5332f054…`; oracles
  `447fa2c5…` (CLEAN).

### FL5 -- F-MECH: module mechanics (file-local)

- **Contract + variation.** The module
  docstring states the skeleton ownership, the
  per-caller arguments, the key-space
  separation, and the import boundary
  (neither `django.forms` nor `rest_framework`
  is imported here); `__all__` admits exactly
  the 5 public names; the import block binds
  only annotation substrate + the
  `utils/inputs.py` shape. All 7 docstring
  claims re-verified against the bodies:
  precheck-first ordering (both write riders +
  filter table), empty filter registries (both
  riders pass `scalar_registry={}` at HEAD and
  worktree), `ConfigurationError` from all
  three factories, `None`-is-a-value (filter
  normalize arm), the bare-`Field` sentinel
  pattern (form precheck), the exact-dict
  snapshot (all three production registries
  are exact dicts: two literals + one
  `dict(builtin)` build), the import boundary
  (both states import neither flavor
  package).
- **Sites + roles.** *Definition*: docstring +
  imports + `__all__` (one mechanics rule).
  *Oracles*: the ratchet (import identity) +
  the `__code__` pins.
- **Challenges.** Adding a public name or an
  import counts 1.
- **Owner + lifetime.** This module.
- **Behavioral proof.** `static-reviewed`.
- **Freshness.** Target `5332f054…` (work
  `3f5e6e18…`); `utils/inputs.py`
  `ee31d360…`; ratchet
  (`tests/rest_framework/test_dry_import_ratchet.py`)
  `595e0f39…` (CLEAN).

### FAM-MRO -- `mro-map-key-lookup` (CONVERGE, no count change)

The dispatch brief ordered converge, adopt, or
distinguish on fresh evidence. Verdict: CONVERGE
with the standing FAM-MRO verdict -- the walk leg
inside `convert_with_mro` stays the listed-not-counted
hardened sibling, and the dispatch rule stays
distinct from the family rule. No plan-row change:
members, owner candidacy, and the blocked-on-hunt
coupling all stand.

- **Contract difference (fresh).** The family
  rule is a pure lookup: the first class in
  `type(field).__mro__` keying a class map (or
  absence). The skeleton's walk is phase 2 of a
  preemptible dispatch: ordered prechecks can
  shadow any registry hit (only `MRO_CONTINUE`
  declines), the registry is caller-supplied per
  call, and a miss raises through a caller
  factory rather than reporting absence. C7
  (pure firing-rule change) moves the 3 family
  legs; this walk moves only if the lookup
  mechanics themselves change -- and hosting a
  shared `_mro_key_for` helper here would be a
  family-item ownership decision about
  mechanics, not a fourth definition of the
  lookup rule.
- **Fresh posture evidence.** At HEAD bytes
  this walk already embodies the hardened
  posture the family converges toward
  (interpreter-read MRO + snapshot + identity
  scan, pinned by four hostile oracles); the
  three family legs at HEAD use the plain
  `type(field).__mro__` + `in` spelling. The
  worktree hunt dirt (`_class_map_lookup` at
  worktree `f6cadb08…`) converges the two
  same-file legs TOWARD this posture without
  extracting a shared helper -- consistent with
  listed-not-counted, and the family item still
  owes the reconciliation behind its
  blocked-on-hunt coupling.
- **Trigger re-check.** The standing trigger
  (the family item choosing this module as the
  shared-helper host) is unfired: no such
  helper exists here at either state, and the
  family item is undispatched.
- **Freshness.** Target `5332f054…` (work
  `3f5e6e18…`); `types/converters.py`
  `058f1081…` (work `f6cadb08…`);
  `inspect_django_type.py` `2807d0fc…`.

### R1 -- skeleton vs read-side dispatch (rejected)

This skeleton (flavor registries over
`forms.Field` / `serializers.Field` / empty,
prechecks-first, value-shape + invoke split)
vs `types/converters.py::scalar_for_field` +
the output-map walk (`models.Field` keys,
shared read-output + filter-input contract,
choice substitution + null widening layered
by callers, last-write-wins hook). Contract
differences: disjoint key roots (fresh census:
26 `models.Field` / 12 `forms.Field` / 16
`serializers.Field` keys, pairwise disjoint)
with disjoint value contracts; what should be
shared (nothing -- the read side answers a
different question) already is. CONVERGE with
the verified converter-table direction
(forms F-reuse + serializer R-TABLES) on
fresh evidence, never inherited. Trigger: a
surface whose population is a SUBSET of an
existing table's key space with an identical
value contract. Freshness: target
`5332f054…`, read side `058f1081…`.

### R2 -- skeleton vs mutations model-input triple (rejected)

The fail-loud multi-kind dispatch vs
`mutations/inputs.py` model-field shaping (a
total 3-arm classifier -- relation probes,
one file `isinstance` probe, `SCALAR` default
-- plus the `<field>_id` / `list[id]` /
`Upload` annotation triple). No registry
walk exists there (census: zero `__mro__`;
`registry` matches 11 lines, all naming the
DjangoType `registry` object (`registry.get` /
`registry.clear()`), none a converter walk;
the one `isinstance` is a kind probe, not
ordered dispatch). Contract difference: partial
dispatch with a raising miss vs total
classification with a default. Fresh pair, no
prior verdict. Trigger: a model-input kind
needing registry dispatch. Freshness: target
`5332f054…`, mutations `inputs.py` as read
(worktree; body cited).

### R3 -- skeleton vs orders leaf converter (rejected)

The multi-kind dispatch vs
`orders/inputs.py::convert_order_field_to_input_annotation`
(a single-kind leaf mapping to the `Ordering`
enum). Contract difference: one-kind output
with no registry, no prechecks, no
fallthrough vs multi-kind dispatch. Fresh
pair, no prior verdict. Trigger: orders
gaining multi-kind dispatch. Freshness:
target `5332f054…`.

### R4 -- skeleton vs `functools.singledispatch` (rejected)

The refused shape, recorded deliberately:
both write-converter docstrings state the
dispatch is NOT `singledispatch` with a base
`Field -> str` catch-all (spec-038 Decision
7), because registration would shadow the
raise. Contract difference: explicit ordered
prechecks + factory raise (no registration
API exists here) vs decorator registration
with an inheritable default. Durable home:
the riders' docstrings + this row. Trigger: a
registration shape that preserves the raising
fallthrough. Freshness: target `5332f054…`.

### R5 -- kind-table ownership stays in filters (rejected)

The skeleton owns walk ORDER mechanics; the
filter kind table (`_FILTER_INPUT_KIND_TYPES`
+ `_filter_input_prechecks`, incl. the
convert-only `TypedFilter` arm and the
`object` catch-all) stays owned by
`filters/inputs.py`. Same shape as the
key-space separation: one shared walk, N
owned tables. Moving the filter table here
would merge a filter population into
flavor-agnostic mechanics. Trigger: a second
kind table needing the identical order (then
the TABLE moves to a shared owner; the
skeleton still does not change). Freshness:
target `5332f054…`, filters `82b52d97…`.

### R6 -- other MRO scans + standing guard triggers (rejected)

The five remaining package MRO scans each
ask a different question, verified at the
body: `finalizer.py` inherits surface field
collection (reversed-MRO declaration scan);
`sets_mixins.py` inherited declaration
collection; `relay.py` already-in-MRO
interface skip; `definition.py` id-resolver
override detection; `querysets.py` shadow-
defect namespace walk. None keys a class map
for conversion. CONVERGE with the verified
R14 direction (three questions, three MROs)
on fresh evidence; R14's own trigger ("one
owned MRO-walk helper") re-checked unfired
(no shared helper at either state:
`_class_map_lookup` is same-file, `truth.mro`
is a read, not a walk). Standing triggers
re-checked unfired: J1 (zero `try/except`
arms here -- nothing to share with a guard
driver) and J2 (the one `type(field)` read
seeds the walk; no exact-type gate lives
here). Freshness: target `5332f054…`.

## Defects

None at HEAD bytes. The sweep verified all 7
module-docstring claims against the riding
bodies (FL5), the exact-dict snapshot claim
against all three production registry builds
(literals + `dict(builtin)`), and the
fallthrough wordings against the three
factories. No authorization / routing /
exposure surface is touched by this module,
so no security routing arises. The worktree
`truth.mro` retargeting is hunt-owned
concurrent dirt (see hunk attribution), not
a defect in either state.

## Judgment

Zero-edit file item, ready for verification.
All 13 `ast.Module.body` members homed (12
HEAD members to 5 file-local findings +
1 family convergence + 6 rejections; the
worktree-only import to the hunk
attribution): 5 file-local, 0 new families,
1 convergence onto open `mro-map-key-lookup`
(count unchanged), 6 rejected, 0 defects.
The open-family alternative converges on
fresh evidence: the walk leg stays the
listed-not-counted hardened sibling, and the
dispatch rule is contract-distinct from the
pure key lookup.

## Index rows for Worker-0

Pipe-table rows to transcribe verbatim (11
new rows; the family convergence needs no
plan change and carries no row):

- `| converters-dispatch-skeleton | django_strawberry_framework/utils/converters.py::convert_with_mro | django_strawberry_framework/utils/converters.py | File utils/converters.py | file-local |`
- `| converters-continue-protocol | django_strawberry_framework/utils/converters.py::MRO_CONTINUE | django_strawberry_framework/utils/converters.py | File utils/converters.py | file-local |`
- `| converters-value-shape-factory | django_strawberry_framework/utils/converters.py::make_kind_converter | django_strawberry_framework/utils/converters.py | File utils/converters.py | file-local |`
- `| converters-post-walk-invoke-split | django_strawberry_framework/utils/converters.py::finish_field_conversion | django_strawberry_framework/utils/converters.py | File utils/converters.py | file-local |`
- `| converters-module-mechanics | django_strawberry_framework/utils/converters.py | django_strawberry_framework/utils/converters.py | File utils/converters.py | file-local |`
- `| converters-skeleton-vs-read-dispatch | django_strawberry_framework/utils/converters.py::convert_with_mro (rejection recorded here; CONVERGE with verified converter-table direction on fresh evidence) | django_strawberry_framework/utils/converters.py, django_strawberry_framework/types/converters.py | File utils/converters.py | rejected |`
- `| converters-skeleton-vs-mutations-triple | django_strawberry_framework/utils/converters.py::convert_with_mro (rejection recorded here; fresh pair, no prior verdict) | django_strawberry_framework/utils/converters.py, django_strawberry_framework/mutations/inputs.py | File utils/converters.py | rejected |`
- `| converters-skeleton-vs-orders-leaf | django_strawberry_framework/utils/converters.py::convert_with_mro (rejection recorded here; fresh pair, no prior verdict) | django_strawberry_framework/utils/converters.py, django_strawberry_framework/orders/inputs.py | File utils/converters.py | rejected |`
- `| converters-skeleton-vs-singledispatch | django_strawberry_framework/utils/converters.py::convert_with_mro (rejection recorded here; refused shape, durable home the riders docstrings) | django_strawberry_framework/utils/converters.py, django_strawberry_framework/forms/converter.py, django_strawberry_framework/rest_framework/serializer_converter.py | File utils/converters.py | rejected |`
- `| converters-kind-table-stays-in-filters | django_strawberry_framework/utils/converters.py::convert_with_mro (rejection recorded here; intentional separation, table owned by filters/inputs.py) | django_strawberry_framework/utils/converters.py, django_strawberry_framework/filters/inputs.py | File utils/converters.py | rejected |`
- `| converters-mro-scans-vs-dispatch-walk | django_strawberry_framework/utils/converters.py::convert_with_mro (rejection recorded here; CONVERGE with verified R14 on fresh evidence; J1/J2 triggers re-checked unfired) | django_strawberry_framework/utils/converters.py, django_strawberry_framework/types/finalizer.py, django_strawberry_framework/sets_mixins.py, django_strawberry_framework/types/relay.py, django_strawberry_framework/types/definition.py, django_strawberry_framework/utils/querysets.py | File utils/converters.py | rejected |`

## Independent verification (Worker-2)

Expectation-first trace, formed from HEAD
bytes (`5332f054`), the worktree state
(`3f5e6e18`), and the riding bodies BEFORE
reading `## Findings`:

- Instrument `ast.Module.body` on HEAD
  bytes: 12 members (docstring; 4
  imports; `__all__` with 5 names;
  `_MroContinue`; `MRO_CONTINUE`;
  `convert_with_mro`,
  `make_kind_converter`,
  `make_scalar_converter`,
  `finish_field_conversion`). Worktree
  adds exactly 1 member (the `truth`
  import) = 13. Expectation: every
  rule here single-owned (skeleton,
  sentinel, value shape, invoke
  split, mechanics); four riders
  compose by name (form convert,
  serializer convert, filter convert
  + normalize); read-side dispatch
  sits on disjoint `models.Field`
  keys.
- Hunk expectation: 3 hunks, all one
  migration (import + docstring +
  body/comment) re-pointing the MRO
  read at `truth.mro`.
  `utils/truth.py` is untracked
  (`??`) and absent at HEAD, and the
  plan records the truth-migration
  as hunt-owned concurrent work, so
  the expected attribution is
  hunt-owned concurrent dirt, traced
  at HEAD bytes.
- FAM-MRO expectation: the plan row
  leaves a `utils/converters.py`
  alternative open; the walk leg is
  the same-mechanism hardened
  sibling, so the expected verdict
  is CONVERGE listed-not-counted
  with the family count unchanged.
- Rejection expectations: read-side
  dispatch (disjoint key roots),
  mutations triple (total
  classifier, no walk), orders leaf
  (single-kind), `singledispatch`
  (refused shape), filter kind
  table (stays in filters), the
  five other MRO scans (distinct
  questions), J1/J2 unfired (no
  `try/except`; one `type(field)`
  seed, no exact-type gate).

Reconciliation against the five
required judgments (every check
re-derived fresh, HEAD bytes unless
named):

1. Enumeration: STANDS. 12 HEAD
   members + 1 worktree-only dirt
   import, all homed; nested defs
   home with parents. My count
   matches member for member.
2. Hunk attribution: STANDS. All 3
   hunks are the one `truth.mro`
   migration; `truth.mro`
   (`_get_mro`, same
   `type.__dict__["__mro__"]` slot,
   `is_type` true for
   `type(field)`) is semantically
   identical to the HEAD spelling,
   and the snapshot + identity
   scan are byte-identical, so the
   `static-reviewed` equivalence
   holds. Hunt-owned concurrent:
   `truth.py` untracked, absent
   at HEAD, absent from the
   ledger and cycle baseline,
   matching the plan's recorded
   truth-migration dirt.
3. FAM-MRO convergence: STANDS.
   The three legs at HEAD use the
   plain `type(field).__mro__` +
   `in` spelling
   (`scalar_for_field`,
   `_field_output_type_for`,
   `_matched_scalar_key`);
   worktree `_class_map_lookup`
   converges the two same-file
   legs toward the hardened
   posture with no shared helper
   extracted. Count unchanged,
   transcribes nothing; plan row
   and blocked-on-hunt coupling
   stand.
4. Rejections: all 6 STAND on
   fresh evidence. R1: census
   re-derived exact (26 / 12 /
   16 keys, disjoint roots) and
   the F-reuse + R-TABLES
   direction confirmed in both
   verified artifacts. R2: zero
   `__mro__`, one `isinstance`
   kind probe; total classifier
   vs raising partial dispatch.
   R3: orders leaf returns
   `Ordering | None` for every
   column. R4: both riders'
   docstrings state NOT
   `singledispatch`. R5: kind
   table owned by
   `filters/inputs.py` at HEAD.
   R6: all five scans re-read at
   the body, each a distinct
   question, none keying a
   conversion map; verified R14
   (`types/base.py`, three
   questions, three MROs) and
   R11 both real with matching
   direction; J1 (zero
   `try/except`) and J2 (one
   `type(field)` seed, no gate)
   re-checked unfired. The
   axis-2 instrument reproduces
   exactly (only the
   `scalar_registry` line, both
   states); both filter riders
   pass `scalar_registry={}` at
   HEAD (:536, :625).
5. Zero-defect call: STANDS. All
   cited fingerprints reproduce
   (target pair, three riders,
   `utils/inputs.py`
   `ee31d360…`, both FAM-MRO
   legs incl. worktree
   `f6cadb08…`, oracle
   `447fa2c5…` CLEAN, ratchet
   `595e0f39…` CLEAN);
   `ITEM_BASELINE` diff on this
   path is empty; no ledger row
   names this file; no
   authorization / routing /
   exposure surface. The 12
   skeleton-test count and the
   four hostile-oracle count
   check out against the CLEAN
   oracle file.

Revision feedback (record
accuracy only; no judgment
moves, no re-trace needed).
Five false record claims to
fix in-artifact:

- D1 (Worker-2): the ratchet
  path `tests/test_dry_import_ratchet.py`
  (3 occurrences: System trace,
  FL1, FL5) names a file that
  does not exist. Real path:
  `tests/rest_framework/test_dry_import_ratchet.py`.
  Fingerprint `595e0f39…` and
  CLEAN are correct as cited.
- D2 (Worker-2): R2 census
  "zero `__mro__` / registry
  tokens" is half false:
  `__mro__` is zero, but
  "registry" matches 11 lines,
  all naming the DjangoType
  `registry` object
  (`registry.get` /
  `registry.clear()`), none a
  converter walk. Reword the
  instrument; the contract
  difference stands.
- D3 (Worker-2): "19-test
  skeleton suite" (Matrix axis
  5) is 18: 12 skeleton + 3
  `make_*` + 1 finish + 2
  `__code__` pins, counted at
  the CLEAN oracle file.
- D4 (Worker-2): FL1 "three
  hostile-MRO rows" is four
  (attribute-access, hashing,
  mro-property, fake-MRO),
  consistent with FAM-MRO's
  "four hostile oracles" in
  this same artifact.
- D5 (Worker-2): FL3 "four
  value-shape tests incl. the
  two `__code__`-identity pins"
  is five (3 `make_*` + 2
  pins).

One strengthening line for R6:
state R14's own trigger ("one
owned MRO-walk helper")
re-checked unfired (no shared
helper at either state;
`_class_map_lookup` is
same-file, `truth.mro` is a
read, not a walk).

Resubmission: SAME W1 context
(no re-trace, no production
edits, no plan edits); return
to this SAME Worker-2. Verdict
after fixes: `verified`
(zero-edit; 5 file-local, 1
convergence, 6 rejections, 0
defects; 11 index rows stand
as written).

Freshness at verification:
HEAD `0c0537e2` unmoved from
dispatch; target pair
`5332f054…` / `3f5e6e18…`
reconfirmed; W1 touched no
tracked path, so no ruff gate
is owed (nothing to run it
on).

## Iterations (pass 2)

Pass 2 applied the five
record-accuracy fixes plus
the R6 strengthening line,
each literal re-verified
fresh against the tree (no
re-trace, no judgment moves):
D1 ratchet path to
`tests/rest_framework/test_dry_import_ratchet.py`
at all three citation sites
(System trace, FL1, FL5);
D2 R2 instrument to zero
`__mro__` + 11 `registry`
lines all naming the
DjangoType registry object;
D3 suite count 19 to 18
(12 + 3 + 1 + 2); D4 FL1
hostile rows three to four
(attribute-access, hashing,
mro-property, fake-MRO);
D5 FL3 value-shape tests
four to five (3 `make_*` +
2 pins); R6 carries R14's
own trigger re-checked
unfired. Set `Status:
ready-for-verification/2`.

## Independent verification
(Worker-2, re-pass)

Same Worker-2 context. Each
D-item re-verified
mechanically against the
tree: D1 real ratchet path
at all 3 citation sites
(blob `595e0f39…` CLEAN,
unchanged); D2 R2
instrument reads zero
`__mro__` + 11 DjangoType-
`registry` lines; D3
18-test suite with the
(12 + 3 + 1 + 2) split;
D4 four hostile-MRO rows
named; D5 five value-shape
tests (3 + 2); R6 carries
R14's own trigger
re-checked unfired. No
other passage moved;
substance untouched. Target
diff vs `ITEM_BASELINE`
still empty; HEAD
`0c0537e2` unmoved. Verdict:
`verified` (zero-edit; 5
file-local, 1 convergence,
6 rejections, 0 defects).

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
