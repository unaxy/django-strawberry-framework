# DRY review: `django_strawberry_framework/orders/sets.py`

Status: verified
Run: 0.0.15 2026-09-22-6

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an open or
verified family holding item, or is a rejection carrying its contract
difference + trigger. One new family is named for Worker 0 (the guard's
twin agreement verdicts). Zero production edits; zero tracked files changed.

## System trace

Target owns the order family's declaration, validation, and apply pipeline
(`django_strawberry_framework/orders/sets.py`, 832 lines at HEAD, HEAD blob
`6044ab1a`): the invocation-scoped normalization ledger
(`_AppliedNormalization` / `_NormalizationLedger` /
`_ORDER_NORMALIZATION_CAPTURE` / `capture_applied_order_normalization` /
`_record_applied_normalization`), the pipeline-boundary return gate
(`_validate_normalized_terms`), the declaration metaclass
(`OrderSetMetaclass`), and `OrderSet` itself (5 class attrs + 10 methods:
Layer-4 expansion, the offset-guard active-terms check, the normalize
delegate, the permission warm-up hook, the cookbook flat walk, the
expression resolver with its row-preserving to-many aggregate, the
uncolored apply tail, and the sync/async resolver pair).

Traced end to end, filter twin FIRST (whole
[filters-sets][filters-sets], 3529 lines, HEAD blob `722e0c77`): same
substrate imports, same two-condition cache gate, same re-readability
gate, same collector call shape with the opposed inherit policy — and
five documented divergences (rejections R-m1..R-m4 converging the
twin's verified separations on fresh evidence, plus the fresh
R-EXPAND split, each re-derived below against HEAD bodies). Owner
bodies in [sets-mixins][sets-mixins] (naming mixin, target mixin,
collector, `expanded_once`, cache gate, re-readability gate,
`SetLifecycleAttrs`, permission facade — read whole, 768 lines), the
Meta readers in [utils-inputs][utils-inputs] (`promote_set_meta_fields`
/ `read_set_meta_fields` / `clear_generated_input_namespace`'s
`binding_attrs` consumption), the boundary in
[utils-querysets][utils-querysets] (`run_in_one_sync_boundary`,
`apply_orderset_sync` / `apply_orderset_async`, the post-sidecar
seal), the path owners in [utils-relations][utils-relations]
(`classify_path`, `path_traverses_to_many`), the mangle in
[utils-strings][utils-strings] (`flatten_lookup_path`), the traversal
shape in [input-values][input-values] (`SetInputTraversal` defaults),
the declaration seam in [orders-base][orders-base] (`RelatedOrder`
whole, 151 lines), the pipeline feeds in
[orders-inputs][orders-inputs] (`normalize_input_value`,
`_ensure_field_specs`, `_get_concrete_field_names_for_order`,
`Ordering`), the sole ledger consumers in [list-field][list-field]
(the offset guard + capture scope, HEAD-clean region), the
terminal-closure sibling in
[operation-lease][operation-lease] (whole, 80 lines), the cookbook
`orderset.py` (`OrderSetMetaclass.__new__`, `AdvancedOrderSet`
suffixes, `get_flat_orders`, `bind_orderset` — port-delta check
against the running upstream, not prose), oracles in
[test-order-sets][test-order-sets] (90 tests at HEAD) plus the live
`orderBy` population (13 `test_query` modules carry the token),
contract sources [spec-028][spec-028] (Decisions 2/3/5/6/8/12/13, DoD
4, Edge cases — read) and [spec-030][spec-030] (Decision 11
aggregate paragraph — read; P1-B census below), and the verified
holding/trigger artifacts [dry-filters-sets][dry-filters-sets]
(R-m1..R-m4/R-1 as orientation triggers, re-derived fresh),
[dry-orders-base][dry-orders-base] (F2 seam + R1 trigger),
[dry-orders-factories][dry-orders-factories] (F-1/F-2 as open-family
facets), [dry-orders-inputs][dry-orders-inputs] (F-ENUM/F-CONC/F-NORM
+ R-guards/R-norm/O1 as triggers, re-derived fresh; D2's twin cite
ADJUDICATED below as D1), [dry-clear-lifecycle][dry-clear-lifecycle]
(membership census), and [dry-mutid][dry-mutid] (R2 trigger, checked
fresh).

Dirt note (all hunt-dirtied paths read via `git show HEAD:<path>`,
never touched): the worktree target (`f09d9983…`, +32/-12:
`_safe_class_name` import + adoption at ten label sites, plus the
guarded `__all__`-shorthand gate with its `except BaseException`
arm) is concurrent-external dirt — every judgment below is against
HEAD bytes `6044ab1a…`, which govern. Findings whose LINES contain
the dirt name it per finding (label-hardening + one guard arm: no
definition moved, no count affected). Likewise read at HEAD bytes
only: [filters-sets][filters-sets] (`c1a0f1b2…`, body hunks outside
the judged metaclass/expansion/normalize/apply regions),
[sets-mixins][sets-mixins] (`a4b301c3…`, hunks outside the judged
bodies), [utils-inputs][utils-inputs] (`47b2af21…`, hardening incl.
inside the judged readers — no definition moved, no count affected),
[utils-querysets][utils-querysets] (`799139be…`, hunks outside the
judged boundary/apply wrappers), [utils-relations][utils-relations]
(`1cf81e58…`, hunks outside the judged classifier + to-many helper),
[utils-strings][utils-strings] (`ffa4fee0…`, `__all__` hunk outside
`flatten_lookup_path`), [orders-base][orders-base] (`afd55efd…`,
`_validate_target` hunk outside the judged slot/constructor lines),
[orders-inputs][orders-inputs] (`889b5971…`, owner-name line outside
the judged delegate/guard/helper lines),
[list-field][list-field] (`f979f0d6…`, validator hardening far from
the judged guard/scope region), [input-values][input-values]
(`d4ebeeb6…`, depth hunk outside `SetInputTraversal`),
[connection][connection] (`9c5b8724…`, hunks outside the judged
`order_by` + sidecar lines), [finalizer][finalizer] (`f866fcf0…`,
hunk outside the judged bind line), and
[test-order-sets][test-order-sets] (`d8cb5bdb…`, 14 appended
hostile-label/eq tests targeting the DIRTY lines — outside the
judged HEAD oracle blocks). Clean witnesses re-hashed both sides:
[orders-factories][orders-factories] (`4f35b66b…`),
[orders-init][orders-init] (`ed546f9c…`), [exceptions][exceptions]
(`e06b0b7f…`), [utils-permissions][utils-permissions] (`9889d6fe…`),
[operation-lease][operation-lease] (`10c164b7…`), [spec-028][spec-028]
(`94a3141c…`), [spec-030][spec-030] (`0f7db072…`).

Excluded with reason: `set-arguments-factory-bfs` does NOT list this
file, and correctly so — the BFS reads `get_fields` through the hook
body (consumption, C-facet in F-EXPAND), the walk/collision/cache
live at the base with zero tokens here. `dynamic-set-class-getter`
DOES list this file (metaclass write-back call site — contributor
facet in F-META). `subsystem-clear-lifecycle` (verified, member 6)
is routed as a lawful convergence (F-LIFE). `one-sync-boundary`
(verified) and `orm-lookup-path-resolution` (verified) are routed as
consumer facets (F-APPLY, F-EXPAND/F-RESOLVE). `sealed-execution-queryset`,
`child-queryset-alias-inheritance`, `queryset-seed-and-model-read`,
`sync-boundary-recourse-wording`, and `field-value-coercion` were
judged on their mechanisms against this target's REAL surface and
correctly withheld (negatives verified: zero `seal` / `base_queryset`
/ `model_for` / `recourse` / `coerce` tokens; the `.model` reads are
direct attribute reads on typed querysets/models, never the seed
machinery). No index row named `lookup-name-spelling-grammar`,
`filter-logic-operators`, `active-input-permission-facade`,
`set-type-naming`, `set-expansion-once-skeleton`,
`set-expansion-cache-write-gate`, `re-readable-field-declaration-gate`,
`related-set-target-lifecycle`, or `related-declaration-collection`
exists in the current plan; the filters-twin artifact's reuse rows
were orientation only (prior verdicts are triggers to check), and
each mechanism is re-derived fresh below — the twin pairs surface as
rejections (R-m1..R-m4, R-EXPAND), the single-sited consumptions as
file-local rows naming their owners, never new families (no second
definition exists to consolidate anywhere except F-PURITY).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Twin read FIRST whole
([filters-sets][filters-sets], 3529 lines). Shared substrate,
consumed by name on both sides: `promote_set_meta_fields` (order
pure read, filter with alias), `collect_related_declarations`
(order `inherit_from_bases=True` over class-body attrs, filter
`False` over declared stream), `expanded_once` (order no
`on_reentry`, filter with), `should_cache_expansion` (family slot
params), `require_re_readable_field_declaration` (family subjects),
`run_in_one_sync_boundary` (order wraps the permission pass only,
filter wraps finalize), `classify_path` + `path_traverses_to_many`
(both seams both sides) — with five genuine semantic divergences,
each re-derived fresh with this file's own difference: expansion
publish (R-m1, CONVERGE); normalizers (R-m2, CONVERGE);
apply pair + coloring (R-m3, CONVERGE); metaclasses (R-m4,
CONVERGE); Meta expansion vs upstream narrowing (R-EXPAND, fresh).
Forms/mutations/rest carry no related-set graph and import nothing
from this module (fresh census: importers are the list field's
deferred scope import, the leaf re-export, the deferred base/validator
reads, the factory, and the TYPE_CHECKING hook — withheld).
The write flavors' `type(...)` sites build different shapes
([dry-mutid][dry-mutid] R2 trigger checked; no shape token here).

**2. Sync/async twins.** Discharged by construction, not inapplicable:
ONE `async def` (`apply_async`) against its sync twin
(`apply_sync`), sharing the uncolored `_apply_orderings` tail —
the order side's answer to the twin's one-body-impossible split
(R-m3 records the contrast at both owners: the filter pair cannot
share one body around consumer `async get_queryset` awaits vs
`SyncMisuseError`; the order tail is pure sync construction, so the
colorings differ ONLY in the permission-wrap). Compared by
behavior: both normalize → flatten → resolve → annotate/order_by
identically (the tail is one body, called by both — C28 proves a
stage change touches one definition). The ledger's `threading.Lock`
covers the `sync_to_async` worker-thread copy case with no await
point of its own (verified against the body + the thread-oracle
pins). No twin drift is expressible: there is one tail.

**3. Derived rather than repeated knowledge.** Searched. Type names
via inherited `type_name_for` (0 definitions here — F-NAME);
`Meta.fields` via `read_set_meta_fields` (0 — the metaclass owns
the write-back, expansion never mutates); re-readability via the
gate (0); cache decisions via `expanded_once` +
`should_cache_expansion` (0); lifecycle tuple via `binding_attrs`
(0); traversal mechanics via `iter_active_fields` + the contained
config (0); path facts via `classify_path` / `_path_traverses_to_many`
(0); alias flattening via `flatten_lookup_path` (0 — the
`_dst_order_{index}_` prefix literal is the one local grammar,
F-RESOLVE); boundary discipline via `run_in_one_sync_boundary`
(0); renderings via the shared `_safe_*` helpers (composed by
name). The `__name__` / `__qualname__` reads at HEAD (10 sites) are
direct where the concurrent dirt adopts `_safe_class_name` —
judged at HEAD bytes throughout (dirt moves no definition).
No local re-derivation of any shared fact.

**4. Inverse / round-trip pairs.** Searched: no local pair with two
halves to twin. Publish/claim is one ledger's append/claim halves,
single-sited (F-LEDGER); normalize/validate is delegate-then-gate,
sequential, not inverse (F-NORMDEL/F-VALIDATE); `_build`/cache is
one expansion with its gate (F-EXPAND); attest/guard is the
handoff's two ends across the list-field boundary (F-LEDGER +
F-ACTIVE, one rule). `Ordering.resolve` is encode-only (no decode
exists — the inputs artifact's census stands, re-checked: `resolve(`
consumers only here). `materialize`/clear live in
[orders-inputs][orders-inputs], not here. No second half anywhere
in the target.

**5. Contracts restated in another medium.** Searched. Four media
carry this file's contracts: production code (definitions here,
machinery at the owners); authoritative contract sources
([spec-028][spec-028] Decisions 2/3/5/6/8/12/13, DoD 4, Edge cases,
plus [spec-030][spec-030] Decision 11 — each cited decision read
and checked against the body; D1/D2/D3 record the three cites
that fail); independent oracles ([test-order-sets][test-order-sets]:
90 tests spelling literals — member lists, message fragments,
`co_names` composition pins, thread/task/close proofs — plus the
live `orderBy` population over 13 `test_query` modules incl. the
combined no-op test and the to-many SQL pins; none reads an owner
body to compute expectations); projections (module/class/function
docstrings — verified claim by claim below; cookbook-port notes —
verified against the running upstream with the D3 delta). A new
aggregate rule, a new expansion shape, or a new verdict moves the
def once; every medium follows (Challenges).

