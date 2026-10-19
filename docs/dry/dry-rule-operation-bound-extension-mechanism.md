# DRY review: `operation-bound-extension-mechanism`

Status: verified
Run: 0.0.15 2026-10-01-12

## System trace

Owner re-derived, not inherited:
`django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
(`operation_state.py:483-595`; base refusal `:497-501`, carrier `__init__`
`:503-517`, `execution_context` property + setter `:519-571`, factory
default `:573-576`, `_operation_state` reader `:578-595`) with the
runner-side selection + binding (`_operation_states` `:598-619`,
`_bind`/`_unbind` `:642-726`, `DjangoExtensionsRunner` `:886-979`) and
the resume registry (`OperationState.rebind_on_resume` `:185-219`,
`resumed_bindings` `:221-223`) in the same module. The rule, re-derived
fresh at WT bytes: one state object per (resolved extension, runner),
reachable only through a task-local carrier while that runner owns it;
a consumer composes it by subclassing the base, declaring the refusal
wording (or inheriting the base string), and building its state type
(or inheriting the base state).

Per-consumer composition, re-censused at WT bytes (all composing lines
byte-identical HEAD vs WT — the hunt hunks touch predicates, guards,
and prose, never a composition line):

| consumer | subclass | refusal | `__init__` | factory | state | config |
|---|---|---|---|---|---|---|
| debug (`:607`) | own | own `:686` | own `:692` (`super` `:712` + bool gate + settle) | own `:725` | `_DebugOperationState` `:565` | `_ACKNOWLEDGEMENT` `:604` |
| error (`:357` in `error_policy.py`) | own | inherits | inherits | inherits | base `OperationState` | none (reads `schema.error_policy` per op) |
| resource (`:1438` in `resource_policy.py`) | own | own `:1482` | own `:1488` (`super` `:1499` + settle) | inherits | base `OperationState` | `_EXPLICIT_POLICY` (`:1422`) |
| optimizer (`:935` in `optimizer/extension.py`) | own | own `:971` | own `:978` (`super` `:992` + compat assign + strictness gate + settle + cache) | own `:1026` | `_OptimizerOperationState` (`:892`) | `_OPTIMIZER_CONFIGURATION` (`:932`) |

Whole-package sweep for the mechanism (fresh; instrument + counts
under `### Enumeration`) finds NO sixth member: production
`SchemaExtension` subclasses are exactly the base, the four consumers
above, and three examined-and-excluded non-bound extensions —
`_OperationModeMarker` (`operation_state.py:344`, construction-fixed
mode fact, no mutable per-operation state), `_AdmissionGuard`
(`resource_policy.py:1707`, stateless verdict restater), and
`_RefusedConfiguration` (`schema.py:653`, built fresh per operation in
`_refused_chain` `:750`, fixed message only). Test doubles compose by
the same rule on the oracle side: `tests/extensions/test_operation_state.py`
`_Probe` (`:77`, `super` `:81`), `_SilentProbe` (`:96`), `_Unbuilt`
(`:112`), `_RefusingState` (`:670`, factory `:673`); live-tier doubles
are plain consumer-shape witnesses (`SchemaExtension`, no per-operation
state of their own).

Key censuses (WT bytes, `rg` over the package):

- `super().__init__()` composing calls: 3 extension inits
  (`debug.py:712`, `resource_policy.py:1499`,
  `optimizer/extension.py:992`) + 2 state inits (`debug.py:584`,
  `optimizer/extension.py:905`); error policy has no `__init__` at all.
- `_reconstruction_refusal`: 4 declarations (base `:497` + 3
  overrides), 1 read (`self._reconstruction_refusal`, base `:513`).
- `_new_operation_state`: base default (`:573`) + 2 one-line overrides;
  2 call sites (compat setter `:570`, runner selection `:618`).
- `rebind_on_resume`: 1 definition (`:185`), 1 call
  (`resource_policy.py:1591`); `resumed_bindings` read once
  (`_bind`, `:675`).
- `operation_is_nested`: 1 production caller
  (`optimizer/extension.py:1126`).
- `_operation_state()` readers: base getter (`:531`) + debug x3
  (`:790`, `:857`, `:894`) + optimizer (`:1114`) + resource (`:1590`).
- `PrivateAuthority` stores: mechanism 2 (`_OPERATION_CARRIERS` `:283`,
  `_PACKAGE_MANAGED` `:302`) + config 3 (one per stateful consumer).

Dirt attribution (by diff content vs `git show HEAD:<path>`): all WT
hunks in the five files (`167+/208-`) are external hunt work (truth
migration, guard narrowing, prose) — none matches a `## Owned changes`
ledger row (the ledger's one row on these paths, the adopted
error-policy three-sites rationale, already sits at HEAD
`error_policy.py:16/:41/:454`). WT == `ITEM_BASELINE` on all five
files: zero movement since dispatch. Touched nothing.

