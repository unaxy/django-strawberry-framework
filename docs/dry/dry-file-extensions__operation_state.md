# DRY review: `django_strawberry_framework/extensions/operation_state.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below lands in one NAMED family (one new, owned here; two indexed, checked
with no surface) or is recorded file-local with its proving challenge, and
every rejection carries its contract difference + trigger + home. Zero
production edits; zero tracked files changed.

## System trace

FRESH target, 922 lines: the per-operation state mechanism for extensions the
engine hands the same object to twice. It DEFINES the operation-bound
extension base
([extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`),
the runner that owns every operation binding
([extensions-operation-state][extensions-operation-state]`::DjangoExtensionsRunner`),
the scope + nesting + executor-mode facts the runner settles, the
bind/unbind lifecycle over leases and tokens, and the streamed-resumption
protocol. It ENFORCES nothing about budgets, masks, payloads, or plans —
those live in the four consumer extensions, which compose this mechanism by
name (subclass + refusal string + state factory). No queryset execution, no
resolver body, no `sync_to_async`, no `run_in_one_sync_boundary`, no
awaitable handling, no logger, no soft dependency, no
`register_subsystem_clear`.

Connected code read for judgment, outside the item:
[schema][schema] (runner factory + `_stream` wrapper + admitted-chain marker
install + declaration folding, passages),
[extensions-debug][extensions-debug] (`_DebugOperationState` + refusal
override + dual-teardown stash, passages),
[extensions-error-policy][extensions-error-policy] (teardown shape + no state
subclass, passages),
[extensions-resource-policy][extensions-resource-policy] (refusal override +
budget resume registration, passages),
[optimizer-extension][optimizer-extension] (`_OptimizerOperationState` +
refusal override + nested read, passages),
[optimizer-context][optimizer-context] (execution-frame lease idiom,
passages), [resource-policy][resource-policy] (budget lease + resume
binding + adopt/end, passages),
[utils-operation-lease][utils-operation-lease] (lease contract, full),
[utils-private-state][utils-private-state] (authority contract, full),
[utils-execution-mode][utils-execution-mode] (mode-carried-not-sampled +
bind primitive, full), [exceptions][exceptions] (`ConfigurationError`
owner, passages), [extensions-init][extensions-init] (leaf privacy prose,
full), oracles [test-operation-state][test-operation-state] (module
docstring contract map + seam-driving rows, head + spot bodies) and the
live isolation matrices (`test_extension_isolation_api`,
`test_resource_policy_api`, `test_error_policy_api` — disclosure outcomes,
titles + head), contract sources spec-050 Decisions 14/19 (config-vs-state
split; mode carried not sampled) and the GLOSSARY operation-isolation
anchor (projection corroborating the contract).

Excluded with reason: every other indexed family was judged on its
mechanism against this target's REAL surface (Matrix axes 1–3, C16–C17,
probe §4); the concurrent dirt (`django_strawberry_framework/connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths. Prior artifacts used only as
rejected-candidate triggers, each re-derived fresh from this side (the debug
artifact's F6 mechanism-vs-override split; the querysets artifact's F1
awaitable rule with its "reported to the operation-state extension"
posit; the error-policy artifact's J1 enforcement-unification refusal; the
schema artifact's runner consumer rows). Never read another worker's
`worker-memory/`. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched and hold none of this finding's
sites.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target owns no flavor policy: it is
the cross-cutting mechanism every enforcement/diagnostic flavor composes
(four subclasses, each owning its own policy object elsewhere). The sibling
extensions share only this base (an owned extension point, F1) plus the
`PrivateAuthority` and `OperationLease` primitives (single owners composed
by name — F1/F3/F4). The resource/error enforcement unification is refused
from this side too (J2 corroborates the error-policy artifact's J1: this
file holds mechanism both use and policy neither does). Considered families
`awaitable-refusal-and-disposal` (0 awaitable vocabulary — R1, do not
inherit) and `sealed-execution-queryset` (0 queryset vocabulary — checked,
not a member).

**2. Sync/async twins.** Three colored surfaces, each owned here with its
twin discipline stated: `_BoundScope` sync/async `__enter__`/`__aenter__`
pairs share the ONE `_bind`/`_unbind` body and differ only in how they
enter/exit the wrapped scope (principle 5's one-body answer: the binding
decisions are pure; only the protocol adapts); `get_extensions_results_sync`
vs `get_extensions_results` share the one `_bound` scope and differ only in
the await (one scope helper + two thin adapters); `_ResumedStream` is
async-only by engine construction (streams are async iterators — no sync
twin owed, inapplicable with reason). `one-sync-boundary` checked: 0
`run_in_one_sync_boundary`/`sync_to_async` calls (probe §4) — nothing here
executes the ORM, so there is no boundary to join; R2, do not inherit. The
`connection.py` two-colored-body contrast is the opposite correct answer on
the same axis (consumer `async def` hooks must be awaited there; this
runner wraps scopes and calls no consumer async code inside the binding),
recorded here for the family/folder pass to home — no edit owed by this
file item.

**3. Derived rather than repeated knowledge.** Every per-operation fact is
derived once: nested settled once at the runner's first binding (`_scope`);
mode read once out of the chain (`_declared_operation_mode`); states built
once in the runner `__init__` (`_operation_states`); `_scope()` memoized;
`_already_bound` by scope identity. Readers compose by name
(`operation_is_nested`, `current_operation_mode` at
[utils-execution-mode][utils-execution-mode], `_armed_budget` at
[resource-policy][resource-policy]). No reconstructed copy found; C6 moves
one site. Considered `soft-dependency-require-guard`: 0 `require_*`
calls — no surface.

**4. Inverse / round-trip pairs.** Four pairs, each single-owned in this
file, never split across modules: `_bind`/`_unbind` (one primitive + its
unwind, with failure-unwind inside `_bind` itself); lease-close +
token-reset inside `_unbind` (close-first order is the stated copied-context
half vs owning-context half); `_register_resumed_binding` /
`_reset_adopted_binding` (adopt/take-back halves of the registrar handoff);
`rebind_on_resume` / `resumed_bindings` (write/read halves on the state).
No pair can drift; C8–C13 prove the split points.

**5. Contracts restated in another medium.** Four media: production code
(the definitions); consumers composing by name (four subclasses; schema
runner factory + `_stream` wrapper + marker install; resource budget
registration; optimizer nested read); independent oracles
([test-operation-state][test-operation-state]: 46 test functions driving
the seams directly — assignment-records-nothing, runner-builds-all-states,
copied-context-reads-nothing, double-construction-refused, stream
resumption bound; live isolation matrices asserting the disclosure
outcomes per shared-entry shape and view color); projections (module +
class + method docstrings, spec-050 D14/D19 contract sources, GLOSSARY
anchor, leaf privacy prose). A mechanism change moves the production owner
once; oracles and prose follow as listed-never-counted (every challenge
below).

**6. Enforcement by omission.** Family = every extension installed on a
schema. `_operation_states` selects ONLY `_is_operation_bound` members; a
consumer extension is deliberately neither wrapped, copied, nor proxied
(stated in its docstring — upstream's assignment is its whole state, and
proxying it would be a second authority). The omission that WOULD be a gap
(a subclass skipping the base `__init__`, leaving no carrier to bind) is
closed by construction: `_carrier` refuses with `ConfigurationError`
(probed consumer: `_Unbuilt` oracle row). The raw-schema shared-instance
shape is outside the guarantee by documented limitation (module docstring +
all four consumer class docstrings), not by missing guard. No member lacks
a guard its contract requires; no defect, no card.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **43 top-level statements (0–42)** — plus, better than the
minimum, every body member of all 8 classes (5/3/2/7/5/7/8/9). Every member
lands below; every challenge in `### Challenges` ends in a family row, a
file-local row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (shared-entry diagnosis, config-vs-state split, lease-on-weakref lifetime, nested/mode/stream/raw-schema contracts) | (none) | prose projection; F1–F5 homes |
| 1–12 | `__future__` + stdlib/upstream/first-party imports | names | consumer bindings (F1/F2/F3 use); machinery |
| 13 | `__all__ = ("DjangoExtensionsRunner", "OperationState")` | 2-member manifest | covered by existing `extensions-helper-state-privacy-omission` row (helpers stay submodule-private); no new row |
| 14 | `OperationState` + `__init__`/`rebind_on_resume`/`resumed_bindings` | per-operation state + resume registry | F4 (registry halves) + F5 (state lifetime) |
| 15 | `_RunnerScope` (`nested`, `mode`) | one-scope-per-runner record | F2 |
| 16 | `_OPERATION_CARRIERS` authority | per-extension carrier store | F1 |
| 17 | `_PACKAGE_MANAGED` authority | managed-set store | F1 |
| 18 | `_RUNNER_SCOPES` variable | live-scope binding | F2/F3 |
| 19 | `_RESUME_REGISTRARS` variable | resume registrar binding | F4 |
| 20 | `_register_resumed_binding` | adopt-handoff primitive | F4 |
| 21 | `_OperationModeMarker` + `__init__` | chain-carried mode fact | F2 |
| 22 | `_declared_operation_mode` | exact-type chain read | F2 (+ J1) |
| 23 | `_live_scope` | live-lease scope read | F2 |
| 24 | `operation_is_nested` | public nested read | F2 (consumer: optimizer) |
| 25 | `_carrier` | carrier recall-or-refuse | F1 |
| 26 | `_bound_state` | lease+weakref state read | F1 |
| 27 | `_is_package_managed` | managed predicate | F1 |
| 28 | `_mark_package_managed` | managed mark + compat drop | F1 |
| 29 | `_is_operation_bound` | subclass predicate | F1 (+ J1) |
| 30 | `_binds_operation_state` | compat-branch predicate | F1 |
| 31 | `_OperationBoundExtension` + 7 members (refusal, `__init__`, property + setter, `_new_operation_state`, `_operation_state`) | the mechanism | F1 OWNER |
| 32 | `_operation_states` | per-operation selection + marking | F1 |
| 33 | `_Binding` (lease/token/adopted) | one undo record | F3 |
| 34 | `_bind` | scope+state binding w/ unwind | F3 |
| 35 | `_already_bound` | scope-identity guard | F3 |
| 36 | `_reset_binding` | token reset | F3 |
| 37 | `_unbind` | close-then-reset unwind | F3 |
| 38 | `_reset_adopted_binding` | adopted take-back | F3/F4 |
| 39 | `_bound` | hold-bound context manager | F3 |
| 40 | `_BoundScope` + 7 members (dual `__enter__`/`__aenter__` pairs) | upstream-scope wrapper | F3 |
| 41 | `_ResumedStream` + 8 members (`__aiter__`/`__anext__`/`asend`/`athrow`/`aclose`) | per-drive stream binding | F4 |
| 42 | `DjangoExtensionsRunner` + 9 members (`__init__`, `_scope`, `operation`, `on_stream_result`, `resumed`, `resumed_stream`, sync/async result collection) | lifetime owner + scopes | F5 (+ F2 scope settle) |

Rules: R-mech (16, 17, 25–32: carrier + managed set + refusal + compat
setter + selection); R-scope (15, 18, 21–24: scope/nested/mode);
R-bind (33–40: leases/tokens/registrar/unwind/dual adapters); R-resume
(14-registry half, 19, 20, 38, 41: handoff + per-drive binding); R-runner
(14-state half, 42: lifetime + operation/result/stream scopes). Indexed
families considered: `awaitable-refusal-and-disposal` (R1),
`one-sync-boundary` (R2), `sealed-execution-queryset`,
`typed-rejection-value-tail`, `logger-single-sourcing`,
`soft-dependency-require-guard`, `subsystem-clear-lifecycle` (all checked,
no surface — probe §4); every remaining indexed family has no vocabulary
in this target (full read: no queryset/filter/order/mutation/form/relay/
registry/consumer/view/request-body/auth machinery). One new family is
named (F1 — the mechanism with four composing consumers); four definition
rules are file-local with proving challenges (F2–F5).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-mech membership | a fifth operation-bound extension kind | **1** (the new subclass declaration — refusal string + state factory; base + runner discover it) | F1 new family |
| C2 | R-mech refusal | reword the base reconstruction refusal | **1** (the base; all four overrides stand — proves override-not-copy) | F1 |
| C3 | R-mech compat | hold the raw-schema compat state weakly instead of on the instance | **1** (the setter branch; managed extensions untouched) | F1 |
| C4 | R-mech selection | wrap consumer extensions too (not just select package ones) | **1** (`_operation_states`; every consumer keeps working — proves the boundary) | F1 |
| C5 | R-scope settle | settle `nested` at construction instead of first binding | **1** (`_scope`; stream-driven-after-close contract follows) | F2 |
| C6 | R-scope mode | sample the ambient loop instead of reading the marker | **1** here (`_declared_operation_mode` + `_scope`; [utils-execution-mode][utils-execution-mode] untouched — proves separation) | F2 |
| C7 | R-scope marker read | accept marker subclasses, not just the exact type | **1** (`_declared_operation_mode`; schema install untouched) | F2 (+ J1) |
| C8 | R-bind order | reset tokens before closing leases | **1** (`_unbind`; copied-context readability follows) | F3 |
| C9 | R-bind adopted | raise on an already-used adopted token instead of tolerating | **1** (`_reset_adopted_binding`; single-frame streamed ops follow) | F3 |
| C10 | R-bind reentry | rebind inside the runner's own scope instead of skipping | **1** (`_bind` via `_already_bound`; resume/generator scopes follow) | F3 |
| C11 | R-resume handoff | the arming scope ends its own binding inside the resume (no adopt) | **1** (the register/reset-adopted pair; budget scope follows) | F4 |
| C12 | R-resume drive | drive stream frames with no per-drive binding | **1** (`_ResumedStream`; generator scopes untouched) | F4 |
| C13 | R-resume second value | change the registrar handoff shape | **1** (`_register_resumed_binding`; the one consumer call follows) | F4 |
| C14 | R-runner collection | collect results with no binding (read off the shared extension) | **1** per scope method (the runner; the stale-payload disclosure returns — why the scopes exist) | F5 |
| C15 | R-runner stream | wrap a non-package runner's stream | **0 here** (schema passes it through — proves the boundary) | F5 |
| C16 | awaitable reporting | report a rejected awaitable to the operation-state extension before disposal | **0 exist** (no awaitable vocabulary — probe §4; the querysets F1 posit reaches no hook here) | no surface — do not inherit |
| C17 | sync boundary | route the binding through `run_in_one_sync_boundary` | **0 calls** (no ORM work; pure ContextVar/lease/token decisions) | no surface — do not inherit |

**Experiment.** Read-only probe (no source mutation, no Django setup, no
DB, no shared-tree pytest — the workspace recipe is for mutating proofs,
of which this zero-edit item has none):

```shell
python3 docs/dry/temp-tests/dry-file-extensions__operation_state/probe_w1.py
```

Output (`W1 PROBE: ALL OK`, 36 checks): 43-member module AST with exact
kind sequence + 8-class body census (§§1–2); 7 async defs exactly where the
twins live, none at module level (§3); zero family vocabulary for all
seven absence probes (§4); one-way primitive edges + schema consumer edge
(§5); four subclass consumers by name (§6); two-member manifest (§7);
working blob == `HEAD:` blob + item-baseline diff empty (§8); package
population 117 (§9). Status: `execution-verified` for every
identity/count/shape/absence/import claim below. Rejects the wrong results
"a second binding definition exists", "an async twin is missing",
"the seam restates the mechanism", "the target drifted from its
baseline". Bodies, seams, and oracle rows are `static-reviewed`.

## Findings

No production edit is owed by a file item; F1 below is the NEW family this
file owns (mechanism-vs-override split re-derived fresh from this side),
F2–F5 its file-local rules with proving challenges, R1/R2 indexed-family
checks, J1/J2 recorded rejections.

### F1 — operation-bound extension mechanism (new family `operation-bound-extension-mechanism`, owner here)

- **Contract + variation.** One state object per (resolved extension,
runner), reachable only through a task-local carrier while that runner
owns it. Configuration stays with authorities; per-operation mutable state
sits on the state the runner builds. The engine's `execution_context`
assignment records nothing for a `DjangoSchema` (compatibility glue for
raw schemas only); a package-managed extension ignores every later
assignment of every shape. The carrier is settled once at construction
behind `PrivateAuthority` (a second `__init__` is refused, with an
overridable message); a subclass whose `__init__` never ran the base is
refused at first read. Legitimate variation: the per-extension scratch
shape (the subclass's state) and the refusal wording (the subclass's
string) — both declarations, never base edits.
- **Mechanism-vs-override split (re-derived, not inherited).** Base owns:
carrier mint + recall-or-refuse (`_carrier`), lease-on-weakref read
(`_bound_state`), managed mark + compat drop (`_mark_package_managed`),
compat predicate (`_binds_operation_state`), selection
(`_operation_states`, `type()`-based for the hostile-`__class__` reason
[schema][schema]`::_is_extension` states), refusal point
(`_reconstruction_refusal`). Each of the four consumers owns: its refusal
string (debug names the acknowledgement; optimizer names strictness +
strategy + plan cache; resource names the accepted policy; error policy
takes the base string — inheriting the point IS the composition), its
state factory (`_DebugOperationState`, `_OptimizerOperationState`;
error/resource use the base `OperationState` — no factory where no
scratch exists), its configuration authority (elsewhere in each case).
Posit C2 → base only; posit rewording one consumer's refusal → that
consumer only (0 at base). Override, not copy.
- **Sites + roles.** *Definitions* (all here, unchanged): statements 16,
17, 25–32. *Consumers*: the four subclasses (compose by name — probe §6);
[schema][schema]`::create_extensions_runner` + `_stream` (build + wrap
by name). *Oracles*: [test-operation-state][test-operation-state]
(assignment-records-nothing, runner-builds-all-states, skipped-constructor
refused, double-construction refused — independent: drive the seams,
never read the authorities); live isolation matrices (disclosure
outcomes per shared-entry shape). *Projections*: module docstring
(entire contract), base docstrings (carrier/compat/selection rationale),
spec-050 D14 (contract source for the config-vs-state split).
- **Challenges.** C1–C4 → 1 each here.
- **Owner + lifetime.** This file (narrowest cohesive owner every
legitimate consumer can depend on without reversing a dependency: the
primitives never import it back — probe §5; the schema already depends
downward). Stored-derivation lifetimes (principle 4): carriers — owner
`_OPERATION_CARRIERS`, validity extension identity, publish construction,
mutators none (settle-once + refusal), invalidated on owner collection;
managed marks — same, boolean payload retaining nothing; compat state —
instance `__dict__`, dropped at marking.
- **Migration.** None (zero-edit item; composition already by name).
- **Distinct behavior.** Consumer extensions keep upstream's assignment
(axis 6 — deliberate, contract-sourced); raw-schema shared instances stay
outside the guarantee (documented limitation, not a gap); error policy's
no-factory shape stays factory-less (no scratch, no subclass).
- **Behavioral proof.** `execution-verified` for census/edges/absences
(probe); `static-reviewed` for base/consumer/oracle bodies. Rejects "a
second carrier authority exists" (probe: one `PrivateAuthority` per
payload, distinct payloads) and "an override copies the mechanism"
(C2 moves base only).
- **Structural gate.** The existing seam-driving rows (assignment,
construction, skipped-constructor, isolation) + live matrices: a local
restatement of the carrier in one consumer passes happy-path oracles and
fails the nested/concurrent isolation rows the owner adds. Negative
control (stated honestly, not run): a behavior-preserving hand copy of
`_carrier`/`_bound_state` into a consumer passes every behavioral oracle
and fails only the import census — so cross-file unity rests on the
one-way edges plus this finding; no new gate owed by a file item.
- **Coupling.** None.
- **Freshness.** Target `b2674a22d2dfd58ff97c51a02e16068bb22032e9`
(== `HEAD:` blob), [schema][schema]
`2f72732123ca1156c4eb122ce7b53de6269de95e`,
[extensions-debug][extensions-debug]
`bf25c146111337ee0af590e7496b34c010c2f7be`,
[extensions-error-policy][extensions-error-policy]
`baea073f5615aaddc82c1f463071998bee7a6b62`,
[extensions-resource-policy][extensions-resource-policy]
`52084078ac166d8116b9e4bb2522e8ce193251ea`,
[optimizer-extension][optimizer-extension]
`49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`,
[utils-private-state][utils-private-state]
`08088b820ac20579e471915644a931953362fca8`,
[test-operation-state][test-operation-state]
`b3a574b155d982ed4db85419fe9a785e9bba0ef2`. Searched population:
whole package (117 `.py`) for a second carrier/managed/selection
definition — every hit lands in owner / consumer / oracle / projection
as recorded. Excluded on strength of body: the four consumers (compose,
never redefine), [utils-private-state][utils-private-state] (primitive
owner, distinct payloads).

### F2 — runner scope + nested fact + executor mode (file-local)

- **Contract + variation.** One scope object per runner, settled at its
first binding (not construction — a stream is driven after its operation,
in a task that merely copied context): `nested` from whether a LIVE outer
lease was bound (copied-but-ended reads top-level — the lease half, not
the token half); `mode` from the chain's exact-type marker read once
(`None` = chain with no marker: non-`DjangoSchema` or custom chain —
readers fall back to ambient dispatch, exactly as upstream leaves it).
Legitimate variation: what settles each field — both here.
- **Sites + roles.** *Definitions*: statements 15, 18, 21–24 (+ 42-`_scope`
settle). No second nested/mode derivation in the package (probe: one
`ContextVar` per fact; readers at
[utils-execution-mode][utils-execution-mode] and
[optimizer-extension][optimizer-extension] compose by name).
*Consumers*: [schema][schema] (installs the marker in `_admitted_chain`
+ `get_extensions`; builds the runner), optimizer (nested read per
execution frame), execution-mode readers (mode). *Oracles*: nested-matrix
rows + copied-context top-level rows in
[test-operation-state][test-operation-state]; mode-carried rows in
`tests/utils/test_execution_mode.py` (defers to the operation-state
suite for binding behavior — stated in its head). *Projections*: scope +
marker docstrings; spec-050 D19 (contract source: mode carried, not
sampled).
- **Challenges.** C5, C6, C7 → 1 each here (C6 leaves
[utils-execution-mode][utils-execution-mode] untouched — proves
separation: that file owns the bind primitive + readers, this one owns
the settle + chain transport).
- **Owner + lifetime.** `_RunnerScope` + marker + readers (existing owners
by responsibility: the runner is the only point seeing chain + context
together). Lease lifetime: bound per scope, closed on unwind; validity a
live outer lease.
- **Migration.** None.
- **Distinct behavior.** `None`-mode fallback stays (raw-schema contract);
copied-context top-level stays (lease half).
- **Behavioral proof.** `execution-verified` (probe census + edges);
`static-reviewed` (settle/read bodies, oracle rows). Rejects "mode is
re-sampled per hook" (one read, memoized scope) and "nested is hook
property" (runner property — resolver/teardown/collection all answer
alike).
- **Structural gate.** Pre-existing nested + mode rows — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target as in F1,
[utils-execution-mode][utils-execution-mode]
`9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9`,
[schema][schema] as in F1,
[optimizer-extension][optimizer-extension] as in F1.

### F3 — bind/unbind lifecycle + dual-protocol adapters (file-local)

- **Contract + variation.** `_bind` binds scope + mode + every state as
leases (states as leases on weakrefs — the runner stays the one strong
owner), plus each state's resumed bindings, unwinding everything it bound
if one bind fails; `_unbind` closes every minted lease FIRST (the half a
copied context can observe) then resets every token independently
(enclosing operation restored in the owning context); adopted bindings
taken back tolerantly (already-used = the arming scope ended inside this
resume — the variable already holds the right value). `_already_bound`
skips by scope identity (a resume holding this runner's bindings meets its
own operation scopes — rebinding would strand tokens across tasks). One
binding primitive under BOTH sync and async adapters (`_BoundScope` differs
only in enter/exit protocol). Legitimate variation: ordering, tolerance,
reentry — all here.
- **Sites + roles.** *Definitions*: statements 18 (variable), 33–40.
*Consumers*: every runner scope method (same file — F5). *Oracles*:
failure-unwind rows, adopted-tolerance rows, own-scope reentry rows in
[test-operation-state][test-operation-state]. *Projections*: `_bind` /
`_unbind` / `_reset_adopted_binding` / `_already_bound` docstrings (each
states its ordering/tolerance/identity reason).
- **Challenges.** C8, C9, C10 → 1 each here.
- **Owner + lifetime.** The five functions + two records (existing owners
by responsibility: the only code minting/closing/resetting these
bindings). No stored derivation beyond the bindings themselves (tokens +
leases created and undone in one scope).
- **Migration.** None.
- **Distinct behavior.** Close-before-reset stays (copied-context half vs
owning-context half); tolerant adopted reset stays (single-frame streamed
ops); identity-not-equality stays (one runner, one scope object).
- **Behavioral proof.** `execution-verified` (probe census);
`static-reviewed` (unwind/tolerance/identity bodies + oracle rows).
Rejects "reset suffices without close" (copied task keeps reading) and
"two primitives for two colors" (one primitive, two adapters — C10 moves
one site).
- **Structural gate.** Pre-existing unwind/tolerance/reentry rows — no new
gate owed.
- **Coupling.** None.
- **Freshness.** Target as in F1; no second-site population (whole-package
sweep for a second bind/unbind pair: none — the budget `_BudgetScope` at
[resource-policy][resource-policy] `647133d23785d325856b2d1d495d18c5741dd23c`
is a distinct scope with distinct ownership prose, read and excluded).

### F4 — streamed resumption + resume registrar (file-local)

- **Contract + variation.** Whole-operation state armed DURING a frame
(the resource budget) must be bound in tasks the operation never started:
the state registers `(variable, value)` on itself; the runner re-binds
registrations around every drive (`__anext__`/`asend`/`athrow`/`aclose`
— close-from-another-task is the teardown that must not strand the
budget); the FIRST resume's extra binding is handed its token by the
registrar and taken back on the way out, so the driving task answers from
its enclosing operation (or nothing) between frames. Long-lived generator
scopes bind nothing while the resume holds the bindings (no token spans a
yield). Legitimate variation: what registers, what the registrar hands
over — here.
- **Sites + roles.** *Definitions*: statements 14 (registry halves), 19,
20, 38, 41. *Consumer*: the resource extension (the ONLY registrar —
`state.rebind_on_resume(*budget_resume_binding(scope))` at
[extensions-resource-policy][extensions-resource-policy], adopting via
`adopt_budget_binding`; [resource-policy][resource-policy] owns the scope
shape). *Oracles*: stream-task binding + subscription-resumption rows in
[test-operation-state][test-operation-state] (fakeshop has no ASGI mount —
stated in its head — so these rows are the contract, not the live
matrices). *Projections*: `rebind_on_resume` docstring (resume-vs-operation
lifetime, the told-apart point), `_ResumedStream` docstring (per-task
drive, per-method binding).
- **Challenges.** C11, C12, C13 → 1 each here (C13's consumer call
follows by name — 0 there).
- **Trigger re-checked fresh (registrar's only consumer).** Exactly one
registration call site in the package (resource budget); the optimizer
frame is NOT registered (its lifetime is the execution, opened per
`on_execute` — read at
[optimizer-extension][optimizer-extension]`::on_execute`). A second
whole-operation value would compose the same two calls — the recorded
trigger for a future family split.
- **Owner + lifetime.** `OperationState` registry + registrar + stream
wrapper (existing owners by responsibility: the state is what an extension
has a handle on; the runner is what drives). Registration scoped to one
operation by construction (stored on the state, rebound per resume, ended
by the arming scope).
- **Migration.** None.
- **Distinct behavior.** Between-frames answering (enclosing-or-nothing)
stays; generator-scope non-binding stays; close-binds-teardown stays.
- **Behavioral proof.** `execution-verified` (probe census + async-def
shape); `static-reviewed` (handoff/adopt/drive bodies + resumption
rows). Rejects "arming scope ends its own inside a resume" (adopted path
— C11) and "bind once per stream" (per-drive — C12).
- **Structural gate.** Pre-existing resumption rows — no new gate owed.
- **Coupling.** None.
- **Freshness.** Target as in F1,
[extensions-resource-policy][extensions-resource-policy] as in F1,
[resource-policy][resource-policy] `647133d2…` (above),
[optimizer-context][optimizer-context]
`3d8dcfdfba5ba644b4759f80e95d57ba0fa1a98b` (frame idiom read, distinct
scope, excluded).

### F5 — runner lifetime + operation/result/stream scopes (file-local)

- **Contract + variation.** The runner builds every state once (all three
entry spellings — class, instance, singleton factory — arrive resolved, so
one point sees them all and marks each managed), then binds scope + states
around: the operation (parse/validate/execute/middleware/ordinary
exceptions), result collection (upstream runs it AFTER sync teardown and,
async, inside an early-return scope plus after a completed one — without
this scope an extension payload answers for no operation), the
streaming-result hook (already covered by the operation scope; bound anyway
so the contract is the runner's, not one call ordering's), every streamed
resumption (F4). States live exactly as long as the runner (leases on
weakrefs — the request dies with the runner, not with the last copied
context). Legitimate variation: which scopes exist — here.
- **Sites + roles.** *Definitions*: statement 42 (runner + 8 scope
methods; `__init__` builds, `_scope` settles, six binders bind).
*Consumers*: [schema][schema]`::create_extensions_runner` (builds) +
`::_stream` (wraps; passes non-package runners through — C15 proves the
boundary). *Oracles*: collection-after-teardown rows + stream-hook rows in
[test-operation-state][test-operation-state]; `_ResumedStream` passthrough
row in `tests/test_schema.py`. *Projections*: runner docstring (full
lifetime + scope list), schema factory docstring (one-point rationale),
`_stream` docstring (narrowest-seam rationale).
- **Challenges.** C14 → 1 per method here (the stale-payload disclosure
returns without them — why they exist); C15 → 0 here (pass-through at
schema).
- **Owner + lifetime.** `DjangoExtensionsRunner` (existing owner by
responsibility: the only central point seeing resolved list + context
together without re-invoking a factory). Lifetime: states owned strongly
by the runner; bindings are leases closed on unwind.
- **Migration.** None.
- **Distinct behavior.** Post-teardown collection binding stays (the
otherwise-unbound payload); stream-result double coverage stays
(contract-over-ordering); non-runner pass-through stays (subclass chains).
- **Behavioral proof.** `execution-verified` (probe census + consumer
edge); `static-reviewed` (scope bodies + collection/stream rows). Rejects
"collection can read off the extension" (stale payload — C14) and "the
runner wraps foreign runners" (pass-through — C15).
- **Structural gate.** Pre-existing collection/stream/passthrough rows —
no new gate owed.
- **Coupling.** None.
- **Freshness.** Target as in F1, [schema][schema] as in F1.

### R1 — `awaitable-refusal-and-disposal` (indexed family: checked, not a member)

Considered: the plan item names it (the querysets F1 trace posited "a
rejected awaitable must also be reported to the operation-state extension
before it is disposed"). No surface: 0 `isawaitable` /
`_dispose_sync_awaitable` / `SyncMisuseError` tokens in the target (probe
§4) — disposal calls no reporting hook anywhere, and this file defines no
refusal. Contract difference: the family owns "detect, dispose, refuse
with a typed error at the sync boundary"; this file owns "bind one state
per operation" — a reporting edge would be a NEW consumer call, not a
second definition. Trigger to reconsider: an `isawaitable` read (or any
disposal call) appearing in this module — then it becomes a consumer row.
Durable home: this artifact (nothing in the target states a refusal
because there is none to state).

### R2 — `one-sync-boundary` (indexed family: checked, not a member)

Considered: the plan item names it ("check don't inherit"). No surface: 0
`run_in_one_sync_boundary` / `sync_to_async` calls (probe §4); the target
performs no ORM execution inside any binding (ContextVar sets, lease
stores, token resets only), and its hooks are scope wrappers rather than
sync/async twin bodies. Contract difference: the family owns "ORM work
must not interleave with awaits inside a transaction"; this file's rule is
"hold one operation bound while its scopes run" with no executor work of
its own. Trigger to reconsider: queryset execution (or any ORM touch)
appearing in this module. Durable home: this artifact.

### J1 — type-identity predicates (refused shared form, recorded here)

Three `type()`-first spellings: `_is_operation_bound` (`issubclass(type,
_OperationBoundExtension)` — whose state the runner binds),
`_declared_operation_mode` (`type(...) is _OperationModeMarker` — what the
chain declares), [schema][schema]`::_is_extension` (+
`_is_resolvable_extension_entry` — what is admitted/refused). Considered:
one shared "hostile-`__class__`" predicate. Refused: distinct contracts
with separate reasons to change — posit admitting a `__class__`-claimant
as operation-bound → only `_is_operation_bound` moves; posit accepting
marker subclasses (or a consumer `mode` attribute) → only
`_declared_operation_mode` moves (its docstring already states the
exact-type reason); posit changing admission → only schema moves (C7
proves the split per axis). A shared helper would couple the runner's
binding population to the schema's admission population across inverse
failure modes. Trigger: a FOURTH identity predicate with the same
hostile-`__class__` rationale — then the rationale (not the predicates)
becomes a family. Durable home: each predicate's docstring (all three
already state their own reason) + this finding. No new index row.

### J2 — error/resource enforcement unification (refused shared form, corroborated)

The error-policy artifact's J1 refused unifying the two enforcement halves
(opposite lifecycle positions, distinct policies/hooks). Corroborated from
this side: this file holds mechanism BOTH use and policy NEITHER does —
there is no third site to unify, and the composition edges (subclass +
refusal + state factory + policy authority elsewhere) are already the DRY
answer. No independent trigger here; the trigger rides the error-policy
finding. Durable home: that finding + this sentence. No new index row.

### Checked non-memberships (absence probe-verified, no family named)

- `sealed-execution-queryset`: 0 `QuerySet`/`queryset`/`seal` tokens —
the target rewrites no row source and seals nothing.
- `typed-rejection-value-tail`: 0 `describe_value` — the two
`ConfigurationError` raises interpolate only `type(...).__name__`, no
`got` tail; no contract source extends the tail rule to a construction
refusal naming its own kind.
- `logger-single-sourcing`: 0 `logger`/`getLogger` — the target emits no
log record (every failure path raises, returns `None`, or unwinds; the
degrades live in the consumers).
- `soft-dependency-require-guard`: 0 `require_*` — every import is stdlib,
hard upstream, or first-party.
- `subsystem-clear-lifecycle`: 0 `register_subsystem_clear` — operation
state is per-runner by construction and needs no clear bus.
- Reconsideration trigger (all): the named token appearing in this module
makes it a consumer row, never silently a member. Durable home: this
section + probe §4.

## Defects

None. Every claim checked while tracing held: the assignment-records-nothing
window (no hook between assignment loop and the factory — schema factory
docstring states it); one-state-per-spelling coverage (selection sees all
three resolved forms + marks each); copied-context reads-nothing at scope
end (close-first) and at runner death (weakref); double-construction
refused before any policy is touched; stream frames bound per drive in the
driving task with between-frames enclosing-or-nothing; mode carried from
the chain, never sampled; non-package runners passed through. The axis-6
sweep finds no member lacking a guard its contract requires (consumer
non-wrapping and raw-schema limits are contract-sourced, Matrix axis 6).
(Static review only beyond the probe — no shared-tree pytest per item
rules; oracle bodies cited above are `static-reviewed`.)

- None additional (Worker 2): axis-6 re-sweep finds no member lacking
  a guard its contract requires; no other non-duplication defect found.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
absence/edge censuses, command in `### Challenges`) already ran green
against the shared tree; they mutate no source, open no database, and
import no Django, so no workspace copy was owed and no `__file__`/DB
`NAME` record applies. No pytest was run in the shared tree, per item
rules; oracle bodies are `static-reviewed`. No `execution-deferred`
items. No `FAKESHOP_SHARDED` or Postgres cell is owed: the target's code
path reaches no database, alias, or dialect decision
(`inapplicable by construction` — ContextVar/lease/token binding plus a
`schema` attribute read guarded to `False`; the only settings-adjacent
surface is none — the target imports no settings).

## Judgment

Backstop discharged: 43/43 `ast.Module.body` members enumerated plus all
8 class bodies (5/3/2/7/5/7/8/9), 17 challenges run, every rule terminating
in the one new family it owns (F1 `operation-bound-extension-mechanism`
— mechanism-vs-override split re-derived fresh, C1–C4 count 1), a
file-local record with its proving challenge (F2–F5, C5–C15 count 1
except boundary-proving C15 at 0), an indexed check with no surface (R1,
R2 — C16/C17 at 0, do not inherit), or a recorded rejection with
difference + trigger + home (J1, J2). No consolidation owed (composition
is already by name on every edge), no defect found, no new family beyond
F1, no pending execution. Zero-edit result is legitimate.

Worker 0 owes: one `## Families` item + five `## Responsibility index`
rows (exact lines below); tick only the file item:

```text
- [ ] Family `operation-bound-extension-mechanism` — [dry-rule-operation-bound-extension-mechanism.md](dry-rule-operation-bound-extension-mechanism.md)
```

```text
| `operation-bound-extension-mechanism` | `django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension` | `django_strawberry_framework/extensions/operation_state.py`, `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/extensions/error_policy.py`, `django_strawberry_framework/extensions/resource_policy.py`, `django_strawberry_framework/optimizer/extension.py` | Family `operation-bound-extension-mechanism` | open |
| Runner scope + nested fact + executor mode | `django_strawberry_framework/extensions/operation_state.py::_RunnerScope` (+ `::operation_is_nested`, `::_declared_operation_mode`) | `django_strawberry_framework/extensions/operation_state.py` | File `extensions/operation_state.py` | file-local |
| Bind/unbind lifecycle + dual-protocol adapters | `django_strawberry_framework/extensions/operation_state.py::_bind` (+ `::_unbind`, `::_BoundScope`) | `django_strawberry_framework/extensions/operation_state.py` | File `extensions/operation_state.py` | file-local |
| Streamed resumption + resume registrar | `django_strawberry_framework/extensions/operation_state.py::OperationState.rebind_on_resume` (+ `::DjangoExtensionsRunner.resumed`, `::_ResumedStream`) | `django_strawberry_framework/extensions/operation_state.py` | File `extensions/operation_state.py` | file-local |
| Runner lifetime + operation/result/stream scopes | `django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner` | `django_strawberry_framework/extensions/operation_state.py` | File `extensions/operation_state.py` | file-local |
```

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `940f2ea456053eb72cae0e51fbc7d88b1c8241de`:
`git diff <baseline> -- django_strawberry_framework/extensions/operation_state.py`
empty (0 bytes); working blob
`b2674a22d2dfd58ff97c51a02e16068bb22032e9` equals the item baseline, the
cycle-baseline member, and `HEAD:` — target CLEAN, so no hunk attribution
was owed. The artifact itself
(`docs/dry/dry-file-extensions__operation_state.md`) is a new untracked
file, the item's only output besides scratch. No `uv run ruff format .` /
`ruff check` run (no tracked `.py` edits; artifact is `.md` only; probe is
untracked scratch). No shared-tree pytest run. Untracked scratch created
(not tracked changes): the read-only probe
`docs/dry/temp-tests/dry-file-extensions__operation_state/probe_w1.py`
(`W1 PROBE: ALL OK`, 36 checks; no source mutation, no Django import, no
DB, no shared-tree pytest). Concurrent dirt listed in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus the
other untracked `dry-file-*.md` artifacts were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no
row from this item. No commit.

## Independent verification (Worker 2)

Expectation-first trace, recorded here before reconciling with
`## Findings`. Method: full target read (922 lines); my own AST
census; reads of all four consumer extensions, the schema factory
plus `_stream` plus admission predicates, the three primitives, the
oracle head plus seam rows; my own absence greps; one re-run of the
read-only probe. Never opened another worker's `worker-memory/`.

### Own trace (sites, roles, counts, owners)

| Rule I derive | Sites + roles | Count per change | Owner I choose |
|---|---|---|---|
| Bound-extension carrier + managed set + refusal + compat setter + selection | definitions: target stmts 16, 17, 25-32; consumers: 4 subclasses plus [schema][schema]`::create_extensions_runner`; oracles: seam rows plus live matrices | 1 here per change (new kind: new declaration; base reword: base only; compat branch: setter only; wrap-consumers: selection only) | target `[extensions-operation-state][extensions-operation-state]` `::_OperationBoundExtension` |
| Runner scope + nested + executor mode | definitions: target stmts 15, 18, 21-24 plus runner `_scope`; readers compose by name ([utils-execution-mode][utils-execution-mode], [optimizer-extension][optimizer-extension]) | 1 here per change (settle-at-construction, sample-ambient, accept-subclasses each move one site; mode readers untouched) | target (settle + chain transport); bind primitive stays at [utils-execution-mode][utils-execution-mode] |
| Bind/unbind lifecycle + dual adapters | definitions: target stmts 18, 33-40; consumers: runner scope methods (same file) | 1 here per change (order, tolerance, reentry each move one site; one primitive under both adapters) | target |
| Streamed resumption + resume registrar | definitions: target stmts 14-registry, 19, 20, 38, 41; consumer: exactly one registration call (resource budget) | 1 here per change (adopt path, per-drive, handoff shape; consumer call follows by name) | target (`OperationState` registry + registrar + stream wrapper) |
| Runner lifetime + operation/result/stream scopes | definitions: target stmt 42; consumers: schema factory + `_stream` (pass-through for foreign runners: 0 here) | 1 per scope method here; 0 at schema for the pass-through | target `DjangoExtensionsRunner` |
| 4 subclass overrides | debug: refusal string + `_DebugOperationState` factory; optimizer: refusal + `_OptimizerOperationState`; resource: refusal only (base `OperationState`, no factory); error policy: neither (inherits both) | rewording base refusal moves base only; rewording one consumer moves that consumer only | declarations, never copies |

Reconciliation vs W1: full agreement on every row (F1 new family,
F2-F5 file-local, R1/R2 checked-not-members, J1/J2 refused). No
difference in sites, roles, counts, or owners. One non-blocking
observation only (see Freshness below): three read inputs carry no
blob, which the holding family item will repair.

### Enumeration (member-by-member vs my own count)

My AST census: **43 module members**, kind sequence `Expr`,
`ImportFrom`, `Import`, 10x `ImportFrom`, `Assign`, 2x `ClassDef`,
4x `AnnAssign`, `FunctionDef`, `ClassDef`, 9x `FunctionDef`,
`ClassDef`, `FunctionDef`, `ClassDef`, 6x `FunctionDef`, 3x
`ClassDef` — identical to the probe's sequence. Class bodies:
`OperationState` 5, `_RunnerScope` 3, `_OperationModeMarker` 2,
`_OperationBoundExtension` 7 (property getter + setter count as
two), `_Binding` 5, `_BoundScope` 7, `_ResumedStream` 8,
`DjangoExtensionsRunner` 9 — identical. Every member lands where
W1 puts it: 0 prose, 1-12 bindings, 13 covered by the existing
`extensions-helper-state-privacy-omission` index row (no new row),
14 registry/state halves F4/F5, 15/18/21-24 F2, 16/17/25-32 F1,
33-40 F3, 41 F4, 42 F5. No member unassigned; no challenge ends
outside a family row, a file-local row, or a rejection.

### Counts, roles, oracles

Counts endorsed: C1-C15 at 1 each here (C15 at 0 at schema, proving
the boundary), C16/C17 at 0 (no surface — my own greps: 0 hits for
every awaitable, boundary, queryset, tail, logger, soft-dep, and
clear-bus token). Roles endorsed: definitions all in-target;
consumers compose by name (four subclass declarations read at
[extensions-debug][extensions-debug], [extensions-error-policy][extensions-error-policy],
[extensions-resource-policy][extensions-resource-policy],
[optimizer-extension][optimizer-extension]; schema builds + wraps by
name). Oracles independent: 46 `test_` functions (my count matches)
drive the seams (`execution_context` assignment, `_operation_state`
reads, `schema.execute`, stream drives) and assert disclosure
outcomes; the two `_OPERATION_CARRIERS` calls in the one lifecycle
row assert the authority's own settle-once contract, never derive an
expectation from the owner — no rewrite violation. Projections
(docstrings, spec-050 D14/D19, GLOSSARY anchor, leaf privacy prose)
listed, never counted.

### Equivalence (principle 8) + zero-edit

No consolidation, no production edit, no observable behavior to
preserve-or-change: principle 8 applies vacuously. Item-scoped diff
re-checked by me: `git diff` vs the item baseline over the target
is empty (0 bytes); working blob `b2674a22…` equals `HEAD:` blob at
pinned `HEAD 9031cb3d`. Coverage validated: 43/43 members plus all
8 class bodies assigned; assignment validated: the one cross-file
rule (F1) names its holding family, F2-F5 are file-local with
proving challenges, R1/R2 are checked non-members, J1/J2 carry
difference + trigger + home. Ruling on the NEW family
`operation-bound-extension-mechanism`: JUSTIFIED, not over-split.
Carrier, managed set, refusal, compat setter, and selection are one
change obligation (every posited change moves exactly one site;
consumers follow by declaration). Splitting further would cut one
lifecycle into four pieces with the same owner; folding F2-F5 in
would merge distinct reasons to change (settle timing vs bind order
vs resume handoff vs scope list). One rule, one owner: this file is
the narrowest cohesive owner every consumer can depend on without a
reversed dependency (one-way edges re-verified: none of the three
primitives imports it back; the schema already depends downward).

### Rejections, fingerprints, gates, pending, coupling

R1/R2: contract differences + triggers present; absences re-verified
by my own greps (all 0). J1: all three `type()`-first spellings
confirmed with distinct contracts and per-axis split (C7 moves the
marker read alone); trigger (fourth same-rationale predicate)
recorded. J2: corroboration of the error-policy finding from this
side; trigger rides that finding. Freshness re-hashed by me — all
match: target `b2674a22…`, [schema][schema] `2f727321…`,
[extensions-debug][extensions-debug] `bf25c146…`,
[extensions-error-policy][extensions-error-policy] `baea073f…`,
[extensions-resource-policy][extensions-resource-policy] `52084078…`,
[optimizer-extension][optimizer-extension] `49667a93…`,
[utils-private-state][utils-private-state] `08088b82…`,
[utils-execution-mode][utils-execution-mode] `9805cdaf…`,
[test-operation-state][test-operation-state] `b3a574b1…`,
[optimizer-context][optimizer-context] `3d8dcfdf…`,
[resource-policy][resource-policy] `647133d2…`; population still 117
`.py`. Observation (non-blocking, not a defect): three read inputs
([utils-operation-lease][utils-operation-lease],
[exceptions][exceptions], [extensions-init][extensions-init]) carry no
blob here; the whole-package sweep statement covers the
second-definition search, and the holding family item re-sweeps and
re-fingerprints everything, so this self-heals there. Gates: the
pre-existing seam rows plus live matrices are the gates; the
negative control is honestly stated-not-run (a behavior-preserving
hand copy passes every behavioral oracle and fails only the import
census), which is exactly what DRY.md predicts for a correct copy —
no new gate is owed by a file item. `## Pending execution`: absent,
correctly — the probe (36 checks, re-ran `ALL OK`) mutates nothing,
opens no database, imports no Django; `inapplicable by construction`
holds (ContextVar/lease/token binding only; the one schema import is
deferred and guarded; no settings, ORM, alias, or dialect surface),
so no sharded or Postgres cell is owed. Coupling: `None` marked on
each finding — explicit, accepted.

### AGENTS.md prose check

No `path:NN` refs (grepped: 0); citations are `path::Symbol` plus
the existing reference-style link scaffold, whose 10 canonical
groups are intact and which I add no new ids to. No process
provenance, no commit, no test-tier violation (zero-edit; oracles
cited `static-reviewed`). Scratch lives at
`docs/dry/temp-tests/dry-file-extensions__operation_state/` as
required. Concurrent dirt (`connection.py` hunk, test dirt, other
artifacts, plan file) untouched; the artifact's own untracked status
is the item's expected output. No shared-tree pytest run (correct
per item rules). No `.py` edits, so the ruff format/check pair is a
no-op for this item and was not run, lest it touch concurrent dirt
(same rationale as Worker 1).

### Defects (Worker 2)

None. The axis-6 sweep holds: consumer non-wrapping is deliberate
and contract-sourced, raw-schema shared-instance limits are a
documented limitation, the skipped-constructor shape is refused by
`_carrier`, double construction is refused before any policy is
touched, close-before-reset and per-drive binding are as stated.

Worker 0 owes exactly the lines in `## Judgment` (one `## Families`
item + five `## Responsibility index` rows); tick only the file item
`extensions/operation_state.py`. Verdict: `Status: verified`, no
pending execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[utils-operation-lease]: ../../django_strawberry_framework/utils/operation_lease.py
[utils-private-state]: ../../django_strawberry_framework/utils/private_state.py

<!-- tests/ -->
[test-operation-state]: ../../tests/extensions/test_operation_state.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