**6. Enforcement by omission.** Enumerated. Orders lacks the
dispatcher (DoD 4(c)), the bound `check_permissions` delegate
(R-m4), child-visibility derivation (R-m3; [dry-orders-base][dry-orders-base]
R1 trigger checked — zero queryset-derivation tokens here), the
operator bag + logic keys (Decision 8), the per-field `__all__`
branch (R-EXPAND), Layer-6 (Decision 12; zero Layer-6 tokens),
`on_reentry` (expansion never re-enters — verified: `_build`
never calls `get_fields`), `_field_type_suffix` (documented
divergence, F-NAME), `_MAX_LOGIC_DEPTH` (the traversal budget
resolves through `set_traversal_depth_cap`'s default — verified
at the owner), the seal (withheld: the wrappers own it; twin
withholds identically), and `model_for`/`base_queryset` (withheld:
direct `.model` reads on typed inputs). Every absence traces to a
contract source, a verified separation, or a no-source design
difference — no missing guard with a contract source behind it,
no omission defect filed.

### Enumeration

Instrument: `ast.parse` over the pinned HEAD blob, counting
`ast.Module.body` members — **31 top-level statements** — plus
every member of the four class bodies — **28 members**
(`_AppliedNormalization`: docstring + 3 fields;
`_NormalizationLedger`: docstring + `__slots__` + 4 methods;
`OrderSetMetaclass`: docstring + `__new__`; `OrderSet`: docstring
+ 5 attrs + 10 methods, 1 `async`). **33 named rule-bearing
members** in total (+ 1 nested `_build` closure counted within
its owner). Every member lands below; every challenge in
`### Challenges` ends in a family row, a file-local row, a
rejection, or a verified no-surface routing.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (port map + pipeline map) | (none) | prose projection, all findings (+ D3) |
| 1 | `from __future__ import annotations` | (boilerplate) | — |
| 2–20 | 19 imports (stdlib 7 + django/strawberry 2 + first-party 10) | 36 names (machinery) | per-finding consumer rows |
| 21 | `if TYPE_CHECKING:` guard | 1 name (type-only) | F-LIFE annotation |
| 22 | `_NormalizedTerms` alias | 1 name | F-LEDGER |
| 23 | `class _AppliedNormalization` + 3 fields | 4 names | F-LEDGER |
| 24 | `class _NormalizationLedger` + slots + 4 methods | 6 names | F-LEDGER (+ R-CLAIM for `claim`) |
| 25 | `_ORDER_NORMALIZATION_CAPTURE` | 1 name | F-LEDGER |
| 26 | `def capture_applied_order_normalization` | 1 name | F-LEDGER |
| 27 | `def _record_applied_normalization` | 1 name | F-LEDGER |
| 28 | `def _validate_normalized_terms` | 1 name | F-VALIDATE (+ R-m2) |
| 29 | `class OrderSetMetaclass` + `__new__` | 2 names | F-META (+ R-m4) |
| 30 | `class OrderSet` + 5 attrs + 10 methods | 16 names | F-EXPAND/F-ACTIVE/F-NORMDEL/F-PERM/F-FLAT/F-RESOLVE/F-APPLY/F-LIFE/F-NAME (+ R-m1/R-m3/R-EXPAND) |

Rules: R-ledger attestation handoff (22–27); R-validate return
gate (28); R-meta collect + bind (29); R-expand Layer-4 expansion
(`get_fields` + `_expand_meta_fields` + `_build`); R-active
guard check (`_input_has_active_terms`); R-normdel delegate
(`_normalize_input`); R-perm config + warm-up (`_permission` +
`_prepare_permission_input`); R-flat cookbook walk
(`get_flat_orders`); R-resolve expression builder
(`_resolve_order_expressions`); R-apply pipeline tail
(`_apply_orderings` + `apply_sync` + `apply_async`); R-life
binding slots (`_owner_definition` + `_expanded_fields` +
`_is_expanding_fields` + `_lifecycle`); R-name default naming
(inherited `type_name_for` + documented non-override). One new
family (F-PURITY: the B/C agreement verdicts), two convergences
onto existing rows (F-LIFE → verified
`subsystem-clear-lifecycle`; F-META/F-APPLY/F-EXPAND/F-RESOLVE
facets → open/verified families, transcribing nothing), eleven
file-local rows, seven rejections — all named for Worker 0
(see `## Index rows for Worker 0`).

### Challenges

Each change posited against the rule's own variation axes; the
count is authoritative definitions only. Consumers, oracles,
projections listed, never counted. All bodies judged at HEAD
bytes (the worktree dirt — target + connected — is
label-hardening/guard arms that move no definition and change no
count; details per finding).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-ledger claim | claim identity rule change (e.g. by value) | **1 here** (`claim`; scope/recorder/scopes follow) | independent |
| C2 | R-ledger closure | close semantics change (e.g. non-terminal) | **1 here** (`close` + scope `finally`; task/thread oracles follow) | independent |
| C3 | R-ledger shape | attestation shape change (new field) | **1 here** (record + publish + claim readers move together) | independent |
| C4 | R-purity verdict | verdict reword (B/C message) | **2 here** (the two adjacent agreement checks — identical skeletons) | **family F-PURITY** |
| C5 | R-purity compare | comparison change (e.g. multiset) | **2 here** (same two checks) | **family F-PURITY** |
| C6 | R-purity middle | inter-application diagnostic change | **1 here** (`claim` only — B/C untouched) | independent — proves R-CLAIM |
| C7 | R-validate shapes | accepted shape change (new term form) | **1 here** (both sets guards + normalizer check untouched — R-guards adopted) | independent |
| C8 | R-validate strictness | exact-type → `isinstance` | **1 here** (per-seam strictness; standing J2 trigger checked — no shared gate) | independent |
| C9 | R-meta policy | flip the inherit policy | **1 here** (call-site arg; collector owns the machinery) | independent |
| C10 | R-meta tombstone | tombstone/diamond rule change | **0 here, 1** at [sets-mixins][sets-mixins]`::collect_related_declarations` | independent — proves single ownership |
| C11 | R-meta promote | alias write-back change | **0 here** (pure read; owner moves once) | independent — proves declaration |
| C12 | R-expand publish | publish-contract change (snapshot/`base_filters`) | **0 shared** (each side keeps its own `_build`) | rejected-merge — proves R-m1 |
| C13 | R-expand selection | `__all__` selection change (admit M2M) | **0 here, 1** at [orders-inputs][orders-inputs] helper | independent — proves single ownership |
| C14 | R-expand branch | branch-structure/entry-gate change | **1 here** (model-require + loop + entry check) | independent |
| C15 | R-expand re-read | re-readability rule change | **0 here, 1** at the gate owner | independent — proves single ownership |
| C16 | R-expand merge | unify with filter `get_fields` narrowing | separation stands (R-EXPAND: self-derive vs upstream-narrow + no per-field branch) | rejected-merge |
| C17 | R-active sense | activeness change (None becomes an error) | **1 here** (resolve arm changes independently — polarity pair, no helper owed) | independent |
| C18 | R-active structure | claim/fallback structure change | **1 here** (the verdicts route to F-PURITY) | independent |
| C19 | R-normdel target | delegate-target change | **1 here** (3 intra-module callers follow) | independent |
| C20 | R-normdel obligation | purity-obligation change | **1 here** (prose; the 3 enforcers follow as family's + ledger's) | independent |
| C21 | R-perm config | traversal-axis change | **1 decl here, 0 mechanics** (walker owns them) | independent — proves declaration |
| C22 | R-perm warm-up | warm-up trigger change | **1 here** (no filter twin exists) | independent |
| C23 | R-flat shape | return-shape change | **1 here** (both intra-module callers follow) | independent |
| C24 | R-flat prefix | prefix-semantics change | **1 here** (0 production non-default callers — census) | independent |
| C25 | R-resolve aggregate | Min/Max rule change | **1 here** (sole production emission site) | independent |
| C26 | R-resolve alias | alias-prefix change | **1 here** (prefix literal; flatten rule 0 here/1 at owner) | independent |
| C27 | R-resolve guard | resolve-time guard change | **1 here** (R-guards seam (c); siblings untouched) | independent |
| C28 | R-apply stages | pipeline-stage change | **1 here** (the tail; both colorings follow) | independent |
| C29 | R-apply boundary | boundary-discipline change | **0 here, 1** at [utils-querysets][utils-querysets]`::run_in_one_sync_boundary` | independent — proves single ownership |
| C30 | R-apply dispatcher | add an `apply` dispatcher | **1 here** (negated: DoD 4(c) absence held — no equivalent code path) | independent — absence is the contract |
| C31 | R-life slot | new cached slot | **1 decl here** (+ the `binding_attrs` derivation at its owner) | independent |
| C32 | R-life clear | clear-contract change | **0 here, 1** (the bus + clear owner) | independent — proves convergence |
| C33 | R-name suffix | per-field suffix change | **1 here** (declaration by absence; add the override) | independent |
| C34 | R-ledger merge | unify ledger with `OperationLease` | separation stands (R-LEASE: mutable-ledger tombstone vs one-payload lease) | rejected-merge |

No executable proof was run: the target is declarations + thin
wrappers + single-predicate/single-walk functions whose every
behavior is pinned by the 90 read oracles in
[test-order-sets][test-order-sets] plus the live `orderBy`
population, and every census above is a byte-level `git grep`
over HEAD blobs or an `ast.parse` enumeration — all read-only,
none mutating, none capable of distinguishing anything the cited
oracles do not already pin. No `docs/dry/temp-tests/` scratch was
created. All claims below are therefore `static-reviewed`; there
is no `execution-deferred` proof.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site (convergences name
their holding family; rejections carry difference + trigger).

### F-LEDGER — invocation-scoped attestation handoff (file-local)

- **Contract + variation.** One list-field resolution's append-only
  record of applied normalizations: every public `apply_*` attests
  (class, input object, validated terms) into the active
  `ContextVar` ledger; the offset guard claims only the entries
  naming its own class + input object, once per pair; disagreeing
  attestations fail closed; closure is terminal (later publishes
  and claims inert). Legitimate variation: the attestation shape,
  the claim identity rule, and the closure semantics only.
- **Sites + roles.** *Definition*: this file's statements 22–27
  (alias, frozen record, ledger + lock, ContextVar, scope,
  recorder). *Publishers*: `_apply_orderings` (3 attestation
  points: term-less, expression-less, ordered — all call the one
  recorder). *Consumers*: [list-field][list-field]'s
  `_order_normalization_scope` (sole scope opener — verified
  census: 1 import + 1 call) and `_check_nonzero_offset_guard`
  (via `_input_has_active_terms`). *Oracles*: the attestation /
  claim-once / child-task / worker-thread / close-terminal tests
  — independent (they drive scopes and assert claim/raise/None,
  never read the ledger body). *Sibling separation*:
  [operation-lease][operation-lease]`::OperationLease` (a
  different rule — R-LEASE).
- **Challenges.** C1 → 1 here; C2 → 1 here; C3 → 1 here.
- **Owner + lifetime.** This ledger (existing owner by
  responsibility: the narrowest site the list field + guard can
  depend on without writing the consumer's context). Lifetime: one
  scope per qualifying request (ContextVar binding; validity key =
  the open scope; published by the scope opener; mutated by
  publishers under the lock; invalidated terminally by `close` +
  token reset in nested `finally`s — verified against the body).
- **Migration.** None (zero-edit item): single owner stands.
- **Distinct behavior.** Identity (`is`) matching on class + input
  is load-bearing (a consumer `__eq__` has no say — pinned by the
  identity oracles); the lock is load-bearing (worker-thread copy
  — pinned by the concurrent-publish oracle); the
  once-per-pair + terminal-close rules are load-bearing (pinned by
  the claim-once + outlived-scope oracles). All verified against
  the body + oracles.
- **Behavioral proof.** `static-reviewed`. Rejects "a slot would
  do" (the docstring's two-requirements argument + the
  child-task/unrelated-descendant oracles pin append-only +
  claim-by-identity) and "close need not clear" (the outlived-scope
  oracles pin terminal inertness + no retention).