Oracles re-read: `tests/extensions/test_operation_state.py` (seam rows;
one focused `--no-cov` run, 55/55 green — see `## Implementation`)
plus the live shared-entry matrices
(`test_extension_isolation_api.py`, `test_resource_policy_api.py`,
`test_error_policy_api.py`).

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. The four consumers ARE
   four flavors (debug / error / resource / optimizer), each read in
   full. Each composes the base by subclassing; each keeps its
   configuration in its own authority with its own payload and read
   posture (acknowledgement bool, accepted policy, strictness +
   strategy; error policy reads per operation and keeps none). The
   per-flavor config split converges with the verified
   `policy-authority-isolation` / per-subject directions — same
   vocabulary, distinct payloads (R5). No second mechanism.
2. Sync/async twins — SEARCHED. `_BoundScope` runs both protocols over
   ONE binding primitive (`_bind`/`_unbind`; async methods differ only
   in how they enter/exit the wrapped scope); sync/async result
   collection share `_bound`; `_ResumedStream`'s four drives all wrap
   `resumed()`. Compared by behavior (same scope + states bound in
   each): one body with adapters, already the principle-5 answer.
3. Derived rather than repeated knowledge — SEARCHED. Refusal strings
   are declarations, never derivations (R3). The two type predicates
   are intentionally different contracts: `_declared_operation_mode`
   reads the EXACT marker type (a consumer attribute named `mode`
   declares nothing) while `_is_operation_bound` accepts SUBCLASSES
   (extension kinds vary by subclassing) — R7. No duplicated fact.
4. Inverse / round-trip pairs — SEARCHED. `_bind`/`_unbind` (unwind on
   partial failure included), settle/recall (carrier + managed +
   config), arm/disarm (budget), bind/resumed-bind (adopted-token
   tolerance). Each pair lives once, in the module that owns its
   half; no second half anywhere in the sweep.
5. Contracts restated in another medium — SEARCHED. Production (base +
   runner), oracles (55 seam rows + 3 live matrices), projections
   (module docstring owning the whole contract, base/consumer
   docstrings, hook prose). A mechanism change moves the base plus
   its oracles plus its docstring — listed under F1, never counted.
   No restatement graduated to a definition.
6. Enforcement by omission — SEARCHED. Family enumerated: all 7
   production `SchemaExtension` subclasses (4 bound + marker + guard
   + refused, each exclusion carrying its contract difference — R6).
   No member lacks a guard the contract requires: the three
   non-bound extensions keep no per-operation mutable state (fixed
   fact / stateless / fresh-per-operation), established from their
   bodies, not from sibling behavior. No defect, no gap.

### Enumeration

Instrument: `rg` (literal + regex) over `django_strawberry_framework/`
for `SchemaExtension` subclasses, `_OperationBoundExtension` namers,
`_new_operation_state` / `_reconstruction_refusal` /
`rebind_on_resume` / `operation_is_nested` / `_operation_state()` /
`super().__init__()` sites, plus first-party import edges; doubles
swept in `tests/` + `examples/`. Population: 7 production
`SchemaExtension` subclasses, 4 bound-subclass declarations, 2 state
subclasses, 3 extension `__init__`s, 3 factory spellings, 4 refusal
declarations, 1 resume-registration call, 1 nestedness caller, 6
`_operation_state()` readers, 5 authority stores, 4 package-test
doubles. Every member homes below; nothing unassigned.

| # | Member | Home |
|---|---|---|
| 1 | base `_OperationBoundExtension` + carrier/managed/selection/compat/factory-default | F1 owner |
| 2 | `OperationState` + resume registry | F1 owner |
| 3 | `DjangoExtensionsRunner` + `_bind`/`_unbind`/`_BoundScope`/`_ResumedStream` | F1 owner |
| 4-7 | 4 subclass declarations (debug / error / resource / optimizer) | F1 consumers |
| 8-9 | 2 state subclasses + 2 factory overrides | F1 consumers / R1 + R4 |
| 10-12 | 3 `__init__` settle bodies | F1 consumers / R2 |
| 13-15 | 3 refusal overrides (+ base string, F1) | F1 consumers / R3 |
| 16-18 | 3 config authorities | F1 consumers / R5 |
| 19-21 | marker / guard / refused-configuration | R6 exclusions |
| 22 | exact-type vs subclass predicate split | R7 exclusion |
| 23 | 4 package-test doubles + live-tier witnesses | oracle scaffolding |

### Challenges

