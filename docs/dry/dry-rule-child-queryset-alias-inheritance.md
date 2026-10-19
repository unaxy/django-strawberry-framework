# DRY review: `child-queryset-alias-inheritance`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

Rule: child querysets inherit the parent's database alias — one GraphQL
resolution stays on one connection. Provisional owner
[querysets.py][querysets]`::base_queryset` (+ `using` pin), confirmed below
for the seed half only; the check half is owned by
[querysets.py][querysets]`::_seal_or_defect`.

Two mechanisms encode the rule, answering different questions: `base_queryset`
pins what the seed routes to; `_seal_or_defect`'s `require_shared_alias` arm
rejects what a hook may change it to. Parent-to-child descents traced:

- Cascade (`permissions.py::_walk`): seeds each edge base pinned
  (`base_queryset(field.related_model, using=state.alias)`), root state pinned
  at `alias=queryset.db`, hook results checked by the seal's generic alias arm
  under `_CASCADE_SEAL_POLICY`, nested-walk re-entry checked by identity
  comparison. Fully pinned both ends.
- Related filters (`filters/sets.py`): seeds each child base pinned
  (`base_queryset(child_model, using=parent_db)`), `parent_db` threaded from
  `queryset.db` at all five `apply_*` entries, hook results checked by the
  generic alias arm under the default policy, nesting re-pinned transitively
  off each level's sealed `queryset.db`. Fully pinned both ends.
- Optimizer prefetch child (`optimizer/walker.py::_build_child_queryset`):
  seeds UNROUTED (`base_queryset(field.related_model)`, no `using`), hook
  result sealed under `_PREFETCH_CHILD_POLICY`
  (`reject_sliced=False, require_shared_alias=True`). Deliberately unpinned:
  the plan is cached and reused across requests and the parent is unknown at
  plan time, so the child must leave alias-agnostic and inherit at fetch time;
  the seal refuses any hook-pinned alias instead.
- Consumer `Prefetch` children
  (`utils/querysets.py::_sealed_prefetch_related_lookups`): outer effective
  alias threaded into the recursive child seal under `_PREFETCH_CHILD_POLICY`.
- Post-`OrderSet` results (`_snapshot_routing_intent` + `_RoutingIntent`
  compare): routing frozen before consumer code runs, result must match.
- Fetch-time inheritance (composers of `queryset.db`, not definitions):
  `single_parent_fetch.py` (`.using(queryset.db)`),
  `predicates.py` (`using(queryset.db)`), the `nested_planner.py` alias-late
  GFK predicate, `types/resolvers.py::_visible_related_object` (row's
  `_state.db`).