- **Structural gate.** The pre-existing scope/claim/thread/close
  oracles (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` — the judged scope +
  recorder + close bodies are the HEAD bytes; the worktree
  `f09d9983…` dirt touches this finding ONLY at the `claim`
  disagreement message's class-name read (label swap, changes no
  count: predicate, loci, and message skeleton judged are the HEAD
  bytes), [list-field][list-field] HEAD
  `21380eb72364caef0da05ca3ee3f26c0134e3904` (worktree `f979f0d6…`
  validator hardening — outside the judged guard/scope region),
  [test-order-sets][test-order-sets] HEAD
  `9e9bb5d980a546e530ec84d248a8ac5e80e5ee05` (worktree `d8cb5bdb…`
  appended hostile tests — outside the judged ledger oracles),
  HEAD `5ee86193`.
- **Rejection (nested R-LEASE).** Considered: unify the ledger
  with [operation-lease][operation-lease]`::OperationLease` into
  one terminal-closure rule (the lease docstring itself names this
  ledger as "the same rule written for one subsystem" — compared
  fresh here against both bodies, not inherited). Contract
  difference here: append-only multi-record ledger tombstoned
  under its own lock because a descendant may still be publishing
  into it (publish/claim/close + identity matching + once-per-pair
  + disagreement verdict) vs a one-payload handle whose close is a
  single store and whose only answer after close is "nothing" —
  different state shapes, different close mechanics, opposite
  change responses (C34: a payload-read change moves the lease
  only; a claim-identity change moves this file only). Same
  insight, not the same rule. CONVERGE with the owner-recorded
  separation on fresh evidence (both bodies still match the stated
  reason at HEAD). Trigger to reconsider: the ledger collapsing
  to a single payload (no append, no claim matching). Durable
  home: the lease docstring (already states the split) + this
  artifact. Named for Worker 0 as rejected index row
  `orders-ledger-vs-operation-lease`.

### F-PURITY — guard agreement verdict (NEW FAMILY `active-terms-purity-agreement`)

- **Contract + variation.** The active-terms guard's two-term
  agreement check: two term readings for one (class, input) that
  disagree fail closed with the not-pure `ConfigurationError`
  naming `_normalize_input`. Legitimate variation: the verdict
  (type + wording) and the comparison only — the operand
  selection stays per path by construction.
- **Sites + roles.** *Definitions*: this file's TWO adjacent
  agreement checks inside `_input_has_active_terms` — the
  ledger-path check (attested terms vs one fresh read) and the
  fallback-path check (two fresh reads) — byte-identical message
  skeletons 8 lines apart in one method (verified byte for byte:
  same prefix, same middle, same suffix shape; only the two repr
  operands differ). *Callers*: the guard's two arms (operand
  selection per arm). *Oracles*: the purity/purity-structure/
  sequence-controls tests — independent (they drive disagreeing
  normalizations and match the verdict, never read the checks).
  *Excluded sibling*: `claim`'s disagreement verdict (a different
  event — R-CLAIM).
- **Challenges.** C4 → 2 here (a reword moves both); C5 → 2 here
  (a comparison change moves both). Count 2 = duplication: the
  messages are identical because the author considers the two
  paths the same check (had the paths been diagnostically
  distinct, the messages would differ — as `claim`'s does).
- **Owner + lifetime.** TBD by the family item. Candidates: the
  guard method itself (restructure to select operands then check
  once — no helper needed, same normalization counts, same walk
  targets), or a module verdict helper both arms call. No stored
  derivation; per-guard-call lifetime either way.
- **Migration.** None in this item (zero-edit): the family item
  decides the shape (restructure vs helper) with permanent tests
  at the mandated tier.
- **Distinct behavior.** The operand pairs stay per arm
  (attested-vs-fresh vs fresh-vs-fresh — forced by which readings
  each path holds); only the verdict + comparison unify. The
  `claim` verdict stays ledger-owned (R-CLAIM).
- **Behavioral proof.** `static-reviewed`. Rejects "the two arms
  check different contracts" (same inputs — two term lists; same
  output — None or raise; same error — identical skeleton; same
  timing, hooks, and reasons to change: the disproof attempt in
  `### Challenges` C4/C5 found no difference) and "unification
  needs machinery" (the operand-select-then-check restructure
  shares the verdict with no helper).
- **Structural gate.** None owed here (zero-edit file item; the
  family item owns any future gate). Pre-existing pins the family
  item inherits: the purity/disagreement/sequence oracles.
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` — the judged checks are
  the HEAD bytes INCLUDING both `cls.__name__` label reads; the
  worktree `f09d9983…` dirt replaces exactly those two reads with
  the `_safe_class_name` adoption (concurrent-external, changes no
  count: skeletons, predicates, and adjacency judged are the HEAD
  bytes), [test-order-sets][test-order-sets] HEAD `9e9bb5d9…`
  (dirt as F-LEDGER — outside the judged purity oracles),
  HEAD `5ee86193`. Searched population for a fourth not-pure
  raiser: `is not pure` package-wide — exactly these two + `claim`
  (tests match as oracles).
- **Rejection (nested R-CLAIM).** Considered: include `claim`'s
  disagreement verdict in the family (same "is not pure" verdict
  family, same exception type). Contract difference here: `claim`
  detects INTER-application disagreement (two attestations for
  one pair, possibly from different tasks/threads) and its middle
  names that event ("two applications of the same input in one
  resolution"), while the family detects guard-time read
  disagreement with the same-input middle — different events,
  different diagnostic information (cross-task vs local
  nondeterminism), different owning class (ledger claim integrity
  vs guard agreement). Unifying the middles would lose the
  distinction; parameterizing it couples the ledger to the guard
  over verdict wording (the per-message-grammars class: each
  message renders its own event). C6 proves the split (an
  inter-application reword moves `claim` only). Trigger to
  reconsider: the three events collapsing to one diagnostic (e.g.
  the ledger retiring, leaving one guard). Durable home: the two
  existing message sites (each already states its own event) +
  this artifact. Named for Worker 0 as rejected index row
  `orders-ledger-claim-vs-guard-agreement`.

### F-VALIDATE — normalize return-contract gate (file-local)

- **Contract + variation.** `_validate_normalized_terms`
  enforces the `_normalize_input` return contract at the pipeline
  boundary: a list of 2-tuples of (`str`, `Ordering | None`),
  every shape pinned by EXACT type (a `list` subclass would run
  consumer `__iter__`, a `tuple` subclass `__len__`/`__getitem__`,
  a `str` subclass `__eq__`/`__format__`), the container rejected
  before iteration and each term before its members are read, so
  everything downstream runs on trusted primitives. Legitimate
  variation: the accepted shapes + the strictness only.
- **Sites + roles.** *Definition*: this file's statement 28.
  *Consumers*: `_input_has_active_terms` (2 calls) +
  `_apply_orderings` (1 call) — single definition, three
  intra-module consumers. *Sibling seams*: the normalizer leaf
  check ([orders-inputs][orders-inputs]) + the resolve-time guard
  (F-RESOLVE) — the adopted three-seam split (existing rejected
  row `orders-normalize-check-vs-resolve-guards` already lists
  this file; adopted, no new row). *Oracles*: the hostile
  container/string-subclass + validation-contract tests —
  independent (they drive hostile values and assert typed
  rejection, never read the gate).
- **Challenges.** C7 → 1 here (siblings untouched); C8 → 1 here
  (standing J2 exact-type-gate trigger checked fresh: per-seam
  strictness with per-seam messages, no shared gate — the two
  exact-type sites in THIS file, here + the F-EXPAND entry check,
  guard different seams with different subjects).
- **Owner + lifetime.** This function (existing owner by
  responsibility: the pipeline-boundary gate). No stored
  derivation.
- **Migration.** None.
- **Distinct behavior.** Exact-`type()` (not `isinstance`) is the
  load-bearing hostile-subclass discipline — the resolve-time
  guard's `isinstance` is deliberately lenient (garbage-shape
  rejection for post-boundary injection, where the injector is
  the consumer's own override; F-RESOLVE records the split).
- **Behavioral proof.** `static-reviewed`. Rejects "a subclass
  passes" (exact-type + hostile oracles pin the loud path) and
  "downstream re-checks" (every downstream reader trusts the
  validated primitives — C7 proves a shape change moves this
  gate only).
- **Structural gate.** The pre-existing hostile + contract oracles
  (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` — the judged predicate +
  skeletons are the HEAD bytes; the worktree `f09d9983…` dirt
  touches this finding's two messages at the class-label reads
  only (changes no count), twin normalizer [filters-sets][filters-sets]
  HEAD `722e0c77…` (dirt as System trace — outside the judged
  `_normalize_input`), [orders-inputs][orders-inputs] HEAD
  `6f6ec946…` (dirt as System trace — outside the judged leaf
  check), [test-order-sets][test-order-sets] HEAD `9e9bb5d9…`
  (dirt as F-LEDGER — outside the judged gate oracles).
- **Rejection (nested R-m2).** Considered: unify with
  [filters-sets][filters-sets]`::FilterSet._normalize_input` into
  one normalize pass (the verified filters artifact rejected the
  same candidate as R-m2; compared fresh here at HEAD bodies, not
  inherited). Contract difference here: this side delegates the
  walk to [orders-inputs][orders-inputs]`::normalize_input_value`
  (flat pair-list emission with branch recursion + direction
  check) and gates the RETURN here (exact-type hostile-subclass
  discipline), while the twin walks `iter_active_fields` itself
  and dispatches three `ActiveField` kinds (LOGIC wire-copy +
  RELATED strip + LEAF operator-bag/range normalization) into a
  form-data dict — different signatures, different returns,
  opposite recursion (recurse vs strip), opposite change responses
  (C7/C19: either normalize contract moves its own side only).
  CONVERGE with verified filters R-m2 on fresh evidence (the twin
  body + this body both match the recorded difference at HEAD).
  Trigger to reconsider: a change to one side's normalize
  contract that must move the other. Durable home: the two
  normalizer docstrings (each already states its own contract) +
  this artifact. Named for Worker 0 as rejected index row
  `orders-normalizer-vs-filter-normalizer`. (The inputs-level pair
  is separately covered by existing rows
  `orders-normalize-vs-filter-normalize` and W2's
  `orders-normalize-vs-filterset-normalize` — adopted, no new row.)

### F-META — declaration metaclass (file-local)

- **Contract + variation.** `OrderSetMetaclass.__new__` builds the
  class, resolves `Meta.fields` through the shared write-back
  (pure read — no cookbook synonym), and collects `RelatedOrder`
  declarations with MRO-merge + owner bind through the shared
  collector. Legitimate variation: the inherit policy + the
  declaration type + the alias posture only.
- **Sites + roles.** *Definition*: this file's statement 29 (the
  two call sites + their arguments). *Machinery owners*:
  [utils-inputs][utils-inputs]`::promote_set_meta_fields`
  (write-back) + [sets-mixins][sets-mixins]`::collect_related_declarations`
  (collect + bind). *Consumers*: every `OrderSet` subclass
  (glossary/kanban/library declarations verified by census).
  *Sibling definition*:
  [filters-sets][filters-sets]`::FilterSetMetaclass` (a different
  construction contract — R-m4). *Oracles*: the
  collect/override/bind/diamond tests — independent (they build
  classes and assert maps, never read the collector).
- **Challenges.** C9 → 1 here (policy arg); C10 → 0 here / 1 at
  the collector; C11 → 0 here (pure read — the owner moves once).
