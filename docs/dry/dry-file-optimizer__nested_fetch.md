# DRY review: `optimizer/nested_fetch.py`

Status: verified
Run: 0.0.15 2026-09-22-5

## System trace

Target `django_strawberry_framework/optimizer/nested_fetch.py` is the
nested-connection fetch-strategy seam. It owns four rules: strategy
SELECTION (which backend fetches: the `StrategySelection` alias, the
`_builtin_strategies` registry, the `resolve_strategy` resolver, the
`WINDOWED_STRATEGY` / `AUTO_STRATEGY` singletons, the `active_strategy`
runtime read); the recognized-fetch queryset SKELETON
(`RecognizedFetchQuerySet`: clone-carried spec slot, planned-window
signature capture at `rebind`, recognized-rows-or-windowed-body
`_fetch_all`); the strategy PLANNING seam (`NestedConnectionRequest`
record, `NestedConnectionStrategy` protocol, `attach_windowed_prefetch`
floor, the windowed + auto backends, the `to_attr` row contract); and
the strategy-independent unwindowable-child-queryset CLASSIFIER.
Three backends implement the protocol (windowed + auto here, lateral in
`optimizer/lateral_fetch.py`); one planner builds the request
(`optimizer/nested_planner.py::plan_connection_relation`); one reader
consumes the rows (`connection.py::_resolve_from_window`); three gates
compose the classifier (planner refusal, two fetch-time fallbacks).

Trace subject is the HEAD bytes (blob
`4d8d37a7f52cf94d2916f17db3a8a21393e28d57`, 488 lines; HEAD `5ee86193`
confirmed at start and end). Worktree `29ce5201` carries the concurrent
hunt's +23/-5 confined to `resolve_strategy` (both `isinstance` gates
rewritten plus docstring; diff-verified, hash stable across the task) —
read for attribution only, never for evidence, never edited. Dirty
connected files (`optimizer/nested_planner.py`, `optimizer/hints.py`,
`optimizer/join_taxonomy.py`, `utils/connections.py`, `connection.py`,
`utils/querysets.py`) and both hunt-dirtied oracle files were likewise
read at HEAD bytes only. The main checkout was never touched.

Converge / diverge on fresh evidence. CONVERGE with run-5
`nested-connection-strategy-selection` (F1): `resolve_strategy` confirmed
as the selection owner — single alias, single registry, single resolver,
every seam composing by name, no second of any found in a package-wide
HEAD census. CONVERGE with the lateral / single-parent F-D skeleton
naming (F2, adopted). DIVERGE-narrowed from lateral F-F's lumped seam
(F3, name adopted): selection and planning vary independently (a new
builtin name moves the registry; a new window parameter moves the
request + floor), so the planning side is its own family and selection
stays in the run-5 family. The two prior items never drew their shared
boundary (neither cites the other), so this split is boundary-drawing on
fresh owner-side evidence, not re-litigation of either verified item.
NEW F4 homes the classifier, which the verified querysets F4 separated
from the seal family but never homed.

"Walker" prose: the target's docstrings say "walker" where HEAD's
executing caller is the planner (the walker delegates
`plan_connection_relation` to `optimizer/nested_planner.py`, and
`active_strategy`'s sole production caller is the planner's
`_select_nested_strategy`). "Walker" names the walk subsystem throughout;
every described behavior holds at the planner bodies. Read that way
below.

Zero-edit file item: no consolidation, no production edits, no permanent
tests. One read-only pure-Python mechanics probe under the item scope
dir (no Django, no package import); no pytest (justified under
`## Pending execution`).

## Verification

### Matrix

Mechanism census ran over a disposable `git archive HEAD` tree of the
package, plus HEAD-oracle and doc reads listed per finding.

1. Cross-flavor policy mirroring — discharged via F1 + R4 + R15. The
   13-file HEAD consumer census (conf, keyset, `_context`, extension,
   hints, lateral_fetch, nested_fetch, nested_planner,
   single_parent_fetch, walker, utils/connections, utils/querysets,
   views) shows no sibling flavor (mutations, forms, rest_framework,
   filters, orders) owning a fetch-strategy surface. The two
   cross-flavor touchpoints are a cited ladder split (views, R4) and a
   shared `"auto"` token with zero shared mechanism (R15).
2. Sync/async twins — discharged by absence with reason. The target has
   zero `async def` (census); lateral, single_parent, and walker
   likewise have none. The seam is plan-time plus synchronous fetch;
   no twin surface exists to drift.
3. Derived rather than repeated knowledge — discharged via F1 + F2 +
   F3. Registry keys vs strategy `name` attrs are two literal spellings
   of one vocabulary inside one family (derive-vs-duplicate is F1's
   family-item question, not a second definition). The floor threads all
   eight window parameters into `apply_window_pagination` by parameter
   (verified against the plans signature — composed, not re-derived).
   The unknown-name message tail derives from `sorted(registry)`.
   Signature capture and re-derivation share one lateral-owned helper.
   No fact has two derivations.
4. Inverse / round-trip pairs — discharged via F2 + F3. Rebind-capture
   vs recognizer-compare share one grammar with an explicit `None`
   fail-closed arm on BOTH recognizers (verified fresh). Strategy-plan
   `True`/`False` vs planner merge/discard is the enforced verdict
   pair. `resolve_strategy` has no inverse (instances pass through;
   nothing unresolves) — correctly absent, not a missing half.
5. Contracts restated in another medium — discharged per finding.
   Oracles: the `test_nested_fetch.py` HEAD matrix (registry, selection,
   hostile-dunder, frame, classifier rows), `_builders.py`, the live
   auto / fastpath suites, hint + extension oracles. Projections:
   target + consumer docstrings, the GLOSSARY strategy paragraph, the
   conf + keyset + views citations. Listed, never counted; no restated
   definition found.