Correction to the item's premise, established from bytes: the enforcement on
the walker path did NOT land in `4d9f1c3d`. `git log -S` shows the walker code
repoint (old policy → `_PREFETCH_CHILD_POLICY`) plus both live oracle suites
landed together in `fd39cac6` ("seal the planned prefetch child against a
routed target hook"); `4d9f1c3d` touched only `querysets.py` docstrings, one
test row, and `spec-034` prose — it retired the then-dead
`_UNRECOMPOSED_CHILD_POLICY` constant. Observable-behavior change is real;
its landing commit is `fd39cac6`, its cleanup is `4d9f1c3d`.

Prior records used as triggers only: the `utils/querysets.py` file item's F8
(two-mechanism count + D1 coupling) and D1 (unguarded walker member), and the
`sealed-execution-queryset` family's D-W2-a GONE verdict — all re-derived
below from current bytes, none inherited.

## Verification

### Matrix

1. Cross-flavor mirroring: sync/async filter derives thread `parent_db`
   identically (both call `_iter_visibility_steps(input_value, parent_db)`);
   the cascade async twin wraps the same sync `_walk`; both visibility
   runners share `_prepared_visibility_source` /
   `_normalized_visibility_result`. No color drift in alias behavior.
2. Sync/async twins: compared by behavior — same seed pins, same seal arms,
   both colors. No twin-only alias path exists.
3. Derived knowledge: `queryset.db` is read at each enforcement entry (five
   filter `apply_*` sites, cascade root, `_visible_related_object` row read)
   and composed by name; `effective_alias` resolution lives in
   `_seal_or_defect` alone (`required_alias if not None else db`). No second
   derivation of the rule.
4. Inverse / round-trip pairs: pin half (`using=` at seed construction) and
   check half (`alias` defect at seal) — the two mechanisms of F1; inherit
   half (unrouted → router/fetch-time default) is Django semantics the seal
   preserves by construction (`using = required_alias if not None else db`).
5. Other media: oracles (seal matrix in `tests/utils/test_querysets.py`;
   live default-DB pair in `test_products_visibility_api.py`; live sharded
   trio in `test_multi_db.py`) and projections (spec-045 Decisions 4–5,
   spec-034 verified-dependency clause, GLOSSARY *Prefetch alias threading*,
   owner + consumer docstrings). Listed, not counted.
6. Enforcement by omission: every parent→child descent enumerated above
   pins or checks. The single-object recheck fallback
   (`related_visibility_queryset_or_default`, unrouted seed) carries no alias
   pin — but no contract source extends the one-connection rule to that
   surface (its family `related-object-visibility-recheck` is open), so per
   DRY.md axis 6 it is an exclusion with a trigger, not a gap. Write-path
   pins (`write_transaction.py`, `mutations/resolvers.py`,
   `rest_framework/resolvers.py`, `relay.py` node decode) answer to the
   pipeline-alias contract, excluded with reason.

### Enumeration

Instruments: `grep` populations over `django_strawberry_framework` +
full read of each site. `require_shared_alias`: 8 hits, all in
[querysets.py][querysets] (field, docstrings, declaration, two seal arms)
plus the [walker.py][walker] rationale comment — one check definition.
`base_queryset(`: pinned-`using=` call sites are exactly two
([permissions.py][permissions], [filter-sets.py][filter-sets]); the walker
seed and all root seeds call it unpinned by contract. `_PREFETCH_CHILD_POLICY`
production consumers: exactly one ([walker.py][walker]); the recursive
consumer-`Prefetch` seal composes the same constant by name. `parent_db`:
5 `queryset.db` thread-throughs in [filter-sets.py][filter-sets], all read.
`_UNRECOMPOSED_CHILD_POLICY`: zero package hits (docs/prose only).
`allow_sliced`: zero package hits. Every member lands in F1 (two mechanisms),
R-merge, or an exclusion above.

### Challenges

- C1 — change the seed spelling (e.g. seed children from `_base_manager`,
  or drop the `using` arm): 1 definition (`base_queryset`). The two pinned
  consumers move as call sites, listed not counted. Count: 1.
- C2 — change the shared-alias semantics (e.g. warn instead of fail closed,
  or demand equality on top-level reads too): 1 definition (the
  `_seal_or_defect` arms at `policy.require_shared_alias` / the generic
  `elif`; policy declarations are principle-1 variation, not definitions).
  Count: 1.
- C3 — a fourth child-seeding surface appears: 0 definitions move; the new
  site composes `base_queryset(using=...)` + a result seal under an
  appropriate policy (1 call site). Count: 0.
- Probe P1 (execution-verified, WS copy): live walker-path rejection +
  narrow-control both pass on current bytes (package inside WS, DB inside
  WS — see F1). Rejects: a routed walker-child hook being accepted; an
  unrouted hook losing its narrowing.
- Probe P2 (execution-verified, WS copy): negative control — WS-only revert
  of the walker call to a local `_SealPolicy(reject_sliced=False)` (the
  pre-`fd39cac6` shape) makes the rejection oracle FAIL (rows served,
  `data` non-`None`). Rejects: an oracle that cannot see the policy the
  site seals under. Shared tree untouched by the mutation.

## Findings

### F1 — CONFIRMED already-single ×2, no consolidation (zero-edit)

Contract + variation: one GraphQL resolution stays on one connection; varies
on which end is known (seed pinnable vs plan-cached parent-unknown) and on
slice tolerance (prefetch children admit Django's legal top-N slice).
Sites + roles: definitions — `base_queryset`'s `using` arm (seed pin),
`_seal_or_defect`'s `require_shared_alias` + generic alias arms (result
check); variation declarations — `_SealPolicy.require_shared_alias`,
`_PREFETCH_CHILD_POLICY` (sole production consumer: the walker);
enforcement sites — cascade root/edge/re-entry, filter child bases (5
`parent_db` entries + transitive re-pin), walker child seal, recursive
consumer-`Prefetch` seal, OrderSet routing snapshot; oracles — seal matrix
(inherit / cross-alias / unrouted-parent rows, policy-preset row), live
default-DB rejection + narrow-control, live sharded rejection + 2 controls;
projections — [spec-045][spec-045] D4/D5, [spec-034][spec-034] dependency clause, GLOSSARY entry,
owner + consumer docstrings.
Challenges: C1=1, C2=1, C3=0 (new surface composes by name).
Owner + lifetime (principles 7/4): split ownership stands — `base_queryset`
owns seed routing (every legitimate seeder already imports it without
reversing a dependency); `_seal_or_defect` owns result routing (every
visibility runner already composes it). Lifetime: per-query / per-queryset;
nothing cached — the `using` pin rides the queryset, `effective_alias`
resolves per seal, publish point is the sealed return, and only downstream
framework transforms may touch the sealed object.
Migration: none — already composed by name at every site.
Distinct behavior kept: walker unrouted-seed (plan-cache + unknown-parent
reason recorded at `walker.py::_build_child_queryset` docstring) vs
cascade/filter pinned-seed; `require_shared_alias` strictness (any explicit
child alias fails, even the request's own) vs the generic arm (unrouted
results repinned, only divergence fails); prefetch slice licence
(`reject_sliced=False`, degrade-to-unplanned gate owns the shape).
Behavioral proof: execution-verified — P1 passes on current bytes, P2 fails
on the reverted shape (both in the disposable copy; one focused shared-tree
run corroborates the rejection on the live tree). Rejects silent cross-shard
reads and policy-blind oracles.
Structural gate: no new gate owed — the live rejection oracles ARE the gate,
and P2 proves they fail their negative control (a behavior-preserving revert
of the owner's call fails the oracle; a hand copy of the owner body would
pass it, correctly, since the copy enforces). No `proof:` remains
gate-runnable; sharded trio stays unverified pending the maintainer's cell
authorization (see Pending).
Freshness: [querysets.py][querysets] `96618fba`, [walker.py][walker]
`9b111ed9`, [permissions.py][permissions] `757dce34`,
[filter-sets.py][filter-sets] worktree `4a40e51b` (HEAD `4ab65a26`;
concurrent +22 declared-filter form-key hunk, alias sites untouched —
verified by content diff), `tests/utils/test_querysets.py` worktree
`8b39c9f8` (HEAD `977a81df`; concurrent test dirt, cited oracle rows read at
worktree bytes), `test_products_visibility_api.py` `0b541ebd`,
`test_multi_db.py` `94e52fda`, spec-045 `97561f2d`, spec-034 `10563b0f`,
GLOSSARY `bc51debc`. HEAD `bfaee91d`; ITEM_BASELINE
`d2300af35a1a64f33de57df6f102d3dbb8b64581` (item-scoped diff on all four
member files: empty).
Coupling: none — zero production edits, nothing to land together.

### R-merge — REJECTED consolidation of seed-pin into result-check

Difference: the pin answers "what connection does this child start on" at
construction (affects SQL routing even when no hook runs); the check answers
"may this hook's return leave the required alias" at seal (affects only
hook-carrying descents). A seed-spelling change (manager, base shape) must
not move the seal contract, and a check-semantics change must not re-spell
every seed. Merging couples independent change axes across the
owner/consumer dependency direction.
Trigger: a descent whose seed and check must move atomically (e.g. a new
child kind whose routing cannot be expressed as `using=` + policy fields).
Home: already at the owners — `base_queryset` docstring (names the three
relation-keyed seeders) + `_SealPolicy.require_shared_alias` docstring
("Set solely for a `Prefetch` child"). No edit owed.

### Old D1 / D-W2-a — GONE, verified from the tree, not re-filed

- Enforcement landed in `fd39cac6` (walker seals under
  `_PREFETCH_CHILD_POLICY`; live rejection + narrow-control oracles landed in
  the same commit, default-DB and sharded). Cleanup landed in `4d9f1c3d`
  (dead constant + docstring/test/prose repoint). Both verified present.
- Pre-side oracle: no committed test ever pinned walker-path acceptance —
  the gap WAS the defect (old D1 + workspace-only probe). Post-side oracles:
  `test_planned_prefetch_child_may_not_pin_its_own_connection` (default DB,
  shared-tree run below), `test_planned_prefetch_child_cannot_route_itself_to_the_other_shard`
  + zero-SQL-both-aliases assertion (sharded, pending cell), plus four
  controls (narrow-hook serves rows; unrouted inherits; routed parent
  carries child). Observable behavior changed exactly as the defect
  predicted: same explicitly-routed hook accepted before, `ConfigurationError`
  (`alias`) after.
- Old D2 glossary half CLOSED in-tree: GLOSSARY *Prefetch alias threading*
  now reads `reject_sliced=False` in `_PREFETCH_CHILD_POLICY` (via
  `dfb95984`); `allow_sliced` zero hits package-wide. spec-045's remaining
  `allow_sliced` mentions are archived history, correctly untouched.

## Defects

None new. Tracing found no live alias violation: every parent→child descent
with a contract source pins or checks, and the two unpinned surfaces
(single-object recheck fallback; top-level root seeds) are unrouted by
contract, never cross-routed. The recheck-fallback exclusion carries its
trigger (a sharded read-surface recheck serving another shard's row homes a
defect here with the reaching query); no such oracle exists today.

## Pending execution

- Executed (evidence, not owed work): WS pristine
  `test_planned_prefetch_child_may_not_pin_its_own_connection` +
  `test_planned_prefetch_child_still_serves_rows_when_the_hook_only_narrows`
  → 2 passed; WS negative-control (pre-`fd39cac6` policy shape) → oracle
  fails as predicted; shared-tree
  `test_products_visibility_api.py::test_planned_prefetch_child_may_not_pin_its_own_connection --no-cov -n0`
  → 1 passed. WS copy `__file__`
  `.../dry-ws/child-queryset-alias-inheritance/django_strawberry_framework/__init__.py`,
  DB `NAME` `.../dry-ws/child-queryset-alias-inheritance/examples/fakeshop/db.sqlite3`.
- Unverified (needs the maintainer's word): `FAKESHOP_SHARDED=1` trio in
  `test_multi_db.py` (rejection + inherit + routed-parent-follow) and any PG
  cell. Same mechanism as the executed proofs, different database topology —
  reported honestly, not marked complete.

## Judgment

The alias rule is two single-owned mechanisms sharing one contract sentence:
`base_queryset` pins seeds, `_seal_or_defect` checks results, `_SealPolicy`
declares the per-descent variation, and every descent composes them by name.
No duplication exists, so no consolidation lands; the merge is rejected with
difference, trigger, and home. The routed walker gap is gone — enforced since
`fd39cac6`, residue retired by `4d9f1c3d` — with live oracles pinning both
the refusal and the three inheritance controls, and the negative control
proved in the disposable copy.

Item-scoped diff state: no tracked edits; one new untracked artifact (this
file). `git diff d2300af35a1a64f33de57df6f102d3dbb8b64581 -- <four member
files>` empty; `git diff HEAD --` empty on `querysets.py`/`walker.py`/
`permissions.py` (`querysets.py` READ-ONLY honored — read freely, never
edited); `filters/sets.py` dirt is pre-baseline concurrent work on
non-alias lines, left alone. No test files touched. Scratch:
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/child-queryset-alias-inheritance`
(WS-only policy revert; never in the shared tree; remove by explicit path
after verification).

Worker 0 notes: plan index row `child-queryset-alias-inheritance` currently
`defect-routed` — the routed defect (walker D1) is landed and verified gone,
recommend `rejected` (zero-change confirmation, already-single ×2) with the
landing note (`fd39cac6` enforces, `4d9f1c3d` retires); no ledger rows owed
(zero production edits).

## Independent verification (Worker-2)

Run: 0.0.15 2026-10-01-9. Written BEFORE reading `## Findings` (headers +
`## Judgment` tail seen for placement only); every pin below is re-derived
from current worktree bytes, never inherited from the Sept record.

### As-found state

- `Status: ready-for-verification/1`, `Run: 0.0.15 2026-09-19-1`; no
  `## Implementation` section; artifact untracked (`??`), so the tracked
  item-scoped diff is exactly `git diff ITEM_BASELINE --name-only` =
  `docs/dry/dry-0_0_15.md` (Worker-0's dispatch note, 23+/0-). The four
  indexed paths are byte-identical between `ITEM_BASELINE=a5c4273f` and the
  worktree: zero-edit claim holds structurally.
- Freshness (W2 pins, `git hash-object` WT / `git rev-parse HEAD:`):
  `utils/querysets.py` `3e392d48`/`69ac3ea3`,
  `optimizer/walker.py` `4fd8077f`/`13e1be20`,
  `permissions.py` `87271361`/`9edd4cf5`,
  `filters/sets.py` `697ffd40`/`85699ac2` (match the plan's dispatch pins).
  HEAD-vs-WT dirt is the typing migration (`_safe_type_name` ->
  `truth.kind`, `_safe_arg_repr` -> `truth.render`, `_safe_routing_repr` ->
  `_routing_repr`, indent/comment churn); the only alias-line hits are that
  rename, no semantic touch. Oracle files clean: `test_products_visibility_api.py`
  `318bc95e`, `test_multi_db.py` `893956aa` (WT = HEAD).

### Owner (re-derived)

`utils/querysets.py::base_queryset` (seed half) +
`utils/querysets.py::_seal_or_defect` `require_shared_alias` arm (check half)
+ `utils/querysets.py::_SealPolicy` (per-descent variation record). Reasons:
the conditional pin `manager.using(using).all() if using is not None else
manager.all()` exists once (:297); the explicit-`_db`-vs-outer comparison
returning the `alias` defect exists once (:3868-3875); all three descents
already import from `utils/querysets.py`, so dependency direction agrees with
narrowest-valid-owner. Same address the plan indexes; reached by mechanism,
not by inheritance.

### Mechanism census (roles)

Seed half (definition, count 1): `base_queryset` (:280-297). Consumers (8):
`initial_queryset` (:337, type-keyed wrapper); cascade `_walk` (:710,
`using=state.alias`); related-filter `_iter_visibility_steps` (:2859 of
`filters/sets.py`, `using=parent_db`); walker `_build_child_queryset` (:592,
unrouted); `filters/base.py:1466`, `connection.py:2153`, `list_field.py:1620`,
`querysets.py:4602` (plain unrouted top-level/fallback seeds, no alias
semantics). No production code re-spells `._default_manager.using(..).all()`
(the one hit is the `filters/sets.py:2820` docstring cross-cite, stale by
spelling, semantically exact — observation O-W2-a, not a defect).

Check half (definition, count 1): `_seal_or_defect` :3868-3875 —
`require_shared_alias` branch (`db is not None and db != required_alias` ->
`("alias", ...)`, None-inclusive) + the `elif` top-level branch. Composition
chain: `_prepared_visibility_source` seals the seed with required `None`,
then `required_alias = sealed._db` (or the write pipeline's alias);
`_normalized_visibility_result` seals the hook return against it
(`using=required_alias` at construction pins, matches preserve, divergences
fail). Both colored runners share this boundary; no twin drift.

Variation record (definition, count 1): `_SealPolicy` (:2893-2967) with two
child policies setting `require_shared_alias=True` — `_PREFETCH_CHILD_POLICY`
(:2989-2992, `reject_sliced=False`) and `_LIST_RELATION_CHILD_POLICY` (:3002)
— differing on `reject_sliced` and nothing else, each difference documented
at both the policy and the consumer.

### The three descents (per-descent composition, all by name)

1. Cascade `_walk` (`permissions.py`): root alias pinned once
   (`_TraversalState(alias=queryset.db)` :658); per-edge seed
   `base_queryset(field.related_model, using=state.alias)` (:710); target
   hook return checked via `apply_type_visibility_sync(..., policy=
   _CASCADE_SEAL_POLICY)` (:717-724), i.e. the `elif` arm against
   `required_alias=state.alias`; `_validated_target_subquery` (:476-556)
   owns only the re-projection battery and states the alias contract is the
   boundary's. Nested-walk guard (:660, effective-vs-effective, raises
   `ConfigurationError`) is cascade-local composition protection, examined
   and excluded (different trigger/comparison/error).
2. Related filters (`filters/sets.py`): `parent_db` threaded from
   `queryset.db` at five call sites (:3505, :3512, :3724, :3785, :3791)
   through sync+async derive twins sharing `_iter_visibility_steps`; seed
   :2859, check `apply_type_visibility_sync(target_type, child_base, info)`
   (:2912, default policy). `parent_db=None` leaves the seed unrouted and
   the hook free to route — sound because the child composes as a
   same-statement subquery RHS while a pinned parent routes the hook's own
   reads to the right shard (docstring rationale verified against the
   composition).
3. Prefetch child (`optimizer/walker.py` + seal): seed unrouted
   `base_queryset(field.related_model)` (:592); hook return sealed via
   `apply_type_visibility_sync(..., policy=policy)` (:627-634) with
   `_LIST_RELATION_CHILD_POLICY` default / `_PREFETCH_CHILD_POLICY` through
   `_build_connection_child_queryset` (:655-662); required alias is `None`
   (no write pipeline at plan time), so ANY explicit hook pin fails closed
   and the unrouted child inherits at fetch. Consumer-`Prefetch` children
   meet the same rule in `_sealed_prefetch_related_lookups` (:2699-2706,
   outer effective alias threaded in). The fetch-time half is Django's own
   `queryset.using(queryset._db or self._db)` in both `get_prefetch_querysets`
   implementations (installed Django 6.1 `related_descriptors.py`), verified
   in `.venv` — the package owns "leave it unrouted", Django owns the `or`.

### Change challenges (definition counts)

- C1 (check variation): "a prefetch child may explicitly pin the PARENT's own
  alias" -> moves only the :3868 arm's None-inclusive condition. Count 1.
- C2 (seed variation): "child seeds take router hints as well as an alias" ->
  moves only `base_queryset` (:297); call sites are consumers. Count 1.
- C3 (descent opt-out): "related filters stop inheriting" -> the five
  `parent_db=` call sites stop passing (consumer-side); owner untouched.
  Count 0 definitions — single-ownership shown from the other side.
- C4 (policy axis): "seal a child under a new axis" -> one `_SealPolicy`
  field + its arm in `_seal_or_defect`, same module. Count 1.
- C5 (None semantics): "unrouted parent accepts a routed child" -> only
  :3872. Count 1. (`attach_exists`, `pin_write_queryset`, cascade :660 move
  under none of C1/C4/C5 — different comparisons, see exclusions.)

### Independent consolidation search (package-wide)

`require_shared_alias`: 1 field, 2 setting policies, 1 reading arm, prose
cites — single check. `.using(` production sites and `_db` comparisons each
censused; every lookalike carries a contract difference (changed only if its
own rule changes, never with this one):

- `optimizer/predicates.py:79` (`_base_manager.using(queryset.db)` + OuterRef
  correlation): unfiltered-base subquery root that never executes
  independently; routing through `base_queryset` (`_default_manager`) would
  change its rows. Its :169 guard compares EFFECTIVE `.db` vs `.db` for
  same-statement Exists composability and raises `OptimizerError` — different
  comparison, trigger, and error from the seal's explicit-`_db` defect.
- `utils/write_transaction.py::pin_write_queryset` (:731-751): pins to the
  WRITE PIPELINE's alias for single-transaction atomicity; same check shape,
  different alias source, raise-vs-defect, write-vs-read.
- `optimizer/single_parent_fetch.py:286` (`.using(queryset.db)` repin):
  execution-time application onto a cached pristine plan artifact, not a seed
  or a check — no equality, no pin-at-build.
- `types/resolvers.py:467` re-pin, `mutations/resolvers.py:877`,
  `rest_framework/resolvers.py:1978/2067`, `_base_manager` seeds: seed-shape
  questions owned by verified Family `queryset-seed-and-model-read` (e8),
  which censused all of them (re-pin `.using()` = routing moves on existing
  sources, R7 `_base_manager`); not re-litigated.
- `walker.py::_hint_prefetch_over_pk_set` :1429-1440 (`using=inner._db`):
  routing-preserving rewrite, threads nothing, checks nothing.
- Seal `routing` arm (:3739, OrderSet-result-vs-snapshot incl. hints),
  `_coerced_manager_queryset` (:4133, manager coercion), cascade :660
  (nested-input guard): different triggers/comparisons/errors.
- No second `require_shared_alias` reader, no second conditional seed-pin,
  no second explicit-`_db`-equality defect exists. No landable owner beyond
  the re-derived one: NOT a `revision-needed` candidate. (Concurrent dirt
  touches none of these lines semantically; no `blocked` positions.)

### R-merge position (re-derived)

Seed-pin and result-check share a contract sentence but not a contract: the
seed answers pre-hook input routing (which database the hook's own reads see
+ where `required_alias` comes from); the check answers post-hook output
validation (did the consumer return stay on it, with None-inclusive child
semantics the top-level `elif` deliberately lacks). Different phases (before
vs after consumer code runs), different inputs (caller-known alias vs
hook-returned queryset), different outputs (routed seed vs defect). A merged
single mechanism would have to both route-before and validate-after with one
shape — the per-descent policies (`_CASCADE_SEAL_POLICY` without the flag
vs the two child policies with it) are the variation that forbids it.
Trigger: a descent whose seed needs no pre-hook routing AND whose result
needs no post-hook validation. Home: `_seal_or_defect` docstring `alias`
bullet. REJECTED.

### D1-gone (fresh at current bytes)

- `fd39cac6` enforcement intact: walker imports both child policies (:20-21);
  `_build_child_queryset` defaults to `_LIST_RELATION_CHILD_POLICY` (:554)
  with the `require_shared_alias=True (both)` rationale comment (:616-626);
  `_build_connection_child_queryset` passes `_PREFETCH_CHILD_POLICY`
  (:661); both policies still set the flag (probe-verified).
- `4d9f1c3d` retirement intact: `_UNRECOMPOSED_CHILD_POLICY` occurs nowhere
  under `django_strawberry_framework/`, `tests/`, or `examples/` (`.pyc`
  excluded from the claim; source: zero hits).
- Live oracles, all present with pinning assertions: refusal
  `test_planned_prefetch_child_may_not_pin_its_own_connection` + narrowing
  control `..._still_serves_rows_when_the_hook_only_narrows`
  (`test_products_visibility_api.py:1076/1104`); sharded refusal
  `..._cannot_route_itself_to_the_other_shard` + inheritance control
  `..._inherits_an_unrouted_parents_connection` + routed-parent control
  `..._follows_a_routed_parent_onto_its_shard`
  (`test_multi_db.py:1594/1616/1636`).
- Executed (shared `.venv`, Py 3.14.2, Dj 6.1): the two default-mode oracles
  green (`2 passed in 8.33s`); `/tmp/childalias-w2/probe.py` (sha
  `9de1d45b38d21c72`, read-only, zero SQL) 9/9 — seed pins both ways, shared
  arm rejects routed/unrouted-parent + seals unrouted, flag-off policy
  ACCEPTS the same routed child (unit-level negative control), elif rejects
  divergence, unrouted pins onto required, both policies carry the flag and
  differ only on `reject_sliced`.
- Live mutant proof (policy-drop -> refusal red) BLOCKED by slot-2's damaged
  venv (`ModuleNotFoundError: typing_extensions`; slots 1-3 all fail
  import; slot-4 healthy but free/warm, not my address — untouched):
  `workspace.py prove` at `dry/childalias-w2/verify` cannot execute. Control
  discharged instead by the executed unit-level both-ways probe + inspection
  (required `None` + flag-off policy: the `elif` needs required not-`None`,
  so the routed child is accepted, data served,
  `assert payload["data"] is None` fails mechanically).

### Matrix (own discharge against the real surface)

1. Cross-flavor mirroring: write flavor's `pin_write_queryset` read and
   excluded (pipeline alias, atomicity, raise); read surfaces share the one
   sealed boundary. Searched, not sampled.
2. Sync/async twins: both visibility runners share
   `_prepared_visibility_source`/`_normalized_visibility_result`; cascade
   async wraps the sync walk; related-filter twins share
   `_iter_visibility_steps`; no twin-only alias logic anywhere.
3. Derived knowledge: effective `.db` (resolved, router-invoking) vs explicit
   `_db` are two different facts, each read at its use; `attach_exists`
   snapshots both before comparing (stateful-router discipline). No second
   derivation of either fact.
4. Inverse/round-trip: seed-pin/check-result is the pair — deliberately two
   halves (see R-merge); composing `using=` construction with `alias` defect
   is the round trip, owned at the seal.
5. Contracts in other media: oracles assert literal messages
   (`"routed to alias 'default'"`) without reading `_defect_message` —
   independent. One prose observation: `filters/sets.py:2820` cites the
   cascade seed by its retired spelling (semantically exact; O-W2-a).
6. Enforcement by omission: descents enumerated — cascade, related filters,
   generated prefetch child, consumer `Prefetch` child, Exists subquery
   (predicates guard), single-parent repin, write pipeline, row recheck —
   each carries its own rule's guard; no member of THIS rule lacks one.

### Gates, verdict shape, cells

- No bespoke existence gate is owed: the realistic bypass (walker drops the
  policy / seals under a flag-less policy) flips the refusal oracles red by
  construction (probe control shows acceptance; acceptance serves data the
  oracles assert is `None`). The contrived bypass (an inlined behavior-equal
  comparison at the walker) has no justified population — DRY forbids a
  per-helper existence test for it. Refusal oracles are the effective gate.
- Zero new defects (O-W2-a is prose, spelled-semantically-exact; recorded
  here, not under `## Defects`).
- Cells: the two default-mode oracles re-executed green by this pass; the
  sharded trio + PG need the maintainer's word — no authorization anywhere in the plan
  (all mentions read "needs the maintainer's word" / "still blocked") — so they stay
  `unverified`; `inapplicable by construction` is correctly NOT claimed (the
  target reaches alias decisions on every descent).
- Type gates (whole-package, current bytes): `uv run mypy` -> `Success: no
  issues found in 119 source files`; `uv run basedpyright` -> `0 errors, 0
  warnings, 0 notes`; `uv run python scripts/check_any.py` -> `130 allowed
  use(s) of Any at 90 site(s)`, exit 0. Ruff on touched tracked paths:
  vacuous (only edit is this untracked `.md` artifact; bare-tree runs
  forbidden) — recorded as such, not run.
- Sept scratch `/var/folders/.../T/opencode/dry-ws/
  child-queryset-alias-inheritance`: does NOT exist (`No such file or
  directory`); never created, used, or deleted by this pass.

### Reconciliation (Worker-2, after reading `## Findings`)

Every difference between the Sept record and the fresh trace above, explicitly:

- R1 F1 ENDORSED. Contract, variation axes, sites+roles, C1=1/C2=1/C3=0
  (identical to mine), split ownership + lifetime fields, no-migration,
  and all three distinct-behavior keeps survive at current bytes. Drift
  deltas, all verdict-neutral: (a) the policy census is now two flagged
  policies — W1's "`_PREFETCH_CHILD_POLICY` sole production consumer: the
  walker" still holds for that constant (walker + the seal's own recursion,
  which W1 lists separately); the `_LIST_RELATION_CHILD_POLICY` split is
  documented in code + GLOSSARY and both flags are probe-verified; (b) all
  Sept freshness pins superseded by mine (expected, never staleness);
  (c) behavioral proof re-based onto current bytes (Sept WS gone): default
  pair re-executed green by this pass, 9/9 probe, live-mutant leg
  substituted as recorded above — verdict direction unchanged.
- R2 R-merge ENDORSED. Difference, trigger, and home all survive; both home
  phrases verified present verbatim (`base_queryset` docstring names the
  three relation-keyed seeders; `_SealPolicy` bullet reads "Set solely for
  a `Prefetch` child"). My independently-derived trigger is restated in
  favor of W1's: theirs (routing inexpressible as `using=` + policy fields)
  is the better-formed merge trigger; mine describes removal, kept as
  secondary. No edit owed.
- R3 D1-gone ENDORSED. `fd39cac6` intact at all four enforcement points,
  `4d9f1c3d` retirement intact (zero source hits), 5/5 oracles present with
  pinning assertions, D2 glossary half closed AND drift-updated (GLOSSARY
  documents the `_LIST` split; `allow_sliced` zero package hits, spec-045
  mentions archived-only). Scratch-prose count wobbles ("four controls",
  "the refusal" singular) noted, verdict-neutral: every test is named
  explicitly and present; true count is 2 refusals + 3 controls.
- R4 Matrix ENDORSED, all six axes. Filing differs (W1 puts twin analysis
  under axis 1 and write-flavor under axis 6; mine files write-flavor under
  axis 1 with full contract differences) but coverage is complete both ways.
  The axis-6 recheck-fallback exclusion is RE-VALIDATED against verified
  Family `related-object-visibility-recheck` (e3 M3/C2: the owning family
  counts the fallback as its own single body and requires no alias step);
  W1's trigger stands.
- R5 Enumeration ENDORSED. Pinned-`using=` sites 2/2, `parent_db`
  thread-throughs 5/5, retired symbol zero, `allow_sliced` zero
  (re-verified), seal-matrix oracle shapes 4/4 present
  (`test_prefetch_unrouted_child_inherits_outer_alias`,
  `test_prefetch_cross_alias_child_fails_closed`,
  `test_unrouted_parent_rejects_cross_routed_prefetch_child`, the
  `require_shared_alias=False` preset row). `require_shared_alias` string
  hits 8 -> 9 by the `_LIST` drift (expected).
- R6 P1/P2: P1 re-executed green in the shared tree; P2's live mutant is not
  re-executable (slot-2 venv damage, recorded) — the unit-level both-ways
  control is executed in its place and both "rejects" statements stand.
- R7 Defects ENDORSED (none new). O-W2-a judged not-a-defect (prose,
  semantically exact, no change obligation, self-correcting) — recorded in
  this section only; no `(Worker-2)` entries under `## Defects`.
- R8 Pending execution: Sept runs are history; the default pair is
  re-executed by this pass; sharded trio + PG stay `unverified` (plan-wide
  grep: no cell authorization exists). Minor record-shape deviation,
  verdict-neutral: W1 types the remaining work as bare "Unverified" rather
  than `proof: <command>`; in substance a deferred proof REMAINS (the
  cross-shard refusal is the defect's core scenario and has never executed
  in any cell), so the plan marking must be `verified, pending execution`
  per the e8 convention. Endorsed transcription for Worker-0: `proof:
  FAKESHOP_SHARDED=1 uv run pytest
  examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_cannot_route_itself_to_the_other_shard
  examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_inherits_an_unrouted_parents_connection
  examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_follows_a_routed_parent_onto_its_shard
  --no-cov` (+ PG cell named unverified, needs the maintainer's word + DSN).
- R9 Index row: the row W1 saw (`defect-routed`) has moved (current row 302:
  `open (D1 fixed by owned fd39cac6, F8 revised; adjudicated run 2,
  W2-endorsed)`). W1's `rejected` recommendation ENDORSED with fresh exact
  wording — Worker-0 applies verbatim: `rejected (W2-1 fresh trace at
  5c3496e0: F1 already-single x2 CONFIRMED, R-merge REJECTED with
  trigger+home, D1 GONE via owned fd39cac6/4d9f1c3d; 5 live oracles present,
  default pair re-executed green; verified, pending execution — sharded trio
  + PG await the maintainer's word)`.
- R10 Judgment endorsed in substance; its Sept diff-state/scratch notes are
  history (scratch path confirmed absent; current diff-state recorded in
  this section).

Verdict: `verified` (artifact); plan item `verified, pending execution`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-034]: ../SPECS/spec-034-permissions-0_0_10.md
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[permissions]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