- **Owner + lifetime.** This metaclass for the call-site policy
  (existing owner); the collector + promote owners for the
  machinery (existing owners). Runs once per class creation.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed`. Rejects "the metaclass
  spells collection" (one collector call; C10 proves a tombstone
  change touches one definition) and "expansion could mutate
  Meta" (the write-back lives here alone; F-EXPAND reads without
  mutation — pinned by the `co_names` oracle).
- **Structural gate.** The pre-existing construction oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` (the worktree dirt does
  NOT touch this finding's lines — verified by the item diff),
  collector + promote owners [sets-mixins][sets-mixins] HEAD
  `ad8987ea…` / [utils-inputs][utils-inputs] HEAD `ee31d360…`
  (dirt as System trace — no definition moved, no count affected),
  twin metaclass [filters-sets][filters-sets] HEAD `722e0c77…`
  (dirt as System trace — outside the judged metaclass),
  [orders-base][orders-base] HEAD `4736fda0…` (dirt as System
  trace — outside the judged slot/bind lines),
  [test-order-sets][test-order-sets] HEAD `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged construction oracles).
- **Rejection (nested R-m4).** Considered: unify with the twin
  metaclass into one set metaclass (the verified filters artifact
  rejected the same candidate as R-m4; compared fresh here at HEAD
  bodies, not inherited). Contract difference here: plain
  `type` vs django-filter subclass; `inherit_from_bases=True`
  over class-body attrs vs `False` over the declared stream;
  no tombstone rebuild + no declared-provenance stamp (filter-only);
  no `apply` dispatcher + no `check_permissions` delegate
  (filter-only — verified absent: zero `def apply` / `def
  check_permissions` in this file's 10 methods); the order-only
  `_prepare_permission_input` warm-up (F-PERM) has no twin.
  Opposite change responses (C9: either construction contract
  moves its own side only). CONVERGE with verified filters R-m4
  on fresh evidence. Trigger to reconsider: a change to one
  side's construction contract that must move the other. Durable
  home: the metaclass docstrings (each already states its own
  policy) + this artifact. Named for Worker 0 as rejected index
  row `orders-metaclass-vs-filter-metaclass`.
- **Convergence (no new row).** The `promote_set_meta_fields`
  call is the write-back-sharer facet of OPEN family
  `dynamic-set-class-getter`, whose files-covered already lists
  this file (factories F-2 recorded the call site; re-verified
  fresh: pure read, `fields_alias=None`). Holding item is the
  open family.

### F-EXPAND — Layer-4 fields expansion (file-local)

- **Contract + variation.** `get_fields` returns the `Meta.fields`
  expansion merged with `related_orders` under the shared
  cache + guard skeleton with the two-condition cache-write gate;
  `_expand_meta_fields` expands list/tuple/set/frozenset/dict-key
  declarations plus the `"__all__"` shorthand (column-backed
  names via the inputs helper, model required), enforcing the
  re-readability contract and the field-name-string entry gate.
  Legitimate variation: the publish shape + the branch structure
  + the entry gate only.
- **Sites + roles.** *Definition*: this file's `get_fields` (+
  nested `_build`) + `_expand_meta_fields`. *Machinery owners*:
  [sets-mixins][sets-mixins]`::expanded_once` (skeleton) +
  `::should_cache_expansion` (gate) +
  `::require_re_readable_field_declaration` (shape gate) +
  [utils-inputs][utils-inputs]`::read_set_meta_fields` (reader).
  *Selection owner*: [orders-inputs][orders-inputs]`::_get_concrete_field_names_for_order`
  (the predicate; this file owns the model-require + loop).
  *Consumers*: the BFS hook body (reads `get_fields` — verified
  call site), the finalizer subpass 2 (expansion drive), the
  permission traversal (related map). *Sibling definitions*: the
  twin `_build` (R-m1) + the twin `get_fields` narrowing (R-EXPAND).
  *Oracles*: the merge/cache/no-cache/`__all__`/entry-gate/
  re-readability/dict-shape tests + the `co_names` composition
  pins — independent (they drive declarations and spell maps,
  never read the skeleton).
- **Challenges.** C12 → 0 shared (R-m1); C13 → 0 here / 1 at the
  helper; C14 → 1 here; C15 → 0 here / 1 at the gate; C16 →
  rejected (R-EXPAND).
- **Owner + lifetime.** These methods for the expansion shape
  (existing owner); the skeleton/gate/reader owners for the
  machinery (existing owners). Cache lives to `registry.clear()`
  (via F-LIFE); the guard lives one `_build` call.
- **Migration.** None.
- **Distinct behavior.** No `on_reentry` is load-bearing AND
  correct: `_build` never calls `get_fields` (verified — it calls
  `_expand_meta_fields` + reads the related map), so the order
  expansion cannot re-enter and the filter's self-referential
  fallback has no analogue. The entry-type gate is unconditional
  (model or no model — pinned by both oracles). Dict shapes
  degrade to their keys (django-filter lookup-bag shape walks in,
  field names walk out — pinned).
- **Behavioral proof.** `static-reviewed`. Rejects "a subclass
  inherits the cache" (own-`__dict__` read — pinned by the
  no-cache oracle) and "a one-shot declaration expands twice"
  (re-readability gate — pinned by the iterator/hostile oracles).
- **Structural gate.** The pre-existing expansion + gate oracles
  (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` — the judged skeleton
  call + branch structure are the HEAD bytes; the worktree
  `f09d9983…` dirt touches this finding at the `__all__` gate
  (new `BaseException` arm) + three message label reads (changes
  no count: gate predicate, branch order, and skeletons judged
  are the HEAD bytes), skeleton/gate/reader owners
  `ad8987ea…` / `ee31d360…` (dirt as System trace — no definition
  moved), helper [orders-inputs][orders-inputs] `6f6ec946…` (dirt
  as System trace — outside the judged helper),
  [orders-factories][orders-factories] `4f35b66b…` (clean; BFS
  consumer), twin [filters-sets][filters-sets] `722e0c77…` (dirt
  as System trace — outside the judged builds),
  [test-order-sets][test-order-sets] `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged expansion oracles).
- **Rejection (nested R-m1).** Considered: unify the two
  expansion `_build` closures into one shared build (the verified
  filters artifact rejected the same candidate as R-m1; compared
  fresh here at HEAD bodies, not inherited). Contract difference
  here: this `_build` merges meta fields + related orders (no
  snapshot, no `base_filters`, no reentry arm) while the twin's
  expands related graphs + freezes candidate metadata + publishes
  the snapshot + writes `base_filters` — different publish
  populations, opposite change responses (C12: either publish
  contract moves its own side only). The skeleton + gate sharing
  is the only common mechanism (already single-sited).
  CONVERGE with verified filters R-m1 on fresh evidence. Trigger
  to reconsider: a change to one side's publish contract that
  must move the other. Durable home: the `_build` closures (each
  already states its own publish) + this artifact. Named for
  Worker 0 as rejected index row
  `orders-expansion-build-vs-filter-publish`.
- **Rejection (nested R-EXPAND).** Considered: unify
  `_expand_meta_fields` with
  [filters-sets][filters-sets]`::FilterSet.get_fields` into one
  `Meta.fields` expansion (same "expand Meta.fields" shape —
  fresh candidate, no prior verdict names this pair). Contract
  difference here: this method SELF-DERIVES (list/tuple/set/
  dict-key branches + `"__all__"` via the column-backed helper,
  model optional, entry-type gate unconditional) while the twin
  NARROWS upstream (`super().get_fields()` + per-field
  `"__all__"` expansion via `_lookups_for_field` + top-level
  sweep PK-add/M2M-remove) — different mechanisms, different
  branch sets (no per-field `"__all__"` exists on the order side:
  a dict VALUE of `"__all__"` degrades to its key here and
  expands to lookups there), opposite change responses (C16: a
  per-field change moves the twin only; an entry-gate change
  moves this file only). Same token, not the same rule. Trigger
  to reconsider: both families expanding through one shared
  Meta-reader (today they share only the re-readability gate,
  already single-sited). Durable home: the two method docstrings
  (each already states its own branches) + this artifact. Named
  for Worker 0 as rejected index row
  `orders-expand-vs-filter-fields-narrow`.
- **Convergences (no new rows).** (a) The BFS hook body reads
  `get_fields` — a consumption facet of OPEN family
  `set-arguments-factory-bfs` (which does NOT list this file:
  the walk/collision/cache live at the base with zero tokens
  here — correctly absent, not membership). (b) The two
  `classify_path` reads are consumer facets of VERIFIED family
  `orm-lookup-path-resolution` (owner `classify_path`; this
  file reads it twice with per-seam wraps — the wrap skeleton
  is shared idiom, the messages per-seam per the
  per-message-grammars class; extraction would be machinery).

### F-ACTIVE — offset-guard active-terms check (file-local)

- **Contract + variation.** `_input_has_active_terms` returns
  whether the input carries at least one non-`None` direction:
  it claims the attested terms when the ledger holds them
  (checking purity against the attestation), else falls back to
  two independent normalizations (checking purity between them),
  then walks the surviving terms for any live direction.
  Legitimate variation: the activeness sense + the
  claim/fallback structure only (the verdicts route to F-PURITY).
- **Sites + roles.** *Definition*: this file's
  `_input_has_active_terms` minus the two F-PURITY verdicts (the
  claim call, the fallback second normalization, the `any()` walk).
  *Consumer*: [list-field][list-field]'s `_check_nonzero_offset_guard`
  (sole production caller — verified census). *Oracles*: the
  active-terms contract/purity/sequence/identity tests —
  independent (they drive inputs and assert booleans/raises,
  never read the check).
- **Challenges.** C17 → 1 here (the `direction is not None` arm;
  the F-RESOLVE `direction is None: continue` arm is the opposite
  polarity of the same None-means-absent semantic — two natural
  enforcement spellings of a 3-token check, not two definitions:
  a shared `is_active_direction` helper would be machinery per
  principle 11); C18 → 1 here (structure; verdicts route out).
- **Owner + lifetime.** This method (existing owner by
  responsibility: the guard's check). Per-guard-call lifetime;
  no stored derivation.
- **Migration.** None.
- **Distinct behavior.** The ledger path costs one fresh
  normalization (two total with apply's), the fallback two
  (three total) — the docstring's counts verified against the
  body arm by arm. An already-claimed pair takes the fallback
  (verified: `claim` returns `None` for claimed pairs).
- **Behavioral proof.** `static-reviewed`. Rejects "the guard
  re-normalizes what apply ordered by" (it claims the attestation
  when one exists — pinned by the sequence-controls oracles) and
  "an unrelated application pollutes the check" (claim-by-identity
  + the never-claimed oracles).
- **Structural gate.** The pre-existing active-terms oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` — the judged structure +
  `any()` walk are the HEAD bytes; the worktree `f09d9983…` dirt
  touches this finding ONLY at the two F-PURITY label reads
  (judged in F-PURITY), [list-field][list-field] HEAD
  `21380eb7…` (dirt as F-LEDGER — outside the judged guard),
  [test-order-sets][test-order-sets] HEAD `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged oracles).

### F-NORMDEL — normalize delegate + purity contract (file-local)

- **Contract + variation.** `_normalize_input` delegates to
  [orders-inputs][orders-inputs]`::normalize_input_value` and
  carries the purity-obligation prose: the method must be a pure,
  deterministic function of its input (apply normalizes once,
  the guard checks against the attestation or two fresh reads;
  disagreement raises naming this method). Legitimate variation:
  the delegate target + the obligation text only.
- **Sites + roles.** *Definition*: this file's one-line body +
  its docstring (the narrowest seam all three purity enforcers —
  `claim`, guard ledger-path, guard fallback — name). *Consumers*:
  `_input_has_active_terms` (2 calls) + `_apply_orderings` (1
  call). *Delegate owner*: the inputs normalizer (leaf semantics
  + recursion). *Oracles*: the delegate test (pins the call) +
  every purity oracle (pins the obligation) — independent.
- **Challenges.** C19 → 1 here (target); C20 → 1 here (prose;
  the enforcers follow as F-PURITY's + F-LEDGER's).
- **Owner + lifetime.** This method (existing owner: the seam).
  No stored derivation.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed`. Rejects "the delegate
  adds semantics" (one call, args passed through — pinned) and
  "the obligation is aspirational" (three enforcers + oracles
  pin every stated count and verdict).
- **Structural gate.** The pre-existing delegate + purity oracles
  (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` (the worktree dirt does
  NOT touch this finding's lines — verified by the item diff),
  delegate [orders-inputs][orders-inputs] HEAD `6f6ec946…` (dirt
  as System trace — outside the judged normalizer),
  [test-order-sets][test-order-sets] HEAD `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged oracles).

### F-PERM — permission config + warm-up hook (file-local)

- **Contract + variation.** `_permission` configures the shared
  facade for the order family (`family_label`, `target_attr`,
  and the contained traversal: order `_field_specs` by reference,
  `related_orders`, `UNSET`, top-level-list handling, no logic
  keys); `_prepare_permission_input` warms the lazy field specs
  before the facade traverses. Legitimate variation: the config
  values + the warm-up trigger only.
- **Sites + roles.** *Declarations*: this file's `_permission`
  attr + `_prepare_permission_input` (the mixin's family hook).
  *Machinery owners*: [sets-mixins][sets-mixins]`::ActiveInputPermissionMixin`
  (facade) + [input-values][input-values]`::iter_active_fields`
  (walk). *Consumers*: `apply_sync` / `apply_async` (via
  `_run_permission_checks`) + the facade recursion. *Oracles*:
  the permission dispatch/dedup/inactive-branch tests —
  independent (they drive inputs and assert gate fire/quiet,
  never read the facade). No filter twin for the warm-up
  (filters build specs at bind — verified absence).
- **Challenges.** C21 → 1 declaration here / 0 mechanics (a sixth
  traversal axis moves the walker once); C22 → 1 here (no twin
  exists — the filters side needs none).
- **Owner + lifetime.** This file for the config values (existing
  owner); the mixin + walker for the mechanics (existing owners).
  Config lives on the class; specs warm at most once per class
  per generation (reset via F-LIFE's clear row).
- **Migration.** None.
- **Behavioral proof.** `static-reviewed`. Rejects "the config
  copies the traversal" (it CONTAINS the traversal object — the
  mixin reads it by reference, verified) and "direct calls skip
  provenance" (the hook warms before traversal — pinned by the
  direct-mapping oracle).
- **Structural gate.** The pre-existing permission oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` (the worktree dirt does
  NOT touch this finding's lines — verified by the item diff),
  facade [sets-mixins][sets-mixins] HEAD `ad8987ea…` (dirt as
  System trace — outside the judged facade),
  [input-values][input-values] HEAD `f2566609…` (dirt as System
  trace — outside `SetInputTraversal`),
  [orders-inputs][orders-inputs] HEAD `6f6ec946…` (dirt as System
  trace — outside `_field_specs` / `_ensure_field_specs`),
  twin config [filters-sets][filters-sets] HEAD `722e0c77…`
  (dirt as System trace — outside the judged declaration),
  [test-order-sets][test-order-sets] HEAD `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged oracles).