6. Enforcement by omission — discharged with contract sources. Three
   protocol backends plus the open consumer-instance seam: the
   windowed-only single-parent wrap is documented v1 scope (lateral
   owns the clean shape at plan time); the lateral-only visibility
   WHERE is documented; auto delegates by design; the `False` refusal
   arm is planner-handled and live-pinned (refusing-default row). Both
   skeleton subclasses implement `_fetch_recognized_rows` (base raises;
   zero direct constructions by census). All three classifier gates
   degrade (planner whole-refusal vs fetch fallback — verified-separate
   per querysets F4). No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast` over the HEAD bytes — 27 `ast.Module.body` nodes (1
module docstring, 13 imports, 13 named members). Every named member
lands below; split members cite both homes.

| # | Member | Home |
|---|---|---|
| 1 | `unwindowable_child_queryset_reason` | F4 |
| 2 | `RecognizedFetchQuerySet` (`_clone`, `rebind`, `_fetch_recognized_rows`, `_fetch_all`, `_dst_spec_attr`, `_dst_window_signature`) | F2 |
| 3 | `NestedConnectionRequest` (14 fields, `__post_init__`) | F3 (+ R11 twin) |
| 4 | `NestedConnectionStrategy` (`name`, `plan`) | F3 |
| 5 | `StrategySelection` | F1 |
| 6 | `attach_windowed_prefetch` | F3 |
| 7 | `WindowedPrefetchStrategy` | `name` to F1; `plan` to F3 |
| 8 | `WINDOWED_STRATEGY` | F1 |
| 9 | `AutoNestedConnectionStrategy` | `name` to F1; `plan` to F3 |
| 10 | `AUTO_STRATEGY` | F1 |
| 11 | `_builtin_strategies` | F1 |
| 12 | `resolve_strategy` | F1 |
| 13 | `active_strategy` | F1 |
| 14 | module docstring + 13 imports (incl. 5 lazy cycle-breaks) | L1 |

13/13 named members homed; 0 unassigned.

### Challenges

Counts are authoritative definitions only; consumers, oracles, and
projections that also move are listed, not counted.

| Rule | Change posited | Definitions forced | Count |
|---|---|---|---|
| F1 selection | fourth builtin name | registry literal + resolver + alias comment (co-located) | 1 |
| F1 selection | reject instances (posture change) | `resolve_strategy` duck-check arm | 1 |
| F1 selection | default windowed to auto | conf reader (resolve delegates) | 1 |
| F1 selection | drop the per-field seam | hint field + factory + planner read (consumers of one resolver) | 1 |
| F1 selection | rename a builtin | registry key + `name` attr + message/prose (one family) | 1 |
| F2 skeleton | third backend subclass | new adapter only; skeleton untouched | 1 |
| F2 skeleton | new clone-carried attr | `_clone` + `rebind` (co-located) | 1 |
| F2 skeleton | drop the signature | `rebind` capture + 2 recognizer compares (consumers) | 1 |
| F3 seam | new window parameter | request field + floor threading (+ composed plans owner) | 1 |
| F3 seam | fourth backend | one protocol implementation | 1 |
| F3 seam | new carried row attribute | plans constants + 3 producer adapters + connection reader | 1 |
| F4 classifier | sixth shape / dropped reason / renamed reason | classifier (+ oracle matrix) | 1 |
| F1 default | `active_strategy` default to setting | `active_strategy` only; extension fallback independent (R3) | 1 |

## Findings

### F1 — Nested-connection strategy selection (EXISTING family `nested-connection-strategy-selection`, CONVERGE)

Contract: one alias (`StrategySelection = str |
NestedConnectionStrategy`) plus one lazily-assembled immutable registry
(`_builtin_strategies`: `MappingProxyType`, `@cache`, lateral imported
behind the function to break the cycle) plus one resolver
(`resolve_strategy`: registered name, `"auto"` to the stable singleton,
instance pass-through by duck-typed `plan`, `None` delegating to the
`NESTED_CONNECTION_STRATEGY` setting) plus the shared singletons
(`WINDOWED_STRATEGY`, `AUTO_STRATEGY`, `LATERAL_STRATEGY` beside their
backends) plus the runtime read (`active_strategy`: frame value or
hard windowed default). Hostile dunders degrade to typed
`ConfigurationError` via base-`str`-slot reads, a linear no-hash scan,
an absorbing `plan` read, and guarded renderers. Varies over builtin
vocabulary, validation posture, default, and per-field / per-instance /
unmanaged seams.

Sites and roles: definition `optimizer/nested_fetch.py` (alias,
registry, resolver, singletons, both `name` attrs, runtime read; HEAD
`4d8d37a7`). Consumers composing by name: `optimizer/hints.py` (field,
factory, `_require_strategy` delegation), `optimizer/extension.py`
(kwarg annotation + two resolve calls + frame publish),
`optimizer/nested_planner.py::_select_nested_strategy` (re-resolution +
`active_strategy`),
`optimizer/lateral_fetch.py` (`LATERAL_STRATEGY` registry value,
`WINDOWED_STRATEGY` downgrade),
`conf.py::nested_connection_strategy_setting` (the thin setting read).
Oracles: the registry / resolve / hostile / frame rows in
`tests/optimizer/test_nested_fetch.py` (incl. the pinned class-exclusion
and falsey-strategy rows), `_builders.py`, the live auto suite, hint +
extension oracles. Projections: the alias + resolver + module docstrings,
GLOSSARY strategy prose, the views ladder citation, the keyset mention.

Challenges: all five selection rows count 1; no second registry,
resolver, or alias exists (package-wide HEAD census). Owner:
`resolve_strategy` beside the alias and the protocol — the narrowest
module every consumer (hints, extension, planner, conf direction)
already imports; dependency direction confirms (nothing valid sits
below it). No stored derivation beyond the `@cache`d immutable
registry (owner the registry function; lifetime process; invalidation
never — values are module singletons).

Migration: none (naming only). Distinct behavior: the `None` arms
differ per seam by design (resolve-None reads the setting; hint
`strategy(None)` rejects — hints F1; extension-fallback resolves —
R3). The registry keys vs `name` attrs dual spelling and the
non-`runtime_checkable` duck-typed instance seam (pinned by the
RecordingStrategy oracle) are F1-internal sub-rules for the family
item. Behavioral proof: `static-reviewed` (naming only; the family
item owes execution where it consolidates). Structural gate (for the
family item): a package-wide singularity census — exactly one
`StrategySelection` alias, one builtin registry, one resolver;
negative control is a behavior-preserving hand copy of the resolver,
which passes every behavior oracle and fails the census. Coupling:
shares the two strategy classes with F3 (`name` here, `plan` there).
Freshness: target HEAD `4d8d37a7` (worktree `29ce5201` hunt dirt in
`resolve_strategy` NOT traced); hints HEAD `da46ef89`, extension
`49667a93`, nested_planner HEAD `b4dfd4a6`, lateral `db1ea315`, conf
`c6ad46aa`, test_nested_fetch HEAD `7fbd957b` (worktree dirt NOT
traced), auto live suite `ca9fea06`, GLOSSARY `d3ef357c`.

### F2 — Recognized-fetch queryset skeleton (ADOPTED family `recognized-fetch-queryset-skeleton`, CONVERGE)

Contract: the shared execution skeleton for a windowed-prefetch
queryset with a recognized fast path — clone-surviving per-strategy
spec slot (`_dst_spec_attr` + `_clone` carry), planned-window signature
capture at `rebind` (`window_predicate_signature` read off the windowed
body before prefetch appends `__in`; `None` fails closed), and
recognized-rows-or-windowed-body `_fetch_all` (plus the nested-prefetch
pass the superclass call still performs). Varies over backend count,
carried clone state, and signature grammar (owned laterally, composed
here).

Sites and roles: definition `optimizer/nested_fetch.py`
(`RecognizedFetchQuerySet` + all four methods + both attrs; HEAD
`4d8d37a7`). Adapters: `optimizer/lateral_fetch.py::LateralQuerySet`
(spec slot + `_fetch_lateral_rows`) and
`optimizer/single_parent_fetch.py::SingleParentWindowQuerySet`
(spec slot + `_fetch_single_parent_rows`) — the ONLY two subclasses
and the ONLY two `rebind` callers (census), each reached exclusively
through a spec-guarded `wrap`. Consumers of the capture helper by
name (lateral-owned vocabulary, not this family). Oracles:
clone-carry + nested-prefetch rows, both recognizers' signature-mismatch
downgrade rows, the live fastpath suite. Projections: the skeleton +
subclass docstrings (each states the shared contract).

Challenges: all three skeleton rows count 1; the two recognizers prove
different queries (lateral SQL vs pristine `LIMIT` re-query) — sharing
stops at the skeleton by design (verified R-c / R-d; triggers
re-checked in R13 + R14, not met). The rebind safety premise (plain
`QuerySet` only — a class swap would erase subclass `_clone` state) is
enforced at the two spec builders, verified-separate. Owner: the
skeleton class — the narrowest module both backends already import.
Lifetime: per-queryset clone chain (`_clone` carry), per-wrap signature
capture; no cross-request state. Migration: none. Behavioral proof:
`static-reviewed`. Structural gate (for the family item): a subclass
census — every `RecognizedFetchQuerySet` subclass defines
`_dst_spec_attr` and `_fetch_recognized_rows` and never overrides
`_fetch_all`; negative control is a subclass with a direct `_fetch_all`
override, behavior-correct but census-failing. Coupling: wraps compose
`rebind` (R12); recognizers compose F4 as shape gates. Freshness:
target HEAD `4d8d37a7`; lateral `db1ea315`, single_parent `e995270a`,
fastpath live suite `492fac73`.

### F3 — Nested-fetch strategy seam (ADOPTED family `nested-fetch-strategy-seam`, DIVERGE-narrowed)

Contract: the plan-time seam between the planner and the backends — the
`NestedConnectionRequest` frozen record (built only after every
strategy-independent refusal arm; `to_attr` / `lookup` attach contract;
probe/count exclusion enforced in `__post_init__` through the shared
`assert_window_fetch_mode_for`), the `NestedConnectionStrategy`
protocol (`plan` attaches directives and returns `True`; `False` leaves
the selection unplanned with no leakage into the parent plan), the
`attach_windowed_prefetch` floor (all eight window parameters threaded
into `apply_window_pagination`, carried as one `to_attr` `Prefetch`;
always `True`), the two here-homed backends (windowed: bare floor or
single-parent-wrapped floor; auto: backend-neutral delegation to the
lateral plan), and the `to_attr` row contract (ordered model instances
carrying `_dst_row_number`, plus `_dst_total_count` when requested).
Varies over window parameters, backend count, attach shape, and carried
attributes.

Sites and roles: definitions `optimizer/nested_fetch.py` (record,
protocol, floor, both backends' `plan`; HEAD `4d8d37a7`).
Builder/enforcer: `optimizer/nested_planner.py` (sole
`NestedConnectionRequest(` site — census; isolated candidate plan,
merge-only-on-`True`, metadata absorb on success, per-key advisory).
Member backend: `optimizer/lateral_fetch.py::LateralPrefetchStrategy`
(spec-or-downgrade, shared floor with lateral wrap).
Row producers: the floor's annotations (plans-owned), lateral
`_instantiate_row`, single-parent synthesis — all composing the
plans-owned `WINDOW_*` names by name. Row reader:
`connection.py::_resolve_from_window`. Fetch-mode owner:
`utils/connections.py` (composed by both `__post_init__` twins — R11).
Oracles: request / floor / backend rows in `test_nested_fetch.py`,
`_builders.py::nested_connection_request`, the advisory suite (request
construction), the auto + fastpath live suites, connection fast-path
oracles. Projections: module + protocol + floor + backend docstrings,
the request-field comments, GLOSSARY prose.

Challenges: all three seam rows count 1. A new window parameter moves
the record + floor (+ the composed plans owner — listed, not counted);
producers inherit it through the floor without moving. A new backend is
one protocol implementation. A new carried attribute moves the
plans-owned name + three producer adapters + the reader — one name
definition, adapters by mechanism (verified R-c). The single-builder /
triple-floor-call-site / triple-`plan`-implementer censuses confirm no
second seam. Owner: `NestedConnectionStrategy` — the contract every
backend implements and the planner enforces; the narrowest symbol all
legitimate consumers already import (the family item may re-home to
the floor on mechanism weight; recorded here either way). No stored
derivation (request is a frozen value; plans merge forward). Migration:
none. Behavioral proof: `static-reviewed`. Structural gate (for the
family item): a floor-threading census — every `apply_window_pagination`
parameter threaded by the floor — plus a name-composition census (no
literal `_dst_*` in producers); negative controls are a param-dropping
floor and a literal-spelling producer, each behavior-green on old
oracles and census-red. Coupling: shares the strategy classes with F1;
the row contract's names live in plans (composed, never re-owned).
Freshness: target HEAD `4d8d37a7`; nested_planner HEAD `b4dfd4a6`,
lateral `db1ea315`, single_parent `e995270a`, plans `cce98531`,
utils/connections HEAD `f549389e`, connection HEAD `4894f90f` (row-attr
sites read; full body for the family item), builders `567defa9`,
advisory suite HEAD `beee6b7d` (worktree dirt NOT traced).

### F4 — Unwindowable-child-queryset classification (NEW family `unwindowable-child-queryset-classification`, open)

Contract: the strategy-independent safety classifier — five consumer-hook
queryset shapes no fetch strategy can window safely (`sliced`,
`select_for_update`, `combined`, `distinct`, `values`, each with its
stated crash-or-silently-wrong reason) mapped to stable reason strings,
`None` for a plain windowable queryset (custom `ModelIterable`
subclasses windowable; non-type iterables `values`). The classifier
never rejects; callers degrade. Varies over shape vocabulary, reason
strings, and windowability policy.

Sites and roles: definition
`optimizer/nested_fetch.py::unwindowable_child_queryset_reason` (HEAD
`4d8d37a7`). Consumers (exactly three — census): the planner gate
(whole-relation refusal: unplanned, no resolver keys),
`lateral_fetch._recognize_lateral_fetch` first shape gate, and
`single_parent_fetch._fetch_single_parent_rows` shape gate (both degrade
to the windowed body). Interplay context (verified-separate): the seal's
`_PREFETCH_CHILD_POLICY` (`reject_sliced=False`) exists BECAUSE this gate
answers for the slice downstream — walker passes the policy, this gate
classifies (querysets F4; trigger re-checked in R10). Oracles: the
reason-matrix test (independent — spells every reason literally),
plus the `.distinct()` live refusal row. Projections: the classifier
docstring (per-reason rationale), the planner / seal comments citing it.

Challenges: all classifier rows count 1; no second shape vocabulary or
reason table exists. Owner: the classifier — the narrowest module all
three gates already import. No stored derivation (pure function of the
queryset). Migration: none. Behavioral proof: `static-reviewed`.
Structural gate (for the family item): the reason matrix already is one
— a renamed reason passes every behavior path and fails the matrix;
negative control is a reason-string edit. Coupling: none (consumers
degrade independently).

Prose-precision observation (below the defect bar, recorded so the
family item need not re-derive it): the docstring calls the classifier
the recognizers' "first gate" — exact for lateral (first statement),
and exact-for-shape-gates for single_parent, where the spec-missing and
setting-off preconditions (non-shape configuration, not query shape)
precede it. The load-bearing claim (degrade, never refuse) holds on
both bodies; nothing reorders gates on the word "first".

Freshness: target HEAD `4d8d37a7`; nested_planner HEAD `b4dfd4a6`,
lateral `db1ea315`, single_parent `e995270a`, querysets HEAD `b68be0e3`
(policy comments read), walker `e8d80005` (policy comments read),
test_nested_fetch HEAD `7fbd957b` (worktree dirt NOT traced).

### L1 — Module mechanics (file-local)

Module docstring (seam rationale, row-contract prose, indexing prose —
descriptions of F1–F4 rules, never definitions), the 13 top-level
imports, and the five lazy cycle-breaks (lateral in `_builtin_strategies`
/ `rebind` / auto `plan`, single_parent in windowed `plan`, conf in the
resolve `None` arm — each breaks a distinct documented edge in the
nested-lazy / backends-top-level direction; no shared machinery, nothing
to consolidate), the stdlib-composed mechanics (`@cache`,
`MappingProxyType` — shared constructor, not shared rule), and the
exceptions consumer link (`ConfigurationError`, `_safe_arg_repr`,
`_safe_type_name` — one of 20+ composing consumers; owner
`exceptions.py`, `e06b0b7f`). Single definition each, single module, no
second site. Challenge: posit a second module rationale, a second lazy
discipline, or a shared cycle-breaking helper — the census finds edge
endpoints, never a second definition; each lazy is load-bearing at its
own call site (a cycle is an `ImportError` at collect, self-proving, no
gate owed).

Freshness: target HEAD `4d8d37a7`; exceptions `e06b0b7f`.

### R1 — Planner re-resolution vs validation (rejected, standing)

Run-5 hints R7, verified. `_select_nested_strategy` composes the same
`resolve_strategy` on an already-validated name — one owner composed
twice, not two definitions. Trigger re-checked fresh against HEAD:
the planner still calls it unguarded (no catch, no branch on failure).
Not met; the standing rejection and its trigger stand.

### R2 — Selection ladder vs policy ladder (rejected, standing)

Run-5 policies W2-R3, verified. `resolve_strategy` returns shared
singletons BY DESIGN (strategies carry no mutable bounds) vs
`resolve_policy` returning a private policy BY DESIGN (enforcement
authorities). Opposite sharing contracts. Trigger re-checked fresh:
all three strategy classes are still stateless (`name` + `plan`
only — read at HEAD). Not met; stands.

### R3 — `active_strategy` default vs extension fallback default (rejected)

`active_strategy` answers hard `WINDOWED_STRATEGY` outside a managed
execution; `extension.py::_configuration` answers `resolve_strategy(None)`
(constructor-never-ran → deployment setting). Different defaults for
different reasons: an unmanaged direct caller gets the deterministic
default (pinned), while a subclass that skipped construction still gets
the deployment's setting. Contract difference: unmanaged-execution
default vs mis-constructed-instance default. Reconsideration trigger:
either default changes to match the other.

### R4 — Ladder shape vs the views ladder (rejected)

`views.py::_resolved_max_request_body_bytes` cites "the same split
`resolve_strategy` uses" (conf stays a thin reader; validation at the
consumer). The split is shared precedent, not shared code: views reads
its setting rung's `None` as DISABLE with int-range validation, while
`resolve_strategy` reads `None` as resolve-the-setting with registry
validation. Contract difference: scalar disable-ladder vs
name/instance selection ladder. Reconsideration trigger: the package
adopts one ladder driver.

### R5 — Shared `except` guard (rejected, standing)

`_request_body.py` J1 (verified) rejects one driver across the
`except` population: per-guard outcomes differ (a shared helper would
need a mode flag). The `resolve_strategy` plan-read arm answers typed
rejection, not position-state classification. Trigger re-checked:
no new guard needs the same position-state classification. Not met;
stands.

### R6 — Shared exact-type gate (rejected, standing)

`_request_body.py` J2 (verified) rejects one shared exact-type gate:
per-domain exclusion rules, different reasons to change. The target
needs the opposite posture at HEAD — `isinstance` INCLUSION gates with
hostile-tolerant slot reads (zero `type(x) is` sites in the target) —
not exclusion inside a boundary. Trigger re-checked: no new
foreign-object protocol needs exclusion here. Not met; stands.

### R7 — Per-message rejection grammars (rejected, standing)

Verified policies-R3 / hints-R5 precedent: each `ConfigurationError`
message names its own subject; no package-wide grammar is owned
anywhere. The target's two messages (unknown name, bad type) are
per-site framings. Trigger re-checked: no owned grammar adopted. Not
met; stands.

### R8 — `LateralJoinShape` vs `NestedConnectionStrategy` (rejected, standing)

Run-5 join_taxonomy R6, verified: join shape (how the child joins) vs
fetch strategy (which backend plans) are two axes of one matrix, not
one vocabulary. Trigger re-checked: the vocabularies are still two
separate enums at HEAD. Not met; stands.

### R9 — Bilateral import-rationale prose (rejected, standing)

Run-5 hints R4, verified: the hints runtime-import comment and the
`StrategySelection` comment state one edge decision twice; prose is not
a definition. Trigger re-checked fresh: both blocks still state the
same invariant (no cycle; `nested_fetch` never imports `hints`) —
verified by reading both comments plus the import census. Not met;
stands.

### R10 — Classifier vs seal rejection (rejected, standing)

Verified querysets F4: the classifier degrades a plan, never rejects —
a different contract with different reasons to change than the seal's
`reject_sliced` / connection guard. Trigger re-checked fresh: at HEAD
the planner gate returns unplanned (no raise) and both fetch gates fall
back to the windowed body — no rejection use exists. Stands.

### R11 — The two `__post_init__` twins (rejected)

`NestedConnectionRequest.__post_init__` and
`LateralWindowSpec.__post_init__` are each one line —
`assert_window_fetch_mode_for(self)` — composing one owner by name.
Two consumers, not two definitions. Contract difference: none in
behavior; the lateral twin exists so the raw-SQL backend cannot develop
a different fetch-mode contract (stated at both ends). Reconsideration
trigger: either body adds logic beyond the delegation.

### R12 — The two rebind wraps (rejected)

`LateralQuerySet.rebind(queryset, spec)` and
`SingleParentWindowQuerySet.rebind(queryset, spec)` (the two `wrap`
lambdas) are one-line compositions of one owner with different subclass
receivers. Two call sites, not two definitions. Reconsideration
trigger: a wrap adds logic beyond `Subclass.rebind(qs, spec)`, or a
third wrap shape appears.

### R13 — Spec-builder custom-subclass arms (rejected, standing)

Verified single-parent R-d: `single_parent_spec` (degenerate-shape
eligibility) vs `_build_lateral_spec` (SQL-expressibility) are not one
gate; the custom-subclass arms share rationale, each stated at its
site. Trigger re-checked fresh: v1 scope unchanged at HEAD
(single_parent still refuses keyset, counted, reversed, M2M, and custom
subclasses). Not met; stands.

### R14 — Row constructors (rejected, standing)

Verified single-parent R-c: pristine-clone synthesis vs lateral
`_instantiate_row` (`from_db` + converters + aliases + optional count)
are not one constructor. Trigger re-checked: still distinct mechanisms
at HEAD. Not met; stands. (F3 claims only the attribute contract both
satisfy, never the constructors.)

### R15 — Strategy `"auto"` vs field `"auto"` (rejected)

The 4-letter token coincides between the strategy-selection name and
the strawberry field-inference marker (`types/base.py`, re-exported at
the root): zero shared mechanism, zero shared rule — backend choice vs
field-shape inference. Contract difference: total (token coincidence
only). Reconsideration trigger: a shared auto-vocabulary rule (not
plausible across these domains).

### R16 — Lenient query-attr reads vs a lenient-readers module (rejected, standing)

Run-5 join_taxonomy R13 (verified) rejects extracting the lenient-read
declaration: local policy pin vs shared machinery. The classifier reads
query attrs via plain `getattr` with defaults — not a second
`lenient=True` consumer. Trigger re-checked: no new consumer of that
declaration. Not met; stands.

## Defects

### D1 — HEAD `resolve_strategy` lets a hostile `__class__` escape raw or detonate the `str` slot (observed; concurrent hunt owns these lines — NOT homed)

Contract row (HEAD `resolve_strategy` docstring): "every dunder its
decision reads is taken through the base `str` slot", and "a hostile
`__eq__` / `__hash__` / `__repr__` can neither force a false match nor
replace the typed `ConfigurationError` with an arbitrary exception."
At HEAD both `isinstance` gates (`isinstance(value, str)` and
`isinstance(value, type)`) read `__class__` through NORMAL lookup,
outside the base-slot discipline the contract claims. Two holes,
proven mechanically by the item probe (pure Python, no Django, no
package import):

- Raising `__class__`: `isinstance` propagates the raw exception —
  probe prints `isinstance(raising, str): RAW RuntimeError escapes`.
  Applies to both gates identically (same lookup mechanism).
- Spoofed `__class__ = str`: the value passes the `str` gate, then
  `str.__eq__` raises `TypeError: descriptor '__eq__' requires a 'str'
  object` — probe prints the detonation. A false match AND a raw
  exception, both contract-forbidden.

Feasible shape under supported API: any consumer-supplied selection —
the extension `nested_connection_strategy=` kwarg, the
`NESTED_CONNECTION_STRATEGY` setting value, or
`OptimizerHint.strategy(...)` — whose `__class__` raises or spoofs.
The contract's own threat model explicitly covers hostile selection
values (three hostile-dunder oracles pin the typed degradation);
`__class__` is the one dunder the decision reads that the HEAD body
does not guard. No HEAD oracle pins `__class__` behavior (the hostile
matrix covers `__eq__` / `__hash__` / `__repr__` / `__name__` only).

Homing: OBSERVED, NOT HOMED. The concurrent hunt owns exactly these
lines (its +23/-5 hunk rewrites both gates to `type()`-based reads
with `except BaseException` arms and adds `__class__` to the docstring
list). Closeout-conditional instruction: home (file a card owning
`optimizer/nested_fetch.py::resolve_strategy`, or fold into the hunt's
own card) ONLY if the hunt does not land; if the hunt lands, verify
its tests pin both holes and close this entry as overtaken. (Precedent:
run-5 hints D1, verified, same defect class on `hints.py`.)

Freshness: target HEAD `4d8d37a7` (defect read at HEAD bytes);
worktree `29ce5201` hunt hunk read for attribution only. Probe:
`docs/dry/temp-tests/dry-file-optimizer__nested_fetch/probe_isinstance_class.py`
(`uv run python` + scoped `ruff check` + `ruff format --check` green).

## Pending execution

None. No pytest: every judgment above is settled by HEAD-byte reading,
a package-wide HEAD census, cited oracles, or the pure-Python mechanics
probe; a shared-tree run would measure concurrent hunt dirt (both
target-adjacent oracle files are hunt-dirtied), not HEAD. No `proof:`
or `gate:` entries are owed.

## Judgment

Zero-edit file item, ready for independent verification: 13/13 named
members homed (1 existing family converged, 2 adopted — 1 converged, 1
narrowed with the divergence stated — 1 new, 1 file-local, 16
rejections with contract differences and triggers), one mechanically
proven defect correctly observed-not-homed on hunt-owned lines, no
pending execution. The family items owed are one new audit each for
F2, F3, and F4 (F1's item already queued); this item makes no edit and
proposes no consolidation.

## Index rows for Worker 0

Family rows (Worker 0 alone edits the plan):

- Family `recognized-fetch-queryset-skeleton` | Owner
  `optimizer/nested_fetch.py::RecognizedFetchQuerySet` | Files
  `optimizer/nested_fetch.py`, `optimizer/lateral_fetch.py`,
  `optimizer/single_parent_fetch.py` | Holding item Family
  `recognized-fetch-queryset-skeleton` | open (name adopted from File
  `optimizer/lateral_fetch.py` F-D prior evidence; boundary re-derived
  fresh, converged)
- Family `nested-fetch-strategy-seam` | Owner
  `optimizer/nested_fetch.py::NestedConnectionStrategy` | Files
  `optimizer/nested_fetch.py`, `optimizer/lateral_fetch.py`,
  `optimizer/single_parent_fetch.py`, `optimizer/nested_planner.py`,
  `connection.py`, `optimizer/plans.py`, `utils/connections.py` |
  Holding item Family `nested-fetch-strategy-seam` | open (name adopted
  from File `optimizer/lateral_fetch.py` F-F prior evidence; boundary
  narrowed fresh — selection stays in
  `nested-connection-strategy-selection`; divergence stated in F3)
- Family `unwindowable-child-queryset-classification` | Owner
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` |
  Files `optimizer/nested_fetch.py`, `optimizer/nested_planner.py`,
  `optimizer/lateral_fetch.py`, `optimizer/single_parent_fetch.py`,
  `utils/querysets.py`, `optimizer/walker.py` | Holding item Family
  `unwindowable-child-queryset-classification` | open (NEW; querysets
  + walker are interplay context for verified-separate querysets F4)
- Existing Family `nested-connection-strategy-selection`: no new row.
  Proposal for Worker 0: extend files-covered with
  `optimizer/lateral_fetch.py` (homes the `LATERAL_STRATEGY` registry
  value + `name` attr — F1 definition set), on F1's fresh census.

File-local row:

- Module mechanics (docstring projections, 13 imports, 5 lazy
  cycle-breaks, stdlib-composed cache/proxy, exceptions consumer link)
  | `optimizer/nested_fetch.py` | `optimizer/nested_fetch.py` | File
  `optimizer/nested_fetch.py` | file-local

Rejection rows:

- Planner re-resolution vs validation |
  `optimizer/nested_fetch.py::resolve_strategy` (standing hints-R7
  trigger-checked here) | `optimizer/nested_fetch.py`,
  `optimizer/nested_planner.py`, `optimizer/hints.py` | File
  `optimizer/nested_fetch.py` | rejected
- Selection ladder vs policy ladder |
  `optimizer/nested_fetch.py::resolve_strategy` (standing policies
  W2-R3 trigger-checked here) | `optimizer/nested_fetch.py`,
  `utils/policies.py` | File `optimizer/nested_fetch.py` | rejected
- `active_strategy` default vs extension fallback default |
  `optimizer/nested_fetch.py::active_strategy` (rejection recorded
  here) | `optimizer/nested_fetch.py`, `optimizer/extension.py` | File
  `optimizer/nested_fetch.py` | rejected
- Ladder shape vs the views ladder |
  `optimizer/nested_fetch.py::resolve_strategy` (rejection recorded
  here) | `optimizer/nested_fetch.py`, `views.py` | File
  `optimizer/nested_fetch.py` | rejected
- Shared `except` guard |
  `optimizer/nested_fetch.py::resolve_strategy` (standing J1
  trigger-checked here) | `optimizer/nested_fetch.py`,
  `_request_body.py` | File `optimizer/nested_fetch.py` | rejected
- Shared exact-type gate |
  `optimizer/nested_fetch.py::resolve_strategy` (standing J2
  trigger-checked here) | `optimizer/nested_fetch.py`,
  `_request_body.py` | File `optimizer/nested_fetch.py` | rejected
- Per-message rejection grammars |
  `optimizer/nested_fetch.py::resolve_strategy` (standing policies-R3
  trigger-checked here) | `optimizer/nested_fetch.py` | File
  `optimizer/nested_fetch.py` | rejected
- `LateralJoinShape` vs `NestedConnectionStrategy` |
  `optimizer/nested_fetch.py::NestedConnectionStrategy` (standing
  join_taxonomy-R6 trigger-checked here) |
  `optimizer/nested_fetch.py`, `optimizer/join_taxonomy.py` | File
  `optimizer/nested_fetch.py` | rejected
- Bilateral import-rationale prose |
  `optimizer/nested_fetch.py` (standing hints-R4 trigger-checked here)
  | `optimizer/nested_fetch.py`, `optimizer/hints.py` | File
  `optimizer/nested_fetch.py` | rejected
- Classifier vs seal rejection |
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
  (standing querysets-F4 trigger-checked here) |
  `optimizer/nested_fetch.py`, `utils/querysets.py`, `connection.py` |
  File `optimizer/nested_fetch.py` | rejected
- The two `__post_init__` twins |
  `optimizer/nested_fetch.py::NestedConnectionRequest.__post_init__`
  (rejection recorded here) | `optimizer/nested_fetch.py`,
  `optimizer/lateral_fetch.py` | File `optimizer/nested_fetch.py` |
  rejected
- The two rebind wraps |
  `optimizer/nested_fetch.py::RecognizedFetchQuerySet.rebind`
  (rejection recorded here) | `optimizer/nested_fetch.py`,
  `optimizer/lateral_fetch.py` | File `optimizer/nested_fetch.py` |
  rejected
- Spec-builder custom-subclass arms |
  `optimizer/nested_fetch.py::RecognizedFetchQuerySet.rebind`
  (standing single_parent-R-d trigger-checked here) |
  `optimizer/nested_fetch.py`, `optimizer/lateral_fetch.py`,
  `optimizer/single_parent_fetch.py` | File
  `optimizer/nested_fetch.py` | rejected
- Row constructors |
  `optimizer/nested_fetch.py::NestedConnectionStrategy` (standing
  single_parent-R-c trigger-checked here) |
  `optimizer/nested_fetch.py`, `optimizer/lateral_fetch.py`,
  `optimizer/single_parent_fetch.py` | File
  `optimizer/nested_fetch.py` | rejected
- Strategy `"auto"` vs field `"auto"` |
  `optimizer/nested_fetch.py::resolve_strategy` (rejection recorded
  here) | `optimizer/nested_fetch.py`, `types/base.py` | File
  `optimizer/nested_fetch.py` | rejected
- Lenient query-attr reads vs a lenient-readers module |
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
  (standing join_taxonomy-R13 trigger-checked here) |
  `optimizer/nested_fetch.py`, `optimizer/join_taxonomy.py` | File
  `optimizer/nested_fetch.py` | rejected

## Independent verification (Worker 2)

### Part A — Own trace (recorded before opening `## Findings`)

Trace subject: HEAD bytes
`git show HEAD:django_strawberry_framework/optimizer/nested_fetch.py`,
blob `4d8d37a7f52cf94d2916f17db3a8a21393e28d57`, 488 lines. Worktree
`29ce5201877864b01079c849b92a1e812166affd`, 506 lines; the diff vs
HEAD is hunt dirt confined to `resolve_strategy` (docstring +
`type()`-not-`isinstance` str gate + `__class__` interrogation
guards), NOT traced. HEAD governs. Neighbor HEAD blobs read fresh
for this trace: `optimizer/hints.py` `da46ef89`,
`optimizer/_context.py` `3d8dcfdf`,
`optimizer/single_parent_fetch.py` `e995270a`,
`optimizer/lateral_fetch.py` `db1ea315`,
`optimizer/nested_planner.py` `b4dfd4a6`,
`optimizer/extension.py` `49667a93`, `optimizer/plans.py`
`cce98531`, `optimizer/join_taxonomy.py` `9b355a50`,
`optimizer/walker.py` `e8d80005` (REOPENED file: bodies read fresh,
artifact used as trigger only), `utils/connections.py` `f549389e`,
`conf.py` `c6ad46aa`, `exceptions.py` `e06b0b7f`,
`connection.py` `4894f90f`, `tests/optimizer/_builders.py`
`567defa9`, `tests/optimizer/test_nested_fetch.py` `7fbd957b`
(worktree hunt dirt NOT traced),
`tests/optimizer/test_nested_index_advisory.py` `beee6b7d`
(worktree hunt dirt NOT traced),
`tests/optimizer/test_hints.py` `d3e413bd`,
`tests/optimizer/test_lateral_fetch.py` `67431054`. Verified prior
artifacts read as orientation only (their verdicts stand):
hints F3 (`nested-connection-strategy-selection`), join_taxonomy
F1–F3, lateral_fetch F-A–F-F, single_parent F-D–F-F, plans F-M.

### W2 enumeration (own instrument: `ast.Module.body` of the HEAD bytes)

27 body nodes: 1 module docstring + 13 imports + 13 named members.
Named members: `unwindowable_child_queryset_reason` (func),
`RecognizedFetchQuerySet` (class), `NestedConnectionRequest`
(class), `NestedConnectionStrategy` (class),
`StrategySelection` (assign), `attach_windowed_prefetch` (func),
`WindowedPrefetchStrategy` (class), `WINDOWED_STRATEGY`
(assign), `AutoNestedConnectionStrategy` (class),
`AUTO_STRATEGY` (assign), `_builtin_strategies` (func),
`resolve_strategy` (func), `active_strategy` (func). Proven by
the read-only probe
`docs/dry/temp-tests/dry-file-optimizer__nested_fetch-w2/census.py`
(HEAD bytes via `git show`; no package import; asserts 27/13).

### W2 sites and roles per posited rule

W2-R1 strategy selection (alias + registry + resolver + hostile
discipline). Definition: this module (`StrategySelection`,
`_builtin_strategies`, `resolve_strategy`). Consumers:
`optimizer/hints.py` (field annotation, `strategy()` factory
parameter, `_require_strategy` delegation; the explicit-`None`
rejection is hints' own counter-rule, needed exactly because the
owner treats `None` as valid),
`optimizer/extension.py` (kwarg annotation + two resolve calls at
construction/default), `optimizer/nested_planner.py::`
`_select_nested_strategy` (re-resolve of a validated name, else
`active_strategy()`), `conf.py::`
`nested_connection_strategy_setting` (the setting read feeding
the `None` leg). Oracles: `test_nested_fetch.py` strategy rows
(registry identity, name/`auto`/instance resolution, unknown
name, bad type, hostile dunders, raising `plan`, lateral lazy
load, `None`-reads-setting, extension construction, per-field
seam), `test_hints.py` factory pins, the live auto-override
suite. Projections: alias comment, `resolve_strategy`
docstring, module selection paragraphs, GLOSSARY/README prose.

W2-R2 unwindowable-child-queryset classification. Definition:
`unwindowable_child_queryset_reason` (five reason arms + the
`values` iterable gate + `None`). Consumers:
`nested_planner.py::plan_connection_relation`
(whole-relation refusal gate),
`lateral_fetch.py::_recognize_lateral_fetch` and
`single_parent_fetch.py::_fetch_single_parent_rows`
(fetch-time degrade gates). Comment-only mentions in `walker.py`
and `utils/querysets.py` are projections. Oracles: the reason
matrix test (spells all five reasons plus `None` shapes —
independent). No index family names this rule; it is new from
here.

W2-R3 windowed-fetch floor. Definition:
`attach_windowed_prefetch` (window-argument threading +
optional `wrap` + `Prefetch` attach under
`request.lookup`/`request.to_attr` + the `True` planned
verdict). Consumers: `WindowedPrefetchStrategy.plan` (bare +
single-parent wrap), `lateral_fetch.py::`
`LateralPrefetchStrategy.plan` (lateral wrap). The `to_attr`
NAME grammar is owned by
`nested_planner.py::relation_connection_to_attr`; the floor
only carries request fields. Oracles: the windowed-prefetch
shape test (spells `to_attr` and both window annotations —
independent), lateral strategy tests, live suites.

W2-R4 recognized-fetch queryset skeleton. Definition:
`RecognizedFetchQuerySet` (`_clone` spec carry, `rebind`
class-swap + planned-window signature capture,
`_fetch_recognized_rows` hook, `_fetch_all` swap-or-windowed
fallback). Adapters: `lateral_fetch.py::LateralQuerySet`,
`single_parent_fetch.py::SingleParentWindowQuerySet`
(`_dst_spec_attr` each + own recognizer). Oracles: plumbing
rows in both backend test files. Lateral_fetch F-D already
names this family with this module as owner.

W2-R5 request record + fetch-mode guard. The
`NestedConnectionRequest` record is defined here; the
probe/count rule it enforces via `__post_init__` is defined in
`utils/connections.py::assert_window_fetch_mode_for`, also
composed by `lateral_fetch.py::LateralWindowSpec.__post_init__`
— one owner composed twice, not two definitions.
Lateral_fetch F-C already names that guard family.

W2-R6 module mechanics (file-local candidates): the
`NestedConnectionStrategy` protocol, both strategy classes,
both singletons, the `@cache` registry builder, and
`active_strategy` (frame read via
`_context.py::active_nested_strategy` with the windowed
default). Single-module each; the only `active_strategy`
production caller is `_select_nested_strategy`. The
`WindowRangePlan`/keyset/window-mode vocabulary the request
carries is owned in `utils/connections.py` / `keyset.py` and
merely referenced here.

### W2 change challenges (definition counts)

- Fourth builtin strategy name: `_builtin_strategies` (+ the
  backend's own `name` + projections/oracles, not counted) = 1.
- Hostile-`__class__` discipline at the str gate: `resolve_strategy`
  only = 1 (the concurrent hunt dirt lands exactly there).
- `None`-means-setting semantics: `resolve_strategy` only = 1
  (`_require_strategy`'s explicit rejection is the counter-rule,
  correct under either semantics).
- Sixth unwindowable shape: the classifier only = 1 (consequences
  stay at the three consumers).
- New window parameter: the floor threads it once; both backends
  inherit = 1.
- New clone-carried fetch attr: `RecognizedFetchQuerySet._clone`
  only = 1.
- Probe/count rule change: `assert_window_fetch_mode_for` only =
  1 (both `__post_init__`s follow by call).
- `to_attr` grammar change:
  `relation_connection_to_attr` only = 1 (floor + request +
  `connection.py` readers follow by call or field carriage;
  the test builder's f-string spelling is oracle-side setup,
  not a production definition).

### W2 owner choice (principle 7)

Selection: `resolve_strategy` beside the alias and the registry
— the same rule hints F3 already named, so this finding
CONVERGES onto `nested-connection-strategy-selection`; the name
vocabulary inside it (registry keys vs backend `.name` attrs
vs the `auto` special-case vs the conf default) is evidence
for the family item, which decides whether the keys derive
from `.name`. Floor + protocol + member backends: the planning
seam, owned at `attach_windowed_prefetch` beside the protocol —
lateral F-F `nested-fetch-strategy-seam` as named ALSO covers
selection, and the two vary independently here (add a backend
vs re-thread the window), so the correct adoption is
DIVERGE-narrowed: cut selection out to the hints family, keep
the seam for the planning contract. Skeleton: adopt
`recognized-fetch-queryset-skeleton` as named (owner-side
evidence for the lateral-named family; adapters stay separate
per principle 5). Classifier: NEW family (no index row names
it). Request record, protocol, singletons, registry builder,
`active_strategy`: file-local mechanics. Post-init twins:
rejection (one guard, two enforcement sites).

### W2 matrix (own discharge)

1. Cross-flavor mirroring: searched. Strategy selection is
   optimizer-internal; the only cross-module policy pair is
   `resolve_strategy`'s hostile-value discipline vs
   `exceptions.py` renderer slot discipline — same technique,
   different contracts (dispatch-match vs render), so a
   rejection, not a family. The selection ladder
   (kwarg → setting → default) vs the `utils/policies.py`
   construction ladder: different domains (strategy backend vs
   error/resource policy), different reasons to change —
   rejection.
2. Sync/async twins: inapplicable by construction. The target is
   sync-only planning plus a sync `QuerySet._fetch_all`
   override; no `async def`, no await point, no twin body
   exists (census: zero `async` tokens in the HEAD bytes).
3. Derived knowledge: searched. `to_attr` naming (owned by the
   planner, carried here), `order_by` (shared with resolve
   time by field carriage), strategy names (registry keys vs
   `.name` — converged-family evidence, above). No second
   derivation of any target-owned fact.
4. Inverse / round-trip pairs: searched. Plan/fetch halves
   (`rebind` capture vs recognizer proof,
   `LateralWindowSpec` planned-vs-fetch-time) live in the
   backend modules; this module owns only the skeleton's half
   (`_fetch_all` swap-or-fallback), single. No pair split
   across two definitions here.
5. Contracts in another medium: searched. Test spellings of
   strategy names, reason strings, `to_attr`, and window
   annotations are literal oracles (independent); the
   `sorted(registry) == ["lateral", "windowed"]` pin asserts a
   literal list (oracle, not owner-read); module/hint/spec
   prose are projections. No oracle reads the owner it checks.
6. Enforcement by omission: searched. The `to_attr` row
   contract (`_dst_row_number`, conditional
   `_dst_total_count`) is enforced for builtins by
   construction through the floor; consumer-authored
   strategies cannot be statically checked and no contract
   source demands a check — no omission defect. Every builtin
   backend ends in the floor (both `plan` bodies censused);
   every strategy-selection seam resolves through the one
   resolver (extension × 2, hints, planner — censused).

### W2 candidate defect (pre-findings)

HEAD `resolve_strategy`'s `isinstance(value, str)` gate
consults a hostile `__class__`: a raising one escapes raw (not
the typed `ConfigurationError`), and a spoofed one (claiming
`str`) passes the gate only for the base-`str`-slot read to
detonate (`str.__eq__` requires a real `str` first argument).
The concurrent hunt owns exactly these lines (worktree
`29ce5201` arms both interrogations), so the correct handling
is observed-not-homed with fingerprints and a
closeout-conditional homing instruction — NOT a homed defect,
NOT verdict leverage.

### Part B — Findings reconciliation and verdict (read after Part A)

Enumeration: 13/13 both sides, member-by-member identical. The
only grouping difference is mine-coarse vs theirs-split: where
Part A held the protocol, strategy classes, singletons,
registry builder, and `active_strategy` as file-local
candidates, the artifact homes `name` attrs + singletons +
registry + resolver + runtime read into F1 and `plan` bodies +
protocol + floor into F3. The split is the better assignment
(selection vocabulary vs seam implementation vary
independently) and leaves L1 exactly the docstring + imports +
mechanics. Adopted; nothing unassigned either way. Part A also
undercounted the lazy cycle-breaks (four vs the artifact's
five — I missed the conf read in the resolve `None` arm);
five is correct (each breaks a distinct documented edge,
verified against the bodies).

F1 CONVERGE onto `nested-connection-strategy-selection`:
accepted. Same rule as hints F3 on fresh evidence — one
alias, one registry, one resolver, hostile discipline, the
same four consumers (hints, extension × 2 calls, planner,
conf reader) — with owner-side additions the consumer-side
record could not make (registry mechanics, singletons beside
their backends, the runtime read, the lateral registry
value). Reproduced the no-second-alias/registry/resolver
census and all seven short fingerprints. The registry-keys
vs `name`-attrs dual spelling is correctly held as
F1-internal evidence for the family item, not a second
definition.

F2 ADOPT `recognized-fetch-queryset-skeleton`: accepted. The
name fits evidence derived here: the skeleton is defined in
this module, exactly two subclasses exist (census over package
+ tests — the test file references but never subclasses),
exactly two `rebind` callers exist (both spec-guarded wraps),
both recognizers fail closed on a `None` signature (verified
on both bodies), and the recognizers prove different queries.
Owner-side evidence for the lateral-named family; adapters
stay separate per principle 5.

F3 ADOPT `nested-fetch-strategy-seam`, DIVERGE-narrowed:
accepted. Cut: selection (alias, registry, resolver,
singletons, runtime read) — stays in the hints family. Kept:
record, protocol, floor, both here-homed `plan` bodies, row
contract. Why: independent variation with counts (a new
builtin name moves the registry; a new window parameter moves
the record + floor), and lateral F-F never drew the shared
boundary (it lumps selection + floor and never cites the
hints family — read, not inherited). Reproduced the
sole-production-builder, triple-floor-call-site (the fourth
match is docstring prose), and triple-`plan`-implementer
censuses, plus the floor's eight parameters against the plans
signature. Owner difference, reconciled: Part A chose the
floor (mechanism weight), the artifact chooses the protocol
(contract every backend implements) and records the re-home
option for the family item. Both are defensible under
principle 7; the alternative is on record either way. No
revision.

F4 NEW `unwindowable-child-queryset-classification`: accepted.
No index row names this rule (checked); the name fits the
evidence (five stable reasons + `None`, exactly three
degrade-gates censused, querysets-F4 interplay read at its
body). The "first gate" prose-precision note is exact on both
bodies (spec-missing + setting-off precede the classifier in
single_parent and are configuration, not shape).

Matrix: agree on all six axes; the artifact's discharge is
strictly more thorough than Part A's (13-file flavor census,
four-module async census, floor-vs-signature threading check,
verdict-pair analysis, per-finding oracle lists, contract
sources for every omission arm). Every claimed search was
reproduced; the one claimed inapplicability (axis 2) carries
its reason (zero `async def`, plan-time + sync fetch).

Rejections: all sixteen carry a contract difference (or an
explicit none-in-behavior where the point is one owner
composed twice) plus a trigger. Every standing trigger was
re-checked against HEAD bodies, not cited — reproduced nine
of them directly (R1 unguarded planner call; R2 all three
strategy classes `name` + `plan` only; R5/R6 the single
except arm + zero `type(x) is` in the target; R8 vocabularies
still separate; R9 both import comments + import census;
R10 planner returns unplanned + both fetch gates fall back;
R13 all five single_parent refusal arms; R14 synthesis vs
`from_db`; R16 plain-`getattr` classifier reads) and confirmed
the trigger texts for the rest (J1/J2, querysets F4, policies
R3, single-parent R-c/R-d, join R6) state what the artifact
checked. New rejections R3, R4, R11, R12, R15 are each
grounded (extension fallback body, views citation, shared
guard body, the two one-line wraps, the `types/base.py` token
— all read).

D1 handling: correct. Observed-not-homed on hunt-owned lines
with both fingerprints, the contract row, the feasible
consumer-supplied shape, and a closeout-conditional homing
instruction — the same handling as verified run-5 hints D1
for the same defect class. Re-ran the item probe: both holes
print exactly as quoted (pure Python, no package import).
Part A covered only the `str` gate; the artifact additionally
covers the `isinstance(value, type)` gate (raising escapes
raw there too) — more complete, and precise about the spoofed
case applying to the `str` gate only.

Corrections on record (Worker 2; below the revision bar —
oracle-listing precision, no count or home affected):
(1) F3's oracle census omits the request constructions in
`tests/test_keyset.py` (one builder) and
`tests/test_lateral_pg_parity.py` (three sites) — test-side
oracles, correctly uncounted, but a new required request
field would move them too; the F3 family item picks them up.
(2) "Sole `NestedConnectionRequest(` site" reads as sole
PRODUCTION site (six test constructions exist as oracles).
(3) R8 "two separate enums" loosely follows the standing
trigger's own "one enum" phrasing; strictly the strategy
vocabulary is names + a Protocol, and the verified substance
is that the two vocabularies have not merged. No production
defect found beyond D1; no `## Defects` entry owed.

Prose and gates: no process-provenance words (census); all
citations `path::Symbol`, zero raw line refs; no tests (file
item — tier N/A); no markdown cross-file links, hence no link
scaffold (same as both verified neighbor artifacts). Ruff on
the touched path: the artifact is `.md`, ruff-excluded
(`ruff check` → "No Python files found", exit 0;
`ruff format --check` exit 0). Both scratch probes
(W1's + mine) are `ruff check` + `ruff format --check` green.
No `$WS` copy taken (no mutating proof needed); probes are
read-only (HEAD bytes via `git show`, one pure-Python
mechanics run).

Window at verdict: `git diff --name-only ITEM_BASELINE --
django_strawberry_framework tests examples` names
`django_strawberry_framework/list_field.py` +
`tests/test_list_field.py` (empty at dispatch). Attributed by
content: concurrent bug-hunt containment arms
(`isclass`/`issubclass`/registry/`origin` interrogation
guards) + companion hostile-`__class__`/`__hash__` oracles —
same session signature as the target's hunt dirt, out of
scope, touched by neither worker. Target + both oracle files
are silent in the window. HEAD still `5ee86193`. Item-scoped
diff remains exactly this artifact (untracked) plus scratch
probes; zero production edits by either worker.

Verdict: `verified`. 13/13 members homed (1 converge +
2 adopted with 1 stated narrowing + 1 new + 1 file-local +
16 rejections), D1 correctly observed-not-homed, no pending
execution. Scratch left for Worker 0's explicit-path removal:
`docs/dry/temp-tests/dry-file-optimizer__nested_fetch/` (W1)
and `docs/dry/temp-tests/dry-file-optimizer__nested_fetch-w2/`
(W2, one 1.5 KB census).