Each change posited against the rule's own variation axes; the count
is authoritative definitions only. Consumers, oracles, projections
listed, never counted. (The nominating re-trace counted refusal /
resume-registration / membership at 0-here / 1-at-owner per consumer;
C2 / C6 / C1 below re-derive those three fresh — same counts.)

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | membership | a fifth operation-bound extension kind | **1** (the new subclass declaration — refusal + state choice; base + runner discover it) | F1 |
| C2 | base refusal | reword the base reconstruction refusal | **1** (the base string; all 3 overrides stand — proves override-not-copy) | F1 |
| C3 | consumer refusal | reword one consumer's refusal | **1** (that consumer; base + siblings stand) | F1 / R3 |
| C4 | binding mechanics | change lease terms, bind order, or unwind | **1** (the base module — `_bind`/`_unbind`/scope; every consumer follows) | F1 |
| C5 | compat branch | accept or ignore a new assignment shape | **1** (setter + `_binds_operation_state`, same owner; managed extensions untouched) | F1 |
| C6 | resume registration | a second whole-operation value registers, or the handoff shape changes | **1** (the state registry; the single caller follows by name — a use, not a second registry) | F1 |
| C7 | state scratch | add a slot to one state | **1** (that state subclass; base + sibling states stand) | F1 / R4 |
| C8 | factory behavior | validate or transform inside construction | **0** existing (no validation exists anywhere — greenfield; the 3 signature spellings restate by language design, as every hook override must) | R1 |

No experiment mutates source (zero-edit item): every count above is
`static-reviewed` over bodies read at WT bytes, corroborated by the
executed 55/55 oracle run in `## Implementation`, which rejects "a
composition line drifted" and "the rule does not currently hold".

## Findings

### F1 — operation-bound extension mechanism (CONFIRMED single-owned, zero-edit)