### F-FLAT — cookbook flat walk (file-local)

- **Contract + variation.** `get_flat_orders` walks normalized
  `(field_path, direction)` pairs into flat tuples, re-applying
  `prefix` per element: a pass-through over pre-walked data (the
  cookbook's recursion moved to the normalizer; DISTINCT ON
  dropped per Decision 12; pair shape per Decision 5). Legitimate
  variation: the return shape + the prefix semantics only.
- **Sites + roles.** *Definition*: this file's `get_flat_orders`.
  *Consumers*: `_input_has_active_terms` + `_apply_orderings`
  (both pass pre-walked data with the default empty prefix —
  verified: zero production non-default-prefix callers; the
  prefix is a documented cookbook-symmetry extension point).
  *Oracles*: the walk/prefix tests — independent (they spell
  pairs and assert tuples). *Upstream shape*:
  `django_graphene_filters/orderset.py::AdvancedOrderSet.get_flat_orders`
  (recursive mapping walk returning `(flat, distinct)` string
  lists — external, never a second definition; the two
  adaptations + the recursion relocation are documented at the
  owner and verified against both bodies).
- **Challenges.** C23 → 1 here (both callers follow); C24 → 1
  here (prefix semantics; unexercised in production by design —
  the test pin + docstring carry it, no defect: a defaulted
  extension point with a stated rationale is not dead code).
- **Owner + lifetime.** This method (existing owner by
  responsibility: the flat-walk rule). Per-call lifetime; no
  stored derivation.
- **Migration.** None.
- **Distinct behavior.** `None` directions pass THROUGH here
  (the filtering lives at F-RESOLVE + F-ACTIVE — the spec Edge
  case's "skipped in `get_flat_orders`" locus sentence is stale
  as to the locus but identical as to the wire behavior; noted
  under D1 as spec-side context, not a target defect).
- **Behavioral proof.** `static-reviewed`. Rejects "the walk
  filters" (pure append — pinned by the walk oracle carrying a
  `None` direction through) and "callers pre-prefix" (both pass
  the default — verified call sites).
- **Structural gate.** The pre-existing walk/prefix oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` (the worktree dirt does
  NOT touch this finding's lines — verified by the item diff),
  cookbook `orderset.py` (read-only port check; out-of-population
  source), [spec-028][spec-028] `94a3141c…` (clean; Decisions
  5/12), [test-order-sets][test-order-sets] HEAD `9e9bb5d9…`
  (dirt as F-LEDGER — outside the judged oracles).

### F-RESOLVE — order-expression resolver (file-local)

- **Contract + variation.** `_resolve_order_expressions` builds
  `(annotations, order_expressions)` from flat pairs against the
  concrete `queryset.model`: `None` directions filtered; every
  direction `isinstance`-checked; every path pre-validated via
  `classify_path`; to-many paths ordered by a `Min`/`Max`
  aggregate annotation (picked by `is_ascending`) aliased
  `_dst_order_{index}_{flattened}`, scalar/to-one paths ordered
  directly via `direction.resolve(...)`. Legitimate variation:
  the aggregate rule + the alias prefix + the guards only.
- **Sites + roles.** *Definition*: this file's
  `_resolve_order_expressions` (sole production emission site of
  the Min/Max aggregate + the `_dst_order_` alias — verified
  census). *Consumers*: `_apply_orderings` (sole production
  caller); [list-field][list-field]'s `_APPROVED_ORDER_AGGREGATES`
  recognizes the emission (consumer, not a second definition).
  *Mechanics owners*: `Ordering.is_ascending` / `::resolve`
  ([orders-inputs][orders-inputs]), `classify_path` /
  `path_traverses_to_many` ([utils-relations][utils-relations]),
  `flatten_lookup_path` ([utils-strings][utils-strings]).
  *Sibling seams*: R-guards seam (c) (existing rejected row
  already lists this file; adopted). *Oracles*: the aggregate/
  scalar/path/direction tests + the live to-many SQL pins —
  independent (they spell paths and assert annotations/SQL,
  never read the resolver).
- **Challenges.** C25 → 1 here (aggregate rule); C26 → 1 here
  (prefix literal) + 0 here / 1 at the flatten owner; C27 → 1
  here (resolve-time guard; R-guards siblings untouched).
- **Owner + lifetime.** This method (existing owner by
  responsibility: the expression-building rule). Per-apply
  lifetime; no stored derivation.
- **Migration.** None.
- **Distinct behavior.** `model=queryset.model` (not `Meta.model`)
  is load-bearing per Decision 8 step 7 (model-less sets +
  descendant application — pinned by both oracles). `isinstance`
  (not exact-type) is load-bearing leniency: this guard rejects
  garbage SHAPES injected post-boundary (strings, ints — pinned),
  while hostile SUBCLASSES are the boundary's (F-VALIDATE) threat
  — the injector here is the consumer's own override, which
  gains no privilege (it could override this method directly).
  The other `order_by(` sites (connection cursor/default,
  optimizer window/fetch) answer different contracts (cursor
  stability, declared config, window math — verified bodies),
  never consumer directions.
- **Behavioral proof.** `static-reviewed`. Rejects "a to-many
  path fans out" (aggregate + annotation — pinned by the SQL
  oracles) and "a bad path reaches Django" (pre-validation —
  pinned by the invalid-path oracles).
- **Structural gate.** The pre-existing resolver + live SQL
  oracles (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` — the judged aggregate
  + alias + guard structure are the HEAD bytes; the worktree
  `f09d9983…` dirt touches this finding's two messages at the
  class-label reads only (changes no count), mechanics owners
  [orders-inputs][orders-inputs] `6f6ec946…` /
  [utils-relations][utils-relations] HEAD
  `7662b0bb669c4dfba4a437f3b8f309357f718dca` /
  [utils-strings][utils-strings] `3ec3b262…` (dirt as System
  trace — no definition moved, no count affected),
  [list-field][list-field] `21380eb7…` (dirt as F-LEDGER —
  outside the judged aggregate set),
  [test-order-sets][test-order-sets] `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged oracles).
- **Convergence (no new row).** The `classify_path` +
  `_path_traverses_to_many` reads are consumer facets of VERIFIED
  family `orm-lookup-path-resolution` (same posture as F-EXPAND).

### F-APPLY — resolver pipeline tail + colorings (file-local)

- **Contract + variation.** `_apply_orderings` is the uncolored
  tail (normalize → gate → empty-out → flatten → resolve →
  conditional annotate → `order_by`, term-less inputs returned
  unchanged); `apply_sync` runs request + permission checks then
  the tail; `apply_async` runs request + the permission checks
  inside the one sync boundary then the tail. Legitimate
  variation: the pipeline stages + the coloring split only.
- **Sites + roles.** *Definition*: this file's three methods (one
  tail, two thin colorings). *Consumers*:
  [utils-querysets][utils-querysets]`::apply_orderset_sync` /
  `::apply_orderset_async` (the field-facing wrappers + seal),
  entered by [list-field][list-field] + [connection][connection];
  direct consumer calls. *Boundary owner*:
  [utils-querysets][utils-querysets]`::run_in_one_sync_boundary`.
  *Sibling definitions*: the twin apply pair (R-m3). *Oracles*:
  the sync/async/dedup/empty/no-op/UNSET tests + the live
  `orderBy` population — independent (they drive inputs and
  assert querysets/wire rows, never read the tail).
- **Challenges.** C28 → 1 here (the tail; both colorings follow —
  a stage change touches one definition); C29 → 0 here / 1 at
  the boundary owner; C30 → absence held (no dispatcher: DoD
  4(c) verified; the filter sync-misuse path has no order
  equivalent — verified zero queryset-derivation tokens).
- **Owner + lifetime.** These methods (existing owner by
  responsibility: the resolver pipeline). Per-apply lifetime; no
  stored derivation.
- **Migration.** None.
- **Distinct behavior.** The tail is NOT wrapped in the boundary
  (pure parsing + lazy queryset construction — no I/O; verified:
  zero queryset-evaluation tokens in the target) while the
  permission pass IS (consumer hooks may block) — the split
  Decision 8's dispatch paragraph pins. Observation (below the
  bar, not a defect): the tail docstring's "mirror of the
  filter split" parenthetical is loose — the order side has one
  tail, not a prelude/finalize split — but the sentence's subject
  (the shared body) + the enumerated pipeline make the actual
  shape self-correcting within the docstring.
- **Behavioral proof.** `static-reviewed`. Rejects "the colorings
  can drift" (one tail, called by both — C28) and "a term-less
  input reorders" (two early returns + the empty/no-op oracles).
- **Structural gate.** The pre-existing apply + live oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` (the worktree dirt does
  NOT touch this finding's lines — verified by the item diff),
  boundary + wrappers [utils-querysets][utils-querysets] HEAD
  `b68be0e337d178fc703ca1ac2ff4144c1fd766a5` (worktree `799139be…`
  hunks outside the judged bodies), twin pair
  [filters-sets][filters-sets] HEAD `722e0c77…` (dirt as System
  trace — outside the judged pipeline), [spec-028][spec-028]
  `94a3141c…` (clean; Decision 8 + DoD 4(c)),
  [test-order-sets][test-order-sets] HEAD `9e9bb5d9…` (dirt as
  F-LEDGER — outside the judged oracles).
- **Rejection (nested R-m3).** Considered: unify with the twin
  apply pair into one apply body (the verified filters artifact
  rejected the same candidate as R-m3; compared fresh here at HEAD
  bodies, not inherited). Contract difference here:
  permission-check + annotate/`order_by` over one shared tail vs
  visibility-derive + related-constrain + form-validate + `.qs` +
  logic tree over a prelude/finalize split with an async pre-walk;
  no `run_permissions`/`_depth` params here (no nested gates to
  double-fire, no visibility recursion to budget); the twin's one
  body per pair is impossible (await vs `SyncMisuseError`) while
  this pair's is one tail by construction. Opposite change
  responses (C28: either apply contract moves its own side only).
  CONVERGE with verified filters R-m3 on fresh evidence. Trigger
  to reconsider: a twin pair whose await points collapse to one
  coloring. Durable home: the apply docstrings (each already
  states its own stages + the contrast) + this artifact. Named
  for Worker 0 as rejected index row
  `orders-apply-vs-filter-apply`.
- **Convergence (no new row).** The `apply_async` boundary wrap
  is a consumer facet of VERIFIED family `one-sync-boundary`
  (owner `run_in_one_sync_boundary`; this file wraps one call —
  C29 proves a discipline change moves the owner once).

### F-LIFE — binding-state declarations (convergence onto verified family `subsystem-clear-lifecycle`; no new row)

State contributor to the verified bus family (member 6 of its
census: order ledger + `_field_specs` + factory caches + these
`OrderSet` binding attrs + parked globals — CONVERGE, lawful:
this file holds no clear contract, only the reset slots + the
descriptor). `_owner_definition` (finalizer-bound, written once through the
shared sidecar driver — `set_cls._owner_definition = definition`
is the single write site package-wide, verified by census),
`_expanded_fields` (expansion cache),
`_is_expanding_fields` (guard slot, write-only through the
shipped surface — `expanded_once` sets/clears it; nothing reads
it with `on_reentry=None`, correctly: the expansion never
re-enters), and `_lifecycle` (the `SetLifecycleAttrs` declaring
owner/cache/guard with empty `extra`, mirroring the twin's with
the order slot names — verified against both declarations).
Challenge C31 → 1 declaration here (+ the derivation at its
owner); C32 → 0 here / 1 at the bus + clear owner. The
write-only guard slot is documented at the owner ("stays in
place for future defensive use") with the planning-pass
disposition — observation (below the bar, not a defect): the
spec Edge case's "genuine cycle exhausts the guard and raises"
sentence is stale (the tree never recurses, no oracle pins a
raise); the target is correct and self-documenting, the spec
sentence is the stale half. Behavioral proof `static-reviewed`
(slots + one descriptor; no clear body spelled here). Freshness:
target HEAD `6044ab1a…` (dirt does NOT touch these lines),
[utils-inputs][utils-inputs] HEAD `ee31d360…` (the
`binding_attrs` consumption verified at the clear body; dirt as
System trace — no definition moved), [finalizer][finalizer] HEAD
`77fd9a2d…` (dirt as System trace — outside the judged bind
line), twin declaration [filters-sets][filters-sets] `722e0c77…`
(dirt as System trace — outside the judged declaration), family
artifact [dry-clear-lifecycle][dry-clear-lifecycle] (member-6
census), [spec-028][spec-028] `94a3141c…` (clean; Decision 6),
HEAD `5ee86193`. No new index row owed (holding item is the
verified family).

### F-NAME — default input naming (file-local)

- **Contract + variation.** `OrderSet` inherits
  `type_name_for` from `ClassBasedTypeNameMixin` and does NOT
  override `_field_type_suffix`: root + per-field names both
  keep the mixin default `"InputType"` (the cookbook declares
  both explicitly at the same value — verified against the
  running upstream; this port relies on the defaults instead),
  the deliberate divergence from `FilterSet` (which overrides
  to `"FilterInputType"` for its operator bags — verified at
  the twin body). Legitimate variation: the suffix posture only.
- **Sites + roles.** *Rule owner*:
  [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin`
  (the naming rule + defaults). *Declaration*: this file's
  non-override + the class-docstring divergence prose.
  *Consumers*: the BFS naming path (via the delegate) + every
  materialized input name. *Oracles*: the naming-convention test
  + the live root/bag names — independent (they spell names).
- **Challenges.** C33 → 1 here (add the override; the rule moves
  at its owner).
- **Owner + lifetime.** The mixin for the rule (existing owner);
  this file for its posture (declaration by absence + prose). No
  stored derivation.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed`. Rejects "the order
  side needs the override" (no per-field-bag machinery exists —
  the sole mention is the `_permission` comment stating its
  absence) and "the default is accidental"
  (the divergence prose + the cookbook's explicit pair pin it
  as deliberate).
- **Structural gate.** The pre-existing naming oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `6044ab1a…` (dirt does NOT touch
  these lines), mixin [sets-mixins][sets-mixins] `ad8987ea…`
  (dirt as System trace — outside `type_name_for`), twin
  override [filters-sets][filters-sets] `722e0c77…` (dirt as
  System trace — outside the judged line), cookbook suffix
  pair (read-only port check), [test-order-sets][test-order-sets]
  `9e9bb5d9…` (dirt as F-LEDGER — outside the judged oracle).

## Defects

### D1 — `apply_sync` cites Decision 13 for a contract that lives in Decision 8 + Edge cases (HEAD defect, clean lines — file for normal homing)

- **What.** The `apply_sync` docstring's step 4 says "`None`
  directions are filtered (spec-028 Decision 13 -- null-direction
  edge case)". Decision 13 is "Live HTTP coverage strategy"
  (verified: read in full — coverage plan + test list + rationale
  pointer; zero filtering semantics). The cited behavior lives in
  Decision 8 step 7 ("a term-less input … returns the queryset
  unchanged, preserving any pre-existing order") and Edge cases
  (the `orderBy: [{ name: null }]` / `[{ shelf: null }]` no-op
  bullets). The cite's own gloss ("null-direction edge case")
  names Edge-cases content, contradicting its number — and the
  docstring's cite convention is contract homes (Decision 8 step
  6, spec-030 P1-B), not test-list pointers. A reader chasing the
  contract's rationale lands in the coverage plan instead of the
  pipeline contract — a wrong stated home, principle-10 class.
  The softness the inputs item noted is real but mitigates
  severity, not verdict: Decision 13's test list DOES enumerate
  the pinning test (`test_library_branches_order_empty_list_and_null_direction_no_op`,
  verified present at HEAD), so the number is not arbitrary — but
  the number still names the test plan, not the contract.
- **Carried-note outcome (from inputs D2): FILED.** The inputs
  item routed this twin cite here for fresh adjudication with no
  homing instruction; judged against this target's HEAD body
  (the filtering happens in `_resolve_order_expressions`'s
  `direction is None: continue` arm — F-RESOLVE) and spec-028,
  the Decision number is wrong — filed below for normal homing.
  This closes the carried note; nothing rides further.
- **Spec-side context (observation, not a defect).** The Edge
  case the gloss names says "`None` directions are skipped in
  `get_flat_orders`" — the LOCUS is stale (the tree passes
  `None` through `get_flat_orders` and filters in
  `_resolve_order_expressions` — F-FLAT/F-RESOLVE), while the
  WIRE behavior is identical and pinned live. Target correct;
  spec sentence is the stale half. The homing card may note it
  alongside the re-point; no separate defect.
- **Lines.** `apply_sync` docstring step-4 lines — CLEAN at HEAD
  (the concurrent dirt sits at the import block + the claim /
  validate / expand / guard-verdict / resolve message + gate
  lines, verified by the item diff; the `apply_sync` docstring is
  untouched). HEAD defect on clean lines → normal closeout
  homing, no conditional.
- **Owner.** `django_strawberry_framework/orders/sets.py`
  `apply_sync` docstring (fix = re-point the cite at Decision 8
  step 7 + Edge cases; prose-only, no behavior change).
- **Freshness.** Target HEAD
  `6044ab1a11c77a42b715f0d0722fe7c9695064bc`;
  [spec-028][spec-028]
  `94a3141c02b92265779d8f3f7a2eefc019f765d8` (clean; Decisions
  8/13 + Edge cases read).
- **Not fixed.** File items never fix; recorded for Worker 0 to
  home on a NAMED owning card at closeout (D1–D3 may share one
  card — same file, all prose-only — at Worker 0's discretion).

### D2 — two `spec-030 … P1-B` cites name a label absent from the cited spec (HEAD defect, clean lines — file for normal homing, dedupe note)

- **What.** `_resolve_order_expressions` and `apply_sync`
  docstrings cite "(``spec-030-connection_field-0_0_9`` P1-B)" for
  the row-preserving aggregate contract. `P1-B` occurs ZERO times
  in the cited spec (verified: `grep -c` over the clean HEAD blob
  `0f7db072…`). The CONTRACT exists — Decision 11's
  "Aggregate-ordering coexistence" paragraph states it, citing
  this very method — but the LABEL does not: it survives only in
  the rationale companion ([spec-030-rationale][spec-030-rationale],
  which claims the label was "deliberately kept" in Decision 11 —
  false against the current tree) and in
  [build-038][build-038], which already judged these exact two
  cites as "the identical defect" (dangling ordinal cite against
  a zero-P-label spec) and routed them to its deferred catalog.
  A reader following the cite greps the spec for `P1-B` and finds
  nothing — a wrong stated home, principle-10 class, same as D1.
- **Prior record (dedupe, not drop).** This filing re-verifies
  fresh (the label is still absent at HEAD; the contract is still
  in Decision 11); it does not duplicate blindly — Worker 0 homes
  ONCE, against the build-038 deferred catalog if that is live,
  else on the D1–D3 card. One card, not two.
- **Lines.** Both docstring cite lines — CLEAN at HEAD (both
  docstrings untouched by the item diff; the nearby dirt is in
  the resolve message bodies). HEAD defect on clean lines →
  normal closeout homing, no conditional.
- **Owner.** `django_strawberry_framework/orders/sets.py` both
  docstrings (fix = re-point at Decision 11's paragraph by
  content — the label has no in-spec home; prose-only).
- **Freshness.** Target HEAD `6044ab1a…`; [spec-030][spec-030]
  `0f7db072fc3248cd6854ce1f1b2b91c6ab410f09` (clean; Decision 11
  read, `P1-B` census 0); [spec-030-rationale][spec-030-rationale]
  `95b704e48b41ea76a98e0575f0098a72136cea94` (clean; label +
  kept-claim witness); [build-038][build-038]
  `dbc2252f5c40e67b6f4e613a45306a8ce7584008` (clean; prior
  verdict witness).
- **Not fixed.** File items never fix; recorded for Worker 0 to
  home on a NAMED owning card at closeout (see dedupe note).

### D3 — module docstring calls the metaclass a "verbatim port" the deltas contradict (HEAD defect, clean lines — file for normal homing)

- **What.** The module docstring says "The metaclass is a verbatim
  port of ``django_graphene_filters/orderset.py::OrderSetMetaclass``".
  Verified against the running upstream: the BODIES differ
  structurally (shared-collector call + alias write-back vs
  inline inherit/override/bind loops) and BEHAVIOR differs on the
  shadow edge — the tree removes an inherited declaration
  shadowed by a non-declaration (tombstone + diamond
  reconciliation via the shared collector, pinned by the
  order-side diamond oracle), while the cookbook keeps it (its
  loop only adds `isinstance` matches). The bind matches (both
  idempotent-once — verified). "Verbatim" denies deltas that
  exist, are load-bearing, and are documented everywhere EXCEPT
  at this sentence (the collector docstring, the promote
  docstring, this file's own metaclass docstring says "Direct
  port" — the accurate word). A port auditor relying on the
  sentence concludes identity and misses the tombstone arm — a
  wrong stated fidelity, principle-10 class.
- **Lines.** Module-docstring lines — CLEAN at HEAD (dirt starts
  at the import block below). HEAD defect on clean lines →
  normal closeout homing, no conditional.
- **Owner.** `django_strawberry_framework/orders/sets.py` module
  docstring (fix = "direct port" + name the collector/promote
  deltas; prose-only, no behavior change).
- **Freshness.** Target HEAD `6044ab1a…`; cookbook `orderset.py`
  + `orders.py` (read-only port check: metaclass body, bind
  body — no tombstone logic upstream); [test-order-sets][test-order-sets]
  HEAD `9e9bb5d9…` (the diamond oracle pins the tree-only
  behavior).
- **Not fixed.** File items never fix; recorded for Worker 0 to
  home on a NAMED owning card at closeout (may share D1's card).

No other defects. Every remaining docstring claim checked held:
the port map (cookbook cycle-safe merge shape, Layer-4 skeleton,
Decision 8 steps 6/7, DoD 4(c) — each verified); the metaclass
MRO + write-back clauses; the `get_fields` two-condition gate +
no-`on_reentry` clauses; the `_expand_meta_fields` shape +
contract clauses; the guard's 2-total/3-total counts; the purity
obligation (three enforcers, every count pinned); the ledger's
append-only/identity/once-per-pair/terminal-close clauses; the
boundary's exact-type rationale; the `_permission` list-shape
clause; the flat walk's adaptation + pipeline clauses; the
resolver's model/aggregate/NULLS/pagination clauses; the tail's
stage + no-wrap clauses; the async sibling's boundary + no-visibility
clauses; the naming divergence (cookbook pair verified); the
`_lifecycle` mirror + slot clauses; the `__all__` helper's
Edge-case match. The axis-6 sweep finds no missing guard.

## Pending execution

None. No `execution-deferred` proof: all claims are
`static-reviewed` from HEAD bytes (byte-level greps, `ast.parse`
enumeration, full-body reads), every target behavior is pinned by
executed oracles on every suite run, and no probe was created that
could distinguish anything further. Sharded / Postgres cells are
inapplicable by construction: the target makes no database, alias,
or dialect decision (zero `_db`/`using`/backend tokens; the
queryset calls are lazy `annotate`/`order_by` construction — the
target never evaluates a queryset; the `threading.Lock` guards an
in-memory ledger, not I/O).

## Judgment

File item with one new family. Thirteen rules traced: eleven
file-local with proving challenges (F-LEDGER C1–C3; F-VALIDATE
C7–C8; F-META C9–C11; F-EXPAND C13–C15; F-ACTIVE C17–C18;
F-NORMDEL C19–C20; F-PERM C21–C22; F-FLAT C23–C24; F-RESOLVE
C25–C27; F-APPLY C28–C30; F-NAME C33), one routed to an existing
holding family on fresh evidence (F-LIFE → verified
`subsystem-clear-lifecycle`, C31–C32 — lawful convergence,
transcribes nothing; plus consumer/consumption facets onto one
open + two verified families and two existing rows, all
transcribing nothing), one new open family (F-PURITY
`active-terms-purity-agreement`, C4–C5 count 2 — the guard's twin
agreement verdicts), and seven rejections with contract
differences + triggers (R-m1..R-m4 CONVERGE the twin's verified
separations; R-EXPAND + R-CLAIM fresh; R-LEASE CONVERGE the
owner-recorded lease split). Enumeration covers 31/31 statements
and 33/33 named members (+ the nested `_build`). Three HEAD
defects on clean lines filed for normal homing (D1 closes the
carried twin-cite note as FILED; D2 carries a dedupe pointer to
the build-038 deferred catalog; D3 the port-fidelity
overstatement). No pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for
verification). Item-scoped check vs
`ITEM_BASELINE=24286c6573b10795e900d788191b56e3d2e75d70`: `git
diff <baseline> -- django_strawberry_framework/orders/sets.py` is
EMPTY (exit 0, zero hunks) — the worktree blob is still
byte-identical to the dispatch record (`f09d9983…`); the target
was never edited, reverted, or worked around. The artifact itself
(`docs/dry/dry-file-orders__sets.md`) is a new untracked file,
the item's only output. `git diff <baseline> --stat` at finish
additionally names three tracked paths, all concurrent-external by
diff content and untouched: `docs/dry/dry-0_0_15.md` (51
insertions — Worker-0 plan accounting),
`django_strawberry_framework/utils/querysets.py` (seal-policy
prose + `_LIST_RELATION_CHILD_POLICY` gaining `reject_combined`,
dirtied mid-task — HEAD never moved) and `tests/utils/test_querysets.py` (3
combinator-refusal tests for it) — hunt seal work in a file this
item reads only for the boundary/apply wrappers, zero relation to
any rule traced here. No `uv run ruff` run
(no `.py` edits; `.md` is outside ruff format scope; no `.py`
scratch created — the only execution was read-only `ast.parse`
enumeration + `git grep` censuses over HEAD blobs and `/tmp`
extracts). No shared-tree pytest run (static-decidable — see
`### Challenges` note; the entry command authorizes a focused
`--no-cov` run only where it could settle a judgment, and here it
could settle nothing). No `docs/dry/temp-tests/` scratch created.
HEAD confirmed `5ee86193` at start, at every fingerprinting step,
and at artifact completion. Concurrent dirt (hunt edits across
`django_strawberry_framework/`, `tests/orders/`,
`docs/dry/dry-0_0_15.md`) left untouched; the `## Owned changes`
ledger gains no row from this item. No commit.

## Index rows for Worker 0

Worker-0 instructions: (a) tick the plan item
`File orders/sets.py — dry-file-orders__sets.md` as verified under
Run `0.0.15 2026-09-22-6` once Worker 2 agrees; (b) add these
nineteen `## Responsibility index` rows verbatim (holding item
`File orders/sets.py`, except the family row as noted) + one
`## Families` item for `active-terms-purity-agreement`; (c) home
D1 + D2 + D3 on NAMED owning card(s) at closeout (all HEAD
defects, clean lines — normal homing, no conditional; the three
may share one card — same file, all prose-only — at Worker 0's
discretion, EXCEPT D2 dedupes against the build-038 deferred
catalog first: one card, not two; D1 closes the carried twin-cite
note as FILED).

| `orders-normalization-ledger` | `django_strawberry_framework/orders/sets.py::_NormalizationLedger` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-normalize-return-gate` | `django_strawberry_framework/orders/sets.py::_validate_normalized_terms` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-metaclass-collect-bind` | `django_strawberry_framework/orders/sets.py::OrderSetMetaclass` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-fields-expansion` | `django_strawberry_framework/orders/sets.py::OrderSet.get_fields` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-active-terms-check` | `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-normalize-delegate` | `django_strawberry_framework/orders/sets.py::OrderSet._normalize_input` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-permission-config` | `django_strawberry_framework/orders/sets.py::OrderSet._permission` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-flat-walk` | `django_strawberry_framework/orders/sets.py::OrderSet.get_flat_orders` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-expression-resolve` | `django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-apply-tail` | `django_strawberry_framework/orders/sets.py::OrderSet._apply_orderings` | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `orders-naming-default` | `django_strawberry_framework/orders/sets.py::OrderSet` (non-override of `_field_type_suffix`; rule at `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin`) | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | file-local |
| `active-terms-purity-agreement` | TBD by family item (candidates: `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms` via restructure, or a module verdict helper) | `django_strawberry_framework/orders/sets.py` | Family `active-terms-purity-agreement` | open |
| `orders-expansion-build-vs-filter-publish` | `django_strawberry_framework/orders/sets.py::OrderSet.get_fields` (rejection recorded here; CONVERGE with verified filters R-m1 on fresh evidence) | `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/filters/sets.py` | File `orders/sets.py` | rejected |
| `orders-normalizer-vs-filter-normalizer` | `django_strawberry_framework/orders/sets.py::_validate_normalized_terms` (rejection recorded here; CONVERGE with verified filters R-m2 on fresh evidence) | `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/filters/sets.py` | File `orders/sets.py` | rejected |
| `orders-apply-vs-filter-apply` | `django_strawberry_framework/orders/sets.py::OrderSet._apply_orderings` (rejection recorded here; CONVERGE with verified filters R-m3 on fresh evidence) | `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/filters/sets.py` | File `orders/sets.py` | rejected |
| `orders-metaclass-vs-filter-metaclass` | `django_strawberry_framework/orders/sets.py::OrderSetMetaclass` (rejection recorded here; CONVERGE with verified filters R-m4 on fresh evidence) | `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/filters/sets.py` | File `orders/sets.py` | rejected |
| `orders-expand-vs-filter-fields-narrow` | `django_strawberry_framework/orders/sets.py::OrderSet._expand_meta_fields` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/filters/sets.py` | File `orders/sets.py` | rejected |
| `orders-ledger-vs-operation-lease` | `django_strawberry_framework/orders/sets.py::_NormalizationLedger` (rejection recorded here; CONVERGE with the owner-recorded lease separation on fresh evidence) | `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/utils/operation_lease.py` | File `orders/sets.py` | rejected |
| `orders-ledger-claim-vs-guard-agreement` | `django_strawberry_framework/orders/sets.py::_NormalizationLedger.claim` (rejection recorded here; fresh split, no prior verdict) | `django_strawberry_framework/orders/sets.py` | File `orders/sets.py` | rejected |

(F-LIFE needs no new row: verified family
`subsystem-clear-lifecycle` already covers this file as member 6.
F-META's write-back facet needs no new row: open family
`dynamic-set-class-getter` already covers this file. F-APPLY's
boundary facet needs no new row: verified family
`one-sync-boundary`. F-EXPAND's BFS-read facet needs no new row:
consumption, and open family `set-arguments-factory-bfs` does not
list this file. F-EXPAND/F-RESOLVE path reads need no new row:
verified family `orm-lookup-path-resolution`. F-VALIDATE/F-RESOLVE
guard seams need no new row: existing rejected row
`orders-normalize-check-vs-resolve-guards` already lists this
file.)

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[build-038]: ../builder/DONE/build-038-form_mutations-0_0_12.md
[dry-clear-lifecycle]: dry-rule-subsystem-clear-lifecycle.md
[dry-filters-sets]: dry-file-filters__sets.md
[dry-mutid]: dry-rule-generated-mutation-input-identity.md
[dry-orders-base]: dry-file-orders__base.md
[dry-orders-factories]: dry-file-orders__factories.md
[dry-orders-inputs]: dry-file-orders__inputs.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md
[spec-030-rationale]: ../SPECS/appx/spec-030-connection_field-0_0_9-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[input-values]: ../../django_strawberry_framework/utils/input_values.py
[list-field]: ../../django_strawberry_framework/list_field.py
[operation-lease]: ../../django_strawberry_framework/utils/operation_lease.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-order-sets]: ../../tests/orders/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

### Trace-first record (written before opening `## Findings`)

Target `django_strawberry_framework/orders/sets.py` traced at HEAD
bytes only. HEAD `5ee8619330e7e236b61060a1ec9cb9e62b7061aa`
(unmoved from dispatch); HEAD blob
`6044ab1a11c77a42b715f0d0722fe7c9695064bc` (832 lines);
worktree `f09d9983ec5c95e3266174949656db8fd4937a62` (+32/-12)
is concurrent hunt dirt (`_safe_class_name` adoption + guarded
`__all__`-shorthand gate with an `except BaseException` arm),
confirmed by diff to match the dispatch description; absent from
the ledger and the cycle baseline. Window diff vs
`ITEM_BASELINE=24286c6573b10795e900d788191b56e3d2e75d70` names
exactly 3 tracked paths, attributed hunk-by-hunk: 5 hunks in
`utils/querysets.py` (all `_LIST_RELATION_CHILD_POLICY`
`reject_combined` + seal-wording seal work), 3 hunks in
`tests/utils/test_querysets.py` (same seal theme: preset asserts,
reworded match, 3 new tests), 1 hunk in `docs/dry/dry-0_0_15.md`
(Worker-0 run-6 accounting). All concurrent; no hunk in any path
this item touches (the artifact is new-untracked); no stop.

Instrument of my own: `ast.parse` over the HEAD extract
(`docs/dry/temp-tests/dry-file-orders__sets-w2/enumerate.py`):
**31** `ast.Module.body` statements; **33** named members (9
module-level bound names in statements 23-31 + 24 class-level
non-docstring members: 3 + 5 + 1 + 15). Sites, roles, and the
owner I would choose, per rule:

- Ledger handoff (stmts 23-28: `_NormalizedTerms`,
  `_AppliedNormalization`, `_NormalizationLedger` +
  `publish`/`claim`/`close`, `_ORDER_NORMALIZATION_CAPTURE`,
  `capture_applied_order_normalization`,
  `_record_applied_normalization`): one definition here; sole
  consumer pair is `list_field.py::_order_normalization_scope`
  (opens, only when positive offset + orderBy + captured
  OrderSet) and `list_field.py::_check_nonzero_offset_guard` via
  `OrderSet._input_has_active_terms` (claims; the guard
  docstring states it is the only caller). Owner: this module
  (file-local). Sibling-ContextVar merge already rejected at
  verified `_boundary_ordering` R2, which names this capture var
  with its contract difference.
- `_validate_normalized_terms` (stmt 29): pipeline-boundary
  exact-`type()` return-contract gate; 3 intra-module calls (2
  in `_input_has_active_terms`, 1 in `_apply_orderings`).
  Owner: this module (file-local). Three-seam split vs the
  inputs-side leaf check and the resolve-time guard already
  rejected at verified `orders/inputs` R-guards.
- `OrderSetMetaclass` (stmt 30 + `__new__`): declaration
  collection through shared `collect_related_declarations`
  (`inherit_from_bases=True`) + `promote_set_meta_fields`
  write-back; policy args here, machinery shared. Owner: this
  module (file-local). Metaclass merge already rejected at
  verified `filters/sets` R-m4.
- `get_fields` + `_build` closure (shared `expanded_once`
  skeleton, no `on_reentry` — verified the mixin documents the
  order side passes None — + shared `should_cache_expansion`
  gate): publish contract here, mechanism shared. Owner: this
  module (file-local). Build merge already rejected at
  verified `filters/sets` R-m1.
- `_expand_meta_fields`: `__all__` expansion consumes
  `.inputs::_get_concrete_field_names_for_order` (0
  definitions here); re-readability gate consumes shared
  `require_re_readable_field_declaration` (0 here); entry-type
  exact gate (1 here); path validation consumes
  `classify_path` (0 here, verified `orm-lookup-path-resolution`
  consumer). Owner of the expansion: this module (file-local).
- `_input_has_active_terms` + `_normalize_input` +
  `get_flat_orders`: the check spells TWO purity-agreement
  verdicts (ledger arm: applied-vs-fresh; fallback arm:
  fresh-vs-fresh), and `_NormalizationLedger.claim` spells a
  THIRD disagree-verdict over two attested terms. Three raise
  sites, one message family. My count question for the
  findings: the new-family count of 2 must pair exactly two of
  these three as one rule and place the third elsewhere with a
  contract difference; neither check calls the other and no
  shared verdict helper exists, so a count below 2 is
  indefensible, while 2-vs-3 turns on whether claim-internal
  attestation-vs-attestation agreement is the same rule as
  guard applied-vs-check agreement. Owner of the verdict rule:
  TBD by the family item if count > 1 holds.
- `_prepare_permission_input`: mixin-hook implementation
  warming lazy `_field_specs`; facade owned by
  `sets_mixins.py::ActiveInputPermissionMixin` (verified the
  hook + call site exist there). Config + hook here
  (file-local).
- `_resolve_order_expressions`: to-many aggregate rule
  (`Min`/`Max` via `Ordering.is_ascending`, alias via
  `flatten_lookup_path`, `OrderBy` via `Ordering.resolve`;
  scalar/to-one direct). Owner: this module (file-local).
  Direction `isinstance` guard is seam (c) of the verified
  R-guards split.
- `_apply_orderings` + `apply_sync` / `apply_async`: one
  uncolored tail; colorings differ only in permission-check
  coloring (`apply_async` wraps in `run_in_one_sync_boundary`
  — verified `one-sync-boundary` consumer, that artifact
  already lists this call); no `apply` dispatcher (verified
  absent). Owner: this module (file-local). Apply merge
  already rejected at verified `filters/sets` R-m3.
- `_lifecycle` + binding slots (`_owner_definition`,
  `_expanded_fields`, `_is_expanding_fields`): declaration
  consumed by `expanded_once` and by
  `utils/inputs.py::clear_generated_input_namespace` via
  `binding_attrs` (verified the read site); member 6 of
  verified `subsystem-clear-lifecycle`, which already lists
  this file. Converge, transcribes nothing.
- `_permission` config: declaration consumed by the mixin
  facade. File-local config; facade stays mixin-owned.
- Naming: `_field_type_suffix` NOT overridden (verified
  absent — only the docstring names it), so the mixin default
  `InputType` applies; deliberate divergence from the filter
  override. File-local (the omission decision).
- Factory/getter facets: target imports `_field_specs` (used
  in the `_permission` traversal config) and
  `_ensure_field_specs` (used in `_prepare_permission_input`);
  zero Layer-6 factory/getter tokens defined here. If the
  findings converge facets onto open `set-arguments-factory-bfs`
  / `dynamic-set-class-getter`, the convergence must
  transcribe nothing and define nothing here.

Matrix discharged against the real surface (my own): (1)
cross-flavor — filter twin read whole at HEAD (metaclass,
`get_filters`, `_lifecycle`, `_permission`, normalizer,
apply); R-m1..R-m4 separations re-verified against blob
`6044ab1a`, which all four cite; (2) sync/async — the apply
pair shares `_apply_orderings`; colorings differ only in the
permission-check boundary wrap; no other `async def`; no twin
duplication; (3) derived knowledge — names via mixin
(consumer), meta-fields read via shared
`read_set_meta_fields` (consumer), no re-derivation; (4)
round-trip — normalize → validate → flat → resolve →
`order_by` has no inverse half in this target; ledger
publish/claim is one grammar with two halves inside one
module; (5) other media — docstring cites checked against
their specs: Decision 13 test list DOES enumerate the
null-direction no-op test (softer cite, semantics live in
Edge cases + Decision 8); `P1-B` x2 at HEAD lines 682/796
match the build-038 catalog item 8 sites verbatim and are
already homed on `TODO-ALPHA-053-0.0.15` (KANBAN bullet
carries the exact pair, residual open); "verbatim port" is
contradicted internally (the body calls package-owned shared
helpers the cookbook never had); (6) omission — guards at
all three verified seams + `__all__`-without-model +
entry-type; no missing guard with a contract source.

Oracle check: `tests/orders/test_sets.py` pins the behaviors
with independently spelled expectations (ledger claim/publish
semantics, active-terms matrices, hostile-subclass gates);
no oracle reads from an owner it checks. Sharded/PG cells:
inapplicable by construction — the target reaches no
database, alias, or dialect decision (pure declaration +
validation + queryset-method calls; `.annotate`/`.order_by`
build expressions, never execute). No source-mutating proof
was needed: every claim above is static-decidable from HEAD
bytes plus the cited verified artifacts.

### Reconciliation (after reading `## Findings`) + verdict

Read the full artifact (1485 lines) after recording the trace
above. Reconciliation, every difference explicit:

- Enumeration: AGREE, member by member. My own `ast.parse`
  instrument returns the identical 31 statements (W1 numbers
  0-30, I number 1-31 — same bodies) and the identical 33
  named members (W1: 1+4+6+1+1+1+1+2+16 per statement; mine:
  9 module-level + 24 class-level 3+5+1+15). Every member's
  home checked: docstring projection (+ D3), future-import
  boilerplate, 19 imports / 36 names (recounted: 11 stdlib +
  25 first-party), TYPE_CHECKING guard, ledger stmts to
  F-LEDGER, validate to F-VALIDATE, metaclass to F-META,
  OrderSet's 5 attrs + 10 methods across the nine findings.
  No gap, no double-home.
- New family F-PURITY: AGREE, count 2 tested hard. The two
  guard arms (ledger-path applied-vs-fresh at HEAD 580-587,
  fallback fresh-vs-fresh at 589-595) spell byte-identical
  skeletons 8 lines apart (verified byte for byte from HEAD:
  same prefix/middle/suffix, only repr operands differ).
  Neither arm calls the other; no shared verdict helper
  exists — so neither is the consumer of the other and both
  cannot be consumers of one verdict. C4 (reword) and C5
  (comparison change) each force both: count 2 = duplication.
  Owner candidates + per-arm operand distinction recorded;
  family item owns the shape + gate. Correct routing for a
  file item.
- R-CLAIM split (the 2-vs-3 question from my trace-first):
  AGREE it is a sound rejection, the closest call in the
  item. `claim`'s verdict names a different event
  (inter-application attestation disagreement, possibly
  cross-task/thread — middle "two applications of the same
  input in one resolution") than the guard's (same-input
  read disagreement), with different diagnostic information
  and a different owning class (ledger claim integrity vs
  guard agreement). C6 (inter-application reword moves
  `claim` only) proves opposite change responses; the
  per-message-grammars argument matches standing rejections.
  Contract difference + trigger + durable home all present.
  My package-wide `is not pure` census confirms exactly
  these three raisers (HEAD lines 175/584/592), so no fourth
  site escapes the family-or-rejection partition.
- Convergences: AGREE on all, each re-verified on fresh
  evidence. F-LIFE: verified `subsystem-clear-lifecycle`
  member 6 already lists this file; `binding_attrs` read site
  verified at the clear body; transcribes nothing. F-APPLY
  boundary: verified `one-sync-boundary` already lists this
  exact call at blob `6044ab1a`; transcribes nothing.
  F-EXPAND/F-RESOLVE path reads: verified
  `orm-lookup-path-resolution` consumer posture; transcribes
  nothing. F-META write-back: open `dynamic-set-class-getter`
  files-covered already lists this file (pure read,
  `fields_alias=None` re-verified). F-EXPAND BFS facet:
  correctly NOT membership (zero walk/collision/cache tokens
  here; hook body reads `get_fields` — consumption only).
  R-guards three-seam split: adopted from the verified
  orders/inputs rejection, both sets-side seams re-read at
  HEAD. R-m1..R-m4: each compared fresh against both HEAD
  bodies; all four cite orders-sets blob `6044ab1a`,
  matching current HEAD. R-LEASE: the lease docstring
  VERBATIM records the split ("the same rule written for
  one subsystem, and stays where it is" + the tombstone
  reason) — converge on fresh body comparison is lawful.
- R-EXPAND (fresh): AGREE. Twin `FilterSet.get_fields` read
  whole at HEAD: `super().get_fields()` upstream-narrow +
  per-field `"__all__"` via `_lookups_for_field` + top-level
  sweep narrowing — vs this side's self-derive (own
  branches, model optional, dict degrades to keys, no
  per-field branch). Different mechanisms, opposite change
  responses. Difference + trigger + home present.
- Matrix: AGREE on all six axes, each judged against the
  real surface. Axis 2 is honestly "discharged by
  construction" (one tail, one `async def` — verified), not
  inapplicable. Axis 6 absences each trace to a contract
  source or verified separation; the twin docstring itself
  corroborates the shared re-readability gate. No unsearched
  axis hiding behind the found family.
- D1 (carried twin-cite note → FILED): AGREE. Decision 13
  read in full: coverage strategy whose test list DOES
  enumerate the no-op pinning test (verified present at
  HEAD line 3158) but states zero filtering semantics; the
  behavior lives in Decision 8 step 7 + Edge cases; the
  filtering locus is `_resolve_order_expressions`'s
  `direction is None: continue` (HEAD 711-712); the
  docstring's cite convention is contract homes. Softness
  mitigates severity, not verdict. Closes the carried note;
  nothing rides further. Lines clean (apply_sync docstring
  untouched by the item diff — verified).
- D2 (P1-B pair → dedupe): AGREE, with a strengthened
  pointer. Fresh facts: spec-030 carries 0 `P1-B`
  (re-censused); Decision 11's "Aggregate-ordering
  coexistence" paragraph states the contract and cites this
  very method (read); the rationale's "deliberately kept in
  the spec" sentence is false against the current tree
  (read); build-038 catalog item 8 names these EXACT two
  sites by unique substring (verified against the retired
  catalog at `31e03eed`) and discharged the package pair to
  `TODO-ALPHA-053-0.0.15`, whose KANBAN bullet carries the
  exact pair with residual open (read). So the live dedupe
  target is specifically the 053 stranded-ordinals bullet
  (sibling half on 056) — one card, not two, and no new
  card. W1's "home ONCE ... one card, not two" instruction
  implements exactly this.
- D3 ("verbatim port"): AGREE. Sustained on internal
  evidence alone (the body calls package-owned shared
  helpers the cookbook never had; the file's own metaclass
  docstring says "Direct port"), and W1's upstream evidence
  re-verified fresh against
  `django-graphene-filters/django_graphene_filters/orderset.py`:
  inline inherit/override/bind loops with `isinstance`-only
  matching (no tombstone — a shadowed inherited declaration
  survives upstream, removed here; the order-side diamond
  oracle pins the tree behavior), explicit upstream suffix
  pair (`_root/_field_type_suffix = "InputType"`, matching
  F-NAME), recursive `(flat, distinct)` string-list walk
  (matching F-FLAT). Lines clean (dirt starts below the
  docstring — verified).
- F-ACTIVE C17 polarity pair (no `is_active_direction`
  helper): AGREE — 3-token check in opposite-polarity
  contexts; a helper would be principle-11 machinery.
  F-APPLY + F-LIFE "below the bar" observations: AGREE they
  stay observations (self-correcting docstring; stale
  spec-side sentence, target correct).
- Zero-edit shape: AGREE. Item diff vs baseline is empty on
  the target; the 3-path window diff is all concurrent
  (re-attributed hunk-by-hunk in my trace-first record);
  artifact is the only output; no `## Owned changes` row
  owed. File-local-only shape holds against the filters
  twin: every mirror pair converges a verified separation
  or a fresh rejection, and the single consolidation
  candidate routes to its holding family item.
- Oracles: no oracle rewritten (zero production/test edits);
  cited oracles spot-verified independent (ledger
  claim/publish semantics, active-terms matrices,
  hostile-subclass gates, `co_names` composition pins at
  test_sets.py HEAD 281-282, diamond oracle at HEAD 112).
  Sharded/PG inapplicability: judged sound (no database,
  alias, or dialect decision; `.annotate`/`.order_by` are
  lazy construction; the lock guards in-memory state).

W2 corrections (evidence-precision slips; none verdict-
affecting, all recorded here so no revision round is owed):

- W2-C1: the System-trace dirt note records
  `[connection]` as `9c5b8724…` — that is the WORKTREE
  blob, not HEAD. Correct HEAD blob (HEAD unmoved, so
  comparable): `4894f90fb2963a44d25b0eabc649c67d04afa587`.
  The judged claim (connection's two `order_by` sites at
  HEAD 851/1716 answer cursor-stability/model-default
  contracts, never consumer directions) re-verified fresh
  at HEAD bytes — HOLDS. Fail-safe direction (a future
  HEAD comparison reopens rather than false-cleans).
- W2-C2: R-m4's "verified absent: zero `def apply`" is
  literally false as a substring census (`def apply_sync`
  + `async def apply_async` contain it). Precise form:
  zero `def apply(` dispatcher. Underlying fact (no
  dispatcher per DoD 4(c)) re-verified — HOLDS.
- W2-C3: `## Pending execution`'s "zero `_db`/`using`/
  backend tokens" needs the word-boundary qualifier: the
  substring `using` occurs once inside prose "reusing"
  (HEAD 562). Precise form: zero `.using(` DB-alias calls.
  Inapplicability conclusion re-verified — HOLDS.
- W2-C4: C30's "verified zero queryset-derivation tokens"
  needs the prose qualifier: one `get_queryset` mention
  exists in the no-dispatcher rationale docstring (HEAD
  349, naming the FILTER side's path). Precise form: zero
  order-side derivation machinery. Absence conclusion
  re-verified — HOLDS.

Prose + gates: no banned provenance words (`feedback`,
`Co-Authored-By`, `subagent`, timestamps — all 0);
`path::Symbol` citations + reference-style links with all
10 canonical scaffold headers present; no `.py:NN` refs;
no tests added (none owed); no `pragma: no cover`. Ruff:
item touched no `.py` (artifact is `.md`); my one probe
(`docs/dry/temp-tests/dry-file-orders__sets-w2/enumerate.py`)
passes `uv run ruff check` + `uv run ruff format --check`
after scoped `--fix` + format (format last).

No new `## Defects` entries: the four W2-C items are
artifact-evidence precisions, not system defects, and are
fully discharged above. W1's D1/D2/D3 stand as filed.

Verdict: `verified`. Zero-edit file item: 13 rules (11
file-local + 1 convergence + 1 new open family
`active-terms-purity-agreement`), 7 rejections (4 twin
converges + R-EXPAND/R-CLAIM fresh + R-LEASE owner
converge), 3 HEAD defects on clean lines for normal
closeout homing (D1 closes the carried note as FILED; D2
dedupes to the live 053 bullet — one card, not two). No
pending execution. HEAD `5ee86193` unmoved at finish;
target HEAD blob `6044ab1a` / worktree `f09d9983`
re-confirmed. Scratch kept small: the one enumeration
probe above (retained for Worker 0's explicit-path
removal).