- **Contract + variation.** One state object per (resolved extension,
  runner), reachable only through a task-local carrier while that
  runner owns it. Configuration stays with authorities; per-operation
  mutable state sits on the state the runner builds. The engine's
  assignment records nothing for a `DjangoSchema` (compatibility glue
  for raw schemas only); a package-managed extension ignores every
  later assignment of every shape. The carrier settles once at
  construction (a second `__init__` is refused with an overridable
  message); a subclass whose `__init__` never ran the base is refused
  at first read. Legitimate variation, both declarations: the
  per-extension scratch shape (the subclass's state) and the refusal
  wording (the subclass's string).
- **Sites + roles.** *Definitions* (all in `operation_state.py`,
  unchanged): carrier mint + recall-or-refuse (`_carrier`),
  lease-on-weakref read (`_bound_state`), managed mark + compat drop
  (`_mark_package_managed`), compat predicate
  (`_binds_operation_state`), selection (`_operation_states`),
  refusal point (`_reconstruction_refusal`), factory default,
  compat setter, resume registry, runner scopes. *Consumers*: the
  four subclasses (compose by name — subclass + refusal + state
  choice + `super().__init__()` where they define `__init__`);
  `schema.py::DjangoSchema.create_extensions_runner` (builds the
  runner by name). *Oracles*: 55 seam rows in
  `tests/extensions/test_operation_state.py` (assignment-records-
  nothing, runner-builds-all-states, skipped-constructor refused,
  double-construction refused, copied-context reads nothing —
  independent: they drive the seams, never read the authorities)
  plus the three live shared-entry matrices. *Projections*: the
  module docstring (the whole contract), base/consumer docstrings,
  hook prose.
- **Challenges.** C1–C7 count 1 each at the owner or the owning
  declaration; C8 counts 0 existing (R1). Consumers, oracles,
  projections that also move: the single registration call, the six
  `_operation_state()` readers, the refusal overrides — listed,
  never counted.
- **Owner + lifetime (principle 7).** `operation_state.py`:
  narrowest cohesive owner every legitimate consumer can depend on
  without reversing a dependency — module-level first-party imports
  are leaves only (`..exceptions`, `..utils.*`; the one `..schema`
  import is deferred inside `_binds_operation_state` as the
  documented cycle-break), all four consumers import downward, and
  none imports `..schema` at module level, so hosting the base in
  `schema.py` would reverse leaf-to-assembler direction. Stored
  derivations: carriers — owner `_OPERATION_CARRIERS`, validity
  extension identity, publish construction, mutators none
  (settle-once + refusal), invalidated on owner collection; managed
  marks — same, boolean payload retaining nothing; compat state —
  instance `__dict__`, dropped at marking; operation states — owned
  strongly by the runner, read through lease-on-weakref.
- **Migration.** None — composition already by name; zero-edit item.
- **Distinct behavior.** Consumer extensions keep upstream's
  assignment (axis 6 — deliberate); raw-schema shared instances stay
  outside the guarantee (documented limitation, not a gap); error
  policy's inherit-everything shape stays as it is (no scratch, no
  config, no factory — inheriting IS the composition); R1–R7
  separations below, each with its specified owner home (unapplied —
  all five files are hunt-dirty; closeout applies).
- **Behavioral proof.** `static-reviewed` for every census, edge,
  and body claim (all composition lines byte-identical HEAD vs WT);
  `execution-verified` for "the rule currently holds" (55/55 oracle
  run). Rejects "a second carrier authority exists" (one authority
  per payload, distinct payloads), "an override copies the mechanism"
  (C2 moves the base only), and "a sixth member exists" (7-subclass
  census, 3 excluded with contract differences).
- **Structural gate.** None owed. Four bypasses judged against the
  gate-only bar (justified population, never a bespoke existence
  test per helper — f21/f48 precedent, verifier-endorsed): a fifth
  kind hand-rolling its own carrier — plausible as a mistake, but
  the population is unjustified ("keeps per-operation state" needs
  reading bodies, no syntax gates it) and a subclass-count census
  fires on legitimate variation (C1); a reader-copy of
  `_carrier`/`_bound_state` into a consumer — behavior-identical
  (the authority is module-global), and an authority-namer census
  would be a bespoke existence test over a 6-line private reader;
  a skipped `super().__init__()` — refused loud at first read by
  construction, pinned by oracle; a re-run `__init__` — refused by
  construction, pinned by oracle. Unity rests on the subclass
  declarations plus the pre-existing seam/isolation oracles.
- **Coupling.** None.
- **Freshness.** WT == baseline on all five files; HEAD `dd0b6691`:

| file | WT / baseline | HEAD |
|---|---|---|
| `extensions/operation_state.py` | `5f6f255d` | `009714fd` |
| `extensions/debug.py` | `b26a7897` | `fe67aad2` |
| `extensions/error_policy.py` | `c2f5eb5a` | `449b8f8a` |
| `extensions/resource_policy.py` | `2971618b` | `289dc159` |
| `optimizer/extension.py` | `8e3fe7c1` | `b7b6c434` |

Full WT hashes: `5f6f255ddd43c8e7081742df0f4b37edb21d7ead`,
`b26a7897279b9c22705b71d71b76143702480d9b`,
`c2f5eb5afa82c88c9f90188350ad11c9e400951e`,
`2971618b87885ccfca34a95355033fda3554a741`,
`8e3fe7c1fbc2d854cfcb805beb132e5639650e4d`.
`ITEM_BASELINE=f91630aea21eb5b67bdac42e4e3254cbb4595628`.
Searched population: `rg` over `django_strawberry_framework/` (all
`.py`), doubles swept in `tests/` + `examples/`. Excluded modules:
every other package module — no `_OperationBoundExtension` namer, no
`SchemaExtension` subclass, no resume/nestedness read outside the
censused sites.

### R1 — factory-override shape (rejected; declaration, not duplication)

The base default plus the two one-line overrides construct three
different types — the type IS the per-extension variation (principle
1), while the shared meaning (signature, call protocol, both call
sites) already lives once at the base. The shared form considered (a
`_state_class` attribute read by one base factory) relieves no change
on any live axis: a new stateful kind still needs the state class
plus one binding line, a per-state change still counts 1, and the
signature restatement is language design, as every `on_operation` /
`on_execute` / `resolve` override in the same files must. Contract
difference: naming the type vs sharing construction behavior (none
exists — C8 counts 0). Trigger: shared factory behavior beyond
construction (validation, transformation, conditional choice)
appearing in 2+ overrides — then it extracts to the base and the
overrides keep only the type selection. Specified home: the base
`_new_operation_state` docstring.

### R2 — `__init__` settle shape (rejected; adapters stay separate)

The three `__init__` bodies share exactly the `super().__init__()`
call — composition by name — and differ in everything else:
signatures (per-extension entry-point API), validation (bool gate /
canonicalization / strictness gate), and settled payload
(acknowledgement / accepted policy / strictness + strategy). The
driver (`PrivateAuthority`) is already shared; consolidating the
settles would couple independent config domains (principle 7).
Trigger: two extensions settling the same record type under the same
validation. Specified home: the base `__init__` docstring.

### R3 — refusal wordings (rejected; per-subject grammar)

Four strings, each naming what reconstruction would replace on its
own extension (binding carrier / disclosure acknowledgement /
accepted policy / strictness + strategy + plan cache); error policy
inherits the base string. Converges with the verified
per-subject-rejection-grammars direction on fresh evidence. Trigger:
wordings mandated to move together (a shared prefix or template).
Specified home: the base `_reconstruction_refusal` comment.

### R4 — state subclasses (rejected; distinct scratch)

`_DebugOperationState` (snapshots + payload) and
`_OptimizerOperationState` (stashes) carry disjoint per-operation
scratch; the base state carries the engine context both extend. C7
counts 1 per state. Trigger: a scratch field needed by 2+ states —
then it lifts to the base. Specified home: the `OperationState`
docstring.

### R5 — config authorities (rejected; distinct payloads)

Three authorities, three record types, three read postures
(False-default acknowledgement / copy-per-read policy / safe-default
configuration). Same settle-at-construction discipline, distinct
subjects — converges with the `policy-authority-isolation` direction.
Trigger: two extensions sharing one record type and read posture.
Specified home: each authority's comment (no base change).

### R6 — non-bound extensions (rejected; no per-operation state)

`_OperationModeMarker` (construction-fixed mode, read once),
`_AdmissionGuard` (stateless), `_RefusedConfiguration`
(fresh-per-operation, fixed message) keep no per-operation mutable
state — established from their bodies. Binding any of them would add
a state no hook reads. Trigger per member: the member gains mutable
per-operation state (marker), a verdict of its own (guard), or a
shared instance reused across operations (refused). Specified home:
each class docstring (no base change).

### R7 — exact-type vs subclass reads (rejected; distinct contracts)

`_declared_operation_mode` demands the EXACT marker type (a consumer
attribute named `mode` declares nothing); `_is_operation_bound`
accepts subclasses (extension kinds vary by subclassing). Converges
with the holding artifact's J1 on fresh evidence. Trigger: markers
gaining legitimate subclasses, or bound membership narrowing to exact
types. Specified home: the base module (no wording change — both
docstrings already state their reason).

No sub-rule decomposes to its own index row: the family stays whole
under F1; R1–R7 are exclusions with triggers plus specified homes,
for Worker-0 to transcribe or close out.

## Defects

None. No non-duplication bugs found while tracing. Concurrent-work
observations (out of scope, untouched, recorded for freshness only):
all five files carry hunt truth-migration + guard-narrowing + prose
dirt (`167+/208-` vs HEAD, itemized in the trace); WT == baseline on
all five; `utils/truth.py` / `utils/lazy.py` remain untracked;
`tests/utils/test_errors.py` MIXED but untouched by this item.

## Pending execution

None. Zero-edit verdict: every proof is static-reviewed over bodies
read at WT bytes, corroborated by the executed 55/55 oracle run
below. Cell typing: `default` executed (that run, shared venv);
`sharded` and `pg` are `inapplicable by construction` — the family
decides task-local binding identity (carriers, leases, tokens,
scopes; no queryset, alias, or dialect decision on the binding path).
Worker-2 judges the typing.

## Judgment

CONFIRM: the operation-bound extension mechanism is one rule,
already single-owned at `operation_state.py`, with four consumers
composing by subclass + refusal + state choice and no sixth member.
Every change challenge counts 1 at the owner or the owning
declaration; the seven closest shared forms are intentional
separations with contract differences, triggers, and specified
homes. Zero edits, zero defects, no gate owed.

## Implementation (Worker-1)

No production or test edits (CONFIRM single-owned, zero-edit
verdict) and no new tracked files besides this artifact (untracked
until Worker-0 records it). No ruff run — zero tracked `.py`
touched, vacuous, none owed (f52 precedent). No workspace run — no
source-mutating proof exists to need one. Concurrent dirt explicitly
untouched (see `## Defects` observations).

Focused oracle corroboration (one `--no-cov` run, shared tree,
exit 0):

```text
uv run pytest tests/extensions/test_operation_state.py --no-cov -n0 -q
55 passed in 0.87s
```

Type gates (shared venv, whole-scope, own runs):

```text
uv run basedpyright → 0 errors, 0 warnings, 0 notes
uv run python scripts/check_any.py → 128 allowed use(s) of Any at 89 site(s)
uv run python scripts/check_truthful_reads.py --check → 119 file(s); errors 0
```

Pins: HEAD `dd0b6691` unmoved; status count 505 (matches dispatch);
`ITEM_BASELINE=f91630aea21eb5b67bdac42e4e3254cbb4595628`; WT ==
baseline on all five files (table in F1); dispatch pins confirmed
(`5f6f255d`/`009714fd`, `b26a7897`/`fe67aad2`, `c2f5eb5a`/`449b8f8a`,
`2971618b`/`289dc159`, `8e3fe7c1`/`b7b6c434`).

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (own trace from source at
WT bytes; W1's `## System trace` / `## Verification` read, findings
not yet).

### Own trace

Owner I would choose:
`django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
with its module machinery — re-derived, not inherited. The rule as
I state it: one state object per (resolved extension, runner),
reachable only through a task-local carrier while that runner owns
it; a consumer composes it by subclassing the base, declaring (or
inheriting) the refusal wording, and building (or inheriting) the
state type. Runner side (`_operation_states` selection,
`_bind`/`_unbind`, `_BoundScope`, `_ResumedStream`,
`DjangoExtensionsRunner`) and the resume registry
(`OperationState.rebind_on_resume` / `resumed_bindings`) are the
same owner — one module, one responsibility (per-operation
binding), one reason to change.

Sites + roles (mine):

- Definition (owner): `_OperationBoundExtension` (refusal string,
  carrier `__init__`, `execution_context` property + compat
  setter, `_new_operation_state` default, `_operation_state`
  reader) + `OperationState` + runner/binding scope machinery +
  `_OPERATION_CARRIERS` / `_PACKAGE_MANAGED` + selection
  predicates (`_is_operation_bound`, `_binds_operation_state`) +
  mode marker + `operation_is_nested` + `_RunnerScope`.
- Consumers (4, each a declaration triple — subclass + refusal
  choice + state choice): `DjangoDebugExtension` (own refusal,
  own `__init__` with `super` + bool gate + settle, own factory,
  own state `_DebugOperationState`, own config authority),
  `DjangoErrorPolicyExtension` (inherits refusal / `__init__` /
  factory / base state; no config authority — reads
  `schema.error_policy` per operation), `DjangoResourcePolicyExtension`
  (own refusal, own `__init__` with `super` + settle, inherits
  factory + base state, own config authority),
  `DjangoOptimizerExtension` (own refusal, own `__init__` with
  `super` + compat assign + gates + settle + cache, own factory,
  own state `_OptimizerOperationState`, own config authority).
- Related consumers outside the five files: `schema.py::DjangoSchema`
  (`create_extensions_runner` builds `DjangoExtensionsRunner`;
  `get_extensions` appends marker/guard) and
  `resource_policy.py::adopt_budget_binding` (the one
  `rebind_on_resume` registration caller path).
- Oracles: `tests/extensions/test_operation_state.py` (4
  `_OperationBoundExtension` doubles: `_Probe`, `_SilentProbe`,
  `_Unbuilt`, `_RefusingState`) + live shared-entry matrices
  (`test_extension_isolation_api.py`,
  `test_resource_policy_api.py`, `test_error_policy_api.py`)
  whose doubles are plain consumer-shape `SchemaExtension`
  witnesses with no per-operation state of their own.
- Projections: the `operation_state.py` module docstring (owns
  the contract in prose), base/consumer docstrings.
- Examined and excluded (not members — contract difference in
  each body): `_OperationModeMarker` (construction-fixed mode
  fact, no hooks, no mutable per-operation state),
  `_AdmissionGuard` (stateless verdict restater reading
  task-local `admission_rejection()`), `_RefusedConfiguration`
  (built fresh per operation in `_refused_chain`, fixed message
  only). No other production `SchemaExtension` subclass exists
  (census below).

Own censuses (re-derived with `muse.search` over package +
tests + examples, WT bytes):

- Production `SchemaExtension` subclass declarations: 8
  including the base itself (base + 4 bound consumers + marker
  + guard + refused); 7 excluding the base. No subclass of a
  subclass anywhere; no `_OperationBoundExtension` namer
  outside the five indexed files in production; no
  `_OperationBoundExtension` subclass in `examples/` (only
  consumer-shape test doubles) — NO sixth member.
- `_new_operation_state`: base default + 2 one-line overrides
  (debug, optimizer); 2 call sites (compat setter,
  `_operation_states`). Error/resource inherit.
- `_reconstruction_refusal`: 4 declarations (base + 3
  overrides), exactly 1 read (`self._reconstruction_refusal`
  in base `__init__`).
- Extension `__init__`s with `super().__init__()`: 3 (debug,
  resource, optimizer); error policy has none. State
  `__init__`s with `super`: 2 (debug, optimizer states).
- `_operation_state()` production readers: 6 (base getter +
  debug x3 + optimizer + resource).
- Authority stores: 5 (mechanism 2: carriers + managed set;
  config 3: acknowledgement / explicit policy / optimizer
  configuration).
- `rebind_on_resume`: 1 definition, 1 production call
  (resource budget arming); `resumed_bindings` read once (in
  `_bind`).
- `operation_is_nested`: 1 definition, 1 production caller
  (optimizer, aliased import).
- Package-test `_OperationBoundExtension` doubles: 4
  (`_Probe` with `super`, `_SilentProbe` inheriting,
  `_Unbuilt` deliberately skipping, `_RefusingState` with
  factory).

Own definition counts (changes posited against the rule's
variation axes; consumers/oracles/projections listed, never
counted):

| # | Change posited | Definitions forced |
|---|---|---|
| W2-1 | a fifth operation-bound extension kind | 1 (the new declaration; base + runner discover it) |
| W2-2 | reword the base refusal | 1 (base string; overrides stand) |
| W2-3 | reword one consumer's refusal | 1 (that consumer only) |
| W2-4 | change lease terms / bind order / unwind | 1 (owner module) |
| W2-5 | accept or ignore a new assignment shape | 1 (setter + `_binds_operation_state`, same owner) |
| W2-6 | a second whole-operation registration, or handoff shape change | 1 (state registry; caller follows by name) |
| W2-7 | add a slot to one state | 1 (that state subclass) |
| W2-8 | validate or transform inside construction | 0 existing (no validation exists anywhere; overrides are one-line constructors) |

Independent consolidation search (zero-edit family — searched
before accepting): candidates considered were (a) the three
`__init__` settle bodies — distinct payloads (bool ack /
policy-or-None / strictness+strategy) with distinct gates, the
shared carrier-settle already in base `__init__`; (b) the two
one-line factories — construct different state types, shared
default already on the base; (c) the three refusal wordings —
per-subject grammar; (d) the two state subclasses — disjoint
slots; (e) marker/guard/refused — no per-operation mutable
state in their bodies; (f) exact-type vs subclass predicates —
distinct contracts (chain-carried fact vs extension kinds).
None is a real consolidation: each shared fragment already
lives once at the owner, each remainder is a per-consumer
declaration. CONFIRM single-owned, zero-edit.

### Reconciliation with W1's findings

(Read `## Findings` only after the trace above was recorded.)

- Owner: AGREE — same owner, same responsibility reasoning.
- Consumers: AGREE — same 4, same per-consumer composition
  (error inherits all four slots; resource inherits factory +
  state; debug/optimizer own all six columns).
- No sixth member: AGREE — my 8-with-base / 7-without-base
  census matches W1's 7 (base excluded); same three exclusions
  with the same contract differences, each established from
  its body.
- Censuses: AGREE on all — 3 extension inits + 2 state inits,
  4 refusal declarations + 1 read, base + 2 factories with 2
  call sites, 1 resume registration, 1 nestedness caller, 6
  `_operation_state()` readers, 5 authority stores, 4
  package-test doubles.
- Definition counts: AGREE — W2-1..W2-8 map onto C1..C8
  one-to-one with identical counts (1 x7, then 0 existing
  greenfield). The C8 count-0 call is correct: no validation
  exists in any factory, so there is nothing to consolidate;
  the signature spellings are language-forced declarations.
- Rejections R1–R7: AGREE on all seven — each carries its
  contract difference + trigger (details under rulings (c)).
- Specified-but-unlanded homes ("closeout applies"): RULED on
  under (c) — ACCEPTED under the f52 R3 precedent (hunt-dirty
  files, zero-edit item, homes specified verbatim).
- No-gate-owed: RULED on under (d) — ACCEPTED; W1's
  four-bypass analysis discharges the gate-only bar.
- Zero-edit: AGREE — scoped diff empty (verified mechanically
  myself), no oracle rewritten, nothing touched.

### Worker-0 check-point rulings

- (a) Sixth-member sweep + 23-member enumeration: VERIFIED
  member by member. My independent censuses reproduce every
  population figure (7 production subclasses sans base, 4
  bound declarations, 2 state subclasses, 3 extension inits,
  3 factory spellings, 4 refusal declarations, 1 resume call,
  1 nestedness caller, 6 readers, 5 stores, 4 doubles). All 23
  enumeration rows home correctly; the 4 test doubles verified
  by body (`_Probe` composes by `super`, `_SilentProbe`
  inherits, `_Unbuilt` is the negative control for the
  carrier refusal, `_RefusingState` exercises the factory
  seam); live-tier witnesses are plain `SchemaExtension`
  consumer shapes with no per-operation state.
- (b) C1–C8: VERIFIED — counts re-derived independently
  (table above), identical. C8 count-0 greenfield call is
  correct and feeds R1 soundly: a change to validation that
  exists nowhere forces zero definitions.
- (c) R1–R7 triggers + unlanded homes: VERIFIED. Each
  rejection carries a contract difference (R1 factory shape
  is declaration; R2 settle bodies carry distinct payloads +
  gates; R3 refusals are per-subject grammar; R4 states carry
  disjoint scratch; R5 authorities carry distinct payloads +
  read postures; R6 non-bound bodies keep no per-operation
  mutable state; R7 exact-type vs subclass are distinct
  contracts) and a reconsideration trigger. RULING on
  "closeout applies": ACCEPTED. The f52 R3 precedent accepts
  specified-but-unlanded homes for rejections on hunt-dirty
  files; a CONFIRMED single-owner owes no more than a
  rejection here — each home is named as a precise location
  (a base docstring / comment / class docstring) with its
  contract difference + trigger on record, so closeout can
  land it without re-derivation; the files are
  blocked-on-hunt, and landing prose on hunt-dirty lines now
  would risk the exact collision the block exists to
  prevent.
- (d) No-gate-owed + f21/f48 precedent: VERIFIED. RULING:
  ACCEPTED. A confirmed single owner with no gate is a
  `gate-only` finding needing a justified population; W1
  supplied the justification by judging four concrete
  bypasses against the gate-only bar: (i) a fifth kind
  hand-rolling its own carrier — plausible as a mistake,
  but the population is unjustified ("keeps per-operation
  state" needs reading bodies, no syntax gates it) and a
  subclass-count census fires on legitimate variation
  (C1); (ii) a reader-copy of `_carrier`/`_bound_state`
  into a consumer — behavior-identical (module-global
  authority), and an authority-namer census would be a
  bespoke existence test over a 6-line private reader;
  (iii) a skipped `super().__init__()` — refused loud at
  first read by construction, pinned by oracle
  (`_Unbuilt` row); (iv) a re-run `__init__` — refused by
  construction, pinned by oracle. Each judgment verified
  against the bodies: the carrier refusal + reconstruction
  refusal + oracles exist as cited. Under the f21/f48
  precedent (no bespoke existence test per helper), no gate
  is owed.
- (e) Consumer composition census + byte-identical claim:
  VERIFIED against `git show HEAD:` myself. Census figures
  reproduce exactly. The composing lines (4 subclass
  declarations, 3 refusal strings, 3 `super().__init__()`
  calls, 2 factory defs + returns, 2 state class decls +
  `super` calls) are byte-identical HEAD vs WT: the hunt
  hunks touch class docstrings, `__init__` gate bodies
  (`isinstance` → exact-type, `describe_value` /
  `_safe_arg_repr` → `truth.describe` / `truth.render`),
  teardown bodies, and predicates — never a composition
  line. The owner-side mechanism hunks (`_is_operation_bound`
  + `_binds_operation_state` predicates:
  `issubclass` → `truth.is_subclass`, guard narrowing;
  compat-setter / `_operation_state` reader truth markers;
  `_carrier` message via `truth.name`) are external
  truth-migration dirt, not composition lines, and change
  no census or count. Base `__init__`, refusal string,
  factory default, and property getter are untouched.
- (f) Freshness table: SPOT-CHECKED by re-hashing — all five
  WT/HEAD pins reproduce exactly (`5f6f255d`/`009714fd`,
  `b26a7897`/`fe67aad2`, `c2f5eb5a`/`449b8f8a`,
  `2971618b`/`289dc159`, `8e3fe7c1`/`b7b6c434`); HEAD
  `dd0b6691` unmoved.
- (g) Dirt attribution: VERIFIED — all WT hunks in the five
  files are external hunt work (truth migration, guard
  narrowing, prose); none matches a `## Owned changes`
  ledger row; WT == `ITEM_BASELINE` on all five files. The
  ledger's adopted error-policy three-sites row sits at HEAD
  (citations are HEAD line numbers, verified via
  `git show HEAD:`: the three-seams prose at `:16`, "One
  masking implementation, three places it is applied" at
  `:41`, and the `on_operation` docstring's "see the module
  docstring for all three seams" at `:454` — the WT file
  ends at 445, so `:454` is HEAD-only and correct as such);
  the WT hunk on the `:41` paragraph only EXTENDS the
  rationale ("The three sites become one only if..."), it
  does not move the adopted row. The cited 55/55 oracle run
  is statically consistent with the file at these bytes (45
  test functions, 5 parametrized 2/3/3/3/4 → 55 cases) and
  the test file is unchanged since `ITEM_BASELINE`.
- (h) Sharded/pg inapplicable: VERIFIED — `inapplicable by
  construction` is correctly typed. The mechanism binds
  in-memory operation state through task-local carriers; it
  reaches no database, no alias, no dialect decision. No
  queryset is built, no id decoded, no connection touched on
  any path through the five files' mechanism lines.
- (i) Independent consolidation search: DONE (see above) —
  six candidates considered, none real. Zero-edit accepted
  on my own search, not on W1's word.
- (j) Axis-2 one-body-with-adapters + axis-6 exclusions:
  VERIFIED from bodies. Axis 2: `_BoundScope.__enter__` and
  `__aenter__` both call the one `_bind` primitive (async
  differs only in wrapped-scope enter/exit); sync/async
  result collection share `_bound`; all four `_ResumedStream`
  drives wrap `resumed()` — one body with adapters, already
  the principle-5 answer. Axis 6: all 7 production
  subclasses enumerated; the three non-bound exclusions
  established from their bodies (fixed fact / stateless /
  fresh-per-operation), not from sibling behavior. No gap,
  no defect.

### Gates + pins (own runs, shared venv, whole-scope)

- `uv run basedpyright` → 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_any.py` → 128 allowed use(s)
  of Any at 89 site(s).
- `uv run python scripts/check_truthful_reads.py --check` →
  119 file(s); errors 0.
- mypy: not run, not cited (gone).
- Ruff: vacuous — zero tracked `.py` touched (scoped diff
  empty); confirmed, none owed.
- Pins: HEAD `dd0b6691` unmoved; `ITEM_BASELINE=f91630ae…`;
  `git diff f91630ae -- .` excluding the plan is empty; all
  five dispatch pins reproduced (see (f)). No defect found;
  no `(Worker-2)` entry owed under `## Defects`.

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
